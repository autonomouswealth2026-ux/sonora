# REA — ElevenLabs (app web real) · Análisis de ingeniería inversa

**Fecha:** 20 de noviembre de 2026
**Analista:** REA (subagente)
**Objetivo:** verificar y profundizar la app web real de ElevenLabs para el clon local
(`~/workspace/elevenlabs-clon/`). Complementa a `FEATURE_MAP.md` (25 funciones) y
`RESEARCH.md` (modelos locales). **No sobrescribe ninguno de los dos.**
**Idioma:** español. **Presupuesto:** cero.

---

## 0. Resumen ejecutivo

- **Qué es ElevenLabs hoy (nov 2026):** ya no es solo TTS. Son tres productos:
  **ElevenCreative** (web creativa: TTS, clonación, doblaje, música, SFX, Studio,
  Flows, imagen y vídeo de terceros), **ElevenAgents** (agentes de voz
  conversacionales, telefonía, WhatsApp, campañas) y **ElevenAPI** (258 endpoints
  documentados en 25 grupos, según el espejo del spec OpenAPI).
- **Modelos vigentes:** Eleven v4 / v4 Turbo (28 sep 2026, 90+ idiomas, 10.000
  caracteres por petición), Scribe v3 / v3 Live (9–10 nov 2026), SFX v3
  (29 oct 2026), Eleven Music v2.5 (11 sep 2026), Eleven Realtime v1 Mini/Max
  (20 oct 2026).
- **Veredicto global del mapa previo:** las 25 funciones de `FEATURE_MAP.md`
  **existen en la app real** (ninguna es inventada). El trabajo de esta
  verificación fue de precisión: **9 correcciones de datos** (límites, planes,
  fechas, costes), **1 corrección de grado** (ElevenReader: el audio no es
  exportable, su "equivalente MP3" no existe), y **12 funciones/áreas que
  faltaban en el mapa** (Flows, imagen/vídeo, Audio Native, Podcasts de Studio,
  Campaign Manager, Reception, Architect, Marketplace, watermark de
  procedencia, Music Finetunes/stems/inpainting, Scribe Medical, Video to
  Music como función propia). Detalle función por función en
  `REA_VERIFICACION.md`.
- **Grados tras la verificación:** 10 totales · 10 parciales · 5 no replicables
  (sin cambio en el conteo), pero con el contenido de varias parciales
  ampliado y una corrección dentro de §21.

---

## 1. Método y límites declarados (léase antes de usar este informe)

### 1.1 Qué es REA aquí

La skill `local-rea` (`~/workspace/custom-skills/local-rea/SKILL.md`) describe
REA como análisis sin código fuente: binarios nativos (Ghidra/Hopper), bundles
JavaScript/Electron, .NET, Android, firmware y páginas web (incluido tráfico
de red). Este informe aplica la parte web de esa metodología.

### 1.2 Ghidra NO aplica — declaración explícita

**ElevenLabs es una aplicación web (JavaScript en el navegador + API REST/
WebSocket en servidor). No es un binario nativo, no hay ejecutable que
desensamblar, no hay firmware ni APK propio que analizar.** Por tanto:

- **Ghidra no se usó y no tiene nada que analizar aquí.** No se fingió su uso.
- El análisis profundo equivalente para una app web es: **(a)** lectura de la
  documentación y el changelog oficiales, **(b)** lectura del spec OpenAPI
  público, **(c)** inspección en navegador vivo de los bundles JS y del tráfico
  de red tras el login. De (a) y (b) se hizo todo lo posible sin navegador
  vivo (ver §1.3); **(c) queda pendiente** y es la única vía que puede
  confirmar la superficie real de la app web (ver §8, lista exacta).

### 1.3 Limitación: sin navegador vivo

**Este analista NO tiene navegador en vivo**: sin DevTools, sin pestaña de red,
sin clics, sin login, sin cuenta de ElevenLabs. Consecuencias directas:

- **No se inspeccionó ninguna llamada de red de la app web** (`elevenlabs.io/app/*`).
  Todo endpoint de la app web que aparece en este informe procede de la
  **API pública documentada** (`api.elevenlabs.io`), no del tráfico de la web.
  La web es, según la propia documentación, "solo un frontend de la API", pero
  eso no se pudo comprobar en tráfico real.
- **No se recorrió ningún flujo tras el login** (crear voz, Studio, Dubbing
  Studio, Flows, agentes). Las descripciones de la UI proceden de la
  documentación y de reseñas con capturas, no de observación directa.
- **No se pudo leer ningún bundle JS** de la app web (habría permitido
  descubrir endpoints no documentados). Ver §8.3.

### 1.4 Bloqueos de lectura encontrados (verificables)

| Intento | Resultado |
|---|---|
| `browser.open` a `https://elevenlabs.io/` | **Fallido**: error `query network grant` (política del origen). Mismo bloqueo que reportó el agente anterior con `/pricing`. |
| `browser.open` al changelog espejado `elevenlabs.docs.buildwithfern.com/docs/changelog/2026/11/9` | **Fallido**: mismo error `query network grant`. |
| `browser.open` a un archivo GitHub (skill con el spec de la API) | **Fallido**: mismo error. |
| `curl` desde la VM a `https://api.elevenlabs.io/openapi.json` | **Fallido**: HTTP `000`, 0 bytes (la VM no tiene salida directa a ese origen; timeout 30 s). Proceso cancelado. |
| `browser.search` (búsqueda web) | **Funciona.** Toda la evidencia de este informe procede de aquí. |

**Conclusión metodológica:** `browser.open` está bloqueado en esta sesión para
cualquier URL (no solo ElevenLabs). La verificación se hizo con **resultados de
búsqueda** (snippets con citas) de: el changelog oficial espejado en
`elevenlabs.docs.buildwithfern.com`, el índice de releases `releases.sh`,
reseñas independientes con fecha de verificación en noviembre de 2026
(Stork, Fruitpunch, Promptwise, Cartesia, TechJack, AssemblyAI), el espejo del
spec OpenAPI (`elevenlabs.docs.specway.com`, 258 endpoints), y repositorios de
GitHub que espejan la documentación (`handotdev/elevenlabs-docs`,
`adriendidoudid/eleven-sk`, `lap-platform/claude-marketplace`,
`mrgoonie/multix-cli`). **Ninguna afirmación de este informe se presenta como
observada en la app web si procede de una fuente secundaria**: cada sección
indica su fuente y su grado de verificación.

### 1.5 Reglas de evidencia usadas

- **Confirmado:** dos fuentes independientes coinciden, o una fuente oficial
  (changelog/docs espejados) lo afirma con fecha.
- **Confirmado (fabricante):** lo afirma ElevenLabs; sin verificación
  independiente (benchmarks propios, "27 % menos errores", "preferido en
  47.885 pares"). Se marca como tal, no como hecho medido.
- **Discrepancia:** dos fuentes secundarias u oficiales discrepan (p. ej.
  límites de subida de Dubbing: 1 GB vs 2 GB vs 3 GB). Se registran todas las
  cifras con su fuente en vez de elegir una.
- **No verificado:** no se encontró fuente suficiente. Se escribe literalmente
  **"no verificado"** con el motivo.

---

## 2. Arquitectura de la plataforma real (noviembre 2026)

```
ElevenLabs (elevenlabs.io)
├── ElevenCreative — app web creativa (la que clona este proyecto)
│   ├── Speech: TTS (v4/v4 Turbo/v3/Multilingual v2/Flash v2.5), Text to Dialogue
│   ├── Voices: Voice Library (10.000+), IVC, PVC (+ fine-tuning v4), Voice Design,
│   │   Voice Remix, colecciones, voces similares
│   ├── Audio: Speech to Speech, Voice Isolator, SFX v3, audio effects en TTS
│   ├── Music: Eleven Music v2.5, Video to Music / Instant Soundtracks,
│   │   composición, inpainting, stems, finetunes
│   ├── Dubbing: automático v2 (por defecto) + Dubbing Studio v1 (legacy)
│   ├── Studio: editor de línea de tiempo (voz, música, SFX, subtítulos, vídeo),
│   │   proyectos, podcasts
│   ├── Flows (Alpha): canvas de nodos con 50+ modelos de imagen/vídeo de terceros
│   ├── Imagen y vídeo: Veo 3.1, Kling, Seedance, Runway, FLUX, Nano Banana, GPT Image
│   ├── Audio Native (player integrable), Scribe (STT), History
│   └── ElevenReader (app aparte: web/iOS/Android/extensión Chrome)
├── ElevenAgents — agentes de voz (producto empresarial)
│   ├── Pipeline STT→LLM→TTS o Eleven Realtime v1 (un solo modelo)
│   ├── Telefonía, WhatsApp (voz y mensajes), web, Unity SDK
│   ├── Campaign Manager, Reception, Architect, Workflows (código y visual)
│   ├── Knowledge base, herramientas (webhooks, MCP), guardrails, analítica,
│   │   pruebas simuladas, colas de espera, DTMF
│   └── Interaction Engine / Memory / Routines — PREVIEW (11 nov 2026, no lanzados)
├── ElevenAPI — https://api.elevenlabs.io (REST + WebSocket)
│   ├── 258 endpoints en 25 grupos (espejo del spec OpenAPI, ver §7)
│   ├── Auth: cabecera xi-api-key (también por query en GET, según guías)
│   ├── SDKs oficiales Python y TypeScript (v2.79.0), CLI, MCP hospedado (en Claude)
│   └── OpenAPI público en https://api.elevenlabs.io/docs
└── Productos aparte
    ├── ElevenAI — app Mac de dictado y notas de reunión (early access, 11 nov 2026)
    ├── ElevenReader — app de lectura (planes propios: Free 10 h/mes, Ultra $11/mes)
    ├── Marketplace — apps de socios (11 nov 2026; compras en 2027)
    └── Ads Engine — traducción/doblaje de anuncios con revisión humana (6 nov 2026)
```

**Modelo de negocio (verificado):** un solo pool de créditos compartido por
todos los productos. Planes (nov 2026, facturación mensual): Free $0 / 10.000
créditos, Starter $6 / 30.000, Creator $22 / 121.000, Pro $99 / 600.000,
Scale $299 / 1,8 M (3 asientos), Business $990 / 6 M (10 asientos),
Enterprise a medida. Facturación anual = 10 meses por 12. Los créditos no
usados de planes de pago se acumulan hasta 2× la cuota mensual (saldo máximo
3×). Costes por producto (app): TTS ~1 crédito/carácter; STT 330/min; música
900/min; Voice Changer e Isolator 1.000/min; SFX 200 por generación (40/crédito
por segundo si se fija duración); doblaje automático v1 2.000/min con marca de
agua o 3.000 sin ella; Dubbing Studio 5.000/10.000 min. Dubbing v2 se cobra en
dólares por API ($2,20/min de origen). API: TTS $0,04/1.000 caracteres
(Flash/Turbo) y $0,08 (v4/v3/Multilingual v2); STT $0,20/hora por lotes y
$0,22/hora en tiempo real (rebaja del 17 nov 2026; antes $0,22/$0,39);
música $0,15/min; SFX $0,12/min.

**Discrepancia registrada (idiomas):** la página de precios lista **74 idiomas**
en los seis planes; los modelos v4 anuncian **90+ idiomas**; Dubbing v2
anuncia 90+ idiomas; ElevenReader anuncia 32 idiomas en su documentación
(3 oct 2026) y 90+ en páginas de marketing. No es un error de una fuente:
son coberturas distintas por producto. El clon debe usar la cifra del
producto que replica, no una sola cifra global.

---

## 3. Estructura de la app web (ElevenCreative)

Lo que se puede afirmar sin navegador vivo procede de la documentación y de
reseñas con capturas (nov 2026). **No verificado en navegación directa.**

- **Entrada:** la web es el frontend de la API; mismo pool de créditos y misma
  calidad que la API con los mismos ajustes (documentación oficial, citada en
  el espejo de GitHub `handotdev/elevenlabs-docs`).
- **Navegación principal:** Speech (TTS), Voices (My Voices, Voice Library,
  Voice Design), Sound Effects, Music, Dubbing, Studio, Flows, Agents
  (ElevenAgents), Scribe/STT, History. Sidebar con botón `+` junto a Voices
  para crear clones (documentado en la guía de PVC).
- **TTS en la web:** selector de voz, selector de modelo (v4 recomendado en
  Studio desde el 2 nov 2026; Multilingual v2 sigue listado como el más
  estable para formato largo), ajustes Stability y Similarity (v4: solo esos
  dos sliders; los sliders Style y Speed de modelos anteriores **no existen
  en v4**), etiquetas de audio en línea (`[whispers]`, `[laughs]`,
  `[long pause]`, SFX, direcciones en lenguaje natural), diccionario de
  pronunciación / IPA. **SSML `<break>` desactivado en v4** (usar `[pause]`).
- **Studio:** editor de línea de tiempo en el navegador que combina voz,
  música, efectos, subtítulos y **vídeo**; importación de documentos; exportación
  MP3 y WAV (Pro+: WAV 16-bit 44,1 kHz; Creator+: sin marca de agua de vídeo en
  Studio). Proyectos: 3 en Free, 20 en Starter. **Corrección al mapa previo:**
  Studio ya no es solo "capítulos de audiolibro": es un editor multimedia con
  vídeo. El clon de "proyectos de formato largo" sigue siendo parcial, pero el
  listón real es más alto que el descrito en `FEATURE_MAP.md` §14.
- **Dubbing:** dos rutas excluyentes (elegir antes de gastar: un doblaje
  automático **no se puede convertir** en proyecto de Dubbing Studio).
  Automático v2 (por defecto, etiquetado alfa en la documentación) y Dubbing
  Studio v1 (legacy, solo mantenimiento: corrección de errores críticos).
  El editor v2 permite editar transcripción y traducción y regenerar segmentos
  en la app; por API, editar/regenerar exige Enterprise. Exportaciones v2
  (según una prueba práctica): MP4; el changelog del 19 oct añade subtítulos
  traducidos como WebVTT. Dubbing Studio (v1) exporta MP4, AAC, MP3, WAV, ZIP
  de pistas, AAF y SRT/CSV.
- **Flows (Alpha):** canvas de nodos; cada nodo es un paso (imagen, imagen a
  vídeo, TTS, lip-sync, música, SFX); re-ejecución por nodo; exportación a
  Studio; ejecución en segundo plano; edición multiusuario en tiempo real;
  Flows Agent (asistente conversacional que construye/modifica el flujo, con
  modo de aprobación para operaciones caras). Conecta 50+ modelos de imagen y
  vídeo de terceros.
- **ElevenReader:** app separada (web, iOS, Android, extensión de Chrome).
  Importa PDF, ePub, DOCX, TXT, HTML, Google Docs, Kindle, artículos, hilos
  de X, texto pegado y páginas escaneadas. 1.000+ voces; velocidad 0,25×–4×;
  temporizador de sueño; marcadores; resaltado sincronizado; sincronización
  web/móvil. Free: 10 h/mes de texto a audio. Ultra: $11/mes ($8,25 anual),
  texto a audio ilimitado, 20 h/mes de audiolibros premium (catálogo 200.000+
  títulos, may 2026), descargas offline (20 h/día, 150 h/mes), voces
  personalizadas, importación inteligente. **La documentación de ElevenReader
  establece que el audio no se puede exportar ni usar comercialmente.**
- **ElevenAI:** app Mac (early access gratuito desde el 11 nov 2026, tres meses
  gratis, precio posterior sin anunciar). Dictado con Scribe v3 en 90+
  idiomas, notas de reunión **sin bot en la llamada** (con consentimiento de
  los participantes), resúmenes, acciones y asistencia en vivo durante llamadas.

---

## 4. Flujos de trabajo principales (reconstruidos desde la documentación)

Ningún flujo se recorrió en vivo; la reconstrucción es documental.

1. **Narrar un texto (TTS):** elegir voz (biblioteca / clonada / diseñada) →
   elegir modelo → escribir o pegar texto (hasta 10.000 caracteres en v4) →
   ajustar Stability/Similarity → generar → escuchar/descargar → queda en
   History. En v4, las etiquetas de audio se escriben dentro del guion.
2. **Clonar una voz instantánea:** plan Starter+ → subir 1–2 min de audio
   limpio (v4: basta con 10 s, pero la documentación recomienda 1–2 min) →
   confirmar derechos/consentimiento → voz disponible como `voice_id`.
3. **Clonar una voz profesional:** plan Creator+ → subir 30 min mínimo
   (1–3 h recomendado; muestras de ~30 min) → ajustes de audio (quitar ruido,
   separar hablantes) → **verificación por captcha de voz**: leer en voz alta
   líneas de una imagen y grabarlas; verificación manual solo como fallback →
   fine-tuning (normalmente 3–6 h; la documentación también da 6–24 h) →
   desde el 2 nov 2026 se puede afinar un PVC sobre v4/v4 Turbo (botón `+`
   junto a Eleven v4 en My Voices; parámetro `clone_strength` guardado en los
   ajustes de la voz).
4. **Diseñar una voz:** describirla en texto (20–1.000 caracteres) → generar
   vistas previas → elegir una y guardarla. **Número de vistas previas no
   verificado (3 según `FEATURE_MAP.md`, 5 según una guía de la API de may
   2026).**
5. **Doblar un vídeo:** subir archivo (límites en disputa, ver §5) o pegar
   enlace de YouTube/TikTok → elegir idiomas destino (cada idioma se cobra
   por separado) → v2 automático (revisión de transcripción/traducción en la
   app) o v1 Dubbing Studio (edición por clip, reasignación de hablantes,
   regeneración por segmento) → exportar.
6. **Crear un agente (ElevenAgents):** crear agente → elegir LLM (por defecto
   en agentes nuevos: `gemini-3.5-flash`; disponibles GPT-6.1 Terra, Claude
   Sonnet 4.6, Nemotron 3.5 Super VL, entre otros) y modelo de voz (v4 Turbo
   por defecto desde el 5 oct 2026, o Eleven Realtime v1 Mini/Max) → prompt,
   knowledge base, herramientas (webhooks/MCP) → probar en simulación →
   desplegar en web/teléfono/WhatsApp/Unity → analítica y conversaciones.
7. **Hacer música:** prompt o plan de composición (hasta 30 secciones) →
   generar (3 s–5 min) → inpainting de una sección / separación de stems /
   Video to Music (subir vídeo, banda sonora automática con SFX opcionales).
8. **Transcribir (Scribe):** subir audio/vídeo o URL → elegir modelo
   (`scribe_v3` por lotes, `scribe_v3_live` en tiempo real) → diarización,
   timestamps por palabra, keyterms (hasta 1.000 en lote; biblioteca de hasta
   10.000 términos en Live), formato de números, idiomas secundarios.

---

## 5. Funciones verificadas: tabla de estado

Estado: ✅ confirmado · ⚠️ confirmado con matiz/corrección · ❓ no verificado.
El detalle función por función (deltas exactos contra `FEATURE_MAP.md`) está
en `REA_VERIFICACION.md`.

| # | Función | Estado | Nota de una línea |
|---|---|---|---|
| 1 | Text to Speech | ✅ | v4/v4 Turbo 28 sep 2026; 10.000 car.; solo Stability+Similarity en v4; sin SSML |
| 2 | Text to Dialogue | ✅ | v4 por API, Turbo por WebSocket; hasta 10 voces |
| 3 | Instant Voice Cloning | ✅ | v4 desde 10 s; docs recomiendan 1–2 min; Starter+ |
| 4 | Professional Voice Cloning | ⚠️ | Fine-tuning v4 abierto a todos 2 nov 2026; slots: 1 Creator/Pro, 3 Scale, 10 Business |
| 5 | Voice Library | ⚠️ | 10.000+ voces (no 17.500+; cifra no verificada); Marketplace con licencias y royalties |
| 6 | Voice Design | ⚠️ | Modelo `eleven_ttv_v3`; n.º de vistas previas en disputa (3 vs 5) |
| 7 | Voice Remix | ✅ | Endpoint `/v1/text-to-voice/{voice_id}/remix` |
| 8 | Speech to Speech | ✅ | `/v1/speech-to-speech/{voice_id}` + stream |
| 9 | Dubbing | ⚠️ | v2 por defecto (alfa); v1 legacy; límites de subida en disputa (1/2/3 GB); v2 API $2,20/min |
| 10 | Speech to Text (Scribe) | ✅ | Scribe v3/v3 Live 9–10 nov 2026; 102 idiomas; $0,20/$0,22 h; Medical existe |
| 11 | Sound Effects | ⚠️ | SFX v3 29 oct 2026; máx. 30 s; loop con v3 en disputa; v2 se retira 1 mar 2027 |
| 12 | Music | ⚠️ | v2.5 11 sep 2026; 3 s–5 min; planes de composición, inpainting, stems, finetunes, Video to Music |
| 13 | Voice Isolator | ✅ | `/v1/audio-isolation` + stream + historial |
| 14 | Studio / Projects | ⚠️ | Ahora editor con vídeo y subtítulos; Podcasts en API; 3 proyectos Free / 20 Starter |
| 15 | Diccionario de pronunciación | ✅ | CRUD `/v1/pronunciation-dictionaries/*`; IPA en v4 |
| 16 | History | ✅ | `/v1/history`, `/v1/history/download` |
| 17 | API (ElevenAPI) | ✅ | 258 endpoints / 25 grupos; SDKs, CLI, MCP hospedado |
| 18 | Agentes conversacionales | ⚠️ | Mucho más grande que §18 del mapa: Campaign Manager, Reception, Architect, Unity SDK, Realtime |
| 19 | Eleven Realtime | ✅ | v1 Mini/Max; API compatible con OpenAI Realtime; en todos los workspaces desde 2 nov |
| 20 | Realtime Translation | ✅ | Alfa Enterprise (21 oct 2026) |
| 21 | ElevenReader | ⚠️ | **Corrección de grado parcial:** audio NO exportable; catálogo 200.000+ audiolibros; Ultra $11/mes |
| 22 | ElevenAI | ✅ | Early access Mac 11 nov 2026; Scribe v3; notas sin bot |
| 23 | Efectos de audio en TTS | ✅ | `GET /v1/audio-effects/catalog`; changelog 12 oct 2026 |
| 24 | Alineación forzada | ✅ | `POST /v1/forced-alignment` |
| 25 | Workspaces / facturación | ✅ | Planes y créditos confirmados; rollover hasta 2×; límite de uso por miembro (9 nov) |

**Funciones que faltaban en el mapa (nuevas, §6 de REA_VERIFICACION.md):**
Flows, generación de imagen y vídeo (terceros), Audio Native, Studio
Podcasts, Music Finetunes / stem separation / inpainting / planes de
composición, Video to Music como función propia, Scribe v3 Medical, Campaign
Manager, Reception, Architect, Unity SDK, Interaction Engine / Memory /
Routines (preview), Marketplace, Ads Engine, watermark de procedencia
(content provenance, beta 17 nov 2026), voces similares (`/v1/similar-voices`).

---

## 6. Modelos vigentes (noviembre 2026)

| Modelo | ID en API | Fecha | Datos clave (fabricante salvo indicación) |
|---|---|---|---|
| Eleven v4 | `eleven_v4` | 28 sep 2026 | Buque insignia; 90+ idiomas; 10.000 car./petición; etiquetas de audio; context stitching; #1 en Artificial Analysis (fabricante) |
| Eleven v4 Turbo | `eleven_v4_turbo` | 28 sep 2026 | ~100 ms latencia mediana de inferencia; ~150 ms hasta el primer audio; para agentes |
| Eleven v3 | `eleven_v3` | 2025 | 70+ idiomas; diálogo multi-hablante; 5.000 car./petición |
| Multilingual v2 | `eleven_multilingual_v2` | 2023 | 29 idiomas; el más estable para formato largo (docs) |
| Flash v2.5 | `eleven_flash_v2_5` | 2025 | ~75 ms; 32 idiomas; 40.000 car./petición — **no verificado** (solo consta en FEATURE_MAP.md) |
| Scribe v3 | `scribe_v3` | 9–10 nov 2026 | 102 idiomas; 27 % menos WER que v2 (FLEURS, fabricante); diarización −12 %/−17 % (3+ hablantes) |
| Scribe v3 Live | `scribe_v3_live` | 9–10 nov 2026 | 43 % menos WER semántico que v2 Realtime; diarización en vivo por 1.ª vez; turn prediction |
| Scribe v2 / v2 Realtime | `scribe_v2` | — | Siguen disponibles |
| Scribe v2 Medical / v3 Live Medical | — | nov 2026 | Transcripción clínica; v3 Live Medical para agentes de salud |
| SFX v3 | `eleven_text_to_sound_v3` | 29 oct 2026 | Varios sonidos por prompt; música y voces; por defecto en ElevenCreative desde 2 nov |
| SFX v2 | `eleven_text_to_sound_v2` | — | **Deprecated; se retira el 1 mar 2027** |
| Eleven Music v2.5 | `music_v2_5` | 11 sep 2026 | 3 s–5 min; planes de composición; inpainting; stems; finetunes |
| Eleven Realtime v1 Mini | `eleven_realtime_v1_mini` | 20 oct 2026 | Voz a voz en un solo modelo; por defecto; más rápido y barato |
| Eleven Realtime v1 Max | `eleven_realtime_v1_max` | 20 oct 2026 | Razona antes de responder; herramientas complejas |
| Voice Design v3 | `eleven_ttv_v3` | — | Última versión de diseño de voz por texto |

---

## 7. Superficie de API

### 7.1 API pública oficial (ElevenAPI)

- **Base:** `https://api.elevenlabs.io` · **Auth:** cabecera `xi-api-key`.
- **Documentación:** `https://elevenlabs.io/docs` (espejo:
  `https://elevenlabs.docs.buildwithfern.com`) · **OpenAPI:**
  `https://api.elevenlabs.io/docs`.
- **Tamaño (espejo del spec, `elevenlabs.docs.specway.com`): 258 endpoints en
  25 grupos.** Una skill de GitHub verificada en CI contra el OpenAPI en vivo
  (`adriendidoudid/eleven-sk`) y el catálogo WireMock (126 endpoints
  validados contra la API real) coinciden en la estructura; el conteo exacto
  varía según la versión del spec (126–258 según el espejo y la fecha).
- **SDKs:** Python y TypeScript oficiales (v2.79.0, nov 2026), CLI
  (`v1.7.0`), MCP hospedado (disponible en Claude desde ago 2026).

Endpoints principales por grupo (rutas exactas tomadas del espejo del spec y
de la skill verificada en CI; las rutas con `*` no se pudieron contrastar con
una segunda fuente):

| Grupo | Endpoints (método + ruta) |
|---|---|
| text-to-speech | `POST /v1/text-to-speech/{voice_id}`, `/stream`, `/with-timestamps`, `/stream/with-timestamps`; WS `/v1/text-to-speech/{voice_id}/stream-input` |
| text-to-dialogue | `POST /v1/text-to-dialogue`, `/stream`; WebSocket de diálogo (v4 Turbo) |
| speech-to-speech | `POST /v1/speech-to-speech/{voice_id}`, `/stream` |
| voices | `GET /v1/voices`, `GET /v2/voices`, `GET /v1/voices/{voice_id}`, `POST /v1/voices/add`, `POST /v1/voices/{voice_id}/edit`, `DELETE /v1/voices/{voice_id}`, `GET/POST /v1/voices/{voice_id}/settings`, samples (`GET/DELETE /v1/voices/{voice_id}/samples/{sample_id}`) |
| voice cloning (PVC) | `POST /v1/voices/pvc`, `POST /v1/voices/pvc/{voice_id}`, `POST /v1/voices/pvc/{voice_id}/verification`, `POST .../verification` (manual)* |
| text-to-voice (diseño/remix) | `POST /v1/text-to-voice/create-previews`, `POST /v1/text-to-voice`, `POST /v1/text-to-voice/design`, `POST /v1/text-to-voice/{voice_id}/remix`, `GET /v1/text-to-voice/{generated_voice_id}/stream` |
| voice library | `GET /v1/shared-voices`, `POST /v1/similar-voices`, `POST /v1/voices/add/{public_user_id}/{voice_id}` |
| speech-to-text | `POST /v1/speech-to-text`, `GET /v1/speech-to-text/transcripts/{id}`*; WS realtime (Scribe Live) |
| sound-generation | `POST /v1/sound-generation` (SFX v2/v3) |
| music | `POST /v1/music`, `/detailed`, `/stream`, `/detailed/stream`, `POST /v1/music/plan`, `POST /v1/music/video-to-music`, `POST /v1/music/upload`, `POST /v1/music/stem-separation`, `/v1/music/finetunes` (GET/POST/GET/PATCH/DELETE) |
| audio-isolation | `POST /v1/audio-isolation`, `/stream`, `GET/DELETE /v1/audio-isolation/history` |
| audio-effects | `GET /v1/audio-effects/catalog` |
| dubbing | `POST /v1/dubbing`, `GET /v1/dubbing`, `GET/DELETE /v1/dubbing/{dubbing_id}`, `GET /v1/dubbing/{dubbing_id}/audio/{language_code}`, `.../transcript/{language_code}`; proyectos: `GET/POST /v1/dubbing/project`, `GET /v1/dubbing/project/{project_id}`, `.../transcript`, `.../language`, `.../resource/{dubbing_id}/speaker/{speaker_id}/similar-voices`* |
| forced-alignment | `POST /v1/forced-alignment` |
| pronunciation | `/v1/pronunciation-dictionaries/*` (CRUD completo) |
| history | `GET /v1/history`, `POST /v1/history/download` |
| studio | `GET/POST /v1/studio/projects`, `POST /v1/studio/podcasts` |
| audio-native | `POST /v1/audio-native`, `POST /v1/audio-native/{project_id}/content`, `GET /v1/audio-native/{project_id}/settings`, `POST /v1/audio-native/content` |
| models / user | `GET /v1/models`, `GET /v1/user`, `GET /v1/user/subscription` |
| convai (ElevenAgents) | `/v1/convai/agents` (list/create), `/v1/convai/conversations`, `/v1/convai/tools`, `/v1/convai/knowledge-base`, `/v1/convai/mcp-servers`, `/v1/convai/secrets`, `/v1/convai/settings`, `/v1/convai/llm/list`, `/v1/convai/phone-numbers`, `/v1/convai/agent-testing`, `/v1/convai/analysis-items` (nov 2026), `POST /v1/convai/realtime/client-secret`, `/v1/convai/realtime/conversation-groups` |
| workspace | `/v1/workspace/members`, `/v1/workspace/invites`, `/v1/workspace/webhooks`, `/v1/workspace/service-accounts`*, `PUT /v1/workspace/members/{user_id}/usage-limit` (nov 2026) |
| content provenance | endpoint beta de detección de watermark (17 nov 2026; ruta exacta **no verificada**) |

### 7.2 Endpoints de la app web (no documentados)

**No se descubrió ninguno.** Sin navegador vivo no se puede leer el bundle JS
de `elevenlabs.io` ni capturar su tráfico, que es la única vía para conocer
los endpoints internos de la app web (si los hay además de la API pública).
La documentación oficial afirma que la web es solo un frontend de la API, lo
que sugiere que **no hay una API web privada relevante**, pero eso es una
afirmación del fabricante, no una comprobación. Ver §8.3 para la lista de
capturas pendientes.

### 7.3 Lo que la API pública NO expone (deliberadamente)

Según la skill verificada en CI (`adriendidoudid/eleven-sk`): **no hay
generación de texto a imagen ni a vídeo en la API pública**; eso vive solo en
la app web cerrada ElevenCreative (y en una Studio API con acceso Enterprise).
ElevenAgents (telefonía, batch calling) es una superficie aparte muy grande
que esa skill declina cubrir. El clon no necesita ninguna de las dos.

---

## 8. Lo que queda para una inspección en navegador vivo

Esta es la lista exacta de trabajo pendiente para el agente que sí tenga
navegador vivo con DevTools y login. **Nada de esto se hizo en este informe.**

### 8.1 Preparación

1. Crear/obtener acceso a una cuenta de ElevenLabs (plan Free basta para la
   mayor parte; Starter $6 para IVC y Dubbing Studio).
2. Abrir `https://elevenlabs.io/app` (o la ruta actual de la app) con DevTools
   → pestaña Network → activar "Preserve log" y el filtro de Fetch/XHR.
3. Anotar la versión del bundle JS principal (nombre del archivo `.js` con
   hash) para poder citarlo.

### 8.2 Endpoints de la app web a capturar (Network)

| # | Qué capturar | Por qué |
|---|---|---|
| N1 | Todas las peticiones al cargar la app (`/app`, Speech, Voices, Studio) | Confirmar si la web llama solo a `api.elevenlabs.io` o hay un host interno (`*.elevenlabs.io/api/...`) |
| N2 | `POST` de generación TTS desde la web (cuerpo exacto) | Ver parámetros reales que envía la UI (p. ej. `audio_effects`, `clone_strength`, `use_pvc_as_ivc`) y compararlos con la API pública |
| N3 | Peticiones de Voice Library (búsqueda, filtros, paginación) | Confirmar si usa `/v2/voices` y `/v1/shared-voices` o un endpoint web propio |
| N4 | Flujo IVC/PVC en la web (subida de muestras, verificación por captcha) | Capturar los endpoints de subida y verificación; confirmar `POST /v1/voices/pvc/{id}/verification` |
| N5 | Studio: guardar/generar/exportar proyecto | Confirmar si Studio usa `/v1/studio/projects` o endpoints web propios; ver el formato de exportación |
| N6 | Dubbing v2 en la web (crear, editar transcripción, regenerar segmento) | La API pública restringe edición/regeneración a Enterprise; ver qué hace la web |
| N7 | Flows: crear nodo, ejecutar, exportar a Studio | Flows es Alpha y puede tener endpoints no documentados |
| N8 | History y descarga por lotes | Confirmar `POST /v1/history/download` |
| N9 | Cualquier petición a un host distinto de `api.elevenlabs.io` | Detectar telemetría, websockets de realtime, o APIs internas |
| N10 | Cabeceras de autenticación de la web (¿`xi-api-key`, cookie de sesión, JWT?) | Determinar si la web usa la misma auth que la API pública |

### 8.3 Bundles JS a inspeccionar

1. Descargar el bundle principal de la app y buscar en el texto las cadenas
   `/v1/`, `api.elevenlabs.io`, `wss://` y `elevenlabs.io/api` para listar
   endpoints embebidos no documentados.
2. Buscar `model_id` por defecto en la UI (qué modelo usa cada pantalla cuando
   el usuario no elige).
3. Buscar límites embebidos en el cliente (máx. de caracteres por campo,
   tamaños de archivo aceptados, formatos) y contrastarlos con la documentación.

### 8.4 Flujos a recorrer con la red grabando

1. TTS con v4 + etiqueta de audio + audio effect (ver el cuerpo exacto).
2. Crear IVC (subir muestra, guardar) y generar con ella.
3. Voice Design (generar previews, guardar una).
4. Dubbing v2 de un vídeo corto a un idioma (ver jobs asíncronos y polling).
5. Scribe: subir un audio y ver la respuesta con diarización.
6. Studio: crear proyecto, añadir párrafo, generar, exportar MP3.
7. ElevenAgents: crear un agente mínimo y hacer una llamada de prueba web
   (capturar el WebSocket de conversación).
8. SFX v3 con `loop: true` (la documentación se contradice sobre si el loop
   funciona en v3; la red dirá qué envía la UI).

### 8.5 Preguntas que solo el navegador vivo puede cerrar

- ¿La web usa exactamente la API pública o hay endpoints web propios?
- Límites reales de subida de Dubbing en la app (1 GB vs 2 GB).
- Número exacto de vistas previas de Voice Design (3 vs 5).
- ¿Funciona `loop` con SFX v3 desde la UI?
- ¿Qué exporta realmente un doblaje v2 (solo MP4, o también audio y WebVTT)?
- Límites de caracteres por plan en la UI (Flash v2.5: ¿40.000?).
- ¿Cuántas voces lista la Voice Library y qué filtros ofrece la UI?
- ¿Qué parámetros envía la web al generar con un PVC afinado en v4?

---

## 9. Riesgos y notas para el clon

- **La brecha real no es de funciones sino de modelos cerrados:** v4, Scribe v3,
  SFX v3 y Music v2.5 son cerrados; el clon los sustituye con modelos locales
  de calidad menor en expresividad sostenida y en español largo (ver
  `RESEARCH.md`).
- **El mapa de funciones crece cada mes:** entre el 28 sep y el 17 nov 2026
  ElevenLabs lanzó v4, SFX v3, Realtime, Video to Music, Scribe v3, ElevenAI,
  Campaign Manager, Unity SDK, Marketplace y el watermark de procedencia.
  Cualquier clon "exacto" queda desactualizado en semanas; fijar la foto de
  noviembre 2026 como alcance y revisarla por changelog, no por la web.
- **No replicar la facturación ni el Marketplace:** son modelo de negocio, no
  funciones de audio. El clon ya lo decidió así (§25 del mapa).
- **Consentimiento y watermark:** ElevenLabs marca sus audios con watermark
  (endpoint beta de detección desde el 17 nov 2026) y exige verificación por
  captcha para PVC. El clon debe mantener su `consent_note` y su registro de
  procedencia (§3–§4 y §16 del mapa).
- **Licencias de los modelos locales:** sin cambios respecto a `FEATURE_MAP.md`
  y `RESEARCH.md`. Recordatorio: F5-TTS, Fish Speech, MusicGen y NLLB son no
  comerciales; el clon es de uso privado para 2 usuarios.

---

## 10. Fuentes

**Oficiales (espejadas; la web oficial no se pudo abrir en esta sesión):**
- Changelog oficial espejado (Fern): `https://elevenlabs.docs.buildwithfern.com/docs/changelog/2026/10/12`,
  `.../2026/10/19`, `.../2026/11/9` (Scribe v3, Unity SDK, workflows as code,
  SFX concurrency, workspace usage-limit).
- Índice de releases: `https://releases.sh/elevenlabs/elevenlabs-changelog`
  (17 nov 2026: STT $0,20/$0,22 h; watermark beta; tools en código v2.79.0).
- Espejo del spec OpenAPI (258 endpoints): `https://elevenlabs.docs.specway.com/api`
- Espejo de la documentación en GitHub: `https://github.com/handotdev/elevenlabs-docs/blob/HEAD/api-reference/getting-started.mdx`
  ("la web es solo un frontend de la API").

**Skills/repos que verifican la API contra el spec en vivo:**
- `https://github.com/adriendidoudid/eleven-sk/blob/HEAD/README.md` (verificado
  en CI contra el OpenAPI en vivo; 258 endpoints no; tabla de capacidades por endpoint).
- `https://github.com/lap-platform/claude-marketplace/blob/HEAD/plugins/elevenlabs-io-elevenlabs-io/skills/api/SKILL.md`
  (258 endpoints en 25 grupos).
- `https://www.wiremock.io/sandboxes/elevenlabs-elevenapi` (126 endpoints
  validados contra la API real mediante proxy de grabación).
- `https://github.com/mrgoonie/multix-cli/blob/HEAD/plans/reports/researcher-260505-1326-elevenlabs-api-surface.md`
  (may 2026; endpoints y parámetros por categoría).

**Reseñas independientes con fecha de verificación (nov 2026):**
- Precios y planes (2 oct–20 nov 2026): `https://www.cartesia.ai/learn/elevenlabs-pricing`,
  `https://www.stork.ai/en/elevenlabs`, `https://fruitpunch.ai/review/elevenlabs`,
  `https://techjacksolutions.com/ai-tools/elevenlabs/elevenlabs-pricing/`,
  `https://dev.to/aistackguide/what-a-dubbed-minute-really-costs-youtube-auto-dub-vs-elevenlabs-vs-rask-ai-vs-heygen-291g`
- v4 / v4 Turbo: `https://www.explainx.ai/blog/elevenlabs-eleven-v4-v4-turbo-voice-models-2026`,
  `https://growthgrader.org/blog/eleven-v4-elevenlabs-new-voice-model-review/`,
  `https://micdrop.dev/blog/eleven-v4-turbo-voice-agent`,
  `https://www.digitalapplied.com/blog/eleven-v4-turbo-voice-agents-latency-pricing`
- Scribe v3: `https://www.wirestack.site/e/elevenlabs-scribe-v3-sound-effects-concurrency-realtime-audio-formats-november-2026`,
  `https://techjacksolutions.com/ai-tools/elevenlabs/scribe-3/`,
  `https://www.assemblyai.com/blog/assemblyai-universal-3-pro-vs-elevenlabs-scribe-v2-compared`
- Octubre 2026 (Realtime, Video to Music, Realtime Translation):
  `https://dailyaipedia.com/elevenlabs-update-2026/`,
  `https://www.newtoolnow.com/guides/elevenlabs-video-to-music/`,
  `https://aiplantracker.com/tools/elevenlabs/news/`
- Clonación: `https://www.bland.ai/compare/bland-speech-vs-elevenlabs-voice-cloning`,
  `https://aiproductivity.ai/guides/elevenlabs-voice-cloning-tutorial/`
- Dubbing: `https://aiproductivity.ai/guides/elevenlabs-multilingual-dubbing-workflow/`,
  `https://www.stork.ai/blog/elevenlabs-dubbing-2026`,
  `https://www.vosko.ai/compare/vosko-ai-vs-elevenlabs-dubbing/`
- SFX v3: `https://www.stork.ai/blog/elevenlabs-sound-effects-2026`,
  `https://thehype.news/how-to-use-elevenlabs-sfx-v3/`,
  `https://mishalbrands.com/trends/elevenlabs-sfx-v3`
- Música v2.5: `https://agientry.com/en/applications/eleven-music`,
  `https://tessl.io/registry/skills/github/elevenlabs/skills/music`,
  `https://www.reviewramble.com/models/eleven-music-v2-5`
- ElevenCreative / Flows / Studio: `https://www.stork.ai/en/elevencreative-by-elevenlabs`,
  `https://www.sabentis.com/en/explore/tools/elevenlabs/`,
  `https://blocksentient.com/briefings/briefing_elevencreative.pdf`
- ElevenReader: `https://www.europeanapps.com/elevenreader/`,
  `https://www.audiopageapp.com/blog/elevenreader-review`,
  `https://toolgpa.com/tools/elevenreader`, `https://elevenreader.io/speechify-alternative`
- Summit 11 nov 2026 / agentes: `https://www.scriptbyai.com/elevenlabs-timeline/`,
  `https://dev.to/alfazreviews/elevenlabs-launched-13-products-this-week-only-3-matter-if-you-build-voice-agents-4nfe`,
  `https://www.my2cents.ai/news/2026-11-05-elevenlabs/`
- Modelos (línea de tiempo): `https://www.avocolab.com/ai-models/elevenlabs`

**Archivos del proyecto consultados:**
- `~/workspace/elevenlabs-clon/FEATURE_MAP.md` (25 funciones, 20 nov 2026)
- `~/workspace/elevenlabs-clon/RESEARCH.md` (modelos locales)
- `~/workspace/custom-skills/local-rea/SKILL.md` (metodología REA)
