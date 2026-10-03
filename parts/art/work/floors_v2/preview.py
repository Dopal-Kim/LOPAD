#!/usr/bin/env python3
# [53라운드] 미리보기·목업 입력 중 구 시트(assets/sprites/player/player_*, enemies/{dummy,archer,charger}_*, enemies/v2/charger_*, player/v2/*)는 삭제됨 — v3 시트로 바꿀지 결정 대기(아트 보고서 인터뷰 항목). 그 단계는 재실행 시 FileNotFoundError.
"""53라운드 — 5지역 미리보기: 쿼터뷰 바닥(v2 타일) + Gemini 테두리 + v3 소품 + v3 주인공(1.5배), 조명 합성.

python3 parts/art/work/floors_v2/preview.py [region ...]
- 1배 = 1920×1080 렌더(논리 960×540 × 2). 전투장 32×20칸(Q7), 카메라 위로 110(연회장 160, Q24).
- 주변광: Q9 숯빛 0.34/0.34/0.38 × 1.25 = 0.425/0.425/0.475 (Q23 '기본 구역 밝기 상향', 임시값).
  주인공 빛: 반경 90 → 140 논리 px, 세기 0.55 → 0.75 (Q23, 임시값). 적은 발밑 그림자 진하게.
- 테두리·골목 조각 배치는 gemini/border_mock.py 를 그대로 쓴다(읽기만 — 테두리 PNG 는 수정하지 않음).
산출: preview_mock_<region>.png(1920×1080), preview_mock_<region>_overview.png(전투장 전체, 논리 1배), preview_mock_f1.png(5지역 모음)
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
GEM = os.path.normpath(os.path.join(HERE, "../gemini"))
sys.path.insert(0, GEM)
sys.path.insert(0, os.path.join(GEM, "border_outer"))
import mock as M  # noqa: E402
import border_mock as BM  # noqa: E402

ROOT = M.ROOT
R, T = 2, 32
FW, FH = 32, 20
AMB = (0.34 * 1.25, 0.34 * 1.25, 0.38 * 1.25)
HERO_LIGHT = {"color": "#b0611a", "radius": 140, "intensity": 0.75}
LOOKUP = {"hall": 160}
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
REG = ["outer", "waste", "gate", "brewery", "hall"]
NAMES = BM.NAMES

# 장면 배치: (이름, tx, ty) — props 는 칸 하나, bigProps 는 발자국 왼쪽 위 칸
SCENES = {
    "outer": {"hero": (13, 5), "props": [
        ("lamp_post", 4, 1), ("stall", 20, 1), ("well", 9, 7), ("crate_stack", 26, 2), ("barrel", 7, 2), ("barrel", 8, 2),
        ("crate", 27, 3), ("sacks", 6, 3), ("brazier", 16, 8), ("tipped_barrel", 18, 5), ("puddle", 12, 9),
        ("debris", 22, 7), ("lantern", 3, 7), ("lamp_post", 24, 9)], "decals": []},
    "waste": {"hero": (13, 5), "props": [
        ("stakes", 4, 1), ("broken_cart", 21, 2), ("banner_pole", 11, 1), ("weapons_stuck", 17, 4), ("cannon", 25, 7),
        ("campfire", 15, 8), ("helmet_shield", 9, 6), ("bones", 20, 9), ("sandbags", 6, 9), ("sandbags", 7, 9),
        ("crate", 27, 3), ("mud_puddle", 11, 10), ("sacks", 26, 3), ("weapons_stuck", 2, 6)],
        "decals": [("wheel_ruts", 8, 4), ("wheel_ruts", 18, 7), ("scorch", 14, 7), ("scorch", 21, 2)]},
    "gate": {"hero": (16, 5), "props": [
        ("torch_stand", 13, 1), ("torch_stand", 18, 1), ("toll_booth", 25, 8), ("barrel_cart", 3, 2),
        ("barricade_x", 21, 4), ("water_trough", 2, 7), ("crate_stack", 28, 2), ("barrel", 9, 1), ("barrel", 10, 1),
        ("sacks", 8, 2), ("puddle", 11, 8), ("tipped_barrel", 20, 9), ("debris", 6, 9)],
        "decals": [("light_puddles", 15, 3), ("wheel_ruts", 14, 6), ("wheel_ruts", 14, 9)]},
    "brewery": {"hero": (13, 5), "props": [
        ("barrel_pyramid", 3, 1), ("crane_barrel", 9, 1), ("steel_vat", 24, 1), ("handcart", 20, 6), ("cauldron", 17, 6),
        ("crate_stack", 28, 2), ("barrel", 12, 3), ("barrel", 13, 2), ("rope_coil", 18, 3), ("liquor_stain", 10, 7),
        ("steam_vent", 6, 6), ("pallet", 26, 7), ("sacks", 22, 3), ("barrel", 8, 10), ("crate", 21, 11)],
        "decals": [("liquor_trail", 13, 7)], "canal": {"row": 8, "bridge": 14}},
    "hall": {"hero": (16, 5), "props": [
        ("banquet_table", 4, 3), ("banquet_table", 26, 3), ("pillar", 8, 1), ("pillar", 23, 1),
        ("candelabra_stand", 12, 1), ("candelabra_stand", 19, 1), ("bench", 3, 11), ("barrel", 28, 2),
        ("tipped_barrel", 7, 11), ("wine_puddle", 13, 6), ("goblets", 19, 7), ("bottles", 10, 9), ("chair", 25, 11)],
        "decals": [("cup_inlay", 14, 7), ("wine_trail", 18, 5)]},
}


def load_floor(rid):
    p = os.path.join(ROOT, f"assets/tiles/v2/stage1_{rid}")
    sheet = Image.open(p + ".png").convert("RGBA")
    meta = json.load(open(p + ".json", encoding="utf-8"))
    cols = meta["columns"]
    cache = {}

    def cell(i):
        if i not in cache:
            cache[i] = M.up(sheet.crop(((i % cols) * T, (i // cols) * T, (i % cols) * T + T, (i // cols) * T + T)))
        return cache[i]

    def decal(name):
        for d in meta.get("decals", []):
            if d["name"] == name:
                r = d["rect"]
                return M.up(sheet.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"])))
        raise KeyError(name)
    return meta, cell, decal


def load_props(rid):
    p = os.path.join(ROOT, f"assets/tiles/v3/stage1_{rid}_props")
    sheet = Image.open(p + ".png").convert("RGBA")
    meta = json.load(open(p + ".json", encoding="utf-8"))
    table = {}
    for e in meta["props"]:
        table[e["name"]] = (e, False)
    for e in meta["bigProps"]:
        table[e["name"]] = (e, True)
    emc = set(M.hx(c)[:3] for c in meta["emissiveColors"])

    def get(name):
        e, big = table[name]
        r = e["rect"]
        return sheet.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"])), e, big
    return get, emc


def h2(x, y, n):
    return M.h2(x, y, n)


def build(rid):
    bdir = os.path.join(ROOT, "assets/tiles/border", rid)
    bj = json.load(open(os.path.join(bdir, "border.json"), encoding="utf-8"))
    world = BM.World(bj)
    meta, cell, decal = load_floor(rid)
    get, emc = load_props(rid)
    sc = SCENES[rid]
    fl = meta["tiles"]["1"]
    rf = meta["roomFloors"]
    mix = meta.get("roomFloorMix", 0.06)
    canal = sc.get("canal")
    for ty in range(FH):
        for tx in range(FW):
            i = fl[h2(tx, ty, len(fl))]
            if h2(tx + 7, ty + 3, 1000) < mix * 1000:
                k = ["start", "trial", "rest", "boss"][h2(tx, ty + 5, 4)]
                i = rf[k][h2(tx + 2, ty, 4)]
            if canal and ty == canal["row"]:
                b = canal["bridge"]
                c = meta["canal"]
                if tx == b:
                    i = c["bridge"]["left"]
                elif tx == b + 1:
                    i = c["bridge"]["right"]
                elif abs(tx - b) <= c["litNearBridge"] or abs(tx - b - 1) <= c["litNearBridge"]:
                    i = c["framesLit"][0]
                else:
                    i = c["frames"][0]
            world.put(cell(i), tx * T, ty * T, occlude=False)
            # 발광 픽셀(수로 빛 줄)
            if canal and ty == canal["row"]:
                world.put(Image.new("RGBA", (1, 1)), tx * T, ty * T, M.emissive_of(cell(i), emc), occlude=False)
    if canal:
        L = meta["tileLights"]["67"]
        world.light(canal["bridge"] * T + L["offset"]["x"], canal["row"] * T + L["offset"]["y"], L["color"], L["radius"] * 1.6,
                    L["intensity"])
    for (name, tx, ty) in sc["decals"]:
        world.put(decal(name), tx * T, ty * T, occlude=False)
    BM.edge_shadow(world)
    b = bj["bands"]
    focus = b["north"].get("focusX")
    phase = (FW * T / 2 - focus) if focus is not None else None
    for n in ("west", "east"):
        BM.place_band(world, bdir, n, b[n])
    BM.place_band(world, bdir, "north", b["north"], phase)
    doors = bj.get("doors", {})
    dc = BM.DOORS[rid]
    for side in ("west", "east", "north"):
        key = "west" if side == "east" else side
        if side in doors and key in dc:
            BM.place_door(world, bdir, side, doors[side], dc[key])

    items = []           # (sortY, x_left, y_top, img, emissive, light list, shadow)
    for (name, tx, ty) in sc["props"]:
        im, e, big = get(name)
        if big:
            fw, fh = e["footprint"][0], max(1, e["footprint"][1])
            px_, py_ = tx * T + fw * T / 2, (ty + fh - 1) * T + 30
        else:
            px_, py_ = tx * T + 16, ty * T + 30
        x0, y0 = px_ - e["pivot"]["x"] / 2, py_ - e["pivot"]["y"] / 2
        lights = []
        for L in ([e["light"]] if "light" in e and "lights" not in e else []) + e.get("lights", []):
            lights.append((x0 + L["offset"]["x"] / 2, y0 + L["offset"]["y"] / 2, L["color"], L["radius"] / 2, L["intensity"]))
        sort_y = py_ if e.get("depth") != "floor" else -1
        items.append((sort_y, x0, y0, im, M.emissive_of(im, emc), lights, None))
    hx_, hy_ = sc["hero"]
    hx, hy = hx_ * T + 16, hy_ * T + 30
    hero, hj = M.frame(os.path.join(ROOT, "assets/sprites/player/v3/player_idle"), 0, 0)
    items.append((hy, hx - hj["pivot"]["x"] / 2, hy - hj["pivot"]["y"] / 2, hero, M.emissive_of(hero, emc | {(226, 163, 60)}),
                  [(hx - 10, hy - 40, HERO_LIGHT["color"], HERO_LIGHT["radius"], HERO_LIGHT["intensity"])], (hx, hy, 34)))
    for (path, row, col, dx, dy) in (("enemies/v2/charger_walk", 2, 2, 150, -40), ("enemies/v2/charger_attack", 3, 1, -170, 30),
                                     ("enemies/v2/charger_idle", 1, 0, 70, 150)):
        im, j = M.frame(os.path.join(ROOT, "assets/sprites", path), row, col)
        im = M.up(im, R * j.get("pixelScale", 1))
        ex, ey = hx + dx, hy + dy
        items.append((ey, ex - j["pivot"]["x"], ey - j["pivot"]["y"], im, M.emissive_of(im, emc), [], (ex, ey, 24)))
    items.sort(key=lambda t: t[0])
    for (sy, x0, y0, im, em, lights, shadow) in items:
        if shadow:
            sx, sy_, w = shadow
            sh = Image.new("RGBA", (w * 2, 16), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse((0, 0, w * 2 - 1, 15), fill=(8, 9, 14, 165))       # Q23: 발밑 그림자 진하게
            world.put(sh, sx - w / 2, sy_ - 4, occlude=False)
        world.put(im, x0, y0, em, occlude=True)
        for L in lights:
            world.light(*L)
    BM.place_band(world, bdir, "south", b["south"], phase)
    if "south" in doors and "south" in dc:
        BM.place_door(world, bdir, "south", doors["south"], dc["south"])
    return world, hx, hy


def run(rid):
    world, hx, hy = build(rid)
    lit = world.lit(AMB)
    cx, cy = min(max(hx, 480 - 120), FW * T - 480 + 120), hy - LOOKUP.get(rid, 110)
    cy = max(cy, -world.bj["bands"]["north"]["baselineY"] + 270)
    v = M.view(world, lit, cx, cy)
    v.save(os.path.join(HERE, f"preview_mock_{rid}.png"))
    ov = lit.resize((world.W // 2, world.H // 2), Image.LANCZOS)
    d = ImageDraw.Draw(ov)
    x0, y0 = cx - 480 - world.x0, cy - 270 - world.y0
    d.rectangle((x0, y0, x0 + 960, y0 + 540), outline=(232, 184, 88), width=3)
    ov.save(os.path.join(HERE, f"preview_mock_{rid}_overview.png"))
    print("mock", rid)
    return v


def collage():
    f = ImageFont.truetype(FONT, 30)
    tiles = [Image.open(os.path.join(HERE, f"preview_mock_{r}.png")).convert("RGB").resize((960, 540), Image.LANCZOS) for r in REG]
    out = Image.new("RGB", (960 * 2 + 12, 3 * (540 + 48)), (12, 12, 16))
    for i, (r, im) in enumerate(zip(REG, tiles)):
        x, y = (i % 2) * 972, (i // 2) * 588 + 44
        out.paste(im, (x, y))
        ImageDraw.Draw(out).text((x + 8, y - 40), f"{NAMES[r]} — v2 바닥 + 테두리 + v3 소품 + v3 주인공", fill=(235, 225, 200), font=f)
    d = ImageDraw.Draw(out)
    d.text((980, 2 * 588 + 60), "주변광 0.425/0.425/0.475 (Q9 × 1.25, Q23)\n주인공 빛 r140 · 0.75 (Q23 임시)\n적 = 결사병 v2(크기 후속)\n"
           "1배 = 1920×1080 렌더를 절반으로 줄인 모음", fill=(200, 190, 170), font=f)
    out.save(os.path.join(HERE, "preview_mock_f1.png"))
    print("collage")


if __name__ == "__main__":
    regs = sys.argv[1:] or REG
    for r in regs:
        run(r)
    if not sys.argv[1:]:
        collage()
