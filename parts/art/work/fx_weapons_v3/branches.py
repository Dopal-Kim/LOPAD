"""1단 갈래 기본 공격 이펙트 v3.1 (55라운드 Q9 '1단 = 궤적 모양이 갈래별로 확 달라짐' · 51라운드 §4 · 53라운드 Q61~Q68).

fx/<weapon>_combo<n>_<branch>: 크기·피벗·프레임·ms·anchor·spawn·판정 필드 = 기본 시트(구 갈래 JSON 복사 → ×4). 판정 불변.
모양(색은 재·호박 램프만, 백열은 판정 프레임만):
  칼  iai    거합 = 빛살 묶음 일섬: 칼끝 반경~판정 가장자리를 가는 호 빛살 5~8줄이 메우고(바깥 줄 = 백열 심), 휘두름 끝에서 접선으로 곧게 뻗는 긴 일섬 + 잔광이 오래 남아 점선으로 끊김
       batto  발도 = 칼집에서 뿜는 반달: 바깥 호 + 곧은 현(弦)으로 닫힌 반달(D) 면을 칼집 입(허리 뒤)에서 뿜어 나온 방사 결이 채움, 칼집 입 섬광 → 반달이 바깥으로 깎이며 재로 흩어짐
  대검 crush  파쇄 = 곤봉형 짧고 두꺼운 호 + 바닥 균열: 시작은 실처럼 가늘고 끝 40% 가 두껍게 뭉친 깨진 녹 띠(틈 3곳) + 정면 바닥에 혼불 균열 별 + 튀는 돌덩이(균열은 마지막까지 남음)
       weight 중압 = 눌린 넓은 부채: 몸 앞부터 판정 가장자리까지 꽉 찬 어두운 흙 부채(바깥 테는 꺾인 다각 테), 안에 압력 물결 능선이 바깥으로 밀려나고 테 아래로 흙먼지가 가라앉음
  단검 twin   쌍격 = 교차 X 두 줄: 두 바늘이 앞 60% 지점에서 X 로 교차(3타는 가운데서 넓게), 교차점 백열 십자 섬광 → 교차 흉터가 식으며 남음
       gale   질풍 = 회오리 꼬리: 가는 본 바늘을 두 가닥 나선이 감고(앞면 호박 · 뒷면 재), 몸 뒤에 옆으로 누운 회오리 고리 3겹(원뿔) → 나선이 앞으로 풀리며 끊김
활 rapid/snipe(defs_bow): 속사 = 짧은 화살 + 뒤로 끊긴 유령 촉(>) 2개·속도 토막 / 저격 = 나선 실 감긴 긴 화살 + 꼬리 = 곧은 심 + 음속 고리(lv 마다 1·2·3개).
2단은 branches2.py (이 모양 위에 입자·빛·잔연 + 큰 틀).
"""
import math

import common as C
import defs_dagger as DG
import parts as P
import swing
import wkit as W
from wkit import FK

PAD2 = 32                                         # 2단 시트 사방 여백(도트) — 틀 +64, 피벗 +32


def geo(name, pad=0):
    """→ (구 JSON, 프레임 크기, 피벗, 판정 원점) — pad 만큼 사방으로 넓힌 틀."""
    old = W.old_json(name)
    fw, fh, px, py = W.geom(old)
    piv = (px + pad, py + pad)
    return old, (fw + 2 * pad, fh + 2 * pad), piv, (piv[0], piv[1] - W.HIT_UP)


def arcinfo(old):
    R = old["hitRadiusPx"] * W.K4
    a0, a1 = math.radians(old["arcFromDeg"]), math.radians(old["arcToDeg"])
    return R, a0, a1, (1 if a1 > a0 else -1)


def states(old):
    return swing.frame_states(old["frames"], old["impactFrame"], C.bright_of(old))


def over(*sets):
    """프레임 묶음을 아래 → 위 순서로 겹침."""
    out = {}
    for d in sets[0]:
        lst = []
        for i in range(len(sets[0][d])):
            im = sets[0][d][i].copy()
            for s in sets[1:]:
                im.alpha_composite(s[d][i])
            lst.append(im)
        out[d] = lst
    return out


def raster(f, t, rmax, cb):
    """원점 둘레 rmax 안의 픽셀마다 cb(x, y, lx, ly) (로컬 좌표)."""
    ox, oy = t((0, 0))
    for y in range(max(0, int(oy - rmax - 2)), min(f.h, int(oy + rmax + 3))):
        for x in range(max(0, int(ox - rmax - 2)), min(f.w, int(ox + rmax + 3))):
            lx, ly = t.inv(x + 0.5, y + 0.5)
            cb(x, y, lx, ly)


def sweep_s(a, a0, a1):
    """로컬 각 a → 휘두름 진행 s(0..1 밖이면 None)."""
    span = a1 - a0
    for k in (0, 1, -1):
        s = (a + k * 2 * math.pi - a0) / span
        if 0 <= s <= 1:
            return s
    return None


def extra(old, weapon, branch, design):
    ex = C.base_extra(old, weapon, C.bright_of(old))
    ex["branchDesignV3"] = design
    ex["tierNote"] = "55라운드 Q9: 1단 = 궤적 모양이 갈래별로 다름(색은 재·호박), 2단 = 이 모양 + 입자·빛·잔연 + 큰 틀(secondarySheets)"
    return ex


def design_of(key):
    for l in __doc__.split("\n"):
        if (" %s " % key) in l:
            return l.strip()
    return key


# ================================================================== 칼 iai 거합 — 빛살 묶음 일섬
IAI_LINES = {1: 6, 2: 5, 3: 8}
IAI_OS = {1: 52, 2: 44, 3: 70}


def iai_main(old, n, fill, lines_extra=0, os_k=1.0, life_k=1.0):
    R, a0, a1, sgn = arcinfo(old)
    st = states(old)
    nl = IAI_LINES[n] + lines_extra
    radii = [R - 1 - (R - 1 - fill) * (j / (nl - 1)) ** 1.2 for j in range(nl)]
    span = a1 - a0
    OS = IAI_OS[n] * os_k

    def draw(f, t, d, i, F):
        kind, k = st[i]
        Lsh = f.L([W.A18, W.A19, W.A21, W.A23])
        Lln = f.L(W.R_EDGE)
        Lin = f.L(W.R_EDGE_SOFT)
        Lfl = f.L(W.R_ASHG)
        if kind == "pre":
            Lln.stroke(t.pts(W.arc_pts(R - 1, a0, a0 + span * 0.22)), 0.8, prof=FK.tp_both(0.8, 0.85), v=0.6)
            Lin.stroke(t.pts(W.arc_pts(R - 7, a0, a0 + span * 0.12)), 0.5, prof=FK.tp_both(0.8, 0.85), v=0.8)
            return
        hot = kind == "hit"
        age = 0.0 if hot else min(1.0, k / life_k)
        # 얇은 호박 날(빛살 바탕): 바깥 가장자리에서 안쪽 6도트, 가운데 두껍게
        if age < 0.75:
            s_cut = 0.0 if hot else 0.7 * age ** 1.1

            def cb(x, y, s, dd, w):
                if s < s_cut:
                    return
                Lsh.put(x, y, (0.95 - 0.6 * dd) * (0.55 + 0.45 * s) * (1.0 if hot else 0.8 - 0.4 * age))
            W.crescent(f.w, f.h, t, R - 1, a0, a1, 6.0, FK.tp_both(0.6, 0.72), cb)
        for j, r in enumerate(radii):
            life = 1.0 - 0.08 * j
            if age > life:
                continue
            s0 = 0.03 + 0.055 * j + 0.05 * W.h2(j, n, 7)
            s1 = 1.0 - 0.02 * j
            if not hot:
                s0 = s0 + (s1 - s0) * 0.62 * (age / life) ** 1.2
            pts = W.arc_pts(r, a0 + span * s0, a0 + span * s1)
            if j == 0:
                L, w, v = Lln, 1.35, (1.0 if hot else 0.62 - 0.24 * age)
            elif j < 3:
                L, w, v = Lln, 0.8, (0.74 - 0.05 * j if hot else 0.56 - 0.26 * age)
            else:
                L, w, v = Lin, 0.6, (0.98 - 0.07 * (j - 3) if hot else 0.82 - 0.45 * age)
            dash = None if (hot or age < 0.3) else (14 + 4 * j, max(0.3, 0.92 - 0.7 * age), 0.13 * j)
            L.stroke(t.pts(pts), w, prof=FK.tp_both(0.6, 0.8), v=v, vprof=lambda s: 0.55 + 0.45 * s, dash=dash)
        # 휘두름 끝에서 접선으로 곧게 뻗는 일섬(가장 오래 남음)
        for j, (rr, kk) in enumerate(((R - 1, 1.0), (radii[1], 0.55))):
            p = (math.cos(a1) * rr, math.sin(a1) * rr)
            tg = (-math.sin(a1) * sgn, math.cos(a1) * sgn)
            ln = OS * kk * (1.0 if hot else 1.0 - 0.35 * age)
            if not hot and age > 0.9 and j:
                continue
            q = (p[0] + tg[0] * ln, p[1] + tg[1] * ln)
            Lln.stroke(t.pts([p, q]), (1.25 if j == 0 else 0.7), prof=FK.tp_tail(0.7),
                       v=(0.97 if hot else 0.6 - 0.2 * age) * (1 if j == 0 else 0.8),
                       dash=None if age < 0.6 else (10, 0.6, 0.2))
        if hot:                                    # 시작점 뒤로 짧은 바늘 빛
            p = (math.cos(a0) * (R - 1), math.sin(a0) * (R - 1))
            tg = (math.sin(a0) * sgn, -math.cos(a0) * sgn)
            Lln.stroke(t.pts([p, (p[0] + tg[0] * 14, p[1] + tg[1] * 14)]), 0.7, prof=FK.tp_tail(0.8), v=0.7)
        else:                                      # 빛살에서 떨어지는 재 비늘
            rng = P.rng(4100 + 10 * n + i)
            for m in range(int(8 + 6 * age)):
                s = rng.uniform(0.15 + 0.5 * age, 1.0)
                a = a0 + span * s
                rr = rng.choice(radii[:4])
                q = t((math.cos(a) * rr, math.sin(a) * rr))
                W.flake(Lfl, q[0] + rng.uniform(-3, 3), q[1] + 10 * age * rng.uniform(0.5, 1.5), rng.uniform(1.0, 2.0),
                        rng.uniform(0, 6), v=rng.uniform(0.5, 0.95))
    return draw


def iai(n, pad=0):
    name = "katana_combo%d_iai" % n
    old, size, piv, o = geo(name, pad)
    R, a0, a1, sgn = arcinfo(old)
    fill, memo = C.trail_fill("katana_combo%d" % n, R)
    fr = C.frames(old, iai_main(old, n, fill), size=size, origin=o)
    return fr, dict(extra(old, "katana", "iai", design_of("iai")), trailFill=memo)


# ================================================================== 칼 batto 발도 — 칼집에서 뿜는 반달
HIP = (-8.0, 22.0)                                # 칼집 입(로컬, 몸 중심 기준 뒤·아래)


def batto_geom(old):
    R, a0, a1, sgn = arcinfo(old)
    mid = (a0 + a1) / 2
    half = abs(a1 - a0) / 2
    c = max(R * math.cos(half), 34.0)            # 몸 앞에서 시작(주인공을 가리지 않게)
    return R, a0, a1, sgn, mid, c


def batto_main(old, n, keep=1.0):
    R, a0, a1, sgn, mid, c = batto_geom(old)
    st = states(old)
    cm, sm = math.cos(mid), math.sin(mid)
    seed = 520 + n

    def draw(f, t, d, i, F):
        kind, k = st[i]
        Lfill = f.L([W.A17, W.A18, W.A19, W.A21, W.A23])
        Lash = f.L(W.R_ASHG)
        Lrim = f.L(W.R_EDGE)
        Lhot = f.L(W.R_HOT)
        Lfl = f.L(W.R_ASHG)
        hip = t(HIP)
        if kind == "pre":                         # 칼집 입이 달아오름(코이구치 한 줄) + 현 쪽으로 새는 실 3
            Lrim.stroke(t.pts([(HIP[0] - 6, HIP[1]), (HIP[0] + 8, HIP[1] - 2)]), 1.2, prof=FK.tp_both(0.7, 0.6), v=0.6)
            for j in (-1, 0, 1):
                a = mid + j * 0.35
                q = (HIP[0] + math.cos(a) * (c + 10), HIP[1] + math.sin(a) * (c + 10) - 10)
                Lfill.stroke(t.pts([HIP, q]), 0.5, prof=FK.tp_head(0.7), v=0.7)
            return
        hot = kind == "hit"
        age = 0.0 if hot else k
        cut = c + (R - c) * 0.72 * age ** 0.9         # 반달 면이 현 쪽부터 깎여 바깥으로 물러남

        def cb(x, y, lx, ly):
            r = math.hypot(lx, ly)
            if r > R + 0.5:
                return
            pr = lx * cm + ly * sm
            if pr < cut:
                return
            s = sweep_s(math.atan2(ly, lx), a0, a1)
            s = 0.5 if s is None else s
            ramp = 0.6 + 0.4 * s
            if R - r < 2.2:                            # 바깥 호 = 날선
                Lrim.put(x, y, (1.0 if hot else 0.6 - 0.22 * age) * (0.75 + 0.25 * s))
                return
            if not hot and pr - cut < 1.6 and age < 0.95:
                Lrim.put(x, y, 0.42 - 0.2 * age)       # 깎이는 앞 가장자리(식은 호박)
                return
            if hot and pr - c < 1.8:                   # 곧은 현 = 두 번째 날선
                Lrim.put(x, y, 0.72 * ramp)
                return
            # 칼집 입에서 뿜어 나온 방사 결: 긴 빛줄(호박) + 그 사이 어두운 호박 바탕(면이 꽉 찬 반달)
            hx, hy = lx - HIP[0], ly - HIP[1]
            ah = math.atan2(hy, hx)
            dh = math.hypot(hx, hy)
            lane = int((ah + math.pi) / 0.05)
            ph = W.h2(lane, 0, seed)
            ln = 46 + 50 * W.h2(lane, 1, seed)
            duty = (0.8 if hot else 0.7 - 0.35 * age) * (0.7 + 0.45 * W.h2(lane, 2, seed))
            u = FK.frac(dh / ln - ph - (0.0 if hot else 0.5 * age))
            q = (r - cut) / max(1.0, R - cut)          # 0 현 → 1 호
            lit = W.h2(lane, 3, seed) > 0.42
            if u < duty and lit:
                v = (0.42 + 0.56 * q ** 1.2) * ramp * (1.0 if hot else 0.88)
                Lfill.put(x, y, v)
            elif q > 0.08 or hot:
                if not hot and W.h2(x // 2, y // 2, seed + i) < 0.25 + 0.5 * age:
                    return                                  # 식으며 바탕이 성겨짐
                Lfill.put(x, y, 0.1 + 0.16 * q)
        raster(f, t, R + 2, cb)
        if hot:                                    # 칼집 입 섬광 + 현까지 뿜는 굵은 빛줄 5
            P.glint(Lhot, hip[0], hip[1], 12, v=1.0, diag=0.5)
            for j in range(5):
                a = mid + (j - 2) * 0.28
                q = (HIP[0] + math.cos(a) * (c + 6), HIP[1] + math.sin(a) * (c + 6))
                Lrim.stroke(t.pts([HIP, q]), 1.1 if j == 2 else 0.7, prof=FK.tp_head(0.6), v=0.8 if j == 2 else 0.66)
        else:
            rng = P.rng(seed * 7 + i)
            for m in range(int(10 + 10 * age)):           # 깎인 자리에서 떨어지는 재 비늘
                a = mid + rng.uniform(-1, 1) * abs(a1 - a0) / 2
                rr = rng.uniform(cut - 6, min(R, cut + 20))
                q = t((math.cos(a) * rr, math.sin(a) * rr))
                W.flake(Lfl, q[0], q[1] + 8 * age * rng.uniform(0.6, 1.6), rng.uniform(1.2, 2.6), rng.uniform(0, 6),
                        v=rng.uniform(0.5, 1.0))
    return draw


def batto(n, pad=0):
    name = "katana_combo%d_batto" % n
    old, size, piv, o = geo(name, pad)
    fr = C.frames(old, batto_main(old, n), size=size, origin=o)
    R, a0, a1, sgn, mid, c = batto_geom(old)
    ex = extra(old, "katana", "batto", design_of("batto"))
    ex["halfMoon"] = {"outerRadiusDots": R, "chordDots": round(c, 1), "sheathMouthDots": list(HIP),
                      "note": "그림 메모 — 반달(D) = 판정 원 안의 현 바깥쪽. 판정은 기본 호(hitRadiusPx·arc) 그대로"}
    return fr, ex


# ================================================================== 대검 crush 파쇄 — 곤봉형 짧고 두꺼운 호 + 바닥 균열
GW = {1: 30, 2: 27, 3: 36}
CRUSH_GAPS = (0.6, 0.74, 0.87)


def club(u):
    if u < 0.86:
        return (u / 0.86) ** 1.9
    return max(0.0, (1 - u) / 0.14) ** 0.3


def crack_pt(R):
    """정면 바닥(발 높이) — 로컬 정면 0.62R 지점에서 화면 아래로 판정 원점 높이만큼."""
    return (R * 0.62, 0.0)


def crush_cracks(old, n, scale=1.0, persist=1.0, seed=0):
    R, a0, a1, sgn = arcinfo(old)
    st = states(old)
    rng0 = P.rng(630 + n + seed)
    angs = [rng0.uniform(-0.3, 0.3) + 2 * math.pi * m / 7 for m in range(7)]

    def draw(f, t, d, i, F):
        kind, k = st[i]
        if kind == "pre":
            return
        hot = kind == "hit"
        age = 0.0 if hot else k
        Lc = f.L(W.R_EDGE)
        Ld = f.L(W.R_DUST)
        Lr = f.L(W.R_ASHB)
        c = t(crack_pt(R))
        c = (c[0], c[1] + W.HIT_UP)
        grow = min(1.0, 0.55 + 0.9 * (i - old["impactFrame"]) / 2.0)
        r1 = (70 + 18 * (n == 3)) * scale * grow
        rng = P.rng(640 + n + seed)
        v = 0.98 if hot else 0.6 - 0.2 * age / persist
        P.radial_cracks(Lc, c, rng, len(angs), 5, r1, v=v, w=1.7 if age < 0.5 else 1.1, seed_angles=angs,
                        dash=None if age < 0.75 else (6, 0.65, 0.0))
        if hot or age < 0.5:                        # 균열 가운데 패인 자리 + 흙 고리
            P.ground_ring(Ld, c, 18 * scale * grow, 3.0, v=0.85 - 0.3 * age)
        rngd = P.rng(650 + n + seed)
        for m in range(int(7 * scale)):           # 튀어 오르는 돌덩이(화면 위로 솟았다 떨어짐)
            a = rngd.uniform(0, 2 * math.pi)
            sp = rngd.uniform(14, 30) * scale
            tt = (i - old["impactFrame"]) + 0.6
            x = c[0] + math.cos(a) * sp * tt * 0.6
            y = c[1] + math.sin(a) * sp * tt * 0.3 - 22 * tt + 9 * tt * tt
            if age < 0.95:
                W.flake(Lr, x, y, rngd.uniform(2.4, 4.2) * (1 - 0.3 * age), rngd.uniform(0, 6) + tt, v=0.95 - 0.3 * age)
    return draw


def crush(n, pad=0):
    name = "greatsword_combo%d_crush" % n
    old, size, piv, o = geo(name, pad)
    R, a0, a1, sgn = arcinfo(old)
    fill, memo = C.trail_fill("greatsword_combo%d" % n, R)
    fr = swing.swing_frames("gs", size, o, R, old["arcFromDeg"], old["arcToDeg"], old["frames"], old["impactFrame"],
                            bright=C.bright_of(old), wmax=GW[n] * 1.15, seed=600 + n, dust=3, gaps=CRUSH_GAPS,
                            fill_to=fill, prof_fn=club)
    top = C.frames(old, crush_cracks(old, n), size=size, origin=o)
    ex = dict(extra(old, "greatsword", "crush", design_of("crush")), trailFill=memo)
    ex["floorCrack"] = {"atLocalDots": [round(R * 0.62, 1), 0], "note": "그림 메모 — 정면 0.62R 바닥(발 높이)에 균열 별. 판정 아님"}
    return over(fr, top), ex


# ================================================================== 대검 weight 중압 — 눌린 넓은 부채
FACETS = {1: 5, 2: 5, 3: 7}
R_IN = 62.0                                       # 몸·팔을 가리지 않게


def fan_poly_r(a, a0, a1, R, nf):
    """꺾인 다각 테: 각 a 에서 테까지 반지름."""
    span = a1 - a0
    s = sweep_s(a, a0, a1)
    if s is None:
        return None, None
    m = min(nf - 1, int(s * nf))
    am = a0 + span * (m + 0.5) / nf
    half = abs(span) / nf / 2
    return R * math.cos(half) / max(0.2, math.cos(a - am)), s


def weight_main(old, n, rim_k=1.0, ridge_k=1.0):
    R, a0, a1, sgn = arcinfo(old)
    st = states(old)
    nf = FACETS[n]
    seed = 720 + n
    b0 = a0 + (a1 - a0) * 0.02
    b1 = a1 - (a1 - a0) * 0.02

    def draw(f, t, d, i, F):
        kind, k = st[i]
        Lb = f.L([W.B0, W.B1, W.B2, W.B3])
        Lrg = f.L(W.R_RUST)
        Lrim = f.L(W.R_EDGE)
        if kind == "pre":
            Lrim.stroke(t.pts(W.arc_pts(R - 3, a0, a0 + (a1 - a0) * 0.18)), 1.5, prof=FK.tp_both(0.8, 0.75), v=0.6)
            return
        hot = kind == "hit"
        age = 0.0 if hot else k
        rin = R_IN + (R - R_IN) * 0.78 * age ** 0.85     # 안쪽부터 비워짐(압력이 바깥으로 밀려남)
        push = 22 * age                                  # 능선이 바깥으로 이동
        rimw = 11.0 * rim_k

        def cb(x, y, lx, ly):
            r = math.hypot(lx, ly)
            if r < rin or r > R + 1:
                return
            rp, s = fan_poly_r(math.atan2(ly, lx), b0, b1, R, nf)
            if rp is None or r > rp:
                return
            ramp = 0.62 + 0.38 * s
            e = rp - r                                     # 테까지 거리
            if e < 1.6:
                Lrim.put(x, y, (0.98 if hot else 0.6 - 0.25 * age) * (0.7 + 0.3 * s))
                return
            if e < rimw:
                Lrg.put(x, y, (1.0 - 0.45 * (e / rimw) ** 1.5) * ramp * (1.0 if hot else 0.85 - 0.3 * age))
                return
            # 압력 능선(동심 물결) — 바깥으로 밀려남
            ph = FK.frac((r - push) / (25.0 * ridge_k))
            if ph < 0.15 and r > rin + 3:
                Lrg.put(x, y, (0.45 + 0.4 * (r / R)) * ramp * (1.0 if hot else 0.85 - 0.3 * age))
                return
            nz = W.h2(x // 2, y // 3, seed)
            if not hot and nz < 0.55 * age + 0.25 * (1 - r / R):
                return                                      # 식으며 안쪽부터 성겨짐
            Lb.put(x, y, (0.18 + 0.72 * (r / R) ** 1.4 + 0.1 * (nz - 0.5)) * (0.8 + 0.2 * s))
        raster(f, t, R + 2, cb)
        Ld = f.L(W.R_DUST)
        if not hot:                                      # 테 아래로 가라앉는 흙먼지(화면 아래로)
            rng = P.rng(seed * 3 + i)
            for m in range(5):
                s = rng.uniform(0.25, 1.0)
                a = b0 + (b1 - b0) * s
                q = t((math.cos(a) * (R - 6), math.sin(a) * (R - 6)))
                W.puff(Ld, q[0], q[1] + 6 + 10 * age, (7 + 5 * rng.random()) * (0.7 + 0.5 * age), v=0.75 - 0.3 * age,
                       seed=seed + m)
        if n == 3 and not hot:                           # 3타: 바닥 눌림 고리(앞-아래)
            c = t((R * 0.55, 0))
            c = (c[0], c[1] + W.HIT_UP - 4)
            rr = R * (0.3 + 0.3 * age)
            Ld.arc(c[0], c[1], rr, rr * 0.4, 0, 2 * math.pi, 2.4 * (1 - 0.5 * age), v=0.75 - 0.3 * age)
    return draw


def weight(n, pad=0):
    name = "greatsword_combo%d_weight" % n
    old, size, piv, o = geo(name, pad)
    fr = C.frames(old, weight_main(old, n), size=size, origin=o)
    R, a0, a1, sgn = arcinfo(old)
    ex = extra(old, "greatsword", "weight", design_of("weight"))
    ex["fan"] = {"innerRadiusDots": R_IN, "outerRadiusDots": R, "facets": FACETS[n],
                 "note": "그림 메모 — 부채 바깥 테 = 판정 반경(꺾인 다각 테, 꼭짓점 = R). 판정은 기본 호 그대로"}
    return fr, ex


# ================================================================== 단검 twin 쌍격 — 교차 X
def _shift(t, off):
    p = t(off)
    return W.T(t.d, p[0], p[1])


def line_thrust(f, t, kind, k, p0, p1, hw, seed, cracks=1, heat=0):
    """로컬 p0 → p1 바늘(thrust_frame 을 p0 원점·p0→p1 각으로)."""
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    ln = math.dist(p0, p1)
    DG.thrust_frame(f, _shift(t, p0), kind, k, ang, 0.0, ln, hw, seed, cracks=cracks, heat=heat)


def twin_geom(old, n):
    th = old["thrust"]
    ang = math.radians(th["angleDeg"])
    x0 = th["fromPx"] * W.K4
    x1 = th["lengthPx"] * W.K4 + 6
    xc = x0 + (x1 - x0) * (0.5 if n == 3 else 0.6)
    h = 22.0 if n == 3 else 15.0
    ca, sa = math.cos(ang), math.sin(ang)

    def R_(u, v):
        return (ca * u - sa * v, sa * u + ca * v)
    lines = []
    for s in (-1, 1):
        y0 = s * h
        y1 = -s * h * (x1 - xc) / (xc - x0)
        lines.append((R_(x0, y0), R_(x1, y1)))
    return lines, R_(xc, 0), ang, x1


def twin_main(old, n, hw=3.4):
    lines, C_, ang, x1 = twin_geom(old, n)
    st = DG._states(old["frames"], old["impactFrame"])

    def draw(f, t, d, i, F):
        kind, k = st[i]
        for j, (p0, p1) in enumerate(lines):
            line_thrust(f, t, kind, k, p0, p1, hw, 800 + 10 * n + j, cracks=1)
        Lh = f.L(W.R_HOT)
        Lx = f.L(W.R_EDGE)
        c = t(C_)
        if kind == "hit":
            P.glint(Lh, c[0], c[1], 13, v=1.0, diag=0.55, rot=t.ang(ang))
        elif kind == "after" and k < 0.99:        # 교차 흉터: 짧은 x 가 식으며 남음
            for (p0, p1) in lines:
                dx, dy = p1[0] - p0[0], p1[1] - p0[1]
                L_ = math.hypot(dx, dy)
                ux, uy = dx / L_, dy / L_
                a = (C_[0] - ux * 9, C_[1] - uy * 9)
                b = (C_[0] + ux * 9, C_[1] + uy * 9)
                Lx.stroke(t.pts([a, b]), 1.2, prof=FK.tp_both(0.7, 0.5), v=0.58 - 0.3 * k)
    return draw


def twin(n, pad=0):
    name = "dagger_combo%d_twin" % n
    old, size, piv, o = geo(name, pad)
    fr = C.frames(old, twin_main(old, n), size=size, origin=o)
    lines, C_, ang, x1 = twin_geom(old, n)
    ex = extra(old, "dagger", "twin", design_of("twin"))
    ex["cross"] = {"atLocalDots": [round(C_[0], 1), round(C_[1], 1)], "note": "그림 메모 — X 교차점(판정 원점 기준). 판정은 기본 thrust 그대로"}
    return fr, ex


# ================================================================== 단검 gale 질풍 — 회오리 꼬리
def gale_geom(old, n):
    th = old["thrust"]
    ang = math.radians(th["angleDeg"])
    x0 = th["fromPx"] * W.K4
    x1 = min(th["lengthPx"] * W.K4 + 6, 110.0)    # 256 틀(반경 128) 안 — 촉 불티 자리
    return ang, x0, x1, (26.0 if n == 3 else 20.0)


def ellipse_pts(cu, ry, rx, ca, sa, a_from=0.0, a_to=2 * math.pi, n=48):
    """찌르기 축(u) 위 cu 에 세운 옆으로 누운 고리(축 방향 rx, 수직 ry) → 로컬 점."""
    out = []
    for m in range(n + 1):
        a = a_from + (a_to - a_from) * m / n
        u = cu + math.cos(a) * rx
        v = math.sin(a) * ry
        out.append((ca * u - sa * v, sa * u + ca * v))
    return out


def gale_main(old, n, amp_k=1.0, rings=3, strands=2):
    ang, x0, x1, A0 = gale_geom(old, n)
    A0 *= amp_k
    ca, sa = math.cos(ang), math.sin(ang)
    st = DG._states(old["frames"], old["impactFrame"])
    u_back = 2.0                                  # 손 앞에서 시작(몸을 가리지 않게)
    turns = 2.4 if n == 3 else 2.0

    def P_(u, v):
        return (ca * u - sa * v, sa * u + ca * v)

    def draw(f, t, d, i, F):
        kind, k = st[i]
        Lr = f.L(W.R_ASHG)
        Lh = f.L(W.R_EDGE)
        DG.thrust_frame(f, t, kind, k, ang, x0, x1, 2.3, 900 + n, cracks=0)
        if kind == "pre":
            pts = ellipse_pts(10, A0 * 0.6, A0 * 0.16, ca, sa)
            Lr.stroke(t.pts(pts), 0.6, v=0.75, dash=(10, 0.6, 0.0))
            return
        hot = kind == "hit"
        age = 0.0 if hot else k
        push = 16 * age
        ph0 = i * 0.9
        for sidx in range(strands):                      # 나선 두 가닥: 앞면 호박 · 뒷면 재
            seg_f, seg_b = [], []
            N = 90
            for m in range(N + 1):
                q = m / N
                u = u_back + (x1 - u_back) * q
                if not hot and q < 0.55 * age:
                    continue
                A = A0 * (1 - q) ** 1.1 * (1 - 0.35 * age)
                phi = 2 * math.pi * turns * q + ph0 + sidx * math.pi * 2 / strands
                v_ = A * math.sin(phi)
                front = math.cos(phi) > 0
                p = P_(u + push, v_)
                (seg_f if front else seg_b).append(p)
                (seg_b if front else seg_f).append(None)
            for seg, L, v in ((seg_b, Lr, 0.85 - 0.3 * age), (seg_f, Lh, (0.62 if hot else 0.55 - 0.25 * age))):
                run = []
                for p in seg + [None]:
                    if p is None:
                        if len(run) > 2:
                            L.stroke(t.pts(run), 1.2 if L is Lh else 0.8, prof=FK.tp_both(0.6, 0.5), v=v,
                                     dash=None if age < 0.6 else (8, 0.6, 0.2 * sidx))
                        run = []
                    else:
                        run.append(p)
        for m in range(rings):                           # 몸 뒤 옆으로 누운 회오리 고리(원뿔)
            cu = 10 + 12 * (rings - 1 - m) - 8 * age     # 몸 앞 원뿔: 뒤가 넓고 촉 쪽으로 좁아짐
            ry = A0 * (1.15 - 0.25 * (rings - 1 - m)) * (1 + 0.4 * age)
            rx = ry * 0.22
            v = (0.8 - 0.12 * m) * (1 - 0.6 * age)
            if v < 0.2:
                continue
            front = ellipse_pts(cu + push * 0.3, ry, rx, ca, sa, -math.pi / 2, math.pi / 2, 30)
            back = ellipse_pts(cu + push * 0.3, ry, rx, ca, sa, math.pi / 2, 3 * math.pi / 2, 30)
            Lr.stroke(t.pts(back), 0.6, v=v * 0.8, dash=(9, 0.55, 0.1 * m))
            Lh.stroke(t.pts(front), 0.8, prof=FK.tp_both(0.6, 0.5), v=min(0.6, v * 0.75) if not hot else v * 0.78)
    return draw


def gale(n, pad=0):
    name = "dagger_combo%d_gale" % n
    old, size, piv, o = geo(name, pad)
    fr = C.frames(old, gale_main(old, n), size=size, origin=o)
    return fr, extra(old, "dagger", "gale", design_of("gale"))


SHEETS = {}
for _n in (1, 2, 3):
    SHEETS["katana_combo%d_iai" % _n] = (lambda n: lambda: iai(n))(_n)
    SHEETS["katana_combo%d_batto" % _n] = (lambda n: lambda: batto(n))(_n)
    SHEETS["greatsword_combo%d_crush" % _n] = (lambda n: lambda: crush(n))(_n)
    SHEETS["greatsword_combo%d_weight" % _n] = (lambda n: lambda: weight(n))(_n)
    SHEETS["dagger_combo%d_twin" % _n] = (lambda n: lambda: twin(n))(_n)
    SHEETS["dagger_combo%d_gale" % _n] = (lambda n: lambda: gale(n))(_n)
