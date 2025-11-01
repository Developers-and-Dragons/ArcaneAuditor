# 🧙 Arcane Auditor – Windows Build Script (uv mode, pinned)
# This script mirrors the macOS build.sh for consistent logging and determinism.

$ErrorActionPreference = "Stop"
$LogDir = "build-logs"
$LogFile = Join-Path $LogDir "build_Windows.log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Log {
    param([string]$msg)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $msg"
    Add-Content -Path $LogFile -Value "[$timestamp] $msg"
}

Log "=============================================================="
Log "🔧 Environment Information"
Log "=============================================================="
Log "DATE: $(Get-Date)"
Log "PWD: $(Get-Location)"
Log "USER: $env:USERNAME"
Log "PATH: $env:PATH"
Log "--------------------------------------------------------------"

try {
    Log "🧩 Checking uv installation..."
    uv --version | Tee-Object -FilePath $LogFile -Append

    Log "📦 Ensuring uv-managed Python is installed and pinned..."
    uv python install 3.12.6
    uv python pin 3.12.6
    if (Test-Path ".python-version") {
        Log "✅ Pinned Python version: $(Get-Content .python-version)"
    } else {
        Log "⚠️ No .python-version file found!"
    }

    $pythonVer = uv run python -V
    Log "✅ uv Python detected: $pythonVer"

    Log "📥 Installing runtime dependencies..."
    uv pip install -r requirements.txt | Tee-Object -FilePath $LogFile -Append

    Log "🛠 Installing PyInstaller..."
    uv pip install pyinstaller | Tee-Object -FilePath $LogFile -Append

    Log "=============================================================="
    Log "🏗️ Building Arcane Auditor Desktop"
    Log "=============================================================="
    uv run pyinstaller -v ArcaneAuditorDesktop.spec --clean --noconfirm | Tee-Object -FilePath $LogFile -Append

    Log "=============================================================="
    Log "🏗️ Building Arcane Auditor CLI"
    Log "=============================================================="
    uv run pyinstaller -v ArcaneAuditorCLI.spec --clean --noconfirm | Tee-Object -FilePath $LogFile -Append

    Log "=============================================================="
    Log "✨ Build complete!"
    Log "Output files:"
    Get-ChildItem -Path dist | ForEach-Object { Log $_.FullName }
    Log "=============================================================="
}
catch {
    Log "❌ Build failed: $_"
    Exit 1
}
