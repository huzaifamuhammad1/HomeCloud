#!/bin/zsh
set -e

clear
cd "$(dirname "$0")"

echo ""
echo "╭──────────────────────────────────────────────╮"
echo "│              HOMECLOUD SETUP                 │"
echo "╰──────────────────────────────────────────────╯"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is not installed yet."
  echo ""
  echo "Open this page in Safari:"
  echo "https://www.python.org/downloads/macos/"
  echo ""
  echo "Install the latest Python 3, then run this setup file again."
  echo ""
  read "?Press Return to close..."
  exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo "→ Creating private Python environment..."

python3 -m venv .venv
source .venv/bin/activate

echo "→ Installing HomeCloud packages..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

mkdir -p HomeCloudStorage/photos HomeCloudStorage/videos HomeCloudStorage/files

echo ""
echo "✓ SETUP COMPLETE"
echo ""
echo "Next:"
echo "Double-click 02_RUN_HOMECLOUD.command"
echo ""
read "?Press Return to close..."
