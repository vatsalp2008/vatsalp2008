#!/usr/bin/env python3
"""Render a shell-prompt section header as a transparent SVG.

Produces text like:  vatsal@github ~ $ ./contributions.sh
styled for a dark GitHub theme (blends in via a transparent background).

Usage:
    python generate_prompt.py <command> <output_svg> [--user NAME]
"""
import sys

COLOR_USER = "#39d353"
COLOR_HOST = "#58a6ff"
COLOR_DIM = "#8b949e"
COLOR_DOLLAR = "#39d353"
COLOR_CMD = "#e6edf3"

FONT_SIZE = 20
CHAR_WIDTH = FONT_SIZE * 0.6
PADDING = 8


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(user, command):
    return [
        (user, COLOR_USER),
        ("@github", COLOR_HOST),
        (" ~ ", COLOR_DIM),
        ("$ ", COLOR_DOLLAR),
        (command, COLOR_CMD),
    ]


def render_svg(user, command):
    segments = build(user, command)
    text_len = sum(len(t) for t, _ in segments)
    width = int(text_len * CHAR_WIDTH + 2 * PADDING)
    height = int(FONT_SIZE + 2 * PADDING)

    spans = "".join(
        '<tspan fill="{c}">{t}</tspan>'.format(c=color, t=escape(text))
        for text, color in segments
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        'viewBox="0 0 {w} {h}">\n'
        '  <text x="{x}" y="{y}" font-family="monospace" '
        'font-size="{fs}px" font-weight="bold" xml:space="preserve">{spans}'
        "</text>\n"
        "</svg>\n"
    ).format(w=width, h=height, x=PADDING, y=FONT_SIZE + PADDING / 2,
             fs=FONT_SIZE, spans=spans)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    user = "vatsal"
    if "--user" in sys.argv:
        user = sys.argv[sys.argv.index("--user") + 1]
        args = [a for a in args if a != user]
    if len(args) != 2:
        print("Usage: python generate_prompt.py <command> <output_svg> "
              "[--user NAME]")
        sys.exit(1)

    command, output_svg = args[0], args[1]
    with open(output_svg, "w", encoding="utf-8") as fh:
        fh.write(render_svg(user, command))
    print("Wrote {}".format(output_svg))


if __name__ == "__main__":
    main()
