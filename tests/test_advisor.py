from speech2md.advisor import MODELS, fits, recommend, render_table
from speech2md.hardware import HardwareInfo, parse_nvidia_smi

GTX_1060 = HardwareInfo(gpu_name="GTX 1060", vram_gb=6.0, ram_gb=32.0, cpu_cores=12)
NO_GPU_BIG_RAM = HardwareInfo(ram_gb=16.0, cpu_cores=8)
NO_GPU_SMALL_RAM = HardwareInfo(ram_gb=4.0, cpu_cores=4)


def test_recommend_by_vram():
    assert recommend(GTX_1060) == "large-v3"
    assert recommend(HardwareInfo(gpu_name="x", vram_gb=4.0, ram_gb=16)) == "large-v3"
    assert recommend(HardwareInfo(gpu_name="x", vram_gb=3.0, ram_gb=16)) == "large-v3-turbo"
    assert recommend(HardwareInfo(gpu_name="x", vram_gb=2.0, ram_gb=16)) == "small"


def test_recommend_cpu():
    assert recommend(NO_GPU_BIG_RAM) == "large-v3-turbo"
    assert recommend(NO_GPU_SMALL_RAM) == "small"
    assert recommend(HardwareInfo()) == "large-v3-turbo"  # unknown RAM → assume enough


def test_tiny_gpu_falls_back_to_cpu_recommendation():
    assert recommend(HardwareInfo(gpu_name="x", vram_gb=1.0, ram_gb=16)) == "large-v3-turbo"


def test_fits_accounts_for_overhead():
    large = next(m for m in MODELS if m.name == "large-v3")
    assert fits(large, GTX_1060)
    assert not fits(large, HardwareInfo(gpu_name="x", vram_gb=3.5, ram_gb=16))


def test_render_table_marks_fit_and_languages():
    table = render_table(HardwareInfo(gpu_name="x", vram_gb=2.5, ram_gb=16))
    assert "English ONLY" in table
    prefixes = ("large", "distil", "medium", "small")
    model_rows = [line for line in table.splitlines() if line.startswith(prefixes)]
    lines = {line.split()[0]: line for line in model_rows}
    assert lines["large-v3"].rstrip().endswith("NO")
    assert lines["small"].rstrip().endswith("yes")


def test_first_run_dialog_enter_picks_recommended(monkeypatch, capsys):
    from speech2md import advisor

    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert advisor.first_run_dialog(GTX_1060) == "large-v3"
    assert "Detected:" in capsys.readouterr().out


def test_first_run_dialog_accepts_typed_name(monkeypatch, capsys):
    from speech2md import advisor

    monkeypatch.setattr("builtins.input", lambda prompt: "  medium  ")
    assert advisor.first_run_dialog(GTX_1060) == "medium"


def test_parse_nvidia_smi():
    assert parse_nvidia_smi("NVIDIA GeForce GTX 1060 6GB, 6144\n") == (
        "NVIDIA GeForce GTX 1060 6GB",
        6.0,
    )
    assert parse_nvidia_smi("") is None
    assert parse_nvidia_smi("garbage without comma") is None
    assert parse_nvidia_smi("Name, not-a-number") is None
