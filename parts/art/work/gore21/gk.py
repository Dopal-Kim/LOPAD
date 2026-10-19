"""P21 아트 B 공용 도구 — 피·타르·재 도트(반투명 0, 결정적 난수), 격자 시트 쓰기 → atlas57 변환.

색(전부 LOPAD 팔레트 parts/art/palette/lopad.json 안 — 새 색 없음):
  피 BL = 7층 '적' 램프의 어두운 5단(고정 hex, paletteSwap none). 밝은 빨강 금지 — BL4 는 덩어리마다 하이라이트 1도트만.
  타르 = 무채 G0~G2(+G4 하이라이트 1도트) · 불씨 = 1층 호박 A19~A26 · 재 = G5~G8.
"""
import json
import math
import os
import random
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
SPR = os.path.join(ROOT, "assets", "sprites")
OUT = os.path.join(HERE, "out")

_pal = json.load(open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8"))
G = _pal["gray"]
_floors = {f["floor"]: f["ramp"] for f in _pal["floors"]}
CRIMSON = _floors[7]
AMBER = _floors[1]
A = {16 + i: c for i, c in enumerate(AMBER)}           # 주인공·불씨 호박 A16~A27 (1층 램프 고정)
BL = CRIMSON[0:5]                                       # #1a0f13 #381b25 #572030 #751f33 #941930
BL0, BL1, BL2, BL3, BL4 = BL
TAR = [G[0], G[1], G[2], G[3], G[4]]
ASHC = [G[5], G[6], G[7], G[8]]
PALETTE_NOTE = ("parts/art/palette/lopad.json — 피 = 7층 '적' 램프 어두운 5단 #1a0f13·#381b25·#572030·#751f33·#941930(고정 hex, "
                "밝은 빨강 없음 · #941930 은 덩어리마다 하이라이트 1도트) · 타르 = 무채 G0~G4 · 불씨 = 1층 호박 램프(고정) · 재 = G5~G8. "
                "paletteSwap none(층 램프 교체 대상 아님). 새 색 없음")


def hexrgb(c):
    if isinstance(c, tuple):
        return tuple(c[:3]) + (255,)
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)


class Canvas:
    """정수 픽셀 캔버스(dict). put 은 덮어쓰기, under 는 빈 칸에만."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.p = {}

    def put(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[(x, y)] = c

    def under(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h and (x, y) not in self.p:
            self.p[(x, y)] = c

    def get(self, x, y):
        return self.p.get((x, y))

    def image(self):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        px = im.load()
        for (x, y), c in self.p.items():
            px[x, y] = hexrgb(c)
        return im


def line_cells(x0, y0, x1, y1):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    out = []
    for i in range(n + 1):
        t = i / max(1, n)
        q = (int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)))
        if not out or out[-1] != q:
            out.append(q)
    return out


def disc_cells(cx, cy, r, sy=1.0):
    """반지름 r(도트) 원(세로 비 sy). r < 0.75 = 1도트, < 1.2 = 십자."""
    if r < 0.75:
        return {(int(round(cx)), int(round(cy)))}
    if r < 1.2:
        x, y = int(round(cx)), int(round(cy))
        return {(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)} if r >= 1.0 else {(x, y), (x + 1, y), (x, y + 1)}
    out = set()
    for y in range(int(cy - r * sy) - 1, int(cy + r * sy) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if ((x + 0.5 - cx) / r) ** 2 + ((y + 0.5 - cy) / (r * sy)) ** 2 <= 1.0:
                out.add((x, y))
    return out


def blob_cells(cx, cy, r, rnd, lobes=5, sy=1.0, rough=0.35):
    """불규칙 덩어리: 가운데 원 + 둘레 작은 원(로브) 합집합."""
    cells = disc_cells(cx, cy, r, sy)
    for k in range(lobes):
        a = rnd.uniform(0, 2 * math.pi)
        d = r * rnd.uniform(0.5, 1.0 + 0.4 * rough)
        cells |= disc_cells(cx + math.cos(a) * d, cy + math.sin(a) * d * sy, r * rnd.uniform(0.25, 0.6) * (1 + rough), sy)
    return cells


def shade_wet(cv, cells, base=BL2, lit=BL3, dark=BL1, edge=BL0, hi=BL4, hi_n=1, rnd=None, rim=True):
    """젖은 덩어리 셰이딩: 아래·오른쪽 가장자리 = dark/edge, 위·왼쪽 안쪽 = lit, 하이라이트 hi_n 도트(왼위 사분면)."""
    cells = set(cells)
    if not cells:
        return
    for (x, y) in cells:
        up, lf = (x, y - 1) in cells, (x - 1, y) in cells
        dn, rt = (x, y + 1) in cells, (x + 1, y) in cells
        if rim and (not dn or not rt) and not (not up or not lf):
            c = edge if (not dn and not rt) else dark
        elif (not up or not lf) and (dn and rt):
            c = lit
        elif not up and not dn:
            c = dark
        else:
            c = base
        cv.put(x, y, c)
    if hi_n and len(cells) >= 6:
        xs = [c[0] for c in cells]
        ys = [c[1] for c in cells]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        cand = sorted((c for c in cells if c[0] <= cx and c[1] <= cy and (c[0] - 1, c[1]) in cells and (c[0], c[1] - 1) in cells),
                      key=lambda c: (c[0] - cx + 1) ** 2 + (c[1] - cy + 1) ** 2)
        for c in cand[:hi_n]:
            cv.put(c[0], c[1], hi)


def flat_cells(cells, dark_center=True):
    return cells


# ---------------------------------------------------------------- 입자(분출)
class Drop:
    __slots__ = ("x", "y", "vx", "vy", "r", "t0", "land", "drag", "chain", "seed", "kind")

    def __init__(self, x, y, vx, vy, r, t0=0.0, land=0.25, drag=3.0, chain=-1, seed=0, kind="blood"):
        self.x, self.y, self.vx, self.vy, self.r = x, y, vx, vy, r
        self.t0, self.land, self.drag, self.chain, self.seed, self.kind = t0, land, drag, chain, seed, kind

    def pos(self, t):
        """t 초 뒤 위치(지수 감속). 착지 뒤에는 멈춘다."""
        tt = max(0.0, min(t - self.t0, self.land))
        k = self.drag
        f = (1 - math.exp(-k * tt)) / k
        return self.x + self.vx * f, self.y + self.vy * f

    def vel(self, t):
        tt = max(0.0, min(t - self.t0, self.land))
        e = math.exp(-self.drag * tt)
        return self.vx * e, self.vy * e

    def alive(self, t):
        return t >= self.t0

    def landed(self, t):
        return t - self.t0 >= self.land


def draw_drop(cv, d, t, cols, end_t, soak=0.12):
    """날아가는 방울 = 머리 + 속도 반대 꼬리, 착지 = 납작한 점(진행 방향으로 늘어남), 끝 무렵 스며들며 작아짐."""
    if not d.alive(t):
        return
    x, y = d.pos(t)
    dark, base, lit, hi = cols
    if not d.landed(t):
        vx, vy = d.vel(t)
        sp = math.hypot(vx, vy)
        ln = min(12.0, sp * 0.028)
        if sp > 1e-3 and ln >= 1.0:
            ux, uy = vx / sp, vy / sp
            for i, (cx, cy) in enumerate(line_cells(x - ux * ln, y - uy * ln, x, y)):
                cv.put(cx, cy, dark if i < max(1, ln * 0.6) else base)
        cells = disc_cells(x, y, d.r)
        for c in cells:
            cv.put(c[0], c[1], base)
        if d.r >= 1.0:
            cv.put(int(round(x)), int(round(y)) - (1 if d.r >= 1.5 else 0), lit)
        if d.r >= 1.6:
            cv.put(int(round(x)) - 1, int(round(y)) - 1, hi)
        return
    # 착지 — 진행 방향으로 늘어난 납작 점
    age = t - d.t0 - d.land
    shrink = max(0.0, (t - (end_t - soak)) / soak) if t > end_t - soak else 0.0
    vx, vy = d.vx, d.vy
    sp = math.hypot(vx, vy) or 1
    ux, uy = vx / sp, vy / sp
    r = d.r * (1.15 - 0.6 * shrink)
    if r < 0.55 and shrink > 0.7:
        return
    L = 1 + min(3, int(d.r * 1.5 + min(age, 0.05) * 30))
    cells = set()
    for k in range(L):
        cells |= disc_cells(x + ux * k * 0.8, y + uy * k * 0.8, max(0.5, r * (1 - 0.18 * k)))
    for c in cells:
        cv.put(c[0], c[1], dark if shrink > 0.3 else base)
    if d.r >= 1.4 and shrink < 0.3:
        cv.put(int(round(x)), int(round(y)), lit)


def draw_ligaments(cv, drops, t, col, max_gap=6.0):
    """같은 사슬(chain)의 이웃 방울을 잇는 피 띠(분출 초반 — 아직 끊기지 않은 줄기)."""
    by = {}
    for d in drops:
        if d.chain >= 0 and d.alive(t) and not d.landed(t):
            by.setdefault(d.chain, []).append(d)
    for lst in by.values():
        lst.sort(key=lambda d: d.seed)
        for a, b in zip(lst, lst[1:]):
            ax, ay = a.pos(t)
            bx, by_ = b.pos(t)
            if math.hypot(ax - bx, ay - by_) <= max_gap:
                for c in line_cells(ax, ay, bx, by_):
                    cv.put(c[0], c[1], col)


def frame_times(ms):
    out, t = [], 0
    for m in ms:
        t += m
        out.append(t / 1000.0)
    return out


# ---------------------------------------------------------------- 시트 쓰기
def sheet_from_rows(rows):
    """rows = [[Image…], …] (행 = 방향/변형) → 격자 시트."""
    fw, fh = rows[0][0].size
    n = len(rows[0])
    sh = Image.new("RGBA", (fw * n, fh * len(rows)), (0, 0, 0, 0))
    for r, lst in enumerate(rows):
        assert len(lst) == n
        for c, im in enumerate(lst):
            assert im.size == (fw, fh), (im.size, fw, fh)
            sh.alpha_composite(im, (c * fw, r * fh))
    return sh


def check_opaque(im, name):
    a = im.getchannel("A")
    bad = sum(1 for v in a.getdata() if 0 < v < 255)
    assert bad == 0, (name, "반투명 픽셀", bad)


def write_sheet(cat, ver, name, rows, meta, convert=True):
    """격자 시트 + JSON 을 assets/sprites/<cat>/<ver>/ 에 쓰고(사본 out/grid/) atlas57 로 곧바로 변환."""
    sh = sheet_from_rows(rows)
    check_opaque(sh, name)
    fw, fh = rows[0][0].size
    m = {"image": name + ".png", "frameWidth": fw, "frameHeight": fh, "frames": len(rows[0])}
    m.update(meta)
    m.setdefault("layout", "row = direction/variant (directions 순서), column = frame index")
    m.setdefault("frameIndex", "row * columns + column (§19 아틀라스 키)")
    m.setdefault("pixelScale", 0.5)
    m.setdefault("paletteSwap", "none")
    m.setdefault("semiTransparent", False)
    m.setdefault("version", "v5-p21" if ver == "v5" else ver + "-p21")
    if "frameDurationsMs" in m:
        ms = m["frameDurationsMs"]
        m.setdefault("fps", round(1000.0 * len(ms) / sum(ms), 2) if sum(ms) else 0)   # 정지 그림(변형 아틀라스)은 0
    gd = os.path.join(OUT, "grid", cat, ver)
    os.makedirs(gd, exist_ok=True)
    sh.save(os.path.join(gd, name + ".png"), optimize=True)
    with open(os.path.join(gd, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    dst = os.path.join(SPR, cat, ver)
    os.makedirs(dst, exist_ok=True)
    sh.save(os.path.join(dst, name + ".png"), optimize=True)
    with open(os.path.join(dst, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    if convert:
        atlas(cat, ver, name)
    return sh


def atlas(cat, ver, only):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "parts", "art", "work", "atlas57", "build.py"), "--in-place",
                        "--cats", cat, "--ver", ver, "--only", only], capture_output=True, text=True)
    if r.returncode != 0 or "오류" in r.stdout:
        raise RuntimeError(r.stdout + r.stderr)
    return r.stdout


def preview(rows, path, scale=3, bg=(22, 22, 26), labels=None):
    """미리보기: 어두운 바닥색 위에 확대(정수 배)."""
    fw, fh = rows[0][0].size
    n = max(len(r) for r in rows)
    W, H = fw * n * scale + (n + 1) * 4, (fh * scale + 4) * len(rows) + 4
    out = Image.new("RGBA", (W, H), bg + (255,))
    for r, lst in enumerate(rows):
        for c, im in enumerate(lst):
            big = im.resize((fw * scale, fh * scale), Image.NEAREST)
            out.alpha_composite(big, (4 + c * (fw * scale + 4), 4 + r * (fh * scale + 4)))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.convert("RGB").save(path)
    return path
