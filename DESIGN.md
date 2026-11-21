# DESIGN.md — Sistema de diseño y UI/UX del clon web de ElevenLabs

**Proyecto:** clon web privado de ElevenLabs (2 usuarios: Carlos y otra persona).
**Fecha:** 2026-11-20. **Idioma del documento:** español.
**Estado:** diseño aprobado para construir. Nada de este documento es entrega
final: el frontend debe verificarse en navegador real antes de entregarse
(regla permanente de Carlos).
**Presupuesto:** cero. Solo herramientas gratuitas / open-source.

## Fuentes de este diseño

| Fuente | Qué aporta aquí |
|---|---|
| `RESEARCH.md` | Modelos ganadores: Kokoro-82M (CPU, narración rápida), Qwen3-TTS-12Hz-1.7B-Base (clonación zero-shot GPU, 3 s), VoxCPM2 (máxima calidad, 48 kHz, LoRA), retador ZONOS3-Mini. Chatterbox RETIRADO: no se usa como modelo en ningún sitio de este diseño. |
| `FEATURE_MAP.md` | 25 funciones mapeadas; fases 1–4 de prioridad. Este diseño cubre Fase 1 (TTS, clonación, Voice Design, History) + las pantallas pedidas (STS, Dubbing, SFX, Settings). |
| `SKILL_AUDIT.md` | Orden de aplicación de skills (§6) y reglas extraídas. |
| `local-ui-ux-pro-max` | Sistema de diseño, prioridades 1→10, diales. Búsqueda ejecutada 2026-11-20: estilo Minimalism & Swiss, densidad 8, motion 2, variance 4. Su paleta rojo/azul era un match genérico de la base de datos y **no** se adopta: la paleta de este documento es propia, con contrastes medidos (ver §3.1). |
| `local-design-extract` | Mecanismo copiar-y-mejorar el sistema de elevenlabs.io: se toman estructura oscura, densidad, jerarquía y motion; NUNCA logo, marca, textos de marketing, nombres de voces ni copy. Atribución honesta: «sistema de diseño de referencia: elevenlabs.io, adaptado y optimizado». La extracción con el CLI `designlang` queda como paso opcional del agente de frontend (la web de referencia estaba bloqueada para lectura directa en la sesión de investigación). |
| `local-frontend-design` | Identidad con punto de vista: ancla temática (§1), héroe = estudio de voz, tipografía con personalidad. |
| `local-impeccable` | Piso anti-genérico (`craft-floor.md`): contraste, estados obligatorios, rechazos por defecto. Modo **Operate** (herramienta), no Persuade. |
| `local-taste` | Sorteo de dirección (solo sorteo + inspección, sin build completa por su coste). Sorteo 2026-11-21, sector `ai-product`, semilla 1901657989: **«The well-kept board»** — tablero de baldosas, una sola nota saturada (amarillo), tipografía Schibsted Grotesk, composición de tablero 2×2. Se adopta adaptado (ver §2). |
| `local-web-design-guidelines` | Auditoría de código contra las guías de Vercel: el agente de frontend debe traer las reglas frescas de `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md` antes de auditar. Si la lectura falla, se para: no se audita de memoria. |
| `narration_voice_design` (adaptada) | Cada voz se diseña en papel antes de generarse; la muestra aprobada por oído es «la voz»; loudness de entrega **-16 LUFS, pico real ≤ -1 dBTP**; bloques cortos verificados. |
| `delivery_audit_gate` | Puerta de entrega: cada función se prueba en navegador vivo, en el teléfono de Carlos, con checklist completa repetida tras cada fix. |

---

## 1. Marca: nombre y identidad

### 1.1 Ancla temática (local-frontend-design)

> **De qué trata:** un taller de voces que vive en tu bolsillo: escribes, eliges
> una voz (tuya, clonada o diseñada) y suena.
> **Para quién:** Carlos y una segunda persona, desde el teléfono, en español.
> **Trabajo principal:** convertir texto en voz que suene a persona, no a robot.

Las decisiones visuales salen de ese mundo —**el estudio de grabación y la
mesa de mezclas**— no de la categoría «otra landing de SaaS»: la forma de
onda es el motivo visual central (no un degradado decorativo), los controles
son faders y perillas de consola, y la jerarquía es la de una mesa de trabajo:
voz → texto → generar → escuchar.

### 1.2 Tres opciones de nombre

| # | Nombre | Justificación | Riesgos |
|---|---|---|---|
| **1** | **Sonora** | Corto (6 letras), español, evoca sonido y sonoridad sin decir «voz» de forma literal; funciona como marca («Sonora — tu taller de voces») y como dominio corto; no copia nada de ElevenLabs. | La palabra existe como topónimo y en otras marcas de audio; para uso privado sin distribución pública el riesgo es nulo, pero si algún día se publicara habría que verificar disponibilidad. |
| **2** | **VozPropia** | Descriptivo y honesto: el valor del clon es que la voz es tuya (clonada o diseñada), no alquilada de un catálogo. Inmediato de entender para la segunda persona. | Largo, poco distintivo como marca, suena a eslogan más que a nombre; difícil de convertir en logotipo compacto. |
| **3** | **Ecovoz** | Juego con «eco» (la voz que vuelve) + voz; corto, memorable, español. | «Eco» puede leerse como reverberación o como ecología; más frío y menos cálido que Sonora. |

### 1.3 Recomendación: SONORA

**Nombre recomendado: Sonora.** Logotipo tipográfico (sin símbolo dibujado):
la palabra «Sonora» en Schibsted Grotesk 800, tracking -0.05em, en tinta
clara sobre fondo oscuro, con el punto de la «i» sustituido por un punto
ámbar (`--accent`) — el único acento de color de toda la interfaz. Eslogan
(propio, no copiado): **«Tu voz, en tus manos.»**

**Nunca:** copiar el logo, la marca, los textos de marketing, los nombres de
voces ni los nombres de modelos de ElevenLabs. Las voces del clon se nombran
por su origen real: voces fijas de Kokoro conservan su identificador técnico
(`ef_dora`…); las clonadas llevan el nombre que les ponga su dueño; las
diseñadas, el nombre que les ponga quien las creó. Los modelos se nombran por
su nombre real (Kokoro-82M, Qwen3-TTS, VoxCPM2): son nombres técnicos, no
marca del clon.

---

## 2. Dirección de arte (local-taste, adaptada)

Sorteo «The well-kept board»: la página es **un tablero de baldosas ajustadas**,
cada baldosa una sola cosa (la voz, el texto, el reproductor, el estado del
backend). Se adopta así, con dos adaptaciones declaradas por conflicto con
restricciones del proyecto:

1. **El sorteo trae tema claro (fondo hueso, tinta verde botella, amarillo).**
   El proyecto exige tema oscuro como ElevenLabs. Se transpone: la tinta
   botella pasa a ser el fondo oscuro, el hueso pasa a ser el texto claro,
   y **el amarillo queda como la única nota saturada** (el acento). La
   disciplina de «un solo acento» se conserva intacta.
2. **El sorteo es de landing (hero 2×2, secciones, testimonios, pricing).**
   El clon es una **app Operate**, no una landing: no hay hero de marketing,
   ni testimonios, ni precios. Del sorteo se toma la **geometría** (baldosas,
   gaps de 8 px, un solo radio, texto arriba-izquierda, nada centrado sin
   motivo) y se aplica al tablero de trabajo, no a una landing.

**Frase del tablero:** «En esta página, la mesa de mezclas se convierte en
tablero de baldosas: cada control es una baldosa y la onda es la imagen.»
**La única cosa viva:** el estudio de voz — caja de texto + selector de voz +
botón Generar — es lo primero que se ve al abrir la app. No hay pantalla de
bienvenida ni marketing.

---

## 3. Sistema de diseño

### 3.1 Paleta (tema oscuro, un solo acento)

Fondo oscuro denso como ElevenLabs, pero con el acento ámbar de la dirección
sorteada en lugar del acento frío habitual. Un solo color de acento; los
demás colores son semánticos y solo aparecen en su estado (éxito, error,
grabando, reproduciendo).

| Token | Valor | Uso | Contraste medido |
|---|---|---|---|
| `--bg` | `#0B0D10` | Fondo de página | — |
| `--surface` | `#14181D` | Tarjetas, paneles, baldosa | texto sobre ella 15.47:1 |
| `--surface-raised` | `#1A1F26` | Elementos elevados (reproductor, modal, menú) | texto sobre ella 14.38:1 |
| `--surface-sunken` | `#0E1114` | Campos de texto, áreas hundidas | — |
| `--border` | `#262D36` | Bordes y divisores (1 px) | — |
| `--border-strong` | `#39424E` | Borde en hover / foco de campo | — |
| `--text` | `#EDEFF2` | Texto principal | 16.89:1 sobre `--bg` |
| `--text-muted` | `#A7B0BA` | Texto secundario, etiquetas, ayuda | 8.86:1 sobre `--bg`, 8.12:1 sobre `--surface` |
| `--text-faint` | `#7C8794` | Solo metadatos no esenciales (timestamps) — nunca cuerpo | 5.06:1 sobre `--bg` (ver nota) |
| `--accent` | `#FACC15` | **Único acento**: CTA principal, foco, onda activa, punto de la «i» | texto `#111` sobre él 12.33:1 |
| `--accent-ink` | `#111111` | Texto sobre acento | — |
| `--accent-dim` | `#FACC1526` | Fondo suave de acento (26 = ~15% alpha) | — |
| `--success` | `#7DD3C8` | Éxito, backend online, voz lista | 11.14:1 sobre `--bg` |
| `--danger` | `#F87171` | Error, borrar, backend offline | 7.03:1 sobre `--bg` |
| `--info` | `#38BDF8` | Información, modelo en cola | 9.08:1 sobre `--bg` |
| `--recording` | `#EF4444` | Grabando (punto rojo + temporizador) | solo como indicador, nunca como texto |

**Contrastes verificados por cálculo WCAG el 2026-11-20** (todos ≥ 4.5:1 para
texto normal; el par más débil es `--text-faint` 5.33:1, por eso solo se usa
en metadatos). Regla: nunca gris sobre color, nunca texto de cuerpo
< 12 px, nunca hex crudo en componentes — siempre tokens semánticos.

**Mejora sobre el original (local-design-extract, eje 2):** ElevenLabs usa
acentos fríos y grises medios con contraste justo en secundarios; aquí todos
los secundarios superan 8:1 y el foco es visible siempre (anillo ámbar de
2 px + offset), no solo en hover.

### 3.2 Tipografía

Dos familias, claramente distintas (local-frontend-design):

| Rol | Familia | Pesos | Uso |
|---|---|---|---|
| Display / marca | **Schibsted Grotesk** (sorteo taste) | 800 (marca y títulos de pantalla), 600 | Nombre «Sonora», títulos de pantalla, números grandes del reproductor |
| Texto / UI | **Inter** | 400 (cuerpo), 500 (etiquetas), 600 (botones y navegación) | Todo lo demás |

Escala (base 16 px, interlineado 1.5 en cuerpo; medida 65–75 caracteres por
línea en textos largos):

| Token | Tamaño | Uso |
|---|---|---|
| `--fs-display` | `clamp(2rem, 1.3rem + 3.2vw, 4rem)` | Nombre en la cabecera de escritorio |
| `--fs-h1` | 24 px / 1.3 | Título de pantalla |
| `--fs-h2` | 18 px / 1.35 | Título de sección / baldosa |
| `--fs-body` | 16 px / 1.5 | Cuerpo, texto a sintetizar |
| `--fs-small` | 14 px / 1.45 | Etiquetas, metadatos, ayuda |
| `--fs-caption` | 13 px / 1.4 | Mínimo admitido (taste: nunca < 13 px). Timestamps, pies |

**Carga de fuentes:** Google Fonts con `display=swap` y pila de reserva del
sistema (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`) — si la
fuente no carga (conexión limitada en Cuba), el layout no se rompe. Sin
fuentes de pago. Sin texto con degradado (rechazo impeccable).

### 3.3 Espaciado, radios, sombras

Escala de espaciado (densidad alta, dial 8 de ui-ux-pro-max, panel-herramienta):
`4 · 8 · 12 · 16 · 24 · 32 · 48 px`. Base de layout: múltiplos de 8 px; gaps
de tablero 8 px (móvil 6 px). Ritmo consistente: no mezclar 10 px con 12 px.

| Token | Valor |
|---|---|
| `--radius-sm` | 6 px (chips, badges) |
| `--radius-md` | 10 px (botones, inputs, tarjetas) — **un solo radio de tarjeta en toda la app** |
| `--radius-lg` | 14 px (reproductor, modal) |
| `--radius-full` | 999 px (avatar de voz, punto de grabación) |
| `--shadow-1` | `0 1px 2px rgb(0 0 0 / .4)` |
| `--shadow-2` | `0 4px 16px rgb(0 0 0 / .45)` (elevados) |
| `--shadow-3` | `0 12px 32px rgb(0 0 0 / .5)` (modal) |

Sombras con desplazamiento y blur suave; nunca sombras duras de bloque.
Bordes de 1 px, nunca bordes laterales de color > 1 px. Sin glassmorphism
decorativo, sin tarjetas anidadas, sin tarjetas idénticas icono+título+texto
como estructura (impeccable).

### 3.4 Motion (motion bajo, dial 2)

Un solo momento de movimiento por pantalla: **la forma de onda al reproducir
o generar**. Todo lo demás es micro-interacción discreta.

| Token | Valor | Uso |
|---|---|---|
| `--dur-fast` | 120 ms | Hover de botones, cambio de estado de icono |
| `--dur-base` | 200 ms | Transiciones de paneles, apertura de selector |
| `--dur-slow` | 350 ms | Entrada de reproductor / cambio de pantalla |
| `--ease-out` | `cubic-bezier(.22, 1, .36, 1)` | Entradas |
| `--ease-in-out` | `cubic-bezier(.65, 0, .35, 1)` | Transiciones de estado |

Reglas: animar solo `transform` y `opacity`, nunca `width`/`height`; un solo
timing por transición no vale (cada duración tiene su uso); respetar
`prefers-reduced-motion` (sin animación: mostrar el estado final de inmediato);
nunca cambios de estado instantáneos (0 ms) sin feedback; el botón Generar
muestra progreso real (porcentaje o barra), nunca un spinner sin contexto.
GSAP solo si el motion necesita más que CSS (condicionado, skill
`local-gsap-skills`): por defecto CSS basta.

### 3.5 Breakpoints y layout base

Mobile-first (Carlos trabaja desde el teléfono). Sin scroll horizontal, sin
anchos fijos en px para contenedores, sin desactivar el zoom.

| Breakpoint | Ancho | Layout |
|---|---|---|
| Móvil | 360–767 px | Una columna; navegación inferior (≤ 5 ítems); estudio a pantalla completa |
| Tableta | 768–1023 px | Una columna ancha (máx. 720 px) + panel lateral colapsable |
| Escritorio | ≥ 1024 px | Sidebar izquierda 264 px + contenido máx. 960 px; tablero de 2 columnas |

Área segura: `env(safe-area-inset-*)` en la navegación inferior y el
reproductor fijo. `100dvh` (no `100vh`) para pantallas completas en móvil.
Inputs de texto con `font-size ≥ 16 px` para que iOS/Android no hagan zoom
al enfocar (local-emil-animations, `mobile-native`).

### 3.6 Tokens CSS (copiar tal cual al frontend)

```css
:root {
  /* Color */
  --bg: #0B0D10; --surface: #14181D; --surface-raised: #1A1F26;
  --surface-sunken: #0E1114; --border: #262D36; --border-strong: #39424E;
  --text: #EDEFF2; --text-muted: #A7B0BA; --text-faint: #7C8794;
  --accent: #FACC15; --accent-ink: #111111; --accent-dim: #FACC1526;
  --success: #7DD3C8; --danger: #F87171; --info: #38BDF8;
  --recording: #EF4444;
  /* Tipografía */
  --font-display: "Schibsted Grotesk", system-ui, sans-serif;
  --font-body: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --fs-display: clamp(2rem, 1.3rem + 3.2vw, 4rem);
  --fs-h1: 1.5rem; --fs-h2: 1.125rem; --fs-body: 1rem;
  --fs-small: 0.875rem; --fs-caption: 0.8125rem;
  --lh-body: 1.5; --lh-tight: 1.3;
  /* Espaciado / forma */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-6: 24px; --space-8: 32px; --space-12: 48px;
  --radius-sm: 6px; --radius-md: 10px; --radius-lg: 14px; --radius-full: 999px;
  --shadow-1: 0 1px 2px rgb(0 0 0 / .4);
  --shadow-2: 0 4px 16px rgb(0 0 0 / .45);
  --shadow-3: 0 12px 32px rgb(0 0 0 / .5);
  /* Motion */
  --dur-fast: 120ms; --dur-base: 200ms; --dur-slow: 350ms;
  --ease-out: cubic-bezier(.22, 1, .36, 1);
  --ease-in-out: cubic-bezier(.65, 0, .35, 1);
  /* Táctil */
  --tap-min: 44px;
}
```

---

## 4. Componentes

Todos los componentes existen en los 5 estados obligatorios (impeccable):
**reposo, hover, foco visible, disabled, loading, error y vacío** — también el
reproductor, la cola de generación y el formulario de clonación. Iconos
siempre SVG (Lucide/Heroicons); nunca emoji como iconos. Sin kicker/eyebrow
sobre cada título (ban absoluto).

### 4.1 Botones

| Variante | Estilo | Uso |
|---|---|---|
| Primario | Fondo `--accent`, texto `--accent-ink`, 600, radio md, altura 48 px (móvil) / 44 px (escritorio) | Generar, Clonar voz, Guardar |
| Secundario | Fondo `--surface-raised`, borde `--border-strong`, texto `--text` | Descargar, Duplicar, Cancelar |
| Fantasma | Sin fondo, texto `--text-muted`, hover → `--text` | Acciones de lista (renombrar, borrar) |
| Peligro | Texto `--danger`, hover fondo `--danger` al 12% | Borrar voz / borrar historial |
| Solo-icono | 44×44 px mínimo, siempre con `aria-label` visible para lector de pantalla | Reproducir/pausar en listas |

Foco: anillo 2 px `--accent` + offset 2 px, nunca eliminado. Disabled:
opacidad .45 + `cursor: not-allowed` + motivo visible («Generar» deshabilitado
sin texto y sin voz muestra el motivo debajo, no solo gris). Loading: el
botón muestra progreso («Generando… 42%») y queda deshabilitado hasta
terminar; el estado nunca cambia en 0 ms sin feedback.

### 4.2 Inputs y formularios

- Etiqueta visible siempre encima del campo (nunca solo placeholder).
- Campo de texto: fondo `--surface-sunken`, borde `--border`, radio md,
  padding 12–16 px, `font-size: 16px` (anti-zoom móvil), caret ámbar,
  selección ámbar al 25%.
- Error junto al campo, en `--danger`, con icono y texto concreto
  («El texto está vacío» / «Máximo 10.000 caracteres, llevas 10.412»).
- Texto de ayuda debajo del campo en `--text-muted`.
- Contador de caracteres en vivo (TTS: `n / 10.000`), con aviso a los 9.000.
- Textarea del estudio: altura mínima 160 px, redimensionable vertical,
  contador y botón «Limpiar» fantasma.
- Subida de audio: zona de soltar grande (mín. 120 px de alto, 44 px el
  botón Examinar), acepta WAV/MP3/FLAC/OGG, límite visible («máx. 25 MB,
  3 s – 2 min»), con validación inmediata de duración y formato antes de
  subir nada.

### 4.3 Sliders (estabilidad, similitud, velocidad, estilo)

- Slider propio (no el nativo sin estilizar): pista 6 px `--border`,
  relleno ámbar hasta el valor, pulgar 24 px (área táctil 44 px),
  valor numérico visible a la derecha (`0,75`), etiqueta encima.
- Cada slider lleva su escala y su efecto explicado en una línea
  («Estabilidad 0,75 — voz consistente, menos expresiva»).
- Pasos: 0,05. Teclado: flechas cambian el valor; `aria-valuetext` con el
  valor y su significado.
- Rangos (según FEATURE_MAP §1): velocidad 0,5–2,0 (defecto 1,0);
  estabilidad 0–1 (defecto 0,5); similitud/claridad 0–1 (defecto 0,75);
  exageración de estilo 0–1 (defecto 0, solo Qwen3-TTS/VoxCPM2).
  Los sliders que un modelo no soporta se muestran deshabilitados con el
  motivo («Kokoro no usa estabilidad»), no se ocultan: ocultar rompe la
  memoria muscular.

### 4.4 Selector de voz y tarjetas de voz

**Selector (en el estudio):** botón ancho que abre un panel (bottom-sheet
en móvil, desplegable en escritorio) con buscador, filtros por origen
(Todas / Fijas / Clonadas / Diseñadas) e idioma, y lista de voces. Cada
fila: avatar circular con inicial o onda, nombre, origen + modelo
(«Clonada · Qwen3-TTS»), idioma, botón de vista previa (play 44 px) y
estrella de favorita. La voz activa lleva borde ámbar de 1 px + marca.

**Tarjeta de voz (Voice Lab):** baldosa con avatar, nombre, origen, idioma,
duración de la muestra, fecha de creación, botones Reproducir muestra /
Usar en estudio / Renombrar / Borrar. Sin tarjetas anidadas ni rejilla de
tarjetas idénticas icono+título+texto como única estructura: la lista es
una lista (filas), no una parrilla decorativa.

**Voces fijas de Kokoro:** se marcan con su identificador técnico
(`ef_dora`, `em_alex`, `em_santa` para español) y una nota honesta:
«Español limitado a 3 voces» (RESEARCH.md §2.1). No se inventan nombres
comerciales para ellas.

### 4.5 Reproductor de audio

Fijo en la parte inferior (móvil) o integrado en la baldosa de resultado
(escritorio). Controles: reproducir/pausar (44 px), barra de progreso con
forma de onda (la onda es ámbar al reproducir, gris en reposo; clic o
arrastre para buscar), tiempo `0:12 / 0:47`, velocidad (0,5×–2×), volumen,
descargar (MP3/WAV según lo generado) y «Usar este audio como referencia».
Muestra metadatos: voz, modelo, duración, caracteres, fecha, loudness
(«-16 LUFS» cuando el backend lo devuelve). Estado de carga: esqueletos
con espacio reservado (CLS < 0,1), nunca salto de layout. Sin autoplay.
Pausa al salir de la pantalla o al ocultar la pestaña.

### 4.6 Tablas de historial

Móvil: lista de filas (no tabla): cada ítem muestra título (primeras
palabras del texto), voz, modelo, duración, fecha relativa («hoy 14:32»),
botón play y menú (Descargar / Re-generar / Borrar). Escritorio: tabla
real con columnas Texto | Voz | Modelo | Duración | Fecha | Acciones,
ordenable por fecha y filtrable por voz y tipo (TTS / diálogo / SFX /
doblaje). Paginación de 50 por página (según FEATURE_MAP §16). Vacío:
«Aún no has generado nada — escribe tu primer texto en el Estudio»
con botón al Estudio. Borrado con confirmación («Borrar también el audio»
con checkbox, por defecto marcado).

### 4.7 Estados globales

| Estado | Tratamiento |
|---|---|
| Vacío | Ilustración de onda en SVG (no foto), una frase y una acción. Nunca una pantalla en blanco. |
| Cargando | Esqueleto con el espacio reservado + texto de progreso real. Nunca spinner solo. |
| Error | Tarjeta `--danger` suave: qué pasó, por qué (si se sabe) y qué hacer («Reintentar», «Revisar la URL del backend»). El error del backend 503 dice «arranca el backend GPU», no un código genérico. |
| Sin conexión | Ver §6 (estado degradado). |
| Éxito | Confirmación breve junto a la acción (toast 4 s, con botón Deshacer cuando aplica: borrar voz, borrar historial). |

---

## 5. Accesibilidad (prioridad 1 de ui-ux-pro-max)

- Contraste ≥ 4.5:1 en texto (≥ 3:1 en texto grande); medido en §3.1.
- Táctil ≥ 44×44 px, separación ≥ 8 px entre objetivos táctiles.
- Navegación por teclado completa: foco visible siempre, orden lógico,
  `Esc` cierra paneles y modales, foco devuelto al elemento que abrió el modal.
- `aria-label` en todo botón solo-icono; `role="status"` / `aria-live="polite"`
  en el estado de generación y en el indicador de backend; `aria-valuetext`
  en sliders; la onda del reproductor tiene alternativa textual
  («Audio de 47 segundos, voz …»).
- Sin dependencia del hover: todo lo que existe en hover existe también por
  toque y por teclado. Sin dependencia del color solo: el estado online
  es punto verde + texto «En línea», no solo color.
- `prefers-reduced-motion`: sin animación, estado final inmediato.
- Texto alternativo en toda imagen decorativa (`aria-hidden` si es
  puramente decorativa). Sin desactivar el zoom. Meta viewport correcto.
- Formularios: etiqueta visible, error junto al campo, ayuda contextual.
- Idioma de la página declarado (`lang="es"`, ver §7).

---

## 6. Layout general y estado del backend

### 6.1 Estructura

```
┌──────────────────────────────────────────────────────┐
│ Cabecera: Sonora · [● En línea · Qwen3-TTS] [Ajustes]│  ← escritorio: sidebar
├──────────┬───────────────────────────────────────────┤
│ Estudio  │                                           │
│ Voice Lab│        PANTALLA ACTIVA                    │
│ Voz a voz│        (tablero de baldosas)              │
│ Doblaje  │                                           │
│ Efectos  │                                           │
│ Historial│                                           │
│ Ajustes  │                                           │
└──────────┴───────────────────────────────────────────┘
│ Reproductor fijo (cuando hay audio)                  │
└──────────────────────────────────────────────────────┘
Móvil: navegación inferior con 5 ítems (Estudio, Voces, Doblaje,
Historial, Ajustes); Voz a voz y Efectos dentro de «Más» o como
segunda fila del menú; deep linking por hash (#/estudio, #/voces…),
botón Atrás predecible.
```

Navegación inferior ≤ 5 ítems (ui-ux-pro-max §9). El indicador de backend
vive en la cabecera, siempre visible: punto + texto + modelo activo
(«● En línea · Qwen3-TTS 1.7B» / «● CPU · Kokoro» / «○ Sin conexión»).
Toca el indicador para ver detalle: URL del backend, latencia del último
`/health`, modelos cargados, VRAM libre.

### 6.2 Estado degradado: backend apagado (Kaggle no corre)

Es el estado normal la mitad del tiempo (sesiones Kaggle de máx. 12 h, URL
del túnel que cambia por sesión). El diseño lo trata como primer ciudadano,
no como error:

- Banner persistente en la parte superior, en `--info` suave (no rojo
  alarmista): «Backend sin conexión — solo funcionan las voces rápidas en
  este dispositivo. Arranca el notebook de Kaggle y pega la URL en Ajustes.»
  con botones «Abrir Ajustes» y «Reintentar».
- Lo que sigue funcionando: nada que exija GPU — en la práctica, la SPA
  entera en modo lectura (historial local, voces guardadas, textos
  guardados) y cualquier generación que el backend CPU local pueda hacer
  si existe; si no hay backend en absoluto, **todo lo que genera se
  deshabilita con el motivo visible**, no se esconde.
- Lo que se deshabilita (con motivo, no oculto): Generar con voz clonada
  o VoxCPM2 («necesita GPU»), Clonar voz, Doblaje, Efectos, Voz a voz.
  El botón Generar con Kokoro queda activo solo si el backend CPU
  (InstaBox) está en línea; si no, también deshabilitado con motivo.
- Los audios ya generados se reproducen y descargan siempre (son archivos
  locales): el historial nunca se bloquea por falta de backend.
- Al volver el backend: el banner desaparece, los botones se reactivan y
  aparece un toast «Backend en línea · Qwen3-TTS 1.7B listo».
- La URL del backend nunca se hardcodea: vive en Ajustes (ver §6.9) y se
  guarda en `localStorage`. Cada arranque de Kaggle = pegar la URL nueva
  del túnel (trycloudflare) o reutilizar la fija (ngrok).

---

## 7. Idioma de la UI — decisión

**Recomendación: español, solo español, en la v1. Sin selector de idioma.**

Razonamiento:

1. **Los dos usuarios son hispanohablantes** (Carlos y la segunda persona).
   La UI es una herramienta privada, no un producto público: no hay
   audiencia en inglés que atender.
2. **Los canales de Carlos son en inglés, pero el clon no es un canal.**
   El inglés de los vídeos es contenido para el público; la herramienta
   que los produce puede (y debe) estar en el idioma en que Carlos piensa
   y decide. Mezclar idiomas en una herramienta de trabajo genera fricción
   en cada error y cada ajuste.
3. **El español es además el idioma fuerte de los modelos elegidos**
   (Qwen3-TTS y VoxCPM2 con español nativo): los textos de ayuda, los
   ejemplos y las etiquetas de emoción se escriben en español sin traducir
   conceptos.
4. **Coste cero de i18n:** un selector de idioma duplica el copy, los
   estados de error y las pruebas (delivery_audit_gate probaría cada
   función dos veces). Para 2 usuarios es trabajo inútil; si algún día
   hace falta, el copy vive en un solo archivo `es.json` y se añade `en.json`.

**Excepciones (se mantienen en inglés, sin traducir):** nombres técnicos de
modelos (`Kokoro-82M`, `Qwen3-TTS`), identificadores de voces fijas
(`ef_dora`), términos de audio sin equivalente asentado (`loop`, `pitch`
acompañado de su explicación en español), y los endpoints de la API.
Los mensajes de error del backend se muestran en español en la UI aunque el
backend los devuelva en inglés (mapeo en el frontend).

---

## 8. Pantallas: layout y flujos

Convención de los wireframes: `[ ]` botón, `( )` campo, `~~~` onda de audio,
`▸` reproducir, `●` estado. Móvil primero: cada wireframe es la vista de
teléfono (360 px); la nota de escritorio dice qué cambia.

### 8.1 Estudio TTS (pantalla principal, `#/estudio`)

El héroe manda: lo primero es la caja de texto + voz + Generar. Estructura
en 3 pasos numerados (la numeración codifica secuencia real, no decoración):
**1 Elegir voz → 2 Escribir → 3 Generar y escuchar.**

```
┌─────────────────────────────────┐
│ Sonora        ● En línea  [⚙]  │
├─────────────────────────────────┤
│ 1 · VOZ                         │
│ ┌─────────────────────────────┐ │
│ │ ▸ Mi voz — Carlos           │ │
│ │   Clonada · Qwen3-TTS · es  │ │
│ │   [Cambiar voz]             │ │
│ └─────────────────────────────┘ │
│ Modelo: ( Qwen3-TTS 1.7B ▾ )    │  ← cambia solo si la voz lo admite
│                                 │
│ 2 · TEXTO                       │
│ ┌─────────────────────────────┐ │
│ │ Hola, este es el primer…    │ │
│ │                             │ │
│ └─────────────────────────────┘ │
│ 312 / 10.000 caracteres         │
│ [Pegar] [Limpiar] [Diccionario] │
│                                 │
│ 3 · AJUSTES                     │
│ Estabilidad   [━━━━●──────] 0,50│
│ Similitud     [━━━━━━●────] 0,75│
│ Velocidad     [━━━●───────] 1,00│
│ Estilo        [●──────────] 0,00│
│ Formato: ( MP3 ▾ )              │
│                                 │
│ [ ▶  GENERAR ]  (ámbar, 48 px)  │
│                                 │
│ RESULTADO                       │
│ ┌─────────────────────────────┐ │
│ │ ~~~~~~~~~~~~~~~~~~~~~~~~~~~ │ │
│ │ ▸ 0:12 / 0:47  [↓ MP3]       │ │
│ │ Mi voz — Carlos · Qwen3-TTS │ │
│ │ -16 LUFS · hoy 14:32        │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
│ Estudio Voces Doblaje Hist. ⚙  │  ← nav inferior
└─────────────────────────────────┘
```

Flujo: elegir voz → escribir/pegar texto → ajustar (opcional, con valores
por defecto sensatos) → Generar → la barra muestra progreso real
(«Sintetizando… 42%», con cancelación) → el resultado aparece en la misma
pantalla con reproductor → Descargar o «Guardar en Historial» (automático:
toda generación queda en Historial). Texto largo (> 10.000 caracteres):
el frontend lo trocea en bloques y los concatena, mostrando el progreso
por bloque (narration_voice_design: bloques cortos verificados). Si el
texto contiene `[risas]` o etiquetas que el modelo no soporta, aviso antes
de generar («Este modelo no hace etiquetas de risa»), no después.
Escritorio: texto a la izquierda (2/3), voz + ajustes + resultado a la
derecha (1/3), en tablero de dos columnas.

### 8.2 Voice Lab (`#/voces`) — clonar y gestionar voces

Dos secciones: **Crear** (arriba) y **Mis voces** (lista debajo).

```
┌─────────────────────────────────┐
│ Voice Lab                       │
├─────────────────────────────────┤
│ CREAR UNA VOZ                   │
│ [ Clonar desde audio ]          │
│ [ Diseñar desde texto ]         │  ← dos pestañas, no dos pantallas
│                                 │
│ ▸ Clonar:                       │
│ Nombre de la voz ( __________ ) │
│ ┌─────────────────────────────┐ │
│ │  Suelta tu audio aquí       │ │
│ │  o [Examinar]               │ │
│ │  WAV/MP3 · 3 s – 2 min      │ │
│ │  máx. 25 MB · una sola voz  │ │
│ └─────────────────────────────┘ │
│ ✓ Audio: 12 s · limpio        │  ← validación inmediata
│ [● Grabar muestra] 0:00         │  ← graba con el micrófono
│ Idioma: ( Español ▾ )          │
│ ☐ Confirmo que esta voz es     │
│   mía o tengo permiso para     │
│   clonarla.                    │  ← consentimiento obligatorio
│ [ ▶  CLONAR VOZ ]              │
│                                 │
│ ▸ Diseñar:                      │
│ «Voz femenina, unos 30 años,   │
│  acento neutro, cálida y       │
│  pausada…» (20–1.000 car.)     │
│ [ Generar 3 muestras ]         │
│ → 3 tarjetas de candidata con  │
│   play cada una + [Guardar]    │
│                                 │
│ MIS VOCES (6)    [Buscar 🔍]   │
│ ┌─────────────────────────────┐ │
│ │ (C) Mi voz — Carlos    ▸ ★  │ │
│ │ Clonada · Qwen3-TTS · es    │ │
│ │ [Usar] [Renombrar] [Borrar] │ │
│ ├─────────────────────────────┤ │
│ │ (N) Narradora cálida   ▸    │ │
│ │ Diseñada · VoxCPM2 · es     │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

Flujo clonar: subir o grabar muestra (3–30 s recomendado) → validación
(duración, un solo hablante, calidad) con mensaje concreto si falla →
nombre + consentimiento (checkbox obligatorio; sin él el botón no se
activa, con el motivo visible) → Clonar → muestra de prueba generada
(«Hola, soy…») → **Carlos la escucha y la aprueba por oído** (puerta de
narration_voice_design: solo la muestra aprobada es «la voz») → Guardar.
Borrar voz: confirmación con el nombre escrito («Borrar "Mi voz — Carlos"
y su audio de referencia») + borrado real (replica-backend: borrado que
borra de verdad). Cada voz guarda: prompt/descripción exacto, modelo,
audio de referencia archivado, muestra aprobada y nota de consentimiento.
**Sin consentimiento explícito y archivado de la segunda persona, su voz
no se clona ni se almacena** (SKILL_AUDIT §5.5).

### 8.3 Speech-to-Speech / Voz a voz (`#/voz-a-voz`)

```
┌─────────────────────────────────┐
│ Voz a voz                       │
│ Voz de destino: [Mi voz ▾]      │
│ Método: ( Conversión de voz ▾ ) │
│   Conversión de voz — mantiene  │
│   tu interpretación.            │
│   Texto a voz — pierde la       │
│   interpretación, solo el texto.│
│ ┌─────────────────────────────┐ │
│ │ Suelta el audio (máx. 10 min)│ │
│ │ o [● Grabar]                │ │
│ └─────────────────────────────┘ │
│ [ ▶  CONVERTIR ]                │
│ Resultado: reproductor +        │
│ «Método usado: conversión»      │
└─────────────────────────────────┘
```

Honestidad en la UI: el método STT→TTS se etiqueta como tal y advierte
que pierde la interpretación (FEATURE_MAP §8). Latencia declarada: no es
tiempo real en T4.

### 8.4 Dubbing / Doblaje (`#/doblaje`)

Flujo por etapas con progreso visible (job asíncrono, FEATURE_MAP §9):
**Subir → Transcribir → Traducir → Sintetizar → Mezclar.**

```
┌─────────────────────────────────┐
│ Doblaje                         │
│ Medio: [Subir vídeo/audio]      │
│ Idioma origen: ( Auto ▾ )       │
│ Destino: [× Inglés] [+ Añadir]  │  ← máx. 3
│ Voz: ( Clonar la original ▾ )   │
│ ☐ Mantener audio de fondo       │
│ [ ▶  EMPEZAR DOBLAJE ]          │
│                                 │
│ TRABAJO EN CURSO                │
│ ● Transcribir ██████░░ 60%      │
│ ○ Traducir   ○ Sintetizar       │
│ ○ Mezclar                       │
│ Segmentos (editable):           │
│ 0:00–0:04 «Hola…» → «Hello…»    │
│   [Editar texto] [↻ Regenerar]  │
│ [↓ Descargar vídeo doblado]     │
└─────────────────────────────────┘
```

Cada segmento muestra texto origen y traducción, editable, con regeneración
solo de ese segmento. Límites visibles desde el principio: ~10 idiomas con
buena calidad (no 90), sin sincronización labial (no se promete).

### 8.5 Sound Effects (`#/efectos`)

```
┌─────────────────────────────────┐
│ Efectos de sonido               │
│ Describe el sonido:             │
│ ( Puerta de madera que chirría, │
│   lluvia de fondo…            ) │
│ Duración [━━━━●────] 10 s (1–47)│
│ Variantes: ( 1 ▾ )  (máx. 3)    │
│ [ ▶  GENERAR EFECTO ]           │
│ → tarjetas de variante con play │
│   + [↓ Descargar]               │
│ Sugerencias: Lluvia · Calle ·   │
│ Puerta · Multitud · Viento…     │
└─────────────────────────────────┘
```

Nota honesta bajo el título: «Efectos y ambientes. Sin voces ni música
estructurada.» (RESEARCH.md §4.1: Stable Audio Open es fuerte en SFX,
débil en música).

### 8.6 History / Historial (`#/historial`)

Ver §4.6. Filtros arriba: buscador de texto, filtro por voz, filtro por
tipo, filtro por fecha. Cada ítem: play inline (sin salir de la lista),
descargar, re-generar con los mismos ajustes (botón «Repetir»), borrar.
Contador de uso al pie: «Este mes: 48.210 caracteres · 62 min de audio»
(`GET /api/v1/usage`, FEATURE_MAP §16/§25) — el sustituto honesto de los
créditos, sin dinero de por medio. Exportar historial (JSON) en Ajustes.

### 8.7 Settings / Ajustes (`#/ajustes`)

```
┌─────────────────────────────────┐
│ Ajustes                         │
│ BACKEND                         │
│ URL del backend                 │
│ ( https://…trycloudflare.com  ) │
│ [Probar conexión] ● En línea    │
│ Token (opcional)                │
│ ( •••••••• ) [Mostrar]          │
│   Se guarda solo en este        │
│   dispositivo. Nunca se sube    │
│   al repositorio.               │
│                                 │
│ AUDIO                           │
│ Formato por defecto ( MP3 ▾ )   │
│ Velocidad de reproducción 1,0×  │
│ Normalizar a -16 LUFS  [●]      │
│                                 │
│ VOCES Y DATOS                   │
│ Diccionario de pronunciación    │
│   [Gestionar reglas]            │
│ [Exportar mis voces e historial]│
│ [Borrar todos mis datos]        │
│                                 │
│ ACERCA DE                       │
│ Sonora v0.1 · Sistema de diseño │
│ de referencia: elevenlabs.io,   │
│ adaptado y optimizado.          │
│ Modelos: Kokoro-82M · Qwen3-TTS │
│ 1.7B · VoxCPM2 · ZONOS3-Mini    │
└─────────────────────────────────┘
```

La URL del backend y el token viven en `localStorage`, nunca en el código
ni en el repo. «Probar conexión» llama a `GET /api/v1/health` y muestra
modelos cargados y VRAM libre. «Borrar todos mis datos» pide confirmación
doble y borra voces, referencias, historial y ajustes locales.

### 8.8 Pantallas fuera del alcance de la v1 (no se diseñan ahora)

Studio/Proyectos, Lector de documentos (ElevenReader), Música, Agentes
conversacionales y Diálogo multi-hablante quedan para Fases 2–4
(FEATURE_MAP Apéndice B). No se ponen en la navegación como promesas
vacías: si aparecen en el futuro, entran con su pantalla completa, no como
botón muerto. Lo que no se puede hacer (Voice Library de miles de voces,
Realtime, traducción en vivo, facturación) no aparece en la UI.

---

## 9. Estructura de archivos sugerida (frontend estático, GitHub Pages)

```
/
├── index.html          ← SPA: una sola página, rutas por hash
├── css/
│   └── tokens.css      ← §3.6 tal cual (única fuente de tokens)
│   └── app.css         ← componentes (sin frameworks; CSS propio)
├── js/
│   ├── app.js          ← router por hash + estado global
│   ├── api.js          ← cliente FastAPI (URL + token de Ajustes)
│   ├── studio.js       ← Estudio TTS
│   ├── voices.js       ← Voice Lab
│   ├── player.js       ← reproductor + onda
│   ├── history.js      ← historial local + contador de uso
│   └── settings.js     ← ajustes + estado del backend
├── assets/
│   └── icons.svg       ← sprite SVG (Lucide, licencia ISC)
└── es.json             ← todo el copy en español, en un solo archivo
```

Sin bundler, sin framework, sin dependencias de pago. Un solo `index.html`
+ CSS + JS vanilla: menos peso, menos roturas, y el agente de frontend puede
auditarlo línea por línea (local-thermo-review: ningún archivo > 1.000 líneas
sin razón fuerte). Rutas relativas (GitHub Pages sirve desde subruta).
Caché: `cache-buster` en la auditoría (delivery_audit_gate).

---

## 10. Checklist de entrega (para el agente de frontend)

Antes de entregar, el agente de frontend debe poder marcar todo esto.
Si algo falla, no se entrega: se corrige y se repite la checklist completa.

### 10.1 Auditoría de código (local-web-design-guidelines)

- [ ] Reglas frescas de Vercel traídas de
      `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`
      el día de la auditoría (si la lectura falla, parar).
- [ ] Hallazgos en formato escueto `archivo:línea`, un hallazgo por línea,
      agrupados por archivo; archivo sin hallazgos = marca de aprobado.
- [ ] Excepciones conscientes anotadas (decisión deliberada aprobada),
      no presentadas como fallos.

### 10.2 Piso de calidad (local-impeccable, craft-floor.md)

- [ ] Contraste medido ≥ 4.5:1 (texto) / ≥ 3:1 (texto grande) en cada pantalla.
- [ ] Medida de texto 65–75 caracteres por línea en textos largos.
- [ ] Todos los componentes en sus 7 estados (reposo, hover, foco,
      disabled, loading, error, vacío), incluido reproductor y clonación.
- [ ] Un solo momento de movimiento por pantalla (la onda).
- [ ] Sin rechazos por defecto: sin tarjetas anidadas, sin texto con
      degradado, sin glassmorphism, sin emoji como iconos, sin
      kicker/eyebrow sobre cada título, sin bordes laterales > 1 px.
- [ ] Superficies del navegador: selección, caret y foco visibles.

### 10.3 Auditoría en navegador vivo (delivery_audit_gate)

Funciones a probar una por una, en el teléfono de Carlos (canal real) y en
escritorio, con caché fresca, con el backend en línea Y con el backend
apagado (estado degradado, §6.2). Una línea por función: pass/fail +
evidencia. Repetir la checklist COMPLETA tras cada fix.

- [ ] Escribir texto, elegir voz, cambiar de modelo, generar, reproducir,
      pausar, buscar en la onda, descargar MP3/WAV.
- [ ] Sliders: cambiar cada uno por teclado y por toque; valores fuera de
      rango rechazados con mensaje junto al campo.
- [ ] Subir audio de referencia válido e inválido (< 3 s, > 2 min, formato
      no soportado): cada caso con su mensaje exacto.
- [ ] Clonar voz sin marcar el consentimiento: botón deshabilitado con motivo.
- [ ] Clonar voz con muestra válida: muestra de prueba audible y aprobada.
- [ ] Borrar voz: confirmación con nombre y borrado real (no reaparece).
- [ ] Voz a voz con ambos métodos; doblaje con edición de un segmento y
      regeneración solo de ese segmento; efectos con duración 1 s y 47 s.
- [ ] Historial: filtrar por voz, reproducir desde la lista, re-generar,
      borrar (con Deshacer), contador de uso correcto.
- [ ] Ajustes: pegar URL de backend, Probar conexión (online y offline),
      token opcional guardado solo local, borrar todos los datos.
- [ ] Backend apagado: banner visible, botones GPU deshabilitados con
      motivo, historial reproducible, reactivación con toast al volver.
- [ ] Responsive: 360 px, 768 px, 1024 px, 1440 px; sin scroll horizontal;
      sin zoom al enfocar inputs; navegación inferior usable con el pulgar.
- [ ] Accesibilidad: recorrido completo por teclado; lector de pantalla en
      los botones solo-icono; `prefers-reduced-motion` activado (sin animación).
- [ ] QC de audio de cada muestra entregada: inteligibilidad (transcribir
      con faster-whisper y comparar normalizado), sin silencios ≥ 0,5 s
      a -50 dB salvo pausa natural, -16 LUFS ± 1, pico real ≤ -1 dBTP,
      escucha completa como espectador antes de entregar.

### 10.4 Reglas permanentes de Carlos (verificación final)

- [ ] Interfaz profesional y única: no parece plantilla genérica.
- [ ] Nada copiado de ElevenLabs salvo el sistema de diseño adaptado
      (con su atribución honesta en Ajustes): sin logo, marca, textos de
      marketing, nombres de voces ni copy ajenos.
- [ ] Presupuesto cero: sin dependencias de pago, sin telemetría.
- [ ] Chatterbox no se usa como modelo en ningún archivo, etiqueta ni comentario.
- [ ] Push al repo solo con autorización explícita de Carlos en cada caso.
- [ ] Informe de auditoría adjunto a la entrega; nada se declara terminado
      por revisión de código.

---

## 11. Decisiones abiertas (para Carlos, no bloquean la v1)

1. **Nombre:** se recomienda **Sonora** (§1.3). Si no le convence, las
   alternativas son VozPropia y Ecovoz.
2. **Acento ámbar vs. acento frío:** el ámbar viene del sorteo de taste;
   si Carlos prefiere el acento frío de ElevenLabs, el cambio es un solo
   token (`--accent`) y no toca la estructura.
3. **Voice Design en v1 o Fase 2:** el diseño lo incluye; si Qwen3-TTS
   VoiceDesign no rinde en español en la prueba A/B, la pestaña
   «Diseñar desde texto» se deshabilita con motivo hasta la Fase 2.
4. **ZONOS3-Mini como modelo visible:** solo aparece en el selector si
   pasa la escucha A/B contra Qwen3-TTS (RESEARCH.md §7); si no, no se
   muestra: no se promete lo no verificado.
