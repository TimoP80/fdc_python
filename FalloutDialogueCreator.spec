# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Fallout Dialogue Creator 2.0
Build command: pyinstaller FalloutDialogueCreator.spec
"""

import os
import sys
import glob

# Get the absolute path to the directory containing main.py
# Use SPECPATH which is provided by PyInstaller
src_dir = os.path.abspath(SPECPATH)

# Collect data files - include all necessary directories
# The plugins directory is included as a data folder so plugins can be loaded at runtime
datas = [
    (os.path.join(src_dir, 'plugins'), 'plugins'),
    (os.path.join(src_dir, 'ui'), 'ui'),
    (os.path.join(src_dir, 'core'), 'core'),
    (os.path.join(src_dir, 'models'), 'models'),
    (os.path.join(src_dir, 'utils'), 'utils'),
    (os.path.join(src_dir, 'plans'), 'plans'),
]

# Collect hidden imports for PyQt6 and other dependencies
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect PyQt6 data files (Qt platform plugins, etc.)
pyqt6_datas = collect_data_files('PyQt6')

# Collect all PyQt6 submodules to ensure they're included
pyqt6_hiddenimports = collect_submodules('PyQt6')

# Additional hidden imports for the application
additional_hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtSvg',
    'PyQt6.QtXml',
    'logging',
    'importlib.metadata',
    'xml.etree.ElementTree',
    'json',
    'os',
    'sys',
    'pathlib',
    # Core modules
    'core.ssl_exporter',
    'core.msg_exporter',
    'core.script_compiler',
    'core.settings',
    'core.plugin_system',
    'core.ddf_importer',
    'core.msg_importer',
    'core.import_manager',
    'core.import_base',
    'models.dialogue',
    # Plugin modules - ensure these are included in the bundle
    'plugins.example_plugin',
    'plugins.export_plugin',
    'plugins.ssl_msg_export_plugin',
]

a = Analysis(
    ['main.py'],
    pathex=[src_dir],
    binaries=[],
    datas=datas + pyqt6_datas,
    hiddenimports=pyqt6_hiddenimports + additional_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
    ],
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
    name='FalloutDialogueCreator',
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
    icon=None,  # Add your icon path here if needed: icon='path/to/icon.ico'
)
