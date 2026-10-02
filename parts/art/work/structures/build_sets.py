#!/usr/bin/env python3
"""LOPAD 49라운드 구조물 추가분 — 세트 배치 소품 · 전장 소품 · 튜토리얼 표식 (계약 art-assets §5 · §7.3).

근거: decisions/2026-10-02-round-49-playtest2.md 3절(전장 탄생·튜토리얼) · 7절(구조물을 노드 중앙에, 맵과 조화롭게 = 세트 배치)
      도영 님: "노드 중간에 위치하도록 하고, 너무 생뚱맞게 있기보다 맵과 조화롭게"
실행: python3 parts/art/work/structures/build_sets.py
입력: build.py(47라운드 구조물 — Cv·flame·outline 규칙 재사용, 기존 시트는 건드리지 않는다),
      assets/tiles/stage1_<region>.png/json (지역 타일, tiles_regions/build.py 가 먼저 돌아야 목업이 맞다)
산출: assets/sprites/structures/set_<region>_<name>.png/json · battlefield_<name>.png/json · tutorial_sign[_<kind>].png/json
      parts/art/work/structures/preview_sets.png (3배 시트) · preview_sets_x2.png (세트 배치 예시 2배 960x540 넷)

규칙 (§5 그대로)
  * 1행(directions ["any"]), 열 = 프레임, 패딩 0. pivot = (w/2, h) = footprint 아래 변 가운데. states 최소 idle.
  * 셀아웃 G00 + 우·하 림 G04 (서 있는 것). 바닥에 까는 것(depth floor: 광장 문양·깔개·불 둘레·표식)은 셀아웃 없음.
  * 색: 무채 + 1층 램프(지역 소품은 그 지역 = 1층 → paletteSwap false, floor "stage1"). 불·발광만 백열 코어 X1.
  * **세트 배치 메모(새 필드, 시스템이 읽으면 사용)**: `setAnchor {x,y}` = 이 시트 안에서 가운데 구조물(예: bonfire)의 피벗이
    놓일 점, `setFor` = 감싸는 구조물 id 목록, `setRole` = center(가운데 깔개) | ring(둘레) | flank(양옆) | edge(가장자리 장식).
"""
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
_spec = importlib.util.spec_from_file_location("structures_build47", os.path.join(HERE, "build.py"))
SB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SB)
Cv, G, R1, X0, X1, flame, g = SB.Cv, SB.G, SB.R1, SB.X0, SB.X1, SB.flame, SB.g
OUT = SB.OUT
OUT_FX = SB.OUT_FX
from PIL import Image, ImageDraw  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "..", "tiles_regions"))


def a(i):
    return R1[i - 16]


# ====================================================================== 공용
def stone(c, x, y, w=3, h=2, lit=7, body=5, shade=3, under=True):
    """바닥에 놓인 납작한 돌(셀아웃 없음): 윗변 lit · 몸 body · 오른쪽 shade · 아래 그늘."""
    c.rect(x, y, x + w - 1, y + h - 1, g(body), keep=True)
    c.hl(x, x + w - 1, y, g(lit), keep=True)
    c.vl(x + w - 1, y + 1, y + h - 1, g(shade), keep=True)
    if under:
        c.hl(x, x + w - 1, y + h, g(1), keep=True)


def log_flat(c, x0, y0, x1, y1, end=True):
    """바닥에 누운 통나무(셀아웃 없음, 위에서 비스듬히): 윗줄 G07 · 몸 G05 · 아랫줄 G03, 끝 나이테 G06/G04."""
    c.line(x0, y0, x1, y1, g(7), keep=True)
    c.line(x0, y0 + 1, x1, y1 + 1, g(5), keep=True)
    c.line(x0, y0 + 2, x1, y1 + 2, g(3), keep=True)
    c.line(x0, y0 + 3, x1, y1 + 3, g(1), keep=True)
    if end:
        c.rect(x1, y1, x1 + 1, y1 + 2, g(6), keep=True)
        c.px(x1 + 1, y1 + 1, g(4), keep=True)


def barrel_side(c, x, y, w=14, h=9):
    """옆으로 누운 술통(서 있는 더미용, 셀아웃은 나중에 한 번): 몸 17/18 · 윗빛 18 · 아랫그늘 16 · 쇠테 G05/G03."""
    for j in range(h):
        inset = 1 if j in (0, h - 1) else 0
        col = a(18) if j == 1 else (a(16) if j >= h - 2 else a(17))
        c.hl(x + inset, x + w - 1 - inset, y + j, col)
    for hx in (x + 2, x + w - 3):
        c.vl(hx, y, y + h - 1, g(5))
        c.px(hx, y + h - 2, g(3)); c.px(hx, y + 1, g(7))
    c.rect(x, y + 2, x, y + h - 3, a(16)); c.rect(x + w - 1, y + 2, x + w - 1, y + h - 3, a(16))
    c.px(x + w // 2, y + h // 2, g(0))


def ell_ring(cx, cy, rx, ry, n, phase=0.0):
    return [(cx + rx * math.cos(phase + 2 * math.pi * k / n), cy + ry * math.sin(phase + 2 * math.pi * k / n)) for k in range(n)]


# ====================================================================== 세트 배치 소품
def set_waste_fire_ring():
    """황무지 휴식 = 전장의 야영 자리 (64x48 바닥): 둘레 돌 9 · 앉을 통나무 셋(굵게, 아래 그늘) · 불자리 재 · 말아 둔 담요 · 냄비 · 흩어진 발자국.
    가운데 비운 자리(setAnchor)에 bonfire(2x1) 를 놓는다. (1회차: 다져진 흙 고리를 16 으로 칠했더니 검은 과녁/해자로 읽혀 뺐다)"""
    c = Cv(64, 48, R1)
    c.ell(32, 32, 13, 6.5, g(2), keep=True)                 # 불자리 재
    c.ell(32, 32, 9, 4.2, g(3), keep=True)
    for k, (x, y) in enumerate(ell_ring(32, 31, 25, 13.5, 12, 0.2)):
        if k in (0, 4, 8):
            continue                                         # 통나무 자리
        stone(c, int(round(x)) - 1, int(round(y)) - 1, 3 + (k % 2), 2)

    def log(x0, y0, x1, y1):
        c.line(x0, y0 + 4, x1, y1 + 4, g(1), keep=True)      # 땅 그늘
        for j, col in enumerate((7, 6, 5, 4)):
            c.line(x0, y0 + j, x1, y1 + j, g(col), keep=True)
        c.rect(x1, y1, x1 + 1, y1 + 3, g(6), keep=True); c.px(x1 + 1, y1 + 1, g(3), keep=True); c.px(x1 + 1, y1 + 2, g(3), keep=True)
        c.rect(x0 - 1, y0, x0, y0 + 3, g(5), keep=True)
    log(3, 30, 12, 27)                                       # 왼쪽 통나무
    log(50, 26, 59, 29)                                      # 오른쪽
    log(24, 5, 40, 5)                                        # 위 (뒤쪽) 통나무
    c.rect(18, 42, 25, 44, g(6), keep=True); c.hl(18, 25, 42, g(8), keep=True); c.hl(18, 25, 45, g(1), keep=True)   # 말아 둔 담요
    c.vl(21, 42, 44, g(4), keep=True); c.vl(24, 42, 44, g(4), keep=True)
    c.ell(45, 42, 3, 2, g(4), keep=True); c.hl(43, 47, 40, g(6), keep=True); c.px(45, 42, g(1), keep=True); c.px(48, 41, g(5), keep=True)   # 냄비
    for (x, y) in [(14, 37), (17, 39), (47, 18), (44, 16)]:  # 발자국 (16, 2px)
        c.rect(x, y, x + 1, y, a(16), keep=True)
    return [c]


def set_outer_plaza():
    """외곽 거리 광장 문양 (64x48 바닥): 판석 길 한가운데 둥글게 깐 자갈돌 — 둘레 연석(G05 윗면 · G03 옆) ·
    방사형으로 깐 돌(G03 면, G02 이음, 바깥 줄일수록 돌이 많다) · 가운데 잔 문양 돌판(G04). 휴식·상점·이벤트 구조물을 가운데에.
    (1회차: 동심원 + 가운데 검은 고리가 맨홀 뚜껑으로 읽혔다 → 가운데를 밝은 돌판으로, 이음을 엇갈린 돌로)"""
    c = Cv(64, 48, R1)
    cx, cy = 32, 25
    rows = [0.0, 0.26, 0.47, 0.66, 0.83, 0.92]
    for y in range(48):
        for x in range(64):
            dx, dy = (x + 0.5 - cx) / 30.5, (y + 0.5 - cy) / 21.0
            r = math.hypot(dx, dy)
            if r > 1.0:
                continue
            if r > 0.92:
                col = g(5) if dy < 0.35 else g(3)                          # 연석 (아래쪽은 옆면이 보인다)
                if r > 0.975 and dy > 0.35:
                    col = g(1)
                ang = (math.atan2(dy, dx) + math.pi) / (2 * math.pi)
                if abs(ang * 28 - round(ang * 28)) < 0.05:
                    col = g(2)
            elif r < rows[1]:
                col = g(4)                                                 # 가운데 돌판
                if r > rows[1] - 0.04:
                    col = g(2)
            else:
                band = max(i for i in range(len(rows) - 1) if r >= rows[i])
                n = 8 + band * 7
                ang = (math.atan2(dy, dx) + math.pi) / (2 * math.pi) + (0.5 / n if band % 2 else 0)
                edge_a = abs(ang * n - round(ang * n)) < 0.035 * n * max(0.18, 1.0 - r) / 1.6
                edge_r = any(abs(r - rr) < 0.022 for rr in rows[1:5])
                col = g(2) if (edge_r or edge_a) else g(3)
            c.px(x, y, col, keep=True)
    # 가운데 돌판의 잔 문양 (닳은 새김 G03)
    for (x, y) in [(30, 23), (31, 23), (32, 23), (33, 23), (34, 23), (31, 24), (32, 24), (33, 24), (32, 25), (32, 26), (31, 27), (32, 27), (33, 27)]:
        c.px(x, y, g(3), keep=True)
    return [c]


def set_outer_lamppost():
    """거리 등불 기둥(16x32, 서 있음): 쇠 기둥 G05/G03 · 팔 · 등 상자 안 불빛(21/23/25 + X1 심). active 4f = 불빛 흔들림."""
    fr = []
    for k in range(4):
        c = Cv(16, 32, R1)
        c.rect(6, 12, 8, 30, g(5)); c.vl(6, 12, 30, g(7)); c.vl(8, 13, 30, g(3))
        c.rect(4, 29, 10, 31, g(4)); c.hl(4, 10, 29, g(6))
        c.hl(5, 13, 11, g(5)); c.px(12, 12, g(5))                   # 팔
        c.rect(9, 2, 15, 10, g(4)); c.hl(9, 15, 2, g(6)); c.rect(11, 0, 13, 1, g(4))
        c.outline()
        glow = [(25, 23), (25, 21), (26, 23), (25, 23)][k]
        c.rect(10, 4, 14, 9, a(21), keep=True)
        c.rect(11, 5, 13, 8, a(glow[1]), keep=True)
        c.px(12, 6, a(glow[0]), keep=True); c.px(12, 7, X1 if k != 1 else a(25), keep=True)
        c.vl(12, 3, 9, g(3), keep=True) if False else None
        c.px(10, 10, a(19), keep=True)
        fr.append(c)
    return fr


def awning(c, x0, x1, y0, depth=7, stripe=4):
    """줄무늬 천막: 갈색(17/18)과 빛바랜 천(G08/G07) 줄, 아래 끝은 물결(가리비) 모양, 윗변 그늘 G03."""
    for y in range(y0, y0 + depth):
        for x in range(x0, x1 + 1):
            band = ((x - x0) // stripe) % 2
            t = (y - y0) / depth
            if band:
                col = a(18) if t < 0.3 else a(17)
            else:
                col = g(9) if t < 0.3 else g(7)
            c.px(x, y, col)
    for x in range(x0, x1 + 1):                                     # 가리비 끝
        if (x - x0) % stripe in (1, 2):
            band = ((x - x0) // stripe) % 2
            c.px(x, y0 + depth, a(16) if band else g(5))
    c.hl(x0, x1, y0, g(10))


def set_outer_stall():
    """노점 천막 + 좌판(48x32, 서 있음, footprint 3x1): 줄무늬 천막 · 기둥 둘 · 판자 좌판 위 술병·항아리·저울 · 앞 널판.
    상점 노드 가운데. 상호작용 표지(강조 25 한 점)는 저울 위."""
    c = Cv(48, 32, R1)
    c.vl(2, 6, 30, g(5)); c.vl(3, 6, 30, g(3)); c.vl(44, 6, 30, g(5)); c.vl(45, 6, 30, g(3))   # 기둥
    awning(c, 0, 47, 1, depth=8)
    c.rect(2, 17, 45, 19, g(7)); c.hl(2, 45, 17, g(9))              # 좌판 윗면
    c.rect(2, 20, 45, 30, g(5))                                     # 앞 널판
    for x in (9, 17, 25, 33, 41):
        c.vl(x, 20, 30, g(4))
    c.hl(2, 45, 25, g(4))
    # 물건: 술병 셋 · 항아리 · 자루
    for i, x in enumerate((6, 10, 13)):
        c.rect(x, 11, x + 1, 16, g(7)); c.rect(x, 13, x + 1, 16, a(21 if i != 1 else 19)); c.px(x, 10, g(9))
    c.ell(21, 14.5, 3, 3, g(6)); c.px(20, 13, g(8)); c.hl(19, 23, 11, g(5))
    c.ell(37, 14.5, 4, 3, g(8)); c.hl(35, 39, 12, g(10)); c.px(36, 13, g(10))
    c.vl(29, 9, 16, g(4)); c.hl(26, 32, 10, g(5)); c.px(26, 11, g(5)); c.px(32, 11, g(5))   # 저울
    c.hl(25, 27, 12, g(6)); c.hl(31, 33, 12, g(6))
    c.outline()
    SB.beacon(c, 29, 7)
    return [c]


def set_outer_stall_side():
    """곁 노점(32x32, footprint 2x1): 손수레 — 큰 바퀴 하나(옆모습, 바퀴살) · 짐칸 널 · 자루 셋 · 술단지 · 왼쪽으로 뻗은 손잡이 둘.
    상점 노점 거리의 곁(flank). (1회차: 작은 바퀴 둘 + 네모 짐이 기관차로 읽혔다)"""
    c = Cv(32, 32, R1)
    c.line(0, 16, 8, 19, g(6)); c.line(0, 18, 8, 21, g(4))                              # 손잡이
    c.rect(6, 18, 30, 22, g(5)); c.hl(6, 30, 18, g(7)); c.hl(6, 30, 22, g(3))        # 짐칸
    for x in (12, 19, 26):
        c.vl(x, 19, 21, g(4))
    c.vl(6, 14, 18, g(5)); c.vl(30, 14, 18, g(5))                                      # 난간 기둥
    for (cx, cy, rx) in ((12, 14, 4.5), (20, 13.5, 4.5), (27, 14.5, 3.6)):            # 자루
        c.ell(cx, cy, rx, 4, g(9)); c.px(int(cx) - 2, int(cy) - 2, g(10)); c.hl(int(cx) - 1, int(cx) + 1, int(cy - 4), g(7))
    c.rect(16, 6, 19, 10, a(17)); c.hl(16, 19, 6, a(18)); c.px(17, 5, g(7))            # 술단지
    c.ell(18, 26, 5.6, 5.6, g(5)); c.ell(18, 26, 4.2, 4.2, g(2))                       # 바퀴
    for (dx, dy) in ((0, -4), (0, 4), (-4, 0), (4, 0), (3, 3), (-3, -3), (3, -3), (-3, 3)):
        c.line(18, 26, 18 + dx, 26 + dy, g(5))
    c.px(18, 26, g(7))
    c.vl(27, 23, 30, g(4)); c.vl(28, 23, 30, g(3))                                     # 받침 다리
    c.outline()
    return [c]


def set_brewery_barrel_stack():
    """술통 더미(48x32, footprint 3x1): 누운 통 3 + 2 + 1 피라미드, 아래 통 꼭지에서 새는 술 한 줄. 양조 구역 증류기·술독 둘레."""
    c = Cv(48, 32, R1)
    for x in (1, 17, 33):
        barrel_side(c, x, 21, 14, 10)
    for x in (9, 25):
        barrel_side(c, x, 11, 14, 10)
    barrel_side(c, 17, 1, 14, 10)
    c.outline()
    c.px(8, 28, g(6), keep=True); c.px(8, 29, a(21), keep=True); c.px(9, 31, a(19), keep=True)
    return [c]


def set_hall_long_table():
    """연회 긴 탁자(48x32, footprint 3x1): 흰 식탁보(G11/G12, 접힌 주름 G10) · 앞 드리운 자락 · 짙은 나무 다리(16) ·
    위: 고기 쟁반·은잔·촛대 · **엎어진 잔에서 식탁보를 타고 흘러내린 포도주**(17/16)."""
    c = Cv(48, 32, R1)
    c.rect(1, 8, 46, 19, g(11)); c.hl(1, 46, 8, g(12)); c.hl(1, 46, 19, g(10))
    for x in (12, 24, 36):
        c.vl(x, 9, 18, g(10))
    c.rect(1, 20, 46, 25, g(10)); c.hl(1, 46, 25, g(9))
    for x in range(2, 46, 6):
        c.px(x, 26, g(9)); c.px(x + 1, 26, g(9))
    for x in (3, 44):
        c.rect(x, 26, x + 1, 31, a(16)); c.vl(x, 26, 31, a(17))
    # 쟁반 둘 (고기 18/17, 뼈 G13)
    for cx in (9, 30):
        c.ell(cx, 13.5, 5, 3, g(7)); c.ell(cx, 13.2, 3.5, 2, a(18)); c.px(cx - 1, 12, a(17)); c.hl(cx + 2, cx + 4, 12, g(13))
    # 촛대 (기둥 G05, 초 G12, 불 23/25)
    for cx in (19, 40):
        c.rect(cx - 1, 9, cx + 1, 12, g(5)); c.vl(cx, 3, 8, g(12))
    # 은잔 (세움)
    c.rect(24, 11, 25, 13, g(9)); c.px(24, 14, g(7)); c.hl(23, 26, 15, g(7))
    # 엎어진 잔 + 쏟아진 포도주
    c.rect(34, 13, 37, 14, g(9)); c.px(33, 12, g(7)); c.px(33, 15, g(7))
    c.outline()
    c.ell(38.5, 15, 3.5, 1.6, a(17), keep=True); c.px(37, 15, a(18), keep=True)
    for y in range(17, 26):
        c.px(41, y, a(17), keep=True)
    c.vl(42, 20, 24, a(16), keep=True)
    c.ell(41.5, 29.5, 3, 1.3, a(17), keep=True); c.px(41, 30, a(16), keep=True)
    for cx in (19, 40):
        c.px(cx, 2, a(25), keep=True); c.px(cx, 1, a(23), keep=True); c.px(cx, 3, X1, keep=True)
    return [c]


def set_hall_rug():
    """연회 깔개(64x48 바닥): 포도주빛 바탕(17) · 금실 테(18) · 안쪽 테 16 · 가운데 마름모 문양 · 짧은 변 술(G09) · 흘린 포도주 얼룩.
    보스·연회 탁자 아래 가운데(center)."""
    c = Cv(64, 48, R1)
    x0, y0, x1, y1 = 4, 4, 59, 43
    c.rect(x0, y0, x1, y1, a(17), keep=True)
    c.rect(x0, y0, x1, y0 + 2, a(18), keep=True); c.rect(x0, y1 - 2, x1, y1, a(18), keep=True)
    c.rect(x0, y0, x0 + 2, y1, a(18), keep=True); c.rect(x1 - 2, y0, x1, y1, a(18), keep=True)
    for (ax, ay, bx, by) in [(x0 + 4, y0 + 4, x1 - 4, y0 + 4), (x0 + 4, y1 - 4, x1 - 4, y1 - 4), (x0 + 4, y0 + 4, x0 + 4, y1 - 4), (x1 - 4, y0 + 4, x1 - 4, y1 - 4)]:
        c.line(ax, ay, bx, by, a(16), keep=True)
    cx, cy = 32, 24
    for k in range(15):                                                 # 가운데 마름모
        for (dx, dy) in ((k, 15 - k), (-k, 15 - k), (k, -(15 - k)), (-k, -(15 - k))):
            c.px(cx + dx, cy + int(dy * 0.66), a(18), keep=True)
    c.ell(cx, cy, 4, 3, a(16), keep=True); c.px(cx, cy - 1, a(18), keep=True)
    for y in range(y0 + 1, y1, 2):                                      # 술(짧은 변)
        c.px(x0 - 1, y, g(9), keep=True); c.px(x0 - 2, y, g(7), keep=True)
        c.px(x1 + 1, y, g(9), keep=True); c.px(x1 + 2, y, g(7), keep=True)
    c.ell(47, 33, 4, 2.4, a(16), keep=True); c.px(45, 32, a(18), keep=True)  # 얼룩
    return [c]


def set_gate_brazier():
    """성문 화톳대(16x32, 서 있음): 세발 다리 G04 · 기둥 G05 · 쇠 그릇 G06 · 불(19~25 + X1). active 4f."""
    fr = []
    for k in range(4):
        c = Cv(16, 32, R1)
        c.line(3, 31, 7, 22, g(4)); c.line(12, 31, 8, 22, g(4)); c.vl(7, 14, 30, g(5)); c.vl(8, 14, 30, g(3))
        c.rect(2, 11, 13, 14, g(6)); c.hl(2, 13, 11, g(8)); c.hl(3, 13, 14, g(4))
        c.outline()
        flame(c, 8, 11, 10, k, w=5)
        flame(c, 5, 11, 6, k + 1, w=3, core=False)
        flame(c, 11, 11, 7, k + 2, w=3, core=False)
        y = 2 - (k % 3)
        if y >= 0:
            c.px(6 + k % 2, y, a(25 if k % 2 else 23), keep=True)
        fr.append(c)
    return fr


# ====================================================================== 전장 소품
def battlefield_weapon():
    """부러진 무기가 꽂힌 자리(16x32) 변형 3: 0 = 칼 + 기댄 창자루, 1 = 도끼창(할버드) 머리만, 2 = 화살 세 대 + 칼자루.
    흙 둔덕(G04/G05) 위. 가는 쇠·나무는 셀아웃 대신 명암 2단(keep)."""
    fr = []
    for v in range(3):
        c = Cv(16, 32, R1)
        c.ell(8, 29, 6.5, 2.6, g(4)); c.ell(7, 28.5, 4.5, 1.6, g(5), only="opaque")
        c.outline()
        if v == 0:
            for y in range(6, 27):                                       # 창자루 (기대어 비스듬)
                x = 11 - (y - 6) // 7
                c.px(x, y, g(7), keep=True); c.px(x + 1, y, g(4), keep=True)
            c.px(12, 5, g(9), keep=True); c.px(11, 4, g(9), keep=True)   # 쪼개진 끝
            for y in range(12, 28):                                       # 칼날 (꽂힘)
                c.px(6, y, g(10), keep=True); c.px(7, y, g(7), keep=True)
            c.hl(3, 10, 11, g(6), keep=True); c.hl(3, 10, 10, g(9), keep=True)   # 코등이
            c.vl(6, 6, 9, g(4), keep=True); c.vl(7, 6, 9, g(3), keep=True); c.px(6, 5, g(7), keep=True)  # 자루 + 머리
            for (x, y, cc) in [(8, 7, 10), (9, 8, 9), (10, 8, 9)]:       # 감긴 천 조각
                c.px(x, y, g(cc), keep=True)
        elif v == 1:
            for y in range(14, 28):
                c.px(8, y, g(6), keep=True); c.px(9, y, g(3), keep=True)
            c.rect(4, 12, 7, 17, g(9), keep=True); c.vl(4, 12, 17, g(10), keep=True); c.px(3, 13, g(9), keep=True); c.px(3, 16, g(9), keep=True)
            c.rect(10, 13, 11, 15, g(7), keep=True); c.px(12, 14, g(7), keep=True)
            c.vl(8, 8, 13, g(9), keep=True); c.px(8, 7, g(10), keep=True)
            c.px(6, 18, g(0), keep=True); c.px(5, 15, g(0), keep=True)   # 이 빠진 날
        else:
            for (x0, y0, dx) in ((4, 16, -1), (8, 13, 0), (12, 17, 1)):
                for k in range(11):
                    c.px(x0 + (dx * k) // 4, y0 + k, g(7), keep=True)
                c.px(x0, y0 - 1, g(10), keep=True); c.px(x0 - 1, y0 - 1, g(9), keep=True); c.px(x0 + 1, y0, g(9), keep=True)
            c.vl(10, 20, 27, g(5), keep=True); c.hl(8, 12, 20, g(7), keep=True); c.px(10, 19, g(7), keep=True)
        c.px(5, 30, g(1), keep=True); c.px(11, 30, g(1), keep=True)
        fr.append(c)
    return fr


def battlefield_banner():
    """찢긴 깃발(16x32): 부러진 깃대(G07/G04) + 찢긴 천(G06 빛 · G05 · 접힌 그늘 G04, 바랜 문장 17, 그을린 끝 16·19).
    idle = 늘어짐, active 4f = 바람에 펄럭임 (천 끝이 오른쪽으로 1~3px 물결). (1회차: 천 5px 는 2배 화면에서 안 읽혀 10px 로)"""
    fr = []
    for k in range(5):
        c = Cv(16, 32, R1)
        c.ell(4, 30, 3.5, 1.4, g(4)); c.outline()
        wave = [0, 1, 2, 1, 0][k] if k else 0
        for j in range(13):
            y = 4 + j
            if k == 0:
                ln = 8 - j // 3
                sh = j // 4
            else:
                ln = 10 - j // 3 + (1 if (j + k) % 4 == 0 else 0)
                sh = int(round(wave * math.sin((j + k * 2) / 3.0)))
            if j in (9, 11) and k:
                ln -= 3                                                    # 찢긴 홈
            for i in range(max(1, ln)):
                x = 5 + i + (sh if i > 2 else 0)
                if x > 15:
                    continue
                col = g(6) if j < 3 else g(5)
                if (i + j * 2 + k) % 7 == 0 and i > 1:
                    col = g(4)
                if i == ln - 1:
                    col = a(16)
                c.px(x, y, col, keep=True)
            if j in (12,) or (k and j == 10):
                c.px(5 + max(1, ln) - 1 + (sh if ln > 3 else 0), y, a(19), keep=True)
        for (x, y) in [(8, 7), (9, 7), (8, 8), (9, 9), (10, 8)]:
            c.px(x + (1 if k in (2, 3) else 0), y, a(17), keep=True)        # 바랜 문장
        for y in range(2, 30):
            c.px(3, y, g(7), keep=True); c.px(4, y, g(4), keep=True)
        c.px(4, 1, g(9), keep=True); c.px(3, 2, g(9), keep=True)
        fr.append(c)
    return fr


def battlefield_fallen():
    """쓰러진 병사의 흔적(32x16, 바닥 근처 y 정렬): 시신은 없다 — 펼쳐진 외투(G03/G04) · 떨어진 투구 · 가슴받이 · 손에서 놓친 칼.
    변형 2: 0 = 창병, 1 = 궁수(부러진 활 + 흩어진 화살)."""
    fr = []
    for v in range(2):
        c = Cv(32, 16, R1)
        c.ell(15, 10, 11, 4.2, g(3)); c.ell(14, 9.5, 9, 3, g(4), only="opaque")             # 외투
        for (x, y) in [(6, 12), (9, 13), (23, 11), (20, 13)]:
            c.px(x, y, g(2), only="opaque")
        c.rect(11, 6, 17, 10, g(7)); c.hl(11, 17, 6, g(9)); c.vl(17, 7, 10, g(5))            # 가슴받이
        c.ell(23.5, 7.5, 3.2, 2.6, g(6)); c.px(22, 6, g(9)); c.hl(20, 27, 9, g(5))           # 투구
        c.outline()
        if v == 0:
            c.line(2, 4, 13, 2, g(7), keep=True); c.line(2, 5, 13, 3, g(4), keep=True)       # 창자루
            c.line(26, 13, 31, 11, g(10), keep=True); c.hl(25, 26, 14, g(6), keep=True)      # 칼
        else:
            for i in range(8):
                x = 2 + i; y = 4 - int(round(2.2 * math.sin(i / 7 * math.pi)))
                c.px(x, y, g(7), keep=True)
            c.px(10, 4, g(9), keep=True); c.px(10, 5, g(0), keep=True)
            for (x, y) in [(26, 12), (28, 9), (29, 13)]:
                c.line(x, y, x + 3, y - 1, g(7), keep=True); c.px(x, y, g(11), keep=True)
        c.px(16, 12, a(17), keep=True); c.px(17, 12, a(17), keep=True)                         # 마른 핏자국 대신 그을음(갈색) 한 점
        fr.append(c)
    return fr


def dummy_body(c, tilt=0, straw_out=0, broken=0):
    """허수아비(16x32): 장대 G05 · 가로대 · 짚 몸통(18/17 + G09 짚 끝) · 낡은 투구 · 찢긴 천(G06). tilt = 위쪽 기울기(px)."""
    def sx(y):
        return (tilt * (28 - y)) // 22
    for y in range(4, 31):
        c.px(7 + sx(y), y, g(6)); c.px(8 + sx(y), y, g(4))
    if broken < 2:
        cy = 13
        c.hl(1 + sx(cy), 14 + sx(cy), cy, g(6)); c.hl(1 + sx(cy), 14 + sx(cy), cy + 1, g(4))   # 가로대
        for y in range(10, 22):
            half = 3 if y < 20 else 2
            for x in range(8 - half, 8 + half + 1):
                xx = x + sx(y)
                col = a(19) if x < 8 else a(18)                                   # 짚 (2회차: 18/17 은 황무지 흙(17)에 묻혔다)
                if (x + y) % 4 == 0:
                    col = a(17)
                c.px(xx, y, col)
        c.rect(5 + sx(6), 4, 10 + sx(6), 9, a(19)); c.vl(10 + sx(6), 5, 9, a(18))          # 짚 머리
        c.rect(4 + sx(4), 3, 11 + sx(4), 5, g(6)); c.hl(4 + sx(4), 11 + sx(4), 3, g(8)); c.hl(3 + sx(5), 12 + sx(5), 6, g(5))   # 투구
        c.rect(5 + sx(15), 15, 10 + sx(15), 18, g(6)); c.hl(5 + sx(15), 10 + sx(15), 15, g(8))   # 천 조끼
        c.px(7 + sx(16), 16, a(21)); c.px(8 + sx(16), 16, a(21))                                 # 과녁 표시
    c.ell(8, 30.5, 4, 1.5, g(4))


def battlefield_dummy():
    """허수아비(16x32, footprint 1x1, solid): idle · hit(기울고 짚이 튐) · broken 3f(무너짐 → 장대만 남음, 마지막 유지)."""
    fr = []
    c = Cv(16, 32, R1); dummy_body(c); c.outline(); fr.append(c)
    c = Cv(16, 32, R1); dummy_body(c, tilt=2); c.outline()
    for (x, y) in [(2, 9), (13, 11), (1, 15), (14, 17)]:
        c.px(x, y, a(18), keep=True)
    c.brighten(1, region=lambda x, y: y < 24)
    fr.append(c)
    c = Cv(16, 32, R1); dummy_body(c, tilt=4); c.outline()
    for (x, y) in [(1, 12), (14, 8), (0, 18), (15, 20), (3, 24), (12, 26)]:
        c.px(x, y, a(18), keep=True)
    fr.append(c)
    c = Cv(16, 32, R1); dummy_body(c, broken=2)
    c.rect(1, 27, 6, 29, a(17)); c.hl(1, 6, 27, a(18)); c.rect(10, 28, 14, 29, a(17))     # 무너진 짚
    c.rect(11, 25, 14, 27, g(6)); c.hl(11, 14, 25, g(8))                                   # 굴러떨어진 투구
    c.outline(); fr.append(c)
    c = Cv(16, 32, R1)
    for y in range(18, 31):
        c.px(7, y, g(6)); c.px(8, y, g(4))
    c.px(7, 17, g(8)); c.px(8, 18, g(9))
    c.ell(8, 30.5, 4, 1.5, g(4))
    c.rect(0, 28, 5, 30, a(17)); c.hl(0, 5, 28, a(18)); c.rect(10, 29, 15, 30, a(17)); c.hl(10, 15, 29, a(18))
    c.rect(11, 26, 14, 28, g(6)); c.hl(11, 14, 26, g(8))
    c.outline(); fr.append(c)
    return fr


# ====================================================================== 튜토리얼 표식 (땅에 새긴 고리 + 글리프)
GLYPHS = {
    "move": ["...#...", "..###..", "...#...", "#.....#", "##...##", "#.....#", "...#...", "..###..", "...#..."],
    "attack": ["......#", ".....#.", "....#..", "...#...", "..#....", ".#.#...", "#...#..", "......."],
    "dash": ["#...#..", ".#...#.", "..#...#", ".#...#.", "#...#.."],
    "skill": ["...#...", "...#...", "#.###.#", ".#####.", "#.###.#", "...#...", "...#..."],
}


def sign_frames(kind=None):
    """32x32 바닥(셀아웃 없음): 타원 고리(rx 13.5, ry 8.5, 가운데 (16,22)) + 가운데 글리프.
    idle 0 = 땅에 새긴 홈(G01 홈 · G04 빛 받는 아랫테), active 1~4 = 홈을 따라 도는 잔불(21/23/25) + 위로 오르는 불티,
    done 5 = 다 탄 고리(G05 재 + 꺼진 불씨 19 한 점)."""
    fr = []
    cx, cy, rx, ry = 16, 22, 13.5, 8.5
    ring = []
    for y in range(32):
        for x in range(32):
            d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
            if 0.84 <= d <= 1.0:
                ring.append((x, y, math.atan2(y + 0.5 - cy, x + 0.5 - cx)))
    gl = GLYPHS.get(kind)
    gpts = []
    if gl:
        gh, gw = len(gl), len(gl[0])
        ox, oy = cx - gw // 2, cy - gh // 2
        gpts = [(ox + i, oy + j) for j, r in enumerate(gl) for i, ch in enumerate(r) if ch == "#"]

    def base(c, groove, lip, glyph_c, glyph_lip):
        for (x, y, ang) in ring:
            c.px(x, y, g(groove), keep=True)
        for (x, y, ang) in ring:                                    # 아래쪽(빛 받는 턱) 1px
            if math.sin(ang) > 0.35 and (x, y + 1) not in {(p[0], p[1]) for p in ring}:
                c.px(x, y + 1, g(lip), keep=True)
        for (x, y) in gpts:
            c.px(x, y, g(glyph_c), keep=True)
            if (x, y + 1) not in gpts:
                c.px(x, y + 1, g(glyph_lip), keep=True)

    c = Cv(32, 32, R1)
    base(c, 1, 4, 1, 4)
    fr.append(c)
    for k in range(4):
        c = Cv(32, 32, R1)
        base(c, 1, 4, 1, 4)
        for (x, y, ang) in ring:
            ph = (ang / (2 * math.pi) * 8 - k * 0.5) % 2
            c.px(x, y, a(19) if ph < 1 else a(21), keep=True)
            if ph < 0.25:
                c.px(x, y, a(23), keep=True)
        for (x, y) in gpts:
            c.px(x, y, a(23) if (x + y + k) % 3 else a(25), keep=True)
            if (x, y + 1) not in gpts:
                c.px(x, y + 1, a(19), keep=True)
        for i, (x0, y0) in enumerate([(6, 18), (26, 17), (12, 14), (21, 13)]):
            y = y0 - (k * 2 + i * 3) % 8
            c.px(x0 + (k + i) % 2, y, a(25 if (i + k) % 2 else 23), keep=True)
        fr.append(c)
    c = Cv(32, 32, R1)
    base(c, 5, 3, 5, 3)
    c.px(int(cx + rx * 0.7), int(cy + ry * 0.7), a(19), keep=True)
    fr.append(c)
    return fr


# ====================================================================== 등록 · 내보내기
REG = []


def reg(sid, frames, states, durs, footprint, solid, depth, note, loops=None, extra=None, budget="gray<=10 accent<=5", fire=False):
    REG.append((sid, frames, dict(states=states, durations=durs, footprint=footprint, solid=solid, depth=depth, note=note,
                                  loops=loops or {}, extra=extra or {}, budget=budget, fire=fire)))


def palette_info(frames):
    used = set()
    for f in frames:
        used |= set(f.p.values())
    gray = sorted(G.index(c) for c in used if c in G)
    acc = sorted(16 + R1.index(c) for c in used if c in R1)
    core = sorted(c for c in used if c in (X0, X1) and c not in G)
    other = sorted(c for c in used if c not in G and c not in R1 and c not in (X0, X1))
    return gray, acc, core, other


def export(sid, frames, m):
    w, h = frames[0].w, frames[0].h
    assert len(m["durations"]) == len(frames), sid
    assert "idle" in m["states"] and all(0 <= i < len(frames) for v in m["states"].values() for i in v), sid
    SB.sheet_png(frames).save(os.path.join(OUT, sid + ".png"))
    gray, acc, core, other = palette_info(frames)
    d = {
        "image": sid + ".png", "action": sid, "frameWidth": w, "frameHeight": h, "frames": len(frames),
        "directions": ["any"], "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column",
        "fps": round(1000.0 / (sum(m["durations"]) / len(m["durations"])), 2),
        "frameDurationsMs": m["durations"], "loop": False, "pivot": {"x": w // 2, "y": h},
        "footprint": m["footprint"], "solid": m["solid"], "depth": m["depth"], "states": m["states"],
        "stateLoop": {k: bool(m["loops"].get(k, False)) for k in m["states"]},
        "floor": "stage1", "paletteSwap": False, "interact": m["extra"].pop("interact", None),
        "pivotNote": "pivot (w/2, h) = 프레임 아래 가장자리 가운데 = footprint 아래 변 가운데. footprint 는 프레임 아래쪽에 붙고 가로 가운데 정렬.",
        "palette": "parts/art/palette/lopad.json — gray G%s + accent %s drawn in stage1 (floor 1 amber) ramp (not swapped)%s" % (
            ",".join("%02d" % i for i in gray), ",".join(str(i) for i in acc), " + fx core X1" if core else ""),
        "colors": {"gray": len(gray), "accent": len(acc), "core": len(core), "budget": m["budget"]},
        "source": "parts/art/work/structures/build_sets.py (round 49)",
        "note": m["note"],
    }
    d.update(m["extra"])
    with open(os.path.join(OUT, sid + ".json"), "w", encoding="utf-8") as fp:
        json.dump(d, fp, ensure_ascii=False, indent=1)
    lim = (10, 8, 2) if m["fire"] else (10, 5, 0)
    ok = len(gray) <= lim[0] and len(acc) <= lim[1] and len(core) <= lim[2] and not other
    print("%-28s %2d f %2dx%-2d fp %s %-5s %-5s gray %2d acc %d core %d %s" % (
        sid, len(frames), w, h, m["footprint"], m["depth"], m["solid"], len(gray), len(acc), len(core), "OK" if ok else "OVER %s" % other))
    return ok


def build_all():
    REG.clear()
    reg("set_waste_fire_ring", set_waste_fire_ring(), {"idle": [0]}, [200], [4, 3], False, "floor",
        "49라운드 7절 세트 배치 — 황무지·전장의 휴식 자리: 밟혀 다져진 흙 고리 + 둘레 돌 + 앉을 통나무 셋 + 담요·냄비. 가운데 setAnchor 에 bonfire.",
        extra={"setAnchor": {"x": 32, "y": 34}, "setFor": ["bonfire"], "setRole": "ring", "region": "waste"})
    reg("set_outer_plaza", set_outer_plaza(), {"idle": [0]}, [200], [4, 3], False, "floor",
        "49라운드 7절 세트 배치 — 외곽 거리 한가운데 둥근 광장 돌 문양(연석 + 동심원 돌 + 가운데 배수 뚜껑). 휴식(bonfire)·상점(set_outer_stall)·이벤트 구조물을 이 위 가운데에.",
        extra={"setAnchor": {"x": 32, "y": 32}, "setFor": ["bonfire", "set_outer_stall", "chest", "grave"], "setRole": "center", "region": "outer"})
    reg("set_outer_lamppost", set_outer_lamppost(), {"idle": [0], "active": [0, 1, 2, 3]}, [160, 130, 170, 140], [1, 1], True, "y",
        "49라운드 7절 — 거리 등불 기둥. 광장·노점 둘레(edge)에 2~4개. active = 불빛 흔들림 루프.",
        loops={"active": True}, extra={"setRole": "edge", "region": "outer"}, budget="gray<=10 accent<=8 core<=2", fire=True)
    reg("set_outer_stall", set_outer_stall(), {"idle": [0]}, [200], [3, 1], True, "y",
        "49라운드 7절 — 상점 노드 가운데 노점: 줄무늬 천막 + 좌판(술병·항아리·자루·저울). 강조 25 표지 = 저울(상호작용 자리).",
        extra={"setRole": "center", "region": "outer", "interact": "E"})
    reg("set_outer_stall_side", set_outer_stall_side(), {"idle": [0]}, [200], [2, 1], True, "y",
        "49라운드 7절 — 노점 양옆 손수레(궤짝·자루·덮개 천). 상점 노점 거리의 곁(flank).",
        extra={"setRole": "flank", "region": "outer"})
    reg("set_brewery_barrel_stack", set_brewery_barrel_stack(), {"idle": [0]}, [200], [3, 1], True, "y",
        "49라운드 7절 — 양조 구역 술통 더미(3+2+1). 증류기(still)·술독(cask) 둘레(flank)·광장 가장자리.",
        extra={"setRole": "flank", "region": "brewery"})
    reg("set_hall_long_table", set_hall_long_table(), {"idle": [0]}, [200], [3, 1], True, "y",
        "49라운드 7절 — 지배자의 연회장 긴 탁자: 흰 식탁보 + 쟁반·은잔·촛대 + 엎어진 잔에서 흘러내린 포도주. 보스방 양옆·연회 이벤트 가운데.",
        extra={"setRole": "flank", "region": "hall"}, budget="gray<=10 accent<=8 core<=2", fire=True)
    reg("set_hall_rug", set_hall_rug(), {"idle": [0]}, [200], [4, 3], False, "floor",
        "49라운드 7절 — 연회 깔개(포도주빛 + 금실 테 + 가운데 마름모, 흘린 포도주). 보스·연회 탁자 아래 가운데.",
        extra={"setAnchor": {"x": 32, "y": 40}, "setFor": ["set_hall_long_table", "boss"], "setRole": "center", "region": "hall"})
    reg("set_gate_brazier", set_gate_brazier(), {"idle": [0], "active": [0, 1, 2, 3]}, [110, 120, 110, 130], [1, 1], True, "y",
        "49라운드 7절 — 성문 앞 화톳대(세발 쇠 그릇 + 불). 성문 노드 광장 양옆(edge).",
        loops={"active": True}, extra={"setRole": "edge", "region": "gate"}, budget="gray<=10 accent<=8 core<=2", fire=True)
    # 전장
    reg("battlefield_weapon", battlefield_weapon(), {"idle": [0]}, [200, 200, 200], [1, 1], False, "y",
        "49라운드 3절 전장 탄생지 — 부러진 무기가 꽂힌 흙 둔덕. 변형 3(variants): 0 칼+기댄 창자루, 1 도끼창 머리, 2 화살 셋+칼자루. 통과 가능(작은 장식).",
        extra={"variants": [0, 1, 2], "variantsNote": "시스템이 variants 를 읽으면 배치마다 하나를 골라 1프레임으로 쓴다(없으면 idle=0).", "region": "waste"})
    reg("battlefield_banner", battlefield_banner(), {"idle": [0], "active": [1, 2, 3, 4]}, [200, 140, 140, 140, 140], [1, 1], False, "y",
        "49라운드 3절 — 부러진 깃대에 찢긴 깃발(바랜 문장, 그을린 끝의 잔불 19). active = 바람에 펄럭임 루프.",
        loops={"active": True}, extra={"region": "waste"})
    reg("battlefield_fallen", battlefield_fallen(), {"idle": [0]}, [200, 200], [2, 1], False, "y",
        "49라운드 3절 — 쓰러진 병사의 흔적(시신 없음): 펼쳐진 외투·가슴받이·투구·무기. 변형 2(variants): 0 창병, 1 궁수. 통과 가능.",
        extra={"variants": [0, 1], "region": "waste"})
    reg("battlefield_dummy", battlefield_dummy(), {"idle": [0], "hit": [1], "broken": [2, 3, 4]}, [200, 90, 80, 120, 200], [1, 1], True, "y",
        "49라운드 3절 튜토리얼 허수아비: 짚 몸통 + 낡은 투구 + 천 조끼(과녁 19). hit = 기울며 짚이 튐(밝게), broken = 무너짐 → 장대만(마지막 유지). 적 시트 dummy_idle 과 별개의 '전장 소품' 판.",
        extra={"interact": "hit", "region": "waste"})
    durs = [200, 110, 110, 110, 110, 200]
    for kind in (None, "move", "attack", "dash", "skill"):
        sid = "tutorial_sign" + ("_" + kind if kind else "")
        reg(sid, sign_frames(kind), {"idle": [0], "active": [1, 2, 3, 4], "used": [5], "done": [5]}, durs, [2, 1], False, "floor",
            "49라운드 3절 튜토리얼 땅의 표식%s: 땅에 새긴 고리. idle = 새긴 홈(꺼짐), active = 홈을 따라 도는 잔불 + 오르는 불티(안내 중, 루프), done(=used) = 다 탄 재 고리. 키 안내 글자는 UI 몫." % (
                (" — 글리프 '%s'" % kind) if kind else " (글리프 없음, 범용)"),
            loops={"active": True}, extra={"glyph": kind or "none", "doneAlias": "used", "region": "waste"}, budget="gray<=10 accent<=5")


# ====================================================================== 미리보기 (시트 3배 · 세트 배치 2배)
def preview_sheet():
    S, gap = 3, 8
    rows = []
    for sid, frames, m in REG:
        w, h = frames[0].w * S, frames[0].h * S
        rows.append((sid, frames, m, w, h))
    W = max(len(f) * (w + 4) for _, f, _, w, _ in rows) + 2 * gap
    W = min(W, 1600)
    # 두 단 배치
    img = Image.new("RGB", (1600, 10), (40, 40, 44))
    y, x, col_h = gap, gap, 0
    placed = []
    for sid, frames, m, w, h in rows:
        need = len(frames) * (w + 4)
        if x + need > 1600 - gap:
            x = gap; y += col_h + 22; col_h = 0
        placed.append((sid, frames, m, x, y, w, h))
        x += need + 16
        col_h = max(col_h, h)
    H = y + col_h + 30
    img = Image.new("RGB", (1600, H), (40, 40, 44))
    d = ImageDraw.Draw(img)
    from rkit import FONT_S
    for sid, frames, m, x, y, w, h in placed:
        d.text((x, y), "%s %dx%d %s" % (sid, frames[0].w, frames[0].h, m["depth"]), fill=(225, 225, 225), font=FONT_S)
        for i, f in enumerate(frames):
            bg = Image.new("RGBA", (f.w, f.h), SB.rgb(G[2]) + (255,))
            bg.alpha_composite(f.image())
            img.paste(bg.resize((w, h), Image.NEAREST).convert("RGB"), (x + i * (w + 4), y + 16))
    img.save(os.path.join(HERE, "preview_sets.png"))


def set_scenes():
    import rkit as K
    import importlib
    T = K.T
    sheets = {}

    def sheet(region):
        if region not in sheets:
            mod = importlib.import_module(region)
            sheets[region] = K.RegionSheet(region, mod.NAME, mod.tiles(), mod.PROPS, os.path.join(HERE, "..", "tiles_regions", region))
        return sheets[region]

    def frame_of(sid, state="idle", k=0):
        for s, frames, m in REG:
            if s == sid:
                st = m["states"].get(state, m["states"]["idle"])
                return frames[st[min(k, len(st) - 1)]].image(), m
        return None

    def put_set(a, sid, tx, ty, state="idle", k=0, dx=0, dy=0):
        """세트 소품: footprint 왼쪽 아래 타일 (tx, ty) 기준, 피벗 = footprint 아래 변 가운데."""
        im, m = frame_of(sid, state, k)
        fw = m["footprint"][0]
        a.put(im, (im.width // 2, im.height), tx * T + fw * T // 2 + dx, (ty + 1) * T + dy, floor=(m["depth"] == "floor"))

    def put_at_anchor(a, set_sid, center_sid, tx, ty, state="active"):
        """setAnchor 규칙 시험: 세트(바닥) 를 (tx,ty) 에, 가운데 구조물 피벗을 setAnchor 점에."""
        im, m = frame_of(set_sid)
        fx, fy = tx * T + m["footprint"][0] * T // 2, (ty + 1) * T
        a.put(im, (im.width // 2, im.height), fx, fy, floor=True)
        anc = m["extra"]["setAnchor"]
        ax, ay = fx - im.width // 2 + anc["x"], fy - im.height + anc["y"]
        if center_sid.startswith("set_"):
            cim, cm = frame_of(center_sid)
            a.put(cim, (cim.width // 2, cim.height), ax, ay)
        else:
            cim, cm = K.state_sprite("structures", center_sid, state, 0)
            a.put(cim, (cm["pivot"]["x"], cm["pivot"]["y"]), ax, ay)

    out = []
    # 1) 외곽 거리 휴식 광장: 광장 문양 + 모닥불 + 등불 넷 + 술통·벤치 대신 통나무
    sh = sheet("outer")
    a = K.Arena(sh, "rest", (1, 2, 28, 15), seed=31)
    put_at_anchor(a, "set_outer_plaza", "bonfire", 13, 11)
    for (tx, ty) in ((10, 8), (17, 8), (10, 12), (17, 12)):
        put_set(a, "set_outer_lamppost", tx, ty, "active", tx % 4)
    a.put_struct("barrel", 4, 4); a.put_struct("barrel", 5, 4); a.put_struct("crate_f1", 24, 13)
    a.prop(3, 13, sh.prop_names[1]); a.prop(25, 4, sh.prop_names[7])
    a.put_char("player", "player_idle", 0, 0, 14 * T + 8, 13 * T + 4)
    out.append(("외곽 거리 · 휴식 광장 (set_outer_plaza + bonfire + set_outer_lamppost x4)", a.render()))
    # 2) 외곽 거리 상점: 광장 문양 위 노점 + 양옆 손수레 + 등불
    a = K.Arena(sh, "floor", (1, 2, 28, 15), seed=37)
    put_at_anchor(a, "set_outer_plaza", "set_outer_stall", 13, 10)
    put_set(a, "set_outer_stall_side", 9, 10); put_set(a, "set_outer_stall_side", 18, 10)
    for (tx, ty) in ((8, 12), (21, 12)):
        put_set(a, "set_outer_lamppost", tx, ty, "active", 1)
    a.put_struct("barrel", 5, 5); a.prop(24, 5, sh.prop_names[5]); a.prop(3, 14, sh.prop_names[6])
    a.put_char("player", "player_idle", 1, 0, 14 * T + 8, 14 * T + 4)
    out.append(("외곽 거리 · 상점 노점 거리 (set_outer_plaza + set_outer_stall + set_outer_stall_side x2)", a.render()))
    # 3) 황무지 휴식: 불 둘레 + 모닥불 + 전장 소품
    sh = sheet("waste")
    a = K.Arena(sh, "rest", (1, 2, 28, 15), seed=41)
    put_at_anchor(a, "set_waste_fire_ring", "bonfire", 13, 11)
    put_set(a, "battlefield_banner", 6, 6, "active", 1); put_set(a, "battlefield_weapon", 22, 5)
    put_set(a, "battlefield_fallen", 21, 13); put_set(a, "battlefield_weapon", 4, 13, "idle")
    a.prop(9, 14, sh.prop_names[6]); a.prop(25, 9, sh.prop_names[1]); a.prop(3, 8, sh.prop_names[7])
    a.put_char("player", "player_idle", 2, 0, 18 * T + 8, 10 * T + 4)
    out.append(("황무지 · 휴식 야영 자리 (set_waste_fire_ring + bonfire + battlefield_*)", a.render()))
    # 4) 연회장 보스: 깔개 + 긴 탁자 둘 + 촛대
    sh = sheet("hall")
    a = K.Arena(sh, "trial", (1, 2, 28, 15), seed=43)
    put_at_anchor(a, "set_hall_rug", "set_hall_long_table", 13, 12)
    put_set(a, "set_hall_long_table", 4, 6); put_set(a, "set_hall_long_table", 22, 6)
    put_set(a, "set_hall_long_table", 4, 14); put_set(a, "set_hall_long_table", 22, 14)
    a.prop(9, 9, sh.prop_names[0]); a.prop(18, 13, sh.prop_names[1]); a.prop(12, 4, sh.prop_names[2]); a.prop(17, 4, sh.prop_names[2])
    a.put_char("player", "player_idle", 1, 0, 14 * T + 8, 14 * T + 12)
    out.append(("지배자의 연회장 · 연회 (set_hall_rug + set_hall_long_table x5)", a.render()))
    return out


def preview_scenes():
    import rkit as K
    sc = set_scenes()
    W, H, gap = 960, 540, 8
    out = Image.new("RGB", (2 * W + 3 * gap, 2 * H + 3 * gap), (40, 40, 44))
    for i, (lab, img) in enumerate(sc):
        big = K.x2(img).convert("RGB")
        K.label(big, lab)
        big.save(os.path.join(HERE, "preview_sets_x2_%d.png" % i))
        out.paste(big, (gap + (i % 2) * (W + gap), gap + (i // 2) * (H + gap)))
    out.save(os.path.join(HERE, "preview_sets_x2.png"))


def main():
    build_all()
    ok = True
    for sid, frames, m in REG:
        ok &= export(sid, frames, m)
    print("palette budget:", "PASS" if ok else "FAIL")
    preview_sheet()
    preview_scenes()


if __name__ == "__main__":
    main()
