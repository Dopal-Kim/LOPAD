#!/usr/bin/env python3
# [53라운드 보관] 이 스크립트가 미리보기·목업·마스크 입력으로 읽던 구 시트(assets/sprites/player/player_*, player/v2/*, enemies/{dummy,archer,charger}_*, enemies/v2/*, weapons/katana_* 중 아이콘 외, weapons/v2/*)는 삭제됨 — 해당 단계는 재실행 시 FileNotFoundError.
"""LOPAD 상호작용 구조물 시트 (47라운드, 계약 art-assets §5) + fx/fire_pool (§3).

근거: parts/producer/decisions/2026-10-02-round-47-structures-impl.md · contracts/art-assets.md §5
외형 메모: parts/system/structures-draft.md "외형(아트 요청)" (교차 참조 승인 #15)
층 분위기: 1층 '잔'(술독·증류·외상, 호박) / 2층 '패'(카드·칩·종·투견, 카지노 녹색)
아트 바이블 37·40라운드: 버려진 구역의 흙바닥, 잔불처럼 올라오는 도트, 처절·삭막, 주인공 대비 유지.

출력: assets/sprites/structures/<id>.png + .json (1행 = directions ["any"], 열 = 프레임, 패딩 0)
      assets/sprites/fx/fire_pool.png + .json
미리보기: preview.png (3배 시트 + 1·2층 바닥 위 1배 목업), preview_mock_x2.png (960x540 근사 확인용)

규칙 요약
  * 색: 무채 16 + 층 강조 램프(16~27). 공통(crate_f1·chest·grave·bonfire)은 1층 램프로 그려 런타임 스왑 대상,
    crate_f2 와 2층 테마는 2층 램프로 그린다(스왑돼도 1층 램프 색이 없으니 그대로 남는다).
    불·발광(bonfire·still·fire_pool)만 백열 코어 X0/X1 허용. UI 세피아·무기 보조 램프 금지.
  * 셀아웃 G00 1px(inside) + 우·하 림 G04 (40라운드 캐릭터 규칙과 같은 언어 — 어두운 흙바닥에서 덩어리가 산다).
    바닥형(dog_ring·roulette·fire_pool)은 셀아웃 없음.
  * 본체 무채는 G05~G10 (소품 G03~G06 보다 한 단 밝게) → 소품과 명도로 구분. 상호작용 대상은 강조 25(glow) 1점 '불씨'.
  * 피벗 = (w/2, h): 프레임 아래 가장자리 가운데 = 발판(footprint) 아래 변 가운데.
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "sprites", "structures")
OUT_FX = os.path.join(ROOT, "assets", "sprites", "fx")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8") as fp:
    PAL = json.load(fp)
G = PAL["gray"]
R1 = PAL["floors"][0]["ramp"]
R2 = PAL["floors"][1]["ramp"]
X0, X1 = PAL["fx"]["core"]
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


# ====================================================================== 캔버스
class Cv:
    """작은 픽셀 캔버스. p[(x,y)] = '#hex'. keep = 셀아웃에서 제외할 픽셀(불꽃·글린트·가는 끈)."""

    def __init__(self, w, h, R):
        self.w, self.h, self.R = w, h, R
        self.p = {}
        self.keep = set()

    # 색 단축
    def a(self, i):
        return self.R[i - 16]

    def px(self, x, y, c, keep=False, only=None):
        x, y = int(x), int(y)
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        if only == "opaque" and (x, y) not in self.p:
            return
        if only == "empty" and (x, y) in self.p:
            return
        if isinstance(only, (set, list, tuple)) and self.p.get((x, y)) not in only:
            return
        if c is None:
            self.p.pop((x, y), None)
            self.keep.discard((x, y))
            return
        self.p[(x, y)] = c
        if keep:
            self.keep.add((x, y))
        else:
            self.keep.discard((x, y))

    def get(self, x, y):
        return self.p.get((x, y))

    def rect(self, x0, y0, x1, y1, c, **k):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c, **k)

    def hl(self, x0, x1, y, c, **k):
        self.rect(min(x0, x1), y, max(x0, x1), y, c, **k)

    def vl(self, x, y0, y1, c, **k):
        self.rect(x, min(y0, y1), x, max(y0, y1), c, **k)

    def line(self, x0, y0, x1, y1, c, **k):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.px(x0, y0, c, **k)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def ell(self, cx, cy, rx, ry, c, **k):
        """연속 좌표 중심 (cx,cy), 반지름 rx,ry. 픽셀 중심이 안에 들면 칠한다."""
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.px(x, y, c, **k)

    def ring(self, cx, cy, rx, ry, c, t=1.0, **k):
        for y in range(int(cy - ry - 2), int(cy + ry + 3)):
            for x in range(int(cx - rx - 2), int(cx + rx + 3)):
                d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
                if 1.0 - t / min(rx, ry) < d <= 1.0:
                    self.px(x, y, c, **k)

    def blit(self, rows, ox, oy, cmap, keep=False):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in ". ":
                    continue
                self.px(ox + i, oy + j, cmap[ch], keep=keep)

    def outline(self, c=None, rim=None, sides="rb"):
        """셀아웃(inside): 투명 4-이웃이 있는 픽셀 → G00. 그중 오른쪽/아래가 투명이면 림 G04."""
        c = c or G[0]
        rim = rim or G[4]
        edge = []
        for (x, y) in list(self.p):
            if (x, y) in self.keep:
                continue
            n = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
            if any(q not in self.p for q in n):
                edge.append((x, y))
        for (x, y) in edge:
            self.p[(x, y)] = c
        if rim:
            for (x, y) in edge:
                if ("r" in sides and (x + 1, y) not in self.p) or ("b" in sides and (x, y + 1) not in self.p):
                    self.p[(x, y)] = rim

    def shift(self, dx, dy):
        self.p = {(x + dx, y + dy): c for (x, y), c in self.p.items() if 0 <= x + dx < self.w and 0 <= y + dy < self.h}
        self.keep = {(x + dx, y + dy) for (x, y) in self.keep}

    def copy(self):
        n = Cv(self.w, self.h, self.R)
        n.p = dict(self.p)
        n.keep = set(self.keep)
        return n

    def brighten(self, steps=1, region=None):
        """무채 픽셀을 steps 단 밝게 (타격 프레임의 '번쩍'). region(x,y)->bool 로 제한."""
        for (x, y), c in list(self.p.items()):
            if region and not region(x, y):
                continue
            if c in G:
                i = G.index(c)
                if 0 < i < 15:
                    self.p[(x, y)] = G[min(14, i + steps)]

    def image(self):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        for (x, y), c in self.p.items():
            im.putpixel((x, y), rgb(c) + (255,))
        return im


def g(i):
    return G[i]


def rr(v):
    """반올림 (파이썬 round 의 짝수 반올림을 피한다)."""
    return int(math.floor(v + 0.5))


# ====================================================================== 공용 조각
def dust(c, pts, col=None):
    for (x, y) in pts:
        c.px(x, y, col or g(6), keep=True)


def shard(c, x, y, kind=0, lit=None, dark=None):
    """파편 3~4px 덩어리 (윤곽 없이 명암 2단 + 아래 G00 한 점)."""
    lit = lit or g(8)
    dark = dark or g(5)
    shapes = [
        [(0, 0, lit), (1, 0, lit), (0, 1, dark), (1, 1, g(0))],
        [(0, 0, lit), (1, 1, dark), (0, 1, dark), (2, 1, g(0))],
        [(1, 0, lit), (0, 1, lit), (1, 1, dark), (1, 2, g(0))],
        [(0, 0, lit), (1, 0, dark), (2, 0, g(0))],
    ]
    for dx, dy, col in shapes[kind % 4]:
        c.px(x + dx, y + dy, col, keep=True)


def beacon(c, x, y, big=False):
    """상호작용 표지: 강조 25(glow) 1점 + 23 받침. big 이면 위에 27 1점."""
    c.px(x, y, c.a(25), keep=True)
    c.px(x, y + 1, c.a(23), keep=True)
    if big:
        c.px(x, y - 1, c.a(27), keep=True)


def puddle(c, cx, cy, rx, ry, shine=True, dim=False):
    """독주 고임: 17 테두리 → 19 몸 → 21 반사 1~2px."""
    c.ell(cx, cy, rx, ry, c.a(17), keep=True)
    if not dim:
        c.ell(cx - 0.5, cy - 0.3, max(1, rx - 1.2), max(0.8, ry - 0.8), c.a(19), keep=True)
    if shine:
        c.px(int(cx - rx / 2), int(cy - ry / 2), c.a(21 if dim else 23), keep=True)


# ====================================================================== C1 crate_f1 — 금 간 술동이 (16x16)
def jar_body(c, dx=0, dy=0, crack=1):
    cx, cy = 8 + dx, 10.5 + dy
    c.ell(cx, cy, 6.6, 5.2, g(6))
    c.ell(cx + 1.2, cy + 1.0, 5.6, 4.4, g(5), only="opaque")      # 그늘 (우하)
    c.ell(cx - 1.6, cy - 1.6, 3.2, 2.6, g(7), only="opaque")      # 빛 (좌상)
    c.px(cx - 3, cy - 3, g(9), only="opaque")
    c.px(cx - 2, cy - 3, g(8), only="opaque")
    # 목 + 묶은 천 뚜껑
    c.rect(5 + dx, 3 + dy, 10 + dx, 5 + dy, g(6))
    c.hl(5 + dx, 6 + dx, 4 + dy, g(7))
    c.rect(4 + dx, 1 + dy, 11 + dx, 3 + dy, g(10))                 # 천
    c.hl(5 + dx, 8 + dx, 1 + dy, g(12))
    c.px(10 + dx, 3 + dy, g(8))
    c.hl(4 + dx, 11 + dx, 4 + dy, g(4))                            # 끈
    c.px(11 + dx, 5 + dy, g(4))                                    # 끈 꼬리
    # 새끼줄 띠
    for x in range(1, 15):
        c.px(x + dx, int(cy) + dy, g(4), only="opaque")
    c.px(3 + dx, int(cy) + 1 + dy, g(4), only="opaque")       # 매듭 꼬리
    c.px(3 + dx, int(cy) + dy, g(7), only="opaque")
    # 금 (목 → 배), 틈으로 새는 호박
    pts = [(9, 6), (9, 7), (10, 8), (10, 9), (9, 10), (9, 11)]
    if crack >= 2:
        pts += [(8, 12), (8, 13), (11, 7)]
    for (x, y) in pts:
        c.px(x + dx, y + dy, g(0), only="opaque")
    c.px(11 + dx, 9 + dy, c.a(21), keep=True)
    c.px(10 + dx, 11 + dy, c.a(19), keep=True)


def crate_f1_frames(R):
    fr = []
    c = Cv(16, 16, R)
    jar_body(c)
    c.outline()
    beacon(c, 11, 8)
    fr.append(c)
    # hit: 1px 밀림 + 빛 쪽 한 단 밝게 + 금 커짐 + 튀는 방울
    c = Cv(16, 16, R)
    jar_body(c, dx=1, crack=2)
    c.outline()
    c.brighten(1, region=lambda x, y: x < 9)
    c.px(13, 7, c.a(23), keep=True)
    c.px(14, 6, c.a(21), keep=True)
    c.px(12, 9, c.a(25), keep=True)
    fr.append(c)
    # broken 4f
    for k in range(4):
        c = Cv(16, 16, R)
        # 남은 밑동 (깨진 테두리)
        top = [11, 12, 13, 13][k]
        c.ell(8, 14, 5.5, 2.6, g(5))
        c.ell(7, 13.5, 3.5, 1.6, g(6), only="opaque")
        for x in range(3, 13):
            jag = top + ((x * 7) % 3) - 1
            for y in range(jag, 12):
                c.px(x, y, g(6) if x < 8 else g(5))
        c.rect(5, top, 10, top, g(1), only="opaque")  # 깨진 속 어둠
        c.outline()
        if k == 0:
            shard(c, 2, 5, 0); shard(c, 11, 3, 1); shard(c, 6, 2, 2, lit=g(10), dark=g(8)); shard(c, 13, 8, 3)
            for (x, y) in [(5, 7), (10, 6), (8, 5)]:
                c.px(x, y, c.a(23), keep=True)
            c.px(9, 8, c.a(25), keep=True)
        elif k == 1:
            shard(c, 1, 8, 0); shard(c, 13, 6, 1); shard(c, 5, 4, 2, lit=g(10), dark=g(8)); shard(c, 14, 11, 3)
            puddle(c, 8, 15, 5, 1.2)
            c.px(4, 9, c.a(21), keep=True)
            c.px(12, 8, c.a(21), keep=True)
        else:
            shard(c, 0, 12, 0); shard(c, 13, 13, 1); shard(c, 3, 10, 2, lit=g(10), dark=g(8)); shard(c, 12, 10, 3)
            puddle(c, 8, 15.2, 6.5 if k == 3 else 6, 1.0, shine=(k == 2), dim=(k == 3))
        fr.append(c)
    return fr


# ====================================================================== C1 crate_f2 — 칩 상자 + 찢어진 카드 (16x16, 2층 램프)
def chipbox_body(c, dx=0):
    # 상자 윗면(y5..8) + 앞면(y9..15)
    c.rect(1 + dx, 5, 14 + dx, 8, g(7))
    c.rect(1 + dx, 9, 14 + dx, 15, g(5))
    c.hl(1 + dx, 14 + dx, 9, g(8))                 # 모서리 빛
    c.vl(5 + dx, 10, 15, g(4)); c.vl(10 + dx, 10, 15, g(4))
    c.hl(2 + dx, 13 + dx, 12, g(6))                 # 널 결
    c.px(3 + dx, 14, g(9)); c.px(12 + dx, 14, g(9))  # 못
    c.rect(2 + dx, 6, 13 + dx, 7, g(3))             # 열린 속 (어둠)
    # 칩 더미 (상자 속에서 넘침): 녹색 원판
    for (x, y, col) in [(3, 5, 21), (4, 5, 21), (5, 5, 19), (3, 4, 23), (4, 4, 23),
                        (8, 6, 21), (9, 6, 19), (8, 5, 23)]:
        c.px(x + dx, y, c.a(col))
    # 찢어진 카드 (비스듬히 위로 걸침)
    card = ["..dd.",
            ".dddd",
            "dddcd",
            "ddcc.",
            ".cc.."]
    c.blit(card, 9 + dx, 1, {"d": g(13), "c": g(10)})
    c.px(11 + dx, 2, c.a(21))                          # 카드 무늬 1점
    # 바닥에 흘린 칩
    c.px(14 + dx, 15, c.a(19))


def crate_f2_frames(R):
    fr = []
    c = Cv(16, 16, R)
    chipbox_body(c)
    c.outline()
    beacon(c, 4, 4)
    fr.append(c)
    c = Cv(16, 16, R)
    chipbox_body(c, dx=1)
    c.outline()
    c.brighten(1, region=lambda x, y: x < 9)
    c.px(6, 2, c.a(23), keep=True); c.px(2, 3, c.a(21), keep=True)
    fr.append(c)
    for k in range(4):
        c = Cv(16, 16, R)
        # 부서진 판자 더미
        c.rect(2, 13, 12, 15, g(5))
        c.hl(2, 7, 13, g(7))
        c.line(9, 12, 13, 14, g(6))
        c.outline()
        if k == 0:
            shard(c, 1, 6, 0, lit=g(7), dark=g(5)); shard(c, 12, 5, 1, lit=g(7), dark=g(5))
            shard(c, 7, 3, 2, lit=g(13), dark=g(10))
            for (x, y) in [(4, 8), (10, 7), (6, 10), (11, 10)]:
                c.px(x, y, c.a(23), keep=True)
            c.px(8, 8, c.a(25), keep=True)
        elif k == 1:
            shard(c, 0, 9, 0, lit=g(7), dark=g(5)); shard(c, 13, 8, 1, lit=g(7), dark=g(5))
            shard(c, 6, 5, 3, lit=g(13), dark=g(10))
            for (x, y) in [(3, 11), (11, 11), (7, 10), (14, 12)]:
                c.px(x, y, c.a(21), keep=True)
        else:
            shard(c, 0, 12, 0, lit=g(7), dark=g(5)); shard(c, 13, 12, 1, lit=g(7), dark=g(5))
            shard(c, 5, 10, 3, lit=g(13), dark=g(10))
            for (x, y) in [(1, 15), (14, 15), (8, 12), (4, 12)]:
                c.px(x, y, c.a(19 if k == 3 else 21), keep=True)
        fr.append(c)
    return fr


# ====================================================================== C2 chest — 종군 상인의 궤짝 (32x16)
def chest_frames(R):
    fr = []
    for opened in (False, True):
        c = Cv(32, 16, R)
        if not opened:
            c.rect(1, 1, 30, 6, g(7))            # 뚜껑 윗면
            c.hl(2, 29, 1, g(9))
            c.rect(1, 6, 30, 8, g(6))            # 뚜껑 앞단
            c.rect(1, 9, 30, 15, g(5))           # 몸통
            c.hl(1, 30, 9, g(3))                 # 뚜껑 이음 그늘
            for x in (8, 16, 23):
                c.vl(x, 10, 14, g(4))            # 널
        else:
            c.rect(2, 0, 29, 3, g(4))            # 젖혀진 뚜껑 안쪽
            c.hl(3, 28, 0, g(6))
            c.rect(1, 4, 30, 8, g(1))            # 빈 속
            c.hl(2, 29, 4, g(3))
            c.rect(1, 9, 30, 15, g(5))
            c.hl(1, 30, 9, g(7))                 # 앞 테두리 빛
            for x in (8, 16, 23):
                c.vl(x, 10, 14, g(4))
        # 쇠띠 2줄
        for bx in (5, 25):
            top = 0 if opened else 1
            c.rect(bx, top, bx + 1, 15, g(9))
            c.vl(bx + 1, top, 15, g(8))
            c.px(bx, 11, g(12)); c.px(bx, 14, g(11))
        c.hl(1, 30, 15, g(4))
        c.outline()
        # 자물쇠 판
        if not opened:
            c.rect(14, 6, 17, 10, g(10))
            c.hl(14, 17, 6, g(12))
            c.vl(17, 7, 10, g(8))
            c.px(15, 8, c.a(25), keep=True)          # 열쇠 구멍의 불씨 = 층 강조 한 점
            c.px(16, 8, c.a(23), keep=True)
            c.px(15, 9, c.a(21), keep=True)
            c.px(16, 9, g(1))
        else:
            c.rect(14, 10, 17, 12, g(8))          # 늘어진 자물쇠
            c.px(15, 11, g(1)); c.px(16, 11, g(1))
            c.px(15, 13, g(6))
            c.px(10, 6, g(5)); c.px(21, 7, g(5))  # 빈 바닥 먼지
        fr.append(c)
    return fr


# ====================================================================== C3 grave — 무명 전사의 묘 (16x32)
def mound(c):
    c.ell(8, 26.5, 7.5, 5.0, g(4))
    c.ell(7, 25.5, 5.5, 3.6, g(5), only="opaque")
    c.ell(6, 24.6, 3.0, 2.0, g(6), only="opaque")
    for (x, y) in [(3, 27), (11, 28), (8, 30), (5, 29), (12, 25)]:
        c.px(x, y, g(3), only="opaque")
    # 돌 두 개 (무덤 테두리)
    c.rect(1, 28, 3, 30, g(7)); c.px(1, 28, g(9))
    c.rect(12, 29, 14, 31, g(7)); c.px(12, 29, g(9))


def grave_frames(R, floor=1):
    fr = []
    for used in (False, True):
        c = Cv(16, 32, R)
        mound(c)
        if not used:
            if floor == 1:
                # 술통 망치 머리 = 작은 통 (가로, 살짝 기울어짐) — 덩어리라 셀아웃 적용
                c.rect(3, 4, 12, 11, g(6))
                c.hl(4, 11, 3, g(6)); c.hl(4, 11, 12, g(6))
                c.rect(3, 4, 12, 6, g(8))
                c.rect(3, 10, 12, 12, g(5))
                c.vl(5, 3, 12, g(10)); c.vl(10, 3, 12, g(10))       # 쇠테
                c.vl(6, 4, 11, g(8))
                c.px(5, 4, g(12)); c.px(10, 4, g(12))
                c.vl(13, 6, 9, g(5))                                  # 통 마구리
        else:
            # 무기가 사라진 구멍
            c.rect(7, 21, 8, 22, g(1))
            c.px(7, 20, g(3)); c.px(8, 20, g(3))
        c.outline()
        if not used:
            if floor == 1:
                # 부러진 자루 (2px, keep: 윤곽 없이 나무색) — 무덤에 꽂힘, 가운데 쪼개진 금
                for y in range(13, 24):
                    x = 7 if y < 19 else 6
                    c.px(x, y, g(7), keep=True); c.px(x + 1, y, g(4), keep=True)
                c.px(7, 16, g(0), keep=True); c.px(8, 17, g(9), keep=True)   # 쪼개진 금 + 가시
                c.px(6, 24, g(1), keep=True); c.px(7, 24, g(1), keep=True)   # 꽂힌 자리 그늘
                # 감긴 붕대 조각 (오른쪽으로 펄럭)
                for (x, y, cc) in [(9, 14, 12), (10, 14, 11), (11, 15, 11), (12, 15, 10), (13, 16, 10)]:
                    c.px(x, y, g(cc), keep=True)
            else:
                # 2층: 개 목줄 쇠말뚝 (2px keep) + 고리 + 사슬 + 늘어진 가죽 목줄
                for y in range(5, 24):
                    c.px(7, y, g(10), keep=True); c.px(8, y, g(6), keep=True)
                c.hl(6, 9, 4, g(12), keep=True); c.hl(6, 9, 5, g(8), keep=True)     # 말뚝 머리
                c.px(6, 24, g(1), keep=True); c.px(7, 24, g(1), keep=True)
                for (x, y) in [(9, 7), (10, 7), (11, 8), (11, 9), (10, 10), (9, 10)]:
                    c.px(x, y, g(9), keep=True)                                  # 고리
                for i, (x, y) in enumerate([(11, 11), (12, 13), (12, 15), (11, 17)]):
                    c.px(x, y, g(11), keep=True); c.px(x, y + 1, g(7), keep=True)  # 사슬
                for (x, y, cc) in [(9, 19, 6), (10, 19, 6), (11, 19, 6), (12, 19, 6), (13, 19, 5),
                                   (9, 20, 4), (10, 20, 3), (11, 20, 9), (12, 20, 3), (13, 20, 4), (13, 21, 4)]:
                    c.px(x, y, g(cc), keep=True)                                 # 목줄 + 쇠 버클
        if not used:
            # 넋의 불씨 (위로 오르는 잔불 3점)
            hx = 8 if floor == 1 else 8
            c.px(hx, 3 if floor == 1 else 1, c.a(25), keep=True)
            c.px(hx - 1, 1 if floor == 1 else 0, c.a(23), keep=True)
            c.px(hx + 2, 2 if floor == 1 else 2, c.a(21), keep=True)
        else:
            for (x, y) in [(5, 23), (10, 24), (8, 19)]:
                c.px(x, y, g(7), keep=True)
            c.px(8, 21, c.a(19), keep=True)   # 꺼져 가는 불씨 1점 (어두움)
        fr.append(c)
    return fr


# ====================================================================== 불꽃 (모닥불·화로·불바다 공용)
def flame(c, x, base, h, phase, w=3, core=True):
    """밑(base)에서 위로 h px 혓바닥. phase 0..3 이 좌우 흔들림·키 변화. 색: 19 테두리 21 몸 23·25 안 X1 심."""
    sway = [0, 1, 0, -1][phase % 4]
    hh = h + [0, -1, 1, 0][phase % 4]
    for i in range(hh):
        y = base - i
        t = i / max(1, hh - 1)
        half = max(0, int(round((w / 2.0) * (1 - t ** 1.5))))
        xc = x + (sway if t > 0.45 else 0)
        for dx in range(-half - 1, half + 2):
            col = 19 if abs(dx) == half + 1 else (21 if abs(dx) == half else (23 if t > 0.5 else 25))
            if abs(dx) == half + 1 and t > 0.7:
                continue
            c.px(xc + dx, y, c.a(col), keep=True)
    if core:
        c.px(x, base, X1, keep=True)
        if hh > 4:
            c.px(x, base - 1, X1 if phase % 2 == 0 else c.a(26), keep=True)


def ember_up(c, x, y, k):
    c.px(x, y, c.a(25 if k % 2 == 0 else 23), keep=True)


# ====================================================================== C5 bonfire — 모닥불 (32x32)
def bonfire_frames(R):
    fr = []
    for k in range(5):  # 0..3 active 루프, 4 = used(꺼져 가는 재)
        c = Cv(32, 32, R)
        # 바닥 반사 (돌 둘레 바깥, 어두운 호박 점) — 화면 5% 규칙 안에서 아주 조금
        if k < 4:
            for (x, y) in [(0, 26), (31, 25), (2, 30), (29, 30), (15, 31), (5, 22), (26, 22)]:
                if (x + y + k) % 3:
                    c.px(x, y, c.a(17), keep=True)
        # 돌 둘레 (타원 고리, 돌 9개)
        stones = [(4, 24), (8, 21), (13, 20), (19, 20), (24, 21), (27, 24), (24, 28), (16, 29), (8, 28)]
        for (sx, sy) in stones:
            c.ell(sx, sy, 2.6, 2.0, g(6))
            c.px(sx - 2, sy - 1, g(8), only="opaque")
            c.px(sx - 1, sy - 2, g(9), only="opaque")
            c.px(sx + 1, sy + 1, g(5), only="opaque")
        # 안쪽 재 바닥
        c.ell(16, 25, 9, 3.6, g(3), only="empty")
        c.ell(16, 25, 7, 2.6, g(2), only=[g(3)])
        # 엇갈린 장작 2 (나무)
        c.line(9, 27, 22, 22, g(5)); c.line(9, 26, 22, 21, g(7))
        c.line(10, 22, 23, 27, g(5)); c.line(10, 21, 23, 26, g(6))
        c.outline()
        # 장작 끝의 달아오름 (돌 반사)
        for (sx, sy) in [(8, 21), (13, 20), (19, 20), (24, 21)]:
            c.px(sx, sy + 1, c.a(19), keep=True)
        if k < 4:
            # 불꽃 3갈래
            flame(c, 16, 24, 15, k, w=5)
            flame(c, 12, 24, 9, k + 1, w=3, core=False)
            flame(c, 20, 24, 10, k + 2, w=3, core=False)
            # 장작 위 숯 빛
            for (x, y) in [(13, 24), (19, 24), (16, 25)]:
                c.px(x, y, c.a(23), keep=True)
            # 잔불처럼 올라오는 도트 (루프 위상)
            for i, (x0, y0) in enumerate([(13, 7), (19, 4), (16, 1)]):
                y = y0 - (k * 2 + i) % 6 + 2
                if 0 <= y < 12:
                    ember_up(c, x0 + ((k + i) % 2), y, k + i)
            # 돌 안쪽 면의 빛
            for (x, y) in [(7, 22), (12, 21), (20, 21), (25, 22), (6, 27), (25, 27)]:
                c.px(x, y, c.a(21 if (x + k) % 2 else 20), only="opaque")
        else:
            for (x, y) in [(14, 24), (17, 23), (19, 25)]:
                c.px(x, y, c.a(19), keep=True)
            c.px(16, 24, c.a(21), keep=True)
            dust(c, [(15, 20), (17, 17), (16, 14)], g(5))
        fr.append(c)
    return fr


# ====================================================================== 1-1 barrel — 독주 술통 (16x16, 1층)
def barrel_up(c, dx=0, tilt=0):
    c.rect(3 + dx, 2, 12 + dx, 14, g(7))
    c.vl(2 + dx, 4, 12, g(7)); c.vl(13 + dx, 4, 12, g(7))
    c.rect(9 + dx, 2, 13 + dx, 14, g(6))                 # 그늘 쪽
    c.rect(4 + dx, 3, 5 + dx, 13, g(8))                  # 빛 쪽
    c.vl(4 + dx, 4, 7, g(10))
    # 윗면 (타원)
    c.ell(8 + dx, 2.5, 5, 1.6, g(8))
    c.hl(5 + dx, 10 + dx, 1, g(9))
    # 널 이음
    c.vl(7 + dx, 4, 13, g(5)); c.vl(10 + dx, 4, 13, g(5))
    # 쇠테 두 줄 (밝은 쇠 — 소품 술통과 구분)
    for y in (5, 11):
        c.hl(2 + dx, 13 + dx, y, g(11))
        c.hl(2 + dx, 13 + dx, y + 1, g(8))
        c.px(3 + dx, y, g(13))
    # 술 얼룩 (마개에서 흘러내림)
    c.vl(9 + dx, 3, 4, g(4))


def barrel_frames(R):
    fr = []
    # idle
    c = Cv(16, 16, R)
    barrel_up(c)
    c.outline()
    c.px(8, 1, c.a(25), keep=True); c.px(9, 1, c.a(23), keep=True); c.px(8, 2, c.a(21), keep=True)  # 마개의 호박 한 점
    c.px(9, 4, c.a(19), keep=True)
    fr.append(c)
    # hit
    c = Cv(16, 16, R)
    barrel_up(c, dx=1)
    c.outline()
    c.brighten(1, region=lambda x, y: x < 9)
    c.px(9, 1, c.a(25), keep=True); c.px(10, 1, c.a(23), keep=True)
    c.px(12, 0, c.a(23), keep=True)
    fr.append(c)
    # active = 구르기 4f (누운 통, 축 가로, 아래(+y)로 굴러감 — 다른 방향은 시스템이 회전)
    for k in range(4):
        c = Cv(16, 16, R)
        # 누운 통: 가운데가 불룩한 몸 (축 가로), 위 빛 / 아래 그늘
        top_of, bot_of = {}, {}
        for x in range(1, 15):
            hh = 3.6 + 1.6 * math.cos((x + 0.5 - 8) / 7.0 * math.pi / 2)
            t, b = rr(9 - hh), rr(9 + hh) - 1
            top_of[x], bot_of[x] = t, b
            for y in range(t, b + 1):
                rel = (y - t) / max(1, b - t)
                c.px(x, y, g(8) if rel < 0.3 else (g(7) if rel < 0.62 else g(5)))
        # 널 이음 — 굴러 내려감 (위상 k, 3px 간격)
        for x in range(2, 14):
            for j in range(4):
                y = top_of[x] + ((j * 3 + k) % (bot_of[x] - top_of[x] + 1))
                if top_of[x] < y < bot_of[x]:
                    c.px(x, y, g(6) if y < 9 else g(4))
        # 쇠테 세로 두 줄 (밝은 쇠)
        for x in (4, 11):
            for y in range(top_of[x], bot_of[x] + 1):
                c.px(x, y, g(11) if y < 10 else g(8))
            c.px(x + 1, top_of[x + 1] + 1, g(8))
        # 양 끝 마구리 (어두운 면)
        c.vl(1, top_of[1], bot_of[1], g(5)); c.vl(14, top_of[14], bot_of[14], g(4))
        c.outline()
        # 마개 위치가 돌아감 (위 → 앞 → 아래 → 뒤(안 보임))
        by = [top_of[8] + 1, 8, bot_of[8] - 1, None][k]
        if by is not None:
            c.px(8, by, c.a(25 if k < 2 else 23), keep=True); c.px(7, by, c.a(21), keep=True)
        # 흘린 술 방울 (굴러온 자취 = 위쪽)
        c.px(7 + k % 2, 0, c.a(19), keep=True)
        c.px(9 - k % 2, 1, c.a(17), keep=True)
        fr.append(c)
    # broken 3f
    for k in range(3):
        c = Cv(16, 16, R)
        if k == 0:
            # 터짐: 통널이 벌어짐 + 술이 솟음
            for (x, y, kd) in [(1, 6, 0), (12, 5, 1), (3, 11, 2), (11, 11, 0), (7, 2, 3)]:
                shard(c, x, y, kd, lit=g(8), dark=g(6))
            c.hl(2, 13, 9, g(11), keep=True)       # 튀는 쇠테
            puddle(c, 8, 12, 5, 2)
            for (x, y) in [(6, 7), (9, 6), (8, 4), (5, 9), (11, 8)]:
                c.px(x, y, c.a(23), keep=True)
            c.px(8, 8, c.a(25), keep=True)
            c.px(7, 8, X1, keep=True) if False else None
        elif k == 1:
            for (x, y, kd) in [(0, 9, 0), (13, 8, 1), (2, 13, 2), (12, 13, 0), (6, 4, 3)]:
                shard(c, x, y, kd, lit=g(8), dark=g(6))
            c.ring(8, 12, 5.5, 2.2, g(10), keep=True)
            puddle(c, 8, 12, 6, 2.6)
            for (x, y) in [(4, 6), (12, 6)]:
                c.px(x, y, c.a(21), keep=True)
        else:
            for (x, y, kd) in [(0, 12, 0), (14, 11, 1), (1, 14, 2), (13, 14, 3)]:
                shard(c, x, y, kd, lit=g(8), dark=g(6))
            c.ring(8, 12, 5.5, 2.2, g(8), keep=True)
            c.ring(8, 12, 4.5, 1.6, g(1), keep=True)
            puddle(c, 8, 12.5, 6.5, 2.8)
        fr.append(c)
    return fr


# ====================================================================== 1-2 still — 증류 화로 (16x32, 1층)
def still_frames(R):
    fr = []
    for k in range(4):
        c = Cv(16, 32, R)
        # 화덕 (돌·벽돌) y 22..31
        c.rect(1, 22, 14, 31, g(5))
        c.hl(1, 14, 22, g(7)); c.hl(2, 13, 23, g(6))
        for (x0, x1, y) in [(1, 6, 26), (8, 14, 26), (3, 10, 29)]:
            c.hl(x0, x1, y, g(4))
        c.vl(7, 23, 25, g(4)); c.vl(11, 27, 28, g(4)); c.vl(4, 27, 28, g(4))
        c.rect(4, 26, 11, 31, g(1))                # 아궁이
        # 단지 (양파 돔) y 9..22
        c.ell(8, 17.5, 6.2, 5.0, g(8))
        c.ell(9.3, 18.6, 5.0, 3.8, g(7), only="opaque")
        c.ell(6.4, 15.4, 2.4, 2.0, g(10), only="opaque")
        c.px(5, 14, g(12), only="opaque")
        c.hl(3, 13, 21, g(6), only="opaque")       # 밑 그늘
        # 목 + 백조목 관 (오른쪽으로 꺾여 내려감)
        c.rect(7, 6, 9, 12, g(8)); c.vl(7, 6, 12, g(10)); c.vl(9, 6, 12, g(6))
        c.rect(6, 4, 10, 6, g(9)); c.hl(6, 10, 4, g(11))
        c.line(10, 5, 13, 7, g(8)); c.line(10, 4, 13, 6, g(10))
        c.vl(13, 7, 15, g(8)); c.vl(14, 7, 15, g(6))
        c.rect(12, 15, 14, 17, g(6))               # 받이 꼭지
        # 리벳
        c.px(5, 18, g(11)); c.px(11, 19, g(5))
        c.outline()
        # 불: 아궁이 속 + 단지 밑을 핥는 혓바닥 (루프)
        for i, x in enumerate((5, 8, 10)):
            flame(c, x, 30, [4, 6, 5][i], k + i, w=2, core=(i == 1))
        c.px(6, 31, c.a(21), keep=True); c.px(9, 31, c.a(21), keep=True)
        # 단지 아래면에 불빛 반사 (구리 대신 층 강조로 데움)
        for x in range(4, 13):
            if (x + k) % 3 != 0:
                c.px(x, 21, c.a(19 if x % 2 else 20), only="opaque")
        c.px(6, 20, c.a(21), only="opaque")
        # 받이 꼭지에서 떨어지는 독주 방울 (상호작용 표지)
        dy = [0, 1, 2, 3][k]
        c.px(13, 18 + dy, c.a(23), keep=True)
        beacon(c, 13, 15) if False else None
        c.px(13, 16, c.a(25), keep=True)
        fr.append(c)
    return fr


# ====================================================================== 1-3 ledger — 외상 장부대 (16x32, 1층)
def ledger_frames(R):
    fr = []
    for used in (False, True):
        c = Cv(16, 32, R)
        # 기둥 두 개 + 판자
        c.rect(2, 4, 3, 31, g(5)); c.vl(2, 4, 31, g(6))
        c.rect(12, 4, 13, 31, g(5)); c.vl(12, 4, 31, g(6))
        c.rect(1, 3, 14, 22, g(6))                         # 판자
        c.hl(1, 14, 3, g(8)); c.hl(1, 14, 12, g(5))        # 판자 이음
        c.vl(1, 3, 22, g(7))
        # 지붕 비가림 널
        c.rect(0, 1, 15, 2, g(4)); c.hl(0, 15, 1, g(6))
        # 박힌 장부 (종이) y 5..20
        c.rect(3, 5, 11, 20, g(12))
        c.vl(11, 6, 20, g(10)); c.hl(3, 11, 20, g(10))
        c.px(3, 5, g(13)); c.hl(4, 10, 5, g(13))
        # 이름 줄 (잉크 G06) — 길이 다르게
        lines = [(4, 9, 7), (4, 8, 9), (4, 10, 11), (4, 7, 13), (4, 9, 15)]
        for (x0, x1, y) in lines:
            c.hl(x0, x1, y, g(6))
            c.px(x1 - 1, y, g(8))                          # 그은 줄 (빚 갚음? 죽음)
        c.hl(4, 9, 17, g(6)) if used else None
        # 못 + 깃펜 (오른쪽 기둥 못에 걸림)
        c.px(13, 9, g(10))
        c.line(13, 10, 15, 16, g(13)); c.line(12, 11, 14, 17, g(11))
        c.px(15, 17, g(3))
        # 받침 발
        c.rect(1, 30, 4, 31, g(4)); c.rect(11, 30, 14, 31, g(4))
        c.outline()
        # 강조: 밀랍 봉인(위 귀퉁이) / 쓴 뒤에는 새 이름 줄이 호박 잉크
        if not used:
            c.px(9, 7, c.a(25), keep=True); c.px(10, 7, c.a(21), keep=True); c.px(9, 8, c.a(21), keep=True); c.px(10, 8, c.a(19), keep=True)
        else:
            c.px(9, 7, c.a(19), keep=True); c.px(10, 7, c.a(17), keep=True); c.px(9, 8, c.a(17), keep=True); c.px(10, 8, c.a(17), keep=True)
            c.hl(4, 9, 17, c.a(21), keep=True)
            c.px(10, 17, c.a(23), keep=True)
        fr.append(c)
    return fr


# ====================================================================== 1-4 cask — 숙성 통 (32x32, 1층)
def cask_body(c):
    # 받침 (양쪽 버팀목)
    c.rect(3, 26, 7, 31, g(4)); c.rect(24, 26, 28, 31, g(4))
    c.hl(3, 7, 26, g(6)); c.hl(24, 28, 26, g(6))
    # 통 몸 윗곡면 (뒤로 이어지는 몸통) y 2..12
    c.ell(16, 9, 12.5, 7.0, g(6))
    c.ell(14.5, 7.5, 9.5, 4.5, g(7), only="opaque")
    c.hl(8, 20, 3, g(9))
    for x in (8, 13, 18, 23):
        c.vl(x, 4, 12, g(5), only="opaque")
    # 앞 마구리 (둥근 머리) — 크게
    c.ell(16, 18.5, 12.0, 10.0, g(6))
    c.ell(14.8, 17.3, 9.8, 8.0, g(7), only="opaque")
    c.ell(13.5, 15.5, 5.0, 3.6, g(8), only="opaque")
    # 테 두 줄 (쇠)
    c.ring(16, 18.5, 12.0, 10.0, g(10), t=1.0)
    c.ring(16, 18.5, 9.5, 7.8, g(5), t=1.0)
    # 마구리 널 이음 (세로)
    for x in (10, 16, 22):
        for y in range(11, 27):
            if c.get(x, y) in (g(7), g(8)):
                c.px(x, y, g(5))
    # 꼭지 (아래 가운데)
    c.rect(14, 22, 17, 24, g(9)); c.hl(14, 17, 22, g(11))
    c.rect(15, 25, 16, 26, g(8))
    c.px(18, 22, g(10)); c.px(19, 21, g(10))   # 손잡이


def cask_frames(R):
    fr = []
    # idle = 빈 통 (꼭지 마름, 꼭지에 칠한 호박 고리 한 점만)
    c = Cv(32, 32, R)
    cask_body(c)
    c.outline()
    c.px(16, 23, c.a(25), keep=True); c.px(15, 23, c.a(21), keep=True)
    c.px(21, 4, g(4))
    fr.append(c)
    # active = 숙성 중 거품 3f (윗면 마개 구멍에서 거품, 마구리 틈 은은한 19)
    for k in range(3):
        c = Cv(32, 32, R)
        cask_body(c)
        c.outline()
        c.px(16, 23, c.a(21), keep=True)
        # 마개 구멍
        c.rect(15, 4, 17, 5, g(2))
        bub = [[(16, 3), (15, 1)], [(15, 2), (17, 0)], [(17, 3), (16, 1), (14, 0)]][k]
        for i, (x, y) in enumerate(bub):
            c.px(x, y, g(10) if i else c.a(23), keep=True)
        for y in (13, 19):
            c.px(10, y + k % 2, c.a(19), keep=True)
            c.px(22, y + (k + 1) % 2, c.a(19), keep=True)
        fr.append(c)
    # ready = 다 익음 2f (이음 틈으로 호박 빛 + 꼭지 방울)
    for k in range(2):
        c = Cv(32, 32, R)
        cask_body(c)
        c.outline()
        for x in (10, 16, 22):
            for y in range(12, 26):
                if c.get(x, y) == g(5) and (y + k) % 2 == 0:
                    c.px(x, y, c.a(21 if y % 4 else 23), keep=True)
        c.px(16, 23, c.a(25), keep=True); c.px(15, 23, c.a(23), keep=True)
        c.px(15, 27 + k, c.a(25), keep=True)
        c.px(15, 26, c.a(23), keep=True)
        c.ring(16, 18.5, 12.0, 10.0, c.a(20), t=1.0, only=[g(0), g(4)]) if False else None
        fr.append(c)
    # used = 꺼낸 뒤 (꼭지 빠진 구멍, 강조 없음)
    c = Cv(32, 32, R)
    cask_body(c)
    c.rect(14, 22, 17, 26, g(6))
    c.rect(15, 23, 16, 24, g(1))
    c.outline()
    fr.append(c)
    return fr


# ====================================================================== 1-5 counter — 선술집 카운터 (48x32, 1층)
def counter_frames(R):
    fr = []
    for n_used in (0, 1, 2, 3):
        c = Cv(48, 32, R)
        # 뒤 선반 뒷판 (낮은 판자 벽) y 3..13 — 병이 창살처럼 떠 보이지 않게 바탕을 깐다
        c.rect(2, 3, 45, 13, g(3))
        c.hl(2, 45, 3, g(5))
        c.hl(3, 44, 8, g(2))
        c.rect(2, 11, 45, 13, g(5)); c.hl(2, 45, 11, g(7))          # 선반 널
        # 카운터 윗면 y 13..17
        c.rect(0, 13, 47, 17, g(7))
        c.hl(0, 47, 13, g(9)); c.hl(0, 47, 17, g(5))
        for x in (11, 27, 39):
            c.px(x, 15, g(6)); c.px(x + 1, 15, g(6))       # 얼룩·칼자국
        # 앞면 패널 y 18..31
        c.rect(0, 18, 47, 31, g(5))
        for x in range(0, 48, 8):
            c.vl(x, 19, 30, g(4)); c.vl(x + 1, 19, 30, g(6))
        c.hl(0, 47, 18, g(3))
        c.hl(1, 46, 27, g(9)); c.hl(1, 46, 28, g(7))         # 발 받침 쇠
        c.outline()
        # 병 (keep: 셀아웃 없이 유리 명암) — 선반 위, 몸 3px + 목 1px + 마개
        bottles = [(5, 5, 21), (10, 4, None), (14, 6, 19), (19, 4, None), (25, 5, 21), (29, 6, None),
                   (34, 4, 19), (39, 5, None), (43, 6, None)]
        for (bx, top, acc) in bottles:
            for y in range(top + 2, 11):
                c.px(bx - 1, y, g(6), keep=True)
                c.px(bx, y, c.a(acc) if (acc and y > top + 3) else g(4), keep=True)
                c.px(bx + 1, y, g(1), keep=True)
            c.px(bx, top + 1, g(5), keep=True); c.px(bx, top, g(2), keep=True)
            c.px(bx - 1, top + 2, g(8), keep=True)
        # 잔 3개 (윗면): 서 있는 잔 / 엎어진 잔
        for i, cx in enumerate((14, 23, 32)):
            if i < n_used:
                # 엎어진 잔 + 쏟아진 방울
                c.rect(cx - 1, 14, cx + 2, 15, g(10)); c.hl(cx - 1, cx + 2, 14, g(12))
                c.px(cx - 2, 15, g(0)); c.px(cx + 3, 15, g(0))
                c.px(cx + 3, 16, c.a(19), keep=True)
            else:
                c.rect(cx - 1, 11, cx + 1, 15, g(10)); c.vl(cx - 1, 11, 15, g(12))
                c.hl(cx - 1, cx + 1, 11, g(13))
                c.rect(cx, 12, cx + 1, 13, c.a(21), keep=True)
                c.px(cx, 12, c.a(23), keep=True)
                c.vl(cx + 2, 11, 15, g(0))
                c.hl(cx - 1, cx + 2, 16, g(4))
        if n_used < 3:
            # 상호작용 표지: 아직 비지 않은 첫 잔의 술 위 불씨
            cx = (14, 23, 32)[n_used]
            c.px(cx, 11, c.a(25), keep=True)
        fr.append(c)
    return fr


# ====================================================================== 1-6 cellar_wall — 밀주 저장고 숨은 벽 (16x16, 1층)
def stage_tile(n, idx):
    im = Image.open(os.path.join(ROOT, "assets", "tiles", "stage%d.png" % n)).convert("RGBA")
    x, y = (idx % 8) * 16, (idx // 8) * 16
    return im.crop((x, y, x + 16, y + 16))


def tile_cv(R, n, idx):
    c = Cv(16, 16, R)
    im = stage_tile(n, idx)
    for y in range(16):
        for x in range(16):
            p = im.getpixel((x, y))
            if p[3]:
                c.p[(x, y)] = "#%02x%02x%02x" % p[:3]
    return c


def wall_crack(c, stage, leak=1):
    pts = [(7, 1), (8, 2), (8, 3), (9, 4), (9, 5), (8, 6), (8, 9), (7, 10), (7, 11), (6, 12), (6, 13)]
    if stage >= 2:
        pts += [(10, 3), (11, 2), (5, 11), (4, 10), (9, 12), (10, 13)]
    if stage >= 3:
        pts += [(12, 1), (3, 9), (2, 9), (10, 14), (5, 14)]
    for (x, y) in pts:
        c.px(x, y, g(0))
    # 금 오른쪽 가장자리를 한 단 밝게 (벌어진 벽돌 모서리)
    for (x, y) in pts:
        if (x + 1, y) not in pts and c.get(x + 1, y) in (g(2), g(3)):
            c.px(x + 1, y, g(4))
    # 틈새로 새는 호박 빛 (1px — 눈치챌 만큼만)
    c.px(8, 9 if True else 9, c.a(21), keep=True)
    if leak >= 2:
        c.px(8, 10, c.a(19), keep=True)
        c.px(9, 5, c.a(23), keep=True)
    if leak >= 3:
        c.px(7, 11, c.a(21), keep=True)
        c.px(8, 2, c.a(19), keep=True)


def cellar_wall_frames(R):
    fr = []
    names = []
    for face, idx in (("front", 5), ("top", 6)):
        base = tile_cv(R, 1, idx)
        # idle
        c = base.copy(); wall_crack(c, 1, 1); fr.append(c); names.append(face + "_idle")
        # hit (번쩍 + 먼지)
        c = base.copy(); wall_crack(c, 2, 2); c.brighten(1)
        dust(c, [(4, 15), (11, 14), (7, 15)], g(7))
        fr.append(c); names.append(face + "_hit")
        # damaged 1·2 (타격 횟수)
        c = base.copy(); wall_crack(c, 2, 2); fr.append(c); names.append(face + "_dmg1")
        c = base.copy(); wall_crack(c, 3, 3); fr.append(c); names.append(face + "_dmg2")
    # broken 3f (앞·윗면 공용): 무너짐 → 먼지 → 잔해(통과 가능, 바닥이 보이게 대부분 투명)
    R_ = R
    c = Cv(16, 16, R_)
    for (x, y, kd) in [(1, 2, 0), (6, 1, 1), (11, 3, 2), (3, 7, 3), (9, 8, 0), (12, 10, 1), (2, 12, 2), (7, 12, 3)]:
        c.rect(x, y, x + 3, y + 2, g(3)); c.hl(x, x + 3, y, g(4)); c.px(x + 3, y + 2, g(0))
    c.rect(5, 4, 10, 10, g(0))
    c.px(7, 6, c.a(23), keep=True); c.px(8, 7, c.a(21), keep=True); c.px(6, 8, c.a(19), keep=True)
    fr.append(c); names.append("broken0")
    c = Cv(16, 16, R_)
    for (x, y) in [(1, 9), (5, 11), (10, 10), (12, 13), (3, 13), (8, 14)]:
        c.rect(x, y, x + 2, y + 1, g(3)); c.hl(x, x + 2, y, g(4))
    dust(c, [(2, 5), (4, 3), (8, 4), (11, 6), (13, 4), (6, 7), (9, 2), (3, 8), (12, 8)], g(6))
    dust(c, [(5, 5), (10, 5), (7, 8)], g(8))
    c.px(7, 6, c.a(21), keep=True); c.px(8, 9, c.a(19), keep=True)
    fr.append(c); names.append("broken1")
    c = Cv(16, 16, R_)
    for (x, y) in [(0, 12), (4, 14), (11, 13), (13, 11), (1, 9)]:
        c.rect(x, y, x + 2, y + 1, g(3)); c.hl(x, x + 2, y, g(4)); c.px(x + 2, y + 1, g(0))
    c.rect(7, 14, 8, 15, g(3)); c.px(7, 14, g(4))
    fr.append(c); names.append("broken2")
    return fr, names


# ====================================================================== 2-1 card_table — 패 탁자 (48x32, 2층)
def rounded(c, x0, y0, x1, y1, r, col, **k):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dx = max(x0 + r - x, 0, x - (x1 - r))
            dy = max(y0 + r - y, 0, y - (y1 - r))
            if dx * dx + dy * dy <= r * r + 1:
                c.px(x, y, col, **k)


def card_back(c, x, y, w=5, h=7, beacon_=False):
    """엎어진 패 뒷면: 밝은 판지 G09 + 빛 테 G11 + 그늘 테 G06 + 가운데 녹색 마름모, 펠트 위 그림자 17."""
    c.rect(x + 1, y + 1, x + w, y + h, c.a(17))              # 그림자
    c.rect(x, y, x + w - 1, y + h - 1, g(9))
    c.hl(x, x + w - 1, y, g(11)); c.vl(x, y, y + h - 1, g(11))
    c.hl(x + 1, x + w - 1, y + h - 1, g(6)); c.vl(x + w - 1, y + 1, y + h - 1, g(6))
    cx, cy = x + w // 2, y + h // 2
    c.px(cx, cy - 1, c.a(21)); c.px(cx - 1, cy, c.a(21)); c.px(cx + 1, cy, c.a(21)); c.px(cx, cy + 1, c.a(21))
    c.px(cx, cy, c.a(25) if beacon_ else g(6))


def card_face(c, x, y, w=5, h=7):
    c.rect(x + 1, y + 1, x + w, y + h, c.a(17))
    c.rect(x, y, x + w - 1, y + h - 1, g(13))
    c.hl(x, x + w - 1, y, g(14))
    c.hl(x + 1, x + w - 1, y + h - 1, g(10)); c.vl(x + w - 1, y + 1, y + h - 1, g(10))
    cx, cy = x + w // 2, y + h // 2
    c.px(cx, cy - 1, c.a(21)); c.px(cx, cy, c.a(21)); c.px(cx - 1, cy, c.a(21)); c.px(cx + 1, cy, c.a(21))
    c.px(cx, cy + 1, g(4))
    c.px(x + 1, y + 1, g(4)); c.px(x + w - 2, y + h - 2, g(4))   # 귀퉁이 표식


def card_table_frames(R):
    fr = []

    def table(c):
        # 딜러 의자 (빈 의자 등받이, 탁자 뒤)
        c.rect(19, 0, 28, 7, g(4))
        c.rect(21, 2, 26, 5, g(3))
        c.hl(19, 28, 0, g(6)); c.vl(19, 0, 7, g(5))
        # 앞 앞판 + 다리
        c.rect(4, 24, 43, 27, g(5)); c.hl(4, 43, 24, g(4))
        c.rect(5, 27, 7, 31, g(4)); c.rect(40, 27, 42, 31, g(4))
        c.vl(5, 27, 31, g(5)); c.vl(40, 27, 31, g(5))
        # 탁자 윗면: 둥근 나무 테 + 녹색 펠트
        rounded(c, 1, 5, 46, 24, 6, g(6))
        rounded(c, 1, 5, 46, 8, 3, g(7), only=[g(6)])
        c.hl(6, 41, 5, g(8))
        rounded(c, 3, 7, 44, 22, 5, c.a(17))
        rounded(c, 4, 8, 44, 22, 4, c.a(18))
        rounded(c, 7, 10, 40, 20, 3, c.a(19))
        for (x, y) in [(9, 19), (38, 11), (35, 19), (11, 11), (23, 20)]:
            c.px(x, y, c.a(18))                             # 닳은 자국
        # 칩 더미 2 (딜러 쪽 양옆): 칩 = 밝은 쇠 G12 + 녹색 띠
        for (sx, sy, n) in [(36, 10, 3), (9, 11, 2)]:
            for i in range(n):
                y = sy + 3 - i
                c.hl(sx, sx + 2, y, g(12) if i % 2 == 0 else c.a(21))
            c.px(sx + 3, sy + 3, c.a(17)); c.hl(sx, sx + 2, sy + 4, c.a(17))

    def finish(c):
        c.outline()

    # idle
    c = Cv(48, 32, R); table(c); finish(c)
    card_back(c, 15, 11); card_back(c, 21, 11, beacon_=True); card_back(c, 27, 11)
    fr.append(c)
    # active = 가운데 패 뒤집기 3f (들림 → 모서리 → 앞면)
    for k in range(3):
        c = Cv(48, 32, R); table(c); finish(c)
        card_back(c, 15, 11); card_back(c, 27, 11)
        if k == 0:
            c.rect(23, 11, 25, 18, c.a(17))
            c.rect(22, 9, 24, 15, g(9)); c.hl(22, 24, 9, g(11)); c.vl(24, 10, 15, g(6)); c.px(23, 12, c.a(21))
        elif k == 1:
            c.rect(23, 12, 24, 18, c.a(17))
            c.vl(23, 8, 15, g(14)); c.vl(24, 9, 15, g(10))
        else:
            card_face(c, 21, 10)
        fr.append(c)
    # used = 앞면이 드러난 패 (길·흉 구분 없는 중립 그림)
    c = Cv(48, 32, R); table(c); finish(c)
    card_back(c, 15, 11); card_back(c, 27, 11)
    card_face(c, 21, 11)
    fr.append(c)
    return fr


# ====================================================================== 2-2 chip_exchange — 목숨 칩 환전대 (32x32, 2층)
def booth(c, sign=True):
    # 판자 부스 몸 y 2..31
    c.rect(1, 2, 30, 31, g(5))
    c.vl(1, 2, 31, g(6))
    for x in (8, 16, 24):
        c.vl(x, 3, 31, g(4))
    c.hl(1, 30, 2, g(7))
    # 지붕 처마
    c.rect(0, 0, 31, 2, g(4)); c.hl(0, 31, 0, g(6))
    # 창구 (어두운 안쪽) y 7..19
    c.rect(4, 7, 27, 19, g(1))
    c.rect(3, 6, 28, 6, g(7)); c.vl(3, 6, 20, g(7)); c.vl(28, 6, 20, g(4))
    # 창턱 (카운터) y 20..22
    c.rect(2, 20, 29, 22, g(8)); c.hl(2, 29, 20, g(10)); c.hl(2, 29, 22, g(5))


def chip_exchange_frames(R):
    fr = []
    for used in (False, True):
        c = Cv(32, 32, R)
        booth(c)
        # 쇠창살 (세로 7개)
        for x in range(6, 27, 3):
            c.vl(x, 7, 19, g(9))
            c.px(x, 7, g(11))
        # 내민 뼈 손 + 접시 (창살 사이)
        c.rect(14, 12, 17, 15, g(3))                                  # 창 안 소매 (어둠 속)
        c.rect(13, 16, 18, 17, g(10)); c.hl(13, 18, 16, g(12))      # 뼈 손등
        for x in (13, 15, 17):
            c.vl(x, 18, 19, g(11))                                    # 손가락 3
        c.ell(15.5, 20.5, 5.0, 1.6, g(12))                           # 접시
        c.hl(11, 20, 21, g(9))
        if not used:
            for (x, y, col) in [(13, 19, 21), (14, 19, 23), (16, 19, 21), (17, 19, 19), (15, 18, 23), (14, 18, 21)]:
                c.px(x, y, c.a(col))
        else:
            c.px(15, 19, c.a(19))
        # 간판 (칩 문양) y 24..29
        c.rect(9, 24, 22, 29, g(4)); c.hl(9, 22, 24, g(6))
        c.ell(15.5, 27, 2.6, 2.0, g(10) if not used else g(7))
        c.px(15, 27, c.a(21) if not used else g(5))
        c.outline()
        if not used:
            c.px(14, 17, c.a(25), keep=True)                          # 칩 위 불씨
            c.px(15, 18, c.a(25), keep=True)
        fr.append(c)
    return fr


# ====================================================================== 2-3 dog_ring — 투견 링 (64x48, 바닥, 2층)
STAKES = []


def dog_ring_frames(R):
    fr = []
    cx, cy, rx, ry = 32, 25, 28.5, 19.5
    stake_pts = []
    for i in range(8):
        ang = -math.pi / 2 + i * math.pi / 4
        stake_pts.append((rr(cx + rx * math.cos(ang) - 0.5), rr(cy + ry * math.sin(ang) - 0.5)))
    STAKES[:] = stake_pts

    def base(c, closed, glow_k=None, cut=False):
        # 링 안 흙: 긁힌 자국·핏자국 (바닥 위 얇게)
        for (x0, y0, x1, y1) in [(18, 18, 22, 21), (40, 28, 44, 30), (27, 31, 30, 33), (36, 15, 39, 17)]:
            c.line(x0, y0, x1, y1, g(3), keep=True)
            c.line(x0 + 1, y0, x1 + 1, y1, g(3), keep=True)
        for (x, y) in [(30, 24), (31, 24), (32, 25), (30, 25), (34, 23), (29, 27)]:
            c.px(x, y, c.a(17), keep=True)
        c.px(31, 25, c.a(19), keep=True)
        # 밧줄 (말뚝 사이 타원), 출입구 = 남쪽(아래) 구간
        n = 360
        for t in range(n):
            ang = 2 * math.pi * t / n
            deg = (math.degrees(ang) + 360) % 360  # 0 = 오른쪽, 90 = 아래
            south = 67 < deg < 113
            if south and not closed:
                continue
            x = cx + rx * math.cos(ang) - 0.5
            y = cy + ry * math.sin(ang) - 0.5
            col = g(9) if (t // 6) % 2 == 0 else g(7)
            if glow_k is not None and ((t // 15) + glow_k) % 4 == 0:
                col = c.a(21)
            c.px(rr(x), rr(y), col, keep=True)
            c.px(rr(x), rr(y) + 1, g(5) if col in (g(9), g(7)) else c.a(19), keep=True, only="empty")   # 밧줄 아랫면 (2px 굵기)
        if not closed and not cut:
            # 풀린 밧줄이 바닥에 늘어짐
            for (x, y) in [(28, 45), (29, 46), (31, 46), (33, 46), (35, 45), (36, 44)]:
                c.px(x, y, g(7), keep=True)
        if cut:
            for (x, y) in [(22, 43), (24, 46), (40, 45), (42, 43)]:
                c.px(x, y, g(6), keep=True)
        # 말뚝 8개 (단단함) — 3x5, 머리 밝게
        for i, (sx, sy) in enumerate(stake_pts):
            tall = 0
            c.rect(sx - 1, sy - 3 - tall, sx + 1, sy + 1, g(5), keep=True)
            c.vl(sx - 1, sy - 3 - tall, sy + 1, g(7), keep=True)
            c.hl(sx - 1, sx + 1, sy - 3 - tall, g(9), keep=True)
            c.vl(sx + 1, sy - 2 - tall, sy + 1, g(4), keep=True)
            c.hl(sx - 1, sx + 1, sy + 2, g(0), keep=True)
            c.px(sx, sy - 1, g(10), keep=True)        # 밧줄 감긴 자리
        # 판돈 깃대 (북쪽 말뚝을 높게 + 깃발)
        sx, sy = stake_pts[0]
        c.rect(sx, 0, sx, sy - 3, g(8), keep=True)
        c.vl(sx + 1, 1, sy - 3, g(4), keep=True)
        return sx

    # idle (출입구 열림)
    c = Cv(64, 48, R); sx = base(c, closed=False)
    c.rect(sx + 1, 1, sx + 6, 4, c.a(19), keep=True); c.hl(sx + 1, sx + 6, 1, c.a(21), keep=True)
    c.px(sx + 6, 5, c.a(17), keep=True)
    c.px(sx + 2, 2, c.a(25), keep=True); c.px(sx + 3, 2, c.a(23), keep=True)
    fr.append(c)
    # active 4f (밧줄 닫힘 + 밧줄 따라 도는 불빛 + 깃발 펄럭)
    for k in range(4):
        c = Cv(64, 48, R); sx = base(c, closed=True, glow_k=k)
        wav = [0, 1, 0, -1][k]
        for i in range(6):
            yy = 1 + (wav if i > 2 else 0)
            c.vl(sx + 1 + i, yy, yy + 3, c.a(19), keep=True)
            c.px(sx + 1 + i, yy, c.a(21), keep=True)
        c.px(sx + 2, 2, c.a(25), keep=True); c.px(sx + 3, 2, c.a(23), keep=True)
        fr.append(c)
    # used (밧줄 끊겨 처짐, 깃발 내려감)
    c = Cv(64, 48, R); sx = base(c, closed=False, cut=True)
    c.rect(sx + 1, 8, sx + 3, 12, c.a(17), keep=True)
    fr.append(c)
    return fr


# ====================================================================== 2-4 bet_bell — 판돈 종 (16x32, 2층)
def bell_body(c, swing=0, crack=False):
    # 기둥 (왼쪽) + 팔
    c.rect(2, 3, 4, 29, g(5)); c.vl(2, 3, 29, g(7)); c.vl(4, 3, 29, g(4))
    c.rect(0, 28, 7, 31, g(4)); c.hl(0, 7, 28, g(6))                # 발판
    c.rect(2, 2, 14, 4, g(5)); c.hl(2, 14, 2, g(7))                  # 팔
    c.px(13, 5, g(9))                                                 # 고리
    # 종 (놋쇠 → 밝은 쇠 G09~G13, 흔들림 swing -1/0/1)
    s = swing
    bx = 12 + s
    pts = []
    c.rect(bx - 3, 7, bx + 2, 8, g(10))
    c.rect(bx - 4, 9, bx + 3, 13, g(10))
    c.rect(bx - 5, 14, bx + 4, 16, g(10))
    c.vl(bx - 4 + (0), 9, 13, g(12)); c.vl(bx - 5, 14, 16, g(12)); c.vl(bx - 3, 7, 8, g(12))
    c.vl(bx + 2, 7, 8, g(8)); c.vl(bx + 3, 9, 13, g(8)); c.vl(bx + 4, 14, 16, g(8))
    c.px(bx - 3, 10, g(14))
    c.hl(bx - 5, bx + 4, 16, g(7))
    c.line(13, 5, bx - 1, 6, g(6))                                    # 매단 끈
    # 추 (아래)
    c.px(bx - 1 - s, 17, g(6)); c.px(bx - 1 - s, 18, g(8))
    if crack:
        c.line(bx - 1, 8, bx + 1, 12, g(3)); c.line(bx + 1, 12, bx, 15, g(3))
        c.px(bx + 4, 16, None)


def bet_bell_frames(R):
    fr = []
    def ribbon(c, s=0, dim=False):
        # 팔에 매단 녹색 판돈 표 (3x4, 상호작용 표지) — 흔들림 s 의 반대로 1px
        x = 6 - (1 if s > 0 else 0)
        c.vl(x + 1, 5, 5, g(8), keep=True)
        if dim:
            c.rect(x, 6, x + 2, 9, c.a(17), keep=True)
            return
        c.rect(x, 6, x + 2, 9, c.a(21), keep=True)
        c.hl(x, x + 2, 6, c.a(23), keep=True)
        c.vl(x + 2, 7, 9, c.a(19), keep=True)
        c.px(x, 7, c.a(25), keep=True)
    c = Cv(16, 32, R); bell_body(c); c.outline(); ribbon(c); fr.append(c)            # idle
    c = Cv(16, 32, R); bell_body(c, swing=1); c.outline(); c.brighten(1, region=lambda x, y: 6 <= y <= 17); ribbon(c, 1)  # hit
    for (x, y) in [(0, 10), (1, 12), (15, 9)]:
        c.px(x, y, g(10), keep=True)
    fr.append(c)
    for k, s in enumerate((-1, 1, 0)):                                         # active 울림 3f
        c = Cv(16, 32, R); bell_body(c, swing=s); c.outline(); ribbon(c, s)
        # 울림 선 (종 양옆 1px 호)
        for (x, y) in ([(5, 11), (5, 13)] if s >= 0 else []) + ([(15, 10), (15, 12)] if s <= 0 else []):
            c.px(x + (1 if s < 0 else 0), y, c.a(23), keep=True)
        if k == 2:
            c.px(5, 12, c.a(21), keep=True); c.px(15, 11, c.a(21), keep=True)
        fr.append(c)
    c = Cv(16, 32, R); bell_body(c, crack=True); c.outline()                      # used (금 간 종)
    ribbon(c, dim=True)
    fr.append(c)
    return fr


# ====================================================================== 2-5 roulette — 룰렛 바닥 (48x48, 바닥, 2층)
def roulette_frames(R):
    fr = []
    cx, cy = 24, 24
    N = 8

    def disc(c, lit=None, dim=False):
        for y in range(48):
            for x in range(48):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                r = math.hypot(dx, dy)
                ang = (math.degrees(math.atan2(dx, -dy)) + 360 + 180 / N) % 360  # 0 = 위(북), 시계 방향
                sl = int(ang // (360 / N))
                if r <= 23.5:
                    if r > 21:
                        col = g(5) if r > 22.3 else g(4)                # 나무 테
                        if dx < -8 and dy < -8 and r > 22.3:
                            col = g(6)
                    elif r > 11:
                        edge = (ang % (360 / N)) < (360 / N) * 0.06 or (ang % (360 / N)) > (360 / N) * 0.94
                        if edge:
                            col = g(7)
                        elif sl % 2 == 0:
                            col = c.a(18 if not dim else 17)
                        else:
                            col = g(1)
                        if lit is not None and sl == lit and not edge:
                            col = c.a(21) if sl % 2 == 0 else c.a(19)
                    elif r > 9.5:
                        col = g(6)
                    elif r > 4:
                        col = g(3)
                    else:
                        col = g(6)
                    c.px(x, y, col, keep=True)
        # 칸 숫자 대신 점 (밝은 쇠)
        for i in range(N):
            a = math.radians(i * 360 / N)
            x, y = cx + 16.5 * math.sin(a) - 0.5, cy - 16.5 * math.cos(a) - 0.5
            c.px(rr(x), rr(y), g(9) if not dim else g(6), keep=True)
        c.ring(cx, cy, 23.5, 23.5, g(0), keep=True)
        c.px(cx - 1, cy - 1, g(10), keep=True); c.px(cx, cy - 1, g(8), keep=True)

    def arrow(c, i, col_body, col_tip):
        """가운데 축에서 칸으로 뻗는 2px 화살 + 5px 촉. 몸 = 밝은 쇠, 그늘 G06, 촉 끝 = 강조 25."""
        a = math.radians(i * 360 / N)
        sx, sy = math.sin(a), -math.cos(a)
        px_, py_ = -sy, sx                       # 수직 (오른쪽)
        for t10 in range(30, 175):
            t = t10 / 10.0
            x, y = cx - 0.5 + sx * t, cy - 0.5 + sy * t
            c.px(rr(x + px_ * 0.8), rr(y + py_ * 0.8), g(6), keep=True)
        for t10 in range(30, 175):
            t = t10 / 10.0
            x, y = cx - 0.5 + sx * t, cy - 0.5 + sy * t
            c.px(rr(x), rr(y), col_body, keep=True)
        # 촉 (삼각형 채움)
        for t10 in range(150, 205):
            t = t10 / 10.0
            half = (20.5 - t) * 0.75
            for w10 in range(-int(half * 10), int(half * 10) + 1, 3):
                w = w10 / 10.0
                x, y = cx - 0.5 + sx * t + px_ * w, cy - 0.5 + sy * t + py_ * w
                c.px(rr(x), rr(y), col_body, keep=True)
        tx, ty = cx - 0.5 + sx * 20, cy - 0.5 + sy * 20
        c.px(rr(tx), rr(ty), col_tip, keep=True)
        # 축 덮개
        c.ell(cx, cy, 3.0, 3.0, g(8), keep=True)
        c.px(cx - 2, cy - 2, g(11), keep=True); c.px(cx - 1, cy - 2, g(10), keep=True)

    # idle
    c = Cv(48, 48, R); disc(c); arrow(c, 0, g(12), c.a(25)); fr.append(c)
    # active 8f (화살표 회전 + 가리킨 칸 점등 = 바닥 문양 맥동)
    for k in range(N):
        c = Cv(48, 48, R); disc(c, lit=k); arrow(c, k, g(13), c.a(25)); fr.append(c)
    # used (멈춤, 어둡게)
    c = Cv(48, 48, R); disc(c, dim=True); arrow(c, 3, g(8), g(9)); fr.append(c)
    return fr


# ====================================================================== 2-6 pawn — 전당포 창구 (32x32, 2층)
def pawn_frames(R):
    fr = []
    for used in (False, True):
        c = Cv(32, 32, R)
        booth(c)
        # 격자 쇠창 (가로·세로 — 환전대의 세로 창살과 구분)
        for x in range(5, 28, 4):
            c.vl(x, 7, 19, g(8))
        for y in (10, 14, 18):
            c.hl(4, 27, y, g(8))
        for x in range(5, 28, 4):
            for y in (10, 14, 18):
                c.px(x, y, g(11))
        if used:
            # 맡긴 보따리 (창 안)
            c.rect(10, 12, 15, 17, g(6)); c.hl(10, 15, 12, g(8)); c.px(12, 11, g(7))
            for y in (14,):
                c.hl(10, 15, y, g(8))
        # 번호표 못판 (창 아래 앞판)
        c.rect(4, 23, 27, 30, g(3)); c.hl(4, 27, 23, g(4))
        tags = [6, 10, 14, 18, 22]
        for i, tx in enumerate(tags):
            c.px(tx + 1, 24, g(10))                          # 못
            c.rect(tx, 25, tx + 2, 28, g(12)); c.vl(tx + 2, 25, 28, g(10))
            c.px(tx + 1, 26 + (i % 2), g(5))                 # 번호
        c.outline()
        if not used:
            # 내 번호표 (녹색) — 비어 있는 마지막 못
            c.rect(25, 25, 26, 28, c.a(21), keep=True); c.px(25, 25, c.a(23), keep=True)
            c.px(26, 24, g(10)); c.px(25, 26, c.a(25), keep=True)
        else:
            c.px(26, 24, g(10))                                # 빈 못
        fr.append(c)
    return fr


# ====================================================================== fx fire_pool — 불바다 루프 (48x24)
def fire_pool_frames():
    fr = []
    rnd = random.Random(7)
    tongues = [(5, 3), (9, 7), (12, 5), (16, 10), (19, 13), (22, 8), (26, 14), (29, 9), (33, 11), (37, 5), (40, 7), (44, 3)]
    for k in range(4):
        c = Cv(48, 24, R1)
        # 웅덩이 (독주) — 바닥에 깔린 타원
        c.ell(24, 18.5, 23, 5.2, c.a(17), keep=True)
        c.ell(23.5, 18.2, 20.5, 4.0, c.a(19), keep=True)
        c.ell(24, 18.6, 15, 2.6, c.a(21), keep=True)
        for (x, y) in [(10, 17), (30, 16), (37, 19), (18, 20)]:
            c.px(x + (k % 2), y, c.a(23), keep=True)
        # 혓바닥
        for i, (x, h) in enumerate(tongues):
            base = 19 + [1, -1, 0, 1, -1, 0][i % 6]
            hh = h + [0, 2, -1, 1][(k + i * 3) % 4]
            flame(c, x, base, max(2, hh), k + i * 3, w=3 if h >= 9 else 2, core=(h >= 11))
        # 오르는 불티
        for i, (x0, y0) in enumerate([(9, 6), (20, 3), (30, 4), (39, 7), (15, 9)]):
            y = y0 - (k * 2 + i * 3) % 7 + 3
            if 0 <= y < 13:
                c.px(x0 + (k + i) % 2, y, c.a(25 if (k + i) % 2 else 23), keep=True)
        fr.append(c)
    return fr


# ====================================================================== 시트·JSON
REG = []   # (id, frames, meta)


def sheet_png(frames):
    w, h = frames[0].w, frames[0].h
    im = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        im.paste(f.image(), (i * w, 0))
    return im


def palette_info(frames, ramp):
    used = set()
    for f in frames:
        used |= set(f.p.values())
    gray = sorted(G.index(c) for c in used if c in G)
    acc = sorted(16 + ramp.index(c) for c in used if c in ramp)
    core = sorted(c for c in used if c in (X0, X1) and c not in G)
    other = sorted(c for c in used if c not in G and c not in ramp and c not in (X0, X1))
    return gray, acc, core, other


FOLD = {
    # 시트별 무채 접기 (드물게 쓴 단을 이웃 단으로 합쳐 무채 <=10 을 맞춘다 — 팔레트 잠금 단계)
    "chest": {10: 9, 11: 12},
    "grave": {1: 0, 11: 12},
    "barrel": {10: 9, 13: 12, 14: 12},
    "still": {11: 12},
    "cask": {1: 0},
    "counter": {13: 12, 10: 9, 8: 7},
    "card_table": {14: 13, 10: 11, 8: 9},
    "chip_exchange": {11: 10, 6: 7},
    "roulette": {10: 12, 11: 12, 9: 8},
    "pawn": {11: 12},
}


def fold_frames(sid, frames):
    fm = FOLD.get(sid)
    if not fm:
        return
    for f in frames:
        for k, c in list(f.p.items()):
            if c in G and G.index(c) in fm:
                f.p[k] = G[fm[G.index(c)]]


def register(sid, frames, states, durations, footprint, solid, depth, floor, swap, kind, note, budget, extra=None,
             loops=None, R=R1):
    fold_frames(sid, frames)
    meta = dict(states=states, durations=durations, footprint=footprint, solid=solid, depth=depth, floor=floor,
                swap=swap, kind=kind, note=note, budget=budget, extra=extra or {}, loops=loops or {}, R=R)
    REG.append((sid, frames, meta))


def export(sid, frames, m, out_dir=OUT, fx=False):
    w, h = frames[0].w, frames[0].h
    assert len(m["durations"]) == len(frames), (sid, len(m["durations"]), len(frames))
    assert all(0 <= i < len(frames) for v in m["states"].values() for i in v), sid
    assert "idle" in m["states"], sid
    assert all(f.w == w and f.h == h for f in frames), sid
    sheet_png(frames).save(os.path.join(out_dir, sid + ".png"))
    gray, acc, core, other = palette_info(frames, m["R"])
    rampname = "stage1 (floor 1 amber)" if m["R"] is R1 else "stage2 (floor 2 casino green)"
    d = {
        "image": sid + ".png",
        "action": sid,
        "frameWidth": w,
        "frameHeight": h,
        "frames": len(frames),
        "directions": ["any"],
        "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column",
        "fps": round(1000.0 / (sum(m["durations"]) / len(m["durations"])), 2),
        "frameDurationsMs": m["durations"],
        "loop": False,
        "pivot": {"x": w // 2, "y": h},
    }
    if not fx:
        d.update({
            "footprint": m["footprint"],
            "solid": m["solid"],
            "depth": m["depth"],
            "states": m["states"],
            "stateLoop": {k: bool(m["loops"].get(k, False)) for k in m["states"]},
            "floor": m["floor"],
            "paletteSwap": m["swap"],
            "interact": m["kind"],
            "pivotNote": "pivot (w/2, h) = 프레임 아래 가장자리 가운데 = footprint 아래 변 가운데. footprint 는 프레임 아래쪽에 붙고 가로 가운데 정렬.",
        })
    d["palette"] = ("parts/art/palette/lopad.json — gray G%s + accent %s drawn in %s ramp%s%s" % (
        ",".join("%02d" % i for i in gray), ",".join(str(i) for i in acc), rampname,
        " (runtime swap target)" if m.get("swap") else " (not swapped)",
        " + fx core X0/X1" if core else ""))
    d["colors"] = {"gray": len(gray), "accent": len(acc), "core": len(core), "budget": m["budget"]}
    d["source"] = "parts/art/work/structures/build.py (round 47)"
    d["note"] = m["note"]
    d.update(m["extra"])
    with open(os.path.join(out_dir, sid + ".json"), "w", encoding="utf-8") as fp:
        json.dump(d, fp, ensure_ascii=False, indent=1)
    return gray, acc, core, other


def frames_range(a, b):
    return list(range(a, b))


def build_all():
    REG.clear()
    f = crate_f1_frames(R1)
    register("crate_f1", f, {"idle": [0], "hit": [1], "broken": [2, 3, 4, 5]}, [200, 80, 50, 70, 100, 200],
             [1, 1], True, "y", "common", True, "hit",
             "C1 부서지는 짐 (1층 외형): 천 뚜껑을 묶은 금 간 술동이. 금 틈으로 호박 술이 샘(강조 한 점). broken: 터짐→파편 비산→바닥에 고임→밑동+파편+어두운 고임(유지, 통과 가능).",
             "gray<=10 accent<=5")
    f = crate_f2_frames(R2)
    register("crate_f2", f, {"idle": [0], "hit": [1], "broken": [2, 3, 4, 5]}, [200, 80, 50, 70, 100, 200],
             [1, 1], True, "y", "stage2", False, "hit",
             "C1 부서지는 짐 (2층 외형): 녹색 칩이 넘치는 판자 상자 + 위에 걸친 찢어진 카드. 2층 램프로 그림(2층 전용 외형).",
             "gray<=10 accent<=5", R=R2)
    f = chest_frames(R1)
    register("chest", f, {"idle": [0], "used": [1]}, [200, 200], [2, 1], True, "y", "common", True, "E",
             "C2 종군 상인의 궤짝: 쇠띠 2줄 나무 궤짝, 자물쇠 열쇠 구멍에 층 강조 불씨. used = 뚜껑 젖혀진 빈 궤짝.",
             "gray<=10 accent<=5")
    f1 = grave_frames(R1, 1)
    f2 = grave_frames(R1, 2)
    register("grave", f1 + f2, {"idle": [0], "used": [1], "idle_f2": [2], "used_f2": [3]}, [200, 200, 200, 200],
             [1, 1], True, "y", "common", True, "E_hold",
             "C3 무명 전사의 묘: 흙무덤 + 꽂힌 부러진 무기 + 넋의 불씨(강조 3점). idle/used = 1층 '술통 망치', idle_f2/used_f2 = 2층 '개 목줄 쇠말뚝'(선택 사용). used = 무기 사라진 구멍 + 꺼져 가는 불씨.",
             "gray<=10 accent<=5")
    f = bonfire_frames(R1)
    register("bonfire", f, {"idle": [0], "active": [0, 1, 2, 3], "used": [4]}, [110, 120, 110, 130, 200],
             [2, 1], True, "y", "common", True, "E",
             "C5 모닥불: 돌 9개 둘레 + 엇갈린 장작 + 3갈래 불(백열 심) + 오르는 잔불 도트, 바깥 바닥에 어두운 호박 반사 점. used = 불씨 0(꺼져 가는 숯, 선택 사용).",
             "gray<=10 accent<=8 core<=2", loops={"active": True})
    f = barrel_frames(R1)
    register("barrel", f, {"idle": [0], "hit": [1], "active": [2, 3, 4, 5], "broken": [6, 7, 8]},
             [200, 80, 90, 90, 90, 90, 50, 80, 200], [1, 1], True, "y", "stage1", False, "hit",
             "1-1 독주 술통: 밝은 쇠테 2줄 + 마개의 호박 한 점(소품 barrel 과 구분). active = 구르기 4f(누운 통, 아래(+y)로 구름 — 다른 방향은 회전), broken = 터짐→고임→쇠테 고리+파편+웅덩이 시작(유지). 3x3 웅덩이·불바다는 fx/fire_pool.",
             "gray<=10 accent<=5", loops={"active": True},
             extra={"rollDrawnFacing": "down", "rollRotate": True})
    f = still_frames(R1)
    register("still", f, {"idle": [0], "active": [0, 1, 2, 3]}, [120, 110, 130, 110], [1, 1], True, "y", "stage1",
             False, "pass",
             "1-2 증류 화로: 벽돌 화덕(아궁이 불) + 쇠 단지(구리 대신 무채 + 불빛 반사 19/20) + 백조목 관 + 받이 꼭지 호박 방울. 부서지지 않음.",
             "gray<=10 accent<=8 core<=2", loops={"active": True},
             extra={"fireBox": {"x": 3, "y": 24, "w": 10, "h": 8, "note": "불꽃 영역(프레임 좌표). 무기 궤적 통과 판정용 참고값"}})
    f = ledger_frames(R1)
    register("ledger", f, {"idle": [0], "used": [1]}, [200, 200], [1, 1], True, "y", "stage1", False, "E",
             "1-3 외상 장부대: 처마 달린 판자에 박힌 장부(이름 줄 5) + 못에 걸린 깃펜 + 호박 밀랍 봉인(표지). used = 봉인이 식고(어두움) 맨 아래에 호박 잉크 새 이름 한 줄.",
             "gray<=10 accent<=5")
    f = cask_frames(R1)
    register("cask", f, {"idle": [0], "active": [1, 2, 3], "ready": [4, 5], "used": [6]},
             [200, 180, 180, 180, 220, 220, 200], [2, 1], True, "y", "stage1", False, "E",
             "1-4 숙성 통: 받침 위 눕힌 큰 오크통(앞 마구리 + 꼭지). idle = 빈 통(꼭지 호박 고리 한 점) / active = 숙성 중(윗마개 거품 루프) / ready = 다 익음(이음 틈 호박 빛 + 꼭지 방울 루프) / used = 꼭지 빠짐(강조 없음).",
             "gray<=10 accent<=5", loops={"active": True, "ready": True})
    f = counter_frames(R1)
    register("counter", f, {"idle": [0], "used1": [1], "used2": [2], "used": [3]}, [200] * 4, [3, 1], True, "y",
             "stage1", False, "E",
             "1-5 선술집 카운터: 판자 앞판 + 발 받침 쇠 + 윗면 잔 3개(호박 술) + 뒤 병 선반. 잔을 마실 때마다 엎어짐: used1/used2/used(=3잔). 표지 불씨는 다음 잔 위.",
             "gray<=10 accent<=5")
    f, names = cellar_wall_frames(R1)
    register("cellar_wall", f,
             {"idle": [0], "hit": [1], "damaged1": [2], "damaged2": [3],
              "idle_top": [4], "hit_top": [5], "damaged1_top": [6], "damaged2_top": [7],
              "broken": [8, 9, 10]},
             [200, 80, 200, 200, 200, 80, 200, 200, 60, 90, 200], [1, 1], True, "y", "stage1", False, "hit",
             "1-6 밀주 저장고 숨은 벽: 1층 벽 타일(5 정면 / 6 윗면)을 그대로 바탕으로 금 + 틈새 호박 빛 1px. 3번 치면: hit(번쩍) → damaged1 → damaged2 → broken(무너짐 → 먼지 → 잔해, 마지막 프레임은 대부분 투명 = 아래 바닥 타일이 보임). 북쪽 벽이면 idle, 나머지 변이면 *_top.",
             "gray<=10 accent<=5", extra={"wallTileBase": {"front": 5, "top": 6, "tileset": "stage1"}})
    f = card_table_frames(R2)
    register("card_table", f, {"idle": [0], "active": [1, 2, 3], "used": [4]}, [200, 70, 60, 90, 200], [3, 2], True,
             "y", "stage2", False, "E",
             "2-1 패 탁자: 녹색 펠트(강조 17~19) + 나무 테 + 빈 딜러 의자 + 엎어진 패 3장(가운데 패에 표지). active = 가운데 패 뒤집기 3f(재생 1회, 마지막 뒤 used), used = 앞면 드러난 패(길·흉 중립).",
             "gray<=10 accent<=5", loops={"active": False}, R=R2)
    f = chip_exchange_frames(R2)
    register("chip_exchange", f, {"idle": [0], "used": [1]}, [200, 200], [2, 1], True, "y", "stage2", False, "E",
             "2-2 목숨 칩 환전대: 처마 달린 판자 부스 + 세로 쇠창살 창구 + 창살 사이로 내민 뼈 손과 칩 접시(녹색 칩) + 칩 간판. used = 접시가 비고 간판이 식음.",
             "gray<=10 accent<=5", R=R2)
    f = dog_ring_frames(R2)
    register("dog_ring", f, {"idle": [0], "active": [1, 2, 3, 4], "used": [5]}, [200, 120, 120, 120, 120, 200],
             [4, 3], False, "floor", "stage2", False, "E",
             "2-3 투견 링: 바닥 타원 밧줄 링 + 말뚝 8 + 북쪽 말뚝 = 판돈 깃대(녹색 깃발, 표지). idle = 남쪽 출입구 열림(밧줄 늘어짐) / active = 밧줄 닫힘 + 밧줄 따라 도는 녹색 불빛 + 깃발 펄럭 / used = 밧줄 끊김·깃발 내려감. 링 안 흙에 긁힌 자국·핏자국.",
             "gray<=10 accent<=5", loops={"active": True}, R=R2,
             extra={"stakes": [list(p) for p in STAKES], "stakesNote": "말뚝 8개 중심(프레임 좌표, 각 3x5). 말뚝만 단단함 — 시스템이 이 점에 작은 충돌체를 둔다.",
                    "flagpost": {"x": STAKES[0][0], "y": STAKES[0][1], "note": "E 상호작용 기준점(북쪽 말뚝 = 판돈 깃대)"},
                    "scale": "allowed", "scaleNote": "초안 링 9x9 타일(144px)은 64x48 상한을 넘는다. 2배(128x96) 배율 허용, 기본 1배."})
    f = bet_bell_frames(R2)
    register("bet_bell", f, {"idle": [0], "hit": [1], "active": [2, 3, 4], "used": [5]}, [200, 80, 90, 90, 120, 200],
             [1, 1], True, "y", "stage2", False, "hit",
             "2-4 판돈 종: 왼쪽 기둥 + 팔에 매단 종(놋쇠 대신 밝은 쇠 G07~G14) + 끈에 묶은 녹색 판돈 띠(표지). hit = 첫 타격(흔들림·번쩍), active = 울림 3f(좌·우·가운데 + 울림 점), used = 금 간 종(띠 식음).",
             "gray<=10 accent<=5", loops={"active": False}, R=R2)
    f = roulette_frames(R2)
    register("roulette", f, {"idle": [0], "active": list(range(1, 9)), "used": [9]}, [200] + [70] * 8 + [200],
             [3, 3], False, "floor", "stage2", False, "auto",
             "2-5 룰렛 바닥: 나무 테 원판, 8칸(녹색 18 / 검정 G01 번갈아) + 칸 점 + 가운데 축, 화살표(밝은 쇠 + 강조 25 촉). active = 화살표 8방향 회전 + 가리킨 칸 점등(바닥 문양 맥동), used = 멈춤·어둡게.",
             "gray<=10 accent<=5", loops={"active": True}, R=R2,
             extra={"stopFrames": {str(i): 1 + i for i in range(8)},
                    "stopNote": "active 의 i 번째 프레임(1+i) = 화살표가 i 번 칸(북쪽부터 시계 방향)을 가리킴. 규칙 결정 후 그 프레임에서 멈춰 보여줄 수 있다.",
                    "scale": "allowed", "scaleNote": "초안 5x5 타일(80px)은 64x48 상한을 넘어 48x48(3x3). 정수 배율 허용."})
    f = pawn_frames(R2)
    register("pawn", f, {"idle": [0], "used": [1]}, [200, 200], [2, 1], True, "y", "stage2", False, "E",
             "2-6 전당포 창구: 환전대와 같은 부스 몸 + 가로세로 격자 쇠창 + 번호표 못판(회색 표 5 + 녹색 '내 번호표', 표지). used = 녹색 표를 떼어 감(빈 못) + 창 안에 맡긴 보따리.",
             "gray<=10 accent<=5", R=R2)


BUDGET = {"gray": 10, "accent": 5}
BUDGET_FIRE = {"gray": 10, "accent": 8, "core": 2}


def check(sid, gray, acc, core, other, m):
    b = BUDGET_FIRE if "core" in m["budget"] else BUDGET
    ok = len(gray) <= b["gray"] and len(acc) <= b["accent"] and not other and (len(core) <= b.get("core", 0))
    return ok


def write_fx():
    fr = fire_pool_frames()
    sheet_png(fr).save(os.path.join(OUT_FX, "fire_pool.png"))
    gray, acc, core, other = palette_info(fr, R1)
    d = {
        "image": "fire_pool.png",
        "action": "fire_pool",
        "frameWidth": 48,
        "frameHeight": 24,
        "frames": len(fr),
        "directions": ["any"],
        "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column",
        "fps": 9,
        "frameDurationsMs": [110, 110, 110, 110],
        "loop": True,
        "pivot": {"x": 24, "y": 18},
        "palette": "parts/art/palette/lopad.json (floor 1 accent %s runtime swap + fx core X0/X1 fixed; NO gray, NO weapon secondary)" % ",".join(map(str, acc)),
        "anchor": "hitbox_center",
        "spawn": "fire_pool_ignite",
        "depth": "below",
        "scale": "allowed",
        "source": "structure",
        "areaTiles": [3, 3],
        "pivotNote": "피벗 (24,18) = 불붙은 웅덩이(독주 웅덩이 3x3 타일) 중심. 웅덩이 타원 48x11 위로 혓바닥 8개가 최대 14px 솟는다. 3x3 타일 영역을 덮으려면 같은 시트를 y-10/+10 두 장(두 번째는 1프레임 어긋나게) 또는 scale 정수 배율.",
        "note": "1-1 독주 웅덩이 불바다 루프 4f(이음새 없음). 층 램프 17~27 + 백열 코어(혓바닥 밑 심). 웅덩이 17/19/21 → 혓바닥 19 테두리·21 몸·23/25 안·X1 심 → 오르는 불티 23/25. 4초 지속 동안 반복 재생, 끝은 시스템이 알파로 지움.",
        "colors": {"gray": len(gray), "accent": len(acc), "core": len(core), "budget": "gray<=2 accent<=8 core<=2"},
    }
    with open(os.path.join(OUT_FX, "fire_pool.json"), "w", encoding="utf-8") as fp:
        json.dump(d, fp, ensure_ascii=False, indent=1)
    ok = len(gray) <= 2 and len(acc) <= 8 and len(core) <= 2 and not other
    print("%-14s %2d f 48x24  gray %2d accent %2d core %d  %s" % ("fx/fire_pool", len(fr), len(gray), len(acc), len(core), "OK" if ok else "OVER %s" % other))
    return fr, ok


# ====================================================================== 미리보기
def swap_img(im, src, dst):
    m = {rgb(a): rgb(b) for a, b in zip(src, dst)}
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            p = px[x, y]
            if p[3] and p[:3] in m:
                px[x, y] = m[p[:3]] + (p[3],)
    return out


def frame_img(sid, idx=0, floor=1):
    for s, frames, m in REG:
        if s == sid:
            im = frames[idx].image()
            if m["swap"] and floor == 2:
                im = swap_img(im, R1, R2)
            return im, m
    raise KeyError(sid)


def state_frame(sid, state):
    for s, frames, m in REG:
        if s == sid:
            return m["states"].get(state, m["states"]["idle"])[0]


def mock_room(floor, layout, wall_override=None, fx_items=(), w=30, h=17):
    """1배 목업. floor 1/2 타일셋. layout = [(sid, state, tx, ty)] tx,ty = footprint 왼쪽 위 타일."""
    tiles = Image.open(os.path.join(ROOT, "assets", "tiles", "stage%d.png" % floor)).convert("RGBA")
    meta = json.load(open(os.path.join(ROOT, "assets", "tiles", "stage%d.json" % floor)))

    def T(i):
        x, y = (i % 8) * 16, (i // 8) * 16
        return tiles.crop((x, y, x + 16, y + 16))

    img = Image.new("RGBA", (w * 16, h * 16), rgb(G[0]) + (255,))
    rf = meta["roomFloors"]
    for ty in range(h):
        for tx in range(w):
            hsh = (tx * 73856093 ^ ty * 19349663) & 0xffff
            if ty == 0:
                idx = [5, 21, 22][hsh % 3]
            elif ty == h - 1 or tx == 0 or tx == w - 1:
                idx = 6
            else:
                kind = "trial" if tx < w // 2 else "rest"
                idx = rf[kind][hsh % 4]
            img.alpha_composite(T(idx), (tx * 16, ty * 16))
    # 기존 소품 8종 (13~20) — 구조물과 구분되는지 비교용
    for i, (tx, ty) in enumerate([(5, 6), (9, 6), (2, 10), (11, 15), (21, 11), (26, 5), (16, 4), (13, 2)]):
        img.alpha_composite(T(13 + i), (tx * 16, ty * 16))
    if wall_override:
        for (sid, state, tx, ty) in wall_override:
            fi, m = frame_img(sid, state_frame(sid, state), floor)
            img.alpha_composite(fi, (tx * 16, ty * 16))
    # 바닥 깊이 먼저, 그다음 y 정렬
    items = []
    for (sid, state, tx, ty) in layout:
        fi, m = frame_img(sid, state_frame(sid, state), floor)
        fw, fh = m["footprint"]
        px_ = tx * 16 + fw * 8 - fi.width // 2
        py_ = (ty + fh) * 16 - fi.height
        items.append((0 if m["depth"] == "floor" else 1, (ty + fh) * 16, fi, px_, py_))
    for (fx_im, x, y) in fx_items:
        items.append((0, y, fx_im, x, y))
    # 주인공·적
    pl = Image.open(os.path.join(ROOT, "assets", "sprites", "player", "player_idle.png")).convert("RGBA").crop((0, 0, 16, 24))
    en = Image.open(os.path.join(ROOT, "assets", "sprites", "enemies", "dummy_idle.png")).convert("RGBA").crop((0, 0, 16, 24))
    if floor == 2:
        pl = swap_img(pl, R1, R2)
        en = swap_img(en, R1, R2)
    for (im, tx, ty) in [(pl, 14, 9), (en, 18, 12)]:
        sh = Image.new("RGBA", (12, 3), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse((0, 0, 11, 2), fill=(0, 0, 0, 140))
        items.append((1, ty * 16 + 16, sh, tx * 16 + 2, ty * 16 + 14))
        items.append((1, ty * 16 + 16, im, tx * 16, ty * 16 + 16 - 24))
    items.sort(key=lambda t: (t[0], t[1]))
    for (_, _, im, x, y) in items:
        img.alpha_composite(im, (x, y))
    return img


def preview(fire):
    S = 3
    pad = 8
    rows = []
    for sid, frames, m in REG:
        rows.append((sid, frames, m))
    rows.append(("fx/fire_pool", fire, {"states": {"active": [0, 1, 2, 3]}, "footprint": "-", "swap": False}))
    # 시트 블록: 2단 배치
    blocks = []
    for sid, frames, m in rows:
        fw, fh = frames[0].w, frames[0].h
        per = max(1, (760 - 16) // (fw * S))
        rows_ = [frames[i:i + per] for i in range(0, len(frames), per)]
        big = Image.new("RGBA", (min(len(frames), per) * fw * S, len(rows_) * (fh * S + 4) - 4), (0, 0, 0, 0))
        for ri, rf in enumerate(rows_):
            sh = sheet_png(rf)
            big.alpha_composite(sh.resize((sh.width * S, sh.height * S), Image.NEAREST), (0, ri * (fh * S + 4)))
        lab = "%s  %dx%d  fp %s  %s" % (sid, fw, fh, m["footprint"], "  ".join("%s=%s" % (k, ",".join(map(str, v))) for k, v in m["states"].items()))
        blocks.append((lab, big))
    col_w = 760
    # 왼쪽/오른쪽 열에 위에서부터 쌓기
    cols = [[], []]
    hts = [0, 0]
    for b in blocks:
        i = 0 if hts[0] <= hts[1] else 1
        cols[i].append(b)
        hts[i] += b[1].height + 22 + 13 * (len(b[0]) // 100)
    m1 = mock_room(1, MOCK1, wall_override=WALL1, fx_items=[(fire[0].image(), 5 * 16 - 0, 12 * 16 - 6)])
    m2 = mock_room(2, MOCK2)
    W = pad + col_w * 2 + pad
    H = pad + max(hts) + 30 + m1.height + pad
    out = Image.new("RGB", (W, H), (58, 58, 62))
    d = ImageDraw.Draw(out)
    for ci, col in enumerate(cols):
        y = pad
        for lab, big in col:
            x = pad + ci * col_w
            lines = [lab[i:i + 100] for i in range(0, len(lab), 100)]
            for li, ln in enumerate(lines):
                d.text((x, y + li * 13), ln, fill=(235, 235, 235), font=FONT)
            y += 13 * (len(lines) - 1)
            bg = Image.new("RGBA", big.size, rgb(G[1]) + (255,))
            bg.alpha_composite(big)
            out.paste(bg.convert("RGB"), (x, y + 14))
            y += big.height + 22
    y0 = pad + max(hts) + 10
    d.text((pad, y0), "1x mock: floor 1 (trial | rest floor)", fill=(235, 235, 235), font=FONT)
    d.text((pad + m1.width + 16, y0), "1x mock: floor 2", fill=(235, 235, 235), font=FONT)
    out.paste(m1.convert("RGB"), (pad, y0 + 16))
    out.paste(m2.convert("RGB"), (pad + m1.width + 16, y0 + 16))
    out.save(os.path.join(HERE, "preview.png"))
    # 960x540 근사 (1배 목업 2배)
    both = Image.new("RGB", (m1.width * 2, m1.height * 2 * 2 + 8), (58, 58, 62))
    both.paste(m1.resize((m1.width * 2, m1.height * 2), Image.NEAREST).convert("RGB"), (0, 0))
    both.paste(m2.resize((m2.width * 2, m2.height * 2), Image.NEAREST).convert("RGB"), (0, m1.height * 2 + 8))
    both.save(os.path.join(HERE, "preview_mock_x2.png"))


# 목업 배치 (sid, state, footprint 왼쪽 위 타일 x, y)
MOCK1 = [
    ("crate_f1", "idle", 2, 2), ("crate_f1", "idle", 3, 2), ("crate_f1", "broken", 2, 4),
    ("chest", "idle", 6, 3), ("grave", "idle", 10, 3), ("barrel", "idle", 3, 8), ("barrel", "active", 7, 9),
    ("still", "active", 12, 7), ("ledger", "idle", 18, 3), ("cask", "ready", 22, 3), ("counter", "used1", 20, 7),
    ("bonfire", "active", 24, 11), ("chest", "used", 9, 13), ("ledger", "used", 16, 13), ("cask", "active", 19, 13),
    ("barrel", "broken", 3, 13),
]
WALL1 = [("cellar_wall", "idle", 13, 0), ("cellar_wall", "damaged2", 15, 0), ("cellar_wall", "idle_top", 0, 6)]
MOCK2 = [
    ("crate_f2", "idle", 2, 2), ("crate_f2", "idle", 3, 2), ("crate_f2", "broken", 2, 4),
    ("chest", "idle", 6, 3), ("grave", "idle_f2", 10, 3), ("card_table", "idle", 2, 7), ("chip_exchange", "idle", 7, 8),
    ("dog_ring", "active", 20, 2), ("bet_bell", "idle", 26, 7), ("roulette", "active", 10, 11), ("pawn", "idle", 16, 9),
    ("bonfire", "active", 24, 12), ("card_table", "used", 2, 12), ("bet_bell", "used", 27, 10), ("pawn", "used", 18, 13),
]


def main():
    build_all()
    print("%-14s %3s %-6s %-6s  colors" % ("id", "f", "size", "fp"))
    all_ok = True
    for sid, frames, m in REG:
        gray, acc, core, other = export(sid, frames, m)
        ok = check(sid, gray, acc, core, other, m)
        all_ok &= ok
        print("%-14s %2d f %2dx%-2d fp %s solid %-5s gray %2d accent %d core %d  %s" % (
            sid, len(frames), frames[0].w, frames[0].h, m["footprint"], m["solid"], len(gray), len(acc), len(core),
            "OK" if ok else "OVER %s" % other))
    fire, ok = write_fx()
    all_ok &= ok
    # 반투명 검사
    print("palette budget:", "PASS" if all_ok else "FAIL")
    preview(fire)



if __name__ == "__main__":
    main()
