#!/usr/bin/env python3
"""53라운드 Q6 — 1층 5지역 테두리 목업 (1920×1080 = 논리 960×540 × 2).

python3 parts/art/work/gemini/border_mock.py [region ...]     # 기본 5지역 전부 + 모음 그림

- 전투장 32×20칸(Q7), 주변광 중립 숯빛 0.34/0.34/0.38(Q9), 카메라 북쪽 치우침 110(Q8).
- 바닥: 외곽 = v2 도트(32px), 나머지 4지역 = v2 바닥이 아직 없어 구판 지역 바닥(16px)을 2배로 키워 명도만 v2 에 맞춘 근사(테두리 검수용).
- 테두리·골목 조각은 assets/tiles/border/<id>/border.json 의 place·doors 규칙만으로 쌓는다(시스템 구현 모름, 교차 참조 없음).
- 조명·발광·비네팅은 border_outer/mock.py 의 World·view 를 그대로 쓴다.
산출: preview_border_<id>.png (목업), preview_border_<id>_vs_keyart.png (키아트·목업·전체 조감), preview_borders_f1.png (5지역 모음)
"""
import json, os, sys
from PIL import Image, ImageDraw

GEM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(GEM, "border_outer"))
import mock as M  # noqa: E402  (World, view, frame, up, emissive_of, label, h2)
import border_kit as BK  # noqa: E402

ROOT = M.ROOT
R, T = 2, 32
FW, FH = 32, 20                      # Q7
AMB = (0.34, 0.34, 0.38)             # Q9
LOOKUP = 110                         # Q8
SPR = os.path.join(ROOT, "assets/sprites")
REGIONS = ["outer", "waste", "gate", "brewery", "hall"]
NAMES = {"outer": "외곽 거리", "waste": "황무지", "gate": "성문", "brewery": "양조 구역", "hall": "연회장(보스)"}
KEYART = {"outer": "keyart_outer/raw_a.jpg", "waste": "keyart_waste/raw_a.jpg", "gate": "keyart_gate/raw_a.jpg",
          "brewery": "keyart_brewery/raw_b.jpg", "hall": "keyart_hall/raw_b.jpg"}
# 문 자리(칸): north = 바닥 위 끝 칸 x 범위, west = 바닥 왼쪽 끝 칸 y 범위, south = 아래 끝 칸 x 범위
DOORS = {
    "outer": {"north": (8, 11), "west": (9, 12), "south": (22, 25)},
    "waste": {"north": (8, 11), "west": (9, 12), "south": (22, 25)},
    "gate": {"north": (6, 9), "west": (9, 12), "south": (14, 18)},
    "brewery": {"north": (8, 11), "west": (9, 12), "south": (22, 25)},
    "hall": {"west": (9, 12), "south": (14, 18)},
}
CAM = {"outer": 400, "waste": 400, "gate": 430, "brewery": 400, "hall": 512}   # 목업 카메라 중심 x(논리)


class World(M.World):
    def __init__(self, bj):
        b = bj["bands"]
        self.bj = bj
        self.x0 = -b["west"]["width"]
        self.y0 = -b["north"]["baselineY"]
        self.x1 = FW * T + b["east"]["width"]
        self.y1 = FH * T - b["south"]["baselineY"] + b["south"]["height"]
        self.W = int((self.x1 - self.x0) * R)
        self.H = int((self.y1 - self.y0) * R)
        self.alb = Image.new("RGBA", (self.W, self.H), (14, 15, 20, 255))
        self.emi = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 255))
        self.lights = []


def floor_tiles(rid):
    """(타일 함수, 소품 목록) — 렌더 해상도 64px."""
    if rid == "outer":
        meta, cell, big, emc = M.load_tiles()
        cache = {}

        def tile(i):
            if i not in cache:
                cache[i] = M.up(cell(i))
            return cache[i]
        return (lambda tx, ty: tile([0, 1, 2, 3][M.h2(tx, ty, 4)] if M.h2(tx + 7, ty + 3, 100) >= 2 else [27, 28, 35, 36][M.h2(tx, ty, 4)]),
                [tile(i) for i in (13, 14, 18, 19)])
    base = os.path.join(ROOT, f"assets/tiles/stage1_{rid}")
    sheet = Image.open(base + ".png").convert("RGBA")
    meta = json.load(open(base + ".json", encoding="utf-8"))
    cols, ts = meta["columns"], meta["tileWidth"]

    def cell(i):
        return sheet.crop(((i % cols) * ts, (i // cols) * ts, (i % cols) * ts + ts, (i // cols) * ts + ts))
    fl = [cell(i) for i in meta["tiles"]["1"]]
    TONE = BK.make_luts("wall")[0]     # 2회차 비평: 구판 바닥 채도가 떠 보임 → 테두리와 같은 톤 사영(무채 ↔ 1층 램프)
    # 명도 맞춤: v2 바닥 알베도 평균 루마 ≈ 64
    acc = n = 0
    for c in fl:
        for p in c.convert("RGB").get_flattened_data():
            acc += 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]
            n += 1
    k = 64 / max(1, acc / n)
    fl = [c.convert("RGB").point(lambda v: min(255, int(v * k))).filter(TONE).convert("RGBA").resize((T * R, T * R), Image.NEAREST) for c in fl]
    props = [cell(p["index"]).resize((T * R, T * R), Image.NEAREST) for p in meta["props"][:6]]
    return (lambda tx, ty: fl[M.h2(tx, ty, len(fl))]), props


def edge_shadow(world):
    """벽 발치 그늘(북·서·동) — 시스템 floorShadows 근사."""
    for (x, y, w, h, d) in ((0, 0, FW * T, 28, "n"), (0, 0, 22, FH * T, "w"), (FW * T - 22, 0, 22, FH * T, "e")):
        g = Image.new("RGBA", (w * R, h * R), (0, 0, 0, 0))
        p = g.load()
        for yy in range(h * R):
            for xx in range(w * R):
                t = {"n": yy / (h * R), "w": xx / (w * R), "e": 1 - xx / (w * R)}[d]
                p[xx, yy] = (6, 7, 10, int(150 * (1 - t) ** 1.5))
        world.put(g, x, y, occlude=False)


def place_band(world, bdir, name, b, phase_x=None):
    img = Image.open(os.path.join(bdir, b["image"])).convert("RGBA")
    em = Image.open(os.path.join(bdir, b["emissive"])).convert("RGBA")
    W, H = b["width"], b["height"]
    if name in ("north", "south"):
        y = -b["baselineY"] if name == "north" else FH * T - b["baselineY"]
        x = world.x0 if phase_x is None else phase_x
        while x > world.x0:
            x -= W
        while x < world.x1:
            world.put(img, x, y, em, occlude=True)
            for L in b["lights"]:
                world.light(x + L["x"], y + L["y"], L["color"], L["radius"], L["intensity"])
            x += W
    else:
        x = world.x0 if name == "west" else FW * T
        y = world.y0 - 120
        while y < world.y1:
            world.put(img, x, y, em, occlude=True)
            for L in b["lights"]:
                ly = y + L["y"]
                if 0 <= ly <= FH * T:
                    world.light(x + L["x"], ly, L["color"], L["radius"], L["intensity"])
            y += H


def place_door(world, bdir, side, d, cells):
    img = Image.open(os.path.join(bdir, d["file"])).convert("RGBA")
    em = Image.open(os.path.join(bdir, d["emissive"])).convert("RGBA")
    a, b = cells
    if side == "north":
        x, y = (a + b) / 2 * T - d["openingX"], -d["baselineY"]
    elif side == "south":
        x, y = (a + b) / 2 * T - d["openingX"], FH * T - d["baselineY"]
    elif side == "west":
        x, y = -d["w"], (a + b) / 2 * T - d["openingY"]
    else:
        x, y = FW * T, (a + b) / 2 * T - d["openingY"]
    world.put(img, x, y, em, occlude=True)
    for L in d.get("lights", []):
        world.light(x + L["x"], y + L["y"], L["color"], L["radius"], L["intensity"])


def build(rid):
    bdir = os.path.join(ROOT, "assets/tiles/border", rid)
    bj = json.load(open(os.path.join(bdir, "border.json"), encoding="utf-8"))
    world = World(bj)
    tile, props = floor_tiles(rid)
    for ty in range(FH):
        for tx in range(FW):
            world.put(tile(tx, ty), tx * T, ty * T, occlude=False)
    edge_shadow(world)
    b = bj["bands"]
    focus = b["north"].get("focusX")
    phase = (FW * T / 2 - focus) if focus is not None else None
    for n in ("west", "east"):
        place_band(world, bdir, n, b[n])
    place_band(world, bdir, "north", b["north"], phase)
    doors = bj.get("doors", {})
    dc = DOORS[rid]
    for side in ("west", "east", "north"):
        key = "west" if side == "east" else side
        if side in doors and key in dc:
            cells = dc[key]
            place_door(world, bdir, side, doors[side], cells)
    # Y 정렬: 소품 몇 개 + 주인공 + 적
    items = []
    for k, (tx, ty) in enumerate(((5, 5), (13, 9), (24, 6), (27, 14), (9, 16), (19, 17))):
        im = props[k % len(props)]
        items.append(((ty + 1) * T - 2, tx * T + 16, im, (T, T * R - 4), None, False, None))
    hero, hj = M.frame(os.path.join(SPR, "player/v3/player_idle"), 0, 0)
    hs = 1.5 if hj["frameWidth"] == 64 else 1.0
    hero = M.up(hero, hs)
    hp = (int(hj["pivot"]["x"] * hs), int(hj["pivot"]["y"] * hs))
    hx = CAM[rid]
    hy = 2 * T + 30 if rid != "hall" else T + 14     # 연회장: 보스 시작(왕좌 앞) 근처 — 화로 역광이 화면에 들어오는 자리
    items.append((hy, hx, hero, hp, None, True, ({"color": "#b0611a", "radius": 90, "intensity": 0.55}, hx - 16, hy - 50)))

    def ch(path, row, col):
        im, j = M.frame(os.path.join(SPR, path), row, col)
        r = M.up(im, R * j.get("pixelScale", 1))
        return r, (int(j["pivot"]["x"] * r.width / im.width), int(j["pivot"]["y"] * r.height / im.height))
    for (path, row, col, x, y) in (("enemies/v2/charger_walk", 2, 2, hx + 150, 3 * T + 20),
                                   ("enemies/v2/charger_attack", 3, 1, hx - 170, 4 * T + 10),
                                   ("enemies/v2/charger_idle", 1, 0, hx + 60, 11 * T)):
        im, piv = ch(path, row, col)
        items.append((y, x, im, piv, None, True, None))
    emc = M.load_tiles()[3]           # v2 발광색(주인공 눈빛·혼불 등)
    items.sort(key=lambda t: t[0])
    for (fy, fx, im, piv, em, shadow, L) in items:
        if shadow:
            sw = int(im.width * 0.5)
            sh = Image.new("RGBA", (sw, 18), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse((0, 0, sw - 1, 17), fill=(10, 12, 18, 130))
            world.put(sh, fx - sw / (2 * R), fy - 5, occlude=False)
        world.put(im, fx - piv[0] / R, fy - piv[1] / R, M.emissive_of(im, emc) if em is None else em, occlude=True)
        if L:
            l, ox, oy = L
            world.light(ox, oy, l["color"], l["radius"], l["intensity"])
    place_band(world, bdir, "south", b["south"], phase)
    if "south" in doors and "south" in dc:
        place_door(world, bdir, "south", doors["south"], dc["south"])
    return world, hx, hy


def run(rid):
    world, hx, hy = build(rid)
    lit = world.lit(AMB)
    cx, cy = CAM[rid], hy - LOOKUP
    cy = max(cy, -world.bj["bands"]["north"]["baselineY"] + 270)     # camera.bounds.top (2회차 비평: 띠 위끝 너머 검은 줄)
    v = M.view(world, lit, cx, cy)
    v.save(os.path.join(GEM, f"preview_border_{rid}.png"))
    # 전체 조감(논리 1배)
    ov = lit.resize((world.W // 2, world.H // 2), Image.LANCZOS)
    d = ImageDraw.Draw(ov)
    x0, y0 = cx - 480 - world.x0, cy - 270 - world.y0
    d.rectangle((x0, y0, x0 + 960, y0 + 540), outline=(232, 184, 88), width=3)
    fx0, fy0 = -world.x0, -world.y0
    d.rectangle((fx0, fy0, fx0 + FW * T, fy0 + FH * T), outline=(120, 160, 200), width=2)
    M.label(ov, "바닥 32×20칸(파랑) · 목업 카메라(노랑)", (fx0 + 8, fy0 + FH * T - 36))
    # 키아트 비교: 위 = 키아트 | 목업, 아래 = 조감
    ka = Image.open(os.path.join(GEM, KEYART[rid])).convert("RGB").resize((1920, 1072), Image.LANCZOS)
    ovs = ov.resize((int(ov.width * 1080 / ov.height), 1080), Image.LANCZOS) if ov.height > 1080 else ov
    W = 1920 * 2 + 24
    cmp_ = Image.new("RGB", (W, 1080 * 2 + 24 + 60), (12, 12, 16))
    cmp_.paste(ka, (0, 60))
    cmp_.paste(v, (1944, 60))
    cmp_.paste(ovs, ((W - ovs.width) // 2, 1080 + 84))
    small = cmp_.resize((cmp_.width // 2, cmp_.height // 2), Image.LANCZOS)
    M.label(small, f"keyart_{rid} 원본", (8, 4))
    M.label(small, f"목업: {NAMES[rid]} 북쪽 (32×20칸 · 중립 주변광 · 위로 110)", (980, 4))
    M.label(small, "전체 조감(논리 1배) — 골목 입구 조각 포함", (8, 556))
    small.save(os.path.join(GEM, f"preview_border_{rid}_vs_keyart.png"))
    print("mock", rid)
    return v


def collage():
    rows = []
    for rid in REGIONS:
        ka = Image.open(os.path.join(GEM, KEYART[rid])).convert("RGB").resize((960, 536), Image.LANCZOS)
        mk = Image.open(os.path.join(GEM, f"preview_border_{rid}.png")).convert("RGB").resize((960, 540), Image.LANCZOS)
        rows.append((rid, ka, mk))
    out = Image.new("RGB", (960 * 2 + 12, len(rows) * (540 + 40)), (12, 12, 16))
    for i, (rid, ka, mk) in enumerate(rows):
        y = i * 580 + 40
        out.paste(ka, (0, y))
        out.paste(mk, (972, y))
        M.label(out, f"{NAMES[rid]} — 키아트 | 목업(테두리 + 골목 입구 조각)", (8, y - 34))
    out.save(os.path.join(GEM, "preview_borders_f1.png"))
    print("collage")


if __name__ == "__main__":
    regs = sys.argv[1:] or REGIONS
    for r in regs:
        run(r)
    if not sys.argv[1:]:
        collage()
