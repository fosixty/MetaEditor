# -*- mode: python ; coding: utf-8 -*-
# macOS: produces dist/Quartz.app (onedir + bundle).
# UPX disabled — often problematic with macOS bundles / code signing.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
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
    icon=None,
    bundle_identifier='com.goldkit.quartz',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
    },
)
