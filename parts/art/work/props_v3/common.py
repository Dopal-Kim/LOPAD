"""여러 지역이 함께 쓰는 v3 소품(술통·상자·자루·쓰러진 술통·잔해·등불·화로 등) + Prop 묶음 형식."""
import math
from pk import *  # noqa: F401,F403
from pk import (U, Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_STONE, R_NSTONE, R_CLOTH, R_CLOTHG,
                R_LIQ, R_EARTH, contact, cyl, plank_box, shade_mask, mask, splash, flame, embers, glass_lantern,
                stone_blob, face, grain, ell_mask, poly_mask, outline, qcol, clamp, lam)

SMALL = 128           # 소품 칸(도트) — 논리 64×64
PIV = (64, 120)       # 소품 피벗 = 바닥 접점. 시스템은 이 점을 칸의 (16, 30)(논리, v2 와 같은 자리)에 둔다


class Prop:
    def __init__(self, name, canvas, pivot, footprint=(1, 1), solid=True, occlude=None, light=None, **extra):
        self.name, self.c, self.pivot = name, canvas, pivot
        self.footprint, self.solid, self.occlude, self.light = footprint, solid, occlude, light
        self.extra = extra

    @property
    def im(self):
        return self.c.im


def L(color, radius, intensity, ox, oy, amp=0.1, hz=5):
    """광원(도트 단위 radius·offset — 시스템이 pixelScale 0.5 로 환산)."""
    return {"color": color, "radius": radius, "intensity": intensity, "flicker": {"amp": amp, "hz": hz},
            "offset": {"x": ox, "y": oy}}


# ---------------------------------------------------------------------------
def barrel_c(c, cx, by, rx=26, h=66, seed=1, spill=True, tone=R_WOOD):
    """세운 참나무 술통. by = 밑면 접점 y. 폭 ≈ 2rx+4, 높이 ≈ h + rx."""
    ry = int(rx * 0.42)
    top, bot = by - ry - h, by - ry
    contact(c, cx + 2, by, rx + 6, 6)
    cyl(c, cx, top, bot, rx, tone, bulge=0.1, ry=ry, staves=7, seed=seed,
        hoops=((top + 7, 3), ((top + bot) // 2 - 2, 3), (bot - 8, 3)))
    # 마개 + 흘러내린 술 자국(층 램프 비발광)
    c.rect(cx - 3, top - 2, cx + 2, top + 1, WD[1]); c.hline(cx - 3, cx + 2, top - 2, WD[3])
    if spill:
        x = cx + rx // 2
        for y in range(bot - 26, bot - 4):
            c.px(x, y, A[19]); c.px(x + 1, y, A[18])
        c.px(x, bot - 26, A[22])


def barrel():
    c = Canvas(SMALL, SMALL)
    barrel_c(c, 64, 120)
    return Prop("barrel", c, PIV, occlude=24, maxPerRoom=3, weight=0.9, slot=13)


def crate_c(c, cx, by, w=60, h=40, top_h=20, seed=2, ramp=R_WOOD):
    contact(c, cx + 3, by - 1, w // 2 + 6, 6)
    plank_box(c, cx - w // 2, by - h - top_h, w, h, top_h, ramp=ramp, seed=seed)


def crate():
    c = Canvas(SMALL, SMALL)
    crate_c(c, 64, 120)
    # 위에 얹힌 자루 하나(덩어리감)
    sack_c(c, 58, 44, 40, 20, R_CLOTH, 4)
    return Prop("crate", c, PIV, occlude=20, maxPerRoom=2, weight=0.8, slot=14)


def puddle():
    c = Canvas(SMALL, SMALL)
    stoneR = [SL[1], SL[2], SL[3], SL[4], SL[6], SL[7]]
    splash(c, 60, 98, 40, 11, ramp=stoneR, seed=5, blobs=9)
    return Prop("puddle", c, PIV, solid=False, occlude=None, maxPerRoom=3, weight=1.0, slot=15, depth="floor")


def lantern():
    """바닥에 놓인 쇠 등불 — 받침 위 유리 등."""
    c = Canvas(SMALL, SMALL)
    contact(c, 66, 120, 18, 4)
    glass_lantern(c, 64, 64, 26, 52)
    # 네 발
    for x in (52, 75):
        c.rect(x, 116, x + 2, 119, G[3]); c.px(x, 116, G[6])
    # 손잡이 고리
    for k in range(15):
        a = math.pi * k / 14
        x, y = int(round(64 - 6 * math.cos(a))), int(round(58 - 8 * math.sin(a)))
        c.px(x, y, G[6] if k < 7 else G[4]); c.px(x, y + 1, G[2])
    return Prop("lantern", c, PIV, occlude=24, maxPerRoom=2, weight=0.6, slot=16,
                light=L("#e8b858", 240, 0.9, 64, 90, 0.08, 5))



def brazier_c(c, cx, by, scale=1.0, seed=3):
    s = scale
    contact(c, cx + 2, by, int(26 * s), 6)
    # 세발 다리(쇠)
    for (dx, col) in ((-18, G[5]), (16, G[3]), (-2, G[4])):
        x0, x1 = int(cx + dx * s), int(cx + dx * 0.45 * s)
        y0, y1 = by, int(by - 34 * s)
        c.line(x0, y0, x1, y1, col); c.line(x0 + 1, y0, x1 + 1, y1, G[2])
        c.rect(x0 - 1, by - 1, x0 + 2, by, G[2])
    # 그릇(반구 + 테)
    rx = int(26 * s)
    top = int(by - 50 * s)
    m, d = mask(2 * rx + 4, int(26 * s))
    d.pieslice((2, -int(22 * s), 2 * rx + 1, int(22 * s)), 0, 180, fill=255)
    shade_mask(c, m, R_IRON, ox=cx - rx - 2, oy=top + int(6 * s), base=0.45, gain=0.6, soft=3)
    # 테(타원)
    for x in range(cx - rx - 1, cx + rx + 2):
        u = (x - cx) / (rx + 1)
        yy = top + int(6 * s) + int(round(4 * s * math.sqrt(max(0, 1 - u * u))))
        c.px(x, top + int(6 * s) - int(round(4 * s * math.sqrt(max(0, 1 - u * u)))), G[7] if u < 0 else G[5])
        c.px(x, yy, G[3])
    # 숯
    for x in range(cx - rx + 3, cx + rx - 2):
        u = (x - cx) / rx
        h = int(3 * s * math.sqrt(max(0, 1 - u * u)))
        for y in range(top + int(6 * s) - h, top + int(6 * s) + 2):
            c.px(x, y, A[18] if (x + y) % 3 else A[21])
    flame(c, cx, top + int(6 * s), int(44 * s), int(46 * s), seed=seed, tongues=5)
    embers(c, cx, top - int(30 * s), 6, int(10 * s), seed + 1)


def brazier():
    c = Canvas(SMALL, SMALL)
    brazier_c(c, 64, 120)
    return Prop("brazier", c, PIV, occlude=26, maxPerRoom=1, weight=0.5, slot=17,
                light=L("#eecc78", 380, 1.2, 64, 66, 0.15, 7))


def sack_c(c, x, y, w, h, ramp, seed):
    """자루 하나: (x,y) 왼쪽 위. 위는 주름 잡혀 묶인 넓은 목(구겨진 천 끝이 비죽)."""
    m, d = mask(w + 4, h + 10)
    d.rounded_rectangle((2, 8, w + 1, h + 8), radius=max(4, min(w, h) // 3), fill=255)
    nw = max(5, w // 3)
    d.polygon([(w // 2 - nw, 10), (w // 2 + nw, 10), (w // 2 + nw // 2, 5), (w // 2 + nw, 0),
               (w // 2, 3), (w // 2 - nw, 1), (w // 2 - nw // 2, 5)], fill=255)
    shade_mask(c, m, ramp, ox=x, oy=y, base=0.5, gain=0.8, soft=4, tilt=0.15, sharp=2.5)
    # 묶은 끈
    c.hline(x + w // 2 - nw // 2 - 1, x + w // 2 + nw // 2 + 1, y + 7, WD[1])
    c.hline(x + w // 2 - nw // 2, x + w // 2 + nw // 2, y + 8, WD[3])
    # 주름(목에서 퍼지는 짧은 선)
    r = Rand(seed)
    for k in range(4):
        sx = x + w // 2 + (k - 1.5) * nw * 0.7
        for j in range(r.i(4, 8)):
            c.px(int(sx + (k - 1.5) * j * 0.4), y + 11 + j, ramp[1])


def sacks():
    c = Canvas(SMALL, SMALL)
    contact(c, 66, 118, 40, 7)
    sack_c(c, 26, 78, 38, 40, R_CLOTH, 1)
    sack_c(c, 60, 74, 40, 44, R_CLOTHG, 2)
    sack_c(c, 42, 48, 36, 34, R_CLOTH, 3)
    return Prop("sacks", c, PIV, occlude=22, maxPerRoom=1, weight=0.6, slot=18)


def tipped_barrel_c(c, x0, cy, length=74, r_=26, spill=True, seed=4):
    """옆으로 누운 술통(가로 원통). (x0, cy) = 왼쪽 끝 중심."""
    ry = int(r_ * 0.42) + 2
    if spill:
        splash(c, x0 + length + 12, cy + r_ - 2, 30, 8, seed=seed, blobs=5)
    contact(c, x0 + length // 2, cy + r_ - 1, length // 2 + 6, 5)
    for x in range(x0, x0 + length + 1):
        t = (x - x0) / length
        bul = 1 + 0.1 * math.sin(math.pi * t)
        rr = r_ * bul
        for y in range(int(cy - rr), int(cy + rr) + 1):
            v = (y + 0.5 - cy) / rr
            if abs(v) > 1:
                continue
            nz = math.sqrt(max(0, 1 - v * v))
            s = 0.42 + 0.62 * (lam(0.0, v, nz) - 0.15) + 0.06 * (0.5 - t)
            c.px(x, y, qcol(R_WOOD, s, x, y))
    # 널(가로 틈)
    for k in range(6):
        th = -math.pi / 2 + math.pi * (k + 0.5) / 6
        v = math.sin(th)
        for x in range(x0 + 2, x0 + length - 1):
            t = (x - x0) / length
            y = int(round(cy + v * r_ * (1 + 0.1 * math.sin(math.pi * t))))
            cur = c.get(x, y)
            if cur in R_WOOD:
                c.px(x, y, R_WOOD[max(0, R_WOOD.index(cur) - 1)])
    # 쇠테(세로 곡선 — 오른쪽으로 휨)
    for hx_ in (x0 + 8, x0 + length // 2, x0 + length - 9):
        t = (hx_ - x0) / length
        rr = r_ * (1 + 0.1 * math.sin(math.pi * t))
        for y in range(int(cy - rr), int(cy + rr) + 1):
            v = (y - cy) / rr
            xx = hx_ + int(round(5 * math.sqrt(max(0, 1 - v * v))))
            s = 0.5 + 0.5 * (lam(0, v, math.sqrt(max(0, 1 - v * v))) - 0.2)
            c.px(xx, y, qcol(R_IRON, s, xx, y)); c.px(xx + 1, y, qcol(R_IRON, s - 0.15, xx + 1, y))
            c.px(xx - 1, y, R_IRON[4] if v < 0 else R_IRON[2])
    # 열린 끝(오른쪽 타원) — 안쪽 어둠 + 술
    ex = x0 + length
    for y in range(int(cy - r_), int(cy + r_) + 1):
        v = (y - cy) / r_
        half = int(round(ry * math.sqrt(max(0, 1 - v * v))))
        for x in range(ex - half, ex + half + 1):
            edge = abs(x - ex) >= half - 2 or abs(v) > 0.88
            c.px(x, y, R_WOOD[3] if (edge and x < ex) else (R_WOOD[1] if edge else SL[0]))
        if half > 3 and v > 0.35:
            c.hline(ex - half + 3, ex + half - 3, y, A[17] if v < 0.7 else A[18])


def tipped_barrel():
    c = Canvas(SMALL, SMALL)
    tipped_barrel_c(c, 8, 92, length=72, r_=24)
    return Prop("tipped_barrel", c, (56, 118), occlude=16, maxPerRoom=1, weight=0.4, slot=19,
                note="'술통 굴림' — 쓰러진 술통 + 쏟아진 술. 그림 폭이 1칸보다 넓다(좌우로 약 0.3칸 넘침, 충돌은 1칸)")


def debris_c(c, cx, cy, w, h, seed, ramp=R_STONE, pottery=True):
    r = Rand(seed)
    for k in range(14):
        x = cx + r.i(-w // 2, w // 2)
        y = cy + r.i(-h // 2, h // 2)
        stone_blob(c, x, y, r.i(3, 7), r.i(2, 5), ramp, seed * 7 + k, soft=2)
    if pottery:
        # 깨진 도기 잔 조각 2개
        for (x, y) in ((cx - 6, cy - 2), (cx + 12, cy + 5)):
            m = poly_mask(14, 10, [(0, 3), (9, 0), (13, 5), (6, 9)])
            shade_mask(c, m, R_CLOTH, ox=x, oy=y, base=0.65, gain=0.6, soft=1)
            c.hline(x + 2, x + 8, y + 2, PL[4])


def debris():
    c = Canvas(SMALL, SMALL)
    debris_c(c, 62, 100, 64, 22, 7)
    return Prop("debris", c, PIV, solid=False, occlude=None, maxPerRoom=3, weight=1.0, slot=20, depth="floor")

