"""61라운드 무기 그림 요청 공용 — 무기 fx v3 팔레트·검사·시트 쓰기(boss61/k61 · bundle2/b2 import 만)."""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
sys.path.insert(0, os.path.join(WORK, "boss61"))
sys.path.insert(0, os.path.join(WORK, "atlas57"))

import k61  # noqa: E402
from k61 import Cv, b2, Rand  # noqa: E402,F401
import gridsheet  # noqa: E402
from PIL import Image  # noqa: E402


def hx(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


X0, X1 = hx("#ffffff"), hx("#fff4dc")
A17, A18, A19, A21, A23, A25, A26 = [hx(c) for c in ("#3f271d", "#653b24", "#8b4d22", "#d67a11", "#e2a33c", "#eecc78", "#f4de9b")]
B0, B1, B2, B3 = [hx(c) for c in ("#2a1e17", "#3b2a1f", "#4f3828", "#664a33")]
S0, S1, S2, S3 = [hx(c) for c in ("#45403b", "#5c554e", "#756c62", "#90857a")]
HERO_PAL = {"#141516", "#14161c", "#1d2028", "#212224", "#272b35", "#2a1e17", "#2f3033", "#3b2a1f", "#3e3f42", "#3f271d",
            "#3f4552", "#45403b", "#4d4f52", "#4e5563", "#4f3828", "#5c554e", "#5c5e62", "#626a78", "#653b24", "#664a33",
            "#6c6f73", "#756c62", "#7d8084", "#8b4d22", "#8e9195", "#90857a", "#d67a11", "#e2a33c", "#eecc78", "#f4de9b"}
ALLOWED = {hx(c)[:3] for c in HERO_PAL} | {X0[:3], X1[:3]}
GLOW = {X0[:3], X1[:3], A26[:3]}
COLOR_MAX = 14
SPR = os.path.join(ROOT, "assets", "sprites")


def check_weapon_fx(name, rows, glow_cols, color_max=COLOR_MAX):
    """무기 fx v3 규칙: 주인공 30색 + X0/X1 · 14색 이하 · 반투명 0 · 가장자리 0 · glowFrames 밖 X0/X1/A26 없음."""
    cols = set()
    for j, row in enumerate(rows):
        for i, im in enumerate(row):
            k61.check_frames([im], "%s[%d,%d]" % (name, j, i))
            c = {p[:3] for p in im.getdata() if p[3]}
            cols |= c
            if i not in glow_cols:
                bad = c & GLOW
                assert not bad, (name, j, i, "glow outside glowFrames", bad)
    bad = cols - ALLOWED
    assert not bad, (name, "palette", bad)
    assert len(cols) <= color_max, (name, len(cols))
    return len(cols)


PREV = os.path.join(HERE, "prev")


def _src_json(cat, name):
    """고치기 전 원본(prev/ 보관본)이 있으면 그것을, 없으면 assets 현재 시트 — 다시 빌드해도 덧칠이 겹치지 않게."""
    p = os.path.join(PREV, cat, "v3", name + ".json")
    return p if os.path.exists(p) else os.path.join(SPR, cat, "v3", name + ".json")


def old_meta(cat, name):
    return gridsheet.load_meta(_src_json(cat, name))


def old_grid(cat, name):
    return gridsheet.open_grid(_src_json(cat, name))


def write(cat, name, rows, fw, fh, meta, ms, loop):
    meta = dict(meta)
    for k in ("image", "frameWidth", "frameHeight", "frames", "framesPerDirection", "frameDurationsMs", "loop"):
        meta.pop(k, None)
    if "directions" not in meta:
        meta["directions"] = ["any"]
    flat = [f for r in rows for f in r]
    return b2.write_sheet(cat, name, flat, fw, fh, meta, rows=len(rows), durations=ms, loop=loop)


def preview_rows(path, rows, k=2, bg=(26, 24, 30)):
    fw, fh = rows[0][0].size
    im = Image.new("RGBA", (fw * len(rows[0]), fh * len(rows)), bg + (255,))
    for j, r in enumerate(rows):
        for i, f in enumerate(r):
            im.alpha_composite(f, (i * fw, j * fh))
    while k > 1 and max(im.size) * k > 8000:
        k -= 1
    im = k61.scale(im, k)
    if max(im.size) > 8000:
        s = 8000.0 / max(im.size)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.NEAREST)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.convert("RGB").save(path)
    return path


def rot(dx, dy, deg):
    a = math.radians(deg)
    return dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
