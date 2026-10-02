#!/usr/bin/env python3
"""LOPAD 3층 '붕(繃)' 야전병원 제국 타일셋 (16x16) — 37라운드 재작업. 단일 소스, 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage3/build.py
산출: assets/tiles/stage3.png (8x4) / stage3.json — 인덱스 표는 tilecommon2.py
      parts/art/work/tiles_stage3/preview.png · preview_room.png · preview_rooms.png · preview_seam.png

컨셉 (text-pack B3·D3): "붕대가 모자라 진흙으로 묶었다." 바닥 = 짙은 진흙(G01 바탕 + G02 진흙 덩어리, 1·2층보다 K 가 적다)
  + 피(이 층의 피 = 청록 S/B) + 붕대 조각(G12/G09, 반쯤 묻힘). 벽 = 천막 캔버스(G02, 솔기 K) / 변형 1 = 제국 표식(붕대 십자 G06)
  / 변형 2 = 솔기에서 늘어진 붕대(G12) + 청록 손자국. 소품 6 = 들것·붕대 더미·약병 상자·번호 말뚝 + 천 덮은 시체(solid)·피 양동이(통과).
색 예산: 무채 10 (K, G01~G07, G09, G12) + 강조 4 (19 shadow1 밴 피, 21 base, 23 light1, 25 glow).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon2 as tc  # noqa: E402

G = tc.G
A = tc.ramp(3)
T = tc.T

C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
    "S": A[3],   # 19 shadow1 — 말라붙은 피
    "B": A[5],   # 21 base   — 젖은 피·약
    "L": A[7],   # 23 light1 — 약병 빛·불티
    "W": A[9],   # 25 glow   — 글린트·잔불 심
}
ctx = tc.Ctx(C)
new = ctx.new


# ============================================================ 바닥 (짙은 진흙)
DOTS = {"K": 16, "2": 22, "3": 3}
PAIRS = {"2": 4, "K": 2}


def bandage_scrap(s, pts, buried_at=()):
    """붕대 조각: 진흙에 밟혀 더러워진 붕대 — G09 가닥 + 아래쪽 G07 그늘 (G12 는 1x 에서 흰 불꽃처럼 튀어 낮췄다).
    buried_at 좌표는 진흙(G02)이 덮는다."""
    for x, y in pts:
        s.px(x, y, C["9"])
    for x, y in pts:
        if (x, y + 1) not in pts:
            s.px(x, y + 1, C["7"])
    for x, y in buried_at:
        s.px(x, y, C["2"])


def common_floor(i):
    s, rnd = tc.dirt(ctx, seed=100 + i, base="1", dots=DOTS, pairs=PAIRS)
    if i == 0:
        bandage_scrap(s, [(3, 9), (4, 9), (5, 10), (6, 10), (7, 11)], buried_at=[(7, 11), (7, 12)])
        s.px(12, 4, C["S"]); s.px(13, 4, C["S"])
    elif i == 1:
        tc.stain_small(s, C, rnd, 9, 8, dark="S", n=4)
    elif i == 2:
        # 붕대는 변형 0 에만 (두 변형에 두면 흰 꼬부랑이가 화면을 덮는다). 여기는 자갈 + 거의 묻힌 붕대 끝 1px.
        s.px(11, 4, C["9"]); s.px(12, 5, C["2"])
        s.px(4, 11, C["2"]); s.px(5, 11, C["3"]); s.px(5, 12, C["2"]); s.px(4, 12, C["2"])   # 자갈
        s.px(9, 12, C["3"]); s.px(10, 12, C["2"])
    else:
        tc.bootprint(s, C, 4, 3, left=True)
        s.px(10, 10, C["S"]); s.px(11, 11, C["S"]); s.px(12, 11, C["S"])
    return s


def corridor_tile():
    s, rnd = tc.dirt(ctx, seed=140, base="1", dots={"K": 38, "2": 10}, pairs={"K": 4})
    return s


def start_floor(i):
    s, rnd = tc.dirt(ctx, seed=200 + i, base="1", dots={"K": 14, "2": 20, "3": 3}, pairs={"2": 3})
    if i == 0:
        tc.bootprint(s, C, 3, 3, left=True); tc.bootprint(s, C, 7, 6, left=False); tc.bootprint(s, C, 11, 2, left=True)
        bandage_scrap(s, [(11, 12), (12, 12), (13, 13)])
    else:
        for x0, y0, dx in [(2, 10, 1), (5, 12, 1), (3, 13, 1), (7, 9, 0), (6, 11, 1)]:
            s.px(x0, y0, C["3"]); s.px(x0 + dx, y0 + (1 - dx), C["3"])
        tc.ash_patch(s, C, rnd, 11, 4, r=2); tc.ember_small(s, C, 11, 4)
        tc.bootprint(s, C, 12, 10, left=False)
    return s


def trial_floor(i):
    s, rnd = tc.dirt(ctx, seed=300 + i, base="1", dots={"K": 22, "2": 16, "3": 2}, pairs={"2": 3, "K": 2})
    if i == 0:
        tc.splat(s, C, rnd, 5, 5, r=2, dark="S", wet="B", drops=3)
        tc.pock(s, C, 11, 10)
        bandage_scrap(s, [(9, 2), (10, 2), (11, 3)], buried_at=[(11, 3)])
    else:
        tc.pock(s, C, 11, 3); tc.pock(s, C, 4, 11)
        s.px(7, 8, C["S"]); s.px(13, 9, C["S"]); s.px(2, 5, C["S"]); s.px(8, 13, C["S"])
        bandage_scrap(s, [(12, 12), (13, 12)]); s.px(13, 13, C["S"])    # 피 밴 붕대
    return s


def rest_floor(i):
    s, rnd = tc.dirt(ctx, seed=400 + i, base="1", dots={"K": 10, "2": 20, "3": 4}, pairs={"2": 3})
    if i == 0:
        tc.ash_patch(s, C, rnd, 8, 8, r=3); s.px(8, 7, C["L"])
        s.px(3, 12, C["3"]); s.px(4, 12, C["3"])
    else:
        tc.ash_patch(s, C, rnd, 4, 4, r=2)
        s.rect(10, 10, 12, 11, C["9"]); s.px(10, 11, C["7"]); s.px(11, 12, C["7"]); s.px(12, 12, C["7"])   # 붕대 두루마리 (더러워진 것)
        s.px(12, 5, C["2"]); s.px(13, 6, C["2"])
    return s


CROSS = [(2, 0), (3, 0), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3),
         (2, 4), (3, 4), (2, 5), (3, 5)]   # 붕대 십자 6x6


def boss_floor(i):
    s, rnd = tc.dirt(ctx, seed=500 + i, base="1", dots={"K": 18, "2": 14, "3": 2}, pairs={"2": 2})
    if i == 0:
        tc.buried_slab(s, C, rnd, (2, 2, 9, 8), carve=[(x + 3, y + 2) for x, y in CROSS if y < 5], bury_from=0.7)
        for x, y in [(2, 2), (3, 2), (2, 3), (9, 2), (2, 8), (2, 7), (3, 8), (9, 8), (9, 7), (8, 8)]:
            s.px(x, y, C["1"])
        s.px(12, 11, C["2"]); s.px(13, 11, C["3"]); s.px(13, 12, C["2"])
    else:
        for x, y, ch in [(10, 3, "2"), (11, 3, "3"), (12, 3, "2"), (11, 4, "2"), (4, 10, "2"), (5, 10, "3"), (5, 11, "2"), (4, 11, "K"), (13, 13, "2")]:
            s.px(x, y, C[ch])
        s.px(7, 7, C["S"]); s.px(8, 7, C["S"]); s.px(8, 8, C["B"])
    return s


# ============================================================ 벽 (천막 캔버스 G02, 솔기 K)
def wall_base(s):
    s.rect(0, 0, T - 1, T - 1, C["2"])
    for x in (0, 8):
        s.line(x, 0, x, T - 1, C["K"])
        s.line(x + 1, 0, x + 1, T - 2, C["3"])
    for x in range(2, 16, 2):
        s.px(x, 7, C["1"])                                   # 가로 솔기 바느질
    s.line(4, 2, 6, 5, C["1"]); s.line(12, 9, 14, 13, C["1"])   # 주름
    s.rect(10, 2, 13, 5, C["3"])                            # 기운 조각
    for x, y in [(10, 2), (13, 2), (10, 5), (13, 5)]:
        s.px(x, y, C["1"])
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_face():
    s = new()
    return wall_base(s)


def wall_v1():
    """제국 표식: 캔버스에 찍은 붕대 십자(G06, 닳은 자리 G04). 병원 천막의 표시."""
    s = new()
    wall_base(s)
    s.rect(10, 2, 13, 5, C["2"])                            # 기운 조각 대신 표식
    for x, y in [(10, 2), (13, 2), (10, 5), (13, 5)]:
        s.px(x, y, C["2"])
    for x, y in CROSS:
        s.px(x + 3, y + 4, C["6"])
    s.px(5, 6, C["4"]); s.px(7, 8, C["4"]); s.px(4, 7, C["4"])
    return s


def wall_v2():
    """걸린 사물: 솔기에서 늘어진 붕대(G12/G09, 아래 끝 피 S) + 캔버스에 찍힌 손자국(S)."""
    s = new()
    wall_base(s)
    for x, y in [(9, 0), (9, 1), (10, 2), (10, 3), (10, 4), (11, 5), (11, 6), (11, 7), (10, 8), (10, 9), (10, 10), (11, 11), (11, 12)]:
        s.px(x, y, C["C"])
    for x, y in [(10, 1), (11, 3), (12, 6), (11, 9), (12, 12)]:
        s.px(x, y, C["9"])
    s.px(11, 13, C["S"]); s.px(12, 13, C["S"]); s.px(11, 14, C["S"])
    for x, y in [(3, 5), (4, 4), (5, 4), (6, 5), (3, 6), (4, 6), (5, 6), (6, 6), (4, 7), (5, 7), (4, 8), (5, 9), (2, 7)]:
        s.px(x, y, C["S"])                                   # 손자국
    return s


def wall_top():
    """벽 윗면: 천막 지붕 G03, 폭 이음 K, 빛 G04, 당김줄 G02 점선 + 말뚝 K."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    for y in (0, 8):
        s.line(0, y, T - 1, y, C["K"]); s.line(0, y + 1, T - 1, y + 1, C["4"])
    s.line(6, 0, 6, 7, C["K"]); s.line(13, 8, 13, 15, C["K"])
    for x in range(1, 16, 3):
        s.px(x, 4, C["2"]); s.px(x + 1, 12, C["2"])
    s.px(3, 5, C["K"]); s.px(11, 11, C["K"])
    return s


# ============================================================ 문 (천막 자락)
def door_frame(s):
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["3"]); s.line(0, 0, 0, T - 1, C["K"]); s.line(1, 0, 1, T - 1, C["4"])
    s.rect(13, 0, 15, T - 1, C["3"]); s.line(15, 0, 15, T - 1, C["K"]); s.line(13, 0, 13, T - 1, C["2"])
    s.rect(0, 0, T - 1, 1, C["3"]); s.line(0, 0, T - 1, 0, C["K"]); s.line(3, 1, 12, 1, C["4"])


def door_open():
    """열린 문: 자락을 왼쪽 기둥에 말아 묶었다. 틀 안은 어두운 진흙 통로, 틈으로 청록빛 한 줄."""
    s = new()
    door_frame(s)
    s.rect(3, 2, 12, 15, C["1"])
    rnd = random.Random(9)
    tc.scatter(s, C, rnd, "K", 10, box=(6, 2, 12, 15)); tc.scatter(s, C, rnd, "2", 8, box=(6, 2, 12, 15))
    s.rect(3, 2, 5, 13, C["2"]); s.line(3, 2, 3, 13, C["3"]); s.px(3, 3, C["5"]); s.px(3, 6, C["5"]); s.px(3, 9, C["5"])
    s.px(4, 5, C["K"]); s.px(4, 10, C["K"])
    s.rect(3, 14, 5, 15, C["3"])
    s.line(6, 3, 6, 13, C["L"])
    return s


def door_flap(s):
    s.rect(3, 2, 12, 15, C["2"])
    for x in (5, 9):
        s.line(x, 2, x, 13, C["K"])
    s.line(3, 2, 3, 14, C["3"]); s.line(6, 2, 6, 10, C["3"]); s.line(10, 2, 10, 8, C["3"])
    s.rect(3, 14, 12, 15, C["3"]); s.px(7, 14, C["2"]); s.px(11, 15, C["2"])


def door_closed():
    s = new()
    door_frame(s); door_flap(s)
    s.rect(6, 7, 9, 8, C["C"]); s.px(7, 6, C["C"]); s.px(8, 9, C["C"]); s.px(9, 8, C["9"]); s.px(6, 8, C["9"])
    return s


def door_locked():
    s = new()
    door_frame(s); door_flap(s)
    for i in range(10):
        x = 3 + i
        s.px(x, 3 + i, C["5"]); s.px(x, 4 + i, C["4"])
    for i in range(10):
        x = 3 + i
        s.px(x, 13 - i, C["5"]); s.px(x, 14 - i, C["4"])
    for x, y in [(4, 4), (11, 11), (4, 12), (11, 4)]:
        s.px(x, y, C["9"])
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


def vial(s, x, y, h=5):
    s.rect(x, y, x + 1, y + h - 1, C["7"])
    s.rect(x, y + 2, x + 1, y + h - 1, C["B"])
    s.px(x + 1, y + h - 1, C["S"]); s.px(x + 1, y + h - 2, C["S"])
    s.px(x, y + 1, C["W"])
    s.px(x, y - 1, C["5"]); s.px(x + 1, y - 1, C["5"])


def bandage_roll(s, x, y):
    s.rect(x, y, x + 3, y + 2, C["C"])
    s.line(x, y + 2, x + 3, y + 2, C["9"]); s.px(x + 3, y + 1, C["9"]); s.px(x + 1, y + 1, C["9"])


def shop_counter():
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["1"]); s.line(0, y + 1, T - 1, y + 1, C["4"])
    s.line(0, 15, T - 1, 15, C["1"])
    vial(s, 3, 4, 6); vial(s, 7, 3, 7)
    s.line(3, 10, 4, 10, C["1"]); s.line(7, 10, 8, 10, C["1"])
    bandage_roll(s, 10, 6); s.line(10, 9, 13, 9, C["1"])
    bandage_roll(s, 3, 12)
    s.px(10, 12, C["9"]); s.px(11, 12, C["9"]); s.px(12, 12, C["C"]); s.px(12, 13, C["9"])
    return s


# ============================================================ 소품
def prop_stretcher():
    s = new()
    s.rect(1, 5, 14, 11, C["6"]); s.line(1, 5, 14, 5, C["7"]); s.line(2, 11, 14, 11, C["5"])
    s.rect(8, 7, 10, 9, C["S"]); s.px(7, 8, C["S"]); s.px(9, 10, C["S"]); s.px(9, 8, C["B"])   # 밴 피 (청록)
    s.rect(0, 3, 15, 4, C["5"]); s.line(0, 4, 15, 4, C["4"])
    s.rect(0, 12, 15, 13, C["5"]); s.line(0, 13, 15, 13, C["4"])
    for x in (0, 15):
        s.px(x, 3, C["7"]); s.px(x, 12, C["7"])
    s.rect(3, 6, 6, 8, C["9"]); s.px(4, 7, C["3"]); s.px(6, 7, C["3"])
    s.line(2, 14, 13, 14, C["2"])
    s.outline(C["K"], where="inside")
    s.line(2, 14, 13, 14, C["2"])
    s.line(1, 3, 14, 3, C["5"], only=C["K"]); s.line(1, 12, 14, 12, C["5"], only=C["K"])
    return s


def prop_bandages():
    s = new()
    prof = {4: (6, 9), 5: (4, 11), 6: (3, 12), 7: (2, 13), 8: (2, 13), 9: (2, 13), 10: (3, 13), 11: (4, 12), 12: (6, 11)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["C"])
    s.line(4, 6, 8, 6, C["9"]); s.line(9, 8, 12, 8, C["9"]); s.line(3, 10, 7, 10, C["9"]); s.px(8, 11, C["9"])
    s.line(6, 12, 11, 12, C["9"]); s.px(12, 11, C["9"]); s.px(13, 10, C["9"])
    s.rect(5, 7, 6, 8, C["B"]); s.px(7, 8, C["S"]); s.px(5, 9, C["S"])
    s.px(10, 10, C["B"]); s.px(11, 10, C["B"]); s.px(11, 11, C["S"]); s.px(9, 5, C["B"])
    s.px(13, 12, C["C"]); s.px(13, 13, C["C"]); s.px(14, 13, C["C"]); s.px(14, 14, C["9"])
    s.line(3, 13, 12, 13, C["2"])
    s.outline(C["K"], where="inside")
    s.line(3, 13, 12, 13, C["2"])
    s.px(13, 12, C["C"]); s.px(13, 13, C["9"]); s.px(14, 13, C["C"]); s.px(14, 14, C["9"])
    s.line(7, 4, 8, 4, C["C"], only=C["K"])
    return s


def prop_vial_crate():
    s = new()
    s.rect(2, 6, 13, 14, C["4"])
    s.line(2, 6, 13, 6, C["5"]); s.line(2, 6, 2, 14, C["5"]); s.line(3, 14, 13, 14, C["3"]); s.line(13, 7, 13, 14, C["3"])
    s.line(2, 10, 13, 10, C["2"]); s.px(7, 11, C["2"]); s.px(7, 12, C["2"]); s.px(7, 13, C["2"])
    s.rect(3, 4, 12, 5, C["6"]); s.px(5, 4, C["7"]); s.px(9, 5, C["7"]); s.px(11, 4, C["5"])
    s.line(3, 15, 13, 15, C["2"])
    s.outline(C["K"], where="inside")
    s.line(3, 15, 13, 15, C["2"]); s.line(4, 4, 11, 4, C["6"], only=C["K"])
    for x in (4, 7, 10):
        s.rect(x, 2, x + 1, 5, C["7"]); s.px(x, 1, C["5"]); s.px(x + 1, 1, C["5"])
        s.px(x, 4, C["B"]); s.px(x + 1, 4, C["B"]); s.px(x + 1, 5, C["S"]); s.px(x, 5, C["B"])
        s.px(x, 2, C["W"]); s.px(x + 1, 3, C["6"])
    return s


def prop_number_stake():
    s = new()
    s.line(7, 6, 7, 13, C["5"]); s.line(8, 6, 8, 13, C["4"]); s.px(7, 14, C["4"]); s.px(8, 14, C["3"])
    s.rect(4, 2, 11, 6, C["9"]); s.line(4, 6, 11, 6, C["7"]); s.px(11, 5, C["7"])
    s.line(5, 3, 5, 5, C["3"]); s.line(7, 3, 7, 5, C["3"]); s.line(9, 3, 9, 5, C["3"]); s.px(10, 5, C["3"])
    s.rect(5, 15, 10, 15, C["2"]); s.px(6, 14, C["2"]); s.px(9, 14, C["2"])
    s.outline(C["K"], where="inside")
    s.rect(5, 15, 10, 15, C["2"]); s.px(6, 14, C["2"]); s.px(9, 14, C["2"])
    s.line(5, 2, 10, 2, C["9"], only=C["K"])
    return s


def prop_shrouded_body():
    """천 덮은 시체(solid): 들것도 번호도 없이 바닥에 뉘어 천(G09, 능선 G12)을 덮었다. 왼쪽 머리 둔덕, 오른쪽 군화 끝(G04).
    머리 쪽 천에 피가 배었다(S/B). 가로로 길게(1..14) 눕혀 '사람 길이' 로 읽히게."""
    s = new()
    prof = {6: (2, 5), 7: (1, 7), 8: (1, 12), 9: (1, 13), 10: (2, 13), 11: (3, 12)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["9"])
    s.line(2, 6, 5, 6, C["C"]); s.px(1, 7, C["C"]); s.line(6, 7, 7, 7, C["C"]); s.line(8, 8, 12, 8, C["C"])   # 능선 빛
    s.px(9, 9, C["7"]); s.px(10, 10, C["7"]); s.px(5, 10, C["7"]); s.px(6, 9, C["7"])                       # 주름
    s.rect(2, 8, 3, 9, C["S"]); s.px(4, 9, C["S"]); s.px(3, 8, C["B"]); s.px(2, 10, C["S"])               # 밴 피 (머리 쪽)
    s.rect(13, 9, 14, 10, C["4"]); s.px(14, 9, C["3"])                                                   # 군화 끝
    s.line(2, 12, 13, 12, C["2"])
    s.outline(C["K"], where="inside")
    s.line(2, 12, 13, 12, C["2"]); s.line(3, 6, 4, 6, C["C"], only=C["K"]); s.line(9, 8, 11, 8, C["C"], only=C["K"])
    return s


def prop_bucket():
    """피 양동이(통과): 쇠 양동이(G05/G06, 테 G07) 안에 피(B, 그늘 S)와 붕대 끝(G12). 바닥에 흘린 자국 S."""
    s = new()
    s.rect(5, 6, 10, 12, C["5"]); s.line(5, 6, 5, 12, C["6"]); s.line(10, 6, 10, 12, C["4"])
    s.line(5, 9, 10, 9, C["6"])                                   # 테
    s.rect(5, 5, 10, 5, C["7"]); s.rect(6, 4, 9, 4, C["B"]); s.px(9, 4, C["S"]); s.px(6, 4, C["B"])
    s.px(7, 4, C["C"]); s.px(7, 3, C["C"]); s.px(8, 3, C["9"])     # 붕대 끝
    s.line(4, 3, 4, 4, C["6"]); s.line(11, 3, 11, 4, C["6"]); s.line(5, 2, 10, 2, C["6"])   # 손잡이
    s.line(5, 13, 10, 13, C["2"])
    s.outline(C["K"], where="inside")
    s.line(5, 13, 10, 13, C["2"])
    s.px(7, 4, C["C"]); s.px(7, 3, C["C"]); s.px(8, 3, C["9"]); s.line(6, 2, 9, 2, C["6"], only=C["K"])
    s.px(11, 12, C["S"]); s.px(12, 13, C["S"]); s.px(3, 11, C["S"])
    return s


def void_tile():
    return new()


TILES = (
    [("floor_%d" % i, common_floor(i)) for i in range(4)]
    + [("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
       ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
       ("exit", exit_stairs()), ("shop", shop_counter()),
       ("prop_stretcher", prop_stretcher()), ("prop_bandages", prop_bandages()), ("prop_vial_crate", prop_vial_crate()),
       ("prop_number_stake", prop_number_stake()), ("prop_shrouded_body", prop_shrouded_body()), ("prop_bucket", prop_bucket()),
       ("wall_v1", wall_v1()), ("wall_v2", wall_v2())]
    + [("start_%d" % i, start_floor(i)) for i in range(2)]
    + [("trial_%d" % i, trial_floor(i)) for i in range(2)]
    + [("rest_%d" % i, rest_floor(i)) for i in range(2)]
    + [("boss_%d" % i, boss_floor(i)) for i in range(2)]
)
PROPS = [("stretcher", True), ("bandage_pile", False), ("vial_crate", True), ("number_stake", False),
         ("shrouded_body", True), ("blood_bucket", False)]

if __name__ == "__main__":
    tc.run(3, "붕(繃) — 야전병원 제국 전선", TILES, PROPS, [19, 21, 23, 25], HERE)
