# Deltas REA aplicadas — Sonora (clon de ElevenLabs)

**Fecha:** 20 de noviembre de 2026
**Fuentes:** `REA.md` + `REA_VERIFICACION.md` (20 nov 2026)
**Resultado:** `FEATURE_MAP.md` v1 → v2. Sin cambios de arquitectura, sin
reescrituras de pantallas, presupuesto cero.

## Resumen de conteos

| Ámbito | Cantidad |
|---|---|
| Deltas aplicadas al mapa (secciones corregidas) | **10** (§4, §5, §6, §9, §10, §11, §12, §14, §18 + §21 corrección de contenido) |
| Precisiones menores aplicadas al mapa (sin cambio de grado) | **6** (§1, §2, §3, §17, §19, §25) |
| Áreas añadidas al mapa | **16 filas (A1–A16)**: 13 secciones nuevas (§26–§38) + 3 sub-funciones plegadas en §10 y §12 |
| Correcciones aplicadas al código | **3** (quirúrgicas, solo texto visible / docstrings) |
| Pendientes (no resueltos aquí) | **8 discrepancias** para el navegador vivo + **2 funciones nuevas sin implementar** + 1 sub-función dependiente de §14 |

**Grados sin cambio:** 10 totales · 10 parciales · 5 no replicables sobre las
25 funciones originales. Las añadidas llevan su propio grado (🟢 2 · 🟡 5 ·
🔴 9) y no alteran ese conteo. Total mapeado en v2: 37 áreas.

---

## 1. Qué cambió en el mapa (FEATURE_MAP.md v2)

Changelog añadido al inicio del archivo (v1 → v2, fecha, qué cambió).

### 1.1 Secciones corregidas (10)

| § | Corrección aplicada |
|---|---|
| §4 PVC | Fine-tuning sobre v4/v4 Turbo **abierto a todos los workspaces desde el 2 nov 2026**; parámetro `clone_strength`. Slots corregidos: **1 en Creator y Pro**, 3 en Scale, 10 en Business. Verificación = **captcha de voz** (`POST /v1/voices/pvc/{voice_id}/verification`); la manual es solo fallback. |
| §5 Voice Library | Cifra corregida a **10.000+ voces**; «17.500+» marcado **no verificado** (Apéndice D, D6). Añadido: **Voice Marketplace** (may 2026, licencias y royalties) y endpoints de descubrimiento (`GET /v2/voices`, `GET /v1/shared-voices`, `POST /v1/similar-voices`). |
| §6 Voice Design | Modelo en API: `eleven_ttv_v3`. Discrepancia abierta: **3 vs 5 vistas previas** (Apéndice D, D1). |
| §9 Dubbing | **Dos productos excluyentes, no uno:** Dubbing v2 automático (por defecto, alfa; edición en app, por API solo Enterprise) vs Dubbing Studio v1 (legacy, solo mantenimiento). Un doblaje automático no se puede convertir en proyecto de Studio v1. Límites **en disputa**: 1 GB (docs) / 2 GB (ayuda) / 3 GB (API); v1: 1 GB y 45 min. Costes: 2.000–10.000 créditos/min son tarifas **v1**; v2 cuesta **$2,20/min** por API (~13.500 créditos/min en app según una prueba práctica). Exportación v2: MP4 verificado; audio separado **no verificado**; subtítulos WebVTT desde el changelog del 19 oct 2026. v2 trabaja desde el audio original, no desde una transcripción. Endpoint del clon: límite propio 500 MB. |
| §10 Scribe | **Scribe v3 / v3 Live son los modelos vigentes** (9–10 nov 2026); v2 sigue disponible. Mejoras del fabricante, parámetros nuevos (`numbers_format`, `secondary_language_codes`, keyterms hasta 1.000 en lote y biblioteca de 10.000 en Live, `commit_strategy=turn_prediction`, `multilang_mode`, `entity_redaction`). **Scribe v2 Medical y v3 Live Medical** como modelos aparte. Precio API: **$0,20/hora por lotes y $0,22/hora en tiempo real** (17 nov 2026). «Hasta 32 hablantes etiquetados» marcado **no verificado** (D7). |
| §11 SFX | **SFX v3** (`eleven_text_to_sound_v3`, 29 oct 2026), por defecto en la app desde el 2 nov. Duración **0,5–30 s**; prompt hasta **450 caracteres** en la app; `prompt_influence` 0–1 (def. 0,3); hasta 4 variantes. **Loop en disputa** (D3). **SFX v2 deprecated, se retira el 1 mar 2027.** Coste 200 créditos/generación; concurrencia propia 4/6/8 por plan. |
| §12 Music | **Music v2.5** (`music_v2_5`, 11 sep 2026); **v1 deprecated, se retira el 31 ene 2027**. Pistas **3 s–5 min** (plan de composición hasta 10 min). Sub-funciones añadidas: planes de composición, inpainting, separación de stems, Audio Reference, Music Finetunes ($1,50), **Video to Music / Instant Soundtracks** (19 oct 2026; a 26 oct 2026 solo API, sin botón en la app — no verificado del todo), publicación en SoundCloud (6 nov), firma C2PA, Zero Retention (Enterprise). Coste API $0,15/min; app 900 créditos/min. Grado: el listón real incluye edición por secciones; el clon cubre la generación básica. |
| §14 Studio | Studio es hoy un **editor de línea de tiempo multimedia con vídeo** (no solo audiolibros/podcasts). **Recomienda v4 desde el 2 nov 2026.** Endpoint `POST /v1/studio/podcasts` (ver §29). |
| §18 Agentes | Añadidos de nov 2026: **Campaign Manager** (§30), **Reception** (§31), **Architect** (§32), **Unity SDK** (§33), **Eleven Realtime** como modo de voz, Workflows as code, herramientas en código + 39 MCP hospedadas, Analysis Items API, guardrails GA, colas de espera, DTMF, timeouts de servidor desde el 26 nov 2026. LLM por defecto `gemini-3.5-flash`; `gpt-6.1-terra` y Nemotron 3.5 Super VL añadidos; Claude Sonnet 4.5 deprecated el 30 nov. **Preview no lanzado:** Interaction Engine / Memory / Routines (§34). «55 % de sus ingresos» marcado **no verificado** (D8). |
| §21 ElevenReader | **Corrección de contenido:** el audio **NO es exportable** ni usable comercialmente según la documentación de ElevenReader. **Eliminada** la frase de v1 «el audio se descarga como MP3, que es el equivalente práctico»: no es equivalente a la función real (escuchar dentro de la app); la exportación pertenece a Studio (§14). Idiomas: **32** según documentación (90+ en marketing). Planes propios: Free 10 h/mes; **Ultra $11/mes ($8,25 anual)**. Catálogo **200.000+ audiolibros y eBooks premium**. Añadidos: sincronización web/móvil, extensión de Chrome, importación inteligente, GenFM, escaneo con cámara, límites offline (20 h/día, 150 h/mes). Grado sigue 🟡 Parcial, con el matiz registrado. |

### 1.2 Precisiones menores (6, sin cambio de grado)

| § | Precisión |
|---|---|---|
| §1 TTS | En v4 solo quedan los sliders Stability y Similarity (Style/Speed no existen en v4); `style_exaggeration` del endpoint del clon es un parámetro propio (Qwen3-TTS), no un control de v4. SSML `<break>` desactivado en v4: usar `[pause]` / `[long pause]`. Los 40.000 caracteres de Flash v2.5 marcados **no verificados**. |
| §2 Text to Dialogue | v4 por la API de Text to Dialogue; **v4 Turbo por el WebSocket** (no por REST). |
| §3 IVC | Mínimo real en v4: **10 s** de audio; la documentación recomienda 1–2 min y la página de clonación dice que 1–5 min funcionan bien. |
| §17 API | Spec público: **258 endpoints en 25 grupos** (catálogo validado: 126; diferencia de versión/agrupación). MCP hospedado en Claude desde ago 2026. SDKs v2.79.0. |
| §19 Realtime | IDs `eleven_realtime_v1_mini` / `_max`; despliegue completado el 2 nov 2026; sesiones inactivas se cierran a los 3 min; grupos de conversación; secreto de cliente. |
| §25 Workspaces | Créditos de pago **se acumulan hasta 2× la cuota** (saldo máx. 3×); límite de uso mensual por miembro (`PUT /v1/workspace/members/{user_id}/usage-limit`, 9 nov 2026); Free no comercial, atribución obligatoria. |

### 1.3 Áreas añadidas (16 filas A1–A16)

13 secciones nuevas §26–§38 + 3 sub-funciones plegadas en su sección:

| Nueva | Área | Grado |
|---|---|---|
| §26 | ElevenCreative Flows (canvas de nodos, Alpha) | 🔴 No |
| §27 | Generación de imagen y vídeo (Veo 3.1, Kling, Runway, FLUX…) | 🔴 No |
| §28 | Audio Native (player integrable) | 🟡 Parcial |
| §29 | Studio Podcasts | 🟡 Parcial |
| §30 | Campaign Manager (ElevenAgents) | 🔴 No |
| §31 | Reception (ElevenAgents) | 🔴 No |
| §32 | Architect (ElevenAgents) | 🔴 No |
| §33 | Unity SDK (ElevenAgents) | 🔴 No |
| §34 | Interaction Engine / Memory / Routines (preview, no lanzado) | 🔴 No |
| §35 | Marketplace (apps de socios) | 🔴 No |
| §36 | Ads Engine (revisión humana) | 🔴 No |
| §37 | Content provenance (detección de watermark, beta; ruta no verificada) | 🟢 Total (equivalente propio) |
| §38 | Voces similares (`POST /v1/similar-voices`) | 🟡 Parcial |
| §10 (sub) | Scribe v2 Medical / v3 Live Medical | 🟢 Total (lotes) |
| §12 (sub) | Music: planes de composición, inpainting, stems, finetunes | 🟡 Parcial |
| §12 (sub) | Video to Music / Instant Soundtracks (función propia) | 🟡 Parcial |

Apéndice A ampliado con las filas 26–38 y el conteo v2; Apéndice B
(«No hacer») ampliado con §26, §27, §30–§36.

---

## 2. Qué se corrigió en código (quirúrgico, solo texto visible)

| # | Archivo:línea | Cambio |
|---|---|---|
| C1 | `app/index.html:242` | Doblaje: «máx. 2 GB · máx. 180 min» → «máx. 500 MB en este clon · máx. 180 min (límite real de ElevenLabs en disputa: 1–3 GB según la fuente)». La cifra 2 GB estaba en disputa y además contradecía el límite real del backend (500 MB, `MAX_DUBBING_MB`). |
| C2 | `backend/app/routers/dubbing.py:7-8` | Docstring del módulo: añadida la nota del límite en disputa (1 GB docs / 2 GB ayuda / 3 GB API) y el límite propio del clon (500 MB por defecto). Sin cambio de comportamiento. |
| C3 | `backend/app/routers/not_implemented.py:124-127` | Respuesta 501 de ElevenReader: añadida la nota REA — en ElevenReader el audio no es exportable; la alternativa (TTS + descarga MP3) es otra función (exportación de Studio), no el Reader. Sin cambio de comportamiento (sigue siendo 501). |

**Verificado en código antes de tocar nada:** el frontend **no tiene pantalla
de ElevenReader** y el backend no ofrece ninguna descarga MP3 como equivalente
de Reader (los endpoints `/reader/*` ya eran 501 honestos), así que la
corrección §21 no exigía ningún cambio de comportamiento, solo el mapa (C3).

**No se tocó (deliberadamente):**
- `style_exaggeration` en `app/js/app.js` y `backend/app/routers/tts.py`:
  es un parámetro propio del clon (Qwen3-TTS), no una afirmación sobre v4;
  el mapa lo aclara en §1.
- Voice Design «3 muestras» (`app/index.html`, `backend/app/routers/voices.py`):
  cifra en disputa (3 vs 5) — queda pendiente D1, no se cambia a ciegas.
- SFX: el slider 1–47 s y `maxlength=500` del prompt son límites **locales**
  (Stable Audio Open), no afirmaciones sobre SFX v3 (0,5–30 s, 450 car. en la
  app real); el mapa recoge los límites reales en §11 sin tocar el comportamiento
  local.
- Límite de subida de doblaje del backend (500 MB): es el límite propio del
  clon, no una afirmación sobre ElevenLabs; no se cambia.

**Validación:** los dos módulos Python editados pasan `ast.parse`. La suite
`pytest` del backend **no se pudo ejecutar en esta VM** (no hay `pytest` ni
`fastapi` instalados en el Python del sistema); los cambios son solo cadenas
de texto, sin lógica alterada.

---

## 3. Qué quedó pendiente

### 3.1 Discrepancias abiertas — para el navegador vivo (Apéndice D del mapa)

| # | Discrepancia | § |
|---|---|---|
| D1 | Voice Design: ¿3 o 5 vistas previas? | §6 |
| D2 | Dubbing: ¿límite de subida 1 GB / 2 GB / 3 GB? | §9 |
| D3 | SFX v3: ¿funciona `loop: true` en v3? | §11 |
| D4 | Dubbing v2: ¿qué exporta realmente (solo MP4, o también audio separado y WebVTT)? | §9 |
| D5 | Flash v2.5: ¿40.000 caracteres por petición? | §1 |
| D6 | Voice Library: ¿17.500+ voces? (usar 10.000+ hasta verificar) | §5 |
| D7 | Scribe: ¿hasta 32 hablantes etiquetados? | §10 |
| D8 | Agentes: ¿«55 % de sus ingresos»? | §18 |

Además: ruta exacta del endpoint beta de content provenance (§37) sin
verificar, y sin inspección de tráfico de la app web (N1–N10 de `REA.md` §8).

### 3.2 Funciones nuevas que exigen trabajo grande — NO implementadas, anotadas en el mapa

| Función | § | Motivo |
|---|---|---|
| Audio Native (player integrable) | §28 | Función nueva completa; el mapa la marca 🟡 Parcial con el motor de TTS existente, pero no hay player ni endpoint. |
| Voces similares (`POST /v1/similar-voices`) | §38 | Función nueva; replicable solo dentro de la biblioteca propia. |
| Studio Podcasts | §29 | Depende de §14 (Studio/Projects), aún no construido (Fase 3, 501). |

El resto de áreas añadidas (§26, §27, §30–§36) son 🔴 No replicables por
alcance y quedan en «No hacer» (Apéndice B).
