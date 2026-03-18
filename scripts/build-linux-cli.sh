#!/usr/bin/env bash
echo "🧙 Arcane Auditor – Linux CLI Build (pure uv mode)"
set -euo pipefail

if [ "$(uname -s)" != "Linux" ]; then
  echo "❌ This script is for Linux only. Current OS: $(uname -s)"
  exit 1
fi

uv python install 3.12.6
uv python pin 3.12.6
uv venv .venv

echo "📥 Installing runtime deps into uv env"
uv pip install -r requirements.txt

echo "🛠 Installing PyInstaller"
uv pip install pyinstaller pyinstaller-hooks-contrib

echo "🏗 Building CLI only"
uv run pyinstaller ArcaneAuditorCLI.spec --clean --noconfirm

if [ -f "dist/ArcaneAuditorCLI" ]; then
  echo "🔧 Setting execute permissions on CLI..."
  chmod +x dist/ArcaneAuditorCLI
  echo "✅ CLI binary is now executable"
else
  echo "❌ CLI artifact missing: dist/ArcaneAuditorCLI"
  exit 1
fi

echo "✨ Linux CLI build complete!"
ls -lh dist/ArcaneAuditorCLI
