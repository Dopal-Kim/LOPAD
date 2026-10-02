#!/usr/bin/env python3
"""gate — 성문 앞 (술 제국 '잔' 에 들어서는 길목). 황무지의 흙길이 처음으로 **돌길(정사각 돌 8x8 엇갈림)** 이 된다.

바닥 = 둥근 모서리 사각 돌(면 2 · 줄눈 1), 변형마다 하나: 닳은 돌 · 금 · 빠진 돌(흙이 드러남) · 줄눈의 흙.
경계 = **성벽 앞면**(위 총안 성가퀴 + 큰 마름돌 2단) · 화살 구멍 · 잔(盞) 제국 깃발, 윗면 = 성벽 위 통로 돌판.
void = 성벽 아래 해자의 검은 물(가로 물결). 문 = 내리닫이 쇠창살(열림 = 들어 올린 창살 이빨). 출구 = 열린 성문 안에서 비치는 등불빛 돌길.
"""
import rkit as K
from rkit import C, T, blit, blob, new

NAME = "잔(盞) — 성문"
FACE, JOINT = "3", "d"   # 2회차: 회색 줄눈(1)은 화장실 타일처럼 읽혔다 → 돌 사이에 흙(d)이 찬 자갈돌 길


# ------------------------------------------------------------ 돌길
def setts(face=FACE, joint=JOINT, lit=None):
    """8x8 돌 엇갈림 (윗줄 이음 x=0,8 / 아랫줄 x=4,12). 돌마다 좌상·우하 모서리 1px 를 줄눈색으로 → 둥근 사각 돌.
    lit 이 있으면 돌 윗변 안쪽 1px 를 lit (등불빛 출구 전용)."""
    s = K.fill(face)
    s.line(0, 0, T - 1, 0, C[joint]); s.line(0, 8, T - 1, 8, C[joint])
    for y0, xs in ((1, (0, 8)), (9, (4, 12))):
        for x in xs:
            s.line(x, y0, x, y0 + 6, C[joint])
        for x in xs:
            x0 = x + 1
            s.px(x0 % T, y0, C[joint]); s.px((x0 + 6) % T, y0 + 6, C[joint])
            if lit:
                for k in range(1, 6):
                    s.px((x0 + k) % T, y0, C[lit])
    return s


def worn(s, x0, y0):
    """닳아 반들반들한 돌 하나: 면 한 단 밝게(3) — 낮은 대비."""
    for y in range(y0 + 1, y0 + 6):
        for x in range(x0 + 1, x0 + 6):
            if s.get(x % T, y) and s.get(x % T, y)[:3] == K.tc2.hexrgb(C[FACE]):
                s.px(x % T, y, C["4"])
    return s


def common_floor(i):
    s = setts()
    if i == 1:
        worn(s, 0, 0)
    elif i == 3:
        K.line(s, [(10, 10), (12, 12), (12, 14)], "2")
    return s


def start_floor(i):
    """성문에 막 닿은 길: 줄눈에 황무지 흙(d)이 끼었다 — 넷 중 둘."""
    s = setts()
    if i == 0:
        s.line(1, 8, 6, 8, C["e"]); s.px(1, 7, C["d"]); s.px(2, 7, C["d"])
    elif i == 2:
        s.px(12, 10, C["d"]); s.px(12, 11, C["d"]); s.px(13, 11, C["d"])
    return s


def trial_floor(i):
    """1회차: 빠진 돌(흙 사각형)을 변형에 넣었더니 25% 섞기에서 갈색 점이 화면에 수십 개 → 빠진 돌은 소품 rubble 쪽으로."""
    s = setts()
    if i == 0:
        K.line(s, [(9, 2), (11, 4), (11, 6)], "2")
    return s


def rest_floor(i):
    return setts()


def boss_floor(i):
    s = setts()
    if i == 0:
        K.line(s, [(9, 1), (11, 3), (11, 5), (13, 7)], "K")
        s.px(11, 4, C["S"])
    elif i == 1:
        worn(s, 4, 8)
    elif i == 3:
        K.line(s, [(2, 10), (5, 12), (5, 14)], "2")
    return s


def corridor_tile():
    return setts(face="2", joint="i")


# ------------------------------------------------------------ 성벽
WALL_TOP_ROWS = [
    "1111166666111116",   # 0 성가퀴 윗면 빛 / 총안 사이 그늘(1)
    "1111165555111116",   # 1
    "1111165555111116",   # 2
    "KKKKK4444KKKKKK4",   # 3 성가퀴 밑동
    "3333333333333333",   # 4 턱
]


def ashlar(s, y0=5):
    """큰 마름돌 2단 (5~9, 10~14), 이음 엇갈림. 면 5 · 이음 3 · 돌 윗변 6(빛)."""
    s.rect(0, y0, T - 1, 14, C["5"])
    for (ya, yb), xs in (((y0, 9), (0,)), ((10, 14), (8,))):
        s.line(0, ya, T - 1, ya, C["6"])
        for x in xs:
            s.line(x, ya, x, yb, C["3"])
        s.line(0, yb, T - 1, yb, C["4"])
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def battlements(s):
    # 성가퀴: 3칸짜리 총안(x 0~4 · 10~14 는 뒤쪽 어둠 1, 5~9 와 15 는 성가퀴 돌)
    blit(s, WALL_TOP_ROWS)
    return s


def wall_face():
    s = new()
    battlements(s)
    ashlar(s)
    s.px(12, 12, C["4"]); s.px(13, 12, C["4"])                                 # 마름돌 닳은 자리
    return s


def wall_v1():
    """화살 구멍(세로 K 틈 + 빛 받은 테)."""
    s = wall_face()
    s.rect(6, 6, 9, 13, C["4"])
    s.line(7, 7, 7, 12, C["K"]); s.line(8, 7, 8, 12, C["K"])
    s.line(6, 6, 9, 6, C["6"]); s.line(6, 6, 6, 13, C["6"])
    return s


def wall_v2():
    """잔(盞) 제국 깃발: 성가퀴에서 늘어뜨린 포도주빛 천(d, 빛 e, 그늘 i) + 어두운 호박 잔 문양(S), 제비꼬리 끝.
    1회차: 작은 천 + 밝은 잔(B) 이 2배 화면에서 '등불' 로 읽혔다 → 천을 성벽 높이 전체로, 문양은 S."""
    s = wall_face()
    s.rect(4, 3, 11, 14, C["d"])
    s.line(4, 3, 11, 3, C["5"])                                                # 걸이 막대
    s.line(4, 4, 4, 14, C["e"]); s.line(11, 4, 11, 14, C["i"])
    s.px(7, 14, C["5"]); s.px(8, 14, C["5"]); s.px(7, 13, C["i"]); s.px(8, 13, C["i"])   # 제비꼬리 홈
    blit(s, ["SSSS", ".SS.", "..S.", ".SS."], 6, 6)
    s.px(6, 6, C["S"]); s.px(9, 6, C["S"]); s.px(7, 8, C["S"]); s.px(8, 8, C["S"])
    return s


def wall_top():
    """성문 앞 길가 둔덕(위에서): 2회차 — 성벽 위 돌판(회색)으로 사방을 두르니 '돌 방' 이 됐다. 성벽은 북쪽 정면에만 있고,
    나머지 변은 해자 쪽으로 무너진 **흙 둔덕 + 성벽에서 굴러온 돌**(토러스 높이장, 이음새 없음)."""
    s = K.new()
    K.relief(s, [(4, 3, 5, 1.0), (12, 6, 5.5, 1.1), (6, 12, 5, 0.9), (13, 13, 3.5, 0.6)], "d", "e", "i", t=0.16)
    for x, y, w in ((2, 6, 4), (10, 11, 3)):
        s.line(x, y, x + w - 1, y, C["5"]); s.line(x, y + 1, x + w - 1, y + 1, C["4"]); s.line(x, y + 2, x + w - 1, y + 2, C["i"])
    return s


def void_tile():
    """원경: 성벽 아래 해자 — 검은 물(1) 위 가로 물결(2, 길이 다르게) · 깊은 곳 K."""
    s = K.fill("1")
    for y, segs in ((1, [(2, 5), (11, 13)]), (5, [(6, 10)]), (9, [(0, 2), (12, 15)]), (13, [(4, 8)])):
        for x0, x1 in segs:
            s.line(x0, y, x1, y, C["3"])
    for y, segs in ((3, [(8, 12)]), (11, [(5, 9)]), (15, [(0, 3), (13, 15)])):
        for x0, x1 in segs:
            s.line(x0, y, x1, y, C["K"])
    return s


# ------------------------------------------------------------ 문 (내리닫이 쇠창살)
def gate_frame(s):
    s.rect(0, 0, 2, T - 1, C["5"]); s.line(0, 0, 0, T - 1, C["6"]); s.line(2, 0, 2, T - 1, C["3"])
    s.rect(13, 0, 15, T - 1, C["5"]); s.line(13, 0, 13, T - 1, C["6"]); s.line(15, 0, 15, T - 1, C["3"])
    s.rect(0, 0, T - 1, 1, C["5"]); s.line(0, 0, T - 1, 0, C["6"]); s.line(3, 1, 12, 1, C["K"])


def door_open():
    s = setts(face="1", joint="K")
    gate_frame(s)
    for x in (4, 7, 10):                                                      # 들어 올린 창살 이빨
        s.line(x, 2, x, 3, C["5"]); s.px(x, 4, C["6"])
    s.line(3, 2, 12, 2, C["4"])
    return s


def door_closed():
    s = K.fill("K")
    gate_frame(s)
    for x in (4, 7, 10):
        s.line(x, 2, x, 14, C["5"]); s.line(x + 1, 2, x + 1, 14, C["3"])
        s.px(x, 15, C["6"])
    for y in (5, 10):
        s.line(3, y, 12, y, C["4"]); s.line(3, y + 1, 12, y + 1, C["2"])
    return s


def door_locked():
    s = door_closed()
    s.rect(6, 7, 9, 9, C["7"]); s.line(6, 7, 9, 7, C["9"]); s.px(7, 8, C["K"])
    s.line(3, 8, 5, 8, C["6"]); s.line(10, 8, 12, 8, C["6"])
    return s


# ------------------------------------------------------------ 출구 · 상점
def exit_tile():
    """출구 = 열린 성문 안에서 비치는 등불빛 돌길: 돌 d · 줄눈 i · 돌 윗변 e. 2x2 반복."""
    return setts(face="d", joint="i", lit="e")


def shop_tile():
    """성문 앞 통행세 탁자: 널빤지(4/3) 위 장부(9/7) · 동전 더미(B) · 도장(5). 2x2 반복."""
    s = K.fill("4")
    s.line(0, 0, T - 1, 0, C["3"]); s.line(0, 8, T - 1, 8, C["3"]); s.line(0, 15, T - 1, 15, C["2"])
    s.rect(2, 2, 7, 6, C["9"]); s.line(2, 6, 7, 6, C["7"]); s.line(4, 2, 4, 6, C["7"])
    s.line(3, 3, 3, 3, C["7"]); s.line(5, 4, 6, 4, C["7"])
    for x, y in ((10, 4), (12, 5)):
        s.line(x, y, x + 1, y, C["B"]); s.line(x, y + 1, x + 1, y + 1, C["S"]); s.px(x, y - 1, C["L"]) if x == 10 else None
    s.rect(4, 10, 5, 13, C["5"]); s.rect(3, 13, 6, 13, C["3"])
    s.px(10, 11, C["e"]); s.px(11, 11, C["e"]); s.px(11, 12, C["d"])
    return s


# ------------------------------------------------------------ 소품 8
def prop_barricade():
    """가시 말뚝 기둥(세움): 기둥 6/3 + 엇갈린 가로 가시 둘."""
    s = new()
    s.rect(7, 3, 8, 14, C["4"]); s.line(7, 3, 7, 14, C["6"]); s.line(8, 4, 8, 14, C["3"])
    s.px(7, 2, C["6"])
    for y, d in ((6, 1), (10, -1)):
        s.line(2, y + d, 13, y - d, C["5"]); s.line(2, y + d + 1, 13, y - d + 1, C["3"])
        s.px(2, y + d, C["7"]); s.px(13, y - d, C["7"])
    s.line(5, 15, 11, 15, C["1"])
    return s


def prop_crate():
    s = new()
    s.rect(2, 4, 13, 14, C["4"])
    s.line(2, 4, 13, 4, C["5"]); s.line(2, 4, 2, 14, C["5"])
    s.line(2, 9, 13, 9, C["3"]); s.line(7, 5, 7, 14, C["3"])
    s.line(3, 5, 6, 8, C["3"]); s.line(8, 10, 12, 13, C["3"])
    s.outline(C["K"], where="inside")
    s.line(3, 4, 12, 4, C["5"], only=C["K"])
    s.px(10, 6, C["e"]); s.px(11, 6, C["e"]); s.px(10, 7, C["e"])               # 잔 낙인(갈색)
    s.line(3, 15, 13, 15, C["1"])
    return s


def prop_brazier():
    """쇠 화로(세발): 불 L·W·B, 그릇 5/3, 다리 4. 성문 보초의 불."""
    s = new()
    s.line(4, 14, 6, 9, C["4"]); s.line(11, 14, 9, 9, C["4"]); s.line(8, 10, 8, 14, C["3"])
    s.rect(3, 7, 12, 9, C["5"]); s.line(3, 7, 12, 7, C["6"]); s.line(4, 9, 11, 9, C["3"])
    s.outline(C["K"], where="inside")
    blit(s, ["....L.....", "...LWL.L..", "..BLWWLB..", "..SBLLBS..", "...SBBS..."], 3, 2)
    s.line(5, 15, 11, 15, C["1"])
    return s


def prop_wheel():
    """쓰러진 수레바퀴(바닥에 누움): 타원 테 5/3 · 바퀴살 4 · 통 6."""
    s = new()
    for y in range(5, 14):
        for x in range(1, 15):
            d = ((x - 7.5) / 6.5) ** 2 + ((y - 9.5) / 4.0) ** 2
            if 0.62 <= d <= 1.0:
                s.px(x, y, C["5"] if y < 9.5 else C["3"])
    for x0, y0, x1, y1 in ((7, 9, 7, 6), (8, 10, 12, 11), (7, 10, 3, 11), (8, 9, 11, 7), (7, 10, 6, 12)):
        s.line(x0, y0, x1, y1, C["4"])
    s.rect(7, 9, 8, 10, C["6"])
    s.line(2, 14, 13, 14, C["1"])
    return s


def prop_rubble():
    """떨어진 마름돌 두 덩이(성벽에서 깨져 나옴)."""
    s = new()
    for x, y, w, h in ((2, 7, 6, 5), (8, 10, 5, 4)):
        s.rect(x, y, x + w - 1, y + h - 1, C["4"])
        s.line(x, y, x + w - 1, y, C["6"]); s.line(x, y, x, y + h - 1, C["5"])
        s.line(x + w - 1, y + 1, x + w - 1, y + h - 1, C["3"])
    s.outline(C["K"], where="inside")
    s.line(3, 7, 6, 7, C["6"], only=C["K"])
    s.px(11, 7, C["4"]); s.px(12, 8, C["3"]); s.px(1, 13, C["4"])
    s.line(2, 14, 7, 14, C["1"])
    return s


def prop_sack():
    s = new()
    blit(s, ["....77.....", "...7997....", "....44.....", "..777777...", ".7999999T..", ".79999997..", ".79999977..", "..777777..."], 3, 5)
    s.outline(C["K"], where="inside")
    s.px(6, 5, C["9"]); s.px(7, 5, C["9"])
    s.line(4, 13, 11, 13, C["1"])
    return s


def prop_puddle():
    """빗물 웅덩이(통과): 젖은 테 2 · 물 1 · 깊은 곳 K · 하늘빛 반사 4 한 줄. (1회차: K 덩어리가 석탄 더미로 읽힘 → 테를 밝게, 반사를 안쪽에)"""
    s = new()
    blob(s, 8, 9, 5.4, "2", seed=8, squash=0.5, lo=0, hi=15)
    blob(s, 8, 9, 4.2, "1", seed=9, squash=0.5)
    blob(s, 8.5, 9.5, 2.2, "K", seed=10, squash=0.5)
    s.line(5, 9, 7, 9, C["4"]); s.px(10, 10, C["3"])
    return s


def prop_notice():
    """방(榜) 붙인 나무판: 기둥 둘 + 판 d + 종이 C/9 + 수배 그림 2."""
    s = new()
    s.line(3, 4, 3, 14, C["4"]); s.line(12, 4, 12, 14, C["4"])
    s.rect(2, 3, 13, 10, C["d"]); s.line(2, 3, 13, 3, C["e"])
    s.rect(4, 5, 7, 9, C["C"]); s.line(4, 9, 7, 9, C["9"]); s.rect(5, 6, 6, 7, C["2"])
    s.rect(9, 4, 11, 7, C["9"]); s.line(9, 6, 11, 6, C["7"])
    s.outline(C["K"], where="inside")
    s.line(3, 3, 12, 3, C["e"], only=C["K"])
    s.line(2, 15, 13, 15, C["1"])
    return s


def tiles():
    return (
        [("floor_%d" % i, common_floor(i)) for i in range(4)]
        + [("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
           ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
           ("exit", exit_tile()), ("shop", shop_tile()),
           ("prop_barricade", prop_barricade()), ("prop_crate", prop_crate()), ("prop_brazier", prop_brazier()),
           ("prop_wheel", prop_wheel()), ("prop_rubble", prop_rubble()), ("prop_sack", prop_sack()),
           ("prop_puddle", prop_puddle()), ("prop_notice", prop_notice()),
           ("wall_v1", wall_v1()), ("wall_v2", wall_v2())]
        + [("start_%d" % i, start_floor(i)) for i in range(4)]
        + [("trial_%d" % i, trial_floor(i)) for i in range(4)]
        + [("rest_%d" % i, rest_floor(i)) for i in range(4)]
        + [("boss_%d" % i, boss_floor(i)) for i in range(4)]
        + [("reserve", new())]
    )


PROPS = [("barricade_post", True, 2, 0.6), ("crate", True, 2, 0.8), ("brazier", True, 1, 0.6), ("cart_wheel", False, 2, 0.7),
         ("rubble", False, 3, 1.0), ("sack", True, 2, 0.8), ("puddle", False, 2, 0.8), ("notice_board", True, 1, 0.4)]
