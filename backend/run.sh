#!/usr/bin/env bash
# Arranca el backend con GPU (Kaggle o PC con CUDA).
# Uso:  ./run.sh            (instala deps GPU y arranca en :8000)
#       PORT=9000 ./run.sh  (otro puerto)
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

pip install -q -r requirements-gpu.txt

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "== Backend GPU en http://0.0.0.0:${PORT:-8000} (CPU_ONLY=0) =="
exec uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"
