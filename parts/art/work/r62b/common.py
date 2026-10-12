"""62 루프 2 아트(r62b) 공용 — 경로·팔레트·시트 쓰기·아틀라스 변환·미리보기.

- 시트 쓰기·아틀라스 변환은 bundle2 의 b2(write_sheet → to_atlas, atlas57 convert_sheet/apply_in_place)를 그대로 쓴다.
- 그림 도구(셰이딩·램프)는 props_v3 의 pk(bundle2 가 다시 내보냄).
- 단위: 도트. pixelScale 0.5 → 64 도트 = 1칸.
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
sys.path.insert(0, os.path.join(WORK, "bundle2"))
sys.path.insert(0, os.path.join(WORK, "atlas57"))

import b2  # noqa: E402
import gridsheet  # noqa: E402
from b2 import (U, Canvas, Rand, G, A, SL, WD, PL, X, EMISSIVE, CLEAR, R_WOOD, R_WOODG, R_IRON, R_STONE,  # noqa: E402,F401
                R_NSTONE, R_WSTONE, R_CLOTH, R_CLOTHG, R_EARTH, R_COPPER, R_LIQ, R_BONE, FLAME, contact, cyl,
                plank_box, shade_mask, mask, splash, flame, embers, glass_lantern, stone_blob, face, grain,
                ell_mask, poly_mask, outline, qcol, clamp, lam, tohex, BAYER)

SPR = os.path.join(ROOT, "assets", "sprites")
TILES = os.path.join(ROOT, "assets", "tiles")
PAL = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))
DRY = False
SRC = "parts/art/work/r62b/build.py (62 루프 2 · P16)"


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexc(c):
    return "#%02x%02x%02x" % tuple(c[:3])


GRAY = [hx(c) for c in PAL["gray"]]
AMB = [hx(c) for c in PAL["floors"][0]["ramp"]]   # 1층 램프 16~27 (A[16..27] 과 같다)

# 무기 색(계약 §28) — 어두운 → 밝은. 마지막 칸은 판정(glow) 칸에만.
FROST = [hx(c) for c in ["#1a3a58", "#1c405f", "#255a84", "#2f78ac", "#3d9ccf", "#5cc6ee", "#8fe3ff", "#bff3ff", "#e6fcff"]]
LAVA = [hx(c) for c in ["#241816", "#3c1a17", "#66231b", "#96301e", "#c83e22", "#ff5a2a", "#ff8448", "#ffb46c", "#ffd496"]]
POISON = [hx(c) for c in ["#2a1544", "#44206c", "#64289a", "#9440d8", "#c060ff", "#ec9cff", "#f6c8ff", "#fbe0ff"]]
JADE = [hx(c) for c in ["#2f2a1c", "#574c2e", "#9a8a50", "#1fa074", "#40e0a0", "#6eecb8", "#aef5d8", "#d2fae8"]]
X0 = (255, 255, 255)
INK = [hx(c) for c in ["#0d0d10", "#141516", "#1a1b1e", "#212224", "#2f3033"]]   # 먹 (gray 1~3 + 짙은 먹)
COLD_RIM = [hx(c) for c in ["#3a4a5e", "#56708c", "#7d98b4", "#a8c0d6"]]           # 차가운 달빛 림(일반 적)


def bayer(x, y):
    return (BAYER[y & 3][x & 3] + 0.5) / 16.0


def ramp_pick(ramp, v, x, y):
    """v 0..1 → 램프 칸(인접 두 칸 사이를 Bayer 디더)."""
    v = max(0.0, min(0.9999, v)) * (len(ramp) - 1)
    i = int(v)
    f = v - i
    if i + 1 < len(ramp) and f > bayer(x, y):
        i += 1
    return ramp[i]


def load_grid(rel):
    """assets/sprites 기준 경로(확장자 없음) → (격자 메타, 격자 RGBA)."""
    p = os.path.join(SPR, rel + ".json")
    return gridsheet.load_meta(p), gridsheet.open_grid(p)


def cell(meta, grid, r, c):
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    return grid.crop((c * fw, r * fh, c * fw + fw, r * fh + fh))


def dump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def save_png(im, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, optimize=True)


def colors_of(im):
    cs = im.convert("RGBA").getcolors(1 << 22) or []
    return {c[:3] for n, c in cs if c[3] > 0}


def board(items, bg=(30, 30, 36), k=2, pad=10, max_w=2400):
    """[(이미지, 라벨 없음)] 을 줄 바꿈 배치 후 k 배 최근접 확대."""
    rows, cur, x, h = [], [], 0, 0
    for im in items:
        if x + im.width > max_w and cur:
            rows.append((cur, h)); cur, x, h = [], 0, 0
        cur.append((x, im)); x += im.width + pad; h = max(h, im.height)
    if cur:
        rows.append((cur, h))
    W = max(sum(i.width + pad for _, i in r) for r, _ in rows) + pad
    H = sum(h + pad for _, h in rows) + pad
    out = Image.new("RGBA", (W, H), bg + (255,))
    y = pad
    for r, h in rows:
        for x, im in r:
            out.alpha_composite(im.convert("RGBA"), (x + pad, y))
        y += h + pad
    return out.resize((W * k, H * k), Image.NEAREST)
