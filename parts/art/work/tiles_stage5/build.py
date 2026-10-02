#!/usr/bin/env python3
"""LOPAD 5층 '귀(耳)' 첩보 제국 타일셋 (16x16, 8열×4행) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage5/build.py
입력: parts/art/palette/lopad.json (무채 16 + 5층 보라 램프), assets/sprites/player/player_idle.png
산출: assets/tiles/stage5.png / stage5.json (37라운드 인덱스 표, tiles_floors/tilecommon2.py 참조)
      parts/art/work/tiles_stage5/preview.png · preview_room.png · preview_seam.png

컨셉 (story text-pack B5·D5, world-bible 5층 / 37라운드 검수 "버려진 구역의 흙바닥, 삭막하고 처절하게"):
  집집마다 창문이 하나씩 열려 있다. 안에서 밖을 본다. 거리는 비에 젖은 검은 흙 — 밟힌 밀고장, 웅덩이에 비친 보랏빛.
  바닥 = 젖은 검은 흙(G01 기조, 흙덩이 G02, 패인 곳 G00, 젖은 번들거림 G03, 웅덩이에 보라 반사)
  벽   = 창문 하나 열린 석벽(안쪽 눈 1px 보라) / 변형 19 = 밀고장 붙은 벽(덧문 닫힘) / 변형 20 = 홈통·물 자국 + 긁힌 耳 표식
  문   = 엿보는 구멍 있는 널문 (닫힘: 구멍 속 눈 / 잠김: 구멍 닫힘 + 사슬)
  소품 = 밀고장 더미(통과) · 기둥 뒤 엿보는 그림자(통과, 보라 눈) · 봉인된 상자(solid) · 가로등(solid, 보라 불, 바닥에 빛 웅덩이)
         · 엎어진 잉크병(통과, 보라 잉크) · 밀고 게시판(solid)
  방 바닥 = 시작: 발자국 / 시련: 깨진 등불 유리·끌린 자국 / 휴식: 재와 잔불 / 보스: 더 검은 흙에 눈들
색 예산: 무채 10 (G00~G07, G09, G12) + 강조 4 (19 shadow1, 21 base, 23 light1, 25 glow). 샘플 방 강조 5% 이하.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon2 as tc  # noqa: E402

G = tc.G
A = tc.ramp(5)
T = tc.T

C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
    "S": A[3],   # 19 shadow1 — 등불 빛 웅덩이·잉크 그늘·봉인 그늘
    "B": A[5],   # 21 base   — 밀랍 봉인·등불 유리·잉크
    "L": A[7],   # 23 light1 — 눈(1px)·웅덩이 반사·계단 빛
    "W": A[9],   # 25 glow   — 등불 심지·잔불
}
ctx = tc.Ctx(C)
new, blit = ctx.new, ctx.blit


# ============================================================ 바닥 (젖은 검은 흙)
def dirt(seed, base="1", clods=18, pits=7, glints=4, clod="2", pit="K", glint="3"):
    """버려진 거리의 젖은 흙. 격자 없음 — 흙덩이는 짧은 랜덤워크 덩어리(1~4px)로, 패인 곳·번들거림은 점으로.
    고르게 흩뿌리지 않고 뭉치는 데는 뭉치고 비는 데는 비게('잔불 오르듯'). 같은 seed 면 같은 그림."""
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
    return s


def puddle(s, pts, refl):
    """웅덩이: G02 물, 가장자리 한쪽 G00, 반사 L (1~2px). pts = (x0,x1,y) 가로 줄 목록."""
    for x0, x1, y in pts:
        s.line(x0, y, x1, y, C["2"])
    x0, x1, y = pts[-1]
    s.line(x0 + 1, y + 1, x1 - 1, y + 1, C["K"])
    for x, y in refl:
        s.px(x, y, C["L"])


def scrap(s, x, y, ch="6"):
    """밟힌 밀고장 조각 3x3: 종이 G06, 접힌 귀 G04, 글줄 G03 1px."""
    s.rect(x, y, x + 2, y + 2, C[ch])
    s.px(x + 2, y + 2, C["4"]); s.px(x + 1, y + 1, C["3"])


def floor_0():
    return dirt(501)


def floor_1():
    s = dirt(502, clods=14)
    puddle(s, [(5, 8, 8), (3, 10, 9), (2, 11, 10), (4, 9, 11), (6, 7, 12)], refl=[(6, 10), (7, 10)])
    return s


def floor_2():
    s = dirt(503, clods=16)
    scrap(s, 9, 3)
    s.px(10, 7, C["3"])
    return s


def floor_3():
    s = dirt(504, clods=15, pits=9)
    puddle(s, [(11, 13, 3), (9, 14, 4), (8, 14, 5), (10, 12, 6)], refl=[(12, 4), (13, 5)])
    scrap(s, 2, 11)
    return s


# ---- 방 종류별
def floor_start(i):
    """시작 방: 밀고자들이 다녀간 발자국 (G00 2x3 쌍) + 떨어진 밀고장."""
    s = dirt(511 + i, clods=14, pits=4)
    feet = [((3, 3), (6, 5)), ((9, 8), (12, 10))] if i == 0 else [((5, 10), (8, 12))]
    for (ax, ay), (bx, by) in feet:
        s.rect(ax, ay, ax + 1, ay + 2, C["K"]); s.px(ax, ay + 3, C["K"])
        s.rect(bx, by, bx + 1, by + 2, C["K"]); s.px(bx, by + 3, C["K"])
    if i == 1:
        scrap(s, 11, 2, ch="7")
    return s


def floor_trial(i):
    """시련 방: 깨진 등불 유리(G05 조각 + 보라 반사 L) 와 끌린 자국(G00 긴 줄)."""
    s = dirt(521 + i, clods=12, pits=6)
    if i == 0:
        s.line(3, 12, 6, 11, C["K"]); s.px(4, 13, C["2"])
        for x, y in [(11, 3), (13, 6)]:
            s.px(x, y, C["5"]); s.px(x + 1, y, C["L"])
    else:
        s.line(9, 5, 11, 7, C["K"]); s.px(12, 8, C["2"])
        for x, y in [(2, 9), (13, 3)]:
            s.px(x, y, C["5"]); s.px(x + 1, y + 1, C["L"]); s.px(x + 1, y, C["4"])
        s.px(13, 2, C["L"])
    return s


def floor_rest(i):
    """휴식 방: 꺼져 가는 모닥불 자리 — 재(G03/G02) 와 잔불(W/L) 2~3px."""
    s = dirt(531 + i, clods=12, pits=5, glints=2)
    if i == 0:
        for x0, x1, y in [(9, 11, 3), (8, 12, 4), (9, 13, 5), (10, 12, 6)]:
            s.line(x0, y, x1, y, C["3"])
        for x, y in [(10, 4), (12, 5), (9, 5)]:
            s.px(x, y, C["2"])
        s.px(11, 4, C["W"]); s.px(11, 5, C["L"]); s.px(3, 11, C["L"])
    else:
        for x, y in [(2, 12), (3, 12), (12, 2), (6, 7)]:
            s.px(x, y, C["3"])
        s.px(4, 11, C["L"]); s.px(13, 3, C["W"])
    return s


def floor_boss(i):
    """보스 방: 더 검은 흙(G00 기조, 덩어리 G01) — 바닥 어둠 속에서 눈(L) 셋이 본다."""
    s = dirt(541 + i, base="K", clod="1", pit="1", glint="2", clods=20, pits=0, glints=5)
    eyes = [(3, 5), (11, 12)] if i == 0 else [(12, 3)]
    for x, y in eyes:
        s.px(x, y, C["L"]); s.px(x - 1, y, C["1"]); s.px(x + 1, y, C["1"])
    return s


# ============================================================ 복도 (골목: 더 어둡고 가운데 도랑)
def corridor_tile():
    s = dirt(505, base="K", clod="1", pit="1", glint="2", clods=16, pits=0, glints=3)
    s.line(7, 0, 7, T - 1, C["1"]); s.line(8, 0, 8, T - 1, C["2"])   # 빗물 도랑
    s.px(8, 5, C["3"]); s.px(8, 12, C["L"])
    return s


# ============================================================ 벽
def stone_courses(s):
    """1층과 같은 석벽: 벽돌 4단, 회반죽 K, 윗변 G02."""
    s.rect(0, 0, T - 1, T - 1, C["1"])
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["2"])
        off = 0 if i % 2 == 0 else 4
        for x in (off, off + 8):
            s.line(x, y, x, y + 3, C["K"])


def window(s, x0=5, y0=3, open_=True):
    """창 7x7: 틀 G03, 안 K. open_: 덧문이 왼쪽으로 젖혀져 있고 안에서 눈(L) 이 본다. 닫힘: 덧문 두 짝이 창을 막는다."""
    s.rect(x0, y0, x0 + 6, y0 + 6, C["3"])
    if open_:
        s.rect(x0 + 1, y0 + 1, x0 + 5, y0 + 5, C["K"])
        s.line(x0 + 1, y0 + 1, x0 + 5, y0 + 1, C["1"])
        s.rect(x0 - 2, y0, x0 - 1, y0 + 6, C["4"]); s.line(x0 - 2, y0, x0 - 2, y0 + 6, C["5"])
        s.px(x0 - 1, y0 + 1, C["6"]); s.px(x0 - 1, y0 + 5, C["6"])
        s.px(x0 + 4, y0 + 3, C["L"])
    else:
        s.rect(x0 + 1, y0 + 1, x0 + 5, y0 + 5, C["4"])
        s.line(x0 + 3, y0 + 1, x0 + 3, y0 + 5, C["2"])
        s.px(x0 + 1, y0 + 1, C["5"]); s.px(x0 + 4, y0 + 1, C["5"])
    s.line(x0, y0 + 7, x0 + 6, y0 + 7, C["4"])  # 창턱


def wall_face():
    """창문이 하나 열린 석벽 (B5). 창 아래 빗물 자국 K 2줄."""
    s = new()
    stone_courses(s)
    window(s, 5, 3, open_=True)
    s.line(7, 11, 7, 13, C["K"]); s.line(10, 11, 10, 12, C["K"])
    for x, y in [(2, 1), (14, 13), (2, 13)]:
        s.px(x, y, C["3"])
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_v1():
    """벽 변형 1: 덧문 닫힌 창 + 벽에 붙은 밀고장 석 장(G07/G06, 글줄 G03, 한 장은 찢겨 반만)."""
    s = new()
    stone_courses(s)
    window(s, 8, 2, open_=False)
    # 밀고장 3장 (왼쪽 벽면)
    s.rect(1, 3, 4, 7, C["7"]); s.px(2, 4, C["3"]); s.px(3, 4, C["3"]); s.px(2, 6, C["3"])
    s.rect(2, 9, 5, 13, C["6"]); s.px(3, 10, C["3"]); s.px(4, 10, C["3"]); s.px(3, 12, C["3"])
    s.rect(10, 11, 13, 12, C["6"]); s.px(11, 13, C["6"]); s.px(12, 12, C["3"])   # 찢긴 반 장
    s.px(1, 3, C["4"]); s.px(4, 7, C["5"])      # 못·들린 귀
    s.px(5, 13, C["5"])
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_v2():
    """벽 변형 2: 홈통(G05 세로관) 과 그 아래 젖은 자국, 긁힌 제국 표식 耳 (G03, 5x7) — 보는 자의 표식."""
    s = new()
    stone_courses(s)
    s.line(12, 0, 12, 13, C["5"]); s.line(13, 0, 13, 13, C["4"])   # 홈통
    s.rect(11, 13, 14, 14, C["5"]); s.px(11, 14, C["4"])
    for y in (2, 7, 11):
        s.line(11, y, 14, y, C["6"])                                 # 관 이음쇠
    for x, y in [(10, 6), (10, 9), (15, 5), (15, 10), (10, 12)]:
        s.px(x, y, C["K"])                                           # 물 자국
    # 耳 표식 (x3..7, y4..10): 두 세로획 + 가로획 셋, 왼 아래 삐침
    s.line(3, 4, 3, 10, C["3"]); s.line(7, 4, 7, 9, C["3"])
    for y in (4, 6, 8):
        s.line(4, y, 6, y, C["3"])
    s.px(2, 11, C["3"]); s.px(4, 5, C["4"])
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_top():
    """벽 윗면: 석벽 덮개 (1층 구조). 젖어서 G03 점이 몇 개."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["1"])
    for y in (0, 8):
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["2"])
    s.line(6, 0, 6, 7, C["K"])
    s.line(11, 8, 11, 15, C["K"])
    for x, y in [(3, 4), (12, 3), (4, 12), (14, 11)]:
        s.px(x, y, C["3"])
    return s


# ============================================================ 문
def door_frame(s):
    """1층과 같은 문설주·상인방 틀 (G03/G04). 바탕 G01."""
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["3"]); s.line(0, 0, 0, T - 1, C["K"]); s.line(1, 0, 1, T - 1, C["4"])
    s.rect(13, 0, 15, T - 1, C["3"]); s.line(15, 0, 15, T - 1, C["K"]); s.line(13, 0, 13, T - 1, C["2"])
    s.rect(0, 0, T - 1, 1, C["3"]); s.line(0, 0, T - 1, 0, C["K"]); s.line(3, 1, 12, 1, C["4"])


def door_open():
    """열린 문: 틀 안으로 골목 흙이 이어진다(도랑 포함). 문짝은 왼쪽에 젖혀져 2px, 구멍 덮개만 보인다."""
    s = new()
    door_frame(s)
    cor = corridor_tile()
    for y in range(2, 16):
        for x in range(3, 13):
            s.px(x, y, cor.get(x, y)[:3])
    s.rect(3, 2, 4, 14, C["5"]); s.line(4, 2, 4, 14, C["4"])
    s.px(3, 7, C["K"]); s.px(4, 7, C["K"])
    s.px(3, 11, C["7"]); s.px(4, 11, C["6"])
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


def peephole(s, open_=True):
    """엿보는 구멍 (y7..8): 쇠 테 G06, 구멍 K. open_: 덮개가 왼쪽으로 밀려 있고 안에서 눈(L) 이 본다."""
    s.rect(5, 7, 10, 8, C["6"])
    if open_:
        s.rect(7, 7, 9, 8, C["K"])
        s.px(8, 7, C["L"])
    else:
        s.rect(6, 7, 9, 8, C["5"]); s.px(7, 8, C["4"])


def door_closed():
    s = new()
    door_frame(s)
    door_planks(s)
    peephole(s, open_=True)
    s.px(10, 11, C["7"]); s.px(10, 12, C["K"])
    return s


def door_locked():
    """잠긴 문(보스 방): 구멍이 닫혔다 — 아무도 보지 않는 문. 사슬 사선 + 자물쇠."""
    s = new()
    door_frame(s)
    door_planks(s)
    peephole(s, open_=False)
    for i, (x, y) in enumerate([(3, 14), (4, 13), (5, 12), (6, 11), (7, 10), (8, 9), (9, 8), (10, 7), (11, 6), (12, 5)]):
        s.px(x, y, C["7"] if i % 2 == 0 else C["6"])
    s.px(2, 14, C["7"]); s.px(13, 5, C["7"])
    s.rect(6, 11, 9, 14, C["7"]); s.line(6, 11, 9, 11, C["9"])
    s.px(6, 10, C["9"]); s.px(9, 10, C["9"])
    s.px(7, 12, C["K"]); s.px(8, 12, C["K"]); s.px(7, 13, C["K"])
    return s


# ============================================================ 출구 · 상점 (2x2)
def exit_stairs():
    """올라가는 돌계단 4단 (1·4층 구조). 위에서 비껴드는 보라 빛 — 밝은 칸 L/W 2px x2 (37라운드: 23~25 칸)."""
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
    return s


def shop_counter():
    """종군 상인 좌판: 널 탁자(G04) 위 밀고장 묶음(G12/G09) + 잉크병(K, 반사 B) + 봉인 편지(G09, 밀랍 B)."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["2"])
        s.line(0, y + 1, T - 1, y + 1, C["5"])
    s.line(0, 15, T - 1, 15, C["2"])
    s.rect(2, 4, 7, 10, C["9"]); s.line(2, 11, 8, 11, C["2"]); s.line(8, 4, 8, 11, C["2"])
    s.rect(3, 3, 8, 9, C["C"]); s.line(3, 10, 8, 10, C["3"]); s.line(8, 3, 8, 10, C["3"])
    for y in (5, 7):
        s.line(4, y, 7, y, C["7"])
    s.px(4, 9, C["7"]); s.px(5, 9, C["7"])
    s.rect(11, 3, 13, 6, C["K"]); s.line(11, 2, 13, 2, C["6"]); s.px(12, 1, C["5"])
    s.px(11, 4, C["B"])
    s.rect(10, 9, 14, 12, C["9"]); s.line(10, 13, 15, 13, C["2"]); s.line(15, 9, 15, 13, C["2"])
    s.px(12, 10, C["B"]); s.px(12, 11, C["B"]); s.px(13, 11, C["S"])
    return s


# ============================================================ 소품 (투명 배경)
def prop_report_pile():
    """밀고장 더미(통과): 종이 세 겹(G07→G09→G12) 비스듬히 쌓임, 맨 위에 밀랍 봉인 B 2x2, 흩어진 한 장."""
    s = new()
    s.rect(3, 8, 12, 13, C["7"])
    s.rect(4, 6, 11, 11, C["9"])
    s.rect(5, 4, 10, 9, C["C"])
    s.line(6, 6, 9, 6, C["9"]); s.line(6, 8, 8, 8, C["9"])
    s.px(9, 5, C["B"]); s.px(10, 5, C["B"]); s.px(9, 6, C["B"]); s.px(10, 6, C["S"])
    s.rect(11, 11, 14, 14, C["9"]); s.px(14, 14, C["7"]); s.px(12, 12, C["7"])
    s.line(3, 14, 12, 14, C["2"])
    s.outline(C["K"], where="inside")
    s.line(3, 14, 12, 14, C["2"])
    s.rect(5, 4, 10, 4, C["C"]); s.px(5, 5, C["C"])
    s.px(9, 5, C["B"]); s.px(10, 5, C["B"])
    return s


def prop_peeker():
    """기둥 뒤 엿보는 그림자(통과): 돌기둥(G05/G04/G03) 오른쪽에서 반쯤 내민 검은 형체(G01) + 보라 눈 1px."""
    s = new()
    s.rect(3, 2, 7, 13, C["4"])
    s.line(3, 2, 3, 13, C["5"]); s.line(4, 2, 4, 13, C["5"])
    s.line(7, 2, 7, 13, C["3"])
    s.rect(2, 1, 8, 1, C["6"]); s.rect(2, 14, 8, 14, C["3"]); s.rect(1, 15, 9, 15, C["2"])
    s.px(5, 6, C["3"]); s.px(5, 10, C["3"])
    s.rect(8, 4, 10, 6, C["1"])
    s.rect(8, 7, 11, 13, C["1"])
    s.px(11, 7, C["K"]); s.px(11, 13, C["K"])
    s.rect(9, 14, 12, 14, C["2"])
    s.px(9, 5, C["L"])
    s.outline(C["K"], where="inside")
    s.px(9, 5, C["L"])
    s.rect(2, 1, 8, 1, C["6"], only=C["K"]); s.line(3, 2, 3, 13, C["5"], only=C["K"])
    s.rect(9, 14, 12, 14, C["2"]); s.rect(1, 15, 9, 15, C["2"])
    return s


def prop_sealed_crate():
    """봉인된 상자(solid): 윗면 G05 / 앞면 G04 / 모서리 K, 쇠띠 G06 두 줄, 끈 K 십자 + 밀랍 봉인 B."""
    s = new()
    s.rect(2, 4, 13, 7, C["5"])
    s.rect(2, 8, 13, 13, C["4"])
    s.line(2, 8, 13, 8, C["3"])
    s.line(2, 4, 13, 4, C["6"])
    for x in (4, 11):
        s.line(x, 4, x, 13, C["6"]); s.px(x, 5, C["7"]); s.px(x, 9, C["7"])
    s.line(2, 10, 13, 10, C["K"])
    s.line(7, 4, 7, 13, C["K"])
    s.rect(7, 9, 8, 10, C["B"]); s.px(8, 10, C["S"])
    s.line(3, 14, 13, 14, C["2"])
    s.outline(C["K"], where="inside")
    s.line(3, 14, 13, 14, C["2"])
    s.line(3, 4, 12, 4, C["6"])
    return s


def prop_street_lamp():
    """가로등(solid, 보라 불): 쇠 기둥 G05/G04, 네모 등갓 G06, 유리 B, 속 L, 심지 W.
    37라운드 '강조색 더 강조': 기둥 발치의 흙에 보랏빛 웅덩이(S) 가 비친다. 1층·2층 등불과 실루엣 분리(각진 가스등)."""
    s = new()
    # 빛 웅덩이 (바닥, 기둥 뒤) — 투명 바탕 위 S 점 흩뿌림
    for x0, x1, y in [(5, 10, 12), (3, 12, 13), (2, 13, 14), (1, 14, 15)]:
        s.line(x0, y, x1, y, C["S"])
    s.line(7, 6, 7, 13, C["5"]); s.line(8, 6, 8, 13, C["4"])
    s.rect(5, 14, 10, 14, C["5"]); s.rect(4, 15, 11, 15, C["3"])
    s.rect(4, 1, 11, 1, C["6"]); s.px(7, 0, C["6"]); s.px(8, 0, C["6"])
    s.rect(5, 2, 10, 5, C["B"])
    s.rect(6, 3, 9, 4, C["L"]); s.px(7, 4, C["W"]); s.px(8, 4, C["W"]); s.px(7, 3, C["W"])
    s.line(5, 2, 5, 5, C["6"]); s.line(10, 2, 10, 5, C["6"])
    s.rect(6, 6, 9, 6, C["6"])
    s.outline(C["K"], where="inside")
    s.rect(6, 3, 9, 4, C["L"]); s.px(7, 4, C["W"]); s.px(8, 4, C["W"]); s.px(7, 3, C["W"])
    s.px(6, 2, C["B"]); s.px(9, 2, C["B"]); s.px(6, 5, C["B"]); s.px(9, 5, C["B"])
    for x0, x1, y in [(5, 10, 12), (3, 12, 13), (2, 13, 14), (1, 14, 15)]:
        s.line(x0, y, x1, y, C["S"], only=C["K"])
    s.rect(5, 14, 10, 14, C["5"]); s.rect(4, 15, 11, 15, C["3"]); s.line(7, 12, 7, 13, C["5"]); s.line(8, 12, 8, 13, C["4"])
    s.px(4, 14, C["K"]); s.px(11, 14, C["K"]); s.px(3, 15, C["K"]); s.px(12, 15, C["K"])
    return s


def prop_ink_spill():
    """엎어진 잉크병(통과): 옆으로 쓰러진 병(K 몸통, G06 목·마개) 에서 흘러나온 보라 잉크(B, 가장자리 S).
    밀고장을 쓰던 잉크 — 보라는 이 층의 '말' 이다."""
    s = new()
    # 잉크 웅덩이 (오른쪽 아래로 흐름)
    for x0, x1, y in [(7, 10, 8), (6, 12, 9), (7, 13, 10), (9, 12, 11), (11, 12, 12)]:
        s.line(x0, y, x1, y, C["B"])
    for x, y in [(6, 9), (7, 10), (12, 11), (11, 12), (12, 12), (13, 10)]:
        s.px(x, y, C["S"])
    s.px(9, 9, C["L"])  # 잉크 표면 반사
    # 병 (x2..7, y5..8) 옆으로 누움, 목이 오른쪽
    s.rect(2, 5, 6, 8, C["K"]); s.line(2, 5, 6, 5, C["2"]); s.px(2, 6, C["2"])
    s.rect(7, 6, 8, 7, C["6"]); s.px(8, 6, C["7"])
    s.line(3, 9, 6, 9, C["2"])
    return s


def prop_notice_board():
    """밀고 게시판(solid): 말뚝 둘에 걸린 널판(G04/G03), 핀으로 꽂힌 밀고장 넉 장(G07/G09), 한 장에 밀랍 봉인 B.
    D5 '밀고장이 쌓여 있다. 절반은 서로를 고발한다.'"""
    s = new()
    s.rect(1, 2, 14, 11, C["4"]); s.line(1, 2, 14, 2, C["5"]); s.line(1, 11, 14, 11, C["3"])
    s.line(7, 3, 7, 10, C["3"])                   # 널 이음
    s.line(2, 12, 2, 14, C["3"]); s.line(13, 12, 13, 14, C["3"]); s.px(2, 15, C["2"]); s.px(13, 15, C["2"])  # 말뚝
    s.rect(2, 3, 6, 5, C["9"]); s.px(3, 4, C["3"]); s.px(4, 4, C["3"]); s.px(5, 4, C["3"])      # 가로 넓은 장
    s.rect(9, 3, 11, 8, C["7"]); s.px(10, 4, C["3"]); s.px(10, 6, C["3"]); s.px(10, 7, C["3"])    # 세로 긴 장
    s.rect(3, 7, 5, 10, C["7"]); s.px(4, 8, C["3"]); s.px(4, 9, C["B"]); s.px(5, 9, C["B"])       # 봉인 붙은 장
    s.rect(12, 5, 13, 9, C["9"]); s.px(13, 10, C["9"]); s.px(12, 7, C["3"])                       # 찢겨 늘어진 쪽지
    s.px(8, 9, C["6"]); s.px(8, 10, C["6"])                                                       # 떼어 낸 자리의 핀 자국
    for x, y in [(2, 3), (10, 3), (3, 7), (12, 5)]:
        s.px(x, y, C["6"])                        # 핀
    s.outline(C["K"], where="inside")
    s.line(2, 2, 13, 2, C["5"])
    s.px(2, 15, C["2"]); s.px(13, 15, C["2"])
    return s


def void_tile():
    return new()


TILES = [
    ("floor_0", floor_0()), ("floor_1", floor_1()), ("floor_2", floor_2()), ("floor_3", floor_3()),
    ("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
    ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
    ("exit", exit_stairs()), ("shop", shop_counter()),
    ("prop_report_pile", prop_report_pile()), ("prop_peeker", prop_peeker()),
    ("prop_sealed_crate", prop_sealed_crate()), ("prop_street_lamp", prop_street_lamp()),
    ("prop_ink_spill", prop_ink_spill()), ("prop_notice_board", prop_notice_board()),
    ("wall_v1", wall_v1()), ("wall_v2", wall_v2()),
    ("start_0", floor_start(0)), ("start_1", floor_start(1)),
    ("trial_0", floor_trial(0)), ("trial_1", floor_trial(1)),
    ("rest_0", floor_rest(0)), ("rest_1", floor_rest(1)),
    ("boss_0", floor_boss(0)), ("boss_1", floor_boss(1)),
]
PROPS = [("report_pile", False), ("peeking_shadow", False), ("sealed_crate", True), ("street_lamp", True),
         ("ink_spill", False), ("notice_board", True)]

if __name__ == "__main__":
    tc.run(5, "귀(耳) — 첩보 제국 외곽", TILES, PROPS, [19, 21, 23, 25], HERE)
