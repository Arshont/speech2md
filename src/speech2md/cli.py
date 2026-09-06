"""Command-line interface for speech2md."""

from __future__ import annotations

import argparse
import glob
import sys
import time
from pathlib import Path

from tqdm import tqdm

from speech2md import __version__
from speech2md.advisor import describe_hardware, first_run_dialog, recommend, render_table
from speech2md.config import config_path, load_config, save_config
from speech2md.formats import (
    KNOWN_FORMATS,
    fmt_clock,
    render_markdown,
    render_srt,
    render_txt,
    render_vtt,
)
from speech2md.hardware import detect_hardware


def _configure_console() -> None:
    """Windows consoles default to a legacy codepage; force UTF-8 so Cyrillic survives."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def expand_inputs(patterns: list[str]) -> list[Path]:
    """Expands glob patterns (PowerShell does not expand them for us)."""
    files: list[Path] = []
    for pattern in patterns:
        if any(ch in pattern for ch in "*?["):
            files.extend(Path(m) for m in sorted(glob.glob(pattern)))
        else:
            files.append(Path(pattern))
    return files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="speech2md",
        description="Local speech-to-text that turns audio into clean Markdown notes (Whisper large-v3).",
        epilog="Run 'speech2md models' to see available models and what fits your hardware.",
    )
    parser.add_argument(
        "inputs", nargs="+", help="audio/video files or glob patterns (mp3, wav, m4a, mp4, ...)"
    )
    parser.add_argument(
        "--language", default=None, help="language code (ru, en, ...) or 'auto' (default)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Whisper model (see 'speech2md models'; default: saved choice or hardware-based)",
    )
    parser.add_argument(
        "--format",
        default=None,
        dest="formats",
        help="output format(s), comma-separated: md,txt,srt,vtt (default: md)",
    )
    parser.add_argument(
        "--device", default=None, choices=["auto", "cuda", "cpu"], help="compute device (default: auto)"
    )
    parser.add_argument(
        "--timestamps",
        action="store_true",
        default=None,
        help="prefix Markdown paragraphs and console output with timestamps",
    )
    parser.add_argument(
        "--output", default=None, help="output file path (single input file and single format only)"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def render(
    fmt: str,
    source: Path,
    language: str,
    duration: float,
    model_name: str,
    segments: list[dict],
    timestamps: bool,
) -> str:
    if fmt == "md":
        return render_markdown(source.name, language, duration, model_name, segments, timestamps)
    if fmt == "txt":
        return render_txt(segments)
    if fmt == "srt":
        return render_srt(segments)
    return render_vtt(segments)


def transcribe_file(model, path: Path, model_name: str, args: argparse.Namespace) -> None:
    from speech2md.engine import transcribe

    print(f"\n=== {path.name} ===")
    language = None if args.language == "auto" else args.language
    need_words = any(fmt in ("md", "txt") for fmt in args.format_list)
    segments_iter, info = transcribe(model, path, language, word_timestamps=need_words)
    print(
        f"Language: {info.language} (p={info.language_probability:.0%}) · "
        f"Duration: {fmt_clock(info.duration)}\n"
    )

    started = time.monotonic()
    segments: list[dict] = []
    bar = tqdm(
        total=round(info.duration, 1),
        unit="s",
        bar_format="{percentage:3.0f}%|{bar:30}| {n:.0f}/{total:.0f}s [{elapsed}<{remaining}]",
        leave=False,
    )
    for seg in segments_iter:
        record = {"start": seg.start, "end": seg.end, "text": seg.text}
        if seg.words:
            record["speech_end"] = seg.words[-1].end
        segments.append(record)
        prefix = f"[{fmt_clock(seg.start)}] " if args.timestamps else ""
        tqdm.write(f"{prefix}{seg.text.strip()}")
        bar.update(max(0.0, min(seg.end, info.duration) - bar.n))
    bar.close()
    elapsed = time.monotonic() - started

    for fmt in args.format_list:
        out_path = Path(args.output) if args.output else path.with_suffix(f".{fmt}")
        content = render(fmt, path, info.language, info.duration, model_name, segments, args.timestamps)
        out_path.write_text(content, encoding="utf-8")
        print(f"→ {out_path}")
    speed = info.duration / elapsed if elapsed > 0 else 0
    print(f"Done in {fmt_clock(elapsed)} ({speed:.1f}x realtime)")


def resolve_model(cli_model: str | None, config: dict) -> str:
    """Priority: --model flag > config > first-run dialog (TTY) / recommendation."""
    if cli_model:
        return cli_model
    if config.get("model"):
        return config["model"]
    hw = detect_hardware()
    if _interactive():
        chosen = first_run_dialog(hw)
        path = save_config({"model": chosen})
        print(f"Saved as default → {path}")
        return chosen
    chosen = recommend(hw)
    print(f"Using recommended model '{chosen}' (run 'speech2md models --setup' to choose).")
    return chosen


def models_command(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="speech2md models", description="Show available models and what fits this machine."
    )
    parser.add_argument("--setup", action="store_true", help="re-run the interactive model chooser")
    parser.add_argument("--set", dest="set_model", metavar="NAME", help="save NAME as the default model")
    args = parser.parse_args(argv)

    if args.set_model:
        path = save_config({"model": args.set_model})
        print(f"Default model set to '{args.set_model}' → {path}")
        return 0

    hw = detect_hardware()
    if args.setup:
        if not _interactive():
            print("--setup requires an interactive terminal", file=sys.stderr)
            return 1
        chosen = first_run_dialog(hw)
        path = save_config({"model": chosen})
        print(f"Default model set to '{chosen}' → {path}")
        return 0

    current = load_config().get("model")
    print(describe_hardware(hw))
    print()
    print(render_table(hw))
    print()
    print(f"Recommended for this machine: {recommend(hw)}")
    print(f"Current default: {current or '(not set — first run will ask)'}")
    print(f"Config file: {config_path()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    _configure_console()
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    if argv[:1] == ["models"]:
        return models_command(argv[1:])

    args = build_parser().parse_args(argv)
    config = load_config()
    args.language = args.language or config.get("language", "auto")
    args.device = args.device or config.get("device", "auto")
    if args.timestamps is None:
        args.timestamps = bool(config.get("timestamps", False))

    formats = args.formats or config.get("format", "md")
    args.format_list = [f.strip().lower() for f in formats.split(",") if f.strip()]
    unknown = [f for f in args.format_list if f not in KNOWN_FORMATS]
    if unknown:
        print(
            f"Unknown format(s): {', '.join(unknown)}. Supported: {', '.join(KNOWN_FORMATS)}",
            file=sys.stderr,
        )
        return 1

    files = expand_inputs(args.inputs)
    if not files:
        print("No input files matched.", file=sys.stderr)
        return 1
    missing = [p for p in files if not p.is_file()]
    if missing:
        for p in missing:
            print(f"File not found: {p}", file=sys.stderr)
        return 1
    if args.output and (len(files) > 1 or len(args.format_list) > 1):
        print("--output requires a single input file and a single format", file=sys.stderr)
        return 1

    model_name = resolve_model(args.model, config)

    from speech2md.engine import load_model

    print(f"Loading model whisper-{model_name} (first run downloads it)...")
    model, device = load_model(model_name, args.device)
    print(f"Model ready on {device}")

    for path in files:
        transcribe_file(model, path, model_name, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
