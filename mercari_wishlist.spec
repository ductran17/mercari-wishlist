# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

# Collect all dependencies for playwright and patchright
playwright_datas, playwright_binaries, playwright_hiddenimports = collect_all('playwright')
patchright_datas, patchright_binaries, patchright_hiddenimports = collect_all('patchright')

# Collect browserforge data
browserforge_datas = collect_data_files('browserforge')

# Hidden imports for the app
hidden_imports = [
    'flask',
    'jinja2',
    'werkzeug',
    'click',
    'lxml',
    'cssselect',
    'orjson',
    'tld',
    'w3lib',
    'curl_cffi',
    'msgspec',
    'anyio',
    'scrapling',
    'scrapling.core',
    'scrapling.fetchers',
    'scrapling.engines',
    'scrapling.parser',
] + playwright_hiddenimports + patchright_hiddenimports

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=playwright_binaries + patchright_binaries,
    datas=[
        ('brand.json', '.'),
        ('templates', 'templates'),
        ('Scrapling/scrapling', 'scrapling'),
    ] + playwright_datas + patchright_datas + browserforge_datas,
    hiddenimports=hidden_imports,
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
    name='MercariWishlist',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to True to see errors, change to False for no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
