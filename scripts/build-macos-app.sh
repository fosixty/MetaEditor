#!/usr/bin/env bash
# Build dist/Quartz.app with PyInstaller. Run from repo root or any cwd.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -r requirements.txt -r requirements-dev.txt

rm -rf build dist
python -m PyInstaller --clean --noconfirm Quartz.spec

echo ""
echo "Built: $ROOT/dist/Quartz.app"
echo "Open it from Finder or: open dist/Quartz.app"
