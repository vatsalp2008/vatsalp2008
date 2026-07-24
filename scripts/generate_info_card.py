#!/usr/bin/env python3
"""Render data/profile.json as a terminal-window styled SVG code block.

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

# Syntax highlight colors.
COLOR_KEYWORD = "#ff7b72"   # const
COLOR_KEY = "#79c0ff"       # object keys
COLOR_STRING = "#a5d6ff"    # string values
COLOR_PUNCT = "#c9d1d9"     # punctuation/brackets

# Layout constants.
FONT_SIZE = 15
CHAR_WIDTH = FONT_SIZE * 0.6
LINE_HEIGHT = 22
TITLE_BAR_HEIGHT = 36
PADDING_X = 20
PADDING_Y = 16
CORNER_RADIUS = 10


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def span(text, color):
    """A single highlighted tspan fragment (no positioning)."""
    return '<tspan fill="{c}">{t}</tspan>'.format(c=color, t=escape(text))


def js_string(value):
    return '"{}"'.format(value)


def js_array(values):
    return "[" + ", ".join(js_string(v) for v in values) + "]"


def build_lines(profile):
    """Build a list of lines; each line is a list of (text, color) fragments."""
    var_name = profile["name"].split()[0].lower()
    tech = profile["techStack"]

    lines = []

    # const vatsal = {
    lines.append([("const ", COLOR_KEYWORD), (var_name, COLOR_KEY),
                  (" = {", COLOR_PUNCT)])

    def kv_string(key, value, indent="  "):
        return [(indent, COLOR_PUNCT), (key, COLOR_KEY), (": ", COLOR_PUNCT),
                (js_string(value), COLOR_STRING), (",", COLOR_PUNCT)]

    def kv_array(key, values, indent="  "):
        line = [(indent, COLOR_PUNCT), (key, COLOR_KEY), (": [", COLOR_PUNCT)]
        for i, v in enumerate(values):
            line.append((js_string(v), COLOR_STRING))
            if i < len(values) - 1:
                line.append((", ", COLOR_PUNCT))
        line.append(("],", COLOR_PUNCT))
        return line

    lines.append(kv_string("role", profile["role"]))
    lines.append(kv_string("education", profile["education"]))
    lines.append(kv_array("focus", profile["focus"]))

    # techStack: { languages: [...], ai_ml: [...], systems: [...] },
    tech_line = [("  ", COLOR_PUNCT), ("techStack", COLOR_KEY),
                 (": { ", COLOR_PUNCT)]
    nested = [("languages", tech["languages"]),
              ("ai_ml", tech["ai_ml"]),
              ("systems", tech["systems"])]
    for i, (k, vals) in enumerate(nested):
        tech_line.append((k, COLOR_KEY))
        tech_line.append((": ", COLOR_PUNCT))
        tech_line.append((js_array(vals), COLOR_STRING))
        if i < len(nested) - 1:
            tech_line.append((", ", COLOR_PUNCT))
    tech_line.append((" },", COLOR_PUNCT))
    lines.append(tech_line)

    lines.append(kv_string("currentGoal", profile["currentGoal"]))
    lines.append(kv_string("openTo", profile["openTo"]))

    lines.append([("};", COLOR_PUNCT)])

    return var_name, lines


def line_text_length(line):
    return sum(len(text) for text, _ in line)


def render_svg(profile):
    var_name, lines = build_lines(profile)
    filename = "{}.ts".format(var_name)

    max_len = max(line_text_length(line) for line in lines)
    body_width = int(max_len * CHAR_WIDTH + 2 * PADDING_X)
    # Ensure the centered filename fits too.
    min_width = int(len(filename) * CHAR_WIDTH + 120)
    width = max(body_width, min_width)

    body_height = int(len(lines) * LINE_HEIGHT + 2 * PADDING_Y)
    height = TITLE_BAR_HEIGHT + body_height

    parts = []
    parts.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        'viewBox="0 0 {w} {h}">'.format(w=width, h=height)
    )
    # Outer rounded card with border.
    parts.append(
        '  <rect x="0.5" y="0.5" width="{w}" height="{h}" rx="{r}" ry="{r}" '
        'fill="{body}" stroke="{border}"/>'.format(
            w=width - 1, h=height - 1, r=CORNER_RADIUS,
            body=BODY_BG, border=BORDER)
    )
    # Title bar (rounded top only via a rect + a covering rect for the bottom).
    parts.append(
        '  <path d="M0.5 {r} A{r} {r} 0 0 1 {r} 0.5 H{x2} '
        'A{r} {r} 0 0 1 {w} {r} V{bar} H0.5 Z" fill="{bar_c}" '
        'stroke="{border}"/>'.format(
            r=CORNER_RADIUS, x2=width - CORNER_RADIUS - 0.5, w=width - 0.5,
            bar=TITLE_BAR_HEIGHT, bar_c=TITLE_BAR, border=BORDER)
    )
    # Traffic-light circles.
    cy = TITLE_BAR_HEIGHT / 2
    for i, color in enumerate((CIRCLE_RED, CIRCLE_YELLOW, CIRCLE_GREEN)):
        cx = PADDING_X + i * 20
        parts.append(
            '  <circle cx="{cx}" cy="{cy}" r="6" fill="{c}"/>'.format(
                cx=cx, cy=cy, c=color)
        )
    # Centered filename.
    parts.append(
        '  <text x="{cx}" y="{cy}" text-anchor="middle" '
        'dominant-baseline="central" font-family="monospace" '
        'font-size="13px" fill="#8b949e">{name}</text>'.format(
            cx=width / 2, cy=cy, name=escape(filename))
    )

    # Code body.
    parts.append(
        '  <text font-family="monospace" font-size="{fs}px" '
        'xml:space="preserve">'.format(fs=FONT_SIZE)
    )
    for i, line in enumerate(lines):
        y = TITLE_BAR_HEIGHT + PADDING_Y + LINE_HEIGHT * (i + 1) - 6
        x = PADDING_X
        frags = "".join(span(text, color) for text, color in line)
        parts.append(
            '    <tspan x="{x}" y="{y}">{frags}</tspan>'.format(
                x=x, y=y, frags=frags)
        )
    parts.append("  </text>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


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
