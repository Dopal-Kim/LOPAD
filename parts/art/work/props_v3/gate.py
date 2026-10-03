"""1층 성문 v3 소품 — 개념도 gate a · 테두리 북(성벽·성문) (통행세 오두막·술통 수레·X 바리케이드·물통·횃불)."""
import math
from common import (Prop, L, SMALL, PIV, barrel, crate, sacks, lantern, tipped_barrel, debris_c, crate_c, barrel_c,
                    sack_c)
from outer import crate_stack
from pk import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_NSTONE, R_STONE, R_CLOTH, R_CLOTHG,
                contact, cyl, face, grain, shade_mask, mask, poly_mask, ell_mask, flame, embers, splash, glass_lantern,
                stone_blob, qcol, lam)


def torch_stand():
    """쇠 횃불대(바닥에 세움)."""
    c = Canvas(SMALL, 192)
    contact(c, 66, 186, 18, 5)
    for (dx, col) in ((-12, G[5]), (12, G[3]), (0, G[4])):
        c.line(64 + dx, 186, 64, 160, col)
    cyl(c, 64, 70, 164, 3, R_IRON, ry=1, lid=False)
    # 바구니
    for y in range(58, 76):
        t = (y - 58) / 18
        half = int(12 - t * 6)
        for x in range(64 - half, 64 + half + 1):
            c.px(x, y, G[5] if (x - y) % 5 == 0 else (G[3] if (x + y) % 5 == 0 else (0, 0, 0, 0)))
        c.px(64 - half, y, G[5]); c.px(64 + half, y, G[2])
    c.hline(51, 77, 58, G[6]); c.hline(51, 77, 59, G[3])
    for x in range(54, 75):
        c.px(x, 57, A[18] if x % 3 else A[21])
    flame(c, 64, 58, 18, 44, seed=23, tongues=3)
    embers(c, 64, 12, 5, 8, 2)
    return Prop("torch_stand", c, (64, 186), footprint=(1, 1), occlude=40, placement="floor (문·길 양옆)",
                light=L("#eebb6d", 320, 1.05, 64, 40, 0.16, 6))


def puddle_g():
    c = Canvas(SMALL, SMALL)
    splash(c, 60, 100, 42, 12, ramp=[SL[0], WD[1], WD[2], A[18], A[20], A[22]], seed=13, blobs=8)
    return Prop("puddle", c, PIV, solid=False, occlude=None, maxPerRoom=3, weight=1.0, depth="floor",
                note="문빛 반사(층 램프, 비발광)")


def debris_g():
    c = Canvas(SMALL, SMALL)
    debris_c(c, 62, 100, 60, 20, 77, ramp=R_NSTONE, pottery=False)
    return Prop("debris", c, PIV, solid=False, occlude=None, maxPerRoom=3, weight=1.0, depth="floor")


def toll_booth():
    """통행세 오두막: 널지붕 + 탁자 + 등불 (2칸)."""
    c = Canvas(160, 208)
    contact(c, 80, 200, 72, 8)
    # 뒷벽(널판)
    face(c, 22, 70, 138, 168, R_WOODG, 0.35, grad=0.1)
    for x in range(22, 139, 10):
        c.vline(x, 70, 168, WD[1]); c.vline(x + 1, 70, 168, PL[0])
    # 탁자(앞) — 윗면 + 앞면
    face(c, 14, 140, 146, 150, R_WOOD, 0.85, grad=0.1); c.hline(14, 146, 140, WD[5])
    face(c, 14, 151, 146, 198, R_WOOD, 0.48, grad=0.2)
    for x in range(14, 147, 12):
        c.vline(x, 151, 198, WD[1]); c.vline(x + 1, 151, 198, WD[4])
    c.hline(14, 146, 198, WD[0]); c.vline(146, 140, 198, WD[0])
    # 탁자 위: 장부·동전·잔·등불
    face(c, 40, 132, 66, 139, R_CLOTH, 0.8); c.hline(40, 66, 132, PL[4]); c.vline(53, 132, 139, PL[0])
    for (x, y) in ((76, 136), (80, 137), (84, 135)):
        c.rect(x, y, x + 2, y + 1, A[22]); c.px(x, y, A[24])
    c.rect(96, 128, 101, 139, PL[3]); c.vline(101, 128, 139, PL[1]); c.hline(96, 101, 128, PL[4])
    glass_lantern(c, 122, 112, 16, 28)
    # 기둥
    for x in (16, 138):
        face(c, x, 44, x + 6, 139, R_WOOD, 0.55); c.vline(x, 44, 139, WD[4]); c.vline(x + 6, 44, 139, WD[1])
    # 지붕(널, 앞으로 기운 면)
    for y in range(14, 60):
        t = (y - 14) / 46
        inset = int(10 * (1 - t))
        for x in range(4 + inset, 156 - inset):
            plank = ((x + int(t * 3)) // 12) % 2
            s = 0.78 - t * 0.35 - (0.1 if plank else 0)
            c.px(x, y, qcol(R_WOODG, s, x, y))
    for x in range(4, 156, 12):
        for y in range(16, 60):
            c.px(x + int((y - 14) / 46 * 3), y, WD[1])
    c.hline(4, 155, 59, WD[0]); c.hline(4, 155, 60, SL[0]); c.hline(14, 146, 14, PL[2])
    grain(c, 6, 16, 154, 58, R_WOODG, 51, vertical=True, density=0.06)
    return Prop("toll_booth", c, (80, 200), footprint=(2, 1), occlude=70,
                light=L("#e8b858", 260, 0.9, 122, 128, 0.08, 5), placement="floor (벽 앞 권장)")


def barrel_cart():
    """술통 수레(3칸): 짐칸에 술통 3 + 바퀴 2 + 끌채."""
    c = Canvas(224, 176)
    contact(c, 112, 166, 100, 9)
    # 짐칸 바닥(윗면) + 옆판(앞면)
    face(c, 24, 96, 196, 110, R_WOOD, 0.7, grad=0.2)
    face(c, 24, 111, 196, 136, R_WOOD, 0.45, grad=0.2)
    for x in range(24, 197, 14):
        c.vline(x, 111, 136, WD[1])
    c.hline(24, 196, 111, WD[4]); c.hline(24, 196, 136, WD[0])
    grain(c, 25, 112, 195, 135, R_WOOD, 61, vertical=False, density=0.08)
    # 누운 술통 3(짐칸 위, 원통 끝이 보임)
    for k, bx in enumerate((40, 92, 144)):
        for x in range(bx, bx + 48):
            t = (x - bx) / 48
            rr = 20 * (1 + 0.1 * math.sin(math.pi * t))
            for y in range(int(80 - rr), int(80 + rr) + 1):
                v = (y - 80) / rr
                s = 0.42 + 0.62 * (lam(0, v, math.sqrt(max(0, 1 - v * v))) - 0.15)
                c.px(x, y, qcol(R_WOOD, s, x, y))
        for hx_ in (bx + 6, bx + 41):
            for y in range(60, 101):
                v = (y - 80) / 21
                if abs(v) <= 1:
                    xx = hx_ + int(3 * math.sqrt(max(0, 1 - v * v)))
                    c.px(xx, y, G[5] if v < 0 else G[3])
        # 끝면 타원(오른쪽)
        for y in range(60, 101):
            v = (y - 80) / 20
            half = int(8 * math.sqrt(max(0, 1 - v * v)))
            for x in range(bx + 48 - half, bx + 48 + half):
                c.px(x, y, qcol(R_WOOD, 0.75 - 0.3 * v, x, y))
            if half:
                c.px(bx + 48 - half, y, WD[1])
        c.rect(bx + 46, 78, bx + 49, 81, WD[1])
    # 바퀴 2
    for wx in (56, 168):
        for k in range(96):
            a = 2 * math.pi * k / 96
            for rr in (28, 27, 26, 25):
                x, y = int(wx + rr * math.cos(a) * 0.45), int(138 + rr * math.sin(a))
                c.px(x, y, WD[4] if rr > 26 and math.cos(a) < 0 else (WD[3] if rr > 25 else WD[1]))
        for k in range(8):
            a = 2 * math.pi * k / 8
            c.line(wx, 138, int(wx + 24 * math.cos(a) * 0.45), int(138 + 24 * math.sin(a)), WD[2])
        cyl(c, wx, 135, 140, 4, R_IRON, ry=2)
    # 끌채(왼쪽으로 뻗음)
    for k in range(30):
        c.px(24 - k, 128 + k // 3, WD[4]); c.px(24 - k, 129 + k // 3, WD[3]); c.px(24 - k, 130 + k // 3, WD[1])
    return Prop("barrel_cart", c, (112, 166), footprint=(3, 1), occlude=50, placement="floor (가장자리 권장)")


def barricade_x():
    """말뚝 X 바리케이드(2칸)."""
    c = Canvas(160, 112)
    contact(c, 80, 104, 70, 6)
    r = Rand(7)
    for k, bx in enumerate((22, 62, 102)):
        for (x0, y0, x1, y1) in ((bx - 14, 104, bx + 30, 30), (bx + 30, 104, bx - 10, 34)):
            n = max(abs(x1 - x0), abs(y1 - y0))
            for i in range(n + 1):
                t = i / n
                x, y = int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)
                w = 5 if t < 0.85 else int(5 * (1 - (t - 0.85) / 0.15)) + 1
                for j in range(w):
                    s = 0.65 - j * 0.1 + (0.2 if t > 0.85 else 0)
                    c.px(x + j, y, qcol(R_WOOD if k % 2 else R_WOODG, s, x + j, y))
    # 가로대
    face(c, 4, 70, 156, 76, R_WOOD, 0.6); c.hline(4, 156, 70, WD[5]); c.hline(4, 156, 76, WD[0])
    for x in (30, 70, 110):
        c.rect(x, 71, x + 2, 73, G[3]); c.px(x, 71, G[7])
    return Prop("barricade_x", c, (80, 104), footprint=(2, 1), occlude=30, placement="floor (엄폐)")


def water_trough():
    """돌 말 물통(2칸 가로)."""
    c = Canvas(144, 96)
    contact(c, 72, 90, 64, 6)
    # 앞면
    face(c, 10, 52, 134, 88, R_NSTONE, 0.45, grad=0.25)
    for x in range(10, 135, 31):
        c.vline(x, 52, 88, G[1])
    c.hline(10, 134, 88, G[1]); c.vline(134, 40, 88, G[1])
    # 윗테 + 물
    face(c, 8, 36, 136, 52, R_NSTONE, 0.8)
    face(c, 16, 40, 128, 49, [SL[1], SL[2], SL[3], SL[4], SL[5]], 0.45, grad=-0.3)
    c.hline(8, 136, 36, G[7]); c.hline(16, 128, 40, G[2])
    for (x, y, n) in ((30, 44, 12), (70, 46, 18), (106, 43, 8)):
        c.hline(x, x + n, y, SL[5]); c.px(x + n // 2, y, SL[7])
    # 이끼·물자국
    r = Rand(4)
    for _ in range(50):
        x, y = r.i(12, 132), r.i(54, 86)
        c.px(x, y, G[2])
    return Prop("water_trough", c, (72, 90), footprint=(2, 1), occlude=20, placement="floor")


def small():
    return [barrel(), crate(), sacks(), lantern(), puddle_g(), debris_g(), tipped_barrel()]


def big():
    return [toll_booth(), barrel_cart(), barricade_x(), water_trough(), torch_stand(), crate_stack()]
