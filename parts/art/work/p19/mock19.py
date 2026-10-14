"""P19 1-A 형태별 대표 화면 목업 + 조명 + 휘도 측정.

- 형태 틀 7종(+ 보스·황무지) 마스크를 아트 쪽에서 계약 §3 문자로 직접 만든다(시스템 S2 의 실제 data/arenas 는 읽지 않음 — 목업 전용).
- 타일셋 v4(JSON v4 블록)의 규칙대로 3겹 바닥·벽·낙하·높은 단을 깔고, 소품·적·주인공(기존 v3 시트)을 Y 정렬해 얹는다.
- 조명 모델(계약 §9·border 목업과 같은 곱하기 모델): 빛 = ambient + Σ 광원·(1−d²)²·세기, 결과 = 바탕 × min(빛, 1.6), 발광색 픽셀은 조명 무시.
- 화면: 카메라 1.75(탐색, 34.3×19.3칸) 와 1.6(전투, 37.5×21.1칸) 두 배율로 1920×1080 렌더 → 평균 휘도(Rec.709)·거의 검정(L<25) 비율.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "../atlas57"))
import gridsheet  # noqa: E402
from tk import ROOT, EMISSIVE, hx, U, dump  # noqa: E402

T = U
TILES = os.path.join(ROOT, "assets/tiles/v4")
SPR = os.path.join(ROOT, "assets/sprites")
FLOORISH = set(".SPhDc")


# ================================================================ 형태 틀(목업)
def _blank(w, h, ch="#"):
    return [[ch] * w for _ in range(h)]


def _fill(g, x0, y0, x1, y1, ch):
    for y in range(max(0, y0), min(len(g), y1)):
        for x in range(max(0, x0), min(len(g[0]), x1)):
            g[y][x] = ch


def shape_plaza():
    w, h = 48, 32
    g = _blank(w, h)
    cx, cy = 24, 17
    for y in range(h):
        for x in range(w):
            if ((x - cx) / 19.5) ** 2 + ((y - cy) / 13) ** 2 <= 1:
                g[y][x] = "."
    for (x0, y0, x1, y1) in ((21, 0, 28, 6), (21, 28, 28, 32), (0, 14, 6, 21), (42, 14, 48, 21)):
        _fill(g, x0, y0, x1, y1, ".")
    _fill(g, 22, 15, 27, 20, "c")    # 분수(무대 중심 — 소품이 덮음)
    return g, dict(center=(24.5, 17.5), stone_r=7.5, doors=[(24, 3), (24, 30), (2, 17), (46, 17)], region="outer",
                   name="원형 광장(술샘 분수)")


def shape_dock():
    w, h = 56, 28
    g = _blank(w, h)
    _fill(g, 1, 3, 55, 17, ".")
    _fill(g, 1, 17, 55, 23, "~")
    _fill(g, 1, 23, 55, 27, ".")
    for bx in (10, 27, 44):
        _fill(g, bx, 17, bx + 3, 23, "=")
    return g, dict(center=(27.5, 10), stone_r=0, doors=[(2, 10), (54, 10), (28, 25)], region="brewery", name="부두 하역장")


def shape_cross():
    w, h = 48, 32
    g = _blank(w, h)
    _fill(g, 16, 10, 34, 24, ".")
    _fill(g, 20, 3, 29, 10, "."); _fill(g, 20, 24, 29, 31, ".")
    _fill(g, 1, 13, 16, 21, "."); _fill(g, 34, 13, 47, 21, ".")
    return g, dict(center=(24.5, 17), stone_r=5, doors=[(24, 4), (24, 30), (2, 17), (46, 17)], region="outer", name="십자로")


def shape_terrace():
    w, h = 48, 32
    g = _blank(w, h)
    _fill(g, 1, 3, 47, 31, ".")
    _fill(g, 1, 3, 47, 14, "^")
    for sx in (9, 34):
        _fill(g, sx, 14, sx + 4, 15, "/")
    return g, dict(center=(24, 18), stone_r=0, stone_on="^", doors=[(2, 8), (46, 22), (24, 30)], region="gate", name="두 단 테라스")


def shape_cellar():
    w, h = 48, 30
    g = _blank(w, h)
    _fill(g, 1, 3, 47, 29, ".")
    for x in range(7, 44, 8):
        for y in (9, 20):
            _fill(g, x, y, x + 2, y + 2, "c")
    return g, dict(center=(24, 16), stone_r=0, doors=[(2, 15), (46, 15)], region="brewery", name="술창고")


def shape_rampart():
    w, h = 60, 26
    g = _blank(w, h)
    _fill(g, 1, 3, 59, 25, "~")
    _fill(g, 1, 10, 59, 18, ".")
    _fill(g, 22, 5, 30, 10, "."); _fill(g, 38, 18, 46, 23, ".")   # 망루 돌출
    return g, dict(center=(30, 14), stone_r=0, doors=[(2, 14), (58, 14)], region="gate", name="성벽 위 회랑")


def shape_still():
    w, h = 50, 32
    g = _blank(w, h)
    _fill(g, 1, 3, 49, 31, ".")
    _fill(g, 30, 3, 49, 16, "#")          # L자
    for y in range(h):
        for x in range(w):
            d = ((x - 18) / 8.5) ** 2 + ((y - 20) / 6.5) ** 2
            if d <= 1 and g[y][x] == ".":
                g[y][x] = "~"
            if d <= 0.45:
                g[y][x] = "."
    _fill(g, 9, 19, 12, 22, "="); _fill(g, 24, 19, 28, 22, "=")
    for y in range(h):
        for x in range(w):
            if g[y][x] == "=":
                pass
    return g, dict(center=(18, 20), stone_r=3.5, doors=[(2, 8), (46, 24)], region="brewery", name="증류소 마당")


def shape_boss():
    w, h = 56, 34
    g = _blank(w, h)
    for y in range(h):
        for x in range(w):
            if ((x - 28) / 26.5) ** 2 + ((y - 18) / 15.5) ** 2 <= 1 and y >= 3:
                g[y][x] = "."
    for (x, y) in ((16, 11), (38, 11), (16, 24), (38, 24)):
        _fill(g, x, y, x + 2, y + 2, "c")
    return g, dict(center=(28, 18), stone_r=8, doors=[(28, 32)], region="hall", name="만취의 연회장(보스)")


def shape_waste():
    w, h = 48, 30
    g = _blank(w, h)
    _fill(g, 1, 3, 47, 29, ".")
    for y in range(3, 29):
        x0 = int(30 + (y - 3) * 0.35 + 2 * math.sin(y * 0.6))
        _fill(g, x0, y, x0 + 4, y + 1, "~")
    _fill(g, 32, 14, 40, 16, "=")
    return g, dict(center=(18, 16), stone_r=4, doors=[(2, 16), (46, 16)], region="waste", name="버려진 길(황무지)")


SHAPES = [("plaza", shape_plaza), ("dock", shape_dock), ("cross", shape_cross), ("terrace", shape_terrace),
          ("cellar", shape_cellar), ("rampart", shape_rampart), ("still", shape_still), ("boss", shape_boss), ("waste", shape_waste)]


# ================================================================ 타일·스프라이트 로드
class Tileset:
    def __init__(self, region):
        self.j = json.load(open(os.path.join(TILES, f"stage1_{region}.json"), encoding="utf-8"))
        self.im = Image.open(os.path.join(TILES, f"stage1_{region}.png")).convert("RGBA")
        self.a = np.asarray(self.im)
        self.v4 = self.j["v4"]

    def t(self, i):
        c = self.j["columns"]
        return self.a[(i // c) * T:(i // c + 1) * T, (i % c) * T:(i % c + 1) * T]


_spr_cache = {}


def sprite(rel, frame=0):
    """assets/sprites 기준 이름 → (RGBA 프레임, 피벗)."""
    if rel not in _spr_cache:
        jp = os.path.join(SPR, rel + ".json")
        m = gridsheet.load_meta(jp)
        _spr_cache[rel] = (m, gridsheet.open_grid(jp))
    m, g = _spr_cache[rel]
    fw, fh = m["frameWidth"], m["frameHeight"]
    cols = g.width // fw
    c, r = frame % cols, frame // cols
    im = g.crop((c * fw, r * fh, c * fw + fw, r * fh + fh))
    pv = m.get("pivot", {"x": fw // 2, "y": fh - 4})
    return im, (pv["x"], pv["y"]), m


def blit(dst, src, x, y):
    """dst (H,W,4) uint8 에 src (h,w,4) 알파 합성(불투명 픽셀만)."""
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    m = s[..., 3] > 127
    d = dst[y0:y1, x0:x1]
    d[m] = s[m]


def masked(tile, mask):
    out = tile.copy()
    out[mask[..., 3] == 0] = 0
    return out


# ================================================================ 바닥 깔기
def bfs_path(g, a, b):
    H, W = len(g), len(g[0])
    from collections import deque
    prev = {a: None}
    q = deque([a])
    ok = lambda c: g[c[1]][c[0]] in FLOORISH or g[c[1]][c[0]] in "=^/"
    while q:
        c = q.popleft()
        if c == b:
            break
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + d[0], c[1] + d[1])
            if 0 <= n[0] < W and 0 <= n[1] < H and n not in prev and ok(n):
                prev[n] = c; q.append(n)
    path, c = [], b
    while c is not None and c in prev:
        path.append(c); c = prev[c]
    return path


def compose(g, info, ts, seed=7):
    H, W = len(g), len(g[0])
    rng = np.random.default_rng(seed)
    v4 = ts.v4
    canvas = np.zeros((H * T, W * T, 4), np.uint8)
    canvas[..., 3] = 255
    canvas[..., :3] = (11, 12, 17)
    at = lambda x, y: g[y][x] if 0 <= x < W and 0 <= y < H else "#"
    is_floor = lambda c: c in FLOORISH or c in "^/"
    # 꼭짓점 재질
    dirtV = np.zeros((H + 1, W + 1), bool)
    stoneV = np.zeros((H + 1, W + 1), bool)
    cx, cy = info["center"]
    doors = info["doors"]
    path_cells = set()
    for d in doors:
        for c in bfs_path(g, d, (int(cx), int(cy))):
            path_cells.add(c)
    for (x, y) in list(path_cells):
        if rng.random() < 0.85:
            dirtV[y + 1, x + 1] = True
        if rng.random() < 0.35:
            dx, dy = rng.integers(-1, 2), rng.integers(-1, 2)
            dirtV[min(H, max(0, y + 1 + dy)), min(W, max(0, x + 1 + dx))] = True
    # 얼룩
    for _ in range(int(W * H * 0.006)):
        x, y = rng.integers(0, W), rng.integers(0, H)
        dirtV[y:y + 2, x:x + 2] = True
    if info.get("stone_r"):
        yy, xx = np.mgrid[0:H + 1, 0:W + 1]
        stoneV = ((xx - cx) ** 2 + ((yy - cy) * 1.15) ** 2) <= info["stone_r"] ** 2
    if info.get("stone_on"):
        ch = info["stone_on"]
        for y in range(1, H):
            for x in range(1, W):
                if sum(g[y + dy][x + dx] == ch for dy in (-1, 0) for dx in (-1, 0)) >= 3:
                    stoneV[y, x] = True
    ov = v4["overlays"]
    macro = v4["floor"]["macro"]
    ox, oy = int(rng.integers(0, 8)), int(rng.integers(0, 8))
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            px, py = x * T, y * T
            if is_floor(c):
                mi = ((y + oy) % 8) * 8 + (x + ox) % 8
                canvas[py:py + T, px:px + T] = ts.t(macro[mi])
                for name, V in (("dirt", dirtV), ("stone", stoneV)):
                    cfg = int(V[y, x]) | int(V[y, x + 1]) << 1 | int(V[y + 1, x]) << 2 | int(V[y + 1, x + 1]) << 3
                    if cfg:
                        o = ov[name]
                        blit(canvas, masked(ts.t(o["macro"][mi]), ts.t(o["mask"][cfg])), px, py)
                        blit(canvas, ts.t(o["rim"][cfg]), px, py)
            elif c in "~=":
                fr = v4["drop"]["fillRule"]
                if fr["kind"] == "water":
                    fi = v4["drop"]["fill"][(y % 2) * 2 + x % 2]
                else:
                    fi = v4["drop"]["fill"][(y % 4) * 4 + x % 4]
                canvas[py:py + T, px:px + T] = ts.t(fi)
    # 데칼
    dec = v4["decals"]["tiles"]
    for y in range(H):
        for x in range(W):
            if g[y][x] in ".S" and rng.random() < 0.11:
                blit(canvas, ts.t(dec[rng.integers(len(dec))]), x * T, y * T)
    # 벽 발치 그늘
    fs = v4["floorShadows"]
    for y in range(H):
        for x in range(W):
            if not is_floor(g[y][x]):
                continue
            n, w_, e_ = at(x, y - 1) == "#", at(x - 1, y) == "#", at(x + 1, y) == "#"
            if n:
                blit(canvas, ts.t(fs["n"]), x * T, y * T)
            if w_:
                blit(canvas, ts.t(fs["w"]), x * T, y * T)
            if e_:
                blit(canvas, ts.t(fs["e"]), x * T, y * T)
    # 높은 단
    tz = v4["terrace"]
    lowc = lambda c: c in FLOORISH
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c == "^":
                bits = (lowc(at(x, y - 1))) | (lowc(at(x + 1, y)) << 1) | ((lowc(at(x, y + 1)) and at(x, y + 1) != "/") << 2) | (lowc(at(x - 1, y)) << 3)
                if bits:
                    blit(canvas, ts.t(tz["lip"][bits]), x * T, y * T)
            elif lowc(c) and at(x, y - 1) == "^":
                l_ = lowc(at(x - 1, y)) and at(x - 1, y - 1) == "^"
                r_ = lowc(at(x + 1, y)) and at(x + 1, y - 1) == "^"
                k = "mid" if (l_ and r_) else "endL" if r_ else "endR" if l_ else "single"
                blit(canvas, ts.t(tz["face"][k]), x * T, y * T)
            elif c == "/":
                l_ = at(x - 1, y) == "/"
                r_ = at(x + 1, y) == "/"
                k = "mid" if (l_ and r_) else "endL" if r_ else "endR" if l_ else "single"
                blit(canvas, ts.t(tz["stairS"][k]), x * T, y * T)
    # 낙하 둑·다리·난간
    dr = v4["drop"]
    land = lambda c: c not in "~="
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c == "~":
                bits = land(at(x, y - 1)) | (land(at(x + 1, y)) << 1) | (land(at(x, y + 1)) << 2) | (land(at(x - 1, y)) << 3)
                if bits:
                    blit(canvas, ts.t(dr["banks"][bits]), x * T, y * T)
                for k, (dx, dy) in (("nw", (-1, -1)), ("ne", (1, -1)), ("sw", (-1, 1)), ("se", (1, 1))):
                    if land(at(x + dx, y + dy)) and not land(at(x + dx, y)) and not land(at(x, y + dy)):
                        blit(canvas, ts.t(dr["innerCorners"][k]), x * T, y * T)
            elif c == "=":
                hor = not land(at(x, y - 1)) or not land(at(x, y + 1))
                hor = hor and (land(at(x - 1, y)) or at(x - 1, y) == "=") and (land(at(x + 1, y)) or at(x + 1, y) == "=")
                if at(x, y - 1) == "=" or at(x, y + 1) == "=":
                    hor = not (at(x, y - 1) == "=" or at(x, y + 1) == "=") and hor
                b = dr["bridge"]
                if hor:
                    k = "hEndW" if land(at(x - 1, y)) and at(x - 1, y) != "#" and at(x - 1, y) != "=" else "hEndE" if land(at(x + 1, y)) and at(x + 1, y) not in "#=" else "h"
                else:
                    k = "vEndN" if land(at(x, y - 1)) and at(x, y - 1) not in "#=" else "vEndS" if land(at(x, y + 1)) and at(x, y + 1) not in "#=" else "v"
                blit(canvas, ts.t(b[k]), x * T, y * T)
    rl = dr["railing"]
    for y in range(H):
        for x in range(W):
            if is_floor(g[y][x]):
                if at(x, y + 1) == "~":
                    k = "s" if (x * 7 + y) % 5 else ("s_broken" if (x + y) % 2 else None)
                    if k:
                        blit(canvas, ts.t(rl[k]), x * T, y * T)
                if at(x, y - 1) == "~" and (x * 3 + y) % 4:
                    blit(canvas, ts.t(rl["n"]), x * T, y * T)
    # 벽
    wl = v4["wall"]
    for y in range(H):
        for x in range(W):
            if g[y][x] != "#":
                continue
            px, py = x * T, y * T
            h_ = (x * 73 + y * 31) % 7
            s1 = at(x, y + 1)
            s2 = at(x, y + 2)
            if s1 != "#" and 0 <= y + 1 < H:
                blit(canvas, ts.t(wl["lower"][h_ % len(wl["lower"])] if h_ < 5 else wl["lower"][0]), px, py)
                if at(x - 1, y) != "#":
                    blit(canvas, ts.t(wl["endLowerL"]), px, py)
                if at(x + 1, y) != "#":
                    blit(canvas, ts.t(wl["endLowerR"]), px, py)
            elif s1 == "#" and s2 != "#" and 0 <= y + 2 < H:
                blit(canvas, ts.t(wl["upper"][h_ % len(wl["upper"])] if h_ < 4 else wl["upper"][0]), px, py)
                if at(x - 1, y) != "#":
                    blit(canvas, ts.t(wl["endUpperL"]), px, py)
                if at(x + 1, y) != "#":
                    blit(canvas, ts.t(wl["endUpperR"]), px, py)
            elif s1 == "#" and s2 == "#" and at(x, y + 3) != "#" and 0 <= y + 3 < H:
                blit(canvas, ts.t(wl["topAboveFront"]), px, py)
            else:
                bits = (at(x, y - 1) != "#" and y > 0) | ((at(x + 1, y) != "#" and x + 1 < W) << 1) | \
                       ((at(x, y + 1) != "#" and y + 1 < H) << 2) | ((at(x - 1, y) != "#" and x > 0) << 3)
                if bits:
                    blit(canvas, ts.t(wl["topEdges"][bits]), px, py)
                else:
                    blit(canvas, ts.t(wl["top"][h_ % len(wl["top"])]), px, py)
    return canvas


# ================================================================ 조명
def light_scene(canvas, lights, ambient, box, out_size=(1920, 1080)):
    """box = (x0, y0, x1, y1) 도트. lights = [(x, y, color, radius_dots, intensity)]. → (렌더 RGB, 측정용 배열)"""
    x0, y0, x1, y1 = box
    view = canvas[y0:y1, x0:x1, :3].astype(np.float32)
    H, W = view.shape[:2]
    s = 8
    lh, lw = H // s + 1, W // s + 1
    acc = np.zeros((lh, lw, 3), np.float32) + np.array(ambient, np.float32)
    gy, gx = np.mgrid[0:lh, 0:lw].astype(np.float32)
    for (lx, ly, colr, rad, it) in lights:
        c = np.array(hx(colr), np.float32) / 255
        cx, cy = (lx - x0) / s, (ly - y0) / s
        rr = rad / s
        d2 = ((gx - cx) ** 2 + ((gy - cy) * 1.15) ** 2) / (rr * rr)
        f = np.clip(1 - d2, 0, 1) ** 2 * it
        acc += f[..., None] * c
    acc = np.minimum(acc, 1.6)
    lm = np.asarray(Image.fromarray((acc / 1.6 * 255).astype(np.uint8), "RGB").resize((lw * s, lh * s), Image.BILINEAR))[:H, :W]
    lit = view * (lm.astype(np.float32) / 255 * 1.6)
    em = np.zeros(view.shape[:2], bool)
    for e in EMISSIVE:
        em |= np.all(canvas[y0:y1, x0:x1, :3] == e, axis=-1)
    lit[em] = view[em]
    lit = np.clip(lit, 0, 255).astype(np.uint8)
    im = Image.fromarray(lit, "RGB")
    # 발광 번짐(bloom) 약하게
    emi = np.zeros_like(lit); emi[em] = lit[em]
    glow = Image.fromarray(emi).filter(ImageFilter.GaussianBlur(10))
    im = Image.fromarray(np.clip(lit.astype(np.int16) + (np.asarray(glow).astype(np.int16) * 0.6).astype(np.int16), 0, 255).astype(np.uint8))
    im = im.resize(out_size, Image.BILINEAR)
    return im


def measure(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    return float(L.mean()), float((L < 25).mean())
