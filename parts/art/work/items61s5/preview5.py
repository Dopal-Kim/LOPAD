"""61 단계 5 미리보기 — 검수용(배포물 아님). 긴 변 8000 이하."""
import math
import os

from PIL import Image, ImageDraw

import kit5
from kit5 import HERE, ROOT, scale

BG = (24, 23, 28, 255)
ITEM_INFO = {}   # build.py 가 채움


def _save(im, name):
    if max(im.size) > 8000:
        s = 8000.0 / max(im.size)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.NEAREST)
    p = os.path.join(HERE, name)
    im.convert("RGB").save(p)
    print("preview", p, im.size)


def _floor(tiles_png, w_tiles, h_tiles, ids=(0, 1, 2, 3), seed=5):
    ts = Image.open(tiles_png).convert("RGBA")
    out = Image.new("RGBA", (w_tiles * 64, h_tiles * 64), BG)
    k = seed
    for ty in range(h_tiles):
        for tx in range(w_tiles):
            k = (k * 1103515245 + 12345) & 0x7fffffff
            i = ids[k % len(ids)]
            out.alpha_composite(ts.crop(((i % 8) * 64, (i // 8) * 64, (i % 8 + 1) * 64, (i // 8 + 1) * 64)), (tx * 64, ty * 64))
    return out


def _player():
    g = kit5.gridsheet.open_grid(os.path.join(ROOT, "assets", "sprites", "player", "v3", "player_idle.json"))
    m = kit5.gridsheet.load_meta(os.path.join(ROOT, "assets", "sprites", "player", "v3", "player_idle.json"))
    fw, fh = m["frameWidth"], m["frameHeight"]
    piv = m.get("pivot", {"x": fw // 2, "y": fh - 6})
    return g.crop((0, 0, fw, fh)), (piv["x"], piv["y"])


def _light(scene, emis_mask, lights, ambient=0.26):
    """어둠 목업: 바탕 × (ambient + Σ 광원 감쇠), emissive 픽셀은 그대로."""
    w, h = scene.size
    sp = scene.load()
    em = emis_mask.load()
    out = Image.new("RGBA", (w, h))
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = sp[x, y]
            if em[x, y]:
                op[x, y] = (r, g, b, 255)
                continue
            lr = lg = lb = ambient
            for (lx, ly, rad, col, inten) in lights:
                d = math.hypot(x - lx, (y - ly) * 1.15) / rad
                if d < 1:
                    f = inten * (1 - d) ** 1.6
                    lr += f * col[0]; lg += f * col[1]; lb += f * col[2]
            op[x, y] = (min(255, int(r * lr)), min(255, int(g * lg)), min(255, int(b * lb)), 255)
    return out


def _hex(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5))


def items_preview(items):
    import items5 as I
    groups = [I.IDLE, I.SPAWN, I.PICKUP, I.MAGNET]
    k = 3
    gap = 10
    rows = [(kind, r, fr[ri * I.NCOL:(ri + 1) * I.NCOL]) for kind, (rws, fr) in items.items() for ri, r in enumerate(rws)]
    W = I.NCOL * I.FW + gap * 3
    sheet = Image.new("RGBA", (W, len(rows) * I.FH), BG)
    d = ImageDraw.Draw(sheet)
    for j, (kind, r, fr) in enumerate(rows):
        x = 0
        for gi, g in enumerate(groups):
            for c in g:
                sheet.alpha_composite(fr[c], (x, j * I.FH))
                if c in I.GLOW_COLS:
                    d.rectangle((x, j * I.FH, x + 3, j * I.FH + 3), fill=(255, 244, 220, 255))
                x += I.FW
            if gi < 3:
                d.rectangle((x + 4, j * I.FH + 8, x + 5, j * I.FH + I.FH - 8), fill=(60, 58, 70, 255))
                x += gap
    big = scale(sheet, k)
    strip = sheet.copy()   # 1배 띠
    out = Image.new("RGBA", (big.width, big.height + strip.height + 16), BG)
    out.alpha_composite(big, (0, 0))
    out.alpha_composite(strip, (0, big.height + 16))
    _save(out, "preview_items.png")

    # 어둠 목업(연회장 바닥 + 주인공 + 물건 idle) — 위: 1배, 아래: 같은 장면 2배 일부
    floor = _floor(os.path.join(ROOT, "assets", "tiles", "v2", "stage1_hall.png"), 12, 6)
    scene = floor.copy()
    emis = Image.new("L", scene.size, 0)
    pl, ppiv = _player()
    px0, py0 = 384, 210
    lights = [(px0, py0 - 40, 300, (1.0, 0.86, 0.64), 1.25)]
    places = [("voucher", 0, 300, 230, 0), ("voucher", 1, 330, 280, 3), ("voucher", 2, 460, 260, 5), ("potion", 0, 250, 170, 4),
              ("fire_bottle", 0, 520, 180, 2), ("voucher", 2, 120, 300, 4), ("potion", 0, 660, 120, 0), ("fire_bottle", 0, 90, 110, 6),
              ("voucher", 0, 700, 330, 4)]
    ems = {}
    for kind in items:
        ems[kind] = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in ITEM_INFO[kind]["emissive"]}
    objs = []
    for kind, ri, x, y, col in places:
        if kind not in items:
            continue
        rws, fr = items[kind]
        objs.append((y, items[kind][1][ri * I.NCOL + col], x - I.PIV[0], y - I.PIV[1], ems[kind]))
        info = ITEM_INFO[kind]
        lt = info["light"] or (info.get("lightByKind", {}).get(rws[ri]))
        if lt:
            c = _hex(lt["color"])
            lights.append((x - I.PIV[0] + lt["offset"]["x"], y - I.PIV[1] + lt["offset"]["y"], lt["radius"], c, lt["intensity"]))
    objs.append((py0, pl, px0 - ppiv[0], py0 - ppiv[1], set()))
    for _, im, x, y, es in sorted(objs, key=lambda o: o[0]):
        scene.alpha_composite(im, (x, y))
        ip = im.load()
        ep = emis.load()
        for yy in range(im.height):
            for xx in range(im.width):
                c = ip[xx, yy]
                if c[3] == 255 and c[:3] in es and 0 <= x + xx < scene.width and 0 <= y + yy < scene.height:
                    ep[x + xx, y + yy] = 255
    lit = _light(scene, emis, lights)
    day = scene
    zoom = scale(lit.crop((200, 120, 584, 330)), 2)
    out = Image.new("RGBA", (max(day.width * 2, zoom.width), day.height + zoom.height + 16), BG)
    out.alpha_composite(day, (0, 0))
    out.alpha_composite(lit, (day.width, 0))
    out.alpha_composite(zoom, (0, day.height + 16))
    _save(out, "preview_items_dark.png")


def pillar_preview(old, col, rub):
    import pillar5 as P
    fr = [old[15]] + col + rub
    strip = Image.new("RGBA", (P.PW * len(fr), P.PH), BG)
    for i, f in enumerate(fr):
        strip.alpha_composite(f, (i * P.PW, 0))
    keys = [old[15], col[0], col[2], col[4], col[5], col[7], rub[1]]
    kz = Image.new("RGBA", (P.PW * len(keys), P.PH), BG)
    for i, f in enumerate(keys):
        kz.alpha_composite(f, (i * P.PW, 0))
    kz = scale(kz, 2)
    out = Image.new("RGBA", (max(strip.width, kz.width), strip.height + kz.height + 16), BG)
    out.alpha_composite(strip, (0, 0))
    out.alpha_composite(kz, (0, strip.height + 16))
    _save(out, "preview_pillar.png")

    # 어둠 목업: 보스방 바닥 + 3단 기둥 | 잔해 위를 걷는 주인공(잔해는 액터 아래 제안)
    floor = _floor(os.path.join(ROOT, "assets", "tiles", "v2", "stage1_hall.png"), 10, 8, ids=(35, 36, 37, 38, 0, 1))
    scene = floor.copy()
    pl, ppiv = _player()
    scene.alpha_composite(old[15], (60, 40))
    scene.alpha_composite(rub[1], (380, 40))
    scene.alpha_composite(pl, (460 - ppiv[0], 450 - ppiv[1]))     # 잔해 위
    scene.alpha_composite(pl, (240 - ppiv[0], 500 - ppiv[1]))
    emis = Image.new("L", scene.size, 0)
    lit = _light(scene, emis, [(460, 420, 320, (1.0, 0.86, 0.64), 1.25), (240, 470, 260, (1.0, 0.86, 0.64), 1.1)], ambient=0.3)
    out = Image.new("RGBA", (scene.width * 2, scene.height), BG)
    out.alpha_composite(scene, (0, 0))
    out.alpha_composite(lit, (scene.width, 0))
    _save(out, "preview_pillar_dark.png")
