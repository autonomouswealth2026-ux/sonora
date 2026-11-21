# Sonora — Tu voz, en tus manos

Frontend estático (SPA sin paso de build) del clon web privado de voz.
Solo HTML, CSS y JavaScript plano. Presupuesto cero: sin dependencias de
pago, sin telemetría, sin framework.

## Servirla en local

Cualquier servidor estático sirve. Desde la carpeta `app/`:

```bash
python3 -m http.server 8000
```

Y abrir <http://localhost:8000/index.html>. También vale `npx serve`,
`python -m SimpleHTTPServer` o subir la carpeta tal cual a GitHub Pages
(las rutas son relativas, funciona desde subruta).

## Estructura

```
index.html        SPA: las 7 pantallas, rutas por hash (#/estudio, #/voces…)
css/app.css       Tokens de DESIGN.md §3.6 + componentes (sin frameworks)
js/api.js         Cliente FastAPI: todos los endpoints de FEATURE_MAP.md
js/store.js       Ajustes en localStorage; voces e historial en IndexedDB
js/player.js      Reproductor fijo con forma de onda y búsqueda por clic
js/screens.js     Voice Lab, Voz a voz, Doblaje, Efectos, Historial, Ajustes
js/app.js         Router, estado del backend y Estudio TTS
```

## Configuración

La URL del backend **no está en el código**. Se pega en Ajustes
(«URL del backend») y se guarda solo en este dispositivo (localStorage).
Sin URL, o con el backend apagado, la app degrada con elegancia: banner
visible, botones de GPU deshabilitados con el motivo, y el Historial y
los Ajustes siempre disponibles.

## Pantallas

Estudio TTS, Voice Lab (clonar / diseñar / gestionar voces), Voz a voz,
Doblaje, Efectos de sonido, Historial local y Ajustes. Detalle del
sistema de diseño en `../DESIGN.md`; endpoints en `../FEATURE_MAP.md`.

## Verificación

Ver `VERIFICACION.md`: qué se verificó en local y qué queda pendiente
para la puerta `delivery_audit_gate` en navegador vivo (no se entrega
nada sin esa auditoría).
