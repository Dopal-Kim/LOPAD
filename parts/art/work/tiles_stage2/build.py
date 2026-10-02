#!/usr/bin/env python3
"""LOPAD 2층 '패(牌)' 도박장 제국 타일셋 (16x16) — 37라운드 재작업. 단일 소스, 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage2/build.py
산출: assets/tiles/stage2.png (8x5 128x80, 40라운드 인덱스 표 v3) / stage2.json — tilecommon2.py (1층과 동일)
      parts/art/work/tiles_stage2/preview.png · preview_room.png · preview_rooms.png · preview_seam.png

컨셉 (text-pack B2·D2): "길바닥에 깔린 패 사이로 사람이 들려 나간다." 마루널은 없다 — 도박장 뒷골목의 검은 흙바닥에
  버린 패(G06 종이, 반쯤 묻힘)·칩(녹색 B/L)이 밟혀 있다. 1층과 같은 가장 어두운 바닥(평균 ≈ G01).
  벽 = 판자(G02, 틈 K) / 변형 1 = 제국 표식(패 문양 스텐실 G06) / 변형 2 = 긁어 쓴 셈 자국 '한 판만 더' 아홉 번 + 못 박은 패
  소품 8 = 주사위 통·판돈 자루·뒤집힌 의자·초록 등불 + 빚 장부(통과)·쇠우리(solid) + 40라운드: 엎어진 노름판(solid)·흩어진 칩과 패(통과)
  40라운드: 방 종류별 바닥 4변형 — 특징 무늬는 _0·_1 에만, _2·_3 은 은은하게(격자 방지).
색 예산: 무채 10 (K, G01~G07, G09, G12) + 강조 4 (19 shadow1 얼룩·펠트, 21 base 칩·등불, 23 light1, 25 glow 잔불 심).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon2 as tc  # noqa: E402

G = tc.G
A = tc.ramp(2)
T = tc.T

C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
    "S": A[3],   # 19 shadow1 — 핏자국·펠트
    "B": A[5],   # 21 base   — 칩·등불 유리
    "L": A[7],   # 23 light1 — 칩 중심·불빛
    "W": A[9],   # 25 glow   — 심지·잔불 심
}
ctx = tc.Ctx(C)
new = ctx.new


# ============================================================ 바닥
DOTS = {"K": 24, "2": 15, "3": 3}
PAIRS = {"K": 3}


def card(s, x, y, buried=True):
    """버린 패 3x3: 종이 G06, 좌상단 G07, 우·하 K 모서리. buried 면 아랫줄이 흙(G01/G02)에 덮인다."""
    s.rect(x, y, x + 2, y + 2, C["6"])
    s.px(x, y, C["7"]); s.px(x + 1, y + 1, C["3"])
    s.line(x, y + 3, x + 3, y + 3, C["K"]); s.line(x + 3, y, x + 3, y + 3, C["K"])
    if buried:
        s.px(x, y + 2, C["2"]); s.px(x + 2, y + 2, C["1"]); s.px(x + 3, y + 3, C["1"])


def chip(s, x, y):
    """칩 2x2: B + 가운데 L 1px. 어두운 바닥에서 녹색 점으로 산다."""
    s.rect(x, y, x + 1, y + 1, C["B"]); s.px(x, y, C["L"])
    s.px(x, y + 2, C["K"])


def common_floor(i):
    s, rnd = tc.dirt(ctx, seed=100 + i, base="1", dots=DOTS, pairs=PAIRS)
    if i == 0:
        card(s, 4, 8)
        tc.ember_small(s, C, 12, 3)
    elif i == 1:
        chip(s, 10, 9)
        s.px(3, 4, C["2"]); s.px(4, 4, C["3"]); s.px(4, 5, C["2"])      # 자갈
    elif i == 2:
        card(s, 9, 3); s.px(12, 7, C["6"]); s.px(13, 7, C["7"])         # 패 두 장, 하나는 거의 묻힘
        tc.ember(s, C, 4, 11, rising=True)
    else:
        tc.stain_small(s, C, rnd, 6, 9, dark="S", n=4)                 # 들려 나간 자리
        chip(s, 12, 4)
    return s


def corridor_tile():
    s, rnd = tc.dirt(ctx, seed=140, base="1", dots={"K": 44, "2": 6}, pairs={"K": 4})
    return s


def start_floor(i):
    s, rnd = tc.dirt(ctx, seed=200 + i, base="1", dots={"K": 20, "2": 14, "3": 3}, pairs={"K": 2})
    if i == 0:
        tc.bootprint(s, C, 3, 3, left=True); tc.bootprint(s, C, 7, 6, left=False); tc.bootprint(s, C, 11, 2, left=True)
        s.rect(12, 12, 13, 13, C["7"]); s.px(12, 12, C["K"])            # 떨어진 주사위 (흙 묻은 G07)
    elif i == 1:
        for x0, y0, dx in [(2, 10, 1), (5, 12, 1), (3, 13, 1), (7, 9, 0), (6, 11, 1)]:
            s.px(x0, y0, C["3"]); s.px(x0 + dx, y0 + (1 - dx), C["3"])   # 짚
        tc.ash_patch(s, C, rnd, 11, 4, r=2); tc.ember_small(s, C, 11, 4)
        tc.bootprint(s, C, 12, 10, left=False)
    elif i == 2:
        tc.bootprint(s, C, 9, 9, left=False)
        s.px(3, 4, C["6"]); s.px(4, 4, C["2"])                           # 거의 묻힌 패 끝
    else:
        s.px(11, 6, C["3"]); s.px(12, 7, C["3"])
        s.px(4, 9, C["2"]); s.px(5, 9, C["3"]); s.px(5, 10, C["2"])
    return s


def trial_floor(i):
    s, rnd = tc.dirt(ctx, seed=300 + i, base="1", dots={"K": 28, "2": 12, "3": 2}, pairs={"K": 4})
    if i == 0:
        tc.stain_small(s, C, rnd, 5, 5, dark="S", n=5); s.px(5, 5, C["B"])
        s.px(8, 4, C["S"]); s.px(3, 8, C["S"])
        tc.pock(s, C, 11, 10)
        s.px(9, 2, C["6"]); s.px(10, 2, C["6"]); s.px(10, 3, C["2"]); s.px(11, 3, C["K"])   # 거의 묻힌 패 (3x3 패는 밝은 네모로 반복됐다)
    elif i == 1:
        tc.pock(s, C, 11, 3); tc.pock(s, C, 4, 11)
        s.px(7, 8, C["S"]); s.px(13, 9, C["S"]); s.px(2, 5, C["S"]); s.px(8, 13, C["S"])
        chip(s, 13, 12)
    elif i == 2:
        s.px(9, 11, C["S"]); s.px(10, 12, C["S"]); s.px(3, 6, C["S"])
        s.px(12, 4, C["6"]); s.px(13, 4, C["7"])                         # 밟혀 찢긴 패 조각
    else:
        tc.pock(s, C, 7, 7)
        s.px(12, 3, C["S"]); s.px(2, 12, C["K"]); s.px(3, 12, C["K"])
    return s


def rest_floor(i):
    s, rnd = tc.dirt(ctx, seed=400 + i, base="1", dots={"K": 14, "2": 16, "3": 4}, pairs={"2": 2})
    if i == 0:
        tc.ash_patch(s, C, rnd, 8, 8, r=3); s.px(8, 7, C["L"])
        s.px(3, 12, C["3"]); s.px(4, 12, C["3"])
    elif i == 1:
        tc.ash_patch(s, C, rnd, 4, 4, r=2)
        s.px(10, 10, C["6"]); s.px(11, 10, C["6"]); s.px(11, 11, C["2"]); s.px(12, 11, C["K"])   # 거의 묻힌 패
        s.px(12, 5, C["2"]); s.px(13, 6, C["2"])
    elif i == 2:
        s.px(11, 3, C["3"]); s.px(12, 3, C["3"]); s.px(12, 4, C["4"])
        s.px(4, 10, C["3"]); s.px(5, 11, C["3"])
    else:
        s.px(6, 6, C["3"]); s.px(7, 6, C["4"])
        s.px(12, 12, C["2"]); s.px(13, 12, C["2"]); s.px(3, 3, C["3"])
    return s


DIAMOND = [(3, 0), (2, 1), (3, 1), (4, 1), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (2, 3), (3, 3), (4, 3), (3, 4)]  # 패 문양(마름모) 7x5


def boss_floor(i):
    s, rnd = tc.dirt(ctx, seed=500 + i, base="1", dots={"K": 22, "2": 10, "3": 2}, pairs={"K": 2})
    if i == 0:
        tc.buried_slab(s, C, rnd, (2, 2, 8, 8), carve=[(x + 2, y + 3) for x, y in DIAMOND], bury_from=0.55)
        for x, y in [(2, 2), (3, 2), (2, 3), (8, 2), (2, 8), (2, 7), (3, 8), (8, 8), (8, 7), (7, 8), (8, 3)]:
            s.px(x, y, C["1"])
        s.px(12, 11, C["2"]); s.px(13, 11, C["3"]); s.px(13, 12, C["2"])
    elif i == 1:
        for x, y, ch in [(10, 3, "2"), (11, 3, "3"), (12, 3, "2"), (11, 4, "2"), (4, 10, "2"), (5, 10, "3"), (5, 11, "2"), (4, 11, "K"), (13, 13, "2")]:
            s.px(x, y, C[ch])
        chip(s, 7, 7)
    elif i == 2:
        s.px(3, 12, C["2"]); s.px(4, 12, C["3"]); s.px(4, 13, C["2"])
        s.px(11, 5, C["B"])                                              # 칩 하나 (반쯤 묻힘)
    else:
        s.px(9, 9, C["3"]); s.px(10, 9, C["2"]); s.px(10, 10, C["K"])
        s.px(3, 3, C["2"]); s.px(4, 3, C["2"])
    return s


# ============================================================ 벽 (판자 G02 + K 틈)
def wall_base(s):
    s.rect(0, 0, T - 1, T - 1, C["2"])
    for x in (0, 4, 8, 12):
        s.line(x, 0, x, T - 1, C["K"])
        s.line(x + 1, 0, x + 1, T - 2, C["3"])
    for x, y in [(2, 2), (6, 13), (10, 2), (14, 13)]:
        s.px(x, y, C["4"])                                   # 못 머리
    s.px(6, 7, C["K"]); s.px(7, 7, C["1"])                   # 옹이
    s.px(11, 10, C["1"]); s.px(11, 11, C["1"])                # 썩은 자리
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_face():
    s = new()
    return wall_base(s)


def wall_v1():
    """제국 표식: 판자에 회칠로 찍은 패 문양(마름모 G06). 닳은 자리 G04."""
    s = new()
    wall_base(s)
    for x, y in DIAMOND:
        s.px(x + 5, y + 5, C["6"])
    s.px(8, 7, C["4"]); s.px(6, 6, C["4"])
    return s


def wall_v2():
    """낙서: '한 판만 더' 셈 자국(세로 4 + 사선, G04/G05) 두 묶음 + 못으로 박아 둔 패(G06) 한 장."""
    s = new()
    wall_base(s)
    for x in (2, 3):
        s.line(x, 4, x, 7, C["4"])
    s.line(2, 7, 3, 5, C["5"])
    for x in (5, 6, 7):
        s.line(x, 9, x, 12, C["4"])
    s.line(5, 12, 7, 10, C["5"])
    s.rect(10, 3, 13, 7, C["6"]); s.px(10, 3, C["7"]); s.px(11, 5, C["3"]); s.px(12, 5, C["3"])
    s.px(11, 2, C["K"]); s.line(10, 8, 13, 8, C["1"])
    return s


def wall_top():
    """벽 윗면: 판자 덮개 G03, 이음 K, 빛 G04, 못 G02."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    for y in (0, 8):
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["4"])
    s.line(5, 0, 5, 7, C["K"]); s.line(12, 8, 12, 15, C["K"])
    for x, y in [(2, 4), (9, 4), (10, 4), (4, 12), (14, 12)]:
        s.px(x, y, C["2"])
    return s


# ============================================================ 문
def door_frame(s):
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["3"]); s.line(0, 0, 0, T - 1, C["K"]); s.line(1, 0, 1, T - 1, C["4"])
    s.rect(13, 0, 15, T - 1, C["3"]); s.line(15, 0, 15, T - 1, C["K"]); s.line(13, 0, 13, T - 1, C["2"])
    s.rect(0, 0, T - 1, 1, C["3"]); s.line(0, 0, T - 1, 0, C["K"]); s.line(3, 1, 12, 1, C["4"])


def door_open():
    s = new()
    door_frame(s)
    s.rect(3, 2, 12, 15, C["1"])
    rnd = random.Random(9)
    tc.scatter(s, C, rnd, "K", 14, box=(5, 2, 12, 15)); tc.scatter(s, C, rnd, "2", 4, box=(5, 2, 12, 15))
    s.rect(3, 2, 4, 14, C["5"]); s.line(4, 2, 4, 14, C["4"])
    s.px(3, 5, C["7"]); s.px(3, 12, C["7"]); s.px(4, 5, C["6"]); s.px(4, 12, C["6"])
    s.line(3, 15, 4, 15, C["2"])
    s.line(5, 3, 5, 13, C["L"])
    return s


def door_planks(s, x0=3, x1=12, y0=2, y1=15):
    s.rect(x0, y0, x1, y1, C["4"])
    for x in (x0 + 2, x0 + 5, x0 + 8):
        s.line(x, y0, x, y1, C["2"])
    s.line(x0, y0, x1, y0, C["5"])
    for y in (y0 + 3, y0 + 10):
        s.line(x0, y, x1, y, C["6"])
        s.line(x0, y + 1, x1, y + 1, C["5"])
        for x in (x0 + 1, x0 + 7):
            s.px(x, y, C["9"])


def peephole(s):
    s.rect(5, 7, 10, 8, C["K"]); s.px(7, 7, C["6"]); s.px(7, 8, C["6"]); s.px(9, 7, C["6"]); s.px(9, 8, C["6"])


def door_closed():
    s = new()
    door_frame(s); door_planks(s); peephole(s)
    s.px(10, 11, C["7"]); s.px(10, 12, C["K"])
    return s


def door_locked():
    s = new()
    door_frame(s); door_planks(s); peephole(s)
    for i, (x, y) in enumerate([(3, 14), (4, 13), (5, 12), (6, 11), (7, 10), (8, 9), (9, 8), (10, 7), (11, 6), (12, 5)]):
        s.px(x, y, C["7"] if i % 2 == 0 else C["6"])
    s.px(2, 14, C["7"]); s.px(13, 5, C["7"])
    s.rect(6, 11, 9, 14, C["7"]); s.line(6, 11, 9, 11, C["9"])
    s.px(6, 10, C["9"]); s.px(9, 10, C["9"])
    s.px(7, 12, C["K"]); s.px(8, 12, C["K"]); s.px(7, 13, C["K"])
    return s


# ============================================================ 출구 · 상점
def exit_stairs():
    s = new()
    body = ["4", "4", "3", "3"]
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["6"])
        s.rect(0, y + 2, T - 1, y + 3, C[body[i]])
        s.line(0, y + 3, T - 1, y + 3, C["2"] if i >= 2 else C["3"])
        if i in (0, 2):
            s.px(12, y + 1, C["L"]); s.px(13, y + 1, C["L"])
    for x, y in [(3, 2), (9, 6), (6, 10), (14, 14)]:
        s.px(x, y, C["2"])
    return s


def shop_counter():
    """좌판: 널 탁자(G03) 위 펠트 깔개(S) + 칩 더미 2 + 패 2."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["1"]); s.line(0, y + 1, T - 1, y + 1, C["4"])
    s.line(0, 15, T - 1, 15, C["1"])
    s.rect(3, 3, 12, 12, C["S"])
    s.line(3, 13, 13, 13, C["1"]); s.line(13, 3, 13, 13, C["1"])
    for bx, h in ((4, 5), (9, 3)):
        for i in range(h):
            y = 11 - i
            if i % 2 == 0:
                s.line(bx, y, bx + 2, y, C["B"]); s.px(bx + 1, y, C["L"])
            else:
                s.line(bx, y, bx + 2, y, C["C"])
        s.px(bx + 3, 11, C["1"]); s.px(bx + 3, 10, C["1"])
    s.rect(8, 4, 10, 7, C["7"]); s.px(8, 4, C["9"]); s.px(9, 6, C["3"]); s.line(8, 8, 11, 8, C["1"]); s.line(11, 4, 11, 8, C["1"])
    return s


# ============================================================ 소품
def prop_dice_cup():
    s = new()
    s.rect(5, 4, 10, 11, C["6"])
    s.line(5, 4, 5, 11, C["7"]); s.line(6, 4, 6, 11, C["7"]); s.line(10, 4, 10, 11, C["5"])
    s.line(5, 4, 10, 4, C["7"])
    s.rect(5, 3, 10, 3, C["5"]); s.rect(6, 2, 9, 2, C["4"]); s.rect(6, 3, 9, 3, C["3"])
    s.line(5, 12, 10, 12, C["2"])
    s.outline(C["K"], where="inside")
    for dx, dy in ((11, 9), (1, 10)):
        s.rect(dx, dy, dx + 2, dy + 2, C["C"]); s.px(dx + 1, dy + 1, C["K"])
        s.px(dx + 3, dy + 2, C["2"]); s.line(dx, dy + 3, dx + 3, dy + 3, C["2"])
    s.line(5, 12, 10, 12, C["2"])
    return s


def prop_sack():
    s = new()
    prof = {2: (6, 9), 3: (6, 9), 4: (5, 10), 5: (4, 11), 6: (3, 12), 7: (3, 12), 8: (2, 13), 9: (2, 13),
            10: (2, 13), 11: (2, 13), 12: (3, 12), 13: (3, 12), 14: (4, 11)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["6"]); s.px(x0, y, C["7"]); s.px(x0 + 1, y, C["7"]); s.px(x1, y, C["5"])
    s.line(6, 4, 9, 4, C["K"]); s.px(5, 5, C["K"])
    s.rect(6, 1, 9, 2, C["5"]); s.px(7, 1, C["6"])
    for y in (7, 9, 11):
        s.px(8 + (y // 2) % 2, y, C["5"])
    s.rect(11, 6, 12, 8, C["9"]); s.px(12, 7, C["3"])
    s.line(4, 15, 12, 15, C["2"])
    s.outline(C["K"], where="inside")
    s.line(4, 15, 12, 15, C["2"])
    chip(s, 13, 12); chip(s, 0, 12)
    return s


def prop_chair():
    s = new()
    s.rect(1, 3, 4, 3, C["5"]); s.rect(1, 12, 4, 12, C["4"])
    s.line(1, 3, 1, 12, C["4"]); s.line(3, 3, 3, 12, C["4"]); s.px(1, 4, C["5"]); s.px(3, 4, C["5"])
    s.rect(5, 5, 9, 10, C["4"]); s.line(5, 5, 9, 5, C["5"]); s.line(5, 5, 5, 10, C["5"]); s.line(5, 10, 9, 10, C["3"]); s.line(9, 6, 9, 10, C["3"])
    s.px(7, 7, C["3"]); s.px(7, 8, C["3"])
    s.line(10, 6, 14, 6, C["5"]); s.line(10, 7, 14, 7, C["3"])
    s.line(10, 10, 14, 10, C["5"]); s.line(10, 11, 14, 11, C["3"])
    s.line(12, 8, 12, 9, C["4"])
    s.line(2, 13, 9, 13, C["2"])
    s.outline(C["K"], where="inside")
    s.line(2, 13, 9, 13, C["2"])
    s.px(1, 3, C["5"]); s.px(2, 3, C["5"]); s.px(5, 5, C["5"]); s.px(6, 5, C["5"])
    return s


def prop_lantern():
    s = new()
    s.line(11, 3, 11, 13, C["5"]); s.line(12, 3, 12, 13, C["4"])
    s.rect(9, 14, 14, 14, C["5"]); s.rect(8, 15, 15, 15, C["3"])
    s.line(7, 1, 12, 1, C["5"]); s.px(6, 2, C["5"]); s.px(12, 2, C["4"])
    s.px(6, 3, C["6"])
    prof = {4: (5, 7), 5: (4, 8), 6: (3, 9), 7: (3, 9), 8: (3, 9), 9: (3, 9), 10: (4, 8), 11: (5, 7)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["B"])
    s.rect(5, 6, 7, 9, C["L"]); s.px(4, 7, C["L"]); s.px(4, 8, C["L"])
    s.px(6, 7, C["W"]); s.px(6, 8, C["W"])
    for y in (6, 9):
        s.px(3, y, C["6"]); s.px(9, y, C["6"])
    s.line(5, 4, 7, 4, C["6"]); s.line(5, 11, 7, 11, C["6"]); s.px(6, 12, C["6"]); s.px(6, 13, C["5"])
    s.outline(C["K"], where="inside")
    s.line(8, 1, 11, 1, C["5"], only=C["K"])
    return s


def prop_ledger():
    """빚 장부(통과): 펼쳐진 두꺼운 장부. 종이 G09(윗장 G12), 글줄 K 점선, 가죽 표지 G04, 잉크 얼룩 B 2px (D1 '외상 장부에 내 이름이 있다')."""
    s = new()
    s.rect(2, 5, 13, 12, C["4"])                       # 표지
    s.rect(3, 4, 7, 11, C["9"]); s.rect(8, 4, 12, 11, C["9"])
    s.line(3, 4, 7, 4, C["C"]); s.line(8, 4, 12, 4, C["C"]); s.line(3, 4, 3, 11, C["C"])
    s.line(7, 4, 7, 11, C["6"]); s.line(8, 5, 8, 11, C["7"])   # 가운데 접힘
    for y in (6, 8, 10):
        s.px(4, y, C["3"]); s.px(5, y, C["3"]); s.px(9, y, C["3"]); s.px(10, y, C["3"]); s.px(11, y, C["3"])
    s.px(5, 8, C["B"]); s.px(6, 8, C["B"]); s.px(6, 9, C["S"])   # 잉크 얼룩 (이름이 있던 자리)
    s.line(3, 13, 14, 13, C["2"])
    s.outline(C["K"], where="inside")
    s.line(3, 13, 14, 13, C["2"])
    s.line(4, 4, 6, 4, C["C"], only=C["K"]); s.line(9, 4, 11, 4, C["C"], only=C["K"])
    return s


def prop_cage():
    """쇠우리(solid): 빚진 자를 가두는 우리. 쇠살 G06/G05, 안쪽 K, 안에 웅크린 사람의 창백한 손·얼굴 G09 (처절하게)."""
    s = new()
    s.rect(3, 2, 12, 13, C["K"])
    for x in (3, 6, 9, 12):
        s.line(x, 2, x, 13, C["6"]); s.px(x, 2, C["7"])
    s.line(3, 2, 12, 2, C["6"]); s.line(3, 13, 12, 13, C["5"]); s.line(3, 7, 12, 7, C["5"])
    s.px(7, 8, C["9"]); s.px(8, 8, C["9"]); s.px(7, 9, C["9"]); s.px(8, 9, C["9"])   # 얼굴
    s.px(7, 9, C["3"])                                                                # 꺼진 눈
    s.px(10, 11, C["9"]); s.px(11, 10, C["9"])                                        # 손
    s.px(4, 11, C["9"])
    s.rect(2, 14, 13, 14, C["4"]); s.line(2, 15, 13, 15, C["2"])
    s.outline(C["K"], where="inside")
    s.rect(3, 14, 12, 14, C["4"]); s.line(2, 15, 13, 15, C["2"])
    s.line(4, 2, 11, 2, C["6"], only=C["K"])
    return s


def prop_card_table():
    """엎어진 노름판(solid): 둥근 탁자가 옆으로 넘어져 상판(G04 원, 테 G05, 펠트 자국 S 반원)이 정면으로 보이고 다리 둘(G03)이 뻗었다.
    '판은 끝나지 않았다' — 상판에 못 박힌 패 한 장(G06)."""
    s = new()
    s.circle(7, 8, 6, C["4"], fill=True)
    s.circle(7, 8, 6, C["5"], fill=False)
    for y in range(5, 12):
        half = 4 - abs(y - 8) // 2
        s.line(7 - half, y, 7 + half, y, C["S"], only=C["4"])             # 펠트 자국
    s.px(4, 4, C["6"]); s.px(5, 3, C["6"])                                # 윗 테 빛
    s.rect(6, 6, 8, 8, C["6"]); s.px(7, 7, C["3"]); s.px(6, 6, C["7"])    # 못 박힌 패
    s.line(13, 5, 15, 3, C["3"]); s.line(13, 11, 15, 13, C["3"])          # 뻗은 다리
    s.px(14, 4, C["4"]); s.px(14, 12, C["4"])
    s.line(3, 14, 11, 14, C["2"])
    s.outline(C["K"], where="inside")
    s.line(3, 14, 11, 14, C["2"]); s.px(14, 4, C["4"]); s.px(14, 12, C["4"])
    s.px(5, 3, C["6"], only=C["K"])
    return s


def prop_chip_scatter():
    """흩어진 칩과 패(통과): 판이 엎어지며 쏟아진 것 — 칩(B/L) 넷, 패(G06, 흙 묻음) 둘, 주사위(G07) 하나. 작은 것들이라 바닥에 묻혀 간다."""
    s = new()
    chip(s, 3, 4); chip(s, 11, 3); chip(s, 7, 10); chip(s, 12, 12)
    s.rect(6, 5, 8, 7, C["6"]); s.px(6, 5, C["7"]); s.px(7, 6, C["3"]); s.px(8, 7, C["2"]); s.px(9, 8, C["K"]); s.px(6, 8, C["K"])
    s.rect(2, 10, 4, 12, C["6"]); s.px(3, 11, C["3"]); s.px(4, 12, C["1"]); s.px(5, 13, C["K"]); s.px(2, 13, C["K"])
    s.rect(10, 7, 11, 8, C["7"]); s.px(10, 7, C["K"]); s.px(12, 9, C["2"])
    return s


def void_tile():
    return new()


TILES = (
    [("floor_%d" % i, common_floor(i)) for i in range(4)]
    + [("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
       ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
       ("exit", exit_stairs()), ("shop", shop_counter()),
       ("prop_dice_cup", prop_dice_cup()), ("prop_sack", prop_sack()), ("prop_chair", prop_chair()),
       ("prop_lantern", prop_lantern()), ("prop_ledger", prop_ledger()), ("prop_cage", prop_cage()),
       ("prop_card_table", prop_card_table()), ("prop_chip_scatter", prop_chip_scatter()),
       ("wall_v1", wall_v1()), ("wall_v2", wall_v2())]
    + [("start_%d" % i, start_floor(i)) for i in range(4)]
    + [("trial_%d" % i, trial_floor(i)) for i in range(4)]
    + [("rest_%d" % i, rest_floor(i)) for i in range(4)]
    + [("boss_%d" % i, boss_floor(i)) for i in range(4)]
    + [("reserve", void_tile())]
)
# (short, solid, maxPerRoom, weight) — 40라운드
PROPS = [("dice_cup", False, 3, 1.0), ("stake_sack", True, 2, 0.8), ("overturned_chair", False, 2, 0.8), ("green_lantern", True, 1, 0.6),
         ("debt_ledger", False, 1, 0.6), ("iron_cage", True, 1, 0.4), ("card_table", True, 1, 0.4), ("chip_scatter", False, 3, 1.0)]

if __name__ == "__main__":
    tc.run(2, "패(牌) — 도박장 제국 외곽", TILES, PROPS, [19, 21, 23, 25], HERE)
