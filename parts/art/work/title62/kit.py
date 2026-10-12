"""62 타이틀 — 공용 도구 (Pillow 만, numpy 없음, 결정적).

논리 캔버스 640×360 에 그린 뒤 3배 최근접 확대 → 1920×1080 (도트 1칸 = 3px).
색은 LOPAD 팔레트(무채 G00~G15 + 1층 '잔' 호박 램프 A0~A11) + 무기 색 4종(계약 art §28 주 색)만.
붓 결: 띠 경계를 가로로 늘인 잡음으로 흔들어 '가로 붓질' 처럼 보이게 한다(디더 격자 없음).
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
PAL = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))

W, H, K = 640, 360, 3          # 논리 크기 · 배율


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


G = [hx(c) for c in PAL["gray"]]                 # G00..G15
A = [hx(c) for c in PAL["floors"][0]["ramp"]]    # A0..A11 (1층 호박)
WEAPON = {                                       # 계약 art §28 주 색 (61 단계 6)
    "katana": hx("#8fe3ff"),
    "greatsword": hx("#ff5a2a"),
    "dagger": hx("#c060ff"),
    "bow": hx("#40e0a0"),
}


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def weapon_ramp(name):
    """무기 색 3단: 어두운(먹과 섞음) · 주 색 · 밝은(흰빛 쪽)."""
    c = WEAPON[name]
    return [mix(G[1], c, 0.45), c, mix(c, (255, 255, 255), 0.55)]


# ------------------------------------------------------------------ 잡음
class Noise:
    """격자 값 잡음(부드러운 보간). 가로 반복(wrap) 가능."""

    def __init__(self, seed, gw, gh, wrap_x=False):
        r = random.Random(seed)
        self.gw, self.gh, self.wrap = gw, gh, wrap_x
        self.v = [[r.random() for _ in range(gw + 1)] for _ in range(gh + 1)]
        if wrap_x:
            for row in self.v:
                row[gw] = row[0]

    def at(self, u, v):
        """u, v ∈ [0,1] (u 는 wrap 이면 주기 1)."""
        x = u * self.gw
        y = min(max(v, 0.0), 0.99999) * self.gh
        if self.wrap:
            x = x % self.gw
        else:
            x = min(max(x, 0.0), self.gw - 1e-5)
        i, j = int(x), int(y)
        fx, fy = x - i, y - j
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        r0, r1 = self.v[j], self.v[j + 1]
        a = r0[i] + (r0[i + 1] - r0[i]) * fx
        b = r1[i] + (r1[i + 1] - r1[i]) * fx
        return a + (b - a) * fy


class Fbm:
    def __init__(self, seed, base_w, base_h, octaves=4, wrap_x=False):
        self.oct = [Noise(seed * 31 + o, base_w * 2 ** o, base_h * 2 ** o, wrap_x) for o in range(octaves)]

    def at(self, u, v):
        s, amp, tot = 0.0, 1.0, 0.0
        for n in self.oct:
            s += n.at(u, v) * amp
            tot += amp
            amp *= 0.5
        return s / tot


# ------------------------------------------------------------------ 색 고르기 (붓 결 띠)
def band(ramp, t, jitter):
    """t ∈ [0,1] 을 램프 인덱스로, jitter(-0.5..0.5)로 경계를 흔든다(디더 격자 대신 붓 결)."""
    n = len(ramp)
    x = t * (n - 1) + jitter
    i = int(math.floor(x + 0.5))
    return ramp[max(0, min(n - 1, i))]


# ------------------------------------------------------------------ 도형
def poly(d, pts, fill):
    d.polygon([(round(x), round(y)) for x, y in pts], fill=fill)


def stroke_poly(p0, p1, w0, w1=None):
    """p0 → p1 굵기 w0 → w1 사다리꼴(붓 획/막대)."""
    w1 = w0 if w1 is None else w1
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    return [(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2), (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
            (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2), (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)]


def mask_new(w=W, h=H):
    return Image.new("L", (w, h), 0)


def mask_has(m, x, y):
    if 0 <= x < m.width and 0 <= y < m.height:
        return m.getpixel((x, y)) > 127
    return False


def edges(m):
    """마스크 안쪽 1칸 가장자리: 방향별 집합 {'l','r','t','b'} → [(x,y)]."""
    px = m.load()
    w, h = m.size
    out = {"l": [], "r": [], "t": [], "b": []}
    for y in range(h):
        for x in range(w):
            if px[x, y] < 128:
                continue
            if x == 0 or px[x - 1, y] < 128:
                out["l"].append((x, y))
            if x == w - 1 or px[x + 1, y] < 128:
                out["r"].append((x, y))
            if y == 0 or px[x, y - 1] < 128:
                out["t"].append((x, y))
            if y == h - 1 or px[x, y + 1] < 128:
                out["b"].append((x, y))
    return out


def up(im, k=K):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def colors_used(im):
    cs = im.getcolors(1 << 20)
    return len(cs) if cs else None
