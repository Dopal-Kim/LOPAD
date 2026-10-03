"""fx_v3 drawing kit — pure Python (no numpy).

Every shape is a curve sampled densely and *stamped* with a disc whose radius
and value vary along the curve. Inside a layer values combine with max(), so
overlapping strokes melt into one shape and the brightest line stays the
centre line. A layer's value (0..1) is quantised onto its colour ramp
(dark -> bright) at render time. Pixels are always fully opaque (pixel art).

Coordinates are v3 dots (pixelScale 0.5).
"""
import math
import random

# ---------------------------------------------------------------- palette
GRAY = ["#000000", "#141516", "#212224", "#2f3033", "#3e3f42", "#4d4f52",
        "#5c5e62", "#6c6f73", "#7d8084", "#8e9195", "#a0a2a6", "#b2b4b8",
        "#c5c6c9", "#d8d9db", "#ebeced", "#ffffff"]
# floor 1 accent ramp = slots 16..27 (runtime swap per floor)
A = ["#1a110f", "#3f271d", "#653b24", "#8b4d22", "#b0611a", "#d67a11",
     "#dc8e23", "#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0"]
X0, X1 = "#ffffff", "#fff4dc"
# hero v3 warm ash (fixed colours shared with player/v3 — not swapped)
ASH = ["#2a1e17", "#3b2a1f", "#4f3828", "#664a33", "#45403b", "#5c554e", "#756c62"]

ALLOWED = set(GRAY) | set(A) | {X0, X1} | set(ASH)

# ramps (dark -> bright)
R_HOT = [A[2], A[4], A[5], A[7], A[9], X1, X0]          # sparks / rays / rings
R_HOT_DIM = [A[1], A[2], A[3], A[4], A[5]]               # cooling
R_EMBER = [A[1], A[3], A[5], A[7]]
R_DUST = [ASH[4], ASH[5], ASH[6], GRAY[9], GRAY[11]]     # ash dust (warm grey, lit top)
R_DUSTD = [ASH[0], ASH[1], ASH[4], ASH[5]]               # dust, darker
R_FLAKE = [ASH[0], ASH[2], ASH[3], ASH[6]]               # ash crust flakes
R_BLOOD = [A[0], A[1], A[2], A[3], A[4]]
R_PALE = [GRAY[6], GRAY[9], GRAY[11], GRAY[13], GRAY[14], X0]
R_TEL = [A[1], A[2], A[3], A[4], A[5], A[7], A[9], X1, X0]  # telegraph body
R_FIRE = [A[1], A[2], A[4], A[5], A[6], A[7], A[9], X1]


def hexrgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def frac(x):
    return x - math.floor(x)


# ---------------------------------------------------------------- curves
def lerp(a, b, t):
    return a + (b - a) * t


def qbez(p0, p1, p2, n=None):
    """quadratic bezier -> list of points"""
    if n is None:
        L = math.dist(p0, p1) + math.dist(p1, p2)
        n = max(2, int(L * 3))
    out = []
    for i in range(n + 1):
        t = i / n
        a = (lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t))
        b = (lerp(p1[0], p2[0], t), lerp(p1[1], p2[1], t))
        out.append((lerp(a[0], b[0], t), lerp(a[1], b[1], t)))
    return out


def resample(pts, step=0.3):
    """polyline -> evenly spaced samples with t in 0..1 (by length)"""
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(seg) or 1e-6
    n = max(2, int(total / step))
    out = []
    i, acc = 0, 0.0
    for k in range(n + 1):
        s = total * k / n
        while i < len(seg) - 1 and acc + seg[i] < s:
            acc += seg[i]
            i += 1
        u = 0.0 if seg[i] == 0 else (s - acc) / seg[i]
        u = clamp(u)
        x = lerp(pts[i][0], pts[i + 1][0], u)
        y = lerp(pts[i][1], pts[i + 1][1], u)
        out.append((x, y, k / n))
    return out, total


# width profiles: f(t) -> 0..1
def tp_both(p=0.6, peak=0.5):
    def f(t):
        if t <= peak:
            return (t / peak) ** p if peak > 0 else 1.0
        return ((1 - t) / (1 - peak)) ** p if peak < 1 else 1.0
    return f


def tp_tail(p=0.8):            # wide at start, pointed end
    return lambda t: (1 - t) ** p


def tp_head(p=0.8):            # pointed start, wide end
    return lambda t: t ** p


def tp_const():
    return lambda t: 1.0


# ---------------------------------------------------------------- layer
class Layer:
    def __init__(self, cv, ramp, gamma=1.0, vmin=0.04):
        self.cv = cv
        self.ramp = [hexrgb(c) for c in ramp]
        self.hex = list(ramp)
        self.gamma = gamma
        self.vmin = vmin
        self.v = {}

    # --- core
    def put(self, x, y, v):
        x, y = int(x), int(y)
        if 0 <= x < self.cv.w and 0 <= y < self.cv.h and v > 0:
            k = (x, y)
            if v > self.v.get(k, 0.0):
                self.v[k] = v

    def stamp(self, cx, cy, r, v0=1.0, soft=1.0):
        """disc at (cx,cy) radius r. value falls from v0 (centre) toward the
        edge; soft=0 -> flat."""
        R = r + 0.42
        x0, x1 = int(math.floor(cx - R)), int(math.ceil(cx + R))
        y0, y1 = int(math.floor(cy - R)), int(math.ceil(cy + R))
        for y in range(y0, y1 + 1):
            dy = y + 0.5 - cy
            for x in range(x0, x1 + 1):
                dx = x + 0.5 - cx
                d = math.sqrt(dx * dx + dy * dy)
                if d <= R:
                    self.put(x, y, v0 * (1 - soft * (d / R) * 0.85))

    # --- strokes
    def _chain(self, sm, soft=1.0):
        """sm = list of (x, y, halfwidth, value) or None (gap). Rasterises the
        chain of tapered capsules exactly (distance to segment, width and value
        interpolated at the projection) -> no stamp ripples."""
        put = self.put
        for i in range(len(sm) - 1):
            a, b = sm[i], sm[i + 1]
            if a is None or b is None:
                continue
            ax, ay, aw, av = a
            bx, by, bw, bv = b
            if aw <= 0.02 and bw <= 0.02:
                aw = bw = 0.02
            ex, ey = bx - ax, by - ay
            ll = ex * ex + ey * ey
            R = max(aw, bw) + 0.42
            x0, x1 = int(math.floor(min(ax, bx) - R)), int(math.ceil(max(ax, bx) + R))
            y0, y1 = int(math.floor(min(ay, by) - R)), int(math.ceil(max(ay, by) + R))
            for y in range(y0, y1 + 1):
                py = y + 0.5
                for x in range(x0, x1 + 1):
                    px = x + 0.5
                    u = 0.0 if ll == 0 else ((px - ax) * ex + (py - ay) * ey) / ll
                    u = 0.0 if u < 0 else 1.0 if u > 1 else u
                    dx, dy = px - (ax + ex * u), py - (ay + ey * u)
                    d = math.sqrt(dx * dx + dy * dy)
                    rr = aw + (bw - aw) * u + 0.42
                    if d <= rr:
                        put(x, y, (av + (bv - av) * u) * (1 - soft * 0.85 * d / rr))

    def stroke(self, pts, w, prof=None, v=1.0, vprof=None, soft=1.0, step=0.6,
               dash=None):
        """pts polyline; w = max half-width; prof(t)->0..1 width; vprof(t)->0..1
        value. dash = (period_px, duty, phase) along the curve, dash ends taper."""
        prof = prof or tp_const()
        sm, L = resample(pts, step)
        out = []
        for x, y, t in sm:
            k = prof(t)
            vv = v * (vprof(t) if vprof else 1.0)
            if dash:
                per, duty, ph = dash
                s = frac(t * L / per + ph)
                if s > duty:
                    out.append(None)
                    continue
                k *= math.sin(math.pi * s / duty) ** 0.5
            out.append((x, y, w * k, vv))
        self._chain(out, soft)

    def curve(self, p0, p1, p2, w, **kw):
        self.stroke(qbez(p0, p1, p2), w, **kw)

    def ray(self, cx, cy, ang, r0, r1, w, bend=0.0, **kw):
        """straight/bent line from radius r0 to r1 at angle ang (rad)."""
        ca, sa = math.cos(ang), math.sin(ang)
        p0 = (cx + ca * r0, cy + sa * r0)
        p2 = (cx + ca * r1, cy + sa * r1)
        rm = (r0 + r1) / 2
        p1 = (cx + ca * rm - sa * bend, cy + sa * rm + ca * bend)
        self.stroke(qbez(p0, p1, p2), w, **kw)

    def arc(self, cx, cy, rx, ry, a0, a1, w, prof=None, v=1.0, vprof=None,
            dash=None, soft=1.0):
        """elliptic arc from angle a0 to a1 (rad). dash=(count_per_turn, duty, phase)"""
        L = abs(a1 - a0) * (rx + ry) / 2
        n = max(8, int(L / 0.6))
        prof = prof or tp_const()
        out = []
        for i in range(n + 1):
            t = i / n
            a = lerp(a0, a1, t)
            k = prof(t)
            if dash:
                cnt, duty, ph = dash
                s = frac(a / (2 * math.pi) * cnt + ph)
                if s > duty:
                    out.append(None)
                    continue
                k *= math.sin(math.pi * s / duty) ** 0.5
            vv = v * (vprof(t) if vprof else 1.0)
            out.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry, w * k, vv))
        self._chain(out, soft)

    def ring(self, cx, cy, r, w, ry=None, **kw):
        self.arc(cx, cy, r, r if ry is None else ry, 0, 2 * math.pi, w, **kw)

    # --- fills
    def disc(self, cx, cy, rx, ry=None, v=1.0, edge=0.25):
        """filled ellipse, value = v at centre .. v*edge at rim"""
        ry = rx if ry is None else ry
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                q = math.hypot((x + 0.5 - cx) / (rx + 0.42), (y + 0.5 - cy) / (ry + 0.42))
                if q <= 1:
                    self.put(x, y, v * (1 - (1 - edge) * q))

    def puff(self, cx, cy, r, v=1.0, ry=None, light=0.35):
        """dust cloud lobe: rounded, lit from the top"""
        ry = r if ry is None else ry
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                dx, dy = (x + 0.5 - cx) / (r + 0.42), (y + 0.5 - cy) / (ry + 0.42)
                q = math.hypot(dx, dy)
                if q <= 1:
                    if q > 0.8 and (x + y) % 2:
                        continue                      # soft checker fringe
                    s = 0.8 - 0.2 * q - light * dy
                    self.put(x, y, v * clamp(s, 0.3, 1))

    def cloud(self, cx, cy, r, v=1.0, flat=0.8, seed=0):
        """organic dust cloud: 3 overlapping lobes (big top-centre, two low sides)"""
        import random as _r
        R = _r.Random(seed)
        for ox, oy, k in ((0, -0.25, 1.0), (-0.55, 0.15, 0.68), (0.6, 0.2, 0.62)):
            k *= R.uniform(0.85, 1.1)
            self.puff(cx + ox * r, cy + oy * r * flat, r * k, v=v, ry=r * k * flat)

    def star4(self, cx, cy, size, w=1.0, v=1.0, rot=0.0, diag=0.0):
        """4-point glint: thin needles tapering to points"""
        for k in range(4):
            a = rot + k * math.pi / 2
            self.ray(cx, cy, a, 0, size, w, prof=tp_tail(0.9), v=v)
        if diag:
            for k in range(4):
                a = rot + math.pi / 4 + k * math.pi / 2
                self.ray(cx, cy, a, 0, size * diag, w * 0.7, prof=tp_tail(1.0), v=v * 0.8)
        self.stamp(cx, cy, w * 1.1, v)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.layers = []

    def layer(self, ramp, gamma=1.0, vmin=0.04):
        L = Layer(self, ramp, gamma, vmin)
        self.layers.append(L)
        return L

    def render(self, img=None, ox=0, oy=0):
        from PIL import Image
        if img is None:
            img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        px = img.load()
        for L in self.layers:
            n = len(L.ramp)
            for (x, y), v in L.v.items():
                if v < L.vmin:
                    continue
                i = min(n - 1, int((v ** L.gamma) * n))
                r, g, b = L.ramp[i]
                px[ox + x, oy + y] = (r, g, b, 255)
        return img


def rng(seed):
    return random.Random(seed)


DIRS = ["down", "up", "left", "right"]
DVEC = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}
DANG = {"down": math.pi / 2, "up": -math.pi / 2, "left": math.pi, "right": 0.0}
