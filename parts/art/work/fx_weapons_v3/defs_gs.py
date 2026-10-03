"""대검 A '녹슨 양손검' 이펙트 v3 — 연격·기본 베기·내리찍기·파쇄·중압·지진·분쇄·거인·가드 파동·철벽.

언어: 녹·흙 넓은 띠 + 이 빠진 홈 혼불 한 줄 / 땅에 닿으면 혼불이 스민 균열(호박) + 흙먼지 + 불씨 + 재.
"""
import math

import common as C
import parts as P
import wkit as W
from wkit import FK

FACE_ANG = {"right": 0.0, "left": math.pi, "down": math.pi / 2, "up": -math.pi / 2}


def greatsword_combo1():
    return C.combo("greatsword_combo1", "gs", 30, seed=21, dust=5)


def greatsword_combo2():
    return C.combo("greatsword_combo2", "gs", 27, seed=22, dust=5)


def greatsword_combo3():
    return C.combo("greatsword_combo3", "gs", 36, seed=23, dust=7, echoes=[(-18, 1, 0.5)], rays=3, cracks=True)


def greatsword_slash():
    return C.slash("greatsword_slash", "gs", 20, -95, 85, 20, seed=24, dust=3)


def _layers(f):
    return dict(dust=f.L(W.R_DUST), ash=f.L(W.R_ASHB), crack_d=f.L(W.R_EDGE_SOFT), crack=f.L(W.R_EDGE),
                hot=f.L(W.R_HOT), ember=f.L(W.R_EMBER))


def _impact_star(L, c, size, v=1.0):
    P.glint(L, c[0], c[1], size, v=v, diag=0.45, w=1.4)
    L.disc(c[0], c[1], size * 0.18, v=v, edge=0.7)


def _shock(f, c, r, ky, k, rng, cracks, bias=None, dust_n=6, rcrack=None, base_v=1.0):
    """바닥 충격: 납작한 고리 + 혼불 균열 + 흙먼지 띠. k = 식음(0 뜨거움 → 1 식음)."""
    Ls = _layers(f)
    v = base_v * (1 - 0.55 * k)
    dash = (5, 0.86, rng.random()) if k < 0.5 else (12 + 6 * k, 0.7 - 0.35 * k, 0.1)   # 뜨거울 때도 몇 군데 끊긴 고리
    P.ground_ring(Ls["crack"] if k < 0.6 else Ls["crack_d"], c, r, 2.4 * (1 - 0.5 * k), v=v * (0.7 if k > 0 else 1.0), ky=ky,
                  dash=dash, prof=lambda s: 0.55 + 0.45 * W.h2(int(s * 23), 3, 5))
    # 고리 둘레 흙먼지(크기·자리 제각각, 이어진 낮은 띠)
    for j in range(dust_n * 2):
        a = 2 * math.pi * j / (dust_n * 2) + rng.uniform(-0.25, 0.25)
        rr = r * rng.uniform(0.86, 1.02)
        W.puff(Ls["dust"], c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr * ky - 2 - rng.uniform(0, 3),
               min(12.0, r * 0.06 * rng.uniform(0.6, 1.4) * (1 + 0.5 * k)), v=0.8 - 0.3 * k, flat=0.5, seed=j)
    if cracks:
        P.radial_cracks(Ls["crack"] if k < 0.5 else Ls["crack_d"], c, rng, cracks, r * 0.12, rcrack or r * 0.95,
                        v=v * 0.95, w=1.2 - 0.4 * k, ky=ky, bias=bias, bias_k=0.3, dash=None if k < 0.7 else (8, 0.6, 0.0))
    return Ls


def greatsword_slam():
    old = W.old_json("greatsword_slam")
    rs = [0, 44, 92, 124, 144, 152]

    def draw(f, t, d, i, F):
        c = (t.ox, t.oy)
        rng = P.rng(60)                         # 같은 균열 모양을 프레임마다 유지(커짐)
        bias = FACE_ANG[d]
        if i == 0:
            Ls = _layers(f)
            _impact_star(Ls["hot"], c, 26)
            Ls["crack"].stroke([(c[0], c[1] - 40), (c[0], c[1])], 2.0, prof=FK.tp_head(0.6), v=0.9)
            P.scatter_embers(Ls["ember"], c, P.rng(61), 6, 6, 20, up=0.6)
            return
        k = (i - 1) / 4
        Ls = _shock(f, c, rs[i], P.KY, k, rng, 9, bias=bias, dust_n=10, rcrack=rs[min(i + 1, 5)] * 0.9)
        if i == 1:
            _impact_star(Ls["hot"], c, 14, v=0.9)
        P.scatter_embers(Ls["ember"], c, P.rng(62 + i), 10 - i, rs[i] * 0.4, rs[i] * 1.05, ky=P.KY, up=0.8,
                         v=(0.5, 0.9 - 0.08 * i))
        if i >= 3:
            P.scatter_flakes(Ls["ash"], c, P.rng(70 + i), 12, rs[i] * 0.3, rs[i], ky=P.KY, fall=2 * i)
    fr = C.frames(old, draw)
    return fr, C.base_extra(old, "greatsword", {0, 1})


def _bolt_hit(name, seed, stages, ring_seq, crack_n, dust_n=8, pivot_y_ground=True):
    """혼불 낙뢰가 꽂히는 적중형(파쇄·지진). stages = {프레임: ('bolt', 굵기) | ('pre',) | ('ring', 반지름, 식음)}."""
    old = W.old_json(name)

    def draw(f, t, d, i, F):
        c = (t.ox, t.oy)
        st = stages[i]
        Ls = _layers(f)
        rng = P.rng(seed)
        if st[0] == "pre":
            pts = W.jag(P.rng(seed + 5), (c[0] + 6, c[1] - st[1]), (c[0], c[1] - 6), n=8, amp=3)
            Ls["crack"].stroke(pts, 1.0, prof=FK.tp_both(0.7, 0.6), v=0.62)
        elif st[0] == "bolt":
            P.bolt(Ls["hot"], Ls["crack"], (c[0] + 8, c[1] - st[1]), c, P.rng(seed + 9 + i), w=st[2], branches=2, v=1.0)
            _impact_star(Ls["hot"], c, 22)
            P.scatter_embers(Ls["ember"], c, P.rng(seed + i), 6, 6, 24, up=0.8)
        else:
            _, r, k = st[:3]
            Ls2 = _shock(f, c, r, P.KY, k, rng, crack_n, dust_n=dust_n)
            if len(st) > 3:
                P.bolt(Ls2["hot"], Ls2["crack"], (c[0] - 10, c[1] - st[3]), c, P.rng(seed + 33), w=st[4], branches=3, v=1.0)
                _impact_star(Ls2["hot"], c, 30)
            elif k < 0.2:
                _impact_star(Ls2["hot"], c, 12, v=0.85)
            P.scatter_embers(Ls2["ember"], c, P.rng(seed + 50 + i), 8, r * 0.3, r, ky=P.KY, up=0.8, v=(0.45, 0.85))
            if k > 0.45:
                P.scatter_flakes(Ls2["ash"], c, P.rng(seed + 70 + i), 10, r * 0.2, r, ky=P.KY, fall=3)
    return C.frames(old, draw), C.base_extra(old, "greatsword", {1})


def crush():
    st = {0: ("pre", 130), 1: ("bolt", 140, 2.6), 2: ("ring", 32, 0.0), 3: ("ring", 60, 0.3), 4: ("ring", 84, 0.6), 5: ("ring", 96, 1.0)}
    return _bolt_hit("crush", 80, st, None, 7)


def quake():
    st = {0: ("pre", 200), 1: ("bolt", 210, 2.6), 2: ("ring", 40, 0.1), 3: ("ring", 80, 0.5),
          4: ("ring", 112, 0.0, 200, 3.4), 5: ("ring", 140, 0.45), 6: ("ring", 156, 1.0)}
    return _bolt_hit("quake", 90, st, None, 10, dust_n=12)


def weight():
    old = W.old_json("weight")
    rs = [0, 26, 46, 64, 74, 80]

    def draw(f, t, d, i, F):
        c = (t.ox, t.oy)
        Ls = _layers(f)
        if i == 0:
            _impact_star(Ls["hot"], c, 24)
            for s in (-1, 1):
                W.puff(Ls["dust"], c[0] + s * 18, c[1] - 2, 9, v=0.8, flat=0.6, seed=s + 3)
            return
        k = (i - 1) / 4
        Ls = _shock(f, c, rs[i], 0.5, k, P.rng(81), 6, dust_n=4)
        for s in (-1, 1):                        # 양옆으로 밀려나는 흙먼지
            for j in range(3):
                W.puff(Ls["dust"], c[0] + s * (rs[i] * 0.85 + 11 * j), c[1] - 4 - 3 * j, 9 + 2 * j - 2 * k * j,
                       v=0.85 - 0.35 * k, flat=0.6, seed=j * 7 + i)
        if i == 1:
            _impact_star(Ls["hot"], c, 12, v=0.85)
        P.scatter_embers(Ls["ember"], c, P.rng(82 + i), 7, 10, rs[i], ky=0.5, up=0.9, v=(0.45, 0.85))
    return C.frames(old, draw), C.base_extra(old, "greatsword", {0, 1})


def pulverize():
    old = W.old_json("pulverize")

    def draw(f, t, d, i, F):
        c = (t.ox, t.oy)
        Ls = _layers(f)
        rng = P.rng(90)
        if i == 0:
            Ls["hot"].disc(c[0], c[1], 9, v=1.0, edge=0.65)
            Ls["crack"].ring(c[0], c[1], 14, 1.6, v=0.85)
            return
        r = [0, 30, 54, 74, 84][i]
        k = (i - 1) / 3
        Ls["crack" if k < 0.5 else "crack_d"].ring(c[0], c[1], r, 2.2 * (1 - 0.5 * k), v=1 - 0.5 * k,
                                                   dash=None if i < 3 else (14, 0.6, 0.0))
        # 녹슨 쐐기 파편 8 — 바깥으로 튐
        for j in range(8):
            a = j * math.pi / 4 + 0.2 + rng.uniform(-0.1, 0.1)
            rr = r * (1.04 + 0.16 * k) + 5
            x, y = c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr + 4 * k * k * 10
            W.flake(Ls["ash"], x, y, 4.5 - 1.5 * k, a, v=0.95 - 0.3 * k)
            if i < 3:
                W.ember(Ls["ember"], x, y, math.cos(a), math.sin(a), 8, v=0.9)
        if i == 1:                               # X 표(투사체 소멸)
            for a in (math.pi / 4, 3 * math.pi / 4):
                p0 = (c[0] - math.cos(a) * 26, c[1] - math.sin(a) * 26)
                p1 = (c[0] + math.cos(a) * 26, c[1] + math.sin(a) * 26)
                Ls["hot"].stroke([p0, p1], 1.6, prof=FK.tp_both(0.7, 0.5), v=1.0)
        if i >= 3:
            P.scatter_flakes(Ls["ash"], c, P.rng(91 + i), 10, r * 0.3, r)
    return C.frames(old, draw), C.base_extra(old, "greatsword", {0, 1})


def giant():
    old = W.old_json("giant")

    def draw(f, t, d, i, F):
        c = (t.ox, t.oy)                       # 발밑
        Ls = _layers(f)
        rx, ry = 100, 30
        Ls["crack_d"].arc(c[0], c[1], rx - 10, ry - 4, 0, 2 * math.pi, 1.0, v=0.7, dash=(22, 0.5, 0.25 * i))
        Ls["dust"].arc(c[0], c[1], rx, ry, 0, 2 * math.pi, 2.2, v=0.6)
        for j in range(4):                       # 도는 혼불 토막(4프레임 = 1/4 바퀴씩 → 이음새 없음)
            a0 = j * math.pi / 2 + i * math.pi / 8
            Ls["crack"].arc(c[0], c[1], rx, ry, a0, a0 + 0.55, 1.6, prof=FK.tp_both(0.7, 0.6), v=0.95)
        a = i * math.pi / 8 + math.pi / 4
        P.glint(Ls["hot"], c[0] + math.cos(a) * rx, c[1] + math.sin(a) * ry, 7, v=0.85)
        # 양옆 솟는 불씨 기둥(4프레임 주기, 48 도트 위로)
        for s in (-1, 1):
            x = c[0] + s * (rx - 6)
            for k in range(4):
                ph = FK.frac((k + i / 4.0) / 4.0)
                y = c[1] - 6 - ph * 120
                ln = 14 * (1 - ph) + 4
                Ls["crack" if ph < 0.6 else "crack_d"].stroke([(x + s * 2 * math.sin(ph * 6), y + ln), (x, y)], 1.4,
                                                                 prof=FK.tp_head(0.6), v=0.95 - 0.5 * ph)
            W.ember(Ls["ember"], x + s * 8, c[1] - 30 - 30 * FK.frac(i / 4 + 0.5), 0, -1, 5, v=0.8)
    return C.frames(old, draw), C.base_extra(old, "greatsword", set())


def guard_wave():
    old = W.old_json("guard_wave")
    rs = [40, 72, 98, 112]

    def draw(f, t, d, i, F):
        Ls = _layers(f)
        c = (t.ox, t.oy)
        r = rs[i]
        k = i / 3
        fa = FACE_ANG[d]
        ky = 0.5                                  # 바닥에 놓인 반타원(세로 0.5) — 정면 쪽 반

        def pts(rr, n=60, lo=-1.35, hi=1.35):
            return [(c[0] + math.cos(fa + lo + (hi - lo) * u / n) * rr, c[1] + math.sin(fa + lo + (hi - lo) * u / n) * rr * ky)
                    for u in range(n + 1)]
        Ls["ash"].stroke(pts(r - 5), 4.0 * (1 - 0.4 * k), prof=FK.tp_both(0.6, 0.5), v=0.8 - 0.3 * k)
        Ls["crack" if k < 0.6 else "crack_d"].stroke(pts(r), 1.8 * (1 - 0.4 * k), prof=FK.tp_both(0.7, 0.5),
                                                     v=1.0 - 0.45 * k, dash=None if i < 2 else (12, 0.6, 0.0))
        if i < 2:
            Ls["hot"].stroke(pts(r, 20, -0.5, 0.5), 0.8, prof=FK.tp_both(0.7, 0.5), v=1.0 if i == 0 else 0.85)
        for s in (-1, 1):
            a = fa + s * 1.25
            W.puff(Ls["dust"], c[0] + math.cos(a) * r * 0.95, c[1] + math.sin(a) * r * ky * 0.95 - 2, 5 + 3 * k,
                   v=0.8 - 0.3 * k, flat=0.6, seed=s + i)
        rng = P.rng(100 + i)
        for j in (-1, 1):
            a = fa + j * 0.3
            p0 = (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * ky)
            p1 = (c[0] + math.cos(a) * (r + 14), c[1] + math.sin(a) * (r + 14) * ky)
            Ls["crack_d" if i > 1 else "crack"].stroke(W.jag(rng, p0, p1, 4, 1.2), 1.0, prof=FK.tp_tail(0.6), v=0.85 - 0.2 * i)
    fr = C.frames(old, draw)
    return fr, C.base_extra(old, "greatsword", {0})


def ironwall():
    old = W.old_json("ironwall")
    fw, fh, px, py = W.geom(old)

    def draw(f, t, d, i, F):
        Ls = _layers(f)
        Lw = f.L([W.B1, W.B2, W.B3, W.S1, W.S2])        # 녹슨 쇠(흙·녹 재)
        x0 = 40
        hh = 52
        if i < 3:
            # 녹슨 쇠 벽(대검 날 면): 세로 판 + 녹 얼룩 + 홈 혼불
            for yy in range(-hh, hh + 1):
                for xx in range(-7, 8):
                    if abs(yy) > hh - (7 - abs(xx)) * 0.6 and abs(xx) > 4:
                        continue
                    p = t((x0 + xx, yy))
                    n = W.h2(xx, yy // 4, 7)
                    Lw.put(int(p[0]), int(p[1]), (0.35 + 0.45 * (xx + 7) / 14 + 0.15 * n) * (1 - 0.25 * i))
            Ls["crack"].stroke(t.pts([(x0 + 1, -hh + 8), (x0 + 1, hh - 8)]), 1.0, v=1.0 if i == 0 else 0.8,
                               dash=(14, 0.8, 0.1))
            if i == 0:
                Ls["hot"].stroke(t.pts([(x0 + 8, -hh), (x0 + 8, hh)]), 1.0, prof=FK.tp_both(0.6, 0.5), v=1.0)
        if i >= 1:
            for j in range(2):
                r = 18 + 16 * (i - 1) + 12 * j
                pts = [(x0 + 10 + math.cos(a) * r * 0.45, math.sin(a) * r * 1.4) for a in [math.radians(-60 + 120 * u / 30) for u in range(31)]]
                Ls["crack" if i < 3 else "crack_d"].stroke(t.pts(pts), 1.2, prof=FK.tp_both(0.7, 0.5), v=0.9 - 0.2 * i,
                                                           dash=None if i < 3 else (10, 0.55, 0.0))
            rng = P.rng(110 + i)
            for j in range(5):
                p = t((x0 + rng.uniform(-4, 20), rng.uniform(-hh, hh)))
                W.ember(Ls["ember"], p[0], p[1] + 6 * i, rng.uniform(-0.3, 0.3), 1, 4, v=0.8)
                W.flake(Ls["ash"], p[0] + 6, p[1] + 8 * i, 2.2, j, v=0.7)
        if i == 1:
            P.bolt(Ls["hot"], Ls["crack"], t((x0 - 18, -hh - 6)), t((x0 - 26, hh * 0.6)), P.rng(115), w=1.6, branches=1, v=0.95,
                   segs=7, amp=3)
    fr = C.frames(old, draw, origin=(px, py - W.HIT_UP))
    return fr, C.base_extra(old, "greatsword", {0})


SHEETS = {
    "greatsword_combo1": greatsword_combo1, "greatsword_combo2": greatsword_combo2, "greatsword_combo3": greatsword_combo3,
    "greatsword_slash": greatsword_slash, "greatsword_slam": greatsword_slam, "crush": crush, "weight": weight,
    "quake": quake, "pulverize": pulverize, "giant": giant, "guard_wave": guard_wave, "ironwall": ironwall,
}
