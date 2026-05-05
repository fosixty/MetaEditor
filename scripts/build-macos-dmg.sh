#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# build-macos-dmg.sh
# Builds a distributable Quartz-<version>.dmg macOS installer.
#
# Usage:
#   ./scripts/build-macos-dmg.sh            # uses existing dist/Quartz.app
#   ./scripts/build-macos-dmg.sh --rebuild  # rebuilds Quartz.app first
#
# Output: dist/Quartz-<version>.dmg
# Requires: macOS (hdiutil, built in)
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ── helpers ──────────────────────────────────────────────────────────────────
info()  { printf '\033[1;34m==> \033[0m%s\n' "$*"; }
ok()    { printf '\033[1;32m ✓  \033[0m%s\n' "$*"; }
die()   { printf '\033[1;31mERROR: \033[0m%s\n' "$*" >&2; exit 1; }

# ── optional rebuild ─────────────────────────────────────────────────────────
if [[ "${1:-}" == "--rebuild" ]]; then
    info "Rebuilding Quartz.app via PyInstaller..."
    bash "$ROOT/scripts/build-macos-app.sh"
fi

APP_BUNDLE="$ROOT/dist/Quartz.app"
[[ -d "$APP_BUNDLE" ]] || die "dist/Quartz.app not found. Run with --rebuild or run build-macos-app.sh first."

# ── read version from Info.plist (falls back to "1.0") ───────────────────────
PLIST="$APP_BUNDLE/Contents/Info.plist"
VERSION=""
if [[ -f "$PLIST" ]]; then
    VERSION=$(defaults read "$PLIST" CFBundleShortVersionString 2>/dev/null || true)
fi
[[ -z "$VERSION" || "$VERSION" == "(null)" ]] && VERSION="1.0"

DMG_NAME="Quartz-${VERSION}"
DMG_OUT="$ROOT/dist/${DMG_NAME}.dmg"
STAGING=$(mktemp -d)
trap 'rm -rf "$STAGING"' EXIT

# ── stage app + Applications symlink ─────────────────────────────────────────
info "Staging installer content..."
cp -R "$APP_BUNDLE" "$STAGING/Quartz.app"
ln -s /Applications "$STAGING/Applications"

# ── create writable DMG from staging dir ─────────────────────────────────────
SCRATCH=$(mktemp -u "$ROOT/dist/scratch_XXXXXX.dmg")
info "Creating DMG..."
hdiutil create \
    -volname "Quartz" \
    -srcfolder "$STAGING" \
    -ov \
    -format UDRW \
    -fs HFS+ \
    "$SCRATCH" >/dev/null

# ── convert to compressed read-only DMG ──────────────────────────────────────
info "Compressing DMG..."
rm -f "$DMG_OUT"
hdiutil convert "$SCRATCH" -format UDZO -imagekey zlib-level=9 -o "$DMG_OUT" >/dev/null
rm -f "$SCRATCH"

ok "Installer ready: dist/${DMG_NAME}.dmg"
echo ""
echo "  Size : $(du -sh "$DMG_OUT" | cut -f1)"
echo "  Path : $DMG_OUT"
echo ""
echo "To test:  open \"$DMG_OUT\""
