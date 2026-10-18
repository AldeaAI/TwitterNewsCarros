"""
Square (1080x1080) text-only images for the daily post, in the Data Automotriz brand.
There are 12 layouts that share the brand palette, logo and fonts; each run uses a different one.
No article photos are used, to avoid copyright issues.
"""
import os
from datetime import datetime, timezone
from typing import Callable, List, Optional

from PIL import Image, ImageDraw, ImageFont

ASSETS = os.path.join(os.path.dirname(__file__), "..", "InstagramNews")
FONT_BOLD = os.path.join(ASSETS, "Fonts", "Roboto-Bold.ttf")
FONT_REG = os.path.join(ASSETS, "Fonts", "Roboto-Regular.ttf")
LOGO_PATH = os.path.join(ASSETS, "Backgrounds", "DA_Logo.png")

SIZE = 1080
MARGIN = 80

# Data Automotriz brand palette, sampled from the logo and banner
BLACK = (16, 16, 16, 255)        # #101010 background
SLATE = (26, 27, 35, 255)        # #1A1B23 dark panel
GOLD = (206, 169, 76, 255)       # #CEA94C accent
GOLD_DEEP = (138, 107, 40, 255)  # darker gold for gradients
TEXT = (245, 241, 230, 255)      # warm white for body text
DARK_TEXT = (16, 16, 16, 255)

HANDLE = "@dataautomotriz"
RUNS_PER_DAY = 2  # the workflow runs twice a day (14:00 and 20:00 UTC)

_FONT_CACHE = {}


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(path, size)
    return _FONT_CACHE[key]


def _logo(size: int) -> Image.Image:
    """The Data Automotriz mark in a rounded square."""
    logo = Image.open(LOGO_PATH).convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=size // 7, fill=255)
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    tile.paste(logo, (0, 0), mask)
    return tile


def _gradient(c1, c2) -> Image.Image:
    """Diagonal gradient from c1 (top-left) to c2 (bottom-right)."""
    layer = Image.new("RGBA", (SIZE, SIZE))
    draw = ImageDraw.Draw(layer)
    for i in range(2 * SIZE):
        t = min(1.0, i / (2 * SIZE))
        color = tuple(int(c1[k] * (1 - t) + c2[k] * t) for k in range(3)) + (255,)
        draw.line([(i, 0), (0, i)], fill=color, width=2)
    return layer


def _wrap(text: str, font, width: int) -> List[str]:
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if probe.textbbox((0, 0), trial, font=font)[2] <= width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _align_x(align: str, x: int, width: int, w: int) -> int:
    return x + (width - w) // 2 if align == "center" else x


def _headline(canvas, text: str, x: int, y: int, width: int, bottom: int, color,
              align: str = "left", sizes=range(66, 41, -2)) -> None:
    """Draw the headline at the largest size that fits the width and the space down to `bottom`."""
    draw = ImageDraw.Draw(canvas)
    for size in sizes:
        font = _font(FONT_BOLD, size)
        step = int(size * 1.27)
        lines = _wrap(text, font, width)
        if y + len(lines) * step <= bottom:
            break
    else:
        # Nothing fits: keep the lines that fit and end with an ellipsis
        max_lines = max(1, (bottom - y) // step)
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" ,.;:") + "…"
        print(f"[image_post] headline too long, truncated to {max_lines} lines")
    for line in lines:
        w = draw.textbbox((0, 0), line, font=font)[2]
        draw.text((_align_x(align, x, width, w), y), line, font=font, fill=color)
        y += step


def _pill(canvas, x: int, y: int, bg, fg, align: str = "left", width: int = 0) -> None:
    draw = ImageDraw.Draw(canvas)
    font = _font(FONT_REG, 34)
    b = draw.textbbox((0, 0), HANDLE, font=font)
    px, py = 28, 14
    w, h = b[2] - b[0] + 2 * px, b[3] - b[1] + 2 * py
    xx = _align_x(align, x, width, w)
    draw.rounded_rectangle([(xx, y), (xx + w, y + h)], radius=h // 2, fill=bg)
    draw.text((xx + px, y + py - b[1]), HANDLE, font=font, fill=fg)


def _new(bg) -> Image.Image:
    return Image.new("RGBA", (SIZE, SIZE), bg)


# Each layout takes the headline text and returns the finished canvas.

def _layout_1(text):  # black, gold top-left and bottom-right triangles
    c = _new(BLACK); d = ImageDraw.Draw(c)
    d.polygon([(0, 0), (300, 0), (0, 240)], fill=GOLD)
    d.polygon([(SIZE, SIZE), (SIZE, 800), (640, SIZE)], fill=GOLD)
    c.alpha_composite(_logo(170), (SIZE - 170 - MARGIN + 10, MARGIN - 10))
    _headline(c, text, MARGIN, 400, SIZE - 2 * MARGIN - 120, 900, TEXT)
    _pill(c, MARGIN, 960, GOLD, DARK_TEXT)
    return c


def _layout_2(text):  # black, thin gold bar on top, logo left
    c = _new(BLACK)
    ImageDraw.Draw(c).rectangle([(0, 0), (SIZE, 16)], fill=GOLD)
    c.alpha_composite(_logo(150), (MARGIN, MARGIN + 20))
    _headline(c, text, MARGIN, 330, SIZE - 2 * MARGIN, 900, TEXT)
    _pill(c, MARGIN, 960, GOLD, DARK_TEXT)
    return c


def _layout_3(text):  # black, gold top-left corner, logo top-right
    c = _new(BLACK)
    ImageDraw.Draw(c).polygon([(0, 0), (260, 0), (0, 200)], fill=GOLD)
    c.alpha_composite(_logo(170), (SIZE - 170 - MARGIN + 10, MARGIN - 10))
    _headline(c, text, MARGIN, 400, SIZE - 2 * MARGIN, 900, TEXT)
    _pill(c, MARGIN, 960, GOLD, DARK_TEXT)
    return c


def _layout_4(text):  # slate, gold bottom-right corner, logo top-left
    c = _new(SLATE)
    ImageDraw.Draw(c).polygon([(SIZE, SIZE), (SIZE, 560), (560, SIZE)], fill=GOLD)
    c.alpha_composite(_logo(130), (MARGIN, MARGIN))
    _headline(c, text, MARGIN, 250, SIZE - 2 * MARGIN - 200, 900, TEXT)
    _pill(c, MARGIN, 960, TEXT, DARK_TEXT)
    return c


def _layout_5(text):  # black, solid gold band across the top, logo centered in the band
    c = _new(BLACK)
    ImageDraw.Draw(c).rectangle([(0, 0), (SIZE, 300)], fill=GOLD)
    c.alpha_composite(_logo(180), ((SIZE - 180) // 2, 60))
    _headline(c, text, MARGIN, 380, SIZE - 2 * MARGIN, 900, TEXT)
    _pill(c, MARGIN, 960, GOLD, DARK_TEXT)
    return c


def _layout_6(text):  # dark gold to black gradient, warm white text, logo top-right
    c = _gradient(GOLD_DEEP, BLACK)
    c.alpha_composite(_logo(150), (SIZE - 150 - MARGIN + 10, MARGIN - 10))
    _headline(c, text, MARGIN, 400, SIZE - 2 * MARGIN, 900, TEXT)
    _pill(c, MARGIN, 960, GOLD, DARK_TEXT)
    return c


def _layout_7(text):  # black, centered, logo centered at the top
    c = _new(BLACK)
    c.alpha_composite(_logo(190), ((SIZE - 190) // 2, 90))
    _headline(c, text, MARGIN, 330, SIZE - 2 * MARGIN, 880, TEXT, "center")
    _pill(c, 0, 960, GOLD, DARK_TEXT, "center", SIZE)
    return c


def _layout_8(text):  # black, gold vertical bar, text indented
    c = _new(BLACK)
    ImageDraw.Draw(c).rectangle([(MARGIN, 300), (MARGIN + 14, 800)], fill=GOLD)
    c.alpha_composite(_logo(140), (SIZE - 140 - MARGIN + 10, MARGIN - 10))
    _headline(c, text, MARGIN + 50, 330, SIZE - 2 * MARGIN - 120, 900, TEXT)
    _pill(c, MARGIN + 50, 960, GOLD, DARK_TEXT)
    return c


def _layout_9(text):  # slate, centered, logo centered at the top
    c = _new(SLATE)
    c.alpha_composite(_logo(170), ((SIZE - 170) // 2, 80))
    _headline(c, text, MARGIN, 330, SIZE - 2 * MARGIN, 900, TEXT, "center")
    _pill(c, 0, 960, GOLD, DARK_TEXT, "center", SIZE)
    return c


def _layout_10(text):  # black with a gold block behind the headline
    c = _new(BLACK)
    ImageDraw.Draw(c).rectangle([(0, 330), (SIZE, 750)], fill=GOLD)
    c.alpha_composite(_logo(150), (MARGIN, MARGIN + 20))
    _headline(c, text, MARGIN, 370, SIZE - 2 * MARGIN, 710, DARK_TEXT)
    _pill(c, MARGIN, 930, SLATE, GOLD)
    return c


def _layout_11(text):  # black with a gold diagonal line near the bottom
    c = _new(BLACK)
    ImageDraw.Draw(c).polygon([(0, 900), (SIZE, 780), (SIZE, 820), (0, 920)], fill=GOLD)
    c.alpha_composite(_logo(150), (SIZE - 150 - MARGIN + 10, MARGIN - 10))
    _headline(c, text, MARGIN, 220, SIZE - 2 * MARGIN, 700, TEXT)
    _pill(c, MARGIN, 960, GOLD, DARK_TEXT)
    return c


def _layout_12(text):  # black top, gold bottom block with the logo on the seam
    c = _new(BLACK)
    ImageDraw.Draw(c).rectangle([(0, 640), (SIZE, SIZE)], fill=GOLD)
    c.alpha_composite(_logo(150), ((SIZE - 150) // 2, 640 - 75))
    _headline(c, text, MARGIN, 740, SIZE - 2 * MARGIN, 935, DARK_TEXT, "center", range(56, 41, -2))
    _pill(c, 0, 960, BLACK, GOLD, "center", SIZE)
    return c


LAYOUTS: List[Callable[[str], Image.Image]] = [
    _layout_1, _layout_2, _layout_3, _layout_4, _layout_5, _layout_6,
    _layout_7, _layout_8, _layout_9, _layout_10, _layout_11, _layout_12,
]


def layout_index(now: Optional[datetime] = None) -> int:
    """Pick the layout for this run: a different one for each run, cycling through all of them."""
    now = now or datetime.now(timezone.utc)
    run_of_day = 0 if now.hour < 17 else 1
    slot = (now.timetuple().tm_yday - 1) * RUNS_PER_DAY + run_of_day
    return slot % len(LAYOUTS)


def build_post_image(text: str, out_path: str, layout: Optional[int] = None) -> str:
    """Render the post image to `out_path` (a .jpg path is saved as JPEG) and return that path."""
    index = layout_index() if layout is None else layout
    print(f"[image_post] layout {index + 1} of {len(LAYOUTS)}")
    LAYOUTS[index](text).convert("RGB").save(out_path, quality=95)
    return out_path
