Write-Host "🧙 Arcane Auditor - Windows Build Script (pure uv mode)"

# Ensure uv python exists
try {
    uv run python --version | Out-Null
} catch {
    Write-Error "❌ uv Python not found. Run: uv python install 3.12"
    exit 1
}

Write-Host "✅ uv Python detected"

Write-Host "📥 Installing runtime deps into uv env"
uv pip install -r requirements.txt

Write-Host "🛠 Installing PyInstaller"
uv pip install pyinstaller

Write-Host "🏗 Building Desktop"
uv run pyinstaller ArcaneAuditorDesktop.spec --clean

Write-Host "🏗 Building CLI"
uv run pyinstaller ArcaneAuditorCLI.spec --clean

Write-Host "🏗 Building Web"
uv run pyinstaller ArcaneAuditorWeb.spec --clean

Write-Host "✨ Build complete!"
