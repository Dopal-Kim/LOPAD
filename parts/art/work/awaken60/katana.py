"""칼 — 최종 각성 '만월' 시안 3개."""
import math

import base as B
import kit60 as K
from kit60 import G, A, SIL, VIO, CRI, X0, X1, h2, clamp, smooth, stage, rp
from concept import Concept, rot_about, crescent

POSES = [
    dict(name="대기 (뽑아 든 칼)", ws="katana_carry_drawn_idle", wi=0, bs="player_idle", bi=0, grip=(113.5, 134.5), t=1),
    dict(name="휘두르기 1 — 3타 치켜듦", ws="katana_combo3", wi=0, bs="player_katana_combo3", bi=0, flip=-1, t=3),
    dict(name="휘두르기 2 — 1타 베기(판정) + 궤적", ws="katana_combo1", wi=2, bs="player_katana_combo1", bi=2, glow=True, t=5,
         trail=dict(S=(104, 116), sweep=95)),
]


class KatanaBase(Concept):
    weapon, weapon_ko = "katana", "칼"
    ramps_before = [("재 G3~G7", G[3:8]), ("호박 A", A)]

    def steel_or_base(self, u, v, x, y, f, thr, steel_fn):
        """칼날(하바키 포함) 픽셀: 전환 문턱 전 = 원래 색, 뒤 = steel_fn."""
        r = B.k_lane(u, v)
        hab = 2.5 <= u < B.K_U0 and abs(v) <= 2.6
        if not (r or hab):
            return None
        cb = B.katana_blade(u, v, f.glow) if r else B.katana_hilt(u, v)
        if cb is None and not hab:
            cb = G[3]
        st = stage(f.p, thr)
        if st < 0:
            return (cb, True)
        if st == 0:
            return (X1, False)
        return (steel_fn(u, v, r, f), True)


# =============================================================================
# K-A 월인(月刃) — 칼끝 너머 초승달 빛날 + 보름달 코등이
# =============================================================================
class KA(KatanaBase):
    key, name, title = "K-A", "만월", "월인(月刃): 칼끝 너머로 초승달 빛날이 자라고 코등이가 보름달이 된다"
    form = "날 55 → 빛날 포함 95도트(초승달처럼 등 쪽으로 크게 휨), 코등이 = 지름 15 보름달 원반(차고 기움), 달 조각 3개가 칼등 위에 뜸"
    color = "재·호박 → 은백(8층 램프). 손잡이→칼끝으로 쓸려가는 X1 앞줄(0~55%), 뒤이어 빛날이 칼끝에서 자람(55~100%). 순환 = 은빛 맥동이 코등이→빛날 끝으로 흐르고 원반이 8프레임에 한 번 차고 기움"
    fx = "궤적 = 바깥 테가 X1 인 초승달 띠(머리 두께 = 반지름의 50%, 꼬리는 가늘어지며 픽셀이 듬성듬성 끊김) + 꼬리를 따라 흩어지는 초승달 조각 5개"
    box = (-18, 100, -32, 10)
    reach = 96
    tn = 8
    bg = [SIL[0], SIL[1]]
    ramps_after = [("은백 SIL", SIL), ("백열", [X1, X0])]

    def ext_len(self, p):
        return 38 * smooth(0.5, 1.0, p)

    def steel(self, u, v, r, f):
        if r is None:
            return SIL[9] if v < 0 else SIL[7]
        un, dn, edge, back = r
        pulse = abs(u - self.pulse_pos(f)) < 3
        if edge:
            return X0 if (f.glow or pulse) else X1
        lv = 9 if dn > 0.72 else 6 if dn > 0.45 else 4 if dn > 0.18 else 2
        return SIL[min(11, lv + (3 if pulse else 0))]

    def pulse_pos(self, f):
        return -4 + f.ph * 120

    def ext(self, u, v, f, ghost=False, x=0, y=0):
        Lx = self.ext_len(f.p) if not ghost else 38
        if Lx <= 0.5:
            return None
        u0, u1 = 40.0, B.K_U1 + Lx
        if u < u0 or u > u1:
            return None
        s = (u - u0) / (u1 - u0)
        c = B.k_curve(min(u, B.K_U1)) - 2.0 * max(0, (u - B.K_U1) / 53) * 2 - 0.0062 * max(0.0, u - 50) ** 2 * (Lx / 38)
        w = 5.6 * math.sin(math.pi * s) ** 0.75
        d = v - c
        if w < 0.6:
            return None
        if abs(d) > w:
            if abs(d) < w + 1.8 and not ghost and (x + y) % 2 == 0:
                return (SIL[2], False)                    # 빛 번짐(체크 1겹)
            return None
        q = 1 - abs(d) / w
        if ghost:
            return (SIL[5], False) if q < 0.3 else None
        if q < 0.2:
            return (SIL[3], False)
        if abs(u - self.pulse_pos(f)) < 3 and q > 0.3:
            return (X0, False)
        if d > 0 and q > 0.5:
            return (X1, False)                            # 날선 쪽 백열 심
        if q > 0.55:
            return (SIL[10], False)
        return (SIL[7], False)

    def disc(self, u, v, f):
        R = 8.6 * smooth(0.05, 0.55, f.p)
        dd = math.hypot(u - 1.2, v)
        if R < 0.5 or dd > R:
            return None
        if dd > R - 1.3:
            return (SIL[9] if v < 0 else SIL[6], True)
        # 차고 기움: 위상 0 = 보름, 0.5 = 그믐
        k = math.cos(2 * math.pi * f.ph) * math.sqrt(max(0.0, (R - 1.3) ** 2 - v * v))
        lit = (u - 1.2) > -k if f.ph < 0.5 else (u - 1.2) < k
        lit = lit if math.cos(2 * math.pi * f.ph) > -0.95 else False
        if lit:
            if h2(int(u + 9), int(v + 9), 4) > 0.83:
                return (SIL[8], True)                    # 달 표면 얼룩
            return (SIL[11] if dd < R - 3 else SIL[10], True)
        return (SIL[1], True)

    def px(self, u, v, x, y, f):
        hilt = B.katana_hilt(u, v)
        if u < 0 and hilt:
            return (hilt, True)
        un = clamp((u - B.K_U0) / (B.K_U1 - B.K_U0))
        s = self.steel_or_base(u, v, x, y, f, 0.55 * un + 0.04 * h2(x, y, 3), self.steel)
        if s:
            return s
        e = self.ext(u, v, f, x=x, y=y)
        if e:
            return e
        dsc = self.disc(u, v, f)
        if dsc:
            return dsc
        if hilt:
            return (hilt, True) if f.p < 0.3 else None
        return None

    def extra(self, cv, g, ang, f):
        if f.p < 0.75:
            return
        shard = [(0, 0, SIL[9]), (1, 0, SIL[10]), (2, 1, X1), (3, 2, X1), (3, 3, SIL[10]), (2, 4, SIL[8]), (1, 5, SIL[7]), (0, 5, SIL[6]),
                 (1, 1, SIL[4]), (2, 2, SIL[4]), (2, 3, SIL[4]), (1, 4, SIL[4])]
        for k, (u, v) in enumerate(((26, -9), (50, -12), (74, -22))):
            if f.p < 0.8 + 0.06 * k:
                continue
            bob = round(1.5 * math.sin(2 * math.pi * (f.ph + k / 3)))
            x, y = self.W(g, ang, u, v - bob, f)
            self.glyph(cv, int(x), int(y), shard)

    def trail(self, cv, S, r1, r2, a0, a1, f, g, ang):
        def fn(tn, rn, x, y):
            q = crescent(tn, rn, x, y, head=0.5, seed=21)
            if q is None:
                return None
            if q > 0.9:
                return X1 if tn > 0.5 else SIL[9]
            if q > 0.65:
                return SIL[10] if tn > 0.6 else SIL[7]
            if q > 0.35:
                return SIL[6] if tn > 0.3 else SIL[4]
            return SIL[3]
        cv.smear(S, r1, r2 + 3, a0, a1, fn, z=-3)
        # 꼬리를 따라 흩어지는 달 조각(초승 글리프)
        shard = [(0, 0, SIL[8]), (1, 0, SIL[10]), (2, 1, X1), (2, 2, SIL[9]), (1, 3, SIL[7]), (0, 3, SIL[5])]
        for j in range(5):
            t = 0.12 + 0.17 * j
            a = a0 + (a1 - a0) * t
            r = r2 - 4 - 10 * h2(j, 3, 7) - 4
            self.glyph(cv, int(S[0] + r * math.cos(a)), int(S[1] + r * math.sin(a)), shard, z=-1)


# =============================================================================
# K-B 삭망(朔望) 쌍날 — 날이 세로로 갈라져 은(보름)·보라(그믐) 두 날
# =============================================================================
class KB(KatanaBase):
    key, name, title = "K-B", "만월", "삭망 쌍날: 칼날이 세로로 갈라져 은빛 '보름 날'과 보랏빛 '그믐 날' 두 줄이 된다"
    form = "날 55 → 74도트, 길이 방향으로 쪼개져 두 날 사이가 칼끝으로 갈수록 벌어짐(틈 0 → 7) · 틈에 보라 빛줄 · 코등이에 은·보라 초승 뿔 2개"
    color = "재·호박 → 은백 + 보라(5층 램프). 전반(0~50%) 날 가운데로 X1 금이 손잡이→칼끝으로 달리고, 후반(45~100%) 두 날이 벌어지며 각자 색으로. 순환 12프레임 = 밝기가 은 날 → 보라 날로 물결처럼 넘어갔다 돌아옴(삭↔망)"
    fx = "궤적 = 겹 궤적: 바깥 은 띠 + 안쪽 보라 띠(15° 늦게 따라옴), 두 띠 사이 빈 틈"
    box = (-18, 80, -16, 16)
    reach = 76
    tn = 12
    loop_ms = 70
    bg = [VIO[0], VIO[1]]
    ramps_after = [("은백 SIL", SIL), ("보라 VIO", VIO), ("백열", [X1, X0])]

    def geom(self, f):
        sg = smooth(0.45, 1.0, f.p)
        return sg, B.K_U1 + 16 * sg

    def wave(self, u, f):
        return 0.5 + 0.5 * math.cos(2 * math.pi * (f.ph - u / 90))

    def px(self, u, v, x, y, f):
        hilt = B.katana_hilt(u, v)
        if u < 0 and hilt:
            return (hilt, True)
        sg, Lc = self.geom(f)
        if f.p > 0.2:
            h = self.horn(u, v, f)
            if h:
                return h
        if sg <= 0.02:
            # 전반: 원래 칼 + 가운데 금(X1)이 손잡이→칼끝으로
            r = B.k_lane(u, v)
            if r:
                un, dn, edge, back = r
                if abs(dn - 0.5) < 0.13 and un < f.p / 0.5:
                    return (X1 if un > f.p / 0.5 - 0.15 else VIO[8], False)
                return (B.katana_blade(u, v, f.glow) or G[3], True)
            return (hilt, True) if hilt else None
        if hilt and u < B.K_U0:
            return (hilt, True)
        if u < B.K_U0 or u > Lc:
            return None
        un = (u - B.K_U0) / (Lc - B.K_U0)
        c = -2.6 * un ** 2
        sep = 7.0 * sg * smooth(0.05, 1.0, un) ** 0.8
        d = v - c
        wv = self.wave(u, f)
        # 위(은·보름) 날: 중심 c - sep/2 - 2 / 아래(보라·그믐) 날: 중심 c + sep/2 + 2
        for side in (-1, 1):
            cc = side * (sep / 2 + 2.0)
            hw = 2.1
            uend = Lc if side < 0 else Lc - 4
            if u > uend:
                continue
            tipk = (u - (uend - 8)) / 8
            dd = (d - cc) * side                           # + = 바깥쪽
            lo, hi = -hw, hw
            if tipk > 0:
                lo = -hw + tipk * 2 * hw                   # 안쪽에서 깎여 바깥쪽 끝으로 모이는 칼끝
            if lo <= dd <= hi:
                q = (dd - lo) / ((hi - lo) or 1)           # 0 안 → 1 바깥
                if side < 0:
                    shift = int(round(3 * (1 - wv)))
                    if q > 0.8:
                        return (X0 if f.glow else (X1 if shift == 0 else SIL[9]), True)
                    lv = 9 if q > 0.55 else 6 if q > 0.25 else 3
                    return (SIL[max(1, lv - shift)], True)
                shift = int(round(3 * wv))
                if q > 0.8:
                    return (VIO[min(11, 7 + shift)] if not f.glow else VIO[11], True)
                lv = 4 if q > 0.5 else 3 if q > 0.25 else 2
                return (VIO[min(9, lv + shift)], True)
        if sep > 1.2 and abs(d) < 0.7 and u < Lc - 6:
            return (X1 if (int(u) + f.t * 3) % 9 < 2 else VIO[8], False)
        return None

    def horn(self, u, v, f):
        k = smooth(0.2, 0.7, f.p)
        for side in (-1, 1):
            # 코등이 위·아래에서 칼끝 쪽으로 말려 나가는 초승 뿔
            for i in range(14):
                t = i / 13
                hu = 1.5 + 9 * t * k
                hv = side * (4.5 + 5.5 * math.sin(t * math.pi * 0.85) * k)
                w = 1.0 * (1 - t) + 0.35
                if t < 0.12:
                    continue
                if math.hypot(u - hu, v - hv) <= w:
                    ramp = SIL if side < 0 else VIO
                    return (ramp[10] if t > 0.8 else ramp[8] if side < 0 else ramp[6], True)
        return None

    def extra(self, cv, g, ang, f):
        if f.p < 0.9:
            return
        for k in range(4):
            u = 20 + ((f.t * 5 + k * 17) % 60)
            v = 6 + 3 * math.sin(k * 2.1 + f.t * 0.6)
            x, y = self.W(g, ang, u, v, f)
            cv.put(x, y, VIO[8] if k % 2 else VIO[6], 1, False)

    def trail(self, cv, S, r1, r2, a0, a1, f, g, ang):
        def outer(tn, rn, x, y):
            q = crescent(tn, rn, x, y, head=0.28, seed=31)
            if q is None:
                return None
            return X1 if q > 0.85 and tn > 0.55 else SIL[9] if q > 0.6 else SIL[6] if q > 0.3 else SIL[3]

        def inner(tn, rn, x, y):
            tn = tn * 1.2 - 0.2
            if tn < 0:
                return None
            q = crescent(tn, rn / 0.66, x, y, head=0.3, seed=33)
            if q is None:
                return None
            return VIO[10] if q > 0.85 and tn > 0.6 else VIO[7] if q > 0.55 else VIO[5] if q > 0.25 else VIO[3]
        cv.smear(S, r1, r2 + 2, a0, a1, outer, z=-3)
        cv.smear(S, r1, r2, a0, a1, inner, z=-4)


# =============================================================================
# K-C 적월(赤月) 파편 — 칼날이 6조각으로 부서져 핏빛 빛줄에 꿰여 뜬다
# =============================================================================
class KC(KatanaBase):
    key, name, title = "K-C", "만월", "적월 파편: 칼날이 6조각으로 부서져 핏빛 등뼈 빛줄에 꿰인 채 떠오른다"
    form = "날 55 → 70도트, 6조각으로 끊겨 조각 사이 1~4도트 틈(칼끝 쪽일수록 넓음), 조각마다 위아래로 어긋나 들썩임 · 코등이 둘레를 붉은 파편 6개가 돎"
    color = "재·호박 → 진홍(7층 램프). 전반(0~40%) 조각 경계로 붉은 금이 퍼짐(픽셀마다 시점이 다른 해시 문턱), 후반(40~100%) 조각이 떨어져 나가며 등뼈 빛줄이 켜짐. 순환 10프레임 = 심장박동(쿵-쿵-쉼): 0·2프레임 등뼈·조각 심 X1·날선 CRI8, 나머지 CRI5~6 로 어둡게(분홍기 도는 CRI9 이상은 안 씀)"
    fx = "궤적 = 조각마다 따로 긋는 가는 핏빛 줄 6가닥(빗살 궤적), 머리 끝만 X1"
    box = (-18, 80, -20, 20)
    reach = 72
    tn = 10
    loop_ms = 70
    bg = [CRI[0], CRI[1]]
    ramps_after = [("진홍 CRI 2~8", CRI[2:9]), ("재 G2~G5", G[2:6]), ("백열", [X1, X0])]
    SEG = [(5, 13), (14, 22), (23, 31), (32, 40), (41, 49), (50, 58)]
    hero_t = 1

    def beat(self, f):
        return {0: 1.0, 1: 0.45, 2: 0.9, 3: 0.35}.get(f.t % self.tn, 0.0)

    def seg_of(self, u, v, x, y, f):
        sg = smooth(0.4, 1.0, f.p)
        for k, (a, b) in enumerate(self.SEG):
            c = (a + b) / 2
            c2 = B.K_U0 + (c - B.K_U0) * (1 + 0.3 * sg) + (3 if k == 5 else 0) * sg
            half = (b - a) / 2 + 0.5
            jag = 1.3 * h2(int(v + 9), k, 17) * sg
            dv = sg * ((2.2 if k % 2 else -2.2) + 1.0 * math.sin(2 * math.pi * f.ph + k * 1.3))
            if c2 - half + jag <= u <= c2 + half - (1.3 * h2(int(v + 9), k, 19) * sg):
                return k, c + (u - c2), v - dv, sg
        return None

    def px(self, u, v, x, y, f):
        hilt = B.katana_hilt(u, v)
        if u < 0 and hilt:
            return (hilt, True)
        bt = self.beat(f) if f.p >= 1 else 0.0
        sgr = self.seg_of(u, v, x, y, f)
        if sgr:
            k, uo, vo, sg = sgr
            r = B.k_lane(uo, vo, hw=B.K_HW + 1.0 * sg)
            if r:
                un, dn, edge, back = r
                crack = min(abs(uo - e) for s0, s1 in self.SEG for e in (s0 - 0.5, s1 + 0.5))
                st = stage(clamp(f.p / 0.4), 0.15 + 0.7 * un + 0.15 * h2(x, y, 5))
                if st < 0:
                    return (B.katana_blade(uo, vo, f.glow) or G[3], True)
                if crack < 1.2 and sg < 0.3:
                    return (X1 if st == 0 else CRI[8], False)
                if edge:
                    return (X1 if (f.glow and bt > 0.8) else CRI[8] if bt > 0.3 or f.glow else CRI[6], True)
                if abs(dn - 0.5) < 0.12 and 0.2 < (uo - self.SEG[k][0]) / 8 < 0.85:
                    return (X1 if bt > 0.8 else CRI[7] if bt > 0.3 else CRI[5], True)        # 조각 속 붉은 심
                if back:
                    return (CRI[3], True)
                return (G[5] if dn > 0.7 else G[4] if dn > 0.45 else G[3] if dn > 0.2 else G[2], True)
        # 하바키
        if 2.5 <= u < B.K_U0 and abs(v) <= 2.6:
            return (CRI[4] if f.p > 0.4 else G[6], True)
        sg = smooth(0.4, 1.0, f.p)
        if sg > 0.05 and B.K_U0 <= u <= 75 * sg + B.K_U0 * (1 - sg):
            c = B.k_curve(min(u, B.K_U1)) * 1.3
            if abs(v - c) < 0.65:
                return (X1 if bt > 0.8 else CRI[7] if bt > 0.3 else CRI[5], False)
        if hilt:
            return (hilt, True)
        return None

    def extra(self, cv, g, ang, f):
        if f.p < 0.5:
            return
        R = 9.5 * smooth(0.5, 1.0, f.p)
        for k in range(6):
            a = 2 * math.pi * (k / 6 + f.ph * 0.5)
            x, y = self.W(g, ang, 1.2 + R * math.cos(a), R * math.sin(a), f)
            x, y = int(x), int(y)
            cv.put(x, y, CRI[7], 1, False)
            cv.put(x + 1, y, CRI[5], 1, False)
            cv.put(x, y + 1, CRI[4], 1, False)

    def trail(self, cv, S, r1, r2, a0, a1, f, g, ang):
        span = r2 - r1
        for k in range(6):
            rc = r1 + span * (0.18 + 0.82 * (k + 0.5) / 6)

            def fn(tn, rn, x, y, k=k):
                if tn < 0.2 and h2(x, y, 41 + k) > tn * 5:
                    return None
                if tn > 0.93:
                    return X1
                return CRI[7] if tn > 0.6 else CRI[5] if tn > 0.3 else CRI[3]
            cv.smear(S, rc - 0.9, rc + 0.6 + 0.6 * (k == 5), a0 + (a1 - a0) * 0.05 * k, a1, fn, z=-3)


CONCEPTS = [KA(), KB(), KC()]
