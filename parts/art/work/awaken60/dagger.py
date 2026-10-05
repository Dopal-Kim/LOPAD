"""단검 — 최종 각성 '백귀' 시안 3개."""
import math

import base as B
import kit60 as K
from kit60 import G, A, VIO, TEAL, CRI, SIL, X0, X1, h2, vnoise, clamp, smooth, stage
from concept import Concept, crescent

POSES = [
    dict(name="대기 (역수로 쥔 단검)", ws="dagger_carry_idle", wi=0, bs="player_idle_free", bi=0, erase=4.5, t=1, flip=-1),
    dict(name="휘두르기 1 — 3타 당겨 듦", ws="dagger_combo3", wi=0, bs="player_dagger_combo3", bi=0, erase=4.5, t=3, flip=-1),
    dict(name="휘두르기 2 — 3타 베기(판정) + 궤적", ws="dagger_combo3", wi=3, bs="player_dagger_combo3", bi=3, erase=4.5, glow=True, t=4,
         trail=dict(S=(112, 104), sweep=100)),
]


class DBase(Concept):
    weapon, weapon_ko = "dagger", "단검"
    hero_ang = -0.62
    trail_in = 2
    ramps_before = [("재 G3~G7", G[3:8]), ("호박 A", A), ("붕대 PL", K.PL)]


# =============================================================================
# D-A 귀화(鬼火) — 날이 보랏빛 도깨비불로 타오르고 불 속에 얼굴이 비친다
# =============================================================================
class DA(DBase):
    key, name, title = "D-A", "백귀", "귀화: 단검이 보랏빛 도깨비불에 휩싸여 날 길이 두 배의 불꽃 칼이 되고, 불 속에 귀신 얼굴이 어른거린다"
    form = "날 24 → 불꽃 포함 48도트, 불꽃이 칼등 쪽으로 휘어 흐르는 갈고리 모양(폭 최대 15) · 끝 1/3은 혀처럼 갈라져 떨어져 나감 · 불 속 얼굴 2개(눈·입 3픽셀)"
    color = "재·호박 → 보라 도깨비불(5층 VIO) + 청록 불끝(3층 TEAL). 날은 칼끝부터 해시 문턱으로 타들어 가듯(용해) 보라로 바뀌고 불꽃이 손잡이 쪽에서 피어 커짐(30~100%). 순환 6프레임 = 불혀가 일렁이고, 청록 띠가 불꽃 밑동→끝으로 타고 올라감(색 순환)"
    fx = "궤적 = 가장자리가 불혀처럼 일렁이는 보라 초승달, 꼬리는 청록 불티로 흩어지고 도깨비 얼굴 잔상 1개가 궤적 머리에 남음"
    box = (-11, 52, -22, 10)
    reach = 48
    tn = 6
    loop_ms = 80
    bg = [VIO[0], VIO[1]]
    ramps_after = [("보라 VIO", VIO), ("청록 TEAL 4~11", TEAL[4:12]), ("백열", [X1])]

    def flame(self, u, v, f, x, y):
        sg = smooth(0.3, 1.0, f.p)
        if sg < 0.03:
            return None
        Lf = 26 + 22 * sg
        if u < 0 or u > Lf:
            return None
        s = u / Lf
        cf = -0.5 - 4.5 * s ** 1.5 * sg
        core = (1.8 + 3.0 * math.sin(math.pi * min(1.0, s * 1.2)) ** 0.8) * (0.5 + 0.5 * sg) * (0.85 + 0.3 * vnoise(u * 0.4 - f.t * 1.2, 3))
        tong = 0.0
        for k in range(5):
            uk = ((k * 0.21 + f.t * 0.05) % 1.0) * Lf * 0.92 + 3
            hk = (3.0 + 3.0 * h2(k, 1, 7)) * sg * (0.35 + 0.65 * s)
            dd = u - uk
            if -3.0 <= dd <= 1.2:
                tong = max(tong, hk * (1 - abs(dd + 0.9) / 2.1))
        hb, he = core + tong, core * 0.6
        d = v - cf
        if d < -hb or d > he:
            return None
        if s > 0.62 and vnoise(u * 0.55 + v * 0.35 - f.t * 1.3, 5) < (s - 0.62) * 1.9:
            return None
        hw = hb if d < 0 else he
        q = 1 - abs(d) / hw
        # 얼굴(눈 2 · 입 1)
        if f.t % 3 != 2:
            for fu, fv in ((0.48, -1.0), (0.74, -2.0)):
                cu, cv = fu * Lf, -1.0 - 6.0 * fu ** 1.6 * sg + fv
                if abs(u - cu) < 0.6 and abs(abs(v - cv) - 1.5) < 0.55:
                    return VIO[1]
                if abs(u - (cu + 2.2)) < 0.6 and abs(v - cv) < 0.6:
                    return VIO[1]
        R = TEAL if ((s * 1.6 - f.ph) % 1.0) < 0.26 else VIO
        if q > 0.74:
            return X1 if (f.glow and R is VIO) else R[11]
        if q > 0.5:
            return R[9]
        if q > 0.27:
            return R[7]
        return R[4]

    def px(self, u, v, x, y, f):
        hilt = B.dagger_hilt(u, v)
        if hilt and u < 1.5:
            return (hilt, True)
        r = B.d_lane(u, v)
        if r:
            un, dn, w = r
            st = stage(f.p, 0.45 * (1 - un) + 0.45 * h2(x, y, 101))
            if st < 0:
                return (B.dagger_blade(u, v, f.glow), True)
            if st == 0:
                return (VIO[11], False)
            if un > 0.84:
                return (X1 if f.glow else VIO[10], True)
            return (VIO[8] if dn > 0.75 else VIO[4] if dn > 0.45 else VIO[3] if dn > 0.2 else VIO[2], True)
        fl = self.flame(u, v, f, x, y)
        if fl:
            return (fl, False)
        return (hilt, True) if hilt else None

    def extra(self, cv, g, ang, f):
        if f.p < 0.8:
            return
        for k in range(5):
            u = 10 + 8 * k
            v = -10 - ((f.t * 3 + k * 4) % 9)
            x, y = self.W(g, ang, u, v, f)
            cv.put(x, y - ((f.t + k) % 3), TEAL[9] if k % 2 else VIO[9], 2, False)

    def trail(self, cv, S, r1, r2, a0, a1, f, g, ang):
        def fn(tn, rn, x, y):
            n = vnoise(tn * 18 + f.t * 1.7, 7) - 0.5
            q = crescent(tn, rn + 0.12 * n, x, y, head=0.55, seed=111, broken=0.45)
            if q is None:
                return None
            R = TEAL if tn < 0.35 else VIO
            if q > 0.86:
                return X1 if tn > 0.7 else R[10]
            if q > 0.6:
                return R[8]
            if q > 0.3:
                return R[6]
            return R[3]
        cv.smear(S, r1, r2 + 4, a0, a1, fn, z=-3)
        # 머리에 남는 얼굴 잔상
        a = a0 + (a1 - a0) * 0.82
        r = r2 - 5
        x, y = int(S[0] + r * math.cos(a)), int(S[1] + r * math.sin(a))
        for dx, dy in ((-1, 0), (1, 0), (0, 2)):
            cv.put(x + dx, y + dy, VIO[1], 3, False)


# =============================================================================
# D-B 귀조(鬼爪) 세 갈래 — 날이 귀신 손톱 세 개로 갈라져 부채처럼 펼쳐진다
# =============================================================================
class DB(DBase):
    key, name, title = "D-B", "백귀", "귀조 세 갈래: 단검이 세 갈래 귀신 손톱으로 갈라져 부채처럼 펼쳐지고 하나씩 깜박인다"
    form = "날 24 → 손톱 3개(가운데 38 · 양옆 34도트), ±18° 부채로 벌어짐, 끝이 날 쪽으로 갈고리처럼 굽음 · 밑동에 귀신 손 마디 3개 → 실루엣 폭 7 → 최대 26"
    color = "재·호박 → 창백한 청록 귀기(3층 TEAL) + 은(8층 SIL) 밑동. 전반 손잡이→칼끝 X1 쓸기, 후반(40~100%) 세 갈래가 펼쳐짐. 순환 6프레임 = 손톱 1→2→3 차례로 번쩍(X1 날선)했다가 다음 프레임에 흐려짐(TEAL3~5 '사라졌다 나타남')"
    fx = "궤적 = 손톱 끝 3개가 긋는 평행 할퀴기 3줄(가늘고 날카로움, 머리 X1), 줄 사이는 비어 있음"
    box = (-11, 44, -16, 16)
    reach = 40
    tn = 6
    loop_ms = 70
    bg = [TEAL[0], TEAL[1]]
    ramps_after = [("청록 TEAL", TEAL), ("은 SIL 4~8", SIL[4:9]), ("백열", [X1])]

    def claw(self, u, v, f, idx, sg):
        th = idx * 0.31 * sg
        L = 24.5 + (8 + 4 * (idx == 0)) * sg
        du, dv = u - 2, v
        c, s_ = math.cos(-th), math.sin(-th)
        uu, vv = du * c - dv * s_, du * s_ + dv * c
        if uu < 0 or uu > L:
            return None
        s = uu / L
        cc = 3.0 * s ** 2.2 * sg + 0.8 * s
        hw = (3.0 if sg < 0.3 else 2.4) * (1 - s) ** 0.65 + 0.35
        d = vv - cc
        if abs(d) > hw:
            return None
        return s, (d + hw) / (2 * hw)

    def px(self, u, v, x, y, f):
        hilt = B.dagger_hilt(u, v)
        sg = smooth(0.4, 1.0, f.p)
        if sg > 0.05 and -0.5 <= u <= 5.5:
            for k in (-1, 0, 1):
                if math.hypot(u - 2.5, v - k * 3.4 * sg) <= 2.1:
                    return (TEAL[5] if v < k * 3.4 * sg else TEAL[3], True)
        if hilt and u < 1.5:
            return (hilt, True)
        for idx in (0, -1, 1):
            r = self.claw(u, v, f, idx, sg)
            if not r:
                continue
            s, dn = r
            st = stage(f.p, 0.5 * s + 0.05 * h2(x, y, 121))
            if st < 0:
                cb = B.dagger_blade(u, v, f.glow)
                if cb:
                    return (cb, True)
                continue
            if st == 0:
                return (X1, False)
            ph = (f.t % 6)
            flash = f.p >= 1 and ph == 2 * (idx + 1)
            dim = f.p >= 1 and ph == 2 * (idx + 1) + 1
            if s < 0.14:
                return (SIL[7] if dn > 0.5 else SIL[4], True)
            if dn > 0.78:
                return (X1 if (flash or f.glow) else TEAL[10] if not dim else TEAL[5], True)
            lv = 8 if dn > 0.5 else 6 if dn > 0.22 else 4
            lv = lv + 2 if flash else lv - 3 if dim else lv
            return (TEAL[max(2, min(11, lv))], True)
        return (hilt, True) if hilt else None

    def trail(self, cv, S, r1, r2, a0, a1, f, g, ang):
        for k, off in enumerate((0, 6, 12)):
            def fn(tn, rn, x, y, k=k):
                if tn < 0.3 and h2(x, y, 131 + k) > tn * 3.3:
                    return None
                if tn > 0.9:
                    return X1
                return TEAL[10] if tn > 0.65 else TEAL[7] if tn > 0.4 else TEAL[4]
            rr = r2 + 2 - off
            cv.smear(S, rr - 0.8 - 0.8 * (k == 0), rr + 0.6, a0 + (a1 - a0) * 0.06 * k, a1 - (a1 - a0) * 0.02 * k, fn, z=-3)


# =============================================================================
# D-C 백귀야행(百鬼夜行) — 핏빛 단검 둘레를 보랏빛 혼령 단검 3자루가 돈다
# =============================================================================
class DC(DBase):
    key, name, title = "D-C", "백귀", "백귀야행: 핏빛으로 물든 단검 둘레를 혼령 단검 3자루가 궤도를 그리며 돈다"
    form = "날 24 → 30(칼등에 톱니 3개) + 혼령 단검 3자루(각 18도트)가 날 가운데를 중심으로 가로 20 · 세로 9 타원 궤도를 돎 → 실루엣이 무기 둘레 지름 ~44 영역으로 커짐"
    color = "재·호박 → 칼 = 핏빛 진홍(7층 CRI2~7), 혼령 = 보라(5층 VIO). 각성 순간 혼령이 한 자루씩 칼에서 벗겨져 나옴(35·55·75%). 순환 12프레임 = 궤도 한 바퀴, 혼령이 앞쪽(카메라 쪽)을 지날 때 청록(3층 TEAL)으로 번쩍, 뒤쪽은 어둡게(VIO2~5)"
    fx = "궤적 = 가는 핏빛 초승달 + 서로 엇갈리며 꼬이는 보라 혼령 줄 3가닥(물결 반지름)"
    box = (-11, 34, -8, 8)
    reach = 34
    tn = 12
    loop_ms = 60
    bg = [CRI[0], VIO[1]]
    ramps_after = [("진홍 CRI 2~7", CRI[2:8]), ("보라 VIO", VIO), ("청록 TEAL 6~11", TEAL[6:12]), ("백열", [X1])]

    def main(self, u, v, f, x, y):
        sg = smooth(0.2, 0.8, f.p)
        r = B.d_lane(u, v, u1=B.D_U1 + 6 * sg)
        if not r:
            return None
        un, dn, w = r
        st = stage(f.p, 0.5 * un + 0.06 * h2(x, y, 141))
        if st < 0:
            return (B.dagger_blade(u, v, f.glow) or G[4], True)
        if st == 0:
            return (X1, False)
        if dn < 0.22 and un < 0.7 and int(u * 0.5) % 2 == 0 and un > 0.25:
            return None                                    # 칼등 톱니
        if un > 0.86:
            return (X1 if f.glow else CRI[7], True)
        return (CRI[6] if dn > 0.78 else CRI[4] if dn > 0.5 else CRI[3] if dn > 0.22 else CRI[2], True)

    def px(self, u, v, x, y, f):
        hilt = B.dagger_hilt(u, v)
        if hilt and u < 1.5:
            return (hilt, True)
        m = self.main(u, v, f, x, y)
        if m:
            return m
        return (hilt, True) if hilt else None

    def ghost_px(self, u, v, R, lvl):
        hwf = lambda un: 0.62 * B.d_hw(un)  # noqa: E731
        r = B.d_lane(u, v, u1=18, hwf=hwf)
        if r and not all(B.d_lane(u + du, v + dv, u1=18, hwf=hwf) for du, dv in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            return R[2] if lvl > -2 else R[1]
        if not r:
            if -4 <= u < 1.5 and abs(v) <= 1.2:
                return R[max(1, 3 + lvl)]
            return None
        un, dn, w = r
        if un > 0.8:
            return R[min(11, 10 + lvl)]
        return R[max(1, min(11, (8 if dn > 0.6 else 6 if dn > 0.3 else 4) + lvl))]

    def extra(self, cv, g, ang, f):
        if f.p < 0.3:
            return
        for k in range(3):
            em = smooth(0.35 + 0.2 * k, 0.55 + 0.2 * k, f.p)
            if em < 0.02:
                continue
            phi = 2 * math.pi * ((f.ph if f.p >= 1 else 0.0) + k / 3)
            ou, ov = 14 + 20 * math.cos(phi) * em - 14 * (1 - em), 9 * math.sin(phi) * em
            front = math.sin(phi) > 0.55 and f.p >= 1
            back = math.sin(phi) < -0.2
            R = TEAL if front else VIO
            lvl = 1 if front else -3 if back else 0
            c = self.W(g, ang, ou, ov, f)
            a2 = ang + 0.25 * math.sin(phi)
            cv.shape(c, a2, (-5, 20, -5, 5), lambda u, v, x, y, R=R, lvl=lvl: self.ghost_px(u, v * f.flip, R, lvl),
                     z=(2 if not back else -1), solid=False)
            for j in range(1, 4):
                pj = phi - 0.3 * j
                tu, tv = 14 + 20 * math.cos(pj) * em + 9, 9 * math.sin(pj) * em
                tx, ty = self.W(g, ang, tu, tv, f)
                cv.put(tx, ty, VIO[7 - 2 * j] if not front else TEAL[9 - 2 * j], -1, False)

    def trail(self, cv, S, r1, r2, a0, a1, f, g, ang):
        def fn(tn, rn, x, y):
            q = crescent(tn, rn, x, y, head=0.3, seed=151)
            if q is None:
                return None
            return X1 if q > 0.88 and tn > 0.75 else CRI[7] if q > 0.6 else CRI[5] if q > 0.3 else CRI[3]
        cv.smear(S, r1, r2 + 2, a0, a1, fn, z=-3)
        for k in range(3):
            pts = []
            for i in range(25):
                tn = i / 24
                a = a0 + (a1 - a0) * tn
                r = (r1 + r2) / 2 + 2 + 9 * math.sin(2 * math.pi * (tn * 1.3 + k / 3))
                pts.append((S[0] + r * math.cos(a), S[1] + r * math.sin(a)))
            cv.chain(pts, lambda t: 0.35 + 0.6 * t, lambda t, d, x, y, k=k: (VIO[9] if t > 0.75 else VIO[6] if t > 0.4 else VIO[4])
                     if (t > 0.25 or h2(x, y, 161 + k) < t * 4) else None, z=-2)


CONCEPTS = [DA(), DB(), DC()]
