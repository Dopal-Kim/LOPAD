#!/usr/bin/env python3
"""waste — 황무지·전장 (여정 노드: 탄생지·튜토리얼·버려진 길). 술 제국에 들어서기 전, 전투가 쓸고 간 맨땅.

바닥 = 메마른 흙(d) 평면 + 변형마다 다른 자리에 작은 흔적 하나(자갈·실금·그을음·군화 자국·부러진 화살대).
경계 = 흙 둔덕에 박힌 **목책 말뚝**(정면) · **흙 바구니(가비온)** · 반쯤 묻힌 **수레바퀴**, 윗면 = 돌과 흙덩이가 섞인 둔덕 꼭대기.
void = 멀리 펼쳐진 어두운 들판(가로 고랑 결). 문 = 목책 틈 / 가시 통나무 바리케이드. 출구 = 바퀴 자국 난 밝은 흙길(북쪽으로 뻗음).
"""
import rkit as K
from rkit import C, T, blit, blob, new, pebble

NAME = "잔(盞) — 황무지·전장"
GROUND, CRACK, LIT = "d", "i", "e"


def ground():
    return K.fill(GROUND)


# ------------------------------------------------------------ 바닥
def boot(s, x, y):
    """군화 자국 한 쌍 (i 2x3 + 뒤꿈치), 위로 걸어간 방향."""
    for dx, dy in ((0, 0), (3, 2)):
        s.rect(x + dx, y + dy, x + dx + 1, y + dy + 2, C[CRACK])
        s.px(x + dx, y + dy + 4, C[CRACK]); s.px(x + dx + 1, y + dy + 4, C[CRACK])


def common_floor(i):
    """2회차 비평: 변형 넷 모두에 흔적을 넣으면 25% 섞기에서 화면 전체가 같은 무늬로 덮였다 → 흔적은 넷 중 둘, 2~3px 만."""
    s = ground()
    if i == 0:
        pebble(s, 4, 5, top="5", body="4", shade=CRACK)
    elif i == 2:
        s.px(11, 4, C[LIT]); s.px(12, 3, C[LIT]); s.px(12, 5, C[CRACK])   # 마른 풀 한 포기
    return s


def start_floor(i):
    """탄생지·여정: 맨흙 + 작은 흔적(넷 중 둘). 군화 자국·화살·그을음 같은 '전장의 흔적' 은 소품(maxPerRoom)과
    battlefield_* 구조물이 맡는다 — 바닥 변형에 넣으면 화면에 수십 개씩 찍힌다(1회차)."""
    s = ground()
    if i == 1:
        s.line(9, 6, 11, 5, C[CRACK]); s.px(12, 5, C[CRACK])                   # 실금
    elif i == 3:
        s.px(5, 11, C["4"]); s.px(6, 11, C["3"]); s.px(6, 12, C[CRACK])        # 부서진 돌 조각
    return s


def trial_floor(i):
    s = ground()
    if i == 0:
        K.line(s, [(3, 4), (6, 5), (8, 4), (10, 6)], CRACK)                  # 갈라진 흙
    return s


def rest_floor(i):
    s = ground()
    if i == 1:
        s.px(6, 7, C[LIT]); s.px(7, 7, C[LIT]); s.px(6, 8, C[CRACK])
    return s


def boss_floor(i):
    s = ground()
    if i == 0:
        K.line(s, [(0, 9), (4, 8), (7, 10), (11, 9), (15, 11)], CRACK)
        s.px(7, 10, C["K"]); s.px(8, 10, C["K"]); s.px(7, 10, C["S"])      # 금 사이 잔불 1px
    elif i == 1:
        blob(s, 6, 6, 2.2, CRACK, seed=12, squash=0.7)
    return s


def corridor_tile():
    s = ground()
    s.line(4, 0, 4, T - 1, C[CRACK]); s.line(11, 0, 11, T - 1, C[CRACK])   # 바퀴 자국 (세로로 이어짐)
    return s


# ------------------------------------------------------------ 둔덕 (북 경계 정면)
def bank(s):
    """흙 둔덕 정면: 위 테 e(빛 받는 둔덕 꼭대기, 울퉁불퉁) · 면 d · 지층 i · 박힌 돌 · 발치 그늘."""
    s.rect(0, 0, T - 1, T - 1, C[GROUND])
    blit(s, ["i.ii..i...ii.i..",
             "eeeeeeeeeeeeeeee",
             "deeeddeeeedeeedd"])
    for x0, x1, y in ((1, 6, 7), (9, 14, 7), (3, 9, 11), (12, 15, 11)):
        s.line(x0, y, x1, y, C[CRACK])
    s.line(0, 14, T - 1, 14, C[CRACK]); s.line(0, 15, T - 1, 15, C["K"])
    return s


def stone(s, x, y, w=3):
    s.line(x, y, x + w - 1, y, C["5"]); s.line(x, y + 1, x + w - 1, y + 1, C["3"]); s.px(x + w - 1, y, C["4"])


def stake(s, x, top=1, bottom=13, lean=0):
    """말뚝 2px (빛 쪽 6, 그늘 3), 끝은 깎아 1px, 아래 흙에 박힌 그늘."""
    for y in range(top + 1, bottom + 1):
        dx = (lean * (bottom - y)) // max(1, bottom - top)
        s.px(x + dx, y, C["6"]); s.px(x + dx + 1, y, C["3"])
    dx = lean
    s.px(x + dx, top, C["6"])
    s.px(x + 2, bottom, C[CRACK])


def wall_face():
    s = bank(new())
    stake(s, 3, 0, 12); stake(s, 10, 1, 13, lean=1)
    stone(s, 6, 9)
    return s


def wall_v1():
    """흙 바구니(가비온): 엮은 나뭇가지 바구니에 흙을 채운 전장 방벽."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C[LIT])
    blit(s, ["i.ii..i...ii.i..", "dddeddddeddddedd", "dddddddddddddddd"])
    for x in (1, 5, 9, 13):
        s.line(x, 3, x, 14, C["3"])
    for y, off in ((5, 0), (8, 2), (11, 0)):
        for x in range(off, T, 4):
            s.line(x, y, min(T - 1, x + 1), y, C[GROUND])
    s.line(0, 14, T - 1, 14, C[CRACK]); s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_v2():
    """반쯤 묻힌 부서진 수레바퀴."""
    s = bank(new())
    cx, cy, r = 8, 9, 5
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if r - 1 <= d <= r + 0.3:
                s.px(x, y, C["5"] if (x - cx) + (y - cy) < 0 else C["3"])
    for (dx, dy) in ((0, -1), (1, 0), (-1, 1), (1, 1), (-1, -1)):
        for k in range(1, r - 1):
            s.px(cx + dx * k, cy + dy * k, C["4"])
    s.px(cx, cy, C["6"])
    s.rect(1, 12, 14, 13, C[GROUND]); s.line(2, 12, 13, 12, C[CRACK])   # 흙에 묻힘
    s.px(13, 5, C[GROUND]); s.px(12, 4, C[GROUND])                     # 빠진 바퀴살 자리
    return s


def wall_top():
    """둔덕 꼭대기(위에서 본 흙 무더기). 2회차: 돌 네 개 → '점선 돌 테', 3회차: 둥근 덩이 둘 → '구슬 꿴 테'.
    → 감아 도는(토러스) 높이장으로 흙덩이를 깔아 이음새·반복 테두리가 안 보이게. 빛 받는 면 e · 면 d · 그늘 i, 돌 하나."""
    s = K.new()
    K.relief(s, [(3, 4, 5, 1.0), (10, 2, 4, 0.8), (13, 10, 6, 1.1), (6, 12, 4.5, 0.9), (8, 7, 3, 0.6)], GROUND, LIT, CRACK, t=0.16)
    return s


def void_tile():
    """원경: 멀리 펼쳐진 어두운 들판 — 바탕 i, 가로 고랑 K(길이·자리 다르게). 가로 결만."""
    s = K.fill("i")
    for y, segs in ((2, [(0, 4), (8, 13)]), (6, [(3, 9), (12, 15)]), (10, [(0, 2), (6, 11)]), (14, [(2, 7), (10, 14)])):
        for x0, x1 in segs:
            s.line(x0, y, x1, y, C["K"])
    return s


# ------------------------------------------------------------ 문 (목책 틈)
def posts(s):
    for x in (0, 13):
        s.rect(x, 0, x + 2, T - 1, C["3"])
        s.line(x, 0, x, T - 1, C["6"]); s.line(x + 1, 0, x + 1, T - 1, C["4"]); s.line(x + 2, 0, x + 2, T - 1, C["K"])
        s.px(x + 1, 0, C["6"])


def door_open():
    s = ground()
    posts(s)
    boot(s, 6, 4)
    return s


def door_closed():
    """가시 통나무 바리케이드: 엇갈린 통나무 둘 + 가로 들보."""
    s = ground()
    posts(s)
    s.line(3, 3, 12, 13, C["5"]); s.line(3, 4, 11, 13, C["3"])
    s.line(12, 3, 3, 13, C["5"]); s.line(12, 4, 4, 13, C["3"])
    s.rect(3, 7, 12, 8, C["4"]); s.line(3, 7, 12, 7, C["6"])
    s.px(3, 2, C["7"]); s.px(12, 2, C["7"])                              # 깎은 끝
    s.line(3, 14, 12, 14, C[CRACK])
    return s


def door_locked():
    s = door_closed()
    s.line(3, 10, 12, 10, C["6"]); s.line(3, 11, 12, 11, C["4"])          # 쇠사슬
    s.rect(6, 9, 9, 12, C["7"]); s.line(6, 9, 9, 9, C["9"]); s.px(7, 10, C["K"]); s.px(7, 11, C["K"])
    return s


# ------------------------------------------------------------ 출구 · 상점
def exit_tile():
    """출구 = 북쪽으로 뻗은 밝은 흙길: 다져진 흙 e, 바퀴 자국 d(세로로 이어짐), 군화 자국 d. 2x2 반복 = 넓은 길목."""
    s = K.fill(LIT)
    s.line(3, 0, 3, T - 1, C[GROUND]); s.line(12, 0, 12, T - 1, C[GROUND])
    for dx, dy in ((0, 0), (3, 3)):
        s.rect(6 + dx, 3 + dy, 7 + dx, 5 + dy, C[GROUND])
    s.px(9, 12, C["5"]); s.px(10, 12, C["4"])
    return s


def shop_tile():
    """행상의 깔개: 줄무늬 천(6/4) 위 병·주머니·단도. 2x2 반복."""
    s = K.fill("6")
    s.line(0, 1, T - 1, 1, C["4"]); s.line(0, 14, T - 1, 14, C["4"])
    s.line(0, 0, T - 1, 0, C["3"]); s.line(0, 15, T - 1, 15, C["3"])
    s.rect(3, 4, 5, 11, C["7"]); s.rect(3, 4, 5, 5, C["4"]); s.rect(3, 7, 5, 10, C["B"]); s.line(5, 8, 5, 10, C["S"])
    s.line(3, 12, 5, 12, C["3"])
    s.rect(8, 7, 12, 11, C["e"]); s.line(9, 6, 11, 6, C["d"]); s.px(10, 5, C["d"]); s.line(8, 11, 12, 11, C["d"])
    s.px(9, 8, C["S"])
    s.line(9, 3, 13, 3, C["9"]); s.line(13, 3, 14, 3, C["3"]); s.line(9, 4, 13, 4, C["4"])
    return s


# ------------------------------------------------------------ 소품 8 (투명 배경)
def prop_spear():
    """부러진 장창 자루가 비스듬히 박힘 + 흙무더기. 가는 막대라 셀아웃 대신 손으로 명암 2단."""
    s = new()
    s.rect(4, 13, 9, 14, C[GROUND]); s.line(5, 12, 8, 12, C[LIT]); s.line(4, 15, 9, 15, C[CRACK])
    for k, y in enumerate(range(2, 13)):
        x = 9 - k * 3 // 10
        s.px(x, y, C["6"]); s.px(x + 1, y, C["3"])
    s.px(9, 1, C["7"]); s.px(10, 2, C["7"]); s.px(8, 2, C["5"])            # 쪼개진 끝
    s.line(11, 13, 14, 14, C[CRACK])                                          # 그림자
    return s


def prop_arrows():
    s = new()
    for (x, y, dx) in ((4, 6, -1), (8, 4, 0), (11, 7, 1)):
        for k in range(6):
            s.px(x + (dx * k) // 3, y + k, C["5"])
        s.px(x, y - 1, C["T"]); s.px(x - 1, y - 1, C["7"]); s.px(x + 1, y, C["7"])
        bx, by = x + (dx * 5) // 3, y + 6
        s.px(bx, by, C[CRACK]); s.px(bx + 1, by, C[CRACK])
    return s


def prop_helmet():
    """옆으로 쓰러진 투구: 둥근 몸 5/6(빛) · 오른쪽 챙 테 4 · 작은 안쪽 어둠 K · 볏 7. (1회차: 세워 두니 종, 2회차: 큰 K 구멍이 솥으로 읽힘)"""
    s = new()
    for y in range(5, 14):
        for x in range(2, 11):
            if (x - 6.5) ** 2 + (y - 9.5) ** 2 <= 16:
                s.px(x, y, C["5"])
    s.rect(4, 7, 6, 8, C["6"]); s.px(4, 7, C["7"])
    s.line(3, 6, 7, 5, C["7"])                                                  # 볏
    s.px(7, 11, C["3"]); s.px(8, 10, C["3"])                                    # 찌그러짐
    for y in range(4, 15):
        for x in range(9, 15):
            d = ((x - 11.5) / 2.4) ** 2 + ((y - 9.5) / 5.2) ** 2
            if d <= 1:
                s.px(x, y, C["4"] if d > 0.35 else C["2"])
    s.outline(C["K"], where="inside")
    s.line(12, 8, 12, 11, C["K"])
    s.line(3, 15, 13, 15, C[CRACK])
    return s


def prop_crater():
    """포탄 구덩이(통과) — 그을린 테 · 어두운 속 · 가운데 잔불(S/B/L). waste 의 '금 사이 잔불' 역할(방당 1)."""
    s = new()
    blob(s, 8, 9, 5.5, CRACK, seed=3, squash=0.7, lo=0, hi=15)
    blob(s, 8, 9.5, 3.4, "K", seed=5, squash=0.7)
    for x, y in ((3, 6), (4, 5), (5, 5), (6, 4), (9, 4), (10, 4)):
        s.px(x, y, C[LIT])
    s.px(8, 10, C["L"]); s.px(7, 10, C["B"]); s.px(9, 9, C["S"]); s.px(6, 11, C["S"])
    s.px(13, 12, C[LIT]); s.px(2, 12, C[LIT])
    return s


def prop_shield():
    """깨진 둥근 방패(나무 d·테 3·쇠 혹 6), 쪼개진 금 K."""
    s = new()
    for y in range(4, 14):
        for x in range(2, 15):
            if ((x - 8) / 6.2) ** 2 + ((y - 8.5) / 4.6) ** 2 <= 1:
                s.px(x, y, C["d"])
    s.outline(C["3"], where="inside")
    s.rect(7, 7, 9, 9, C["5"]); s.px(7, 7, C["6"])
    s.line(10, 5, 11, 8, C["K"]); s.line(11, 8, 10, 11, C["K"])
    s.line(4, 6, 6, 5, C["e"])
    s.line(3, 14, 13, 14, C[CRACK])
    return s


def prop_cannonball():
    s = new()
    s.line(1, 12, 6, 11, C[CRACK]); s.line(1, 13, 5, 12, C[CRACK])          # 굴러온 고랑
    for y in range(6, 14):
        for x in range(6, 14):
            if (x - 9.5) ** 2 + (y - 9.5) ** 2 <= 12.5:
                s.px(x, y, C["3"])
    s.rect(8, 7, 9, 8, C["5"]); s.px(8, 7, C["6"])
    s.outline(C["K"], where="inside")
    s.line(7, 14, 12, 14, C[CRACK])
    return s


def prop_stones():
    s = new()
    for x, y, w, h in ((2, 8, 4, 3), (8, 10, 3, 2), (10, 5, 4, 3)):
        s.rect(x, y, x + w - 1, y + h - 1, C["4"])
        s.line(x, y, x + w - 1, y, C["5"]); s.px(x, y, C["6"])
        s.line(x + w - 1, y + 1, x + w - 1, y + h - 1, C["3"])
        s.line(x, y + h, x + w - 1, y + h, C[CRACK])
    return s


def prop_bush():
    """말라 죽은 덤불: 가지 4/3 · 마른 잎 e · 밑동 그늘."""
    s = new()
    for pts in ([(8, 13), (5, 8), (3, 5)], [(8, 13), (7, 6), (8, 3)], [(8, 13), (11, 8), (13, 6)], [(8, 13), (10, 10), (12, 11)], [(8, 13), (5, 11), (3, 10)]):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            s.line(x0, y0, x1, y1, C["4"])
    for x, y in ((3, 5), (8, 3), (13, 6), (5, 8)):
        s.px(x, y, C["3"])
    for x, y in ((4, 6), (9, 4), (12, 7), (11, 10)):
        s.px(x, y, C[LIT])
    s.line(6, 14, 11, 14, C[CRACK])
    return s


def tiles():
    return (
        [("floor_%d" % i, common_floor(i)) for i in range(4)]
        + [("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
           ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
           ("exit", exit_tile()), ("shop", shop_tile()),
           ("prop_spear", prop_spear()), ("prop_arrows", prop_arrows()), ("prop_helmet", prop_helmet()),
           ("prop_crater", prop_crater()), ("prop_shield", prop_shield()), ("prop_cannonball", prop_cannonball()),
           ("prop_stones", prop_stones()), ("prop_bush", prop_bush()),
           ("wall_v1", wall_v1()), ("wall_v2", wall_v2())]
        + [("start_%d" % i, start_floor(i)) for i in range(4)]
        + [("trial_%d" % i, trial_floor(i)) for i in range(4)]
        + [("rest_%d" % i, rest_floor(i)) for i in range(4)]
        + [("boss_%d" % i, boss_floor(i)) for i in range(4)]
        + [("reserve", new())]
    )


# (short, solid, maxPerRoom, weight)
PROPS = [("broken_spear", True, 2, 0.8), ("arrows", False, 3, 1.0), ("helmet", False, 2, 0.7), ("crater", False, 1, 0.6),
         ("shield", False, 2, 0.7), ("cannonball", False, 2, 0.5), ("stones", False, 3, 1.0), ("dead_bush", False, 3, 0.9)]
