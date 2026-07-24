#!/usr/bin/env python3
"""Convert a source photo into an ASCII-art SVG portrait for a dark GitHub theme.

Usage:
    python generate_ascii.py <input_image> <output_svg>
"""
import sys

from PIL import Image

# Character ramp from darkest to lightest.
RAMP = "@%#*+=-:. "

# Target number of character columns.
COLS = 100

# Terminal characters are taller than they are wide; correct for it so the
# portrait is not vertically stretched.
FONT_ASPECT = 0.55

# SVG styling (GitHub dark theme).
BG_COLOR = "#0d1117"
FG_COLOR = "#39d353"
FONT_SIZE = 8          # px per character cell (height)
CHAR_WIDTH = FONT_SIZE * 0.6  # monospace advance width
PADDING = 16
CORNER_RADIUS = 12


def escape(text):
    """Escape XML-significant characters for SVG text content."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def image_to_ascii(path):
    """Return a list of ASCII rows for the given image."""
    img = Image.open(path).convert("L")
    width, height = img.size

    cols = COLS
    # Scale rows by the true image aspect ratio, corrected for font aspect.
    rows = max(1, int(cols * (height / width) * FONT_ASPECT))

    img = img.resize((cols, rows))

    # Newer Pillow versions require materializing the pixel sequence with list().
    pixels = list(img.getdata())

    ramp_len = len(RAMP)
    lines = []
    for r in range(rows):
        chars = []
        for c in range(cols):
            brightness = pixels[r * cols + c]
            # Map 0..255 brightness onto the ramp (0 -> darkest char).
            idx = brightness * (ramp_len - 1) // 255
            chars.append(RAMP[idx])
        lines.append("".join(chars))
    return lines


def ascii_to_svg(lines):
    """Render ASCII rows as an SVG <text> block."""
    cols = max((len(line) for line in lines), default=0)
    rows = len(lines)

    text_width = cols * CHAR_WIDTH
    text_height = rows * FONT_SIZE
    svg_width = int(text_width + 2 * PADDING)
    svg_height = int(text_height + 2 * PADDING)

    tspans = []
    for i, line in enumerate(lines):
        y = PADDING + FONT_SIZE * (i + 1)
        tspans.append(
            '<tspan x="{x}" y="{y}">{content}</tspan>'.format(
                x=PADDING, y=y, content=escape(line)
            )
        )

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
        '  <rect width="{w}" height="{h}" rx="{r}" ry="{r}" fill="{bg}"/>\n'
        '  <text font-family="monospace" font-size="{fs}px" '
        'fill="{fg}" xml:space="preserve">\n'
        "    {tspans}\n"
        "  </text>\n"
        "</svg>\n"
    ).format(
        w=svg_width,
        h=svg_height,
        r=CORNER_RADIUS,
        bg=BG_COLOR,
        fg=FG_COLOR,
        fs=FONT_SIZE,
        tspans="\n    ".join(tspans),
    )


def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_ascii.py <input_image> <output_svg>")
        sys.exit(1)

    input_image, output_svg = sys.argv[1], sys.argv[2]
    lines = image_to_ascii(input_image)
    svg = ascii_to_svg(lines)
    with open(output_svg, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("Wrote {} ({} rows)".format(output_svg, len(lines)))


if __name__ == "__main__":
    main()
