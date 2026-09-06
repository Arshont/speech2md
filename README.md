# speech2md

[![CI](https://github.com/Arshont/speech2md/actions/workflows/ci.yml/badge.svg)](https://github.com/Arshont/speech2md/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

**Turn audio into clean Markdown notes — locally, on your GPU, no cloud.**

speech2md transcribes speech (Russian, English, and 90+ other languages) with
[Whisper large-v3](https://huggingface.co/openai/whisper-large-v3) and writes the result as a
readable Markdown document: a title, a metadata line, and text split into paragraphs at natural
speech pauses. Drop the output straight into Obsidian, Notion, or a git repo.

[Читать на русском](README.ru.md)

```
> speech2md interview.mp3

Loading model whisper-large-v3 (first run downloads it)...
Model ready on GPU (CUDA, INT8)

=== interview.mp3 ===
Language: en (p=99%) · Duration: 42:17

So, the first thing I want to ask about is how you got started...
 63%|██████████████████░░░░░░░░░░░░| 1591/2537s [09:12<05:28]
```

## Why not just use whisper-ctranslate2 / whisper.cpp?

| | speech2md | [whisper-ctranslate2](https://github.com/Softcatala/whisper-ctranslate2) | [whisper.cpp](https://github.com/ggerganov/whisper.cpp) |
|---|---|---|---|
| Markdown output with smart paragraphs | ✅ | ❌ (flat txt/srt) | ❌ (flat txt/srt) |
| GPU on Windows without CUDA Toolkit install | ✅ (one `pip install`) | manual | manual build |
| Subtitles (srt/vtt) | ✅ | ✅ | ✅ |
| Realtime mic input, diarization | ❌ (roadmap) | ✅ | partial |

If you need subtitles for a video pipeline, the mature tools above are great. If you want
**notes you can actually read**, that's what speech2md is for.

## Requirements

- Python 3.10+
- ~2 GB disk for the model (downloaded on first run)
- Optional: NVIDIA GPU with 4+ GB VRAM (CUDA 12 driver). Works on CPU without it, just slower.
- No FFmpeg needed — mp3, wav, m4a, mp4, ogg, flac and more are decoded out of the box.

## Install

**Windows (PowerShell):**

```powershell
git clone https://github.com/Arshont/speech2md
cd speech2md
.\install.ps1
```

**Any OS (pip):**

```bash
pip install -e .          # CPU
pip install -e .[cuda]    # NVIDIA GPU (installs cuBLAS/cuDNN wheels, no CUDA Toolkit needed)
```

## Usage

```powershell
speech2md recording.mp3                        # auto-detect language → recording.md
speech2md meeting.m4a --language ru            # force language
speech2md lecture.mp4 --timestamps             # prefix paragraphs with [00:01:23]
speech2md talk.wav --format md,srt             # multiple output formats
speech2md .\records\*.m4a                      # batch: glob patterns
speech2md long.mp3 --model large-v3-turbo      # ~5x faster, slightly lower accuracy
speech2md audio.wav --device cpu               # force CPU
```

On Windows you can also use the wrapper: `.\transcribe.ps1 recording.mp3 -Language ru -Timestamps`.

Output formats: `md` (default), `txt`, `srt`, `vtt`.

## Choosing a model

On first run speech2md probes your hardware (GPU VRAM, RAM, CPU), shows which models fit,
and asks you to confirm the recommended one — press Enter to accept or type another name.
The choice is saved and used from then on. To revisit it:

```powershell
speech2md models            # table of models + what fits this machine
speech2md models --setup    # re-run the interactive chooser
speech2md models --set large-v3-turbo
```

| model | size | VRAM (INT8) | speed vs large-v3 | quality | languages |
|---|---|---|---|---|---|
| [large-v3](https://huggingface.co/Systran/faster-whisper-large-v3) | 1.5B | ~3.1 GB | 1x (baseline) | best | multilingual |
| [large-v3-turbo](https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo) | 0.8B | ~1.8 GB | ~5x faster | near-best | multilingual |
| [distil-large-v3](https://huggingface.co/Systran/faster-distil-whisper-large-v3) | 0.8B | ~1.5 GB | ~6x faster | near-best | **English only** |
| [medium](https://huggingface.co/Systran/faster-whisper-medium) | 0.8B | ~1.0 GB | ~2x faster | good | multilingual |
| [small](https://huggingface.co/Systran/faster-whisper-small) | 0.2B | ~0.5 GB | ~4x faster | fair | multilingual |

*Speed is transcription speed relative to large-v3 on the same hardware: the same file with
large-v3-turbo finishes ~5 times sooner. How fast that is in wall-clock terms depends on your
machine — see [Performance](#performance).*

Rule of thumb: 4+ GB VRAM → `large-v3`; 2.5–4 GB → `large-v3-turbo`; CPU only → `large-v3-turbo`
with 8+ GB RAM, `small` below that. Any other faster-whisper model name or Hugging Face repo id
works with `--model` too.

## Configuration

Defaults live in a JSON file (`%APPDATA%\speech2md\config.json` on Windows,
`~/.config/speech2md/config.json` elsewhere) — created by the first-run dialog. Command-line
flags always win over the config. Supported keys:

```json
{ "model": "large-v3", "language": "auto", "format": "md", "timestamps": false, "device": "auto" }
```

## Example output

```markdown
# interview.mp3

> Language: en · Duration: 42:17 · Model: whisper-large-v3 · 2026-09-06

So, the first thing I want to ask about is how you got started. Back in 2019
we were a three-person team working out of a garage...

**[02:14]** The turning point came when we realized the market had shifted...
```

Paragraphs are split at speech pauses ≥ 1.5 s (or at ~600 characters), so a one-hour
recording becomes a structured document instead of a wall of text.

## Performance

Measured on a GTX 1060 6GB (INT8 quantization, VAD enabled): ~6x realtime on short clips;
expect 1.5–3x realtime on long recordings with `large-v3`, several times faster with
`large-v3-turbo`. On CPU (Ryzen 5 3600) expect well below realtime with `large-v3` —
prefer `distil-large-v3` or `medium` there.

## How it works

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) runs Whisper
  large-v3 quantized to INT8 — ~3 GB VRAM instead of 10+, with negligible accuracy loss.
- Voice-activity detection (Silero VAD) skips silence before it reaches the model.
- On GPU-less machines it falls back to CPU automatically.
- cuBLAS/cuDNN come from pip wheels (`nvidia-cublas-cu12`, `nvidia-cudnn-cu12`), so there is
  no system-wide CUDA Toolkit to install.

## Licenses

speech2md is MIT-licensed. It downloads and runs
[whisper-large-v3](https://huggingface.co/openai/whisper-large-v3) (© OpenAI, Apache 2.0) in the
[CTranslate2 conversion by Systran](https://huggingface.co/Systran/faster-whisper-large-v3) (MIT).

## Roadmap

- [ ] Publish to PyPI
- [ ] Live transcription from microphone
- [ ] Speaker diarization
- [ ] Watch-folder mode
