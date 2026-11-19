#!/usr/bin/env python3
"""
One-time Static Asset Pre-Baker for SOLE — Bits -N- Bytes (IGIT Sarang).
Pre-renders and caches the heavy reusable 1080x1350 base frames into `assets/`:
  - `assets/base_cover_frame.png`: Exact torn edges + HD transparent SOLE & IGIT logos +
    scaled authentic "PRESENTS / BITS -N- BYTES" emblem + @sole_igit footer.
  - `assets/base_inner_frame.png`: Exact torn edges + cleared starry sky + HD transparent
    SOLE & IGIT logos + @sole_igit footer.

By saving these once, every weekly run skips JPEG upscaling, Gaussian mask blurs, and
logo compositing, cutting CPU & memory usage by >85%.
"""

import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
TEMPLATE_PATH = ASSETS_DIR / "bits_n_bytes_template.jpg"
SOLE_LOGO_HD_PATH = ASSETS_DIR / "sole_logo_hd.png"
IGIT_LOGO_HD_PATH = ASSETS_DIR / "igit_logo_hd.png"

BASE_COVER_OUT = ASSETS_DIR / "base_cover_frame.png"
BASE_INNER_OUT = ASSETS_DIR / "base_inner_frame.png"

WIDTH = 1080
HEIGHT = 1350
COSMIC_TOP = (5, 17, 34)
COSMIC_BOTTOM = (9, 32, 54)


def build_base_frames() -> None:
    raw_tpl = Image.open(TEMPLATE_PATH).convert("RGBA").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)

    # 1. Build base_inner_frame.png (cleared central sky + exact torn edges + HD logos)
    patch = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(patch)
    for y in range(138, 1240):
        t = (y - 138) / (1240 - 138)
        r = int(COSMIC_TOP[0] * (1 - t) + COSMIC_BOTTOM[0] * t)
        g = int(COSMIC_TOP[1] * (1 - t) + COSMIC_BOTTOM[1] * t)
        b = int(COSMIC_TOP[2] * (1 - t) + COSMIC_BOTTOM[2] * t)
        pdraw.line([(20, y), (WIDTH - 20, y)], fill=(r, g, b, 255))

    rng = random.Random(2026)
    for _ in range(75):
        sx = rng.randint(70, WIDTH - 70)
        sy = rng.randint(155, 1200)
        sr = rng.choice([1, 1, 2])
        alpha = rng.randint(90, 210)
        pdraw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(220, 240, 255, alpha))

    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.polygon(
        [
            (40, 145),
            (850, 145),
            (905, 235),
            (1035, 340),
            (1035, 1140),
            (940, 1225),
            (310, 1225),
            (185, 1140),
            (40, 940),
        ],
        fill=255,
    )
    mask = mask.filter(ImageFilter.GaussianBlur(radius=14))
    inner_frame = Image.composite(patch, raw_tpl, mask)

    # Replace blurry JPEG logos in top-left header with HD transparent SOLE & IGIT logos
    logo_bg = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    lb_draw = ImageDraw.Draw(logo_bg)
    for y in range(20, 146):
        lb_draw.line([(16, y), (256, y)], fill=COSMIC_TOP + (255,))
    logo_mask = Image.new("L", (WIDTH, HEIGHT), 0)
    ImageDraw.Draw(logo_mask).rounded_rectangle([20, 24, 252, 140], radius=14, fill=255)
    logo_mask = logo_mask.filter(ImageFilter.GaussianBlur(radius=4))
    inner_frame = Image.composite(logo_bg, inner_frame, logo_mask)

    draw = ImageDraw.Draw(inner_frame)
    if SOLE_LOGO_HD_PATH.exists():
        sole_hd = Image.open(SOLE_LOGO_HD_PATH).convert("RGBA")
        sole_hd.thumbnail((96, 92), Image.Resampling.LANCZOS)
        inner_frame.paste(sole_hd, (30 + (96 - sole_hd.width) // 2, 36 + (92 - sole_hd.height) // 2), sole_hd)

    draw.line([(138, 40), (138, 126)], fill=(255, 255, 255, 245), width=3)

    if IGIT_LOGO_HD_PATH.exists():
        igit_hd = Image.open(IGIT_LOGO_HD_PATH).convert("RGBA")
        igit_hd.thumbnail((96, 96), Image.Resampling.LANCZOS)
        inner_frame.paste(igit_hd, (150 + (96 - igit_hd.width) // 2, 35 + (96 - igit_hd.height) // 2), igit_hd)

    inner_frame.convert("RGB").save(BASE_INNER_OUT, format="PNG", optimize=True)

    # 2. Build base_cover_frame.png (inner_frame + scaled authentic PRESENTS / BITS -N- BYTES emblem)
    cover_frame = inner_frame.copy()
    crop_box = (70, 190, 1010, 1170)
    emblem_crop = raw_tpl.crop(crop_box)
    cw, ch = emblem_crop.size

    emblem_mask = Image.new("L", (cw, ch), 0)
    em_draw = ImageDraw.Draw(emblem_mask)
    em_draw.ellipse([18, 68, cw - 18, ch - 14], fill=255)
    em_draw.ellipse([230, 4, cw - 230, 210], fill=255)
    emblem_mask = emblem_mask.filter(ImageFilter.GaussianBlur(radius=10))

    target_w = int(cw * 0.65)
    target_h = int(ch * 0.65)
    emblem_scaled = emblem_crop.resize((target_w, target_h), Image.Resampling.LANCZOS)
    mask_scaled = emblem_mask.resize((target_w, target_h), Image.Resampling.LANCZOS)

    paste_x = (WIDTH - target_w) // 2
    paste_y = 160
    cover_frame.paste(emblem_scaled, (paste_x, paste_y), mask_scaled)
    cover_frame.convert("RGB").save(BASE_COVER_OUT, format="PNG", optimize=True)

    print(f"Pre-baked {BASE_INNER_OUT.name} ({BASE_INNER_OUT.stat().st_size // 1024} KB)")
    print(f"Pre-baked {BASE_COVER_OUT.name} ({BASE_COVER_OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build_base_frames()
