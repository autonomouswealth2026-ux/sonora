# CORRECCIONES — Sonora (clon web de ElevenLabs)

- **Fecha:** 2026-11-20/21 (hora de La Habana).
- **Alcance:** `app/` + `backend/`, solo correcciones de lo listado en
  `AUDIT.md` (9 bloqueantes, 17 altos, 9 medios, 4 bajos) y en
  `VERIFICACION.md` §5 (6 defectos B1–B6). Sin funciones nuevas.
- **Conteo final: bloqueantes 9/9, altos 17/17, medios 8/9, bajos 3/4,
  defectos de verificación 6/6.** Los 2 no contados como corregidos
  (M3, L4) son errores de la auditoría verificados contra el código,
  justificados en su sección: no había nada que cambiar.
- **Cambios de contrato (FEATURE_MAP.md v2):** solo dos, ambos para
  arreglar algo roto y anotados aquí: (1) §1 ya no lista `pcm_44100`
  como formato (el backend solo admite `mp3|wav`, M5); (2) la cabecera
  STS `X-Transcribed-Text` pasa a `X-Transcribed-Text-B64` (base64
  UTF-8) porque el texto en claro no es Latin-1 y daba 500 (A12).
  Adiciones compatibles: `GET /dubbing/{id}` devuelve también
  `target_languages` y `result_paths`; `POST /dubbing/{id}/segments/{n}/edit`
  acepta `?language=`; `TTSRequest` gana los campos `similarity` y
  `normalize`. Ningún archivo supera 1.000 líneas (máx. `screens.js`, 899).

## 1. Bloqueantes (9/9)

### B1 — Doblaje: `target_languages` JSON vs coma
- `backend/app/routers/dubbing.py:83-99` — nuevo `_parse_targets()`:
  acepta JSON (`["en"]`), lista por comas (`en,es`) y un solo idioma.
- `app/js/screens.js` (iniciarDoblaje) — el frontend ya manda el valor
  plano (`en`), no `JSON.stringify([...])`.

### B2 — Doblaje: `completed` y etapas que el backend nunca emitía
- `backend/app/routers/dubbing.py` (`_run_dubbing`) — la etapa de
  síntesis es ahora `synthesize`, no `synthesize-{tgt}`. El estado
  guardado sigue siendo `done` (contrato interno); el frontend lo
  traduce a `completed` en `app/js/screens.js` (consultarDoblaje),
  con tolerancia a `synthesize-*` por si llega una etapa vieja.

### B3 — VoxCPM2 ofrecido y rechazado (422)
- Quitado del selector: `app/index.html:78` (opción eliminada) y
  `app/js/app.js:186` (entrada `voxcpm2` de `MODELOS` eliminada).
  El registro del backend (`engines.py`, `voxcpm2`, no integrado) y
  `PENDIENTES_KAGGLE.md` se mantienen como están: no se finge
  integración. `app/index.html:377` (Acerca) ahora dice explícitamente
  «VoxCPM2 no está integrado».

### B4 — Sliders placebo
- `backend/app/schemas.py:12-26` — `TTSRequest` gana `similarity`
  (antes Pydantic lo ignoraba en silencio).
- `backend/app/routers/tts.py:62-160` (`synthesize()`) — `similarity`
  se rechaza con 422 en todas las rutas (ningún motor la expone);
  `stability`/`style` se rechazan con 422 en voces clonadas/diseñadas
  y en Kokoro; en CustomVoice se traducen a un `instruct` graduado
  por valor (no binario: ≥0,7 / ≤0,3). `speed` en voces clonadas es
  ahora real: remuestreo del audio resultante (`_synthesize_clone`).
- `app/js/app.js` (`aplicarModelo`, `generar()`) — el soporte de cada
  slider depende de la voz activa (Kokoro: solo velocidad; CustomVoice:
  velocidad + estabilidad/estilo; clonadas/diseñadas: solo velocidad);
  `similitud` siempre deshabilitada con su motivo; `similarity` no se
  envía nunca.

### B5 — Conflicto de dependencias GPU
- `backend/requirements-gpu.txt:11-17` — `transformers==4.57.3` y
  `accelerate==1.12.0` (lo que exige `qwen-tts==0.1.1`), en vez de
  4.48.3/1.4.0. Sin re-verificar en Kaggle (pendiente del run).

### B6 — CORS roto para GitHub Pages → trycloudflare
- `backend/build_notebook.py` (celda 5) — el notebook fija
  `CORS_ORIGINS` con la URL de GitHub Pages por defecto
  (`https://carlosmiguelvaldesrodriguez-prog.github.io/elevenlabs-clon`,
  sobreescribible con `CORS_ORIGINS` en Secrets). Regenerado
  `backend/kaggle_notebook.ipynb` (8 celdas).
- `backend/.env.example:13-15` — ejemplo corregido con la URL completa.
  El default de `config.py` (solo localhost) se mantiene para desarrollo.

### B7 — Grabación `.webm` rechazada de extremo a extremo
- `app/js/screens.js:16-18` — `validarArchivoAudio` admite `audio/webm`
  y `.webm`; `app/index.html` — inputs de muestra y STS aceptan WebM y
  la ayuda lo dice.
- `backend/app/security.py:133` — `AUDIO_EXTS` incluye `webm` (el magic
  `\x1a\x45\xdf\xa3` ya estaba en `_MAGIC`).
- Verificado en vivo: muestra `.webm` generada con ffmpeg →
  `POST /voices/instant-clone` 201, duración 5,15 s leída, referencia
  transcrita.

### B8 — Previews de Voice Design y variantes SFX: URLs relativas 404
- `app/js/api.js` — nuevo `blobUrl(rutaRelativa)`: descarga con base
  + `Authorization` y devuelve una blob URL para `<audio src>`.
- `app/js/screens.js` — previews de diseño (`disenarVoz`) y variantes
  SFX (`generarSfx`) usan `blobUrl()`; ya no se asigna la URL relativa
  directa al `src`.

### B9 — Voz a voz: método por defecto 501
- `app/index.html:212` — el método seleccionado por defecto es ahora
  `stt-tts` (implementado); `voice-conversion` queda visible y marcado
  «no implementada todavía (501)».
- `app/js/api.js` (`mensajeEnEspanol`) — el 501 ya tiene mensaje propio
  en español (antes caía en el genérico).

## 2. Defectos de verificación (6/6)

- **VERIF B1 — `av` sin fijar** → `av==13.1.0` en
  `backend/requirements-gpu.txt` y `backend/requirements-cpu.txt`
  (también A14). Verificado en vivo: `/verify` 200, WER 0,125.
- **VERIF B2 — WebSockets que no conectan** →
  `backend/app/routers/not_implemented.py` ya no usa `Depends`
  a nivel de router (cada ruta HTTP lleva su propio `Depends`, los WS
  usan `require_auth_ws()` de `backend/app/security.py`, que lee el
  token de la cabecera o de `?token=` y cierra con 1008 si falta).
  Tests: cierre 1011 sin token configurado, 1008 con token fijado.
- **VERIF B3 — `/tts/stream` sin motor: 200 con 0 bytes** →
  `backend/app/routers/tts.py` (`tts_stream`) sintetiza la primera
  frase ANTES de devolver el `StreamingResponse`: sin motor sale 503.
  Verificado en vivo (venv sin motor): 503 con 179 B.
- **VERIF B4 — `/audio-effects/apply` con preset inválido: 500** →
  `backend/app/routers/isolate.py` captura `ValidationError` y devuelve
  422. Verificado en vivo: `reverb=catedral` → 422.
- **VERIF B5 — `/dubbing` con `target_languages=""`: 202** →
  `backend/app/routers/dubbing.py` (`create_dubbing`): el parámetro es
  `None` solo si no se envía (default `en`); vacío explícito → 400.
  Verificado en vivo: `""` → 400.
- **VERIF B6 — CORS por defecto** → ver B6 arriba (notebook).

## 3. Altos (17/17)

- **A1 — Doblaje multi-idioma se sobrescribía** →
  `backend/app/store.py` (columna `language` en `dubbing_segments` con
  migración para bases viejas; `save_segments`/`list_segments`/
  `update_segment` por idioma) y `backend/app/routers/dubbing.py`
  (`_run_dubbing` guarda por idioma, `result_paths` por idioma en el
  payload del job; `GET /dubbing/{id}` y `download` eligen por
  `language`). Sin verificar en vivo con 2 idiomas (exige GPU:
  MarianMT + Qwen); pendiente del run de Kaggle.
- **A2 — Editar un segmento no se oía** →
  `backend/app/routers/dubbing.py`: `_input_path()` (extensión real de
  la entrada, no siempre `.wav`), `_rebuild_result()` (reconstruye
  timeline + mezcla + re-mux), `edit_segment()` acepta `?language=` y
  reconstruye el resultado tras re-sintetizar. Los audios de segmento
  ya se guardan en `audio_dir` (persistentes), no en el tmpdir del job.
- **A3 — Destinos fr/de/pt/it no soportados** → quitados del selector
  (`app/index.html:247`, solo `en`/`es`).
- **A4 — Descarga de doblaje `format=mp4` fijo y sin token** →
  `app/js/api.js` (`descargarDoblaje()`, fetch con token) y
  `app/js/screens.js` (formato según la entrada: `mp4` si era vídeo,
  `mp3` si era audio; texto del botón acorde).
- **A5 — Kokoro de/ko/ru → inglés en silencio** →
  `backend/app/engines.py` (`KOKORO_LANG_CODES` sin de/ko/ru;
  `synthesize_kokoro` rechaza idiomas sin pipeline) y
  `backend/app/routers/tts.py` (el idioma pedido debe tener pipeline,
  400 si no; el pipeline usado es el del idioma DE LA VOZ, no el
  pedido). Verificado en vivo: `language=de` → 400.
- **A6 — VRAM Qwen 1.7B 6 GB vs piso 8 GB** →
  `backend/app/engines.py` (`vram_gb: 8` en los tres modelos 1.7B, con
  nota del tokenizer 0,68 GB) y `backend/README.md` («~8 GB VRAM»).
  Medición en Kaggle pendiente (PENDIENTES_KAGGLE.md punto 10).
- **A7 — Frontend local que diverge del backend** →
  `app/js/screens.js`: diccionario remoto primero (con `remoteId` y
  aviso si solo queda local); contador «Este mes» filtra por mes en
  curso; borrar voz: primero backend, si falla no se borra en local;
  borrar historial: intenta el borrado remoto si hay `remoteId`.
  `app/js/app.js` (`generar()`): envía `dictionary_id='local'` si hay
  reglas y guarda `remoteId` (`gen_…`). `backend/app/routers/tts.py`
  (`apply_dictionary`): con `dictionary_id` aplica solo las reglas de
  ese idioma (antes se aplicaban a todo sin `dictionary_id`).
- **A8 — Voice Lab sin voces fijas ni favoritos** →
  `app/js/store.js` (las 9 voces Qwen CustomVoice en `VOCES_FIJAS`);
  `app/js/api.js` (`listarBiblioteca()`, `favoritoVoz()`); `app/js/screens.js`
  (`renderVoces` mezcla biblioteca del backend + locales, con estrella
  ★/☆; las fijas no se pueden borrar); `app/index.html` + `app/js/app.js`
  (opción y entrada `qwen3-tts-1.7b-customvoice` en el selector de modelo,
  y `pintarVozActiva` ya no fuerza Kokoro a las CustomVoice).
- **A9 — Tests sin ejecutar** → ejecutados: **40/40** (ver §6). Nuevos
  tests: 401, CORS, 429 del middleware, contrato de doblaje (JSON y
  vacío), traversal en preview de diseño, rechazos TTS (idioma `xx`,
  Kokoro `de`, `similarity` en clonada), WebM en `AUDIO_EXTS`, WS 1008
  con token. El test WS original comprobaba mal el cierre (`"1011" in
  str(exc)`; el `str()` de `WebSocketDisconnect` es vacío): ahora
  comprueba `exc.code`.
- **A10 — Voice Design: 3 candidatos idénticos** →
  `backend/app/engines.py` (`design_voices`): cada candidato se pide
  con una variante explícita del instruct y se descartan duplicados
  byte a byte (hasta 3 reintentos por candidato). Sin verificar en vivo
  (exige GPU).
- **A11 — `/tts/stream`: sin historial, cabecera a ciegas, excepción
  en el generador** → cabecera recortada buscando el chunk `data`
  (`_strip_wav_header`); el stream queda en el historial como `/tts`;
  la excepción del motor ya no se lanza dentro del generador sin
  motor (ver VERIF B3). Verificado en vivo: stream 200 con 151.244 B
  y entrada `gen_2c6f475b7ec8` en el historial.
- **A12 — STS devuelve el texto en cabecera HTTP** →
  `backend/app/routers/sts.py`: `X-Transcribed-Text` eliminado;
  `X-Transcribed-Text-B64` (base64 UTF-8) + `X-Transcribed-Chars`.
  Verificado en vivo: STS 200, cabecera B64 presente y decodificable,
  sin cabecera en claro. Cambio de contrato anotado arriba.
- **A13 — Path traversal en preview de diseño** →
  `backend/app/routers/voices.py` (`_candidate_path()`: solo
  `cand_[0-9a-f]+` y ruta resuelta dentro de `voices_dir`), aplicado
  en preview y en save. Verificado en vivo: `..%2Fsecreto` → 404.
- **A14 — `av` sin fijar** → ver VERIF B1.
- **A15 — Rate-limit con `HTTPException` en el middleware** →
  `backend/app/main.py`: el middleware captura la excepción y devuelve
  429 JSON (antes subía como 500). Test nuevo incluido.
- **A16 — `language` acepta cualquier `[a-z]{2}`** →
  `backend/app/schemas.py` (`LANGUAGE_PATTERN`, lista cerrada de 10
  idiomas, también en `VoiceDesignRequest` y reglas de pronunciación);
  `backend/app/engines.py` ya no cae a «Spanish» por defecto en Qwen
  (lanza `ValueError` → 400). Verificado en vivo: `language=xx` → 422.
- **A17 — API abierta por defecto + túnel público** →
  `backend/build_notebook.py` (celda 5): en Kaggle el token es
  obligatorio — si no viene en Secrets se genera uno aleatorio y se
  imprime para copiarlo en Ajustes. `backend/README.md` actualizado.
  El default local (abierto sin token) se mantiene solo para desarrollo.

## 4. Medios (8/9)

- **M1 — Textos largos: WAV inválido al concatenar** →
  `app/js/app.js` (`combinarWav()`: reescribe una sola cabecera WAV
  con los PCM concatenados) y `app/index.html` (sin `maxlength="10000"`
  en el textarea; el aviso ahora dice que se trocea por bloques).
- **M2 — `verify_history` elegía modelo por prefijo** →
  `backend/app/routers/history.py`: conjunto explícito de modelos Qwen.
- **M3 — SFX: textarea 500 vs backend 450 — NO APLICABLE (error de la
  auditoría).** Verificado: `backend/app/schemas.py` (`SFXRequest`)
  fija `max_length=500`, igual que el frontend. El «450» es el límite
  del prompt de SFX **en la app de ElevenLabs** (FEATURE_MAP.md §11,
  «prompt de hasta 450 caracteres en la app»), no de este backend.
  Sin cambio.
- **M4 — Duración desconocida (0) pasaba el mínimo** →
  `app/js/screens.js` (`recibirMuestra`): duración 0 → error y la
  muestra no se acepta.
- **M5 — Deriva de FEATURE_MAP: `pcm_44100`** → eliminado de
  FEATURE_MAP.md §1 (el backend solo admite `mp3|wav`). La segunda
  mitad del hallazgo era un error de la auditoría: `audio_effects` SÍ
  existe en el contrato (`schemas.py:27`, `tts.py:114`).
- **M6 — Documentación con coberturas falsas** →
  `app/VERIFICACION.md` (§1.7 lista real de endpoints que llama el
  frontend; §2 FEATURE_MAP v2 con deltas aplicadas; §3 VoxCPM2: sí
  aparecía en el selector, quitado el 2026-11-20) y `backend/README.md`
  (nueva sección «Qué llama el frontend (y qué no)» con las 15 rutas
  implementadas sin UI).
- **M7 — Al restaurar ajustes, el idioma de la voz se perdía** →
  `app/js/app.js` (`init` lee `vozActivaIdioma`; `setVozActiva`
  persiste id, nombre, origen, modelo E idioma).
- **M8 — El degradado re-habilitaba sin revalidar** →
  `app/js/app.js` (`aplicarDegradado` llama a `validarSts()` además de
  `validarClonar()`); `app/js/screens.js` exporta `validarSts`.
  Doblaje y SFX validan al pulsar (comprueban el archivo), sin cambio.
- **M9 — Interruptor «Normalizar volumen» placebo** →
  `backend/app/schemas.py` (`TTSRequest.normalize`, por defecto true)
  y `backend/app/engines.py` (los sintetizadores respetan el flag);
  `app/js/app.js` (`generar()` envía `normalize` desde Ajustes).

## 5. Bajos (3/4)

- **L1 — Cachés de Python en el árbol** → eliminados `__pycache__/` y
  `.pytest_cache/`; `backend/.gitignore` ya los cubría.
- **L2 — Código muerto** → eliminado: `concat_wav_bytes`
  (`audio_utils.py`), `safe_name` (`security.py`), `VoiceRemixRequest`
  (`schemas.py`), `MODELS_DIR` (`config.py` y `.env.example`),
  `modelos()`/`uso()`/`historialRemoto()`/`urlExportarDiccionario()`
  (`api.js`). `borrarHistorialRemoto` se conserva y ahora se usa (A7).
- **L3 — Health polling cada 60 s** → cada 5 min y solo con la pestaña
  visible (`app/js/app.js`).
- **L4 — Google Fonts externo — NO APLICABLE (ya mitigado).** Verificado:
  `app/css/app.css:9-10` define `--font-display` y `--font-body` con
  fallback del sistema (`system-ui, sans-serif`); sin red hay
  tipografía prevista. Sin cambio.

## 6. Re-verificación

- `python3 -m py_compile backend/app/*.py backend/app/routers/*.py
  backend/tests/test_api.py` — OK.
- `node --check` en los 5 JS (`api`, `store`, `player`, `screens`,
  `app`) — 5/5 OK.
- Cruce de IDs frontend: 172 IDs en `index.html`, 0 faltantes en JS.
- `pytest tests/ -q` (venv `sonora-base`, límites altos): **40/40**
  (30 originales + 10 nuevos). Antes de esta corrección la suite era
  26/30 en el mismo entorno.
- Ciclo vivo con el venv `sonora` (torch CPU + Kokoro + faster-whisper
  + `av==13.1.0`), backend en `:8001`, `DATA_DIR=/tmp/sonora-corr`:
  - `POST /tts` ef_dora → 200, 247.244 B WAV, `gen_343ae01ee52e`.
  - `POST /history/gen_343ae01ee52e/verify` → **WER 0,125, verdict `ok`**
    (mismo valor que la verificación original).
  - `POST /tts/stream` → 200, 151.244 B, entrada en historial.
  - `POST /voices/instant-clone` con `.webm` → 201, duración 5,15 s.
  - `POST /speech-to-speech` stt-tts → 200, 107.085 B, cabecera B64.
  - `language=de` → 400; `language=xx` → 422; `similarity` en clonada
    → 422; `stability` en Kokoro → 422; traversal de diseño → 404.
- Ciclo vivo con el venv `sonora-base` (sin motor), backend en `:8002`:
  `/tts/stream` → 503 (179 B, no 200 vacío); `/audio-effects/apply`
  `reverb=catedral` → 422; `/dubbing target_languages=""` → 400;
  `/dubbing target_languages='["en"]'` → 202; `target_languages=en`
  → 202. Servidores apagados al terminar.

## 7. Qué queda sin corregir / sin verificar (no es humo)

- **Sin verificar en GPU** (pendiente del run de Kaggle, checklist en
  `backend/PENDIENTES_KAGGLE.md`): resolución de `requirements-gpu.txt`
  (B5), CORS + token en el notebook (B6, A17), doblaje multi-idioma de
  extremo a extremo (A1, A2), Voice Design sin duplicados (A10),
  clonación Qwen y `speed` por remuestreo en voces clonadas (B4),
  VRAM 8 GB con Whisper en el mismo proceso (A6).
- **Sin verificar en navegador vivo** (`delivery_audit_gate`): las 7
  pantallas con backend en línea y apagado, en el teléfono de Carlos.
  El contrato frontend↔backend se verificó por código, tests y curl,
  no en navegador.
- `X-Forwarded-For` confiable para rate-limit (puerta 2 de AUDIT.md,
  sin número A): no se tocó — el despliegue previsto es por túnel y
  el primer salto es el del túnel; queda documentado como riesgo
  conocido, no como hallazgo numerado.
- El historial remoto del backend (`GET /history`) sigue sin UI: el
  historial que ve el usuario es local por diseño (ver README).

## Cierre de los hallazgos nuevos de AUDIT2 (N1–N3)

- **N1 (media) — suite 40/40 no reproducible con la orden documentada:** cerrado. `backend/tests/test_api.py` fija ahora `RATE_LIMIT_PER_MINUTE=10000` y `HEAVY_RATE_LIMIT_PER_MINUTE=10000` antes de importar la app (mismo patrón que el resto de variables de entorno de la suite). Verificado: `pytest tests/ -q` en el venv `sonora-base` da **40 passed**. Matiz documentado en la cabecera del test: en el venv `sonora` (con Kokoro instalado) 5 tests fallan por diseño — el motor carga y devuelve 200 con audio real donde la suite espera 503 ("sin motores"). No es un defecto del producto.
- **N2 (baja) — FEATURE_MAP §8 desactualizado:** cerrado. El método por defecto de voz a voz es ahora `stt-tts`; `voice-conversion` figura como 501 no implementado.
- **N3 (baja) — cabecera B64 sin documentar ni consumir:** cerrado. `X-Transcribed-Text-B64` (transcripción original en base64 UTF-8) documentada en FEATURE_MAP §8, con la nota de que el frontend aún no la consume.
