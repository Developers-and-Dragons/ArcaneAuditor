#!/usr/bin/env bash
set -euo pipefail

echo "🧙 Arcane Auditor – macOS Build Script (uv mode, pinned)"
echo "🕒 $(date '+%Y-%m-%d %H:%M:%S') Build started"
BUILD_LOG="build-logs/build_macos.log"
mkdir -p build-logs

{
    echo "=============================================================="
    echo "🔧 Environment Information"
    echo "=============================================================="
    echo "DATE: $(date)"
    echo "PWD: $(pwd)"
    echo "USER: $(whoami)"
    echo "PATH: $PATH"
    echo "--------------------------------------------------------------"

    echo "🧩 Checking uv installation..."
    uv --version

    echo "📦 Ensuring uv-managed Python is installed and pinned..."
    uv python install 3.12.6
    uv python pin 3.12.6
    echo "✅ uv Python pinned version:"
    cat .python-version || echo "(no .python-version found!)"

    echo "✅ uv Python detected: $(uv run python3 --version)"

    # Prevent PyInstaller from finding system framework Python
    export PATH="/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin"

    echo "🔍 Python executable:"
    uv run which python3
    echo "--------------------------------------------------------------"

    echo "📥 Installing runtime dependencies..."
    uv pip install -r requirements.txt

    echo "🛠 Installing PyInstaller..."
    uv pip install pyinstaller

    echo "=============================================================="
    echo "🏗️ Building Arcane Auditor Desktop"
    echo "=============================================================="
    uv run pyinstaller -v ArcaneAuditorDesktop.spec --clean --noconfirm

    echo "=============================================================="
    echo "🏗️ Building Arcane Auditor CLI"
    echo "=============================================================="
    uv run pyinstaller -v ArcaneAuditorCLI.spec --clean --noconfirm

    echo "=============================================================="
    echo "✨ Build complete!"
    echo "Output files:"
    ls -lh dist/
    echo "=============================================================="
} 2>&1 | tee "$BUILD_LOG"
