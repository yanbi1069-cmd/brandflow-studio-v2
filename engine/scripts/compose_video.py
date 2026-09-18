"""
Compose final video: avatar + B-roll slots + big text overlays + captions (ASS) + footer text.

B-roll source resolution per slot (in priority order, depends on slot "type"):
  type="chart"  (default): chartanimator/<slot>.mp4 (animated) -> <slot>.png (mplfinance fallback)
  type="pexels":            pexels/<slot>.mp4 (downloaded stock clip)
  type="pixabay":           pixabay/<slot>.mp4 (downloaded stock clip)
  type="stock":             pexels/<slot>.mp4 -> pixabay/<slot>.mp4

Usage:
  python compose_video.py <avatar.mp4> <broll_slots.json> <chart_dir> <captions.ass> <footer_text> <output.mp4> [text_overlays.json] [edit_plan.json]
"""

import sys, os, json, subprocess, shutil

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

FPS, W, H = 25, 1080, 1920

OVERLAY_COLORS = {
    "red":    "0xE53935",
    "yellow": "0xFDD835",
    "green":  "0x43A047",
    "white":  "0xFFFFFF",
}


def ffprobe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return float(out.stdout.strip())


def find_broll_source(slot_name: str, chart_dir: str, slot_type: str = "chart") -> str:
    if slot_type in {"pexels", "pixabay", "stock"}:
        providers = [slot_type] if slot_type != "stock" else ["pexels", "pixabay"]
        for provider in providers:
            stock_path = os.path.join(chart_dir, provider, f"{slot_name}.mp4")
            if os.path.exists(stock_path):
                return stock_path
        raise FileNotFoundError(f"No stock clip found for slot '{slot_name}' in providers: {', '.join(providers)}")

    mp4_path = os.path.join(chart_dir, "chartanimator", f"{slot_name}.mp4")
    png_path = os.path.join(chart_dir, f"{slot_name}.png")
    if os.path.exists(mp4_path):
        return mp4_path
    if os.path.exists(png_path):
        return png_path
    raise FileNotFoundError(f"No B-roll source found for slot '{slot_name}' in {chart_dir}")


def style_grade_filter(style_id: str) -> str:
    """Apply the selected art direction to photographic footage."""
    grades = {
        "editorial-proof": "eq=contrast=1.08:saturation=0.92:brightness=-0.015",
        "clean-expert": "eq=contrast=0.96:saturation=0.82:brightness=0.025",
        "warm-story": "eq=contrast=0.98:saturation=1.10:brightness=0.025",
        "luxury-minimal": "eq=contrast=1.14:saturation=0.72:brightness=-0.025",
        "bold-social": "eq=contrast=1.15:saturation=1.24:brightness=0.005",
        "tiktok-creator": "eq=contrast=1.10:saturation=1.18:brightness=0.01",
        "screen-demo": "eq=contrast=1.05:saturation=0.88:brightness=0.01",
        "data-kinetic": "eq=contrast=1.12:saturation=0.86:brightness=-0.02",
        "visual-metaphor": "eq=contrast=1.04:saturation=1.04:brightness=0.005",
        "documentary-reveal": "eq=contrast=1.18:saturation=0.62:brightness=-0.035",
        "swiss-pulse": "eq=contrast=1.12:saturation=0.82:brightness=0.015",
        "velvet-standard": "eq=contrast=1.16:saturation=0.66:brightness=-0.035",
        "deconstructed": "eq=contrast=1.24:saturation=0.72:brightness=-0.035",
        "maximalist-type": "eq=contrast=1.18:saturation=1.30:brightness=0.005",
        "data-drift": "eq=contrast=1.14:saturation=1.12:brightness=-0.03",
        "soft-signal": "eq=contrast=0.94:saturation=0.92:brightness=0.04",
        "folk-frequency": "eq=contrast=1.08:saturation=1.28:brightness=0.015",
        "shadow-cut": "eq=contrast=1.30:saturation=0.42:brightness=-0.07",
    }
    return grades.get(style_id, grades["editorial-proof"])


def normalize_broll_clip(source_path: str, target_duration: float, output_path: str, style_id: str = "editorial-proof", apply_grade: bool = False):
    """Normalize any PNG or MP4 source into a 720x1280/25fps clip of exact target_duration."""
    ext = os.path.splitext(source_path)[1].lower()

    visual_filters = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}"
    if apply_grade:
        visual_filters += "," + style_grade_filter(style_id)

    if ext in (".png", ".jpg", ".jpeg"):
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-t", f"{target_duration}", "-i", source_path,
            "-vf", visual_filters,
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", output_path
        ]
    elif ext == ".mp4":
        src_dur = ffprobe_duration(source_path)
        if src_dur >= target_duration:
            cmd = [
                "ffmpeg", "-y", "-i", source_path, "-t", f"{target_duration}",
                "-vf", visual_filters,
                "-an", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", output_path
            ]
        else:
            pad = target_duration - src_dur
            cmd = [
                "ffmpeg", "-y", "-i", source_path,
                "-vf", f"{visual_filters},tpad=stop_mode=clone:stop_duration={pad}",
                "-t", f"{target_duration}",
                "-an", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", output_path
            ]
    else:
        raise ValueError(f"Unsupported B-roll source extension: {ext}")

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg normalize failed for {source_path}:\n{result.stderr[-1500:]}")


def escape_drawtext(text: str) -> str:
    """Escape text for ffmpeg drawtext filter (colon, quote, backslash).
    NOTE: '%' is NOT escaped here - drawtext is used with expansion=none
    (see build_text_overlay_filters), which lets '%' pass through literally.
    Escaping it as \\% causes a "Stray %" parse error that silently drops
    the whole filter (confirmed via isolated ffmpeg test)."""
    # A backslash-escaped ASCII apostrophe can still terminate FFmpeg's
    # single-quoted filter value on Windows. The typographic apostrophe is
    # visually equivalent and does not alter filtergraph parsing.
    return text.replace("'", "’").replace("\\", "\\\\").replace(":", "\\:")


def wrap_overlay_text(text: str, max_chars_per_line: int = 16) -> str:
    """Wrap every logical line so manual line breaks cannot overflow the frame."""
    wrapped_lines = []
    for source_line in text.splitlines() or [text]:
        words = source_line.split()
        current, current_len = [], 0
        for word in words:
            add_len = len(word) + (1 if current else 0)
            if current and current_len + add_len > max_chars_per_line:
                wrapped_lines.append(" ".join(current))
                current, current_len = [word], len(word)
            else:
                current.append(word)
                current_len += add_len
        if current:
            wrapped_lines.append(" ".join(current))
    return "\n".join(wrapped_lines)


FONT_BOLD = "C\\:/Windows/Fonts/Montserrat-ExtraBold.ttf"
FONT_SEMI = "C\\:/Windows/Fonts/Montserrat-SemiBold.ttf"


def build_text_overlay_filters(text_overlays: list[dict], prev_label: str, style: dict | None = None, settings: dict | None = None) -> tuple[list[str], str]:
    """Finance-editorial overlay: small accent kicker + bold readable headline.

    The renderer keeps the reference pack's top-left hierarchy while allowing
    safe, manifest-controlled colors, sizing, alignment and position.
    """
    parts = []
    style = style or {}
    settings = settings or {}
    palette = style.get("palette") or []
    def ff_color(value: str, fallback: str) -> str:
        candidate = str(value or "").strip().lstrip("#")
        return "0x" + candidate if len(candidate) == 6 and all(char in "0123456789abcdefABCDEF" for char in candidate) else fallback
    accent = ff_color(settings.get("accent_color"), "0x" + str(palette[1]).lstrip("#") if len(palette) > 1 else OVERLAY_COLORS["yellow"])
    text_color = ff_color(settings.get("text_color"), "0xF4F7EF")
    background = ff_color(settings.get("background_color"), "0x060B16")
    font_size = max(42, min(72, int(settings.get("font_size") or 54)))
    max_chars = max(12, min(34, int(settings.get("max_chars_per_line") or 24)))
    band_alpha = max(.2, min(.95, float(settings.get("background_opacity") or .72)))
    position = settings.get("position") if settings.get("position") in {"top", "middle", "lower"} else "top"
    align = settings.get("align") if settings.get("align") in {"left", "center", "right"} else "left"
    uppercase = bool(settings.get("uppercase", True))
    accent_stripe = bool(settings.get("accent_stripe", False))
    for i, ov in enumerate(text_overlays):
        item_font_size = max(42, min(72, int(ov.get("font_size") or font_size)))
        item_position = ov.get("position") if ov.get("position") in {"top", "middle", "lower"} else position
        headline = str(ov.get("text") or "").upper() if uppercase else str(ov.get("text") or "")
        kicker_raw = str(ov.get("kicker") or settings.get("kicker") or "").upper()
        raw = wrap_overlay_text(headline, max_chars)
        text = escape_drawtext(raw)
        kicker = escape_drawtext(kicker_raw)
        enable = f"between(t,{ov['start']},{ov['end']})"
        line_count = raw.count("\n") + 1
        band_h = 104 + line_count * (item_font_size + 16)
        band_y = 78 if item_position == "top" else ((H - band_h) // 2 if item_position == "middle" else min(H - band_h - 330, int(H * .6)))
        margin_x = 74
        text_x = str(margin_x) if align == "left" else ("(w-text_w)/2" if align == "center" else f"w-text_w-{margin_x}")
        band_label = f"bnd{i+1}"
        carrier_label = band_label
        kicker_label = f"kck{i+1}"
        out_label = f"ovl{i+1}"
        parts.append(
            f"[{prev_label}]drawbox=x=0:y={band_y}:w=iw:h={band_h}:"
            f"color={background}@{band_alpha:.2f}:thickness=fill:enable='{enable}'[{band_label}]"
        )
        if accent_stripe:
            stripe_label = f"stp{i+1}"
            parts.append(f"[{band_label}]drawbox=x=0:y={band_y}:w=12:h={band_h}:color={accent}@1.0:thickness=fill:enable='{enable}'[{stripe_label}]")
            carrier_label = stripe_label
        if kicker:
            parts.append(
                f"[{carrier_label}]drawtext=text='{kicker}':fontfile='{FONT_SEMI}':fontsize=30:fontcolor={accent}:"
                f"expansion=none:x={text_x}:y={band_y}+28:enable='{enable}'[{kicker_label}]"
            )
            carrier_label = kicker_label
        parts.append(
            f"[{carrier_label}]drawtext=text='{text}':fontfile='{FONT_BOLD}':fontsize={item_font_size}:fontcolor={text_color}:"
            f"expansion=none:borderw=3:bordercolor=black@0.9:shadowcolor=black@0.6:shadowx=2:shadowy=2:"
            f"x={text_x}:y={band_y}+76:line_spacing=14:"
            f"enable='{enable}'[{out_label}]"
        )
        prev_label = out_label
    return parts, prev_label


def compose(avatar_path: str, slots: list[dict], chart_dir: str,
            captions_ass: str, footer_text: str, output_path: str,
            text_overlays: list[dict] | None = None, edit_plan: dict | None = None,
            overlay_settings: dict | None = None):
    # Use absolute paths throughout - subprocess cwd is changed at render time
    # (needed so the subtitles filter can use a bare relative filename).
    avatar_path = os.path.abspath(avatar_path)
    chart_dir = os.path.abspath(chart_dir)
    captions_ass = os.path.abspath(captions_ass)
    output_path = os.path.abspath(output_path)

    tmp_dir = os.path.join(os.path.dirname(output_path), "_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    style_id = str(((edit_plan or {}).get("style") or {}).get("id") or "editorial-proof")
    print(f"[1] Normalizing {len(slots)} B-roll slots with style '{style_id}'...")
    chart_clips = []
    for i, slot in enumerate(slots):
        source = find_broll_source(slot["name"], chart_dir, slot.get("type", "chart"))
        dur = slot["end"] - slot["start"]
        clip_path = os.path.join(tmp_dir, f"c{i+1}.mp4")
        normalize_broll_clip(source, dur, clip_path, style_id, slot.get("type") in {"pexels", "pixabay", "stock"})
        chart_clips.append(clip_path)
        if "pexels" in source:
            kind = "Pexels stock"
        elif "pixabay" in source:
            kind = "Pixabay stock"
        elif "chartanimator" in source:
            kind = "ChartAnimator MP4"
        else:
            kind = "mplfinance PNG"
        print(f"  Slot '{slot['name']}' [{kind}] -> {dur:.1f}s")

    print("[2] Building ffmpeg filter graph...")
    inputs = ["-i", avatar_path]
    for clip in chart_clips:
        inputs += ["-i", clip]

    filter_parts = [f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}[base]"]
    for i, slot in enumerate(slots):
        filter_parts.append(f"[{i+1}:v]setpts=PTS-STARTPTS+{slot['start']}/TB[c{i+1}]")

    prev = "base"
    for i, slot in enumerate(slots):
        out_label = f"v{i+1}"
        filter_parts.append(
            f"[{prev}][c{i+1}]overlay=0:0:enable='between(t,{slot['start']},{slot['end']})'[{out_label}]"
        )
        prev = out_label

    if text_overlays:
        print(f"  Adding {len(text_overlays)} big text overlay(s)...")
        style = (edit_plan or {}).get("style") or (edit_plan or {}).get("editStyle") or {}
        print(f"  Applying edit style: {style.get('id', 'editorial-proof')}")
        overlay_parts, prev = build_text_overlay_filters(text_overlays, prev, style, overlay_settings)
        filter_parts.extend(overlay_parts)

    # Copy captions.ass next to output so the subtitles filter can use a
    # relative filename (avoids Windows drive-colon escaping issues).
    captions_local = os.path.join(os.path.dirname(output_path), os.path.basename(captions_ass))
    if os.path.abspath(captions_local) != os.path.abspath(captions_ass):
        shutil.copy(captions_ass, captions_local)

    filter_parts.append(f"[{prev}]subtitles={os.path.basename(captions_local)}[vsub]")
    if footer_text:
        filter_parts.append(
            f"[vsub]drawtext=text='{footer_text}':fontsize=36:fontcolor=white@0.85:"
            f"x=(w-text_w)/2:y=h-60:box=1:boxcolor=black@0.4:boxborderw=9[vfinal]"
        )
    else:
        filter_parts.append(f"[vsub]null[vfinal]")
    filter_complex = ";".join(filter_parts)

    cmd = (
        ["ffmpeg", "-y"] + inputs +
        ["-filter_complex", filter_complex,
         "-map", "[vfinal]", "-map", "0:a",
         "-c:v", "libx264", "-preset", "fast", "-crf", "22",
         "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart",
         os.path.basename(output_path)]
    )

    print("[3] Rendering...")
    result = subprocess.run(cmd, cwd=os.path.dirname(output_path), capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg compose failed:\n{result.stderr[-3000:]}")

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"\nDone! Output: {output_path}")


if __name__ == "__main__":
    avatar_path  = sys.argv[1]
    slots_file   = sys.argv[2]
    chart_dir    = sys.argv[3]
    captions_ass = sys.argv[4]
    footer_text  = sys.argv[5]
    output_path  = sys.argv[6]
    overlays_file = sys.argv[7] if len(sys.argv) > 7 else None
    edit_plan_file = sys.argv[8] if len(sys.argv) > 8 else None

    with open(slots_file, encoding="utf-8") as f:
        slots = json.load(f)["slots"]

    text_overlays = None
    overlay_settings = None
    if overlays_file and os.path.exists(overlays_file):
        with open(overlays_file, encoding="utf-8") as f:
            overlay_payload = json.load(f)
            text_overlays = overlay_payload.get("overlays") or []
            overlay_settings = overlay_payload.get("settings") or {}

    edit_plan = None
    if edit_plan_file and os.path.exists(edit_plan_file):
        with open(edit_plan_file, encoding="utf-8") as f:
            edit_plan = json.load(f)

    compose(avatar_path, slots, chart_dir, captions_ass, footer_text, output_path, text_overlays, edit_plan, overlay_settings)
