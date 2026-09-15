from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


PACK_ROOT = Path(__file__).resolve().parents[1]
ROOT = PACK_ROOT / "generated"
SOURCE = PACK_ROOT / "source" / "finance_reference_raw.mp4"
W, H, FPS = 1080, 1920, 25
GRAPHICS_START = 3.6
GRAPHICS_END = 35.6
TOTAL = 39.404

BG = "#060B16"
INK = "#F4F7EF"
MUTED = "#8B97A8"
LIME = "#B6FF36"
RED = "#FF4D5E"
YELLOW = "#FFC857"
BLUE = "#55B8FF"

FONT_XB = r"C:\Windows\Fonts\Montserrat-ExtraBold.ttf"
FONT_SB = r"C:\Windows\Fonts\Montserrat-SemiBold.ttf"

BROLLS = [
    {
        "file": PACK_ROOT / "assets" / "broll" / "pexels_ebook.mp4",
        "source_start": 1.0,
        "start": 6.5,
        "duration": 2.9,
        "kicker": "TÀI LIỆU THỰC HÀNH",
        "title": "EBOOK + CHỈ BÁO",
    },
]


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_XB if bold else FONT_SB, size)


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def smooth(v: float) -> float:
    v = clamp(v)
    return v * v * (3 - 2 * v)


def ease_out(v: float) -> float:
    v = clamp(v)
    return 1 - (1 - v) ** 3


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def fade_for(t: float, start: float, end: float, edge: float = 0.28) -> float:
    return min(smooth((t - start) / edge), smooth((end - t) / edge))


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, min_size: int = 38) -> ImageFont.FreeTypeFont:
    size = start
    while size > min_size:
        f = font(size)
        if draw.textbbox((0, 0), text, font=f)[2] <= max_width:
            return f
        size -= 2
    return font(min_size)


def centered(draw: ImageDraw.ImageDraw, y: int, text: str, f: ImageFont.FreeTypeFont, fill: str = INK, stroke: int = 0) -> None:
    box = draw.textbbox((0, 0), text, font=f, stroke_width=stroke)
    x = (W - (box[2] - box[0])) // 2
    draw.text((x, y), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=BG)


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: str, outline: str | None = None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def glow_line(img: Image.Image, pts: list[tuple[float, float]], color: str, width: int = 8) -> None:
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.line(pts, fill=color, width=width * 4, joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(width * 2))
    img.alpha_composite(glow)
    ImageDraw.Draw(img).line(pts, fill=color, width=width, joint="curve")


def base_frame() -> Image.Image:
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    for y in range(H):
        p = y / H
        col = (6 + int(5 * p), 11 + int(8 * p), 22 + int(13 * p), 255)
        d.line((0, y, W, y), fill=col)
    for x in range(0, W, 90):
        d.line((x, 0, x, 1480), fill=(30, 42, 58, 80), width=1)
    for y in range(0, 1480, 90):
        d.line((0, y, W, y), fill=(30, 42, 58, 80), width=1)
    d.ellipse((760, -240, 1260, 260), fill=(86, 255, 100, 12))
    return img


def header(d: ImageDraw.ImageDraw, kicker: str, line1: str, line2: str = "", accent: str = LIME) -> None:
    d.text((72, 92), kicker, font=font(28, False), fill=accent)
    d.line((72, 142, 222, 142), fill=accent, width=5)
    f1 = fit_text(d, line1, 936, 86, 58)
    d.text((72, 190), line1, font=f1, fill=INK)
    if line2:
        f2 = fit_text(d, line2, 936, 86, 58)
        d.text((72, 300), line2, font=f2, fill=accent)


def scene_failure(t: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    p = smooth((t - 3.6) / 2.1)
    header(d, "MULTI-TIMEFRAME / 01", "VÀO LỆNH NGƯỢC H4", accent=RED)

    rounded(d, (92, 510, 988, 890), 36, "#101A2A", "#26354B", 3)
    d.text((136, 548), "H4 · XU HƯỚNG CHÍNH", font=font(34, False), fill=MUTED)
    pts = [(145, 700), (280, 635), (390, 725), (520, 660), (650, 790), (790, 735), (930, 825)]
    reveal = max(2, int(len(pts) * ease_out(p)))
    glow_line(img, pts[:reveal], RED, 10)
    d = ImageDraw.Draw(img)
    d.text((750, 560), "GIẢM", font=font(58), fill=RED)

    rounded(d, (92, 975, 988, 1360), 36, "#101A2A", "#26354B", 3)
    d.text((136, 1012), "M5 · LỆNH VỪA VÀO", font=font(34, False), fill=MUTED)
    ticket_y = int(1130 + 70 * (1 - ease_out(p)))
    rounded(d, (255, ticket_y, 825, ticket_y + 126), 24, "#14251D", LIME, 4)
    d.text((298, ticket_y + 27), "BUY  ·  ENTRY", font=font(48), fill=LIME)

    if p > 0.55:
        q = smooth((p - 0.55) / 0.45)
        sweep_y = int(760 + q * 500)
        d.line((160, sweep_y, 920, sweep_y), fill=RED, width=18)
        d.polygon([(920, sweep_y), (870, sweep_y - 28), (870, sweep_y + 28)], fill=RED)
    if p > 0.48:
        alpha = int(255 * smooth((p - 0.48) / 0.22))
        stamp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(stamp)
        rounded(sd, (270, 1260, 810, 1418), 26, (70, 8, 18, 235), RED, 7)
        sd.text((333, 1292), "BỊ QUÉT", font=font(68), fill=RED)
        mask = stamp.getchannel("A").point(lambda a: a * alpha // 255)
        stamp.putalpha(mask)
        img.alpha_composite(stamp)
    return img


def scene_gift(t: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    p = smooth((t - 5.7) / 3.7)
    header(d, "TÀI LIỆU MIỄN PHÍ", "COMMENT", "“CHỈ BÁO”", accent=LIME)
    y = int(520 + 50 * (1 - ease_out(p)))
    rounded(d, (120, y, 960, y + 600), 44, "#F4F7EF", LIME, 5)
    d.rounded_rectangle((185, y + 92, 500, y + 486), radius=22, fill="#07111F", outline="#24364D", width=3)
    d.text((225, y + 135), "EBOOK", font=font(46), fill=LIME)
    d.text((225, y + 220), "TRADING", font=font(52), fill=INK)
    d.line((225, y + 312, 455, y + 312), fill=RED, width=9)
    d.line((225, y + 365, 410, y + 365), fill=BLUE, width=9)
    rounded(d, (555, y + 118, 895, y + 265), 22, "#E5FFBA", None)
    d.text((600, y + 150), "FOLLOW", font=font(42), fill="#102011")
    d.text((610, y + 200), "TREND", font=font(38), fill="#102011")
    rounded(d, (555, y + 310, 895, y + 455), 22, "#D7E6FF", None)
    d.text((620, y + 344), "CHỈ BÁO", font=font(38), fill="#0A1A35")
    d.text((204, y + 528), "EBOOK + BỘ CHỈ BÁO FOLLOW TREND", font=font(27, False), fill="#172234")
    if p > 0.6:
        # Keep the confirmation badge away from the footer copy.
        d.ellipse((840, y + 486, 930, y + 576), fill=LIME)
        d.text((885, y + 531), "OK", font=font(25), fill="#07110A", anchor="mm")
    return img


def scene_ladder(t: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    p = clamp((t - 9.4) / 8.2)
    header(d, "QUY TRÌNH / 3 TẦNG", "ĐI TỪ KHUNG LỚN", "XUỐNG KHUNG NHỎ")
    x = 250
    ys = [570, 800, 1030, 1260]
    labels = [("D1 / H4", "XU HƯỚNG + VÙNG GIÁ"), ("H1", "ĐIỀU CHỈNH / TIẾP DIỄN"), ("M15", "TÍN HIỆU"), ("M5", "ĐIỂM VÀO")]
    d.line((x, ys[0], x, ys[-1]), fill="#26364A", width=16)
    active_y = lerp(ys[0], ys[-1], ease_out(p))
    glow_line(img, [(x, ys[0]), (x, active_y)], LIME, 8)
    d = ImageDraw.Draw(img)
    for i, (label, desc) in enumerate(labels):
        local = smooth((p * 1.3) - i * 0.22)
        active = active_y >= ys[i] - 6
        r = 40 + int(8 * local)
        d.ellipse((x - r, ys[i] - r, x + r, ys[i] + r), fill=LIME if active else "#152238", outline=INK if active else "#4A5B70", width=4)
        label_font = fit_text(d, label, (r * 2) - 12, 25, 15)
        d.text((x, ys[i]), label, font=label_font, fill="#07110A" if active else INK, anchor="mm")
        card_x = int(340 + 70 * (1 - ease_out(local)))
        rounded(d, (card_x, ys[i] - 72, 952, ys[i] + 72), 26, "#101A2A", LIME if active else "#2D3B4E", 3)
        d.text((card_x + 36, ys[i] - 35), desc, font=fit_text(d, desc, 540, 34, 26), fill=INK if active else MUTED)
    d.text((92, 1430), "KHUNG LỚN = BẢN ĐỒ", font=font(34), fill=MUTED)
    d.text((572, 1430), "KHUNG NHỎ = ĐIỂM BẤM", font=font(30), fill=LIME)
    return img


def scene_h1(t: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    p = clamp((t - 17.6) / 7.1)
    header(d, "TẦNG TRUNG GIAN / H1", "GIÁ ĐANG ĐIỀU CHỈNH", "HAY TIẾP DIỄN?")

    source = (180, 770)
    junction = (540, 880)
    # Branch connectors terminate at the card edge; they never run beneath copy.
    upper = (700, 690)
    lower = (700, 1075)
    target = (540, 1320)
    d.ellipse((120, 710, 240, 830), fill="#142238", outline=BLUE, width=5)
    d.text((153, 742), "H1", font=font(38), fill=INK)
    glow_line(img, [source, junction], BLUE, 9)
    d = ImageDraw.Draw(img)
    if p > 0.25:
        glow_line(img, [junction, upper], YELLOW, 8)
        d = ImageDraw.Draw(img)
        rounded(d, (700, 600, 990, 780), 26, "#241E10", YELLOW, 4)
        d.text((845, 690), "ĐIỀU CHỈNH", font=font(30), fill=YELLOW, anchor="mm")
    if p > 0.48:
        glow_line(img, [junction, lower], LIME, 8)
        d = ImageDraw.Draw(img)
        rounded(d, (700, 985, 990, 1165), 26, "#132314", LIME, 4)
        d.text((845, 1075), "TIẾP DIỄN", font=font(30), fill=LIME, anchor="mm")
    if p > 0.7:
        q = smooth((p - 0.7) / 0.3)
        # The final guide runs through the open center, never across either label card.
        glow_line(img, [junction, (540, 1110), target], LIME, 6)
        d = ImageDraw.Draw(img)
        rr = int(45 + 35 * q)
        d.ellipse((target[0] - rr, target[1] - rr, target[0] + rr, target[1] + rr), outline=LIME, width=8)
        d.line((target[0] - 120, target[1], target[0] + 120, target[1]), fill=LIME, width=4)
        d.line((target[0], target[1] - 120, target[0], target[1] + 120), fill=LIME, width=4)
        centered(d, 1430, "M15 / M5 · TÌM TÍN HIỆU", font(34), LIME)
    return img


def chart_points(progress: float) -> list[tuple[float, float]]:
    full = [(110, 1160), (200, 1030), (290, 1070), (390, 870), (480, 925), (585, 720), (680, 785), (770, 660), (860, 770), (960, 610)]
    n = max(2, int(2 + progress * (len(full) - 2)))
    return full[:n]


def scene_trade(t: float) -> Image.Image:
    img = base_frame()
    d = ImageDraw.Draw(img)
    # Two explicit voice-aligned beats: chart proof, then distilled rule.
    if t < 31.9:
        p = clamp((t - 24.7) / (31.9 - 24.7))
        header(d, "VÍ DỤ THỰC CHIẾN", "H4 TĂNG · GIÁ HỒI", "VỀ VÙNG HỖ TRỢ")
        rounded(d, (72, 500, 1008, 1395), 34, "#0B1422", "#26364A", 3)
        for x in range(120, 1000, 120):
            d.line((x, 560, x, 1350), fill="#1D2C40", width=2)
        for y in range(600, 1360, 120):
            d.line((100, y, 980, y), fill="#1D2C40", width=2)
        d.rectangle((98, 1050, 982, 1200), fill=(182, 255, 54, 35), outline=LIME, width=3)
        q = ease_out(p / 0.42)
        pts = chart_points(q)
        glow_line(img, pts, LIME, 9)
        d = ImageDraw.Draw(img)
        if p > 0.34:
            r = smooth((p - 0.34) / 0.20)
            pull = [(960, 610), (900, 740), (930, 835), (830, 960), (860, 1095)]
            take = max(2, int(2 + r * (len(pull) - 2)))
            glow_line(img, pull[:take], YELLOW, 9)
        if p > 0.54:
            r = smooth((p - 0.54) / 0.18)
            breakout = [(860, 1095), (905, 1010), (875, 970), (960, 850)]
            take = max(2, int(2 + r * (len(breakout) - 2)))
            glow_line(img, breakout[:take], BLUE, 10)
            d = ImageDraw.Draw(img)
            # Put the explanation in a dedicated callout zone above the plot.
            rounded(d, (120, 570, 590, 665), 20, "#24131A", RED, 3)
            d.text((355, 618), "PHÁ CẤU TRÚC GIẢM", font=font(25), fill=RED, anchor="mm")
            d.line((590, 640, 825, 930), fill=RED, width=4)
            if r > 0.72:
                # Keep the action label in a clear lower-right callout zone.
                d.line((835, 1230, 930, 900), fill=BLUE, width=4)
                rounded(d, (700, 1230, 965, 1340), 24, LIME, None)
                d.text((832, 1285), "BUY", font=font(42), fill="#07110A", anchor="mm")
        # Draw the support label last so animated price paths cannot cross the text.
        rounded(d, (390, 1080, 610, 1150), 18, "#0B1422", LIME, 2)
        d.text((500, 1115), "HỖ TRỢ", font=font(29), fill=LIME, anchor="mm")
        d.text((92, 1430), "CHỈ VÀO KHI KHUNG NHỎ XÁC NHẬN", font=font(35), fill=INK)
    else:
        q = smooth((t - 31.9) / (35.6 - 31.9))
        header(d, "NGUYÊN TẮC CHỐT", "KHUNG LỚN", "KHUNG NHỎ")
        x = 540
        d.line((x, 560, x, 1330), fill="#27364A", width=14)
        glow_line(img, [(x, 590), (x, lerp(590, 1290, q))], LIME, 8)
        d = ImageDraw.Draw(img)
        rounded(d, (120, 565, 960, 850), 36, "#101A2A", LIME, 4)
        centered(d, 630, "PHƯƠNG HƯỚNG", font(66), LIME)
        centered(d, 742, "Xu hướng · vùng giá", font(31, False), MUTED)
        if q > 0.38:
            rounded(d, (120, 1040, 960, 1325), 36, "#F4F7EF", LIME, 5)
            centered(d, 1105, "ĐIỂM VÀO", font(72), "#07110A")
            centered(d, 1222, "Tín hiệu · xác nhận", font(31, False), "#364252")
        d.text((140, 1435), "ĐÚNG HƯỚNG TRƯỚC · ĐẸP ENTRY SAU", font=font(34), fill=INK)
    return img


def render_graphics() -> Path:
    out = ROOT / "graphics.mp4"
    duration = GRAPHICS_END - GRAPHICS_START
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
        "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", str(out),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    total_frames = round(duration * FPS)
    for i in range(total_frames):
        t = GRAPHICS_START + i / FPS
        if t < 5.7:
            frame = scene_failure(t)
        elif t < 9.4:
            frame = scene_gift(t)
        elif t < 17.6:
            frame = scene_ladder(t)
        elif t < 24.7:
            frame = scene_h1(t)
        else:
            frame = scene_trade(t)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    code = proc.wait()
    if code:
        raise SystemExit(f"ffmpeg graphics failed: {code}")
    return out


CAPTIONS = [
    (0.00, 3.60, r"Bạn trade trên {\c&H0036FFB6&}khung 5 phút{\c&H00FFFFFF&}\Nnhưng {\c&H0036FFB6&}khung 4 giờ{\c&H00FFFFFF&} đang giảm mạnh"),
    (3.60, 5.70, r"Đó là lý do lệnh vừa vào\Nđã {\c&H004D4DFF&}BỊ QUÉT{\c&H00FFFFFF&}"),
    (5.70, 9.40, r"Comment {\c&H0036FFB6&}CHỈ BÁO{\c&H00FFFFFF&} để nhận ebook\Nvà bộ chỉ báo follow trend miễn phí"),
    (9.40, 12.80, r"Hãy phân tích từ {\c&H0036FFB6&}khung thời gian lớn{\c&H00FFFFFF&}\Nxuống khung thời gian nhỏ"),
    (12.80, 17.60, r"Dùng khung ngày hoặc H4 để xác định\N{\c&H0036FFB6&}xu hướng và vùng giá quan trọng{\c&H00FFFFFF&}"),
    (17.60, 21.20, r"Chuyển xuống H1 để quan sát giá\Nđang {\c&H0036FFB6&}điều chỉnh hay tiếp diễn{\c&H00FFFFFF&}"),
    (21.20, 24.70, r"Cuối cùng dùng M15 hoặc M5\Nđể tìm {\c&H0036FFB6&}tín hiệu vào lệnh{\c&H00FFFFFF&}"),
    (24.70, 28.20, r"H4 đang tăng và giá điều chỉnh\Nvề {\c&H0036FFB6&}vùng hỗ trợ{\c&H00FFFFFF&}"),
    (28.20, 31.90, r"Chờ giá phá cấu trúc giảm ngắn hạn\Nrồi mới tìm cơ hội {\c&H0036FFB6&}BUY{\c&H00FFFFFF&}"),
    (31.90, 35.60, r"Khung lớn cho bạn {\c&H0036FFB6&}phương hướng{\c&H00FFFFFF&}\NKhung nhỏ cho bạn {\c&H0036FFB6&}điểm vào{\c&H00FFFFFF&}"),
    (35.60, 39.40, r"Follow kênh để chọn điểm vào đẹp hơn\Nbằng {\c&H0036FFB6&}phân tích đa khung thời gian{\c&H00FFFFFF&}"),
]


def ass_time(seconds: float) -> str:
    cs = round(seconds * 100)
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def write_captions() -> Path:
    out = ROOT / "captions.ass"
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "ScaledBorderAndShadow: yes",
        "WrapStyle: 2",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Caption,Montserrat ExtraBold,58,&H00FFFFFF,&H00FFFFFF,&H00101010,&H00000000,-1,0,0,0,100,100,0,0,1,6,2,2,64,64,195,1",
        "Style: BrollKicker,Montserrat SemiBold,30,&H0036FFB6,&H0036FFB6,&H00101010,&H90060B16,0,0,0,0,100,100,1,0,3,2,0,7,74,74,0,1",
        "Style: BrollTitle,Montserrat ExtraBold,62,&H00FFFFFF,&H00FFFFFF,&H00101010,&H90060B16,-1,0,0,0,100,100,0,0,3,3,0,7,74,74,0,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for start, end, text in CAPTIONS:
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,{{\\fad(90,90)}}{text}")
    for item in BROLLS:
        start = item["start"] + 0.18
        end = item["start"] + item["duration"] - 0.18
        lines.append(f"Dialogue: 1,{ass_time(start)},{ass_time(end)},BrollKicker,,0,0,0,,{{\\pos(74,92)\\fad(120,120)}}{item['kicker']}")
        lines.append(f"Dialogue: 1,{ass_time(start)},{ass_time(end)},BrollTitle,,0,0,0,,{{\\pos(74,145)\\fad(120,120)}}{item['title']}")
    out.write_text("\n".join(lines), encoding="utf-8-sig")
    return out


def compose(graphics: Path, captions: Path) -> Path:
    base = ROOT / "base.mp4"
    master = ROOT / "master_broll.mp4"
    final = ROOT / "TEST_STYLE_EDITORIAL_MULTITIMEFRAME_V2_NO_FLASH.mp4"
    filter_graph = (
        f"[0:v]trim=start=0:end={GRAPHICS_START},setpts=PTS-STARTPTS[v0];"
        "[1:v]setpts=PTS-STARTPTS[v1];"
        f"[0:v]trim=start={GRAPHICS_END}:end={TOTAL},setpts=PTS-STARTPTS[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[v]"
    )
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(SOURCE), "-i", str(graphics),
        "-filter_complex", filter_graph,
        "-map", "[v]", "-map", "0:a:0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-t", str(TOTAL), str(base),
    ], check=True)

    for item in BROLLS:
        if not item["file"].exists():
            raise SystemExit(f"Missing B-roll: {item['file']}")

    broll_inputs: list[str] = []
    broll_filters: list[str] = []
    previous = "0:v"
    for i, item in enumerate(BROLLS, start=1):
        broll_inputs.extend(["-i", str(item["file"])])
        start = item["start"]
        duration = item["duration"]
        source_start = item["source_start"]
        broll_filters.append(
            f"[{i}:v]trim=start={source_start}:duration={duration},"
            f"setpts=PTS-STARTPTS+{start}/TB,fps={FPS},"
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,"
            f"format=yuva420p,fade=t=in:st={start}:d=0.22:alpha=1[br{i}]"
        )
        out_label = f"mix{i}"
        broll_filters.append(
            f"[{previous}][br{i}]overlay=0:0:eof_action=pass:shortest=0[{out_label}]"
        )
        previous = out_label

    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(base), *broll_inputs,
        "-filter_complex", ";".join(broll_filters),
        "-map", f"[{previous}]", "-map", "0:a:0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "copy", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(master),
    ], check=True)

    escaped = str(captions).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(master), "-vf", f"ass='{escaped}'",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "copy", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(final),
    ], check=True)
    return final


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source: {SOURCE}")
    ROOT.mkdir(parents=True, exist_ok=True)
    graphics = render_graphics()
    captions = write_captions()
    final = compose(graphics, captions)
    print(final.name)


if __name__ == "__main__":
    main()
