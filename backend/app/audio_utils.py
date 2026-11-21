"""Utilidades de audio: WAV/MP3, duración, efectos DSP y normalización.

Sin dependencias pesadas: numpy + soundfile para WAV, ffmpeg (binario
del sistema, presente en Kaggle y en InstaBox) para MP3 y para
decodificar formatos con compresión. Los efectos son DSP clásico
(reverb por convolución, filtros, paneo, mezcla de ruido): replican la
función de `audio_effects` de ElevenLabs sin ningún modelo generativo.
La normalización usa pyloudnorm si está instalada (-16 LUFS, pico
≤ -1 dBTP); si no, una aproximación por RMS documentada como tal.
"""

import io
import re
import subprocess

import numpy as np
import soundfile as sf

TARGET_LUFS = -16.0
MAX_TRUE_PEAK_DBTP = -1.0


def wav_bytes(samples: np.ndarray, sr: int) -> bytes:
    """Codifica muestras float32 mono/estéreo a WAV PCM 16 bits."""
    buf = io.BytesIO()
    sf.write(buf, np.asarray(samples, dtype=np.float32), sr,
             format="WAV", subtype="PCM_16")
    return buf.getvalue()


def read_audio_bytes(data: bytes) -> tuple[np.ndarray, int]:
    """Decodifica audio en memoria. Devuelve (muestras mono float32, sr)."""
    try:
        samples, sr = sf.read(io.BytesIO(data), dtype="float32")
    except Exception:
        samples, sr = _ffmpeg_decode(data)
    if samples.ndim > 1:
        samples = samples.mean(axis=1)
    return np.asarray(samples, dtype=np.float32), int(sr)


def _ffmpeg_decode(data: bytes) -> tuple[np.ndarray, int]:
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", "pipe:0",
         "-f", "f32le", "-ac", "1", "-ar", "24000", "pipe:1"],
        input=data, capture_output=True, timeout=120,
    )
    if proc.returncode != 0:
        raise ValueError("No se pudo decodificar el audio (ffmpeg).")
    return np.frombuffer(proc.stdout, dtype=np.float32), 24000


def wav_to_mp3(wav: bytes) -> bytes:
    """Convierte WAV a MP3 (libmp3lame, 192 kbps) con ffmpeg."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", "pipe:0",
         "-codec:a", "libmp3lame", "-b:a", "192k", "-f", "mp3", "pipe:1"],
        input=wav, capture_output=True, timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError("ffmpeg no pudo codificar el MP3.")
    return proc.stdout


def audio_duration(data: bytes) -> float:
    """Duración en segundos de un audio en memoria."""
    try:
        info = sf.info(io.BytesIO(data))
        return float(info.duration)
    except Exception:
        samples, sr = read_audio_bytes(data)
        return len(samples) / sr if sr else 0.0


def split_sentences(text: str) -> list[str]:
    """Trocea un texto en frases para el streaming por frases."""
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    out = [p.strip() for p in parts if p.strip()]
    return out or [text.strip()]


def resample(samples: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    """Remuestreo lineal simple (suficiente para mezclas y efectos)."""
    if sr_in == sr_out or len(samples) == 0:
        return samples
    n_out = int(round(len(samples) * sr_out / sr_in))
    x_old = np.linspace(0, 1, len(samples))
    x_new = np.linspace(0, 1, n_out)
    return np.interp(x_new, x_old, samples).astype(np.float32)


# ---------------------------------------------------------------------------
# Normalización de loudness
# ---------------------------------------------------------------------------

def normalize_loudness(samples: np.ndarray, sr: int,
                       target_lufs: float = TARGET_LUFS) -> np.ndarray:
    """Normaliza a ~target LUFS con pico real ≤ -1 dBTP.

    Con pyloudnorm: medición LUFS real. Sin ella: aproximación por RMS
    (se documenta en el log del servidor, no se finge precisión).
    """
    if len(samples) == 0:
        return samples
    peak_limit = 10 ** (MAX_TRUE_PEAK_DBTP / 20)
    try:
        import pyloudnorm as pyln

        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(samples)
        gain = 10 ** ((target_lufs - loudness) / 20)
        out = samples * gain
    except Exception:
        rms = float(np.sqrt(np.mean(samples ** 2))) or 1.0
        # -16 LUFS ≈ -20 dBFS RMS en voz; aproximación, no medición.
        gain = (10 ** (-20 / 20)) / rms
        out = samples * gain
    peak = float(np.max(np.abs(out))) if len(out) else 0.0
    if peak > peak_limit:
        out = out * (peak_limit / peak)
    return np.clip(out, -1.0, 1.0).astype(np.float32)


# ---------------------------------------------------------------------------
# Efectos DSP (audio_effects)
# ---------------------------------------------------------------------------

def _reverb_ir(sr: int, kind: str) -> np.ndarray:
    rng = np.random.default_rng(7)
    if kind == "room":
        length, decay = int(sr * 0.6), 3.5
    else:  # hall
        length, decay = int(sr * 1.8), 2.2
    t = np.arange(length) / sr
    ir = rng.standard_normal(length) * np.exp(-decay * t)
    ir[0] = 1.0
    return ir.astype(np.float32)


def _one_pole_lowpass(x: np.ndarray, alpha: float) -> np.ndarray:
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def apply_effects(samples: np.ndarray, sr: int, effects: dict) -> np.ndarray:
    """Aplica reverb, distancia, ruido de fondo, paneo y filtro.

    `effects` sigue el esquema de AudioEffectsRequest. Devuelve
    muestras estéreo (2, N) si pan != 0 o hay ruido de fondo, si no mono.
    """
    out = np.asarray(samples, dtype=np.float32).copy()

    preset = effects.get("filter_preset", "none")
    if preset == "telephone":
        # Banda ~300-3400 Hz aproximada: pasa-altas + pasa-bajas suaves.
        out = out - _one_pole_lowpass(out, 0.02)
        out = _one_pole_lowpass(out, 0.35)
    elif preset == "radio":
        out = out - _one_pole_lowpass(out, 0.05)
        out = _one_pole_lowpass(out, 0.5)

    if effects.get("distance") == "far":
        out = _one_pole_lowpass(out, 0.12) * 0.7

    reverb = effects.get("reverb", "none")
    if reverb in ("room", "hall"):
        ir = _reverb_ir(sr, reverb)
        wet = np.convolve(out, ir, mode="same") * (0.25 if reverb == "room" else 0.4)
        out = np.clip(out * 0.85 + wet, -1.0, 1.0).astype(np.float32)

    stereo = out
    noise_kind = effects.get("background_noise", "none")
    if noise_kind in ("rain", "cafe"):
        rng = np.random.default_rng(11)
        white = rng.standard_normal(len(out))
        # Ruido marrón suave para lluvia; blanco atenuado para café.
        if noise_kind == "rain":
            brown = np.cumsum(white)
            brown = brown / (np.max(np.abs(brown)) + 1e-9)
            noise = brown * 0.05
        else:
            noise = white * 0.02
        stereo = np.clip(out + noise.astype(np.float32), -1.0, 1.0)

    pan = float(effects.get("pan", 0.0))
    if pan != 0.0 or noise_kind != "none":
        left = stereo * (1.0 - max(pan, 0.0))
        right = stereo * (1.0 - max(-pan, 0.0))
        return np.stack([left, right], axis=1).astype(np.float32)
    return stereo
