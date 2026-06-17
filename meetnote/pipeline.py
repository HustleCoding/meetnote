"""Post-recording pipeline: transcribe an audio file, then summarize it.

Outputs are written next to the audio file, sharing its stem:
    <name>.m4a          (recording)
    <name>.transcript.txt
    <name>.summary.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Config
from .summarize import summarize
from .transcribe import Transcript, transcribe, transcript_to_text


@dataclass
class PipelineResult:
    audio_path: Path
    transcript_path: Path | None = None
    summary_path: Path | None = None
    transcript: Transcript | None = None
    summary: str | None = None


def transcript_path_for(audio_path: Path) -> Path:
    return audio_path.with_suffix("").with_suffix(".transcript.txt")


def summary_path_for(audio_path: Path) -> Path:
    return audio_path.with_suffix("").with_suffix(".summary.md")


def process_recording(
    audio_path: Path,
    config: Config,
    do_transcribe: bool | None = None,
    do_summarize: bool | None = None,
) -> PipelineResult:
    """Run transcription and summarization for ``audio_path`` per config flags."""
    do_transcribe = config.auto_transcribe if do_transcribe is None else do_transcribe
    do_summarize = config.auto_summarize if do_summarize is None else do_summarize

    result = PipelineResult(audio_path=audio_path)
    if not do_transcribe:
        return result

    transcript = transcribe(audio_path, config)
    transcript_path = transcript_path_for(audio_path)
    transcript_path.write_text(transcript_to_text(transcript, with_timestamps=True))
    result.transcript = transcript
    result.transcript_path = transcript_path

    if do_summarize and transcript.text.strip():
        summary = summarize(transcript.text, config)
        summary_path = summary_path_for(audio_path)
        summary_path.write_text(summary + "\n")
        result.summary = summary
        result.summary_path = summary_path

    return result
