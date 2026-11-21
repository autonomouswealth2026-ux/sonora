"""TTS (FEATURE_MAP §1) + compatibilidad OpenAI + streaming por frases.

Motores:
- Voces fijas Kokoro -> Kokoro-82M (CPU, 24 kHz).
- Voces fijas Qwen CustomVoice (Ryan, Vivian...) -> Qwen3-TTS CustomVoice.
- Voces clonadas/diseñadas -> Qwen3-TTS Base (clonación zero-shot).
- model=auto elige según el tipo de voz.

Errores: 400 texto vacío o >10000 caracteres (lo valida Pydantic);
404 voice_id desconocido; 503 modelo GPU no cargado ("arranca el
backend GPU"); 429 rate limit.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse

from ..audio_utils import (
    apply_effects,
    split_sentences,
    wav_bytes,
    wav_to_mp3,
)
from ..engines import (
    KOKORO_LANG_CODES,
    KOKORO_VOICES,
    QWEN_CUSTOM_SPEAKERS,
    ModelUnavailable,
    manager,
)
from ..schemas import OpenAISpeechRequest, TTSRequest
from ..security import limit_heavy, require_auth
from ..store import store

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_auth)])

PREVIEW_TEXT = {
    "es": "Hola, soy {name}. Esta es una muestra de mi voz en español.",
    "en": "Hello, I am {name}. This is a sample of my voice in English.",
}


def resolve_voice(voice_id: str) -> dict:
    """Devuelve {source, voice_id, language, ...} o 404."""
    if voice_id in KOKORO_VOICES:
        return {"source": "kokoro", "voice_id": voice_id,
                **KOKORO_VOICES[voice_id]}
    if voice_id in QWEN_CUSTOM_SPEAKERS:
        return {"source": "qwen-customvoice", "voice_id": voice_id,
                **QWEN_CUSTOM_SPEAKERS[voice_id]}
    row = store.get_voice(voice_id)
    if row:
        return {"source": row["source"], "voice_id": voice_id, **row}
    raise HTTPException(
        status_code=404, detail=f"Voz desconocida: {voice_id}."
    )


def apply_dictionary(text: str, dictionary_id: str | None,
                     language: str = "es") -> str:
    """Aplica las reglas de pronunciación (sustitución por palabra).

    Sin dictionary_id no se aplica nada (A7: antes el frontend nunca
    lo enviaba y el backend aplicaba las reglas a todo). Con
    dictionary_id se aplican solo las reglas de ese idioma.
    """
    if not dictionary_id:
        return text
    import re

    out = text
    for rule in store.list_rules(language):
        pattern = re.compile(rf"\b{re.escape(rule['word'])}\b", re.IGNORECASE)
        out = pattern.sub(rule["replacement"], out)
    return out


def _instruct_graduado(valor: float | None, bajo: str, alto: str) -> str:
    """Traduce un slider 0..1 a una instrucción graduada (no binaria)."""
    if valor is None:
        return ""
    if valor >= 0.7:
        return alto + " "
    if valor <= 0.3:
        return bajo + " "
    return ""


def synthesize(req: TTSRequest, voice: dict) -> tuple[bytes, int, str, float]:
    """Sintetiza y devuelve (wav_bytes, sr, modelo_usado, duración_s)."""
    text = apply_dictionary(req.text, req.dictionary_id, req.language)
    source = voice["source"]
    language = req.language or voice.get("language", "es")

    # B4: similarity no la usa ningún motor de este backend. Rechazar
    # con 422 en vez de ignorarla en silencio. stability/style solo
    # existen en CustomVoice (vía instruct); en voces clonadas o
    # diseñadas Qwen3-TTS Base no expone ninguno de los tres.
    if req.similarity is not None:
        raise HTTPException(
            status_code=422,
            detail="similarity no está soportado por ningún motor de "
            "este backend (ni Kokoro ni Qwen3-TTS lo exponen).",
        )
    if source in ("cloned", "designed") and (
        req.stability is not None or req.style_exaggeration is not None
    ):
        raise HTTPException(
            status_code=422,
            detail="stability/style no están soportados para voces "
            "clonadas o diseñadas: Qwen3-TTS Base no expone esos "
            "ajustes. Solo speed tiene efecto en estas voces.",
        )

    if req.model == "kokoro" or (req.model == "auto" and source == "kokoro"):
        if source != "kokoro":
            raise HTTPException(
                status_code=400,
                detail="Esa voz no es de Kokoro: usa model=qwen3-tts-1.7b.",
            )
        if req.stability is not None or req.style_exaggeration is not None:
            raise HTTPException(
                status_code=422,
                detail="stability/style no están soportados por Kokoro: "
                "solo speed tiene efecto en estas voces.",
            )
        # A5: el pipeline lo decide el idioma DE LA VOZ, no el pedido:
        # ef_dora + language=en mezclaba voz española con pipeline inglés.
        # Pero el idioma PEDIDO también debe tener pipeline Kokoro: de/ko/ru
        # no lo tienen y se rechazan con 400 en vez de fingir inglés.
        if req.language not in KOKORO_LANG_CODES:
            raise HTTPException(
                status_code=400,
                detail=f"Kokoro no tiene pipeline para el idioma "
                f"'{req.language}'. Idiomas con pipeline: es, en, fr, "
                "it, pt, ja, zh.",
            )
        language = voice.get("language", "es")
        try:
            samples, sr = manager.synthesize_kokoro(
                text, req.voice_id, req.speed, language, req.normalize
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        model_used = "kokoro"
    elif req.model in ("qwen3-tts-0.6b",):
        samples, sr = _synthesize_clone(
            text, voice, language, "qwen3-tts-0.6b", req
        )
        model_used = "qwen3-tts-0.6b"
    elif source == "qwen-customvoice":
        instruct = (
            _instruct_graduado(
                req.stability,
                "Speak expressively with varied intonation.",
                "Speak very steadily and consistently.",
            )
            + _instruct_graduado(
                req.style_exaggeration,
                "Keep a neutral, plain delivery.",
                "Be very expressive and dramatic.",
            )
        )
        try:
            samples, sr = manager.synthesize_qwen_custom(
                text, req.voice_id, language, instruct.strip(), req.normalize
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        model_used = "qwen3-tts-1.7b-customvoice"
    elif source in ("cloned", "designed"):
        samples, sr = _synthesize_clone(
            text, voice, language, "qwen3-tts-1.7b", req
        )
        model_used = "qwen3-tts-1.7b"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"La voz {req.voice_id} no tiene motor asignado.",
        )

    if req.audio_effects:
        samples = apply_effects(samples, sr, req.audio_effects)
    wav = wav_bytes(samples, sr)
    duration = len(samples) / sr if sr else 0.0
    return wav, sr, model_used, duration


def _synthesize_clone(text, voice, language, variant, req):
    ref_path = voice.get("reference_path") or ""
    ref_text = voice.get("reference_text") or ""
    if not ref_path:
        raise HTTPException(
            status_code=400,
            detail=f"La voz {voice['voice_id']} no tiene audio de referencia.",
        )
    try:
        samples, sr = manager.synthesize_qwen_clone(
            text, ref_path, ref_text, language, variant, req.normalize
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    # B4: speed SÍ tiene efecto real en voces clonadas: Qwen3-TTS no
    # expone velocidad, así que se remuestrea el audio resultante
    # (menos muestras a la misma sr = más rápido, y al revés).
    if req.speed != 1.0:
        from ..audio_utils import resample

        samples = resample(samples, sr, max(1, int(sr / req.speed)))
    return samples, sr


def _audio_response(wav: bytes, sr: int, fmt: str, gen_id: str,
                    model_used: str, voice_id: str, duration: float):
    if fmt == "mp3":
        body, media = wav_to_mp3(wav), "audio/mpeg"
    else:
        body, media = wav, "audio/wav"
    headers = {
        "X-Generation-Id": gen_id,
        "X-Duration-Seconds": f"{duration:.2f}",
        "X-Model": model_used,
        "X-Voice-Id": voice_id,
    }
    return Response(content=body, media_type=media, headers=headers)


@router.post("/tts")
async def tts(req: TTSRequest, _rl=Depends(limit_heavy)):
    """Texto -> audio. Ver FEATURE_MAP §1."""
    voice = resolve_voice(req.voice_id)
    try:
        wav, sr, model_used, duration = synthesize(req, voice)
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    gen_id = uuid.uuid4().hex[:12]
    audio_path = store.audio_dir / f"{gen_id}.{req.format}"
    try:
        audio_path.write_bytes(
            wav_to_mp3(wav) if req.format == "mp3" else wav
        )
    except Exception:
        audio_path = None
    store.add_history(
        id=f"gen_{gen_id}", type="tts", text=req.text,
        voice_id=req.voice_id, model=model_used, duration_s=round(duration, 2),
        characters=len(req.text),
        audio_path=str(audio_path) if audio_path else "",
        audio_format=req.format,
    )
    return _audio_response(wav, sr, req.format, gen_id, model_used,
                           req.voice_id, duration)


def _strip_wav_header(wav: bytes) -> bytes:
    """Quita la cabecera WAV buscando el chunk 'data' (A11: antes se
    recortaban 44 bytes fijos a ciegas; la cabecera puede ser más larga)."""
    idx = wav.find(b"data")
    if idx < 0:
        return wav
    start = idx + 8
    return wav[start:]


@router.post("/tts/stream")
async def tts_stream(req: TTSRequest, _rl=Depends(limit_heavy)):
    """Streaming por frases: cada frase se sintetiza y se envía en cuanto
    está lista, dentro de un único WAV. No es streaming por token del
    modelo (Qwen3-TTS no lo expone por el paquete Python); para
    narración por lotes el efecto es el mismo: el audio empieza antes
    de que termine todo el texto."""
    voice = resolve_voice(req.voice_id)
    sentences = split_sentences(req.text)
    gen_id = uuid.uuid4().hex[:12]
    # VERIFICACION B3: sintetizar la PRIMERA frase ANTES de devolver
    # el StreamingResponse. Si no hay motor, el 503 sale aquí (antes
    # la excepción dentro del generador dejaba un 200 con 0 bytes).
    try:
        first_wav, sr, model_used, first_dur = synthesize(
            TTSRequest(**{**req.model_dump(), "text": sentences[0]}), voice
        )
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    def _generate():
        total_dur = first_dur
        yield first_wav
        for sentence in sentences[1:]:
            sub = TTSRequest(**{**req.model_dump(), "text": sentence})
            try:
                wav, _sr, _m, dur = synthesize(sub, voice)
            except ModelUnavailable:
                # El motor falló a mitad de stream: no se puede cambiar
                # el 200 ya enviado; se corta el audio aquí.
                break
            total_dur += dur
            yield _strip_wav_header(wav)
        # A11: el stream también queda en el historial, como /tts.
        store.add_history(
            id=f"gen_{gen_id}", type="tts", text=req.text,
            voice_id=req.voice_id, model=model_used,
            duration_s=round(total_dur, 2), characters=len(req.text),
            audio_path="", audio_format="wav",
        )

    return StreamingResponse(
        _generate(), media_type="audio/wav",
        headers={"X-Generation-Id": gen_id,
                 "X-Model": "stream-por-frases",
                 "X-Voice-Id": req.voice_id})


@router.get("/tts/voices")
def list_tts_voices():
    """Voces disponibles: fijas (Kokoro + Qwen CustomVoice) + clonadas
    + diseñadas. Ver FEATURE_MAP §1."""
    out = [
        {"voice_id": vid, "name": info["name"], "source": "kokoro",
         "language": info["language"]}
        for vid, info in KOKORO_VOICES.items()
    ]
    out += [
        {"voice_id": name, "name": f"{name} (Qwen CustomVoice)",
         "source": "qwen-customvoice",
         "language": info["language"]}
        for name, info in QWEN_CUSTOM_SPEAKERS.items()
    ]
    for row in store.list_voices():
        out.append(
            {"voice_id": row["voice_id"], "name": row["name"],
             "source": row["source"], "language": row["language"],
             "favorite": bool(row["favorite"]),
             "preview_url": f"/api/v1/voices/{row['voice_id']}/preview"}
        )
    return {"voices": out}


@router.post("/audio/speech")
async def openai_speech(req: OpenAISpeechRequest, _rl=Depends(limit_heavy)):
    """Compatibilidad parcial con OpenAI (/v1/audio/speech)."""
    model_map = {
        "kokoro": "kokoro",
        "qwen3-tts": "qwen3-tts-1.7b",
        "qwen3-tts-1.7b": "qwen3-tts-1.7b",
        "qwen3-tts-0.6b": "qwen3-tts-0.6b",
        "tts-1": "kokoro",
    }
    model = model_map.get(req.model)
    if not model:
        raise HTTPException(
            status_code=400,
            detail=f"Modelo no admitido: {req.model}. "
            "Usa kokoro o qwen3-tts-1.7b.",
        )
    tts_req = TTSRequest(
        text=req.input, voice_id=req.voice, model=model,
        speed=min(max(req.speed, 0.5), 2.0), format=req.response_format,
    )
    voice = resolve_voice(req.voice)
    try:
        wav, sr, model_used, duration = synthesize(tts_req, voice)
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    gen_id = uuid.uuid4().hex[:12]
    store.add_history(
        id=f"gen_{gen_id}", type="tts", text=req.input,
        voice_id=req.voice, model=model_used, duration_s=round(duration, 2),
        characters=len(req.input), audio_path="",
        audio_format=req.response_format,
    )
    return _audio_response(wav, sr, req.response_format, gen_id,
                           model_used, req.voice, duration)
