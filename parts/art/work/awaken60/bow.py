"""활 — 최종 각성 '유성' 시안 3개. 로컬: u = 조준 방향, v = 활대 방향(− = 위 활대), 줌통(쥔 왼손) = 원점."""
import math

import base as B
import kit60 as K
from kit60 import G, A, GOLD, SIL, VIO, CRI, X0, X1, h2, vnoise, clamp, smooth, stage
from concept import Concept, sparkle

POSES = [
    dict(name="대기 (왼손에 내려 든 활)", ws="bow_carry_idle", wi=0, bs="player_idle_free", bi=0, ang=13, erase="all", t=1),
    dict(name="휘두르기 1 — 가득 당김", ws="bow_draw_hold", wi=6, bs="player_bow_draw_hold", bi=6, ang=0, erase="all", draw=1.0, t=3,
         handR_from=True),
    dict(name="휘두르기 2 — 놓기 + 날아가는 화살 궤적", ws="bow_release", wi=1, bs="player_bow_release", bi=1, ang=0, erase="all", glow=True,
         release=True, t=4, arrow_fly=dict(u=58)),
]


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


class BowBase(Concept):
    weapon, weapon_ko = "bow", "활"
    hero_ang = 0.0
    hero_draw = 1.0
    strip_ang = -math.pi / 2          # 띠에서는 활을 눕혀(조준 = 위) 가로로 길게
    half = B.B_HALF
    ramps_before = [("재 G3~G6", G[3:7]), ("호박 A", A), ("흉갑 SL", K.SL)]

    # 형태 공통 ------------------------------------------------------------
    def bend(self, f):
        return 5 + 15 * f.draw

    def drawlen(self, g, ang, f):
        hr = getattr(f, "handR", None)
        if hr and f.draw > 0:
            return max(8.0, -((hr[0] - g[0]) * math.cos(ang) + (hr[1] - g[1]) * math.sin(ang)))
        return 6 + 28 * f.draw

    def tips(self, f, half=None):
        half = half or self.half_now(f)
        uc = B.bow_uc(half, self.bend(f), half)
        return (uc, -half), (uc, half)

    def half_now(self, f):
        return self.half

    def string(self, cv, g, ang, f, col_fn, w=0.55, dash=None):
        (tu, tv0), (_, tv1) = self.tips(f)
        if f.draw > 0.02 and not f.release:
            n = (-self.drawlen(g, ang, f), 0.0)
        else:
            n = (tu + (1.5 * math.sin(f.t * 2.5) if f.release else 0.0), 0.0)
        for a, b in (((tu, tv0), n), (n, (tu, tv1))):
            pts = [self.W(g, ang, *lerp(a, b, i / 12), f) for i in range(13)]
            cv.chain(pts, lambda t: w, lambda t, d, x, y: col_fn(t, x, y) if (dash is None or dash(x, y)) else None, z=1)
        return n

    def arrow_on_string(self, cv, g, ang, f, shaft, head):
        if f.draw <= 0.02 or f.release:
            return
        dl = self.drawlen(g, ang, f)
        u0, u1 = -dl, 51 - dl
        pts = [self.W(g, ang, u0 + (u1 - u0) * i / 20, 0, f) for i in range(21)]
        cv.chain(pts, lambda t: 0.6, lambda t, d, x, y: shaft(t, x, y), z=2)
        hx, hy = self.W(g, ang, u1, 0, f)
        head(cv, hx, hy)


# =============================================================================
# B-A 혜성 날개 — 활대 끝에서 금빛 불꽃 깃이 뒤로 펼쳐지고 화살이 혜성이 된다
# =============================================================================
class BA(BowBase):
    key, name, title = "B-A", "유성", "혜성 날개: 활대가 금빛으로 달아오르고 양 끝에서 불꽃 깃 3장씩이 날개처럼 뒤로 펼쳐진다"
    form = "활 60 → 활대 68 + 불꽃 깃 6장(길이 17~27, 활대 바깥 절반에서 뒤·바깥으로 부채처럼 펼침) → 실루엣 폭 9 → ~40(뒤로), 높이 68 → ~100 · 줌통에 유성 핵(지름 7) · 시위에 건 화살촉이 불덩이"
    color = "재·호박 → 금(6층 GOLD) + 백열. 줌통에서 활대 끝으로 X1 앞줄이 퍼지며 금으로(0~55%), 이어 깃이 펼쳐짐(55~100%). 순환 6프레임 = 깃 길이·혀가 일렁, 핵 맥동. 당김 정도에 따라 시위 GOLD10 → 가득 X1"
    fx = "화살 = 혜성: 머리 X1 불덩이(지름 6) + 70도트 꼬리(X1 → 금 → 호박, 끝은 끊긴 불티), 놓는 순간 활대 깃이 한 번 크게 펄럭"
    box = (-46, 10, -52, 52)
    reach = 40
    tn = 6
    loop_ms = 80
    bg = [GOLD[0], A[1]]
    ramps_after = [("금 GOLD", GOLD), ("호박 A 3~5", A[3:6]), ("백열", [X1, X0])]

    def half_now(self, f):
        return self.half + 4 * smooth(0.0, 0.55, f.p)

    def feather(self, u, v, f):
        fl = smooth(0.55, 1.0, f.p)
        if fl < 0.03:
            return None
        bend = self.bend(f)
        hv = self.half_now(f)
        for sgn in (-1, 1):
            for k in range(3):
                rv = sgn * (hv * (0.5 + 0.22 * k))
                ru = B.bow_uc(rv, bend, hv)
                wob = 1 + 0.12 * math.sin(2 * math.pi * (f.ph + k / 3)) + (0.25 if f.release else 0)
                L = (17 + 5 * k) * fl * wob
                ang_k = math.radians(172 - 26 * k) if sgn > 0 else math.radians(-172 + 26 * k)
                dx, dy = math.cos(ang_k), math.sin(ang_k)
                a = (u - ru) * dx + (v - rv) * dy
                b = -(u - ru) * dy + (v - rv) * dx
                if a < 0 or a > L:
                    continue
                s = a / L
                c = 4.0 * s ** 2 * (-sgn)
                w = 3.4 * (1 - s) ** 0.7 + 0.3
                d = b - c
                if abs(d) > w:
                    continue
                if s > 0.7 and h2(int(u * 2), int(v * 2), 171 + f.t) > 1.6 - s * 1.4:
                    continue
                q = 1 - abs(d) / w
                if q > 0.7 and s < 0.6:
                    return X1
                if q > 0.45:
                    return GOLD[10] if s < 0.5 else GOLD[8]
                if q > 0.2:
                    return GOLD[6]
                return A[5]
        return None

    def px(self, u, v, x, y, f):
        hv = self.half_now(f)
        cb = B.bow_limb(u, v, f.draw)
        # 유성 핵
        R = 3.6 * smooth(0.0, 0.4, f.p)
        dd = math.hypot(u - 2.5, v)
        if R > 0.5 and dd <= R:
            pulse = 0.5 + 0.5 * math.sin(2 * math.pi * f.ph)
            return (X1 if dd < 1.3 + pulse * 0.6 else GOLD[9] if dd < R - 1.0 else A[4], True)
        if abs(v) <= hv:
            d = u - B.bow_uc(v, self.bend(f), hv)
            hw = 2.2 - 0.9 * abs(v) / hv
            if abs(d) <= hw:
                st = stage(f.p, 0.55 * abs(v) / hv + 0.04 * h2(x, y, 172))
                if st < 0:
                    return (cb, True) if cb else None
                if st == 0:
                    return (X1, False)
                if abs(v) <= 4:
                    return (A[3] if int(v + 9) % 3 else A[2], True)
                if abs(v) > hv - 4:
                    return (GOLD[10] if d > 0 else GOLD[5], True)
                return (GOLD[9] if d > 0.9 else GOLD[6] if d > -0.3 else A[4], True)
        fe = self.feather(u, v, f)
        if fe:
            return (fe, False)
        return (cb, True) if cb else None

    def extra(self, cv, g, ang, f):
        hot = f.p >= 1
        self.string(cv, g, ang, f, lambda t, x, y: (X1 if f.draw > 0.9 else GOLD[10]) if hot else (A[5] if f.p < 0.5 else GOLD[8]))

        def head(cv_, hx, hy):
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    r = math.hypot(dx, dy)
                    if r <= 2.4:
                        cv_.put(hx + dx, hy + dy, X1 if r < 1.2 else GOLD[9] if r < 2 else A[5], 3, False)
        self.arrow_on_string(cv, g, ang, f, lambda t, x, y: GOLD[8] if t > 0.6 else G[5], head)

    def arrow_fly(self, cv, g, ang, f, spec):
        hu = spec["u"]
        tail = 70
        pts = [self.W(g, ang, hu - tail * (1 - i / 24), 0.6 * math.sin(i * 0.9), f) for i in range(25)]

        def col(t, d, x, y):
            if t < 0.35 and h2(x, y, 181) > t * 2.6:
                return None
            if d < 0.35 and t > 0.4:
                return X1
            if t > 0.75:
                return GOLD[10] if d < 0.7 else GOLD[7]
            if t > 0.45:
                return GOLD[7] if d < 0.6 else A[5]
            return A[5] if d < 0.5 else A[3]
        cv.chain(pts, lambda t: 0.6 + 3.0 * t ** 1.4, col, z=-1)
        hx, hy = self.W(g, ang, hu, 0, f)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                r = math.hypot(dx, dy)
                if r <= 3.2:
                    cv.put(hx + dx, hy + dy, X0 if r < 1.4 else X1 if r < 2.3 else GOLD[9], 3, False)
        for k in range(6):
            sx, sy = self.W(g, ang, hu - 10 - 9 * k, (5 + 3 * h2(k, 1, 182)) * (1 if k % 2 else -1), f)
            cv.put(sx, sy + k % 3, GOLD[9] if k % 2 else A[5], 2, False)


# =============================================================================
# B-B 성좌(星座) — 활대가 별 조각으로 흩어져 별자리 선으로 이어진다
# =============================================================================
class BB(BowBase):
    key, name, title = "B-B", "유성", "성좌: 활대가 은빛 별 조각 8개로 흩어져 보랏빛 별자리 선에 이어진 채 떠 있다"
    form = "활 60 → 활대가 조각 8개(각 9×5, 서로 2~4도트 떨어짐) + 관절 별 6개 + 활대 바깥 떠도는 별 4개(활 높이 60 → ~78) · 줌통 = 보라 고리 · 시위 = 점선 별빛"
    color = "재·호박 → 은백(8층 SIL) + 보라 밤하늘 선(5층 VIO). 전반(0~45%) 활대에 보라 금이 줌통→끝으로 그어지고, 후반(45~100%) 조각이 벌어지며 은으로 바뀌고 별자리 선이 이어짐. 순환 10프레임 = 별 하나씩 차례로 크게 반짝(X0 4갈래) — 별자리를 따라 빛이 달림"
    fx = "화살 = 별똥: 머리 큰 반짝임(4갈래 4도트) + 6도트마다 작은 별이 찍히고 보라 선으로 이어지는 점선 꼬리"
    box = (-30, 12, -42, 42)
    reach = 40
    tn = 10
    loop_ms = 70
    bg = [VIO[0], SIL[1]]
    ramps_after = [("은백 SIL", SIL), ("보라 VIO 5~9", VIO[5:10]), ("백열", [X1, X0])]
    POS = [0.22, 0.42, 0.62, 0.84]

    def shards(self, f):
        sg = smooth(0.45, 1.0, f.p)
        bend = self.bend(f)
        out = []
        for sgn in (-1, 1):
            for k, t in enumerate(self.POS):
                v0 = sgn * self.half * t
                u0 = B.bow_uc(v0, bend, self.half)
                gap = sg * (1.5 + 1.4 * k)
                bob = 0.8 * math.sin(2 * math.pi * (f.ph + k / 4 + (sgn > 0) * 0.5)) * sg
                v1 = v0 + sgn * gap
                u1 = B.bow_uc(v1, bend, self.half) - 1.5 * sg + bob
                slope = -2 * bend * abs(v1) / self.half ** 2 * sgn
                out.append((u1, v1, slope, sgn, k))
        return out, sg

    def stars(self, f):
        sh, sg = self.shards(f)
        pts = []
        for sgn in (-1, 1):
            row = [s for s in sh if s[3] == sgn]
            for a, b in zip(row, row[1:]):
                pts.append(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2))
            last = row[-1]
            pts.append((last[0] - 4 * sg, last[1] + sgn * 7 * sg))
        extra = [(-12, -26), (-16, 22), (-6, -40), (-8, 39)]
        return pts, [(eu * sg, ev * sg + (1 - sg) * ev * 0.6) for eu, ev in extra], sh, sg

    def px(self, u, v, x, y, f):
        cb = B.bow_limb(u, v, f.draw)
        sh, sg = self.shards(f)
        # 줌통 고리
        dd = math.hypot(u - 1.5, v)
        if f.p > 0.3 and 3.0 <= dd <= 4.4:
            return (VIO[7] if v < 0 else VIO[5], True)
        if abs(v) <= 4 and cb:
            return (cb, True)
        st0 = stage(min(1.0, f.p / 0.45), abs(v) / self.half + 0.04 * h2(x, y, 191))
        if sg < 0.04:
            if cb is None:
                return None
            if st0 >= 0 and any(abs(abs(v) - self.half * (t + 0.1)) < 0.6 for t in self.POS):
                return (X1 if st0 == 0 else VIO[8], False)
            return (cb, True)
        for (su, sv, slope, sgn, k) in sh:
            # 활대 방향 단위벡터 (slope, 1) 정규화
            n = math.hypot(slope, 1)
            tu, tv = slope / n, 1 / n
            a = (u - su) * tu + (v - sv) * tv
            b = -(u - su) * tv + (v - sv) * tu
            if abs(a) / 4.6 + abs(b) / 2.5 <= 1:
                if abs(a) / 4.6 + abs(b) / 2.5 > 0.74:
                    return (SIL[4], True)
                return (SIL[11] if b < 0 else SIL[7], True)
        if cb and sg < 0.5:
            return (cb, True)
        return None

    def extra(self, cv, g, ang, f):
        pts, ext, sh, sg = self.stars(f)
        if f.p > 0.5:
            # 별자리 선(점선): 조각 중심 → 관절 별 → 바깥 별
            k = smooth(0.6, 1.0, f.p)
            chain_up = [p for p in [(s[0], s[1]) for s in sh if s[3] < 0]]
            chain_dn = [p for p in [(s[0], s[1]) for s in sh if s[3] > 0]]
            lines = [chain_up + [ext[0], ext[2]], chain_dn + [ext[1], ext[3]]]
            for ln in lines:
                for a, b in zip(ln, ln[1:]):
                    L = math.hypot(b[0] - a[0], b[1] - a[1])
                    for i in range(int(L * k) + 1):
                        if i % 2:
                            continue
                        p = lerp(a, b, i / max(1, L))
                        x, y = self.W(g, ang, p[0], p[1], f)
                        cv.put(x, y, VIO[7], -1, False)
        if f.p > 0.6:
            allst = pts + ext
            hot = f.t % len(allst) if f.p >= 1 else -1
            for j, (su, sv) in enumerate(allst):
                x, y = self.W(g, ang, su, sv, f)
                big = j == hot or (f.glow and j % 3 == 0)
                sparkle(cv, int(x), int(y), 3 if big else 1, X0 if big else X1, SIL[9] if big else SIL[8])
        hot = f.p >= 1
        self.string(cv, g, ang, f, lambda t, x, y: X1 if (hot and f.draw > 0.9) else SIL[9] if hot else A[5],
                    dash=(lambda x, y: (x + y) % 3 != 2) if f.p > 0.5 else None)

        def head(cv_, hx, hy):
            sparkle(cv_, int(hx), int(hy), 2, X0, SIL[9], z=3)
        self.arrow_on_string(cv, g, ang, f, lambda t, x, y: (SIL[9] if (x + y) % 3 else VIO[7]) if f.p > 0.5 else G[5], head)

    def arrow_fly(self, cv, g, ang, f, spec):
        hu = spec["u"]
        prev = None
        for i in range(10):
            u = hu - 7 * i
            vv = 1.2 * math.sin(i * 1.1)
            x, y = self.W(g, ang, u, vv, f)
            if prev:
                L = int(math.hypot(x - prev[0], y - prev[1]))
                for j in range(1, L):
                    if j % 2 == 0 and i < 8:
                        p = lerp(prev, (x, y), j / L)
                        cv.put(p[0], p[1], VIO[7] if i < 5 else VIO[5], -1, False)
            if i == 0:
                sparkle(cv, int(x), int(y), 4, X0, SIL[10], z=3)
            elif i < 9:
                sparkle(cv, int(x), int(y), 1 if i % 2 else 2, X1 if i < 4 else SIL[8], SIL[9] if i < 4 else SIL[6])
            prev = (x, y)


# =============================================================================
# B-C 운석 심핵(隕石心核) — 줌통이 녹아내리는 운석 핵이 되고, 당길수록 달아오른다
# =============================================================================
HEAT = [CRI[2], CRI[3], CRI[4], CRI[6], GOLD[4], GOLD[6], GOLD[9], X1, X0]


def heat(h):
    return HEAT[max(0, min(len(HEAT) - 1, int(h * (len(HEAT) - 1) + 0.5)))]


class BC(BowBase):
    key, name, title = "B-C", "유성", "운석 심핵: 줌통이 녹아내리는 운석 핵이 되고 활대는 용암 맥이 흐르는 운석 바위가 된다 — 당길수록 붉음 → 금 → 백열"
    form = "활대 폭 4 → 8(울퉁불퉁한 운석 바위) + 활대 끝 바위 가시 · 줌통 = 지름 15 운석 핵(깨진 껍질 사이로 녹은 속) · 화살촉 = 달군 운석 조각"
    color = "재·호박 → 운석 바위(무채 G2~G5) + 열 램프(진홍 CRI2~6 → 금 GOLD4~9 → X1·X0). 각성 순간 핵이 먼저 붉게 켜지고 바위 껍질이 활대 끝으로 덮여 감. 열은 당김에 묶임: 대기 = 붉음 · 당김 = 금 · 가득 = 백열 · 놓는 순간 X0 섬광. 순환 8프레임 = 핵 맥동 + 맥을 따라 열 띠가 흐름"
    fx = "화살 = 불타는 운석: 머리 3×3 달군 바위 + 굵은 불꽃 꼬리(가운데 X1 → 금 → 진홍) 끝에 검은 연기 덩이(G2·G3) + 떨어지는 불똥"
    box = (-32, 12, -42, 42)
    reach = 40
    tn = 8
    loop_ms = 80
    bg = [CRI[0], CRI[1]]
    hero_draw = 0.3
    ramps_after = [("바위 G2~G6", G[2:7]), ("열 램프", HEAT)]

    def H(self, f):
        if f.release:
            return 1.0
        return clamp(0.32 + 0.6 * f.draw + 0.08 * math.sin(2 * math.pi * f.ph))

    def px(self, u, v, x, y, f):
        cb = B.bow_limb(u, v, f.draw)
        sg = smooth(0.2, 1.0, f.p)
        Hh = self.H(f) * smooth(0.0, 0.4, f.p)
        # 운석 핵
        R = 7.5 * smooth(0.0, 0.35, f.p)
        dd = math.hypot(u - 1.0, v)
        if R > 0.5 and dd <= R:
            crust = dd > R * 0.42 and h2(int((u + 20) / 2.2), int((v + 20) / 2.2), 201) > 0.28
            crack = abs(math.sin(math.atan2(v, u - 1.0) * 2.5 + 0.7)) < 0.16
            if crust and not crack:
                return (G[4] if v < -1 else G[3] if v < 2 else G[2], True)
            return (heat(Hh + 0.25 * (1 - dd / R)), True)
        hv = self.half + 2 * sg
        if abs(v) <= hv:
            uc = B.bow_uc(v, self.bend(f), hv)
            d = u - uc
            hw = (2.1 - 0.9 * abs(v) / hv) + sg * (2.2 + 1.6 * (vnoise(abs(v) * 0.45, 7 if v < 0 else 8) - 0.5))
            if abs(v) > hv - 5:
                hw += sg * 1.5 * (1 - (hv - abs(v)) / 5) * (1 if int(abs(v)) % 3 else -0.5)
            if abs(d) <= hw:
                st = stage(f.p, 0.15 + 0.7 * abs(v) / hv + 0.05 * h2(x, y, 202))
                if st < 0:
                    return (cb, True) if cb else None
                if st == 0:
                    return (CRI[6], True)
                vein = abs(d - 0.9 * math.sin(v * 0.42)) < 0.7 and abs(v) > 5
                if vein:
                    band = 0.15 * math.sin(2 * math.pi * (abs(v) / 18 - f.ph))
                    return (heat(Hh + band + 0.08), True)
                if abs(v) <= 4:
                    return (G[3], True)
                if d > hw - 1.1:
                    return (G[6] if v < 0 else G[5], True)
                return (G[4] if d > 0 else G[3] if d > -hw + 1.1 else G[2], True)
        return (cb, True) if cb else None

    def extra(self, cv, g, ang, f):
        Hh = self.H(f) * smooth(0.0, 0.4, f.p)
        self.string(cv, g, ang, f, lambda t, x, y: heat(Hh - 0.1) if f.p > 0.4 else A[5])

        def head(cv_, hx, hy):
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    cv_.put(hx + dx, hy + dy, heat(Hh + 0.1) if (dx, dy) == (0, 0) else G[3] if dy < 1 else G[2], 3, False)
        self.arrow_on_string(cv, g, ang, f, lambda t, x, y: heat(Hh - 0.15) if t > 0.7 else G[4], head)
        if f.p >= 1 and Hh > 0.5:
            for k in range(4):
                sx, sy = self.W(g, ang, -2 + 3 * k, (8 - k * 4), f)
                cv.put(sx, sy - (f.t * 2 + k * 3) % 9, heat(Hh - 0.2), 2, False)

    def arrow_fly(self, cv, g, ang, f, spec):
        hu = spec["u"]
        tail = 64
        pts = [self.W(g, ang, hu - tail * (1 - i / 24), 1.0 * math.sin(i * 0.6), f) for i in range(25)]

        def col(t, d, x, y):
            if t < 0.3:
                if h2(x // 2, y // 2, 211) > 0.5:
                    return G[3] if d < 0.6 else G[2]
                return None
            if d < 0.3 and t > 0.55:
                return X1
            if d < 0.6:
                return GOLD[8] if t > 0.6 else GOLD[5]
            return CRI[6] if t > 0.5 else CRI[4]
        cv.chain(pts, lambda t: 1.5 + 3.5 * t ** 0.9, col, z=-1)
        hx, hy = self.W(g, ang, hu, 0, f)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if abs(dx) + abs(dy) <= 3:
                    cv.put(hx + dx, hy + dy, X0 if (dx, dy) == (0, 0) else X1 if abs(dx) + abs(dy) <= 1 else G[3], 3, False)
        for k in range(5):
            sx, sy = self.W(g, ang, hu - 14 - 10 * k, 4 * (1 if k % 2 else -1), f)
            cv.put(sx, sy + 3 + 2 * k, GOLD[6] if k % 2 else CRI[6], 2, False)


CONCEPTS = [BA(), BB(), BC()]
