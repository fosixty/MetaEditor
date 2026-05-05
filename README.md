<<<<<<< Updated upstream
# MetaEditor

A focused desktop app for **editing audio metadata** with a **dark, minimal UI**. Built with **Python**, **PyQt6**, and **mutagen**—one file, no database, no account.

**Supported formats:** MP3, FLAC, M4A (AAC), WAV.

---

## What it does

- **Tag editing:** title, artist, album, album artist, track number, year, genre (with quick suggestions), composer, comment, BPM, and musical key.
- **Cover art:** add or replace embedded artwork (JPEG/PNG). Very large cover images may skip preview in the UI but are still written on save.
- **Save options:** **Save** writes tags in place, or use **Save as copy…** to duplicate the file and apply your changes to the new path.
- **File loading:** drag-and-drop a track onto the window or use **Open…** from the empty state.
- **Track info:** status area shows file size, duration, bitrate, sample rate, and channel count when available.

**Shortcut:** `Ctrl+S` saves the current file (on macOS this is the **Control** key, not Command).

**WAV notes:** When a WAV has embedded cover art, the app may not render a thumbnail (preview skipped); you can still replace artwork and save.

---

## Run from source

**Requirements:** Python 3.10+ (3.12+ recommended).
=======
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
- **Shortcut:** standard **Save** shortcut (Ctrl+S on Windows/Linux, ⌘S on macOS).

> **WAV note:** When a WAV has embedded cover art, the app may not render a thumbnail (preview skipped); you can still replace artwork and save.

## Run from source

Requirements: Python 3.10+ (3.12+ recommended).
>>>>>>> Stashed changes

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

<<<<<<< Updated upstream
Dependencies: `PyQt6`, `mutagen`, `Pillow` (see `requirements.txt`).

---

## Build a standalone app (PyInstaller)

The repo includes `MetaEditor.spec` for [PyInstaller](https://pyinstaller.org/). After installing dev tools:

```bash
pip install pyinstaller
pyinstaller MetaEditor.spec
```

Outputs are under `dist/`. On macOS you get an app bundle; on Windows, a foldered executable layout. You can package the macOS app into a `.dmg` with your usual tooling (e.g. `create-dmg` or Disk Utility).

**Crash logs (packaged Windows builds):** startup failures are appended to  
`%LOCALAPPDATA%\MetaEditor\crash.log` when the app cannot start normally.

---
=======
Dependencies: PyQt6, PyQt6-Qt6, mutagen, Pillow (see `requirements.txt`).

PyQt6 is pinned to **6.5.x** so current macOS wheels stay compatible with **macOS 12 Monterey** (newer Qt builds may require macOS 13+).

## Build a standalone app (PyInstaller)

The repo includes `Quartz.spec` for PyInstaller. After installing dev tools:

```bash
pip install -r requirements-dev.txt   # adds PyInstaller
pyinstaller Quartz.spec
```

**macOS:** you can use the helper script (creates/uses `.venv` if needed):

```bash
chmod +x scripts/build-macos-app.sh   # once
./scripts/build-macos-app.sh
```

Outputs are under `dist/`. On macOS you get `Quartz.app`; on Windows, a foldered executable layout. You can package the macOS app into a `.dmg` with your usual tooling (e.g. `create-dmg` or Disk Utility).

> **Crash logs (packaged builds):** if the UI fails to start, details are appended to a log file: Windows `%LOCALAPPDATA%\GoldKit\Quartz\crash.log`, macOS `~/Library/Application Support/GoldKit/Quartz/crash.log`, or Linux under `XDG_STATE_HOME` / `~/.local/state` (see `main.py`).
>>>>>>> Stashed changes

## Repository layout

| Path | Role |
|------|------|
| `main.py` | Application (UI, tag read/write, format handling) |
<<<<<<< Updated upstream
| `MetaEditor.spec` | PyInstaller configuration |
| `requirements.txt` | Runtime dependencies |

---

## Open source & contributing

MetaEditor is **open source**: you may use it, change it, build on top of it, and share your work. The [MIT License](LICENSE) keeps those terms simple and permissive so others can extend the app, fix bugs, or adapt it for their own workflows.

Contributions are welcome. Open an issue to discuss an idea, or send a pull request with a clear description of what changed and why. Forks and experiments are encouraged.

---

## License

[MIT](LICENSE) — Copyright (c) 2026 Mitchell Gendron.

---

**MetaEditor** — quick metadata fixes without leaving the file you’re working on.
=======
| `Quartz.spec` | PyInstaller configuration |
| `scripts/build-macos-app.sh` | Optional macOS app build script |
| `requirements.txt` | Runtime dependencies |

## Open source & contributing

Quartz is open source: you may use it, change it, build on top of it, and share your work. The MIT License keeps those terms simple and permissive so others can extend the app, fix bugs, or adapt it for their own workflows.

Contributions are welcome. Open an issue to discuss an idea, or send a pull request with a clear description of what changed and why. Forks and experiments are encouraged.

## License

MIT — Copyright (c) 2026 Mitchell Gendron.

---

*Quartz — quick metadata fixes without leaving the file you're working on.*
>>>>>>> Stashed changes
