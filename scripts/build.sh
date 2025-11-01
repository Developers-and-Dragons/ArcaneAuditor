#!/usr/bin/env bash
set -e

echo "🧙 Arcane Auditor – macOS Build Script (uv mode)"

# Ensure uv-managed Python exists
uv python install 3.12
echo "✅ uv Python ready: $(uv run python3 --version)"

# Preserve uv path but strip system frameworks
UV_BIN=$(dirname "$(command -v uv)")
export PATH="$UV_BIN:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin"

echo "🔍 Using uv from: $UV_BIN"
echo "🔍 PATH: $PATH"

# Install dependencies
uv pip install -r requirements.txt
uv pip install pyinstaller

echo "🏗 Building Desktop"
uv run pyinstaller ArcaneAuditorDesktop.spec --clean --noconfirm

echo "🏗 Building CLI"
uv run pyinstaller ArcaneAuditorCLI.spec --clean --noconfirm

echo "✨ macOS build complete!"
