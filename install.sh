#!/bin/sh
set -eu

if [ "$(uname -s)" != "Darwin" ]; then
  echo "This tool only supports macOS." >&2
  exit 1
fi

if [ ! -d /Applications/GarageBand.app ]; then
  echo "Install GarageBand from the Mac App Store first." >&2
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required to install abcmidi: https://brew.sh" >&2
  exit 1
fi

if ! command -v abc2midi >/dev/null 2>&1; then
  brew install abcmidi
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 -m venv "$SCRIPT_DIR/.venv"
"$SCRIPT_DIR/.venv/bin/python" -m pip install --upgrade pip
"$SCRIPT_DIR/.venv/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"
chmod +x "$SCRIPT_DIR/garageband"

echo "Installed. Run:"
echo "  $SCRIPT_DIR/garageband --doctor"
echo "  $SCRIPT_DIR/garageband $SCRIPT_DIR/examples/rusty-waltz.abc --mix room"
