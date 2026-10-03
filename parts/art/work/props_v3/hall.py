"""1층 연회장(보스) v3 소품 — 개념도 hall b · 테두리 북(단상·왕좌·화로) (긴 연회 탁자·촛대·돌기둥·의자·잔·병·엎질러진 술)."""
import math
from common import (Prop, L, SMALL, PIV, barrel, tipped_barrel, barrel_c, sack_c)
from pk import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_NSTONE, R_STONE, R_CLOTH, R_CLOTHG, R_LIQ,
                contact, cyl, face, grain, shade_mask, mask, poly_mask, ell_mask, flame, splash, qcol, lam)

R_LINEN = [SL[1], G[4], G[5], G[6], G[7], G[9]]          # 바랜 식탁보(촛불에 너무 뜨지 않게 눌러 둠)
R_GOLD = [WD[1], A[16], A[17], A[19], A[21], A[22]]     # 잔·촛대 놋쇠(층 램프, 어둡게 눌러 촛불보다 낮게)


def candle(c, x, y, h=10, w=3):
    """초(밑 = y) + 불꽃(자체 발광)."""
    c.rect(x, y - h, x + w - 1, y, PL[4]); c.vline(x + w - 1, y - h, y, PL[2]); c.px(x, y - h, G[13])
    cx = x + w // 2
    c.px(cx, y - h - 1, SL[0])
    for (dx, dy, col) in ((0, -2, A[25]), (0, -3, A[26]), (0, -4, A[27]), (0, -5, A[26]), (0, -6, A[24]),
                          (-1, -3, A[23]), (1, -3, A[23]), (-1, -4, A[24]), (1, -4, A[24]), (0, -7, A[23])):
        c.px(cx + dx, y - h + dy, col)


def candelabra_c(c, cx, by, h=60, arms=2, big=False):
    """놋쇠 촛대(탁자 위·바닥 공용). by = 받침 밑. big = 바닥 촛대(굵은 대·큰 초)."""
    sw = 2 if big else 1
    c.rect(cx - 7 - sw, by - 4, cx + 7 + sw, by, R_GOLD[2]); c.hline(cx - 7 - sw, cx + 7 + sw, by - 4, R_GOLD[4]); c.hline(cx - 7, cx + 7, by, R_GOLD[0])
    for y in range(by - h, by - 4):
        for k in range(-sw, sw + 1):
            c.px(cx + k, y, R_GOLD[4] if k < 0 else (R_GOLD[2] if k == 0 else R_GOLD[1]))
    for k in (by - h // 2, by - h + 8, by - h // 4):
        c.rect(cx - sw - 2, k, cx + sw + 2, k + 2, R_GOLD[3]); c.hline(cx - sw - 2, cx + sw + 2, k, R_GOLD[5])
    top = by - h
    ch, cw = (16, 4) if big else (9, 3)
    for k in range(1, arms + 1):
        w = (12 if big else 7) * k
        for x in range(-w, w + 1):
            y = top + 8 - int(8 * (1 - (x / w) ** 2))
            c.px(cx + x, y, R_GOLD[3]); c.px(cx + x, y + 1, R_GOLD[1])
            if big:
                c.px(cx + x, y + 2, R_GOLD[0])
        for sx in (-w, w):
            c.rect(cx + sx - 3, top + 3, cx + sx + 3, top + 6, R_GOLD[3]); c.hline(cx + sx - 3, cx + sx + 3, top + 3, R_GOLD[5])
            candle(c, cx + sx - cw // 2, top + 2, ch - 2 * k, cw)
    c.rect(cx - 3, top - 2, cx + 3, top + 1, R_GOLD[3])
    candle(c, cx - cw // 2, top - 3, ch + 2, cw)


def candelabra_stand():
    c = Canvas(96, 208)
    contact(c, 48, 202, 22, 5)
    for (dx, col) in ((-14, R_GOLD[3]), (14, R_GOLD[1]), (-6, R_GOLD[2])):
        for k in range(3):
            c.line(48 + dx, 202 - k, 48, 186 - k, col)
    candelabra_c(c, 48, 190, h=130, arms=2, big=True)
    return Prop("candelabra_stand", c, (48, 202), footprint=(1, 1), occlude=60, placement="floor (탁자 끝·단상 양옆)",
                light=L("#f4de9b", 280, 0.9, 48, 50, 0.1, 6))


def goblet(c, x, y, tipped=False):
    if tipped:
        c.rect(x, y - 3, x + 7, y, R_GOLD[3]); c.hline(x, x + 7, y - 3, R_GOLD[5]); c.px(x + 8, y - 2, R_GOLD[1])
        c.rect(x - 3, y - 2, x - 1, y - 1, R_GOLD[2])
        splash(c, x + 13, y + 2, 7, 2, seed=x, blobs=2, glint=False)
        return
    c.rect(x, y - 9, x + 6, y - 5, R_GOLD[3]); c.hline(x, x + 6, y - 9, R_GOLD[5]); c.vline(x + 6, y - 9, y - 5, R_GOLD[1])
    c.hline(x + 1, x + 5, y - 8, A[18])
    c.vline(x + 3, y - 4, y - 1, R_GOLD[2]); c.hline(x + 1, x + 5, y, R_GOLD[2])


def bottle(c, x, y, tipped=False, ramp=None):
    ramp = ramp or [SL[0], SL[2], SL[3], SL[5], SL[6]]
    if tipped:
        m = poly_mask(22, 10, [(0, 2), (14, 1), (16, 3), (21, 3), (21, 6), (16, 6), (14, 9), (0, 8)])
        shade_mask(c, m, ramp, ox=x, oy=y - 9, base=0.5, gain=0.8, soft=2)
        return
    m, d = mask(10, 22)
    d.rounded_rectangle((0, 8, 9, 21), radius=3, fill=255); d.rectangle((3, 0, 6, 8), fill=255)
    shade_mask(c, m, ramp, ox=x, oy=y - 21, base=0.5, gain=0.8, soft=2)
    c.vline(x + 2, y - 11, y - 4, ramp[4])


def banquet_table():
    """긴 연회 탁자(세로 2×4칸, 막힘 장애물). 식탁보 + 촛대 2 + 잔·병·접시 + 의자."""
    c = Canvas(160, 304)
    contact(c, 80, 296, 70, 8)
    x0, x1, y0, y1 = 28, 131, 30, 262          # 윗면
    face(c, x0, y0, x1, y1, R_LINEN, 0.38, grad=0.08)
    r = Rand(31)
    # 천 주름(세로 결) + 얼룩
    for x in range(x0 + 6, x1 - 4, 9):
        for y in range(y0 + 2, y1):
            if r.f() < 0.85:
                c.px(x, y, R_LINEN[2])
    for _ in range(5):
        splash(c, r.i(x0 + 16, x1 - 16), r.i(y0 + 20, y1 - 20), r.i(6, 12), r.i(3, 6), ramp=R_LIQ, seed=r.i(1, 99),
               blobs=3, glint=False)
    c.hline(x0, x1, y0, G[12]); c.vline(x0, y0, y1, G[10]); c.vline(x1, y0, y1, G[4])
    # 드리운 식탁보 앞자락(남쪽 끝) + 옆 자락
    for x in range(x0 - 2, x1 + 3):
        drop = 22 + (3 if (x // 7) % 2 else 0)
        for y in range(y1 + 1, y1 + drop):
            c.px(x, y, qcol(R_LINEN, 0.45 - (y - y1) / drop * 0.3 - (0.12 if (x // 7) % 2 else 0), x, y))
        c.px(x, y1 + drop, SL[0])
    for y in range(y0, y1 + 1):
        c.px(x0 - 1, y, G[7]); c.px(x0 - 2, y, G[5]); c.px(x1 + 1, y, G[3]); c.px(x1 + 2, y, G[2])
    # 다리(앞자락 아래)
    for x in (x0 + 4, x1 - 8):
        face(c, x, y1 + 22, x + 5, 294, R_WOOD, 0.45)
    # 위 소품: 촛대 2, 접시·잔·병
    for yy in (100, 214):
        candelabra_c(c, 80, yy, h=34, arms=2)
    rr = Rand(7)
    for k in range(8):
        px_ = (x0 + 18) if k % 2 == 0 else (x1 - 26)
        py = y0 + 18 + k * 28
        m = ell_mask(18, 10, (0, 0, 17, 9))
        shade_mask(c, m, [SL[1], G[6], G[8], G[10], G[12]], ox=px_ - 2, oy=py, base=0.6, gain=0.5, soft=2)
        if rr.f() < 0.6:
            goblet(c, px_ + (16 if k % 2 == 0 else -12), py + 10, tipped=rr.f() < 0.35)
    for (bx, by, t) in ((60, 70, False), (96, 150, True), (64, 186, False), (100, 244, False)):
        bottle(c, bx, by, tipped=t, ramp=[A[16], A[17], A[18], A[20], A[22]] if bx < 80 else None)
    # 의자(양옆, 하나는 넘어짐)
    for (cx, cy, fallen) in ((12, 80, False), (12, 170, True), (148, 120, False), (148, 220, False)):
        if fallen:
            face(c, cx - 10, cy, cx + 8, cy + 8, R_WOOD, 0.6); c.hline(cx - 10, cx + 8, cy, WD[5])
            c.line(cx - 8, cy + 8, cx - 12, cy + 18, WD[2]); c.line(cx + 6, cy + 8, cx + 10, cy + 18, WD[2])
            continue
        face(c, cx - 9, cy, cx + 9, cy + 18, R_WOOD, 0.7, grad=0.2)
        face(c, cx - 9, cy + 19, cx + 9, cy + 24, R_WOOD, 0.4)
        c.vline(cx - 8, cy + 25, cy + 34, WD[2]); c.vline(cx + 8, cy + 25, cy + 34, WD[1])
    return Prop("banquet_table", c, (80, 296), footprint=(2, 4), occlude=40, placement="floor (측면 세로, 막힘 장애물 — 52라운드)",
                light=L("#f4de9b", 240, 0.7, 80, 140, 0.1, 6),
                lights=[L("#f4de9b", 220, 0.65, 80, 56, 0.1, 6), L("#f4de9b", 220, 0.65, 80, 170, 0.1, 6)])


def pillar():
    """돌기둥(내부 장애물 1칸) — 기단 + 몸통 + 주두, 잔 문양 휘장."""
    c = Canvas(96, 304)
    contact(c, 48, 296, 40, 7)
    face(c, 10, 266, 85, 296, R_NSTONE, 0.5, grad=0.25); c.hline(10, 85, 266, G[8]); c.hline(10, 85, 296, G[1])
    face(c, 14, 256, 81, 265, R_NSTONE, 0.75); c.hline(14, 81, 256, G[9])
    # 몸통(세로 홈 있는 반원기둥)
    for x in range(20, 76):
        u = (x - 48) / 28
        nz = math.sqrt(max(0, 1 - u * u))
        flute = 0.08 if (x - 20) % 7 in (0, 1) else 0
        for y in range(40, 256):
            s = 0.45 + 0.6 * (lam(u, 0, nz) - 0.15) - flute
            c.px(x, y, qcol(R_NSTONE, s, x, y))
    # 주두
    face(c, 12, 22, 83, 40, R_NSTONE, 0.65, grad=0.3); c.hline(12, 83, 22, G[9]); c.hline(12, 83, 40, G[1])
    face(c, 8, 8, 87, 21, R_NSTONE, 0.85, grad=0.2); c.hline(8, 87, 8, G[10])
    # 휘장(잔 문양)
    pts = [(0, 0), (40, 0), (40, 88), (20, 104), (0, 88)]
    m = poly_mask(42, 106, pts)
    shade_mask(c, m, [SL[0], A[16], A[17], A[18], WD[4]], ox=28, oy=52, base=0.45, gain=0.5, soft=3)
    for y in range(66, 84):
        t = (y - 66) / 18
        half = int(9 * (1 - t) ** 0.6)
        c.hline(48 - half, 48 + half, y, R_GOLD[3] if y > 67 else R_GOLD[4])
    c.vline(48, 84, 92, R_GOLD[3]); c.hline(42, 54, 93, R_GOLD[3])
    c.hline(26, 70, 52, R_GOLD[2])
    return Prop("pillar", c, (48, 296), footprint=(1, 1), occlude=60, placement="floor (내부 장애물, 대칭 배치)")


def bench():
    c = Canvas(160, 96)
    contact(c, 80, 88, 70, 6)
    # 넘어져 옆으로 누운 긴 의자
    face(c, 10, 40, 150, 52, R_WOOD, 0.8, grad=0.2); c.hline(10, 150, 40, WD[5])
    face(c, 10, 53, 150, 64, R_WOOD, 0.45)
    for x in (24, 132):
        for k in range(26):
            c.px(x + k // 3, 64 + k, WD[3]); c.px(x + 1 + k // 3, 64 + k, WD[1])
    grain(c, 11, 41, 149, 63, R_WOOD, 81, vertical=False, density=0.08)
    return Prop("bench", c, (80, 88), footprint=(2, 1), occlude=20, placement="floor")


def wine_puddle():
    c = Canvas(SMALL, SMALL)
    splash(c, 62, 100, 46, 13, ramp=[WD[1], A[16], A[17], A[18], A[20], A[24]], seed=41, blobs=9)
    return Prop("wine_puddle", c, PIV, solid=False, occlude=None, maxPerRoom=3, weight=1.0, depth="floor",
                note="엎질러진 술 — 글린트(A24)만 약한 자체 발광",
                light=L("#e2a33c", 90, 0.25, 62, 98, 0.05, 2))


def goblet_big(c, x, y, tipped=False):
    """바닥에 구른 큰 잔(높이 약 20 도트). (x, y) = 밑받침 왼쪽 아래."""
    if tipped:
        m = poly_mask(26, 16, [(0, 2), (14, 0), (14, 15), (0, 13)])
        shade_mask(c, m, R_GOLD, ox=x + 8, oy=y - 15, base=0.55, gain=0.8, soft=2)
        c.vline(x + 22, y - 13, y - 2, A[17])
        c.rect(x, y - 9, x + 8, y - 7, R_GOLD[3]); c.rect(x - 3, y - 13, x - 1, y - 3, R_GOLD[2])
        splash(c, x + 34, y - 2, 12, 3, ramp=[WD[1], A[16], A[17], A[18], A[20], A[24]], seed=x, blobs=3, glint=False)
        return
    m, d = mask(18, 14)
    d.pieslice((0, -12, 17, 13), 0, 180, fill=255)
    shade_mask(c, m, R_GOLD, ox=x, oy=y - 22, base=0.55, gain=0.8, soft=2)
    c.hline(x + 1, x + 16, y - 22, R_GOLD[5]); c.hline(x + 3, x + 14, y - 21, A[17])
    c.vline(x + 8, y - 9, y - 2, R_GOLD[3]); c.vline(x + 9, y - 9, y - 2, R_GOLD[1])
    c.rect(x + 3, y - 1, x + 14, y, R_GOLD[2]); c.hline(x + 3, x + 14, y - 1, R_GOLD[4])


def goblets():
    c = Canvas(SMALL, SMALL)
    goblet_big(c, 24, 108, True)
    goblet_big(c, 70, 100, False)
    goblet_big(c, 74, 122, True)
    return Prop("goblets", c, PIV, solid=False, occlude=None, maxPerRoom=2, weight=0.8, depth="floor")


def bottles():
    c = Canvas(SMALL, SMALL)
    bottle(c, 30, 112, tipped=True)
    bottle(c, 58, 104, ramp=[A[16], A[17], A[18], A[20], A[22]])
    bottle(c, 72, 106)
    bottle(c, 80, 118, tipped=True, ramp=[A[16], A[17], A[18], A[20], A[22]])
    splash(c, 104, 118, 10, 3, seed=2, blobs=2, glint=False)
    return Prop("bottles", c, PIV, solid=False, occlude=None, maxPerRoom=2, weight=0.8, depth="floor")


def chair():
    c = Canvas(SMALL, SMALL)
    contact(c, 64, 118, 22, 5)
    # 등받이 높은 의자(정면)
    face(c, 46, 50, 82, 92, R_WOOD, 0.55, grad=0.2)
    for x in range(52, 80, 8):
        c.vline(x, 56, 90, WD[1])
    c.hline(46, 82, 50, WD[5])
    face(c, 42, 93, 86, 100, R_WOOD, 0.8); c.hline(42, 86, 93, WD[5])
    face(c, 42, 101, 86, 105, R_WOOD, 0.4)
    for x in (44, 82):
        face(c, x, 106, x + 3, 118, R_WOOD, 0.4)
    return Prop("chair", c, PIV, occlude=20, maxPerRoom=2, weight=0.5)


def small():
    return [barrel(), tipped_barrel(), wine_puddle(), goblets(), bottles(), chair()]


def big():
    return [banquet_table(), pillar(), candelabra_stand(), bench()]
