"""4지역 쿼터뷰 바닥 타일셋 정의 — 황무지·성문·양조·연회장 (53라운드, 외곽 v2 인덱스 규칙).

각 지역 함수는 Region 을 돌려준다: cells{인덱스: Canvas 32×32}, decals[(이름, Canvas, 메타)], meta(JSON 조각).
벽은 '최소' — 테두리(Gemini)가 외벽을 맡으므로 내부 장애물(앞면 2칸 + 윗면)과 엄폐 담(stoneSet)만 지역 재질로.
문·출구·상점(8~12)은 외곽 v2 그림을 그대로 쓴다(테두리 골목 조각이 덮음, 폴백).
"""
import math
from fk import *  # noqa: F401,F403
from fk import (fbm, T, new, Canvas, Rand, G, A, SL, WD, PL, NT, TV2, surface, field, mask_field, crack, pebbles, tuft,
                soot, stain, flags, recolor, add_rim, bricks, qcol, clamp, window)


class Region:
    def __init__(self, rid):
        self.rid = rid
        self.cells = {}
        self.decals = []        # (name, Canvas, meta)
        self.meta = {}

    def put(self, i, c):
        self.cells[i] = c


def common_cells(R, top_fn, void_fn):
    """모든 지역 공통: 문·출구·상점(외곽 v2), 바닥 그늘 53~57, 윗면 가장자리 48~52."""
    R.put(8, TV2.gate("open")); R.put(9, TV2.gate("closed")); R.put(10, TV2.gate("locked"))
    R.put(11, TV2.exit_steps()); R.put(12, TV2.shop_deck())
    for i, k in zip(range(53, 58), ("n", "w", "e", "nw", "ne")):
        R.put(i, TV2.shadow(k))
    for i, sides in zip(range(48, 53), ("e", "w", "n", "ne", "nw")):
        R.put(i, top_fn(600 + i, sides))
    R.put(7, void_fn(0)); R.put(58, void_fn(1)); R.put(59, void_fn(2))


# ===========================================================================
# 황무지 waste — 갈라진 마른 흙(개념도 b · 테두리 북 b 의 흙둑·앞 땅 색)
# ===========================================================================
EARTH = [WD[1], WD[2], PL[0], WD[3], PL[1], PL[2]]     # 회갈 위주(테두리 앞 땅 50,41,39 의 /0.85) + 갈색 섞임
EARTH_D = [SL[0], WD[0], WD[1], WD[2], WD[3], PL[0]]   # 젖은·그을린 흙
STONE_W = [SL[1], G[3], PL[0], PL[1], PL[2]]            # 납작 돌·자갈(따뜻한 회색)
GRASS = [WD[1], WD[3], PL[1], PL[2]]                     # 마른 풀(밑동 → 끝)
SHARED_W = 9001


def w_earth(var, base=0.42, amp=0.3, varamp=1.0, ramp=EARTH):
    return surface(ramp, base, amp, SHARED_W, var, sharp=3.0, varamp=varamp)


def w_flatstone(c, seed, cx, cy, rx, ry):
    r = Rand(seed)
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            d = ((x - cx) / (rx + 0.3)) ** 2 + ((y - cy) / (ry + 0.3)) ** 2
            if d <= 1:
                s = 0.55 - 0.3 * (x - cx) / rx - 0.35 * (y - cy) / ry
                c.px(x, y, qcol(STONE_W, s, x, y, 3))
    for x in range(cx - rx + 1, cx + rx):
        c.px(x, cy + ry + 1, WD[1])


def waste():
    R = Region("waste")
    # 0~3 바닥
    c = w_earth(11); pebbles(c, 12, 1, STONE_W); R.put(0, c)
    c = w_earth(21, varamp=0.8)
    crack(c, 22, 5, 8, 22, WD[0], PL[1]); crack(c, 23, 18, 20, 12, WD[0], PL[1]); R.put(1, c)
    c = w_earth(31); tuft(c, 32, 12, 20, GRASS); R.put(2, c)
    c = w_earth(41); w_flatstone(c, 42, 17, 15, 6, 3); R.put(3, c)
    # 4 복도: 다져진 길(어둡고 매끈) + 발자국
    c = w_earth(51, varamp=0.5)
    for (x, y) in ((8, 8), (14, 20), (22, 10)):
        c.px(x, y, WD[1]); c.px(x + 1, y, WD[1]); c.px(x, y + 1, WD[2]); c.px(x + 1, y + 2, WD[1])
    R.put(4, c)
    # roomFloors
    for k in range(4):                                         # start: 그을린 흙 + 재
        c = w_earth(100 + k)
        soot(c, 10 + k * 3, 14 + k, 7, 4, 110 + k, SL[0])
        if k in (1, 3):
            for (x, y) in ((14, 18), (18, 12)):
                c.px(x, y, G[6]); c.px(x + 1, y, G[5])          # 재
        if k == 2:
            c.px(16, 16, A[18]); c.px(17, 16, A[17])           # 식은 숯불(비발광)
        R.put(23 + k, c)
    for k in range(4):                                         # trial: 진흙 + 웅덩이
        c = w_earth(200 + k)
        if k != 1:
            stain(c, 15 + k, 15, 7, 3, 210 + k, [SL[0], SL[1], SL[3]], glint=SL[5])
        else:
            crack(c, 211, 6, 8, 16, SL[0], WD[3])
        R.put(27 + k, c)
    for k in range(4):                                         # rest: 다진 흙 + 지푸라기
        c = w_earth(300 + k)
        r = Rand(310 + k)
        for _ in range(7):
            x, y = r.i(5, 24), r.i(5, 25)
            ln = r.i(3, 6)
            for j in range(ln):
                c.px(x + j, y + (j if r.f() < 0.3 else 0) // 2, PL[3] if j % 2 else A[19])
        R.put(31 + k, c)
    for k in range(4):                                         # boss: 짓밟힌 흙 + 부러진 화살·뼛조각
        c = w_earth(400 + k)
        r = Rand(410 + k)
        for _ in range(2):
            x, y = r.i(6, 20), r.i(6, 22)
            for j in range(8):
                c.px(x + j, y + j // 3, WD[4] if j < 6 else G[7])
        pebbles(c, 420 + k, 3, STONE_W)
        if k == 0:
            c.px(12, 20, PL[4]); c.px(13, 20, PL[3]); c.px(12, 21, PL[2])
        R.put(35 + k, c)
    # 60~62 바닥 특징
    c = w_earth(601)
    for y0 in (10, 21):                                        # 바퀴 자국(가로 이어짐)
        c.hline(0, T - 1, y0, WD[1]); c.hline(0, T - 1, y0 + 1, WD[2]); c.hline(0, T - 1, y0 + 2, PL[1])
    R.put(60, c)
    c = w_earth(602)
    for k in range(5):
        tuft(c, 610 + k, 6 + k * 5, 14 + (k % 2) * 8, GRASS)
    R.put(61, c)
    c = w_earth(603); pebbles(c, 604, 14, STONE_W); R.put(62, c)

    # 벽: 흙둑(앞면 아랫단·윗단·윗면)
    def bank_face(seed, upper=False, kind="plain"):
        c = new()
        r = Rand(seed)
        for y in range(T):
            for x in range(T):
                s = 0.45 + 0.25 * field(SHARED_W + 5, None, x, y * 2) - (0.0 if upper else 0.1 * y / T)
                if (x * 7 + seed) % 11 == 0:
                    s -= 0.18                                    # 세로 결(다진 흙 단면)
                c.px(x, y, qcol(EARTH, s, x, y, 3))
        for _ in range(3):                                        # 잔뿌리
            x, y = r.i(3, 28), r.i(2, 20)
            for j in range(r.i(5, 9)):
                c.px(x + (j % 3 == 0) * r.choice([-1, 1]), y + j, WD[0])
        for _ in range(2):
            w_flatstone(c, r.i(0, 99), r.i(6, 25), r.i(8, 24), 3, 2)
        if upper:
            # 위 끝: 둑 위 풀이 넘어 늘어짐
            for x in range(T):
                h = 2 + (x * 5 + seed) % 4
                for y in range(h):
                    c.px(x, y, GRASS[min(3, y)] if (x + y) % 3 else WD[1])
        else:
            c.hline(0, T - 1, T - 1, WD[0]); c.hline(0, T - 1, T - 2, WD[1])
        if kind == "planks":                                     # 널 받침(무너짐 방지)
            for x0 in (2, 13, 24):
                c.rect(x0, 4, x0 + 6, T - 3, WD[3]); c.vline(x0, 4, T - 3, WD[4]); c.vline(x0 + 6, 4, T - 3, WD[1])
            c.rect(0, 12, T - 1, 13, WD[2]); c.hline(0, T - 1, 12, WD[4])
        if kind == "torch":                                      # 꽂힌 횃불(자체 발광)
            c.rect(15, 14, 16, 29, WD[3]); c.vline(15, 14, 29, WD[4])
            for (x, y, col) in ((14, 12, A[23]), (15, 11, A[25]), (16, 10, A[26]), (15, 12, A[26]), (16, 12, A[25]),
                                (17, 12, A[23]), (15, 9, A[24]), (16, 13, A[24]), (15, 13, A[24])):
                c.px(x, y, col)
        if kind == "bones":
            c.rect(9, 16, 14, 20, PL[3]); c.px(10, 18, SL[0]); c.px(13, 18, SL[0]); c.hline(10, 13, 20, PL[2])
            c.hline(16, 24, 22, PL[3]); c.hline(16, 24, 23, PL[1])
        if kind == "banner":
            pts = [(9, 0), (22, 0), (22, 24), (18, 20), (15, 28), (12, 19), (9, 23)]
            m = Canvas(T, T)
            m.poly(pts, SL[1])
            for y in range(T):
                for x in range(T):
                    if m.get(x, y)[3]:
                        c.px(x, y, A[16] if (x + y) % 5 else SL[1])
            c.hline(12, 19, 6, A[18]); c.vline(15, 6, 12, A[18]); c.vline(16, 6, 12, A[18]); c.hline(13, 18, 13, A[18])
        return c

    R.put(5, bank_face(501)); R.put(21, bank_face(521, kind="torch")); R.put(22, bank_face(522, kind="planks"))
    R.put(63, bank_face(563, kind="bones"))
    R.put(40, bank_face(540, True)); R.put(41, bank_face(541, True, "planks")); R.put(42, bank_face(542, True, "banner"))

    def bank_top(seed, sides=""):
        c = surface([WD[1], WD[2], WD[3], PL[0], PL[1]], 0.45, 0.35, SHARED_W + 9, seed, sharp=3)
        r = Rand(seed)
        for _ in range(3):
            tuft(c, r.i(0, 999), r.i(4, 27), r.i(6, 28), GRASS)
        return add_rim(c, sides, PL[1], WD[3], WD[0])
    R.put(6, bank_top(601)); R.put(47, add_rim(bank_top(647), "s", PL[1], WD[2], WD[0]))

    # 엄폐 담 = 모래주머니 담 (43 아랫단 · 44 윗단 · 45 윗면 · 46 아랫단 + 말뚝)
    SB = [SL[1], PL[0], PL[1], PL[2], PL[3]]

    def sandbag_rows(c, y0, y1, seed, offset=0):
        r = Rand(seed)
        y = y0
        row = 0
        while y + 7 <= y1 + 1:
            x = -((row + offset) % 2) * 8
            while x < T:
                w = 15
                for yy in range(y, y + 7):
                    for xx in range(max(0, x), min(T, x + w)):
                        u, v = (xx - x) / w, (yy - y) / 7
                        edge = u < 0.08 or u > 0.92 or v > 0.85
                        s = 0.75 - 0.4 * u - 0.5 * v + (0.15 if v < 0.25 else 0)
                        c.px(xx, yy, SB[0] if (edge and v > 0.85) else qcol(SB, s, xx, yy, 3))
                if 0 <= x + w // 2 < T:
                    c.px(x + w // 2, y + 3, SB[1])
                x += w + 1
            y += 7
            row += 1
    c = new(); c.rect(0, 0, T - 1, T - 1, SB[0]); sandbag_rows(c, 0, 31, 1); c.hline(0, T - 1, T - 1, SL[0]); R.put(43, c)
    c = new(); c.rect(0, 4, T - 1, T - 1, SB[0]); sandbag_rows(c, 4, 31, 2, 1)
    for x in range(T):                                          # 맨 위 줄(위에서 보이는 둥근 윗면)
        c.px(x, 2, SB[3]); c.px(x, 3, SB[2])
    R.put(44, c)
    c = new()
    for y in range(T):
        for x in range(T):
            u = (x % 16) / 16
            v = (y % 8) / 8
            c.px(x, y, qcol(SB, 0.8 - 0.3 * u - 0.45 * v, x, y, 3) if not (v > 0.86 or u > 0.94) else SB[0])
    R.put(45, c)
    c = R.cells[43].im.copy(); c2 = new(); c2.im = c; c2.p = c.load()
    c2.rect(13, 0, 18, T - 1, WD[3]); c2.vline(13, 0, T - 1, WD[4]); c2.vline(18, 0, T - 1, WD[1])
    R.put(46, c2)

    def top_fn(seed, sides):
        return bank_top(seed, sides)

    def void_fn(k):
        c = new()
        c.rect(0, 0, T - 1, T - 1, NT[1])
        if k == 1:
            soot(c, 16, 16, 12, 8, 77, NT[0])
        elif k == 2:
            c.rect(0, 0, T - 1, T - 1, NT[0])
        else:
            for y in range(0, T, 6):
                c.hline(0, T - 1, y, NT[2])
        return c
    common_cells(R, top_fn, void_fn)

    # 데칼(반투명·rect): 바퀴 자국 3칸, 그을린 자국 2칸
    d = Canvas(96, 32)
    for x in range(96):
        a = int(150 * min(1, x / 16, (95 - x) / 16))
        yy = int(2 * math.sin(x / 20))
        for (y0, col) in ((9, WD[0]), (10, WD[1]), (21, WD[0]), (22, WD[1])):
            d.px(x, y0 + yy, col[:3] + (a,))
        d.px(x, 11 + yy, PL[1][:3] + (a // 2,)); d.px(x, 23 + yy, PL[1][:3] + (a // 2,))
    R.decals.append(("wheel_ruts", d, {"footprint": [3, 1], "note": "가로 바퀴 자국(바닥 위·소품 아래)"}))
    d = Canvas(64, 64)
    r = Rand(5)
    for y in range(64):
        for x in range(64):
            dd = ((x - 32) / 30) ** 2 + ((y - 32) / 22) ** 2
            if dd < 1 and r.f() < (1 - dd) * 0.8 and (x + y) % 2 == 0:
                d.px(x, y, SL[0][:3] + (int(170 * (1 - dd)),))
    R.decals.append(("scorch", d, {"footprint": [2, 2], "note": "그을린 자국(모닥불·불탄 수레 밑)"}))

    R.meta = {
        "name": "잔(盞) — 황무지(전장) v2 (쿼터뷰)",
        "tiles": {"0": [7, 7, 7, 58, 59], "1": [0, 0, 1, 2, 3], "2": [5, 5, 22, 21, 63], "3": [8], "4": [9], "5": [10],
                  "6": [4], "7": [11], "8": [12]},
        "walls": {"front": {"lower": [5, 5, 22, 21, 63], "upper": [40, 40, 41, 42]}, "top": 6, "topAboveFront": 47,
                  "left": 48, "right": 49, "bottom": 50, "corner_tl": 48, "corner_tr": 49, "corner_bl": 51, "corner_br": 52,
                  "stoneSet": {"lower": [43, 43, 46], "upper": [44], "top": 45,
                               "note": "모래주머니 담(엄폐). 52라운드: 황무지는 1칸 낮은 담 허용 → upper 를 생략하고 lower+top 만 써도 된다"},
                  "note": "흙둑(내부 장애물). 외벽은 테두리(assets/tiles/border/waste)가 덮는다"},
        "tileLights": {"21": {"color": "#eebb6d", "radius": 80, "intensity": 0.6, "flicker": {"amp": 0.15, "hz": 6},
                              "offset": {"x": 16, "y": 11}}},
        "floorFeatures": {"wheelRut": 60, "grass": 61, "gravel": 62,
                          "note": "선택. wheelRut 은 가로로 이어짐(같은 행 연속)"},
        "roomFloorsNote": "start = 그을린 흙·재, trial = 진흙·웅덩이·금, rest = 다진 흙·지푸라기, boss = 짓밟힌 흙·부러진 화살",
    }
    return R


# ===========================================================================
# 성문 gate — 진창 위 닳은 포석(개념도 a · 테두리 북 성벽 발치)
# ===========================================================================
SETT = [G[1], G[2], G[3], G[4], G[5], G[6]]
MUD = [SL[0], SL[1], WD[1], WD[2], PL[0], PL[1]]
SHARED_G = 9101


GSTONE = [WD[1], G[4], PL[0], PL[1], PL[2]]       # 따뜻한 회갈 돌(테두리 성벽 발치 땅 46,37,34 쪽)


def setts_mud(var, mud_p=0.3, seed=0, puddle=False, layout=None):
    """성문 바닥: 닳은 중립 회색 판석(외곽 v2 판석 규칙) + 안쪽 진흙 얼룩(가장자리 안 걸침).
    mud_p = 진흙 덩어리 수·크기 정도. 큰 진창은 데칼(wheel_ruts·light_puddles)과 roomFloors 로."""
    c = flags(layout or TV2.FLOOR_LAYOUTS[var % 4], 700 + var * 13, GSTONE, WD[1], SL[0], wet=0.15)
    r = Rand(seed * 31 + var)
    n = int(mud_p * 4 + 0.5)
    for k in range(n):
        cx, cy = r.i(8, 23), r.i(8, 23)
        stain(c, cx, cy, r.i(3, 3 + int(mud_p * 8)), r.i(2, 3), seed + k, [WD[2], WD[2], WD[3]])
    if puddle:
        stain(c, 16, 18, 8, 2, seed + 11, [SL[0], SL[1], A[17]], glint=A[19])
    return c


def gate():
    R = Region("gate")
    R.put(0, setts_mud(11, 0.0, 1)); R.put(1, setts_mud(21, 0.0, 2)); R.put(2, setts_mud(31, 0.6, 3))
    R.put(3, setts_mud(41, 0.12, 4))
    c = setts_mud(51, 0.05, 5); R.put(4, c)
    for k in range(4):                         # start: 포석 + 지푸라기·말굽 자국
        c = setts_mud(100 + k, 0.2, 100 + k)
        r = Rand(110 + k)
        for _ in range(4):
            x, y = r.i(4, 24), r.i(4, 26)
            for j in range(4):
                c.px(x + j, y + (j // 2), PL[3] if j % 2 else A[19])
        R.put(23 + k, c)
    for k in range(4):                         # trial: 깨진 포석 + 진흙 웅덩이(문빛 반사)
        c = setts_mud(200 + k, 0.35, 200 + k, puddle=(k % 2 == 0))
        if k % 2:
            crack(c, 210 + k, 7, 7, 14, G[1], G[5])
        R.put(27 + k, c)
    for k in range(4):                         # rest: 진흙 + 짚
        c = setts_mud(300 + k, 0.6, 300 + k)
        r = Rand(310 + k)
        for _ in range(6):
            x, y = r.i(4, 24), r.i(4, 26)
            for j in range(5):
                c.px(x + j, y, PL[3] if j % 2 else A[19])
        R.put(31 + k, c)
    for k in range(4):                         # boss: 성문 앞 광장 큰 판석(잔 문양 하나)
        c = flags(TV2.FLOOR_LAYOUTS[k], 400 + k * 13, [G[2], G[3], G[4], G[5], G[6]], G[1], SL[0], wet=0.3)
        if k == 0:
            for y in range(10, 18):
                half = int(5 * (1 - (y - 10) / 8) ** 0.6)
                c.hline(16 - half, 16 + half, y, A[17])
            c.vline(16, 18, 22, A[17]); c.hline(12, 20, 23, A[17])
        R.put(35 + k, c)
    # 특징
    c = setts_mud(601, 0.3, 601)
    for y0 in (9, 21):
        c.hline(0, T - 1, y0, SL[0]); c.hline(0, T - 1, y0 + 1, WD[1]); c.hline(0, T - 1, y0 + 2, WD[3])
    R.put(60, c)
    c = setts_mud(602, 0.1, 602)
    c.rect(9, 9, 22, 22, G[1])
    for x in range(10, 22, 3):
        c.vline(x, 10, 21, G[5]); c.vline(x + 1, 10, 21, G[3])
    c.hline(9, 22, 9, G[6]); c.hline(9, 22, 22, SL[0]); R.put(61, c)
    R.put(62, setts_mud(603, 0.5, 603, puddle=True))

    # 벽: 성벽 큰 돌(앞면 2칸) — 다듬은 큰 돌 + 기단
    NS = [G[1], G[2], G[3], G[4], G[5], G[6]]

    def ashlar_n(c, y0, y1, seed, course=10):
        r = Rand(seed)
        c.rect(0, y0, T - 1, y1, G[1])
        y, row = y0, 0
        while y <= y1:
            h = min(course, y1 - y + 1)
            x = -(row % 2) * 9 - r.i(0, 3)
            while x < T:
                w = r.i(13, 18)
                sx0, sx1 = max(0, x), min(T - 1, x + w - 2)
                if sx1 - sx0 >= 1 and h >= 3:
                    k = r.i(2, 3)
                    c.rect(sx0, y, sx1, y + h - 2, NS[k])
                    c.hline(sx0, sx1, y, NS[k + 2]); c.vline(sx0, y, y + h - 2, NS[k + 1])
                    c.hline(sx0, sx1, y + h - 2, NS[k - 1])
                    if r.f() < 0.5:
                        c.px(sx0 + r.i(2, max(2, sx1 - sx0 - 2)), y + r.i(2, max(2, h - 3)), NS[k - 1])
                x += w
            y += h
            row += 1

    def wall_lower(seed, kind="plain"):
        c = new(); ashlar_n(c, 0, 25, seed)
        c.rect(0, 26, T - 1, T - 1, G[3]); c.hline(0, T - 1, 26, G[6]); c.hline(0, T - 1, T - 1, G[0])
        c.hline(0, T - 1, 27, G[4])
        if kind == "torch":
            c.rect(14, 12, 17, 18, G[2]); c.hline(13, 18, 12, G[5]); c.rect(15, 18, 16, 22, G[3])
            for (x, y, col) in ((15, 11, A[25]), (16, 11, A[26]), (15, 10, A[26]), (16, 9, A[24]), (14, 11, A[23]),
                                (17, 11, A[23]), (15, 8, A[23]), (16, 10, A[27])):
                c.px(x, y, col)
        if kind == "ring":
            c.rect(14, 12, 17, 13, G[6])
            for (x, y) in ((13, 14), (13, 15), (13, 16), (18, 14), (18, 15), (18, 16), (14, 17), (15, 17), (16, 17), (17, 17)):
                c.px(x, y, G[5])
        if kind == "drain":
            c.rect(11, 18, 20, 25, SL[0]); c.hline(11, 20, 18, G[5])
            for x in range(12, 20, 3):
                c.vline(x, 19, 25, G[4])
        return c

    def wall_upper(seed, kind="plain"):
        c = new(); ashlar_n(c, 0, T - 1, seed)
        if kind == "slit":
            c.rect(14, 4, 17, 24, G[3]); c.rect(15, 5, 16, 23, SL[0]); c.hline(14, 17, 4, G[5])
        if kind == "banner":
            for y in range(0, 28):
                for x in range(9, 23):
                    if y < 22 or abs(x - 16) < (28 - y):
                        c.px(x, y, A[16] if (x + y) % 6 else SL[1])
            c.vline(9, 0, 22, A[18]); c.vline(22, 0, 22, A[17])
            for y in range(6, 13):
                half = int(4 * (1 - (y - 6) / 7) ** 0.6)
                c.hline(16 - half, 16 + half, y, A[19])
            c.vline(16, 13, 16, A[19]); c.hline(13, 19, 17, A[19])
        return c

    R.put(5, wall_lower(501)); R.put(21, wall_lower(521, "torch")); R.put(22, wall_lower(522, "ring"))
    R.put(63, wall_lower(563, "drain"))
    R.put(40, wall_upper(540)); R.put(41, wall_upper(541, "slit")); R.put(42, wall_upper(542, "banner"))

    def walk_top(seed, sides=""):
        c = flags(TV2.FLOOR_LAYOUTS[seed % 4], seed, [G[1], G[2], G[3], G[4], G[5]], SL[0], SL[0], wet=0.0, flecks=0.6)
        return add_rim(c, sides, G[6], G[4], G[0])
    R.put(6, walk_top(601))
    c = walk_top(647)                           # 흉벽 끝(아래 = 앞면 쪽): 위에서 본 총안
    for x0 in range(0, T, 16):
        c.rect(x0, 22, x0 + 9, T - 1, G[4]); c.hline(x0, x0 + 9, 22, G[6]); c.vline(x0 + 9, 22, T - 1, G[1])
        c.rect(x0 + 10, 26, x0 + 15, T - 1, SL[0])
    R.put(47, c)

    # 엄폐 담 = 낮은 경비 돌담(외곽 돌담을 중립 회색으로)
    mp = {SL[i][:3]: G[i + 1][:3] for i in range(7)}
    R.put(43, recolor(TV2.stone_lower(543), mp)); R.put(44, recolor(TV2.stone_upper(544), mp))
    R.put(45, recolor(TV2.stone_top(545), mp)); R.put(46, recolor(TV2.stone_lower(546, ring=True), mp))

    def void_fn(k):                             # 해자(검은 물)
        c = new(); c.rect(0, 0, T - 1, T - 1, NT[0] if k == 2 else NT[1])
        if k != 2:
            for (x, y, n) in ((4, 8, 6), (18, 20, 8), (10, 27, 4)):
                c.hline(x, x + n, y, NT[2])
            if k == 1:
                c.hline(12, 16, 14, A[17]); c.px(14, 14, A[19])
        return c
    common_cells(R, walk_top, void_fn)

    d = Canvas(96, 32)
    for x in range(96):
        a = int(160 * min(1, x / 14, (95 - x) / 14))
        yy = int(2 * math.sin(x / 18 + 1))
        for (y0, col) in ((8, SL[0]), (9, WD[1]), (10, WD[2]), (20, SL[0]), (21, WD[1]), (22, WD[2])):
            d.px(x, y0 + yy, col[:3] + (a,))
    R.decals.append(("wheel_ruts", d, {"footprint": [3, 1], "note": "진창 깊은 바퀴 자국(성문 앞 길)"}))
    d = Canvas(64, 32)
    stain(d, 20, 16, 14, 5, 7, [SL[0], WD[1], A[18]], glint=A[20])
    stain(d, 44, 18, 10, 4, 9, [SL[0], WD[1], A[18]], glint=A[20])
    R.decals.append(("light_puddles", d, {"footprint": [2, 1], "note": "문빛을 받은 물웅덩이(층 램프, 비발광)"}))

    R.meta = {
        "name": "잔(盞) — 성문 v2 (쿼터뷰)",
        "tiles": {"0": [7, 7, 7, 58, 59], "1": [0, 0, 1, 1, 3, 3, 2], "2": [5, 5, 22, 21, 63], "3": [8], "4": [9], "5": [10],
                  "6": [4], "7": [11], "8": [12]},
        "walls": {"front": {"lower": [5, 5, 22, 21, 63], "upper": [40, 40, 41, 42]}, "top": 6, "topAboveFront": 47,
                  "left": 48, "right": 49, "bottom": 50, "corner_tl": 48, "corner_tr": 49, "corner_bl": 51, "corner_br": 52,
                  "stoneSet": {"lower": [43, 43, 46], "upper": [44], "top": 45, "note": "낮은 경비 돌담(엄폐)"},
                  "note": "성벽 큰 돌(내부 장애물). 52라운드 '성문만 앞면 3칸'은 테두리 북 띠가 맡는다 — 내부 장애물은 2칸"},
        "tileLights": {"21": {"color": "#eebb6d", "radius": 90, "intensity": 0.65, "flicker": {"amp": 0.15, "hz": 6},
                              "offset": {"x": 16, "y": 9}}},
        "floorFeatures": {"wheelRut": 60, "grate": 61, "lightPuddle": 62, "note": "선택. wheelRut 은 가로로 이어짐"},
        "roomFloorsNote": "start = 포석·짚, trial = 깨진 포석·문빛 웅덩이, rest = 진흙·짚, boss = 성문 앞 큰 판석(_0 잔 문양)",
    }
    return R


# ===========================================================================
# 양조 구역 brewery — 젖은 닳은 판석 + 술 얼룩 + 술 수로(개념도 b)
# ===========================================================================
BSTONE = [G[2], G[3], G[4], G[5], G[6]]
LIQ = [A[16], A[17], A[18], A[19], A[20], A[21]]


def b_floor(i, seed, wet=0.4, stain_k=None):
    c = flags(TV2.FLOOR_LAYOUTS[i % 4], seed, BSTONE, G[1], SL[0], wet=wet)
    if stain_k is not None:
        stain(c, 14 + stain_k, 16, 6, 2, seed + 5, [WD[1], A[16], A[17]], glint=A[19])
    return c


def canal(frame, lit=False):
    """술 수로(가로, 1칸 높이): 위 6px = 북쪽 둑 안벽(앞면), 아래 3px = 남쪽 둑 갓돌, 가운데 = 흐르는 술.
    frame 0~2: 물결이 오른쪽으로 4px 씩 흐름(32 의 약수 아님 → 주기 3프레임에 12px, 타일 이음은 줄 단위로 닫힘)."""
    c = new()
    # 남쪽 갓돌(아래 3px) + 북쪽 안벽(위 6px)
    for x in range(T):
        c.px(x, 0, G[6]); c.px(x, 1, G[4])
        for y in range(2, 7):
            c.px(x, y, G[3] if (x // 8 + y // 3) % 2 == 0 else G[2])
        c.px(x, 7, SL[0])
        c.px(x, T - 3, G[1]); c.px(x, T - 2, G[5]); c.px(x, T - 1, G[4])
    for x in range(0, T, 8):
        c.vline(x, 2, 6, G[1])
    c.px(0, T - 2, G[2]); c.px(16, T - 2, G[2])
    # 술(비발광 램프 위주, lit = 다리 근처 밝은 판)
    off = frame * 4
    for y in range(8, T - 3):
        t = (y - 8) / (T - 11)
        for x in range(T):
            wave = math.sin(2 * math.pi * ((x + off) / 16.0) + y * 0.9)
            s = 0.25 + 0.35 * t + 0.12 * wave + (0.25 if lit else 0)
            c.px(x, y, qcol(LIQ, s, x, y, 3))
    # 물결 빛 줄(lit 이면 자체 발광 색 일부)
    for (yy, ph) in ((12, 0), (17, 5), (22, 11)):
        for x in range(T):
            if (x + off + ph) % 16 < 4:
                c.px(x, yy, A[23] if lit and (x + off + ph) % 16 == 1 else A[21])
    # 거품
    for (x0, y0) in ((5, 10), (21, 19)):
        x = (x0 + off) % T
        c.px(x, y0, PL[3]); c.px((x + 1) % T, y0, PL[2])
    c.hline(0, T - 1, 8, A[16])          # 안벽 밑 그늘
    return c


def bridge(side, frame=0):
    """널다리(2칸 폭, 남북으로 건넘): side 'l'/'r'. 아래 수로가 다리 가장자리로 보인다."""
    c = canal(frame, lit=True)
    x0, x1 = (3, T - 1) if side == "l" else (0, T - 4)
    for y in range(0, T):
        for x in range(x0, x1 + 1):
            k = (x - x0) % 6
            c.px(x, y, WD[4] if k == 0 else (WD[1] if k == 5 else WD[3]))
    for y in range(0, T, 11):
        c.hline(x0, x1, y, WD[2])
    # 난간 기둥·가로대(바깥쪽)
    rx = x0 if side == "l" else x1
    c.vline(rx, 0, T - 1, WD[5] if side == "l" else WD[1])
    for y in (3, 19):
        c.rect(rx - (0 if side == "l" else 2), y, rx + (2 if side == "l" else 0), y + 4, WD[2])
    c.vline(x0 - 1 if side == "l" else x1 + 1, 0, T - 1, SL[0])
    for y in (6, 22):
        c.px(x0 + 3, y, G[7]); c.px(x1 - 3, y, G[7])
    return c


def brewery():
    R = Region("brewery")
    R.put(0, b_floor(0, 100)); R.put(1, b_floor(1, 113)); R.put(2, b_floor(2, 126)); R.put(3, b_floor(3, 139))
    R.put(4, recolor(TV2.corridor(), {SL[i][:3]: G[min(15, i + 1)][:3] for i in range(8)}))
    for k in range(4):
        c = b_floor(k, 200 + k * 7, wet=0.2)
        soot(c, 12 + k * 2, 14, 8, 5, 210 + k, G[1])
        R.put(23 + k, c)
    for k in range(4):
        c = b_floor(k, 300 + k * 7, stain_k=k)
        if k == 1:
            crack(c, 311, 6, 6, 14, G[1], G[5])
        R.put(27 + k, c)
    for k in range(4):                     # rest: 자루 천 깔개·짚
        c = b_floor(k, 400 + k * 7, wet=0.1)
        r = Rand(410 + k)
        for _ in range(6):
            x, y = r.i(4, 24), r.i(4, 26)
            for j in range(5):
                c.px(x + j, y, PL[3] if j % 2 else A[19])
        R.put(31 + k, c)
    for k in range(4):                     # boss: 큰 술 얼룩
        c = b_floor(0, 500 + k * 7, wet=0.5)
        stain(c, 16, 16, 10, 5, 510 + k, [A[16], A[17], A[18]], glint=A[21])
        R.put(35 + k, c)
    mp = {SL[i][:3]: G[min(15, i + 1)][:3] for i in range(8)}
    R.put(60, recolor(TV2.drain(False), mp)); R.put(61, recolor(TV2.drain(True), mp))
    c = b_floor(2, 603); stain(c, 16, 16, 11, 4, 604, [A[16], A[17], A[18]], glint=A[20]); R.put(62, c)
    # 수로·다리 64~71
    R.put(64, canal(0)); R.put(65, canal(1)); R.put(66, canal(2))
    R.put(67, bridge("l")); R.put(68, bridge("r"))
    R.put(69, canal(0, True)); R.put(70, canal(1, True)); R.put(71, canal(2, True))

    # 벽: 그을린 벽돌
    BR = [SL[1], G[2], G[3], PL[0], PL[1]]

    def brick_lower(seed, kind="plain"):
        c = new(); bricks(c, 0, 24, seed, BR, SL[0], soot_top=0.4)
        c.rect(0, 25, T - 1, T - 1, G[3]); c.hline(0, T - 1, 25, G[5]); c.hline(0, T - 1, T - 1, G[0])
        if kind == "furnace":              # 아치 화구(쇠문 반쯤 열림, 자체 발광)
            for y in range(6, 25):
                for x in range(6, 26):
                    if (x - 16) ** 2 / 100 + (y - 16) ** 2 / 110 <= 1 or y >= 16:
                        c.px(x, y, G[2])
            for y in range(9, 25):
                for x in range(9, 23):
                    if (x - 16) ** 2 / 49 + (y - 16) ** 2 / 64 <= 1 or y >= 16:
                        hot = 1 - ((x - 16) ** 2 + (y - 22) ** 2) / 90
                        c.px(x, y, [A[22], A[23], A[24], A[25], A[26], A[27]][max(0, min(5, int(hot * 6)))])
            c.rect(19, 13, 23, 24, G[3]); c.vline(19, 13, 24, G[5])
        if kind == "pipe":
            c.rect(0, 10, T - 1, 13, G[3]); c.hline(0, T - 1, 10, G[6]); c.hline(0, T - 1, 13, G[1])
            c.rect(20, 6, 25, 17, G[4]); c.hline(20, 25, 6, G[7]); c.rect(21, 3, 24, 5, A[18])
        if kind == "vent":
            c.rect(10, 8, 21, 18, SL[0])
            for x in range(11, 21, 3):
                c.vline(x, 8, 18, G[4])
            c.hline(10, 21, 7, G[5])
        return c

    def brick_upper(seed, kind="plain"):
        c = new(); bricks(c, 0, T - 1, seed, BR, SL[0], soot_top=0.7)
        if kind == "window":
            c.rect(9, 6, 22, 22, G[2]); c.rect(10, 7, 21, 21, SL[0])
            for x in range(11, 21, 3):
                c.vline(x, 7, 21, G[4])
            c.hline(9, 22, 22, G[5])
        if kind == "pipe":
            c.rect(0, 14, T - 1, 18, A[17]); c.hline(0, T - 1, 14, A[19]); c.hline(0, T - 1, 18, A[16])
            for x in (6, 22):
                c.rect(x, 13, x + 2, 19, G[4])
        return c

    R.put(5, brick_lower(501)); R.put(21, brick_lower(521, "furnace")); R.put(22, brick_lower(522, "pipe"))
    R.put(63, brick_lower(563, "vent"))
    R.put(40, brick_upper(540)); R.put(41, brick_upper(541, "window")); R.put(42, brick_upper(542, "pipe"))
    R.put(6, TV2.roof(601)); R.put(47, TV2.roof(647, eave=True))
    # 엄폐 담: 낮은 벽돌 담 + 돌 갓
    c = new(); bricks(c, 0, T - 1, 543, BR, SL[0]); c.hline(0, T - 1, T - 1, SL[0]); R.put(43, c)
    c = new(); bricks(c, 6, T - 1, 544, BR, SL[0])
    c.rect(0, 0, T - 1, 5, G[4]); c.hline(0, T - 1, 0, G[6]); c.hline(0, T - 1, 5, G[1])
    for x in range(0, T, 10):
        c.vline(x, 0, 5, G[2])
    R.put(44, c)
    c = flags(TV2.FLOOR_LAYOUTS[3], 545, [G[2], G[3], G[4], G[5], G[6]], G[1], SL[0], wet=0.0, flecks=0.4); R.put(45, c)
    c = new(); bricks(c, 0, T - 1, 546, BR, SL[0])
    c.rect(12, 6, 19, 25, A[17]); c.rect(13, 7, 18, 24, A[18]); c.hline(12, 19, 6, A[19])   # 구리 관 뚜껑(층 램프)
    R.put(46, c)

    def top_fn(seed, sides):
        s = {"e": "e", "w": "w", "n": "n", "ne": "ne", "nw": "nw"}[sides]
        return TV2.roof_edge(s, seed)

    def void_fn(k):
        return TV2.void(["roofs", "chimney", "gap"][k], 700 + k)
    common_cells(R, top_fn, void_fn)

    d = Canvas(64, 32)
    stain(d, 22, 15, 15, 6, 31, [A[16], A[17], A[18]], glint=A[20])
    stain(d, 46, 20, 9, 4, 33, [A[16], A[17], A[18]])
    R.decals.append(("liquor_trail", d, {"footprint": [2, 1], "note": "술 흘린 자국(층 램프, 글린트만 밝게)"}))

    R.meta = {
        "name": "잔(盞) — 양조 구역 v2 (쿼터뷰)",
        "tiles": {"0": [7, 7, 7, 58, 59], "1": [0, 0, 1, 1, 3, 3, 2], "2": [5, 5, 22, 21, 63], "3": [8], "4": [9], "5": [10],
                  "6": [4], "7": [11], "8": [12]},
        "walls": {"front": {"lower": [5, 5, 22, 21, 63], "upper": [40, 40, 41, 42]}, "top": 6, "topAboveFront": 47,
                  "left": 48, "right": 49, "bottom": 50, "corner_tl": 48, "corner_tr": 49, "corner_bl": 51, "corner_br": 52,
                  "stoneSet": {"lower": [43, 43, 46], "upper": [44], "top": 45, "note": "낮은 벽돌 담(엄폐)"},
                  "note": "그을린 벽돌(내부 장애물). 21 = 화구(자체 발광, tileLights)"},
        "tileLights": {"21": {"color": "#e8a33c", "radius": 110, "intensity": 0.8, "flicker": {"amp": 0.12, "hz": 5},
                              "offset": {"x": 16, "y": 20}},
                       "67": {"color": "#e2a33c", "radius": 70, "intensity": 0.45, "flicker": {"amp": 0.05, "hz": 1.5},
                              "offset": {"x": 30, "y": 16}}},
        "floorFeatures": {"drain": 60, "drainGrate": 61, "liquorStain": 62},
        "canal": {
            "frames": [64, 65, 66], "framesLit": [69, 70, 71], "frameMs": 180,
            "bridge": {"left": 67, "right": 68},
            "litNearBridge": 2,
            "walkable": False,
            "note": ("술 수로(52라운드 Q4: 지나갈 수 없음, 다리로만 건넘). 가로 한 줄(1칸 높이)로 바닥을 가로지른다. "
                     "수로 칸 = 걷기 막힘(벽처럼 충돌), 다리 칸(2칸 폭, left·right) = 걷기 가능. "
                     "frames 를 frameMs 로 순환(3프레임, 물결이 동쪽으로 흐름). 다리 좌우 litNearBridge 칸은 framesLit(밝은 판, "
                     "52라운드 '수로 밝기는 다리 근처만'). 투사체 통과 여부는 시스템 결정(질문)"),
        },
        "roomFloorsNote": "start = 그을음, trial = 술 얼룩·금, rest = 짚, boss = 큰 술 얼룩",
    }
    return R


# ===========================================================================
# 연회장 hall — 큰 광택 돌판 + 잔 문장 상감(개념도 b · 테두리 북 단상)
# ===========================================================================
HSTONE = [G[3], G[4], G[5], G[6], G[7]]


def h_floor(layout, seed, wet=0.55):
    c = flags(layout, seed, HSTONE, G[2], G[1], wet=wet, flecks=0.5)
    return c


def hall():
    R = Region("hall")
    L1 = [(1, 1, 31, 31)]
    R.put(0, h_floor(L1, 100)); R.put(1, h_floor(L1, 113)); R.put(2, h_floor(TV2.FLOOR_LAYOUTS[3], 126))
    R.put(3, h_floor(L1, 139))
    # 4 복도 = 붉은 양탄자(층 램프) + 금실 가장자리 — 가로·세로 어느 쪽도 이어지게 무늬는 안쪽 반복
    c = new()
    for y in range(T):
        for x in range(T):
            k = 0.45 + 0.1 * math.sin(x * 0.8) * math.sin(y * 0.8)
            c.px(x, y, qcol([SL[0], A[16], A[17], A[18]], k, x, y, 3))
    for y in range(4, T, 8):
        for x in range(4, T, 8):
            c.px(x, y, A[19]); c.px(x + 1, y, A[18]); c.px(x, y + 1, A[18])
    R.put(4, c)
    for k in range(4):                      # start: 엎질러진 술
        c = h_floor(L1, 200 + k * 7)
        if k % 2 == 0:
            stain(c, 15, 16, 8, 3, 210 + k, [A[16], A[17], A[18]], glint=A[21])
        R.put(23 + k, c)
    for k in range(4):                      # trial: 금 간 돌판
        c = h_floor(TV2.FLOOR_LAYOUTS[k], 300 + k * 7)
        crack(c, 310 + k, 6, 7, 16, G[2], G[7])
        R.put(27 + k, c)
    for k in range(4):                      # rest: 골풀 깔개
        c = h_floor(L1, 400 + k * 7, wet=0.2)
        r = Rand(410 + k)
        for _ in range(8):
            x, y = r.i(4, 24), r.i(4, 26)
            for j in range(5):
                c.px(x + j, y + j // 3, PL[3] if j % 2 else A[19])
        R.put(31 + k, c)
    for k in range(4):                      # boss: 금실 상감 테
        c = h_floor(L1, 500 + k * 7)
        for (a, b) in ((3, 28),):
            c.hline(a, b, a, A[19]); c.hline(a, b, b, A[18]); c.vline(a, a, b, A[19]); c.vline(b, a, b, A[18])
        R.put(35 + k, c)
    c = h_floor(L1, 601); stain(c, 16, 16, 10, 4, 602, [A[16], A[17], A[18]], glint=A[21]); R.put(60, c)
    c = h_floor(L1, 603); c.hline(0, T - 1, 15, A[19]); c.hline(0, T - 1, 16, A[17]); R.put(61, c)
    c = h_floor(L1, 604)
    r = Rand(605)
    for _ in range(6):
        x, y = r.i(5, 25), r.i(5, 25)
        c.px(x, y, SL[6]); c.px(x + 1, y, SL[4]); c.px(x, y + 1, SL[3])
    R.put(62, c)

    # 벽: 판벽 돌 + 기단
    def panel_lower(seed, kind="plain"):
        c = flags([(1, 1, 31, 24)], seed, [G[2], G[3], G[4], G[5], G[6]], G[1], G[0], wet=0.0, flecks=0.4)
        c.rect(0, 25, T - 1, T - 1, G[4]); c.hline(0, T - 1, 25, G[7]); c.hline(0, T - 1, 26, G[5]); c.hline(0, T - 1, T - 1, G[1])
        c.rect(5, 5, 26, 20, G[3]); c.hline(5, 26, 5, G[2]); c.vline(5, 5, 20, G[2]); c.hline(5, 26, 20, G[5]); c.vline(26, 5, 20, G[5])
        if kind == "sconce":
            c.rect(14, 12, 17, 16, A[18]); c.hline(12, 19, 11, A[19]); c.rect(15, 6, 16, 10, PL[4])
            c.px(15, 5, A[25]); c.px(16, 4, A[26]); c.px(15, 4, A[24]); c.px(16, 5, A[27])
        if kind == "niche":
            c.rect(10, 7, 21, 20, SL[0]); c.hline(10, 21, 7, G[2]); c.rect(13, 13, 18, 20, PL[2]); c.hline(13, 18, 13, PL[4])
        return c

    def drape_upper(seed, kind="plain"):
        c = flags([(1, 1, 31, 31)], seed, [G[2], G[3], G[4], G[5], G[6]], G[1], G[0], wet=0.0, flecks=0.4)
        if kind in ("drape", "banner"):
            for y in range(T):
                for x in range(6, 26):
                    fold = (x - 6) % 5
                    c.px(x, y, [A[16], A[17], A[16], SL[0], A[16]][fold])
            if kind == "banner":
                for y in range(8, 17):
                    half = int(5 * (1 - (y - 8) / 9) ** 0.6)
                    c.hline(16 - half, 16 + half, y, A[19])
                c.vline(16, 17, 21, A[19]); c.hline(12, 20, 22, A[19])
        if kind == "plain":
            c.rect(0, 0, T - 1, 3, G[5]); c.hline(0, T - 1, 3, G[1])
        return c

    R.put(5, panel_lower(501)); R.put(21, panel_lower(521, "sconce")); R.put(22, panel_lower(522))
    R.put(63, panel_lower(563, "niche"))
    R.put(40, drape_upper(540)); R.put(41, drape_upper(541, "drape")); R.put(42, drape_upper(542, "banner"))

    def h_top(seed, sides=""):
        c = flags([(1, 1, 31, 15), (1, 17, 31, 31)], seed, [G[1], G[2], G[3], G[4], G[5]], SL[0], SL[0], wet=0.0, flecks=0.4)
        return add_rim(c, sides, G[6], G[4], G[0])
    R.put(6, h_top(601))
    c = h_top(647); c.rect(0, 24, T - 1, T - 1, G[4]); c.hline(0, T - 1, 24, G[7]); c.hline(0, T - 1, 27, G[2])
    c.hline(0, T - 1, T - 1, G[1])
    for x in range(2, T, 6):
        c.rect(x, 28, x + 2, 30, G[5])
    R.put(47, c)
    # 엄폐 담 = 돌 난간(43 난간 기둥 · 44 손잡이 + 기둥 윗부분 · 45 손잡이 윗면 · 46 굵은 기둥)

    def balusters(c, y0, y1, thick=False):
        c.rect(0, y1 - 3, T - 1, y1, G[4]); c.hline(0, T - 1, y1 - 3, G[6]); c.hline(0, T - 1, y1, G[1])
        for bx in ((4, 20) if not thick else (8,)):
            w = 8 if not thick else 16
            for y in range(y0, y1 - 3):
                t = (y - y0) / max(1, y1 - 3 - y0)
                half = w / 2 * (0.55 + 0.45 * abs(math.sin(math.pi * (t * 1.6 + 0.1))))
                cx = bx + w / 2
                for x in range(int(cx - half), int(cx + half) + 1):
                    u = (x - cx) / max(1, half)
                    c.px(x, y, qcol([G[2], G[3], G[4], G[5], G[6], G[7]], 0.6 - 0.45 * u, x, y, 3))
    c = new(); balusters(c, 0, T - 1); R.put(43, c)
    c = new(); balusters(c, 10, T - 1)
    c.rect(0, 0, T - 1, 9, G[5]); c.hline(0, T - 1, 0, G[8]); c.hline(0, T - 1, 1, G[7]); c.hline(0, T - 1, 9, G[1])
    c.hline(0, T - 1, 8, G[3]); R.put(44, c)
    c = new(); c.rect(0, 0, T - 1, T - 1, G[5])
    for y in range(T):
        c.px(0, y, G[3])
    c.rect(0, 0, T - 1, 2, G[7]); c.hline(0, T - 1, T - 1, G[2])
    for y in range(6, T, 8):
        c.hline(2, T - 3, y, G[4])
    R.put(45, c)
    c = new(); balusters(c, 0, T - 1, thick=True); R.put(46, c)

    def void_fn(k):                          # 난간 너머 낭떠러지(멀리 도시 창 몇 점)
        c = new(); c.rect(0, 0, T - 1, T - 1, NT[0])
        if k == 0:
            for (x, y) in ((6, 20), (22, 9)):
                c.px(x, y, A[17]); c.px(x + 1, y, A[16])
        if k == 1:
            for y in range(18, T):
                c.hline(0, T - 1, y, NT[1] if (y // 3) % 2 else NT[2])
        return c
    common_cells(R, h_top, void_fn)

    # 잔 문장 상감 데칼(4×4칸, 바닥 위) — 개념도 b 가운데
    d = Canvas(128, 128)
    for y in range(128):
        for x in range(128):
            dd = max(abs(x - 63.5), abs(y - 63.5))
            if 58 <= dd <= 60:
                d.px(x, y, A[18][:3] + (200,))
            elif dd == 61:
                d.px(x, y, A[16][:3] + (200,))
    # 잔(굽 + 몸통)
    for y in range(24, 64):
        t = (y - 24) / 40
        half = 26 * (1 - t ** 1.6)
        for x in range(int(64 - half), int(64 + half) + 1):
            edge = abs(x - 64) > half - 3 or y < 27
            d.px(x, y, (A[19] if edge else A[17])[:3] + (190,))
    for y in range(64, 92):
        d.rect(61, y, 66, y, A[18][:3] + (190,))
    for y in range(92, 100):
        half = 18 + (y - 92)
        d.hline(64 - half, 64 + half, y, (A[19] if y == 92 else A[17])[:3] + (190,))
    R.decals.append(("cup_inlay", d, {"footprint": [4, 4], "note": "잔 문장 상감(연회장 가운데 — 보스 시작 단상 앞). 층 램프, 비발광"}))
    d = Canvas(64, 32)
    stain(d, 26, 15, 16, 6, 61, [A[16], A[17], A[18]], glint=A[21])
    stain(d, 50, 21, 8, 3, 63, [A[16], A[17], A[18]])
    R.decals.append(("wine_trail", d, {"footprint": [2, 1], "note": "엎질러진 술 줄기"}))

    R.meta = {
        "name": "잔(盞) — 지배자의 연회장 v2 (쿼터뷰)",
        "tiles": {"0": [7, 7, 7, 58, 59], "1": [0, 0, 1, 1, 2, 3], "2": [5, 5, 22, 21, 63], "3": [8], "4": [9], "5": [10],
                  "6": [4], "7": [11], "8": [12]},
        "walls": {"front": {"lower": [5, 5, 22, 21, 63], "upper": [40, 41, 41, 42]}, "top": 6, "topAboveFront": 47,
                  "left": 48, "right": 49, "bottom": 50, "corner_tl": 48, "corner_tr": 49, "corner_bl": 51, "corner_br": 52,
                  "stoneSet": {"lower": [43, 43, 46], "upper": [44], "top": 45, "note": "돌 난간(엄폐). 46 = 굵은 난간 기둥"},
                  "note": "판벽 돌 + 휘장(내부 장애물). 21 = 촛불 벽등(tileLights)"},
        "tileLights": {"21": {"color": "#f4de9b", "radius": 80, "intensity": 0.55, "flicker": {"amp": 0.1, "hz": 6},
                              "offset": {"x": 16, "y": 5}}},
        "floorFeatures": {"wineStain": 60, "inlayLine": 61, "shards": 62, "note": "inlayLine 은 가로로 이어짐"},
        "roomFloorsNote": "start = 엎질러진 술, trial = 금 간 돌판, rest = 골풀 깔개, boss = 금실 상감 테(_0~3 같은 무늬 — 4칸 묶음 아님)",
    }
    return R


ALL = {"waste": waste, "gate": gate, "brewery": brewery, "hall": hall}
