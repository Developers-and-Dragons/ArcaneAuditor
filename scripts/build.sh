#!/usr/bin/env bash
set -e

echo "🧙 Arcane Auditor – macOS Build Script (uv mode)"

# Ensure uv python exists
if ! uv run python3 --version >/dev/null 2>&1; then
    echo "❌ uv-managed Python missing. Install with:"
    echo "   uv python install 3.12"
    exit 1
fi

echo "✅ uv Python detected"

echo "📥 Installing runtime deps"
uv pip install -r requirements.txt

echo "🛠 Installing PyInstaller"
uv pip install pyinstaller

echo "🏗 Building Desktop"
uv run pyinstaller ArcaneAuditorDesktop.spec --clean

echo "🏗 Building CLI"
uv run pyinstaller ArcaneAuditorCLI.spec --clean

# ✅ We are skipping a web executable on macOS (your call earlier)
echo "✨ macOS build complete!"
