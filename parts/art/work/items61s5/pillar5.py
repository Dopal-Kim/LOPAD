"""61 단계 5 (P13 §3) 보스방 기둥 무너짐 — `structures/v3/boss1_pillar` 18 → 30 프레임.

0~17 = 61 단계 2·3 그림 그대로(입력 사본 `before61s5/boss1_pillar_grid.png` — 다시 돌려도 같은 결과, 픽셀 대조 assert).
18~27 collapse(10) : 흔들림 → 금 자리에서 윗동이 주저앉으며 기울어 내려앉음 → 큰 먼지 → 가라앉음.
28~29 rubble(2)   : 낮은 잔해(기단 + 드럼 조각·주두 판·떨어진 휘장·돌무더기). 29 유지.
"""
import math
import os

from PIL import Image

from kit5 import Canvas, Rand, G, A, SL, WD, PL, R_NSTONE, stone_blob, disc, HERE
import sys
sys.path.insert(0, os.path.join(HERE, "..", "boss1_v3"))
from pk import face, contact, qcol, mask, shade_mask  # noqa: E402

PW, PH = 160, 448
PIV = (80, 440)
SRC_GRID = os.path.join(HERE, "before61s5", "boss1_pillar_grid.png")
BREAK = (86, 262)                      # 금 시작점(= impactPoint) — 윗동이 꺾이는 자리
R_GOLD = [(0x3f, 0x27, 0x1d, 255), (0x65, 0x3b, 0x24, 255), (0x8b, 0x4d, 0x22, 255), (0xb0, 0x61, 0x1a, 255), (0xd6, 0x7a, 0x11, 255)]
BANNER = [SL[0], A[16], A[17], A[18], WD[4]]
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def old_frames():
    sh = Image.open(SRC_GRID).convert("RGBA")
    return [sh.crop((i * PW, 0, (i + 1) * PW, PH)) for i in range(sh.width // PW)]


# ---------------------------------------------------------------------------------------- 층 나누기
def col_mask_fn(x, y):
    """몸통(반지름 40 원기둥, 70~360+밑 곡선) + 주두(26~133 × 14~70)."""
    if 14 <= y <= 70 and 26 <= x <= 133:
        return True
    if 40 <= x <= 120 and 70 <= y:
        u = (x - 80) / 40.0
        nz = math.sqrt(max(0.0, 1 - u * u))
        return y <= 360 + int(10 * nz)
    return False


def cut_y(x):
    return BREAK[1] + 7 * math.sin(x * 0.31) + (x - 80) * 0.22


def split_layers(im):
    """crack3 그림 → (기단층, 아랫동, 윗동). 기단층의 몸통 자리는 다시 그린 기단 윗면으로 채운다."""
    W, H = im.size
    p = im.load()
    base = plinth()
    bp = base.load()
    lower = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    upper = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lp, up = lower.load(), upper.load()
    for y in range(H):
        for x in range(W):
            c = p[x, y]
            if not c[3]:
                continue
            if col_mask_fn(x, y) or (y < 330 and 20 <= x <= 140):
                if y < cut_y(x):
                    up[x, y] = c
                else:
                    lp[x, y] = c
            elif y >= 330 and c[3] == 255:
                bp[x, y] = c          # 기단 위 돌 부스러기 등 crack3 그림을 기단층에 그대로
    return base, lower, upper


def plinth():
    """boss1_v3/props.py pillar_frame 의 기단 부분만 같은 식으로(몸통 뒤에 가려졌던 윗면을 채우려고)."""
    c = Canvas(PW, PH)
    contact(c, 80, 438, 76, 8)
    x0, x1 = 16, 143
    face(c, x0, 414, x1, 439, R_NSTONE, 0.45, grad=0.3)
    c.hline(x0, x1, 414, G[8]); c.hline(x0, x1, 439, G[1])
    face(c, x0, 318, x1, 413, R_NSTONE, 0.62, grad=0.18)
    for y in (350, 382):
        c.hline(x0 + 2, x1 - 2, y, G[3])
    c.vline(80, 318, 413, G[3])
    c.hline(x0, x1, 318, G[9]); c.vline(x0, 318, 439, G[2]); c.vline(x1, 318, 439, G[1])
    x2, x3 = 30, 129
    face(c, x2, 380, x3, 398, R_NSTONE, 0.5, grad=0.25)
    face(c, x2, 330, x3, 379, R_NSTONE, 0.72, grad=0.15)
    c.hline(x2, x3, 330, G[10]); c.hline(x2, x3, 398, G[1]); c.vline(x3, 330, 398, G[1])
    return c.im


# ---------------------------------------------------------------------------------------- 조각·먼지
def chunk(c, x, y, r, seed):
    """작은 돌 조각(빠른 3톤): 왼쪽 위 빛 G8 · 몸 G5 · 오른쪽 아래 G2 · 테 G1."""
    rr = Rand(seed)
    pts = []
    for k in range(6):
        a = 2 * math.pi * k / 6 + rr.f() * 0.5
        f = 0.7 + 0.45 * rr.f()
        pts.append((x + math.cos(a) * r * f, y + math.sin(a) * r * f * 0.85))
    from PIL import ImageDraw
    m = Image.new("L", (c.w, c.h), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    bb = m.getbbox()
    if not bb:
        return
    mp = m.load()
    for yy in range(bb[1], bb[3]):
        for xx in range(bb[0], bb[2]):
            if mp[xx, yy] < 128:
                continue
            edge_br = mp[min(c.w - 1, xx + 1), yy] < 128 or mp[xx, min(c.h - 1, yy + 1)] < 128
            edge_tl = mp[max(0, xx - 1), yy] < 128 or mp[xx, max(0, yy - 1)] < 128
            d = (xx - x) + (yy - y)
            col = G[1] if edge_br else (G[8] if edge_tl else (G[6] if d < -r * 0.3 else (G[4] if d < r * 0.5 else G[3])))
            c.px(xx, yy, col)


def cloud(c, puffs, density=1.0, seed=0):
    """먼지 구름: 둥근 덩이들의 합(불투명). density<1 이면 바이어 문턱으로 성기게(얇은 먼지).
    덩이마다 아래·오른쪽 그늘 PL2, 몸 PL3, 왼쪽 위 빛 G11·G12."""
    W, H = c.w, c.h
    val = {}
    for (px_, py_, r) in puffs:
        for y in range(int(py_ - r) - 1, int(py_ + r) + 2):
            for x in range(int(px_ - r * 1.15) - 1, int(px_ + r * 1.15) + 2):
                if not (2 <= x < W - 2 and 2 <= y < H - 2):
                    continue
                dx, dy = (x - px_) / (r * 1.15), (y - py_) / r
                d = dx * dx + dy * dy
                if d <= 1.0:
                    lit = -(dx + dy) * 0.7 + (1 - d) * 0.6     # 왼쪽 위가 밝음
                    if (x, y) not in val or lit > val[(x, y)]:
                        val[(x, y)] = lit
    for (x, y), lit in val.items():
        if density < 1.0 and BAYER[y % 4][x % 4] / 16.0 >= density:
            continue
        col = G[9] if lit > 0.9 else (PL[3] if lit > 0.45 else (PL[2] if lit > -0.25 else PL[1]))
        c.px(x, y, col)


def puffs_fill(cx, cy, rx, ry, n, r0, seed):
    """타원 안을 채우는 덩이들(가운데일수록 큼) — 고리처럼 보이지 않게."""
    rr = Rand(seed)
    out = []
    for k in range(n):
        a = rr.f() * 2 * math.pi
        d = math.sqrt(rr.f())
        out.append((cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d, r0 * (1.15 - 0.6 * d) * (0.75 + 0.4 * rr.f())))
    return out


def puffs_ring(cx, cy, rx, ry, n, r0, seed, jitter=0.3):
    rr = Rand(seed)
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n + rr.f() * jitter
        out.append((cx + math.cos(a) * rx * (0.8 + 0.3 * rr.f()), cy + math.sin(a) * ry * (0.8 + 0.3 * rr.f()),
                    r0 * (0.7 + 0.5 * rr.f())))
    return out


# ---------------------------------------------------------------------------------------- 잔해(rubble)
def drum(c, x0, y0, ln, rad, tilt, seed):
    """누운 기둥 드럼 조각: 위가 빛 받는 원통 옆면(세로 홈 → 가로 줄) + 앞쪽 끊긴 단면(밝은 타원, 거친 테)."""
    m, d = mask(PW, PH)
    pts = [(x0, y0 - rad), (x0 + ln, y0 - rad + tilt), (x0 + ln, y0 + rad + tilt), (x0, y0 + rad)]
    d.polygon(pts, fill=255)
    W, H = PW, PH
    mp = m.load()
    for y in range(max(0, y0 - rad - 2), min(H, y0 + rad + abs(tilt) + 3)):
        for x in range(max(0, x0), min(W, x0 + ln + 1)):
            if mp[x, y] < 128:
                continue
            cy = y0 + tilt * (x - x0) / max(1, ln)
            v = (y - cy) / rad                  # -1 위 … 1 아래
            nz = math.sqrt(max(0.0, 1 - v * v))
            s = 0.5 + 0.55 * (-v * 0.6 + nz * 0.5) - 0.1
            flute = (int(round(y - cy)) + rad) % 8 in (0,)
            c.px(x, y, qcol(R_NSTONE, s - (0.05 if flute else 0), x, y))
    # 거친 끝(오른쪽) 이빨 + 단면(왼쪽, 보는 쪽)
    rr = Rand(seed)
    for y in range(y0 - rad + tilt, y0 + rad + tilt + 1):
        k = rr.i(0, 4)
        for j in range(k):
            c.px(x0 + ln - j, y, (0, 0, 0, 0))
        c.px(x0 + ln - k, y, G[2])
    for y in range(y0 - rad, y0 + rad + 1):
        v = (y - y0) / rad
        hw = int(round(5 * math.sqrt(max(0, 1 - v * v))))
        for x in range(x0 - hw, x0 + hw + 1):
            c.px(x, y, G[7] if (x - x0) + (y - y0) * 0.5 < 1 else G[6])
        c.px(x0 - hw, y, G[2])
    c.px(x0 - 1, y0 - 2, G[9]); c.px(x0 + 1, y0 + 2, G[4])


def slab(c, pts, top_h, s=0.8):
    """주두 판 조각(윗면 + 앞면 두께)."""
    front = [(x, y + top_h) for x, y in pts]
    m, d = mask(PW, PH)
    d.polygon(front, fill=255)
    shade_mask(c, m, R_NSTONE, base=0.35, gain=0.3, soft=0, rim=False)
    m2, d2 = mask(PW, PH)
    d2.polygon(pts, fill=255)
    shade_mask(c, m2, R_NSTONE, base=s, gain=0.3, soft=2, rim=True)


def fallen_banner(c):
    """떨어진 잔 휘장 — 윗단 앞 모서리에 걸쳐 납작하게 늘어진 찢긴 천 띠(두께 없음, 상자처럼 보이지 않게).
    놋 잔 문양은 접힌 틈의 금빛 한 줄만 남김."""
    pts = [(46, 384), (70, 378), (96, 383), (104, 392), (98, 396), (90, 393), (84, 401), (72, 397), (58, 402), (50, 396)]
    m, d = mask(PW, PH)
    d.polygon(pts, fill=255)
    shade_mask(c, m, BANNER, base=0.42, gain=0.5, soft=2)
    # 주름(가로로 접힘) + 찢긴 끝 술
    c.line(52, 389, 96, 388, A[16]); c.line(53, 390, 95, 389, A[18])
    c.line(60, 396, 82, 395, A[16])
    for x in (60, 66, 86, 92):
        c.vline(x, 398 if x < 80 else 395, 401 if x < 80 else 398, A[17])
    # 접힌 틈의 놋 문양 조각
    c.line(64, 384, 74, 383, R_GOLD[3]); c.px(75, 384, R_GOLD[2]); c.px(68, 385, R_GOLD[4])


def rubble_image(stage=1):
    """stage 1 = 최종 유지(29), 0 = 살짝 남은 먼지·구르는 돌(28)."""
    c = Canvas(PW, PH)
    c.paste(plinth(), 0, 0)
    # 기단 모서리 깨짐 + 금
    p = c.im.load()
    for (x0, y0, x1, y1) in ((16, 318, 26, 332), (132, 318, 143, 336), (16, 404, 22, 420), (138, 410, 143, 424)):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x - x0) + (y - y0) * 0.8 < (x1 - x0) * 0.9 or x0 > 100:
                    if (x0 > 100 and (x1 - x) + (y - y0) * 0.8 < (x1 - x0) * 0.9) or x0 <= 100:
                        p[x, y] = (0, 0, 0, 0)
    for pts in ([(30, 330), (36, 346), (34, 362), (40, 378)], [(120, 418), (116, 428), (118, 438)], [(98, 330), (104, 342), (101, 356)]):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            c.line(ax, ay, bx, by, G[1]); c.line(ax + 1, ay, bx + 1, by, G[8])
    # 뒤쪽 돌무더기(윗단 뒤)
    for k, (x, y, rx, ry) in enumerate([(46, 330, 12, 7), (70, 324, 14, 8), (98, 326, 13, 7), (120, 334, 10, 6), (86, 336, 12, 7)]):
        stone_blob(c, x, y, rx, ry, R_NSTONE, seed=300 + k)
    # 드럼 2(누운 기둥 조각) + 주두 판
    drum(c, 40, 344, 54, 13, -3, 7)
    slab(c, [(92, 330), (134, 336), (130, 350), (88, 344)], 8, s=0.85)
    drum(c, 74, 360, 50, 12, 4, 9)
    # 앞쪽 돌무더기 + 떨어진 휘장
    for k, (x, y, rx, ry) in enumerate([(40, 372, 10, 6), (112, 378, 11, 7), (128, 368, 8, 5), (30, 388, 7, 5)]):
        stone_blob(c, x, y, rx, ry, R_NSTONE, seed=320 + k)
    fallen_banner(c)
    for k, (x, y, rx, ry) in enumerate([(104, 400, 8, 5), (44, 404, 7, 4), (124, 398, 6, 4), (90, 398, 7, 5), (60, 404, 5, 3)]):
        stone_blob(c, x, y, rx, ry, R_NSTONE, seed=340 + k)
    # 기단 밖 바닥에 흩어진 조각(앞·옆)
    for k, (x, y, r) in enumerate([(10, 430, 3), (150, 432, 3), (34, 444, 2), (126, 444, 2), (8, 410, 2), (152, 404, 3), (96, 445, 2), (60, 444, 2)]):
        chunk(c, x, y, r, 360 + k)
    # 내려앉은 먼지 얼룩(성긴 점) — 윗단 위
    rr = Rand(77)
    for k in range(40):
        x, y = rr.i(28, 132), rr.i(332, 398)
        if p[x, y][3] == 255 and p[x, y][:3] in {g[:3] for g in R_NSTONE}:
            p[x, y] = PL[2] if k % 3 else PL[3]
    if stage == 0:
        cloud(c, [(22, 420, 6), (140, 418, 7), (80, 316, 8), (60, 320, 5)], density=0.45)
        chunk(c, 152, 424, 3, 390)
        chunk(c, 14, 440, 2, 391)
    return c.im


# ---------------------------------------------------------------------------------------- 무너짐(collapse)
def rotate_layer(im, ang_deg, pivot, dx, dy):
    """층 그림을 pivot 기준 회전(최근접) 후 (dx,dy) 이동."""
    r = im.rotate(ang_deg, resample=Image.NEAREST, center=pivot, translate=(dx, dy))
    return r


def crumble(layer, ycut_fn, seed, keep_above=True):
    """층에서 ycut_fn(x) 아래(또는 위) 픽셀을 지우고 그 경계에 거친 이빨을 낸다."""
    out = layer.copy()
    p = out.load()
    rr = Rand(seed)
    W, H = out.size
    for x in range(W):
        yc = ycut_fn(x) + rr.i(-3, 3)
        for y in range(H):
            if p[x, y][3] and ((y >= yc) if keep_above else (y < yc)):
                p[x, y] = (0, 0, 0, 0)
    return out


def collapse_frames():
    old = old_frames()
    base15 = old[15]
    plin, lower, upper = split_layers(base15)
    rubble = rubble_image(1)
    frames = []
    ux, uy = BREAK

    def comp(parts):
        c = Canvas(PW, PH)
        for im, off in parts:
            if off == (0, 0):
                c.im.alpha_composite(im)
            else:
                c.paste(im, off[0], off[1])
        c.p = c.im.load()
        return c

    # 0 흔들림(오른쪽 1) + 금에서 먼지가 새어 나옴 + 떨어지는 부스러기
    c = comp([(plin, (0, 0)), (lower, (0, 0)), (upper.transform(upper.size, Image.AFFINE, (1, 0, -1, 0, 1, 0)), (0, 0))])
    cloud(c, [(ux + 4, uy, 5), (ux - 18, uy + 4, 4), (ux + 26, uy - 6, 4), (ux - 6, uy - 40, 3), (ux + 10, uy + 50, 3)])
    for k in range(6):
        chunk(c, 112 + (k % 3) * 6, 280 + k * 12, 2, 400 + k)
    frames.append(c.im)
    # 1 왼쪽 1 + 윗동이 3 내려앉으며 2° 기욺 + 갈라진 자리 옆으로 먼지 분출
    up1 = rotate_layer(upper, -2, (ux, uy), -1, 3)
    c = comp([(plin, (0, 0)), (lower, (0, 0)), (up1, (0, 0))])
    cloud(c, [(ux - 34, uy + 2, 6), (ux - 44, uy - 2, 4), (ux + 32, uy + 6, 6), (ux + 44, uy + 2, 4), (ux, uy + 4, 5)])
    for k in range(8):
        chunk(c, 30 + k * 14, 290 + (k * 7) % 30, 2 + k % 2, 410 + k)
    frames.append(c.im)
    # 2 윗동 12 내려옴·4° — 아랫동 윗머리가 부서짐, 조각 떨어짐, 먼지 커짐
    up2 = rotate_layer(upper, -4, (ux, uy), 0, 12)
    low2 = crumble(lower, lambda x: cut_y(x) + 12, 21, keep_above=False)
    c = comp([(plin, (0, 0)), (low2, (0, 0)), (up2, (0, 0))])
    cloud(c, puffs_ring(ux, uy + 14, 44, 14, 9, 7, 31))
    for k in range(12):
        chunk(c, 24 + (k * 37) % 112, 286 + (k * 23) % 60, 2 + k % 3, 420 + k)
    frames.append(c.im)
    # 3 윗동 통째로 34 내려옴·6° — 아랫동 윗머리가 깨져 나가고 갈라진 자리에서 먼지 기둥, 조각 줄줄이
    up3 = rotate_layer(upper, -6, (ux, uy), -8, 34)
    low3 = crumble(lower, lambda x: cut_y(x) + 34, 34, keep_above=False)
    c = comp([(plin, (0, 0)), (low3, (0, 0)), (up3, (0, 0))])
    cloud(c, puffs_fill(ux, uy + 40, 50, 22, 16, 11, 35))
    for k in range(16):
        chunk(c, 20 + (k * 29) % 120, 270 + (k * 31) % 120, 2 + k % 3, 440 + k)
    frames.append(c.im)
    # 4 윗동 아래 절반이 부서지고(들쭉날쭉) 머리가 84 내려옴·9° — 먼지 기둥이 솟아 떨어지는 머리를 받친다
    up4 = crumble(upper, lambda x: 196 + 10 * math.sin(x * 0.5), 41)
    up4 = rotate_layer(up4, -9, (ux, 190), -14, 84)
    c = comp([(plin, (0, 0)), (up4, (0, 0))])
    cloud(c, puffs_fill(80, 330, 56, 70, 30, 17, 42))
    for k in range(12):
        chunk(c, 14 + (k * 41) % 132, 250 + (k * 17) % 120, 3 + k % 3, 460 + k)
    frames.append(c.im)
    # 5 땅에 부딪힘 — 가장 큰 먼지(기단 전체를 덮음), 위로 삐죽 나온 주두 조각 + 옆으로 튀는 조각
    c = comp([(rubble, (0, 0))])
    cloud(c, puffs_fill(80, 360, 66, 72, 40, 20, 51))
    slab(c, [(62, 290), (100, 280), (104, 292), (66, 302)], 7, s=0.8)
    cloud(c, puffs_fill(84, 312, 34, 8, 7, 9, 52))
    for k in range(10):
        side = -1 if k % 2 else 1
        chunk(c, 80 + side * (62 + (k * 7) % 12), 370 + (k * 13) % 60 - 20, 2 + k % 3, 480 + k)
    frames.append(c.im)
    # 6~9 먼지가 옆으로 퍼지며 낮아지고 얇아짐 → 잔해가 드러남
    for j, (rx, ry, r0, dens, cy, n) in enumerate([(70, 56, 18, 0.9, 372, 36), (74, 46, 15, 0.62, 382, 30),
                                                   (74, 36, 12, 0.4, 392, 24), (74, 28, 9, 0.22, 400, 18)]):
        c = comp([(rubble, (0, 0))])
        cloud(c, puffs_fill(80, cy, rx, ry, n, r0, 61 + j), density=dens)
        for k in range(4 - j):
            chunk(c, 10 + (k * 47) % 140, 420 + (k * 11) % 22, 2, 500 + 10 * j + k)
        frames.append(c.im)
    return old, frames


def rubble_frames():
    return [rubble_image(0), rubble_image(1)]
