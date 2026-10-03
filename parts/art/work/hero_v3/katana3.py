"""칼(katana) v3 — 96×144 몸(53라운드 Q1 1.5배)의 무기 오버레이 + 칼 연격·뽑기·넣기·특수 몸 동작 (계약 §3.1·§6.1·§6.2·§7.1·§11·§13).

무기 시트 192×192, 피벗 (96,186) = 몸 피벗 (48,138). 몸 도트 (x,y) → 무기 도트 (x+48, y+48) (playerFrameOffset).
칼은 해부 왼허리 칼집에 차고(일기장은 오른허리), 오른손으로 뽑는다. 1타 = 발도(뽑으며 베기).
대기·걷기·달리기에서는 왼손이 칼집 입구(코이구치)를 쥐고 엄지로 코등이를 누른다(53라운드 '무기 든 느낌').

한 개의 '몸 기준 3D' 로 칼·손을 정의하고 4방향으로 투영한다 — 측면을 거울로 만들지 않고, 깊이도 같은 기준으로 판단한다.
  로컬 축: f = 앞(바라보는 쪽), r = 해부 오른쪽, z = 위(발바닥 0). 단위 = 설계 좌표(64×96 판 도트, ×1.5 = 지금 도트).
  화면(설계): sx = 32 + gx, sy = 92 - z + gy*KY → 도트 = hero.to_px.
  깊이: gy < 0(몸 중심보다 카메라에서 먼 쪽) 인 칼 픽셀은 몸 실루엣과 겹치면 지운다(occlusionBaked) → 시트 depth 는 항상 above.
각도는 계약의 화면각 규약(right 기준 0 = 앞, + = 아래(=해부 오른쪽), down = +90°, up = -90°, left = 180-θ)과 같다.
"""
import math

from PIL import Image

import hero
from hero import pose, G, A, SL, PL, OUT, S, to_px
from v3kit import WD, kit, raster_path

X = kit.X                                         # 백열 코어 (이펙트 규칙: 판정 프레임 날 끝 1px 만)
KY = 0.35
OFF = 48
WF = 192
WPIV = (96, 186)

FACING = {"down": ((0, 1), (-1, 0)), "up": ((0, -1), (1, 0)), "right": ((1, 0), (0, 1)), "left": ((-1, 0), (0, -1))}

# 칼 치수(설계 단위 — ×1.5 도트). 날 37(55 도트) + 손잡이 12(18 도트), 칼집 38(57 도트)
BLADE_LEN = 37
HILT_LEN = 12
SAYA_LEN = 38

STEEL = [G[6], G[9], G[12], G[10]]                # 등 · 몸 · 날 선 · 칼날 몸 반사(보오히 쪽)
FADE = [G[4], G[6], G[8], G[7]]
GLOW = [A[23], A[25], A[26], A[25]]
SAYA = [SL[0], SL[1], SL[2], SL[4], SL[6]]        # 검은 옻칠: 그늘 · 본색 · 중간 · 빛 · 옻칠 반사(53라운드: 폭 3→5, 반사 띠로 대비 강화)
TSUBA = [SL[1], G[6], G[8], G[10]]
WRAP = [G[4], PL[3]]                              # 손잡이 감은 끈 · 마름모 사이 상어가죽
CORD = [PL[1], PL[2], PL[3]]                      # 칼집 끈(사게오) — 어두운 칼집 위 밝은 감김(대비)


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
# 래스터: 설계 좌표 선분을 도트 좌표로 옮겨 깊이와 함께 찍는다. 픽셀 = (색, 깊이 gy, 종류)
# =============================================================================
class Layer:
    def __init__(self):
        self.px = {}

    def put(self, x, y, c, gy, kind, prio=0):
        """도트 좌표."""
        k = (round(x), round(y))
        old = self.px.get(k)
        if old is None or prio >= old[3]:
            self.px[k] = (c, gy, kind, prio)

    def dot(self, x, y, c, gy, kind, prio=5):
        """설계 좌표."""
        q = to_px((x, y))
        self.put(q[0], q[1], c, gy, kind, prio)

    def stroke(self, d, p0, v, length, cols_fn, width_fn, kind, prio=0, step=0.5):
        """p0 = 시작점(설계 화면 좌표 + 깊이), v = 로컬 단위 벡터, length = 설계 길이.
        cols_fn(t, lane, k) → 색(k = 도트 단위 진행 칸), width_fn(t) → 도트 차선 목록(법선 + = 화면 아래 = 그늘 쪽)."""
        dx, dy, dg = project(d, v)
        dx, dy = dx * S, dy * S
        L2 = math.hypot(dx, dy) or 1e-6
        nx, ny = -dy / L2, dx / L2                 # 화면 법선
        if ny < 0 or (abs(ny) < 1e-6 and nx < 0):  # 법선은 화면 아래(+y)쪽 = 그늘 쪽으로 통일
            nx, ny = -nx, -ny
        P0 = to_px(p0[:2])
        n = max(1, int(length * max(L2, 0.35) / step))
        for k in range(n + 1):
            t = k / n
            x, y, g = P0[0] + dx * length * t, P0[1] + dy * length * t, p0[2] + dg * length * t
            kk = int(length * L2 * t)
            for lane in width_fn(t):
                c = cols_fn(t, lane, kk)
                if c is not None:
                    self.put(x + nx * lane, y + ny * lane, c, g, kind, prio)
        return (nx, ny)


def _normal(d, v):
    dx, dy, _ = project(d, v)
    l2 = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / l2, dx / l2
    if ny < 0 or (abs(ny) < 1e-6 and nx < 0):
        nx, ny = -nx, -ny
    return nx, ny, dx / l2, dy / l2


def draw_tsuba(L, d, tsuba, v, glint=False):
    """코등이: 날에 수직 7 도트 × 두께 2 (+ 날 쪽 하바키 1)."""
    nx, ny, ax, ay = _normal(d, v)
    P = to_px(tsuba[:2])
    g = tsuba[2]
    cols = {-3: TSUBA[0], -2: TSUBA[2], -1: TSUBA[3], 0: TSUBA[2], 1: TSUBA[1], 2: TSUBA[1], 3: TSUBA[0]}
    for k, c in cols.items():
        for a_ in (0, -1):
            L.put(P[0] + nx * k + ax * a_, P[1] + ny * k + ay * a_, c if a_ == 0 else (TSUBA[1] if k < 0 else TSUBA[0]), g, "tsuba", prio=3)
    for k in (-1, 0):
        L.put(P[0] + nx * k + ax * 1.2, P[1] + ny * k + ay * 1.2, G[10] if k < 0 else G[8], g, "tsuba", prio=3)   # 하바키
    if glint:
        for ox, oy, c in ((0, 0, X[1]), (1, -1, G[13]), (-1, -1, G[12]), (0, -2, G[12]), (2, -2, G[11])):
            L.put(P[0] + nx * -2 + ox, P[1] + ny * -2 + oy - 1, c, g + 0.1, "glint", prio=7)


def draw_hilt(L, d, tsuba, hv, length=HILT_LEN):
    """손잡이: tsuba 에서 hv(로컬, 손잡이 끝 쪽)로. 감은 끈 마름모(3칸 주기) + 끝 쇠(카시라)."""
    def col(t, lane, k):
        if t > 0.9:
            return G[8] if lane <= 0 else G[6]
        if lane == 0:
            return WRAP[1] if k % 3 == 1 else WRAP[0]
        if lane < 0:
            return G[5] if k % 3 == 0 else WRAP[0]
        return G[2] if k % 3 == 2 else G[3]
    p0 = add(tsuba, project(d, hv), 1.0)
    L.stroke(d, p0, hv, length - 1.0, col, lambda t: (-1, 0, 1), "hilt", prio=2)


def draw_katana(L, d, grip, v, state, seed=0, visible=None):
    """grip = 오른손 위치(설계 화면 3튜플). 손잡이는 grip 에서 뒤로, 코등이는 grip 앞 3.
    visible = 칼집 밖으로 나온 날 길이(설계, None = 전부) — 뽑기·넣기."""
    tsuba = add(grip, project(d, v), 3.0)
    cols = {"glow": GLOW, "fade": FADE}.get(state, STEEL)
    blen = BLADE_LEN if visible is None else max(0.0, min(BLADE_LEN, visible))
    full = visible is None or visible >= BLADE_LEN

    def blade_col(t, lane, k):
        tt = t * blen / BLADE_LEN
        if full and tt > 0.95:
            return cols[2] if lane == 0 else None   # 칼끝(kissaki)
        if full and tt > 0.88 and lane == 1:
            return None
        if lane == -1:
            return cols[2]                          # 날 선(빛 쪽 = 화면 위)
        if lane == 0:
            return cols[3] if 0.12 < tt < 0.7 and k % 5 != 4 else cols[1]
        return cols[0]                              # 등(그늘 쪽)

    if blen > 0:
        L.stroke(d, tsuba, v, blen, blade_col, lambda t: (-1, 0, 1), "blade", prio=1)
    draw_hilt(L, d, tsuba, (-v[0], -v[1], -v[2]))
    draw_tsuba(L, d, tsuba, v, glint=(state == "click"))
    if state == "glow":
        tip = to_px(add(tsuba, project(d, v), BLADE_LEN)[:2])
        g = tsuba[2]
        L.put(tip[0], tip[1], X[0], g, "blade", prio=6)
        mid = to_px(add(tsuba, project(d, v), BLADE_LEN - 1.5)[:2])
        L.put(mid[0], mid[1], X[1], g, "blade", prio=6)
    if state == "embers" and blen > 0:
        nx, ny, _, _ = _normal(d, v)
        r = seed * 7 + 3
        for k in range(8):
            r = (r * 1103515245 + 12345) % 2147483648
            t = 0.35 + 0.6 * (r % 1000) / 1000.0
            q = add(tsuba, project(d, v), BLADE_LEN * t)
            P = to_px(q[:2])
            off = 3 + (r // 1000) % 4
            L.put(P[0] + nx * off * (1 if k % 2 else -1), P[1] - 1 - (k % 4), A[23] if k % 2 else A[21], q[2], "ember", prio=4)


def draw_saya(L, d, mouth, v, with_hilt, slide=0.0):
    """칼집 입구 mouth(설계 화면 3튜플)에서 v(로컬, 칼집 끝 쪽)로. slide = 왼손이 칼집을 뒤로 당긴 거리(설계, 뽑기·넣기).
    with_hilt = 칼이 들어 있음(손잡이가 반대쪽으로). → 입구(설계 화면 3튜플)"""
    mouth = add(mouth, project(d, v), slide)

    def col(t, lane, k):
        if t > 0.94:                                # 칼집 끝 쇠(코지리)
            return {-1: G[8], 0: G[7], 1: G[5], 2: G[3]}.get(lane)
        if t < 0.035:                               # 입구 쇠테(코이구치)
            return {-2: G[10], -1: G[8], 0: G[7], 1: G[6], 2: G[4]}.get(lane)
        if lane == -2:
            return SAYA[4] if (k % 9 < 5 and 0.08 < t < 0.85) else SAYA[3]   # 옻칠 반사 띠(끊김)
        return {-1: SAYA[3], 0: SAYA[2], 1: SAYA[1], 2: SAYA[0]}[lane]
    L.stroke(d, mouth, v, SAYA_LEN, col, lambda t: (-2, -1, 0, 1, 2) if t < 0.72 else (-1, 0, 1, 2), "saya", prio=1)
    nx, ny, ax, ay = _normal(d, v)
    # 쿠리카타(끈 고리 혹) + 사게오(밝은 끈): 칼집을 두 번 감고 아래로 늘어진 고리
    q = to_px(add(mouth, project(d, v), 6.0)[:2])
    g = mouth[2] + 0.2
    L.put(q[0] + nx * 3, q[1] + ny * 3, SL[4], g, "saya", prio=2)
    L.put(q[0] + nx * 3 + ax, q[1] + ny * 3 + ay, SL[2], g, "saya", prio=2)
    for w_ in (3.6, 6.4):
        c0 = to_px(add(mouth, project(d, v), w_)[:2])
        for k in range(-2, 3):
            L.put(c0[0] + nx * k + ax * (k * 0.35), c0[1] + ny * k + ay * (k * 0.35), CORD[2] if k < 0 else CORD[1], g, "cord", prio=3)
    loop = [(3.6, 0.0), (4.6, 1.6), (5.8, 3.4), (6.2, 5.0), (5.4, 6.4), (4.0, 6.8), (2.8, 5.8), (2.4, 4.2), (2.8, 2.6)]
    pts = []
    for a_, b_ in loop:
        c0 = to_px(add(mouth, project(d, v), a_ + 3.0)[:2])
        pts.append((c0[0] + nx * (b_ + 2.5), c0[1] + ny * (b_ + 2.5) + b_ * 0.4))
    for i, (x, y) in enumerate(raster_path(pts)):
        L.put(x, y, CORD[1] if i % 4 else CORD[0], g, "cord", prio=3)
    if with_hilt:
        hv = (-v[0], -v[1], -v[2])
        tsuba = add(mouth, project(d, hv), 1.0)
        draw_tsuba(L, d, tsuba, v)
        draw_hilt(L, d, tsuba, hv)
    return mouth


HIDE_UNDER_HAND = ("hilt", "tsuba", "saya", "cord")


def rasterize(L, R, hold_hands=()):
    """Layer → 192×192 RGBA. 몸 뒤(gy<0) 픽셀은 몸 실루엣과 겹치면 지움. 쥔 손 픽셀 위의 손잡이·코등이·칼집 입구도 지움(주먹이 감쌈)."""
    im = Image.new("RGBA", (WF, WF), (0, 0, 0, 0))
    po = im.load()
    body = R.image.load()
    hands = []
    for name in hold_hands:
        a = R.anchors.get(name)
        if a:
            hands.append((name, to_px(a)))
    for (x, y), (c, gy, kind, prio) in L.px.items():
        bx, by = x, y
        inside = 0 <= bx < hero.FW and 0 <= by < hero.FH and body[bx, by][3] > 0
        if inside and gy < 0 and kind not in ("glint",):
            continue
        if inside and kind in HIDE_UNDER_HAND and hands:
            part = R.part_at(bx, by) or ""
            if part.startswith("hand") and any(math.hypot(bx - hx_, by - hy) < 6.5 for _, (hx_, hy) in hands):
                continue
        wx, wy = x + OFF, y + OFF
        if 0 <= wx < WF and 0 <= wy < WF:
            po[wx, wy] = c
    return im


# =============================================================================
# 휴대(허리 칼집) — 해부 왼허리. 입구는 몸의 hipL 기준점을 따라가고(출렁임·골반 기울기), 칼집은 뒤·아래·바깥으로.
# =============================================================================
SAYA_DIR = (-0.78, -0.55, -0.30)                  # 칼집 끝 쪽(로컬): 뒤 · 바깥(해부 왼쪽) · 아래 (53라운드: 손잡이가 배 앞을 가로질러 정면·뒷면에서 읽히게 -0.36 → -0.55)


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


HILT_DIR = _norm(tuple(-c for c in SAYA_DIR))


def saya_vec(sway=0.0):
    """sway(허리천 흔들림 값) 만큼 칼집 끝이 앞뒤로 흔들린다(관성)."""
    a = math.radians(sway * 2.2)
    f, r, z = SAYA_DIR
    return _norm((f * math.cos(a) - r * math.sin(a), f * math.sin(a) + r * math.cos(a), z))


def mouth_point(d, R):
    """칼집 입구(설계 화면 3튜플) = hipL 기준점 + 앞 3 · (측면은 hipL 이 몸 중심이므로) 깊이만 해부 왼쪽 11."""
    hx_, hy = R.anchors["hipL"]
    if d in ("down", "up"):
        _, sy, gy = project(d, (3.0, -11.0, 0.0))
        return (hx_, hy + 1.0 + (sy - project(d, (0, -11.0, 0))[1]), gy)
    sx, _, _ = project(d, (2.5, 0, 0))
    gy = ground(d, 2.5, -11.0)[1]
    return (hx_ + sx, hy + 1.0, gy)


def saya_hold(d, p):
    """왼손이 칼집 입구를 쥔 자세(엄지가 코등이에): 1차 골격으로 입구를 찾고 왼손 IK 목표로 넣는다."""
    R0 = hero.build(d, p)
    m = mouth_point(d, R0)
    t = add(m, project(d, SAYA_DIR), 2.2)          # 입구 바로 뒤 칼집을 쥠 — 코등이·손잡이는 손 앞으로 드러남
    q = dict(p)
    q["handAt"] = dict(p.get("handAt") or {})
    q["handAt"]["L"] = (t[0], t[1])
    return q


def carry_frame(d, p, R):
    L = Layer()
    draw_saya(L, d, mouth_point(d, R), saya_vec(p.get("sway", 0.0)), with_hilt=True)
    return rasterize(L, R, hold_hands=("handL",) if "L" in (p.get("handAt") or {}) else ())


# 뽑아 든 휴대(공격 뒤 납도 전): 칼 방향(로컬 θ, elev) — 몸 동작별. 오른손은 몸 시트의 손 자리를 그대로 쓴다.
DRAWN = {"idle": (30.0, -40.0), "walk": (30.0, -40.0), "run": (165.0, -18.0), "dash": (172.0, -16.0)}


def drawn_vec(act, i, p):
    th, el = DRAWN[act]
    if act == "walk":
        th += 6.0 * math.sin(math.pi * i / 4)
        el += 4.0 * math.cos(math.pi * i / 4)
    elif act == "idle":
        el += [0, 1, 2, 2, 1, 0][i % 6] * 1.2
    elif act == "run":
        el += 5.0 * math.sin(math.pi * i / 2)
    return dir3(th, el)


def carry_drawn_frame(d, act, i, p, R):
    L = Layer()
    draw_saya(L, d, mouth_point(d, R), saya_vec(p.get("sway", 0.0)), with_hilt=False)
    v = drawn_vec(act, i, p)
    gR = R.anchors["handR"]
    # 깊이: 손 위치의 몸 기준 깊이 — 측면에서 오른손은 right = 가까움, left = 멂
    g = {"down": 2.0, "up": -2.0, "right": 6.0, "left": -6.0}[d]
    draw_katana(L, d, (gR[0], gR[1], g), v, "steel", seed=i)
    holds = ["handR"] + (["handL"] if "L" in (p.get("handAt") or {}) else [])
    return rasterize(L, R, hold_hands=tuple(holds))


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


# =============================================================================
# 뽑기 · 넣기 · 특수(패링) — 53라운드 신규. 구 시트(16×24) 의 단계·ms 합을 그대로 두고 프레임만 늘렸다.
#   along = 칼집 입구에서 손잡이 축으로 오른손까지 거리(설계) — 날이 칼집 밖으로 나온 길이 = along - 3
#   slide = 왼손이 칼집을 뒤로 당긴 거리(사야비키, 설계) — 팔이 닿게 하고 뽑는 힘을 보여 줌
#   idle = True: 마지막 프레임은 대기 0 프레임 몸 + 휴대(뽑아 든/칼집) 그림과 같다(다음 시트로 이어짐)
# =============================================================================
MOVES = {
    "draw": dict(  # 구 70·70·90 (grip · pull · drawn) = 230
        ms=[40, 30, 35, 35, 45, 45],
        phases={"grip": [0, 1], "pull": [2, 3], "drawn": [4, 5]},
        frames=[
            dict(state="sheathed", along=7.0, slide=0.0, crouch=2.0, tw=-0.5, lean=0.4, off="saya"),
            dict(state="partial", along=11.0, slide=2.0, crouch=2.6, tw=-0.6, lean=0.6, off="saya"),
            dict(state="partial", along=24.0, slide=8.0, crouch=3.0, tw=-0.4, lean=0.8, off="saya"),
            dict(state="partial", along=37.5, slide=13.0, crouch=3.2, tw=-0.1, lean=0.8, off="saya"),
            dict(state="steel", th=-45, el=-8, hth=-4, hr=19, hz=43, lunge=0.2, crouch=2.8, tw=0.0, lean=0.7, off="saya", slide=5.0),
            dict(state="steel", idle=True),
        ]),
    "sheathe": dict(  # 구 90·90·90·120 (chiburi · insert · insert · click) = 390
        ms=[45, 45, 45, 45, 45, 45, 60, 60],
        phases={"chiburi": [0, 1], "insert": [2, 3, 4, 5], "click": [6, 7]},
        frames=[
            dict(state="steel", th=70, el=24, hth=52, hr=16, hz=47, lunge=0.1, crouch=2.0, tw=0.6, lean=0.4, off="saya"),
            dict(state="embers", th=58, el=-42, hth=44, hr=18, hz=40, lunge=0.3, crouch=3.2, tw=0.7, lean=0.8, off="saya"),
            dict(state="partial", along=40.0, slide=13.0, crouch=3.0, tw=-0.2, lean=0.7, off="saya"),
            dict(state="partial", along=30.0, slide=10.0, crouch=2.8, tw=-0.4, lean=0.6, off="saya"),
            dict(state="partial", along=20.0, slide=6.0, crouch=2.6, tw=-0.5, lean=0.5, off="saya"),
            dict(state="partial", along=11.0, slide=2.0, crouch=2.4, tw=-0.5, lean=0.4, off="saya"),
            dict(state="click", along=7.0, slide=0.0, crouch=2.0, tw=-0.5, lean=0.3, off="saya"),
            dict(state="sheathed", idle=True),
        ]),
    "special": dict(  # 패링. 구 50·90·120·70·110 (ready · window · window(유지) · riposte · recover) = 440
        ms=[25, 25, 50, 40, 120, 35, 35, 50, 60],
        phases={"ready": [0, 1], "window": [2, 3, 4], "riposte": [5, 6], "recover": [7, 8]},
        holdFrame=4,
        frames=[
            dict(state="steel", th=12, el=-14, hth=-6, hr=16, hz=43, lunge=0.1, crouch=3.0, tw=0.0, lean=0.6, off="saya"),
            dict(state="steel", th=-36, el=26, hth=10, hr=15, hz=48, lunge=0.0, crouch=3.6, tw=-0.3, lean=0.4, off="guard"),
            dict(state="steel", th=-52, el=36, hth=24, hr=15, hz=48, lunge=-0.1, crouch=4.4, tw=-0.4, lean=0.3, off="blade"),
            dict(state="steel", th=-56, el=40, hth=26, hr=16, hz=49, lunge=-0.1, crouch=4.8, tw=-0.45, lean=0.3, off="blade"),
            dict(state="glow", th=-56, el=42, hth=26, hr=16, hz=49, lunge=-0.1, crouch=4.6, tw=-0.45, lean=0.3, off="blade"),
            dict(state="glow", th=-28, el=-6, hth=-14, hr=21, hz=43, lunge=1.0, crouch=5.0, tw=-0.1, lean=1.4, off="back"),
            dict(state="steel", th=46, el=-12, hth=38, hr=20, hz=41, lunge=1.0, crouch=5.0, tw=0.6, lean=1.4, off="back"),
            dict(state="fade", th=72, el=-26, hth=52, hr=15, hz=40, lunge=0.6, crouch=3.6, tw=0.6, lean=0.9, off="saya"),
            dict(state="steel", idle=True),
        ]),
}
# 판정·연출 시점(구 시트와 같은 ms) — export 가 assert 로 검사
OLD_TIMING = {"draw": dict(total=230, phaseStart={"grip": 0, "pull": 70, "drawn": 140}),
              "sheathe": dict(total=390, phaseStart={"chiburi": 0, "insert": 90, "click": 270}),
              "special": dict(total=440, phaseStart={"ready": 0, "window": 50, "riposte": 260, "recover": 330})}


# 구 시트(assets/sprites/player/player_katana_*.json, 16×24) 기록 사본 — 파일이 지워져도 대조할 수 있게
OLD_SHEET = {
    "draw": dict(frames=3, frameDurationsMs=[70, 70, 90], phases={"grip": [0], "pull": [1], "drawn": [2]},
                 usage="공격이 아닌 동작(보조 동작 등)으로 전투에 들어갈 때. 연격 1타(katana_combo1)는 자체가 발도 베기라 draw 없이 바로 재생."),
    "sheathe": dict(frames=4, frameDurationsMs=[90, 90, 90, 120], phases={"chiburi": [0], "insert": [1, 2], "click": [3]},
                    usage="공격 뒤 비전투·무공격 시간이 지나면 재생(시간은 시스템)."),
    "special": dict(frames=5, frameDurationsMs=[50, 90, 120, 70, 110],
                    phases={"ready": [0], "window": [1, 2], "riposte": [3], "recover": [4]}, secondaryAction="parry (우클릭 패링)",
                    overlayFx=[{"id": "parry_flash", "spawn": "parry_success", "atFrame": 3, "anchor": "hitbox_center (접점)"}]),
}


def hand_local(fr):
    t = math.radians(fr["hth"])
    return (math.cos(t) * fr["hr"], math.sin(t) * fr["hr"], fr["hz"])


SAYA_MOUTH_LOCAL = (3.0, -11.0, 33.0)
HILT_LOCAL_DIR = HILT_DIR


def off_local(fr, hand, v):
    o = fr["off"]
    if o == "two":
        return add(hand, v, -7.0)                   # 왼손 = 손잡이 끝 쪽
    if o == "saya":
        return add(SAYA_MOUTH_LOCAL, SAYA_DIR, fr.get("slide", 0.0) + 2.2)
    if o == "guard":
        return (9.0, -6.0, 46.0)
    if o == "blade":
        return add(add(hand, v, 15.0), (0.0, 0.0, -2.0))   # 왼손바닥이 날 등을 받침(패링)
    return (-4.0, -15.0, 37.0)                      # back: 뒤·아래로 뻗어 균형


def move_frame_def(kind, n_or_name, i):
    return (COMBO[n_or_name] if kind == "combo" else MOVES[n_or_name])["frames"][i]


def combo_pose(d, fr, i):
    """프레임 정의 → (pose, 오른손 로컬, 칼 벡터 v, 상태, 보이는 날 길이)."""
    st = fr["state"]
    visible = None
    if st in ("sheathed", "partial", "click"):
        along = fr.get("along", 7.0)
        mouth = add(SAYA_MOUTH_LOCAL, SAYA_DIR, fr.get("slide", 0.0))
        hand = add(mouth, HILT_DIR, along)
        v = SAYA_DIR if st == "partial" else HILT_DIR
        if st == "partial":
            visible = along - 3.0
    else:
        hand = hand_local(fr)
        v = dir3(fr["th"], fr["el"])
    off = off_local(fr, hand, v)
    side = d in ("left", "right")
    hR = to_screen(d, hand)
    hL = to_screen(d, off)
    kw = dict(handAt={"R": hR[:2], "L": hL[:2]}, crouch=fr["crouch"], flame=i % 6, pulse=1 if st == "glow" else 0,
              lean=-2.0 * fr["lean"] if side else -2.0 * fr["tw"])
    lg = fr.get("lunge", 0.0)
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
                  twist=-3.2 * fr["tw"], shift=-1.0 * fr["tw"],
                  stilt=-1.2 * fr["tw"], squash=0.05 * fr["lean"], head=round(fr["lean"]),
                  sway=2.0 * fr["tw"])
        back = tuple(s for s, h in (("R", hR), ("L", hL)) if h[2] < -3.0)
        kw["armBack"] = back
    return pose(**kw), hand, v, st, visible


def _anchors(R):
    return {k: [round(c, 1) for c in to_px(R.anchors[k])] for k in ("handR", "handL")}


def idle_end_frame(d, state):
    """'idle' 프레임: 대기 0 프레임 몸(왼손 칼집) + 휴대 그림(뽑아 든 / 칼집)."""
    p = saya_hold(d, hero.act_idle(d)[0])
    R = hero.draw_rig(d, p)
    w = carry_drawn_frame(d, "idle", 0, p, R) if state != "sheathed" else carry_frame(d, p, R)
    return R, w, _anchors(R), state, p


def move_frame(d, kind, key, i):
    """kind = "combo"(key = 1·2·3) / "move"(key = draw·sheathe·special) → (몸 Rig, 무기 RGBA, 손 기준점(도트), 상태, pose)."""
    fr = move_frame_def(kind, key, i)
    if fr.get("idle"):
        return idle_end_frame(d, fr["state"])
    p, hand, v, state, visible = combo_pose(d, fr, i)
    R = hero.draw_rig(d, p)
    L = Layer()
    slide = fr.get("slide", 0.0)
    # 칼집은 항상 허리에(빈 칼집 또는 칼이 든 칼집)
    draw_saya(L, d, mouth_point(d, R), saya_vec(p["sway"] * 0.5), with_hilt=(state in ("sheathed", "click")), slide=slide)
    if state in ("sheathed", "click"):
        if state == "click":
            m = add(mouth_point(d, R), project(d, SAYA_DIR), slide)
            draw_tsuba(L, d, add(m, project(d, HILT_DIR), 1.0), SAYA_DIR, glint=True)
    else:
        gR = R.anchors["handR"]
        grip = (gR[0], gR[1], to_screen(d, hand)[2])
        if state == "partial":
            # 손은 IK 로 닿은 자리 — 날은 칼집 축을 따라 입구까지
            m = add(mouth_point(d, R), project(d, SAYA_DIR), slide)
            grip = add(m, project(d, HILT_DIR), fr["along"])
            draw_katana(L, d, grip, SAYA_DIR, "steel", seed=i, visible=visible)
        else:
            draw_katana(L, d, grip, v, state, seed=hash((kind, str(key))) % 97 + i)
    off = fr["off"]
    hold = ("handR", "handL") if off in ("two", "saya") else ("handR",)
    im = rasterize(L, R, hold_hands=hold)
    return R, im, _anchors(R), state, p


def combo_frame(d, n, i):
    return move_frame(d, "combo", n, i)
