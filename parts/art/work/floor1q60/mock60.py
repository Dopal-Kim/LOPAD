"""60라운드 Q4 — 1층 양조 구역 조명 목업: 현행(v2 타일 + 적 v3) / 보강안(타일 32 규격) / 보강안(타일 64 = 2배 밀도, 인터뷰용).

python3 parts/art/work/floor1q60/mock60.py
- 1배 = 1920×1080 내부 렌더 기준(논리 1px = 렌더 2px). 장면 16×9칸 (논리 512×288 → 렌더 1024×576) + 위쪽 Gemini 북쪽 테두리 띠 일부.
- 조명: floors_v2 목업과 같은 값 — 주변광 0.425/0.425/0.475, 주인공 빛 #b0611a r140 · 0.75, 솥 빛(v3 소품 JSON), 발광 색 가산 + 번짐.
  (조명 합성기는 gemini/border_outer/mock.py 의 World.lit 를 import 만 — 시스템 실제 셰이더와 다를 수 있음)
산출: preview_mock_before_after.png (3패널 1배) · preview_mock_zoom.png (같은 자리 2배 확대 3장)
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
sys.path.insert(0, HERE)
import tiles60  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

R, T = 2, 32
CW, CH = 16, 9
AMB = (0.425, 0.425, 0.475)
HERO_LIGHT = ("#b0611a", 140, 0.75)
FONT = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 26)
FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 18)
EMC = {M.hx(c) for c in ["#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0", "#ffffff", "#fff4dc"]}
TOPPAD = 120          # 논리: 북쪽 테두리 띠를 보여 줄 높이


class World(M.World):
    def __init__(self):
        self.bj = None
        self.x0, self.y0 = 0, -TOPPAD
        self.x1, self.y1 = CW * T, CH * T
        self.W, self.H = int((self.x1 - self.x0) * R), int((self.y1 - self.y0) * R)
        self.alb = Image.new("RGBA", (self.W, self.H), (14, 15, 20, 255))
        self.emi = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 255))
        self.lights = []


def sprite(path, row, col):
    meta = gridsheet.load_meta(path + ".json")
    im = gridsheet.open_grid(path + ".png")
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    return im.crop((col * fw, row * fh, col * fw + fw, row * fh + fh)), meta


def grid_frame(png, js, row, col):
    j = json.load(open(js))
    im = Image.open(png).convert("RGBA")
    fw, fh = j["frameWidth"], j["frameHeight"]
    return im.crop((col * fw, row * fh, col * fw + fw, row * fh + fh)), j


def old_tiles():
    p = os.path.join(ROOT, "assets/tiles/v2/stage1_brewery")
    sh = Image.open(p + ".png").convert("RGBA")
    meta = json.load(open(p + ".json", encoding="utf-8"))
    cols = meta["columns"]

    def cell(i):
        return M.up(sh.crop(((i % cols) * T, (i // cols) * T, (i % cols) * T + T, (i // cols) * T + T)))
    floors = [cell(i) for i in meta["tiles"]["1"]]
    stains = [cell(i) for i in meta["roomFloors"]["trial"]]
    return floors, stains, {"top": cell(45), "upper": cell(44), "lower": [cell(43), cell(46)]}


def new_tiles(N):
    t = tiles60.build_set(N)
    k = R * T // N

    def u(im):
        return im.resize((im.width * k, im.height * k), Image.NEAREST)
    floors = [u(t["floor_%d" % i]) for i in range(6)]
    # 가중치: 큰 판석(one·two)이 더 자주
    floors = floors + [floors[1], floors[3], floors[4]]
    stains = [u(t["trial_%d" % i]) for i in range(4)]
    return floors, stains, {"top": u(t["cover_top"]), "upper": u(t["cover_upper"]), "lower": [u(t["cover_lower"]), u(t["cover_lower_b"])]}


STAIN_AT = {(3, 6), (12, 7), (10, 1)}
WALL = (2, 1, 4)    # 열 시작, 행(윗면), 칸 수


def build(kind):
    w = World()
    floors, stains, cover = old_tiles() if kind == "before" else new_tiles(32 if kind == "after32" else 64)
    # 북쪽 테두리 띠(바닥 위 TOPPAD 만큼)
    bdir = os.path.join(ROOT, "assets/tiles/border/brewery")
    bj = json.load(open(os.path.join(bdir, "border.json"), encoding="utf-8"))
    nb = bj["bands"]["north"]
    band = Image.open(os.path.join(bdir, nb["image"])).convert("RGBA")
    bem = Image.open(os.path.join(bdir, nb["emissive"])).convert("RGBA")
    by0 = (nb["baselineY"] - TOPPAD) * R
    crop = (400 * R, int(by0), 400 * R + w.W, int(by0 + (TOPPAD + nb.get("apronBelow", 0)) * R))
    for ty in range(CH):
        for tx in range(CW):
            im = stains[M.h2(tx, ty, len(stains))] if (tx, ty) in STAIN_AT else floors[M.h2(tx + 3, ty * 7 + 1, len(floors))]
            w.put(im, tx * T, ty * T, occlude=False)
    w.put(band.crop(crop), 0, -TOPPAD, bem.crop(crop), occlude=True)
    for L in nb["lights"]:
        lx = L["x"] - 400
        if 0 <= lx <= CW * T:
            w.light(lx, L["y"] - nb["baselineY"], L["color"], L["radius"], L["intensity"])
    # 엄폐 담: 윗면(행 r) · 앞면 윗단(r+1) · 앞면 아랫단(r+2)
    c0, r0, n = WALL
    for i in range(n):
        w.put(cover["top"], (c0 + i) * T, r0 * T, occlude=True)
        w.put(cover["upper"], (c0 + i) * T, (r0 + 1) * T, occlude=True)
        w.put(cover["lower"][i % 2], (c0 + i) * T, (r0 + 2) * T, occlude=True)
    # 발치 그늘 한 줄
    sh = Image.new("RGBA", (n * T * R, 10 * R), (6, 7, 10, 120))
    w.put(sh, c0 * T, (r0 + 3) * T, occlude=False)
    # 소품(v3, 그대로)
    pp = os.path.join(ROOT, "assets/tiles/v3/stage1_brewery_props")
    psh = Image.open(pp + ".png").convert("RGBA")
    pj = json.load(open(pp + ".json", encoding="utf-8"))
    table = {e["name"]: e for e in pj["props"] + pj["bigProps"]}
    items = []

    def prop(name, tx, ty):
        e = table[name]
        r = e["rect"]
        im = psh.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]))
        px_, py_ = tx * T + 16, ty * T + 30
        x0, y0 = px_ - e["pivot"]["x"] / 2, py_ - e["pivot"]["y"] / 2
        lights = []
        if e.get("light"):
            L = e["light"]
            lights.append((x0 + L["offset"]["x"] / 2, y0 + L["offset"]["y"] / 2, L["color"], L["radius"] / 2, L["intensity"]))
        items.append((py_, x0, y0, im, M.emissive_of(im, EMC), lights, None))
    prop("cauldron", 13, 2)
    prop("barrel", 14, 6)
    prop("barrel", 13, 7)
    prop("crate", 1, 7)
    # 캐릭터: 주인공 v3 + 징집병 3(대기 오른쪽 · 휘두름 왼쪽 · 내리꽂기 아래)
    hero, hj = sprite(os.path.join(ROOT, "assets/sprites/player/v3/player_idle"), 0, 0)
    hx, hy = 8 * T + 16, 5 * T + 10
    items.append((hy, hx - hj["pivot"]["x"] / 2, hy - hj["pivot"]["y"] / 2, hero, M.emissive_of(hero, EMC | {(226, 163, 60)}),
                  [(hx - 10, hy - 40, *HERO_LIGHT)], (hx, hy, 34)))
    if kind == "before":
        def en(act, row, col):
            return sprite(os.path.join(ROOT, "assets/sprites/enemies/v3/dummy_%s" % act), row, col)
        cast = [(en("idle", 3, 0), 5 * T + 4, 6 * T + 20), (en("attack", 2, 2), 11 * T + 10, 4 * T + 26),
                (en("attack", 0, 3), 9 * T + 30, 7 * T + 28)]
    else:
        def en(act, row, col):
            return grid_frame(os.path.join(HERE, "out/dummy60_%s.png" % act), os.path.join(HERE, "out/dummy60_%s.json" % act), row, col)
        cast = [(en("idle", 3, 0), 5 * T + 4, 6 * T + 20), (en("attack", 2, 3), 11 * T + 10, 4 * T + 26),
                (en("attack", 0, 4), 9 * T + 30, 7 * T + 28)]
    for (im, j), ex, ey in cast:
        items.append((ey, ex - j["pivot"]["x"] / 2, ey - j["pivot"]["y"] / 2, im, M.emissive_of(im, EMC), [], (ex, ey, 34)))
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
    return w


TITLES = {"before": "현행 — v2 바닥(32) · 징집병 v3",
          "after32": "보강안 A — 바닥 32 규격(현행 크기) · 징집병 보강",
          "after64": "보강안 B — 바닥 64(2배 밀도, 규격 변경 필요) · 징집병 보강"}


def main():
    panels = {}
    for k in ("before", "after32", "after64"):
        w = build(k)
        panels[k] = M.vignette(w.lit(AMB), 0.35)
        print("panel", k, panels[k].size)
    pw, ph = panels["before"].size
    out = Image.new("RGB", (pw * 3 + 24, ph + 50), (12, 12, 16))
    d = ImageDraw.Draw(out)
    for i, k in enumerate(("before", "after32", "after64")):
        out.paste(panels[k], (i * (pw + 12), 50))
        d.text((i * (pw + 12) + 8, 10), TITLES[k], fill=(235, 225, 200), font=FONT)
    out.save(os.path.join(HERE, "preview_mock_before_after.png"))
    # 2배 확대: 주인공·징집병 둘레
    box = (int(4.5 * T * R), int((TOPPAD + 3.2 * T) * R), int(12.5 * T * R), int((TOPPAD + 8.4 * T) * R))
    zs = [panels[k].crop(box) for k in ("before", "after32", "after64")]
    zw, zh = zs[0].size
    out2 = Image.new("RGB", (zw * 2, (zh * 2 + 44) * 3), (12, 12, 16))
    d2 = ImageDraw.Draw(out2)
    for i, (k, z) in enumerate(zip(("before", "after32", "after64"), zs)):
        y = i * (zh * 2 + 44)
        out2.paste(z.resize((zw * 2, zh * 2), Image.NEAREST), (0, y + 40))
        d2.text((8, y + 6), TITLES[k] + " — 2배 확대", fill=(235, 225, 200), font=FONT_S)
    out2.save(os.path.join(HERE, "preview_mock_zoom.png"))
    print("saved", out.size, out2.size)


if __name__ == "__main__":
    main()
