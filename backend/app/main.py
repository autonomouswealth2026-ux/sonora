"""Backend del clon de ElevenLabs: FastAPI + modelos locales.

Arranque: NO carga ningún modelo (carga perezosa en engines.py).
Rutas: /health, /docs, /api/v1/* (ver routers/). OpenAPI automático.
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .engines import ModelUnavailable
from .routers import (
    dubbing,
    history,
    isolate,
    not_implemented,
    pronunciation,
    sfx,
    sts,
    stt,
    system,
    tts,
    voices,
)

log = logging.getLogger("elevenlabs-clon")

app = FastAPI(
    title="Clon de ElevenLabs (local)",
    description=(
        "TTS, clonación de voz zero-shot, Voice Design, STT, aislamiento, "
        "diccionario, historial, SFX, voice changer y doblaje con modelos "
        "open-source en local. Presupuesto cero; 2 usuarios. "
        "Las funciones de fases 3-4 devuelven 501."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type",
                   "ngrok-skip-browser-warning"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limit general en /api/v1/* (las rutas pesadas añaden el suyo)."""
    if request.url.path.startswith("/api/v1"):
        from .security import client_ip, limiter

        # A15: HTTPException dentro del middleware no la gestiona
        # ningún handler de FastAPI y llegaba como 500. Se convierte
        # aquí en 429 JSON.
        try:
            limiter.check(
                client_ip(request), "general",
                settings.rate_limit_per_minute,
            )
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )
    return await call_next(request)


@app.exception_handler(ModelUnavailable)
async def model_unavailable_handler(request: Request, exc: ModelUnavailable):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc),
                 "hint": "Si es un modelo GPU, arranca el backend GPU "
                 "(notebook de Kaggle)."},
    )


@app.on_event("startup")
async def startup() -> None:
    logging.basicConfig(level=settings.log_level.upper())
    if not settings.api_token:
        log.warning(
            "API_TOKEN vacío: la API está ABIERTA. No publiques la URL "
            "del túnel. Pon API_TOKEN en el entorno para exigir token."
        )
    log.info("CORS permitido para: %s", ", ".join(settings.cors_origins))
    log.info("CPU_ONLY=%s  DATA_DIR=%s  modelos: ninguno cargado "
             "(carga perezosa)", settings.cpu_only, settings.data_dir)


@app.get("/")
def root() -> dict:
    return {
        "service": "clon-elevenlabs-backend",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


app.include_router(system.router)
app.include_router(tts.router)
app.include_router(voices.router)
app.include_router(stt.router)
app.include_router(isolate.router)
app.include_router(pronunciation.router)
app.include_router(history.router)
app.include_router(sfx.router)
app.include_router(sts.router)
app.include_router(dubbing.router)
app.include_router(not_implemented.router)
