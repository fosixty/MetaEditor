#!/usr/bin/env python3
"""
MetaEditor — Dark, precision-styled audio metadata editor (desktop).
Formats: MP3, FLAC, M4A, WAV (mutagen + PyQt6).
"""

from __future__ import annotations

import faulthandler
import io
import os
import sys
import traceback
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Optional

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QImage, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from PIL import Image

from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3

try:
    EasyID3.RegisterKey("key", "TKEY")
except Exception:
    pass
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, COMM, ID3, TALB, TBPM, TCOM, TCON, TDRC, TIT2, TKEY, TPE1, TPE2, TRCK, USLT
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover, MP4FreeForm
from mutagen.wave import WAVE


def _get_error_log_path() -> str:
    root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    log_dir = os.path.join(root, "MetaEditor")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "crash.log")


def _log_startup_exception(ex: BaseException) -> str:
    path = _get_error_log_path()
    tb = traceback.format_exc()
    with open(path, "a", encoding="utf-8") as f:
        f.write("=" * 72 + "\n")
        f.write("MetaEditor startup failure\n")
        f.write(tb)
        if not tb.endswith("\n"):
            f.write("\n")
        f.write(f"Error: {ex}\n")
    return path


# --- Theme --------------------------------------------------------------------

BG = "#0d0d0f"
SURFACE = "#16181c"
SURFACE_ELEVATED = "#1c1f24"
ACCENT = "#00b4d8"
ACCENT_DIM = "#0096b8"
TEXT = "#f2f4f8"
TEXT_MUTED = "#8b909a"
BORDER = "#2a2f38"
BORDER_FOCUS = ACCENT
FONT_FAMILY = "Segoe UI Variable"
FONT_FALLBACK = "Segoe UI"


# Skip decoding huge embedded covers (can stress Qt/PIL on malformed data)
MAX_COVER_DISPLAY_BYTES = 8 * 1024 * 1024
# Downscale before building QImage (avoids huge allocations / driver issues)
MAX_COVER_DECODE_EDGE = 2048

COMMON_GENRES = [
    "Blues", "Classic Rock", "Country", "Dance", "Electronic", "Folk",
    "Funk", "Hip-Hop", "House", "Indie", "Jazz", "Latin", "Metal",
    "Pop", "Punk", "R&B", "Reggae", "Rock", "Soul", "Techno", "Trance",
    "Trap", "Drum & Bass", "Dubstep", "Ambient", "Soundtrack", "Other",
]


def app_stylesheet() -> str:
    return f"""
    QMainWindow {{ background-color: {BG}; }}
    QWidget#central {{ background-color: {BG}; }}
    QLabel {{ color: {TEXT}; font-size: 13px; }}
    QLabel[class="muted"] {{ color: {TEXT_MUTED}; font-size: 11px; }}
    QLabel[class="fieldLabel"] {{
        color: {TEXT_MUTED};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }}
    QLineEdit, QComboBox {{
        background-color: {SURFACE_ELEVATED};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px 10px;
        font-size: 13px;
        min-height: 18px;
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {BORDER_FOCUS};
        background-color: #22262c;
    }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox QAbstractItemView {{
        background-color: {SURFACE};
        color: {TEXT};
        selection-background-color: {ACCENT_DIM};
        border: 1px solid {BORDER};
    }}
    QPushButton {{
        background-color: {SURFACE_ELEVATED};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 10px 18px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
    QPushButton#primary {{
        background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 #0096c7, stop:1 {ACCENT});
        color: #0d0d0f;
        border: none;
    }}
    QPushButton#primary:hover {{
        background-color: #33c4e0;
    }}
    QPushButton#ghost {{
        background: transparent;
        border: 1px dashed {BORDER};
        color: {TEXT_MUTED};
    }}
    QScrollArea {{ border: none; background: transparent; }}
    QStatusBar {{
        background-color: #0a0a0c;
        color: {TEXT_MUTED};
        border-top: 1px solid {BORDER};
        font-size: 11px;
        padding: 4px;
    }}
    """


class AudioKind(Enum):
    MP3 = auto()
    FLAC = auto()
    M4A = auto()
    WAV = auto()


def _s(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, list):
        if not val:
            return ""
        x = val[0]
        return _s(x)
    if isinstance(val, tuple):
        return _s(list(val))
    return str(val)


def _frame_text(frame: Any) -> str:
    """Safely read the first string from an ID3 text frame (avoids IndexError on empty text)."""
    if frame is None:
        return ""
    raw = getattr(frame, "text", None)
    if raw is None:
        return ""
    if isinstance(raw, list):
        if not raw:
            return ""
        return str(raw[0]) if raw[0] is not None else ""
    return str(raw)


def _comm_first(comm: Any) -> str:
    if comm is None:
        return ""
    raw = getattr(comm, "text", None)
    if raw is None:
        return ""
    if isinstance(raw, list) and raw:
        entry = raw[0]
        return str(entry) if entry is not None else ""
    return str(raw)


@dataclass
class TagBundle:
    title: str = ""
    artist: str = ""
    album: str = ""
    albumartist: str = ""
    track: str = ""
    year: str = ""
    genre: str = ""
    composer: str = ""
    comment: str = ""
    bpm: str = ""
    key: str = ""
    cover_data: Optional[bytes] = None
    cover_mime: str = "image/jpeg"
    _cover_replaced: bool = False


@dataclass
class LoadedAudio:
    path: str
    kind: AudioKind
    audio: Any
    tags: TagBundle = field(default_factory=TagBundle)


def _read_id3_common(audio: ID3) -> TagBundle:
    t = TagBundle()
    try:

        def comm_text() -> str:
            for f in audio.values():
                if isinstance(f, COMM):
                    return _comm_first(f)
            return ""

        def lyrics_or_comment() -> str:
            c = comm_text()
            if c:
                return c
            for f in audio.values():
                if isinstance(f, USLT):
                    ut = getattr(f, "text", None)
                    if isinstance(ut, list) and ut:
                        return str(ut[0])
                    if isinstance(ut, str):
                        return ut
                    return str(ut) if ut is not None else ""
            return ""

        fr = audio.get
        if fr("TIT2"):
            t.title = _frame_text(fr("TIT2"))
        if fr("TPE1"):
            t.artist = _frame_text(fr("TPE1"))
        if fr("TALB"):
            t.album = _frame_text(fr("TALB"))
        if fr("TPE2"):
            t.albumartist = _frame_text(fr("TPE2"))
        if fr("TRCK"):
            t.track = _frame_text(fr("TRCK"))
        if fr("TDRC"):
            y = _frame_text(fr("TDRC"))
            t.year = y[:4] if y else ""
        elif fr("TYER"):
            t.year = _frame_text(fr("TYER"))
        if fr("TCON"):
            t.genre = _frame_text(fr("TCON"))
        if fr("TCOM"):
            t.composer = _frame_text(fr("TCOM"))
        t.comment = lyrics_or_comment()
        if fr("TBPM"):
            t.bpm = _frame_text(fr("TBPM"))
        if fr("TKEY"):
            t.key = _frame_text(fr("TKEY"))
    except Exception:
        return TagBundle()
    return t


def _apic_read(audio: ID3) -> tuple[Optional[bytes], str]:
    try:
        for _k, v in audio.items():
            try:
                if str(_k).startswith("APIC") or isinstance(v, APIC):
                    if not hasattr(v, "data") or not v.data:
                        continue
                    mime = getattr(v, "mime", None) or "image/jpeg"
                    return v.data, mime
            except Exception:
                continue
    except Exception:
        pass
    return None, "image/jpeg"


def _read_mp3(path: str, audio: MP3) -> TagBundle:
    if audio.tags is None:
        return TagBundle()
    try:
        e = EasyID3(path)
    except Exception:
        t = _read_id3_common(audio.tags)
        data, mime = _apic_read(audio.tags)
        t.cover_data, t.cover_mime = data, mime
        return t

    def gv(key: str) -> str:
        if key not in e:
            return ""
        return _s(e[key])

    t = TagBundle()
    t.title = gv("title")
    t.artist = gv("artist")
    t.album = gv("album")
    t.albumartist = gv("albumartist")
    t.track = gv("tracknumber")
    y = gv("date")
    t.year = y[:4] if y else ""
    t.genre = gv("genre")
    t.composer = gv("composer")
    t.comment = gv("comment")
    t.bpm = gv("bpm")
    t.key = gv("key")
    if not t.comment:
        t.comment = _read_id3_common(audio.tags).comment
    data, mime = _apic_read(audio.tags)
    t.cover_data, t.cover_mime = data, mime
    return t


def _read_flac(audio: FLAC) -> TagBundle:
    t = TagBundle()
    vc = audio
    t.title = _s(vc.get("title"))
    t.artist = _s(vc.get("artist"))
    t.album = _s(vc.get("album"))
    t.albumartist = _s(vc.get("albumartist") or vc.get("album artist"))
    t.track = _s(vc.get("tracknumber") or vc.get("track"))
    t.year = (_s(vc.get("date")) or _s(vc.get("year")))[:4]
    t.genre = _s(vc.get("genre"))
    t.composer = _s(vc.get("composer"))
    t.comment = _s(vc.get("comment") or vc.get("description"))
    t.bpm = _s(vc.get("bpm") or vc.get("tbpm"))
    t.key = _s(vc.get("initialkey") or vc.get("key"))
    if audio.pictures:
        pic = audio.pictures[0]
        t.cover_data = pic.data
        t.cover_mime = pic.mime or "image/jpeg"
    return t


def _read_m4a(audio: MP4) -> TagBundle:
    t = TagBundle()
    g = lambda k: _s(audio.tags.get(k)) if audio.tags else ""

    t.title = g("\xa9nam")
    t.artist = g("\xa9ART")
    t.album = g("\xa9alb")
    t.albumartist = g("aART")
    tr = audio.tags.get("trkn") if audio.tags else None
    if tr and len(tr) > 0:
        x = tr[0]
        if isinstance(x, tuple) and len(x) > 0:
            t.track = str(x[0])
        else:
            t.track = str(x)
    t.year = (g("\xa9day") or "")[:4]
    t.genre = g("\xa9gen")
    t.composer = g("\xa9wrt")
    t.comment = g("\xa9cmt")
    tmpo = audio.tags.get("tmpo") if audio.tags else None
    if tmpo:
        t.bpm = str(tmpo[0])
    ik = "----:com.apple.iTunes:Initial Key"
    if audio.tags and ik in audio.tags:
        raw = audio.tags[ik][0]
        if isinstance(raw, MP4FreeForm):
            t.key = raw.decode()
        else:
            t.key = str(raw)
    cov = audio.tags.get("covr") if audio.tags else None
    if cov:
        c0 = cov[0]
        if isinstance(c0, MP4Cover):
            t.cover_data = bytes(c0)
            t.cover_mime = "image/jpeg" if c0.imageformat == MP4Cover.FORMAT_JPEG else "image/png"
        elif isinstance(c0, (bytes, bytearray, memoryview)):
            t.cover_data = bytes(c0)
            t.cover_mime = "image/jpeg"
    return t


def _read_wav(audio: WAVE) -> TagBundle:
    try:
        if audio.tags is None:
            return TagBundle()
        base = _read_id3_common(audio.tags)
        data, mime = _apic_read(audio.tags)
        base.cover_data = data
        base.cover_mime = mime
        return base
    except Exception:
        return TagBundle()


def _open_audio_file(path: str) -> Any:
    """Open with mutagen. WAV files use explicit WAVE() for predictable behavior."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".wav", ".wave"):
        try:
            return WAVE(path)
        except Exception as e:
            raise ValueError(f"Could not read WAV file: {e}") from e
    audio = MutagenFile(path)
    if audio is None:
        raise ValueError("Could not open audio file.")
    return audio


def load_audio(path: str) -> LoadedAudio:
    audio = _open_audio_file(path)

    if isinstance(audio, MP3):
        tags = _read_mp3(path, audio)
        return LoadedAudio(path, AudioKind.MP3, audio, tags)
    if isinstance(audio, FLAC):
        tags = _read_flac(audio)
        return LoadedAudio(path, AudioKind.FLAC, audio, tags)
    if isinstance(audio, MP4):
        tags = _read_m4a(audio)
        return LoadedAudio(path, AudioKind.M4A, audio, tags)
    if isinstance(audio, WAVE):
        tags = _read_wav(audio)
        return LoadedAudio(path, AudioKind.WAV, audio, tags)

    raise ValueError(f"Unsupported format ({type(audio).__name__}). Use MP3, FLAC, M4A, or WAV.")


def _write_id3_frame(audio: ID3, tid: str, frame_cls, text: str) -> None:
    if not text.strip():
        if tid in audio:
            del audio[tid]
        return
    audio[tid] = frame_cls(encoding=3, text=text)


def _save_mp3(loaded: LoadedAudio, tb: TagBundle) -> None:
    path = loaded.path
    audio = loaded.audio
    if not isinstance(audio, MP3):
        raise RuntimeError("Internal error: expected MP3")

    if audio.tags is None:
        audio.add_tags()
        audio.save()

    e = EasyID3(path)

    def set_e(key: str, val: str) -> None:
        if not val.strip():
            if key in e:
                del e[key]
            return
        e[key] = val

    set_e("title", tb.title)
    set_e("artist", tb.artist)
    set_e("album", tb.album)
    set_e("albumartist", tb.albumartist)
    set_e("tracknumber", tb.track)
    set_e("date", tb.year)
    set_e("genre", tb.genre)
    set_e("composer", tb.composer)
    set_e("comment", tb.comment)
    set_e("bpm", tb.bpm)
    set_e("key", tb.key)
    e.save()

    audio = MP3(path)
    loaded.audio = audio
    tags = audio.tags
    if tags is None:
        audio.add_tags()
        audio.save()
        audio = MP3(path)
        tags = audio.tags

    for k in list(tags.keys()):
        if k.startswith("APIC"):
            del tags[k]
    if tb.cover_data:
        mime = tb.cover_mime or "image/jpeg"
        tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=tb.cover_data))

    audio.save()


def _save_flac(loaded: LoadedAudio, tb: TagBundle) -> None:
    audio = loaded.audio
    assert isinstance(audio, FLAC)

    def sv(k: str, v: str) -> None:
        if not v.strip():
            if k in audio:
                del audio[k]
            return
        audio[k] = v

    sv("title", tb.title)
    sv("artist", tb.artist)
    sv("album", tb.album)
    sv("albumartist", tb.albumartist)
    sv("tracknumber", tb.track)
    sv("date", tb.year)
    sv("genre", tb.genre)
    sv("composer", tb.composer)
    sv("comment", tb.comment)
    sv("bpm", tb.bpm)
    sv("initialkey", tb.key)

    if tb._cover_replaced:
        audio.clear_pictures()
        if tb.cover_data:
            pic = Picture()
            pic.type = 3
            pic.mime = tb.cover_mime or "image/jpeg"
            pic.desc = "Cover"
            pic.data = tb.cover_data
            audio.add_picture(pic)

    audio.save()


def _save_m4a(loaded: LoadedAudio, tb: TagBundle) -> None:
    audio = loaded.audio
    assert isinstance(audio, MP4)
    if audio.tags is None:
        audio.add_tags()

    def del_if_empty(k: str, val: str) -> None:
        if not val.strip():
            if k in audio.tags:
                del audio.tags[k]

    def set_s(k: str, val: str) -> None:
        if not val.strip():
            del_if_empty(k, val)
            return
        audio.tags[k] = [val]

    set_s("\xa9nam", tb.title)
    set_s("\xa9ART", tb.artist)
    set_s("\xa9alb", tb.album)
    set_s("aART", tb.albumartist)

    if tb.track.strip():
        try:
            tn = int(tb.track.split("/")[0])
            audio.tags["trkn"] = [(tn, 0)]
        except ValueError:
            pass
    elif "trkn" in audio.tags:
        del audio.tags["trkn"]

    set_s("\xa9day", tb.year)
    set_s("\xa9gen", tb.genre)
    set_s("\xa9wrt", tb.composer)
    set_s("\xa9cmt", tb.comment)

    if tb.bpm.strip():
        try:
            audio.tags["tmpo"] = [int(float(tb.bpm))]
        except ValueError:
            pass
    elif "tmpo" in audio.tags:
        del audio.tags["tmpo"]

    ik = "----:com.apple.iTunes:Initial Key"
    if tb.key.strip():
        audio.tags[ik] = [MP4FreeForm(tb.key.encode("utf-8"))]
    elif ik in audio.tags:
        del audio.tags[ik]

    if tb._cover_replaced:
        if "covr" in audio.tags:
            del audio.tags["covr"]
        if tb.cover_data:
            fmt = MP4Cover.FORMAT_JPEG if "jpeg" in (tb.cover_mime or "").lower() else MP4Cover.FORMAT_PNG
            audio.tags["covr"] = [MP4Cover(tb.cover_data, fmt)]

    audio.save()


def _save_wav(loaded: LoadedAudio, tb: TagBundle) -> None:
    audio = loaded.audio
    assert isinstance(audio, WAVE)
    if audio.tags is None:
        audio.add_tags()

    tags = audio.tags
    assert tags is not None

    _write_id3_frame(tags, "TIT2", TIT2, tb.title)
    _write_id3_frame(tags, "TPE1", TPE1, tb.artist)
    _write_id3_frame(tags, "TALB", TALB, tb.album)
    _write_id3_frame(tags, "TPE2", TPE2, tb.albumartist)
    _write_id3_frame(tags, "TRCK", TRCK, tb.track)
    _write_id3_frame(tags, "TDRC", TDRC, tb.year)
    _write_id3_frame(tags, "TCON", TCON, tb.genre)
    _write_id3_frame(tags, "TCOM", TCOM, tb.composer)
    if tb.comment.strip():
        for k, f in list(tags.items()):
            if isinstance(f, COMM):
                del tags[k]
        tags.add(COMM(encoding=3, lang="eng", desc="", text=tb.comment))
    elif not tb.comment.strip():
        for k, f in list(tags.items()):
            if isinstance(f, COMM):
                del tags[k]
    _write_id3_frame(tags, "TBPM", TBPM, tb.bpm)
    _write_id3_frame(tags, "TKEY", TKEY, tb.key)

    for k in list(tags.keys()):
        if k.startswith("APIC"):
            del tags[k]
    if tb.cover_data:
        mime = tb.cover_mime or "image/jpeg"
        tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=tb.cover_data))

    audio.save()


def save_tags(loaded: LoadedAudio, tb: TagBundle) -> None:
    if loaded.kind == AudioKind.MP3:
        _save_mp3(loaded, tb)
    elif loaded.kind == AudioKind.FLAC:
        _save_flac(loaded, tb)
    elif loaded.kind == AudioKind.M4A:
        _save_m4a(loaded, tb)
    elif loaded.kind == AudioKind.WAV:
        _save_wav(loaded, tb)
    else:
        raise RuntimeError("Unknown audio kind")


def build_info_strip(loaded: LoadedAudio, path: str) -> str:
    try:
        size_b = os.path.getsize(path)
        size_mb = size_b / (1024 * 1024)
        a = loaded.audio
        parts = [f"{size_mb:.2f} MB"]

        info = getattr(a, "info", None)
        if info is not None:
            ln = getattr(info, "length", None)
            if ln is not None:
                try:
                    sec = float(ln)
                    if sec >= 0:
                        m, s = int(sec // 60), int(sec % 60)
                        parts.append(f"{m}:{s:02d}")
                except (TypeError, ValueError, OverflowError):
                    pass
            br = getattr(info, "bitrate", None)
            if br is not None:
                try:
                    parts.append(f"{int(br // 1000)} kbps")
                except (TypeError, ValueError, OverflowError):
                    pass
            sr = getattr(info, "sample_rate", None)
            if sr is not None:
                try:
                    parts.append(f"{int(sr)} Hz")
                except (TypeError, ValueError, OverflowError):
                    pass
            ch = getattr(info, "channels", None)
            if ch:
                try:
                    parts.append(f"{int(ch)} ch")
                except (TypeError, ValueError, OverflowError):
                    pass

        return "  ·  ".join(parts)
    except Exception:
        return "—"


def _pil_bytes_to_preview_pixmap(data: bytes, display_size: int = 224) -> Optional[QPixmap]:
    """Decode cover art with PIL only; build QPixmap via QImage.copy() (avoids Qt PNG/JPEG decoders)."""
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
        im = im.convert("RGBA")
        if im.width > MAX_COVER_DECODE_EDGE or im.height > MAX_COVER_DECODE_EDGE:
            im.thumbnail(
                (MAX_COVER_DECODE_EDGE, MAX_COVER_DECODE_EDGE),
                Image.Resampling.LANCZOS,
            )
        w, h = im.size
        if w < 1 or h < 1:
            return None
        raw = im.tobytes("raw", "RGBA")
        stride = w * 4
        qimg = QImage(raw, w, h, stride, QImage.Format.Format_RGBA8888)
        qimg = qimg.copy()
        pm = QPixmap.fromImage(qimg)
        return pm.scaled(
            display_size,
            display_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    except Exception:
        return None


# --- Custom widgets -----------------------------------------------------------

class DropZone(QFrame):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(280)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover = False
        self.on_file: Optional[Callable[[str], None]] = None
        self.on_click: Optional[Callable[[], None]] = None
        self._apply_style()

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon = QLabel("♪")
        icon.setStyleSheet(f"font-size: 48px; color: {TEXT_MUTED}; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t = QLabel("Drop your track here")
        t.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {TEXT}; letter-spacing: 0.5px;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub = QLabel("or click to browse  ·  MP3  FLAC  M4A  WAV")
        sub.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(icon)
        lay.addSpacing(8)
        lay.addWidget(t)
        lay.addWidget(sub)

    def _apply_style(self) -> None:
        b = ACCENT if self._hover else BORDER
        self.setStyleSheet(
            f"""
            QFrame#dropZone {{
                background-color: {SURFACE};
                border: 2px dashed {b};
                border-radius: 14px;
                min-height: 280px;
            }}
            """
        )

    def dragEnterEvent(self, e: Any) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self._hover = True
            self._apply_style()
        else:
            e.ignore()

    def dragLeaveEvent(self, e: Any) -> None:
        self._hover = False
        self._apply_style()

    def dropEvent(self, e: Any) -> None:
        self._hover = False
        self._apply_style()
        path = ""
        if e.mimeData().hasUrls():
            path = e.mimeData().urls()[0].toLocalFile()
        e.acceptProposedAction()
        if path and self.on_file:
            self.on_file(path)

    def mousePressEvent(self, e: Any) -> None:
        if e.button() == Qt.MouseButton.LeftButton and self.on_click:
            self.on_click()
        super().mousePressEvent(e)


class ArtworkFrame(QFrame):
    clicked = None

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("artFrame")
        self.setFixedSize(240, 240)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"""
            QFrame#artFrame {{
                background: transparent;
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            """
        )
        self._pixmap: Optional[QPixmap] = None

        self._lbl = QLabel(self)
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl.setGeometry(8, 8, 224, 224)
        self._lbl.setStyleSheet(
            f"background-color: {SURFACE_ELEVATED}; border-radius: 12px; color: {TEXT_MUTED}; font-size: 11px;"
        )
        self._lbl.setText("No artwork")

    def set_artwork(self, data: Optional[bytes], *, wav_embedded: bool = False) -> None:
        if wav_embedded:
            self._pixmap = None
            self._lbl.setPixmap(QPixmap())
            self._lbl.setText("Embedded cover (WAV)\npreview skipped · click to replace")
            return
        if not data:
            self._pixmap = None
            self._lbl.setPixmap(QPixmap())
            self._lbl.setText("No artwork\n(click to add)")
            return
        if len(data) > MAX_COVER_DISPLAY_BYTES:
            self._pixmap = None
            self._lbl.setPixmap(QPixmap())
            self._lbl.setText("Artwork too large to preview\n(still saved with file)")
            return
        pm = _pil_bytes_to_preview_pixmap(data)
        if pm is None:
            self._pixmap = None
            self._lbl.setPixmap(QPixmap())
            self._lbl.setText("Invalid or unsupported image")
            return
        self._pixmap = pm
        self._lbl.setPixmap(self._pixmap)
        self._lbl.setText("")

    def mousePressEvent(self, e: Any) -> None:
        if e.button() == Qt.MouseButton.LeftButton and callable(self.clicked):
            self.clicked()
        super().mousePressEvent(e)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MetaEditor")
        self.setMinimumSize(920, 640)
        self.resize(980, 700)

        self._loaded: Optional[LoadedAudio] = None

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(0)

        self._stack_empty = QWidget()
        empty_l = QVBoxLayout(self._stack_empty)
        self._drop = DropZone(self._stack_empty)
        self._drop.on_file = self.file_dropped
        self._drop.on_click = self.browse_file
        empty_l.addStretch(1)
        empty_l.addWidget(self._drop, alignment=Qt.AlignmentFlag.AlignCenter)
        empty_l.addStretch(1)

        self._content = QWidget()
        self._content.setObjectName("editorCard")
        self._content.setVisible(False)
        self._content.setStyleSheet(
            f"""
            QWidget#editorCard {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            """
        )

        cl = QHBoxLayout(self._content)
        cl.setContentsMargins(22, 22, 22, 22)
        cl.setSpacing(28)

        left = QVBoxLayout()
        left.setSpacing(10)
        self._art = ArtworkFrame()
        self._art.clicked = self.replace_artwork
        left.addWidget(self._art, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._info_strip = QLabel("")
        self._info_strip.setProperty("class", "muted")
        self._info_strip.setWordWrap(True)
        self._info_strip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left.addWidget(self._info_strip)

        form_wrap = QScrollArea()
        form_wrap.setWidgetResizable(True)
        form_wrap.setFrameShape(QFrame.Shape.NoFrame)
        form_wrap.setStyleSheet("background: transparent;")
        form_wrap.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        form_wrap.viewport().setStyleSheet("background: transparent;")
        form_inner = QWidget()
        form_inner.setStyleSheet("background: transparent;")
        form = QGridLayout(form_inner)
        form.setColumnStretch(1, 1)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self._fields: dict[str, QLineEdit | QComboBox] = {}
        row = 0

        def add_row(label: str, key: str, combo: bool = False) -> None:
            nonlocal row
            lb = QLabel(label)
            lb.setProperty("class", "fieldLabel")
            if combo:
                w: QLineEdit | QComboBox = QComboBox()
                w.setEditable(True)
                w.addItems([""] + COMMON_GENRES)
                w.setCurrentText("")
            else:
                w = QLineEdit()
                w.setPlaceholderText("")
            form.addWidget(lb, row, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            form.addWidget(w, row, 1)
            self._fields[key] = w
            row += 1

        add_row("Title", "title")
        add_row("Artist", "artist")
        add_row("Album", "album")
        add_row("Album Artist", "albumartist")
        add_row("Track #", "track")
        add_row("Year", "year")
        add_row("Genre", "genre", combo=True)
        add_row("Composer", "composer")
        add_row("Comment", "comment")
        add_row("BPM", "bpm")
        add_row("Key", "key")

        form_wrap.setWidget(form_inner)
        cl.addLayout(left, 0)
        cl.addWidget(form_wrap, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        self._btn_browse = QPushButton("Open…")
        self._btn_browse.setObjectName("ghost")
        self._btn_browse.clicked.connect(self.browse_file)
        self._btn_save_copy = QPushButton("Save as copy…")
        self._btn_save_copy.clicked.connect(self.save_copy)
        self._btn_save = QPushButton("Save")
        self._btn_save.setObjectName("primary")
        self._btn_save.clicked.connect(self.save_in_place)
        btn_row.addWidget(self._btn_browse)
        btn_row.addStretch(1)
        btn_row.addWidget(self._btn_save_copy)
        btn_row.addWidget(self._btn_save)

        root.addWidget(self._stack_empty, 1)
        root.addWidget(self._content, 1)
        root.addLayout(btn_row)

        sb = QStatusBar()
        self.setStatusBar(sb)
        self.statusBar().showMessage("Ready — drop a file or click the zone to browse")

        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_in_place)

        self.setStyleSheet(app_stylesheet())

        self.setAcceptDrops(True)

    def dragEnterEvent(self, e: Any) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e: Any) -> None:
        path = ""
        if e.mimeData().hasUrls():
            path = e.mimeData().urls()[0].toLocalFile()
        e.acceptProposedAction()
        if path:
            self.file_dropped(path)

    def file_dropped(self, path: str) -> None:
        path = os.path.abspath(os.path.normpath(path))
        QTimer.singleShot(0, lambda p=path: self._apply_loaded_file(p))

    def _apply_loaded_file(self, path: str) -> None:
        try:
            loaded = load_audio(path)
            tb = loaded.tags
            self._loaded = loaded
            self._set_field("title", tb.title)
            self._set_field("artist", tb.artist)
            self._set_field("album", tb.album)
            self._set_field("albumartist", tb.albumartist)
            self._set_field("track", tb.track)
            self._set_field("year", tb.year)
            self._set_field("genre", tb.genre)
            self._set_field("composer", tb.composer)
            self._set_field("comment", tb.comment)
            self._set_field("bpm", tb.bpm)
            self._set_field("key", tb.key)

            wav_embed = loaded.kind == AudioKind.WAV and bool(tb.cover_data)
            self._art.set_artwork(tb.cover_data, wav_embedded=wav_embed)
            self._info_strip.setText(build_info_strip(loaded, path))

            self._stack_empty.setVisible(False)
            self._content.setVisible(True)

            name = os.path.basename(path)
            self.statusBar().showMessage(f"Loaded: {name}", 5000)
        except Exception as ex:
            self.statusBar().showMessage(f"Error: {ex}", 8000)
            QMessageBox.warning(self, "Could not open file", str(ex))

    def _set_field(self, key: str, val: str) -> None:
        w = self._fields[key]
        if isinstance(w, QComboBox):
            w.setCurrentText(val)
        else:
            w.setText(val)

    def _get_field(self, key: str) -> str:
        w = self._fields[key]
        if isinstance(w, QComboBox):
            return w.currentText().strip()
        return w.text().strip()

    def _collect_bundle(self) -> TagBundle:
        assert self._loaded is not None
        tb = TagBundle(
            title=self._get_field("title"),
            artist=self._get_field("artist"),
            album=self._get_field("album"),
            albumartist=self._get_field("albumartist"),
            track=self._get_field("track"),
            year=self._get_field("year"),
            genre=self._get_field("genre"),
            composer=self._get_field("composer"),
            comment=self._get_field("comment"),
            bpm=self._get_field("bpm"),
            key=self._get_field("key"),
            cover_data=self._loaded.tags.cover_data,
            cover_mime=self._loaded.tags.cover_mime,
            _cover_replaced=self._loaded.tags._cover_replaced,
        )
        return tb

    def replace_artwork(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select artwork",
            "",
            "Images (*.jpg *.jpeg *.png);;All files (*.*)",
        )
        if not path:
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
            Image.open(io.BytesIO(data)).verify()
        except Exception as ex:
            QMessageBox.warning(self, "Invalid image", str(ex))
            return

        mime = "image/jpeg" if path.lower().endswith((".jpg", ".jpeg")) else "image/png"
        assert self._loaded is not None
        self._loaded.tags.cover_data = data
        self._loaded.tags.cover_mime = mime
        self._loaded.tags._cover_replaced = True
        self._art.set_artwork(data)
        self.statusBar().showMessage("Artwork updated — save to write to file", 5000)

    def browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open audio",
            "",
            "Audio (*.mp3 *.flac *.m4a *.wav);;All files (*.*)",
        )
        if path:
            self.file_dropped(path)

    def save_in_place(self) -> None:
        if not self._loaded:
            self.statusBar().showMessage("No file loaded.", 4000)
            return
        tb = self._collect_bundle()
        try:
            save_tags(self._loaded, tb)
            self._loaded.tags = tb
            tb._cover_replaced = False
            self.statusBar().showMessage("Saved successfully.", 6000)
        except Exception as ex:
            self.statusBar().showMessage(f"Save failed: {ex}", 10000)
            QMessageBox.critical(self, "Save failed", str(ex))

    def save_copy(self) -> None:
        if not self._loaded:
            self.statusBar().showMessage("No file loaded.", 4000)
            return
        base = os.path.basename(self._loaded.path)
        stem, ext = os.path.splitext(base)
        default = f"{stem} (edited){ext}"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save copy as",
            default,
            "Audio (*.mp3 *.flac *.m4a *.wav);;All files (*.*)",
        )
        if not path:
            return
        import shutil
        try:
            shutil.copy2(self._loaded.path, path)
            copy_loaded = load_audio(path)
            tb = self._collect_bundle()
            copy_loaded.tags = tb
            save_tags(copy_loaded, tb)
            self.statusBar().showMessage(f"Exported copy: {os.path.basename(path)}", 8000)
        except Exception as ex:
            self.statusBar().showMessage(f"Export failed: {ex}", 10000)
            QMessageBox.critical(self, "Export failed", str(ex))

def main() -> None:
    try:
        # In windowed/frozen builds, stderr may be unavailable.
        # Guard faulthandler so startup does not abort silently.
        try:
            if sys.stderr is not None and hasattr(sys.stderr, "fileno"):
                faulthandler.enable(all_threads=True)
        except Exception:
            pass
        app = QApplication(sys.argv)
        f = QFont(FONT_FAMILY, 10)
        if not QFont(FONT_FAMILY).exactMatch():
            f = QFont(FONT_FALLBACK, 10)
        app.setFont(f)
        w = MainWindow()
        w.show()
        sys.exit(app.exec())
    except Exception as ex:
        log_path = _log_startup_exception(ex)
        QMessageBox.critical(
            None,
            "MetaEditor failed to start",
            f"{ex}\n\nA crash log was written to:\n{log_path}",
        )
        raise


if __name__ == "__main__":
    main()
