# VERIFICACION.md — Sonora v0.1 (frontend)

Fecha: 2026-11-20. Verificado en local por el agente frontendista.
**Nada de esto sustituye a la auditoría en navegador vivo**: la entrega
sigue bloqueada hasta `delivery_audit_gate` (función por función, en el
teléfono de Carlos, con backend en línea Y apagado), `thermo-review`,
`ecc-revisores` y `replica-diff/test`.

## 1. Qué se verificó en local (con evidencia)

| # | Comprobación | Resultado |
|---|--------------|-----------|
| 1 | `node --check` en los 5 archivos JS (`api`, `store`, `player`, `screens`, `app`) | PASA — sin errores de sintaxis |
| 2 | Ningún archivo > 1000 líneas (máx. `screens.js`, 797; total 2633 líneas) | PASA — `wc -l` |
| 3 | Servidor estático local (`python3 -m http.server`, puerto 8931): `index.html` y los 6 archivos CSS/JS | PASA — todos HTTP 200 |
| 4 | Cruce automático de IDs: los 129 IDs usados en JS (`$('…')`) existen en `index.html` | PASA — ninguno falta |
| 5 | Las 7 rutas por hash existen en el HTML: `#/estudio`, `#/voces`, `#/voz-a-voz`, `#/doblaje`, `#/efectos`, `#/historial`, `#/ajustes` | PASA |
| 6 | Todos los archivos referenciados con ruta relativa (`./css/…`, `./js/…`) existen | PASA |
| 7 | Endpoints usados, contra FEATURE_MAP.md v2 (deltas aplicadas; corregido 2026-11-20, AUDIT M6): `GET /api/v1/health`, `GET /api/v1/tts/voices`, `GET /api/v1/library/voices`, `POST /api/v1/library/voices/{id}/favorite`, `POST /api/v1/tts`, `POST /api/v1/voices/instant-clone`, `GET /api/v1/voices/{id}/preview`, `DELETE /api/v1/voices/{id}`, `POST /api/v1/voices/design`, `GET /api/v1/voices/design/{id}/preview` (fetch con token), `POST /api/v1/voices/design/{id}/save`, `POST /api/v1/speech-to-speech`, `POST /api/v1/dubbing`, `GET /api/v1/dubbing/{job_id}`, `POST /api/v1/dubbing/{job_id}/segments/{n}/edit`, `GET /api/v1/dubbing/{job_id}/download` (fetch con token), `POST /api/v1/sfx`, `GET/POST/DELETE /api/v1/pronunciation`, `GET /api/v1/pronunciation/export` (fetch con token), `DELETE /api/v1/history/{id}` (solo con remoteId). Sin UI: `/tts/stream`, `/audio/speech`, `/stt`, `/align`, `/isolate`, `/audio-effects/*`, `PUT /pronunciation/{id}`, `POST /pronunciation/import`, `GET /history`, `GET /history/{id}/audio`, `POST /history/{id}/verify`, `GET /usage`, `GET /models` (ver backend/README.md). | PASA — revisión manual línea por línea de `js/api.js`; cada llamada va a la URL configurable de Ajustes, ninguna hardcodeada |
| 8 | Sin secretos ni claves en el código; token solo desde Ajustes (localStorage) | PASA — `grep` de claves: nada |
| 9 | Sin «Chatterbox» en ningún archivo, etiqueta ni comentario | PASA — `grep -ri chatterbox` vacío |
| 10 | Sin TODO/FIXME/XXX (sin código muerto ni atajos pendientes) | PASA — `grep` vacío |
| 11 | Sin copias de ElevenLabs: única mención es la atribución honesta en Ajustes («Sistema de diseño de referencia: elevenlabs.io, adaptado y optimizado») | PASA |
| 12 | Degradado con backend apagado (por código, no en navegador): sin URL configurada, `comprobarBackend()` sale antes de llamar a `fetch`; el banner se muestra, `Generar`/`Clonar`/`Diseñar`/`Convertir`/`Doblaje`/`Efectos` se deshabilitan con motivo visible; Historial y Ajustes no dependen del backend | PASA (código) — PENDIENTE de comprobar en navegador vivo |
| 13 | Tokens CSS copiados tal cual de DESIGN.md §3.6; táctil ≥ 44 px; `lang="es"`; `aria-label` en botones solo-icono; foco visible; `prefers-reduced-motion` | PASA (código) — PENDIENTE de medir en navegador vivo |

## 2. Qué queda pendiente (navegador vivo, agente principal)

La puerta `delivery_audit_gate` (checklist DESIGN.md §10.3, completa,
con backend en línea Y apagado, en el teléfono de Carlos y en escritorio,
con caché fresca):

- Escribir texto, elegir voz, cambiar de modelo, generar, reproducir,
  pausar, buscar en la onda, descargar MP3/WAV.
- Sliders por teclado y por toque; valores fuera de rango rechazados.
- Subir muestra válida e inválida (< 3 s, > 2 min, formato no soportado).
- Clonar sin consentimiento (botón deshabilitado con motivo) y con muestra
  válida (muestra de prueba audible y aprobada).
- Borrar voz (confirmación con nombre, borrado real, no reaparece).
- Voz a voz con ambos métodos; doblaje con edición de un segmento y
  regeneración solo de ese segmento; efectos con 1 s y 47 s.
- Historial: filtrar, reproducir desde la lista, re-generar, borrar.
- Ajustes: pegar URL, Probar conexión (online y offline), token local,
  borrar todos los datos.
- Backend apagado: banner, botones GPU deshabilitados con motivo,
  historial reproducible, toast al volver.
- Responsive 360 / 768 / 1024 / 1440 px; sin scroll horizontal; sin zoom
  al enfocar inputs; navegación inferior usable con el pulgar.
- Accesibilidad: recorrido por teclado, lector de pantalla,
  `prefers-reduced-motion`.
- QC de audio de cada muestra: -16 LUFS ± 1, pico ≤ -1 dBTP,
  inteligibilidad por transcripción, escucha completa.

Además: `thermo-review` (código), `ecc-revisores` y `replica-diff/test`
(fidelidad contra la app real de ElevenLabs, según los deltas del agente
REA; las deltas llegaron y se aplicaron: el contrato es
FEATURE_MAP.md v2, ver DELTAS_REA_APLICADAS.md).

## 3. Decisiones anotadas

- **CraftAnything descartada** (decisión del agente principal, 2026-11-20):
  el clon es un frontend conectado a un backend vivo (URL configurable,
  token, subidas de audio, streaming, IndexedDB) y exige código auditable
  y correcciones quirúrgicas; la cuota del constructor está saturada y la
  orden de Carlos del 15 nov mantiene los rebuilds en pausa. Construcción
  a mano, como se hizo.
- **Vía de construcción**: a mano, HTML/CSS/JS plano, sin build.
- **Idioma**: solo español en la v1 (DESIGN.md §7).
- **Modelo visible ZONOS3-Mini**: no aparece en el selector (DESIGN.md
  §11.4: solo si pasa la escucha A/B; no ha pasado).
- **VoxCPM2**: SÍ aparecía en el selector (contrario a lo que decía
  antes esta sección) y se quitó el 2026-11-20 (AUDIT B3): el backend
  lo registra como no integrado y el selector ya no lo ofrece.
- **Voice Design**: pestaña incluida; si Qwen3-TTS VoiceDesign no rinde
  en español en la prueba A/B, se deshabilita con motivo (DESIGN.md §11.3).
- **Historial**: local en IndexedDB (el backend puede no existir); el
  contador de uso se calcula sobre el historial local.
