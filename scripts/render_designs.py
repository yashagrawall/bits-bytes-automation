#!/usr/bin/env python3
"""
Branded Graphic & Carousel Design Engine for SOLE Bits & Bytes (IGIT Sarang).
Renders 1080x1350 (4:5 Instagram Portrait) PNG slides, a multi-page LinkedIn Carousel PDF,
a Canva Bulk-Create CSV (for the `canva-bulk-create` skill), and a Google Slides batch JSON
(for the `gslides` CLI).
"""

import argparse
import csv
import json
import math
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_DIR = Path("/home/yashagrawall/bits-bytes-automation")
SOLE_LOGO_PATH = BASE_DIR / "SOLE Logo.png"
IGIT_LOGO_PATH = BASE_DIR / "IGIT Sarang Logo.webp"

FONT_DIR_MONTSERRAT = Path("/usr/share/fonts/julietaula-montserrat-fonts")
FONT_DIR_CALADEA = Path("/usr/share/fonts/google-crosextra-caladea-fonts")
FONT_DIR_LIBERATION_SERIF = Path("/usr/share/fonts/liberation-serif-fonts")

WIDTH = 1080
HEIGHT = 1350

# Color Palette matched to SOLE Logo (#0887A8 cyan-teal on deep obsidian)
BG_TOP = (7, 12, 20)
BG_BOTTOM = (13, 25, 43)
CARD_BG = (17, 30, 50)
CARD_BG_ALT = (22, 38, 62)
CARD_BORDER = (34, 62, 96)
SOLE_TEAL = (8, 135, 168)
SOLE_CYAN = (34, 211, 238)
GOLD_ACCENT = (245, 158, 11)
EMERALD_ACCENT = (16, 185, 129)
CORAL_ACCENT = (244, 63, 94)
TEXT_WHITE = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)
TEXT_LIGHT = (203, 213, 225)


def get_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    font_map = {
        "black": FONT_DIR_MONTSERRAT / "Montserrat-Black.otf",
        "extrabold": FONT_DIR_MONTSERRAT / "Montserrat-ExtraBold.otf",
        "bold": FONT_DIR_MONTSERRAT / "Montserrat-Bold.otf",
        "semibold": FONT_DIR_MONTSERRAT / "Montserrat-SemiBold.otf",
        "medium": FONT_DIR_MONTSERRAT / "Montserrat-Medium.otf",
        "regular": FONT_DIR_MONTSERRAT / "Montserrat-Regular.otf",
        "italic": FONT_DIR_MONTSERRAT / "Montserrat-Italic.otf",
        "serif_bold": FONT_DIR_CALADEA / "Caladea-Bold.ttf",
        "serif_italic": FONT_DIR_LIBERATION_SERIF / "LiberationSerif-Italic.ttf",
        "serif_regular": FONT_DIR_LIBERATION_SERIF / "LiberationSerif-Regular.ttf",
    }
    path = font_map.get(name, font_map["regular"])
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def create_background() -> Image.Image:
    """Creates a rich obsidian-to-navy vertical gradient canvas with subtle geometric grid accents."""
    base = Image.new("RGBA", (WIDTH, HEIGHT), BG_TOP + (255,))
    draw = ImageDraw.Draw(base)

    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))

    # Subtle glowing orb in top-right and bottom-left
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([WIDTH - 380, -180, WIDTH + 220, 420], fill=(8, 135, 168, 48))
    gdraw.ellipse([-220, HEIGHT - 420, 380, HEIGHT + 180], fill=(8, 135, 168, 38))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=90))
    base = Image.alpha_composite(base, glow)

    # Subtle architectural grid lines
    grid_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid_overlay)
    for x in range(60, WIDTH, 120):
        grid_draw.line([(x, 0), (x, HEIGHT)], fill=(255, 255, 255, 7), width=1)
    for y in range(60, HEIGHT, 120):
        grid_draw.line([(0, y), (WIDTH, y)], fill=(255, 255, 255, 7), width=1)
    base = Image.alpha_composite(base, grid_overlay)
    return base


def prepare_circular_logo(path: Path, size: int, bg_color: Tuple[int, int, int, int]) -> Image.Image:
    """Loads a logo and frames it inside a clean circular badge with a subtle cyan ring."""
    badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(badge)
    bdraw.ellipse([0, 0, size - 1, size - 1], fill=bg_color, outline=SOLE_CYAN + (200,), width=2)

    if not path.exists():
        return badge

    img = Image.open(path).convert("RGBA")
    inner = int(size * 0.80)
    img.thumbnail((inner, inner), Image.Resampling.LANCZOS)

    mask = Image.new("L", img.size, 255)
    offset_x = (size - img.width) // 2
    offset_y = (size - img.height) // 2
    badge.paste(img, (offset_x, offset_y), img)
    return badge


def draw_header_and_footer(
    canvas: Image.Image,
    slide_num: int,
    total_slides: int,
    week_label: str,
    content_badge_text: str,
) -> None:
    draw = ImageDraw.Draw(canvas)

    # Top accent bar
    draw.rectangle([0, 0, WIDTH, 8], fill=SOLE_CYAN)

    # Logos
    igit_badge = prepare_circular_logo(IGIT_LOGO_PATH, 74, (255, 255, 255, 245))
    sole_badge = prepare_circular_logo(SOLE_LOGO_PATH, 74, (5, 8, 14, 255))

    canvas.paste(igit_badge, (64, 44), igit_badge)
    canvas.paste(sole_badge, (150, 44), sole_badge)

    f_club = get_font("extrabold", 21)
    f_sub = get_font("semibold", 15)
    draw.text((240, 52), "SOLE  |  IGIT SARANG", font=f_club, fill=TEXT_WHITE)
    draw.text((240, 82), f"BITS & BYTES  •  {content_badge_text.upper()}", font=f_sub, fill=SOLE_CYAN)

    # Slide counter pill on top-right
    pill_w, pill_h = 128, 46
    pill_x, pill_y = WIDTH - 64 - pill_w, 56
    draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=23,
        fill=CARD_BG_ALT,
        outline=SOLE_TEAL,
        width=2,
    )
    f_count = get_font("bold", 19)
    count_str = f"{slide_num:02d} / {total_slides:02d}"
    bbox = draw.textbbox((0, 0), count_str, font=f_count)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(
        (pill_x + (pill_w - tw) // 2, pill_y + (pill_h - th) // 2 - 2),
        count_str,
        font=f_count,
        fill=TEXT_WHITE,
    )

    # Header divider line
    draw.line([(64, 142), (WIDTH - 64, 142)], fill=CARD_BORDER, width=2)

    # Footer divider line
    footer_y = HEIGHT - 96
    draw.line([(64, footer_y), (WIDTH - 64, footer_y)], fill=CARD_BORDER, width=2)

    f_foot = get_font("semibold", 18)
    draw.text((64, footer_y + 28), f"@sole_igit  •  {week_label}", font=f_foot, fill=TEXT_MUTED)

    cta_text = "SWIPE FOR MORE  →" if slide_num < total_slides else "FOLLOW @SOLE_IGIT"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=f_foot)
    cta_w = cta_bbox[2] - cta_bbox[0]
    draw.text((WIDTH - 64 - cta_w, footer_y + 28), cta_text, font=f_foot, fill=SOLE_CYAN)


def wrap_text_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    words = text.split()
    if not words:
        return []
    lines = []
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


def draw_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    max_width: int,
    line_gap: int = 12,
    max_lines: int = 10,
) -> int:
    lines = wrap_text_lines(draw, text, font, max_width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".") + "..."
    curr_y = y
    for line in lines:
        draw.text((x, curr_y), line, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), line, font=font)
        curr_y += (bbox[3] - bbox[1]) + line_gap
    return curr_y


def render_news_cover_slide(selected_news: List[Dict[str, Any]], week_label: str, total_slides: int) -> Image.Image:
    canvas = create_background()
    draw_header_and_footer(canvas, 1, total_slides, week_label, "Weekly News Digest")
    draw = ImageDraw.Draw(canvas)

    # Category pill
    draw.rounded_rectangle([64, 185, 410, 235], radius=25, fill=SOLE_TEAL)
    draw.text((88, 198), "WEEKLY EDITION  •  TOP 10", font=get_font("extrabold", 18), fill=TEXT_WHITE)

    # Big Hero Title
    f_hero = get_font("black", 68)
    draw.text((64, 265), "WEEKLY TOP 10", font=f_hero, fill=TEXT_WHITE)
    draw.text((64, 345), "NEWS HIGHLIGHTS", font=f_hero, fill=SOLE_CYAN)

    f_desc = get_font("medium", 24)
    draw_multiline(
        draw,
        "Curated by Bits & Bytes (SOLE, IGIT Sarang) - ranked on student relevance, global impact, and verified primary sources.",
        64,
        445,
        f_desc,
        TEXT_LIGHT,
        WIDTH - 128,
        line_gap=10,
    )

    # Preview table card of top 5 headlines on cover
    card_top = 545
    card_bottom = HEIGHT - 135
    draw.rounded_rectangle(
        [64, card_top, WIDTH - 64, card_bottom],
        radius=28,
        fill=CARD_BG,
        outline=CARD_BORDER,
        width=2,
    )
    draw.rectangle([64, card_top + 28, 72, card_bottom - 28], fill=SOLE_CYAN)

    draw.text((104, card_top + 32), "INSIDE THIS WEEK'S BRIEFING:", font=get_font("extrabold", 21), fill=GOLD_ACCENT)

    y_cursor = card_top + 82
    f_num = get_font("black", 24)
    f_hl = get_font("semibold", 22)
    f_src = get_font("medium", 16)

    for idx, item in enumerate(selected_news[:5], 1):
        if y_cursor > card_bottom - 95:
            break
        draw.rounded_rectangle([104, y_cursor, 156, y_cursor + 40], radius=10, fill=SOLE_TEAL)
        draw.text((115, y_cursor + 7), f"#{idx:02d}", font=f_num, fill=TEXT_WHITE)

        hl_lines = wrap_text_lines(draw, item.get("headline", ""), f_hl, WIDTH - 295)
        first_line = hl_lines[0] if hl_lines else ""
        if len(hl_lines) > 1:
            first_line = first_line + "..."
        draw.text((174, y_cursor + 2), first_line, font=f_hl, fill=TEXT_WHITE)
        draw.text((174, y_cursor + 32), f"Source: {item.get('source', 'Verified')}", font=f_src, fill=SOLE_CYAN)
        y_cursor += 88

    draw.text(
        (104, card_bottom - 48),
        f"+ {max(0, len(selected_news) - 5)} more verified stories inside  •  Swipe left to read all 10",
        font=get_font("bold", 19),
        fill=TEXT_MUTED,
    )
    return canvas


def render_news_item_slide(
    item: Dict[str, Any],
    rank: int,
    slide_num: int,
    total_slides: int,
    week_label: str,
) -> Image.Image:
    canvas = create_background()
    draw_header_and_footer(canvas, slide_num, total_slides, week_label, "Weekly Top 10 News")
    draw = ImageDraw.Draw(canvas)

    # Rank badge + Category Pill
    draw.rounded_rectangle([64, 185, 220, 265], radius=20, fill=SOLE_TEAL)
    draw.text((90, 203), f"#{rank:02d}", font=get_font("black", 44), fill=TEXT_WHITE)

    category = item.get("category", "GLOBAL & TECH").upper()
    draw.rounded_rectangle([240, 198, 240 + max(240, len(category) * 16 + 48), 252], radius=27, fill=CARD_BG_ALT, outline=SOLE_CYAN, width=2)
    draw.text((264, 214), category, font=get_font("bold", 20), fill=SOLE_CYAN)

    # Main Content Card
    card_top = 300
    card_bottom = HEIGHT - 140
    draw.rounded_rectangle(
        [64, card_top, WIDTH - 64, card_bottom],
        radius=32,
        fill=CARD_BG,
        outline=CARD_BORDER,
        width=2,
    )
    # Accent top bar on card
    draw.rounded_rectangle([64, card_top, WIDTH - 64, card_top + 12], radius=6, fill=SOLE_CYAN)

    # Headline
    f_headline = get_font("extrabold", 42)
    next_y = draw_multiline(
        draw,
        item.get("headline", ""),
        108,
        card_top + 56,
        f_headline,
        TEXT_WHITE,
        WIDTH - 216,
        line_gap=14,
        max_lines=5,
    )

    # Accent divider
    draw.rectangle([108, next_y + 24, 268, next_y + 30], fill=GOLD_ACCENT)

    # Summary / Story Body
    f_body = get_font("medium", 27)
    body_y = draw_multiline(
        draw,
        item.get("summary", ""),
        108,
        next_y + 62,
        f_body,
        TEXT_LIGHT,
        WIDTH - 216,
        line_gap=16,
        max_lines=9,
    )

    # Bottom metadata panel inside card (Source + Relevance/Popularity Rating)
    meta_top = card_bottom - 175
    draw.rounded_rectangle(
        [104, meta_top, WIDTH - 104, card_bottom - 36],
        radius=20,
        fill=CARD_BG_ALT,
        outline=CARD_BORDER,
        width=1,
    )
    draw.text((134, meta_top + 24), "PRIMARY SOURCE", font=get_font("bold", 15), fill=TEXT_MUTED)
    draw.text((134, meta_top + 50), str(item.get("source", "Verified News Wire")), font=get_font("extrabold", 24), fill=SOLE_CYAN)
    url_display = str(item.get("url", ""))
    if len(url_display) > 52:
        url_display = url_display[:49] + "..."
    draw.text((134, meta_top + 88), url_display, font=get_font("regular", 16), fill=TEXT_MUTED)

    # Score pills on right side of metadata panel
    rel = item.get("relevance_score", 9.0)
    pop = item.get("popularity_score", 9.0)
    score_box_x = WIDTH - 370
    draw.rounded_rectangle([score_box_x, meta_top + 24, WIDTH - 130, meta_top + 64], radius=12, fill=(10, 46, 38), outline=EMERALD_ACCENT, width=2)
    draw.text((score_box_x + 18, meta_top + 33), f"RELEVANCE: {rel}/10", font=get_font("bold", 17), fill=EMERALD_ACCENT)

    draw.rounded_rectangle([score_box_x, meta_top + 76, WIDTH - 130, meta_top + 116], radius=12, fill=(52, 36, 10), outline=GOLD_ACCENT, width=2)
    draw.text((score_box_x + 18, meta_top + 85), f"POPULARITY: {pop}/10", font=get_font("bold", 17), fill=GOLD_ACCENT)

    return canvas


def render_fact_slide(item: Dict[str, Any], slide_num: int, total_slides: int, week_label: str) -> Image.Image:
    canvas = create_background()
    draw_header_and_footer(canvas, slide_num, total_slides, week_label, "Random Fact of the Week")
    draw = ImageDraw.Draw(canvas)

    # Top badge (auto-sized width)
    badge_txt = "DID YOU KNOW?  •  FACT SPOTLIGHT"
    f_badge = get_font("black", 19)
    b_bbox = draw.textbbox((0, 0), badge_txt, font=f_badge)
    draw.rounded_rectangle([64, 185, 64 + (b_bbox[2] - b_bbox[0]) + 56, 240], radius=27, fill=GOLD_ACCENT)
    draw.text((92, 201), badge_txt, font=f_badge, fill=(10, 15, 24))

    # Main Fact Card
    card_top = 275
    card_bottom = HEIGHT - 140
    draw.rounded_rectangle([64, card_top, WIDTH - 64, card_bottom], radius=32, fill=CARD_BG, outline=SOLE_TEAL, width=2)

    category = item.get("category", "SCIENCE & LITERATURE").upper()
    draw.text((108, card_top + 42), f"CATEGORY: {category}", font=get_font("bold", 19), fill=SOLE_CYAN)

    # Fact Title
    f_title = get_font("black", 42)
    y_after_title = draw_multiline(
        draw,
        item.get("title", "Random Fact of the Week"),
        108,
        card_top + 82,
        f_title,
        TEXT_WHITE,
        WIDTH - 216,
        line_gap=10,
        max_lines=3,
    )

    draw.rectangle([108, y_after_title + 16, 280, y_after_title + 22], fill=GOLD_ACCENT)

    # Main Fact Text
    f_fact = get_font("serif_bold", 30)
    y_after_fact = draw_multiline(
        draw,
        item.get("fact", ""),
        108,
        y_after_title + 44,
        f_fact,
        TEXT_WHITE,
        WIDTH - 216,
        line_gap=12,
        max_lines=6,
    )

    # Deeper Context Box
    if item.get("context"):
        ctx_top = y_after_fact + 24
        ctx_bottom = card_bottom - 125
        draw.rounded_rectangle([108, ctx_top, WIDTH - 108, ctx_bottom], radius=20, fill=CARD_BG_ALT, outline=CARD_BORDER, width=1)
        draw.text((136, ctx_top + 18), "WHY IT MATTERS", font=get_font("extrabold", 16), fill=GOLD_ACCENT)
        draw_multiline(
            draw,
            item.get("context", ""),
            136,
            ctx_top + 48,
            get_font("medium", 21),
            TEXT_LIGHT,
            WIDTH - 272,
            line_gap=10,
            max_lines=4,
        )

    # Source footer inside card
    draw.text((108, card_bottom - 95), f"VERIFIED SOURCE: {item.get('source', 'Archival Research')}", font=get_font("bold", 19), fill=SOLE_CYAN)
    rel = item.get("relevance_score", 9.5)
    pop = item.get("popularity_score", 9.5)
    draw.text((108, card_bottom - 58), f"Relevance Rating: {rel}/10   •   Popularity Rating: {pop}/10", font=get_font("medium", 17), fill=TEXT_MUTED)
    return canvas


def render_vocab_slide(item: Dict[str, Any], slide_num: int, total_slides: int, week_label: str) -> Image.Image:
    canvas = create_background()
    draw_header_and_footer(canvas, slide_num, total_slides, week_label, "Vocabulary & Thesaurus")
    draw = ImageDraw.Draw(canvas)

    # Badge (auto-sized width)
    badge_txt = "WORD OF THE WEEK  •  THESAURUS"
    f_badge = get_font("extrabold", 19)
    b_bbox = draw.textbbox((0, 0), badge_txt, font=f_badge)
    draw.rounded_rectangle([64, 185, 64 + (b_bbox[2] - b_bbox[0]) + 56, 240], radius=27, fill=SOLE_TEAL)
    draw.text((92, 201), badge_txt, font=f_badge, fill=TEXT_WHITE)

    card_top = 275
    card_bottom = HEIGHT - 140
    draw.rounded_rectangle([64, card_top, WIDTH - 64, card_bottom], radius=32, fill=CARD_BG, outline=CARD_BORDER, width=2)

    # Word + Pronunciation + Part of Speech
    word = item.get("word", "")
    pronunciation = item.get("pronunciation", "")
    pos = item.get("part_of_speech", "noun")

    draw.text((108, card_top + 48), word, font=get_font("black", 64), fill=TEXT_WHITE)
    phonetic_line = f"{pronunciation}   •   {pos.upper()}" if pronunciation else pos.upper()
    draw.text((108, card_top + 132), phonetic_line, font=get_font("serif_italic", 28), fill=SOLE_CYAN)

    draw.rectangle([108, card_top + 182, 280, card_top + 188], fill=GOLD_ACCENT)

    # Definition
    draw.text((108, card_top + 212), "DEFINITION", font=get_font("extrabold", 18), fill=GOLD_ACCENT)
    y_after_def = draw_multiline(
        draw,
        item.get("definition", ""),
        108,
        card_top + 244,
        get_font("semibold", 30),
        TEXT_WHITE,
        WIDTH - 216,
        line_gap=12,
        max_lines=4,
    )

    # Example Sentence Box
    ex_top = y_after_def + 28
    ex_bottom = ex_top + 175
    draw.rounded_rectangle([108, ex_top, WIDTH - 108, ex_bottom], radius=20, fill=CARD_BG_ALT, outline=SOLE_TEAL, width=1)
    draw.text((136, ex_top + 20), "USAGE IN CONTEXT", font=get_font("bold", 16), fill=SOLE_CYAN)
    draw_multiline(
        draw,
        f"\"{item.get('example', '')}\"",
        136,
        ex_top + 52,
        get_font("serif_italic", 25),
        TEXT_LIGHT,
        WIDTH - 272,
        line_gap=10,
        max_lines=3,
    )

    # Synonyms & Antonyms section
    syn_top = ex_bottom + 28
    syns = ", ".join(item.get("synonyms", [])[:5]) or "N/A"
    ants = ", ".join(item.get("antonyms", [])[:4]) or "N/A"

    draw.text((108, syn_top), "SYNONYMS:", font=get_font("extrabold", 19), fill=EMERALD_ACCENT)
    draw.text((260, syn_top), syns, font=get_font("semibold", 21), fill=TEXT_WHITE)

    draw.text((108, syn_top + 42), "ANTONYMS:", font=get_font("extrabold", 19), fill=CORAL_ACCENT)
    draw.text((260, syn_top + 42), ants, font=get_font("semibold", 21), fill=TEXT_LIGHT)

    if item.get("etymology"):
        draw_multiline(
            draw,
            f"ETYMOLOGY: {item.get('etymology')}",
            108,
            syn_top + 92,
            get_font("regular", 18),
            TEXT_MUTED,
            WIDTH - 216,
            line_gap=8,
            max_lines=3,
        )

    return canvas


def render_cta_closing_slide(content_type: str, slide_num: int, total_slides: int, week_label: str) -> Image.Image:
    canvas = create_background()
    draw_header_and_footer(canvas, slide_num, total_slides, week_label, "Bits & Bytes SOLE")
    draw = ImageDraw.Draw(canvas)

    card_top = 240
    card_bottom = HEIGHT - 160
    draw.rounded_rectangle([64, card_top, WIDTH - 64, card_bottom], radius=36, fill=CARD_BG, outline=SOLE_CYAN, width=2)

    sole_big = prepare_circular_logo(SOLE_LOGO_PATH, 180, (5, 8, 14, 255))
    igit_big = prepare_circular_logo(IGIT_LOGO_PATH, 180, (255, 255, 255, 245))
    canvas.paste(igit_big, (WIDTH // 2 - 200, card_top + 70), igit_big)
    canvas.paste(sole_big, (WIDTH // 2 + 20, card_top + 70), sole_big)

    f_title = get_font("black", 46)
    t1 = "SOCIETY OF LITERARY"
    t2 = "ENTHUSIASTS (SOLE)"
    for idx, line in enumerate([t1, t2]):
        bbox = draw.textbbox((0, 0), line, font=f_title)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, card_top + 290 + idx * 58), line, font=f_title, fill=TEXT_WHITE if idx == 0 else SOLE_CYAN)

    sub = "INDIRA GANDHI INSTITUTE OF TECHNOLOGY, SARANG"
    f_sub = get_font("bold", 21)
    bbox = draw.textbbox((0, 0), sub, font=f_sub)
    draw.text(((WIDTH - (bbox[2] - bbox[0])) // 2, card_top + 425), sub, font=f_sub, fill=GOLD_ACCENT)

    # Action pills
    actions = [
        ("FOLLOW ON INSTAGRAM", "@sole_igit"),
        ("SAVE THIS POST", "For your weekly reference"),
        ("SHARE WITH YOUR BATCH", "Drop your thoughts in comments"),
    ]
    y_act = card_top + 500
    for label, val in actions:
        draw.rounded_rectangle([144, y_act, WIDTH - 144, y_act + 74], radius=20, fill=CARD_BG_ALT, outline=CARD_BORDER, width=2)
        draw.text((180, y_act + 24), label, font=get_font("extrabold", 20), fill=SOLE_CYAN)
        v_bbox = draw.textbbox((0, 0), val, font=get_font("semibold", 20))
        draw.text((WIDTH - 180 - (v_bbox[2] - v_bbox[0]), y_act + 24), val, font=get_font("semibold", 20), fill=TEXT_WHITE)
        y_act += 96

    return canvas


def export_canva_csv_and_gslides_batch(
    content_type: str,
    selected_items: List[Dict[str, Any]],
    week_label: str,
    out_dir: Path,
) -> Tuple[Path, Path]:
    """
    Exports:
    1. canva_autofill.csv (compatible with the `canva-bulk-create` skill)
    2. gslides_batch.json (compatible with `gslides mutate batch`)
    """
    csv_path = out_dir / "canva_autofill.csv"
    gslides_path = out_dir / "gslides_batch.json"

    # 1. Write Canva Bulk-Create CSV
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

    # 2. Write Google Slides batch JSON
    ops: List[Dict[str, Any]] = [
        {"op": "set-background", "slide": "p", "color": "#070C14"},
        {"op": "add-textbox", "slide": "p", "text": f"SOLE | IGIT SARANG — BITS & BYTES ({week_label})", "x": 40, "y": 30, "width": 640, "height": 35, "font_size": 16, "bold": True, "color": "#22D3EE", "font_family": "Montserrat"},
        {"op": "add-textbox", "slide": "p", "text": f"Bits & Bytes: {content_type.upper()}", "x": 40, "y": 110, "width": 640, "height": 90, "font_size": 36, "bold": True, "color": "#F8FAFC", "font_family": "Montserrat"},
    ]
    for idx, item in enumerate(selected_items, 1):
        sid = f"SLIDE_{idx}"
        ops.append({"op": "add-slide", "layout": "BLANK", "id": sid})
        ops.append({"op": "set-background", "slide": sid, "color": "#0D1829"})
        if content_type == "news":
            title_txt = f"#{idx:02d} — {item.get('headline', '')}"
            body_txt = f"{item.get('summary', '')}\n\nSource: {item.get('source', '')} ({item.get('url', '')})"
        elif content_type == "facts":
            title_txt = f"DID YOU KNOW? — {item.get('title', '')}"
            body_txt = f"{item.get('fact', '')}\n\n{item.get('context', '')}\nSource: {item.get('source', '')}"
        else:
            title_txt = f"{item.get('word', '')} ({item.get('part_of_speech', '')})"
            body_txt = f"Definition: {item.get('definition', '')}\n\nExample: \"{item.get('example', '')}\"\nSynonyms: {', '.join(item.get('synonyms', []))}"
        ops.append({"op": "add-textbox", "slide": sid, "text": title_txt, "x": 40, "y": 35, "width": 640, "height": 85, "font_size": 24, "bold": True, "color": "#22D3EE", "font_family": "Montserrat"})
        ops.append({"op": "add-textbox", "slide": sid, "text": body_txt, "x": 40, "y": 135, "width": 640, "height": 220, "font_size": 15, "color": "#F8FAFC", "font_family": "Montserrat"})

    with open(gslides_path, "w", encoding="utf-8") as f:
        json.dump(ops, f, indent=2, ensure_ascii=False)

    return csv_path, gslides_path


def render_package_designs(
    content_type: str,
    selected_items: List[Dict[str, Any]],
    week_label: str,
    out_dir: Path,
) -> Dict[str, Any]:
    slides_dir = out_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)

    rendered_images: List[Image.Image] = []
    png_paths: List[str] = []

    if content_type == "news":
        total = len(selected_items) + 2
        cover = render_news_cover_slide(selected_items, week_label, total)
        rendered_images.append(cover)
        for idx, item in enumerate(selected_items, 1):
            slide = render_news_item_slide(item, idx, idx + 1, total, week_label)
            rendered_images.append(slide)
        closing = render_cta_closing_slide("news", total, total, week_label)
        rendered_images.append(closing)
    elif content_type == "facts":
        total = 2
        fact_slide = render_fact_slide(selected_items[0], 1, total, week_label)
        closing = render_cta_closing_slide("facts", 2, total, week_label)
        rendered_images.extend([fact_slide, closing])
    elif content_type == "vocab":
        total = 2
        vocab_slide = render_vocab_slide(selected_items[0], 1, total, week_label)
        closing = render_cta_closing_slide("vocab", 2, total, week_label)
        rendered_images.extend([vocab_slide, closing])
    else:
        raise ValueError(f"Unknown content_type: {content_type}")

    rgb_images: List[Image.Image] = []
    for idx, img in enumerate(rendered_images, 1):
        rgb = img.convert("RGB")
        rgb_images.append(rgb)
        p = slides_dir / f"slide_{idx:02d}.png"
        rgb.save(p, format="PNG", optimize=True)
        png_paths.append(str(p))

    pdf_path = out_dir / "linkedin_carousel.pdf"
    if rgb_images:
        rgb_images[0].save(
            pdf_path,
            format="PDF",
            resolution=150.0,
            save_all=True,
            append_images=rgb_images[1:],
        )

    csv_path, gslides_path = export_canva_csv_and_gslides_batch(content_type, selected_items, week_label, out_dir)

    return {
        "slide_count": len(png_paths),
        "png_paths": png_paths,
        "linkedin_pdf_path": str(pdf_path),
        "canva_csv_path": str(csv_path),
        "gslides_batch_path": str(gslides_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render SOLE Bits & Bytes Social Media Graphics")
    parser.add_argument("--type", choices=["news", "facts", "vocab"], required=True)
    parser.add_argument("--input", required=True, help="JSON file containing selected items")
    parser.add_argument("--week-label", required=True, help="Formatted date label e.g. 2026-Nov-W3-Saturday")
    parser.add_argument("--out-dir", required=True, help="Output folder for PNGs, PDF, CSV, and Slides JSON")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else data.get("selected", data.get("items", []))
    res = render_package_designs(args.type, items, args.week_label, Path(args.out_dir))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
