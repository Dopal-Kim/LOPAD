"""대검 v3 — 53라운드 Q27 'A 녹슨 양손검': 갈고리(파리어하켄)가 달린 녹슨 츠바이헨더, 박힌 화살촉, 이 빠진 홈에서 새는 혼불.
휴대(Q31): 가죽끈으로 등에 비스듬히 — 손잡이가 오른어깨 위, 날이 왼허리 뒤로. 두 손으로 쥔다(오른손 = 코등이 쪽, 왼손 = 손잡이 끝).
치수(설계 ×1.5 = 도트): 날 44(66 도트, 리카소 7 포함) + 손잡이 10(15 도트) — 2차 몸 시트 안내선(weaponTipDots)과 같은 길이.
색(Q32): 16색 이하, 전부 주인공 팔레트 — 강철 G4~G8 · 녹 A18/A19 · 혼불 A21~A26 · 가죽 WD2/WD3 · 셀아웃 SL0.
빛(Q30): 평소 홈 혼불 1px(A21) 은은, glow(판정) 프레임만 날 가장자리 A25/A23 + 홈 A26.
"""
import math

import wv3
from wv3 import K, Q, hero, G, A, WD, OUT, add

BLADE = 44.0
HILT = 10.0
RIC = 7.0 / 44.0                                     # 리카소(가죽 감은 날 밑동) 비율
NOTCH_EDGE = {(-3, 27), (-3, 28), (3, 18), (3, 19), (3, 20), (2, 19), (3, 47), (-3, 52)}   # 이 빠짐(설계 도트 칸 = t × 66)
SOUL = {(-2, 39): 1, (-3, 38): 0, (-3, 39): 0, (-3, 40): 0, (-2, 38): 2, (-2, 40): 2, (-3, 41): 0}   # 가장 깊은 홈: 혼불(1) · 결손(0) · 데워진 쇠(2)
STEEL = {-3: G[8], -2: G[7], -1: G[6], 0: G[5], 1: G[6], 2: G[5], 3: G[4]}   # 빛 쪽 날 · 빗면 · 면 · 홈(풀러) · 면 · 빗면 · 그늘 날
FADE = {-3: G[6], -2: G[5], -1: G[5], 0: G[4], 1: G[5], 2: G[4], 3: G[4]}


RUST = [((9, 13), (-1, 1)), ((22, 24), (0, 2)), ((33, 37), (-2, 0)), ((45, 47), (1, 2)), ((55, 58), (-1, 1))]   # 녹 얼룩(칸 구간, 차선 구간)


def _rust(kk, lane):
    """녹: 흩뿌린 점이 아니라 몇 군데 얼룩(가운데 A18, 가장자리 한 점 A19)."""
    for (k0, k1), (l0, l1) in RUST:
        if k0 <= kk <= k1 and l0 <= lane <= l1:
            return A[19] if (kk == k0 and lane == l0) else A[18]
    return None


def draw_greatsword(L, d, grip, v, state, carry=False):
    """grip = 오른손(코등이 쪽) 위치(설계 화면 3튜플). 코등이는 grip 앞 2.5. → 칼끝(설계 화면 2튜플)."""
    tsuba = add(grip, K.project(d, v), 2.5)
    glow = state == "glow"
    pal = FADE if state == "fade" else STEEL

    def width(t):
        if t < RIC:
            return (-1, 0, 1)
        if t < RIC + 0.025:
            return tuple(range(-5, 6))                 # 갈고리(파리어하켄)
        if t < 0.84:
            return (-3, -2, -1, 0, 1, 2, 3)
        if t < 0.9:
            return (-2, -1, 0, 1, 2)
        if t < 0.95:
            return (-1, 0, 1)
        return (0,)

    def col(t, lane, k):
        kk = int(t * 66)
        if t < RIC:                                    # 가죽 감은 리카소
            if lane == -1:
                return WD[3] if kk % 3 else G[6]
            return WD[2] if (kk + lane) % 3 else WD[3]
        if abs(lane) >= 4:                             # 갈고리
            return G[7] if lane < 0 else G[4]
        if (lane, kk) in NOTCH_EDGE:
            return None
        s = SOUL.get((lane, kk))
        if s is not None:
            if s == 0:
                return None
            if s == 1:
                return A[26] if glow else A[21]
            return A[23] if glow else A[19]
        if t >= 0.95:
            return A[26] if glow else G[7]
        if t >= 0.84 and abs(lane) == max(abs(x) for x in width(t)):
            return (A[25] if glow else G[8]) if lane < 0 else (A[21] if glow else G[4])   # 칼끝 쪽 날
        if glow:                                       # 판정: 양 날 달아오름 + 홈(풀러)에 불줄 한 줄
            if lane == -3:
                return A[25]
            if lane == 3:
                return A[23]
            if lane == 0:
                return A[21]
        r = _rust(kk, lane) if not glow else None
        if r is not None:
            return r
        return pal[lane]

    wv3.fill_blade(L, d, tsuba, v, BLADE, col, width, "blade", prio=1)
    nx, ny, ax, ay = K._normal(d, v)
    # 박힌 화살촉(날 그늘 쪽 가장자리, 날 길이 0.55) — 촉 2 + 부러진 화살대 + 깃
    P = hero.to_px(add(tsuba, K.project(d, v), BLADE * 0.55)[:2])
    g = tsuba[2]
    for lane, c in ((4, G[6]), (5, G[5])):
        L.put(P[0] + nx * lane, P[1] + ny * lane, c, g, "blade", prio=2)
    for j in range(5):
        L.put(P[0] + nx * (6 + j) - ax * j * 0.45, P[1] + ny * (6 + j) - ay * j * 0.45, WD[3] if j % 2 == 0 else WD[2], g, "blade", prio=2)
    for j, c in ((10, G[7]), (11, G[6])):
        L.put(P[0] + nx * j - ax * (j * 0.45 - 1.2), P[1] + ny * j - ay * (j * 0.45 - 1.2), c, g, "blade", prio=2)
    # 십자 코등이: 긴 막대(±6) + 끝이 날 쪽으로 굽음
    T = hero.to_px(tsuba[:2])
    for lane in range(-7, 8):
        top = G[8] if abs(lane) <= 1 else (G[7] if lane < 0 else G[5])
        L.put(T[0] + nx * lane, T[1] + ny * lane, top, g, "tsuba", prio=3)
        L.put(T[0] + nx * lane - ax, T[1] + ny * lane - ay, G[5] if lane < 2 else G[4], g, "tsuba", prio=3)
    for lane in (-7, 7):
        L.put(T[0] + nx * lane + ax, T[1] + ny * lane + ay, G[6], g, "tsuba", prio=3)
        L.put(T[0] + nx * lane + 2 * ax, T[1] + ny * lane + 2 * ay, G[5], g, "tsuba", prio=3)

    # 손잡이: 가죽(사선 감김) + 가운데 쇠고리 + 둥근 폼멜
    hv = (-v[0], -v[1], -v[2])

    def hcol(t, lane, k):
        if t > 0.84:
            return {-2: G[7], -1: G[8], 0: G[6], 1: G[5], 2: G[4]}.get(lane) if (abs(lane) < 2 or 0.88 < t < 0.97) else None
        if 0.46 < t < 0.54:
            return G[6] if lane <= 0 else G[4]
        if (k + lane) % 3 == 0:
            return WD[2]
        return WD[3] if lane <= 0 else WD[2]
    L.stroke(d, add(tsuba, K.project(d, hv), 1.5), hv, HILT, hcol,
             lambda t: (-2, -1, 0, 1, 2) if t > 0.84 else (-1, 0, 1), "hilt", prio=2)
    if carry:                                          # 등에 멘 가죽끈 고리 2개(날 위·리카소)
        for tt in (0.08, 0.6):
            C = hero.to_px(add(tsuba, K.project(d, v), BLADE * tt)[:2])
            for lane in range(-4, 5):
                L.put(C[0] + nx * lane + ax * 0.4 * lane / 3, C[1] + ny * lane + ay * 0.4 * lane / 3,
                      WD[3] if lane < 0 else WD[2], g + 0.3, "strap", prio=4)
                L.put(C[0] + nx * lane + ax * (1 + 0.4 * lane / 3), C[1] + ny * lane + ay * (1 + 0.4 * lane / 3),
                      WD[2] if lane < 0 else OUT, g + 0.3, "strap", prio=4)
    return add(tsuba, K.project(d, v), BLADE)[:2]


# =============================================================================
# 휴대: 등(칼집 없음, 가죽끈) · 뽑아 든(오른손 한 손으로 낮게 끎)
# =============================================================================
BACK_TH, BACK_EL = -100.0, -56.0                     # 등에 멘 날 방향(로컬) — 아래·해부 왼쪽(왼허리 뒤로), 살짝 뒤로
BACK_REL = (-4.5, 5.6, 16.0)                         # 가슴 기준점 → 코등이(로컬): 등 뒤 · 오른어깨 위
DRAWN = {"idle": (58.0, -30.0), "walk": (58.0, -30.0), "run": (125.0, -16.0), "dash": (140.0, -12.0)}   # 192 틀 아래 여백(6 도트) 안에 칼끝이 들게


def body_lean(d, R):
    """측면 몸 숙임(라디안, + = 앞으로) — 등에 멘 칼도 같이 기운다."""
    if d not in ("left", "right"):
        return 0.0
    sg = 1 if d == "right" else -1
    c, h = R.anchors["chest"], R.anchors["hipL"]
    return math.atan2((c[0] - h[0]) * sg - 2.0, h[1] - c[1])


def rot_fz(vec, a):
    f, r, z = vec
    return (f * math.cos(a) + z * math.sin(a), r, z * math.cos(a) - f * math.sin(a))


def back_frame(d, R):
    L = K.Layer()
    a = body_lean(d, R) - body_lean_rest(d)
    rel = rot_fz((BACK_REL[0] - (2.0 if d in ("left", "right") else 0.0), BACK_REL[1], BACK_REL[2]), a)
    v = wv3.norm3(rot_fz(K.dir3(BACK_TH, BACK_EL), a))
    c = R.anchors["chest"]
    sx, sy, gy = K.project(d, rel)
    tsuba = (c[0] + sx, c[1] + sy, gy)
    grip = add(tsuba, K.project(d, v), -2.5)
    tip = draw_greatsword(L, d, grip, v, "steel", carry=True)
    return K.rasterize(L, R), tip


_REST = {}


def body_lean_rest(d):
    if d not in _REST:
        _REST[d] = body_lean(d, hero.draw_rig(d, hero.act_idle(d)[0]))
    return _REST[d]


def drawn_vec(act, i):
    th, el = DRAWN[act]
    if act == "walk":
        th += 5.0 * math.sin(math.pi * i / 4)
        el += 3.0 * math.cos(math.pi * i / 4)
    elif act == "idle":
        el += [0, 1, 2, 2, 1, 0][i % 6] * 0.8
    elif act == "run":
        el += 3.0 * math.sin(math.pi * i / 2)
    return K.dir3(th, el)


def drawn_frame(d, act, i, R):
    L = K.Layer()
    v = drawn_vec(act, i)
    gR = R.anchors["handR"]
    g = {"down": 2.0, "up": -2.0, "right": 6.0, "left": -6.0}[d]
    tip = draw_greatsword(L, d, (gR[0], gR[1], g), v, "steel")
    return K.rasterize(L, R, hold_hands=("handR",)), tip


# =============================================================================
# 동작 오버레이(2차 몸 시트 gear3 자세 그대로 — weaponLocal 방향, 두 손)
# =============================================================================
def gear_frame(d, name, k, R):
    """k = gear3 정규 자세 또는 IDLE. → (무기 RGBA, 칼끝 설계 좌표 | None)."""
    if k == Q.IDLE:
        if name == "greatsword_sheathe":
            return back_frame(d, R)
        return drawn_frame(d, "idle", 0, R)
    L = K.Layer()
    v = K.dir3(k["th"], k["el"])
    gR = R.anchors["handR"]
    grip = (gR[0], gR[1], K.to_screen(d, k["R"])[2])
    tip = draw_greatsword(L, d, grip, v, k["state"])
    hold = ("handR", "handL") if k["off"] == "two" else ("handR",)
    return K.rasterize(L, R, hold_hands=hold), tip


DESIGN = dict(design="A 녹슨 양손검 (53라운드 Q27) — 갈고리 달린 녹슨 츠바이헨더 · 박힌 화살촉 · 이 빠진 홈에서 새는 혼불 · 가죽 리카소",
              designRef="parts/art/work/gemini/concept_weapons/raw_greatsword_A2.jpg (참고만, 도트는 직접)",
              glowRule="53라운드 Q30: 평소 가장 깊은 홈 혼불 1px(A21) 은은, 판정(glow) 프레임만 날 가장자리 A25/A23 + 홈·끝 A26",
              colorBudget=16, colorNote="무기 16색 이하, 전부 주인공 30색 팔레트 안(강철 G · 녹 A18/A19 · 혼불 A · 가죽 WD, Q32)",
              twoHanded=True, bladeLengthDots=66, hiltLengthDots=15)
