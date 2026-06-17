"""Automatic output-device switching while recording (macOS).

To capture the other participants, the Mac's *output* must be a Multi-Output
Device that includes BlackHole. This module flips the system output to that
device when a recording starts and restores the previous output afterwards,
using the ``SwitchAudioSource`` CLI (``brew install switchaudio-osx``).

``SwitchAudioSource`` is shelled out lazily, and the decision logic is kept as
pure functions, so the package imports and tests fine on machines without it.
"""

from __future__ import annotations

import shutil
import subprocess

from .config import Config

SWITCH_BIN = "SwitchAudioSource"


class AudioSwitchError(RuntimeError):
    """Raised when a SwitchAudioSource invocation fails."""


def is_available() -> bool:
    """True if the SwitchAudioSource CLI is installed."""
    return shutil.which(SWITCH_BIN) is not None


def _run(args: list[str]) -> str:
    proc = subprocess.run([SWITCH_BIN, *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise AudioSwitchError(proc.stderr.strip() or f"SwitchAudioSource {args} failed")
    return proc.stdout.strip()


def get_current_output() -> str:
    """Name of the current system output device."""
    return _run(["-c", "-t", "output"])


def list_outputs() -> list[str]:
    """All available output device names."""
    return [line.strip() for line in _run(["-a", "-t", "output"]).splitlines() if line.strip()]


def set_output(name: str) -> None:
    """Set the system output device by name."""
    _run(["-t", "output", "-s", name])


def capture_output_names(config: Config) -> list[str]:
    """Configured BlackHole-containing Multi-Output device names (speakers first)."""
    names = [config.multi_output_device_name]
    if config.multi_output_device_airpods:
        names.append(config.multi_output_device_airpods)
    return names


def is_capture_output(name: str, config: Config) -> bool:
    """True if ``name`` is already one of our capture Multi-Output devices."""
    return name in capture_output_names(config)


def choose_target_output(current: str, available: list[str], config: Config) -> str | None:
    """Pick the Multi-Output device to switch to, or ``None`` if none is usable.

    If the current output looks like AirPods/headphones and an AirPods capture
    device is configured, prefer it; otherwise fall back to the default
    (speakers) Multi-Output device. Returns ``None`` when the chosen device is
    not actually available, so callers can warn instead of switching blindly.
    """
    if "airpod" in current.lower() and config.multi_output_device_airpods:
        target = config.multi_output_device_airpods
    else:
        target = config.multi_output_device_name
    return target if target in available else None


class OutputSwitch:
    """Context manager that routes output through a capture device while active.

    No-op unless ``config.auto_switch_output`` is set. Any failure is reported
    and swallowed so it can never break a recording.
    """

    def __init__(self, config: Config):
        self.config = config
        self._previous: str | None = None
        self._switched = False

    def activate(self) -> None:
        """Switch output to a capture device, remembering the previous one."""
        if not self.config.auto_switch_output:
            return
        if not is_available():
            print(
                "auto_switch_output is on but SwitchAudioSource is missing; "
                "install with 'brew install switchaudio-osx'. "
                "Recording without switching output."
            )
            return
        try:
            current = get_current_output()
            if is_capture_output(current, self.config):
                return  # already routed through a capture device
            available = list_outputs()
            target = choose_target_output(current, available, self.config)
            if target is None:
                print(
                    f"No capture Multi-Output device found for current output '{current}'. "
                    "Create one (your speakers/AirPods + BlackHole 2ch) in Audio MIDI Setup "
                    "and set 'multi_output_device_name'/'multi_output_device_airpods' in your "
                    "config. Recording without switching output."
                )
                return
            set_output(target)
            self._previous = current
            self._switched = True
            print(f"Switched audio output: '{current}' -> '{target}'")
        except AudioSwitchError as exc:
            print(f"Could not switch audio output ({exc}); recording without switching.")

    def restore(self) -> None:
        """Restore the output device that was active before :meth:`activate`."""
        if self._switched and self._previous:
            try:
                set_output(self._previous)
                print(f"Restored audio output -> '{self._previous}'")
            except AudioSwitchError as exc:
                print(f"Could not restore audio output to '{self._previous}' ({exc}).")
        self._switched = False
        self._previous = None

    def __enter__(self) -> OutputSwitch:
        self.activate()
        return self

    def __exit__(self, *exc_info: object) -> bool:
        self.restore()
        return False
