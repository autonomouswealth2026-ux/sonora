# PENDIENTES_KAGGLE.md — qué queda por verificar en GPU

**Regla: no se afirma que funciona en GPU sin haberlo probado.**
Todo lo de esta lista está SIN VERIFICAR hasta el primer run de Kaggle
con audio real generado y comprobado con `POST /history/{id}/verify`.

## Checklist del primer run (en orden)

- [ ] **1. Arranque**: el notebook ejecuta las 6 celdas y `/health`
      responde `{"status": "ok", "gpu": true}`.
- [ ] **2. Túnel**: la celda 6 imprime una URL `https://*.trycloudflare.com`
      y `/health` responde a través de ella desde el teléfono.
- [ ] **3. Kokoro en español**: `POST /api/v1/tts` con
      `voice_id=ef_dora`, texto en español. Escuchar: ¿suena aceptable?
      Si suena flojo, probar `em_alex` y anotarlo (RESEARCH.md §2.1 avisa
      que el español de Kokoro no tiene nota de calidad).
- [ ] **4. Qwen3-TTS Base (clonación)**: subir una muestra limpia de
      10–30 s a `POST /api/v1/voices/instant-clone` (con `consent_note`),
      luego `POST /api/v1/tts` con esa voz y verificar con
      `POST /api/v1/history/{id}/verify` (WER ≤ 0.15 esperado).
- [ ] **5. Voice Design**: `POST /api/v1/voices/design` con un prompt en
      español; escuchar los 3 candidatos.
- [ ] **6. STT large-v3**: `POST /api/v1/stt` con un audio en español;
      comprobar timestamps por palabra y `language=es`.
- [ ] **7. Demucs**: `POST /api/v1/isolate` con un audio con música de fondo.
- [ ] **8. SFX**: `POST /api/v1/sfx` (requiere aceptar los términos de
      `stabilityai/stable-audio-open-1.0` en Hugging Face y `HF_TOKEN`).
- [ ] **9. Doblaje ES→EN**: `POST /api/v1/dubbing` con un audio corto;
      seguir el job hasta `done` y descargar el resultado.
- [ ] **10. VRAM**: con Qwen3-TTS 1.7B cargado, `GET /api/v1/models`
      y `nvidia-smi`: ¿queda VRAM libre suficiente para Whisper en el
      mismo proceso? El piso declarado ya es 8 GB (no 6 GB, AUDIT A6:
      fuente secundaria + tokenizer 0,68 GB). Si no cabe, el gestor
      descarga modelos entre jobs (ya implementado), pero hay que medirlo.

## Correcciones aplicadas antes de este run (2026-11-20)

- `requirements-gpu.txt`: `transformers==4.57.3`, `accelerate==1.12.0`
  (qwen-tts lo exige; con 4.48.3 pip no resolvía, AUDIT B5) y
  `av==13.1.0` (faster-whisper 1.2.1 se rompe con av>=14, A14).
- El notebook (celda 5) fija `CORS_ORIGINS` con la URL de GitHub Pages
  (B6) y genera un `API_TOKEN` si no viene en Secrets (A17).

## Cosas que NO se pudieron verificar en esta sesión

- **VoxCPM2**: registrado en `/api/v1/models` como no integrado. Su API
  Python no se verificó (el repo oficial es `openbmb/VoxCPM2`); no se
  finge integración. Para integrarlo: leer su README oficial, añadir un
  cargador en `engines.py` y probarlo en el run A/B.
- **ZONOS3-Mini** (retador, RESEARCH.md §2.14): no integrado; candidato
  para la prueba de escucha A/B (Qwen3-TTS vs VoxCPM2 vs ZONOS3-Mini).
- **Diarización (pyannote)**: el código la intenta si pyannote está
  instalado; sin HF_TOKEN y sin aceptar sus condiciones devuelve 422.
  No instalada en `requirements-gpu.txt` a propósito (modelos con acceso
  restringido).
- **Versiones fijadas**: `qwen-tts==0.1.1` y `kokoro==0.9.4` se verificaron
  en PyPI el 2026-11-21. El resto de versiones fijadas (transformers,
  diffusers, demucs, faster-whisper) son las estables conocidas en esa
  fecha; si `pip install -r requirements-gpu.txt` falla por resolución
  de dependencias, anotar el conflicto aquí y ajustar.
- **Streaming real por token**: `/tts/stream` es streaming **por frases**
  (se sintetiza frase a frase), no por token del modelo. Documentado en
  el código y en el README; no se presenta como latencia de 97 ms.
- **Contrato de endpoints**: FEATURE_MAP.md v2. Si el agente REA envía
  deltas verificados contra la app real de ElevenLabs, aplicarlos aquí
  y en los routers (esta lista se actualiza en ese momento).

## Notas de operación

- Kaggle: 30 h GPU/semana, 12 h/sesión. La URL del túnel muere con la sesión.
- Dos GPUs T4 de 16 GB **no suman VRAM** para un solo modelo: cada modelo
  corre en una sola T4.
- Si un endpoint devuelve 503 en Kaggle, leer `server.log` (panel Files
  de Kaggle) antes de reintentar: el 503 lleva el motivo.
