from pathlib import Path

from meetnote.pipeline import summary_path_for, transcript_path_for
from meetnote.summarize import build_summary_prompt


def test_output_paths_share_stem():
    audio = Path("/tmp/2026-06-17_10-00-00_standup.m4a")
    assert transcript_path_for(audio).name == "2026-06-17_10-00-00_standup.transcript.txt"
    assert summary_path_for(audio).name == "2026-06-17_10-00-00_standup.summary.md"
    assert transcript_path_for(audio).parent == audio.parent


def test_summary_prompt_has_required_sections():
    prompt = build_summary_prompt("Alice: hello. Bob: hi.")
    for heading in ("## Overview", "## Key Points", "## Decisions", "## Action Items"):
        assert heading in prompt
    assert "Alice: hello" in prompt
