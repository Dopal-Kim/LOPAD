"""휘두름 궤적(칼·대검·단검 베기) — 시안 공격 컷의 분위기: 혼불이 남기는 초승달 궤적이 곧 재 장막·불티로 부서진다.

style
  katana : 재 칼날 · 날선 호박 한 줄 → 가는 초승달. 바깥 1px 백열 날선 + 호박 몸 + 안쪽 회색 재 장막(조각으로 부서짐) + 끝에서 튀는 불티
  gs     : 녹슨 양손검 · 이 빠진 홈 혼불 → 넓고 묵직한 녹·흙 띠 + 바깥 호박 날선 + 띠 안의 홈 혼불 한 줄(이 빠진 자리마다 끊김)
           + 꼬리 쪽 흙먼지 구름 + 홈에서 떨어지는 불씨
  dagger : 재 송곳니 · 백열 끝 → 짧고 가는 호 + 바늘 끝 백열 + 공중에 남는 호박 금(균열) → 재로 떨어짐
빛 규칙(Q27·Q30): 판정 프레임(bright)에서만 백열(X0/X1)·A26 이 나온다. 나머지는 A25 이하.
"""
import math

import wkit as W
from wkit import FK


def frame_states(F, impact, bright):
    """→ [(kind, k)] kind = pre / hit / after, k = 진행(0..1)."""
    out = []
    after = [i for i in range(F) if i > impact]
    for i in range(F):
        if i < impact:
            out.append(("pre", (i + 1) / (impact + 1)))
        elif i == impact or i in bright:
            out.append(("hit", 0.0 if i == impact else 0.25))
        else:
            n = len(after)
            out.append(("after", (after.index(i) + 1) / n))
    return out


STYLE = {
    "katana": dict(edge=W.R_EDGE, veil=W.R_ASHG, prof=(0.7, 0.62), veil_k=2.4, ember_n=10, flake_n=12),
    "gs": dict(edge=W.R_EDGE, veil=W.R_RUST, prof=(0.55, 0.55), veil_k=0.0, ember_n=14, flake_n=9),
    "dagger": dict(edge=W.R_EDGE, veil=W.R_ASHG, prof=(0.8, 0.66), veil_k=0.6, ember_n=6, flake_n=8),
    "gs_dark": dict(edge=W.R_EDGE, veil=W.R_RUST, prof=(0.5, 0.5), veil_k=0.0, ember_n=10, flake_n=9),
}


def swing_frames(style, size, origin, R, a0d, a1d, F, impact, bright=(), wmax=10.0, echoes=(), seed=1, rays=0,
                 cracks=False, dust=0, sliver=0.3, tail_dash=True, long_glow=False, gaps=(), wscale=1.0):
    """→ {dir: [RGBA]}. echoes = [(dR, delay, wk)] 겹 궤적(반지름 차, 프레임 지연, 폭 비율)."""
    st = STYLE[style]
    a0, a1 = math.radians(a0d), math.radians(a1d)
    sgn = 1 if a1 > a0 else -1
    states = frame_states(F, impact, set(bright))
    out = {}
    for d in W.DIRS:
        t = W.T(d, *origin)
        deb = W.Debris(seed * 97 + 3)
        rng = deb.rng
        # ---- 파편 생성(로컬): 판정 프레임에 띠를 따라
        # 재 조각: 판정 뒤 프레임마다 '부서지는 자리'(꼬리가 물러난 구간)에서 떨어져 나간다
        prev_tail = 0.0
        for i2, (kind2, k2) in enumerate(states):
            if kind2 != "after":
                continue
            tl = min(0.92, 0.12 + 0.8 * k2 ** 0.85)
            for j in range(st["flake_n"]):
                s = rng.uniform(prev_tail, tl + 0.06)
                a = a0 + (a1 - a0) * s
                rr = R - wmax * rng.uniform(0.3, 1.5)
                tang = (-math.sin(a) * sgn, math.cos(a) * sgn)
                sp = rng.uniform(1.0, 3.5)
                out_v = rng.uniform(-0.8, 1.6)
                deb.spawn("flake", (math.cos(a) * rr, math.sin(a) * rr),
                          (tang[0] * sp * 0.6 + math.cos(a) * out_v, tang[1] * sp * 0.6 + math.sin(a) * out_v),
                          i2, F - i2, size=rng.uniform(1.3, 3.4) * (1.35 if style == "gs" else 1.0), v=rng.uniform(0.45, 1.0), g=1.8)
            prev_tail = tl
        for j in range(st["ember_n"]):
            s = rng.uniform(0.55, 1.0) if style != "gs" else rng.uniform(0.2, 1.0)
            a = a0 + (a1 - a0) * s
            rr = R - rng.uniform(0, wmax * 0.6)
            tang = (-math.sin(a) * sgn, math.cos(a) * sgn)
            sp = rng.uniform(5.0, 11.0) * (R / 130.0) ** 0.5
            spread = rng.uniform(-0.35, 0.6)
            vx = tang[0] * sp + math.cos(a) * sp * spread
            vy = tang[1] * sp + math.sin(a) * sp * spread
            deb.spawn("ember", (math.cos(a) * rr, math.sin(a) * rr), (vx, vy), impact + (j % 2), rng.choice((2, 2, 3)),
                      size=rng.uniform(3.0, 7.0), v=rng.uniform(0.6, 1.0), g=1.2)
        for j in range(dust):
            s = rng.uniform(0.0, 0.6)
            a = a0 + (a1 - a0) * s
            rr = R - wmax * rng.uniform(0.3, 1.1)
            deb.spawn("dust", (math.cos(a) * rr, math.sin(a) * rr), (math.cos(a) * 1.5, math.sin(a) * 1.5),
                      impact + 1 + (j % 2), min(3, F - impact - 2), size=rng.uniform(11, 16) * (R / 200.0) ** 0.5,
                      v=rng.uniform(0.6, 0.95), g=-0.8)
        frames = []
        for i, (kind, k) in enumerate(states):
            fr = W.Frame(size[0], size[1], t)
            Ldust = fr.L(W.R_DUST)
            Lveil = fr.L(st["veil"])
            Lbody = fr.L(W.R_RUST if style == "gs" else [W.B0, W.B1, W.B2, W.B3, W.A18]) if style.startswith("gs") else None
            Ledge = fr.L(st["edge"])
            Lgroove = fr.L(W.R_EDGE) if style.startswith("gs") else None
            Lflake = fr.L(W.R_ASHG if not style.startswith("gs") else W.R_ASHB)
            Lember = fr.L(W.R_EMBER)
            if kind == "pre":
                _pre(Ledge, t, R, a0, a1, k * sliver, style)
            else:
                age = 0.0 if kind == "hit" else k
                hot = kind == "hit"
                # 겹 궤적(지연)
                layers = [(0.0, 0, 1.0)] + list(echoes)
                for e in layers:
                    dR, delay, wk = e[:3]
                    flip = len(e) > 3 and e[3]
                    if i - impact < delay:
                        continue
                    ea = age if delay == 0 else min(1.0, max(0.0, (i - impact - delay) / max(1, F - 1 - impact)))
                    ehot = hot and delay == 0 or (delay > 0 and i - impact == delay and long_glow)
                    b0, b1 = (a1, a0) if flip else (a0, a1)
                    _band(style, fr, Ldust, Lveil, Lbody, Ledge, Lgroove, t, R + dR, b0, b1, wmax * wk, ea, ehot, st,
                          seed + int(dR), last=(i == F - 1), tail_dash=tail_dash, gaps=gaps if delay == 0 else ())
                if rays and i == impact + 1:
                    _rays(Ledge, t, R, a1, sgn, rays, rng)
                if cracks and i >= impact:
                    _ground_cracks(Ledge, Lflake, t, R, i - impact, F - 1 - impact, seed)
            deb.draw(fr, t, {"ember": Lember, "flake": Lflake, "dust": Ldust}, i)
            frames.append(fr.render())
        out[d] = frames
    return out


def _pre(L, t, R, a0, a1, frac, style):
    """예비 프레임: 판정 40ms 전, 시작 쪽 가는 1px 선(바늘 끝)."""
    b = a0 + (a1 - a0) * max(0.08, frac)
    pts = W.arc_pts(R - 2, a0, b)
    L.stroke(t.pts(pts), 1.1 if style != "gs" else 1.5, prof=FK.tp_both(0.8, 0.75), v=0.62,
             vprof=lambda s: 0.6 + 0.4 * s)


def _band(style, fr, Ldust, Lveil, Lbody, Ledge, Lgroove, t, R, a0, a1, wmax, age, hot, st, seed, last=False, tail_dash=True, gaps=()):
    W_, H_ = fr.w, fr.h
    pw, pk = st["prof"]
    base = FK.tp_both(pw, pk)
    tail = 0.0 if hot else min(0.92, 0.12 + 0.8 * age ** 0.85)
    shrink = 1.0 if hot else max(0.25, 1.0 - 0.62 * age)
    heat = 1.0 if hot else max(0.3, 0.80 - 0.5 * age)
    if last and tail_dash:
        # 마지막: 끊긴 1px 잔광 + 조각(파편 시스템)
        pts = W.arc_pts(R - wmax * 0.15, a0 + (a1 - a0) * 0.45, a1)
        Ledge.stroke(t.pts(pts), 0.8, prof=FK.tp_both(0.8, 0.7), v=0.42, dash=(9.0, 0.55, 0.2 + seed * 0.13))
        return

    def prof(s):
        if s < tail:
            return 0.0
        u = (s - tail) / max(1e-6, 1 - tail)
        return base(u) * shrink

    if style.startswith("gs"):
        notch = 7 if style == "gs" else 0          # gs_dark(중압) = 홈 혼불이 끊기지 않는 녹은 줄

        def cb(x, y, s, d, w):
            for g in gaps:                          # 파쇄: 비스듬한 틈으로 끊긴 '깨진 띠'
                if abs(s - g - 0.025 * (d - 0.5)) < 0.012 + 0.006 * W.h2(int(d * 5), int(g * 100), 1):
                    return
            q0 = FK.frac(s * notch + 0.3) if notch else 0.5
            if notch and 0.15 < s < 0.95 and min(q0, 1 - q0) < 0.035 and d < 0.28 - min(q0, 1 - q0) * 5:
                return                                  # 이 빠진 자리: 날선에 작은 V 홈
            if d < 0.09:
                Ledge.put(x, y, heat * (0.95 if hot else 0.75) * (0.7 + 0.3 * s) if hot else min(0.62, heat * 0.8))
            elif d <= 1.0:
                n = W.h2(x // 3, y // 3, seed)
                # 날선 쪽 35% = 녹빛·혼불(A19/A21), 안쪽 = 흙·녹(B2/B3/A18) 얼룩
                lit = max(0.0, 1 - d / 0.4)
                Lbody.put(x, y, (0.22 + 0.42 * (1 - d) + 0.38 * lit + 0.16 * (n - 0.5)) * (0.65 + 0.35 * s) * (1.0 if hot else 0.85))
                # 홈 혼불: 깊이 0.38 근처 한 줄, 이 빠진 자리(notch) 마다 끊김
                g = abs(d - 0.38) * w
                q = FK.frac(s * notch + 0.3) if notch else 0.5
                if g < (1.3 if hot else 0.9) and (0.12 < q < 0.92 or not notch):
                    Lgroove.put(x, y, heat * (1 - g / 1.6) * (0.65 + 0.35 * s) if hot else min(0.62, heat * 0.8 * (1 - g / 1.6)))
            elif not hot:
                pass
        W.crescent(W_, H_, t, R, a0, a1, wmax, prof, cb)
    else:
        veil_k = st["veil_k"]
        arclen = abs(a1 - a0) * R

        def cb(x, y, s, d, w):
            if d <= 1.0:
                v = heat * (1 - 0.72 * d ** 0.75) * (0.62 + 0.38 * s)
                if not hot:
                    v = min(v, 0.62)                  # 판정 밖에서는 A25 이하(Q27 · 백열 없음)
                Ledge.put(x, y, v)
            else:
                # 안쪽 재 장막: 3px 덩이로 부서짐, 나이 들수록 더 많이 빠짐
                n = W.h2(int(s * arclen / 6.0), int((d - 1.0) * w / 2.0), seed)   # 호를 따라 길쭉한 재 결
                keep = 0.12 + 0.6 * age + 0.5 * ((d - 1.0) / veil_k) ** 1.5
                if n > keep:
                    Lveil.put(x, y, 0.3 + 0.62 * (1 - (d - 1.0) / veil_k) ** 1.5 * (0.5 + 0.5 * s))
        W.crescent(W_, H_, t, R, a0, a1, wmax, prof, cb, inner_pad=veil_k)


def _rays(L, t, R, a1, sgn, n, rng):
    """판정 다음 프레임: 휘두름 끝에서 접선으로 새는 바늘 광선."""
    for j in range(n):
        a = a1 - sgn * (0.05 + 0.12 * j)
        p = (math.cos(a) * (R - 3), math.sin(a) * (R - 3))
        tang = (-math.sin(a) * sgn, math.cos(a) * sgn)
        ang = math.atan2(tang[1], tang[0]) + rng.uniform(-0.35, 0.35) + (j - n / 2) * 0.28
        ln = rng.uniform(14, 26)
        q = (p[0] + math.cos(ang) * ln, p[1] + math.sin(ang) * ln)
        L.stroke(t.pts([p, q]), 1.2, prof=FK.tp_tail(0.8), v=0.8)


def _ground_cracks(Ledge, Lflake, t, R, age, n, seed):
    """대검 3타: 앞-아래 바닥 균열(혼불이 스민 금) — 화면 좌표로 그려 방향과 무관하게 바닥에 놓인다."""
    import random
    rng = random.Random(seed * 7 + 1)
    base = t((R * 0.72, R * 0.18))
    k = age / max(1, n)
    for j in range(4):
        ang = math.radians(-160 + j * 45 + rng.uniform(-12, 12)) if j < 4 else 0
        ln = R * rng.uniform(0.18, 0.3) * min(1.0, 0.5 + k * 1.2)
        p1 = (base[0] + math.cos(ang) * ln, base[1] + math.sin(ang) * ln * 0.5)
        pts = W.jag(rng, base, p1, n=5, amp=2.2)
        Ledge.stroke(pts, 1.0 if k < 0.6 else 0.7, prof=FK.tp_tail(0.7), v=0.8 * (1 - 0.6 * k),
                     dash=(7.0, 0.7, 0.0) if k > 0.7 else None)
