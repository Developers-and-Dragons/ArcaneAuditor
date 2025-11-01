#!/usr/bin/env bash
set -e

echo "🧙 Arcane Auditor – macOS Build Script (uv mode)"

# Ensure uv python exists
if ! uv run python3 --version >/dev/null 2>&1; then
    echo "❌ uv-managed Python missing"
    exit 1
fi

echo "✅ uv Python detected: $(uv run python3 --version)"

# CRITICAL FIX: Remove /usr/local/bin and /Library/Frameworks from PATH
# This prevents PyInstaller from finding system Python.framework
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin"

echo "🔍 Environment:"
echo "  PATH: $PATH"
echo "  Python: $(uv run which python3)"

echo "📥 Installing runtime deps"
uv pip install -r requirements.txt

echo "🛠 Installing PyInstaller"
uv pip install pyinstaller

echo "🏗 Building Desktop"
uv run pyinstaller ArcaneAuditorDesktop.spec --clean

echo "🏗 Building CLI"
uv run pyinstaller ArcaneAuditorCLI.spec --clean

echo "✨ macOS build complete!"