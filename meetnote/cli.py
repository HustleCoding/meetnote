"""Command-line interface for meetnote."""

from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

from . import __version__
from .audio import Recorder, RecorderError
from .config import CONFIG_PATH, Config, load_config, write_default_config
from .pipeline import process_recording, transcript_path_for


def _print_result(result) -> None:
    print(f"Recording:  {result.audio_path}")
    if result.transcript_path:
        print(f"Transcript: {result.transcript_path}")
    if result.summary_path:
        print(f"Summary:    {result.summary_path}")


def cmd_init(args: argparse.Namespace, config: Config) -> int:
    path = write_default_config(args.config, overwrite=args.force)
    print(f"Wrote config to {path}")
    return 0


def cmd_devices(args: argparse.Namespace, config: Config) -> int:
    from .devices import list_audio_devices

    devices = list_audio_devices()
    if not devices:
        print("No avfoundation audio devices found (are you on macOS with ffmpeg?).")
        return 1
    print("avfoundation audio devices:")
    for index, name in sorted(devices.items()):
        marker = "  <- configured" if name.strip().lower() == config.audio_device_name.lower() else ""
        print(f"  [{index}] {name}{marker}")
    return 0


def cmd_doctor(args: argparse.Namespace, config: Config) -> int:
    from .health import run_all_checks

    checks = run_all_checks(config)
    all_ok = True
    for check in checks:
        status = "OK " if check.ok else "FAIL"
        all_ok = all_ok and check.ok
        print(f"[{status}] {check.name}: {check.detail}")
    print()
    print("All good!" if all_ok else "Some checks failed — see the README setup steps.")
    return 0 if all_ok else 1


def cmd_record(args: argparse.Namespace, config: Config) -> int:
    recorder = Recorder(config)
    try:
        path = recorder.start(label=args.name)
    except RecorderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Recording to {path}")
    print("Press Ctrl+C to stop.")

    stop_requested = {"value": False}

    def _handler(signum, frame):  # noqa: ARG001
        stop_requested["value"] = True

    signal.signal(signal.SIGINT, _handler)
    elapsed = 0.0
    try:
        while not stop_requested["value"] and recorder.is_recording:
            time.sleep(0.25)
    finally:
        elapsed = recorder.elapsed_seconds()
        path = recorder.stop()

    if path is None:
        print("Nothing was recorded.")
        return 1
    print(f"Saved {path} ({elapsed:.0f}s).")

    if config.auto_transcribe:
        print("Transcribing and summarizing (this can take a while)...")
        result = process_recording(path, config)
        _print_result(result)
    return 0


def cmd_process(args: argparse.Namespace, config: Config) -> int:
    audio_path = Path(args.audio).expanduser()
    if not audio_path.exists():
        print(f"error: file not found: {audio_path}", file=sys.stderr)
        return 1
    print("Transcribing and summarizing (this can take a while)...")
    result = process_recording(
        audio_path,
        config,
        do_transcribe=True,
        do_summarize=not args.no_summary,
    )
    _print_result(result)
    return 0


def cmd_transcribe(args: argparse.Namespace, config: Config) -> int:
    from .transcribe import transcribe, transcript_to_text

    audio_path = Path(args.audio).expanduser()
    if not audio_path.exists():
        print(f"error: file not found: {audio_path}", file=sys.stderr)
        return 1
    transcript = transcribe(audio_path, config)
    out = transcript_path_for(audio_path)
    out.write_text(transcript_to_text(transcript))
    print(f"Transcript: {out}")
    return 0


def cmd_summarize(args: argparse.Namespace, config: Config) -> int:
    from .summarize import summarize

    transcript_path = Path(args.transcript).expanduser()
    if not transcript_path.exists():
        print(f"error: file not found: {transcript_path}", file=sys.stderr)
        return 1
    summary = summarize(transcript_path.read_text(), config)
    out = transcript_path.with_suffix("").with_suffix(".summary.md")
    out.write_text(summary + "\n")
    print(f"Summary: {out}")
    return 0


def cmd_menubar(args: argparse.Namespace, config: Config) -> int:
    from .app import run_menubar

    return run_menubar(config)


def cmd_agent(args: argparse.Namespace, config: Config) -> int:
    from .agent import install_agent, uninstall_agent

    if args.action == "install":
        path = install_agent()
        print(f"Installed and loaded launchd agent: {path}")
        print("meetnote will now start automatically at login.")
    else:
        uninstall_agent()
        print("Unloaded and removed launchd agent.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="meetnote", description="Local-first macOS meeting recorder.")
    parser.add_argument("--version", action="version", version=f"meetnote {__version__}")
    parser.add_argument("--config", type=Path, default=None, help="path to config.toml")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="write a default config file")
    p_init.add_argument("--force", action="store_true", help="overwrite an existing config")
    p_init.set_defaults(func=cmd_init)

    sub.add_parser("devices", help="list avfoundation audio devices").set_defaults(func=cmd_devices)
    sub.add_parser("doctor", help="check that the environment is set up correctly").set_defaults(func=cmd_doctor)

    p_record = sub.add_parser("record", help="record until Ctrl+C, then transcribe/summarize")
    p_record.add_argument("--name", default=None, help="label for the recording filename")
    p_record.set_defaults(func=cmd_record)

    p_process = sub.add_parser("process", help="transcribe and summarize an existing audio file")
    p_process.add_argument("audio")
    p_process.add_argument("--no-summary", action="store_true", help="transcribe only")
    p_process.set_defaults(func=cmd_process)

    p_transcribe = sub.add_parser("transcribe", help="transcribe an audio file")
    p_transcribe.add_argument("audio")
    p_transcribe.set_defaults(func=cmd_transcribe)

    p_summarize = sub.add_parser("summarize", help="summarize a transcript file")
    p_summarize.add_argument("transcript")
    p_summarize.set_defaults(func=cmd_summarize)

    sub.add_parser("menubar", help="run the menu-bar app").set_defaults(func=cmd_menubar)

    p_agent = sub.add_parser("agent", help="manage the login (launchd) agent")
    p_agent.add_argument("action", choices=["install", "uninstall"])
    p_agent.set_defaults(func=cmd_agent)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config or CONFIG_PATH)
    return args.func(args, config)


if __name__ == "__main__":
    raise SystemExit(main())
