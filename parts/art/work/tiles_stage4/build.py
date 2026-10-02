#!/usr/bin/env python3
"""LOPAD 4층 '계(契)' 용병 제국 타일셋 (16x16) — 37라운드 재작업. 단일 소스, 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage4/build.py
산출: assets/tiles/stage4.png (8x4) / stage4.json — 인덱스 표는 tilecommon2.py
      parts/art/work/tiles_stage4/preview.png · preview_room.png · preview_rooms.png · preview_seam.png

컨셉 (text-pack B4·D4): "화승총 연기 너머로 계약서가 나부낀다." 바닥 = 짙은 진흙(G01 + G02 덩어리 + 박힌 돌 G03)
  + 탄피(G06/G09 2px) + 계약서 조각(G07, 반쯤 묻힘) + 잔불. 벽 = 모래주머니(G02, 틈 K) / 변형 1 = 제국 표식(못 박은 계약서 + 밀랍 봉인 B/S)
  / 변형 2 = 터진 자루에서 흘러내린 모래 + 걸어 둔 화약 뿔. 소품 6 = 거치대·계약서 뭉치·깃발·모닥불 자국 + 화약통(solid)·부러진 장창(통과).
색 예산: 무채 10 (K, G01~G07, G09, G12) + 강조 4 (19 shadow1 피·밀랍 그늘, 21 base 깃발·밀랍·잉걸, 23 light1, 25 glow).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon2 as tc  # noqa: E402

G = tc.G
A = tc.ramp(4)
T = tc.T

C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
    "S": A[3],   # 19 shadow1 — 말라붙은 피·밀랍 그늘
    "B": A[5],   # 21 base   — 깃발·밀랍·잉걸
    "L": A[7],   # 23 light1 — 깃발 빛·불티
    "W": A[9],   # 25 glow   — 잉걸 심
}
ctx = tc.Ctx(C)
new = ctx.new


# ============================================================ 바닥 (진흙 + 돌)
DOTS = {"K": 18, "2": 20, "3": 4}
PAIRS = {"2": 3, "K": 2}


def shell(s, x, y):
    """탄피 2px: 놋쇠 G05 + 끝 빛 G07 (G09 는 1x 에서 불티처럼 튀어 낮췄다)."""
    s.px(x, y, C["5"]); s.px(x + 1, y, C["7"])


def scrap(s, x, y, buried=True):
    """계약서 조각 3x3: 종이 G07, 글줄 G03, 우·하 K. buried 면 아랫줄이 진흙(G02)에 덮인다."""
    s.rect(x, y, x + 2, y + 2, C["7"]); s.px(x + 1, y + 1, C["3"])
    s.line(x, y + 3, x + 3, y + 3, C["K"]); s.line(x + 3, y, x + 3, y + 3, C["K"])
    if buried:
        s.px(x, y + 2, C["2"]); s.px(x + 2, y + 2, C["1"]); s.px(x + 3, y + 3, C["1"])


def stone(s, x, y):
    s.px(x, y, C["3"]); s.px(x + 1, y, C["3"]); s.px(x + 1, y + 1, C["2"]); s.px(x, y + 1, C["K"])


def common_floor(i):
    s, rnd = tc.dirt(ctx, seed=100 + i, base="1", dots=DOTS, pairs=PAIRS)
    if i == 0:
        shell(s, 4, 9)
        stone(s, 7, 12); stone(s, 11, 4)
    elif i == 1:
        scrap(s, 9, 7)
        tc.ember_small(s, C, 3, 4)
    elif i == 2:
        stone(s, 3, 3); stone(s, 11, 10); stone(s, 8, 6)
        s.px(5, 12, C["2"]); s.px(6, 12, C["2"])
    else:
        s.px(6, 9, C["S"]); s.px(7, 10, C["S"]); s.px(4, 8, C["S"])   # 튄 피 방울만 (덩어리는 시련 방에서)
        tc.ember(s, C, 12, 4, rising=True)
    return s


def corridor_tile():
    """복도: 보급 마차가 다진 진흙 — 더 검고, 바퀴에 눌린 자국은 선이 아니라 K 덩어리로."""
    s, rnd = tc.dirt(ctx, seed=140, base="1", dots={"K": 40, "2": 10}, pairs={"K": 5})
    return s


def start_floor(i):
    s, rnd = tc.dirt(ctx, seed=200 + i, base="1", dots={"K": 14, "2": 18, "3": 4}, pairs={"2": 3})
    if i == 0:
        tc.bootprint(s, C, 3, 3, left=True); tc.bootprint(s, C, 7, 6, left=False); tc.bootprint(s, C, 11, 2, left=True)
        shell(s, 12, 12)
    else:
        for x0, y0, dx in [(2, 10, 1), (5, 12, 1), (3, 13, 1), (7, 9, 0), (6, 11, 1)]:
            s.px(x0, y0, C["3"]); s.px(x0 + dx, y0 + (1 - dx), C["3"])
        tc.ash_patch(s, C, rnd, 11, 4, r=2); tc.ember_small(s, C, 11, 4)
        tc.bootprint(s, C, 12, 10, left=False)
    return s


def trial_floor(i):
    s, rnd = tc.dirt(ctx, seed=300 + i, base="1", dots={"K": 24, "2": 14, "3": 3}, pairs={"2": 2, "K": 3})
    if i == 0:
        tc.splat(s, C, rnd, 5, 5, r=2, dark="S", wet="B", drops=3)
        tc.pock(s, C, 11, 10)
        shell(s, 9, 2); shell(s, 12, 4)
    else:
        tc.pock(s, C, 11, 3); tc.pock(s, C, 4, 11)
        s.px(7, 8, C["S"]); s.px(13, 9, C["S"]); s.px(2, 5, C["S"]); s.px(8, 13, C["S"])
        shell(s, 13, 12); shell(s, 3, 7)
    return s


def rest_floor(i):
    s, rnd = tc.dirt(ctx, seed=400 + i, base="1", dots={"K": 10, "2": 20, "3": 5}, pairs={"2": 3})
    if i == 0:
        tc.ash_patch(s, C, rnd, 8, 8, r=3); s.px(8, 7, C["L"])
        s.px(3, 12, C["3"]); s.px(4, 12, C["3"])
    else:
        tc.ash_patch(s, C, rnd, 4, 4, r=2)
        stone(s, 10, 10); shell(s, 12, 5)
    return s


SEAL = [(2, 0), (3, 0), (1, 1), (4, 1), (0, 2), (5, 2), (0, 3), (5, 3), (1, 4), (4, 4), (2, 5), (3, 5), (2, 2), (3, 3)]  # 봉인 고리 6x6 + 안 사선


def boss_floor(i):
    s, rnd = tc.dirt(ctx, seed=500 + i, base="1", dots={"K": 18, "2": 14, "3": 3}, pairs={"2": 2})
    if i == 0:
        tc.buried_slab(s, C, rnd, (2, 2, 9, 8), carve=[(x + 3, y + 2) for x, y in SEAL if y < 5], bury_from=0.7)
        for x, y in [(2, 2), (3, 2), (2, 3), (9, 2), (2, 8), (2, 7), (3, 8), (9, 8), (9, 7), (8, 8)]:
            s.px(x, y, C["1"])
        s.px(12, 11, C["2"]); s.px(13, 11, C["3"]); s.px(13, 12, C["2"])
    else:
        for x, y, ch in [(10, 3, "2"), (11, 3, "3"), (12, 3, "2"), (11, 4, "2"), (4, 10, "2"), (5, 10, "3"), (5, 11, "2"), (4, 11, "K"), (13, 13, "2")]:
            s.px(x, y, C[ch])
        scrap(s, 6, 6)
        s.px(8, 7, C["B"]); s.px(8, 8, C["S"])                        # 조각 위 밀랍
    return s


# ============================================================ 벽 (모래주머니 G02, 틈 K)
def sandbag_row(s, y, off, body="2", hi="3"):
    s.line(0, y, T - 1, y, C["K"])
    for x0 in range(off - 8, T, 8):
        x1 = x0 + 7
        for yy in range(y + 1, y + 4):
            s.line(max(x0, 0), yy, min(x1, T - 1), yy, C[body])
        if 0 <= x0 + 1 <= T - 1:
            s.line(max(x0 + 1, 0), y + 1, min(x1 - 1, T - 1), y + 1, C[hi])
        for x in (x0, x1):
            if 0 <= x < T:
                s.px(x, y + 1, C["K"]); s.px(x, y + 2, C["K"]); s.px(x, y + 3, C["K"])


def wall_base(s):
    s.rect(0, 0, T - 1, T - 1, C["K"])
    for i in range(4):
        sandbag_row(s, i * 4, 0 if i % 2 == 0 else 4)
    s.px(3, 6, C["1"]); s.px(4, 6, C["1"]); s.px(12, 10, C["1"])    # 젖은 자리
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_face():
    s = new()
    wall_base(s)
    s.px(10, 10, C["3"]); s.px(10, 11, C["3"]); s.px(11, 12, C["3"])   # 흘러내린 모래 조금
    return s


def wall_v1():
    """제국 표식: 자루에 못 박은 계약서(G07, 윗장 G09) + 밀랍 봉인(B/S 4px). '계약서가 깃발이다'."""
    s = new()
    wall_base(s)
    s.rect(5, 3, 10, 11, C["7"]); s.line(5, 3, 10, 3, C["9"]); s.line(5, 3, 5, 11, C["9"])
    s.line(6, 12, 11, 12, C["K"]); s.line(11, 4, 11, 12, C["K"])
    s.px(7, 2, C["6"])                                              # 못
    for y in (5, 7):
        s.px(6, y, C["3"]); s.px(7, y, C["3"]); s.px(8, y, C["3"])
    s.px(8, 9, C["B"]); s.px(9, 9, C["B"]); s.px(8, 10, C["B"]); s.px(9, 10, C["S"])
    s.px(10, 11, C["4"])                                            # 찢어진 귀
    return s


def wall_v2():
    """걸린 사물·파손: 터진 자루에서 모래가 흘러내리고(G03/G04), 자루 틈에 꽂아 둔 화약 뿔(G06/G07)."""
    s = new()
    wall_base(s)
    for x, y in [(4, 6), (5, 6), (3, 7), (4, 7), (5, 7), (6, 7), (4, 8), (5, 8), (3, 9), (5, 9), (6, 10), (4, 11), (5, 12), (4, 13)]:
        s.px(x, y, C["3"])
    for x, y in [(4, 6), (5, 7), (4, 9), (5, 11)]:
        s.px(x, y, C["4"])
    s.px(5, 5, C["K"]); s.px(6, 5, C["K"]); s.px(4, 5, C["1"])     # 터진 자리
    s.line(10, 9, 13, 6, C["6"]); s.line(10, 10, 13, 7, C["6"]); s.px(13, 6, C["7"]); s.px(10, 10, C["5"]); s.px(9, 10, C["5"])
    s.px(11, 5, C["4"]); s.px(12, 5, C["4"])                        # 걸이 끈
    return s


def wall_top():
    """벽 윗면: 말뚝 울타리 위에서 본 것. 땅 G03, 가로대 G02 2줄, 말뚝 머리 G04/G05."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    s.line(0, 0, T - 1, 0, C["K"])
    s.rect(0, 7, T - 1, 8, C["2"])
    for x in (1, 5, 9, 13):
        s.rect(x, 6, x + 1, 9, C["4"]); s.px(x, 6, C["5"]); s.px(x + 1, 6, C["5"])
    s.px(4, 3, C["2"]); s.px(12, 13, C["2"]); s.px(13, 13, C["2"])
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
    tc.scatter(s, C, rnd, "K", 14, box=(5, 2, 12, 15)); tc.scatter(s, C, rnd, "2", 5, box=(5, 2, 12, 15))
    s.rect(3, 2, 4, 14, C["5"]); s.line(4, 2, 4, 14, C["4"])
    s.px(3, 5, C["7"]); s.px(3, 12, C["7"]); s.px(4, 5, C["6"]); s.px(4, 12, C["6"])
    s.line(3, 15, 4, 15, C["2"])
    s.line(5, 3, 5, 13, C["L"])
    return s


def gate(s):
    s.rect(3, 2, 12, 15, C["4"])
    for y in (5, 9, 13):
        s.line(3, y, 12, y, C["2"]); s.line(3, y + 1, 12, y + 1, C["5"])
    s.line(3, 2, 12, 2, C["5"])
    s.line(3, 3, 12, 12, C["5"]); s.line(3, 12, 12, 3, C["5"])
    s.line(4, 3, 12, 11, C["3"], only=C["4"]); s.line(4, 12, 12, 4, C["3"], only=C["4"])


def door_closed():
    s = new()
    door_frame(s); gate(s)
    s.px(10, 8, C["7"]); s.px(10, 9, C["K"])
    return s


def door_locked():
    s = new()
    door_frame(s); gate(s)
    for x in range(2, 14):
        s.px(x, 7, C["7"] if x % 2 == 0 else C["6"])
    s.px(2, 8, C["5"]); s.px(13, 8, C["5"])
    s.rect(6, 8, 9, 12, C["9"]); s.px(6, 8, C["C"]); s.line(6, 13, 10, 13, C["2"]); s.line(10, 8, 10, 13, C["2"])
    s.px(7, 9, C["3"]); s.px(8, 9, C["3"])
    s.px(7, 11, C["B"]); s.px(8, 11, C["B"]); s.px(7, 12, C["B"]); s.px(8, 12, C["S"])
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
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["1"]); s.line(0, y + 1, T - 1, y + 1, C["4"])
    s.line(0, 15, T - 1, 15, C["1"])
    s.line(1, 3, 10, 3, C["7"]); s.line(1, 4, 10, 4, C["1"])
    s.rect(10, 3, 14, 4, C["5"]); s.px(13, 5, C["5"]); s.px(14, 5, C["5"]); s.line(10, 5, 12, 5, C["1"]); s.px(13, 6, C["1"]); s.px(14, 6, C["1"])
    s.px(9, 2, C["6"])
    s.rect(2, 8, 6, 12, C["9"]); s.line(2, 8, 6, 8, C["C"]); s.line(2, 13, 7, 13, C["1"]); s.line(7, 8, 7, 13, C["1"])
    s.px(3, 10, C["3"]); s.px(4, 10, C["3"])
    s.px(5, 11, C["B"]); s.px(5, 12, C["S"])
    s.line(9, 11, 13, 9, C["6"]); s.line(9, 12, 13, 10, C["6"]); s.px(13, 9, C["7"]); s.px(9, 12, C["5"]); s.px(10, 12, C["5"])
    s.line(10, 13, 13, 11, C["1"])
    return s


# ============================================================ 소품
def prop_musket_rack():
    s = new()
    s.rect(2, 5, 13, 6, C["5"]); s.line(2, 6, 13, 6, C["4"])
    s.line(2, 7, 2, 14, C["4"]); s.line(3, 7, 3, 14, C["5"])
    s.line(12, 7, 12, 14, C["4"]); s.line(13, 7, 13, 14, C["3"])
    s.rect(1, 15, 14, 15, C["3"])
    s.outline(C["K"], where="inside")
    s.rect(1, 15, 14, 15, C["3"]); s.line(3, 5, 12, 5, C["5"], only=C["K"])
    for x in (5, 8, 11):
        s.line(x, 1, x, 11, C["7"]); s.px(x, 2, C["9"])
        s.rect(x - 1, 11, x, 14, C["5"]); s.px(x, 14, C["4"]); s.px(x - 1, 14, C["4"])
        s.px(x + 1, 7, C["6"])
    return s


def prop_contracts():
    s = new()
    s.rect(4, 6, 10, 11, C["9"]); s.line(4, 6, 10, 6, C["C"]); s.line(4, 7, 4, 11, C["C"])
    s.line(5, 12, 11, 12, C["3"]); s.line(11, 7, 11, 12, C["3"])
    s.line(4, 9, 10, 9, C["K"])
    s.px(9, 7, C["B"]); s.px(9, 8, C["S"])
    s.px(5, 8, C["3"]); s.px(5, 10, C["3"])
    s.outline(C["K"], where="inside")
    s.rect(11, 2, 13, 4, C["9"]); s.px(11, 2, C["C"]); s.px(12, 3, C["3"]); s.px(14, 3, C["2"]); s.px(14, 4, C["2"]); s.line(11, 5, 14, 5, C["2"])
    s.rect(1, 12, 3, 13, C["9"]); s.px(2, 13, C["3"]); s.line(1, 14, 4, 14, C["2"]); s.px(4, 13, C["2"])
    s.line(5, 6, 9, 6, C["C"], only=C["K"])
    s.line(5, 12, 11, 12, C["3"]); s.line(11, 7, 11, 12, C["3"])
    return s


def prop_flag():
    s = new()
    s.line(3, 1, 3, 13, C["5"]); s.line(4, 1, 4, 13, C["4"])
    s.px(3, 0, C["7"]); s.px(4, 0, C["7"])
    s.rect(2, 14, 5, 14, C["4"]); s.rect(1, 15, 6, 15, C["3"])
    rows = {2: (5, 12), 3: (5, 13), 4: (5, 13), 5: (5, 12), 6: (5, 11), 7: (5, 12), 8: (5, 10)}
    for y, (x0, x1) in rows.items():
        s.line(x0, y, x1, y, C["B"])
    s.line(5, 2, 12, 2, C["L"])
    s.line(6, 8, 10, 8, C["S"]); s.px(12, 7, C["S"]); s.px(11, 6, C["S"]); s.px(13, 4, C["S"])
    s.line(7, 4, 10, 4, C["K"]); s.line(7, 6, 9, 6, C["K"])
    s.outline(C["K"], where="inside")
    s.px(3, 0, C["7"]); s.px(4, 0, C["7"])
    s.line(5, 2, 12, 2, C["L"], only=C["K"])
    s.line(2, 14, 5, 14, C["4"], only=C["K"]); s.line(1, 15, 6, 15, C["3"], only=C["K"])
    return s


def prop_firepit():
    s = new()
    ring = [(5, 3), (6, 3), (8, 3), (9, 3), (3, 5), (3, 6), (12, 5), (12, 6), (2, 8), (2, 9), (13, 8), (13, 9),
            (3, 11), (4, 12), (11, 12), (12, 11), (6, 13), (7, 13), (9, 13)]
    s.rect(3, 4, 12, 12, C["1"]); s.rect(4, 4, 11, 4, C["1"]); s.rect(3, 13, 12, 13, C["1"])
    inner = {5: (5, 10), 6: (4, 11), 7: (4, 11), 8: (4, 11), 9: (4, 11), 10: (5, 10), 11: (6, 9)}
    for y, (x0, x1) in inner.items():
        s.line(x0, y, x1, y, C["K"])
    s.rect(6, 7, 9, 9, C["7"]); s.px(5, 8, C["7"]); s.px(10, 8, C["7"])
    s.px(6, 8, C["1"]); s.px(9, 9, C["1"])
    s.px(7, 8, C["B"]); s.px(8, 8, C["L"]); s.px(8, 7, C["B"]); s.px(7, 9, C["W"])
    s.px(8, 5, C["L"])                                              # 오르는 불티
    for x, y in ring:
        s.px(x, y, C["5"])
    for x, y in [(6, 3), (9, 3), (3, 6), (12, 6), (2, 9), (13, 9), (4, 12), (11, 12), (7, 13)]:
        s.px(x, y, C["6"])
    for x, y in [(4, 3), (10, 3), (11, 3), (5, 13), (10, 13), (11, 13), (2, 7), (13, 7), (2, 10), (13, 10), (3, 4), (12, 4), (3, 12), (12, 12)]:
        s.px(x, y, C["5"])
    return s


def prop_powder_keg():
    """화약통(solid): 작은 통(G04 널, 쇠테 G06) 옆으로 눕힘. 뚜껑에 K 해골 표식 대신 'X' 두 줄, 뚜껑 틈으로 흘린 화약(K 알갱이)."""
    s = new()
    s.rect(2, 5, 12, 12, C["4"])
    for y in (6, 11):
        s.line(2, y, 12, y, C["5"])
    s.line(2, 8, 12, 8, C["3"]); s.line(2, 9, 12, 9, C["3"])
    for x in (4, 10):
        s.line(x, 5, x, 12, C["6"]); s.px(x, 6, C["7"])
    s.rect(12, 4, 13, 13, C["5"]); s.line(13, 4, 13, 13, C["3"])         # 뚜껑 (오른쪽 끝)
    s.px(12, 7, C["K"]); s.px(12, 10, C["K"]); s.px(13, 8, C["K"]); s.px(13, 9, C["K"])   # X 표식
    s.px(14, 11, C["K"]); s.px(15, 12, C["K"]); s.px(14, 13, C["K"]); s.px(13, 14, C["1"])  # 흘린 화약
    s.line(3, 13, 12, 13, C["2"])
    s.outline(C["K"], where="inside")
    s.line(3, 13, 12, 13, C["2"]); s.line(3, 5, 11, 5, C["5"], only=C["K"])
    s.px(14, 11, C["K"]); s.px(15, 12, C["K"]); s.px(14, 13, C["K"])
    return s


def prop_broken_pike():
    """부러진 장창(통과): 사선으로 누운 자루(G05/G04) 가운데가 부러져 어긋나고, 창날(G07/G09)은 흙에 꽂혀 있다."""
    s = new()
    for i in range(6):
        s.px(2 + i, 12 - i, C["5"]); s.px(3 + i, 12 - i, C["4"])
    for i in range(5):
        s.px(9 + i, 7 - i, C["5"]); s.px(10 + i, 7 - i, C["4"])
    s.px(8, 8, C["3"]); s.px(8, 7, C["3"])                                # 부러진 자리 (쪼개짐)
    s.px(13, 2, C["7"]); s.px(14, 1, C["9"]); s.px(14, 2, C["7"]); s.px(13, 3, C["6"])   # 창날
    s.px(1, 13, C["3"]); s.px(2, 14, C["2"])                              # 흙에 묻힌 끝
    s.outline(C["K"], where="inside")
    s.px(14, 1, C["9"]); s.px(13, 2, C["7"])
    for i in range(1, 6):
        s.px(2 + i, 12 - i, C["5"])
    for i in range(1, 5):
        s.px(9 + i, 7 - i, C["5"])
    return s


def void_tile():
    return new()


TILES = (
    [("floor_%d" % i, common_floor(i)) for i in range(4)]
    + [("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
       ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
       ("exit", exit_stairs()), ("shop", shop_counter()),
       ("prop_musket_rack", prop_musket_rack()), ("prop_contracts", prop_contracts()), ("prop_flag", prop_flag()),
       ("prop_firepit", prop_firepit()), ("prop_powder_keg", prop_powder_keg()), ("prop_broken_pike", prop_broken_pike()),
       ("wall_v1", wall_v1()), ("wall_v2", wall_v2())]
    + [("start_%d" % i, start_floor(i)) for i in range(2)]
    + [("trial_%d" % i, trial_floor(i)) for i in range(2)]
    + [("rest_%d" % i, rest_floor(i)) for i in range(2)]
    + [("boss_%d" % i, boss_floor(i)) for i in range(2)]
)
PROPS = [("musket_rack", True), ("contract_bundle", False), ("flag", True), ("firepit", False),
         ("powder_keg", True), ("broken_pike", False)]

if __name__ == "__main__":
    tc.run(4, "계(契) — 용병 제국 전선", TILES, PROPS, [19, 21, 23, 25], HERE)
