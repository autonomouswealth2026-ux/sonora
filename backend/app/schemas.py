"""Esquemas Pydantic: validación de entrada en el servidor en cada ruta.

Los límites reproducen FEATURE_MAP.md (texto 1..10000, velocidad
0.5..2.0, etc.). Un cuerpo que no cumple devuelve 422 con el detalle
de Pydantic; nunca llega al motor.
"""

from pydantic import BaseModel, Field

LANGUAGES = ["es", "en", "fr", "de", "it", "pt", "ja", "ko", "ru", "zh"]
# Lista cerrada de idiomas (A16): un código libre como "xx" ya no cae
# en silencio a español; Pydantic lo rechaza con 422.
LANGUAGE_PATTERN = r"^(es|en|fr|de|it|pt|ja|ko|ru|zh)$"


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    voice_id: str = Field(..., min_length=1, max_length=64)
    model: str = Field(
        default="auto",
        pattern=r"^(auto|kokoro|qwen3-tts-0.6b|qwen3-tts-1.7b|"
        r"qwen3-tts-1.7b-customvoice)$",
    )
    language: str = Field(default="es", pattern=LANGUAGE_PATTERN)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    format: str = Field(default="mp3", pattern=r"^(mp3|wav)$")
    stability: float | None = Field(default=None, ge=0.0, le=1.0)
    # similarity existe en el contrato, pero NINGÚN motor de este
    # backend la usa: Qwen3-TTS no expone similitud y Kokoro tampoco.
    # El frontend no la envía nunca; si llega, synthesize() la
    # rechaza con 422 en vez de ignorarla en silencio (B4).
    similarity: float | None = Field(default=None, ge=0.0, le=1.0)
    style_exaggeration: float | None = Field(default=None, ge=0.0, le=1.0)
    dictionary_id: str | None = Field(default=None, max_length=64)
    audio_effects: dict | None = None
    # normalize (M9): el interruptor de Ajustes. El backend normalizaba
    # siempre a -16 LUFS; con normalize=false no normaliza.
    normalize: bool = True


class OpenAISpeechRequest(BaseModel):
    """Compatibilidad parcial con la API de OpenAI (/v1/audio/speech)."""

    model: str = Field(..., min_length=1, max_length=64)
    input: str = Field(..., min_length=1, max_length=10000)
    voice: str = Field(..., min_length=1, max_length=64)
    response_format: str = Field(default="mp3", pattern=r"^(mp3|wav)$")
    speed: float = Field(default=1.0, ge=0.25, le=4.0)


class VoiceDesignRequest(BaseModel):
    prompt: str = Field(..., min_length=20, max_length=1000)
    language: str = Field(default="es", pattern=LANGUAGE_PATTERN)
    num_previews: int = Field(default=3, ge=1, le=3)


class VoiceDesignSaveRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


# VoiceRemixRequest eliminado (L2): el remix es 501 y ningún
# endpoint usaba este esquema.

class STTRequest(BaseModel):
    language: str = Field(default="auto", pattern=r"^(auto|[a-z]{2})$")
    model: str = Field(default="large-v3", pattern=r"^(small|medium|large-v3)$")
    diarize: bool = False
    word_timestamps: bool = True
    keyterms: list[str] = Field(default_factory=list, max_length=1000)
    output_format: str = Field(default="json", pattern=r"^(json|srt|vtt|txt)$")


class SFXRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    duration_s: float = Field(default=10, ge=1, le=47)
    num_variants: int = Field(default=1, ge=1, le=3)
    model: str = Field(default="stable-audio-open-1.0")


class STSRequest(BaseModel):
    target_voice_id: str = Field(..., min_length=1, max_length=64)
    method: str = Field(
        default="stt-tts", pattern=r"^(voice-conversion|stt-tts)$"
    )


class DubbingRequest(BaseModel):
    source_language: str = Field(default="auto", pattern=r"^(auto|[a-z]{2})$")
    target_languages: list[str] = Field(default_factory=lambda: ["en"], max_length=3)
    voice_mode: str = Field(
        default="clone-original", pattern=r"^(clone-original|fixed-voice-id)$"
    )
    fixed_voice_id: str | None = Field(default=None, max_length=64)
    keep_background_audio: bool = True


class DubbingSegmentEdit(BaseModel):
    translated_text: str = Field(..., min_length=1, max_length=2000)


class PronunciationRuleCreate(BaseModel):
    word: str = Field(..., min_length=1, max_length=120)
    replacement: str = Field(..., min_length=1, max_length=200)
    phonetic: str = Field(default="", max_length=200)
    language: str = Field(default="es", pattern=LANGUAGE_PATTERN)


class PronunciationRuleUpdate(BaseModel):
    word: str | None = Field(default=None, min_length=1, max_length=120)
    replacement: str | None = Field(default=None, min_length=1, max_length=200)
    phonetic: str | None = Field(default=None, max_length=200)
    language: str | None = Field(default=None, pattern=LANGUAGE_PATTERN)


class AudioEffectsRequest(BaseModel):
    reverb: str = Field(default="none", pattern=r"^(none|room|hall)$")
    distance: str = Field(default="close", pattern=r"^(close|far)$")
    background_noise: str = Field(
        default="none", pattern=r"^(none|rain|cafe)$"
    )
    pan: float = Field(default=0.0, ge=-1.0, le=1.0)
    filter_preset: str = Field(
        default="none", pattern=r"^(none|telephone|radio)$"
    )
