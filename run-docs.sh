#!/usr/bin/env bash
set -euo pipefail

VENV_DIR="$(dirname "$0")/.venv-docs"

# Create the venv once
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment at .venv-docs..."
  python3 -m venv "$VENV_DIR"
fi

# Install/upgrade inside the venv only
if ! "$VENV_DIR/bin/python" -m mkdocs --version &>/dev/null; then
  echo "Installing MkDocs into .venv-docs..."
  "$VENV_DIR/bin/pip" install mkdocs mkdocs-material --quiet
fi

echo "Starting docs server → http://127.0.0.1:8080"
"$VENV_DIR/bin/python" -m mkdocs serve --dev-addr 127.0.0.1:8080
