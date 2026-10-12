"""P1-19 · P2-4 · P2-10 — 월드 결 정리.

1. 바닥 변주 타일 4종 × 지역(gate·hall·brewery = 빈 칸 13~16 / outer = 새 행 80~83, 옛 소품 칸은 건드리지 않음) → `tiles["1"]` 에 섞음.
   칸 가장자리 8도트는 원 바닥 그대로(이음 불변), 가운데만 그 지역 바닥 색으로 금·돌부스러기·때·지역 물건.
2. 그을음 알파 데칼 `structures/v3/decal_soot` 6종(둥근 알파 가장자리 — 칸 경계에서 사각으로 잘리지 않음).
3. 돌기둥 3면 명암 구조물 `structures/v3/pillar_stone`(행 = 지역 돌 램프 4, 열 = 온전·금·윗동 부서짐).
4. 노드 지도 플레이어 표식 `ui/map_marker_ghost`(먹 붓 망령, 6프레임 둥실).
5. 노드 세트피스 `structures/v3/setpiece_broken_cart`·`setpiece_spilled_casks`.
"""
import json
import math
import os
import shutil

from PIL import Image

import common
from common import SPR, TILES, SRC, dump, save_png, board, hexc, bayer, b2, INK, COLD_RIM, PAL, hx
from kit2 import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_STONE, R_NSTONE, R_WSTONE, R_CLOTH,
                  R_LEATHER, R_LIQ, R_BONE, contact, cyl, shade_mask, ell_mask, poly_mask, ell, pol, cap, line, selout,
                  splash, flame, embers, smoke, outline, qcol)

HERE = os.path.dirname(os.path.abspath(__file__))
T = (0, 0, 0, 0)


# ---------------------------------------------------------------- 1. 바닥 변주
def tile_palette(tile):
    cs = [c[:3] for n, c in tile.getcolors(4096) if c[3] == 255]
    return sorted(set(cs), key=lambda c: c[0] * 3 + c[1] * 6 + c[2])


def h2(x, y, s):
    n = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n & 0xFFFF) / 65535.0


def inner(x, y):
    return 8 <= x < 56 and 8 <= y < 56


def v_crack(t, pal, s):
    p = t.load()
    dark, mid, lite = pal[0], pal[len(pal) // 3], pal[-2]
    r = Rand(s)
    for k in range(3):
        x, y = 14 + r.i(0, 30), 12 + r.i(0, 8)
        for j in range(r.i(18, 34)):
            if inner(x, y):
                p[x, y] = dark + (255,)
                if inner(x - 1, y) and r.f() < 0.5:
                    p[x - 1, y] = lite + (255,)
            x += r.i(-1, 1); y += 1 if r.f() < 0.8 else 0
            if r.f() < 0.12:
                for b in range(r.i(3, 7)):
                    bx, by = x + b * (1 if k % 2 else -1), y + b // 2
                    if inner(bx, by):
                        p[bx, by] = dark + (255,)


def v_rubble(t, pal, s):
    c = Canvas(64, 64); c.paste(t, 0, 0)
    r = Rand(s)
    n_ = len(pal)
    ramp = [pal[n_ // 4], pal[n_ // 2], pal[(n_ * 2) // 3], pal[-3], pal[-2], pal[-1]]
    for k in range(9):
        x, y = r.i(12, 50), r.i(12, 50)
        rr = r.i(2, 5) if k < 3 else r.i(1, 2)
        c.ellipse((x + 1, y + 1, x + rr + 2, y + rr * 0.7 + 2), pal[0] + (255,))
        ell(c, (x, y, x + rr + 1, y + rr * 0.7 + 1), ramp, base=0.5, gain=0.9, soft=1)
    t.paste(c.im, (0, 0))


def v_grime(t, pal, s, ramp_extra=None):
    p = t.load()
    d1, d2 = pal[min(2, len(pal) - 1)], pal[min(3, len(pal) - 1)]
    for y in range(8, 56):
        for x in range(8, 56):
            d = math.hypot((x - 32) / 22, (y - 34) / 16)
            n = h2(x // 3, y // 3, s)
            if d < 0.75 + 0.3 * n:
                if bayer(x, y) < (1 - d) * 0.85:
                    p[x, y] = (d1 if d < 0.5 else d2) + (255,)


def v_region(t, pal, region, s):
    c = Canvas(64, 64); c.paste(t, 0, 0)
    r = Rand(s)
    if region == "outer":          # 흩어진 지푸라기 · 낙엽
        for k in range(14):
            x, y = r.i(10, 50), r.i(10, 52)
            L = r.i(4, 9)
            a = r.f() * math.pi
            for j in range(L):
                xx, yy = int(x + math.cos(a) * j), int(y + math.sin(a) * j * 0.5)
                if inner(xx, yy):
                    c.px(xx, yy, PL[3] if j % 3 else PL[2])
        for k in range(4):
            x, y = r.i(14, 48), r.i(14, 48)
            ell(c, (x, y, x + 4, y + 2), [WD[1], WD[2], WD[3], A[18]], base=0.5, soft=0)
    elif region == "gate":         # 진창 발자국 + 작은 물웅덩이
        splash(c, 36, 38, 11, 5, ramp=[SL[0], SL[1], SL[2], SL[3], SL[2], SL[5]], seed=s, glint=True, blobs=3)
        for k in range(4):
            x, y = 14 + k * 9, 20 + (k % 2) * 6
            c.ellipse((x, y, x + 3, y + 5), pal[0] + (255,))
            c.px(x + 1, y + 1, pal[1])
    elif region == "hall":         # 엎지른 술 얼룩 + 깨진 잔 조각
        splash(c, 30, 34, 13, 6, ramp=R_LIQ, seed=s, glint=True, blobs=4)
        for (x, y) in ((44, 22), (48, 26), (41, 27)):
            pol(c, [(x, y), (x + 3, y - 1), (x + 2, y + 2)], [G[3], G[6], G[9], G[12]], base=0.6, soft=0)
    elif region == "brewery":      # 쏟아진 보리 낟알 + 술통 테 얼룩(고리)
        for t_ in range(0, 360, 6):
            a = math.radians(t_)
            x, y = 26 + 12 * math.cos(a), 30 + 6 * math.sin(a)
            if t_ % 24:
                c.px(int(x), int(y), pal[1])
        for k in range(40):
            x, y = int(40 + (r.f() - 0.3) * 18), int(40 + (r.f() - 0.4) * 12)
            if inner(x, y):
                c.px(x, y, A[20] if k % 3 else A[19])
    t.paste(c.im, (0, 0))


REGION_TILES = {"gate": [13, 14, 15, 16], "hall": [13, 14, 15, 16], "brewery": [13, 14, 15, 16], "outer": [80, 81, 82, 83]}


def build_floors(items):
    before = os.path.join(HERE, "before")
    os.makedirs(before, exist_ok=True)
    rep = {}
    for region, idx in REGION_TILES.items():
        png = os.path.join(TILES, "v2", f"stage1_{region}.png")
        js = os.path.join(TILES, "v2", f"stage1_{region}.json")
        bp, bj = os.path.join(before, f"stage1_{region}.png"), os.path.join(before, f"stage1_{region}.json")
        if not os.path.exists(bp):            # 원본 사본(재실행 멱등 — 늘 원본에서 다시 만든다)
            shutil.copy(png, bp); shutil.copy(js, bj)
        im = Image.open(bp).convert("RGBA")
        meta = json.load(open(bj, encoding="utf-8"))
        cols, tw = meta["columns"], meta["tileWidth"]
        need_rows = max(idx) // cols + 1
        if need_rows > meta["rows"]:
            big = Image.new("RGBA", (im.width, need_rows * tw), T)
            big.paste(im, (0, 0))
            im = big
            meta["rows"] = need_rows
        for i, (fn, base_i) in enumerate(zip((v_crack, v_rubble, v_grime, None), (0, 1, 2, 3))):
            bx, by = (base_i % cols) * tw, (base_i // cols) * tw
            t = im.crop((bx, by, bx + tw, by + tw))
            pal = tile_palette(t)
            s = 62 + i * 7 + len(region)
            if fn:
                fn(t, pal, s)
            else:
                v_region(t, pal, region, s)
            ti = idx[i]
            im.paste(t, ((ti % cols) * tw, (ti // cols) * tw))
        floor = meta["tiles"]["1"]
        meta["tiles"]["1"] = [v for v in floor if v not in idx] * 2 + idx
        meta["floorVariants62b"] = {"indices": idx, "kinds": ["crack", "rubble", "grime", "region"],
                                    "regionKind": {"outer": "straw_leaves", "gate": "mud_puddle", "hall": "wine_shards", "brewery": "grain_ring"}[region],
                                    "note": "62 루프 2 P1-19 — 원 바닥 0~3 의 가장자리 8도트 그대로(이음 불변), 가운데만 변주. tiles['1'] = 원 바닥 목록 ×2 + 변주 4(변주 비중 약 22~33%)",
                                    "source": SRC + " · world.py"}
        if region == "outer":
            meta["floorVariants62b"]["rowAdded"] = "행 10(칸 80~83) 새로 — 옛 소품 칸(13~20·64~79)은 건드리지 않음"
        if not common.DRY:
            im.save(png, optimize=True)
            with open(js, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=1); f.write("\n")
        rep[region] = idx
        strip = Image.new("RGBA", (8 * 66, 64), (0, 0, 0, 255))
        for k, ti in enumerate([0, 1, 2, 3] + idx):
            strip.paste(im.crop(((ti % cols) * tw, (ti // cols) * tw, (ti % cols) * tw + tw, (ti // cols) * tw + tw)), (k * 66, 0))
        items.append(strip)
    return rep


# ---------------------------------------------------------------- 2. 그을음 데칼
SOOT = (10, 11, 16)


def soot(k):
    W, H = 128, 96
    im = Image.new("RGBA", (W, H), T)
    p = im.load()
    r = Rand(70 + k)
    rx, ry = [52, 40, 30, 56, 44, 34][k], [30, 24, 18, 22, 28, 20][k]
    blobs = [(64 + r.i(-14, 14), 50 + r.i(-6, 6), r.i(10, 22)) for _ in range(4 + k % 3)]
    for y in range(H):
        for x in range(W):
            d = math.hypot((x - 64) / rx, (y - 50) / ry)
            for bx, by, br in blobs:
                d = min(d, math.hypot((x - bx) / (br * 1.4), (y - by) / br) * 1.15)
            n = h2(x // 2, y // 2, k)
            d += (n - 0.5) * 0.25
            if d >= 1:
                continue
            a = int(min(1.0, (1 - d) * 1.8) * (150 if k < 4 else 110))
            if a <= 6:
                continue
            p[x, y] = SOOT + (a,)
            if k in (0, 3) and d < 0.25 and h2(x, y, 9) > 0.93:       # 탄 숯 조각
                p[x, y] = G[1][:3] + (255,)
            if k == 1 and d < 0.3 and h2(x, y, 11) > 0.985:
                p[x, y] = A[23][:3] + (255,)                          # 남은 불씨 한두 점
            if k == 5 and 0.55 < d < 0.75 and h2(x, y, 13) > 0.8:
                p[x, y] = G[4][:3] + (200,)                           # 재 고리
    return im


def build_soot(items):
    frames = [soot(k) for k in range(6)]
    meta = {
        "directions": ["any"], "pivot": {"x": 64, "y": 50}, "kind": "decal", "depth": "floor",
        "states": {"v0": [0], "v1": [1], "v2": [2], "v3": [3], "v4": [4], "v5": [5]},
        "variants": ["wide", "ember", "small", "streak", "blot", "ash_ring"],
        "pickRule": "방마다 좌표 해시로 변주 고르기, flipX 허용, 겹쳐 놓아도 됨(알파 곱)",
        "alpha": "그림 자체가 알파 가장자리(최대 150) — 칸 경계에서 사각으로 잘리지 않는다. 바닥 위·그림자 아래에 깐다",
        "colors": ["(10,11,16) 반투명", hexc(G[1]), hexc(A[23]), hexc(G[4])],
        "footprint": [2, 1.5], "solid": False, "paletteSwap": False, "version": "v3-r62b", "source": SRC + " · world.py",
        "replaces": "옛 사각 그을음 장식(타일 데칼 scorch 등)을 방 꾸밈으로 흩뿌릴 때 이 시트 권장",
    }
    b2.write_sheet("structures", "decal_soot", frames, 128, 96, meta, rows=1, durations=[1000] * 6)
    bg = []
    for f in frames:
        b = Image.new("RGBA", f.size, (92, 84, 72, 255)); b.alpha_composite(f); bg.append(b)
    items.append(board(bg, k=1, max_w=900))


# ---------------------------------------------------------------- 3. 돌기둥 3면
PILLAR_RAMPS = {
    "waste": [SL[0], G[2], G[3], PL[0], PL[1], PL[2], PL[3]],
    "outer": [SL[0], SL[1], SL[2], SL[3], SL[4], SL[5], SL[6]],
    "gate": [G[1], G[2], G[3], G[4], G[5], G[6], G[7]],
    "hall": [SL[0], WD[1], G[3], G[4], G[6], G[8], G[9]],
}


def pillar(ramp, state, seed):
    W, H = 96, 208
    c = Canvas(W, H)
    cx, base_y = 48, 196
    hw, d = 26, 13              # 반 폭 · 깊이(윗면 반높이)
    top_y = 36 if state != "broken" else 80
    contact(c, cx, base_y + 2, hw + 10, d + 2)
    r = Rand(seed)
    # 받침돌(넓은 단)
    for (y0, y1, w_) in ((base_y - 12, base_y, hw + 6),):
        c.poly([(cx - w_, y0), (cx, y0 + d), (cx, y1 + d), (cx - w_, y1)], ramp[3])
        c.poly([(cx, y0 + d), (cx + w_, y0), (cx + w_, y1), (cx, y1 + d)], ramp[1])
        c.poly([(cx - w_, y0), (cx, y0 - d), (cx + w_, y0), (cx, y0 + d)], ramp[5])
    # 몸통: 왼쪽 면(밝음) · 오른쪽 면(어두움) — 돌 단마다 줄눈·명암 변화
    yb = base_y - 12
    for y in range(top_y, yb + 1):
        for x in range(cx - hw, cx + hw + 1):
            left = x <= cx
            off = (cx - x) / hw * d if left else (x - cx) / hw * d
            yy = y + (d - off)                    # 면 위 위치(아래 모서리 기준 맞춤)
            if yy > yb + d - (d - off) * 0 and False:
                continue
            course = int((y - top_y) / 22)
            fy = (y - top_y) % 22
            if left:
                s = 0.62 - 0.12 * ((cx - x) / hw) * 0 + 0.04 * ((course * 7 + seed) % 3)
                col = qcol(ramp, s - (0.18 if fy < 1 else 0) - 0.15 * (1 - (cx - x) / hw) * 0.3, x, y)
            else:
                s = 0.30 + 0.04 * ((course * 5 + seed) % 3) - 0.08 * ((x - cx) / hw)
                col = qcol(ramp, s - (0.15 if fy < 1 else 0), x, y)
            # 줄눈(가로) · 세로 줄눈 엇갈림
            if fy == 0 or (fy < 21 and (x - cx + (11 if course % 2 else 0)) % 26 == 0 and x != cx):
                col = ramp[0] if not left else ramp[1]
            py = y + int(off)  # 3/4: 면의 아래 모서리가 가운데로 갈수록 내려감
            c.px(x, py, col)
    # 가운데 모서리(빛 받는 날)
    for y in range(top_y + d, yb + d + 1):
        c.px(cx, y, ramp[5] if (y // 3) % 4 else ramp[4])
    # 윗면
    if state != "broken":
        c.poly([(cx - hw, top_y), (cx, top_y - d), (cx + hw, top_y), (cx, top_y + d)], ramp[5])
        for k in range(hw):
            c.px(cx - hw + k, int(top_y - k * d / hw), ramp[6])
        c.poly([(cx - hw - 4, top_y - 2), (cx, top_y - d - 4), (cx + hw + 4, top_y - 2), (cx, top_y + d + 2)], ramp[4])
        c.poly([(cx - hw - 4, top_y - 2), (cx, top_y + d + 2), (cx, top_y + d + 7), (cx - hw - 4, top_y + 3)], ramp[3])
        c.poly([(cx, top_y + d + 2), (cx + hw + 4, top_y - 2), (cx + hw + 4, top_y + 3), (cx, top_y + d + 7)], ramp[1])
        c.poly([(cx - hw - 2, top_y - 3), (cx, top_y - d - 3), (cx + hw + 2, top_y - 3), (cx, top_y + d)], ramp[5])
        for k in range(hw):
            c.px(cx - hw - 2 + k, int(top_y - 3 - k * (d) / hw), ramp[6])
    else:
        # 부서진 윗동: 들쭉날쭉한 단면 + 떨어진 돌
        pts = [(cx - hw, top_y)] + [(cx - hw + k * 6, top_y - r.i(0, 10) + (k * d // 9)) for k in range(1, 9)] + [(cx + hw, top_y), (cx, top_y + d)]
        c.poly(pts, ramp[4])
        for (x, y, rr) in ((cx + 30, base_y - 2, 6), (cx - 34, base_y + 4, 5), (cx + 20, base_y + 10, 4)):
            ell(c, (x - rr, y - rr * 0.7, x + rr, y + rr * 0.7), ramp, base=0.5, gain=0.9, soft=1)
    if state in ("cracked", "broken"):
        x, y = cx - 10, top_y + 30
        for j in range(60):
            c.px(x, y, ramp[0]); c.px(x - 1, y, ramp[5])
            x += r.i(-1, 1); y += 1
            if r.f() < 0.1:
                for b in range(5):
                    c.px(x + b, y + b // 2, ramp[0])
        x, y = cx + 12, top_y + 50
        for j in range(30):
            c.px(x, y, ramp[0]); x += r.i(-1, 1); y += 1
    # 이끼·그을음(아래쪽)
    for y in range(yb - 20, yb + d):
        for x in range(cx - hw, cx + hw):
            if c.get(x, y)[3] and h2(x, y, seed) > 0.9 and bayer(x, y) < 0.5:
                c.px(x, y, ramp[1])
    im = c.im
    selout(im, SL[0][:3] if len(SL[0]) else SL[0])
    return im


def build_pillars(items):
    frames = []
    regions = list(PILLAR_RAMPS)
    for ri, reg in enumerate(regions):
        for si, st in enumerate(("whole", "cracked", "broken")):
            frames.append(pillar(PILLAR_RAMPS[reg], st, 5 + ri * 3 + si))
    meta = {
        "directions": regions, "rowsAre": "regions", "pivot": {"x": 48, "y": 196},
        "states": {"whole": [0], "cracked": [1], "broken": [2]}, "frameRule": "프레임 = 지역 행 × 3 + 상태 열",
        "footprint": [1, 1], "solid": True, "blocksProjectiles": True, "depth": "y", "occludeAbove": 150,
        "design": "3면 명암 — 윗면(가장 밝음)·왼쪽 면(빛)·오른쪽 면(그늘), 돌 단 줄눈 엇갈림, 받침돌. 같은 자갈 블록 반복 대체(P1-19)",
        "paletteSwap": False, "palette": "지역 돌 램프(SL·G·PL·WD) — 새 색 없음", "version": "v3-r62b", "source": SRC + " · world.py",
    }
    b2.write_sheet("structures", "pillar_stone", frames, 96, 208, meta, rows=len(regions), durations=[1000] * 3)
    items.append(board(frames, bg=(70, 60, 50), k=1, max_w=1400))


# ---------------------------------------------------------------- 4. 지도 표식(먹 붓 망령)
S_UI = [hx(c) for c in PAL["ui"]["ramp"]]


def marker(k):
    W, H = 40, 56
    im = Image.new("RGBA", (W, H), T)
    p = im.load()
    bob = [0, -1, -2, -2, -1, 0][k]
    cx, top = 20, 6 + bob
    for y in range(H):
        for x in range(W):
            yy = y - top
            if yy < 0:
                continue
            # 머리(둥근) + 어깨에서 아래로 갈라지는 붓 꼬리(바람에 흔들림)
            if yy < 12:
                ins = math.hypot((x - cx) / 5.4, (yy - 6) / 6.2) < 1
            else:
                t = (yy - 12) / 34
                if t > 1:
                    continue
                sway = math.sin(t * 3 + k * 1.05) * 3.5 * t
                half = (4 + 6 * min(1, t / 0.22)) * (1 - max(0, t - 0.22) / 0.78) ** 0.9 + 0.5
                ins = abs(x - cx - sway) < half
                if ins and t > 0.5 and h2(x, y // 2, k) > 1.25 - t:
                    ins = False                                       # 마른 붓 갈라짐(세로 결)
            if ins:
                p[x, y] = INK[1] + (255,)
                if yy >= 0 and x > 0 and p[x - 1, y][3] == 0:
                    p[x, y] = INK[3] + (255,)                         # 왼쪽 젖은 먹 윤
    # 먹 테(종이 위에서 읽히게 — 세피아 S4 한 겹 바깥)
    src = im.copy(); sp = src.load()
    for y in range(H):
        for x in range(W):
            if sp[x, y][3]:
                continue
            if any(0 <= x + a < W and 0 <= y + b < H and sp[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                p[x, y] = S_UI[4] + (255,)
    # 눈 하나(호박, 등 상흔 빛) + 발밑 붓 점
    p[cx + 2, top + 6] = A[24][:3] + (255,)
    p[cx + 3, top + 6] = A[23][:3] + (255,)
    for x in range(cx - 6, cx + 7):
        if abs(x - cx) < 6 - (k % 2):
            p[x, H - 3] = S_UI[1] + (180,)
    return im


def build_marker(items):
    frames = [marker(k) for k in range(6)]
    sheet = Image.new("RGBA", (40 * 6, 56), T)
    for i, f in enumerate(frames):
        sheet.alpha_composite(f, (i * 40, 0))
    meta = {"image": "map_marker_ghost.png", "frameWidth": 40, "frameHeight": 56, "frames": 6, "frameDurationsMs": [160] * 6, "loop": True,
            "pivot": {"x": 20, "y": 53}, "uiScale": "UI 1배(지도 그림 위 논리 px)", "kind": "map_marker",
            "design": "먹 붓으로 그은 망령 — 둥근 머리 + 갈라지는 붓 꼬리, 호박 눈 하나. 세피아 지도와 같은 먹·종이 색(흰 도트 인형 대체, P2-4)",
            "moveHint": "노드 이동 중엔 표식을 길 위로 보간 이동 + 꼬리 쪽을 이동 반대 방향으로 flipX(제안)",
            "palette": "먹 #141516 + UI 세피아 S1·S4 + 호박 A23·A24", "source": SRC + " · world.py"}
    if not common.DRY:
        save_png(sheet, os.path.join(SPR, "ui", "map_marker_ghost.png"))
        dump(meta, os.path.join(SPR, "ui", "map_marker_ghost.json"))
    bg = Image.new("RGBA", sheet.size, S_UI[3] + (255,)); bg.alpha_composite(sheet)
    items.append(bg.resize((bg.width * 3, bg.height * 3), Image.NEAREST))


# ---------------------------------------------------------------- 5. 세트피스
def broken_cart(k):
    W, H = 288, 200
    c = Canvas(W, H)
    contact(c, 140, 170, 120, 22)
    # 기운 짐칸(왼쪽 바퀴 빠져 주저앉음): 바닥판 + 옆판
    pol(c, [(46, 120), (196, 96), (232, 118), (82, 150)], R_WOODG, base=0.55, gain=0.7, soft=3)
    for i in range(6):
        line(c, (52 + i * 26, 121 - i * 4), (88 + i * 26, 149 - i * 4), WD[1])
    pol(c, [(46, 120), (196, 96), (196, 70), (50, 96)], R_WOOD, base=0.5, gain=0.8, soft=2)    # 뒤 옆판
    for y in (78, 88):
        line(c, (50, y + 18), (196, y - 6), WD[1])
    pol(c, [(82, 150), (232, 118), (232, 100), (86, 128)], R_WOOD, base=0.42, gain=0.8, soft=2)  # 앞 옆판(그늘)
    line(c, (86, 139), (232, 109), WD[1])
    # 바퀴: 오른쪽 하나는 붙어 있음, 왼쪽 하나는 빠져 바닥에 누움
    for (x, y, rx, ry) in ((206, 132, 30, 34),):
        m = ell_mask(W, H, (x - rx, y - ry, x + rx, y + ry)); m2 = ell_mask(W, H, (x - rx + 6, y - ry + 6, x + rx - 6, y + ry - 6))
        mp, mp2 = m.load(), m2.load()
        for yy in range(H):
            for xx in range(W):
                if mp2[xx, yy] > 127:
                    mp[xx, yy] = 0
        shade_mask(c, m, R_WOOD, base=0.5, gain=0.8, soft=2)
        for a in range(0, 360, 45):
            line(c, (x, y), (int(x + (rx - 4) * math.cos(math.radians(a))), int(y + (ry - 4) * math.sin(math.radians(a)))), WD[2])
        ell(c, (x - 5, y - 5, x + 5, y + 5), R_IRON, base=0.6, soft=1)
    m = ell_mask(W, H, (20, 158, 84, 186)); m2 = ell_mask(W, H, (30, 163, 74, 181))
    mp, mp2 = m.load(), m2.load()
    for yy in range(H):
        for xx in range(W):
            if mp2[xx, yy] > 127:
                mp[xx, yy] = 0
    shade_mask(c, m, R_WOOD, base=0.5, gain=0.8, soft=2)
    # 끌채(부러져 앞으로 처박힘)
    line(c, (226, 112), (280, 150), WD[3], w=3); line(c, (230, 118), (270, 160), WD[2], w=2)
    # 쏟아진 짐: 자루 둘·술병·지푸라기
    ell(c, (96, 140, 132, 164), R_CLOTH, base=0.5, gain=0.85, soft=3)
    ell(c, (124, 150, 150, 172), R_CLOTH, base=0.45, gain=0.85, soft=3)
    for kx in range(10):
        x, y = 150 + kx * 7, 170 + (kx % 3) * 3
        line(c, (x, y), (x + 6, y - 2), PL[3])
    # 쓰러진 짐꾼 자리 표시 없음(빈 마차) · 등불 하나가 꺼져 가는 불씨
    c.px(64, 112, A[23 + (k % 2)]); c.px(65, 111, A[24])
    im = c.im; selout(im, SL[0])
    return im


def spilled_casks(k):
    W, H = 256, 208
    c = Canvas(W, H)
    splash(c, 132, 176, 96, 20, ramp=R_LIQ, seed=40 + k, glint=True, blobs=6)
    contact(c, 120, 150, 90, 20)
    # 세운 통 둘 + 쓰러져 터진 통 하나 + 깨진 통널
    cyl(c, 70, 80, 150, 26, R_WOOD, bulge=0.12, staves=7, hoops=((92, 3), (138, 3)), seed=3)
    cyl(c, 122, 104, 162, 22, R_WOOD, bulge=0.12, staves=6, hoops=((114, 3), (152, 3)), seed=4)
    # 쓰러진 통(옆으로 — 타원 몸통)
    pol(c, [(150, 150), (214, 132), (224, 168), (162, 186)], R_WOOD, base=0.5, gain=0.8, soft=4)
    for t in (0.2, 0.8):
        x0, y0 = 150 + 64 * t, 150 - 18 * t
        line(c, (int(x0), int(y0)), (int(x0 + 12), int(y0 + 36)), R_IRON[3], w=2)
    ell(c, (208, 128, 232, 172), R_WOOD, base=0.55, soft=2)
    c.ellipse((212, 136, 228, 166), A[16])
    # 터진 구멍에서 술 흐름
    for j in range(16):
        c.px(186 + j, 176 + j // 3, A[20] if j % 3 else A[22])
    for (x, y, a) in ((96, 182, 0.3), (40, 170, -0.5), (200, 192, 0.1)):
        pol(c, [(x, y), (x + 14 * math.cos(a), y + 14 * math.sin(a)), (x + 14 * math.cos(a) + 2, y + 14 * math.sin(a) + 4), (x + 2, y + 4)], R_WOOD, base=0.5, soft=1)
    c.px(130, 180, A[24]); c.px(60, 186, A[23])
    im = c.im; selout(im, SL[0])
    return im


def build_setpieces(items):
    frames = [broken_cart(0)]
    meta = {"directions": ["any"], "pivot": {"x": 140, "y": 176}, "footprint": [4, 2], "solid": True, "blocksProjectiles": True,
            "depth": "y", "occludeAbove": 120, "states": {"idle": [0]}, "kind": "setpiece",
            "usage": "P2-10 노드 세트피스 — 외곽 거리·성문 길 전투 노드 가운데 하나. 엄폐(짐칸·바퀴), 쏟아진 자루는 통과",
            "solidRects": [{"x": -96, "y": -40, "w": 176, "h": 44, "note": "피벗 기준 논리 도트 — 짐칸 몸만"}],
            "region": ["outer", "gate", "waste"], "flipX": "허용", "paletteSwap": True, "version": "v3-r62b", "source": SRC + " · world.py"}
    b2.write_sheet("structures", "setpiece_broken_cart", frames, 288, 200, meta, rows=1, durations=[1000])
    f2 = [spilled_casks(0)]
    meta2 = {"directions": ["any"], "pivot": {"x": 128, "y": 170}, "footprint": [4, 3], "solid": True, "blocksProjectiles": True,
             "depth": "y", "occludeAbove": 100, "states": {"idle": [0]}, "kind": "setpiece",
             "usage": "P2-10 노드 세트피스 — 양조장·외곽 거리 노드. 세운 통 둘 = 엄폐, 술 웅덩이 = 불붙음(pool_liquor 와 같은 규칙 제안)",
             "liquorPool": {"x": 4, "y": 6, "rx": 96, "ry": 20, "note": "피벗 기준 도트 — 불이 닿으면 pool_liquor_fire 를 이 자리에 겹침(제안)"},
             "region": ["brewery", "outer", "hall"], "flipX": "허용", "paletteSwap": True, "version": "v3-r62b", "source": SRC + " · world.py"}
    b2.write_sheet("structures", "setpiece_spilled_casks", f2, 256, 208, meta2, rows=1, durations=[1000])
    items.append(board(frames + f2, bg=(70, 60, 50), k=1))


def build(preview_path=None):
    items = []
    build_floors(items)
    build_soot(items)
    build_pillars(items)
    build_marker(items)
    build_setpieces(items)
    if preview_path:
        board(items, bg=(36, 34, 34), k=1, max_w=2000).save(preview_path)
