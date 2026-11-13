#!/usr/bin/env python3
"""Generate the dsh-provider-params README artwork (docs/assets/).

Outputs (idempotent overwrite):
  dsh-provider-params-hero-{zh,en}-{light,dark}.webp
      1440x576 Pillow banner. Left column: kicker, title, two value lines,
      subtitle, meta, compatibility line, footer. Right side: the semantic
      motif that belongs to this plugin alone - a five-row *verdict ledger*
      (mapped / adjusted / dropped / added / unknown) filled with the real
      quickstart result (openai -> anthropic), plus a repair-receipt strip.
  dsh-provider-params-flow-v5-{light,dark}.svg
      1100x660 hand-written structure diagram, two coupled panels:
        A  params_map - a *gate cascade*: one recognised? gate, one target-
           support gate, one documented-range gate; each "no" leaves through a
           side exit into its own verdict list, survivors land in mapped and
           the target-required gap is the added card.
        B  json_repair - a *bounded loop*: normalize/parse, a strategy pass
           that can only be retried max_steps times, fieldCompletion+validate,
           then two terminals (ok | E_JSON_*), fail-closed.
      Text inside the SVG is API tokens plus short English labels, so all five
      README languages share the same pair.

The previous dsh-provider-params-flow-{light,dark}.svg are left on disk on
purpose (external links); the five READMEs reference only the new files.

Run:      python scripts/gen-readme-assets.py
Requires: Pillow with WebP (the bundled runtime Python has both) and the CJK
          fonts msyh.ttc / msyhbd.ttc / consola.ttf. The script exits loudly
          instead of rendering tofu boxes.
"""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "assets")

# ---------------------------------------------------------------------------
# Fonts: fail loudly, never render tofu.
# ---------------------------------------------------------------------------
FONT_CANDIDATES = {
    "regular": [r"C:\Windows\Fonts\msyh.ttc",
                r"C:\Windows\Fonts\Deng.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/System/Library/Fonts/PingFang.ttc"],
    "bold": [r"C:\Windows\Fonts\msyhbd.ttc",
             r"C:\Windows\Fonts\msyh.ttc",
             "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
             "/System/Library/Fonts/PingFang.ttc"],
    "mono": [r"C:\Windows\Fonts\consola.ttf",
             r"C:\Windows\Fonts\msyh.ttc",
             "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"],
}
FONTS = {}
for role, paths in FONT_CANDIDATES.items():
    found = next((p for p in paths if os.path.exists(p)), None)
    if found is None:
        sys.exit(f"FATAL: no usable {role} font found (probed {paths}). "
                 "Refusing to render text that could come out as tofu boxes.")
    FONTS[role] = found

# The SVG is rendered by the browser, so its text is measured with the fonts
# Chrome actually resolves there (Segoe UI for sans, Cascadia Mono for mono).
# Measure over-wide rather than under-wide: if the browser picks Consolas
# instead of Cascadia Mono the strings only get narrower.
MEASURE = {
    "sans": next((p for p in [r"C:\Windows\Fonts\segoeui.ttf",
                              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
                  if os.path.exists(p)), FONTS["regular"]),
    "sansb": next((p for p in [r"C:\Windows\Fonts\segoeuib.ttf",
                               r"C:\Windows\Fonts\seguisb.ttf"]
                   if os.path.exists(p)), FONTS["bold"]),
    "mono": next((p for p in [r"C:\Windows\Fonts\CascadiaMono.ttf",
                              r"C:\Windows\Fonts\consola.ttf",
                              "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
                  if os.path.exists(p)), FONTS["mono"]),
}
_MEASURE_CACHE: dict[tuple[str, int, str], float] = {}


def measure(s: str, size: float, role: str = "sans") -> float:
    """Advance width of `s` in CSS pixels (4x supersampled measurement)."""
    key = (s, int(round(size * 4)), role)
    if key not in _MEASURE_CACHE:
        f = ImageFont.truetype(MEASURE[role], max(4, key[1]))
        _MEASURE_CACHE[key] = f.getlength(s) / 4.0
    return _MEASURE_CACHE[key]


# ---------------------------------------------------------------------------
# Palette: PerryLink family accent + the required page backgrounds.
# ---------------------------------------------------------------------------
PALETTE = {
    "light": dict(
        bg=(249, 246, 253), bg2=(228, 234, 248),
        panel=(253, 252, 255), panel2=(244, 245, 252),
        border=(214, 211, 230), card=(255, 255, 255),
        text=(27, 33, 64), sub=(91, 98, 121), faint=(122, 129, 150),
        accent=(75, 103, 180), accent_soft=(231, 234, 247),
        green=(22, 128, 76), green_soft=(227, 243, 234),
        amber=(178, 106, 0), amber_soft=(252, 243, 227),
        red=(180, 35, 24), red_soft=(252, 236, 233),
        shadow=(24, 32, 64, 34), dot=(75, 103, 180, 20),
        glow1=(75, 103, 180, 26), glow2=(112, 179, 166, 16),
    ),
    "dark": dict(
        bg=(19, 26, 42), bg2=(12, 16, 22),
        panel=(26, 34, 51), panel2=(21, 29, 46),
        border=(44, 56, 82), card=(30, 40, 60),
        text=(238, 241, 248), sub=(167, 176, 197), faint=(124, 135, 160),
        accent=(132, 150, 245), accent_soft=(34, 43, 69),
        green=(71, 196, 110), green_soft=(24, 51, 38),
        amber=(240, 180, 95), amber_soft=(58, 45, 28),
        red=(248, 122, 122), red_soft=(58, 30, 35),
        shadow=(0, 0, 0, 80), dot=(132, 150, 245, 24),
        glow1=(73, 99, 180, 48), glow2=(42, 120, 110, 24),
    ),
}

SS = 2  # supersampling factor for the Pillow hero
W, H = 1440, 576


def sc(v: float) -> int:
    return int(round(v * SS))


def font(role: str, size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONTS[role], sc(size))


def text(draw: ImageDraw.ImageDraw, xy, s: str, f, fill, anchor="ls",
         tracking: float = 0.0) -> None:
    x, y = xy
    if tracking:
        cursor = x
        for ch in s:
            draw.text((sc(cursor), sc(y)), ch, font=f, fill=fill, anchor=anchor)
            cursor += draw.textlength(ch, font=f) / SS + tracking
    else:
        draw.text((sc(x), sc(y)), s, font=f, fill=fill, anchor=anchor)


def width(draw: ImageDraw.ImageDraw, s: str, f) -> float:
    return draw.textlength(s, font=f) / SS


def fit_font(draw, role, size, s, max_width, min_size=14):
    """Largest font size (<= size) at which s fits max_width."""
    while size > min_size:
        f = font(role, size)
        if width(draw, s, f) <= max_width:
            return f
        size -= 1
    return font(role, min_size)


def grad_bg(skin: str) -> Image.Image:
    p = PALETTE[skin]
    grad = Image.new("RGB", (1, H * SS))
    top, bottom = p["bg"], p["bg2"]
    for y in range(H * SS):
        t = y / (H * SS - 1)
        grad.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t)
                                    for i in range(3)))
    return grad.resize((W * SS, H * SS)).convert("RGBA")


def add_glow(img: Image.Image, skin: str) -> None:
    p = PALETTE[skin]
    small = Image.new("RGBA", (W * SS // 4, H * SS // 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(small)
    q = SS / 4  # 1x design coordinates -> quarter-resolution glow layer
    d.ellipse([int(700 * q), int(-150 * q), int(1520 * q), int(300 * q)],
              fill=p["glow1"])
    d.ellipse([int(960 * q), int(360 * q), int(1540 * q), int(740 * q)],
              fill=p["glow2"])
    d.ellipse([int(-180 * q), int(340 * q), int(480 * q), int(760 * q)],
              fill=p["glow1"])
    small = small.filter(ImageFilter.GaussianBlur(28))
    img.alpha_composite(small.resize((W * SS, H * SS), Image.BILINEAR))


def add_dots(img: Image.Image, skin: str) -> None:
    p = PALETTE[skin]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(30, H, 26):
        for x in range(26, W, 26):
            d.ellipse([sc(x - 1), sc(y - 1), sc(x + 1), sc(y + 1)],
                      fill=p["dot"])
    img.alpha_composite(layer)


def rounded_mask() -> Image.Image:
    mask = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, W * SS - 1, H * SS - 1], radius=sc(22), fill=255)
    return mask


def panel(img: Image.Image, box, skin: str, radius: float = 20,
          fill_key: str = "panel") -> None:
    p = PALETTE[skin]
    x, y, w, h = box
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([sc(x), sc(y + 8), sc(x + w), sc(y + h + 8)],
                         radius=sc(radius), fill=p["shadow"])
    shadow = shadow.filter(ImageFilter.GaussianBlur(sc(10)))
    img.alpha_composite(shadow)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([sc(x), sc(y), sc(x + w), sc(y + h)],
                        radius=sc(radius), fill=p[fill_key],
                        outline=p["border"], width=max(1, sc(1.1)))


def dashed_line(draw, pts, fill, width_px=1.2, dash=6, gap=5) -> None:
    """Straight dashed segments between successive points."""
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        dx, dy = x2 - x1, y2 - y1
        dist = (dx * dx + dy * dy) ** 0.5
        if dist == 0:
            continue
        ux, uy = dx / dist, dy / dist
        t = 0.0
        while t < dist:
            a = t
            b = min(t + dash, dist)
            draw.line([sc(x1 + ux * a), sc(y1 + uy * a),
                       sc(x1 + ux * b), sc(y1 + uy * b)],
                      fill=fill, width=max(1, sc(width_px)))
            t += dash + gap


# ---------------------------------------------------------------------------
# Hero illustration: the five-row verdict ledger + repair receipt.
# ---------------------------------------------------------------------------
# Real quickstart values (samples/quickstart/expected/params-mapped.json):
# openai -> anthropic, temperature 1.35 clamped to 1, stop -> stop_sequences,
# frequency_penalty dropped. `added` / `unknown` stay empty for that sample, so
# those rows describe the rule instead of inventing a field.
LEDGER_ROWS = [
    ("mapped", "green", [
        "temperature 1 · top_p 0.9 · max_tokens 512",
        "stop → stop_sequences",
    ]),
    ("adjusted", "amber", [
        "temperature 1.35 → 1",
        "clamp 0..1 — documented range only",
    ]),
    ("dropped", "red", [
        "frequency_penalty",
        "no equivalent in anthropic — listed, not guessed",
    ]),
    ("added", "accent", [
        "max_tokens, when the input omits it",
        "reported without a value",
    ]),
    ("unknown", "faint", [
        "a key neither canonical nor a source wire",
        "strict:false → listed · strict:true → error",
    ]),
]

RECEIPT = ("json_repair → ok · actions[2] · "
           "strategies[escapeRepair,trailingComma]")


def draw_ledger(img: Image.Image, skin: str) -> None:
    p = PALETTE[skin]
    panel(img, (720, 76, 644, 412), skin, radius=20)
    d = ImageDraw.Draw(img)

    # --- header -----------------------------------------------------------
    text(d, (748, 116), "VERDICT LEDGER", font("bold", 15), p["accent"],
         tracking=1.4)
    text(d, (1336, 116), "openai → anthropic", font("mono", 14), p["sub"],
         anchor="rs")
    text(d, (748, 141),
         "every field it was given lands in mapped, adjusted, dropped or unknown",
         font("regular", 13), p["faint"])

    # --- five verdict rows ------------------------------------------------
    row_x, row_w, row_h, gap = 748, 588, 52, 7
    y = 154
    for label, color_key, lines in LEDGER_ROWS:
        color = p[color_key]
        d.rounded_rectangle([sc(row_x), sc(y), sc(row_x + row_w), sc(y + row_h)],
                            radius=sc(10), fill=p["panel2"],
                            outline=p["border"], width=max(1, sc(0.8)))
        d.rounded_rectangle([sc(row_x), sc(y + 8), sc(row_x + 4),
                             sc(y + row_h - 8)], radius=sc(2), fill=color)
        text(d, (row_x + 24, y + 30), label, font("bold", 15), color)
        mono = font("mono", 13.5)
        text(d, (row_x + 140, y + 22), lines[0], mono, p["text"])
        text(d, (row_x + 140, y + 41), lines[1], mono, p["sub"])
        y += row_h + gap

    # --- repair receipt strip --------------------------------------------
    dashed_line(d, [(row_x, 452), (1336, 452)], p["border"], 1.2, 5, 4)
    text(d, (row_x, 474), RECEIPT, font("mono", 13), p["sub"])
    chip_x = 1336 - 44
    d.rounded_rectangle([sc(chip_x), sc(456), sc(1336), sc(478)],
                        radius=sc(7), fill=p["accent_soft"])
    text(d, (chip_x + 22, 473), "R0", font("bold", 12.5), p["accent"],
         anchor="mm")


HERO_COPY = {
    "zh": dict(
        kicker="DSH 插件 · 四个只读工具",
        line1="11 家厂商 × 13 个字段，按真实字段名映射",
        line2="改名、丢弃、夹住、缺失——每一项都列出来",
        subtitle="纯内存计算 · 确定性 · 不联网 · 不调用模型 · 不写文件",
        meta="R0 · 11 vendors × 13 fields · 5 verdict lists · 4 strategies",
        meta2="Apache-2.0 · DSH >=0.2.1 <0.4.0 · Node >=24.9 <25",
        footer="github.com/PerryLink/dsh-provider-params",
        version="v0.2.0 · alpha / public-synthetic",
    ),
    "en": dict(
        kicker="DSH PLUGIN · FOUR READ-ONLY TOOLS",
        line1="11 vendors × 13 fields, mapped in one call.",
        line2="Every rename, drop, clamp and gap is reported.",
        subtitle="In-memory, deterministic · no network · no model call",
        meta="R0 · 11 vendors × 13 fields · 5 verdict lists · 4 strategies",
        meta2="Apache-2.0 · DSH >=0.2.1 <0.4.0 · Node >=24.9 <25",
        footer="github.com/PerryLink/dsh-provider-params",
        version="v0.2.0 · alpha / public-synthetic",
    ),
}


def build_hero(lang: str, skin: str) -> Image.Image:
    p = PALETTE[skin]
    copy = HERO_COPY[lang]
    img = grad_bg(skin)
    add_glow(img, skin)
    add_dots(img, skin)

    draw_ledger(img, skin)

    d = ImageDraw.Draw(img)
    # kicker: dot + tracked caps
    d.ellipse([sc(80), sc(104), sc(88), sc(112)], fill=p["accent"])
    text(d, (100, 111), copy["kicker"], font("bold", 17), p["accent"],
         tracking=1.6)

    # title + accent bar (left column, kept clear of the ledger card)
    title_f = fit_font(d, "bold", 60, "dsh-provider-params", 560, 48)
    d.rounded_rectangle([sc(76), sc(152), sc(81), sc(222)],
                        radius=sc(2.5), fill=p["accent"])
    text(d, (100, 220), "dsh-provider-params", title_f, p["text"])

    # two value lines
    f1 = fit_font(d, "regular", 26, copy["line1"], 600, 20)
    f2 = fit_font(d, "regular", 26, copy["line2"], 600, 20)
    text(d, (76, 285), copy["line1"], f1, p["text"])
    text(d, (76, 327), copy["line2"], f2, p["text"])

    # subtitle (>=15px), meta (>=12px)
    text(d, (76, 376), copy["subtitle"], font("regular", 22), p["sub"])
    text(d, (76, 420), copy["meta"], font("mono", 18), p["faint"])
    text(d, (76, 447), copy["meta2"], font("mono", 15), p["faint"])

    # footer rule + footer
    d.line([sc(76), sc(500), sc(1364), sc(500)], fill=p["border"],
           width=sc(1))
    text(d, (76, 538), copy["footer"], font("regular", 18), p["sub"])
    text(d, (1364, 538), copy["version"], font("mono", 17), p["faint"],
         anchor="rs")

    out = img.convert("RGBA")
    out.putalpha(Image.composite(out.getchannel("A"),
                                 Image.new("L", out.size, 0),
                                 rounded_mask()))
    return out.resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------------------
# Structure diagram: hand-written SVG, 1100 x 660, light + dark.
# ---------------------------------------------------------------------------
def flow_svg(skin: str) -> str:
    p = PALETTE[skin]
    c = lambda key: "#%02x%02x%02x" % p[key][:3]
    G, GS = c("accent"), c("accent_soft")
    TEXT, SUB, FAINT = c("text"), c("sub"), c("faint")
    BORDER, PANEL, PANEL2 = c("border"), c("panel"), c("panel2")
    GREEN, GREENS = c("green"), c("green_soft")
    AMBER, AMBERS = c("amber"), c("amber_soft")
    RED, REDS = c("red"), c("red_soft")
    BG1, BG2 = c("bg"), c("bg2")
    SANS = ("ui-sans-serif,system-ui,-apple-system,'Segoe UI',"
            "'Noto Sans',sans-serif")
    MONO = ("ui-monospace,SFMono-Regular,'Cascadia Mono',Consolas,"
            "'Liberation Mono',monospace")

    def fit(s, size, maxw, mono, weight):
        """Shrink a label until it fits maxw (never below 11px)."""
        role = "mono" if mono else ("sansb" if weight else "sans")
        while size > 11 and measure(s, size, role) > maxw:
            size -= 0.25
        return size

    def card(x, y, w, h, fill=PANEL, stroke=BORDER, dash=None, r=20):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1" '
                f'filter="url(#soft)"{dash_attr}/>')

    def txt(x, y, s, size=14, fill=None, weight=None, anchor="start",
            mono=False, tracking=None, maxw=None):
        if maxw is not None:
            size = fit(s, size, maxw, mono, weight)
        family = MONO if mono else SANS
        attrs = [f'x="{x}"', f'y="{y}"', f'fill="{fill or TEXT}"',
                 f'font-family="{family}"', f'font-size="{size:g}"']
        if weight:
            attrs.append(f'font-weight="{weight}"')
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if tracking:
            attrs.append(f'letter-spacing="{tracking}"')
        return f'<text {" ".join(attrs)}>{s}</text>'

    def line(x1, y1, x2, y2, stroke=BORDER, w=1, dash=None):
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'stroke="{stroke}" stroke-width="{w}"{dash_attr}/>')

    def arrow(d, stroke=SUB, marker="arw"):
        return (f'<path d="{d}" fill="none" stroke="{stroke}" '
                f'stroke-width="1.6" stroke-linecap="round" '
                f'stroke-linejoin="round" marker-end="url(#{marker})"/>')

    def chip(x, y, w, h, label, fill, color=None, size=11.5, maxw=None,
             r=6):
        stroke = f' stroke="{color}" stroke-width="1"' if color else ""
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
               f'fill="{fill}"{stroke}/>']
        if label:
            out.append(txt(x + 10, y + h / 2 + 4, label, size=size,
                           fill=color or TEXT, mono=True,
                           maxw=(maxw if maxw is not None else w - 14)))
        return "\n".join(out)

    # -- gate row: numbered question bar with a side exit tag ---------------
    gate_n = 0

    def gate(x, y, question, note, tag, tag_color, tag_fill):
        nonlocal gate_n
        gate_n += 1
        marker = {GREEN: "arw-g", AMBER: "arw-m", RED: "arw-r",
                  FAINT: "arw-f"}[tag_color]
        out = [
            f'<rect x="{x}" y="{y}" width="340" height="40" rx="11" '
            f'fill="{PANEL2}" stroke="{BORDER}" stroke-width="1"/>',
            f'<circle cx="{x + 20}" cy="{y + 20}" r="9" fill="{GS}"/>',
            txt(x + 20, y + 24, str(gate_n), size=11, fill=G, weight="700",
                anchor="middle"),
            txt(x + 38, y + 17, question, size=13.5, weight="700", maxw=252),
            txt(x + 38, y + 33, note, size=11.5, fill=SUB, maxw=286),
            arrow(f"M{x + 340} {y + 20} H{x + 356}", tag_color, marker),
            f'<rect x="{x + 358}" y="{y + 7}" width="108" height="26" '
            f'rx="8" fill="{tag_fill}" stroke="{tag_color}" stroke-width="1"/>',
            txt(x + 358 + 54, y + 24, tag, size=12, fill=tag_color, mono=True,
                anchor="middle", maxw=96),
        ]
        return "\n".join(out)

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="660" '
        'viewBox="0 0 1100 660" role="img" '
        'aria-label="dsh-provider-params structure: params_map sorts every '
        'field through three gates into five verdict lists; json_repair runs a '
        'bounded normalize-parse-strategy loop and stops at ok or E_JSON_*">',
        '<title>dsh-provider-params structure: verdict gates + bounded repair loop</title>',
        '<desc>Panel A: params_map reads the 11-by-13 table; each input key '
        'passes a recognised? gate (else unknown), a target-support gate (else '
        'dropped) and a documented-range gate (else adjusted), survivors land '
        'in mapped, and target-required gaps become added with no value. '
        'Panel B: json_repair trims and extracts a fence, parses, retries a '
        'bounded strategy pass (escapeRepair, trailingComma, truncationClosure) '
        'at most max_steps times, completes required fields with null, '
        'validates against the supported schema subset, then returns ok or a '
        'fail-closed E_JSON_* error.</desc>',
        '<defs>',
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{BG1}"/>'
        f'<stop offset="1" stop-color="{BG2}"/></linearGradient>',
        '<pattern id="dots" width="24" height="24" '
        'patternUnits="userSpaceOnUse">'
        f'<circle cx="1" cy="1" r="1" fill="{G}" opacity="0.08"/></pattern>',
        '<filter id="soft" x="-20%" y="-30%" width="140%" height="170%">'
        '<feDropShadow dx="0" dy="3" stdDeviation="6" flood-color="#1b2140" '
        f'flood-opacity="{0.10 if skin == "light" else 0.45}"/></filter>',
        '<marker id="arw" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" '
        f'markerHeight="7" orient="auto"><path d="M0 0 L8 4 L0 8 z" '
        f'fill="{SUB}"/></marker>',
        '<marker id="arw-a" viewBox="0 0 8 8" refX="7" refY="4" '
        f'markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0 0 L8 4 L0 8 z" fill="{G}"/></marker>',
        '<marker id="arw-g" viewBox="0 0 8 8" refX="7" refY="4" '
        f'markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0 0 L8 4 L0 8 z" fill="{GREEN}"/></marker>',
        '<marker id="arw-r" viewBox="0 0 8 8" refX="7" refY="4" '
        f'markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0 0 L8 4 L0 8 z" fill="{RED}"/></marker>',
        '<marker id="arw-m" viewBox="0 0 8 8" refX="7" refY="4" '
        f'markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0 0 L8 4 L0 8 z" fill="{AMBER}"/></marker>',
        '<marker id="arw-f" viewBox="0 0 8 8" refX="7" refY="4" '
        f'markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0 0 L8 4 L0 8 z" fill="{FAINT}"/></marker>',
        '</defs>',
        '<rect width="1100" height="660" rx="22" fill="url(#bg)"/>',
        '<rect width="1100" height="660" rx="22" fill="url(#dots)"/>',
        # ---- header ------------------------------------------------------
        txt(48, 54, "dsh-provider-params", size=30, weight="700"),
        txt(48, 82, "src/plugin/tools.ts · src/core/{rosetta,mapping,repair}.ts",
            size=14, fill=SUB, mono=True, maxw=620),
        txt(1052, 54, "R0 · no network · no writes · no model call",
            size=14, fill=SUB, mono=True, anchor="end", maxw=370),
        txt(1052, 82, "11 vendors × 13 canonical fields",
            size=14, fill=FAINT, mono=True, anchor="end", maxw=300),
        line(48, 100, 1052, 100),
        # ---- panel A: params_map ----------------------------------------
        card(48, 112, 508, 472),
        f'<circle cx="72" cy="146" r="11" fill="{GS}"/>',
        txt(72, 150, "A", size=13, fill=G, weight="700", anchor="middle"),
        txt(92, 151, "params_map — per-field verdicts", size=15, weight="700",
            maxw=300),
        txt(532, 151, "openai → anthropic", size=12, fill=FAINT, mono=True,
            anchor="end", maxw=130),
        # input card
        f'<rect x="68" y="164" width="468" height="84" rx="12" '
        f'fill="{PANEL2}" stroke="{BORDER}" stroke-width="1"/>',
        txt(82, 186, "IN · params-request.json", size=12, fill=G, mono=True,
            tracking="0.4", maxw=230),
        txt(82, 210, 'temperature 1.35 · top_p 0.9 · max_tokens 512',
            size=14, mono=True, maxw=438),
        txt(82, 233, 'stop ["\\n\\nHuman:"] · frequency_penalty 0.2',
            size=14, mono=True, maxw=438),
        # the three gates (side exits to the verdict lists)
        gate(68, 266, "recognized?", "13 canonical or source wire names",
             "no → unknown", FAINT, PANEL2),
        gate(68, 316, "target supports it?", "supported:false → drop",
             "no → dropped", RED, REDS),
        gate(68, 366, "out of documented range?", "clamp only where documented",
             "yes → adjusted", AMBER, AMBERS),
        # survivors -> mapped
        arrow("M238 406 V416", SUB),
        f'<rect x="68" y="420" width="340" height="124" rx="14" '
        f'fill="{GREENS}" stroke="{GREEN}" stroke-width="1"/>',
        txt(84, 444, "mapped", size=14, fill=GREEN, weight="700"),
        txt(392, 444, "target wire shape", size=11.5, fill=SUB, anchor="end",
            mono=True, maxw=110),
        txt(84, 470, "temperature: 1", size=13, mono=True, maxw=300),
        txt(84, 491, "top_p: 0.9", size=13, mono=True, maxw=300),
        txt(84, 512, "max_tokens: 512", size=13, mono=True, maxw=300),
        txt(84, 533, 'stop_sequences: ["..."]', size=13, mono=True, maxw=300),
        # added card (target-required gap, no value)
        f'<rect x="424" y="420" width="112" height="124" rx="14" '
        f'fill="{PANEL2}" stroke="{G}" stroke-width="1" '
        f'stroke-dasharray="5 4"/>',
        txt(438, 444, "added", size=14, fill=G, weight="700"),
        txt(438, 470, "required", size=11.5, mono=True, maxw=84),
        txt(438, 489, "by target", size=11.5, mono=True, maxw=84),
        txt(438, 508, "no value", size=11.5, mono=True, maxw=84),
        txt(438, 527, "invented", size=11.5, mono=True, maxw=84),
        # panel A footnote
        txt(68, 570, "params_compare → 13 rows · params_vendors → 11 × 13",
            size=12, fill=SUB, mono=True, maxw=330),
        txt(536, 570, "R0 · read-only", size=12, fill=FAINT, mono=True,
            anchor="end", maxw=120),
        # ---- panel B: json_repair ---------------------------------------
        card(572, 112, 480, 472),
        f'<circle cx="596" cy="146" r="11" fill="{GS}"/>',
        txt(596, 150, "B", size=13, fill=G, weight="700", anchor="middle"),
        txt(616, 151, "json_repair — bounded loop", size=15, weight="700",
            maxw=290),
        txt(1032, 151, "max_steps 1..64 · default 8", size=12, fill=FAINT,
            mono=True, anchor="end", maxw=150),
        # B1 input
        f'<rect x="592" y="164" width="232" height="84" rx="12" '
        f'fill="{PANEL2}" stroke="{BORDER}" stroke-width="1"/>',
        txt(606, 186, "IN · text", size=12, fill=G, mono=True, tracking="0.4",
            maxw=120),
        txt(606, 211, "raw text or ```json fence", size=13, mono=True,
            maxw=204),
        txt(606, 233, "caller-supplied · no file read", size=11.5, fill=SUB,
            maxw=204),
        arrow("M708 248 V260", SUB),
        # B2 normalize + parse
        f'<rect x="592" y="264" width="232" height="104" rx="12" '
        f'fill="{PANEL2}" stroke="{BORDER}" stroke-width="1"/>',
        txt(606, 287, "normalize · parse", size=14, weight="700", maxw=204),
        txt(606, 311, "trim · extract fence", size=13, mono=True, maxw=204),
        txt(606, 331, "root must be { or [", size=13, mono=True, maxw=204),
        txt(606, 351, "JSON.parse → fail?", size=13, mono=True, maxw=204),
        # B2b strategy pass (the only retryable stage)
        f'<rect x="840" y="254" width="192" height="128" rx="14" '
        f'fill="{GS}" stroke="{G}" stroke-width="1" stroke-dasharray="6 4"/>',
        txt(856, 278, "strategy pass", size=13.5, fill=G, weight="700",
            maxw=150),
        chip(856, 288, 160, 17, "escapeRepair", PANEL),
        chip(856, 309, 160, 17, "trailingComma", PANEL),
        chip(856, 330, 160, 17, "truncationClosure", PANEL),
        txt(1016, 370, "retry · ≤ max_steps 1..64", size=11.5, fill=SUB,
            mono=True, anchor="end", maxw=168),
        # cycle: parse -> pass (out) and pass -> parse (retry)
        arrow("M824 290 H838", SUB),
        arrow("M838 352 H826", SUB),
        # B3 fieldCompletion + validate
        arrow("M708 368 V392", SUB),
        f'<rect x="592" y="396" width="232" height="104" rx="12" '
        f'fill="{PANEL2}" stroke="{BORDER}" stroke-width="1"/>',
        txt(606, 419, "fieldCompletion · validate", size=14, weight="700",
            maxw=204),
        txt(606, 443, "required → null", size=13, mono=True, maxw=204),
        txt(606, 463, "schema subset only", size=13, mono=True, maxw=204),
        txt(606, 483, "placeholders[] reported", size=13, mono=True, maxw=204),
        # terminals: ok | fail-closed
        arrow("M708 500 V510", SUB),
        f'<rect x="592" y="512" width="232" height="46" rx="12" '
        f'fill="{GREENS}" stroke="{GREEN}" stroke-width="1"/>',
        txt(608, 542, "ok: true", size=15, fill=GREEN, weight="700"),
        txt(816, 542, "actions[] · value", size=11.5, fill=SUB, mono=True,
            anchor="end", maxw=120),
        f'<rect x="840" y="512" width="192" height="46" rx="12" '
        f'fill="{REDS}" stroke="{RED}" stroke-width="1"/>',
        txt(856, 542, "E_JSON_*", size=15, fill=RED, weight="700"),
        txt(1016, 542, "ok: false", size=11.5, fill=SUB, mono=True,
            anchor="end", maxw=90),
        # panel B footnote
        txt(592, 576, "E_JSON_*: NOT_CONTAINER · UNREPAIRABLE · "
                      "SCHEMA_VIOLATION", size=11.5, fill=SUB, mono=True,
            maxw=440),
        # ---- footer ------------------------------------------------------
        line(48, 602, 1052, 602),
        txt(48, 628, "every verdict listed · no value invented", size=13,
            fill=SUB, maxw=420),
        txt(1052, 628, "4 tools · deterministic · Apache-2.0", size=13,
            fill=FAINT, anchor="end", maxw=330),
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for lang in ("zh", "en"):
        for skin in ("light", "dark"):
            img = build_hero(lang, skin)
            path = os.path.join(
                OUT, f"dsh-provider-params-hero-{lang}-{skin}.webp")
            img.save(path, "WEBP", quality=92, method=6)
            print(f"wrote {os.path.relpath(path, ROOT)}")
    for skin in ("light", "dark"):
        path = os.path.join(OUT, f"dsh-provider-params-flow-v5-{skin}.svg")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(flow_svg(skin))
        print(f"wrote {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    main()
