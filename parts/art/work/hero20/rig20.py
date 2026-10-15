"""P20 주인공 새 몸 리그 — 키아트 hero3_b 비율(약 6.8등신 · 작은 숯빛 맨머리 · 마른 근육질)로 다시 설계.

왜 새 리그인가(프로듀서 재점검 6가지): 옛 hero.py 는 머리가 키의 1/3.5(밝은 회색 투구 같은 덩어리)·짧은 다리·말린 등·
번개 지그재그 균열·막대 화살 하나·큰 네모 주머니였다. 이 리그는 같은 pose 키(hero.pose)를 받아 새 해부로 그린다.

한 렌더러로 8방향: 몸을 높이별 단면(타원)으로 보고 방향 ψ 로 돌려 투영(58라운드 rig34 방식의 일반화).
  ψ: down 0 · right +90 · up 180 · left −90 · down-right +45 · down-left −45 · up-right +135 · up-left −135
  화면 x = 32 + a·cosψ + f·sinψ, 깊이(카메라 쪽 +) = f·cosψ − a·sinψ, 화면 y = y + 깊이·KD (발은 KYG)
  a = 해부 왼쪽 +, f = 앞 +, y = 설계 높이(아래 +). 설계 1 = 1.5 도트(96×144, 피벗 (48,138) = 설계 (32,92)).
pose 키 해석(옛 리그와 같은 뜻):
  정면/뒷면 — squash(→ 앞숙임) · tilt(화면 기울기) · shift · twist · stilt · ptilt · step · footdx · stanceW · lift · hand · hdx
  측면 — foot(먼, 가까운) · tilt(앞숙임 도) · lean_body · gdx · hdx · hand(스윙)
  대각 — feet((a,f),(a,f)) · lean_f · twist_deg · yaw · head_turn (+ 정면 키)
  공통 — crouch · bob · breath · head · handAt(화면 설계 좌표, IK) · elbow · armBack · farArmFront · sway · flame · lean · pulse ·
         glow · eyeOff · eyeHot · flameOff · flameRows · arrowOut · tension · reachFrac
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hero_v3"))
import hero  # noqa: E402  (pose · draw_flame · fline · fpoly · wraps — 팔레트와 덧칠 도구는 그대로)
from hero import pose, lerp, fline, fpoly, wraps, draw_flame, path_px  # noqa: E402
from v3kit import Rig3, Part, G, A, SL, WD, PL, OUT, ik2, capsule_on  # noqa: E402

S = 1.5
FW, FH = 96, 144
PIV = (48, 138)
DPIV = (32, 92)
to_px = hero.to_px

# ---- 팔레트 (몸 30색 안) ------------------------------------------------------
ASH = [G[1], G[2], G[3], G[4], G[5], G[6], G[7]]        # 숯빛 몸 = 머리 (본색 2 = G3 · 머리도 같은 본색 — 밝은 투구 덩어리 금지)
IRON = [SL[1], SL[2], SL[4], SL[6]]
CLOTH = [WD[1], WD[2], WD[3], WD[4]]
LEATH = [WD[1], WD[2], WD[3], WD[4]]          # 몸 색 예산 30 — WD5 안 씀
BAND = [G[3], PL[0], PL[1]]
EYE = [A[21], A[23], A[25], A[26]]
LIMB_BANDS = ((0.93, 2), (0.80, 1), (0.30, 0), (0.0, -1), (-9, -2))

# ---- 해부 (서 있을 때, 설계 단위) ---------------------------------------------
HIP_Y = 54.0            # 엉덩관절 (옛 61) — 다리가 키의 약 46%
FOOT_Y = 89.0           # 발목
SOLE_Y = 92.0
THIGH, SHIN = 18.6, 17.2
UPPER, FORE = 13.8, 12.6
HIP_A = 4.6
SH_A, SH_Y = 10.4, 31.0
HEAD_Y, HEAD_F = 19.4, 1.1   # 머리 중심(키 92−13 = 79, 머리 11.6 → 약 6.8등신)
KD, KYG = 0.12, 0.42

# 몸통 단면 (y, 반폭 w, 앞 fe, 뒤 be) — 승모 → 삼각근 → 가슴 → 잘록한 허리 → 골반·볼기. 등은 곧다(굽은 혹 없음)
TORSO = [(27.4, 3.6, 1.2, -2.0), (28.5, 7.6, 2.0, -3.0), (29.8, 10.6, 3.2, -3.7), (31.6, 11.8, 4.6, -4.2),
         (34.0, 11.4, 5.8, -4.5), (36.6, 10.7, 6.2, -4.5), (39.2, 9.8, 5.6, -4.3), (42.0, 8.6, 4.6, -3.9),
         (45.0, 7.5, 3.9, -3.5), (47.6, 7.2, 3.7, -3.5), (50.0, 7.7, 3.8, -3.9), (52.6, 8.3, 3.9, -4.6),
         (55.4, 7.8, 3.2, -4.8)]
# 두개 단면 (머리 중심 기준 dy, 반폭 w, 앞 fe, 뒤 be) — 좁은 턱 · 이마뼈 · 콧등 · 둥근 뒤통수
SKULL = [(-6.0, 1.4, 0.6, -1.4), (-5.5, 2.9, 1.9, -3.1), (-4.5, 3.8, 3.1, -4.2), (-3.0, 4.2, 3.8, -4.7),
         (-1.5, 4.3, 4.1, -4.8), (-0.4, 4.2, 4.5, -4.6), (0.6, 4.0, 4.0, -4.2), (1.6, 3.8, 4.6, -3.6),
         (2.8, 3.4, 4.3, -2.6), (3.8, 2.9, 4.1, -1.7), (4.8, 2.2, 3.8, -0.7), (5.6, 1.3, 3.3, 0.3)]

PSI = {"down": 0.0, "right": 90.0, "up": 180.0, "left": -90.0,
       "down-right": 45.0, "down-left": -45.0, "up-right": 135.0, "up-left": -135.0}
SIDE = ("left", "right")


def _interp(tab, y, col):
    if y <= tab[0][0]:
        return tab[0][col]
    for r0, r1 in zip(tab, tab[1:]):
        if y <= r1[0]:
            t = (y - r0[0]) / (r1[0] - r0[0])
            return r0[col] + (r1[col] - r0[col]) * t
    return tab[-1][col]


def section(y):
    return _interp(TORSO, y, 1), _interp(TORSO, y, 2), _interp(TORSO, y, 3)


def head_section(dy):
    return _interp(SKULL, dy, 1), _interp(SKULL, dy, 2), _interp(SKULL, dy, 3)


def _hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def P(name, ramp, base, **kw):
    return Part(name, ramp, base, **kw)


# =============================================================================
# 자세 → 몸 좌표계
# =============================================================================
class Body:
    def __init__(self, d, p):
        self.d, self.p = d, p
        self.psi = PSI[d] + p.get("yaw", 0.0)
        r = math.radians(self.psi)
        self.c, self.s = math.cos(r), math.sin(r)
        self.view = "side" if d in SIDE else ("front" if self.c > 0 else "back")
        self.diag = d not in ("down", "up", "left", "right")
        self.m = 1 if d == "down" else -1
        self.near = "R" if self.s > 0.2 else ("L" if self.s < -0.2 else None)
        cr = p["crouch"] + p["bob"]
        self.br = p["breath"]
        lean, roll, tw, sh_a, pa, pf = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        sq = p.get("squash", 0.0)
        if self.view == "side":
            lean = p["tilt"] + 6.5 * p["lean_body"]
            pf = p["gdx"]
        elif self.diag:
            lean = 6.5 * p.get("lean_f", 0.6)
            tw = p.get("twist_deg", 0.0)
            roll = 0.0
        else:
            roll = p["tilt"] * self.m
            sh_a = p["shift"]
        if sq and self.view != "side":
            v = max(-0.5, min(0.6, sq))
            lean += math.degrees(math.acos(max(0.0, 1.0 - abs(v)))) * (0.92 if v > 0 else -0.92)
        if not self.diag and self.view != "side":
            tw += p["twist"] * 4.0
            pa = p["shift"] * 0.4
        self.lean, self.roll, self.tw, self.sh_a = math.radians(lean), math.radians(roll), math.radians(tw), sh_a
        self.pel = (pa, pf, HIP_Y + cr)
        self.twist_dx = p.get("twist", 0.0) if self.view != "side" and not self.diag else 0.0

    # ---- 몸통 좌표 -------------------------------------------------------------
    def k_up(self, y):
        return max(0.0, min(1.0, (HIP_Y - y) / 22.0))

    def local(self, a, f, y):
        """서 있는 몸 좌표 (a, f, y) → 세계 (a, f, y) (비틀림·숙임·기울임·호흡·어깨 기울기 적용)."""
        p = self.p
        k = self.k_up(y)
        h = HIP_Y - y
        if y < 40.0:
            h += self.br * 0.5 * (40.0 - y) / 12.0
            h -= p["stilt"] * (a / 12.0) * min(1.0, (40.0 - y) / 8.0)
        elif y > 50.0:
            h += p["ptilt"] * (a / 9.0)
        a = a + self.sh_a * k + self.twist_dx * k
        t = self.tw * k
        if t:
            ca, sa = math.cos(t), math.sin(t)
            a, f = a * ca - f * sa, a * sa + f * ca
        if self.lean and h > 0:
            cl, sl = math.cos(self.lean), math.sin(self.lean)
            f, h = f * cl + h * sl, h * cl - f * sl
        if self.roll and h > 0:
            cr, sr = math.cos(self.roll), math.sin(self.roll)
            a, h = a * cr + h * sr, h * cr - a * sr
        return (self.pel[0] + a, self.pel[1] + f, self.pel[2] - h)

    def proj(self, w, kd=KD):
        a, f, y = w
        x = 32 + a * self.c + f * self.s
        dep = f * self.c - a * self.s
        return (x, y + dep * kd), dep

    def P(self, a, f, y):
        return self.proj(self.local(a, f, y))[0]

    def depth(self, a, f, y):
        return self.proj(self.local(a, f, y))[1]

    def surf(self, a, y, back=False, out=0.3):
        w, fe, be = section(y)
        u = max(-1.0, min(1.0, a / max(w, 1e-3)))
        mid, half = (fe + be) / 2, (fe - be) / 2
        f = mid + (-1 if back else 1) * (half + out) * math.sqrt(max(0.0, 1 - u * u))
        return self.P(a * (1 + out / max(w, 1)), f, y)

    def vis(self, a, y, back=False):
        """표면 법선의 카메라 쪽 성분(+ = 보임)."""
        w, fe, be = section(y)
        u = max(-1.0, min(1.0, a / max(w, 1e-3)))
        half = (fe - be) / 2
        nf = (-1 if back else 1) * math.sqrt(max(0.0, 1 - u * u)) / max(half, 1e-3)
        na = u / max(w, 1e-3)
        t = self.psi * math.pi / 180 + self.tw * self.k_up(y)
        n = math.hypot(na, nf) or 1
        return (nf * math.cos(t) - na * math.sin(t)) / n

    def ring(self, y, n=20, grow=0.0):
        w, fe, be = section(y)
        mid, half = (fe + be) / 2, (fe - be) / 2
        return [self.P((w + grow) * math.cos(2 * math.pi * i / n), mid + (half + grow) * math.sin(2 * math.pi * i / n), y) for i in range(n)]

    # ---- 머리 -------------------------------------------------------------------
    def head_setup(self):
        p = self.p
        hf = HEAD_F
        ha = 0.0
        if self.view == "side":
            hf += 0.35 * p["hdx"]
        elif not self.diag:
            ha = p["hdx"] * self.m
        c = self.local(ha, hf, HEAD_Y + p["head"] * 0.8)
        # 숙인 만큼 머리는 덜 숙임(앞을 노려봄): 몸 숙임의 35% + 고개 숙임(head 키)
        self.hpitch = self.lean * 0.35 + math.radians(2.5 * p["head"])
        if self.view != "side" and not self.diag:
            self.hpitch = self.lean * 0.45 + math.radians(2.0 * p["head"])
        self.hyaw = self.tw + math.radians(p.get("head_turn", 0.0))
        self.hroll = self.roll * 0.6
        self.hc = c

    def hlocal(self, a, f, dy):
        """머리 좌표(a, f, dy; dy 아래 +) → 세계."""
        v = -dy
        cp, sp = math.cos(self.hpitch), math.sin(self.hpitch)
        f, v = f * cp + v * sp, v * cp - f * sp
        if self.hroll:
            cr, sr = math.cos(self.hroll), math.sin(self.hroll)
            a, v = a * cr + v * sr, v * cr - a * sr
        if self.hyaw:
            ca, sa = math.cos(self.hyaw), math.sin(self.hyaw)
            a, f = a * ca - f * sa, a * sa + f * ca
        return (self.hc[0] + a, self.hc[1] + f, self.hc[2] - v)

    def HPt(self, a, f, dy):
        return self.proj(self.hlocal(a, f, dy))

    def hsurf(self, a, dy, back=False, out=0.2):
        w, fe, be = head_section(dy)
        u = max(-1.0, min(1.0, a / max(w, 1e-3)))
        mid, half = (fe + be) / 2, (fe - be) / 2
        f = mid + (-1 if back else 1) * (half + out) * math.sqrt(max(0.0, 1 - u * u))
        q, _ = self.HPt(a, f, dy)
        nf = (-1 if back else 1) * math.sqrt(max(0.0, 1 - u * u)) / max(half, 1e-3)
        na = u / max(w, 1e-3)
        t = math.radians(self.psi) + self.hyaw
        n = math.hypot(na, nf) or 1
        return q, (nf * math.cos(t) - na * math.sin(t)) / n


# =============================================================================
# 그리기
# =============================================================================
def strip_union(R, part, rings):
    """연속 단면 고리 쌍의 볼록 껍질 합집합 → 한 부위 마스크."""
    def fn(dr):
        for r0, r1 in zip(rings, rings[1:]):
            h = _hull(r0 + r1)
            if len(h) >= 3:
                dr.polygon([(round(x), round(y)) for x, y in (R.T(q) for q in h)], fill=255)
    return R.shape(part, fn)


def quads(R, part, top, bot):
    def fn(dr):
        for i in range(len(top) - 1):
            q = [top[i], top[i + 1], bot[i + 1], bot[i]]
            h = _hull(q)
            if len(h) >= 3:
                dr.polygon([(round(x), round(y)) for x, y in (R.T(c) for c in h)], fill=255)
    return R.shape(part, fn)


def vline(R, B, pts, col, part, back=False, minvis=0.05):
    """몸통 표면 선(a, y 목록) — 보이는 구간만."""
    seg = []
    for a, y in pts:
        if B.vis(a, y, back) > minvis:
            seg.append(B.surf(a, y, back, out=0.0))
        else:
            if len(seg) >= 2:
                fline(R, seg, col, part)
            seg = []
    if len(seg) >= 2:
        fline(R, seg, col, part)


def patch(R, B, pts, back=False, lit=G[5], dim=G[4], cx=None):
    """몸통 표면 면 덧칠(근육 덩어리의 빛 받는 면) — 화면 왼쪽(빛 쪽)이면 lit, 아니면 dim."""
    if min(B.vis(a, y, back) for a, y in pts) < 0.15:
        return
    q = [B.surf(a, y, back, out=0.0) for a, y in pts]
    mx = sum(c[0] for c in q) / len(q)
    col = lit if mx < (cx if cx is not None else B.P(0, 0, 38)[0]) else dim
    if col is not None:
        fpoly(R, q, col, "torso")


def tear(R, B, outline, core, back=False, glow=0, pulse=0):
    """찢긴 틈에서 새는 불: 불규칙 다각형(가장자리 어두운 숯 → 21 → 23 → 심 25/26) + 주변 몸 데움. 번개 지그재그 아님."""
    vis = [B.vis(a, y, back) for a, y in outline]
    if max(vis) < -0.25:
        return
    o = [B.surf(a, y, back, out=0.0) for a, y in outline]
    c = [B.surf(a, y, back, out=0.0) for a, y in core]
    po = [R.T(q) for q in o]
    cells = set()
    from PIL import Image, ImageDraw
    x0, y0 = int(min(q[0] for q in po)) - 2, int(min(q[1] for q in po)) - 2
    x1, y1 = int(max(q[0] for q in po)) + 3, int(max(q[1] for q in po)) + 3
    m = Image.new("L", (max(1, x1 - x0), max(1, y1 - y0)), 0)
    ImageDraw.Draw(m).polygon([(round(x - x0), round(y - y0)) for x, y in po], fill=255)
    mp = m.load()
    for yy in range(y1 - y0):
        for xx in range(x1 - x0):
            if mp[xx, yy]:
                cells.add((xx + x0, yy + y0))
    pc = [R.T(q) for q in c]
    mc = Image.new("L", (max(1, x1 - x0), max(1, y1 - y0)), 0)
    if len(pc) >= 3:
        ImageDraw.Draw(mc).polygon([(round(x - x0), round(y - y0)) for x, y in pc], fill=255)
    mcp = mc.load()
    hot = glow >= 2
    for (x, y) in cells:
        edge = any((x + dx, y + dy) not in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        inner = 0 <= x - x0 < mc.width and 0 <= y - y0 < mc.height and mcp[x - x0, y - y0]
        if edge:
            col = A[21] if hot else (A[19] if (x + y) % 3 == 0 else A[21])
        elif inner:
            col = A[26] if (hot or pulse) else A[25]
        else:
            col = A[25] if hot else A[23]
        R.cdot(x, y, col, "torso")
    R.spill_cells.extend(list(cells))


def build(d, p):
    if "feet" not in p:
        p = dict(p)
    for k, v in (("lean_f", 0.6), ("twist_deg", 0.0)):
        p.setdefault(k, v)
    B = Body(d, p)
    if B.view == "side" and not B.diag and any(t[1] < B.P(0, 0, SH_Y)[1] - 4.0 for t in p["handAt"].values()):
        # 머리 위로 칼을 든 자세: 가슴을 카메라 쪽으로 비틀고 살짝 젖힘(키아트 OVERHEAD SLASH 의 비튼 몸통)
        B.tw = math.radians(-18.0 if B.s > 0 else 18.0)
        B.lean -= math.radians(4.0)
    R = Rig3(FW, FH, S=S, src=DPIV, dst=PIV)
    details = []
    view, near = B.view, B.near
    m = B.m

    # ---------------- 다리 ----------------
    def foot_world(side):
        li = 0 if side == "L" else 1
        s = 1 if side == "L" else -1
        lift = p["lift"][li]
        if view == "side" and not B.diag:
            which = 1 if side == near else 0          # foot = (먼, 가까운)
            fx, fl = p["foot"][which]
            a = s * 2.2
            return (a, fx + B.pel[1], lift + fl), fx
        if B.diag:
            fa, ff = p["feet"][li]
            return (fa, ff, lift), ff
        st = p["step"][li]
        fa = s * (7.2 + p["stanceW"]) + m * p["footdx"][li]
        ff = m * st / KYG
        return (fa + B.pel[0] * 0.3, ff, lift), ff

    def leg(side, shade):
        s = 1 if side == "L" else -1
        (fa, ff, lift), _ = foot_world(side)
        hipw = B.local(s * HIP_A, 0.2, HIP_Y + 0.6)
        ank = (fa, ff, FOOT_Y - lift)
        # 3D 2관절 IK — 무릎은 앞(+f)·약간 바깥
        hx, hf, hy = hipw
        dv = (ank[0] - hx, ank[1] - hf, ank[2] - hy)
        dist = math.sqrt(sum(c * c for c in dv)) or 1.0
        L1, L2 = THIGH, SHIN
        dd = min(dist, L1 + L2 - 0.05)
        aa = (L1 * L1 - L2 * L2 + dd * dd) / (2 * dd)
        hh = math.sqrt(max(0.0, L1 * L1 - aa * aa))
        u = tuple(c / dist for c in dv)
        pole = (s * 0.32, 1.0, 0.0)
        dp = sum(pc * uc for pc, uc in zip(pole, u))
        pv = tuple(pc - dp * uc for pc, uc in zip(pole, u))
        pn = math.sqrt(sum(c * c for c in pv)) or 1.0
        pv = tuple(c / pn for c in pv)
        knee = tuple(hipw[i] + u[i] * aa + pv[i] * hh for i in range(3))
        hip2, _ = B.proj(hipw)
        kn2, _ = B.proj(knee)
        an2, adep = B.proj(ank, KYG)
        name = "leg" + side
        mid_th = lerp(hip2, kn2, 0.42)
        calf = lerp(kn2, an2, 0.3)
        R.capsule(P(name, ASH, 2 - shade, group=name, soft=2.0, vgrad=0.82, bands=LIMB_BANDS, warm=False),
                  [hip2, mid_th, kn2, calf, an2], [4.8, 4.2, 2.8, 3.2, 1.9])
        # 발: 뒤꿈치 → 발끝, 바닥에 눕혀 투영(들린 뒷발은 발끝이 아래로)
        yaw_f = 0.0
        if B.diag or view != "side":
            yaw_f = s * 0.18
        pitch = 0.0
        if lift > 0.5:
            pitch = min(0.9, lift * 0.09) if ff < B.pel[1] + 2 else -min(0.35, lift * 0.04)
        pts = []
        for la, lf, lh in ((-1.6, -2.4, 0), (1.6, -2.4, 0), (1.9, 2.2, 0), (1.2, 6.2, 0), (-1.2, 6.2, 0), (-1.9, 2.2, 0),
                           (-1.4, -1.8, 3.0), (1.4, -1.8, 3.0), (1.4, 1.5, 2.6), (-1.4, 1.5, 2.6)):
            ca, sa = math.cos(yaw_f), math.sin(yaw_f)
            la2 = la * ca - lf * sa
            lf2 = la * sa + lf * ca
            hgt = lh - lf * math.sin(pitch)
            w = (fa + la2, ff + lf2, SOLE_Y - lift - hgt)
            pts.append(B.proj(w, KYG)[0])
        R.shape(P("foot" + side, ASH, 2 - shade, group="foot" + side, soft=1.2),
                lambda dr, pts=pts: dr.polygon([(round(x), round(y)) for x, y in (R.T(q) for q in _hull(pts))], fill=255))
        details.append(("footwrap" + side, an2, lerp(pts[2], pts[5], 0.5)))
        if side == "R":
            a0, a1 = lerp(kn2, an2, 0.18), lerp(kn2, an2, 0.72)
            R.capsule(P("greave", IRON, 2 - shade, soft=1.3), [a0, a1], [3.0, 2.4])
            R.ellipse(P("kneecap", IRON, 2 - shade, group="greave", soft=1.0), kn2[0], kn2[1] - 0.3, 2.3, 1.9)
            q0, q1 = lerp(kn2, an2, 0.74), lerp(kn2, an2, 0.97)
            R.capsule(P("shinbandR", BAND, 1, soft=1.0, rim=False), [q0, q1], [2.2, 1.9])
            details.append(("greave", a0, a1, shade))
            details.append(("shinband", q0, q1, "shinbandR"))
        else:
            q0, q1 = lerp(kn2, an2, 0.28), lerp(kn2, an2, 0.96)
            R.capsule(P("shinbandL", BAND, 1, soft=1.0, rim=False), [q0, q1], [2.75, 1.95])
            details.append(("shinband", q0, q1, "shinbandL"))
        R.anchors["knee" + side] = kn2
        R.anchors["ankle" + side] = an2

    # ---------------- 팔 ----------------
    def shoulder(side):
        s = 1 if side == "L" else -1
        return B.P(s * SH_A, 0.0, SH_Y)

    def arm(side, shade):
        s = 1 if side == "L" else -1
        li = 0 if side == "L" else 1
        shj = shoulder(side)
        tgt = p["handAt"].get(side)
        if tgt is None:
            sw = B.local(s * SH_A, 0.0, SH_Y)
            if view == "side":
                which = 1 if side == near else 0
                hx_, hy_ = p["hand"][which]
                hw = (sw[0] + s * 0.8, sw[1] + 2.5 + hx_ * 0.9, sw[2] + 24.0 + hy_ - abs(hx_) * 0.12)
            else:
                hx_, hy_ = p["hand"][li]
                hw = (sw[0] + s * (0.6 + 0.6 * hx_), sw[1] + 2.0 + 0.3 * abs(hy_), sw[2] + 25.0 + hy_)
            hand = B.proj(hw)[0]
        else:
            hand = _reach(shj, tgt, p["reachFrac"])
        over = tgt is not None and tgt[1] < shj[1] - 4.0
        if over:                                   # 머리 위로 든 팔: 어깨가 들리며 손 쪽으로 — 팔꿈치가 굽어 막대 팔이 되지 않게(키아트 OVERHEAD SLASH)
            vx, vy = hand[0] - shj[0], hand[1] - shj[1]
            vl = math.hypot(vx, vy) or 1.0
            shj = (shj[0] + vx / vl * 2.6, shj[1] + vy / vl * 2.6 - 0.8)
            hand = _reach(shj, tgt, 0.93)
        bend = (p["elbow"] or {}).get(side)
        if bend is None and over:
            c1, c2 = ik2(shj, hand, UPPER, FORE, 1), ik2(shj, hand, UPPER, FORE, -1)
            if view == "side":
                el = c1 if (c1[0] - c2[0]) * (1 if B.s > 0 else -1) > 0 else c2       # 팔꿈치는 앞·위로
            else:
                cx = B.P(0, 0, 40)[0]
                el = c1 if abs(c1[0] - cx) >= abs(c2[0] - cx) else c2              # 팔꿈치는 바깥으로
        elif bend is None:
            if view == "side":
                bend = -(1 if B.s > 0 else -1)
                el = ik2(shj, hand, UPPER, FORE, bend)
            elif B.diag:
                c1, c2 = ik2(shj, hand, UPPER, FORE, 1), ik2(shj, hand, UPPER, FORE, -1)
                el = c1 if c1[1] >= c2[1] else c2
            else:
                el = ik2(shj, hand, UPPER, FORE, m * s)
        else:
            el = ik2(shj, hand, UPPER, FORE, bend)
        dx, dy = hand[0] - el[0], hand[1] - el[1]
        dl = math.hypot(dx, dy) or 1.0
        wrist = (hand[0] - dx * 1.6 / dl, hand[1] - dy * 1.6 / dl)
        name = "arm" + side
        R.capsule(P(name, ASH, 2 - shade, group=name, soft=1.8, vgrad=0.85, bands=LIMB_BANDS, warm=False),
                  [shj, lerp(shj, el, 0.4), el, lerp(el, wrist, 0.35), wrist], [3.2, 2.9, 2.2, 2.5, 1.8])
        if side == "L":
            v0, v1 = lerp(el, wrist, 0.22), lerp(el, wrist, 0.68)
            R.capsule(P("vamb", IRON, 2 - shade, soft=1.0), [v0, v1], [2.75, 2.4])
            details.append(("vamb", v0, v1))
            b0, b1 = lerp(el, wrist, 0.70), wrist
        else:
            b0, b1 = lerp(el, wrist, 0.3), wrist
        R.capsule(P("band" + side, BAND, 1, soft=1.0, rim=False), [b0, b1], [2.2, 1.8])
        details.append(("armband", b0, b1, "band" + side))
        R.ellipse(P("hand" + side, ASH, 2 - shade, group="hand" + side, soft=1.0), hand[0], hand[1], 2.1, 2.3)
        details.append(("hand", (hand[0] - dx * 0.4 / dl, hand[1] - dy * 0.4 / dl), (dx / dl, dy / dl), "hand" + side))
        R.anchors["hand" + side] = (hand[0], hand[1])
        R.anchors["shoulder" + side] = shj
        R.anchors["elbow" + side] = el
        if side == "L":
            pauldron(shade)

    # ---------------- 견갑(해부 왼어깨) ----------------
    def pauldron(shade):
        if near == "R" and view == "side" and not B.diag:
            return
        c0 = B.P(SH_A + 0.6, 0.2, SH_Y - 0.6)
        ax = math.cos(math.radians(B.psi) + B.tw)
        o = 1 if ax >= 0 else -1
        sc = 0.62 + 0.38 * abs(ax)
        top = [(-3.4, -2.6), (0.4, -3.8), (3.6, -2.2), (4.6, 1.4), (3.2, 3.6), (-1.2, 3.2), (-3.8, 0.6)]
        pts = [(c0[0] + o * u * sc, c0[1] + v) for u, v in top]
        R.poly(P("pauldron", IRON, 2 - shade, soft=1.6), pts)
        lame = [(-2.6, 2.4), (3.4, 2.6), (4.4, 4.8), (2.6, 6.2), (-2.2, 5.0)]
        R.poly(P("pauldron2", IRON, 1, soft=1.2, group="pauldron"), [(c0[0] + o * u * sc, c0[1] + v) for u, v in lame])
        details.append(("pauldron", c0, o * sc))

    # ---------------- 화살 3대 (해부 오른어깨 뒤 · 등) ----------------
    ARROWS = [((-5.6, 33.2), (-0.42, -0.30, 1.0), 15.5), ((-8.8, 36.4), (-0.75, -0.42, 0.72), 13.0), ((-2.6, 39.6), (-0.15, -0.62, 0.86), 11.5)]

    def arrows():
        for k, ((a0, y0), dv, ln) in enumerate(ARROWS):
            if k == 0 and p["arrowOut"]:
                continue
            w, fe, be = section(y0)
            u = max(-1.0, min(1.0, a0 / w))
            f0 = (fe + be) / 2 - (fe - be) / 2 * math.sqrt(1 - u * u) + 0.4
            n = math.sqrt(sum(c * c for c in dv))
            base = B.P(a0, f0, y0)
            tipl = (a0 + dv[0] / n * ln, f0 + dv[1] / n * ln, y0 - dv[2] / n * ln)
            tip = B.P(*tipl)
            nock = B.P(a0 + dv[0] / n * (ln - 3.6), f0 + dv[1] / n * (ln - 3.6), y0 - dv[2] / n * (ln - 3.6))
            R.capsule(P("arrow%d" % k, CLOTH, 2, flat=True, rim=False, cast=False, group="arrows"), [base, tip], [0.55, 0.5])
            ddx, ddy = tip[0] - nock[0], tip[1] - nock[1]
            dl = math.hypot(ddx, ddy) or 1
            nx_, ny_ = -ddy / dl, ddx / dl
            R.poly(P("fletch%d" % k, ASH, 4, flat=True, rim=False, cast=False, group="arrows"),
                   [nock, (nock[0] + nx_ * 1.4 + ddx * 0.2, nock[1] + ny_ * 1.4 + ddy * 0.2), tip,
                    (nock[0] - nx_ * 1.4 + ddx * 0.2, nock[1] - ny_ * 1.4 + ddy * 0.2)])
            details.append(("fletch", nock, tip))

    # ---------------- 허리천 (앞 폭 · 뒤 폭) ----------------
    sw = p["sway"]

    def knee_push(sign):
        best = 0.0
        for side in ("L", "R"):
            (fa, ff, lift), _ = foot_world(side)
            v = (ff - B.pel[1]) * sign
            best = max(best, v * (0.45 if sign > 0 else 0.22) + lift * 0.2)
        return min(best, 9.0)

    def loin(back_panel):
        """찢긴 허리천: 허리띠 아래 좁은 띠 + 아래로 갈수록 좁아지며 갈라지는 천 자락(앞 3 · 뒤 2) — 자락 사이로 다리·어둠이 보인다(P20 2차)."""
        sign = -1 if back_panel else 1
        w, fe, be = section(50.8)
        mid, half = (fe + be) / 2, (fe - be) / 2
        push = knee_push(sign)

        def ring_pt(t, y, out=0.7):
            r = math.radians(t)
            return (w + out) * math.sin(r), mid + sign * (half + out) * math.cos(r)

        def hang(t, y, shrink=1.0, k_push=1.0):
            a, f = ring_pt(t, y)
            k = math.cos(math.radians(t))
            pw = (B.pel[0] + a * shrink, B.pel[1] + f + sign * push * k * k_push + sw * 0.6 * k_push, B.pel[2] - (HIP_Y - y))
            return B.proj(pw)[0]
        band_top = [B.proj(B.local(*ring_pt(t, 50.6), 50.6))[0] for t in range(-16, 17, 16)]
        band_bot = [hang(t, 52.2, 1.0, 0.15) for t in range(-16, 17, 16)]
        tails = ([(-27.0, 7.5, 59.6, -0.8), (0.0, 13.5, 65.8, 0.4), (28.0, 7.0, 58.8, 0.9)] if not back_panel
                 else [(-17.0, 13.0, 61.0, -0.4), (19.0, 12.0, 59.8, 0.6)])
        polys = []
        for tc, hw, tip_y, tdx in tails:
            top = [hang(tc + hw * u, 52.0, 1.0, 0.2) for u in (-1.0, 0.0, 1.0)]
            ym = 52.0 + (tip_y - 52.0) * 0.5
            midR = hang(tc + hw * 0.45, ym + 0.8, 0.98, 0.7)
            notch = hang(tc + hw * 0.1, ym + 2.6, 0.98, 0.75)
            midL = hang(tc - hw * 0.4, ym - 0.4, 0.98, 0.7)
            tip = hang(tc + tdx * 6.0, tip_y, 0.97, 1.0)
            polys.append([top[0], top[1], top[2], midR, notch, tip, midL])
        name = "loinB" if back_panel else "loin"

        def fn(dr):
            for i in range(len(band_top) - 1):
                h = _hull([band_top[i], band_top[i + 1], band_bot[i + 1], band_bot[i]])
                if len(h) >= 3:
                    dr.polygon([(round(x), round(y)) for x, y in (R.T(c) for c in h)], fill=255)
            for pg in polys:
                dr.polygon([(round(x), round(y)) for x, y in (R.T(c) for c in pg)], fill=255)
        R.shape(P(name, CLOTH, 1 if not back_panel else 0, soft=1.4, group=name), fn)
        details.append(("loin", polys, None, name))

    def belt(back_side):
        pts = []
        for i in range(13):
            a = -8.0 + 16.0 * i / 12
            if B.vis(a, 50.6, back_side) > -0.15:
                pts.append(B.surf(a, 50.6, back_side, out=0.4))
        if len(pts) >= 2:
            pts.sort(key=lambda q: q[0])
            R.capsule(P("belt", CLOTH, 1, soft=0.8), pts, [1.0] * len(pts))

    def pouch(shade):
        # 작은 가죽 주머니(해부 오른허리 옆구리) — 일기장이 든 주머니(사망 끝 바닥 일기장과 이어짐)
        c0 = B.P(-9.0, -0.4, 52.8)
        wv = 0.9 + 0.5 * abs(math.cos(math.radians(B.psi)))
        pts = [(c0[0] - wv, c0[1] - 1.5), (c0[0] + wv, c0[1] - 1.5), (c0[0] + wv + 0.2, c0[1] + 1.3), (c0[0] + wv - 0.4, c0[1] + 2.2),
               (c0[0] - wv + 0.4, c0[1] + 2.2), (c0[0] - wv - 0.2, c0[1] + 1.3)]
        R.poly(P("pouch", LEATH, 2 - shade, soft=1.0), pts)
        details.append(("pouch", c0, wv))

    # ---------------- 몸통 ----------------
    def torso():
        ys = [r[0] for r in TORSO]
        fine = []
        for y0, y1 in zip(ys, ys[1:]):
            fine += [y0, (y0 + y1) / 2]
        fine.append(ys[-1])
        rings = [B.ring(y) for y in fine]
        strip_union(R, P("torso", ASH, 2, group="body", soft=3.6, vgrad=0.84), rings)

    def chest_gear():
        if B.vis(6, 36) > -0.1:
            plate = [(2.2, 33.2), (9.6, 31.8), (10.6, 36.2), (8.6, 40.4), (3.2, 39.6)]
            R.poly(P("plate", IRON, 2, soft=1.6), [B.surf(a, y, out=0.5) for a, y in plate])
            details.append(("plate", plate))
        if B.vis(-4, 33) > -0.2:
            R.capsule(P("strap", CLOTH, 1, soft=0.8, rim=False), [B.surf(-8.6, 30.0, out=0.5), B.surf(-4.0, 33.4, out=0.5), B.surf(2.6, 37.4, out=0.5)], [1.0, 1.0, 1.0])

    def back_gear():
        if B.vis(0, 40, True) > -0.1:
            R.capsule(P("strap", CLOTH, 1, soft=0.8, rim=False),
                      [B.surf(9.0, 30.0, True, 0.5), B.surf(2.0, 38.5, True, 0.5), B.surf(-6.6, 48.0, True, 0.5)], [1.1, 1.1, 1.1])

    def neck_head():
        B.head_setup()
        n0 = B.P(0.0, 0.2, 28.2)
        n1, _ = B.HPt(0.0, -0.8, 3.6)
        R.capsule(P("neck", ASH, 2, group="body", soft=1.4), [n0, n1], [2.6, 2.2])
        rings = []
        for k in range(len(SKULL)):
            dy, w, fe, be = SKULL[k]
            mid, half = (fe + be) / 2, (fe - be) / 2
            rings.append([B.HPt(w * math.cos(2 * math.pi * i / 18), mid + half * math.sin(2 * math.pi * i / 18), dy)[0] for i in range(18)])
        strip_union(R, P("head", ASH, 2, group="head", soft=1.8, vgrad=0.78), rings)
        hc, _ = B.HPt(0, 0, 0)
        R.anchors["head"] = hc

    # ======================= 그리는 순서 =======================
    arm_back = set(p.get("armBack") or ())
    if view == "side" and not B.diag:
        far = "L" if near == "R" else "R"
        if not p["farArmFront"]:
            arm(far, 1)
        leg(far, 1)
        loin(True)
        torso()
        back_gear() if B.vis(0, 40, True) > 0.3 else None
        if B.vis(0, 36) > -0.6:
            chest_gear()
        belt(False)
        belt(True)
        neck_head()
        leg(near, 0)
        loin(False)
        if near == "R":
            pouch(0)
        arrows()
        if p["farArmFront"]:
            arm(far, 1)
        arm(near, 0)
    else:
        facing = view == "front"
        legs = sorted(("L", "R"), key=lambda sd: foot_world(sd)[1] * B.c - (1 if sd == "L" else -1) * 7 * B.s)
        if facing:
            arrows()
            loin(True)
        else:
            loin(False)
            if near == "L" or near is None:
                pouch(1)
        for sd in legs:
            sh = 1 if (near and sd != near) else 0
            leg(sd, sh)
        for sd in ("L", "R"):
            if sd in arm_back:
                arm(sd, 1)
        if B.diag and near:
            far = "L" if near == "R" else "R"
        torso()
        if facing:
            chest_gear()
        else:
            back_gear()
        belt(not facing)
        if facing:
            loin(False)
            if near != "L":
                pouch(0)
        else:
            loin(True)
        neck_head() if not facing else None
        if not facing:
            arrows()
        order = ("L", "R") if (B.s < 0) else ("R", "L")
        if not B.diag:
            order = ("R", "L") if facing else ("L", "R")
        for sd in order:
            if sd not in arm_back:
                arm(sd, 1 if (near and sd != near) else 0)
        if facing:
            neck_head()
    if "head" not in R.anchors:
        neck_head()

    decorate(R, B, p, details)
    R.anchors.update(chest=B.surf(0, 38, view == "back", 0), hipL=B.surf(7.4, 51.0, view == "back", 0.2),
                     hipR=B.surf(-7.4, 51.0, view == "back", 0.2))
    if view == "side":
        R.anchors["hipL"] = R.anchors["hipR"] = B.P(0.3, 0.0, 51.0)
        R.anchors["chest"] = B.surf(0.0, 38, False, 0) if True else None
    w_, fe_, be_ = section(50.6)
    c_ = B.P(0.0, (fe_ + be_) / 2, 50.6)
    ys_ = [B.surf(a_, 50.6, bk_, 0.4)[1] for a_ in (-8.0, -4.0, 0.0, 4.0, 8.0) for bk_ in (False, True)]
    R.anchors["beltTop"] = (c_[0], min(ys_) - 1.1)      # 허리띠 윗줄 가운데(오버레이 오프셋 측정 기준)
    R.scar = scar(B)
    R.body = B
    return R


def _reach(sh, tgt, frac):
    dx, dy = tgt[0] - sh[0], tgt[1] - sh[1]
    d = math.hypot(dx, dy)
    L = (UPPER + FORE + 1.2) * frac
    if d <= L or d == 0:
        return tgt
    return (sh[0] + dx * L / d, sh[1] + dy * L / d)


def scar(B):
    """등 상흔 사각형(계약 §13): up = 등 가운데 · 측면 = 어깨뼈 아래 등 · down = 안 보임."""
    if B.view == "front":
        box, back, vis = (-7.0, 7.0, 33.6, 44.6), True, False
    elif B.view == "back":
        box, back, vis = (-7.0, 7.0, 33.6, 44.6), True, True
    else:
        box, back, vis = None, True, True
    if box is None:
        # 측면: 등 가장자리 안쪽 작은 사각형(어깨뼈 아래)
        s = 1 if B.s > 0 else -1
        a0 = -4.0 * s
        pts = [B.surf(a0 - 2.2, 34.8, True, 0), B.surf(a0 + 2.2, 34.8, True, 0), B.surf(a0 - 2.2, 41.5, True, 0), B.surf(a0 + 2.2, 41.5, True, 0)]
    else:
        x0, x1, y0, y1 = box
        pts = [B.surf(x0, y0, back, 0), B.surf(x1, y0, back, 0), B.surf(x0, y1, back, 0), B.surf(x1, y1, back, 0)]
    tl, tr, bl, br = [to_px(q) for q in pts]
    tc, bc = ((tl[0] + tr[0]) / 2, (tl[1] + tr[1]) / 2), ((bl[0] + br[0]) / 2, (bl[1] + br[1]) / 2)
    w = (math.hypot(tr[0] - tl[0], tr[1] - tl[1]) + math.hypot(br[0] - bl[0], br[1] - bl[1])) / 2
    if B.view == "side":
        w = max(w, 7.0)
    h = math.hypot(tc[0] - bc[0], tc[1] - bc[1])
    rot = math.degrees(math.atan2(tc[0] - bc[0], bc[1] - tc[1]))
    return {"x": round((tc[0] + bc[0]) / 2, 1), "y": round((tc[1] + bc[1]) / 2, 1), "w": round(abs(w), 1), "h": round(h, 1),
            "rot": round(rot, 1), "visible": vis}


# =============================================================================
# 덧칠(세부) — 근육 결 · 찢긴 균열 · 얼굴 · 갑옷 · 붕대
# =============================================================================
def decorate(R, B, p, details):
    view = B.view
    glow, pulse = p["glow"], p["pulse"]
    # ---- 몸통 앞: 쇄골 · 가슴 아래선 · 복근 · 톱니근 · 장골선 ----
    if view != "back":
        for s in (1, -1):
            patch(R, B, [(s * 1.0, 30.4), (s * 8.0, 30.2), (s * 9.4, 33.0), (s * 7.4, 36.4), (s * 1.2, 37.2)], lit=G[4], dim=None)
            patch(R, B, [(s * 1.6, 31.0), (s * 6.6, 30.9), (s * 7.6, 33.0), (s * 1.8, 34.4)], lit=G[5], dim=G[4])
            for y in (39.6, 42.2, 44.8):
                patch(R, B, [(s * 0.7, y), (s * 3.0, y - 0.2), (s * 3.1, y + 1.6), (s * 0.7, y + 1.7)], lit=G[4], dim=None)
            patch(R, B, [(s * 6.4, 39.0), (s * 8.4, 39.6), (s * 7.6, 44.0), (s * 6.0, 43.4)], lit=G[4], dim=None)
        for s in (1, -1):
            vline(R, B, [(s * 1.2, 29.4), (s * 4.5, 29.0), (s * 8.4, 29.6)], G[6] if s < 0 else G[5], "torso")
            vline(R, B, [(s * 0.6, 38.4), (s * 3.5, 38.8), (s * 6.6, 38.2), (s * 9.0, 36.6)], G[1], "torso")
            vline(R, B, [(s * 1.0, 36.0), (s * 4.0, 35.6), (s * 6.8, 34.6)], G[5] if s < 0 else G[4], "torso")
            vline(R, B, [(s * 7.6, 39.6), (s * 8.4, 41.2)], G[1], "torso")
            vline(R, B, [(s * 7.0, 42.0), (s * 7.8, 43.6)], G[1], "torso")
            vline(R, B, [(s * 6.4, 46.6), (s * 4.6, 49.4), (s * 2.4, 51.4)], G[1], "torso")
            for y in (41.6, 44.2, 46.8):
                vline(R, B, [(s * 0.6, y), (s * 3.0, y - 0.3)], G[2], "torso")
                vline(R, B, [(s * 0.8, y - 1.1), (s * 2.8, y - 1.3)], G[5] if s < 0 else G[4], "torso", minvis=0.3)
        vline(R, B, [(0, 30.6), (0, 37.0)], G[2], "torso")
        vline(R, B, [(0, 39.4), (0, 48.6)], G[1], "torso")
        # 찢긴 가슴 균열(해부 오른가슴 ~ 명치) — 불규칙 틈 + 안쪽 밝은 심 + 짧은 갈래
        outline = [(-1.4, 33.8), (0.2, 35.0), (-0.4, 36.4), (0.8, 37.8), (-0.2, 39.4), (0.2, 41.4), (-1.2, 42.8), (-1.8, 41.0),
                   (-3.4, 41.2), (-2.8, 39.6), (-4.6, 38.4), (-3.2, 37.4), (-3.8, 35.6), (-2.4, 35.8)]
        core = [(-1.4, 36.0), (-0.8, 37.8), (-1.2, 40.2), (-2.0, 39.0), (-2.6, 37.8)]
        tear(R, B, outline, core, glow=glow, pulse=pulse)
        for pts in ([(-4.4, 35.2), (-6.4, 34.2), (-7.4, 34.6)], [(-5.4, 38.4), (-7.6, 39.4)], [(-1.0, 43.6), (-1.6, 46.0), (-0.8, 47.4)],
                    [(1.4, 37.8), (3.0, 37.2)]):
            seg = [B.surf(a, y, False, 0) for a, y in pts if B.vis(a, y) > -0.2]
            if len(seg) >= 2:
                fline(R, seg, [A[23] if glow < 2 else A[25], A[21], A[19]], "torso")
        if p["tension"] > 0.3:
            for s in (1, -1):
                vline(R, B, [(s * 3.5, 28.6), (s * 7.0, 29.0), (s * 10.0, 30.4)], G[6] if p["tension"] > 0.65 else G[5], "torso")
    if view != "front":
        bk = True
        tn = p["tension"]
        for s in (1, -1):
            patch(R, B, [(s * 1.4, 30.0), (s * 9.0, 30.4), (s * 8.6, 33.4), (s * 2.0, 32.0)], back=True, lit=G[5], dim=G[4])
            patch(R, B, [(s * 3.0, 33.4), (s * 7.6, 34.2), (s * 8.2, 38.6), (s * 4.0, 38.4)], back=True, lit=G[4], dim=None)
            patch(R, B, [(s * 1.0, 40.0), (s * 6.6, 40.6), (s * 5.2, 46.0), (s * 1.0, 46.4)], back=True, lit=G[4], dim=None)
        vline(R, B, [(0, 29.4), (0.2, 34), (0, 39), (0.2, 44), (0, 48.4)], G[1], "torso", back=bk)
        for s in (1, -1):
            vline(R, B, [(s * (3.4 - 1.2 * tn), 32.4), (s * (7.2 - 1.5 * tn), 33.6), (s * (8.4 - 1.0 * tn), 37.8), (s * (5.6 - 1.0 * tn), 39.6)],
                  G[1], "torso", back=bk)
            vline(R, B, [(s * (3.6 - 1.2 * tn), 31.6), (s * (7.0 - 1.5 * tn), 32.6)], G[6] if tn > 0.5 else G[4], "torso", back=bk, minvis=0.2)
            vline(R, B, [(s * 8.6, 40.6), (s * 7.0, 44.4), (s * 4.4, 47.2)], G[1], "torso", back=bk)
            vline(R, B, [(s * 1.4, 41.0), (s * 1.6, 46.0)], G[4], "torso", back=bk, minvis=0.3)
        outline = [(1.6, 42.0), (3.0, 43.6), (2.0, 45.0), (2.8, 47.0), (0.6, 48.0), (-0.8, 46.4), (-2.6, 47.0), (-1.6, 45.0), (-2.4, 43.4), (-0.4, 43.6)]
        core = [(0.8, 43.8), (1.4, 45.6), (0.0, 46.6), (-1.0, 45.0)]
        tear(R, B, outline, core, back=True, glow=glow, pulse=pulse)
        for pts in ([(3.0, 43.6), (5.0, 42.4)], [(-2.6, 47.0), (-4.4, 48.0)]):
            seg = [B.surf(a, y, True, 0) for a, y in pts if B.vis(a, y, True) > -0.2]
            if len(seg) >= 2:
                fline(R, seg, [A[21], A[19]], "torso")
    # 측면 옆구리 결(보이는 쪽)
    if view == "side":
        s = -1 if B.s > 0 else 1
        vline(R, B, [(s * 8.4, 39.0), (s * 8.2, 42.6)], G[1], "torso", minvis=-0.5)
    # ---- 갑옷·붕대·천 세부 ----
    for det in details:
        kind = det[0]
        if kind == "greave":
            _, a0, a1, shade = det
            fline(R, [lerp(a0, a1, 0.1), lerp(a0, a1, 0.85)], SL[6] if not shade else SL[4], "greave")
            q = R.T(lerp(a0, a1, 0.12))
            R.px(q[0], q[1], SL[6]); R.px(q[0] + 1, q[1] + 1, SL[1])
        elif kind == "shinband":
            _, a0, a1, part = det
            wraps(R, a0, a1, 2.6, 4, part, col=PL[0], slant=0.8)
        elif kind == "armband":
            _, a0, a1, part = det
            wraps(R, a0, a1, 2.3, 3, part, col=PL[0], slant=0.6)
        elif kind == "vamb":
            _, a0, a1 = det
            fline(R, [lerp(a0, a1, 0.1), lerp(a0, a1, 0.9)], SL[6], "vamb")
        elif kind == "hand":
            _, c, (ux, uy), part = det
            nx, ny = -uy, ux
            fline(R, [(c[0] - nx * 2.0, c[1] - ny * 2.0), (c[0] + nx * 2.0, c[1] + ny * 2.0)], PL[1], part)
        elif kind.startswith("footwrap"):
            _, an, mid = det
            fline(R, [(an[0] - 1.6, an[1] + 0.6), (an[0] + 1.6, an[1] + 1.4)], PL[0], "foot" + kind[-1])
            fline(R, [(mid[0] - 1.4, mid[1] - 1.2), (mid[0] + 1.2, mid[1] - 0.4)], PL[0], "foot" + kind[-1])
        elif kind == "loin":
            _, polys, _, name = det
            for pg in polys:
                fline(R, [lerp(pg[1], pg[5], 0.15), lerp(pg[1], pg[5], 0.8)], WD[0] if name == "loinB" else WD[1], name)
                q = R.T(pg[5])
                R.px(q[0], q[1] - 1, OUT)
        elif kind == "pouch":
            _, c0, wv = det
            fline(R, [(c0[0] - wv, c0[1] - 0.5), (c0[0] + wv, c0[1] - 0.5)], WD[1], "pouch")
            q = R.T((c0[0], c0[1] + 0.3))
            R.px(q[0], q[1], SL[6]); R.px(q[0], q[1] + 1, SL[2])
        elif kind == "plate":
            _, plate = det
            for a, y in ((3.6, 34.4), (8.6, 33.2), (7.2, 38.6)):
                if B.vis(a, y) > 0.1:
                    q = R.T(B.surf(a, y, out=0.5))
                    R.px(q[0], q[1], SL[6]); R.px(q[0] + 1, q[1] + 1, SL[1])
            seg = [B.surf(a, y, out=0.5) for a, y in ((2.6, 33.6), (9.2, 32.3)) if B.vis(a, y) > 0]
            if len(seg) == 2:
                fline(R, seg, SL[6], "plate")
        elif kind == "pauldron":
            _, c0, o = det
            fline(R, [(c0[0] - o * 3.0, c0[1] - 2.8), (c0[0] + o * 0.4, c0[1] - 3.6), (c0[0] + o * 3.2, c0[1] - 2.0)], SL[6], "pauldron")
            fline(R, [(c0[0] - o * 2.4, c0[1] + 2.6), (c0[0] + o * 3.6, c0[1] + 2.8)], SL[1], "pauldron")
            q = R.T((c0[0] + o * 1.2, c0[1] - 0.6))
            R.px(q[0], q[1], SL[6]); R.px(q[0] + 1, q[1] + 1, SL[1])
        elif kind == "fletch":
            _, nock, tip = det
            fline(R, [nock, tip], [G[6], G[4]])
    # ---- 머리: 맨머리 숯빛 · 이마뼈 · 가늘게 빛나는 한쪽 눈(해부 왼눈) ----
    head(R, B, p)
    # ---- 어깨 혼불 ----
    fx, fy = B.P(SH_A + 0.8, -1.2 if view == "side" else 0.2, 28.0)
    R.anchors["flame"] = (fx, fy)
    if not p["flameOff"]:
        q = R.T((fx, fy))
        rows = None
        if B.near == "R":
            rows = 3 if B.diag else 0
        if p["flameRows"] is not None:
            rows = min(rows or 6, p["flameRows"])
        if rows != 0:
            R.px(q[0], q[1] + 1, A[19])
            draw_flame(R, round(q[0]), round(q[1]), p["flame"], p["lean"], rows=rows)


def head(R, B, p):
    pts = lambda lst, back=False: [B.hsurf(a, dy, back)[0] for a, dy in lst if B.hsurf(a, dy, back)[1] > -0.05]  # noqa: E731
    # 정수리 빛(작게, 밝은 덩어리 금지 — G5 한 줄)
    top = pts([(-2.6, -4.8), (-1.0, -5.6), (0.8, -5.6)], back=False) + pts([(0.8, -5.6), (2.4, -4.8)], back=True)
    tl = R.T(B.HPt(0, 0, -5.7)[0])
    fline(R, [(tl[0] - 4, tl[1] + 2), (tl[0] - 2.2, tl[1] + 0.6), (tl[0], tl[1] + 0.2)], G[5], "head")
    if B.view == "back" or (B.diag and B.c < 0):
        return _eye(R, B, p, hidden=True)
    # 이마뼈(브로우) 그늘·빛
    brow_l = pts([(0.4, -0.6), (1.6, -1.2), (3.2, -1.0), (4.0, -0.2)])
    brow_r = pts([(-0.4, -0.6), (-1.6, -1.2), (-3.2, -1.0), (-4.0, -0.2)])
    for b in (brow_l, brow_r):
        if len(b) >= 2:
            fline(R, [(q[0], q[1] - 0.8) for q in b], G[4], "head")
    # 눈구멍(어둠)
    for s in (1, -1):
        sock = pts([(s * 0.8, 0.2), (s * 2.0, -0.2), (s * 3.6, 0.2), (s * 3.2, 1.2), (s * 1.6, 1.3)])
        if len(sock) >= 3:
            fpoly(R, sock, OUT, "head")
        elif len(sock) == 2:
            fline(R, sock, OUT, "head")
    # 콧등 · 광대 · 입 · 턱선
    fline(R, pts([(0, 0.4), (0, 2.2)]), G[4], "head")
    fline(R, pts([(-0.6, 2.6), (0.6, 2.6)]), G[1], "head")
    for s, c in ((1, G[1]), (-1, G[4])):
        fline(R, pts([(s * 2.0, 2.4), (s * 3.2, 2.0)]), c, "head")
    fline(R, pts([(-1.4, 3.8), (1.4, 3.8)]), OUT, "head")
    fline(R, pts([(-2.6, 4.6), (-0.6, 5.4)]), G[4], "head")
    _eye(R, B, p)


def _eye(R, B, p, hidden=False):
    R.anchors["eye"] = None
    if p["eyeOff"]:
        return
    q0, v0 = B.hsurf(2.1, 0.5)
    if hidden or v0 < -0.55:
        return
    if v0 < 0.05:
        # 먼 눈: 이마뼈 가장자리로 새는 빛 1~2 도트(오른쪽 보기에서도 눈빛이 읽힘)
        c = R.T(q0)
        R.px(c[0], c[1], EYE[1]); R.px(c[0], c[1] - 1, EYE[0])
        R.spill.append((c[0], c[1], 2.2))
        R.anchors["eye"] = q0
        return
    ln = [B.hsurf(a, dy)[0] for a, dy in ((1.0, 0.8), (2.0, 0.5), (3.0, 0.1), (3.7, -0.4))]
    fline(R, ln, [EYE[0], EYE[2], EYE[3] if (p["pulse"] or p["eyeHot"]) else EYE[2], EYE[1]])
    c = R.T(B.hsurf(2.2, 0.5)[0])
    R.px(c[0], c[1] - 1, EYE[1])
    if p["eyeHot"]:
        e = R.T(B.hsurf(4.1, -0.9)[0])
        R.px(e[0], e[1], EYE[1])
    R.spill.append((c[0], c[1], 3.0))
    # 다른 눈(해부 오른눈)은 어둠 속 꺼진 결
    o = [B.hsurf(a, dy) for a, dy in ((-1.2, 0.7), (-2.6, 0.5))]
    if all(v > 0.1 for _, v in o):
        fline(R, [q for q, _ in o], G[1], "head")
    R.anchors["eye"] = B.hsurf(2.2, 0.5)[0]


def draw_rig(d, p):
    R = build(d, p)
    R.render()
    return R


def draw(d, p):
    return draw_rig(d, p).image
