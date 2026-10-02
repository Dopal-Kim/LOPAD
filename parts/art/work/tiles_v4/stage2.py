#!/usr/bin/env python3
"""2층 '패(牌)' 도박장 제국 외곽 — 바닥 타일 v4: 보도블록 뒷골목.

1층(큰 판석 16x16)과 갈리도록 **보도블록 16x8 반장 엇쌓기**(위 줄 이음 x=0, 아래 줄 이음 x=8). 패턴 자체가 타일 안에서 완결되어
어떤 변형 조합으로도 같은 엇쌓기가 이어진다(16px 격자가 아니라 블록 결이 보인다). 면 G02 · 줄눈 G01 — 1층과 같은 명도 대역.
강조(녹색)는 1층과 같은 규칙: 시련·보스 방 한 변형의 금 사이 1~2px, 버린 칩은 소품으로만.
2층에는 여정 노드가 없다(48라운드 Q9) → start 는 '들어선 자리' 로 흙이 밀려든 보도블록.
"""
import pave
import tilecommon2 as tc

T = pave.T
C = pave.colors(2)
ctx = tc.Ctx(C)
P = pave.Pave(ctx, face="2", joint="1")
new = ctx.new

DIAMOND = [(3, 0), (2, 1), (3, 1), (4, 1), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (2, 3), (3, 3), (4, 3), (3, 4)]  # 패 문양 7x5


def bond():
    s = P.base(edges=False)
    P.hj(s, 0); P.hj(s, 8)
    P.vj(s, 0, 1, 7); P.vj(s, 8, 9, T - 1)
    return s


def sunk(s, x0, y0, x1, y1):
    """가라앉은 블록 한 장: 면이 한 단 어둡고(G01) 위 턱 K 그늘."""
    s.rect(x0, y0, x1, y1, C["1"])
    s.line(x0, y0, x1, y0, C["K"])


# ============================================================ 바닥 — 엇쌓기는 4변형 모두 같고, 손상은 변형 하나에 하나만
def common_floor(i):
    s = bond()
    if i == 1:
        P.crack(s, [(9, 1), (11, 4), (12, 7)])                      # 블록 한 장 금 (줄눈 → 줄눈)
    elif i == 2:
        s.px(1, 1, C["1"]); s.px(2, 1, C["1"]); s.px(1, 2, C["1"])   # 줄눈 교차점이 깨져 넓어짐        # 귀퉁이 이 빠짐
    return s


def corridor_tile():
    s = bond()
    s.rect(1, 1, T - 1, 7, C["1"]); s.rect(0, 9, 7, T - 1, C["1"]); s.rect(9, 9, T - 1, T - 1, C["1"])
    return s


def start_floor(i):
    """들어선 자리: 보도블록 위 흙(작게)."""
    s = bond()
    if i == 0:
        P.blob(s, 6, 12, 2.4, "1", seed=71, squash=0.6)
    elif i == 2:
        s.px(11, 4, C["3"]); s.px(12, 4, C["3"]); s.px(11, 5, C["1"]); s.px(12, 5, C["1"])
    return s


def trial_floor(i):
    if i == 0:
        s = bond()
        P.crack(s, [(3, 0), (4, 3), (7, 5), (8, 8)])
        P.crack(s, [(8, 8), (10, 11), (13, 13), (15, 13)])
        s.px(7, 5, C["K"]); s.px(8, 6, C["K"])
        return s
    if i == 3:
        s = bond()
        s.px(1, 1, C["1"]); s.px(2, 1, C["1"]); s.px(1, 2, C["1"])   # 줄눈 교차점이 깨져 넓어짐
        return s
    return bond()


def rest_floor(i):
    s = bond()
    if i == 0:
        s.px(1, 1, C["1"]); s.px(2, 1, C["1"]); s.px(1, 2, C["1"])
    return s


def boss_floor(i):
    """판돈 백작의 판: _0 벌어진 금 사이에만 녹빛 2px, _1 블록에 패 문양(G01 낮은 대비)."""
    if i == 0:
        s = bond()
        P.crack(s, [(0, 5), (4, 4), (6, 6), (9, 5), (11, 7), (14, 6), (15, 6)])
        s.px(6, 6, C["K"]); s.px(7, 6, C["K"])
        s.px(6, 6, C["S"])                                          # 금 사이 녹빛 1px
        return s
    if i == 1:
        s = bond()
        P.crack(s, [(2, 9), (4, 12), (3, 15)])
        return s
    return bond()


# ============================================================ 벽 (도박장 뒷벽: 판자)
def wall_base(s):
    """벽 정면: 세로 판자 4장(G03), 틈 G02, 위 덮개 테 G04 + K, 아래 발치 K. 못·옹이 1점씩."""
    s.rect(0, 0, T - 1, T - 1, C["3"])
    for x in (0, 4, 8, 12):
        s.line(x, 2, x, T - 1, C["2"])
    s.line(0, 0, T - 1, 0, C["4"]); s.line(0, 1, T - 1, 1, C["K"])
    s.px(6, 4, C["4"]); s.px(14, 12, C["4"])
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_face():
    return wall_base(new())


def wall_v1():
    """패 문양 스텐실 — 닳아서 G04(낮은 대비)."""
    s = wall_base(new())
    for x, y in DIAMOND:
        s.px(x + 4, y + 6, C["4"])
    return s


def wall_v2():
    """'한 판만 더' 셈 자국(G04) 한 묶음 + 판자 하나가 떨어져 나간 틈(K)."""
    s = wall_base(new())
    for x in (2, 3):
        s.line(x, 5, x, 9, C["4"])
    s.line(1, 9, 4, 6, C["4"])
    s.line(9, 9, 9, 13, C["1"])                                    # 판자 틈이 벌어진 자리
    return s


def wall_top():
    """벽 윗면: 가로 판자 덮개 G04, 이음 G03, 못 1점."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["3"])
    s.line(0, 0, 0, T - 1, C["3"])
    s.px(7, 2, C["5"]); s.px(12, 13, C["3"])
    return s


# ============================================================ 문
def door_frame(s):
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["4"]); s.line(0, 0, 0, T - 1, C["3"]); s.line(2, 0, 2, T - 1, C["K"])
    s.rect(13, 0, 15, T - 1, C["4"]); s.line(15, 0, 15, T - 1, C["3"]); s.line(13, 0, 13, T - 1, C["K"])
    s.rect(0, 0, T - 1, 1, C["4"]); s.line(0, 0, T - 1, 0, C["3"]); s.line(3, 1, 12, 1, C["K"])


def door_open():
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
    for y in (y0 + 2, y0 + 11):
        s.line(x0, y, x1, y, C["6"])
        s.line(x0, y + 1, x1, y + 1, C["3"])


def peephole(s):
    s.rect(5, 7, 10, 8, C["K"]); s.px(7, 7, C["S"]); s.px(8, 7, C["S"])


def door_closed():
    s = new()
    door_frame(s); door_planks(s); peephole(s)
    s.px(10, 11, C["7"])
    return s


def door_locked():
    s = new()
    door_frame(s); door_planks(s); peephole(s)
    for i, (x, y) in enumerate([(3, 14), (4, 13), (5, 12), (6, 11), (7, 10), (8, 9), (9, 8), (10, 7), (11, 6), (12, 5)]):
        s.px(x, y, C["7"] if i % 2 == 0 else C["6"])
    s.rect(6, 11, 9, 14, C["7"]); s.line(6, 11, 9, 11, C["9"])
    s.px(7, 12, C["K"]); s.px(7, 13, C["K"])
    return s


# ============================================================ 출구 · 상점
def exit_stairs():
    s = new()
    body = ["4", "3", "3", "2"]
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["5" if i < 2 else "4"])
        s.rect(0, y + 2, T - 1, y + 3, C[body[i]])
    s.px(6, 13, C["S"]); s.px(7, 13, C["B"])
    return s


def chip(s, x, y):
    s.rect(x, y, x + 1, y + 1, C["B"]); s.px(x, y, C["L"])


def shop_counter():
    """좌판: 널 탁자(G04) 위 펠트 깔개(S) + 칩 더미 2 + 패 1."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    s.line(0, 0, T - 1, 0, C["3"]); s.line(0, 15, T - 1, 15, C["2"])
    s.rect(2, 3, 13, 12, C["S"])
    s.line(2, 13, 13, 13, C["2"])
    for bx, h in ((4, 5), (9, 3)):
        for k in range(h):
            y = 11 - k
            s.line(bx, y, bx + 2, y, C["B"] if k % 2 == 0 else C["C"])
    s.rect(8, 4, 10, 7, C["7"]); s.px(8, 4, C["9"])
    return s


# ============================================================ 소품 — 40라운드 그림 정돈
def prop_dice_cup():
    s = new()
    s.rect(5, 4, 10, 11, C["6"])
    s.line(5, 4, 5, 11, C["7"]); s.line(10, 4, 10, 11, C["5"])
    s.rect(5, 3, 10, 3, C["5"]); s.rect(6, 2, 9, 2, C["4"])
    s.outline(C["K"], where="inside")
    for dx, dy in ((11, 9), (1, 10)):
        s.rect(dx, dy, dx + 2, dy + 2, C["C"]); s.px(dx + 1, dy + 1, C["K"])
        s.line(dx, dy + 3, dx + 2, dy + 3, C["K"])
    return s


def prop_sack():
    s = new()
    prof = {2: (6, 9), 3: (6, 9), 4: (5, 10), 5: (4, 11), 6: (3, 12), 7: (3, 12), 8: (2, 13), 9: (2, 13),
            10: (2, 13), 11: (2, 13), 12: (3, 12), 13: (3, 12), 14: (4, 11)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["6"]); s.px(x0, y, C["7"]); s.px(x1, y, C["5"])
    s.line(6, 4, 9, 4, C["K"])
    s.rect(6, 1, 9, 2, C["5"])
    s.rect(11, 6, 12, 8, C["9"])
    s.outline(C["K"], where="inside")
    chip(s, 13, 13)
    return s


def prop_chair():
    s = new()
    s.rect(1, 3, 4, 3, C["5"]); s.rect(1, 12, 4, 12, C["4"])
    s.line(1, 3, 1, 12, C["4"]); s.line(3, 3, 3, 12, C["4"])
    s.rect(5, 5, 9, 10, C["4"]); s.line(5, 5, 9, 5, C["5"]); s.line(5, 10, 9, 10, C["3"])
    s.line(10, 6, 14, 6, C["5"]); s.line(10, 10, 14, 10, C["5"])
    s.outline(C["K"], where="inside")
    s.px(1, 3, C["5"]); s.px(2, 3, C["5"])
    return s


def prop_lantern():
    s = new()
    s.line(11, 3, 11, 13, C["5"]); s.line(12, 3, 12, 13, C["4"])
    s.rect(9, 14, 14, 14, C["5"]); s.rect(8, 15, 15, 15, C["3"])
    s.line(7, 1, 12, 1, C["5"]); s.px(6, 2, C["5"])
    prof = {4: (5, 7), 5: (4, 8), 6: (3, 9), 7: (3, 9), 8: (3, 9), 9: (3, 9), 10: (4, 8), 11: (5, 7)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["B"])
    s.rect(5, 6, 7, 9, C["L"])
    s.px(6, 7, C["W"]); s.px(6, 8, C["W"])
    s.line(5, 4, 7, 4, C["6"]); s.line(5, 11, 7, 11, C["6"]); s.px(6, 12, C["6"])
    s.outline(C["K"], where="inside")
    s.line(8, 1, 11, 1, C["5"], only=C["K"])
    return s


def prop_ledger():
    s = new()
    s.rect(2, 5, 13, 12, C["4"])
    s.rect(3, 4, 7, 11, C["9"]); s.rect(8, 4, 12, 11, C["9"])
    s.line(7, 4, 7, 11, C["6"])
    for y in (6, 8, 10):
        s.line(4, y, 6, y, C["5"]); s.line(9, y, 11, y, C["5"])
    s.px(5, 8, C["S"]); s.px(6, 8, C["S"])
    s.outline(C["K"], where="inside")
    s.line(4, 4, 6, 4, C["C"], only=C["K"]); s.line(9, 4, 11, 4, C["C"], only=C["K"])
    return s


def prop_cage():
    s = new()
    s.rect(3, 2, 12, 13, C["K"])
    for x in (3, 6, 9, 12):
        s.line(x, 2, x, 13, C["6"])
    s.line(3, 2, 12, 2, C["6"]); s.line(3, 13, 12, 13, C["5"]); s.line(3, 7, 12, 7, C["5"])
    s.px(7, 9, C["9"]); s.px(8, 9, C["9"]); s.px(10, 11, C["9"])
    s.rect(2, 14, 13, 14, C["4"])
    s.outline(C["K"], where="inside")
    s.rect(3, 14, 12, 14, C["4"])
    s.line(4, 2, 11, 2, C["6"], only=C["K"])
    return s


def prop_card_table():
    s = new()
    s.circle(7, 8, 6, C["4"], fill=True)
    s.circle(7, 8, 6, C["5"], fill=False)
    for y in range(6, 11):
        half = 3 - abs(y - 8) // 2
        s.line(7 - half, y, 7 + half, y, C["S"], only=C["4"])
    s.rect(6, 6, 8, 8, C["6"])
    s.line(13, 5, 15, 3, C["3"]); s.line(13, 11, 15, 13, C["3"])
    s.outline(C["K"], where="inside")
    return s


def prop_chip_scatter():
    s = new()
    chip(s, 3, 4); chip(s, 11, 3); chip(s, 7, 11)
    s.rect(6, 5, 8, 7, C["6"]); s.line(6, 8, 8, 8, C["K"])
    s.rect(11, 9, 12, 10, C["7"]); s.line(11, 11, 12, 11, C["K"])
    return s


def void_tile():
    return new()


def tiles():
    return (
        [("floor_%d" % i, common_floor(i)) for i in range(4)]
        + [("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
           ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
           ("exit", exit_stairs()), ("shop", shop_counter()),
           ("prop_dice_cup", prop_dice_cup()), ("prop_sack", prop_sack()), ("prop_chair", prop_chair()),
           ("prop_lantern", prop_lantern()), ("prop_ledger", prop_ledger()), ("prop_cage", prop_cage()),
           ("prop_card_table", prop_card_table()), ("prop_chip_scatter", prop_chip_scatter()),
           ("wall_v1", wall_v1()), ("wall_v2", wall_v2())]
        + [("start_%d" % i, start_floor(i)) for i in range(4)]
        + [("trial_%d" % i, trial_floor(i)) for i in range(4)]
        + [("rest_%d" % i, rest_floor(i)) for i in range(4)]
        + [("boss_%d" % i, boss_floor(i)) for i in range(4)]
        + [("reserve", void_tile())]
    )


PROPS = [("dice_cup", False, 3, 1.0), ("stake_sack", True, 2, 0.8), ("overturned_chair", False, 2, 0.8), ("green_lantern", True, 1, 0.6),
         ("debt_ledger", False, 1, 0.6), ("iron_cage", True, 1, 0.4), ("card_table", True, 1, 0.4), ("chip_scatter", False, 3, 1.0)]
NAME = "패(牌) — 도박장 제국 외곽"
