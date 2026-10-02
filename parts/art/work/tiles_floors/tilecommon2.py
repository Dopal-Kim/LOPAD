#!/usr/bin/env python3
"""LOPAD 층별 타일셋 공통 모듈 **확장판** (37라운드 재작업용). `tilecommon.py` 는 손대지 않고 그 위에 얹는다.

바뀐 것 (37라운드 결정 `2026-10-02-round-37-tileset-review.md`, 계약 `art-assets.md` §2):
  * 시트 8열 x 4행 (128x64). 인덱스 표 (5~8층과 공유, 변경 금지):
      0..3   공통 바닥 4 (복도 근처·기타)      4  복도            5  벽 정면        6  벽 윗면
      7      void (투명)                      8/9/10 문 열림/닫힘/잠김               11 출구 2x2
      12     상점 2x2                          13..18 소품 6종    19..20 벽 변형 2   21..28 방 종류별 바닥
      29..31 예비 (투명)
  * JSON: tiles["2"] = [5, 19, 20] (좌표 해시 변형), props 6, roomFloors {start:[21,22], trial:[23,24], rest:[25,26], boss:[27,28]}
  * 흙바닥 공용 헬퍼 (dirt / scatter / ember / splat / bootprint / pock / ash_patch / buried_slab):
    '정돈된 타일' 이 아니라 '버려진 구역의 흙바닥' — 균일 바탕 + 정상(stationary) 랜덤 흩뿌림이라 가장자리 규칙 없이도 이어진다.
    덩어리 디테일은 1..14 안쪽에만 둬서 타일 경계에서 잘리지 않게 한다 (잘리면 격자가 보인다).
  * 미리보기: preview.png (시트) · preview_room.png (12x8 샘플 방, 소품 6, 벽 변형 섞음) · preview_rooms.png (방 종류 4 비교) · preview_seam.png

각 층 build.py: `tc2.run(stage, 이름, TILES, PROPS, 강조슬롯, HERE)`. TILES 는 ORDER2 순 29개 (name, Sprite).
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tilecommon as tc  # noqa: E402  (Ctx, G, ramp, T, checker, FONT, hexrgb, ROOT, OUT_ASSETS 재사용)
from PIL import Image, ImageDraw  # noqa: E402

G, T, ROOT, OUT_ASSETS, FONT = tc.G, tc.T, tc.ROOT, tc.OUT_ASSETS, tc.FONT
Ctx, ramp, hexrgb, checker = tc.Ctx, tc.ramp, tc.hexrgb, tc.checker

COLS, ROWS = 8, 4
PROP_N = 6
ROOM_KINDS = ["start", "trial", "rest", "boss"]
ORDER2 = (["floor_0", "floor_1", "floor_2", "floor_3", "corridor", "wall", "wall_top", "void",
           "door_open", "door_closed", "door_locked", "exit", "shop"]
          + ["prop_%d" % i for i in range(PROP_N)]          # 13..18 (층마다 실제 이름은 다름 — 접두사 prop_ 만 검사)
          + ["wall_v1", "wall_v2"]                          # 19, 20
          + ["%s_%d" % (k, i) for k in ROOM_KINDS for i in range(2)])  # 21..28
N_TILES = len(ORDER2)  # 29
assert N_TILES == 29


# ====================================================================== 흙바닥 공용 헬퍼
# 모든 헬퍼는 ctx.C 의 문자 키를 쓴다. 필수 키: K(G00) 1 2 3 4 5 6 7 (G01~G07), S B L W (강조 19/21/23/25).

def scatter(s, C, rnd, ch, n, box=(0, 0, T - 1, T - 1), avoid=None):
    """색 ch 의 점 n 개를 box 안에 균일 랜덤으로. avoid: 이미 쓴 좌표 집합(겹침 방지)."""
    x0, y0, x1, y1 = box
    placed, tries = 0, 0
    while placed < n and tries < 2000:
        tries += 1
        x, y = rnd.randint(x0, x1), rnd.randint(y0, y1)
        if avoid is not None:
            if (x, y) in avoid:
                continue
            avoid.add((x, y))
        s.px(x, y, C[ch])
        placed += 1


def dirt(ctx, seed, base="1", dots=None, pairs=None):
    """짙은 흙 바탕. base 색으로 채우고, 점(dots: {문자: 개수})과 2px 가로 쌍(pairs: {문자: 개수})을 전면에 흩뿌린다.
    균일 바탕 + 정상 노이즈 = 어떤 조합으로도 이어진다(가장자리 규칙 불필요). 격자가 보이지 않으려면 '선' 을 긋지 않는 것이 전부."""
    C = ctx.C
    s = ctx.new()
    s.rect(0, 0, T - 1, T - 1, C[base])
    rnd = random.Random(seed)
    used = set()
    for ch, n in (pairs or {}).items():
        for _ in range(n):
            x, y = rnd.randint(0, T - 2), rnd.randint(0, T - 1)
            s.px(x, y, C[ch]); s.px(x + 1, y, C[ch])
            used.add((x, y)); used.add((x + 1, y))
    for ch, n in (dots or {}).items():
        scatter(s, C, rnd, ch, n, avoid=used)
    return s, rnd


def ember(s, C, x, y, rising=True):
    """잔불 1점: 심 W, 위로 오르는 불티 L (rising), 아래 꺼져 가는 B. 3px — 어두운 바닥에서 또렷이 산다."""
    s.px(x, y, C["W"])
    if rising:
        s.px(x, y - 1, C["L"])
    else:
        s.px(x + 1, y, C["L"])
    s.px(x - 1, y + 1, C["B"])


def ember_small(s, C, x, y):
    """꺼져 가는 불씨 2px: L + B."""
    s.px(x, y, C["L"]); s.px(x + 1, y + 1, C["B"])


def splat(s, C, rnd, cx, cy, r=2, dark="S", wet=None, drops=2):
    """핏자국/술 얼룩: 중심 덩어리(dark) 반지름 r 불규칙 + 튄 방울 drops 개. wet 이면 중심 1~2px 에 밝은 색(젖음)."""
    for y in range(cy - r, cy + r + 1):
        half = r - abs(y - cy) + (1 if rnd.random() < 0.5 else 0)
        for x in range(cx - half, cx + half + 1):
            if 1 <= x <= T - 2 and 1 <= y <= T - 2 and rnd.random() < 0.85:
                s.px(x, y, C[dark])
    for _ in range(drops):
        dx, dy = rnd.choice([-1, 1]) * rnd.randint(r + 1, r + 3), rnd.choice([-1, 1]) * rnd.randint(0, r + 1)
        x, y = cx + dx, cy + dy
        if 1 <= x <= T - 2 and 1 <= y <= T - 2:
            s.px(x, y, C[dark])
    if wet:
        s.px(cx, cy, C[wet])
        if r >= 2:
            s.px(cx + 1, cy, C[wet])


def stain_small(s, C, rnd, cx, cy, dark="S", n=4, drop=True):
    """작은 얼룩: 중심 + 8방 이웃 중 n 개를 시드로 골라 불규칙 4~5px 덩어리 (r=1 splat 은 '+' 가 반복돼 보여서 대체). drop 이면 방울 1."""
    s.px(cx, cy, C[dark])
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]
    rnd.shuffle(nb)
    for dx, dy in nb[:n]:
        s.px(cx + dx, cy + dy, C[dark])
    if drop:
        s.px(cx + rnd.choice([-3, 3]), cy + rnd.choice([-2, 2]), C[dark])


def bootprint(s, C, x, y, left=True):
    """군화 자국(눌린 흙 = K 2x4 + 뒤꿈치 2x1, 빛 쪽 가장자리 G02 1px). 2x 로 짝을 이뤄 쓴다."""
    s.rect(x, y, x + 1, y + 3, C["K"])
    s.rect(x, y + 5, x + 1, y + 5, C["K"])
    s.px(x + (0 if left else 1), y - 1, C["2"])


def pock(s, C, x, y):
    """탄흔: K 2x2 구덩이, 좌상단 빛 받는 테 G03, 우하단 흙 튄 자국 G02."""
    s.rect(x, y, x + 1, y + 1, C["K"])
    s.px(x - 1, y, C["3"]); s.px(x, y - 1, C["3"])
    s.px(x + 2, y + 2, C["2"]); s.px(x + 2, y + 1, C["2"])


def ash_patch(s, C, rnd, cx, cy, r=3, ash="3", core="2", light="4"):
    """식은 재: 회색 덩어리(ash) 불규칙 원 + 가운데 어두운 숯(core) + 가장자리 밝은 재 2px."""
    for y in range(cy - r, cy + r + 1):
        half = r - abs(y - cy)
        for x in range(cx - half, cx + half + 1):
            if 1 <= x <= T - 2 and 1 <= y <= T - 2 and rnd.random() < 0.8:
                s.px(x, y, C[ash])
    s.px(cx, cy, C[core]); s.px(cx + 1, cy, C[core]); s.px(cx, cy + 1, C[core])
    s.px(cx - r + 1, cy, C[light]); s.px(cx, cy - r + 1, C[light])


def buried_slab(s, C, rnd, box, carve=(), joint="K", stone="2", lit="3", bury_from=0.55):
    """제국 포석: 흙에 반쯤 묻힌 돌판. box 안을 stone 으로 채우고 K 이음, 윗변·왼변 lit. carve: 새긴 무늬 (x,y) 목록(lit).
    bury_from(0~1) 이후 행은 흙(G01/K 점)이 덮는다 → '반쯤 묻힘'."""
    x0, y0, x1, y1 = box
    s.rect(x0, y0, x1, y1, C[stone])
    s.line(x0, y0, x1, y0, C[lit]); s.line(x0, y0, x0, y1, C[lit])
    s.line(x0, y1, x1, y1, C[joint]); s.line(x1, y0, x1, y1, C[joint])
    for x, y in carve:
        s.px(x, y, C[lit])
    by = y0 + int((y1 - y0 + 1) * bury_from)
    for y in range(by, y1 + 1):
        for x in range(x0, x1 + 1):
            if rnd.random() < 0.45 + 0.3 * (y - by) / max(1, y1 - by):
                s.px(x, y, C["1"])
    for _ in range(3):
        s.px(rnd.randint(x0, x1), rnd.randint(by, y1), C["K"])


# ====================================================================== 시트 · JSON · 미리보기
class Sheet2:
    def __init__(self, stage, name_kr, tiles, props, accent_slots, here, floor_no):
        names = [n for n, _ in tiles]
        assert len(tiles) == N_TILES, "need %d tiles, got %d" % (N_TILES, len(tiles))
        assert names[:13] == ORDER2[:13], "index 0..12 must match the shared table"
        assert all(n.startswith("prop_") for n in names[13:19]), "13..18 must be props"
        assert names[19:] == ORDER2[19:], "19..28 must be wall_v1, wall_v2, start_0.. boss_1"
        assert len(props) == PROP_N
        self.stage, self.name_kr, self.tiles, self.props = stage, name_kr, tiles, props
        self.accent_slots, self.here, self.floor_no = accent_slots, here, floor_no
        self.idx = {name: i for i, (name, _) in enumerate(tiles)}
        self.A = ramp(floor_no)

    def tile_img(self, name):
        return self.tiles[self.idx[name]][1].composite(1)

    def build_sheet(self):
        IDX = self.idx
        sheet = Image.new("RGBA", (COLS * T, ROWS * T), (0, 0, 0, 0))
        for i, (name, s) in enumerate(self.tiles):
            r, c = divmod(i, COLS)
            sheet.alpha_composite(s.composite(1), (c * T, r * T))
        sheet.save(os.path.join(OUT_ASSETS, "stage%d.png" % self.stage))
        prop_names = [n for n, _ in self.tiles[13:19]]
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
                "2": [IDX["wall"], IDX["wall_v1"], IDX["wall_v2"]],
                "3": [IDX["door_open"]],
                "4": [IDX["door_closed"]],
                "5": [IDX["door_locked"]],
                "6": [IDX["corridor"]],
                "7": [IDX["exit"]],
                "8": [IDX["shop"]],
            },
            "tileIdNames": {"0": "void", "1": "floor", "2": "wall", "3": "door_open", "4": "door_closed",
                            "5": "door_locked", "6": "corridor", "7": "exit", "8": "shop"},
            "roomFloors": {k: [IDX["%s_0" % k], IDX["%s_1" % k]] for k in ROOM_KINDS},
            "roomFloorsNote": "방 종류별 바닥 (37라운드). 키가 없거나 비면 tiles['1']. 복도 근처·기타 방은 tiles['1'].",
            "walls": {
                "top": IDX["wall"], "bottom": IDX["wall_top"], "left": IDX["wall_top"], "right": IDX["wall_top"],
                "corner_tl": IDX["wall_top"], "corner_tr": IDX["wall_top"], "corner_bl": IDX["wall_top"], "corner_br": IDX["wall_top"],
                "variants": [IDX["wall"], IDX["wall_v1"], IDX["wall_v2"]],
                "note": "top = 방 위쪽(북) 벽: 정면이 보인다 (tiles['2'] 의 세 인덱스를 좌표 해시로 섞는다). 나머지 변·모서리는 윗면. 단일 벽만 쓰면 전부 정면이어도 무방."
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

    # ------------------------------------------------------------------ previews
    def preview_sheet(self, scale=6):
        cw, gap = T * scale, 6
        W = COLS * (cw + gap) + gap
        H = ROWS * (cw + gap + 14) + gap
        img = Image.new("RGB", (W, H), (60, 60, 64))
        d = ImageDraw.Draw(img)
        for i, (name, s) in enumerate(self.tiles):
            r, c = divmod(i, COLS)
            ox, oy = gap + c * (cw + gap), gap + r * (cw + gap + 14)
            cell = checker(cw, cw).convert("RGBA")
            cell.alpha_composite(s.composite(1).resize((cw, cw), Image.NEAREST))
            img.paste(cell.convert("RGB"), (ox, oy))
            d.text((ox, oy + cw + 1), "%d %s" % (i, name), fill=(230, 230, 230), font=FONT)
        img.save(os.path.join(self.here, "preview.png"))

    def _blocks(self):
        rnd = random.Random(7)
        blocks = []
        fl = Image.new("RGBA", (T * 5, T * 4))
        for y in range(4):
            for x in range(5):
                fl.alpha_composite(self.tile_img("floor_%d" % rnd.randrange(4)), (x * T, y * T))
        blocks.append(("floor 5x4", fl))
        for k in ROOM_KINDS:
            b = Image.new("RGBA", (T * 3, T * 3))
            for y in range(3):
                for x in range(3):
                    b.alpha_composite(self.tile_img("%s_%d" % (k, rnd.randrange(2))), (x * T, y * T))
            blocks.append((k + " 3x3", b))
        w = Image.new("RGBA", (T * 5, T * 2))
        for x, nm in enumerate(["wall", "wall_v1", "wall", "wall_v2", "wall"]):
            w.alpha_composite(self.tile_img("wall_top"), (x * T, 0))
            w.alpha_composite(self.tile_img(nm), (x * T, T))
        blocks.append(("wall_top / wall+v1+v2", w))
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
        return blocks

    def preview_seam(self, scale=4):
        blocks = self._blocks()
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

    def _player_frame(self):
        pl = Image.open(os.path.join(ROOT, "assets", "sprites", "player", "player_idle.png")).convert("RGBA")
        return pl.crop((0, 0, 16, 24))

    def _place_player(self, img, tx, ty, f):
        px, py = tx * T, ty * T + T - 1 - 23 + 4
        sh = ImageDraw.Draw(img)
        sh.ellipse([px + 3, py + 21, px + 12, py + 24], fill=hexrgb(G[0]) + (255,))
        img.alpha_composite(f, (px, py))

    def _room(self, IW, IH, floor_pick, corridor=True, rnd=None):
        """벽 포함 (IW+2) x (IH+2) 방 격자. 북벽은 wall/v1/v2 해시 섞음, 나머지 wall_top. corridor 면 위 3칸 복도."""
        rnd = rnd or random.Random(3)
        GW, GH = IW + 2, IH + 2 + (3 if corridor else 0)
        OY = 3 if corridor else 0
        grid = [[None] * GW for _ in range(GH)]
        for y in range(IH + 2):
            for x in range(GW):
                gy = y + OY
                if y == 0 or y == IH + 1 or x == 0 or x == GW - 1:
                    grid[gy][x] = "wall_top"
                else:
                    grid[gy][x] = floor_pick(rnd)
        wv = ["wall", "wall", "wall_v1", "wall", "wall_v2", "wall", "wall", "wall_v1", "wall", "wall_v2", "wall", "wall"]
        for x in range(1, GW - 1):
            grid[OY][x] = wv[x % len(wv)]
        if corridor:
            for y in range(3):
                grid[y][GW // 2] = "corridor"
                grid[y][GW // 2 - 1] = "wall_top"
                grid[y][GW // 2 + 1] = "wall_top"
            grid[OY][GW // 2] = "door_open"
        return grid, OY

    def _render(self, grid, props):
        GH, GW = len(grid), len(grid[0])
        img = Image.new("RGBA", (GW * T, GH * T), (0, 0, 0, 255))
        for y in range(GH):
            for x in range(GW):
                if grid[y][x]:
                    img.alpha_composite(self.tile_img(grid[y][x]), (x * T, y * T))
        for (x, y), nm in props.items():
            img.alpha_composite(self.tile_img(nm), (x * T, y * T))
        return img

    def _accent_ratio(self, img):
        accent = set(hexrgb(c) for c in self.A)
        n = sum(1 for p_ in img.getdata() if p_[:3] in accent)
        return n, img.width * img.height

    def preview_room(self, scale=4):
        """12x8 샘플 방 + 위쪽 복도, 문 3종, 출구·상점 2x2, 소품 6종, 주인공 idle 2명. 공통 바닥 0~3."""
        rnd = random.Random(3)
        IW, IH = 12, 8
        grid, OY = self._room(IW, IH, lambda r: "floor_%d" % r.randrange(4), rnd=rnd)
        GW = IW + 2
        grid[OY + 4][0] = "door_closed"
        grid[OY + IH + 1][6] = "door_locked"
        for dy in range(2):
            for dx in range(2):
                grid[OY + 1 + dy][10 + dx] = "exit"
                grid[OY + 1 + dy][7 + dx] = "shop"
        p = [n for n, _ in self.tiles[13:19]]
        props = {(2, OY + 2): p[0], (3, OY + 2): p[0], (10, OY + 6): p[3],
                 (5, OY + 5): p[2], (8, OY + 7): p[1], (2, OY + 7): p[3],
                 (11, OY + 4): p[1], (4, OY + 8): p[4], (12, OY + 8): p[5], (7, OY + 4): p[5]}
        img = self._render(grid, props)
        f = self._player_frame()
        for (tx, ty) in [(5, OY + 4), (9, OY + 5)]:
            self._place_player(img, tx, ty, f)
        W, H = img.size
        big = img.resize((W * scale, H * scale), Image.NEAREST).convert("RGB")
        out = Image.new("RGB", (big.width + W + 24, big.height + 16), (60, 60, 64))
        out.paste(big, (8, 8))
        out.paste(img.convert("RGB"), (big.width + 16, 8))
        out.save(os.path.join(self.here, "preview_room.png"))
        n, tot = self._accent_ratio(img)
        print("accent px in sample room: %d / %d = %.2f%%" % (n, tot, 100.0 * n / tot))

    def preview_rooms(self, scale=3):
        """방 종류 4 비교: 8x6 방 네 개 (start / trial / rest / boss), 각각 소품 2 + 주인공 1. 아래 줄에 1x."""
        IW, IH = 8, 6
        p = [n for n, _ in self.tiles[13:19]]
        f = self._player_frame()
        tiles_imgs, labels, ratios = [], [], []
        for ki, k in enumerate(ROOM_KINDS):
            rnd = random.Random(11 + ki)
            grid, OY = self._room(IW, IH, lambda r, k=k: "%s_%d" % (k, r.randrange(2)), corridor=False, rnd=rnd)
            grid[OY][IW // 2] = "door_open"
            if k == "boss":
                grid[OY + IH + 1][IW // 2] = "door_locked"
            props = {(2, OY + 2): p[(ki * 2) % PROP_N], (IW - 1, OY + IH - 1): p[(ki * 2 + 1) % PROP_N]}
            img = self._render(grid, props)
            self._place_player(img, IW // 2, OY + IH // 2 + 1, f)
            tiles_imgs.append(img)
            labels.append(k)
            n, tot = self._accent_ratio(img)
            ratios.append(100.0 * n / tot)
        W, H = tiles_imgs[0].size
        gap = 12
        out = Image.new("RGB", (gap + 4 * (W * scale + gap), 20 + H * scale + gap + H + gap), (60, 60, 64))
        d = ImageDraw.Draw(out)
        x = gap
        for img, lab, r in zip(tiles_imgs, labels, ratios):
            big = img.resize((W * scale, H * scale), Image.NEAREST).convert("RGB")
            out.paste(big, (x, 20))
            out.paste(img.convert("RGB"), (x, 20 + H * scale + gap))
            d.text((x, 4), "%s  (accent %.2f%%)" % (lab, r), fill=(230, 230, 230), font=FONT)
            x += W * scale + gap
        out.save(os.path.join(self.here, "preview_rooms.png"))
        print("room kinds accent %%: " + ", ".join("%s %.2f" % (l, r) for l, r in zip(labels, ratios)))

    def stats(self):
        used = set()
        for name, s in self.tiles:
            for (r, g, b), _ in s.used_colors().items():
                used.add("#%02x%02x%02x" % (r, g, b))
            info = s.stats(print_=False)
            if info["semi_alpha_px"]:
                print("  SEMI ALPHA %s %d" % (name, info["semi_alpha_px"]))
        gray = [c for c in used if c in G]
        acc = [c for c in used if c in self.A]
        print("colors used: gray %d (budget 10), accent %d (budget 4), other %d" % (
            len(gray), len(acc), len(used) - len(gray) - len(acc)))
        print("  gray:", sorted(G.index(c) for c in gray))
        print("  accent slots:", sorted(16 + self.A.index(c) for c in acc))
        # 바닥 명도: 타일별 평균 무채 인덱스 (얼마나 '짙은가' 의 숫자 근거)
        for name, s in self.tiles:
            if name.startswith(("floor", "corridor", "start", "trial", "rest", "boss")):
                im = s.composite(1)
                tot, cnt, acc_n = 0, 0, 0
                for px in im.getdata():
                    h = "#%02x%02x%02x" % px[:3]
                    if h in G:
                        tot += G.index(h); cnt += 1
                    elif h in self.A:
                        acc_n += 1
                print("  %-10s mean gray G%.2f  accent %d px (%.1f%%)" % (name, tot / max(1, cnt), acc_n, 100.0 * acc_n / 256))

    def run(self):
        self.build_sheet()
        self.preview_sheet()
        self.preview_seam()
        self.preview_room()
        self.preview_rooms()
        self.stats()
        print("index table:", {i: n for i, (n, _) in enumerate(self.tiles)})


def run(stage, name_kr, tiles, props, accent_slots, here, floor_no=None):
    Sheet2(stage, name_kr, tiles, props, accent_slots, here, floor_no or stage).run()
