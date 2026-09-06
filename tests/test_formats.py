from speech2md.formats import (
    fmt_clock,
    fmt_srt_time,
    fmt_vtt_time,
    group_paragraphs,
    render_markdown,
    render_srt,
    render_txt,
    render_vtt,
)

SEGMENTS = [
    {"start": 0.0, "end": 1.2, "text": " Hello there."},
    {"start": 1.4, "end": 3.0, "text": " This is a test."},
    {"start": 6.0, "end": 8.5, "text": " New paragraph after a pause."},
]


def test_fmt_clock():
    assert fmt_clock(0) == "00:00"
    assert fmt_clock(75) == "01:15"
    assert fmt_clock(3671) == "1:01:11"


def test_fmt_srt_vtt_time():
    assert fmt_srt_time(1.5) == "00:00:01,500"
    assert fmt_srt_time(3661.007) == "01:01:01,007"
    assert fmt_vtt_time(1.5) == "00:00:01.500"


def test_group_paragraphs_splits_on_pause():
    paras = group_paragraphs(SEGMENTS, gap=1.5)
    assert len(paras) == 2
    assert paras[0]["text"] == "Hello there. This is a test."
    assert paras[0]["start"] == 0.0
    assert paras[0]["end"] == 3.0
    assert paras[1]["text"] == "New paragraph after a pause."


def test_group_paragraphs_splits_on_length():
    segs = [
        {"start": float(i), "end": i + 0.9, "text": "x" * 100}
        for i in range(10)
    ]
    paras = group_paragraphs(segs, max_chars=250, gap=5.0)
    assert len(paras) > 1
    assert all(len(p["text"]) <= 250 for p in paras)


def test_group_paragraphs_uses_speech_end_over_padded_end():
    # Whisper often stretches segment `end` across silence up to the next segment's start;
    # `speech_end` (last word's end) keeps the real pause visible.
    segs = [
        {"start": 0.0, "end": 9.18, "speech_end": 7.0, "text": "First thought."},
        {"start": 9.18, "end": 14.8, "speech_end": 14.0, "text": "Second thought."},
    ]
    paras = group_paragraphs(segs, gap=1.5)
    assert len(paras) == 2


def test_group_paragraphs_skips_empty():
    segs = [{"start": 0.0, "end": 1.0, "text": "  "}]
    assert group_paragraphs(segs) == []


def test_render_markdown():
    md = render_markdown("audio.mp3", "en", 8.5, "large-v3", SEGMENTS)
    assert md.startswith("# audio.mp3")
    assert "Language: en" in md
    assert "Duration: 00:08" in md
    assert "Hello there. This is a test." in md
    assert "[00:00]" not in md


def test_render_markdown_timestamps():
    md = render_markdown("audio.mp3", "en", 8.5, "large-v3", SEGMENTS, timestamps=True)
    assert "**[00:00]** Hello there." in md
    assert "**[00:06]** New paragraph" in md


def test_render_txt():
    txt = render_txt(SEGMENTS)
    assert txt == "Hello there. This is a test.\n\nNew paragraph after a pause.\n"


def test_render_srt():
    srt = render_srt(SEGMENTS)
    blocks = srt.strip().split("\n\n")
    assert len(blocks) == 3
    assert blocks[0].splitlines() == ["1", "00:00:00,000 --> 00:00:01,200", "Hello there."]


def test_render_vtt():
    vtt = render_vtt(SEGMENTS)
    assert vtt.startswith("WEBVTT\n")
    assert "00:00:01.400 --> 00:00:03.000" in vtt
