#!/usr/bin/env python3
"""hall — 지배자의 연회장 (보스 '취하지 않는 자' 의 노천 연회 테라스). 거리를 다 지나 마지막에 닿는, 밤하늘 아래 열린 연회장.

바닥 = 마름모 줄눈의 대리석(면 3 · 줄 2) — 거리보다 한 단 밝은 '부자의 바닥'. 흘린 포도주는 넷 중 하나, 작게.
보스 방 바닥(boss) = 바닥 전체에 깐 **연회 깔개**(포도주빛 d · 무늬 i · 금실 e). 뒤집힌 잔·흘린 술은 소품.
경계 = **돌 난간**(난간동자 사이로 밤의 어둠이 보인다 — 실내가 아니다) · 횃불 걸린 기둥 · 잔 문양 휘장, 윗면 = 난간 위 대리석 판.
void = 테라스 아래 멀리 깔린 밤의 도시 지붕들(어두운 갈색 기와 결 + 드문 창 불빛).
"""
import rkit as K
import stage1 as v4
from rkit import C, T, blit, blob, new

NAME = "잔(盞) — 지배자의 연회장"
FACE, LINE = "3", "2"


# ------------------------------------------------------------ 대리석 · 깔개
def lattice(face=FACE, line_c=LINE, dot=None):
    """마름모 줄눈: 꼭짓점이 타일 변의 가운데(8,0)(15,8)(8,15)(0,8) → 이어 붙이면 45° 마름모 격자. dot = 마름모 가운데(=타일 모서리) 장식."""
    s = K.fill(face)
    for k in range(8):
        s.px(8 + k, k, C[line_c]); s.px(7 - k, k, C[line_c])
        s.px(8 + k, 15 - k, C[line_c]); s.px(7 - k, 15 - k, C[line_c])
    if dot:
        for x, y in ((0, 0), (15, 0), (0, 15), (15, 15)):
            s.px(x, y, C[dot])
    return s


def wine(s, cx, cy, r, seed):
    """흘린 포도주: d 덩어리 + 가장자리 i, 반사 e 1px."""
    blob(s, cx, cy, r, "d", seed=seed, squash=0.6, core=None)
    s.px(int(cx) - 1, int(cy) - 1, C["e"])
    return s


def common_floor(i):
    s = lattice()
    if i == 1:
        K.line(s, [(4, 9), (6, 10), (7, 12)], LINE)                               # 실금
    return s


def start_floor(i):
    return common_floor(i)


def trial_floor(i):
    """2회차: 포도주 얼룩을 변형 하나에 넣었더니 25% 섞기에서 갈색 점이 화면 가득 → 얼룩은 소품(wine_spill·toppled_goblet)으로만."""
    s = lattice()
    if i == 2:
        K.line(s, [(10, 3), (11, 5), (13, 6)], LINE)
    return s


def rest_floor(i):
    return lattice()


CARPET_FIELD, CARPET_LINE, CARPET_GOLD = "d", "i", "e"


def carpet(i):
    """연회 깔개(보스 방 전체): 포도주빛 바탕 d · 마름모 무늬 i · 마름모 가운데 금실 e 2x2. 넷 중 하나 포도주 얼룩, 하나 닳은 자리."""
    s = lattice(CARPET_FIELD, CARPET_LINE)
    s.px(8, 8, C[CARPET_GOLD]); s.px(7, 7, C[CARPET_GOLD])                       # 마름모 가운데 금실 2px (모서리 점은 뺐다: 점 격자)
    if i == 1:
        blob(s, 11, 4, 1.8, "i", seed=9, squash=0.7)                               # 흘린 포도주
    elif i == 2:
        s.px(4, 11, C["e"]); s.px(5, 12, C["e"])                                    # 닳은 올
    return s


def boss_floor(i):
    return carpet(i)


def corridor_tile():
    return lattice("2", "1")


# ------------------------------------------------------------ 난간 (북 경계)
NIGHT = "K"


def balustrade(gap=NIGHT):
    """돌 난간: 위 손잡이 6/5/3 · 난간동자 4개(꽃병 모양, 빛 6 · 몸 5 · 그늘 3) · 사이 = 밤(K) · 아래 받침 5/4 · 땅 그늘 K."""
    s = K.fill(gap)
    s.line(0, 0, T - 1, 0, C["6"]); s.line(0, 1, T - 1, 1, C["5"]); s.line(0, 2, T - 1, 2, C["3"])
    BAL = [".565.", ".55..", "..5..", ".565.", "65553", "65553", ".555.", "..5..", ".565.", "6555."]
    for bx in (0, 4, 8, 12):
        for j, row in enumerate(BAL):
            for i, ch in enumerate(row):
                if ch != ".":
                    x = (bx - 1 + i) % T
                    c = ch
                    if ch == "5" and i >= 3:
                        c = "3"
                    s.px(x, 3 + j, C[c])
    s.line(0, 13, T - 1, 13, C["5"]); s.line(0, 14, T - 1, 14, C["4"]); s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_face():
    return balustrade()


def wall_v1():
    """난간 기둥 + 횃불 걸이: 기둥 4~11(빛 6 · 그늘 3), 쇠 걸이 5, 불꽃 L/W/B."""
    s = balustrade()
    s.rect(4, 0, 11, 14, C["5"]); s.line(4, 0, 4, 14, C["6"]); s.line(11, 0, 11, 14, C["3"])
    s.line(4, 0, 11, 0, C["6"]); s.line(5, 2, 10, 2, C["4"]); s.line(5, 12, 10, 12, C["4"])
    s.rect(6, 7, 9, 8, C["4"]); s.line(6, 9, 9, 9, C["3"])
    blit(s, ["..L.", ".LWL", ".BWB", "..S."], 6, 3)
    return s


def wall_v2():
    """잔 문양 휘장이 난간에 걸침: 천 d(빛 e · 그늘 i) + 잔 문양 S, 아래 술 장식 e."""
    s = balustrade()
    s.rect(3, 0, 12, 12, C["d"])
    s.line(3, 0, 3, 12, C["e"]); s.line(12, 0, 12, 12, C["i"])
    s.line(3, 0, 12, 0, C["5"])
    blit(s, ["SSSS", ".SS.", "..S.", ".SS."], 6, 3)
    s.px(6, 3, C["S"]); s.px(9, 3, C["S"])
    for x in (4, 7, 10):
        s.px(x, 13, C["e"]); s.px(x, 14, C["d"])
    return s


def wall_top():
    """난간 윗면(위에서): 1회차 — 대리석 판으로 채웠더니 회색 테가 '깔개 깐 방' 의 벽으로 읽혔다.
    → 밤(K) 바탕에 **십자 난간대**(가로·세로 4px, 빛 6 · 면 5 · 그늘 3) + 가운데 기둥머리. 가로로 이으면 가로 난간,
    세로로 이으면 세로 난간이 되고, 사이로 밤이 보여 테라스가 트여 있다."""
    s = K.fill(NIGHT)
    s.rect(0, 6, T - 1, 9, C["5"]); s.line(0, 6, T - 1, 6, C["6"]); s.line(0, 9, T - 1, 9, C["3"])
    s.rect(6, 0, 9, T - 1, C["5"]); s.line(6, 0, 6, T - 1, C["6"]); s.line(9, 0, 9, T - 1, C["3"])
    s.rect(5, 5, 10, 10, C["6"]); s.line(5, 10, 10, 10, C["4"]); s.line(10, 5, 10, 10, C["4"]); s.rect(7, 7, 8, 8, C["5"])
    return s


def void_tile():
    """원경: 테라스 아래 밤의 도시 — 어두운 갈색 기와 지붕 결(i/K) + 창 불빛 S 한 점(가로 결 위라 격자로 줄서지 않게 한 장에 하나)."""
    s = K.fill("K")
    for r in range(4):
        y = r * 4
        s.line(0, y, T - 1, y, C["i"])
        off = (r % 2) * 4
        for x in range(off, T, 8):
            s.px(x, y + 1, C["i"]); s.px(x, y + 2, C["i"])
    s.px(11, 10, C["S"])
    return s


# ------------------------------------------------------------ 문 (큰 두짝 문)
def door_frame(s):
    s.rect(0, 0, 2, T - 1, C["5"]); s.line(0, 0, 0, T - 1, C["6"]); s.line(2, 0, 2, T - 1, C["3"])
    s.rect(13, 0, 15, T - 1, C["5"]); s.line(13, 0, 13, T - 1, C["6"]); s.line(15, 0, 15, T - 1, C["3"])
    s.rect(0, 0, T - 1, 1, C["5"]); s.line(0, 0, T - 1, 0, C["6"]); s.line(3, 1, 12, 1, C["K"])


def leaves(s):
    s.rect(3, 2, 12, 15, C["d"])
    s.line(7, 2, 7, 15, C["i"]); s.line(8, 2, 8, 15, C["i"])
    for x0 in (3, 9):
        s.rect(x0 + 1, 4, x0 + 2, 7, C["i"]); s.rect(x0 + 1, 10, x0 + 2, 13, C["i"])
    s.line(3, 2, 12, 2, C["e"])
    s.px(6, 9, C["e"]); s.px(9, 9, C["e"])


def door_open():
    s = lattice("2", "1")
    door_frame(s)
    s.rect(3, 2, 4, 15, C["d"]); s.line(4, 2, 4, 15, C["e"])
    s.rect(11, 2, 12, 15, C["d"]); s.line(11, 2, 11, 15, C["i"])
    s.line(7, 4, 7, 13, C["S"]); s.px(7, 8, C["B"])
    return s


def door_closed():
    s = new()
    door_frame(s)
    leaves(s)
    return s


def door_locked():
    s = door_closed()
    s.rect(2, 8, 13, 9, C["6"]); s.line(2, 9, 13, 9, C["4"])
    s.rect(6, 10, 9, 12, C["7"]); s.line(6, 10, 9, 10, C["9"]); s.px(7, 11, C["K"])
    return s


# ------------------------------------------------------------ 출구 · 상점
def exit_tile():
    """출구 = 더 안쪽으로 이어지는 붉은 길 깔개: 깔개보다 한 단 밝은 e 바탕 · 무늬 d · 금실 f(가운데). 2x2 반복."""
    s = lattice("e", "d")
    s.px(8, 8, C["f"]); s.px(7, 7, C["f"])
    return s


def shop_tile():
    """연회 식탁 위: 흰 식탁보(C/T) · 접시(7) 위 고기(e/d) · 잔(6, 포도주 d). 2x2 반복."""
    s = K.fill("T")
    s.line(0, 0, T - 1, 0, C["C"]); s.line(0, 15, T - 1, 15, C["7"])
    s.line(0, 7, T - 1, 7, C["E"])
    s.rect(2, 2, 7, 5, C["7"]); s.rect(3, 2, 6, 4, C["e"]); s.line(3, 2, 6, 2, C["f"]); s.px(6, 4, C["d"])
    s.rect(10, 9, 12, 13, C["6"]); s.line(10, 9, 12, 9, C["d"]); s.px(10, 10, C["7"]); s.line(11, 13, 11, 14, C["5"])
    s.px(3, 11, C["d"]); s.px(4, 11, C["d"]); s.px(4, 12, C["d"])
    return s


# ------------------------------------------------------------ 소품 8
def prop_goblet():
    """옆으로 뒤집힌 은잔 + 쏟아진 포도주. 잔 = 오른쪽으로 벌어진 잔몸(9/7, 입 K) · 가는 목(7) · 왼쪽 받침(7 세로).
    (1회차: 네모 몸 + 짧은 목이 장화로 읽혔다 → 잔몸을 나팔꼴로, 받침을 원판 세로선으로)"""
    s = new()
    blob(s, 10, 11, 3.8, "d", seed=4, squash=0.5, lo=0, hi=15)
    s.px(9, 10, C["e"])
    blit(s, ["7.......",
             "7...9999",
             "7777999T",
             "7...977T",
             "7....777"], 2, 5)
    s.line(13, 6, 13, 9, C["K"])                                                  # 잔 입(안쪽 어둠)
    s.px(12, 7, C["d"]); s.px(12, 8, C["d"])
    s.outline(C["K"], where="inside")
    s.line(13, 6, 13, 9, C["d"])
    return s


def prop_wine_spill():
    s = new()
    blob(s, 8, 9, 5.4, "d", seed=14, squash=0.5, lo=0, hi=15)
    blob(s, 7, 9, 2.6, "i", seed=15, squash=0.5)
    s.px(5, 8, C["e"]); s.px(6, 8, C["e"]); s.px(13, 12, C["d"]); s.px(2, 7, C["d"])
    return s


def prop_candelabra():
    """촛대(세움): 받침 5 · 기둥 6/4 · 가지 셋 · 초 C · 불꽃 L/W."""
    s = new()
    s.rect(5, 13, 10, 14, C["5"]); s.line(5, 13, 10, 13, C["6"])
    s.line(7, 6, 7, 12, C["6"]); s.line(8, 6, 8, 12, C["4"])
    s.line(3, 6, 12, 6, C["5"]); s.px(3, 5, C["5"]); s.px(12, 5, C["5"]); s.px(7, 5, C["6"]); s.px(8, 5, C["5"])
    for x in (3, 8, 12):
        s.px(x, 4, C["C"]); s.px(x, 3, C["C"])
    s.outline(C["K"], where="inside")
    for x in (3, 8, 12):
        s.px(x, 2, C["W"]); s.px(x, 1, C["L"])
    s.px(7, 15, C["1"]); s.px(8, 15, C["1"])
    return s


def prop_platter():
    """먹다 남은 쟁반(바닥): 접시 테 7/6 · 뼈 D · 포도 i/d."""
    s = new()
    for y in range(5, 14):
        for x in range(1, 15):
            d = ((x - 7.5) / 6.5) ** 2 + ((y - 9.5) / 4.0) ** 2
            if d <= 1:
                s.px(x, y, C["7"] if d > 0.6 else C["6"])
    s.line(4, 9, 9, 8, C["D"]); s.px(3, 9, C["C"]); s.px(10, 8, C["C"]); s.px(4, 10, C["9"])
    for x, y in ((9, 10), (10, 11), (11, 10), (10, 9)):
        s.px(x, y, C["i"])
    s.px(10, 10, C["d"])
    s.outline(C["K"], where="inside")
    s.line(3, 14, 12, 14, C["1"])
    return s


def prop_chair():
    """쓰러진 의자: 등받이 d/e · 다리 i · 앉는 판 e."""
    s = new()
    s.rect(2, 4, 9, 6, C["d"]); s.line(2, 4, 9, 4, C["e"])
    s.rect(3, 7, 4, 12, C["d"]); s.rect(7, 7, 8, 12, C["d"])
    s.rect(9, 8, 13, 12, C["e"]); s.line(9, 12, 13, 12, C["d"])
    s.line(13, 6, 13, 7, C["d"]); s.line(10, 13, 10, 14, C["d"]); s.line(13, 13, 13, 14, C["d"])
    s.outline(C["K"], where="inside")
    s.line(3, 15, 13, 15, C["1"])
    return s


def prop_cushion():
    """방석(술 장식): 천 d · 빛 e · 그늘 i · 귀퉁이 술 S."""
    s = new()
    s.rect(3, 6, 12, 12, C["d"]); s.line(3, 6, 12, 6, C["e"]); s.line(3, 6, 3, 12, C["e"])
    s.line(4, 12, 12, 12, C["i"]); s.line(12, 7, 12, 12, C["i"])
    s.px(7, 9, C["i"]); s.px(8, 9, C["i"])
    s.outline(C["K"], where="inside")
    for x, y in ((2, 5), (13, 5), (2, 13), (13, 13)):
        s.px(x, y, C["S"])
    return s


def tiles():
    return (
        [("floor_%d" % i, common_floor(i)) for i in range(4)]
        + [("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
           ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
           ("exit", exit_tile()), ("shop", shop_tile()),
           ("prop_goblet", prop_goblet()), ("prop_wine_spill", prop_wine_spill()), ("prop_candelabra", prop_candelabra()),
           ("prop_platter", prop_platter()), ("prop_chair", prop_chair()), ("prop_wine_jar", v4.prop_wine_jar()),
           ("prop_cushion", prop_cushion()), ("prop_bottle", v4.prop_bottle()),
           ("wall_v1", wall_v1()), ("wall_v2", wall_v2())]
        + [("start_%d" % i, start_floor(i)) for i in range(4)]
        + [("trial_%d" % i, trial_floor(i)) for i in range(4)]
        + [("rest_%d" % i, rest_floor(i)) for i in range(4)]
        + [("boss_%d" % i, boss_floor(i)) for i in range(4)]
        + [("reserve", new())]
    )


PROPS = [("toppled_goblet", False, 3, 1.0), ("wine_spill", False, 3, 1.0), ("candelabra", True, 1, 0.6), ("platter", False, 2, 0.8),
         ("chair", True, 2, 0.7), ("wine_jar", True, 1, 0.5), ("cushion", False, 2, 0.7), ("broken_bottle", False, 3, 0.9)]
