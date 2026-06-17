from meetnote.audioswitch import (
    capture_output_names,
    choose_target_output,
    is_capture_output,
)
from meetnote.config import Config

AVAILABLE = [
    "MacBook Pro Speakers",
    "Florin's AirPods Pro",
    "Multi-Output Device",
    "AirPods Capture",
]


def test_capture_output_names_includes_airpods_when_set():
    cfg = Config(multi_output_device_name="Multi-Output Device", multi_output_device_airpods="AirPods Capture")
    assert capture_output_names(cfg) == ["Multi-Output Device", "AirPods Capture"]


def test_capture_output_names_omits_blank_airpods():
    cfg = Config(multi_output_device_name="Multi-Output Device")
    assert capture_output_names(cfg) == ["Multi-Output Device"]


def test_is_capture_output_true_for_configured_device():
    cfg = Config(multi_output_device_name="Multi-Output Device")
    assert is_capture_output("Multi-Output Device", cfg) is True
    assert is_capture_output("MacBook Pro Speakers", cfg) is False


def test_choose_target_defaults_to_speakers_multi_output():
    cfg = Config(multi_output_device_name="Multi-Output Device")
    assert choose_target_output("MacBook Pro Speakers", AVAILABLE, cfg) == "Multi-Output Device"


def test_choose_target_prefers_airpods_device_when_on_airpods():
    cfg = Config(multi_output_device_name="Multi-Output Device", multi_output_device_airpods="AirPods Capture")
    assert choose_target_output("Florin's AirPods Pro", AVAILABLE, cfg) == "AirPods Capture"


def test_choose_target_falls_back_when_no_airpods_device_configured():
    cfg = Config(multi_output_device_name="Multi-Output Device")
    assert choose_target_output("Florin's AirPods Pro", AVAILABLE, cfg) == "Multi-Output Device"


def test_choose_target_none_when_device_unavailable():
    cfg = Config(multi_output_device_name="Nonexistent Device")
    assert choose_target_output("MacBook Pro Speakers", AVAILABLE, cfg) is None


def test_choose_target_none_when_airpods_device_unavailable():
    cfg = Config(multi_output_device_name="Multi-Output Device", multi_output_device_airpods="Missing AirPods")
    assert choose_target_output("Some AirPods", AVAILABLE, cfg) is None
