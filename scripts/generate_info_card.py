#!/usr/bin/env python3
"""Render data/profile.json as a neofetch-style terminal-window SVG card.

Usage:
    python generate_info_card.py <input_json> <output_svg>
"""
import json
import sys

# Window chrome / theme colors.
TITLE_BAR = "#161b22"
BODY_BG = "#0d1117"
BORDER = "#30363d"
CIRCLE_RED = "#ff5f56"
CIRCLE_YELLOW = "#ffbd2e"
CIRCLE_GREEN = "#27c93f"
TITLE_TEXT = "#8b949e"

# neofetch palette.
COLOR_USER = "#39d353"      # user@host
COLOR_HOST = "#58a6ff"
COLOR_LABEL = "#f0883e"     # field labels (Role, Edu, Languages, ...)
COLOR_VALUE = "#c9d1d9"     # values
COLOR_SECTION = "#58a6ff"   # "- Stack" dividers
COLOR_BULLET = "#39d353"    # list bullets
COLOR_RULE = "#30363d"

# Layout.
FONT_SIZE = 15
CHAR_WIDTH = FONT_SIZE * 0.6
LINE_HEIGHT = 22
TITLE_BAR_HEIGHT = 36
PADDING_X = 22
PADDING_Y = 18
CORNER_RADIUS = 10

# Width of the aligned label column (in characters).
LABEL_WIDTH = 11


def escape(text):
    return (str(text).replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def span(text, color):
    return '<tspan fill="{c}">{t}</tspan>'.format(c=color, t=escape(text))


def build_lines(profile):
    """Return (var_name, [line]) where each line is [(text, color), ...]."""
    var_name = profile["name"].split()[0].lower()
    tech = profile["techStack"]
    lines = []

    def label_row(label, value):
        padded = label.ljust(LABEL_WIDTH)
        return [(padded, COLOR_LABEL), (value, COLOR_VALUE)]

    def section(title):
        return [("─ " + title, COLOR_SECTION)]

    def bullet(value):
        return [("• ", COLOR_BULLET), (value, COLOR_VALUE)]

    def blank():
        return [("", COLOR_VALUE)]

    # Header: user@host
    lines.append([(var_name, COLOR_USER), ("@", COLOR_VALUE),
                  ("github", COLOR_HOST)])
    lines.append([("".ljust(len(var_name) + 7, "─"), COLOR_RULE)])

    lines.append(label_row("Role", profile["role"]))
    lines.append(label_row("Edu", profile["education"]))
    lines.append(label_row("Focus", " · ".join(profile["focus"])))
    lines.append(blank())

    lines.append(section("Stack"))
    lines.append(label_row("Languages", ", ".join(tech["languages"])))
    lines.append(label_row("AI / ML", ", ".join(tech["ai_ml"])))
    lines.append(label_row("Systems", ", ".join(tech["systems"])))
    lines.append(blank())

    lines.append(section("Now"))
    lines.append(bullet(profile["currentGoal"]))
    lines.append(section("Open to"))
    lines.append(bullet(profile["openTo"]))

    return var_name, lines


def line_len(line):
    return sum(len(t) for t, _ in line)


def render_svg(profile):
    var_name, lines = build_lines(profile)
    title = "{}@github: ~".format(var_name)

    max_len = max(line_len(line) for line in lines)
    body_width = int(max_len * CHAR_WIDTH + 2 * PADDING_X)
    min_width = int(len(title) * CHAR_WIDTH + 140)
    width = max(body_width, min_width)

    body_height = int(len(lines) * LINE_HEIGHT + 2 * PADDING_Y)
    height = TITLE_BAR_HEIGHT + body_height

    p = []
    p.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        'viewBox="0 0 {w} {h}">'.format(w=width, h=height)
    )
    p.append(
        '  <rect x="0.5" y="0.5" width="{w}" height="{h}" rx="{r}" ry="{r}" '
        'fill="{body}" stroke="{border}"/>'.format(
            w=width - 1, h=height - 1, r=CORNER_RADIUS,
            body=BODY_BG, border=BORDER)
    )
    p.append(
        '  <path d="M0.5 {r} A{r} {r} 0 0 1 {r} 0.5 H{x2} '
        'A{r} {r} 0 0 1 {w} {r} V{bar} H0.5 Z" fill="{bar_c}" '
        'stroke="{border}"/>'.format(
            r=CORNER_RADIUS, x2=width - CORNER_RADIUS - 0.5, w=width - 0.5,
            bar=TITLE_BAR_HEIGHT, bar_c=TITLE_BAR, border=BORDER)
    )
    cy = TITLE_BAR_HEIGHT / 2
    for i, color in enumerate((CIRCLE_RED, CIRCLE_YELLOW, CIRCLE_GREEN)):
        p.append('  <circle cx="{cx}" cy="{cy}" r="6" fill="{c}"/>'.format(
            cx=PADDING_X + i * 20, cy=cy, c=color))
    p.append(
        '  <text x="{cx}" y="{cy}" text-anchor="middle" '
        'dominant-baseline="central" font-family="monospace" '
        'font-size="13px" fill="{tc}">{name}</text>'.format(
            cx=width / 2, cy=cy, tc=TITLE_TEXT, name=escape(title)))

    p.append(
        '  <text font-family="monospace" font-size="{fs}px" '
        'xml:space="preserve">'.format(fs=FONT_SIZE))
    for i, line in enumerate(lines):
        y = TITLE_BAR_HEIGHT + PADDING_Y + LINE_HEIGHT * (i + 1) - 6
        frags = "".join(span(t, c) for t, c in line)
        p.append('    <tspan x="{x}" y="{y}">{frags}</tspan>'.format(
            x=PADDING_X, y=y, frags=frags))
    p.append("  </text>")
    p.append("</svg>")
    return "\n".join(p) + "\n"


def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_info_card.py <input_json> <output_svg>")
        sys.exit(1)

    input_json, output_svg = sys.argv[1], sys.argv[2]
    with open(input_json, encoding="utf-8") as fh:
        profile = json.load(fh)

    svg = render_svg(profile)
    with open(output_svg, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("Wrote {}".format(output_svg))


if __name__ == "__main__":
    main()
