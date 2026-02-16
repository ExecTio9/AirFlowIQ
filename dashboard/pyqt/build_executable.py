"""
Build script for creating AirFlow IQ Analytics executable
This script uses PyInstaller to package the application
"""

import os
import subprocess
import sys


def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("✓ PyInstaller is already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "--break-system-packages"])
        print("✓ PyInstaller installed successfully")


def create_spec_file():
    """Create PyInstaller spec file"""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],  # Your main entry point
    pathex=[],
    binaries=[],
    datas=[
        ('ui/new_ui.ui', 'ui'),  # Include UI file
        ('assets/*', 'assets'),   # Include assets folder if it exists
        ('config.py', '.'),       # Include config file
    ],
    hiddenimports=[
        'supabase',
        'pandas',
        'matplotlib',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.uic',
        'matplotlib.backends.backend_qt5agg',
        'numpy',
    ],
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
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)
"""

    with open('AirFlowIQ.spec', 'w') as f:
        f.write(spec_content)

    print("✓ Created AirFlowIQ.spec file")


def build_executable():
    """Build the executable using PyInstaller"""
    print("\n" + "=" * 60)
    print("Building AirFlow IQ Analytics Executable")
    print("=" * 60 + "\n")

    # Install PyInstaller
    install_pyinstaller()

    # Create spec file
    create_spec_file()

    # Build using spec file
    print("\nBuilding executable...")
    print("This may take a few minutes...\n")

    try:
        subprocess.check_call(['pyinstaller', 'AirFlowIQ.spec', '--clean'])
        print("\n" + "=" * 60)
        print("✓ Build completed successfully!")
        print("=" * 60)
        print("\nYour executable is located at:")
        print("  → dist/AirFlowIQ (Linux/Mac)")
        print("  → dist/AirFlowIQ.exe (Windows)")
        print("\nYou can distribute the entire 'dist' folder or just the executable.")

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure all Python dependencies are installed")
        print("2. Check that config.py exists with SUPABASE_URL and SUPABASE_KEY")
        print("3. Ensure ui/new_ui.ui file exists")
        print("4. Try running with console=True in the spec file for debugging")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()