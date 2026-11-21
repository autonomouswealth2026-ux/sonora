# Backend — clon de ElevenLabs (local, presupuesto cero)

Backend FastAPI del clon web de ElevenLabs para **2 usuarios** (Carlos y
otra persona). Modelos 100 % locales y open-source; sin pagos, sin cuentas
de pago, sin enviar audio a terceros.

- **Clonación zero-shot (GPU):** Qwen3-TTS 1.7B Base (Apache 2.0, desde 3 s,
  español nativo, ~8 GB VRAM). Identificador exacto:
  `Qwen/Qwen3-TTS-12Hz-1.7B-Base`, paquete `qwen-tts==0.1.1`.
- **Narración rápida (CPU):** Kokoro-82M (Apache 2.0, 24 kHz), paquete
  `kokoro==0.9.4`, `hexgrad/Kokoro-82M`. Español: `ef_dora`, `em_alex`,
  `em_santa` (probar `ef_dora` primero; su calidad en español no tiene
  nota publicada).
- **Máxima calidad opcional:** VoxCPM2 (Apache 2.0, ~8 GB VRAM) — registrado
  en `/api/v1/models` pero **no integrado todavía** (ver
  `PENDIENTES_KAGGLE.md`).
- **NO se usan:** Chatterbox (retirado ago 2026), Coqui/XTTS (cerrado dic
  2025), Fish S2 Pro / Drama 3 (no caben en una T4 de 16 GB).

Decisiones y licencias completas en `../RESEARCH.md`; especificación de
endpoints en `../FEATURE_MAP.md`.

## Estructura

```
backend/
├── app/
│   ├── main.py          # FastAPI, CORS, rate limit, handlers (sin cargar modelos)
│   ├── config.py        # Todo de variables de entorno (sin secretos)
│   ├── security.py      # Token opcional, rate limit, validación de uploads
│   ├── store.py         # SQLite + ficheros (voces, historial, reglas, jobs)
│   ├── schemas.py       # Validación Pydantic de cada ruta
│   ├── audio_utils.py   # WAV/MP3, efectos DSP, normalización -16 LUFS
│   ├── engines.py       # Carga PEREZOSA de modelos + registro
│   └── routers/
│       ├── system.py    # /health, /api/v1/health, /api/v1/models
│       ├── tts.py       # TTS, streaming por frases, compat. OpenAI
│       ├── voices.py    # Clonación instantánea, Voice Design, biblioteca
│       ├── stt.py       # STT + alineación forzada
│       ├── isolate.py   # Voice Isolator (Demucs) + efectos de audio
│       ├── pronunciation.py  # Diccionario (CRUD + PLS)
│       ├── history.py   # Historial, uso, verificación por transcripción
│       ├── sfx.py       # Efectos de sonido (Stable Audio Open)
│       ├── sts.py       # Speech-to-speech (vía stt-tts)
│       ├── dubbing.py   # Doblaje básico ES<->EN (asíncrono)
│       └── not_implemented.py  # Fases 3-4 y no replicables: 501 honesto
├── kaggle_notebook.ipynb  # Notebook listo para Kaggle (2x T4)
├── build_notebook.py      # Regenera el notebook (python3 build_notebook.py)
├── requirements.txt       # Base (CPU-seguro, versiones fijadas)
├── requirements-gpu.txt   # GPU (Kaggle)
├── requirements-cpu.txt   # Solo CPU (InstaBox)
├── run.sh / run_cpu.sh    # Arranque local / solo CPU
├── .env.example           # Variables SIN valores
└── tests/test_api.py      # Tests (pytest): validación, 404, 501, 503
```

**Regla de arranque:** ningún modelo se carga al arrancar. Cada endpoint
carga su modelo bajo demanda y lo cachea; antes de cargar un modelo grande
se descargan los demás para que quepa en la T4 de 16 GB.

## Cómo correrlo en local (PC)

```bash
cd backend
cp .env.example .env        # edita solo si quieres token o CORS
./run.sh                    # GPU: instala requirements-gpu.txt y arranca en :8000
# o solo CPU:
./run_cpu.sh                # instala torch CPU + requirements-cpu.txt, CPU_ONLY=1
```

Abre `http://localhost:8000/docs` (Swagger) y `http://localhost:8000/health`.

## Cómo arrancarlo en Kaggle desde el teléfono (paso a paso, tocando)

> Sin atajos de teclado: todo se hace tocando la pantalla. Para pegar texto,
> mantén pulsado el campo y toca **Pegar**.

1. **Prepara el código una sola vez (desde el ordenador o el teléfono):**
   sube esta carpeta `backend/` a GitHub en el repo `elevenlabs-clon`
   (o súbela como dataset de Kaggle llamado `elevenlabs-backend`).
2. **En Kaggle, abre el notebook:** sube `kaggle_notebook.ipynb` a Kaggle
   (o ábrelo desde el repo) y toca **Run**.
3. **Activa la GPU:** toca **⋮ → Accelerator → GPU T4 x2**.
4. **Activa Internet:** en el panel derecho, **Settings → Internet: ON**.
5. **Ejecuta las celdas en orden, de arriba abajo** (toca el ▶ de cada
   celda y espera a que termine antes de pasar a la siguiente):
   - Celda 1: comprueba la GPU.
   - Celda 2: trae el código del backend.
   - Celda 3: instala dependencias (tarda varios minutos).
   - Celda 4: descarga los pesos (Qwen3-TTS + Kokoro + Whisper).
   - Celda 5: arranca el servidor y comprueba `/health`. Fija
     `CORS_ORIGINS` con la URL de GitHub Pages y genera un `API_TOKEN`
     si no lo pusiste en Secrets (la API ya no queda abierta en Kaggle).
   - Celda 6: crea el túnel y **muestra la URL https**.
6. **Copia la URL:** mantén pulsado sobre la URL
   `https://....trycloudflare.com`, toca **Copiar**.
7. **Pégala en la app:** abre el frontend (GitHub Pages) → **Settings** →
   campo **URL del backend** → mantén pulsado → **Pegar** → **Guardar**.
8. **Listo.** La sesión dura 12 h como máximo y la URL cambia en cada
   arranque: repite desde el paso 5 cada vez que arranques.

Token obligatorio en Kaggle: en **Add-ons → Secrets**, añade `API_TOKEN`
con un texto secreto inventado por ti; si no lo pones, la celda 5 genera
uno aleatorio y lo imprime en la salida. El frontend deberá enviarlo como
`Authorization: Bearer <API_TOKEN>` (campo Token en Ajustes). La API ya
no queda abierta en Kaggle: no compartas la URL con nadie.

## Modo CPU en InstaBox (sin GPU)

```bash
./run_cpu.sh
```

Solo funciona Kokoro (narración con voces fijas) y Whisper small (STT).
Qwen3-TTS, Demucs y SFX devuelven **503** con el mensaje
"arranca el backend GPU". No se toca la GPU.

## Endpoints implementados (fases 1–2)

| Ruta | Método | Función |
|---|---|---|
| `/health`, `/api/v1/health` | GET | Estado, modelos cargados, VRAM libre |
| `/api/v1/models` | GET | Modelos registrados y su estado |
| `/api/v1/tts` | POST | Texto → audio (Kokoro / Qwen3-TTS) |
| `/api/v1/tts/stream` | POST | TTS por frases (streaming) |
| `/api/v1/tts/voices` | GET | Voces fijas + clonadas + diseñadas |
| `/api/v1/audio/speech` | POST | Compatibilidad OpenAI TTS |
| `/api/v1/voices/instant-clone` | POST | Clonación zero-shot (3 s–2 min, consentimiento obligatorio) |
| `/api/v1/voices/{id}/preview` | GET | Muestra "Hola, soy…" |
| `/api/v1/voices/{id}` | DELETE | Borra voz + referencia (borrado real) |
| `/api/v1/voices/design` | POST | Voice Design (hasta 3 candidatos) |
| `/api/v1/voices/design/{id}/preview` | GET | Audio del candidato |
| `/api/v1/voices/design/{id}/save` | POST | Guarda el candidato como voz |
| `/api/v1/library/voices` | GET | Biblioteca propia (búsqueda, idioma) |
| `/api/v1/library/voices/{id}/favorite` | POST | Favorito |
| `/api/v1/stt` | POST | Transcripción (JSON/SRT/VTT/TXT) |
| `/api/v1/align` | POST | Alineación forzada por palabra |
| `/api/v1/isolate` | POST | Voice Isolator (Demucs) |
| `/api/v1/audio-effects/catalog` | GET | Presets de efectos DSP |
| `/api/v1/audio-effects/apply` | POST | Reverb, distancia, ruido, paneo, filtro |
| `/api/v1/pronunciation` | POST/GET | Diccionario (crear, listar) |
| `/api/v1/pronunciation/{id}` | PUT/DELETE | Editar / borrar regla |
| `/api/v1/pronunciation/import` | POST | Importar .pls |
| `/api/v1/pronunciation/export` | GET | Exportar .pls |
| `/api/v1/history` | GET | Historial (filtros, paginación) |
| `/api/v1/history/{id}/audio` | GET | Audio generado |
| `/api/v1/history/{id}` | DELETE | Borra registro + audio |
| `/api/v1/history/{id}/verify` | POST | **Verificación por transcripción Whisper** (WER normalizado) |
| `/api/v1/usage` | GET | Contador de uso (caracteres, minutos) |
| `/api/v1/sfx` | POST | Efectos de sonido (Stable Audio Open) |
| `/api/v1/speech-to-speech` | POST | Voice changer vía stt-tts |
| `/api/v1/dubbing` | POST | Doblaje ES↔EN (202, asíncrono) |
| `/api/v1/dubbing/{job_id}` | GET | Estado + segmentos |
| `/api/v1/dubbing/{job_id}/segments/{n}/edit` | POST | Re-traducir y re-sintetizar un segmento |
| `/api/v1/dubbing/{job_id}/download` | GET | Vídeo/audio doblado |

### Verificación del audio generado (método Whisper)

`POST /api/v1/history/{id}/verify` transcribe el audio generado con
faster-whisper y lo compara con el texto esperado **normalizado**
(minúsculas, sin tildes ni puntuación — Whisper normaliza grafías
fonéticas). Devuelve `wer`, palabras coincidentes y `verdict`
(`ok` ≤ 0.15, `revisar` ≤ 0.35, `fallo` > 0.35). Es la pieza que usa la
auditoría para verificar cada generación sin escuchar una por una.

## Qué llama el frontend (y qué no)

El frontend (`app/js/api.js`) llama solo a estas rutas: `GET /health`,
`GET /tts/voices`, `GET /library/voices`, `POST /library/voices/{id}/favorite`,
`POST /tts`, `POST /voices/instant-clone`, `GET /voices/{id}/preview`,
`DELETE /voices/{id}`, `POST /voices/design`, `GET /voices/design/{id}/preview`
(vía fetch con token), `POST /voices/design/{id}/save`,
`POST /speech-to-speech`, `POST /dubbing`, `GET /dubbing/{job_id}`,
`POST /dubbing/{job_id}/segments/{n}/edit`, `GET /dubbing/{job_id}/download`
(vía fetch con token), `POST /sfx`, `GET/POST/DELETE /pronunciation`,
`GET /pronunciation/export` (vía fetch con token) y
`DELETE /history/{id}` (solo si la generación tiene `remoteId`).

Sin UI (implementados en el backend, fuera del alcance de la v1 del
frontend): `/tts/stream`, `/audio/speech`, `/stt`, `/align`, `/isolate`,
`/audio-effects/catalog`, `/audio-effects/apply`, `PUT /pronunciation/{id}`,
`POST /pronunciation/import`, `GET /history`, `GET /history/{id}/audio`,
`POST /history/{id}/verify`, `GET /usage`, `GET /models`. El historial
que ve el usuario es local (IndexedDB); el del backend solo existe para
las generaciones que el propio backend creó.

## Endpoints en 501 (fases 3–4 y no replicables, sin fingir)

Diálogo multi-hablante, Studio/Projects, Reader, Music, Professional Voice
Cloning (LoRA manual), Voice Remix, agentes conversacionales, Eleven
Realtime, Realtime Translation, ElevenAI, STT en vivo (WebSocket) y el modo
`denoise` del isolator. Cada uno devuelve 501 con el motivo y la
alternativa real. También es 501 `voice-conversion` en
`/speech-to-speech` (solo está la vía `stt-tts`, que pierde la
interpretación original y lo dice en la cabecera `X-Note`).

## Errores

| Código | Cuándo |
|---|---|
| 400 | Entrada inválida (texto vacío, muestra < 3 s, idioma no cubierto) |
| 401 | Falta el token o no es válido (solo si `API_TOKEN` está fijado) |
| 404 | Voz, generación, trabajo o regla desconocidos |
| 409 | El doblaje aún no terminó (edita o descarga cuando esté `done`) |
| 413 | Fichero demasiado grande |
| 422 | No se pudo hacer lo pedido con los datos (p. ej. diarización sin pyannote, doblaje a idioma no cubierto, verificar un audio sin texto) |
| 429 | Rate limit (60/min general, 20/min en rutas pesadas) |
| 501 | Función de fase 3–4 o no replicable |
| 503 | Modelo no instalado o sin GPU ("arranca el backend GPU") |

## Seguridad (checklist replica-backend)

- Secretos solo en variables de entorno; `.env.example` sin valores;
  `.env*` en `.gitignore`; nada en el bundle del cliente.
- Validación de entrada en el servidor en cada ruta (Pydantic + límites
  de tamaño/tipo con magic bytes en uploads).
- Token opcional por entorno (`API_TOKEN`); nunca hardcodeado.
- Rate limits en todo lo que genera audio (la GPU/CPU es el recurso escaso).
- Borrado de voz que borra de verdad su audio de referencia.
- Sin datos de usuario en URLs ni en logs (los logs no imprimen el texto
  a sintetizar ni el token).
- Tiempos en UTC en la base de datos; jobs con registro de fallos
  (`jobs.error` = dead-letter log).
- Dependencias fijadas; sin pagos, sin webhooks, sin Supabase/Stripe
  (no aplican a este backend local).

## Licencias de los modelos

| Modelo | Licencia |
|---|---|
| Kokoro-82M | Apache 2.0 |
| Qwen3-TTS (Base/CustomVoice/VoiceDesign) | Apache 2.0 |
| faster-whisper / Whisper | MIT |
| Demucs | MIT |
| Stable Audio Open 1.0 | Stability AI Community License (< 1M USD/año) + términos en HF |
| MarianMT (doblaje ES↔EN) | Apache 2.0 |
| VoxCPM2 (no integrado) | Apache 2.0 |

Uso privado de 2 personas; no redistribuir ni cobrar por el clon con
estos modelos dentro sin revisar cada licencia.

## Tests

```bash
python -m pytest tests/ -v
```

Cubren health, validación 400/422, 404, 501 de fases 3–4, 503 sin motor,
el CRUD del diccionario y, desde la corrección 2026-11-20, 401 con token,
CORS (localhost permitido, origen desconocido bloqueado), 429 del
middleware (ya no 500), el contrato de doblaje (JSON y cadena vacía),
el rechazo de traversal en previews de diseño y los rechazos honestos
de TTS (idioma desconocido, idioma sin pipeline Kokoro, similarity en
voz clonada). No necesitan GPU ni modelos instalados: los endpoints
que exigen motor devuelven 503, y eso es lo que se verifica.

## Qué queda pendiente de verificar en Kaggle

Ver `PENDIENTES_KAGGLE.md`: nada de lo que exige GPU se ha probado en GPU
en esta sesión. No se afirma que funcione en GPU hasta el primer run con
audio real generado y verificado con `POST /history/{id}/verify`.
