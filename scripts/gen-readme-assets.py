#!/usr/bin/env python3
"""Generate README image assets for dsh-provider-params (docs/assets/).

Outputs (idempotent overwrite):
  dsh-provider-params-flow-light.svg / dsh-provider-params-flow-dark.svg
      Hero data-flow diagram. Two hand-written SVG files (vector — never
      rasterized to webp). Text inside is command-surface tokens only
      (params.map, json.repair, dropped, actions, ...), so all five README
      languages share the same pair.

This plugin is pure host-side tooling with no UI and the repo ships no
benchmark dataset, so there is no raster evidence chart here. The CJK font
probe below is kept from the family skeleton as a guard: the moment a
Pillow-rendered (raster) asset with Chinese text is added, the script must
abort loudly instead of rendering tofu boxes.

Run once:  python scripts/gen-readme-assets.py
Requires:  Pillow (bundled DSH runtime Python already ships it)
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont  # noqa: F401  (raster assets later)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")

# --- palette: PerryLink family (accent) + GitHub page backgrounds ----------
FAMILY = "#4B67B4"   # family accent (badges labelColor family uses #2B3245)
GREEN = {"light": "#16a34a", "dark": "#3fb950"}
ORANGE = {"light": "#bc4c00", "dark": "#d29922"}
SKIN = {
    "light": dict(bg="#ffffff", box="#f6f8fa", border="#d0d7de",
                  text="#1f2328", sub="#57606a", track="#eaeef2"),
    "dark": dict(bg="#0d1117", box="#161b22", border="#30363d",
                 text="#f0f6fc", sub="#8b949e", track="#21262d"),
}

# --- CJK font probe: Chinese must never render as tofu boxes ----------------
FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyh.ttc",      # Microsoft YaHei
    r"C:\Windows\Fonts\simhei.ttf",    # SimHei
    r"C:\Windows\Fonts\Deng.ttf",      # DengXian
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
if FONT_PATH is None:
    sys.exit("FATAL: no CJK font found (looked for msyh.ttc, simhei.ttf, "
             "Deng.ttf, Noto Sans CJK, PingFang). Refusing to render Chinese "
             "as tofu boxes; install one of the probed fonts and re-run.")


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size)


# ---------------------------------------------------------------------------
# 1. Hero data-flow SVG (light + dark)
# ---------------------------------------------------------------------------
# Two independent pipelines: params.* (table lookups) and json.repair
# (text/structure passes). Only tool names, file names, and result keys appear.
TOP_NODES = [
    ("params-request.json", "openai · temperature 1.35"),
    ("params.map", "11 vendors · 13 fields"),
]
TOP_RESULT = ["mapped · dropped · added", "adjusted · unknown"]

BOTTOM_NODES = [
    ("broken-tool-output.json", "raw newline · trailing comma"),
    ("json.repair", "fixed pipeline · no model"),
]
BOTTOM_RESULT = ["actions[] · strategies[]",
                 "placeholders[] · validated"]


def _arrow(parts, s, x1: int, x2: int, y: int) -> None:
    parts.append(
        f'<path d="M{x1} {y}h{x2 - x1 - 14}" stroke="{s["sub"]}" '
        f'stroke-width="3"/>')
    parts.append(
        f'<path d="M{x2 - 16} {y - 7}l10 7-10 7" fill="none" '
        f'stroke="{s["sub"]}" stroke-width="3" '
        f'stroke-linecap="round" stroke-linejoin="round"/>')


def _lane(parts, s, nodes, result_lines, y, accent_index) -> None:
    box_h = 84
    input_w, tool_w = 270, 200
    input_x, tool_x, result_x = 60, 390, 650
    result_w = 490
    for i, (label, sub) in enumerate(nodes):
        x = input_x if i == 0 else tool_x
        width = input_w if i == 0 else tool_w
        accent = FAMILY if i == accent_index else s["border"]
        parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{box_h}" rx="14" '
            f'fill="{s["box"]}" stroke="{accent}" stroke-width="2"/>')
        parts.append(
            f'<text x="{x + width // 2}" y="{y + 38}" fill="{s["text"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="16" font-weight="700">{label}</text>')
        parts.append(
            f'<text x="{x + width // 2}" y="{y + 64}" fill="{s["sub"]}" '
            f'text-anchor="middle" font-family="ui-monospace,monospace" '
            f'font-size="12">{sub}</text>')
    _arrow(parts, s, input_x + input_w + 6, tool_x, y + box_h // 2)
    _arrow(parts, s, tool_x + tool_w + 6, result_x, y + box_h // 2)
    parts.append(
        f'<rect x="{result_x}" y="{y}" width="{result_w}" height="{box_h}" '
        f'rx="14" fill="{s["box"]}" stroke="{GREEN[s["_skin"]]}" '
        f'stroke-width="2"/>')
    for offset, line in enumerate(result_lines):
        parts.append(
            f'<text x="{result_x + 24}" y="{y + 35 + offset * 26}" '
            f'fill="{s["text"]}" font-family="ui-monospace,monospace" '
            f'font-size="14">{line}</text>')


def flow_svg(skin: str) -> str:
    s = SKIN[skin]
    s["_skin"] = skin
    w, h = 1200, 430
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="dsh-provider-params data flow">',
        f'<title>dsh-provider-params data flow</title>',
        f'<rect width="{w}" height="{h}" rx="18" fill="{s["bg"]}"/>',
        f'<text x="60" y="62" fill="{s["text"]}" font-family="ui-sans-serif,'
        f'system-ui,sans-serif" font-size="30" font-weight="700">'
        f'dsh-provider-params</text>',
        f'<text x="60" y="94" fill="{s["sub"]}" font-family="ui-monospace,'
        f'monospace" font-size="16">params.map · params.compare · '
        f'params.vendors · json.repair · R0 · no network · no writes</text>',
        f'<line x1="60" y1="116" x2="1140" y2="116" stroke="{s["border"]}"/>',
    ]
    _lane(parts, s, TOP_NODES, TOP_RESULT, 150, 1)
    _lane(parts, s, BOTTOM_NODES, BOTTOM_RESULT, 270, 1)
    parts.append(
        f'<text x="60" y="400" fill="{s["sub"]}" font-family="ui-monospace,'
        f'monospace" font-size="13">params.compare → 13 rows · '
        f'params.vendors → 11 vendors × 13 fields · deterministic · '
        f'no model call</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for skin in ("light", "dark"):
        with open(os.path.join(OUT, f"dsh-provider-params-flow-{skin}.svg"),
                  "w", encoding="utf-8", newline="\n") as fh:
            fh.write(flow_svg(skin))
    print("wrote 2 SVG assets to docs/assets/ "
          "(no raster evidence chart: this repo ships no benchmark dataset)")


if __name__ == "__main__":
    main()
