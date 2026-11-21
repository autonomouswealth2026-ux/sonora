"""Endpoints de fases 3-4 y no replicables: 501 honesto, sin fingir.

Cada ruta devuelve 501 + qué falta + la alternativa real. Un 501 es
mejor que una función fingida: la auditoría (replica-diff) lo puede
verificar y el usuario sabe exactamente qué no existe todavía.

Fase 3 (501): diálogo multi-hablante, Studio/Projects, Reader.
Fase 4 (501): música, Professional Voice Cloning (LoRA manual),
Voice Remix, agentes conversacionales.
No replicable (501): Eleven Realtime, Realtime Translation, ElevenAI.
STT en vivo (WebSocket): 501 al conectar, con el motivo.
"""

from fastapi import APIRouter, Depends, WebSocket
from fastapi.responses import JSONResponse

from ..security import require_auth, require_auth_ws

# Sin Depends a nivel de router (VERIFICACION B2): la dependencia
# require_auth pide un Request que en WebSocket no se puede inyectar
# y la conexión moría con TypeError antes de cerrarse con 1011.
# Cada ruta HTTP lleva su propio Depends; los WS usan
# require_auth_ws() antes de aceptar.
router = APIRouter(prefix="/api/v1")
AUTH = [Depends(require_auth)]


def not_implemented(feature: str, reason: str, alternative: str) -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={
            "detail": f"{feature} no está implementado todavía.",
            "reason": reason,
            "alternative": alternative,
        },
    )


@router.post("/dialogue", dependencies=AUTH)
def dialogue():
    return not_implemented(
        "Text to Dialogue",
        "Fase 3: la orquestación por segmentos (sintetizar cada línea "
        "con su voz y concatenar) aún no está construida.",
        "Llama a POST /api/v1/tts línea por línea y concatena los audios.",
    )


@router.post("/voices/pro-clone", status_code=202, dependencies=AUTH)
def pro_clone():
    return not_implemented(
        "Professional Voice Cloning",
        "Fase 4: el fine-tuning LoRA de VoxCPM2/Qwen3-TTS es un trabajo "
        "manual por voz (horas de GPU), no un endpoint automático.",
        "Usa POST /api/v1/voices/instant-clone con varias referencias "
        "largas (multi-referencia) o pide el LoRA manual.",
    )


@router.get("/voices/pro-clone/{job_id}", dependencies=AUTH)
def pro_clone_status(job_id: str):
    return not_implemented(
        "Professional Voice Cloning",
        "No hay trabajos de pro-clone: el endpoint de creación es 501.",
        "Usa POST /api/v1/voices/instant-clone.",
    )


@router.post("/voices/{voice_id}/remix", dependencies=AUTH)
def remix_voice(voice_id: str):
    return not_implemented(
        "Voice Remix",
        "Fase 4: el remix (edad, acento) por DSP + regeneración aún no "
        "está construido.",
        "Usa POST /api/v1/audio-effects/apply para tono/velocidad, o "
        "POST /api/v1/voices/design con un prompt derivado.",
    )


@router.post("/music", status_code=202, dependencies=AUTH)
def music():
    return not_implemented(
        "Music",
        "Fase 4: ACE-Step 1.5 / MusicGen no están instalados en este "
        "backend (VRAM y licencia NC en MusicGen).",
        "Genera la música fuera del clon y mézclala con ffmpeg.",
    )


@router.get("/music/{job_id}", dependencies=AUTH)
def music_status(job_id: str):
    return not_implemented(
        "Music",
        "No hay trabajos de música: el endpoint de creación es 501.",
        "Sin alternativa dentro del clon.",
    )


@router.post("/projects", status_code=201, dependencies=AUTH)
def create_project():
    return not_implemented(
        "Studio / Projects",
        "Fase 3: el editor de formato largo (capítulos, párrafos, caché "
        "de fragmentos) es trabajo de aplicación, aún no construido.",
        "Usa POST /api/v1/tts por párrafos y concatena con ffmpeg.",
    )


@router.get("/projects", dependencies=AUTH)
@router.get("/projects/{project_id}", dependencies=AUTH)
@router.post("/projects/{project_id}/chapters", dependencies=AUTH)
@router.post("/projects/{project_id}/chapters/{chapter_id}/paragraphs", dependencies=AUTH)
@router.post("/projects/{project_id}/generate", dependencies=AUTH)
@router.post("/projects/{project_id}/paragraphs/{paragraph_id}/regenerate", dependencies=AUTH)
@router.get("/projects/{project_id}/export", dependencies=AUTH)
@router.delete("/projects/{project_id}", dependencies=AUTH)
def projects_any(project_id: str = "", chapter_id: str = "",
                 paragraph_id: str = ""):
    return not_implemented(
        "Studio / Projects",
        "Fase 3: aún no construido.",
        "Usa POST /api/v1/tts por párrafos y concatena con ffmpeg.",
    )


@router.post("/reader/upload", dependencies=AUTH)
def reader_upload():
    return not_implemented(
        "ElevenReader",
        "Fase 3: la extracción de PDF/ePub y la lectura por capítulos "
        "aún no está construida. Nota REA (v2): en ElevenReader el audio "
        "no es exportable; la alternativa (TTS + descarga MP3) es otra "
        "función, la exportación de Studio, no el Reader.",
        "Extrae el texto del documento y usa POST /api/v1/tts.",
    )


@router.post("/reader/{document_id}/generate", dependencies=AUTH)
@router.get("/reader/{document_id}/audio", dependencies=AUTH)
@router.get("/reader/{document_id}/timings", dependencies=AUTH)
def reader_any(document_id: str = ""):
    return not_implemented(
        "ElevenReader",
        "Fase 3: aún no construido.",
        "Extrae el texto del documento y usa POST /api/v1/tts.",
    )


@router.post("/agents", status_code=201, dependencies=AUTH)
def create_agent():
    return not_implemented(
        "Conversational AI / Agentes",
        "Fase 4: el pipeline STT -> LLM -> TTS por WebSocket aún no está "
        "construido (y su latencia en T4 sería de segundos, no de 100 ms).",
        "Sin alternativa dentro del clon.",
    )


@router.get("/agents/{agent_id}/conversations", dependencies=AUTH)
def agent_conversations(agent_id: str):
    return not_implemented(
        "Conversational AI / Agentes",
        "Fase 4: aún no construido.",
        "Sin alternativa dentro del clon.",
    )


@router.websocket("/agents/{agent_id}/talk")
async def agent_talk(websocket: WebSocket, agent_id: str):
    if not await require_auth_ws(websocket):
        await websocket.close(code=1008, reason="Falta el token.")
        return
    await websocket.accept()
    await websocket.close(
        code=1011,
        reason="Agentes conversacionales no implementados (fase 4).",
    )


@router.get("/realtime", dependencies=AUTH)
def realtime():
    return not_implemented(
        "Eleven Realtime",
        "No replicable en este proyecto: no hay modelo voz-a-voz "
        "open-source con esa calidad y latencia para una T4.",
        "El pipeline por piezas (STT -> LLM -> TTS) es el sustituto "
        "honesto; tampoco está construido (fase 4).",
    )


@router.get("/realtime-translation", dependencies=AUTH)
def realtime_translation():
    return not_implemented(
        "Realtime Translation",
        "No replicable: traducción simultánea con latencia de "
        "conversación, fuera del hardware disponible.",
        "Usa el doblaje por lotes: POST /api/v1/dubbing.",
    )


@router.get("/elevenai", dependencies=AUTH)
def elevenai():
    return not_implemented(
        "ElevenAI",
        "No replicable como producto (app de Mac, captura de reuniones "
        "sin bot). El dictado aislado es POST /api/v1/stt.",
        "Usa POST /api/v1/stt para dictado y transcripción.",
    )


@router.websocket("/stt/stream")
async def stt_stream(websocket: WebSocket):
    if not await require_auth_ws(websocket):
        await websocket.close(code=1008, reason="Falta el token.")
        return
    await websocket.accept()
    await websocket.close(
        code=1011,
        reason="Transcripcion en vivo no disponible: usa POST /api/v1/stt "
        "por lotes (latencia de segundos, no de 150 ms).",
    )
