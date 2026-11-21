"""History (§16) + contador de uso + verificación por transcripción.

Verificación (método establecido, AGENTS.md 2026-10-19): el audio
generado se transcribe con faster-whisper y se compara contra el
texto esperado NORMALIZADO (minúsculas, sin tildes ni puntuación),
porque Whisper normaliza grafías fonéticas al transcribir. El
endpoint POST /history/{id}/verify deja esa comparación lista para
la auditoría: devuelve el texto transcrito normalizado, el WER por
palabra y el veredicto. No afirma que el audio sea correcto: muestra
la evidencia.
"""

import re
import unicodedata
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from ..engines import ModelUnavailable, manager
from ..security import require_auth
from ..store import store

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_auth)])


def normalize_text(text: str) -> str:
    """Normalización para comparar: minúsculas, sin tildes, sin puntuación."""
    lowered = text.lower()
    no_accents = "".join(
        c for c in unicodedata.normalize("NFD", lowered)
        if unicodedata.category(c) != "Mn"
    )
    no_punct = re.sub(r"[^\w\s]", " ", no_accents)
    return re.sub(r"\s+", " ", no_punct).strip()


def word_error_rate(expected: str, got: str) -> dict:
    """WER por distancia de Levenshtein a nivel de palabra."""
    exp = expected.split()
    got_words = got.split()
    n, m = len(exp), len(got_words)
    if n == 0:
        return {"wer": 0.0 if m == 0 else 1.0, "matched": 0, "total": 0}
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if exp[i - 1] == got_words[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    edits = prev[m]
    matched = sum(1 for w in got_words if w in exp)
    return {
        "wer": round(edits / n, 3),
        "matched": matched,
        "total": n,
        "edits": edits,
    }


@router.get("/history")
def list_history(
    voice_id: str | None = Query(default=None),
    from_date: str | None = Query(default=None, alias="from"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    total, items = store.list_history(voice_id, from_date, limit, offset)
    for item in items:
        item["audio_url"] = f"/api/v1/history/{item['id']}/audio"
    return {"total": total, "items": items}


@router.get("/history/{gen_id}/audio")
def history_audio(gen_id: str, track: str | None = Query(default=None)):
    item = store.get_history(gen_id)
    if not item:
        raise HTTPException(status_code=404, detail="Generación desconocida.")
    path = item.get("audio_path") or ""
    if track == "background" and path:
        bg = Path(path).with_name(
            Path(path).name.replace("-vocals.wav", "-background.wav")
        )
        if bg.exists():
            path = str(bg)
    if not path or not Path(path).exists():
        raise HTTPException(
            status_code=404,
            detail="El audio de esa generación ya no está en el servidor.",
        )
    media = ("audio/mpeg" if item.get("audio_format") == "mp3"
             else "audio/wav")
    return FileResponse(path, media_type=media)


@router.delete("/history/{gen_id}")
def delete_history(gen_id: str):
    if not store.delete_history(gen_id):
        raise HTTPException(status_code=404, detail="Generación desconocida.")
    return {"deleted": True, "id": gen_id}


@router.get("/usage")
def usage():
    """Contador de uso (equivalente local de los créditos, §16/§25)."""
    return store.usage()


@router.post("/history/{gen_id}/verify")
def verify_history(gen_id: str):
    """Verifica un audio generado: lo transcribe y lo compara con el
    texto esperado normalizado. Para audios sin texto esperado (SFX,
    isolate) devuelve 422."""
    item = store.get_history(gen_id)
    if not item:
        raise HTTPException(status_code=404, detail="Generación desconocida.")
    expected = (item.get("text") or "").strip()
    if not expected:
        raise HTTPException(
            status_code=422,
            detail="Esa generación no tiene texto esperado (no es TTS).",
        )
    path = item.get("audio_path") or ""
    if not path or not Path(path).exists():
        raise HTTPException(
            status_code=404,
            detail="El audio de esa generación ya no está en el servidor.",
        )
    try:
        # M2: el modelo se elige por pertenencia explícita a un
        # conjunto, no por prefijo ("qwen..."): un modelo futuro
        # que empiece por "qwen" no debe heredar large-v3 a ciegas.
        qwen_models = {"qwen3-tts-1.7b", "qwen3-tts-0.6b",
                       "qwen3-tts-1.7b-customvoice"}
        size = "large-v3" if item.get("model") in qwen_models else "small"
        segments, _meta = manager.transcribe(
            path, None, size, word_timestamps=False
        )
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    transcribed = " ".join(s["text"] for s in segments).strip()
    exp_norm = normalize_text(expected)
    got_norm = normalize_text(transcribed)
    wer = word_error_rate(exp_norm, got_norm)
    return {
        "id": gen_id,
        "expected": expected,
        "expected_normalized": exp_norm,
        "transcribed": transcribed,
        "transcribed_normalized": got_norm,
        "wer": wer["wer"],
        "matched_words": wer["matched"],
        "total_words": wer["total"],
        "verdict": (
            "ok" if wer["wer"] <= 0.15 else
            "revisar" if wer["wer"] <= 0.35 else "fallo"
        ),
        "note": "Comparación normalizada (minúsculas, sin tildes ni "
        "puntuación): Whisper normaliza grafías fonéticas.",
    }
