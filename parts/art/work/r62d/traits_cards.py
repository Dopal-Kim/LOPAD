"""62 루프 4 (P18 §1) '떠올릴 개성' 카드 그림 8장 — ui_traits/<weapon>_<id>.png 128×128 (pixelScale 0.5 · 화면 64px).

규격(계약 §27 · 스토리 팩 64 md §1.3): 투명 배경, 그 개성의 '한 순간' 장면, 키캡·숫자·글자 없음, 테두리는 UI.
결: 기존 카드와 같은 쿼터뷰 돌판 + 장면 한 점(r62b cards.py 의 돌판·빛무리·셰이딩 도구를 그대로 import).
무기 색(§28)이 주인공 — 칼 서리 · 대검 용암 · 단검 독 · 활 비취. 불·술은 1층 호박(보조).
Gemini 402(크레디트 소진) → Claude 직접 도트.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "r62b"))
import common as rc  # noqa: E402
import cards as RC  # noqa: E402  (base·finish — 돌판·빛무리·바깥 외곽)
from kit2 import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_IRON, R_CLOTH, R_LIQ, R_LEATHER, R_INKB, R_SKIN,  # noqa: E402
                  contact, flame, ell, pol, cap, line, sparks, splash, smoke)
from PIL import Image  # noqa: E402

N = 128
SRC = "parts/art/work/r62d/build.py --only traits (62 루프 4 · P18 §1) · traits_cards.py"


def c4(c):
    return tuple(c[:3]) + (255,)


FR = [c4(c) for c in rc.FROST]
LV = [c4(c) for c in rc.LAVA]
PO = [c4(c) for c in rc.POISON]
JD = [c4(c) for c in rc.JADE]
X0 = (255, 255, 255, 255)
HERO = [G[1], G[2], G[3], G[4], G[5], G[6]]                    # 주인공 숯빛 몸(먹 실루엣)
FOE = [SL[0], WD[1], WD[2], WD[3], WD[4], WD[5]]              # 적 갈색 옷
STEEL = [SL[0], G[4], G[6], G[8], G[10], G[12]]
PX = lambda c, x, y, col: c.px(int(round(x)), int(round(y)), col)  # noqa: E731


def seg(c, a, b, col, w=1):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 1.5) + 1
    for i in range(n + 1):
        t = i / n
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        for dx in range(w):
            for dy in range(w):
                PX(c, x + dx - w // 2, y + dy - w // 2, col)


def blade(c, base, tip, w, ramp, edge=None, back=None, soft=1):
    """날: 밑동(base)에서 끝(tip)으로 좁아지는 쐐기. edge = 날선 색(아래·오른쪽 가장자리), back = 등 테."""
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    pts = [(base[0] + nx * w, base[1] + ny * w), (tip[0] + nx * 0.6, tip[1] + ny * 0.6), tip, (base[0] - nx * w, base[1] - ny * w)]
    pol(c, pts, ramp, base=0.6, gain=0.8, soft=soft)
    if edge:
        seg(c, (base[0] - nx * (w - 0.5), base[1] - ny * (w - 0.5)), tip, edge)
    if back:
        seg(c, (base[0] + nx * (w - 0.5), base[1] + ny * (w - 0.5)), (tip[0] + nx * 0.5, tip[1] + ny * 0.5), back)


def glowline(c, a, b, ramp, w=2, core=None):
    """무기 색 빛줄(가운데 굵고 양끝 가늘게) — ramp 는 바깥→안."""
    n = int(math.hypot(b[0] - a[0], b[1] - a[1]) * 1.5) + 1
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    for i in range(n + 1):
        t = i / n
        x, y = a[0] + dx * t, a[1] + dy * t
        hw = w * math.sin(math.pi * t) ** 0.6
        for k, col in enumerate(ramp):
            r_ = hw * (1 - k / len(ramp))
            for s in (-1, 1):
                for q in range(int(r_ + 0.5) + 1):
                    if q <= r_:
                        PX(c, x + nx * q * s, y + ny * q * s, col)
        if core and 0.25 < t < 0.75:
            PX(c, x, y, core)


def star4(c, x, y, r, mid, edge, core=X0):
    for k in range(1, r + 1):
        col = mid if k < r * 0.5 else edge
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            PX(c, x + dx * k, y + dy * k, col)
    for k in range(1, r // 2 + 1):
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            PX(c, x + dx * k, y + dy * k, edge)
    PX(c, x, y, core)


def drops(c, pts, ramp=R_LIQ, glint=None):
    for i, (x, y, r_) in enumerate(pts):
        for yy in range(-r_, r_ + 1):
            for xx in range(-r_, r_ + 1):
                if xx * xx + yy * yy <= r_ * r_ + 0.4:
                    PX(c, x + xx, y + yy, ramp[3] if (xx < 0 or yy < 0) else ramp[1])
        PX(c, x - (r_ > 0), y - (r_ > 0), glint if (glint and i % 3 == 0) else ramp[4])


def arrow(c, tail, head, fl=JD, shaft=R_WOOD, tipc=STEEL, broken=False):
    seg(c, tail, head, shaft[3])
    dx, dy = head[0] - tail[0], head[1] - tail[1]
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    seg(c, (tail[0] + nx * 0.7, tail[1] + ny * 0.7), (head[0] + nx * 0.7, head[1] + ny * 0.7), shaft[2])
    if fl:
        for k in range(6):
            for s in (-1, 1):
                PX(c, tail[0] + ux * (k + 1) + nx * s * (1 + k * 0.45), tail[1] + uy * (k + 1) + ny * s * (1 + k * 0.45),
                   fl[4] if s < 0 else fl[3])
                PX(c, tail[0] + ux * (k + 2) + nx * s * (k * 0.45), tail[1] + uy * (k + 2) + ny * s * (k * 0.45), fl[5] if s < 0 else fl[2])
    if not broken:
        for k in range(5):
            w = (5 - k) * 0.5
            for q in (-1, 0, 1):
                PX(c, head[0] + ux * k + nx * q * w, head[1] + uy * k + ny * q * w, tipc[4] if q < 0 else tipc[2])
        PX(c, head[0] + ux * 5, head[1] + uy * 5, tipc[5])


def figure(c, hip, lean=0.0, knees=None, feet=None, hands=None, ramp=None, cracks=True, hood=True, back_arm_first=True):
    """사람 실루엣(주인공 먹빛 기본): 기운 몸통(허리 좁고 어깨 넓은 사다리꼴) + 어깨받이 + 두건 머리 + 관절 둘 다리·팔.
    hip = 골반 점, lean = 몸통 기울기(도, + 오른쪽으로), knees/feet = [(x,y)]*2, hands = [(팔꿈치, 손)]*2."""
    ramp = ramp or HERO
    a = math.radians(lean)
    up = (math.sin(a), -math.cos(a))
    rt = (math.cos(a), math.sin(a))
    sh = (hip[0] + up[0] * 24, hip[1] + up[1] * 24)
    # 다리(뒤 → 앞)
    for k in (1, 0):
        kn, ft = knees[k], feet[k]
        cap(c, [hip, kn], 4.2, ramp, base=0.42 if k else 0.5, soft=2)
        cap(c, [kn, ft], 3.8, ramp, base=0.40 if k else 0.48, soft=2)
        pol(c, [(ft[0] - 4, ft[1] - 3), (ft[0] + 6, ft[1] - 2), (ft[0] + 7, ft[1] + 2), (ft[0] - 4, ft[1] + 2)], ramp, base=0.35, soft=1)
    if hands and back_arm_first:
        el, hd = hands[1]
        cap(c, [(sh[0] - rt[0] * 7, sh[1] - rt[1] * 7), el, hd], 3.3, ramp, base=0.38, soft=2)
    torso = [(hip[0] - rt[0] * 6, hip[1] - rt[1] * 6), (hip[0] + rt[0] * 6, hip[1] + rt[1] * 6),
             (sh[0] + rt[0] * 9, sh[1] + rt[1] * 9), (sh[0] - rt[0] * 9, sh[1] - rt[1] * 9)]
    pol(c, torso, ramp, base=0.48, gain=0.7, soft=3)
    # 허리띠(어두운 띠) · 앞 어깨받이
    seg(c, (hip[0] - rt[0] * 6 + up[0] * 3, hip[1] - rt[1] * 6 + up[1] * 3), (hip[0] + rt[0] * 6 + up[0] * 3, hip[1] + rt[1] * 6 + up[1] * 3),
        ramp[0], w=2)
    ps = (sh[0] + rt[0] * 7, sh[1] + rt[1] * 7 + 2)
    ell(c, (int(ps[0]) - 6, int(ps[1]) - 4, int(ps[0]) + 6, int(ps[1]) + 5), ramp, base=0.58, gain=0.8, soft=2)
    # 두건 머리(뾰족한 뒤끝) + 눈 틈
    hc = (sh[0] + up[0] * 8, sh[1] + up[1] * 8)
    ell(c, (int(hc[0]) - 6, int(hc[1]) - 7, int(hc[0]) + 6, int(hc[1]) + 6), ramp, base=0.5, soft=2)
    if hood:
        pol(c, [(hc[0] - 6, hc[1] - 2), (hc[0] - 11, hc[1] + 3), (hc[0] - 4, hc[1] + 4)], ramp, base=0.4, soft=1)
    PX(c, hc[0] + 3, hc[1] - 1, A[23])
    PX(c, hc[0] + 4, hc[1] - 1, A[21])
    if hands:
        el, hd = hands[0]
        cap(c, [(sh[0] + rt[0] * 7, sh[1] + rt[1] * 7), el, hd], 3.5, ramp, base=0.5, soft=2)
    if cracks:
        for t, d in ((0.3, -1), (0.45, 0), (0.6, -1), (0.7, 1)):
            PX(c, hip[0] + up[0] * 24 * t + rt[0] * d * 2, hip[1] + up[1] * 24 * t + rt[1] * d * 2, A[21])
        PX(c, hip[0] + up[0] * 12, hip[1] + up[1] * 12, A[23])
    return sh, hc


# ===================================================================================== 칼
def k_fireLine():
    c, h = RC.base(41, glow=FR[1:6], gx=64, gy=70, grx=54, gry=24)
    splash(c, 62, 98, 36, 9, ramp=R_LIQ, seed=3, glint=False, blobs=4)
    # 선을 따라 막 일어서는 불줄(왼쪽부터 높아짐)
    for k, x in enumerate(range(28, 104, 9)):
        hgt = 6 + k * 2.2
        flame(c, x, 98 - (k % 2), 9, int(hgt), seed=k + 3, core=False, tongues=2)
    # 서리 청백 일섬 한 줄(가로) + 아래 잔광
    glowline(c, (6, 72), (110, 66), [FR[4], FR[6], FR[7]], w=2.6, core=X0)
    seg(c, (14, 75), (96, 70), FR[3])
    for x in range(10, 100, 7):
        PX(c, x, 77 - x * 0.05, FR[5])
    # 칼끝 한 점 + 손목 실루엣(오른쪽 끝)
    blade(c, (122, 64), (100, 66), 1.8, STEEL, edge=FR[6], back=G[3])
    star4(c, 100, 66, 5, FR[7], FR[5])
    cap(c, [(116, 58), (126, 54)], 5, HERO, base=0.45, soft=2)
    ell(c, (110, 58, 120, 68), HERO, base=0.5, gain=0.7, soft=2)
    PX(c, 114, 62, A[21])
    PX(c, 115, 61, A[23])
    return RC.finish(c, h)


def k_sheathBlock():
    c, h = RC.base(42, glow=FR[1:6], gx=82, gy=44, grx=40, gry=30)
    # 칼집째 비스듬히(손잡이 왼아래 → 칼집 끝 오른위)
    cap(c, [(44, 86), (96, 36)], 4, R_INKB, base=0.55, gain=0.9, soft=1)
    seg(c, (46, 82), (94, 36), G[5])                         # 옻칠 윤기 줄
    for t in (0.12, 0.96):
        x, y = 44 + 52 * t, 86 - 50 * t
        ell(c, (int(x) - 4, int(y) - 4, int(x) + 4, int(y) + 4), [A[17], A[18], A[19], A[20], A[22]], base=0.6, soft=1)
    ell(c, (34, 88, 46, 98), [G[1], G[2], G[3], G[4], G[6]], base=0.5, soft=1)          # 코등이
    cap(c, [(28, 104), (38, 94)], 3, [G[1], G[1], G[2], G[3], G[4]], base=0.5, soft=1)  # 손잡이
    for k in range(4):
        PX(c, 30 + k * 2.4, 102 - k * 2.4, PL[2])
    cap(c, [(16, 116), (30, 100)], 6, HERO, base=0.4, soft=2)                        # 손·소매(먹)
    # 검기 고리(칼자루 둘레)
    for k in range(80):
        a = 2 * math.pi * k / 80
        x, y = 38 + 15 * math.cos(a), 96 + 6 * math.sin(a)
        if math.sin(a) > -0.2 or k % 3:
            PX(c, x, y, FR[6] if math.sin(a) > 0 else FR[4])
    for a in (40, 140, 220, 320):
        r_ = math.radians(a)
        PX(c, 38 + 15 * math.cos(r_), 95 + 6 * math.sin(r_), FR[7])
    # 칼집 끝에서 부러져 튕기는 화살 + 쇳불꽃
    star4(c, 98, 34, 8, FR[7], FR[5])
    arrow(c, (124, 36), (104, 32), fl=None)                                           # 촉 쪽 반동강(튕겨 오른쪽으로)
    seg(c, (104, 33), (124, 37), WD[4])
    arrow(c, (96, 16), (118, 6), fl=[G[2], G[3], PL[1], PL[2], PL[3], PL[4]], broken=True)   # 깃 쪽 반동강(위로 돎)
    for k in range(10):
        a_ = math.radians(180 + k * 14)
        PX(c, 108 + 14 * math.cos(a_), 14 + 8 * math.sin(a_), G[6] if k % 2 else G[8])     # 도는 자국
    for x, y in ((106, 40), (110, 36), (104, 44), (112, 42), (101, 26), (92, 28)):
        PX(c, x, y, FR[6] if (x + y) % 2 else A[23])
    return RC.finish(c, h)


# ===================================================================================== 대검
def g_caskRoll():
    c, h = RC.base(43, glow=LV[1:6], gx=60, gy=64, grx=50, gry=28)
    # 바닥에 긴 술 줄(왼쪽 → 오른쪽 술통) + 줄 끝 불씨
    for k in range(60):
        t = k / 59
        x = 24 + 64 * t
        y = 100 - 8 * t + math.sin(t * 9) * 1.2
        w = 1.5 + 2.0 * t
        for q in range(-int(w), int(w) + 1):
            PX(c, x, y + q * 0.5, R_LIQ[1] if q > 0 else R_LIQ[2])
        if k % 7 == 0:
            PX(c, x, y - 1, R_LIQ[4])
    flame(c, 24, 100, 6, 7, seed=4, core=False, tongues=2)
    # 굴러가는 술통(옆으로 누움, 기울어짐)
    cx, cy = 86, 70
    pol(c, [(70, 56), (98, 50), (106, 80), (78, 88)], R_WOOD, base=0.5, gain=0.8, soft=3)
    for t in (0.2, 0.5, 0.8):
        seg(c, (70 + 28 * t, 56 - 6 * t), (78 + 28 * t, 88 - 8 * t), WD[1])
    for t in (0.08, 0.92):                                                             # 쇠테
        seg(c, (70 + 8 * t, 56 + 32 * t), (98 + 8 * t, 50 + 30 * t), G[6], w=2)
    ell(c, (96, 50, 112, 80), [WD[0], WD[2], WD[3], WD[4], WD[5]], base=0.55, soft=2)  # 마구리
    for r_ in (3, 6):
        for k in range(24):
            a = 2 * math.pi * k / 24
            PX(c, 104 + r_ * 0.5 * math.cos(a), 65 + r_ * math.sin(a), WD[2])
    # 이음새에서 새는 술
    for k in range(8):
        PX(c, 80 - k * 0.5, 88 + k, R_LIQ[3 if k < 4 else 2])
    # 속도 줄
    for y in (58, 66, 74):
        seg(c, (54, y + 4), (66, y), G[4])
    # 대검(왼쪽에서 휘두른 넓은 날) + 닿은 자리 용암 별
    blade(c, (-4, 84), (64, 62), 9, STEEL, edge=LV[5], back=G[3], soft=2)
    seg(c, (6, 80), (52, 66), G[9])
    glowline(c, (8, 92), (66, 68), [LV[3], LV[5]], w=1.6)
    star4(c, 66, 66, 9, LV[7], LV[5])
    for x, y, r_ in ((60, 52, 2), (74, 46, 1), (56, 44, 1)):
        drops(c, [(x, y, r_)])
    for x, y in ((70, 60), (62, 76), (76, 52), (58, 58)):
        PX(c, x, y, WD[4])
        PX(c, x + 1, y, WD[3])
    return RC.finish(c, h)


def g_blockCharge():
    c, h = RC.base(44, glow=LV[1:6], gx=62, gy=56, grx=46, gry=40)
    # 주인공(어깨를 앞으로 — 오른쪽으로 튀어나감) 먹 실루엣 + 호박 금
    figure(c, (46, 74), lean=28, knees=[(58, 88), (36, 86)], feet=[(66, 100), (24, 98)],
           hands=[((66, 62), (70, 74)), ((44, 56), (66, 80))])
    # 세워 든 대검(방패처럼) — 넓은 날, 양쪽 날 가장자리 용암 빛
    pol(c, [(66, 14), (82, 14), (84, 86), (64, 86)], STEEL, base=0.55, gain=0.7, soft=2)
    pol(c, [(66, 14), (74, 4), (82, 14)], STEEL, base=0.6, soft=1)
    seg(c, (74, 12), (74, 82), G[4])                                                  # 피 홈
    seg(c, (65, 14), (63, 86), LV[5])
    seg(c, (83, 14), (85, 86), LV[4])
    seg(c, (66, 6), (73, 2), LV[6])
    pol(c, [(56, 86), (92, 86), (92, 91), (56, 91)], [G[1], G[2], A[17], A[18], A[19]], base=0.5, soft=1)   # 코등이
    cap(c, [(74, 92), (74, 104)], 3, [G[1], G[2], WD[1], WD[2], WD[3]], base=0.5)
    # 막힌 화살 자국 + 부러져 박힌 화살
    for k in range(6):
        PX(c, 70 + k, 42 + k * 0.4, G[11] if k % 2 else G[9])
    arrow(c, (100, 34), (78, 44), fl=[G[2], G[3], PL[1], PL[2], PL[3], PL[4]], broken=True)
    star4(c, 76, 44, 4, LV[6], LV[4])
    # 발밑 흙먼지 — 앞으로 쏠림
    for k, (x, y, r_) in enumerate(((88, 98, 5), (98, 94, 6), (108, 96, 4), (82, 102, 4), (116, 92, 3))):
        ell(c, (x - r_, y - r_, x + r_, y + r_ - 1), [WD[1], WD[2], WD[3], PL[0], PL[1]], base=0.5, soft=2)
    for y in (88, 94):
        seg(c, (96, y), (122, y - 4), PL[1])
    return RC.finish(c, h)


# ===================================================================================== 단검
def d_pickpocket():
    c, h = RC.base(45, glow=PO[1:6], gx=64, gy=50, grx=48, gry=36)
    # 적의 들린 팔(갈색 소매) — 빈 손(손가락 펼침)
    cap(c, [(112, 116), (96, 74), (84, 50)], 5, FOE, base=0.45, soft=3)
    ell(c, (78, 46, 92, 56), [SL[0], WD[0], WD[1], WD[2], WD[3]], base=0.5, soft=1)                 # 소매 끝
    ell(c, (74, 34, 92, 52), R_SKIN, base=0.5, soft=2)
    for k, (dx, L) in enumerate(((-6, 7), (-2, 9), (2, 9), (6, 7))):
        cap(c, [(83 + dx, 38), (83 + dx * 1.5, 38 - L)], 1.6, R_SKIN, base=0.55, soft=1)
    cap(c, [(76, 46), (70, 42)], 1.8, R_SKIN, base=0.5, soft=1)
    # 공중에 뜬 창(빠져나가 돎) + 회전 호
    seg(c, (14, 30), (70, 8), WD[3], w=2)
    seg(c, (15, 29), (69, 7), WD[4])
    pol(c, [(70, 8), (82, 2), (78, 10), (72, 12)], STEEL, base=0.6, soft=1)
    for k in range(30):
        a = math.radians(200 + k * 4)
        PX(c, 46 + 30 * math.cos(a), 26 + 12 * math.sin(a), G[5] if k % 3 else G[7])
    # 손목 아래로 파고든 단검 끝(독 자주) + 먹 그림자 손
    cap(c, [(18, 104), (34, 86)], 6, [G[0], G[1], G[1], G[2], G[3]], base=0.35, soft=2)     # 먹빛 손
    blade(c, (36, 84), (70, 56), 3.2, STEEL, edge=PO[5], back=G[3])
    glowline(c, (40, 84), (72, 56), [PO[3], PO[5]], w=1.4)
    star4(c, 72, 54, 7, PO[6], PO[4])
    for x, y in ((80, 56), (66, 46), (78, 64), (62, 60)):
        PX(c, x, y, PO[5])
    return RC.finish(c, h)


def d_slipDash():
    c, h = RC.base(46, glow=PO[1:6], gx=64, gy=78, grx=54, gry=22)
    # 길게 끌린 술 자국(왼쪽 → 미끄러지는 발 → 적 발치)
    for k in range(90):
        t = k / 89
        x = 10 + 96 * t
        y = 106 - 16 * t
        w = 1.0 + 2.6 * math.sin(math.pi * min(1.0, t * 1.1)) ** 0.5
        for q in range(-int(w), int(w) + 1):
            PX(c, x, y + q * 0.5, R_LIQ[1] if q > 0 else (R_LIQ[2] if q > -2 else R_LIQ[3]))
        if k % 9 == 0:
            PX(c, x, y - 1, R_LIQ[4])
    # 낮게 미끄러지는 주인공(앞발을 뻗고 뒷무릎을 꿇은 자세)
    figure(c, (40, 84), lean=34, knees=[(54, 92), (32, 94)], feet=[(66, 96), (20, 98)],
           hands=[((54, 70), (62, 78)), ((34, 66), (22, 60))])
    for k in range(12):                                                                # 앞발 물보라
        a = math.radians(-160 + k * 12)
        r_ = 7 + (k % 3) * 3
        drops(c, [(int(70 + r_ * math.cos(a) * 0.6), int(94 + r_ * 0.6 * math.sin(a)), 1 if k % 2 else 0)], glint=PO[5])
    # 자국 끝에서 걸려 뒤로 넘어가는 적(다리가 들림)
    figure(c, (98, 70), lean=-62, knees=[(104, 60), (110, 70)], feet=[(116, 52), (120, 66)],
           hands=[((86, 54), (78, 48)), ((92, 62), (84, 70))], ramp=FOE, cracks=False, hood=False)
    for x, y in ((100, 88), (106, 84), (94, 86), (112, 86)):
        drops(c, [(x, y, 1)], glint=PO[5])
    for x, y in ((48, 102), (30, 104), (80, 96)):
        PX(c, x, y, PO[5])
    return RC.finish(c, h)


# ===================================================================================== 활
def b_bottleShot():
    c, h = RC.base(47, glow=JD[1:6], gx=64, gy=42, grx=40, gry=30)
    # 아래 어둠에 고개 든 적 그림자
    sil = [G[0], G[1], G[1], G[2], G[3]]
    pol(c, [(42, 104), (48, 82), (58, 76), (72, 76), (82, 82), (88, 104)], sil, base=0.35, soft=3)    # 어깨
    ell(c, (55, 60, 75, 80), sil, base=0.4, soft=2)                                                     # 고개 든 머리
    pol(c, [(52, 66), (64, 56), (78, 64), (74, 68), (56, 70)], sil, base=0.3, soft=1)                   # 챙 모자
    PX(c, 61, 72, A[21]); PX(c, 68, 72, A[21])
    # 공중에서 터지는 술병(불덩이) + 유리 조각 + 술방울 + 불티
    cx, cy = 66, 38
    for f_, col in ((1.0, A[19]), (0.75, A[21]), (0.5, A[23]), (0.25, A[25])):
        for lx, ly, lr in ((0, 0, 11), (8, -4, 7), (-8, -3, 7), (5, 6, 6), (-6, 6, 6), (0, -9, 6)):
            r_ = lr * f_
            for yy in range(-int(r_) - 1, int(r_) + 2):
                for xx in range(-int(r_) - 1, int(r_) + 2):
                    if xx * xx + yy * yy <= r_ * r_:
                        PX(c, cx + lx * f_ + xx, cy + ly * f_ + yy, col)
    for k in range(10):
        a = 2 * math.pi * k / 10 + 0.3
        r_ = 18 + (k % 3) * 5
        x, y = cx + r_ * math.cos(a), cy + r_ * 0.85 * math.sin(a)
        pol(c, [(x, y), (x + 3 * math.cos(a + 1), y + 3 * math.sin(a + 1)), (x + 4 * math.cos(a), y + 4 * math.sin(a))],
            [WD[1], WD[2], WD[3], WD[4], PL[3]], base=0.6, soft=0)
        PX(c, x + 1, y, PL[4])
    drops(c, [(cx - 20, cy + 22, 1), (cx + 16, cy + 24, 1), (cx - 8, cy + 30, 0), (cx + 4, cy + 34, 1), (cx + 24, cy + 14, 0),
              (cx - 26, cy + 10, 0)])
    for x, y in ((cx - 14, cy - 18), (cx + 18, cy - 16), (cx + 26, cy - 4), (cx - 28, cy - 2), (cx + 2, cy - 24)):
        PX(c, x, y, A[23] if (x + y) % 2 else A[25])
    # 꿰뚫은 화살(왼쪽에서) — 비취 깃
    arrow(c, (8, 52), (cx - 6, cy + 2))
    arrow(c, (cx + 10, cy - 3), (cx + 26, cy - 8), fl=None)
    star4(c, cx + 12, cy - 3, 5, JD[6], JD[4])
    return RC.finish(c, h)


def b_quiverShake():
    c, h = RC.base(48, glow=JD[1:6], gx=72, gy=52, grx=50, gry=34)
    # 몸을 비틀어 옆으로 빠지는 주인공(먹 실루엣) — 왼쪽으로 몸을 빼며 통을 든 팔은 위로
    figure(c, (44, 76), lean=-18, knees=[(54, 90), (34, 88)], feet=[(62, 102), (22, 100)],
           hands=[((58, 50), (62, 40)), ((28, 58), (16, 66))])
    # 거꾸로 뒤집어 터는 화살통(가죽 + 바랜 금 테)
    pol(c, [(54, 30), (64, 24), (78, 50), (68, 56)], [SL[0], WD[1], WD[2], WD[3], WD[4]], base=0.5, gain=0.8, soft=2)
    seg(c, (66, 56), (79, 50), A[20], w=2)
    seg(c, (55, 30), (64, 24), A[19])
    for k in range(3):
        seg(c, (58 + k * 3, 34 + k * 6), (67 + k * 3, 29 + k * 6), WD[1])
    # 쏟아진 화살 — 앞(오른쪽)으로 부채꼴
    for k, ang in enumerate((-30, -14, 2, 18, 34)):
        a = math.radians(ang)
        L = 30 + (k % 2) * 6
        sx, sy = 76 + 6 * math.cos(a), 54 + 6 * math.sin(a)
        arrow(c, (sx, sy), (sx + L * math.cos(a), sy + L * math.sin(a)))
    for x, y in ((80, 62), (86, 48), (74, 62), (90, 66), (70, 44)):
        PX(c, x, y, JD[4] if (x + y) % 2 else JD[5])
    return RC.finish(c, h)


# ===================================================================================== 유품 '만취의 짝짝이 신'(drunkFist) — 보스 새 도트와 같은 신
def relic_drunkFist():
    """스토리 63 팩 그림 메모 '크기도 색도 다른 신 두 짝, 한 짝은 군화' — 새 보스가 신은 그 두 짝(왼 검은 군화 · 오른 헌 슬리퍼)."""
    c, h = RC.base(15)
    contact(c, 62, 96, 30, 7)
    JK = [G[1], G[2], G[3], G[4], G[5], G[6], G[8]]
    # 검은 군화(서 있음, 무릎까지 오는 넓은 목, 버클 띠 둘, 쇠 앞코)
    pol(c, [(34, 36), (56, 34), (56, 80), (72, 84), (76, 94), (32, 94)], JK, base=0.45, gain=0.8, soft=3)
    ell(c, (32, 30, 58, 40), [G[1], G[1], G[2], G[3], G[4]], base=0.4, soft=1)                  # 목 안쪽
    for y in (52, 66):
        seg(c, (33, y), (56, y - 1), WD[1], w=2)
        PX(c, 53, y - 1, A[21]); PX(c, 54, y - 1, A[22]); PX(c, 53, y, A[19])
    pol(c, [(64, 86), (72, 84), (76, 92), (66, 93)], [G[3], G[5], G[7], G[9], G[11]], base=0.6, soft=1)  # 쇠 앞코
    seg(c, (36, 92), (74, 93), G[1], w=2)                                                       # 굽·밑창
    for k in range(4):
        PX(c, 38 + k, 42 + k * 9, G[7])                                                         # 가죽 주름
    # 헌 슬리퍼(옆으로 쓰러짐, 말린 코 + 방울, 크기 작고 갈색) + 줄무늬 양말 한 짝이 걸쳐 있음
    pol(c, [(74, 78), (98, 72), (110, 76), (108, 84), (80, 90)], R_WOOD, base=0.5, gain=0.8, soft=2)
    ell(c, (78, 74, 92, 82), [WD[0], WD[0], WD[1], WD[2], WD[3]], base=0.4, soft=1)            # 신 입구
    cap(c, [(108, 76), (114, 68)], 2.4, R_WOOD, base=0.55, soft=1)
    ell(c, (110, 61, 118, 69), [A[17], A[18], A[19], A[20], A[21]], base=0.55, soft=1)        # 방울
    for k in range(5):
        PX(c, 86 + k * 4, 86 - k * 0.6, WD[1])                                                  # 해진 바늘땀
    # 술 자국(신 사이) + 비틀대는 호박 소용돌이(취권의 흔적 — 작게)
    splash(c, 64, 98, 12, 3, ramp=R_LIQ, seed=5, glint=True, blobs=2)
    for k, (x0, y0) in enumerate(((84, 64), (100, 58))):                                       # 비틀대는 흔들림 자국(작게)
        for t in range(10):
            PX(c, x0 + t, y0 + 2 * math.sin(t * 0.9 + k), A[20] if t < 6 else A[22])
    return RC.finish(c, h)


CARDS = {
    "katana_k_mem_fireLine": (k_fireLine, "가로로 그은 서리 일섬 아래, 술 웅덩이에서 선을 따라 불줄이 일어서는 순간(칼끝·손목만)"),
    "katana_k_mem_sheathBlock": (k_sheathBlock, "칼집째 세운 칼 끝에서 부러져 튕기는 화살, 칼자루 둘레 서리 검기 고리"),
    "greatsword_g_mem_caskRoll": (g_caskRoll, "대검에 맞아 굴러가는 술통, 바닥의 긴 술 줄과 끝의 불씨, 날의 용암 빛"),
    "greatsword_g_mem_blockCharge": (g_blockCharge, "방패처럼 세운 대검(막힌 화살) 뒤에서 어깨를 내밀며 튀어나감, 앞으로 쏠린 흙먼지"),
    "dagger_d_mem_pickpocket": (d_pickpocket, "들린 빈 손목 아래로 파고든 독 자주 단검 끝, 공중에 뜬 창, 먹빛 손"),
    "dagger_d_mem_slipDash": (d_slipDash, "젖은 바닥을 낮게 미끄러지는 발과 끌린 술 자국, 걸려 넘어가는 적의 다리"),
    "bow_b_mem_bottleShot": (b_bottleShot, "공중에서 화살에 꿰여 터지는 술병, 비취 깃, 아래 고개 든 적 그림자"),
    "bow_b_mem_quiverShake": (b_quiverShake, "몸을 비틀며 뒤집어 터는 화살통, 부채꼴로 쏟아지는 화살"),
}


def build(dry=False):
    out = []
    for cid, (fn, note) in CARDS.items():
        im = fn()
        assert im.size == (N, N)
        if not dry:
            rc.save_png(im, os.path.join(rc.SPR, "ui_traits", cid + ".png"))
        out.append((cid, im, note))
    im = relic_drunkFist()
    if not dry:
        rc.save_png(im, os.path.join(rc.SPR, "ui_relics", "drunkFist.png"))
        jp = os.path.join(rc.SPR, "ui_relics", "relics.json")
        m = json.load(open(jp, encoding="utf-8"))
        m["relics"]["drunkFist"]["scene"] = "크기도 색도 다른 신 두 짝 — 검은 군화(한 짝은 만취 것이 아니다)와 방울 달린 헌 슬리퍼, 술 자국과 비틀댄 흔들림"
        m["relics"]["drunkFist"]["colors"] = len(rc.colors_of(im))
        m["relics"]["drunkFist"]["redraw62d"] = "62 루프 4 — 스토리 63 팩 그림 메모(짝짝이 신)에 맞춰 다시 그림 · 보스 새 도트의 신과 같은 두 짝"
        rc.dump(m, jp)
    out.append(("relic_drunkFist", im, "유품 짝짝이 신"))
    prev = rc.board([im for _, im, _ in out], bg=(46, 40, 36), k=3, max_w=4 * 140)
    prev.save(os.path.join(HERE, "preview_trait_cards.png"))
    return [(cid, len(rc.colors_of(im))) for cid, im, _ in out]
