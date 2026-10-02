#!/usr/bin/env python3
"""LOPAD UI 키트 빌드 (32라운드 전폭 재설계: 무채 + 층 강조색, 종이·잉크·일기장) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/ui/build.py
입력: parts/art/palette/lopad.json, assets/tiles/stage1.png, assets/sprites/{player,enemies,weapons}/* (목업용)
산출: assets/sprites/ui/*.png + *.json  (UI 파트가 assets/ui/ 로 복사해 쓴다)
      parts/art/work/ui/preview_kit.png   키트 전체 2배 + 9-slice 늘림 검증
      parts/art/work/ui/preview_mock.png  960x540 HUD·메뉴 목업 (1층 타일 배경)
      parts/art/work/ui/preview_icons.png 아이콘 8배 (종이·잉크 두 배경)

색 규칙
  - 무채 G00~G15 만 기본. 유채는 1층 호박 램프(인덱스 16~27)로 그리고 시스템/UI 가 층 램프로 스왑·틴트.
  - 종이 = G12/G13/G14, 잉크 = G00/G01, 잉크 번짐·연필 = G03/G09/G10/G11.
  - 아이콘: 무채 ≤5 + 강조 ≤2, 바깥 K 윤곽 1px (16 캔버스 안에 1px 여백).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "pixel-art-studio", "scripts"))
from pixelstudio import Sprite  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

OUT = os.path.join(ROOT, "assets", "sprites", "ui")
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8") as fp:
    PAL = json.load(fp)
G = PAL["gray"]
A = PAL["floors"][0]["ramp"]  # 1층 잔(호박). 인덱스 16+i
PALETTE = G + A

# 문자 지도 범례 (아이콘·커서·작은 그림)
LEG = {
    "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4], "5": G[5], "6": G[6], "7": G[7],
    "8": G[8], "9": G[9], "a": G[10], "b": G[11], "c": G[12], "d": G[13], "e": G[14], "w": G[15],
    "I": A[0], "D": A[1], "T": A[3], "S": A[4], "B": A[5], "M": A[6], "L": A[7], "N": A[8], "G": A[9], "F": A[11],
}
NAME = {v: k for k, v in LEG.items()}

REPORT = []


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def rgba(h, a=255):
    return rgb(h) + (a,)


def blit(s, rows, ox=0, oy=0):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            s.px(ox + i, oy + j, LEG[ch])


def new(w, h):
    return Sprite(w, h, palette=PALETTE)


def check(name, s, allow_semi=0, allow_iso=0):
    """고립·반투명·색 수 검사 → REPORT."""
    info = s.stats(print_=False)
    img = s.composite(1)
    cols = set()
    for i in range(1, s.n_frames + 1):
        for c, n in s.used_colors(frame=i).items():
            cols.add(c[:3])
    grays = sum(1 for c in cols if "#%02x%02x%02x" % c in G)
    accs = sum(1 for c in cols if "#%02x%02x%02x" % c in A)
    other = len(cols) - grays - accs
    iso = len(info["isolated_px"])
    semi = info["semi_alpha_px"]
    REPORT.append((name, "%dx%d" % (s.w, s.h), grays, accs, other, iso, semi))
    return img


def save_json(name, data):
    data = {"image": name + ".png", **data,
            "palette": "parts/art/palette/lopad.json (gray G00-G15 + floor-1 accent 16-27; runtime swap/tint)"}
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=1)


def export(name, s, meta, frames=None):
    """1x PNG(+가로 프레임 스트립) + JSON."""
    if s.n_frames == 1:
        s.save_png(os.path.join(OUT, name + ".png"))
    else:
        strip = Image.new("RGBA", (s.w * s.n_frames, s.h), (0, 0, 0, 0))
        for i in range(s.n_frames):
            strip.alpha_composite(s.composite(i + 1), (i * s.w, 0))
        strip.save(os.path.join(OUT, name + ".png"))
    save_json(name, meta)


# ============================================================ 9-slice 유틸 (미리보기·목업용 — 엔진은 자체 NineSlice)
def nine(img, sl, w, h):
    """img 를 9-slice 로 w x h 에 늘린다 (가장자리·가운데는 NEAREST 늘림)."""
    L, R, T, Bm = sl["left"], sl["right"], sl["top"], sl["bottom"]
    iw, ih = img.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def part(x0, y0, x1, y1, dx, dy, dw, dh):
        if x1 <= x0 or y1 <= y0 or dw <= 0 or dh <= 0:
            return
        p = img.crop((x0, y0, x1, y1))
        if p.size != (dw, dh):
            p = p.resize((dw, dh), Image.NEAREST)
        out.paste(p, (dx, dy))

    cw, ch = w - L - R, h - T - Bm
    part(0, 0, L, T, 0, 0, L, T)
    part(iw - R, 0, iw, T, w - R, 0, R, T)
    part(0, ih - Bm, L, ih, 0, h - Bm, L, Bm)
    part(iw - R, ih - Bm, iw, ih, w - R, h - Bm, R, Bm)
    part(L, 0, iw - R, T, L, 0, cw, T)
    part(L, ih - Bm, iw - R, ih, L, h - Bm, cw, Bm)
    part(0, T, L, ih - Bm, 0, T, L, ch)
    part(iw - R, T, iw, ih - Bm, w - R, T, R, ch)
    part(L, T, iw - R, ih - Bm, L, T, cw, ch)
    return out


def tile_fill(dst, tile, x0, y0, w, h):
    tw, th = tile.size
    region = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y in range(0, h, th):
        for x in range(0, w, tw):
            region.alpha_composite(tile, (x, y))
    dst.alpha_composite(region, (x0, y0))


# ============================================================ 1. 패널 틀
PAPER_SL = {"left": 24, "right": 24, "top": 24, "bottom": 24}
PAPER_INNER = {"left": 12, "right": 12, "top": 12, "bottom": 12}  # 글·타일 질감을 넣을 안쪽 여백 (안쪽 선 안)


def paper_tile():
    """32x32 타일링 종이 질감 (G13 바탕 + G12 2~3px 섬유 소량). 가장자리 1px 는 바탕색만 → 이음새 없음."""
    s = new(32, 32)
    s.rect(0, 0, 31, 31, G[13])
    import random
    rnd = random.Random(7)
    for _ in range(11):
        x, y = rnd.randrange(1, 28), rnd.randrange(1, 31)
        c = G[12] if rnd.random() < 0.8 else G[14]
        n = rnd.choice([2, 2, 3])
        if rnd.random() < 0.3:
            s.rect(x, y, x, y + n - 1, c)     # 세로 섬유도 섞어 줄무늬 주기 깨기
        else:
            s.rect(x, y, x + n - 1, y, c)
    return s


def octagon(s, inset, cham, color, size):
    """inset 만큼 들어간 사각형을 cham 길이 모따기한 팔각형 선."""
    a, b = inset, size - 1 - inset
    s.rect(a + cham, a, b - cham, a, color)
    s.rect(a + cham, b, b - cham, b, color)
    s.rect(a, a + cham, a, b - cham, color)
    s.rect(b, a + cham, b, b - cham, color)
    s.line(a, a + cham, a + cham, a, color)
    s.line(b - cham, a, b, a + cham, color)
    s.line(a, b - cham, a + cham, b, color)
    s.line(b - cham, b, b, b - cham, color)


def panel_paper():
    size = 80
    s = new(size, size)
    s.rect(0, 0, size - 1, size - 1, G[13])
    # 종이 가장자리 (빛 좌상단): 윗·왼쪽 2줄 G14, 아래·오른쪽 G12 + 맨 바깥 G11 그늘
    s.rect(0, 0, size - 1, 1, G[14]); s.rect(0, 0, 1, size - 1, G[14])
    s.rect(2, size - 2, size - 1, size - 2, G[12]); s.rect(size - 2, 2, size - 2, size - 1, G[12])
    s.rect(1, size - 1, size - 1, size - 1, G[11]); s.rect(size - 1, 1, size - 1, size - 1, G[11])
    # 바깥 잉크 선: 번짐(G03) 을 안쪽에 먼저 깔고 그 위에 잉크(G01) — 2px 무게, 팔각 모따기 7
    octagon(s, 4, 6, G[3], size)
    octagon(s, 3, 7, G[1], size)
    # 안쪽 가는 선 (G09) 평행 팔각
    octagon(s, 8, 7, G[9], size)
    # 코너 삼각 여백에 손으로 찍은 잉크 점 (3px 군집) — 좌상단·우하단만
    s.rect(1, 1, 2, 1, G[9]); s.px(1, 2, G[9])
    s.rect(size - 3, size - 2, size - 2, size - 2, G[9]); s.px(size - 2, size - 3, G[9])
    return s


INK_SL = {"left": 12, "right": 12, "top": 12, "bottom": 12}
INK_INNER = {"left": 5, "right": 5, "top": 5, "bottom": 5}
INK_ALPHA = 218  # 가운데 G01 반투명 (약 85%)


def panel_ink():
    size = 48
    s = new(size, size)
    s.rect(0, 0, size - 1, size - 1, rgba(G[1], INK_ALPHA))
    # 바깥 테: 위·왼쪽 G02 림(빛), 아래·오른쪽 G00 (그늘). 모두 불투명. 코너 1px 모따기(투명)
    s.rect(0, 0, size - 1, 0, G[2]); s.rect(0, 0, 0, size - 1, G[2])
    s.rect(0, size - 1, size - 1, size - 1, G[0]); s.rect(size - 1, 0, size - 1, size - 1, G[0])
    for (x, y) in [(0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)]:
        s.px(x, y, (0, 0, 0, 0))
    # 안쪽 1px 어두운 잉크선 (G00) — 림 바로 안
    s.rect(1, 1, size - 2, size - 2, G[0], fill=False)
    # 코너 안쪽 꺾쇠 (G03, 길이 4): 종이 패널의 꺾쇠와 짝
    for (x, y, dx, dy) in [(3, 3, 1, 1), (size - 4, 3, -1, 1), (3, size - 4, 1, -1), (size - 4, size - 4, -1, -1)]:
        for i in range(4):
            s.px(x + dx * i, y, G[3]); s.px(x, y + dy * i, G[3])
    return s


MINI_SL = {"left": 10, "right": 10, "top": 10, "bottom": 10}


def minimap_frame():
    size = 32
    s = new(size, size)
    s.rect(0, 0, size - 1, size - 1, G[1])
    s.rect(0, 0, size - 1, size - 1, G[0], fill=False)
    s.rect(1, 1, size - 2, size - 2, G[3], fill=False)   # 안쪽 밝은 선 (지도 종이 테두리 느낌)
    s.rect(2, 2, size - 3, size - 3, G[0], fill=False)
    # 좌상단 코너: 접힌 지도 귀 (G05 삼각 3px) / 우하단: 나침 눈금 (작은 십자 G05)
    s.px(3, 3, G[5]); s.px(4, 3, G[5]); s.px(3, 4, G[5])
    cx, cy = size - 6, size - 6
    s.px(cx, cy - 1, G[5]); s.px(cx, cy + 1, G[5]); s.px(cx - 1, cy, G[5]); s.px(cx + 1, cy, G[5]); s.px(cx, cy, G[7])
    return s


# ============================================================ 2. 게이지
GAUGE_SL = {"left": 4, "right": 4, "top": 1, "bottom": 1}
GAUGE_INSET = {"left": 2, "right": 2, "top": 1, "bottom": 1}


def gauge_frame():
    w, h = 24, 10
    s = new(w, h)
    s.rect(0, 0, w - 1, h - 1, G[1], fill=False)
    for (x, y) in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        s.px(x, y, (0, 0, 0, 0))
    s.rect(1, 1, w - 2, h - 2, G[2])              # 빈 트랙
    s.rect(1, 1, 1, h - 2, G[3]); s.rect(w - 2, 1, w - 2, h - 2, G[3])   # 양 끝 캡 (fill 은 x=2 부터)
    s.rect(2, h - 2, w - 3, h - 2, G[0])         # 트랙 바닥 1px 그늘 (fill 이 덮음)
    return s


BOSS_SL = {"left": 8, "right": 8, "top": 3, "bottom": 3}
BOSS_INSET = {"left": 5, "right": 5, "top": 3, "bottom": 3}


def gauge_boss():
    w, h = 32, 14
    s = new(w, h)
    s.rect(0, 0, w - 1, h - 1, G[0])                    # 바깥 잉크
    s.rect(1, 1, w - 2, h - 2, G[3], fill=False)         # 밝은 안쪽 선
    s.rect(2, 2, w - 3, h - 3, G[1], fill=False)         # 어두운 선
    s.rect(3, 3, w - 4, h - 4, G[2])                     # 트랙
    for (x, y) in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        s.px(x, y, (0, 0, 0, 0))
    # 캡: 트랙 양 끝 2px 를 G03 로, 그 바깥에 세로 쐐기(G05) 장식
    s.rect(3, 3, 4, h - 4, G[3]); s.rect(w - 5, 3, w - 4, h - 4, G[3])
    for x0, dx in [(1, 1), (w - 2, -1)]:
        s.px(x0, 6, G[5]); s.px(x0, 7, G[5]); s.px(x0 + dx, 5, G[5]); s.px(x0 + dx, 8, G[5])
    s.rect(5, h - 4, w - 6, h - 4, G[0])                 # 트랙 바닥 그늘
    return s


def gauge_fill():
    s = new(1, 8)
    for y, c in enumerate([A[7], A[6], A[5], A[5], A[5], A[4], A[4], A[3]]):
        s.px(0, y, c)
    return s


def gauge_fill_gray():
    s = new(1, 8)
    for y, c in enumerate([G[15], G[14], G[13], G[13], G[13], G[11], G[11], G[10]]):
        s.px(0, y, c)
    return s


# ============================================================ 3. 아이콘 16x16 (1px 여백 안에 그리고 바깥 K 윤곽)
ICONS = {}

ICONS["icon_gold"] = [  # 전표: 접힌 귀 종이쪽 + 글줄 + 호박 도장
    "................",
    "..dddddddddd....",
    "..dddddddddKd...",
    "..dd9999999Kdd..",
    "..dddddddddddd..",
    "..dd99999ddddd..",
    "..dddddddddddd..",
    "..dd999999dddd..",
    "..dddddddddddd..",
    "..dd9999ddTBBd..",
    "..ddddddddBBTd..",
    "..dddddddddddd..",
    "..dddddddddddd..",
    "..9999999999c9..",
    "................",
    "................",
]
ICONS["icon_potion"] = [  # 잔의 독주 병: 코르크 + 목 + 둥근 몸통, 호박 술
    "................",
    "......7777......",
    "......7777......",
    "......dddd......",
    "......dddd......",
    "......ddd9......",
    "....dddddddd....",
    "...dddddddddd...",
    "...dwLBBBBBBT...",
    "...dwBBBBBBTT...",
    "...dBBBBBBBTT...",
    "...dBBBBBBTTT...",
    "...dBBBBBTTTT...",
    "....9TTTTTTT....",
    "................",
    "................",
]
ICONS["icon_souls"] = [  # 전장의 영혼: 회색 혼불, 눈 두 틈, 심지 호박 2px
    "................",
    "........d.......",
    ".......dd.......",
    ".......ddd......",
    "......dddd......",
    "......ddddd.....",
    ".....dddddd.....",
    ".....dKddKd.....",
    "....dddddddd....",
    "....ddddddd9....",
    "....dddLLdd9....",
    "....ddddddd9....",
    "....9dd9dd99....",
    ".....9..9.9.....",
    "................",
    "................",
]
ICONS["icon_sense"] = [  # 감각: 눈 + 위로 뻗는 눈금 3개
    "................",
    ".......d........",
    "...d...d...d....",
    "....d..d..d.....",
    "................",
    ".....dddddd.....",
    "...dddddddddd...",
    "..ddddBBBBdddd..",
    ".dddddBLBKddddd.",
    "..ddddBBKKdddd..",
    "...ddddBBddddd..",
    ".....dddddd.....",
    "................",
    "................",
    "................",
    "................",
]
ICONS["icon_save"] = [  # 일기장(닫힘): 어두운 표지 + 책등 + 종이 단면 + 끈 + 호박 책갈피
    "................",
    "..13333333B.....",
    "..13333333Bd....",
    "..13333333Bd....",
    "..1333333333d...",
    "..1333333333d...",
    "..1399999999d...",
    "..13333333339...",
    "..1333333333d...",
    "..1333333333d...",
    "..1333333333d...",
    "..1333333333d...",
    "..1333333333d...",
    "..1333333333d...",
    "................",
    "................",
]
ICONS["icon_sound"] = [  # 소리: 나팔 + 음파 2줄
    "................",
    "........d.......",
    ".......dd...d...",
    "......ddd..d.d..",
    "..dddddddd.d.d..",
    "..d9ddddddd..d..",
    "..d9dddddd.d.d..",
    "..d9dddddd.d.d..",
    "..d9ddddddd..d..",
    "..dddddddd.d.d..",
    "......ddd..d.d..",
    ".......dd...d...",
    "........d.......",
    "................",
    "................",
    "................",
]
ICONS["icon_mute"] = [  # 음소거: 나팔 + 가위표 (1px 사선, 바깥 윤곽으로 3px 굵기)
    "................",
    "........d.......",
    ".......dd.......",
    "......ddd.......",
    "..dddddddd......",
    "..d9dddddd.d..d.",
    "..d9ddddddddd...",
    "..d9dddddd.dd...",
    "..d9dddddddd.d..",
    "..dddddddd.d..d.",
    "......ddd.......",
    ".......dd.......",
    "........d.......",
    "................",
    "................",
    "................",
]
ICONS["icon_boss"] = [  # 본영 문: 아치 돌틀 + 두 짝 문(어두움) + 호박 문장
    "................",
    ".....dddddd.....",
    "....d9dddd9d....",
    "...d9ddBBdd9d...",
    "...d9ddBBdd9d...",
    "...d9d3333d9d...",
    "...d9d3113d9d...",
    "...d9d3113d9d...",
    "...d9d3113d9d...",
    "...d9d3113d9d...",
    "...d9d9113d9d...",
    "...d9d3113d9d...",
    "...d9d3113d9d...",
    "...dddddddddd...",
    "................",
    "................",
]
ICONS["icon_exit"] = [  # 오르는 계단: 4단, 위에서 떨어지는 호박빛
    "................",
    "..........LL....",
    "..........LL....",
    ".........ddddd..",
    ".........d9999..",
    ".........d9999..",
    "......dddd9999..",
    "......d999.9999.",
    "......d999.9999.",
    "...dddd999.9999.",
    "...d999999.9999.",
    "...d999999.9999.",
    "...d999999.9999.",
    "...9999999.9999.",
    "................",
    "................",
]

MINI = {  # 8x8 미니맵 방 아이콘 (G14 단색, 윤곽 없음 — 어두운 지도 위)
    "mini_start": [
        "..eeee..",
        ".e....e.",
        ".e....e.",
        ".e.ee.e.",
        ".e.ee.e.",
        ".e.ee.e.",
        ".e.ee.e.",
        "eee..eee",
    ],
    "mini_trial": [
        "ee....ee",
        "eee..eee",
        ".eeeeee.",
        "..eeee..",
        "..eeee..",
        ".eeeeee.",
        "eee..eee",
        "ee....ee",
    ],
    "mini_rest": [
        "........",
        "eeeeeee.",
        ".eeeee..",
        ".eeeee..",
        "..eee...",
        "...e....",
        "...e....",
        "..eee...",
    ],
    "mini_boss": [
        "........",
        "e..ee..e",
        "e.eeee.e",
        "ee.ee.ee",
        "eeeeeeee",
        "eeeeeeee",
        ".eeeeee.",
        "........",
    ],
}
ICON_ORDER = ["icon_hp", "icon_gold", "icon_potion", "icon_souls", "icon_sense", "icon_save",
              "icon_sound", "icon_mute", "icon_boss", "icon_exit",
              "mini_start", "mini_trial", "mini_rest", "mini_boss"]


def icon_hp():
    """붕대 두 가닥 X + 피 얼룩. 코드로 띠를 만든다 (사선 띠 폭 4)."""
    s = new(16, 16)
    for y in range(1, 15):
        for x in range(1, 15):
            a = abs(x - y) <= 2
            b = abs(x + y - 15) <= 2
            if a or b:
                s.px(x, y, G[13])
    # 띠 아래쪽 가장자리 그늘 (빛 좌상단): 각 띠의 오른쪽/아래 경계 1줄
    for y in range(1, 15):
        for x in range(1, 15):
            if s.get(x, y) and (x - y == 2 or x + y - 15 == 2):
                s.px(x, y, G[9])
    # 거즈 패드: 띠 양 끝 2x2 G11 군집 (반창고의 패드)
    for (x, y) in [(2, 2), (12, 2), (2, 12), (12, 12)]:
        s.rect(x, y, x + 1, y + 1, G[11])
    # 피 얼룩 (교차점 오른쪽 아래, 호박 base + shadow)
    for (x, y, c) in [(8, 8, A[5]), (9, 8, A[5]), (8, 9, A[5]), (9, 9, A[4]), (10, 9, A[4]), (9, 10, A[4]), (7, 8, A[5])]:
        s.px(x, y, c)
    return s


def build_icons():
    canv = {}
    for name in ICON_ORDER:
        if name == "icon_hp":
            s = icon_hp()
        elif name.startswith("mini_"):
            s = new(8, 8)
            blit(s, MINI[name])
            canv[name] = s
            check(name, s)
            continue
        else:
            s = new(16, 16)
            blit(s, ICONS[name])
        s.outline(G[0], where="outside")
        canv[name] = s
        check(name, s)
    # 시트: 8열 x 2행, 16x16 칸. 8x8 아이콘은 칸 좌상단 (4,4) 에.
    cols = 8
    rows = (len(ICON_ORDER) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 16, rows * 16), (0, 0, 0, 0))
    frames = {}
    for i, name in enumerate(ICON_ORDER):
        r, c = divmod(i, cols)
        img = canv[name].composite(1)
        off = 4 if img.width == 8 else 0
        sheet.alpha_composite(img, (c * 16 + off, r * 16 + off))
        frames[name] = {"index": i, "x": c * 16 + off, "y": r * 16 + off, "w": img.width, "h": img.height}
    sheet.save(os.path.join(OUT, "icons.png"))
    save_json("icons", {
        "cellWidth": 16, "cellHeight": 16, "columns": cols, "rows": rows,
        "frameIndex": "row * columns + column (16x16 cell). 8x8 icons sit at (+4,+4) inside their cell; use x/y/w/h for exact crop",
        "frames": frames,
        "anchor": "ui",
        "notes": {
            "icon_hp": "bandage cross + blood (accent 20/21)", "icon_gold": "voucher slip (names.gold) + amber seal",
            "icon_potion": "bottle of Zan liquor (names.potion)", "icon_souls": "battlefield soul wisp (names.souls)",
            "icon_sense": "eye + 3 ticks (stats.sense)", "icon_save": "closed diary (savesLeft)",
            "icon_sound": "horn + waves", "icon_mute": "horn + cross",
            "icon_boss": "headquarters gate (bossUnlocked)", "icon_exit": "ascending stairs (exitOpen)",
            "mini_*": "8x8 single-color G14 room glyphs for minimap: start/trial/rest/boss"},
    })
    return canv, sheet


# ============================================================ 4. 커서·구분선
def cursor(dark=True):
    """깃펜 촉 ▶ 2프레임: 0 = 정지, 1 = 1px 앞으로 + 촉 끝 잉크 방울."""
    ink, slit = (G[1], G[9]) if dark else (G[14], G[9])
    s = new(8, 8)
    nib = ["........", ".1......", ".11.....", ".111....", ".1K11...", ".11111..", ".1111...", ".111...."]
    # 위 지도는 '길쭉한 촉'이 아니라 ▶ 에 가깝게 다시: 7줄 삼각
    nib = [
        "........",
        ".1......",
        ".11.....",
        ".111....",
        ".1K11...",
        ".111....",
        ".11.....",
        ".1......",
    ]
    for j, row in enumerate(nib):
        for i, ch in enumerate(row):
            if ch == "1":
                s.px(i, j, ink)
            elif ch == "K":
                s.px(i, j, slit)
    # 촉의 홈: 끝에서 안쪽으로 2px (K)
    s.px(3, 4, slit)
    s.set_duration(420, [1])
    s.add_frame(copy=False)
    s.use(frame=2)
    for j, row in enumerate(nib):
        for i, ch in enumerate(row):
            if ch == "1":
                s.px(i + 1, j, ink)
            elif ch == "K":
                s.px(i + 1, j, slit)
    s.px(4, 4, slit)
    s.px(6, 5, A[5])    # 잉크 방울 (호박 1px: 의도된 고립 픽셀)
    s.set_duration(260, [2])
    s.use(frame=1)
    return s


def rule(dark=True):
    s = new(1, 4)
    if dark:
        s.px(0, 1, G[0]); s.px(0, 2, G[10])
    else:
        s.px(0, 1, G[9]); s.px(0, 2, G[3])
    return s


# ============================================================ 5. 타이틀 일기장 · 도장
def ink_scribble(s, x0, y0, x1, seed, color, step=6):
    """글줄 흉내: 2~5px 잉크 대시를 1~2px 간격으로. 1px 대시는 안 쓴다(고립 방지)."""
    import random
    rnd = random.Random(seed)
    y = y0
    x = x0
    while x < x1:
        n = rnd.choice([2, 3, 3, 4, 5])
        if x + n > x1:
            break
        s.rect(x, y, x + n - 1, y, color)
        if rnd.random() < 0.25:
            s.px(x + rnd.randrange(n), y - 1, color)  # 위로 삐친 획 (대시에 붙어 있어 고립 아님)
        x += n + rnd.choice([1, 2, 2, 3])
    return s


def title_diary():
    W, H = 160, 96
    s = new(W, H)
    # 표지 (어두운 가죽 G03, 윤곽 K, 책등 G01)
    s.rect(1, 1, W - 2, H - 2, G[3])
    s.rect(1, 1, W - 2, H - 2, G[0], fill=False)
    s.rect(2, 2, W - 3, 2, G[5]); s.rect(2, 2, 2, H - 3, G[5])   # 표지 윗·왼 빛
    # 쌓인 종이 단면 (페이지 아래쪽 2줄·오른쪽 2줄 G11/G12 번갈아)
    def page(x0, y0, x1, y1, gutter_right):
        s.rect(x0 + 2, y0 + 2, x1 + 2, y1 + 2, G[10])          # 아래 그림자
        s.rect(x0 + 1, y0 + 1, x1 + 1, y1 + 1, G[11])          # 종이 단면
        s.rect(x0, y0, x1, y1, G[13])
        s.rect(x0, y0, x1, y0, G[14]); s.rect(x0, y0, x0, y1, G[14])
        # 안쪽 홈(제본부) 그늘: 홈 쪽 3열 G12
        if gutter_right:
            s.rect(x1 - 2, y0 + 1, x1, y1, G[12])
        else:
            s.rect(x0 + 1, y0 + 1, x0 + 3, y1, G[12])
        # 괘선 (G11) 7px 간격
        for y in range(y0 + 10, y1 - 3, 7):
            s.rect(x0 + 4, y, x1 - 4, y, G[11])
    LX0, LX1, RX0, RX1, PY0, PY1 = 7, 76, 83, 152, 6, 86
    page(LX0, PY0, LX1, PY1, True)
    page(RX0, PY0, RX1, PY1, False)
    # 제본부: 가운데 어두운 홈 + 실 꿰맨 자국
    s.rect(77, 2, 82, H - 3, G[1])
    s.rect(79, 2, 80, H - 3, G[0])
    for y in range(10, H - 8, 9):
        s.rect(78, y, 81, y, G[7]); s.rect(78, y + 1, 81, y + 1, G[7])
    # 왼쪽 페이지: 손글씨 (잉크 G01) — 첫 줄은 짧은 제목처럼 굵게(2줄)
    s.rect(LX0 + 8, PY0 + 7, LX0 + 30, PY0 + 8, G[1])
    for k, y in enumerate(range(PY0 + 17, PY1 - 6, 7)):
        ink_scribble(s, LX0 + 6, y - 2, LX1 - 6 - (k % 3) * 9, seed=11 + k, color=G[1])
    # 오른쪽 페이지: 두 줄만 쓰다 만 글 + 잉크 얼룩 + 술잔 자국(호박 고리)
    for k, y in enumerate(range(PY0 + 17, PY0 + 32, 7)):
        ink_scribble(s, RX0 + 7, y - 2, RX1 - 20 - k * 14, seed=31 + k, color=G[1])
    # 잉크 얼룩 (G01 덩어리 + 붙은 방울)
    s.circle(RX0 + 50, PY0 + 52, 3, G[1], fill=True)
    s.rect(RX0 + 47, PY0 + 54, RX0 + 54, PY0 + 55, G[1])
    s.circle(RX0 + 56, PY0 + 56, 1, G[1], fill=True)
    s.px(RX0 + 54, PY0 + 50, G[1]); s.px(RX0 + 53, PY0 + 50, G[1]); s.px(RX0 + 53, PY0 + 49, G[1])
    # 술잔 자국: 반지름 9 고리 (호박 shadow1 19), 군데군데 끊김 + 안쪽 번짐(base_dark 20 → 1px)
    cx, cy = RX0 + 26, PY0 + 58
    ring = new(W, H)
    ring.circle(cx, cy, 10, A[3], fill=False)
    ring.circle(cx, cy, 9, A[4], fill=False)
    ring.circle(cx, cy, 10, A[3], fill=False)
    import random
    rnd = random.Random(5)
    rimg = ring.composite(1)
    for y in range(H):
        for x in range(W):
            if rimg.getpixel((x, y))[3] and rnd.random() < 0.78:
                s.px(x, y, rimg.getpixel((x, y)))
    # 고리 아래쪽은 더 진하게(술이 고인 쪽): 2px 두께
    for x in range(cx - 6, cx + 7):
        s.px(x, cy + 10, A[4]); s.px(x, cy + 9, A[3])
    s.despeckle(min_cluster=2)
    # 책갈피 끈 (호박 base, 가장자리 base_dark): 제본부 위에서 오른쪽 페이지로 늘어짐
    s.rect(81, 0, 83, 0, A[4])
    for y in range(0, 30):
        x = 84 + (y * 7) // 30
        s.px(x, y, A[5]); s.px(x + 1, y, A[5]); s.px(x + 2, y, A[4])
    s.rect(91, 30, 93, 33, A[4]); s.px(92, 34, A[4]); s.px(92, 35, A[4])   # 끈 끝 매듭
    # 가죽 끈 (표지 묶음): 왼쪽 아래 모서리를 사선으로 감는 가는 끈 (G07 + G05 그늘) + K 윤곽
    for t in range(0, 26):
        x, y = 1 + t, H - 27 + t
        s.px(x, y, G[7]); s.px(x + 1, y, G[5])
    for t in range(0, 26):
        x, y = 1 + t, H - 27 + t
        s.px(x - 1, y, G[0]); s.px(x + 2, y, G[0])
    s.px(0, H - 27, (0, 0, 0, 0))
    # 끈 매듭: 끈 중간에 2x3 혹
    s.rect(12, H - 17, 14, H - 14, G[7]); s.rect(12, H - 17, 14, H - 14, G[0], fill=False); s.px(13, H - 16, G[9])
    # 오른쪽 아래 페이지 귀 (들린 모서리): 작은 삼각 G14 + 그늘 G11
    for k in range(5):
        s.rect(RX1 - k, PY1 - 4 + k, RX1, PY1 - 4 + k, G[11])
    for k in range(4):
        s.rect(RX1 - 4 + k, PY1 - 4 + k, RX1 - 4 + k, PY1, G[14])
    # 표지 얼룩 (G02) 좌상단
    s.rect(10, 92, 20, 93, G[2]); s.rect(12, 91, 17, 91, G[2])
    return s


def diary_closed():
    W, H = 96, 64
    s = new(W, H)
    s.rect(1, 1, W - 2, H - 2, G[3])
    s.rect(1, 1, W - 2, H - 2, G[0], fill=False)
    s.rect(2, 2, W - 3, 2, G[5]); s.rect(2, 2, 2, H - 3, G[5])
    s.rect(2, 2, 9, H - 3, G[1])                                   # 책등
    s.rect(10, 2, 10, H - 3, G[0])
    # 종이 단면 (오른쪽 4열 G13/G12 번갈아, 아래 2줄)
    for i, c in enumerate([G[12], G[13], G[12], G[13]]):
        s.rect(W - 6 + i, 4, W - 6 + i, H - 5, c)
    s.rect(12, H - 4, W - 3, H - 4, G[12]); s.rect(12, H - 3, W - 3, H - 3, G[11])
    # 가죽 끈 가로 (G07/G05) + 매듭
    s.rect(2, 38, W - 7, 40, G[7]); s.rect(2, 40, W - 7, 40, G[5])
    s.rect(2, 37, W - 7, 37, G[0]); s.rect(2, 41, W - 7, 41, G[0])
    s.rect(60, 35, 66, 43, G[7]); s.rect(60, 35, 66, 43, G[0], fill=False); s.rect(62, 37, 64, 41, G[5])
    # 호박 밀랍 봉인 (오른쪽 위, r=5): 21 base + 20 그늘 + 23 하이라이트 + 안 문양 19
    cx, cy = 76, 20
    s.circle(cx, cy, 5, A[4], fill=True)
    s.circle(cx - 1, cy - 1, 4, A[5], fill=True, only="opaque")
    s.rect(cx - 2, cy - 2, cx - 1, cy - 2, A[7]); s.px(cx - 3, cy - 1, A[7])
    s.rect(cx - 1, cy, cx + 1, cy, A[3]); s.rect(cx, cy - 1, cx, cy + 1, A[3])
    s.circle(cx, cy, 6, G[0], fill=False)
    # 표지 긁힘·얼룩 (G02·G04 군집)
    s.rect(20, 12, 34, 13, G[2]); s.rect(24, 14, 30, 14, G[2])
    s.rect(30, 50, 31, 56, G[4]); s.rect(32, 52, 32, 58, G[4])
    s.rect(14, 20, 15, 21, G[4])
    return s


def stamp(kind):
    """48x48 잉크 도장: 이중 고리 + 문양. 눌린 자국처럼 군데군데 빠짐 (seed 고정)."""
    import random
    S = 48
    s = new(S, S)
    c = 23
    s.circle(c, c, 22, G[1], fill=False); s.circle(c, c, 21, G[1], fill=False)
    s.circle(c, c, 18, G[1], fill=False)
    if kind == "dead":
        # 큰 X (3px 두께) + 아래로 흐른 잉크
        for o in (-1, 0, 1):
            s.line(13 + o, 13, 33 + o, 33, G[1]); s.line(33 + o, 13, 13 + o, 33, G[1])
        s.rect(23, 34, 24, 40, G[1]); s.px(23, 41, G[1]); s.px(23, 42, G[1])
    else:
        # 오르는 계단: 4단 채운 실루엣 (디딤 5, 챌판 5), 바닥선 포함
        x0, y1 = 12, 35
        for k in range(4):
            s.rect(x0 + k * 5, y1 - (k + 1) * 5 + 1, x0 + 23, y1, G[1])
        s.rect(x0 - 2, y1 + 1, x0 + 25, y1 + 2, G[1])
    # 눌림 불균일: 고리·문양 안에서 12% 를 G03(옅음), 7% 를 빼냄
    rnd = random.Random(3 if kind == "dead" else 4)
    img = s.composite(1)
    for y in range(S):
        for x in range(S):
            if img.getpixel((x, y))[3]:
                r = rnd.random()
                if r < 0.07:
                    s.px(x, y, (0, 0, 0, 0))
                elif r < 0.19:
                    s.px(x, y, G[3])
    s.despeckle(min_cluster=2)
    return s


# ============================================================ 미리보기
FONT_PATH = "/usr/share/fonts/opentype/unifont/unifont.otf"


def font(size=16):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def text(img, xy, s, color=G[14], size=16, anchor="la", shadow=None):
    d = ImageDraw.Draw(img)
    f = font(size)
    if shadow:
        d.text((xy[0] + 1, xy[1] + 1), s, fill=rgba(shadow), font=f, anchor=anchor)
    d.text(xy, s, fill=rgba(color), font=f, anchor=anchor)


def up(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def preview_kit(assets, icons, sheet):
    """모든 키트 2배 + 9-slice 늘림 검증 (종이 240x120, 잉크 200x60, 미니맵 110x90, 게이지 120·200)."""
    W, H = 1180, 820
    img = Image.new("RGBA", (W, H), rgba(G[6]))
    y = 10

    def put(name, im, x, y, k=2):
        img.alpha_composite(up(im, k), (x, y))
        text(img, (x, y + im.height * k + 2), name, G[13], 16)
        return im.height * k + 22

    # 1행: 패널 원본 + 늘림
    put("panel_paper 80x80", assets["panel_paper"], 10, y)
    paper_big = nine(assets["panel_paper"], PAPER_SL, 240, 120)
    tile_fill(paper_big, assets["paper_tile"], PAPER_INNER["left"], PAPER_INNER["top"],
              240 - PAPER_INNER["left"] - PAPER_INNER["right"], 120 - PAPER_INNER["top"] - PAPER_INNER["bottom"])
    put("panel_paper 9-slice 240x120 + paper_tile", paper_big, 190, y)
    put("paper_tile 32", assets["paper_tile"], 690, y)
    ink_big = nine(assets["panel_ink"], INK_SL, 200, 60)
    put("panel_ink 48", assets["panel_ink"], 780, y)
    put("panel_ink 9-slice 200x60", ink_big, 900, y)
    y += 270
    # 2행: 게이지
    x = 10
    for nm in ["gauge_frame", "gauge_boss"]:
        x += put(nm, assets[nm], x, y) * 0 + assets[nm].width * 2 + 30
    gf = nine(assets["gauge_frame"], GAUGE_SL, 120, 10)
    fill = assets["gauge_fill"].resize((int((120 - 4) * 0.7), 8), Image.NEAREST)
    gf.alpha_composite(fill, (2, 1))
    put("gauge_frame 120 + fill 70%", gf, x, y); x += 270
    gb = nine(assets["gauge_boss"], BOSS_SL, 200, 14)
    fill = assets["gauge_fill"].resize((int((200 - 10) * 0.45), 8), Image.NEAREST)
    gb.alpha_composite(fill, (5, 3))
    put("gauge_boss 200 + fill 45%", gb, x, y); x += 430
    gg = nine(assets["gauge_frame"], GAUGE_SL, 120, 10)
    fill = assets["gauge_fill_gray"].resize((int((120 - 4) * 0.5), 8), Image.NEAREST)
    gg.alpha_composite(fill, (2, 1))
    put("gauge_fill_gray 50% (tint용)", gg, x, y)
    put("fill 1x8", up(assets["gauge_fill"], 4), 10, y + 50, 2)
    put("fill_gray", up(assets["gauge_fill_gray"], 4), 110, y + 50, 2)
    # 미니맵 틀
    mm = nine(assets["minimap_frame"], MINI_SL, 110, 90)
    put("minimap_frame 32 → 110x90", mm, 240, y + 44)
    # 커서·구분선
    cx = 500
    put("cursor f1/f2 (ink)", Image.open(os.path.join(OUT, "cursor.png")), cx, y + 44, 4)
    put("cursor_light", Image.open(os.path.join(OUT, "cursor_light.png")), cx + 90, y + 44, 4)
    r = assets["rule"].resize((120, 4), Image.NEAREST)
    put("rule 1x4 → 120", r, cx + 180, y + 44, 2)
    r2 = assets["rule_light"].resize((120, 4), Image.NEAREST)
    put("rule_light", r2, cx + 180, y + 80, 2)
    y += 140
    # 3행: 아이콘 시트 (4배) 종이 위 / 잉크 위
    paper_bg = nine(assets["panel_paper"], PAPER_SL, 8 + sheet.width * 4 + 8, 8 + sheet.height * 4 + 8)
    paper_bg.alpha_composite(up(sheet, 4), (8, 8))
    put("icons.png 4x on paper", paper_bg, 10, y, 1)
    ink_bg = nine(assets["panel_ink"], INK_SL, 8 + sheet.width * 4 + 8, 8 + sheet.height * 4 + 8)
    ink_bg.alpha_composite(up(sheet, 4), (8, 8))
    put("icons.png 4x on ink", ink_bg, 560, y, 1)
    y += 170
    # 4행: 일기장·도장
    put("title_diary 160x96", assets["title_diary"], 10, y)
    put("diary_closed 96x64", assets["diary_closed"], 350, y)
    pap = nine(assets["panel_paper"], PAPER_SL, 240, 130)
    pap.alpha_composite(up(assets["stamp_dead"], 2), (16, 16))
    pap.alpha_composite(up(assets["stamp_clear"], 2), (124, 16))
    put("stamp_dead / stamp_clear 48 (on paper)", pap, 560, y, 1)
    img.convert("RGB").save(os.path.join(HERE, "preview_kit.png"))
    print("preview -> preview_kit.png")


def preview_icons(icons):
    names = [n for n in ICON_ORDER]
    k = 8
    cell = 16 * k + 8
    img = Image.new("RGBA", (len(names) * cell + 8, cell * 2 + 44), rgba(G[6]))
    for row, bgc in enumerate([G[13], G[1]]):
        for i, n in enumerate(names):
            x, y = 8 + i * cell, 8 + row * cell
            ImageDraw.Draw(img).rectangle([x - 4, y - 4, x + 16 * k + 3, y + 16 * k + 3], fill=rgba(bgc))
            im = icons[n].composite(1)
            off = 4 * k if im.width == 8 else 0
            img.alpha_composite(up(im, k), (x + off, y + off))
    for i, n in enumerate(names):
        text(img, (8 + i * cell, cell * 2 + 14), n.replace("icon_", "").replace("mini_", "m:"), G[14], 16)
    img.convert("RGB").save(os.path.join(HERE, "preview_icons.png"))


def preview_mock(assets, sheet, icon_frames):
    """960x540: 1층 타일 배경 + 가장자리 HUD + 중앙 종이 메뉴."""
    import random
    W, H = 960, 540
    T = 16
    tiles = Image.open(os.path.join(ROOT, "assets", "tiles", "stage1.png")).convert("RGBA")

    def tile(i):
        r, c = divmod(i, 8)
        return tiles.crop((c * T, r * T, c * T + T, r * T + T))

    img = Image.new("RGBA", (W, H), rgba(G[0]))
    rnd = random.Random(2)
    cols, rows = W // T, H // T + 1
    for ty in range(rows):
        for tx in range(cols):
            if ty == 1:
                t = tile(5)
            elif ty == 0 or tx == 0 or tx == cols - 1:
                t = tile(6)
            else:
                t = tile(rnd.randrange(4))
            img.alpha_composite(t, (tx * T, ty * T))
    for (tx, ty, i) in [(6, 5, 13), (7, 5, 13), (40, 20, 16), (14, 24, 16), (30, 12, 15), (50, 9, 14), (22, 28, 14)]:
        img.alpha_composite(tile(i), (tx * T, ty * T))
    # 주인공·적 (idle down 1프레임)
    def sprite(path, fw, fh, col=0):
        im = Image.open(path).convert("RGBA")
        return im.crop((col * fw, 0, col * fw + fw, fh))
    d = ImageDraw.Draw(img)
    for (path, fw, fh, x, y) in [
        (os.path.join(ROOT, "assets", "sprites", "player", "player_idle.png"), 16, 24, 300, 250),
        (os.path.join(ROOT, "assets", "sprites", "enemies", "dummy_idle.png"), 16, 24, 520, 200),
        (os.path.join(ROOT, "assets", "sprites", "enemies", "archer_idle.png"), 16, 24, 640, 330),
        (os.path.join(ROOT, "assets", "sprites", "enemies", "charger_idle.png"), 24, 24, 420, 380),
    ]:
        d.ellipse([x + 3, y + fh - 3, x + fw - 4, y + fh], fill=rgba(G[1]))
        img.alpha_composite(sprite(path, fw, fh), (x, y))

    def icon(name, x, y):
        f = icon_frames[name]
        img.alpha_composite(sheet.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])), (x, y))

    def gauge(x, y, w, ratio, boss=False, gray=False):
        fr = nine(assets["gauge_boss" if boss else "gauge_frame"], BOSS_SL if boss else GAUGE_SL, w, 14 if boss else 10)
        ins = BOSS_INSET if boss else GAUGE_INSET
        inner = w - ins["left"] - ins["right"]
        fw = max(0, int(inner * ratio))
        if fw:
            fr.alpha_composite((assets["gauge_fill_gray"] if gray else assets["gauge_fill"]).resize((fw, 8), Image.NEAREST),
                               (ins["left"], ins["top"]))
        img.alpha_composite(fr, (x, y))

    P = 8
    # 좌상단: 체력·전표·독주
    pw, ph = 236, 62
    img.alpha_composite(nine(assets["panel_ink"], INK_SL, pw, ph), (P, P))
    icon("icon_hp", P + 8, P + 8)
    gauge(P + 28, P + 11, 196, 0.72)
    text(img, (P + 30, P + 24), "72 / 100", G[13], 16)
    icon("icon_gold", P + 8, P + 40)
    text(img, (P + 28, P + 40), "137 전표", G[13], 16)
    icon("icon_potion", P + 120, P + 40)
    text(img, (P + 140, P + 40), "잔의 독주 2/3  Q", G[13], 16)
    # 상단 중앙: 층 제목 (패널 없이 그림자 글씨) + 시련
    text(img, (W // 2, P + 2), "1층 · 술독 제국 '잔'   시련 2/4", G[11], 16, anchor="ma", shadow=G[0])
    # 우상단: 미니맵 + 음소거
    mw, mh = 118, 98
    img.alpha_composite(nine(assets["minimap_frame"], MINI_SL, mw, mh), (W - P - mw, P))
    cell = 14
    ox, oy = W - P - mw + 10, P + 10
    rooms = [((0, 1), "mini_start", True), ((1, 1), "mini_trial", True), ((2, 1), "mini_trial", False),
             ((1, 0), "mini_rest", False), ((2, 2), "mini_boss", False), ((3, 1), "mini_trial", True)]
    d = ImageDraw.Draw(img)
    for (ax, ay), (bx, by) in [((0, 1), (1, 1)), ((1, 1), (2, 1)), ((1, 1), (1, 0)), ((2, 1), (2, 2)), ((2, 1), (3, 1))]:
        d.line([ox + ax * cell * 2 + cell // 2 + 7, oy + ay * cell * 2 + cell // 2 + 7,
                ox + bx * cell * 2 + cell // 2 + 7, oy + by * cell * 2 + cell // 2 + 7], fill=rgba(G[4]), width=2)
    for (cx, cy), nm, cleared in rooms:
        x, y = ox + cx * cell * 2 + 3, oy + cy * cell * 2 + 3
        d.rectangle([x, y, x + 21, y + 21], fill=rgba(G[3] if cleared else G[2]))
        icon(nm, x + 7, y + 7)
    x, y = ox + 1 * cell * 2 + 3, oy + 1 * cell * 2 + 3
    d.rectangle([x - 1, y - 1, x + 22, y + 22], outline=rgba(A[7]))
    icon("icon_sound", W - P - 16 - 44, P + mh + 6)
    text(img, (W - P - 44 + 2, P + mh + 6), "M", G[11], 16)
    # 좌하단: 무기 + 개성 게이지
    ww, wh = 330, 52
    img.alpha_composite(nine(assets["panel_ink"], INK_SL, ww, wh), (P, H - P - wh))
    wi = Image.open(os.path.join(ROOT, "assets", "sprites", "weapons", "katana_icon.png")).convert("RGBA")
    img.alpha_composite(wi, (P + 8, H - P - wh + 8))
    text(img, (P + 30, H - P - wh + 7), "사무라이 칼 · 거합   우클릭 패링", G[13], 16)
    icon("icon_sense", P + 8, H - P - 22)
    gauge(P + 30, H - P - 21, 160, 0.4, gray=True)
    text(img, (P + 196, H - P - 24), "개성 40/100", G[11], 16)
    # 하단 중앙: 보스 게이지
    bw = 360
    bx, by = W // 2 - bw // 2, H - P - 26
    icon("icon_boss", bx - 22, by - 2)
    text(img, (W // 2, by - 20), "양조장주  페이즈 1", A[8], 16, anchor="ma", shadow=G[0])
    gauge(bx, by, bw, 0.63, boss=True)
    # 우하단: 출구 열림 공지 (작은 잉크 패널)
    nw, nh = 150, 30
    img.alpha_composite(nine(assets["panel_ink"], INK_SL, nw, nh), (W - P - nw, H - P - nh))
    icon("icon_exit", W - P - nw + 8, H - P - nh + 7)
    text(img, (W - P - nw + 30, H - P - nh + 6), "오르는 길 열림", A[7], 16)
    # 중앙: 종이 메뉴 (일시정지 '일기장')
    pw, ph = 420, 236
    px0, py0 = W // 2 - pw // 2, H // 2 - ph // 2 - 6
    paper = nine(assets["panel_paper"], PAPER_SL, pw, ph)
    tile_fill(paper, assets["paper_tile"], PAPER_INNER["left"], PAPER_INNER["top"],
              pw - PAPER_INNER["left"] - PAPER_INNER["right"], ph - PAPER_INNER["top"] - PAPER_INNER["bottom"])
    img.alpha_composite(paper, (px0, py0))
    text(img, (W // 2, py0 + 18), "일기장", G[1], 16, anchor="ma")
    img.alpha_composite(assets["rule"].resize((pw - 60, 4), Image.NEAREST), (px0 + 30, py0 + 40))
    text(img, (px0 + 30, py0 + 50), "전장의 망령   1층 · 술독 제국 '잔'   시련 2/4", G[3], 16)
    text(img, (px0 + 30, py0 + 70), "공격 7  방어 3  치명타 5%  감각 2", G[3], 16)
    text(img, (px0 + 30, py0 + 90), "무기: 사무라이 칼 · 거합  (개성 40/100)", G[3], 16)
    icon("icon_save", px0 + 30, py0 + 110)
    text(img, (px0 + 52, py0 + 110), "세이브 남음 2", G[3], 16)
    img.alpha_composite(assets["rule"].resize((pw - 60, 4), Image.NEAREST), (px0 + 30, py0 + 136))
    cur = Image.open(os.path.join(OUT, "cursor.png")).crop((0, 0, 8, 8))
    img.alpha_composite(cur, (px0 + 32, py0 + 154))
    text(img, (px0 + 48, py0 + 150), "[1] 더 쓴다 (Esc)", G[0], 16)
    text(img, (px0 + 48, py0 + 172), "[2] 그래도 덮는다", G[3], 16)
    img.alpha_composite(assets["stamp_clear"], (px0 + pw - 86, py0 + ph - 86))
    img.convert("RGB").save(os.path.join(HERE, "preview_mock.png"))
    print("preview -> preview_mock.png")


# ============================================================ main
def main():
    assets = {}

    pp = panel_paper()
    assets["panel_paper"] = check("panel_paper", pp)
    export("panel_paper", pp, {"kind": "nineslice", "width": 80, "height": 80, "slice": PAPER_SL,
                                "inner": PAPER_INNER, "tile": "paper_tile.png (draw as tileSprite inside `inner` on top of the stretched center)",
                                "colors": "paper G12-G14, ink G00/G01, inner faint rule G09"})
    pt = paper_tile()
    assets["paper_tile"] = check("paper_tile", pt)
    export("paper_tile", pt, {"kind": "tile", "width": 32, "height": 32, "seamless": True})

    pi = panel_ink()
    assets["panel_ink"] = check("panel_ink", pi, allow_semi=1)
    export("panel_ink", pi, {"kind": "nineslice", "width": 48, "height": 48, "slice": INK_SL, "inner": INK_INNER,
                              "centerAlpha": round(INK_ALPHA / 255, 2), "colors": "rim G02 (top/left), G00 (bottom/right), fill G01 @ 0.85"})
    mf = minimap_frame()
    assets["minimap_frame"] = check("minimap_frame", mf)
    export("minimap_frame", mf, {"kind": "nineslice", "width": 32, "height": 32, "slice": MINI_SL,
                                  "inner": {"left": 4, "right": 4, "top": 4, "bottom": 4}, "colors": "G00/G01/G03 + G05 corner marks"})

    gf = gauge_frame()
    assets["gauge_frame"] = check("gauge_frame", gf)
    export("gauge_frame", gf, {"kind": "nineslice", "width": 24, "height": 10, "slice": GAUGE_SL, "fillInset": GAUGE_INSET,
                                "fill": "gauge_fill.png stretched to (w - 4) * ratio, placed at (2, 1)"})
    gb = gauge_boss()
    assets["gauge_boss"] = check("gauge_boss", gb)
    export("gauge_boss", gb, {"kind": "nineslice", "width": 32, "height": 14, "slice": BOSS_SL, "fillInset": BOSS_INSET,
                               "fill": "gauge_fill.png stretched to (w - 10) * ratio, placed at (5, 3)"})
    fl = gauge_fill()
    assets["gauge_fill"] = check("gauge_fill", fl)
    export("gauge_fill", fl, {"kind": "strip", "width": 1, "height": 8, "rows": "23 light1, 22, 21 base x3, 20 x2, 19 shadow1",
                               "usage": "stretch horizontally (NEAREST). Floor-1 amber; system/UI swaps to current floor ramp"})
    fg = gauge_fill_gray()
    assets["gauge_fill_gray"] = check("gauge_fill_gray", fg)
    export("gauge_fill_gray", fg, {"kind": "strip", "width": 1, "height": 8, "rows": "G15, G14, G13 x3, G11 x2, G10",
                                    "usage": "luminance strip for multiplicative tint (setTint with ramp 'light1' ≈ amber fill) or as-is for gray gauges (personality)"})

    icons, sheet = build_icons()
    with open(os.path.join(OUT, "icons.json"), encoding="utf-8") as fp:
        icon_frames = json.load(fp)["frames"]

    cu = cursor(True)
    check("cursor", cu, allow_iso=1)
    export("cursor", cu, {"kind": "strip", "frameWidth": 8, "frameHeight": 8, "frames": 2, "frameDurationsMs": [420, 260],
                           "loop": True, "pivot": {"x": 4, "y": 4}, "colors": "ink G01, slit G00, drop 21 (frame 2)"})
    cl = cursor(False)
    check("cursor_light", cl, allow_iso=1)
    export("cursor_light", cl, {"kind": "strip", "frameWidth": 8, "frameHeight": 8, "frames": 2, "frameDurationsMs": [420, 260],
                                 "loop": True, "pivot": {"x": 4, "y": 4}, "colors": "G14/G12, drop 21 — for ink panels"})
    ru = rule(True)
    assets["rule"] = check("rule", ru)
    export("rule", ru, {"kind": "tile", "width": 1, "height": 4, "usage": "stretch/tile horizontally; row1 ink G00, row2 bleed G10"})
    rl = rule(False)
    assets["rule_light"] = check("rule_light", rl)
    export("rule_light", rl, {"kind": "tile", "width": 1, "height": 4, "usage": "for ink panels; row1 G09, row2 G03"})

    td = title_diary()
    assets["title_diary"] = check("title_diary", td)
    export("title_diary", td, {"kind": "image", "width": 160, "height": 96, "pivot": {"x": 80, "y": 48},
                                "accent": "bookmark ribbon 20/21, wine-cup ring 19/20 (runtime swap ok)"})
    dc = diary_closed()
    assets["diary_closed"] = check("diary_closed", dc)
    export("diary_closed", dc, {"kind": "image", "width": 96, "height": 64, "pivot": {"x": 48, "y": 32},
                                 "accent": "wax seal 19/20/21/23"})
    for kind in ["dead", "clear"]:
        st = stamp(kind)
        assets["stamp_" + kind] = check("stamp_" + kind, st)
        export("stamp_" + kind, st, {"kind": "image", "width": 48, "height": 48, "pivot": {"x": 24, "y": 24},
                                     "colors": "ink G01 + worn G03 (grayscale; UI may set alpha 0.8-0.9)"})

    preview_icons(icons)
    preview_kit(assets, icons, sheet)
    preview_mock(assets, sheet, icon_frames)

    print("\n%-16s %-8s gray acc other iso semi" % ("asset", "size"))
    for r in REPORT:
        print("%-16s %-8s %4d %3d %5d %3d %4d" % r)


if __name__ == "__main__":
    main()
