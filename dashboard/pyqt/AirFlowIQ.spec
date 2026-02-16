# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all data files
datas = []

# ✅ FIXED: Add UI files with absolute path
ui_file = os.path.abspath('ui/new_ui.ui')
if os.path.exists(ui_file):
    datas.append((ui_file, 'ui'))
    print(f"✓ Including UI file: {ui_file}")
else:
    print(f"⚠️ WARNING: UI file not found at {ui_file}")

# Add all .ui files from ui directory
ui_dir = os.path.abspath('ui')
if os.path.exists(ui_dir):
    for file in os.listdir(ui_dir):
        if file.endswith('.ui'):
            full_path = os.path.join(ui_dir, file)
            datas.append((full_path, 'ui'))
            print(f"✓ Including: {full_path}")

# Add assets
assets_dir = os.path.abspath('assets')
if os.path.exists(assets_dir):
    datas.append((assets_dir, 'assets'))
    print(f"✓ Including assets directory: {assets_dir}")

print(f"\n📦 Total data files to include: {len(datas)}")
for data in datas:
    print(f"  - {data[0]} -> {data[1]}")

# Collect hidden imports
hiddenimports = [
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.uic',
    'pandas',
    'matplotlib',
    'matplotlib.backends.backend_qt5agg',
    'supabase',
    'gotrue',
    'postgrest',
    'realtime',
    'storage3',
]

# Add hidden imports for supabase sub-packages
hiddenimports += collect_submodules('supabase')
hiddenimports += collect_submodules('gotrue')
hiddenimports += collect_submodules('postgrest')

a = Analysis(
    ['main.py'],  # Your main entry point
    pathex=[os.path.abspath('.')],  # Add current directory to path
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AirFlowIQ',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep True for now to see any errors
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)