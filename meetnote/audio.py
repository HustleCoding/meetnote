"""Audio recording via ffmpeg's avfoundation input.

We record from a single avfoundation audio device. To capture *both* your voice
and the other participants, that device should be an Aggregate Device combining
your microphone and BlackHole (see the README for the one-time setup).
"""

from __future__ import annotations

import datetime as dt
import re
import subprocess
import time
from pathlib import Path

from .config import Config
from .devices import list_audio_devices, resolve_device_index

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _slugify(label: str) -> str:
    label = _SAFE_NAME.sub("-", label.strip())
    return label.strip("-") or "meeting"


def default_recording_path(recordings_dir: Path, label: str | None = None) -> Path:
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    suffix = f"_{_slugify(label)}" if label else ""
    return recordings_dir / f"{stamp}{suffix}.m4a"


class RecorderError(RuntimeError):
    pass


class Recorder:
    """Wraps a long-running ffmpeg process that records to an .m4a file."""

    def __init__(self, config: Config, ffmpeg_bin: str = "ffmpeg"):
        self.config = config
        self.ffmpeg_bin = ffmpeg_bin
        self._proc: subprocess.Popen | None = None
        self._output_path: Path | None = None
        self._started_at: float | None = None

    @property
    def is_recording(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    @property
    def output_path(self) -> Path | None:
        return self._output_path

    def _resolve_device_index(self) -> int:
        devices = list_audio_devices(self.ffmpeg_bin)
        index = resolve_device_index(self.config.audio_device_name, devices)
        if index is None:
            available = ", ".join(f"[{i}] {n}" for i, n in sorted(devices.items())) or "(none found)"
            raise RecorderError(
                f"Audio device '{self.config.audio_device_name}' not found. "
                f"Available avfoundation audio devices: {available}. "
                "Run 'meetnote doctor' and check the README setup steps."
            )
        return index

    def _build_command(self, device_index: int, output_path: Path) -> list[str]:
        return [
            self.ffmpeg_bin,
            "-hide_banner",
            "-loglevel",
            "warning",
            "-f",
            "avfoundation",
            "-i",
            f":{device_index}",
            "-ac",
            "2",
            "-ar",
            "44100",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(output_path),
        ]

    def start(self, label: str | None = None) -> Path:
        if self.is_recording:
            raise RecorderError("A recording is already in progress.")

        self.config.ensure_dirs()
        device_index = self._resolve_device_index()
        output_path = default_recording_path(self.config.recordings_dir, label)

        self._proc = subprocess.Popen(
            self._build_command(device_index, output_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        # Give ffmpeg a moment; if it died immediately the device is unusable.
        time.sleep(0.6)
        if self._proc.poll() is not None:
            err = self._proc.stderr.read().decode(errors="replace") if self._proc.stderr else ""
            self._proc = None
            raise RecorderError(f"ffmpeg failed to start recording:\n{err.strip()}")

        self._output_path = output_path
        self._started_at = time.monotonic()
        return output_path

    def stop(self) -> Path | None:
        """Stop recording and return the finished file path (or None if nothing recorded)."""
        if self._proc is None:
            return None

        proc, self._proc = self._proc, None
        if proc.poll() is None:
            try:
                # 'q' tells ffmpeg to finish cleanly and finalize the container.
                if proc.stdin:
                    proc.stdin.write(b"q")
                    proc.stdin.flush()
                proc.wait(timeout=10)
            except (subprocess.TimeoutExpired, BrokenPipeError, OSError):
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()

        output_path = self._output_path
        self._output_path = None
        self._started_at = None
        return output_path

    def elapsed_seconds(self) -> float:
        if self._started_at is None:
            return 0.0
        return time.monotonic() - self._started_at
