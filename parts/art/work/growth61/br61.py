"""갈래 12종의 1차(a1)·2차(a2 덧붙임 + a2_glow 빛 마스크) 외형.

좌표 = 설계 단위(awaken60 base.py 와 같음): u = 쥔 곳(코등이) → 끝, v = 법선. 칼은 +v = 날선 쪽, 대검·단검은 −v = 화면 위쪽.
화면 길이는 geo.sc 로 줄고(원근), 폭(v)은 그대로 — awaken60 각성 오버레이와 같은 규칙.
가림: 날 길이 안쪽 덧붙임은 원래 무기 픽셀에서 R 도트 안만(몸 뒤로 숨은 구간은 그리지 않음), 끝 너머는 끝이 보일 때만.

층:
  a1   = 원래 날 픽셀 다시 칠하기(재질) + 실루엣을 바꾸는 덧붙임(넓은 날·두꺼운 날·가지 날 등). 셀아웃 INK.
  a2   = a1 위 덧붙임(날 연장·장식 돋음). 고정색(갈래 색). 셀아웃 INK.
  glow = 빛 부분만(회백 X0·G11·G12·G13) — 시스템이 pathTint 로 곱해 길마다 강조색만 달라진다. 셀아웃 없음.
셋째 갈래(만월·광전·백귀·유성)의 a1 은 60라운드 최종 각성 그림(awaken60 prod_overlay)을 그대로 다시 쓴다(광전만 쇠사슬 보정).
"""
import math

import g61 as Z
from g61 import Cv, F, G, A, GRN, TEAL, OCH, VIO, GOLD, CRI, SIL, SL, PL, WD, X0, X1, INK, h2, clamp, smooth
import base as B

PO = Z.PO
KA = PO.KA


def kcurve(u):
    return B.k_curve(min(max(u, B.K_U0), B.K_U1))


def seg_d(px, py, ax, ay, bx, by):
    ex, ey = bx - ax, by - ay
    ll = ex * ex + ey * ey or 1e-9
    k = clamp(((px - ax) * ex + (py - ay) * ey) / ll)
    return math.hypot(px - (ax + ex * k), py - (ay + ey * k)), k


def poly_d(px, py, pts):
    best = (1e9, 0.0)
    tot = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])) or 1
    s0 = 0.0
    for a, b in zip(pts, pts[1:]):
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        d, k = seg_d(px, py, a[0], a[1], b[0], b[1])
        if d < best[0]:
            best = (d, (s0 + k * ln) / tot)
        s0 += ln
    return best


# =============================================================================
# 래스터 도구
# =============================================================================
def fld(ctx, geo, box, fn, R=6.0, tip_u=None, over=False, z=0, gate=True, anchor=None):
    """설계 상자 box = (u0, u1, v0, v1) 안에서 fn(ud, vd, X, Y) → 색 | (색, solid) | None.
    over=False: 원래 무기 픽셀 위는 그리지 않음(ctx.add). over=True(빛 층): 위에도 그림, 셀아웃 없음.
    gate: 끝(tip_u) 너머 = 끝이 보일 때만, 안쪽 = 원래 무기 픽셀 R 도트 안만. anchor=(ud, vd) 이면 그 점이 무기 근처일 때만 전부 그림."""
    u0, u1, v0, v1 = box
    vm = max(abs(v0), abs(v1)) + 1
    near = geo.near_set(R) if gate else None
    if anchor is not None:
        ax, ay = geo.w(*anchor)
        if (int(ax), int(ay)) not in geo.near_set(3.0):
            return
        near = None
    tu = 1e9 if tip_u is None else tip_u
    sc, flip = geo.sc, geo.flip

    def f2(u, v, X, Y):
        ud, vd = u / sc, v * flip
        if not (u0 <= ud <= u1 and v0 <= vd <= v1):
            return None
        if gate and anchor is None:
            if ud > tu:
                if not geo.tip_vis:
                    return None
            elif (X - ctx.ox, Y - ctx.oy) not in near:
                return None
        return fn(ud, vd, X, Y)
    tmp = Cv(ctx.cv.w, ctx.cv.h)
    G0 = (geo.g[0] + ctx.ox, geo.g[1] + ctx.oy)
    tmp.shape(G0, geo.ang, (u0 * sc - 1, u1 * sc + 1, -vm, vm), f2)
    for (x, y), (c, zz, sol) in tmp.px.items():
        if over:
            ctx.cv.put(x, y, c, z, False)
        else:
            ctx.add(x, y, c, z, sol)


def chain_px(ctx, pts, wfn, cfn, over=False, solid=True, z=0):
    """화면(확대 캔버스) 좌표 폴리라인 캡슐."""
    tmp = Cv(ctx.cv.w, ctx.cv.h)
    tmp.chain(pts, wfn, cfn, 0, solid)
    for (x, y), (c, zz, sol) in tmp.px.items():
        if over:
            ctx.cv.put(x, y, c, z, False)
        else:
            ctx.add(x, y, c, z, sol)


def disc_px(ctx, cx, cy, r, cfn, over=False, solid=True, z=0):
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= r:
                c = cfn(d / r if r else 0, x, y)
                if c:
                    if over:
                        ctx.cv.put(x, y, c, z, False)
                    else:
                        ctx.add(x, y, c, z, solid)


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


# =============================================================================
class Branch:
    weapon = "katana"
    bid = "?"
    tn = 8
    loop_ms = 80
    reuse = False
    a1_design = ""
    a2_design = ""
    glow_design = ""

    def recolor(self, cls, L, ud, vd, f):
        return None

    def a1(self, ctx, geo, f):
        pass

    def a2(self, ctx, geo, f):
        pass

    def gl(self, ctx, geo, f):
        pass

    # 칼집 안(칼만) -----------------------------------------------------------
    def sheath_col(self):
        return None

    def s1(self, ctx, geo, f):
        """칼집 금 다시 칠하기 + 작은 문장."""
        col = self.sheath_col()
        for k, p in enumerate(geo.hot):
            ctx.put_orig(p, X1 if (p[0] + p[1] + f.t) % 5 == 0 else col)
        if geo.hot:
            x, y = geo.hot[len(geo.hot) // 2]
            for dx, dy, c in self.emblem():
                ctx.add(x + ctx.ox + dx - 1, y + ctx.oy - 9 + dy, c, 2, True)

    def emblem(self):
        return []

    def s2(self, ctx, geo, f):
        if geo.hot:
            x, y = geo.hot[len(geo.hot) // 2]
            for dx, dy, c in self.emblem2():
                ctx.add(x + ctx.ox + dx - 1, y + ctx.oy - 9 + dy, c, 3, True)

    def emblem2(self):
        return []

    def sg(self, ctx, geo, f):
        if geo.hot:
            x, y = geo.hot[len(geo.hot) // 2]
            c = X0 if f.t % 4 < 2 else G[12]
            ctx.cv.put(x + ctx.ox + 1, y + ctx.oy - 7, c, 4, False)
            ctx.cv.put(x + ctx.ox, y + ctx.oy - 7, G[11], 4, False)


# =============================================================================
# 칼 — 선풍(旋風): 휘어진 넓은 날 + 바람 지느러미 + 손잡이 술
# =============================================================================
class Senpu(Branch):
    weapon, bid = "katana", "senpu"
    a1_design = ("날 55 → 넓고 크게 휜 언월 날(끝 66, 날선 쪽 폭 최대 +5.6 — 끝이 등 쪽으로 쓸려 갈고리처럼 휨) · 등에 뒤로 쓸린 바람 지느러미 2 · "
                 "손잡이 끝 청록 술(바람에 일렁임) / 색: 재 → 청록 강철(3층 TEAL) + 은백 날선, 바람 결 무늬가 칼끝 쪽으로 흐름")
    a2_design = "칼끝 너머 가는 바람 갈고리 연장(+12) · 지느러미 셋째(칼끝 쪽) · 첫 지느러미가 커짐"
    glow_design = "날을 감고 도는 나선 바람 줄 + 넓은 날선 테(맥동) + 칼끝 바람 호 2"

    def sp(self, u):
        return kcurve(u) - 2.5 * clamp((u - 10) / 56) ** 2.5 - B.K_HW

    def W(self, u):
        s = clamp((u - 8) / 58)
        if s < 0.8:
            return 5.2 + 5.6 * math.sin(math.pi * s) ** 0.9 if s > 0 else 5.2
        w8 = 5.2 + 5.6 * math.sin(math.pi * 0.8) ** 0.9
        return w8 * (1 - (s - 0.8) / 0.2) ** 1.1

    def recolor(self, cls, L, ud, vd, f):
        if cls == "edge":
            return X1 if f.glow else SIL[10]
        lv = 7 if L > 120 else 5 if L > 96 else 4 if L > 74 else 2
        return TEAL[lv]

    def blade(self, ud, vd, f, X, Y):
        if ud < 6 or ud > 66:
            return None
        sp = self.sp(ud)
        W = self.W(ud)
        d = vd - sp
        if W < 0.4 or d < 0 or d > W:
            return None
        dn = d / W
        if d > W - 1.0:
            return (X1 if f.glow else SIL[10], True)
        if d > W - 2.0 and dn > 0.6:
            return (SIL[7], True)
        k = (ud * 0.55 - d * 0.9 - f.ph * 7) % 7
        if k < 1.1 and dn > 0.3:
            return (TEAL[9], True)
        if d < 1.0:
            return (TEAL[2], True)
        return (TEAL[4] if dn < 0.45 else TEAL[6], True)

    def fin(self, ud, vd, u0, Hm=6.5):
        if not (u0 - 6 <= ud <= u0 + 4):
            return None
        H = Hm * ((u0 + 4 - ud) / 10) ** 1.6
        o = self.sp(ud) - vd
        if o < -0.5 or o > H:
            return None
        if o > H - 1.1 or ud < u0 - 5:
            return (SIL[8], True)
        return (TEAL[6] if o < H * 0.5 else TEAL[8], True)

    def a1(self, ctx, geo, f):
        def fn(ud, vd, X, Y):
            return self.blade(ud, vd, f, X, Y) or self.fin(ud, vd, 26) or self.fin(ud, vd, 44)
        fld(ctx, geo, (5, 67, -14, 12), fn, R=7.5, tip_u=56)

        def tassel(ud, vd, X, Y):
            if not (-32 <= ud <= -16):
                return None
            t = (-ud - 16) / 16
            c = 2.4 * math.sin(t * 4.2 - 2 * math.pi * f.ph) * t
            w = 1.5 - 0.8 * t
            if abs(vd - c) > w:
                return None
            if ud > -18:
                return (TEAL[3], True)
            return (TEAL[8] if int(t * 8) % 2 == 0 else TEAL[5], True)
        fld(ctx, geo, (-32, -15, -6, 6), tassel, anchor=(-16, 0))

    def a2(self, ctx, geo, f):
        def hook(ud, vd, X, Y):
            if 63 <= ud <= 79:
                t = (ud - 63) / 16
                c = self.sp(66) - 4.0 * t ** 1.6 + 1.0
                w = 1.6 * (1 - t) + 0.3
                if abs(vd - c) <= w:
                    return (SIL[9] if vd < c else TEAL[8], True)
            return self.fin(ud, vd, 56, Hm=5.0) or self.fin(ud, vd, 26, Hm=8.5) and (None if self.fin(ud, vd, 26) else (SIL[6], True))
        fld(ctx, geo, (20, 80, -16, 8), hook, R=9, tip_u=58)

        def ring(ud, vd, X, Y):
            r = math.hypot(ud - 1.2, vd)
            a = math.atan2(vd, ud - 1.2)
            if 5.4 <= r <= 7.0 + 0.8 * math.sin(3 * a + 2 * math.pi * f.ph):
                if (int((a + math.pi) / (2 * math.pi) * 12)) % 4 == 3:
                    return None
                return (TEAL[7] if vd < 0 else TEAL[4], True)
            return None

    def gl(self, ctx, geo, f):
        def fn(ud, vd, X, Y):
            if 8 <= ud <= 66:
                sp, W = self.sp(ud), self.W(ud)
                mid = sp + W * 0.5
                yv = mid + (W * 0.5 + 1.2) * math.sin(ud * 0.32 - 2 * math.pi * f.ph)
                if abs(vd - yv) < 0.65:
                    return X0 if f.glow or abs(((ud * 0.32 - 2 * math.pi * f.ph) % (2 * math.pi)) - math.pi / 2) < 0.4 else G[12]
                if W > 1 and 0 <= vd - sp - W + 1.0 <= 1.0 and int(ud + f.t * 3) % 6 < 3:
                    return G[13]
            if 66 <= ud <= 82:
                for k, r0 in enumerate((6.0, 9.0)):
                    r = math.hypot(ud - 64, vd - self.sp(64))
                    a = math.atan2(vd - self.sp(64), ud - 64)
                    if abs(r - r0 - f.ph * 2) < 0.6 and -1.2 < a < 0.6:
                        return G[11]
            return None
        fld(ctx, geo, (6, 82, -16, 14), fn, R=8, tip_u=58, over=True, z=5)

    def sheath_col(self):
        return TEAL[8]

    def emblem(self):
        return [(0, 0, TEAL[7]), (1, 0, TEAL[9]), (2, 1, TEAL[9]), (2, 2, TEAL[6]), (1, 3, TEAL[5]), (0, 2, TEAL[7])]

    def emblem2(self):
        return [(3, 0, SIL[8]), (4, 1, SIL[9]), (-1, 3, SIL[7]), (-2, 2, SIL[8])]


# =============================================================================
# 칼 — 투구가르기(兜割): 두껍고 곧은 쇳덩이 날 · 끌 같은 칼끝 · 투박한 네모 코등이 · 묵직한 칼자루 머리
# =============================================================================
class Kabuto(Branch):
    weapon, bid = "katana", "kabuto"
    a1_design = ("날 폭 5 → 9.2(등 −5.2 곧은 등줄 · 날선 +4)의 두꺼운 쇳덩이 날, 칼끝은 등 쪽이 긴 끌 모양 · 등에 이 빠진 홈 3 · "
                 "네모난 투박한 쇠 코등이(15×5, 모서리 깎임, 황동 못 2) · 황동 칼자루 머리 / 색: 재 → 검은 무쇠(G2~G7, 망치 자국) + 황동 날선(4층 OCH)")
    a2_design = "코등이 양 끝에서 날을 따라 뻗는 투구 뿔(쿠와가타) 2 · 등에 쇠 징 3"
    glow_design = "날선 전체 백열 줄(맥동이 칼끝으로) + 날 가운데 쪼개는 점선 + 뿔 끝"

    SP, ED, TIP = -5.2, 4.0, 61.0

    def prof(self, ud):
        k = smooth(5, 10, ud)
        return -B.K_HW - (-self.SP - B.K_HW) * k, B.K_HW + (self.ED - B.K_HW) * k

    def recolor(self, cls, L, ud, vd, f):
        if cls == "edge":
            return X1 if f.glow else OCH[9]
        return G[5] if L > 110 else G[4] if L > 80 else G[3]

    def slab(self, ud, vd, f, X, Y):
        if ud < 5 or ud > self.TIP:
            return None
        sp, ed = self.prof(ud)
        if vd < sp or vd > ed:
            return None
        if ud > self.TIP - (vd - sp) * 0.55:
            return None
        if vd < sp + 0.9 and any(abs(ud - n) < 1.0 for n in (19, 34, 47)):
            return None
        if vd < sp + 1.2:
            return (G[9], True)
        if vd > ed - 1.0 or ud > self.TIP - (vd - sp) * 0.55 - 1.0:
            return (X1 if f.glow else OCH[9], True)
        if vd > ed - 2.6:
            return (OCH[6] if vd > ed - 1.8 else OCH[4], True)
        if abs(vd - 0.4) < 0.5:
            return (G[7], True)
        return (G[4] if h2(X // 2, Y // 2, 61) > 0.8 else G[5] if vd > -1.5 else G[6], True)

    def guard(self, ud, vd, X, Y):
        if -2.2 <= ud <= 3.8 and abs(vd) <= 9.6:
            if abs(vd) > 8.2 and (ud < -1.2 or ud > 2.8):
                return None
            if abs(abs(vd) - 6.6) < 1.1 and abs(ud - 0.8) < 1.1:
                return (OCH[9] if vd < 0 else OCH[7], True)
            if ud < -1.2 or vd < -8.4:
                return (SL[7], True)
            if ud > 2.8 or vd > 8.4:
                return (SL[2], True)
            return (SL[5] if h2(X, Y, 7) > 0.25 else SL[4], True)
        if -20.2 <= ud <= -16.0 and abs(vd) <= 3.6:
            return (OCH[8] if vd < 0 else OCH[5], True)
        return None

    def a1(self, ctx, geo, f):
        fld(ctx, geo, (4, 62, -6, 5), lambda ud, vd, X, Y: self.slab(ud, vd, f, X, Y), R=6.5, tip_u=55)
        fld(ctx, geo, (-21, 5, -10, 10), self.guard, R=10)

    def horn(self, ud, vd, X, Y, f):
        for sg in (-1, 1):
            best = None
            for k in range(13):
                t = k / 12
                cu, cv = 3.8 + 10 * t, sg * (9.0 + 3.4 * math.sin(math.pi * t * 0.8))
                d = math.hypot(ud - cu, vd - cv)
                w = 1.8 * (1 - t) + 0.5
                if d <= w and (best is None or d < best[0]):
                    best = (d, t, cv)
            if best:
                return (OCH[8] if (vd - best[2]) * sg < 0 else OCH[5], True)
        return None

    def a2(self, ctx, geo, f):
        def fn(ud, vd, X, Y):
            r = self.horn(ud, vd, X, Y, f)
            if r:
                return r
            for n in (22, 33, 44):
                if abs(ud - n) <= 1.6 - 0.5 * max(0, self.SP - vd) and self.SP - 2.6 <= vd < self.SP:
                    return (G[7] if ud < n else G[4], True)
            return None
        fld(ctx, geo, (1, 48, -14, 14), fn, R=13, tip_u=None)

    def gl(self, ctx, geo, f):
        pp = -4 + f.ph * 72

        def fn(ud, vd, X, Y):
            if 7 <= ud <= self.TIP - 3:
                sp, ed = self.prof(ud)
                if ed - 1.0 <= vd <= ed:
                    return X0 if (f.glow or abs(ud - pp) < 4) else G[12]
                if abs(vd - 0.4) < 0.5 and int(ud) % 4 < 2:
                    return G[11]
            for sg in (-1, 1):
                if math.hypot(ud - 13.8, vd - sg * (9.0 + 3.4 * math.sin(math.pi * 0.8))) < 1.0:
                    return X0
            return None
        fld(ctx, geo, (5, 62, -14, 14), fn, R=13, tip_u=55, over=True, z=5)

    def sheath_col(self):
        return OCH[8]

    def emblem(self):
        return [(dx, dy, OCH[8] if (dx, dy) == (1, 1) else SL[4]) for dx in range(3) for dy in range(3)]

    def emblem2(self):
        return [(-1, -1, OCH[7]), (3, -1, OCH[7])]


# =============================================================================
# 칼 — 만월(滿月): 60라운드 월인 그대로(a1) + 코등이 뒤 초승달 고리 · 빛날 안쪽 둘째 초승달(a2)
# =============================================================================
class Mangetsu(Branch):
    weapon, bid = "katana", "mangetsu"
    reuse = True
    a1_design = "60라운드 최종 각성 '월인' 재사용 — " + PO.DESIGN["katana"][1]
    a2_design = ("코등이 뒤로 크게 두른 초승달 고리(반지름 13, 등 쪽이 두꺼움, 양 끝이 뿔처럼 뾰족) · 고리를 도는 달 구슬 3 "
                 "(메모리 1.5배 상한 때문에 2차 덧붙임은 코등이 둘레에 모음)")
    glow_design = "초승달 고리 바깥 테(빛이 고리를 따라 돎) + 달 구슬 심"
    RO, RI, OFF = 13.0, 11.6, 2.4

    def crescent(self, ud, vd):
        ro = math.hypot(ud - 1.2, vd)
        ri = math.hypot(ud - 1.2, vd - self.OFF)
        return ro <= self.RO and ri >= self.RI and vd < 6, ro

    def beads(self, f):
        out = []
        for k in range(3):
            a = 2 * math.pi * (f.ph / 3 + k / 3) - math.pi / 2
            out.append((1.2 + 16.5 * math.cos(a), 16.5 * math.sin(a) * 0.8))
        return out

    def a2(self, ctx, geo, f):
        beads = self.beads(f)

        def ring(ud, vd, X, Y):
            ok, ro = self.crescent(ud, vd)
            if ok:
                return (SIL[10] if ro > self.RO - 0.9 else SIL[7] if vd < -4 else SIL[5], True)
            for (bu, bv) in beads:
                d = math.hypot(ud - bu, vd - bv)
                if d <= 1.9:
                    return (SIL[10] if vd < bv else SIL[6], True)
            return None
        fld(ctx, geo, (-17, 19, -18, 18), ring, R=19)

    def gl(self, ctx, geo, f):
        beads = self.beads(f)

        def fn(ud, vd, X, Y):
            ok, ro = self.crescent(ud, vd)
            if ok and ro > self.RO - 1.0:
                a = math.atan2(vd, ud - 1.2)
                return X0 if (f.glow or abs(((a - 2 * math.pi * f.ph) % (2 * math.pi)) - math.pi) < 0.5) else G[12]
            for (bu, bv) in beads:
                if math.hypot(ud - bu, vd - bv) <= 0.9:
                    return X0
            return None
        fld(ctx, geo, (-17, 19, -18, 18), fn, R=19, over=True, z=5)

    def sg(self, ctx, geo, f):
        if geo.hot:
            x, y = geo.hot[len(geo.hot) // 2]
            bob = (f.t % 4 > 1)
            for dx, dy in ((0, 0), (1, 0), (2, 1), (2, 2), (1, 3), (0, 3)):
                ctx.cv.put(x + ctx.ox + dx - 1, y + ctx.oy - 9 - bob + dy, G[12] if dy in (1, 2) else X0, 4, False)

    def s2(self, ctx, geo, f):
        if geo.hot:
            x, y = geo.hot[len(geo.hot) // 2]
            for dx, dy in ((-3, -1), (-3, 4), (-4, 0), (-4, 3), (-5, 1), (-5, 2)):
                ctx.add(x + ctx.ox + dx, y + ctx.oy - 9 + dy, SIL[8], 3, True)


# =============================================================================
# 대검 — 파쇄(破碎): 끝으로 갈수록 넓어지는 바위 쐐기 머리 · 망치 면 · 용암 균열
# =============================================================================
class Crush(Branch):
    weapon, bid = "greatsword", "crush"
    tn = 10
    a1_design = ("날 90×폭 9 → 끝으로 갈수록 넓어지는 바위 쐐기(폭 9 → 최대 23, 끝 96 의 들쭉날쭉 깨진 망치 면) / "
                 "색: 녹슨 쇠 → 바위 회색 면(G3~G7) + 황토 테 + 균열 속 호박 불씨(1층 A)")
    a2_design = "망치 면 양 모서리에서 앞·바깥으로 뻗는 바위 뿔 2 · 머리 양옆에 떠서 맴도는 바위 조각 4"
    glow_design = "머리를 가로지르는 균열 그물(가지 늘어남) 백열 + 망치 면 충격 줄"
    CRACKS = [[(40, 0), (55, -3), (66, -6), (78, -9)], [(50, 1), (63, 4), (74, 8)], [(70, -1), (82, 2), (92, -1)], [(84, -6), (94, -9)]]
    CRACKS2 = [[(60, -5), (70, -11)], [(78, 3), (88, 9), (94, 11)], [(86, -2), (90, -6), (95, -4)], [(30, 0), (40, 0)]]

    def hw(self, u):
        return 4.5 + 7.2 * smooth(28, 80, u)

    def head(self, ud, vd, f, X, Y, glow_on):
        if ud < 3:
            return None
        hw = self.hw(ud)
        if abs(vd) > hw:
            return None
        front = 96 - 2.5 * h2(int((vd + 20) / 2.6), 0, 77)
        front -= max(0.0, abs(vd) - (hw - 3)) * 1.0
        if ud > front:
            return None
        cd = min(poly_d(ud, vd, c)[0] for c in self.CRACKS)
        if cd < 0.7:
            return (A[8] if glow_on else A[6], True)
        if cd < 1.4:
            return (OCH[2], True)
        if ud > front - 1.4:
            return (G[3], True)
        if abs(vd) > hw - 1.2:
            return (G[7] if vd < 0 else OCH[2], True)
        fid = int((ud + 7 * vd / hw * 0.6) / 9)
        sh = 4 + int(h2(fid, int(vd > 0), 5) * 2.4) + (1 if vd < -hw * 0.4 else 0) - (1 if vd > hw * 0.5 else 0)
        return (G[sh], True)

    def recolor(self, cls, L, ud, vd, f):
        r = self.head(ud, vd, f, 0, 0, f.glow)
        if r:
            return r[0]
        return G[6] if L > 120 else G[5] if L > 90 else G[4]

    def a1(self, ctx, geo, f):
        fld(ctx, geo, (3, 97, -13, 13), lambda ud, vd, X, Y: self.head(ud, vd, f, X, Y, f.glow), R=14, tip_u=90)

    def rock(self, ud, vd, cu, cv, r=2.6):
        d = abs(ud - cu) + abs(vd - cv) * 1.2
        if d <= r:
            return (G[6] if (vd - cv) < 0 else G[4], True)
        return None

    def a2(self, ctx, geo, f):
        def fn(ud, vd, X, Y):
            for sg in (-1, 1):
                bx, by = 93.0, sg * 10.2
                dx, dy = math.cos(math.radians(35)), sg * math.sin(math.radians(35))
                a = (ud - bx) * dx + (vd - by) * dy
                b = -(ud - bx) * dy + (vd - by) * dx
                if 0 <= a <= 10:
                    w = 2.8 * (1 - a / 10)
                    if abs(b) <= w:
                        return (G[6] if b * sg < 0 else G[3], True)
            for k, a0 in enumerate((75, 120, 240, 285)):
                ang = math.radians(a0) + 2 * math.pi * f.ph * 0.1
                cu = 76 + 19 * math.cos(ang)
                cv = 18 * math.sin(ang) + 1.2 * math.sin(2 * math.pi * (f.ph + k / 4))
                r = self.rock(ud, vd, cu, cv)
                if r:
                    return r
            return None
        fld(ctx, geo, (55, 106, -22, 22), fn, R=24, tip_u=60)

    def gl(self, ctx, geo, f):
        pp = 30 + f.ph * 70

        def fn(ud, vd, X, Y):
            if not self.head(ud, vd, f, X, Y, False):
                return None
            cd = min(poly_d(ud, vd, c)[0] for c in self.CRACKS + self.CRACKS2)
            if cd < 0.6:
                return X0 if (f.glow or abs(ud - pp) < 6) else G[12]
            if ud > 93.5 and int(vd + f.t) % 3 == 0:
                return G[11]
            return None
        fld(ctx, geo, (28, 97, -13, 13), fn, R=14, tip_u=90, over=True, z=5)


# =============================================================================
# 대검 — 중압(重壓): 방패 같은 넓은 철판 날 · 황동 못 줄 · 넓게 굽은 막이 코등이
# =============================================================================
class Weight(Branch):
    weapon, bid = "greatsword", "weight"
    tn = 10
    a1_design = ("날 폭 9 → 18 의 곧은 철판(방패 판), 끝 86~97 뭉툭한 삼각 · 판 이음 3줄 · 양쪽 황동 못 줄 · 가운데 홈 / "
                 "넓게 굽은 막이 코등이(폭 30, 끝이 날 쪽으로 꺾임, 황동 마개) / 색: 흉갑 쇠(SL) + 황동(6층 GOLD)")
    a2_design = "판 양 테에서 돋는 쇠 가시 3쌍 · 판 밑동 마름모 황동 보주"
    glow_design = "보주 심 + 밑동 쪽 가운데 홈 빛(흐름) + 밑동 못 머리 (메모리 상한으로 날 아래 절반)"

    def hw(self, u):
        if u < 86:
            return 4.5 + 4.5 * smooth(3, 9, u)
        return 9.0 * max(0.0, 1 - (u - 86) / 11) ** 0.8

    def plate(self, ud, vd, f, X, Y):
        if ud < 3 or ud > 97:
            return None
        hw = self.hw(ud)
        if abs(vd) > hw:
            return None
        if abs(vd) > hw - 1.6:
            return (SL[7] if vd < 0 else SL[2], True)
        if ud > 9:
            for uu in range(14, 85, 10):
                if math.hypot(ud - uu, abs(vd) - 6.3) < 1.15:
                    return (GOLD[7] if vd < 0 else GOLD[6], True)
                if math.hypot(ud - uu, abs(vd) - 6.3) < 1.7:
                    return (GOLD[3], True)
        if any(abs(ud - s) < 0.6 for s in (28, 50, 72)):
            return (SL[2], True)
        if abs(vd) < 0.8 and 10 <= ud <= 84:
            return (SL[1], True)
        return (SL[5] if vd < -2 else SL[4], True)

    def guard(self, ud, vd, X, Y):
        a = abs(vd)
        if a > 15:
            return None
        lo, hi = -2.2, 2.6
        if a > 12:
            lo, hi = lo + (a - 12) * 1.2, hi + (a - 12) * 1.2
        if not (lo <= ud <= hi):
            return None
        if a > 13.8:
            return (GOLD[6], True)
        return (SL[7] if ud < lo + 1 else SL[5], True)

    def recolor(self, cls, L, ud, vd, f):
        r = self.plate(ud, vd, f, 0, 0)
        if r:
            return r[0]
        return SL[6] if L > 100 else SL[4]

    def a1(self, ctx, geo, f):
        fld(ctx, geo, (3, 98, -10, 10), lambda ud, vd, X, Y: self.plate(ud, vd, f, X, Y), R=12, tip_u=84)
        fld(ctx, geo, (-3, 8, -16, 16), self.guard, R=14)

    def a2(self, ctx, geo, f):
        def fn(ud, vd, X, Y):
            a = abs(vd)
            for us in (30, 52, 74):
                if 8.8 <= a <= 14.5:
                    w = 3.2 * (1 - (a - 8.8) / 5.7)
                    if abs(ud - us) <= w:
                        return (SL[6] if vd < 0 else SL[3], True)
            q = abs(ud - 18) / 5.2 + a / 4.2
            if q <= 1:
                return (GOLD[8] if vd < 0 and q > 0.45 else GOLD[5] if q > 0.45 else GOLD[3], True)
            return None
        fld(ctx, geo, (10, 80, -15, 15), fn, R=16, tip_u=84)

    def gl(self, ctx, geo, f):
        pp = 6 + f.ph * 44

        def fn(ud, vd, X, Y):
            if abs(vd) < 0.8 and 10 <= ud <= 46:
                return X0 if (f.glow or abs(ud - pp) < 5) else G[11]
            for uu in range(14, 45, 10):
                if math.hypot(ud - uu, abs(vd) - 6.3) < 0.6:
                    return G[13]
            if abs(ud - 18) + abs(vd) <= 1.6:
                return X0
            return None
        fld(ctx, geo, (8, 47, -8, 8), fn, R=12, tip_u=84, over=True, z=5)


# =============================================================================
# 대검 — 광전(狂戰): 60라운드 핏빛 거암검(a1) + 쇠사슬 감기·늘어진 사슬(보정), a2 = 등 뿔 2 · 사슬 끝 가시 추
# =============================================================================
def chain_link(s, du, period=3.2):
    """사슬 고리: s = 사슬을 따라 거리, du = 사슬 축에서 수직 거리 → (색 단계 0~2 | None)."""
    k = int(math.floor(s / period))
    ls = (s % period) - period / 2
    if k % 2 == 0:
        q = (ls / 1.75) ** 2 + (du / 1.35) ** 2
        if 0.3 <= q <= 1.0:
            return 2 if du < 0 else 1
        return None
    if abs(du) <= 0.6 and abs(ls) <= 1.9:
        return 1
    return None


class Berserk(Branch):
    weapon, bid = "greatsword", "berserk"
    tn = 10
    reuse = True
    a1_design = ("60라운드 최종 각성 '핏빛 거암검' 재사용 + 보정: 날을 두 번 감은 쇠사슬(u 34·62) · 코등이에서 늘어져 흔들리는 사슬 — "
                 + PO.DESIGN["greatsword"][1])
    a2_design = "코등이 위 등 쪽으로 휘어 솟는 현무암 뿔 2 · 늘어진 사슬 끝 가시 철퇴"
    glow_design = "코등이에서 늘어진 사슬이 달아오름(맥동) + 뿔 끝 (메모리 상한으로 감긴 사슬은 a1 그대로)"
    BANDS = (34, 62)

    def hang(self, f):
        return [(1 - 15 * t, 10 + 6 * t + 2.5 * math.sin(2 * math.pi * (f.ph + t)) * t) for t in [i / 12 for i in range(13)]]

    def chains(self, ud, vd, f):
        for uc in self.BANDS:
            if abs(vd) > 11:
                continue
            du = ud - (uc + 0.45 * vd)
            r = chain_link(vd + 17, du)
            if r is not None:
                return r
        pts = self.hang(f)
        d, t = poly_d(ud, vd, pts)
        if d < 1.6:
            s = t * 24
            # 사슬 축의 수직 성분 부호
            r = chain_link(s, d * (1 if (vd - 10 - 6 * t) > 0 else -1))
            if r is not None:
                return r
        return None

    def a1_extra(self, ctx, geo, f):
        def fn(ud, vd, X, Y):
            r = self.chains(ud, vd, f)
            if r is None:
                return None
            return (G[8] if r == 2 else G[5], True)
        fld(ctx, geo, (-16, 70, -21, 21), fn, R=12, tip_u=None)

    def a2(self, ctx, geo, f):
        pts = self.hang(f)
        bu, bv = pts[-1]

        def fn(ud, vd, X, Y):
            for k in range(11):
                t = k / 10
                cu, cv = 10 - 7 * t, -7 - 11 * t + 2 * t * t
                if math.hypot(ud - cu, vd - cv) <= 2.6 * (1 - t) + 0.4:
                    return (CRI[5] if t > 0.75 else G[5] if vd < cv else G[3], True)
            d = math.hypot(ud - bu, vd - (bv + 2.2))
            if d <= 2.4:
                return (G[6] if vd < bv + 2 else G[4], True)
            for a in range(4):
                ang = a * math.pi / 2 + math.pi / 4
                for r in (2.6, 3.4, 4.2):
                    if math.hypot(ud - (bu + r * math.cos(ang)), vd - (bv + 2.2 + r * math.sin(ang))) < 0.7 - (r - 2.6) * 0.15:
                        return (G[7], True)
            return None
        fld(ctx, geo, (-21, 14, -21, 24), fn, R=16)

    def gl(self, ctx, geo, f):
        pts = self.hang(f)

        def fn(ud, vd, X, Y):
            d, t = poly_d(ud, vd, pts)
            r = self.chains(ud, vd, f) if d < 1.6 else None
            if r is not None:
                return X0 if (f.glow or r == 2 and int(ud + vd + f.t * 2) % 5 == 0) else G[12] if r == 2 else G[11]
            if math.hypot(ud - 3, vd + 17.9) < 1.0:
                return X0
            return None
        fld(ctx, geo, (-16, 6, -21, 21), fn, R=12, over=True, z=5)


# =============================================================================
# 단검 — 쌍격(雙擊): 등 쪽 둘째 갈래 날(쌍날) + 두 날을 잇는 가로막이
# =============================================================================
class Twin(Branch):
    weapon, bid = "dagger", "twin"
    tn = 6
    a1_design = ("날 24 옆(등 쪽 6 도트)에 나란한 둘째 갈래 날(길이 20, 끝 뾰족) + 두 날을 잇는 가로막이 — 두 갈래 쌍날 실루엣 / "
                 "색: 재 → 은백(8층 SIL) + 청록 날끝(3층 TEAL)")
    a2_design = "앞으로 꺾인 X자 막이 날개 2 · 둘째 날 끝 연장 + 미늘"
    glow_design = "날선 쪽에 나란히 뜬 '분신 날' 윤곽(셋째 날) + 갈래 날 날선"

    def prong_c(self, ud):
        return -6.2 + 0.4 * clamp((ud - 1.5) / 24.5)

    def prong(self, ud, vd, f, end=22.5):
        if not (2.5 <= ud <= end):
            return None
        w = 1.7 if ud < end - 5.5 else 1.7 * (end - ud) / 5.5
        c = self.prong_c(ud)
        d = vd - c
        if abs(d) > w + 0.05:
            return None
        if ud > end - 2.2:
            return (X1 if f.glow else TEAL[9], True)
        return (SIL[10] if d < -0.6 else SIL[4] if d > 0.6 else SIL[7], True)

    def recolor(self, cls, L, ud, vd, f):
        if cls == "amber":
            return X1 if f.glow else TEAL[9]
        return SIL[9] if L > 112 else SIL[6] if L > 86 else SIL[4] if L > 64 else SIL[2]

    def a1(self, ctx, geo, f):
        def fn(ud, vd, X, Y):
            r = self.prong(ud, vd, f)
            if r:
                return r
            if 0 <= ud <= 2.5 and -8.0 <= vd <= 3.2:
                return (SIL[6] if ud < 0.9 else SIL[3], True)
            return None
        fld(ctx, geo, (-1, 24, -9, 4), fn, R=9, tip_u=20)

    def a2(self, ctx, geo, f):
        def fn(ud, vd, X, Y):
            for a, b in (((1.2, -8.0), (6.5, -11.6)), ((1.2, 3.2), (6.5, 6.9))):
                d, k = seg_d(ud, vd, a[0], a[1], b[0], b[1])
                if d <= 1.3 - 0.6 * k:
                    return (SIL[7] if vd < (a[1] + b[1]) / 2 else SIL[3], True)
            if 22 <= ud <= 27.5:
                c = self.prong_c(ud) - 0.3 * (ud - 22)
                if abs(vd - c) <= 0.9 * (27.5 - ud) / 5.5 + 0.2:
                    return (SIL[8], True)
            if 18.5 <= ud <= 21.5:
                c = self.prong_c(ud)
                if c - 1.7 - (21.5 - ud) * 0.8 <= vd <= c - 1.4:
                    return (SIL[5], True)
            return None
        fld(ctx, geo, (0, 28, -13, 8), fn, R=10, tip_u=20)

    def gl(self, ctx, geo, f):
        pp = f.ph * 30

        def inside(ud, vd):
            if not (1.5 <= ud <= 25):
                return False
            un = (ud - 1.5) / 23.5
            w = B.d_hw(un) + 0.4
            return abs(vd - (7.2 + 0.8 * un)) <= w

        def fn(ud, vd, X, Y):
            if inside(ud, vd) and not all(inside(ud + du, vd + dv) for du, dv in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                return X0 if abs(ud - pp) < 3 or f.glow else G[12]
            if 3 <= ud <= 21 and -1.4 <= vd - self.prong_c(ud) <= -0.8:
                return G[11]
            return None
        fld(ctx, geo, (0, 27, -9, 13), fn, R=11, tip_u=20, over=True, z=5)


# =============================================================================
# 단검 — 질풍(疾風): 넓은 잎 날 + 고리 손잡이 + 부채처럼 펼친 작은 날 2(투척 부채 3)
# =============================================================================
class Gale(Branch):
    weapon, bid = "dagger", "gale"
    tn = 6
    a1_design = ("날 24 → 잎 모양 넓은 날(길이 28.5, 폭 최대 9.6) · 손잡이 끝 고리 · 코등이에서 ±30° 로 펼친 작은 잎 날 2 — 부채 셋 실루엣 / "
                 "색: 재 → 녹청(2층 GRN), 날선 연두 빛")
    a2_design = "부채 날 2 → 길게(+5) + 바깥 ±58° 작은 날 2 더(부채 다섯) · 고리에 매단 바람 끈 2"
    glow_design = "부채 날마다 가운데 바람 줄 + 잎 날 윤곽 맥동 + 고리 테"

    def leaf(self, ud, vd, f):
        if not (1.5 <= ud <= 30):
            return None
        s = (ud - 1.5) / 28.5
        hw = 4.8 * math.sin(math.pi * s ** 0.85) ** 0.75
        c = 0.5 * s
        d = vd - c
        if abs(d) > hw or hw < 0.3:
            return None
        if abs(d) > hw - 0.9:
            return (X1 if (f.glow and s > 0.6) else GRN[10], True)
        if abs(d) < 0.55:
            return (GRN[9], True)
        return (GRN[7] if d < 0 else GRN[4], True)

    def fan(self, ud, vd, f, deg, L0=2.0, L1=15.0, wmax=1.9):
        for sg in (-1, 1):
            a = math.radians(deg) * sg
            ca, sa = math.cos(a), math.sin(a)
            x, y = ud - 0.5, vd
            al = x * ca + y * sa
            pe = -x * sa + y * ca
            if L0 <= al <= L1:
                w = wmax * math.sin(math.pi * (al - L0) / (L1 - L0)) ** 0.7
                if abs(pe) <= w:
                    if abs(pe) > w - 0.8:
                        return (GRN[10], True)
                    return (GRN[7] if pe * sg < 0 else GRN[4], True)
        return None

    def ringp(self, ud, vd):
        r = math.hypot(ud + 12.5, vd)
        if 2.0 <= r <= 3.5:
            return (GRN[8] if vd < 0 else GRN[5], True)
        return None

    def recolor(self, cls, L, ud, vd, f):
        if cls == "amber":
            return X1 if f.glow else GRN[10]
        return GRN[8] if L > 112 else GRN[6] if L > 86 else GRN[4] if L > 64 else GRN[2]

    def a1(self, ctx, geo, f):
        fld(ctx, geo, (0, 31, -9, 9), lambda ud, vd, X, Y: self.leaf(ud, vd, f) or self.fan(ud, vd, f, 30), R=9, tip_u=24)
        fld(ctx, geo, (-17, -8, -5, 5), lambda ud, vd, X, Y: self.ringp(ud, vd), anchor=(-9, 0))

    def a2(self, ctx, geo, f):
        def fn(ud, vd, X, Y):
            r = self.fan(ud, vd, f, 30, L0=14.0, L1=20.0, wmax=1.4)
            if r:
                return r
            return self.fan(ud, vd, f, 58, L0=2.0, L1=11.0, wmax=1.5)
        fld(ctx, geo, (0, 20, -18, 18), fn, R=13, tip_u=None)

        def streamer(ud, vd, X, Y):
            for sg in (-1, 1):
                if -31 <= ud <= -15:
                    t = (-ud - 15) / 16
                    c = sg * (1.6 + 2.0 * t) + 2.0 * math.sin(t * 5 - 2 * math.pi * f.ph + sg) * t
                    if abs(vd - c) <= 0.9 - 0.4 * t:
                        return (GRN[8] if int(t * 6) % 2 == 0 else GRN[5], True)
            return None
        fld(ctx, geo, (-32, -14, -8, 8), streamer, anchor=(-12.5, 0))

    def gl(self, ctx, geo, f):
        pp = f.ph * 32

        def fn(ud, vd, X, Y):
            for deg, L1 in ((30, 20.0), (58, 11.0)):
                for sg in (-1, 1):
                    a = math.radians(deg) * sg
                    x, y = ud - 0.5, vd
                    al = x * math.cos(a) + y * math.sin(a)
                    pe = -x * math.sin(a) + y * math.cos(a)
                    if 3 <= al <= L1 - 1.5 and abs(pe) < 0.5:
                        return X0 if abs(al - pp * 0.6) < 2 else G[11]
            r = self.leaf(ud, vd, f)
            if r and r[0] in (GRN[10], X1):
                return X0 if abs(ud - pp) < 3 else G[12]
            rr = math.hypot(ud + 12.5, vd)
            if 3.0 <= rr <= 3.6:
                return G[11]
            return None
        fld(ctx, geo, (-17, 31, -12, 12), fn, R=13, tip_u=24, over=True, z=5)


# =============================================================================
# 단검 — 백귀(百鬼): 60라운드 귀화(a1) + 코등이 도깨비 뿔 2(a2) · 맴도는 혼불 3(빛)
# =============================================================================
class Hyakki(Branch):
    weapon, bid = "dagger", "hyakki"
    tn = 6
    reuse = True
    a1_design = "60라운드 최종 각성 '귀화' 재사용 — " + PO.DESIGN["dagger"][1]
    a2_design = "코등이 양쪽에서 뒤로 휘어 솟는 뼈빛 도깨비 뿔 2"
    glow_design = "뿔 사이(코등이 둘레)를 맴도는 혼불 2(고리 + 심) + 뿔 끝"

    def a2(self, ctx, geo, f):
        def fn(ud, vd, X, Y):
            for sg in (-1, 1):
                for k in range(11):
                    t = k / 10
                    cu, cv = 0.5 - 7 * t, sg * (3 + 6 * t + 2 * t * t)
                    if math.hypot(ud - cu, vd - cv) <= 1.7 * (1 - t) + 0.45:
                        return (PL[4] if (vd - cv) * sg < 0 else PL[2], True)
            return None
        fld(ctx, geo, (-8, 2, -12, 12), fn, R=12)

    def gl(self, ctx, geo, f):
        def fn(ud, vd, X, Y):
            for k in range(2):
                ph = 2 * math.pi * (f.ph + k / 2)
                cu = -2 + 6 * math.cos(ph)
                cv = 7.5 * math.sin(ph)
                d = math.hypot(ud - cu, (vd - cv))
                if d <= 0.8:
                    return X0
                if 1.4 <= d <= 2.1:
                    return G[12]
            for sg in (-1, 1):
                if math.hypot(ud + 6.5, vd - sg * 11) < 0.9:
                    return X0
            return None
        fld(ctx, geo, (-9, 6, -12, 12), fn, R=14, over=True, z=5)


# =============================================================================
# 활 — 화면 좌표 도구(활대 끝 ends · 쥔 곳 g · 쏘는 방향 n · 활대 방향 e)
# =============================================================================
def bp(ctx, p):
    return (p[0] + ctx.ox, p[1] + ctx.oy)


def badd(p, v, k):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


class BowBranch(Branch):
    weapon = "bow"
    tn = 6
    RAMP = OCH

    def recolor_px(self, ctx, geo, f):
        px = ctx.px
        for p in geo.pts:
            c = Z.hx(px[p])
            if c in PO.PLSET:
                continue
            L = lum(px[p])
            if c in PO.AMBER:
                col = self.amber(f)
            elif c in PO.SLSET:
                col = self.tipcol(L)
            else:
                col = self.wood(L)
            ctx.put_orig(p, col)

    def end_pts(self, geo):
        return [(sg, e[0], e[1]) for sg, e in sorted(geo.ends.items())]


class Rapid(BowBranch):
    bid = "rapid"
    a1_design = ("활대 양 끝이 앞으로 말린 갈고리(리커브) · 줌통 앞 받침대에 부채꼴로 꽂힌 화살촉 3 — 연사 실루엣 / "
                 "색: 재·호박 → 황토 나무(4층 OCH) + 청록 표식, 은빛 촉")
    a2_design = "활대 양 끝 바퀴(도르래 캠, 살 4) · 아래 활대에 화살통 상자 + 깃 3"
    glow_design = "캠 심 + 화살촉 끝 + 받침 둘레 고리"

    def amber(self, f):
        return X1 if f.glow else TEAL[8]

    def tipcol(self, L):
        return TEAL[5] if L > 75 else TEAL[3]

    def wood(self, L):
        return OCH[8] if L > 108 else OCH[6] if L > 84 else OCH[4] if L > 58 else OCH[3]

    def a1(self, ctx, geo, f):
        self.recolor_px(ctx, geo, f)
        n, e, sc = geo.n, geo.e, geo.scale
        for sg, p, d in self.end_pts(geo):
            P = bp(ctx, p)
            pts = [P, badd(badd(P, d, 3 * sc), n, 1 * sc), badd(badd(P, d, 5 * sc), n, 4 * sc), badd(badd(P, d, 4 * sc), n, 7 * sc)]
            chain_px(ctx, pts, lambda t: 1.4 - 0.7 * t, lambda t, dd, x, y: OCH[6] if dd < 0.5 else OCH[3])
        Gp = bp(ctx, geo.g)
        chain_px(ctx, [badd(Gp, n, 2), badd(Gp, n, 7.5 * sc)], lambda t: 1.0, lambda t, dd, x, y: G[5])
        for k in (-1, 0, 1):
            base = badd(badd(Gp, n, 8.5 * sc), e, k * 4 * sc)
            chain_px(ctx, [badd(badd(Gp, n, 5 * sc), e, k * 1.5 * sc), base], lambda t: 0.6, lambda t, dd, x, y: WD[4])
            self.head(ctx, base, n, e, 4.2 * sc, 2.0 * sc, f)

    def head(self, ctx, base, n, e, L, hw, f, over=False, col=None):
        for y in range(int(base[1] - L - 3), int(base[1] + L + 4)):
            for x in range(int(base[0] - L - 3), int(base[0] + L + 4)):
                dx, dy = x + 0.5 - base[0], y + 0.5 - base[1]
                a = dx * n[0] + dy * n[1]
                b = dx * e[0] + dy * e[1]
                if 0 <= a <= L and abs(b) <= hw * (1 - a / L) + 0.35:
                    c = col or (SIL[9] if b < 0 else SIL[5])
                    if over:
                        ctx.cv.put(x, y, c, 5, False)
                    else:
                        ctx.add(x, y, c, 1, True)

    def a2(self, ctx, geo, f):
        n, e, sc = geo.n, geo.e, geo.scale
        for sg, p, d in self.end_pts(geo):
            C = badd(bp(ctx, p), d, 2.5 * sc)
            R = 3.8 * max(0.7, sc)
            spin = 2 * math.pi * f.ph

            def cf(rn, x, y, C=C, R=R):
                if rn > 0.68:
                    return SL[6] if (y + 0.5 - C[1]) < 0 else SL[3]
                if rn < 0.3:
                    return GOLD[7]
                a = math.atan2(y + 0.5 - C[1], x + 0.5 - C[0]) + spin
                return SL[4] if (a % (math.pi / 2)) < 0.35 else None
            disc_px(ctx, C[0], C[1], R, cf)
        q = geo.limb_point(geo.smin * 0.45) if geo.smin < -10 else None
        if q:
            Q = badd(bp(ctx, q), n, -4.5 * sc)
            a0, a1_ = badd(Q, e, -5 * sc), badd(Q, e, 5 * sc)
            chain_px(ctx, [a0, a1_], lambda t: 2.1 * max(0.7, sc), lambda t, dd, x, y: WD[4] if dd < 0.4 else WD[2])
            for k in (-1, 0, 1):
                b0 = badd(a0, n, k * 1.5)
                chain_px(ctx, [b0, badd(badd(b0, e, -3.5 * sc), n, k * 1.0)], lambda t: 0.9 - 0.4 * t,
                         lambda t, dd, x, y: TEAL[7] if t < 0.5 else TEAL[5])

    def gl(self, ctx, geo, f):
        n, e, sc = geo.n, geo.e, geo.scale
        for sg, p, d in self.end_pts(geo):
            C = badd(bp(ctx, p), d, 2.5 * sc)
            disc_px(ctx, C[0], C[1], 1.3, lambda rn, x, y: X0 if f.t % 3 != 1 else G[12], over=True)
        Gp = bp(ctx, geo.g)
        for k in (-1, 0, 1):
            tipp = badd(badd(badd(Gp, n, 8.5 * sc), e, k * 4 * sc), n, 3.6 * sc)
            disc_px(ctx, tipp[0], tipp[1], 0.9, lambda rn, x, y: X0, over=True)
        Cc = badd(Gp, n, 9.5 * sc)
        R = 7.0 * max(0.7, sc)
        disc_px(ctx, Cc[0], Cc[1], R + 0.6, lambda rn, x, y: (G[11] if int(math.atan2(y - Cc[1], x - Cc[0]) * 6 / math.pi + f.t) % 2 else None)
                if rn > R / (R + 0.6) - 0.1 else None, over=True)


class Snipe(BowBranch):
    bid = "snipe"
    a1_design = ("활대 양 끝이 바깥으로 12 더 길게 뻗은 긴 활(장궁, 끝이 살짝 뒤로) · 줌통 앞 기둥 위 고리 조준기(지름 7, 붉은 점) / "
                 "색: 재 → 흉갑 쇠(SL) + 은백 끝 + 진홍 렌즈")
    a2_design = "조준기 앞으로 뻗는 안정 막대(+11, 끝 추) · 조준기 양옆 십자 날개 2 (메모리 상한으로 2차 덧붙임은 조준기 둘레에 모음)"
    glow_design = "조준기 렌즈 + 앞으로 뻗는 짧은 점선 조준줄(흐름)"

    def amber(self, f):
        return X1 if f.glow else CRI[7]

    def tipcol(self, L):
        return SIL[8] if L > 75 else SIL[5]

    def wood(self, L):
        return SL[7] if L > 108 else SL[6] if L > 84 else SL[4] if L > 58 else SL[3]

    def ext_pts(self, ctx, geo, p, d):
        n, sc = geo.n, geo.scale
        P = bp(ctx, p)
        return [badd(badd(P, d, 12 * sc * t), n, -2 * t * t) for t in [i / 6 for i in range(7)]]

    def a1(self, ctx, geo, f):
        self.recolor_px(ctx, geo, f)
        n, sc = geo.n, geo.scale
        for sg, p, d in self.end_pts(geo):
            pts = self.ext_pts(ctx, geo, p, d)
            chain_px(ctx, pts, lambda t: 1.5 * (1 - t) + 0.55, lambda t, dd, x, y: SIL[9] if t > 0.85 else SL[6] if dd < 0.5 else SL[3])
        Gp = bp(ctx, geo.g)
        chain_px(ctx, [badd(Gp, n, 1), badd(Gp, n, 8 * sc)], lambda t: 0.8, lambda t, dd, x, y: SL[5])
        C = badd(Gp, n, 11.5 * sc)
        disc_px(ctx, C[0], C[1], 3.6, lambda rn, x, y: (SL[6] if y + 0.5 < C[1] else SL[3]) if rn > 0.62 else (CRI[8] if rn < 0.2 else None))

    def a2(self, ctx, geo, f):
        n, e, sc = geo.n, geo.e, geo.scale
        Gp = bp(ctx, geo.g)
        C = badd(Gp, n, 11.5 * sc)
        chain_px(ctx, [badd(C, n, 3.8), badd(C, n, 3.8 + 11 * sc)], lambda t: 0.7, lambda t, dd, x, y: SL[5])
        W_ = badd(C, n, 4.8 + 11 * sc)
        disc_px(ctx, W_[0], W_[1], 1.9, lambda rn, x, y: SL[6] if y + 0.5 < W_[1] else SL[3])
        for sg in (-1, 1):                                   # 조준기 양옆 십자 날개
            a0 = badd(C, e, sg * 3.6)
            chain_px(ctx, [a0, badd(badd(a0, e, sg * 4.5), n, -2.0)], lambda t: 1.1 - 0.6 * t,
                     lambda t, dd, x, y: SIL[8] if dd < 0.5 else SL[4])

    def gl(self, ctx, geo, f):
        n, sc = geo.n, geo.scale
        Gp = bp(ctx, geo.g)
        C = badd(Gp, n, 11.5 * sc)
        disc_px(ctx, C[0], C[1], 1.0, lambda rn, x, y: X0, over=True)
        for k in range(4, 17):
            if (k + f.t) % 4 < 2:
                q = badd(C, n, k)
                ctx.cv.put(q[0], q[1], X0 if k < 10 else G[12], 5, False)


class Meteor(BowBranch):
    bid = "meteor"
    reuse = True
    a1_design = "60라운드 최종 각성 '혜성 날개' 재사용 — " + PO.DESIGN["bow"][1]
    a2_design = "줌통 뒤 별 고리(반지름 10.5, 별 끝 5)"
    glow_design = "별 끝 5 + 별 고리를 따라 도는 빛 호"

    def ring_c(self, ctx, geo):
        return badd(bp(ctx, geo.g), geo.n, -3)

    def a2(self, ctx, geo, f):
        C = self.ring_c(ctx, geo)
        R = 10.5 * max(0.75, geo.scale)
        rot = 2 * math.pi * f.ph / 5

        def cf(rn, x, y):
            r = rn * (R + 3)
            a = math.atan2(y + 0.5 - C[1], x + 0.5 - C[0]) - rot
            spike = max(0.0, 1 - abs(((a * 5 / (2 * math.pi)) % 1) - 0.5) * 2 * 3.0)
            if R - 0.9 <= r <= R + 0.4 + 2.6 * spike:
                return GOLD[8] if y + 0.5 < C[1] else GOLD[5]
            return None
        disc_px(ctx, C[0], C[1], R + 3, cf)

    def gl(self, ctx, geo, f):
        C = self.ring_c(ctx, geo)
        R = 10.5 * max(0.75, geo.scale)
        rot = 2 * math.pi * f.ph / 5
        for k in range(5):
            a = rot + (k + 0.5) * 2 * math.pi / 5
            q = (C[0] + math.cos(a) * (R + 2.4), C[1] + math.sin(a) * (R + 2.4))
            ctx.cv.put(q[0], q[1], X0, 5, False)
            ctx.cv.put(q[0] + 1, q[1], G[12], 5, False)
        hl = 2 * math.pi * f.ph
        for t in range(48):
            a = hl + t / 48 * 1.4
            q = (C[0] + math.cos(a) * (R - 0.4), C[1] + math.sin(a) * (R - 0.4))
            ctx.cv.put(q[0], q[1], X0 if t > 36 else G[12], 5, False)


REG = {"senpu": Senpu(), "kabuto": Kabuto(), "mangetsu": Mangetsu(), "crush": Crush(), "weight": Weight(), "berserk": Berserk(),
       "twin": Twin(), "gale": Gale(), "hyakki": Hyakki(), "rapid": Rapid(), "snipe": Snipe(), "meteor": Meteor()}
