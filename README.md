# Sonora — clon web de ElevenLabs con modelos locales open-source

**Sonora** («Tu voz, en tus manos») es un clon funcional de ElevenLabs construido
exclusivamente con modelos locales open-source. Solo para uso privado
(2 usuarios); no se distribuye al público. Presupuesto cero.

> **Nombre de repo propuesto: `sonora`** (alternativa si está ocupado:
> `sonora-voice-studio`). El repo NO está creado ni se ha hecho push: el
> agente principal mostrará la app a Carlos y pedirá su confirmación del
> nombre antes de subirla.

## Qué es

- **Frontend** (`app/`): SPA estática sin paso de build (HTML/CSS/JS) para
  GitHub Pages. 7 pantallas: Estudio TTS, Voice Lab, Voz a voz, Doblaje,
  Efectos de sonido, Historial local y Ajustes. Las voces y el historial
  viven en IndexedDB; los ajustes (URL del backend + token opcional) en
  localStorage. Con el backend apagado degrada con elegancia (banner,
  botones GPU deshabilitados con motivo, Historial y Ajustes disponibles).
- **Backend** (`backend/`): FastAPI con carga perezosa de modelos, 37
  endpoints implementados + 26 en 501 honestos, OpenAPI en `/docs`,
  SQLite + ficheros en `DATA_DIR`, rate limit, token opcional por env,
  `/health` con modelos cargados y VRAM libre.

## Modelos ganadores (ver `RESEARCH.md` con fuentes)

| Caso | Modelo | Por qué |
|---|---|---|
| Narración rápida en CPU | **Kokoro-82M** (ONNX, Apache 2.0) | Tiempo real en CPU, ELO 1060. Español débil (3 voces). |
| Clonación zero-shot en GPU (T4) | **Qwen3-TTS-12Hz-1.7B-Base** (Apache 2.0) | Español nativo, clona con 3 s, ~5–6 GB VRAM, streaming. |
| Máxima calidad en T4 | **VoxCPM2** (Apache 2.0) | 2B, 30 idiomas, salida 48 kHz, ~8 GB, LoRA oficial. Registrado como no integrado (su API Python no se verificó). |
| Retador | **ZONOS3-Mini** (Apache 2.0) | 43 idiomas, clona sin transcripción, corre hasta en CPU. Benchmark del fabricante: escuchar en A/B antes de coronarlo. |

No se usa Chatterbox (retirado ago 2026) ni Coqui/XTTS (cerrado dic 2025).
Fish S2 Pro y Drama 3 no caben en una T4 de 16 GB. Satélites: Stable Audio
Open (SFX), Whisper large-v3-turbo (doblaje/STT), Demucs v4 (aislamiento),
MarianMT (traducción ES↔EN). Licencias no comerciales etiquetadas en
`RESEARCH.md` (F5-TTS, XTTS v2, Fish, Spark-TTS, etc.).

## Mapa de funciones (ver `FEATURE_MAP.md` v2)

37 áreas mapeadas contra la app real de ElevenLabs (verificación REA en
`REA.md`): **10 totalmente replicables, 10 parciales, 5 no replicables**
(Voice Library, Eleven Realtime, traducción en tiempo real, ElevenAI,
workspaces/facturación). Todo lo no implementado devuelve 501 con motivo,
sin fingir. Ghidra no aplica: ElevenLabs es una app web JS; el análisis
profundo es REA + inspección en navegador (ver `REA.md` §8 para lo
pendiente del navegador vivo).

## Arquitectura y despliegue

```
GitHub Pages (app/ estática, https)
        │  fetch a URL configurable en Ajustes
        ▼
Backend FastAPI bajo demanda ──► trycloudflare (túnel https gratuito)
        │
        ├─ Kaggle: notebook backend/kaggle_notebook.ipynb
        │  (2× T4 16 GB, sesiones ≤12 h, ~30 h/semana)
        └─ InstaBox / local CPU: backend/run_cpu.sh (solo Kokoro)
```

GitHub Pages es https y no admite http: el túnel **trycloudflare** es
imprescindible (gratis, sin cuenta; la URL cambia por sesión). El
notebook fija `CORS_ORIGINS` con la URL de Pages y genera un `API_TOKEN`
obligatorio si no viene en Secrets. Pasos exactos desde el teléfono en
`backend/README.md` (tocar pantalla, mantener pulsado para pegar).

## Qué se verificó (ver `VERIFICACION.md`, `AUDIT.md`, `AUDIT2.md`)

- Ciclo real en CPU con Kokoro: TTS en español → 200, WAV 24 kHz;
  transcripción independiente con faster-whisper: **WER 0,125**,
  veredicto `ok`; el endpoint `/verify` del backend devuelve lo mismo.
  Re-auditoría posterior: `/verify` **WER 0,0**.
- Suite pytest **40/40** con la orden documentada (`pytest tests/ -q`
  en el venv `sonora-base`, sin motores). En el venv `sonora` (con Kokoro)
  5 tests fallan por diseño: el motor carga y devuelve 200 con audio
  real donde la suite espera 503.
- `node --check` 5/5, `py_compile` OK, cruce de IDs 172/172, ningún
  archivo >1.000 líneas, sin secretos en el código, sin marca/textos/
  voces de ElevenLabs copiados.
- Auditoría 1: NO APTO (39 hallazgos). Correcciones: 9/9 bloqueantes,
  17/17 altos, 8/9 medios, 3/4 bajos (2 eran errores de la auditoría).
  Re-auditoría: **APTO CON CORRECCIONES MENORES**, 0 hallazgos abiertos;
  los 3 nuevos menores (N1–N3) cerrados y verificados.
- CraftAnything **descartada** como vía de construcción (ver
  `DECISIONES.md`): el clon es un frontend conectado a un backend vivo;
  el código a mano da control preciso sobre la integración.

## Qué queda pendiente (sin verificar, sin afirmar)

1. **Run de Kaggle (GPU):** resolución de `requirements-gpu.txt`,
   CORS+token en el notebook, clonación Qwen3-TTS 1.7B con WER ≤0,15,
   Voice Design, STT large-v3, Demucs, SFX, doblaje ES→EN y medición de
   VRAM. Checklist íntegra en `backend/PENDIENTES_KAGGLE.md`.
2. **Puerta `delivery_audit_gate` en navegador vivo:** cada función en
   el teléfono de Carlos, con backend en línea y apagado. Los subagentes
   no tienen navegador en vivo; la hace el agente principal.
3. **Discrepancias REA D1–D8** y las 10 incógnitas de tráfico N1–N10
   (`REA.md` §8): solo resolvibles con inspección de red en vivo.
4. **Escucha A/B** de las voces españolas de Kokoro y de ZONOS3-Mini
   antes de coronar al retador.

## Documentos

| Archivo | Contenido |
|---|---|
| `RESEARCH.md` | Comparativa de modelos con fuentes |
| `FEATURE_MAP.md` | Mapa de funciones v2 (37 áreas) |
| `REA.md` / `REA_VERIFICACION.md` | Análisis REA de la app real |
| `SKILL_AUDIT.md` | Auditoría de skills (27 evaluadas, 14 útiles) |
| `DESIGN.md` | Sistema de diseño de Sonora |
| `DECISIONES.md` | Decisiones (CraftAnything descartada) |
| `DELTAS_REA_APLICADAS.md` | Deltas REA aplicadas |
| `AUDIT.md` / `AUDIT2.md` | Auditoría y re-auditoría |
| `CORRECCIONES.md` | Correcciones aplicadas |
| `VERIFICACION.md` | Verificación del ciclo completo |
| `app/` | Frontend (SPA estática) |
| `backend/` | Backend FastAPI + notebook Kaggle |
