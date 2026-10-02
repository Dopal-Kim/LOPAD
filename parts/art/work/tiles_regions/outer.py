#!/usr/bin/env python3
"""outer — 외곽 거리 (술 제국 '잔' 의 외곽 뒷골목). 바닥은 v4 판석 결 그대로(tiles_v4/stage1.py 재사용),
경계는 **반목조 집 앞면**(북) · **지붕 처마**(윗면) · **멀리 이어진 지붕들**(void) — 골목 광장 위로 하늘이 트였다.
문·상점·소품은 v4 그대로(뒷골목의 나무 문·술 좌판·술통·깨진 병…). 출구 = 등불이 비친 판석 길(계단 아님)."""
import rkit as K
import stage1 as v4
from rkit import C, T, blit, new

NAME = "잔(盞) — 외곽 거리"


# ------------------------------------------------------------ 바닥 (v4 재사용 + start 만 골목 흙)
def start_floor(i):
    """외곽 거리의 여정·시작 칸: 판석 줄눈에 흙이 쌓인 자리(흙 G01 → 줄눈이 두꺼워짐), 변형마다 다른 자리."""
    s = v4.lay(["full", "half", "tee", "ell"][i])
    spots = [[(3, 0), (4, 0), (5, 0), (4, 1)], [(0, 6), (0, 7), (1, 7), (0, 9)], [(8, 11), (8, 12), (9, 12), (7, 13)], [(11, 8), (12, 8), (13, 8), (12, 9)]]
    for x, y in spots[i]:
        s.px(x, y, C["1"])
    return s


# ------------------------------------------------------------ 집 앞면 (북 경계) · 지붕 (윗면·원경)
# 1회차 비평: 회벽 띠 16px 만으로는 '장식 띠' 로 읽혔고, 회색 기와 테두리는 돌 테처럼 보였다(방 안 느낌 그대로).
# → 집 앞면 맨 위에 **처마 기와(갈색)** 를 얹고, 윗면·원경을 **갈색 기와 지붕 경사**(16px 한 장 = 용마루→처마)로 바꿨다.
#    원경(void)은 같은 지붕을 한 단 어둡게 → 골목 둘레로 지붕들이 겹겹이 이어진다.
FACADE = [
    "eeeeeeeeeeeeeeee",   # 0 처마 기와 끝 (밝음)
    "dddidddidddidddi",                        # 1 기와 이음
    "iiiiiiiiiiiiiiii",   # 2 처마 끝 그늘
    "KKKKKKKKKKKKKKKK",   # 3 처마 밑 그늘
    "2222222222222222",   # 4 윗 도리
    "2244444442444444",   # 5
    "2244444442444444",   # 6
    "2244444442444444",   # 7
    "2244444442444444",   # 8
    "2244444442444444",   # 9
    "2222222222222222",   # 10 문지방 도리
    "3333332333333323",   # 11 돌 기단
    "3333332333333323",   # 12
    "2222222222222222",   # 13 기단 줄눈
    "3332333333332333",   # 14
    "KKKKKKKKKKKKKKKK",   # 15 땅에 닿는 그늘
]


def facade(brace=True):
    s = new()
    blit(s, FACADE)
    if brace:
        s.line(2, 9, 6, 5, C["2"])              # 왼쪽 칸 버팀목 (반목조)
        s.line(3, 9, 7, 5, C["3"])
    return s


def wall_face():
    s = facade()
    s.px(12, 7, C["3"]); s.px(13, 8, C["3"])     # 회벽 실금 2px
    return s


def wall_v1():
    """덧창 닫힌 창 — 덧창 틈으로 새는 등불 한 줄(S) + 한 점(B). 사람이 사는 거리."""
    s = facade(brace=True)
    s.rect(10, 5, 14, 9, C["2"])
    s.rect(11, 6, 11, 9, C["3"]); s.rect(13, 6, 13, 9, C["3"])
    s.line(12, 6, 12, 9, C["S"]); s.px(12, 7, C["B"])
    return s


def wall_v2():
    """나무 문 + 매달린 선술집 간판(잔 모양). 문은 기단을 끊고 땅까지."""
    s = facade(brace=False)
    s.rect(2, 5, 7, 14, C["3"])
    s.line(2, 5, 7, 5, C["2"]); s.line(2, 5, 2, 14, C["2"]); s.line(7, 5, 7, 14, C["1"])
    s.line(4, 6, 4, 14, C["2"])
    s.px(6, 10, C["6"])                          # 손잡이
    s.line(2, 15, 7, 15, C["K"])
    # 간판: 쇠 팔 + 나무판(d) + 잔 문양(i)
    s.line(10, 5, 14, 5, C["5"])
    s.px(11, 6, C["4"]); s.px(14, 6, C["4"])
    s.rect(11, 7, 14, 10, C["d"]); s.line(11, 7, 14, 7, C["e"])
    s.px(12, 8, C["i"]); s.px(13, 8, C["i"]); s.px(12, 9, C["i"]); s.px(12, 10, C["i"])
    return s


def roof(ridge, faces, seam, eave):
    """지붕 경사 한 장: y0 용마루(ridge) → 3px 기와 줄 5개(faces[r], 이음·아랫변 seam, 줄마다 2px 엇갈림) → y15 처마 그늘(eave).
    세로로 이어 붙이면 지붕이 겹겹이, 가로로는 이음새 없음. 결이 가로라 void 반복에서도 점 격자가 서지 않는다."""
    s = new()
    s.line(0, 0, T - 1, 0, C[ridge])
    for r in range(5):
        y0 = 1 + r * 3
        s.rect(0, y0, T - 1, y0 + 1, C[faces[r]])
        s.line(0, y0 + 2, T - 1, y0 + 2, C[seam])
        off = (r % 2) * 2
        for x in range(off, T, 4):
            s.px(x, y0, C[seam]); s.px(x, y0 + 1, C[seam])
    s.line(0, T - 1, T - 1, T - 1, C[eave])
    return s


def wall_top():
    """가까운 지붕(처마): 갈색 기와 — 용마루 e, 기와 e→d, 이음 i, 처마 그늘 K."""
    return roof("e", ["e", "d", "d", "d", "d"], "i", "K")


def void_tile():
    """원경: 멀리 겹겹이 이어진 지붕들 — 가까운 지붕보다 두 단 어둡다(용마루 d, 기와 i, 이음 K)."""
    return roof("d", ["d", "i", "i", "i", "i"], "K", "K")


def exit_tile():
    """출구 = 등불이 비친 판석 길 (계단 대신 '앞으로 이어지는 길'): 판석 d · 줄눈 i · 빛 e. 2x2 반복."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["d"])
    s.line(0, 0, T - 1, 0, C["i"]); s.line(0, 0, 0, T - 1, C["i"])
    s.line(0, 8, T - 1, 8, C["i"]); s.line(8, 1, 8, 7, C["i"])
    s.line(1, 1, 7, 1, C["e"]); s.line(9, 1, 14, 1, C["e"]); s.line(1, 9, 13, 9, C["e"])
    s.px(5, 12, C["S"]); s.px(12, 4, C["S"])
    return s


def tiles():
    return (
        [("floor_%d" % i, v4.common_floor(i)) for i in range(4)]
        + [("corridor", v4.corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
           ("door_open", v4.door_open()), ("door_closed", v4.door_closed()), ("door_locked", v4.door_locked()),
           ("exit", exit_tile()), ("shop", v4.shop_counter()),
           ("prop_barrel", v4.prop_barrel()), ("prop_bottle", v4.prop_bottle()), ("prop_puddle", v4.prop_puddle()),
           ("prop_lantern", v4.prop_lantern()), ("prop_ash_pit", v4.prop_ash_pit()), ("prop_bottle_crate", v4.prop_bottle_crate()),
           ("prop_wine_jar", v4.prop_wine_jar()), ("prop_cup_pile", v4.prop_cup_pile()),
           ("wall_v1", wall_v1()), ("wall_v2", wall_v2())]
        + [("start_%d" % i, start_floor(i)) for i in range(4)]
        + [("trial_%d" % i, v4.trial_floor(i)) for i in range(4)]
        + [("rest_%d" % i, v4.rest_floor(i)) for i in range(4)]
        + [("boss_%d" % i, v4.boss_floor(i)) for i in range(4)]
        + [("reserve", new())]
    )


PROPS = list(v4.PROPS)
