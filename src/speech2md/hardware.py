"""Hardware probing: GPU (via nvidia-smi), RAM, CPU cores."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class HardwareInfo:
    gpu_name: str | None = None
    vram_gb: float | None = None
    ram_gb: float | None = None
    cpu_cores: int = 1


def parse_nvidia_smi(output: str) -> tuple[str, float] | None:
    """Parses 'name, memory_in_mib' from nvidia-smi CSV output; None if unparsable."""
    line = output.strip().splitlines()[0].strip() if output.strip() else ""
    if not line or "," not in line:
        return None
    name, _, mem = line.rpartition(",")
    try:
        return name.strip(), float(mem.strip()) / 1024
    except ValueError:
        return None


def _detect_gpu() -> tuple[str, float] | None:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return parse_nvidia_smi(result.stdout)


def _detect_ram_gb() -> float | None:
    try:
        if sys.platform == "win32":
            import ctypes

            class MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatusEx()
            status.dwLength = ctypes.sizeof(MemoryStatusEx)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return None
            return status.ullTotalPhys / 1024**3
        if sys.platform == "darwin":
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5
            )
            return int(result.stdout.strip()) / 1024**3
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
    except Exception:
        return None


def detect_hardware() -> HardwareInfo:
    gpu = _detect_gpu()
    return HardwareInfo(
        gpu_name=gpu[0] if gpu else None,
        vram_gb=gpu[1] if gpu else None,
        ram_gb=_detect_ram_gb(),
        cpu_cores=os.cpu_count() or 1,
    )
