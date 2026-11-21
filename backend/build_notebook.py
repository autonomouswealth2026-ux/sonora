"""Genera backend/kaggle_notebook.ipynb (JSON nbformat 4, sin dependencias).

Se genera con un script en vez de escribir el JSON a mano: el notebook
tiene celdas largas de shell y es fácil romper el JSON. Para regenerar:
    python3 build_notebook.py
"""

import json
from pathlib import Path

REPO_URL = "https://github.com/carlosmiguelvaldesrodriguez-prog/elevenlabs-clon.git"


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {},
            "source": source.splitlines(keepends=True)}


def code(source: str) -> dict:
    return {"cell_type": "code", "metadata": {},
            "execution_count": None, "outputs": [],
            "source": source.splitlines(keepends=True)}


CELLS = [
    md("""# Clon de ElevenLabs — backend en Kaggle (2× T4)

Ejecuta las celdas **en orden, de arriba abajo**. Al final obtienes una URL
`https://....trycloudflare.com`: **cópiala y pégala en Settings de la app**
(frontend en GitHub Pages).

**Antes de empezar (en Kaggle, desde el teléfono):**
1. Abre este notebook y toca **⋮ → Accelerator → GPU T4 x2**.
2. En el panel derecho, **Settings → Internet: ON**.
3. Tu cuenta de Kaggle debe estar verificada por teléfono (requisito de GPU).
4. La sesión dura **12 h como máximo** y la URL del túnel **cambia en cada
   arranque**: hay que copiarla de nuevo cada vez.

Opcional: en **Add-ons → Secrets** añade `API_TOKEN` (un texto secreto
inventado por ti) para que la API exija token. Si no lo pones, la celda 5
genera uno aleatorio y lo imprime: la API YA NO queda abierta en Kaggle
(A17). En cualquier caso, copia el token en Ajustes de la app.
"""),
    code("""# Celda 1 — Comprueba GPU y Python
import platform, sys
print("Python:", platform.python_version())
try:
    import torch
    print("torch:", torch.__version__)
    print("CUDA disponible:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPUs:", torch.cuda.device_count(), "-", torch.cuda.get_device_name(0))
except ImportError:
    print("torch NO instalado (Kaggle normalmente ya lo trae).")
"""),
    code("""# Celda 2 — Trae el código del backend
# Vía A (recomendada): el repo ya está en GitHub y contiene la carpeta backend/.
# Vía B: sube la carpeta backend/ como dataset de Kaggle llamado
#        "elevenlabs-backend" (Add data → Upload) y se usa esa copia.
import os, subprocess, sys
from pathlib import Path

REPO_URL = os.environ.get("REPO_URL", "REPO_URL_PLACEHOLDER")
BACKEND_DIR = None
dataset_dir = Path("/kaggle/input/elevenlabs-backend")
if dataset_dir.exists() and (dataset_dir / "app" / "main.py").exists():
    BACKEND_DIR = dataset_dir
    print("Backend desde dataset de Kaggle:", BACKEND_DIR)
elif (Path("/kaggle/working/backend/app/main.py").exists()):
    BACKEND_DIR = Path("/kaggle/working/backend")
    print("Backend ya presente en /kaggle/working/backend")
else:
    print("Clonando el repo:", REPO_URL)
    r = subprocess.run(["git", "clone", REPO_URL, "/kaggle/working/elevenlabs-clon"],
                       capture_output=True, text=True)
    print(r.stdout[-500:], r.stderr[-500:])
    cand = Path("/kaggle/working/elevenlabs-clon/backend")
    if (cand / "app" / "main.py").exists():
        BACKEND_DIR = cand
        print("Backend clonado en:", BACKEND_DIR)
    else:
        raise SystemExit(
            "NO se encontró backend/app/main.py. Sube la carpeta backend/ "
            "como dataset 'elevenlabs-backend' o haz push del repo a GitHub "
            "y vuelve a ejecutar esta celda."
        )
os.environ["BACKEND_DIR"] = str(BACKEND_DIR)
print("BACKEND_DIR =", BACKEND_DIR)
"""),
    code("""# Celda 3 — Dependencias del sistema + Python (tarda varios minutos)
import subprocess, sys
from pathlib import Path
backend = Path(os.environ["BACKEND_DIR"])
print("Instalando espeak-ng y ffmpeg (necesarios para Kokoro)...")
subprocess.run(["apt-get", "update", "-qq"], check=False)
subprocess.run(["apt-get", "install", "-qq", "-y", "espeak-ng", "ffmpeg"], check=False)
print("Instalando requirements-gpu.txt...")
r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r",
                    str(backend / "requirements-gpu.txt")],
                   capture_output=True, text=True)
print(r.stdout[-1000:])
print(r.stderr[-2000:])
print("Return code:", r.returncode)
"""),
    code("""# Celda 4 — Descarga los pesos (Qwen3-TTS + Kokoro + Whisper)
# Identificadores exactos de RESEARCH.md. La primera vez tarda varios
# minutos (varios GB); Kaggle los guarda en caché entre sesiones.
import subprocess, sys
MODELS = [
    "Qwen/Qwen3-TTS-Tokenizer-12Hz",
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "hexgrad/Kokoro-82M",
]
for repo in MODELS:
    print("Descargando", repo, "...")
    r = subprocess.run(["huggingface-cli", "download", repo],
                       capture_output=True, text=True)
    print("  ->", "OK" if r.returncode == 0 else r.stderr[-300:])
print("Descargando Whisper large-v3 (faster-whisper)...")
r = subprocess.run([sys.executable, "-c",
    "from faster_whisper import WhisperModel; "
    "m = WhisperModel('large-v3', device='cuda', compute_type='float16'); "
    "del m; print('Whisper large-v3 listo')"],
    capture_output=True, text=True)
print(r.stdout[-500:], r.stderr[-500:])
print("Pesos listos.")
"""),
    code("""# Celda 5 — Arranca el servidor FastAPI en segundo plano
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path

backend = Path(os.environ["BACKEND_DIR"])
log = open(backend / "server.log", "wb")
env = dict(os.environ)
env["PORT"] = "8000"
# B6: CORS para el frontend en GitHub Pages. Sin esto el navegador
# bloquea todas las llamadas (Pages y trycloudflare son orígenes
# distintos). Se puede sobreescribir con CORS_ORIGINS en Secrets.
env["CORS_ORIGINS"] = os.environ.get(
    "CORS_ORIGINS",
    "https://carlosmiguelvaldesrodriguez-prog.github.io/elevenlabs-clon",
)
# A17: en Kaggle el token es OBLIGATORIO. Si no viene en Secrets, se
# genera uno aleatorio y se imprime: hay que copiarlo en Ajustes.
import secrets
if not env.get("API_TOKEN"):
    env["API_TOKEN"] = secrets.token_urlsafe(24)
    print("API_TOKEN generado (la API exige token en Kaggle):")
    print(" ", env["API_TOKEN"])
    print("Copialo en Ajustes de la app, campo Token.")
else:
    print("API_TOKEN tomado de Secrets de Kaggle.")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app",
     "--host", "0.0.0.0", "--port", "8000"],
    cwd=str(backend), stdout=log, stderr=subprocess.STDOUT,
    env=env, start_new_session=True,
)
print("Servidor lanzado, PID:", proc.pid)
print("Esperando a /health ...")
ok = False
for i in range(60):
    time.sleep(2)
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as resp:
            print("HEALTH:", json.loads(resp.read()))
            ok = True
            break
    except Exception:
        pass
if not ok:
    print("El servidor no respondió. Mira el final de server.log:")
    print((backend / "server.log").read_text()[-3000:])
else:
    print("Servidor UP. Ningún modelo cargado todavía (carga perezosa).")
"""),
    code("""# Celda 6 — Túnel trycloudflare: imprime la URL https final
# *** COPIA LA URL QUE IMPRIME ESTA CELDA Y PÉGALA EN SETTINGS DE LA APP ***
import re, subprocess, time
from pathlib import Path

backend = Path(os.environ["BACKEND_DIR"])
cf = backend / "cloudflared"
if not cf.exists():
    print("Descargando cloudflared...")
    subprocess.run(["wget", "-q",
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
        "-O", str(cf)], check=False)
    cf.chmod(0o755)
log = open(backend / "cloudflared.log", "wb")
proc = subprocess.Popen(
    [str(cf), "tunnel", "--url", "http://localhost:8000"],
    stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
)
print("Túnel lanzado, PID:", proc.pid)
url = None
for i in range(45):
    time.sleep(2)
    text = (backend / "cloudflared.log").read_text(errors="ignore")
    m = re.search(r"https://[a-z0-9-]+\\.trycloudflare\\.com", text)
    if m:
        url = m.group(0)
        break
if url:
    print()
    print("=" * 60)
    print("  URL DEL BACKEND (copiala en Settings de la app):")
    print(" ", url)
    print("=" * 60)
    print()
    print("Comprueba en el navegador:", url + "/health")
    print("La sesión dura 12 h. No cierres esta pestaña de Kaggle.")
else:
    print("No apareció la URL. Últimas líneas de cloudflared.log:")
    print((backend / "cloudflared.log").read_text(errors="ignore")[-2000:])
"""),
    md("""## Si algo falla

- **`/health` no responde**: abre `server.log` (en la carpeta del backend,
  panel derecho de Kaggle → Files) y mira el error al final.
- **La URL no aparece**: espera 1 minuto y vuelve a ejecutar solo la celda 6.
- **`torch` no instalado**: en una celda nueva ejecuta
  `!pip install torch --index-url https://download.pytorch.org/whl/cu124`
  y repite desde la celda 3.
- **Error de cuota GPU (30 h/semana)**: espera al reset semanal de Kaggle.

## Alternativa: ngrok (URL fija, con cuenta gratuita)

Si te molesta copiar la URL en cada sesión: crea una cuenta en ngrok, copia
tu authtoken en Secrets de Kaggle como `NGROK_TOKEN`, y en vez de la celda 6
ejecuta en una celda nueva:

```python
import subprocess, time
subprocess.run(["pip", "install", "-q", "pyngrok"], check=True)
from pyngrok import ngrok
import os
ngrok.set_auth_token(os.environ["NGROK_TOKEN"])
tunnel = ngrok.connect(8000)
print("URL fija:", tunnel.public_url)
```

Ojo: el plan gratis de ngrok tiene 1 GB de transferencia al mes.

## Para parar

Detén el notebook (Run → Interrupt / apaga la sesión). La URL muere con la
sesión: la próxima vez hay que repetir desde la celda 5.
"""),
]

NB = {
    "cells": CELLS,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python",
                       "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "kaggle_notebook.ipynb"
    text = json.dumps(NB, indent=1, ensure_ascii=False)
    text = text.replace("REPO_URL_PLACEHOLDER", REPO_URL)
    out.write_text(text, encoding="utf-8")
    print("Escrito:", out, f"({len(CELLS)} celdas)")
