"""1층 황무지(전장) v3 소품 — 개념도 waste b · 테두리 북 b (꽂힌 무기·찢긴 깃발·투구·방패·불탄 수레·대포·말뚝·모닥불)."""
import math
from common import Prop, L, SMALL, PIV, crate_c, sack_c, debris_c, brazier_c
from pk import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_WSTONE, R_CLOTH, R_CLOTHG, R_EARTH, R_BONE,
                contact, cyl, face, grain, shade_mask, mask, poly_mask, ell_mask, flame, embers, splash, stone_blob,
                qcol, lam, clamp)

R_MUD = [SL[0], WD[0], WD[1], WD[2], WD[3], PL[0]]
R_RUST = [WD[0], A[16], A[17], WD[3], A[18], G[6]]


def mound(c, cx, by, rx, ry, seed=1, ramp=R_EARTH):
    m = ell_mask(2 * rx + 2, 2 * ry + 2, (0, 0, 2 * rx, 2 * ry))
    shade_mask(c, m, ramp, ox=cx - rx, oy=by - ry * 2 + ry // 2, base=0.45, gain=0.6, soft=4, tilt=0.35, sharp=2)
    r = Rand(seed)
    for _ in range(rx // 2):
        x, y = cx + r.i(-rx + 3, rx - 3), by - ry + r.i(-ry // 2, ry // 2)
        c.px(x, y, ramp[1]); c.px(x + 1, y, ramp[4])


def blade(c, x0, y0, x1, y1, w, ramp=R_IRON, hilt=True, guard=8):
    """기울어진 칼날(또는 창대). (x0,y0) = 땅에 박힌 끝, (x1,y1) = 손잡이 쪽."""
    n = max(abs(x1 - x0), abs(y1 - y0))
    for k in range(n + 1):
        t = k / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        for j in range(w):
            col = ramp[4] if j == 0 else (ramp[2] if j < w - 1 else ramp[1])
            if hilt and t > 0.78:
                col = WD[2] if j else WD[3]
            c.px(int(round(x)) + j, int(round(y)), col)
    if hilt:
        gx = x0 + (x1 - x0) * 0.78
        gy = y0 + (y1 - y0) * 0.78
        c.hline(int(gx - guard // 2), int(gx + guard // 2 + w), int(gy), ramp[3])
        c.hline(int(gx - guard // 2), int(gx + guard // 2 + w), int(gy) + 1, ramp[1])
        c.rect(int(x1) - 1, int(y1) - 2, int(x1) + w, int(y1), ramp[3])


def spear(c, x0, y0, x1, y1):
    n = max(abs(x1 - x0), abs(y1 - y0))
    for k in range(n + 1):
        t = k / n
        x, y = int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t))
        c.px(x - 1, y, WD[4]); c.px(x, y, WD[3]); c.px(x + 1, y, WD[1])
    # 창날(위 끝)
    dx, dy = (x1 - x0) / n, (y1 - y0) / n
    for k in range(14):
        x, y = x1 + dx * k, y1 + dy * k
        half = 3 * (1 - k / 14) + 0.5
        for j in range(-int(half), int(half) + 1):
            c.px(int(round(x - dy * j)), int(round(y + dx * j)), G[7] if j < 0 else G[4])


def weapons_stuck():
    """꽂힌 창·검 묶음 + 흙 둔덕."""
    c = Canvas(96, 192)
    contact(c, 50, 184, 34, 6)
    mound(c, 48, 186, 30, 9, 3)
    spear(c, 30, 182, 16, 30)
    blade(c, 56, 180, 64, 96, 6, guard=12)
    blade(c, 42, 182, 34, 120, 5, guard=10)
    spear(c, 66, 182, 84, 52)
    # 찢긴 천 조각(창에 걸림)
    m = poly_mask(26, 30, [(0, 0), (22, 4), (18, 16), (25, 28), (8, 20), (3, 29)])
    shade_mask(c, m, R_CLOTHG, ox=18, oy=40, base=0.4, gain=0.6, soft=2)
    return Prop("weapons_stuck", c, (48, 184), footprint=(1, 1), solid=False, occlude=40, placement="floor")


def banner_pole():
    c = Canvas(96, 208)
    contact(c, 44, 202, 22, 5)
    mound(c, 42, 204, 18, 6, 5)
    # 장대(약간 기울어짐)
    for y in range(18, 202):
        x = 40 + int((202 - y) * 0.06)
        c.px(x, y, WD[4]); c.px(x + 1, y, WD[3]); c.px(x + 2, y, WD[1])
    c.hline(40, 74, 24, WD[3]); c.hline(40, 74, 25, WD[1])
    # 찢긴 깃발(잔 문양, 가로대에 매달림)
    pts = [(0, 0), (34, 0), (33, 50), (28, 72), (24, 58), (18, 86), (12, 60), (6, 78), (1, 52)]
    m = poly_mask(36, 88, pts)
    shade_mask(c, m, [SL[0], SL[1], A[16], A[17], WD[3], PL[0]], ox=43, oy=26, base=0.4, gain=0.6, soft=3, sharp=2)
    # 잔 문양(바랜 층 램프)
    for y in range(36, 50):
        t = (y - 36) / 14
        half = int(7 * (1 - t) ** 0.6) if y < 46 else 1
        c.hline(60 - half, 60 + half, y, A[18])
    c.hline(56, 64, 51, A[18]); c.vline(60, 46, 51, A[18])
    return Prop("banner_pole", c, (42, 202), footprint=(1, 1), occlude=50, placement="floor")


def helmet_shield():
    c = Canvas(SMALL, SMALL)
    contact(c, 64, 112, 40, 6)
    # 둥근 방패(비스듬히 묻힘)
    m = ell_mask(56, 40, (0, 0, 55, 39))
    shade_mask(c, m, R_WOODG, ox=50, oy=76, base=0.45, gain=0.6, soft=6, tilt=0.3)
    for k in range(40):
        a = 2 * math.pi * k / 40
        c.px(int(77 + 27 * math.cos(a)), int(96 + 19 * math.sin(a)), G[5] if math.sin(a) < 0 else G[3])
    m = ell_mask(12, 10, (0, 0, 11, 9))
    shade_mask(c, m, R_IRON, ox=72, oy=91, base=0.6, soft=2)
    # 투구(반구 + 챙)
    m, d = mask(40, 30)
    d.pieslice((1, 2, 38, 52), 180, 360, fill=255)
    shade_mask(c, m, R_IRON, ox=24, oy=78, base=0.5, gain=0.8, soft=5)
    c.hline(22, 64, 104, G[5]); c.hline(22, 64, 105, G[2])
    c.hline(30, 50, 94, SL[0]); c.hline(30, 50, 95, SL[0]); c.vline(40, 95, 102, SL[0])   # 눈구멍·코가리개
    mound(c, 44, 112, 26, 4, 8)
    return Prop("helmet_shield", c, PIV, solid=False, occlude=None, maxPerRoom=2, weight=0.8, depth="floor",
                note="혼불 fx 자리(Q25: 둑 위 2~3개는 fx) — 투구 위 0.5칸")


def bones():
    c = Canvas(SMALL, SMALL)
    debris_c(c, 64, 104, 70, 18, 21, ramp=R_WSTONE, pottery=False)
    # 해골
    m = ell_mask(22, 20, (0, 0, 21, 19))
    shade_mask(c, m, R_BONE, ox=40, oy=86, base=0.6, gain=0.7, soft=3)
    c.rect(44, 94, 47, 97, SL[0]); c.rect(52, 94, 55, 97, SL[0]); c.rect(46, 102, 54, 105, R_BONE[2])
    for x in range(46, 55, 2):
        c.px(x, 103, SL[1])
    # 갈비·뼈
    for k in range(4):
        y = 98 + k * 4
        for x in range(66, 92):
            yy = y + int(3 * math.sin((x - 66) / 26 * math.pi))
            c.px(x, yy, R_BONE[3]); c.px(x, yy + 1, R_BONE[1])
    blade(c, 22, 112, 60, 116, 2, hilt=False)
    return Prop("bones", c, PIV, solid=False, occlude=None, maxPerRoom=2, weight=0.7, depth="floor")


def campfire():
    c = Canvas(SMALL, SMALL)
    contact(c, 64, 116, 34, 7)
    # 돌 고리(뒤쪽 먼저)
    for k in range(10):
        a = math.pi + math.pi * k / 9
        stone_blob(c, int(64 + 30 * math.cos(a)), int(106 + 11 * math.sin(a)), 7, 5, R_WSTONE, 40 + k)
    # 장작(교차)
    for (x0, y0, x1, y1) in ((40, 110, 86, 98), (44, 98, 88, 110), (52, 112, 76, 94)):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(n + 1):
            x, y = int(x0 + (x1 - x0) * k / n), int(y0 + (y1 - y0) * k / n)
            for j in range(4):
                c.px(x, y + j, [WD[3], WD[2], WD[1], SL[0]][j])
    for x in range(48, 82):
        if (x * 7) % 5 < 2:
            c.px(x, 106, A[21]); c.px(x, 105, A[22])
    flame(c, 64, 106, 38, 54, seed=9, tongues=5)
    embers(c, 64, 46, 7, 12, 4)
    for k in range(9):
        a = math.pi * k / 8
        stone_blob(c, int(64 + 32 * math.cos(a)), int(108 + 10 * math.sin(a)), 7, 5, R_WSTONE, 60 + k)
    return Prop("campfire", c, PIV, occlude=30, maxPerRoom=1, weight=0.6,
                light=L("#eebb6d", 400, 1.25, 64, 80, 0.18, 6))


def sandbags():
    c = Canvas(SMALL, SMALL)
    contact(c, 64, 118, 52, 6)
    r = Rand(3)
    rows = [(119, 3, 34), (106, 3, 34), (93, 2, 34)]
    for (by, n, w) in rows:
        x0 = 64 - n * w // 2 + (0 if n % 2 else 2)
        for k in range(n):
            x = x0 + k * (w - 3) + r.i(-2, 2)
            m, d = mask(w + 4, 18)
            d.polygon([(2, 5), (6, 2), (w - 3, 2), (w + 1, 6), (w + 1, 13), (w - 3, 16), (5, 16), (1, 12)], fill=255)
            shade_mask(c, m, [SL[1], WD[1], WD[2], PL[0], PL[1], PL[2]], ox=x, oy=by - 18, base=0.45, gain=0.8, soft=3, tilt=0.3, sharp=2.5)
            c.vline(x + 5, by - 14, by - 4, PL[0]); c.vline(x + w - 4, by - 14, by - 4, PL[0])
    return Prop("sandbags", c, PIV, occlude=24, maxPerRoom=2, weight=0.8)


def crate_w():
    c = Canvas(SMALL, SMALL)
    crate_c(c, 64, 120, ramp=R_WOODG, seed=5)
    return Prop("crate", c, PIV, occlude=20, maxPerRoom=2, weight=0.6)


def sacks_w():
    c = Canvas(SMALL, SMALL)
    contact(c, 66, 118, 34, 6)
    sack_c(c, 30, 80, 38, 38, R_CLOTH, 1)
    sack_c(c, 62, 86, 34, 32, R_CLOTHG, 2)
    return Prop("sacks", c, PIV, occlude=20, maxPerRoom=1, weight=0.5)


def mud():
    c = Canvas(SMALL, SMALL)
    splash(c, 62, 100, 44, 12, ramp=[SL[0], WD[1], WD[2], SL[3], SL[5], SL[6]], seed=31, blobs=8)
    return Prop("mud_puddle", c, PIV, solid=False, occlude=None, maxPerRoom=3, weight=1.0, depth="floor")


def broken_cart():
    """부서진 보급 수레(불탐) — 2칸."""
    c = Canvas(176, 160)
    contact(c, 90, 150, 74, 9)
    # 짐칸(기울어짐: 오른쪽 바퀴 빠짐)
    pts = [(14, 70), (150, 86), (150, 120), (14, 104)]
    m = poly_mask(176, 160, pts)
    shade_mask(c, m, R_WOODG, base=0.42, gain=0.5, soft=2, sharp=2)
    for k in range(5):
        x0 = 14 + k * 34
        for y in range(70, 124):
            yy = y + int((x0 - 14) * 16 / 136)
            if c.get(x0, yy)[3]:
                c.px(x0, yy, WD[1])
    pts2 = [(14, 56), (150, 72), (150, 86), (14, 70)]
    m = poly_mask(176, 160, pts2)
    shade_mask(c, m, R_WOODG, base=0.7, gain=0.4, soft=1, sharp=2)
    grain(c, 16, 58, 148, 118, R_WOODG, 7, vertical=False, density=0.06)
    # 그을음
    r = Rand(5)
    for _ in range(260):
        x, y = r.i(70, 150), r.i(60, 122)
        if c.get(x, y)[3]:
            c.px(x, y, SL[0] if r.f() < 0.5 else SL[1])
    # 왼쪽 바퀴(서 있음)
    for k in range(64):
        a = 2 * math.pi * k / 64
        for rr in (22, 21, 20):
            x, y = int(40 + rr * math.cos(a) * 0.55), int(122 + rr * math.sin(a))
            c.px(x, y, WD[3] if math.cos(a) < 0 else WD[1])
    for k in range(6):
        a = 2 * math.pi * k / 6
        c.line(40, 122, int(40 + 19 * math.cos(a) * 0.55), int(122 + 19 * math.sin(a)), WD[2])
    c.rect(38, 120, 42, 124, G[4])
    # 오른쪽 빠진 바퀴(바닥에 누움)
    for k in range(64):
        a = 2 * math.pi * k / 64
        for rr in (24, 23, 22):
            x, y = int(140 + rr * math.cos(a)), int(146 + rr * math.sin(a) * 0.35)
            c.px(x, y, WD[3] if math.sin(a) < 0 else WD[1])
    # 끌채
    c.line(14, 98, 0, 120, WD[3]); c.line(14, 99, 0, 121, WD[1])
    # 불(짐칸 오른쪽에서)
    flame(c, 120, 82, 40, 58, seed=17, tongues=5)
    flame(c, 94, 80, 22, 30, seed=19, tongues=3)
    embers(c, 112, 20, 8, 14, 21)
    return Prop("broken_cart", c, (88, 150), footprint=(2, 1), occlude=40,
                light=L("#eebb6d", 360, 1.1, 116, 60, 0.18, 6), placement="floor (가장자리 권장)")


def cannon():
    c = Canvas(160, 112)
    contact(c, 80, 104, 66, 7)
    # 포가(나무) + 바퀴
    m = poly_mask(160, 112, [(30, 70), (118, 62), (124, 86), (34, 94)])
    shade_mask(c, m, R_WOODG, base=0.5, gain=0.5, soft=2)
    for (wx, wy) in ((52, 88), (106, 84)):
        for k in range(56):
            a = 2 * math.pi * k / 56
            for rr in (18, 17, 16):
                c.px(int(wx + rr * math.cos(a) * 0.5), int(wy + rr * math.sin(a)), WD[3] if math.cos(a) < 0 else WD[1])
        c.rect(wx - 2, wy - 2, wx + 2, wy + 2, G[4])
    # 포신(가로 원통, 앞이 오른쪽 위)
    for k in range(110):
        t = k / 110
        x = 22 + k
        y = 66 - int(t * 22)
        rr = 12 - int(t * 4)
        for j in range(-rr, rr + 1):
            v = j / rr
            s = 0.45 + 0.6 * (lam(0, v, math.sqrt(max(0, 1 - v * v))) - 0.2)
            c.px(x, y + j, qcol(R_IRON, s, x, y + j))
    for (x, y, rr) in ((26, 66, 13), (70, 56, 11), (128, 44, 9)):
        for j in range(-rr, rr + 1):
            c.px(x, y + j, G[6] if j < 0 else G[3]); c.px(x + 1, y + j, G[2])
    for j in range(-6, 7):                              # 포구
        half = int(3 * math.sqrt(max(0, 1 - (j / 7) ** 2)))
        c.hline(131 - half, 131 + half, 44 + j, SL[0] if abs(j) < 5 else G[4])
    # 포탄 몇 개
    for (x, y) in ((126, 98), (140, 100), (133, 92)):
        m = ell_mask(12, 12, (0, 0, 11, 11))
        shade_mask(c, m, R_IRON, ox=x - 6, oy=y - 6, base=0.5, gain=0.9, soft=2)
    return Prop("cannon", c, (78, 104), footprint=(2, 1), occlude=30, placement="floor")


def stakes():
    """뾰족 말뚝 울타리 묶음(기울어진 통나무 4~5개) — 캐릭터를 가림."""
    c = Canvas(160, 176)
    contact(c, 80, 168, 70, 7)
    mound(c, 80, 172, 70, 7, 9)
    r = Rand(13)
    for k in range(6):
        bx = 18 + k * 25 + r.i(-3, 3)
        lean = r.i(-14, 22)
        h = r.i(110, 150)
        w = r.i(9, 12)
        for y in range(h):
            t = y / h
            x = bx + int(lean * t)
            half = w / 2 if t < 0.82 else w / 2 * (1 - (t - 0.82) / 0.18)
            for j in range(-int(half), int(half) + 1):
                u = j / max(1, half)
                s = 0.55 - 0.4 * u + (0.25 if t > 0.82 else 0)
                c.px(x + j, 168 - y, qcol(R_WOODG if k % 2 else R_WOOD, s, x + j, 168 - y))
        # 껍질 마디
        for y in range(8, int(h * 0.8), r.i(14, 20)):
            x = bx + int(lean * y / h)
            c.hline(x - w // 2, x + w // 2, 168 - y, WD[1])
    # 가로 묶음 줄
    for y in (120, 140):
        c.hline(14, 150, y, PL[1]); c.hline(14, 150, y + 1, WD[1])
    return Prop("stakes", c, (80, 168), footprint=(2, 1), occlude=60, placement="floor (흙둑 앞·엄폐)")


def debris_w():
    c = Canvas(SMALL, SMALL)
    debris_c(c, 62, 100, 64, 22, 47, ramp=R_WSTONE, pottery=False)
    return Prop("debris", c, PIV, solid=False, occlude=None, maxPerRoom=3, weight=1.0, depth="floor")


def small():
    return [crate_w(), sacks_w(), sandbags(), helmet_shield(), bones(), campfire(), debris_w(), mud()]


def big():
    return [weapons_stuck(), banner_pole(), broken_cart(), cannon(), stakes()]
