#!/usr/bin/env python3
"""LOPAD 1층 '잔(盞)' 술독 제국 타일셋 (16x16) — 37라운드 재작업. 단일 소스, 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage1/build.py
입력: parts/art/palette/lopad.json (무채 16 + 1층 호박 램프), assets/sprites/player/player_idle.png
산출: assets/tiles/stage1.png (8열x5행 128x80, 40라운드 인덱스 표 v3) / stage1.json (tilecommon2.py)
      parts/art/work/tiles_stage1/preview.png · preview_room.png · preview_rooms.png · preview_seam.png

37라운드 지시 (도영 님 원문): "바닥을 더 어둡고 짙게, 소품·벽 디테일 보강, 방 종류별 바닥 구분, 강조색을 더 강조하되,
  짙은 검은색이 초반부 바닥이면 좋겠음. 더 삭막하고. 처절하게. 도트도 더 잔불 올라오듯이 찍어내서 정돈된 타일을
  걷는 게 아니라, 버려진 구역의 흙바닥"
→ 바닥 = G01 흙 바탕 + K/G02 흩뿌림(격자 없음) + 깨진 병 조각(G07/G09 글린트) + 술 얼룩(호박 19) + 잔불(25/23/21).
  1층은 전 층에서 가장 어둡다 (바닥 평균 ≈ G01). 벽은 바닥과 갈라지도록 돌 G02 + K 이음, 윗면 G03 (text-pack L2: 윗면 밝게, 수직면 짙게).
40라운드 (v3): 시트 5행. 방 종류별 바닥 4변형 — 특징 무늬는 _0·_1 에만, _2·_3 은 은은하게(격자 방지). 소품 8종(+ 깨진 술독 solid, 나무잔 더미 통과).
색 예산: 무채 10 (K, G01~G07, G09, G12) + 강조 4 (19 shadow1 술·핏자국, 21 base, 23 light1, 25 glow 잔불 심).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon2 as tc  # noqa: E402

G = tc.G
A = tc.ramp(1)
T = tc.T

C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
    "S": A[3],   # 19 shadow1 — 말라붙은 술·피 얼룩
    "B": A[5],   # 21 base   — 술·꺼져 가는 불씨
    "L": A[7],   # 23 light1 — 불티·반사
    "W": A[9],   # 25 glow   — 잔불 심
}
ctx = tc.Ctx(C)
new = ctx.new


# ============================================================ 바닥 (버려진 구역의 흙바닥)
DOTS = {"K": 26, "2": 14, "3": 3}     # 1층: 전 층 중 가장 짙게 — K 가 G02 보다 많다
PAIRS = {"K": 3}


def shard(s, x, y, flip=False):
    """깨진 병 조각 2px: 유리 G07 + 글린트 G09. 옆에 술 한 방울(S)."""
    s.px(x, y, C["7"]); s.px(x + 1, y, C["9"])
    s.px(x + (2 if not flip else -1), y + 1, C["S"])


def common_floor(i):
    s, rnd = tc.dirt(ctx, seed=100 + i, base="1", dots=DOTS, pairs=PAIRS)
    if i == 0:
        shard(s, 4, 9)
        tc.ember_small(s, C, 11, 4)
    elif i == 1:
        tc.stain_small(s, C, rnd, 9, 8, dark="S", n=4)             # 말라붙은 술 얼룩 (작게 — 변형 1이 1/4 확률로 깔린다)
        shard(s, 3, 3, flip=True)
    elif i == 2:
        # 자갈 한 줌 (G02/G03 덩어리) + 풀뿌리 (G02 짧은 사선) + 잔불
        for x, y in [(3, 10), (4, 10), (5, 11), (3, 11), (6, 12)]:
            s.px(x, y, C["2"])
        s.px(4, 11, C["3"]); s.px(5, 10, C["3"])
        s.px(10, 2, C["2"]); s.px(11, 3, C["2"]); s.px(12, 3, C["2"]); s.px(13, 4, C["2"])
        tc.ember(s, C, 12, 11, rising=True)
    else:
        shard(s, 10, 5); s.px(12, 7, C["7"]); s.px(8, 4, C["7"])      # 조각 여럿 (병 하나가 깨진 자리)
        s.rect(4, 11, 5, 12, C["K"]); s.px(6, 12, C["K"])              # 파인 구덩이
        s.px(3, 11, C["2"])
    return s


def corridor_tile():
    """복도: 더 밟혀 더 검은 흙. K 가 많고 디테일·강조 없음 (방보다 한 단 어둡게 읽힌다)."""
    s, rnd = tc.dirt(ctx, seed=140, base="1", dots={"K": 44, "2": 6}, pairs={"K": 4})
    return s


# ---- 방 종류별 바닥 (4변형: _0·_1 특징, _2·_3 은은)
def start_floor(i):
    """시작 방: 발자국·야영 흔적. 누군가 머물다 갔다."""
    s, rnd = tc.dirt(ctx, seed=200 + i, base="1", dots={"K": 20, "2": 14, "3": 3}, pairs={"K": 2})
    if i == 0:
        tc.bootprint(s, C, 3, 3, left=True); tc.bootprint(s, C, 7, 6, left=False)
        tc.bootprint(s, C, 11, 2, left=True)
        s.px(12, 12, C["3"]); s.px(13, 12, C["3"])                     # 짚 한 줌
    elif i == 1:
        # 야영 흔적: 흩어진 짚(G03 짧은 가닥, 직사각형이면 격자가 보여서 흩뿌림) + 꺼진 불 자리(재 + 불씨 1) + 발자국
        for x0, y0, dx in [(2, 10, 1), (5, 12, 1), (3, 13, 1), (7, 9, 0), (6, 11, 1)]:
            s.px(x0, y0, C["3"]); s.px(x0 + dx, y0 + (1 - dx), C["3"])
        s.px(4, 11, C["2"]); s.px(8, 12, C["2"]); s.px(2, 12, C["2"])
        tc.ash_patch(s, C, rnd, 11, 4, r=2)
        tc.ember_small(s, C, 11, 4)
        tc.bootprint(s, C, 12, 10, left=False)
    elif i == 2:
        tc.bootprint(s, C, 9, 9, left=False)                           # 발자국 하나 + 짚 두 가닥
        s.px(3, 4, C["3"]); s.px(4, 4, C["3"]); s.px(6, 12, C["3"])
    else:
        s.px(11, 6, C["3"]); s.px(12, 7, C["3"])                       # 짚 한 가닥 + 자갈
        s.px(4, 9, C["2"]); s.px(5, 9, C["3"]); s.px(5, 10, C["2"])
    return s


def trial_floor(i):
    """시련 방: 핏자국·탄흔 많음. 가장 처절하다."""
    s, rnd = tc.dirt(ctx, seed=300 + i, base="1", dots={"K": 28, "2": 12, "3": 2}, pairs={"K": 4})
    if i == 0:
        # 핏자국 하나(젖은 가운데 B 1px) + 탄흔 1 + 조각. 4변형 중 _0·_1 만 덩어리를 가져야 물방울 무늬가 안 생긴다.
        tc.stain_small(s, C, rnd, 5, 5, dark="S", n=5); s.px(5, 5, C["B"])   # r=2 splat 은 25% 타일마다 같은 꼴로 반복돼 보여 5px 불규칙 얼룩으로
        s.px(8, 4, C["S"]); s.px(3, 8, C["S"])
        tc.pock(s, C, 11, 10)
        shard(s, 10, 3)
    elif i == 1:
        tc.pock(s, C, 11, 3); tc.pock(s, C, 4, 11)
        s.px(7, 8, C["S"]); s.px(13, 9, C["S"]); s.px(2, 5, C["S"]); s.px(8, 13, C["S"])
        tc.ember_small(s, C, 13, 13)
    elif i == 2:
        s.px(9, 11, C["S"]); s.px(10, 12, C["S"]); s.px(3, 6, C["S"])   # 튄 방울만
        shard(s, 5, 2, flip=True)
    else:
        tc.pock(s, C, 7, 7)                                             # 탄흔 하나 + 방울 하나
        s.px(12, 3, C["S"]); s.px(2, 12, C["K"]); s.px(3, 12, C["K"])
    return s


def rest_floor(i):
    """휴식 방: 재 식은 모닥불 자국. 조금 덜 처절 — K 점이 적고 재(G03/G04)가 있다."""
    s, rnd = tc.dirt(ctx, seed=400 + i, base="1", dots={"K": 14, "2": 16, "3": 4}, pairs={"2": 2})
    if i == 0:
        tc.ash_patch(s, C, rnd, 8, 8, r=3)
        s.px(8, 7, C["L"])                                             # 재 속 식은 불씨 하나
        s.px(3, 12, C["3"]); s.px(4, 12, C["3"])
    elif i == 1:
        tc.ash_patch(s, C, rnd, 4, 4, r=2)
        s.px(10, 11, C["3"]); s.px(11, 11, C["3"]); s.px(11, 12, C["3"])   # 흩어진 재
        s.px(12, 5, C["2"]); s.px(13, 6, C["2"])
    elif i == 2:
        s.px(11, 3, C["3"]); s.px(12, 3, C["3"]); s.px(12, 4, C["4"])    # 재 세 점
        s.px(4, 10, C["3"]); s.px(5, 11, C["3"])
    else:
        s.px(6, 6, C["3"]); s.px(7, 6, C["4"])                           # 재 두 점 + 자갈
        s.px(12, 12, C["2"]); s.px(13, 12, C["2"]); s.px(3, 3, C["3"])
    return s


GOBLET = [(2, 0), (3, 0), (4, 0), (1, 1), (5, 1), (2, 2), (4, 2), (3, 3), (3, 4), (2, 5), (3, 5), (4, 5)]   # 잔 문양 6x6


def boss_floor(i):
    """보스 방(양조장주 본영): 제국 포석에 새긴 '잔' 문양이 흙에 반쯤 묻혔다."""
    s, rnd = tc.dirt(ctx, seed=500 + i, base="1", dots={"K": 22, "2": 10, "3": 2}, pairs={"K": 2})
    # 포석은 타일 가운데에 두지 않고 귀퉁이를 사선으로 깨서 네모가 반복되지 않게 한다. _1 은 잔해, _2·_3 은 조각 몇 점.
    if i == 0:
        tc.buried_slab(s, C, rnd, (2, 2, 8, 8), carve=[(x + 2, y + 2) for x, y in GOBLET], bury_from=0.55)
        for x, y in [(2, 2), (3, 2), (2, 3), (8, 2), (2, 8), (2, 7), (3, 8), (8, 8), (8, 7), (7, 8), (8, 3)]:
            s.px(x, y, C["1"])                                          # 사선으로 깨진 귀퉁이 (네모가 안 보이게 더 깨고 더 묻음)
        s.px(12, 11, C["2"]); s.px(13, 11, C["3"]); s.px(13, 12, C["2"])  # 떨어져 나간 조각
    elif i == 1:
        for x, y, ch in [(10, 3, "2"), (11, 3, "3"), (12, 3, "2"), (11, 4, "2"), (4, 10, "2"), (5, 10, "3"), (5, 11, "2"), (4, 11, "K"), (13, 13, "2")]:
            s.px(x, y, C[ch])                                           # 포석 잔해
        s.px(7, 7, C["S"]); s.px(8, 7, C["S"]); s.px(8, 8, C["S"])      # 밴 술
    elif i == 2:
        s.px(3, 12, C["2"]); s.px(4, 12, C["3"]); s.px(4, 13, C["2"])    # 조각 하나 + 밴 술 1px
        s.px(11, 5, C["S"])
    else:
        s.px(9, 9, C["3"]); s.px(10, 9, C["2"]); s.px(10, 10, C["K"])    # 조각 하나
        s.px(3, 3, C["2"]); s.px(4, 3, C["2"])
    return s


# ============================================================ 벽 (돌 G02 + K 이음, 바닥보다 밝은 덩어리)
def wall_base(s):
    """벽 정면: 큰 돌 2단(8px), 반 칸 어긋남. 돌 G02, 이음 K, 윗변 빛 G03, 회반죽 떨어진 자리 G01. 아랫단 K 그늘."""
    s.rect(0, 0, T - 1, T - 1, C["2"])
    for i, (y0, off) in enumerate(((0, 0), (8, 5))):
        s.line(0, y0, T - 1, y0, C["K"])
        s.line(0, y0 + 1, T - 1, y0 + 1, C["3"])
        for x in (off, off + 10):
            if 0 <= x < T:
                s.line(x, y0, x, y0 + 7, C["K"])
                if x + 1 < T:
                    s.line(x + 1, y0 + 2, x + 1, y0 + 6, C["3"], only=C["2"])
    # 회반죽 떨어진 어두운 자리·갈라진 돌 (조용한 G01 덩어리)
    for x, y in [(3, 4), (4, 4), (4, 5), (12, 11), (13, 11), (13, 12), (12, 12), (8, 13)]:
        s.px(x, y, C["1"])
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_face():
    s = new()
    wall_base(s)
    s.px(7, 3, C["1"]); s.px(7, 4, C["K"])      # 돌 틈 한 점
    return s


def wall_v1():
    """벽 변형 1: 제국 표식 — 돌 위에 스텐실로 찍은 '잔' 문양(흰 회칠 G06, 닳은 자리 G04). 양조장주의 구역 표시."""
    s = new()
    wall_base(s)
    for x, y in GOBLET:
        s.px(x + 5, y + 4, C["6"])
    for x, y in [(6, 5), (8, 9)]:
        s.px(x, y, C["4"])                           # 닳아 벗겨짐
    s.px(10, 4, C["4"]); s.px(4, 9, C["4"])         # 튄 회칠
    return s


def wall_v2():
    """벽 변형 2: 균열 + 못에 걸린 빈 병(G07 유리, 바닥에 술 찌꺼기 S). 걸린 사물."""
    s = new()
    wall_base(s)
    # 균열: 위에서 아래로 지그재그 K, 옆에 G03 빛 받는 모서리
    for x, y in [(3, 1), (3, 2), (4, 3), (4, 4), (5, 5), (4, 6), (4, 7), (5, 8), (5, 9), (6, 10), (6, 11), (5, 12), (5, 13), (5, 14)]:
        s.px(x, y, C["K"])
    for x, y in [(5, 3), (6, 5), (5, 7), (7, 10), (6, 13)]:
        s.px(x, y, C["3"])
    # 못 + 끈 + 매달린 병 (목 위, 몸통 아래)
    s.px(11, 2, C["6"]); s.px(11, 3, C["4"]); s.px(11, 4, C["4"])
    s.rect(10, 5, 12, 6, C["7"]); s.px(11, 5, C["9"])
    s.rect(10, 7, 12, 11, C["7"]); s.px(10, 8, C["9"])
    s.px(11, 10, C["S"]); s.px(12, 10, C["S"]); s.px(11, 11, C["S"]); s.px(12, 11, C["S"])
    s.line(10, 12, 12, 12, C["1"])
    return s


def wall_top():
    """벽 윗면: 돌 덮개 G03 (바닥보다 두 단 밝다 — 검은 구덩이를 두르는 돌 테). 이음 K, 빛 G04 알갱이, 때 G02."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    s.line(0, 0, T - 1, 0, C["K"]); s.line(0, 8, T - 1, 8, C["K"])
    s.line(7, 0, 7, 7, C["K"]); s.line(3, 8, 3, 15, C["K"]); s.line(11, 8, 11, 15, C["K"])
    s.line(0, 1, T - 1, 1, C["4"], only=C["3"]); s.line(0, 9, T - 1, 9, C["4"], only=C["3"])
    for x, y in [(2, 4), (12, 3), (13, 5), (6, 12), (14, 11), (1, 13)]:
        s.px(x, y, C["2"])
    for x, y in [(4, 3), (10, 5), (8, 11), (13, 13)]:
        s.px(x, y, C["4"])
    return s


# ============================================================ 문 (벽 자리)
def door_frame(s):
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["3"]); s.line(0, 0, 0, T - 1, C["K"]); s.line(1, 0, 1, T - 1, C["4"])
    s.rect(13, 0, 15, T - 1, C["3"]); s.line(15, 0, 15, T - 1, C["K"]); s.line(13, 0, 13, T - 1, C["2"])
    s.rect(0, 0, T - 1, 1, C["3"]); s.line(0, 0, T - 1, 0, C["K"]); s.line(3, 1, 12, 1, C["4"])


def door_open():
    """열린 문: 틀 안은 어두운 통로(흙 + K 점). 왼쪽에 젖혀진 문짝 2px, 문틈으로 호박빛 한 줄(L, text-pack L3)."""
    s = new()
    door_frame(s)
    s.rect(3, 2, 12, 15, C["1"])
    rnd = random.Random(9)
    tc.scatter(s, C, rnd, "K", 14, box=(5, 2, 12, 15))
    tc.scatter(s, C, rnd, "2", 4, box=(5, 2, 12, 15))
    s.rect(3, 2, 4, 14, C["5"]); s.line(4, 2, 4, 14, C["4"])
    s.px(3, 5, C["7"]); s.px(3, 12, C["7"]); s.px(4, 5, C["6"]); s.px(4, 12, C["6"])
    s.line(3, 15, 4, 15, C["2"])
    s.line(5, 3, 5, 13, C["L"])                   # 문틈 빛
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


def door_closed():
    s = new()
    door_frame(s)
    door_planks(s)
    s.px(10, 9, C["7"]); s.px(10, 10, C["K"])
    return s


def door_locked():
    s = new()
    door_frame(s)
    door_planks(s)
    s.rect(2, 7, 13, 8, C["6"]); s.line(2, 7, 13, 7, C["7"]); s.px(2, 8, C["5"]); s.px(13, 8, C["5"])
    s.rect(6, 9, 9, 12, C["7"]); s.line(6, 9, 9, 9, C["9"])
    s.px(6, 8, C["9"]); s.px(9, 8, C["9"])
    s.px(7, 10, C["K"]); s.px(8, 10, C["K"]); s.px(7, 11, C["K"])
    return s


# ============================================================ 출구 · 상점 (2x2)
def exit_stairs():
    """올라가는 돌계단 4단. 어두운 바닥 위라 한 단 낮춰(G04/G03) 번쩍이지 않게. 위에서 비껴드는 호박빛 2px x2."""
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
    """술 좌판: 널빤지(G03) 위 병 2개. 병 속 술 B/S, 유리 G07, 글린트 G09."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["1"])
        s.line(0, y + 1, T - 1, y + 1, C["4"])
    s.line(0, 15, T - 1, 15, C["1"])
    for bx in (3, 10):
        s.rect(bx, 2, bx + 2, 11, C["7"])
        s.rect(bx, 2, bx + 2, 3, C["1"]); s.px(bx + 1, 2, C["7"]); s.px(bx + 1, 3, C["7"])
        s.rect(bx, 6, bx + 2, 10, C["B"])
        for y in range(7, 11):
            s.px(bx + 2, y, C["S"])
        s.px(bx, 5, C["9"])
        s.line(bx, 11, bx + 2, 11, C["4"])
        s.line(bx, 12, bx + 2, 12, C["1"])
    return s


# ============================================================ 소품 (투명 배경)
def prop_barrel():
    s = new()
    prof = {2: (5, 10), 3: (4, 11), 4: (3, 12), 5: (3, 12), 6: (2, 13), 7: (2, 13), 8: (2, 13), 9: (2, 13),
            10: (2, 13), 11: (3, 12), 12: (3, 12), 13: (3, 12), 14: (4, 11), 15: (5, 10)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["4"])
    for x in (6, 9):
        s.line(x, 3, x, 15, C["3"])
    for y, (x0, x1) in prof.items():
        s.px(x0, y, C["5"]); s.px(x1, y, C["2"]); s.px(x1 - 1, y, C["3"])
    for y in (5, 12):
        x0, x1 = prof[y]
        s.line(x0, y, x1, y, C["6"])
        s.px(x0 + 1, y, C["9"]); s.px(x0 + 2, y, C["9"])
        s.line(x0 + 1, y + 1, x1 - 1, y + 1, C["3"])
    s.line(5, 2, 10, 2, C["5"]); s.line(4, 3, 11, 3, C["5"]); s.px(5, 3, C["7"]); s.px(6, 3, C["7"])
    s.px(7, 9, C["1"]); s.px(8, 9, C["1"]); s.px(7, 10, C["K"]); s.px(8, 10, C["K"]); s.px(8, 8, C["7"])
    s.px(8, 11, C["B"]); s.px(8, 14, C["B"]); s.px(8, 15, C["S"]); s.px(9, 15, C["S"])
    s.outline(C["K"], where="inside")
    s.line(5, 2, 10, 2, C["5"], only=C["K"])
    return s


def prop_bottle():
    """깨진 병: 옆으로 누운 병, 오른쪽 끝이 깨짐. 흘러나온 술은 S 로 어둡게, 빛 받은 1px 만 B."""
    s = new()
    s.rect(9, 10, 13, 11, C["S"]); s.rect(10, 9, 12, 9, C["S"]); s.px(14, 11, C["S"]); s.px(11, 12, C["S"])
    s.px(10, 10, C["B"]); s.px(11, 9, C["B"])
    s.rect(5, 5, 11, 8, C["7"])
    s.rect(2, 6, 4, 7, C["7"])
    s.px(2, 6, C["9"]); s.line(5, 5, 10, 5, C["9"])
    s.line(5, 8, 10, 8, C["6"])
    s.px(8, 6, C["B"]); s.px(9, 6, C["B"]); s.px(8, 7, C["S"]); s.px(9, 7, C["S"])
    s.px(11, 5, C["7"]); s.px(12, 6, C["9"]); s.px(11, 7, C["7"]); s.px(12, 8, C["7"])
    s.px(11, 6, C["K"]); s.px(11, 8, C["K"])
    s.outline(C["K"], where="inside")
    s.px(2, 6, C["9"]); s.line(6, 5, 10, 5, C["9"], only=C["K"])
    s.px(13, 4, C["9"]); s.px(14, 4, C["7"])
    s.px(6, 11, C["7"]); s.px(7, 11, C["9"])
    return s


def prop_puddle():
    """웅덩이(통과): 검은 물(K) — 흙보다 더 검다. 먼 쪽 테 G02, 등불 반사 L/W, 가까운 쪽 어두운 반사 S."""
    s = new()
    rows = {4: (6, 9), 5: (4, 11), 6: (3, 12), 7: (2, 13), 8: (2, 13), 9: (3, 13), 10: (4, 11), 11: (6, 12), 12: (9, 12), 13: (10, 11)}
    for y, (x0, x1) in rows.items():
        s.line(x0, y, x1, y, C["K"])
    s.line(6, 4, 9, 4, C["2"]); s.px(4, 5, C["2"]); s.px(5, 5, C["2"]); s.px(3, 6, C["2"]); s.px(2, 7, C["2"]); s.px(10, 5, C["2"])
    s.px(5, 7, C["L"]); s.px(6, 7, C["L"]); s.px(5, 8, C["W"]); s.px(6, 8, C["L"])
    s.px(9, 10, C["S"]); s.px(10, 10, C["S"])
    s.px(11, 13, C["2"]); s.px(12, 12, C["2"])
    return s


def prop_lantern():
    s = new()
    s.rect(5, 14, 10, 14, C["5"]); s.rect(4, 15, 11, 15, C["3"])
    s.line(7, 9, 7, 13, C["5"]); s.line(8, 9, 8, 13, C["4"])
    s.rect(4, 2, 11, 8, C["6"])
    s.rect(5, 3, 10, 7, C["B"])
    s.rect(6, 4, 9, 6, C["L"])
    s.px(7, 5, C["W"]); s.px(8, 5, C["W"])
    s.line(4, 2, 11, 2, C["7"]); s.px(4, 3, C["7"])
    s.rect(6, 0, 9, 1, C["6"]); s.px(7, 0, C["7"]); s.px(8, 0, C["7"])
    s.px(7, 3, C["6"]); s.px(8, 7, C["6"])
    s.outline(C["K"], where="inside")
    s.px(7, 0, C["7"]); s.px(8, 0, C["7"])
    s.line(5, 2, 10, 2, C["7"], only=C["K"])
    return s


def prop_ash_pit():
    """잔불 더미(통과): 누가 밤새 쬔 자리. 재 G03/G04 덩어리 + 숯 K + 잔불 3점(W/L/B). 호박 ~9px — 이 층에서 가장 또렷한 강조."""
    s = new()
    rnd = random.Random(21)
    prof = {5: (6, 9), 6: (4, 11), 7: (3, 12), 8: (3, 12), 9: (2, 13), 10: (3, 12), 11: (4, 11), 12: (6, 10)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["3"])
    for x, y in [(4, 7), (5, 6), (3, 9), (9, 11), (10, 10), (6, 12)]:
        s.px(x, y, C["4"])
    for x, y in [(6, 8), (7, 8), (8, 9), (9, 8), (7, 10), (5, 10), (10, 7), (6, 9)]:
        s.px(x, y, C["K"])
    s.px(7, 9, C["W"]); s.px(7, 7, C["L"]); s.px(8, 8, C["B"])
    s.px(10, 9, C["L"]); s.px(10, 8, C["W"]); s.px(11, 10, C["B"])
    s.px(5, 11, C["B"]); s.px(4, 10, C["L"])
    s.px(8, 4, C["L"])                             # 오르는 불티 하나
    for x, y in [(2, 12), (12, 13), (13, 7)]:
        s.px(x, y, C["2"])                         # 둘레로 흩어진 재
    return s


def prop_bottle_crate():
    """술 상자(solid): 열린 나무 상자(G04, 틈 G02) 안에 병 목 4개(G07, 마개 G05). 빈 병이 더 많다 — 술은 하나만(B)."""
    s = new()
    s.rect(2, 6, 13, 14, C["4"])
    s.line(2, 6, 13, 6, C["5"]); s.line(2, 6, 2, 14, C["5"])
    s.line(3, 14, 13, 14, C["3"]); s.line(13, 7, 13, 14, C["3"])
    s.line(2, 10, 13, 10, C["2"]); s.line(7, 11, 7, 13, C["2"])
    s.rect(3, 4, 12, 5, C["1"])                     # 상자 안 어둠
    s.line(3, 15, 13, 15, C["2"])
    s.outline(C["K"], where="inside")
    s.line(3, 15, 13, 15, C["2"])
    s.line(3, 6, 12, 6, C["5"], only=C["K"])
    # 병 4개 (셀아웃 뒤 = keep)
    for i, x in enumerate((3, 6, 9, 12)):
        s.px(x, 2, C["5"]); s.rect(x, 3, x, 5, C["7"])
        if i == 1:
            s.px(x, 5, C["B"]); s.px(x, 4, C["B"])
        if i == 3:
            s.px(x, 3, C["9"])
    s.px(5, 4, C["K"]); s.px(8, 4, C["K"]); s.px(11, 4, C["K"]); s.px(10, 5, C["K"])  # 병 사이 어둠
    return s


def prop_wine_jar():
    """깨진 술독(solid): 큰 옹기 항아리(G03 몸, 빛 G04, 그늘 G02), 입이 깨져 나갔고(K 톱니) 옆구리 금 사이로 술(B/S)이 흘러 바닥에 고였다.
    1층 '잔' 의 가장 큰 사물 — 술통(prop_barrel)과 실루엣 분리: 배가 둥글고 어깨가 좁다."""
    s = new()
    prof = {3: (6, 9), 4: (5, 10), 5: (4, 11), 6: (3, 12), 7: (2, 13), 8: (2, 13), 9: (2, 13), 10: (2, 13),
            11: (3, 12), 12: (3, 12), 13: (4, 11), 14: (5, 10)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["4"])                                    # 몸 G04 (G03 은 검은 바닥에서 검은 덩어리로만 읽혔다)
        s.px(x0, y, C["5"]); s.px(x0 + 1, y, C["5"]); s.px(x1, y, C["2"]); s.px(x1 - 1, y, C["3"])
    s.line(6, 2, 9, 2, C["5"]); s.px(7, 2, C["6"])                      # 입 테
    s.px(9, 2, C["K"]); s.px(10, 3, C["K"]); s.px(8, 3, C["1"])         # 깨진 입
    s.line(6, 4, 6, 7, C["6"]); s.px(7, 5, C["6"]); s.px(7, 4, C["6"])  # 빛 받는 어깨
    s.line(3, 8, 3, 11, C["3"], only=C["4"])                             # 몸 둘레 결
    for x, y in [(10, 7), (10, 8), (11, 9), (11, 10), (10, 11)]:
        s.px(x, y, C["K"])                                             # 옆구리 금
    s.px(11, 11, C["S"]); s.px(11, 12, C["B"]); s.px(12, 13, C["S"])    # 금 사이로 흘러나온 술
    s.line(5, 15, 10, 15, C["2"]); s.px(12, 14, C["S"]); s.px(13, 14, C["S"]); s.px(12, 15, C["S"])
    s.outline(C["K"], where="inside")
    s.line(6, 2, 8, 2, C["5"], only=C["K"]); s.px(7, 2, C["6"])
    s.line(5, 15, 10, 15, C["2"]); s.px(12, 14, C["S"]); s.px(13, 14, C["S"]); s.px(12, 15, C["S"])
    return s


def prop_cup_pile():
    """나무잔 더미(통과): 엎어지고 넘어진 나무잔 셋(G04/G05, 테 G06, 속 어둠 K). 하나에 남은 술(B) 한 모금, 바닥에 흘린 자국(S)."""
    s = new()
    # 잔 1: 세워진 잔 (왼쪽 위) 입이 보임
    s.rect(3, 5, 6, 9, C["4"]); s.line(3, 5, 6, 5, C["6"]); s.px(4, 6, C["K"]); s.px(5, 6, C["K"]); s.px(4, 7, C["B"])
    s.line(3, 10, 6, 10, C["3"])
    # 잔 2: 옆으로 누운 잔 (오른쪽) 입이 오른쪽
    s.rect(8, 7, 12, 10, C["4"]); s.line(8, 7, 12, 7, C["5"]); s.rect(12, 7, 13, 10, C["6"]); s.px(13, 8, C["K"]); s.px(13, 9, C["K"])
    s.line(8, 11, 12, 11, C["3"])
    # 잔 3: 엎어진 잔 (아래) 바닥면
    s.rect(4, 11, 7, 13, C["4"]); s.line(4, 11, 7, 11, C["5"]); s.line(4, 13, 7, 13, C["3"])
    s.px(9, 13, C["S"]); s.px(10, 13, C["S"]); s.px(10, 14, C["S"]); s.px(2, 9, C["S"])   # 흘린 술
    s.outline(C["K"], where="inside")
    s.line(4, 5, 5, 5, C["6"], only=C["K"]); s.px(9, 13, C["S"]); s.px(10, 13, C["S"]); s.px(10, 14, C["S"]); s.px(2, 9, C["S"])
    return s


def void_tile():
    return new()


TILES = (
    [("floor_%d" % i, common_floor(i)) for i in range(4)]
    + [("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
       ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
       ("exit", exit_stairs()), ("shop", shop_counter()),
       ("prop_barrel", prop_barrel()), ("prop_bottle", prop_bottle()), ("prop_puddle", prop_puddle()),
       ("prop_lantern", prop_lantern()), ("prop_ash_pit", prop_ash_pit()), ("prop_bottle_crate", prop_bottle_crate()),
       ("prop_wine_jar", prop_wine_jar()), ("prop_cup_pile", prop_cup_pile()),
       ("wall_v1", wall_v1()), ("wall_v2", wall_v2())]
    + [("start_%d" % i, start_floor(i)) for i in range(4)]
    + [("trial_%d" % i, trial_floor(i)) for i in range(4)]
    + [("rest_%d" % i, rest_floor(i)) for i in range(4)]
    + [("boss_%d" % i, boss_floor(i)) for i in range(4)]
    + [("reserve", void_tile())]
)
# (short, solid, maxPerRoom, weight) — 40라운드. 작고 통과하는 것은 많이·자주, 몸통 큰 것은 적게·드물게.
PROPS = [("barrel", True, 2, 0.8), ("broken_bottle", False, 3, 1.0), ("puddle", False, 2, 0.8), ("lantern", True, 1, 0.6),
         ("ash_pit", False, 1, 0.6), ("bottle_crate", True, 1, 0.5), ("wine_jar", True, 1, 0.4), ("cup_pile", False, 3, 1.0)]

if __name__ == "__main__":
    if "--legacy" not in sys.argv:
        sys.exit("48라운드: stage1 는 parts/art/work/tiles_v4/build.py (바닥 v4) 로 대체됨. 이 v3 판을 다시 쓰려면 --legacy")
    tc.run(1, "잔(盞) — 술독 제국 외곽", TILES, PROPS, [19, 21, 23, 25], HERE)
