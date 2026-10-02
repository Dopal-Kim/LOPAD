#!/usr/bin/env python3
"""LOPAD 4층 '계(契)' 용병 제국 타일셋 (16x16) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage4/build.py
입력: parts/art/palette/lopad.json (무채 16 + 4층 황토 램프), assets/sprites/player/player_idle.png
산출: assets/tiles/stage4.png / stage4.json (1층과 같은 레이아웃·인덱스 표, tilecommon.py 참조)
      parts/art/work/tiles_stage4/preview.png · preview_room.png · preview_seam.png

컨셉 (story text-pack B4·D4, world-bible 3~4층 전선): 화승총 연기 너머로 계약서가 나부낀다. 깃발은 그걸로 충분하다.
  바닥 = 야영지 땅(돌 + 진흙) + 흩날린 계약서 / 복도 = 보급 마차 바퀴 자국 / 벽 = 모래주머니 / 벽 윗면 = 말뚝 울타리
  문 = 모래주머니 사이 나무 문 (열림 / 닫힘: X 버팀 / 잠김: 사슬 + 계약 봉인)
  소품 = 화승총 거치대·계약서 뭉치·깃발(황토)·모닥불 자국
색 예산: 무채 10 (G00~G07, G09, G12) + 강조 4 (19 shadow1, 21 base, 23 light1, 25 glow).
황토는 깃발·봉인(밀랍)·모닥불 잉걸·계단 빛에만.
바닥 명도 대역은 1층과 동일 (본색 G04, 진흙 G03, 돌 G05, 그늘 G02).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon as tc  # noqa: E402

G = tc.G
A = tc.ramp(4)
T = tc.T

C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
    "S": A[3],   # 19 shadow1 — 깃발 그늘·밀랍 그늘
    "B": A[5],   # 21 base   — 깃발 본색·밀랍 봉인·잉걸
    "L": A[7],   # 23 light1 — 깃발 빛·잉걸 빛·계단 빛
    "W": A[9],   # 25 glow   — 잉걸 심
}
ctx = tc.Ctx(C)
new, blit = ctx.new, ctx.blit


# ============================================================ 바닥 (야영지 땅: 돌 + 진흙)
def stone(s, x, y, w=3):
    """박힌 돌: 윗면 G05 (w px), 아랫줄 G03 그늘."""
    s.line(x, y, x + w - 1, y, C["5"])
    s.line(x + 1, y + 1, x + w - 1, y + 1, C["3"]) if w > 2 else s.px(x + 1, y + 1, C["3"])


def paper(s, x, y, lines=2):
    """흩날린 계약서 3x4: 종이 G07 (좌상단 G09 1px — 바닥 위에서 조용히), 글줄 G03, 우·하 그늘 G02."""
    s.rect(x, y, x + 2, y + 3, C["7"])
    s.px(x, y, C["9"])
    for i in range(lines):
        s.px(x + 1, y + 1 + i, C["3"])
    s.line(x, y + 4, x + 3, y + 4, C["2"]); s.line(x + 3, y, x + 3, y + 4, C["2"])


def ground(mud=(), stones=(), extra=None):
    """G04 바탕 위 진흙 덩어리(G03)·돌. 가장자리는 바탕색 유지 → 어떤 조합도 이어진다."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    for blob in mud:
        for y, (x0, x1) in blob.items():
            s.line(x0, y, x1, y, C["3"])
    for st in stones:
        stone(s, *st)
    if extra:
        extra(s)
    return s


def floor_0():
    return ground(
        mud=[{3: (9, 12), 4: (8, 13), 5: (9, 12)}, {11: (2, 5), 12: (1, 6), 13: (3, 5)}],
        stones=[(3, 3, 3), (12, 9, 2), (8, 13, 3)],
    )


def floor_1():
    return ground(
        mud=[{6: (3, 6), 7: (2, 7), 8: (3, 6)}],
        stones=[(10, 2, 2), (13, 12, 2)],
        extra=lambda s: paper(s, 9, 6),
    )


def floor_2():
    """자갈 깔린 자리 + 진흙."""
    return ground(
        mud=[{10: (8, 12), 11: (7, 13), 12: (8, 12), 13: (9, 11)}],
        stones=[(2, 2, 3), (6, 3, 2), (3, 6, 2), (9, 2, 3), (6, 7, 3), (12, 5, 2), (2, 12, 3)],
    )


def floor_3():
    """계약서 한 장 (진흙에 반쯤) + 돌."""
    def papers(s):
        paper(s, 10, 10, lines=1)
        s.px(12, 13, C["3"]); s.px(11, 13, C["3"])  # 진흙에 묻힌 모서리
    return ground(
        mud=[{12: (8, 13), 13: (7, 14), 14: (9, 12)}],
        stones=[(11, 4, 3), (5, 11, 2)],
        extra=papers,
    )


FLOORS = [floor_0(), floor_1(), floor_2(), floor_3()]


# ============================================================ 복도 (보급 마차 바퀴 자국)
def corridor_tile():
    """진흙길 G03. 바퀴 자국 2줄(G02, x3·x12 세로로 이어짐) + 자국 가장자리 G04 둔덕 + 발굽 자국."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    for x in (3, 12):
        s.line(x, 0, x, T - 1, C["2"])
        s.line(x - 1, 0, x - 1, T - 1, C["4"])
        s.line(x + 1, 0, x + 1, T - 1, C["2"])
    s.px(7, 4, C["2"]); s.px(8, 4, C["2"]); s.px(7, 11, C["2"]); s.px(8, 11, C["2"])  # 발굽
    s.px(6, 8, C["4"]); s.px(9, 14, C["4"]); s.px(0, 6, C["4"]); s.px(15, 12, C["4"])
    return s


# ============================================================ 벽
def sandbag_row(s, y, off, body="1", hi="2"):
    """모래주머니 한 줄(4px 높이): 8px 폭 자루가 off 만큼 어긋남. 틈 K, 윗면 빛 hi, 모서리 K 로 둥글림."""
    s.line(0, y, T - 1, y, C["K"])
    for x0 in range(off - 8, T, 8):
        x1 = x0 + 7
        for yy in range(y + 1, y + 4):
            s.line(max(x0, 0), yy, min(x1, T - 1), yy, C[body])
        if 0 <= x0 + 1 <= T - 1:
            s.line(max(x0 + 1, 0), y + 1, min(x1 - 1, T - 1), y + 1, C[hi])
        for x in (x0, x1):
            if 0 <= x < T:
                s.px(x, y + 1, C["K"]); s.px(x, y + 3, C["K"])
                s.px(x, y + 2, C["K"])


def wall_face():
    """모래주머니 벽: 4단, 반 칸 어긋남. 자루 G01, 윗면 빛 G02, 틈 K. 아랫단 K 그늘."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["K"])
    for i in range(4):
        sandbag_row(s, i * 4, 0 if i % 2 == 0 else 4)
    # 터진 자루에서 모래 흘러내림 (G02 점 몇 개)
    s.px(10, 10, C["2"]); s.px(10, 11, C["2"]); s.px(11, 12, C["2"])
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_top():
    """벽 윗면: 말뚝 울타리를 위에서 본 것. 땅 G01, 가로대 G02 2줄, 말뚝 머리(2x4 G03, 윗변 G04) 4px 간격."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.line(0, 0, T - 1, 0, C["K"])
    s.rect(0, 7, T - 1, 8, C["2"])
    for x in (1, 5, 9, 13):
        s.rect(x, 6, x + 1, 9, C["3"]); s.px(x, 6, C["4"]); s.px(x + 1, 6, C["4"])
    s.px(4, 3, C["2"]); s.px(12, 13, C["2"]); s.px(13, 13, C["2"])  # 돌
    return s


# ============================================================ 문 (나무 기둥 틀)
def door_frame(s):
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["3"]); s.line(0, 0, 0, T - 1, C["K"]); s.line(1, 0, 1, T - 1, C["4"])
    s.rect(13, 0, 15, T - 1, C["3"]); s.line(15, 0, 15, T - 1, C["K"]); s.line(13, 0, 13, T - 1, C["2"])
    s.rect(0, 0, T - 1, 1, C["3"]); s.line(0, 0, T - 1, 0, C["K"]); s.line(3, 1, 12, 1, C["4"])


def door_open():
    """열린 문: 틀 안으로 바퀴 자국 길이 이어진다. 문짝은 왼쪽에 젖혀져 2px."""
    s = new()
    door_frame(s)
    s.rect(3, 2, 12, 15, C["3"])
    for x in (5, 10):
        s.line(x, 2, x, 15, C["2"]); s.line(x - 1, 2, x - 1, 15, C["4"]); s.line(x + 1, 2, x + 1, 15, C["2"])
    s.rect(3, 2, 4, 14, C["5"]); s.line(4, 2, 4, 14, C["4"])
    s.px(3, 5, C["7"]); s.px(3, 12, C["7"]); s.px(4, 5, C["6"]); s.px(4, 12, C["6"])
    s.line(3, 15, 4, 15, C["2"])
    return s


def gate(s):
    """나무 문짝: 가로 널 G04 4장 + X 버팀대 G05. 틈 G02."""
    s.rect(3, 2, 12, 15, C["4"])
    for y in (5, 9, 13):
        s.line(3, y, 12, y, C["2"])
        s.line(3, y + 1, 12, y + 1, C["5"])
    s.line(3, 2, 12, 2, C["5"])
    s.line(3, 3, 12, 12, C["5"]); s.line(3, 12, 12, 3, C["5"])
    s.line(4, 3, 12, 11, C["3"], only=C["4"]); s.line(4, 12, 12, 4, C["3"], only=C["4"])


def door_closed():
    s = new()
    door_frame(s)
    gate(s)
    s.px(10, 8, C["7"]); s.px(10, 9, C["K"])   # 손잡이
    return s


def door_locked():
    """잠긴 문(보스 방): 문짝 + 가로 쇠사슬 + 계약서(G09)에 찍힌 밀랍 봉인(B/S, 4px)."""
    s = new()
    door_frame(s)
    gate(s)
    for x in range(2, 14):
        s.px(x, 7, C["7"] if x % 2 == 0 else C["6"])
    s.px(2, 8, C["5"]); s.px(13, 8, C["5"])
    s.rect(6, 8, 9, 12, C["9"]); s.px(6, 8, C["C"]); s.line(6, 13, 10, 13, C["2"]); s.line(10, 8, 10, 13, C["2"])
    s.px(7, 9, C["3"]); s.px(8, 9, C["3"])
    s.px(7, 11, C["B"]); s.px(8, 11, C["B"]); s.px(7, 12, C["B"]); s.px(8, 12, C["S"])
    return s


# ============================================================ 출구 · 상점 (2x2)
def exit_stairs():
    """올라가는 돌계단 4단 (1층과 같은 구조). 위에서 비껴드는 황토빛 2px x2."""
    s = new()
    body = ["5", "5", "4", "4"]
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["7"])
        s.rect(0, y + 2, T - 1, y + 3, C[body[i]])
        s.line(0, y + 3, T - 1, y + 3, C["3"] if i >= 2 else C["4"])
        if i in (0, 2):
            s.px(12, y + 1, C["L"]); s.px(13, y + 1, C["L"])
    for x, y in [(3, 2), (9, 6), (6, 10), (14, 14)]:
        s.px(x, y, C["3"])
    return s


def shop_counter():
    """종군 상인 좌판: 널 탁자 위 화승총 1정(가로), 계약서 묶음(봉인 B), 화약 뿔(G06). 2x2 로 깔면 좌판 4칸."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["2"])
        s.line(0, y + 1, T - 1, y + 1, C["5"])
    s.line(0, 15, T - 1, 15, C["2"])
    # 화승총: 총신 G07 (x1..10, y3), 개머리판 G05 (x10..14, y3..5), 그늘 G02
    s.line(1, 3, 10, 3, C["7"]); s.line(1, 4, 10, 4, C["2"])
    s.rect(10, 3, 14, 4, C["5"]); s.px(13, 5, C["5"]); s.px(14, 5, C["5"]); s.line(10, 5, 12, 5, C["2"]); s.px(13, 6, C["2"]); s.px(14, 6, C["2"])
    s.px(9, 2, C["6"])  # 화승 걸쇠
    # 계약서 묶음 (x2..6, y8..12) + 봉인
    s.rect(2, 8, 6, 12, C["9"]); s.line(2, 8, 6, 8, C["C"]); s.line(2, 13, 7, 13, C["2"]); s.line(7, 8, 7, 13, C["2"])
    s.px(3, 10, C["3"]); s.px(4, 10, C["3"])
    s.px(5, 11, C["B"]); s.px(5, 12, C["S"])
    # 화약 뿔 (x9..13, y9..12)
    s.line(9, 11, 13, 9, C["6"]); s.line(9, 12, 13, 10, C["6"]); s.px(13, 9, C["7"]); s.px(9, 12, C["5"]); s.px(10, 12, C["5"])
    s.line(10, 13, 13, 11, C["2"])
    return s


# ============================================================ 소품 (투명 배경)
def prop_musket_rack():
    """화승총 거치대(solid): 기둥 2개 + 가로대, 세워 둔 화승총 3정 (총신 G07 1px — 셀아웃 제외, 개머리판 G05)."""
    s = new()
    s.rect(2, 5, 13, 6, C["5"]); s.line(2, 6, 13, 6, C["4"])   # 가로대
    s.line(2, 7, 2, 14, C["4"]); s.line(3, 7, 3, 14, C["5"])   # 왼 기둥
    s.line(12, 7, 12, 14, C["4"]); s.line(13, 7, 13, 14, C["3"])
    s.rect(1, 15, 14, 15, C["3"])
    s.outline(C["K"], where="inside")
    s.rect(1, 15, 14, 15, C["3"]); s.line(3, 5, 12, 5, C["5"], only=C["K"])
    # 화승총 3정 (셀아웃 뒤에 그린다 = keep)
    for x in (5, 8, 11):
        s.line(x, 1, x, 11, C["7"])             # 총신
        s.px(x, 2, C["9"])                      # 총구 빛
        s.rect(x - 1, 11, x, 14, C["5"])        # 개머리판
        s.px(x, 14, C["4"]); s.px(x - 1, 14, C["4"])
        s.px(x + 1, 7, C["6"])                  # 화승 걸쇠
    return s


def prop_contracts():
    """계약서 뭉치(통과 가능): 쌓인 종이(G09, 윗장 G12) + 끈(K) + 봉인(B/S) + 흩날린 낱장 2."""
    s = new()
    s.rect(4, 6, 10, 11, C["9"]); s.line(4, 6, 10, 6, C["C"]); s.line(4, 7, 4, 11, C["C"])
    s.line(5, 12, 11, 12, C["3"]); s.line(11, 7, 11, 12, C["3"])
    s.line(4, 9, 10, 9, C["K"])                                 # 끈 (가로 한 줄)
    s.px(9, 7, C["B"]); s.px(9, 8, C["S"])                     # 봉인
    s.px(5, 8, C["3"]); s.px(5, 10, C["3"])                    # 글줄
    # 낱장 2 (오른쪽 위로 날림, 왼쪽 아래)
    s.rect(11, 2, 13, 4, C["9"]); s.px(11, 2, C["C"]); s.px(12, 3, C["3"]); s.px(14, 3, C["2"]); s.px(14, 4, C["2"]); s.line(11, 5, 14, 5, C["2"])
    s.rect(1, 12, 3, 13, C["9"]); s.px(2, 13, C["3"]); s.line(1, 14, 4, 14, C["2"]); s.px(4, 13, C["2"])
    s.outline(C["K"], where="inside")
    s.rect(11, 2, 13, 4, C["9"]); s.px(11, 2, C["C"]); s.px(12, 3, C["3"]); s.px(14, 3, C["2"]); s.px(14, 4, C["2"]); s.line(11, 5, 14, 5, C["2"])
    s.rect(1, 12, 3, 13, C["9"]); s.px(2, 13, C["3"]); s.line(1, 14, 4, 14, C["2"]); s.px(4, 13, C["2"])
    s.line(5, 6, 9, 6, C["C"], only=C["K"])
    s.line(5, 12, 11, 12, C["3"]); s.line(11, 7, 11, 12, C["3"])
    return s


def prop_flag():
    """깃발(solid): 장대(G05/G04)에 황토 깃발(B 본색, 윗변 L, 아랫단·주름 S). 계약서 문장 대신 K 줄 하나. 황토 ~30px."""
    s = new()
    s.line(3, 1, 3, 13, C["5"]); s.line(4, 1, 4, 13, C["4"])
    s.px(3, 0, C["7"]); s.px(4, 0, C["7"])
    s.rect(2, 14, 5, 14, C["4"]); s.rect(1, 15, 6, 15, C["3"])  # 흙더미 받침
    # 깃발 (x5..13): 바람에 오른쪽으로 펄럭임
    rows = {2: (5, 12), 3: (5, 13), 4: (5, 13), 5: (5, 12), 6: (5, 11), 7: (5, 12), 8: (5, 10)}
    for y, (x0, x1) in rows.items():
        s.line(x0, y, x1, y, C["B"])
    s.line(5, 2, 12, 2, C["L"])
    s.line(6, 8, 10, 8, C["S"]); s.px(12, 7, C["S"]); s.px(11, 6, C["S"]); s.px(13, 4, C["S"])
    s.line(7, 4, 10, 4, C["K"]); s.line(7, 6, 9, 6, C["K"])   # 계약 문장(글줄)
    s.outline(C["K"], where="inside")
    s.px(3, 0, C["7"]); s.px(4, 0, C["7"])
    s.line(5, 2, 12, 2, C["L"], only=C["K"])
    s.line(2, 14, 5, 14, C["4"], only=C["K"]); s.line(1, 15, 6, 15, C["3"], only=C["K"])
    return s


def prop_firepit():
    """모닥불 자국(통과 가능): 돌 테(G05/G06) 안에 숯(K/G01)·재(G07), 잉걸 B/L/W 4px."""
    s = new()
    ring = [(5, 3), (6, 3), (8, 3), (9, 3), (3, 5), (3, 6), (12, 5), (12, 6), (2, 8), (2, 9), (13, 8), (13, 9),
            (3, 11), (4, 12), (11, 12), (12, 11), (6, 13), (7, 13), (9, 13)]
    s.rect(3, 4, 12, 12, C["1"])
    s.rect(4, 4, 11, 4, C["1"]); s.rect(3, 13, 12, 13, C["1"])
    inner = {5: (5, 10), 6: (4, 11), 7: (4, 11), 8: (4, 11), 9: (4, 11), 10: (5, 10), 11: (6, 9)}
    for y, (x0, x1) in inner.items():
        s.line(x0, y, x1, y, C["K"])
    s.rect(6, 7, 9, 9, C["7"]); s.px(5, 8, C["7"]); s.px(10, 8, C["7"])   # 재
    s.px(6, 8, C["1"]); s.px(9, 9, C["1"])
    s.px(7, 8, C["B"]); s.px(8, 8, C["L"]); s.px(8, 7, C["B"]); s.px(7, 9, C["W"])  # 잉걸
    for x, y in ring:
        s.px(x, y, C["5"])
    for x, y in [(6, 3), (9, 3), (3, 6), (12, 6), (2, 9), (13, 9), (4, 12), (11, 12), (7, 13)]:
        s.px(x, y, C["6"])
    s.px(4, 3, C["5"]); s.px(10, 3, C["5"]); s.px(11, 3, C["5"]); s.px(5, 13, C["5"]); s.px(10, 13, C["5"]); s.px(11, 13, C["5"])
    s.px(2, 7, C["5"]); s.px(13, 7, C["5"]); s.px(2, 10, C["5"]); s.px(13, 10, C["5"])
    s.px(3, 4, C["5"]); s.px(12, 4, C["5"]); s.px(3, 12, C["5"]); s.px(12, 12, C["5"])
    return s


def void_tile():
    return new()


TILES = [
    ("floor_0", FLOORS[0]), ("floor_1", FLOORS[1]), ("floor_2", FLOORS[2]), ("floor_3", FLOORS[3]),
    ("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
    ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
    ("exit", exit_stairs()), ("shop", shop_counter()),
    ("prop_musket_rack", prop_musket_rack()), ("prop_contracts", prop_contracts()), ("prop_flag", prop_flag()),
    ("prop_firepit", prop_firepit()),
]
PROPS = [("musket_rack", True), ("contract_bundle", False), ("flag", True), ("firepit", False)]

if __name__ == "__main__":
    tc.run(4, "계(契) — 용병 제국 전선", TILES, PROPS, [19, 21, 23, 25], HERE)
