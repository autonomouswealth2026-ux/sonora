"""Speech to Text (§10) y alineación forzada (§24).

Motor: faster-whisper (large-v3 en GPU, small en CPU). Diarización:
solo si pyannote está instalado y sus modelos aceptados; si no,
422 con el motivo (no se finge diarización).
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ..config import settings
from ..engines import ModelUnavailable, manager
from ..security import MEDIA_EXTS, limit_heavy, read_upload, require_auth

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_auth)])


def _segments_to_srt(segments: list[dict]) -> str:
    def fmt(t: float) -> str:
        h, m = int(t // 3600), int((t % 3600) // 60)
        s, ms = int(t % 60), int((t % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, seg in enumerate(segments, 1):
        lines.append(f"{i}\n{fmt(seg['start'])} --> {fmt(seg['end'])}\n{seg['text']}\n")
    return "\n".join(lines)


def _segments_to_vtt(segments: list[dict]) -> str:
    def fmt(t: float) -> str:
        h, m = int(t // 3600), int((t % 3600) // 60)
        s, ms = int(t % 60), int((t % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

    lines = ["WEBVTT", ""]
    for seg in segments:
        lines.append(f"{fmt(seg['start'])} --> {fmt(seg['end'])}\n{seg['text']}\n")
    return "\n".join(lines)


def _diarize(audio_path: str, segments: list[dict]) -> list[dict]:
    """Etiqueta hablantes con pyannote si está disponible."""
    try:
        from pyannote.audio import Pipeline
    except ImportError:
        raise HTTPException(
            status_code=422,
            detail="Diarización no disponible: pyannote no está instalado. "
            "Reintenta con diarize=false.",
        )
    try:
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=settings.hf_token or None,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Diarización no disponible: el modelo de pyannote exige "
            f"aceptar sus condiciones en Hugging Face y HF_TOKEN. ({exc})",
        )
    diarization = pipeline(audio_path)
    turns = [(t.start, t.end, spk) for t, _, spk in diarization.itertracks(yield_label=True)]
    for seg in segments:
        mid = (seg["start"] + seg["end"]) / 2
        seg["speaker"] = next(
            (spk for s, e, spk in turns if s <= mid <= e), None
        )
    return segments


@router.post("/stt")
async def stt(
    audio: UploadFile = File(...),
    language: str = Form(default="auto"),
    model: str = Form(default="large-v3"),
    diarize: bool = Form(default=False),
    word_timestamps: bool = Form(default=True),
    keyterms: str = Form(default=""),
    output_format: str = Form(default="json"),
    _rl=Depends(limit_heavy),
):
    """Transcribe audio o vídeo (FEATURE_MAP §10)."""
    if model not in ("small", "medium", "large-v3"):
        raise HTTPException(status_code=400, detail="Modelo STT no admitido.")
    if output_format not in ("json", "srt", "vtt", "txt"):
        raise HTTPException(status_code=400, detail="Formato no admitido.")
    data, ext = await read_upload(audio, MEDIA_EXTS, settings.max_upload_bytes)
    terms = [t.strip() for t in keyterms.split(",") if t.strip()][:1000]
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        if model == "large-v3" and settings.cpu_only:
            raise HTTPException(
                status_code=503,
                detail="large-v3 necesita GPU. En CPU usa model=small.",
            )
        segments, meta = manager.transcribe(
            tmp_path, language, model, word_timestamps, terms
        )
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    if diarize:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            segments = _diarize(tmp_path, segments)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    else:
        for seg in segments:
            seg["speaker"] = None
    if output_format == "srt":
        return Response(content=_segments_to_srt(segments),
                        media_type="text/plain")
    if output_format == "vtt":
        return Response(content=_segments_to_vtt(segments),
                        media_type="text/vtt")
    if output_format == "txt":
        return Response(
            content="\n".join(s["text"] for s in segments),
            media_type="text/plain",
        )
    return {
        "language": meta["language"],
        "duration_s": meta["duration_s"],
        "segments": segments,
    }


@router.post("/align")
async def align(
    audio: UploadFile = File(...),
    transcript: str = Form(..., min_length=1, max_length=20000),
    language: str = Form(default="es"),
    output_format: str = Form(default="json"),
    _rl=Depends(limit_heavy),
):
    """Alineación forzada (§24): palabras con inicio y fin.

    Implementada con faster-whisper (timestamps por palabra). La
    cobertura indica qué parte de la transcripción conocida coincide
    con lo transcrito: no es un alineador fonético (MFA), y se dice.
    """
    if output_format not in ("json", "srt", "vtt"):
        raise HTTPException(status_code=400, detail="Formato no admitido.")
    data, ext = await read_upload(audio, MEDIA_EXTS, settings.max_upload_bytes)
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        size = "large-v3" if not settings.cpu_only else "small"
        segments, meta = manager.transcribe(
            tmp_path, language, size, word_timestamps=True
        )
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    words = [w for s in segments for w in s.get("words", [])]
    known = set(transcript.lower().split())
    matched = sum(1 for w in words if w["word"].strip().lower() in known)
    coverage = round(matched / max(len(words), 1), 3)
    if output_format == "srt":
        return Response(
            content=_segments_to_srt(
                [{"start": w["start"], "end": w["end"], "text": w["word"]}
                 for w in words]
            ),
            media_type="text/plain",
        )
    if output_format == "vtt":
        return Response(
            content=_segments_to_vtt(
                [{"start": w["start"], "end": w["end"], "text": w["word"]}
                 for w in words]
            ),
            media_type="text/vtt",
        )
    return {
        "words": words,
        "segments": segments,
        "coverage_vs_transcript": coverage,
        "note": "Alineación por Whisper (timestamps por palabra). "
        "Si coverage es bajo, revisa que el audio y la transcripción coincidan.",
    }
