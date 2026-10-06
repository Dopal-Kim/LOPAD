"""미리보기 도구 — 전(git HEAD 사본 폴더)/후(assets) 비교. 긴 변 8000 이하."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
sys.path.insert(0, os.path.join(WORK, "atlas57"))
import gridsheet  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SPR = os.path.join(ROOT, "assets", "sprites")
BG = (34, 31, 38)
BG_LIGHT = (92, 88, 82)

_cache = {}


def sheet(root, rel):
    """rel = 'weapons/v3/katana_rise' → (meta, grid RGBA)."""
    k = (root, rel)
    if k not in _cache:
        jp = os.path.join(root, rel + ".json")
        if not os.path.exists(jp):
            jp2 = os.path.join(root, rel + ".png")
            _cache[k] = (None, Image.open(jp2).convert("RGBA"))
        else:
            _cache[k] = (gridsheet.load_meta(jp), gridsheet.open_grid(jp))
    return _cache[k]


def frame(root, rel, row, col):
    m, g = sheet(root, rel)
    fw, fh = m["frameWidth"], m["frameHeight"]
    return g.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh)), m


def compose(root, body_rel, layers, row, col, bg=BG, box=(0, 0, 192, 192)):
    """몸(96×144, 피벗 48,138) + 무기 오버레이들(피벗 기준 정렬) → 192 판."""
    cv = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), bg + (255,))
    bodies = []
    if body_rel:
        b, bm = frame(root, body_rel, row, col)
        bodies.append((b, (bm["pivot"]["x"], bm["pivot"]["y"]) if "pivot" in bm else (48, 138)))
    for rel in layers:
        try:
            w, wm = frame(root, rel, row, col)
        except Exception:
            continue
        piv = wm.get("pivot", {"x": 96, "y": 186})
        bodies.append((w, (piv["x"], piv["y"])))
    for im, (px, py) in bodies:
        cv.alpha_composite(im, (96 - px - box[0], 186 - py - box[1]))
    return cv


def scale(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def grid(cells, cols, pad=6, bg=(12, 12, 14), labels=None):
    w = max(c.width for c in cells)
    h = max(c.height for c in cells)
    rows = (len(cells) + cols - 1) // cols
    lh = 14 if labels else 0
    out = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad + lh) + pad), bg)
    dr = ImageDraw.Draw(out)
    for i, c in enumerate(cells):
        x = pad + (i % cols) * (w + pad)
        y = pad + (i // cols) * (h + pad + lh)
        out.paste(c.convert("RGB"), (x, y + lh))
        if labels:
            dr.text((x + 2, y), labels[i], fill=(230, 220, 200))
    return out


def stack(ims, pad=10, bg=(12, 12, 14), titles=None):
    w = max(i.width for i in ims)
    th = 16 if titles else 0
    out = Image.new("RGB", (w, sum(i.height + pad + th for i in ims)), bg)
    dr = ImageDraw.Draw(out)
    y = 0
    for k, i in enumerate(ims):
        if titles:
            dr.text((4, y + 2), titles[k], fill=(255, 230, 160))
        out.paste(i.convert("RGB"), (0, y + th))
        y += i.height + pad + th
    return out


def fit(im, maxside=8000):
    if max(im.size) <= maxside:
        return im
    s = maxside / max(im.size)
    return im.resize((int(im.width * s), int(im.height * s)), Image.NEAREST)


def strip(root, rel, row, k=1, bg=BG, crop=None):
    m, g = sheet(root, rel)
    fw, fh = m["frameWidth"], m["frameHeight"]
    n = g.width // fw
    out = Image.new("RGBA", (fw * n, fh), bg + (255,))
    out.alpha_composite(g.crop((0, row * fh, fw * n, (row + 1) * fh)))
    if crop:
        out = out.crop(crop)
    return scale(out, k)
