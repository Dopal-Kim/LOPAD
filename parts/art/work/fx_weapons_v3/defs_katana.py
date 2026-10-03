"""칼 B '재 칼날' 이펙트 v3 — 연격·기본 베기·거합·발도·만월·잔월·급소·허보."""
import math

import common as C
import parts as P
import swing
import wkit as W
from wkit import FK

FACE = {"right": (1, 0), "left": (-1, 0), "down": (0, 1), "up": (0, -1)}


def overlay(base, top):
    for d in base:
        for i, im in enumerate(base[d]):
            im2 = top[d][i].copy()
            im2.alpha_composite(im)              # base 를 위에(궤적이 앞)
            base[d][i] = im2
    return base


def katana_combo1():
    return C.combo("katana_combo1", "katana", 11, seed=11)


def katana_combo2():
    return C.combo("katana_combo2", "katana", 9, seed=12)


def katana_combo3():
    return C.combo("katana_combo3", "katana", 14, seed=13, echoes=[(-12, 1, 0.6), (-22, 2, 0.45)], rays=3)


def katana_slash():
    return C.slash("katana_slash", "katana", 17, -85, 75, 9, seed=14, rays=2)


def iai():
    return C.slash("iai", "katana", 26, -105, 105, 14, seed=15, echoes=[(7, 1, 0.7), (-10, 2, 0.6)], rays=3)


def wide():
    old = W.old_json("wide")
    fr, ex = C.slash("wide", "katana", 40, -105, 105, 16, seed=16, echoes=[(8, 1, 0.7), (-12, 2, 0.6)], rays=3)
    prog = [0.25, 0.55, 0.8, 1.0, 1.0, 1.0, 1.0]

    def draw(f, t, d, i, F):
        L = f.L(W.R_EDGE)
        Lg = f.L(W.R_HOT)
        c = (t.ox, t.oy - W.HIT_UP)
        r = 84
        a0 = t.ang(math.radians(-90))
        span = 2 * math.pi * prog[i]
        if i < 3:
            L.arc(c[0], c[1], r, r, a0, a0 + span, 1.0, prof=FK.tp_both(0.6, 0.85), v=0.45 + 0.12 * i)
        elif i == 3:
            L.ring(c[0], c[1], r, 1.3, v=0.95, dash=(28, 0.7, 0.0))
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2
                P.glint(Lg, c[0] + math.cos(a) * r, c[1] + math.sin(a) * r, 9, v=0.85)
        else:
            L.ring(c[0], c[1], r, 1.0 if i < 6 else 0.8, v=[0.7, 0.55, 0.42][i - 4], dash=(28 - 4 * (i - 4), 0.6 - 0.12 * (i - 4), 0.1 * i))
    moon = C.frames(old, draw)
    ex["moon"] = {"radiusDots": 84, "closedFrame": 3, "note": "안쪽 달무리 r84 가 f3 에서 닫힌 보름달(점선 백열 + 네 귀 글린트)"}
    return overlay(fr, moon), ex


def batto():
    old = W.old_json("batto")
    fw, fh, px, py = W.geom(old)
    arc = swing.swing_frames("katana", (fw, fh), (px - 8, py - W.HIT_UP), 92, -70, 70, old["frames"], 1, bright={1, 2},
                             wmax=11, seed=17, echoes=[(-10, 1, 0.6)])

    def draw(f, t, d, i, F):
        Ls = f.L(W.R_ASHG)
        Lc = f.L(W.R_EDGE)
        k = [0.35, 1.0, 1.0, 0.8, 0.6, 0.4, 0.25][i]
        heat = [0.6, 1.0, 0.85, 0.7, 0.55, 0.45, 0.4][i]
        for j, y in enumerate((-18, 0, 16)):
            x0 = -34 - j * 6 + i * 3
            ln = (70 + 18 * (1 - abs(j - 1))) * k
            p0, p1 = (x0 - ln, y), (x0, y)
            dash = None if i < 4 else (14 - i, 0.55, 0.3 * j)
            Ls.stroke(t.pts([p0, p1]), 2.6 * (0.6 + 0.4 * k), prof=FK.tp_head(0.6), v=0.8, dash=dash)
            if i < 5:
                q0 = (x0 - ln * 0.55, y)
                Lc.stroke(t.pts([q0, p1]), 0.8, prof=FK.tp_head(0.7), v=heat if i in (1, 2) else min(heat, 0.8), dash=dash)
    lines = C.frames(old, draw, origin=(px, py - W.HIT_UP))
    ex = C.base_extra(old, "katana", {1, 2})
    return overlay(arc, lines), ex


def zangetsu():
    old = W.old_json("zangetsu")
    fw, fh, px, py = W.geom(old)
    a0, a1 = math.radians(-105), math.radians(100)

    def draw(f, t, d, i, F):
        Lb = f.L(W.R_ASHG)
        Lc = f.L(W.R_EDGE)
        Lg = f.L(W.R_HOT)
        for j, r in enumerate((104, 92, 80)):
            Lb.stroke(t.pts(W.arc_pts(r, a0, a1)), 3.2 - 0.6 * j, prof=FK.tp_both(0.6, 0.55), v=0.55 + 0.1 * (2 - j))
        # 띠 사이 혼불 금(번개 토막) — 프레임마다 자리 이동
        rng = P.rng(40 + i)
        for j, r in enumerate((98, 86)):
            for k in range(3):
                s = FK.frac(0.15 + 0.3 * k + 0.08 * i + 0.11 * j)
                a = a0 + (a1 - a0) * s
                pts = [(math.cos(a + u * 0.06) * (r + rng.uniform(-2, 2)), math.sin(a + u * 0.06) * (r + rng.uniform(-2, 2)))
                       for u in range(4)]
                Lc.stroke(t.pts(pts), 0.8, prof=FK.tp_both(0.7, 0.5), v=0.72)
        a = a0 + (a1 - a0) * FK.frac(0.1 + 0.25 * i)
        g = t((math.cos(a) * 104, math.sin(a) * 104))
        P.glint(Lg, g[0], g[1], 8, v=0.9)
        if i == 0:
            Lc.stroke(t.pts(W.arc_pts(116, a0, a1)), 1.0, v=0.7, dash=(26, 0.5, 0.0))
    fr = C.frames(old, draw, origin=(px, py - W.HIT_UP))
    return fr, C.base_extra(old, "katana", {0})


def dashcrit():
    old = W.old_json("dashcrit")

    def draw(f, t, d, i, F):
        Lf = f.L(W.R_ASHG)
        L = f.L(W.R_EDGE)
        Lc = f.L(W.R_HOT)
        c = (t.ox, t.oy)
        rng = P.rng(50 + i)
        if i == 0:
            Lc.disc(c[0], c[1], 7, v=1.0, edge=0.6)
            L.ring(c[0], c[1], 12, 1.4, v=0.8)
        elif i == 1:
            P.rays(L, c, 8, 6, 60, 2.6, v=0.85, rot=0.2, jitter=0.12, rng=rng)
            P.rays(Lc, c, 8, 4, 50, 1.0, v=1.0, rot=0.2)
            Lc.disc(c[0], c[1], 5, v=1.0, edge=0.7)
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2
                P.glint(Lc, c[0] + math.cos(a) * 44, c[1] + math.sin(a) * 44, 6, v=0.7)
        elif i == 2:
            L.ring(c[0], c[1], 34, 1.6, v=0.95)
            P.rays(L, c, 8, 40, 62, 1.4, v=0.75, rot=0.2, prof=FK.tp_both(0.7, 0.3))
            Lc.disc(c[0], c[1], 3, v=0.9)
        elif i == 3:
            L.ring(c[0], c[1], 56, 1.3, v=0.72, dash=(10, 0.7, 0.0))
            for k in range(4):
                a = k * math.pi / 2
                P.glint(L, c[0] + math.cos(a) * 56, c[1] + math.sin(a) * 56, 7, v=0.78)
            P.scatter_flakes(Lf, c, rng, 10, 30, 60)
        else:
            L.ring(c[0], c[1], 80, 1.0, v=0.45, dash=(12, 0.4, 0.2))
            P.scatter_flakes(Lf, c, rng, 14, 40, 84, v=(0.3, 0.8))
            P.scatter_embers(f.L(W.R_EMBER), c, rng, 5, 50, 80, v=(0.5, 0.8))
    fr = C.frames(old, draw)
    return fr, C.base_extra(old, "katana", {0, 1})


def _behind(d):
    fx, fy = FACE[d]
    return (-fx, -fy)


def longinvuln():
    old = W.old_json("longinvuln")
    fw, fh, px, py = W.geom(old)

    def draw(f, t, d, i, F):
        Lh = f.L(W.R_ASHG)
        Ls = f.L(W.R_ASHG)
        L = f.L(W.R_EDGE)
        Lf = f.L(W.R_HOT)
        mask, (mw, mh), (mpx, mpy) = P.silhouette_mask("player_dash", d, 1)
        bx, by = _behind(d)
        ox, oy = px - mpx + bx * 4 * i, py - mpy + by * 4 * i
        # 성긴 재 빗금 속
        for (x, y) in mask:
            if (x + y + i) % 7 == 0 and i < 4:
                Lh.put(ox + x, oy + y, 0.55)
        v = [0.82, 0.74, 0.62, 0.5, 0.4][i]
        dash = None if i < 3 else (6, 0.6 - 0.15 * (i - 3), 0.0)
        fxv = FACE[d]
        P.outline_mask(L, mask, ox, oy, v=v, dash=dash, front=fxv, Lfront=Lf if i < 2 else L, fv=1.0 if i == 0 else 0.9)
        # 몸 뒤 속도선 3
        if i < 4:
            cx, cy = px, py - 70
            for j in (-1, 0, 1):
                sx = cx + bx * (40 + 6 * abs(j)) + (by != 0) * j * 18
                sy = cy + by * (34 + 6 * abs(j)) + (bx != 0) * j * 22
                ln = (46 if bx else 30) * (1 - 0.2 * i)
                Ls.stroke([(sx, sy), (sx + bx * ln, sy + by * ln)], 1.6, prof=FK.tp_tail(0.7), v=0.8,
                          dash=None if i < 2 else (10, 0.6, 0.2))
    fr = C.frames(old, draw)
    ex = C.base_extra(old, "katana", {0})
    ex["heroSource"] = "player/v3/player_dash 열 1(방향 행별) 실루엣 — 주인공 대쉬가 바뀌면 재빌드"
    return fr, ex


SHEETS = {
    "katana_combo1": katana_combo1, "katana_combo2": katana_combo2, "katana_combo3": katana_combo3,
    "katana_slash": katana_slash, "iai": iai, "wide": wide, "batto": batto, "zangetsu": zangetsu,
    "dashcrit": dashcrit, "longinvuln": longinvuln,
}
