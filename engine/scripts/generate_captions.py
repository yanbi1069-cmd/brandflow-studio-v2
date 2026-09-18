"""
Generate ASS subtitle file from Whisper timestamps.json
Splits long segments into short caption cards (~5-7 words) with prorated timing,
so no text gets truncated and each card stays readable on portrait video.

Usage: python generate_captions.py <timestamps.json> <output.ass>
"""

import sys, json

VIDEO_W, VIDEO_H = 1080, 1920
MAX_WORDS_PER_CARD = 6
MAX_CHARS_PER_CARD = 28  # tránh tràn viền khi dòng chứa từ dài (VD tên thương hiệu tiếng Anh)

def ass_color(hex_color: str, alpha: str = "00") -> str:
    value = str(hex_color or "#FFFFFF").lstrip("#")
    if len(value) != 6:
        value = "FFFFFF"
    return f"&H{alpha}{value[4:6]}{value[2:4]}{value[0:2]}"


def caption_profile(style_id: str, accent: str) -> dict:
    profiles = {
        "editorial-proof": {"font": "Montserrat SemiBold", "size": 62, "border": 3, "shadow": 1, "margin": 240, "style": 1},
        "clean-expert": {"font": "Arial", "size": 54, "border": 2, "shadow": 0, "margin": 250, "style": 1},
        "warm-story": {"font": "Arial", "size": 55, "border": 1, "shadow": 0, "margin": 230, "style": 3},
        "luxury-minimal": {"font": "Georgia", "size": 52, "border": 2, "shadow": 1, "margin": 250, "style": 1},
        "bold-social": {"font": "Arial", "size": 72, "border": 5, "shadow": 2, "margin": 205, "style": 1},
        "tiktok-creator": {"font": "Arial", "size": 74, "border": 6, "shadow": 1, "margin": 195, "style": 1},
        "screen-demo": {"font": "Arial", "size": 48, "border": 2, "shadow": 0, "margin": 190, "style": 3},
        "data-kinetic": {"font": "Montserrat ExtraBold", "size": 66, "border": 3, "shadow": 1, "margin": 225, "style": 1},
        "documentary-reveal": {"font": "Georgia", "size": 54, "border": 2, "shadow": 1, "margin": 235, "style": 3},
        "maximalist-type": {"font": "Arial", "size": 76, "border": 5, "shadow": 2, "margin": 200, "style": 1},
        "shadow-cut": {"font": "Arial", "size": 60, "border": 4, "shadow": 2, "margin": 225, "style": 1},
    }
    profile = profiles.get(style_id, {"font": "Arial", "size": 60, "border": 3, "shadow": 1, "margin": 235, "style": 1})
    return {**profile, "accent": accent}


def ass_header(style_id: str, accent: str) -> str:
    profile = caption_profile(style_id, accent)
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {VIDEO_W}
PlayResY: {VIDEO_H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{profile['font']},{profile['size']},&H00FFFFFF,{ass_color(accent)},&H00000000,&H99000000,1,0,0,0,100,100,0,0,{profile['style']},{profile['border']},{profile['shadow']},2,45,45,{profile['margin']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    cs = int(round((s - int(s)) * 100))
    return f"{h}:{m:02d}:{int(s):02d}.{cs:02d}"


def chunk_words(text: str, n: int):
    """Nhóm từ theo cả số từ tối đa (n) lẫn tổng ký tự tối đa (MAX_CHARS_PER_CARD),
    chặn theo điều kiện nào đạt trước — tránh dòng tràn viền khi có từ dài (VD tên
    thương hiệu tiếng Anh) làm dòng vượt bề rộng khung hình dù số từ vẫn <= n."""
    words = text.strip().split()
    chunk, chars = [], 0
    for w in words:
        added = len(w) + (1 if chunk else 0)
        if chunk and (len(chunk) >= n or chars + added > MAX_CHARS_PER_CARD):
            yield chunk
            chunk, chars = [], 0
            added = len(w)
        chunk.append(w)
        chars += added
    if chunk:
        yield chunk


def generate_ass(timestamps_file: str, output_file: str, style_id: str = "editorial-proof", accent: str = "#B6FF36"):
    with open(timestamps_file, encoding="utf-8") as f:
        segments = json.load(f)

    lines = [ass_header(style_id, accent)]
    card_count = 0

    for seg in segments:
        seg_start, seg_end = seg["start"], seg["end"]
        seg_dur = seg_end - seg_start
        text = seg["text"].strip()
        word_chunks = list(chunk_words(text, MAX_WORDS_PER_CARD))
        total_words = sum(len(c) for c in word_chunks)

        t = seg_start
        for chunk in word_chunks:
            chunk_text = " ".join(chunk)
            # Prorate duration by word count share of this chunk
            share = len(chunk) / total_words if total_words else 1 / len(word_chunks)
            dur = seg_dur * share
            start = fmt_time(t)
            end = fmt_time(min(t + dur, seg_end))
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{chunk_text}")
            t += dur
            card_count += 1

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Generated {card_count} caption cards from {len(segments)} segments -> {output_file}")


if __name__ == "__main__":
    ts_file  = sys.argv[1] if len(sys.argv) > 1 else "timestamps.json"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "captions.ass"
    style = sys.argv[3] if len(sys.argv) > 3 else "editorial-proof"
    accent = sys.argv[4] if len(sys.argv) > 4 else "#B6FF36"
    generate_ass(ts_file, out_file, style, accent)
