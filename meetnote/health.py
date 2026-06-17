"""Environment health checks used by ``meetnote doctor``."""

from __future__ import annotations

import shutil
from dataclasses import dataclass

from .config import Config
from .devices import list_audio_devices, resolve_device_index


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def check_ffmpeg() -> Check:
    path = shutil.which("ffmpeg")
    if path:
        return Check("ffmpeg", True, path)
    return Check("ffmpeg", False, "not found — install with 'brew install ffmpeg'")


def check_audio_device(config: Config) -> Check:
    if not shutil.which("ffmpeg"):
        return Check("audio device", False, "ffmpeg missing; cannot list devices")
    try:
        devices = list_audio_devices()
    except Exception as exc:  # pragma: no cover - defensive
        return Check("audio device", False, f"error listing devices: {exc}")

    index = resolve_device_index(config.audio_device_name, devices)
    if index is None:
        available = ", ".join(f"[{i}] {n}" for i, n in sorted(devices.items())) or "(none)"
        return Check(
            "audio device",
            False,
            f"'{config.audio_device_name}' not found. Available: {available}",
        )
    return Check("audio device", True, f"'{config.audio_device_name}' -> index {index}")


def check_blackhole() -> Check:
    if not shutil.which("ffmpeg"):
        return Check("BlackHole", False, "ffmpeg missing; cannot verify")
    try:
        devices = list_audio_devices()
    except Exception as exc:  # pragma: no cover - defensive
        return Check("BlackHole", False, f"error listing devices: {exc}")
    if any("blackhole" in name.lower() for name in devices.values()):
        return Check("BlackHole", True, "BlackHole virtual device detected")
    return Check("BlackHole", False, "not found — install with 'brew install --cask blackhole-2ch'")


def check_ollama(config: Config) -> Check:
    try:
        import requests
    except ImportError:  # pragma: no cover
        return Check("ollama", False, "python 'requests' not installed")
    try:
        resp = requests.get(f"{config.ollama_host.rstrip('/')}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m.get("name", "") for m in resp.json().get("models", [])]
    except Exception as exc:
        return Check("ollama", False, f"not reachable at {config.ollama_host} ({exc})")

    if any(config.ollama_model.split(":")[0] in m for m in models):
        return Check("ollama", True, f"reachable; model '{config.ollama_model}' available")
    return Check(
        "ollama",
        False,
        f"reachable but model '{config.ollama_model}' not pulled. Run 'ollama pull {config.ollama_model}'",
    )


def check_whisper(config: Config) -> Check:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return Check("faster-whisper", False, "not installed — run 'pip install faster-whisper'")
    return Check("faster-whisper", True, f"installed; model '{config.whisper_model}' (downloads on first use)")


def run_all_checks(config: Config) -> list[Check]:
    return [
        check_ffmpeg(),
        check_blackhole(),
        check_audio_device(config),
        check_whisper(config),
        check_ollama(config),
    ]
