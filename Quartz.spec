# -*- mode: python ; coding: utf-8 -*-
# macOS: produces dist/Quartz.app (onedir + bundle).
# UPX disabled — often problematic with macOS bundles / code signing.

from pathlib import Path

from PIL import Image


ROOT = Path(globals().get('SPECPATH', Path.cwd())).resolve()
ASSETS_DIR = ROOT / 'assets'
SOURCE_LOGO = ASSETS_DIR / 'Quartz_Logo.png'
WIN_ICON = ASSETS_DIR / 'Quartz_Logo.ico'
MAC_ICON = ASSETS_DIR / 'Quartz_Logo.icns'


def _ensure_platform_icons() -> None:
    if not SOURCE_LOGO.exists():
        return

    with Image.open(SOURCE_LOGO) as src:
        rgba = src.convert('RGBA')
        if not WIN_ICON.exists():
            rgba.save(WIN_ICON, format='ICO', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        if not MAC_ICON.exists():
            rgba.resize((1024, 1024), Image.Resampling.LANCZOS).save(MAC_ICON, format='ICNS')


_ensure_platform_icons()

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(str(SOURCE_LOGO), 'assets')] if SOURCE_LOGO.exists() else [],
    hiddenimports=['PIL.JpegImagePlugin', 'PIL.PngImagePlugin', 'PIL.GifImagePlugin', 'PIL.BmpImagePlugin', 'PIL.TiffImagePlugin', 'mutagen.id3', 'mutagen.flac', 'mutagen.mp3', 'mutagen.mp4', 'mutagen.wave'],
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
    [],
    exclude_binaries=True,
    name='Quartz',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(WIN_ICON) if WIN_ICON.exists() else None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Quartz',
)
app = BUNDLE(
    coll,
    name='Quartz.app',
    icon=str(MAC_ICON) if MAC_ICON.exists() else None,
    bundle_identifier='com.goldkit.quartz',
    version='1.0.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
    },
)
