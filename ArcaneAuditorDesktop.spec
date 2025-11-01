# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
import sys, os
from pathlib import Path
sys.path.append(os.path.abspath("."))

# ---------------------------------------------------------------------------
# Hidden imports (modules PyInstaller must bundle explicitly)
# ---------------------------------------------------------------------------
hidden_imports = (
    collect_submodules("parser.rules")
    + collect_submodules("pydantic")
    + collect_submodules("lark")
    + collect_submodules("fastapi")
    + collect_submodules("starlette")
    + collect_submodules("uvicorn")
    + collect_submodules("webview")  # pywebview backend
    + ["requests"]
)

# ---------------------------------------------------------------------------
# Platform-aware data layout (critical for macOS code signing)
# ---------------------------------------------------------------------------
datas = [
        # --- Assets (logos/icons) ---
        ("assets/arcane-auditor-splash.webp", "assets"),
        ("assets/icons", "assets"),

        # --- Web service config ---
        ("config/web/web_service_config.json.sample", "config/web"),

        # --- Rule presets ---
        ("config/rules/presets", "config/rules/presets"),

        # --- Delivered rule directories ---
        ("parser/rules/script", "parser/rules/script"),
        ("parser/rules/structure", "parser/rules/structure"),

        # --- Frontend files (HTML, CSS, JS) ---
        ("web/frontend", "web/frontend"),

        # --- Grammar for PMD parsing ---
        ("parser/pmd_script_grammar.lark", "parser"),
    ]

# ---------------------------------------------------------------------------
# Analysis phase
# ---------------------------------------------------------------------------
a = Analysis(
    ['arcane_auditor_desktop.py'],  # Main desktop launcher
    pathex=[os.path.abspath(".")],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hooks/runtime-hook-macos-paths.py'] if sys.platform == 'darwin' else [],
    excludes=['matplotlib', 'PIL', 'numpy', 'pandas', 'scipy', 'wx'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# ---------------------------------------------------------------------------
# macOS build: onedir mode + .app bundle (signable)
# ---------------------------------------------------------------------------
if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='ArcaneAuditor',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        icon='assets/icons/aa-mac.icns',
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='ArcaneAuditor',
    )

    app = BUNDLE(
        coll,
        name='ArcaneAuditor.app',
        icon='assets/icons/aa-mac.icns',
        bundle_identifier='com.arcaneauditor.desktop',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.2.0',
            'CFBundleVersion': '1.2.0',
            'NSHumanReadableCopyright': 'Copyright © 2025',
        },
    )

# ---------------------------------------------------------------------------
# Windows build: onefile mode
# ---------------------------------------------------------------------------
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='ArcaneAuditor',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        icon='assets/icons/aa-windows.ico',
    )
