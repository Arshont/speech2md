from pathlib import Path

import pytest

from speech2md import cli
from speech2md.cli import build_parser, expand_inputs, main
from speech2md.hardware import HardwareInfo

GTX_1060 = HardwareInfo(gpu_name="GTX 1060", vram_gb=6.0, ram_gb=32.0, cpu_cores=12)


@pytest.fixture(autouse=True)
def no_user_config(monkeypatch):
    """Tests must not read or write the developer's real config file."""
    monkeypatch.setattr(cli, "load_config", lambda: {})
    monkeypatch.setattr(cli, "save_config", lambda updates: Path("unused/config.json"))


def test_parser_defaults_are_unset():
    args = build_parser().parse_args(["audio.mp3"])
    assert args.language is None
    assert args.model is None
    assert args.formats is None
    assert args.device is None
    assert args.timestamps is None


def test_expand_inputs_glob(tmp_path: Path):
    (tmp_path / "a.wav").touch()
    (tmp_path / "b.wav").touch()
    files = expand_inputs([str(tmp_path / "*.wav")])
    assert [f.name for f in files] == ["a.wav", "b.wav"]


def test_expand_inputs_plain_path():
    assert expand_inputs(["some file.mp3"]) == [Path("some file.mp3")]


def test_main_rejects_unknown_format(capsys):
    assert main(["audio.mp3", "--format", "docx"]) == 1
    assert "Unknown format" in capsys.readouterr().err


def test_main_rejects_missing_file(capsys):
    assert main(["no-such-file.mp3"]) == 1
    assert "File not found" in capsys.readouterr().err


def test_main_rejects_output_with_multiple_formats(tmp_path: Path, capsys):
    audio = tmp_path / "a.wav"
    audio.touch()
    assert main([str(audio), "--format", "md,srt", "--output", "out.md"]) == 1
    assert "--output requires" in capsys.readouterr().err


def test_resolve_model_flag_beats_config():
    assert cli.resolve_model("small", {"model": "medium"}) == "small"


def test_resolve_model_config_beats_recommendation():
    assert cli.resolve_model(None, {"model": "medium"}) == "medium"


def test_resolve_model_non_tty_uses_recommendation(monkeypatch, capsys):
    monkeypatch.setattr(cli, "_interactive", lambda: False)
    monkeypatch.setattr(cli, "detect_hardware", lambda: GTX_1060)
    assert cli.resolve_model(None, {}) == "large-v3"
    assert "recommended" in capsys.readouterr().out


def test_resolve_model_dialog_saves_choice(monkeypatch, tmp_path):
    saved = {}
    monkeypatch.setattr(cli, "_interactive", lambda: True)
    monkeypatch.setattr(cli, "detect_hardware", lambda: GTX_1060)
    monkeypatch.setattr(cli, "first_run_dialog", lambda hw: "medium")
    monkeypatch.setattr(cli, "save_config", lambda u: saved.update(u) or tmp_path / "config.json")
    assert cli.resolve_model(None, {}) == "medium"
    assert saved == {"model": "medium"}


def test_models_command_shows_table_and_recommendation(monkeypatch, capsys):
    monkeypatch.setattr(cli, "detect_hardware", lambda: GTX_1060)
    assert main(["models"]) == 0
    out = capsys.readouterr().out
    assert "large-v3-turbo" in out
    assert "Recommended for this machine: large-v3" in out
    assert "Current default: (not set" in out


def test_models_set_saves_model(monkeypatch, capsys):
    saved = {}
    monkeypatch.setattr(cli, "save_config", lambda u: saved.update(u) or Path("x/config.json"))
    assert main(["models", "--set", "small"]) == 0
    assert saved == {"model": "small"}


def test_config_defaults_apply_when_flags_missing(monkeypatch, tmp_path, capsys):
    audio = tmp_path / "a.wav"
    audio.touch()
    monkeypatch.setattr(cli, "load_config", lambda: {"format": "docx"})
    assert main([str(audio)]) == 1  # config format reaches validation → proves it was applied
    assert "Unknown format" in capsys.readouterr().err
