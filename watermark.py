"""
Bulk watermark script for Awakening Vajra Nusantara photos.

Produces two watermark variants, since the same source photos are displayed
at very different sizes on the two pages:

  assets/watermarked/       - full-size photos for gallery.html (larger font)
  assets/watermarked-small/ - small thumbnails used on index.html (smaller font)

Both use a single small watermark centered at the bottom of the photo,
fully inside the frame (no more tiled/cropped text).

Usage:
    python3 watermark.py

Reads from:  assets/
Writes to:   assets/watermarked/ and assets/watermarked-small/
             (originals are left untouched)
"""

import os
from PIL import Image, ImageDraw, ImageFont

SOURCE_DIR = "assets"
WATERMARK_TEXT = "@awakening vajra nusantara"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

MAX_DIMENSION = 1600        # cap so huge camera originals get normalized
OPACITY = 165               # 0-255 — readable but still subtle

# Manual rotation fixes, in degrees counter-clockwise (matches PIL's
# Image.rotate convention — 90 = quarter turn left).
ROTATE_FIXES = {
    "DSC_0500.JPG": 90,
    "DSC_0598.JPG": 90,
}

# --- Variant 1: gallery.html photos (full-size photo grid) ---
GALLERY_OUTPUT_DIR = "assets/watermarked"
GALLERY_FONT_SIZE = 24
GALLERY_BOTTOM_MARGIN = 28
GALLERY_FILES = [
    "DSC_0193.jpg", "DSC_0229.jpg", "DSC_0238.jpg", "DSC_0338.jpg",
    "DSC_0500.JPG", "DSC_0578.jpg", "DSC_0598.JPG", "DSC_0717.jpg",
    "DSC_0418.jpg", "DSC_0524.jpg", "DSC_0646 (1).jpg", "DSC_0616.JPG",
    "gallery2.png",
]

# --- Variant 2: index.html photos — these render much smaller on the
# homepage (timeline thumbnails, small gallery-preview tiles), so they get
# a smaller watermark sized for that display, not the full photo size. ---
INDEX_OUTPUT_DIR = "assets/watermarked-small"
INDEX_FONT_SIZE = 12
INDEX_BOTTOM_MARGIN = 10
INDEX_FILES = [
    "day1.png", "day2.png", "day3.jpg", "day4.png", "day5.png",
    "gallery1.png", "gallery2.png", "gallery3.png", "gallery4.png",
    "cta-bg.png",
]


def normalize_size(img):
    """Downscale (never upscale) so the longer side is at most MAX_DIMENSION."""
    w, h = img.size
    longest = max(w, h)
    if longest <= MAX_DIMENSION:
        return img
    scale = MAX_DIMENSION / longest
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def make_bottom_center_overlay(size, font, bottom_margin):
    """Build a single small watermark stamp, centered at the bottom, fully inside the frame."""
    w, h = size

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    x = (w - text_w) / 2 - bbox[0]
    y = h - text_h - bottom_margin - bbox[1]

    # Faint dark outline first so the text stays legible against any
    # background (light or dark), then the semi-transparent white text on top.
    outline_opacity = min(255, OPACITY + 40)
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        draw.text((x + dx, y + dy), WATERMARK_TEXT, font=font,
                   fill=(0, 0, 0, outline_opacity // 3))
    draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, OPACITY))

    return overlay


def watermark_image(path_in, path_out, font, bottom_margin, rotate_deg=None):
    base = Image.open(path_in).convert("RGBA")
    if rotate_deg:
        base = base.rotate(rotate_deg, expand=True)
    base = normalize_size(base)

    overlay = make_bottom_center_overlay(base.size, font, bottom_margin)
    watermarked = Image.alpha_composite(base, overlay).convert("RGB")

    os.makedirs(os.path.dirname(path_out), exist_ok=True)
    watermarked.save(path_out, quality=90)


def run_variant(files, output_dir, font_size, bottom_margin):
    os.makedirs(output_dir, exist_ok=True)
    font = ImageFont.truetype(FONT_PATH, font_size)
    done, skipped = [], []

    for fname in files:
        src = os.path.join(SOURCE_DIR, fname)
        if not os.path.exists(src):
            skipped.append(fname)
            continue
        out = os.path.join(output_dir, fname)
        watermark_image(src, out, font, bottom_margin, rotate_deg=ROTATE_FIXES.get(fname))
        done.append(fname)

    print(f"Watermarked {len(done)} images -> {output_dir}/")
    if skipped:
        print(f"  Skipped (not found): {skipped}")


def main():
    run_variant(GALLERY_FILES, GALLERY_OUTPUT_DIR, GALLERY_FONT_SIZE, GALLERY_BOTTOM_MARGIN)
    run_variant(INDEX_FILES, INDEX_OUTPUT_DIR, INDEX_FONT_SIZE, INDEX_BOTTOM_MARGIN)


if __name__ == "__main__":
    main()
