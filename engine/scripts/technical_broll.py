"""Generate voice-beat technical motion graphics without external APIs.

The visual grammar follows the approved Finance Editorial reference: dark
full-screen canvas, one focal mechanism per scene, neon trace, readable proof
state and enough hold time to understand the claim.
"""

from __future__ import annotations

import hashlib
import math
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont


W, H, FPS = 1080, 1920, 25
BG = "#060B16"
INK = "#F4F7EF"
MUTED = "#8B97A8"
LIME = "#B6FF36"
RED = "#FF4D5E"
YELLOW = "#FFC857"
BLUE = "#55B8FF"
FONT_XB = Path(r"C:\Windows\Fonts\Montserrat-ExtraBold.ttf")
FONT_SB = Path(r"C:\Windows\Fonts\Montserrat-SemiBold.ttf")


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value).lower().replace("đ", "d"))
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def ease(value: float) -> float:
    value = clamp(value)
    return 1 - (1 - value) ** 3


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    preferred = FONT_XB if bold else FONT_SB
    candidates = (
        preferred,
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default(size=size)


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, minimum: int = 24) -> ImageFont.FreeTypeFont:
    size = start
    while size > minimum:
        candidate = font(size)
        if draw.textbbox((0, 0), text, font=candidate)[2] <= max_width:
            return candidate
        size -= 2
    return font(minimum)


def short_label(value: str, limit: int = 8) -> str:
    words = re.sub(r"\s+", " ", str(value)).strip().split()
    return " ".join(words[:limit]).upper()


def glow_line(image: Image.Image, points: list[tuple[int, int]], color: str, width: int = 7) -> None:
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.line(points, fill=color, width=width * 4, joint="curve")
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(width * 2)))
    ImageDraw.Draw(image).line(points, fill=color, width=width, joint="curve")


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str, width: int = 3) -> None:
    draw.rounded_rectangle(box, radius=30, fill=fill, outline=outline, width=width)


def resolve_theme(palette: list[str] | None, style_id: str) -> dict[str, str]:
    values = palette or [BG, LIME, INK]
    background = values[0] if len(values) > 0 else BG
    accent = values[1] if len(values) > 1 else LIME
    ink = values[2] if len(values) > 2 else INK
    overrides = {
        "editorial-proof": {"background": "#060B16", "accent": "#B6FF36", "ink": "#F4F7EF"},
        "soft-signal": {"background": "#183029", "accent": "#F5A623", "ink": "#FFF8EC"},
        "folk-frequency": {"background": "#0047AB", "accent": "#FF1493", "ink": "#FFE000"},
        "visual-metaphor": {"background": "#18201B", "accent": "#FFCB69", "ink": "#FFF8E7"},
    }
    return overrides.get(style_id, {"background": background, "accent": accent, "ink": ink})


def base_frame(kind: str, accent: str, beat: dict[str, Any] | None = None) -> Image.Image:
    theme = (beat or {}).get("_theme") or {"background": BG, "ink": INK}
    background = theme.get("background", BG)
    ink = theme.get("ink", INK)
    style_id = str((beat or {}).get("_style_id") or "editorial-proof")
    image = Image.new("RGBA", (W, H), background)
    draw = ImageDraw.Draw(image, "RGBA")
    base_rgb = tuple(int(background[index:index + 2], 16) for index in (1, 3, 5))
    for y in range(H):
        ratio = y / H
        draw.line((0, y, W, y), fill=tuple(min(255, channel + int(12 * ratio)) for channel in base_rgb) + (255,))
    if style_id in {"editorial-proof", "data-kinetic", "swiss-pulse", "screen-demo", "data-drift"}:
        for x in range(0, W, 90):
            draw.line((x, 430, x, 1510), fill=(100, 120, 148, 42), width=1)
        for y in range(430, 1511, 90):
            draw.line((0, y, W, y), fill=(100, 120, 148, 42), width=1)
    elif style_id in {"bold-social", "deconstructed", "maximalist-type"}:
        draw.rectangle((0, 0, 18, H), fill=accent)
    light = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(light).ellipse((720, -280, 1280, 280), fill=(182, 255, 54, 18))
    image.alpha_composite(light)
    draw.text((72, 465), "SƠ ĐỒ MINH HỌA", font=font(24, False), fill=accent)
    draw.text((1008, 470), kind.upper(), font=font(18, False), fill=MUTED, anchor="ra")
    draw.line((72, 510, 1008, 510), fill=(139, 151, 168, 72), width=2)
    draw.text((72, 400), "MÔ PHỎNG CƠ CHẾ · KHÔNG PHẢI BIỂU ĐỒ GIÁ THỰC", font=fit_font(draw, "MÔ PHỎNG CƠ CHẾ · KHÔNG PHẢI BIỂU ĐỒ GIÁ THỰC", 920, 22, 18), fill=MUTED)
    return image


def classify_visual(beat: dict[str, Any]) -> str:
    text = normalize(beat.get("spoken_meaning") or beat.get("spokenMeaning") or "")
    source = normalize(beat.get("asset_source") or beat.get("assetSource") or "")
    if "ly nuoc" in text or "mep ban" in text:
        return "glass-metaphor"
    if any(word in text for word in ("nfp", "tin tuc", "bao cao", "nghien cuu", "pitchbook", "mckinsey")):
        return "signal-dashboard"
    if any(word in text for word in ("bieu do", "duong xanh", "duong do", "gia ", "vang", "xu huong", "phuc hoi", "thanh khoan", "thi truong")):
        return "market-chart"
    if any(word in source for word in ("before after", "comparison")) or any(word in text for word in ("truoc", "sau", "so sanh", "ket qua")):
        return "comparison"
    if any(word in source for word in ("screen demo", "dashboard")) or any(word in text for word in ("man hinh", "bao cao", "du lieu", "nghien cuu", "nfp", "tin tuc", "pitchbook", "mckinsey")):
        return "signal-dashboard"
    if any(word in text for word in ("quy trinh", "buoc", "dau vao", "dau ra", "he thong", "co che")):
        return "workflow"
    return "mechanism"


def visual_variant(kind: str, beat: dict[str, Any]) -> str:
    """Choose a claim-shaped layout, not merely a different headline."""
    text = normalize(beat.get("spoken_meaning") or beat.get("spokenMeaning") or "")
    if kind == "signal-dashboard":
        if "giam" in text or "pitchbook" in text:
            return "report-decline"
        if re.search(r"\d+\s*%", text) or "mckinsey" in text:
            return "source-stat"
        return "evidence-network"
    if kind == "market-chart":
        if "duong xanh" in text or "duong do" in text:
            return "head-to-head"
        if "chi phi" in text and "doanh thu" in text:
            return "dual-series"
        return "trend-line"
    return kind


def percent_from_beat(beat: dict[str, Any], fallback: str = "--") -> str:
    match = re.search(r"\d+(?:[.,]\d+)?\s*%", str(beat.get("spoken_meaning") or ""))
    return match.group(0).replace(" ", "") if match else fallback


def source_from_beat(beat: dict[str, Any]) -> str:
    text = str(beat.get("spoken_meaning") or "")
    for source in ("McKinsey", "PitchBook", "NFP"):
        if source.lower() in text.lower():
            return source.upper()
    return "VERIFIED SOURCE"


def market_frame(progress: float, beat: dict[str, Any], accent: str) -> Image.Image:
    image = base_frame("market / trend", accent, beat)
    draw = ImageDraw.Draw(image, "RGBA")
    spoken = normalize(beat.get("spoken_meaning") or "")
    draw.text((72, 555), "DIỄN BIẾN → PHẢN ỨNG", font=font(46), fill=INK)
    rounded(draw, (76, 670, 1004, 1390), "#0D1726", "#263A52")
    for x in range(130, 960, 110):
        draw.line((x, 730, x, 1320), fill=(74, 94, 120, 70), width=1)
    for y in range(760, 1321, 112):
        draw.line((130, y, 950, y), fill=(74, 94, 120, 70), width=1)
    falling = "giam" in spoken or "lao doc" in spoken or "phuc hoi" in spoken
    if falling:
        points = [(135, 820), (250, 870), (355, 805), (470, 1010), (575, 1210), (675, 1260), (790, 1080), (940, 940)]
    else:
        points = [(135, 1210), (250, 1110), (355, 1160), (470, 980), (575, 1030), (680, 840), (790, 910), (940, 735)]
    reveal = max(2, round(2 + ease(progress) * (len(points) - 2)))
    first_color = RED if falling else accent
    glow_line(image, points[:reveal], first_color, 9)
    draw = ImageDraw.Draw(image, "RGBA")
    if progress > 0.58 and ("phuc hoi" in spoken or "van tang" in spoken or "xu huong" in spoken):
        recovery = points[-3:]
        glow_line(image, recovery, accent, 10)
        draw = ImageDraw.Draw(image, "RGBA")
        draw.text((916, 850), "PHỤC HỒI", font=font(25), fill=accent, anchor="ra")
    draw.rounded_rectangle((125, 1450, 955, 1580), radius=28, fill="#14231D", outline=accent, width=3)
    draw.text((540, 1515), "ÁP LỰC NGẮN HẠN  →  KIỂM TRA XU HƯỚNG", font=fit_font(draw, "ÁP LỰC NGẮN HẠN  →  KIỂM TRA XU HƯỚNG", 750, 31), fill=INK, anchor="mm")
    return image


def dual_series_frame(progress: float, beat: dict[str, Any], accent: str) -> Image.Image:
    image = base_frame("cost / revenue", accent, beat)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.text((72, 555), "COST vs REVENUE", font=font(48), fill=INK)
    rounded(draw, (76, 680, 1004, 1390), "#0D1726", "#263A52")
    for x in range(145, 960, 135):
        draw.line((x, 750, x, 1320), fill=(74, 94, 120, 70), width=1)
    for y in range(780, 1321, 110):
        draw.line((135, y, 950, y), fill=(74, 94, 120, 70), width=1)
    cost = [(140, 1220), (300, 1110), (460, 990), (620, 850), (780, 690), (945, 570)]
    revenue = [(140, 1200), (300, 1150), (460, 1100), (620, 1040), (780, 965), (945, 900)]
    count = max(2, round(2 + ease(progress) * 4))
    glow_line(image, cost[:count], RED, 9)
    glow_line(image, revenue[:count], accent, 9)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((120, 1475, 150, 1505), fill=RED)
    draw.text((170, 1470), "GPU COST +300%", font=font(28), fill=INK)
    draw.ellipse((560, 1475, 590, 1505), fill=accent)
    draw.text((610, 1470), "REVENUE +45%", font=font(28), fill=INK)
    return image


def head_to_head_frame(progress: float, beat: dict[str, Any], accent: str) -> Image.Image:
    image = base_frame("head / to / head", accent, beat)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.text((72, 555), "TWO OUTCOMES", font=font(48), fill=INK)
    cards = [("ANIMAI", RED, 0.38), ("AIQ", accent, 0.78)]
    for index, (label, color, ratio) in enumerate(cards):
        x1 = 76 + index * 476
        rounded(draw, (x1, 690, x1 + 428, 1390), "#0D1726", color, 4)
        draw.text((x1 + 214, 765), label, font=font(38), fill=color, anchor="mm")
        height = int(470 * ratio * ease(progress))
        draw.rounded_rectangle((x1 + 105, 1280 - height, x1 + 323, 1280), radius=22, fill=color)
        arrow = "DOWN" if index == 0 else "UP"
        draw.text((x1 + 214, 1330), arrow, font=font(29), fill=INK, anchor="mm")
    draw.text((540, 1515), "SAME THEME. DIFFERENT RISK.", font=font(30, False), fill=MUTED, anchor="mm")
    return image


def glass_frame(progress: float, beat: dict[str, Any], accent: str) -> Image.Image:
    image = base_frame("physical / metaphor", accent, beat)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.text((72, 555), "ÁP LỰC KHÔNG PHẢI KẾT CỤC", font=fit_font(draw, "ÁP LỰC KHÔNG PHẢI KẾT CỤC", 930, 45), fill=INK)
    rounded(draw, (76, 660, 1004, 1420), "#0D1726", "#263A52")
    draw.rectangle((130, 1270, 950, 1310), fill="#42536B")
    draw.rectangle((140, 1310, 188, 1480), fill="#263A52")
    draw.rectangle((885, 1310, 925, 1480), fill="#263A52")
    draw.line((895, 1165, 895, 1370), fill=RED, width=9)
    draw.text((875, 1040), "MÉP BÀN", font=font(29), fill=RED, anchor="ra")
    x = int(295 + 420 * ease(progress))
    glass = [(x - 86, 835), (x + 86, 835), (x + 67, 1245), (x - 67, 1245)]
    draw.polygon(glass, fill="#12293B")
    draw.polygon([(x - 73, 1005), (x + 73, 1005), (x + 63, 1230), (x - 63, 1230)], fill="#245777")
    draw.line(glass + [glass[0]], fill=INK, width=6, joint="curve")
    draw.line((x - 68, 1005, x + 68, 1005), fill=BLUE, width=6)
    draw.text((x, 890), "NƯỚC", font=font(28), fill=INK, anchor="mm")
    if progress > 0.16:
        trace = [(185, 1150), (x - 115, 1150)]
        glow_line(image, trace, accent, 5)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((125, 1480, 955, 1598), radius=28, fill="#14231D", outline=accent, width=3)
    draw.text((540, 1539), "CHẠM NGƯỠNG  ≠  ĐÃ ĐỔ", font=fit_font(draw, "CHẠM NGƯỠNG  ≠  ĐÃ ĐỔ", 750, 36), fill=INK, anchor="mm")
    return image


def comparison_frame(progress: float, beat: dict[str, Any], accent: str) -> Image.Image:
    image = base_frame("before / after", accent, beat)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.text((72, 555), "SO SÁNH HAI TRẠNG THÁI", font=font(46), fill=INK)
    labels = [("PHẢN ỨNG", "VỘI VÀNG", RED), ("KIỂM CHỨNG", "CÓ BỐI CẢNH", accent)]
    for index, (kicker, label, color) in enumerate(labels):
        local = ease(progress * 1.35 - index * 0.18)
        x1 = 76 + index * 476
        y1 = int(700 + 70 * (1 - local))
        rounded(draw, (x1, y1, x1 + 428, 1375), "#0D1726", color, 4)
        draw.text((x1 + 34, y1 + 45), kicker, font=font(23, False), fill=color)
        draw.text((x1 + 34, y1 + 115), label, font=fit_font(draw, label, 360, 39), fill=INK)
        bar_height = int(360 * local)
        draw.rounded_rectangle((x1 + 95, 1280 - bar_height, x1 + 333, 1280), radius=20, fill=color)
    draw.text((540, 1505), "CLAIM  →  BẰNG CHỨNG  →  QUYẾT ĐỊNH", font=fit_font(draw, "CLAIM  →  BẰNG CHỨNG  →  QUYẾT ĐỊNH", 870, 32), fill=MUTED, anchor="mm")
    return image


def signal_frame(progress: float, beat: dict[str, Any], accent: str) -> Image.Image:
    image = base_frame("signal / evidence", accent, beat)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.text((72, 555), "ĐỌC TÍN HIỆU TRONG BỐI CẢNH", font=fit_font(draw, "ĐỌC TÍN HIỆU TRONG BỐI CẢNH", 920, 46), fill=INK)
    center = (540, 1020)
    nodes = [("DỮ LIỆU", (210, 760), BLUE), ("TIN TỨC", (870, 760), YELLOW), ("XU HƯỚNG", (540, 1370), accent)]
    for index, (label, point, color) in enumerate(nodes):
        local = ease(progress * 1.4 - index * 0.17)
        end = (int(center[0] + (point[0] - center[0]) * local), int(center[1] + (point[1] - center[1]) * local))
        glow_line(image, [center, end], color, 5)
        draw = ImageDraw.Draw(image, "RGBA")
        radius = 92
        draw.ellipse((end[0] - radius, end[1] - radius, end[0] + radius, end[1] + radius), fill="#101C2C", outline=color, width=4)
        draw.text(end, label, font=fit_font(draw, label, 160, 25, 19), fill=INK, anchor="mm")
    pulse = int(10 * math.sin(progress * math.tau * 2))
    draw.ellipse((center[0] - 120 - pulse, center[1] - 120 - pulse, center[0] + 120 + pulse, center[1] + 120 + pulse), fill="#15251C", outline=accent, width=6)
    draw.text(center, "KIỂM\nCHỨNG", font=font(34), fill=accent, anchor="mm", align="center")
    return image


def source_stat_frame(progress: float, beat: dict[str, Any], accent: str) -> Image.Image:
    image = base_frame("source / statistic", accent, beat)
    draw = ImageDraw.Draw(image, "RGBA")
    source = source_from_beat(beat)
    value = percent_from_beat(beat)
    draw.text((72, 555), source, font=font(36, False), fill=accent)
    draw.text((72, 640), "REPORTED OUTCOME", font=font(47), fill=INK)
    rounded(draw, (76, 790, 1004, 1390), "#0D1726", "#263A52")
    scale = 0.82 + 0.18 * ease(progress)
    value_font = font(int(190 * scale))
    draw.text((540, 1015), value, font=value_font, fill=accent, anchor="mm")
    draw.text((540, 1195), "PROJECTS WITH POSITIVE RETURN", font=fit_font(draw, "PROJECTS WITH POSITIVE RETURN", 760, 33), fill=INK, anchor="mm")
    width = int(780 * 0.12 * ease(progress))
    draw.rounded_rectangle((150, 1290, 930, 1345), radius=22, fill="#233044")
    draw.rounded_rectangle((150, 1290, 150 + max(12, width), 1345), radius=22, fill=accent)
    return image


def report_decline_frame(progress: float, beat: dict[str, Any], accent: str) -> Image.Image:
    image = base_frame("report / decline", accent, beat)
    draw = ImageDraw.Draw(image, "RGBA")
    source = source_from_beat(beat)
    value = percent_from_beat(beat, "60%")
    draw.text((72, 555), source + " REPORT", font=font(42), fill=INK)
    rounded(draw, (92, 685, 988, 1450), "#F1F3F5", "#263A52", 4)
    draw.rectangle((140, 750, 940, 845), fill="#DCE2E8")
    draw.text((175, 774), "VALUATION REVIEW", font=font(27), fill="#172234")
    for y, width in ((910, 650), (985, 730), (1060, 520)):
        draw.rounded_rectangle((155, y, 155 + width, y + 25), radius=10, fill="#AAB4C0")
    reveal = int(310 * ease(progress))
    draw.rounded_rectangle((170, 1340 - reveal, 390, 1340), radius=18, fill=RED)
    draw.text((610, 1130), value, font=font(135), fill=RED, anchor="mm")
    draw.text((610, 1265), "VALUATION", font=font(30), fill="#172234", anchor="mm")
    return image


def workflow_frame(progress: float, beat: dict[str, Any], accent: str) -> Image.Image:
    image = base_frame("mechanism / flow", accent, beat)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.text((72, 555), "MỘT CƠ CHẾ · BA BƯỚC", font=font(46), fill=INK)
    items = [("01", "TÍN HIỆU", BLUE), ("02", "KIỂM CHỨNG", YELLOW), ("03", "HÀNH ĐỘNG", accent)]
    for index, (number, label, color) in enumerate(items):
        local = ease(progress * 1.45 - index * 0.17)
        y = int(700 + index * 275 + 60 * (1 - local))
        if index:
            glow_line(image, [(540, y - 100), (540, y - 28)], color, 4)
            draw = ImageDraw.Draw(image, "RGBA")
        rounded(draw, (120, y, 960, y + 185), "#0D1726", color, 4)
        draw.text((175, y + 48), number, font=font(31, False), fill=color)
        draw.text((290, y + 48), label, font=font(42), fill=INK)
        draw.ellipse((840, y + 58, 900, y + 118), fill=color if local > 0.72 else MUTED)
    return image


def render_technical_clip(beat: dict[str, Any], output_path: Path, palette: list[str] | None = None, style_id: str = "editorial-proof") -> dict[str, Any]:
    global INK
    start = float(beat.get("start") or 0)
    end = float(beat.get("end") or start + 1)
    duration = max(0.9, end - start)
    theme = resolve_theme(palette, style_id)
    INK = theme["ink"]
    render_beat = {**beat, "_theme": theme, "_style_id": style_id}
    kind = classify_visual(render_beat)
    variant = visual_variant(kind, render_beat)
    accent = theme["accent"]
    renderer = {
        "market-chart": market_frame,
        "glass-metaphor": glass_frame,
        "comparison": comparison_frame,
        "signal-dashboard": signal_frame,
        "workflow": workflow_frame,
        "mechanism": workflow_frame,
    }[kind]
    renderer = {
        "dual-series": dual_series_frame,
        "head-to-head": head_to_head_frame,
        "source-stat": source_stat_frame,
        "report-decline": report_decline_frame,
    }.get(variant, renderer)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(output_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdin is not None
    frame_count = max(round(duration * FPS), round(0.9 * FPS))
    try:
        for index in range(frame_count):
            progress = index / max(1, frame_count - 1)
            process.stdin.write(renderer(progress, render_beat, accent).convert("RGB").tobytes())
    finally:
        process.stdin.close()
    error = (process.stderr.read() if process.stderr else b"").decode("utf-8", errors="replace")
    if process.wait() != 0:
        raise RuntimeError(f"Không thể tạo B-roll kỹ thuật: {error[-1200:]}")
    return {
        "kind": kind,
        "visual_variant": variant,
        "style_id": style_id,
        "theme": theme,
        "overlay_policy": "suppress",
        "duration": round(frame_count / FPS, 3),
        "generator": "brandflow-technical-motion-v1",
        "fingerprint": hashlib.sha256(str(beat.get("spoken_meaning") or "").encode("utf-8")).hexdigest()[:12],
    }
