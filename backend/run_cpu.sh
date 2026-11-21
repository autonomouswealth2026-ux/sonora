#!/usr/bin/env bash
# Arranca el backend en modo SOLO CPU (InstaBox: 4 vCPU, 8 GB RAM).
# Solo Kokoro (narración, voces fijas) + Whisper small (STT ligero).
# Qwen3-TTS, Demucs y SFX devuelven 503 con el mensaje "arranca el
# backend GPU". Sin tocar la GPU: no se instala ni se importa torch CUDA.
# Uso:  ./run_cpu.sh
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv-cpu ]; then
  python3 -m venv .venv-cpu
fi
# shellcheck disable=SC1091
source .venv-cpu/bin/activate

# torch CPU primero: si no, pip instalaría el wheel con CUDA (~800 MB).
pip install -q torch --index-url https://download.pytorch.org/whl/cpu
pip install -q -r requirements-cpu.txt

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export CPU_ONLY=1
echo "== Backend SOLO CPU en http://0.0.0.0:${PORT:-8000} (solo Kokoro) =="
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
