#!/usr/bin/env python3
"""1층 '잔(盞)' 술독 제국 외곽 — 바닥 타일 v4: 큰 판석 뒷골목 + 황폐한 평화지역(start).

인덱스 표 v3 그대로 (0~3 공통 / 4 복도 / 5 벽 / 6 벽 윗면 / 7 void / 8·9·10 문 / 11 출구 / 12 상점 / 13~20 소품 /
21·22 벽 변형 / 23~26 start / 27~30 trial / 31~34 rest / 35~38 boss / 39 예비).
판석 = 16x16 한 장(또는 반·L 분할). 면 G02, 줄눈 G01 — 대비를 일부러 낮췄다(눈 피로). 깊은 금·구멍 그늘만 K.
start(여정 노드: 탄생지·버려진 길·국경 초소) = 포장이 없는 흙바닥 + 깨진 판석 조각 + 탄 자국.
"""
import random

import pave
import tilecommon2 as tc

T = pave.T
C = pave.colors(1)
ctx = tc.Ctx(C)
P = pave.Pave(ctx, face="2", joint="1")
new = ctx.new

GOBLET = [(2, 0), (3, 0), (4, 0), (1, 1), (5, 1), (2, 2), (4, 2), (3, 3), (3, 4), (2, 5), (3, 5), (4, 5)]  # 잔 문양 6x6


# ============================================================ 판석 배치 4종 (모든 바닥이 공유)
def lay(kind):
    """full = 한 장 / half = 가로 반(위아래 2장) / tee = 위 한 장 + 아래 두 장 / ell = 왼쪽 세로 한 장 + 오른쪽 두 장."""
    s = P.base()
    if kind == "half":
        P.hj(s, 8)
    elif kind == "tee":
        P.hj(s, 8); P.vj(s, 8, 9, T - 1)
    elif kind == "ell":
        P.vj(s, 8); P.hj(s, 8, 9, T - 1)
    return s


# ============================================================ 공통 바닥 0~3 (기타 노드·상점·이벤트)
def common_floor(i):
    if i == 0:
        return lay("full")
    if i == 1:
        return lay("half")
    if i == 2:
        s = lay("tee")
        P.crack(s, [(3, 2), (5, 4), (5, 6)])                 # 실금 하나 (줄눈색)
        return s
    s = lay("ell")
    s.px(1, 1, C["1"]); s.px(2, 1, C["1"]); s.px(1, 2, C["1"])   # 줄눈 교차점이 깨져 넓어짐      # 모서리 이 빠짐 2x2
    return s


def corridor_tile():
    """복도(노드 지도에서는 거의 안 쓰임): 판석 한 장, 한 단 어둡게."""
    s = P.base()
    s.rect(1, 1, T - 1, T - 1, C["1"])
    return s


# ============================================================ 방 종류별 바닥
def start_floor(i):
    """황폐한 평화지역: 포장이 없는 흙 G02 평면 + 아주 작은 흔적(2px 덩어리, G01/G03) 2개씩.
    흔적을 변형마다 **다른 자리**에 두어 25% 균등 섞기에서 같은 자리 무늬가 격자로 줄 서지 않게 한다(2회차 비평: 한 자리 덩어리 = 격자 점무늬).
    큰 탄 자국·잔불은 소품 ash_pit(방당 1)·구조물(모닥불·묘) 몫."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["2"])
    if i == 0:
        s.px(3, 4, C["1"]); s.px(4, 4, C["1"])                                        # 흙 덩이
        s.px(11, 11, C["3"]); s.px(12, 11, C["3"]); s.px(11, 12, C["1"]); s.px(12, 12, C["1"])   # 자갈 + 그늘
    elif i == 1:
        P.blob(s, 9, 6, 2.2, "1", seed=23, squash=0.6)                                 # 그을린 자리 (작게)
        s.px(4, 12, C["1"]); s.px(5, 12, C["1"])
    elif i == 2:
        s.px(12, 3, C["1"]); s.px(13, 3, C["1"])
        s.px(6, 9, C["1"]); s.px(6, 10, C["1"])
    else:
        for x, y in [(4, 9), (5, 9), (6, 9), (4, 10), (5, 10)]:                         # 깨진 판석 조각
            s.px(x, y, C["3"])
        s.px(4, 9, C["4"]); s.line(5, 11, 6, 11, C["K"]); s.px(7, 10, C["K"])
        s.px(12, 13, C["1"]); s.px(13, 13, C["1"])
    return s


def trial_floor(i):
    """전투 노드: 판석 4배치 중 하나만 깨졌다 — 금은 줄눈에서 줄눈으로 이어져 '판석이 갈라진' 것으로 읽힌다(도장처럼 떠 있지 않게).
    잔불은 바닥 타일에 두지 않는다 (25% 균등 섞기에서는 화면에 100개 넘게 찍힌다: 1회차 비평) → 소품 ash_pit(방당 1)·보스 바닥."""
    if i == 0:
        s = lay("full")
        P.crack(s, [(9, 0), (10, 3), (13, 5), (15, 8)])             # 귀퉁이가 떨어져 나간 금 (줄눈 → 줄눈)
        s.px(10, 3, C["K"]); s.px(11, 4, C["K"])                    # 금이 벌어진 한 곳만 K
        return s
    if i == 1:
        return lay("half")
    if i == 2:
        return lay("tee")
    s = lay("ell")
    s.px(1, 1, C["1"]); s.px(2, 1, C["1"]); s.px(1, 2, C["1"])   # 줄눈 교차점이 깨져 넓어짐
    return s


def rest_floor(i):
    """휴식 노드: 가장 조용하다. 줄눈 모서리에 그을음 3px 하나뿐."""
    if i == 0:
        s = lay("full")
        s.px(1, 1, C["1"]); s.px(2, 1, C["1"]); s.px(1, 2, C["1"])
        return s
    if i == 1:
        return lay("half")
    if i == 2:
        return lay("tee")
    return lay("ell")


def boss_floor(i):
    """보스(양조장주 본영): 판석이 더 깨지고, _0 의 벌어진 금 사이에만 잔불 2px. _1 은 판석에 새긴 잔 문양(G01 낮은 대비)."""
    if i == 0:
        s = lay("full")
        P.crack(s, [(0, 9), (4, 8), (6, 10), (9, 9), (12, 11), (15, 11)])
        s.px(6, 10, C["K"]); s.px(7, 10, C["K"])
        s.px(6, 10, C["S"])                                         # 금 사이 잔불 1px (어두운 강조 S)
        return s
    if i == 1:
        s = lay("tee")
        P.crack(s, [(3, 0), (4, 4), (2, 8)])                        # (잔 문양 각인은 25% 반복으로 벽지처럼 보여 뺐다: 2회차 비평)
        return s
    if i == 2:
        s = lay("half")
        return s
    return lay("ell")


# ============================================================ 벽 (뒷골목 건물 벽: 벽돌, 바닥보다 한 단 밝다)
def wall_base(s):
    """벽 정면(북벽): 벽돌 16x5 3단 + 아래 받침. 벽돌 G03, 줄눈 G02(낮은 대비), 위 덮개 G04 테 + 아래 발치 K 그늘."""
    s.rect(0, 0, T - 1, T - 1, C["3"])
    s.line(0, 0, T - 1, 0, C["4"])                                 # 덮개 테
    s.line(0, 1, T - 1, 1, C["K"])
    for j, y in enumerate((6, 11)):
        s.line(0, y, T - 1, y, C["2"])
    for j, (y0, y1) in enumerate(((2, 5), (7, 10), (12, 14))):
        for x in ((0, 8) if j % 2 == 0 else (4, 12)):
            s.line(x, y0, x, y1, C["2"])
    s.line(0, 15, T - 1, 15, C["K"])                               # 바닥과 만나는 발치 그늘
    return s


def wall_face():
    s = new()
    return wall_base(s)


def wall_v1():
    """벽 변형 1: 회칠 스텐실 '잔' 문양 — 닳아서 G04(벽돌 G03 위 한 단 밝음). 낮은 대비라 여러 장 섞여도 벽지처럼 튀지 않는다."""
    s = new()
    wall_base(s)
    for x, y in GOBLET:
        s.px(x + 5, y + 5, C["4"])
    s.px(7, 7, C["3"])
    return s


def wall_v2():
    """벽 변형 2: 벽돌이 빠진 자리(K 구멍 + 아래 턱 G04) 와 흘러내린 술 얼룩(S 1px 줄)."""
    s = new()
    wall_base(s)
    s.rect(9, 7, 11, 9, C["2"]); s.line(9, 7, 11, 7, C["1"])      # 벽돌 하나가 빠진 얕은 홈 (K 구멍은 벽을 따라 점선처럼 보였다)
    s.line(3, 3, 3, 9, C["2"])
    return s


def wall_top():
    """벽 윗면: 덮개돌 G04 (바닥 G02 보다 두 단 밝은 테), 덮개 이음 G03, 바깥 그늘 없음. 디테일 2점."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    s.line(0, 0, T - 1, 0, C["3"]); s.line(0, 0, 0, T - 1, C["3"])
    s.line(0, 8, T - 1, 8, C["3"]); s.line(8, 1, 8, 7, C["3"])
    s.px(11, 12, C["3"]); s.px(12, 12, C["3"])
    s.px(4, 4, C["5"])
    return s


# ============================================================ 문
def door_frame(s):
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["4"]); s.line(0, 0, 0, T - 1, C["3"]); s.line(2, 0, 2, T - 1, C["K"])
    s.rect(13, 0, 15, T - 1, C["4"]); s.line(15, 0, 15, T - 1, C["3"]); s.line(13, 0, 13, T - 1, C["K"])
    s.rect(0, 0, T - 1, 1, C["4"]); s.line(0, 0, T - 1, 0, C["3"]); s.line(3, 1, 12, 1, C["K"])


def door_open():
    """열린 문: 틀 안은 어두운 통로(G01 평면), 젖힌 문짝 2px, 문틈으로 호박빛 한 줄."""
    s = new()
    door_frame(s)
    s.rect(3, 2, 12, 15, C["1"])
    s.rect(3, 2, 4, 15, C["5"]); s.line(4, 2, 4, 15, C["4"])
    s.line(5, 3, 5, 13, C["S"]); s.px(5, 7, C["B"])
    return s


def door_planks(s, x0=3, x1=12, y0=2, y1=15):
    s.rect(x0, y0, x1, y1, C["4"])
    for x in (x0 + 3, x0 + 6):
        s.line(x, y0, x, y1, C["3"])
    for y in (y0 + 3, y0 + 10):
        s.line(x0, y, x1, y, C["6"])
        s.line(x0, y + 1, x1, y + 1, C["3"])


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
    s.rect(2, 7, 13, 8, C["6"]); s.line(2, 8, 13, 8, C["4"])
    s.rect(6, 9, 9, 12, C["7"]); s.line(6, 9, 9, 9, C["9"])
    s.px(7, 10, C["K"]); s.px(7, 11, C["K"])
    return s


# ============================================================ 출구 · 상점 (2x2)
def exit_stairs():
    """내려가는 지하 계단(뒷골목 지하 술집 입구): 단 4개, 단면 G04 → 아래로 갈수록 어둡게. 바닥에 비치는 호박빛 2px."""
    s = new()
    body = ["4", "3", "3", "2"]
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["5" if i < 2 else "4"])
        s.rect(0, y + 2, T - 1, y + 3, C[body[i]])
    s.px(6, 13, C["S"]); s.px(7, 13, C["B"])
    return s


def shop_counter():
    """술 좌판: 널빤지(G04) 위 병 2개. 줄눈은 2줄만."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    s.line(0, 0, T - 1, 0, C["3"]); s.line(0, 8, T - 1, 8, C["3"]); s.line(0, 15, T - 1, 15, C["2"])
    for bx in (3, 10):
        s.rect(bx, 2, bx + 2, 11, C["7"])
        s.rect(bx, 2, bx + 2, 3, C["2"]); s.px(bx + 1, 2, C["7"])
        s.rect(bx, 6, bx + 2, 10, C["B"])
        s.line(bx + 2, 7, bx + 2, 10, C["S"])
        s.px(bx, 5, C["9"])
        s.line(bx, 12, bx + 2, 12, C["2"])
    return s


# ============================================================ 소품 (투명 배경, 셀아웃 K) — 37·40라운드 그림을 정돈 (잡점·과한 강조 제거)
def prop_barrel():
    s = new()
    prof = {2: (5, 10), 3: (4, 11), 4: (3, 12), 5: (3, 12), 6: (2, 13), 7: (2, 13), 8: (2, 13), 9: (2, 13),
            10: (2, 13), 11: (3, 12), 12: (3, 12), 13: (3, 12), 14: (4, 11), 15: (5, 10)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["4"])
        s.px(x0, y, C["5"]); s.px(x1, y, C["2"]); s.px(x1 - 1, y, C["3"])
    for x in (6, 9):
        s.line(x, 4, x, 14, C["3"])
    for y in (5, 12):
        x0, x1 = prof[y]
        s.line(x0, y, x1, y, C["6"])
        s.line(x0 + 1, y + 1, x1 - 1, y + 1, C["3"])
    s.line(5, 2, 10, 2, C["5"]); s.line(4, 3, 11, 3, C["5"])
    s.px(8, 14, C["S"]); s.px(8, 15, C["S"])
    s.outline(C["K"], where="inside")
    s.line(6, 2, 9, 2, C["5"], only=C["K"])
    return s


def prop_bottle():
    """깨진 병: 누운 병 + 깨진 끝. 흘러나온 술은 S 덩어리 하나."""
    s = new()
    s.rect(9, 10, 13, 11, C["S"]); s.rect(10, 9, 12, 9, C["S"])
    s.rect(5, 5, 11, 8, C["7"])
    s.rect(2, 6, 4, 7, C["7"])
    s.line(5, 5, 10, 5, C["9"]); s.line(5, 8, 10, 8, C["6"])
    s.px(11, 6, C["K"]); s.px(11, 8, C["K"])
    s.outline(C["K"], where="inside")
    s.line(6, 5, 10, 5, C["9"], only=C["K"])
    return s


def prop_puddle():
    """웅덩이(통과) — v4: 꺼진 판석 자리에 고인 검은 물 + 쇠 배수구 뚜껑. '배수구' 는 바닥 변형이 아니라 이 소품으로만 나온다(방당 ≤2)."""
    s = new()
    rows = {4: (5, 10), 5: (3, 12), 6: (2, 13), 7: (2, 13), 8: (2, 13), 9: (3, 13), 10: (4, 12), 11: (6, 11)}
    for y, (x0, x1) in rows.items():
        s.line(x0, y, x1, y, C["K"])
    for x, y in [(5, 4), (6, 4), (3, 5), (4, 5), (2, 6), (2, 7)]:
        s.px(x, y, C["1"])                                          # 먼 쪽 젖은 테
    # 배수구 뚜껑 (쇠살 3줄, G04/G03) — 물 속에 반쯤
    s.rect(7, 6, 11, 9, C["4"])                                     # 쇠 뚜껑 테 G04
    for x in (8, 10):
        s.line(x, 7, x, 8, C["K"])                                  # 살 사이 구멍
    s.line(7, 6, 11, 6, C["5"]); s.line(7, 9, 11, 9, C["3"])
    s.px(4, 8, C["S"]); s.px(5, 8, C["B"])                           # 등불 반사 2px
    s.line(6, 12, 11, 12, C["1"])
    return s


def prop_lantern():
    s = new()
    s.rect(5, 14, 10, 14, C["5"]); s.rect(4, 15, 11, 15, C["3"])
    s.line(7, 9, 7, 13, C["5"]); s.line(8, 9, 8, 13, C["4"])
    s.rect(4, 2, 11, 8, C["6"])
    s.rect(5, 3, 10, 7, C["B"])
    s.rect(6, 4, 9, 6, C["L"])
    s.px(7, 5, C["W"]); s.px(8, 5, C["W"])
    s.line(4, 2, 11, 2, C["7"])
    s.rect(6, 0, 9, 1, C["6"])
    s.outline(C["K"], where="inside")
    s.px(7, 0, C["7"]); s.px(8, 0, C["7"])
    return s


def prop_ash_pit():
    """잔불 금(통과, 이름 ash_pit 유지) — v4: 판석이 별 모양으로 깨지고 그 금 사이로만 잔불이 비친다(심 W 1 · L 2 · B 3 · S 몇 점).
    '금 사이 잔불' 은 바닥 변형이 아니라 이 소품(방당 ≤1)이 맡는다 — 균등 섞기 바닥에 넣으면 화면에 수백 개가 된다."""
    s = new()
    for pts in ([(8, 9), (5, 7), (2, 7)], [(8, 9), (6, 12), (5, 14)], [(8, 9), (11, 12), (13, 13)],
                [(8, 9), (11, 7), (14, 6)], [(8, 9), (8, 5), (9, 2)]):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            s.line(x0, y0, x1, y1, C["K"])
    s.px(8, 9, C["W"]); s.px(7, 8, C["L"]); s.px(9, 10, C["L"])
    s.px(6, 7, C["B"]); s.px(10, 8, C["B"]); s.px(7, 11, C["B"])
    s.px(5, 7, C["S"]); s.px(8, 6, C["S"]); s.px(11, 12, C["S"]); s.px(12, 7, C["S"])
    for x, y in [(6, 9), (10, 10), (9, 7)]:
        s.px(x, y, C["3"])                                           # 들뜬 판석 모서리
    return s


def prop_bottle_crate():
    s = new()
    s.rect(2, 6, 13, 14, C["4"])
    s.line(2, 6, 13, 6, C["5"]); s.line(2, 6, 2, 14, C["5"])
    s.line(3, 14, 13, 14, C["3"]); s.line(13, 7, 13, 14, C["3"])
    s.line(2, 10, 13, 10, C["3"])
    s.rect(3, 4, 12, 5, C["1"])
    s.outline(C["K"], where="inside")
    s.line(3, 6, 12, 6, C["5"], only=C["K"])
    for i, x in enumerate((3, 6, 9, 12)):
        s.px(x, 2, C["5"]); s.rect(x, 3, x, 5, C["7"])
        if i == 1:
            s.px(x, 5, C["B"]); s.px(x, 4, C["B"])
    return s


def prop_wine_jar():
    s = new()
    prof = {3: (6, 9), 4: (5, 10), 5: (4, 11), 6: (3, 12), 7: (2, 13), 8: (2, 13), 9: (2, 13), 10: (2, 13),
            11: (3, 12), 12: (3, 12), 13: (4, 11), 14: (5, 10)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["4"])
        s.px(x0, y, C["5"]); s.px(x0 + 1, y, C["5"]); s.px(x1, y, C["2"]); s.px(x1 - 1, y, C["3"])
    s.line(6, 2, 9, 2, C["5"])
    s.px(9, 2, C["K"]); s.px(10, 3, C["K"])
    s.line(6, 4, 6, 7, C["6"]); s.px(7, 4, C["6"])
    for x, y in [(10, 7), (10, 8), (11, 9), (11, 10), (10, 11)]:
        s.px(x, y, C["K"])
    s.px(11, 11, C["S"]); s.px(11, 12, C["S"])
    s.outline(C["K"], where="inside")
    s.line(6, 2, 8, 2, C["5"], only=C["K"])
    s.rect(12, 14, 13, 14, C["S"])
    return s


def prop_cup_pile():
    s = new()
    s.rect(3, 5, 6, 9, C["4"]); s.line(3, 5, 6, 5, C["6"]); s.px(4, 6, C["K"]); s.px(5, 6, C["K"])
    s.rect(8, 7, 12, 10, C["4"]); s.line(8, 7, 12, 7, C["5"]); s.rect(12, 7, 13, 10, C["6"]); s.px(13, 8, C["K"]); s.px(13, 9, C["K"])
    s.rect(4, 11, 7, 13, C["4"]); s.line(4, 11, 7, 11, C["5"])
    s.outline(C["K"], where="inside")
    s.line(4, 5, 5, 5, C["6"], only=C["K"])
    s.rect(9, 13, 10, 13, C["S"])
    return s


def void_tile():
    return new()


def tiles():
    return (
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


# (short, solid, maxPerRoom, weight) — 40라운드 값 그대로 (JSON 규약 유지)
PROPS = [("barrel", True, 2, 0.8), ("broken_bottle", False, 3, 1.0), ("puddle", False, 2, 0.8), ("lantern", True, 1, 0.6),
         ("ash_pit", False, 1, 0.6), ("bottle_crate", True, 1, 0.5), ("wine_jar", True, 1, 0.4), ("cup_pile", False, 3, 1.0)]
NAME = "잔(盞) — 술독 제국 외곽"
