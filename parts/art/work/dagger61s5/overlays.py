"""단검 각성 외형 — weapons/v3/dagger_<동작>_awaken(= 백귀 1차) · weapons/v4/dagger_<갈래>_{a1,a2,a2_glow}_<동작> 을 '재 발톱' 날로.

같은 축·가림(blade.Geo)을 기본 무기 시트와 공유한다 → 오버레이가 기본 날을 정확히 덮고, 덧붙임만 실루엣을 바꾼다.
틀·피벗·프레임·ms·행 = 기존 오버레이 그대로(틀 = 무기 + 사방 32, pivotDelta (32,32)).
갈래 외형(계약 §26 · P12 설계의 갈래 한 줄 양상은 유지, 모양은 발톱 날 언어로 다시):
  쌍격 twin   a1 은백 날 + 등 쪽에 나란한 둘째 발톱 날(짧게) + 두 날을 잇는 가로막이 / a2 앞뒤로 뻗은 X 막이 날개 + 둘째 날 끝 미늘 / 빛 날선 쪽 '분신 날' 윤곽
  질풍 gale   a1 녹청 넓은 발톱 날 + 큰 바람 고리 + 코등이에서 ±32° 로 펼친 작은 발톱 2(부채 셋) / a2 ±62° 발톱 2 더(부채 다섯) + 고리 바람 끈 2 / 빛 부채 날 바람 줄 · 날선 맥동 · 고리 테
  백귀 hyakki a1 = 각성(귀화): 보라 날 + 청록 불혀 날선 + 등 위 일렁이는 혼불 / a2 코등이 양쪽 뼈빛 도깨비 뿔 2 / 빛 코등이 둘레 혼불 2 + 뿔 끝
"""
import math

import d5
import blade as BL
import weapons as WP
from blade import Skin
from d5 import Cv, h2, clamp

PAD = 32
V4 = "v4-r61s5"


def phase_of(ms0, tn=6, loop=80):
    return int(ms0 / loop) % tn


# =============================================================================
# 피부
# =============================================================================
class OnibiSkin(Skin):
    """귀화: 보라 몸 · 청록 불혀 날선 · 백열 끝(판정)."""
    name = "hyakki"

    def col(self, part, s, d, state, x, y, ph):
        V, T, G = d5.VIO, d5.TEAL, d5.G
        hot = state == "glow"
        if part == "ring":
            return T[8] if (d < 0.5 and s > 0.5) else V[6] if s > 0.5 else V[3]
        if part == "wrap":
            k = int(math.floor((s + 6) / 1.5))
            return d5.PL[0] if k % 2 == 0 else d5.PL[2]
        if part == "guard":
            return V[4] if d < 0 else V[2]
        if part == "out":
            return V[1]
        if part == "spine":
            return V[9] if (h2(x, y, ph) < 0.25 + 0.15 * (ph % 3)) else V[8]
        if part == "body":
            return V[6] if d < -0.2 else V[5] if d < 0.35 else V[4]
        if part == "vein":
            return T[9] if hot else T[7]
        if part == "edge":
            band = (s * 6 - ph) % 6 < 1.0                 # 청록 띠가 밑동 → 끝으로 타고 오름
            return (T[11] if hot else T[10]) if band else (T[9] if s > 0.5 else T[7])
        if part == "tip":
            return d5.X1 if hot and d > -0.4 else T[10] if d > -0.3 else V[9]
        return None


class TwinSkin(Skin):
    """쌍격: 은백 강철 · 청록 날선."""
    name = "twin"

    def col(self, part, s, d, state, x, y, ph):
        S, T, G = d5.SIL, d5.TEAL, d5.G
        hot = state == "glow"
        if part == "ring":
            return S[9] if (d < 0.5 and s > 0.5) else S[5] if s > 0.5 else S[3]
        if part == "wrap":
            k = int(math.floor((s + 6) / 1.5))
            return d5.PL[1] if k % 2 == 0 else d5.PL[3]
        if part == "guard":
            return S[6] if d < 0 else S[3]
        if part == "out":
            return S[1]
        if part == "spine":
            return S[10] if hot else S[9]
        if part == "body":
            return S[7] if d < -0.2 else S[5] if d < 0.35 else S[4]
        if part == "vein":
            return T[8]
        if part == "edge":
            return (d5.X1 if s > 0.6 else T[10]) if hot else (T[9] if s > 0.5 else T[7])
        if part == "tip":
            return d5.X1 if hot else T[10] if d > -0.3 else S[9]
        return None


class GaleSkin(Skin):
    """질풍: 녹청 잎 강철 · 연두 날선."""
    name = "gale"

    def col(self, part, s, d, state, x, y, ph):
        R, G = d5.GRN, d5.G
        hot = state == "glow"
        if part == "ring":
            return R[9] if (d < 0.5 and s > 0.5) else R[6] if s > 0.5 else R[3]
        if part == "wrap":
            k = int(math.floor((s + 6) / 1.5))
            return d5.PL[0] if k % 2 == 0 else d5.PL[2]
        if part == "guard":
            return R[5] if d < 0 else R[3]
        if part == "out":
            return R[1]
        if part == "spine":
            return R[9] if hot else R[8]
        if part == "body":
            return R[6] if d < -0.2 else R[5] if d < 0.35 else R[4]
        if part == "vein":
            return R[9]
        if part == "edge":
            return (d5.X1 if s > 0.6 else R[11]) if hot else (R[10] if s > 0.45 else R[9])
        if part == "tip":
            return d5.X1 if hot else R[11] if d > -0.3 else R[8]
        return None


# =============================================================================
# 덧붙임 도구 — 국소 (u, v) 모양을 화면에 (가림 규칙 포함)
# =============================================================================
def near_handle(geo):
    return geo.cov is None or any(k in geo.cov for k in range(-1, 9))


def field(cv, geo, box, fn, gate="blade", ox=PAD, oy=PAD):
    """box = (u0, u1, v0, v1) 안 픽셀마다 fn(u, v, x, y) → 색|None. gate: blade(그 u 의 날이 보일 때) · handle(손잡이 쪽 보일 때) · tip."""
    if geo.cov is not None and geo.count == 0:
        return
    u0, u1, v0, v1 = box
    pts = [geo.w(u, v) for u in (u0, u1) for v in (v0, v1)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    hn = near_handle(geo)
    ts = geo.tip_seen()
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            u, v = geo.loc(x, y)
            if not (u0 <= u <= u1 and v0 <= v <= v1):
                continue
            if gate == "handle" and not hn:
                continue
            if gate == "tip" and not ts:
                continue
            if gate == "blade" and not geo.seen(clamp(u, 0, geo.L)):
                continue
            c = fn(u, v, x, y)
            if c:
                cv.put(x + ox, y + oy, c)


def talon(u, v, u0, L, ang_deg, vbase, w=1.6, hook=1.0):
    """작은 발톱 날(국소): 시작 (u0, vbase) 에서 ang 방향으로 길이 L, 끝이 hook 쪽으로 휨. → (s, d, hw) | None."""
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    x, y = u - u0, v - vbase
    al = x * ca + y * sa
    pe = -x * sa + y * ca
    if not (0 <= al <= L):
        return None
    s = al / L
    c = -hook * 1.8 * math.sin(math.pi * s ** 1.3) * (1 - 0.15 * s) * (1 if ang_deg >= 0 else -1)
    hw = w * (math.sin(math.pi * min(1.0, s * 1.15)) ** 0.6) if s < 0.87 else w * (1 - s) / 0.13 * 0.6
    dd = pe - c
    if abs(dd) <= hw + 0.05 and hw > 0.25:
        return s, dd, hw
    return None


# ---------------------------------------------------------------- 쌍격
def twin_a1(cv, geo, st, ph):
    S, T = d5.SIL, d5.TEAL
    L = geo.L

    def fn(u, v, x, y):
        # 둘째 발톱 날: 등 쪽(−v) 5.5 도트 옆, 길이 0.72L, 같은 휨
        if 1.0 <= u <= 0.72 * L + 1:
            s = (u - 1.0) / (0.72 * L)
            c = -5.6 + BL.vc_of(s, 0.72 * L) * 0.9
            hw = 1.5 * (1.0 if s < 0.6 else max(0.0, (1 - s) / 0.4))
            if abs(v - c) <= hw + 0.05 and hw > 0.3:
                if s > 0.85:
                    return d5.X1 if st == "glow" else T[10]
                return S[9] if v - c < -0.5 else S[4] if v - c > 0.5 else S[7]
        # 가로막이(두 날을 잇는 막대)
        if -0.6 <= u <= 1.4 and -8.2 <= v <= 2.8:
            return S[6] if u < 0.4 else S[3]
        return None
    field(cv, geo, (-1, L * 0.75 + 2, -9, 3.5), fn)


def twin_a2(cv, geo, st, ph):
    S = d5.SIL
    L = geo.L

    def fn(u, v, x, y):
        for (a0, b0) in (((0.6, -8.2), (6.0, -12.0)), ((0.6, 2.8), (5.6, 6.6)), ((0.2, -8.2), (-4.4, -11.4))):
            ex, ey = b0[0] - a0[0], b0[1] - a0[1]
            ll = ex * ex + ey * ey
            k = clamp(((u - a0[0]) * ex + (v - a0[1]) * ey) / ll)
            dd = math.hypot(u - (a0[0] + ex * k), v - (a0[1] + ey * k))
            if dd <= 1.25 - 0.75 * k:
                return S[8] if v < (a0[1] + b0[1]) / 2 else S[4]
        # 둘째 날 끝 미늘(뒤로 꺾인 가시)
        u2 = 0.72 * L * 0.8
        if u2 - 3 <= u <= u2 and -9.2 + (u2 - u) * 0.5 <= v <= -7.0:
            return S[5]
        return None
    field(cv, geo, (-6, L * 0.75, -13, 8), fn, gate="handle")


def twin_glow(cv, geo, st, ph):
    G = d5.G
    L = geo.L

    def inside(u, v):
        if not (2 <= u <= L * 0.95):
            return False
        s = u / L
        return abs(v - (6.5 + BL.vc_of(s, L))) <= BL.hw_of(s, L) * 0.85

    def fn(u, v, x, y):
        if inside(u, v) and not all(inside(u + du, v + dv) for du, dv in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            return d5.X0 if (abs(u - (ph / 6.0) * L) < 3 or st == "glow") else G[12]
        s = u / L if L else 0
        if 0.1 < s < 0.86 and 0 <= v - BL.vc_of(s, L) - (BL.hw_of(s, L) - 0.9) <= 0.9:
            return G[11]
        return None
    field(cv, geo, (0, L, -4, 12), fn)


# ---------------------------------------------------------------- 질풍
FAN1 = 32
FAN2 = 62


def gale_fan(u, v, deg, L0, L1, w):
    for sg in (-1, 1):
        r = talon(u, v, -0.5, L1, deg * sg, 0.0, w=w, hook=0.8)
        if r and r[0] * L1 >= L0:
            return r, sg
    return None


def gale_a1(cv, geo, st, ph):
    R = d5.GRN

    def fn(u, v, x, y):
        r = gale_fan(u, v, FAN1, 3.0, min(15.0, geo.L * 0.5), 1.7)
        if r:
            (s, dd, hw), sg = r
            if s > 0.86:
                return d5.X1 if st == "glow" else R[11]
            return R[10] if abs(dd) > hw - 0.8 else R[7] if dd * sg < 0 else R[4]
        rr = math.hypot(u + 10.5, v - 1.2)                # 큰 바람 고리
        if 2.6 <= rr <= 4.3:
            return R[9] if v < 1.2 else R[5]
        return None
    field(cv, geo, (-15.5, 16, -10, 10), fn, gate="handle")


def gale_a2(cv, geo, st, ph):
    R = d5.GRN

    def fn(u, v, x, y):
        r = gale_fan(u, v, FAN2, 2.0, 10.0, 1.4)
        if r:
            (s, dd, hw), sg = r
            return R[10] if abs(dd) > hw - 0.7 else R[6] if dd * sg < 0 else R[4]
        for sg in (-1, 1):                                # 고리에 매단 바람 끈 2
            if -25 <= u <= -14.5:
                t = (-u - 14.5) / 10.5
                c = 1.2 + sg * (1.5 + 2.2 * t) + 2.0 * math.sin(t * 5 - 2 * math.pi * ph / 6.0 + sg) * t
                if abs(v - c) <= 0.85 - 0.35 * t:
                    return R[8] if int(t * 6) % 2 == 0 else R[5]
        return None
    field(cv, geo, (-26, 11, -12, 12), fn, gate="handle")


def gale_glow(cv, geo, st, ph):
    G = d5.G
    pp = ph / 6.0

    def fn(u, v, x, y):
        for deg, L1 in ((FAN1, min(15.0, geo.L * 0.5)), (FAN2, 10.0)):
            for sg in (-1, 1):
                a = math.radians(deg * sg)
                x0, y0 = u + 0.5, v
                al = x0 * math.cos(a) + y0 * math.sin(a)
                pe = -x0 * math.sin(a) + y0 * math.cos(a)
                if 3 <= al <= L1 - 2 and abs(pe) < 0.5:
                    return d5.X0 if abs(al / L1 - pp) < 0.2 else G[11]
        s = u / geo.L if geo.L else 0
        if 0.1 < s < 0.9:
            dd = v - BL.vc_of(s, geo.L)
            hw = BL.hw_of(s, geo.L, 1.15)
            if hw - 0.9 <= dd <= hw + 0.1:
                return d5.X0 if abs(s - pp) < 0.12 else G[12]
        rr = math.hypot(u + 10.5, v - 1.2)
        if 4.3 < rr <= 5.0:
            return G[11]
        return None
    field(cv, geo, (-16, geo.L, -12, 12), fn, gate="handle")


# ---------------------------------------------------------------- 백귀
def onibi_wisps(cv, geo, st, ph):
    """등 위로 일렁이는 혼불 3점(순환) — a1(=_awaken)."""
    if not geo.tip_seen() and geo.vis < 0.5:
        return
    T, V = d5.TEAL, d5.VIO
    for k in range(3):
        s = 0.25 + 0.25 * k
        u = geo.L * s
        v = BL.vc_of(s, geo.L) - BL.hw_of(s, geo.L) - 2.5 - 2.0 * math.sin((ph + 2 * k) * math.pi / 3)
        if not geo.seen(u):
            continue
        x, y = geo.w(u, v)
        c = T[10] if (ph + k) % 3 == 0 else V[9]
        cv.put(x + PAD, y + PAD, c)
        if (ph + k) % 2 == 0:
            x2, y2 = geo.w(u, v - 2)
            cv.put(x2 + PAD, y2 + PAD, V[7])


def hyakki_a2(cv, geo, st, ph):
    def fn(u, v, x, y):
        for sg in (-1, 1):
            for k in range(11):
                t = k / 10.0
                cu, cv_ = 0.5 - 7 * t, sg * (3 + 6 * t + 2 * t * t) + 0.4
                if math.hypot(u - cu, v - cv_) <= 1.7 * (1 - t) + 0.45:
                    return d5.PL[4] if (v - cv_) * sg < 0 else d5.PL[2]
        return None
    field(cv, geo, (-8, 2, -12, 12), fn, gate="handle")


def hyakki_glow(cv, geo, st, ph):
    G = d5.G

    def fn(u, v, x, y):
        for k in range(2):
            a = 2 * math.pi * (ph / 6.0 + k / 2.0)
            cu, cv_ = -2 + 6 * math.cos(a), 7.5 * math.sin(a)
            dd = math.hypot(u - cu, v - cv_)
            if dd <= 0.8:
                return d5.X0
            if 1.4 <= dd <= 2.1:
                return G[12]
        for sg in (-1, 1):
            if math.hypot(u + 6.5, v - sg * 11 - 0.4) < 0.9:
                return d5.X0
        return None
    field(cv, geo, (-9, 6, -12, 12), fn, gate="handle")


BRANCH = {
    "twin": dict(skin=TwinSkin(), widen=1.0, ring=1.0, a1=twin_a1, a2=twin_a2, gl=twin_glow,
                 a1_design="은백 발톱 날(청록 날선) + 등 쪽 5.5 도트 옆 나란한 짧은 둘째 발톱 날 + 두 날을 잇는 가로막이 — 쌍날 실루엣",
                 a2_design="가로막이 앞뒤로 뻗은 X 막이 날개 3 + 둘째 날 끝 미늘", glow_design="날선 쪽에 나란히 뜬 '분신 날' 윤곽(셋째 날, 순환 빛) + 날선 줄"),
    "gale": dict(skin=GaleSkin(), widen=1.15, ring=1.3, a1=gale_a1, a2=gale_a2, gl=gale_glow,
                 a1_design="녹청 넓은 발톱 날 + 큰 바람 고리 + 코등이에서 ±32° 로 펼친 작은 발톱 2(부채 셋)",
                 a2_design="±62° 작은 발톱 2 더(부채 다섯) + 고리에 매단 바람 끈 2(순환 일렁임)", glow_design="부채 날마다 바람 줄(순환) + 날선 맥동 + 고리 테"),
    "hyakki": dict(skin=OnibiSkin(), widen=1.0, ring=1.0, a1=onibi_wisps, a2=hyakki_a2, gl=hyakki_glow,
                   a1_design="귀화(최종 각성 재사용): 보라 발톱 날 + 청록 불혀 날선(청록 띠가 밑동 → 끝으로 타고 오름) + 등 위 혼불 3점 일렁임",
                   a2_design="코등이 양쪽에서 뒤로 휘어 솟는 뼈빛 도깨비 뿔 2", glow_design="코등이 둘레를 맴도는 혼불 2(고리 + 심) + 뿔 끝"),
}


def render(geo, bid, st, ph, size):
    """→ (a1, a2, glow) 각 size 캔버스(무기 틀 + 사방 PAD)."""
    b = BRANCH[bid]
    c1, c2, c3 = Cv(*size), Cv(*size), Cv(*size)
    BL.paint(c1, geo, b["skin"], st, ph, PAD, PAD, widen=b["widen"], ring_scale=b["ring"])
    b["a1"](c1, geo, st, ph)
    b["a2"](c2, geo, st, ph)
    b["gl"](c3, geo, st, ph)
    return c1.im, c2.im, c3.im


def build(only=None, branches=("twin", "gale", "hyakki")):
    for sheet in WP.SHEETS:
        if only and not any(o in sheet for o in only):
            continue
        m, fr = d5.grid("weapons/v3/" + sheet)
        G = WP.geos(m, fr)
        st_ms = d5.starts(m["frameDurationsMs"])
        size = (m["frameWidth"] + 2 * PAD, m["frameHeight"] + 2 * PAD)
        act = sheet.split("_", 1)[1]
        outs = {b: ([], [], []) for b in branches}
        for ri, d in enumerate(m["directions"]):
            rows = {b: ([], [], []) for b in branches}
            for i in range(m["frames"]):
                st = WP.state_of(m, i)
                ph = phase_of(st_ms[i])
                for b in branches:
                    ims = render(G[d][i], b, st, ph, size)
                    for k in range(3):
                        rows[b][k].append(ims[k])
            for b in branches:
                for k in range(3):
                    outs[b][k].append(rows[b][k])
        for b in branches:
            info = BRANCH[b]
            names = ("dagger_%s_a1_%s" % (b, act), "dagger_%s_a2_%s" % (b, act), "dagger_%s_a2_glow_%s" % (b, act))
            designs = (info["a1_design"], info["a2_design"], info["glow_design"])
            for k in range(3):
                om, _ = d5.grid("weapons/v4/" + names[k])
                allowed = {c[:3] for c in (d5.X0, d5.G[11], d5.G[12], d5.G[13])} if k == 2 else d5.aw_allowed()
                n = d5.check(names[k], outs[b][k], None, allowed, 24, edge_ok=True)
                meta = dict(om)
                meta.update(design=designs[k], designPrevious=om.get("design"), source=d5.SRC, version=V4, r61s5=d5.R61S5, colors=n)
                d5.write_grid("weapons", "v4", names[k], outs[b][k], meta)
            if b == "hyakki":                             # 기존 각성 오버레이 = 백귀 1차와 같은 그림
                an = sheet + "_awaken"
                om, _ = d5.grid("weapons/v3/" + an)
                n = d5.check(an, outs[b][0], None, d5.aw_allowed(), 24, edge_ok=True)
                meta = dict(om)
                meta.update(design="61 단계 5 귀화(백귀 1차와 같은 그림) — " + info["a1_design"], designPrevious=om.get("design"),
                            source=d5.SRC, version=d5.VERSION, r61s5=d5.R61S5, colors=n)
                d5.write_grid("weapons", "v3", an, outs[b][0], meta)
        print("overlay", sheet)


if __name__ == "__main__":
    import sys
    build(sys.argv[1:] or None)
