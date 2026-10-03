"""활 v3 — 53라운드 Q29 'B + 몸에 꽂힌 화살 뽑기': 재·흙 활대(창자루 심) + 호박 균열, 양 끝 갑옷 조각, 혼불 시위(유일하게 빛나는 선), 재 화살.
장전 = 오른어깨 뒤에 꽂힌 자기 화살을 뽑아 시위에 대면 재로 부서져 시위에 스민다(탄 보충). 왼손 = 줌통, 오른손 = 시위.
치수(설계 ×1.5 = 도트): 활대 반길이 20(30 도트, 전체 60) · 폭 4(줌통 5 · 끝 갑옷 5, Q44 굵게) · 화살 34(51 도트).
색(Q32): 16색 이하, 주인공 팔레트 — 재 G2~G6 · 흙 WD2 · 호박 A19~A26 · 갑옷 SL2/4/6 · 붕대 PL1/2.
빛(Q30): 시위 평소 A21(은은한 한 줄) · 당김 A23 · 가득 A25 · 놓는 순간(판정) A26. 활대 균열 1px A21 · 화살촉 A23(가득 A25).
"""
import math

import wv3
from wv3 import K, Q, hero, G, A, WD, SL, PL, add
from v3kit import raster_path

H = 20.0                       # 활대 반길이(설계)
ARROW = 34.0                   # 가득 당김(줌통~시위 32) 보다 길게 — 촉이 활 앞으로 나옴
BODY_ARROW_BASE = (-4.0, 9.5, 56.0)            # 오른어깨 뒤 꽂힌 화살이 몸에 들어간 자리(로컬)
BODY_ARROW_DIR = wv3.norm3((-0.47, 0.47, 0.75))  # 그 화살의 깃 쪽 방향(로컬)
CRACK_S = {-14.0, -6.5, 5.0, 12.5}


def frame_vectors(a):
    """조준 a(로컬 단위) → 활 위 u(a 에 수직, z 에 가까움)."""
    z = (0.0, 0.0, 1.0)
    dz = sum(x * y for x, y in zip(z, a))
    return wv3.norm3(tuple(zc - dz * ac for zc, ac in zip(z, a)))


def scr(d, base, vec):
    """base = 설계 화면 3튜플, vec = 로컬 벡터 → 도트 (x, y), 깊이."""
    q = add(base, K.project(d, vec))
    p = hero.to_px(q[:2])
    return p[0], p[1], q[2]


def limb_point(s, u, a, bend):
    return tuple(uc * s - ac * bend * (s / H) ** 2 for uc, ac in zip(u, a))


def draw_bow(L, d, grip, a, bend, string_col, nock=None, flash=False):
    """grip = 왼손(설계 화면 3튜플). nock = 시위를 당긴 점(설계 화면 3튜플) 또는 None(곧은 시위)."""
    u = frame_vectors(a)
    pts = []
    for i in range(int(2 * H / 0.25) + 1):
        s = -H + i * 0.25
        pts.append((s,) + scr(d, grip, limb_point(s, u, a, bend)))
    for j in range(len(pts) - 1):
        s, x0, y0, g0 = pts[j]
        _, x1, y1, _ = pts[j + 1]
        tx, ty = x1 - x0, y1 - y0
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / ln, tx / ln
        if ny < 0 or (abs(ny) < 1e-6 and nx < 0):
            nx, ny = -nx, -ny
        tip = abs(s) > H - 3.2
        grip_zone = abs(s) < 2.6
        lanes = (-2, -1, 0, 1, 2) if (tip or grip_zone) else (-1, 0, 1, 2)
        for lane in lanes:
            if tip:
                c = {-2: SL[6], -1: SL[6], 0: SL[4], 1: SL[4], 2: SL[2]}[lane]
                kind = "bow"
            elif grip_zone:
                c = PL[2] if (int(s * 4) + lane) % 3 else PL[1]
                kind = "hilt"
            else:
                crack = any(abs(s - cs) < 0.4 for cs in CRACK_S) and lane == 0
                c = A[21] if crack else {-1: G[6], 0: G[5], 1: WD[2] if int(abs(s) * 2) % 5 else G[4], 2: G[3]}[lane]
                kind = "bow"
            L.put(x0 + nx * lane, y0 + ny * lane, c, g0, kind, prio=2)
    top, bot = pts[-1], pts[0]
    path = [(top[1], top[2]), (bot[1], bot[2])] if nock is None else [(top[1], top[2]), hero.to_px(nock[:2]), (bot[1], bot[2])]
    for x, y in raster_path(path):
        L.put(x, y, string_col, grip[2] - 0.5, "string", prio=1)
    if flash:                                          # 놓는 순간 시위 가운데 짧은 번쩍임
        mx, my = (top[1] + bot[1]) / 2, (top[2] + bot[2]) / 2
        for ox, oy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            L.put(mx + ox, my + oy, A[26] if (ox, oy) == (0, 0) else A[25], grip[2] + 0.5, "glint", prio=6)
    return (top[1], top[2]), (bot[1], bot[2])


def draw_arrow(L, d, tail, direction, head_col, length=ARROW, kind="arrow", ash=0.0):
    """tail = 깃 쪽 끝(설계 화면 3튜플), direction = 촉 쪽(로컬 단위). ash > 0 = 재로 부서짐(0~1)."""
    n = int(length / 0.4)
    nx, ny, ax, ay = K._normal(d, direction)
    for i in range(n + 1):
        t = i / n
        x, y, g = scr(d, tail, tuple(c * length * t for c in direction))
        if ash and ((i * 7) % 10) / 10.0 < ash:
            if i % 3 == 0:
                L.put(x + nx * (i % 4 - 1.5) * ash * 3, y + ny * (i % 4 - 1.5) * ash * 3 - ash * 2, G[4] if i % 2 else A[21], g, "ember", prio=4)
            continue
        if t > 0.88:
            L.put(x, y, head_col if t < 0.97 else (A[26] if head_col == A[25] else head_col), g, kind, prio=4)
            if t < 0.93:
                L.put(x + nx, y + ny, A[19], g, kind, prio=4)
                L.put(x - nx, y - ny, A[19], g, kind, prio=4)
            continue
        L.put(x, y, G[5], g, kind, prio=3)
        L.put(x + nx, y + ny, G[3], g, kind, prio=3)
        if t < 0.14 and not ash:                       # 깃
            off = 1.5 + (0.14 - t) * 10
            L.put(x - nx * off, y - ny * off, G[6], g, kind, prio=3)
            L.put(x + nx * (off + 1), y + ny * (off + 1), G[5], g, kind, prio=3)


# =============================================================================
# 동작 오버레이(gear3 자세 그대로)
# =============================================================================
def _grips(d, k, R):
    gL, gR = R.anchors["handL"], R.anchors["handR"]
    return (gL[0], gL[1], K.to_screen(d, k["L"])[2]), (gR[0], gR[1], K.to_screen(d, k["R"])[2])


def wound(L, d, R, col=A[21], big=False):
    """뽑힌 자리(오른어깨 뒤) 불티 — 등 쪽에서만 보임(몸 앞에선 실루엣 가림)."""
    c = R.anchors["chest"]
    base = (c[0], c[1], 0.0)
    rel = (BODY_ARROW_BASE[0] - (2.0 if d in ("left", "right") else 0.0), BODY_ARROW_BASE[1], BODY_ARROW_BASE[2] - 47.0)
    x, y, g = scr(d, base, rel)
    pts = ((0, 0, col), (1, -1, A[19])) + (((-1, -2, A[23]), (1, -3, A[21]), (0, -4, A[19])) if big else ())
    for ox, oy, cc in pts:
        L.put(x + ox, y + oy, cc, g + 0.6, "ember", prio=5)


def gear_frame(d, name, k, R):
    L = K.Layer()
    st = k["state"]
    gripL, gripR = _grips(d, k, R)
    hold = ("handL",)
    if name in ("bow_aim", "attack") and st in ("draw", "full"):
        a = wv3.norm3(tuple(l - r for l, r in zip(k["L"], k["R"])))
        pull = math.dist(k["L"], k["R"])
        bend = 4.5 + 0.18 * max(0.0, pull - 8.0)        # 당긴 만큼 활 끝이 궁수 쪽으로 더 휨
        p = k["tension"]
        scol = A[25] if st == "full" else (A[23] if p > 0.35 else A[21])
        draw_bow(L, d, gripL, a, bend, scol, nock=gripR)
        hc = A[25] if st == "full" else (A[23] if p > 0.35 else A[21])
        if p > 0.05 or name == "attack":
            draw_arrow(L, d, add(gripR, K.project(d, a), -2.0), a, hc, ash=max(0.0, 0.5 - p * 2.5) if name == "bow_aim" else 0.0)
        hold = ("handL", "handR")
        tip = scr(d, gripR, tuple(c * (ARROW - 2.0) for c in a))[:2]
        return K.rasterize(L, R, hold_hands=hold), _design(tip)
    if st == "release":
        a = K.dir3(-15.0, 0.0)
        flash = k["tension"] > 0.5
        draw_bow(L, d, gripL, a, 4.5, A[26] if flash else A[23], flash=flash)
        return K.rasterize(L, R, hold_hands=hold), None
    # 장전·휴대 비슷한 자세: 활은 몸 앞에 거의 세워 든다
    a = K.dir3(0.0, -10.0)
    scol = A[21]
    tip = None
    if name == "bow_reload":
        if st in ("grab", "pull", "bring"):
            if st == "grab":
                head = tuple(-c for c in BODY_ARROW_DIR)
                tail = add(gripR, K.project(d, BODY_ARROW_DIR), 9.0)
            else:
                t = 0.0 if st == "pull" else (0.55 if k.get("sub", 0) == 0 else 0.9)
                head = wv3.norm3(tuple((1 - t) * -bc + t * fc for bc, fc in zip(BODY_ARROW_DIR, (0.9, -0.2, -0.35))))
                tail = add(gripR, K.project(d, head), -10.0)
            draw_arrow(L, d, tail, head, A[23] if st != "grab" else A[21])
            hold = ("handL", "handR")
            tip = _design(scr(d, tail, tuple(c * ARROW for c in head))[:2])
        if st == "refill":
            first = k.get("sub", 0) == 0
            head = wv3.norm3((0.9, -0.2, -0.35))
            draw_arrow(L, d, add(gripR, K.project(d, head), -10.0), head, A[23], ash=0.45 if first else 0.9)
            scol = A[25]
        if st == "settle":
            scol = A[23]
        if st in ("pull", "bring", "refill", "settle"):
            wound(L, d, R)
        if st == "regrow":
            wound(L, d, R, A[23], big=True)
    draw_bow(L, d, gripL, a, 4.5, scol)
    return K.rasterize(L, R, hold_hands=hold), tip


def _design(px):
    """도트 → 설계 화면 좌표(hero.to_px 역변환) — build 가 다시 to_px 로 무기 끝 기준점을 만든다."""
    return (hero.DPIV[0] + (px[0] - hero.PIV[0]) / hero.S, hero.DPIV[1] + (px[1] - hero.PIV[1]) / hero.S)


# =============================================================================
# 휴대(왼손에 내려 든 활) — player_*_free 위
# =============================================================================
CARRY = {"idle": (-60.0, -25.0), "walk": (-60.0, -25.0), "run": (-30.0, -50.0), "dash": (170.0, -35.0)}   # 바깥·앞으로 — 정면에서 활 곡선이 보이게
LDEPTH = {"down": 3.0, "up": -3.0, "left": 10.0, "right": -10.0}


def carry_frame(d, act, i, R):
    th, el = CARRY[act]
    if act == "walk":
        el += 5.0 * math.sin(math.pi * i / 4)
    L = K.Layer()
    gL = R.anchors["handL"]
    draw_bow(L, d, (gL[0], gL[1], LDEPTH[d]), K.dir3(th, el), 4.5, A[21])
    return K.rasterize(L, R, hold_hands=("handL",)), None


DESIGN = dict(design="B + 몸에 꽂힌 화살 뽑기 (53라운드 Q29) — 재·흙 활대 + 호박 균열 · 양 끝 갑옷 조각 · 혼불 시위(유일하게 빛나는 선) · 재 화살",
              designRef="parts/art/work/gemini/concept_weapons/raw_bow_B.jpg (+ 장전 연출 raw_bow_A2, 참고만)",
              glowRule="53라운드 Q30: 시위 평소 A21 · 당김 A23 · 가득 A25 · 놓는 순간 A26 번쩍. 활대 균열 1px A21, 화살촉 A21→A25",
              colorBudget=16, colorNote="무기 16색 이하, 전부 주인공 30색 팔레트 안(재 G · 흙 WD · 호박 A · 갑옷 SL · 붕대 PL, Q32)",
              bowLengthDots=60, arrowLengthDots=36)
