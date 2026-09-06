#!/bin/zsh
set -e
cd "${0:A:h}"
export PYBAMM_DISABLE_TELEMETRY=true
.venv/bin/python scripts/precompute_demo.py
.venv/bin/python scripts/validate_science.py
(cd frontend && npm run build)
echo 'Scientific demo and interface rebuilt.'
