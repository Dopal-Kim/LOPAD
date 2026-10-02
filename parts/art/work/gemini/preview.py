#!/usr/bin/env python3
"""검수용 미리보기 (게임 투입 아님).
- preview_keyart_all.png : 키아트 5장 여정 순서 모음(1/2 축소 + 1장 원본 크기)
- preview_map_nodes.png  : 지도 위 노드 아이콘 목업(배치는 아트 임의 목업 — 실제 배치는 UI 몫)
- preview_tone_vs_quant.png : 게임 투입본(톤 맞춤) vs 보관 비교안(도트화·감색) 부분 확대
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gkit as K

UI = os.path.join(K.ROOT, "assets/sprites/ui")
FONT = None
for f in ["/usr/share/fonts/truetype/unifont/unifont.ttf", "/usr/share/fonts/opentype/unifont/unifont.otf",
          "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"]:
    if os.path.exists(f):
        FONT = ImageFont.truetype(f, 16)
        break
if FONT is None:
    FONT = ImageFont.load_default()

REGIONS = [("waste", "1 황무지·전장"), ("gate", "2 성문"), ("outer", "3 외곽 거리"),
           ("brewery", "4 양조 구역"), ("hall", "5 지배자의 연회장")]
BG = (20, 21, 22)


def label(d, xy, text):
    x, y = xy
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((x + dx, y + dy), text, font=FONT, fill=(0, 0, 0))
    d.text((x, y), text, font=FONT, fill=(235, 236, 237))


def keyart_all():
    W, H = 480, 270
    c = Image.new("RGB", (W * 2 + 24, 24 + (H + 28) * 3), BG)
    d = ImageDraw.Draw(c)
    label(d, (8, 4), "1층 '잔' 테마 키아트 — 여정 순서 (1/2 축소, 원본 960x540)")
    for i, (r, name) in enumerate(REGIONS):
        im = Image.open(f"{UI}/keyart_{r}.png").convert("RGB").resize((W, H), Image.LANCZOS)
        x = 8 + (i % 2) * (W + 8)
        y = 28 + (i // 2) * (H + 28)
        c.paste(im, (x, y))
        label(d, (x + 6, y + 4), name)
    # 남은 칸: 다섯 장 가로 띠(흐름 확인)
    x, y = 8 + W + 8, 28 + 2 * (H + 28)
    strip = Image.new("RGB", (W, H), BG)
    sw = W // 5
    for i, (r, _) in enumerate(REGIONS):
        im = Image.open(f"{UI}/keyart_{r}.png").convert("RGB").resize((int(sw * 540 / 270 * 0 + H * 960 / 540), H), Image.LANCZOS)
        cx = (im.width - sw) // 2
        strip.paste(im.crop((cx, 0, cx + sw, H)), (i * sw, 0))
    c.paste(strip, (x, y))
    label(d, (x + 6, y + 4), "흐름: 황무지 → 성문 → 외곽 → 양조 → 연회장")
    c.save(os.path.join(K.HERE, "preview_keyart_all.png"))


def map_nodes():
    m = Image.open(f"{UI}/map_bg_f1.png").convert("RGBA")
    icons = Image.open(f"{UI}/node_icons.png").convert("RGBA")
    order = ["journey", "battle", "shop", "rest", "event", "boss"]

    def icon(kind, state):
        col, row = order.index(kind), state
        return icons.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32))
    # (id, kind, x, y, state 0 기본 / 1 지나옴 / 2 잠김)
    nodes = [("a", "journey", 110, 135, 1), ("b", "battle", 200, 185, 1), ("c", "battle", 290, 232, 0),
             ("d1", "battle", 390, 258, 0), ("d2", "shop", 380, 340, 0),
             ("e1", "rest", 490, 300, 0), ("e2", "battle", 480, 372, 2),
             ("f1", "event", 590, 280, 0), ("f2", "battle", 590, 355, 0),
             ("g", "battle", 690, 312, 0), ("h", "rest", 772, 250, 0), ("i", "boss", 858, 218, 0)]
    edges = [("a", "b"), ("b", "c"), ("c", "d1"), ("c", "d2"), ("d1", "e1"), ("d2", "e1"), ("d2", "e2"),
             ("e1", "f1"), ("e1", "f2"), ("e2", "f2"), ("f1", "g"), ("f2", "g"), ("g", "h"), ("h", "i")]
    pos = {n[0]: (n[2], n[3]) for n in nodes}
    d = ImageDraw.Draw(m)
    S2, S4, S5 = (K.hex2rgb(K.SEPIA[i]) for i in (2, 4, 5))
    A21 = K.hex2rgb(K.RAMP1[5])
    for a, b in edges:
        (x0, y0), (x1, y1) = pos[a], pos[b]
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(0, n + 1):
            if (t // 4) % 2:
                continue
            x = round(x0 + (x1 - x0) * t / n)
            y = round(y0 + (y1 - y0) * t / n)
            d.point((x, y + 1), fill=S2)
            d.point((x, y), fill=S5 if a in ("a", "b") else S4)
    for nid, kind, x, y, st in nodes:
        m.alpha_composite(icon(kind, st), (x - 16, y - 16))
    cx, cy = pos["c"]
    d.ellipse((cx - 20, cy - 20, cx + 20, cy + 20), outline=A21, width=2)
    out = Image.new("RGB", (960, 540 + 28), BG)
    out.paste(m.convert("RGB"), (0, 28))
    label(ImageDraw.Draw(out), (8, 4), "map_bg_f1 + node_icons 목업 (1배, 배치는 임의 — 지나온 길 밝은 잉크, 현재 위치 = 성문 노드 링)")
    out.save(os.path.join(K.HERE, "preview_map_nodes.png"))


def tone_vs_quant():
    rows = [("keyart_waste", (180, 140, 660, 410)), ("keyart_outer", (380, 160, 860, 430)),
            ("map_f1", (180, 120, 660, 390))]
    c = Image.new("RGB", (480 * 2 + 24, 28 + 300 * len(rows)), BG)
    d = ImageDraw.Draw(c)
    label(d, (8, 4), "왼쪽 = 게임 투입본(톤 맞춤, 고해상도)   오른쪽 = 보관 비교안 alt_quant(도트화·감색)")
    for i, (aid, box) in enumerate(rows):
        out = f"{UI}/{'map_bg_f1' if aid == 'map_f1' else aid}.png"
        a = Image.open(out).convert("RGB").crop(box)
        b = Image.open(os.path.join(K.HERE, aid, "alt_quant.png")).convert("RGB").crop(box)
        y = 28 + i * 300
        c.paste(a, (8, y)); c.paste(b, (8 + 480 + 8, y))
        label(d, (14, y + 4), aid)
    c.save(os.path.join(K.HERE, "preview_tone_vs_quant.png"))


if __name__ == "__main__":
    keyart_all()
    map_nodes()
    tone_vs_quant()
    print("ok")
