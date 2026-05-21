# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

from PyInstaller.building.splash import Splash
from PyInstaller.utils.hooks import collect_data_files

try:
    project_dir = Path(__file__).resolve().parent
except NameError:
    project_dir = Path.cwd()

assets_dir = project_dir / "assets"

datas = collect_data_files("nicegui")
if assets_dir.exists():
    datas.append((str(assets_dir), "assets"))

icon_path = None
if sys.platform == "win32":
    icon_path = assets_dir / "mechsoc_32.ico"
elif sys.platform == "darwin":
    icon_path = assets_dir / "mechsoc_32.icns"

splash = None

if sys.platform.startswith("win") or sys.platform.startswith("linux"):
    splash_image = Path("assets/splash.png")
    if splash_image.exists():
        try:
            import tkinter  # noqa: F401
        except Exception:
            splash = None
        else:
            splash = Splash(str(splash_image), [], [])

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="mechsocemailtool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=str(icon_path) if icon_path and icon_path.exists() else None,
    splash=splash,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="mechsocemailtool.app",
        icon=str(icon_path) if icon_path and icon_path.exists() else None,
        bundle_identifier="uk.ac.bath.mechsoc.emailtool",
    )
