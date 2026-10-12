"""62a — 탄생 전장 소품 `structures/v3/birth_*` (P0-2 회피 시험 무대 · 탄생지 방 꾸밈). 64도트 = 1칸, pixelScale 0.5, 트림 아틀라스.

회피 시험이 '회색 원통·허공' 대신 이 소품 위에서 진행되게: 엄폐(시체 더미·작은 더미·창 숲)는 solid,
분위기(피 묻은 깃발·쓰러진 병사·흩어진 창)는 통과. 빛 = 좌상단(바이블). 색 = lopad gray + 1층 램프(피·불씨) + v2 재질 SL·WD·PL — 새 색 없음.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../bundle2"))
import b2  # noqa: E402
from b2 import (Canvas, Rand, G, A, SL, WD, PL, X, R_WOOD, R_WOODG, R_IRON, R_CLOTH, R_CLOTHG, R_EARTH, R_BONE,  # noqa: E402
                contact, shade_mask, mask, poly_mask, ell_mask, splash, flame, embers, outline, EMISSIVE_HEX, CLEAR)
from b2 import tohex  # noqa: E402

SRC = "parts/art/work/r62a/birthprops.py (62라운드 루프 1 · P0-2 탄생 전장 무대)"
R_SOLDIER = [SL[0], SL[1], SL[2], SL[3], SL[4], SL[5]]               # 잔 병사(청회 군복)
R_FOE = [SL[0], SL[1], G[2], G[3], G[4], G[5], G[6]]                 # 낯선 군복(무채)
R_SKIN = [SL[0], WD[1], PL[0], PL[1], PL[2], PL[3]]                  # 죽은 살갗(잿빛)
R_HELM = [SL[0], G[2], G[3], G[5], G[7], G[9]]
R_LEATHER = [SL[0], WD[0], WD[1], WD[2], WD[3], WD[4]]
R_BLOOD = [A[16], A[17], A[18], A[17], A[16], A[19]]                 # 피 웅덩이(splash 순서: 위 가장자리·몸·아래·…·글린트)
R_MUD = [SL[0], WD[1], WD[2], PL[0], WD[1], PL[0]]
R_BANNER = [SL[0], SL[1], SL[2], SL[3], SL[4]]
R_DIRT = [SL[0], WD[0], WD[1], WD[2], PL[0], PL[1]]


# ---------------------------------------------------------------- 도구
def capsule_mask(w, h, pts, r):
    m, d = mask(w, h)
    for (a, b) in zip(pts, pts[1:]):
        d.line([a, b], fill=255, width=max(1, int(r * 2)))
    for p in pts:
        d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=255)
    return m


def capsule(c, pts, r, ramp, base=0.5, gain=0.7, soft=2, tilt=0.0):
    shade_mask(c, capsule_mask(c.w, c.h, pts, r), ramp, base=base, gain=gain, soft=soft, tilt=tilt)


def rot(p, ang, o=(0, 0), squash=0.55):
    """바닥에 누운 몸 좌표(로컬, 단위 도트) → 화면: 각도 ang 회전 + 세로 납작(쿼터뷰)."""
    x, y = p
    ca, sa = math.cos(ang), math.sin(ang)
    return (o[0] + x * ca - y * sa, o[1] + (x * sa + y * ca) * squash)


def lying_body(c, o, ang, coat, seed, helm=True, lift=0.0, arm_pose=None, leg_pose=None, squash=0.55, s=1.0):
    """엎드리거나 누운 병사. o = 골반, ang = 머리 쪽 방향(라디안). lift = 위로 올린 높이(더미 위). s = 크기 배율."""
    r = Rand(seed)
    oo = (o[0], o[1] - lift)

    def cap(c_, pts, rad, ramp, **kw):     # 반지름도 배율
        capsule(c_, pts, rad * s, ramp, **kw)

    def P(x, y):
        return rot((x * s, y * s), ang, oo, squash)
    arm_pose = arm_pose or [(r.f() * 1.6 - 0.2), -(r.f() * 1.6 - 0.2)]
    leg_pose = leg_pose or [0.25 + r.f() * 0.35, -0.2 - r.f() * 0.35]
    # 다리(뒤) — 허벅지 → 정강이 → 장화
    for k, a in enumerate(leg_pose):
        side = 1 if k == 0 else -1
        hip = P(-2, side * 4)
        knee = P(-2 - 14 * math.cos(a), side * 4 + 14 * math.sin(a) * side * 0.4)
        foot = P(-2 - 27 * math.cos(a * 0.7), side * 5 + 20 * math.sin(a) * side * 0.3)
        cap(c, [hip, knee], 4.2, coat, base=0.42)
        cap(c, [knee, foot], 3.6, coat, base=0.40)
        cap(c, [foot, P(-2 - 31 * math.cos(a * 0.7), side * 5 + 21 * math.sin(a) * side * 0.3)], 3.4, R_LEATHER, base=0.45)
    # 몸통
    cap(c, [P(-3, 0), P(15, 0)], 7.5, coat, base=0.52, gain=0.85, soft=4, tilt=0.2)
    # 허리띠
    a_, b_ = P(1, -7), P(1, 7)
    c.line(int(a_[0]), int(a_[1]), int(b_[0]), int(b_[1]), R_LEATHER[1])
    # 팔
    for k, a in enumerate(arm_pose):
        side = 1 if k == 0 else -1
        sh = P(14, side * 7)
        el = P(14 - 12 * math.cos(a), side * 7 + 12 * math.sin(abs(a)) * side)
        hd = P(14 - 22 * math.cos(a * 1.3), side * 8 + 20 * math.sin(abs(a)) * side)
        cap(c, [sh, el], 3.4, coat, base=0.5)
        cap(c, [el, hd], 3.0, coat, base=0.48)
        c.ellipse((hd[0] - 2.5 * s, hd[1] - 2 * s, hd[0] + 2.5 * s, hd[1] + 2 * s), R_SKIN[3])
        c.px(int(hd[0]) - 1, int(hd[1]) - 1, R_SKIN[4])
    # 머리 + 투구
    hc = P(24, 0)
    cap(c, [hc], 5.6, R_SKIN, base=0.45, soft=2)
    if helm:
        m = ell_mask(c.w, c.h, (hc[0] - 6.5 * s, hc[1] - 6.5 * s, hc[0] + 6.5 * s, hc[1] + 4 * s))
        shade_mask(c, m, R_HELM, base=0.55, gain=0.9, soft=2)
        c.hline(int(hc[0] - 6 * s), int(hc[0] + 6 * s), int(hc[1] + 3 * s), R_HELM[0])
        c.px(int(hc[0] - 3 * s), int(hc[1] - 4 * s), R_HELM[5])
        c.px(int(hc[0] - 3 * s) + 1, int(hc[1] - 4 * s), R_HELM[4])
    return hc


def spear_shaft(c, a, b, w=2, ramp=R_WOOD, tip=True, broken=False):
    """창대(2도트) + 창날. broken 이면 꺾인 끝(쪼개진 나무 결)."""
    ax, ay = a
    bx, by = b
    n = int(max(abs(bx - ax), abs(by - ay))) + 1
    for i in range(n):
        t = i / max(1, n - 1)
        x, y = int(round(ax + (bx - ax) * t)), int(round(ay + (by - ay) * t))
        c.px(x, y, ramp[3])
        if w > 1:
            c.px(x + 1, y, ramp[1])
        if w > 2:
            c.px(x - 1, y, ramp[4])
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    if tip and not broken:
        for k in range(9):
            wd = max(0, 2 - k // 3)
            x, y = bx + ux * k, by + uy * k
            for s in range(-wd, wd + 1):
                c.px(int(round(x - uy * s)), int(round(y + ux * s)), R_IRON[4] if s <= 0 else R_IRON[2])
        c.px(int(round(bx + ux * 8)), int(round(by + uy * 8)), R_IRON[5])
    if broken:
        for k, s in ((1, -1), (2, 1), (3, 0), (2, -2)):
            c.px(int(round(bx + ux * k - uy * s)), int(round(by + uy * k + ux * s)), ramp[4] if s <= 0 else ramp[2])


def shield(c, cx, cy, rx, ry, seed, emblem=True, ang_tilt=0.0):
    m = ell_mask(c.w, c.h, (cx - rx, cy - ry, cx + rx, cy + ry))
    shade_mask(c, m, R_WOOD, base=0.5, gain=0.8, soft=3, tilt=0.3)
    m2 = ell_mask(c.w, c.h, (cx - rx + 2, cy - ry + 2, cx + rx - 2, cy + ry - 2))
    mp = m2.load()
    # 테두리 쇠 띠
    for y in range(c.h):
        for x in range(c.w):
            if m.getpixel((x, y)) > 127 and mp[x, y] <= 127:
                c.px(x, y, R_IRON[3] if (x + y) % 5 else R_IRON[4])
    c.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), R_IRON[4])
    c.px(cx - 1, cy - 1, R_IRON[5])
    if emblem:     # 바랜 잔 문양(결사병 방패와 같은 모양)
        for dx in range(-3, 4):
            c.px(cx + dx, cy - ry // 2, A[19])
        for (dx, dy) in ((-2, 1), (2, 1), (-1, 2), (1, 2), (0, 3), (0, 4)):
            c.px(cx + dx, cy - ry // 2 + dy, A[18])


def blood(c, cx, cy, rx, ry, seed):
    splash(c, cx, cy, rx, ry, ramp=R_BLOOD, seed=seed, glint=False, blobs=4)


def arrow_stuck(c, x, y, ang, L=14):
    ux, uy = math.cos(ang), math.sin(ang)
    for k in range(L):
        c.px(int(round(x + ux * k)), int(round(y + uy * k)), R_WOOD[2] if k % 4 else R_WOOD[3])
    ex, ey = x + ux * L, y + uy * L
    for s in (-1, 1):
        for k in range(3):
            c.px(int(round(ex - ux * k - uy * s * (k + 1))), int(round(ey - uy * k + ux * s * (k + 1))), PL[3] if s < 0 else PL[1])


def ember_dots(c, pts, k):
    """꺼져 가는 불씨(자체 발광 23~25) — k 에 따라 깜빡."""
    for i, (x, y) in enumerate(pts):
        ph = (i * 3 + k) % 5
        if ph == 0:
            continue
        c.px(x, y, A[25] if ph in (1, 2) else A[23])
        if ph == 1:
            c.px(x, y - 1, A[24])


def smoke(c, x0, y0, k, seed, length=30, lean=0.4):
    """가는 연기(비발광): 아래 짙게 → 위 옅게."""
    cols = (G[5], G[4], G[3])
    for j in range(length):
        y = y0 - j * 2 - (k * 2 + seed) % 4
        x = x0 + lean * j + int(round((1.2 + j * 0.1) * math.sin(j * 0.32 + k * 1.1 + seed)))
        f = j / length
        if (j + k + seed) % 7 == 0 or (f > 0.6 and (x + y) % 2):
            continue
        c.px(int(x), int(y), cols[0] if f < 0.3 else (cols[1] if f < 0.65 else cols[2]))


def dirt_mound(c, cx, cy, rx, ry, seed, ramp=R_DIRT):
    m, d = mask(c.w, c.h)
    r = Rand(seed)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    for _ in range(7):
        bx = cx + r.i(-rx + 6, rx - 6)
        by = cy + r.i(-ry // 2, ry // 3)
        br = r.i(6, 12)
        d.ellipse((bx - br, by - br * 0.6, bx + br, by + br * 0.6), fill=255)
    shade_mask(c, m, ramp, base=0.42, gain=0.7, soft=6, tilt=0.35)
    # 박힌 돌·재
    for _ in range(18):
        x, y = cx + r.i(-rx + 4, rx - 4), cy + r.i(-ry + 3, ry - 2)
        if c.get(x, y)[3]:
            c.px(x, y, G[5] if r.f() < 0.5 else G[2])


# ---------------------------------------------------------------- 1. 시체 더미 (2×1, 엄폐)
def corpse_pile(k):
    W_, H_ = 288, 216
    c = Canvas(W_, H_)
    contact(c, 144, 184, 120, 15, a=100)
    blood(c, 196, 186, 44, 8, 11)
    blood(c, 74, 182, 24, 6, 12)
    dirt_mound(c, 144, 166, 100, 20, 13)
    spear_shaft(c, (100, 140), (78, 36), w=3)
    spear_shaft(c, (196, 138), (222, 66), w=3, broken=True)
    lying_body(c, (136, 124), math.pi * 0.04, R_FOE, 21, helm=False, arm_pose=[1.2, -0.3], leg_pose=[0.4, -0.3], s=1.85)
    lying_body(c, (94, 152), math.pi * 0.86, R_SOLDIER, 22, helm=True, arm_pose=[0.3, -1.1], leg_pose=[0.5, -0.2], s=1.85)
    lying_body(c, (184, 160), -math.pi * 0.10, R_SOLDIER, 23, helm=True, arm_pose=[-0.5, 1.4], leg_pose=[0.2, -0.45], s=1.85)
    arrow_stuck(c, 184, 148, -2.2, 18)
    arrow_stuck(c, 196, 150, -1.9, 20)
    shield(c, 130, 172, 18, 13, 24)
    m = ell_mask(W_, H_, (232, 172, 252, 186))
    shade_mask(c, m, R_HELM, base=0.55, gain=0.9, soft=2)
    c.hline(232, 252, 184, R_HELM[0])
    c.px(238, 175, R_HELM[5])
    spear_shaft(c, (34, 186), (98, 176), w=3, tip=False, broken=True)
    m = poly_mask(W_, H_, [(150, 114), (168, 112), (174, 134), (166, 150), (160, 138), (152, 146)])
    shade_mask(c, m, R_CLOTH, base=0.45, gain=0.7, soft=2)
    ember_dots(c, [(116, 138), (152, 144), (72, 160), (214, 154), (176, 130)], k)
    smoke(c, 160, 120, k, 1, length=32, lean=0.35)
    smoke(c, 112, 132, k + 2, 4, length=24, lean=0.5)
    return c.im


# ---------------------------------------------------------------- 2. 작은 더미 (1×1, 엄폐)
def corpse_mound(k):
    W_, H_ = 176, 184
    c = Canvas(W_, H_)
    contact(c, 88, 154, 66, 11, a=100)
    blood(c, 112, 156, 22, 5, 31)
    dirt_mound(c, 88, 140, 56, 15, 32)
    spear_shaft(c, (60, 124), (40, 44), w=3, broken=True)
    lying_body(c, (86, 114), math.pi * 0.08, R_FOE, 33, helm=False, arm_pose=[1.0, -0.6], leg_pose=[0.3, -0.2], s=1.75)
    lying_body(c, (98, 138), math.pi * 0.92, R_SOLDIER, 34, helm=True, arm_pose=[0.1, 1.2], leg_pose=[0.4, -0.3], s=1.75)
    shield(c, 126, 142, 14, 10, 35, emblem=True)
    ember_dots(c, [(70, 122), (108, 112), (54, 140)], k)
    smoke(c, 84, 108, k, 3, length=26, lean=0.3)
    return c.im


# ---------------------------------------------------------------- 3. 창 숲 (1×1, 엄폐)
def spear_thicket(k):
    W_, H_ = 144, 208
    c = Canvas(W_, H_)
    contact(c, 72, 194, 50, 11, a=100)
    dirt_mound(c, 72, 184, 40, 12, 41, ramp=R_MUD)
    r = Rand(42)
    spears = [((50, 186), (34, 56), False), ((62, 190), (70, 30), False), ((80, 188), (104, 60), True), ((92, 186), (120, 96), False),
              ((70, 192), (48, 110), True), ((58, 188), (24, 128), False), ((86, 190), (84, 104), True)]
    for (a, b, br) in spears:
        spear_shaft(c, a, b, w=3, broken=br)
    shield(c, 90, 178, 12, 10, 43)
    # 꽂힌 창에 걸린 투구 · 찢긴 천(펄럭 4프레임)
    m = ell_mask(W_, H_, (63, 36, 79, 48))
    shade_mask(c, m, R_HELM, base=0.55, gain=0.9, soft=2)
    c.hline(63, 79, 46, R_HELM[0])
    c.px(66, 39, R_HELM[5])
    sway = [0, 1, 2, 1, 0, -1][k % 6]
    m = poly_mask(W_, H_, [(36, 62), (48, 64), (52 + sway, 84), (46 + sway, 80), (44 + sway, 92), (38 + sway, 84), (34, 76)])
    shade_mask(c, m, R_BANNER, base=0.45, gain=0.7, soft=2)
    c.px(42 + sway, 78, A[18])
    c.px(43 + sway, 79, A[17])
    # 밑동 화살·부러진 조각
    for (x, y, a) in ((40, 182, -1.2), (98, 184, -2.0), (74, 180, -1.6)):
        arrow_stuck(c, x, y, a, 10)
    for _ in range(6):
        x, y = 40 + r.i(0, 64), 182 + r.i(0, 8)
        c.line(x, y, x + r.i(3, 7), y + r.i(-1, 1), R_WOOD[2])
    return c.im


# ---------------------------------------------------------------- 4. 피 묻은 깃발 (1×1, 통과)
def banner_bloody(k):
    W_, H_ = 144, 240
    c = Canvas(W_, H_)
    contact(c, 66, 228, 22, 6, a=100)
    blood(c, 74, 230, 14, 4, 51)
    # 기운 깃대 + 가로대
    spear_shaft(c, (64, 228), (78, 26), w=3, tip=False)
    for x in range(56, 122):
        y = 34 + (x - 56) // 12
        c.px(x, y, R_WOOD[3])
        c.px(x, y + 1, R_WOOD[1])
    # 깃발: 4프레임 펄럭(위상), 찢긴 아래 끝, 피 얼룩(번진 손자국 · 흘러내림), 바랜 잔 문양, 그을린 구멍
    ph = k * math.pi / 2
    pts_top, pts_bot = [], []
    for i in range(13):
        t = i / 12
        x = 60 + t * 58
        wv = math.sin(t * 3.2 + ph) * 5 * t
        pts_top.append((x, 36 + (x - 56) / 12 + wv))
        rag = [0, 8, 2, 12, 4, 0, 10, 3, 14, 6, 9, 2, 0][i]
        pts_bot.append((x, 118 + wv * 1.2 - rag - t * 10))
    m = poly_mask(W_, H_, pts_top + pts_bot[::-1])
    shade_mask(c, m, R_BANNER, base=0.5, gain=0.8, soft=3)
    mp = m.load()
    r = Rand(52 + k)
    # 접힌 결(세로 그늘 띠 — 펄럭 위상 따라)
    for x in range(60, 120):
        t = (x - 60) / 58
        f = math.cos(t * 3.2 + ph)
        if f < -0.55:
            for y in range(30, 130):
                if mp[x, y] > 127 and c.get(x, y)[:3] in (SL[2][:3], SL[3][:3], SL[4][:3]):
                    c.px(x, y, SL[1] if f < -0.85 else SL[2])
    # 잔 문양(바랜 호박)
    cx, cy = 86, 70 + int(math.sin(0.45 * 3.2 + ph) * 2)
    for dx in range(-6, 7):
        c.px(cx + dx, cy, A[19])
    for (dx, dy) in ((-5, 1), (5, 1), (-4, 2), (4, 2), (-3, 3), (3, 3), (-1, 4), (1, 4), (0, 5), (0, 6), (0, 7), (-3, 8), (-2, 8), (-1, 8), (0, 8), (1, 8), (2, 8), (3, 8)):
        c.px(cx + dx, cy + dy, A[18] if dy < 5 else A[19])
    # 피: 비스듬히 문지른 손 자국(긴 번짐) + 아래로 흘러내린 가는 줄
    for (bx, by, ang, ln) in ((96, 60, 0.5, 9), (72, 96, -0.4, 7), (106, 92, 0.2, 5)):
        ux, uy = math.cos(ang), math.sin(ang)
        for t in range(-ln, ln + 1):
            wd = 2.6 * (1 - abs(t) / (ln + 1)) + 0.6
            for s_ in range(-3, 4):
                if abs(s_) > wd:
                    continue
                x, y = int(round(bx + ux * t - uy * s_)), int(round(by + uy * t + ux * s_))
                if mp[x, y] > 127 and r.f() < 0.9 - abs(s_) / 4:
                    c.px(x, y, A[17] if abs(s_) > wd * 0.5 else A[18])
    for (x0, y0, L) in ((98, 63, 18), (92, 61, 9), (74, 99, 13), (107, 95, 7)):
        for j in range(L):
            if mp[x0, y0 + j] > 127 and not (j > L * 0.6 and j % 2):
                c.px(x0, y0 + j, A[17])
    # 그을린 구멍 2
    for (hx, hy, hr) in ((76, 52, 4), (112, 74, 3)):
        for y in range(hy - hr - 1, hy + hr + 2):
            for x in range(hx - hr - 1, hx + hr + 2):
                dd = math.hypot(x - hx, y - hy)
                if dd < hr:
                    c.px(x, y, CLEAR)
                elif dd < hr + 1.4 and mp[x, y] > 127:
                    c.px(x, y, SL[0] if (x + y) % 2 else WD[1])
    # 찢긴 아래 끝 불씨 한두 점
    ember_dots(c, [(int(pts_bot[3][0]), int(pts_bot[3][1]) - 1), (int(pts_bot[8][0]), int(pts_bot[8][1]) - 1)], k)
    # 깃대 밑동 돌무더기
    for (x, y) in ((58, 226), (70, 228), (64, 222)):
        m = ell_mask(W_, H_, (x - 5, y - 3, x + 5, y + 3))
        shade_mask(c, m, [SL[0], G[2], G[3], G[5], G[6]], base=0.5, gain=0.8, soft=1)
    return c.im


# ---------------------------------------------------------------- 5. 쓰러진 병사 (2×1, 통과 — 바닥 꾸밈)
def fallen_soldier(k):
    W_, H_ = 224, 128
    c = Canvas(W_, H_)
    contact(c, 104, 92, 80, 10, a=90)
    blood(c, 136, 94, 30, 7, 61)
    spear_shaft(c, (26, 92), (110, 80), w=3, broken=True)
    lying_body(c, (86, 84), math.pi * 0.03, R_SOLDIER, 62, helm=True, arm_pose=[1.3, -0.9], leg_pose=[0.35, -0.25], s=1.85)
    for (x, y, a) in ((88, 72, -2.0), (102, 74, -1.7), (80, 78, -2.3)):
        arrow_stuck(c, x, y, a, 16)
    shield(c, 178, 84, 14, 10, 63)
    return c.im


# ---------------------------------------------------------------- 6. 흩어진 창 (2×1, 바닥 꾸밈)
def broken_spears(k):
    W_, H_ = 160, 80
    c = Canvas(W_, H_)
    r = Rand(71)
    for (a, b, br) in (((16, 60), (84, 52), True), ((60, 68), (140, 56), False), ((40, 44), (98, 64), True), ((96, 70), (130, 42), True)):
        spear_shaft(c, a, b, w=2, broken=br, tip=not br)
    m = ell_mask(W_, H_, (110, 54, 124, 64))
    shade_mask(c, m, R_HELM, base=0.55, gain=0.9, soft=2)
    c.hline(110, 124, 62, R_HELM[0])
    blood(c, 70, 66, 12, 3, 72)
    for _ in range(5):
        x, y = 20 + r.i(0, 120), 50 + r.i(0, 20)
        arrow_stuck(c, x, y, -1.4 - r.f(), 7)
    return c.im


SHEETS = [
    # 이름, 함수, 틀, 피벗, 발자국, solid, 프레임 수, ms, 상태, 설명
    ("birth_corpse_pile", corpse_pile, (288, 216), (144, 188), [2, 1], True, 4, [220, 220, 220, 220],
     {"idle": [0, 1, 2, 3]}, {"idle": True}, 60,
     "시체 더미(흙 둔덕 위 엎어진 병사 3 · 꽂힌 창 2 · 방패 · 굴러떨어진 투구 · 피 웅덩이). idle 루프 = 불씨 깜빡·연기. 회피 시험 주 엄폐물(회색 원통 대체)"),
    ("birth_corpse_mound", corpse_mound, (176, 184), (88, 156), [1, 1], True, 4, [220, 220, 220, 220],
     {"idle": [0, 1, 2, 3]}, {"idle": True}, 50,
     "작은 시체 더미(병사 2 · 방패 · 부러진 창). 1칸 엄폐 — 회색 원통 자리를 그대로 바꿔 넣는 크기"),
    ("birth_spear_thicket", spear_thicket, (144, 208), (72, 196), [1, 1], True, 6, [160, 120, 120, 120, 120, 160],
     {"idle": [0, 1, 2, 3, 4, 5]}, {"idle": True}, 120,
     "창 숲(땅에 꽂힌 창 7 · 걸린 투구 · 펄럭이는 천 조각 · 밑동 화살). 1칸 엄폐 — 사이로 화살이 지나갈 것처럼 보이지만 solid(판정 단순화)"),
    ("birth_banner_bloody", banner_bloody, (144, 240), (64, 228), [1, 1], False, 4, [180, 180, 180, 180],
     {"idle": [0, 1, 2, 3]}, {"idle": True}, 170,
     "피 묻은 깃발(기운 깃대 · 찢긴 청회 깃발 · 바랜 잔 문양 · 피 손자국·흘러내림 · 그을린 구멍 2 · 끝 불씨). idle = 펄럭 루프. 통과"),
    ("birth_fallen_soldier", fallen_soldier, (224, 128), (104, 96), [2, 1], False, 1, [1000],
     {"idle": [0]}, {"idle": False}, 24,
     "쓰러진 병사(엎드림 · 등에 화살 3 · 부러진 창 · 방패 · 피 웅덩이). 바닥 꾸밈, 통과"),
    ("birth_broken_spears", broken_spears, (160, 80), (80, 72), [2, 1], False, 1, [1000],
     {"idle": [0]}, {"idle": False}, 0,
     "흩어진 창(부러진 창대 4 · 투구 · 화살 · 피 얼룩). 바닥 꾸밈(depth floor), 통과"),
]


def build(dry=False):
    b2.DRY = dry
    out = {}
    for (name, fn, (fw, fh), piv, fp, solid, n, ms, states, loops, occl, note) in SHEETS:
        frames = [fn(k) for k in range(n)]
        cols = set()
        for i, im in enumerate(frames):
            p = im.load()
            for y in range(fh):
                for x in range(fw):
                    cc = p[x, y]
                    if not cc[3]:
                        continue
                    assert x not in (0, fw - 1) and y not in (0, fh - 1), (name, i, "edge", x, y)
                    if cc[3] < 255:
                        assert cc[:3] == (10, 11, 16), (name, i, "semi", x, y, cc)
                        continue
                    cols.add(cc[:3])
        meta = {
            "id": name, "kind": "birth", "floor": "stage1", "region": "waste",
            "usage": "탄생 전장(여정 birth) — 회피 시험·튜토리얼 방 무대. " + note,
            "footprint": fp, "solid": solid, "depth": "floor" if name == "birth_broken_spears" else "y",
            "pivot": {"x": piv[0], "y": piv[1]}, "occludeAbove": occl,
            "states": states, "stateLoop": loops,
            "light": None, "emissiveColors": EMISSIVE_HEX, "paletteSwap": False, "version": "v3-r62a",
            "pivotNote": "pivot = 발자국 아래 변 가운데(바닥 접점). 도트 단위 — 시스템은 pixelScale 0.5 로 환산",
            "colors": len(cols), "source": SRC,
        }
        if solid:
            meta["blocksProjectiles"] = True
            meta["coverNote"] = "엄폐물 제안: 적 투사체를 막음(회피 시험의 숨을 자리). 판정 모양은 발자국 사각형"
        if name in ("birth_corpse_pile", "birth_corpse_mound"):
            meta["lightByState"] = {"idle": {"color": "#d67a11", "radius": 60, "intensity": 0.3, "flicker": {"amp": 0.25, "hz": 3},
                                             "offset": {"x": piv[0], "y": piv[1] - 30}}}
            meta["lightNote"] = "더미 속 불씨의 약한 빛(선택 — 광원 상한이면 생략)"
        b2.write_sheet("structures", name, frames, fw, fh, meta, durations=ms, loop=loops.get("idle", False))
        out[name] = (frames, piv)
    rep = b2.to_atlas() if not dry else []
    b2.WRITTEN.clear()
    return out, rep
