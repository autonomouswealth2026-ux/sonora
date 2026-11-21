"""Voces: clonación instantánea (§3), Voice Design (§6), biblioteca
propia (§5, solo la cáscara local) y borrado.

CONSENTIMIENTO: clonar exige `consent_note` (declaración explícita de
que la persona de la muestra autoriza la clonación) y queda guardado
junto a la voz. Sin consentimiento no hay clonación, aunque el modelo
lo permita. El audio de referencia se guarda solo con ese
consentimiento y se borra si se borra la voz.
"""

import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ..audio_utils import audio_duration, wav_bytes, wav_to_mp3
from ..config import settings
from ..engines import ModelUnavailable, manager
from ..schemas import VoiceDesignRequest, VoiceDesignSaveRequest
from ..security import AUDIO_EXTS, limit_heavy, read_upload, require_auth
from ..store import store
from .tts import PREVIEW_TEXT, resolve_voice

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_auth)])

DESIGN_PREVIEW_TEXT = {
    "es": "Hola, soy una voz nueva, creada desde una descripción. "
    "¿Te gusta cómo sueno?",
    "en": "Hello, I am a brand new voice, created from a description. "
    "How do I sound?",
}


def _candidate_path(candidate_id: str) -> Path:
    """Ruta del audio de un candidato, sin path traversal (A13):
    el id lo controla el cliente y "../" leía .wav fuera del
    directorio. Solo se acepta el formato cand_<hex> y la ruta
    resuelta debe quedar dentro de voices_dir."""
    if not re.fullmatch(r"cand_[0-9a-f]+", candidate_id or ""):
        raise HTTPException(status_code=404, detail="Candidato desconocido.")
    path = (store.voices_dir / f"{candidate_id}.wav").resolve()
    if not path.is_relative_to(store.voices_dir.resolve()):
        raise HTTPException(status_code=404, detail="Candidato desconocido.")
    return path


@router.post("/voices/instant-clone", status_code=201)
async def instant_clone(
    audio: UploadFile = File(...),
    name: str = Form(..., min_length=1, max_length=80),
    description: str = Form(default=""),
    language: str = Form(default="es"),
    consent_note: str = Form(..., min_length=10, max_length=500),
    _rl=Depends(limit_heavy),
):
    """Crea una voz clonada desde 3 s..2 min de audio limpio (FEATURE_MAP §3)."""
    if language not in ("es", "en", "fr", "de", "it", "pt"):
        raise HTTPException(status_code=400, detail="Idioma no admitido.")
    data, ext = await read_upload(audio, AUDIO_EXTS, settings.max_clone_bytes)
    duration = audio_duration(data)
    if duration < 3:
        raise HTTPException(
            status_code=400,
            detail=f"Muestra demasiado corta: {duration:.1f} s (mínimo 3 s). "
            "Graba al menos 10-30 s limpios, sin música ni eco.",
        )
    if duration > 120:
        raise HTTPException(
            status_code=400,
            detail=f"Muestra demasiado larga: {duration:.0f} s (máximo 2 min).",
        )
    voice_id = f"v_{uuid.uuid4().hex[:12]}"
    voice_dir = store.voices_dir / voice_id
    voice_dir.mkdir(parents=True, exist_ok=True)
    ref_path = voice_dir / f"reference.{ext}"
    ref_path.write_bytes(data)

    # Qwen3-TTS Base necesita la transcripción de la referencia.
    # Se intenta con Whisper; si no está disponible, se usa el modo
    # solo-embedding (x_vector_only_mode), con algo menos de fidelidad.
    ref_text = ""
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        segments, _meta = manager.transcribe(
            tmp_path, language, "small", word_timestamps=False
        )
        ref_text = " ".join(s["text"] for s in segments).strip()
        Path(tmp_path).unlink(missing_ok=True)
    except ModelUnavailable:
        ref_text = ""
    except Exception:
        ref_text = ""

    voice = store.create_voice(
        voice_id=voice_id, name=name, source="cloned", language=language,
        description=description, model="qwen3-tts-1.7b",
        reference_path=str(ref_path), reference_text=ref_text,
        consent_note=consent_note,
    )
    return {
        "voice_id": voice["voice_id"],
        "name": voice["name"],
        "model": "qwen3-tts-1.7b",
        "reference_duration_s": round(duration, 2),
        "reference_transcribed": bool(ref_text),
        "created_at": voice["created_at"],
        "preview_url": f"/api/v1/voices/{voice_id}/preview",
    }


@router.get("/voices/{voice_id}/preview")
async def voice_preview(voice_id: str, _rl=Depends(limit_heavy)):
    """Audio corto de prueba ("Hola, soy…") con esa voz."""
    voice = resolve_voice(voice_id)
    if voice["source"] == "kokoro":
        samples, sr = manager.synthesize_kokoro(
            PREVIEW_TEXT.get(voice.get("language", "es"), PREVIEW_TEXT["es"])
            .format(name=voice.get("name", voice_id)),
            voice_id, 1.0, voice.get("language", "es"),
        )
        model_used = "kokoro"
    elif voice["source"] == "qwen-customvoice":
        samples, sr = manager.synthesize_qwen_custom(
            PREVIEW_TEXT.get("en", PREVIEW_TEXT["en"]).format(
                name=voice_id),
            voice_id, "en",
        )
        model_used = "qwen3-tts-1.7b-customvoice"
    else:
        lang = voice.get("language", "es")
        text = PREVIEW_TEXT.get(lang, PREVIEW_TEXT["es"]).format(
            name=voice.get("name", voice_id)
        )
        try:
            samples, sr = manager.synthesize_qwen_clone(
                text, voice["reference_path"], voice.get("reference_text", ""),
                lang,
            )
        except ModelUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        model_used = "qwen3-tts-1.7b"
    wav = wav_bytes(samples, sr)
    return Response(content=wav_to_mp3(wav), media_type="audio/mpeg",
                    headers={"X-Model": model_used, "X-Voice-Id": voice_id})


@router.delete("/voices/{voice_id}")
def delete_voice(voice_id: str):
    """Borra la voz y su audio de referencia (borrado real)."""
    if voice_id in ("ef_dora", "em_alex", "em_santa") or voice_id in (
        "af_heart", "af_bella", "af_sarah", "am_adam", "am_michael",
        "bf_emma", "bm_george",
    ):
        raise HTTPException(
            status_code=400, detail="Las voces fijas de Kokoro no se borran."
        )
    deleted = store.delete_voice(voice_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Voz desconocida.")
    return {"deleted": True, "voice_id": voice_id}


@router.post("/voices/design", status_code=201)
async def design_voice(req: VoiceDesignRequest, _rl=Depends(limit_heavy)):
    """Voice Design (§6): describe una voz y recibe hasta 3 candidatos."""
    preview_text = DESIGN_PREVIEW_TEXT.get(req.language,
                                           DESIGN_PREVIEW_TEXT["es"])
    try:
        candidates = manager.design_voices(
            preview_text, req.prompt, req.language, req.num_previews
        )
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    out = []
    for samples, sr in candidates:
        candidate_id = f"cand_{uuid.uuid4().hex[:12]}"
        path = store.voices_dir / f"{candidate_id}.wav"
        path.write_bytes(wav_bytes(samples, sr))
        out.append(
            {
                "candidate_id": candidate_id,
                "preview_url": f"/api/v1/voices/design/{candidate_id}/preview",
                "description": req.prompt,
            }
        )
    return {"candidates": out}


@router.get("/voices/design/{candidate_id}/preview")
def design_preview(candidate_id: str):
    path = _candidate_path(candidate_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Candidato desconocido.")
    return Response(content=wav_to_mp3(path.read_bytes()),
                    media_type="audio/mpeg")


@router.post("/voices/design/{candidate_id}/save", status_code=201)
def save_designed_voice(candidate_id: str, req: VoiceDesignSaveRequest):
    """Guarda un candidato de Voice Design como voz.

    La voz diseñada se reutiliza después como clonación desde su
    propio audio candidato (más estable que re-diseñarla cada vez).
    """
    path = _candidate_path(candidate_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Candidato desconocido.")
    voice_id = f"v_{uuid.uuid4().hex[:12]}"
    voice_dir = store.voices_dir / voice_id
    voice_dir.mkdir(parents=True, exist_ok=True)
    ref_path = voice_dir / "reference.wav"
    ref_path.write_bytes(path.read_bytes())
    voice = store.create_voice(
        voice_id=voice_id, name=req.name, source="designed",
        language="es", model="qwen3-tts-1.7b",
        reference_path=str(ref_path),
        reference_text=DESIGN_PREVIEW_TEXT["es"],
        design_prompt="",
    )
    return {
        "voice_id": voice["voice_id"], "name": voice["name"],
        "source": "designed",
        "preview_url": f"/api/v1/voices/{voice_id}/preview",
    }


@router.get("/library/voices")
def library_voices(language: str | None = None, tag: str | None = None,
                   q: str | None = None):
    """Biblioteca propia (§5): voces fijas + diseñadas + clonadas.

    No es la Voice Library de ElevenLabs (miles de voces con licencia):
    es la biblioteca local de 2 usuarios, con búsqueda y favoritos.
    """
    from .tts import list_tts_voices

    voices = list_tts_voices()["voices"]
    if language:
        voices = [v for v in voices if v.get("language") == language]
    if q:
        ql = q.lower()
        voices = [v for v in voices if ql in v.get("name", "").lower()]
    return {"voices": voices, "total": len(voices)}


@router.post("/library/voices/{voice_id}/favorite")
def favorite_voice(voice_id: str):
    """Marca/desmarca una voz clonada o diseñada como favorita."""
    voice = store.get_voice(voice_id)
    if not voice:
        raise HTTPException(
            status_code=404,
            detail="Solo las voces clonadas o diseñadas tienen favoritos.",
        )
    updated = store.set_favorite(voice_id, not bool(voice["favorite"]))
    return {"voice_id": voice_id, "favorite": bool(updated["favorite"])}
