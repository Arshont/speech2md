"""Rendering transcription results into output formats: md, txt, srt, vtt."""

from __future__ import annotations

from datetime import date

Segment = dict  # {"start": float, "end": float, "text": str}


def fmt_clock(seconds: float) -> str:
    """Human-readable time: mm:ss, or h:mm:ss for long audio."""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def _fmt_ms_time(seconds: float, ms_sep: str) -> str:
    ms = round(seconds * 1000)
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{ms_sep}{ms:03d}"


def fmt_srt_time(seconds: float) -> str:
    return _fmt_ms_time(seconds, ",")


def fmt_vtt_time(seconds: float) -> str:
    return _fmt_ms_time(seconds, ".")


def group_paragraphs(segments: list[Segment], max_chars: int = 600, gap: float = 1.5) -> list[Segment]:
    """Groups segments into paragraphs: a new one starts on a pause >= gap seconds
    or when the current paragraph exceeds max_chars.

    Pauses are measured against `speech_end` (end of the last spoken word) when present:
    Whisper pads a segment's `end` across silence up to the next segment, hiding the pause.
    """
    paragraphs: list[Segment] = []
    current: Segment | None = None
    last_speech_end = 0.0
    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue
        if (
            current is None
            or seg["start"] - last_speech_end >= gap
            or len(current["text"]) + len(text) > max_chars
        ):
            if current:
                paragraphs.append(current)
            current = {"start": seg["start"], "end": seg["end"], "text": text}
        else:
            current["text"] += " " + text
            current["end"] = seg["end"]
        last_speech_end = seg.get("speech_end", seg["end"])
    if current:
        paragraphs.append(current)
    return paragraphs


def render_markdown(
    source_name: str,
    language: str,
    duration: float,
    model_name: str,
    segments: list[Segment],
    timestamps: bool = False,
) -> str:
    meta = (
        f"> Language: {language} · Duration: {fmt_clock(duration)} · "
        f"Model: whisper-{model_name} · {date.today().isoformat()}"
    )
    lines = [f"# {source_name}", "", meta, ""]
    for para in group_paragraphs(segments):
        if timestamps:
            lines.append(f"**[{fmt_clock(para['start'])}]** {para['text']}")
        else:
            lines.append(para["text"])
        lines.append("")
    return "\n".join(lines)


def render_txt(segments: list[Segment]) -> str:
    return "\n\n".join(p["text"] for p in group_paragraphs(segments)) + "\n"


def render_srt(segments: list[Segment]) -> str:
    lines: list[str] = []
    for i, seg in enumerate(segments, 1):
        timing = f"{fmt_srt_time(seg['start'])} --> {fmt_srt_time(seg['end'])}"
        lines += [str(i), timing, seg["text"].strip(), ""]
    return "\n".join(lines)


def render_vtt(segments: list[Segment]) -> str:
    lines: list[str] = ["WEBVTT", ""]
    for seg in segments:
        lines += [f"{fmt_vtt_time(seg['start'])} --> {fmt_vtt_time(seg['end'])}", seg["text"].strip(), ""]
    return "\n".join(lines)


KNOWN_FORMATS = ("md", "txt", "srt", "vtt")
