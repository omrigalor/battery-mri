#!/bin/zsh
set -e
cd "${0:A:h}"
export PYBAMM_DISABLE_TELEMETRY=true
if [[ ! -x .venv/bin/python ]]; then
  echo 'Preparing Battery MRI dependencies (first launch only)…'
  python3 -m venv .venv
fi
if ! .venv/bin/python -c 'import pybamm, fastapi, uvicorn, scipy' >/dev/null 2>&1; then
  .venv/bin/python -m pip install -r requirements.txt
fi
if [[ ! -f frontend/dist/index.html ]]; then
  echo 'Building the local interface…'
  (cd frontend && npm ci && npm run build)
fi
if ! .venv/bin/python -c 'from pathlib import Path; from backend.science.cache import read_cache; read_cache(Path("backend/data/demo.json"))' >/dev/null 2>&1; then
  echo 'Computing the scientific demo (first launch only)…'
  .venv/bin/python scripts/precompute_demo.py
fi
echo 'Opening Battery MRI. Keep this window open; Control-C stops the app.'
exec .venv/bin/python scripts/launch.py
