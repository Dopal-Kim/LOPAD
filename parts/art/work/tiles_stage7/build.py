#!/usr/bin/env python3
"""LOPAD 7층 '적(赤)' 붉은 근위 제국 타일셋 (16x16, 8열×4행) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage7/build.py
입력: parts/art/palette/lopad.json (무채 16 + 7층 진홍 램프), assets/sprites/player/player_idle.png
산출: assets/tiles/stage7.png / stage7.json (37라운드 인덱스 표, tiles_floors/tilecommon2.py 참조)
      parts/art/work/tiles_stage7/preview.png · preview_room.png · preview_rooms.png · preview_seam.png

컨셉 (story text-pack B7·C7·D7, world-bible 7층 / 37라운드 "붉은 피 섞인 흙"):
  붉은 외투가 줄지어 서 있다. 바닥이 더 붉다. 적(赤). 외투는 염색이 아니다.
  바닥 = 피 섞인 검은 흙(G01) — 마른 핏자국 S, 젖은 피 B/L (5% 한도 안), 군화 자국, 탄흔
  벽   = 큰 돌 쌓은 성벽(G01/K) + 창살 창 + 걸린 붉은 외투 / 변형 19 = 외투 두 벌 나란히(줄지어) / 변형 20 = 벽에 튄 피 + 쇠사슬 + 긁힌 자국
  문   = 쇠문 (열림: 쇠문짝 젖힘 / 닫힘: 리벳 철판 + 창살 틈 / 잠김: 가로 쇠빗장 + 자물쇠)
  출구 = 돌계단 + 붉은 빛 / 상점 = 종군 상인 좌판 (창끝·투구·개킨 외투)
  소품 = 걸린 외투(solid) · 창 다발(solid) · 핏자국 웅덩이(통과) · 화로(solid, 진홍 불)
         · 처형대(solid, 도끼 박힌 나무 토막) · 잔불 더미(통과)
  방 바닥 = 시작: 줄지어 선 군화 자국 / 시련: 탄흔·핏자국 / 휴식: 식은 재·잔불 / 보스: 더 검은 흙, 바닥이 더 붉다(넓은 핏자국)
색 예산: 무채 10 (G00~G07, G09, G12) + 강조 4 (19 shadow1 마른 피, 21 base 외투·젖은 피, 23 light1, 25 glow 불).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon2 as tc  # noqa: E402

G = tc.G
A = tc.ramp(7)
T = tc.T

C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
    "S": A[3],   # 19 shadow1 — 마른 피·외투 그늘·숯불 속
    "B": A[5],   # 21 base   — 외투·젖은 피
    "L": A[7],   # 23 light1 — 외투 빛·불꽃 테·피 반사
    "W": A[9],   # 25 glow   — 불꽃 심·잔불
}
ctx = tc.Ctx(C)
new, blit = ctx.new, ctx.blit


# ============================================================ 바닥 (피 섞인 검은 흙)
def dirt(seed, base="1", clods=16, pits=6, glints=3, clod="2", pit="K", glint="3"):
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


BLOBS = [
    [(0, 0), (1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (0, 2)],                       # 비스듬한 덩어리
    [(0, 0), (1, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (1, 2), (2, 2)],               # 오른쪽으로 번짐
    [(-1, 0), (0, 0), (0, 1), (1, 1), (2, 1), (1, 2)],                                # 작은 덩어리
    [(0, -1), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (3, 1), (1, 2)],  # 넓은 얼룩
]


def blood(s, rnd, cx, cy, r=1, wet=True, drops=2):
    """핏자국: 손으로 그린 불규칙 덩어리(BLOBS) 를 S 로, 젖은 가운데 B 1~2px, 튄 방울 S.
    (tc.splat 의 r=1 은 십자(+) 로 읽혀서 쓰지 않는다.)"""
    blob = BLOBS[rnd.randrange(len(BLOBS))] if r <= 1 else BLOBS[3]
    for dx, dy in blob:
        x, y = cx + dx, cy + dy
        if 0 <= x < T and 0 <= y < T:
            s.px(x, y, C["S"])
    if wet:
        s.px(cx, cy, C["B"])
        if r >= 2:
            s.px(cx + 1, cy, C["B"])
    for _ in range(drops):
        dx = rnd.choice([-1, 1]) * rnd.randint(2, 4)
        dy = rnd.choice([-1, 1]) * rnd.randint(0, 3)
        x, y = cx + dx, cy + dy
        if 0 <= x < T and 0 <= y < T:
            s.px(x, y, C["S"])


def floor_0():
    s, rnd = dirt(701)
    s.px(12, 11, C["S"])
    return s


def floor_1():
    s, rnd = dirt(702, clods=14)
    blood(s, rnd, 5, 9, r=1)
    return s


def floor_2():
    s, rnd = dirt(703, clods=14)
    for x, y in [(9, 3), (10, 4), (10, 6), (11, 7), (11, 9)]:
        s.px(x, y, C["S"])                              # 끌려간 핏줄
    s.px(11, 9, C["B"])
    return s


def floor_3():
    s, rnd = dirt(704, clods=15, pits=7)
    blood(s, rnd, 12, 5, r=1, wet=False, drops=3)
    tc.bootprint(s, C, 3, 8, left=True)
    return s


def floor_start(i):
    """시작 방: 줄지어 선 군화 자국 — 근위병이 서 있던 자리. 핏자국은 없다."""
    s, rnd = dirt(711 + i, clods=12, pits=3)
    if i == 0:
        tc.bootprint(s, C, 3, 3, left=True); tc.bootprint(s, C, 6, 3, left=False)
        s.px(12, 11, C["K"]); s.px(13, 11, C["K"])
    else:
        tc.bootprint(s, C, 9, 8, left=True); tc.bootprint(s, C, 12, 8, left=False)
        s.px(2, 12, C["S"])
    return s


def floor_trial(i):
    """시련 방: 탄흔(K 구덩이) 과 핏자국 — 처형 집행관의 자리."""
    s, rnd = dirt(721 + i, clods=12, pits=5)
    if i == 0:
        tc.pock(s, C, 4, 4); tc.pock(s, C, 11, 10)
        blood(s, rnd, 8, 12, r=1, drops=2)
    else:
        tc.pock(s, C, 12, 3)
        blood(s, rnd, 4, 9, r=1, wet=False, drops=3)
        s.px(9, 6, C["S"]); s.px(10, 6, C["S"])
    return s


def floor_rest(i):
    """휴식 방: 식은 재(G03) 와 잔불(W/L/B) — 근위병이 쬐던 불 자리."""
    s, rnd = dirt(731 + i, clods=11, pits=4, glints=2)
    if i == 0:
        tc.ash_patch(s, C, rnd, 10, 5, r=2)
        tc.ember(s, C, 10, 5, rising=True)
        tc.ember_small(s, C, 3, 12)
    else:
        for x, y in [(4, 4), (5, 4), (12, 11), (7, 13)]:
            s.px(x, y, C["3"])
        tc.ember_small(s, C, 5, 5)
        s.px(12, 12, C["W"])
    return s


def floor_boss(i):
    """보스 방 (근위 총사령): 더 검은 흙(G00) 에 넓은 핏자국 — '바닥이 더 붉다'. 강조 ≤ 5% 는 방 단위로 지킨다."""
    s, rnd = dirt(741 + i, base="K", clod="1", pit="1", glint="2", clods=18, pits=0, glints=3)
    if i == 0:
        blood(s, rnd, 5, 6, r=2, drops=2)
        s.px(6, 6, C["L"])
    else:
        blood(s, rnd, 11, 10, r=1, drops=2)
        s.px(3, 3, C["S"]); s.px(4, 3, C["S"])
    return s


# ============================================================ 복도 (어두운 흙 + 끌려간 핏줄)
def corridor_tile():
    s, rnd = dirt(705, base="K", clod="1", pit="1", glint="2", clods=14, pits=0, glints=2)
    for y in range(T):
        x = 7 + (1 if y % 5 in (2, 3) else 0)
        s.px(x, y, C["S"])
    s.px(8, 4, C["B"]); s.px(7, 11, C["B"])
    return s


# ============================================================ 벽
def fort_wall(s):
    """성벽: 큰 돌 2단(8px), 이음 K, 돌 윗변 G02, 돌 G01, 아랫단 K."""
    s.rect(0, 0, T - 1, T - 1, C["1"])
    for i in range(2):
        y = i * 8
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["2"])
        for x in ((0, 8) if i == 0 else (4, 12)):
            s.line(x, y, x, y + 7, C["K"])
    s.line(0, 15, T - 1, 15, C["K"])


def coat(s, x, y):
    """걸린 붉은 외투 (x..x+4, y..y+9): 고리 G07, 깃 K, 몸 B, 왼쪽 빛 L 1줄, 오른쪽·주름 S, 아랫단 너덜."""
    s.px(x + 2, y, C["7"])
    s.rect(x + 1, y + 1, x + 3, y + 1, C["K"])
    s.rect(x, y + 2, x + 4, y + 8, C["B"])
    s.line(x, y + 2, x, y + 8, C["L"])
    s.line(x + 4, y + 2, x + 4, y + 8, C["S"]); s.px(x + 2, y + 4, C["S"]); s.px(x + 2, y + 5, C["S"]); s.px(x + 2, y + 7, C["S"])
    s.px(x, y + 9, C["B"]); s.px(x + 2, y + 9, C["S"]); s.px(x + 4, y + 9, C["B"])


def barred_window(s, x0, y0):
    """창살 창 5x6: 틀 G03, 안 K, 쇠살 G06 둘."""
    s.rect(x0, y0, x0 + 4, y0 + 5, C["3"])
    s.rect(x0 + 1, y0 + 1, x0 + 3, y0 + 4, C["K"])
    s.line(x0 + 2, y0 + 1, x0 + 2, y0 + 4, C["6"])
    s.line(x0 + 1, y0 + 2, x0 + 3, y0 + 2, C["5"])


def wall_face():
    """성벽 + 창살 창(왼쪽) + 걸린 외투 한 벌(오른쪽). B7 '붉은 외투가 줄지어 서 있다'."""
    s = new()
    fort_wall(s)
    barred_window(s, 2, 3)
    coat(s, 9, 2)
    return s


def wall_v1():
    """벽 변형 1: 외투 두 벌 나란히 — 줄. 한 벌은 더 낡아(S 많음) 염색이 아님을 안다."""
    s = new()
    fort_wall(s)
    coat(s, 2, 2)
    coat(s, 9, 3)
    s.px(10, 7, C["S"]); s.px(11, 9, C["S"]); s.px(9, 11, C["S"])
    return s


def wall_v2():
    """벽 변형 2: 벽에 튄 피(S 가 아래로 흘러내림, 젖은 B 1px) + 걸린 쇠사슬(G06/G07 고리) + 손톱 긁힌 자국(K 3줄)."""
    s = new()
    fort_wall(s)
    rnd = random.Random(77)
    for x0, x1, y in [(3, 6, 3), (2, 7, 4), (3, 6, 5)]:
        s.line(x0, y, x1, y, C["S"])
    for x, y in [(4, 6), (4, 7), (4, 8), (4, 9), (6, 6), (6, 7), (2, 6), (3, 10)]:
        s.px(x, y, C["S"])
    s.px(4, 4, C["B"]); s.px(5, 4, C["B"])
    for i, y in enumerate(range(1, 13)):
        s.px(12, y, C["7"] if i % 2 == 0 else C["6"])
    s.px(11, 13, C["7"]); s.px(12, 13, C["6"]); s.px(13, 13, C["7"])
    for x in (8, 9, 10):
        s.line(x, 8, x, 11, C["K"])
    return s


def wall_top():
    """벽 윗면: 성벽 덮개 (G01, K 이음) + 쇠못 머리(G05) 둘."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["1"])
    for y in (0, 8):
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["2"])
    s.line(7, 0, 7, 7, C["K"]); s.line(3, 8, 3, 15, C["K"]); s.line(11, 8, 11, 15, C["K"])
    s.px(3, 4, C["5"]); s.px(13, 12, C["5"])
    return s


# ============================================================ 문 (쇠문)
def door_frame(s):
    """문설주·상인방 틀 — 7층은 돌 틀(G03/G04) 에 쇠 보강(G06 점)."""
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["3"]); s.line(0, 0, 0, T - 1, C["K"]); s.line(1, 0, 1, T - 1, C["4"])
    s.rect(13, 0, 15, T - 1, C["3"]); s.line(15, 0, 15, T - 1, C["K"]); s.line(13, 0, 13, T - 1, C["2"])
    s.rect(0, 0, T - 1, 1, C["3"]); s.line(0, 0, T - 1, 0, C["K"]); s.line(3, 1, 12, 1, C["4"])
    for x, y in [(1, 4), (1, 11), (14, 4), (14, 11)]:
        s.px(x, y, C["6"])


def iron_plate(s, x0=3, x1=12, y0=2, y1=15):
    """쇠문짝: 철판 G05, 가로 띠 G06 두 줄, 리벳 G07, 아랫단 G04 녹."""
    s.rect(x0, y0, x1, y1, C["5"])
    s.line(x0, y0, x1, y0, C["6"])
    for y in (y0 + 3, y0 + 10):
        s.line(x0, y, x1, y, C["6"])
        for x in (x0 + 1, x0 + 4, x0 + 7):
            s.px(x, y, C["7"])
    s.rect(x0, y1 - 1, x1, y1, C["4"])
    s.px(x0 + 2, y1, C["3"]); s.px(x1 - 1, y1 - 1, C["3"])


def door_open():
    """열린 쇠문: 틀 안으로 복도 흙과 핏줄. 문짝은 왼쪽에 젖혀져 2px (철판 G05/G04)."""
    s = new()
    door_frame(s)
    cor = corridor_tile()
    for y in range(2, 16):
        for x in range(3, 13):
            s.px(x, y, cor.get(x, y)[:3])
    s.rect(3, 2, 4, 14, C["5"]); s.line(4, 2, 4, 14, C["4"])
    s.px(3, 5, C["7"]); s.px(3, 12, C["7"])
    s.line(3, 15, 4, 15, C["2"])
    return s


def door_closed():
    """닫힌 쇠문: 철판 + 눈높이 창살 틈(K, 살 G07) + 손잡이 고리."""
    s = new()
    door_frame(s)
    iron_plate(s)
    s.rect(5, 7, 10, 8, C["K"]); s.px(7, 7, C["7"]); s.px(7, 8, C["7"]); s.px(9, 7, C["7"]); s.px(9, 8, C["7"])
    s.px(10, 11, C["7"]); s.px(10, 12, C["K"])
    return s


def door_locked():
    """잠긴 쇠문(보스 방): 가로 쇠빗장 두 줄(G07/G06) + 자물쇠 + 빗장에 마른 피 S."""
    s = new()
    door_frame(s)
    iron_plate(s)
    s.rect(5, 7, 10, 8, C["K"]); s.px(7, 7, C["7"]); s.px(7, 8, C["7"]); s.px(9, 7, C["7"]); s.px(9, 8, C["7"])
    for y in (4, 11):
        s.line(2, y, 13, y, C["7"]); s.line(2, y + 1, 13, y + 1, C["6"])
        s.px(3, y, C["9"]); s.px(12, y, C["9"])
    s.rect(6, 9, 9, 12, C["7"]); s.line(6, 9, 9, 9, C["9"])
    s.px(7, 10, C["K"]); s.px(8, 10, C["K"]); s.px(7, 11, C["K"])
    s.px(4, 12, C["S"]); s.px(5, 12, C["S"]); s.px(4, 13, C["S"])
    return s


# ============================================================ 출구 · 상점 (2x2)
def exit_stairs():
    """올라가는 돌계단 4단 (1·4·5층 구조). 위에서 비껴드는 붉은 빛 W/L 2px x2."""
    s = new()
    body = ["5", "5", "4", "4"]
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["7"])
        s.rect(0, y + 2, T - 1, y + 3, C[body[i]])
        s.line(0, y + 3, T - 1, y + 3, C["3"] if i >= 2 else C["4"])
        if i in (0, 2):
            s.px(12, y + 1, C["W"]); s.px(13, y + 1, C["L"])
    for x, y in [(3, 2), (9, 6), (6, 10), (14, 14)]:
        s.px(x, y, C["3"])
    s.px(4, 7, C["S"]); s.px(5, 7, C["S"])   # 계단에 마른 피
    return s


def shop_counter():
    """종군 상인 좌판: 널 탁자 위 창끝 2개(G09/G07), 투구(G06/G05), 개킨 붉은 외투(B/S), 수통(G05)."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["2"])
        s.line(0, y + 1, T - 1, y + 1, C["5"])
    s.line(0, 15, T - 1, 15, C["2"])
    for x in (2, 4):
        s.line(x, 2, x, 9, C["7"]); s.px(x, 2, C["9"]); s.px(x, 3, C["9"]); s.px(x, 9, C["3"])
    s.rect(7, 2, 11, 6, C["6"]); s.line(7, 2, 11, 2, C["7"]); s.rect(8, 5, 10, 6, C["K"]); s.px(9, 4, C["5"])
    s.rect(7, 9, 12, 12, C["B"]); s.line(7, 12, 12, 12, C["S"]); s.px(12, 9, C["S"]); s.line(8, 10, 11, 10, C["L"])
    s.rect(2, 11, 4, 13, C["5"]); s.px(3, 10, C["6"]); s.px(2, 13, C["3"])
    return s


# ============================================================ 소품 (투명 배경)
def prop_hung_coat():
    """걸린 외투(solid): 옷걸이 기둥(G05/G04, 받침 G03) 에 걸린 붉은 외투. D7 '염색이 아니다' — 아랫단 S 얼룩."""
    s = new()
    s.line(7, 1, 7, 13, C["5"]); s.line(8, 1, 8, 13, C["4"])
    s.rect(5, 14, 10, 14, C["4"]); s.rect(4, 15, 11, 15, C["3"])
    s.line(4, 2, 11, 2, C["6"]); s.px(4, 3, C["6"]); s.px(11, 3, C["6"])   # 가로 걸이
    s.rect(4, 4, 10, 4, C["K"])                                             # 깃
    s.rect(3, 5, 11, 12, C["B"])
    s.line(3, 5, 3, 12, C["L"]); s.line(4, 5, 4, 7, C["L"])
    s.line(11, 5, 11, 12, C["S"]); s.line(7, 6, 7, 12, C["S"])              # 앞여밈
    for x, y in [(5, 11), (6, 12), (9, 12), (10, 11), (8, 12)]:
        s.px(x, y, C["S"])                                                  # 아랫단 얼룩
    s.px(5, 13, C["B"]); s.px(9, 13, C["B"]); s.px(7, 13, C["S"])
    s.outline(C["K"], where="inside")
    s.line(4, 5, 10, 5, C["B"]); s.px(3, 6, C["L"]); s.line(4, 2, 11, 2, C["6"], only=C["K"])
    return s


def prop_spear_bundle():
    """창 다발(solid): 창 세 자루가 기대어 묶임 — 자루 G06/G05, 창끝 G09/G12, 끈 G07, 바닥 받침 G03."""
    s = new()
    s.line(5, 13, 7, 2, C["6"]); s.line(8, 13, 8, 1, C["5"]); s.line(11, 13, 9, 2, C["6"])
    for x, y in [(7, 2), (8, 1), (9, 2)]:
        s.px(x, y, C["9"]); s.px(x, y - 1 if y > 0 else y, C["C"])
    s.px(7, 1, C["C"]); s.px(8, 0, C["C"]); s.px(9, 1, C["C"])
    s.line(6, 8, 10, 8, C["7"]); s.line(6, 9, 10, 9, C["7"])                 # 묶은 끈
    s.rect(4, 14, 12, 14, C["3"]); s.rect(5, 15, 11, 15, C["2"])
    s.px(10, 11, C["S"]); s.px(9, 7, C["S"])                                 # 창끝 아래 마른 피
    s.outline(C["K"], where="inside")
    s.px(8, 0, C["C"]); s.px(7, 1, C["C"]); s.px(9, 1, C["C"]); s.px(8, 1, C["C"])
    s.line(6, 8, 10, 8, C["7"]); s.line(6, 9, 10, 9, C["7"])
    return s


def prop_blood_pool():
    """핏자국 웅덩이(통과): 마른 테 S, 안쪽 젖은 B, 반사 L 1~2px, 끌린 자국. 투명 배경. 진홍 ~34px."""
    s = new()
    for x0, x1, y in [(5, 9, 4), (4, 11, 5), (3, 12, 6), (3, 12, 7), (4, 11, 8), (5, 10, 9), (7, 9, 10)]:
        s.line(x0, y, x1, y, C["S"])
    for x0, x1, y in [(6, 9, 6), (6, 10, 7), (7, 9, 8)]:
        s.line(x0, y, x1, y, C["B"])
    s.px(7, 6, C["L"])
    for x, y in [(12, 9), (13, 10), (2, 5), (8, 12), (9, 13)]:
        s.px(x, y, C["S"])
    return s


def prop_brazier():
    """화로(solid, 진홍 불): 세발 쇠 화로(G05/G04/G03) 에 숯(S/B) 과 불꽃(L/W). 불 ~16px."""
    s = new()
    s.rect(4, 7, 11, 10, C["5"]); s.line(4, 7, 11, 7, C["6"]); s.rect(4, 10, 11, 11, C["4"])
    s.px(3, 8, C["5"]); s.px(12, 8, C["5"])
    s.line(4, 12, 3, 14, C["4"]); s.line(11, 12, 12, 14, C["4"]); s.line(7, 12, 7, 14, C["3"]); s.px(8, 13, C["3"])
    s.rect(5, 6, 10, 6, C["S"]); s.px(6, 6, C["B"]); s.px(9, 6, C["B"])      # 숯
    s.rect(6, 4, 9, 5, C["L"]); s.px(7, 3, C["L"]); s.px(8, 3, C["W"]); s.px(7, 4, C["W"]); s.px(8, 5, C["W"]); s.px(6, 2, C["L"])
    s.line(3, 15, 12, 15, C["2"])
    s.outline(C["K"], where="inside")
    s.rect(6, 4, 9, 5, C["L"]); s.px(7, 3, C["L"]); s.px(8, 3, C["W"]); s.px(7, 4, C["W"]); s.px(8, 5, C["W"]); s.px(6, 2, C["L"])
    s.rect(5, 6, 10, 6, C["S"]); s.px(6, 6, C["B"]); s.px(9, 6, C["B"])
    s.line(3, 15, 12, 15, C["2"])
    return s


def prop_execution_block():
    """처형대(solid): 나무 토막(G05 윗면/G04 옆/G03 결) 에 박힌 도끼(G07 날, G05 자루), 윗면과 옆에 피(S, 젖은 B)."""
    s = new()
    s.rect(3, 6, 12, 8, C["5"]); s.rect(3, 9, 12, 13, C["4"])
    s.line(3, 9, 12, 9, C["3"]); s.line(5, 10, 5, 13, C["3"]); s.line(9, 10, 9, 13, C["3"])
    s.rect(6, 6, 9, 7, C["S"]); s.px(7, 6, C["B"]); s.px(8, 7, C["B"]); s.px(7, 9, C["S"]); s.px(7, 10, C["S"]); s.px(7, 11, C["S"])
    s.rect(10, 2, 12, 4, C["7"]); s.px(12, 5, C["7"]); s.px(10, 2, C["9"]); s.line(9, 3, 9, 5, C["5"]); s.px(9, 2, C["5"])  # 도끼
    s.line(4, 14, 12, 14, C["2"])
    s.outline(C["K"], where="inside")
    s.line(4, 6, 11, 6, C["5"]); s.rect(6, 6, 9, 6, C["S"]); s.px(7, 6, C["B"])
    s.line(4, 14, 12, 14, C["2"]); s.px(10, 2, C["9"])
    return s


def prop_ember_pile():
    """잔불 더미(통과): 식은 재(G03/G02) 위에 아직 사는 잔불(W/L/B) 넷 — 도영 님 '잔불 올라오듯'."""
    s = new()
    rnd = random.Random(76)
    for x0, x1, y in [(5, 10, 6), (4, 11, 7), (3, 12, 8), (4, 11, 9), (5, 10, 10), (6, 9, 11)]:
        s.line(x0, y, x1, y, C["3"])
    for x, y in [(5, 7), (9, 8), (6, 10), (10, 10), (4, 8), (8, 11)]:
        s.px(x, y, C["2"])
    tc.ember(s, C, 7, 8, rising=True)
    tc.ember(s, C, 10, 9, rising=False)
    tc.ember_small(s, C, 5, 10)
    s.px(8, 6, C["L"]); s.px(9, 5, C["W"])
    return s


def void_tile():
    return new()


TILES = [
    ("floor_0", floor_0()), ("floor_1", floor_1()), ("floor_2", floor_2()), ("floor_3", floor_3()),
    ("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
    ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
    ("exit", exit_stairs()), ("shop", shop_counter()),
    ("prop_hung_coat", prop_hung_coat()), ("prop_spear_bundle", prop_spear_bundle()),
    ("prop_blood_pool", prop_blood_pool()), ("prop_brazier", prop_brazier()),
    ("prop_execution_block", prop_execution_block()), ("prop_ember_pile", prop_ember_pile()),
    ("wall_v1", wall_v1()), ("wall_v2", wall_v2()),
    ("start_0", floor_start(0)), ("start_1", floor_start(1)),
    ("trial_0", floor_trial(0)), ("trial_1", floor_trial(1)),
    ("rest_0", floor_rest(0)), ("rest_1", floor_rest(1)),
    ("boss_0", floor_boss(0)), ("boss_1", floor_boss(1)),
]
PROPS = [("hung_coat", True), ("spear_bundle", True), ("blood_pool", False), ("brazier", True),
         ("execution_block", True), ("ember_pile", False)]

if __name__ == "__main__":
    tc.run(7, "적(赤) — 붉은 근위 제국 외곽", TILES, PROPS, [19, 21, 23, 25], HERE)
