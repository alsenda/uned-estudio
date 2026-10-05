#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python) || { echo "Instala Python 3.12 desde https://www.python.org/downloads/"; exit 1; }
exec "$PY" iniciar.py "$@"
