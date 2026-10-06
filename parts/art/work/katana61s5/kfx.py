"""61 단계 5 칼 이펙트 '은선 베기' — 무기(은선 칼)와 같은 디자인 언어로 칼 fx 를 다시 그린다.

원칙(P13 §2): 굵은 반달 덩어리 대신 종이를 베듯 곧고 가는 빛줄기. 날끝(머리)이 가장 밝고 뾰족하며 꼬리로 갈수록 1도트로 가늘어짐.
  · 획 = 바깥(날선 쪽) 가장자리가 가장 밝은 1~3도트 '틈' + 안쪽 1도트 잔상 실선(끊김이 흐름) — 무채 G9~G14 · 청강 SL.
  · 판정(glowFrames) 머리만 백열 X0/X1 + 접선 방향으로 곧게 뻗는 섬광 바늘 + 4갈래 별(첫 판정 칸) · 머리 옆 호박 불티 몇 점(주인공 호박과 잇기).
  · 소멸 = 재 부스러기 대신 '베인 자국' — 선이 마디로 끊기고 마디가 법선 방향으로 엇갈려 벌어지며(종이 틈) 식는다.
  · 발도(iai)·일섬(issen) = 한 줄 섬광이 남아 떨리다가, 늦게 '터짐' 칸에서 두 줄로 갈라지며 비스듬한 베인 자국들이 열림.
기하(시트별 경로·칸별 머리/꼬리)는 고치기 전 그림(git kcommon.SRC_REV)에서 그대로 따 온다(trace) — 판정 호·선 위치·타이밍 불변.
틀·피벗·프레임·ms·행·앵커·glowFrames 는 기존 JSON 그대로.
"""
import json
import math
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kcommon as C  # noqa: E402
from PIL import Image  # noqa: E402

HEAD_DIR = os.path.join(HERE, "out", "head")


def hx(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


GRAY = ['#000000', '#141516', '#212224', '#2f3033', '#3e3f42', '#4d4f52', '#5c5e62', '#6c6f73', '#7d8084', '#8e9195', '#a0a2a6', '#b2b4b8',
        '#c5c6c9', '#d8d9db', '#ebeced', '#ffffff']
G = [hx(c) for c in GRAY]
SL = [hx(c) for c in ["#14161c", "#1d2028", "#272b35", "#323743", "#3f4552", "#4e5563", "#626a78", "#7e8693"]]
A17, A19, A21, A23, A25, A26 = [hx(c) for c in ("#3f271d", "#8b4d22", "#d67a11", "#e2a33c", "#eecc78", "#f4de9b")]
X0, X1 = hx("#ffffff"), hx("#fff4dc")
SIL = [hx(c) for c in ['#16171a', '#33343a', '#50535b', '#6e717b', '#8a8f9c', '#a6adbd', '#b1b8c7', '#bdc4d1', '#cad0db', '#d7dce6', '#e4e9f0', '#f2f5fa']]
HOT = {X0[:3], X1[:3], A26[:3]}

# 값(0..1) → 색. 판정 칸만 백열.
RAMP = [(0.88, G[13]), (0.72, G[12]), (0.58, G[11]), (0.44, G[9]), (0.30, SL[7]), (0.16, SL[6]), (0.0, SL[4])]
RAMP_MOON = [(0.88, SIL[11]), (0.72, SIL[9]), (0.58, SIL[8]), (0.44, SIL[6]), (0.30, SIL[4]), (0.16, SIL[3]), (0.0, SIL[2])]


class Pal:
    def __init__(self, moon=False):
        self.moon = moon
        self.ramp = RAMP_MOON if moon else RAMP

    def col(self, v, hot=False):
        if hot and v > 0.93:
            return X0
        if hot and v > 0.82:
            return X1
        for t, c in self.ramp:
            if v >= t:
                return c
        return None


# =============================================================================
# 캔버스
# =============================================================================
class Cv:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = {}

    def put(self, x, y, c, pr=0):
        x, y = int(math.floor(x + 0.5)), int(math.floor(y + 0.5))
        if not (1 <= x < self.w - 1 and 1 <= y < self.h - 1) or c is None:
            return
        o = self.px.get((x, y))
        if o is None or pr >= o[1]:
            self.px[(x, y)] = (c, pr)

    def image(self):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        p = im.load()
        for (x, y), (c, _) in self.px.items():
            p[x, y] = c
        return im


def clean_line(p0, p1):
    out = []
    x0, y0 = p0
    x1, y1 = p1
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 3) + 1
    for k in range(n + 1):
        c = (int(math.floor(x0 + (x1 - x0) * k / n + 0.5)), int(math.floor(y0 + (y1 - y0) * k / n + 0.5)))
        if not out or out[-1] != c:
            out.append(c)
    i = 1
    while i < len(out) - 1:
        a, b = out[i - 1], out[i + 1]
        if abs(a[0] - b[0]) == 1 and abs(a[1] - b[1]) == 1:
            out.pop(i)
            continue
        i += 1
    return out


# =============================================================================
# 고치기 전 그림(git C.SRC_REV)
# =============================================================================
def head_grid(rel):
    jp = os.path.join(HEAD_DIR, rel + ".json")
    if not os.path.exists(jp):
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        raw = subprocess.run(["git", "-C", C.ROOT, "show", "%s:assets/sprites/%s.json" % (C.SRC_REV, rel)], capture_output=True, check=True).stdout
        open(jp, "wb").write(raw)
        m = json.loads(raw)
        pages = [t["image"] for t in m.get("textures", [])] or [m.get("meta", {}).get("image", os.path.basename(rel) + ".png")]
        for pg in pages:
            b = subprocess.run(["git", "-C", C.ROOT, "show", "%s:assets/sprites/%s/%s" % (C.SRC_REV, os.path.dirname(rel), pg)], capture_output=True, check=True).stdout
            open(os.path.join(os.path.dirname(jp), pg), "wb").write(b)
    m = C.gridsheet.load_meta(jp)
    g = C.gridsheet.open_grid(jp)
    fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
    rows = m["directions"]
    return m, {d: [g.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r, d in enumerate(rows)}


def opaque(im):
    p = im.load()
    W, H = im.size
    bb = im.getbbox()
    if not bb:
        return []
    return [(x, y, p[x, y]) for y in range(bb[1], bb[3]) for x in range(bb[0], bb[2]) if p[x, y][3]]


# =============================================================================
# 경로 따기
# =============================================================================
class Path:
    def __init__(self, pts, center=None):
        self.p = pts
        acc = [0.0]
        for a, b in zip(pts, pts[1:]):
            acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.L = acc[-1] or 1.0
        self.u = [a / self.L for a in acc]
        self.center = center

    def at(self, u):
        u = max(0.0, min(1.0, u))
        lo, hi = 0, len(self.u) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if self.u[m] <= u:
                lo = m
            else:
                hi = m
        a, b = self.p[lo], self.p[hi]
        du = (self.u[hi] - self.u[lo]) or 1e-9
        t = (u - self.u[lo]) / du
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        tx, ty = tx / ln, ty / ln
        nx, ny = -ty, tx
        if self.center is not None:            # 바깥(중심에서 먼 쪽) = +n
            if (x - self.center[0]) * nx + (y - self.center[1]) * ny < 0:
                nx, ny = -nx, -ny
        elif ny > 0 or (abs(ny) < 1e-6 and nx < 0):   # 곧은 선: 화면 위쪽 = +n
            nx, ny = -nx, -ny
        return (x, y), (tx, ty), (nx, ny)

    def nearest(self, x, y):
        best, bu = 1e18, 0.0
        step = max(1, len(self.p) // 400)
        for i in range(0, len(self.p), step):
            q = self.p[i]
            d = (q[0] - x) ** 2 + (q[1] - y) ** 2
            if d < best:
                best, bu = d, self.u[i]
        return bu, math.sqrt(best)


def smooth(pts, w=3):
    out = []
    for i in range(len(pts)):
        a, b = max(0, i - w), min(len(pts), i + w + 1)
        out.append((sum(p[0] for p in pts[a:b]) / (b - a), sum(p[1] for p in pts[a:b]) / (b - a)))
    return out


def trace_arc(pix, center, binw=1.2):
    if len(pix) < 10:
        return None
    angs = sorted(math.degrees(math.atan2(y - center[1], x - center[0])) for x, y in pix)
    # 가장 큰 각 틈에서 자른다(회전 베기 328° 도 이어짐)
    gaps = [(angs[(i + 1) % len(angs)] - angs[i]) % 360 for i in range(len(angs))]
    i_cut = max(range(len(gaps)), key=lambda i: gaps[i])
    cut = angs[(i_cut + 1) % len(angs)]
    bins = {}
    for x, y in pix:
        a = (math.degrees(math.atan2(y + 0.5 - center[1], x + 0.5 - center[0])) - cut) % 360
        bins.setdefault(int(a / binw), []).append(math.hypot(x + 0.5 - center[0], y + 0.5 - center[1]))
    ks = sorted(k for k in bins if len(bins[k]) >= 2)
    if len(ks) < 4:
        return None
    rad = {k: sorted(bins[k])[len(bins[k]) // 2] for k in ks}

    def smooth_r(keys, w):
        out = {}
        for i, k in enumerate(keys):
            win = [rad[q] for q in keys[max(0, i - w): i + w + 1]]
            win.sort()
            out[k] = win[len(win) // 2]
        return out
    sm = smooth_r(ks, 6)
    ks = [k for k in ks if abs(rad[k] - sm[k]) < 5]          # 튄 점·붓 머리 덩이 제거
    sm = smooth_r(ks, 5)
    pts = []
    for i, k in enumerate(ks):
        win = [sm[q] for q in ks[max(0, i - 4): i + 5]]
        r = sum(win) / len(win)
        ang = math.radians(cut + (k + 0.5) * binw)
        pts.append((center[0] + math.cos(ang) * r, center[1] + math.sin(ang) * r))
    return Path(pts, center)


def trace_line(pix, binw=2.0):
    """곧은 선(찌르기·발도·일섬·땅 틈): 주축(PCA) 위 1~99% 범위를 잇는 완전한 직선 — 붓 떨림·튄 점을 따라가지 않음."""
    if len(pix) < 6:
        return None
    mx = sum(x for x, y in pix) / len(pix)
    my = sum(y for x, y in pix) / len(pix)
    sxx = sum((x - mx) ** 2 for x, y in pix)
    syy = sum((y - my) ** 2 for x, y in pix)
    sxy = sum((x - mx) * (y - my) for x, y in pix)
    a = 0.5 * math.atan2(2 * sxy, sxx - syy)
    ax, ay = math.cos(a), math.sin(a)
    lat = sorted((x - mx) * -ay + (y - my) * ax for x, y in pix)
    lm = lat[len(lat) // 2]
    ts = sorted((x - mx) * ax + (y - my) * ay for x, y in pix if abs((x - mx) * -ay + (y - my) * ax - lm) < 4)
    t0, t1 = ts[int(len(ts) * 0.01)], ts[min(len(ts) - 1, int(len(ts) * 0.99))]
    cx, cy = mx + -ay * lm + 0.5, my + ax * lm + 0.5
    n = max(4, int((t1 - t0) / 2))
    pts = [(cx + ax * (t0 + (t1 - t0) * i / n), cy + ay * (t0 + (t1 - t0) * i / n)) for i in range(n + 1)]
    return Path(pts, None)


def coverage(path, pix, tol=7.0):
    us = []
    for x, y in pix:
        u, d = path.nearest(x + 0.5, y + 0.5)
        if d <= tol:
            us.append(u)
    if len(us) < 4:
        return None
    us.sort()
    return us[int(len(us) * 0.02)], us[min(len(us) - 1, int(len(us) * 0.98))], len(us)


def orient(path, frames_pix, origin):
    """처음 그려지는 칸(가장 이른 비지 않은 칸)의 평균 위치가 경로 앞쪽이 되게."""
    for pix in frames_pix:
        if len(pix) >= 4:
            us = [path.nearest(x + 0.5, y + 0.5)[0] for x, y in pix[:: max(1, len(pix) // 200)]]
            mu = sum(us) / len(us)
            if abs(mu - 0.5) > 0.08:
                if mu > 0.5:
                    return Path(list(reversed(path.p)), path.center)
                return path
            break
    if origin is not None:
        a, b = path.p[0], path.p[-1]
        if math.hypot(b[0] - origin[0], b[1] - origin[1]) < math.hypot(a[0] - origin[0], a[1] - origin[1]):
            return Path(list(reversed(path.p)), path.center)
    return path


# =============================================================================
# 그리기 조각
# =============================================================================
def slit(cv, path, u0, u1, pal, hot=False, wmax=3.0, bright=1.0, pr=2, needle=True, head_fade=False):
    """머리(u1)가 밝고 뾰족, 꼬리(u0)로 1도트까지 가늘어지는 '틈' 획. 바깥(+n) 가장자리가 가장 밝다."""
    if u1 - u0 < 1e-4:
        return
    Ls = (u1 - u0) * path.L
    n = max(2, int(Ls / 0.35))
    for j in range(n + 1):
        s = j / n
        u = u0 + (u1 - u0) * s
        (x, y), _, (nx, ny) = path.at(u)
        w = 1.0 + (wmax - 1.0) * (s ** 1.3)
        if needle and s > 0.9:
            w *= max(0.25, (1 - s) / 0.1)
        b = bright * (0.42 + 0.58 * s ** 0.8)
        if head_fade and s > 0.85:
            b *= 0.8
        half = w / 2.0
        o = -half
        while o <= half + 1e-6:
            q = 1 - (abs(o) / (half + 0.6)) ** 2
            v = b * (0.55 + 0.45 * q) + (0.12 if o > half - 0.6 else 0.0)
            cv.put(x + nx * (o + 0.5), y + ny * (o + 0.5), pal.col(min(1.0, v), hot and s > 0.55), pr)
            o += 0.5


def hairline(cv, path, u0, u1, off, col, dash=(5, 3), shift=0, pr=1, taper=True):
    """안쪽(-n 쪽) 잔상 실선 1도트(끊김 흐름)."""
    if u1 - u0 < 1e-4:
        return
    Ls = (u1 - u0) * path.L
    n = max(2, int(Ls / 0.4))
    pts = []
    for j in range(n + 1):
        s = j / n
        (x, y), _, (nx, ny) = path.at(u0 + (u1 - u0) * s)
        o = off * (0.4 + 0.6 * math.sin(math.pi * min(1.0, s)) if taper else 1.0)
        pts.append((x + nx * o, y + ny * o))
    k = 0
    seen = set()
    for a, b in zip(pts, pts[1:]):
        for q in clean_line(a, b):
            if q in seen:
                continue
            seen.add(q)
            if not dash or ((k + shift) % (dash[0] + dash[1])) < dash[0]:
                cv.put(q[0], q[1], col, pr)
            k += 1


def needle(cv, x, y, tx, ty, ln, cols, pr=4):
    for j in range(int(ln)):
        c = cols[min(len(cols) - 1, int(j / ln * len(cols)))]
        cv.put(x + tx * j, y + ty * j, c, pr)


def star(cv, x, y, arm, pr=6, hot=True):
    cv.put(x, y, X0 if hot else G[13], pr)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for j in range(1, arm + 1):
            c = (X1 if hot else G[13]) if j == 1 else (G[13] if j < arm else G[11])
            cv.put(x + dx * j, y + dy * j, c, pr)


def sparks(cv, x, y, tx, ty, nx, ny, seed, n=4, age=0.0, pr=5):
    r = random.Random(seed)
    for k in range(n):
        a = r.uniform(3, 9) + age * r.uniform(6, 12)
        b = r.uniform(-4, 5) + age * r.uniform(-2, 4)
        px_, py_ = x + tx * a + nx * b, y + ty * a + ny * b + age * age * 4
        c = (A25, A23, A23, A21)[k % 4] if age < 0.5 else (A21, A19)[k % 2]
        cv.put(px_, py_, c, pr)
        if age < 0.3 and k % 2 == 0:
            cv.put(px_ - tx, py_ - ty, A21, pr)


def cut_marks(cv, path, u0, u1, k, pal, seed, opening=True, pr=2):
    """소멸: 선을 마디로 끊고 마디를 법선으로 엇갈려 벌림(종이 틈). k 0..1."""
    if u1 - u0 < 1e-4:
        return
    r = random.Random(seed)
    seg = 15 - 6 * k
    gap = 1.5 + 9 * k
    L = (u1 - u0) * path.L
    pos = r.uniform(0, gap)
    idx = 0
    while pos < L:
        e = min(L, pos + seg * r.uniform(0.7, 1.25))
        sgn = 1 if idx % 2 else -1
        off = sgn * (round(1.6 * k) if opening else 0)
        v = 0.78 - 0.45 * k
        n = max(2, int((e - pos) / 0.4))
        for j in range(n + 1):
            s = j / n
            u = u0 + (pos + (e - pos) * s) / path.L
            (x, y), _, (nx, ny) = path.at(u)
            w = 1 if (k > 0.45 or s < 0.15 or s > 0.85) else 2
            for o in range(w):
                cv.put(x + nx * (off + o * 0.9), y + ny * (off + o * 0.9), pal.col(v * (1 - 0.25 * o)), pr)
        if k < 0.85 and r.random() < 0.35 + 0.4 * k:           # 떨어지는 쇳가루 점
            (x, y), _, (nx, ny) = path.at(u0 + (pos + e) / 2 / path.L)
            cv.put(x + r.uniform(-2, 2), y + 3 + 9 * k * r.uniform(0.6, 1.4), pal.col(0.35), 1)
        pos = e + gap * r.uniform(0.6, 1.5)
        idx += 1


def cross_cuts(cv, path, k, pal, seed, hot=False, n=4, ln=16, ang=55, pr=5, spark=True, max_v=1.0):
    """터짐: 선을 비스듬히 가로지르는 짧은 베인 자국 n 개(가운데 밝고 양끝 뾰족). k 0(열림)..1(식음)."""
    r = random.Random(seed)
    for j in range(n):
        u = (j + 0.5 + r.uniform(-0.25, 0.25)) / n
        (x, y), (tx, ty), (nx, ny) = path.at(u)
        a = math.radians(ang if j % 2 == 0 else 180 - ang)
        dx, dy = tx * math.cos(a) + nx * math.sin(a), ty * math.cos(a) + ny * math.sin(a)
        L = ln * (1.0 - 0.45 * k) * r.uniform(0.8, 1.2)
        m = int(L)
        for i in range(-m // 2, m // 2 + 1):
            s = abs(i) / (m / 2.0 + 0.5)
            v = max_v * (1.0 - 0.5 * k) * (1 - 0.6 * s * s)
            if k > 0.5 and (i + j) % 3 == 0:
                continue
            cv.put(x + dx * i, y + dy * i, pal.col(v, hot and s < 0.35), pr)
            if s < 0.45 and k < 0.5:                 # 가운데 1/3 은 2도트(벌어진 틈)
                cv.put(x + dx * i + tx, y + dy * i + ty, pal.col(v * 0.8), pr - 1)
        if spark and k < 0.5:
            sparks(cv, x, y, dx, dy, -dy, dx, seed * 31 + j, n=2, age=k)
