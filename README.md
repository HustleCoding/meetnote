# meetnote

A **local-first macOS meeting recorder**. It runs quietly in your menu bar,
auto-detects when you're in a meeting, records both sides of the call, and then
**transcribes and summarizes** everything **on your machine** — no audio ever
leaves your computer.

- 🎙️ Records your mic **and** the other participants (system audio)
- 🤖 Auto-starts/stops when Zoom, Teams, Webex, Slack, etc. are running (or toggle manually)
- 📝 On-device transcription with [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- 🧠 On-device summaries + action items with [Ollama](https://ollama.com)
- 🔒 100% local — private and free

> **Consent matters.** Recording meetings is legally restricted in many places
> ("all-party consent" jurisdictions). meetnote shows a notification when it
> starts recording and gives you an explicit toggle. Make sure participants are
> aware and you comply with the laws that apply to you.

---

## How it works

```
                  ┌──────────────┐
  mic ─────────┐  │  meetnote    │   ~/Recordings/Meetnote/
               ├─▶│  menu-bar    │──▶  2026-06-17_10-00_standup.m4a
  system audio ┘  │  app         │     2026-06-17_10-00_standup.transcript.txt
  (via BlackHole) └──────────────┘     2026-06-17_10-00_standup.summary.md
                       │  │
              ffmpeg ──┘  └── faster-whisper → Ollama
```

`meetnote` records from a single macOS **Aggregate Device** that mixes your
microphone with [BlackHole](https://existential.audio/blackhole/) (a virtual
audio device that exposes system audio). When a recording stops, it runs
faster-whisper for the transcript and Ollama for the summary.

---

## Requirements

- macOS 12+ (Apple Silicon recommended)
- [Homebrew](https://brew.sh)
- Python 3.10+

## Install

```bash
git clone https://github.com/HustleCoding/meetnote.git
cd meetnote
./install.sh
```

`install.sh` installs `ffmpeg`, `blackhole-2ch`, and `ollama`, creates a Python
virtualenv, installs meetnote, writes a default config, and pulls the default
Ollama model.

### One-time audio setup (the important part)

macOS won't let apps capture system audio directly, so we route it through
BlackHole. Open **Audio MIDI Setup** (`/Applications/Utilities`) and create:

1. **Multi-Output Device** — check **your speakers/headphones** *and* **BlackHole 2ch**.
   Set this as your Mac's **output** while in meetings so you still hear people
   *and* BlackHole receives the audio.
2. **Aggregate Device** named **`Meetnote Aggregate`** — check **your microphone**
   *and* **BlackHole 2ch**. This is what meetnote records from.

> Prefer not to rename? Set `audio_device_name` in your config to whatever you
> called the aggregate device.

Then grant **Microphone** permission (and **Screen & System Audio Recording** if
prompted) to your terminal / Python under **System Settings → Privacy & Security**.

### Verify

```bash
source .venv/bin/activate
meetnote doctor
```

You want all checks to pass:

```
[OK ] ffmpeg: /opt/homebrew/bin/ffmpeg
[OK ] BlackHole: BlackHole virtual device detected
[OK ] audio device: 'Meetnote Aggregate' -> index 2
[OK ] faster-whisper: installed; model 'base.en' (downloads on first use)
[OK ] ollama: reachable; model 'llama3.1:8b' available
```

---

## Usage

### Menu-bar app (recommended)

```bash
meetnote menubar
```

A `●` icon appears in your menu bar (turns `🔴` while recording). With
**Auto-detect Meetings** on, it starts/stops automatically. You can also start
and stop manually from the menu, and open the recordings folder.

Start it automatically at login:

```bash
meetnote agent install     # installs a launchd LaunchAgent
meetnote agent uninstall   # removes it
```

### Command line

```bash
meetnote record --name standup     # record until Ctrl+C, then transcribe + summarize
meetnote process meeting.m4a       # transcribe + summarize an existing file
meetnote transcribe meeting.m4a    # transcript only
meetnote summarize meeting.transcript.txt
meetnote devices                   # list audio input devices
meetnote doctor                    # check your setup
meetnote init                      # write a default config file
```

---

## Configuration

Config lives at `~/.config/meetnote/config.toml` (run `meetnote init` to create
it). See [`config.example.toml`](config.example.toml) for all options. Common ones:

| Key | Default | Notes |
|-----|---------|-------|
| `recordings_dir` | `~/Recordings/Meetnote` | where files are written |
| `whisper_model` | `base.en` | `tiny.en`→`large-v3`; bigger = better/slower |
| `ollama_model` | `llama3.1:8b` | any model you've `ollama pull`-ed |
| `audio_device_name` | `Meetnote Aggregate` | your aggregate input device |
| `detect_apps` | Zoom/Teams/Webex/Slack/… | substring match on process names |
| `min_recording_seconds` | `20` | shorter recordings are discarded |
| `notify` | `true` | show a notification when recording starts/stops |

---

## Output

Each meeting produces three files that share a timestamped name:

- `…​.m4a` — the audio recording
- `…​.transcript.txt` — timestamped transcript
- `…​.summary.md` — Overview / Key Points / Decisions / Action Items

---

## Troubleshooting

- **`audio device 'Meetnote Aggregate' not found`** — finish the Audio MIDI Setup
  step, or run `meetnote devices` and set `audio_device_name` to a listed device.
- **Recording is silent / only my voice** — your output isn't going through the
  Multi-Output Device, so BlackHole isn't receiving system audio. Switch your Mac
  output to the Multi-Output Device during meetings.
- **`Could not reach Ollama`** — start it with `ollama serve` and ensure the model
  is pulled (`ollama pull llama3.1:8b`).
- **No transcript** — make sure `faster-whisper` installed (`pip install -e .`).

---

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

## License

MIT
