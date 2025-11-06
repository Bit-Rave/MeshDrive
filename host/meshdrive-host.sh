#!/bin/bash
# Script shell pour Linux/Mac pour faciliter l'utilisation du CLI MeshDrive Host

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

python3 "$PROJECT_ROOT/host/cli.py" "$@"

