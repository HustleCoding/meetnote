"""Configuration loading for meetnote.

Config is stored as TOML at ``~/.config/meetnote/config.toml``. Any field that is
missing falls back to the defaults defined here, so the file is always optional.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, fields
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised only on Python 3.10
    import tomli as tomllib

CONFIG_DIR = Path(os.path.expanduser("~/.config/meetnote"))
CONFIG_PATH = CONFIG_DIR / "config.toml"

# Process-name substrings that indicate a meeting app is running. Matching is
# case-insensitive and substring-based against the running process names.
DEFAULT_DETECT_APPS = [
    "zoom.us",
    "Microsoft Teams",
    "Webex",
    "Slack",
    "FaceTime",
    "Discord",
    "GoogleMeet",
]


@dataclass
class Config:
    # Where finished recordings, transcripts and summaries are written.
    recordings_dir: Path = Path(os.path.expanduser("~/Recordings/Meetnote"))

    # faster-whisper model name (e.g. "tiny.en", "base.en", "small", "medium").
    whisper_model: str = "base.en"
    # CTranslate2 compute type. "int8" is a good CPU default on Apple Silicon.
    whisper_compute_type: str = "int8"
    # Force a language code (e.g. "en") or leave None to auto-detect.
    whisper_language: str | None = None

    # Ollama model used for summaries and the host it listens on.
    ollama_model: str = "llama3.1:8b"
    ollama_host: str = "http://localhost:11434"

    # The avfoundation input device to record from. This should be an Aggregate
    # Device that combines your microphone and BlackHole so both sides of the
    # call are captured. Set by name; the index is resolved at runtime.
    audio_device_name: str = "Meetnote Aggregate"

    # Automatically route the system output through a BlackHole Multi-Output
    # Device while recording (so participants are captured), restoring it after.
    # Requires SwitchAudioSource ('brew install switchaudio-osx').
    auto_switch_output: bool = False
    # Multi-Output Device (your speakers + BlackHole 2ch) used while recording.
    multi_output_device_name: str = "Multi-Output Device"
    # Optional Multi-Output Device (your AirPods + BlackHole 2ch); used instead
    # when the current output looks like AirPods. Leave blank to disable.
    multi_output_device_airpods: str = ""

    # Meeting detection.
    detect_apps: list[str] = field(default_factory=lambda: list(DEFAULT_DETECT_APPS))
    poll_interval_seconds: float = 5.0
    # Recordings shorter than this (seconds) are discarded as false positives.
    min_recording_seconds: float = 20.0

    # Pipeline behaviour after a recording stops.
    auto_transcribe: bool = True
    auto_summarize: bool = True
    # Show a macOS notification when recording starts/stops (consent reminder).
    notify: bool = True

    def ensure_dirs(self) -> None:
        self.recordings_dir.mkdir(parents=True, exist_ok=True)


def _coerce(name: str, value: object) -> object:
    if name == "recordings_dir" and isinstance(value, str):
        return Path(os.path.expanduser(value))
    return value


def load_config(path: Path | None = None) -> Config:
    """Load config from ``path`` (defaults to ``CONFIG_PATH``), filling gaps with defaults."""
    path = path or CONFIG_PATH
    cfg = Config()
    if not path.exists():
        return cfg

    with path.open("rb") as fh:
        data = tomllib.load(fh)

    known = {f.name for f in fields(Config)}
    for key, value in data.items():
        if key in known and value is not None:
            setattr(cfg, key, _coerce(key, value))
    return cfg


DEFAULT_CONFIG_TOML = """\
# meetnote configuration. All values are optional; delete any line to use the default.

# Where recordings, transcripts and summaries are saved.
recordings_dir = "~/Recordings/Meetnote"

# faster-whisper transcription model. Bigger = more accurate but slower.
# Options: tiny.en, base.en, small.en, small, medium, large-v3
whisper_model = "base.en"
whisper_compute_type = "int8"
# whisper_language = "en"

# Local Ollama model used to summarize transcripts.
ollama_model = "llama3.1:8b"
ollama_host = "http://localhost:11434"

# avfoundation Aggregate Device that mixes your mic + BlackHole (see README).
audio_device_name = "Meetnote Aggregate"

# Auto-route output through a BlackHole Multi-Output Device while recording so
# participants are captured, then restore your previous output afterwards.
# Requires SwitchAudioSource ('brew install switchaudio-osx').
auto_switch_output = false
multi_output_device_name = "Multi-Output Device"
# If you wear AirPods, create an "AirPods + BlackHole 2ch" Multi-Output Device
# and put its name here; meetnote uses it automatically when you're on AirPods.
multi_output_device_airpods = ""

# Apps whose presence triggers auto-recording (substring, case-insensitive).
detect_apps = ["zoom.us", "Microsoft Teams", "Webex", "Slack", "FaceTime", "Discord"]
poll_interval_seconds = 5.0
min_recording_seconds = 20.0

auto_transcribe = true
auto_summarize = true
notify = true
"""


def write_default_config(path: Path | None = None, overwrite: bool = False) -> Path:
    """Write a commented default config file. Returns the path written."""
    path = path or CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return path
    path.write_text(DEFAULT_CONFIG_TOML)
    return path
