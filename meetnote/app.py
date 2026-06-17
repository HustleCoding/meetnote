"""Menu-bar application (rumps) that ties recording, detection and the pipeline together.

This module imports ``rumps`` (macOS-only). It is only imported when the menu-bar
app is actually launched, so the rest of the package works without it.
"""

from __future__ import annotations

import threading
from pathlib import Path

import rumps

from .audio import Recorder, RecorderError
from .audioswitch import OutputSwitch
from .config import Config
from .detect import active_meeting_apps
from .pipeline import process_recording

IDLE_TITLE = "●"  # shown when idle
RECORDING_TITLE = "🔴"  # shown while recording


class MeetnoteApp(rumps.App):
    def __init__(self, config: Config):
        super().__init__("Meetnote", title=IDLE_TITLE, quit_button=None)
        self.config = config
        self.recorder = Recorder(config)
        self._output_switch = OutputSwitch(config)
        self._auto_started = False  # True if the current recording was auto-triggered

        self.record_item = rumps.MenuItem("Start Recording", callback=self.on_toggle_record)
        self.auto_item = rumps.MenuItem("Auto-detect Meetings", callback=self.on_toggle_auto)
        self.auto_item.state = True
        self.status_item = rumps.MenuItem("Idle", callback=None)

        self.menu = [
            self.status_item,
            None,
            self.record_item,
            self.auto_item,
            None,
            rumps.MenuItem("Open Recordings Folder", callback=self.on_open_folder),
            None,
            rumps.MenuItem("Quit", callback=self.on_quit),
        ]

        self.timer = rumps.Timer(self.on_tick, self.config.poll_interval_seconds)
        self.timer.start()

    # ---- helpers ---------------------------------------------------------
    def _notify(self, title: str, message: str) -> None:
        if not self.config.notify:
            return
        try:
            rumps.notification(title, "", message)
        except Exception:  # pragma: no cover - notifications need a bundled app
            pass

    def _set_recording_ui(self, recording: bool) -> None:
        self.title = RECORDING_TITLE if recording else IDLE_TITLE
        self.record_item.title = "Stop Recording" if recording else "Start Recording"
        self.status_item.title = "Recording…" if recording else "Idle"

    def _start(self, auto: bool) -> None:
        self._output_switch.activate()
        try:
            path = self.recorder.start()
        except RecorderError as exc:
            self._output_switch.restore()
            rumps.alert("Meetnote — cannot record", str(exc))
            return
        self._auto_started = auto
        self._set_recording_ui(True)
        self._notify("Meetnote", f"Recording started → {Path(path).name}")

    def _stop_and_process(self) -> None:
        elapsed = self.recorder.elapsed_seconds()
        path = self.recorder.stop()
        self._output_switch.restore()
        self._auto_started = False
        self._set_recording_ui(False)
        if path is None:
            return

        if elapsed < self.config.min_recording_seconds:
            # Too short to be a real meeting — discard.
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass
            self._notify("Meetnote", "Recording discarded (too short).")
            return

        self._notify("Meetnote", "Recording saved. Transcribing…")
        self.status_item.title = "Transcribing…"
        threading.Thread(target=self._run_pipeline, args=(Path(path),), daemon=True).start()

    def _run_pipeline(self, path: Path) -> None:
        try:
            result = process_recording(path, self.config)
        except Exception as exc:  # pragma: no cover - surfaced to the user
            self._notify("Meetnote — processing failed", str(exc))
            self.status_item.title = "Idle"
            return
        name = result.summary_path.name if result.summary_path else path.name
        self._notify("Meetnote", f"Done: {name}")
        self.status_item.title = "Idle"

    # ---- callbacks -------------------------------------------------------
    def on_tick(self, _timer) -> None:
        if not self.auto_item.state:
            return
        meeting = bool(active_meeting_apps(self.config.detect_apps))
        if meeting and not self.recorder.is_recording:
            self._start(auto=True)
        elif not meeting and self.recorder.is_recording and self._auto_started:
            self._stop_and_process()

    def on_toggle_record(self, _item) -> None:
        if self.recorder.is_recording:
            self._stop_and_process()
        else:
            self._start(auto=False)

    def on_toggle_auto(self, item) -> None:
        item.state = not item.state

    def on_open_folder(self, _item) -> None:
        import subprocess

        self.config.ensure_dirs()
        subprocess.run(["open", str(self.config.recordings_dir)])

    def on_quit(self, _item) -> None:
        if self.recorder.is_recording:
            self.recorder.stop()
            self._output_switch.restore()
        rumps.quit_application()


def run_menubar(config: Config) -> int:
    config.ensure_dirs()
    MeetnoteApp(config).run()
    return 0
