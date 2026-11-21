# Auditoría de skills — Clon web de ElevenLabs con modelos locales open-source

- **Fecha:** 2026-11-20
- **Auditor:** subagente auditor (por encargo del orquestador)
- **Proyecto:** clon web de ElevenLabs, solo para Carlos y otra persona. Presupuesto cero. Frontend: SPA estática para GitHub Pages (HTML/CSS/JS). Backend: FastAPI con modelos TTS / clonación de voz locales. UI profesional copiando el **sistema de diseño** de ElevenLabs (mejorado, marca propia; sin copiar logo, textos de marketing ni nombres de voces).
- **Método:** encuesta del catálogo con `muse.skill_search` (5 consultas: diseño UI frontend, TTS/voz/narración, investigación paralela, documentos, QC audio/vídeo; más 5 de refuerzo: clonación de voz, FastAPI/backend, licencias open-source, animación GSAP, humanizar texto) y lectura completa del `SKILL.md` de cada candidata. Ninguna skill se clasifica de adorno: cada ÚTIL lleva su aporte concreto escrito.

---

## 1. Resumen del recuento (deduplicado)

| Clasificación | Cantidad |
|---|---|
| **ÚTIL** | **14** |
| **CONDICIONADO** | **9** |
| **NO ÚTIL** | **4** |
| **Total evaluadas** | **27** |

---

## 2. Skills ÚTILES (14)

### 2.1. `local-ui-ux-pro-max` — ÚTIL (pilar de diseño)
**Aporte concreto:** genera el sistema de diseño completo del clon (estilo, paleta, tipografía, espaciado, componentes) con su script de búsqueda local y lo persiste como fuente única de verdad en `design-system/<proyecto>/MASTER.md`.
**Reglas extraídas, aplicables sin releer la skill:**
- Orden de prioridades 1→10: (1) accesibilidad, (2) táctil/interacción, (3) rendimiento, (4) selección de estilo, (5) layout responsive, (6) tipografía y color, (7) animación, (8) formularios y feedback, (9) navegación, (10) gráficos y datos.
- Accesibilidad: contraste ≥ 4.5:1 (texto grande ≥ 3:1), texto alternativo, navegación por teclado, `aria-labels`; prohibido quitar anillos de foco y botones solo-icono sin etiqueta.
- Táctil: tamaño mínimo 44×44 px, separación ≥ 8 px, feedback de carga siempre; prohibido depender solo de hover y cambios de estado instantáneos (0 ms).
- Rendimiento: CLS < 0.1, reservar espacio para contenido que carga, lazy loading.
- Tipografía y color: base 16 px, interlineado 1.5, tokens semánticos de color (nunca hex crudo en componentes); prohibido texto de cuerpo < 12 px y gris sobre gris.
- Layout: mobile-first (Carlos trabaja desde el teléfono), meta viewport, prohibido scroll horizontal, anchos fijos en px y desactivar zoom.
- Animación: un solo timing por transición no vale; animar transform/opacity, nunca width/height; respetar `prefers-reduced-motion`.
- Formularios: etiquetas visibles (nunca solo placeholder), error junto al campo, texto de ayuda, revelado progresivo.
- Navegación: comportamiento de "atrás" predecible, navegación inferior ≤ 5 ítems, deep linking.
- Flujo de uso: `python "~/workspace/custom-skills/local-ui-ux-pro-max/scripts/search.py" "<tipo producto> <industria> <palabras clave>" --design-system --persist --output-dir <raíz del proyecto> -p "<nombre de marca propia>"`; diales opcionales `--variance/--motion/--density` (para un panel-herramienta: densidad alta 8, motion bajo 2–3, variance media 4–6). Leer `references/pro-rules.md` y pasar su checklist pre-entrega antes de entregar la UI.
- Si una búsqueda devuelve 0 resultados: reintentar una vez con frase más estrecha; si sigue vacío, decir explícitamente que la recomendación viene de los defaults, no de la base de datos. Nunca presentar un 0-resultados como si hubiera datos.

### 2.2. `local-design-extract` — ÚTIL (el mecanismo de "copiar el sistema de ElevenLabs")
**Aporte concreto:** es la skill que ejecuta la copia del sistema de diseño de elevenlabs.io (tokens, tipografías, espaciados, layout, motion, estados hover/focus/active, responsive) y su verificación de fidelidad; la regla de Carlos (2026-10-21) ya está codificada en ella.
**Reglas extraídas:**
- Se copia el sistema de diseño, NUNCA contenido, textos, imágenes, logos, nombres ni marcas. El copy, las fotos y la marca son siempre del proyecto de Carlos.
- La copia debe SUPERAR al original en tres ejes o no se entrega: rendimiento (menos CSS, sin tokens sin uso), accesibilidad (contraste WCAG, foco visible) y calidad (consistencia en todos los breakpoints).
- Solo se ejecuta sobre una URL que Carlos indique en cada caso (aquí: elevenlabs.io). Nunca autónomo ni masivo.
- Flujo: extraer con el CLI upstream (`npx designlang <url>`), guardar la salida (17+ archivos: tokens DTCG, config Tailwind, tema shadcn, variables Figma, tokens de motion, anatomía de componentes) como referencia separada del código final; adaptar, no pegar: reescribir tokens en el stack del proyecto (HTML/CSS/JS estático), eliminar lo sin uso; verificar con `designlang fidelity <sitio> --clone <local>` y demostrar la mejora con medidas propias.
- Prohibido `designlang --smart` (clasificación externa de Atlas Cloud) sin aprobación explícita de Carlos.
- Entrega con atribución honesta: "sistema de diseño de referencia: elevenlabs.io, adaptado y optimizado", sin presentarlo como invención propia.

### 2.3. `local-frontend-design` — ÚTIL (criterio de diseño distintivo)
**Aporte concreto:** convierte la copia de tokens en una identidad con punto de vista propio (marca propia, no plantilla de SaaS genérica) y fija qué verificar en navegador antes de entregar.
**Reglas extraídas:**
- Ancla en el tema antes de escribir código, en una frase: de qué trata el producto, para quién es y cuál es su trabajo principal. Las decisiones visuales salen del mundo del tema, no de la categoría "otra landing de SaaS".
- El héroe manda: la primera pantalla muestra lo más característico (aquí: el estudio de voz — caja de texto + selector de voz + botón de generar, no un hero de marketing).
- La tipografía lleva la personalidad: una o dos familias, claramente distintas si son dos; escala deliberada, pesos y espaciados con intención.
- La estructura informa: bordes, números, etiquetas y divisores codifican información real (p. ej. pasos 1-2-3: elegir voz → escribir → generar). No numerar lo que no es secuencia; no etiquetar lo que no necesita etiqueta.
- Delatores de plantilla prohibidos: acentuar una sola palabra del titular con otro color o cursiva, TODO EN MAYÚSCULAS para etiquetas, etiquetas decorativas sobre el contenido, secciones intercambiables que servirían para cualquier producto.
- Verificación (regla de entrega de Carlos): comprobar en navegador real, escritorio y móvil, antes de entregar: que cada función responde, que el texto es exacto y que nada se rompe en pantallas estrechas. Entregar la dirección resumida (paleta, tipografías, estructura) en pocas líneas junto al código, con qué se decidió y por qué.

### 2.4. `local-impeccable` — ÚTIL (piso de calidad anti-genérico)
**Aporte concreto:** vocabulario compartido para criticar el diseño con precisión (`audit` antes que `polish`, `critique`, `distill`, `bolder`/`quieter`) y un piso de calidad verificable sobre el resultado construido, no sobre la intención.
**Reglas extraídas (de `reference/craft-floor.md`, leer antes de editar):**
- Contraste: texto ≥ 4.5:1, texto grande ≥ 3:1; nunca gris sobre color.
- Sombras con desplazamiento y blur suave; ritmo de espaciado consistente; medida de texto 65–75 caracteres por línea.
- Un solo momento de movimiento (no el mismo fundido en cada sección).
- Estados obligatorios: hover, disabled, loading, error y vacío — también en el reproductor de audio, la cola de generación y el formulario de clonación.
- Superficies del navegador: selección, caret, scrollbars y focus visibles.
- Rechazos por defecto: tarjetas idénticas icono+título+texto como estructura, tarjetas anidadas, hero-métrica, texto con degradado, glassmorphism decorativo, bordes laterales de color > 1 px, sombras duras de bloque, glifos/emoji como iconos, SVG que imita ilustración a mano, y kicker/eyebrow sobre cada título (este último es ban absoluto).
- Modo según la superficie: el clon es **Operate** (app/herramienta), no Persuade (landing): prima la operatividad sobre la persuasión.
- Límites honestos: NO ejecutar el lanzador ni el CLI (`npx impeccable install` descarga un binario), NO instalar hooks, sin telemetría; las 61 reglas deterministas del motor Rust NO corren automáticamente — se aplican leyendo `reference/` y verificando en el navegador.
- Verificar mirando el resultado real a los tamaños de entrega, en una sola pasada por tanda de correcciones, con `delivery_audit_gate`.

### 2.5. `local-taste` — ÚTIL (dirección de arte sorteada + verificación en navegador)
**Aporte concreto:** sortea una dirección de arte de su biblioteca (paleta, tipografía, escenas, secciones) en vez de dejar que el modelo elija el default de su categoría, y verifica la página real en varios anchos con `scripts/inspect.mjs`.
**Reglas extraídas:**
- Dirección antes que código: usar `scripts/draw.mjs` (local, sin dependencias, sin red) para sortear la dirección.
- Verificación en navegador real: `scripts/inspect.mjs` renderiza, mide y fotografía la página en varios anchos; salida 0 = sin fallos, 1 = hay fallos.
- Activos con licencia: `scripts/assets.mjs` solo consulta fuentes públicas (Openverse, Wikimedia Commons, Art Institute of Chicago, Met, Archive.org) y registra la licencia de cada imagen.
- **COSTE: una build lleva ~30–45 minutos y cientos de miles de tokens.** Es para páginas que lo justifiquen, NUNCA por defecto ni para un ajuste pequeño. Avisar a Carlos del coste antes de arrancar una build completa. Para este clon: usar solo el sorteo de dirección + la inspección, no la build completa, salvo que Carlos lo pida.
- Complementa, no sustituye, a `local-ui-ux-pro-max` (sistema de diseño y usabilidad).

### 2.6. `local-web-design-guidelines` — ÚTIL (auditoría de código contra las guías de Vercel)
**Aporte concreto:** audita el código fuente ya construido contra las Web Interface Guidelines de Vercel; es la única skill de auditoría que revisa código (no render), y complementa a `delivery_audit_gate` (que audita en navegador vivo).
**Reglas extraídas:**
- Paso 1 obligatorio: traer las reglas frescas de `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md` antes de revisar nada. Si la lectura falla, parar: no auditar con reglas recordadas ni inventadas.
- Paso 2: leer los archivos indicados; si no se indica ninguno, preguntar cuáles revisar, no auditar el proyecto entero por defecto.
- Paso 3: aplicar TODAS las reglas del documento (accesibilidad, foco, tipografía, modo oscuro, botones, formularios, errores…), sin filtrar solo las cómodas.
- Salida escueta formato `archivo:línea`, un hallazgo por línea, agrupado por archivo, sin relleno ni elogios; archivo sin hallazgos = marca de aprobado escueta.
- Un hallazgo es "incumple la guía de Vercel", no "está mal en absoluto": si una regla choca con una decisión deliberada aprobada por Carlos, se anota como excepción consciente, no como fallo.
- No genera código ni corrige nada por sí sola; la corrección es un paso aparte que Carlos aprueba. Gratuita, sin instalación ni credenciales.

### 2.7. `narration_voice_design` — ÚTIL (diseño y estabilidad de cada voz del clon)
**Aporte concreto:** es la skill de voz del catálogo: diseña cada voz por escrito antes de generarla, persiste su identidad y verifica cada bloque contra la muestra aprobada. Es el puente entre la UI y el backend TTS.
**Reglas extraídas (adaptadas a modelos locales — ver §5):**
- Diseñar la voz en papel primero: prompt de diseño con género, banda de edad aproximada, acento y marcadores dialectales, ritmo, banda de tono y textura, en términos concretos. Pedir aprobación de Carlos del texto exacto del prompt antes de aplicarlo. El prompt debe ser corto y reproducible verbatim.
- Persistir la voz antes de prometer identidad: crear primero el objeto persistente (en local: embedding de locutor + audio de referencia archivado, no un ID de proveedor). Generar una muestra corta de ese objeto exacto y que Carlos la apruebe por oído. Solo la muestra aprobada del objeto persistido es "la voz".
- Archivar juntos: prompt exacto, identificador/embedding, proveedor/proyecto (aquí: modelo local + ruta del audio de referencia) y muestra aprobada. Los IDs de voz no se portan entre proyectos, cuentas ni claves — en local, el embedding no se porta entre modelos.
- Generar en bloques cortos (~2 min) y verificar cada bloque contra la muestra aprobada: mismo género, mismo acento, tono dentro de la banda de referencia, sin texto del prompt filtrado al inicio del audio. Regenerar el bloque que se desvíe; máximo 3 intentos de corrección, luego escalar a Carlos con el diagnóstico.
- Comprobar tier y límites antes de empezar (en local: VRAM, tiempo de inferencia, cuota de CPU/GPU) — en proveedores, la replicación de voz se vio bloqueada tras un tier de pago y los límites diarios gratuitos pararon una narración dos veces.
- Ensamblar y masterizar: concatenar bloques verificados en orden y normalizar loudness al target de entrega, p. ej. **-16 LUFS con pico real ≤ -1 dBTP** para vídeo online.
- Escuchar el ensamblaje completo como espectador antes de entregar; corregir lo que se oiga y entregar una sola vez.
- Informar con la entrega: ID de voz, prompt de diseño y resultado de la verificación, para que una sesión posterior pueda reproducir o auditar la voz.

### 2.8. `delivery_audit_gate` — ÚTIL (puerta de entrega de la SPA)
**Aporte concreto:** audita función por función la SPA en el navegador vivo y bloquea la entrega hasta que todo pase; es la puerta que exige la regla permanente de Carlos ("ninguna entrega sin haber comprobado todas las funciones en el navegador").
**Reglas extraídas:**
- Enumerar cada función antes de abrir el navegador: leer los archivos y contar botones, formularios, vistas, descargas, exportaciones y estados dinámicos; escribir la checklist (para el clon: escribir texto, elegir voz, generar, reproducir, pausar, descargar WAV/MP3, subir audio de referencia, clonar, borrar voz, estados vacío/error/cargando, responsive móvil).
- Tratar rutas dinámicas y condicionales como funciones separadas: un botón que se comporta distinto con estado vacío o error lleva su propia línea.
- Ejecutar cada función en el navegador vivo, con las mismas credenciales, datos de muestra y ajustes que usaría un usuario real. Capturar evidencia por cada ejecución (qué se pulsó, qué apareció, texto de error). Una función pasa solo cuando su salida real coincide con la esperada, no cuando el código "parece correcto".
- Registrar una línea por función: pass/fail + evidencia (enlace, captura o salida citada). Agrupar fallos por causa.
- Corregir cada fallo y repetir la checklist COMPLETA, no solo la línea fallida (un fix puede romper otra función). Repetir hasta un pase limpio sin ediciones entre pasadas.
- Entregar solo con pase limpio; adjuntar el informe de auditoría a la entrega. Nunca declarar terminado por revisión de código. Probar con caché fresca (cache-buster) y en el canal que Carlos usa (su teléfono).

### 2.9. `local-thermo-review` — ÚTIL (calidad de código del frontend y del backend)
**Aporte concreto:** rúbrica de revisión de mantenibilidad extremadamente estricta para el código que se va a mantener meses (SPA + FastAPI): simplificación estructural ambiciosa, tope de tamaño de archivo y freno al crecimiento espagueti.
**Reglas extraídas:**
- Buscar el "code judo": la reorganización que hace la implementación dramáticamente más simple, pequeña, directa y elegante. Medir dos veces, cortar una.
- Regla 1: ningún archivo pasa de < 1000 líneas a > 1000 sin razón muy fuerte; extraer helpers, subcomponentes o módulos. Si el diff cruza ese umbral, preguntar explícitamente si se descompone primero.
- Regla 2: cada nuevo condicional debe justificarse y no puede degradar la estructura existente.
- Solo cuando se pida expresamente una revisión dura o en cambios grandes/refactors; NO por defecto en cada cambio pequeño (ralentiza deliberadamente). Para revisión normal: `delivery_audit_gate`.
- No toca seguridad ni tests por sí misma: combinar con el checklist de seguridad de `replica-backend` (§2.14) y con tests cuando el cambio lo exija. Es rúbrica de opinión, no verdad universal: presentar la recomendación, no aplicarla sin aprobación.
- Material: Markdown puro, sin código, sin red, sin scripts, sin telemetría.

### 2.10. `wide-research` — ÚTIL (investigación paralela de modelos TTS locales)
**Aporte concreto:** coordina un subagente gestor que reparte la misma tarea de investigación entre muchos inputs independientes (aquí: un modelo TTS local por input — XTTS-v2, Chatterbox, F5-TTS, Kokoro, etc.) y devuelve un único conjunto normalizado con el mismo esquema de salida.
**Reglas extraídas:**
- Usar solo cuando la tarea se divide en subtareas independientes con los mismos campos estructurados; no para tareas de un solo ítem ni subtareas dependientes.
- Contrato del gestor: `operation_brief` (una frase), `inputs` (un ítem independiente por elemento), `output_schema` (campos y tipos), `worker_prompt_template`, `completion_format` (forma JSON exacta). Salida del gestor: `total`, `success_count`, `failure_count`, `results`, `failures`, `notes`.
- Deduplicar y normalizar la lista de inputs antes de lanzar el gestor; un solo gestor por objetivo; un worker por input, cada uno en su ítem.
- Esquema de salida mínimo y explícito para los modelos TTS: licencia, calidad de clonación (SIM / WER si hay datos), idiomas (español), requisitos de hardware (VRAM/RAM/CPU), latencia, formato de salida, mantenimiento (último commit), adopción (stars/forks).
- Completar un ítem, medir CPU/memoria/requisitos, y solo entonces subir la concurrencia. Tras un fallo, corregir la causa y reintentar solo el trabajo faltante, preservando resultados y checkpoints.
- En la salida final, informar cobertura verificada (`success_count/total`) y huecos sin resolver; distinguir pendiente, fallido, parado y nunca iniciado; contar cada ítem una sola vez aunque necesitara varios intentos.

### 2.11. `provider_model_verification` — ÚTIL (verificar el modelo antes de asignarlo)
**Aporte concreto:** disciplina de verificación de un modelo antes de asignarle un build o un lote: catálogo vivo, llamada de tamaño real y registro de la asignación. Nació para ApiNex/Coarena, pero su método es el que evita asignar al clon un modelo TTS que luego no rinde.
**Reglas extraídas (adaptadas a modelos locales — ver §5):**
- Consultar la fuente viva el día de la asignación (endpoint público de modelos / repo / release) y leer los campos de licencia y disponibilidad del modelo exacto; nunca asignar desde una captura o lista de otro día cuando la fuente viva es alcanzable.
- Probar capacidad con una llamada de tamaño real: primero un probe mínimo, luego una llamada del tamaño del trabajo real (p. ej. generar 30–60 s de español con la voz clonada) antes de asignar todo el build. Un probe que pasa y una llamada real que devuelve 429 (o OOM, o timeout) es un fallo de capacidad: esperar o cambiar de proveedor solo por orden explícita de Carlos.
- Registrar la sustitución cuando el modelo que responde difiere del pedido; nunca informar el modelo pedido como el que respondió.
- Registrar en el plan antes de lanzar: id del modelo, modelo que respondió, fuente viva y su fecha, cuota/coste/peso y resultado de capacidad. Re-verificar tras una caída, cambio de roster o nuevo día.
- Si ninguna fuente viva confirma el modelo necesario, pedir decisión a Carlos nombrando el chequeo que falta. Un 402 persistente tras reclamar el check-in diario = puerta de pago: parar e informar la decisión de pago, no reclamar de nuevo.

### 2.12. `local-repo-radar` — ÚTIL (vetar los repositorios de los modelos TTS)
**Aporte concreto:** rúbrica de calidad + auditoría de seguridad obligatoria antes de instalar cualquier repo público, con dominios rotativos que ya incluyen "Procesamiento de audio / TTS / pódcast". Es el filtro de entrada de cada modelo TTS candidato.
**Reglas extraídas:**
- Rúbrica (todo debe cumplirse para instalar): (1) público y con licencia permisiva (MIT, Apache-2.0, ISC, BSD); (2) actualidad: commits en los últimos 12 meses, idealmente 6; (3) adopción real: stars, forks, issues activos o uso documentado en producción — un repo pequeño pero activo y enfocado vale más que uno grande abandonado; (4) utilidad concreta: resuelve un problema real; (5) seguridad obligatoria antes de instalar: leer el código buscando llamadas de red (`fetch`, `XMLHttpRequest`, websockets), exfiltración de datos, ofuscación, `eval` con contenido remoto, mineros y telemetría oculta; revisar `package.json`/dependencias por paquetes typosquat o sospechosos. Si algo no se puede auditar, NO se instala.
- Protocolo: clonar en `~/workspace/skills/<nombre>/` (solo lo necesario, anotando URL + commit); crear `NOTAS.md` con URL, commit/versión, licencia, para qué sirve, ejemplo mínimo y resultado de la auditoría; si es librería JS utilizable en la app, vendorear el `dist` mínimo y anotar cómo integrarlo; registrar en `~/workspace/custom-skills/local-repo-radar/REGISTRO.md` con fecha y motivo.
- Cada barrido produce un reporte breve: dominios cubiertos, candidatos evaluados (con veredicto), instalados (con ruta), descartados (con motivo).
- Nota de contexto: auditoría 2026-11-20 — ya pasaron Maigret (MIT) y otros; los repositorios con licencia copyleft (AGPL/GPL) NO pasan. Esto es decisivo para TTS: varios modelos de voz usan licencias no permisivas o de uso no comercial — verificar la licencia del modelo y de sus pesos por separado, no solo la del repo.

### 2.13. `transcribe_recordings` — ÚTIL (verificar por oído y por texto lo que el clon genera)
**Aporte concreto:** transcribe audio localmente con faster-whisper (venv ya existente `~/workspace/venvs/whisper`, modelo `small`, CPU int8) en trozos de 60 s con solape, con reanudación por checkpoints. Sirve como oráculo independiente de inteligibilidad: transcribir lo generado por el clon y comparar con el texto de entrada (WER aproximado, palabras inventadas, cortes).
**Reglas extraídas:**
- Inspeccionar duración y límites de CPU/memoria antes de transcribir; el tamaño comprimido no acota la memoria decodificada.
- Comando: `python3 /opt/muse/assets/audio/transcribe_chunks.py --input <audio> --model ~/workspace/models/whisper-small --output-dir <dir> --language es` (omitir `--language` para detección automática; `--chunk-seconds` entre 5 y 120 si hace falta).
- Tras una interrupción, repetir el mismo comando y directorio: reutiliza trozos completos. Tras un OOM, reducir trabajo concurrente y reintentar preservando los trozos.
- Acortar trozos o cambiar de modelo exige un directorio nuevo (reinicia desde cero); el helper rechaza checkpoints incompatibles.
- Tratar los trozos como trabajo parcial hasta que aparezcan `complete.json` y `transcript.txt`. Un resultado `needs_review` = límites disputados: revisar esos pasajes contra el audio, no presentarlos como verificados.
- Verificar que la transcripción cubre toda la grabación y contrastar nombres dudosos contra el audio.
- Nota de AGENTS.md (2026-10-19): Whisper normaliza grafías fonéticas al transcribir (eya→ella, etc.): comparar contra el texto esperado **normalizado** (minúsculas, sin tildes ni puntuación), no literal. Fijar `av<14` (13.1.0): faster-whisper 1.2.1 falla con av≥14.

### 2.14. `replica-backend` — ÚTIL (checklist de backend, adaptado a FastAPI)
**Aporte concreto:** checklist de backend (auth, base de datos, seguridad, jobs) y reglas de integración por API oficial. Nació para clones con Supabase/Stripe, pero su checklist de seguridad y su disciplina de `.env.example` se aplican tal cual al FastAPI local; las partes de pagos/Supabase no aplican (ver §5).
**Reglas extraídas (solo las aplicables; el resto se descarta, no se fuerza):**
- Solo APIs oficiales y públicas, con las claves del usuario. Nunca llamar endpoints privados del original, nunca reutilizar su OAuth, nunca proxear a través de él.
- El usuario crea cuentas y claves; el agente nunca escribe contraseñas, tarjetas ni claves vivas. Escribir `.env.example` con cada nombre de variable y sin valores.
- Sesiones con cookies http-only seguras; cierre de sesión en todas partes; borrado de cuenta que borre de verdad (aquí: borrado de voces clonadas y audios de referencia).
- Reglas de acceso en cada tabla/endpoint: una función que responda "¿puede este usuario hacer esto a este registro?"; probarlo con un segundo usuario que no debe ver nada (aquí: los 2 usuarios del clon no deben verse las voces del otro).
- Jobs con reintentos y registro de fallos (dead-letter log) para lo que lleve tiempo (generación TTS larga, limpieza); horas en UTC, mostradas en la zona del usuario.
- Checklist de seguridad (aplicar entero): secretos solo en variables de entorno, `.env*` en `.gitignore`, nada en el bundle del cliente; validación de entrada en el servidor en cada ruta; autorización comprobada en cada lectura y escritura; rate limits en auth y en todo lo que genere audio (la GPU/CPU es el recurso escaso); uploads con límite de tamaño y tipo, servidos desde dominio o bucket separado; sin datos de usuario en URLs ni logs; dependencias auditadas; política de privacidad que liste cada procesador.
- Webhooks con firma verificada e idempotencia: no aplica si no hay webhooks; no inventar webhooks.

---

## 3. Skills CONDICIONADAS (9)

| Skill | Condición de uso | Aporte concreto cuando aplica |
|---|---|---|
| `documents` | Solo para los documentos del proyecto (SPEC, informe de licencias, informe de entrega), no para el build | Elegir formato según el lector (Word para editar, PDF para compartir fijo); trabajar desde el texto extraído con localización de fuente; citar cada hallazgo con archivo y página/sección; mantener fuente editable de cada archivo; verificar nombres, números, fechas y enlaces contra la fuente; comprobar el layout real de la salida antes de entregar |
| `local-document-skills` | Solo si algún entregable documental exige Word/PowerPoint/Excel/PDF (p. ej. informe de licencias en Word) | Regla 0: el documento se verifica renderizado, no por el código; regla de Carlos: una tabla no se parte entre páginas (si el corte es inevitable, la sección siguiente empieza en página nueva); revisar paginación, títulos huérfanos y tablas legibles antes de entregar; en Excel, fórmulas (no valores pegados) y recálculo comprobado; en PDF escaneado, declarar texto incompleto y usar OCR revisado |
| `local-gsap-skills` | Solo si el motion necesita más que CSS (timeline, ScrollTrigger, stagger); no por defecto | Animar transform y opacity; nunca layout (width/height/top/left) ni filter/boxShadow salvo exigencia del diseño; secuenciar con `gsap.timeline()`, no con cascadas de `setTimeout`; easing con intención (`power2.out` entradas, `power2.inOut` transiciones; stagger 0.05–0.1 s); `gsap.matchMedia()` por viewport y respetar `prefers-reduced-motion`; matar tweens y ScrollTriggers al desmontar; un trigger por sección, `start: "top 80%"`, `once: true` si no debe repetirse; leer el SKILL.md oficial en `~/workspace/skills/gsap-skills/skills/<nombre>/` antes de escribir animación, no reescribirlo de memoria; plugins GSAP 100% gratuitos desde 2025; si CSS basta, la transición CSS es la respuesta correcta |
| `local-emil-animations` | Solo dos de sus 5 módulos: `mobile-native` (Carlos usa el teléfono) y `break-ui` (datos extremos); `animate`/`review-animations`/`improve-animations` solo si el motion lo exige | `mobile-native`: que la web se sienta nativa en el teléfono (hover pegajoso, 100vh, zoom en inputs, taps lentos, notch); probar en hardware real cuando se pueda. `break-ui`: romper la UI con datos extremos (nombres de voz larguísimos, textos irrompibles, cero voces, emoji, números enormes) detrás de un toggle de demo e informar cada rotura con su fix. No instalados: `write-swift` y `animate-expo` (sin Swift ni React Native) |
| `local-humanizer` | Solo para el copy de la UI en español (etiquetas, estados vacíos, ayuda, mensajes de error) que suene a IA; nunca para código ni para textos académicos | Preservar el significado exacto (no añadir datos, no cambiar cifras, no suavizar afirmaciones); eliminar muletillas, palabras de moda de IA, etiquetas en negrita innecesarias y relleno; variar estructura y ritmo; evitar la plantilla "introducción, tres puntos, conclusión triunfal"; entregar solo la versión revisada y señalar cualquier cambio que altere el sentido. No es evasión de detectores y nunca se presenta como tal. Complemento de `redaccion_estilo_humano`, no sustituto |
| `redaccion_estilo_humano` | Solo para redactar el copy de la UI y la ayuda en español con voz humana; no para salidas técnicas, código o tablas | Variar la longitud de las oraciones (cortas de 5–8 palabras alternadas con largas de >25; no tres seguidas con la misma forma); conectar con puntuación antes que con conectores (repertorio sobrio y rotado: pero, aunque, pues, porque, ya que, así, de modo que, es decir, por ejemplo, en cambio); voz activa por defecto; verbos de postura (sostengo, la evidencia sugiere, a mi juicio); anclar cada afirmación general en un dato concreto; mostrar antes de abstraer; admitir matices y límites; cortar toda palabra que sobre (evaluar, no "llevar a cabo una evaluación"); dos pasadas (borrador + corrector con `references/anti-tics.md`); leer el texto en voz alta y reescribir lo que no suene a algo que una persona diría |
| `local-legal-skills` | Solo para el triaje de licencias y riesgos del proyecto (módulos `compliance-check` y `legal-risk-assessment`); NO es asesoría legal y sus módulos de NDA/contratos no aplican aquí | Regla 0: organiza, clasifica y señala riesgos; no sustituye a un abogado y no afirma cómo se resolvería un caso bajo la ley cubana ni ninguna otra. `compliance-check`: antes de lanzar, regulaciones aplicables, aprobaciones requeridas y áreas de riesgo (aquí: licencias de cada modelo TTS y de sus pesos, condiciones de uso no comercial, consentimiento de la segunda persona para clonar su voz). `legal-risk-assessment`: riesgo por severidad × probabilidad, con criterio de escalamiento explícito (qué puede resolver Carlos, qué necesita abogado). Cada entrega termina con nivel (verde/amarillo/rojo) y siguiente paso; toda referencia a norma concreta se verifica o se marca "por verificar para Cuba", nunca se presenta una norma extranjera como aplicable |
| `spoken_audio` | Solo para entregar a Carlos muestras de voz comparables en su teléfono (nota de voz con la muestra aprobada vs. la generada por el clon) | Escribir el texto hablado como debe sonar (números, horas y abreviaturas desarrolladas; sin Markdown ni citas en el texto hablado; enlaces y citas en el mensaje del chat que acompaña al audio); sintetizar con `/opt/hatch/bin/tts`; guardar bajo `~/workspace/`; comprobar que la síntesis terminó y que el archivo contiene las palabras previstas, y escuchar cuando importen pronunciación, ritmo o pulido; mantener aparte un render fallido o parcial y nunca entregarlo como terminado; adjuntar el archivo en su propia línea con enlace sandbox |
| `closed_generator_rule_check` | Solo si se usa un generador cerrado (Fish Audio, Gemini TTS, etc.) como oráculo de comparación de calidad de voz, o para verificar los controles reales del clon frente a las reglas vigentes | Listar primero todas las reglas vigentes por escrito, reescribiendo cada regla vaga en un comportamiento observable. Cruzar cada regla con los controles reales del diálogo de creación (no con la página de ayuda; si discrepan, manda el diálogo) en una matriz regla × control (soportado / no soportado / no probado); un campo de texto libre es una petición, no un control — nunca marcar "soportado" solo por el prompt. Verificar en fotogramas/frames (aquí: en muestras de audio), no desde el prompt; comprobar subtítulos y texto de diagrama como cosas distintas (aquí: inteligibilidad y similitud de locutor como cosas distintas). Entregar solo con un veredicto corto por regla (pasó / falló / sin probar) con la evidencia detrás; cuando una regla falle, nombrar el trade-off en términos llanos y ofrecer las alternativas reales antes de pedir veredicto a Carlos |

---

## 4. Skills NO ÚTILES (4)

| Skill | Motivo |
|---|---|
| `local-qc-video` | Puerta de vídeo (H.264 High level ≤ 4.0, yuv420p, CFR, faststart con `moov` antes que `mdat`, `blackdetect`, `freezedetect`, subtítulos ASS, conteo de frames, sincronía AV). El clon entrega **audio**, no vídeo. Ninguno de sus 12 gates aplica como tal. Nota: sus sub-reglas de audio (AAC-LC 48 kHz, sin silencios ≥ 0.5 s a -50 dB salvo cabeza/cola ≤ 1 s, **-16 LUFS ± 1 con pico real ≤ -1 dBTP**) ya están recogidas donde corresponden, en `narration_voice_design` (§2.7); no hace falta esta skill para usarlas. |
| `local-qc-photo` | Puerta fotográfica (perfil ICC, 300 PPI, PSD < 2 GB, `psd-tools`, RMSE < 3.0 contra master, capas con nombre real). Nada del clon es una foto. Sin aporte. |
| `game_clone_fidelity_gate` | Puerta de clon de **juego** (mecánicas contra el original, partidas sostenidas de minutos buscando actores atascados, arte juzgado por ojo contra frames originales). El clon es una herramienta web de audio, no un juego. Sin aporte. (Su principio genérico "juzgar el arte por ojo a tamaño real" ya lo cubren `delivery_audit_gate` e `impeccable`.) |
| `local-cinecode` | Hacer películas solo con código (un `film.html` por película, Chrome headless + ffmpeg, sonido Web Audio, máster -14 LUFS, espectador en frío). El entregable no es una película ni un vídeo. Sin aporte. |

---

## 5. Huecos: skills que NO existen y cómo se cubren

### 5.1. No hay skill de FastAPI / backend Python
**Hueco:** ninguna skill del catálogo enseña a construir una API FastAPI (rutas, validación con Pydantic, subida de archivos, streaming de audio, despliegue local con uvicorn, colas de generación).
**Cómo se cubre:**
- `replica-backend` (§2.14) aporta el checklist de seguridad y la disciplina de `.env.example`, auth y jobs — pero hay que **adaptar** sus partes de Supabase/Stripe (no aplican) a FastAPI/SQLite local, y esa adaptación debe quedar escrita en el SPEC del proyecto antes de codificar.
- `local-thermo-review` (§2.9) aporta la rúbrica de mantenibilidad del código Python.
- `delivery_audit_gate` (§2.8) verifica cada endpoint a través de la UI en el navegador vivo.
- Documentación oficial de FastAPI (docs.fastapi.tiangolo.com) como fuente primaria, leída en el momento de construir, no recordada.
- **Recomendación:** crear una skill local nueva `local-fastapi-basico` (plantilla de `custom_connector_setup` / skill template) con: estructura de proyecto, validación Pydantic, subida de audio con límites, streaming de WAV, manejo de errores y despliegue con uvicorn + systemd. No es urgente para la fase de diseño; sí antes de escribir el backend.

### 5.2. No hay skill de TTS local / clonación de voz con modelos open-source
**Hueco:** ninguna skill cubre elegir, instalar, correr y evaluar un modelo TTS local (XTTS-v2, Chatterbox, F5-TTS, Kokoro…), ni la clonación few-shot (audio de referencia, embedding de locutor, similitud, WER), ni el QC de audio generado.
**Cómo se cubre (combinación de 4 skills, ninguna basta sola):**
- `wide-research` (§2.10) para la comparativa paralela de modelos con esquema común.
- `local-repo-radar` (§2.12) para vetar cada repo (licencia permisiva, actividad, adopción, auditoría de seguridad). Ojo: la licencia del repo y la de los **pesos** pueden diferir; verificar ambas, y las cláusulas de uso no comercial.
- `provider_model_verification` (§2.11) adaptada: "catálogo vivo" = repo/release del día; "llamada de tamaño real" = generar 30–60 s de español con la voz clonada en el hardware disponible antes de asignar el modelo; registrar modelo pedido vs. modelo que respondió, fuente y fecha.
- `narration_voice_design` (§2.7) adaptada: el "objeto persistente" del proveedor se sustituye por **embedding de locutor + audio de referencia archivado**; la muestra aprobada por oído de Carlos sigue siendo la puerta.
- `transcribe_recordings` (§2.13) como oráculo de inteligibilidad (WER aproximado contra el texto de entrada normalizado).
- **Recomendación:** crear una skill local nueva `local-tts-local` con: matriz de modelos candidatos y licencias, instalación por modelo (venv, VRAM), protocolo de clonación (duración mínima del audio de referencia, limpieza, consentimiento archivado de la segunda persona), QC de audio generado (inteligibilidad vía Whisper, similitud de locutor, loudness -16 LUFS / pico ≤ -1 dBTP, sin silencios ni artefactos) y registro de voces (prompt, embedding, muestra aprobada). Esta skill es el entregable de conocimiento que falta y debe escribirse con los resultados reales de la comparativa, no antes.

### 5.3. No hay skill de QC de audio (solo de vídeo y de foto)
**Hueco:** `local-qc-video` y `local-qc-photo` son puertas de archivo final para vídeo y foto; no existe su equivalente para un WAV/MP3 generado (silencios, clipping, loudness, artefactos, truncamiento).
**Cómo se cubre:** con las sub-reglas de audio ya existentes — loudness -16 LUFS ± 1 y pico real ≤ -1 dBTP (`narration_voice_design`), silencio ≥ 0.5 s a -50 dB como fallo salvo pausa natural declarada (`local-qc-video`, audio), verificación por transcripción (`transcribe_recordings`) y escucha completa como espectador (`narration_voice_design`, `delivery_audit_gate`). **Recomendación:** el gate de audio debe quedar codificado como sección del SPEC y, a medio plazo, como script `qc-audio.sh` análogo a `qc-video.sh`, dentro de la skill `local-tts-local` propuesta.

### 5.4. No hay skill de SPA estática / GitHub Pages
**Hueco:** ninguna skill cubre publicar una SPA estática en GitHub Pages (build sin bundler, rutas relativas, caché, HTTPS, dominio propio).
**Cómo se cubre:** es trabajo estándar de frontend estático; lo cubren `local-frontend-design` (estructura), `local-impeccable` (piso de calidad) y `delivery_audit_gate` (verificación en navegador vivo, con cache-buster). El despliegue en sí lo hace Carlos desde su teléfono o el agente por push al repo, con la regla permanente: el push requiere autorización explícita de Carlos en cada caso. No justifica una skill nueva salvo que el despliegue se repita.

### 5.5. No hay skill de consentimiento para clonación de voz
**Hueco:** clonar la voz de otra persona exige su consentimiento explícito y archivado; ninguna skill lo regula.
**Cómo se cubre:** `local-legal-skills` (§3, módulos `compliance-check` y `legal-risk-assessment`) para el triaje de riesgo, más una regla de proyecto escrita en el SPEC: **sin consentimiento explícito y archivado de la segunda persona, su voz no se clona ni se almacena**; el audio de referencia se guarda solo con ese consentimiento y se borra si lo retira. Esto es una regla del proyecto, no asesoría legal.

---

## 6. Orden de aplicación recomendado para los agentes de diseño y frontend

1. **Investigación de modelos** (antes de diseñar): `wide-research` + `local-repo-radar` + `provider_model_verification` adaptada → matriz de modelos TTS con licencia, hardware y calidad.
2. **Sistema de diseño**: `local-design-extract` (extraer el sistema de ElevenLabs) → `local-ui-ux-pro-max` (`--design-system --persist`, diales: densidad alta, motion bajo) → `local-frontend-design` (identidad propia) → `local-taste` (solo sorteo de dirección + inspección; avisar del coste antes de una build completa).
3. **Construcción**: `local-impeccable` (piso de calidad, leer `craft-floor.md` antes de editar) + `local-thermo-review` (revisiones duras puntuales) + `replica-backend` (checklist de seguridad del FastAPI).
4. **Voces**: `narration_voice_design` adaptada a local (prompt aprobado → embedding + referencia archivados → muestra aprobada por oído) + `transcribe_recordings` (inteligibilidad).
5. **Puertas antes de entregar**: `local-web-design-guidelines` (auditoría de código, reglas frescas de Vercel) → `delivery_audit_gate` (todas las funciones en navegador vivo, en el teléfono de Carlos) → QC de audio (§5.3).
6. **Condicionadas solo si su condición se cumple**: `local-gsap-skills` y `local-emil-animations` (motion y móvil), `local-humanizer` + `redaccion_estilo_humano` (copy en español), `documents` / `local-document-skills` (documentos del proyecto), `local-legal-skills` (licencias y consentimiento), `spoken_audio` (muestras comparables), `closed_generator_rule_check` (solo si hay un generador cerrado como oráculo).

---

## 7. Fuentes consultadas

- `muse.skill_search`: 10 consultas (diseño UI frontend; TTS/voz/narración; investigación paralela; documentos; QC audio/vídeo; clonación de voz; FastAPI/backend; licencias open-source; animación GSAP; humanizar texto).
- `SKILL.md` leídos completos (27): local-ui-ux-pro-max, local-frontend-design, local-impeccable, local-taste, local-design-extract, local-web-design-guidelines, narration_voice_design, wide-research, local-qc-video, documents, local-gsap-skills, local-emil-animations, local-humanizer, redaccion_estilo_humano, local-legal-skills, local-thermo-review, delivery_audit_gate, local-document-skills, provider_model_verification, replica-backend, closed_generator_rule_check, game_clone_fidelity_gate, local-qc-photo, local-cinecode, local-repo-radar, transcribe-recordings, spoken-audio.
- Reglas permanentes de Carlos aplicadas: presupuesto cero (solo gratuitas/open-source); verificación en navegador real antes de entregar; copiar solo sistemas de diseño, nunca contenido, textos, logos ni marcas; push al repo solo con autorización explícita; Whisper normaliza grafías fonéticas (comparar normalizado).
