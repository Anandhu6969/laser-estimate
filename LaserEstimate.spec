# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


project = Path(SPECPATH).resolve()
datas = [
    (str(project / "assets" / "universallogo.png"), "assets"),
    (str(project / "app" / "ui" / "assets"), "app/ui/assets"),
]
datas += collect_data_files("reportlab")
hiddenimports = ["PySide6.QtSvg"]

a = Analysis(
    [str(project / "app" / "main.py")],
    pathex=[str(project)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pypdf", "tests", "reportlab.test", "reportlab.tests"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LaserEstimate",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=r"E:\laser_estimate\installer\LaserEstimate.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="LaserEstimate",
)
