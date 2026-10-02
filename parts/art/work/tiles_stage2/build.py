#!/usr/bin/env python3
"""LOPAD 2층 '패(牌)' 도박장 제국 타일셋 (16x16) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage2/build.py
입력: parts/art/palette/lopad.json (무채 16 + 2층 녹색 램프), assets/sprites/player/player_idle.png
산출: assets/tiles/stage2.png / stage2.json (1층과 같은 레이아웃·인덱스 표, tilecommon.py 참조)
      parts/art/work/tiles_stage2/preview.png · preview_room.png · preview_seam.png

컨셉 (story text-pack B2·D2, world-bible 2-0): 길바닥에 깔린 패 사이로 사람이 들려 나간다.
  바닥 = 닳은 마루널 + 흩어진 카드·칩 + 펠트 테이블 자국 / 벽 = 판자 + 공고 포스터 / 소품 = 주사위 통·판돈 자루·뒤집힌 의자·초록 등불.
색 예산: 무채 10 (G00~G07, G09, G12) + 강조 4 (18 shadow2 펠트, 21 base 칩·등불, 23 light1, 25 glow). 녹색은 펠트·칩·등불에만.
바닥 명도 대역은 1층과 동일 (본색 G04, 틈 G02, 하이라이트 G05, 그늘 G03).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon as tc  # noqa: E402

G = tc.G
A = tc.ramp(2)
T = tc.T

C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
    "F": A[2],   # 18 shadow2 — 펠트(어두운 녹색)
    "B": A[5],   # 21 base   — 칩·등불 유리
    "L": A[7],   # 23 light1 — 칩 중심·불빛
    "W": A[9],   # 25 glow   — 등불 심지
}
ctx = tc.Ctx(C)
new, blit = ctx.new, ctx.blit


# ============================================================ 바닥 (마루널 가로 3장: y0/6/11 틈)
GAPS = (0, 6, 11)


def board_floor(seams=(), grain=(), stains=()):
    """가로 널 3장. 모든 변형이 같은 y 에 틈(G02)·하이라이트(G05)를 두어 어떤 조합으로도 이어진다.
    seams: 널 끝이음 (x, 행번호). grain: 나뭇결 G03 짧은 가로선 (x0,x1,y). stains: G02 얼룩 점."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    for y in GAPS:
        s.line(0, y, T - 1, y, C["2"])
        s.line(0, y + 1, T - 1, y + 1, C["5"])
    bands = {0: (1, 5), 1: (7, 10), 2: (12, 15)}
    for x, b in seams:
        y0, y1 = bands[b]
        s.line(x, y0, x, y1, C["2"])
        s.px(x + 1, y0, C["4"])  # 끝이음 뒤 널의 하이라이트는 끊김
    for x0, x1, y in grain:
        s.line(x0, y, x1, y, C["3"])
    for x, y in stains:
        s.px(x, y, C["2"])
    return s


def card(s, x, y, pip=True):
    """카드 3x4: 종이 G07, 좌상단 빛 G09, 우·하 그늘 G02, 중앙 점 G03 (바닥 G04 위에서 조용히 읽히게)."""
    s.rect(x, y, x + 2, y + 3, C["7"])
    s.px(x, y, C["9"]); s.px(x + 1, y, C["9"]); s.px(x, y + 1, C["9"])
    s.line(x, y + 4, x + 3, y + 4, C["2"]); s.line(x + 3, y, x + 3, y + 4, C["2"])
    if pip:
        s.px(x + 1, y + 2, C["3"])


def chip(s, x, y, top=True):
    """칩 4x3 납작한 원반(탑다운): 녹색 B, 가운데 L 2px, 아래 그늘 G02. 십자형은 별표처럼 보여서 둥글게."""
    s.line(x + 1, y, x + 2, y, C["B"])
    s.line(x, y + 1, x + 3, y + 1, C["B"]); s.px(x + 1, y + 1, C["L"]); s.px(x + 2, y + 1, C["L"])
    s.line(x + 1, y + 2, x + 2, y + 2, C["B"])
    s.line(x + 1, y + 3, x + 2, y + 3, C["2"])


def floor_0():
    s = board_floor(seams=[(5, 0), (12, 1), (3, 2)], grain=[(8, 10, 3), (1, 3, 9), (9, 12, 14)])
    return s


def floor_1():
    s = board_floor(seams=[(10, 0), (2, 1), (8, 2)], grain=[(3, 5, 4), (13, 14, 8)])
    card(s, 3, 7)
    return s


def floor_2():
    s = board_floor(seams=[(7, 0), (13, 1), (6, 2)], grain=[(2, 4, 2), (9, 11, 13)])
    chip(s, 10, 8)
    card(s, 4, 12)
    return s


def floor_3():
    """펠트 테이블 자국: 테이블을 끌어낸 자리에 남은 어두운 녹색 얼룩 + 다리 자국 G02."""
    s = board_floor(seams=[(4, 0), (9, 1), (14, 2)], grain=[(11, 13, 4)])
    blob = {7: (8, 10), 8: (6, 12), 9: (5, 12), 10: (6, 11), 12: (7, 9)}
    for y, (x0, x1) in blob.items():
        s.line(x0, y, x1, y, C["F"])
    s.px(11, 11, C["F"]); s.px(12, 11, C["F"])
    for y in GAPS:
        s.line(0, y, T - 1, y, C["2"], only=C["F"])  # 틈은 얼룩 위로 보인다
    for x, y in [(2, 13), (3, 13), (13, 3)]:
        s.px(x, y, C["2"])  # 테이블 다리 자국
    return s


FLOORS = [floor_0(), floor_1(), floor_2(), floor_3()]


# ============================================================ 복도 (세로 널, 방보다 한 단 어둡다)
def corridor_tile():
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    ends = [9, 3, 13]
    for i, x in enumerate((0, 5, 10)):
        s.line(x, 0, x, T - 1, C["2"])
        s.line(x + 1, 0, x + 1, T - 1, C["4"])
        e = ends[i]
        s.line(x + 1, e, x + 4, e, C["2"])
    s.line(15, 0, 15, 15, C["2"])
    for x, y in [(3, 6), (12, 12)]:
        s.px(x, y, C["2"])
    s.px(7, 2, C["5"]); s.px(13, 8, C["5"])
    return s


# ============================================================ 벽
def wall_face():
    """판자벽: 세로 판자 4장(4px), 틈 K, 왼쪽 빛 G02. 판자에 긁어 쓴 셈 자국(G03, D2 '한 판만 더' 아홉 번)
    과 못 머리. 포스터는 16px 마다 반복되면 사물함처럼 읽혀서 뺐다. 아랫단 K 그늘."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["1"])
    for x in (0, 4, 8, 12):
        s.line(x, 0, x, T - 1, C["K"])
        s.line(x + 1, 0, x + 1, T - 2, C["2"])
    # 못 머리
    for x, y in [(2, 2), (6, 13), (10, 2), (14, 13)]:
        s.px(x, y, C["3"])
    # 셈 자국: 세로 4 + 사선 1 (x9..11, y5..8), 아래에 짧은 두 번째 묶음
    for x in (9, 10, 11):
        s.line(x, 5, x, 8, C["3"] if x != 10 else C["4"])
    s.px(13, 6, C["3"]); s.px(13, 7, C["3"])
    s.line(9, 8, 11, 6, C["4"])
    s.line(9, 11, 9, 12, C["3"]); s.line(11, 11, 11, 12, C["3"])
    # 판자 옹이
    s.px(6, 7, C["K"]); s.px(7, 7, C["2"])
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_top():
    """벽 윗면: 판자 덮개. G01 바탕, 이음 K, 윗면 빛 G02, 못 G02."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["1"])
    for y in (0, 8):
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["2"])
    s.line(5, 0, 5, 7, C["K"])
    s.line(12, 8, 12, 15, C["K"])
    for x, y in [(2, 4), (9, 4), (10, 4), (4, 12), (14, 12)]:
        s.px(x, y, C["2"])
    return s


# ============================================================ 문
def door_frame(s):
    """1층과 같은 문설주·상인방 틀 (나무 G03/G04). 바탕 G01."""
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["3"]); s.line(0, 0, 0, T - 1, C["K"]); s.line(1, 0, 1, T - 1, C["4"])
    s.rect(13, 0, 15, T - 1, C["3"]); s.line(15, 0, 15, T - 1, C["K"]); s.line(13, 0, 13, T - 1, C["2"])
    s.rect(0, 0, T - 1, 1, C["3"]); s.line(0, 0, T - 1, 0, C["K"]); s.line(3, 1, 12, 1, C["4"])


def door_open():
    """열린 문: 틀 안으로 복도 세로 널이 이어진다. 문짝은 왼쪽에 젖혀져 2px."""
    s = new()
    door_frame(s)
    s.rect(3, 2, 12, 15, C["3"])
    for x in (5, 10):
        s.line(x, 2, x, 15, C["2"])
        s.line(x + 1, 2, x + 1, 15, C["4"])
    s.line(3, 2, 3, 15, C["2"]); s.line(4, 2, 4, 15, C["4"])
    s.line(6, 9, 9, 9, C["2"])
    s.rect(3, 2, 4, 14, C["5"]); s.line(4, 2, 4, 14, C["4"])
    s.px(3, 5, C["7"]); s.px(3, 12, C["7"]); s.px(4, 5, C["6"]); s.px(4, 12, C["6"])
    s.line(3, 15, 4, 15, C["2"])
    return s


def door_planks(s, x0=3, x1=12, y0=2, y1=15):
    """문짝: 세로 널 G04, 틈 G02, 쇠띠 G06 + 리벳 G09."""
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
    """닫힌 문: 널문 + 눈높이 들여다보는 쪽창(쇠살 G06, 안쪽 K) — 도박장 문."""
    s = new()
    door_frame(s)
    door_planks(s)
    s.rect(5, 7, 10, 8, C["K"]); s.px(7, 7, C["6"]); s.px(7, 8, C["6"]); s.px(9, 7, C["6"]); s.px(9, 8, C["6"])
    s.px(10, 11, C["7"]); s.px(10, 12, C["K"])   # 손잡이 고리
    return s


def door_locked():
    """잠긴 문(보스 방): 닫힌 문 + 사슬 사선(G07 고리) + 자물쇠. 녹색 없음."""
    s = new()
    door_frame(s)
    door_planks(s)
    s.rect(5, 7, 10, 8, C["K"]); s.px(7, 7, C["6"]); s.px(7, 8, C["6"]); s.px(9, 7, C["6"]); s.px(9, 8, C["6"])
    # 사슬: 좌하→우상 2px 고리들
    for i, (x, y) in enumerate([(3, 14), (4, 13), (5, 12), (6, 11), (7, 10), (8, 9), (9, 8), (10, 7), (11, 6), (12, 5)]):
        s.px(x, y, C["7"] if i % 2 == 0 else C["6"])
    s.px(2, 14, C["7"]); s.px(13, 5, C["7"])
    # 자물쇠 (중앙 아래): 몸통 G07, 고리 G09, 열쇠구멍 K
    s.rect(6, 11, 9, 14, C["7"]); s.line(6, 11, 9, 11, C["9"])
    s.px(6, 10, C["9"]); s.px(9, 10, C["9"])
    s.px(7, 12, C["K"]); s.px(8, 12, C["K"]); s.px(7, 13, C["K"])
    return s


# ============================================================ 출구 · 상점 (2x2)
def exit_stairs():
    """올라가는 나무 계단 4단. 챌 K, 디딤 윗변 G07, 디딤 G05/G04. 위에서 비껴드는 녹색빛 2px x2."""
    s = new()
    body = ["5", "5", "4", "4"]
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["7"])
        s.rect(0, y + 2, T - 1, y + 3, C[body[i]])
        s.line(0, y + 3, T - 1, y + 3, C["3"] if i >= 2 else C["4"])
        if i in (0, 2):
            s.px(12, y + 1, C["L"]); s.px(13, y + 1, C["L"])
    for x, y in [(3, 2), (9, 6), (6, 10), (14, 14)]:
        s.px(x, y, C["3"])
    return s


def shop_counter():
    """종군 상인 좌판: 널 탁자(G04) 위 펠트 깔개(F, 10x10) + 칩 더미 2 + 카드 2. 2x2 로 깔면 깔개 4장."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["2"])
        s.line(0, y + 1, T - 1, y + 1, C["5"])
    s.line(0, 15, T - 1, 15, C["2"])
    s.rect(3, 3, 12, 12, C["F"])
    s.line(3, 13, 13, 13, C["2"]); s.line(13, 3, 13, 13, C["2"])  # 깔개 그늘
    # 칩 더미 (세로 쌓임): 3폭, 흰 칩(G12)·녹색 칩(B, 가운데 L) 번갈아. 펠트와 분리되도록 흰 줄이 들어간다.
    for bx, h in ((4, 5), (9, 3)):
        for i in range(h):
            y = 11 - i
            if i % 2 == 0:
                s.line(bx, y, bx + 2, y, C["B"]); s.px(bx + 1, y, C["L"])
            else:
                s.line(bx, y, bx + 2, y, C["C"])
        s.px(bx + 3, 11, C["2"]); s.px(bx + 3, 10, C["2"])
    # 카드 2장 (겹침)
    card(s, 8, 4)
    s.rect(10, 5, 11, 7, C["9"]); s.px(12, 5, C["2"]); s.px(12, 6, C["2"]); s.px(12, 7, C["2"]); s.line(10, 8, 12, 8, C["2"])
    s.px(11, 6, C["3"])
    return s


# ============================================================ 소품 (투명 배경)
def prop_dice_cup():
    """주사위 통(통과 가능): 가죽 통 G06 (왼쪽 빛 G07, 오른쪽 그늘 G05) + 흰 주사위 2개(G12, 눈 K)."""
    s = new()
    s.rect(5, 4, 10, 11, C["6"])
    s.line(5, 4, 5, 11, C["7"]); s.line(6, 4, 6, 11, C["7"])
    s.line(10, 4, 10, 11, C["5"])
    s.line(5, 4, 10, 4, C["7"])
    s.rect(5, 3, 10, 3, C["5"]); s.rect(6, 2, 9, 2, C["4"])  # 입구(어두운 안쪽이 보임)
    s.rect(6, 3, 9, 3, C["3"])
    s.line(5, 12, 10, 12, C["2"])  # 바닥 그림자
    for dx, dy in ((11, 9), (1, 10)):
        s.rect(dx, dy, dx + 2, dy + 2, C["C"])
        s.px(dx + 1, dy + 1, C["K"])
        s.px(dx + 3, dy + 2, C["2"]); s.line(dx, dy + 3, dx + 3, dy + 3, C["2"])
    s.outline(C["K"], where="inside")
    for dx, dy in ((11, 9), (1, 10)):
        s.rect(dx, dy, dx + 2, dy + 2, C["C"]); s.px(dx + 1, dy + 1, C["K"])
        s.px(dx + 3, dy + 2, C["2"]); s.line(dx, dy + 3, dx + 3, dy + 3, C["2"])
    s.line(5, 12, 10, 12, C["2"])
    return s


def prop_sack():
    """판돈 자루(solid): 불룩한 삼베 자루 G06 (왼쪽 빛 G07, 오른쪽 그늘 G05), 목은 끈(K)으로 묶임.
    꼬리표 G09 + 쏟아진 칩 2개(B/L)."""
    s = new()
    prof = {2: (6, 9), 3: (6, 9), 4: (5, 10), 5: (4, 11), 6: (3, 12), 7: (3, 12), 8: (2, 13), 9: (2, 13),
            10: (2, 13), 11: (2, 13), 12: (3, 12), 13: (3, 12), 14: (4, 11)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["6"])
        s.px(x0, y, C["7"]); s.px(x0 + 1, y, C["7"])
        s.px(x1, y, C["5"])
    s.line(6, 4, 9, 4, C["K"]); s.px(5, 5, C["K"])   # 묶은 끈
    s.rect(6, 1, 9, 2, C["5"]); s.px(7, 1, C["6"])     # 자루 입(접힌 천)
    for y in (7, 9, 11):
        s.px(8 + (y // 2) % 2, y, C["5"])             # 삼베 결
    s.rect(11, 6, 12, 8, C["9"]); s.px(12, 7, C["3"])  # 꼬리표(오른쪽 어깨)
    s.line(4, 15, 12, 15, C["2"])                      # 그림자
    s.outline(C["K"], where="inside")
    s.line(4, 15, 12, 15, C["2"])
    chip(s, 12, 12)
    chip(s, 0, 12)
    return s


def prop_chair():
    """뒤집힌 의자(통과 가능): 옆으로 넘어진 나무 의자. 등받이 세로 살 2개(왼쪽), 앉는 판(가운데), 다리 2개(오른쪽)."""
    s = new()
    # 등받이 (x1..4): 윗가로대 + 살 2개 + 아랫가로대
    s.rect(1, 3, 4, 3, C["5"]); s.rect(1, 12, 4, 12, C["4"])
    s.line(1, 3, 1, 12, C["4"]); s.line(3, 3, 3, 12, C["4"]); s.px(1, 4, C["5"]); s.px(3, 4, C["5"])
    # 앉는 판 (x5..9, y5..10)
    s.rect(5, 5, 9, 10, C["4"]); s.line(5, 5, 9, 5, C["5"]); s.line(5, 5, 5, 10, C["5"]); s.line(5, 10, 9, 10, C["3"]); s.line(9, 6, 9, 10, C["3"])
    s.px(7, 7, C["3"]); s.px(7, 8, C["3"])  # 판 틈
    # 다리 2개 (오른쪽으로 뻗음) + 가로 받침
    s.line(10, 6, 14, 6, C["5"]); s.line(10, 7, 14, 7, C["3"])
    s.line(10, 10, 14, 10, C["5"]); s.line(10, 11, 14, 11, C["3"])
    s.line(12, 8, 12, 9, C["4"])
    # 바닥 그림자
    s.line(2, 13, 9, 13, C["2"])
    s.outline(C["K"], where="inside")
    s.line(2, 13, 9, 13, C["2"])
    s.px(1, 3, C["5"]); s.px(2, 3, C["5"]); s.px(5, 5, C["5"]); s.px(6, 5, C["5"])
    return s


def prop_lantern():
    """초록 등불(solid): 갈고리 기둥에 매단 둥근 초롱 (도박장 처마 등). 기둥 G05/G04, 초롱 B, 안쪽 빛 L, 심지 W, 살 G06.
    1층 세운 등불과 실루엣을 다르게 — 둥근 등이 왼쪽에 매달린다. 녹색 ~26px."""
    s = new()
    # 기둥 (x11..12, y3..13) + 받침
    s.line(11, 3, 11, 13, C["5"]); s.line(12, 3, 12, 13, C["4"])
    s.rect(9, 14, 14, 14, C["5"]); s.rect(8, 15, 15, 15, C["3"])
    # 갈고리: 기둥 꼭대기에서 왼쪽으로 꺾여 내려옴
    s.line(7, 1, 12, 1, C["5"]); s.px(6, 2, C["5"]); s.px(12, 2, C["4"])
    s.px(6, 3, C["6"])  # 걸이 고리
    # 초롱 (x3..9, y4..11): 둥근 몸통
    prof = {4: (5, 7), 5: (4, 8), 6: (3, 9), 7: (3, 9), 8: (3, 9), 9: (3, 9), 10: (4, 8), 11: (5, 7)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["B"])
    s.rect(5, 6, 7, 9, C["L"]); s.px(4, 7, C["L"]); s.px(4, 8, C["L"])
    s.px(6, 7, C["W"]); s.px(6, 8, C["W"])
    # 살 (가로 2줄) + 위아래 틀
    for y in (6, 9):
        s.px(3, y, C["6"]); s.px(9, y, C["6"])
    s.line(5, 4, 7, 4, C["6"]); s.line(5, 11, 7, 11, C["6"]); s.px(6, 12, C["6"])  # 꼬리 술
    s.px(6, 13, C["5"])
    s.outline(C["K"], where="inside")
    s.line(8, 1, 11, 1, C["5"], only=C["K"])
    return s


def void_tile():
    return new()


TILES = [
    ("floor_0", FLOORS[0]), ("floor_1", FLOORS[1]), ("floor_2", FLOORS[2]), ("floor_3", FLOORS[3]),
    ("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
    ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
    ("exit", exit_stairs()), ("shop", shop_counter()),
    ("prop_dice_cup", prop_dice_cup()), ("prop_sack", prop_sack()), ("prop_chair", prop_chair()),
    ("prop_lantern", prop_lantern()),
]
PROPS = [("dice_cup", False), ("stake_sack", True), ("overturned_chair", False), ("green_lantern", True)]

if __name__ == "__main__":
    tc.run(2, "패(牌) — 도박장 제국 외곽", TILES, PROPS, [18, 21, 23, 25], HERE)
