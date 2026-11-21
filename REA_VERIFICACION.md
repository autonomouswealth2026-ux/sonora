# REA_VERIFICACION — Deltas contra FEATURE_MAP.md

**Fecha:** 20 de noviembre de 2026
**Método:** verificación función por función de `FEATURE_MAP.md` contra la app
real de ElevenLabs, con las fuentes del informe `REA.md` (§10).
**Regla:** este archivo **no sobrescribe** `FEATURE_MAP.md`; solo registra
qué se confirmó, qué cambió y qué falta.
**Estados:** ✅ confirmado sin cambios · ⚠️ confirmado con corrección ·
➕ añadido (faltaba en el mapa) · ❓ no verificado.

---

## 1. Resumen de deltas

| Resultado | Funciones |
|---|---|
| ✅ Confirmadas sin cambios | 15 (§1, §2, §3, §7, §8, §13, §15, §16, §17, §19, §20, §22, §23, §24, §25) |
| ⚠️ Confirmadas con corrección | 9 (§4, §5, §6, §9, §10, §11, §12, §14, §18) + §21 con corrección de contenido |
| ➕ Faltan en el mapa | 12 áreas/funciones nuevas (§6 de este archivo) |
| **Total revisado** | **25 funciones del mapa + 12 añadidas = 37** |

**Conteo de grados tras la verificación:** 10 totales · 10 parciales · 5 no
replicables (sin cambio en el conteo). Cambia el contenido dentro de varias
parciales (§9, §12, §14, §18, §21) y una corrección de grado parcial dentro de
§21 (el audio de ElevenReader no es exportable; el "equivalente MP3" del mapa
no existe como tal).

---

## 2. Verificación función por función

### §1 Text to Speech — ✅ confirmado (con 2 precisiones)

- Confirmado: v4 (90+ idiomas, 10.000 caracteres por petición, etiquetas de
  audio), v4 Turbo (~100 ms latencia mediana de inferencia, ~150 ms hasta el
  primer audio), v3 (70+ idiomas, 5.000 caracteres), Multilingual v2
  (29 idiomas, el más estable para formato largo), Flash v2.5 (~75 ms,
  32 idiomas).
- **Precisión 1:** en v4 solo quedan los sliders **Stability y Similarity**;
  los sliders Style y Speed de modelos anteriores **no existen en v4**
  (fuente: reseña de v4 con lectura de la documentación, 13 oct 2026).
  El endpoint del clon (`POST /api/v1/tts`) puede mantener `style_exaggeration`
  como parámetro propio, pero no es un control de v4.
- **Precisión 2:** **SSML `<break>` está desactivado en v4**; se usan las
  etiquetas `[pause]` / `[long pause]`. El clon no debe prometer SSML.
- ❓ **No verificado:** los 40.000 caracteres por petición de Flash v2.5
  (solo consta en `FEATURE_MAP.md`; ninguna fuente consultada lo confirma ni
  lo niega).
- Grado: 🟢 Total (sin cambio).

### §2 Text to Dialogue — ✅ confirmado

- Confirmado: multi-hablante con `voice_id` por línea, hasta 10 voces,
  timestamps por palabra y hablante.
- **Precisión:** v4 se usa por la API de Text to Dialogue; **v4 Turbo va por
  el WebSocket de Text to Dialogue** (no por el endpoint REST). El clon con
  orquestación por segmentos sigue siendo la vía correcta.
- Grado: 🟡 Parcial (sin cambio).

### §3 Instant Voice Cloning — ✅ confirmado

- Confirmado: clon zero-shot rápido, disponible como `voice_id` para TTS.
- **Precisión:** la página de v4 dice que bastan **10 s** de audio; la
  documentación de clonación recomienda **1–2 min** de audio limpio, y la
  página de clonación dice "1–5 minutos funcionan bien". El mapa decía
  "1–2 minutos según el plan Starter": correcto como recomendación, pero el
  mínimo real en v4 es 10 s. El endpoint del clon (mín. 3 s) sigue siendo
  coherente con Qwen3-TTS.
- Plan: IVC desde Starter ($6); el plan Free no lo incluye.
- Grado: 🟢 Total (sin cambio).

### §4 Professional Voice Cloning — ⚠️ confirmado con correcciones

- Confirmado: fine-tuning con 30 min–3 h, verificación de identidad, mayor
  fidelidad, 3–6 h de entrenamiento (la documentación también da 6–24 h).
- **Corrección 1 (fecha):** desde el **2 de noviembre de 2026** el fine-tuning
  de un PVC sobre **Eleven v4 y v4 Turbo está abierto a todos los workspaces**
  (antes era limitado). Se activa desde el botón `+` junto a Eleven v4 en
  My Voices. Nuevo parámetro: `clone_strength`, guardado en los ajustes de la
  voz (se usa cuando la petición no fija `clone_strength` ni
  `use_pvc_as_ivc`).
- **Corrección 2 (slots):** el mapa decía "1 voz en Creator, 3 en Scale, 10 en
  Business". Correcto, pero incompleto: **Pro también tiene 1 slot** (1 en
  Creator **y** Pro, 3 en Scale, 10 en Business).
- **Corrección 3 (verificación):** la verificación es un **captcha de voz**:
  la API devuelve una imagen con líneas de texto, el propietario las lee en
  voz alta y la grabación va a un endpoint de verificación
  (`POST /v1/voices/pvc/{voice_id}/verification`); la verificación manual es
  solo el fallback. El mapa solo decía "verificación de identidad".
- Grado: 🟡 Parcial (sin cambio). La vía local (multi-referencia + LoRA
  manual) sigue siendo la correcta.

### §5 Voice Library — ⚠️ confirmado con corrección de cifra

- Confirmado: catálogo buscable por idioma/acento/edad/estilo, voces de la
  comunidad con reparto de ingresos.
- **Corrección:** el mapa da dos cifras ("más de 10.000 voces" y "17.500+
  voces en 90+ idiomas"). **La cifra 17.500+ no se pudo verificar** en ninguna
  fuente consultada; todas las fuentes independientes dicen **10.000+ voces**.
  Usar 10.000+ hasta que el navegador vivo lea la cifra de la web.
- **Añadido:** existe el **Voice Marketplace** (may 2026): los creadores
  suben PVC, fijan términos de licencia (casos de uso, niveles de precio,
  preaviso de hasta 2 años) y cobran royalties por generación. Y endpoints de
  descubrimiento: `GET /v2/voices`, `GET /v1/shared-voices`,
  `POST /v1/similar-voices`.
- Grado: 🔴 No replicable (sin cambio).

### §6 Voice Design — ⚠️ confirmado, con una discrepancia abierta

- Confirmado: describir una voz en texto (20–1.000 caracteres) y generar
  vistas previas para elegir una, sin muestras de audio. Modelo en API:
  `eleven_ttv_v3` (antes `eleven_multilingual_ttv_v2`).
- ❓ **Discrepancia no resuelta:** el mapa dice **3 vistas previas**; una guía
  de la API de mayo 2026 dice **5 variantes**. No se pudo determinar el número
  actual sin la app web. Queda para el navegador vivo (§8.5 de `REA.md`).
- Grado: 🟢 Total (sin cambio).

### §7 Voice Remix — ✅ confirmado

- Confirmado: cambiar acento/edad/tono/ritmo de una voz creada manteniendo la
  identidad base, con previsualización. Endpoint:
  `POST /v1/text-to-voice/{voice_id}/remix`.
- Grado: 🟡 Parcial (sin cambio).

### §8 Speech to Speech / Voice Changer — ✅ confirmado

- Confirmado: convierte voz grabada o subida a otra voz manteniendo emoción,
  cadencia, acento, susurros y risas. Endpoints:
  `POST /v1/speech-to-speech/{voice_id}` y `/stream`. Coste en app:
  1.000 créditos/min.
- Grado: 🟡 Parcial (sin cambio).

### §9 Dubbing — ⚠️ confirmado con correcciones importantes

- Confirmado: traduce y re-dobla manteniendo voz e interpretación;
  multi-hablante; 90+ idiomas con dialectos regionales (inglés US/UK/AU/CA,
  español ES/MX/AR/CL, francés FR/CA, portugués BR/PT, árabe EG, chino TW);
  acepta enlaces de YouTube/TikTok; sin sincronización labial.
- **Corrección 1 (dos rutas, no una):** el mapa describe un solo pipeline con
  "edición de transcripción/traducción y regeneración por segmentos". La
  realidad es **dos productos excluyentes**: (a) **Dubbing v2 automático**
  (por defecto, etiquetado **alfa** en la documentación; edición de
  transcripción/traducción y regeneración en la app; por API solo Enterprise)
  y (b) **Dubbing Studio v1** (legacy, **solo mantenimiento**, corrección de
  errores críticos; edición por clip, reasignación de hablantes, exportación
  AAF/SRT/CSV). Un doblaje automático **no se puede convertir** en proyecto
  de Dubbing Studio. El endpoint del clon debe modelar la ruta v2 (la vigente)
  y no prometer la edición fina de v1.
- **Corrección 2 (límites en disputa):** el mapa dice "hasta 2 GB y 180 min".
  Las fuentes discrepan: **1 GB y 180 min** (resumen de la documentación),
  **2 GB y 180 min** (artículo de ayuda), **3 GB por archivo por API**
  (documentación de la API). Dubbing Studio v1: 1 GB y 45 min. Registrar las
  tres cifras; el navegador vivo debe leer el límite que muestra la app.
- **Corrección 3 (coste):** los 2.000–10.000 créditos/min del mapa son las
  tarifas **v1** (automático con/sin marca de agua 2.000/3.000; Studio
  5.000/10.000). **Dubbing v2 se cobra por API a $2,20/min de origen** (no en
  créditos). En la app, una prueba práctica midió ~13.500 créditos por minuto
  de vídeo y por idioma (fuente: comparativa Vosko, 2026).
- **Corrección 4 (exportación v2):** el mapa promete "vídeo doblado (o audio)".
  Una prueba práctica de v2 solo pudo descargar **MP4** (sin pista de audio
  separada ni subtítulos); el changelog del 19 oct 2026 añade **subtítulos
  traducidos como WebVTT** a las salidas de doblaje. La exportación de audio
  separado en v2 queda **no verificada**.
- **Añadido:** Dubbing v2 trabaja **desde el audio original, no desde una
  transcripción**, y así transfiere tono y emoción entre idiomas.
- Grado: 🟡 Parcial (sin cambio), pero el alcance real de "editar por
  segmentos" es menor de lo que el mapa sugiere (v2 en app sí, por API solo
  Enterprise; v1 legacy).

### §10 Speech to Text (Scribe) — ⚠️ confirmado, modelo actualizado

- **Actualización mayor:** el mapa describe Scribe v2 y anuncia Scribe v3
  (10 nov 2026). **Confirmado: Scribe v3 (`scribe_v3`) y Scribe v3 Live
  (`scribe_v3_live`) se lanzaron el 9–10 nov 2026** y son los modelos vigentes;
  v2 y v2 Realtime siguen disponibles. Mejoras (fabricante, FLEURS):
  27 % menos WER que v2 en 102 idiomas; diarización −12 % en general y −17 %
  con 3+ hablantes; v3 Live: 43 % menos WER semántico y 31 % menos WER que
  v2 Realtime, diarización en vivo por primera vez.
- **Parámetros nuevos:** `numbers_format` (dígitos o palabras),
  `secondary_language_codes` (audio que mezcla idiomas), keyterms hasta 1.000
  en lote y **biblioteca de keyterms de hasta 10.000 términos** en Live,
  `commit_strategy=turn_prediction`, `multilang_mode` (cada idioma en su
  propio alfabeto), redacción de entidades en tiempo real
  (`entity_redaction`), timestamps con filtrado de fondo.
- **Añadido:** **Scribe v2 Medical** (clínico, por lotes) y **Scribe v3 Live
  Medical** (tiempo real, para agentes de salud) existen como modelos aparte.
  El mapa solo mencionaba Scribe v2 Medical de pasada.
- **Precio (17 nov 2026):** STT por API a **$0,20/hora por lotes y $0,22/hora
  en tiempo real** en planes self-serve y Business (antes $0,22/$0,39).
  En la app sigue siendo 330 créditos/min.
- ❓ **No verificado:** "hasta 32 hablantes etiquetados" (solo consta en el
  mapa; ninguna fuente consultada da esa cifra para Scribe v3).
- Grado: 🟢 Total en lotes (sin cambio); en vivo sigue siendo parcial.

### §11 Sound Effects — ⚠️ confirmado con correcciones

- Confirmado: texto → efecto/ambiente/pista corta, con control de influencia
  del prompt.
- **Corrección 1 (modelo y fecha):** **SFX v3 (`eleven_text_to_sound_v3`) se
  lanzó el 29 oct 2026** y es el modelo por defecto en ElevenCreative, Studio
  y Flows desde el **2 nov 2026**. Mejora: varios sonidos en un mismo prompt,
  mejor música y voces, menos clipping en agudos.
- **Corrección 2 (límites exactos):** duración **0,5–30 s** (auto si no se
  fija); prompt de hasta **450 caracteres en la app**; `prompt_influence`
  0–1 (por defecto 0,3); hasta 4 variantes por generación (según una reseña).
  El mapa decía "hasta ~30 s" (correcto) pero no daba el resto.
- **Corrección 3 (loop en disputa):** el changelog del 2 nov lista
  `"loop": true` entre las opciones de v3 y la página de modelos lo anuncia
  como función de v3, pero el blog de desarrollo dice que el loop sigue
  necesitando v2. **Discrepancia abierta**; queda para el navegador vivo.
- **Corrección 4 (retirada):** **SFX v2 está deprecated y se retira el
  1 mar 2027.** El clon no debe tomar v2 como referencia.
- **Coste:** 200 créditos por generación en app (40 créditos/s si se fija la
  duración); API $0,12/min. Concurrencia propia desde el 9 nov: 4 en
  Free/Starter, 6 en Creator/Pro, 8 en Scale/Business (antes compartía el
  límite de TTS).
- Grado: 🟡 Parcial (sin cambio).

### §12 Music — ⚠️ confirmado, con mucho contenido añadido

- Confirmado: canciones e instrumentales desde prompt, con o sin voces,
  género/estado de ánimo/estructura, regeneración de secciones, uso comercial
  desde Starter.
- **Corrección 1 (versión y fechas):** el modelo vigente es **Eleven Music
  v2.5 (`music_v2_5`), lanzado el 11 sep 2026** (mejor calidad y adherencia al
  prompt que v2; preferido en la mayoría de 47.885 pares en prueba ciega del
  fabricante). **Music v1 está deprecated y se retira el 31 ene 2027.**
- **Corrección 2 (duración):** pistas de **3 s a 5 min** por generación
  (el mapa no daba duración; el plan de composición admite hasta 10 min en
  total). Formatos: MP3 44,1 kHz (128–192 kbps) o WAV.
- **Añadido (sub-funciones que el mapa no recoge):**
  - **Planes de composición:** `POST /v1/music/plan` expande un prompt a un
    plan JSON editable (hasta 30 secciones de 3–120 s, con letra, estilos
    positivos/negativos y adherencia al contexto).
  - **Inpainting:** regenerar una sola sección sin tocar el resto
    (`store_for_inpainting=true`).
  - **Separación de stems:** `POST /v1/music/stem-separation` (2 o 6 stems,
    devuelve ZIP; alta latencia en archivos largos).
  - **Audio Reference:** ~30 s de audio como referencia de sonido.
  - **Music Finetunes:** entrenar una variante privada de estilo con audio
    propio, $1,50 cada uno (`/v1/music/finetunes`).
  - **Video to Music / Instant Soundtracks:** `POST /v1/music/video-to-music`
    (19 oct 2026): hasta 10 vídeos, 200 MB combinados, 600 s en total;
    descripción opcional (<1.000 caracteres) y hasta 10 etiquetas de estilo;
    `use_audio_as_reference`, `add_sfx`, `separate_tracks` (ZIP con música y
    SFX separados). En la app se llama **Instant Soundtracks** (15 oct 2026).
    Una fuente indica que, a 26 oct 2026, era **solo API** (sin botón en la
    app web): no verificado del todo.
  - **SoundCloud:** desde el 6 nov 2026 se puede publicar directamente en
    SoundCloud desde ElevenMusic.
  - **C2PA:** `sign_with_c2pa` firma los MP3 con credenciales de contenido.
  - **Zero Retention Mode:** `enable_logging=false` en música/SFX, solo
    Enterprise.
- **Coste:** API $0,15/min; app 900 créditos/min.
- Grado: 🟡 Parcial (sin cambio), pero el listón real incluye planes de
  composición, inpainting, stems y Video to Music: el clon cubre la generación
  básica, no el pipeline de edición.

### §13 Voice Isolator — ✅ confirmado

- Confirmado: elimina ruido de fondo, calle y música; acepta WAV/MP3/FLAC/OGG/
  AAC y vídeo. Endpoints: `POST /v1/audio-isolation`, `/stream`,
  `GET/DELETE /v1/audio-isolation/history`. Coste: 1.000 créditos/min.
- Grado: 🟢 Total (sin cambio).

### §14 Studio / Projects — ⚠️ confirmado con correcciones

- Confirmado: proyectos de formato largo, capítulos, voces por párrafo,
  regeneración de fragmentos, diccionario de pronunciación, límites 3
  proyectos en Free y 20 en Starter.
- **Corrección 1:** Studio es hoy un **editor de línea de tiempo multimedia**
  (voz, música, efectos, subtítulos **y vídeo**), con importación de
  documentos y exportación MP3/WAV (Pro+: WAV 16-bit 44,1 kHz; Creator+:
  sin marca de agua de vídeo). El mapa lo describía solo como editor de
  audiolibros/podcasts. El clon de "capítulos + regeneración" sigue siendo
  parcial, pero el listón real es más alto.
- **Corrección 2:** desde la actualización del **2 nov 2026, Studio recomienda
  Eleven v4** en los ajustes de proyecto (antes Multilingual v2).
- **Añadido:** existe el endpoint **`POST /v1/studio/podcasts`** (crear
  podcast) además de `/v1/studio/projects`.
- Grado: 🟡 Parcial (sin cambio).

### §15 Diccionario de pronunciación — ✅ confirmado

- Confirmado: reglas palabra → pronunciación, formato PLS, aplicable a TTS,
  Studio y ElevenReader. Endpoints CRUD: `/v1/pronunciation-dictionaries/*`.
  v4 admite pronunciaciones en IPA.
- Grado: 🟢 Total (sin cambio).

### §16 History — ✅ confirmado

- Confirmado: lista de generaciones con texto, voz, modelo y fecha; escuchar,
  descargar y borrar. Endpoints: `GET /v1/history`,
  `POST /v1/history/download` (descarga por lotes).
- Grado: 🟢 Total (sin cambio).

### §17 API — ✅ confirmado

- Confirmado: REST + WebSocket, SDKs oficiales de Python y TypeScript, CLI y
  MCP; auth por `xi-api-key`; expone TTS, diálogo, STS, clonación, doblaje,
  SFX, aislamiento, Scribe, música, agentes y colecciones de voces.
- **Precisión:** el spec público tiene **258 endpoints en 25 grupos** (espejo
  del OpenAPI); un catálogo validado contra la API real lista 126 endpoints
  (la diferencia es versión del spec y agrupación, no funciones ausentes).
  MCP hospedado disponible en Claude desde ago 2026. SDKs en v2.79.0
  (nov 2026).
- Grado: 🟢 Total como API propia (sin cambio).

### §18 Agentes conversacionales — ⚠️ confirmado, alcance mucho mayor

- Confirmado: constructor de agentes con ASR + LLM a elegir + TTS de baja
  latencia, herramientas (webhooks, MCP), telefonía y web, workflows,
  guardrails, analítica y pruebas simuladas. Agentes nuevos usan v4 Turbo por
  defecto desde el 5 oct 2026.
- **Añadido (todo confirmado en changelog nov 2026, faltaba en el mapa):**
  - **Eleven Realtime** como modo de voz del agente (v1 Mini/Max) — ver §19.
  - **Campaign Manager** (9 nov 2026): campañas salientes por teléfono,
    voz de WhatsApp y mensajes de WhatsApp; contactos por CSV o API;
    seguimiento, rellamadas, ventanas de llamada, límites de intentos,
    listas de no llamar, analítica y exportación CSV.
  - **Reception** (6 oct 2026): recepcionista de IA para pequeñas empresas
    (atiende llamadas, reserva trabajos).
  - **Architect** (6 oct 2026; fin de la alfa gratuita el 31 oct 2026):
    asistente que revisa la configuración del agente y propone mejoras
    probadas en conversaciones simuladas.
  - **Unity SDK** (5 nov 2026, `io.elevenlabs.agents` v0.1.0): agentes en
    juegos, audio espacial, acciones del juego; escritorio y WebGL, iOS/
    Android/XR en beta.
  - **Workflows as code** (9 nov 2026, SDK v2.77.0): constructor `Workflow`
    en Python/JS, versionable, editable también en el editor visual.
  - **Herramientas en código** (17 nov 2026, SDK v2.79.0) y **39 herramientas
    MCP hospedadas** para construir agentes.
  - **Analysis Items API** (`/v1/convai/analysis-items`, nov 2026):
    criterios de evaluación y recogida de datos reutilizables y versionados.
  - **Guardrails** fuera de alfa (19 oct 2026, GA).
  - **Colas de espera** por concurrencia (audio en espera, eventos
    `queue_status`), **DTMF** (teclado telefónico), **timeouts del lado del
    servidor desde el 26 nov 2026** (HTTP 504).
  - **LLM:** agentes nuevos usan por defecto `gemini-3.5-flash`; añadidos
    `gpt-6.1-terra` y **Nemotron 3.5 Super VL** (NVIDIA, 11 nov 2026);
    Claude Sonnet 4.5 deprecated el 30 nov (reemplazo: Sonnet 4.6).
  - **Preview (11 nov 2026, no lanzado):** **Interaction Engine** (turn-taking,
    interrupciones, selección de modelo), **Memory** (contexto entre
    conversaciones) y **Routines** (trabajo multi-paso antes/durante/después
    de la conversación). También se previsualiza fine-tuning de modelos para
    empresas.
- ❓ **No verificado:** "55 % de sus ingresos" (solo consta en
  `FEATURE_MAP.md` citando una reseña; ninguna fuente consultada lo confirma).
- Grado: 🟡 Parcial (sin cambio). El clon cubre un agente web básico; la
  distancia real con ElevenAgents es mayor de lo que el mapa describía.

### §19 Eleven Realtime — ✅ confirmado

- Confirmado: dos modelos voz a voz en un solo modelo (v1 Mini, bajo coste;
  v1 Max, soporte y herramientas), 90+ idiomas, API Realtime compatible con
  la especificación de OpenAI (solo WebSocket).
- **Precisión:** IDs `eleven_realtime_v1_mini` (por defecto) y
  `eleven_realtime_v1_max`; lanzamiento 20 oct 2026; despliegue gradual
  completado el 2 nov 2026 (todos los workspaces); sesiones de audio
  inactivas se cierran a los 3 min (antes 60 s); grupos de conversación
  (`/v1/convai/realtime/conversation-groups`); secreto de cliente
  (`POST /v1/convai/realtime/client-secret`).
- Grado: 🔴 No replicable (sin cambio).

### §20 Realtime Translation — ✅ confirmado

- Confirmado: traducción de voz en directo en 90+ idiomas con voz
  consistente; alfa del 21 oct 2026; **solo Enterprise** vía ElevenAPI.
- Grado: 🔴 No replicable (sin cambio).

### §21 ElevenReader — ⚠️ confirmado con corrección de contenido

- Confirmado: app iOS/Android/web que convierte libros, PDF, ePub, documentos
  y enlaces en audio; 1.000+ voces; resaltado; velocidad 0,25×–4×;
  temporizador de sueño; marcadores; diccionario de pronunciación.
- **Corrección 1 (idiomas):** la documentación (3 oct 2026) lista **32
  idiomas**; las páginas de marketing dicen 90+. El mapa decía "30+
  idiomas": compatible con la documentación, no con el marketing.
- **Corrección 2 (planes propios):** ElevenReader tiene **sus propios planes**,
  separados de la suscripción de ElevenLabs: Free 10 h/mes de texto a audio;
  **Ultra $11/mes ($8,25 anual)** con texto a audio ilimitado, 20 h/mes de
  audiolibros premium, descargas offline y voces personalizadas.
- **Corrección 3 (catálogo):** **200.000+ audiolibros y eBooks premium**
  (may 2026), incluidos títulos narrados por humanos; 20 h/mes en Ultra.
  El mapa no mencionaba el catálogo.
- **Corrección 4 (grado parcial — importante):** la documentación de
  ElevenReader establece que **el audio no se puede exportar ni usar
  comercialmente**. El mapa proponía como "equivalente práctico" descargar el
  audio como MP3: eso **no** es equivalente a la función real (que es
  escuchar dentro de la app, con sincronización y offline interno). El clon
  puede replicar "subir un documento y escucharlo", pero no debe presentar la
  descarga de MP3 como la misma función: es una función distinta (exportación,
  que pertenece a Studio). Grado sigue 🟡 Parcial, con este matiz registrado.
- **Añadido:** sincronización web/móvil, extensión de Chrome, importación
  inteligente (Ultra, ignora encabezados/pies), GenFM, escaneo de páginas con
  cámara, límites offline (20 h/día, 150 h/mes).
- Grado: 🟡 Parcial (con la corrección 4 registrada).

### §22 ElevenAI — ✅ confirmado

- Confirmado: app Mac, acceso anticipado gratuito desde el 11 nov 2026
  (tres meses gratis, precio posterior sin anunciar), dictado en 90+ idiomas
  con Scribe v3, notas de reunión **sin bot en la llamada** (con
  consentimiento de los participantes), resúmenes y acciones.
- **Precisión:** incluye asistencia en vivo durante llamadas.
- Grado: 🔴 No replicable como producto (sin cambio).

### §23 Efectos de audio en TTS — ✅ confirmado

- Confirmado: objeto `audio_effects` en TTS y Text to Dialogue desde el
  12 oct 2026 (preset de filtro, distancia, reverberación, cama de ruido en
  bucle, paneo estéreo), sin coste adicional; catálogo en
  `GET /v1/audio-effects/catalog`.
- Grado: 🟢 Total (sin cambio).

### §24 Alineación forzada — ✅ confirmado

- Confirmado: dada una transcripción y su audio, devuelve inicio/fin de cada
  palabra. Endpoint: `POST /v1/forced-alignment`.
- Grado: 🟢 Total (sin cambio).

### §25 Workspaces / facturación — ✅ confirmado

- Confirmado: planes Free $0/10.000, Starter $6/30.000, Creator $22/121.000,
  Pro $99/600.000, Scale $299/1,8 M, Business $990/6 M (nov 2026);
  1 crédito por carácter de TTS estándar; STT 330/min; música 900/min;
  SFX 200 por generación; Voice Changer/Isolator 1.000/min; doblaje
  2.000–10.000/min (v1).
- **Añadido:** créditos no usados de planes de pago **se acumulan hasta 2×
  la cuota mensual** (saldo máximo 3×); límite de uso mensual por miembro o
  cuenta de servicio (`PUT /v1/workspace/members/{user_id}/usage-limit`,
  9 nov 2026); Free no comercial y con atribución obligatoria.
- Grado: 🔴 No replicable / fuera de alcance (sin cambio; decisión de alcance).

---

## 3. Correcciones de datos del mapa (lista corta)

| Dato en FEATURE_MAP.md | Corrección verificada |
|---|---|
| §4 PVC: "1 voz en Creator, 3 en Scale, 10 en Business" | 1 en Creator **y Pro**, 3 en Scale, 10 en Business |
| §4 PVC: fine-tuning v4 "desde el 2 de noviembre de 2026 también se puede afinar" | Confirmado y ampliado: abierto a **todos** los workspaces; parámetro `clone_strength` |
| §5 Voice Library: "17.500+ voces" | **No verificado**; usar 10.000+ |
| §6 Voice Design: "tres vistas previas" | En disputa: 3 vs 5 (guía API may 2026) — no verificado |
| §9 Dubbing: "archivos de hasta 2 GB y 180 minutos" | En disputa: 1 GB (docs) / 2 GB (ayuda) / 3 GB (API) |
| §9 Dubbing: costes 2.000–10.000 créditos/min | Son tarifas **v1**; v2 cuesta $2,20/min por API |
| §9 Dubbing: "edición de transcripción/traducción y regeneración por segmentos" | En v2 solo en la app; por API exige Enterprise; v1 legacy |
| §10 STT: "hasta 32 hablantes etiquetados" | **No verificado** |
| §10 STT: Scribe v3 "desde el 10 de noviembre de 2026" | Confirmado: 9–10 nov 2026 (changelog 9 nov, lanzamiento 10 nov) |
| §11 SFX: "modelo SFX v3 desde el 29 de octubre de 2026" | Confirmado; por defecto en la app desde el 2 nov; v2 se retira 1 mar 2027 |
| §12 Music: "Instant Soundtracks" como función de la app | Es **Video to Music** (API, 19 oct 2026); a 26 oct 2026 no tenía botón en la app web (no verificado del todo) |
| §12 Music: sin duración | Pistas de 3 s a 5 min; planes de composición hasta 10 min |
| §14 Studio: editor de audiolibros/podcasts | Es editor de línea de tiempo **con vídeo**; recomienda v4 desde el 2 nov |
| §18 Agentes: "55 % de sus ingresos" | **No verificado** |
| §21 ElevenReader: "modo offline" ≈ "audio se descarga como MP3" | **Corregido:** el audio de Reader **no es exportable**; la descarga de MP3 es otra función (Studio) |
| §1 TTS: Flash v2.5 "40.000 caracteres por petición" | **No verificado** |
| §25: sin rollover de créditos | Los créditos de pago se acumulan hasta 2× la cuota (saldo máx. 3×) |

---

## 4. Funciones que faltan en el mapa (añadidas por esta verificación)

| # | Función real | Grado para el clon | Nota |
|---|---|---|---|
| A1 | **ElevenCreative Flows** (canvas de nodos, Alpha) | 🔴 No replicable | Conecta 50+ modelos de imagen/vídeo de terceros + todos los modelos de audio; re-ejecución por nodo; exportación a Studio; multiusuario en tiempo real; Flows Agent con aprobación. El clon no tiene modelos de imagen/vídeo. |
| A2 | **Generación de imagen y vídeo** (Veo 3.1, Kling, Seedance, Runway, FLUX, Nano Banana, GPT Image) | 🔴 No replicable | Modelos cerrados de terceros, de pago, dentro de ElevenCreative (Starter+). Fuera del alcance del clon de audio. |
| A3 | **Audio Native** (player integrable en webs) | 🟡 Parcial | `POST /v1/audio-native` (+ contenido por URL, ajustes). Replicable como player HTML5 que narra el texto de una página con el TTS del clon. Desde Creator. |
| A4 | **Studio Podcasts** | 🟡 Parcial | `POST /v1/studio/podcasts`. Sub-función de §14; replicable con el mismo motor de proyectos. |
| A5 | **Music: planes de composición, inpainting, stems, finetunes** | 🟡 Parcial | Sub-funciones de §12 (ver §2-§12). El clon cubre la generación; no la edición por secciones ni los stems. |
| A6 | **Video to Music / Instant Soundtracks** | 🟡 Parcial | Función propia dentro de §12 (ver §2-§12). Emulación local: generar pista y alinearla a mano. |
| A7 | **Scribe v3 Medical / v3 Live Medical** | 🟢 Total (lotes) | Sub-función de §10. Whisper transcribe terminología médica razonablemente; sin modelo clínico dedicado (igual que el mapa ya decía de Scribe Medical). |
| A8 | **Campaign Manager** (ElevenAgents) | 🔴 No replicable | Campañas salientes (teléfono, WhatsApp voz/mensajes), CSV/API, rellamadas, analítica. Exige telefonía y escala empresarial. |
| A9 | **Reception** (ElevenAgents) | 🔴 No replicable | Recepcionista de IA para pymes. Sub-función de §18; sin telefonía en el clon. |
| A10 | **Architect** (ElevenAgents) | 🔴 No replicable | Asistente que propone mejoras al agente y las prueba en simulación. Sub-función de §18. |
| A11 | **Unity SDK** (ElevenAgents) | 🔴 No replicable | Agentes en juegos (audio espacial, acciones). Sub-función de §18. |
| A12 | **Interaction Engine / Memory / Routines** | 🔴 No replicable | **Preview** 11 nov 2026, no lanzados. Sub-funciones de §18; no hay nada que replicar aún. |
| A13 | **Marketplace** (apps de socios) | 🔴 No replicable | Abierto 11 nov 2026; compras en 2027. Modelo de negocio, no función de audio. |
| A14 | **Ads Engine** (revisión humana, 6 nov 2026) | 🔴 No replicable | Traducción/doblaje de anuncios con revisión por lingüistas. Empresarial. |
| A15 | **Content provenance** (detección de watermark, beta 17 nov 2026) | 🟢 Total (equivalente propio) | Endpoint beta que detecta el watermark de ElevenLabs en un audio. El clon ya prevé registro de procedencia (§16); no necesita detectar el watermark ajeno. Ruta exacta **no verificada**. |
| A16 | **Voces similares** (`POST /v1/similar-voices`) | 🟡 Parcial | Dado un audio, devuelve voces parecidas de la biblioteca. Replicable solo dentro de la biblioteca propia (decenas de voces). |

**Nuevo conteo con las añadidas:** 37 funciones/áreas (25 del mapa + 12 nuevas
contando A5–A7 como sub-funciones dentro de su sección: 10 nuevas de primer
nivel si se cuentan A1, A2, A3, A4, A8, A9, A10, A11, A12, A13, A14, A15, A16
como 13). Para no enredar el conteo del mapa, las añadidas se registran aquí
sin modificar los 10/10/5 originales.

---

## 5. API pública vs app web (qué existe en cada lado)

| Capacidad | API pública (`api.elevenlabs.io`) | App web (ElevenCreative) | Estado de verificación |
|---|---|---|---|
| TTS, diálogo, STS, clonación, Scribe, SFX, música, doblaje, aislamiento, alineación, diccionarios, historial, Studio | ✅ Todos documentados (258 endpoints) | ✅ Mismo pool de créditos y calidad (según la documentación) | API: confirmado por el espejo del spec. Web: **no verificado en tráfico** |
| Voice Library (búsqueda, filtros) | ✅ `/v2/voices`, `/v1/shared-voices`, `/v1/similar-voices` | ✅ (UI de biblioteca) | API: confirmado. Web: no verificado |
| Generación de imagen y vídeo | ❌ **No existe** (solo app web cerrada y Studio API Enterprise) | ✅ Veo, Kling, Runway, FLUX, etc. | Confirmado por la skill verificada en CI |
| Flows | ❌ Sin endpoints públicos documentados | ✅ Canvas Alpha | Web: no verificado en tráfico |
| Dubbing v2: editar transcripción / regenerar por API | ❌ Solo Enterprise | ✅ En la app | Confirmado por reseñas |
| ElevenAgents (telefonía, campañas, WhatsApp) | ✅ `/v1/convai/*` (grande) | ✅ Panel de agentes | API: confirmado. Web: no verificado |
| Content provenance (detectar watermark) | ✅ Beta (17 nov 2026) | ❓ | Ruta exacta **no verificada** |
| Endpoints internos de la app web (si existen) | — | ❓ | **No descubierto ninguno**: exige navegador vivo (§8 de `REA.md`) |

**Conclusión:** con la evidencia disponible, la API pública cubre todo lo que
el clon necesita replicar. No hay indicios de una API web privada relevante,
pero eso es una afirmación del fabricante ("la web es solo un frontend de la
API"), no una comprobación. La única vía para cerrarlo es la inspección en
navegador vivo.

---

## 6. Pendientes para el navegador vivo (resumen)

Ver la lista exacta y numerada en `REA.md` §8 (N1–N10, bundles JS, 8 flujos,
8 preguntas). Resumen:

1. Confirmar si la web llama solo a `api.elevenlabs.io` o hay host interno.
2. Capturar el cuerpo real de generación TTS desde la web (v4 + audio effects).
3. Resolver las discrepancias: vistas previas de Voice Design (3 vs 5), límite
   de subida de Dubbing (1/2/3 GB), loop de SFX v3, exportación real de
   doblaje v2, 40.000 caracteres de Flash v2.5, 17.500+ voces.
4. Recorrer IVC, PVC (captcha de voz), Dubbing v2, Scribe, Studio y un agente
   con la red grabando.
5. Inspeccionar el bundle JS buscando endpoints no documentados.

---

## 7. Fuentes

Las mismas de `REA.md` §10 (changelog oficial espejado, espejo del spec
OpenAPI, skills/repos verificados en CI, reseñas independientes de noviembre
de 2026). Fuentes clave por delta:

- PVC fine-tuning v4 (2 nov 2026) y SFX v3 para todos: changelog 2 nov 2026
  (espejo Fern) y `https://www.my2cents.ai/news/2026-11-05-elevenlabs/`.
- Scribe v3 (9–10 nov 2026): changelog 9 nov 2026 (espejo Fern),
  `https://www.wirestack.site/e/elevenlabs-scribe-v3-sound-effects-concurrency-realtime-audio-formats-november-2026`,
  `https://www.assemblyai.com/blog/assemblyai-universal-3-pro-vs-elevenlabs-scribe-v2-compared`.
- STT $0,20/$0,22 h y watermark beta (17 nov 2026):
  `https://releases.sh/elevenlabs/elevenlabs-changelog`.
- v4 (28 sep 2026): `https://growthgrader.org/blog/eleven-v4-elevenlabs-new-voice-model-review/`,
  `https://micdrop.dev/blog/eleven-v4-turbo-voice-agent`.
- Dubbing v2 vs Studio v1: `https://aiproductivity.ai/guides/elevenlabs-multilingual-dubbing-workflow/`,
  `https://www.stork.ai/blog/elevenlabs-dubbing-2026`,
  `https://www.vosko.ai/compare/vosko-ai-vs-elevenlabs-dubbing/`.
- SFX v3: `https://www.stork.ai/blog/elevenlabs-sound-effects-2026`,
  `https://thehype.news/how-to-use-elevenlabs-sfx-v3/`.
- Música v2.5: `https://agientry.com/en/applications/eleven-music`,
  `https://tessl.io/registry/skills/github/elevenlabs/skills/music`,
  `https://www.reviewramble.com/models/eleven-music-v2-5`.
- ElevenReader: `https://www.audiopageapp.com/blog/elevenreader-review`,
  `https://toolgpa.com/tools/elevenreader`.
- Agentes / Summit 11 nov 2026: `https://www.scriptbyai.com/elevenlabs-timeline/`,
  `https://dev.to/alfazreviews/elevenlabs-launched-13-products-this-week-only-3-matter-if-you-build-voice-agents-4nfe`.
- Precios y créditos: `https://www.cartesia.ai/learn/elevenlabs-pricing`,
  `https://techjacksolutions.com/ai-tools/elevenlabs/elevenlabs-pricing/`.
- Spec OpenAPI (258 endpoints): `https://elevenlabs.docs.specway.com/api`,
  `https://github.com/adriendidoudid/eleven-sk/blob/HEAD/README.md`,
  `https://www.wiremock.io/sandboxes/elevenlabs-elevenapi`.
