#!/usr/bin/env bash
# Download the site's images into assets/img/ and switch the build to serve them
# from this domain instead of the generator's CDN.
#
# Run this once, from the repo root, on a machine with normal internet access:
#     bash tools/localise-images.sh && python3 tools/build.py
#
# After that the site has no external image dependency.

set -euo pipefail
cd "$(dirname "$0")/.."

BASE="https://d8j0ntlcm91z4.cloudfront.net/user_3EWpoiN6nlg900Jz4gzZzRlxgtK/"
mkdir -p assets/img

# key                  remote filename
MAP="
hero                 hf_20260819_123233_fa5a8a1c-cabc-4249-a8c6-059d46080806.png
lawn-mowing          hf_20260819_123233_260d5f73-7fb3-44cd-96c8-ff8bbbab7b43.png
gutter-cleaning      hf_20260819_123233_0dfd591f-fffa-4d91-9506-bb7904fb736d.png
garden-maintenance   hf_20260819_123233_c6cafff7-a0ca-4f67-8d4a-fab24d3e695d.png
hedge-trimming       hf_20260819_123233_1e21adb0-7221-4fbd-a5da-2cca2e051a8e.png
rubbish-removal      hf_20260819_123233_4da63f9f-98bc-43e0-8a89-d1edb27732a3.png
garden-clean-ups     hf_20260819_123529_50a8bac6-6f5d-445d-93e2-99c2747b66c5.png
about-dave           hf_20260819_123529_a7040eb6-a422-44ad-9608-2e3a1453bb0d.png
work-edging          hf_20260819_123233_5dd26d6f-c9dc-4d20-bd52-627396a03585.png
work-peninsula       hf_20260819_123233_1e6435e5-9980-406d-83d0-8c1fc9fe7df1.png
work-gutters         hf_20260819_123233_355bf930-b6ad-4fe7-bae0-9766e62b10c5.png
og                   hf_20260819_123233_8da94588-3ea2-44be-aed5-f3dff83853e7.png
"

echo "$MAP" | while read -r key remote; do
  [ -z "${key:-}" ] && continue
  echo "  fetching $key"
  curl -fsSL "$BASE$remote" -o "assets/img/$key.png"
done

# Flip the build over to local paths.
python3 - <<'PY'
p = "tools/build.py"
s = open(p, encoding="utf-8").read()
s = s.replace("USE_LOCAL_IMAGES = False", "USE_LOCAL_IMAGES = True", 1)
open(p, "w", encoding="utf-8").write(s)
PY

echo
echo "Done. Images are in assets/img/."
echo "Now run:  python3 tools/build.py"
echo
echo "Optional but recommended before launch — convert to WebP and resize:"
echo "  for f in assets/img/*.png; do cwebp -q 82 \"\$f\" -o \"\${f%.png}.webp\"; done"
