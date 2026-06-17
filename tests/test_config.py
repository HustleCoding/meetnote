from pathlib import Path

from meetnote.config import Config, load_config, write_default_config


def test_defaults_are_sane():
    cfg = Config()
    assert cfg.whisper_model
    assert cfg.ollama_host.startswith("http")
    assert "zoom.us" in cfg.detect_apps


def test_load_missing_file_returns_defaults(tmp_path):
    cfg = load_config(tmp_path / "does-not-exist.toml")
    assert isinstance(cfg, Config)
    assert cfg.whisper_model == Config().whisper_model


def test_load_overrides_and_expands_paths(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        'recordings_dir = "~/CustomMeetings"\n'
        'whisper_model = "small"\n'
        'detect_apps = ["zoom.us"]\n'
    )
    cfg = load_config(path)
    assert cfg.whisper_model == "small"
    assert cfg.detect_apps == ["zoom.us"]
    assert cfg.recordings_dir == Path.home() / "CustomMeetings"


def test_unknown_keys_are_ignored(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('whisper_model = "tiny.en"\nbogus_key = 123\n')
    cfg = load_config(path)
    assert cfg.whisper_model == "tiny.en"
    assert not hasattr(cfg, "bogus_key")


def test_write_default_config_roundtrips(tmp_path):
    path = tmp_path / "config.toml"
    write_default_config(path)
    assert path.exists()
    cfg = load_config(path)
    assert cfg.whisper_model == Config().whisper_model

    # Does not overwrite unless forced.
    path.write_text('whisper_model = "medium"\n')
    write_default_config(path)
    assert load_config(path).whisper_model == "medium"
    write_default_config(path, overwrite=True)
    assert load_config(path).whisper_model == Config().whisper_model
