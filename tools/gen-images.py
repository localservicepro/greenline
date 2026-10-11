#!/usr/bin/env python3
"""
Generate responsive variants + a manifest for every site photo.

Run after changing anything in assets/img/. Requires Pillow; tools/build.py
itself stays stdlib-only and just reads the manifest this writes.

    python3 tools/gen-images.py && python3 tools/build.py
"""
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")

# Widths to emit. Anything wider than the source is skipped — we never upscale.
# 800 sits just above what a 412px phone at 1.75x needs (721px), so mobile
# stops jumping to a 960 file it never uses in full.
WIDTHS = [480, 800, 1200, 1600]
QUALITY = 70

# Photos that get responsive variants. Icons and the logo are already tiny.
SKIP = re.compile(r"(favicon|icon-\d+|apple-touch-icon|logo-|og)\.", re.I)
VARIANT = re.compile(r"-\d{3,4}\.(jpg|png)$")


def main():
    manifest = {}
    made = 0
    for name in sorted(os.listdir(IMG)):
        path = os.path.join(IMG, name)
        if not os.path.isfile(path) or not name.lower().endswith((".jpg", ".png")):
            continue
        if VARIANT.search(name):          # a variant from a previous run
            continue
        key, ext = os.path.splitext(name)
        with Image.open(path) as im:
            w, h = im.size
        entry = {"file": name, "w": w, "h": h, "srcset": []}

        if not SKIP.search(name):
            for tw in WIDTHS:
                if tw >= w:
                    continue
                vname = "%s-%d%s" % (key, tw, ext)
                vpath = os.path.join(IMG, vname)
                if not os.path.exists(vpath):
                    with Image.open(path) as im:
                        im = im.convert("RGB") if ext == ".jpg" else im
                        im = im.resize((tw, round(h * tw / w)), Image.LANCZOS)
                        if ext == ".jpg":
                            im.save(vpath, "JPEG", quality=QUALITY, optimize=True,
                                    progressive=True)
                        else:
                            im.save(vpath, optimize=True)
                    made += 1
                entry["srcset"].append([tw, vname])
            entry["srcset"].append([w, name])

        manifest[key] = entry

    out = os.path.join(IMG, "manifest.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)

    total = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG)
                if f.lower().endswith((".jpg", ".png")))
    print("generated %d new variants; %d images in manifest; %d KB on disk"
          % (made, len(manifest), total // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
