"""61 단계 6 미리보기 (배포물 아님): preview_doors · preview_transition · preview_training · preview_props."""
import json
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(HERE, "../atlas57"))
sys.path.insert(0, os.path.join(HERE, "../v2_outer"))
import gridsheet  # noqa: E402
from kit import light_scene  # noqa: E402

PAINT = os.path.join(ROOT, "assets/sprites/paint")
STR = os.path.join(ROOT, "assets/sprites/structures/v3")


def doors():
    man = json.load(open(os.path.join(PAINT, "doors.json"), encoding="utf-8"))
    keys = list(man["doors"])
    cols = 4
    W, H = 320, 180
    rows = (len(keys) + cols - 1) // cols
    s = Image.new("RGB", (cols * W, rows * (H + 14)), (20, 20, 22))
    d = ImageDraw.Draw(s)
    for i, k in enumerate(keys):
        m = json.load(open(os.path.join(PAINT, man["doors"][k]["json"]), encoding="utf-8"))
        im = Image.open(os.path.join(PAINT, m["image"])).convert("RGB")
        dd = ImageDraw.Draw(im)
        r = m["doorRect"]
        dd.rectangle([r["x"], r["y"], r["x"] + r["w"] - 1, r["y"] + r["h"] - 1], outline=(80, 255, 120), width=2)
        x, y = (i % cols) * W, (i // cols) * (H + 14)
        s.paste(im.resize((W, H), Image.LANCZOS), (x, y + 14))
        d.text((x + 4, y + 1), f"door_{k}  light {m['light']['color']}", fill=(220, 220, 220))
    s.save(os.path.join(HERE, "preview_doors.png"))


def room_mock(seed=1):
    """수련장 방 목업 960×540(2배 도트를 0.5 로) — 타일 + 소품."""
    til = Image.open(os.path.join(ROOT, "assets/tiles/v2/stage1_training.png")).convert("RGBA")
    big = Image.new("RGBA", (1920, 1080))
    rnd = random.Random(seed)
    for ty in range(17):
        for tx in range(30):
            i = rnd.choice([0, 1, 2, 3, 27, 28])
            big.paste(til.crop(((i % 8) * 64, (i // 8) * 64, (i % 8) * 64 + 64, (i // 8) * 64 + 64)), (tx * 64, ty * 64))
    lights = []
    props = [("training_rack_katana", 1, 520, 470), ("training_rack_greatsword", 1, 760, 470), ("training_rack_dagger", 1, 1000, 470),
             ("training_rack_bow", 1, 1240, 470), ("training_task_sign", 2, 1560, 420), ("training_stamp_board", 5, 1720, 470),
             ("training_flag", 2, 400, 800), ("training_task_sign", 5, 260, 470)]
    for name, fi, px, py in sorted(props, key=lambda t: t[3]):
        m = gridsheet.load_meta(os.path.join(STR, name + ".json"))
        g = gridsheet.open_grid(os.path.join(STR, name + ".json"))
        fw, fh = m["frameWidth"], m["frameHeight"]
        fr = g.crop((fi * fw, 0, fi * fw + fw, fh))
        ox, oy = px - m["pivot"]["x"], py - m["pivot"]["y"]
        big.alpha_composite(fr, (ox, oy))
        L = m.get("light")
        st = [k for k, v in m["states"].items() if fi in v][0]
        if L and (m.get("lightByState", {}).get(st) or (fi == 3 and "lightByFrame" in m)):
            lights.append({"x": ox + L["offset"]["x"], "y": oy + L["offset"]["y"], "color": L["color"],
                           "radius": L["radius"], "intensity": L["intensity"] + 0.4})
    lights.append({"x": 960, "y": 300, "color": "#f4de9b", "radius": 1300, "intensity": 0.55})
    lit = light_scene(big, lights, ambient=(0.42, 0.42, 0.46), vignette=0.35, scale=8)
    return lit.resize((960, 540), Image.BOX)


def transition():
    """노드 지도 → 입구로 파고듦 → 어둠 → 먹 붓질 걷힘 → 방 → (나갈 때) 액자."""
    door = Image.open(os.path.join(PAINT, "door_outer_shop.png")).convert("RGB")
    m = json.load(open(os.path.join(PAINT, "door_outer_shop.json"), encoding="utf-8"))
    r = m["doorRect"]
    room = room_mock()
    cells = []
    big = door.resize((960, 540), Image.LANCZOS)
    cells.append(big)
    cx, cy = (r["x"] + r["w"] / 2) * 1.5, (r["y"] + r["h"] / 2) * 1.5
    for z in (2.0, 4.0):
        w, h = 960 / z, 540 / z
        cells.append(big.crop((int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))).resize((960, 540), Image.LANCZOS))
    mask = Image.open(os.path.join(PAINT, "brush_reveal_2.png")).convert("L")
    ink = Image.new("RGB", (960, 540), (14, 14, 16))
    for p in (0.25, 0.5, 0.8):
        a = mask.point(lambda v, p=p: max(0, min(255, int((p * 255 - v) / (0.04 * 255) * 255))))
        cells.append(Image.composite(room, ink, a))
    cells.append(room)
    fr = Image.open(os.path.join(PAINT, "frame.png")).convert("RGBA")
    B = 44
    W2, H2 = 960 + 2 * B, 540 + 2 * B
    nine = Image.new("RGBA", (W2, H2))
    for (x0, x1, tw, dx) in ((0, B, B, 0), (B, 128 - B, W2 - 2 * B, B), (128 - B, 128, B, W2 - B)):
        for (y0, y1, th, dy) in ((0, B, B, 0), (B, 128 - B, H2 - 2 * B, B), (128 - B, 128, B, H2 - B)):
            nine.alpha_composite(fr.crop((x0, y0, x1, y1)).resize((tw, th), Image.NEAREST), (dx, dy))
    framed = Image.new("RGBA", (W2, H2), (0, 0, 0, 255))
    framed.paste(room, (B, B))
    framed.alpha_composite(nine)
    out = Image.new("RGB", (960, 540), (24, 20, 18))
    out.paste(framed.resize((W2 * 3 // 5, H2 * 3 // 5), Image.LANCZOS).convert("RGB"), ((960 - W2 * 3 // 5) // 2, (540 - H2 * 3 // 5) // 2))
    cells.append(out)
    cw, ch = 480, 270
    s = Image.new("RGB", (cw * 3, ch * 3), (0, 0, 0))
    for i, c in enumerate(cells[:9]):
        s.paste(c.resize((cw, ch), Image.LANCZOS), ((i % 3) * cw, (i // 3) * ch))
    s.save(os.path.join(HERE, "preview_transition.png"))
    room.save(os.path.join(HERE, "preview_room_mock.png"))


def training_map():
    im = Image.open(os.path.join(PAINT, "map_training.png")).convert("RGB")
    m = json.load(open(os.path.join(PAINT, "map_training.json"), encoding="utf-8"))
    d = ImageDraw.Draw(im)
    col = {"katana": (143, 227, 255), "greatsword": (255, 90, 42), "dagger": (192, 96, 255), "bow": (64, 224, 160)}
    for r in m["rooms"]:
        c = col.get(r.get("weapon"), (232, 184, 88))
        d.ellipse([r["x"] - 12, r["y"] - 12, r["x"] + 12, r["y"] + 12], outline=c, width=3)
        d.text((r["x"] + 14, r["y"] - 6), f"{r['index']} {r['id']}", fill=c)
    h = m["hub"]
    d.rectangle([h["x"] - 6, h["y"] - 6, h["x"] + 6, h["y"] + 6], outline=(255, 255, 255))
    im.save(os.path.join(HERE, "preview_training_map.png"))


def props():
    names = ["training_rack_katana", "training_rack_greatsword", "training_rack_dagger", "training_rack_bow",
             "training_task_sign", "training_stamp_board", "training_flag"]
    rows = []
    for n in names:
        g = gridsheet.open_grid(os.path.join(STR, n + ".json"))
        bg = Image.new("RGBA", g.size, (64, 62, 60, 255))
        bg.alpha_composite(g)
        rows.append(bg)
    W = max(r.width for r in rows)
    H = sum(r.height for r in rows)
    s = Image.new("RGBA", (W, H), (24, 24, 26, 255))
    y = 0
    for r in rows:
        s.paste(r, (0, y))
        y += r.height
    s.resize((W * 2 // 2, H * 2 // 2)).save(os.path.join(HERE, "preview_props.png"))


def brush():
    s = Image.new("L", (960, 540 + 4 * 112), 30)
    for i in range(4):
        im = Image.open(os.path.join(PAINT, f"brush_reveal_{i}.png"))
        s.paste(im.resize((480, 270)), ((i % 2) * 480, (i // 2) * 270))
        for k, p in enumerate((0.15, 0.35, 0.55, 0.75, 0.9)):
            th = im.point(lambda v, p=p: 255 if v <= p * 255 else 0)
            s.paste(th.resize((180, 102)), (k * 190, 540 + i * 112))
    s.save(os.path.join(HERE, "preview_brush.png"))


def run():
    doors()
    brush()
    training_map()
    props()
    transition()
    print("preview ok")
