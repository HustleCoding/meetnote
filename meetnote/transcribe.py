"""Local transcription using faster-whisper (CTranslate2).

The faster-whisper import is deliberately lazy so that the rest of the package
(config, CLI plumbing, tests) imports fine on machines without the model deps.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import Config


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    text: str
    segments: list[TranscriptSegment]
    language: str | None = None


def _format_timestamp(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def transcript_to_text(transcript: Transcript, with_timestamps: bool = True) -> str:
    if not with_timestamps:
        return transcript.text.strip() + "\n"
    lines = [f"[{_format_timestamp(seg.start)}] {seg.text.strip()}" for seg in transcript.segments]
    return "\n".join(lines) + "\n"


def transcribe(audio_path: Path, config: Config) -> Transcript:
    """Transcribe an audio file with faster-whisper and return the full transcript."""
    from faster_whisper import WhisperModel  # lazy import (heavy, optional dep)

    model = WhisperModel(config.whisper_model, compute_type=config.whisper_compute_type)
    segments_iter, info = model.transcribe(
        str(audio_path),
        language=config.whisper_language,
        vad_filter=True,
    )

    segments: list[TranscriptSegment] = []
    parts: list[str] = []
    for seg in segments_iter:
        text = seg.text.strip()
        segments.append(TranscriptSegment(start=seg.start, end=seg.end, text=text))
        parts.append(text)

    return Transcript(
        text=" ".join(parts).strip(),
        segments=segments,
        language=getattr(info, "language", None),
    )
