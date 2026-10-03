"""1단 갈래 기본 공격 이펙트 v3 (51라운드 §4 · 53라운드 Q5) — 새 무기 기준으로 다시 그림.

fx/<weapon>_combo<n>_<branch>: 크기·피벗·프레임·ms·anchor·spawn·판정 필드 = 기본 시트(구 갈래 JSON 복사 → ×4). 판정 불변.
  칼  iai   거합 = 초승달 잔광: 기본보다 가는 초승달 + 판정 가장자리 바깥 1px 이어진 잔광 호(꼬리까지 남음) + 끝에서 접선으로 새는 바늘 빛
      batto 발도 = 직선 섬광: 호 대신 판정 안쪽의 곧은 섬광(1타 세로 · 2타 아래→위 · 3타 X) + 판정 범위 1px 재 점선 호
  대검 crush  파쇄 = 깨진 띠: 비스듬한 틈으로 끊긴 녹 띠 + 틈에서 바깥으로 갈라지는 혼불 균열 + 튀어 떨어지는 돌 파편
      weight 중압 = 무거운 압력: 더 어둡고 넓은 흙·녹 띠 + 끊기지 않는 녹은 홈 + 바깥으로 밀려나는 압력 파동 2겹(3타 바닥 눌림 고리)
  단검 twin  쌍격 = 이중 바늘: 나란한 찌르기 두 줄(둘째 1프레임 늦음), 3타는 촉에서 만나는 가위 + 교차 섬광
      gale  질풍 = 바람 줄기: 가는 본 바늘 + 몸 옆에서 촉으로 모여드는 1px 재 바람 줄기(혼불 결) → 다음 프레임 앞으로 밀려남
활 rapid/snipe 은 defs_bow(화살·꼬리·조준선)에서 다시 그렸다.
"""
import math

import common as C
import defs_dagger as DG
import parts as P
import swing
import wkit as W
from wkit import FK


def _geo(name):
    old = W.old_json(name)
    fw, fh, px, py = W.geom(old)
    return old, (fw, fh), (px, py - W.HIT_UP)


def _extra(old, weapon, branch, base):
    ex = C.base_extra(old, weapon, C.bright_of(old))
    ex["branchDesignV3"] = __doc__.split("\n")[[i for i, l in enumerate(__doc__.split("\n")) if (" %s " % branch) in l][0]].strip()
    return ex


def _fill(n, weapon, R):
    """53라운드 Q63: 갈래도 기본 연격과 같은 칼끝 반경까지 메움(무기 오버레이는 갈래와 공용)."""
    return C.trail_fill("%s_combo%d" % (weapon, n), R)


def _over(base, top):
    for d in base:
        for i, im in enumerate(base[d]):
            im2 = top[d][i].copy()
            im2.alpha_composite(im)
            base[d][i] = im2
    return base


# ------------------------------------------------------------------ 칼
KW = {1: 11, 2: 9, 3: 14}


def iai(n):
    name = "katana_combo%d_iai" % n
    old, size, o = _geo(name)
    R = old["hitRadiusPx"] * W.K4
    a0, a1 = math.radians(old["arcFromDeg"]), math.radians(old["arcToDeg"])
    imp = old["impactFrame"]
    fr = swing.swing_frames("katana", size, o, R, old["arcFromDeg"], old["arcToDeg"], old["frames"], imp,
                            bright=C.bright_of(old), wmax=KW[n] * 0.75, seed=400 + n,
                            echoes=[(-10, 1, 0.5)] if n == 3 else (), tail_dash=False, fill_to=_fill(n, "katana", R)[0])
    sgn = 1 if a1 > a0 else -1

    def draw(f, t, d, i, F):
        if i < imp:
            return
        L = f.L(W.R_EDGE)
        k = (i - imp) / max(1, F - 1 - imp)
        v = 0.97 if i == imp else 0.82 - 0.38 * k
        for j, dr in enumerate((6, 12) if n == 3 else (6,)):
            L.stroke(t.pts(W.arc_pts(R + dr, a0, a1)), 0.6, prof=FK.tp_both(0.5, 0.6), v=v - 0.08 * j)
        if i <= imp + 1:                          # 양 끝 접선 바늘 빛
            for a, s in ((a0, -1), (a1, 1)):
                p = (math.cos(a) * (R + 6), math.sin(a) * (R + 6))
                tg = (-math.sin(a) * sgn * s, math.cos(a) * sgn * s)
                q = (p[0] + tg[0] * 16, p[1] + tg[1] * 16)
                L.stroke(t.pts([p, q]), 0.7, prof=FK.tp_tail(0.8), v=v)
    glow = C.frames(old, draw, origin=o)
    return _over(fr, glow), dict(_extra(old, "katana", "iai", None), trailFill=_fill(n, "katana", R)[1])


BATTO_LINES = {1: [((0.72, -0.62), (0.72, 0.62))],
               2: [((0.42, 0.58), (0.82, -0.52))],
               3: [((0.38, -0.5), (0.9, 0.5)), ((0.38, 0.5), (0.9, -0.5))]}


def batto(n):
    name = "katana_combo%d_batto" % n
    old, size, o = _geo(name)
    R = old["hitRadiusPx"] * W.K4
    a0, a1 = math.radians(old["arcFromDeg"]), math.radians(old["arcToDeg"])
    imp = old["impactFrame"]
    lines = BATTO_LINES[n]

    def draw(f, t, d, i, F):
        Lr = f.L([W.S0, W.S1])
        Lv = f.L(W.R_ASHG)
        L = f.L(W.R_EDGE)
        Lf = f.L(W.R_ASHG)
        Lh = f.L(W.R_HOT)
        Lr.stroke(t.pts(W.arc_pts(R, a0, a1)), 0.55, v=0.9, dash=(12, 0.4, 0.0))      # 판정 범위 점선
        k = 0.0 if i <= imp else (i - imp) / max(1, F - 1 - imp)
        rng = P.rng(500 + n)
        for j, ((x0, y0), (x1, y1)) in enumerate(lines):
            p0, p1 = (x0 * R, y0 * R), (x1 * R, y1 * R)
            if i < imp:
                m = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
                L.stroke(t.pts([m, (m[0] + (p1[0] - m[0]) * 0.3, m[1] + (p1[1] - m[1]) * 0.3)]), 0.8, prof=FK.tp_both(0.7, 0.5), v=0.62)
                continue
            sh = 1 - 0.55 * k                    # 가운데로 줄어듦
            m = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
            q0 = (m[0] + (p0[0] - m[0]) * sh, m[1] + (p0[1] - m[1]) * sh)
            q1 = (m[0] + (p1[0] - m[0]) * sh, m[1] + (p1[1] - m[1]) * sh)
            last = i == F - 1
            Lv.stroke(t.pts([q0, q1]), 4.2 * (1 - 0.5 * k), prof=FK.tp_both(0.7, 0.5), v=0.8 - 0.3 * k,
                      dash=None if not last else (8, 0.5, 0.2))
            L.stroke(t.pts([q0, q1]), 1.8 * (1 - 0.4 * k), prof=FK.tp_both(0.7, 0.5), v=(0.95 if i == imp else 0.82 - 0.35 * k),
                     dash=None if not last else (9, 0.55, 0.1))
            if i == imp:
                Lh.stroke(t.pts([q0, q1]), 0.6, prof=FK.tp_both(0.7, 0.5), v=1.0)
                c = t(m)
                P.glint(Lh, c[0], c[1], 14, v=1.0)
            if i > imp:                          # 섬광에서 벗겨지는 재 조각
                for m2 in range(6):
                    u = rng.uniform(0.1, 0.9)
                    pp = t((q0[0] + (q1[0] - q0[0]) * u, q0[1] + (q1[1] - q0[1]) * u))
                    W.flake(Lf, pp[0] + rng.uniform(-5, 5), pp[1] + 5 * k * 3 + rng.uniform(0, 4), rng.uniform(1.2, 2.6),
                            rng.uniform(0, 6), v=rng.uniform(0.5, 1.0))
    fr = C.frames(old, draw, origin=o)
    return fr, _extra(old, "katana", "batto", None)


# ------------------------------------------------------------------ 대검
GW = {1: 30, 2: 27, 3: 36}


def crush(n):
    name = "greatsword_combo%d_crush" % n
    old, size, o = _geo(name)
    R = old["hitRadiusPx"] * W.K4
    a0, a1 = math.radians(old["arcFromDeg"]), math.radians(old["arcToDeg"])
    imp = old["impactFrame"]
    gaps = (0.18, 0.36, 0.53, 0.7, 0.86)
    fr = swing.swing_frames("gs", size, o, R, old["arcFromDeg"], old["arcToDeg"], old["frames"], imp, bright=C.bright_of(old),
                            wmax=GW[n] * 0.85, seed=600 + n, dust=3, gaps=gaps, cracks=(n == 3), fill_to=_fill(n, "greatsword", R)[0])

    def draw(f, t, d, i, F):
        if i < imp:
            return
        Lc = f.L(W.R_EDGE)
        Ls = f.L(W.R_ASHB)
        Le = f.L(W.R_EMBER)
        k = (i - imp) / max(1, F - 1 - imp)
        rng = P.rng(610 + n)
        for g in gaps[:4]:
            a = a0 + (a1 - a0) * (g + 0.02)
            p0 = (math.cos(a) * (R - 2), math.sin(a) * (R - 2))
            p1 = (math.cos(a + 0.05) * (R + rng.uniform(20, 30)), math.sin(a + 0.05) * (R + rng.uniform(20, 30)))
            pts = W.jag(rng, p0, p1, 4, 2.0)
            Lc.stroke(t.pts(pts), 1.1 - 0.4 * k, prof=FK.tp_tail(0.6), v=0.95 - 0.5 * k if i > imp else 0.98,
                      dash=None if k < 0.7 else (6, 0.6, 0.0))
            for m in range(2):                    # 돌 파편: 바깥으로 튀며 떨어짐(화면 아래)
                aa = a + rng.uniform(-0.08, 0.08)
                rr = R + 8 + (16 + 10 * m) * (0.3 + k)
                q = t((math.cos(aa) * rr, math.sin(aa) * rr))
                W.flake(Ls, q[0], q[1] + 14 * k * k, 3.6 - 1.2 * k, aa + m, v=0.95 - 0.25 * k)
                if k < 0.4:
                    W.ember(Le, q[0], q[1], *DG._vec(t, aa), 5, v=0.85)
    top = C.frames(old, draw, origin=o)
    return _over(fr, top), dict(_extra(old, "greatsword", "crush", None), trailFill=_fill(n, "greatsword", R)[1])


def weight(n):
    name = "greatsword_combo%d_weight" % n
    old, size, o = _geo(name)
    R = old["hitRadiusPx"] * W.K4
    a0, a1 = math.radians(old["arcFromDeg"]), math.radians(old["arcToDeg"])
    imp = old["impactFrame"]
    fr = swing.swing_frames("gs_dark", size, o, R, old["arcFromDeg"], old["arcToDeg"], old["frames"], imp, bright=C.bright_of(old),
                            wmax=GW[n] * 1.05, seed=700 + n, dust=4, fill_to=_fill(n, "greatsword", R)[0])

    def draw(f, t, d, i, F):
        if i < imp:
            return
        Ld = f.L(W.R_DUST)
        Lc = f.L(W.R_EDGE)
        k = (i - imp) / max(1, F - 1 - imp)
        for j in range(2):                        # 압력 파동 2겹: 밝은 안선 + 흙먼지 바깥선, 밀려남
            rr = R + 6 + 10 * j + 30 * k
            if rr > min(size) / 2 - 8:
                continue
            Ld.stroke(t.pts(W.arc_pts(rr + 3, a0 + 0.1, a1 - 0.1)), 2.2 * (1 - 0.5 * k), prof=FK.tp_both(0.6, 0.5), v=0.7 - 0.3 * k)
            Lc.stroke(t.pts(W.arc_pts(rr, a0 + 0.15, a1 - 0.15)), 0.7, prof=FK.tp_both(0.6, 0.5), v=0.58 - 0.25 * k - 0.08 * j,
                      dash=None if k < 0.6 else (10, 0.5, 0.0))
        if n == 3:                               # 바닥 눌림 납작 고리(앞-아래)
            c = t((R * 0.55, 0))
            c = (c[0], c[1] + W.HIT_UP - 4)
            rr = R * (0.32 + 0.3 * k)
            Ld.arc(c[0], c[1], rr, rr * 0.4, 0, 2 * math.pi, 2.4 * (1 - 0.5 * k), v=0.75 - 0.3 * k)
            Lc.arc(c[0], c[1], rr * 0.92, rr * 0.36, 0, 2 * math.pi, 0.8, v=0.55 - 0.25 * k, dash=(14, 0.6, 0.0) if k > 0.5 else None)
    top = C.frames(old, draw, origin=o)
    return _over(fr, top), dict(_extra(old, "greatsword", "weight", None), trailFill=_fill(n, "greatsword", R)[1])


# ------------------------------------------------------------------ 단검
def _shift(t, off):
    p = t(off)
    return W.T(t.d, p[0], p[1])


def twin(n):
    name = "dagger_combo%d_twin" % n
    old, size, o = _geo(name)
    th = old["thrust"]
    ang = math.radians(th["angleDeg"])
    x0, x1 = th["fromPx"] * W.K4, th["lengthPx"] * W.K4 + 6
    st = DG._states(old["frames"], old["impactFrame"])

    def draw(f, t, d, i, F):
        for j, s in enumerate((-1, 1)):
            ii = i - j                            # 둘째 줄 1프레임 늦음
            if ii < 0:
                continue
            kind, k = st[min(ii, F - 1)]
            if j == 1 and ii == 0:
                kind = "pre"
            off = (-math.sin(ang) * 10 * s, math.cos(ang) * 10 * s)
            if n == 3:                            # 가위: 촉에서 만남
                t2 = _shift(t, off)
                a2 = ang - math.atan2(10 * s, x1 - 4)
                DG.thrust_frame(f, t2, kind, k, a2, x0, math.hypot(x1 - 4, 10) + 2, 2.4, 800 + j, cracks=1)
            else:
                DG.thrust_frame(f, _shift(t, off), kind, k, ang, x0, x1, 2.4, 800 + 10 * n + j, cracks=1)
        if n == 3 and i == 2:
            Lh = f.L(W.R_HOT)
            c = t((math.cos(ang) * (x1 - 2), math.sin(ang) * (x1 - 2)))
            P.glint(Lh, c[0], c[1], 12, v=1.0, diag=0.6)
    fr = C.frames(old, draw, origin=o)
    return fr, _extra(old, "dagger", "twin", None)


def gale(n):
    name = "dagger_combo%d_gale" % n
    old, size, o = _geo(name)
    th = old["thrust"]
    ang = math.radians(th["angleDeg"])
    x0, x1 = th["fromPx"] * W.K4, th["lengthPx"] * W.K4 + 6
    st = DG._states(old["frames"], old["impactFrame"])
    nwind = 4 if n == 3 else 3
    ca, sa = math.cos(ang), math.sin(ang)

    def R_(u, v):
        u = min(u, 116.0)                         # 256 틀(반경 128) 안
        return (ca * u - sa * v, sa * u + ca * v)

    def draw(f, t, d, i, F):
        kind, k = st[i]
        DG.thrust_frame(f, t, kind, k, ang, x0, x1, 2.2, 900 + n, cracks=1)
        if kind == "pre":
            return
        Lw = f.L(W.R_ASHG)
        Lc = f.L(W.R_EDGE)
        push = 0 if kind == "hit" else 12 * k
        for j in range(nwind):
            s = 1 if j % 2 else -1
            side = 16 + 8 * (j // 2)
            p0 = R_(-8 + push, s * side)
            p1 = R_(x1 * 0.55 + push, s * (side * 0.55))
            p2 = R_(x1 * 0.92 + push, s * 3)
            pts = FK.qbez(p0, p1, p2)
            v = 0.85 if kind == "hit" else 0.75 - 0.35 * k
            Lw.stroke(t.pts(pts), 0.7, prof=FK.tp_head(0.6), v=v, dash=None if k < 0.6 else (9, 0.6, 0.1 * j))
            Lc.stroke(t.pts(pts[len(pts) // 2:]), 0.5, prof=FK.tp_head(0.7), v=0.6 if kind == "hit" else 0.55 - 0.25 * k)
        if kind == "hit" or k < 0.6:              # 촉 너머로 이어지는 바람 한 줄
            Lw.stroke(t.pts([R_(x1 * 0.9 + push, 0), R_(x1 + 14 + push, 1)]), 0.6, prof=FK.tp_tail(0.7), v=0.8)
    fr = C.frames(old, draw, origin=o)
    return fr, _extra(old, "dagger", "gale", None)


SHEETS = {}
for _n in (1, 2, 3):
    SHEETS["katana_combo%d_iai" % _n] = (lambda n: lambda: iai(n))(_n)
    SHEETS["katana_combo%d_batto" % _n] = (lambda n: lambda: batto(n))(_n)
    SHEETS["greatsword_combo%d_crush" % _n] = (lambda n: lambda: crush(n))(_n)
    SHEETS["greatsword_combo%d_weight" % _n] = (lambda n: lambda: weight(n))(_n)
    SHEETS["dagger_combo%d_twin" % _n] = (lambda n: lambda: twin(n))(_n)
    SHEETS["dagger_combo%d_gale" % _n] = (lambda n: lambda: gale(n))(_n)
