#!/usr/bin/env python3
# [53라운드 보관] 이 스크립트가 미리보기·목업·마스크 입력으로 읽던 구 시트(assets/sprites/player/player_*, player/v2/*, enemies/{dummy,archer,charger}_*, enemies/v2/*, weapons/katana_* 중 아이콘 외, weapons/v2/*)는 삭제됨 — 해당 단계는 재실행 시 FileNotFoundError.
"""LOPAD 층별 타일셋 공통 모듈 (2층 이후). 1층 `tiles_stage1/build.py` 의 시트 조립·JSON·미리보기 부분을
그대로 떼어 낸 것 — 시트 레이아웃(8열×3행, 16×16)과 인덱스 표(0~16)는 1층과 동일하게 고정한다.

각 층 build.py 가 하는 일: 팔레트 C 를 정하고 17개 Sprite 를 그린 뒤 `run(...)` 을 부른다.

인덱스 표 (1층과 동일, 변경 금지)
  0..3  바닥 변형 4            4 복도              5 벽 정면           6 벽 윗면
  7     void (완전 투명)       8 문 열림           9 문 닫힘           10 문 잠김(보스)
  11    출구 계단(2x2)         12 상점(2x2)        13..16 소품 4종     17..23 예비(투명)
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

T = 16
COLS, ROWS = 8, 3
ORDER = ["floor_0", "floor_1", "floor_2", "floor_3", "corridor", "wall", "wall_top", "void",
         "door_open", "door_closed", "door_locked", "exit", "shop"]  # + 소품 4 (층마다 이름 다름)

FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)


def ramp(floor_no):
    return PAL["floors"][floor_no - 1]["ramp"]


def hexrgb(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


class Ctx:
    """팔레트 문자 → 색 사전 C 와 Sprite 생성기."""

    def __init__(self, C):
        self.C = C
        self.palette = list(dict.fromkeys(C.values()))

    def new(self):
        return Sprite(T, T, palette=self.palette)

    def blit(self, s, rows, ox=0, oy=0):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == ".":
                    continue
                x, y = ox + i, oy + j
                if 0 <= x < T and 0 <= y < T:
                    s.px(x, y, self.C[ch])


def checker(w, h, sq=8):
    bg = Image.new("RGB", (w, h), (232, 232, 232))
    d = ImageDraw.Draw(bg)
    for y in range(0, h, sq):
        for x in range(0, w, sq):
            if (x // sq + y // sq) % 2:
                d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=(203, 203, 203))
    return bg


class Sheet:
    def __init__(self, stage, name_kr, tiles, props, accent_slots, here, floor_no):
        """tiles: [(name, Sprite)] 17개, ORDER 순 + 소품 4. props: [(name, solid)] 소품 4개 순서대로."""
        assert [n for n, _ in tiles[:13]] == ORDER, "index table must match stage1"
        assert len(tiles) == 17
        self.stage, self.name_kr, self.tiles, self.props = stage, name_kr, tiles, props
        self.accent_slots, self.here, self.floor_no = accent_slots, here, floor_no
        self.idx = {name: i for i, (name, _) in enumerate(tiles)}
        self.A = ramp(floor_no)

    def tile_img(self, name):
        return self.tiles[self.idx[name]][1].composite(1)

    # ---------------------------------------------------------------- sheet + json
    def build_sheet(self):
        IDX = self.idx
        sheet = Image.new("RGBA", (COLS * T, ROWS * T), (0, 0, 0, 0))
        for i, (name, s) in enumerate(self.tiles):
            r, c = divmod(i, COLS)
            sheet.alpha_composite(s.composite(1), (c * T, r * T))
        sheet.save(os.path.join(OUT_ASSETS, "stage%d.png" % self.stage))
        prop_names = [n for n, _ in self.tiles[13:]]
        meta = {
            "image": "stage%d.png" % self.stage,
            "stage": self.stage,
            "name": self.name_kr,
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
                "note": "top = 방 위쪽(북) 벽: 정면이 보인다. 나머지 변·모서리는 윗면. 단일 벽만 쓰면 전부 정면이어도 무방."
            },
            "props": [
                {"index": IDX[pn], "name": short, "solid": solid}
                for pn, (short, solid) in zip(prop_names, self.props)
            ],
            "propsLayer": "overlay — 소품 타일은 배경이 투명하므로 바닥 레이어 위에 겹쳐 그린다",
            "names": {str(i): name for i, (name, _) in enumerate(self.tiles)},
            "palette": "parts/art/palette/lopad.json (gray + floor %d accent slots %s)" % (
                self.floor_no, ", ".join(str(a) for a in self.accent_slots)),
        }
        with open(os.path.join(OUT_ASSETS, "stage%d.json" % self.stage), "w", encoding="utf-8") as fp:
            json.dump(meta, fp, ensure_ascii=False, indent=1)
        return sheet, meta

    # ---------------------------------------------------------------- previews
    def preview_sheet(self, scale=6):
        cw = T * scale
        gap = 6
        W = COLS * (cw + gap) + gap
        H = ROWS * (cw + gap + 14) + gap
        img = Image.new("RGB", (W, H), (60, 60, 64))
        d = ImageDraw.Draw(img)
        for i, (name, s) in enumerate(self.tiles):
            r, c = divmod(i, COLS)
            ox = gap + c * (cw + gap)
            oy = gap + r * (cw + gap + 14)
            cell = checker(cw, cw).convert("RGBA")
            cell.alpha_composite(s.composite(1).resize((cw, cw), Image.NEAREST))
            img.paste(cell.convert("RGB"), (ox, oy))
            d.text((ox, oy + cw + 1), "%d %s" % (i, name), fill=(230, 230, 230), font=FONT)
        img.save(os.path.join(self.here, "preview.png"))

    def preview_seam(self, scale=4):
        import random
        rnd = random.Random(7)
        blocks = []
        fl = Image.new("RGBA", (T * 4, T * 4))
        for y in range(4):
            for x in range(4):
                fl.alpha_composite(self.tile_img("floor_%d" % rnd.randrange(4)), (x * T, y * T))
        blocks.append(("floor 4x4", fl))
        w = Image.new("RGBA", (T * 4, T * 2))
        for x in range(4):
            w.alpha_composite(self.tile_img("wall_top"), (x * T, 0))
            w.alpha_composite(self.tile_img("wall"), (x * T, T))
        blocks.append(("wall_top / wall", w))
        for nm in ("exit", "shop"):
            b = Image.new("RGBA", (T * 2, T * 2))
            for y in range(2):
                for x in range(2):
                    b.alpha_composite(self.tile_img(nm), (x * T, y * T))
            blocks.append((nm + " 2x2", b))
        c = Image.new("RGBA", (T * 3, T))
        for x in range(3):
            c.alpha_composite(self.tile_img("corridor"), (x * T, 0))
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
        img.save(os.path.join(self.here, "preview_seam.png"))

    def preview_room(self, scale=4):
        """1층과 같은 12x8 샘플 방 + 위쪽 복도, 문 3종, 출구·상점 2x2, 소품 4종, 주인공 idle down."""
        import random
        rnd = random.Random(3)
        IW, IH = 12, 8
        GW, GH = IW + 2, IH + 2 + 3
        grid = [[None] * GW for _ in range(GH)]
        OY = 3
        for y in range(IH + 2):
            for x in range(GW):
                gy = y + OY
                if y == 0 or y == IH + 1 or x == 0 or x == GW - 1:
                    grid[gy][x] = "wall_top"
                else:
                    grid[gy][x] = "floor_%d" % rnd.randrange(4)
        for x in range(1, GW - 1):
            grid[OY][x] = "wall"
        grid[OY][7] = "door_open"
        grid[OY + 4][0] = "door_closed"
        grid[OY + IH + 1][6] = "door_locked"
        for y in range(3):
            grid[y][7] = "corridor"
            grid[y][6] = "wall_top"
            grid[y][8] = "wall_top"
        for dy in range(2):
            for dx in range(2):
                grid[OY + 1 + dy][10 + dx] = "exit"
                grid[OY + 1 + dy][7 + dx] = "shop"
        p = [n for n, _ in self.tiles[13:]]
        props = {(2, OY + 2): p[0], (3, OY + 2): p[0], (10, OY + 6): p[3],
                 (5, OY + 5): p[2], (8, OY + 7): p[1], (2, OY + 7): p[3],
                 (11, OY + 4): p[1]}
        W, H = GW * T, GH * T
        img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        for y in range(GH):
            for x in range(GW):
                nm = grid[y][x]
                if nm:
                    img.alpha_composite(self.tile_img(nm), (x * T, y * T))
        for (x, y), nm in props.items():
            img.alpha_composite(self.tile_img(nm), (x * T, y * T))
        pl = Image.open(os.path.join(ROOT, "assets", "sprites", "player", "player_idle.png")).convert("RGBA")
        f = pl.crop((0, 0, 16, 24))
        for (tx, ty) in [(5, OY + 4), (9, OY + 5)]:
            px, py = tx * T, ty * T + T - 1 - 23 + 4
            sh = ImageDraw.Draw(img)
            sh.ellipse([px + 3, py + 21, px + 12, py + 24], fill=hexrgb(G[1]) + (255,))
            img.alpha_composite(f, (px, py))
        big = img.resize((W * scale, H * scale), Image.NEAREST).convert("RGB")
        out = Image.new("RGB", (big.width + W + 24, big.height + 16), (60, 60, 64))
        out.paste(big, (8, 8))
        out.paste(img.convert("RGB"), (big.width + 16, 8))
        out.save(os.path.join(self.here, "preview_room.png"))
        accent = set(hexrgb(c) for c in self.A)
        n = sum(1 for p_ in img.getdata() if p_[:3] in accent)
        print("accent px in sample room: %d / %d = %.2f%%" % (n, W * H, 100.0 * n / (W * H)))

    def stats(self):
        used = set()
        for name, s in self.tiles:
            for (r, g, b), _ in s.used_colors().items():
                used.add("#%02x%02x%02x" % (r, g, b))
            info = s.stats(print_=False)
            iso = info["isolated_px"]
            if iso and name != "void":
                print("  isolated %-14s %s" % (name, iso))
            if info["semi_alpha_px"]:
                print("  SEMI ALPHA %s %d" % (name, info["semi_alpha_px"]))
        gray = [c for c in used if c in G]
        acc = [c for c in used if c in self.A]
        print("colors used: gray %d (budget 10), accent %d (budget 4), other %d" % (
            len(gray), len(acc), len(used) - len(gray) - len(acc)))
        print("  gray:", sorted(G.index(c) for c in gray))
        print("  accent slots:", sorted(16 + self.A.index(c) for c in acc))

    def run(self):
        self.build_sheet()
        self.preview_sheet()
        self.preview_seam()
        self.preview_room()
        self.stats()
        print("index table:", {i: n for i, (n, _) in enumerate(self.tiles)})


def run(stage, name_kr, tiles, props, accent_slots, here, floor_no=None):
    Sheet(stage, name_kr, tiles, props, accent_slots, here, floor_no or stage).run()
