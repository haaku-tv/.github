#!/usr/bin/env python3
"""Build haaku's font-independent SVG assets (mark + wordmark banner).

Text in an SVG renders with whatever font the *viewer* happens to have, so the
same logo is a different width on macOS, Windows and Linux. These assets
convert every glyph to outlines instead, so the lockup is identical everywhere.

    .venv/bin/python scripts/build_assets.py

Inputs:  Poppins Bold/Medium (fetched from Google Fonts into scripts/.fonts,
         which is gitignored — the fonts are not vendored)
Outputs: assets/mark.svg, assets/logo-banner.svg
"""
import os
import urllib.request

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(BASE, "assets")
FONTS = os.path.join(BASE, "scripts", ".fonts")
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/{}"

BOLD, MEDIUM = "Poppins-Bold.ttf", "Poppins-Medium.ttf"

GRADIENT = """    <linearGradient id="haaku-g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#f4ebff"/>
      <stop offset="0.5" stop-color="#c4a5f0"/>
      <stop offset="1" stop-color="#9f7aea"/>
    </linearGradient>
"""
INK = "#1a1030"          # the near-black purple of the badge label pills
WORD = "#a78bfa"         # wordmark lavender
WORD_TAIL = "#8b6fbb"    # ".tv" tail


def load(name):
    path = os.path.join(FONTS, name)
    if not os.path.exists(path):
        os.makedirs(FONTS, exist_ok=True)
        print(f"fetching {name}")
        urllib.request.urlretrieve(FONT_URL.format(name), path)
    font = TTFont(path)
    return {
        "gs": font.getGlyphSet(),
        "upem": font["head"].unitsPerEm,
        "cmap": font.getBestCmap(),
        "hmtx": font["hmtx"],
    }


def glyph(f, ch):
    name = f["cmap"][ord(ch)]
    pen = SVGPathPen(f["gs"])
    f["gs"][name].draw(pen)
    return pen.getCommands(), f["hmtx"][name][0]


def bounds(f, text):
    """Font-unit bbox of a whole string (x_min, y_min, x_max, y_max)."""
    x = 0.0
    box = None
    for ch in text:
        name = f["cmap"][ord(ch)]
        bp = BoundsPen(f["gs"])
        f["gs"][name].draw(bp)
        if bp.bounds:
            x0, y0, x1, y1 = bp.bounds
            cand = (x + x0, y0, x + x1, y1)
            box = cand if box is None else (min(box[0], cand[0]), min(box[1], cand[1]),
                                            max(box[2], cand[2]), max(box[3], cand[3]))
        x += f["hmtx"][name][0]
    return box


def text_group(f, text, size, tracking=0.0, fill=WORD):
    """<g> holding the outlined string; caller places it at the baseline."""
    scale = size / f["upem"]
    scale = size / f["upem"]
    parts = [f'  <g fill="{fill}" transform="scale({scale:.6f} {-scale:.6f})">']
    x = 0.0
    for ch in text:
        d, adv = glyph(f, ch)
        if d:
            parts.append(f'    <path transform="translate({x:.1f} 0)" d="{d}"/>')
        x += adv + tracking / scale
    parts.append("  </g>")
    return "\n".join(parts)


def centered_h(f, size, cx, cy):
    """Translate for an 'h' whose glyph bbox is centred on (cx, cy)."""
    box = bounds(f, "h")
    s = size / f["upem"]
    gw = (box[2] - box[0]) * s
    gh = (box[3] - box[1]) * s
    return cx - gw / 2 - box[0] * s, cy + gh / 2 + box[1] * s


def build_mark():
    f = load(BOLD)
    size = 58.0
    x, y = centered_h(f, size, 44.0, 44.0)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="88" height="88" viewBox="0 0 88 88" role="img" aria-label="haaku">
  <defs>
{GRADIENT}  </defs>
  <rect x="2" y="2" width="84" height="84" rx="21" fill="url(#haaku-g)"/>
  <g transform="translate({x:.2f} {y:.2f})">
{text_group(f, "h", size, fill=INK)}
  </g>
</svg>
"""


def build_banner():
    bold = load(BOLD)
    med = load(MEDIUM)
    size = 84.0
    tracking = -2.0
    box = bounds(bold, "haaku")
    word_w = (box[2] - box[0]) * size / bold["upem"] + tracking * 4
    tail_box = bounds(med, ".tv")
    tail_w = (tail_box[2] - tail_box[0]) * size / med["upem"]
    mark_x, mark_y, mark = 10.0, 12.0, 96.0
    word_x = mark_x + mark + 30.0
    width = word_x + word_w + 14.0 + tail_w + mark_x
    height = 120.0
    # centre the wordmark's ink on the mark's vertical centre, not on the
    # baseline (which would leave the lockup looking bottom-heavy)
    s = size / bold["upem"]
    word_box = bounds(bold, "haaku")
    tail_box_v = bounds(med, ".tv")
    ink_top = max(word_box[3], tail_box_v[3])
    ink_bottom = min(word_box[1], tail_box_v[1])
    baseline = mark_y + mark / 2 + (ink_top + ink_bottom) * s / 2
    hb = centered_h(bold, mark * 0.6, mark / 2, mark / 2)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-label="haaku.tv">
  <defs>
{GRADIENT}  </defs>
  <g transform="translate({mark_x:.0f} {mark_y:.0f})">
    <rect x="0" y="0" width="{mark:.0f}" height="{mark:.0f}" rx="24" fill="url(#haaku-g)"/>
    <g transform="translate({hb[0]:.2f} {hb[1]:.2f})">
{text_group(bold, "h", mark * 0.6, fill=INK)}
    </g>
  </g>
  <g transform="translate({word_x - box[0] * size / bold['upem']:.2f} {baseline:.0f})">
{text_group(bold, "haaku", size, tracking)}
  </g>
  <g transform="translate({word_x + word_w + 14 - tail_box[0] * size / med['upem']:.2f} {baseline:.0f})">
{text_group(med, ".tv", size, 0.0, WORD_TAIL)}
  </g>
</svg>
"""


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "mark.svg"), "w").write(build_mark())
    open(os.path.join(OUT, "logo-banner.svg"), "w").write(build_banner())
    for name in ("mark.svg", "logo-banner.svg"):
        print(name, os.path.getsize(os.path.join(OUT, name)), "bytes")
