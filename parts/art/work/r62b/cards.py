"""P16 §1·§3·§4 — 유품 카드 그림(128×128) · 기억의 소품 아이콘(64×64) · 결산 처치자 초상(96×96).

- 유품 카드: data/passives.json 의 1층 풀(floor 1) 15종, 파일 = `ui_relics/<passiveId>.png`. 개성 카드(ui_traits)와 같은 결 —
  쿼터뷰 돌판 위 '그 물건 한 점' + 효과 한 순간, 투명 배경, 키캡·숫자·글자 없음, 테두리는 UI 가 그림. 128×128 도트(pixelScale 0.5, 화면 64px).
- 기억의 소품: `ui_relics/keepsake_<id>.png` 64×64 (깨진 잔·낡은 전표·매듭 끈·먹 묻은 붓).
- 처치자 초상: `ui_portraits/<enemyId>.png` 96×96 — 적 시트 idle down 0 프레임의 상반신을 1배로(밀도 그대로) + 먹 원 배경.
Gemini 402(크레디트 소진) → Claude 직접 도트(절차 셰이딩 + 좌표 손 보정).
"""
import math
import os

from PIL import Image

from common import SPR, SRC, dump, save_png, load_grid, cell, colors_of, board, hexc, FROST, LAVA, COLD_RIM, INK
import common
from kit2 import *  # noqa: F401,F403
from kit2 import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_NSTONE, R_CLOTH, R_CLOTHG, R_LIQ, R_BONE,
                  R_LEATHER, R_BLOOD, R_SKIN, R_HELM, R_PAPER, R_AMBERGLOW, R_GOLD, R_INKB, FLAME, contact, cyl, flame,
                  embers, ell, pol, cap, line, selout, slab, halo, sparks, star, splash, smoke, shade_mask, ell_mask,
                  poly_mask, arrow_stuck, qcol)

N = 128
CX, CY = 64, 98          # 돌판 가운데


def base(seed, glow=R_AMBERGLOW, gx=64, gy=62, grx=40, gry=34):
    c = Canvas(N, N)
    slab(c, CX, CY, 44, 22, th=6, seed=seed)
    c2 = Canvas(N, N)
    halo(c2, gx, gy, grx, gry, glow[:4], k=0.2)
    return c, c2


def finish(c, halo_c):
    im = c.im.copy()
    selout(im)
    out = halo_c.im.copy()
    out.alpha_composite(im)
    return out


# ---------------------------------------------------------------- 유품 15
def r_lifesteal():
    c, h = base(1)
    contact(c, 64, 94, 14, 5)
    # 쇠 술잔(잔 몸 + 목 + 받침)
    ell(c, (50, 88, 78, 96), R_IRON, base=0.45, gain=0.8, soft=2)
    cap(c, [(64, 76), (64, 90)], 3, R_IRON, base=0.55, gain=0.9, soft=1)
    pol(c, [(46, 52), (82, 52), (78, 70), (70, 78), (58, 78), (50, 70)], R_IRON, base=0.55, gain=0.9, soft=4)
    c.ellipse((46, 49, 82, 56), R_IRON[1])
    c.ellipse((48, 50, 80, 55), A[16])
    c.ellipse((52, 51, 72, 54), A[17])
    c.px(56, 52, A[19]); c.px(57, 52, A[20])
    for x, L in ((50, 14), (76, 9), (61, 6)):
        for k in range(L):
            c.px(x, 55 + k, A[17] if k < L - 2 else A[18])
    # 쓰러진 자의 혼이 잔으로(호박 줄기 3, 아래 → 위 → 잔)
    for j, ox in enumerate((-30, 30, 0)):
        for k in range(26):
            t = k / 25
            x = 64 + ox * (1 - t) + math.sin(t * 5 + j) * 2
            y = 30 + 26 * t - 22 * math.sin(t * math.pi) * (0.6 if j < 2 else 0.2) - (10 if j == 2 else 0)
            if (k + j) % 4:
                c.px(int(x), int(y), A[23] if t > 0.6 else A[20])
                if t > 0.85:
                    c.px(int(x) + 1, int(y), A[24])
    sparks(c, [(34, 30), (94, 30), (64, 16), (58, 26), (71, 24)])
    return finish(c, h)


def r_sprint():
    c, h = base(2)
    contact(c, 58, 94, 22, 7)
    # 장화 한 짝 서 있음, 한 짝 들린 채 앞으로
    pol(c, [(36, 64), (50, 64), (51, 86), (62, 88), (64, 94), (36, 94)], R_LEATHER, base=0.48, gain=0.8, soft=3)
    c.hline(36, 50, 66, R_LEATHER[4])
    pol(c, [(62, 52), (75, 49), (79, 70), (92, 70), (95, 77), (68, 80)], R_LEATHER, base=0.52, gain=0.8, soft=3)
    c.hline(68, 94, 79, R_LEATHER[0])
    for x in (40, 44, 48):
        c.px(x, 72, R_IRON[4])
    # 먼지 · 속도 줄(재)
    for y, L in ((58, 22), (66, 30), (74, 18)):
        for k in range(L):
            if k % 5 != 4:
                c.px(14 + k + (74 - y), y, PL[2] if k > L / 2 else PL[1])
    for (x, y, r) in ((30, 92, 5), (22, 90, 4), (100, 84, 3)):
        ell(c, (x - r, y - r * 0.6, x + r, y + r * 0.6), R_CLOTH, base=0.6, gain=0.4, soft=2, rim=False)
    sparks(c, [(98, 66), (104, 72), (94, 60)])
    return finish(c, h)


def r_ferocity():
    c, h = base(3)
    contact(c, 64, 92, 22, 7)
    # 땅에 박힌 이 빠진 전투 도끼
    for k in range(46):
        c.px(70 - k // 6, 88 - k, R_WOOD[3]); c.px(71 - k // 6, 88 - k, R_WOOD[1])
    for k in range(0, 46, 9):
        c.px(70 - k // 6, 88 - k, R_LEATHER[4])
    head = [(64, 44), (76, 40), (86, 30)] + [(86 + 12 * math.sin(t / 10 * math.pi), 30 + 36 * t / 10) for t in range(11)] + [(76, 58), (64, 54)]
    pol(c, head, R_IRON, base=0.55, gain=0.9, soft=3)
    for t in range(11):
        c.px(int(86 + 12 * math.sin(t / 10 * math.pi)), int(30 + 36 * t / 10), G[12])
    # 날 이 빠짐 + 날선 호박빛
    for (x, y) in ((96, 44), (97, 48), (96, 52)):
        c.px(x, y, A[25])
    for (x, y) in ((98, 46), (98, 47), (97, 56), (96, 57)):
        c.px(x, y, (0, 0, 0, 0))
    c.px(92, 36, A[26])
    sparks(c, [(100, 44), (104, 40), (102, 58), (106, 50)])
    # 피 자국
    for (x, y) in ((80, 60), (84, 59), (86, 62)):
        c.px(x, y, A[17])
    return finish(c, h)


def r_lastStand():
    c, h = base(4, glow=[A[16], A[17], A[18], A[19], A[20], A[21]])
    contact(c, 64, 92, 18, 6)
    # 부러진 검 꽂힘(짧은 날) + 붕대 감긴 자루
    pol(c, [(60, 88), (68, 88), (68, 64), (66, 58), (62, 62), (60, 66)], R_IRON, base=0.55, gain=0.9, soft=2)
    c.vline(64, 62, 87, R_IRON[5])
    c.rect(52, 54, 76, 57, R_IRON[3]); c.hline(52, 76, 54, R_IRON[5])   # 코등이
    cap(c, [(64, 52), (64, 34)], 3, R_CLOTH, base=0.6, gain=0.6)
    for y in range(35, 52, 3):
        c.hline(61, 67, y, PL[1])
    for (x, y) in ((63, 40), (65, 44), (62, 47)):
        c.px(x, y, A[17])
    ell(c, (60, 28, 68, 35), R_IRON, base=0.6, soft=1)
    # 부러진 자리 불씨
    for (x, y) in ((62, 58), (65, 57), (63, 60)):
        c.px(x, y, A[25])
    flame(c, 64, 59, 6, 10, seed=4, tongues=2)
    sparks(c, [(54, 44), (75, 40), (70, 30), (57, 30)])
    return finish(c, h)


def r_ironParry():
    c, h = base(5, glow=[FROST[1], FROST[2], FROST[3], FROST[4], FROST[5], FROST[6]])
    contact(c, 64, 92, 20, 6)
    ell(c, (40, 40, 88, 90), R_IRON, base=0.55, gain=0.85, soft=4, tilt=0.25)
    ell(c, (46, 46, 82, 84), R_IRON, base=0.45, gain=0.85, soft=4, tilt=0.25)
    for a in range(0, 360, 30):
        x, y = 64 + 21 * math.cos(math.radians(a)), 65 + 22 * math.sin(math.radians(a))
        c.px(int(x), int(y), R_IRON[5])
    # 패링 섬광(칼 '서리' — 간파 = 칼·대검 공용 빛, 차가운 흰빛)
    star(c, 70, 58, 9, FROST[8], FROST[6])
    ell(c, (66, 54, 74, 62), [FROST[5], FROST[6], FROST[7], FROST[8]], base=0.7, gain=0.4, soft=1, rim=False)
    for (x, y) in ((86, 46), (90, 52), (84, 40), (92, 44)):
        c.px(x, y, FROST[7])
    return finish(c, h)


def half_sprite(fr):
    """주인공 프레임을 카드 크기(½)로 — 면적 평균 후 원 프레임 색으로 되돌림(새 색 없음)."""
    pal = [cc for n, cc in (fr.getcolors(1 << 16) or []) if cc[3] >= 200]
    sm = fr.resize((fr.width // 2, fr.height // 2), Image.BOX)
    p = sm.load()
    for y in range(sm.height):
        for x in range(sm.width):
            r_, g_, b_, a_ = p[x, y]
            if a_ < 120:
                p[x, y] = (0, 0, 0, 0); continue
            best = min(pal, key=lambda q: (q[0] - r_) ** 2 + (q[1] - g_) ** 2 + (q[2] - b_) ** 2)
            p[x, y] = best[:3] + (255,)
    return sm


def r_afterimage():
    c, h = base(6, glow=[SL[1], SL[2], SL[3], SL[4], SL[5], G[8]])
    m, g = load_grid("player/v3/player_dash")
    fr = half_sprite(cell(m, g, 3, 2))   # right 행 대쉬 한가운데, 48×72
    piv = (24, 69)
    for ox, ramp in ((-34, [SL[0], SL[1], SL[2]]), (-17, [SL[1], SL[2], SL[3]])):
        im = fr.copy(); p = im.load()
        for y in range(im.height):
            for x in range(im.width):
                r_, g_, b_, a_ = p[x, y]
                if a_:
                    lum = (r_ * 3 + g_ * 6 + b_) / 2550
                    col = ramp[0] if lum < 0.18 else ramp[1] if lum < 0.4 else ramp[2]
                    p[x, y] = tuple(col[:3]) + (255,) if (ox > -30 or (x + y) % 4) else (0, 0, 0, 0)
        c.paste(im, 66 - piv[0] + ox, 96 - piv[1])
    contact(c, 68, 96, 12, 4)
    c.paste(fr, 66 - piv[0] + 4, 96 - piv[1])
    for y in (84, 90):
        for k in range(40):
            if k % 6 < 4:
                c.px(12 + k + (y - 84) // 2, y, PL[1])
    return finish(c, h)


def r_whetstone():
    c, h = base(7)
    contact(c, 64, 90, 26, 7)
    # 숫돌(납작한 직육면체) — 윗면·앞면
    c.poly([(36, 76), (78, 64), (94, 72), (52, 84)], SL[4])
    pol(c, [(36, 76), (78, 64), (94, 72), (52, 84)], [SL[2], SL[3], SL[4], SL[5], PL[2]], base=0.55, gain=0.5, soft=2)
    c.poly([(36, 76), (52, 84), (52, 90), (36, 82)], SL[2])
    c.poly([(52, 84), (94, 72), (94, 78), (52, 90)], SL[1])
    # 칼날이 숫돌 위를 미끄러짐
    pol(c, [(26, 66), (88, 56), (91, 60), (28, 71)], R_IRON, base=0.6, gain=0.9, soft=1)
    line(c, (27, 67), (88, 57), G[13])
    cap(c, [(20, 70), (8, 74)], 2.6, R_LEATHER, base=0.5, soft=1)
    # 불티
    sparks(c, [(72, 60), (76, 56), (80, 53), (84, 51), (78, 48), (88, 49), (70, 54), (92, 46)],
           (A[24], A[25], A[26], A[27]))
    return finish(c, h)


def r_callus():
    c, h = base(8)
    contact(c, 64, 92, 24, 7)
    # 감긴 손 싸개 두루마리 + 펼쳐진 끈
    cyl(c, 48, 72, 86, 11, R_CLOTH, ry=6, lid=True)
    for y in range(74, 88, 3):
        c.hline(37, 59, y, PL[1])
    c.ellipse((44, 69, 52, 75), PL[0])
    pts = [(58, 82), (70, 86), (84, 82), (96, 86), (104, 82)]
    for a, b in zip(pts, pts[1:]):
        cap(c, [a, b], 2.6, R_CLOTH, base=0.6, gain=0.6, soft=1)
    # 굳은 가죽 장갑(손가락 마디)
    pol(c, [(66, 48), (90, 44), (96, 62), (72, 70)], R_LEATHER, base=0.5, gain=0.8, soft=3)
    for k in range(4):
        cap(c, [(70 + k * 6, 48 - k), (68 + k * 6, 40 - k)], 2.4, R_LEATHER, base=0.55, gain=0.8, soft=1)
    for (x, y) in ((76, 54), (82, 52), (88, 51)):
        c.px(x, y, R_IRON[5])
    return finish(c, h)


def r_heavyWrist():
    c, h = base(9)
    contact(c, 60, 92, 26, 7)
    # 쇠 팔찌(수갑) — 두꺼운 고리
    m = ell_mask(N, N, (36, 46, 76, 86))
    m2 = ell_mask(N, N, (44, 54, 68, 78))
    mp, mp2 = m.load(), m2.load()
    for y in range(N):
        for x in range(N):
            if mp2[x, y] > 127:
                mp[x, y] = 0
    shade_mask(c, m, R_IRON, base=0.5, gain=0.9, soft=3)
    for a in range(0, 360, 45):
        x, y = 56 + 17 * math.cos(math.radians(a)), 66 + 17 * math.sin(math.radians(a))
        c.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), R_IRON[5])
    # 끊어진 사슬
    for i in range(4):
        x, y = 78 + i * 7, 74 + i * 3
        m3 = ell_mask(N, N, (x - 4, y - 3, x + 4, y + 3))
        m4 = ell_mask(N, N, (x - 2, y - 1, x + 2, y + 1))
        p3, p4 = m3.load(), m4.load()
        for yy in range(N):
            for xx in range(N):
                if p4[xx, yy] > 127:
                    p3[xx, yy] = 0
        shade_mask(c, m3, R_IRON, base=0.5, gain=0.8, soft=1)
    c.px(105, 85, A[25]); c.px(103, 84, A[24])
    # 무게 금(돌판 패임)
    for (x, y) in ((40, 88), (42, 89), (70, 90), (72, 89)):
        c.px(x, y, SL[0])
    return finish(c, h)


def r_closeCall():
    c, h = base(10, glow=[SL[1], SL[2], SL[3], SL[4], PL[2], PL[3]])
    contact(c, 62, 92, 20, 6)
    # 투구(챙에 화살이 스쳐 박힘)
    ell(c, (40, 46, 84, 86), R_HELM, base=0.55, gain=0.9, soft=4, tilt=0.3)
    c.rect(36, 78, 88, 82, R_HELM[2]); c.hline(36, 88, 78, R_HELM[4])
    c.vline(62, 48, 77, R_HELM[5])
    # 화살: 왼쪽 위에서 오른쪽 아래로 챙 꼭대기를 꿰뚫음
    for k in range(60):
        x, y = 22 + k, 30 + int(k * 0.5)
        col = R_WOOD[3] if k % 4 else R_WOOD[4]
        if not (54 < k < 60):
            c.px(x, y, col); c.px(x, y + 1, R_WOOD[1])
    for s in (-1, 1):
        for k in range(5):
            c.px(22 - k, 30 + s * (k + 1), PL[3] if s < 0 else PL[1])
    pol(c, [(82, 59), (90, 61), (82, 64)], R_IRON, base=0.6, soft=1)
    # 스친 자국(호박 불티)
    sparks(c, [(77, 54), (80, 52), (74, 50), (84, 56)])
    return finish(c, h)


def r_domino():
    c, h = base(11)
    # 쓰러지는 뼈 패 4장 + 마지막에서 튀는 재 파편
    for i in range(4):
        x0, y0 = 30 + i * 15, 88 - i * 3
        tilt = 0.0 + i * 0.32
        hgt, wd = 26, 9
        tx, ty = x0 + math.sin(tilt) * hgt, y0 - math.cos(tilt) * hgt
        pts = [(x0, y0), (x0 + wd, y0), (tx + wd, ty), (tx, ty)]
        contact(c, x0 + 5, y0 + 1, 7, 3)
        pol(c, pts, R_BONE, base=0.55, gain=0.7, soft=2)
        c.px(int((x0 + tx) / 2 + 4), int((y0 + ty) / 2), SL[1])
        c.px(int((x0 + tx) / 2 + 4), int((y0 + ty) / 2) - 5, SL[1])
    # 재 파편이 날아감(호박 꼬리)
    for k in range(16):
        x, y = 92 + k, 52 - int(k * 0.7)
        c.px(x, y, A[20] if k < 8 else A[23])
    pol(c, [(106, 38), (112, 36), (110, 42)], [A[19], A[22], A[24], A[25]], base=0.6, soft=1)
    return finish(c, h)


def r_brokenMirror():
    c, h = base(12, glow=[SL[1], SL[2], A[17], A[18], A[19], A[20]])
    contact(c, 60, 92, 18, 6)
    # 손거울(둥근 테 + 손잡이) 비스듬히 세움
    for k in range(18):
        c.px(70 + k // 2, 76 + k, R_WOOD[3]); c.px(71 + k // 2, 76 + k, R_WOOD[1])
    ell(c, (40, 34, 82, 80), R_GOLD, base=0.55, gain=0.8, soft=3)
    # 거울면(어두운 은) + 비친 망령(호박 눈 하나)
    ell(c, (45, 39, 77, 75), [G[1], G[2], G[3], G[4], G[5], G[6]], base=0.45, gain=0.6, soft=3, rim=False)
    cap(c, [(61, 60), (61, 70)], 6, [G[0], G[1], G[1], G[2]], base=0.4, gain=0.2, soft=1)
    ell(c, (55, 47, 67, 59), [G[0], G[1], G[1], G[2]], base=0.4, gain=0.2, soft=1, rim=False)
    c.px(63, 52, A[25]); c.px(64, 52, A[24])
    # 금(가운데에서 뻗음) — 갈라진 조각 하나는 어긋남
    for a in (20, 75, 140, 210, 290):
        x, y = 66.0, 50.0
        for k in range(18):
            x += math.cos(math.radians(a)) * 1.0
            y += math.sin(math.radians(a)) * 1.0
            if 46 < x < 76 and 40 < y < 74:
                c.px(int(x), int(y), G[12] if k % 3 else G[9])
    star(c, 52, 44, 3, G[14], G[11])
    return finish(c, h)


def r_spilledDrink():
    c, h = base(13)
    splash(c, 72, 88, 30, 9, ramp=R_LIQ, seed=13, glint=True, blobs=5)
    # 쓰러진 술병(옆으로 누운 도기)
    ell(c, (26, 62, 64, 88), R_WOODG, base=0.5, gain=0.85, soft=5, tilt=0.2)
    cap(c, [(62, 72), (72, 74)], 3.4, R_WOODG, base=0.5, soft=1)
    c.ellipse((70, 70, 76, 77), A[17])
    # 쏟아지는 술줄기
    for k in range(10):
        c.px(74 + k, 74 + k // 2, A[20] if k % 3 else A[22])
    c.hline(34, 56, 70, R_LEATHER[2])
    sparks(c, [(88, 82), (60, 90), (96, 88)], (A[22], A[24]))
    return finish(c, h)


def r_hipFlask():
    c, h = base(14)
    contact(c, 64, 92, 18, 6)
    # 호리병(조롱박) — 아래 큰 알 + 위 작은 알 + 마개 + 끈
    R_GOURD = [WD[0], WD[2], WD[3], WD[4], A[19], A[20]]
    ell(c, (44, 58, 84, 92), R_GOURD, base=0.45, gain=0.85, soft=4, tilt=0.2)
    ell(c, (52, 40, 76, 62), R_GOURD, base=0.5, gain=0.85, soft=3, tilt=0.2)
    c.rect(59, 34, 69, 40, R_WOOD[2]); c.hline(59, 69, 34, R_WOOD[4])
    c.hline(52, 76, 61, R_LEATHER[1]); c.hline(52, 76, 62, R_LEATHER[3])
    pts = [(52, 62), (40, 54), (34, 64), (40, 74)]
    for a, b in zip(pts, pts[1:]):
        line(c, a, b, R_LEATHER[3])
    # 잔 낙인(바랜 잔 문양)
    for dx in range(-4, 5):
        c.px(64 + dx, 72, A[19])
    for (dx, dy) in ((-3, 1), (3, 1), (-2, 2), (2, 2), (-1, 3), (1, 3), (0, 4), (0, 5)):
        c.px(64 + dx, 72 + dy, A[18])
    return finish(c, h)


def r_drunkFist():
    c, h = base(15)
    contact(c, 64, 96, 24, 6)
    # 쓰러진 잔(왼쪽 아래) + 크게 휘는 주먹 궤적(호박 소용돌이) + 붕대 감은 주먹(가운데)
    ell(c, (24, 82, 42, 94), R_WOODG, base=0.5, gain=0.8, soft=3)
    c.ellipse((38, 84, 44, 91), A[17])
    splash(c, 50, 94, 10, 3, ramp=R_LIQ, seed=5, glint=True, blobs=2)
    for t in range(120):
        a = t * 0.11
        r_ = 10 + t * 0.26
        x, y = 66 + r_ * math.cos(a), 52 + r_ * 0.6 * math.sin(a)
        if t % 5 != 4:
            col = A[19] if t < 40 else A[22] if t < 85 else A[24]
            c.px(int(x), int(y), col)
            if t > 60:
                c.px(int(x), int(y) + 1, A[20])
    # 주먹: 손등 덩어리 + 네 손가락 마디 + 엄지 + 붕대 줄
    ell(c, (50, 40, 82, 66), R_SKIN, base=0.5, gain=0.85, soft=4)
    for k in range(4):
        ell(c, (50 + k * 8, 34 - (k % 2), 59 + k * 8, 46 - (k % 2)), R_SKIN, base=0.55, gain=0.85, soft=2)
    cap(c, [(52, 56), (64, 52)], 4, R_SKIN, base=0.5, soft=2)
    for y in (48, 53, 58, 63):
        line(c, (52, y + 2), (80, y - 2), PL[3])
        line(c, (52, y + 3), (80, y - 1), PL[1])
    cap(c, [(70, 66), (78, 82)], 6, R_CLOTH, base=0.5, soft=2)
    sparks(c, [(98, 44), (100, 60), (34, 46), (90, 30)])
    return finish(c, h)


RELICS = {
    "lifesteal": (r_lifesteal, "피 고인 쇠잔 — 쓰러진 자의 혼이 잔으로 흘러든다"),
    "sprint": (r_sprint, "닳은 장화 한 켤레 — 한 짝은 이미 앞으로"),
    "ferocity": (r_ferocity, "이 빠진 전투 도끼가 돌판에 박혔다"),
    "lastStand": (r_lastStand, "붕대 감긴 부러진 검 — 부러진 자리에서 불씨"),
    "ironParry": (r_ironParry, "움푹 팬 쇠방패와 받아친 순간의 찬 섬광"),
    "afterimage": (r_afterimage, "찢긴 목도리가 잔상 둘을 끌고 날린다"),
    "whetstone": (r_whetstone, "숫돌 위를 미끄러지는 날, 불티"),
    "callus": (r_callus, "손 싸개 두루마리와 굳은 가죽 장갑"),
    "heavyWrist": (r_heavyWrist, "끊어진 사슬이 달린 쇠 팔찌"),
    "closeCall": (r_closeCall, "투구 챙을 스쳐 꿰뚫은 화살"),
    "domino": (r_domino, "차례로 쓰러지는 뼈 패, 마지막 패에서 튀는 재 파편"),
    "brokenMirror": (r_brokenMirror, "금 간 손거울 속 망령 하나"),
    "spilledDrink": (r_spilledDrink, "쓰러진 술병과 번지는 술 웅덩이"),
    "hipFlask": (r_hipFlask, "잔 낙인이 찍힌 허리춤 호리병"),
    "drunkFist": (r_drunkFist, "쓰러진 잔과 휘청이는 주먹의 소용돌이"),
}


# ---------------------------------------------------------------- 기억의 소품 4 (64×64)
def k_brokenCup():
    c = Canvas(64, 64)
    contact(c, 30, 54, 22, 6)
    cyl(c, 28, 22, 50, 16, R_WOODG, bulge=-0.1, ry=7)
    c.ellipse((13, 18, 43, 27), SL[1])
    c.ellipse((16, 19, 40, 25), SL[0])
    # 깨진 이(오른쪽 위 조각이 떨어져 나감)
    for y in range(14, 40):
        for x in range(32, 48):
            if c.get(x, y)[3] and (y - 14) < 22 - (x - 32) * 1.1 and (y - 14) < (x - 30) * 1.6:
                c.px(x, y, (0, 0, 0, 0))
    for (x, y) in ((33, 22), (35, 26), (37, 29), (39, 33), (41, 36)):
        c.px(x, y, PL[3])
    pol(c, [(44, 46), (56, 43), (58, 50), (47, 53)], R_WOODG, base=0.5, soft=1)
    pol(c, [(48, 34), (56, 32), (54, 39)], R_WOODG, base=0.55, soft=1)
    for dx in range(-4, 5):
        c.px(24 + dx, 38, A[19])
    for (dx, dy) in ((-3, 1), (3, 1), (-2, 2), (2, 2), (-1, 3), (1, 3), (0, 4), (0, 5)):
        c.px(24 + dx, 38 + dy, A[18])
    c.px(16, 22, A[22]); c.px(17, 22, A[21])
    im = c.im; selout(im)
    return im


def k_oldVoucher():
    c = Canvas(64, 64)
    contact(c, 32, 54, 26, 5)
    pol(c, [(4, 18), (48, 6), (58, 40), (12, 52)], R_PAPER, base=0.58, gain=0.5, soft=2)
    pol(c, [(8, 26), (54, 20), (60, 52), (14, 58)], R_PAPER, base=0.68, gain=0.5, soft=2)
    for y in (32, 37, 42):
        line(c, (16, y + 2), (46, y - 2), PL[1])
    line(c, (16, 27), (34, 25), WD[2])
    ell(c, (38, 40, 52, 52), [A[16], A[17], A[18], A[19]], base=0.55, soft=1, rim=False)
    c.px(44, 44, A[20]); c.px(45, 45, A[20])
    for (x, y) in ((56, 50), (58, 49), (59, 51), (57, 53), (55, 54), (54, 52)):
        c.px(x, y, G[1])
    c.px(57, 47, A[25]); c.px(60, 50, A[24]); c.px(56, 51, A[23])
    im = c.im; selout(im)
    return im


def k_knotCord():
    c = Canvas(64, 64)
    contact(c, 32, 56, 22, 4)
    R_CORD = [SL[0], A[16], A[17], A[18], A[19], A[20]]
    for t in range(0, 360, 3):
        a = math.radians(t)
        for (cx, cy) in ((18, 24), (46, 24)):
            x, y = cx + 13 * math.cos(a), cy + 10 * math.sin(a)
            cap(c, [(x, y)], 2.2, R_CORD, base=0.55, gain=0.6, soft=0, rim=False)
    ell(c, (25, 18, 39, 32), R_CORD, base=0.6, gain=0.8, soft=1)
    for pts in (((28, 31), (20, 44), (14, 56)), ((36, 31), (44, 44), (48, 58))):
        for a, b in zip(pts, pts[1:]):
            cap(c, [a, b], 2.2, R_CORD, base=0.5, soft=0)
    for (x, y) in ((13, 57), (12, 59), (15, 59), (48, 59), (49, 61), (47, 61)):
        c.px(x, y, A[19])
    c.px(30, 21, A[22]); c.px(31, 21, A[21])
    im = c.im; selout(im)
    return im


def k_inkBrush():
    c = Canvas(64, 64)
    contact(c, 30, 54, 26, 4)
    for y in range(42, 58):
        for x in range(4, 40):
            d = math.hypot((x - 20) / 17, (y - 50) / 6)
            if d < 1 and ((x * 7 + y * 3) % 11) > 1:
                c.px(x, y, G[1] if d < 0.7 else G[2])
    for k in range(46):
        x, y = 16 + k, 46 - int(k * 0.85)
        for w in range(3):
            c.px(x + w - 1, y, R_WOOD[4] if w == 0 else R_WOOD[3] if w == 1 else R_WOOD[1])
        if k % 9 == 0:
            c.px(x, y, R_WOOD[2]); c.px(x + 1, y, R_WOOD[1])
    pol(c, [(4, 56), (10, 46), (18, 42), (22, 46), (14, 54)], R_INKB, base=0.45, gain=0.6, soft=1)
    c.rect(16, 43, 20, 46, R_IRON[3])
    c.px(10, 50, G[5]); c.px(13, 46, G[4])
    c.px(60, 7, A[18]); c.px(61, 6, A[18]); c.px(62, 8, A[17])
    for (x, y) in ((36, 30), (40, 26), (38, 28)):
        c.px(x, y, A[23])
    im = c.im; selout(im)
    return im


KEEPSAKES = {
    "brokenCup": (k_brokenCup, "깨진 잔 — 첫 피격 피해 무효(예)"),
    "oldVoucher": (k_oldVoucher, "낡은 전표 — 시작 전표(예)"),
    "knotCord": (k_knotCord, "매듭 끈 — 대쉬 1회 추가 충전(예)"),
    "inkBrush": (k_inkBrush, "먹 묻은 붓 — 첫 개성 발현 카드 +1(예)"),
}


# ---------------------------------------------------------------- 처치자 초상 96×96
PORTRAITS = {
    # id: (시트, 행, 프레임, 상반신 잘라낼 위쪽 y, 이름 메모)
    "dummy": ("enemies/v3/dummy_idle", 0, 0, None, "징집병"),
    "archer": ("enemies/v3/archer_idle", 0, 0, None, "사수"),
    "charger": ("enemies/v3/charger_idle", 0, 0, None, "결사병"),
    "peddler": ("enemies/v3/peddler_idle", 0, 0, None, "독주 행상"),
    "porter": ("enemies/v3/porter_idle", 0, 0, None, "술통 짐꾼"),
    "boss1": ("bosses/v3/stage1_idle", 0, 0, None, "만취"),
}


def portrait(sheet, row, col, seed):
    m, g = load_grid(sheet)
    fr = cell(m, g, row, col)
    bb = fr.getbbox()
    x0, y0, x1, y1 = bb
    w = x1 - x0
    S = 96
    big = (y1 - y0) > 200
    if big:   # 보스: 머리·어깨(1배)
        cx = (x0 + x1) // 2
        top = y0
        crop = fr.crop((cx - S // 2, top - 4, cx + S // 2, top - 4 + S))
    else:
        cx = (x0 + x1) // 2
        crop = fr.crop((cx - S // 2, y0 - 6, cx + S // 2, y0 - 6 + S))
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    c = Canvas(S, S)
    # 먹 원 배경(가장자리 붓 결) + 차가운 테
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - 48, y - 46) / 44
            n = ((x * 13 + y * 7 + seed) % 17) / 17
            if d < 0.92 + 0.08 * n:
                c.px(x, y, INK[1] if d < 0.75 else INK[2] if d < 0.86 else INK[3])
    out.alpha_composite(c.im)
    # 몸을 원 안으로 자르되 아래는 원 밖으로 흘러도 됨(아래 가장자리 페이드: 아래 10줄 체커)
    cp = crop.load()
    for y in range(S):
        for x in range(S):
            if cp[x, y][3] and y > S - 12 and (x + y) % 2 and y > S - 6:
                cp[x, y] = (0, 0, 0, 0)
    out.alpha_composite(crop)
    # 차가운 림(적 림과 같은 색)
    op = out.load()
    for y in range(S):
        for x in range(S):
            if op[x, y][3] == 0:
                continue
            d = math.hypot(x - 48, y - 46) / 44
            if 0.9 < d < 1.0 and y < 70 and (x + y) % 3:
                op[x, y] = COLD_RIM[1] + (255,)
    return out


def build(preview_path=None):
    items = []
    meta = {"size": [N, N], "pixelScale": 0.5, "screenSize": [64, 64], "background": "투명",
            "rule": "개성 카드(ui_traits, 계약 §27)와 같은 결 — 쿼터뷰 돌판 위 물건 한 점·효과 한 순간. 키캡·숫자·글자·테두리 없음(UI 가 그림)",
            "method": "Claude 직접 도트(Gemini 402) — r62b/cards.py", "source": SRC + " · cards.py", "relics": {}, "keepsakes": {},
            "portraits": {}}
    for rid, (fn, note) in RELICS.items():
        im = fn()
        assert im.size == (N, N)
        if not common.DRY:
            save_png(im, os.path.join(SPR, "ui_relics", rid + ".png"))
        meta["relics"][rid] = {"file": f"ui_relics/{rid}.png", "passiveId": rid, "scene": note, "colors": len(colors_of(im))}
        items.append(im)
    for kid, (fn, note) in KEEPSAKES.items():
        im = fn()
        assert im.size == (64, 64)
        if not common.DRY:
            save_png(im, os.path.join(SPR, "ui_relics", "keepsake_" + kid + ".png"))
        meta["keepsakes"][kid] = {"file": f"ui_relics/keepsake_{kid}.png", "size": [64, 64], "note": note,
                                  "idNote": "아트 임시 id — 시스템·스토리 확정 id 가 다르면 파일 이름만 바꿔 다시 냄"}
        items.append(im)
    pmeta = {"size": [96, 96], "pixelScale": 0.5, "rule": "적 idle down 0 프레임 상반신 1배(월드와 같은 밀도) + 먹 원 배경 + 차가운 림. 결산 '처치자' 칸",
             "source": SRC + " · cards.py", "portraits": {}}
    for i, (pid, (sheet, row, col, _, name)) in enumerate(PORTRAITS.items()):
        im = portrait(sheet, row, col, i)
        if not common.DRY:
            save_png(im, os.path.join(SPR, "ui_portraits", pid + ".png"))
        pmeta["portraits"][pid] = {"file": f"ui_portraits/{pid}.png", "enemyId": pid, "from": sheet, "name": name}
        items.append(im)
    if not common.DRY:
        dump(meta, os.path.join(SPR, "ui_relics", "relics.json"))
        dump(pmeta, os.path.join(SPR, "ui_portraits", "portraits.json"))
    if preview_path:
        board(items, bg=(46, 40, 36), k=2, max_w=1100).save(preview_path)
