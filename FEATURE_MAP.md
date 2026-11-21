# FEATURE_MAP — ElevenLabs → clon local open-source

**Fecha de investigación:** 20 de noviembre de 2026
**Proyecto:** clon web de ElevenLabs con modelos locales, presupuesto cero, 2 usuarios, sin 24/7
**Arquitectura de referencia:** frontend estático en GitHub Pages + backend FastAPI bajo demanda.
TTS base en CPU: Kokoro-82M. Clonación zero-shot en GPU (Kaggle T4 16 GB).
**Alcance de este documento:** mapa función por función. No es un plan de implementación
(eso lo hacen los agentes de backend/frontend); es la especificación de *qué* se puede
replicar, con *qué* modelo/herramienta, y *qué endpoint* necesita cada función.

> **Nota de verificación:** la web oficial `elevenlabs.io` estaba bloqueada para la
> lectura directa de páginas en esta sesión (el intento de abrir `/pricing` devolvió
> error de política del origen), por lo que la lista de funciones se verificó contra
> la documentación oficial (changelog de octubre de 2026), la página de precios
> reflejada en reseñas independientes fechadas el 1 de noviembre de 2026 y varias
> reseñas cruzadas entre sí. Donde dos fuentes secundarias discrepan (p. ej. número
> de idiomas: 74 en la tabla de planes frente a 90+ en los modelos v4), se indica
> la discrepancia en vez de elegir un número.

---

> ## Changelog — v1 → v2 (20 de noviembre de 2026)
>
> Verificación REA función por función contra la app real de ElevenLabs
> (`REA.md` + `REA_VERIFICACION.md`, 20 nov 2026). **Deltas aplicadas al mapa:
> 10 secciones** — 9 funciones con corrección (§4, §5, §6, §9, §10, §11, §12,
> §14, §18) + §21 con corrección de contenido (el audio de ElevenReader **no
> es exportable**; la descarga de MP3 no equivale a esa función). **Áreas
> añadidas: 16 filas (A1–A16 de `REA_VERIFICACION.md` §4)**: 13 como secciones
> nuevas (§26–§38) y 3 como sub-funciones plegadas en su sección (§10 Scribe
> Medical, §12 planes de composición / inpainting / stems / finetunes y Video
> to Music). **Grados sin cambio:** 10 totales · 10 parciales · 5 no
> replicables sobre las 25 funciones originales; las añadidas llevan su
> propio grado y no alteran ese conteo. **Total mapeado en v2: 37 áreas**
> (25 + 12 nuevas, contando las sub-funciones dentro de su sección, según
> `REA_VERIFICACION.md` §4). **Pendientes para el navegador vivo: 8
> discrepancias abiertas** marcadas «no verificado» (ver Apéndice D); no se
> resolvieron aquí.
>
> ---

## 0. Resumen ejecutivo

| Grado | Funciones | N.º |
|---|---|---|
| 🟢 Totalmente replicable | TTS, Instant Voice Cloning, Voice Design, Speech to Text (Scribe), Voice Isolator, diccionario de pronunciación, History, API propia, efectos de audio, alineación forzada / subtítulos | **10** |
| 🟡 Parcialmente replicable | Text to Dialogue, Professional Voice Cloning, Voice Remix, Speech to Speech / Voice Changer, Dubbing, Sound Effects, Music, Studio (Projects), Agentes conversacionales (pipeline), ElevenReader | **10** |
| 🔴 No replicable (en este proyecto) | Voice Library, Eleven Realtime (voz a voz en un solo modelo), Realtime Translation, ElevenAI, Workspaces / equipos / facturación | **5** |
| **Total mapeado** | | **25** |

**Áreas añadidas en v2 (REA):** 16 filas (A1–A16): 13 secciones nuevas (§26–§38)
y 3 sub-funciones plegadas en §10 y §12. Sus grados: 🟢 2 (Scribe Medical,
content provenance) · 🟡 5 (Audio Native, Studio Podcasts, sub-funciones de
Music, Video to Music, voces similares) · 🔴 9 (Flows, imagen y vídeo,
Campaign Manager, Reception, Architect, Unity SDK, Interaction Engine /
Memory / Routines, Marketplace, Ads Engine). **Total mapeado en v2: 37
áreas.** El conteo original 10/10/5 no cambia.

**Lectura honesta del resumen:** el núcleo de ElevenLabs —sintetizar texto con una voz
(clonada o de diseño), transcribir, limpiar audio y organizar proyectos— **sí se replica
con software libre y calidad utilizable**. Lo que **no** se replica es (a) el catálogo
propietario de miles de voces con licencia y reparto de ingresos, (b) la latencia
ultrabaja (~75–100 ms) y la calidad expresiva de los modelos cerrados v3/v4 en
narración larga, y (c) los productos de agente de voz en tiempo real de extremo a
extremo. Ningún modelo local iguala hoy a Eleven v4 en arco emocional sostenido
durante miles de palabras; la brecha en MOS (calidad percibida) entre el mejor
open-source y ElevenLabs se estima en 2026 en ~0,1–0,2 puntos, pero esa cifra es
un promedio: en español y en textos largos la brecha es mayor.

**Regla de oro para el backend:** un solo motor de clonación como primario
(**Qwen3-TTS 1.7B**, Apache-2.0, zero-shot desde 3 s) + **Kokoro-82M** como motor
rápido en CPU para voces fijas. No se instalan cinco clonadores a la vez: cada
modelo extra es VRAM, disco y mantenimiento en una T4 de 16 GB. Los demás modelos
de este mapa son alternativas documentadas, no una lista de la compra.

### Modelos de referencia (licencias verificadas en noviembre de 2026)

| Modelo / herramienta | Uso en el clon | Licencia | Advertencia |
|---|---|---|---|
| Kokoro-82M (`hexgrad/Kokoro-82M`) | TTS rápido en CPU, voces fijas | Apache-2.0 | No clona. 54 voces, 8 idiomas. Español presente pero más flojo que el inglés. Sin release nuevo desde feb 2025. |
| Qwen3-TTS 0.6B / 1.7B (`Qwen/Qwen3-TTS-…`) | TTS + clonación zero-shot + Voice Design | Apache-2.0 (código y pesos) | **Primario recomendado.** 10–11 idiomas incl. español. 1.7B ~3,4 GB. Streaming con primer audio ~97 ms según el fabricante. |
| CosyVoice 2 / 3 (`FunAudioLLM`) | Alternativa de clonación, streaming ~150 ms | Apache-2.0 | 9 idiomas + dialectos chinos. Mejor en EN/ZH que en ES. |
| VoxCPM2 (`OpenBMB`) | Alternativa Apache-2.0, 30 idiomas, Voice Design | Apache-2.0 | ~8 GB VRAM. |
| Chatterbox Turbo / Multilingual v3 (`ResembleAI`) | Clonación, 23 idiomas, MIT | MIT | **Retirado en agosto de 2026** según una comparativa de nov 2026: no basar el proyecto en él; solo plan B archivado. |
| F5-TTS | Clonación, prosodia de largo formato | **CC-BY-NC-4.0 (pesos)** | Calidad alta, pero **no comercial**. Para un clon de uso personal/privado es usable; no redistribuir ni monetizar. |
| Fish Speech / OpenAudio S1-mini | Clonación, 80+ idiomas (S2) | **CC-BY-NC-SA-4.0** (S1-mini); Drama 3 con tope de ingresos | No comercial sin licencia aparte. Calidad muy alta, pero licencia incompatible con uso comercial. |
| XTTS v2 (Coqui) | Clonación histórica, 17 idiomas | CPML (Coqui Public Model License) | **Coqui cerró en diciembre de 2025.** Sin mantenimiento. No elegirlo para un proyecto nuevo en 2026. |
| IndexTTS-2 | Clonación + control de emoción/duración | Licencia de modelo de Bilibili | **Uso comercial solo con acuerdo aparte.** Evitar como primario. |
| Dia 1.6B (Nari Labs) | Diálogo multi-hablante en una pasada | Apache-2.0 | Solo inglés. Identidad de voz inestable sin semilla. |
| Orpheus-3B (Canopy Labs) | TTS emotivo con etiquetas (`<laugh>`, `<sigh>`) | Apache-2.0 | Solo inglés. 3B: pesado para T4 si convive con otros modelos. |
| faster-whisper / WhisperX | Speech to Text + timestamps por palabra | MIT (código); pesos de Whisper bajo licencia MIT de OpenAI | large-v3: ~100 idiomas. Diarización con pyannote (modelos con acceso restringido: hay que aceptar condiciones en Hugging Face). |
| Demucs (`facebookresearch/demucs`) | Voice Isolator | MIT | Separa voz de música/ruido. Lento en CPU; en T4 va bien. |
| Stable Audio Open 1.0 | Sound Effects / loops | Stability AI Community License | Gratis por debajo de 1 M$ de ingresos/año. Hasta 47 s, estéreo 44,1 kHz. Sin voces. |
| MusicGen (Meta, `audiocraft`) | Música instrumental | Código MIT / **pesos CC-BY-NC-4.0** | No comercial. Máx. ~30 s por generación en la práctica. |
| ACE-Step 1.5 | Música con voces y letra | Apache-2.0 | Mejor alternativa permisiva para canciones completas; 3,5B, ~4 GB VRAM. |
| NLLB-200 / MADLAD-400 (Meta/Google) | Traducción para Dubbing | CC-BY-NC (NLLB) / Apache-2.0 (MADLAD-400) | NLLB no comercial; MADLAD-400 es la vía permisiva. Traducir ES↔EN es el caso fácil; 90 idiomas no es realista en local. |

> **Sobre licencias:** "open-source" no significa "sin condiciones". Antes de publicar
> o compartir cualquier audio generado, el agente de backend debe dejar por escrito
> en el repo qué modelo genera cada salida y bajo qué licencia. Los modelos
> CC-BY-NC (F5-TTS, Fish Speech, MusicGen, NLLB) **no** pueden usarse con fines
> comerciales. Como el clon es para 2 usuarios y uso privado, son aceptables en
> local; no lo serían en un producto público de pago.

---

## 1. Text to Speech (TTS)

**Qué hace en ElevenLabs:** convierte texto en audio con voces naturales. Modelos
actuales (nov 2026): Eleven v4 (buque insignia, 90+ idiomas, hasta 10.000 caracteres
por petición, etiquetas de audio `[laughs]`, `[whispers]`), Eleven v4 Turbo
(~100 ms de latencia mediana, para apps en vivo), Eleven v3 (70+ idiomas,
diálogo multi-hablante), Multilingual v2 (29 idiomas, el más estable para
narración larga) y Flash v2.5 (32 idiomas, ~75 ms; los 40.000 caracteres por petición **no
están verificados**: solo constan en este mapa, ninguna fuente consultada
los confirma ni los niega). Controles de estabilidad, claridad/similitud y exageración de estilo.
**Precisión REA:** en v4 solo quedan los sliders **Stability y Similarity**;
los sliders Style y Speed de modelos anteriores **no existen en v4**. El
parámetro `style_exaggeration` del endpoint del clon es propio (Qwen3-TTS),
no un control de v4.
Salida MP3/WAV, hasta 44,1 kHz PCM en planes Pro+ vía API. En v4, SSML
`<break>` está desactivado: se usan las etiquetas `[pause]` / `[long pause]`.

**Equivalente local:** **Kokoro-82M** (CPU, voces fijas) + **Qwen3-TTS 1.7B**
(GPU, clonación y expresividad). Kokoro rinde ~6× tiempo real en CPU y carga
en ~1,7 s; Qwen3-TTS añade streaming y control emocional.

**Grado: 🟢 TOTAL** (funcionalmente). La función —texto → audio natural en una
voz elegida— se replica por completo. La **calidad** no es idéntica: Eleven v4
sigue por delante en expresividad y en arco emocional en textos largos, y
Kokoro no tiene etiquetas de audio `[laughs]`/`[whispers]` (Qwen3-TTS y
Orpheus/Chatterbox sí tienen etiquetas paralingüísticas parciales).

**Notas honestas:**
- Kokoro: el español existe, pero las voces no inglesas son más débiles y hay
  una sola voz en francés; los textos deben trocearse (~100–200 tokens por
  fragmento; más de ~400 suena apresurado).
- Qwen3-TTS 1.7B en T4 16 GB cabe (~3,4 GB de pesos + overhead); el 0.6B
  (~1,2 GB) es el plan B si la VRAM aprieta.
- Ningún modelo local ofrece 90 idiomas con calidad uniforme: Qwen3-TTS
  cubre 10–11, CosyVoice 9, Kokoro 8. El español está cubierto en los tres.
- La latencia de 75–100 ms de Flash/v4 Turbo **no** se replica en T4 con
  modelos de 1,7B: el primer audio llega en cientos de ms como mínimo; para
  narración por lotes es irrelevante, para conversación en vivo sí importa
  (ver §18).

**Endpoint FastAPI (para el agente de backend):**
```
POST /api/v1/tts
  Entrada (JSON): {
    "text": "string, 1..10000 caracteres",
    "voice_id": "string (id de voz fija o clonada)",
    "model": "kokoro | qwen3-tts-0.6b | qwen3-tts-1.7b  (por defecto: kokoro si voice fija, qwen3-tts-1.7b si clonada)",
    "language": "es | en | … (ISO 639-1, opcional; por defecto 'es')",
    "speed": 0.5..2.0 (por defecto 1.0),
    "format": "mp3 | wav (por defecto mp3)",
    "stability": 0.0..1.0 (opcional, solo qwen3),
    "style_exaggeration": 0.0..1.0 (opcional, solo qwen3)
  }
  Salida: audio binario (Content-Type audio/mpeg o audio/wav) + cabeceras
    X-Generation-Id, X-Duration-Seconds, X-Model, X-Voice-Id.
  Errores: 400 texto vacío o >10000 caracteres; 404 voice_id desconocido;
    503 modelo GPU no cargado (Kaggle apagado) con mensaje "arranca el backend GPU".
POST /api/v1/tts/stream        (mismo cuerpo; respuesta chunked / SSE con
  los primeros bytes lo antes posible; obligatorio para narraciones largas)
GET  /api/v1/tts/voices        → lista de voces disponibles (fijas + clonadas + diseño)
GET  /api/v1/models            → modelos cargados, VRAM libre, estado CPU/GPU
```

---

## 2. Text to Dialogue (diálogo multi-hablante)

**Qué hace en ElevenLabs:** varias voces en un solo audio: líneas ordenadas, cada
una con su `voice_id` (Eleven v3, hasta 10 voces), con timestamps por palabra y
por hablante. Es la función detrás de podcasts dramatizados y escenas con dos
personajes. **Precisión REA:** v4 se usa por la API de Text to Dialogue;
**v4 Turbo va por el WebSocket** de Text to Dialogue (no por el endpoint
REST). La orquestación por segmentos del clon sigue siendo la vía correcta.

**Equivalente local:** dos vías. (a) **Orquestación por segmentos:** el backend
trocea el guion por hablante y sintetiza cada línea con su voz (Qwen3-TTS o
Kokoro), luego concatena con silencios calibrados — funciona con cualquier
motor y es la vía recomendada. (b) **Dia 1.6B** (Nari Labs, Apache-2.0):
genera diálogo multi-hablante con risas/suspiros en una sola pasada.

**Grado: 🟡 PARCIAL.** La orquestación por segmentos replica el resultado
(un audio con varias voces y sus tiempos) pero no la generación en una sola
pasada ni la interacción prosódica entre hablantes (interrupciones, solapamientos).
Dia sí hace una sola pasada, pero solo en inglés y con identidad de voz
inestable sin semilla/prompt.

**Endpoint FastAPI:**
```
POST /api/v1/dialogue
  Entrada (JSON): {
    "lines": [{"speaker_voice_id": "…", "text": "…"}, …],   // máx. 10 líneas por petición
    "model": "segmented (por defecto) | dia-1.6b",
    "pause_between_lines_ms": 250 (por defecto),
    "format": "mp3 | wav"
  }
  Salida: audio binario + JSON acompañante (o cabecera X-Timings) con
    [{"speaker_voice_id", "start_ms", "end_ms", "text"}] por línea.
  Errores: 400 si >10 líneas o alguna vacía; 422 si model=dia-1.6b y el
    idioma no es inglés.
```

---

## 3. Instant Voice Cloning (IVC)

**Qué hace en ElevenLabs:** crea una copia usable de una voz a partir de una
muestra corta (la página de v4 dice que bastan **10 s** de audio; la
documentación recomienda 1–2 min de audio limpio y la página de clonación
dice que 1–5 minutos funcionan bien; muestras más largas ayudan).
Rápido, sin entrenamiento: la voz queda disponible como `voice_id` para TTS.

**Equivalente local:** **Qwen3-TTS 1.7B en modo CustomVoice** — zero-shot real
desde **3 segundos** de referencia (3–30 s recomendado), sin entrenamiento.
Alternativas: CosyVoice 3, Chatterbox (retirado, ver tabla), F5-TTS (5–15 s),
XTTS v2 (6 s, desaconsejado por cierre de Coqui).

**Grado: 🟢 TOTAL** (funcionalmente). El clon zero-shot local es, en 2026, el
área donde el open-source más se ha acercado: Qwen3-TTS y Chatterbox han
ganado o empatado pruebas ciegas contra ElevenLabs en muestras cortas, y
Fish Speech S2 superó el "test de Turing de audio" (los oyentes solo lo
identificaron como IA el 48,5 % de las veces). La fidelidad en español con
muestras de 10–30 s es buena; en frases muy largas la estabilidad del timbre
puede derivar más que en ElevenLabs.

**Notas honestas:**
- La calidad depende casi por completo de la muestra: audio limpio, sin
  música ni eco, 10–30 s, una sola persona, sin solapamientos. El backend
  debe rechazar muestras de <3 s o con SNR baja, y avisar al usuario.
- **Consentimiento:** clonar solo voces propias o con permiso explícito.
  El clon debe guardar, junto a cada voz, quién autorizó la muestra y cuándo
  (campo `consent_note`). ElevenLabs exige verificación de identidad para
  PVC; el clon local debe exigir al menos una declaración explícita del usuario.
- Qwen3-TTS no deja marca de agua en el audio; el clon debe añadir metadatos
  o un registro interno de procedencia (ver §16).

**Endpoint FastAPI:**
```
POST /api/v1/voices/instant-clone        (multipart/form-data)
  Entrada: audio (wav/mp3/flac/ogg, 3 s..2 min, ≤25 MB),
    "name": "string", "description": "string (opcional)",
    "language": "es (por defecto)", "consent_note": "string (obligatorio)"
  Salida (JSON 201): {"voice_id", "name", "model": "qwen3-tts-1.7b",
    "reference_duration_s": …, "created_at": …, "preview_url": "/api/v1/voices/{id}/preview"}
  Errores: 400 audio <3 s o >2 min / formato no soportado; 422 audio
    con más de un hablante o SNR insuficiente; 503 GPU no disponible.
GET  /api/v1/voices/{voice_id}/preview  → audio corto de prueba ("Hola, soy…")
DELETE /api/v1/voices/{voice_id}        → borra voz + referencia
```

---

## 4. Professional Voice Cloning (PVC)

**Qué hace en ElevenLabs:** clon entrenado (fine-tuning) con 30 minutos a 3 horas
de grabaciones de la propia voz, con verificación de identidad. Es el clon
más fiel; desde el 2 de noviembre de 2026 también se puede afinar (fine-tune)
un PVC sobre Eleven v4 / v4 Turbo. Limitado por plan: **1 voz en Creator y Pro, 3 en Scale, 10 en Business**.
**Desde el 2 de noviembre de 2026** el fine-tuning de un PVC sobre Eleven v4
y v4 Turbo está **abierto a todos los workspaces** (antes era limitado); se
activa desde el botón `+` junto a Eleven v4 en My Voices. Nuevo parámetro:
`clone_strength`, guardado en los ajustes de la voz (se usa cuando la petición
no fija `clone_strength` ni `use_pvc_as_ivc`). La verificación de identidad es
un **captcha de voz**: la API devuelve una imagen con líneas de texto, el
propietario las lee en voz alta y la grabación va a un endpoint de verificación
(`POST /v1/voices/pvc/{voice_id}/verification`); la verificación manual es
solo el fallback.

**Equivalente local:** no hay un equivalente directo "sube 30 min y pulsa un
botón". Las vías son: (a) **zero-shot con referencia larga** — concatenar
varios clips de referencia (Qwen3-TTS acepta multi-clip) y elegir el mejor,
que se acerca mucho sin entrenar nada; (b) **fine-tuning LoRA** del modelo
de clonación con 30+ min de audio (posible con Qwen3-TTS / CosyVoice /
F5-TTS, pero exige scripts de entrenamiento, horas de GPU T4 y evaluación
auditiva; no es una operación de un endpoint); (c) **adaptación por embedding**
— promediar embeddings de varios clips de referencia.

**Grado: 🟡 PARCIAL.** La vía (a) cubre el 80 % del caso de uso real (una voz
propia consistente para narración) sin entrenar. El fine-tuning real existe
en local, pero no es un producto: es un trabajo manual por voz, sin garantía
de superar al zero-shot y con riesgo de sobreajuste. No se promete "PVC"
como tal; se promete "clon mejorado con múltiples referencias".

**Endpoint FastAPI:**
```
POST /api/v1/voices/pro-clone            (multipart/form-data)
  Entrada: audios[] (varios ficheros, total 5..180 min, ≤500 MB),
    "name", "language", "consent_note" (obligatorio),
    "mode": "multi-reference (por defecto) | lora-finetune (manual, ver nota)"
  Salida (JSON 202, asíncrono): {"voice_id", "job_id", "status": "processing",
    "mode": "multi-reference", "estimated_minutes": …}
  Nota: mode=lora-finetune NO se ejecuta automáticamente: crea el job y
    devuelve 202 con instrucciones; el fine-tuning lo lanza un operador
    y el endpoint solo consulta el estado.
GET  /api/v1/voices/pro-clone/{job_id}  → {"status", "progress", "voice_id"|null, "error"|null}
```

---

## 5. Voice Library (biblioteca de voces)

**Qué hace en ElevenLabs:** catálogo de miles de voces listas para usar
(**10.000+ voces**; la cifra «17.500+ voces en 90+ idiomas» que daba este
mapa en v1 **no se pudo verificar** en ninguna fuente consultada: usar
10.000+ hasta que el navegador vivo lea la cifra de la web), buscables por
idioma, acento, edad y estilo, incluidas voces de la comunidad con reparto de
ingresos para sus creadores. Es un marketplace con licencias, no solo una
lista de archivos. **Añadido REA:** existe el **Voice Marketplace** (mayo
2026): los creadores suben PVC, fijan términos de licencia (casos de uso,
niveles de precio, preaviso de hasta 2 años) y cobran royalties por
generación. Endpoints de descubrimiento: `GET /v2/voices`,
`GET /v1/shared-voices`, `POST /v1/similar-voices` (ver §38).

**Equivalente local:** ninguno en cuanto a catálogo. Lo replicable es la
**cáscara**: una biblioteca propia con las 54 voces fijas de Kokoro, las voces
diseñadas con Qwen3-TTS y las clonadas por los 2 usuarios, con búsqueda por
etiquetas (idioma, sexo, edad aproximada, estilo) y favoritos. Eso es una
biblioteca de decenas de voces, no de miles.

**Grado: 🔴 NO REPLICABLE.** El valor de la Voice Library es el catálogo
mismo: miles de voces reales con licencia, verificación y reparto de ingresos.
No se puede descargar ni reproducir legalmente; cada voz pertenece a alguien.
Tampoco existe un corpus libre equivalente con esa escala y esa curaduría.
La biblioteca propia cubre el uso de 2 personas, pero no es "la Voice Library".

**Endpoint FastAPI (solo para la biblioteca propia):**
```
GET  /api/v1/library/voices?language=es&tag=narracion&q=…
  → [{"voice_id", "name", "source": "kokoro | designed | cloned",
       "language", "tags": […], "preview_url": …}]
POST /api/v1/library/voices/{voice_id}/favorite   → {"favorite": true}
```
*(Sin endpoint de "subir una voz a la comunidad": no hay comunidad.)*

---

## 6. Voice Design (diseñar una voz desde texto)

**Qué hace en ElevenLabs:** describes una voz en texto (20–1.000 caracteres:
edad, sexo, acento, tono) y genera vistas previas para elegir una. Sin muestras de audio. Modelo en API:
`eleven_ttv_v3` (antes `eleven_multilingual_ttv_v2`). **Discrepancia
abierta:** este mapa dice 3 vistas previas; una guía de la API de mayo de 2026
dice 5 variantes. Número no verificado; queda para el navegador vivo
(Apéndice D).

**Equivalente local:** **Qwen3-TTS 1.7B en modo VoiceDesign** (describe la voz
y genera una nueva) y **VoxCPM2** (diseño de voz desde descripción, 30 idiomas).
Ambos son Apache-2.0. CosyVoice 3 también admite control por instrucciones
de estilo/emoción.

**Grado: 🟢 TOTAL** (funcionalmente). La función —texto → voz nueva inexistente—
existe en local. La variedad y la precisión del control (p. ej. acentos
regionales concretos del español) son menores que en ElevenLabs, y el número
de previsualizaciones conviene limitarlo a 3 por coherencia con el original.

**Endpoint FastAPI:**
```
POST /api/v1/voices/design
  Entrada (JSON): {"prompt": "Voz femenina, 30 años, acento neutro, cálida… (20..1000 caracteres)",
    "language": "es", "num_previews": 3 (por defecto, máx. 3)}
  Salida (JSON 201): {"candidates": [{"candidate_id", "preview_url", "description"}, …]}
POST /api/v1/voices/design/{candidate_id}/save
  Entrada: {"name": "…"} → Salida: {"voice_id", "name", "source": "designed"}
```

---

## 7. Voice Remix (remezclar una voz creada)

**Qué hace en ElevenLabs:** cambia una voz ya creada (acento, edad, tono,
ritmo) manteniendo su identidad base, con previsualización antes de guardar.

**Equivalente local:** no hay un modelo "remix" como tal. Se emula con tres
operaciones combinadas: (a) ajuste DSP (tono/velocidad con `librosa`/`sox`),
(b) regeneración con la misma referencia y distintos parámetros de estilo/
estabilidad del clonador, y (c) Voice Design con un prompt derivado de la
voz original ("como X pero más grave y más lenta").

**Grado: 🟡 PARCIAL.** Los cambios de ritmo y tono son triviales; los de edad
o acento son aproximados y pueden romper la identidad de la voz. No se
promete "misma voz, 10 años mayor" con fidelidad.

**Endpoint FastAPI:**
```
POST /api/v1/voices/{voice_id}/remix
  Entrada (JSON): {"pitch_semitones": -4..+4, "speed": 0.8..1.2,
    "style_prompt": "string (opcional, p. ej. 'más grave')"}
  Salida: {"candidate_id", "preview_url"}  (luego POST …/save como en §6)
```

---

## 8. Speech to Speech / Voice Changer

**Qué hace en ElevenLabs:** graba o sube tu voz y la re-emite en otra voz
manteniendo la interpretación: emoción, cadencia, acento, susurros, risas
y matices. No es TTS (no hay texto de por medio): es conversión de voz.

**Equivalente local:** conversión de voz (voice conversion) con **OpenVoice v2**
(MIT, clonación zero-shot + control de emoción/tono) o **kNN-VC** (conversión
por vecinos más cercanos, ligera, buena para cambiar el timbre manteniendo
la prosodia). Vía alternativa en dos pasos: STT (Whisper) → TTS clonado,
que conserva el contenido pero **pierde** la interpretación original
(es la vía fácil y la menos fiel; debe etiquetarse como tal en la UI).

**Grado: 🟡 PARCIAL.** La conversión de voz local funciona y mantiene la
prosodia mejor que el rodeo STT→TTS, pero la calidad y la similitud del
timbre están por debajo de ElevenLabs, sobre todo en susurros/risas y en
audios largos. OpenVoice v2 es el candidato principal; kNN-VC el plan B
ligero. Latencia: no en tiempo real en T4.

**Endpoint FastAPI:**
```
POST /api/v1/speech-to-speech          (multipart/form-data)
  Entrada: audio (wav/mp3, ≤10 min), "target_voice_id",
    "method": "stt-tts (por defecto) | voice-conversion (501, no implementado)"
  Salida: audio binario + X-Method usada + cabecera X-Transcribed-Text-B64
    (transcripción original en base64 UTF-8; el frontend aún no la consume).
  Errores: 400 audio >10 min; 404 voz destino desconocida; 503 GPU no disponible.
```

---

## 9. Dubbing (doblaje / traducción de vídeo)

**Qué hace en ElevenLabs:** traduce y re-dobla audio o vídeo a otro idioma
manteniendo la voz y la interpretación del hablante original. **Dos
productos excluyentes, no uno:** (a) **Dubbing v2 automático** (por defecto,
etiquetado **alfa** en la documentación; edición de transcripción/traducción y
regeneración en la app; por API solo Enterprise) y (b) **Dubbing Studio v1**
(legacy, **solo mantenimiento**, corrección de errores críticos; edición por
clip, reasignación de hablantes, exportación AAF/SRT/CSV). Un doblaje
automático **no se puede convertir** en proyecto de Dubbing Studio. Dubbing
v2 cubre 90+ idiomas con dialectos regionales (inglés US/UK/AU/CA, español
ES/MX/AR/CL, francés FR/CA, portugués BR/PT, árabe EG, chino TW) y trabaja
**desde el audio original, no desde una transcripción**, y así transfiere tono
y emoción entre idiomas. En la web acepta archivos o enlaces de
YouTube/TikTok. **Límites en disputa:** 1 GB y 180 min (resumen de la
documentación), 2 GB y 180 min (artículo de ayuda) o 3 GB por archivo por API
(documentación de la API); Dubbing Studio v1: 1 GB y 45 min. **Coste:** las
tarifas 2.000–10.000 créditos/min son de **v1** (automático con/sin marca de
agua 2.000/3.000; Studio 5.000/10.000); **Dubbing v2 se cobra por API a
$2,20/min** de origen; en la app, una prueba práctica midió ~13.500 créditos
por minuto de vídeo y por idioma. El endpoint del clon debe modelar la ruta
v2 (la vigente) y no prometer la edición fina de v1.

**Equivalente local:** pipeline por piezas, todo con software libre:
transcripción + diarización (WhisperX + pyannote) → traducción
(MADLAD-400, Apache-2.0) → TTS clonado en el idioma destino (Qwen3-TTS,
clonación cross-lingual) → mezcla con el audio original atenuado de fondo
(`ffmpeg`) y re-muxado con el vídeo. Es el pipeline que ya implementan
proyectos como OmniVoice Studio (código abierto).

**Grado: 🟡 PARCIAL.** El pipeline completo es construible y el resultado es
utilizable, pero con límites claros: (a) idiomas reales: ~10 con buena
calidad (Qwen3-TTS) frente a 90+; (b) la transferencia de emoción/ritmo
entre idiomas es parcial — el TTS clonado cross-lingual mantiene el timbre,
no la interpretación exacta; (c) **no hay sincronización labial** (ElevenLabs
tampoco la tiene en Dubbing v2, según las reseñas; no prometerla); (d) los
tiempos: un vídeo de 10 min puede tardar varios minutos en T4; (e) la
traducción automática ES↔EN es buena, pero ES→idiomas poco representados
degrada el resultado.

**Endpoint FastAPI:**
```
POST /api/v1/dubbing                   (multipart/form-data, asíncrono)
  Entrada: media (audio o vídeo, ≤500 MB en este clon, ≤180 min; el límite
real de ElevenLabs está en disputa: 1 GB / 2 GB / 3 GB según la fuente),
    "source_language": "auto | es | …", "target_languages": ["en", …] (máx. 3 por job),
    "voice_mode": "clone-original (por defecto) | fixed-voice-id",
    "keep_background_audio": true|false
  Salida (JSON 202): {"job_id", "status": "queued", "stages": ["transcribe","translate","synthesize","mix"]}
GET  /api/v1/dubbing/{job_id}         → {"status", "stage", "progress",
    "segments": [{"start_ms","end_ms","source_text","translated_text","status"}]}
POST /api/v1/dubbing/{job_id}/segments/{n}/edit
  Entrada: {"translated_text": "…"} → re-sintetiza solo ese segmento
GET  /api/v1/dubbing/{job_id}/download?language=en&format=mp4
  → vídeo doblado en MP4 (o audio si la entrada era audio). La exportación de
audio separado en Dubbing v2 no está verificada (una prueba práctica solo
pudo descargar MP4; el changelog del 19 oct 2026 añade subtítulos traducidos
como WebVTT)
```

---

## 10. Speech to Text — Scribe (transcripción)

**Qué hace en ElevenLabs:** **Scribe v3** (`scribe_v3`) y **Scribe v3 Live** (`scribe_v3_live`),
lanzados el **9–10 de noviembre de 2026**, son los modelos vigentes (v2 y v2
Realtime siguen disponibles). 27 % menos de errores de palabra que v2 en 102
idiomas, según ElevenLabs (FLEURS); diarización −12 % en general y −17 % con
3+ hablantes; v3 Live: 43 % menos WER semántico y 31 % menos WER que v2
Realtime, con diarización en vivo por primera vez. Timestamps por palabra,
detección de entidades y prompting con hasta 1.000 términos clave en lote y
**biblioteca de keyterms de hasta 10.000 términos** en Live. Parámetros
nuevos: `numbers_format` (dígitos o palabras), `secondary_language_codes`
(audio que mezcla idiomas), `commit_strategy=turn_prediction`,
`multilang_mode` (cada idioma en su propio alfabeto) y redacción de entidades
en tiempo real (`entity_redaction`). **«Hasta 32 hablantes etiquetados» no
está verificado** (solo consta en este mapa). Existe además **Scribe v2
Medical** (clínico, por lotes) y **Scribe v3 Live Medical** (tiempo real,
para agentes de salud) como modelos aparte (sub-función de este §10, sin
sección propia). Precio por API (17 nov 2026): **$0,20/hora por lotes y $0,22/hora en
tiempo real** (antes $0,22/$0,39); en la app sigue siendo 330 créditos/min.

**Equivalente local:** **faster-whisper** (large-v3, ~100 idiomas, MIT) +
**WhisperX** (alineación por palabra con wav2vec2 + diarización con
pyannote, hasta N hablantes) + prompting de términos clave (faster-whisper
admite `initial_prompt` y lista de palabras). Para tiempo real, el
streaming de faster-whisper con VAD existe pero con latencia de segundos,
no de 150 ms.

**Grado: 🟢 TOTAL** (funcionalmente; en lotes). Transcribir con timestamps
por palabra, diarización y términos clave se replica por completo. La
precisión bruta de Scribe v3 es superior (27 % menos de errores según el
fabricante, sin verificación independiente a fecha de este mapa), sobre
todo en nombres propios y jerga; Whisper large-v3 queda cerca pero no
igual. La versión **en vivo** es parcial (ver nota).

**Notas honestas:**
- La diarización con pyannote exige aceptar las condiciones de sus modelos
  en Hugging Face y descargar ~500 MB; es el único paso con fricción legal.
- Scribe Medical no tiene equivalente local directo: Whisper transcribe
  terminología médica razonablemente, pero sin modelo clínico dedicado.
- large-v3 en T4 va sobrado; en CPU es lento (mejor `small`/`medium` en CPU).

**Endpoint FastAPI:**
```
POST /api/v1/stt                       (multipart/form-data)
  Entrada: audio o vídeo (cualquier formato común),
    "language": "auto | es | …", "model": "small | medium | large-v3 (por defecto large-v3 en GPU)",
    "diarize": true|false (por defecto true),
    "word_timestamps": true|false (por defecto true),
    "keyterms": ["término1", …] (máx. 1000, opcional),
    "output_format": "json | srt | vtt | txt"
  Salida (JSON): {"language", "duration_s",
    "segments": [{"start", "end", "speaker": "SPEAKER_00"|null,
       "text": "…", "words": [{"word","start","end"}]}]}
  Errores: 400 formato no soportado; 413 archivo >2 GB.
POST /api/v1/stt/stream                (WebSocket; audio en chunks → transcripción
  parcial en vivo; latencia de segundos, documentar como tal)
```

---

## 11. Sound Effects (efectos de sonido por texto)

**Qué hace en ElevenLabs:** genera efectos de sonido, ambientes y pistas
instrumentales cortas desde una descripción en texto (modelo **SFX v3** (`eleven_text_to_sound_v3`), lanzado el **29 de octubre
de 2026** y modelo por defecto en ElevenCreative, Studio y Flows desde el
**2 de noviembre de 2026**; maneja varios sonidos en un mismo prompt, mejor
música y voces, menos clipping en agudos). Duración **0,5–30 s** (auto si no
se fija); prompt de hasta **450 caracteres en la app**; `prompt_influence`
0–1 (por defecto 0,3); hasta 4 variantes por generación (según una reseña).
**Loop en disputa:** el changelog del 2 nov lista `"loop": true` entre las
opciones de v3, pero el blog de desarrollo dice que el loop sigue necesitando
v2 — queda para el navegador vivo (Apéndice D). **SFX v2 está deprecated y se
retira el 1 de marzo de 2027**: el clon no debe tomarlo como referencia.
Coste: 200 créditos por generación en app (40 créditos/s si se fija la
duración); API $0,12/min. Concurrencia propia desde el 9 nov: 4 en
Free/Starter, 6 en Creator/Pro, 8 en Scale/Business.

**Equivalente local:** **Stable Audio Open 1.0** (hasta 47 s, estéreo 44,1 kHz,
licencia comunitaria gratuita <1 M$) como primario; **AudioLDM2** como
alternativa (CC-BY-NC-SA, solo no comercial); **Bark** (Suno, MIT) para
efectos no verbales y risas/llantos, con calidad inferior para SFX puros.

**Grado: 🟡 PARCIAL.** Se generan efectos y ambientes utilizables, pero la
adherencia al prompt y la limpieza del sonido están por debajo de SFX v3,
y la duración máxima (47 s) y la lentitud de la difusión en T4 (decenas de
segundos por clip) limitan el uso. No hay "música y voces" en un mismo
prompt con la calidad de ElevenLabs.

**Endpoint FastAPI:**
```
POST /api/v1/sfx
  Entrada (JSON): {"prompt": "Puerta de madera que chirría, lluvia de fondo…",
    "duration_s": 1..47 (por defecto 10), "num_variants": 1..3,
    "model": "stable-audio-open-1.0 (por defecto)"}
  Salida: audio binario (o JSON con URLs si num_variants > 1).
  Errores: 400 prompt vacío o duración fuera de rango; 503 GPU no disponible.
```

---

## 12. Music (generación de música)

**Qué hace en ElevenLabs:** Eleven Music **v2.5** (`music_v2_5`), lanzado el **11 de septiembre de
2026** (mejor calidad y adherencia al prompt que v2; preferido en la mayoría
de 47.885 pares en prueba ciega del fabricante), genera canciones e
instrumentales desde un prompt, con o sin voces, género/estado de ánimo/
estructura configurables y regeneración de secciones concretas. Pistas de
**3 s a 5 min** por generación (el plan de composición admite hasta 10 min en
total); formatos MP3 44,1 kHz (128–192 kbps) o WAV. Uso comercial incluido
desde el plan Starter. **Music v1 está deprecated y se retira el 31 de enero
de 2027.** Sub-funciones: **planes de composición** (`POST /v1/music/plan`:
expande un prompt a un plan JSON editable, hasta 30 secciones de 3–120 s, con
letra, estilos positivos/negativos y adherencia al contexto),
**inpainting** (regenerar una sola sección sin tocar el resto,
`store_for_inpainting=true`), **separación de stems**
(`POST /v1/music/stem-separation`, 2 o 6 stems, devuelve ZIP),
**Audio Reference** (~30 s de audio como referencia de sonido),
**Music Finetunes** (entrenar una variante privada de estilo con audio
propio, $1,50 cada una, `/v1/music/finetunes`) y **Video to Music /
Instant Soundtracks** (`POST /v1/music/video-to-music`, 19 oct 2026: hasta
10 vídeos, 200 MB combinados, 600 s en total; descripción opcional (<1.000
caracteres) y hasta 10 etiquetas de estilo; `use_audio_as_reference`,
`add_sfx`, `separate_tracks`; en la app se llama Instant Soundtracks desde
el 15 oct 2026 y musicaliza un vídeo subido colocando efectos en los
timestamps correspondientes, en capas separadas; a 26 oct 2026 era solo API,
sin botón en la app web — no verificado del todo). Desde el 6 nov 2026 se
puede publicar directamente en SoundCloud desde ElevenMusic. `sign_with_c2pa`
firma los MP3 con credenciales de contenido; Zero Retention Mode
(`enable_logging=false`) solo Enterprise. Coste: API $0,15/min; app 900
créditos/min.

**Equivalente local:** **ACE-Step 1.5** (Apache-2.0, canciones completas con
voces y letra, hasta 10 min, ~4 GB VRAM) como primario para canciones;
**MusicGen-small** (Meta, 300M, ~3 GB VRAM) para instrumentales cortos
(~30 s) con la advertencia de licencia CC-BY-NC; **Stable Audio Open**
para loops/ambientes instrumentales (ver §11).

**Grado: 🟡 PARCIAL.** Se genera música instrumental y canciones con voz
utilizables, pero la calidad de composición, la coherencia estructural en
piezas largas y la mezcla están por debajo de Music v2.5, y la generación
es lenta en T4 (una canción de 2–3 min puede tardar varios minutos). El
listón real incluye planes de composición, inpainting, stems y Video to Music:
el clon cubre la generación básica, no el pipeline de edición.
"Instant Soundtracks" (música sincronizada a un vídeo) no existe en local:
se emula generando la pista y alineándola a mano en el editor (§14).

**Endpoint FastAPI:**
```
POST /api/v1/music
  Entrada (JSON): {"prompt": "Balada pop nostálgica, piano y cuerdas…",
    "lyrics": "string (opcional, solo ACE-Step)",
    "duration_s": 10..180, "instrumental": true|false,
    "model": "ace-step-1.5 (por defecto) | musicgen-small"}
  Salida (JSON 202, asíncrono): {"job_id", "status": "processing"}
GET  /api/v1/music/{job_id}           → {"status", "audio_url"|null, "duration_s"|null}
```

---

## 13. Voice Isolator (aislamiento de voz)

**Qué hace en ElevenLabs:** elimina ruido de fondo, sonidos de calle y música
de una grabación y deja solo la voz. Acepta WAV/MP3/FLAC/OGG/AAC y también
vídeo.

**Equivalente local:** **Demucs** (`htdemucs`, MIT) — separa voz de música/
ruido; para ruido no musical, **noisereduce** o **DeepFilterNet** (ruido
ambiental y reverberación). En la práctica: Demucs para música de fondo,
DeepFilterNet para ruido de calle/oficina.

**Grado: 🟢 TOTAL** (funcionalmente). La separación de voz es un problema
resuelto en open-source y Demucs es el estándar. La calidad es comparable;
ElevenLabs puede ser algo más limpio en casos extremos (música alta con
voz baja), pero la diferencia no cambia el caso de uso: limpiar una muestra
antes de clonar o transcribir.

**Endpoint FastAPI:**
```
POST /api/v1/isolate                  (multipart/form-data)
  Entrada: audio o vídeo, "mode": "demucs (por defecto) | denoise",
    "keep_background": false (si true, devuelve también la pista de fondo)
  Salida: audio WAV/MP3 limpio (+ opcionalmente "background_url").
```

---

## 14. Studio / Projects (proyectos de formato largo)

**Qué hace en ElevenLabs:** Studio es hoy un **editor de línea de tiempo multimedia** (voz, música,
efectos, subtítulos **y vídeo**), con importación de documentos y exportación
MP3/WAV (Pro+: WAV 16-bit 44,1 kHz; Creator+: sin marca de agua de vídeo).
Proyectos con capítulos, asignación de voces por párrafo, control de ritmo,
regeneración de fragmentos y diccionarios de pronunciación. Límites por plan:
3 proyectos en Free, 20 en Starter. **Desde la actualización del 2 de
noviembre de 2026, Studio recomienda Eleven v4** en los ajustes de proyecto
(antes Multilingual v2). Existe además el endpoint
**`POST /v1/studio/podcasts`** (crear podcast; ver §29). El clon de
«capítulos + regeneración» sigue siendo parcial, pero el listón real es más
alto que el descrito aquí en v1.

**Equivalente local:** no hay un "Studio" open-source equivalente listo para
usar; se **construye** con piezas que ya existen: el frontend (GitHub Pages)
implementa capítulos/párrafos/voces por párrafo; el backend trocea el texto,
sintetiza por fragmentos con caché (mismo texto + misma voz = mismo audio),
permite regenerar un fragmento y exporta el proyecto completo (MP3/WAV
concatenado + SRT). Es trabajo de aplicación, no de modelo.

**Grado: 🟡 PARCIAL.** El flujo completo (escribir → asignar voces → generar
por capítulos → exportar) se replica. Lo que no se replica es el pulido del
editor de ElevenLabs (ondas por fragmento, ajustes finos de pausa/énfasis
en la UI, colaboración en equipo) ni su estabilidad probada con libros de
10 horas. Para 2 usuarios y proyectos de duración moderada, el clon cubre
el caso de uso.

**Endpoints FastAPI:**
```
POST /api/v1/projects
  Entrada: {"title": "…"} → {"project_id", "title", "created_at"}
GET  /api/v1/projects                  → lista de proyectos
GET  /api/v1/projects/{id}            → proyecto con capítulos y párrafos
POST /api/v1/projects/{id}/chapters   → {"chapter_id", "title"}
POST /api/v1/projects/{id}/chapters/{cid}/paragraphs
  Entrada: {"text": "…", "voice_id": "…", "speed": 1.0} → {"paragraph_id", "status": "pending"}
POST /api/v1/projects/{id}/generate   → 202 {"job_id"} (sintetiza párrafos pendientes con caché)
POST /api/v1/projects/{id}/paragraphs/{pid}/regenerate → 202 (regenera solo ese fragmento)
GET  /api/v1/projects/{id}/export?format=mp3|wav|srt
  → audio completo concatenado (o subtítulos); cabecera X-Duration-Seconds
DELETE /api/v1/projects/{id}
```

---

## 15. Diccionario de pronunciación

**Qué hace en ElevenLabs:** reglas de pronunciación personalizadas (palabra →
cómo debe sonar), en formato PLS o por reglas, aplicables a TTS, Studio y
ElevenReader. Sirve para nombres propios, siglas y neologismos.

**Equivalente local:** sustitución de texto antes de sintetizar + fonemas.
Vía simple y robusta: el backend guarda reglas (palabra → reemplazo
ortográfico/fonético) y las aplica al texto en el pre-procesado de TTS;
vía avanzada: `espeak-ng`/fonemas IPA en el pipeline de Kokoro y
`phonemizer` para Qwen3-TTS. El estándar PLS (XML) se importa/exporta
para compatibilidad.

**Grado: 🟢 TOTAL.** Es una función de aplicación, no de modelo, y se replica
por completo. La única diferencia: ElevenLabs aplica el diccionario dentro
de su modelo; en local se aplica antes, con el mismo efecto audible en la
inmensa mayoría de casos (nombres y siglas).

**Endpoint FastAPI:**
```
POST /api/v1/pronunciation
  Entrada: {"word": "Valdestudio", "replacement": "bal-des-TU-dio",
    "phonetic": "baldesˈtuðjo (opcional, IPA)", "language": "es"}
  → {"rule_id", …}
GET  /api/v1/pronunciation?language=es → lista de reglas
PUT  /api/v1/pronunciation/{rule_id}  → actualiza una regla
DELETE /api/v1/pronunciation/{rule_id}
POST /api/v1/pronunciation/import     (multipart, fichero .pls XML)
GET  /api/v1/pronunciation/export     → fichero .pls
```
*(El TTS de §1 acepta `"dictionary_id"` opcional para aplicar un diccionario
concreto a esa generación.)*

---

## 16. History (historial de generaciones)

**Qué hace en ElevenLabs:** lista todas las generaciones (texto, voz, modelo,
fecha), permite escucharlas, descargarlas y borrarlas; es el registro de
uso y la base de la facturación por caracteres.

**Equivalente local:** tabla en base de datos local (SQLite/PostgreSQL) +
almacenamiento de los audios generados, con metadatos completos.

**Grado: 🟢 TOTAL.** Es una función de aplicación trivial en local y, de
hecho, mejorable: el clon puede guardar el texto exacto, la muestra de
referencia usada, el modelo y la semilla, cosa que facilita reproducir
cualquier generación — algo que ElevenLabs no garantiza.

**Endpoint FastAPI:**
```
GET  /api/v1/history?voice_id=…&from=2026-11-01&limit=50&offset=0
  → {"total": …, "items": [{"id", "created_at", "type": "tts|dialogue|sfx|music|dubbing",
       "text", "voice_id", "model", "duration_s", "characters", "audio_url"}]}
GET  /api/v1/history/{id}/audio      → audio original generado
DELETE /api/v1/history/{id}          → borra registro + audio
GET  /api/v1/usage                   → {"total_characters", "total_minutes",
  "by_model": {…}, "by_voice": {…}} (equivalente local del contador de créditos)
```

---

## 17. API (ElevenAPI: acceso programático)

**Qué hace en ElevenLabs:** API REST + WebSocket con SDKs oficiales de Python
y TypeScript, CLI y MCP. Expone TTS (síncrono y streaming), Text to Dialogue,
Speech to Speech, clonación, doblaje, SFX, aislamiento, Scribe, música,
agentes y colecciones de voces. Autenticación por `xi-api-key`, con
facturación por uso. **Precisión REA:** el spec público tiene **258 endpoints
en 25 grupos** (espejo del OpenAPI; un catálogo validado contra la API real
lista 126 — la diferencia es versión del spec y agrupación, no funciones
ausentes). MCP hospedado disponible en Claude desde agosto de 2026. SDKs en
v2.79.0 (nov 2026).

**Equivalente local:** **la propia API del clon** (FastAPI, OpenAPI/Swagger
automático). No se replica la API de ElevenLabs como tal (no tiene sentido
imitar sus rutas ni su autenticación de pago), sino su **función**: que
cualquier programa pueda llamar a las funciones del clon. Se recomienda
adoptar la **compatibilidad parcial con la API de OpenAI** (`/v1/audio/speech`,
estilo Kokoro-FastAPI) para TTS, porque muchos clientes ya hablan ese
dialecto; el resto de funciones usa rutas propias (`/api/v1/…`, ver cada
sección).

**Grado: 🟢 TOTAL** (como API propia; no como clon de la API de ElevenLabs).
La cobertura funcional —todos los servicios del clon accesibles por HTTP—
se replica. Lo que no existe es el ecosistema (SDKs oficiales, MCP,
facturación por uso, alta disponibilidad).

**Endpoints FastAPI (contrato base):**
```
GET  /api/v1/health                   → {"status": "ok", "gpu": true|false, "models_loaded": […]}
GET  /api/openapi.json  |  GET /docs  → especificación OpenAPI y Swagger UI
POST /api/v1/audio/speech             → compatibilidad OpenAI (TTS simple:
  {"model": "kokoro|qwen3-tts", "input": "…", "voice": "…", "response_format": "mp3"})
Autenticación: token fijo en cabecera Authorization: Bearer <token-local>
  (2 usuarios; sin facturación, sin cuotas de pago; con límite opcional
  de caracteres/día por usuario para no saturar la T4).
Streaming: TTS y STT por WebSocket (ver §1 y §10).
```

---

## 18. Conversational AI / ElevenAgents (agentes de voz)

**Qué hace en ElevenLabs:** constructor de agentes de voz conversacionales
(soporte, ventas, asistentes) con ASR + LLM a elegir (GPT, Claude, Gemini,
etc.) + TTS de baja latencia, turn-taking, herramientas (webhooks, MCP,
transferencia de llamada), telefonía y web, workflows, guardrails, analítica
y pruebas simuladas. Desde el 5 de octubre de 2026 los agentes nuevos usan
Eleven v4 Turbo por defecto. Es el producto empresarial de la compañía («55 % de sus ingresos», según una
reseña de noviembre de 2026 — **cifra no verificada** por ninguna fuente
consultada). **Añadido REA (changelog nov 2026):** **Campaign Manager**
(9 nov 2026, ver §30), **Reception** (6 oct 2026, ver §31), **Architect**
(6 oct 2026, ver §32), **Unity SDK** (5 nov 2026, ver §33), **Eleven
Realtime** como modo de voz del agente (ver §19), **Workflows as code**
(9 nov 2026, SDK v2.77.0), **herramientas en código** (17 nov 2026, SDK
v2.79.0) y **39 herramientas MCP hospedadas**, **Analysis Items API**
(`/v1/convai/analysis-items`), **guardrails** fuera de alfa (19 oct 2026,
GA), **colas de espera** por concurrencia, **DTMF** y **timeouts del lado del
servidor desde el 26 nov 2026** (HTTP 504). LLM por defecto en agentes nuevos:
`gemini-3.5-flash`; añadidos `gpt-6.1-terra` y **Nemotron 3.5 Super VL**
(NVIDIA, 11 nov 2026); Claude Sonnet 4.5 deprecated el 30 nov (reemplazo:
Sonnet 4.6). **Preview (11 nov 2026, no lanzados):** **Interaction Engine**
(turn-taking, interrupciones, selección de modelo), **Memory** (contexto entre
conversaciones) y **Routines** (trabajo multi-paso antes/durante/después de la
conversación) — ver §34.

**Equivalente local:** pipeline por piezas: STT en streaming (faster-whisper)
→ LLM local o por API gratuita (según el proyecto; en local, un modelo
pequeño como Qwen3-8B en T4, o el LLM que ya use el usuario) → TTS en
streaming (Qwen3-TTS / CosyVoice 3, ~150 ms por chunk) → WebSocket al
navegador. Herramientas vía function-calling del LLM y webhooks FastAPI.
Sin telefonía (no hay número ni SIP en presupuesto cero).

**Grado: 🟡 PARCIAL.** Un agente de voz que conversa por web **sí** se puede
montar, y para 2 usuarios es suficiente. Pero la latencia total del pipeline
local (STT + LLM + TTS en T4) es de **segundos**, no de los ~100 ms de
ElevenAgents; la interrupción natural (barge-in) y el turn-taking fino son
mucho más toscos; y no hay telefonía, ni panel de analítica, ni guardrails
empresariales, ni 30+ LLMs a elegir. Es un agente funcional, no un producto
empresarial.

**Endpoint FastAPI:**
```
POST /api/v1/agents
  Entrada: {"name": "…", "system_prompt": "…", "voice_id": "…",
    "llm": "local-qwen3-8b | …", "tools": [{"name", "webhook_url"}]}
  → {"agent_id", …}
WS   /api/v1/agents/{agent_id}/talk   (WebSocket bidireccional:
  cliente envía audio en chunks → servidor responde audio + texto;
  mensajes: {"type": "audio_chunk"|"text"|"interrupt", "data": …})
GET  /api/v1/agents/{agent_id}/conversations → historial de conversaciones
```

---

## 19. Eleven Realtime (modelos voz a voz en un solo modelo)

**Qué hace en ElevenLabs:** lanzado el 20 de octubre de 2026, dos modelos
speech-to-speech (v1 Mini, de bajo coste; v1 Max, para soporte y tareas
con herramientas) que hacen **toda** la conversación en un solo modelo,
sin pasos separados de STT → LLM → TTS. 90+ idiomas, API Realtime
compatible con la especificación de OpenAI (solo WebSocket). IDs:
`eleven_realtime_v1_mini` (por defecto) y `eleven_realtime_v1_max`;
despliegue gradual completado el 2 nov 2026 (todos los workspaces); las
sesiones de audio inactivas se cierran a los 3 min (antes 60 s); grupos de
conversación (`/v1/convai/realtime/conversation-groups`); secreto de cliente
(`POST /v1/convai/realtime/client-secret`).

**Equivalente local:** no hay equivalente en este proyecto. Los modelos
voz a voz open-source existen en investigación (p. ej. Moshi de Kyutai,
modelos de diálogo full-duplex), pero no con la calidad, la estabilidad ni
la latencia de Realtime v1, y mucho menos corriendo en una T4 de 16 GB
bajo demanda con presupuesto cero. El pipeline por piezas del §18 es el
sustituto honesto, y es más lento y menos natural en las interrupciones.

**Grado: 🔴 NO REPLICABLE** (en las condiciones de este proyecto: T4
bajo demanda, presupuesto cero, 2 usuarios). No se incluye endpoint:
cualquier intento de "realtime local" con el hardware disponible sería
una promesa falsa. Si en el futuro el proyecto dispone de GPU dedicada,
re-evaluar Moshi / modelos S2S abiertos.

---

## 20. Realtime Translation (traducción de voz en vivo)

**Qué hace en ElevenLabs:** traducción de voz en directo en 90+ idiomas con
una voz consistente durante la sesión. Lanzada en alfa el 21 de octubre de
2026, solo para clientes Enterprise vía ElevenAPI.

**Equivalente local:** ninguno en vivo. La traducción por lotes sí existe
(ver §9, Dubbing), pero la traducción simultánea con latencia de
conversación exige streaming STT → traducción → TTS en tiempo real, que
en T4 no alcanza la latencia necesaria y acumula errores en cadena.

**Grado: 🔴 NO REPLICABLE.** Ni siquiera está disponible de forma general
en ElevenLabs (alfa Enterprise). Queda fuera del clon; el sustituto es el
doblaje por lotes del §9.

---

## 21. ElevenReader (app de lectura en voz alta)

**Qué hace en ElevenLabs:** app (iOS/Android/web) que convierte libros,
PDFs, ePubs, documentos y enlaces de artículos en audio con más de 1.000 voces, resaltado de texto, velocidad 0,25×–4×, modo
offline, temporizador de sueño, marcadores y diccionario de pronunciación.
**Idiomas:** la documentación (3 oct 2026) lista **32 idiomas**; las páginas
de marketing dicen 90+. **Planes propios**, separados de la suscripción de
ElevenLabs: Free 10 h/mes de texto a audio; **Ultra $11/mes ($8,25 anual)**
con texto a audio ilimitado, 20 h/mes de audiolibros premium, descargas
offline y voces personalizadas. **Catálogo: 200.000+ audiolibros y eBooks
premium** (mayo 2026), incluidos títulos narrados por humanos. Añadidos:
sincronización web/móvil, extensión de Chrome, importación inteligente
(Ultra, ignora encabezados/pies), GenFM, escaneo de páginas con cámara,
límites offline (20 h/día, 150 h/mes).

**Equivalente local:** la función central —**subir un documento y escucharlo**—
se replica como una página del clon: extracción de texto (PDF/ePub con
`pypdf`/`ebooklib`), troceado en capítulos, TTS con la voz elegida,
resaltado sincronizado (con los timestamps por palabra del §24) y control
de velocidad en el reproductor HTML5. No hay app móvil nativa, ni sincronización entre dispositivos, ni catálogo
de audiolibros. **Corrección de contenido (v2, importante): la documentación
de ElevenReader establece que el audio NO se puede exportar ni usar
comercialmente. La descarga del audio como MP3 que este mapa proponía en v1
como «equivalente práctico» NO es equivalente a la función real (escuchar
dentro de la app, con sincronización y offline interno): es una función
distinta, la exportación, que pertenece a Studio (§14). El clon puede
replicar «subir un documento y escucharlo», pero no debe presentar la
descarga de MP3 como la misma función.**

**Grado: 🟡 PARCIAL.** La lectura en voz alta de tus documentos funciona;
la app móvil, la sincronización entre dispositivos y el catálogo de libros
no se replican.

**Endpoint FastAPI:**
```
POST /api/v1/reader/upload             (multipart: pdf | epub | txt | docx)
  → {"document_id", "title", "chapters": n, "total_characters": …}
POST /api/v1/reader/{document_id}/generate
  Entrada: {"voice_id": "…", "speed": 1.0} → 202 {"job_id"}
GET  /api/v1/reader/{document_id}/audio?chapter=n → MP3 del capítulo
GET  /api/v1/reader/{document_id}/timings?chapter=n → palabras con tiempos (resaltado)
```

---

## 22. ElevenAI (dictado y notas de reunión, Mac)

**Qué hace en ElevenLabs:** app para Mac (acceso anticipado gratuito desde
el 11 de noviembre de 2026, tres meses gratis, precio posterior sin
anunciar) que combina dictado en 90+ idiomas con notas de reunión **sin
bot en la llamada**, resúmenes y acciones.

**Equivalente local:** el dictado sí se replica (Whisper local en el
navegador o en el backend, ver §10); la captura de reuniones sin bot es
específica de macOS y de su integración con el sistema, y no existe
equivalente local multiplataforma con presupuesto cero. Grabar una reunión
desde el propio micrófono/altavoz y transcribirla después sí es posible,
pero no es "sin bot" ni es automático.

**Grado: 🔴 NO REPLICABLE** (como producto). El dictado aislado es un
subconjunto del §10 y no necesita endpoint propio; la app Mac y la captura
de reuniones sin bot quedan fuera del clon.

---

## 23. Efectos de audio en TTS (audio effects)

**Qué hace en ElevenLabs:** desde el 12 de octubre de 2026, las peticiones
de TTS y Text to Dialogue aceptan un objeto `audio_effects`: preset de
filtro, distancia percibida, reverberación, cama de ruido de fondo en bucle
y paneo estéreo. Sin coste adicional. Catálogo consultable vía
`GET /v1/audio-effects/catalog`.

**Equivalente local:** procesado de señal clásico, sin IA: `ffmpeg` /
`sox` / `pedalboard` (Spotify, Apache-2.0). Reverb (convolución),
ecualización, paneo, mezcla de ruido de fondo y distancia (filtro +
reverb + atenuación) son operaciones DSP estándar.

**Grado: 🟢 TOTAL.** Es la función más fácil de replicar de todo el mapa:
ningún modelo generativo implicado, solo filtros. La calidad depende de
los presets, no de la IA.

**Endpoint FastAPI:**
```
POST /api/v1/audio-effects/apply       (multipart o JSON con audio_url)
  Entrada: audio, {"reverb": "hall|room|none", "distance": "close|far",
    "background_noise": "rain|cafe|none", "pan": -1.0..1.0,
    "filter_preset": "telephone|radio|none"}
  Salida: audio procesado.
GET  /api/v1/audio-effects/catalog    → lista de presets disponibles
```
*(El TTS de §1 acepta `"audio_effects": {…}` opcional y lo aplica tras sintetizar.)*

---

## 24. Alineación forzada / subtítulos (forced alignment)

**Qué hace en ElevenLabs:** dadas una transcripción conocida y su audio,
devuelve el inicio y fin de cada palabra (para subtítulos, karaoke,
audiolibros). En su API/MCP aparece como `forced_alignment`.

**Equivalente local:** **WhisperX** (alineación con wav2vec2, timestamps por
palabra) o **Montreal Forced Aligner** (MFA, más preciso, más pesado de
instalar). WhisperX es suficiente para subtítulos y resaltado.

**Grado: 🟢 TOTAL.** Función resuelta en open-source; WhisperX da la misma
información (palabra, inicio, fin) que el servicio de ElevenLabs.

**Endpoint FastAPI:**
```
POST /api/v1/align                     (multipart/form-data)
  Entrada: audio, "transcript": "texto conocido…", "language": "es",
    "output_format": "json | srt | vtt"
  Salida (JSON): {"words": [{"word", "start", "end"}], "segments": […]}
  (o fichero .srt/.vtt si output_format es srt/vtt)
```

---

## 25. Workspaces, equipos, facturación y créditos

**Qué hace en ElevenLabs:** espacios de trabajo multi-usuario (asientos,
roles, permisos), colecciones de voces compartidas, métricas de uso y
facturación por créditos (planes Free $0/10.000 créditos, Starter $6/30.000,
Creator $22/121.000, Pro $99/600.000, Scale $299/1,8 M, Business $990/6 M;
precios mensuales de noviembre de 2026, con descuento anual). El sistema
de créditos es el modelo de negocio: 1 crédito por carácter de TTS estándar,
330 por minuto de STT, 900 por minuto de música, 200 por efecto de sonido,
1.000 por minuto de Voice Changer/Isolator, 2.000–10.000 por minuto de doblaje
(**tarifas v1**; Dubbing v2 se cobra por API a $2,20/min de origen, ver §9).
**Añadido REA:** los créditos no usados de planes de pago **se acumulan hasta
2× la cuota mensual** (saldo máximo 3×); existe un límite de uso mensual por
miembro o cuenta de servicio (`PUT /v1/workspace/members/{user_id}/usage-limit`,
9 nov 2026); el plan Free no es comercial y exige atribución obligatoria.

**Equivalente local:** no se replica ni se necesita. El clon tiene 2 usuarios,
sin pago, sin equipos y sin facturación. Lo único que se conserva es el
**contador de uso** (§16, `GET /api/v1/usage`), que cumple la función
práctica del sistema de créditos —saber cuánto se ha generado— sin dinero
de por medio. La gestión de usuarios se reduce a un token por usuario.

**Grado: 🔴 NO REPLICABLE / FUERA DE ALCANCE.** No es una limitación técnica:
es una decisión de alcance. Replicar facturación y multi-tenant para 2
usuarios sería trabajo inútil. Se documenta aquí para que nadie lo pida
después como "función que falta".

**Endpoint FastAPI:** ninguno nuevo (ver `GET /api/v1/usage` en §16).

---

## 26. ElevenCreative Flows (canvas de nodos)

**Qué hace en ElevenLabs:** canvas de nodos (Alpha) donde cada nodo es un paso
(imagen, imagen a vídeo, TTS, lip-sync, música, SFX); re-ejecución por nodo;
exportación a Studio; ejecución en segundo plano; edición multiusuario en
tiempo real; Flows Agent (asistente conversacional que construye o modifica el
flujo, con modo de aprobación para operaciones caras). Conecta 50+ modelos de
imagen y vídeo de terceros + todos los modelos de audio. Sin endpoints
públicos documentados.

**Equivalente local:** ninguno. El clon no tiene modelos de imagen/vídeo.

**Grado: 🔴 NO REPLICABLE.** Fuera del alcance del clon de audio.

## 27. Generación de imagen y vídeo (modelos de terceros)

**Qué hace en ElevenLabs:** Veo 3.1, Kling, Seedance, Runway, FLUX, Nano
Banana y GPT Image dentro de ElevenCreative (Starter+). Modelos cerrados de
terceros, de pago. No existe en la API pública (solo app web cerrada y Studio
API Enterprise).

**Equivalente local:** ninguno en este proyecto.

**Grado: 🔴 NO REPLICABLE.** Fuera del alcance del clon de audio.

## 28. Audio Native (player integrable en webs)

**Qué hace en ElevenLabs:** player integrable en páginas web que narra el
contenido. Endpoints: `POST /v1/audio-native` (+ contenido por URL, ajustes).
Desde el plan Creator.

**Equivalente local:** un player HTML5 que narra el texto de una página con
el TTS del clon (§1).

**Grado: 🟡 PARCIAL.** Replicable con el motor de TTS existente, pero **no
implementado en el clon**: es una función nueva completa (pendiente, ver
`DELTAS_REA_APLICADAS.md`).

## 29. Studio Podcasts

**Qué hace en ElevenLabs:** crear podcasts desde Studio. Endpoint:
`POST /v1/studio/podcasts`.

**Equivalente local:** el mismo motor de proyectos de §14 (capítulos,
párrafos, voces por párrafo, exportación).

**Grado: 🟡 PARCIAL.** Sub-función de §14; pendiente porque §14 aún no está
construido (Fase 3).

## 30. Campaign Manager (ElevenAgents)

**Qué hace en ElevenLabs:** desde el 9 de noviembre de 2026, campañas
salientes por teléfono, voz de WhatsApp y mensajes de WhatsApp; contactos por
CSV o API; seguimiento, rellamadas, ventanas de llamada, límites de intentos,
listas de no llamar, analítica y exportación CSV.

**Equivalente local:** ninguno.

**Grado: 🔴 NO REPLICABLE.** Exige telefonía y escala empresarial.
Sub-función de §18.

## 31. Reception (ElevenAgents)

**Qué hace en ElevenLabs:** desde el 6 de octubre de 2026, recepcionista de
IA para pequeñas empresas: atiende llamadas y reserva trabajos.

**Equivalente local:** ninguno (sin telefonía en el clon).

**Grado: 🔴 NO REPLICABLE.** Sub-función de §18.

## 32. Architect (ElevenAgents)

**Qué hace en ElevenLabs:** desde el 6 de octubre de 2026 (fin de la alfa
gratuita el 31 de octubre de 2026), asistente que revisa la configuración del
agente y propone mejoras probadas en conversaciones simuladas.

**Equivalente local:** ninguno.

**Grado: 🔴 NO REPLICABLE.** Sub-función de §18.

## 33. Unity SDK (ElevenAgents)

**Qué hace en ElevenLabs:** desde el 5 de noviembre de 2026
(`io.elevenlabs.agents` v0.1.0), agentes en juegos: audio espacial y acciones
del juego; escritorio y WebGL, iOS/Android/XR en beta.

**Equivalente local:** ninguno.

**Grado: 🔴 NO REPLICABLE.** Sub-función de §18.

## 34. Interaction Engine / Memory / Routines (ElevenAgents)

**Qué hace en ElevenLabs:** preview del 11 de noviembre de 2026, **no
lanzados**: Interaction Engine (turn-taking, interrupciones, selección de
modelo), Memory (contexto entre conversaciones) y Routines (trabajo multi-paso
antes/durante/después de la conversación). También se previsualiza fine-tuning
de modelos para empresas.

**Equivalente local:** ninguno.

**Grado: 🔴 NO REPLICABLE.** No hay nada que replicar aún (preview sin
lanzar). Sub-funciones de §18.

## 35. Marketplace (apps de socios)

**Qué hace en ElevenLabs:** abierto el 11 de noviembre de 2026; compras en
2027. Tienda de apps de socios. Modelo de negocio, no función de audio.

**Equivalente local:** ninguno; fuera de alcance por decisión (§25).

**Grado: 🔴 NO REPLICABLE.**

## 36. Ads Engine

**Qué hace en ElevenLabs:** desde el 6 de noviembre de 2026,
traducción/doblaje de anuncios con revisión por lingüistas. Producto
empresarial.

**Equivalente local:** el doblaje por lotes de §9 cubre la parte automática,
sin revisión humana.

**Grado: 🔴 NO REPLICABLE** (como producto con revisión humana).

## 37. Content provenance (detección de watermark)

**Qué hace en ElevenLabs:** endpoint beta (17 nov 2026) que detecta el
watermark de ElevenLabs en un audio. Ruta exacta **no verificada**.

**Equivalente local:** el clon ya prevé registro de procedencia (§16: modelo,
muestra de referencia y metadatos por generación); no necesita detectar el
watermark ajeno.

**Grado: 🟢 TOTAL** (equivalente propio).

## 38. Voces similares

**Qué hace en ElevenLabs:** `POST /v1/similar-voices`: dado un audio,
devuelve voces parecidas de la biblioteca.

**Equivalente local:** búsqueda por similitud solo dentro de la biblioteca
propia (decenas de voces, §5).

**Grado: 🟡 PARCIAL.** Replicable en la biblioteca propia, pero **no
implementado en el clon**: es una función nueva (pendiente, ver
`DELTAS_REA_APLICADAS.md`).

---

## Apéndice A. Tabla resumen (para el agente de backend)

| # | Función ElevenLabs | Grado | Equivalente local primario | Endpoint principal |
|---|---|---|---|---|
| 1 | Text to Speech | 🟢 Total | Kokoro-82M + Qwen3-TTS 1.7B | `POST /api/v1/tts` |
| 2 | Text to Dialogue | 🟡 Parcial | Orquestación por segmentos (+ Dia, solo EN) | `POST /api/v1/dialogue` |
| 3 | Instant Voice Cloning | 🟢 Total | Qwen3-TTS CustomVoice (3 s) | `POST /api/v1/voices/instant-clone` |
| 4 | Professional Voice Cloning | 🟡 Parcial | Multi-referencia (+ LoRA manual) | `POST /api/v1/voices/pro-clone` |
| 5 | Voice Library | 🔴 No | Biblioteca propia (decenas de voces) | `GET /api/v1/library/voices` |
| 6 | Voice Design | 🟢 Total | Qwen3-TTS VoiceDesign 1.7B | `POST /api/v1/voices/design` |
| 7 | Voice Remix | 🟡 Parcial | DSP + regeneración con estilo | `POST /api/v1/voices/{id}/remix` |
| 8 | Speech to Speech / Voice Changer | 🟡 Parcial | OpenVoice v2 / kNN-VC | `POST /api/v1/speech-to-speech` |
| 9 | Dubbing | 🟡 Parcial | WhisperX + MADLAD-400 + Qwen3-TTS + ffmpeg | `POST /api/v1/dubbing` |
| 10 | Speech to Text (Scribe) | 🟢 Total | faster-whisper large-v3 + WhisperX + pyannote | `POST /api/v1/stt` |
| 11 | Sound Effects | 🟡 Parcial | Stable Audio Open 1.0 | `POST /api/v1/sfx` |
| 12 | Music | 🟡 Parcial | ACE-Step 1.5 (+ MusicGen, NC) | `POST /api/v1/music` |
| 13 | Voice Isolator | 🟢 Total | Demucs (+ DeepFilterNet) | `POST /api/v1/isolate` |
| 14 | Studio / Projects | 🟡 Parcial | App propia (capítulos + caché + regeneración) | `POST /api/v1/projects/…` |
| 15 | Diccionario de pronunciación | 🟢 Total | Reglas + espeak-ng / PLS | `POST /api/v1/pronunciation` |
| 16 | History | 🟢 Total | BD local + ficheros | `GET /api/v1/history` |
| 17 | API | 🟢 Total | FastAPI propia (+ compat. OpenAI TTS) | `GET /api/v1/health`, `/docs` |
| 18 | Agentes conversacionales | 🟡 Parcial | Pipeline STT→LLM→TTS por WebSocket | `WS /api/v1/agents/{id}/talk` |
| 19 | Eleven Realtime | 🔴 No | — (pipeline §18 como sustituto) | — |
| 20 | Realtime Translation | 🔴 No | — (doblaje por lotes §9) | — |
| 21 | ElevenReader | 🟡 Parcial | Lector web (PDF/ePub → TTS) | `POST /api/v1/reader/upload` |
| 22 | ElevenAI | 🔴 No | Dictado = §10 | — |
| 23 | Efectos de audio en TTS | 🟢 Total | ffmpeg / pedalboard (DSP) | `POST /api/v1/audio-effects/apply` |
| 24 | Alineación forzada | 🟢 Total | WhisperX | `POST /api/v1/align` |
| 25 | Workspaces / facturación | 🔴 No | Contador de uso (§16) | `GET /api/v1/usage` |
| 26 | ElevenCreative Flows | 🔴 No | — | — |
| 27 | Imagen y vídeo (terceros) | 🔴 No | — | — |
| 28 | Audio Native | 🟡 Parcial | Player HTML5 + TTS (§1) | `POST /api/v1/audio-native` (pendiente) |
| 29 | Studio Podcasts | 🟡 Parcial | Motor de proyectos (§14) | `POST /v1/studio/podcasts` (pendiente) |
| 30 | Campaign Manager | 🔴 No | — | — |
| 31 | Reception | 🔴 No | — | — |
| 32 | Architect | 🔴 No | — | — |
| 33 | Unity SDK | 🔴 No | — | — |
| 34 | Interaction Engine / Memory / Routines | 🔴 No | — (preview, no lanzado) | — |
| 35 | Marketplace | 🔴 No | — | — |
| 36 | Ads Engine | 🔴 No | Doblaje por lotes (§9) | — |
| 37 | Content provenance (watermark) | 🟢 Total | Registro de procedencia (§16) | — |
| 38 | Voces similares | 🟡 Parcial | Biblioteca propia (§5) | `POST /v1/similar-voices` (pendiente) |

**Conteo final (25 funciones originales): 10 totales · 10 parciales · 5 no
replicables (sin cambio en v2). Áreas añadidas en v2 (§26–§38 + sub-funciones
de §10 y §12): 2 totales · 5 parciales · 9 no replicables (16 filas A1–A16;
3 de ellas son sub-funciones dentro de su sección, por lo que el total de
áreas es 37 según `REA_VERIFICACION.md` §4).**

## Apéndice B. Prioridad de implementación sugerida (no vinculante)

1. **Fase 1 (núcleo):** §1 TTS, §3 IVC, §6 Voice Design, §16 History, §17 API.
2. **Fase 2 (utilidad diaria):** §10 STT, §13 Isolator, §15 pronunciación,
   §23 efectos, §24 alineación.
3. **Fase 3 (proyectos):** §14 Studio, §2 diálogo, §21 Reader, §9 Dubbing.
4. **Fase 4 (generativo y experimental):** §11 SFX, §12 Music, §8 STS,
   §4 PVC multi-referencia, §7 Remix, §18 agentes.
5. **No hacer:** §5 catálogo de miles de voces, §19 Realtime, §20 traducción
   en vivo, §22 ElevenAI, §25 facturación, §26 Flows, §27 imagen y vídeo,
§30 Campaign Manager, §31 Reception, §32 Architect, §33 Unity SDK, §34
Interaction Engine / Memory / Routines (preview, no lanzado), §35
Marketplace, §36 Ads Engine.

## Apéndice C. Riesgos y límites que el backend debe asumir por escrito

- **GPU bajo demanda:** si Kaggle está apagado, solo funciona Kokoro en CPU
  (§1) y el STT ligero; todos los endpoints GPU deben devolver 503 con un
  mensaje claro, no un error genérico.
- **VRAM T4 16 GB:** no cargar Qwen3-TTS 1.7B + Whisper large-v3 + Stable
  Audio a la vez sin descargar modelos entre jobs. El backend necesita un
  gestor de modelos con carga/descarga bajo demanda.
- **Español:** es el idioma del usuario y está cubierto en Qwen3-TTS,
  Kokoro y CosyVoice, pero la calidad de referencia de ElevenLabs es en
  inglés; validar cada función en español antes de darla por hecha.
- **Licencias NC:** F5-TTS, Fish Speech, MusicGen y NLLB son no comerciales.
  Uso privado de 2 usuarios: aceptable. Publicar o cobrar por el clon con
  esos modelos dentro: no aceptable sin cambiar de modelo.
- **Clonación y consentimiento:** guardar `consent_note` en cada voz clonada
  (§3–§4). Sin consentimiento no hay clonación, aunque el modelo lo permita.
- **Chatterbox retirado (ago 2026) y Coqui cerrado (dic 2025):** no basar
  nada nuevo en ellos; quedan como referencia histórica en este mapa.

---

## Apéndice D. Discrepancias abiertas — pendientes para el navegador vivo

Estas 8 discrepancias las marcó el REA como «no verificado» y **no se
resuelven en esta v2**: solo el navegador vivo con DevTools y login en
`elevenlabs.io/app` puede cerrarlas (ver `REA.md` §8, lista exacta N1–N10,
bundles JS, 8 flujos y 8 preguntas).

| # | Discrepancia | Sección | Estado |
|---|---|---|---|
| D1 | Voice Design: ¿3 o 5 vistas previas? (mapa: 3; guía API may 2026: 5) | §6 | No verificado |
| D2 | Dubbing: ¿límite de subida 1 GB (docs) / 2 GB (ayuda) / 3 GB (API)? | §9 | No verificado |
| D3 | SFX v3: ¿funciona `loop: true` en v3 o sigue necesitando v2? | §11 | No verificado |
| D4 | Dubbing v2: ¿qué exporta realmente (solo MP4, o también audio separado y WebVTT)? | §9 | No verificado |
| D5 | Flash v2.5: ¿40.000 caracteres por petición? | §1 | No verificado |
| D6 | Voice Library: ¿17.500+ voces? (usar 10.000+ hasta verificar) | §5 | No verificado |
| D7 | Scribe: ¿hasta 32 hablantes etiquetados? | §10 | No verificado |
| D8 | Agentes: ¿«55 % de sus ingresos»? | §18 | No verificado |

Además: la ruta exacta del endpoint beta de content provenance (§37) tampoco
está verificada, y no se inspeccionó ningún tráfico de la app web (N1–N10 de
`REA.md` §8): queda por confirmar si la web llama solo a `api.elevenlabs.io`
o hay un host interno.

---

## Fuentes

**ElevenLabs (funciones, modelos y precios, nov 2026):**
- Documentación oficial, changelog 12 oct 2026 (audio effects, colecciones
  de voces, agentes): https://elevenlabs.docs.buildwithfern.com/docs/changelog/2026/10/12
- Reseña con precios verificados en elevenlabs.io el 1 nov 2026 (planes
  Free–Business, créditos por producto, modelos v4/v3/Multilingual v2/Flash):
  https://www.stork.ai/en/elevenlabs
- Reseña con precios verificados el 1 nov 2026 (Scribe v2, Dubbing v2,
  Instant/Professional Cloning): https://www.stork.ai/blog/elevenlabs-review-2026
- Resumen de producto (ElevenCreative / ElevenAgents / ElevenAPI, v4,
  Scribe v3 10 nov 2026, Realtime 20 oct 2026): https://fruitpunch.ai/review/elevenlabs
- Línea de tiempo de lanzamientos 2026 (Scribe v3, Realtime, SFX v3,
  ElevenAI 11 nov 2026, PVC fine-tuning v4): https://www.scriptbyai.com/elevenlabs-timeline/
- Guía de producto y modelos (v4 90+ idiomas, Scribe, Voice Design, Studio,
  Dubbing): https://www.ithub.directory/ai-voice-speech/elevenlabs
- Guía 2026 (v4 lanzado 28 sep 2026, Scribe v3, Realtime, Instant Soundtracks):
  https://promptwises.com/tools/ai-content/elevenlabs
- Reseña con changelog re-verificado el 6 nov 2026 (precios API, Dubbing,
  Scribe v3 Live): https://promptwises.com/reviews/elevenlabs-review

**Modelos TTS / clonación open-source:**
- Qwen3-TTS, guía de clonación zero-shot (Apache-2.0, 3–30 s, 0.6B/1.7B):
  https://github.com/wty2003328/voice-cloning-guide/blob/HEAD/docs/models/qwen3-tts.md
- Qwen3-TTS para creadores (Apache-2.0, sin marca de agua, Colab):
  https://github.com/artcore-c/ai-voice-clone-with-qwen3-tts/blob/HEAD/README.md
- Qwen3-TTS, resumen general (modos, tamaños, licencias):
  https://qwen-ai.com/qwen-tts/
- Comparativa de modelos TTS open-source por licencia y VRAM, verificada
  el 12 nov 2026 (Kokoro, Qwen3-TTS, CosyVoice 3, Chatterbox retirado,
  F5-TTS NC, IndexTTS, Fish Drama 3): https://quantacloud.net/guides/open-source-tts-models
- Kokoro-82M, prueba real en CPU (Apache-2.0, 54 voces, 8 idiomas, ~6×
  tiempo real): https://www.visionstory.ai/open-source/kokoro-tts
- Modelos TTS open-source comparados (licencias, clonación, hardware):
  https://voicemodeler.com/guides/open-source-text-to-speech
- Mejores TTS locales nov 2026 (Kokoro, Qwen3-TTS, Chatterbox Nano en CPU):
  https://vdf.ai/blog/best-local-tts-models/
- TTS open-source por licencia y puntuación (Cartesia, nov 2026):
  https://www.cartesia.ai/learn/open-source-tts
- Alternativas open-source a ElevenLabs, 18+ modelos, MOS y clonación
  (abr 2026, validado 21 may 2026): https://github.com/bettercallzaal/ZAOOS/blob/main/research/music/329-open-source-tts-elevenlabs-alternatives/README.md
- Comparativa de 6 clonadores probados (F5-TTS, XTTS v2, IndexTTS-2,
  Chatterbox, Fish Speech): https://rarebuildsoftware.com/blog/best-open-source-voice-cloning-2026.html

**STT, aislamiento, música y SFX:**
- OmniVoice Studio, alternativa open-source a ElevenLabs (WhisperX, Demucs,
  pyannote, doblaje local — arquitectura de referencia para el pipeline
  del §9): https://github.com/zhuganglie/OmniVoice-Studio
- Verbatim, pipeline STT local (faster-whisper + Demucs + pyannote):
  https://pypi.org/project/verbatim/0.1.6/
- AudioLDM2, Stable Audio Open y MusicGen para SFX y música (licencias,
  VRAM, duraciones): https://studio.aifilms.ai/blog/audioldm2-stable-audio-open-musicgen-local-foley-sound-design
- Generación de música open-source 2026 (MusicGen, Stable Audio Open,
  ACE-Step, YuE; licencias): https://github.com/elite588/ai-engineering-from-scratch/blob/HEAD/phases/06-speech-and-audio/09-music-generation/docs/en.md

**Nota sobre enlaces:** los enlaces de arriba son las URLs exactas devueltas
por la búsqueda web durante esta investigación. La web oficial de ElevenLabs
(`elevenlabs.io/pricing`, `/docs`) no pudo abrirse directamente en esta
sesión (origen bloqueado para la lectura de páginas); sus contenidos se
verificaron a través de la documentación oficial espejada (changelog) y de
las reseñas citadas, todas ellas con fecha de verificación en noviembre
de 2026. Los repositorios y pesos de los modelos locales se citan por su
identificador de Hugging Face / GitHub en el cuerpo del documento
(`hexgrad/Kokoro-82M`, `Qwen/Qwen3-TTS-12Hz-1.7B-Base`,
`FunAudioLLM/CosyVoice2-0.5B`, `stabilityai/stable-audio-open-1.0`,
`facebook/musicgen-small`, `Systran/faster-whisper`); el agente de backend
debe confirmar la ruta exacta en Hugging Face antes de descargar.
