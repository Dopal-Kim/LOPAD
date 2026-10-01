#!/usr/bin/env python3
"""LOPAD 1층 '잔(盞)' 타일셋 빌드 (16x16) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_stage1/build.py
입력: parts/art/palette/lopad.json (무채 16 + 1층 호박 램프), assets/sprites/player/player_idle.png (샘플 방 미리보기용)
산출:
  assets/tiles/stage1.png   8열 x 3행 격자 (24칸, 17칸 사용). 인덱스 = row*8 + col
  assets/tiles/stage1.json  계약 §2: tiles(게임 TileId -> 인덱스 목록), walls, props
  parts/art/work/tiles_stage1/preview.png       시트 6배 + 인덱스 라벨
  parts/art/work/tiles_stage1/preview_room.png  12x8 샘플 방 4배 (주인공 idle 얹음)
  parts/art/work/tiles_stage1/preview_seam.png  바닥·벽·출구·상점 2x2 이어붙임 검사

근거: 29라운드 자율 결정 A (바닥 G02~G04 기조 + 무늬 G04/G05, 벽 G00~G01, 호박은 등불·웅덩이·술에만, 화면 5% 이하).
색 예산: 타일셋 무채 <=10 + 강조 <=4.

인덱스 표
  0..3  바닥 석판 변형 4        4 복도 널빤지        5 벽 정면(벽돌)      6 벽 윗면
  7     void (완전 투명)        8 문 열림           9 문 닫힘            10 문 잠김(보스)
  11    출구 계단(2x2 이어붙임)  12 상점 좌판(2x2)    13 소품 술통(solid)  14 소품 깨진 병
  15    소품 웅덩이              16 소품 등불(solid)  17..23 예비(투명)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "pixel-art-studio", "scripts"))
from pixelstudio import Sprite  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

OUT_ASSETS = os.path.join(ROOT, "assets", "tiles")
os.makedirs(OUT_ASSETS, exist_ok=True)

with open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8") as fp:
    PAL = json.load(fp)
G = PAL["gray"]
A = PAL["floors"][0]["ramp"]  # 1층 잔(호박)

T = 16
COLS, ROWS = 8, 3

# 색 예산: 무채 10 (G00~G09) + 강조 4 (A19 shadow1, A21 base, A23 light1, A25 glow)
C = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
    "5": G[5], "6": G[6], "7": G[7], "8": G[8], "9": G[9],
    "S": A[3],   # 19 shadow1 — 술 그늘·웅덩이 반사 어두운 쪽
    "B": A[5],   # 21 base   — 술·불꽃 본색
    "L": A[7],   # 23 light1 — 불빛·반사
    "W": A[9],   # 25 glow   — 불꽃 심지·강한 반사
}
PALETTE = list(dict.fromkeys(C.values()))


def new():
    return Sprite(T, T, palette=PALETTE)


def blit(s, rows, ox=0, oy=0):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x, y = ox + i, oy + j
            if 0 <= x < T and 0 <= y < T:
                s.px(x, y, C[ch])


# ============================================================ 바닥 (석판)
def slab(s, x0, y0, x1, y1, fill="4", hi="5", shade="3"):
    """석판 하나: 본색 + 좌상단 1px 하이라이트 + 우하단 1px 그늘. 빛 좌상단."""
    s.rect(x0, y0, x1, y1, C[fill])
    s.line(x0, y0, x1, y0, C[hi])       # 윗변
    s.line(x0, y0, x0, y1, C[hi])       # 왼변
    s.line(x0 + 1, y1, x1, y1, C[shade])  # 아랫변
    s.line(x1, y0 + 1, x1, y1, C[shade])  # 오른변


def floor_tile(slabs, cracks=(), chips=(), dark=()):
    """줄눈 G02 바탕 위에 석판을 깔고 균열(G02)·조각(G05)·얼룩(G03) 을 찍는다.
    모든 변형이 x=0 열·y=0 행을 줄눈으로 두어 어떤 조합으로도 이어진다."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["2"])
    for sl in slabs:
        slab(s, *sl)
    for pts in cracks:
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            s.line(ax, ay, bx, by, C["2"])
    for x, y in chips:
        s.px(x, y, C["5"])
    for x, y in dark:
        s.px(x, y, C["3"])
    return s


FLOORS = [
    # 0 기본: 큰 석판 2단, 어긋난 줄눈
    floor_tile(
        slabs=[(1, 1, 8, 7), (10, 1, 15, 7), (1, 9, 4, 15), (6, 9, 12, 15), (14, 9, 15, 15)],
        chips=[(3, 3), (12, 11)],
        dark=[(7, 6), (11, 5)],
    ),
    # 1 균열: 한 석판에 사선 금
    floor_tile(
        slabs=[(1, 1, 6, 7), (8, 1, 15, 7), (1, 9, 9, 15), (11, 9, 15, 15)],
        cracks=[[(10, 2), (12, 4), (12, 6)], [(3, 11), (5, 13), (5, 15)]],
        dark=[(13, 3), (2, 14)],
    ),
    # 2 잔돌: 작은 석판이 섞임
    floor_tile(
        slabs=[(1, 1, 5, 4), (7, 1, 15, 4), (1, 6, 9, 11), (11, 6, 15, 11), (1, 13, 3, 15), (5, 13, 11, 15), (13, 13, 15, 15)],
        chips=[(8, 7)],
        dark=[(3, 8), (13, 2), (7, 14)],
    ),
    # 3 얼룩: 큰 석판 + 술 얼룩(어두운 무채 G03, 색 없음) 과 빠진 조각
    floor_tile(
        slabs=[(1, 1, 10, 9), (12, 1, 15, 9), (1, 11, 6, 15), (8, 11, 15, 15)],
        cracks=[[(4, 9), (4, 6)]],
        dark=[(5, 3), (6, 3), (5, 4), (6, 4), (7, 4), (6, 5), (13, 13), (14, 13), (13, 14)],
    ),
]


# ============================================================ 복도 (널빤지)
def corridor_tile():
    """가로 널빤지 4장(4px), 끝이음 어긋남. 방 바닥보다 한 단 어둡다 (G03 본색)."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["3"])
    ends = [5, 11, 2, 9]
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["2"])            # 널빤지 사이 틈
        s.line(0, y + 1, T - 1, y + 1, C["4"])    # 윗면 하이라이트
        e = ends[i]
        s.px(e, y + 1, C["2"]); s.px(e, y + 2, C["2"]); s.px(e, y + 3, C["2"])  # 끝이음
    # 옹이·못
    for x, y in [(3, 7), (12, 14)]:
        s.px(x, y, C["2"])
    for x, y in [(8, 2), (14, 10)]:
        s.px(x, y, C["5"])
    return s


# ============================================================ 벽
def wall_face():
    """벽 정면: 벽돌 4단(4px), 반 칸 어긋남. 회반죽 G00, 벽돌 G01, 윗변 G02 하이라이트. 거의 검정 덩어리."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["1"])
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["K"])
        s.line(0, y + 1, T - 1, y + 1, C["2"])
        off = 0 if i % 2 == 0 else 4
        for x in (off, off + 8):
            s.line(x, y, x, y + 3, C["K"])
            if x + 8 < T:
                pass
    # 벽돌 좌상단 모서리 한 점만 밝게 (한 단 위)
    for x, y in [(2, 1), (10, 1), (6, 9), (14, 9)]:
        s.px(x, y, C["3"])
    # 아랫단 그늘(바닥과 닿는 곳)
    s.line(0, 15, T - 1, 15, C["K"])
    return s


def wall_top():
    """벽 윗면: 평평한 돌 덮개. G01 바탕, 돌 이음 G00, 윗면 빛 G02 알갱이."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.line(0, 0, T - 1, 0, C["K"])
    s.line(0, 8, T - 1, 8, C["K"])
    s.line(0, 1, T - 1, 1, C["2"])
    s.line(0, 9, T - 1, 9, C["2"])
    s.line(7, 0, 7, 7, C["K"])
    s.line(3, 8, 3, 15, C["K"])
    s.line(11, 8, 11, 15, C["K"])
    for x, y in [(2, 4), (3, 4), (12, 3), (6, 12), (7, 12), (14, 11)]:
        s.px(x, y, C["2"])
    return s


# ============================================================ 문 (벽 자리)
DOOR_FRAME = [
    "1333........3331",
    "1343........3431",
]


def door_frame(s):
    """양쪽 문설주(x0..2, x13..15) + 상인방(y0..1). 벽 톤 안에서 나무 G03/G04."""
    s.rect(0, 0, T - 1, T - 1, C["1"])
    s.rect(0, 0, 2, T - 1, C["3"]); s.line(0, 0, 0, T - 1, C["K"]); s.line(1, 0, 1, T - 1, C["4"])
    s.rect(13, 0, 15, T - 1, C["3"]); s.line(15, 0, 15, T - 1, C["K"]); s.line(13, 0, 13, T - 1, C["2"])
    s.rect(0, 0, T - 1, 1, C["3"]); s.line(0, 0, T - 1, 0, C["K"]); s.line(3, 1, 12, 1, C["4"])


def door_open():
    """열린 문: 문틀 안으로 복도 널빤지가 그대로 이어진다(통로로 읽힘). 문짝은 왼쪽 문설주에 젖혀져 2px 폭."""
    s = new()
    door_frame(s)
    s.rect(3, 2, 12, 15, C["3"])
    for y in (2, 6, 10, 14):
        s.line(3, y, 12, y, C["2"])
        s.line(3, y + 1, 12, y + 1, C["4"])
    s.px(8, 7, C["2"]); s.px(8, 8, C["2"]); s.px(8, 9, C["2"])
    # 젖혀진 문짝 (x3..4): 밝은 널 + 쇠띠 2점
    s.rect(3, 2, 4, 14, C["5"]); s.line(4, 2, 4, 14, C["4"])
    s.px(3, 5, C["7"]); s.px(3, 12, C["7"]); s.px(4, 5, C["6"]); s.px(4, 12, C["6"])
    s.line(3, 15, 4, 15, C["2"])
    return s


def door_planks(s, x0=3, x1=12, y0=2, y1=15):
    """나무 문짝: 세로 널 G04, 틈 G02, 쇠띠 G06 + 리벳 G08."""
    s.rect(x0, y0, x1, y1, C["4"])
    for x in (x0 + 2, x0 + 5, x0 + 8):
        s.line(x, y0, x, y1, C["2"])
    s.line(x0, y0, x1, y0, C["5"])
    for y in (y0 + 3, y0 + 10):
        s.line(x0, y, x1, y, C["6"])
        s.line(x0, y + 1, x1, y + 1, C["5"])
        for x in (x0 + 1, x0 + 7):
            s.px(x, y, C["8"])


def door_closed():
    s = new()
    door_frame(s)
    door_planks(s)
    s.px(10, 9, C["7"]); s.px(10, 10, C["K"])   # 손잡이 고리
    return s


def door_locked():
    """잠긴 문(보스 방): 닫힌 문 + 가로 쇠 빗장 + 자물쇠. 호박 없음."""
    s = new()
    door_frame(s)
    door_planks(s)
    s.rect(2, 7, 13, 8, C["6"]); s.line(2, 7, 13, 7, C["7"]); s.px(2, 8, C["5"]); s.px(13, 8, C["5"])
    # 자물쇠 (중앙): 몸통 G07, 고리 G08, 열쇠구멍 G00
    s.rect(6, 9, 9, 12, C["7"]); s.line(6, 9, 9, 9, C["8"])
    s.px(6, 8, C["8"]); s.px(9, 8, C["8"])
    s.px(7, 10, C["K"]); s.px(8, 10, C["K"]); s.px(7, 11, C["K"])
    return s


# ============================================================ 출구 · 상점 (2x2 이어붙임)
def exit_stairs():
    """올라가는 돌계단(스토리: 층이 오를수록 수도에 가까워진다). 4px 단 x4.
    단 = 챌(그늘 G00 1px) + 디딤 윗변(G07) + 디딤(G05/G04 2px). 위 단일수록 밝다.
    위에서 비껴 떨어지는 호박빛: 디딤 오른쪽 끝에 L 2px x2 (타일당 4px).
    가로·세로 모두 이어 붙어 2x2 = 8단 계단으로 읽힌다."""
    s = new()
    body = ["5", "5", "4", "4"]
    for i in range(4):
        y = i * 4
        s.line(0, y, T - 1, y, C["K"])              # 챌 그늘
        s.line(0, y + 1, T - 1, y + 1, C["7"])      # 디딤 윗변(빛)
        s.rect(0, y + 2, T - 1, y + 3, C[body[i]])  # 디딤
        s.line(0, y + 3, T - 1, y + 3, C["3"] if i >= 2 else C["4"])
        if i in (0, 2):
            s.px(12, y + 1, C["L"]); s.px(13, y + 1, C["L"])
    # 마모 자국
    for x, y in [(3, 2), (9, 6), (6, 10), (14, 14)]:
        s.px(x, y, C["3"])
    return s


def shop_counter():
    """술 좌판: 가로 널빤지 위 병 2개. 병 안의 술만 호박(B/S), 유리 G07, 글린트 G09.
    병이 타일 안에 완결되어 2x2 로 깔면 좌판 4칸 = 병 8개."""
    s = new()
    s.rect(0, 0, T - 1, T - 1, C["4"])
    for y in (0, 5, 10):
        s.line(0, y, T - 1, y, C["2"])
        s.line(0, y + 1, T - 1, y + 1, C["5"])
    s.line(0, 15, T - 1, 15, C["2"])
    for bx in (3, 10):
        # 병: 목(1폭) + 몸통(3폭), 높이 9. 바닥 그림자 1px
        s.rect(bx, 2, bx + 2, 11, C["7"])
        s.rect(bx + 1, 2, bx + 1, 3, C["7"])
        s.rect(bx, 2, bx + 2, 3, C["2"]); s.px(bx + 1, 2, C["7"]); s.px(bx + 1, 3, C["7"])
        s.rect(bx, 6, bx + 2, 10, C["B"])   # 술
        s.px(bx + 2, 7, C["S"]); s.px(bx + 2, 8, C["S"]); s.px(bx + 2, 9, C["S"]); s.px(bx + 2, 10, C["S"])
        s.px(bx, 5, C["9"])                  # 글린트
        s.line(bx, 11, bx + 2, 11, C["5"])
        s.line(bx, 12, bx + 2, 12, C["2"])   # 그림자
    return s


# ============================================================ 소품 (투명 배경, 바닥 위에 겹침)
def prop_barrel():
    """술통(solid): 배부른 통. 세로 널 G04/G03, 쇠테 G06+G08, 윗뚜껑 G05. 주둥이(쇠꼭지)에서 술 방울(B)."""
    s = new()
    # 행별 반폭 (y2..15): 위·아래가 좁고 가운데가 넓다
    prof = {2: (5, 10), 3: (4, 11), 4: (3, 12), 5: (3, 12), 6: (2, 13), 7: (2, 13), 8: (2, 13), 9: (2, 13),
            10: (2, 13), 11: (3, 12), 12: (3, 12), 13: (3, 12), 14: (4, 11), 15: (5, 10)}
    for y, (x0, x1) in prof.items():
        s.line(x0, y, x1, y, C["4"])
    for x in (6, 9):
        s.line(x, 3, x, 15, C["3"])      # 널 틈
    for y, (x0, x1) in prof.items():
        s.px(x0, y, C["5"])              # 왼쪽(빛) 가장자리
        s.px(x1, y, C["2"])              # 오른쪽 그늘
        s.px(x1 - 1, y, C["3"])
    # 쇠테 2줄
    for y in (5, 12):
        x0, x1 = prof[y]
        s.line(x0, y, x1, y, C["6"])
        s.px(x0 + 1, y, C["8"]); s.px(x0 + 2, y, C["8"])
        s.line(x0 + 1, y + 1, x1 - 1, y + 1, C["3"])
    # 뚜껑 (윗면 G05)
    s.line(5, 2, 10, 2, C["5"]); s.line(4, 3, 11, 3, C["5"]); s.px(5, 3, C["7"]); s.px(6, 3, C["7"])
    # 쇠꼭지 + 술 방울
    s.px(7, 9, C["1"]); s.px(8, 9, C["1"]); s.px(7, 10, C["K"]); s.px(8, 10, C["K"]); s.px(8, 8, C["7"])
    s.px(8, 11, C["B"]); s.px(8, 14, C["B"]); s.px(8, 15, C["S"]); s.px(9, 15, C["S"])
    s.outline(C["K"], where="inside")
    s.line(5, 2, 10, 2, C["5"], only=C["K"])  # 윗변은 셀아웃 대신 밝게
    return s


def prop_bottle():
    """깨진 병(통과 가능): 옆으로 누운 병. 목은 왼쪽, 오른쪽 끝이 깨져 들쭉날쭉. 깨진 쪽에서 술(B/S)이 흘러 고인다."""
    s = new()
    # 고인 술 (바닥, 오른쪽 아래)
    s.rect(9, 10, 13, 11, C["S"]); s.rect(10, 9, 12, 9, C["S"]); s.px(14, 11, C["S"]); s.px(11, 12, C["S"])
    s.px(10, 10, C["B"]); s.px(11, 10, C["B"]); s.px(11, 9, C["B"])
    # 병 몸통 (x5..11, y5..8) + 목 (x2..4, y6..7)
    s.rect(5, 5, 11, 8, C["7"])
    s.rect(2, 6, 4, 7, C["7"])
    s.px(2, 6, C["8"]); s.line(5, 5, 10, 5, C["8"])      # 윗면 빛
    s.line(5, 8, 10, 8, C["6"])                          # 아랫면 그늘
    s.px(8, 6, C["B"]); s.px(9, 6, C["B"]); s.px(8, 7, C["S"]); s.px(9, 7, C["S"])  # 남은 술
    # 깨진 끝: 들쭉날쭉 (x11..12)
    s.px(11, 5, C["7"]); s.px(12, 6, C["8"]); s.px(11, 7, C["7"]); s.px(12, 8, C["7"])
    s.px(11, 6, C["K"]); s.px(11, 8, C["K"])
    # 흩어진 조각 2개 (2px 덩어리)
    s.px(13, 4, C["8"]); s.px(14, 4, C["7"])
    s.px(6, 11, C["7"]); s.px(7, 11, C["8"])
    s.outline(C["K"], where="inside")
    s.px(2, 6, C["8"]); s.line(6, 5, 10, 5, C["8"], only=C["K"])
    s.px(6, 11, C["7"]); s.px(7, 11, C["8"]); s.px(13, 4, C["8"]); s.px(14, 4, C["7"])
    return s


def prop_puddle():
    """웅덩이(통과 가능): 불규칙한 어두운 액체 G01/G02, 등불 반사(L 3px + W 1px), 먼 쪽 반사 S 2px."""
    s = new()
    rows = {4: (6, 9), 5: (4, 11), 6: (3, 12), 7: (2, 13), 8: (2, 13), 9: (3, 13), 10: (4, 11), 11: (6, 12), 12: (9, 12), 13: (10, 11)}
    for y, (x0, x1) in rows.items():
        s.line(x0, y, x1, y, C["1"])
    s.px(1, 8, C["1"]); s.px(13, 6, C["1"])
    inner = {6: (5, 10), 7: (4, 11), 8: (4, 11), 9: (5, 11), 10: (6, 10), 11: (8, 11)}
    for y, (x0, x1) in inner.items():
        s.line(x0, y, x1, y, C["2"])
    # 반사 (좌상단 빛)
    s.px(5, 7, C["L"]); s.px(6, 7, C["L"]); s.px(5, 8, C["W"]); s.px(6, 8, C["L"])
    s.px(9, 10, C["S"]); s.px(10, 10, C["S"])
    return s


def prop_lantern():
    """세운 등불(solid): 쇠기둥 G05/G06, 유리통 안 불꽃 B/L/W, 바닥 받침. 호박 12px."""
    s = new()
    # 받침 (바닥에 놓인 삼발이)
    s.rect(5, 14, 10, 14, C["5"]); s.rect(4, 15, 11, 15, C["3"])
    # 기둥
    s.line(7, 9, 7, 13, C["5"]); s.line(8, 9, 8, 13, C["4"])
    # 등 (x4..11, y2..8): 틀 G06, 안 B, 심지 W
    s.rect(4, 2, 11, 8, C["6"])
    s.rect(5, 3, 10, 7, C["B"])
    s.rect(6, 4, 9, 6, C["L"])
    s.px(7, 5, C["W"]); s.px(8, 5, C["W"])
    s.line(4, 2, 11, 2, C["7"]); s.px(4, 3, C["7"])
    # 꼭지
    s.rect(6, 0, 9, 1, C["6"]); s.px(7, 0, C["7"]); s.px(8, 0, C["7"])
    # 틀의 세로 살
    s.px(7, 3, C["6"]); s.px(8, 7, C["6"])
    s.outline(C["K"], where="inside")
    s.px(7, 0, C["7"]); s.px(8, 0, C["7"])
    s.line(5, 2, 10, 2, C["7"], only=C["K"])
    return s


def void_tile():
    return new()


# ============================================================ 시트 조립
TILES = [
    ("floor_0", FLOORS[0]), ("floor_1", FLOORS[1]), ("floor_2", FLOORS[2]), ("floor_3", FLOORS[3]),
    ("corridor", corridor_tile()), ("wall", wall_face()), ("wall_top", wall_top()), ("void", void_tile()),
    ("door_open", door_open()), ("door_closed", door_closed()), ("door_locked", door_locked()),
    ("exit", exit_stairs()), ("shop", shop_counter()),
    ("prop_barrel", prop_barrel()), ("prop_bottle", prop_bottle()), ("prop_puddle", prop_puddle()),
    ("prop_lantern", prop_lantern()),
]
IDX = {name: i for i, (name, _) in enumerate(TILES)}


def build_sheet():
    sheet = Image.new("RGBA", (COLS * T, ROWS * T), (0, 0, 0, 0))
    for i, (name, s) in enumerate(TILES):
        r, c = divmod(i, COLS)
        sheet.alpha_composite(s.composite(1), (c * T, r * T))
    sheet.save(os.path.join(OUT_ASSETS, "stage1.png"))
    meta = {
        "image": "stage1.png",
        "stage": 1,
        "name": "잔(盞) — 술독 제국 외곽",
        "tileWidth": T, "tileHeight": T,
        "columns": COLS, "rows": ROWS,
        "indexFormula": "row * columns + column",
        "tiles": {
            "0": [IDX["void"]],
            "1": [IDX["floor_0"], IDX["floor_1"], IDX["floor_2"], IDX["floor_3"]],
            "2": [IDX["wall"]],
            "3": [IDX["door_open"]],
            "4": [IDX["door_closed"]],
            "5": [IDX["door_locked"]],
            "6": [IDX["corridor"]],
            "7": [IDX["exit"]],
            "8": [IDX["shop"]],
        },
        "tileIdNames": {"0": "void", "1": "floor", "2": "wall", "3": "door_open", "4": "door_closed",
                        "5": "door_locked", "6": "corridor", "7": "exit", "8": "shop"},
        "walls": {
            "top": IDX["wall"], "bottom": IDX["wall_top"], "left": IDX["wall_top"], "right": IDX["wall_top"],
            "corner_tl": IDX["wall_top"], "corner_tr": IDX["wall_top"], "corner_bl": IDX["wall_top"], "corner_br": IDX["wall_top"],
            "note": "top = 방 위쪽(북) 벽: 정면(벽돌)이 보인다. 나머지 변·모서리는 윗면 덮개. 단일 벽만 쓰면 전부 벽돌 정면이어도 무방."
        },
        "props": [
            {"index": IDX["prop_barrel"], "name": "barrel", "solid": True},
            {"index": IDX["prop_bottle"], "name": "broken_bottle", "solid": False},
            {"index": IDX["prop_puddle"], "name": "puddle", "solid": False},
            {"index": IDX["prop_lantern"], "name": "lantern", "solid": True},
        ],
        "propsLayer": "overlay — 소품 타일은 배경이 투명하므로 바닥 레이어 위에 겹쳐 그린다",
        "names": {str(i): name for i, (name, _) in enumerate(TILES)},
        "palette": "parts/art/palette/lopad.json (gray 0..9 + floor 1 accent slots 19, 21, 23, 25)",
    }
    with open(os.path.join(OUT_ASSETS, "stage1.json"), "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    return sheet, meta


# ============================================================ 미리보기
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)


def checker(w, h, sq=8):
    bg = Image.new("RGB", (w, h), (232, 232, 232))
    d = ImageDraw.Draw(bg)
    for y in range(0, h, sq):
        for x in range(0, w, sq):
            if (x // sq + y // sq) % 2:
                d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=(203, 203, 203))
    return bg


def preview_sheet(sheet, scale=6):
    cw = T * scale
    gap = 6
    W = COLS * (cw + gap) + gap
    H = ROWS * (cw + gap + 14) + gap
    img = Image.new("RGB", (W, H), (60, 60, 64))
    d = ImageDraw.Draw(img)
    for i, (name, s) in enumerate(TILES):
        r, c = divmod(i, COLS)
        ox = gap + c * (cw + gap)
        oy = gap + r * (cw + gap + 14)
        cell = checker(cw, cw).convert("RGBA")
        cell.alpha_composite(s.composite(1).resize((cw, cw), Image.NEAREST))
        img.paste(cell.convert("RGB"), (ox, oy))
        d.text((ox, oy + cw + 1), "%d %s" % (i, name), fill=(230, 230, 230), font=FONT)
    img.save(os.path.join(HERE, "preview.png"))


def tile_img(name):
    return TILES[IDX[name]][1].composite(1)


def preview_seam(scale=4):
    """이어붙임 검사: 바닥 4변형 무작위 4x4, 벽 1x4, 벽 윗면 4x1, 출구 2x2, 상점 2x2, 복도 3x1."""
    blocks = []
    import random
    rnd = random.Random(7)
    fl = Image.new("RGBA", (T * 4, T * 4))
    for y in range(4):
        for x in range(4):
            fl.alpha_composite(tile_img("floor_%d" % rnd.randrange(4)), (x * T, y * T))
    blocks.append(("floor 4x4", fl))
    w = Image.new("RGBA", (T * 4, T * 2))
    for x in range(4):
        w.alpha_composite(tile_img("wall_top"), (x * T, 0))
        w.alpha_composite(tile_img("wall"), (x * T, T))
    blocks.append(("wall_top / wall", w))
    for nm in ("exit", "shop"):
        b = Image.new("RGBA", (T * 2, T * 2))
        for y in range(2):
            for x in range(2):
                b.alpha_composite(tile_img(nm), (x * T, y * T))
        blocks.append((nm + " 2x2", b))
    c = Image.new("RGBA", (T * 3, T))
    for x in range(3):
        c.alpha_composite(tile_img("corridor"), (x * T, 0))
    blocks.append(("corridor 3x1", c))
    W = sum(b.width * scale + 12 for _, b in blocks) + 12
    H = max(b.height for _, b in blocks) * scale + 30
    img = Image.new("RGB", (W, H), (60, 60, 64))
    d = ImageDraw.Draw(img)
    x = 12
    for label, b in blocks:
        im = b.resize((b.width * scale, b.height * scale), Image.NEAREST)
        img.paste(im.convert("RGB"), (x, 20), im)
        d.text((x, 4), label, fill=(230, 230, 230), font=FONT)
        x += im.width + 12
    img.save(os.path.join(HERE, "preview_seam.png"))


def preview_room(scale=4):
    """12x8 방(벽 포함 14x10) + 위쪽 복도. 문 3종, 출구·상점 2x2, 소품 4종, 주인공 idle down."""
    import random
    rnd = random.Random(3)
    IW, IH = 12, 8
    GW, GH = IW + 2, IH + 2 + 3  # 위에 복도 3칸
    grid = [[None] * GW for _ in range(GH)]
    OY = 3
    for y in range(IH + 2):
        for x in range(GW):
            gy = y + OY
            if y == 0:
                grid[gy][x] = "wall_top"
            elif y == IH + 1:
                grid[gy][x] = "wall_top"
            elif x == 0 or x == GW - 1:
                grid[gy][x] = "wall_top"
            else:
                grid[gy][x] = "floor_%d" % rnd.randrange(4)
    # 북벽: 윗면 한 줄 위에 정면(벽돌)을 보여주려면 벽이 2타일이 필요하나 방은 1타일 두께.
    # → 북벽 = 벽돌 정면(walls.top), 나머지 = 윗면. 모서리는 윗면.
    for x in range(1, GW - 1):
        grid[OY][x] = "wall"
    # 문: 북(열림, 복도로), 서(닫힘), 남(잠김)
    grid[OY][7] = "door_open"
    grid[OY + 4][0] = "door_closed"
    grid[OY + IH + 1][6] = "door_locked"
    # 복도 (북문 위로 3칸, 양옆 벽)
    for y in range(3):
        grid[y][7] = "corridor"
        grid[y][6] = "wall_top"
        grid[y][8] = "wall_top"
    # 출구 2x2 (오른쪽 위), 상점 2x2 (그 왼쪽)
    for dy in range(2):
        for dx in range(2):
            grid[OY + 1 + dy][10 + dx] = "exit"
            grid[OY + 1 + dy][7 + dx] = "shop"
    props = {(2, OY + 2): "prop_barrel", (3, OY + 2): "prop_barrel", (10, OY + 6): "prop_lantern",
             (5, OY + 5): "prop_puddle", (8, OY + 7): "prop_bottle", (2, OY + 7): "prop_lantern",
             (11, OY + 4): "prop_bottle"}
    W, H = GW * T, GH * T
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    for y in range(GH):
        for x in range(GW):
            nm = grid[y][x]
            if nm:
                img.alpha_composite(tile_img(nm), (x * T, y * T))
    for (x, y), nm in props.items():
        img.alpha_composite(tile_img(nm), (x * T, y * T))
    # 주인공 idle down 1프레임 (아트 파트 산출물) — 발 피벗 (8,23) 을 타일 (5, OY+4) 중앙 아래에
    pl = Image.open(os.path.join(ROOT, "assets", "sprites", "player", "player_idle.png")).convert("RGBA")
    f = pl.crop((0, 0, 16, 24))
    for (tx, ty) in [(5, OY + 4), (9, OY + 5)]:
        px, py = tx * T, ty * T + T - 1 - 23 + 4
        # 시스템이 그릴 발밑 그림자 가정: 타원 G00 반투명 대신 G01 로 흉내
        sh = ImageDraw.Draw(img)
        sh.ellipse([px + 3, py + 21, px + 12, py + 24], fill=tuple(int(G[1][i:i + 2], 16) for i in (1, 3, 5)) + (255,))
        img.alpha_composite(f, (px, py))
    big = img.resize((W * scale, H * scale), Image.NEAREST).convert("RGB")
    # 1x 도 같이 붙여 '1x 테스트'
    out = Image.new("RGB", (big.width + W + 24, big.height + 16), (60, 60, 64))
    out.paste(big, (8, 8))
    out.paste(img.convert("RGB"), (big.width + 16, 8))
    out.save(os.path.join(HERE, "preview_room.png"))
    # 호박 비율 (방 화면 전체 대비)
    amber = set(tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in (A[3], A[5], A[7], A[9]))
    n = sum(1 for p in img.getdata() if p[:3] in amber)
    print("amber px in sample room: %d / %d = %.2f%%" % (n, W * H, 100.0 * n / (W * H)))


def stats():
    used = set()
    for name, s in TILES:
        for (r, g, b), _ in s.used_colors().items():
            used.add("#%02x%02x%02x" % (r, g, b))
        info = s.stats(print_=False)
        iso = info["isolated_px"]
        if iso and name != "void":
            print("  isolated %-12s %s" % (name, iso))
        if info["semi_alpha_px"]:
            print("  SEMI ALPHA %s %d" % (name, info["semi_alpha_px"]))
    gray = [c for c in used if c in G]
    amb = [c for c in used if c in A]
    print("colors used: gray %d (budget 10), accent %d (budget 4), other %d" % (len(gray), len(amb), len(used) - len(gray) - len(amb)))
    print("  gray:", sorted(G.index(c) for c in gray))
    print("  accent slots:", sorted(16 + A.index(c) for c in amb))


def main():
    sheet, meta = build_sheet()
    preview_sheet(sheet)
    preview_seam()
    preview_room()
    stats()
    print("index table:", {i: n for i, (n, _) in enumerate(TILES)})


if __name__ == "__main__":
    main()
