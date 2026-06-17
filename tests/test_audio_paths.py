from pathlib import Path

from meetnote.audio import _slugify, default_recording_path


def test_slugify_sanitizes_labels():
    assert _slugify("Weekly Sync!") == "Weekly-Sync"
    assert _slugify("  spaces  ") == "spaces"
    assert _slugify("///") == "meeting"


def test_default_recording_path_uses_label_and_extension():
    path = default_recording_path(Path("/tmp/recordings"), label="Standup")
    assert path.parent == Path("/tmp/recordings")
    assert path.suffix == ".m4a"
    assert path.name.endswith("_Standup.m4a")


def test_default_recording_path_without_label():
    path = default_recording_path(Path("/tmp/recordings"))
    assert path.suffix == ".m4a"
    assert "_" in path.stem  # date_time stem
