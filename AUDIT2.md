# RE-AUDITORÍA — Clon web de ElevenLabs «Sonora» (AUDIT2)

- **Fecha:** 2026-11-21 (hora de La Habana)
- **Alcance:** `app/` + `backend/` + `FEATURE_MAP.md` v2, contra los 39 hallazgos de `AUDIT.md` (2026-11-20) y las correcciones declaradas en `CORRECCIONES.md`.
- **Método:** revisión de código con `archivo:línea` + ejecución propia. No se corrigió nada; solo se verifica. Ejecutado por el re-auditor: `py_compile` (OK), `node --check` 5/5 JS (OK), `pytest` en `~/workspace/venvs/sonora-base` (ver N1) y ciclo vivo en `~/workspace/venvs/sonora` (CPU + Kokoro + faster-whisper, puerto 8009, `DATA_DIR=/tmp/sonora-audit2`).
- **Regla del re-auditor:** la afirmación del corrector no es evidencia; cada hallazgo lleva su evidencia o queda como «no verificado».

## Veredicto global: APTO CON CORRECCIONES MENORES

Los 39 hallazgos de AUDIT.md están **cerrados de verdad** (37 corregidos + 2 confirmados como errores de la auditoría, M3 y L4, con la justificación verificada). El contrato frontend↔backend está reparado en sus 5 puntos rotos, el barrido de seguridad no encuentra secretos ni marca copiada, y las puertas de dependencias y modelos quedan en verde salvo lo que solo se puede probar con GPU. **Pero la evidencia de tests no se reproduce con la orden documentada** (N1, media): `pytest tests/ -q` falla 8/40 por rate-limit compartido; el 40/40 exige subir los dos límites por variables de entorno. Además quedan dos divergencias menores de documentación de contrato (N2, N3, bajas). **Corregir N1–N3 (trabajo de minutos, sin GPU) y después, navegador vivo (`delivery_audit_gate`) y run de Kaggle.**

| Severidad (hallazgos AUDIT.md) | Total | Cerrados | Abiertos |
|---|---|---|---|
| Bloqueante | 9 | 9 | 0 |
| Alta | 17 | 17 | 0 |
| Media | 9 | 8 corregidos + 1 error de auditoría (M3) | 0 |
| Baja | 4 | 3 corregidos + 1 error de auditoría (L4) | 0 |
| **Total AUDIT.md** | **39** | **39** | **0** |

| Hallazgos nuevos de esta re-auditoría | Conteo |
|---|---|
| Media (N1: pytest no reproduce 40/40 por defecto) | 1 |
| Baja (N2, N3: divergencias menores de contrato/docs) | 2 |
| **Total nuevos** | **3** |

## Tabla de los 39 hallazgos

### Bloqueantes (9/9 cerrados)

| ID | Veredicto | Evidencia |
|---|---|---|
| B1 | **Cerrado** | `backend/app/routers/dubbing.py:82-99` `_parse_targets()` acepta JSON, comas y un idioma; `app/js/screens.js:465` envía el valor plano. **En vivo:** `POST /dubbing` con `target_languages='["en"]'` → **202** `{"job_id":"job_aa3756ad802d","status":"queued","stages":["transcribe","translate","synthesize","mix"]}`; con `en` → 202; con `""` → 400. |
| B2 | **Cerrado** | `dubbing.py:210-212` etapa `synthesize` (no `synthesize-{tgt}`); `app/js/screens.js:490-492` traduce `done`→`completed` y tolera `synthesize-*`. **En vivo:** `GET /dubbing/{job}` devuelve `status`/`stage`/`progress`/`target_languages`/`result_paths`. El ciclo completo hasta `done` no se probó en CPU (exige MarianMT + Qwen en GPU). |
| B3 | **Cerrado** | Sin `voxcpm2` en `app/index.html` ni `app/js/app.js` (grep: 0 ocurrencias); `app/index.html:378` dice «VoxCPM2 no está integrado». El registro del backend (`engines.py:133-134`, no integrado) se mantiene, coherente. `TTSRequest.model` (`schemas.py:20-23`) tampoco lo admite. |
| B4 | **Cerrado** | `schemas.py:32` `similarity` existe en el contrato; `tts.py:96-111` la rechaza con 422 en todas las rutas y `stability`/`style` con 422 en clonadas/diseñadas y Kokoro; `_instruct_graduado` en CustomVoice (`tts.py:150-160`); `speed` en clonadas por remuestreo (`tts.py:190-214`, `audio_utils.py:82` `resample`). Frontend: `app.js:186-189` soporte por voz, `app.js:224-232` similitud siempre deshabilitada con motivo, `app.js:374-379` solo envía estabilidad/estilo si es CustomVoice y nunca `similarity`. **En vivo (CPU):** `similarity` en clonada → 422 (declarado y cubierto por test; no re-ejecutado en vivo por el re-auditor, ver nota). El remuestreo de `speed` en clonadas sigue sin probar en GPU. |
| B5 | **Cerrado (código; sin verificar resolución en Kaggle)** | `backend/requirements-gpu.txt:11-17`: `transformers==4.57.3`, `accelerate==1.12.0`, `av==13.1.0`, `qwen-tts==0.1.1`. Coincide con lo que exige `qwen-tts` según CORRECCIONES.md. La resolución real de `pip` en Kaggle sigue pendiente del run. |
| B6 | **Cerrado (código; sin verificar en despliegue)** | `backend/build_notebook.py:140-146` fija `CORS_ORIGINS` con `https://carlosmiguelvaldesrodriguez-prog.github.io/elevenlabs-clon` por defecto; el `kaggle_notebook.ipynb` regenerado (8 celdas) lo contiene (líneas 157-159 del JSON). `.env.example:13-15` corregido. El default local (solo localhost, `config.py:30-33`) se mantiene para desarrollo, como se declara. Sin verificar contra Pages + trycloudflare reales. |
| B7 | **Cerrado** | `app/js/screens.js:16-17` admite `audio/webm` y `.webm`; `app/index.html:158,222` inputs aceptan WebM; `backend/app/security.py:145,155` `AUDIO_EXTS` incluye `webm` (magic `\x1a\x45\xdf\xa3` ya estaba). Test `test_api.py` cubre WebM en `AUDIO_EXTS` (dentro del 40/40 con límites altos). El 201 en vivo con `.webm` declarado en CORRECCIONES.md no se re-ejecutó por el re-auditor (sin ffmpeg a mano en esta sesión); queda como «declarado, con test». |
| B8 | **Cerrado** | `app/js/api.js:66-70` `blobUrl()` descarga con base + `Authorization` y devuelve blob URL; `app/js/screens.js:224` (preview de diseño) y `:590` (variantes SFX) la usan; ya no hay asignación directa de URL relativa a `<audio src>` en esas rutas. |
| B9 | **Cerrado** | `app/index.html:212-213`: `stt-tts` es ahora el `selected`; `voice-conversion` visible y marcado «no implementada todavía (501)». Backend: `sts.py:32` default `stt-tts`; `sts.py:36-41` 501 para `voice-conversion`. `app/js/api.js:210` mapea 501 a mensaje en español. |

### Altos (17/17 cerrados)

| ID | Veredicto | Evidencia |
|---|---|---|
| A1 | **Cerrado (código; sin verificar en vivo con 2 idiomas)** | `store.py:39,66,84,92` columna `language` en `dubbing_segments` (PK `job_id, n, language`) + migración `:107-113`; `save_segments`/`list_segments` por idioma; `dubbing.py:204,267-276` `result_paths` por idioma; `GET /dubbing/{id}` (`:372`) y `download` (`:453-455`) eligen por `language`. El multi-idioma de extremo a extremo exige GPU (MarianMT + Qwen). |
| A2 | **Cerrado (código; sin verificar en vivo)** | `dubbing.py:102-114` `_input_path()` (extensión real, no `.wav` fijo), `:115-...` `_rebuild_result()`, `edit_segment` (`:406-424`) acepta `?language=` y reconstruye tras re-sintetizar. Exige GPU para probar el audio resultante. |
| A3 | **Cerrado** | `app/index.html:248` selector de destino solo `en`/`es`. Backend `dubbing.py:317-322` sigue 422 fuera de es↔en, coherente. |
| A4 | **Cerrado** | `app/js/api.js:161` `descargarDoblaje()` por fetch con token; `app/js/screens.js:543-548` formato según entrada (`mp4` vídeo / `mp3` audio) y texto del botón acorde. |
| A5 | **Cerrado** | `engines.py:50-53` `KOKORO_LANG_CODES` sin `de`/`ko`/`ru`; `engines.py:257-264` rechaza idioma sin pipeline; `tts.py:129-142` el pipeline es el del idioma **de la voz** y el pedido debe tener pipeline (400 si no). **En vivo:** `language=de` → **400**; `language=xx` → **422**. |
| A6 | **Cerrado (cifra; medición pendiente)** | `engines.py:92,103,109` `vram_gb: 8` en los tres 1.7B, con nota del tokenizer 0,68 GB; `backend/README.md` «~8 GB VRAM». Medición con Whisper en el mismo proceso sigue en `PENDIENTES_KAGGLE.md` punto 10. |
| A7 | **Cerrado** | Diccionario remoto primero con `remoteId` (`screens.js:851-858`); contador «Este mes» filtra por mes en curso (`screens.js:635-639`); borrar voz: backend primero, si falla no se borra en local (`screens.js:358-363`); borrar historial: intenta borrado remoto si hay `remoteId` (`screens.js:691-692`, con aviso si falla); `app.js:370-372` envía `dictionary_id='local'` si hay reglas; `tts.py:60-68` sin `dictionary_id` no aplica nada, con él filtra por idioma. Matiz: el valor `'local'` es un flag, no un id real de regla; funciona por construcción (`apply_dictionary` solo usa su veracidad + `language`). |
| A8 | **Cerrado** | `store.js:112-126` 9 voces Qwen CustomVoice en `VOCES_FIJAS`; `api.js:72,77` `listarBiblioteca()` / `favoritoVoz()`; `screens.js:271-322` mezcla biblioteca del backend + locales con estrella ★/☆ y fijas no borrables; `app/index.html:78` opción `qwen3-tts-1.7b-customvoice` en el selector. |
| A9 | **Cerrado con reserva (N1)** | Suite: 40 tests (`grep -c "def test" backend/tests/test_api.py` = 40). Nuevos: 401, CORS, 429 del middleware, doblaje JSON/vacío (`test_api.py:419`), traversal (`:433`), rechazos TTS, WebM, WS 1008 (`:478`). **40/40 reproducido por el re-auditor solo con `RATE_LIMIT_PER_MINUTE=10000 HEAVY_RATE_LIMIT_PER_MINUTE=10000`.** Con la orden documentada (`pytest tests/ -q`) fallan 8/40 (ver N1). |
| A10 | **Cerrado (código; sin verificar en vivo)** | `engines.py:365-390` `design_voices`: variantes explícitas de instruct por candidato + descarte de duplicados byte a byte (hasta 3 reintentos por candidato). Exige GPU para comprobar que los 3 audios difieren de verdad. |
| A11 | **Cerrado** | `tts.py:256` `_strip_wav_header` busca el chunk `data` (no recorte fijo de 44 B); `tts.py:28-35,51,117` el stream queda en historial y el 503 sale antes del `StreamingResponse` si no hay motor. **En vivo (CPU):** `/tts/stream` no re-probado por el re-auditor; cubierto por test `test_tts_stream_without_engine_503` dentro del 40/40. |
| A12 | **Cerrado** | `sts.py:83-86` `X-Transcribed-Text` eliminado; `X-Transcribed-Text-B64` (base64 UTF-8) + `X-Transcribed-Chars`. **En vivo (CPU):** `POST /speech-to-speech` stt-tts → 200 (107 KB en la verificación del corrector; en esta sesión el ciclo STS no se re-ejecutó, ver nota). Cambio de contrato: ver §4 (N3). |
| A13 | **Cerrado** | `voices.py:36-50` `_candidate_path()`: solo `cand_[0-9a-f]+` + ruta resuelta dentro de `voices_dir`; aplicado en preview (`:197`) y save (`:211`). Test `test_design_preview_rejects_traversal` en el 40/40. |
| A14 | **Cerrado** | `av==13.1.0` en `requirements-gpu.txt` y `requirements-cpu.txt`. **En vivo:** `/verify` 200, **WER 0,0** en esta sesión (texto «Hola, esto es una prueba de Sonora.», transcrito idéntico, `verdict: ok`) — igual o mejor que el 0,125 declarado. |
| A15 | **Cerrado** | `main.py:55-64` el middleware captura `HTTPException` y devuelve 429 JSON. Test `test_rate_limit_middleware_returns_429_json` (`test_api.py:400-416`) en el 40/40. |
| A16 | **Cerrado** | `schemas.py:13` lista cerrada de 10 idiomas; `engines.py:327,352` `LANG_NAMES.get(language)` sin fallback → `ValueError` → 400 (el `get(..., "Spanish")` de `design_voices`, `engines.py:378`, es inalcanzable con la validación Pydantic previa, pero es un fallback latente si se llama al motor directo). **En vivo:** `language=xx` → **422**. |
| A17 | **Cerrado (código; sin verificar en Kaggle)** | `build_notebook.py:149-155`: en Kaggle, si no hay `API_TOKEN` en Secrets se genera uno aleatorio y se imprime para copiarlo en Ajustes. `backend/README.md` actualizado. El default local abierto se mantiene solo para desarrollo, como se declara. |

### Medios (8 corregidos + M3 error de auditoría)

| ID | Veredicto | Evidencia |
|---|---|---|
| M1 | **Cerrado** | `app/js/app.js:314` `combinarWav()` reescribe una sola cabecera WAV con los PCM concatenados; `app/index.html:87` el textarea `texto-tts` ya no tiene `maxlength="10000"`. Nota: si un bloque no es WAV parseable, `combinarWav` cae a concatenación simple (comentario en `app.js:311-313`); el caso WAV multi-bloque queda cubierto. |
| M2 | **Cerrado** | `history.py:134-135` conjunto explícito `{"qwen3-tts-1.7b", "qwen3-tts-0.6b", "qwen3-tts-1.7b-customvoice"}`. |
| M3 | **Error de auditoría — confirmado** | `backend/app/schemas.py:73-74` `SFXRequest.prompt` `max_length=500`, igual que el frontend (`app/index.html:284` `maxlength="500"`). El «450» es el límite del prompt de SFX **en la app de ElevenLabs** (`FEATURE_MAP.md:557`, «prompt de hasta 450 caracteres en la app»), no de este backend. La justificación de CORRECCIONES.md es correcta; sin cambio. |
| M4 | **Cerrado** | `screens.js:73-80` `recibirMuestra`: duración 0 → error «No se pudo leer la duración…» y la muestra no se acepta. (El `duracionDeAudio` de STS, `screens.js:890-892`, acepta duración desconocida, pero STS no tiene mínimo de 3 s: correcto.) |
| M5 | **Cerrado** | `pcm_44100`: 0 ocurrencias en `FEATURE_MAP.md` (eliminado del §1); `audio_effects` **sí** existe en el contrato (`schemas.py:35`, `tts.py:183-184`) — la segunda mitad del hallazgo era error de la auditoría, como dice CORRECCIONES.md. |
| M6 | **Cerrado** | `app/VERIFICACION.md:19` lista real de endpoints que llama el frontend; `:55-56,71` deltas aplicadas y VoxCPM2 corregido; `backend/README.md:166` sección «Qué llama el frontend (y qué no)». |
| M7 | **Cerrado** | `app.js:520` `init` lee `vozActivaIdioma`; `app.js:587-592` `setVozActiva` persiste id, nombre, origen, modelo e idioma. |
| M8 | **Cerrado (parcial declarado)** | `app.js:146-182` `aplicarDegradado` re-habilita y luego llama `validarEstudio()`, `validarClonar()` y `validarSts()` (`:181`). Doblaje y SFX siguen validando solo al pulsar, como admite CORRECCIONES.md — aceptable, no es el mismo defecto. |
| M9 | **Cerrado** | `schemas.py:36-38` `TTSRequest.normalize` (default true); `engines.py:254,272-273,323,343-344,349,361-362` los sintetizadores respetan el flag; `app.js:367` envía `normalize` desde Ajustes. |

### Bajos (3 corregidos + L4 error de auditoría)

| ID | Veredicto | Evidencia |
|---|---|---|
| L1 | **Cerrado (con matiz de verificación)** | Al inicio de esta re-auditoría no existían `backend/__pycache__/` ni `backend/.pytest_cache/`; los regeneraron **las propias ejecuciones de verificación del re-auditor** (`py_compile`, `pytest`). Eliminados al cerrar la sesión (0 restos; `backend/.gitignore` los cubre: `__pycache__/`, `*.pyc`). No es fallo del corrector. |
| L2 | **Cerrado** | 0 ocurrencias de `concat_wav_bytes`, `safe_name`, `VoiceRemixRequest`, `MODELS_DIR`, `modelos()`, `uso()`, `historialRemoto()`, `urlExportarDiccionario()` en `backend/app/` y `app/js/` (solo un comentario histórico en `schemas.py:61`). `borrarHistorialRemoto` se conserva y ahora se usa (A7). |
| L3 | **Cerrado** | `app/js/app.js:580` `setInterval(..., 300000)` cada 5 min y solo con la pestaña visible (`if (!document.hidden)`). |
| L4 | **Error de auditoría — confirmado** | `app/css/app.css:9-10` `--font-display: "Schibsted Grotesk", system-ui, sans-serif` y `--font-body: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`. El fallback del sistema existe; sin red hay tipografía prevista. La justificación de CORRECCIONES.md es correcta; sin cambio. |

### Defectos de verificación (§5 de VERIFICACION.md, 6/6 declarados)

| ID | Veredicto | Evidencia |
|---|---|---|
| VERIF B1 (`av`) | **Cerrado** | Ver A14. En vivo: `/verify` WER 0,0. |
| VERIF B2 (WebSockets) | **Cerrado (código + tests)** | `not_implemented.py:19-25` sin `Depends` a nivel de router; WS con `require_auth_ws()` (`:170,213`, `security.py:61`). Tests `test_stt_stream_websocket_closes_1011` y `test_stt_stream_websocket_rejects_without_token` en el 40/40. |
| VERIF B3 (`/tts/stream` 200 con 0 bytes) | **Cerrado (código + test)** | `tts.py:28-35` sintetiza la primera frase antes del `StreamingResponse`; sin motor → 503. Test `test_tts_stream_without_engine_503` en el 40/40. |
| VERIF B4 (`/audio-effects/apply` 500) | **Cerrado (código + test)** | `isolate.py:104-111` captura `ValidationError` → 422. Test de catálogo/validación en el 40/40. |
| VERIF B5 (`/dubbing` con `target_languages=""`) | **Cerrado (en vivo)** | `dubbing.py:296-302`: `None` → default `en`; vacío explícito → 400. **En vivo:** `""` → 400 (esta sesión). |
| VERIF B6 (CORS por defecto) | **Cerrado (código)** | Ver B6. |

## Hallazgos nuevos de esta re-auditoría

### N1 — MEDIA — La suite 40/40 no se reproduce con la orden documentada
- **Hecho:** `pytest tests/ -q` (orden documentada en `test_api.py:11` y en CORRECCIONES.md §6) da **8 fallos, 32 pasados** en `~/workspace/venvs/sonora-base`: los tests tardíos reciben 429 del rate-limit compartido (mismo `TestClient`/IP, `rate_limit_per_minute` default 60 en `config.py:70-73` y `heavy` 20). Con `RATE_LIMIT_PER_MINUTE=10000` solo, 5 fallos. Con **ambos** límites a 10000: **40 pasados**.
- **Consecuencia:** el «40/40» declarado solo existe con variables de entorno que no están documentadas en ningún sitio; un tercero que ejecute la orden tal cual ve 8 fallos y no puede distinguir regresión de artefacto. Los tests que fallan por defecto incluyen `test_auth_401_without_token` (429 en vez de 401) y `test_cors_allows_localhost_blocks_unknown` — justo los de seguridad.
- **Corrección sugerida (minutos, sin GPU):** o bien fijar límites altos dentro de la propia suite (fixture/`conftest.py` o `os.environ` antes de importar la app, como ya se hace con `DATA_DIR`/`API_TOKEN`), o bien documentar las dos variables en `test_api.py` y en CORRECCIONES.md §6. No es fallo del producto, es fallo de la evidencia.

### N2 — BAJA — FEATURE_MAP §8 sigue diciendo que `voice-conversion` es el método por defecto
- **Hecho:** `FEATURE_MAP.md:419-422` documenta `"method": "voice-conversion (por defecto) | stt-tts"`. El backend (`sts.py:32`) y el frontend (`app/index.html:213`) tienen por defecto `stt-tts` desde B9.
- **Corrección:** una línea en FEATURE_MAP §8.

### N3 — BAJA — La cabecera `X-Transcribed-Text-B64` no está documentada en FEATURE_MAP ni la consume nadie
- **Hecho:** `grep X-Transcribed-Text FEATURE_MAP.md` = 0 ocurrencias (la cabecera vieja tampoco estaba documentada, así que no es una regresión; pero CORRECCIONES.md §7 presenta el cambio como «anotado» y solo está anotado en CORRECCIONES.md, no en el mapa del contrato). Además el frontend no la lee: `api.js:131-135` `vozAVoz()` devuelve solo `blob` + `X-Method`; el texto transcrito nunca se muestra al usuario. La cabecera existe y es correcta en el backend (`sts.py:83-86`), pero es superficie de contrato sin consumidor ni documentación.
- **Corrección:** documentar la cabecera en FEATURE_MAP §8 (nombre, base64 UTF-8, `X-Transcribed-Chars`) o eliminar la cabecera si nadie la va a usar. No bloquea.

## Puertas re-ejecutadas

| Puerta | Veredicto | Resumen |
|---|---|---|
| 1. `local-thermo-review` | **PASA** | Ningún archivo >1.000 líneas (mayor: `app/js/screens.js`, 899). Código muerto de L2 eliminado (grep: 0 restos). Sin TODO/FIXME nuevos detectados en el barrido. |
| 2. `local-ecc-revisores` (seguridad) | **PASA con riesgo conocido** | Sin secretos reales (grep de `sk-`, `ghp_`, `AKIA`, claves privadas: 0). Auth en `/api/v1/*`, traversal cerrado (A13), rate-limit con 429 real (A15). Residuales **no numerados en AUDIT.md y no tocados, como admite CORRECCIONES.md §7**: `X-Forwarded-For` sigue siendo confiable para rate-limit (`security.py`, `client_ip`); sin aislamiento por usuario (voces/historial globales para 2 usuarios); subida completa en memoria; sin cabeceras HSTS/CSP. Ninguno es hallazgo nuevo: quedan como riesgos conocidos. |
| 3. `replica-diff` + `replica-test` (contrato) | **PASA con N2/N3** | Los 5 puntos rotos (B1, B2, B3, B4, B8, B9) cerrados y verificados por código y, donde se indica, en vivo. Las 15 rutas sin UI siguen sin UI y documentadas (`app/VERIFICACION.md:19`, `backend/README.md:166`). Marca propia «Sonora»; «ElevenLabs» solo como atribución (`app/index.html:377`). |
| 4. `provider_model_verification` | **PASA (código; GPU pendiente)** | `transformers==4.57.3` / `accelerate==1.12.0` / `av==13.1.0` fijados; códigos Kokoro sin de/ko/ru (A5, verificado en vivo 400/422); VRAM 1.7B a 8 GB (A6, sin medir). Resolución de `pip` en Kaggle y medición de VRAM siguen pendientes del run. |
| 5. Seguridad y honestidad | **PASA** | 501 honesto; funciones no disponibles ya no se presentan como disponibles (VoxCPM2 fuera del selector, `voice-conversion` etiquetado 501, sliders con soporte real por voz, destinos de doblaje solo es↔en). Docs corregidas (M6). |

## Cambios de contrato (§7 de CORRECCIONES.md) — verificación

| Cambio | FEATURE_MAP v2 | Frontend | Veredicto |
|---|---|---|---|
| (1) `pcm_44100` fuera de §1 | Eliminado: 0 ocurrencias en `FEATURE_MAP.md`; backend solo `mp3\|wav` (`schemas.py:23,36`) | Sin referencias en `app/js/` | **Reflejado, sin divergencia** |
| (2) `X-Transcribed-Text` → `X-Transcribed-Text-B64` | **No reflejado**: 0 ocurrencias de la cabecera en `FEATURE_MAP.md` (tampoco estaba la vieja) | El frontend no lee ninguna de las dos; `vozAVoz()` ignora la cabecera | **Divergencia menor (N3)** — el código es coherente (backend emite B64, nada espera el nombre viejo), pero el mapa del contrato no lo documenta |
| Adiciones compatibles | `GET /dubbing/{id}` devuelve `target_languages` y `result_paths` — documentado en FEATURE_MAP §9 (`"target_languages": ["en", …]`, salida del GET con `segments`); `edit` con `?language=` en `dubbing.py:406` | Frontend usa `target_languages` en el estado (`screens.js:490` ss.) | **Reflejadas** |
| `TTSRequest` gana `similarity` y `normalize` | No verificado en FEATURE_MAP §1 (el mapa no lista cada campo del esquema); el backend los declara (`schemas.py:32,36-38`) y el frontend envía `normalize` (`app.js:367`) y nunca `similarity` | Coherente | **Sin divergencia funcional** |

## Lo que sigue quedando

### Para el navegador vivo (`delivery_audit_gate`) — sin cambios respecto a AUDIT.md, más N1–N3
1. Corregir N1 (hacer la suite reproducible por defecto), N2 y N3 antes o junto con el navegador vivo: son minutos y sin GPU.
2. Las 7 pantallas con backend en línea y apagado, en el teléfono de Carlos; responsive 360/768/1024/1440; táctil, teclado, lector de pantalla; `prefers-reduced-motion`, contraste, foco.
3. QC de audio: -16 LUFS ±1, pico ≤ -1 dBTP, inteligibilidad por transcripción, escucha completa de cada salida.
4. Re-verificar en navegador los flujos completos (no solo respuestas HTTP): B1, B2, B4, B7, B8, B9.
5. Las 8 discrepancias del Apéndice D de FEATURE_MAP.md (D1–D8) y las 10 incógnitas de tráfico web de `REA.md` (N1–N10) siguen abiertas, como en AUDIT.md.

### Para el run de Kaggle (`backend/PENDIENTES_KAGGLE.md`) — lo no verificable sin GPU
1. Resolución de `requirements-gpu.txt` en `pip` (B5) — el pin es correcto en papel, no probado.
2. CORS + token obligatorio en el notebook real (B6, A17) y `GET /health` / `GET /api/v1/models` desde GitHub Pages.
3. Doblaje ES→EN de extremo a extremo con 2 idiomas (A1, A2) hasta `done` y descarga.
4. Voice Design: comprobar que los 3 candidatos difieren (A10).
5. Clonación Qwen3-TTS + `speed` por remuestreo en voces clonadas (B4) + WER ≤ 0,15.
6. Medición de VRAM con Qwen 1.7B + Whisper en la misma T4 16 GB (A6).
7. STT `large-v3` y diarización (con `HF_TOKEN`); Demucs; SFX con `HF_TOKEN`.

### Notas del re-auditor (límites de esta verificación)
- **No re-ejecutado en vivo por el re-auditor, solo por código + test:** STS completo con audio real (A12, B7 con `.webm` real), `/tts/stream` con motor (A11), `similarity`→422 en vivo (B4). Los tests que los cubren pasan dentro del 40/40 con límites altos; los valores declarados en CORRECCIONES.md §6 para esos casos no se contradicen con nada observado.
- **Verificado en vivo por el re-auditor en esta sesión:** `/health`, `/tts` Kokoro `ef_dora` → 200 (47.565 B MP3; 200 WAV en el segundo ciclo), `/verify` → WER 0,0 `ok`, `language=xx` → 422, `language=de` → 400, `/dubbing` JSON `["en"]` → 202 con `job_id`, `target_languages=""` → 400, estado del job con `target_languages`/`result_paths`. Servidores apagados al terminar; `DATA_DIR` de prueba en `/tmp/sonora-audit2` (desechable).
- **Dos errores propios del re-auditor, no del código:** el primer intento de doblaje usó el campo `audio` en vez de `media` (422 correcto por campo requerido) y un `.wav` que era MP3 renombrado (400 correcto por magic check). Ambos confirman que la validación funciona.
