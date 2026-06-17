#!/usr/bin/env bash
# meetnote installer for macOS.
# Installs system + Python dependencies and pulls the default Ollama model.
# The one-time audio-device setup (Aggregate Device) is manual — see the README.
set -euo pipefail

if [[ "$(uname)" != "Darwin" ]]; then
  echo "meetnote is a macOS tool. This installer only runs on macOS." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Checking Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install it from https://brew.sh and re-run." >&2
  exit 1
fi

echo "==> Installing system dependencies (ffmpeg, ollama, switchaudio-osx)"
brew install ffmpeg ollama switchaudio-osx || true

echo "==> Installing BlackHole audio driver (cask)"
# BlackHole is a cask (a system audio driver) and may prompt for your password.
if brew list --cask blackhole-2ch >/dev/null 2>&1; then
  echo "BlackHole 2ch already installed."
elif ! brew install --cask blackhole-2ch; then
  echo >&2
  echo "WARNING: 'brew install --cask blackhole-2ch' failed." >&2
  echo "It installs an audio driver and needs your macOS password, so run it" >&2
  echo "directly in your terminal, then re-run this installer:" >&2
  echo "    brew install --cask blackhole-2ch" >&2
  echo "(If BlackHole still doesn't appear afterwards: 'sudo killall coreaudiod')" >&2
fi

echo "==> Creating Python virtual environment (.venv)"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -e .

echo "==> Writing default config (if missing)"
meetnote init || true

OLLAMA_MODEL="$(python3 -c 'from meetnote.config import load_config; print(load_config().ollama_model)')"
echo "==> Pulling Ollama model: ${OLLAMA_MODEL}"
if command -v ollama >/dev/null 2>&1; then
  (ollama serve >/dev/null 2>&1 &) || true
  sleep 2
  ollama pull "${OLLAMA_MODEL}" || echo "Could not pull ${OLLAMA_MODEL}; run 'ollama pull ${OLLAMA_MODEL}' later."
fi

cat <<'EOF'

==> Almost done!

Two manual steps remain (see README for details):

  1. Create the audio capture device in "Audio MIDI Setup":
       - A Multi-Output Device (your speakers + BlackHole 2ch) so you still
         hear the call while it's captured.
       - An Aggregate Device named "Meetnote Aggregate" combining your
         microphone + BlackHole 2ch. meetnote records from this device.

  2. Grant Microphone + Screen/Audio permissions to your terminal/Python when
     macOS prompts on first run.

Then verify everything:
    source .venv/bin/activate
    meetnote doctor

And (optional) start at login:
    meetnote agent install
EOF
