"""Dubbing básico (§9): pipeline Whisper -> traducción -> TTS clonado.

Alcance honesto del "básico":
- Idiomas: solo español<->inglés (MarianMT Helsinki-NLP). Otros pares
  devuelven 422, no una traducción fingida.
- Sin sincronización labial (ElevenLabs tampoco la tiene en Dubbing v2).
- Límite de subida en ElevenLabs en disputa (1 GB docs / 2 GB ayuda /
  3 GB API); este clon admite 500 MB por defecto (MAX_DUBBING_MB).
- La transferencia de emoción/ritmo es parcial: el TTS clonado
  cross-lingual mantiene el timbre, no la interpretación exacta.
- Un vídeo de 10 min puede tardar varios minutos en T4: trabajo
  asíncrono con job_id y consulta de estado (el fallo queda registrado
  en la tabla de jobs: dead-letter log de replica-backend).

Flujo: extraer audio -> transcribir por segmentos -> traducir ->
sintetizar cada segmento con la voz original clonada -> colocar cada
segmento en su tiempo -> mezclar el fondo original atenuado -> si la
entrada era vídeo, re-muxar.
"""

import subprocess
import tempfile
import threading
from pathlib import Path

import numpy as np

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response

from ..audio_utils import read_audio_bytes, resample, wav_bytes, wav_to_mp3
from ..config import settings
from ..engines import ModelUnavailable, manager
from ..schemas import DubbingSegmentEdit
from ..security import MEDIA_EXTS, limit_heavy, read_upload, require_auth
from ..store import store
from .tts import resolve_voice

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_auth)])

TARGET_SR = 24000


def _ffmpeg(*args: str, input_data: bytes | None = None,
            timeout: int = 1800) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", *args],
        input=input_data, capture_output=True, timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg falló: {proc.stderr.decode()[-300:]}")
    return proc


def _extract_audio(media_path: Path, tmpdir: Path) -> Path:
    wav_path = tmpdir / "source.wav"
    _ffmpeg("-i", str(media_path), "-vn", "-ac", "1", "-ar", "16000",
            str(wav_path))
    return wav_path


def _is_video(path: Path) -> bool:
    """¿La entrada tiene pista de vídeo? Un .webm puede ser solo audio
    (la grabación del navegador), así que no basta la extensión: se
    pregunta a ffprobe y, si no está, solo .mp4 cuenta como vídeo."""
    if path.suffix.lower() == ".mp4":
        return True
    if path.suffix.lower() != ".webm":
        return False
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0",
             str(path)],
            capture_output=True, text=True, timeout=30,
        )
        return proc.returncode == 0 and "video" in proc.stdout
    except Exception:
        return False


def _parse_targets(raw: str) -> list[str]:
    """B1: el frontend mandaba JSON (["en"]) y el backend lo partía
    por comas -> 422 siempre. Se aceptan los tres formatos: JSON
    (["en","es"]), lista por comas ("en,es") y un solo idioma ("en")."""
    raw = (raw or "").strip()
    if not raw:
        return []
    if raw.startswith("["):
        import json

        try:
            parsed = json.loads(raw)
        except ValueError:
            return []
        if isinstance(parsed, list):
            return [str(t).strip() for t in parsed if str(t).strip()]
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def _input_path(job_id: str, payload: dict) -> Path | None:
    """Ruta de la entrada guardada, con su extensión real (A2: antes
    se buscaba siempre {job_id}-input.wav aunque fuera .mp3/.mp4)."""
    ext = payload.get("input_ext") or ""
    if ext:
        p = store.audio_dir / f"{job_id}-input.{ext}"
        if p.exists():
            return p
    for p in sorted(store.audio_dir.glob(f"{job_id}-input.*")):
        return p
    return None


def _rebuild_result(job_id: str, tgt: str, payload: dict) -> str:
    """Reconstruye el resultado de un idioma desde sus segmentos
    (A2: editar un segmento actualizaba la tabla pero el audio
    descargado no cambiaba). Devuelve la ruta del resultado."""
    segs = store.list_segments(job_id, language=tgt)
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        timeline = _build_timeline(segs, tmpdir)
        if payload.get("keep_background_audio"):
            media_path = _input_path(job_id, payload)
            if media_path is not None:
                wav_path = _extract_audio(media_path, tmpdir)
                bg, bg_sr = read_audio_bytes(wav_path.read_bytes())
                if bg_sr != TARGET_SR:
                    bg = resample(bg, bg_sr, TARGET_SR)
                n = min(len(timeline), len(bg))
                timeline[:n] += (bg[:n] * 0.15).astype(np.float32)
                timeline = np.clip(timeline, -1.0, 1.0).astype(np.float32)
        out_audio = store.audio_dir / f"{job_id}-{tgt}.wav"
        out_audio.write_bytes(wav_bytes(timeline, TARGET_SR))
        media_path = _input_path(job_id, payload)
        if media_path is not None and _is_video(media_path):
            out_video = store.audio_dir / f"{job_id}-{tgt}.mp4"
            _ffmpeg("-i", str(media_path), "-i", str(out_audio),
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac",
                    "-shortest", str(out_video))
            return str(out_video)
        return str(out_audio)


def _synthesize_segment(text: str, lang: str, ref_path: str, ref_text: str,
                        voice: dict | None) -> tuple[np.ndarray, int]:
    if voice is not None:
        samples, sr = manager.synthesize_qwen_clone(
            text, voice["reference_path"],
            voice.get("reference_text", ""), lang,
        )
        return samples, sr
    return manager.synthesize_qwen_clone(text, ref_path, ref_text, lang)


def _build_timeline(segments: list[dict], tmpdir: Path) -> np.ndarray:
    """Coloca cada segmento sintetizado en su tiempo; resto silencio."""
    total_ms = max((s["end_ms"] for s in segments), default=0)
    total = int(total_ms * TARGET_SR / 1000) + TARGET_SR
    timeline = np.zeros(total, dtype=np.float32)
    for seg in segments:
        audio_path = seg.get("audio_path") or ""
        if not audio_path or not Path(audio_path).exists():
            continue
        samples, sr = read_audio_bytes(Path(audio_path).read_bytes())
        if sr != TARGET_SR:
            samples = resample(samples, sr, TARGET_SR)
        start = int(seg["start_ms"] * TARGET_SR / 1000)
        end = min(start + len(samples), total)
        timeline[start:end] += samples[: end - start]
    return np.clip(timeline, -1.0, 1.0).astype(np.float32)


def _run_dubbing(job_id: str, media_path: Path, is_video_input: bool,
                 source_lang: str, targets: list[str], voice_mode: str,
                 fixed_voice_id: str | None, keep_bg: bool) -> None:
    """Trabajo en segundo plano. Cada fallo queda en jobs.error."""
    try:
        store.update_job(job_id, status="processing", stage="transcribe",
                         progress=0.05)
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            wav_path = _extract_audio(media_path, tmpdir)
            size = "large-v3" if not settings.cpu_only else "small"
            segments, meta = manager.transcribe(
                str(wav_path), source_lang, size, word_timestamps=False
            )
            detected = meta.get("language") or source_lang
            if source_lang == "auto":
                source_lang = detected
            store.update_job(job_id, status="processing",
                             stage="translate", progress=0.3)
            # Referencia para clonar la voz original: primeros 30 s.
            ref_path = tmpdir / "ref.wav"
            _ffmpeg("-i", str(wav_path), "-t", "30", str(ref_path))
            ref_text = " ".join(
                s["text"] for s in segments
                if s["start"] < 30
            ).strip()
            fixed_voice = None
            if voice_mode == "fixed-voice-id" and fixed_voice_id:
                fixed_voice = resolve_voice(fixed_voice_id)
            result_paths: dict[str, str] = {}
            for tgt in targets:
                if tgt == source_lang:
                    raise ValueError(
                        f"Idioma destino igual al origen: {tgt}."
                    )
                # B2: la etapa es "synthesize" (la que espera el
                # frontend), no "synthesize-{tgt}".
                store.update_job(job_id, stage="synthesize",
                                 progress=0.5)
                seg_rows = []
                for i, seg in enumerate(segments):
                    translated = manager.translate(
                        seg["text"], source_lang, tgt
                    )
                    seg_rows.append({
                        "start_ms": int(seg["start"] * 1000),
                        "end_ms": int(seg["end"] * 1000),
                        "speaker": seg.get("speaker") or "",
                        "source_text": seg["text"],
                        "translated_text": translated,
                        "status": "pending",
                    })
                # A1: los segmentos se guardan POR IDIOMA; antes cada
                # idioma borraba los del anterior.
                store.save_segments(job_id, seg_rows, language=tgt)
                for i, seg in enumerate(seg_rows):
                    samples, sr = _synthesize_segment(
                        seg["translated_text"], tgt,
                        str(ref_path), ref_text, fixed_voice,
                    )
                    # El audio del segmento se guarda en audio_dir
                    # (persistente), no en el tmpdir que se borra al
                    # terminar el job: si no, editarlo después (A2)
                    # no podría reconstruir el resultado.
                    seg_audio = (store.audio_dir /
                                 f"{job_id}-{tgt}-seg-{i}.wav")
                    seg_audio.write_bytes(wav_bytes(samples, sr))
                    store.update_segment(
                        job_id, i, language=tgt, status="done",
                        audio_path=str(seg_audio),
                    )
                    store.update_job(
                        job_id, progress=0.5 + 0.4 * (i + 1) / len(seg_rows)
                    )
                store.update_job(job_id, stage="mix", progress=0.92)
                segs = store.list_segments(job_id, language=tgt)
                timeline = _build_timeline(segs, tmpdir)
                if keep_bg:
                    bg, bg_sr = read_audio_bytes(wav_path.read_bytes())
                    if bg_sr != TARGET_SR:
                        bg = resample(bg, bg_sr, TARGET_SR)
                    n = min(len(timeline), len(bg))
                    timeline[:n] += (bg[:n] * 0.15).astype(np.float32)
                    timeline = np.clip(timeline, -1.0, 1.0).astype(np.float32)
                out_audio = store.audio_dir / f"{job_id}-{tgt}.wav"
                out_audio.write_bytes(wav_bytes(timeline, TARGET_SR))
                if is_video_input:
                    out_video = store.audio_dir / f"{job_id}-{tgt}.mp4"
                    _ffmpeg("-i", str(media_path), "-i", str(out_audio),
                            "-map", "0:v:0", "-map", "1:a:0",
                            "-c:v", "copy", "-c:a", "aac",
                            "-shortest", str(out_video))
                    result_paths[tgt] = str(out_video)
                else:
                    result_paths[tgt] = str(out_audio)
                job = store.get_job(job_id) or {}
                payload = dict(job.get("payload") or {})
                payload["result_paths"] = result_paths
                store.update_job(job_id, payload=payload)
            store.update_job(job_id, status="done", stage="done",
                             progress=1.0,
                             result_path=result_paths[targets[0]])
    except Exception as exc:  # noqa: BLE001 - el fallo queda registrado
        store.update_job(job_id, status="failed", stage="failed",
                         error=str(exc)[:1000])


@router.post("/dubbing", status_code=202)
async def create_dubbing(
    media: UploadFile = File(...),
    source_language: str = Form(default="auto"),
    target_languages: str | None = Form(default=None),
    voice_mode: str = Form(default="clone-original"),
    fixed_voice_id: str | None = Form(default=None),
    keep_background_audio: bool = Form(default=True),
    _rl=Depends(limit_heavy),
):
    """Crea un trabajo de doblaje (FEATURE_MAP §9). Devuelve 202 + job_id."""
    # VERIFICACION B5: una cadena vacía NO cae al default "en".
    # El parámetro es None solo cuando NO se envía (default "en");
    # si se envía vacío, el usuario no pidió ningún idioma: 400.
    if target_languages is None:
        target_languages = "en"
    if not target_languages.strip():
        raise HTTPException(
            status_code=400, detail="Falta al menos un idioma destino."
        )
    targets = _parse_targets(target_languages)
    if not targets or len(targets) > 3:
        raise HTTPException(
            status_code=400, detail="Entre 1 y 3 idiomas destino."
        )
    if source_language not in ("auto", "es", "en"):
        raise HTTPException(
            status_code=400,
            detail="Idioma origen admitido: auto, es o en.",
        )
    for tgt in targets:
        if tgt not in ("es", "en"):
            raise HTTPException(
                status_code=422,
                detail=f"Doblaje básico solo cubre es<->en (pedido: {tgt}).",
            )
    if voice_mode not in ("clone-original", "fixed-voice-id"):
        raise HTTPException(status_code=400, detail="voice_mode no admitido.")
    if voice_mode == "fixed-voice-id":
        if not fixed_voice_id:
            raise HTTPException(
                status_code=400,
                detail="fixed-voice-id exige fixed_voice_id.",
            )
        resolve_voice(fixed_voice_id)
    data, ext = await read_upload(
        media, MEDIA_EXTS, settings.max_dubbing_bytes
    )
    job = store.create_job("dubbing", {
        "source_language": source_language,
        "target_languages": targets,
        "voice_mode": voice_mode,
        "fixed_voice_id": fixed_voice_id,
        "keep_background_audio": keep_background_audio,
        "input_ext": ext,
    })
    media_path = store.audio_dir / f"{job['job_id']}-input.{ext}"
    media_path.write_bytes(data)
    thread = threading.Thread(
        target=_run_dubbing,
        args=(job["job_id"], media_path, _is_video(media_path),
              source_language, targets, voice_mode, fixed_voice_id,
              keep_background_audio),
        daemon=True,
    )
    thread.start()
    return {
        "job_id": job["job_id"],
        "status": "queued",
        "stages": ["transcribe", "translate", "synthesize", "mix"],
    }


@router.get("/dubbing/{job_id}")
def get_dubbing(job_id: str):
    job = store.get_job(job_id)
    if not job or job["kind"] != "dubbing":
        raise HTTPException(status_code=404, detail="Trabajo desconocido.")
    payload = job.get("payload") or {}
    return {
        "job_id": job["job_id"],
        # El estado interno es "done"; el frontend lo muestra como
        # "completed" (B2). Se devuelve el interno y el contrato del
        # frontend hace la traducción; no se cambia el valor guardado.
        "status": job["status"],
        "stage": job["stage"],
        "progress": job["progress"],
        "error": job.get("error") or None,
        "segments": store.list_segments(job_id),
        "target_languages": payload.get("target_languages") or [],
        "result_paths": payload.get("result_paths") or {},
    }


@router.post("/dubbing/{job_id}/segments/{n}/edit")
def edit_segment(job_id: str, n: int, req: DubbingSegmentEdit,
                 language: str | None = Query(default=None)):
    """Edita la traducción de un segmento, lo re-sintetiza y
    reconstruye el resultado de ese idioma (A2)."""
    job = store.get_job(job_id)
    if not job or job["kind"] != "dubbing":
        raise HTTPException(status_code=404, detail="Trabajo desconocido.")
    if job["status"] != "done":
        raise HTTPException(
            status_code=409,
            detail="El doblaje aún no terminó; edita cuando esté done.",
        )
    payload = job["payload"]
    targets = payload.get("target_languages") or ["en"]
    tgt = language or targets[0]
    if tgt not in targets:
        raise HTTPException(
            status_code=400,
            detail=f"Idioma {tgt} no es destino de este trabajo.",
        )
    seg = store.update_segment(job_id, n, language=tgt,
                               translated_text=req.translated_text,
                               status="pending")
    if not seg:
        raise HTTPException(status_code=404, detail="Segmento desconocido.")
    try:
        fixed_voice = None
        if payload.get("voice_mode") == "fixed-voice-id":
            fixed_voice = resolve_voice(payload["fixed_voice_id"])
        ref_path = _input_path(job_id, payload)
        if ref_path is None:
            raise HTTPException(
                status_code=404,
                detail="La entrada original del doblaje ya no está.",
            )
        samples, sr = _synthesize_segment(
            req.translated_text, tgt,
            str(ref_path), seg.get("source_text", ""), fixed_voice,
        )
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    seg_audio = store.audio_dir / f"{job_id}-{tgt}-seg-{n}.wav"
    seg_audio.write_bytes(wav_bytes(samples, sr))
    store.update_segment(job_id, n, language=tgt, status="done",
                         audio_path=str(seg_audio))
    # A2: reconstruir el resultado para que la edición se oiga.
    try:
        result = _rebuild_result(job_id, tgt, payload)
    except Exception as exc:  # noqa: BLE001 - el segmento sí se guardó
        return {"job_id": job_id, "segment": n, "status": "done",
                "note": "Segmento re-sintetizado, pero no se pudo "
                f"reconstruir el resultado: {exc}"}
    result_paths = dict(payload.get("result_paths") or {})
    result_paths[tgt] = result
    payload["result_paths"] = result_paths
    store.update_job(job_id, payload=payload,
                     result_path=result_paths[targets[0]])
    return {"job_id": job_id, "segment": n, "status": "done",
            "note": "Segmento re-sintetizado y resultado reconstruido. "
            "Descarga de nuevo para oír el cambio."}


@router.get("/dubbing/{job_id}/download")
def download_dubbing(job_id: str,
                     language: str = Query(default="en"),
                     format: str = Query(default="mp3", pattern=r"^(mp3|wav|mp4)$")):
    job = store.get_job(job_id)
    if not job or job["kind"] != "dubbing":
        raise HTTPException(status_code=404, detail="Trabajo desconocido.")
    if job["status"] != "done":
        raise HTTPException(
            status_code=409,
            detail=f"El doblaje está en {job['status']}; espera a done.",
        )
    # A1: el resultado es POR IDIOMA; antes solo quedaba el último.
    payload = job.get("payload") or {}
    result_paths = payload.get("result_paths") or {}
    result = Path(result_paths.get(language) or job.get("result_path") or "")
    if not result_paths and language not in (
            payload.get("target_languages") or ["en"]):
        raise HTTPException(
            status_code=400,
            detail=f"Idioma {language} no es destino de este trabajo.",
        )
    if format == "mp4":
        if result.suffix.lower() != ".mp4":
            raise HTTPException(
                status_code=400,
                detail="La entrada era audio, no vídeo: pide mp3 o wav.",
            )
        return FileResponse(result, media_type="video/mp4")
    audio = result.with_suffix(".wav")
    if not audio.exists():
        raise HTTPException(status_code=404, detail="Resultado no encontrado.")
    if format == "wav":
        return FileResponse(audio, media_type="audio/wav")
    return Response(content=wav_to_mp3(audio.read_bytes()),
                    media_type="audio/mpeg")
