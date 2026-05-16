Write-Host "🧙 Arcane Auditor - Windows Build Script (pure uv mode)"

# Create uv environment
uv venv .venv

# Ensure uv Python exists (and pin)
uv python install 3.12.6
uv python pin 3.12.6

Write-Host "✅ uv Python detected"

Write-Host "📥 Installing runtime deps into uv env"
uv pip install -r requirements.txt

Write-Host "🛠 Installing PyInstaller"
uv pip install pyinstaller pyinstaller-hooks-contrib

Write-Host "🏗 Building Desktop"
uv run pyinstaller ArcaneAuditorDesktop.spec --clean --noconfirm

Write-Host "🏗 Building CLI"
uv run pyinstaller ArcaneAuditorCLI.spec --clean --noconfirm

Write-Host "✨ Build complete!"
Get-ChildItem dist
