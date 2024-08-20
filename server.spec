#! python
# -*- mode: python ; coding: utf-8 -*-
# SPDX-FileCopyrightText: 2023 Number6174
# SPDX-License-Identifier: CC0-1.0
import shutil

block_cipher = None

added_files = [
    ("config.json", "."),
    ("config.json.license", "."),
    ("control_panel.html", "."),
    ("favicon.ico", "."),
    ("favicon.ico.license", "."),
    ("examples/*", "examples"),
]

a = Analysis(
    ["server.py"],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="favicon.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="server",
)

# Pyinstaller 6.0 moves all files into internal locations, need to manually copy them to the right place now
shutil.copy("config.json", "dist/server")
shutil.copy("config.json.license", "dist/server")
shutil.copy("control_panel.html", "dist/server")
shutil.copytree("examples", "dist/server/examples")
