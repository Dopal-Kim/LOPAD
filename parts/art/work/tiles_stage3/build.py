#!/usr/bin/env python3
"""LOPAD 3층 '붕(繃)' 야전병원 제국 타일셋 (16x16) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage3/build.py
입력: parts/art/palette/lopad.json (무채 16 + 3층 청록 램프), assets/sprites/player/player_idle.png
산출: assets/tiles/stage3.png / stage3.json (1층과 같은 레이아웃·인덱스 표, tilecommon.py 참조)
      parts/art/work/tiles_stage3/preview.png · preview_room.png · preview_seam.png

컨셉 (story text-pack B3·D3, world-bible 3~4층 전선): 붕대가 모자라 진흙으로 묶었다. 들것에 번호가 있다. 사람에겐 없다.
  바닥 = 다져진 진흙 + 말라붙은 핏자국(무채 G02, 색 없음) + 발자국 + 떨어진 번호표
  복도 = 진흙 위 널 발판 / 벽 = 천막 캔버스(기운 자국) / 벽 윗면 = 천막 지붕 이음·당김줄
  문 = 천막 자락 (열림: 말아 올림 / 닫힘: 자락 내림 + 붕대 매듭 / 잠김: 널빤지 X 못질 = 격리)
  소품 = 들것(번호판)·붕대 더미·약병 상자·환자 번호 말뚝
색 예산: 무채 10 (G00~G07, G09, G12) + 강조 4 (19 shadow1, 21 base, 23 light1, 25 glow).
청록은 **붕대에 밴 피·약병 속 약**에만 (램프 규칙: 이 층의 피 = 청록. 바닥 얼룩은 무채로 둬서 바닥이 조용하다).
바닥 명도 대역은 1층과 동일 (본색 G04, 진흙 G03, 얼룩 G02, 마른 흙 G05).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon as tc  # noqa: E402

G = tc.G
A = tc.ramp(3)
T = tc.T

C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
    "S": A[3],   # 19 shadow1 — 밴 피 가장자리·약 그늘
    "B": A[5],   # 21 base   — 붕대에 밴 피·약병 속 약
    "L": A[7],   # 23 light1 — 약병 빛·계단 빛
    "W": A[9],   # 25 glow   — 약병 글린트
}
ctx = tc.Ctx(C)
new, blit = ctx.new, ctx.blit


# ============================================================ 바닥 (다져진 진흙)
def mud_floor(mud=(), dry=(), stains=(), extra=None):
    """G04 바탕. mud: 진흙 G03 덩어리 (행: (x0,x1)) 사전 목록. dry: 마른 흙 G05 점. stains: 어두운 얼룩 G02 덩어리.
    가장자리(0·15행·열)는 바탕색을 유지해 어떤 조합으로도 이어진다."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    for blob in mud:
        for y, (x0, x1) in blob.items():
            s.line(x0, y, x1, y, C["3"])
    for blob in stains:
        for y, (x0, x1) in blob.items():
            s.line(x0, y, x1, y, C["2"])
    for x, y in dry:
        s.px(x, y, C["5"])
    if extra:
        extra(s)
    return s


def floor_0():
    return mud_floor(
        mud=[{2: (3, 6), 3: (2, 8), 4: (2, 7), 5: (4, 6)}, {10: (9, 13), 11: (8, 14), 12: (10, 13)}],
        dry=[(11, 3), (12, 3), (4, 12), (5, 13), (13, 7)],
    )


def floor_1():
    """말라붙은 핏자국: 어두운 얼룩 G02 + 진흙 테 G03. 색은 없다."""
    return mud_floor(
        mud=[{5: (5, 11), 6: (4, 12), 7: (4, 12), 8: (4, 12), 9: (5, 11), 10: (7, 9)}],
        stains=[{6: (6, 10), 7: (5, 11), 8: (6, 10), 9: (7, 9)}, {11: (2, 3), 12: (1, 3)}],
        dry=[(13, 2), (2, 7)],
    )


def floor_2():
    """발자국(군화 두 짝, G03) + 진흙."""
    def boots(s):
        for bx, by in ((3, 3), (7, 8)):
            s.rect(bx, by, bx + 1, by + 3, C["3"])
            s.rect(bx, by + 5, bx + 1, by + 5, C["3"])
            s.px(bx, by, C["2"]); s.px(bx + 1, by + 5, C["2"])
    return mud_floor(
        mud=[{11: (10, 13), 12: (9, 14), 13: (11, 13)}],
        dry=[(12, 2), (13, 2), (2, 12)],
        extra=boots,
    )


def floor_3():
    """떨어진 번호표(G07 나무패 4x3, 반쯤 진흙에 묻힘, G03 눈금) + 진흙 + 작은 얼룩. G09 는 1x 에서 얼굴처럼 반복돼 낮췄다."""
    def tag(s):
        s.rect(9, 4, 12, 6, C["7"]); s.px(9, 4, C["9"]); s.px(10, 5, C["3"]); s.px(12, 5, C["3"])
        s.line(10, 7, 13, 7, C["3"]); s.px(13, 6, C["3"]); s.px(12, 6, C["3"])
    return mud_floor(
        mud=[{9: (2, 6), 10: (1, 7), 11: (2, 7), 12: (3, 5)}],
        stains=[{12: (11, 12), 13: (10, 13)}],
        dry=[(4, 2), (14, 11)],
        extra=tag,
    )


FLOORS = [floor_0(), floor_1(), floor_2(), floor_3()]


# ============================================================ 복도 (진흙 위 널 발판)
def corridor_tile():
    """가로 널 4장을 진흙(G03) 위에 깔았다. 널 윗면 G05, 널 G04, 널 사이 진흙 G03·그늘 G02. 끝이 부러진 널 하나."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["2"])
        s.line(0, y + 1, T - 1, y + 1, C["5"])
        s.line(0, y + 2, T - 1, y + 2, C["4"])
    # 부러진 끝: 2번째 널 오른쪽이 진흙에 잠김
    s.rect(12, 5, 15, 6, C["3"]); s.px(12, 6, C["2"])
    s.px(5, 10, C["2"]); s.px(9, 2, C["2"])  # 못
    return s


# ============================================================ 벽
def wall_face():
    """천막 캔버스 벽: 두 폭(x0..7, x8..15) 을 K 솔기로 잇고, 솔기 왼쪽에 빛 G02. 가로 솔기 y7 에 바느질 점.
    기운 조각(G03 천 + K 바늘땀) 하나. 아랫단 K 그늘."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["1"])
    for x in (0, 8):
        s.line(x, 0, x, T - 1, C["K"])
        s.line(x + 1, 0, x + 1, T - 2, C["2"])
    # 가로 솔기 (바느질)
    for x in range(2, 16, 2):
        s.px(x, 7, C["2"])
    # 천 주름 (느슨한 사선 G02)
    s.line(4, 2, 6, 5, C["2"]); s.line(12, 9, 14, 13, C["2"])
    # 기운 조각 (x10..13, y2..5): G03 천, 네 귀 바늘땀 G02 (K 점은 벌레처럼 보여서 뺐다)
    s.rect(10, 2, 13, 5, C["3"])
    for x, y in [(10, 2), (13, 2), (10, 5), (13, 5)]:
        s.px(x, y, C["2"])
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_top():
    """벽 윗면: 천막 지붕을 위에서 본 것. G01 바탕, 폭 이음 K(y0, y8) + 빛 G02, 당김줄 G03 점선 + 말뚝 K."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["1"])
    for y in (0, 8):
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["2"])
    s.line(6, 0, 6, 7, C["K"]); s.line(13, 8, 13, 15, C["K"])
    for x in range(1, 16, 3):
        s.px(x, 4, C["2"]); s.px(x + 1, 12, C["2"])
    s.px(3, 5, C["K"]); s.px(11, 11, C["K"])
    return s


# ============================================================ 문 (천막 자락, 나무 기둥 틀)
def door_frame(s):
    """기둥 2개(x0..2, x13..15) + 상인방(y0..1). 나무 G03/G04. 바탕 G01."""
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["3"]); s.line(0, 0, 0, T - 1, C["K"]); s.line(1, 0, 1, T - 1, C["4"])
    s.rect(13, 0, 15, T - 1, C["3"]); s.line(15, 0, 15, T - 1, C["K"]); s.line(13, 0, 13, T - 1, C["2"])
    s.rect(0, 0, T - 1, 1, C["3"]); s.line(0, 0, T - 1, 0, C["K"]); s.line(3, 1, 12, 1, C["4"])


def door_open():
    """열린 문: 자락을 왼쪽 기둥에 말아 묶었다(G02/G03 두루마리 + G05 빛). 틀 안으로 널 발판이 이어진다."""
    s = new()
    door_frame(s)
    s.rect(3, 2, 12, 15, C["3"])
    for y in (2, 6, 10, 14):
        s.line(3, y, 12, y, C["2"])
        s.line(3, y + 1, 12, y + 1, C["5"])
        if y + 2 < 16:
            s.line(3, y + 2, 12, y + 2, C["4"])
    # 말아 올린 자락 (x3..5, y2..13)
    s.rect(3, 2, 5, 13, C["2"]); s.line(3, 2, 3, 13, C["3"]); s.px(3, 3, C["5"]); s.px(3, 6, C["5"]); s.px(3, 9, C["5"])
    s.px(4, 5, C["K"]); s.px(4, 10, C["K"])  # 묶은 끈
    s.rect(3, 14, 5, 15, C["3"])
    return s


def door_flap(s):
    """내린 천막 자락: 천 G02, 주름 K, 왼쪽 빛 G03, 아랫단 진흙 G03."""
    s.rect(3, 2, 12, 15, C["2"])
    for x in (5, 9):
        s.line(x, 2, x, 13, C["K"])
    s.line(3, 2, 3, 14, C["3"]); s.line(6, 2, 6, 10, C["3"]); s.line(10, 2, 10, 8, C["3"])
    s.rect(3, 14, 12, 15, C["3"]); s.px(7, 14, C["2"]); s.px(11, 15, C["2"])


def door_closed():
    """닫힌 문: 자락 내림 + 가운데 붕대 매듭(G12, 그늘 G09)."""
    s = new()
    door_frame(s)
    door_flap(s)
    s.rect(6, 7, 9, 8, C["C"]); s.px(7, 6, C["C"]); s.px(8, 9, C["C"]); s.px(9, 8, C["9"]); s.px(6, 8, C["9"])
    return s


def door_locked():
    """잠긴 문(보스 방): 자락 + 널빤지 X 못질(격리). 널 G05/G04, 못 G09. 청록 없음."""
    s = new()
    door_frame(s)
    door_flap(s)
    for i in range(10):
        x = 3 + i
        s.px(x, 3 + i, C["5"]); s.px(x, 4 + i, C["4"])
    for i in range(10):
        x = 3 + i
        s.px(x, 13 - i, C["5"]); s.px(x, 14 - i, C["4"])
    for x, y in [(4, 4), (11, 11), (4, 12), (11, 4)]:
        s.px(x, y, C["9"])
    return s


# ============================================================ 출구 · 상점 (2x2)
def exit_stairs():
    """올라가는 돌계단 4단 (1층과 같은 구조). 위에서 비껴드는 청록빛 2px x2."""
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


def vial(s, x, y, h=5):
    """약병 2폭 x h: 유리 G07, 약 B (아래 2/3), 그늘 S, 글린트 W 1px, 마개 G05."""
    s.rect(x, y, x + 1, y + h - 1, C["7"])
    s.rect(x, y + 2, x + 1, y + h - 1, C["B"])
    s.px(x + 1, y + h - 1, C["S"]); s.px(x + 1, y + h - 2, C["S"])
    s.px(x, y + 1, C["W"])
    s.px(x, y - 1, C["5"]); s.px(x + 1, y - 1, C["5"])


def bandage_roll(s, x, y):
    """붕대 두루마리 4x3 (옆으로 눕힘): G12 본색, 아래 G09 그늘, 감긴 결 G09 1px."""
    s.rect(x, y, x + 3, y + 2, C["C"])
    s.line(x, y + 2, x + 3, y + 2, C["9"]); s.px(x + 3, y + 1, C["9"])
    s.px(x + 1, y + 1, C["9"])


def shop_counter():
    """종군 상인 좌판: 널 탁자 위 약병 2 + 붕대 두루마리 1. 2x2 로 깔면 좌판 4칸."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["2"])
        s.line(0, y + 1, T - 1, y + 1, C["5"])
    s.line(0, 15, T - 1, 15, C["2"])
    vial(s, 3, 4, 6); vial(s, 7, 3, 7)
    s.line(3, 10, 4, 10, C["2"]); s.line(7, 10, 8, 10, C["2"])
    bandage_roll(s, 10, 6)
    s.line(10, 9, 13, 9, C["2"])
    bandage_roll(s, 3, 12)
    s.px(10, 12, C["9"]); s.px(11, 12, C["9"]); s.px(12, 12, C["C"]); s.px(12, 13, C["9"])  # 풀린 붕대 끝
    return s


# ============================================================ 소품 (투명 배경)
def prop_stretcher():
    """들것(solid): 가로 장대 2개(G05/G04) 사이 캔버스(G06), 손잡이 끝. 번호판 G09 (왼쪽 위) + 얼룩 G03. 청록 없음."""
    s = new()
    s.rect(1, 5, 14, 11, C["6"])                       # 캔버스 (장대 끝 1px 만 밖으로 — 괄호처럼 보이지 않게)
    s.line(1, 5, 14, 5, C["7"])                        # 윗변 빛
    s.line(2, 11, 14, 11, C["5"])                      # 아랫변 그늘
    s.rect(8, 7, 10, 9, C["3"]); s.px(7, 8, C["3"]); s.px(9, 10, C["3"])  # 마른 얼룩
    s.rect(0, 3, 15, 4, C["5"]); s.line(0, 4, 15, 4, C["4"])   # 윗장대
    s.rect(0, 12, 15, 13, C["5"]); s.line(0, 13, 15, 13, C["4"])  # 아랫장대
    for x in (0, 15):
        s.px(x, 3, C["7"]); s.px(x, 12, C["7"])
    s.rect(3, 6, 6, 8, C["9"]); s.px(4, 7, C["3"]); s.px(6, 7, C["3"])  # 번호판
    s.line(2, 14, 13, 14, C["2"])                      # 그림자
    s.outline(C["K"], where="inside")
    s.line(2, 14, 13, 14, C["2"])
    s.line(1, 3, 14, 3, C["5"], only=C["K"])
    s.line(1, 12, 14, 12, C["5"], only=C["K"])
    return s


def prop_bandages():
    """붕대 더미(통과 가능): 쓰고 버린 붕대 뭉치. G12 본색, G09 그늘, 밴 피 B/S 3곳 (청록 ~12px)."""
    s = new()
    prof = {4: (6, 9), 5: (4, 11), 6: (3, 12), 7: (2, 13), 8: (2, 13), 9: (2, 13), 10: (3, 13), 11: (4, 12), 12: (6, 11)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["C"])
    # 감긴 결 (G09 곡선)
    s.line(4, 6, 8, 6, C["9"]); s.line(9, 8, 12, 8, C["9"]); s.line(3, 10, 7, 10, C["9"]); s.px(8, 11, C["9"])
    s.line(6, 12, 11, 12, C["9"]); s.px(12, 11, C["9"]); s.px(13, 10, C["9"])
    # 밴 피 (청록)
    s.rect(5, 7, 6, 8, C["B"]); s.px(7, 8, C["S"]); s.px(5, 9, C["S"])
    s.px(10, 10, C["B"]); s.px(11, 10, C["B"]); s.px(11, 11, C["S"])
    s.px(9, 5, C["B"])
    # 풀린 끝
    s.px(13, 12, C["C"]); s.px(13, 13, C["C"]); s.px(14, 13, C["C"]); s.px(14, 14, C["9"])
    s.line(3, 13, 12, 13, C["2"])
    s.outline(C["K"], where="inside")
    s.line(3, 13, 12, 13, C["2"])
    s.px(13, 12, C["C"]); s.px(13, 13, C["9"]); s.px(14, 13, C["C"]); s.px(14, 14, C["9"])
    s.line(7, 4, 8, 4, C["C"], only=C["K"])
    return s


def prop_vial_crate():
    """약병 상자(solid): 열린 나무 상자(G04/G05, 틈 G02), 짚 G06, 약병 3개 목이 보임 (청록 ~9px)."""
    s = new()
    s.rect(2, 6, 13, 14, C["4"])
    s.line(2, 6, 13, 6, C["5"]); s.line(2, 6, 2, 14, C["5"])
    s.line(3, 14, 13, 14, C["3"]); s.line(13, 7, 13, 14, C["3"])
    s.line(2, 10, 13, 10, C["2"]); s.px(7, 11, C["2"]); s.px(7, 12, C["2"]); s.px(7, 13, C["2"])
    # 윗면 (열림): 짚
    s.rect(3, 4, 12, 5, C["6"]); s.px(5, 4, C["7"]); s.px(9, 5, C["7"]); s.px(11, 4, C["5"])
    s.line(3, 15, 13, 15, C["2"])
    s.outline(C["K"], where="inside")
    s.line(3, 15, 13, 15, C["2"])
    s.line(4, 4, 11, 4, C["6"], only=C["K"])
    # 약병 3개 (목 + 마개), 짚 위로 — 2폭 유리는 셀아웃에 통째로 검어지므로 셀아웃 뒤에 그린다 (소지품 keep 규칙)
    for x in (4, 7, 10):
        s.rect(x, 2, x + 1, 5, C["7"])
        s.px(x, 1, C["5"]); s.px(x + 1, 1, C["5"])
        s.px(x, 4, C["B"]); s.px(x + 1, 4, C["B"]); s.px(x + 1, 5, C["S"]); s.px(x, 5, C["B"])
        s.px(x, 2, C["W"])
        s.px(x + 1, 3, C["6"])
    return s


def prop_number_stake():
    """환자 번호 말뚝(통과 가능): 진흙에 박은 말뚝(G05/G04) + 나무패(G09, G03 눈금). 청록 없음."""
    s = new()
    s.line(7, 6, 7, 13, C["5"]); s.line(8, 6, 8, 13, C["4"])
    s.px(7, 14, C["4"]); s.px(8, 14, C["3"])
    s.rect(4, 2, 11, 6, C["9"]); s.line(4, 6, 11, 6, C["7"]); s.px(11, 5, C["7"])
    s.line(5, 3, 5, 5, C["3"]); s.line(7, 3, 7, 5, C["3"]); s.line(9, 3, 9, 5, C["3"]); s.px(10, 5, C["3"])
    s.rect(5, 15, 10, 15, C["2"]); s.px(6, 14, C["2"]); s.px(9, 14, C["2"])  # 파인 진흙
    s.outline(C["K"], where="inside")
    s.rect(5, 15, 10, 15, C["2"]); s.px(6, 14, C["2"]); s.px(9, 14, C["2"])
    s.line(5, 2, 10, 2, C["9"], only=C["K"])
    return s


def void_tile():
    return new()


TILES = [
    ("floor_0", FLOORS[0]), ("floor_1", FLOORS[1]), ("floor_2", FLOORS[2]), ("floor_3", FLOORS[3]),
    ("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
    ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
    ("exit", exit_stairs()), ("shop", shop_counter()),
    ("prop_stretcher", prop_stretcher()), ("prop_bandages", prop_bandages()), ("prop_vial_crate", prop_vial_crate()),
    ("prop_number_stake", prop_number_stake()),
]
PROPS = [("stretcher", True), ("bandage_pile", False), ("vial_crate", True), ("number_stake", False)]

if __name__ == "__main__":
    tc.run(3, "붕(繃) — 야전병원 제국 전선", TILES, PROPS, [19, 21, 23, 25], HERE)
