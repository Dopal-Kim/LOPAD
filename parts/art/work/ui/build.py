#!/usr/bin/env python3
"""LOPAD UI 키트 빌드 (32라운드 전폭 재설계 + 33라운드 낡은 용지·칙칙한 톤 재작업) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/ui/build.py
입력: parts/art/palette/lopad.json, assets/tiles/stage1.png, assets/sprites/{player,enemies,weapons}/* (목업용)
산출: assets/sprites/ui/*.png + *.json  (UI 파트가 assets/ui/ 로 복사해 쓴다)
      parts/art/work/ui/preview_kit.png   키트 전체 2배 + 9-slice 늘림 검증
      parts/art/work/ui/preview_mock.png  960x540 HUD·메뉴 목업 (1층 타일 배경)
      parts/art/work/ui/preview_icons.png 아이콘 8배 (종이·잉크 두 배경)

      parts/art/work/ui/preview_mock_result.png 결과 화면 목업 (종이 전면 + 닫힌 일기장 + 도장)

색 규칙 (33라운드 검수 반영: "A4 가 아니라 낡은 용지, 암울하고 칙칙한 색")
  - 무채 G00~G15 만 기본. 유채는 1층 호박 램프(인덱스 16~27)로 그리고 시스템/UI 가 층 램프로 스왑·틴트.
  - 종이 = G09 바탕 / G10 덜 바랜 자리 / G08 얼룩·섬유 / G07 접힌 자국·해진 가장자리 / 19(18) 누런 얼룩 점.
  - 잉크 = G00/G01, 번짐 = G03/G04(종이 위)·G06(옅은 선). 도장은 바랜 잉크 G02 (닳은 자리 G03/G04).
  - 잉크 패널 림 G01/G00, 꺾쇠 G02. 게이지 채움 상한 22.
  - 아이콘: 무채 ≤5 + 강조 ≤3, 바깥 K 윤곽 1px (16 캔버스 안에 1px 여백). 종이 요소는 G10, 옅은 선 G06.
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


PAPER = G[9]        # 낡은 용지 본색 (33라운드: G13 흰 A4 → G09 바랜 회색)
PAPER_LIGHT = G[10]  # 덜 바랜 자리
PAPER_DARK = G[8]    # 얼룩·그늘
PAPER_WORN = G[7]    # 접힌 자국·해진 가장자리
STAIN = A[3]         # 누렇게 바랜 얼룩 점 (1층 shadow1 19, G08 과 섞어 저채도로)


def blob(s, cx, cy, rx, ry, color, seed, density=0.85, stain=0.0):
    """불규칙한 얼룩: 타원 안을 density 확률로 color, stain 확률로 STAIN 점. 가장자리는 듬성듬성."""
    import random
    rnd = random.Random(seed)
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if not (0 <= x < s.w and 0 <= y < s.h):
                continue
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d > 1.0:
                continue
            p = density if d < 0.55 else density * 0.45
            if rnd.random() < p:
                # 누런 점은 얼룩 한가운데(d<0.4)에만 — 바깥에 흩어지면 '주황 색종이'처럼 보인다
                s.px(x, y, STAIN if (stain and d < 0.4 and rnd.random() < stain) else color)


def _periodic_noise(S, cell, seed):
    """S x S 주기 값 노이즈 (cell px 격자에 난수, 코사인 보간, 타일 경계에서 이어짐). 0~1."""
    import math, random
    rnd = random.Random(seed)
    n = S // cell
    grid = [[rnd.random() for _ in range(n)] for _ in range(n)]
    out = [[0.0] * S for _ in range(S)]
    for y in range(S):
        gy, fy = divmod(y, cell)
        ty = (1 - math.cos(math.pi * fy / cell)) / 2
        for x in range(S):
            gx, fx = divmod(x, cell)
            tx = (1 - math.cos(math.pi * fx / cell)) / 2
            a, b = grid[gy % n][gx % n], grid[gy % n][(gx + 1) % n]
            c, d = grid[(gy + 1) % n][gx % n], grid[(gy + 1) % n][(gx + 1) % n]
            out[y][x] = (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty
    return out


def paper_tile():
    """64x64 타일링 낡은 종이 질감 (33라운드: 32→64, 반복 주기가 글 밑에서 격자로 보이던 문제).
    주기 값 노이즈(16px + 8px) 를 문턱으로 잘라 G10 덜 바랜 자리 / G08 그늘 얼룩덜룩 — 타원 무늬가 아니라
    불규칙한 얼룩. + G08 섬유 + 19 점 2~3px 군집 소량. 노이즈가 주기적이라 가장자리 처리 없이 이음새 없음."""
    S = 64
    s = new(S, S)
    s.rect(0, 0, S - 1, S - 1, PAPER)
    import random
    rnd = random.Random(7)
    n1, n2 = _periodic_noise(S, 16, 11), _periodic_noise(S, 8, 12)
    for y in range(S):
        for x in range(S):
            v = n1[y][x] * 0.7 + n2[y][x] * 0.3
            # 덩어리로 칠하지 않고 노이즈 값에 비례한 확률로 점을 찍는다 → 성긴 스티플(얼룩덜룩), 반복이 덜 보임
            p_light = min(0.6, max(0.0, (v - 0.58) / 0.28))
            p_dark = min(0.6, max(0.0, (0.40 - v) / 0.28))
            r = rnd.random()
            if r < p_light:
                s.px(x, y, PAPER_LIGHT)
            elif r < p_dark:
                s.px(x, y, PAPER_DARK)
    # 섬유 (G08 2~3px, 가로·세로 섞음) — 타일 경계는 넘지 않음
    for _ in range(22):
        x, y = rnd.randrange(1, S - 4), rnd.randrange(1, S - 4)
        n = rnd.choice([2, 2, 3])
        if rnd.random() < 0.35:
            s.rect(x, y, x, y + n - 1, PAPER_DARK)
        else:
            s.rect(x, y, x + n - 1, y, PAPER_DARK)
    # 누런 점: 19 를 2~3px 군집으로, G08 에 감싸서 (단독 1px 유채는 노이즈로 보여 금지)
    # 타일당 2개만 (4개면 1배 화면에서 64px 격자로 줄지어 보인다), 하나는 더 어두운 18
    for (x, y, c) in [(20, 24, STAIN), (51, 47, A[2])]:
        s.rect(x - 1, y - 1, x + 2, y + 1, PAPER_DARK)
        s.px(x, y, c); s.px(x + 1, y, c); s.px(x, y + 1, c)
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


def _is(s, x, y, color):
    c = s.get(x, y)
    return bool(c) and c[3] and tuple(c[:3]) == rgb(color)


def panel_paper():
    """80x80 낡은 용지 (33라운드). 바탕 G09, 해진 가장자리(G08/G07 + 코너 결손 알파 0), 얼룩(G08 + 19 점),
    좌상단 접힌 자국(사선 G07/G10, 잉크선이 닳음), 우하단 접힌 귀(dog-ear). 잉크 번짐 테두리는 유지.
    늘어나는 가운데 띠(24~56)에는 결손·얼룩을 두지 않는다 (늘리면 줄무늬가 된다)."""
    size = 80
    s = new(size, size)
    s.rect(0, 0, size - 1, size - 1, PAPER)
    # 얼룩 — 잉크선 아래 깔림. 코너 영역(12px 띠 안쪽은 paper_tile 이 덮는다)만
    blob(s, 69, 6, 9, 4, PAPER_DARK, seed=31, density=0.8, stain=0.3)     # 우상단 누런 얼룩
    blob(s, 6, 64, 4, 8, PAPER_DARK, seed=32, density=0.75, stain=0.25)   # 좌하단 세로 얼룩
    blob(s, 16, 5, 6, 3, PAPER_LIGHT, seed=33, density=0.5)               # 좌상단 덜 바랜 자리
    blob(s, 72, 70, 5, 4, PAPER_DARK, seed=34, density=0.7)               # 우하단 (귀 아래 그늘)
    # 해진 가장자리: 위·왼쪽 바깥 1줄 G08, 아래·오른쪽 바깥 1줄 G07 + 안쪽 1줄 G08
    s.rect(0, 0, size - 1, 0, PAPER_DARK); s.rect(0, 0, 0, size - 1, PAPER_DARK)
    s.rect(0, size - 1, size - 1, size - 1, PAPER_WORN); s.rect(size - 1, 0, size - 1, size - 1, PAPER_WORN)
    s.rect(1, size - 2, size - 1, size - 2, PAPER_DARK); s.rect(size - 2, 1, size - 2, size - 1, PAPER_DARK)
    # 가장자리 그을림: 잉크선 바깥 띠(inset 1~2) 를 G08 로 어둡게 — 오래 만져 때 탄 가장자리
    s.rect(1, 1, size - 2, 2, PAPER_DARK); s.rect(1, 1, 2, size - 2, PAPER_DARK)
    s.rect(1, size - 3, size - 2, size - 2, PAPER_DARK); s.rect(size - 3, 1, size - 2, size - 2, PAPER_DARK)
    # 바깥 잉크 선: 번짐(G03) 을 안쪽에 먼저 깔고 그 위에 잉크(G01) — 2px 무게, 팔각 모따기 7
    octagon(s, 4, 6, G[3], size)
    octagon(s, 3, 7, G[1], size)
    # 안쪽 가는 선 (G06) 평행 팔각 — 바랜 종이 위라 G09 로는 안 보여 G06
    octagon(s, 8, 7, G[6], size)
    # 코너 잉크 닳음: 코너 24 안의 잉크선 픽셀 일부를 G03/G04 로 (늘어나는 띠는 건드리지 않음)
    import random
    rnd = random.Random(35)
    for y in range(size):
        for x in range(size):
            corner = (x < 24 or x >= size - 24) and (y < 24 or y >= size - 24)
            if corner and _is(s, x, y, G[1]) and rnd.random() < 0.12:
                s.px(x, y, G[3] if rnd.random() < 0.6 else G[4])
    # 좌상단 접힌 자국: 사선 x+y=18 (G07, 잉크선 위는 닳아서 G03/G06), x+y=19 빛 받은 능선 G10
    for x in range(0, 19):
        y = 18 - x
        if _is(s, x, y, G[1]):
            s.px(x, y, G[3])
        elif _is(s, x, y, G[3]):
            s.px(x, y, G[6])
        else:
            s.px(x, y, PAPER_WORN)
        y2 = 19 - x
        if _is(s, x, y2, PAPER) or _is(s, x, y2, PAPER_DARK) or _is(s, x, y2, PAPER_LIGHT):
            s.px(x, y2, PAPER_LIGHT)
    # 우하단 접힌 귀: u+v<=7 결손(알파 0), 8~15 뒷면 플랩(G08, 바깥 가장자리 G07, 접힌 능선 G07 + G10)
    for y in range(size - 18, size):
        for x in range(size - 18, size):
            u, v = size - 1 - x, size - 1 - y
            t = u + v
            if t <= 7:
                s.px(x, y, (0, 0, 0, 0))
            elif t == 8:
                s.px(x, y, PAPER_WORN)
            elif t <= 14:
                s.px(x, y, PAPER_DARK)
            elif t == 15:
                s.px(x, y, PAPER_WORN)
            elif t == 16:
                s.px(x, y, PAPER_LIGHT)
    # 찢긴 가장자리: 코너 24 영역의 바깥 1~2px 결손 (잉크선 inset 3 은 건드리지 않음)
    bites = [
        (0, 0), (1, 0), (0, 1), (0, 2),                                   # 좌상단 모서리 뭉개짐
        (79, 0), (78, 0), (77, 0), (79, 1), (78, 1), (79, 2), (79, 3), (76, 0),   # 우상단 찢김
        (66, 0), (67, 0), (70, 0), (79, 12), (79, 13), (79, 20), (78, 20),
        (0, 79), (1, 79), (2, 79), (0, 78), (1, 78), (0, 77), (0, 76), (3, 79),   # 좌하단 찢김
        (0, 60), (0, 61), (1, 61), (0, 70), (12, 79), (13, 79), (19, 79),
        (0, 20), (0, 21), (8, 0), (9, 0),                                 # 좌상단 가장자리 작은 결손
        (79, 60), (79, 61), (62, 79), (63, 79), (64, 79),                 # 우하단 귀 바깥쪽 작은 결손
    ]
    for (x, y) in bites:
        s.px(x, y, (0, 0, 0, 0))
    # 결손 옆 종이는 G07 로 해져 보이게 (알파 0 과 닿은 종이색 픽셀)
    for y in range(size):
        for x in range(size):
            if (x < 24 or x >= size - 24) and (y < 24 or y >= size - 24):
                c = s.get(x, y)
                if c and c[3] and tuple(c[:3]) in (rgb(PAPER), rgb(PAPER_DARK), rgb(PAPER_LIGHT)):
                    if any(0 <= x + dx < size and 0 <= y + dy < size and s.get(x + dx, y + dy) is None
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        s.px(x, y, PAPER_WORN)
    return s


INK_SL = {"left": 12, "right": 12, "top": 12, "bottom": 12}
INK_INNER = {"left": 5, "right": 5, "top": 5, "bottom": 5}
INK_ALPHA = 218  # 가운데 G01 반투명 (약 85%)


def panel_ink():
    size = 48
    s = new(size, size)
    s.rect(0, 0, size - 1, size - 1, rgba(G[1], INK_ALPHA))
    # 바깥 테 (33라운드 더 탁하게): 위·왼쪽 G01 림, 아래·오른쪽 G00. 모두 불투명. 코너 1px 모따기(투명)
    s.rect(0, 0, size - 1, 0, G[1]); s.rect(0, 0, 0, size - 1, G[1])
    s.rect(0, size - 1, size - 1, size - 1, G[0]); s.rect(size - 1, 0, size - 1, size - 1, G[0])
    for (x, y) in [(0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)]:
        s.px(x, y, (0, 0, 0, 0))
    # 안쪽 1px 어두운 잉크선 (G00) — 림 바로 안
    s.rect(1, 1, size - 2, size - 2, G[0], fill=False)
    # 코너 안쪽 꺾쇠 (G02, 길이 4): 종이 패널의 꺾쇠와 짝
    for (x, y, dx, dy) in [(3, 3, 1, 1), (size - 4, 3, -1, 1), (3, size - 4, 1, -1), (size - 4, size - 4, -1, -1)]:
        for i in range(4):
            s.px(x + dx * i, y, G[2]); s.px(x, y + dy * i, G[2])
    return s


MINI_SL = {"left": 10, "right": 10, "top": 10, "bottom": 10}


def minimap_frame():
    size = 32
    s = new(size, size)
    s.rect(0, 0, size - 1, size - 1, G[1])
    s.rect(0, 0, size - 1, size - 1, G[0], fill=False)
    s.rect(1, 1, size - 2, size - 2, G[2], fill=False)   # 안쪽 선 (지도 종이 테두리 느낌) — 33라운드 G03→G02
    s.rect(2, 2, size - 3, size - 3, G[0], fill=False)
    # 좌상단 코너: 접힌 지도 귀 (G04 삼각 3px) / 우하단: 나침 눈금 (작은 십자 G04, 중심 G05)
    s.px(3, 3, G[4]); s.px(4, 3, G[4]); s.px(3, 4, G[4])
    cx, cy = size - 6, size - 6
    s.px(cx, cy - 1, G[4]); s.px(cx, cy + 1, G[4]); s.px(cx - 1, cy, G[4]); s.px(cx + 1, cy, G[4]); s.px(cx, cy, G[5])
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
    s.rect(1, 1, w - 2, h - 2, G[2], fill=False)         # 안쪽 선 (33라운드 G03→G02)
    s.rect(2, 2, w - 3, h - 3, G[1], fill=False)         # 어두운 선
    s.rect(3, 3, w - 4, h - 4, G[2])                     # 트랙
    for (x, y) in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        s.px(x, y, (0, 0, 0, 0))
    # 캡: 트랙 양 끝 2px 를 G03 로, 그 바깥에 세로 쐐기(G04) 장식
    s.rect(3, 3, 4, h - 4, G[3]); s.rect(w - 5, 3, w - 4, h - 4, G[3])
    for x0, dx in [(1, 1), (w - 2, -1)]:
        s.px(x0, 6, G[4]); s.px(x0, 7, G[4]); s.px(x0 + dx, 5, G[4]); s.px(x0 + dx, 8, G[4])
    s.rect(5, h - 4, w - 6, h - 4, G[0])                 # 트랙 바닥 그늘
    return s


def gauge_fill():
    """33라운드: 상한 23→22 (한 단 낮춤). 22 / 21 / 20x3 / 19x2 / 18."""
    s = new(1, 8)
    for y, c in enumerate([A[6], A[5], A[4], A[4], A[4], A[3], A[3], A[2]]):
        s.px(0, y, c)
    return s


def gauge_fill_gray():
    """무채 띠도 한 단 낮춤: G14 / G13 / G12x3 / G10x2 / G09 (틴트 곱 결과가 gauge_fill 과 비슷해지도록)."""
    s = new(1, 8)
    for y, c in enumerate([G[14], G[13], G[12], G[12], G[12], G[10], G[10], G[9]]):
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
# 33라운드 톤 다운: 문자 지도는 흰 종이 기준으로 그려 두고 블릿 직전에 치환한다.
#   종이 d(G13)→a(G10), 옅은 선 9(G09)→6(G06), 단면 c(G12)→8(G08), 하이라이트 w(G15)→d(G13),
#   미니맵 글리프 e(G14)→c(G12), 강조 하이라이트 L(23)→M(22)
ICON_REMAP = str.maketrans("d9cweL", "a68dcM")


def icon_hp():
    """붕대 두 가닥 X + 피 얼룩. 코드로 띠를 만든다 (사선 띠 폭 4)."""
    s = new(16, 16)
    for y in range(1, 15):
        for x in range(1, 15):
            a = abs(x - y) <= 2
            b = abs(x + y - 15) <= 2
            if a or b:
                s.px(x, y, G[10])
    # 띠 아래쪽 가장자리 그늘 (빛 좌상단): 각 띠의 오른쪽/아래 경계 1줄
    for y in range(1, 15):
        for x in range(1, 15):
            if s.get(x, y) and (x - y == 2 or x + y - 15 == 2):
                s.px(x, y, G[6])
    # 거즈 패드: 띠 양 끝 2x2 G08 군집 (반창고의 패드)
    for (x, y) in [(2, 2), (12, 2), (2, 12), (12, 12)]:
        s.rect(x, y, x + 1, y + 1, G[8])
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
            blit(s, [r.translate(ICON_REMAP) for r in MINI[name]])
            canv[name] = s
            check(name, s)
            continue
        else:
            s = new(16, 16)
            blit(s, [r.translate(ICON_REMAP) for r in ICONS[name]])
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
            "mini_*": "8x8 single-color G12 room glyphs for minimap (dark map only): start/trial/rest/boss"},
    })
    return canv, sheet


# ============================================================ 4. 커서·구분선
def cursor(dark=True):
    """깃펜 촉 ▶ 2프레임: 0 = 정지, 1 = 1px 앞으로 + 촉 끝 잉크 방울."""
    ink, slit = (G[1], G[7]) if dark else (G[12], G[8])   # 33라운드: 홈 G09→G07, 밝은 판 G14→G12
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
        s.px(0, 1, G[0]); s.px(0, 2, G[6])    # 33라운드: 번짐 G10→G06 (바랜 종이보다 어둡게)
    else:
        s.px(0, 1, G[8]); s.px(0, 2, G[2])    # 잉크 패널용 G09/G03 → G08/G02
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
        if rnd.random() < 0.3:
            s.rect(x, y + 1, x + n - 2, y + 1, G[4])   # 번진 잉크 (바랜 종이 위 G04)
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
    s.rect(2, 2, W - 3, 2, G[4]); s.rect(2, 2, 2, H - 3, G[4])   # 표지 윗·왼 빛 (33라운드 G05→G04)
    # 쌓인 종이 단면 (페이지 아래쪽 2줄·오른쪽 2줄 G11/G12 번갈아)
    def page(x0, y0, x1, y1, gutter_right):
        s.rect(x0 + 2, y0 + 2, x1 + 2, y1 + 2, G[6])           # 아래 그림자
        s.rect(x0 + 1, y0 + 1, x1 + 1, y1 + 1, G[7])           # 종이 단면
        s.rect(x0, y0, x1, y1, PAPER)                           # 낡은 종이 G09
        s.rect(x0, y0, x1, y0, PAPER_LIGHT); s.rect(x0, y0, x0, y1, PAPER_LIGHT)
        # 안쪽 홈(제본부) 그늘: 홈 쪽 3열 G12
        if gutter_right:
            s.rect(x1 - 2, y0 + 1, x1, y1, PAPER_DARK)
        else:
            s.rect(x0 + 1, y0 + 1, x0 + 3, y1, PAPER_DARK)
        # 괘선 (G07) 7px 간격
        for y in range(y0 + 10, y1 - 3, 7):
            s.rect(x0 + 4, y, x1 - 4, y, G[7])
        # 바랜 얼룩 (G08 + 19 점)
        blob(s, (x0 + x1) // 2 + 6, y1 - 14, 9, 5, PAPER_DARK, seed=x0, density=0.6, stain=0.2)
    LX0, LX1, RX0, RX1, PY0, PY1 = 7, 76, 83, 152, 6, 86
    page(LX0, PY0, LX1, PY1, True)
    page(RX0, PY0, RX1, PY1, False)
    # 제본부: 가운데 어두운 홈 + 실 꿰맨 자국
    s.rect(77, 2, 82, H - 3, G[1])
    s.rect(79, 2, 80, H - 3, G[0])
    for y in range(10, H - 8, 9):
        s.rect(78, y, 81, y, G[6]); s.rect(78, y + 1, 81, y + 1, G[6])
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
    ring.circle(cx, cy, 10, A[2], fill=False)
    ring.circle(cx, cy, 9, A[3], fill=False)
    ring.circle(cx, cy, 10, A[2], fill=False)
    import random
    rnd = random.Random(5)
    rimg = ring.composite(1)
    for y in range(H):
        for x in range(W):
            if rimg.getpixel((x, y))[3] and rnd.random() < 0.78:
                s.px(x, y, rimg.getpixel((x, y)))
    # 고리 아래쪽은 더 진하게(술이 고인 쪽): 2px 두께
    for x in range(cx - 6, cx + 7):
        s.px(x, cy + 10, A[3]); s.px(x, cy + 9, A[2])
    s.despeckle(min_cluster=2)
    # 책갈피 끈 (호박 base, 가장자리 base_dark): 제본부 위에서 오른쪽 페이지로 늘어짐
    s.rect(81, 0, 83, 0, A[3])
    for y in range(0, 30):
        x = 84 + (y * 7) // 30
        s.px(x, y, A[4]); s.px(x + 1, y, A[4]); s.px(x + 2, y, A[3])
    s.rect(91, 30, 93, 33, A[3]); s.px(92, 34, A[3]); s.px(92, 35, A[3])   # 끈 끝 매듭
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
        s.rect(RX1 - k, PY1 - 4 + k, RX1, PY1 - 4 + k, G[7])
    for k in range(4):
        s.rect(RX1 - 4 + k, PY1 - 4 + k, RX1 - 4 + k, PY1, PAPER_LIGHT)
    # 표지 얼룩 (G02) 좌상단
    s.rect(10, 92, 20, 93, G[2]); s.rect(12, 91, 17, 91, G[2])
    return s


def diary_closed():
    W, H = 96, 64
    s = new(W, H)
    s.rect(1, 1, W - 2, H - 2, G[3])
    s.rect(1, 1, W - 2, H - 2, G[0], fill=False)
    s.rect(2, 2, W - 3, 2, G[4]); s.rect(2, 2, 2, H - 3, G[4])
    s.rect(2, 2, 9, H - 3, G[1])                                   # 책등
    s.rect(10, 2, 10, H - 3, G[0])
    # 종이 단면 (오른쪽 4열 G13/G12 번갈아, 아래 2줄)
    for i, c in enumerate([G[8], G[9], G[8], G[9]]):
        s.rect(W - 6 + i, 4, W - 6 + i, H - 5, c)
    s.rect(12, H - 4, W - 3, H - 4, G[8]); s.rect(12, H - 3, W - 3, H - 3, G[7])
    # 가죽 끈 가로 (G07/G05) + 매듭
    s.rect(2, 38, W - 7, 40, G[7]); s.rect(2, 40, W - 7, 40, G[5])
    s.rect(2, 37, W - 7, 37, G[0]); s.rect(2, 41, W - 7, 41, G[0])
    s.rect(60, 35, 66, 43, G[7]); s.rect(60, 35, 66, 43, G[0], fill=False); s.rect(62, 37, 64, 41, G[5])
    # 호박 밀랍 봉인 (오른쪽 위, r=5): 21 base + 20 그늘 + 23 하이라이트 + 안 문양 19
    cx, cy = 76, 20
    s.circle(cx, cy, 5, A[3], fill=True)
    s.circle(cx - 1, cy - 1, 4, A[4], fill=True, only="opaque")
    s.rect(cx - 2, cy - 2, cx - 1, cy - 2, A[6]); s.px(cx - 3, cy - 1, A[6])
    s.rect(cx - 1, cy, cx + 1, cy, A[2]); s.rect(cx, cy - 1, cx, cy + 1, A[2])
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
    INK = G[2]   # 33라운드: 바랜 잉크 G02 (닳은 자리 G03/G04)
    s.circle(c, c, 22, INK, fill=False); s.circle(c, c, 21, INK, fill=False)
    s.circle(c, c, 18, INK, fill=False)
    if kind == "dead":
        # 큰 X (3px 두께) + 아래로 흐른 잉크
        for o in (-1, 0, 1):
            s.line(13 + o, 13, 33 + o, 33, INK); s.line(33 + o, 13, 13 + o, 33, INK)
        s.rect(23, 34, 24, 40, INK); s.px(23, 41, INK); s.px(23, 42, INK)
    else:
        # 오르는 계단: 4단 채운 실루엣 (디딤 5, 챌판 5), 바닥선 포함
        x0, y1 = 12, 35
        for k in range(4):
            s.rect(x0 + k * 5, y1 - (k + 1) * 5 + 1, x0 + 23, y1, INK)
        s.rect(x0 - 2, y1 + 1, x0 + 25, y1 + 2, INK)
    # 눌림 불균일: 고리·문양 안에서 12% 를 G03(옅음), 7% 를 빼냄
    rnd = random.Random(3 if kind == "dead" else 4)
    img = s.composite(1)
    for y in range(S):
        for x in range(S):
            if img.getpixel((x, y))[3]:
                r = rnd.random()
                if r < 0.09:
                    s.px(x, y, (0, 0, 0, 0))
                elif r < 0.21:
                    s.px(x, y, G[4])
                elif r < 0.33:
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
    W, H = 1400, 820
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
    put("paper_tile 64", assets["paper_tile"], 690, y)
    ink_big = nine(assets["panel_ink"], INK_SL, 200, 60)
    put("panel_ink 48", assets["panel_ink"], 840, y)
    put("panel_ink 9-slice 200x60", ink_big, 960, y)
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
    for row, bgc in enumerate([PAPER, G[1]]):
        for i, n in enumerate(names):
            x, y = 8 + i * cell, 8 + row * cell
            ImageDraw.Draw(img).rectangle([x - 4, y - 4, x + 16 * k + 3, y + 16 * k + 3], fill=rgba(bgc))
            im = icons[n].composite(1)
            off = 4 * k if im.width == 8 else 0
            img.alpha_composite(up(im, k), (x + off, y + off))
    for i, n in enumerate(names):
        text(img, (8 + i * cell, cell * 2 + 14), n.replace("icon_", "").replace("mini_", "m:"), G[14], 16)
    img.convert("RGB").save(os.path.join(HERE, "preview_icons.png"))


def _mock_scene(W, H):
    """1층 타일 배경 + 주인공·적 (목업 공용)."""
    import random
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
    return img


def _paper(assets, w, h):
    paper = nine(assets["panel_paper"], PAPER_SL, w, h)
    tile_fill(paper, assets["paper_tile"], PAPER_INNER["left"], PAPER_INNER["top"],
              w - PAPER_INNER["left"] - PAPER_INNER["right"], h - PAPER_INNER["top"] - PAPER_INNER["bottom"])
    return paper


def _with_alpha(im, a):
    im = im.copy()
    al = im.getchannel("A").point(lambda v: int(v * a))
    im.putalpha(al)
    return im


def preview_mock(assets, sheet, icon_frames):
    """960x540 (33라운드 레이아웃): 상단 좌 층 제목 / 상단 우 미니맵+음소거 /
    하단 중앙 한 묶음(체력·전표·독주·무기·개성·우클릭, 잉크 패널 480) / 그 위 보스 게이지 / 그 위 자막 /
    중앙 낡은 종이 일시정지 패널. 종이 위 글자: 제목 G00, 본문 G01, 흐림 G04."""
    W, H = 960, 540
    img = _mock_scene(W, H)
    d = ImageDraw.Draw(img)

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
    # 상단 좌: 층 제목 · 시련 (패널 없이 그림자 글씨)
    text(img, (P + 4, P + 2), "1층 · 술독 제국 '잔'   시련 2/4", G[11], 16, shadow=G[0])
    # 상단 우: 미니맵 + 음소거
    mw, mh = 118, 98
    img.alpha_composite(nine(assets["minimap_frame"], MINI_SL, mw, mh), (W - P - mw, P))
    cell = 14
    ox, oy = W - P - mw + 10, P + 10
    rooms = [((0, 1), "mini_start", True), ((1, 1), "mini_trial", True), ((2, 1), "mini_trial", False),
             ((1, 0), "mini_rest", False), ((2, 2), "mini_boss", False), ((3, 1), "mini_trial", True)]
    for (ax, ay), (bx, by) in [((0, 1), (1, 1)), ((1, 1), (2, 1)), ((1, 1), (1, 0)), ((2, 1), (2, 2)), ((2, 1), (3, 1))]:
        d.line([ox + ax * cell * 2 + cell // 2 + 7, oy + ay * cell * 2 + cell // 2 + 7,
                ox + bx * cell * 2 + cell // 2 + 7, oy + by * cell * 2 + cell // 2 + 7], fill=rgba(G[4]), width=2)
    for (cx, cy), nm, cleared in rooms:
        x, y = ox + cx * cell * 2 + 3, oy + cy * cell * 2 + 3
        d.rectangle([x, y, x + 21, y + 21], fill=rgba(G[3] if cleared else G[2]))
        icon(nm, x + 7, y + 7)
    x, y = ox + 1 * cell * 2 + 3, oy + 1 * cell * 2 + 3
    d.rectangle([x - 1, y - 1, x + 22, y + 22], outline=rgba(A[6]))
    icon("icon_sound", W - P - 16 - 44, P + mh + 6)
    text(img, (W - P - 44 + 2, P + mh + 6), "M", G[11], 16)
    # 하단 중앙 한 묶음: 잉크 패널 480x64
    bw0, bh0 = 480, 64
    x0, y0 = (W - bw0) // 2, H - P - bh0
    img.alpha_composite(nine(assets["panel_ink"], INK_SL, bw0, bh0), (x0, y0))
    icon("icon_hp", x0 + 8, y0 + 8)
    gauge(x0 + 28, y0 + 11, 180, 0.72)
    text(img, (x0 + 214, y0 + 7), "72 / 100", G[13], 16)
    icon("icon_gold", x0 + 292, y0 + 8)
    text(img, (x0 + 312, y0 + 7), "137", G[13], 16)
    icon("icon_potion", x0 + 352, y0 + 8)
    text(img, (x0 + 372, y0 + 7), "2/3  Q", G[13], 16)
    wi = Image.open(os.path.join(ROOT, "assets", "sprites", "weapons", "katana_icon.png")).convert("RGBA")
    img.alpha_composite(wi, (x0 + 8, y0 + 38))
    text(img, (x0 + 28, y0 + 37), "사무라이 칼 · 거합", G[13], 16)
    icon("icon_sense", x0 + 184, y0 + 38)
    gauge(x0 + 204, y0 + 41, 100, 0.4, gray=True)
    text(img, (x0 + 310, y0 + 37), "40/100", G[11], 16)
    text(img, (x0 + 376, y0 + 37), "우클릭 패링", G[11], 16)
    # 그 위: 보스 게이지 360
    gw = 360
    gx, gy = W // 2 - gw // 2, y0 - 8 - 14
    icon("icon_boss", gx - 22, gy - 1)
    text(img, (W // 2, gy - 20), "양조장주  페이즈 1", A[6], 16, anchor="ma", shadow=G[0])
    gauge(gx, gy, gw, 0.63, boss=True)
    # 그 위: 자막 (그림자 글씨, 패널 없음)
    text(img, (W // 2, gy - 44), "양조장주: 「잔을 비우기 전엔 아무도 못 나간다.」", G[13], 16, anchor="ma", shadow=G[0])
    # 우하단: 출구 열림 공지 (작은 잉크 패널) — 묶음 바깥, 임시
    nw, nh = 150, 30
    img.alpha_composite(nine(assets["panel_ink"], INK_SL, nw, nh), (W - P - nw, H - P - nh))
    icon("icon_exit", W - P - nw + 8, H - P - nh + 7)
    text(img, (W - P - nw + 30, H - P - nh + 6), "오르는 길 열림", A[6], 16)
    # 중앙: 낡은 종이 메뉴 (일시정지 '일기장')
    pw, ph = 420, 236
    px0, py0 = W // 2 - pw // 2, H // 2 - ph // 2 - 10
    img.alpha_composite(_paper(assets, pw, ph), (px0, py0))
    text(img, (W // 2, py0 + 18), "일기장", G[0], 16, anchor="ma")
    img.alpha_composite(assets["rule"].resize((pw - 60, 4), Image.NEAREST), (px0 + 30, py0 + 40))
    text(img, (px0 + 30, py0 + 50), "전장의 망령   1층 · 술독 제국 '잔'   시련 2/4", G[1], 16)
    text(img, (px0 + 30, py0 + 70), "공격 7  방어 3  치명타 5%  감각 2", G[1], 16)
    text(img, (px0 + 30, py0 + 90), "무기: 사무라이 칼 · 거합  (개성 40/100)", G[1], 16)
    icon("icon_save", px0 + 30, py0 + 110)
    text(img, (px0 + 52, py0 + 110), "세이브 남음 2", G[1], 16)
    img.alpha_composite(assets["rule"].resize((pw - 60, 4), Image.NEAREST), (px0 + 30, py0 + 136))
    cur = Image.open(os.path.join(OUT, "cursor.png")).crop((0, 0, 8, 8))
    img.alpha_composite(cur, (px0 + 32, py0 + 154))
    text(img, (px0 + 48, py0 + 150), "[1] 더 쓴다 (Esc)", G[0], 16)
    text(img, (px0 + 48, py0 + 172), "[2] 그래도 덮는다", G[3], 16)
    text(img, (px0 + 30, py0 + 204), "덮으면 이 층의 기록은 지워진다", G[4], 16)
    img.alpha_composite(_with_alpha(assets["stamp_clear"], 0.85), (px0 + pw - 92, py0 + ph - 92))
    img.convert("RGB").save(os.path.join(HERE, "preview_mock.png"))
    print("preview -> preview_mock.png")


def preview_mock_result(assets, sheet, icon_frames):
    """결과 화면 목업: 어두워진 전장 위 낡은 종이 전면(600x400) + 닫힌 일기장 + 사망 도장."""
    W, H = 960, 540
    img = _mock_scene(W, H)
    img.alpha_composite(Image.new("RGBA", (W, H), rgba(G[0], 150)))

    def icon(name, x, y):
        f = icon_frames[name]
        img.alpha_composite(sheet.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])), (x, y))

    pw, ph = 600, 400
    px0, py0 = (W - pw) // 2, (H - ph) // 2
    img.alpha_composite(_paper(assets, pw, ph), (px0, py0))
    text(img, (W // 2, py0 + 22), "일기장을 덮는다", G[0], 16, anchor="ma")
    img.alpha_composite(assets["rule"].resize((pw - 80, 4), Image.NEAREST), (px0 + 40, py0 + 46))
    img.alpha_composite(assets["diary_closed"], (px0 + 40, py0 + 64))
    lx = px0 + 160
    text(img, (lx, py0 + 64), "전장의 망령은 1층 · 술독 제국 '잔' 에서 쓰러졌다", G[1], 16)
    text(img, (lx, py0 + 88), "시련 2/4   방 7   걸린 시간 04:12", G[1], 16)
    icon("icon_gold", lx, py0 + 112); text(img, (lx + 22, py0 + 112), "전표 137", G[1], 16)
    icon("icon_souls", lx + 140, py0 + 112); text(img, (lx + 162, py0 + 112), "영혼 +12", G[1], 16)
    wi = Image.open(os.path.join(ROOT, "assets", "sprites", "weapons", "katana_icon.png")).convert("RGBA")
    img.alpha_composite(wi, (lx, py0 + 136)); text(img, (lx + 22, py0 + 136), "사무라이 칼 · 거합  (개성 40/100)", G[1], 16)
    text(img, (lx, py0 + 160), "쓰러뜨린 적 23   받은 피해 188", G[4], 16)
    img.alpha_composite(assets["rule"].resize((pw - 80, 4), Image.NEAREST), (px0 + 40, py0 + 200))
    text(img, (px0 + 40, py0 + 216), "'한 잔만 더' 라는 말을 믿지 말 걸 그랬다.", G[1], 16)
    text(img, (px0 + 40, py0 + 238), "다음 장은 비어 있다.", G[4], 16)
    cur = Image.open(os.path.join(OUT, "cursor.png")).crop((0, 0, 8, 8))
    img.alpha_composite(cur, (px0 + 42, py0 + 300))
    text(img, (px0 + 58, py0 + 296), "[Enter] 다시 쓴다", G[0], 16)
    text(img, (px0 + 58, py0 + 318), "[Esc] 본영으로", G[3], 16)
    icon("icon_save", px0 + 42, py0 + 346); text(img, (px0 + 64, py0 + 346), "세이브 남음 1", G[4], 16)
    img.alpha_composite(_with_alpha(assets["stamp_dead"], 0.85), (px0 + pw - 48 - 48, py0 + ph - 44 - 48))
    img.convert("RGB").save(os.path.join(HERE, "preview_mock_result.png"))
    print("preview -> preview_mock_result.png")


# ============================================================ main
def main():
    assets = {}

    pp = panel_paper()
    assets["panel_paper"] = check("panel_paper", pp)
    export("panel_paper", pp, {"kind": "nineslice", "width": 80, "height": 80, "slice": PAPER_SL,
                                "inner": PAPER_INNER, "tile": "paper_tile.png (draw as tileSprite inside `inner` on top of the stretched center)",
                                "colors": "old paper G09 (G10 light / G08 stain / G07 crease·worn edge / 19 stain dots), ink G01 + bleed G03, inner faint rule G06",
                                "edges": "corners have 1-3px torn bites (alpha 0) and a folded dog-ear at bottom-right; keep stretched middle bands plain"})
    pt = paper_tile()
    assets["paper_tile"] = check("paper_tile", pt)
    export("paper_tile", pt, {"kind": "tile", "width": 64, "height": 64, "seamless": True,
                               "colors": "paper G09 base, G08 shade/fibre, G10 lighter patches, stain 19 (2-3px clusters)"})

    pi = panel_ink()
    assets["panel_ink"] = check("panel_ink", pi, allow_semi=1)
    export("panel_ink", pi, {"kind": "nineslice", "width": 48, "height": 48, "slice": INK_SL, "inner": INK_INNER,
                              "centerAlpha": round(INK_ALPHA / 255, 2), "colors": "rim G01 (top/left), G00 (bottom/right), brackets G02, fill G01 @ 0.85"})
    mf = minimap_frame()
    assets["minimap_frame"] = check("minimap_frame", mf)
    export("minimap_frame", mf, {"kind": "nineslice", "width": 32, "height": 32, "slice": MINI_SL,
                                  "inner": {"left": 4, "right": 4, "top": 4, "bottom": 4}, "colors": "G00/G01/G02 + G04 corner marks"})

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
    export("gauge_fill", fl, {"kind": "strip", "width": 1, "height": 8, "rows": "22 base_light, 21 base, 20 base_dark x3, 19 shadow1 x2, 18 shadow2 (round 33: one step darker)",
                               "usage": "stretch horizontally (NEAREST). Floor-1 amber; system/UI swaps to current floor ramp"})
    fg = gauge_fill_gray()
    assets["gauge_fill_gray"] = check("gauge_fill_gray", fg)
    export("gauge_fill_gray", fg, {"kind": "strip", "width": 1, "height": 8, "rows": "G14, G13, G12 x3, G10 x2, G09",
                                    "usage": "luminance strip for multiplicative tint (setTint with ramp 23 light1 ≈ gauge_fill) or as-is for gray gauges (personality)"})

    icons, sheet = build_icons()
    with open(os.path.join(OUT, "icons.json"), encoding="utf-8") as fp:
        icon_frames = json.load(fp)["frames"]

    cu = cursor(True)
    check("cursor", cu, allow_iso=1)
    export("cursor", cu, {"kind": "strip", "frameWidth": 8, "frameHeight": 8, "frames": 2, "frameDurationsMs": [420, 260],
                           "loop": True, "pivot": {"x": 4, "y": 4}, "colors": "ink G01, slit G07, drop 21 (frame 2)"})
    cl = cursor(False)
    check("cursor_light", cl, allow_iso=1)
    export("cursor_light", cl, {"kind": "strip", "frameWidth": 8, "frameHeight": 8, "frames": 2, "frameDurationsMs": [420, 260],
                                 "loop": True, "pivot": {"x": 4, "y": 4}, "colors": "G12/G08, drop 21 — for ink panels"})
    ru = rule(True)
    assets["rule"] = check("rule", ru)
    export("rule", ru, {"kind": "tile", "width": 1, "height": 4, "usage": "stretch/tile horizontally; row1 ink G00, row2 bleed G06"})
    rl = rule(False)
    assets["rule_light"] = check("rule_light", rl)
    export("rule_light", rl, {"kind": "tile", "width": 1, "height": 4, "usage": "for ink panels; row1 G08, row2 G02"})

    td = title_diary()
    assets["title_diary"] = check("title_diary", td)
    export("title_diary", td, {"kind": "image", "width": 160, "height": 96, "pivot": {"x": 80, "y": 48},
                                "accent": "bookmark ribbon 19/20, wine-cup ring 18/19 (runtime swap ok); pages old paper G09"})
    dc = diary_closed()
    assets["diary_closed"] = check("diary_closed", dc)
    export("diary_closed", dc, {"kind": "image", "width": 96, "height": 64, "pivot": {"x": 48, "y": 32},
                                 "accent": "wax seal 18/19/20/22"})
    for kind in ["dead", "clear"]:
        st = stamp(kind)
        assets["stamp_" + kind] = check("stamp_" + kind, st)
        export("stamp_" + kind, st, {"kind": "image", "width": 48, "height": 48, "pivot": {"x": 24, "y": 24},
                                     "colors": "faded ink G02 + worn G03/G04 (grayscale; UI may set alpha 0.8-0.9)"})

    preview_icons(icons)
    preview_kit(assets, icons, sheet)
    preview_mock(assets, sheet, icon_frames)
    preview_mock_result(assets, sheet, icon_frames)

    print("\n%-16s %-8s gray acc other iso semi" % ("asset", "size"))
    for r in REPORT:
        print("%-16s %-8s %4d %3d %5d %3d %4d" % r)


if __name__ == "__main__":
    main()
