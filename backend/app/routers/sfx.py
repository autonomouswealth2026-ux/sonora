"""Sound Effects (§11): Stable Audio Open 1.0.

Hasta 47 s por generación, estéreo 44,1 kHz. Repo con términos en
Hugging Face: hay que aceptarlos y poner HF_TOKEN en el entorno.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from ..audio_utils import wav_bytes, wav_to_mp3
from ..engines import ModelUnavailable, manager
from ..schemas import SFXRequest
from ..security import limit_heavy, require_auth
from ..store import store

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_auth)])


@router.post("/sfx")
async def sfx(req: SFXRequest, _rl=Depends(limit_heavy)):
    """Genera efectos de sonido desde texto (FEATURE_MAP §11)."""
    variants = []
    try:
        for _ in range(req.num_variants):
            samples, sr = manager.sfx_generate(req.prompt, req.duration_s)
            variants.append((samples, sr))
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if req.num_variants == 1:
        samples, sr = variants[0]
        wav = wav_bytes(samples, sr)
        gen_id = uuid.uuid4().hex[:12]
        audio_path = store.audio_dir / f"{gen_id}.mp3"
        audio_path.write_bytes(wav_to_mp3(wav))
        store.add_history(
            id=f"gen_{gen_id}", type="sfx", text=req.prompt, voice_id="",
            model=req.model, duration_s=round(len(samples) / sr, 2),
            characters=len(req.prompt), audio_path=str(audio_path),
            audio_format="mp3",
        )
        return Response(content=wav_to_mp3(wav), media_type="audio/mpeg",
                        headers={"X-Generation-Id": gen_id,
                                 "X-Model": req.model})
    out = []
    for samples, sr in variants:
        gen_id = uuid.uuid4().hex[:12]
        audio_path = store.audio_dir / f"{gen_id}.mp3"
        audio_path.write_bytes(wav_to_mp3(wav_bytes(samples, sr)))
        store.add_history(
            id=f"gen_{gen_id}", type="sfx", text=req.prompt, voice_id="",
            model=req.model, duration_s=round(len(samples) / sr, 2),
            characters=len(req.prompt), audio_path=str(audio_path),
            audio_format="mp3",
        )
        out.append({"generation_id": gen_id,
                    "audio_url": f"/api/v1/history/gen_{gen_id}/audio"})
    return {"variants": out}
