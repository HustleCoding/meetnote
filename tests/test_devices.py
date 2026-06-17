from meetnote.devices import parse_audio_devices, resolve_device_index

SAMPLE = """\
[AVFoundation indev @ 0x123] AVFoundation video devices:
[AVFoundation indev @ 0x123] [0] FaceTime HD Camera
[AVFoundation indev @ 0x123] AVFoundation audio devices:
[AVFoundation indev @ 0x123] [0] MacBook Pro Microphone
[AVFoundation indev @ 0x123] [1] BlackHole 2ch
[AVFoundation indev @ 0x123] [2] Meetnote Aggregate
"""


def test_parse_audio_devices_only_returns_audio():
    devices = parse_audio_devices(SAMPLE)
    assert devices == {
        0: "MacBook Pro Microphone",
        1: "BlackHole 2ch",
        2: "Meetnote Aggregate",
    }


def test_resolve_device_index_exact_match():
    devices = parse_audio_devices(SAMPLE)
    assert resolve_device_index("Meetnote Aggregate", devices) == 2


def test_resolve_device_index_is_case_insensitive():
    devices = parse_audio_devices(SAMPLE)
    assert resolve_device_index("meetnote aggregate", devices) == 2


def test_resolve_device_index_substring_match():
    devices = parse_audio_devices(SAMPLE)
    assert resolve_device_index("BlackHole", devices) == 1


def test_resolve_device_index_missing_returns_none():
    devices = parse_audio_devices(SAMPLE)
    assert resolve_device_index("Nonexistent", devices) is None
