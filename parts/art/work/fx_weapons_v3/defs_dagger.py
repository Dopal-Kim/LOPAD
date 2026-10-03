"""단검 B '재 송곳니' 이펙트 v3 — 찌르기 연격(+가열 1~3)·기본 베기·쌍격·질풍·난무·암살·잔상·그림자 걸음·출혈.

언어: 백열 끝 바늘 찌르기(몸은 가는 재 방추, 심은 호박, 끝 4도트 백열) + 지나간 자리 공중에 남는 가는 호박 금(균열)
→ 금이 식으며 재 조각으로 떨어진다(시안 raw_dagger_B 공격 컷).
"""
import math

import common as C
import parts as P
import swing
import wkit as W
from wkit import FK

FACE = {"right": (1, 0), "left": (-1, 0), "down": (0, 1), "up": (0, -1)}


def _states(F, impact=1):
    out = []
    n = F - 1 - impact
    for i in range(F):
        if i < impact:
            out.append(("pre", 0.0))
        elif i == impact:
            out.append(("hit", 0.0))
        else:
            out.append(("after", (i - impact) / n))
    return out


def thrust_frame(f, t, kind, k, ang, x0, x1, hw, seed, heat=0, side=(), cracks=3, echo=False):
    """찌르기 한 프레임. 로컬(오른쪽 보기): 원점 = 몸 중심, ang = 화면각(+ 아래)."""
    Lflake = f.L(W.R_ASHG)
    Lbody = f.L(W.R_ASHG if heat < 3 else [W.A19, W.A21, W.A23, W.A25])
    Lcrack = f.L(W.R_EDGE)
    Lcore = f.L(W.R_EDGE)
    Lember = f.L(W.R_EMBER)
    ca, sa = math.cos(ang), math.sin(ang)

    def P_(u, v=0.0):
        return (ca * u - sa * v, sa * u + ca * v)
    rng = P.rng(seed)
    L = x1 - x0
    # 금(균열): 경로 40~90% 지점에서 뒤·바깥으로 갈라지는 가는 선 — 프레임 사이 같은 모양 유지
    crack_pts = []
    for j in range(cracks + heat):
        u = x0 + L * rng.uniform(0.42, 0.92)
        sgn = 1 if j % 2 else -1
        a = sgn * rng.uniform(0.35, 0.75)
        ln = rng.uniform(14, 26) * (1 + 0.15 * heat)
        p0 = P_(u, sgn * rng.uniform(0.5, 2.0))
        p1 = P_(u - math.cos(a) * ln, math.sin(a) * ln * 1.0)
        pts = W.jag(rng, p0, p1, n=4, amp=1.4)
        crack_pts.append(pts)
        if rng.random() < 0.6:                  # 잔가지
            q = pts[2]
            q1 = (q[0] - ca * 6 + sgn * sa * 4, q[1] - sa * 6 - sgn * ca * 4)
            crack_pts.append([q, q1])
    if kind == "pre":
        a, b = P_(x0), P_(x0 + L * 0.35)
        Lcore.stroke(t.pts([a, b]), 0.9, prof=FK.tp_head(0.6), v=0.62)
        e = t(b)
        Lcore.stamp(e[0], e[1], 1.0, 0.72, soft=0)
        return
    hot = kind == "hit"
    s0 = x0 if hot else x0 + L * (0.3 + 0.6 * k)
    s1 = x1 if hot else x1 - L * 0.06 * k
    w = hw * (1.0 if hot else max(0.35, 1 - 0.65 * k))
    if not (kind == "after" and k >= 0.99):
        # 몸: 뒤 가늘고 앞 70% 가장 굵고 끝 바늘
        pts = [P_(s0), P_(s1)]
        Lbody.stroke(t.pts(pts), w, prof=FK.tp_both(0.75, 0.7), v=0.9 if hot else 0.75 * (1 - 0.3 * k))
        cv = (1.0 if hot else min(0.6, 0.62 - 0.3 * k))

        def vp(s):
            return 0.55 + 0.45 * max(0.0, (s - 0.55) / 0.45) ** 0.8
        Lcore.stroke(t.pts(pts), max(0.6, w * 0.32), prof=FK.tp_both(0.6, 0.8), v=cv, vprof=vp)
        if hot:
            tip = t(P_(s1 - 2))
            P.glint(Lcore, tip[0], tip[1], 6 + 2 * heat, v=1.0, w=0.8)
            for j in range(2 + heat):          # 끝에서 앞으로 튀는 불티
                aa = ang + rng.uniform(-0.6, 0.6)
                e = t(P_(s1 + 4 + 3 * j, rng.uniform(-3, 3)))
                W.ember(Lember, e[0], e[1], *_vec(t, aa), rng.uniform(3, 6), v=0.9)
    for e in side:                              # 옆 그림자 줄기(±각)
        a2 = ang + e
        c2, s2 = math.cos(a2), math.sin(a2)
        if hot or k < 0.6:
            p0 = (c2 * (x0 + 6), s2 * (x0 + 6))
            p1 = (c2 * (x1 - 10), s2 * (x1 - 10))
            Lbody.stroke(t.pts([p0, p1]), hw * 0.5, prof=FK.tp_both(0.7, 0.7), v=0.6 * (1 - 0.5 * k))
            Lcrack.stroke(t.pts([p0, p1]), 0.6, prof=FK.tp_both(0.7, 0.75), v=0.62 * (1 - 0.4 * k))
    if echo and not hot and k < 0.7:            # 가열 2: 한 겹 뒤 잔상
        pts = [P_(x0 - 8), P_(x1 - 18)]
        Lbody.stroke(t.pts(pts), hw * 0.7, prof=FK.tp_both(0.75, 0.7), v=0.55)
    # 금: 판정 = A25(백열 없음, 날 끝만 백열) → 식으며 끊김 → 재
    cvk = 0.6 if hot else 0.58 * (1 - 0.45 * k)          # 금 = A25 → A23 → A21 (백열은 끝만)
    for pts in crack_pts:
        if kind == "after" and k >= 0.99:
            Lcrack.stroke(t.pts(pts), 0.7, prof=FK.tp_both(0.8, 0.4), v=0.42, dash=(5, 0.5, 0.3))
        else:
            Lcrack.stroke(t.pts(pts), 0.85, prof=FK.tp_both(0.8, 0.35), v=cvk, dash=None if k < 0.5 else (7, 0.7, 0.1))
    if not hot:                                 # 금에서 떨어지는 재 조각
        for j, pts in enumerate(crack_pts):
            q = t(pts[len(pts) // 2])
            for m in range(2):
                W.flake(Lflake, q[0] + rng.uniform(-4, 4), q[1] + 5 * k * (2 + m) + rng.uniform(0, 3),
                        rng.uniform(1.2, 2.4), rng.uniform(0, 6), v=rng.uniform(0.5, 1.0))


def _vec(t, a):
    o = t((0, 0))
    p = t((math.cos(a), math.sin(a)))
    return (p[0] - o[0], p[1] - o[1])


def combo(name, heat=0):
    old = W.old_json(name)
    fw, fh, px, py = W.geom(old)
    th = old["thrust"]
    ang = math.radians(th["angleDeg"])
    x0 = th["fromPx"] * W.K4
    vis = old.get("visualLengthPx", th["lengthPx"]) * W.K4
    x1 = vis + 6
    hw = 3.0 + 0.5 * heat
    side = (math.radians(9), math.radians(-9)) if old.get("comboIndex") == 3 else ()
    st = _states(old["frames"], old["impactFrame"])
    seed = 300 + old.get("comboIndex", 1) * 10 + heat

    def draw(f, t, d, i, F):
        kind, k = st[i]
        thrust_frame(f, t, kind, k, ang, x0, x1, hw, seed, heat=heat, side=side, cracks=3, echo=heat >= 2)
    fr = C.frames(old, draw, origin=(px, py - W.HIT_UP))
    return fr, C.base_extra(old, "dagger", C.bright_of(old))


def _heat(name):
    base, lv = name.rsplit("_heat", 1)
    return lambda: combo(name, heat=int(lv))


def dagger_slash():
    return C.slash("dagger_slash", "dagger", 15, -75, 55, 6, seed=31)


def twin():
    old = W.old_json("twin")
    fw, fh, px, py = W.geom(old)
    fr = swing.swing_frames("dagger", (fw, fh), (px, py - W.HIT_UP), 52, -88, 60, old["frames"], 1, bright={1, 2}, wmax=6,
                            seed=32, echoes=[(24, 1, 1.0)], rays=3, long_glow=True)
    return fr, C.base_extra(old, "dagger", {1, 2})


def dance():
    old = W.old_json("dance")
    fw, fh, px, py = W.geom(old)
    fr = swing.swing_frames("dagger", (fw, fh), (px, py - W.HIT_UP), 56, -92, 72, old["frames"], 1, bright={1, 2, 3}, wmax=6,
                            seed=33, echoes=[(28, 1, 1.0, True), (56, 2, 1.0)], rays=4, long_glow=True)
    return fr, C.base_extra(old, "dagger", {1, 2, 3})


def gale():
    old = W.old_json("gale")
    fw, fh, px, py = W.geom(old)

    def draw(f, t, d, i, F):
        Ls = f.L(W.R_ASHG)
        Lc = f.L(W.R_EDGE)
        Le = f.L(W.R_EMBER)
        for j, y in enumerate((-22, 0, 20)):
            x0, x1 = -24 - 6 * abs(j - 1), -112 + 10 * abs(j - 1)
            Ls.stroke(t.pts([(x0, y), (x1, y + 4 * (j - 1))]), 1.5 - 0.3 * abs(j - 1), prof=FK.tp_both(0.6, 0.15), v=0.75)
            # 뒤로 흐르는 혼불 토막: 주기 32, 프레임당 8 → 4프레임 이음새 없음
            for m in range(4):
                u = x0 - FK.frac((m * 32 + i * 8) / 128.0) * (x0 - x1)
                ln = 10 + 4 * (j == 1)
                k = (x0 - u) / (x0 - x1)
                if u - ln < x1:
                    continue
                Lc.stroke(t.pts([(u, y + 4 * (j - 1) * k), (u - ln, y + 4 * (j - 1) * k)]), 0.8,
                          prof=FK.tp_both(0.7, 0.3), v=0.85 - 0.35 * k)
        for m in range(3):
            u = -30 - FK.frac((m * 43 + i * 8) / 129.0) * 90
            p = t((u, -30 + 30 * m + 4 * math.sin(u / 9)))
            W.ember(Le, p[0], p[1], *_vec(t, math.pi), 3, v=0.75)
    fr = C.frames(old, draw, origin=(px, py - W.HIT_UP))
    return fr, C.base_extra(old, "dagger", set())


def _pool(L, c, rx, v=0.8):
    L.disc(c[0], c[1], rx, rx * 0.32, v=v, edge=0.6)


def assassin():
    old = W.old_json("assassin")
    mask, _, (mpx, mpy) = P.silhouette_mask("player_idle_free", "down", 0)
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    sc = 0.62

    def draw(f, t, d, i, F):
        Lp = f.L([W.B0, W.B0])
        Lsh = f.L([W.B0, W.B1, W.B2])
        Lrim = f.L([W.S0, W.S1, W.S2])
        Lc = f.L(W.R_EDGE)
        Lh = f.L(W.R_HOT)
        c = (t.ox, t.oy)
        _pool(Lp, (c[0], c[1] + 34), [70, 84, 84, 70, 40][i], v=0.7)
        if i < 4:
            r = [92, 62, 40, 30][i]
            for k, a in enumerate((-math.pi / 2, math.pi * 0.85, math.pi * 0.15)):
                gx, gy = c[0] + math.cos(a) * r, c[1] + 34 + math.sin(a) * r * 0.5
                ox, oy = int(gx - mpx * sc), int(gy - mpy * sc)
                stripe = (6, 0.55, k * 2) if i == 3 else None
                P.paint_mask(Lsh, mask, ox, oy, v=0.6 + 0.2 * (i > 0), rim=Lrim, rim_v=0.7 + 0.1 * i, stripe=stripe, scale=sc)
        if i in (2, 3):
            for a in (math.pi / 4, 3 * math.pi / 4):
                p0 = (c[0] - math.cos(a) * 70, c[1] - math.sin(a) * 70)
                p1 = (c[0] + math.cos(a) * 70, c[1] + math.sin(a) * 70)
                Lc.stroke([p0, p1], 2.4 if i == 2 else 1.4, prof=FK.tp_both(0.7, 0.5), v=0.9 if i == 2 else 0.7,
                          dash=None if i == 2 else (10, 0.6, 0.0))
                if i == 2:
                    Lh.stroke([p0, p1], 0.8, prof=FK.tp_both(0.7, 0.5), v=1.0)
        if i >= 3:
            P.scatter_flakes(f.L(W.R_ASHG), c, P.rng(70 + i), 10, 20, 80, fall=6 * (i - 2))
            P.scatter_embers(f.L(W.R_EMBER), c, P.rng(80 + i), 4, 30, 80, v=(0.5, 0.8))
    fr = C.frames(old, draw)
    ex = C.base_extra(old, "dagger", {2})
    ex["heroSource"] = "player/v3/player_idle_free down 0 실루엣 ×0.62 — 주인공이 바뀌면 재빌드"
    return fr, ex


def afterimage():
    old = W.old_json("afterimage")
    fw, fh, px, py = W.geom(old)

    def draw(f, t, d, i, F):
        Lp = f.L([W.B0, W.B0])
        Lsh = f.L([W.B0, W.B1, W.B2])
        Lrim = f.L([W.S0, W.S1, W.S2])
        Lc = f.L(W.R_EDGE)
        Lh = f.L(W.R_HOT)
        mask, _, (mpx, mpy) = P.silhouette_mask("player_dash", d, 1)
        fx, fy = FACE[d]
        perp = (-fy, fx)
        _pool(Lp, (px, py - 4), [60, 52, 40, 28, 16][i], v=0.7)
        if i < 4:
            spread = [0, 32, 52, 60][i]
            for k in ((-1, 1) if spread else ()):
                ox, oy = int(px - mpx + perp[0] * k * spread), int(py - mpy + perp[1] * k * spread)
                P.paint_mask(Lsh, mask, ox, oy, v=0.55, rim=Lrim, rim_v=0.6, stripe=(5, 0.5, k) if i >= 2 else None)
            P.paint_mask(Lsh, mask, px - mpx, py - mpy, v=0.75, rim=Lrim, rim_v=0.9 - 0.1 * i,
                         stripe=(4, 0.55 - 0.1 * (i - 2), 0) if i >= 2 else None)
        if i == 1:
            c = (px, py - 70)
            for a in (math.pi / 4, 3 * math.pi / 4):
                p0 = (c[0] - math.cos(a) * 50, c[1] - math.sin(a) * 50)
                p1 = (c[0] + math.cos(a) * 50, c[1] + math.sin(a) * 50)
                Lc.stroke([p0, p1], 2.0, prof=FK.tp_both(0.7, 0.5), v=0.88)
                Lh.stroke([p0, p1], 0.7, prof=FK.tp_both(0.7, 0.5), v=1.0)
        if i >= 3:
            P.scatter_flakes(f.L(W.R_ASHG), (px, py - 60), P.rng(90 + i), 12, 10, 60, fall=8 * (i - 2))
    fr = C.frames(old, draw)
    ex = C.base_extra(old, "dagger", {1})
    ex["heroSource"] = "player/v3/player_dash 열 1(방향 행별) 실루엣"
    return fr, ex


def shadowstep_ghost():
    old = W.old_json("shadowstep_ghost")
    # 주인공 v3(1.5배) 실루엣에 맞춰 ×6 (dash_trail 과 같은 규칙) — 96×144, 피벗 = 주인공 발 (48,138)
    fw, fh, px, py = 96, 144, 48, 138

    def draw(f, t, d, i, F):
        Lp = f.L([W.B0, W.B0])
        Lsh = f.L([W.B0, W.B1, W.B2])
        Lrim = f.L([W.S0, W.S1, W.S2])
        mask, _, (mpx, mpy) = P.silhouette_mask("player_idle_free", d, 0)
        Lp.disc(px, py - 1, [30, 22, 13][i], [3.5, 2.8, 2][i], v=0.75, edge=0.6)
        keep = None if i < 2 else (lambda x, y: W.h2(x // 3, y // 5, 3) > 0.45)
        P.paint_mask(Lsh, mask, px - mpx, py - mpy, v=0.6 - 0.1 * i, rim=Lrim, rim_v=0.75 - 0.15 * i,
                     stripe=(4, 0.5, 0) if i >= 1 else None, keep=keep)
    out = {}
    for d in old["directions"]:
        t = W.T(d, px, py)
        lst = []
        for i in range(old["frames"]):
            fr = W.Frame(fw, fh, t)
            draw(fr, t, d, i, old["frames"])
            lst.append(fr.render())
        out[d] = lst
    ex = C.base_extra(old, "dagger", set())
    ex["heroSource"] = "player/v3/player_idle_free 열 0(방향 행별) 실루엣"
    return out, ex, dict(pivot=(px, py), legacyNote="주인공 v3(1.5배)에 맞춰 ×6 (구 16×24 → 96×144) — dash_trail 과 같은 규칙. 피벗 = 주인공 발.")


def bleed():
    old = W.old_json("bleed")

    def draw(f, t, d, i, F):
        Lb = f.L([W.A17, W.A18, W.A19, W.A21])     # 피 = 층 램프 17~21 (런타임 스왑)
        Lp = f.L([W.A17, W.A18])
        Lg = f.L(W.R_HOT)
        c = (t.ox, t.oy)
        Lp.disc(c[0], c[1] + 30, 22 + 2 * (i % 2), 6, v=0.7, edge=0.6)
        for j, x in enumerate((-14, 2, 16)):
            ph = FK.frac(i / 4 + j * 0.33)
            y = c[1] - 32 + ph * 56
            Lb.stroke([(c[0] + x, y - 8 - 6 * ph), (c[0] + x, y)], 2.4, prof=FK.tp_head(0.7), v=0.85)
            Lb.stamp(c[0] + x, y + 1, 2.2, 0.95, soft=0.4)
        if i == 0:
            P.glint(Lg, c[0] + 2, c[1] - 36, 7, v=0.85)
    fr = C.frames(old, draw)
    return fr, C.base_extra(old, "dagger", {0}), dict(swap="floor-accent 17~21 (피, 구 bleed 와 같이 층 램프 스왑) · 글린트만 고정")


SHEETS = {"dagger_combo1": lambda: combo("dagger_combo1"), "dagger_combo2": lambda: combo("dagger_combo2"),
          "dagger_combo3": lambda: combo("dagger_combo3"),
          "dagger_slash": dagger_slash, "twin": twin, "dance": dance, "gale": gale, "assassin": assassin,
          "afterimage": afterimage, "shadowstep_ghost": shadowstep_ghost, "bleed": bleed}
for _n in (1, 2, 3):
    for _h in (1, 2, 3):
        SHEETS["dagger_combo%d_heat%d" % (_n, _h)] = _heat("dagger_combo%d_heat%d" % (_n, _h))
