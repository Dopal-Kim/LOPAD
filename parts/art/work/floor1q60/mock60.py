"""60라운드 Q8~Q10 — 1층 5지역 조명 목업: 현행(53라운드 v2 32도트 바닥 + 적 v3) / 60라운드(64도트 바닥·담 + 적 3종 보강).

python3 parts/art/work/floor1q60/mock60.py [waste gate outer brewery hall]
- 1배 = 1920×1080 내부 렌더 기준(논리 1px = 렌더 2px). 장면 16×9칸(논리 512×288 → 렌더 1024×576) + 위쪽 Gemini 북쪽 테두리 띠 일부.
- 현행 = before/tiles(32 → 2배) + before/<적>_*.png(53라운드 격자 사본), 60 = out/tiles64_<지역>(64 → 1배) + out/<적>60_*.png.
- 조명: floors_v2 목업과 같은 값 — 주변광 0.425/0.425/0.475, 주인공 빛 #b0611a r140 · 0.75, 소품 빛(v3 소품 JSON), 테두리 빛, 발광 색 가산 + 번짐.
  합성기는 gemini/border_outer/mock.py 의 World.lit 를 import 만 — 시스템 실제 셰이더와 다를 수 있음.
산출: preview_mock_regions.png (5지역 × 전/후, 1배를 절반으로) · preview_mock_<지역>.png (전/후 1배) · preview_mock_zoom_<지역>.png (2배 확대)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(ROOT, "parts/art/work/gemini/border_outer"))
sys.path.insert(0, os.path.join(ROOT, "parts/art/work/atlas57"))
import mock as M  # noqa: E402
import gridsheet  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

R, T = 2, 32
CW, CH = 16, 9
AMB = (0.425, 0.425, 0.475)
HERO_LIGHT = ("#b0611a", 140, 0.75)
FONT = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 26)
FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 18)
EMC = {M.hx(c) for c in ["#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0", "#ffffff", "#fff4dc"]}
TOPPAD = 120
REG = ["waste", "gate", "outer", "brewery", "hall"]
NAMES = {"waste": "황무지", "gate": "성문", "outer": "외곽 거리", "brewery": "양조 구역", "hall": "연회장"}
# 장면 소품(이름, 칸 x, 칸 y)
PROPS = {
    "waste": [("campfire", 13, 2), ("crate", 14, 6), ("sacks", 13, 7), ("bones", 1, 7)],
    "gate": [("lantern", 13, 2), ("barrel", 14, 6), ("barrel", 13, 7), ("crate", 1, 7)],
    "outer": [("brazier", 13, 2), ("barrel", 14, 6), ("sacks", 13, 7), ("crate", 1, 7)],
    "brewery": [("cauldron", 13, 2), ("barrel", 14, 6), ("barrel", 13, 7), ("crate", 1, 7)],
    "hall": [("candelabra_stand", 13, 2), ("barrel", 14, 6), ("goblets", 13, 7), ("chair", 1, 7)],
}
STAIN_AT = {(3, 6): "trial", (12, 7): "trial", (10, 1): "start", (6, 8): "rest"}
WALL = (2, 1, 4)
CORRIDOR_ROW = 8


class World(M.World):
    def __init__(self):
        self.bj = None
        self.x0, self.y0 = 0, -TOPPAD
        self.x1, self.y1 = CW * T, CH * T
        self.W, self.H = int((self.x1 - self.x0) * R), int((self.y1 - self.y0) * R)
        self.alb = Image.new("RGBA", (self.W, self.H), (14, 15, 20, 255))
        self.emi = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 255))
        self.lights = []


def grid_frame(png, js, row, col):
    j = json.load(open(js))
    im = Image.open(png).convert("RGBA")
    fw, fh = j["frameWidth"], j["frameHeight"]
    return im.crop((col * fw, row * fh, col * fw + fw, row * fh + fh)), j


def tileset(rid, kind):
    if kind == "before":
        p = os.path.join(HERE, "before/tiles", f"stage1_{rid}")
    else:
        p = os.path.join(HERE, "out", f"tiles64_{rid}")
    sh = Image.open(p + ".png").convert("RGBA")
    meta = json.load(open(p + ".json", encoding="utf-8"))
    ts, cols = meta["tileWidth"], meta["columns"]
    k = R * T // ts

    def cell(i):
        c = sh.crop(((i % cols) * ts, (i // cols) * ts, (i % cols) * ts + ts, (i // cols) * ts + ts))
        return c.resize((c.width * k, c.height * k), Image.NEAREST)
    return meta, cell


def north_band(bdir, nb):
    """북쪽 띠 이미지(반복 단위) — x 반복 띠는 image, 'sides' 는 왼쪽 반복 조각, 나뉜 띠는 첫 조각."""
    if nb.get("repeat") == "sides":
        s = nb["sides"]["left"]
        return Image.open(os.path.join(bdir, s["image"])).convert("RGBA"), Image.open(os.path.join(bdir, s["emissive"])).convert("RGBA")
    if "pieces" in nb:
        pc = nb["pieces"][0]
        return Image.open(os.path.join(bdir, pc["image"])).convert("RGBA"), Image.open(os.path.join(bdir, pc["emissive"])).convert("RGBA")
    return Image.open(os.path.join(bdir, nb["image"])).convert("RGBA"), Image.open(os.path.join(bdir, nb["emissive"])).convert("RGBA")


def enemy(kind, eid, act, row, col):
    if kind == "before":
        return grid_frame(os.path.join(HERE, "before", f"{eid}_{act}.png"), os.path.join(HERE, "before", f"{eid}_{act}.json"), row, col)
    return grid_frame(os.path.join(HERE, "out", f"{eid}60_{act}.png"), os.path.join(HERE, "out", f"{eid}60_{act}.json"), row, col)


def build(rid, kind):
    w = World()
    meta, cell = tileset(rid, kind)
    fl = meta["tiles"]["1"]
    rf = meta["roomFloors"]
    for ty in range(CH):
        for tx in range(CW):
            if (tx, ty) in STAIN_AT:
                i = rf[STAIN_AT[(tx, ty)]][M.h2(tx, ty, 4)]
            elif ty == CORRIDOR_ROW and 4 <= tx <= 11:
                i = 4
            else:
                i = fl[M.h2(tx + 3, ty * 7 + 1, len(fl))]
            w.put(cell(i), tx * T, ty * T, occlude=False)
    bdir = os.path.join(ROOT, "assets/tiles/border", rid)
    bj = json.load(open(os.path.join(bdir, "border.json"), encoding="utf-8"))
    nb = bj["bands"]["north"]
    band, bem = north_band(bdir, nb)
    by0 = int((nb["baselineY"] - TOPPAD) * R)
    hgt = int((TOPPAD + nb.get("apronBelow", 0)) * R)
    x = 0
    while x < w.W:
        cw = min(band.width, w.W - x)
        w.put(band.crop((0, by0, cw, by0 + hgt)), x / R, -TOPPAD, bem.crop((0, by0, cw, by0 + hgt)), occlude=True)
        x += band.width
    for L in nb.get("lights", []) + (nb.get("sides", {}).get("left", {}).get("lights", []) if nb.get("repeat") == "sides" else []):
        if 0 <= L["x"] <= CW * T:
            w.light(L["x"], L["y"] - nb["baselineY"], L["color"], L["radius"], L["intensity"])
    c0, r0, n = WALL
    ss = meta["walls"]["stoneSet"]
    for i in range(n):
        w.put(cell(ss["top"]), (c0 + i) * T, r0 * T, occlude=True)
        w.put(cell(ss["upper"][0]), (c0 + i) * T, (r0 + 1) * T, occlude=True)
        w.put(cell(ss["lower"][-1] if i == 2 else ss["lower"][0]), (c0 + i) * T, (r0 + 2) * T, occlude=True)
    sh = Image.new("RGBA", (n * T * R, 10 * R), (6, 7, 10, 120))
    w.put(sh, c0 * T, (r0 + 3) * T, occlude=False)
    pp = os.path.join(ROOT, f"assets/tiles/v3/stage1_{rid}_props")
    psh = Image.open(pp + ".png").convert("RGBA")
    pj = json.load(open(pp + ".json", encoding="utf-8"))
    table = {e["name"]: e for e in pj["props"] + pj["bigProps"]}
    items = []
    for (name, tx, ty) in PROPS[rid]:
        e = table[name]
        r = e["rect"]
        im = psh.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]))
        px_, py_ = tx * T + 16, ty * T + 30
        x0, y0 = px_ - e["pivot"]["x"] / 2, py_ - e["pivot"]["y"] / 2
        lights = []
        for L in ([e["light"]] if e.get("light") else []) + e.get("lights", []):
            lights.append((x0 + L["offset"]["x"] / 2, y0 + L["offset"]["y"] / 2, L["color"], L["radius"] / 2, L["intensity"]))
        items.append((py_ if e.get("depth") != "floor" else -1, x0, y0, im, M.emissive_of(im, EMC), lights, None))
    meta_h = gridsheet.load_meta(os.path.join(ROOT, "assets/sprites/player/v3/player_idle.json"))
    hg = gridsheet.open_grid(os.path.join(ROOT, "assets/sprites/player/v3/player_idle.json"))
    hero = hg.crop((0, 0, meta_h["frameWidth"], meta_h["frameHeight"]))
    hx, hy = 8 * T + 16, 5 * T + 10
    items.append((hy, hx - meta_h["pivot"]["x"] / 2, hy - meta_h["pivot"]["y"] / 2, hero, M.emissive_of(hero, EMC | {(226, 163, 60)}),
                  [(hx - 10, hy - 40, *HERO_LIGHT)], (hx, hy, 34)))
    # 징집병 대기(오른쪽 보기) · 사수 발사(왼쪽 보기, 새 = fire 3 / 구 = 2) · 결사병 예고(아래 보기, 새 2 / 구 2)
    fire = 3 if kind != "before" else 2
    cast = [(enemy(kind, "dummy", "idle", 3, 0), 5 * T + 4, 6 * T + 22),
            (enemy(kind, "archer", "attack", 2, fire), 11 * T + 14, 4 * T + 26),
            (enemy(kind, "charger", "attack", 0, 2), 9 * T + 30, 7 * T + 26)]
    for (im, j), ex, ey in cast:
        items.append((ey, ex - j["pivot"]["x"] / 2, ey - j["pivot"]["y"] / 2, im, M.emissive_of(im, EMC), [],
                      (ex, ey, int(j["frameWidth"] * 0.5 * 0.7))))
    items.sort(key=lambda t: t[0])
    for (sy, x0, y0, im, em, lights, shadow) in items:
        if shadow:
            sx, sy_, ww = shadow
            s = Image.new("RGBA", (ww * 2, 16), (0, 0, 0, 0))
            ImageDraw.Draw(s).ellipse((0, 0, ww * 2 - 1, 15), fill=(8, 9, 14, 165))
            w.put(s, sx - ww / 2, sy_ - 4, occlude=False)
        w.put(im, x0, y0, em, occlude=True)
        for L in lights:
            w.light(*L)
    return M.vignette(w.lit(AMB), 0.35)


def main(regs):
    pairs = {}
    for rid in regs:
        b, a = build(rid, "before"), build(rid, "after")
        pairs[rid] = (b, a)
        pw, ph = b.size
        out = Image.new("RGB", (pw * 2 + 12, ph + 44), (12, 12, 16))
        d = ImageDraw.Draw(out)
        out.paste(b, (0, 44))
        out.paste(a, (pw + 12, 44))
        d.text((8, 8), f"{NAMES[rid]} — 현행(53라운드 32도트 바닥 · 적 v3)", fill=(235, 225, 200), font=FONT)
        d.text((pw + 20, 8), f"{NAMES[rid]} — 60라운드(64도트 바닥·담 · 적 3종 보강)", fill=(235, 225, 200), font=FONT)
        out.save(os.path.join(HERE, f"preview_mock_{rid}.png"))
        box = (int(4.0 * T * R), int((TOPPAD + 3.0 * T) * R), int(13.0 * T * R), int((TOPPAD + 8.6 * T) * R))
        zb, za = b.crop(box), a.crop(box)
        zw, zh = zb.size
        z = Image.new("RGB", (zw * 2, zh * 4 + 88), (12, 12, 16))
        dz = ImageDraw.Draw(z)
        z.paste(zb.resize((zw * 2, zh * 2), Image.NEAREST), (0, 40))
        z.paste(za.resize((zw * 2, zh * 2), Image.NEAREST), (0, zh * 2 + 84))
        dz.text((8, 8), f"{NAMES[rid]} 현행 — 2배", fill=(235, 225, 200), font=FONT_S)
        dz.text((8, zh * 2 + 52), f"{NAMES[rid]} 60라운드 — 2배", fill=(235, 225, 200), font=FONT_S)
        z.save(os.path.join(HERE, f"preview_mock_zoom_{rid}.png"))
        print("mock", rid, out.size, z.size)
    if len(regs) == len(REG):
        pw, ph = pairs[REG[0]][0].size
        hw, hh = pw // 2, ph // 2
        out = Image.new("RGB", (hw * 2 + 12, (hh + 36) * len(REG)), (12, 12, 16))
        d = ImageDraw.Draw(out)
        for i, rid in enumerate(REG):
            b, a = pairs[rid]
            y = i * (hh + 36)
            out.paste(b.resize((hw, hh), Image.LANCZOS), (0, y + 32))
            out.paste(a.resize((hw, hh), Image.LANCZOS), (hw + 12, y + 32))
            d.text((6, y + 6), f"{NAMES[rid]} 현행", fill=(235, 225, 200), font=FONT_S)
            d.text((hw + 18, y + 6), f"{NAMES[rid]} 60라운드", fill=(235, 225, 200), font=FONT_S)
        out.save(os.path.join(HERE, "preview_mock_regions.png"))
        print("regions", out.size)


if __name__ == "__main__":
    main(sys.argv[1:] or REG)
