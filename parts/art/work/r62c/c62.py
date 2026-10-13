"""62 루프 3 아트(r62c) 공용 — 경로·팔레트·작은 그리기 도구. Pillow 만, 결정적."""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets", "sprites")
PAINT = os.path.join(SPR, "paint")
PAL = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))
SRC = "parts/art/work/r62c/build.py (62 루프 3 · P17)"
SCRATCH = os.environ.get("R62C_SCRATCH", os.path.join(HERE, "_scratch"))


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexc(c):
    return "#%02x%02x%02x" % tuple(c[:3])


GRAY = [hx(c) for c in PAL["gray"]]
AMB = [hx(c) for c in PAL["floors"][0]["ramp"]]     # 1층 램프 '잔' 16~27
RED = [hx(c) for c in PAL["floors"][6]["ramp"]]     # '적' (엘리트 깃발)
GHOST = [hx(c) for c in PAL["floors"][4]["ramp"]]   # '귀' (저주 — 61 단계 6 그림 결에 둘째 강조 축으로)
SEPIA = [hx(c) for c in PAL["ui"]["ramp"]]


def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v
