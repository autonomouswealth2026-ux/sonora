"""Configuración del backend del clon de ElevenLabs.

Toda la configuración sale de variables de entorno. No hay secretos
ni valores por defecto sensibles en este archivo: si falta un valor,
el servidor arranca en modo abierto y lo avisa en el log (ver README).
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if not raw:
        # Sin configurar: solo localhost (desarrollo). El origen de
        # GitHub Pages se fija con CORS_ORIGINS en producción.
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    return [o.strip() for o in raw.split(",") if o.strip()]


@dataclass
class Settings:
    """Ajustes leídos del entorno en el arranque."""

    host: str = field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _env_int("PORT", 8000))
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "info"))
    # Token opcional: si está vacío, la API queda abierta (solo para uso
    # privado con URL de túnel no publicada). Si tiene valor, todas las
    # rutas /api/v1/* exigen `Authorization: Bearer <token>`.
    api_token: str = field(default_factory=lambda: os.environ.get("API_TOKEN", ""))
    cors_origins: list[str] = field(default_factory=_cors_origins)
    data_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("DATA_DIR", BACKEND_DIR / "data"))
    )
    cpu_only: bool = field(
        default_factory=lambda: os.environ.get("CPU_ONLY", "0") == "1"
    )
    # Límite de subida por defecto (MB). Cada endpoint puede ser más
    # estricto; el de doblaje lo amplía con su propia variable.
    max_upload_mb: int = field(default_factory=lambda: _env_int("MAX_UPLOAD_MB", 100))
    max_clone_mb: int = field(default_factory=lambda: _env_int("MAX_CLONE_MB", 25))
    max_dubbing_mb: int = field(
        default_factory=lambda: _env_int("MAX_DUBBING_MB", 500)
    )
    # Rate limit: peticiones por minuto por IP (general) y para las
    # rutas pesadas (generación de audio).
    rate_limit_per_minute: int = field(
        default_factory=lambda: _env_int("RATE_LIMIT_PER_MINUTE", 60)
    )
    heavy_rate_limit_per_minute: int = field(
        default_factory=lambda: _env_int("HEAVY_RATE_LIMIT_PER_MINUTE", 20)
    )
    # Texto máximo por petición TTS (caracteres). Coincide con FEATURE_MAP.
    max_text_chars: int = field(default_factory=lambda: _env_int("MAX_TEXT_CHARS", 10000))
    # Hugging Face: solo se usa si el modelo lo exige (p. ej. Stable
    # Audio Open, repo con términos). Nunca se escribe en el código.
    hf_token: str = field(default_factory=lambda: os.environ.get("HF_TOKEN", ""))

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def max_clone_bytes(self) -> int:
        return self.max_clone_mb * 1024 * 1024

    @property
    def max_dubbing_bytes(self) -> int:
        return self.max_dubbing_mb * 1024 * 1024


settings = Settings()
