"""61라운드 단계 2 미리보기(긴 변 8000 이하).
- preview_structs_v1_v3.png   : 시트마다 v1 첫 프레임(4배 = 같은 칸 크기) | v3 전 프레임 — 회색 칸 = 발자국, 빨강 = 피벗
- preview_mock_lit.png        : 양조 구역 새 타일(벽·문·수로) 위 구조물·소품·주인공, 어둠 조명 합성(위 = 낮 조명, 아래 = 어둠 + 광원) 2배
- preview_props61.png         : 지역별 새 소품(주인공 v3 옆, 1배·2배)
- out/mock61_<지역>.png        : 타일 전/후 목업(tiles61_build)
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import s61  # noqa: E402
import structs61  # noqa: E402
import sets61  # noqa: E402
import props61  # noqa: E402
import kit  # noqa: E402  (v2_outer — light_scene)

FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
N = 64


def font(sz):
    return ImageFont.truetype(FONT, sz) if os.path.exists(FONT) else ImageFont.load_default()


def hero():
    p = os.path.join(s61.SPR, "player", "v3", "player_idle")
    j = json.load(open(p + ".json", encoding="utf-8"))
    im = Image.open(os.path.join(os.path.dirname(p), j["image"] if j.get("image") else j["textures"][0]["image"])).convert("RGBA")
    fr = j["frames"]["0"] if isinstance(j["frames"], dict) else None
    out = Image.new("RGBA", (j["frameWidth"], j["frameHeight"]), (0, 0, 0, 0))
    if fr:
        f, ss = fr["frame"], fr["spriteSourceSize"]
        out.alpha_composite(im.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])), (ss["x"], ss["y"]))
    else:
        out = im.crop((0, 0, j["frameWidth"], j["frameHeight"]))
    return out, (j["pivot"]["x"], j["pivot"]["y"])


def v1_frame0(id_):
    j = json.load(open(os.path.join(s61.SPR, "structures", id_ + ".json"), encoding="utf-8"))
    im = Image.open(os.path.join(s61.SPR, "structures", j["image"])).convert("RGBA")
    f = im.crop((0, 0, j["frameWidth"], j["frameHeight"]))
    return f.resize((f.width * 4, f.height * 4), Image.NEAREST), j


def structs_board():
    rows = []
    for id_ in s61.STRUCTS + s61.SETS:
        v1im, v1 = v1_frame0(id_)
        mod = structs61 if hasattr(structs61, id_) else sets61
        fr, W, H, piv, m = getattr(mod, id_)(v1)
        rows.append((id_, v1im, fr, piv, m["footprint"]))
    pad = 10
    Wmax = 0
    heights = []
    for (_, v1im, fr, piv, fp) in rows:
        w = 200 + v1im.width + 30 + sum(f.width + pad for f in fr)
        Wmax = max(Wmax, w)
        heights.append(max(v1im.height, fr[0].height) + 30)
    Hsum = sum(heights) + 40
    k = max(1, min(2, 8000 // max(Wmax, Hsum)))
    out = Image.new("RGBA", (Wmax, Hsum), (40, 42, 50, 255))
    d = ImageDraw.Draw(out)
    y = 40
    d.text((8, 8), "61라운드 AR-4 구조물 v1(왼쪽, 4배 = 같은 칸 크기) → v3 64도트(오른쪽 전 프레임) · 파랑 = 발자국 · 빨강 = 피벗",
           fill=(235, 225, 200), font=font(20))
    for (id_, v1im, fr, piv, fp), h in zip(rows, heights):
        d.text((8, y + 8), id_, fill=(232, 184, 88), font=font(16))
        base = y + h - 20
        out.alpha_composite(v1im, (200, base - v1im.height))
        x = 200 + v1im.width + 30
        for f in fr:
            ox, oy = x, base - f.height
            out.alpha_composite(f, (ox, oy))
            px_, py_ = ox + piv[0], oy + piv[1]
            fw, fh = fp[0] * N, max(1, fp[1]) * N
            d.rectangle((px_ - fw // 2, py_ - fh, px_ + fw // 2, py_), outline=(90, 140, 220, 255))
            d.rectangle((px_ - 1, py_ - 1, px_ + 1, py_ + 1), fill=(230, 60, 60, 255))
            x += f.width + pad
        y += h
    out = out.resize((out.width * k, out.height * k), Image.NEAREST)
    out.convert("RGB").save(os.path.join(HERE, "preview_structs_v1_v3.png"))
    return out.size


def mock_lit():
    """양조 구역 방 한 칸(14×8): 북쪽 벽(61 새 칸) + 수로·다리 + 구조물 v3 + 새 소품 + 주인공 → 어둠 조명."""
    sheet = Image.open(os.path.join(HERE, "out", "tiles61_brewery.png")).convert("RGBA")
    cols = sheet.width // N
    cell = lambda i: sheet.crop(((i % cols) * N, (i // cols) * N, (i % cols) * N + N, (i // cols) * N + N))
    TW, TH = 14, 9
    al = Image.new("RGBA", (TW * N, TH * N), (0, 0, 0, 255))
    lower = [5, 21, 5, 63, 22, 5, 5, 21, 5, 8, 5, 63, 5, 5]
    upper = [40, 40, 41, 42, 41, 40, 40, 40, 42, 40, 40, 41, 40, 40]
    for x in range(TW):
        al.alpha_composite(cell(47), (x * N, 0))
        al.alpha_composite(cell(upper[x]), (x * N, N))
        al.alpha_composite(cell(lower[x]), (x * N, 2 * N))
        for y in range(3, TH):
            al.alpha_composite(cell([0, 1, 3, 2][(x * 7 + y * 3) % 4]), (x * N, y * N))
        al.alpha_composite(cell(53), (x * N, 3 * N))
        if x in (5, 6):
            al.alpha_composite(cell(67 if x == 5 else 68), (x * N, 6 * N))
        else:
            al.alpha_composite(cell([64, 65, 66][x % 3] if abs(x - 5.5) > 2 else [69, 70, 71][x % 3]), (x * N, 6 * N))
    lights = []
    for x in range(TW):
        if lower[x] == 21:
            lights.append({"x": x * N + 32, "y": 2 * N + 40, "color": "#e8a33c", "radius": 220, "intensity": 0.8})
    items = []

    def put(id_, tx, ty, frame=0):
        v1 = s61.v1json(id_)
        mod = structs61 if hasattr(structs61, id_) else sets61
        fr, W, H, piv, m = getattr(mod, id_)(v1)
        fp = m["footprint"]
        bx = tx * N + fp[0] * N // 2
        by = (ty + 1) * N
        items.append((by, fr[frame], bx - piv[0], by - piv[1]))
        L = m.get("light")
        if L and L.get("radius"):
            o = L.get("offset", {"x": piv[0], "y": piv[1]})
            lights.append({"x": bx - piv[0] + o["x"], "y": by - piv[1] + o["y"], "color": L["color"], "radius": L["radius"], "intensity": L["intensity"]})
    put("counter", 1, 4)
    put("cask", 5, 4)
    put("barrel", 8, 4); put("barrel", 9, 5, 0); put("crate_f1", 10, 4)
    put("chest", 11, 4)
    put("ledger", 13, 4)
    put("bonfire", 2, 7, 1)
    put("grave", 9, 8)
    put("cellar_wall", 12, 2)
    for f, tx, ty in ((props61.brew_still_column, 0, 4), (props61.brew_mash_tub, 6, 8), (props61.brew_liquor_sacks, 12, 8),
                      (props61.brew_bottle_crate, 4, 8)):
        p = f()
        fpw = p.footprint[0]
        bx, by = tx * N + fpw * N // 2, (ty + 1) * N
        items.append((by, p.im, bx - p.pivot[0], by - p.pivot[1]))
        if p.light:
            lights.append({"x": bx - p.pivot[0] + p.light["offset"]["x"], "y": by - p.pivot[1] + p.light["offset"]["y"],
                           "color": p.light["color"], "radius": p.light["radius"], "intensity": p.light["intensity"]})
    h, hp = hero()
    items.append((5 * N + 40, h, 7 * N - hp[0], 5 * N + 40 - hp[1]))
    lights.append({"x": 7 * N, "y": 5 * N, "color": "#c8c0b0", "radius": 260, "intensity": 0.35})
    for (_, im, x, y) in sorted(items, key=lambda t: t[0]):
        al.alpha_composite(im, (int(x), int(y)))
    lit = kit.light_scene(al, lights, ambient=(0.22, 0.24, 0.32), scale=4)
    out = Image.new("RGB", (al.width, al.height * 2 + 20), (10, 10, 12))
    out.paste(al.convert("RGB"), (0, 0)); out.paste(lit, (0, al.height + 20))
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.save(os.path.join(HERE, "preview_mock_lit.png"))
    return out.size


def props_board():
    h, hp = hero()
    rows = []
    for rid, d in props61.NEW.items():
        rows.append((rid, [f() for f in d["small"] + d["big"]]))
    pad = 16
    W = max(h.width + sum(p.im.width + pad for p in ps) for _, ps in rows) + 200
    Hs = [max([h.height] + [p.im.height for p in ps]) + 40 for _, ps in rows]
    out = Image.new("RGBA", (W, sum(Hs) + 40), (44, 46, 54, 255))
    d = ImageDraw.Draw(out)
    d.text((8, 8), "61라운드 방 다양화 소품(새 항목) — 지역별 · 왼쪽 주인공 v3 · 빨강 = 피벗", fill=(235, 225, 200), font=font(20))
    y = 40
    for (rid, ps), hh in zip(rows, Hs):
        d.text((8, y + 6), rid, fill=(232, 184, 88), font=font(18))
        base = y + hh - 30
        out.alpha_composite(h, (120, base - hp[1]))
        x = 120 + h.width + pad
        for p in ps:
            ox, oy = x, base - p.pivot[1]
            out.alpha_composite(p.im, (ox, oy))
            d.rectangle((ox + p.pivot[0] - 1, oy + p.pivot[1] - 1, ox + p.pivot[0] + 1, oy + p.pivot[1] + 1), fill=(230, 60, 60, 255))
            d.text((ox, base + 6), p.name, fill=(220, 220, 220), font=font(12))
            x += p.im.width + pad
        y += hh
    out = out.resize((out.width * 2, out.height * 2), Image.NEAREST)
    out.convert("RGB").save(os.path.join(HERE, "preview_props61.png"))
    return out.size


def main():
    print("structs", structs_board())
    print("mock", mock_lit())
    print("props", props_board())


if __name__ == "__main__":
    main()
