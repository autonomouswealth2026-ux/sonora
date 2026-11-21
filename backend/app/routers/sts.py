"""Speech to Speech / Voice Changer (§8), vía básica.

Dos métodos:
- voice-conversion: 501 (no hay modelo de conversión de voz instalado;
  OpenVoice v2 / kNN-VC quedan como trabajo futuro, no se fingen).
- stt-tts (implementado): transcribe con Whisper y re-sintetiza con la
  voz destino. Conserva el contenido, PIERDE la interpretación
  original (emoción, cadencia, susurros): la UI debe etiquetarlo así.
"""

import base64
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ..audio_utils import audio_duration, wav_to_mp3
from ..config import settings
from ..engines import ModelUnavailable, manager
from ..schemas import TTSRequest
from ..security import AUDIO_EXTS, limit_heavy, read_upload, require_auth
from .tts import resolve_voice, synthesize

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_auth)])


@router.post("/speech-to-speech")
async def speech_to_speech(
    audio: UploadFile = File(...),
    target_voice_id: str = Form(...),
    method: str = Form(default="stt-tts"),
    _rl=Depends(limit_heavy),
):
    """Convierte una voz grabada a la voz destino (FEATURE_MAP §8)."""
    if method == "voice-conversion":
        raise HTTPException(
            status_code=501,
            detail="Conversión de voz directa no implementada: no hay "
            "modelo de voice conversion instalado. Usa method=stt-tts "
            "(transcribe y re-sintetiza; pierde la interpretación).",
        )
    if method != "stt-tts":
        raise HTTPException(status_code=400, detail="Método no admitido.")
    voice = resolve_voice(target_voice_id)
    data, ext = await read_upload(audio, AUDIO_EXTS, settings.max_upload_bytes)
    if audio_duration(data) > 600:
        raise HTTPException(
            status_code=400, detail="Audio mayor de 10 minutos."
        )
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        size = "large-v3" if not settings.cpu_only else "small"
        segments, _meta = manager.transcribe(
            tmp_path, None, size, word_timestamps=False
        )
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    text = " ".join(s["text"] for s in segments).strip()
    if not text:
        raise HTTPException(
            status_code=422,
            detail="No se detectó voz en el audio (transcripción vacía).",
        )
    req = TTSRequest(text=text, voice_id=target_voice_id, format="mp3")
    try:
        wav, sr, model_used, duration = synthesize(req, voice)
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return Response(
        content=wav_to_mp3(wav), media_type="audio/mpeg",
        headers={
            "X-Method": "stt-tts",
            "X-Model": model_used,
            "X-Duration-Seconds": f"{duration:.2f}",
            # A12: el texto transcrito ya no va en claro en una
            # cabecera: acentos, emojis o saltos de línea no son
            # Latin-1 y daban 500 DESPUÉS de sintetizar. Va en
            # base64 UTF-8 (X-Transcribed-Text-B64) y su longitud.
            "X-Transcribed-Text-B64": base64.b64encode(
                text.encode("utf-8")).decode("ascii"),
            "X-Transcribed-Chars": str(len(text)),
            "X-Note": "Metodo stt-tts: conserva el contenido, "
            "pierde la interpretacion original.",
        },
    )
