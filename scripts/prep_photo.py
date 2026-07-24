#!/usr/bin/env python3
"""Crop and clean a source photo into a headshot for the ASCII portrait.

Removes the background (via rembg if installed, else a radial vignette),
crops to a centered head-and-shoulders region, and boosts contrast, then
writes a PNG that generate_ascii.py can consume.

Usage:
    python prep_photo.py <input_image> <output_png> [--dark]

By default the background fades to white (pair with the default ASCII
mapping). Pass --dark to place the subject on black instead (pair with
generate_ascii.py --invert, so a lit face renders as bright green on empty).
"""
import sys

from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFilter

# Crop box as fractions of the source (left, top, right, bottom).
# Tuned for an upright portrait: horizontal center ~48%, head-to-torso vertical.
CROP = (0.26, 0.20, 0.74, 0.62)

CONTRAST = 1.3

# Radial vignette (fallback when rembg is unavailable). Fractions of the crop.
VIGNETTE_CENTER = (0.5, 0.40)
VIGNETTE_RADIUS = (0.34, 0.44)


def segment(img):
    """Return an RGBA cutout of the subject, or None if rembg is unavailable."""
    try:
        from rembg import remove
    except ImportError:
        return None
    return remove(img.convert("RGB")).convert("RGBA")


def apply_vignette(img, bg):
    """Fade everything outside a central ellipse toward the bg color."""
    w, h = img.size
    cx, cy = VIGNETTE_CENTER[0] * w, VIGNETTE_CENTER[1] * h
    rx, ry = VIGNETTE_RADIUS[0] * w, VIGNETTE_RADIUS[1] * h
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse(
        [cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=min(w, h) * 0.10))
    backdrop = Image.new("RGB", (w, h), bg)
    return Image.composite(img, backdrop, mask)


def main():
    args = [a for a in sys.argv[1:] if a != "--dark"]
    dark = "--dark" in sys.argv[1:]
    if len(args) != 2:
        print("Usage: python prep_photo.py <input_image> <output_png> [--dark]")
        sys.exit(1)

    input_image, output_png = args[0], args[1]
    bg = (0, 0, 0) if dark else (255, 255, 255)

    src = Image.open(input_image)
    cutout = segment(src)

    if cutout is not None:
        w, h = cutout.size
        box = (int(CROP[0] * w), int(CROP[1] * h),
               int(CROP[2] * w), int(CROP[3] * h))
        cutout = cutout.crop(box)
        img = Image.new("RGB", cutout.size, bg)
        img.paste(cutout, (0, 0), cutout.split()[3])
        img = ImageOps.autocontrast(img.convert("L"), cutoff=1)
        img = ImageEnhance.Contrast(img).enhance(CONTRAST)
        note = "segmented"
    else:
        img = src.convert("RGB")
        w, h = img.size
        box = (int(CROP[0] * w), int(CROP[1] * h),
               int(CROP[2] * w), int(CROP[3] * h))
        img = img.crop(box)
        img = ImageOps.autocontrast(img, cutoff=1)
        img = ImageEnhance.Contrast(img).enhance(CONTRAST)
        img = apply_vignette(img, bg)
        note = "vignette fallback (install rembg for a cleaner cutout)"

    img.save(output_png)
    print("Wrote {} ({}x{}) [{}]".format(output_png, *img.size, note))


if __name__ == "__main__":
    main()
