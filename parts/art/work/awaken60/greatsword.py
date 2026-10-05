"""대검 — 최종 각성 '산붕' 시안 3개."""
import math

import base as B
import kit60 as K
from kit60 import G, A, OCH, TEAL, GRN, GOLD, CRI, WD, X0, X1, h2, vnoise, clamp, smooth, stage
from concept import Concept, rot_about, crescent

POSES = [
    dict(name="대기 (뽑아 든 대검)", ws="greatsword_carry_drawn_idle", wi=0, bs="player_idle_free", bi=0, erase=6.5,
         erase_extra=[(-3, 9, 12)], t=1),
    dict(name="휘두르기 1 — 1타 치켜듦", ws="greatsword_combo1", wi=0, bs="player_greatsword_combo1", bi=0, erase=6.5,
         erase_extra=[(-3, 9, 12)], t=3),
    dict(name="휘두르기 2 — 1타 내려베기(판정) + 궤적", ws="greatsword_combo1", wi=5, bs="player_greatsword_combo1", bi=5, erase=6.5,
         erase_extra=[(-3, 9, 12)], glow=True, t=5, trail=dict(S=(128, 120), sweep=125)),
]


def seg_dist(px_, py_, pts):
    best = 1e9
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        ex, ey = bx - ax, by - ay
        ll = ex * ex + ey * ey or 1e-6
        k = clamp(((px_ - ax) * ex + (py_ - ay) * ey) / ll)
        best = min(best, math.hypot(px_ - ax - ex * k, py_ - ay - ey * k))
    return best


def in_poly(x, y, poly):
    ins = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            ins = not ins
        j = i
    return ins


class GSBase(Concept):
    weapon, weapon_ko = "greatsword", "대검"
    hero_ang = -0.7
    trail_in = 8
    ramps_before = [("재·쇠 G4~G8", G[4:9]), ("녹·호박 A", A), ("흉갑 SL", K.SL)]


# =============================================================================
# G-A 용암 거암검 — 날이 현무암 판으로 부풀고 용암 균열이 흐른다
# =============================================================================
class GA(GSBase):
    key, name, title = "G-A", "산붕", "용암 거암검: 대검이 현무암 판으로 부풀어 오르고 갈라진 틈으로 용암이 흐른다"
    form = "날 90×폭 9 → 108×최대 19도트, 가장자리가 들쭉날쭉한 바위 판 · 등날에 바위 가시 4개 · 갈래 균열 5줄(용암) · 칼끝은 깨진 바위 촉"
    color = "녹슨 쇠 → 현무암(무채 G2~G7) + 용암(진홍 7층 → 금 6층 → X1). 전반(5~45%) 균열이 손잡이→칼끝으로 먼저 불붙고, 이어 날 몸이 현무암으로 굳으며 판이 부풂(35~100%). 순환 = 용암 밝기 띠가 균열을 따라 칼끝 쪽으로 흐름(8프레임), 불티가 위로·용암 방울이 아래로"
    fx = "궤적 = 머리가 두꺼운 용암 초승달(바깥 X1 → 금 → 진홍), 안쪽 가장자리는 검은 연기(G2·G3)로 끊김 + 궤적 아래로 떨어지는 달군 돌 4개"
    box = (-26, 115, -24, 22)
    reach = 111
    tn = 8
    bg = [CRI[0], CRI[1]]
    ramps_after = [("현무암 G2~G7", G[2:8]), ("진홍 CRI 3~7", CRI[3:8]), ("금 GOLD", GOLD[4:12]), ("백열", [X1, X0])]
    FISS = [
        [(10, 0.5), (22, -0.8), (34, 0.9), (46, -0.4), (58, 1.0), (70, -0.6), (82, 0.7), (94, -0.3), (104, 0.2)],
        [(30, 0.6), (34, -3), (39, -5.5), (43, -8)],
        [(50, -0.2), (55, 2.6), (61, 5.5)],
        [(72, -0.4), (77, -3.5), (82, -7)],
        [(88, 0.6), (93, 3.2), (97, 5)],
    ]

    def spikes(self, u):
        s = 0.0
        for k, uc in enumerate((28, 48, 68, 86)):
            H = 6 + 3 * h2(k, 5, 1)
            if uc - 6 <= u <= uc:
                s = max(s, H * (u - (uc - 6)) / 6)
            elif uc < u <= uc + 1.5:
                s = max(s, H * (1 - (u - uc) / 1.5))
        return s

    def slab(self, u, v, sg, Lc):
        if u < 8 or u > Lc:
            return None
        un = (u - 3) / (Lc - 3)
        wt = 4.5 + sg * (3.0 + 2.2 * (vnoise(u * 0.28, 1) - 0.5) + self.spikes(u * 1.0))
        wb = 4.5 + sg * (2.6 + 2.0 * (vnoise(u * 0.31, 2) - 0.5))
        if un > 0.8:
            k = (1 - (un - 0.8) / 0.2) ** 0.85
            wt, wb = wt * k, wb * k + 1.2 * (1 - k) * sg
        if -wt <= v <= wb:
            return un, (v + wt) / ((wt + wb) or 1), wt, wb
        return None

    def fiss(self, u, v, sg, Lc):
        sc = (Lc - 3) / 90.0
        best = 9.0
        for pts in self.FISS:
            pp = [(3 + (a - 3) * sc, b * (0.6 + 0.4 * sg)) for a, b in pts]
            best = min(best, seg_dist(u, v, pp))
        return best

    def lava(self, u, d, f, glow):
        band = 0.5 + 0.5 * math.sin(2 * math.pi * (u / 22 - f.ph))
        if d < 0.75:
            if glow or band > 0.75:
                return X1
            return GOLD[9] if band > 0.4 else GOLD[6]
        return CRI[6] if band > 0.5 else CRI[4]

    def px(self, u, v, x, y, f):
        hilt = B.gs_hilt(u, v)
        if u < 3 and hilt:
            if f.p > 0.6 and 0 <= u < 3 and abs(v - 0.3 * u) < 0.6:
                return (CRI[6], True)                     # 코등이에도 금
            return (hilt, True)
        sg = smooth(0.35, 1.0, f.p)
        Lc = 93 + 18 * sg
        cb = B.gs_blade(u, v, f.glow)
        sl = self.slab(u, v, sg, Lc)
        if cb is None and sl is None:
            return None
        un = sl[0] if sl else clamp((u - 3) / 90)
        # 균열(먼저 불붙음)
        if u >= 9:
            d = self.fiss(u, v, sg, Lc)
            if d < 1.6:
                stf = stage(f.p, 0.05 + 0.4 * un)
                if stf == 0:
                    return (X1, False)
                if stf > 0:
                    return (self.lava(u, d, f, f.glow), True)
        st = stage(f.p, 0.3 + 0.35 * un + 0.06 * h2(x, y, 9))
        if st < 0 or sl is None:
            return (cb, True) if cb else None
        if st == 0:
            return (G[8], True)
        un, dn, wt, wb = sl
        if v < -wt + 1.1:
            lv = 7
        elif dn < 0.3:
            lv = 5
        elif dn < 0.6:
            lv = 4
        elif dn < 0.85:
            lv = 3
        else:
            lv = 2
        if h2(x // 2, y // 2, 13) > 0.82:
            lv -= 1
        return (G[max(1, lv)], True)

    def extra(self, cv, g, ang, f):
        if f.p < 0.7:
            return
        for k in range(7):
            u = 14 + 13 * k + 3 * h2(k, 1, 3)
            x, y = self.W(g, ang, u, -6 * f.flip, f)
            yy = y - 3 - ((f.t * 3 + k * 5) % 16)
            cv.put(x + (k % 3) - 1, yy, GOLD[8] if (f.t + k) % 3 == 0 else CRI[6], 2, False)
        for k, u in enumerate((44, 78)):
            x, y = self.W(g, ang, u, 7 * f.flip, f)
            yy = y + 2 + ((f.t * 2 + k * 4) % 10)
            cv.put(x, yy, GOLD[6], 2, False)
            cv.put(x, yy + 1, CRI[5], 2, False)

    def trail(self, cv, S, r1, r2, a0, a1, f, g, ang):
        def fn(tn, rn, x, y):
            q = crescent(tn, rn, x, y, head=0.62, seed=51)
            if q is None:
                return None
            q = q + 0.12 * (vnoise(x * 0.25 + y * 0.1, 4) - 0.5) + 0.08 * (h2(x, y, 53) - 0.5)
            if q > 0.9:
                return X1 if tn > 0.5 else GOLD[7]
            if q > 0.76:
                return GOLD[7] if tn > 0.55 else CRI[7]
            if q > 0.56:
                return CRI[6] if tn > 0.3 else CRI[4]
            if q > 0.36:
                return CRI[4] if tn > 0.3 else CRI[3]
            if q > 0.22:
                return CRI[2]
            if h2(x // 2, y // 2, 52) > 0.45:
                return G[3] if q > 0.1 else G[2]
            return None
        cv.smear(S, r1, r2 + 3, a0, a1, fn, z=-3)
        for j in range(4):
            a = a0 + (a1 - a0) * (0.25 + 0.18 * j)
            r = r1 + (r2 - r1) * (0.55 + 0.3 * h2(j, 2, 3))
            x, y = S[0] + r * math.cos(a), S[1] + r * math.sin(a) + 8 + 5 * j
            for dx, dy, c in ((0, 0, G[3]), (1, 0, G[4]), (0, 1, G[2]), (1, 1, CRI[6]), (0, -1, CRI[5])):
                cv.put(int(x) + dx, int(y) + dy, c, -1, False)


# =============================================================================
# G-B 붕산(崩山) 부유 암괴 — 넓어진 날이 바위 덩이(보로노이 칸)로 쪼개져 벌어지고 틈으로 황토빛이 터진다
# =============================================================================
class GB(GSBase):
    key, name, title = "G-B", "산붕", "붕산 부유 암괴: 넓어진 날이 바위 덩이 20개로 쪼개져 벌어지고, 틈마다 황토빛이 터져 나온다"
    form = "날 90×폭 9 → 112×폭 최대 26의 '바위 날'. 날 전체가 덩이 20개(보로노이 칸)로 갈라져 칼등 쪽·날 쪽으로 1~4도트씩 벌어져 뜸(바깥 덩이일수록 더 멀리) · 칼끝은 떨어져 나간 화살촉 바위"
    color = "녹슨 쇠 → 흑갈 바위(G2·WD3·황토 OCH2~5) + 틈의 황토빛(4층 OCH6~11 → X1). 전반(0~45%) 덩이 경계 금이 코등이→칼끝으로 빛나며 그어지고, 후반(45~100%) 날이 넓어지며 덩이가 벌어져 틈이 빛으로 참. 순환 8프레임 = 덩이가 손잡이→칼끝 순서로 파도처럼 들썩, 틈 빛 OCH8 ↔ X1 맥동"
    fx = "궤적 = 앞선 각도 2곳에 바위 날 실루엣 잔상(OCH2·OCH3 성긴 점) + 바깥 테 가는 황토 호 1줄 + 흙먼지 점"
    box = (-26, 118, -24, 24)
    reach = 114
    tn = 8
    bg = [OCH[0], OCH[1]]
    ramps_after = [("바위 G2·WD3", [G[2], G[3], K.WD[3]]), ("황토 OCH", OCH), ("백열", [X1])]
    _memo = {}

    def hw(self, u, sg, Lc):
        un = (u - 8) / (Lc - 8)
        prof = 0.3 + 0.7 * math.sin(math.pi * clamp(un * 0.8 + 0.12)) ** 0.7
        w = 4.5 + sg * 9.0 * prof
        if un > 0.72:
            w *= max(0.0, 1 - (un - 0.72) / 0.28) ** 0.8
        return w

    def cells(self, f, sg):
        key = (round(sg, 4), f.t % self.tn, f.p >= 1)
        if key in self._memo:
            return self._memo[key]
        Lc = 93 + 12 * sg
        seeds = []
        k = 0
        for i in range(10):
            un = (i + 0.5) / 10
            for side in (-1, 1):
                vn = side * (0.45 + 0.35 * h2(i, side, 66))
                su = 8 + (Lc - 8 - 6) * (un + 0.04 * (h2(i, side, 67) - 0.5))
                seeds.append([su, vn, k])
                k += 1
        out = []
        for su, vn, k in seeds:
            sv = vn * self.hw(su, sg, Lc)
            bob = 1.0 * math.sin(2 * math.pi * (f.ph - su / 110)) * (1 if f.p >= 1 else 0)
            lift = (0.6 + 2.8 * abs(vn)) * sg + bob * sg
            out.append((su, sv, 0.0, math.copysign(lift, vn), k))
        tu = Lc + 3 + 6 * sg
        self._memo[key] = (out, Lc, tu)
        return self._memo[key]

    def which(self, u, v, cl, sg, Lc):
        """(칸 번호, 경계까지 여유) | (None, None)."""
        best = None
        for su, sv, du, dv, k in cl:
            pu, pv = u - du, v - dv
            lim = self.hw(pu, sg, Lc) * (1 - sg * (0.2 * h2(k, 7, 68) + 0.08 * h2(k, int(pu // 3), 69)))
            if pu < 8 or pu > Lc or abs(pv) > lim:
                continue
            d1 = (pu - su) ** 2 + ((pv - sv) * 1.4) ** 2
            if d1 > 260:
                continue
            ok = True
            d2 = 1e9
            for su2, sv2, _, _, k2 in cl:
                if k2 == k:
                    continue
                dd = (pu - su2) ** 2 + ((pv - sv2) * 1.4) ** 2
                if dd < d1:
                    ok = False
                    break
                d2 = min(d2, dd)
            if ok:
                m = math.sqrt(d2) - math.sqrt(d1)
                if best is None or m > best[1]:
                    best = (k, m, pv - sv)
        return best

    def px(self, u, v, x, y, f):
        hilt = B.gs_hilt(u, v)
        if u < 3 and hilt:
            return (hilt, True)
        sg = smooth(0.45, 1.0, f.p)
        ghost = getattr(f, "ghost", False)
        if ghost:
            sg = 1.0
        cl, Lc, tu = self.cells(f, sg)
        cb = B.gs_blade(u, v, f.glow)
        if 3 <= u < 8:
            return (cb, True) if cb and not ghost else None
        # 칼끝 화살촉 바위
        if sg > 0.1:
            poly = [(tu - 7, -4), (tu - 2, -5), (tu + 9, 0), (tu - 2, 5), (tu - 7, 4), (tu - 5, 0)]
            if in_poly(u, v, poly):
                if ghost:
                    return (OCH[3] if (x + y) % 2 else OCH[2], False)
                return (OCH[9] if u > tu + 5 else OCH[4] if v < -1.5 else OCH[2] if v < 1.5 else G[2], True)
        w = self.which(u, v, cl, sg, Lc)
        if ghost:
            return (OCH[3] if (x + 2 * y) % 5 == 0 else OCH[2], False) if (w and w[1] > 1.2 and (x + y) % 2 == 0) else None
        inside = 8 <= u <= Lc and abs(v) <= self.hw(u, sg, Lc)
        un = clamp((u - 8) / (Lc - 8))
        stc = stage(min(1.0, f.p / 0.45), un + 0.05 * h2(x, y, 64))
        if w and w[1] > (0.9 if stc > 0 else -1):
            k, m, dvv = w
            if stc < 0 or sg < 0.03:
                return (cb, True) if cb else (G[5], True)
            tone = h2(k, 1, 65)
            if m < 1.9:
                return (OCH[6] if dvv * (1 if cl[k][3] < 0 else -1) < 0 else OCH[4], True)    # 틈 빛을 받는 테
            if dvv < -2.0:
                return (OCH[4] if tone > 0.5 else OCH[3], True)
            if dvv < 1.0:
                return (OCH[3] if tone > 0.6 else K.WD[3] if tone > 0.3 else OCH[2], True)
            return (G[3] if tone > 0.5 else G[2], True)
        if inside or (w and stc >= 0):
            if stc < 0:
                return (cb, True) if cb else None
            if stc == 0:
                return (X1, False)
            glow = 0.6 + 0.4 * math.sin(2 * math.pi * (f.ph - u / 100))
            core = abs(v) < 1.1 + 1.5 * sg
            if core and (glow > 0.88 or f.glow):
                return (X1, False)
            return (OCH[10] if core else OCH[8] if glow > 0.7 else OCH[7], False)
        return None

    def extra(self, cv, g, ang, f):
        if f.p < 0.7:
            return
        for k in range(10):
            u = 12 + 9 * k + 4 * h2(k, 3, 1)
            v = (15 + 6 * h2(k, 4, 1)) * (1 if k % 2 else -1)
            x, y = self.W(g, ang, u, v, f)
            cv.put(x + ((f.t + k) % 3) - 1, y - (f.t + k * 2) % 4, OCH[5] if k % 2 else OCH[8], 1, False)

    def trail(self, cv, S, r1, r2, a0, a1, f, g, ang):
        def arc(tn, rn, x, y):
            q = crescent(tn, rn, x, y, head=0.08, tail=0.03, seed=71)
            if q is None:
                return None
            return OCH[9] if tn > 0.7 else OCH[6] if tn > 0.35 else OCH[4]
        cv.smear(S, r1, r2 + 3, a0, a1, arc, z=-3)
        for j, frac in enumerate((0.62, 0.3)):
            da = (a0 - a1) * frac
            gg = rot_about(g, S, da)
            ff = K.F(p=1.0, t=f.t, tn=f.tn, flip=f.flip)
            ff.ghost = True
            cv.shape(gg, ang + da, self.box, lambda u, v, x, y, ff=ff: self.px(u, v * ff.flip, x, y, ff), z=-4 - j)
        for k in range(14):
            a = a0 + (a1 - a0) * h2(k, 1, 72)
            r = r1 + (r2 - r1) * h2(k, 2, 72)
            cv.put(S[0] + r * math.cos(a), S[1] + r * math.sin(a), OCH[5] if k % 2 else OCH[3], -2, False)


# =============================================================================
# G-C 산신(山神) 비취 결정 — 날이 비취로 굳고 등날에서 수정 봉우리가 솟는다
# =============================================================================
class GC(GSBase):
    key, name, title = "G-C", "산붕", "산신 비취 결정: 대검이 비취로 굳고 등날에서 수정 봉우리 6개가 산맥처럼 솟는다"
    form = "날 90 → 104(칼끝이 긴 수정 촉), 등날에 육각 수정 봉우리 6개(높이 10~27, 기울기 제각각 = 산맥) + 날 아래 작은 수정 2개 → 실루엣 폭 9 → 최대 36"
    color = "녹슨 쇠 → 비취(3층 청록 TEAL2~11) + 녹 맥(2층 GRN). 수정이 코등이에서 칼끝으로 기어가듯 굳고(앞줄 TEAL11), 봉우리는 자기 차례에 솟음(25~100%). 순환 8프레임 = 봉우리 색이 청록 → 녹으로 한 개씩 넘어가는 물결 + 흰 반사 띠(X0)가 날을 가로질러 훑음"
    fx = "궤적 = 깎인 면(삼각 면 조각마다 청록 명도가 다름), 머리 바깥 테 X0, 꼬리는 면 조각이 통째로 빠져 수정 파편처럼 흩어짐"
    box = (-26, 108, -30, 16)
    reach = 106
    tn = 8
    bg = [TEAL[0], TEAL[1]]
    ramps_after = [("비취 TEAL", TEAL), ("녹 GRN 5~9", GRN[5:10]), ("백열", [X0])]
    CR = [(14, 10, 6, -1.15), (27, 19, 8, -0.95), (43, 27, 9, -0.72), (58, 20, 8, -0.55), (72, 15, 7, -0.85), (84, 10, 5, -0.45),
          (36, 9, 5, 1.0), (66, 11, 5, 0.75)]

    def glint(self, u, v, f):
        pos = -12 + f.ph * 140
        return abs(u + 0.6 * v - pos) < 1.3

    def crystal(self, u, v, f, x, y):
        for k, (uc, L, w, lean) in enumerate(self.CR):
            sideTop = lean < 0
            thr = 0.25 + 0.5 * (uc / 93)
            gr = smooth(thr, thr + 0.3, f.p)
            if gr < 0.05:
                continue
            Lk = L * gr
            ru, rv = uc, (-3.2 if sideTop else 3.2)
            dx, dy = u - ru, v - rv
            ca, sa = math.cos(lean), math.sin(lean)
            a = dx * ca + dy * sa
            b = -dx * sa + dy * ca
            if a < -1 or a > Lk:
                continue
            wb = w / 2 if a < 0.72 * Lk else w / 2 * (Lk - a) / (0.28 * Lk)
            if abs(b) > wb:
                continue
            green = math.cos(2 * math.pi * (f.ph - k / 6)) > 0.55 and f.p >= 1
            R = GRN if green else TEAL
            if a > Lk - 2.2 and gr > 0.9:
                return X0
            if self.glint(u, v, f) and f.p >= 1:
                return X0
            if abs(b) > wb - 0.9:
                return R[3]
            if b < -w / 6:
                return R[10] if not green else R[9]
            if b <= w / 6:
                return R[8] if not green else R[7]
            return R[5]
        return None

    def px(self, u, v, x, y, f):
        hilt = B.gs_hilt(u, v)
        if u < 3 and hilt:
            return (hilt, True)
        sg = smooth(0.4, 1.0, f.p)
        Lc = 93 + 13 * sg
        cb = B.gs_blade(u, v, f.glow)
        c = self.crystal(u, v, f, x, y)
        if c:
            return (c, True)
        if u < 9:
            return (cb, True) if cb else None
        r = B.gs_lane(u, v, u1=Lc, hw=4.5 + 0.5 * sg)
        if r is None and cb is None:
            return None
        if r is None:
            return (cb, True)
        un, dn, w = r
        st = stage(f.p, 0.6 * un + 0.05 * h2(x, y, 81))
        if st < 0:
            return (cb, True) if cb else None
        if st == 0:
            return (TEAL[11], False)
        if self.glint(u, v, f) and f.p >= 1:
            return (X0 if f.glow else TEAL[11], True)
        if f.glow and dn < 0.14:
            return (X0, True)
        if abs(v - 1.4 * math.sin(u * 0.23)) < 0.55:
            return (GRN[7], True)
        if dn < 0.14:
            return (TEAL[9], True)
        if abs(v) < 0.5:
            return (TEAL[7], True)
        return (TEAL[6] if dn < 0.4 else TEAL[4] if dn < 0.75 else TEAL[2], True)

    def extra(self, cv, g, ang, f):
        if f.p < 0.85:
            return
        for k in range(5):
            u = 20 + 18 * k
            v = -26 + 4 * h2(k, 3, 2) - ((f.t + k * 3) % 8)
            x, y = self.W(g, ang, u, v, f)
            c = TEAL[10] if (f.t + k) % 4 == 0 else TEAL[6]
            cv.put(x, y, c, 1, False)
            cv.put(x + 1, y + 1, TEAL[4], 1, False)

    def trail(self, cv, S, r1, r2, a0, a1, f, g, ang):
        span = abs(a1 - a0) or 1e-6
        shades = [TEAL[4], TEAL[6], TEAL[8], TEAL[10], TEAL[5], TEAL[7]]

        def fn(tn, rn, x, y):
            q = crescent(tn, rn, x, y, head=0.55, seed=91, broken=0.0)
            if q is None:
                return None
            # 삼각 면: 각 띠(tn) × 반지름 띠(q) 칸을 대각선으로 둘로 나눔
            ti, qi = int(tn * 9), int(q * 3)
            ft, fq = tn * 9 - ti, q * 3 - qi
            tri = 0 if ft + fq < 1 else 1
            hid = h2(ti * 2 + tri, qi, 92)
            if tn < 0.4 and hid > tn * 2.2:
                return None
            if q > 0.92 and tn > 0.6:
                return X0
            base = 2 + int(tn * 2.5) + (1 if q > 0.6 else 0)
            return shades[min(5, base + (1 if hid > 0.6 else 0)) % 6] if hid < 0.85 else TEAL[9]
        cv.smear(S, r1, r2 + 3, a0, a1, fn, z=-3)


CONCEPTS = [GA(), GB(), GC()]


# =============================================================================
# G-A2 핏빛 거암검 (60라운드 Q15 결정: G-A 형태 + 용암 대신 '적을 죽이며 쌓인 피가 균열에서 터져 나옴')
# =============================================================================
BLOOD_FILL = [0.12, 0.26, 0.42, 0.58, 0.74, 0.9, 1.0, 0.72, 0.46, 0.24]     # 순환 10프레임: 차오름 0~5 → 터짐 6 → 빠짐 7~9


class GBlood(GA):
    key, name, title = "G-A2", "산붕", "핏빛 거암검: 부푼 바위 판의 균열에 베어 낸 피가 차오르다가 넘쳐 터져 나온다"
    form = "G-A 와 같음 — 날 90×폭 9 → 108×최대 19의 들쭉날쭉한 바위 판 · 등날 바위 가시 4개 · 갈래 균열 5줄 · 깨진 바위 촉. 균열은 비어 있으면 검은 틈, 차면 피"
    color = ("녹슨 쇠 → 검붉은 현무암(G2~G7 + 마른 피 얼룩 CRI2) + 균열 속 피(진홍 CRI3~7, 젖은 반사 X1 점). 전환: 균열이 먼저 갈라져 검게 열리고(5~45%) 피가 스미며 판이 부풂(35~100%). "
             "순환 10프레임(80ms) = 피가 손잡이→칼끝으로 균열을 채움(0~5) → 넘쳐 터짐(6: 균열 끝마다 피 줄기·방울 분출) → 흘러내리며 빠짐(7~9, 날 아래로 방울)")
    fx = "궤적 = 진홍 초승달(바깥 테 CRI7 + 젖은 반사 X1 점) · 머리 바깥으로 튀는 핏방울 14개 · 안쪽은 성긴 피 안개(CRI1·CRI2) · 궤적 아래로 떨어지는 방울"
    tn = 10
    loop_ms = 80
    hero_t = 6
    bg = [CRI[0], CRI[1]]
    ramps_after = [("현무암 G2~G7", G[2:8]), ("피 CRI 1~7", CRI[1:8]), ("젖은 반사", [X1])]
    ENDS = [(43, -8, -1), (61, 5.5, 1), (82, -7, -1), (97, 5, 1), (104, 0.2, 0)]   # 균열 끝(설계 u, v, 바깥 방향)

    def fill(self, f):
        if f.p < 1:
            return 0.55 * smooth(0.2, 0.9, f.p)
        return BLOOD_FILL[f.t % 10]

    def burst(self, f):
        return f.p >= 1 and (f.t % 10) == 6

    def blood(self, u, d, f, glow, x=0, y=0, Lc=111):
        us = (u - 9) / max(1.0, Lc - 9)
        fl = self.fill(f)
        if us > fl:
            return G[1] if d < 0.75 else G[2]                      # 빈 균열(검은 틈)
        if abs(us - fl) * Lc < 1.6 and fl < 1:
            return CRI[7]                                          # 차오르는 앞줄
        if d < 0.75:
            if (glow or self.burst(f)) and h2(x, y, 231) > 0.82:
                return X1
            return CRI[7] if (glow or self.burst(f)) else CRI[6] if h2(x // 2, y // 2, 232) > 0.35 else CRI[5]
        return CRI[3]

    def px(self, u, v, x, y, f):
        hilt = B.gs_hilt(u, v)
        if u < 3 and hilt:
            if f.p > 0.6 and 0 <= u < 3 and abs(v - 0.3 * u) < 0.6:
                return (CRI[5], True)
            return (hilt, True)
        sg = smooth(0.35, 1.0, f.p)
        Lc = 93 + 18 * sg
        cb = B.gs_blade(u, v, f.glow)
        sl = self.slab(u, v, sg, Lc)
        if cb is None and sl is None:
            return None
        un = sl[0] if sl else clamp((u - 3) / 90)
        if u >= 9:
            d = self.fiss(u, v, sg, Lc)
            if d < (2.3 if self.burst(f) else 1.6):
                stf = stage(f.p, 0.05 + 0.4 * un)
                if stf == 0:
                    return (CRI[7], False)
                if stf > 0:
                    return (self.blood(u, d, f, f.glow, x, y, Lc), True)
            elif d < 3.2 and f.p > 0.5 and h2(x, y, 233) > 0.72:
                return (CRI[2], True)                              # 균열 둘레 마른 피
        st = stage(f.p, 0.3 + 0.35 * un + 0.06 * h2(x, y, 9))
        if st < 0 or sl is None:
            return (cb, True) if cb else None
        if st == 0:
            return (G[6], True)
        un, dn, wt, wb = sl
        if v < -wt + 1.1:
            lv = 7
        elif dn < 0.3:
            lv = 5
        elif dn < 0.6:
            lv = 4
        elif dn < 0.85:
            lv = 3
        else:
            lv = 2
        if h2(x // 2, y // 2, 13) > 0.82:
            lv -= 1
        return (G[max(1, lv)], True)

    def extra(self, cv, g, ang, f):
        if f.p < 0.7:
            return
        sg = smooth(0.35, 1.0, f.p)
        sc = (93 + 18 * sg - 3) / 90.0
        cyc = f.t % 10
        for k, (eu, ev, side) in enumerate(self.ENDS):
            u0 = 3 + (eu - 3) * sc
            if self.burst(f) or f.glow:
                for m in range(10):
                    dist = 3 + 2.0 * m + 3 * h2(k, m, 241)
                    lat = (h2(k, m, 242) - 0.5) * (4 + m)
                    if side == 0:
                        uu, vv = u0 + dist, lat * 0.6
                    else:
                        uu, vv = u0 + lat * 0.5, ev + side * dist
                    x, y = self.W(g, ang, uu, vv * f.flip, f)
                    y += 0.08 * dist * dist
                    c = X1 if m == 0 and h2(k, 1, 243) > 0.5 else CRI[7] if m < 2 else CRI[6] if m < 5 else CRI[4]
                    cv.put(x, y, c, 2, False)
                    if m < 4:                                   # 굵은 피 줄기(앞쪽 방울은 2~3도트)
                        x2, y2 = self.W(g, ang, uu - (0 if side else 1.2), (vv - side * 1.2) * f.flip, f)
                        cv.put(x2, y2 + 0.08 * dist * dist, CRI[6], 2, False)
                        cv.put(x + 1, y, CRI[5], 2, False)
            elif cyc >= 7 and side > 0:
                x, y = self.W(g, ang, u0, (ev + 1) * f.flip, f)
                yy = y + 2 + (cyc - 7) * 4 + 2 * (k % 2)
                cv.put(x, yy, CRI[6], 2, False)
                cv.put(x, yy + 1, CRI[4], 2, False)
        if cyc in (3, 4, 5) and f.p >= 1:
            for k, u in enumerate((40, 70)):
                x, y = self.W(g, ang, u * sc, 7 * f.flip, f)
                cv.put(x, y + 1 + (cyc - 3) * 2, CRI[5], 2, False)

    def trail(self, cv, S, r1, r2, a0, a1, f, g, ang):
        def fn(tn, rn, x, y):
            q = crescent(tn, rn, x, y, head=0.58, seed=251)
            if q is None:
                if rn > 0.2 and rn < 1 and tn > 0.15 and h2(x, y, 252) > 0.93:
                    return CRI[2] if h2(x, y, 253) > 0.5 else CRI[1]       # 피 안개
                return None
            q = q + 0.1 * (vnoise(x * 0.3 + y * 0.12, 6) - 0.5)
            if q > 0.9:
                return X1 if (tn > 0.6 and h2(x, y, 254) > 0.75) else CRI[7]
            if q > 0.66:
                return CRI[6] if tn > 0.3 else CRI[5]
            if q > 0.42:
                return CRI[4]
            if q > 0.22:
                return CRI[2]
            return CRI[1] if h2(x // 2, y // 2, 255) > 0.5 else None
        cv.smear(S, r1, r2 + 3, a0, a1, fn, z=-3)
        for j in range(14):
            t = 0.45 + 0.55 * h2(j, 1, 256)
            a = a0 + (a1 - a0) * t
            r = r2 + 3 + 12 * h2(j, 2, 256) * t
            x, y = S[0] + r * math.cos(a), S[1] + r * math.sin(a) + 3 * (1 - t) * j % 5
            c = X1 if j % 5 == 0 else CRI[6] if j % 2 else CRI[4]
            cv.put(x, y, c, -1, False)
            if j % 3 == 0:
                cv.put(x + 1, y, CRI[5], -1, False)
                cv.put(x, y + 1, CRI[4], -1, False)
        for j in range(5):
            a = a0 + (a1 - a0) * (0.3 + 0.13 * j)
            r = r1 + (r2 - r1) * (0.6 + 0.3 * h2(j, 4, 257))
            x, y = S[0] + r * math.cos(a), S[1] + r * math.sin(a) + 6 + 4 * j
            cv.put(x, y, CRI[6], -1, False)
            cv.put(x, y + 1, CRI[4], -1, False)


BLOOD = GBlood()
