"""Voice Isolator (§13) y efectos de audio en TTS (§23).

Isolator: Demucs (htdemucs, MIT). El modo `denoise` (ruido no musical)
no está implementado: devuelve 501 con la alternativa (DeepFilterNet,
pendiente de integrar).
Efectos: DSP clásico con audio_utils.apply_effects.
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError

from ..audio_utils import apply_effects, read_audio_bytes, wav_bytes, wav_to_mp3
from ..config import settings
from ..engines import ModelUnavailable, manager
from ..schemas import AudioEffectsRequest
from ..security import MEDIA_EXTS, limit_heavy, read_upload, require_auth
from ..store import new_id, store

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_auth)])


@router.post("/isolate")
async def isolate(
    audio: UploadFile = File(...),
    mode: str = Form(default="demucs"),
    keep_background: bool = Form(default=False),
    _rl=Depends(limit_heavy),
):
    """Limpia una grabación: devuelve solo la voz (FEATURE_MAP §13)."""
    if mode not in ("demucs", "denoise"):
        raise HTTPException(status_code=400, detail="Modo no admitido.")
    if mode == "denoise":
        raise HTTPException(
            status_code=501,
            detail="El modo denoise (ruido no musical) no está implementado. "
            "Usa mode=demucs para música de fondo.",
        )
    data, ext = await read_upload(audio, MEDIA_EXTS, settings.max_upload_bytes)
    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = Path(tmpdir) / f"input.{ext}"
        in_path.write_bytes(data)
        out_dir = Path(tmpdir) / "out"
        try:
            vocals_path, bg_path = manager.isolate_demucs(str(in_path), str(out_dir))
        except ModelUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        vocals = Path(vocals_path).read_bytes()
        gen_id = new_id("gen_")
        vocals_file = store.audio_dir / f"{gen_id}-vocals.wav"
        vocals_file.write_bytes(vocals)
        if keep_background and bg_path:
            bg_file = store.audio_dir / f"{gen_id}-background.wav"
            bg_file.write_bytes(Path(bg_path).read_bytes())
            store.add_history(
                id=gen_id, type="isolate", text="", voice_id="",
                model="demucs", duration_s=0, characters=0,
                audio_path=str(vocals_file), audio_format="wav",
            )
            return {
                "vocals_url": f"/api/v1/history/{gen_id}/audio",
                "background_url": f"/api/v1/history/{gen_id}/audio?track=background",
                "note": "Descarga la voz limpia en vocals_url.",
            }
        store.add_history(
            id=gen_id, type="isolate", text="", voice_id="",
            model="demucs", duration_s=0, characters=0,
            audio_path=str(vocals_file), audio_format="wav",
        )
        return Response(content=wav_to_mp3(vocals), media_type="audio/mpeg",
                        headers={"X-Generation-Id": gen_id, "X-Model": "demucs"})


EFFECTS_CATALOG = {
    "reverb": ["none", "room", "hall"],
    "distance": ["close", "far"],
    "background_noise": ["none", "rain", "cafe"],
    "pan": {"min": -1.0, "max": 1.0},
    "filter_preset": ["none", "telephone", "radio"],
}


@router.get("/audio-effects/catalog")
def effects_catalog():
    """Catálogo de presets de efectos (§23)."""
    return {"presets": EFFECTS_CATALOG}


@router.post("/audio-effects/apply")
async def apply_audio_effects(
    audio: UploadFile = File(...),
    reverb: str = Form(default="none"),
    distance: str = Form(default="close"),
    background_noise: str = Form(default="none"),
    pan: float = Form(default=0.0),
    filter_preset: str = Form(default="none"),
    _rl=Depends(limit_heavy),
):
    """Aplica efectos DSP a un audio subido (§23)."""
    # VERIFICACION B4: construir el esquema a mano sin capturar
    # ValidationError subía como 500; un preset inválido es 422.
    try:
        req = AudioEffectsRequest(
            reverb=reverb, distance=distance,
            background_noise=background_noise, pan=pan,
            filter_preset=filter_preset,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    data, _ext = await read_upload(audio, MEDIA_EXTS, settings.max_upload_bytes)
    samples, sr = read_audio_bytes(data)
    out = apply_effects(samples, sr, req.model_dump())
    wav = wav_bytes(out, sr)
    return Response(content=wav_to_mp3(wav), media_type="audio/mpeg")
