"""Model loading and transcription on top of faster-whisper."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _register_cuda_dlls() -> None:
    """Makes cuBLAS/cuDNN from the pip packages nvidia-* visible to ctranslate2 on Windows."""
    if sys.platform != "win32":
        return
    site_packages = Path(sys.prefix) / "Lib" / "site-packages"
    for sub in ("cublas", "cudnn"):
        bin_dir = site_packages / "nvidia" / sub / "bin"
        if bin_dir.is_dir():
            os.add_dll_directory(str(bin_dir))
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


_register_cuda_dlls()

from faster_whisper import WhisperModel


def load_model(model_name: str, device: str = "auto") -> tuple[WhisperModel, str]:
    """Loads the model in INT8 on GPU, falling back to CPU when device='auto'."""
    if device in ("auto", "cuda"):
        try:
            model = WhisperModel(model_name, device="cuda", compute_type="int8")
            return model, "GPU (CUDA, INT8)"
        except Exception as exc:
            if device == "cuda":
                raise
            print(f"[!] GPU unavailable ({exc}); falling back to CPU.", file=sys.stderr)
    model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
    return model, "CPU (INT8)"


def transcribe(model: WhisperModel, path: Path, language: str | None, word_timestamps: bool = False):
    """Returns (segments_iterator, info) for an audio file.

    word_timestamps is needed by paragraph grouping (md/txt): Whisper pads segment ends
    across silence, so the end of the last word is the only reliable speech boundary.
    """
    return model.transcribe(
        str(path),
        language=language,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        beam_size=5,
        word_timestamps=word_timestamps,
    )
