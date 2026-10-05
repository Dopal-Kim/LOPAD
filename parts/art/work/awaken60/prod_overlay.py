"""각성 무기 오버레이 60장 — weapons/v3/<무기 시트>_awaken (60라운드 재디자인, 기존 파일 교체).

원 무기 시트 프레임마다(4/8방향 전부):
  1) 날(활은 활대) 픽셀을 찾아(기존 combo56_res/overlay · build57/fx_awaken 의 마스크 함수 — 읽기만) 각성 색으로 다시 칠한다
     (원래 명암 순서를 유지한 밝기 대응 → 원 시트 셀아웃·가림이 그대로 살아 있음).
  2) 시안 형태(빛날·바위 판·불꽃·불꽃 깃)를 날 축 로컬 좌표(설계 단위 = 화면 길이 / 설계 길이로 맞춤)로 그려 더한다.
     원 무기 픽셀 위는 덮지 않고(1에서 처리), 날 길이 안쪽 추가분은 원 날 픽셀 근처만, 칼끝 너머는 칼끝이 보일 때만(몸 뒤 가림 보존).
  3) 순환 위상 = 프레임 시작 ms / 순환 ms (시트가 바뀌어도 맥동 속도 같음).
틀: 원 시트 + PAD(칼·단검·활 32 사방, 대검 40·32). pivot·playerFrameOffset 도 같은 만큼 옮겨 JSON 에 적는다.
"""
import math
import os
import sys

from PIL import Image

import prod_common as P
import kit60 as K6
from kit60 import Cv, F, G, A, SIL, CRI, VIO, TEAL, GOLD, X0, X1, INK, h2, clamp, smooth
import base as B
import katana as KM
import greatsword as GM
import dagger as DM
import bow as BM

sys.path.insert(0, os.path.join(P.WORK, "build57"))
import fx_awaken as FA  # noqa: E402  (시트 목록·seg_mask — 읽기만)

OV = FA.OV
KA = KM.KA()
GB = GM.BLOOD
DA = DM.DA()
BA = BM.BA()

SLSET = {c.lower() for c in K6.SL} | {"#3f4552", "#4e5563", "#626a78", "#14161c", "#1d2028", "#272b35"}
PLSET = {c.lower() for c in K6.PL}
WDSET = {c.lower() for c in K6.WD}
EDGE_HEX = {P.hx(c) for c in OV.EDGE_COLS}
AMBER = {c.lower() for c in A}

DESIGN = {
    "katana": ("만월(滿月) — 월인(月刃)", KA.form + " / 색: " + KA.color),
    "greatsword": ("산붕(山崩) — 핏빛 거암검", GB.form + " / 색: " + GB.color),
    "dagger": ("백귀(百鬼) — 귀화(鬼火)", DA.form + " / 색: " + DA.color),
    "bow": ("유성(流星) — 혜성 날개", BA.form + " / 색: " + BA.color),
}
LOOP = {"katana": (KA.tn, KA.loop_ms), "greatsword": (GB.tn, GB.loop_ms), "dagger": (DA.tn, DA.loop_ms), "bow": (BA.tn, BA.loop_ms)}


def dilate(pts, r):
    out = set()
    rr = int(math.ceil(r))
    offs = [(dx, dy) for dx in range(-rr, rr + 1) for dy in range(-rr, rr + 1) if dx * dx + dy * dy <= r * r]
    for x, y in pts:
        for dx, dy in offs:
            out.add((x + dx, y + dy))
    return out


class Ctx:
    """원 무기 프레임 + 확대 캔버스."""

    def __init__(self, im, weapon):
        self.im = im
        self.px = im.load()
        self.fw, self.fh = im.size
        pad = P.PAD[weapon]
        self.ox, self.oy = pad[0], pad[1]
        self.cv = Cv(self.fw + pad[0] + pad[2], self.fh + pad[1] + pad[3])
        self.solid_added = set()

    def orig(self, x, y):
        """확대 캔버스 좌표 → 원 프레임 픽셀(불투명이면 RGBA, 아니면 None)."""
        X, Y = x - self.ox, y - self.oy
        if 0 <= X < self.fw and 0 <= Y < self.fh:
            c = self.px[X, Y]
            return c if c[3] else None
        return None

    def put_orig(self, p, c, z=1):
        self.cv.put(p[0] + self.ox, p[1] + self.oy, c, z, False)

    def add(self, x, y, c, z=0, solid=False):
        if self.orig(x, y) is not None:
            return
        self.cv.put(x, y, c, z, solid)
        if solid:
            self.solid_added.add((int(x), int(y)))

    def shape(self, g, ang, box, fn):
        """g = 원 프레임 좌표의 축 원점. fn(u, v, X, Y) → (색, solid) | 색 | None (X, Y = 확대 캔버스 좌표)."""
        G0 = (g[0] + self.ox, g[1] + self.oy)
        tmp = Cv(self.cv.w, self.cv.h)
        tmp.shape(G0, ang, box, fn)
        for (x, y), (c, z, sol) in tmp.px.items():
            self.add(x, y, c, z, sol)

    def finish(self):
        for (x, y) in list(self.solid_added):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in self.cv.px and self.orig(*q) is None and 0 <= q[0] < self.cv.w and 0 <= q[1] < self.cv.h:
                    self.cv.px[q] = (INK, -9, True)
        return self.cv.image()


def axis_flip_up(ang):
    """−v 가 화면 위쪽을 보게 하는 flip(불꽃·가시가 위로)."""
    ny = math.cos(ang)              # v+ 방향 = (−sin, cos)
    if abs(ny) < 0.2:
        return 1 if -math.sin(ang) < 0 else -1
    return 1 if ny > 0 else -1


def local(p, g, ang):
    dx, dy = p[0] + 0.5 - g[0], p[1] + 0.5 - g[1]
    return dx * math.cos(ang) + dy * math.sin(ang), -dx * math.sin(ang) + dy * math.cos(ang)


# =============================================================================
# 칼 — 월인
# =============================================================================
def katana_frame(ctx, tip_a, grip_a, glow, sheathed, refine, t):
    px = ctx.px
    f = F(p=1.0, t=t, tn=KA.tn, glow=glow)
    bl = None if sheathed else OV.katana_blade(ctx.im, tip_a, refine)
    if bl is None or (tip_a is None and not bl[1]):
        # 칼집 안: 칼집 금을 은빛으로 + 칼집 위 작은 초승달
        hot = [(x, y) for y in range(ctx.fh) for x in range(ctx.fw) if px[x, y][3] and px[x, y][:3] in OV.SHEATH_GLOW]
        for k, p in enumerate(hot):
            ctx.put_orig(p, X1 if (p[0] + p[1] + t) % 4 == 0 else SIL[9])
        if hot:
            x, y = hot[len(hot) // 2]
            bob = (t % 4 > 1)
            gl = [(0, 0, SIL[8]), (1, 0, SIL[10]), (2, 1, X1), (2, 2, SIL[9]), (1, 3, SIL[7]), (0, 3, SIL[5])]
            for dx, dy, c in gl:
                ctx.add(x + ctx.ox + dx - 1, y + ctx.oy - 9 - bob + dy, c, 2)
        return
    pts, edge, a, b = bl
    tsu = [p for p in pts if P.hx(px[p]) in SLSET]
    if grip_a:
        g = (grip_a[0], grip_a[1])
    elif tsu:
        g = (sum(p[0] for p in tsu) / len(tsu), sum(p[1] for p in tsu) / len(tsu))
    else:
        g = (b[0] + 0.5, b[1] + 0.5)
    tip = (a[0] + 0.5, a[1] + 0.5)
    L = math.hypot(tip[0] - g[0], tip[1] - g[1])
    ang = math.atan2(tip[1] - g[1], tip[0] - g[0]) if L > 0.5 else 0.0
    sc = clamp(L / 58.0, 0.12, 1.3)
    flip = 1
    if edge:
        s = sum(local(p, g, ang)[1] for p in edge) / len(edge)
        flip = 1 if s >= 0 else -1
    tip_vis = tip_a is None or math.hypot(a[0] - tip_a[0], a[1] - tip_a[1]) < 6
    pp = KA.pulse_pos(f)
    for p in pts:
        c = P.hx(px[p])
        if c in SLSET or c in PLSET:
            continue
        ud = local(p, g, ang)[0] / sc
        pulse = abs(ud - pp) < 3
        if c in EDGE_HEX:
            col = X0 if (glow or pulse) else X1
        else:
            Lm = P.lum(px[p])
            lv = 9 if Lm > 120 else 6 if Lm > 96 else 4 if Lm > 74 else 2
            col = SIL[min(11, lv + (3 if pulse else 0))]
        ctx.put_orig(p, col)
    near = dilate(pts, 3.2)
    if L >= 10:
        def fn(u, v, X, Y):
            ud = u / sc
            e = KA.ext(ud, v * flip, f, x=X, y=Y)
            if not e:
                return None
            if ud > B.K_U1 - 2:
                return e if tip_vis else None
            return e if (X - ctx.ox, Y - ctx.oy) in near else None
        ctx.shape(g, ang, (0, (B.K_U1 + 40) * sc, -34, 34), fn)
    # 보름달 코등이
    if tsu:
        cx = sum(p[0] for p in tsu) / len(tsu)
        cy = sum(p[1] for p in tsu) / len(tsu)
        R = 7.6
        for y in range(int(cy - R) - 1, int(cy + R) + 2):
            for x in range(int(cx - R) - 1, int(cx + R) + 2):
                du, dv = local((x, y), (cx, cy), ang)
                dd = math.hypot(du, dv)
                if dd > R:
                    continue
                c = KA.disc(du + 1.2, dv * flip, f)
                if not c:
                    continue
                X, Y = x + ctx.ox, y + ctx.oy
                o = ctx.orig(X, Y)
                if o is None:
                    ctx.add(X, Y, c[0], 0, True)
                elif P.hx(o) in SLSET:
                    ctx.cv.put(X, Y, c[0], 1, False)
    # 달 조각(날이 충분히 보일 때)
    if sc > 0.45 and tip_vis:
        shard = [(0, 0, SIL[9]), (1, 0, SIL[10]), (2, 1, X1), (3, 2, X1), (3, 3, SIL[10]), (2, 4, SIL[8]), (1, 5, SIL[7]), (0, 5, SIL[6])]
        for k, (u, v) in enumerate(((26, -9), (50, -12), (74, -22))):
            bob = round(1.5 * math.sin(2 * math.pi * (f.ph + k / 3)))
            x, y = K6.L2W((g[0] + ctx.ox, g[1] + ctx.oy), ang, u * sc, (v - bob) * flip)
            for dx, dy, c in shard:
                ctx.add(int(x) + dx, int(y) + dy, c, 2)


# =============================================================================
# 대검 — 핏빛 거암검
# =============================================================================
def gs_frame(ctx, grip, tip, glow, t):
    im, px = ctx.im, ctx.px
    if tip and not grip:
        comps = OV.components(im)
        if comps:
            c = min(comps, key=lambda cc: min((x - tip[0]) ** 2 + (y - tip[1]) ** 2 for x, y in cc))
            pm = max(c, key=lambda p: (p[0] - tip[0]) ** 2 + (p[1] - tip[1]) ** 2)
            grip = (pm[0] + (tip[0] - pm[0]) * 0.17, pm[1] + (tip[1] - pm[1]) * 0.17)
    if not (grip and tip):
        return
    pts = OV.gs_blade(im, grip, tip)
    if not pts:
        return
    pts = {p for p in pts if P.hx(px[p]) not in SLSET}
    g = (grip[0], grip[1])
    L = math.hypot(tip[0] - g[0], tip[1] - g[1])
    if L < 4:
        return
    ang = math.atan2(tip[1] - g[1], tip[0] - g[0])
    sc = clamp(L / 93.0, 0.12, 1.3)
    flip = axis_flip_up(ang)
    f = F(p=1.0, t=t, tn=GB.tn, glow=glow, flip=flip)
    Lc = 111.0
    burst = GB.burst(f)
    tip_vis = min(math.hypot(p[0] - tip[0], p[1] - tip[1]) for p in pts) < 6
    for p in pts:
        u, v = local(p, g, ang)
        ud, vd = u / sc, v * flip
        X, Y = p[0] + ctx.ox, p[1] + ctx.oy
        d = GB.fiss(ud, vd, 1.0, Lc) if ud >= 9 else 9
        if d < (2.3 if burst else 1.6):
            col = GB.blood(ud, d, f, glow, X, Y, Lc)
        elif d < 3.2 and h2(X, Y, 233) > 0.72:
            col = CRI[2]
        else:
            Lm = P.lum(px[p])
            lv = 7 if Lm > 140 else 5 if Lm > 112 else 4 if Lm > 88 else 3 if Lm > 64 else 2
            if h2(X // 2, Y // 2, 13) > 0.84:
                lv -= 1
            col = G[max(1, lv)]
        ctx.put_orig(p, col)
    near = dilate(pts, 10)

    def fn(u, v, X, Y):
        ud, vd = u / sc, v * flip
        if ud < 8:
            return None
        if ud > 93 and not tip_vis:
            return None
        if ud <= 93 and (X - ctx.ox, Y - ctx.oy) not in near:
            return None
        r = GB.px(ud, vd, X, Y, f)
        return r
    ctx.shape(g, ang, (6 * sc, Lc * sc + 1, -24, 24), fn)
    # 터짐·방울
    G0 = (g[0] + ctx.ox, g[1] + ctx.oy)
    cyc = f.t % 10
    W = lambda u, v: K6.L2W(G0, ang, u * sc, v * flip)  # noqa: E731
    for k, (eu, ev, side) in enumerate(GB.ENDS):
        u0 = 3 + (eu - 3) * (Lc - 3) / 90.0
        if u0 > 93 and not tip_vis:
            continue
        if burst or glow:
            for m in range(10):
                dist = 3 + 2.0 * m + 3 * h2(k, m, 241)
                lat = (h2(k, m, 242) - 0.5) * (4 + m)
                if side == 0:
                    uu, vv = u0 + dist, lat * 0.6
                else:
                    uu, vv = u0 + lat * 0.5, ev + side * dist
                x, y = W(uu, vv)
                y += 0.035 * dist * dist
                c = X1 if m == 0 and h2(k, 1, 243) > 0.5 else CRI[7] if m < 2 else CRI[6] if m < 5 else CRI[4]
                ctx.add(x, y, c, 2)
                if m < 4:
                    ctx.add(x + 1, y, CRI[5], 2)
        elif cyc >= 7 and side > 0:
            x, y = W(u0, ev + 1)
            yy = y + 2 + (cyc - 7) * 4 + 2 * (k % 2)
            ctx.add(x, yy, CRI[6], 2)
            ctx.add(x, yy + 1, CRI[4], 2)


# =============================================================================
# 단검 — 귀화
# =============================================================================
def dagger_frame(ctx, grip, tip, glow, t):
    im, px = ctx.im, ctx.px
    if grip is None and tip is not None:
        comps = OV.components(im)
        c = min(comps, key=lambda cc: min((x - tip[0]) ** 2 + (y - tip[1]) ** 2 for x, y in cc)) if comps else None
        grip = max(c, key=lambda p: (p[0] - tip[0]) ** 2 + (p[1] - tip[1]) ** 2) if c else None
    if not (grip and tip):
        return
    pts = FA.seg_mask(im, grip, tip, rad=5.5, umin=0.25)
    pts = {p for p in pts if P.hx(px[p]) not in PLSET}
    if len(pts) < 4:
        return
    g = (grip[0], grip[1])
    L = math.hypot(tip[0] - g[0], tip[1] - g[1])
    ang = math.atan2(tip[1] - g[1], tip[0] - g[0])
    sc = clamp(L / 26.0, 0.2, 1.4)
    flip = axis_flip_up(ang)
    f = F(p=1.0, t=t, tn=DA.tn, glow=glow, flip=flip)
    tip_vis = min(math.hypot(p[0] - tip[0], p[1] - tip[1]) for p in pts) < 5
    for p in pts:
        c = P.hx(px[p])
        if c in AMBER:
            col = X1 if glow else VIO[10]
        else:
            Lm = P.lum(px[p])
            col = VIO[8] if Lm > 112 else VIO[4] if Lm > 86 else VIO[3] if Lm > 64 else VIO[2]
        ctx.put_orig(p, col)
    near = dilate(pts, 4)

    def fn(u, v, X, Y):
        ud, vd = u / sc, v * flip
        c = DA.flame(ud, vd, f, X, Y)
        if not c:
            return None
        if not tip_vis and (X - ctx.ox, Y - ctx.oy) not in near:
            return None
        return c
    ctx.shape(g, ang, (0, 50 * sc, -24, 24), fn)
    if tip_vis:
        G0 = (g[0] + ctx.ox, g[1] + ctx.oy)
        for k in range(4):
            u = (10 + 8 * k) * sc
            v = -10 - ((f.t * 3 + k * 4) % 9)
            x, y = K6.L2W(G0, ang, u, v * flip)
            ctx.add(x, y - ((f.t + k) % 3), TEAL[9] if k % 2 else VIO[9], 2)


# =============================================================================
# 활 — 혜성 날개
# =============================================================================
def bow_frame(ctx, grip, tip, hand_r, state, glow, t):
    im, px = ctx.im, ctx.px
    allp = [(x, y) for y in range(ctx.fh) for x in range(ctx.fw) if px[x, y][3]]
    if len(allp) < 6:
        return
    if grip is None:
        grip = (sum(p[0] for p in allp) / len(allp), sum(p[1] for p in allp) / len(allp))
    g = (grip[0], grip[1])
    full = state in ("full",)
    rel = state in ("release",)
    f = F(p=1.0, t=t, tn=BA.tn, glow=glow or rel)
    # 1) 다시 칠하기
    for p in allp:
        c = P.hx(px[p])
        if c in PLSET:
            continue
        if c in AMBER:
            col = X0 if rel else X1 if full else GOLD[10]
        elif c in SLSET:
            col = GOLD[10] if P.lum(px[p]) > 75 else GOLD[5]
        else:
            Lm = P.lum(px[p])
            col = GOLD[9] if Lm > 108 else GOLD[6] if Lm > 84 else A[4] if Lm > 58 else A[3]
        ctx.put_orig(p, col)
    # 2) 활대 축(PCA) — 화살(줌통 → 촉 선) 근처 제외
    limb = [p for p in allp if P.hx(px[p]) not in AMBER]
    aim_ref = None
    if hand_r is not None and state in ("draw", "full", "release") and math.hypot(hand_r[0] - g[0], hand_r[1] - g[1]) > 10:
        aim_ref = (g[0] - hand_r[0], g[1] - hand_r[1])           # 시위 손 → 줌통 = 쏘는 방향
    elif tip is not None and math.hypot(tip[0] - g[0], tip[1] - g[1]) > 8:
        aim_ref = (tip[0] - g[0], tip[1] - g[1])
    if aim_ref is not None:
        ex, ey = aim_ref
        ll = math.hypot(ex, ey) or 1
        limb = [p for p in limb if abs(((p[0] + 0.5 - g[0]) * -ey + (p[1] + 0.5 - g[1]) * ex) / ll) > 2.5]
    if len(limb) < 14:
        return
    mx = sum(p[0] for p in limb) / len(limb)
    my = sum(p[1] for p in limb) / len(limb)
    sxx = sum((p[0] - mx) ** 2 for p in limb)
    syy = sum((p[1] - my) ** 2 for p in limb)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in limb)
    th = 0.5 * math.atan2(2 * sxy, sxx - syy)
    e = (math.cos(th), math.sin(th))
    n = (-e[1], e[0])
    offs = [((p[0] + 0.5 - g[0]) * n[0] + (p[1] + 0.5 - g[1]) * n[1]) for p in limb]
    if sum(offs) / len(offs) > 0:          # 활 끝은 줌통보다 뒤(쏘는 쪽 반대)
        n = (-n[0], -n[1])
    if aim_ref is not None:
        if aim_ref[0] * n[0] + aim_ref[1] * n[1] < 0:
            n = (-n[0], -n[1])
    ss = [((p[0] + 0.5 - g[0]) * e[0] + (p[1] + 0.5 - g[1]) * e[1]) for p in limb]
    smin, smax = min(ss), max(ss)
    if smax - smin < 18:
        return
    G0 = (g[0] + ctx.ox, g[1] + ctx.oy)
    scale = clamp((smax - smin) / 68.0, 0.4, 1.25)

    def limb_point(s_target):
        cand = [(p, s) for p, s in zip(limb, ss) if abs(s - s_target) < 1.6]
        if not cand:
            return None
        return (sum(p[0] for p, _ in cand) / len(cand) + 0.5, sum(p[1] for p, _ in cand) / len(cand) + 0.5)
    # 3) 불꽃 깃 6장
    for sgn, half in ((-1, -smin), (1, smax)):
        if half < 8:
            continue
        for k in range(3):
            root = limb_point(sgn * half * (0.5 + 0.22 * k))
            if root is None:
                continue
            wob = 1 + 0.12 * math.sin(2 * math.pi * (f.ph + k / 3)) + (0.25 if rel else 0)
            Lf = (17 + 5 * k) * wob * scale
            angk = math.radians(172 - 26 * k)
            dvec = (math.cos(angk) * n[0] + math.sin(angk) * sgn * e[0], math.cos(angk) * n[1] + math.sin(angk) * sgn * e[1])
            bvec = (-dvec[1], dvec[0])
            # 휘는 방향: 바깥(활대 끝 쪽)
            out_sign = 1 if (bvec[0] * sgn * e[0] + bvec[1] * sgn * e[1]) > 0 else -1
            R0 = (root[0] + ctx.ox, root[1] + ctx.oy)
            for y in range(int(R0[1] - Lf - 5), int(R0[1] + Lf + 6)):
                for x in range(int(R0[0] - Lf - 5), int(R0[0] + Lf + 6)):
                    dx, dy = x + 0.5 - R0[0], y + 0.5 - R0[1]
                    a_ = dx * dvec[0] + dy * dvec[1]
                    b_ = dx * bvec[0] + dy * bvec[1]
                    if a_ < 0 or a_ > Lf:
                        continue
                    s_ = a_ / Lf
                    cc = 4.0 * s_ ** 2 * scale * out_sign
                    w = (3.4 * (1 - s_) ** 0.7 + 0.3) * max(0.6, scale)
                    d = b_ - cc
                    if abs(d) > w:
                        continue
                    if s_ > 0.7 and h2(x, y, 171 + f.t) > 1.6 - s_ * 1.4:
                        continue
                    q = 1 - abs(d) / w
                    col = X1 if (q > 0.7 and s_ < 0.6) else (GOLD[10] if s_ < 0.5 else GOLD[8]) if q > 0.45 else GOLD[6] if q > 0.2 else A[5]
                    ctx.add(x, y, col, 0)
    # 4) 유성 핵(줌통 앞)
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * f.ph)
    cxp, cyp = G0[0] + n[0] * 2.5, G0[1] + n[1] * 2.5
    for y in range(int(cyp) - 5, int(cyp) + 6):
        for x in range(int(cxp) - 5, int(cxp) + 6):
            dd = math.hypot(x + 0.5 - cxp, y + 0.5 - cyp)
            if dd <= 3.6:
                ctx.add(x, y, X1 if dd < 1.3 + 0.6 * pulse else GOLD[9] if dd < 2.6 else A[4], 1, True)
    # 5) 시위에 건 화살촉 = 불덩이
    if tip is not None and state in ("draw", "full"):
        T = (tip[0] + ctx.ox, tip[1] + ctx.oy)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                r = math.hypot(dx, dy)
                if r <= 2.4:
                    ctx.cv.put(T[0] + dx, T[1] + dy, X1 if r < 1.2 else GOLD[9] if r < 2 else A[5], 3, False)


# =============================================================================
def overlay_job(arg):
    weapon, sheet = arg
    j, fr = P.K57.grid_frames("weapons/v3/" + sheet)
    note = None
    try:
        blade_only = OV.body_in_overlay_masks(j, sheet, fr)
    except AssertionError as e:
        blade_only = {}
        note = "bodyInOverlayFrames 마스크 크기 불일치 — 몸이 든 칸은 오버레이 비움(%s)" % (e,)
    skip = set(j.get("bodyInOverlayFrames") or []) if (note and j.get("bodyInOverlayFrames")) else set()
    for (d, i), im in blade_only.items():
        fr[d][i] = im
    glow = set(j.get("glowFrames") or [])
    tips = j.get("bladeTipAnchors") if isinstance(j.get("bladeTipAnchors"), dict) else None
    grips = j.get("gripAnchors") if isinstance(j.get("gripAnchors"), dict) else None
    hands = j.get("handAnchors") if isinstance(j.get("handAnchors"), dict) else None
    states = j.get("frameStates")
    tn, lms = LOOP[weapon]
    st_ms = P.starts(j["frameDurationsMs"])
    frames = {}
    for d in j["directions"]:
        lst = []
        for i, im in enumerate(fr[d]):
            ctx = Ctx(im, weapon)
            t = int(st_ms[i] / lms) % tn
            tip = tips[d][i] if tips else None
            grip = grips[d][i] if grips and grips.get(d) else None
            g = i in glow
            if i not in skip:
                if weapon == "katana":
                    sh = (tips is not None and tip is None) or bool(states and states[i] in OV.SHEATHED_STATES)
                    katana_frame(ctx, tip, grip, g, sh, bool(states) and not tips, t)
                elif weapon == "greatsword":
                    gs_frame(ctx, grip, tip, g, t)
                elif weapon == "dagger":
                    dagger_frame(ctx, grip, tip, g, t)
                else:
                    hr = hands[d][i].get("handR") if hands and hands.get(d) and hands[d][i] else None
                    bow_frame(ctx, grip, tip, hr, states[i] if states else None, g, t)
            lst.append(ctx.finish())
        frames[d] = lst
    name = sheet + "_awaken"
    ox, oy = P.PAD[weapon][0], P.PAD[weapon][1]
    meta = {k: j[k] for k in OV.COPY if k in j}
    for k in ("frames", "frameWidth", "frameHeight", "glowFrames"):
        meta.pop(k, None)
    pv = j.get("pivot", {"x": 96, "y": 186})
    po = j.get("playerFrameOffset", {"x": 48, "y": 48})
    meta["pivot"] = {"x": pv["x"] + ox, "y": pv["y"] + oy}
    meta["playerFrameOffset"] = {"x": po["x"] + ox, "y": po["y"] + oy}
    meta["weaponSheetPivot"] = pv
    meta["pivotDelta"] = {"x": ox, "y": oy}
    aw, design = DESIGN[weapon]
    meta.update(overlayOf="weapons/v3/" + sheet, depth="above_weapon", weapon=weapon, awakening=aw, design=design,
                drawRule=("무기 시트 '%s' 를 그린 바로 위에 같은 프레임 번호(row*atlas.grid.columns+col)·같은 시각으로 겹친다. 틀이 원 무기 시트보다 크다(60 Q20): "
                          "이 시트의 pivot = 주인공 피벗 자리(원 무기 pivot + pivotDelta), playerFrameOffset 도 같은 만큼 큼 → 주인공 피벗에 이 pivot 을 맞추면 무기와 정확히 겹친다. "
                          "각성한 런에서만. 검기·울분 오버레이가 있으면 그 위(무기 → _awaken → _ki/_grudge)") % sheet,
                loopFrames=tn, loopMs=lms,
                loopRule="순환 위상 = (그 프레임 시작 ms ÷ %dms) mod %d — 시트마다 같은 속도로 맥동(60 Q21 '각성 상태 순환 6~12프레임')" % (lms, tn),
                glowRule="glowFrames(무기 시트 판정 순간)에 가장 밝음(X0). 60 Q19 로 각성은 재·호박·백열 위치 규칙의 예외 — 순환 맥동에도 X1 사용")
    if note:
        meta["bodyInOverlayNote"] = note
    P.write_sheet(name, P.STAGE_W, j["directions"], frames, j["frameDurationsMs"], meta, loop=j.get("loop", False), glow=glow)
    return name


SHEETS = FA.SHEETS


def build(flt=None, procs=8):
    from multiprocessing import Pool
    jobs = [s for s in SHEETS if not flt or any(x in s[1] for x in flt)]
    with Pool(procs) as p:
        for r in p.imap_unordered(overlay_job, jobs):
            print(r, flush=True)


if __name__ == "__main__":
    build(sys.argv[1:])
