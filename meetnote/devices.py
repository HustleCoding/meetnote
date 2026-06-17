"""Discovery of avfoundation audio input devices via ffmpeg.

macOS exposes capture devices through ffmpeg's ``avfoundation`` input. We list
them and resolve a human-readable device name (e.g. an Aggregate Device) to the
numeric index that ``ffmpeg -i ":<index>"`` expects.
"""

from __future__ import annotations

import re
import subprocess

_AUDIO_HEADER = re.compile(r"AVFoundation audio devices:")
_VIDEO_HEADER = re.compile(r"AVFoundation video devices:")
_DEVICE_LINE = re.compile(r"\[(\d+)\]\s+(.*\S)\s*$")


def parse_audio_devices(ffmpeg_stderr: str) -> dict[int, str]:
    """Parse ``ffmpeg -list_devices`` stderr into ``{index: name}`` for audio devices."""
    devices: dict[int, str] = {}
    in_audio_section = False
    for line in ffmpeg_stderr.splitlines():
        if _AUDIO_HEADER.search(line):
            in_audio_section = True
            continue
        if _VIDEO_HEADER.search(line):
            in_audio_section = False
            continue
        if not in_audio_section:
            continue
        match = _DEVICE_LINE.search(line)
        if match:
            devices[int(match.group(1))] = match.group(2)
    return devices


def list_audio_devices(ffmpeg_bin: str = "ffmpeg") -> dict[int, str]:
    """Return the avfoundation audio devices available on this machine."""
    proc = subprocess.run(
        [ffmpeg_bin, "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
        capture_output=True,
        text=True,
    )
    # ffmpeg prints the device list to stderr and exits non-zero; that's expected.
    return parse_audio_devices(proc.stderr)


def resolve_device_index(name: str, devices: dict[int, str]) -> int | None:
    """Resolve a device *name* to its index.

    Tries an exact (case-insensitive) match first, then a substring match.
    """
    name_lower = name.strip().lower()
    for index, device_name in devices.items():
        if device_name.strip().lower() == name_lower:
            return index
    for index, device_name in devices.items():
        if name_lower in device_name.strip().lower():
            return index
    return None
