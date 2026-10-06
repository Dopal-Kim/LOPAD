"""61 단계 5 개성 fx(칼·대검) — 공용 도구: 팔레트 · 픽셀 캔버스 · 붓/은선/금/먼지/불 · 검사 · 격자→트림 아틀라스.

결정적(난수는 시드 고정 random.Random). numpy 없이 순수 파이썬(Pillow 만).
다른 아트 작업(단검·활 개성 fx, 카드 그림)과 공용 스크립트·임시 폴더를 나누지 않는다 — 임시 폴더는 out/_atlas_tmp_tkg_<pid>.
"""
import importlib.util
import json
import math
import os
import random
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets", "sprites")
FXDIR = os.path.join(SPR, "fx", "v3")
GRID = os.path.join(HERE, "out", "grid")
sys.path.insert(0, os.path.join(WORK, "atlas57"))
import gridsheet  # noqa: E402


def hx(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


def hexs(c):
    return "#%02x%02x%02x" % c[:3]


# ---------------------------------------------------------------- 팔레트
_LOP = json.load(open(os.path.join(WORK, "..", "palette", "lopad.json"), encoding="utf-8"))
G = [hx(c) for c in _LOP["gray"]]                                  # 무채 16 (G0~G15)
_F1 = [hx(c) for c in _LOP["floors"][0]["ramp"]]                   # 1층 램프 → A16~A27
A = {16 + i: c for i, c in enumerate(_F1)}
SL = [hx(c) for c in ["#14161c", "#1d2028", "#272b35", "#323743", "#3f4552", "#4e5563", "#626a78", "#7e8693"]]  # 칼 청강(은선과 같은 값)
S = [hx(c) for c in ["#45403b", "#5c554e", "#756c62", "#90857a"]]  # 재 회색 S0~S3
B = [hx(c) for c in ["#2a1e17", "#3b2a1f", "#4f3828", "#664a33"]]  # 재 갈색 B0~B3
X0, X1 = hx("#ffffff"), hx("#fff4dc")
BIND = [hx(c) for c in ["#232a38", "#3a4458", "#56647e", "#7688ae", "#9ab0d8", "#c0d0ec"]]   # 묶음 청회(#9ab0d8)
MOON = [hx(c) for c in ["#262d3c", "#414c63", "#66748f", "#94a3c0", "#c8d8f0", "#e4ecf8"]]   # 달 청백(#c8d8f0)
CRIM = [hx(c) for c in ["#2a1214", "#4a1c1e", "#6e2628", "#903434", "#b04848", "#cf6a62", "#e8968a"]]  # 피·적갈(#b04848)
HOT = {X0[:3], X1[:3], A[26][:3], A[27][:3]}                       # glowFrames 에만

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- 캔버스
class Fx:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [None] * (w * h)

    def put(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y * self.w + x] = c

    def get(self, x, y):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y * self.w + x]
        return None

    def put_if_empty(self, x, y, c):
        if self.get(x, y) is None:
            self.put(x, y, c)

    def image(self):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        im.putdata([c if c else (0, 0, 0, 0) for c in self.px])
        return im

    # 1도트 선(브레젠험)
    def line(self, x0, y0, x1, y1, c, every=None):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        k = 0
        while True:
            if every is None or every(k):
                self.put(x0, y0, c)
            k += 1
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c, sy=1.0):
        r2 = r * r
        for y in range(int(cy - r * sy) - 1, int(cy + r * sy) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                dy = (y - cy) / sy
                if (x - cx) ** 2 + dy * dy <= r2:
                    self.put(x, y, c)

    def dots(self, pts, c):
        for x, y in pts:
            self.put(x, y, c)


# ---------------------------------------------------------------- 경로
def densify(pts, step=0.5):
    """꼭짓점 목록 → 1도트 간격 정수 점(연속 중복 제거)."""
    out = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for k in range(n):
            t = k / n
            p = (int(round(lerp(x0, x1, t))), int(round(lerp(y0, y1, t))))
            if not out or out[-1] != p:
                out.append(p)
    p = (int(round(pts[-1][0])), int(round(pts[-1][1])))
    if not out or out[-1] != p:
        out.append(p)
    # 대각 L 모서리 제거(1도트 선이 계단처럼 두꺼워지지 않게)
    res = []
    for p in out:
        if len(res) >= 2:
            a, b = res[-2], res[-1]
            if abs(p[0] - a[0]) == 1 and abs(p[1] - a[1]) == 1 and (b[0] == a[0] or b[1] == a[1]):
                res[-1] = p
                continue
        res.append(p)
    return res


def arc_pts(cx, cy, rx, ry, a0, a1, n=None):
    """각도(도, 화면 시계 +) a0→a1 타원 호 꼭짓점."""
    if n is None:
        n = max(8, int(abs(a1 - a0) / 3))
    return [(cx + rx * math.cos(math.radians(lerp(a0, a1, k / n))), cy + ry * math.sin(math.radians(lerp(a0, a1, k / n)))) for k in range(n + 1)]


def normals(pts):
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[max(0, i - 2)], pts[min(n - 1, i + 2)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        out.append((-dy / L, dx / L))
    return out


def tangents(pts):
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[max(0, i - 2)], pts[min(n - 1, i + 2)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        out.append((dx / L, dy / L))
    return out


def rot(x, y, deg, cx=0, cy=0):
    a = math.radians(deg)
    dx, dy = x - cx, y - cy
    return cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)


# ---------------------------------------------------------------- 값 필드(붓·고리·불)
class Field:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.v = [0.0] * (w * h)

    def _set(self, x, y, val):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = y * self.w + x
            if val > self.v[i]:
                self.v[i] = val

    def capsule(self, x0, y0, x1, y1, r0, r1, v0, v1, flat=0.35):
        """끝이 둥근 굵은 선(반지름·값이 선을 따라 변함). 값 = v × 단면 윤곽."""
        rm = max(r0, r1)
        bx0, bx1 = int(min(x0, x1) - rm - 1), int(max(x0, x1) + rm + 2)
        by0, by1 = int(min(y0, y1) - rm - 1), int(max(y0, y1) + rm + 2)
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1e-9
        for y in range(max(0, by0), min(self.h, by1)):
            for x in range(max(0, bx0), min(self.w, bx1)):
                t = clamp(((x - x0) * dx + (y - y0) * dy) / L2)
                px, py = x0 + dx * t, y0 + dy * t
                d = math.hypot(x - px, y - py)
                r = lerp(r0, r1, t)
                if r <= 0 or d > r:
                    continue
                u = d / r
                prof = 1.0 if u < flat else 1.0 - ((u - flat) / (1 - flat)) ** 2
                self._set(x, y, lerp(v0, v1, t) * prof)

    def path(self, pts, rfun, vfun, flat=0.35):
        n = len(pts)
        for i in range(n - 1):
            t0, t1 = i / (n - 1), (i + 1) / (n - 1)
            self.capsule(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], rfun(t0), rfun(t1), vfun(t0), vfun(t1), flat)

    def ring(self, cx, cy, rx, ry, width, val, a0=None, a1=None, vfun=None):
        """타원 고리(정규화 반지름 1 둘레 ± width/rx). a0~a1(도) 구간만 가능. vfun(각도) 로 값 변조."""
        bx0, bx1 = int(cx - rx - width - 2), int(cx + rx + width + 3)
        by0, by1 = int(cy - ry - width - 2), int(cy + ry + width + 3)
        for y in range(max(0, by0), min(self.h, by1)):
            for x in range(max(0, bx0), min(self.w, bx1)):
                ex, ey = (x - cx) / rx, (y - cy) / ry
                rr = math.hypot(ex, ey)
                if rr == 0:
                    continue
                d = abs(rr - 1.0) * rx
                if d > width:
                    continue
                ang = math.degrees(math.atan2(ey, ex)) % 360
                if a0 is not None:
                    if not ((ang - a0) % 360 <= (a1 - a0) % 360):
                        continue
                v = val * (1 - (d / width) ** 2)
                if vfun:
                    v *= vfun(ang)
                self._set(x, y, v)

    def blob(self, cx, cy, rx, ry, val):
        for y in range(max(0, int(cy - ry - 1)), min(self.h, int(cy + ry + 2))):
            for x in range(max(0, int(cx - rx - 1)), min(self.w, int(cx + rx + 2))):
                d = math.hypot((x - cx) / rx, (y - cy) / ry)
                if d <= 1:
                    self._set(x, y, val * (1 - d * d))

    def paint(self, fx, ramp, dither=0.0, only_empty=False, seedmask=None):
        """ramp = [(문턱, 색) ...] 높은 문턱부터. dither = 4×4 베이어 흔들림 폭(마른 붓 가장자리)."""
        w = self.w
        for i, v in enumerate(self.v):
            if v <= 0:
                continue
            x, y = i % w, i // w
            if dither:
                v += (BAYER[y & 3][x & 3] / 15.0 - 0.5) * dither
            for th, c in ramp:
                if v >= th:
                    if not (only_empty and fx.px[i] is not None):
                        fx.px[i] = c
                    break


# ---------------------------------------------------------------- 칼 '은선' 획
def slit(fx, pts, maxw=3, hot=False, side=1, ghost=True, phase=0, head=True, dim=0, tipw=None, ghost_off=None):
    """가는 은빛 틈: 바깥(side 쪽) 가장자리가 가장 밝고, 머리(끝 점)가 가장 밝고 뾰족, 꼬리 1도트.
    dim = 0(새것)~3(식음) — 색을 한 단계씩 낮춘다. ghost = 안쪽 1도트 잔상 실선(끊김이 흐름)."""
    P = densify(pts)
    N = normals(P)
    n = len(P)
    if n < 2:
        return P
    lay_cols = [
        [G[13], G[14], X0 if hot else G[14]],   # 가장자리: 몸 → 머리 → 머리끝
        [G[11], G[12], X1 if hot else G[13]],
        [SL[7], G[9], G[11]],
    ]
    for i, (x, y) in enumerate(P):
        t = i / (n - 1)
        # 폭: 꼬리 1 → 머리 앞 maxw → 끝 1
        w = 1 + (maxw - 1) * smooth(t / 0.75) * (1 - smooth((t - 0.9) / 0.1))
        w = int(round(w))
        part = 0 if t < 0.6 else (1 if t < 0.93 or not head else 2)
        for k in range(w):
            c = lay_cols[min(k, 2)][part]
            c = _dim(c, dim)
            nx, ny = N[i]
            fx.put(x - nx * k * side, y - ny * k * side, c)
    if ghost:
        go = ghost_off if ghost_off is not None else maxw + 2
        for i, (x, y) in enumerate(P):
            t = i / (n - 1)
            if t < 0.08 or t > 0.85:
                continue
            if ((i + phase) // 7) % 3 == 2:
                continue
            nx, ny = N[i]
            fx.put_if_empty(x - nx * go * side, y - ny * go * side, _dim(SL[6] if t < 0.5 else G[8], dim))
    return P


_DIM = {}


def _dim(c, k):
    if k <= 0:
        return c
    order = [X0, X1, G[14], G[13], G[12], G[11], G[10], G[9], G[8], SL[7], G[7], SL[6], G[6], SL[5], SL[4], SL[3]]
    keys = [o[:3] for o in order]
    if c[:3] in keys:
        i = keys.index(c[:3])
        return order[min(len(order) - 1, i + 2 * k)]
    return c


def slit_decay(fx, pts, age, seed=0, side=1, seg=9):
    """마디로 끊기며 법선으로 엇갈려 벌어지는 베인 자국 + 쇳가루 점. age 0~1."""
    rng = random.Random(seed)
    P = densify(pts)
    N = normals(P)
    n = len(P)
    gap = 2 + int(age * 6)
    i = 0
    k = 0
    cols = [G[12], G[10], SL[7], SL[6]]
    c = cols[min(3, int(age * 3.2))]
    while i < n:
        L = seg - int(age * 3)
        off = (1 if k % 2 else -1) * age * 3.0
        for j in range(i, min(n, i + L)):
            x, y = P[j]
            nx, ny = N[j]
            fx.put(x + nx * off, y + ny * off, c)
        if rng.random() < 0.5:
            j = min(n - 1, i + L // 2)
            x, y = P[j]
            nx, ny = N[j]
            fx.put(x - nx * (off + 3 * side) + rng.randint(-1, 1), y - ny * (off + 3 * side) + rng.randint(-1, 1), SL[5])
        i += L + gap
        k += 1


def star4(fx, x, y, arm, hot=True, diag=False, col=None):
    """4갈래 별(첫 판정 칸) — 가운데 백열, 팔 끝으로 G13→G11."""
    c0 = col or (X0 if hot else G[14])
    fx.put(x, y, c0)
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)] if not diag else [(1, 1), (-1, 1), (1, -1), (-1, -1)]
    for dx, dy in dirs:
        for k in range(1, arm + 1):
            t = k / arm
            c = (X1 if hot else G[14]) if t < 0.35 else (G[13] if t < 0.7 else G[11])
            fx.put(x + dx * k, y + dy * k, c)


def embers(fx, cx, cy, n, spread, rng, cols=None, up=0.0):
    cols = cols or [A[25], A[23], A[21], A[19]]
    for _ in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.3, 1.0) * spread
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.8 - up * rng.random()
        c = rng.choice(cols)
        fx.put(x, y, c)
        if rng.random() < 0.3:
            fx.put(x, y + 1, cols[-1])


# ---------------------------------------------------------------- 먼지·돌·금·그림자
def puff(fx, cx, cy, r, ramp, sy=0.85, seed=None):
    """먼지 덩이(구름): 작은 원 2~3개가 겹친 덩이 — 아래 1도트 그늘 · 몸 · 위 왼쪽 밝음 · 윗 테 · 바깥 체커 보풀.
    ramp = [그늘, 몸, 밝음, 테]."""
    if r < 1.2:
        fx.put(cx, cy, ramp[1])
        return
    rng = random.Random(seed if seed is not None else int(cx * 7919 + cy * 104729 + r * 31))
    subs = [(cx, cy, r)]
    if r >= 2.5:
        for _ in range(2):
            subs.append((cx + rng.uniform(-0.75, 0.75) * r, cy + rng.uniform(-0.55, 0.15) * r * sy, r * rng.uniform(0.5, 0.72)))
    # 보풀(체커) — 바깥 1도트
    for x, y, rr in subs:
        for yy in range(int(y - (rr + 2) * sy) - 1, int(y + (rr + 2) * sy) + 2):
            for xx in range(int(x - rr - 2), int(x + rr + 3)):
                d = math.hypot(xx - x, (yy - y) / sy)
                if rr < d <= rr + 1.3 and (xx + yy) % 2 == 0:
                    fx.put_if_empty(xx, yy, ramp[0])
    for x, y, rr in subs:
        fx.disc(x, y + 1, rr, ramp[0], sy)
    for x, y, rr in subs:
        fx.disc(x, y, rr * 0.92, ramp[1], sy)
    for x, y, rr in subs:
        fx.disc(x - rr * 0.22, y - rr * 0.32 * sy, rr * 0.55, ramp[2], sy)
    for x, y, rr in subs:
        if rr >= 2.5:
            for a in range(205, 300, 9):
                px_, py_ = x + math.cos(math.radians(a)) * rr * 0.8, y + math.sin(math.radians(a)) * rr * 0.8 * sy
                if fx.get(px_, py_) in (ramp[1], ramp[2]):
                    fx.put(px_, py_, ramp[3])


DUST_ASH = [S[0], S[1], S[2], S[3]]
DUST_BROWN = [B[1], B[2], B[3], S[2]]
DUST_COOL = [SL[3], SL[5], SL[6], G[8]]


def chunk(fx, cx, cy, r, ang, rng, ramp=None):
    """돌 파편(3~5각): 어두운 테 + 몸 + 윗면 밝음."""
    ramp = ramp or [B[0], S[0], S[2], S[3]]
    k = rng.randint(4, 5)
    poly = []
    for i in range(k):
        a = ang + i * 2 * math.pi / k + rng.uniform(-0.4, 0.4)
        rr = r * rng.uniform(0.7, 1.15)
        poly.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    fill_poly(fx, poly, ramp[1])
    # 테(아래쪽 어둠)·윗면(밝음)
    for i in range(k):
        a, b = poly[i], poly[(i + 1) % k]
        my = (a[1] + b[1]) / 2
        col = ramp[3] if my < cy - r * 0.2 else (ramp[0] if my > cy + r * 0.1 else ramp[2])
        fx.line(a[0], a[1], b[0], b[1], col)


def fill_poly(fx, poly, c):
    ys = [p[1] for p in poly]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        xs = []
        n = len(poly)
        for i in range(n):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
            if (y0 <= y + 0.5 < y1) or (y1 <= y + 0.5 < y0):
                xs.append(x0 + (y + 0.5 - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            for x in range(int(math.ceil(xs[j] - 0.5)), int(math.floor(xs[j + 1] - 0.5)) + 1):
                fx.put(x, y, c)


def crack_tree(x, y, ang, length, rng, depth=2, jitter=0.35, step=2.5, branch_p=0.18):
    """갈라지는 금 — 선분 목록 [(점들, 굵기단계)]."""
    out = []

    def walk(x, y, ang, L, d):
        pts = [(x, y)]
        a = ang
        s = 0.0
        while s < L:
            a += rng.uniform(-jitter, jitter)
            a = lerp(a, ang, 0.25)
            x += math.cos(a) * step
            y += math.sin(a) * step
            pts.append((x, y))
            s += step
            if d > 0 and rng.random() < branch_p and s > L * 0.2:
                walk(x, y, a + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9), (L - s) * rng.uniform(0.35, 0.6), d - 1)
        out.append((pts, d))

    walk(x, y, ang, length, depth)
    return out


def draw_cracks(fx, tree, core, shadow, sy=1.0, cx=0, cy=0, grow=1.0, edge=None, thick=False):
    """금: 아래 1도트 그림자 + 1도트 심(가지는 가는 쪽). grow(0~1) = 자라난 비율. sy = 바닥 납작."""
    for pts, d in tree:
        m = max(2, int(len(pts) * grow))
        P = [(cx + (px - cx), cy + (py - cy) * sy) for px, py in pts[:m]]
        if len(P) < 2:
            continue
        D = densify(P)
        for x, y in D:
            fx.put_if_empty(x, y + 1, shadow)
        top = max(dd for _, dd in tree)
        for i, (x, y) in enumerate(D):
            fx.put(x, y, core if (d > 0 or i < len(D) * 0.7) else (edge or core))
            if thick and d == top and i < len(D) * 0.55:
                fx.put(x + 1, y, core)
                fx.put_if_empty(x + 1, y + 1, shadow)


def ground_shadow(fx, cx, cy, rx, ry, c=None, dense=True):
    """발밑 그림자(반투명 금지 → 체커 디더). dense=False 면 가장자리만 성기게."""
    c = c or G[0]
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d > 1:
                continue
            on = (x + y) % 2 == 0 if d > 0.45 else ((x + y) % 2 == 0 or (dense and y % 2 == 0))
            if on:
                fx.put_if_empty(x, y, c)


# ---------------------------------------------------------------- 불(pool_liquor_fire 계열)
FIRE = [A[19], A[21], A[23], A[25]]          # 바깥 → 심
FIRE_HOT = [A[19], A[21], A[23], A[25], A[26]]
LIQ = [A[17], A[18], A[19], A[23]]             # 술: 그늘·몸·밝음·반짝


def flame(fx, x, yb, h, w, lean=0.0, cols=None, fld=None):
    """혓바닥 불꽃: 밑이 둥글고 끝이 뾰족·휘어짐. cols = 바깥→심. yb = 밑동(바닥) y. 정수 행으로 그림(줄무늬 없음)."""
    cols = cols or FIRE
    rb = max(1.0, w * 0.5)
    yb = int(round(yb))
    ytop = int(round(yb - h))
    ybot = int(round(yb + rb * 0.6))
    for yy in range(ytop, ybot + 1):
        if yy > yb:   # 둥근 밑(납작)
            q = (yy - yb) / (rb * 0.6 + 1e-6)
            hw = rb * math.sqrt(max(0.0, 1 - q * q))
            t = 0.0
        else:
            t = clamp((yb - yy) / max(1.0, h))
            hw = rb * (1 - t) ** 0.85
        cxl = x + lean * t * t
        if hw < 0.35:
            fx.put(cxl, yy, cols[min(1, len(cols) - 1)])
            continue
        for xx in range(int(math.floor(cxl - hw)), int(math.ceil(cxl + hw)) + 1):
            u = abs(xx - cxl) / (hw + 0.5)
            if u > 1:
                continue
            core = (1 - u) * (1 - t * 0.7)
            idx = 0 if core < 0.18 else 1 if core < 0.4 else 2 if core < 0.6 else 3
            idx = min(idx, len(cols) - 1)
            fx.put(xx, yy, cols[idx])


# ---------------------------------------------------------------- 주인공 실루엣
_SIL = {}


def hero_mask(direction="down", frame=0, sheet="player/v3/player_idle"):
    key = (sheet, direction, frame)
    if key not in _SIL:
        m = gridsheet.load_meta(os.path.join(SPR, sheet + ".json"))
        g = gridsheet.open_grid(os.path.join(SPR, sheet + ".json"))
        fw, fh = m["frameWidth"], m["frameHeight"]
        r = m["directions"].index(direction)
        im = g.crop((frame * fw, r * fh, (frame + 1) * fw, (r + 1) * fh))
        px = im.load()
        pts = {(x, y) for y in range(fh) for x in range(fw) if px[x, y][3]}
        lum = {(x, y): sum(px[x, y][:3]) / 765.0 for (x, y) in pts}
        _SIL[key] = (pts, lum, m["pivot"], (fw, fh))
    return _SIL[key]


def draw_sil(fx, mask, dx, dy, body, rim, top=None, keep=None, lum=None, light=None):
    """실루엣(점 집합)을 (dx,dy) 만큼 옮겨 그림. 테 = 바깥 1도트, top = 윗/왼쪽 테 밝음. light = (문턱, 색) 원 그림 밝은 곳 강조."""
    for (x, y) in mask:
        if keep and not keep(x, y):
            continue
        c = body
        if light and lum and lum.get((x, y), 0) > light[0]:
            c = light[1]
        edge = any((x + ax, y + ay) not in mask for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            c = rim
            if top and ((x, y - 1) not in mask or (x - 1, y) not in mask):
                c = top
        fx.put(x + dx, y + dy, c)


# ---------------------------------------------------------------- 검사·내보내기
def check_frames(name, frames, glow, max_colors=16):
    cols = set()
    for i, im in enumerate(frames):
        a = set(im.getchannel("A").getdata())
        assert a <= {0, 255}, (name, i, "반투명")
        cs = {p[:3] for p in im.getdata() if p[3]}
        if i not in glow:
            bad = cs & HOT
            assert not bad, (name, i, "glowFrames 밖 백열", bad)
        cols |= cs
        w, h = im.size
        px = im.load()
        edge = sum(1 for x in range(w) for y in (0, h - 1) if px[x, y][3]) + sum(1 for y in range(h) for x in (0, w - 1) if px[x, y][3])
        assert edge == 0, (name, i, "틀 가장자리", edge)
        assert any(p[3] for p in im.getdata()) or i > 0, (name, i, "빈 첫 칸")
    assert len(cols) <= max_colors, (name, "색 수", len(cols))
    return len(cols)


def clear_edge(im):
    px = im.load()
    w, h = im.size
    for x in range(w):
        px[x, 0] = px[x, h - 1] = (0, 0, 0, 0)
    for y in range(h):
        px[0, y] = px[w - 1, y] = (0, 0, 0, 0)
    return im


_ab = {}


def atlas_mod():
    if "m" not in _ab:
        spec = importlib.util.spec_from_file_location("atlas57_build_tkg", os.path.join(WORK, "atlas57", "build.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _ab["m"] = m
    return _ab["m"]


def publish(name, frames, meta):
    """격자 원본(out/grid) + assets/sprites/fx/v3 트림 아틀라스."""
    fw, fh = frames[0].size
    n = len(frames)
    sheet = Image.new("RGBA", (fw * n, fh), (0, 0, 0, 0))
    for c, im in enumerate(frames):
        sheet.alpha_composite(im, (c * fw, 0))
    m = dict(meta)
    m.update(image=name + ".png", frameWidth=fw, frameHeight=fh, frames=n)
    os.makedirs(GRID, exist_ok=True)
    gp, gj = os.path.join(GRID, name + ".png"), os.path.join(GRID, name + ".json")
    sheet.save(gp, optimize=True)
    with open(gj, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    pp, jp = os.path.join(FXDIR, name + ".png"), os.path.join(FXDIR, name + ".json")
    if os.path.exists(jp):
        om = json.load(open(jp, encoding="utf-8"))
        for t in om.get("textures", []):
            p = os.path.join(FXDIR, t["image"])
            if os.path.exists(p):
                os.remove(p)
    shutil.copy2(gp, pp)
    shutil.copy2(gj, jp)
    ab = atlas_mod()
    tmp = os.path.join(HERE, "out", "_atlas_tmp_tkg_%d" % os.getpid())
    os.makedirs(tmp, exist_ok=True)
    try:
        res = ab.convert_sheet(pp, jp, tmp, 2, 4096, True)
        ab.apply_in_place(res, tmp, FXDIR, pp, jp, 4096)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    am = json.load(open(jp, encoding="utf-8"))
    sz = am["meta"]["size"]
    return dict(page=[sz["w"], sz["h"]], mb=round(sz["w"] * sz["h"] * 4 / 1048576.0, 3), png_kb=round(os.path.getsize(pp) / 1024.0, 1))
