# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


asset_datas = []
for icon_asset in ("assets/icon.ico", "assets/icon.png"):
    if Path(icon_asset).exists():
        asset_datas.append((icon_asset, "assets"))

exe_icon = "assets/icon.ico" if Path("assets/icon.ico").exists() else None


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=asset_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FuwaMoza",
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
    codesign_identity=None,
    entitlements_file=None,
    icon=exe_icon,
)
