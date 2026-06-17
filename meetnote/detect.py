"""Meeting detection based on running processes.

This is intentionally simple and dependency-light: we scan process names for the
configured meeting apps. Browser-based calls (e.g. Google Meet in a tab) are hard
to detect reliably, so the menu-bar app always offers a manual start/stop toggle.
"""

from __future__ import annotations

from collections.abc import Iterable


def _iter_process_names() -> Iterable[str]:
    import psutil  # imported lazily so the module imports on systems without psutil

    for proc in psutil.process_iter(["name"]):
        name = proc.info.get("name")
        if name:
            yield name


def active_meeting_apps(detect_apps: list[str], process_names: Iterable[str] | None = None) -> list[str]:
    """Return the configured app names that currently appear to be running.

    ``process_names`` can be supplied for testing; otherwise the live process list
    is scanned.
    """
    if process_names is None:
        process_names = list(_iter_process_names())
    else:
        process_names = list(process_names)

    lowered = [p.lower() for p in process_names]
    found: list[str] = []
    for app in detect_apps:
        needle = app.lower()
        if any(needle in name for name in lowered):
            found.append(app)
    return found


def is_meeting_active(detect_apps: list[str], process_names: Iterable[str] | None = None) -> bool:
    return bool(active_meeting_apps(detect_apps, process_names))
