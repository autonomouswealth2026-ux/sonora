# AUDITORÍA — Clon web de ElevenLabs «Sonora»

- **Fecha:** 2026-11-20
- **Alcance:** `app/` (SPA estática, 7 pantallas) + `backend/` (FastAPI) + documentos (`DESIGN.md`, `FEATURE_MAP.md` v2, `RESEARCH.md`, `REA.md`, `SKILL_AUDIT.md`, `DECISIONES.md`, `DELTAS_REA_APLICADAS.md`, `app/VERIFICACION.md`, `backend/PENDIENTES_KAGGLE.md`)
- **Método:** revisión de código estática + verificación web de modelos (2026-11-20). Sin navegador en vivo y sin GPU: lo no probado en ejecución queda listado al final.
- **Regla del auditor:** no se corrigió nada; solo se listan fallos con `archivo:línea` y severidad.

## Veredicto global: NO APTO

El clon está bien estructurado, es honesto en lo que declara en 501 y no tiene secretos ni marca copiada, pero **9 hallazgos bloqueantes rompen flujos principales en el despliegue previsto** (frontend en GitHub Pages + backend en trycloudflare): el doblaje falla en todos sus pasos (422 en la creación, estado que nunca llega a «completado», descarga con formato fijo), la grabación de muestra se rechaza, el método por defecto de Voz a voz es un 501, las vistas previas de Voice Design y SFX usan URLs relativas que en producción son 404, los sliders de la pantalla principal no hacen nada en voces clonadas, VoxCPM2 se ofrece y el backend lo rechaza, el notebook de Kaggle no fija CORS y las dependencias GPU entran en conflicto de versiones. **No entregar hasta corregir los 9 bloqueantes; después, navegador vivo (`delivery_audit_gate`) y run de Kaggle.**

| Severidad | Conteo |
|---|---|
| Bloqueante | 9 |
| Alta | 17 |
| Media | 9 |
| Baja | 4 |
| **Total** | **39** |

## Tabla por puerta

| Puerta | Veredicto | Hallazgos |
|---|---|---|
| 1. `local-thermo-review` | **PASA con notas** | Sin archivos >1.000 líneas (mayor: `app/js/screens.js`, 797). Código muerto menor (L2). Sin TODO/FIXME. |
| 2. `local-ecc-revisores` | **FALLA** | Sin secretos reales y auth aplicada en `/api/v1/*`, pero: sin aislamiento por usuario (voces/historial globales para los 2 usuarios), API abierta por defecto + túnel público (A17), `X-Forwarded-For` confiable para rate-limit, `HTTPException` en middleware (A15), path traversal en preview de diseño (A13), subida completa en memoria. |
| 3. `replica-diff` + `replica-test` | **FALLA** | Contrato frontend↔backend roto en 5 puntos bloqueantes (B1, B2, B3, B4, B8, B9) + 15 endpoints implementados sin UI. Las 26 rutas en 501 son honestas y el frontend no tiene pantallas muertas para ellas. Fidelidad de diseño: tokens CSS copiados de `DESIGN.md` §3.6; marca propia «Sonora». |
| 4. `provider_model_verification` | **FALLA** | Todos los modelos existen con la licencia declarada, pero: conflicto de dependencias `qwen-tts` vs `transformers`/`accelerate` (B5), códigos Kokoro de/de/ru incorrectos (A5), VRAM Qwen 1.7B declarada 6 GB vs piso secundario de 8 GB (A6), `av` sin fijar (A14). |
| 5. Seguridad y honestidad | **FALLA** | Sin secretos ni marca copiada; 501 honesto. Pero el frontend presenta como disponibles funciones que no lo están (VoxCPM2, destinos de doblaje, sliders, método STS por defecto), y `backend/README.md` / `app/VERIFICACION.md` afirman coberturas falsas (M6). |

## Hallazgos bloqueantes

### B1 — Doblaje: el frontend envía `target_languages` como JSON y el backend lo parte por comas → 422 siempre
- `app/js/screens.js:402` — `fd.append('target_languages', JSON.stringify([...]))` envía `["en"]`.
- `backend/app/routers/dubbing.py:196-199` — `target_languages.split(",")` sobre `'["en"]'` produce `['["en"]']` → 422 «Idioma no admitido». **Ningún doblaje puede crearse.**

### B2 — Doblaje: el frontend espera `status === 'completed'` y etapas que el backend nunca emite
- `app/js/screens.js:428-433,464` — progreso y «Doblaje terminado» dependen de `status === 'completed'`; lista de etapas `transcribe|translate|synthesize|mix`.
- `backend/app/routers/dubbing.py:150,156,165,182-183` + `backend/app/store.py` — estados reales `queued|processing|done|failed`; etapas reales `synthesize-{tgt}` y `mix`. **El botón de descarga nunca aparece aunque el doblaje termine.**

### B3 — VoxCPM2 ofrecido en la UI pero rechazado por el backend
- `app/index.html:78` y `app/js/app.js:186` — VoxCPM2 en el selector, «máxima calidad (48 kHz), necesita GPU», con los 4 sliders habilitados.
- `backend/app/schemas.py:18-19` — `TTSRequest.model` no admite `voxcpm2` → 422. El modelo está registrado como no integrado (`backend/app/engines.py`, `backend/PENDIENTES_KAGGLE.md`). **Decidir: quitarlo del selector o integrarlo; no ofrecerlo roto.** Además `app/VERIFICACION.md` §3 afirma que no aparece en el selector — falso (M6).

### B4 — Sliders placebo en la pantalla principal (voces clonadas/diseñadas)
- `app/js/app.js:302-304` — el frontend envía `stability`, `similarity`, `style_exaggeration` (y `speed`) según el modelo.
- `backend/app/schemas.py:12-26` — `TTSRequest` no tiene campo `similarity`: Pydantic lo ignora en silencio.
- `backend/app/routers/tts.py:72-100` — `synthesize()` solo aplica `speed` en la ruta Kokoro; para voces clonadas/diseñadas `speed` no se pasa, y `stability`/`style_exaggeration` solo se traducen a un `instruct` genérico («Speak steadily» / «Be expressive») en CustomVoice. **En voces clonadas 3 de 4 sliders no hacen nada y el cuarto (`similarity`) no existe en el contrato.**

### B5 — Conflicto de dependencias: el install GPU de Kaggle no resuelve
- `backend/requirements-gpu.txt:11-12` — fija `transformers==4.48.3` y `accelerate==1.4.0`.
- `qwen-tts==0.1.1` (PyPI, verificado 2026-11-20 en dos fuentes) exige `transformers==4.57.3` y `accelerate==1.12.0` (o `transformers>=4.57.3` según otra fuente; en cualquier caso 4.48.3 está por debajo del mínimo). **pip fallará en el notebook antes de probar nada.** Subir `transformers` a 4.57.3 y `accelerate` a 1.12.0 y re-verificar el resto del pin.

### B6 — CORS roto para el despliegue previsto (GitHub Pages → trycloudflare)
- `backend/app/config.py:28-40` — por defecto `CORS_ORIGINS` solo permite localhost.
- `backend/build_notebook.py:130-140` (celda 5) — el notebook no fija `CORS_ORIGINS`; la URL de GitHub Pages solo aparece como comentario en `backend/.env.example:13-15` y los pasos de Kaggle del README no la mencionan. **Con el despliegue previsto, el navegador bloqueará todas las llamadas.**

### B7 — La grabación de muestra se rechaza en el frontend y en el backend
- `app/js/screens.js:99-100` — MediaRecorder produce `muestra-grabada.webm`.
- `app/js/screens.js:16-18` — `validarArchivoAudio` no admite `audio/webm` ni `.webm` → «Formato no soportado».
- `backend/app/security.py:133,138` — `AUDIO_EXTS` no incluye `webm` (solo `MEDIA_EXTS`). **El flujo «Grabar muestra» de Voice Lab está roto de extremo a extremo.**

### B8 — Voice Design y SFX multi-variante: URLs relativas usadas como `src` sin base ni token
- `backend/app/routers/voices.py:172` — `preview_url` es relativa (`/api/v1/voices/design/{id}/preview`).
- `backend/app/routers/sfx.py:69-70` — `audio_url` de variantes también relativa.
- `app/js/screens.js:213-216` y `app/js/screens.js:510-512` — se asignan directas a `<audio src>`; en producción (Pages ≠ trycloudflare) son 404, y tampoco llevan el `API_TOKEN`. La vista previa de clonación instantánea sí usa `fetch` con base y funciona (`screens.js:161`, `vistaPreviaVoz`). **En producción no suena ninguna preview de diseño ni variante de SFX.**

### B9 — Voz a voz: el método por defecto es un 501
- `app/index.html:212` — `voice-conversion` es la opción `selected` por defecto.
- `backend/app/routers/sts.py:35-41` — ese método devuelve 501 («no implementado»). **El primer clic de un usuario en Voz a voz es un error.** Además `mensajeEnEspanol` (`app/js/api.js`) no mapea 501.

## Hallazgos de severidad alta

### A1 — Doblaje multi-idioma: `result_path` y segmentos se sobrescriben por idioma
- `backend/app/routers/dubbing.py:144,177-183` — en el bucle por idioma, `store.save_segments(job_id, ...)` y `result_path` se reescriben; solo queda el último idioma. **Pedir 2 destinos destruye el primero.**

### A2 — Editar un segmento no reconstruye el resultado y usa una ruta inexistente
- `backend/app/routers/dubbing.py:288` — `ref_path = {job_id}-input.wav` aunque la entrada se guarda con su extensión real (`.mp3`/`.mp4`).
- `backend/app/routers/dubbing.py:296-300` — `edit_segment` actualiza la tabla pero no regenera el audio ni reconstruye el timeline: **la edición no se oye al descargar.**

### A3 — Doblaje: el selector ofrece fr/de/pt/it, el backend solo admite es↔en
- `app/index.html:248` — destinos fr/de/pt/it.
- `backend/app/routers/dubbing.py:208-212` — 422 para cualquier par distinto de es↔en (coherente con MarianMT, puerta 4). **Quitar los destinos no soportados del selector o ampliar el backend.**

### A4 — Descarga de doblaje: `format=mp4` fijo y sin token
- `app/js/api.js:144` — `urlDescargaDoblaje` siempre pide `format=mp4`.
- `app/js/screens.js:469` — se usa como `href` directo, sin token: con entrada de audio el backend responde 400, y con `API_TOKEN` configurado, 401. **La descarga de doblaje de audio nunca funciona como está.**

### A5 — Kokoro: idiomas de/ko/ru mapeados en silencio a inglés americano
- `backend/app/engines.py:48-49` — `KOKORO_LANG_CODES` mapea `de`, `ko`, `ru` a `"a"` (inglés americano). Los códigos reales de Kokoro son solo `a, b, e, f, h, i, j, p, z` (verificado 2026-11-20): no existe alemán, coreano ni ruso en Kokoro. **El usuario pide alemán y recibe síntesis con pipeline inglés sin aviso.** Además el pipeline se elige por `language` pedida, no por la voz (`backend/app/routers/tts.py:84-85`): `ef_dora` + `language=en` mezcla voz española con pipeline inglés.

### A6 — Qwen 1.7B: VRAM declarada 6 GB frente a piso secundario de 8 GB
- `backend/app/engines.py:89,100,106` — `vram_gb: 6` para los tres modelos Qwen 1.7B.
- Fuente secundaria (verificado 2026-11-20): piso de 8 GB VRAM para 1.7B, más tokenizer 0,68 GB no contabilizado. **No probado en GPU: medir en Kaggle antes de afirmar que cabe junto a Whisper en la misma T4 16 GB** (`backend/PENDIENTES_KAGGLE.md` punto 10).

### A7 — Diccionario, historial y voces: el frontend es solo local y diverge del backend
- `app/js/screens.js:762` — las reglas de pronunciación se crean en IndexedDB y el intento remoto se ignora en silencio; el frontend nunca envía `dictionary_id` (no hay campo en `TTSRequest`, `backend/app/schemas.py:12-26`), así que **las reglas del backend se aplican a todo y las del frontend a nada**.
- `app/js/screens.js:549-562` — el contador «Este mes» suma todo el historial, no el mes.
- `app/js/screens.js:305-311` — borrar una voz/historial borra primero en local y luego intenta el backend best-effort, con toast de éxito aunque el borrado remoto falle. **Los dos historiales divergen sin que el usuario lo sepa.**

### A8 — Voice Lab incompleto: no muestra las voces fijas ni las de CustomVoice; sin favoritos
- `app/js/screens.js:250` — `renderVoces` solo lista voces locales (IndexedDB); no aparecen las 3 fijas de Kokoro ni las 9 de Qwen CustomVoice que sí existen en el backend.
- `app/js/api.js:64` — existe `listarVoces` pero nunca se llama; no hay wrapper para `GET /library/voices`.
- `DESIGN.md` §4.4 promete estrella de favorita y el endpoint existe; no hay UI de favorita (`app/js/screens.js:144,229` solo guarda `favorite: false`).

### A9 — Los 30 tests existen pero nunca se ejecutaron en esta sesión
- `backend/tests/test_api.py` — no hay `fastapi`/`pytest` en el Python del sistema ni en `~/workspace/apex/venv`; la ejecución no se pudo verificar.
- Cobertura ausente: nunca se aserta un 401 (auth no probada), ni CORS, ni rate-limit del middleware (solo test unitario del limiter, `test_api.py:353-361`), ni doblaje, ni el contrato frontend↔backend (B1–B4, B8–B9 pasarían desapercibidos).

### A10 — Voice Design: los 3 candidatos pueden ser idénticos
- `backend/app/engines.py:339-360` — `design_voices` llama `generate_voice_design` N veces con el mismo `instruct` y sin semilla; el propio docstring lo admite. **El usuario puede recibir 3 previews iguales.**

### A11 — `/tts/stream`: sin historial, cabecera WAV recortada a ciegas, excepción dentro del generador
- `backend/app/routers/tts.py:177-201` — no registra historial (a diferencia de `synthesize`), recorta 44 bytes fijos de cabecera WAV (puede ser más larga) y lanza `HTTPException` dentro del generador (comportamiento 500 vs error de stream sin verificar).

### A12 — STS devuelve el texto transcrito en una cabecera HTTP
- `backend/app/routers/sts.py:79` — `X-Transcribed-Text: text[:500]` con texto arbitrario del usuario (acentos, emojis, saltos de línea) → riesgo de 500 por caracteres no Latin-1 **después** de haber sintetizado.

### A13 — Path traversal en la preview de diseño
- `backend/app/routers/voices.py:169,183,197` — `store.voices_dir / f"{candidate_id}.wav"` con `candidate_id` controlado por el cliente (`../` permite leer `.wav` fuera del directorio). `resolve_voice` y los demás endpoints usan lookup en BD y no tienen este problema.

### A14 — `av` sin fijar: faster-whisper 1.2.1 se rompe con `av>=14`
- `backend/requirements-gpu.txt` no fija `av`, pese a la lección registrada en `AGENTS.md` (2026-10-19: fijar `av<14`, 13.1.0). **Si pip resuelve `av>=14`, el STT falla en Kaggle.**

### A15 — El middleware de rate-limit lanza `HTTPException` dentro del middleware
- `backend/app/main.py:55-64` — no verificado en ejecución si el cliente recibe 429 o un 500. El test existente es solo unitario (`backend/tests/test_api.py:353-361`).

### A16 — `TTSRequest.language` acepta cualquier `[a-z]{2}` y Qwen cae a «Spanish» en silencio
- `backend/app/schemas.py:21` — patrón `^[a-z]{2}$` sin lista cerrada.
- `backend/app/engines.py:42-44` — idiomas no soportados caen a «Spanish» sin aviso. **Pedir `xx` sintetiza en español sin error.**

### A17 — API abierta por defecto + túnel público = GPU expuesta
- `backend/app/main.py:77-80` y `backend/app/config.py:46-48` — sin `API_TOKEN` la API queda abierta por diseño documentado (aviso en log). En el despliegue previsto (trycloudflare, URL pública) **cualquiera con la URL puede consumir la GPU de Kaggle de Carlos**. Para 2 usuarios privados, el token debería ser obligatorio en el notebook.

## Hallazgos de severidad media

### M1 — Textos largos: concatenar WAV produce un WAV inválido y el límite del textarea contradice el mensaje
- `app/js/app.js:317-321` — los bloques se concatenan con `new Blob(audios, ...)`; con formato WAV eso deja cabeceras intermedias → WAV inválido. Cada bloque además crea una entrada de historial separada en el backend.
- `app/index.html:87` — `maxlength="10000"` impide el caso >10.000 que el mensaje de `app/js/app.js:260` dice trocear.

### M2 — `verify_history` elige el modelo por prefijo frágil
- `backend/app/routers/history.py:131` — `large-v3` si el modelo empieza por «qwen», criterio que se rompe con cualquier modelo futuro.

### M3 — SFX: el textarea admite 500 caracteres, el backend 450
- `app/index.html:284` — `maxlength="500"`; `backend/app/routers/sfx.py:28` — límite real 450 → 422 entre 451 y 500 caracteres.

### M4 — La duración desconocida pasa la validación mínima
- `app/js/screens.js:28-30,73-75` — `duracionDeAudio` resuelve `0` ante error de metadatos y la validación acepta duración desconocida; el mínimo de 3 s para clonación no se aplica en ese caso.

### M5 — Deriva de FEATURE_MAP: `pcm_44100` y `audio_effects` no existen en el contrato
- `backend/app/schemas.py:23,36` — `format`/`response_format` solo admiten `mp3|wav`; no hay campo `audio_effects`. Lo que FEATURE_MAP atribuye a la API pública no está en este backend.

### M6 — Documentación que afirma coberturas falsas
- `app/VERIFICACION.md` §2 — «deltas no recibidos» (desactualizado: las deltas existen y se aplicaron al mapa) y §3 — VoxCPM2 «no aparece en el selector» (falso, B3); el cruce de IDs/endpoints «pasa» sin detectar B1–B4, B8–B9.
- `backend/README.md` — afirma que el frontend cubre endpoints que en realidad nunca llama (15, ver puerta 3).

### M7 — Al restaurar ajustes, el idioma de la voz activa se pierde
- `app/js/app.js:436-444` — `vozActiva.language` se fija siempre a `'es'` al iniciar, aunque la voz guardada fuera de otro idioma.

### M8 — El modo degradado re-habilita botones sin revalidar
- `app/js/app.js:95-118` — `aplicarDegradado` re-habilita los botones al reconectar sin revalidar los requisitos por pantalla (muestra, consentimiento, texto). El estado puede quedar stale hasta el siguiente evento de entrada.

### M9 — El interruptor «Normalizar volumen» no hace nada
- `app/js/screens.js:751` — el ajuste se guarda en local, pero nunca se envía (no hay campo `normalize` en `TTSRequest`, `backend/app/schemas.py:12-26`); el backend normaliza siempre. **Interruptor placebo.**

## Hallazgos de severidad baja

### L1 — Cachés de Python en el árbol entregado
- `backend/__pycache__/`, `backend/.pytest_cache/` presentes. El directorio no es repo git; verificar `.gitignore` antes de subir a GitHub.

### L2 — Código muerto
- `backend/app/audio_utils.py` — `concat_wav_bytes` sin llamadas.
- `backend/app/security.py:192` — `safe_name` definido y sin uso.
- `backend/app/schemas.py` — `VoiceRemixRequest` sin endpoint (remix es 501).
- `backend/app/config.py` — `MODELS_DIR` sin uso en `engines.py`.
- `app/js/api.js` — `historialRemoto`, `uso()` y `modelos()` definidos y nunca llamados.

### L3 — Health polling cada 60 s
- `app/js/app.js:508` — `setInterval(comprobarBackend, 60000)`; ruido menor contra un backend con cuota de Kaggle.

### L4 — Google Fonts externo con fallback
- `app/index.html:9-11` — dependencia externa con fallback del sistema; coherente con `DESIGN.md`, pero sin red no hay tipografía prevista.

## Puerta 4 — Verificación de modelos (2026-11-20)

| Modelo pedido (backend) | ¿Existe? | Licencia | VRAM / T4 16 GB | Veredicto |
|---|---|---|---|---|
| Kokoro-82M (`hexgrad/Kokoro-82M`, `kokoro==0.9.4`) | Sí | Apache-2.0 | ~0,4 GB, CPU/GPU | **OK** — 54 voces; español solo `ef_dora`, `em_alex`, `em_santa`. Códigos solo `a,b,e,f,h,i,j,p,z` (A5). |
| Qwen3-TTS 1.7B Base (`Qwen/Qwen3-TTS-12Hz-1.7B-Base`) | Sí | Apache-2.0 | ~3,9 GB pesos + tokenizer 0,68 GB; piso secundario 8 GB | **OK con reserva** (A6) — 10 idiomas incl. español, clonación desde 3 s. |
| Qwen3-TTS 1.7B CustomVoice | Sí | Apache-2.0 | igual que Base | **OK** — 9 voces, coincide con el backend. |
| Qwen3-TTS 1.7B VoiceDesign | Sí | Apache-2.0 | igual que Base | **OK** — con la reserva de A10 (sin semilla). |
| Qwen3-TTS 0.6B Base | Sí | Apache-2.0 | ~1,6 GB | **OK**. |
| VoxCPM2 (`openbmb/VoxCPM2`) | Sí, **no integrado** | Apache-2.0 | ~8 GB, 2B, 30 idiomas, 48 kHz, `pip install voxcpm`, Python 3.10–3.13, CUDA ≥12 | **Honesto en backend, roto en UI** (B3). |
| faster-whisper (`large-v3`/`small`) | Sí | MIT | — | **OK** — diarización con pyannote exige aceptar condiciones en HF + `HF_TOKEN`; el backend devuelve 422 honesto si falta. Reserva A14 (`av`). |
| Demucs (`facebookresearch/demucs`, `htdemucs`) | Sí | MIT | — | **OK** — modo `denoise` en 501 honesto (DeepFilterNet como alternativa declarada, no integrada). |
| Stable Audio Open 1.0 (`stabilityai/stable-audio-open-1.0`) | Sí | Stability AI Community License (comercial gratis <1 M USD/año, con registro) | Sin cifra oficial publicada; el backend estima 8 GB | **OK** — repo gated en HF (aceptar términos + `HF_TOKEN`); hasta 47 s, estéreo 44,1 kHz. |
| MarianMT (`Helsinki-NLP/opus-mt-es-en` / `en-es`) | Sí | Apache-2.0 | — | **OK** — solo par es↔en, coherente con el 422 de A3. |
| Chatterbox / XTTS | — | — | — | **Correctamente excluidos** (Chatterbox retirado agosto 2026; Coqui cerrado diciembre 2025); solo aparecen como exclusión documentada (`backend/app/engines.py:23`). |

## Puerta 3 — Paridad frontend↔backend (contrato)

- **Rutas verificadas:** 37 implementadas + 26 en 501, coinciden con lo afirmado. Las 26 en 501 son honestas (`backend/app/routers/not_implemented.py`): diálogo, pro-clone (2), remix, música (2), proyectos (9), Reader (4), agentes (3), Realtime, Realtime Translation, ElevenAI, STT en vivo (WebSocket). El frontend no tiene pantallas ni botones muertos para ellas — correcto.
- **Endpoints implementados sin UI (15 de 37):** `/tts/stream`, `/audio/speech`, `/library/voices` (sin wrapper en `api.js`), `/stt`, `/align`, `/isolate`, `/audio-effects/catalog`, `/audio-effects/apply`, `PUT /pronunciation/{id}`, `POST /pronunciation/import`, `GET /history/{id}/audio`, `POST /history/{id}/verify`, preview de diseño vía API; `historialRemoto`, `uso()` y `modelos()` existen en `api.js` pero nunca se llaman. **Decidir cuáles se conectan y cuáles se declaran fuera de alcance; hoy el README sugiere una cobertura que no existe.**
- **Fidelidad de diseño:** tokens CSS de `DESIGN.md` §3.6 presentes en `app/css/app.css`; `lang="es"`, viewport, `prefers-reduced-motion`, `:focus-visible`, `safe-area-inset`, `100dvh`, táctil 44 px presentes. Marca propia «Sonora», eslogan «Tu voz, en tus manos»; las menciones a «ElevenLabs» en código son atribución honesta, referencias a endpoints/documentación o exclusiones. El botón «Diccionario» del wireframe de Estudio (`DESIGN.md` §8.1) no existe en `app/index.html` (el diccionario solo vive en Ajustes y es local, A7).
- **Puerta 1 (thermo):** ningún archivo supera 1.000 líneas; sin condicionales sin justificar relevantes; sin «code judo» detectado. Solo L2.

## Puerta 5 — Seguridad y honestidad (barrido)

- **Secretos:** ninguno real. Solo placeholders en `backend/.env.example` (`API_TOKEN=<redacted>`, `HF_TOKEN=<redacted>`, `CORS_ORIGINS=` vacío). Token del frontend solo en `localStorage` (diseño documentado).
- **«Chatterbox» / «XTTS» / «ElevenLabs»:** sin uso como marca propia ni como modelo; apariciones legítimas (atribución en `app/index.html:377`, documentación, exclusiones, IDs `eleven_realtime_v1_mini/_max` en `DELTAS_REA_APLICADAS.md` / `FEATURE_MAP.md` como referencia al original).
- **501 honesto:** verificado — ningún endpoint en 501 se presenta como implementado. Excepciones a ese principio, ya listadas: VoxCPM2 (B3), `voice-conversion` por defecto (B9), sliders placebo (B4), destinos de doblaje no soportados (A3).
- **Riesgos anotados, no confirmados como explotables sin ejecución:** `X-Forwarded-For` confiable para rate-limit (`backend/app/security.py`, `client_ip`); `read_upload` carga el fichero completo en memoria (doblaje hasta 500 MB); SQL con nombres de columna por f-string solo desde claves internas (`store.py`: `create_voice`, `update_rule`, `update_job`) — seguro por construcción, frágil ante refactors; sin cabeceras de seguridad (HSTS/CSP) en el backend.
- **README honesto en lo principal:** `backend/README.md` y `PENDIENTES_KAGGLE.md` declaran que nada de GPU está probado y que VoxCPM2 no está integrado; el streaming se documenta como «por frases, no por token» sin prometer 97 ms. Matices a corregir: M6.

## Lo que queda para el navegador vivo (`delivery_audit_gate`)

No verificable por revisión de código; requiere backend en línea y teléfono de Carlos:

1. Todas las funciones en el teléfono, con backend en línea Y apagado (modo degradado real, no simulado).
2. Responsive 360 / 768 / 1024 / 1440 px; navegación táctil; diálogos y menús con teclado y lector de pantalla.
3. `prefers-reduced-motion`; contraste; foco visible en cada pantalla.
4. QC de audio: -16 LUFS ±1, pico ≤ -1 dBTP, inteligibilidad por transcripción, escucha completa de cada salida.
5. Las 8 discrepancias abiertas del Apéndice D de `FEATURE_MAP.md` (D1–D8): vistas previas de Voice Design (3 vs 5), límite de subida de Dubbing (1/2/3 GB), loop de SFX v3, exportación real de doblaje v2, 40.000 caracteres de Flash v2.5, cifra de voces 17.500+, «hasta 32 hablantes» de Scribe, «55 % de sus ingresos» de agentes.
6. Las 10 incógnitas de tráfico web de `REA.md` (N1–N10): endpoints reales de la web de ElevenLabs, parámetros TTS, Voice Library, IVC/PVC, Studio, Dubbing v2, Flows, descarga de historial, telemetría y auth.
7. Re-verificar tras las correcciones: B1, B2, B4, B7, B8, B9 (flujos completos, no solo respuestas HTTP).

## Lo que queda para el run de Kaggle (`backend/PENDIENTES_KAGGLE.md`)

1. Resolver B5 (dependencias) y B6 (CORS) y A14 (`av`) **antes** de lanzar el notebook; si no, el run muere en el install.
2. Arranque del notebook y túnel trycloudflare; comprobar `GET /health` y `GET /api/v1/models` desde GitHub Pages.
3. Kokoro en español (`ef_dora`) + verificación de idioma real (A5).
4. Clonación Qwen3-TTS + verificación WER ≤ 0,15.
5. Voice Design (3 candidatos; comprobar A10: ¿idénticos?).
6. STT `large-v3` y diarización (con `HF_TOKEN`).
7. Demucs (separación real) y SFX con términos aceptados + `HF_TOKEN`.
8. Doblaje ES→EN de extremo a extremo (tras corregir B1, B2, A1–A4).
9. Medición de VRAM con Qwen 1.7B + Whisper en el mismo proceso (A6).
10. Medir latencia real de streaming (sin prometer 97 ms).

## Resumen para el corrector (orden de trabajo sugerido)

1. **Bloqueantes primero:** B5 + B6 (sin ellos nada arranca en Kaggle/Pages) → B1 + B2 + A1–A4 (doblaje completo) → B3 (quitar VoxCPM2 del selector) → B4 (sliders: quitar `similarity`, deshabilitar o implementar los demás por voz) → B7 (aceptar `.webm` o transcodificar la grabación) → B8 (URLs absolutas con base + token) → B9 (método por defecto `stt-tts`).
2. **Altas después:** A17 (token obligatorio en el notebook), A13, A12, A15, A5, A7, A8.
3. **Luego:** medias y bajas; actualizar `app/VERIFICACION.md` y `backend/README.md` (M6) y ejecutar los 30 tests con `fastapi` instalado (A9).
4. **Finalmente:** navegador vivo y run de Kaggle según las listas anteriores. Nada se declara terminado por revisión de código.
