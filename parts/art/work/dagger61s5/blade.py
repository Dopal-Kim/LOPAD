"""단검 '재 발톱' 날 — 프레임 하나의 축(쥔 곳 → 끝)·가림·피부(색)·덧붙임을 받아 도트로 그린다.

무기 시트·각성 오버레이(_awaken)·v4 갈래 오버레이(a1·a2·a2_glow)·미리보기 정지 그림이 모두 이 한 함수를 쓴다.
축: 기존 JSON 의 gripAnchors(쥔 곳)·bladeTipAnchors(끝) 그대로 — 끝 앵커·손 위치가 바뀌지 않는다.
가림: 고치기 전 그 프레임에서 날이 보이던 구간(축 방향 u 칸)만 그린다 → 몸 뒤로 숨은 구간·주먹이 덮은 손잡이는 그대로 숨는다.
"""
import math

import d5
from d5 import clamp, h2

FACING = {"down": (0.0, 1.0), "up": (0.0, -1.0), "left": (-1.0, 0.0), "right": (1.0, 0.0)}


class Geo:
    """한 프레임의 날 축. g = 쥔 곳, a = 축 단위벡터, n = 날선(오목한 안쪽) 쪽 법선, L = 쥔 곳→끝 길이."""

    def __init__(self, grip, tip, side=1, old=None, facing=(1.0, 0.0), prev_sign=None):
        self.g = grip
        dx, dy = tip[0] - grip[0], tip[1] - grip[1]
        self.L = math.hypot(dx, dy) or 1.0
        self.a = (dx / self.L, dy / self.L)
        n0 = (-self.a[1], self.a[0])
        dot = n0[0] * facing[0] + n0[1] * facing[1]
        if prev_sign is not None and abs(dot) < 0.45:
            sign = prev_sign
        elif abs(dot) >= 0.2:
            sign = 1 if dot > 0 else -1
        else:
            sign = 1 if (n0[0] * 0.6 - n0[1] * 0.8) > 0 else -1
        self.sign = sign
        self.n = (n0[0] * sign, n0[1] * sign)
        self.cov = None
        self.vis = 1.0
        self.count = 0
        self.extra = []
        if old is not None:
            self._coverage(old)

    def loc(self, x, y):
        px, py = x + 0.5 - self.g[0], y + 0.5 - self.g[1]
        return px * self.a[0] + py * self.a[1], px * self.n[0] + py * self.n[1]

    def w(self, u, v):
        return (self.g[0] + u * self.a[0] + v * self.n[0], self.g[1] + u * self.a[1] + v * self.n[1])

    def _coverage(self, old):
        px = old.load()
        cov = set()
        extra = []
        cnt = 0
        for y in range(old.height):
            for x in range(old.width):
                if px[x, y][3]:
                    cnt += 1
                    u, v = self.loc(x, y)
                    if abs(v) <= 8.5 and -13 <= u <= self.L + 3:
                        cov.add(int(round(u)))
                    else:
                        extra.append((x, y))
        self.cov, self.count, self.extra = cov, cnt, extra
        span = [k for k in range(0, int(self.L) + 1)]
        self.vis = sum(1 for k in span if k in cov) / float(len(span)) if span else 0.0

    def seen(self, u):
        if self.cov is None:
            return True
        k = int(round(u))
        return k in self.cov or (k - 1) in self.cov and (k + 1) in self.cov

    def tip_seen(self):
        return self.cov is None or any(k in self.cov for k in range(int(self.L) - 2, int(self.L) + 3))


# ---------------------------------------------------------------- 날 모양 (u 도트, v 도트; +v = 날선 = 오목한 안쪽)
def bow_of(L):
    return clamp(0.14 * L, 1.0, 5.0)


def vc_of(s, L):
    """중심선: 등 쪽(−v)으로 휘었다가 끝이 날선 쪽으로 돌아오는 발톱 곡선."""
    return -bow_of(L) * math.sin(math.pi * s ** 1.3) * (1.0 - 0.15 * s)


def hw_of(s, L, k=1.0):
    if s < 0:
        return 0.0
    base = 2.2 if L >= 14 else 1.6
    if s < 0.38:
        t = s / 0.38
        return k * (base + 1.7 * (3 * t * t - 2 * t * t * t))
    return k * (base + 1.7) * ((1.0 - s) / 0.62) ** 0.7 if s < 1 else 0.0


RING_U, RING_V, RING_R, RING_RI = -8.0, 1.2, 3.1, 1.6


def blade_px(geo, widen=1.0, ring_scale=1.0, handle=True):
    """→ {(x, y): (part, s, d)}  part ∈ out·body·spine·edge·tip·wrap·ring — 피부가 색을 고른다."""
    L = geo.L
    res = {}
    ext = 14 + 8 * widen
    xs = [geo.g[0], geo.g[0] + geo.a[0] * L]
    ys = [geo.g[1], geo.g[1] + geo.a[1] * L]
    x0, x1 = int(min(xs) - ext), int(max(xs) + ext) + 1
    y0, y1 = int(min(ys) - ext), int(max(ys) + ext) + 1
    rr, ri = RING_R * ring_scale, RING_RI * ring_scale
    for y in range(y0, y1):
        for x in range(x0, x1):
            u, v = geo.loc(x, y)
            # 고리
            if handle:
                dr = math.hypot(u - RING_U * ring_scale, v - RING_V)
                if ri <= dr <= rr:
                    up = (v - RING_V) < 0
                    res[(x, y)] = ("ring", 1.0 if up else 0.0, dr - ri)
                    continue
                if -5.6 <= u < 0.2 and abs(v - 0.4) <= 1.55:
                    res[(x, y)] = ("wrap", u, v)
                    continue
                if -1.0 <= u < 0.9 and -2.9 <= v <= 2.2:
                    res[(x, y)] = ("guard", u, v)
                    continue
            if u < 0.2 or u > L + 0.4:
                continue
            s = u / L
            hw = hw_of(s, L, widen)
            d = v - vc_of(s, L)
            if -hw <= d <= hw and hw > 0.3:
                if s > 0.86:
                    part = "tip"
                elif d > hw - 1.05:
                    part = "edge"
                elif d < -hw + 0.95:
                    part = "out"
                elif d < -hw + 1.95:
                    part = "spine"
                elif 0.12 < s < 0.5 and hw > 2.4 and abs(d * max(0.5, hw) + 0.4) <= 0.55:
                    part = "vein"
                else:
                    part = "body"
                res[(x, y)] = (part, s, d / max(0.5, hw))
    return res


# ---------------------------------------------------------------- 피부(색)
class Skin:
    """상태(steel·glow·fade·embers) → 부위 색. cap·allowed 는 시트 검사용."""
    name = "base"

    def col(self, part, s, d, state, x, y, ph):
        raise NotImplementedError


class BaseSkin(Skin):
    """기본: 재빛 강철 + 호박 날선 + 붕대 손잡이 + 무쇠 고리."""
    name = "base"

    def col(self, part, s, d, state, x, y, ph):
        G = d5.G
        if state == "fade":                    # 그림자에 녹는 중 — 먹 + 듬성한 구멍 + 호박 점
            if (x + y) % 2 == 0 and part not in ("edge", "tip"):
                return None
            if part in ("edge", "tip"):
                return d5.A19 if (x + 2 * y) % 3 else d5.A21
            return d5.INK if part in ("out", "ring", "wrap", "guard") else d5.B1
        if part == "ring":
            if d < 0.5 and s > 0.5:
                return d5.A23 if state == "glow" and h2(x, y) < 0.4 else G[8]
            return G[5] if s > 0.5 else G[3]
        if part == "wrap":
            k = int(math.floor((s + 6) / 1.5))
            return d5.B1 if k % 2 == 0 and abs(d - 0.4) < 1.3 else (d5.S2 if d < 0.4 else d5.S1)
        if part == "guard":
            return G[4] if d < 0 else G[3]
        if part == "out":
            return G[1]
        if part == "spine":
            return G[9] if (state == "glow" and 0.25 < s < 0.7) else G[8] if s < 0.7 else G[7]
        if part == "body":
            return G[7] if d < -0.45 else G[6] if d < 0.1 else G[5] if d < 0.55 else G[4]
        hot = state == "glow"
        if part == "vein":
            return d5.A21 if hot else d5.A19
        if part == "edge":
            if hot:
                return d5.A25 if s > 0.55 else d5.A23
            if state == "embers":
                return d5.A23 if s > 0.6 else d5.A21
            return d5.A21 if s > 0.45 else d5.A19
        if part == "tip":
            if hot:
                return d5.A26 if d > -0.5 else d5.A25
            return d5.A23 if d > -0.2 else d5.A21
        return None


# ---------------------------------------------------------------- 그리기
def paint(cv, geo, skin, state, ph=0, ox=0, oy=0, widen=1.0, ring_scale=1.0, mode="full"):
    """mode: full(기본 무기·a1) — 가림 규칙(geo.seen)으로 보이는 칸만. 반환 = 그린 화면 좌표 집합."""
    drawn = set()
    if geo.cov is not None and geo.count == 0:
        return drawn
    st = state
    for (x, y), (part, s, d) in blade_px(geo, widen, ring_scale).items():
        u, v = geo.loc(x, y)
        if part == "ring":
            if geo.cov is not None and not any(k in geo.cov for k in range(-1, 4)):
                continue
        elif not geo.seen(u):
            continue
        c = skin.col(part, s, d, st, x, y, ph)
        if c:
            cv.put(x + ox, y + oy, c)
            drawn.add((x + ox, y + oy))
    if state == "embers" and geo.tip_seen():
        r = d5.Rand(int(geo.g[0] * 7 + geo.g[1] * 13))
        for k in range(4):
            u = geo.L * (0.35 + 0.6 * r.f())
            v = -6 - 5 * r.f()
            x, y = geo.w(u, v)
            cv.put(x + ox, y + oy, d5.A21 if k % 2 else d5.A23)
    return drawn


def mini_talons(cv, old_geo, hand, skin, state, ox=0, oy=0):
    """부채 투척 맺힘 칸: 왼손 손가락 사이 작은 발톱 날 3(옛 송곳니 3자루 자리)."""
    pts = old_geo.extra
    if len(pts) < 6 or not hand:
        return
    hx_, hy_ = hand
    cx = sum(p[0] for p in pts) / float(len(pts))
    cy = sum(p[1] for p in pts) / float(len(pts))
    far = max(pts, key=lambda p: (p[0] - hx_) ** 2 + (p[1] - hy_) ** 2)
    base_ang = math.atan2(far[1] - hy_, far[0] - hx_)
    ext = math.hypot(far[0] - hx_, far[1] - hy_)
    ln = clamp(ext * 0.95, 8, 15)
    for k, da in enumerate((-24, 0, 24)):
        a = base_ang + math.radians(da)
        tip = (hx_ + math.cos(a) * ln * (0.85 if k != 1 else 1.0), hy_ + math.sin(a) * ln * (0.85 if k != 1 else 1.0))
        g = Geo((hx_ + math.cos(a) * 2, hy_ + math.sin(a) * 2), tip, facing=(math.cos(base_ang), math.sin(base_ang)))
        for (x, y), (part, s, d) in blade_px(g, 0.8, handle=False).items():
            c = skin.col(part, s, d, state, x, y, 0)
            if c:
                cv.put(x + ox, y + oy, c)
