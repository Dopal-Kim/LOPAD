"""1층 외곽 거리 v3 소품 — v2 `stage1_outer` 의 소품 8종(13~20) + 큰 소품 5종을 2배 밀도·1.5배 비율로 다시 그림 (53라운드 Q12)."""
from common import *  # noqa: F401,F403
from common import (Prop, L, SMALL, PIV, barrel, crate, puddle, lantern, brazier, sacks, tipped_barrel, debris,
                    crate_c, sack_c, barrel_c)
from pk import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_IRON, R_STONE, R_CLOTH, R_CLOTHG, contact, cyl, face, grain,
                shade_mask, mask, poly_mask, ell_mask, glass_lantern, qcol, clamp, lam)
import math


def lamp_post():
    c = Canvas(96, 224)
    cx = 34
    contact(c, cx + 4, 218, 18, 5)
    # 돌 받침 2단
    m = poly_mask(40, 22, [(0, 6), (39, 6), (39, 21), (0, 21)])
    shade_mask(c, m, R_STONE, ox=cx - 20, oy=197, base=0.5, soft=2, tilt=0.5)
    c.hline(cx - 20, cx + 19, 203, SL[6])
    m = poly_mask(26, 16, [(0, 3), (25, 3), (25, 15), (0, 15)])
    shade_mask(c, m, R_STONE, ox=cx - 13, oy=186, base=0.55, soft=2, tilt=0.5)
    # 쇠기둥(가는 원통) + 장식 고리
    cyl(c, cx, 40, 192, 4, R_IRON, ry=2, lid=False)
    for yy in (60, 150, 184):
        cyl(c, cx, yy, yy + 4, 6, R_IRON, ry=2, lid=True)
    # 꼭대기 장식
    for k in range(6):
        c.hline(cx - 3 + k // 2, cx + 3 - k // 2, 34 + k, G[6] if k < 3 else G[4])
    c.rect(cx - 1, 28, cx + 1, 33, G[5])
    # 까치발 팔(오른쪽) + 소용돌이
    c.hline(cx, cx + 40, 44, G[6]); c.hline(cx, cx + 40, 45, G[3]); c.hline(cx, cx + 40, 46, G[2])
    for k in range(22):
        x = cx + 3 + k
        y = 72 - int(k * 1.2)
        c.px(x, y, G[5]); c.px(x, y + 1, G[2])
    for k in range(12):
        a = 2 * math.pi * k / 12
        c.px(int(cx + 22 + 5 * math.cos(a)), int(52 + 5 * math.sin(a)), G[5] if a > math.pi else G[3])
    # 매달린 등불
    lx = cx + 36
    c.vline(lx, 47, 52, G[5])
    glass_lantern(c, lx, 56, 20, 38)
    return Prop("lamp_post", c, (cx, 218), footprint=(1, 1), occlude=40,
                light=L("#e8b858", 300, 1.0, lx, 76, 0.06, 4), placement="floor (벽 앞 권장)")


def crate_stack():
    c = Canvas(96, 176)
    crate_c(c, 48, 170, w=72, h=46, top_h=22, seed=11)
    crate_c(c, 44, 104, w=56, h=34, top_h=18, seed=12)
    # 위 상자 아래 그늘(아래 상자 윗면)
    for x in range(18, 74):
        for y in (103, 104, 105):
            if c.get(x, y)[3]:
                c.px(x, y, WD[2] if y > 103 else WD[1])
    sack_c(c, 30, 46, 44, 22, R_CLOTHG, 5)
    return Prop("crate_stack", c, (48, 170), footprint=(1, 1), occlude=30, placement="floor")


def stall():
    """노점: 줄무늬 천막 + 기둥 + 술병 좌판 (3칸 폭)."""
    c = Canvas(192, 192)
    contact(c, 98, 186, 86, 7)
    cy0 = 118
    # 좌판 윗면 + 앞면 널
    face(c, 18, cy0, 173, cy0 + 9, R_WOOD, 0.85, grad=0.15)
    c.hline(18, 173, cy0, WD[5])
    face(c, 18, cy0 + 10, 173, 185, R_WOOD, 0.5, grad=0.2)
    for x in range(18, 174, 13):
        c.vline(x, cy0 + 10, 185, WD[1]); c.vline(x + 1, cy0 + 10, 185, WD[4])
    grain(c, 19, cy0 + 11, 172, 184, R_WOOD, 31, vertical=True, density=0.08)
    c.hline(18, 173, cy0 + 10, WD[1]); c.hline(18, 173, 185, WD[0]); c.vline(173, cy0, 185, WD[0])
    # 술병·잔(층 램프 비발광 + 1점 반사)
    r = Rand(17)
    x = 28
    while x < 160:
        h = r.i(12, 20)
        kind = r.i(0, 3)
        if kind == 3:     # 잔
            c.rect(x, cy0 - 7, x + 5, cy0 - 1, PL[3]); c.hline(x, x + 5, cy0 - 7, PL[4]); c.vline(x + 5, cy0 - 7, cy0 - 1, PL[1])
            x += 10
            continue
        body = [A[17], A[18], A[19], A[21]] if kind else [SL[1], SL[3], SL[4], SL[6]]
        m, d = mask(10, h + 2)
        d.rounded_rectangle((0, h // 3, 8, h), radius=3, fill=255)
        d.rectangle((3, 0, 5, h // 3), fill=255)
        shade_mask(c, m, body, ox=x, oy=cy0 - h - 1, base=0.45, gain=0.9, soft=2, sharp=2)
        c.px(x + 2, cy0 - h + h // 3 + 2, body[3]); c.px(x + 2, cy0 - h + h // 3 + 3, body[3])
        c.rect(x + 3, cy0 - h - 2, x + 5, cy0 - h - 1, WD[2])
        x += r.i(11, 15)
    # 기둥
    for px_ in (20, 166):
        face(c, px_, 24, px_ + 5, cy0 - 1, R_WOOD, 0.55)
        c.vline(px_, 24, cy0 - 1, WD[4]); c.vline(px_ + 5, 24, cy0 - 1, WD[1])
    # 천막: 비스듬히 보이는 윗면(줄무늬) + 찢긴 앞자락
    for y in range(6, 36):
        t = (y - 6) / 30
        inset = int(6 * (1 - t))
        for x in range(8 + inset, 184 - inset):
            stripe = ((x + int(t * 4)) // 14) % 2 == 0
            ramp = [PL[1], PL[2], PL[3], PL[4]] if stripe else [A[16], A[17], A[18], WD[4]]
            s = 0.85 - t * 0.5 - (0.08 if (x // 3 + y) % 9 == 0 else 0)
            c.px(x, y, qcol(ramp, s, x, y))
    c.hline(14, 177, 6, PL[4])
    r = Rand(77)
    for x in range(8, 184):
        drop = 36 + r.i(4, 14) + (8 if 70 < x < 84 else 0) + (6 if 140 < x < 150 else 0)
        stripe = (x // 14) % 2 == 0
        for y in range(36, drop):
            t = (y - 36) / 24
            c.px(x, y, qcol([SL[1], PL[0], PL[1], PL[2]] if stripe else [SL[0], A[16], A[17], A[18]], 0.6 - t * 0.4, x, y))
        c.px(x, drop, SL[0] if r.f() < 0.5 else (0, 0, 0, 0))
    c.hline(8, 183, 36, PL[3])
    return Prop("stall", c, (96, 186), footprint=(3, 1), occlude=60, placement="floor (방 가장자리 권장)")


def well():
    c = Canvas(144, 176)
    cx = 72
    contact(c, cx + 4, 170, 64, 7)
    # 몸통(돌 원통) — 줄눈 있는 돌
    cyl(c, cx, 120, 160, 52, R_STONE, ry=20, lid=False)
    r = Rand(91)
    for row, y in enumerate(range(124, 172, 10)):
        for x in range(cx - 52, cx + 53):
            u = (x - cx) / 52
            yy = y + int(round(20 * math.sqrt(max(0, 1 - u * u)) * 0.9)) - 20
            if c.get(x, yy)[3]:
                c.px(x, yy, SL[1])
                c.px(x, yy + 1, SL[4] if u < 0 else SL[3])
        for k in range(8):
            u = -0.95 + (k + (row % 2) * 0.5) * 0.25
            if abs(u) > 0.97:
                continue
            x = int(cx + u * 52)
            for yy in range(y - 10, y):
                y2 = yy + int(round(20 * math.sqrt(max(0, 1 - u * u)) * 0.9)) - 20
                if c.get(x, y2)[3] and y2 > 112:
                    c.px(x, y2, SL[1])
    # 윗테(두꺼운 고리) + 어두운 구멍 + 물빛
    for y in range(96, 146):
        for x in range(cx - 58, cx + 59):
            d = ((x - cx) / 58) ** 2 + ((y - 120) / 24) ** 2
            di = ((x - cx) / 44) ** 2 + ((y - 121) / 17) ** 2
            if d <= 1 and di > 1:
                s = 0.8 - 0.35 * ((x - cx) / 58) - 0.3 * ((y - 120) / 24)
                c.px(x, y, qcol(R_STONE, s, x, y))
            elif di <= 1:
                c.px(x, y, NT_[0] if y < 128 else (SL[1] if y < 134 else SL[2]))
    for x in range(cx - 20, cx + 14):
        c.px(x, 130, SL[4])
    c.hline(cx - 8, cx + 2, 131, SL[5])
    # 나무 틀 + 지붕보 + 도르래 + 두레박
    for x in (cx - 60, cx + 54):
        face(c, x, 22, x + 5, 136, R_WOOD, 0.55)
        c.vline(x, 22, 136, WD[4]); c.vline(x + 5, 22, 136, WD[1])
    face(c, cx - 66, 14, cx + 65, 25, R_WOOD, 0.7, grad=0.3)
    c.hline(cx - 66, cx + 65, 14, WD[5]); c.hline(cx - 66, cx + 65, 25, WD[0])
    grain(c, cx - 65, 15, cx + 64, 24, R_WOOD, 41, vertical=False, density=0.1)
    cyl(c, cx, 30, 36, 6, R_IRON, ry=2)
    c.vline(cx, 40, 76, PL[2]); c.vline(cx + 1, 40, 76, PL[0])
    cyl(c, cx, 80, 92, 8, R_WOOD, ry=3, hoops=((83, 1),), staves=3)
    return Prop("well", c, (72, 170), footprint=(2, 1), occlude=64, placement="floor")


NT_ = [(11, 12, 17, 255)]


def washing_line(seed=3):
    """앞면 윗단 겹침 장식(엄폐 담·건물 벽용, 가로 반복)."""
    c = Canvas(128, 64)
    pts = []
    for x in range(128):
        y = 8 + int(round(10 * math.sin(math.pi * x / 127)))
        pts.append(y)
        c.px(x, y, G[6]); c.px(x, y + 1, G[3])
    r = Rand(seed)
    x = 6
    while x < 116:
        w = r.i(12, 20)
        h = r.i(20, 36)
        ramp = r.choice([R_CLOTH, R_CLOTHG, R_CLOTH])
        y0 = pts[min(127, x + w // 2)] + 2
        m, d = mask(w + 2, h + 2)
        d.polygon([(0, 0), (w, 0), (w - 1, h - r.i(0, 6)), (w // 2, h), (1, h - r.i(0, 6))], fill=255)
        shade_mask(c, m, ramp, ox=x, oy=y0, base=0.55, gain=0.7, soft=3, tilt=0.2)
        c.px(x + 2, y0 - 1, WD[3]); c.px(x + w - 3, y0 - 1, WD[3])
        x += w + r.i(4, 10)
    return Prop("washing_line", c, (0, 0), solid=False, footprint=(2, 0),
                placement="wallUpper — 앞면 윗단 위 겹침, 가로 이어붙임", depth="above_wall")


def small():
    return [barrel(), crate(), puddle(), lantern(), brazier(), sacks(), tipped_barrel(), debris()]


def big():
    return [lamp_post(), crate_stack(), stall(), well(), washing_line()]
