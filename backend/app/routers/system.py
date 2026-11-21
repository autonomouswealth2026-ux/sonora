"""Rutas de sistema: health y catálogo de modelos. Públicas (sin token)."""

import platform

from fastapi import APIRouter

from ..config import settings
from ..engines import gpu_available, manager, vram_free_gb

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """Health check: estado, modelos cargados y VRAM libre."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "python": platform.python_version(),
        "gpu": gpu_available(),
        "cpu_only": settings.cpu_only,
        "vram_free_gb": vram_free_gb(),
        "models_loaded": manager.loaded_models(),
        "auth_required": bool(settings.api_token),
    }


@router.get("/api/v1/health")
def health_v1() -> dict:
    return health()


@router.get("/api/v1/models")
def list_models() -> dict:
    """Modelos registrados, cuáles están cargados y VRAM libre."""
    return {
        "gpu": gpu_available(),
        "cpu_only": settings.cpu_only,
        "vram_free_gb": vram_free_gb(),
        "models": manager.status(),
    }
