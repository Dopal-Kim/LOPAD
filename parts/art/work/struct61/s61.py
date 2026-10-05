"""61라운드 단계 2 (AR-4 · P3 · 방 다양화 소품) 공용 — import 경로·셰이딩 도구 재수출·조각 내기·미리보기.

- 그림 도구는 props_v3 `pk`·`common`, bundle2 `b2`·`structs`, floor1q60 `fk64`·`regions64` 를 읽기만 한다(수정 없음).
- 단위: 도트. pixelScale 0.5 → 64 도트 = 1칸(논리 32px).
- 색: lopad.json gray(G) + 1층 램프 A16~27 + v2 재질 블록 SL·WD·PL(+NT) — 새 색 없음.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
for p in ("../bundle2", "../props_v3", "../floor1q60", "../atlas57", "../v2_outer"):
    q = os.path.normpath(os.path.join(HERE, p))
    if q not in sys.path:
        sys.path.insert(0, q)

from PIL import Image, ImageDraw  # noqa: E402

import b2  # noqa: E402
from b2 import (Canvas, Rand, G, A, SL, WD, PL, X, U, CLEAR, R_WOOD, R_WOODG, R_IRON, R_STONE, R_NSTONE,  # noqa: E402,F401
                R_WSTONE, R_CLOTH, R_CLOTHG, R_EARTH, R_COPPER, R_LIQ, R_BONE, FLAME, contact, cyl, plank_box,
                shade_mask, mask, splash, flame, embers, glass_lantern, stone_blob, face, grain, ell_mask, poly_mask,
                outline, qcol, clamp, lam, tohex, EMISSIVE_HEX, pcommon)
import structs  # noqa: E402,F401
from structs import mark, states_json, L, R_CLAY, R_GLAZE, R_BRICK, R_BANNER, R_GLASS  # noqa: E402,F401

SPR = os.path.join(ROOT, "assets", "sprites")
TILES = os.path.join(ROOT, "assets", "tiles")
PALETTE_NOTE = b2.PALETTE_NOTE
R_IRONB = [SL[1], G[4], G[6], G[8], G[10], G[12]]                    # 밝은 쇠테(독주 술통)
R_WOODD = [SL[0], WD[0], WD[1], WD[2], WD[3], WD[4]]                 # 짙은 참나무
R_ASH = [SL[0], G[2], G[3], G[5], G[7], G[9]]                         # 재·숯
R_PAPER = [PL[1], PL[2], PL[3], PL[4], G[12], G[13]]                  # 장부 종이
EMB = [A[19], A[21], A[23], A[24], A[25]]                             # 불씨


def blank(w, h):
    return Canvas(w, h)


def paste(c, im, x=0, y=0):
    c.paste(im, x, y)


def shift_im(im, dx, dy):
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(im, (dx, dy)) if dx >= 0 and dy >= 0 else out.paste(im, (dx, dy), im)
    return out


def brighten(im, ramp_map):
    """정확 색 치환(램프 한 단 밝게 등) — 맞음 번쩍임용."""
    px = im.load()
    out = im.copy()
    po = out.load()
    for y in range(im.height):
        for x in range(im.width):
            c = px[x, y]
            if c[3] == 255 and c[:3] in ramp_map:
                po[x, y] = ramp_map[c[:3]] + (255,)
    return out


def step_map(*ramps):
    """램프들의 각 칸 → 한 칸 밝은 칸 사전(RGB)."""
    m = {}
    for r in ramps:
        for i, c in enumerate(r):
            m.setdefault(tuple(c[:3]), tuple(r[min(len(r) - 1, i + 1)][:3]))
    return m


def shatter(src, center, t, seed, n=9, spread=1.0, ground=None, gravity=60.0, flatten=False, keep_below=None, land=False):
    """src 그림을 보로노이 조각으로 나눠 center 에서 바깥으로 흩뜨린다(t 0..1).
    ground = 조각이 내려앉는 바닥 y(조각 아래 끝 기준). keep_below = 이 y 아래는 '밑동'으로 제자리에 둔다."""
    W, H = src.size
    r = Rand(seed)
    bb = src.getbbox()
    if not bb:
        return src.copy()
    x0, y0, x1, y1 = bb
    seeds = [(r.i(x0, x1), r.i(y0, y1)) for _ in range(n)]
    sp = src.load()
    pieces = [[] for _ in seeds]
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bp = base.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = sp[x, y]
            if c[3] < 255:
                continue                                                   # 반투명(접지 그림자)은 조각에 싣지 않음 — 섞인 색 방지
            if keep_below is not None and y >= keep_below:
                bp[x, y] = c
                continue
            k = min(range(len(seeds)), key=lambda i: (seeds[i][0] - x) ** 2 + (seeds[i][1] - y) ** 2)
            pieces[k].append((x, y, c))
    out = base
    op = out.load()
    for k, pts in enumerate(pieces):
        if not pts:
            continue
        sx, sy = seeds[k]
        vx = (sx - center[0]) * 0.9 * spread + r.i(-6, 6)
        vy = (sy - center[1]) * 0.6 * spread - r.i(8, 20) * spread
        dx = vx * t
        dy = vy * t + gravity * t * t
        maxy = max(p[1] for p in pts)
        if ground is not None and (land or maxy + dy > ground):
            dy = ground - maxy - (r.i(0, 6) if land else 0)
        for (x, y, c) in pts:
            yy = y
            if flatten and ground is not None:
                yy = maxy - (maxy - y) * 0.5
            nx, ny = int(round(x + dx)), int(round(yy + dy))
            if 0 <= nx < W and 0 <= ny < H:
                op[nx, ny] = c
    return out


def droplets(c, cx, cy, t, n, seed, ramp=None, spread=40):
    ramp = ramp or [A[18], A[20], A[22]]
    r = Rand(seed)
    for _ in range(n):
        ang = -math.pi * (0.1 + 0.8 * r.f())
        sp = spread * (0.4 + 0.6 * r.f())
        x = cx + math.cos(ang) * sp * t
        y = cy + math.sin(ang) * sp * t * 0.7 + 40 * t * t
        col = ramp[r.i(0, len(ramp) - 1)]
        c.px(int(x), int(y), col)
        if r.f() < 0.5:
            c.px(int(x), int(y) + 1, ramp[0])


def colors(im):
    return {p[:3] for p in im.get_flattened_data() if p[3] > 0}


def semi(im):
    return sum(1 for p in im.get_flattened_data() if 0 < p[3] < 255)


# 61라운드 AR-4 대상(1층에서 실제로 쓰는 v1 구조물 — README 61라운드 절 표)
STRUCTS = ["crate_f1", "chest", "grave", "bonfire", "barrel", "ledger", "cask", "counter", "cellar_wall"]
SETS = ["set_waste_fire_ring", "set_outer_plaza", "set_outer_stall", "set_outer_lamppost", "set_gate_brazier",
        "set_brewery_barrel_stack", "set_hall_rug", "set_hall_long_table", "battlefield_banner", "battlefield_weapon",
        "battlefield_fallen", "battlefield_dummy", "tutorial_sign", "tutorial_sign_move", "tutorial_sign_attack",
        "tutorial_sign_dash", "tutorial_sign_skill"]


def v1json(id_):
    import json
    return json.load(open(os.path.join(SPR, "structures", id_ + ".json"), encoding="utf-8"))
