"""활 B '혼불 시위 + 재 화살' 이펙트 v3 — 화살(기본·조준·중시·속사·저격)·저격 꼬리 3단·발사 섬광·조준(차지·선·저격 레이저)·중시 적중·섬광·관통.

언어: 재 화살대(회색 재, 윗면 밝음) + 재 깃 + 타는 촉(호박 → 백열) / 꼬리 = 재 연기 + 호박 실 + 불티 / 조준 = 시위와 같은 혼불 실(1px).
모든 투사체는 오른쪽을 향해 그린다(drawnFacing right, 시스템이 회전).
"""
import math

import common as C
import parts as P
import wkit as W
from wkit import FK

RIGHT = W.T("right", 0, 0)


def _frames(name, draw, size=None, pivot=None):
    old = W.old_json(name)
    fw, fh, px, py = W.geom(old)
    if size:
        fw, fh = size
    if pivot:
        px, py = pivot
    out = {}
    for d in old["directions"]:
        t = W.T("right" if d == "any" else d, px, py)
        lst = []
        for i in range(old["frames"]):
            fr = W.Frame(fw, fh, t)
            draw(fr, t, d, i, old["frames"], (px, py))
            lst.append(fr.render())
        out[d] = lst
    return out, old


def arrow(f, x_tail, x_tip, y, thick=1.0, heat=0.8, fletch=2, barb=False):
    """재 화살(화면 좌표, 오른쪽). heat: 촉 밝기(1 = 백열 X0 까지)."""
    Lsh = f.L(W.R_ASHG)
    Lhead = f.L(W.R_EDGE)
    ln = x_tip - x_tail
    hx = x_tip - 7 - 2 * thick
    # 대: 아랫면 S0 · 몸 S1/S2 · 윗면 S3
    Lsh.stroke([(x_tail + 3, y), (hx, y)], 0.9 * thick, v=0.6)
    Lsh.stroke([(x_tail + 5, y - 0.6 * thick), (hx - 2, y - 0.6 * thick)], 0.45, v=0.95)
    # 깃(재): 꼬리 쪽 V 두 쌍
    for k in range(fletch):
        bx = x_tail + 2 + 5 * k
        for s in (-1, 1):
            Lsh.stroke([(bx + 7, y), (bx, y + s * (2.6 + 0.8 * thick))], 0.55, prof=FK.tp_head(0.6), v=0.8 - 0.15 * k)
    # 촉: 호박 바늘 + 백열 끝
    Lhead.stroke([(hx - 1, y), (x_tip, y)], 1.5 * thick, prof=FK.tp_both(0.7, 0.35), v=0.62 + 0.18 * heat)
    Lhead.stroke([(hx + 2, y), (x_tip - 0.5, y)], 0.55, prof=FK.tp_head(0.7), v=0.75 + 0.25 * heat)
    if barb:
        for s in (-1, 1):
            Lhead.stroke([(hx + 4, y), (hx - 1, y + s * 3.6)], 0.7, prof=FK.tp_head(0.6), v=0.72)
    # 촉에서 뒤로 핥는 작은 불꽃 2
    Lhead.stroke([(hx + 3, y - 0.8), (hx - 4, y - 2.4)], 0.5, prof=FK.tp_tail(0.7), v=0.6 + 0.2 * heat)
    Lhead.stroke([(hx + 2, y + 0.8), (hx - 3, y + 2.0)], 0.45, prof=FK.tp_tail(0.7), v=0.55 + 0.2 * heat)


def smoke(f, x0, x1, y, w, seed, phase=0.0, v=0.8, core=0.0, core_hot=False, embers=0):
    """x0(화살 쪽) → x1(꼬리 끝) 재 연기 띠 + 호박 실."""
    Ls = f.L([W.S0, W.S1, W.S2])
    Lc = f.L(W.R_EDGE)
    Le = f.L(W.R_EMBER)
    rng = P.rng(seed)
    n = int(abs(x0 - x1) / 7) + 1
    for k in range(n):
        u = k / max(1, n - 1)
        x = x0 + (x1 - x0) * u
        wob = math.sin(u * 9 + phase * 2 * math.pi) * w * 0.35 * u
        nz = W.h2(k, int(phase * 4), seed)
        r = w * (1 - 0.7 * u) * (0.55 + 0.75 * nz)
        if r < 0.5 or (u > 0.45 and nz < 0.3 + 0.4 * u):
            continue                              # 꼬리 끝으로 갈수록 연기가 끊겨 흩어짐
        Ls.disc(x, y + wob, r * 1.4, r, v=v * (1 - 0.45 * u), edge=0.55)
    if core:
        Lc.stroke([(x0, y), (x0 + (x1 - x0) * core, y)], 0.7 if not core_hot else 0.95, prof=FK.tp_tail(0.8),
                  v=0.95 if core_hot else 0.78)
    for k in range(embers):
        u = FK.frac(rng.random() + phase * 0.5)
        x = x0 + (x1 - x0) * u
        W.ember(Le, x, y + rng.uniform(-w, w) * 1.2, 1, -0.3, 3, v=0.8 - 0.3 * u)


# ------------------------------------------------------------------ 화살
def bow_arrow():
    def draw(f, t, d, i, F, pv):
        arrow(f, pv[0] - 20, pv[0] + 20, pv[1], thick=1.0, heat=0.7)
    fr, old = _frames("bow_arrow", draw)
    return fr, C.base_extra(old, "bow", set())


def bow_arrow_aimed():
    def draw(f, t, d, i, F, pv):
        smoke(f, pv[0] - 18, 3, pv[1], 3.2, 7, v=0.75, embers=2)
        arrow(f, pv[0] - 24, pv[0] + 28, pv[1], thick=1.3, heat=1.0)
    fr, old = _frames("bow_arrow_aimed", draw)
    return fr, C.base_extra(old, "bow", {0})


def heavyarrow():
    def draw(f, t, d, i, F, pv):
        smoke(f, pv[0] - 18, 3, pv[1], 4.2, 8, v=0.85, embers=3)
        arrow(f, pv[0] - 26, pv[0] + 28, pv[1], thick=1.8, heat=1.0, fletch=3, barb=True)
    fr, old = _frames("heavyarrow", draw)
    return fr, C.base_extra(old, "bow", {0})


# 속사·저격 화살·꼬리(1단 갈래)는 bow_tiers.py (55라운드 Q9 — 모양 차별 + 2단 시트)


def bow_muzzle_rapid():
    def draw(f, t, d, i, F, pv):
        L = f.L(W.R_EDGE)
        Lh = f.L(W.R_HOT)
        Le = f.L(W.R_EMBER)
        x, y = pv
        if i == 0:
            L.stroke([(x - 2, y), (x + 34, y)], 3.4, prof=FK.tp_both(0.7, 0.2), v=0.8)
            Lh.stroke([(x, y), (x + 26, y)], 0.9, prof=FK.tp_both(0.7, 0.2), v=1.0)
            Lh.stroke([(x - 1, y - 16), (x - 1, y + 16)], 0.6, prof=FK.tp_both(0.7, 0.5), v=0.95)   # 튕긴 시위 섬광
            for s in (-1, 1):
                L.stroke([(x + 4, y + s * 3), (x + 16, y + s * 13)], 0.8, prof=FK.tp_tail(0.7), v=0.8)
        else:
            L.arc(x + 8, y, 12, 12, -1.2, 1.2, 0.9, v=0.62, dash=(10, 0.55, 0.0))
            rng = P.rng(5)
            for k in range(4):
                W.ember(Le, x + 14 + rng.uniform(0, 14), y + rng.uniform(-10, 10), 1, rng.uniform(-0.5, 0.5), 4, v=0.75)
    fr, old = _frames("bow_muzzle_rapid", draw)
    return fr, C.base_extra(old, "bow", {0})


# ------------------------------------------------------------------ 조준
def aim_charge():
    def draw(f, t, d, i, F, pv):
        Ls = f.L(W.R_ASHG)
        L = f.L(W.R_EDGE)
        Lh = f.L(W.R_HOT)
        c = pv
        r = 40
        Ls.ring(c[0], c[1], r, 0.7, v=0.65, dash=(24, 0.35, 0.0))
        for k in range(4):                       # 네 귀 눈금
            a = k * math.pi / 2
            Ls.stroke([(c[0] + math.cos(a) * (r + 5), c[1] + math.sin(a) * (r + 5)),
                       (c[0] + math.cos(a) * (r + 11), c[1] + math.sin(a) * (r + 11))], 0.6, v=0.8)
        if i < 5:
            p = i / 5 + 0.04
            if p > 0.05:
                a0 = -math.pi / 2
                a1 = a0 + 2 * math.pi * p
                L.arc(c[0], c[1], r, r, a0, a1, 0.9, prof=FK.tp_head(0.4), v=0.82)
                Lh.stamp(c[0] + math.cos(a1) * r, c[1] + math.sin(a1) * r, 1.2, 0.85, soft=0)
        else:
            L.ring(c[0], c[1], r, 1.3, v=0.9)
            Lh.ring(c[0], c[1], r - 6, 0.6, v=1.0, dash=(20, 0.6, 0.0))
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2
                P.glint(Lh, c[0] + math.cos(a) * r, c[1] + math.sin(a) * r, 7, v=0.9)
            Lh.disc(c[0], c[1], 2.5, v=1.0)
    fr, old = _frames("aim_charge", draw)
    return fr, C.base_extra(old, "bow", {5})


def aim_line():
    def draw(f, t, d, i, F, pv):
        L = f.L(W.R_EDGE)
        Ls = f.L(W.R_ASHG)
        y = pv[1]
        Ls.stroke([(0, y + 1.5), (31.9, y + 1.5)], 0.45, v=0.5)
        # 타일 주기 32 도트(구 8 ×4): 16 켜짐 / 16 꺼짐, 양끝 뾰족
        L.stroke([(2, y), (18, y)], 0.65, prof=FK.tp_both(0.6, 0.5), v=0.72 if i == 0 else 0.97)
    fr, old = _frames("aim_line", draw)
    return fr, C.base_extra(old, "bow", {1}) | {"tilePeriodPx": 32}, dict(legacyNote="TileSprite 주기 32 도트(구 8 ×4)", edge_ok=True)


def aim_line_snipe():
    def draw(f, t, d, i, F, pv):
        L = f.L(W.R_EDGE)
        Ls = f.L(W.R_ASHG)
        y = pv[1]
        if i < 5:
            duty = [0.12, 0.4, 0.62, 0.82, 0.95][i]
            v = [0.45, 0.55, 0.65, 0.75, 0.82][i]
            on = 64 * duty
            L.stroke([(1, y), (1 + on, y)], 0.65, prof=FK.tp_both(0.6, 0.5) if i < 4 else None, v=v)
            if i >= 2:
                for s in (-1, 1):
                    Ls.stroke([(4, y + s * 3), (4 + 64 * duty * 0.6, y + s * 3)], 0.45, v=0.55 + 0.1 * i)
        else:
            L.stroke([(0, y), (63.9, y)], 0.7, v=1.0)
            for s in (-1, 1):
                L.stroke([(0, y + s * 3), (63.9, y + s * 3)], 0.45, v=0.66)
    fr, old = _frames("aim_line_snipe", draw)
    return fr, C.base_extra(old, "bow", {5}) | {"tilePeriodPx": 64}, dict(legacyNote="TileSprite 주기 64 도트(구 16 ×4)", edge_ok=True)


# ------------------------------------------------------------------ 적중·꼬리
def heavyarrow_hit():
    old = W.old_json("heavyarrow_hit")

    def draw(f, t, d, i, F):
        c = (t.ox, t.oy)
        Ld = f.L([W.S0, W.S1, W.S2])
        L = f.L(W.R_EDGE)
        Lh = f.L(W.R_HOT)
        Le = f.L(W.R_EMBER)
        if i == 0:
            L.stroke(W.jag(P.rng(3), (c[0] + 4, c[1] - 150), (c[0], c[1] - 10), 8, 2), 0.8, prof=FK.tp_both(0.7, 0.6), v=0.6)
        elif i == 1:
            P.bolt(Lh, L, (c[0] + 4, c[1] - 160), c, P.rng(4), w=1.8, branches=2)
            P.glint(Lh, c[0], c[1], 24, v=1.0, diag=0.4, w=1.2)
        else:
            k = (i - 2) / 2
            r = [32, 56, 72][i - 2]
            P.ground_ring(L, c, r, 1.6 - 0.5 * k, v=0.92 - 0.4 * k, dash=None if i == 2 else (12, 0.65 - 0.25 * k, 0.0))
            if i == 2:
                Lh.disc(c[0], c[1], 3, v=1.0)
                P.radial_cracks(L, c, P.rng(6), 3, 30, 66, v=0.8)
                L.stroke(W.jag(P.rng(7), (c[0] + 2, c[1] - 90), (c[0], c[1] - 6), 6, 2), 0.7, prof=FK.tp_head(0.7), v=0.55,
                         dash=(6, 0.6, 0))
            for j in range(5):
                a = j * 1.3 + i
                W.puff(Ld, c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * P.KY - 3, 4 + 2 * k, v=0.75 - 0.2 * k, flat=0.6, seed=j)
            P.scatter_embers(Le, c, P.rng(8 + i), 5, r * 0.4, r, ky=P.KY, up=0.8, v=(0.5, 0.85))
    fr = C.frames(old, draw)
    return fr, C.base_extra(old, "bow", {1})


def flash():
    def draw(f, t, d, i, F, pv):
        L = f.L(W.R_EDGE)
        Ls = f.L(W.R_ASHG)
        Lh = f.L(W.R_HOT)
        x, y = pv
        Ls.stroke([(x - 2, y), (6, y)], 3.4, prof=FK.tp_tail(0.6), v=0.7)
        L.stroke([(x - 2, y), (6, y)], 1.8, prof=FK.tp_tail(0.7), v=0.85)
        Lh.stroke([(x - 2, y), (30, y)], 0.6, prof=FK.tp_tail(0.6), v=1.0)
        for k in range(2):                      # 뒤로 뛰는 불꽃 토막(12/프레임, 48 주기)
            u = x - 10 - FK.frac((k * 24 + i * 12) / 48.0) * 96
            Lh.stroke([(u, y - 2 + 4 * k), (u - 8, y + 2 - 4 * k)], 0.6, prof=FK.tp_both(0.7, 0.5), v=0.95)
    fr, old = _frames("flash", draw)
    return fr, C.base_extra(old, "bow", set())


def pierce():
    def draw(f, t, d, i, F, pv):
        x, y = pv
        smoke(f, x - 4, 8, y, 3.6, 50 + i, phase=i / 4, v=0.8, core=0.0)
        L = f.L(W.R_EDGE)
        L.stroke([(x, y), (x - 36, y)], 1.3, prof=FK.tp_tail(0.5), v=0.95)
        L.stroke([(x - 30, y), (x - 100, y + 1.5 * math.sin(i * math.pi / 2))], 0.8, prof=FK.tp_tail(0.8), v=0.72)
    fr, old = _frames("pierce", draw)
    return fr, C.base_extra(old, "bow", set())


def muzzle_flash():
    old = W.old_json("muzzle_flash")

    def draw(f, t, d, i, F):
        L = f.L([W.A19, W.A21, W.A23, W.A25])
        Lh = f.L(W.R_HOT)
        if i == 0:
            L.stroke(t.pts([(-4, 0), (16, 0)]), 4.2, prof=FK.tp_both(0.6, 0.25), v=0.9)
            Lh.stroke(t.pts([(-2, 0), (11, 0)]), 1.2, prof=FK.tp_both(0.6, 0.25), v=1.0)
            for s in (-1, 1):
                L.stroke(t.pts([(2, s * 2), (11, s * 10)]), 0.8, prof=FK.tp_tail(0.7), v=0.85)
        else:
            L.stroke(t.pts([(-2, 0), (7, 0)]), 2.4, prof=FK.tp_both(0.6, 0.3), v=0.75)
            for k in range(3):
                p = t((8 + 4 * k, (k - 1) * 5))
                W.ember(L, p[0], p[1], 0, -1, 2, v=0.7)
    fr = C.frames(old, draw)
    return fr, C.base_extra(old, None, {0}), dict(swap="none")  # 53라운드 Q62: fx 는 바닥 팔레트 교체 제외(구: 층 램프 19~25 스왑)


SHEETS = {"bow_arrow": bow_arrow, "bow_arrow_aimed": bow_arrow_aimed, "heavyarrow": heavyarrow,
          "bow_muzzle_rapid": bow_muzzle_rapid,
          "aim_charge": aim_charge, "aim_line": aim_line, "aim_line_snipe": aim_line_snipe, "heavyarrow_hit": heavyarrow_hit,
          "flash": flash, "pierce": pierce, "muzzle_flash": muzzle_flash}


def _tier1(name):
    def fn():
        import bow_tiers
        return bow_tiers.TIER1[name]()
    return fn


for _n in ("bow_arrow_rapid", "bow_arrow_aimed_rapid", "bow_arrow_snipe", "bow_arrow_aimed_snipe",
           "bow_arrow_snipe_lv1", "bow_arrow_snipe_lv2", "bow_arrow_snipe_lv3"):
    SHEETS[_n] = _tier1(_n)
