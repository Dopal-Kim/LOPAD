"""미리보기: 1층 어두운 바닥(연회장 바닥 타일 0~3 을 어둠 0.5 로 눌러 깜) 위에 시트 칸을 1배(= 1080p 화면 크기)로 늘어놓는다.
줄마다 이름·칸 ms. 피벗 자리에 작은 십자(회색). 회전 시트는 오른쪽을 본 그대로."""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
_BG = {}


def floor_bg(w, h, dark=0.5):
    key = (w, h, dark)
    if key not in _BG:
        ts = Image.open(os.path.join(ROOT, "assets", "tiles", "v2", "stage1_hall.png")).convert("RGBA")
        tiles = [ts.crop((i * 64, 0, i * 64 + 64, 64)) for i in range(4)]
        bg = Image.new("RGBA", (w, h))
        for y in range(0, h, 64):
            for x in range(0, w, 64):
                bg.paste(tiles[((x // 64) * 7 + (y // 64) * 3) % 4], (x, y))
        px = bg.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                px[x, y] = (int(r * dark), int(g * dark), int(b * dark), 255)
        _BG[key] = bg
    return _BG[key].copy()


def sheets(items, out, title="", scale=1):
    pad = 6
    lab = 14
    rows = []
    W = 0
    for name, ims, meta in items:
        fw, fh = ims[0].size
        w = (fw + pad) * len(ims) + pad
        W = max(W, w)
        rows.append((name, ims, meta, fw, fh))
    H = sum(fh + lab + pad for *_, fh in rows) + pad
    canvas = Image.new("RGBA", (W, H), (12, 10, 10, 255))
    d = ImageDraw.Draw(canvas)
    y = pad
    for name, ims, meta, fw, fh in rows:
        d.text((pad, y), "%s  %s  %s%s" % (name, "x".join(map(str, (fw, fh))), meta["frameDurationsMs"],
                                            "  rot" if meta.get("rotate") else ""), fill=(200, 200, 200, 255))
        y += lab
        bg = floor_bg(fw, fh)
        for i, im in enumerate(ims):
            x = pad + i * (fw + pad)
            tile = bg.copy()
            tile.alpha_composite(im)
            canvas.paste(tile, (x, y))
            pv = meta["pivot"]
            for k in (-2, -1, 1, 2):
                canvas.putpixel((x + pv["x"] + k, y + pv["y"]), (120, 200, 120, 255))
                canvas.putpixel((x + pv["x"], y + pv["y"] + k), (120, 200, 120, 255))
            if i in meta.get("glowFrames", []):
                d.rectangle((x, y, x + fw - 1, y + fh - 1), outline=(240, 220, 160, 255))
        y += fh + pad
    if scale != 1:
        canvas = canvas.resize((canvas.width * scale, canvas.height * scale), Image.NEAREST)
    canvas.save(out)
    return out


_ACT = {}


def actor(kind):
    """주인공(player_idle down f0) / 적(dummy_idle down f0) 정지 그림 + 피벗."""
    if kind not in _ACT:
        import sys
        sys.path.insert(0, os.path.join(ROOT, "parts", "art", "work", "atlas57"))
        import gridsheet
        rel = "player/v3/player_idle" if kind == "hero" else "enemies/v3/dummy_idle"
        jp = os.path.join(ROOT, "assets", "sprites", rel + ".json")
        m = gridsheet.load_meta(jp)
        g = gridsheet.open_grid(jp)
        im = g.crop((0, 0, m["frameWidth"], m["frameHeight"]))
        _ACT[kind] = (im, (m["pivot"]["x"], m["pivot"]["y"]))
    return _ACT[kind]


def overview(items, out, cell=300):
    """시트마다 대표 칸(첫 glowFrame, 없으면 가운데)을 실제 쓰임처럼 배치: 주인공/적 정지 그림 + 앵커에 fx 피벗.
    회전 시트는 0° · 90° · 210° 세 칸."""
    cells = []
    for name, ims, meta in items:
        n = len(ims)
        g = meta.get("glowFrames") or []
        k = g[0] if g else min(n - 1, n // 2)
        angs = [0, 90, 210] if meta.get("rotate") else [0]
        for a in angs:
            cells.append((name, ims[k], meta, k, a))
    cols = 5
    rows = (len(cells) + cols - 1) // cols
    lab = 14
    canvas = Image.new("RGBA", (cols * cell, rows * (cell + lab)), (12, 10, 10, 255))
    d = ImageDraw.Draw(canvas)
    for i, (name, im, meta, k, a) in enumerate(cells):
        cx0, cy0 = (i % cols) * cell, (i // cols) * (cell + lab)
        tile = floor_bg(cell, cell)
        anc = meta["anchor"]
        ax, ay = cell // 2, int(cell * 0.62)
        who = {"player_pivot": "hero", "mob_feet": "enemy", "hitbox_center": "enemy", "contact": "enemy"}.get(anc)
        if anc == "floor" and "주인공" in meta.get("anchorNote", ""):
            who = "hero"
        if who:
            body, (bx, by) = actor(who)
            tile.alpha_composite(body, (ax - bx, ay - by))
        px, py = meta["pivot"]["x"], meta["pivot"]["y"]
        fy = ay - 40 if anc == "hitbox_center" else ay
        if anc == "contact":
            fy = ay - 40
        if meta.get("anchorOffsetDots"):
            fy += meta["anchorOffsetDots"]["y"]
        f = im
        if a:
            big = Image.new("RGBA", (im.width * 3, im.height * 3), (0, 0, 0, 0))
            big.alpha_composite(im, (im.width, im.height))
            f = big.rotate(-a, resample=Image.NEAREST, center=(im.width + px, im.height + py))
            px, py = im.width + px, im.height + py
        _paste_clip(tile, f, int(ax - px), int(fy - py))
        canvas.paste(tile, (cx0, cy0 + lab))
        d.text((cx0 + 3, cy0), "%s f%d%s" % (name.replace("trait_", ""), k, (" %d°" % a) if meta.get("rotate") else ""), fill=(200, 200, 200, 255))
    canvas.save(out)
    return out


def _paste_clip(dst, src, x, y):
    sx0, sy0 = max(0, -x), max(0, -y)
    crop = src.crop((sx0, sy0, src.width, src.height))
    dx, dy = max(0, x), max(0, y)
    w = min(crop.width, dst.width - dx)
    h = min(crop.height, dst.height - dy)
    if w > 0 and h > 0:
        dst.alpha_composite(crop.crop((0, 0, w, h)), (dx, dy))
