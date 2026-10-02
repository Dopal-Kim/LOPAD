#!/usr/bin/env python3
"""brewery — 양조 구역 (외곽 거리를 지나 술을 빚는 곳). 젖은 판석 마당과 술통·증류 배관.

바닥 = 반장(16x8) 엇쌓기 판석(면 2 · 줄눈 1) + **젖은 반사**(4 짧은 줄)·**술 얼룩**(i)을 넷 중 하나씩.
경계 = **쌓아 올린 술통 마구리**(정면) · 벽돌 벽을 지나는 **증류 배관과 밸브** · 꼭지에서 술이 새는 **큰 술독**, 윗면 = 세워 둔 술통 뚜껑들.
void = 술이 흘러드는 어두운 수로(갈색 물결). 문 = 술통 널빤지 문. 출구 = 등불빛 젖은 널판 길. 상점 = 술통 위 판자 계산대.
"""
import rkit as K
import stage1 as v4
from rkit import C, T, blit, blob, new

NAME = "잔(盞) — 양조 구역"


# ------------------------------------------------------------ 바닥
# 1회차 비평: 16x8 판석은 '벽돌 바닥(실내)' 으로 읽혔고, 술 얼룩 변형이 25% 섞기에서 갈색 점 무늬가 됐다.
# → **젖은 널판 마당**(수로 옆 선창 널): 가로 널 4px 줄 · 이음 K · 면 PLANK, 젖은 반사는 d 짧은 줄(넷 중 하나), 얼룩은 소품으로.
PLANK, SEAM, WET = "2", "1", "3"   # 3회차: 반사를 d(갈색)로 하니 나뭇조각으로 읽혀 회색 한 단(3)으로
BUTTS = [(0, None), (4, 11), (8, None), (12, 4)]     # (줄 y, 맞댄 이음 x) — 2회차: 줄마다 이음을 넣으면 벽돌로 읽혀 두 줄만


def planks(face=PLANK, seam=SEAM, butts=BUTTS):
    s = K.fill(face)
    for y, bx in butts:
        s.line(0, y, T - 1, y, C[seam])
        if bx is not None:
            s.line(bx, y + 1, bx, y + 3, C[seam])
    return s


def sheen(s, x, y, n=3, c=WET):
    """젖은 널의 반사: 이음 바로 아래 줄에 n px."""
    s.line(x, y, x + n - 1, y, C[c])
    return s


def common_floor(i):
    s = planks()
    if i == 0:
        sheen(s, 6, 1)
    elif i == 2:
        s.px(9, 10, C["2"]); s.px(10, 10, C["2"])                                 # 못 자국
    return s


def start_floor(i):
    s = planks()
    if i == 1:
        sheen(s, 1, 9)
    return s


def trial_floor(i):
    s = planks()
    if i == 0:
        sheen(s, 8, 5, 4)
    elif i == 3:
        s.line(2, 13, 6, 13, C["K"])                                              # 갈라진 널
    return s


def rest_floor(i):
    s = planks()
    if i == 2:
        sheen(s, 9, 13)
    return s


def boss_floor(i):
    s = planks()
    if i == 0:
        blob(s, 7, 10, 2.6, "i", seed=17, squash=0.6); s.px(6, 9, C["S"])
    elif i == 1:
        sheen(s, 3, 1, 4)
    elif i == 2:
        s.line(9, 6, 13, 6, C["K"])
    return s


def corridor_tile():
    return planks("1", "K")


# ------------------------------------------------------------ 술통 더미 (북 경계)
def barrel_side(s, x0, y0, length=16):
    """옆으로 누운 술통(옆모습) 한 줄: 높이 7 — 윗줄 e(빛) · 몸 d · 아랫줄 i, 양 끝 마구리 i/K, 쇠테 4(세로 2줄씩).
    x 는 16 으로 감아 그린다(윗줄 통을 8px 엇갈려 쌓기 위해). 1회차의 '작은 마구리 원 4개' 는 2배 화면에서 사슬처럼 읽혔다."""
    rows = ["iddddddddddddddi", "deeeeeeeeeeeeeed", "dddddddddddddddd", "dddddddddddddddd", "dddddddddddddddd", "iddddddddddddddi", "KiiiiiiiiiiiiiiK"]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            x = (x0 + i) % T
            if i in (0, 15) and j in (0, 6):
                ch = "K"
            s.px(x, y0 + j, C[ch])
    for hx in (3, 12):
        for j in range(7):
            x = (x0 + hx) % T
            s.px(x, y0 + j, C["5" if j == 1 else ("3" if j >= 5 else "4")])
    s.px((x0 + 8) % T, y0 + 3, C["K"])                                        # 마개
    return s


def barrel_wall():
    """술통 더미 정면: 옆으로 누운 통 두 줄(윗줄 8px 엇갈림) + 맨 아래 땅 그늘."""
    s = K.fill("K")
    barrel_side(s, 8, 1)
    barrel_side(s, 0, 8)
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_face():
    return barrel_wall()


def brick_wall():
    s = K.fill("3")
    for y in (0, 4, 8, 12):
        s.line(0, y, T - 1, y, C["2"])
    for j, y0 in enumerate((1, 5, 9, 13)):
        for x in ((0, 8) if j % 2 == 0 else (4, 12)):
            s.line(x, y0, x, y0 + 2, C["2"])
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_v1():
    """벽돌 벽을 지나는 증류 배관(6/5/4) + 밸브 바퀴(7) + 이음 테 · 밸브 아래 맺힌 술 방울(S)."""
    s = brick_wall()
    s.rect(0, 5, T - 1, 7, C["5"]); s.line(0, 5, T - 1, 5, C["6"]); s.line(0, 7, T - 1, 7, C["4"]); s.line(0, 8, T - 1, 8, C["1"])
    for x in (3, 4):
        s.line(x, 4, x, 8, C["4"])
    s.line(3, 4, 3, 8, C["6"])
    s.rect(9, 2, 13, 4, C["7"]); s.rect(10, 3, 12, 3, C["5"]); s.line(11, 4, 11, 5, C["6"])
    s.px(11, 9, C["S"]); s.px(11, 11, C["S"]); s.px(11, 14, C["d"]); s.px(12, 14, C["d"])
    return s


def wall_v2():
    """큰 술독 앞면: 세로 널(d/e/i) + 쇠테 둘(4) + 꼭지(6)에서 새는 술(B → S) + 발치 고임(d)."""
    s = K.fill("d")
    for x in range(0, T, 4):
        s.line(x, 0, x, 14, C["i"]); s.line(x + 1, 0, x + 1, 14, C["e"])
    for y in (2, 11):
        s.line(0, y, T - 1, y, C["5"]); s.line(0, y + 1, T - 1, y + 1, C["4"]); s.line(0, y - 1, T - 1, y - 1, C["3"])
    s.rect(7, 7, 9, 8, C["6"]); s.px(9, 9, C["5"])
    s.px(9, 10, C["B"]); s.px(9, 12, C["S"])
    s.line(6, 14, 11, 14, C["S"]); s.line(7, 15, 10, 15, C["d"])
    s.line(0, 15, 5, 15, C["K"]); s.line(11, 15, T - 1, 15, C["K"])
    return s


def wall_top():
    """세워 둔 큰 술통 뚜껑(위에서) 한 장: 쇠테 5/3 · 뚜껑 널 d(빛 e, 이음 i) · 마개 K, 통 사이 틈 K.
    1회차: 작은 뚜껑 4개는 사슬 무늬 → 한 장에 하나."""
    s = K.fill("K")
    cx = cy = 8
    for y in range(T):
        for x in range(T):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = (dx * dx + dy * dy) ** 0.5
            if d > 7.6:
                continue
            if d > 6.3:
                c = "5" if (dx + dy) < -2 else ("4" if (dx + dy) < 3 else "3")
            else:
                c = "e" if (dx + dy) < -6 else ("d" if (dx + dy) < 5 else "i")
                if x in (5, 10):
                    c = "i"
            s.px(x, y, C[c])
    s.px(8, 8, C["K"]); s.px(7, 8, C["i"])
    return s


def void_tile():
    """원경: 술이 흘러드는 어두운 수로 — 바탕 i, 물결 d(가로, 길이 다르게), 드물게 e 반짝임."""
    s = K.fill("i")
    for y, segs in ((1, [(1, 4), (10, 14)]), (5, [(5, 9)]), (9, [(0, 2), (11, 15)]), (13, [(3, 7)])):
        for x0, x1 in segs:
            s.line(x0, y, x1, y, C["d"])
    s.px(6, 5, C["e"])
    for y, segs in ((3, [(7, 11)]), (11, [(6, 9)]), (15, [(12, 15)])):
        for x0, x1 in segs:
            s.line(x0, y, x1, y, C["K"])
    return s


# ------------------------------------------------------------ 문 (술통 널 문)
def frame(s):
    s.rect(0, 0, 2, T - 1, C["3"]); s.line(0, 0, 0, T - 1, C["4"]); s.line(2, 0, 2, T - 1, C["K"])
    s.rect(13, 0, 15, T - 1, C["3"]); s.line(13, 0, 13, T - 1, C["4"]); s.line(15, 0, 15, T - 1, C["2"])
    s.rect(0, 0, T - 1, 1, C["3"]); s.line(0, 0, T - 1, 0, C["4"]); s.line(3, 1, 12, 1, C["K"])


def staves(s):
    s.rect(3, 2, 12, 15, C["d"])
    for x in (3, 6, 9):
        s.line(x, 2, x, 15, C["i"]); s.line(x + 1, 2, x + 1, 15, C["e"])
    for y in (5, 12):
        s.line(3, y, 12, y, C["5"]); s.line(3, y + 1, 12, y + 1, C["3"])


def door_open():
    s = K.fill("i")
    frame(s)
    s.rect(3, 2, 4, 15, C["d"]); s.line(4, 2, 4, 15, C["e"])
    s.line(6, 4, 6, 13, C["S"]); s.px(6, 8, C["B"])
    return s


def door_closed():
    s = new()
    frame(s)
    staves(s)
    return s


def door_locked():
    s = door_closed()
    s.rect(2, 8, 13, 9, C["6"]); s.line(2, 9, 13, 9, C["4"])
    s.rect(6, 10, 9, 12, C["7"]); s.line(6, 10, 9, 10, C["9"]); s.px(7, 11, C["K"])
    return s


# ------------------------------------------------------------ 출구 · 상점
def exit_tile():
    """출구 = 등불빛 젖은 널판 길(가로 널 d · 이음 i · 윗변 e · 반사 S). 2x2 반복."""
    s = K.fill("d")
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["i"]); s.line(0, y + 1, T - 1, y + 1, C["e"])
    for x, y in ((5, 2), (12, 7), (2, 12)):
        s.line(x, y, x, y + 2, C["i"])
    s.line(8, 3, 10, 3, C["S"]); s.line(3, 13, 4, 13, C["S"])
    return s


def shop_tile():
    """술통 위 판자 계산대: 널(e/d) 위 백랍 잔(6/7) + 거품(C) · 술 자국(i). 2x2 반복."""
    s = K.fill("d")
    for y in (0, 8):
        s.line(0, y, T - 1, y, C["i"]); s.line(0, y + 1, T - 1, y + 1, C["e"])
    for x, y in ((3, 2), (10, 9)):
        s.rect(x, y + 1, x + 2, y + 5, C["6"]); s.line(x, y + 1, x, y + 5, C["7"]); s.line(x + 2, y + 2, x + 2, y + 5, C["4"])
        s.line(x, y, x + 2, y, C["C"]); s.px(x + 3, y + 2, C["5"]); s.px(x + 3, y + 3, C["5"])
        s.line(x, y + 6, x + 2, y + 6, C["i"])
    s.px(12, 4, C["i"]); s.px(13, 4, C["i"]); s.px(5, 12, C["i"])
    return s


# ------------------------------------------------------------ 소품 8
def ell(s, cx, cy, rx, ry, ch):
    for y in range(T):
        for x in range(T):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                s.px(x, y, C[ch])


def prop_liquor_puddle():
    """술 웅덩이(통과): 납작한 타원 — 젖은 테 1 · 술 i · 가운데 d, 반사는 안쪽 가로 줄 e + 등불 한 점 S.
    (1회차: 울퉁불퉁한 덩어리 + 테두리 위쪽 밝은 줄이 갈색 돌로 읽혔다)"""
    s = new()
    ell(s, 8, 10, 7, 3.6, "1")
    ell(s, 8, 10, 6, 2.8, "i")
    ell(s, 7.5, 10, 3.5, 1.4, "d")
    s.line(5, 9, 8, 9, C["e"]); s.px(11, 11, C["S"])
    return s


def prop_pipe_valve():
    """바닥에서 솟은 배관 + 밸브 바퀴(세움)."""
    s = new()
    s.rect(6, 6, 9, 14, C["5"]); s.line(6, 6, 6, 14, C["6"]); s.line(9, 6, 9, 14, C["3"])
    s.rect(5, 12, 10, 13, C["4"]); s.line(5, 12, 10, 12, C["6"])
    s.rect(3, 2, 12, 5, C["7"]); s.rect(5, 3, 10, 4, C["K"]); s.line(7, 3, 8, 4, C["6"]); s.px(7, 4, C["6"])
    s.outline(C["K"], where="inside")
    s.line(4, 2, 11, 2, C["9"], only=C["K"])
    s.px(10, 15, C["S"]); s.line(4, 15, 9, 15, C["1"])
    return s


def prop_grain_sack():
    s = new()
    blit(s, ["....TT.....", "...T99T....", "....44.....", "..TTTTTT...", ".T999999T..", ".T9999997..", ".T9999977..", "..777777..."], 3, 4)
    s.outline(C["K"], where="inside")
    s.px(6, 4, C["9"]); s.px(7, 4, C["9"])
    for x, y in ((12, 12), (13, 13), (11, 13)):
        s.px(x, y, C["e"])
    s.line(4, 12, 10, 12, C["1"])
    return s


def prop_mash_tub():
    """술밑 통(세움): 타원 테 e/d + 속 엿기름 반죽 d·거품 e + 쇠테."""
    s = new()
    for y in range(3, 15):
        for x in range(1, 15):
            if ((x - 7.5) / 6.5) ** 2 + ((y - 9) / 6) ** 2 <= 1 and y >= 5:
                s.px(x, y, C["d"])
    s.rect(2, 8, 13, 13, C["d"])
    for x in range(2, 14, 3):
        s.line(x, 8, x, 13, C["i"])
    s.line(2, 11, 13, 11, C["4"])
    for y in range(4, 9):
        for x in range(1, 15):
            d = ((x - 7.5) / 6.5) ** 2 + ((y - 6) / 2.4) ** 2
            if d <= 1:
                s.px(x, y, C["e"] if d > 0.55 else "#000000")
    for y in range(5, 8):
        for x in range(3, 13):
            if ((x - 7.5) / 4.6) ** 2 + ((y - 6.2) / 1.4) ** 2 <= 1:
                s.px(x, y, C["i"])
    s.px(6, 6, C["d"]); s.px(9, 6, C["e"]); s.px(8, 7, C["d"])
    s.outline(C["K"], where="inside")
    s.line(3, 15, 12, 15, C["1"])
    return s


def prop_hose():
    """둘둘 만 밧줄·호스(바닥): 나선 e/d."""
    s = new()
    for r, c in ((5, "e"), (3, "d"), (1.5, "e")):
        for y in range(3, 15):
            for x in range(1, 15):
                d = ((x - 8) / 1.0) ** 2 + ((y - 9) / 0.7) ** 2
                if (r - 0.7) ** 2 <= d <= (r + 0.5) ** 2:
                    s.px(x, y, C[c])
    s.line(12, 8, 15, 6, C["d"])
    s.line(3, 13, 12, 13, C["1"])
    return s


def prop_furnace_grate():
    """증류 화덕 바닥 쇠살창(통과): 쇠살 4 사이로 숯불 S·B·L — 양조 구역의 '금 사이 잔불' 역할(방당 1)."""
    s = new()
    s.rect(2, 4, 13, 12, C["K"])
    for x, y in ((4, 6), (6, 9), (9, 7), (11, 10), (7, 5)):
        s.px(x, y, C["S"])
    s.px(6, 8, C["B"]); s.px(9, 8, C["L"]); s.px(10, 7, C["B"]); s.px(8, 10, C["S"])
    for x in (2, 5, 8, 11):
        s.line(x, 4, x, 12, C["4"])
    s.line(13, 4, 13, 12, C["3"])
    s.line(2, 4, 13, 4, C["5"]); s.line(2, 12, 13, 12, C["3"])
    return s


def prop_drain():
    """바닥 배수구(통과): 젖은 테 1 + 쇠 뚜껑 4/5 + 구멍 K."""
    s = new()
    blob(s, 8, 9, 5, "1", seed=33, squash=0.6, lo=0, hi=15)
    s.rect(4, 7, 11, 11, C["4"]); s.line(4, 7, 11, 7, C["5"]); s.line(4, 11, 11, 11, C["3"])
    for x in (5, 7, 9):
        s.line(x, 8, x, 10, C["K"])
    s.px(10, 13, C["i"]); s.px(11, 13, C["i"])
    return s


def tiles():
    return (
        [("floor_%d" % i, common_floor(i)) for i in range(4)]
        + [("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
           ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
           ("exit", exit_tile()), ("shop", shop_tile()),
           ("prop_barrel", v4.prop_barrel()), ("prop_liquor_puddle", prop_liquor_puddle()), ("prop_pipe_valve", prop_pipe_valve()),
           ("prop_grain_sack", prop_grain_sack()), ("prop_mash_tub", prop_mash_tub()), ("prop_hose", prop_hose()),
           ("prop_furnace_grate", prop_furnace_grate()), ("prop_drain", prop_drain()),
           ("wall_v1", wall_v1()), ("wall_v2", wall_v2())]
        + [("start_%d" % i, start_floor(i)) for i in range(4)]
        + [("trial_%d" % i, trial_floor(i)) for i in range(4)]
        + [("rest_%d" % i, rest_floor(i)) for i in range(4)]
        + [("boss_%d" % i, boss_floor(i)) for i in range(4)]
        + [("reserve", new())]
    )


PROPS = [("barrel", True, 2, 0.8), ("liquor_puddle", False, 3, 1.0), ("pipe_valve", True, 1, 0.6), ("grain_sack", True, 2, 0.7),
         ("mash_tub", True, 1, 0.5), ("hose", False, 2, 0.8), ("furnace_grate", False, 1, 0.6), ("drain", False, 2, 0.8)]
