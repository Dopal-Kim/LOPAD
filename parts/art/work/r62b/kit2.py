"""r62b 그림 도구 — 카드·아이콘·NPC·세트피스 공용(도트 셰이딩 원형). Claude 직접 디자인(Gemini 402).

빛 = 좌상단(바이블). 색 = lopad gray + 1층 램프(A16~27) + v2 재질 SL·WD·PL + 무기 색(§28, 효과 덩어리만).
"""
import importlib.util
import math
import os

from PIL import Image, ImageDraw

from common import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_STONE, R_NSTONE, R_WSTONE, R_CLOTH,
                    R_CLOTHG, R_EARTH, R_LIQ, R_BONE, FLAME, contact, cyl, shade_mask, mask, splash, flame, embers,
                    ell_mask, poly_mask, outline, qcol, clamp, WORK, BAYER, glass_lantern, plank_box)

_spec = importlib.util.spec_from_file_location("r62a_birth", os.path.join(WORK, "r62a", "birthprops.py"))
BP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BP)
capsule, capsule_mask, spear_shaft, shield, blood, arrow_stuck, smoke, dirt_mound, lying_body = (
    BP.capsule, BP.capsule_mask, BP.spear_shaft, BP.shield, BP.blood, BP.arrow_stuck, BP.smoke, BP.dirt_mound, BP.lying_body)
R_SOLDIER, R_FOE, R_SKIN, R_HELM, R_LEATHER, R_BLOOD, R_DIRT = (
    BP.R_SOLDIER, BP.R_FOE, BP.R_SKIN, BP.R_HELM, BP.R_LEATHER, BP.R_BLOOD, BP.R_DIRT)
R_PAPER = [SL[0], WD[2], PL[1], PL[2], PL[3], PL[4]]
R_AMBERGLOW = [A[17], A[18], A[19], A[20], A[21], A[22]]
R_GOLD = [WD[1], A[18], A[19], A[20], A[22], A[24]]
R_INKB = [G[0], G[1], G[2], G[3], G[4]]
OUT = G[1]


def ell(c, box, ramp, **kw):
    shade_mask(c, ell_mask(c.w, c.h, box), ramp, **kw)


def pol(c, pts, ramp, **kw):
    shade_mask(c, poly_mask(c.w, c.h, pts), ramp, **kw)


def cap(c, pts, r, ramp, **kw):
    kw.setdefault("base", 0.5); kw.setdefault("gain", 0.7); kw.setdefault("soft", 2)
    shade_mask(c, capsule_mask(c.w, c.h, pts, r), ramp, **kw)


def line(c, a, b, col, w=1):
    ax, ay = a
    bx, by = b
    n = int(max(abs(bx - ax), abs(by - ay))) + 1
    for i in range(n):
        t = i / max(1, n - 1)
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        for k in range(w):
            c.px(int(round(x)) + k, int(round(y)), col)


def selout(im, col=OUT, only_empty=True):
    """바깥 1도트 외곽선(카드 가독성). 반투명 접지 그림자 칸은 외곽 대상에서 뺀다."""
    w, h = im.size
    p = im.load()
    src = [[p[x, y][3] >= 200 for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if src[y][x]:
                continue
            if any(0 <= x + dx < w and 0 <= y + dy < h and src[y + dy][x + dx]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p[x, y] = tuple(col[:3]) + (255,)
    return im


def slab(c, cx, cy, hw, hh, th=7, ramp=R_NSTONE, seed=1, tiles=2):
    """쿼터뷰 돌바닥 판(마름모 윗면 + 앞 두 면). 개성 카드(ui_traits)와 같은 결."""
    r = Rand(seed)
    top = [(cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy)]
    # 앞면(왼쪽 밝게, 오른쪽 어둡게)
    c.poly([(cx - hw, cy), (cx, cy + hh), (cx, cy + hh + th), (cx - hw, cy + th)], ramp[2])
    c.poly([(cx, cy + hh), (cx + hw, cy), (cx + hw, cy + th), (cx, cy + hh + th)], ramp[1])
    m = poly_mask(c.w, c.h, top)
    mp = m.load()
    for y in range(c.h):
        for x in range(c.w):
            if mp[x, y] > 127:
                u = ((x - cx) / hw + (y - cy) / hh) * tiles / 2
                v = ((x - cx) / hw - (y - cy) / hh) * tiles / 2
                fu, fv = u - math.floor(u), v - math.floor(v)
                cell_ = (math.floor(u) * 7 + math.floor(v) * 13 + seed) % 5
                s = 0.42 + 0.08 * cell_ / 4 - 0.18 * ((y - cy) / hh)
                if fu < 0.035 * tiles or fv < 0.035 * tiles:
                    col = ramp[0]
                else:
                    col = qcol(ramp, s, x, y)
                c.px(x, y, col)
    # 윗면 위·왼 모서리 밝은 선
    for k in range(hw):
        c.px(cx - hw + k, int(cy - k * hh / hw), ramp[4])
    for _ in range(3):   # 금
        x, y = cx + r.i(-hw // 2, hw // 2), cy + r.i(-hh // 2, hh // 2)
        for j in range(r.i(4, 9)):
            c.px(x, y, ramp[0]); x += r.i(-1, 1) or 1; y += r.i(0, 1)


def halo(c, cx, cy, rx, ry, ramp, k=0.55):
    """디더 빛무리(뒤에 깔기 — 빈 칸에만)."""
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            d = math.hypot((x - cx) / rx, (y - cy) / ry)
            if d > 1 or c.get(x, y)[3]:
                continue
            t = (1 - d) * k
            th = (BAYER[y % 4][x % 4] + 0.5) / 16
            if t > th * 0.9:
                c.px(x, y, ramp[min(len(ramp) - 1, int((1 - d) * len(ramp)))])


def sparks(c, pts, ramp=(A[23], A[25], A[26])):
    for i, (x, y) in enumerate(pts):
        c.px(x, y, ramp[i % len(ramp)])


def star(c, cx, cy, r, col_core, col_ray):
    for k in range(-r, r + 1):
        cc = col_core if abs(k) < 2 else col_ray
        c.px(cx + k, cy, cc)
        c.px(cx, cy + k, cc)
    for k in range(-r // 2, r // 2 + 1):
        c.px(cx + k, cy + k, col_ray)
        c.px(cx + k, cy - k, col_ray)
