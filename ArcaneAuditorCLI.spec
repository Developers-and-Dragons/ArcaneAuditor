# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
import sys, os
sys.path.append(os.path.abspath("."))

hidden_imports = (
    collect_submodules("parser.rules")
    + collect_submodules("typer")
    + collect_submodules("click")
    + collect_submodules("pydantic")
    + collect_submodules("lark") 
)


a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath(".")],
    binaries=[],
    datas=[
    ("config/rules/presets", "config/rules/presets"),
    ("parser/rules/script", "parser/rules/script"),
    ("parser/rules/structure", "parser/rules/structure"),
    ("parser/pmd_script_grammar.lark", "parser"),
    ("assets/icons", "assets"),  # Application icon
    ("pyproject.toml", "."),     # Version metadata for __version__
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")

# ---------------------------------------------------------------------------
# macOS build: onedir mode (signable)
# ---------------------------------------------------------------------------
if IS_MAC:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='ArcaneAuditorCLI',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        icon='assets/icons/aa-mac.icns',
        codesign_identity=os.environ.get('MAC_IDENTITY', None),
        entitlements_file='entitlements.plist',
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        name='ArcaneAuditorCLI',
    )

# ---------------------------------------------------------------------------
# Windows build: onefile mode
# ---------------------------------------------------------------------------
elif IS_WIN:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='ArcaneAuditorCLI',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        icon='assets/icons/aa-windows.ico',
    )

# ---------------------------------------------------------------------------
# Linux build: onefile mode (no icon)
# ---------------------------------------------------------------------------
elif IS_LINUX:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='ArcaneAuditorCLI',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
    )
else:
    raise SystemExit(f"Unsupported platform for CLI build: {sys.platform}")