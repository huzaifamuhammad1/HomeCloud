#!/bin/zsh
set -e

clear
cd "$(dirname "$0")"

echo ""
echo "╭──────────────────────────────────────────────╮"
echo "│             HOMECLOUD STAGE 6                │"
echo "│          PRIVATE REMOTE ACCESS               │"
echo "╰──────────────────────────────────────────────╯"
echo ""

if [ ! -d ".venv" ]; then
  echo "HomeCloud is not set up yet."
  echo "Run 01_SETUP_HOMECLOUD.command first."
  read "?Press Return to close..."
  exit 1
fi

if [ ! -f "HomeCloudData/remote_url.txt" ]; then
  echo "Secure remote access is not configured yet."
  echo ""
  echo "Run 04_SETUP_REMOTE_ACCESS.command first."
  echo ""
  read "?Press Return to close..."
  exit 1
fi

PUBLIC_URL="$(cat HomeCloudData/remote_url.txt)"
export HOMECLOUD_PUBLIC_URL="$PUBLIC_URL"
export HOMECLOUD_SECURE_COOKIE="1"
export TAILSCALE_BE_CLI=1

if command -v tailscale >/dev/null 2>&1; then
  TS="$(command -v tailscale)"
elif [ -x "/Applications/Tailscale.app/Contents/MacOS/Tailscale" ]; then
  TS="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
else
  echo "Tailscale is missing. Open/install Tailscale, then try again."
  read "?Press Return to close..."
  exit 1
fi

if ! "$TS" status >/dev/null 2>&1; then
  echo "Tailscale is not connected."
  echo "Open Tailscale and connect it, then run HomeCloud again."
  read "?Press Return to close..."
  exit 1
fi

# Ensure Serve remains configured privately.
"$TS" serve --bg 5050 >/dev/null

source .venv/bin/activate

echo "Mac admin page:"
echo "  http://127.0.0.1:5050"
echo ""
echo "Private iPhone / remote URL:"
echo "  $PUBLIC_URL"
echo ""
echo "HomeCloud now listens ONLY on this Mac."
echo "Tailscale Serve provides the private HTTPS connection."
echo ""
echo "Keep this Terminal window open."
echo "Press Control + C to stop HomeCloud."
echo ""

(sleep 1.4; open "http://127.0.0.1:5050") &

python app.py
