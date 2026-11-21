"""Gestor de modelos con carga perezosa.

REGLA DE ORO: en el arranque no se carga ningún modelo. Cada endpoint
pide el suyo con `manager.require(...)`; la primera llamada lo descarga
(si hace falta) y lo deja en caché; las siguientes lo reutilizan.

Modelos (identificadores exactos de RESEARCH.md):
- kokoro: hexgrad/Kokoro-82M, paquete `kokoro==0.9.4`, KPipeline.
- qwen3-tts-1.7b (Base): Qwen/Qwen3-TTS-12Hz-1.7B-Base, paquete
  `qwen-tts==0.1.1`, Qwen3TTSModel.generate_voice_clone (3 s).
- qwen3-tts-1.7b-customvoice: Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice,
  9 voces fijas con control por instrucciones.
- qwen3-tts-1.7b-voicedesign: Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign.
- qwen3-tts-0.6b: Qwen/Qwen3-TTS-12Hz-0.6B-Base (plan B de VRAM).
- whisper-large-v3 / small: faster-whisper (Systran), MIT.
- demucs: facebookresearch/demucs, htdemucs, MIT.
- stable-audio-open-1.0: stabilityai/stable-audio-open-1.0, repo con
  términos (hay que aceptarlos en HF y poner HF_TOKEN en el entorno).
- voxcpm2: OpenBMB VoxCPM2, Apache 2.0, ~8 GB VRAM. Registrado pero
  NO integrado todavía: su API Python no se verificó en esta sesión
  y no se finge una integración. Ver PENDIENTES_KAGGLE.md.

NO se usan: Chatterbox (retirado ago 2026), Coqui/XTTS (cerrado dic
2025), Fish S2 Pro / Drama 3 (no caben en una T4 de 16 GB).

Si un modelo no está instalado o no hay GPU, el endpoint devuelve 503
con un mensaje claro ("arranca el backend GPU"), nunca un error
genérico ni un audio falso.
"""

import logging
import threading

import numpy as np

from .audio_utils import normalize_loudness
from .config import settings

log = logging.getLogger("elevenlabs-clon.engines")

LANG_NAMES = {
    "es": "Spanish", "en": "English", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "ja": "Japanese",
    "ko": "Korean", "ru": "Russian", "zh": "Chinese",
}

# Códigos reales de Kokoro: solo a, b, e, f, h, i, j, p, z (A5).
# Kokoro NO tiene alemán, coreano ni ruso: pedirlos ya no cae en
# silencio al pipeline inglés americano, se rechaza con 400 en tts.py.
KOKORO_LANG_CODES = {
    "es": "e", "en": "a", "fr": "f", "it": "i",
    "pt": "p", "ja": "j", "zh": "z",
}

# Voces fijas de Kokoro-82M (subset curado; la lista completa tiene 54).
# Español: ef_dora, em_alex, em_santa (sin nota de calidad en VOICES.md:
# probar ef_dora primero, ver RESEARCH.md §2.1).
KOKORO_VOICES = {
    "ef_dora": {"language": "es", "gender": "female", "name": "Dora (español)"},
    "em_alex": {"language": "es", "gender": "male", "name": "Alex (español)"},
    "em_santa": {"language": "es", "gender": "male", "name": "Santa (español)"},
    "af_heart": {"language": "en", "gender": "female", "name": "Heart (inglés)"},
    "af_bella": {"language": "en", "gender": "female", "name": "Bella (inglés)"},
    "af_sarah": {"language": "en", "gender": "female", "name": "Sarah (inglés)"},
    "am_adam": {"language": "en", "gender": "male", "name": "Adam (inglés)"},
    "am_michael": {"language": "en", "gender": "male", "name": "Michael (inglés)"},
    "bf_emma": {"language": "en", "gender": "female", "name": "Emma (inglés GB)"},
    "bm_george": {"language": "en", "gender": "male", "name": "George (inglés GB)"},
}

# Voces fijas de Qwen3-TTS CustomVoice (9 voces premium del fabricante).
QWEN_CUSTOM_SPEAKERS = {
    "Vivian": {"language": "zh", "gender": "female"},
    "Serena": {"language": "zh", "gender": "female"},
    "Uncle_Fu": {"language": "zh", "gender": "male"},
    "Dylan": {"language": "zh", "gender": "male"},
    "Eric": {"language": "zh", "gender": "male"},
    "Ryan": {"language": "en", "gender": "male"},
    "Aiden": {"language": "en", "gender": "male"},
    "Ono_Anna": {"language": "ja", "gender": "female"},
    "Sohee": {"language": "ko", "gender": "female"},
}

MODEL_REGISTRY = {
    "kokoro": {
        "kind": "tts-fijo", "hf_repo": "hexgrad/Kokoro-82M",
        "vram_gb": 1, "device": "cpu", "license": "Apache-2.0",
        "note": "Narración rápida en CPU. No clona.",
    },
    "qwen3-tts-1.7b": {
        "kind": "tts-clon", "hf_repo": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        "vram_gb": 8, "device": "cuda", "license": "Apache-2.0",
        "note": "Clonación zero-shot desde 3 s. Primario en GPU. Piso 8 GB VRAM (fuente secundaria) + tokenizer 0,68 GB; medir en Kaggle junto a Whisper (PENDIENTES_KAGGLE.md punto 10)."
    },
    "qwen3-tts-0.6b": {
        "kind": "tts-clon", "hf_repo": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
        "vram_gb": 4, "device": "cuda", "license": "Apache-2.0",
        "note": "Plan B si la VRAM aprieta.",
    },
    "qwen3-tts-1.7b-customvoice": {
        "kind": "tts-fijo",
        "hf_repo": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        "vram_gb": 8, "device": "cuda", "license": "Apache-2.0",
        "note": "9 voces premium con control por instrucciones. Piso 8 GB VRAM (fuente secundaria) + tokenizer 0,68 GB."
    },
    "qwen3-tts-1.7b-voicedesign": {
        "kind": "voice-design",
        "hf_repo": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        "vram_gb": 8, "device": "cuda", "license": "Apache-2.0",
        "note": "Diseña voces desde descripción en texto. Piso 8 GB VRAM (fuente secundaria) + tokenizer 0,68 GB."
    },
    "whisper-large-v3": {
        "kind": "stt", "hf_repo": "Systran/faster-whisper-large-v3",
        "vram_gb": 6, "device": "cuda", "license": "MIT (pesos OpenAI)",
        "note": "Transcripción, ~100 idiomas. En CPU usar small.",
    },
    "whisper-small": {
        "kind": "stt", "hf_repo": "Systran/faster-whisper-small",
        "vram_gb": 2, "device": "cpu", "license": "MIT (pesos OpenAI)",
        "note": "STT ligero para CPU (InstaBox).",
    },
    "demucs": {
        "kind": "isolate", "hf_repo": "facebookresearch/demucs",
        "vram_gb": 3, "device": "cuda", "license": "MIT",
        "note": "Aislamiento de voz (htdemucs).",
    },
    "stable-audio-open-1.0": {
        "kind": "sfx", "hf_repo": "stabilityai/stable-audio-open-1.0",
        "vram_gb": 8, "device": "cuda",
        "license": "Stability AI Community License (<1M USD/año)",
        "note": "SFX hasta 47 s. Repo con términos: aceptarlos en HF.",
    },
    "voxcpm2": {
        "kind": "tts-clon", "hf_repo": "openbmb/VoxCPM2",
        "vram_gb": 8, "device": "cuda", "license": "Apache-2.0",
        "note": "Máxima calidad opcional (48 kHz, LoRA). "
        "NO INTEGRADO todavía: falta verificar su API Python.",
    },
}


class ModelUnavailable(Exception):
    """El modelo no está disponible: 503 con mensaje claro para el usuario."""

    def __init__(self, model: str, reason: str) -> None:
        self.model = model
        self.reason = reason
        super().__init__(f"{model}: {reason}")


def _torch():
    try:
        import torch

        return torch
    except ImportError:
        return None


def gpu_available() -> bool:
    if settings.cpu_only:
        return False
    torch = _torch()
    return bool(torch and torch.cuda.is_available())


def vram_free_gb() -> float | None:
    torch = _torch()
    if not torch or not torch.cuda.is_available():
        return None
    try:
        free, _total = torch.cuda.mem_get_info()
        return round(free / 1024**3, 2)
    except Exception:
        return None


class ModelManager:
    """Carga perezosa + caché + descarga para no saturar la VRAM."""

    def __init__(self) -> None:
        self._loaded: dict[str, object] = {}
        self._lock = threading.Lock()
        self._kokoro_pipelines: dict[str, object] = {}

    # -- estado -----------------------------------------------------------
    def loaded_models(self) -> list[str]:
        return sorted(self._loaded)

    def status(self) -> list[dict]:
        out = []
        for name, info in MODEL_REGISTRY.items():
            out.append(
                {
                    "model": name,
                    "kind": info["kind"],
                    "loaded": name in self._loaded,
                    "device": info["device"],
                    "vram_gb_estimate": info["vram_gb"],
                    "license": info["license"],
                    "hf_repo": info["hf_repo"],
                    "note": info["note"],
                }
            )
        return out

    def unload(self, name: str) -> bool:
        with self._lock:
            if name in self._loaded:
                del self._loaded[name]
                log.info("Modelo descargado: %s", name)
                return True
            return False

    def unload_all_except(self, keep: str | None = None) -> None:
        """Libera VRAM antes de cargar un modelo grande."""
        with self._lock:
            for name in list(self._loaded):
                if name != keep:
                    del self._loaded[name]
        torch = _torch()
        if torch and torch.cuda.is_available():
            torch.cuda.empty_cache()

    # -- Kokoro -------------------------------------------------------------
    def kokoro_pipeline(self, lang_code: str):
        if lang_code in self._kokoro_pipelines:
            return self._kokoro_pipelines[lang_code]
        try:
            from kokoro import KPipeline
        except ImportError:
            raise ModelUnavailable(
                "kokoro",
                "El paquete `kokoro` no está instalado. "
                "En Kaggle: pip install -r requirements-gpu.txt. "
                "En CPU: pip install -r requirements-cpu.txt "
                "(y apt install espeak-ng).",
            )
        try:
            pipe = KPipeline(lang_code=lang_code)
        except Exception as exc:  # espeak-ng ausente, pesos, etc.
            raise ModelUnavailable(
                "kokoro",
                f"No se pudo iniciar Kokoro ({lang_code}): {exc}. "
                "Comprueba que espeak-ng está instalado.",
            )
        self._kokoro_pipelines[lang_code] = pipe
        if "kokoro" not in self._loaded:
            self._loaded["kokoro"] = pipe
        return pipe

    def synthesize_kokoro(
        self, text: str, voice: str, speed: float, language: str,
        normalize: bool = True,
    ) -> tuple[np.ndarray, int]:
        """Devuelve (muestras float32 mono, sr=24000)."""
        lang_code = KOKORO_LANG_CODES.get(language)
        if lang_code is None:
            # A5: Kokoro no tiene pipeline para este idioma; no fingir
            # inglés americano. tts.py lo convierte en 400.
            raise ValueError(
                f"Kokoro no tiene pipeline para el idioma '{language}'. "
                "Idiomas con pipeline: es, en, fr, it, pt, ja, zh."
            )
        pipe = self.kokoro_pipeline(lang_code)
        chunks = []
        for _gs, _ps, audio in pipe(text, voice=voice, speed=speed):
            chunks.append(np.asarray(audio, dtype=np.float32))
        if not chunks:
            raise ModelUnavailable("kokoro", "Kokoro no devolvió audio.")
        samples = np.concatenate(chunks)
        if normalize:
            samples = normalize_loudness(samples, 24000)
        return samples, 24000

    # -- Qwen3-TTS ----------------------------------------------------------
    def qwen_model(self, variant: str):
        """Carga perezosa de un Qwen3TTSModel. `variant` es la clave del registro."""
        if variant in self._loaded:
            return self._loaded[variant]
        if settings.cpu_only:
            raise ModelUnavailable(
                variant,
                "Qwen3-TTS necesita GPU. Arranca el backend GPU "
                "(notebook de Kaggle) o usa Kokoro en CPU.",
            )
        if not gpu_available():
            raise ModelUnavailable(
                variant,
                "No hay GPU disponible en este servidor. "
                "Arranca el backend GPU (notebook de Kaggle).",
            )
        try:
            import torch
            from qwen_tts import Qwen3TTSModel
        except ImportError:
            raise ModelUnavailable(
                variant,
                "El paquete `qwen-tts` no está instalado. "
                "En Kaggle: pip install -r requirements-gpu.txt.",
            )
        repo = MODEL_REGISTRY[variant]["hf_repo"]
        # Descarga el resto de modelos grandes para que quepa en la T4.
        self.unload_all_except(keep=None)
        kwargs: dict = {
            "device_map": "cuda:0",
            "dtype": torch.bfloat16,
        }
        try:
            model = Qwen3TTSModel.from_pretrained(
                repo, attn_implementation="flash_attention_2", **kwargs
            )
        except Exception:
            model = Qwen3TTSModel.from_pretrained(repo, **kwargs)
        with self._lock:
            self._loaded[variant] = model
        log.info("Modelo cargado: %s (%s)", variant, repo)
        return model

    def synthesize_qwen_clone(
        self, text: str, ref_audio_path: str, ref_text: str,
        language: str, variant: str = "qwen3-tts-1.7b",
        normalize: bool = True,
    ) -> tuple[np.ndarray, int]:
        """Clonación zero-shot con el modelo Base."""
        model = self.qwen_model(variant)
        lang = LANG_NAMES.get(language)
        if lang is None:
            raise ValueError(
                f"Qwen3-TTS no cubre el idioma '{language}'."
            )
        kwargs: dict = {
            "text": text,
            "language": lang,
            "ref_audio": ref_audio_path,
        }
        if ref_text:
            kwargs["ref_text"] = ref_text
        else:
            kwargs["x_vector_only_mode"] = True
        wavs, sr = model.generate_voice_clone(**kwargs)
        samples = np.asarray(wavs[0], dtype=np.float32)
        if normalize:
            samples = normalize_loudness(samples, int(sr))
        return samples, int(sr)

    def synthesize_qwen_custom(
        self, text: str, speaker: str, language: str,
        instruct: str = "", normalize: bool = True,
    ) -> tuple[np.ndarray, int]:
        model = self.qwen_model("qwen3-tts-1.7b-customvoice")
        lang = LANG_NAMES.get(language)
        if lang is None:
            raise ValueError(
                f"Qwen3-TTS no cubre el idioma '{language}'."
            )
        wavs, sr = model.generate_custom_voice(
            text=text, language=lang, speaker=speaker, instruct=instruct or ""
        )
        samples = np.asarray(wavs[0], dtype=np.float32)
        if normalize:
            samples = normalize_loudness(samples, int(sr))
        return samples, int(sr)

    def design_voices(
        self, text: str, prompt: str, language: str, num: int
    ) -> list[tuple[np.ndarray, int]]:
        """Voice Design: genera `num` candidatos desde la descripción.

        Qwen3-TTS no documenta semilla para diseños distintos en una
        misma llamada (A10): cada candidato se pide con una variante
        explícita del instruct (timbre/ritmo distintos) y se descartan
        los duplicados byte a byte, reintentando con otra variante.
        Si el modelo devuelve el mismo audio pese a todo, se devuelven
        los candidatos distintos que haya, sin fingir variedad.
        """
        model = self.qwen_model("qwen3-tts-1.7b-voicedesign")
        lang = LANG_NAMES.get(language, "Spanish")
        variants = [
            "",
            " Timbre ligeramente más grave.",
            " Timbre ligeramente más agudo.",
            " Ritmo algo más pausado.",
            " Ritmo algo más vivo.",
            " Voz algo más cálida.",
        ]
        out: list[tuple[np.ndarray, int]] = []
        seen: set[bytes] = set()
        for i in range(num * 3):
            if len(out) >= num:
                break
            instruct = prompt + variants[i % len(variants)]
            wavs, sr = model.generate_voice_design(
                text=text, language=lang, instruct=instruct
            )
            samples = np.asarray(wavs[0], dtype=np.float32)
            samples = normalize_loudness(samples, int(sr))
            key = samples.tobytes()
            if key in seen:
                continue
            seen.add(key)
            out.append((samples, int(sr)))
        return out

    # -- Whisper (STT) ------------------------------------------------------
    def whisper_model(self, size: str):
        key = f"whisper-{size}"
        if key in self._loaded:
            return self._loaded[key]
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ModelUnavailable(
                f"whisper-{size}",
                "El paquete `faster-whisper` no está instalado. "
                "En Kaggle: pip install -r requirements-gpu.txt.",
            )
        device = "cuda" if gpu_available() and size == "large-v3" else "cpu"
        compute = "float16" if device == "cuda" else "int8"
        try:
            model = WhisperModel(size, device=device, compute_type=compute)
        except Exception as exc:
            if device == "cuda":
                # En Kaggle, torch cu130 trae libcublas.so.13 pero
                # ctranslate2 (faster-whisper) pide libcublas.so.12:
                # sin esa librería la carga CUDA falla y el doblaje
                # muere en «transcribe». Caer a CPU (int8) antes que
                # dejar el doblaje/STT sin servicio.
                log.warning(
                    "Whisper CUDA falló (%s); reintentando en CPU.", exc
                )
                model = WhisperModel(size, device="cpu", compute_type="int8")
            else:
                raise ModelUnavailable(
                    f"whisper-{size}", f"No se pudo cargar Whisper: {exc}"
                )
        with self._lock:
            self._loaded[key] = model
        return model

    def transcribe(
        self, audio_path: str, language: str | None, size: str,
        word_timestamps: bool, keyterms: list[str] | None = None,
    ) -> tuple[list[dict], dict]:
        model = self.whisper_model(size)
        lang = None if language in (None, "auto") else language
        initial_prompt = None
        if keyterms:
            initial_prompt = "Términos clave: " + ", ".join(keyterms[:50])
        segments, info = model.transcribe(
            audio_path,
            language=lang,
            word_timestamps=word_timestamps,
            initial_prompt=initial_prompt,
        )
        out: list[dict] = []
        for seg in segments:
            words = []
            if word_timestamps and getattr(seg, "words", None):
                words = [
                    {"word": w.word, "start": round(w.start, 3),
                     "end": round(w.end, 3)}
                    for w in seg.words
                ]
            out.append(
                {
                    "start": round(seg.start, 3),
                    "end": round(seg.end, 3),
                    "text": seg.text.strip(),
                    "words": words,
                }
            )
        meta = {
            "language": getattr(info, "language", lang or "auto"),
            "duration_s": round(getattr(info, "duration", 0) or 0, 2),
        }
        return out, meta

    # -- Demucs (aislamiento) ------------------------------------------------
    def isolate_demucs(self, audio_path: str, out_dir: str) -> tuple[str, str]:
        """Separa voz y fondo con htdemucs. Devuelve (vocals, background)."""
        import importlib.util
        import subprocess
        import sys

        if importlib.util.find_spec("demucs") is None:
            raise ModelUnavailable(
                "demucs",
                "El paquete `demucs` no está instalado. "
                "En Kaggle: pip install -r requirements-gpu.txt.",
            )
        proc = subprocess.run(
            [sys.executable, "-m", "demucs", "--two-stems=vocals",
             "-o", out_dir, audio_path],
            capture_output=True, text=True, timeout=1800,
        )
        if proc.returncode != 0:
            raise ModelUnavailable(
                "demucs", f"Demucs falló: {(proc.stderr or '')[-500:]}"
            )
        import glob

        vocals = glob.glob(f"{out_dir}/htdemucs*/vocals.wav")
        other = glob.glob(f"{out_dir}/htdemucs*/no_vocals.wav")
        if not vocals:
            raise ModelUnavailable(
                "demucs", "Demucs terminó sin producir vocals.wav."
            )
        return vocals[0], (other[0] if other else "")

    # -- Stable Audio Open (SFX) ----------------------------------------------
    def sfx_generate(self, prompt: str, duration_s: float) -> tuple[np.ndarray, int]:
        if settings.cpu_only or not gpu_available():
            raise ModelUnavailable(
                "stable-audio-open-1.0",
                "Stable Audio Open necesita GPU. Arranca el backend GPU.",
            )
        key = "stable-audio-open-1.0"
        if key not in self._loaded:
            try:
                import torch
                from diffusers import StableAudioPipeline
            except ImportError:
                raise ModelUnavailable(
                    key,
                    "El paquete `diffusers` no está instalado. "
                    "En Kaggle: pip install -r requirements-gpu.txt.",
                )
            try:
                pipe = StableAudioPipeline.from_pretrained(
                    "stabilityai/stable-audio-open-1.0",
                    torch_dtype=torch.float16,
                    token=settings.hf_token or None,
                )
            except Exception as exc:
                raise ModelUnavailable(
                    key,
                    "No se pudo cargar Stable Audio Open. Es un repo con "
                    f"términos: acéptalos en Hugging Face y pon HF_TOKEN. ({exc})",
                )
            pipe.to("cuda")
            with self._lock:
                self._loaded[key] = pipe
        pipe = self._loaded[key]
        result = pipe(
            prompt, num_inference_steps=100,
            audio_end_in_s=float(duration_s),
        )
        audio = np.asarray(result.audios[0], dtype=np.float32)
        # diffusers devuelve (canales, muestras); pasamos a (muestras, canales).
        if audio.ndim == 2:
            audio = audio.T
        return normalize_loudness(audio, 44100), 44100

    # -- Traducción ES<->EN (doblaje básico) ----------------------------------
    def translate(self, text: str, src: str, tgt: str) -> str:
        """Traducción con MarianMT. Solo pares ES<->EN en este backend."""
        pair = f"{src}-{tgt}"
        if pair not in ("es-en", "en-es"):
            raise ValueError(
                f"Traducción {src}→{tgt} no disponible: el doblaje básico "
                "solo cubre español↔inglés (Helsinki-NLP/opus-mt)."
            )
        key = f"marian-{pair}"
        if key not in self._loaded:
            try:
                from transformers import MarianMTModel, MarianTokenizer
            except ImportError:
                raise ModelUnavailable(
                    key,
                    "El paquete `transformers` no está instalado. "
                    "En Kaggle: pip install -r requirements-gpu.txt.",
                )
            repo = f"Helsinki-NLP/opus-mt-{pair}"
            try:
                tok = MarianTokenizer.from_pretrained(repo)
                model = MarianMTModel.from_pretrained(repo)
            except Exception as exc:
                raise ModelUnavailable(key, f"No se pudo cargar {repo}: {exc}")
            with self._lock:
                self._loaded[key] = (tok, model)
        tok, model = self._loaded[key]
        batch = tok([text], return_tensors="pt", padding=True)
        out = model.generate(**batch)
        return tok.decode(out[0], skip_special_tokens=True)


manager = ModelManager()
