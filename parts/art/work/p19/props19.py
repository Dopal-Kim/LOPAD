"""P19 1-A 형태별 무대 중심 소품 7 + 위험물 실루엣 4 (structures/v3, 트림 아틀라스).

무대 중심: stage_fountain(원형 광장) · stage_dock_crane(부두) · stage_signpost(십자로) · stage_terrace_stair(테라스 계단 난간 기둥)
          · stage_cask_pile(술창고 — 연쇄 폭발 무더기) · stage_rampart_beacon(성벽 회랑 봉화) · stage_still(증류소 증류기 — 증기 분출)
위험물: hazard_cask_row(술통 줄) · hazard_pool(술 웅덩이) · hazard_merlon(흉벽) · (증류기는 stage_still 상태)
읽힘 규칙(P19 F): 술통 = 호박 띠(A22~23 칠한 띠), 웅덩이 = 반짝임, 낙하 = 난간 끊김(타일), 흉벽 = 금 → 무너짐.
그림 도구는 props_v3/pk(bundle2 b2 경유)·색은 lopad gray + 1층 램프 + SL·WD·PL. 단위 도트(pixelScale 0.5).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "bundle2"))
sys.path.insert(0, os.path.join(WORK, "atlas57"))
import b2  # noqa: E402
from b2 import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_STONE, R_NSTONE, R_WSTONE, R_CLOTH,  # noqa: E402
                R_COPPER, R_LIQ, FLAME, contact, cyl, plank_box, shade_mask, splash, flame, embers, glass_lantern,
                stone_blob, face, grain, ell_mask, poly_mask, qcol, clamp, lam, EMISSIVE_HEX)
from PIL import Image, ImageDraw  # noqa: E402

SRC = "parts/art/work/p19/props19.py (P19 1-A 무대 중심·위험물)"
R_BRASS = [A[16], A[17], A[18], A[19], A[20], A[22]]
BAND = [A[19], A[21], A[22], A[23]]          # 호박 띠(23 = 발광 — 불붙음 상태에서만 넓게)
R_BRICK = [WD[0], WD[1], A[17], A[18], WD[4], A[19], PL[3]]
R_STEAM = [SL[5], SL[6], SL[7], G[11], G[12], G[13]]
R_LIGHTSTONE = [SL[2], SL[3], PL[1], PL[2], PL[3], PL[4], G[12]]


def C(w, h):
    return Canvas(w, h)


def ellipse_ring(c, cx, cy, rx, ry, rx2, ry2, ramp, base=0.6):
    m = ell_mask(c.w, c.h, (cx - rx, cy - ry, cx + rx, cy + ry))
    inner = ell_mask(c.w, c.h, (cx - rx2, cy - ry2, cx + rx2, cy + ry2))
    mp, ip = m.load(), inner.load()
    for y in range(c.h):
        for x in range(c.w):
            if mp[x, y] > 127 and ip[x, y] <= 127:
                s = base + 0.25 * (-(x - cx) / rx * 0.5 - (y - cy) / ry * 0.6)
                c.px(x, y, qcol(ramp, s, x, y))


def fill_ell(c, cx, cy, rx, ry, fn):
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d <= 1:
                col = fn(x, y, d)
                if col is not None:
                    c.px(x, y, col)


def stream(c, x0, y0, x1, y1, phase, w=2):
    """흘러내리는 술 줄기(포물선) — phase 로 밝은 마디가 흐름."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 1.5) + 2
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t * t
        lit = ((t * 6 - phase) % 1.0) < 0.35
        for k in range(w):
            c.px(int(x) + k, int(y), A[22] if lit and k == 0 else (A[20] if k == 0 else A[19]))


# ================================================================ 무대 중심 소품
def fountain(frame):
    """원형 광장 술샘 분수: 낮은 둥근 석조 수반(술 고임) + 가운데 기둥 + 위 잔 모양 받침 + 네 줄기 술."""
    W, H = 256, 256
    c = C(W, H)
    cx, cy = 128, 186
    contact(c, cx + 4, cy + 30, 120, 22, a=120)
    # 수반 옆면(원통 벽)
    cyl(c, cx, cy, cy + 22, 112, R_LIGHTSTONE, ry=44, lid=False, staves=0)
    # 수반 옆면 돌 이음(세로)
    for k in range(14):
        th = -math.pi / 2 + math.pi * (k + 0.5) / 14
        x = int(cx + math.sin(th) * 112)
        yb = cy + 22 + int(44 * math.cos(th) * 0.95)
        c.vline(x, cy + int(44 * math.cos(th)) + 2, yb - 1, R_LIGHTSTONE[1])
    # 위 테두리(두꺼운 돌 테) + 안쪽 술
    ellipse_ring(c, cx, cy, 112, 44, 98, 36, R_LIGHTSTONE, base=0.62)
    ph = frame / 6

    def liq(x, y, d):
        rr = math.sqrt(d)
        ring = math.sin((rr * 4 - ph * 2) * math.pi * 2)
        s = 0.44 + 0.05 * ring + 0.12 * (y - cy) / 36 - 0.08 * (x - cx) / 98
        if rr > 0.9:
            s -= 0.2
        return qcol(R_LIQ, s, x, y, 4)
    fill_ell(c, cx, cy + 2, 98, 35, liq)
    # 반짝임(술 = 반짝임 규칙)
    r = Rand(11 + frame)
    for _ in range(9):
        a = r.f() * 6.283
        rr = 0.3 + 0.6 * r.f()
        x, y = int(cx + math.cos(a) * 90 * rr), int(cy + 2 + math.sin(a) * 30 * rr)
        c.px(x, y, A[24]); c.px(x + 1, y, A[23])
    # 가운데 기둥(받침대)
    cyl(c, cx, cy - 64, cy + 2, 16, R_LIGHTSTONE, ry=7, staves=0, lid=False, bulge=-0.1)
    for y in range(cy - 60, cy + 2, 12):
        c.hline(cx - 15, cx + 15, y, R_LIGHTSTONE[1])
    # 위 받침(잔 모양): 아래 반구 + 테
    for y in range(cy - 90, cy - 62):
        t = (y - (cy - 90)) / 28
        half = 46 * math.sqrt(max(0, 1 - t * t * 0.9)) * (1 - 0.55 * t)
        for x in range(int(cx - half), int(cx + half) + 1):
            u = (x - cx) / max(1, half)
            s = 0.5 + 0.35 * (-u * 0.6) - 0.2 * t
            c.px(x, y, qcol(R_BRASS, s, x, y))
    ellipse_ring(c, cx, cy - 92, 48, 16, 40, 12, R_BRASS, base=0.7)
    fill_ell(c, cx, cy - 91, 40, 12, lambda x, y, d: qcol(R_LIQ, 0.62 - 0.3 * d + 0.08 * math.sin((d * 4 - ph) * 6.28), x, y, 4))
    # 잔(盞) 문양 — 받침 앞면
    for (dx, dy) in ((-4, -80), (-3, -80), (-2, -80), (-1, -80), (0, -80), (1, -80), (2, -80), (3, -80), (4, -80),
                     (-3, -79), (3, -79), (-2, -78), (2, -78), (-1, -77), (1, -77), (0, -76), (0, -75), (-2, -74), (-1, -74),
                     (0, -74), (1, -74), (2, -74)):
        c.px(cx + dx, cy + dy, A[23])
    # 네 줄기(위 받침 테에서 아래 수반으로)
    for k, (sx, ex) in enumerate(((-44, -86), (44, 86), (-26, -54), (26, 54))):
        sy = cy - 90 + (6 if abs(sx) < 30 else 0)
        stream(c, cx + sx, sy, cx + ex, cy + (8 if abs(sx) < 30 else -6), (ph + k * 0.25) % 1.0, w=3)
        # 떨어지는 곳 물보라
        ex_, ey_ = cx + ex, cy + (8 if abs(sx) < 30 else -6)
        for j in range(5):
            a = (j / 5 + ph) * 6.283
            c.px(int(ex_ + math.cos(a) * (4 + 2 * ((frame + j) % 2))), int(ey_ - abs(math.sin(a)) * 3), A[22] if j % 2 else PL[4])
    # 앞쪽 테 두 등(발광)
    for x in (cx - 78, cx + 78):
        y = cy + 30
        c.rect(x - 3, y - 26, x + 3, y, R_IRON[2]); c.vline(x - 3, y - 26, y, R_IRON[4])
        glass_lantern(c, x, y - 46, 12, 22)
    return c.im


def dock_crane(frame):
    """부두 나무 기중기: 돌 받침 + 기둥 + 팔 + 도르래 + 매달린 술통(흔들림 4)."""
    W, H = 224, 320
    c = C(W, H)
    contact(c, 70, 300, 60, 12, a=120)
    # 돌 받침
    plank_box(c, 30, 252, 84, 36, 18, ramp=R_STONE, seed=3, planks=3, slats=True, brace=False)
    # 감는 바퀴(왼쪽)
    for y in range(226, 262):
        for x in range(18, 54):
            d = math.hypot(x - 36, (y - 244) * 1.1)
            if 13 <= d <= 17:
                c.px(x, y, qcol(R_WOOD, 0.55 - (y - 244) / 40, x, y))
            elif d < 13 and abs(x - 36) < 2 or (d < 13 and abs(y - 244) < 2):
                c.px(x, y, R_WOOD[2])
    # 기둥
    for y in range(40, 256):
        for x in range(62, 76):
            u = (x - 69) / 7
            c.px(x, y, qcol(R_WOOD, 0.55 - u * 0.3, x, y))
    c.vline(62, 40, 255, R_WOOD[4]); c.vline(75, 40, 255, R_WOOD[0])
    grain(c, 63, 42, 74, 250, R_WOOD, 5)
    # 버팀대(사선)
    for k in range(70):
        x, y = 76 + k, 140 - k * 1.1
        for t in range(-2, 3):
            c.px(int(x), int(y) + t, R_WOOD[3] if t < 0 else R_WOOD[2])
    # 팔(가로)
    for y in range(44, 56):
        for x in range(50, 206):
            c.px(x, y, qcol(R_WOOD, 0.62 - (y - 44) / 22, x, y))
    c.hline(50, 205, 44, R_WOOD[5]); c.hline(50, 205, 55, R_WOOD[0])
    # 쇠 고리·도르래
    for y in range(52, 66):
        for x in range(190, 204):
            if math.hypot(x - 197, y - 59) <= 6:
                c.px(x, y, R_IRON[3] if (x + y) % 3 else R_IRON[5])
    # 줄 + 술통(흔들림)
    sway = [0, 3, 0, -3][frame % 4]
    top = (197, 64)
    bot = (197 + sway, 196)
    for i in range(140):
        t = i / 140
        x = int(top[0] + (bot[0] - top[0]) * t)
        y = int(top[1] + (bot[1] - top[1]) * t)
        c.px(x, y, R_WOOD[1]); c.px(x + 1, y, R_WOOD[3])
    bx = bot[0]
    cyl(c, bx, 204, 250, 22, R_WOOD, ry=9, staves=6, seed=7, hoops=((210, 2), (244, 2)), bulge=0.1)
    # 호박 띠(위험물 아님 — 기중기 짐)
    for x in range(bx - 23, bx + 24):
        c.px(x, 227 + int(9 * math.sqrt(max(0, 1 - ((x - bx) / 23) ** 2)) * 0.9), BAND[1])
    # 다른 쪽 줄(받침에 묶음)
    for i in range(100):
        t = i / 100
        c.px(int(76 + (190 - 76) * t), int(250 - (250 - 60) * t ** 0.7), R_WOOD[2] if i % 3 else R_WOOD[4])
    return c.im


def signpost(frame):
    """십자로 이정표: 돌 받침 + 나무 기둥 + 방향 판 4장(새긴 표식) + 매단 등."""
    W, H = 128, 224
    c = C(W, H)
    contact(c, 66, 214, 30, 8, a=120)
    stone_blob(c, 64, 206, 22, 10, R_STONE, 3)
    for y in range(30, 206):
        for x in range(59, 69):
            c.px(x, y, qcol(R_WOOD, 0.6 - (x - 59) / 14, x, y))
    c.vline(59, 30, 205, R_WOOD[4]); c.vline(68, 30, 205, R_WOOD[0])
    grain(c, 60, 32, 67, 200, R_WOOD, 9)
    boards = [(56, -1, 50), (74, 1, 46), (96, -1, 42), (118, 1, 38)]
    for (y, d, L_) in boards:
        x0 = 64 if d > 0 else 64 - L_
        x1 = 64 + L_ if d > 0 else 64
        for yy in range(y, y + 14):
            for xx in range(x0, x1 + 1):
                tip = (xx - x0) if d < 0 else (x1 - xx)
                if tip < abs(yy - (y + 7)) * 0.9:
                    continue
                c.px(xx, yy, qcol(R_WOODG, 0.62 - (yy - y) / 26, xx, yy))
        c.hline(x0 + 3, x1 - 3, y, R_WOODG[5]); c.hline(x0 + 3, x1 - 3, y + 13, R_WOODG[0])
        # 새긴 표식(가로 선 + 점)
        for k in range(3):
            xx = (x0 + 10 + k * 9) if d > 0 else (x1 - 14 - k * 9)
            c.hline(xx, xx + 5, y + 6, R_WOODG[1])
            c.px(xx + 2, y + 9, R_WOODG[1])
    # 위 가로대 + 매단 등
    for x in range(64, 100):
        c.px(x, 30, R_IRON[3]); c.px(x, 31, R_IRON[1])
    sw = [0, 1, 0, -1][frame % 4]
    c.vline(96 + sw, 31, 40, R_IRON[2])
    glass_lantern(c, 96 + sw, 42, 14, 24)
    # 기둥 위 갓
    c.rect(56, 24, 72, 30, R_WOOD[3]); c.hline(56, 72, 24, R_WOOD[5])
    return c.im


def terrace_stair(frame):
    """두 단 테라스 큰 계단 양옆 돌 난간 기둥(등 2) — 계단 타일(/) 위에 덧그림. 3~4칸 폭 계단 가운데에 둔다."""
    W, H = 288, 208
    c = C(W, H)
    for px_ in (22, 266):
        contact(c, px_ + 3, 198, 24, 7, a=120)
        # 기둥 몸(돌, 위 갓돌 + 몸 + 받침)
        face(c, px_ - 16, 120, px_ + 16, 196, R_LIGHTSTONE, 0.5, grad=0.25)
        c.vline(px_ - 16, 120, 196, R_LIGHTSTONE[4]); c.vline(px_ + 16, 120, 196, R_LIGHTSTONE[0])
        for y in (140, 160, 180):
            c.hline(px_ - 16, px_ + 16, y, R_LIGHTSTONE[1])
        face(c, px_ - 20, 112, px_ + 20, 120, R_LIGHTSTONE, 0.75)
        c.hline(px_ - 20, px_ + 20, 112, R_LIGHTSTONE[6]); c.hline(px_ - 20, px_ + 20, 120, R_LIGHTSTONE[1])
        face(c, px_ - 19, 190, px_ + 19, 197, R_LIGHTSTONE, 0.4)
        # 등(발광) + 쇠받침
        c.rect(px_ - 6, 100, px_ + 6, 111, R_IRON[2]); c.hline(px_ - 6, px_ + 6, 100, R_IRON[4])
        glass_lantern(c, px_, 66, 18, 34)
        # 난간 손잡이(계단 쪽으로 내려오는 돌 띠)
        d = 1 if px_ < 144 else -1
        for k in range(30):
            x = px_ + d * (16 + k)
            y = 128 + k * 2
            for t in range(6):
                c.px(x, y + t, R_LIGHTSTONE[3] if t else R_LIGHTSTONE[5])
            c.px(x, y + 6, R_LIGHTSTONE[0])
    return c.im


def cask_end(c, cx, cy, r, seed, lit=0, band=True):
    """누운 술통 끝(마구리)이 정면: 원판 + 널 이음 + 쇠테 + 호박 띠(테 안쪽)."""
    ry = r
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - r, cx + r + 1):
            d = math.hypot((x - cx) / r, (y - cy) / ry)
            if d > 1:
                continue
            if d > 0.86:
                s = 0.5 - 0.3 * (y - cy) / ry
                c.px(x, y, qcol(R_IRON, s, x, y))
            elif d > 0.74 and band:
                c.px(x, y, BAND[2 if lit == 0 else 3] if (x + y) % 5 else BAND[1])
            else:
                s = 0.55 - 0.25 * (x - cx) / r - 0.2 * (y - cy) / ry
                c.px(x, y, qcol(R_WOOD, s, x, y))
    for k in (-0.4, 0.0, 0.4):
        yy = int(cy + k * ry)
        half = int(r * 0.72 * math.sqrt(max(0, 1 - k * k)))
        c.hline(cx - half, cx + half, yy, R_WOOD[1])
    c.rect(cx - 2, cy - 2, cx + 2, cy + 2, R_WOOD[0]); c.px(cx - 1, cy - 1, A[20])


def cask_side_top(c, cx, cy, r, depth=18):
    """누운 술통 몸 윗면(뒤로 뻗은 부분) — 마구리 위로 보이는 원통 윗면."""
    for y in range(cy - r - depth // 2, cy - r + 4):
        for x in range(cx - r + 2, cx + r - 1):
            u = (x - cx) / r
            if abs(u) > 0.95:
                continue
            s = 0.62 - 0.3 * abs(u) + 0.1 * (cy - r - y) / depth
            c.px(x, y, qcol(R_WOOD, s, x, y))
    for x in range(cx - r + 2, cx + r - 1, 9):
        c.vline(x, cy - r - depth // 2, cy - r + 2, R_WOOD[1])


def cask_pile(state):
    """술창고 술통 더미(누운 통 3 + 2 + 1, 마구리가 정면): idle / lit_0 / lit_1(불꽃 튐) / wreck."""
    W, H = 256, 224
    c = C(W, H)
    contact(c, 132, 212, 116, 14, a=130)
    if state == "wreck":
        r = Rand(9)
        splash(c, 128, 198, 96, 16, seed=4, blobs=7)
        for k in range(16):
            x, y = 40 + r.i(0, 176), 150 + r.i(0, 50)
            L_ = r.i(10, 22)
            a = r.f() * 3.14
            for t in range(L_):
                c.px(int(x + math.cos(a) * t), int(y + math.sin(a) * t * 0.5), R_WOOD[2 + (t % 2)])
        for (x, y) in ((70, 190), (150, 186), (196, 196)):
            for k in range(30):
                a = k / 30 * 6.283
                c.px(int(x + math.cos(a) * 16), int(y + math.sin(a) * 6), R_IRON[3])
        for k in range(26):
            c.px(40 + r.i(0, 176), 160 + r.i(0, 44), [WD[0], SL[1]][k % 2])
        return c.im
    lit = 1 if state.startswith("lit") else 0
    rows = [(176, [58, 128, 198]), (122, [93, 163]), (68, [128])]
    for (cy, xs) in rows:
        for x in xs:
            cask_side_top(c, x, cy, 32)
        for x in xs:
            cask_end(c, x, cy, 32, x, lit)
    # 쐐기·받침목
    for x in (22, 236):
        face(c, x - 8, 196, x + 8, 208, R_WOOD, 0.45)
    if lit:
        r = Rand(3 + (state == "lit_1"))
        embers(c, 128, 60, 14, 26, 5 + (state == "lit_1"))
        for (x, y) in ((58, 176), (163, 122), (128, 68)):
            c.px(x + r.i(-20, 20), y - 30 - r.i(0, 6), A[25])
    return c.im


def rampart_beacon(frame):
    """성벽 회랑 봉화: 돌 받침 + 쇠 바구니 + 불(4) + 짧은 깃발."""
    W, H = 128, 240
    c = C(W, H)
    contact(c, 66, 230, 40, 9, a=120)
    plank_box(c, 30, 160, 68, 52, 20, ramp=R_STONE, seed=2, planks=2, slats=True, brace=False)
    # 바구니
    for y in range(128, 162):
        t = (y - 128) / 34
        half = 30 - t * 12
        for x in range(int(64 - half), int(64 + half) + 1):
            if (x + y) % 6 < 2 or y in (128, 129, 161):
                c.px(x, y, R_IRON[3] if y < 140 else R_IRON[2])
    flame(c, 64, 134, 46, 70 + [0, 6, 2, -4][frame % 4], seed=frame * 3 + 1, tongues=5)
    embers(c, 64, 70, 8, 18, frame + 2)
    # 깃대 + 깃발(층 램프 천)
    c.vline(104, 70, 170, R_WOOD[2]); c.vline(105, 70, 170, R_WOOD[0])
    wave = [0, 2, 0, -2][frame % 4]
    for y in range(72, 100):
        for x in range(106, 124):
            yy = y + int(wave * math.sin((x - 106) / 6))
            c.px(x, yy, qcol([WD[1], A[17], A[18], A[19]], 0.6 - (x - 106) / 40, x, yy))
    return c.im


def still(state, frame):
    """증류소 증류기(무대 중심·위험물): 벽돌 화덕 + 구리 솥(양파꼴) + 백조 목 관 + 냉각 통.
    states: idle(불 4) · warn(쉬익 — 밸브 김·솥 달아오름 4) · vent(증기 분출 6, 3초 루프) · broken(찌그러진 솥·끊긴 관·연기 1)."""
    W, H = 288, 320
    c = C(W, H)
    cx = 120
    contact(c, 150, 300, 132, 16, a=130)
    # 냉각 통(오른쪽)
    cyl(c, 226, 196, 286, 34, R_WOOD, ry=14, staves=7, seed=4, hoops=((206, 3), (240, 3), (274, 3)), bulge=0.06)
    # 화덕(벽돌)
    for y in range(206, 296):
        for x in range(cx - 70, cx + 71):
            row = (y - 206) // 8
            off = 8 if row % 2 else 0
            jx = (x + off - (cx - 70)) % 16
            s = 0.55 - 0.25 * (x - cx) / 70 - 0.15 * (y - 206) / 90
            col = R_BRICK[1] if (jx == 0 or (y - 206) % 8 == 7) else qcol(R_BRICK, s, x, y)
            c.px(x, y, col)
    c.hline(cx - 70, cx + 70, 206, R_BRICK[5])
    # 아궁이(발광 불)
    for y in range(248, 292):
        for x in range(cx - 26, cx + 27):
            d = ((x - cx) / 26) ** 2 + ((y - 292) / 44) ** 2
            if d <= 1:
                c.px(x, y, SL[0] if d > 0.82 else WD[0])
    if state != "broken":
        flame(c, cx, 290, 40, 32 + [0, 4, 2, -2, 5, 1][frame % 6], seed=frame + 3, tongues=4)
    else:
        for k in range(8):
            c.px(cx - 16 + k * 4, 286 - (k % 3), A[19])
    # 구리 솥(양파꼴)
    hot = state in ("warn", "vent")
    pot = ell_mask(W, H, (cx - 72, 112, cx + 72, 212))
    dpot = ImageDraw.Draw(pot)
    dpot.polygon([(cx - 58, 140), (cx - 14, 84), (cx + 14, 84), (cx + 58, 140)], fill=255)
    dpot.ellipse((cx - 22, 76, cx + 22, 100), fill=255)
    ramp = [A[16], A[17], A[18], A[19], A[20], A[21], A[22]] if not hot else [A[17], A[18], A[19], A[20], A[21], A[22], A[23]]
    shade_mask(c, pot, ramp, base=0.5, gain=0.7, soft=6, tilt=0.1)
    if state == "broken":
        for (x, y, r_) in ((cx - 30, 150, 14), (cx + 22, 172, 10)):
            dm = ell_mask(W, H, (x - r_, y - r_ * 0.7, x + r_, y + r_ * 0.7))
            shade_mask(c, dm, [A[16], A[17], A[18], A[19]], base=0.3, gain=0.8, soft=3, rim=False)
    # 리벳 줄
    for y in (120, 160, 196):
        for k in range(-5, 6):
            x = cx + int(k * 11 * (1.0 if y > 140 else 0.7))
            c.px(x, y, ramp[-1]); c.px(x + 1, y + 1, ramp[1])
    # 목 + 백조 관
    for y in range(64, 96):
        for x in range(cx - 12, cx + 13):
            c.px(x, y, qcol(ramp, 0.6 - (x - cx) / 30, x, y))
    if state != "broken":
        prev = None
        for i in range(120):
            t = i / 119
            x = cx + 10 + (226 - cx - 10) * t
            y = 70 - 40 * math.sin(t * math.pi * 0.8) + 130 * t ** 2.2
            for k in range(-4, 5):
                c.px(int(x), int(y) + k, qcol(ramp, 0.65 - k / 9, int(x), int(y) + k))
    else:
        for i in range(40):
            x, y = cx + 10 + i * 1.2, 70 - 30 * math.sin(i / 40 * 1.4)
            for k in range(-4, 5):
                c.px(int(x), int(y) + k, qcol(ramp, 0.55 - k / 9, int(x), int(y) + k))
    # 밸브(빨간 손잡이 대신 쇠 바퀴)
    for a in range(24):
        th = a / 24 * 6.283
        c.px(int(cx + 36 + math.cos(th) * 7), int(96 + math.sin(th) * 4), R_IRON[4])
    # 상태 연출
    r = Rand(frame * 7 + 1)
    if state == "warn":
        for k in range(10 + frame * 3):
            x, y = cx + 36 + r.i(-6, 12), 92 - r.i(0, 26 + frame * 4)
            c.px(x, y, R_STEAM[r.i(1, 4)])
        if frame % 2 == 0:
            for y in range(110, 200, 3):
                c.px(cx - 50 + r.i(0, 100), y, A[23])
    if state == "vent":
        h_ = 120 + 30 * (frame % 3)
        for y in range(96 - h_, 96):
            t = (96 - y) / h_
            half = 6 + 26 * t
            for x in range(int(cx + 36 - half), int(cx + 36 + half) + 1):
                d = abs(x - (cx + 36)) / max(1, half)
                if r.f() < 0.9 - 0.5 * d - 0.3 * t:
                    c.px(x, y, qcol(R_STEAM, 0.85 - d * 0.6 - t * 0.2, x, y, 2.5))
    if state == "broken":
        for k in range(60):
            x, y = cx + r.i(-40, 40), 60 - r.i(0, 60)
            c.px(x, y, [SL[3], SL[4], G[7]][k % 3])
    return c.im


# ================================================================ 위험물
def cask_row(state):
    """술통 줄(세운 통 3, 호박 띠): idle / hit / lit_0 / lit_1 / wreck. 터짐 자체는 fx(react_explode_*)."""
    W, H = 224, 176
    c = C(W, H)
    contact(c, 114, 158, 100, 12, a=120)
    if state == "wreck":
        r = Rand(5)
        splash(c, 112, 150, 84, 14, seed=6, blobs=6)
        for k in range(14):
            x, y = 30 + r.i(0, 160), 128 + r.i(0, 34)
            for t in range(r.i(10, 20)):
                c.px(x + t, y + int(t * 0.3 * (1 if k % 2 else -1)), R_WOOD[2 + t % 2])
        for (x, y) in ((56, 150), (114, 146), (172, 152)):
            for k in range(30):
                a = k / 30 * 6.283
                c.px(int(x + math.cos(a) * 18), int(y + math.sin(a) * 7), R_IRON[3])
        for k in range(30):
            c.px(30 + r.i(0, 160), 130 + r.i(0, 32), [WD[0], SL[1]][k % 2])
        return c.im
    dx = {"hit": 3}.get(state, 0)
    lit = 1 if state.startswith("lit") else 0
    for i, x in enumerate((56, 114, 172)):
        xx = x + (dx if i == 1 else 0)
        cyl(c, xx, 64, 140, 28, R_WOOD, ry=12, staves=7, seed=i + 3, hoops=((72, 3), (132, 3)), bulge=0.1)
        # 호박 띠(가운데 굵은 띠 6 도트)
        for X in range(xx - 31, xx + 32):
            u = (X - xx) / 30.8
            if abs(u) > 1:
                continue
            yy = 100 + int(12 * math.sqrt(1 - u * u) * 0.9)
            for k in range(6):
                colr = BAND[3] if lit and k in (1, 2, 3) else BAND[min(3, 1 + (k < 3)) if not lit else 2]
                c.px(X, yy + k, colr if not (k == 0) else BAND[0])
        # 마개 + 도화선(불붙은 상태 = 불티)
        c.rect(xx - 3, 58, xx + 2, 62, WD[1])
        if lit:
            embers(c, xx + 2, 54, 6, 6, i + (state == "lit_1") * 9)
            c.px(xx, 54 - (state == "lit_1") * 2, A[26])
    if state == "hit":
        for k in range(6):
            c.px(114 + 30 + k, 80 + k * 3, PL[4])
    return c.im


def pool(state, frame):
    """술 웅덩이(바닥 깊이): idle 반짝임 4 · ignited 불 4 · scorched 1. 지름 약 3칸 × 1.6칸."""
    W, H = 224, 128
    c = C(W, H)
    cx, cy = 112, 64
    if state == "scorched":
        r = Rand(4)
        for y in range(cy - 34, cy + 35):
            for x in range(cx - 100, cx + 101):
                d = ((x - cx) / 100) ** 2 + ((y - cy) / 34) ** 2
                if d <= 1 and r.f() < 1.1 - d:
                    c.px(x, y, [SL[0], WD[0], SL[1]][(x * 3 + y) % 3])
        return c.im
    m = ell_mask(W, H, (cx - 96, cy - 30, cx + 96, cy + 30))
    d_ = m.copy()
    dr = ImageDraw.Draw(d_)
    r = Rand(17)
    for _ in range(6):
        bx, by = cx + r.i(-90, 90), cy + r.i(-26, 26)
        br = r.i(12, 26)
        dr.ellipse((bx - br, by - br * 0.45, bx + br, by + br * 0.45), fill=255)
    mp = d_.load()
    for y in range(H):
        for x in range(W):
            if mp[x, y] > 127:
                up = y > 0 and mp[x, y - 1] <= 127
                dn = y + 1 < H and mp[x, y + 1] <= 127
                rr_ = math.hypot((x - cx) / 96, (y - cy) / 30)
                s_ = 0.36 + 0.1 * (y - cy) / 30 + 0.05 * math.sin((rr_ * 3 - frame / 4) * 6.283)
                col = R_LIQ[0] if up else (R_LIQ[3] if dn else qcol(R_LIQ, s_, x, y, 4))
                c.px(x, y, col)
    if state == "idle":
        rr = Rand(30 + frame)
        for _ in range(8):
            x, y = cx + rr.i(-80, 80), cy + rr.i(-20, 20)
            if mp[x, y] > 127:
                c.px(x, y, A[24]); c.px(x + 1, y, A[23]); c.px(x, y - 1, A[22])
    else:
        for k in range(9):
            fx = cx - 84 + k * 21 + (frame % 2) * 4
            fy = cy + int(10 * math.sin(k * 1.7))
            if mp[min(W - 1, fx), min(H - 1, fy)] > 127:
                flame(c, fx, fy + 6, 18, 26 + ((k + frame) % 3) * 6, seed=k * 5 + frame, tongues=3)
    return c.im


def merlon(state):
    """흉벽(성벽 이빨): whole / cracked / broken(무너진 잔해). 쳐서 날린 적이 부딪치면 금 → 무너짐."""
    W, H = 128, 144
    c = C(W, H)
    contact(c, 66, 132, 46, 9, a=120)
    if state == "broken":
        r = Rand(3)
        for k in range(9):
            stone_blob(c, 64 + r.i(-36, 36), 120 + r.i(-10, 8), r.i(6, 13), r.i(4, 8), R_STONE, 40 + k)
        return c.im
    face(c, 24, 46, 104, 60, R_STONE, 0.88, grad=0.1)          # 윗면
    c.hline(24, 104, 46, R_STONE[6])
    face(c, 24, 61, 104, 128, R_STONE, 0.66, grad=0.25)         # 앞면
    c.hline(24, 104, 61, R_STONE[5]); c.hline(24, 104, 128, R_STONE[0])
    c.vline(24, 46, 128, R_STONE[4]); c.vline(104, 46, 128, R_STONE[0])
    for y in (84, 106):
        c.hline(25, 103, y, R_STONE[1])
    for x, y0, y1 in ((60, 61, 84), (44, 84, 106), (84, 84, 106), (64, 106, 128)):
        c.vline(x, y0, y1, R_STONE[1])
    if state == "cracked":
        r = Rand(9)
        x, y = 70, 64
        for k in range(46):
            x += r.i(-1, 1); y += 1
            c.px(x, y, SL[0]); c.px(x + 1, y, R_STONE[5])
            if k in (14, 30):
                bx, by = x, y
                for j in range(14):
                    bx += 1 if k == 14 else -1; by += r.i(0, 1)
                    c.px(bx, by, SL[0])
        stone_blob(c, 98, 118, 7, 5, R_STONE, 77)
    return c.im


# ================================================================ 시트
def build(dry=False):
    b2.DRY = dry
    prev = []

    def sheet(name, frames, fw, fh, meta, durations=None, loop=False):
        b2.write_sheet("structures", name, frames, fw, fh, dict(meta, source=SRC, version="v3-p19", pixelScale=0.5),
                       durations=durations, loop=loop)
        prev.extend([(f, (meta["pivot"]["x"], meta["pivot"]["y"])) for f in frames[:3]])

    E = EMISSIVE_HEX
    fr = [fountain(i) for i in range(6)]
    sheet("stage_fountain", fr, 256, 256, {
        "id": "stage_fountain", "role": "stage_center", "shape": "plaza", "pivot": {"x": 128, "y": 238}, "footprint": [3, 2],
        "solid": True, "depth": "y", "occludeAbove": 70, "states": {"idle": [0, 1, 2, 3, 4, 5]}, "stateLoop": {"idle": True},
        "lights": [{"color": "#e8b858", "radius": 120, "intensity": 0.5, "offset": {"x": 50, "y": 200}},
                   {"color": "#e8b858", "radius": 120, "intensity": 0.5, "offset": {"x": 206, "y": 200}},
                   {"color": "#eecc78", "radius": 480, "intensity": 0.45, "offset": {"x": 128, "y": 150}, "flicker": {"amp": 0.05, "hz": 2}}],
        "emissiveColors": E, "hazardRing": {"kind": "pool", "radiusTiles": 2.6, "note": "둘레 술 웅덩이(hazard_pool) 2~3개를 반경 2.6칸 바깥에 두는 것을 제안"},
        "note": "원형 광장 무대 중심 — 석회 수반에 술이 고이고, 잔 받침에서 네 줄기가 흘러내림(6 프레임 루프 130ms). 앞 테 두 등(발광)",
    }, durations=[130] * 6, loop=True)
    fr = [dock_crane(i) for i in range(4)]
    sheet("stage_dock_crane", fr, 224, 320, {
        "id": "stage_dock_crane", "role": "stage_center", "shape": "dock", "pivot": {"x": 70, "y": 300}, "footprint": [2, 2], "solid": True,
        "solidRects": [{"x": 0, "y": 0, "w": 2, "h": 1}], "depth": "y", "occludeAbove": 60, "states": {"idle": [0, 1, 2, 3]},
        "stateLoop": {"idle": True}, "hangAnchor": [{"x": 197, "y": 228}, {"x": 200, "y": 228}, {"x": 197, "y": 228}, {"x": 194, "y": 228}],
        "note": "부두 하역장 무대 중심 — 돌 받침 나무 기중기, 팔 끝 매단 술통이 흔들림(4×220ms). 팔은 수로 쪽(오른쪽)으로 뻗게 — 좌우 뒤집기 허용. "
                "매단 술통은 장식(판정 없음). 제안: 쳐서 줄을 끊으면 술통이 떨어져 술통 폭발(시스템 선택)",
    }, durations=[220] * 4, loop=True)
    fr = [signpost(i) for i in range(4)]
    sheet("stage_signpost", fr, 128, 224, {
        "id": "stage_signpost", "role": "stage_center", "shape": "crossroads", "pivot": {"x": 64, "y": 212}, "footprint": [1, 1], "solid": True,
        "depth": "y", "occludeAbove": 40, "states": {"idle": [0, 1, 2, 3]}, "stateLoop": {"idle": True},
        "light": {"color": "#e8b858", "radius": 360, "intensity": 0.55, "flicker": {"amp": 0.06, "hz": 4}, "offset": {"x": 96, "y": 56}},
        "emissiveColors": E, "note": "십자로 무대 중심 — 방향 판 4장 + 매단 등(흔들림 4×200ms)",
    }, durations=[200] * 4, loop=True)
    fr = [terrace_stair(0)]
    sheet("stage_terrace_stair", fr, 288, 208, {
        "id": "stage_terrace_stair", "role": "stage_center", "shape": "terrace", "pivot": {"x": 144, "y": 198}, "footprint": [4, 1],
        "solid": False, "solidRects": [{"x": 0, "y": 0, "w": 1, "h": 1}, {"x": 3, "y": 0, "w": 1, "h": 1}], "depth": "y", "occludeAbove": 40,
        "states": {"idle": [0]},
        "lights": [{"color": "#e8b858", "radius": 260, "intensity": 0.5, "offset": {"x": 22, "y": 82}},
                   {"color": "#e8b858", "radius": 260, "intensity": 0.5, "offset": {"x": 266, "y": 82}}],
        "emissiveColors": E, "placement": "계단(/) 줄 가운데 아래 칸에 피벗 — 양 끝 기둥 2칸만 막힘(가운데 2칸 = 계단 통로). 계단 폭이 2칸이면 좌우 뒤집기 없이 그대로(기둥이 계단 양옆 칸)",
        "note": "두 단 테라스 무대 중심 — 계단 양옆 돌 난간 기둥 + 등. 계단 디딤은 타일 v4 terrace.stairS",
    })
    pile = [cask_pile(s) for s in ("idle", "lit_0", "lit_1", "wreck")]
    sheet("stage_cask_pile", pile, 256, 224, {
        "id": "stage_cask_pile", "role": "stage_center+hazard", "shape": "cellar", "pivot": {"x": 128, "y": 210}, "footprint": [3, 2],
        "solid": True, "depth": "y", "occludeAbove": 60, "states": {"idle": [0], "lit": [1, 2], "wreck": [3]},
        "stateLoop": {"idle": False, "lit": True, "wreck": False},
        "lightByState": {"lit": {"color": "#e2a33c", "radius": 200, "intensity": 0.6, "flicker": {"amp": 0.3, "hz": 9}, "offset": {"x": 128, "y": 100}}},
        "hazard": {"kind": "cask", "explode": "react_explode_l", "chainRadiusTiles": 2.5, "litMs": 500,
                   "note": "술창고 무대 중심 겸 큰 위험물 — 타격 2회 또는 불 → lit(0.5초) → 큰 폭발(react_explode_l) → wreck. 반경 2.5칸 안 술통 줄·웅덩이로 연쇄(0.3초 간격)"},
        "amberBand": "마구리 테 안쪽 호박 띠 = 위험물 표지", "emissiveColors": E,
    }, durations=[200, 90, 90, 200])
    fr = [rampart_beacon(i) for i in range(4)]
    sheet("stage_rampart_beacon", fr, 128, 240, {
        "id": "stage_rampart_beacon", "role": "stage_center", "shape": "rampart", "pivot": {"x": 64, "y": 226}, "footprint": [1, 1], "solid": True,
        "depth": "y", "occludeAbove": 50, "states": {"idle": [0, 1, 2, 3]}, "stateLoop": {"idle": True},
        "light": {"color": "#eebb6d", "radius": 420, "intensity": 0.6, "flicker": {"amp": 0.16, "hz": 6}, "offset": {"x": 64, "y": 100}},
        "emissiveColors": E, "note": "성벽 위 회랑 무대 중심 — 망루 돌출부의 봉화(불 4×120ms) + 짧은 깃발",
    }, durations=[120] * 4, loop=True)
    sf = [still("idle", i) for i in range(4)] + [still("warn", i) for i in range(4)] + [still("vent", i) for i in range(6)] + [still("broken", 0)]
    sheet("stage_still", sf, 288, 320, {
        "id": "stage_still", "role": "stage_center+hazard", "shape": "distillery", "pivot": {"x": 150, "y": 300}, "footprint": [3, 2],
        "solid": True, "depth": "y", "occludeAbove": 90,
        "states": {"idle": [0, 1, 2, 3], "warn": [4, 5, 6, 7], "vent": [8, 9, 10, 11, 12, 13], "broken": [14]},
        "stateLoop": {"idle": True, "warn": True, "vent": True, "broken": False},
        "lightByState": {"idle": {"color": "#eecc78", "radius": 420, "intensity": 0.6, "flicker": {"amp": 0.18, "hz": 7}, "offset": {"x": 120, "y": 270}},
                         "warn": {"color": "#e2a33c", "radius": 460, "intensity": 0.75, "flicker": {"amp": 0.3, "hz": 10}, "offset": {"x": 120, "y": 200}},
                         "vent": {"color": "#eecc78", "radius": 420, "intensity": 0.6, "offset": {"x": 120, "y": 270}}},
        "ventAnchor": {"x": 156, "y": 96}, "ventNote": "증기 기둥 시작점(밸브). vent 동안 이 점 위로 1.5칸 폭 기둥 = 피해 판정(시스템)",
        "hazard": {"kind": "still", "warnMs": 600, "ventMs": 3000, "explode": "react_explode_m",
                   "note": "쳐서 warn(0.6초 쉬익) → vent(증기 3초) — P19 표 형태 7. 불이 닿거나 연쇄 폭발에 휘말리면 react_explode_m 후 broken"},
        "emissiveColors": E, "note": "증류소 마당 무대 중심(섬) — 벽돌 화덕·구리 솥·백조 목 관·냉각 통. 기존 structures/v3/still(1칸 화로)과 별개",
    }, durations=[110] * 4 + [80] * 4 + [90] * 6 + [200], loop=False)
    cr = [cask_row(s) for s in ("idle", "hit", "lit_0", "lit_1", "wreck")]
    sheet("hazard_cask_row", cr, 224, 176, {
        "id": "hazard_cask_row", "role": "hazard", "pivot": {"x": 112, "y": 158}, "footprint": [3, 1], "solid": True, "depth": "y",
        "occludeAbove": 40, "states": {"idle": [0], "hit": [1], "lit": [2, 3], "wreck": [4]},
        "stateLoop": {"idle": False, "hit": False, "lit": True, "wreck": False},
        "lightByState": {"idle": {"color": "#e2a33c", "radius": 140, "intensity": 0.4, "flicker": {"amp": 0.1, "hz": 3}, "offset": {"x": 112, "y": 104}},
                         "lit": {"color": "#e2a33c", "radius": 200, "intensity": 0.7, "flicker": {"amp": 0.3, "hz": 9}, "offset": {"x": 112, "y": 70}}},
        "hazard": {"kind": "cask", "hitsToIgnite": 2, "litMs": 300, "explode": "react_explode_m", "chainRadiusTiles": 2.0,
                   "note": "P19 B7: 타격 2회 또는 불 → lit(0.3초) → 폭발(반경 2칸) → wreck(널·쇠테·고인 술 → hazard_pool 을 남김). 이웃 술통으로 0.3초 간격 연쇄"},
        "amberBand": "통마다 굵은 호박 띠 6 도트 — 어둠에서도 '터지는 것'으로 읽힘(P19 F)", "emissiveColors": E,
    }, durations=[200, 80, 90, 90, 200])
    pl = [pool("idle", i) for i in range(4)] + [pool("ignited", i) for i in range(4)] + [pool("scorched", 0)]
    sheet("hazard_pool", pl, 224, 128, {
        "id": "hazard_pool", "role": "hazard", "pivot": {"x": 112, "y": 64}, "footprint": [3, 2], "solid": False, "depth": "floor",
        "states": {"idle": [0, 1, 2, 3], "ignited": [4, 5, 6, 7], "scorched": [8]},
        "stateLoop": {"idle": True, "ignited": True, "scorched": False},
        "lightByState": {"ignited": {"color": "#eebb6d", "radius": 300, "intensity": 0.75, "flicker": {"amp": 0.25, "hz": 8}, "offset": {"x": 112, "y": 60}}},
        "hazard": {"kind": "pool", "radiusTiles": [1.5, 0.95], "igniteBy": ["fire", "explosion", "fire_bottle"], "burnMs": 4000,
                   "note": "P19 C: 행상이 만든 웅덩이와 같은 규칙 — 주인공도 불로 점화. idle 반짝임(점 4개 위치가 프레임마다 바뀜)이 위험물 표지"},
        "emissiveColors": E, "note": "바닥 깊이(데칼 위·캐릭터 아래). 기존 fx/v3/pool_liquor 와 같은 뜻의 '배치형' 웅덩이",
    }, durations=[180] * 4 + [110] * 4 + [200], loop=False)
    mr = [merlon(s) for s in ("whole", "cracked", "broken")]
    sheet("hazard_merlon", mr, 128, 144, {
        "id": "hazard_merlon", "role": "hazard", "pivot": {"x": 64, "y": 130}, "footprint": [1, 1], "solid": True, "depth": "y",
        "occludeAbove": 30, "states": {"whole": [0], "cracked": [1], "broken": [2]},
        "solidByState": {"whole": True, "cracked": True, "broken": False}, "blocksProjectiles": True,
        "hazard": {"kind": "merlon", "breakOn": "ENEMY_WALL_SLAM(surface prop) 2회 또는 강 넉백 1회", "afterBreak": "통과·낙하 가능(난간 끊김)",
                   "note": "성벽 회랑 가장자리 흉벽 — 금 → 무너짐. 무너진 자리는 낭떠러지로 밀어 떨어뜨릴 수 있는 틈"},
    }, durations=[200, 200, 200])
    b2.preview(os.path.join(HERE, "preview_props19.png"), prev, k=2, max_w=2400)
    return b2.WRITTEN


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    w = build(dry)
    if not dry:
        for cat, name, src, pages in b2.to_atlas():
            print(f"{cat}/v3/{name}: 격자 {src[0]}x{src[1]} -> 아틀라스 " + ", ".join(f"{a}x{b}" for a, b in pages))
