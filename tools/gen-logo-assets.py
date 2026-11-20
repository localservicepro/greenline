#!/usr/bin/env python3
"""
Build every logo asset from the client's supplied artwork.

    node tools/relabel-wordmark.js && python3 tools/gen-logo-assets.py

The artwork arrived with "PROPERTY SERVICES" on its second line; the trading
name is Prestige Property Care, so that line is redrawn here. The tree and the
PRESTIGE wordmark are never touched — the replacement line is Montserrat Bold
at the artwork's own 58px cap height, tracked so PROPERTY measures the same
494px of ink, and painted with a metallic ramp sampled row by row out of the
original letters so the gold matches rather than approximates. The flanking
rules grow to keep the line's full width, since the shorter word leaves slack.

Writes to assets/img/logo/:

    logo-lockup.png              the corrected lockup, gold on black
    logo-lockup-transparent.png  the same keyed to alpha, for other dark grounds
    logo-email-800.png           horizontal arrangement for email, 800x240
    logo-email-400.png           half size
    *-transparent.png            both of those with alpha

logo-supplied.png is the untouched original and is this script's input; it is
never overwritten. Requires Pillow (python3.13 in the build container — the
3.11 Pillow there is broken).
"""
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, "assets", "img", "logo")

# Measured once off the supplied artwork (1445x1088) and fixed since.
TOP, BOT = 928, 985              # cap band of the line being replaced
DASH_Y0, DASH_Y1 = 950, 961      # the flanking rules' own band
CENTRE = 722.5                   # the lockup's optical centre
GAP = 32                         # ink-to-rule gap in the original
LINE_L, LINE_R = 39, 1406        # the line's full width, kept
TREE = (345, 20, 1098, 706)      # ink bounds of the tree
WORDS = (39, 717, 1406, 986)     # ink bounds of both wordmark lines


def ramp(px, x0, x1, y0, y1):
    """Mean colour per row over the lit pixels in a box — the metallic ramp."""
    rows = {}
    for y in range(y0, y1 + 1):
        acc, n = [0, 0, 0], 0
        for x in range(x0, x1 + 1):
            p = px[x, y]
            if sum(p) > 150:
                acc = [acc[i] + p[i] for i in range(3)]
                n += 1
        rows[y] = tuple(round(c / n) for c in acc) if n else (0, 0, 0)
    return rows


def main():
    src = Image.open(os.path.join(LOGO, "logo-supplied.png")).convert("RGB")
    W, H = src.size
    px = src.load()

    text_ramp = ramp(px, 232, 1215, TOP, BOT)
    dash_ramp = ramp(px, 39, 198, DASH_Y0, DASH_Y1)

    mask = Image.open(os.path.join(LOGO, ".wordline.png")).convert("L")
    mask = mask.crop(mask.point(lambda v: 255 if v > 40 else 0).getbbox())
    h = BOT - TOP + 1
    mask = mask.resize((round(mask.size[0] * h / mask.size[1]), h), Image.LANCZOS)
    tw = mask.size[0]

    line = Image.new("RGB", mask.size)
    lp = line.load()
    for y in range(h):
        c = text_ramp[TOP + y]
        for x in range(tw):
            lp[x, y] = c

    src.paste((0, 0, 0), (0, TOP - 12, W, BOT + 12))
    x0 = round(CENTRE - tw / 2)
    src.paste(line, (x0, TOP), mask)
    for a, b in ((LINE_L, x0 - GAP), (x0 + tw + GAP, LINE_R)):
        for y in range(DASH_Y0, DASH_Y1 + 1):
            c = dash_ramp[y]
            for x in range(a, b):
                px[x, y] = c

    src.save(os.path.join(LOGO, "logo-lockup.png"), optimize=True)
    lum = src.convert("L")
    keyed = src.convert("RGBA")
    # Luminance as alpha keeps the soft edges of the gold without the dark halo
    # a threshold would leave behind.
    keyed.putalpha(lum.point(lambda v: min(255, int(v * 1.35))))
    keyed.save(os.path.join(LOGO, "logo-lockup-transparent.png"), optimize=True)
    print("wrote logo-lockup.png + transparent", src.size)

    tree, words = keyed.crop(TREE), keyed.crop(WORDS)
    for name, w, hh in (("logo-email-800", 800, 240), ("logo-email-400", 400, 120)):
        for suffix, bg in (("", (13, 13, 13, 255)), ("-transparent", (0, 0, 0, 0))):
            canvas = Image.new("RGBA", (w, hh), bg)
            pad = round(hh * 0.11)
            th = hh - pad * 2
            t = tree.resize((round(tree.size[0] * th / tree.size[1]), th), Image.LANCZOS)
            gap = round(hh * 0.09)
            wmw = w - t.size[0] - gap - pad * 2
            wm = words.resize((wmw, round(words.size[1] * wmw / words.size[0])), Image.LANCZOS)
            canvas.alpha_composite(t, (pad, pad))
            canvas.alpha_composite(wm, (pad + t.size[0] + gap, (hh - wm.size[1]) // 2))
            out = os.path.join(LOGO, name + suffix + ".png")
            (canvas if suffix else canvas.convert("RGB")).save(out, optimize=True)
            print("wrote", os.path.basename(out), canvas.size)


if __name__ == "__main__":
    main()
