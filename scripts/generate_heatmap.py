#!/usr/bin/env python3
"""Fetch a year of GitHub contributions and render a custom SVG heatmap.

Usage:
    python generate_heatmap.py <github_username> <output_svg>

Requires a GITHUB_TOKEN in the environment.
"""
import json
import os
import sys
import urllib.request
import urllib.error

GRAPHQL_URL = "https://api.github.com/graphql"

# Heatmap geometry.
CELL = 11          # cell width/height
GAP = 3            # gap between cells
RADIUS = 2         # rounded corners on each cell
PADDING = 16

BG_COLOR = "#0d1117"
EMPTY_COLOR = "#161b22"

# Fallback green scale (darkest -> brightest) when the API gives no color.
GREEN_SCALE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""


def escape(text):
    return (str(text).replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))


def fetch_calendar(username, token):
    payload = json.dumps({"query": QUERY, "variables": {"login": username}})
    request = urllib.request.Request(
        GRAPHQL_URL,
        data=payload.encode("utf-8"),
        headers={
            "Authorization": "bearer {}".format(token),
            "Content-Type": "application/json",
            "User-Agent": "generate_heatmap",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")
        print("GitHub API HTTP error {}: {}".format(err.code, detail),
              file=sys.stderr)
        sys.exit(1)

    if "errors" in body:
        print("GitHub API returned errors: {}".format(body["errors"]),
              file=sys.stderr)
        sys.exit(1)

    user = body.get("data", {}).get("user")
    if not user:
        print("No user data returned for '{}'.".format(username),
              file=sys.stderr)
        sys.exit(1)

    return (user["contributionsCollection"]["contributionCalendar"]["weeks"])


def level_color(count):
    if count <= 0:
        return GREEN_SCALE[0]
    if count < 3:
        return GREEN_SCALE[1]
    if count < 6:
        return GREEN_SCALE[2]
    if count < 10:
        return GREEN_SCALE[3]
    return GREEN_SCALE[4]


def render_svg(weeks):
    num_weeks = len(weeks)
    width = int(2 * PADDING + num_weeks * (CELL + GAP) - GAP)
    height = int(2 * PADDING + 7 * (CELL + GAP) - GAP)

    parts = []
    parts.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        'viewBox="0 0 {w} {h}">'.format(w=width, h=height)
    )
    parts.append(
        '  <rect width="{w}" height="{h}" rx="6" ry="6" fill="{bg}"/>'.format(
            w=width, h=height, bg=BG_COLOR)
    )

    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            # Position the day in its correct weekday row.
            weekday = _weekday_index(day["date"])
            x = PADDING + wi * (CELL + GAP)
            y = PADDING + weekday * (CELL + GAP)

            count = day["contributionCount"]
            color = day.get("color")
            if not color or count == 0:
                color = EMPTY_COLOR if count == 0 else level_color(count)
            plural = "" if count == 1 else "s"
            title = "{}: {} contribution{}".format(day["date"], count, plural)

            parts.append(
                '  <rect x="{x}" y="{y}" width="{c}" height="{c}" '
                'rx="{r}" ry="{r}" fill="{color}">'
                '<title>{title}</title></rect>'.format(
                    x=x, y=y, c=CELL, r=RADIUS, color=color,
                    title=escape(title))
            )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _weekday_index(date_str):
    """Return 0..6 (Sun..Sat) matching GitHub's calendar rows."""
    import datetime
    d = datetime.date.fromisoformat(date_str)
    # Python weekday(): Mon=0..Sun=6; GitHub rows are Sun=0..Sat=6.
    return (d.weekday() + 1) % 7


def main():
    if len(sys.argv) != 3:
        print("Usage: python generate_heatmap.py <github_username> "
              "<output_svg>")
        sys.exit(1)

    username, output_svg = sys.argv[1], sys.argv[2]

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is not set.",
              file=sys.stderr)
        sys.exit(1)

    weeks = fetch_calendar(username, token)
    svg = render_svg(weeks)
    with open(output_svg, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("Wrote {} ({} weeks)".format(output_svg, len(weeks)))


if __name__ == "__main__":
    main()
