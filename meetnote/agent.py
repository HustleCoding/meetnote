"""Install/uninstall a launchd LaunchAgent so meetnote starts at login.

The agent runs ``meetnote menubar`` using the current Python interpreter, so it
works whether meetnote is installed in a venv or globally.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

LABEL = "com.hustlecoding.meetnote"
LAUNCH_AGENTS_DIR = Path(os.path.expanduser("~/Library/LaunchAgents"))


def plist_path() -> Path:
    return LAUNCH_AGENTS_DIR / f"{LABEL}.plist"


def render_plist(python_executable: str | None = None) -> str:
    python_executable = python_executable or sys.executable
    log_dir = Path(os.path.expanduser("~/Library/Logs"))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_executable}</string>
        <string>-m</string>
        <string>meetnote</string>
        <string>menubar</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>{log_dir / 'meetnote.log'}</string>
    <key>StandardErrorPath</key>
    <string>{log_dir / 'meetnote.error.log'}</string>
</dict>
</plist>
"""


def install_agent(python_executable: str | None = None) -> Path:
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = plist_path()
    path.write_text(render_plist(python_executable))
    # Reload if already loaded, then load.
    subprocess.run(["launchctl", "unload", str(path)], capture_output=True)
    subprocess.run(["launchctl", "load", str(path)], check=True)
    return path


def uninstall_agent() -> None:
    path = plist_path()
    if path.exists():
        subprocess.run(["launchctl", "unload", str(path)], capture_output=True)
        path.unlink()
