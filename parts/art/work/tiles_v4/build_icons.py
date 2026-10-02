#!/usr/bin/env python3
"""LOPAD 노드 지도 아이콘 (48라운드 Q3·Q9, 계약 art-assets §6.5, UI 키트 규칙 contracts/ui-art-kit.md).

실행: python3 parts/art/work/tiles_v4/build_icons.py
산출: assets/sprites/ui/node_icons.png (192x96 = 32x32 x 6열 x 3행) + node_icons.json
      parts/art/work/tiles_v4/preview_icons.png (시트 4배 · 일기장 페이지 위 1배 지도 목업 + 2배)

열 순서 고정: journey, battle, shop, rest, event, boss.  행: 0 기본 / 1 지나옴(식음) / 2 잠김(흐림).
색: UI 세피아 S0~S5 + 현재 층 강조 1점(슬롯 21 본색, 22 밝은 끝) — 1층 램프로 그리고 UI 가 층 램프로 바꿔 쓴다(다른 UI 키트와 같음).
모양: 마름모 테(발광 잉크 S5 1px + 안쪽 할로 S4 + 바깥 그늘 S2) 안에 짙은 가죽 바탕 S1, 상징은 S5 선 + 4방향 할로 S4 (글자 발광 규칙 1.2절과 같은 구조).
  상징 = 여정: 원근으로 뻗어 나가는 길 + 지평선 불빛(49라운드 교체) / 전투: 엇갈린 칼 / 상점: 묶은 자루 / 휴식: 모닥불 / 이벤트: 물음표 / 보스: 왕관.
  강조 1점 = 여정 길 끝 너머 불빛 · 칼끝 · 자루의 동전 · 불꽃 심 · 물음표 점 · 왕관 보석.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "pixel-art-studio", "scripts"))
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

PAL = json.load(open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8"))
S = PAL["ui"]["ramp"]          # S0..S5
A = PAL["floors"][0]["ramp"]   # 1층 강조 (16+i)
OUT = os.path.join(ROOT, "assets", "sprites", "ui")
CELL = 32
ORDER = ["journey", "battle", "shop", "rest", "event", "boss"]
STATES = ["default", "visited", "locked"]
CX = CY = 16


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


# ---------------------------------------------------------------------- 상징 (셀 좌표 그대로, 마름모 안쪽 |dx|+|dy|<=11 에 들어가게)
def line(pts, a, b):
    (x0, y0), (x1, y1) = a, b
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.add((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy


def rows(pts, ox, oy, art, ch="#"):
    for j, r in enumerate(art):
        for i, c in enumerate(r):
            if c == ch:
                pts.add((ox + i, oy + j))


def glyph(name):
    """returns (ink 픽셀 집합, 면 픽셀 집합(S2), 강조 [(x,y,슬롯)])"""
    ink, fill, acc = set(), set(), []
    if name == "journey":
        # 49라운드 6절 — "계단이 놓여져 있는데 이것 보다는 앞으로 나아간다는 느낌": 굽은 점선 길(계단처럼 읽힘)을 버리고
        # **원근으로 뻗어 나가는 길**: 아래(가까움)는 넓고 지평선 쪽으로 좁아지는 두 가장자리 + 가운데 끊긴 중앙선(멀수록 짧게) +
        # 지평선 한 줄, 길 끝 너머에 강조 한 점(가야 할 곳의 불빛).
        # (1회차: 지평선 한 줄을 그었더니 'A' 모양 송전탑으로 읽혔다 → 지평선을 빼고 길 끝을 열어 두었다. 길 끝 너머 불빛만.)
        line(ink, (11, 21), (15, 10)); line(ink, (21, 21), (17, 10))       # 길 가장자리 (원근, 위로 모임)
        for y in range(10, 22):                                             # 길 면
            xl = 11 + (21 - y) * 4 / 11.0
            xr = 21 - (21 - y) * 4 / 11.0
            for x in range(int(xl) + 1, int(round(xr))):
                fill.add((x, y))
        fill -= ink
        dash = {(16, 20), (16, 19), (16, 18), (16, 15), (16, 14), (16, 12)}   # 중앙선: 가까울수록 길게
        ink |= dash
        fill -= dash
        acc = [(16, 7, 22), (16, 8, 21)]
    elif name == "battle":
        # 엇갈린 칼 둘 — 마름모 안은 대각선 폭이 ±5 뿐이라 가파르게 세우고, 코등이는 가로 막대로 떨어뜨렸다(1회차: 칼끝이 테에 닿아 X 로만 읽힘)
        line(ink, (12, 9), (18, 18)); line(ink, (20, 9), (14, 18))     # 칼날
        line(ink, (17, 19), (21, 19)); line(ink, (11, 19), (15, 19))   # 코등이
        line(ink, (19, 20), (20, 22)); line(ink, (13, 20), (12, 22))   # 자루
        acc = [(12, 9, 22), (20, 9, 22)]
        ink -= {(12, 9), (20, 9)}
    elif name == "shop":
        # 묶은 자루: 위로 모인 주름 + 좁은 목 끈 + 둥근 몸통, 동전은 몸통 아래쪽 (2회차: 귀 둘 + 가운데 동전이 얼굴로 읽혔다)
        rows(ink, 11, 8, ["...#.#.#...",
                          "....###....",
                          ".....#.....",
                          "....###....",
                          "...#...#...",
                          "..#.....#..",
                          ".#.......#.",
                          "#.........#",
                          "#.........#",
                          ".#.......#.",
                          "..#######.."])
        rows(fill, 11, 8, ["...........",
                           "...........",
                           "...........",
                           "...........",
                           "....###....",
                           "...#####...",
                           "..#######..",
                           ".#########.",
                           ".#########.",
                           "..#######..",
                           "..........."])
        acc = [(17, 16, 22), (18, 16, 21), (17, 17, 21), (18, 17, 20)]
        fill -= {(x, y) for x, y, _ in acc}
    elif name == "rest":
        rows(ink, 11, 7, ["....#.....",
                          "....##....",
                          "...#.#....",
                          "...#..#...",
                          "..#...#.#.",
                          "..#....##.",
                          ".#......#.",
                          ".#......#.",
                          "..#....#..",
                          "...####..."])
        rows(fill, 11, 7, ["..........",
                           "..........",
                           "....#.....",
                           "....##....",
                           "...###....",
                           "...####...",
                           "..######..",
                           "..######..",
                           "...####...",
                           ".........."])
        line(ink, (11, 19), (20, 22)); line(ink, (21, 19), (12, 22))   # 엇갈린 장작
        acc = [(15, 13, 22), (15, 14, 21), (16, 14, 21)]
        fill -= {(x, y) for x, y, _ in acc}
    elif name == "event":
        rows(ink, 12, 7, ["..####..",
                          ".#....#.",
                          "#......#",
                          "......#.",
                          ".....#..",
                          "....#...",
                          "...#....",
                          "...#....",
                          "........",
                          "........",
                          "........",
                          "........"])
        rows(fill, 12, 7, ["........",
                           "..####..",
                           ".######.",
                           "........"])
        fill -= ink
        # 물음표 획을 2px 로 (세로 부분): 할로가 둘러도 뭉개지지 않게 바깥으로만 덧댄다
        ink |= {(13, 9), (18, 9), (16, 12), (15, 13)}
        acc = [(15, 17, 21), (16, 17, 22), (15, 18, 20), (16, 18, 21)]
    elif name == "boss":
        rows(ink, 11, 10, ["#....#....#",
                           "##..#.#..##",
                           "#.##...##.#",
                           "#.........#",
                           "#.........#",
                           "###########",
                           "#.........#",
                           "###########"])
        rows(fill, 11, 10, ["...........",
                            ".....#.....",
                            ".#..###..#.",
                            ".#########.",
                            ".#########.",
                            "...........",
                            ".#########.",
                            "..........."])
        fill -= ink
        acc = [(15, 13, 22), (16, 13, 21), (15, 14, 21), (16, 14, 20)]
        fill -= {(x, y) for x, y, _ in acc}
    for x, y in ink | fill | {(x, y) for x, y, _ in acc}:
        assert abs(x - CX) + abs(y - CY) <= 11, (name, x, y)
    return ink, fill, acc


# ---------------------------------------------------------------------- 칸 그리기
def d4(p):
    x, y = p
    return {(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)}


def dist(x, y):
    return abs(x - CX) + abs(y - CY)


def draw_cell(name, state):
    im = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    px = im.load()
    put = lambda x, y, h: px.__setitem__((x, y), rgb(h) + (255,)) if 0 <= x < CELL and 0 <= y < CELL else None  # noqa: E731
    ink, fill, acc = glyph(name)
    for y in range(CELL):
        for x in range(CELL):
            d = dist(x, y)
            if state == "default":
                if d == 15: put(x, y, S[2])          # 바깥 그늘 ring
                elif d == 14: put(x, y, S[5])        # 발광 테
                elif d == 13: put(x, y, S[4])        # 안쪽 할로
                elif d <= 12: put(x, y, S[1])        # 가죽 바탕
            elif state == "visited":
                if d == 15: put(x, y, S[2])
                elif d == 14: put(x, y, S[4])        # 식은 테 (발광 없음)
                elif d <= 13: put(x, y, S[1])
            else:  # locked: 흐린 바탕 S2 + 끊긴 테 S4 (1회차: S2 테만으로는 페이지 얼룩에 묻혀 1배에서 안 보였다)
                if d == 14 and ((x + y) // 2) % 2 == 0:
                    put(x, y, S[4])
                elif d <= 13:
                    put(x, y, S[2])
    if state == "default":
        halo = set()
        for p in ink | {(x, y) for x, y, _ in acc}:
            halo |= d4(p)
        for x, y in halo - ink - fill:
            if dist(x, y) <= 12:
                put(x, y, S[4])
        for x, y in fill:
            put(x, y, S[2])
        for x, y in ink:
            put(x, y, S[5])
        for x, y, slot in acc:
            put(x, y, A[slot - 16])
    elif state == "visited":
        for x, y in fill:
            put(x, y, S[2])
        for x, y in ink | {(x, y) for x, y, _ in acc}:
            put(x, y, S[4])
    else:
        for x, y in ink | {(x, y) for x, y, _ in acc}:
            put(x, y, S[3])                          # 눌린 자국처럼 흐리게 (S3 on S2)
    return im


def build():
    sheet = Image.new("RGBA", (CELL * len(ORDER), CELL * len(STATES)), (0, 0, 0, 0))
    for r, st in enumerate(STATES):
        for c, nm in enumerate(ORDER):
            sheet.alpha_composite(draw_cell(nm, st), (c * CELL, r * CELL))
    sheet.save(os.path.join(OUT, "node_icons.png"))
    meta = {
        "image": "node_icons.png",
        "frameWidth": CELL, "frameHeight": CELL,
        "columns": len(ORDER), "rows": len(STATES),
        "order": ORDER,
        "states": STATES,
        "frameIndex": "row * columns + column  (row = state: 0 default, 1 visited, 2 locked; column = order)",
        "pivot": {"x": CX, "y": CY},
        "anchor": "ui",
        "accentSlots": [20, 21, 22],
        "notes": {
            "shape": "diamond node: glowing ink rim S5 + inner halo S4 + outer shade S2, dark leather fill S1; symbol S5 + 4-neighbour halo S4",
            "journey": "road receding in perspective toward a light beyond its end (49라운드: 계단처럼 읽히던 굽은 점선 길 교체 — '앞으로 나아가는 길')", "battle": "crossed blades",
            "shop": "tied sack + coin", "rest": "campfire", "event": "question mark", "boss": "crown",
            "accent": "one accent point per icon (slots 20-22, drawn with floor-1 ramp; UI swaps to current floor ramp like other UI kit files)",
            "visited": "cooled: rim and symbol S4, no glow, no accent",
            "locked": "no fill (page shows through), broken rim S2 + symbol S2 = faint pressed mark",
            "scale": "integer only, no rotation (UI kit 4)",
        },
        "palette": "parts/art/palette/lopad.json (ui.ramp sepia S0-S5 fixed, UI only + floor accent slots 20-22 runtime swap)",
    }
    with open(os.path.join(OUT, "node_icons.json"), "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    return sheet


# ---------------------------------------------------------------------- 미리보기
def preview(sheet):
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
    except Exception:
        font = ImageFont.load_default()
    paper = Image.open(os.path.join(OUT, "paper_tile.png")).convert("RGBA")

    def page(w, h):
        bg = Image.new("RGBA", (w, h))
        for y in range(0, h, paper.height):
            for x in range(0, w, paper.width):
                bg.alpha_composite(paper, (x, y))
        return bg

    # (a) 시트 4배 on 페이지
    sw, sh = sheet.width * 4, sheet.height * 4
    a = page(sheet.width, sheet.height)
    a.alpha_composite(sheet)
    a = a.resize((sw, sh), Image.NEAREST)
    # (b) 1배 지도 목업: 1층 = 여정 3 → 갈림길 두 줄 (3+3) → 보스, 지나온 노드·현재·잠김 섞음
    mw, mh = 300, 150
    m = page(mw, mh)
    d = ImageDraw.Draw(m)
    nodes = {"j0": (20, 75, "journey", 1), "j1": (60, 75, "battle", 1), "j2": (100, 75, "rest", 1),
             "a0": (140, 45, "battle", 0), "a1": (180, 45, "shop", 2), "a2": (220, 45, "battle", 2),
             "b0": (140, 105, "event", 0), "b1": (180, 105, "rest", 2), "b2": (220, 105, "battle", 2),
             "boss": (270, 75, "boss", 2)}
    edges = [("j0", "j1"), ("j1", "j2"), ("j2", "a0"), ("j2", "b0"), ("a0", "a1"), ("a1", "a2"), ("b0", "b1"), ("b1", "b2"),
             ("a2", "boss"), ("b2", "boss")]
    for u, v in edges:
        (x0, y0, _, _), (x1, y1, _, _) = nodes[u], nodes[v]
        n = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(0, n, 4):
            x, y = x0 + (x1 - x0) * k // n, y0 + (y1 - y0) * k // n
            d.rectangle([x, y, x + 1, y], fill=rgb(S[4]))
    for x, y, nm, st in nodes.values():
        m.alpha_composite(sheet.crop((ORDER.index(nm) * CELL, st * CELL, ORDER.index(nm) * CELL + CELL, st * CELL + CELL)), (x - CX, y - CY))
    W = max(sw, mw * 3) + 20
    out = Image.new("RGB", (W, sh + mh * 3 + mh + 70), (60, 60, 64))
    dd = ImageDraw.Draw(out)
    dd.text((10, 4), "node_icons.png x4 on page — cols " + ", ".join(ORDER) + " / rows default, visited, locked", fill=(230, 230, 230), font=font)
    out.paste(a.convert("RGB"), (10, 20))
    y = 20 + sh + 10
    dd.text((10, y), "map mock 1x (UI scale)  +  x3", fill=(230, 230, 230), font=font)
    out.paste(m.convert("RGB"), (10, y + 16))
    out.paste(m.resize((mw * 3, mh * 3), Image.NEAREST).convert("RGB"), (10, y + 16 + mh + 10))
    out.save(os.path.join(HERE, "preview_icons.png"))


if __name__ == "__main__":
    sh = build()
    preview(sh)
    print("node_icons.png", sh.size)
