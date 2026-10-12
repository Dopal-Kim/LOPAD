"""62a 공용 — 경로·팔레트·잡음(타이틀 62 kit 재사용)."""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("title62_kit", os.path.join(WORK, "title62", "kit.py"))
TK = importlib.util.module_from_spec(_spec)   # 타이틀 62 공용 도구(이름 'kit' 이 v2_outer 와 겹쳐 경로로 읽음)
_spec.loader.exec_module(TK)

PAL = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))
SPR = os.path.join(ROOT, "assets", "sprites")
TILES = os.path.join(ROOT, "assets", "tiles")


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexc(c):
    return "#%02x%02x%02x" % tuple(c[:3])


G = [hx(c) for c in PAL["gray"]]
A = [hx(c) for c in PAL["floors"][0]["ramp"]]
S = [hx(c) for c in PAL["ui"]["ramp"]]
RED = [hx(c) for c in PAL["floors"][6]["ramp"]]
WHITE = (255, 255, 255)
CORE = [hx(c) for c in PAL["fx"]["core"]]

Noise, Fbm, band, poly, stroke_poly, edges, up = TK.Noise, TK.Fbm, TK.band, TK.poly, TK.stroke_poly, TK.edges, TK.up


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def mask(w, h):
    m = Image.new("L", (w, h), 0)
    return m, ImageDraw.Draw(m)


def normals(m, blur):
    """마스크 흐림 기울기 → 바깥 법선(nx, ny) 함수 + 높이 접근."""
    bl = m.filter(ImageFilter.GaussianBlur(blur)) if blur else m
    bp = bl.load()
    w, h = m.size

    def n(x, y):
        gx = bp[min(w - 1, x + 1), y] - bp[max(0, x - 1), y]
        gy = bp[x, min(h - 1, y + 1)] - bp[x, max(0, y - 1)]
        return gx, gy, bp[x, y]
    return n


def colors_of(im):
    cs = im.convert("RGBA").getcolors(1 << 22) or []
    return {c[:3] for n, c in cs if c[3] > 0}


def save(im, path, **kw):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, optimize=True, **kw)


def dump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")
