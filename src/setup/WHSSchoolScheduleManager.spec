# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('JetBrainsMono-Medium.ttf', '.')]
datas += collect_data_files('lucide')


a = Analysis(
    ['code.py'],
    pathex=[],
    binaries=[('C:/Program Files/GTK3-Runtime Win64/bin/*.dll', '.')],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tagflow', 'fastapi', 'hypercorn', 'trio', 'pydantic', 'rich', 'nuitka', 'pygame.mixer', 'pygame.mixer_music', 'pygame.controller', 'pygame.audio', 'pygame.midi'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WHSSchoolScheduleManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WHSSchoolScheduleManager',
)
