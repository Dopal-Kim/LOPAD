#!/usr/bin/env python3
"""LOPAD 8층 '평상' 황제의 수도 타일셋 (16x16, 8열×4행) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage8/build.py
입력: parts/art/palette/lopad.json (무채 16 + 8층 은빛 흰 램프), assets/sprites/player/player_idle.png
산출: assets/tiles/stage8.png / stage8.json (37라운드 인덱스 표, tiles_floors/tilecommon2.py 참조)
      parts/art/work/tiles_stage8/preview.png · preview_room.png · preview_rooms.png · preview_seam.png

컨셉 (story text-pack B8·D8, world-bible 8층 / 37라운드 "수도는 고르지만 생기 없는 잿빛 흙·돌가루"):
  거리에 다툼도, 발소리도 없다. 모두가 평등하다. 조용하다 — 이 도시에서 가장 비싼 것이다.
  바닥 = 고르게 다져진 잿빛 흙(G02 기조, 돌가루 G03, 패인 곳 G01 조금) — 덩어리도 격자도 없이 '고른' 흙. 드물게 돌가루 반짝임(W 1px)
  벽   = 매끈한 흰 석벽(G05) 에 똑같은 창(불 꺼짐) / 변형 19 = 똑같은 공고판(글줄만, 내용 없음) / 변형 20 = 덧문 닫힌 창 둘
  문   = 흰 문 (열림: 문짝 젖힘 / 닫힘: 판 두 칸 + 손잡이 / 잠김: 쇠 빗장 + 자물쇠)
  출구 = 흰 돌계단 + 은빛 / 상점 = 흰 천 좌판에 똑같은 병 셋·상자 셋 (모두가 평등하다)
  소품 = 빈 벤치(solid) · 꺼진 가로등(solid) · 똑같은 화분(solid, 마른 관목) · 바닥의 작은 균열 하나(통과)
         · 빈 좌대(solid, 동상은 없다) · 쓸어 모은 재(통과)
  방 바닥 = 시작: 비질 자국 / 시련: 흐트러진 자갈 몇 알 / 휴식: 쓸어 둔 재 / 보스: 더 어두운 흙(G01) 에 돌가루 반짝임 — 황제의 광장
  8층은 다른 층과 반대로 벽이 바닥보다 밝다 — 흰 도시가 잿빛 흙 위에 서 있다. 바닥은 G02 기조라 주인공(K 윤곽·G03 외투) 실루엣은 유지.
색 예산: 무채 10 (G00~G07, G09, G12) + 강조 4 (19 shadow1 유리 반사, 21 base, 23 light1 테, 25 glow 돌가루·빛).
  은빛 램프는 무채와 거의 같은 명도라 '강조' 는 차가운 기운으로만 남는다 — 이 층의 의도(생기 없음).
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon2 as tc  # noqa: E402

G = tc.G
A = tc.ramp(8)
T = tc.T

C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
    "S": A[3],   # 19 shadow1 — 꺼진 유리의 반사·창 안 반사
    "B": A[5],   # 21 base   — 돌 테두리 은빛
    "L": A[7],   # 23 light1 — 벤치·화분 테 하이라이트
    "W": A[9],   # 25 glow   — 돌가루 반짝임·계단 빛
}
ctx = tc.Ctx(C)
new, blit = ctx.new, ctx.blit


# ============================================================ 바닥 (고른 잿빛 흙)
def dust(seed, base="2", grains=7, pits=4, dark="1", grain="3", pairs=0):
    """고르게 다져진 잿빛 흙. 덩어리 없이 돌가루(grain) 와 패인 곳(dark) 1px 만 성기게 — '고르지만 생기 없는'."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C[base])
    rnd = random.Random(seed)
    for _ in range(grains):
        s.px(rnd.randrange(T), rnd.randrange(T), C[grain])
    for _ in range(pits):
        x, y = rnd.randrange(T), rnd.randrange(T)
        s.px(x, y, C[dark])
    for _ in range(pairs):
        x, y = rnd.randrange(T - 1), rnd.randrange(T)
        s.px(x, y, C[dark]); s.px(x + 1, y, C[dark])
    return s, rnd


def floor_0():
    s, rnd = dust(801)
    return s


def floor_1():
    s, rnd = dust(802, grains=6)
    s.px(11, 4, C["W"])
    return s


def floor_2():
    s, rnd = dust(803, grains=8, pits=3)
    s.px(4, 10, C["4"]); s.px(5, 10, C["4"])   # 자갈 한 알
    return s


def floor_3():
    s, rnd = dust(804, grains=6, pits=5)
    s.px(13, 12, C["4"])
    s.px(3, 3, C["1"])
    return s


def floor_start(i):
    """시작 방: 비질 자국 — 같은 방향으로 짧은 G01 선 몇 개. 누군가 쓸고 갔다. 발소리는 없었다."""
    s, rnd = dust(811 + i, grains=5, pits=1)
    lines = [(2, 4, 5), (7, 9, 6), (11, 13, 5), (4, 6, 11), (9, 11, 12)] if i == 0 else [(3, 5, 8), (8, 10, 9), (12, 14, 8), (5, 7, 2)]
    for x0, x1, y in lines:
        s.line(x0, y, x1, y, C["1"])
    return s


def floor_trial(i):
    """시련 방: 흐트러진 자갈 몇 알(G04) — 이 도시에서 유일하게 정렬되지 않은 것."""
    s, rnd = dust(821 + i, grains=6, pits=3)
    stones = [(3, 4), (10, 7), (6, 12)] if i == 0 else [(12, 3), (5, 9)]
    for x, y in stones:
        s.px(x, y, C["4"]); s.px(x + 1, y, C["4"]); s.px(x + 1, y + 1, C["1"])
    if i == 1:
        s.px(8, 13, C["4"])
    return s


def floor_rest(i):
    """휴식 방: 쓸어 둔 재(G03 작은 더미) 와 돌가루 반짝임 — 불은 없다. 재만 정돈되어 있다."""
    s, rnd = dust(831 + i, grains=5, pits=2)
    if i == 0:
        s.line(9, 5, 11, 5, C["3"]); s.line(8, 6, 12, 6, C["3"]); s.px(10, 4, C["4"]); s.px(9, 6, C["2"])
    else:
        s.line(4, 10, 6, 10, C["3"]); s.px(5, 9, C["4"])
        s.px(12, 3, C["3"])
    return s


def floor_boss(i):
    """보스 방 (황제 '평' 의 광장): 더 어두운 흙(G01) 위에 돌가루가 은빛으로 반짝인다(W/L). 가장 조용한 바닥."""
    s, rnd = dust(841 + i, base="1", grains=10, pits=3, dark="K", grain="2")
    pts = [(3, 3), (12, 10)] if i == 0 else [(9, 5)]
    for j, (x, y) in enumerate(pts):
        s.px(x, y, C["W"] if (i + j) % 2 == 0 else C["L"])
    return s


# ============================================================ 복도 (어두운 흙, 고름)
def corridor_tile():
    s, rnd = dust(805, base="1", grains=8, pits=3, dark="K", grain="2")
    s.px(7, 6, C["3"]); s.px(8, 12, C["3"])
    return s


# ============================================================ 벽 (흰 석벽 — 바닥보다 밝다)
def white_wall(s):
    """매끈한 흰 석벽: G05 바탕, 돌 이음 G04 (가로 1, 세로 2 — 아주 얇게), 윗변 G06, 바닥과 닿는 아랫단 G04/G03."""
    s.rect(0, 0, T - 1, T - 1, C["5"])
    s.line(0, 0, T - 1, 0, C["6"])
    s.line(0, 8, T - 1, 8, C["4"])
    s.line(5, 1, 5, 7, C["4"]); s.line(11, 9, 11, 13, C["4"])
    s.line(0, 14, T - 1, 14, C["4"]); s.line(0, 15, T - 1, 15, C["3"])


def dark_window(s, x0, y0, w=4, h=5):
    """불 꺼진 창: 틀 G07, 안 G01, 창살 G06 십자 없이 — 반사 S 1px. 창턱 G06."""
    s.rect(x0, y0, x0 + w - 1, y0 + h - 1, C["7"])
    s.rect(x0 + 1, y0 + 1, x0 + w - 2, y0 + h - 2, C["1"])
    s.px(x0 + 1, y0 + 1, C["S"])
    s.line(x0, y0 + h, x0 + w - 1, y0 + h, C["6"])


def wall_face():
    """흰 석벽 + 똑같은 창 하나(불 꺼짐). 집집마다 같은 창, 같은 간격."""
    s = new()
    white_wall(s)
    dark_window(s, 6, 3)
    return s


def wall_v1():
    """벽 변형 1: 똑같은 공고판(G06 판, G07 테) — 글줄(G04) 만 있고 읽을 내용은 없다. '모두가 평등하다'."""
    s = new()
    white_wall(s)
    s.rect(3, 3, 12, 9, C["7"]); s.rect(4, 4, 11, 8, C["6"])
    for y in (5, 7):
        s.line(5, y, 10, y, C["4"])
    s.px(5, 6, C["4"]); s.px(6, 6, C["4"])
    s.px(3, 3, C["9"]); s.px(12, 9, C["5"])
    return s


def wall_v2():
    """벽 변형 2: 덧문 닫힌 창 둘(G06 널, 틈 G04) — 안을 보여 주지 않는다."""
    s = new()
    white_wall(s)
    for x0 in (2, 10):
        s.rect(x0, 3, x0 + 3, 7, C["7"])
        s.rect(x0 + 1, 4, x0 + 2, 6, C["6"])
        s.px(x0 + 1, 5, C["4"]); s.px(x0 + 2, 5, C["4"])
        s.line(x0, 8, x0 + 3, 8, C["6"])
    return s


def wall_top():
    """벽 윗면: 흰 덮개돌 G06, 이음 G05, 모서리 빛 G07."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["6"])
    s.line(0, 0, T - 1, 0, C["5"]); s.line(0, 8, T - 1, 8, C["5"])
    s.line(7, 0, 7, 7, C["5"]); s.line(3, 8, 3, 15, C["5"]); s.line(11, 8, 11, 15, C["5"])
    s.px(1, 1, C["7"]); s.px(8, 1, C["7"]); s.px(4, 9, C["7"]); s.px(12, 9, C["7"])
    return s


# ============================================================ 문 (흰 문)
def door_frame(s):
    """흰 돌 문설주·상인방: 바깥 K 선, 돌 G06, 안쪽 빛 G07. 바탕 G05(벽)."""
    s.rect(0, 0, T - 1, T - 1, C["5"])
    s.rect(0, 0, 2, T - 1, C["6"]); s.line(0, 0, 0, T - 1, C["K"]); s.line(2, 0, 2, T - 1, C["7"])
    s.rect(13, 0, 15, T - 1, C["6"]); s.line(15, 0, 15, T - 1, C["K"]); s.line(13, 0, 13, T - 1, C["4"])
    s.rect(0, 0, T - 1, 1, C["6"]); s.line(0, 0, T - 1, 0, C["K"]); s.line(3, 1, 12, 1, C["7"])


def white_leaf(s, x0=3, x1=12, y0=2, y1=15):
    """흰 문짝: 판 G07, 두 칸 패널 테 G06, 아랫단 G06, 손잡이 G09."""
    s.rect(x0, y0, x1, y1, C["7"])
    s.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 5, C["6"], fill=False)
    s.rect(x0 + 1, y0 + 7, x1 - 1, y1 - 2, C["6"], fill=False)
    s.line(x0, y1, x1, y1, C["6"])
    s.px(x1 - 2, y0 + 8, C["9"]); s.px(x1 - 2, y0 + 9, C["5"])


def door_open():
    """열린 흰 문: 틀 안은 복도 흙. 문짝은 왼쪽에 젖혀져 2px."""
    s = new()
    door_frame(s)
    cor = corridor_tile()
    for y in range(2, 16):
        for x in range(3, 13):
            s.px(x, y, cor.get(x, y)[:3])
    s.rect(3, 2, 4, 14, C["7"]); s.line(4, 2, 4, 14, C["6"])
    s.px(4, 9, C["9"])
    s.line(3, 15, 4, 15, C["4"])
    return s


def door_closed():
    s = new()
    door_frame(s)
    white_leaf(s)
    return s


def door_locked():
    """잠긴 흰 문(보스 방): 검은 쇠 빗장(G04/G03) 두 줄 + 자물쇠(G05, 구멍 K) — 흰 도시에서 유일하게 검은 것."""
    s = new()
    door_frame(s)
    white_leaf(s)
    for y in (4, 11):
        s.line(2, y, 13, y, C["4"]); s.line(2, y + 1, 13, y + 1, C["3"])
        s.px(3, y, C["6"]); s.px(12, y, C["6"])
    s.rect(6, 7, 9, 10, C["5"]); s.line(6, 7, 9, 7, C["7"]); s.px(6, 6, C["7"]); s.px(9, 6, C["7"])
    s.px(7, 8, C["K"]); s.px(8, 8, C["K"]); s.px(7, 9, C["K"])
    return s


# ============================================================ 출구 · 상점 (2x2)
def exit_stairs():
    """올라가는 흰 돌계단 4단: 챌 G03, 디딤 윗변 G09, 디딤 G06/G05. 위에서 비껴드는 은빛 W/L 2px x2."""
    s = new()
    body = ["6", "6", "5", "5"]
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["3"])
        s.line(0, y + 1, T - 1, y + 1, C["9"])
        s.rect(0, y + 2, T - 1, y + 3, C[body[i]])
        s.line(0, y + 3, T - 1, y + 3, C["4"] if i >= 2 else C["5"])
        if i in (0, 2):
            s.px(12, y + 1, C["W"]); s.px(13, y + 1, C["L"])
    s.px(5, 6, C["4"]); s.px(10, 14, C["4"])
    return s


def shop_counter():
    """상점: 흰 천 좌판(G07, 테 G06, 다리 G04) 에 똑같은 병 셋(G09, 마개 K) 과 똑같은 상자 셋(G05) — 줄 맞춰."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["7"])
    s.line(0, 0, T - 1, 0, C["9"]); s.line(0, 15, T - 1, 15, C["4"]); s.line(0, 14, T - 1, 14, C["6"])
    for x in (2, 7, 12):
        s.rect(x, 3, x + 1, 6, C["9"]); s.px(x, 2, C["K"]); s.px(x + 1, 2, C["K"]); s.px(x + 1, 6, C["6"])
        s.rect(x, 9, x + 2, 12, C["5"]); s.line(x, 9, x + 2, 9, C["6"]); s.px(x + 2, 12, C["4"])
    return s


# ============================================================ 소품 (투명 배경)
def prop_bench():
    """빈 벤치(solid): 흰 돌 벤치 — 앉는 면 G07(테 L), 앞면 G06, 다리 G05, 그림자 G03. 아무도 앉지 않는다."""
    s = new()
    s.rect(2, 6, 13, 8, C["7"]); s.line(2, 6, 13, 6, C["L"])
    s.rect(2, 9, 13, 10, C["6"])
    s.rect(3, 11, 4, 13, C["5"]); s.rect(11, 11, 12, 13, C["5"])
    s.line(3, 14, 12, 14, C["3"])
    s.outline(C["K"], where="inside")
    s.line(3, 6, 12, 6, C["L"]); s.line(3, 14, 12, 14, C["3"])
    return s


def prop_dead_lamp():
    """꺼진 가로등(solid): 흰 돌 기둥(G06/G05) 위 쇠 등갓(G04), 유리는 어둡다(K, 반사 S 1px). 5층 가로등과 같은 자리, 불만 없다."""
    s = new()
    s.line(7, 6, 7, 13, C["6"]); s.line(8, 6, 8, 13, C["5"])
    s.rect(5, 14, 10, 14, C["6"]); s.rect(4, 15, 11, 15, C["4"])
    s.rect(4, 1, 11, 1, C["4"]); s.px(7, 0, C["4"]); s.px(8, 0, C["4"])
    s.rect(5, 2, 10, 5, C["K"]); s.px(6, 3, C["S"])
    s.line(5, 2, 5, 5, C["4"]); s.line(10, 2, 10, 5, C["4"])
    s.rect(6, 6, 9, 6, C["4"])
    s.outline(C["K"], where="inside")
    s.rect(5, 14, 10, 14, C["6"], only=C["K"]); s.px(6, 3, C["S"])
    return s


def prop_flower_pot():
    """똑같은 화분(solid): 흰 화분(G07, 테 L, 아래 G06) 에 마른 관목(G03/G02, 빛 G04 2px). 모든 화분이 같다."""
    s = new()
    for x0, x1, y in [(6, 9, 3), (5, 10, 4), (4, 11, 5), (4, 11, 6), (5, 10, 7), (6, 9, 8)]:
        s.line(x0, y, x1, y, C["3"])
    for x, y in [(7, 5), (8, 6), (6, 6), (9, 4)]:
        s.px(x, y, C["2"])
    s.px(6, 4, C["4"]); s.px(5, 5, C["4"])
    s.rect(4, 9, 11, 9, C["L"])
    s.rect(4, 10, 11, 13, C["7"]); s.line(5, 13, 10, 13, C["6"]); s.px(4, 13, C["6"]); s.px(11, 13, C["6"])
    s.line(5, 14, 10, 14, C["3"])
    s.outline(C["K"], where="inside")
    s.line(5, 9, 10, 9, C["L"]); s.line(5, 14, 10, 14, C["3"])
    return s


def prop_floor_crack():
    """바닥의 작은 균열 하나(통과): K 금 한 줄 + 빛 받는 가장자리 G03. 이 도시에서 유일하게 고르지 않은 것."""
    s = new()
    pts = [(3, 12), (5, 10), (6, 9), (8, 8), (9, 6), (11, 5), (12, 3)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        s.line(ax, ay, bx, by, C["K"])
    for x, y in [(4, 10), (7, 8), (10, 5), (12, 2)]:
        s.px(x, y, C["3"])
    s.px(6, 10, C["1"]); s.px(9, 7, C["1"])
    return s


def prop_pedestal():
    """빈 좌대(solid): 흰 돌 좌대 — 윗면 G07, 몸 G06, 받침 G07, 새긴 글줄 G04 둘, 윗면 모서리 W 1px. 동상은 없다."""
    s = new()
    s.rect(4, 3, 11, 5, C["7"]); s.px(4, 3, C["W"])
    s.rect(5, 6, 10, 11, C["6"])
    s.line(6, 8, 9, 8, C["4"]); s.line(6, 10, 8, 10, C["4"])
    s.rect(3, 12, 12, 13, C["7"]); s.line(3, 13, 12, 13, C["6"])
    s.line(4, 14, 12, 14, C["3"])
    s.outline(C["K"], where="inside")
    s.line(5, 3, 10, 3, C["7"]); s.px(4, 3, C["W"]); s.line(4, 14, 12, 14, C["3"])
    return s


def prop_swept_ash():
    """쓸어 모은 재(통과): 가지런한 재 더미(G03, 윗줄 G04) 와 옆의 비질 자국(G01) — 잔불은 없다. W 1px."""
    s = new()
    for x0, x1, y in [(7, 8, 8), (6, 9, 9), (5, 10, 10), (4, 11, 11), (3, 12, 12)]:
        s.line(x0, y, x1, y, C["3"])
    s.px(7, 8, C["4"]); s.px(6, 9, C["4"])
    s.px(9, 10, C["2"]); s.px(5, 11, C["2"]); s.px(10, 12, C["2"])
    s.px(8, 10, C["W"])
    s.line(2, 13, 13, 13, C["1"])
    s.line(12, 6, 14, 6, C["1"]); s.line(1, 7, 3, 7, C["1"])
    return s


def void_tile():
    return new()


TILES = [
    ("floor_0", floor_0()), ("floor_1", floor_1()), ("floor_2", floor_2()), ("floor_3", floor_3()),
    ("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
    ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
    ("exit", exit_stairs()), ("shop", shop_counter()),
    ("prop_bench", prop_bench()), ("prop_dead_lamp", prop_dead_lamp()),
    ("prop_flower_pot", prop_flower_pot()), ("prop_floor_crack", prop_floor_crack()),
    ("prop_pedestal", prop_pedestal()), ("prop_swept_ash", prop_swept_ash()),
    ("wall_v1", wall_v1()), ("wall_v2", wall_v2()),
    ("start_0", floor_start(0)), ("start_1", floor_start(1)),
    ("trial_0", floor_trial(0)), ("trial_1", floor_trial(1)),
    ("rest_0", floor_rest(0)), ("rest_1", floor_rest(1)),
    ("boss_0", floor_boss(0)), ("boss_1", floor_boss(1)),
]
PROPS = [("empty_bench", True), ("dead_lamp", True), ("flower_pot", True), ("floor_crack", False),
         ("empty_pedestal", True), ("swept_ash", False)]

if __name__ == "__main__":
    tc.run(8, "평상 — 황제의 수도", TILES, PROPS, [19, 21, 23, 25], HERE)
