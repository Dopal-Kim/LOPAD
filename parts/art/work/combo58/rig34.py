"""58라운드 Q4 — 주인공 v3 '진짜 3/4' 대각 리그 (56 Q27 '정면/뒷면 몸 + 3/4 단서' 대체).

대각 4방향(down-right · down-left · up-right · up-left) 몸을 정면/뒷면 그림을 비튼 것이 아니라, 몸을 3D 단면(높이별 타원)으로 보고
몸 방향 ψ 만큼 돌려 다시 투영해 그린다. 부위·색·셰이딩 규칙(Rig3 · Part · 셀아웃 · 가장자리 빛)은 hero.py 그대로.

ψ(몸 방향, 도): 0 = 정면(카메라를 봄), +90 = 화면 오른쪽, 180 = 뒷면. 해부 좌표 a(+ = 해부 왼쪽) · f(+ = 앞) · y(설계 높이, 아래 +).
  화면 x = 32 + a·cosψ + f·sinψ,  깊이(카메라 쪽 +) = f·cosψ − a·sinψ
  down-right ψ = +35 · down-left ψ = −35 · up-right ψ = +145 · up-left ψ = −145.
무기·손 투영(katana3.project)도 대각만 바닥 압축 KY 0.35 → 0.70 으로 바꾼다(tan 35° = 0.70):
  → 화면 45° 조준 = 바닥 각 55°(= 몸 방향 ψ 35°와 같은 각) — 몸과 칼이 같은 방향을 보고, 앞으로 뻗은 칼이 화면에서 0.81 길이로 읽힌다
  (56 판은 바닥 70.7° · 0.47 길이 → 대각이 정면처럼 보이고 칼이 짧았음 — 58 원문 7 '대각선 공격은 아직 허술').
기존 4방향(down · up · left · right)은 건드리지 않는다(픽셀 그대로).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "combo56_body"))

import rig8  # noqa: E402  (8방향 FACING 설치 · DIRS8 · Q · EX · hero · wv3)
from rig8 import K, Q, hero  # noqa: E402
from hero import (A, G, SL, WD, PL, OUT, ASH, FACE, IRON, CLOTH, BAND, DIARY, EYE, LIMB_BANDS, HIP_Y, FOOT_Y, UPPER, FORE,  # noqa: E402
                  SKULL_FRONT, SKULL_SIDE, SKULL_BACK, FACE_FRONT, P, new_rig, lerp, reach, arm_end, crack, groove, fline, fpoly,
                  wraps, rivet, bite, draw_flame, scar_rect, SCAR_BACK, path_px)
from v3kit import ik2  # noqa: E402

DIAG = rig8.DIAG
PSI = {"down-right": 45.0, "down-left": -45.0, "up-right": 135.0, "up-left": -135.0}   # 몸 그림 방향(3/4 = 45°)
KY_DIAG = math.tan(math.radians(35.0))        # 0.700
KY_BASE = K.KY

# =============================================================================
# 무기·손 투영: 대각만 KY 0.70 · 바닥 각 55°(화면 45°)
# =============================================================================
_orig_project = K.project


def ground_deg34(d):
    s = math.radians(rig8.SCREEN_DEG[d])
    return math.degrees(math.atan2(math.sin(s) / KY_DIAG, math.cos(s)))


def project34(d, v):
    if d in PSI:
        gx, gy = K.ground(d, v[0], v[1])
        return (gx, -v[2] + gy * KY_DIAG, gy)
    return _orig_project(d, v)


def install():
    """이 프로세스 안에서만: 대각 FACING(바닥 55°) · 투영 KY 0.70 · rig8.body_pose8/draw_rig8 을 3/4 리그로."""
    for d in DIAG:
        a = math.radians(ground_deg34(d))
        F = (math.cos(a), math.sin(a))
        K.FACING[d] = (F, (-F[1], F[0]))
    K.project = project34
    rig8.body_pose8 = body_pose8
    rig8.draw_rig8 = draw_rig8
    rig8.ground_deg = ground_deg34
    rig8.RIG34 = True


# =============================================================================
# 몸 단면 (설계 단위, 정면/측면 그림의 윤곽에서 읽음)
# =============================================================================
def _interp(tab, y):
    if y <= tab[0][0]:
        return tab[0][1]
    for (y0, v0), (y1, v1) in zip(tab, tab[1:]):
        if y <= y1:
            t = (y - y0) / (y1 - y0)
            return v0 + (v1 - v0) * t
    return tab[-1][1]


T_W = [(31, 5.0), (33.5, 11.5), (38, 15.6), (43, 15.6), (48.5, 12.8), (54, 9.8), (61, 9.0)]       # 반폭(정면 torso)
T_FE = [(31, 5.0), (33, 6.0), (36.5, 9.6), (42, 10.4), (48, 8.6), (54, 6.4), (61, 5.6)]            # 앞 가장자리(측면 torso)
T_BE = [(31, 0.5), (33.5, 1.5), (36.5, -2.2), (41, -4.6), (47, -6.6), (54, -7.8), (61, -7.2)]      # 뒤 가장자리(굽은 등)


def _skull_tables():
    """두개: 높이 dy 별 반폭(정면 윤곽) · 앞/뒤 가장자리(옆얼굴 윤곽)."""
    def extent(poly, dy, side):
        xs = []
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            if (y0 - dy) * (y1 - dy) <= 0 and y0 != y1:
                xs.append(x0 + (x1 - x0) * (dy - y0) / (y1 - y0))
        if not xs:
            return None
        return max(xs) if side > 0 else min(xs)
    rows = []
    for k in range(-20, 21):
        dy = k * 0.5
        w = extent(SKULL_FRONT, dy, 1)
        fe = extent(SKULL_SIDE, dy, 1)
        be = extent(SKULL_SIDE, dy, -1)
        if w is None or fe is None or be is None:
            continue
        rows.append((dy, w, fe - 0.5, be + 0.5))
    return rows


SKULL_ROWS = _skull_tables()


class Body:
    """한 프레임의 3/4 몸 좌표계."""

    def __init__(self, d, p):
        self.d = d
        self.p = p
        self.psi = PSI[d] + p.get("yaw", 0.0)
        self.front = abs(self.psi) < 90
        self.cr = p["crouch"] + p["bob"]
        self.lb = p.get("lean_f", 0.0)                 # 상체 앞 숙임(측면 lean_body 와 같은 뜻)
        self.tw = p.get("twist_deg", 0.0)              # 가슴 비틀림(도, + = 화면 시계 = ψ 증가)
        self.sq = p.get("squash", 0.0)
        self.near = "R" if math.sin(math.radians(self.psi)) > 0 else "L"   # 카메라 쪽 해부 측
        self.far = "L" if self.near == "R" else "R"

    # ---- 높이별 변형 ----
    def k_up(self, y):
        return max(0.0, min(1.0, (HIP_Y - y) / 26.0))

    def psi_at(self, y):
        return math.radians(self.psi + self.tw * self.k_up(y))

    def fshift(self, y):
        return self.lb * self.k_up(y) * 3.0

    def sy(self, y, depth=0.0, kd=0.12):
        """설계 높이 → 화면 y(웅크림·숙임 압축·깊이 기울기)."""
        if self.sq and y < HIP_Y:
            y = HIP_Y - (HIP_Y - y) * (1.0 - self.sq)
        return y + self.cr + depth * kd

    def proj(self, a, f, y, kd=0.12, psi=None, lean=True):
        """lean=True: 몸에 붙은 점(어깨·목·허리 등)은 상체 숙임(fshift)을 따라 앞으로."""
        if lean and y < HIP_Y:
            f = f + self.fshift(y)
        s = self.psi_at(y) if psi is None else psi
        c, sn = math.cos(s), math.sin(s)
        x = 32 + a * c + f * sn
        dep = f * c - a * sn
        return (x, self.sy(y, dep, kd)), dep

    def P(self, a, f, y, kd=0.12):
        return self.proj(a, f, y, kd)[0]

    def Pn(self, a, f, y):
        """단면 값(이미 숙임 포함)으로 만든 점 — 숙임을 다시 더하지 않음."""
        return self.proj(a, f, y, lean=False)[0]

    # ---- 몸통 단면 ----
    def section(self, y):
        w = _interp(T_W, y)
        fe = _interp(T_FE, y) + self.fshift(y)
        be = _interp(T_BE, y) + self.fshift(y)
        return w, (fe + be) / 2, (fe - be) / 2

    def edges(self, y):
        w, mid, half = self.section(y)
        s = self.psi_at(y)
        cx = 32 + mid * math.sin(s)
        e = math.sqrt((w * math.cos(s)) ** 2 + (half * math.sin(s)) ** 2)
        return cx - e, cx + e

    def surf(self, dx, y, back=False, clamp=True):
        """정면(back=False)/등(back=True) 그림의 (dx, y) → 몸 표면 화면 점. 안 보이는 쪽은 실루엣 안으로 붙임."""
        w, mid, half = self.section(y)
        u = max(-1.0, min(1.0, dx / max(w, 1e-3)))
        f = mid + (-1 if back else 1) * half * math.sqrt(max(0.0, 1 - u * u))
        (x, yy), dep = self.proj(dx, f, y, lean=False)
        if clamp:
            lo, hi = self.edges(y)
            x = max(lo + 0.6, min(hi - 0.6, x))
        return (x, yy)

    def vis(self, dx, y, back=False):
        """표면 점이 카메라 쪽인가(법선 · 시선)."""
        w, mid, half = self.section(y)
        u = max(-1.0, min(1.0, dx / max(w, 1e-3)))
        s = self.psi_at(y)
        nf = (-1 if back else 1) * math.sqrt(max(0.0, 1 - u * u)) / max(half, 1e-3)
        na = u / max(w, 1e-3)
        return na * -math.sin(s) + nf * math.cos(s)

    # ---- 머리 ----
    def head_frame(self):
        p = self.p
        ys = 23.4 + p["head"] - p["breath"] * 0.6
        fh = 3.5 + self.lb * 2.6
        s = self.psi_at(20.0) + math.radians(p.get("head_turn", 0.0))
        (hx, hy), _ = self.proj(0.0, fh, ys, psi=s, lean=False)
        return hx + p["hdx"], hy, s


# =============================================================================
# 그리기
# =============================================================================
def draw_q(p, d):
    B = Body(d, p)
    R = new_rig()
    psi = math.radians(B.psi)
    sgnx = 1 if math.sin(psi) > 0 else -1           # 바라보는 화면 x 쪽
    front = B.front
    b = p["bob"]
    details = []

    # ---------------- 팔(손 목표 IK) ----------------
    def shoulder(side):
        a = 14.4 if side == "L" else -14.4
        return B.proj(a, 2.0, 39.0)

    def arm(side):
        shj, sdep = shoulder(side)
        tgt = p["handAt"].get(side)
        s = 1 if side == "L" else -1
        if tgt is None:
            hand = B.P(s * 13.0, 3.0, 58.0)
            hand = (hand[0], hand[1])
        else:
            hand = reach(shj, tgt)
        # 팔꿈치: 바깥·뒤로 — 화면에서 어깨의 바깥쪽
        bend = (p["elbow"] or {}).get(side)
        if bend is None:                     # 팔꿈치는 아래로(두 손 쥠·머리 위 듦 모두 팔꿈치가 손보다 낮게) — 들린 닭날개 방지
            c1, c2 = ik2(shj, hand, UPPER, FORE, 1), ik2(shj, hand, UPPER, FORE, -1)
            el = c1 if c1[1] >= c2[1] else c2
        else:
            el = ik2(shj, hand, UPPER, FORE, bend)
        end = arm_end(el, hand)
        shade = 0 if side == B.near else 1
        R.capsule(P("arm" + side, ASH, 2 - shade, group="arm" + side, soft=1.8, vgrad=0.85, bands=LIMB_BANDS), [shj, el, end], [3.6, 3.0, 2.5])
        if side == "L":
            R.capsule(P("vamb", IRON, 2 - shade, soft=1.0), [lerp(el, hand, 0.25), lerp(el, hand, 0.66)], [3.2, 2.9])
            details.append(("vamb", lerp(el, hand, 0.25), lerp(el, hand, 0.66)))
        R.ellipse(P("hand" + side, BAND, 1, soft=1.0, rim=False), hand[0], hand[1] + 0.4, 2.6, 2.8)
        details.append(("hand" + side, (hand[0], hand[1] - 2.2), (hand[0], hand[1] + 2.8)))
        R.anchors["hand" + side] = (hand[0], hand[1] + 0.4)
        R.anchors["shoulder" + side] = shj

    back_arms = set(p.get("armBack") or ())

    # ---------------- 화살(오른어깨 뒤) — 앞모습이면 몸 뒤에 ----------------
    def arrow(base, tip, fl, shade=2):
        R.capsule(P("arrow", CLOTH, shade, flat=True, rim=False, cast=False), [base, tip], [0.6, 0.6])
        dx_ = tip[0] - base[0]
        R.poly(P("fletch", ASH, 5 if shade == 2 else 4, flat=True, rim=False, cast=False),
               [tip, (tip[0] + fl * 2.5 + dx_ * 0.18, tip[1] - 5.0), (tip[0] - fl * 1.0, tip[1] - 0.4)])

    arrows = []
    if not p["arrowOut"]:
        w36 = B.section(36.0)
        arrows.append((B.Pn(-9.0, w36[1] - w36[2] * 0.7, 37.0), B.Pn(-16.5, w36[1] - w36[2] * 0.9 - 2.0, 23.5), -sgnx))
    if front:
        for base, tip, fl in arrows:
            arrow(base, tip, fl, 1)

    # ---------------- 다리 ----------------
    def leg(side):
        s = 1 if side == "L" else -1
        li = 0 if side == "L" else 1
        fa, ff = p["feet"][li]
        lift = p["lift"][li]
        hip = B.P(s * 5.4, 0.0, HIP_Y)
        (fx, fy0), fdep = B.proj(fa, ff, FOOT_Y, kd=0.0, psi=psi)
        fy = FOOT_Y + fdep * 0.42 - lift
        foot = (fx, fy)
        kn_off = 2.2 + 0.18 * p["crouch"]
        kx = B.proj(s * 1.3, kn_off, 75.0, psi=psi)[0][0] - 32
        knee = ((hip[0] + foot[0]) / 2 + kx, (hip[1] + foot[1]) / 2 - 0.4 * lift + 0.6)
        shade = 0 if side == B.near else 1
        R.capsule(P("leg" + side, ASH, 2 - shade, group="leg" + side, soft=2.0, vgrad=0.82, bands=LIMB_BANDS), [hip, knee, foot], [4.4, 3.3, 2.5])
        # 발: 뒤꿈치 → 발끝(앞) 다각형을 바닥에 눕혀 투영
        pts = []
        for la, lf in ((-2.4, -3.0), (2.4, -3.0), (2.6, 2.0), (1.4, 6.0), (-1.4, 6.0), (-2.6, 2.0)):
            (qx, _), qd = B.proj(fa + la, ff + lf, FOOT_Y, kd=0.0, psi=psi)
            pts.append((qx, FOOT_Y + qd * 0.42 - lift + 1.6))
        top = [(x, y - 3.2) for x, y in pts]
        hull = sorted(pts + top)
        R.poly(P("foot" + side, ASH, 2 - shade, group="foot" + side, soft=1.2), _hull(hull))
        if side == "R":
            a0, a1 = lerp(knee, foot, 0.22), lerp(knee, foot, 0.84)
            R.poly(P("greave", IRON, 2 - shade, soft=1.4), [(a0[0] - 3.0, a0[1] + 1), (a0[0] + 3.0, a0[1]), (a1[0] + 2.4, a1[1] - 4),
                                                         (a1[0] - 0.5, a1[1] - 1.5), (a1[0] - 2.8, a1[1] - 4.5)])
            R.ellipse(P("kneecap", IRON, 2 - shade, group="greave", soft=1.0), knee[0], knee[1] - 0.5, 2.5, 2.0)
            details.append(("greave", a0, a1))
        else:
            q0, q1 = lerp(knee, foot, 0.3), lerp(knee, foot, 0.86)
            R.capsule(P("shinband", BAND, 1, soft=1.0, rim=False), [q0, q1], [3.2, 2.8])
            details.append(("shinband", q0, q1))

    leg(B.far)

    # 몸 뒤로 간 팔(손이 몸 뒤) — 몸통 전에
    for side in (B.far, B.near):
        if side in back_arms:
            arm(side)
    leg(B.near)

    # ---------------- 일기장(오른허리, 상자 두 면) ----------------
    def diary(draw_far):
        sw = p["sway"]
        y0 = 59.0
        faces = []
        # 바깥 면(법선 −a) · 앞 면(+f) · 뒤 면(−f)
        faces.append(([(-14.6, -3.4), (-14.6, 1.0)], (-1.0, 0.0)))
        faces.append(([(-14.6, 1.0), (-10.4, 1.0)], (0.0, 1.0)))
        faces.append(([(-10.4, -3.4), (-14.6, -3.4)], (0.0, -1.0)))
        vx, vf = -math.sin(psi), math.cos(psi)
        is_far = (B.near == "L")
        if is_far != draw_far:
            return
        for (e0, e1), (na, nf) in faces:
            if na * vx + nf * vf <= 0.05:
                continue
            p0 = B.P(e0[0] - 0.6 * sw, e0[1], y0)
            p1 = B.P(e1[0] - 0.6 * sw, e1[1], y0)
            R.poly(P("diary", DIARY, 1 if na == 0 else 0, soft=1.0), [p0, p1, (p1[0], p1[1] + 6.0), (p0[0], p0[1] + 6.2)])
            if na == 0 and abs(p1[0] - p0[0]) > 2.5:
                details.append(("diary", p0, p1))

    diary(True)

    # ---------------- 몸통 ----------------
    ys = [31, 32.2, 33.5, 35.5, 38, 40.5, 43, 45.5, 48.5, 51, 54, 57.5, 61]
    L_, R_ = [], []
    for y in ys:
        lo, hi = B.edges(y)
        yy = B.sy(y)
        L_.append((lo, yy))
        R_.append((hi, yy))
    torso = R_ + L_[::-1]
    R.poly(P("torso", ASH, 2, group="body", soft=4.4, vgrad=0.80), torso)

    if front:
        # 흉갑 조각(해부 왼쪽 가슴) · 끈
        R.poly(P("plate", IRON, 2, soft=1.8), [B.surf(dx, y) for dx, y in [(2, 38), (12.5, 36), (14.5, 42.5), (10.5, 49.5), (3, 47.5)]])
        R.capsule(P("strap", CLOTH, 1, soft=0.8, rim=False), [B.surf(-12.5, 34.5), B.surf(-5, 38.7), B.surf(3, 43)], [1.1, 1.1, 1.1])
    else:
        R.capsule(P("strap", CLOTH, 1, soft=0.8, rim=False), [B.surf(13, 34.5, True), B.surf(2, 45, True), B.surf(-8.5, 55, True)], [1.2, 1.2, 1.2])

    # ---------------- 허리천 · 허리띠 ----------------
    sw = p["sway"]
    hem = [(10, 62), (9 + sw, 68.5), (6.5 + sw * 1.1, 66), (4.5 + sw * 1.2, 72), (1.5 + sw * 1.3, 67.5), (-1.5 + sw * 1.3, 71.5),
           (-4 + sw * 1.2, 66.5), (-6.5 + sw * 1.1, 70.5), (-9 + sw, 66.5), (-10, 62)]
    bk = not front

    def hem_pt(dx, y):
        q = B.surf(dx, 57.0, bk)
        return (q[0], q[1] + (y - 57.0))
    lo57, hi57 = B.edges(57.0)
    top = [(lo57 + 0.3, B.sy(57.0)), (hi57 - 0.3, B.sy(57.0))]
    hem_s = [hem_pt(dx, y) for dx, y in hem]
    hem_s = sorted(hem_s, key=lambda q: q[0], reverse=True)
    # 옆으로 보이는 천(실루엣 가장자리를 따라 처짐)
    side_flap_hi = (hi57 + 0.4, B.sy(57.0) + 9.5 + 0.5 * sw)
    side_flap_lo = (lo57 - 0.4, B.sy(57.0) + 9.0 + 0.5 * sw)
    loin = [top[0], top[1], side_flap_hi] + hem_s + [side_flap_lo]
    R.poly(P("loin", CLOTH, 0, soft=1.8), loin)
    details.append(("loin", hem_s, ((lo57 + hi57) / 2, B.sy(57.5))))
    belt = [B.surf(dx, 57.6, bk) for dx in (-9.8, -5, 0, 5, 9.8)]
    belt = [(lo57 - 0.2, belt[0][1])] + sorted(belt, key=lambda q: q[0]) + [(hi57 + 0.2, belt[-1][1])]
    belt = sorted(belt, key=lambda q: q[0])
    R.capsule(P("belt", CLOTH, 2, soft=0.8), belt, [1.2] * len(belt))
    diary(False)

    # ---------------- 팔(몸 앞) ----------------
    for side in (B.far, B.near):
        if side not in back_arms:
            arm(side)

    # ---------------- 목 · 머리 ----------------
    hx, hy, hs = B.head_frame()
    neck0 = B.P(0.0, 1.5, 34.5)
    R.capsule(P("neck", ASH, 2, group="body", soft=1.5), [neck0, (hx - math.sin(hs) * 1.5, hy + 5.0)], [3.4, 3.0])
    cH, sH = math.cos(hs), math.sin(hs)

    def HP(dx, dy, fsurf=None, back=False):
        """머리 정면 그림 좌표 (dx, dy) → 화면. fsurf 없으면 두개 표면(앞/뒤)."""
        if fsurf is None:
            row = min(SKULL_ROWS, key=lambda r: abs(r[0] - dy))
            _, w, fe, be = row
            u = max(-1.0, min(1.0, dx / max(w, 1e-3)))
            mid, half = (fe + be) / 2, (fe - be) / 2
            fsurf = mid + (-1 if back else 1) * half * math.sqrt(max(0.0, 1 - u * u))
        return (hx + dx * cH + fsurf * sH, hy + dy), fsurf * cH - dx * sH

    # 두개 실루엣: 높이별 단면 투영
    rl, rr = [], []
    for dy, w, fe, be in SKULL_ROWS:
        mid, half = (fe + be) / 2, (fe - be) / 2
        cx = hx + mid * sH
        e = math.sqrt((w * cH) ** 2 + (half * sH) ** 2)
        rl.append((cx - e, hy + dy))
        rr.append((cx + e, hy + dy))
    skull = rr + rl[::-1]
    R.poly(P("head", ASH, 4, group="head", soft=2.6, vgrad=0.80), skull)

    def hclamp(q, dy):
        row = min(range(len(SKULL_ROWS)), key=lambda i: abs(SKULL_ROWS[i][0] - dy))
        return (max(rl[row][0] + 0.8, min(rr[row][0] - 0.8, q[0])), q[1])

    if front:
        face = []
        for dx, dy in FACE_FRONT:
            q, _ = HP(dx, dy)
            face.append(hclamp(q, dy))
        R.poly(P("face", FACE, 3, group="head", soft=1.4, rim=False, cast=False, warm=True, vgrad=0.8), face)
    # 결손(해부 기준 — 보이는 것만)
    for dx, dy, r in ((4.4, -10.2, 1.7), (8.4, -4.4, 1.8), (-8.4, -2.6, 1.2), (-6.8, 7.0, 1.1)):
        (q, dep) = HP(dx * 0.92, dy, back=not front)
        row = min(range(len(SKULL_ROWS)), key=lambda i: abs(SKULL_ROWS[i][0] - dy))
        near_edge = min(abs(q[0] - rl[row][0]), abs(q[0] - rr[row][0])) < 1.6 or dy < -9.5
        if dep > -2.0 and near_edge:                 # 가장자리 결손만(안쪽에 찍히면 구멍처럼 보임)
            bite(R, q[0], q[1], r)
    R.anchors.update(head=(hx, hy), chest=B.surf(0, 45, not front), hipL=B.surf(10.5, 58.5, not front), hipR=B.surf(-10.5, 58.5, not front))
    R.scar = scar_rect(lambda dx, y: B.surf(dx, y, True), SCAR_BACK, not front)

    # ---------------- 견갑(해부 왼어깨) ----------------
    def pauldron():
        (cx, cy), dep = B.proj(13.6, 1.2, 37.0)
        o = 1 if math.cos(psi) * (1 if True else -1) >= 0 else -1          # 바깥(해부 왼쪽)이 화면에서 어느 쪽인가
        ax = math.cos(B.psi_at(37.0))
        o = 1 if ax >= 0 else -1
        shape = [(-6.0, -4.6), (0.5, -4.8), (5.5, -0.9), (5.1, 4.6), (-1.0, 4.2), (-5.5, 0.2)]
        sc = 0.82 + 0.18 * abs(ax)
        pts = [(cx + o * u * sc, cy + v) for u, v in shape]
        R.poly(P("pauldron", IRON, 2 if B.near == "L" else 1, soft=1.8), pts)
        details.append(("pauldron", (cx, cy), o))

    if B.near == "R":
        pauldron()
    # (팔 다음) 머리 덧칠 뒤 근처 견갑
    if not front:
        for base, tip, fl in arrows:
            arrow(base, tip, fl, 2)
        w49 = B.section(49.0)
        arrow(B.surf(9.0, 49.0, True), B.Pn(16.0, w49[1] - w49[2] - 2.0, 37.0), sgnx, 2)

    if B.near == "L":
        pauldron()

    # ======================= 덧칠 =======================
    # 정수리 빛(화면 좌상단 고정)
    fpoly(R, [(hx - 5.6, hy - 6.0), (hx - 4.6, hy - 8.2), (hx - 2.6, hy - 9.5), (hx - 0.8, hy - 9.4), (hx - 2.4, hy - 8.0), (hx - 4.2, hy - 6.4)], G[8], "head")
    # 정수리 균열 혼불(해부 왼쪽)
    crown_pts = [(1.5, -9.6), (2.4, -8.0), (2.6, -6.8), (3.6, -5.8), (4.6, -4.8), (5.0, -3.6), (5.4, -2.4), (5.0, -1.4)]
    crown = [hclamp(HP(dx, dy, fsurf=2.5 if front else -1.5)[0], dy) for dx, dy in crown_pts]
    fline(R, [(q[0] + 0.7, q[1]) for q in crown[:6]], A[18], "head")
    fline(R, crown, [A[21], A[23], A[25], A[26] if p["pulse"] else A[25], A[25], A[23], A[21], A[19]])
    if front:
        HF = lambda dx, dy: hclamp(HP(dx, dy)[0], dy)          # noqa: E731
        HFv = lambda dx, dy: HP(dx, dy)[1] > -0.8              # noqa: E731
        HFs = lambda pts: [HF(dx, dy) for dx, dy in pts if HFv(dx, dy)]   # noqa: E731
        fline(R, HFs([(-5.6, -2.2), (-4, -2.0), (-2.6, -1.0), (-1, -0.2), (1, -0.2), (2.6, -1.0), (4, -2.0), (5.6, -2.2)]), G[5])
        for poly, sideL in (([(1.4, 1.4), (3.6, -0.6), (6.6, -1.0), (6.9, 1.2), (5.6, 2.9), (3.4, 3.7), (1.6, 3.3)], True),
                            ([(-1.4, 1.2), (-3.8, -0.4), (-6.6, -0.2), (-6.9, 2.4), (-5.0, 3.6), (-2.4, 3.7)], False)):
            q = HFs(poly)
            if len(q) >= 3:
                fpoly(R, q, OUT)
        if HFv(-4.6, 2.3):
            fline(R, HFs([(-5.2, 2.2), (-4.0, 2.4)]), G[1])
        fline(R, HFs([(0, 1.2), (0, 3.0)]), G[3], "face")
        fline(R, HFs([(0, 3.6), (0, 4.8)]), G[2], "face")
        fline(R, HFs([(-0.6, 5.6), (1.0, 5.6)]), G[1], "face")
        fline(R, HFs([(-6.4, 4.0), (-4.2, 4.2)]), G[4], "face")
        fline(R, HFs([(4.4, 4.2), (6.2, 4.0)]), G[3], "face")
        fline(R, HFs([(-4.8, 6.2), (-3.6, 7.4)]), G[1], "face")
        fline(R, HFs([(4.8, 6.2), (3.6, 7.4)]), G[1], "face")
        fline(R, HFs([(-2.4, 8.4), (2.4, 8.4)]), G[1], "face")
        fline(R, HFs([(-0.8, 8.4), (0.8, 8.4)]), OUT, "face")
        if not p["eyeOff"] and HFv(4.2, 1.6):
            q = R.T(HF(4.2, 1.6))
            R.spill.append((q[0], q[1], 3.6))
            fline(R, HFs([(2.3, 2.5), (3.6, 1.8), (5.0, 1.0), (6.2, 0.2)]),
                  [EYE[0], EYE[1], EYE[2], EYE[3] if p["pulse"] else EYE[2], EYE[2], EYE[1]])
            fline(R, HFs([(3.0, 2.6), (4.6, 1.9)]), [EYE[0], EYE[1], EYE[2]])
            q = R.T(HF(5.0, 1.0))
            R.px(q[0], q[1] - 1, EYE[1])
        # 가슴 균열 · 갈비 · 쇄골 · 금
        S = lambda dx, y: B.surf(dx, y)                       # noqa: E731
        crack(R, [(-3, 37.5), (-1, 40.5), (-4.5, 43.5), (-1.5, 46.5), (-3.5, 50), (-1, 53)], S, pulse=p["pulse"], thick=(sgnx, 0), glow=p["glow"])
        crack(R, [(-1, 40.5), (2.5, 41.5)], S, thick=(0, 1), spill=False, glow=p["glow"])
        crack(R, [(-3.5, 50), (-6.5, 51.5)], S, thick=(0, 0), spill=False, glow=p["glow"])
        if B.vis(-10, 47) > 0:
            for y in (44.6, 47.6, 50.6):
                fline(R, [S(-12.2, y - 0.8), S(-10, y), S(-7.6, y + 0.5)], G[4], "torso")
                fline(R, [S(-12.0, y + 0.3), S(-9.8, y + 1.1), S(-7.6, y + 1.5)], G[1], "torso")
        for y in (51.0, 54.0):
            fline(R, [S(7.6, y), S(9.8, y + 0.4)], G[2], "torso")
        fline(R, [S(-3.5, 34.0), S(-7, 34.6), S(-10, 34.2)], G[1], "torso")
        fline(R, [S(-4.0, 33.4), S(-8.5, 33.6)], G[5], "torso")
        groove(R, [(-15, 40), (-13, 42.5), (-14, 45.5), (-12.5, 48)], S)
        groove(R, [(6, 51), (7.5, 53.5), (6.5, 56)], S, hi=False)
        for dx, y in ((4.0, 39.2), (11.6, 37.4), (6.0, 46.4)):
            if B.vis(dx, y) > 0:
                rivet(R, *S(dx, y))
        fline(R, [S(3, 38.2), S(12, 36.4)], SL[6], "plate")
        fline(R, [S(7, 41), S(10.5, 45.5)], SL[1], "plate")
        if p["tension"] > 0.3:
            for s_ in (1, -1):
                fline(R, [S(s_ * 4.0, 32.6), S(s_ * 9.0, 33.6), S(s_ * 13.0, 36.0)], G[7] if p["tension"] > 0.65 else G[6], "torso")
    else:
        HF = lambda dx, dy: hclamp(HP(dx, dy, back=True)[0], dy)          # noqa: E731
        groove(R, [(-2, -9.5), (-3.5, -7), (-3, -5)], HF, hi=False)
        Sb = lambda dx, y: B.surf(dx, y, True)                # noqa: E731
        crack(R, [(1.5, 48), (-1, 51), (1.5, 54), (0, 57)], Sb, pulse=p["pulse"], thick=(-sgnx, 0), glow=p["glow"])
        crack(R, [(1.5, 54), (5.5, 52.5)], Sb, thick=(0, 1), spill=False, glow=p["glow"])
        tn = p["tension"]
        for s_ in (1, -1):
            fline(R, [Sb(s_ * (5.5 - 2.2 * tn), 38.5), Sb(s_ * (9.5 - 2.6 * tn), 41.5), Sb(s_ * (11 - 1.8 * tn), 45)], G[1], "torso")
            fline(R, [Sb(s_ * (5.0 - 2.2 * tn), 37.6), Sb(s_ * (9.0 - 2.6 * tn), 40.4)], G[5], "torso")
        fline(R, [Sb(0, 35.5), Sb(0.5, 39), Sb(0, 43), Sb(0.4, 46)], G[2], "torso")
        groove(R, [(-14, 46), (-12, 48.5), (-12.5, 51)], Sb)
        groove(R, [(11.5, 40), (13.5, 43), (12.5, 45)], Sb, hi=False)
    # 옆구리 능선(측면 그림의 갈비 능선을 보이는 옆구리에)
    near_dx = -11.5 if B.near == "R" else 11.5
    Sn = lambda dx, y: B.surf(dx, y, not front)               # noqa: E731
    fline(R, [Sn(near_dx, 42.5), Sn(near_dx * 1.05, 45.0)], G[4], "torso")
    # 견갑 리벳·능선
    for kind, c, o in [x for x in details if x[0] == "pauldron"]:
        rivet(R, c[0] - o * 3.6, c[1] - 2.4)
        rivet(R, c[0] + o * 2.4, c[1] + 0.2)
        fline(R, [(c[0] - o * 5.0, c[1] - 3.6), (c[0], c[1] - 3.6), (c[0] + o * 4.0, c[1] - 0.6)], SL[6] if front else SL[4], "pauldron")
        fline(R, [(c[0] - o * 0.6, c[1] + 1.0), (c[0] + o * 1.9, c[1] + 3.5)], SL[1], "pauldron")
    for kind, a0, a1 in [x for x in details if x[0] != "pauldron"]:
        if kind == "greave":
            rivet(R, a0[0] + 1.6, a0[1] + 1.2)
            rivet(R, a0[0] - 1.8, a0[1] + 1.6)
            fline(R, [lerp(a0, a1, 0.15), lerp(a0, a1, 0.8)], SL[6], "greave")
        elif kind == "shinband":
            wraps(R, a0, a1, 3.0, 4, "shinband")
        elif kind == "vamb":
            wraps(R, a0, a1, 3.0, 2, "vamb", col=WD[2], slant=0.5)
        elif kind.startswith("hand"):
            wraps(R, a0, a1, 2.6, 2, kind, slant=0.6)
        elif kind == "loin":
            hem_s, topc = a0, a1
            for j in (1, 3, 5, 7):
                if j < len(hem_s):
                    fline(R, [(topc[0] + (hem_s[j][0] - topc[0]) * 0.25, topc[1] + 1.2), hem_s[j]], WD[1], "loin")
        elif kind == "diary":
            fline(R, [(a1[0], a1[1] + 0.3), (a1[0], a1[1] + 5.6)], PL[2], "diary")
            q = R.T(((a0[0] + a1[0]) / 2, a0[1] + 2.6))
            R.px(q[0], q[1], G[9]); R.px(q[0] + 1, q[1], G[7]); R.px(q[0], q[1] + 1, G[6])
    # 허리끈 매듭
    kn = R.T(B.surf(-2, 58.5, not front))
    for dx_, dy_, c in ((0, 1, WD[4]), (1, 1, WD[4]), (1, 2, WD[3]), (0, 3, WD[3]), (2, 3, WD[3]), (0, 4, WD[2]), (2, 5, WD[2])):
        R.px(kn[0] + dx_, kn[1] + dy_, c)
    # 어깨 혼불(해부 왼어깨 위)
    fx_, fy_ = B.P(13.0, 1.0, 32.0)
    R.anchors["flame"] = (fx_, fy_)
    if not p["flameOff"]:
        q = R.T((fx_, fy_))
        R.px(q[0], q[1] + 1, A[19]); R.px(q[0] - 1, q[1] + 1, A[19])
        rows = None if B.near == "L" else 5
        if p["flameRows"] is not None:
            rows = min(rows or 6, p["flameRows"])
        draw_flame(R, round(q[0]), round(q[1]), p["flame"], p["lean"], rows=rows)
    return R


def _hull(pts):
    """볼록 껍질(단조 사슬)."""
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


# =============================================================================
# 자세(무기 키 → 3/4 pose)
# =============================================================================
def pose34(**kw):
    p = hero.pose(**kw)
    p.setdefault("lean_f", 0.0)
    p.setdefault("twist_deg", 0.0)
    p.setdefault("feet", ((7.0, -2.5), (-7.0, 2.5)))
    return p


def body_pose8(d, k, i):
    if d not in PSI:
        return Q.body_pose(d, k, i)
    hR = K.to_screen(d, k["R"])
    hL = K.to_screen(d, k["L"])
    lg, tuck = k["lunge"], k["tuck"]
    kw = dict(handAt={"R": hR[:2], "L": hL[:2]}, crouch=k["crouch"], flame=i % 6,
              pulse=1 if k["state"] in ("glow", "full", "materialize") else 0,
              lean=-2.0 * k["tw"] - 1.0 * (1 if PSI[d] > 0 else -1), tension=k["tension"],
              lean_f=0.6 + 1.25 * k["lean"], twist_deg=-16.0 * k["tw"], squash=0.03 * max(0.0, k["lean"]),
              head=round(0.6 * k["lean"]), hdx=0.0,
              feet=((7.0 - 0.5 * lg, -2.5 - 3.5 * lg + 2.0 * tuck), (-7.0 + 0.5 * lg, 2.5 + 5.5 * lg - 3.0 * tuck)),
              sway=-1.0 * (1 if PSI[d] > 0 else -1) + 1.5 * k["tw"] + 2.5 * tuck - 1.5 * lg,
              lift=(max(0, round(tuck * 7.0) - 1), round(tuck * 7.0)))
    kw["armBack"] = tuple(s for s, h in (("R", hR), ("L", hL)) if h[2] < -4.0)
    kw.update(k.get("extra") or {})
    return pose34(**kw)


def draw_rig8(d, p):
    if d not in PSI:
        return hero.draw_rig(d, p)
    if "feet" not in p:                      # 다른 모듈이 hero.pose 로 만든 자세 — 3/4 기본값
        p = dict(p, lean_f=p.get("lean_f", 0.6), twist_deg=p.get("twist_deg", 0.0), feet=((7.0, -2.5), (-7.0, 2.5)))
    R = draw_q(p, d)
    R.render()
    return R
