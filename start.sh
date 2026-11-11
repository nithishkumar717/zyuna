#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║                  Zyuna - Auto-Update & Startup                   ║
# ╚══════════════════════════════════════════════════════════════════╝

set -e

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -n "${PYTHON:-}" ]]; then
    PYTHON_BIN="$PYTHON"
elif [[ -x "$SCRIPT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
else
    echo "✖ Python was not found on PATH."
    exit 1
fi

echo "◈ Starting Zyuna from $SCRIPT_DIR..."
exec "$PYTHON_BIN" "$SCRIPT_DIR/zyuna.py"
