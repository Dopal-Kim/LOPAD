"""칼(katana) v3 — 64×96 몸 밀도(2배)의 무기 오버레이 + 칼 3연격 몸 동작 (52라운드 Q8·Q12, 계약 §3.1·§6.1·§7.1·§11).

무기 시트 128×128, 피벗 (64,124) = 몸 피벗 (32,92). 몸 좌표 (x,y) → 무기 좌표 (x+32, y+32) (playerFrameOffset).
칼은 해부 왼허리 칼집에 차고(일기장은 오른허리), 오른손으로 뽑는다. 1타 = 발도(뽑으며 베기).

한 개의 '몸 기준 3D' 로 칼·손을 정의하고 4방향으로 투영한다 — 측면을 거울로 만들지 않고, 깊이도 같은 기준으로 판단한다.
  로컬 축: f = 앞(바라보는 쪽), r = 해부 오른쪽, z = 위(발바닥 0).
  방향별 바닥 벡터: F(앞)·Rv(해부 오른쪽) → 바닥 (gx 동쪽, gy 남쪽=카메라 쪽).
  화면: sx = 32 + gx, sy = 92 - z + gy*KY  (KY = 바닥 깊이 눌림).
  깊이: gy < 0(몸 중심보다 카메라에서 먼 쪽) 인 칼 픽셀은 몸 실루엣과 겹치면 지운다(occlusionBaked) → 시트 depth 는 항상 above.
각도는 계약의 화면각 규약(right 기준 0 = 앞, + = 아래(=해부 오른쪽), down = +90°, up = -90°, left = 180-θ)과 같다:
  로컬 θ 의 바닥 방향 = (cos θ)·F + (sin θ)·Rv.
"""
import math

from PIL import Image

import hero
from hero import pose, G, A, SL, PL, OUT
from v3kit import WD, kit

X = kit.X                                         # 백열 코어 (이펙트 규칙: 판정 프레임 날 끝 1px 만)
KY = 0.35
OFF = 32
WF = 128
WPIV = (64, 124)

FACING = {"down": ((0, 1), (-1, 0)), "up": ((0, -1), (1, 0)), "right": ((1, 0), (0, 1)), "left": ((-1, 0), (0, -1))}

# 칼 치수(도트) — v2 날 27 + 손잡이 7(32×48 → ×2 = 68) 보다 짧게 50: 숙인 몸(키 약 80)에 비해 칼이 지팡이처럼 길어 보여 줄임
BLADE_LEN = 37
HILT_LEN = 12
SAYA_LEN = 38

STEEL = [G[6], G[9], G[12]]                       # 등 · 몸 · 날 선
FADE = [G[4], G[6], G[8]]
GLOW = [A[23], A[25], A[26]]
SAYA = [SL[0], SL[1], SL[3]]                      # 검은 옻칠: 그늘 · 본색 · 빛
TSUBA = [SL[1], G[6], G[8]]
WRAP = [G[3], PL[3]]                              # 손잡이 감은 끈 · 마름모 사이 상어가죽


def ground(d, f, r):
    F, Rv = FACING[d]
    return (f * F[0] + r * Rv[0], f * F[1] + r * Rv[1])


def project(d, v):
    """로컬 (f, r, z) → (화면 dx, 화면 dy, 깊이 gy) — 원점 이동 없음(벡터)."""
    gx, gy = ground(d, v[0], v[1])
    return (gx, -v[2] + gy * KY, gy)


def to_screen(d, p):
    sx, sy, gy = project(d, p)
    return (32 + sx, 92 + sy, gy)


def dir3(theta, elev):
    """로컬 θ(수평, 0 = 앞, + = 해부 오른쪽) · elev(+ = 위) → 단위 벡터."""
    t, e = math.radians(theta), math.radians(elev)
    return (math.cos(t) * math.cos(e), math.sin(t) * math.cos(e), math.sin(e))


def add(a, b, k=1.0):
    return tuple(x + y * k for x, y in zip(a, b))


# =============================================================================
# 래스터: 화면 위 선분을 깊이와 함께 찍는다. 픽셀 = (색, 깊이 gy, 종류)
# =============================================================================
class Layer:
    def __init__(self):
        self.px = {}

    def put(self, x, y, c, gy, kind, prio=0):
        k = (round(x), round(y))
        old = self.px.get(k)
        if old is None or prio >= old[3]:
            self.px[k] = (c, gy, kind, prio)

    def stroke(self, d, p0, v, length, cols_fn, width_fn, kind, prio=0, step=0.5):
        """p0 = 시작점(몸 화면 좌표 + 깊이 3튜플), v = 로컬 단위 벡터. cols_fn(t, lane) → 색, width_fn(t) → 차선 목록."""
        dx, dy, dg = project(d, v)
        L2 = math.hypot(dx, dy) or 1e-6
        nx, ny = -dy / L2, dx / L2                 # 화면 법선
        if ny < 0 or (abs(ny) < 1e-6 and nx < 0):  # 법선은 화면 아래(+y)쪽 = 그늘 쪽으로 통일
            nx, ny = -nx, -ny
        n = max(1, int(length / step))
        for k in range(n + 1):
            t = k / n
            x, y, g = p0[0] + dx * length * t, p0[1] + dy * length * t, p0[2] + dg * length * t
            for lane in width_fn(t):
                c = cols_fn(t, lane)
                if c is not None:
                    self.put(x + nx * lane, y + ny * lane, c, g, kind, prio)

    def dot(self, x, y, c, gy, kind, prio=5):
        self.put(x, y, c, gy, kind, prio)


def draw_katana(L, d, grip, v, state, seed=0):
    """grip = 오른손 위치(몸 화면 3튜플). 손잡이는 grip 에서 뒤로 HILT_LEN, 날 밑(코등이)은 grip 앞 3."""
    tsuba = add(grip, project(d, v), 3.0)
    pomm = add(grip, project(d, v), -(HILT_LEN - 3.0))
    cols = {"glow": GLOW, "fade": FADE}.get(state, STEEL)

    def blade_col(t, lane):
        if t > 0.94:
            return cols[2] if lane == 0 else None   # 칼끝(kissaki) 1px
        if lane == 0:
            return cols[1]
        if lane == -1:
            return cols[2]                          # 날 선(빛 쪽 = 화면 위)
        return cols[0] if t < 0.86 else None        # 등(그늘 쪽)

    L.stroke(d, tsuba, v, BLADE_LEN, blade_col, lambda t: (-1, 0, 1), "blade", prio=1)
    # 손잡이: 감은 끈 마름모(2칸 주기) + 끝 쇠(카시라)
    L.stroke(d, pomm, v, HILT_LEN - 2.0, lambda t, lane: WRAP[1] if (lane == 0 and int(t * 11) % 2 == 0) else WRAP[0],
             lambda t: (-0.5, 0.5), "hilt", prio=2)
    L.dot(pomm[0], pomm[1], G[7], pomm[2], "hilt")
    # 코등이(날에 수직 5px)
    dx, dy, _ = project(d, v)
    l2 = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / l2, dx / l2
    for k, c in ((-2, TSUBA[0]), (-1, TSUBA[2]), (0, TSUBA[1]), (1, TSUBA[1]), (2, TSUBA[0])):
        L.dot(tsuba[0] + nx * k, tsuba[1] + ny * k, c, tsuba[2], "tsuba", prio=3)
    if state == "glow":
        tip = add(tsuba, project(d, v), BLADE_LEN)
        L.dot(tip[0], tip[1], X[0], tip[2], "blade", prio=6)
        mid = add(tsuba, project(d, v), BLADE_LEN - 2)
        L.dot(mid[0], mid[1], X[1], mid[2], "blade", prio=6)
    if state == "embers":
        r = seed * 7 + 3
        for k in range(5):
            r = (r * 1103515245 + 12345) % 2147483648
            t = 0.35 + 0.6 * (r % 1000) / 1000.0
            q = add(tsuba, project(d, v), BLADE_LEN * t)
            off = 2 + (r // 1000) % 3
            L.dot(q[0] + nx * off * (1 if k % 2 else -1), q[1] - 1 - (k % 3), A[23] if k % 2 else A[21], q[2], "ember", prio=4)


def draw_saya(L, d, mouth, v, with_hilt, sway_seed=0):
    """칼집 입구 mouth(화면 3튜플)에서 v(로컬, 칼집 끝 쪽)로. with_hilt = 칼이 들어 있음(손잡이가 반대쪽으로)."""
    def col(t, lane):
        if t > 0.95:
            return G[5] if lane == 0 else (G[3] if lane == 1 else None)   # 칼집 끝 쇠(코지리)
        return {-1: SAYA[2], 0: SAYA[1], 1: SAYA[0]}[lane]
    L.stroke(d, mouth, v, SAYA_LEN, col, lambda t: (-1, 0, 1) if t < 0.9 else (0, 1), "saya", prio=1)
    dx, dy, _ = project(d, v)
    l2 = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / l2, dx / l2
    for k in (-1, 0, 1):
        L.dot(mouth[0] + nx * k, mouth[1] + ny * k, G[6] if k <= 0 else G[4], mouth[2], "saya", prio=2)   # 입구 쇠테
    # 매듭 끈(사게오) 짧게 늘어짐
    q = add(mouth, project(d, v), 6)
    for k in range(3):
        L.dot(q[0] + nx * (2 + k * 0.4), q[1] + ny * (2 + k * 0.4) + k, WD[3] if k < 2 else WD[2], q[2] + 0.5, "cord", prio=3)
    if with_hilt:
        hv = (-v[0], -v[1], -v[2])
        tsuba = add(mouth, project(d, hv), 1.0)
        draw_katana_hilt_only(L, d, tsuba, hv)


def draw_katana_hilt_only(L, d, tsuba, hv):
    dx, dy, _ = project(d, hv)
    l2 = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / l2, dx / l2
    for k, c in ((-2, TSUBA[0]), (-1, TSUBA[2]), (0, TSUBA[1]), (1, TSUBA[1]), (2, TSUBA[0])):
        L.dot(tsuba[0] + nx * k, tsuba[1] + ny * k, c, tsuba[2], "tsuba", prio=3)
    p0 = add(tsuba, project(d, hv), 1.0)
    L.stroke(d, p0, hv, HILT_LEN - 1.0, lambda t, lane: WRAP[1] if (lane == 0 and int(t * 11) % 2 == 0) else WRAP[0],
             lambda t: (-0.5, 0.5), "hilt", prio=2)
    e = add(tsuba, project(d, hv), HILT_LEN)
    L.dot(e[0], e[1], G[7], e[2], "hilt")


def rasterize(L, R, hold_hands=()):
    """Layer → 128×128 RGBA. 몸 뒤(gy<0) 픽셀은 몸 실루엣과 겹치면 지움. 쥔 손 픽셀 위의 손잡이·코등이도 지움(주먹이 감쌈)."""
    im = Image.new("RGBA", (WF, WF), (0, 0, 0, 0))
    po = im.load()
    body = R.image.load()
    hands = []
    for name in hold_hands:
        a = R.anchors.get(name)
        if a:
            hands.append(a)
    for (x, y), (c, gy, kind, prio) in L.px.items():
        bx, by = x, y
        inside = 0 <= bx < 64 and 0 <= by < 96 and body[bx, by][3] > 0
        if inside and gy < 0:
            continue
        if inside and kind in ("hilt", "tsuba") and hands:
            part = R.part_at(bx, by) or ""
            if part.startswith("hand") and any(math.hypot(bx - hx_, by - hy) < 4.5 for hx_, hy in hands):
                continue
        wx, wy = x + OFF, y + OFF
        if 0 <= wx < WF and 0 <= wy < WF:
            po[wx, wy] = c
    return im


# =============================================================================
# 휴대(허리 칼집) — 해부 왼허리. 입구는 몸의 hipL 기준점을 따라가고(출렁임·골반 기울기), 칼집은 뒤·아래·바깥으로.
# =============================================================================
SAYA_DIR = (-0.86, -0.36, -0.30)                  # 칼집 끝 쪽(로컬): 뒤 · 바깥(해부 왼쪽) · 아래


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def saya_vec(sway=0.0):
    """sway(허리천 흔들림 값) 만큼 칼집 끝이 앞뒤로 흔들린다(관성)."""
    a = math.radians(sway * 2.2)
    f, r, z = SAYA_DIR
    return _norm((f * math.cos(a) - r * math.sin(a), f * math.sin(a) + r * math.cos(a), z))


def mouth_point(d, R):
    """칼집 입구 = hipL 기준점(몸 화면) + 앞 3 · (측면은 hipL 이 몸 중심이므로) 깊이만 해부 왼쪽 11."""
    hx_, hy = R.anchors["hipL"]
    if d in ("down", "up"):
        _, sy, gy = project(d, (3.0, -11.0, 0.0))
        return (hx_, hy + 1.0 + (sy - project(d, (0, -11.0, 0))[1]), gy)
    sx, _, _ = project(d, (2.5, 0, 0))
    gy = ground(d, 2.5, -11.0)[1]
    return (hx_ + sx, hy + 1.0, gy)


def carry_frame(d, p, R):
    L = Layer()
    draw_saya(L, d, mouth_point(d, R), saya_vec(p.get("sway", 0.0)), with_hilt=True)
    return rasterize(L, R)


# =============================================================================
# 3연격 — 프레임 정의(로컬). 판정 프레임 칼은 호 중앙에서 30° 비껴 둔다(정면·뒷면에서 칼이 몸에 가려지거나 카메라를 똑바로 향해 짧아지지 않게).
# θ/elev = 칼 방향, hθ/hr/hz = 오른손 위치(몸 중심 기준 수평각·거리·높이).
# lunge 0~1(오른발 내딛기), crouch, tw(몸 회전, + = 해부 오른쪽으로 돌아감), lean(앞 숙임)
# off = 왼손: "saya"(칼집 입구) · "two"(양손) · "guard"(가슴 앞) · "back"(뒤로 균형)
# state: sheathed · steel · glow(판정) · fade(다음 타로 흐림) · embers(불티)
# =============================================================================
COMBO = {
    1: dict(  # 발도 — 왼쪽에서 오른쪽으로 뽑아 벰 (-70 → +70). 90 대기 · 40 판정 · 120 여운 · 100 캔슬 구간 = v2 합 350
        ms=[40, 50, 40, 30, 40, 50, 100], impact=2, active=[2], cancel=6,
        frames=[
            dict(state="sheathed", hth=-62, hr=11, hz=34, lunge=0.0, crouch=4.0, tw=-0.8, lean=0.6, off="saya"),
            dict(state="steel", th=-78, el=-4, hth=-48, hr=14, hz=38, lunge=0.3, crouch=4.5, tw=-0.6, lean=0.9, off="saya"),
            dict(state="glow", th=-30, el=-6, hth=-20, hr=21, hz=41, lunge=1.0, crouch=5.0, tw=-0.1, lean=1.4, off="saya"),
            dict(state="steel", th=40, el=-9, hth=30, hr=20, hz=41, lunge=1.0, crouch=5.0, tw=0.5, lean=1.4, off="back"),
            dict(state="steel", th=80, el=-12, hth=62, hr=18, hz=40, lunge=0.9, crouch=4.5, tw=0.85, lean=1.2, off="back"),
            dict(state="steel", th=98, el=-18, hth=74, hr=16, hz=38, lunge=0.8, crouch=4.0, tw=0.9, lean=1.0, off="back"),
            dict(state="steel", th=28, el=-26, hth=18, hr=13, hz=37, lunge=0.3, crouch=2.5, tw=0.2, lean=0.6, off="guard"),
        ]),
    2: dict(  # 되베기 — 오른쪽에서 왼쪽 (+65 → -65), 빠른 '씽씽'. 40 대기 · 40 판정 · 90 여운 = v2 합 170
        ms=[20, 20, 20, 20, 40, 50], impact=2, active=[2, 3], cancel=4,
        frames=[
            dict(state="steel", th=112, el=6, hth=82, hr=13, hz=44, lunge=0.5, crouch=3.5, tw=0.9, lean=0.8, off="guard"),
            dict(state="steel", th=70, el=2, hth=52, hr=17, hz=43, lunge=0.7, crouch=4.0, tw=0.6, lean=1.0, off="guard"),
            dict(state="glow", th=28, el=-4, hth=22, hr=21, hz=42, lunge=1.0, crouch=4.5, tw=0.0, lean=1.3, off="guard"),
            dict(state="glow", th=-30, el=-8, hth=-22, hr=20, hz=41, lunge=1.0, crouch=4.5, tw=-0.5, lean=1.3, off="back"),
            dict(state="steel", th=-82, el=-12, hth=-58, hr=16, hz=40, lunge=0.9, crouch=4.0, tw=-0.85, lean=1.1, off="back"),
            dict(state="fade", th=-92, el=-16, hth=-64, hr=14, hz=39, lunge=0.8, crouch=3.5, tw=-0.9, lean=0.9, off="back"),
        ]),
    3: dict(  # 마무리 양손 큰 베기 (-85 → +85). 40 대기 · 40 판정 · 240 여운(캔슬 없음) = v2 합 320
        ms=[20, 20, 40, 30, 50, 70, 90], impact=2, active=[2], cancel=None,
        frames=[
            dict(state="steel", th=-128, el=38, hth=-58, hr=9, hz=52, lunge=0.2, crouch=4.0, tw=-1.0, lean=0.4, off="two"),
            dict(state="steel", th=-88, el=14, hth=-52, hr=14, hz=48, lunge=0.6, crouch=5.0, tw=-0.8, lean=0.9, off="two"),
            dict(state="glow", th=-30, el=-6, hth=-22, hr=19, hz=42, lunge=1.0, crouch=6.5, tw=-0.1, lean=1.6, off="two"),
            dict(state="steel", th=48, el=-10, hth=38, hr=18, hz=41, lunge=1.0, crouch=6.5, tw=0.5, lean=1.6, off="two"),
            dict(state="steel", th=96, el=-18, hth=68, hr=15, hz=39, lunge=1.0, crouch=6.0, tw=0.95, lean=1.4, off="two"),
            dict(state="embers", th=112, el=-26, hth=78, hr=14, hz=38, lunge=1.0, crouch=5.5, tw=1.0, lean=1.2, off="two"),
            dict(state="steel", th=30, el=-32, hth=18, hr=11, hz=36, lunge=0.4, crouch=3.0, tw=0.3, lean=0.6, off="two"),
        ]),
}
# v2 대응(판정 시점 고정): hitAt = 판정 프레임 시작 ms, cancelAt = 캔슬 프레임 시작 ms
V2_TIMING = {1: dict(hitAt=90, cancelAt=250, total=350), 2: dict(hitAt=40, cancelAt=80, total=170),
             3: dict(hitAt=40, cancelAt=None, total=320)}
ARC = {1: dict(arcDeg=140, arcFromDeg=-70, arcToDeg=70, nextCombo="katana_combo2"),
       2: dict(arcDeg=130, arcFromDeg=65, arcToDeg=-65, nextCombo="katana_combo3"),
       3: dict(arcDeg=170, arcFromDeg=-85, arcToDeg=85, nextCombo=None)}


def hand_local(fr):
    t = math.radians(fr["hth"])
    return (math.cos(t) * fr["hr"], math.sin(t) * fr["hr"], fr["hz"])


SAYA_MOUTH_LOCAL = (3.0, -11.0, 33.0)
HILT_LOCAL_DIR = tuple(-c for c in SAYA_DIR)


def off_local(fr, hand, v):
    o = fr["off"]
    if o == "two":
        return add(hand, v, -7.0)                   # 왼손 = 손잡이 끝 쪽
    if o == "saya":
        return add(SAYA_MOUTH_LOCAL, (1.5, 0.5, 0.5))
    if o == "guard":
        return (9.0, -6.0, 46.0)
    return (-4.0, -15.0, 37.0)                      # back: 뒤·아래로 뻗어 균형


def combo_pose(d, n, i):
    """연격 n 의 i 프레임 → (pose, 오른손 로컬, 칼 벡터 v, 상태)."""
    fr = COMBO[n]["frames"][i]
    if fr["state"] == "sheathed":
        mouth = SAYA_MOUTH_LOCAL
        hand = add(mouth, _norm(HILT_LOCAL_DIR), 7.0)
        v = _norm(HILT_LOCAL_DIR)
    else:
        hand = hand_local(fr)
        v = dir3(fr["th"], fr["el"])
    off = off_local(fr, hand, v)
    side = d in ("left", "right")
    hR = to_screen(d, hand)
    hL = to_screen(d, off)
    kw = dict(handAt={"R": hR[:2], "L": hL[:2]}, crouch=fr["crouch"], flame=i % 6, pulse=1 if fr["state"] == "glow" else 0,
              lean=-2.0 * fr["lean"] if side else -2.0 * fr["tw"])
    lg = fr["lunge"]
    if side:
        near = "R" if d == "right" else "L"
        # 오른발이 앞으로 내딛음: right 에선 가까운 발, left 에선 먼 발
        fR, fL = (5.0 + 7.0 * lg, 0), (-5.0 - 4.0 * lg, 0)
        kw.update(foot=(fL, fR) if near == "R" else (fR, fL), lean_body=1.0 + 1.6 * fr["lean"],
                  hdx=1.2 * fr["lean"], sway=-1.5 - 2.0 * lg)
        far_side = "L" if near == "R" else "R"
        far_g = hL[2] if far_side == "L" else hR[2]
        kw["farArmFront"] = far_g > 2.0
    else:
        sgn = 1 if d == "down" else -1
        kw.update(step=(-2.0 * lg * sgn, 4.5 * lg * sgn), footdx=(1.0 * lg, -1.0 * lg),
                  twist=-3.2 * fr["tw"] * (1 if d == "down" else 1), shift=-1.0 * fr["tw"],
                  stilt=-1.2 * fr["tw"], squash=0.05 * fr["lean"], head=round(fr["lean"]),
                  sway=2.0 * fr["tw"])
        back = tuple(s for s, h in (("R", hR), ("L", hL)) if h[2] < -3.0)
        kw["armBack"] = back
    return pose(**kw), hand, v, fr["state"]


def combo_frame(d, n, i):
    """→ (몸 Rig, 무기 RGBA, 손 기준점 dict)."""
    p, hand, v, state = combo_pose(d, n, i)
    R = hero.draw_rig(d, p)
    L = Layer()
    # 빈 칼집(또는 칼이 든 칼집)은 항상 허리에
    draw_saya(L, d, mouth_point(d, R), saya_vec(p["sway"] * 0.5), with_hilt=(state == "sheathed"))
    if state != "sheathed":
        gR = R.anchors["handR"]
        grip = (gR[0], gR[1], to_screen(d, hand)[2])
        draw_katana(L, d, grip, v, state, seed=n * 10 + i)
    hold = ("handR", "handL") if COMBO[n]["frames"][i]["off"] == "two" else ("handR",)
    im = rasterize(L, R, hold_hands=hold)
    anchors = {k: [round(R.anchors[k][0], 1), round(R.anchors[k][1], 1)] for k in ("handR", "handL")}
    return R, im, anchors, state, p
