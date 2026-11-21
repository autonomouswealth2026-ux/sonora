# VERIFICACIÓN — Sonora (clon web de ElevenLabs): ciclo completo en local

**Fecha:** 2026-11-20 (hora de La Habana; 2026-11-21 00:45 UTC en los logs del servidor).
**Verificador:** agente verificador (subagente). **Alcance:** todo lo verificable en local, sin GPU.
**Regla aplicada:** evidencia o «no verificado» con motivo. Nada de humo.

**Veredicto corto:** el ciclo CPU completo **funciona de verdad** — frontend servido,
backend FastAPI en pie, narración Kokoro en español generada y verificada por
transcripción con **WER 0,125 (veredicto `ok`)**. La suite pytest pasa **26/30** en
entorno limpio sin modelos. Hay **4 defectos reales** (2 graves, 2 menores) y
**1 dependencia rota en `requirements*.txt`** que también afectará al run de Kaggle
si no se corrige antes. La clonación Qwen3-TTS y todo lo GPU queda **no verificado**,
pendiente del run de Kaggle (checklist en `backend/PENDIENTES_KAGGLE.md`).

---

## 0. Corrección importante: la red SÍ funciona para pip y Hugging Face

El agente del backend reportó PyPI inalcanzable desde exec (ProxyError/timeout,
curl a pypi.org devuelve 000). **No se reproduce:**

| Prueba | Resultado |
|---|---|
| `curl https://pypi.org/simple/` (15 s) | Sin respuesta (timeout; igual que lo reportado) |
| `curl https://huggingface.co` (15 s) | Sin respuesta (timeout) |
| `pip install fastapi==0.115.6` en venv | **OK — 94,8 kB a 261,6 kB/s** |
| `pip install -r requirements.txt` (10 paquetes) | **OK** (fastapi 0.115.6, pydantic 2.10.4, uvicorn 0.34.0, pytest 8.3.4, etc.) |
| `pip install torch --index-url …/whl/cpu` | **OK — torch 2.15.0+cpu** |
| `pip install kokoro==0.9.4 faster-whisper==1.2.1` | **OK** |
| Descarga de pesos Kokoro-82M desde HF (vía `huggingface-hub`) | **OK** — log: `HEAD https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/kokoro-v1_0.pth → 302 Found` |
| `apt-get download espeak-ng` / `sudo apt-get install -y espeak-ng` | **OK — espeak-ng 1.51** |

Conclusión: `curl` directo falla (probable proxy que curl no usa igual que pip),
pero **pip, `huggingface-hub` y apt sí llegan a la red**. La suite pytest
no se había ejecutado por falta de FastAPI, no por falta de red. Ningún venv
preexistente tenía FastAPI (revisados: whisper, apex, muapi-cli, glmocr,
pdftools, psd, rea-video, scrapling, ytdlp; solo muapi-cli tenía pydantic).

**Entornos creados para esta verificación** (en `~/workspace/venvs/`, no en `/tmp`):

| Venv | Contenido | Tamaño |
|---|---|---|
| `~/workspace/venvs/sonora/` | requirements.txt + torch CPU 2.15.0 + kokoro 0.9.4 + faster-whisper 1.2.1 + **av==13.1.0** (ver §5) | 2,0 GB |
| `~/workspace/venvs/sonora-base/` | Solo `requirements.txt` (sin modelos: el entorno «sin motor» de los tests) | 287 MB |

**Por qué no en `/tmp`:** `/tmp` es un tmpfs de **512 MB (210 MB libres)**; la
instalación de torch falló ahí con `OSError: [Errno 28] No space left on device`.
`/home` tiene 46 GB libres. Lección: no instalar nada pesado en `/tmp` en esta VM.

---

## 1. Frontend (SPA estática) — VERIFICADO en local

Servido con `python3 -m http.server 8931` desde `app/` (PID 16511 durante la
verificación; apagado al final, ver §8).

| # | Comprobación | Resultado |
|---|---|---|
| 1.1 | `index.html` + 6 ficheros CSS/JS por HTTP | **200 en los 7** (`index.html` 34 559 B, `screens.js` 36 840 B, resto 5–24 kB) |
| 1.2 | `node --check` en los 5 JS (`api`, `store`, `player`, `screens`, `app`) | **PASA, 5/5, sin errores** (re-verificado, no solo lo del autor) |
| 1.3 | Cruce de IDs: los 129 IDs usados en JS existen en `index.html` | **PASA — 0 faltantes** (re-verificado con script Node independiente) |
| 1.4 | Las 7 rutas por hash en el HTML | **PASA** — `#/estudio`, `#/voces`, `#/voz-a-voz`, `#/doblaje`, `#/efectos`, `#/historial`, `#/ajustes` |
| 1.5 | URL del backend configurable, sin hardcodear | **PASA** — `js/api.js`: `baseUrl()` lee `ajustes.backendUrl` (localStorage, por defecto `''`); todas las llamadas pasan por `pedir()` → `fetch(url(ruta))`. Ningún `localhost`/`127.0.0.1` en el JS. La única URL externa es Google Fonts y el placeholder `https://xxxx.trycloudflare.com` del campo de Ajustes |
| 1.6 | Endpoints del frontend contra rutas reales del backend | **PASA** — las 19 llamadas de `js/api.js` (`/health`, `/models`, `/tts/voices`, `/tts`, `/voices/instant-clone`, `/voices/{id}/preview`, `DELETE /voices/{id}`, `/voices/design`, `/voices/design/{id}/save`, `/speech-to-speech`, `/dubbing`, `/dubbing/{id}`, `/dubbing/{id}/segments/{n}/edit`, `/dubbing/{id}/download?language=…&format=mp4`, `/sfx`, `/usage`, `/history`, `DELETE /history/{id}`, `/pronunciation`, `/pronunciation/export`) existen en el OpenAPI del backend (58 rutas). El backend acepta `language` y `format` (mp3|wav|mp4) en la descarga de doblaje, como pide el frontend |
| 1.7 | Modo degradado con backend apagado (por código) | **PASA (código)** — `comprobarBackend()` en `js/app.js:122`, re-chequeo cada 60 s, botones GPU deshabilitados con motivo; Historial y Ajustes no dependen del backend. **Pendiente de comprobar en navegador vivo** (ver §7) |
| 1.8 | Sin secretos en el frontend | **PASA** — token solo desde Ajustes (localStorage); sin claves en el código |

---

## 2. Backend: estructura y rutas — VERIFICADO

- `python3 -m py_compile app/*.py app/routers/*.py tests/test_api.py`: **OK, 21 ficheros**.
- **Tabla de rutas por AST + grep (63 rutas con prefijo `/api/v1`, más `/` y `/health`):**
  37 implementadas + `/` y `/health` — coincide con lo declarado (37 + 26 en 501).
  26 en 501 en `not_implemented.py` (diálogo, pro-clone ×2, remix, música ×2,
  projects ×9, reader ×4, agentes ×3 incl. WebSocket, realtime, realtime-translation,
  elevenai, `stt/stream` WebSocket) — coincide con lo declarado.
- **OpenAPI:** `/openapi.json` lista 58 rutas; `/docs` responde 200.
- `.env.example` sin valores; no existe `.env` con secretos en el repo local;
  `.gitignore` cubre `.env`, `data/`, `models/`, `.venv/`, `*.log`.
- Notebook de Kaggle (`kaggle_notebook.ipynb`): 8 celdas (2 markdown + 6 de código,
  coincide con «las 6 celdas» del README). Celda 3 instala `espeak-ng` + `ffmpeg`
  por apt e instala `requirements-gpu.txt`; celda 4 descarga los 6 repos Qwen3-TTS
  + Kokoro + Whisper large-v3; celda 5 arranca uvicorn y espera a `/health`;
  celda 6 crea el túnel trycloudflare. **No verificado en Kaggle** (ver §7).

---

## 3. Suite pytest — 26/30 en entorno limpio sin modelos

Ejecutada con el venv `sonora-base` (solo `requirements.txt`, sin torch/Kokoro/
faster-whisper) y rate limits altos para aislar fallos reales del ruido del
limitador (ver §6):

```
RATE_LIMIT_PER_MINUTE=10000 HEAVY_RATE_LIMIT_PER_MINUTE=10000 pytest tests/ -q
→ 4 failed, 26 passed in 4.38s
```

Pasan: health, models, validación TTS (400/422), voz desconocida 404,
TTS sin motor 503, compat. OpenAI, lista de voces, clonación (consentimiento
obligatorio, muestra <3 s rechazada, registro sin motor + preview 503),
borrado de voz fija 400, Voice Design validación + 503, biblioteca y favoritos,
STT validación + 503, alineación sin transcripción, isolate denoise 501 y
demucs 503, diccionario CRUD + import/export PLS, historial vacío + 404s,
verify rechaza entradas no-TTS, `normalize_text` + `word_error_rate`, SFX
validación + 503, STS voice-conversion 501 + voz desconocida 404, fases 3–4
todas 501, rate limiter unitario.

**Los 4 fallos son defectos reales del código (detalle en §5):**

| Test | Esperado | Obtenido |
|---|---|---|
| `test_tts_stream_without_engine_503` | 503 | **200 con 0 bytes** |
| `test_stt_stream_websocket_closes_1011` | cierre 1011 | **TypeError** (la conexión muere antes) |
| `test_audio_effects_catalog_and_validation` | 422 con `reverb=catedral` | **500** |
| `test_dubbing_validation_and_404s` | 400 con `target_languages=""` | **202** (job creado) |

---

## 4. Ciclo CPU completo con Kokoro — VERIFICADO con audio real

Backend arrancado con el venv `sonora` (torch CPU + kokoro + faster-whisper +
espeak-ng 1.51): `CPU_ONLY=1 DATA_DIR=/tmp/sonora-data2 PORT=8001`,
`GET /health → {"status":"ok","gpu":false,"cpu_only":true,"models_loaded":[]}`.

### 4.1 Narración Kokoro en español (voz `ef_dora`)

```
POST /api/v1/tts {"text":"Hola, soy Dora. Este es el clon de ElevenLabs
funcionando en local, con voz en espanol.","voice_id":"ef_dora",
"model":"kokoro","language":"es","format":"wav"}
→ 200, 247 244 B, X-Generation-Id: 5924cef4bf14, X-Duration-Seconds: 5.15,
  X-Model: kokoro, X-Voice-Id: ef_dora
```

Audio verificado: **WAV mono, 24 kHz, 16 bits, 123 600 frames, 5,15 s**.
Primera llamada: 82 s (descarga de pesos Kokoro-82M desde HF + carga del
pipeline). Segunda generación (`em_alex`, MP3): 200 inmediato, 1,98 s de audio.
Aviso en el log (no bloqueante): `phonemizer: words count mismatch on 100.0%
of the lines (1/1)` — no afecta al resultado audible/transcrito (ver §4.2).

### 4.2 Verificación por transcripción — WER 0,125, veredicto `ok`

Transcripción independiente con faster-whisper **small** local
(venv `~/workspace/venvs/whisper`, `HF_HUB_OFFLINE=1`, modelo ya en caché):

- Transcrito: «Hola, soy Dora. Este es el clon de Eleven Labs funcionando en
  local con voz en español.» — idioma `es`, probabilidad 1,0.
- Esperado normalizado: `hola soy dora este es el clon de elevenlabs funcionando
  en local con voz en espanol`
- Obtenido normalizado: `hola soy dora este es el clon de eleven labs funcionando
  en local con voz en espanol`
- **WER: 2/16 = 0,125** (única diferencia: «elevenlabs» → «eleven labs»,
  artefacto de tokenización de Whisper, no error de síntesis).

El propio endpoint del backend coincide exactamente:

```
POST /api/v1/history/gen_5924cef4bf14/verify → 200
{"wer": 0.125, "matched_words": 15, "total_words": 16, "verdict": "ok",
 "transcribed": "Hola, soy Dora. Este es el clon de Eleven Labs funcionando
  en local con voz en español."}
```

(El primer intento de `/verify` dio 500 por el defecto §5-B1; tras corregir `av`
en el venv de verificación, devuelve 200 con el mismo WER que la transcripción
independiente.)

### 4.3 Resto del ciclo, todo con respuestas reales

| Paso | Resultado |
|---|---|
| `POST /api/v1/tts/stream` (2 frases, Kokoro) | **200, 145 244 B** de WAV real |
| `POST /api/v1/stt` (model=small, el WAV generado) | **200, language `es`, duration 5,15 s**, transcripción correcta |
| `POST /api/v1/align` (transcripción conocida) | **200**, palabras con inicio/fin (`Hola,` 0,00–0,38 s; `soy` 0,54–0,66 s; …) |
| `GET /api/v1/history` | **200, total 2** (las 2 generaciones, con `audio_url`) |
| `GET /api/v1/history/gen_5924cef4bf14/audio` | **200, 247 244 B** (idéntico al generado) |
| `GET /api/v1/voices/ef_dora/preview` | **200, 82 125 B, MP3 válido** (ID3 v2.4, 160 kbps, 24 kHz, mono) |
| `POST /api/v1/audio-effects/apply` (reverb=room) | **200, 104 205 B** (DSP sin modelo) |
| `GET /api/v1/audio-effects/catalog` | **200** (reverb none/room/hall, distance, rain/cafe, pan ±1, telephone/radio) |
| `POST /api/v1/voices/design` (sin GPU) | **503** con mensaje «arranca el backend GPU» |
| `POST /api/v1/isolate` mode=demucs (sin paquete) | **503**; mode=denoise → **501** con motivo |
| `POST /api/v1/sfx` (sin GPU) | **503** |
| `POST /api/v1/stt` model=large-v3 (sin GPU) | **503** («large-v3 necesita GPU. En CPU usa model=small») |
| `POST /api/v1/voices/instant-clone` sin `consent_note` | **422** (`Field required`); con consentimiento → **201** (registra la voz; la síntesis es 503, por diseño y por test) |
| `GET /api/v1/voices/{id}/preview` (voz clonada, sin GPU) | **503**; `POST /api/v1/tts` con esa voz → **503** |
| `DELETE /api/v1/voices/{id}` (clonada) | **200** y el fichero de referencia y su directorio **desaparecen del disco** (borrado real, verificado) |
| `POST /api/v1/dubbing` sin media | **422**; con `target_languages=fr` → **422**; job inexistente → **404** |
| `POST /api/v1/agents`, `/dialogue`, `/music` | **501** con motivo y alternativa |
| `GET /api/v1/usage` | **200** (`total_characters`, `total_minutes`, por modelo y por voz) |
| Diccionario: `POST /api/v1/pronunciation` → **201**, `GET ?language=es` lista la regla | **PASA** (CRUD verificado también directo en `store.py`: voz, historial, regla, borrados) |

### 4.4 Validación Pydantic y WER (sin servidor)

Probado directo en Python: texto vacío → `string_too_short`; texto >10 000 →
`string_too_long`; `speed=3.0` → `less_than_equal`; `format=ogg` →
`string_pattern_mismatch`; prompt de diseño corto → `string_too_short`;
SFX 60 s → `less_than_equal`. `normalize_text("¡Hola, Valdés! ¿Cómo estás?")`
→ `hola valdes como estas`. `word_error_rate`: idéntico 0,0; 1 palabra de 2 → 0,5.

---

## 5. Defectos encontrados (hay que corregir antes de entregar)

### B1 — GRAVE: `faster-whisper` incompatible con `av` sin fijar → `/verify` y `/stt` dan 500

- **Evidencia:** `POST /api/v1/history/{id}/verify` → 500. Log:
  `File ".../faster_whisper/audio.py", line 46, in decode_audio:
  with av.open(input_file, mode="r", metadata_errors="ignore") ...
  TypeError: open() got an unexpected keyword argument 'metadata_errors'`
- **Causa:** `pip install faster-whisper==1.2.1` arrastra `av` 19.0.2; faster-whisper
  1.2.1 solo funciona con `av` que acepte `metadata_errors="ignore"`.
  **CORRECCIÓN 2026-11-20:** el umbral NO es 14 — `av==15.1.0` SÍ acepta ese
  argumento (verificado con `av.open(..., metadata_errors="ignore")`); el que
  lo elimina es `av` 19.x. En Python 3.13 (Kaggle) `av==13.1.0` no tiene wheel
  y hay que usar `av==15.1.0` (ver `requirements-gpu.txt`).
- **Verificación de la corrección:** con `av==13.1.0` en el venv `sonora`,
  `/verify` → 200, WER 0,125, y `/stt` y `/align` funcionan.
- **Acción requerida:** añadir `av==13.1.0` (o `av<14`) a `requirements-cpu.txt`
  **y a `requirements-gpu.txt`** — el notebook de Kaggle instala
  `requirements-gpu.txt` sin pin de `av`, así que el run de Kaggle reproducirá
  este 500 en `/stt`, `/align` y `/verify` si no se corrige antes. No lo corregí
  en el repo: solo en mi venv de verificación; el cambio en `requirements*.txt`
  lo debe hacer el agente del backend (o Carlos) y quedar registrado.

### B2 — GRAVE: WebSocket `/api/v1/stt/stream` no conecta nunca (dependencia de auth)

- **Evidencia:** `pytest test_stt_stream_websocket_closes_1011` → `TypeError:
  get_token_dependency.<locals>._check() missing 1 required positional argument:
  'request'`. El test espera cierre 1011 con motivo; la conexión muere antes.
- **Causa:** todos los routers usan `dependencies=[Depends(require_auth)]` y
  `_check(request: Request)`; en rutas WebSocket no hay `Request` que inyectar,
  así que FastAPI no puede resolver la dependencia. Afecta a las dos rutas WS
  (`/api/v1/stt/stream` y `/api/v1/agents/{id}/talk`).
- **Acción requerida:** dependencia de auth separada para WS (leer el token de
  `websocket.headers` / query param) o excluir los WS del `Depends` de router.

### B3 — MEDIO: `/api/v1/tts/stream` sin motor devuelve 200 vacío en vez de 503

- **Evidencia (vivo y en pytest):** sin Kokoro instalado → `200, 0 B` en vez de
  503. Con motor funciona (200, 145 244 B).
- **Causa:** `tts.py` levanta `ModelUnavailable` dentro del generador de
  `StreamingResponse`; la respuesta ya arrancó con 200 y la excepción no se
  convierte en 503. El frontend recibiría un audio vacío sin error visible.
- **Acción requerida:** comprobar disponibilidad del motor **antes** de devolver
  el `StreamingResponse` (o sintetizar la primera frase fuera del generador).

### B4 — MEDIO: `/api/v1/audio-effects/apply` con preset inválido devuelve 500 en vez de 422

- **Evidencia (vivo y en pytest):** `reverb=catedral` → `Internal Server Error
  [500]`. Esperado 422.
- **Causa:** el handler construye `AudioEffectsRequest(...)` a mano (con
  `pattern` en el schema) sin capturar `ValidationError`; la excepción sube
  como 500.
- **Acción requerida:** capturar `ValidationError` → 422 (o validar con
  `Form(pattern=…)`).

### B5 — MENOR: `/api/v1/dubbing` con `target_languages=""` crea el job (202) en vez de 400

- **Evidencia (vivo y en pytest):** `target_languages=""` → `202, job_id`
  (el campo vacío cae al valor por defecto `"en"`). El código sí tiene la
  guarda (`if not targets … → 400`), pero nunca se alcanza porque FastAPI
  aplica el default ante el campo vacío.
- **Acción requerida:** rechazar explícitamente la cadena vacía (o documentar
  que vacío = `en`). Menor: el job resultante es válido (`en`), pero el
  usuario no pidió nada y el test del propio backend lo considera error.

### B6 — MENOR (operativo): CORS por defecto no cubre el puerto del autor ni GitHub Pages

- **Evidencia:** `Origin: http://127.0.0.1:8931` (puerto usado por el autor del
  frontend) → **sin cabecera `access-control-allow-origin`** (el navegador
  bloquearía). `Origin: http://127.0.0.1:8000` (puerto del README) → cabecera
  presente. Origen de GitHub Pages sin `CORS_ORIGINS` → también bloqueado.
- Es el comportamiento documentado en `config.py` (por defecto solo
  localhost:3000/8000; en producción hay que fijar `CORS_ORIGINS` con la URL
  de GitHub Pages). **Riesgo real en el run de Kaggle:** si Carlos pega la URL
  del túnel en Ajustes sin fijar `CORS_ORIGINS=https://…github.io` en el
  notebook, el frontend no podrá llamar al backend. La celda 5 del notebook
  no fija `CORS_ORIGINS`. Acción: añadirlo a la checklist del run (o al
  notebook) antes de probar desde el teléfono.

### Ruido de test (no es defecto de la app, pero sí de la suite)

- Con los límites por defecto (60/min general), la suite completa falla en
  **5 tests con 429** por acumulación (el limitador es global en memoria y el
  TestClient usa una sola IP): la primera ejecución dio **8 fallos (22/30)**,
  5 de ellos 429. Con límites altos, esos 5 pasan. La suite necesita resetear
  el limitador entre tests (o subir el límite en el entorno de test); si no,
  el resultado depende del orden y del volumen acumulado.
- El fallo 500 de `POST /api/v1/agents` en la primera ejecución completa **no
  se reproduce en aislado** (en aislado da 501 correcto, y en vivo también):
  es un artefacto en cascada de la ejecución completa con el limitador.
- Warnings menores: `@app.on_event("startup")` deprecado (usar `lifespan`);
  `torch.nn.utils.weight_norm` deprecado (aviso de Kokoro/torch).

---

## 6. Red y entorno — resumen

- **PyPI, Hugging Face (vía `huggingface-hub`) y apt SÍ alcanzables desde exec**
  (pip a ~260 kB/s); `curl` directo a pypi.org/huggingface.co agota el timeout
  (15 s). La afirmación «PyPI inalcanzable» queda **refutada para pip**; el
  bloqueo era de `curl`, no de la red.
- **Modelos en caché local:** `faster-whisper-small/medium/base`, `whisper-tiny`,
  `Kokoro-82M` (descargado durante esta verificación). **No** hay en caché:
  Qwen3-TTS, Whisper large-v3, Demucs, Stable Audio Open, VoxCPM2.
- **Qwen3-TTS en CPU:** no probado y **no cabe en el diseño CPU** — `engines.py`
  exige GPU para Qwen3-TTS (`CPU_ONLY=1` → 503 «necesita GPU»). La clonación
  zero-shot solo existe en GPU; no se afirma nada sobre su calidad o
  funcionamiento en CPU.
- Servidores usados: frontend `python3 -m http.server 8931`, backend uvicorn
  `:8001` con `RATE_LIMIT_PER_MINUTE=1000` (para no contaminar las pruebas con
  429). **Apagados al final de la verificación** (ver §8).

---

## 7. Qué queda PENDIENTE (no verificado aquí)

### 7.1 Run de Kaggle T4 — verificación pendiente de Carlos

Nada de lo que exige GPU se ha probado en GPU en esta sesión. Checklist íntegra
en `backend/PENDIENTES_KAGGLE.md` (10 puntos); antes de ejecutarla, corregir
**B1** (`av==13.1.0` en `requirements-gpu.txt`) y **B6** (`CORS_ORIGINS` con la
URL de GitHub Pages). Resumen de lo pendiente:

1. Arranque del notebook (6 celdas) y `/health` con `{"gpu": true}`.
2. Túnel trycloudflare y `/health` a través de él desde el teléfono.
3. Kokoro en español (`ef_dora`): escucha — ¿suena aceptable? (en CPU local la
   transcripción es correcta, WER 0,125; la **calidad percibida** no se ha
   evaluado por escucha).
4. **Qwen3-TTS Base (clonación)**: muestra 10–30 s → `instant-clone` → TTS con
   esa voz → `verify` (WER ≤ 0,15 esperado). **Sin probar.**
5. Voice Design: 3 candidatos en español, escucha.
6. STT large-v3: timestamps por palabra, `language=es`.
7. Demucs: audio con música de fondo.
8. SFX: requiere aceptar términos de `stabilityai/stable-audio-open-1.0` en HF
   y `HF_TOKEN`.
9. Doblaje ES→EN: job hasta `done` + descarga.
10. VRAM con Qwen3-TTS 1.7B cargado (`/models` + `nvidia-smi`).

Además, sin verificar: VoxCPM2 (registrado, no integrado), ZONOS3-Mini
(candidato A/B), diarización pyannote (422 sin `HF_TOKEN` ni términos
aceptados), streaming real por token (es por frases, documentado).

### 7.2 Navegador vivo (puerta `delivery_audit_gate`)

Nada de esto se ha probado en navegador: las 7 pantallas con backend en línea
**y** apagado, en el teléfono de Carlos y en escritorio, con caché fresca
(checklist completa en `app/VERIFICACION.md` §2). En particular: reproducir/
pausar/buscar en la onda, sliders táctiles, subida de muestra inválida,
clonar sin consentimiento, borrar voz, voz a voz, doblaje con edición de
segmento, efectos 1 s y 47 s, historial (filtrar/re-generar/borrar), Ajustes
(pegar URL, Probar conexión online/offline, token, borrar datos), responsive
360/768/1024/1440, accesibilidad y QC de audio (-16 LUFS ± 1, pico ≤ -1 dBTP).
Tampoco se han corrido `thermo-review`, `ecc-revisores` ni `replica-diff/test`.

### 7.3 Calidad de la voz española de Kokoro

La inteligibilidad está verificada (WER 0,125), pero **nadie ha escuchado**
`ef_dora` en español en esta verificación (no hay escucha humana ni MOS).
RESEARCH.md §2.1 advierte que el español de Kokoro no tiene nota de calidad.
Pendiente: escucha A/B `ef_dora` vs `em_alex` vs `em_santa` (y en Kaggle,
contra Qwen3-TTS).

---

## 8. Cómo reproducir esta verificación

```bash
# Frontend
cd ~/workspace/elevenlabs-clon/app && python3 -m http.server 8000
# (puerto 8000: está en el CORS por defecto; el 8931 del autor NO lo está)

# Backend CPU (venv con modelos; crear una vez)
python3 -m venv ~/workspace/venvs/sonora
~/workspace/venvs/sonora/bin/pip install -r backend/requirements.txt
~/workspace/venvs/sonora/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
~/workspace/venvs/sonora/bin/pip install kokoro==0.9.4 faster-whisper==1.2.1 "av==13.1.0"
sudo apt-get install -y espeak-ng
cd backend && CPU_ONLY=1 DATA_DIR=/tmp/sonora-data PORT=8001 \
  ~/workspace/venvs/sonora/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001

# TTS + verificación
curl -X POST http://127.0.0.1:8001/api/v1/tts -H 'Content-Type: application/json' \
  -d '{"text":"Hola, soy Dora.","voice_id":"ef_dora","model":"kokoro","language":"es","format":"wav"}' -o tts.wav
curl -X POST http://127.0.0.1:8001/api/v1/history/gen_<id>/verify -H 'Content-Type: application/json' -d '{}'

# Suite (entorno sin modelos)
python3 -m venv ~/workspace/venvs/sonora-base
~/workspace/venvs/sonora-base/bin/pip install -r backend/requirements.txt
cd backend && RATE_LIMIT_PER_MINUTE=10000 HEAVY_RATE_LIMIT_PER_MINUTE=10000 \
  ~/workspace/venvs/sonora-base/bin/python -m pytest tests/ -q
```

Servidores de esta verificación (frontend :8931 PID 16511, backend :8001 PID 21643)
**apagados al terminar**; los venvs `sonora` y `sonora-base` quedan en
`~/workspace/venvs/` para reutilizar. Datos de prueba en `/tmp/sonora-data`,
`/tmp/sonora-data2` y `/tmp/sonora-store-test` (efímeros).
