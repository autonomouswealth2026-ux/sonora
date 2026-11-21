"""Tests del backend (pytest). Sin GPU ni modelos instalados.

Criterio verificable (Karpathy + superpowers): cada endpoint debe
responder con el código correcto en su camino de error — 400/422 de
validación, 404 de desconocido, 501 de fase 3-4, 503 sin motor — y el
CRUD del diccionario y de voces debe funcionar contra SQLite real.
Los endpoints que exigen motor devuelven 503 aquí; en Kaggle con GPU
deben devolver audio (ver PENDIENTES_KAGGLE.md).

Ejecutar:  python -m pytest tests/ -v

Entorno: la suite espera NO tener motores instalados (venv sonora-base):
los endpoints que exigen motor deben devolver 503. En el venv sonora
(con Kokoro instalado) 5 tests fallan por diseño: el motor carga y
devuelve 200 con audio real en vez del 503 esperado. Eso no es un
defecto del producto; es la suite asumiendo "sin motores".
"""

import io
import os
import struct
import tempfile

# Aislar la base de datos ANTES de importar la app (store se crea al importar).
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="elclon-test-")
os.environ["API_TOKEN"] = ""
os.environ["CPU_ONLY"] = "1"
# Sin esto la suite da 8 fallos por el limitador global en memoria
# (AUDIT2 N1): los límites altos pertenecen a la suite, no al despliegue.
os.environ["RATE_LIMIT_PER_MINUTE"] = "10000"
os.environ["HEAVY_RATE_LIMIT_PER_MINUTE"] = "10000"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.routers.history import normalize_text, word_error_rate  # noqa: E402
from app.security import RateLimiter  # noqa: E402
from app.store import store  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)


def make_wav(seconds: float = 5.0, sr: int = 16000) -> bytes:
    """WAV mono 16 bits con un tono, generado con la stdlib."""
    n = int(seconds * sr)
    frames = b"".join(struct.pack("<h", int(8000 * (i % 100 < 50) * 2 - 8000))
                      for i in range(n))
    buf = io.BytesIO()
    import wave

    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(frames)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Sistema
# ---------------------------------------------------------------------------

def test_root_and_docs():
    assert client.get("/").status_code == 200
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_health_reports_no_models_loaded():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["models_loaded"] == []
    assert body["gpu"] is False  # CPU_ONLY=1 en este entorno de test
    assert client.get("/api/v1/health").status_code == 200


def test_models_lists_registry():
    r = client.get("/api/v1/models")
    assert r.status_code == 200
    names = {m["model"] for m in r.json()["models"]}
    assert "kokoro" in names
    assert "qwen3-tts-1.7b" in names
    assert "voxcpm2" in names
    assert all(m["loaded"] is False for m in r.json()["models"])


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------

def test_tts_validation():
    assert client.post("/api/v1/tts", json={"text": "", "voice_id": "ef_dora"}).status_code == 422
    assert client.post("/api/v1/tts", json={"text": "x" * 10001, "voice_id": "ef_dora"}).status_code == 422
    assert client.post("/api/v1/tts", json={"text": "hola", "voice_id": "ef_dora", "speed": 9}).status_code == 422
    assert client.post("/api/v1/tts", json={"text": "hola", "voice_id": "ef_dora", "format": "ogg"}).status_code == 422


def test_tts_unknown_voice_404():
    r = client.post("/api/v1/tts", json={"text": "hola", "voice_id": "no_existe"})
    assert r.status_code == 404


def test_tts_without_engine_503():
    # Kokoro no instalado en este entorno: 503 con mensaje claro.
    r = client.post("/api/v1/tts", json={"text": "hola", "voice_id": "ef_dora"})
    assert r.status_code == 503
    assert "kokoro" in r.json()["detail"].lower()


def test_tts_stream_without_engine_503():
    r = client.post("/api/v1/tts/stream", json={"text": "hola", "voice_id": "ef_dora"})
    assert r.status_code == 503


def test_openai_compat():
    r = client.post("/api/v1/audio/speech",
                    json={"model": "nope", "input": "hola", "voice": "ef_dora"})
    assert r.status_code == 400
    r = client.post("/api/v1/audio/speech",
                    json={"model": "kokoro", "input": "hola", "voice": "ef_dora"})
    assert r.status_code == 503


def test_tts_voices_lists_fixed():
    r = client.get("/api/v1/tts/voices")
    assert r.status_code == 200
    ids = {v["voice_id"] for v in r.json()["voices"]}
    assert "ef_dora" in ids and "em_alex" in ids and "Ryan" in ids


# ---------------------------------------------------------------------------
# Voces: clonación y diseño
# ---------------------------------------------------------------------------

def test_instant_clone_requires_consent():
    files = {"audio": ("ref.wav", make_wav(5), "audio/wav")}
    r = client.post("/api/v1/voices/instant-clone", files=files,
                    data={"name": "Prueba"})
    assert r.status_code == 422  # falta consent_note


def test_instant_clone_rejects_short_sample():
    files = {"audio": ("ref.wav", make_wav(1), "audio/wav")}
    r = client.post("/api/v1/voices/instant-clone", files=files,
                    data={"name": "Prueba",
                          "consent_note": "Yo mismo autorizo clonar mi voz."})
    assert r.status_code == 400


def test_instant_clone_registers_voice_without_engine():
    files = {"audio": ("ref.wav", make_wav(5), "audio/wav")}
    r = client.post("/api/v1/voices/instant-clone", files=files,
                    data={"name": "Voz Prueba",
                          "consent_note": "Yo mismo autorizo clonar mi voz."})
    assert r.status_code == 201, r.text
    voice_id = r.json()["voice_id"]
    assert r.json()["model"] == "qwen3-tts-1.7b"
    # La preview exige GPU: 503.
    assert client.get(f"/api/v1/voices/{voice_id}/preview").status_code == 503
    # Borrar dos veces: 200 y luego 404.
    assert client.delete(f"/api/v1/voices/{voice_id}").status_code == 200
    assert client.delete(f"/api/v1/voices/{voice_id}").status_code == 404


def test_delete_fixed_voice_400():
    assert client.delete("/api/v1/voices/ef_dora").status_code == 400


def test_voice_design_validation_and_503():
    r = client.post("/api/v1/voices/design",
                    json={"prompt": "corto", "language": "es"})
    assert r.status_code == 422
    r = client.post("/api/v1/voices/design",
                    json={"prompt": "Voz femenina, 30 años, cálida y clara.",
                          "language": "es", "num_previews": 4})
    assert r.status_code == 422
    r = client.post("/api/v1/voices/design",
                    json={"prompt": "Voz femenina, 30 años, cálida y clara.",
                          "language": "es"})
    assert r.status_code == 503


def test_library_and_favorite():
    assert client.get("/api/v1/library/voices").status_code == 200
    assert client.get("/api/v1/library/voices?language=es").status_code == 200
    assert client.post("/api/v1/library/voices/no_existe/favorite").status_code == 404


# ---------------------------------------------------------------------------
# STT / align / isolate / efectos
# ---------------------------------------------------------------------------

def test_stt_validation_and_503():
    files = {"audio": ("a.wav", make_wav(2), "audio/wav")}
    r = client.post("/api/v1/stt", files=files, data={"model": "nope"})
    assert r.status_code == 400
    r = client.post("/api/v1/stt", files=files, data={"model": "small"})
    assert r.status_code == 503  # faster-whisper no instalado aquí
    assert client.post("/api/v1/stt").status_code == 422


def test_align_requires_transcript():
    files = {"audio": ("a.wav", make_wav(2), "audio/wav")}
    assert client.post("/api/v1/align", files=files).status_code == 422


def test_isolate_denoise_501_and_bad_mode_400():
    files = {"audio": ("a.wav", make_wav(2), "audio/wav")}
    r = client.post("/api/v1/isolate", files=files, data={"mode": "denoise"})
    assert r.status_code == 501
    r = client.post("/api/v1/isolate", files=files, data={"mode": "otro"})
    assert r.status_code == 400
    r = client.post("/api/v1/isolate", files=files, data={"mode": "demucs"})
    assert r.status_code == 503


def test_audio_effects_catalog_and_validation():
    r = client.get("/api/v1/audio-effects/catalog")
    assert r.status_code == 200
    assert "telephone" in r.json()["presets"]["filter_preset"]
    files = {"audio": ("a.wav", make_wav(2), "audio/wav")}
    r = client.post("/api/v1/audio-effects/apply", files=files,
                    data={"reverb": "catedral"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Diccionario de pronunciación
# ---------------------------------------------------------------------------

def test_pronunciation_crud():
    r = client.post("/api/v1/pronunciation",
                    json={"word": "Valdestudio", "replacement": "bal-des-TU-dio"})
    assert r.status_code == 201
    rule_id = r.json()["rule_id"]
    items = client.get("/api/v1/pronunciation").json()["rules"]
    assert any(x["rule_id"] == rule_id for x in items)
    r = client.put(f"/api/v1/pronunciation/{rule_id}",
                   json={"replacement": "baldes-TU-dio"})
    assert r.status_code == 200
    assert r.json()["replacement"] == "baldes-TU-dio"
    assert client.put("/api/v1/pronunciation/no_existe",
                      json={"replacement": "x"}).status_code == 404
    assert client.delete(f"/api/v1/pronunciation/{rule_id}").status_code == 200
    assert client.delete(f"/api/v1/pronunciation/{rule_id}").status_code == 404


def test_pronunciation_import_export():
    bad = client.post("/api/v1/pronunciation/import",
                      files={"file": ("x.pls", b"esto no es xml", "text/xml")})
    assert bad.status_code == 400
    pls = ('<?xml version="1.0"?><lexicon version="1.0" '
           'xmlns="http://www.w3.org/2005/01/pronunciation-lexicon" '
           'alphabet="ipa" xml:lang="es-ES">'
           '<lexeme><grapheme>UCLV</grapheme>'
           '<alias>u-ce-ele-uve</alias></lexeme></lexicon>')
    r = client.post("/api/v1/pronunciation/import",
                    files={"file": ("d.pls", pls.encode(), "text/xml")})
    assert r.status_code == 200 and r.json()["imported"] == 1
    r = client.get("/api/v1/pronunciation/export")
    assert r.status_code == 200 and "UCLV" in r.text


# ---------------------------------------------------------------------------
# Historial, uso y verificación
# ---------------------------------------------------------------------------

def test_history_empty_usage_and_404s():
    assert client.get("/api/v1/history").json()["total"] == 0
    u = client.get("/api/v1/usage").json()
    assert u["total_characters"] == 0 and u["total_minutes"] == 0
    assert client.get("/api/v1/history/gen_nope/audio").status_code == 404
    assert client.delete("/api/v1/history/gen_nope").status_code == 404
    assert client.post("/api/v1/history/gen_nope/verify").status_code == 404


def test_verify_rejects_non_tts_entry():
    item = store.add_history(id="gen_sfx1", type="sfx", text="", voice_id="",
                             model="stable-audio-open-1.0", duration_s=5,
                             characters=0, audio_path="", audio_format="mp3")
    r = client.post(f"/api/v1/history/{item['id']}/verify")
    assert r.status_code == 422


def test_normalize_and_wer():
    assert normalize_text("¡Hola, Valdestudio! ¿Qué tal?") == "hola valdestudio que tal"
    assert normalize_text("ÁÉÍÓÚ ü") == "aeiou u"
    wer = word_error_rate("hola mundo cruel", "hola mundo cruel")
    assert wer["wer"] == 0.0 and wer["matched"] == 3
    wer = word_error_rate("hola mundo cruel", "hola mundo")
    assert wer["wer"] == round(1 / 3, 3)


# ---------------------------------------------------------------------------
# SFX / STS / Dubbing
# ---------------------------------------------------------------------------

def test_sfx_validation_and_503():
    assert client.post("/api/v1/sfx", json={"prompt": ""}).status_code == 422
    assert client.post("/api/v1/sfx", json={"prompt": "lluvia",
                                            "duration_s": 99}).status_code == 422
    r = client.post("/api/v1/sfx", json={"prompt": "puerta que chirría",
                                         "duration_s": 5})
    assert r.status_code == 503


def test_sts_voice_conversion_501_and_unknown_voice_404():
    files = {"audio": ("a.wav", make_wav(2), "audio/wav")}
    r = client.post("/api/v1/speech-to-speech", files=files,
                    data={"target_voice_id": "ef_dora",
                          "method": "voice-conversion"})
    assert r.status_code == 501
    r = client.post("/api/v1/speech-to-speech", files=files,
                    data={"target_voice_id": "no_existe",
                          "method": "stt-tts"})
    assert r.status_code == 404


def test_dubbing_validation_and_404s():
    files = {"media": ("a.wav", make_wav(2), "audio/wav")}
    r = client.post("/api/v1/dubbing", files=files,
                    data={"target_languages": "fr"})
    assert r.status_code == 422
    r = client.post("/api/v1/dubbing", files=files,
                    data={"target_languages": ""})
    assert r.status_code == 400
    assert client.get("/api/v1/dubbing/job_nope").status_code == 404
    assert client.get("/api/v1/dubbing/job_nope/download").status_code == 404


# ---------------------------------------------------------------------------
# Fases 3-4 y no replicables: 501 honesto
# ---------------------------------------------------------------------------

def test_phase_3_4_return_501():
    assert client.post("/api/v1/dialogue", json={"lines": []}).status_code == 501
    assert client.post("/api/v1/voices/pro-clone").status_code == 501
    assert client.get("/api/v1/voices/pro-clone/job_x").status_code == 501
    assert client.post("/api/v1/voices/ef_dora/remix", json={}).status_code == 501
    assert client.post("/api/v1/music", json={}).status_code == 501
    assert client.get("/api/v1/music/job_x").status_code == 501
    assert client.post("/api/v1/projects", json={"title": "Libro"}).status_code == 501
    assert client.get("/api/v1/projects").status_code == 501
    assert client.get("/api/v1/projects/p1").status_code == 501
    assert client.post("/api/v1/reader/upload").status_code == 501
    assert client.post("/api/v1/agents", json={}).status_code == 501
    assert client.get("/api/v1/realtime").status_code == 501
    assert client.get("/api/v1/realtime-translation").status_code == 501
    assert client.get("/api/v1/elevenai").status_code == 501


def test_stt_stream_websocket_closes_1011():
    from starlette.websockets import WebSocketDisconnect

    with client.websocket_connect("/api/v1/stt/stream") as ws:
        try:
            ws.receive_text()
            raise AssertionError("el WebSocket debió cerrarse")
        except WebSocketDisconnect as exc:
            assert exc.code == 1011


def test_rate_limiter_unit():
    limiter = RateLimiter()
    for _ in range(3):
        limiter.check("1.2.3.4", "test", 3)
    try:
        limiter.check("1.2.3.4", "test", 3)
        raise AssertionError("debió lanzar 429")
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, "status_code", None) == 429


# ---------------------------------------------------------------------------
# Añadidos en la corrección 2026-11-20 (AUDIT.md): auth, CORS,
# rate-limit del middleware, contrato de doblaje y rechazos honestos
# ---------------------------------------------------------------------------

def test_auth_401_without_token():
    # A9: la autenticación nunca se había probado (ningún test 401).
    from app.config import settings

    anterior = settings.api_token
    settings.api_token = "secreto-prueba"
    try:
        r = client.get("/api/v1/history")
        assert r.status_code == 401
        r = client.get("/api/v1/history",
                       headers={"Authorization": "Bearer secreto-prueba"})
        assert r.status_code == 200
    finally:
        settings.api_token = anterior


def test_cors_allows_localhost_blocks_unknown():
    # B6: preflight desde localhost (desarrollo) permitido; desde un
    # origen desconocido, sin cabecera allow-origin.
    r = client.options("/api/v1/models", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"
    r = client.options("/api/v1/models", headers={
        "Origin": "https://origen-desconocido.example",
        "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in r.headers


def test_rate_limit_middleware_returns_429_json():
    # A15: el middleware ya no deja subir la HTTPException como 500.
    from app.config import settings
    from app.security import limiter

    anterior = settings.rate_limit_per_minute
    settings.rate_limit_per_minute = 2
    limiter._hits.clear()
    try:
        assert client.get("/api/v1/models").status_code == 200
        assert client.get("/api/v1/models").status_code == 200
        r = client.get("/api/v1/models")
        assert r.status_code == 429
        assert "detail" in r.json()
    finally:
        settings.rate_limit_per_minute = anterior
        limiter._hits.clear()


def test_dubbing_accepts_json_target_languages():
    # B1: el frontend mandaba ["en"] como JSON y el backend lo partía
    # por comas -> 422 siempre. Ahora JSON, comas y un solo idioma valen.
    files = {"media": ("a.wav", make_wav(2), "audio/wav")}
    r = client.post("/api/v1/dubbing", files=files,
                    data={"target_languages": '["en"]'})
    assert r.status_code == 202, r.text
    assert r.json()["status"] == "queued"
    files = {"media": ("a.wav", make_wav(2), "audio/wav")}
    r = client.post("/api/v1/dubbing", files=files,
                    data={"target_languages": "en"})
    assert r.status_code == 202, r.text


def test_design_preview_rejects_traversal():
    # A13: candidate_id con ../ ya no sale de voices_dir.
    r = client.get("/api/v1/voices/design/%2E%2E%2Fsecreto/preview")
    assert r.status_code == 404
    r = client.get("/api/v1/voices/design/cand_noexiste/preview")
    assert r.status_code == 404


def test_tts_rejects_unknown_language_code():
    # A16: "xx" ya no sintetiza en español en silencio.
    r = client.post("/api/v1/tts", json={"text": "hola", "voice_id": "ef_dora",
                                         "language": "xx"})
    assert r.status_code == 422


def test_tts_kokoro_rejects_unsupported_language():
    # A5: Kokoro no tiene alemán; antes caía al pipeline inglés.
    r = client.post("/api/v1/tts", json={"text": "hola", "voice_id": "ef_dora",
                                         "language": "de"})
    assert r.status_code == 400


def test_tts_similarity_rejected_for_cloned_voice():
    # B4: similarity no existe en ningún motor; se rechaza con 422.
    files = {"audio": ("ref.wav", make_wav(5), "audio/wav")}
    r = client.post("/api/v1/voices/instant-clone", files=files,
                    data={"name": "Voz Sim",
                          "consent_note": "Yo mismo autorizo clonar mi voz."})
    assert r.status_code == 201, r.text
    voice_id = r.json()["voice_id"]
    try:
        r = client.post("/api/v1/tts", json={
            "text": "hola", "voice_id": voice_id, "similarity": 0.8})
        assert r.status_code == 422
    finally:
        client.delete(f"/api/v1/voices/{voice_id}")


def test_webm_accepted_as_audio_extension():
    # B7: la grabación del navegador es .webm.
    from app.security import AUDIO_EXTS

    assert "webm" in AUDIO_EXTS


def test_stt_stream_websocket_rejects_without_token():
    # VERIFICACION B2: con token fijado, el WS sin token cierra 1008
    # (antes moría con TypeError antes de cerrarse).
    from app.config import settings

    anterior = settings.api_token
    settings.api_token = "secreto-prueba"
    from starlette.websockets import WebSocketDisconnect

    try:
        # El cierre 1008 llega al conectar, antes de entrar al with.
        with client.websocket_connect("/api/v1/stt/stream") as ws:
            ws.receive_text()
        raise AssertionError("el WebSocket debió cerrarse al conectar")
    except WebSocketDisconnect as exc:
        assert exc.code == 1008
    finally:
        settings.api_token = anterior
