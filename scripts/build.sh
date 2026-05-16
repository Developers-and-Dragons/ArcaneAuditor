#!/usr/bin/env bash
echo "🧙 Arcane Auditor – macOS Build Script (pure uv mode)"
set -euo pipefail


uv python install 3.12.6
uv python pin 3.12.6
uv venv .venv

echo "📥 Installing runtime deps into uv env"
uv pip install -r requirements.txt

echo "🛠 Installing PyInstaller"
uv pip install pyinstaller pyinstaller-hooks-contrib

echo "🏗 Building Desktop"
uv run pyinstaller ArcaneAuditorDesktop.spec --clean --noconfirm

echo "🏗 Building CLI"
uv run pyinstaller ArcaneAuditorCLI.spec --clean --noconfirm

echo "✨ Build complete!"
ls -lh dist/ || echo "⚠️ dist/ folder missing!"

# Set execute permissions on CLI binary
if [ -f "dist/ArcaneAuditorCLI" ]; then
  echo "🔧 Setting execute permissions on CLI..."
  chmod +x dist/ArcaneAuditorCLI
  echo "✅ CLI binary is now executable"
else
  echo "⚠️ CLI binary not found (may not have been built)"
fi

echo ""
echo "📊 Final build artifacts:"
ls -lh dist/