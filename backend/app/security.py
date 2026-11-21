"""Seguridad: autenticación por token, rate limit y validación de uploads.

Checklist replica-backend aplicada (solo lo aplicable a este backend
local sin pagos ni Supabase):
- secretos solo en variables de entorno (ver config.py / .env.example);
- validación de entrada en el servidor en cada ruta (Pydantic + este
  módulo para ficheros);
- rate limits en todo lo que genera audio (la GPU/CPU es el recurso
  escaso);
- uploads con límite de tamaño y de tipo, inspeccionando la cabecera
  real del fichero (magic bytes), no solo la extensión;
- sin datos de usuario en URLs ni en logs (los logs nunca imprimen el
  texto a sintetizar ni el token).
"""

import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import HTTPException, Request, UploadFile, status

from .config import settings

# ---------------------------------------------------------------------------
# Autenticación por token (opcional por entorno)
# ---------------------------------------------------------------------------


def get_token_dependency():
    """Devuelve la dependencia de autenticación para las rutas /api/v1/*.

    Si API_TOKEN está vacío, la API queda abierta (uso privado con URL
    de túnel no publicada). Si tiene valor, exige
    `Authorization: Bearer <token>` en cada petición.
    """

    async def _check(request: Request):
        token = settings.api_token
        if not token:
            return None
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Falta el token: envía Authorization: Bearer <API_TOKEN>.",
            )
        presented = auth[len("Bearer ") :].strip()
        if presented != token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no válido.",
            )
        return None

    return _check


require_auth = get_token_dependency()


async def require_auth_ws(websocket) -> bool:
    """Auth para WebSocket (VERIFICACION B2): Depends(require_auth)
    no se puede inyectar en un WS porque no hay Request que resolver.
    El token llega por cabecera Authorization o ?token= en la URL.
    Devuelve True si pasa; si no, el llamador debe cerrar con 1008.
    """
    token = settings.api_token
    if not token:
        return True
    auth = websocket.headers.get("authorization", "")
    presented = ""
    if auth.startswith("Bearer "):
        presented = auth[len("Bearer "):].strip()
    else:
        presented = (websocket.query_params.get("token") or "").strip()
    return presented == token

# ---------------------------------------------------------------------------
# Rate limit en memoria (por IP, ventana deslizante de 60 s)
# ---------------------------------------------------------------------------


class RateLimiter:
    """Limitador sencillo por IP. Suficiente para 2 usuarios.

    No es distribuido ni persistente: el backend corre en una sola
    sesión de Kaggle/InstaBox y se reinicia con ella.
    """

    def __init__(self) -> None:
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def check(self, key: str, group: str, limit: int, window_s: int = 60) -> None:
        now = time.monotonic()
        bucket = self._hits[(key, group)]
        while bucket and bucket[0] <= now - window_s:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Demasiadas peticiones ({limit}/min). "
                    "Espera un minuto y reintenta."
                ),
            )
        bucket.append(now)


limiter = RateLimiter()


def client_ip(request) -> str:
    """IP del cliente, respetando X-Forwarded-For del túnel (primer salto)."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "desconocida"


async def limit_general(request: Request) -> None:
    limiter.check(client_ip(request), "general", settings.rate_limit_per_minute)


async def limit_heavy(request: Request) -> None:
    """Para rutas que generan audio: límite más bajo."""
    limiter.check(
        client_ip(request), "heavy", settings.heavy_rate_limit_per_minute
    )


# ---------------------------------------------------------------------------
# Validación de uploads
# ---------------------------------------------------------------------------

# Magic bytes por tipo permitido (extensión -> cabeceras válidas).
_MAGIC = {
    "wav": [b"RIFF"],
    "mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    "flac": [b"fLaC"],
    "ogg": [b"OggS"],
    "m4a": [b"ftyp"],
    "mp4": [b"ftyp"],
    "webm": [b"\x1a\x45\xdf\xa3"],
    "aac": [b"\xff\xf1", b"\xff\xf9"],
    "txt": None,  # texto plano: sin cabecera que comprobar
    "pdf": [b"%PDF"],
    "epub": [b"PK\x03\x04"],
    "docx": [b"PK\x03\x04"],
    "pls": None,  # XML de pronunciación
    "xml": None,
}

AUDIO_EXTS = {"wav", "mp3", "flac", "ogg", "m4a", "aac", "webm"}
MEDIA_EXTS = AUDIO_EXTS | {"mp4"}


def _sniff(data: bytes, ext: str) -> bool:
    expected = _MAGIC.get(ext)
    if expected is None:
        return True  # sin cabecera que comprobar (txt/xml)
    head = data[:16]
    return any(m in head for m in expected)


async def read_upload(
    file: UploadFile, allowed_exts: set[str], max_bytes: int
) -> tuple[bytes, str]:
    """Lee y valida un fichero subido. Devuelve (contenido, extensión).

    Errores: 400 extensión no permitida o contenido que no coincide
    con su tipo; 413 fichero demasiado grande.
    """
    filename = file.filename or "sin-nombre"
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Formato no admitido: .{ext or 'sin extensión'}. "
                f"Permitidos: {', '.join(sorted(allowed_exts))}."
            ),
        )
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El fichero está vacío.",
        )
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Fichero demasiado grande: {len(data) / 1024 / 1024:.1f} MB "
                f"(máximo {max_bytes / 1024 / 1024:.0f} MB)."
            ),
        )
    if not _sniff(data, ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El contenido del fichero no coincide con su extensión .{ext}. "
                "Renómbralo con su formato real o conviértelo a WAV/MP3."
            ),
        )
    return data, ext
