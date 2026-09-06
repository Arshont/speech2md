"""Model catalog, hardware-based recommendation, and the first-run dialog."""

from __future__ import annotations

from dataclasses import dataclass

from speech2md.hardware import HardwareInfo


@dataclass
class ModelSpec:
    name: str
    params: str
    vram_gb: float  # VRAM needed for INT8 inference (excluding CUDA context overhead)
    speed: str  # relative to large-v3
    quality: str
    languages: str
    cpu_ok: bool  # fast enough to be practical on CPU-only machines
    url: str


MODELS = [
    ModelSpec(
        "large-v3", "1.5B", 3.1, "1x (baseline)", "best", "multilingual", False,
        "https://huggingface.co/Systran/faster-whisper-large-v3",
    ),
    ModelSpec(
        "large-v3-turbo", "0.8B", 1.8, "~5x faster", "near-best", "multilingual", True,
        "https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo",
    ),
    ModelSpec(
        "distil-large-v3", "0.8B", 1.5, "~6x faster", "near-best", "English ONLY", True,
        "https://huggingface.co/Systran/faster-distil-whisper-large-v3",
    ),
    ModelSpec(
        "medium", "0.8B", 1.0, "~2x faster", "good", "multilingual", False,
        "https://huggingface.co/Systran/faster-whisper-medium",
    ),
    ModelSpec(
        "small", "0.2B", 0.5, "~4x faster", "fair", "multilingual", True,
        "https://huggingface.co/Systran/faster-whisper-small",
    ),
]

# Rough CUDA context + activations overhead on top of the weights.
VRAM_OVERHEAD_GB = 0.8


def fit_status(spec: ModelSpec, hw: HardwareInfo) -> str:
    """How this model suits this machine: 'yes', 'NO (VRAM)', 'NO (RAM)', or 'slow on CPU'."""
    if hw.vram_gb is not None:
        return "yes" if hw.vram_gb >= spec.vram_gb + VRAM_OVERHEAD_GB else "NO (VRAM)"
    if hw.ram_gb is not None and hw.ram_gb < spec.vram_gb + 2:
        return "NO (RAM)"
    return "yes" if spec.cpu_ok else "slow on CPU"


def recommend(hw: HardwareInfo) -> str:
    """Picks the best model this machine can run comfortably."""
    if hw.vram_gb is not None:
        if hw.vram_gb >= 4:
            return "large-v3"
        if hw.vram_gb >= 2.5:
            return "large-v3-turbo"
        if hw.vram_gb >= 1.5:
            return "small"
    if hw.ram_gb is None or hw.ram_gb >= 8:
        return "large-v3-turbo"
    return "small"


def describe_hardware(hw: HardwareInfo) -> str:
    gpu = f"{hw.gpu_name} ({hw.vram_gb:.0f} GB VRAM)" if hw.gpu_name else "no NVIDIA GPU (CPU mode)"
    ram = f"{hw.ram_gb:.0f} GB RAM" if hw.ram_gb else "RAM unknown"
    return f"Detected: {gpu} · {ram} · {hw.cpu_cores} CPU cores"


def render_table(hw: HardwareInfo) -> str:
    recommended = recommend(hw)
    header = (
        f"{'model':<17} {'size':<5} {'VRAM':<7} {'speed':<14} {'quality':<10} {'languages':<13} fits"
    )
    lines = [header, "-" * (len(header) + 12)]
    for spec in MODELS:
        row = (
            f"{spec.name:<17} {spec.params:<5} {spec.vram_gb:.1f} GB  {spec.speed:<14} "
            f"{spec.quality:<10} {spec.languages:<13} {fit_status(spec, hw):<12}"
        )
        if spec.name == recommended:
            row += "← recommended"
        lines.append(row.rstrip())
    lines.append("")
    lines.append("speed: transcription speed relative to large-v3 on the same hardware")
    lines.append("Details: https://huggingface.co/collections/Systran/faster-whisper")
    return "\n".join(lines)


def first_run_dialog(hw: HardwareInfo) -> str:
    """Interactive model choice; returns the chosen model name."""
    recommended = recommend(hw)
    print("First run: let's pick a Whisper model for this machine.\n")
    print(describe_hardware(hw))
    print()
    print(render_table(hw))
    print()
    answer = input(f"Press Enter to use '{recommended}' (recommended), or type a model name: ").strip()
    return answer or recommended
