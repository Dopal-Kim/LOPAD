"""P19 미리보기 — 몸 + 무기 오버레이(오프셋 적용) 합성, 전/후 비교 띠·GIF."""
import os

from PIL import Image, ImageDraw

import body19 as B

BG = (34, 36, 42, 255)
HERE = B.HERE


def overlay_cell(rel, d, col, off=(0, 0)):
    meta, im = B.load_grid(rel)
    row = meta["directions"].index(d)
    c = B.cell(meta, im, row, col)
    px, py = meta["pivot"]["x"], meta["pivot"]["y"]
    return c, (48 - px + off[0], 138 - py + off[1])   # 몸 시트 좌표계에서 오버레이 왼위 모서리


_cache = {}


def overlay_cell_c(rel, d, col, off=(0, 0)):
    if rel not in _cache:
        _cache[rel] = B.load_grid(rel)
    meta, im = _cache[rel]
    row = meta["directions"].index(d)
    c = B.cell(meta, im, row, col)
    return c, (48 - meta["pivot"]["x"] + off[0], 138 - meta["pivot"]["y"] + off[1])


def compose(body_img, overlays=(), pad=48, bg=BG, under=()):
    """body_img 96×144 → (96+2pad)×(144+2pad) 캔버스. overlays = [(img, (x, y))] 몸 좌표 왼위."""
    W, H = 96 + 2 * pad, 144 + 2 * pad
    can = Image.new("RGBA", (W, H), bg)
    for im, (x, y) in under:
        can.alpha_composite(im, (x + pad, y + pad)) if x + pad >= 0 and y + pad >= 0 else _paste(can, im, x + pad, y + pad)
    can.alpha_composite(body_img, (pad, pad))
    for im, (x, y) in overlays:
        _paste(can, im, x + pad, y + pad)
    return can


def _paste(can, im, x, y):
    tmp = Image.new("RGBA", can.size, (0, 0, 0, 0))
    tmp.paste(im, (x, y), im)
    can.alpha_composite(tmp)


def strip(cells, scale=2, gap=0):
    W = sum(c.width for c in cells) + gap * (len(cells) - 1)
    H = max(c.height for c in cells)
    out = Image.new("RGBA", (W, H), BG)
    x = 0
    for c in cells:
        out.paste(c, (x, 0))
        x += c.width + gap
    return out.resize((out.width * scale, out.height * scale), Image.NEAREST)


def stack(rows, label=None):
    W = max(r.width for r in rows)
    H = sum(r.height for r in rows)
    out = Image.new("RGBA", (W, H), BG)
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    return out


def gif(frames, ms, path, scale=3):
    fr = [f.resize((f.width * scale, f.height * scale), Image.NEAREST).convert("P", palette=Image.ADAPTIVE, colors=255) for f in frames]
    fr[0].save(path, save_all=True, append_images=fr[1:], duration=list(ms), loop=0, disposal=2)


def label(im, text):
    d = ImageDraw.Draw(im)
    d.text((4, 2), text, fill=(230, 200, 120, 255))
    return im
