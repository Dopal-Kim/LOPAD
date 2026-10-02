#!/usr/bin/env python3
"""LOPAD 6층 '연(宴)' 연회 제국 타일셋 (16x16, 8열×4행) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage6/build.py
입력: parts/art/palette/lopad.json (무채 16 + 6층 황금 램프), assets/sprites/player/player_idle.png
산출: assets/tiles/stage6.png / stage6.json (37라운드 인덱스 표, tiles_floors/tilecommon2.py 참조)
      parts/art/work/tiles_stage6/preview.png · preview_room.png · preview_rooms.png · preview_seam.png

컨셉 (story text-pack B6·C6·D6, world-bible 6층 / 37라운드 "연회장도 바닥은 버려진 흙 위에 융단 조각만"):
  악단이 전황 소식에 맞춰 곡을 바꾼다. 경매는 후식 뒤에. 연회장 바닥은 흙 — 융단은 조각만 남고, 밟힌 꽃잎과 흘린 술.
  바닥 = 밟힌 검은 흙(G01) + 융단 조각(G03 천, 황금 가장자리) + 흘린 술(S) + 꽃잎(L/W 1px)
  벽   = 판벽 몰딩 + 촛대(황금 B, 불꽃 W/L) / 변형 19 = 빈 액자(그림은 뜯김) / 변형 20 = 벽에 끼얹은 술 + 분필 '7'(품목 7번)
  문   = 커튼 (열림: 양옆으로 묶음 / 닫힘: 주름 + 술 장식 / 잠김: 커튼 위 쇠 빗장 + 자물쇠)
  출구 = 융단 깔린 계단 / 상점 = 경매대 (목록·망치·금화)
  소품 = 경매 번호판(통과) · 엎어진 잔(통과) · 샹들리에 그림자(통과, 촛불 반사) · 황금 촛대(solid)
         · 경매 우리(solid, 품목 7번 '건강한 남자') · 먹다 남은 접시(통과)
  방 바닥 = 시작: 융단 띠 흔적·꽃잎 / 시련: 깨진 병·술 얼룩 / 휴식: 쓰러진 초의 촛농과 잔불 / 보스: 검은 흙에 황금 꽃잎 비
색 예산: 무채 10 (G00~G07, G09, G12) + 강조 4 (18 shadow2 술·융단 테, 21 base 황금, 23 light1, 25 glow 불꽃·꽃잎).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon2 as tc  # noqa: E402

G = tc.G
A = tc.ramp(6)
T = tc.T

C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
    "S": A[2],   # 18 shadow2 — 흘린 술(마른 갈색)·융단 가장자리·황금 그늘 (19 는 흙 위에서 금덩이처럼 보여 한 단 내림)
    "B": A[5],   # 21 base   — 황금(촛대·틀·금화)
    "L": A[7],   # 23 light1 — 황금 빛·꽃잎·불꽃 테
    "W": A[9],   # 25 glow   — 불꽃 심·밝은 꽃잎
}
ctx = tc.Ctx(C)
new, blit = ctx.new, ctx.blit


# ============================================================ 바닥 (밟힌 검은 흙)
def dirt(seed, base="1", clods=16, pits=6, glints=3, clod="2", pit="K", glint="3"):
    """버려진 연회장의 흙 (5층 dirt 와 같은 규칙: 랜덤워크 덩어리 + 점, 격자 없음)."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C[base])
    rnd = random.Random(seed)
    n = 0
    while n < clods:
        x, y = rnd.randrange(T), rnd.randrange(T)
        for _ in range(rnd.choice((1, 1, 2, 3, 4))):
            s.px(x, y, C[clod]); n += 1
            x += rnd.choice((-1, 0, 1, 1)); y += rnd.choice((-1, 0, 0, 1))
            if not (0 <= x < T and 0 <= y < T):
                break
    for _ in range(pits):
        x, y = rnd.randrange(T), rnd.randrange(T)
        s.px(x, y, C[pit])
        if rnd.random() < 0.35 and x + 1 < T:
            s.px(x + 1, y, C[pit])
    for _ in range(glints):
        s.px(rnd.randrange(T), rnd.randrange(T), C[glint])
    return s, rnd


def petals(s, pts):
    """밟힌 꽃잎: 밝은 황금 1px (W) 와 그 옆 L 1px — 어두운 흙 위에서 또렷이."""
    for i, (x, y) in enumerate(pts):
        s.px(x, y, C["W"] if i % 2 == 0 else C["L"])


def carpet_scrap(s, x0, y0, x1, y1, fray=()):
    """융단 조각: 천 G03, 올 풀린 가장자리 G02, 황금 테(S) 한 변. fray: 뜯긴 점 (x,y)."""
    s.rect(x0, y0, x1, y1, C["3"])
    s.line(x0, y1, x1, y1, C["2"]); s.px(x1, y0, C["2"])
    s.line(x0, y0, x1 - 1, y0, C["S"])
    for x, y in fray:
        s.px(x, y, C["2"])


def wine(s, rnd, cx, cy, r=2, drops=2):
    tc.splat(s, C, rnd, cx, cy, r=r, dark="S", wet="L", drops=drops)


def floor_0():
    s, rnd = dirt(601)
    petals(s, [(12, 4)])
    return s


def floor_1():
    s, rnd = dirt(602, clods=13)
    carpet_scrap(s, 3, 8, 9, 12, fray=[(3, 10), (9, 9), (6, 12)])
    s.px(10, 11, C["2"])
    return s


def floor_2():
    s, rnd = dirt(603, clods=14)
    wine(s, rnd, 10, 5, r=1, drops=2)
    petals(s, [(3, 12)])
    return s


def floor_3():
    s, rnd = dirt(604, clods=15, pits=7)
    s.px(5, 4, C["5"]); s.px(6, 4, C["4"]); s.px(12, 11, C["5"])     # 깨진 유리
    petals(s, [(9, 9)])
    return s


def floor_start(i):
    """시작 방: 융단이 깔렸던 띠 자국(길게 남은 조각) + 꽃잎 몇 장 — 손님이 들어오던 길."""
    s, rnd = dirt(611 + i, clods=12, pits=4)
    if i == 0:
        carpet_scrap(s, 2, 6, 9, 9, fray=[(2, 7), (4, 9), (9, 6)])
        petals(s, [(12, 12), (11, 3)])
    else:
        carpet_scrap(s, 10, 10, 14, 13, fray=[(10, 12), (12, 13)])
        petals(s, [(3, 4), (5, 13)])
    return s


def floor_trial(i):
    """시련 방: 깨진 병(G05/G04 조각) 과 술 얼룩 — 연회가 싸움으로."""
    s, rnd = dirt(621 + i, clods=12, pits=6)
    if i == 0:
        wine(s, rnd, 5, 10, r=1, drops=3)
        for x, y in [(11, 3), (12, 4), (13, 3)]:
            s.px(x, y, C["5"])
        s.px(12, 3, C["4"])
    else:
        tc.splat(s, C, rnd, 11, 7, r=1, dark="S", wet=None, drops=2)
        s.px(3, 4, C["5"]); s.px(4, 5, C["4"]); s.px(2, 12, C["5"])
        petals(s, [(8, 13)])
    return s


def floor_rest(i):
    """휴식 방: 쓰러진 초 — 굳은 촛농(G12/G09) 과 꺼져 가는 심지(잔불 W/L)."""
    s, rnd = dirt(631 + i, clods=11, pits=4, glints=2)
    if i == 0:
        s.rect(9, 4, 11, 5, C["7"]); s.px(12, 5, C["7"]); s.px(10, 4, C["9"])
        tc.ember(s, C, 13, 4, rising=True)
        petals(s, [(3, 11)])
    else:
        s.px(4, 9, C["7"]); s.px(5, 9, C["9"]); s.px(5, 10, C["7"])
        tc.ember_small(s, C, 13, 12)
    return s


def floor_boss(i):
    """보스 방 (연회 후작의 홀): 더 검은 흙(G00) 위에 황금 꽃잎이 비처럼 — 후작의 건배."""
    s, rnd = dirt(641 + i, base="K", clod="1", pit="1", glint="2", clods=18, pits=0, glints=4)
    pts = [(2, 3), (3, 3), (11, 6), (7, 12), (13, 13)] if i == 0 else [(5, 2), (12, 9), (3, 13)]
    petals(s, pts)
    return s


# ============================================================ 복도 (어두운 흙 + 가운데 융단 띠 잔해)
def corridor_tile():
    s, rnd = dirt(605, base="K", clod="1", pit="1", glint="2", clods=14, pits=0, glints=2)
    s.rect(5, 0, 10, T - 1, C["2"])
    for y in (0, 3, 7, 12):
        s.px(5, y, C["S"]); s.px(10, y + 1, C["S"])        # 끊어진 황금 테
    for x, y in [(6, 2), (9, 5), (7, 9), (8, 13), (6, 14)]:
        s.px(x, y, C["1"])                                   # 닳은 자리
    return s


# ============================================================ 벽
def panel_wall(s):
    """연회장 판벽: 바탕 G01, 위·아래 몰딩(G03 위 G02), 판 틀 G02, 아랫단 K."""
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.line(0, 0, T - 1, 0, C["K"]); s.line(0, 1, T - 1, 1, C["3"]); s.line(0, 2, T - 1, 2, C["2"])
    s.line(0, 12, T - 1, 12, C["2"]); s.line(0, 13, T - 1, 13, C["3"]); s.line(0, 14, T - 1, 14, C["2"])
    s.line(0, 15, T - 1, 15, C["K"])
    s.rect(1, 4, 6, 11, C["2"], fill=False); s.rect(9, 4, 14, 11, C["2"], fill=False)


def sconce(s, x, y, lit=True):
    """벽 등: 황금 틀(B, 3x4) 안에 촛불(L, 심 W), 아래 받침 S. lit=False 면 틀만 남고 안은 어둡다(K).
    (1차 시안의 '초 + 불꽃' 은 16px 에서 아래 화살표처럼 읽혀 등 모양으로 바꿈)"""
    s.rect(x - 1, y, x + 1, y + 3, C["B"])
    s.px(x - 1, y + 3, C["S"]); s.px(x + 1, y + 3, C["S"])
    s.px(x, y + 4, C["S"])
    if lit:
        s.px(x, y + 1, C["L"]); s.px(x, y + 2, C["W"])
    else:
        s.px(x, y + 1, C["K"]); s.px(x, y + 2, C["K"]); s.px(x + 1, y, C["K"])


def wall_face():
    """판벽 + 촛대 하나 (오른쪽 판 가운데). 왼쪽 판에 벽지 얼룩(G00)."""
    s = new()
    panel_wall(s)
    sconce(s, 11, 5)
    for x, y in [(3, 6), (3, 7), (4, 8)]:
        s.px(x, y, C["K"])
    return s


def wall_v1():
    """벽 변형 1: 빈 액자 — 금박 틀(B/S) 안의 그림은 뜯겨 나가고 캔버스 조각(G03)만. 촛대는 꺼짐."""
    s = new()
    panel_wall(s)
    s.rect(2, 4, 8, 10, C["S"]); s.line(2, 4, 8, 4, C["B"]); s.line(2, 4, 2, 10, C["B"])
    s.rect(3, 5, 7, 9, C["K"])
    s.px(4, 6, C["3"]); s.px(5, 6, C["3"]); s.px(4, 7, C["3"]); s.px(6, 8, C["3"])
    sconce(s, 12, 5, lit=False)
    return s


def wall_v2():
    """벽 변형 2: 끼얹은 술(S 얼룩이 흘러내림) + 분필로 쓴 '7' (G07, D6 품목 7번) + 떼어진 촛대 자리(못 2개)."""
    s = new()
    panel_wall(s)
    rnd = random.Random(66)
    for x0, x1, y in [(2, 5, 4), (1, 6, 5), (2, 5, 6)]:
        s.line(x0, y, x1, y, C["S"])
    for x, y in [(3, 7), (3, 8), (3, 9), (5, 7), (5, 8), (2, 7), (4, 10)]:
        s.px(x, y, C["S"])
    s.px(3, 5, C["L"])                                    # 젖은 반사
    s.line(10, 5, 13, 5, C["7"]); s.px(13, 6, C["7"]); s.px(12, 7, C["7"]); s.px(12, 8, C["7"]); s.px(11, 9, C["7"]); s.px(11, 10, C["7"])
    s.px(10, 11, C["4"]); s.px(14, 11, C["4"])            # 못
    return s


def wall_top():
    """벽 윗면: 처마 돌림띠 — G01 바탕, 이음 K, 몰딩 G02 두 줄."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.line(0, 0, T - 1, 0, C["K"]); s.line(0, 8, T - 1, 8, C["K"])
    s.line(0, 3, T - 1, 3, C["2"]); s.line(0, 11, T - 1, 11, C["2"])
    s.line(5, 0, 5, 7, C["K"]); s.line(12, 8, 12, 15, C["K"])
    s.px(9, 5, C["3"]); s.px(3, 13, C["3"])
    return s


# ============================================================ 문
def door_frame(s):
    """1층과 같은 문설주·상인방 틀 (G03/G04). 바탕 G01."""
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["3"]); s.line(0, 0, 0, T - 1, C["K"]); s.line(1, 0, 1, T - 1, C["4"])
    s.rect(13, 0, 15, T - 1, C["3"]); s.line(15, 0, 15, T - 1, C["K"]); s.line(13, 0, 13, T - 1, C["2"])
    s.rect(0, 0, T - 1, 1, C["3"]); s.line(0, 0, T - 1, 0, C["K"]); s.line(3, 1, 12, 1, C["4"])


def curtain_rod(s):
    s.line(3, 2, 12, 2, C["6"]); s.px(3, 2, C["7"]); s.px(12, 2, C["7"])


def door_open():
    """열린 문: 커튼이 양옆으로 묶였다(G06/G05 3폭, 황금 끈 B). 틀 안은 복도 흙."""
    s = new()
    door_frame(s)
    cor = corridor_tile()
    for y in range(2, 16):
        for x in range(3, 13):
            s.px(x, y, cor.get(x, y)[:3])
    curtain_rod(s)
    for x0 in (3, 10):
        s.rect(x0, 3, x0 + 2, 14, C["5"]); s.line(x0 + 1, 3, x0 + 1, 14, C["6"])
        s.px(x0 + 2, 9, C["4"]); s.px(x0, 9, C["4"])
        s.line(x0, 8, x0 + 2, 8, C["B"]); s.px(x0 + 1, 9, C["S"])  # 묶은 끈
    return s


def curtain_full(s):
    """닫힌 커튼: 세로 주름 (G05 / G06 빛 / G04 그늘) 반복, 아래 황금 술 B/S."""
    s.rect(3, 3, 12, 14, C["5"])
    for x in (4, 8, 12):
        s.line(x, 3, x, 14, C["6"])
    for x in (6, 10):
        s.line(x, 3, x, 14, C["4"])
    s.line(3, 15, 12, 15, C["K"])
    for x in range(3, 13, 2):
        s.px(x, 14, C["B"]); s.px(x + 1, 14, C["S"])


def door_closed():
    s = new()
    door_frame(s)
    curtain_rod(s)
    curtain_full(s)
    s.px(7, 6, C["B"]); s.px(8, 6, C["L"]); s.px(7, 7, C["S"]); s.px(8, 7, C["B"])  # 가운데 황금 걸쇠
    return s


def door_locked():
    """잠긴 문(보스 방): 커튼 위로 쇠 빗장(G07/G06) 두 줄 + 자물쇠."""
    s = new()
    door_frame(s)
    curtain_rod(s)
    curtain_full(s)
    for y in (5, 11):
        s.line(2, y, 13, y, C["7"]); s.line(2, y + 1, 13, y + 1, C["6"])
        s.px(3, y, C["9"]); s.px(12, y, C["9"])
    s.rect(6, 7, 9, 10, C["7"]); s.line(6, 7, 9, 7, C["9"])
    s.px(7, 8, C["K"]); s.px(8, 8, C["K"]); s.px(7, 9, C["K"])
    return s


# ============================================================ 출구 · 상점 (2x2)
def exit_stairs():
    """융단 깔린 돌계단 4단: 가운데 띠(G03 천, 황금 테 S) + 위에서 비껴드는 황금 빛 W/L 2px x2."""
    s = new()
    body = ["5", "5", "4", "4"]
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["7"])
        s.rect(0, y + 2, T - 1, y + 3, C[body[i]])
        s.line(0, y + 3, T - 1, y + 3, C["3"] if i >= 2 else C["4"])
        s.rect(5, y + 1, 10, y + 3, C["3"]); s.line(5, y + 1, 10, y + 1, C["2"])
        s.px(5, y + 2, C["S"]); s.px(10, y + 2, C["S"])
        if i in (0, 2):
            s.px(12, y + 1, C["W"]); s.px(13, y + 1, C["L"])
    s.px(7, 6, C["2"]); s.px(8, 10, C["2"])   # 닳은 융단
    return s


def shop_counter():
    """경매대: 널 탁자 위 경매 목록(G12, 글줄 G07) + 망치(G07 머리/G05 자루) + 금화 더미(B/L)."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["2"])
        s.line(0, y + 1, T - 1, y + 1, C["5"])
    s.line(0, 15, T - 1, 15, C["2"])
    s.rect(2, 3, 7, 9, C["C"]); s.line(2, 10, 8, 10, C["2"]); s.line(8, 3, 8, 10, C["2"])
    for y in (4, 6, 8):
        s.line(3, y, 6, y, C["7"])
    s.px(5, 6, C["3"])                                     # '7번' 줄에 표시
    s.rect(10, 3, 13, 5, C["7"]); s.line(10, 3, 13, 3, C["9"]); s.line(11, 6, 11, 11, C["5"]); s.px(11, 11, C["4"])
    s.line(10, 12, 13, 12, C["B"]); s.line(9, 13, 13, 13, C["B"]); s.px(10, 12, C["L"]); s.px(11, 13, C["L"]); s.px(13, 13, C["S"])
    return s


# ============================================================ 소품 (투명 배경)
def prop_paddle():
    """경매 번호판(통과): 모난 판(G12, 모서리 둥글림) 에 큰 '7'(K 3x5) 과 손잡이(G05/G04). 흙 위에 버려짐."""
    s = new()
    s.rect(4, 2, 10, 9, C["C"])
    for x, y in [(4, 2), (10, 2), (4, 9), (10, 9)]:
        s.px(x, y, C["9"])
    s.line(6, 4, 8, 4, C["K"]); s.px(8, 5, C["K"]); s.px(8, 6, C["K"]); s.px(7, 7, C["K"]); s.px(7, 8, C["K"])
    s.line(7, 10, 7, 14, C["5"]); s.line(8, 10, 8, 14, C["4"])
    s.line(5, 10, 10, 10, C["2"])
    s.outline(C["K"], where="inside")
    s.rect(5, 2, 9, 2, C["9"]); s.px(4, 3, C["9"]); s.px(4, 8, C["9"])
    s.line(5, 10, 6, 10, C["2"]); s.line(9, 10, 10, 10, C["2"])
    return s


def prop_spilled_cup():
    """엎어진 잔(통과): 옆으로 누운 금속 잔(G07/G09, 받침 G05) 과 쏟아진 술(S, 반사 L)."""
    s = new()
    rnd = random.Random(62)
    for x0, x1, y in [(8, 11, 9), (7, 13, 10), (9, 13, 11), (11, 12, 12)]:
        s.line(x0, y, x1, y, C["S"])
    s.px(10, 10, C["L"])
    s.rect(2, 6, 7, 9, C["7"]); s.line(2, 6, 7, 6, C["9"]); s.line(7, 6, 7, 9, C["K"])
    s.rect(0, 4, 1, 11, C["5"]); s.px(1, 5, C["6"])         # 받침(세워진 원반)
    s.px(8, 7, C["K"]); s.px(8, 8, C["K"])                  # 잔 입구 어둠
    s.line(2, 10, 7, 10, C["2"])
    return s


def prop_chandelier_shadow():
    """샹들리에 그림자(통과): 흙 위에 떨어진 둥근 그림자(K 고리) 와 촛불 반사(W/L 점 여섯) — 머리 위에 아직 불이 켜져 있다."""
    s = new()
    s.circle(8, 8, 6, C["K"], fill=False)
    s.circle(8, 8, 3, C["K"], fill=False)
    for x, y in [(8, 2), (8, 14), (2, 8), (14, 8)]:
        s.px(x, y, C["1"])
    for i, (x, y) in enumerate([(8, 3), (12, 5), (13, 11), (8, 13), (3, 11), (4, 5)]):
        s.px(x, y, C["W"] if i % 2 == 0 else C["L"])
    s.px(8, 8, C["L"])
    return s


def prop_candelabra():
    """황금 촛대(solid): 세 갈래 촛대(B, 그늘 S), 초 G12 세 자루, 불꽃 W/L. 황금 ~22px."""
    s = new()
    s.line(7, 7, 7, 13, C["B"]); s.line(8, 7, 8, 13, C["S"])
    s.rect(5, 14, 10, 14, C["B"]); s.rect(4, 15, 11, 15, C["S"])
    s.line(3, 7, 12, 7, C["B"]); s.px(3, 6, C["B"]); s.px(12, 6, C["B"]); s.px(12, 7, C["S"])
    for x in (3, 7, 12):
        s.px(x, 5, C["C"]); s.px(x, 4, C["C"])
        s.px(x, 3, C["W"]); s.px(x, 2, C["L"])
    s.px(7, 6, C["C"])
    s.outline(C["K"], where="inside")
    for x in (3, 7, 12):
        s.px(x, 3, C["W"]); s.px(x, 2, C["L"]); s.px(x, 4, C["C"])
    s.px(7, 5, C["C"]); s.px(3, 5, C["C"]); s.px(12, 5, C["C"])
    return s


def prop_cage():
    """경매 우리(solid): 쇠창살 우리(G05 살, G04 틀, 안 K) + 번호표 G12 '7'. D6 '품목 7번: 건강한 남자, 치아 양호'."""
    s = new()
    s.rect(2, 2, 13, 13, C["K"])
    s.rect(2, 2, 13, 2, C["4"]); s.rect(2, 13, 13, 13, C["4"]); s.line(2, 2, 2, 13, C["4"]); s.line(13, 2, 13, 13, C["4"])
    for x in (5, 8, 11):
        s.line(x, 3, x, 12, C["5"])
    s.line(3, 7, 12, 7, C["4"])
    s.line(2, 14, 13, 14, C["2"])
    s.rect(9, 9, 12, 12, C["C"]); s.px(10, 10, C["K"]); s.px(11, 10, C["K"]); s.px(11, 11, C["K"])  # 번호표 '7'
    s.px(4, 5, C["6"]); s.px(6, 5, C["6"])   # 안에서 보는 것 — 밝은 점 둘(눈)
    s.outline(C["K"], where="inside")
    s.rect(3, 2, 12, 2, C["5"]); s.line(2, 14, 13, 14, C["2"])
    s.px(10, 10, C["K"]); s.px(11, 10, C["K"]); s.px(11, 11, C["K"]); s.rect(9, 9, 12, 9, C["C"]); s.px(9, 10, C["C"]); s.px(9, 11, C["C"]); s.rect(9, 12, 12, 12, C["C"])
    return s


def prop_plate():
    """먹다 남은 접시(통과): 둥근 접시(G09 테, G07 안) 위 뼈 두 조각(G12) 과 포크(G05)."""
    s = new()
    s.circle(7, 8, 5, C["7"], fill=True)
    s.circle(7, 8, 5, C["9"], fill=False)
    s.line(5, 7, 9, 7, C["C"]); s.px(4, 6, C["C"]); s.px(10, 8, C["C"])
    s.line(6, 10, 9, 10, C["C"]); s.px(10, 11, C["C"])
    s.line(12, 3, 14, 5, C["5"]); s.px(14, 6, C["5"]); s.px(12, 2, C["6"])
    s.outline(C["K"], where="inside")
    s.px(7, 3, C["9"]); s.px(2, 8, C["9"]); s.px(7, 13, C["9"]); s.px(12, 8, C["9"])
    s.px(12, 2, C["6"])
    return s


def void_tile():
    return new()


TILES = [
    ("floor_0", floor_0()), ("floor_1", floor_1()), ("floor_2", floor_2()), ("floor_3", floor_3()),
    ("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
    ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
    ("exit", exit_stairs()), ("shop", shop_counter()),
    ("prop_paddle", prop_paddle()), ("prop_spilled_cup", prop_spilled_cup()),
    ("prop_chandelier_shadow", prop_chandelier_shadow()), ("prop_candelabra", prop_candelabra()),
    ("prop_cage", prop_cage()), ("prop_plate", prop_plate()),
    ("wall_v1", wall_v1()), ("wall_v2", wall_v2()),
    ("start_0", floor_start(0)), ("start_1", floor_start(1)),
    ("trial_0", floor_trial(0)), ("trial_1", floor_trial(1)),
    ("rest_0", floor_rest(0)), ("rest_1", floor_rest(1)),
    ("boss_0", floor_boss(0)), ("boss_1", floor_boss(1)),
]
PROPS = [("auction_paddle", False), ("spilled_cup", False), ("chandelier_shadow", False),
         ("gold_candelabra", True), ("auction_cage", True), ("plate_bones", False)]

if __name__ == "__main__":
    tc.run(6, "연(宴) — 연회 제국 외곽", TILES, PROPS, [18, 21, 23, 25], HERE)
