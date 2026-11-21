# RESEARCH.md — Clon local de ElevenLabs (presupuesto cero)

**Fecha de investigación:** 20 de noviembre de 2026
**Autor:** investigador (subagente) para Carlos Miguel Valdés Rodríguez
**Contexto:** uso personal para 2 personas, sin distribución pública. Frontend estático en GitHub Pages (https). Backend bajo demanda en Kaggle (2× NVIDIA T4 de 16 GB, sesiones máx. 12 h, ~30 h GPU/semana) o InstaBox (CPU, 4 vCPU, 8 GB RAM). Presupuesto cero: nada de pago.
**Método:** cada modelo se verificó contra su model card de Hugging Face, su repo de GitHub o un benchmark publicado. Donde no existe dato publicado se escribe **«sin dato publicado»**. Las cifras MOS/ELO de fuentes secundarias se marcan como tales. Los benchmarks de cada fabricante («vendor claims») se señalan explícitamente: no son verificación independiente.
**Regla de licencias:** las licencias **no comerciales valen** para este uso personal, pero se etiquetan con ⚠️ **NO COMERCIAL** en cada ficha. «Comercial» = Apache 2.0 / MIT / MPL-2.0 sin restricciones sobre los pesos.

---

## 0. Resumen ejecutivo — el ganador

| Pregunta | Ganador | Por qué (una línea) |
|---|---|---|
| **(a) Narración rápida en CPU** | **Kokoro-82M** (ONNX) | 82M parámetros, Apache 2.0, CPU en tiempo real, ELO 1060–1063 en Artificial Analysis. Pero ojo: español débil (solo 3 voces, sin nota de calidad). |
| **(b) Clonación zero-shot en GPU (T4 16 GB)** | **Qwen3-TTS-12Hz-1.7B-Base** | Apache 2.0, clona con 3 s, español nativo entre sus 10 idiomas, ~5–6 GB VRAM, streaming, soporte vLLM-Omni. |
| **(c) Máxima calidad (que quepa en una T4)** | **VoxCPM2** (OpenBMB) | 2B parámetros, 30 idiomas incl. español, salida 48 kHz, Apache 2.0, ~8 GB VRAM, LoRA oficial con 5–10 min de audio. |
| **Retador a probar en A/B** | **ZONOS3-Mini** (Zyphra, 9–11 nov 2026) | Apache 2.0, 43 idiomas, 100M activos/800M totales, clona sin transcripción, corre en CPU (ggml) y hasta en navegador (WebGPU). Es el modelo nuevo más prometedor; su benchmark es del propio fabricante, así que hay que escucharlo antes de coronarlo. |

**La calidad máxima absoluta en open-weights hoy es Fish Audio Drama 3** (ELO 1277 en Artificial Analysis, 20 nov 2026), pero **no cabe en una T4**: 37–42 GB de pesos. Queda fuera del hardware disponible. El techo de referencia comercial es ElevenLabs Eleven v4 (ELO 1334–1340).

**Hallazgo crítico de mantenimiento:** Chatterbox (Resemble AI), uno de los favoritos habituales, fue **retirado en agosto de 2026**: «Chatterbox is retired research and is no longer maintained». Sigue siendo usable (MIT), pero sin soporte ni actualizaciones.

---

## 1. Tabla comparativa maestra

ELO = Artificial Analysis Speech Arena (votos ciegos de oyentes), datos del 20 nov 2026 según la tabla reproducida en 17nas.com. TTS Arena V2 es otra escala (no comparable directamente). «Cabe en T4» = cabe en **una** T4 de 16 GB (las 2×T4 no suman VRAM para un solo modelo sin paralelismo de tensores).

| Modelo | Parámetros | ELO (AA) / TTS Arena V2 | VRAM inferencia | ¿Cabe en 1×T4 16 GB? | RTF / velocidad | Licencia pesos | Español real | Muestra p/ clonar | Streaming | Mantenimiento |
|---|---|---|---|---|---|---|---|---|---|---|
| **Kokoro-82M** | 82M | 1060 / 1477 | <1 GB pesos; 2,4–4 GB residente | ✅ Sí | RTF ~0,03 GPU (fuente secundaria); 35–100× tiempo real | Apache 2.0 ✅ | ⚠️ Sí, pero solo 3 voces (ef_dora, em_alex, em_santa), sin nota de calidad en VOICES.md | — (no clona; 54 voces fijas) | Sí | ⚠️ Congelado: v1.0 desde ene 2025, sin cambios |
| **Chatterbox Multilingual V3** | 500M | 1019 / 1490 | sin dato publicado (Turbo 350M: 4–8 GB según fuente secundaria) | ✅ Sí (estimado) | Turbo: hasta 6× tiempo real GPU (fabricante) | MIT ✅ | Sí, 23 idiomas incl. español; calidad por idioma sin dato publicado | ~5 s | Sí (Turbo) | ❌ **RETIRADO ago 2026** — repo archivado como investigación, sin soporte |
| **Qwen3-TTS-12Hz-1.7B-Base** | 1.7B (0.6B ligero) | sin dato publicado en AA | ~5–6 GB (1.7B); ~3,5–4 GB (0.6B) | ✅ Sí | Latencia 97 ms (fabricante); streaming | Apache 2.0 ✅ | ✅ Sí, 10 idiomas incl. español | **3 s** | ✅ Sí | ✅ Activo (ene 2026; paper arXiv:2601.15621) |
| **F5-TTS v1 Base** | ~335M | sin dato publicado en AA | ~2–3 GB | ✅ Sí | RTF ~0,15 GPU | ⚠️ **NO COMERCIAL**: código MIT, pesos CC-BY-NC 4.0 | ❌ Base solo EN+ZH; español solo vía fine-tune comunitario (sin checkpoint oficial verificado) | 5–15 s + transcripción exacta del clip | ❌ No nativo | ✅ Activo (paquete 1.1.22, jul 2026) |
| **XTTS v2** | ~1,6B (sin dato oficial exacto en fuentes consultadas) | 914 / sin dato | sin dato publicado (GPU recomendada) | ✅ Sí (estimado) | Streaming <200 ms latencia | ⚠️ **NO COMERCIAL**: CPML (modelo y salidas) | ✅ Sí, 17 idiomas incl. español, clonación cross-lingual | ~6 s (3 s según fork) | ✅ Sí | ⚠️ Empresa cerrada dic 2023; fork mantenido idiap/coqui-ai-TTS 0.28.0 (oct 2026) |
| **Fish Speech S2 Pro** | ~4–4,6B | 1101 / sin dato | **~17 GB** | ❌ **No** (supera 16 GB) | RTF 0,195 en H200 (fabricante) | ⚠️ **NO COMERCIAL**: Fish Audio Research License | ✅ Sí, 80+ idiomas; español Tier 2 (no Tier 1) | 10–30 s | ✅ Sí | ✅ Activo (informe técnico arXiv:2603.08823) |
| **Fish Audio Drama 3** | 35B (3B activos) | **1277** / sin dato | 37–42 GB (FP8); ~24 GB int4 | ❌ **No** | sin dato publicado | ⚠️ Comunidad: comercial gratis solo <500.000 USD/año; prohibido ofrecerlo como servicio | ✅ Sí, 83 idiomas incl. español | Clip corto (sin dato exacto publicado) | ✅ Sí | ✅ Activo (13 oct 2026) |
| **Orpheus-3B** | 3B (+variantes 1B/400M/150M) | sin dato publicado en AA | ~8–12 GB (fuente secundaria) | ✅ Sí (3B justo) | Streaming ~200 ms (fabricante); 25–50 ms según fuente secundaria | Apache 2.0 ✅ (con matiz: deriva de Llama-3.2-3B-Instruct; revisar licencia Llama) | ⚠️ Producción solo inglés; multilingüe (incl. español) solo research preview | ~5–10 s | ✅ Sí | ⚠️ Último commit 5 dic 2025; sin actividad en 2026 |
| **Dia 1.6B** | 1.6B | sin dato publicado en AA | ~10 GB | ✅ Sí | sin dato publicado | Apache 2.0 ✅ | ❌ Inglés (variante multilingüe mencionada en fuentes secundarias, español sin verificar) | Vía audio prompt (sin dato exacto) | sin dato publicado | ⚠️ Repo con última actividad relevante 2025; «updated Nov 2025» |
| **CosyVoice 3 (Fun-CosyVoice3-0.5B-2512)** | 0.5B (1.5B solo paper) | sin dato publicado en AA | sin dato publicado (0.5B: estimado <4 GB) | ✅ Sí | Streaming, latencia desde 150 ms (fabricante) | Apache 2.0 ✅ | ✅ Sí, 9 idiomas incl. español | Clip corto (sin dato exacto publicado) | ✅ Sí | ⚠️ Último push may 2026 (fuente secundaria) |
| **IndexTTS-2.5** | ~0,8B | sin dato publicado en AA | ~6 GB | ✅ Sí | 2,28× más rápido que IndexTTS-2 (informe técnico) | ⚠️ Licencia bilibili (no OSI): comercial gratis salvo umbrales altos (ver §2.11) | ✅ Sí, 5 idiomas incl. español (nuevo en 2.5) | 1 clip (sin dato exacto publicado) | sin dato publicado | ✅ Activo (10 ago 2026) |
| **Spark-TTS-0.5B** | 0.5B | sin dato publicado en AA | sin dato publicado | ✅ Sí (estimado) | RTF ~0,07–0,14 en L20 (fuente secundaria) | ⚠️ **NO COMERCIAL**: código Apache 2.0, pesos CC BY-NC-SA 4.0 (cambio mar 2025) | ❌ Solo ZH+EN | 5–30 s | ✅ Sí | ⚠️ Sin dato de actividad reciente verificado |
| **Zonos-v0.1** | 1.6B (transformer/híbrido) | 1000 / sin dato | 6 GB+ | ✅ Sí | ~2× tiempo real en RTX 4090 | Apache 2.0 ✅ | ❌ Solo EN/JA/ZH/FR/DE (sin español) | 10–30 s | ✅ Sí | ❌ **Superado**: último commit del repo 5 mar 2025; sustituido por ZONOS2 y ZONOS3-Mini |
| **ZONOS3-Mini** | 800M total / 100M activos (MoE) | sin dato publicado en AA (1.º entre open-weights en ZTTS2-Eval, benchmark del fabricante) | sin dato publicado (corre en CPU/ggml y WebGPU; 100M activos) | ✅ Sí | TTFA <570 ms en Pixel 9, <150 ms en MacBook M3, 80 ms en H100; pico 457× tiempo real (fabricante) | Apache 2.0 ✅ | ✅ Sí, 43 idiomas; normalización de texto cubre español (entre 9 idiomas con normalización completa) | 5–10 s (hasta 60 s); sin transcripción | ✅ Sí | ✅ **Activo, nov 2026** (9–11 nov 2026) |
| **KittenTTS 2** | 1.7B (ternario 1,58-bit) | sin dato publicado en AA | ~8 GB GPU o ~6 GB RAM CPU | ✅ Sí | ~Tiempo real en CPU con el fork C++ (1,1–1,5 s por 1 s de audio en portátil, fuente secundaria) | ⚠️ Pesos bajo Stellon Labs Community License (comercial gratis solo <1M USD ingresos/financiación + registro); código Apache 2.0 | ✅ 16 idiomas según fuente secundaria (lista exacta sin verificar) | 5–30 s | ❌ El fork C++ no tiene streaming (CLI por lotes) | ✅ Activo (30 sep 2026; paquete 0.9.4, 6 oct 2026) |
| **VoxCPM2** | 2B | sin dato publicado en AA (VoxCPM 0.5B: Seed-TTS-eval WER EN 1,85 %, SIM 72,9 %) | **~8 GB** (oficial) | ✅ Sí | RTF ~0,30 en RTX 4090; ~0,13 con Nano-vLLM | Apache 2.0 ✅ | ✅ Sí, 30 idiomas incl. español, sin etiqueta de idioma | Clip corto (sin dato exacto publicado) | ✅ Sí | ✅ Activo (abr 2026) |
| **Higgs Audio v3 (Higgs TTS 3)** | 4,65B | 1035 / sin dato | ~11 GB (estimado; archivo 9,31 GB) | ✅ Sí (justo) | sin dato publicado | ⚠️ **NO COMERCIAL** + Creator Grant (vídeos/podcasts monetizados OK con crédito a Boson; hosting/producto prohibido sin licencia) | ✅ Sí, 102 idiomas; español en tier pulido (WER/CER <5, según fabricante) | Clip corto (sin dato exacto publicado) | ✅ Sí (vía SGLang/vLLM-Omni) | ✅ Activo (jun–jul 2026) |

### Notas a la tabla
- **MOS:** no existe un MOS comparable y público para la mayoría de estos modelos. Las cifras MOS 4.x que circulan en blogs (p. ej. Kokoro 4.2, Orpheus 4.6, Sesame CSM 4.7) no se pudieron rastrear a una publicación primaria verificable en esta investigación; **no se reproducen como hechos**. La señal de calidad más sólida y comparable es el ELO de Artificial Analysis (tabla) y los WER/SIM de Seed-TTS-eval donde existen.
- **UTMOS:** sin dato publicado para ninguno de los candidatos en las fuentes consultadas.
- **«Sin dato publicado» ≠ malo:** significa que el fabricante no publica esa cifra, no que el modelo sea lento o malo.

---

## 2. Fichas por modelo

### 2.1 Kokoro-82M — hexgrad
- **Qué es:** TTS ligero de 82M parámetros (StyleTTS 2 + ISTFTNet), 54 voces fijas en 9 códigos de idioma, salida 24 kHz. **No clona voces.**
- **Licencia:** Apache 2.0 (pesos y código; dependencia espeak-ng GPLv3). ✅ Comercial.
- **Idiomas:** 9 códigos: inglés US/GB, japonés, mandarín, **español (3 voces: ef_dora, em_alex, em_santa)**, francés, hindi, italiano, portugués BR. Las voces españolas **no tienen nota de calidad** en VOICES.md (las inglesas llegan a A); el español es claramente secundario en el entrenamiento.
- **VRAM/velocidad:** pesos 326 MB fp32 (86 MB ONNX q8f16); instancia residente medida 2,4–4 GB con PyTorch+CUDA; RTF ~0,03 en GPU según comparativa secundaria; en CPU con ONNX corre en tiempo real.
- **Streaming:** sí.
- **Mantenimiento:** ⚠️ pesos v1.0 congelados desde el 27 ene 2025; es el modelo más descargado de HF en TTS (~12,5M descargas/30 días a nov 2026), pero no evoluciona.
- **Veredicto:** mejor narrador CPU. Para narración en español, probar primero ef_dora: si suena flojo, no hay alternativa dentro de Kokoro.
- **Fuentes:** <https://huggingface.co/hexgrad/Kokoro-82M> · <https://github.com/hexgrad/kokoro> · ELO: <https://17nas.com/tts-leaderboard.php?f=open&%3Blang=zh-CN&lang=en-US>

### 2.2 Chatterbox (Resemble AI) — Multilingual V3 / Turbo / Nano
- **Qué es:** familia 110M–500M (backbone Llama 0.5B en el multilingüe), clonación zero-shot, control de exageración emocional, etiquetas paralingüísticas ([laugh], [cough]), watermark PerTh en cada audio.
- **Licencia:** MIT ✅ Comercial.
- **Idiomas:** Multilingual V3: 23 idiomas incl. español. Turbo/Nano: solo inglés.
- **Muestra:** ~5 s (Turbo), 10 s+ (Nano).
- **VRAM:** sin dato oficial publicado; Turbo 350M estimado 4–8 GB (fuente secundaria).
- **Mantenimiento:** ❌ **RETIRADO en agosto de 2026.** El README oficial dice: «As of August 2026, Chatterbox is retired research and is no longer maintained». Resemble AI ahora hace detección de deepfakes. El código queda como archivo MIT. **No construir el clon sobre un proyecto muerto si hay alternativas vivas.**
- **Fuentes:** <https://github.com/resemble-ai/chatterbox> · <https://huggingface.co/ResembleAI/chatterbox/blob/main/README.md> · <https://www.resemble.ai/learn/models/chatterbox-turbo>

### 2.3 Qwen3-TTS (Alibaba Qwen) — 12Hz-0.6B / 1.7B ⭐ ganador (b)
- **Qué es:** familia con tres modos: Base (clonación), CustomVoice (9 voces + control emocional) y VoiceDesign (crear voces desde descripción en texto). Tokenizer propio a 12,5 Hz.
- **Licencia:** Apache 2.0 ✅ Comercial.
- **Idiomas:** 10 (ZH, EN, JA, KO, DE, FR, RU, PT, **ES**, IT).
- **Muestra:** **3 s** para clonar (la más corta del grupo).
- **VRAM:** 1.7B ~5–6 GB; 0.6B ~3,5–4 GB. Cabe holgado en una T4.
- **Velocidad/streaming:** latencia declarada 97 ms; streaming sí; soporte oficial día 0 en vLLM-Omni.
- **Calidad:** paper arXiv:2601.15621 (ene 2026). En Seed-TTS-eval, Qwen3-TTS-1.7B figura con WER EN 1,24 % según comparativa secundaria (frente a Fish S2 Pro 0,99 %); Higgs v3 declara 1,30 % en su propia tabla. Sin ELO en Artificial Analysis a fecha de consulta.
- **Mantenimiento:** ✅ Activo (lanzado ene 2026, actualizado a través de 2026).
- **Veredicto:** **ganador para clonación zero-shot en GPU.** Mejor combinación de licencia limpia + español nativo + muestra de 3 s + VRAM baja + streaming + mantenimiento activo.
- **Fuentes:** <https://github.com/QwenLM/Qwen3-TTS> · <https://huggingface.co/collections/Qwen/qwen3-tts> · paper: <https://arxiv.org/abs/2601.15621> (citado en <https://github.com/yepicaiaaron/awesome-audio-generation-2026/blob/HEAD/README.md>)

### 2.4 F5-TTS (SWivid, Shanghai Jiao Tong)
- **Qué es:** flow-matching DiT no autorregresivo, ~335M, referente de naturalidad/prosodia en 2025–2026 según la comunidad.
- **Licencia:** ⚠️ **NO COMERCIAL** — código MIT, **pesos CC-BY-NC 4.0** (entrenado con Emilia). Vale para este uso personal; no vale para vender el audio.
- **Idiomas:** ❌ base solo EN+ZH. Español requiere fine-tune comunitario (existen fine-tunes de alemán documentados; de español no se verificó ningún checkpoint oficial).
- **Muestra:** 5–15 s **+ transcripción exacta** del clip (paso extra de UX; se puede auto-transcribir con Whisper).
- **VRAM:** ~2–3 GB; RTF ~0,15 en GPU; en CPU varias veces más lento que tiempo real.
- **Streaming:** ❌ no nativo (genera la frase completa).
- **Fine-tuning:** documentado; 10–60 min de audio, ~12 GB VRAM según fuente secundaria → factible en T4.
- **Veredicto:** descartado como principal por el español; segunda opción para narración en inglés.
- **Fuentes:** <https://github.com/SWivid/F5-TTS> · <https://supavocal.com/models/f5-tts>

### 2.5 XTTS v2 (Coqui)
- **Qué es:** el clásico multilingüe (17 idiomas, clonación cross-lingual: clona de un clip en inglés y habla español con esa voz).
- **Licencia:** ⚠️ **NO COMERCIAL** — código MPL-2.0, pesos y **salidas** bajo Coqui Public Model License (CPML). Sin vía comercial: Coqui cerró sus servicios de pago en dic 2023.
- **Idiomas:** ✅ 17 incl. español.
- **Muestra:** ~6 s (el fork dice que 3 s bastan).
- **Streaming:** sí, <200 ms latencia.
- **Mantenimiento:** ⚠️ repo original abandonado; fork mantenido **idiap/coqui-ai-TTS**, versión 0.28.0 (19 oct 2026).
- **Veredicto:** veterano fiable para uso personal, pero superado en calidad (ELO 914, el más bajo de la tabla) y con licencia restrictiva. Solo como plan C.
- **Fuentes:** <https://github.com/coqui-ai/TTS> · <https://huggingface.co/coqui/XTTS-v2> · <https://supavocal.com/models/coqui-tts>

### 2.6 Fish Speech S2 Pro (Fish Audio)
- **Qué es:** Dual-AR, 4B+400M, 80+ idiomas, control emocional con 15.000+ etiquetas. Pasó el «Audio Turing Test» según el fabricante (oyentes lo identifican como IA solo el 48,5 % de las veces).
- **Licencia:** ⚠️ **NO COMERCIAL** — Fish Audio Research License (código bajo Community License v1.0, uso comercial gratis solo <500.000 USD/año; pesos S2 Pro: investigación/no comercial).
- **Idiomas:** 80+; español Tier 2 (Tier 1: EN/ZH/JA).
- **VRAM:** **~17 GB → NO cabe en una T4 de 16 GB.** Descartado por hardware, aunque la calidad sea top.
- **Muestra:** 10–30 s. Streaming sí. RTF 0,195 en H200 (fabricante).
- **Veredicto:** inalcanzable en Kaggle T4. Solo viable si algún día hay GPU mayor.
- **Fuentes:** <https://github.com/fishaudio/fish-speech> · <https://www.assemblyai.com/blog/how-to-generate-speech-fish-audio> · informe técnico arXiv:2603.08823

### 2.7 Fish Audio Drama 3 (oct 2026)
- **Qué es:** MoE 35B (3B activos), dirección por lenguaje natural («[whispering]»), hasta 16 personajes en un texto, 83 idiomas.
- **Licencia:** ⚠️ Fish Audio Community License v1.0: comercial gratis solo <500.000 USD/año; **prohibido ofrecerlo como servicio** de TTS/clonación.
- **VRAM:** 37–42 GB (FP8); int4 ~24 GB. **No cabe en T4.**
- **ELO:** 1277 — el open-weight mejor clasificado en Artificial Analysis (20 nov 2026).
- **Veredicto:** la mejor calidad open-weight del momento, pero fuera del hardware. Referencia de techo, no opción real.
- **Fuentes:** <https://huggingface.co/fishaudio/drama-3> · <https://rits.shanghai.nyu.edu/ai/fish-audio-releases-drama-3-a-35b-open-weight-directable-tts-model/> · <https://ai-opensource.com/models/drama-3/>

### 2.8 Orpheus-TTS (Canopy Labs)
- **Qué es:** LLM-TTS sobre Llama-3.2-3B, etiquetas de emoción (<laugh>, <sigh>), 8 voces integradas, variantes 3B/1B/400M/150M.
- **Licencia:** Apache 2.0 ✅, con matiz: deriva de Llama-3.2-3B-Instruct, cuya licencia comunitaria puede aplicar también. Pesos con acceso restringido (gated) en HF.
- **Idiomas:** ⚠️ producción solo inglés; familia multilingüe (ZH/HI/KO/ES/IT/FR/DE) solo como research preview.
- **Muestra:** ~5–10 s. Streaming ~200 ms.
- **Mantenimiento:** ⚠️ último commit 5 dic 2025; la propia comparativa de Bland (nov 2026) señala que el cuaderno de clonación sigue pendiente de arreglo.
- **Veredicto:** descartado como principal por el español en preview y el mantenimiento parado. Interesante solo para inglés expresivo.
- **Fuentes:** <https://github.com/canopyai/Orpheus-TTS> · <https://www.assemblyai.com/blog/free-open-source-text-to-speech> · <https://www.bland.ai/compare/bland-speech-vs-orpheus-tts>

### 2.9 Dia 1.6B (Nari Labs)
- **Qué es:** diálogo multi-hablante ([S1]/[S2]), sonidos no verbales ((laughs), (coughs)).
- **Licencia:** Apache 2.0 ✅.
- **Idiomas:** ❌ inglés en su lanzamiento principal; variante multilingüe mencionada en fuentes secundarias sin verificación de español.
- **VRAM:** ~10 GB. Cabe en T4.
- **Veredicto:** nicho diálogo en inglés. No sirve para el requisito de español.
- **Fuentes:** <https://github.com/nari-labs/dia> · <https://github.com/bettercallzaal/ZAOOS/blob/main/research/music/329-open-source-tts-elevenlabs-alternatives/README.md>

### 2.10 CosyVoice 3 (FunAudioLLM / Alibaba)
- **Qué es:** LLM-TTS 0.5B abierto (el 1.5B es solo paper), streaming, clonación zero-shot multilingüe y cross-lingual, control por instrucciones (idioma, dialecto, emoción, velocidad, volumen).
- **Licencia:** Apache 2.0 ✅ (pesos y código).
- **Idiomas:** ✅ 9 (ZH, EN, JA, KO, DE, **ES**, FR, IT, RU) + 18 dialectos chinos.
- **VRAM:** sin dato oficial publicado; 0.5B estimado <4 GB.
- **Velocidad:** streaming con latencia desde 150 ms (fabricante). Métricas propias: CER chino 1,21 %, WER inglés 2,24 %, similitud de hablante 78,0 (base); RL: CER 0,81 %.
- **Mantenimiento:** ⚠️ último push may 2026 según fuente secundaria; repo que ha cambiado de organización en GitHub (QwenAudio/CosyVoice).
- **Veredicto:** alternativa sólida a Qwen3-TTS si este falla; mismo perfil de licencia y español. Probar en A/B.
- **Fuentes:** <https://github.com/FunAudioLLM/CosyVoice> · <https://huggingface.co/spaces/FunAudioLLM/Fun-CosyVoice3-0.5B/blob/03875f4fd87bf6572169ae905dc69a9b5114f2aa/README.md> · <https://cosyvoice.org/cosyvoice-3>

### 2.11 IndexTTS-2.5 (IndexTeam / Bilibili, 10 ago 2026)
- **Qué es:** ~0,8B autorregresivo, clonación zero-shot, vector de emoción de 8 dimensiones, control de velocidad.
- **Licencia:** ⚠️ **bilibili Model Use License** (no es licencia open-source OSI). Permite uso comercial salvo umbrales muy altos: el texto en chino (prevalente) exige licencia aparte si ingresos >100M RMB/año o >100M usuarios activos mensuales; el texto en inglés dice 1.000M RMB. Para uso personal de 2 personas: sin efecto práctico. Prohíbe usar las salidas para entrenar otros modelos.
- **Idiomas:** ✅ 5 (ZH, EN, JA, **ES**, AR) — español, japonés y árabe son nuevos en 2.5; cross-lingual.
- **VRAM:** ~6 GB. Cabe en T4.
- **Mantenimiento:** ✅ Activo (ago 2026). IndexTTS-2 (jun 2025) era Apache 2.0; la 2.5 cambió de licencia.
- **Veredicto:** candidato serio por español nativo + emoción + VRAM baja. Su licencia es el único pero, irrelevante para uso personal.
- **Fuentes:** <https://github.com/index-tts/index-tts> · <https://huggingface.co/IndexTeam/IndexTTS-2.5> · <https://creativeaishow.com/indextts-2-5-the-free-open-weights-ai-voice-cloning-model-with-emotion-control-runs-on-6gb-vram/>

### 2.12 Spark-TTS-0.5B (SparkAudio)
- **Qué es:** LLM-TTS con BiCodec, control de género/tono/velocidad, clonación cross-lingual.
- **Licencia:** ⚠️ **NO COMERCIAL** — código Apache 2.0, **pesos CC BY-NC-SA 4.0** desde mar 2025 (por los datos de entrenamiento Emilia). Muchas guías antiguas aún dicen «Apache 2.0»: es un error.
- **Idiomas:** ❌ solo ZH+EN.
- **Veredicto:** descartado por idioma y licencia.
- **Fuentes:** <https://github.com/SparkAudio/Spark-TTS> · <https://github.com/SparkAudio/Spark-TTS/issues/110>

### 2.13 Zonos-v0.1 (Zyphra, feb 2025)
- **Qué es:** 1,6B transformer/híbrido (Mamba2), 44,1 kHz, 200k horas de entrenamiento.
- **Licencia:** Apache 2.0 ✅.
- **Idiomas:** ❌ EN/JA/ZH/FR/DE — sin español.
- **Mantenimiento:** ❌ superado: último commit del repo 5 mar 2025; Zyphra pasó a ZONOS2 (jun 2026, MoE 8B) y ZONOS3-Mini.
- **Veredicto:** descartado (sin español, abandonado). Se mantiene en la tabla por ser el «Zonos» que piden verificar.
- **Fuentes:** <https://github.com/Zyphra/Zonos> · <https://pinggy.io/blog/best_open_source_self_hosted_text_to_speech_models/>

### 2.14 ZONOS3-Mini (Zyphra, 9–11 nov 2026) ⭐ retador
- **Qué es:** MoE disperso: 800M totales, **100M activos** por token; codec ZAC-1 a 15 Hz; steering de activación (ritmo, emoción, proyección, viveza por palabra); 27 voces integradas; runtimes SGLang-Omni, vLLM, MLX, C++/ggml (CPU/CUDA/Metal/Vulkan) y **WebGPU en navegador**.
- **Licencia:** Apache 2.0 ✅ (pesos), MIT (código).
- **Idiomas:** ✅ 43 idiomas; normalización de texto completa en 9 (EN, ZH, JA, KO, DE, **ES**, FR, IT, PT); el resto se procesa tal cual se escribe.
- **Muestra:** 5–10 s sugeridos (hasta 60 s); **sin transcripción**.
- **Velocidad:** TTFA <570 ms en Pixel 9 (navegador), <150 ms en MacBook Air M3, 80 ms en H100, pico 457× tiempo real (fabricante).
- **Calidad:** 1.º entre modelos open-weight en **ZTTS2-Eval, benchmark creado por el propio Zyphra** — cifra no independiente; el índice cae a 44,7 en clonación por clip de referencia según análisis secundario. **Hay que escucharlo antes de coronarlo.**
- **Veredicto:** el modelo nuevo más prometedor del mes. Si su español suena bien en prueba A/B contra Qwen3-TTS, puede convertirse en el ganador absoluto: es el único que además corre en CPU/navegador y cubre los tres casos de uso con un solo modelo.
- **Fuentes:** <https://huggingface.co/blog/Zyphra/zonos3-mini> · <https://huggingface.co/Zyphra/ZONOS3-Mini> · <https://dev.to/aitecharchive/zonos3-mini-vs-fish-audio-s2-pro-open-tts-verdict-1l54>

### 2.15 KittenTTS 2 (KittenML / Stellon Labs, 30 sep 2026)
- **Qué es:** speech-LM 1.7B con pesos ternarios (1,58-bit), 506 MB; clonación in-context, etiquetas de expresión ([joyful], <laugh>); variantes pequeñas ONNX (pico 7M, mini, nano) aún Apache 2.0.
- **Licencia:** ⚠️ **pesos bajo Stellon Labs Community License**: comercial gratis solo si ingresos anuales <1M USD **y** financiación total <1M USD, con registro obligatorio en Stellon Labs. Código Apache 2.0. (Los modelos legacy ONNX 0.8 siguen Apache 2.0.)
- **Idiomas:** 16 según fuente secundaria (lista exacta sin verificar en esta investigación); español incluido según esa fuente, sin verificación de calidad.
- **Muestra:** 5 s (fabricante dice 5–30 s).
- **Velocidad:** tiempo real en CPU con el fork C++ (kitten-tts-2-cpp, creado 1 oct 2026); el paquete Python es «solo para demo» según su propia documentación.
- **Veredicto:** interesante como narrador CPU con clonación, pero la licencia con registro y el fork C++ en beta lo dejan por detrás de Kokoro (CPU sin clonación) y ZONOS3-Mini (CPU con clonación, Apache limpio).
- **Fuentes:** <https://github.com/KittenML/KittenTTS> · <https://pypi.org/project/kittenml/0.9.4/> · <https://andrew.ooo/posts/kittentts-review-cpu-text-to-speech-voice-cloning/>

### 2.16 VoxCPM2 (OpenBMB, abr 2026) ⭐ ganador (c)
- **Qué es:** TTS sin tokenizer, difusión autorregresiva (MiniCPM-4), 2M+ horas de entrenamiento, salida nativa **48 kHz** (la más alta del grupo), Voice Design (crear voz desde descripción).
- **Licencia:** Apache 2.0 ✅.
- **Idiomas:** ✅ 30 incl. español, sin etiqueta de idioma (detecta solo).
- **VRAM:** **~8 GB** (oficial). Cabe en una T4 con margen para Whisper en paralelo.
- **Velocidad:** RTF ~0,30 en RTX 4090; ~0,13 con Nano-vLLM. Streaming sí.
- **Fine-tuning:** LoRA oficial con **5–10 min** de audio (r=32, alpha=16, intercambiable en caliente) y SFT completo.
- **Calidad:** Seed-TTS-eval del VoxCPM 0.5B: WER EN 1,85 %, SIM 72,9 %; ZH 0,93 % / 77,2 % — mejores que HiggsAudio-v2 y VibeVoice en esa tabla (datos del fabricante/espejo HF). Para VoxCPM2 no se encontró ELO en Artificial Analysis.
- **Veredicto:** **ganador de máxima calidad dentro de una T4.** 48 kHz + Apache + español + LoRA oficial lo hacen también el mejor candidato para el clon «profesional» con fine-tuning.
- **Fuentes:** <https://openbmb.cn/docs/en/guides/voxcpm/voxcpm-2> · <https://huggingface.co/openbmb/VoxCPM1.5> (familia) · <https://vdf.ai/blog/best-local-tts-models/>

### 2.17 Higgs Audio v3 / Higgs TTS 3 (Boson AI, jun–jul 2026)
- **Qué es:** 4,65B autorregresivo, voz conversacional, 100+ idiomas, etiquetas inline de emoción/estilo/SFX, diálogo multi-hablante.
- **Licencia:** ⚠️ **NO COMERCIAL** + Creator Use Grant (9 jul 2026): vídeos/podcasts/audiolibros monetizados **sí, con crédito** a Boson AI; hosting, producto o API, no sin licencia aparte.
- **Idiomas:** ✅ 102 idiomas; español en tier pulido (WER/CER <5 según fabricante).
- **VRAM:** archivo 9,31 GB; estimado ~11 GB. Cabe en T4 (justo).
- **ELO:** 1035.
- **Veredicto:** calidad alta y español fuerte, pero la licencia prohíbe justo el uso como servicio (el backend del clon sería un servicio, aunque sea privado). Para uso estrictamente personal sin exponerlo, usable; con más fricción legal que VoxCPM2/Qwen3. Reserva.
- **Fuentes:** <https://huggingface.co/bosonai/higgs-audio-v3-tts-4b> · <https://ai-opensource.com/models/higgs-tts-3/> · <https://localaimaster.com/blog/higgs-tts-3-licence-and-vram>

---

## 3. Modelos nuevos en trending (nov 2026) que no estaban en la lista inicial

| Modelo | Fecha | Por qué importa | Estado de verificación |
|---|---|---|---|
| **ZONOS3-Mini** (Zyphra) | 9–11 nov 2026 | Ver §2.14. El lanzamiento del mes. | ✅ Verificado a fondo |
| **Fish Audio Drama 3** | 13 oct 2026 | Ver §2.7. Mejor ELO open-weight (1277). | ✅ Verificado a fondo |
| **KittenTTS 2 Mini** (KittenML) | 13 nov 2026 | 82M, 16 idiomas, rival directo de Kokoro en CPU. | ⚠️ Solo mención en comparativa (vdf.ai); sin ficha propia verificada |
| **Breeze TTS 2** (BreezeBlue) | ago 2026 | ELO 1228 en AA — 3.º entre open-weights. | ⚠️ Solo aparece en el leaderboard; licencia, VRAM e idiomas sin verificar — **a verificar antes de usar** |
| **Ming-3.0-tts** (Ant Group) | oct 2026 | ELO 1179 en AA. | ⚠️ Solo leaderboard; sin verificar |
| **Phonon 31M** (Gradium) | oct 2026 | ELO 1108 con solo 31M parámetros; inglés. | ⚠️ Solo leaderboard; sin verificar |
| **Higgs TTS 3** | jun 2026 | Ver §2.17. | ✅ Verificado |
| **VoxCPM2** | abr 2026 | Ver §2.16. | ✅ Verificado |
| **Voxtral TTS** (Mistral) | oct 2026 | ELO 1218 en AA (15.º general). | ⚠️ Solo leaderboard; sin verificar |
| **Sesame CSM** | 2025 | MOS 4,7 citado en blogs (sin fuente primaria verificada); solo inglés, diálogo. | ⚠️ No verificado a fondo; inglés solo lo descarta para español |

**Conclusión del trending:** ningún modelo nuevo de noviembre 2026 supera con evidencia independiente a Qwen3-TTS/VoxCPM2 en el caso de uso (español + T4 + Apache). ZONOS3-Mini es la única novedad que puede cambiar el ranking, pendiente de escucha.

---

## 4. Funciones satélite del clon (más allá del TTS)

### 4.1 Efectos de sonido — Stable Audio Open
- **Stable Audio Open 1.0** (Stability AI): texto→audio, hasta 47 s, estéreo 44,1 kHz. Entrenado con ~486k grabaciones CC0/CC BY/CC Sampling+ (Freesound + Free Music Archive). **Fuerte en SFX/foley/texturas, débil en música estructurada; sin voces.**
- Licencia: Stability AI Community License — comercial gratis solo <1M USD ingresos anuales + registro. Pesos con acceso restringido (aceptar términos en HF).
- **Stable Audio 3.0 Small SFX** (0,6B, 2026): variante específica para SFX en dispositivo. Misma licencia.
- Alternativa: **MusicGen** (Meta, CC-BY-NC) para música — no comercial, peor licencia.
- **Veredicto:** Stable Audio Open 1.0 es la opción para SFX. En T4 cabe (sin dato oficial de VRAM publicado; modelo DiT ~1B, estimado <8 GB).
- Fuentes: <https://huggingface.co/stabilityai/stable-audio-open-1.0> · <https://www.clintjohnson.cloud/patchbay/ai-music/run-stable-audio-open-locally/> · <https://github.com/haxzie/genmotion/blob/HEAD/apps/web/content/blog/best-ai-sound-effect-generators.md>

### 4.2 Doblaje — pipeline Whisper + TTS
- **Whisper large-v3-turbo** (OpenAI, MIT): 809M parámetros, ~6 GB VRAM, 99 idiomas, español WER 3,35 % en FLEURS (mejor que Parakeet v3 en español). Transcribe y traduce a inglés. `faster-whisper` (CTranslate2) es la implementación eficiente que Carlos ya usa.
- Pipeline: audio original → Demucs (aislar voz, §4.4) → Whisper (transcripción + timestamps) → traducción del texto → TTS clonado con la voz original → mezcla con la pista sin voz.
- Herramienta de referencia para doblaje con clonación: el add-on KittenTTS 2 de Subtitld (usa este mismo esquema).
- Fuentes: <https://github.com/openai/whisper> · <https://metavert.io/compare/whisper-vs-parakeet> · <https://northflank.com/blog/best-open-source-speech-to-text-stt-model-in-2026-benchmarks>

### 4.3 Speech-to-speech / voice changer
- **Chatterbox VC** (`ChatterboxVC`, `example_vc.py`): conversión voz→voz con el mismo modelo, MIT. Pero el proyecto está **retirado** (ago 2026).
- **RVC (Retrieval-based Voice Conversion)**: MIT, estándar de facto. Entrena un modelo por voz con **~10 min** de audio limpio; inferencia en tiempo real (~170 ms, ~90 ms con ASIO); VRAM mín. 4 GB (GTX 1060). **No es zero-shot**: cada voz exige entrenar. Upstream con commits lentos; la actividad vive en forks.
- **Veredicto:** para cambiar la voz de un audio ya grabado sin entrenar, usar la VC de Chatterbox o la clonación cross-lingual de XTTS/Qwen3; para voice changer en vivo o covers, RVC.
- Fuentes: <https://github.com/resemble-ai/chatterbox> · <https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI> · <https://en.wikipedia.org/wiki/Retrieval-based_Voice_Conversion>

### 4.4 Aislamiento de audio — Demucs
- **Demucs v4.1.0** (Meta/Kyutai, 11 jul 2026): separación en 4 stems (vocals/drums/bass/other), modelo por defecto `htdemucs` SDR 9,0 dB; `htdemucs_ft` ~4× más lento con mejora modesta. MIT (código y modelos).
- Uso: `demucs --two-stems=vocals audio.mp3` → `vocals.wav` limpio para clonar o doblar.
- VRAM: ~3 GB mínimo, cómodo ~7 GB. Cabe en T4 y en CPU (más lento).
- **Veredicto:** pieza estándar del pipeline; sin alternativa open que lo supere de forma verificable.
- Fuentes: <https://github.com/facebookresearch/demucs> (repo actual: adefossez/demucs) · <https://pypi.org/project/demucs/3.0.4/> · <https://clintjohnson.cloud/patchbay/ai-music/separate-stems-with-demucs/>

### 4.5 Clonado «profesional» con fine-tuning (LoRA) en una T4 16 GB
- **Viable, con límites.** LoRA entrena solo adaptadores (~0,1–1 % de parámetros); el coste lo dominan los pesos base + optimizador + activaciones.
  - **VoxCPM2:** LoRA oficial con 5–10 min de audio (r=32, alpha=16). 2B en bf16 ≈ 4 GB de pesos + adaptadores + gradientes: **cabe en 16 GB** con batch pequeño. Es la vía recomendada.
  - **F5-TTS:** fine-tune documentado con 10–60 min, ~12 GB VRAM (fuente secundaria). Cabe, pero el modelo base no habla español: el fine-tune tendría que enseñarle español además de la voz.
  - **XTTS v2:** fine-tuning soportado por la librería coqui-tts (GPT + vocoder); sin cifra oficial de VRAM verificada.
  - **Qwen3-TTS Base:** el fabricante lo describe como «fine-tunable»; sin guía de VRAM verificada en esta investigación.
- **Full fine-tuning de un 2B en 16 GB: no viable** sin QLoRA 4-bit + gradient checkpointing, y aun así lento en T4. **No intentarlo.**
- **Recomendación práctica:** zero-shot primero (3–30 s). Solo si la voz no se parece lo suficiente, LoRA de VoxCPM2 con 5–10 min limpios (grabar en silencio, sin música; aislar con Demucs si hace falta).
- Fuentes: <https://openbmb.cn/docs/en/guides/voxcpm/voxcpm-2> · <https://github.com/aberson/toybox/blob/HEAD/documentation/research/2026-08-23-storytime-investigation/research-voice-clone.md>

---

## 5. Túneles: exponer el backend de Kaggle por https

GitHub Pages es https y bloquea llamadas a http (mixed content). El backend de Kaggle necesita una URL **https** pública. Dos opciones gratuitas verificadas:

### 5.1 Cloudflare Quick Tunnel (trycloudflare) — recomendado
- **Cómo:** descargar el binario `cloudflared` en el notebook y ejecutar `cloudflared tunnel --url http://localhost:8000`. Imprime una URL `https://<aleatorio>.trycloudflare.com`.
- **Coste:** 0 USD, **sin cuenta, sin token, sin tarjeta**.
- **Límites:** 200 peticiones simultáneas en vuelo; sin SSE (server-sent events) según comparativas 2026; la URL **cambia en cada sesión** (hay que copiarla al frontend en cada arranque).
- **Evidencia de uso en Kaggle:** proyectos reales lo usan exactamente así (notebook GPU + FastAPI + cloudflared), p. ej. `gpu-free-serve` (Kaggle T4×2) y `AgarthaVision/inference/KAGGLE.md` (Kaggle T4×2 + `https://<random>.trycloudflare.com`).
- **Variante estable (gratis, con cuenta):** túnel Cloudflare con nombre + dominio propio en Cloudflare Zero Trust (plan gratuito): URL fija `https://api.tudominio.com`, token guardado en secretos de Kaggle, no en el notebook.
- Fuentes: <https://github.com/iramarfalcao/gpu-free-serve> · <https://github.com/Joryuoo/AgarthaVision/blob/HEAD/inference/KAGGLE.md> · <https://webhooks.sh/alternatives/ngrok-vs-cloudflare-tunnel>

### 5.2 ngrok (plan gratuito) — alternativa
- **Cómo:** cuenta + authtoken (`ngrok config add-authtoken <token>`), `ngrok http 8000`.
- **Límites gratuitos (nov 2026):** 1 GB de transferencia/mes, 20.000 peticiones HTTP/mes, 5.000 conexiones TCP/mes, máx. 3 endpoints online, 4.000 peticiones/min. **Sin límite de tiempo de sesión** (el «límite de 2 h» es un mito: la documentación oficial dice que los endpoints gratuitos no caducan).
- **Ventaja:** **dominio fijo** `xxx.ngrok-free.app` que sobrevive a reinicios (el plan gratis incluye 1 dominio de desarrollo asignado).
- **Desventajas:** página intersticial de aviso en el navegador (los clientes API la saltan con el header `ngrok-skip-browser-warning`); 1 GB/mes es poco si se devuelven audios WAV largos (un minuto de WAV 24 kHz ≈ 2,9 MB; 1 GB ≈ 350 min/mes); requiere cuenta y token (secreto en Kaggle).
- Fuentes: <https://www.localcan.com/blog/ngrok-free-tier-limits> · <https://stacksfree.com/blog/ngrok-free-tier-guide-2026/> · <https://www.ajayk.sh/blog/cloudflare-tunnel-vs-ngrok-vs-tailscale-funnel-2026/>

### 5.3 Veredicto túneles
| Criterio | trycloudflare | ngrok gratis |
|---|---|---|
| Cuenta/token | No | Sí (authtoken) |
| URL | Aleatoria por sesión | Fija (`*.ngrok-free.app`) |
| https | ✅ Sí | ✅ Sí |
| Límite duro | 200 en vuelo | 1 GB + 20k req/mes |
| Aviso en navegador | No | Sí (intersticial) |
| SSE/streaming | Sin soporte documentado | Sí |
| **Recomendación** | **Primera opción**: cero fricción, sin cuenta, sin cuota mensual. Copiar la URL en cada sesión. | Segunda opción si molesta re-copiar la URL o si hace falta streaming SSE. Ojo al GB mensual. |

**Notas operativas Kaggle:** Internet debe estar en ON y la cuenta verificada por teléfono (requisito para GPU e Internet). La sesión muere a las 12 h y la URL del túnel muere con ella: el frontend debe permitir pegar la URL base del backend (campo de configuración), no hardcodearla. Un T4×2 son **dos GPUs de 16 GB separadas**: un modelo de >16 GB no cabe aunque «sumen» 32 GB.

---

## 6. Arquitectura recomendada (resumen para la fase de construcción)

1. **Frontend (GitHub Pages):** estático; campo configurable con la URL del túnel; subida de clip de referencia (WAV/MP3); cola de trabajos; descarga del audio generado (preferir MP3/Opus para no gastar la cuota del túnel).
2. **Backend (notebook Kaggle, FastAPI):** un endpoint `/tts` (texto + referencia → audio) y `/health`. Modelos en este orden de carga:
   - **Por defecto: Qwen3-TTS-12Hz-1.7B-Base** (clonación, español, 3 s).
   - **Narración sin clonar / CPU (InstaBox): Kokoro-82M-ONNX**.
   - **Máxima calidad / LoRA: VoxCPM2**.
   - **Retador A/B: ZONOS3-Mini** (probar su español antes de decidir).
3. **Pipeline de doblaje:** Demucs → faster-whisper (turbo) → traducción → Qwen3-TTS/VoxCPM2.
4. **SFX:** Stable Audio Open 1.0 en el mismo notebook (sesión separada si la VRAM no da para todo a la vez).
5. **Seguridad mínima:** token secreto en el header (el túnel es público: cualquiera con la URL puede llamar al backend); subir el clip de referencia solo con consentimiento de la persona clonada; watermark si el modelo lo incluye (Chatterbox lo trae; Qwen3/VoxCPM2 no lo documentan).

---

## 7. Recomendación final

| Caso de uso | Modelo | Justificación en una frase |
|---|---|---|
| (a) Narración rápida en CPU | **Kokoro-82M** (ONNX) | El más rápido y ligero con licencia limpia; español limitado a 3 voces sin nota de calidad — verificar ef_dora antes de adoptarlo para español. |
| (b) Clonación zero-shot en GPU | **Qwen3-TTS-12Hz-1.7B-Base** | Apache 2.0 + español nativo + 3 s de muestra + ~5–6 GB VRAM + streaming + activo. |
| (c) Máxima calidad (en T4) | **VoxCPM2** | 48 kHz, 30 idiomas, Apache 2.0, ~8 GB VRAM y LoRA oficial de 5–10 min. |
| Empate/retador | **ZONOS3-Mini** | Nov 2026, Apache 2.0, 43 idiomas, CPU/WebGPU; si su español pasa la escucha A/B, desbanca a los tres anteriores en versatilidad. |
| Descartados con motivo | Fish S2 Pro y Drama 3 (no caben en T4), F5-TTS y Spark-TTS (sin español oficial), Chatterbox (retirado), Zonos-v0.1 (abandonado, sin español), Orpheus (español en preview, parado), Dia (inglés) | Ver fichas §2. |

**Próximo paso sugerido:** prueba de escucha A/B en una sola sesión de Kaggle con el mismo texto en español y el mismo clip de referencia (10 s, limpio): Qwen3-TTS 1.7B vs VoxCPM2 vs ZONOS3-Mini vs IndexTTS-2.5. Decidir por oído, no por esta tabla.

---

## 8. Fuentes principales (verificación)

- Artificial Analysis Speech Arena / leaderboard open (20 nov 2026): <https://17nas.com/tts-leaderboard.php?f=open&%3Blang=zh-CN&lang=en-US>
- Ranking nov 2026 con ELO: <https://www.teamday.ai/blog/best-ai-voice-models-2026>
- Comparativa local TTS nov 2026: <https://vdf.ai/blog/best-local-tts-models/>
- Guía open-source TTS (licencias y commits, 12 nov 2026): <https://www.assemblyai.com/blog/free-open-source-text-to-speech>
- Comparativa ElevenLabs open-source (abr 2026): <https://github.com/bettercallzaal/ZAOOS/blob/main/research/music/329-open-source-tts-elevenlabs-alternatives/README.md>
- Awesome Audio Generation 2026: <https://github.com/yepicaiaaron/awesome-audio-generation-2026/blob/HEAD/README.md>
- Kaggle GPU: 30 h/semana, 12 h/sesión, T4×2: <https://dev.to/viswaretas_kotra/how-can-you-get-free-cloud-gpus-for-ai-training-522f>

*Nota metodológica (skill wide-research): la tarea se diseñó para fan-out paralelo con un coordinador y un worker por modelo; en esta ejecución no fue posible lanzar subagentes (profundidad máxima 2/2, sin capacidad de spawn), así que la investigación se hizo secuencialmente por lotes de búsqueda, con el mismo esquema de campos por modelo. Cobertura: 17 modelos verificados + 10 en trending, 100 % de la lista mínima pedida.*
