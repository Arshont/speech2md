from speech2md.advisor import MODELS, fit_status, recommend, render_table
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


def test_fit_status_accounts_for_overhead():
    large = next(m for m in MODELS if m.name == "large-v3")
    assert fit_status(large, GTX_1060) == "yes"
    assert fit_status(large, HardwareInfo(gpu_name="x", vram_gb=3.5, ram_gb=16)) == "NO (VRAM)"


def test_fit_status_low_ram_cpu():
    large = next(m for m in MODELS if m.name == "large-v3")
    assert fit_status(large, HardwareInfo(ram_gb=4.0, cpu_cores=4)) == "NO (RAM)"


def _model_rows(table: str) -> dict[str, str]:
    prefixes = ("large", "distil", "medium", "small")
    return {line.split()[0]: line for line in table.splitlines() if line.startswith(prefixes)}


def test_render_table_marks_fit_and_languages():
    table = render_table(HardwareInfo(gpu_name="x", vram_gb=2.5, ram_gb=16))
    assert "English ONLY" in table
    lines = _model_rows(table)
    assert "NO (VRAM)" in lines["large-v3"]
    assert "yes" in lines["small"]


def test_render_table_cpu_only_laptop():
    # A GPU-less laptop: everything fits RAM-wise, but heavy models must not show a bare 'yes'
    # while the recommendation points at turbo (user-reported inconsistency).
    table = render_table(NO_GPU_BIG_RAM)
    lines = _model_rows(table)
    assert "slow on CPU" in lines["large-v3"]
    assert "slow on CPU" in lines["medium"]
    assert "yes" in lines["large-v3-turbo"]
    assert lines["large-v3-turbo"].endswith("← recommended")


def test_render_table_marks_recommended_on_gpu():
    lines = _model_rows(render_table(GTX_1060))
    assert lines["large-v3"].endswith("← recommended")
    assert not lines["small"].endswith("← recommended")


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
