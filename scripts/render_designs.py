#!/usr/bin/env python3
"""
Centered, Zero-Overlap High-Retention Carousel Design Engine for SOLE — Bits -N- Bytes (IGIT Sarang).

Design & Layout Guarantees:
1. All content cards and cliffhanger bars are 100% horizontally centered at `x = 540`
   (`x1 = 165, x2 = 915` — equal 165px left and right margins), forming a clean, aligned
   center column that naturally clears the top-right (`x >= 931`), bottom-left (`x <= 160`),
   and bottom-right (`x >= 1045`) torn graph-paper corners of `assets/bits_n_bytes_template.jpg`.
2. Prominent Week / Edition identifier (e.g. "NOV 2026 • WEEK 3") on the Cover Slide and inner slides.
3. No page/slide numbers, no relevance/popularity scores, and no cluttered source/URL footers
   on the visual cards (sources remain in the email table for the team).
4. Uses "WEEKLY NEWS HIGHLIGHTS" (never "Top 10 Countdown").
"""

import argparse
import csv
import json
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "assets" / "bits_n_bytes_template.jpg"
SOLE_LOGO_HD_PATH = BASE_DIR / "assets" / "sole_logo_hd.png"
IGIT_LOGO_HD_PATH = BASE_DIR / "assets" / "igit_logo_hd.png"
BASE_COVER_FRAME_PATH = BASE_DIR / "assets" / "base_cover_frame.png"
BASE_INNER_FRAME_PATH = BASE_DIR / "assets" / "base_inner_frame.png"

_FRAME_CACHE: Dict[str, Image.Image] = {}
_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}

FONT_DIR_MONTSERRAT = Path("/usr/share/fonts/julietaula-montserrat-fonts")
FONT_DIR_CALADEA = Path("/usr/share/fonts/google-crosextra-caladea-fonts")
FONT_DIR_LIBERATION_SERIF = Path("/usr/share/fonts/liberation-serif-fonts")

WIDTH = 1080
HEIGHT = 1350

# Perfectly centered column bounds (Left margin = 165px, Right margin = 165px, Center = 540px)
COL_X1 = 165
COL_X2 = 915
COL_PAD = 32

# Palette sampled from assets/bits_n_bytes_template.jpg
COSMIC_TOP = (5, 17, 34)
COSMIC_BOTTOM = (9, 32, 54)
PORTAL_BG = (15, 9, 36)
PIXEL_DARK = (24, 14, 56)
PIXEL_MID = (48, 24, 104)
PIXEL_BRIGHT = (92, 44, 178)

MUSTARD_GOLD = (234, 170, 54)
MUSTARD_INK = (32, 20, 4)
DENIM_BLUE = (44, 102, 154)

PAPER_BG = (244, 243, 236)
PAPER_GRID = (186, 208, 228)
PAPER_BORDER = (255, 255, 255)
PAPER_INK = (15, 23, 42)
PAPER_MUTED = (51, 65, 85)

SOLE_CYAN = (45, 212, 238)
EMERALD = (16, 185, 129)
CORAL = (244, 63, 94)
TEXT_WHITE = (248, 250, 252)
TEXT_LIGHT = (218, 228, 242)


def format_human_week(week_label: str) -> str:
    """
    Converts internal date code like '2026-Nov-W3-Saturday' into a clean reader-facing
    week label like 'NOV 2026  •  WEEK 3'.
    """
    m = re.match(r"^(\d{4})-([A-Za-z]+)-W(\d+)", (week_label or "").strip())
    if m:
        year, month, wk = m.group(1), m.group(2).upper(), m.group(3)
        return f"{month} {year}  •  WEEK {wk}"
    return (week_label or "WEEKLY EDITION").upper()


def get_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    cache_key = (name, size)
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]
    font_map = {
        "black": [FONT_DIR_MONTSERRAT / "Montserrat-Black.otf", "Montserrat-Black.otf", "Montserrat-Black.ttf", "Montserrat-Bold.otf", "Montserrat-Bold.ttf", "LiberationSans-Bold.ttf"],
        "extrabold": [FONT_DIR_MONTSERRAT / "Montserrat-ExtraBold.otf", "Montserrat-ExtraBold.otf", "Montserrat-ExtraBold.ttf", "Montserrat-Bold.otf", "Montserrat-Bold.ttf", "LiberationSans-Bold.ttf"],
        "bold": [FONT_DIR_MONTSERRAT / "Montserrat-Bold.otf", "Montserrat-Bold.otf", "Montserrat-Bold.ttf", "LiberationSans-Bold.ttf"],
        "semibold": [FONT_DIR_MONTSERRAT / "Montserrat-SemiBold.otf", "Montserrat-SemiBold.otf", "Montserrat-SemiBold.ttf", "Montserrat-Bold.otf", "Montserrat-Bold.ttf", "LiberationSans-Bold.ttf"],
        "medium": [FONT_DIR_MONTSERRAT / "Montserrat-Medium.otf", "Montserrat-Medium.otf", "Montserrat-Medium.ttf", "Montserrat-Regular.otf", "Montserrat-Regular.ttf", "LiberationSans-Regular.ttf"],
        "regular": [FONT_DIR_MONTSERRAT / "Montserrat-Regular.otf", "Montserrat-Regular.otf", "Montserrat-Regular.ttf", "LiberationSans-Regular.ttf"],
        "italic": [FONT_DIR_MONTSERRAT / "Montserrat-Italic.otf", "Montserrat-Italic.otf", "Montserrat-Italic.ttf", "LiberationSans-Italic.ttf"],
        "serif_bold": [FONT_DIR_CALADEA / "Caladea-Bold.ttf", "Caladea-Bold.ttf", "LiberationSerif-Bold.ttf"],
        "serif_italic": [FONT_DIR_LIBERATION_SERIF / "LiberationSerif-Italic.ttf", "LiberationSerif-Italic.ttf", "Caladea-Italic.ttf"],
        "serif_regular": [FONT_DIR_LIBERATION_SERIF / "LiberationSerif-Regular.ttf", "LiberationSerif-Regular.ttf", "Caladea-Regular.ttf"],
    }
    candidates = font_map.get(name, font_map["regular"])
    for cand in candidates:
        if isinstance(cand, Path) and cand.exists():
            f = ImageFont.truetype(str(cand), size)
            _FONT_CACHE[cache_key] = f
            return f
        if isinstance(cand, str):
            matches = list(Path("/usr/share/fonts").rglob(cand))
            if matches:
                f = ImageFont.truetype(str(matches[0]), size)
                _FONT_CACHE[cache_key] = f
                return f
    return ImageFont.load_default()


def wrap_text_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    lines: List[str] = []
    for paragraph in (text or "").splitlines():
        words = paragraph.split()
        if not words:
            continue
        current = words[0]
        for word in words[1:]:
            test = f"{current} {word}"
            bbox = draw.textbbox((0, 0), test, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_fitted_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: Tuple[int, int, int, int],
    font_name: str,
    max_font_size: int,
    min_font_size: int,
    fill: Tuple[int, int, int],
    line_gap_ratio: float = 0.28,
    align: str = "left",
    valign: str = "top",
) -> int:
    """
    Auto-scales font size between `max_font_size` and `min_font_size` so that `text`
    always fits 100% inside `box = (x1, y1, x2, y2)` without overflowing.
    """
    x1, y1, x2, y2 = box
    max_w = max(40, x2 - x1)
    max_h = max(20, y2 - y1)

    chosen_font = get_font(font_name, min_font_size)
    chosen_lines: List[str] = []
    chosen_gap = 6
    chosen_total_h = 0

    for size in range(max_font_size, min_font_size - 1, -2):
        font = get_font(font_name, size)
        gap = max(4, int(size * line_gap_ratio))
        lines = wrap_text_lines(draw, text, font, max_w)
        total_h = 0
        for ln in lines:
            bb = draw.textbbox((0, 0), ln, font=font)
            total_h += (bb[3] - bb[1])
        if lines:
            total_h += gap * (len(lines) - 1)
        if total_h <= max_h:
            chosen_font = font
            chosen_lines = lines
            chosen_gap = gap
            chosen_total_h = total_h
            break
    else:
        chosen_font = get_font(font_name, min_font_size)
        chosen_gap = max(4, int(min_font_size * line_gap_ratio))
        all_lines = wrap_text_lines(draw, text, chosen_font, max_w)
        sample_bb = draw.textbbox((0, 0), "Ay", font=chosen_font)
        lh = max(12, sample_bb[3] - sample_bb[1])
        max_lines = max(1, (max_h + chosen_gap) // (lh + chosen_gap))
        chosen_lines = all_lines[:max_lines]
        if len(all_lines) > max_lines and chosen_lines:
            chosen_lines[-1] = chosen_lines[-1].rstrip(".,;:") + "..."
        chosen_total_h = len(chosen_lines) * lh + max(0, len(chosen_lines) - 1) * chosen_gap

    curr_y = y1
    if valign == "middle":
        curr_y = y1 + max(0, (max_h - chosen_total_h) // 2)

    for ln in chosen_lines:
        bb = draw.textbbox((0, 0), ln, font=chosen_font)
        lw = bb[2] - bb[0]
        lh = bb[3] - bb[1]
        dx = x1
        if align == "center":
            dx = x1 + (max_w - lw) // 2
        draw.text((dx, curr_y), ln, font=chosen_font, fill=fill)
        curr_y += lh + chosen_gap

    return curr_y


def shorten_sentence(text: str, max_words: int = 24) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    first_sent = re.split(r"(?<=[.!?])\s+", text)[0]
    words = first_sent.split()
    if len(words) <= max_words:
        return first_sent
    return " ".join(words[:max_words]).rstrip(".,;:") + "..."


def load_cached_frame(kind: str) -> Image.Image:
    """
    Loads pre-baked static 1080x1350 base frames (`base_cover_frame.png` / `base_inner_frame.png`)
    into RAM once and returns a fast `.copy()` per slide — avoiding repeated resizing,
    Gaussian blurs, and logo compositing on every run.
    """
    if kind not in _FRAME_CACHE:
        path = BASE_COVER_FRAME_PATH if kind == "cover" else BASE_INNER_FRAME_PATH
        if not path.exists():
            from build_static_assets import build_base_frames
            build_base_frames()
        _FRAME_CACHE[kind] = Image.open(path).convert("RGBA")
    return _FRAME_CACHE[kind].copy()


def create_authentic_blank_frame(week_display: str, seed: int = 1, show_top_week_pill: bool = True) -> Image.Image:
    """
    Fast O(1) copy of the pre-baked `assets/base_inner_frame.png` (exact torn edges +
    HD transparent SOLE & IGIT logos + @sole_igit footer) with the centered Week Edition badge.
    """
    frame = load_cached_frame("inner")
    if show_top_week_pill:
        draw = ImageDraw.Draw(frame)
        font = get_font("black", 16)
        txt = f"EDITION: {week_display}"
        bb = draw.textbbox((0, 0), txt, font=font)
        tw = bb[2] - bb[0]
        pw = tw + 36
        ph = 36
        px = (WIDTH - pw) // 2
        py = 152
        draw.rounded_rectangle([px - 2, py - 2, px + pw + 2, py + ph + 2], radius=12, fill=PAPER_BG)
        draw.rounded_rectangle([px, py, px + pw, py + ph], radius=10, fill=PORTAL_BG)
        draw.text((px + 18, py + 8), txt, font=font, fill=MUSTARD_GOLD)

    return frame


def render_cover_slide(
    edition_badge: str,
    week_display: str,
    hook_headline: str,
    sub_hook: str,
) -> Image.Image:
    """
    Slide 1: Fast copy of pre-baked `assets/base_cover_frame.png` + Centered Graph-Paper
    Curiosity Hook Card (`x = 165..915`, `y = 845..1175`).
    """
    canvas = load_cached_frame("cover")
    draw = ImageDraw.Draw(canvas)

    # 100% Centered Graph-Paper Curiosity Hook Card (x = 165..915, center = 540)
    card_box = (COL_X1, 845, COL_X2, 1175)
    draw_clean_graph_paper_card(canvas, card_box, accent_bar_color=MUSTARD_GOLD)

    full_badge = f"{edition_badge}  •  {week_display}"
    draw_inline_pill(
        draw,
        COL_X1 + COL_PAD,
        872,
        full_badge,
        bg_color=DENIM_BLUE,
        text_color=TEXT_WHITE,
        font_size=16,
        pad_x=16,
        pad_y=7,
        white_outline=False,
    )

    next_y = draw_fitted_text_block(
        draw,
        hook_headline,
        box=(COL_X1 + COL_PAD, 928, COL_X2 - COL_PAD, 1075),
        font_name="black",
        max_font_size=27,
        min_font_size=19,
        fill=PAPER_INK,
    )

    draw_fitted_text_block(
        draw,
        sub_hook,
        box=(COL_X1 + COL_PAD, max(1082, next_y + 8), COL_X2 - COL_PAD, 1158),
        font_name="extrabold",
        max_font_size=19,
        min_font_size=15,
        fill=PIXEL_BRIGHT,
    )

    return canvas


def draw_clean_purple_card(
    canvas: Image.Image,
    box: Tuple[int, int, int, int],
    border_color: Tuple[int, int, int] = SOLE_CYAN,
    seed: int = 1,
) -> None:
    x1, y1, x2, y2 = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([x1 + 6, y1 + 8, x2 + 6, y2 + 8], radius=24, fill=(2, 6, 14, 220))
    draw.rounded_rectangle([x1, y1, x2, y2], radius=24, fill=PORTAL_BG, outline=border_color, width=3)

    # Subtle decorative pixel blocks ONLY in the bottom-right corner rim
    rng = random.Random(seed * 131)
    p = 14
    for gx in range(x2 - 104, x2 - 18, p):
        for gy in range(y2 - 44, y2 - 16, p):
            if rng.random() < 0.55:
                draw.rectangle([gx, gy, gx + p - 2, gy + p - 2], fill=rng.choice([PIXEL_DARK, PIXEL_MID, PIXEL_BRIGHT]))


def draw_clean_graph_paper_card(
    canvas: Image.Image,
    box: Tuple[int, int, int, int],
    accent_bar_color: Tuple[int, int, int] = MUSTARD_GOLD,
) -> None:
    x1, y1, x2, y2 = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([x1 + 6, y1 + 8, x2 + 6, y2 + 8], radius=22, fill=(2, 6, 14, 220))
    draw.rounded_rectangle([x1, y1, x2, y2], radius=22, fill=PAPER_BG, outline=PAPER_BORDER, width=3)

    step = 28
    for gx in range(x1 + step, x2 - 10, step):
        draw.line([(gx, y1 + 14), (gx, y2 - 10)], fill=PAPER_GRID, width=1)
    for gy in range(y1 + step, y2 - 10, step):
        draw.line([(x1 + 10, gy), (x2 - 10, gy)], fill=PAPER_GRID, width=1)

    draw.rounded_rectangle([x1 + 3, y1 + 3, x2 - 3, y1 + 15], radius=8, fill=accent_bar_color)


def draw_inline_pill(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    bg_color: Tuple[int, int, int],
    text_color: Tuple[int, int, int],
    font_size: int = 18,
    pad_x: int = 18,
    pad_y: int = 8,
    white_outline: bool = True,
) -> Tuple[int, int]:
    font = get_font("black", font_size)
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    w = tw + pad_x * 2
    h = th + pad_y * 2 + 2

    if white_outline:
        draw.rounded_rectangle([x - 2, y - 2, x + w + 2, y + h + 2], radius=12, fill=PAPER_BG)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=bg_color)
    draw.text((x + pad_x, y + pad_y - 1), text, font=font, fill=text_color)
    return w, h


def draw_bottom_cliffhanger_bar(draw: ImageDraw.ImageDraw, hook_text: str, y: int = 1118) -> None:
    """
    100% Centered at `x = 165..915, y = 1118..1180` (dead center at x = 540,
    and clears both the bottom-left and bottom-right torn paper corners!).
    """
    x1, x2 = COL_X1, COL_X2
    h = 62
    draw.rounded_rectangle([x1 - 3, y - 3, x2 + 3, y + h + 3], radius=18, fill=PAPER_BG)
    draw.rounded_rectangle([x1, y, x2, y + h], radius=16, fill=MUSTARD_GOLD)

    draw_fitted_text_block(
        draw,
        hook_text.upper(),
        box=(x1 + 20, y + 8, x2 - 20, y + h - 8),
        font_name="black",
        max_font_size=18,
        min_font_size=14,
        fill=MUSTARD_INK,
        align="center",
        valign="middle",
    )


# ==============================================================================
# 1. WEEKLY NEWS HIGHLIGHTS (8-Slide Curiosity Flow: #10 -> #01)
# ==============================================================================

def render_news_dual_slide(
    item_a: Dict[str, Any],
    rank_a: int,
    item_b: Dict[str, Any],
    rank_b: int,
    week_display: str,
    seed: int,
    next_teaser: str,
) -> Image.Image:
    """
    Both cards are 100% horizontally centered (`x = 165..915`, center = 540):
    - Top Card: `x = 165..915, y = 210..632`
    - Bottom Card: `x = 165..915, y = 664..1086`
    - Cliffhanger Bar: `x = 165..915, y = 1118..1180`
    Zero relevance scores or source footers cluttering the cards!
    """
    canvas = create_authentic_blank_frame(week_display=week_display, seed=seed)
    draw = ImageDraw.Draw(canvas)

    # Top Centered Card (Story A)
    top_box = (COL_X1, 210, COL_X2, 632)
    draw_clean_purple_card(canvas, top_box, border_color=SOLE_CYAN, seed=rank_a)

    w_r1, _ = draw_inline_pill(draw, COL_X1 + COL_PAD, 236, f"HIGHLIGHT #{rank_a:02d}", bg_color=MUSTARD_GOLD, text_color=MUSTARD_INK, font_size=17, white_outline=False)
    cat_a = item_a.get("category", "NEWS").upper()
    draw_inline_pill(draw, COL_X1 + COL_PAD + w_r1 + 12, 236, cat_a, bg_color=DENIM_BLUE, text_color=TEXT_WHITE, font_size=15, white_outline=False)

    y_after_hl_a = draw_fitted_text_block(
        draw,
        item_a.get("headline", ""),
        box=(COL_X1 + COL_PAD, 294, COL_X2 - COL_PAD, 430),
        font_name="black",
        max_font_size=29,
        min_font_size=21,
        fill=TEXT_WHITE,
    )

    short_a = shorten_sentence(item_a.get("summary", ""), max_words=26)
    draw_fitted_text_block(
        draw,
        short_a,
        box=(COL_X1 + COL_PAD, max(442, y_after_hl_a + 12), COL_X2 - COL_PAD, 606),
        font_name="medium",
        max_font_size=22,
        min_font_size=17,
        fill=TEXT_LIGHT,
    )

    # Bottom Centered Card (Story B)
    bot_box = (COL_X1, 664, COL_X2, 1086)
    draw_clean_graph_paper_card(canvas, bot_box, accent_bar_color=DENIM_BLUE)

    w_r2, _ = draw_inline_pill(draw, COL_X1 + COL_PAD, 694, f"HIGHLIGHT #{rank_b:02d}", bg_color=PIXEL_BRIGHT, text_color=TEXT_WHITE, font_size=17, white_outline=False)
    cat_b = item_b.get("category", "NEWS").upper()
    draw_inline_pill(draw, COL_X1 + COL_PAD + w_r2 + 12, 694, cat_b, bg_color=MUSTARD_GOLD, text_color=MUSTARD_INK, font_size=15, white_outline=False)

    y_after_hl_b = draw_fitted_text_block(
        draw,
        item_b.get("headline", ""),
        box=(COL_X1 + COL_PAD, 752, COL_X2 - COL_PAD, 888),
        font_name="black",
        max_font_size=28,
        min_font_size=20,
        fill=PAPER_INK,
    )

    short_b = shorten_sentence(item_b.get("summary", ""), max_words=26)
    draw_fitted_text_block(
        draw,
        short_b,
        box=(COL_X1 + COL_PAD, max(900, y_after_hl_b + 12), COL_X2 - COL_PAD, 1062),
        font_name="semibold",
        max_font_size=21,
        min_font_size=16,
        fill=PAPER_MUTED,
    )

    draw_bottom_cliffhanger_bar(draw, next_teaser, y=1118)
    return canvas


def render_news_spotlight_slide(
    item: Dict[str, Any],
    rank: int,
    week_display: str,
    badge_label: str,
    next_teaser: str,
) -> Image.Image:
    """
    100% Centered Spotlight Slide for #02 and #01 (`x = 165..915`, center = 540):
    - Top Purple Card: `x = 165..915, y = 210..795`
    - Bottom Graph-Paper Takeaway Card: `x = 165..915, y = 825..1086`
    - Cliffhanger Bar: `x = 165..915, y = 1118..1180`
    """
    canvas = create_authentic_blank_frame(week_display=week_display, seed=rank * 99)
    draw = ImageDraw.Draw(canvas)

    draw_clean_purple_card(canvas, (COL_X1, 210, COL_X2, 795), border_color=MUSTARD_GOLD if rank == 1 else SOLE_CYAN, seed=rank + 50)

    draw_inline_pill(
        draw,
        COL_X1 + COL_PAD,
        238,
        f"HIGHLIGHT #{rank:02d}  •  {badge_label}",
        bg_color=MUSTARD_GOLD if rank == 1 else DENIM_BLUE,
        text_color=MUSTARD_INK if rank == 1 else TEXT_WHITE,
        font_size=17,
        white_outline=False,
    )

    cat = item.get("category", "TOP STORY").upper()
    draw.text((COL_X1 + COL_PAD, 298), f"CATEGORY: {cat}", font=get_font("extrabold", 18), fill=SOLE_CYAN)

    y_after_hl = draw_fitted_text_block(
        draw,
        item.get("headline", ""),
        box=(COL_X1 + COL_PAD, 336, COL_X2 - COL_PAD, 520),
        font_name="black",
        max_font_size=35,
        min_font_size=24,
        fill=TEXT_WHITE,
    )

    draw.rectangle([COL_X1 + COL_PAD, y_after_hl + 10, COL_X1 + COL_PAD + 170, y_after_hl + 16], fill=MUSTARD_GOLD)

    draw_fitted_text_block(
        draw,
        item.get("summary", ""),
        box=(COL_X1 + COL_PAD, y_after_hl + 34, COL_X2 - COL_PAD, 768),
        font_name="medium",
        max_font_size=24,
        min_font_size=17,
        fill=TEXT_LIGHT,
    )

    # Centered Bottom Graph-Paper Takeaway Card (x = 165..915, y = 825..1086)
    draw_clean_graph_paper_card(canvas, (COL_X1, 825, COL_X2, 1086), accent_bar_color=MUSTARD_GOLD)
    draw.text((COL_X1 + COL_PAD, 858), "WHY THIS MATTERS FOR US:", font=get_font("black", 19), fill=PIXEL_BRIGHT)

    if rank == 1:
        takeaway = "This took the #01 spot this week for its direct impact on campus innovation, students, and researchers. Swipe for the final 3-second poll!"
    elif rank == 2:
        takeaway = "One big story still beats this one. Ready for the #01 Highlight of the Week? Swipe right now to see what took the top spot."
    else:
        takeaway = f"{rank - 1} big stories still beat this one. Swipe right now for Highlight #{rank - 1:02d}!"
    draw_fitted_text_block(
        draw,
        takeaway,
        box=(COL_X1 + COL_PAD, 896, COL_X2 - COL_PAD, 1062),
        font_name="bold",
        max_font_size=22,
        min_font_size=17,
        fill=PAPER_INK,
    )

    draw_bottom_cliffhanger_bar(draw, next_teaser, y=1118)
    return canvas


# ==============================================================================
# 2. RANDOM FACT OF THE WEEK (4-Slide Mystery -> Setup -> Plot Twist -> Poll)
# ==============================================================================

def render_fact_carousel(item: Dict[str, Any], week_label: str) -> List[Image.Image]:
    week_display = format_human_week(week_label)
    title = item.get("title", "")
    fact_body = item.get("fact", "")
    context = item.get("context", "")
    cat = item.get("category", "FACT SPOTLIGHT").upper()

    source = item.get("source", "Archival Research")
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", fact_body) if s.strip()]
    context_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", context) if s.strip()]
    if len(sentences) > 1:
        setup_sent = sentences[0]
        twist_sent = " ".join(sentences[1:])
        why_text = context or f"Documented by {source}, showing why {cat.lower()} still surprises researchers today."
    elif len(context_sentences) > 1:
        setup_sent = fact_body
        twist_sent = context_sentences[0]
        why_text = " ".join(context_sentences[1:])
    else:
        setup_sent = fact_body
        twist_sent = context or fact_body
        why_text = f"Verified via {source}. A standout detail from {cat.lower()} that most textbooks leave out."

    s1 = render_cover_slide(
        edition_badge="FACT OF THE WEEK",
        week_display=week_display,
        hook_headline=f"MYSTERY: {title}",
        sub_hook="Most people only know half of this story. Swipe for the plot twist →",
    )

    # Slide 2: Part 1 — The Setup (Both cards centered at x = 165..915)
    s2 = create_authentic_blank_frame(week_display=week_display, seed=201)
    d2 = ImageDraw.Draw(s2)

    draw_clean_purple_card(s2, (COL_X1, 210, COL_X2, 632), border_color=SOLE_CYAN, seed=22)
    draw_inline_pill(d2, COL_X1 + COL_PAD, 236, "PART 1  •  THE SETUP", bg_color=MUSTARD_GOLD, text_color=MUSTARD_INK, font_size=18, white_outline=False)
    d2.text((COL_X1 + COL_PAD, 296), f"CATEGORY: {cat}", font=get_font("extrabold", 17), fill=SOLE_CYAN)
    draw_fitted_text_block(
        d2,
        title,
        box=(COL_X1 + COL_PAD, 332, COL_X2 - COL_PAD, 605),
        font_name="black",
        max_font_size=33,
        min_font_size=22,
        fill=TEXT_WHITE,
    )

    draw_clean_graph_paper_card(s2, (COL_X1, 664, COL_X2, 1086), accent_bar_color=DENIM_BLUE)
    d2.text((COL_X1 + COL_PAD, 700), "HOW IT STARTED:", font=get_font("black", 19), fill=DENIM_BLUE)
    draw_fitted_text_block(
        d2,
        setup_sent,
        box=(COL_X1 + COL_PAD, 740, COL_X2 - COL_PAD, 1060),
        font_name="bold",
        max_font_size=26,
        min_font_size=19,
        fill=PAPER_INK,
    )
    draw_bottom_cliffhanger_bar(d2, "WAIT... HERE IS THE PLOT TWIST NOBODY EXPECTS →", y=1118)

    # Slide 3: Part 2 — The Plot Twist (Both cards centered at x = 165..915)
    s3 = create_authentic_blank_frame(week_display=week_display, seed=202)
    d3 = ImageDraw.Draw(s3)

    draw_clean_graph_paper_card(s3, (COL_X1, 210, COL_X2, 632), accent_bar_color=CORAL)
    draw_inline_pill(d3, COL_X1 + COL_PAD, 238, "PART 2  •  THE PLOT TWIST", bg_color=CORAL, text_color=TEXT_WHITE, font_size=18, white_outline=False)
    draw_fitted_text_block(
        d3,
        twist_sent or fact_body,
        box=(COL_X1 + COL_PAD, 298, COL_X2 - COL_PAD, 605),
        font_name="black",
        max_font_size=28,
        min_font_size=20,
        fill=PAPER_INK,
    )

    draw_clean_purple_card(s3, (COL_X1, 664, COL_X2, 1086), border_color=MUSTARD_GOLD, seed=33)
    d3.text((COL_X1 + COL_PAD, 700), "WHY THIS MATTERS:", font=get_font("extrabold", 19), fill=MUSTARD_GOLD)
    draw_fitted_text_block(
        d3,
        why_text,
        box=(COL_X1 + COL_PAD, 742, COL_X2 - COL_PAD, 1060),
        font_name="medium",
        max_font_size=24,
        min_font_size=17,
        fill=TEXT_WHITE,
    )
    draw_bottom_cliffhanger_bar(d3, "FINAL SLIDE: QUICK 3-SECOND CAMPUS POLL →", y=1118)

    # Slide 4: Interactive Poll Outro
    s4 = render_interactive_outro_slide(
        week_display=week_display,
        headline_summary=f"Curated for the {week_display} edition of Bits -N- Bytes.",
        question_prompt="BE HONEST: Did you know this fact before swiping today?",
        options=[
            "A) Yes, I actually knew this one!",
            "B) No way — learned something new today",
            "C) Forwarding this to my batch group chat",
        ],
    )
    return [s1, s2, s3, s4]


# ==============================================================================
# 3. RANDOM VOCABULARY / THESAURUS (4-Slide POV -> Word Unlock -> Power Swaps)
# ==============================================================================

def render_vocab_carousel(item: Dict[str, Any], week_label: str) -> List[Image.Image]:
    week_display = format_human_week(week_label)
    word = item.get("word", "Vellichor")
    pron = item.get("pronunciation", "")
    pos = item.get("part_of_speech", "noun")
    defn = item.get("definition", "")
    example = item.get("example", "")
    syns = item.get("synonyms", [])[:4]
    ants = item.get("antonyms", [])[:3]
    etym = item.get("etymology", "")

    s1 = render_cover_slide(
        edition_badge="WORD OF THE WEEK",
        week_display=week_display,
        hook_headline=f"There's a single {len(word)}-letter English word for this exact feeling...",
        sub_hook="Bet you've felt it on campus, but never knew what to call it. Swipe →",
    )

    # Slide 2: Step 1 — The Relatable POV (Centered at x = 165..915)
    s2 = create_authentic_blank_frame(week_display=week_display, seed=301)
    d2 = ImageDraw.Draw(s2)

    draw_clean_graph_paper_card(s2, (COL_X1, 210, COL_X2, 648), accent_bar_color=DENIM_BLUE)
    draw_inline_pill(d2, COL_X1 + COL_PAD, 238, "STEP 1  •  HAVE YOU EVER FELT THIS?", bg_color=MUSTARD_GOLD, text_color=MUSTARD_INK, font_size=18, white_outline=False)
    d2.text((COL_X1 + COL_PAD, 298), "IMAGINE THIS MOMENT:", font=get_font("black", 19), fill=DENIM_BLUE)
    draw_fitted_text_block(
        d2,
        defn,
        box=(COL_X1 + COL_PAD, 336, COL_X2 - COL_PAD, 620),
        font_name="black",
        max_font_size=31,
        min_font_size=21,
        fill=PAPER_INK,
    )

    draw_clean_purple_card(s2, (COL_X1, 678, COL_X2, 1086), border_color=SOLE_CYAN, seed=44)
    d2.text((COL_X1 + COL_PAD, 714), "MOST PEOPLE TAKE 20 WORDS TO EXPLAIN THIS.", font=get_font("extrabold", 20), fill=SOLE_CYAN)
    first_letter = word[0].upper() if word else "?"
    draw_fitted_text_block(
        d2,
        f"Writers use just ONE {len(word)}-letter {pos} (starts with '{first_letter}'). Can you guess it before swiping to the next slide?",
        box=(COL_X1 + COL_PAD, 758, COL_X2 - COL_PAD, 1060),
        font_name="bold",
        max_font_size=26,
        min_font_size=19,
        fill=TEXT_WHITE,
    )
    draw_bottom_cliffhanger_bar(d2, f"SWIPE TO UNLOCK THE WORD (STARTS WITH '{first_letter}') →", y=1118)

    # Slide 3: Step 2 — Word Unlocked + IGIT Campus Usage (Centered at x = 165..915)
    s3 = create_authentic_blank_frame(week_display=week_display, seed=302)
    d3 = ImageDraw.Draw(s3)

    draw_clean_purple_card(s3, (COL_X1, 210, COL_X2, 648), border_color=MUSTARD_GOLD, seed=55)
    draw_inline_pill(d3, COL_X1 + COL_PAD, 236, "STEP 2  •  WORD UNLOCKED", bg_color=SOLE_CYAN, text_color=MUSTARD_INK, font_size=18, white_outline=False)

    max_word_w = COL_X2 - COL_X1 - 2 * COL_PAD
    word_upper = word.upper()
    f_word = get_font("black", 30)
    for sz in range(62, 29, -2):
        cand_font = get_font("black", sz)
        bb = d3.textbbox((0, 0), word_upper, font=cand_font)
        if (bb[2] - bb[0]) <= max_word_w:
            f_word = cand_font
            break
    d3.text((COL_X1 + COL_PAD + 5, 297), word_upper, font=f_word, fill=(6, 4, 16))
    d3.text((COL_X1 + COL_PAD, 292), word_upper, font=f_word, fill=MUSTARD_GOLD)
    d3.text((COL_X1 + COL_PAD, 376), f"{pron}   •   {pos.upper()}", font=get_font("serif_italic", 28), fill=SOLE_CYAN)

    draw_fitted_text_block(
        d3,
        defn,
        box=(COL_X1 + COL_PAD, 424, COL_X2 - COL_PAD, 622),
        font_name="semibold",
        max_font_size=22,
        min_font_size=17,
        fill=TEXT_WHITE,
    )

    draw_clean_graph_paper_card(s3, (COL_X1, 678, COL_X2, 1086), accent_bar_color=MUSTARD_GOLD)
    d3.text((COL_X1 + COL_PAD, 714), "HOW TO DROP IT IN A CONVERSATION AT IGIT:", font=get_font("black", 19), fill=PIXEL_BRIGHT)
    draw_fitted_text_block(
        d3,
        f"\"{example}\"",
        box=(COL_X1 + COL_PAD, 756, COL_X2 - COL_PAD, 1060),
        font_name="serif_italic",
        max_font_size=29,
        min_font_size=20,
        fill=PAPER_INK,
    )
    draw_bottom_cliffhanger_bar(d3, "LAST SLIDE: 4 POWER SWAPS & COMMENT CHALLENGE →", y=1118)

    # Slide 4: Step 3 — Thesaurus Power-Up + Comment Challenge (Centered at x = 165..915)
    s4 = create_authentic_blank_frame(week_display=week_display, seed=303)
    d4 = ImageDraw.Draw(s4)

    draw_clean_purple_card(s4, (COL_X1, 210, COL_X2, 725), border_color=SOLE_CYAN, seed=66)
    draw_inline_pill(d4, COL_X1 + COL_PAD, 236, "STEP 3  •  THESAURUS POWER-UP", bg_color=MUSTARD_GOLD, text_color=MUSTARD_INK, font_size=18, white_outline=False)

    d4.text((COL_X1 + COL_PAD, 296), "SIMILAR VIBES (SYNONYMS):", font=get_font("black", 19), fill=EMERALD)
    px_cursor, py_cursor = COL_X1 + COL_PAD, 332
    for syn in syns:
        syn_txt = syn.upper()
        syn_bb = d4.textbbox((0, 0), syn_txt, font=get_font("black", 16))
        est_w = (syn_bb[2] - syn_bb[0]) + 32
        if px_cursor > COL_X1 + COL_PAD and (px_cursor + est_w) > (COL_X2 - COL_PAD):
            px_cursor = COL_X1 + COL_PAD
            py_cursor += 50
        w_pill, _ = draw_inline_pill(d4, px_cursor, py_cursor, syn_txt, bg_color=DENIM_BLUE, text_color=TEXT_WHITE, font_size=16, pad_x=16, pad_y=7)
        px_cursor += w_pill + 14

    ant_heading_y = max(455, py_cursor + 56)
    d4.text((COL_X1 + COL_PAD, ant_heading_y), "EXACT OPPOSITES (ANTONYMS):", font=get_font("black", 19), fill=CORAL)
    px_cursor, py_ant = COL_X1 + COL_PAD, ant_heading_y + 37
    for ant in ants:
        ant_txt = ant.upper()
        ant_bb = d4.textbbox((0, 0), ant_txt, font=get_font("black", 16))
        est_w = (ant_bb[2] - ant_bb[0]) + 32
        if px_cursor > COL_X1 + COL_PAD and (px_cursor + est_w) > (COL_X2 - COL_PAD):
            px_cursor = COL_X1 + COL_PAD
            py_ant += 48
        w_pill, _ = draw_inline_pill(d4, px_cursor, py_ant, ant_txt, bg_color=(76, 22, 48), text_color=TEXT_WHITE, font_size=16, pad_x=16, pad_y=7)
        px_cursor += w_pill + 14

    if etym:
        draw_fitted_text_block(
            d4,
            f"ORIGIN: {etym}",
            box=(COL_X1 + COL_PAD, max(568, py_ant + 54), COL_X2 - COL_PAD, 706),
            font_name="medium",
            max_font_size=18,
            min_font_size=13,
            fill=TEXT_LIGHT,
        )

    draw_clean_graph_paper_card(s4, (COL_X1, 758, COL_X2, 1175), accent_bar_color=MUSTARD_GOLD)
    d4.text((COL_X1 + COL_PAD, 794), "5-SECOND COMMENT CHALLENGE:", font=get_font("black", 21), fill=PIXEL_BRIGHT)
    draw_fitted_text_block(
        d4,
        f"Write a short sentence using '{word}' in the comments below! Best line gets pinned by @sole_igit.",
        box=(COL_X1 + COL_PAD, 836, COL_X2 - COL_PAD, 1075),
        font_name="bold",
        max_font_size=25,
        min_font_size=18,
        fill=PAPER_INK,
    )
    draw_inline_pill(d4, COL_X1 + COL_PAD, 1106, "BOOKMARK THIS POST FOR LATER", bg_color=MUSTARD_GOLD, text_color=MUSTARD_INK, font_size=17, white_outline=False)

    return [s1, s2, s3, s4]


def render_interactive_outro_slide(
    week_display: str,
    headline_summary: str,
    question_prompt: str,
    options: List[str],
) -> Image.Image:
    """
    100% Centered Interactive Poll Slide (`x = 165..915`, center = 540):
    - Top Graph-Paper Poll Card: `x = 165..915, y = 210..845`
    - Bottom Purple CTA Card: `x = 165..915, y = 876..1175`
    """
    canvas = create_authentic_blank_frame(week_display=week_display, seed=999)
    draw = ImageDraw.Draw(canvas)

    draw_clean_graph_paper_card(canvas, (COL_X1, 210, COL_X2, 845), accent_bar_color=DENIM_BLUE)
    draw_inline_pill(
        draw,
        COL_X1 + COL_PAD,
        236,
        f"FINAL PAGE  •  3-SECOND CAMPUS POLL",
        bg_color=MUSTARD_GOLD,
        text_color=MUSTARD_INK,
        font_size=17,
        white_outline=False,
    )

    y_after_q = draw_fitted_text_block(
        draw,
        question_prompt,
        box=(COL_X1 + COL_PAD, 296, COL_X2 - COL_PAD, 445),
        font_name="black",
        max_font_size=28,
        min_font_size=20,
        fill=PAPER_INK,
    )

    opt_y = max(462, y_after_q + 14)
    for idx, opt in enumerate(options[:3]):
        bg = MUSTARD_GOLD if idx == 0 else (DENIM_BLUE if idx == 1 else PORTAL_BG)
        fg = MUSTARD_INK if idx == 0 else TEXT_WHITE
        draw.rounded_rectangle([COL_X1 + COL_PAD, opt_y, COL_X2 - COL_PAD, opt_y + 80], radius=16, fill=bg)
        draw_fitted_text_block(
            draw,
            opt,
            box=(COL_X1 + COL_PAD + 22, opt_y + 10, COL_X2 - COL_PAD - 22, opt_y + 70),
            font_name="extrabold",
            max_font_size=19,
            min_font_size=15,
            fill=fg,
            valign="middle",
        )
        opt_y += 96

    draw_clean_purple_card(canvas, (COL_X1, 876, COL_X2, 1175), border_color=SOLE_CYAN, seed=777)
    draw.text((COL_X1 + COL_PAD, 910), f"BITS -N- BYTES  •  {week_display}", font=get_font("black", 21), fill=SOLE_CYAN)
    draw_fitted_text_block(
        draw,
        f"{headline_summary}\nDrop your vote (A, B, or C) in the comments & hit SAVE so you can revisit this edition anytime.",
        box=(COL_X1 + COL_PAD, 952, COL_X2 - COL_PAD, 1152),
        font_name="semibold",
        max_font_size=20,
        min_font_size=16,
        fill=TEXT_WHITE,
    )
    return canvas


def export_canva_csv(
    content_type: str,
    selected_items: List[Dict[str, Any]],
    week_label: str,
    out_dir: Path,
) -> Path:
    csv_path = out_dir / "canva_autofill.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if content_type == "news":
            writer = csv.DictWriter(f, fieldnames=["rank", "category", "headline", "summary", "source", "url", "relevance_score", "popularity_score", "week_label"])
            writer.writeheader()
            for idx, item in enumerate(selected_items, 1):
                writer.writerow({
                    "rank": f"#{idx:02d}",
                    "category": item.get("category", "News"),
                    "headline": item.get("headline", ""),
                    "summary": item.get("summary", ""),
                    "source": item.get("source", ""),
                    "url": item.get("url", ""),
                    "relevance_score": item.get("relevance_score", 9.0),
                    "popularity_score": item.get("popularity_score", 9.0),
                    "week_label": week_label,
                })
        elif content_type == "facts":
            writer = csv.DictWriter(f, fieldnames=["category", "title", "fact", "context", "source", "week_label"])
            writer.writeheader()
            for item in selected_items:
                writer.writerow({
                    "category": item.get("category", "Fact"),
                    "title": item.get("title", ""),
                    "fact": item.get("fact", ""),
                    "context": item.get("context", ""),
                    "source": item.get("source", ""),
                    "week_label": week_label,
                })
        else:
            writer = csv.DictWriter(f, fieldnames=["word", "pronunciation", "part_of_speech", "definition", "example", "synonyms", "antonyms", "week_label"])
            writer.writeheader()
            for item in selected_items:
                writer.writerow({
                    "word": item.get("word", ""),
                    "pronunciation": item.get("pronunciation", ""),
                    "part_of_speech": item.get("part_of_speech", ""),
                    "definition": item.get("definition", ""),
                    "example": item.get("example", ""),
                    "synonyms": ", ".join(item.get("synonyms", [])),
                    "antonyms": ", ".join(item.get("antonyms", [])),
                    "week_label": week_label,
                })

    return csv_path


def render_package_designs(
    content_type: str,
    selected_items: List[Dict[str, Any]],
    week_label: str,
    out_dir: Path,
) -> Dict[str, Any]:
    slides_dir = out_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)
    for old_img in list(slides_dir.glob("slide_*.png")) + list(slides_dir.glob("slide_*.jpg")):
        old_img.unlink()

    week_display = format_human_week(week_label)
    rendered_images: List[Image.Image] = []

    if content_type == "news":
        items = list(selected_items[:10])
        if len(items) < 3:
            raise RuntimeError(f"Need at least 3 unique news items to render carousel, got {len(items)}")

        total_n = len(items)
        top1 = items[0]
        top2 = items[1]
        top3 = items[2]

        s1 = render_cover_slide(
            edition_badge="WEEKLY NEWS HIGHLIGHTS",
            week_display=week_display,
            hook_headline=f"{total_n} big stories this week. Wait till you see #01 ({top1.get('category', 'Campus')}):",
            sub_hook=f"\"{top1.get('headline', '')}\" - Swipe through all {total_n} highlights →",
        )
        rendered_images.append(s1)

        # Pair remaining stories (indices total_n-1 down to 2) without duplicating any story
        rem_indices = list(range(total_n - 1, 1, -1))
        seed_val = 20
        pos = 0
        while pos < len(rem_indices):
            if pos + 1 < len(rem_indices):
                idx_a = rem_indices[pos]
                idx_b = rem_indices[pos + 1]
                rank_a, rank_b = idx_a + 1, idx_b + 1
                next_pos = pos + 2
                if next_pos + 1 < len(rem_indices):
                    n_a, n_b = rem_indices[next_pos], rem_indices[next_pos + 1]
                    teaser = f"NEXT (#{n_a + 1:02d} & #{n_b + 1:02d}): {items[n_a].get('headline', '')} →"
                elif next_pos < len(rem_indices):
                    n_a = rem_indices[next_pos]
                    teaser = f"NEXT (#{n_a + 1:02d} HIGHLIGHT): {items[n_a].get('headline', '')} →"
                else:
                    teaser = f"NEXT (#02 HIGHLIGHT): {top2.get('headline', '')} →"
                rendered_images.append(
                    render_news_dual_slide(
                        items[idx_a],
                        rank_a,
                        items[idx_b],
                        rank_b,
                        week_display,
                        seed_val,
                        teaser,
                    )
                )
                seed_val += 10
                pos += 2
            else:
                idx_single = rem_indices[pos]
                rendered_images.append(
                    render_news_spotlight_slide(
                        items[idx_single],
                        rank=idx_single + 1,
                        week_display=week_display,
                        badge_label="WEEKLY NEWS HIGHLIGHT",
                        next_teaser=f"NEXT (#02 HIGHLIGHT): {top2.get('headline', '')} →",
                    )
                )
                pos += 1

        s_top2 = render_news_spotlight_slide(
            top2,
            rank=2,
            week_display=week_display,
            badge_label="WEEKLY NEWS HIGHLIGHT",
            next_teaser=f"NEXT SLIDE: THE #01 HIGHLIGHT OF THE WEEK ({top1.get('category', 'SPOTLIGHT')}) →",
        )
        rendered_images.append(s_top2)

        s_top1 = render_news_spotlight_slide(
            top1,
            rank=1,
            week_display=week_display,
            badge_label="MOST IMPORTANT HIGHLIGHT OF THE WEEK",
            next_teaser="FINAL SLIDE: CAST YOUR VOTE IN THIS WEEK'S 3-SECOND POLL →",
        )
        rendered_images.append(s_top1)

        s_outro = render_interactive_outro_slide(
            week_display=week_display,
            headline_summary=f"Curated for the {week_display} edition of Bits -N- Bytes.",
            question_prompt="Which of this week's Top 3 news highlights is the biggest deal?",
            options=[
                f"A) #01: {top1.get('headline', '')}",
                f"B) #02: {top2.get('headline', '')}",
                f"C) #03: {top3.get('headline', '')}",
            ],
        )
        rendered_images.append(s_outro)

    elif content_type == "facts":
        rendered_images = render_fact_carousel(selected_items[0], week_label)
    elif content_type == "vocab":
        rendered_images = render_vocab_carousel(selected_items[0], week_label)
    else:
        raise ValueError(f"Unknown content_type: {content_type}")

    slide_paths: List[str] = []
    rgb_images: List[Image.Image] = []
    for idx, img in enumerate(rendered_images, 1):
        rgb = img.convert("RGB")
        rgb_images.append(rgb)
        # High-quality 4:4:4 JPEG (zero chroma subsampling blur, 4x faster Gmail SMTP & smaller storage)
        p = slides_dir / f"slide_{idx:02d}.jpg"
        rgb.save(p, format="JPEG", quality=92, subsampling=0, optimize=True)
        slide_paths.append(str(p))

    pdf_title_map = {
        "news": "Weekly_News_Highlights",
        "facts": "Random_Fact",
        "vocab": "Random_Vocabulary",
    }
    safe_date = re.sub(r"[^A-Za-z0-9_-]+", "_", (week_label or "Edition").strip())
    pdf_filename = f"{safe_date}_{pdf_title_map.get(content_type, content_type.title())}.pdf"
    pdf_path = out_dir / pdf_filename
    for old_pdf in out_dir.glob("*.pdf"):
        if old_pdf != pdf_path:
            old_pdf.unlink(missing_ok=True)
    if rgb_images:
        rgb_images[0].save(
            pdf_path,
            format="PDF",
            resolution=110.0,
            quality=85,
            save_all=True,
            append_images=rgb_images[1:],
        )

    csv_path = export_canva_csv(content_type, selected_items, week_label, out_dir)

    return {
        "slide_count": len(slide_paths),
        "slide_paths": slide_paths,
        "carousel_pdf_name": pdf_filename,
        "carousel_pdf_path": str(pdf_path),
        "canva_csv_path": str(csv_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render SOLE Bits & Bytes Centered Authentic Zine Graphics")
    parser.add_argument("--type", choices=["news", "facts", "vocab"], required=True)
    parser.add_argument("--input", required=True, help="JSON file containing selected items")
    parser.add_argument("--week-label", required=True, help="Formatted date label e.g. 2026-Nov-W3-Saturday")
    parser.add_argument("--out-dir", required=True, help="Output folder for 1080x1350 JPGs, dated Carousel PDF, and Canva CSV")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else data.get("selected", data.get("items", []))
    res = render_package_designs(args.type, items, args.week_label, Path(args.out_dir))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
