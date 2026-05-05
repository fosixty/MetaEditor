# Quartz

Part of the [GoldKit](https://github.com/fosixty) open source music tools suite.

> Formerly released as **MetaEditor v0.9.0-beta.1**.

A focused desktop app for editing audio metadata with a dark, minimal UI. Built with Python, PyQt6, and mutagen — one file, no database, no account.

Supported formats: **MP3, FLAC, M4A (AAC), WAV.**

## What it does

- **Tag editing:** title, artist, album, album artist, track number, year, genre (with quick suggestions), composer, engineer(s), recorded at, BPM, musical key, and comment.
- **Cover art:** add or replace embedded artwork (JPEG/PNG). Very large cover images may skip preview in the UI but are still written on save.
- **Save options:** Save writes tags in place, or use Save as copy… to duplicate the file and apply your changes to the new path.
- **File loading:** drag-and-drop a track onto the window or use Open… from the empty state.
- **Track info:** status area shows file size, duration, bitrate, sample rate, and channel count when available.
- **Shortcut:** Ctrl+S saves the current file.

> **WAV note:** When a WAV has embedded cover art, the app may not render a thumbnail (preview skipped); you can still replace artwork and save.

## Run from source

Requirements: Python 3.10+ (3.12+ recommended).

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Dependencies: PyQt6, mutagen, Pillow (see `requirements.txt`).

## Build a standalone app (PyInstaller)

The repo includes `Quartz.spec` for PyInstaller. After installing dev tools:

```bash
pip install pyinstaller
pyinstaller Quartz.spec
```

Outputs are under `dist/`. On macOS you get an app bundle; on Windows, a foldered executable layout.

### macOS installer (.dmg)

Use the included script to produce a drag-to-install `.dmg` — no extra tools needed, just the macOS built-in `hdiutil`.

```bash
# Uses the existing dist/Quartz.app
bash scripts/build-macos-dmg.sh

# Or rebuild the app bundle first, then package it
bash scripts/build-macos-dmg.sh --rebuild
```

Output: `dist/Quartz-<version>.dmg`

The version is read from `Quartz.spec` → `CFBundleShortVersionString` in `info_plist`. Update it there before releasing.

> **Crash logs (packaged Windows builds):** startup failures are appended to `%LOCALAPPDATA%\GoldKit\Quartz\crash.log` when the app cannot start normally.

## Repository layout

| Path | Role |
|------|------|
| `main.py` | Application (UI, tag read/write, format handling) |
| `Quartz.spec` | PyInstaller configuration |
| `requirements.txt` | Runtime dependencies |

## Open source & contributing

Quartz is open source: you may use it, change it, build on top of it, and share your work. The MIT License keeps those terms simple and permissive so others can extend the app, fix bugs, or adapt it for their own workflows.

Contributions are welcome. Open an issue to discuss an idea, or send a pull request with a clear description of what changed and why. Forks and experiments are encouraged.

## License

MIT — Copyright (c) 2026 Mitchell Gendron.

---

*Quartz — quick metadata fixes without leaving the file you're working on.*
