"""P19 1-A 아트 공용 도구 (numpy) — 팔레트·디더 양자화·주기 노이즈·주기 보로노이.

단위: 도트(pixelScale 0.5 → 64 도트 = 1칸). 색은 lopad.json gray G · 1층 램프 A + v2 재질 블록 SL·WD·PL 만(새 색 없음).
모든 텍스처 함수는 (H, W) float 배열을 돌려주고, 마지막에 quant() 로 램프 칸 색을 고른다(칸 경계만 4×4 바이어 디더).
주기(period) 인자를 주면 가로·세로로 이어 붙였을 때 이음매가 없다(매크로 타일·물결 프레임용).
build 스크립트 전용 의존: numpy (pip install numpy).
"""
import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
U = 64

_pal = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))
_v2 = json.load(open(os.path.join(ROOT, "parts/art/work/v2_outer/palette_v2_proposal.json"), encoding="utf-8"))["blocks"]


def hx(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


G = [hx(c) for c in _pal["gray"]]
A = {16 + i: hx(c) for i, c in enumerate(_pal["floors"][0]["ramp"])}   # A[16]..A[27]
SL = [hx(c) for c in _v2["SL"]]
WD = [hx(c) for c in _v2["WD"]]
PL = [hx(c) for c in _v2["PL"]]
NT = [hx(c) for c in _v2["NT"]]
EMISSIVE = [hx(c) for c in ["#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0", "#ffffff", "#fff4dc"]]
ALLOWED = set(G) | set(A.values()) | set(SL) | set(WD) | set(PL) | set(NT) | set(EMISSIVE)

BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) + 0.5) / 16.0


def bayer(h, w, ox=0, oy=0):
    ys = (np.arange(h) + oy) % 4
    xs = (np.arange(w) + ox) % 4
    return BAYER[ys[:, None], xs[None, :]]


def quant(v, ramp, sharp=3.0, ox=0, oy=0):
    """v (H,W) 0..1 → RGB uint8 (H,W,3). 램프 칸 사이 경계만 디더(sharp 클수록 좁게)."""
    ramp = np.array(ramp, dtype=np.uint8)
    n = len(ramp)
    s = np.clip(v, 0, 0.99999) * (n - 1)
    i = np.floor(s).astype(int)
    f = s - i
    f = np.clip((f - 0.5) * sharp + 0.5, 0, 1)
    th = bayer(*v.shape, ox, oy)
    i = np.where(f > th, np.minimum(i + 1, n - 1), i)
    return ramp[i]


def rgba(rgb, alpha=None):
    h, w = rgb.shape[:2]
    a = np.full((h, w), 255, np.uint8) if alpha is None else np.where(alpha, 255, 0).astype(np.uint8)
    out = np.dstack([rgb, a])
    if alpha is not None:
        out[~alpha] = 0
    return Image.fromarray(out, "RGBA")


def lum(rgb):
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


# ---------------------------------------------------------------- 노이즈
def vnoise(h, w, cells_x, cells_y, seed, period=True):
    """값 노이즈(부드러운 보간). period=True 면 w×h 로 이어 붙여도 이음매 없음(격자 cells 가 정수)."""
    rng = np.random.default_rng(seed)
    g = rng.random((cells_y + 1, cells_x + 1)).astype(np.float32)
    if period:
        g[-1, :] = g[0, :]
        g[:, -1] = g[:, 0]
    ys = np.arange(h) / h * cells_y
    xs = np.arange(w) / w * cells_x
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    fy = ys - y0
    fx = xs - x0
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]
    b = g[y0][:, x0 + 1]
    c = g[y0 + 1][:, x0]
    d = g[y0 + 1][:, x0 + 1]
    top = a + (b - a) * fx[None, :]
    bot = c + (d - c) * fx[None, :]
    return top + (bot - top) * fy[:, None]


def fbm(h, w, base_cells, octaves, seed, gain=0.5, aspect=1.0):
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cx = int(base_cells * (2 ** o))
        cy = max(1, int(round(cx * h / w * aspect)))   # aspect > 1 → 가로로 긴 무늬
        out += amp * vnoise(h, w, cx, cy, seed + 97 * o)
        tot += amp
        amp *= gain
    return out / tot


# ---------------------------------------------------------------- 보로노이(주기)
def voronoi(h, w, pts, period=True, aniso=(1.0, 1.0), weights=None):
    """pts: [(x,y)] → (id, d1, d2) 배열. period 면 상하좌우로 감싸서 잰다. aniso = (sx, sy) 거리 축척."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d1 = np.full((h, w), 1e9, np.float32)
    d2 = np.full((h, w), 1e9, np.float32)
    idv = np.zeros((h, w), np.int32)
    for k, (px, py) in enumerate(pts):
        dx = np.abs(xx - px)
        dy = np.abs(yy - py)
        if period:
            dx = np.minimum(dx, w - dx)
            dy = np.minimum(dy, h - dy)
        d = np.sqrt((dx * aniso[0]) ** 2 + (dy * aniso[1]) ** 2)
        if weights is not None:
            d = d - weights[k]
        closer = d < d1
        d2 = np.where(closer, d1, np.minimum(d2, d))
        idv = np.where(closer, k, idv)
        d1 = np.where(closer, d, d1)
    return idv, d1, d2


def relax(pts, w, h, iters, seed=0, sample=4):
    """로이드 완화(주기) — 돌 크기를 고르게."""
    pts = [tuple(p) for p in pts]
    for _ in range(iters):
        hh, ww = h // sample, w // sample
        sp = [(x / sample, y / sample) for x, y in pts]
        idv, _, _ = voronoi(hh, ww, sp)
        yy, xx = np.mgrid[0:hh, 0:ww]
        new = []
        for k, (px, py) in enumerate(sp):
            m = idv == k
            if not m.any():
                new.append(pts[k]); continue
            # 원형 평균(주기 좌표)
            ax = np.angle(np.mean(np.exp(1j * 2 * np.pi * xx[m] / ww))) / (2 * np.pi) * ww % ww
            ay = np.angle(np.mean(np.exp(1j * 2 * np.pi * yy[m] / hh))) / (2 * np.pi) * hh % hh
            new.append((ax * sample, ay * sample))
        pts = new
    return pts


def jitter_grid(w, h, nx, ny, jit, seed, stagger=0.0):
    rng = np.random.default_rng(seed)
    pts = []
    for j in range(ny):
        for i in range(nx):
            ox = (stagger * (j % 2)) * w / nx
            pts.append((((i + 0.5) * w / nx + ox + rng.uniform(-jit, jit) * w / nx) % w,
                        ((j + 0.5) * h / ny + rng.uniform(-jit, jit) * h / ny) % h))
    return pts


def shift_wrap(a, dx, dy):
    return np.roll(np.roll(a, dy, axis=0), dx, axis=1)


# ---------------------------------------------------------------- 시트·저장
def save(im, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, optimize=True)


def dump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def off_palette(im):
    a = np.asarray(im.convert("RGBA"))
    cs = {tuple(c[:3]) for c in a.reshape(-1, 4) if c[3] > 0}
    return cs - ALLOWED


def tex_tiles(arr_rgba, cols):
    """(H,W,4) 배열 → 64 칸 목록(행 우선)."""
    h, w = arr_rgba.shape[:2]
    out = []
    for ty in range(h // U):
        for tx in range(w // U):
            out.append(Image.fromarray(np.ascontiguousarray(arr_rgba[ty * U:(ty + 1) * U, tx * U:(tx + 1) * U]), "RGBA"))
    return out
