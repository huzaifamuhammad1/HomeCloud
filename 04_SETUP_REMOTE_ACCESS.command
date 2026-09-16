#!/bin/zsh
set -e

clear
cd "$(dirname "$0")"

echo ""
echo "╭──────────────────────────────────────────────╮"
echo "│       HOMECLOUD SECURE REMOTE SETUP          │"
echo "╰──────────────────────────────────────────────╯"
echo ""

export TAILSCALE_BE_CLI=1

if command -v tailscale >/dev/null 2>&1; then
  TS="$(command -v tailscale)"
elif [ -x "/Applications/Tailscale.app/Contents/MacOS/Tailscale" ]; then
  TS="/Applications/Tailscale.app/Contents/MacOS/Tailscale"
else
  echo "Tailscale is not installed yet."
  echo ""
  echo "Install the Tailscale app on this Mac, sign in, then run this file again."
  echo "Official download: https://tailscale.com/download/mac"
  echo ""
  read "?Press Return to close..."
  exit 1
fi

echo "✓ Tailscale app found"

if ! "$TS" status >/dev/null 2>&1; then
  echo ""
  echo "Tailscale is installed but not connected."
  echo "Open the Tailscale app, sign in, and make sure it says Connected."
  echo ""
  read "?Press Return to close..."
  exit 1
fi

echo "✓ Tailscale connected"
echo ""
echo "→ Creating a private HTTPS route to HomeCloud..."
echo ""
echo "Tailscale may open a browser page asking you to enable HTTPS."
echo "Approve it if asked. This does NOT make HomeCloud public."
echo ""

"$TS" serve --bg 5050

DNS_NAME="$("$TS" status --json | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("Self",{}).get("DNSName","").rstrip("."))')"

if [ -z "$DNS_NAME" ]; then
  echo ""
  echo "I could not read the Tailscale HTTPS hostname."
  echo "Send a screenshot of this Terminal window."
  read "?Press Return to close..."
  exit 1
fi

PUBLIC_URL="https://${DNS_NAME}"
echo "$PUBLIC_URL" > HomeCloudData/remote_url.txt

echo ""
echo "✓ SECURE REMOTE ACCESS CONFIGURED"
echo ""
echo "Private HomeCloud address:"
echo "  $PUBLIC_URL"
echo ""
echo "IMPORTANT:"
echo "This uses Tailscale Serve, NOT Tailscale Funnel."
echo "Do not enable Funnel for HomeCloud."
echo ""
echo "Next:"
echo "1. Install Tailscale on your iPhone."
echo "2. Sign in to the SAME Tailscale account."
echo "3. Run 02_RUN_HOMECLOUD.command."
echo "4. Pair the iPhone again using the new secure QR."
echo ""
read "?Press Return to close..."
