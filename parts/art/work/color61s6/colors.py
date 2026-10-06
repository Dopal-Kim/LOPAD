"""대상 시트의 색 집계(작업 트리) — LUT 설계용."""
import colorsys
import json
import os
import sys
from collections import Counter

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import targets as T  # noqa: E402


def pages(rel):
    jp = os.path.join(T.SPR, rel + ".json")
    if rel.endswith(".png"):
        return [os.path.join(T.SPR, rel)]
    m = json.load(open(jp, encoding="utf-8"))
    d = os.path.dirname(jp)
    if "textures" in m:
        return [os.path.join(d, t["image"]) for t in m["textures"]]
    if "meta" in m:
        return [os.path.join(d, m["meta"]["image"])]
    return [os.path.join(d, m["image"])]


def hist(rels):
    C = Counter()
    per = Counter()
    for r in rels:
        seen = set()
        for p in pages(r):
            for (c, n) in Counter(Image.open(p).convert("RGBA").get_flattened_data() if hasattr(Image.Image, "get_flattened_data") else Image.open(p).convert("RGBA").getdata()).items():
                if c[3]:
                    h = "#%02x%02x%02x" % c[:3]
                    C[h] += n
                    seen.add(h)
        for h in seen:
            per[h] += 1
    return C, per


def show(name, rels):
    C, per = hist(rels)
    print("==", name, len(rels), "sheets", len(C), "colors")
    rows = []
    for h, n in C.items():
        r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
        hh, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        rows.append((round(hh * 360) if s > 0.12 else -1, h, n, per[h], round(0.2126 * r + 0.7152 * g + 0.0722 * b)))
    for hh, h, n, p, L in sorted(rows):
        print("  %s hue%4d L%3d px%8d sheets%3d" % (h, hh, L, n, p))


if __name__ == "__main__":
    groups = {"katana_fx": T.katana_fx(), "dagger_fx": T.dagger_fx(), "trait_katana": T.trait_fx("katana"), "trait_dagger": T.trait_fx("dagger"),
              "ki": T.ki_overlays(), "k_awaken": T.awaken_overlays("katana"), "d_awaken": T.awaken_overlays("dagger"),
              "k_a2glow": T.v4("katana", "a2_glow"), "d_a2glow": T.v4("dagger", "a2_glow"),
              "k_looks": T.looks("katana"), "d_looks": T.looks("dagger"), "k_cards": T.cards("katana"), "d_cards": T.cards("dagger")}
    for g in (sys.argv[1:] or groups):
        show(g, groups[g])
