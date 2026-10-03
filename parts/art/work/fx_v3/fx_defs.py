"""fx_v3 designs — weapon-independent common fx, redrawn at v3 density.

Each builder returns {direction: [PIL frames]} at v3 size (old dots x4,
pixelScale 0.5 -> same on-screen size as the old pixelScale-2 sheets).
dash_trail follows the hero v3 body (96x144).
"""
import math
from PIL import Image
from fxkit import (Canvas, rng, frac, clamp, tp_both, tp_tail, tp_head, tp_const,
                   qbez, DIRS, DVEC, DANG, GRAY, A, X0, X1, ASH,
                   R_HOT, R_HOT_DIM, R_EMBER, R_DUST, R_DUSTD, R_FLAKE, R_BLOOD,
                   R_PALE, R_TEL, R_FIRE)

TAU = 2 * math.pi


# ======================================================================
# shared bits
def sparks(L, cx, cy, n, r0, r1, length, w, v, seed, ang0=0.0, spread=TAU,
           yscale=1.0, grav=0.0):
    """streaks flying outward: pointed head (outer), thin tail toward centre"""
    R = rng(seed)
    for i in range(n):
        a = ang0 - spread / 2 + spread * (i + R.random() * 0.8) / n
        r = R.uniform(r0, r1)
        ln = length * R.uniform(0.6, 1.2)
        ca, sa = math.cos(a), math.sin(a) * yscale
        hx, hy = cx + ca * r, cy + sa * r + grav * (r / max(r1, 1)) ** 2
        tx, ty = cx + ca * (r - ln), cy + sa * (r - ln)
        L.stroke([(tx, ty), (hx, hy)], w, prof=tp_head(0.7), v=v * R.uniform(0.75, 1.0))


def flakes(L, cx, cy, n, r0, r1, size, v, seed, ang0=0.0, spread=TAU, yscale=1.0,
           lift=0.0):
    """small ash crust bits: 2-4 dot slanted chips"""
    R = rng(seed)
    for i in range(n):
        a = ang0 - spread / 2 + spread * R.random()
        r = R.uniform(r0, r1)
        x = cx + math.cos(a) * r
        y = cy + math.sin(a) * r * yscale - lift * R.random()
        s = size * R.uniform(0.6, 1.2)
        b = R.uniform(0, TAU)
        L.stroke([(x - math.cos(b) * s, y - math.sin(b) * s * 0.6),
                  (x + math.cos(b) * s, y + math.sin(b) * s * 0.6)],
                 0.9 * s / 2 + 0.3, prof=tp_both(0.4, R.uniform(0.3, 0.7)),
                 v=v * R.uniform(0.6, 1.0), soft=0.6)


def tel_ramp(f):
    """telegraph band for progress frame f (0..5): rim / flat body / 1px core —
    few steps so the band has no staircase banding"""
    body = [A[3], A[4], A[5], A[6], A[8], A[10]][f]
    core = [A[6], A[7], A[8], A[9], X1, X0][f]
    return [A[1], body, body, body, core]


R_DUSTSOFT = [ASH[0], ASH[1], ASH[4], ASH[5], ASH[6]]
R_DUSTM = [ASH[1], ASH[4], ASH[5], ASH[6], GRAY[9]]      # mid dust (dash / knock)


def frames_any(fn, n):
    return {"any": [fn(i) for i in range(n)]}


# ======================================================================
# hit_burst / hit_spark  (24 -> 96)
def hit_burst():
    W = 96
    c = W / 2
    R = rng(11)
    rays = []
    for k in range(6):
        a = k * TAU / 6 + R.uniform(-0.28, 0.28) + 0.3
        rays.append((a, R.uniform(28, 40), R.uniform(-3, 3)))

    def frame(f):
        cv = Canvas(W, W)
        if f == 0:
            G = cv.layer(R_HOT_DIM)
            G.ring(c, c, 17, 1.1, v=0.8, dash=(10, 0.55, 0.1))
            L = cv.layer(R_HOT)
            for k in range(4):
                a = k * TAU / 4 + 0.3
                L.ray(c, c, a, 0, 28, 2.0, prof=tp_tail(0.9))
            for k in range(4):
                a = k * TAU / 4 + 0.3 + TAU / 8
                L.ray(c, c, a, 0, 15, 1.4, prof=tp_tail(1.0), v=0.85)
            L.disc(c, c, 10.5, v=1.0, edge=0.42)
        elif f == 1:
            G = cv.layer(R_HOT_DIM)
            G.ring(c, c, 17, 0.9, v=0.8, dash=(12, 0.6, 0.3))
            L = cv.layer(R_HOT)
            for a, ln, b in rays:
                L.ray(c, c, a, 3, ln, 2.9, bend=b, prof=tp_both(0.55, 0.32))
            L.disc(c, c, 4.2, v=0.95, edge=0.5)
        elif f == 2:
            G = cv.layer(R_HOT_DIM)
            G.ring(c, c, 24, 0.8, v=0.6, dash=(14, 0.4, 0.15))
            L = cv.layer(R_HOT)
            for a, ln, b in rays:
                L.ray(c, c, a, ln * 0.55, ln + 4, 1.7, bend=b * 0.5,
                      prof=tp_both(0.6, 0.65), v=0.82)
            sparks(L, c, c, 9, 30, 42, 6, 1.0, 0.75, seed=21, ang0=0.6)
            L.stamp(c, c, 1.6, 0.6)
        else:
            L = cv.layer(R_EMBER)
            sparks(L, c, c, 9, 38, 46, 4, 0.8, 0.7, seed=21, ang0=0.6)
            for a, ln, b in rays:
                L.ray(c, c, a, ln + 2, ln + 9, 0.9, prof=tp_both(0.6, 0.6), v=0.55)
            D = cv.layer(R_DUSTD)
            flakes(D, c, c, 6, 20, 34, 1.4, 0.9, seed=23)
        return cv.render()
    return frames_any(frame, 4)


# ======================================================================
# crit_burst (32 -> 128)
def crit_burst():
    W = 128
    c = W / 2
    R = rng(31)
    rays = []
    for k in range(8):
        a = k * TAU / 8 + R.uniform(-0.12, 0.12) + 0.2
        rays.append((a, (54 if k % 2 == 0 else 40) * R.uniform(0.9, 1.05)))

    def glints(L, r, size, v):
        for k in range(4):
            a = TAU / 8 + k * TAU / 4
            L.star4(c + math.cos(a) * r, c + math.sin(a) * r, size, 0.9, v)

    def frame(f):
        cv = Canvas(W, W)
        if f == 0:
            G = cv.layer(R_HOT_DIM)
            G.ring(c, c, 23, 1.3, v=0.85, dash=(14, 0.6, 0))
            L = cv.layer(R_HOT)
            for a, ln in rays:
                L.ray(c, c, a, 0, ln * 0.5, 1.8, prof=tp_tail(0.9))
            L.disc(c, c, 15, v=1.0, edge=0.42)
        elif f == 1:
            G = cv.layer(R_HOT_DIM)
            G.ring(c, c, 21, 1.0, v=0.85)
            L = cv.layer(R_HOT)
            for a, ln in rays:
                L.ray(c, c, a, 2, ln, 2.6, prof=tp_both(0.55, 0.3))
            L.star4(c, c, 14, 1.4, 1.0, rot=0.2 + TAU / 16)
            L.disc(c, c, 5, v=1.0, edge=0.6)
        elif f == 2:
            G = cv.layer(R_HOT)
            G.ring(c, c, 34, 1.5, v=0.8)
            L = cv.layer(R_HOT)
            for a, ln in rays:
                L.ray(c, c, a, ln * 0.45, ln + 4, 1.9, prof=tp_both(0.6, 0.62), v=0.85)
            glints(L, 47, 7, 0.95)
            L.star4(c, c, 6, 1.0, 0.85)
        elif f == 3:
            G = cv.layer(R_HOT_DIM)
            G.ring(c, c, 46, 1.2, v=0.85, dash=(18, 0.6, 0.1))
            L = cv.layer(R_HOT)
            sparks(L, c, c, 12, 48, 58, 7, 1.0, 0.75, seed=33, ang0=0.2)
            glints(L, 52, 5, 0.65)
        else:
            G = cv.layer(R_EMBER)
            G.ring(c, c, 55, 0.9, v=0.55, dash=(18, 0.28, 0.25))
            sparks(G, c, c, 12, 55, 62, 4, 0.8, 0.7, seed=33, ang0=0.2)
            glints(G, 55, 3, 0.5)
        return cv.render()
    return frames_any(frame, 5)


# ======================================================================
# player_hit (24 -> 96): no accent (the hero does not bleed) — white crack
# flash + flung ash crust (hero ash)
def player_hit():
    W = 96
    c = W / 2
    R = rng(41)
    cracks = []
    for k in range(5):
        a = k * TAU / 5 + R.uniform(-0.3, 0.3) - 0.4
        ln = R.uniform(17, 25)
        pts = [(c, c)]
        r, aa = 0, a
        for s in range(3):
            r += ln / 3
            aa += R.uniform(-0.35, 0.35)
            pts.append((c + math.cos(aa) * r, c + math.sin(aa) * r))
        cracks.append(pts)

    def frame(f):
        cv = Canvas(W, W)
        if f == 0:
            L = cv.layer(R_PALE)
            for p in cracks:
                L.stroke(p, 1.7, prof=tp_tail(0.7))
            L.disc(c, c, 5.5, v=1.0, edge=0.55)
            F = cv.layer(R_FLAKE)
            flakes(F, c, c, 6, 9, 15, 1.8, 1.0, seed=43)
        elif f == 1:
            L = cv.layer([GRAY[4], GRAY[6], GRAY[9], GRAY[11]])
            for p in cracks:
                L.stroke(p[1:], 1.1, prof=tp_both(0.6, 0.3), v=0.9)
            F = cv.layer(R_FLAKE)
            flakes(F, c, c, 10, 18, 30, 2.0, 1.0, seed=43)
            D = cv.layer(R_DUST)
            for k in range(3):
                a = k * TAU / 3 + 0.5
                D.arc(c + math.cos(a) * 13, c + math.sin(a) * 10, 5, 4, math.pi * 1.0,
                      math.pi * 2.0, 0.9, prof=tp_both(0.5), v=0.7)
        else:
            F = cv.layer(R_FLAKE)
            flakes(F, c, c, 10, 28, 40, 1.4, 0.8, seed=43)
            D = cv.layer(R_DUST)
            for k in range(3):
                a = k * TAU / 3 + 0.5
                D.arc(c + math.cos(a) * 19, c + math.sin(a) * 14 - 3, 6.5, 5, math.pi * 1.1,
                      math.pi * 1.9, 0.7, prof=tp_both(0.5), v=0.45)
        return cv.render()
    return frames_any(frame, 3)


# ======================================================================
# blood (24 -> 96), 4 dirs, 5f — dark amber ichor (floor ramp, swapped) +
# ash specks. Direction = attack travel direction.
def blood():
    W = 96
    c = W / 2
    out = {}
    for d in DIRS:
        dx, dy = DVEC[d]
        base = math.atan2(dy, dx)
        R = rng(51)
        drops = []
        for i in range(8):
            a = base + R.uniform(-0.6, 0.6)
            sp = R.uniform(0.7, 1.15)
            drops.append((a, sp, R.uniform(1.4, 2.4)))

        def pos(a, sp, t):
            # flight: t = 0..1, distance with drag, small hop (screen y gravity)
            dist = 40 * sp * (1 - (1 - t) ** 2)
            x = c + math.cos(a) * dist
            y = c + math.sin(a) * dist * 0.85 - 7 * math.sin(math.pi * t) * sp + 6 * t
            return x, y

        frames = []
        for f in range(5):
            cv = Canvas(W, W)
            S = cv.layer(R_BLOOD[:4])                # floor stains
            L = cv.layer(R_BLOOD + [A[6]])          # flying drops
            T = [0.0, 0.25, 0.55, 0.85, 1.0][f]
            if f == 0:
                L.disc(c, c, 8, 7, v=0.8, edge=0.35)
                for a, sp, sz in drops[:5]:
                    L.ray(c, c, a, 4, 15 * sp, 2.4, prof=tp_tail(0.6), v=0.85)
                L.put(c - 2, c - 3, 1.0)
            else:
                for i, (a, sp, sz) in enumerate(drops):
                    land = 0.55 + 0.4 * (i % 3) / 2       # landing time
                    if T < land:
                        hx, hy = pos(a, sp, T)
                        tx, ty = pos(a, sp, max(0.04, T - 0.13))
                        L.stroke([(tx, ty), (hx, hy)], sz, prof=tp_head(0.55), v=0.8)
                        L.put(hx - 0.5, hy - 1, 1.0)          # wet glint
                    else:
                        lx, ly = pos(a, sp, land)
                        fade = 1.0 if f < 4 else 0.6
                        S.disc(lx, ly + 1, sz * 1.5, sz * 0.75, v=0.9 * fade, edge=0.6)
                        # streak where it skidded
                        S.stroke([(lx - math.cos(a) * 5, ly + 1 - math.sin(a) * 2.5),
                                  (lx, ly + 1)], 0.8, prof=tp_head(0.6), v=0.6 * fade)
                if f <= 2:
                    # mist
                    sparks(L, c, c, 6, 8 + 12 * T, 16 + 20 * T, 3, 0.6, 0.55,
                           seed=53 + f, ang0=base, spread=1.4)
                if f >= 3:
                    S.disc(c + dx * 3, c + 2 + dy * 2, 4.5, 2.2, v=0.7 if f == 3 else 0.5,
                           edge=0.6)
                if f == 4:
                    D = cv.layer(R_DUSTD)
                    flakes(D, c + dx * 14, c + dy * 10 + 2, 4, 0, 10, 1.0, 0.7,
                           seed=57, yscale=0.5)
            frames.append(cv.render())
        out[d] = frames
    return out


# ======================================================================
# dash_dust (16x8 -> 64x32), 4 dirs, 3f — ash dust kicked behind the foot
def _ground_dir(d):
    dx, dy = DVEC[d]
    return dx, dy * 0.5


def dash_dust():
    """hero-attached -> drawn at hero v3 scale (old x6 = x4 x 1.5, like dash_trail)"""
    Z = 1.5
    W, H = 96, 48
    px, py = 48, 36
    out = {}
    for d in DIRS:
        bx, by = _ground_dir(d)
        bx, by = -bx, -by                       # dust goes behind
        perp = (-by, bx) if bx else (1, 0)
        R = rng(61)
        lobes = [(R.uniform(-0.6, 0.6), R.uniform(0.5, 1.0), R.uniform(0.8, 1.2))
                 for _ in range(4)]
        frames = []
        for f in range(3):
            cv = Canvas(W, H)
            G = cv.layer(R_DUSTD + [GRAY[9]])
            D = cv.layer(R_DUSTM)
            reach = [10, 18, 24][f] * (0.6 if by else 1.0) * Z
            # a trail of puffs: biggest at the foot, smaller further back,
            # alternating sides (a V when dashing up/down)
            for i, (far, sz, side) in enumerate(((0.15, 1.0, 0), (0.45, 0.8, -1),
                                                 (0.7, 0.66, 1), (1.0, 0.5, -0.6))):
                s = reach * far
                lat = side * (3 + 2.5 * f) * Z * (2.2 if by else 1.0)
                x = px + bx * s + perp[0] * lat
                y = py + by * s + perp[1] * lat * 0.5 - (f * 1.5 + i * 0.6) * Z
                r = [3.4, 5.0, 5.6][f] * sz * Z
                if f < 2:
                    D.cloud(x, y, r, v=[1.0, 0.85][f], flat=0.62, seed=i)
                else:
                    # thinning: only the lit rim of the lobe
                    D.arc(x, y, r, r * 0.7, math.pi * 1.05, math.pi * 1.95, 1.0,
                          prof=tp_both(0.5), v=0.7)
            ang = math.atan2(by, bx) if (bx or by) else 0
            gl = [11, 18, 24][f] * (0.6 if by else 1.0) * Z
            sparks(G, px, py - 1, 6, gl * 0.7, gl, [5, 4, 3][f] * Z, 0.8, [0.95, 0.85, 0.6][f],
                   seed=63, ang0=ang, spread=1.3, yscale=0.6)
            frames.append(cv.render())
        out[d] = frames
    return out


# ======================================================================
# knock_dust (16x8 -> 64x32), 4 dirs, 4f — skid scrape + dust piled in front
def knock_dust():
    W, H = 64, 32
    px, py = 32, 24
    out = {}
    for d in DIRS:
        fx, fy = _ground_dir(d)
        ang = math.atan2(fy, fx)
        perp = (-fy, fx) if fx else (1, 0)
        frames = []
        for f in range(4):
            cv = Canvas(W, H)
            S = cv.layer([ASH[0], ASH[1], ASH[2]])     # scrape marks (behind)
            sl = [10, 14, 14, 12][f]
            for side in (-1, 1):
                ox, oy = perp[0] * side * 3, perp[1] * side * 1.5
                S.stroke([(px - fx * sl + ox, py - fy * sl + oy + 1), (px + ox, py + oy + 1)],
                         0.9, prof=tp_head(0.7), v=[0.9, 0.9, 0.7, 0.45][f])
            D = cv.layer(R_DUSTM)
            # crescent of dust in front
            reach = [7, 12, 16, 18][f] * (0.6 if fy else 1.0)
            for k in range(5):
                side = (k - 2) / 2
                x = px + fx * reach * (1 - 0.25 * abs(side)) + perp[0] * side * (9 + f * 3)
                y = py + fy * reach * (1 - 0.25 * abs(side)) + perp[1] * side * (3 + f) - f
                r = [4.0, 5.5, 6.2, 6.5][f] * (1 - 0.2 * abs(side))
                if f < 3:
                    D.cloud(x, y, r, v=[1.0, 0.9, 0.7][f], flat=0.7, seed=k)
                else:
                    D.arc(x, y, r, r * 0.75, math.pi * 1.1, math.pi * 1.9, 0.7,
                          prof=tp_both(0.5), v=0.55)
            G = cv.layer(R_DUSTD + [GRAY[9]])
            sparks(G, px, py - 1, 4, reach + 2, reach + 6, 3, 0.6, 0.8 - 0.15 * f,
                   seed=71 + f, ang0=ang, spread=1.6, yscale=0.6)
            cv.layers = [cv.layers[0], cv.layers[2], cv.layers[1]]
            frames.append(cv.render())
        out[d] = frames
    return out


# ======================================================================
# dash_trail (16x24 -> hero v3 96x144) — ash silhouette that crumbles
def dash_trail(hero_dash_path):
    sheet = Image.open(hero_dash_path).convert("RGBA")
    FW, FH = 96, 144
    src_frame = 2                                # mid-dash pose
    out = {}
    for r, d in enumerate(DIRS):
        sil = sheet.crop((src_frame * FW, r * FH, (src_frame + 1) * FW, (r + 1) * FH))
        a = sil.load()
        mask = {(x, y) for y in range(FH) for x in range(FW) if a[x, y][3] > 0}
        dx, dy = DVEC[d]
        ys = [y for _, y in mask] or [0]
        top, bot = min(ys), max(ys)
        R = rng(81 + r)
        frames = []
        for f in range(3):
            cv = Canvas(FW, FH)
            B = cv.layer([GRAY[1], GRAY[2], GRAY[3], GRAY[4], ASH[4]])
            E = cv.layer([ASH[1], ASH[4], ASH[5]])
            for (x, y) in mask:
                h = (y - top) / max(1, bot - top)
                # trailing edge = side facing back (-dash dir): lit warm rim
                back = (x - dx, y - dy) not in mask and (x - dx, y - dy) != (x, y)
                edge = any((x + ex, y + ey) not in mask
                           for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                lane = y if dx else x                # stripes run along the motion
                along = x if dx else y
                if f == 1 and (lane % 3 == 0 or (edge and R.random() < 0.5)):
                    continue
                if f == 2 and (lane % 3 != 1 or ((along // 5 + lane * 7) % 3 == 0)):
                    continue
                v = 0.62 - 0.3 * h
                if edge:
                    v = 0.85 if back else 0.2
                B.put(x, y, v * [1.0, 0.85, 0.7][f])
            if f >= 1:
                # ash flakes peeling off the trailing side, drifting up
                pts = list(mask)
                for i in range(14 if f == 1 else 18):
                    x, y = pts[R.randrange(len(pts))]
                    s = (4 + 6 * f) * R.uniform(0.5, 1.2)
                    E.stroke([(x - dx * s, y - dy * s - s * 0.5),
                              (x - dx * s + 1.5, y - dy * s - s * 0.5 - 0.6)], 0.8,
                             prof=tp_both(0.5), v=R.uniform(0.5, 1.0), soft=0.5)
            frames.append(cv.render())
        out[d] = frames
    return out


# ======================================================================
# telegraph_circle (64 -> 256), 6f progress-driven, range ring r88
def telegraph_circle():
    W = 256
    c = W / 2
    RR = 88

    def frame(f):
        p = f / 5
        cv = Canvas(W, W)
        O = cv.layer([A[1], A[2], A[4], A[6], A[8], X1])
        ro = 124 - (124 - RR - 6) * p
        O.ring(c, c, ro, 1.0, v=0.45 + 0.4 * p, dash=(28, 0.5, p * 0.25))
        # faint inner guide rings (area read)
        Gd = cv.layer([A[0], A[1], A[2]])
        for rr in (RR * 0.38, RR * 0.7):
            Gd.ring(c, c, rr, 0.55, v=0.5 + 0.4 * p, dash=(40, 0.3, 0.0))
        M = cv.layer(tel_ramp(f))
        M.ring(c, c, RR, 4.2, v=1.0)
        # ticks
        for k in range(8):
            a = k * TAU / 8
            ln = 9 if k % 2 == 0 else 5
            M.ray(c, c, a, RR - 5 - ln, RR - 5, 1.0, prof=tp_head(0.8), v=0.75)
        M.star4(c, c, 4 + 1.5 * f, 1.0, 0.8)
        if f == 5:
            Hc = cv.layer([A[9], X1, X0])
            Hc.ring(c, c, RR, 0.6, v=1.0, dash=(36, 0.62, 0.0))
        return cv.render()
    return frames_any(frame, 6)


# ======================================================================
# telegraph_line (16x16 tile -> 64x64 tile), 2f loop, flowing core
def telegraph_line():
    T = 64
    cy = 32

    def frame(f):
        cv = Canvas(T, T)
        M = cv.layer(R_TEL[:7])
        for ox in (-T, 0, T):
            M.stroke([(ox - 1, cy), (ox + T + 1, cy)], 6.4, v=0.55, step=0.5)
        Hc = cv.layer([A[6], A[8], A[10], X1])
        for ox in (-T, 0, T):
            s = ox + f * 32
            Hc.stroke([(s + 4, cy), (s + 30, cy)], 1.8, prof=tp_both(0.6, 0.7), v=1.0)
            Hc.stroke([(s + 38, cy), (s + 50, cy)], 0.9, prof=tp_both(0.6, 0.7), v=0.7)
        E = cv.layer([A[1], A[2], A[3]])
        for ox in (-T, 0, T):
            for side in (-1, 1):
                for k in range(4):
                    x0 = ox + k * 16 + f * 8
                    E.stroke([(x0, cy + side * 11.5), (x0 + 7, cy + side * 11.5)], 0.6,
                             prof=tp_both(0.6), v=0.9)
        img = cv.render()
        return img
    return frames_any(frame, 2)


# ======================================================================
# telegraph_cone (64 -> 256), 4 dirs, 6f progress — apex at pivot, r108, 32 deg
def telegraph_cone():
    W = 256
    c = W / 2
    RR, HA = 108, math.radians(32)
    out = {}
    for d in DIRS:
        base = DANG[d]
        frames = []
        for f in range(6):
            p = f / 5
            cv = Canvas(W, W)
            O = cv.layer([A[1], A[2], A[4], A[6], A[8], X1])
            ro = 140 - (140 - RR - 6) * p
            O.arc(c, c, ro, ro, base - HA, base + HA, 1.0, v=0.45 + 0.4 * p,
                  dash=(60, 0.5, p * 0.3))
            Gd = cv.layer([A[0], A[1], A[2]])
            for rr in (RR * 0.38, RR * 0.7):
                Gd.arc(c, c, rr, rr, base - HA, base + HA, 0.55, v=0.5 + 0.4 * p,
                       dash=(80, 0.3, 0.0))
            Gd.ray(c, c, base, 8, RR - 6, 0.55, v=0.5 + 0.4 * p, dash=(10, 0.4, 0))
            M = cv.layer(tel_ramp(f))
            v = 1.0
            for s in (-1, 1):
                M.ray(c, c, base + s * HA, 2, RR, 3.4, prof=tp_head(0.3), v=v)
            M.arc(c, c, RR, RR, base - HA, base + HA, 3.8, v=v)
            Hc = cv.layer([A[6], A[8], X1, X0])
            for s in (-1, 1):
                for k in range(2):
                    t = frac(p * 0.9 + k * 0.5)
                    r0 = 12 + (RR - 30) * t
                    Hc.ray(c, c, base + s * HA, r0, r0 + 16, 0.9,
                           prof=tp_both(0.6, 0.7), v=0.75 + 0.25 * p)
            if f == 5:
                Hc.arc(c, c, RR, RR, base - HA, base + HA, 0.6, v=1.0, dash=(60, 0.62, 0))
            M.star4(c, c, 3 + f, 1.0, 0.8)
            frames.append(cv.render())
        out[d] = frames
    return out


# ======================================================================
# telegraph_aura (64 -> 256), 4f seamless loop — streaks converging + core
def telegraph_aura():
    W = 256
    c = W / 2
    R = rng(91)
    streams = [(k * TAU / 12 + R.uniform(-0.1, 0.1), R.random()) for k in range(12)]

    def frame(f):
        cv = Canvas(W, W)
        S = cv.layer([A[1], A[2], A[4], A[6], A[8], A[10]])
        for a0, ph in streams:
            for j in range(2):
                t = frac(ph + j * 0.5 + f / 4)          # 0 outer -> 1 inner
                r = 120 - 82 * t
                ln = 22 - 10 * t
                a = a0 + (r - 30) * 0.004
                a2 = a0 + (r + ln - 30) * 0.004
                p0 = (c + math.cos(a) * r, c + math.sin(a) * r)
                p2 = (c + math.cos(a2) * (r + ln), c + math.sin(a2) * (r + ln))
                S.stroke([p0, p2], 1.3, prof=tp_tail(0.6), v=0.35 + 0.65 * t)
        K = cv.layer([A[1], A[3], A[5], A[7], A[9], X1, X0])
        pulse = 0.5 + 0.5 * math.cos(f / 4 * TAU)
        K.disc(c, c, 17 + 3 * pulse, v=0.8 + 0.2 * pulse, edge=0.3)
        K.ring(c, c, 28 + 3 * pulse, 1.1, v=0.6, dash=(14, 0.55, f / 16))
        return cv.render()
    return frames_any(frame, 4)


# ======================================================================
# enemy_bullet (8 -> 32), 1f, faces right, pivot = orb centre (20,16)
def enemy_bullet():
    cv = Canvas(32, 32)
    cx, cy = 20, 16
    T = cv.layer([A[1], A[2], A[4], A[6]])
    T.stroke([(cx - 3, cy), (1, cy)], 3.6, prof=tp_tail(0.8), v=0.8)
    for s in (-1, 1):
        T.stroke([(cx - 6, cy + s * 4.5), (3, cy + s * 2.5)], 0.6, prof=tp_tail(0.9), v=0.7)
    O = cv.layer([A[1], A[3], A[5], A[7], A[9], X1, X0])
    O.disc(cx, cy, 9, v=1.0, edge=0.08)
    O.disc(cx + 1.5, cy - 1.5, 3.2, v=1.0, edge=0.9)
    return {"any": [cv.render()]}


# ======================================================================
# boss_fan_shot (10 -> 40), 2f loop, pulsing core
def boss_fan_shot():
    def frame(f):
        cv = Canvas(40, 40)
        c = 20
        H = cv.layer([A[1], A[2], A[3]])
        H.ring(c, c, 14, 0.7, v=0.9, dash=(8, 0.4, f * 0.5 / 8 + 0.03))
        O = cv.layer([A[1], A[3], A[5], A[7], A[9], X1, X0])
        O.disc(c, c, 9, v=0.86 if f == 0 else 0.74, edge=0.1)
        O.disc(c, c, 3.4 if f == 0 else 2.4, v=1.0, edge=0.9)
        if f == 0:
            O.star4(c, c, 7, 0.7, 1.0, rot=TAU / 8)
        return cv.render()
    return frames_any(frame, 2)


# ======================================================================
# boss_slam (96 -> 384), 6f, judgement ring r156 (hitRadius 160 dots)
def boss_slam():
    W = 384
    c = W / 2
    R = rng(101)
    cracks = []
    for k in range(9):
        a = k * TAU / 9 + R.uniform(-0.2, 0.2)
        pts = [(c, c)]
        r, aa = 0.0, a
        ln = R.uniform(76, 104)
        n = 6
        for s in range(n):
            r += ln / n
            aa += R.uniform(-0.22, 0.22)
            pts.append((c + math.cos(aa) * r, c + math.sin(aa) * r * 0.92))
        twigs = []
        for s in (2, 4):
            if R.random() < 0.85:
                bx, by = pts[s]
                ta = aa + R.choice((-1, 1)) * R.uniform(0.5, 0.9)
                tl = R.uniform(12, 24)
                twigs.append((s, [(bx, by), (bx + math.cos(ta) * tl, by + math.sin(ta) * tl)]))
        cracks.append((pts, twigs))
    dust = [(k * TAU / 34 + R.uniform(-0.05, 0.05), R.uniform(0.94, 1.06), R.uniform(0.85, 1.3))
            for k in range(34)]

    def draw_cracks(L, upto, w, v):
        for pts, twigs in cracks:
            m = max(2, int(len(pts) * upto + 0.5))
            L.stroke(pts[:m], w, prof=tp_tail(0.55), v=v)
            for s, tw in twigs:
                if s < m - 1:
                    L.stroke(tw, w * 0.6, prof=tp_tail(0.7), v=v * 0.8)

    def dust_ring(L, r, rs, v, lift):
        for a, k, s in dust:
            x = c + math.cos(a) * r * k
            y = c + math.sin(a) * r * k * 0.92 - lift
            L.cloud(x, y, rs * s, v=v * 0.8, flat=0.6, seed=int(a * 100))

    def frame(f):
        cv = Canvas(W, W)
        D = cv.layer(R_DUSTSOFT)
        Cr = cv.layer([A[0], A[1], A[2], A[3], A[5], A[7], X1])
        M = cv.layer(R_HOT)
        if f == 0:
            M.disc(c, c, 34, v=1.0, edge=0.45)
            M.ring(c, c, 44, 1.6, v=0.75, dash=(18, 0.55, 0))
            for k in range(8):
                M.ray(c, c, k * TAU / 8 + 0.2, 38, 60, 1.6, prof=tp_both(0.6, 0.3), v=0.75)
        elif f == 1:
            Cr.disc(c, c, 13, v=0.55, edge=0.3)
            draw_cracks(Cr, 0.4, 2.8, 1.0)
            M.ring(c, c, 80, 3.0, v=1.0)
            M.disc(c, c, 6, v=1.0, edge=0.7)
        elif f == 2:
            Cr.disc(c, c, 14, v=0.5, edge=0.3)
            draw_cracks(Cr, 0.75, 2.8, 0.95)
            M.ring(c, c, 124, 2.6, v=0.95)
            dust_ring(D, 110, 6, 0.85, 2)
            sparks(M, c, c, 10, 60, 100, 9, 1.0, 0.8, seed=103)
        elif f == 3:
            Cr.disc(c, c, 14, v=0.45, edge=0.3)
            draw_cracks(Cr, 1.0, 2.6, 0.85)
            dust_ring(D, 150, 9, 0.9, 4)
            M.ring(c, c, 156, 2.4, v=0.95)
        elif f == 4:
            Cr.disc(c, c, 14, v=0.4, edge=0.3)
            draw_cracks(Cr, 1.0, 2.2, 0.65)
            dust_ring(D, 166, 11, 0.7, 8)
            M2 = cv.layer(R_HOT_DIM)
            M2.ring(c, c, 160, 1.4, v=0.95, dash=(40, 0.55, 0.1))
        else:
            Cr.disc(c, c, 13, v=0.32, edge=0.3)
            draw_cracks(Cr, 1.0, 1.8, 0.42)
            for a, k, s in dust:
                x = c + math.cos(a) * 176 * k
                y = c + math.sin(a) * 176 * k * 0.92 - 12
                D.arc(x, y, 10 * s, 8 * s, math.pi * 1.05, math.pi * 1.95, 0.8,
                      prof=tp_both(0.5), v=0.55)
            E = cv.layer(R_EMBER)
            sparks(E, c, c, 10, 120, 170, 3, 0.7, 0.6, seed=105)
        return cv.render()
    return frames_any(frame, 6)


# ======================================================================
# soul_wisp (16x24 -> 64x96), 8f loop, pivot (32,92) = ground under the wisp
def soul_wisp():
    W, H = 64, 96

    def frame(f):
        ph = f / 8 * TAU
        cv = Canvas(W, H)
        bob = 3.5 * math.sin(ph)
        hx, hy = 32, 44 + bob
        Gd = cv.layer([A[1], A[2]])
        Gd.ring(32, 91, 7 - 0.8 * math.sin(ph), 0.5, ry=2.0, v=0.9, dash=(10, 0.55, f / 40))
        T = cv.layer([GRAY[6], GRAY[9], GRAY[11]])
        # two tails hanging and swaying below the head
        for s, amp, ln in ((-1, 4.0, 30), (1, 3.0, 22)):
            sw = amp * math.sin(ph + s * 1.1)
            T.curve((hx + s * 2, hy + 6), (hx + s * 5 + sw, hy + 6 + ln * 0.55),
                    (hx + s * 2 - sw * 0.6, hy + 6 + ln), 2.2, prof=tp_tail(0.8),
                    vprof=lambda t: 1 - 0.7 * t)
        B = cv.layer(R_PALE)
        sway = 2.6 * math.sin(ph + 0.8)
        tip = 14 + 2.5 * math.sin(ph * 2)
        body = qbez((hx, hy + 8), (hx - sway * 0.4, hy - 4), (hx + sway, hy - tip))
        B.stroke(body, 8.4, prof=lambda t: (min(1, t / 0.2) ** 0.45) * (1 - t) ** 0.6,
                 vprof=lambda t: 0.75 + 0.25 * (1 - abs(t - 0.35)))
        Hh = cv.layer([A[5], A[7], A[9]])
        fl = 0.7 + 0.3 * ((f * 3) % 4) / 3
        Hh.disc(hx - sway * 0.1, hy + 2, 2.6 * fl, 3.2 * fl, v=fl, edge=0.5)
        # a spark peeling off the tip, rising
        t = frac(f / 8)
        Hh.stroke([(hx + sway + 3 + 2 * t, hy - tip - 4 - 14 * t),
                   (hx + sway + 3 + 2 * t, hy - tip - 2 - 14 * t)], 0.7,
                  prof=tp_both(0.5), v=0.9 - 0.5 * t)
        return cv.render()
    return frames_any(frame, 8)


# ======================================================================
# birth_dust (64x32 -> 256x128), 9f: swirl loop 0-3 (3-fold, 30 deg/f), scatter 4-8
def birth_dust():
    W, H = 256, 128
    cx, cy = 128, 88
    YS = 0.36
    R = rng(111)
    grains = [(R.uniform(0, 1), R.uniform(0.85, 1.15), R.random()) for _ in range(30)]

    def spiral(arm, t, rot):
        a = rot + arm * TAU / 3 + t * 2.4
        r = 112 - 52 * t
        return cx + math.cos(a) * r, cy + math.sin(a) * r * YS

    def frame(f):
        cv = Canvas(W, H)
        D = cv.layer(R_DUST)
        G = cv.layer(R_FLAKE + [GRAY[9]])
        E = cv.layer(R_EMBER)
        if f < 4:
            rot = f * math.radians(30)
            for arm in range(3):
                pts = [spiral(arm, i / 40, rot) for i in range(41)]
                D.stroke(pts, 1.4, prof=tp_both(0.5, 0.55), v=0.7, dash=(14, 0.7, 0.2))
                for t0, k, sz in grains:
                    t = frac(t0 + f / 4 * 0)          # fixed along arm, arm rotates
                    x, y = spiral(arm, t, rot)
                    G.stroke([(x - 1.5, y), (x + 1.5, y - 0.4)], 0.5 + 0.7 * sz,
                             prof=tp_both(0.5), v=0.5 + 0.5 * sz, soft=0.5)
                ex, ey = spiral(arm, 0.3, rot)
                E.stamp(ex, ey - 2, 1.0, 0.95)
            D.ring(cx, cy, 52, 0.7, ry=52 * YS, v=0.5, dash=(18, 0.35, f / 12))
        else:
            k = f - 4                                   # 0..4
            Ds = cv.layer(R_DUSTSOFT)
            cv.layers.insert(0, cv.layers.pop())        # soft dust lowest
            t = (k + 1) / 5
            r = 100 + 26 * t
            for i, (t0, kk, sz) in enumerate(grains):
                a = t0 * TAU
                rr = r * kk * (0.9 if i % 2 else 1.0)
                x = cx + math.cos(a) * rr
                y = cy + math.sin(a) * rr * YS - 10 * math.sin(math.pi * min(1, t * 1.4))
                if R.random() < 0.15 * k:
                    continue
                G.stroke([(x - math.cos(a) * 3 * (1 - t), y - math.sin(a) * 1.2),
                          (x, y)], 0.5 + 0.7 * sz, prof=tp_head(0.6), v=(0.95 - 0.15 * k),
                         soft=0.5)
            n = 9
            for j in range(n):
                a = j * TAU / n + 0.2
                pr = 66 + 30 * t
                x, y = cx + math.cos(a) * pr, cy + math.sin(a) * pr * YS - 4 * t
                rs = 11 + 7 * t
                if k <= 2:
                    Ds.cloud(x, y, rs, v=0.7 - 0.12 * k, flat=0.45, seed=j)
                else:
                    D.arc(x, y, rs, rs * 0.7, math.pi * 1.05, math.pi * 1.95, 0.8,
                          prof=tp_both(0.5), v=0.6 - 0.1 * (k - 3))
            if k <= 3:
                sparks(E, cx, cy - 20 - 14 * t, 6, 10 + 30 * t, 18 + 34 * t, 4, 0.7,
                       0.9 - 0.15 * k, seed=113, ang0=-math.pi / 2, spread=2.4)
        return cv.render()
    return frames_any(frame, 9)


# ======================================================================
# fire_pool (48x24 -> 192x96), 4f seamless loop, pivot (96,72)
def fire_pool():
    W, H = 192, 96
    cx, cy = 96, 72
    rx, ry = 88, 19
    R = rng(121)
    tongues = []
    for k in range(15):
        x = cx - rx * 0.86 + k * (rx * 1.72) / 14 + R.uniform(-3, 3)
        q = (x - cx) / rx
        yb = cy + ry * R.uniform(-0.1, 0.45) * math.sqrt(max(0, 1 - q * q))
        hmax = (22 + 34 * (1 - q * q)) * R.uniform(0.55, 1.05)
        tongues.append((x, yb, hmax, R.random(), R.uniform(6.0, 8.5)))
    small = []
    for k in range(14):
        x = cx + R.uniform(-0.9, 0.9) * rx
        q = (x - cx) / rx
        yb = cy + R.uniform(-0.5, 0.6) * ry * math.sqrt(max(0, 1 - q * q))
        small.append((x, yb, R.uniform(10, 20), R.random(), R.uniform(2.2, 3.2)))
    embers = [(cx + R.uniform(-0.8, 0.8) * rx, R.random(), R.uniform(30, 60)) for _ in range(7)]

    def tongue(L, x, yb, h, ph, w, f, v=1.0, inner=False):
        s = math.sin(TAU * (f / 4 + ph))
        hh = h * (0.78 + 0.22 * s)
        sw = (4 + 4 * ph) * math.sin(TAU * (f / 4 + ph + 0.25)) + (ph - 0.5) * 8
        pts = qbez((x, yb), (x - sw * 0.5, yb - hh * 0.55), (x + sw, yb - hh))
        # rounded base, pointed curling tip
        L.stroke(pts, w, prof=lambda t: (min(1, t / 0.12) ** 0.5) * (1 - t) ** 0.85,
                 vprof=lambda t: (1 - 0.55 * t) if not inner else 1.0, v=v)

    def frame(f):
        cv = Canvas(W, H)
        P = cv.layer([A[0], A[1], A[2], A[3], A[4]])
        P.disc(cx, cy, rx, ry, v=0.85, edge=0.15)
        Bd = cv.layer(R_FIRE)
        # continuous fire bed along the pool (tongues rise from it)
        Bd.arc(cx, cy - 2, rx * 0.86, ry * 0.42, math.pi * 0.98, math.pi * 2.02, 5.5,
               prof=tp_both(0.35), v=0.62)
        Bd.arc(cx, cy + 1, rx * 0.8, ry * 0.4, math.pi * 0.02, math.pi * 0.98, 4.0,
               prof=tp_both(0.35), v=0.55)
        # liquid glow bands (periodic)
        for j in range(3):
            yy = cy - ry * 0.45 + j * ry * 0.45
            span = rx * math.sqrt(max(0, 1 - ((yy - cy) / ry) ** 2)) * 0.85
            P.stroke([(cx - span, yy), (cx + span, yy)], 0.8,
                     prof=tp_both(0.6), v=0.95, dash=(26, 0.55, f / 4 + j * 0.33))
        Fo = cv.layer(R_FIRE)
        for x, yb, h, ph, w in small:
            tongue(Fo, x, yb, h, ph, w, f, v=0.75)
        for x, yb, h, ph, w in sorted(tongues, key=lambda t: t[1]):
            tongue(Fo, x, yb, h, ph, w, f, v=0.85)
        Fi = cv.layer([A[7], A[9], X1])
        for x, yb, h, ph, w in tongues:
            tongue(Fi, x, yb + 1, h * 0.5, ph, w * 0.45, f, v=1.0, inner=True)
        E = cv.layer(R_EMBER + [A[9]])
        for ex, ph, hmax in embers:
            t = frac(ph + f / 4)
            y = cy - 12 - hmax * t
            x = ex + 3 * math.sin(TAU * t + ph * 6)
            if y > 1:
                E.stroke([(x, y + 2.5), (x, y)], 0.7, prof=tp_head(0.6), v=1.0 - 0.6 * t)
        return cv.render()
    return frames_any(frame, 4)


# ======================================================================
# parry_flash (48 -> 192), 5f
def parry_flash():
    W = 192
    c = W / 2

    def glints(L, r, size, v):
        for k in range(4):
            a = TAU / 8 + k * TAU / 4
            L.star4(c + math.cos(a) * r, c + math.sin(a) * r, size, 0.9, v)

    def frame(f):
        cv = Canvas(W, W)
        if f == 0:
            G = cv.layer(R_HOT_DIM)
            G.ring(c, c, 14, 1.0, v=0.85)
            L = cv.layer(R_HOT)
            for k in range(4):
                L.ray(c, c, k * TAU / 4, 0, 88, 2.2, prof=tp_tail(0.85))
            for k in range(4):
                L.ray(c, c, TAU / 8 + k * TAU / 4, 0, 20, 1.2, prof=tp_tail(0.9), v=0.85)
            L.disc(c, c, 8, v=1.0, edge=0.6)
        elif f == 1:
            L = cv.layer(R_HOT)
            L.ring(c, c, 24, 1.6, v=0.9)
            L.ring(c, c, 40, 1.4, v=0.75)
            for k in range(8):
                L.ray(c, c, k * TAU / 8, 46, 62, 1.1, prof=tp_both(0.6, 0.4), v=0.95)
            L.star4(c, c, 8, 1.0, 1.0)
        elif f == 2:
            L = cv.layer(R_HOT)
            L.ring(c, c, 34, 1.4, v=0.8)
            L.ring(c, c, 52, 1.2, v=0.65)
            glints(L, 64, 8, 0.95)
            L.star4(c, c, 5, 0.9, 0.8)
        elif f == 3:
            L = cv.layer(R_HOT_DIM)
            L.ring(c, c, 44, 1.2, v=0.85, dash=(16, 0.6, 0.0))
            L.ring(c, c, 62, 1.0, v=0.7, dash=(20, 0.5, 0.25))
            G = cv.layer(R_HOT)
            glints(G, 68, 5, 0.6)
        else:
            L = cv.layer(R_EMBER)
            L.ring(c, c, 54, 0.9, v=0.6, dash=(16, 0.25, 0.1))
            L.ring(c, c, 72, 0.8, v=0.5, dash=(20, 0.2, 0.35))
            sparks(L, c, c, 8, 60, 76, 3, 0.7, 0.6, seed=131)
        return cv.render()
    return frames_any(frame, 5)
