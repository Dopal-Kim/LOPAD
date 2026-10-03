"""단검 v3 — 53라운드 Q28 'B 재 껍데기 송곳니': 자기 재 껍데기에서 부러낸 송곳니 조각, 균열을 타고 흐르는 혼불, 하얗게 달아오른 끝.
역수로 쥔다(날이 새끼손가락 쪽 — 2차 몸 시트 gear3 의 weaponLocal 방향 그대로). 휴대 = 손(계약 §7.1).
치수(설계 ×1.5 = 도트): 조각 16(24 도트, 폭 최대 7 도트 — Q44 +1) + 붕대 손잡이 4.5(7 도트, 녹슨 못 1).
색(Q32): 16색 이하, 주인공 팔레트 — 재 G3~G7(Q44 한 단 밝게) · 셀아웃 SL0 · 호박 A18~A26 · 붕대 PL1/PL2.
빛(Q30): 평소 균열 2줄 1px(A19/A21) + 끝 2 도트(A23) 은은, glow(판정)만 균열 A23 · 끝 A25→A26.
"""
import wv3
from wv3 import K, Q, hero, G, A, PL, OUT, add

FANG = 16.0
GRIP = 4.5
# 폭(차선): 밑동 좁음 → 가운데 넓음(-2..1) → 끝 뾰족. 차선 - = 빛 쪽(화면 위), + = 그늘 쪽
CRACKS = {(4, 0), (5, 0), (6, -1), (7, -1), (8, -2), (9, -1), (10, 0), (11, 1), (12, 1), (13, 0), (14, 0), (15, -1),
          (16, -1), (17, 0), (11, -2), (12, -2)}   # (칸 = t×24, 차선) — 밑동에서 끝으로 갈라지는 균열 두 줄


def width(t):
    """송곳니: 붕대 밑동 좁음 → 배(가운데)가 불룩 → 휘어 뾰족한 끝(빛 쪽으로 치우침)."""
    if t < 0.1:
        return (-2, -1, 0, 1)
    if t < 0.22:
        return (-2, -1, 0, 1, 2, 3)
    if t < 0.55:
        return (-3, -2, -1, 0, 1, 2, 3)
    if t < 0.72:
        return (-3, -2, -1, 0, 1)
    if t < 0.86:
        return (-2, -1, 0, 1)
    return (-1, 0)


def draw_dagger(L, d, grip, v, state):
    glow = state == "glow"
    base = add(grip, K.project(d, v), 1.5)
    fade = state == "fade"

    def col(t, lane, k):
        kk = int(t * 24)
        if t >= 0.88:                                  # 달아오른 끝
            return A[26] if glow else (A[25] if t > 0.95 else A[23])
        if t >= 0.78 and lane == -1:
            return A[25] if glow else A[21]
        if (kk, lane) in CRACKS:
            return A[23] if glow else (A[19] if fade or kk % 3 == 0 else A[21])
        w = width(t)
        if lane == w[0]:
            return G[7] if not fade else G[6]          # 빛 쪽 깨진 날(Q44 한 단 밝게)
        if lane == w[-1]:
            return OUT                                  # 그늘 쪽 셀아웃 — 팔뚝(붕대)과 겹쳐도 떨어져 보이게
        if lane < 0:
            return G[5] if (kk + lane) % 4 else G[6]   # 재 비늘 면
        return G[4] if (kk + lane) % 5 else G[3]

    wv3.fill_blade(L, d, base, v, FANG, col, width, "blade", prio=1)
    hv = (-v[0], -v[1], -v[2])

    def hcol(t, lane, k):
        if t > 0.8:
            return G[5] if lane <= 0 else G[3]         # 부러진 밑동(재)
        return PL[2] if (k + lane) % 3 else PL[1]
    L.stroke(d, add(grip, K.project(d, v), 1.0), hv, GRIP, hcol, lambda t: (-1, 0, 1), "hilt", prio=2)
    nx, ny, ax, ay = K._normal(d, v)
    N = hero.to_px(add(grip, K.project(d, hv), 1.6)[:2])     # 손잡이를 꿰뚫은 녹슨 못
    for lane, c in ((-3, G[7]), (-2, A[18]), (2, A[18]), (3, A[19])):
        L.put(N[0] + nx * lane, N[1] + ny * lane, c, grip[2] + 0.2, "nail", prio=3)
    return add(base, K.project(d, v), FANG)[:2]   # (끝은 축에서 반 차선 빛 쪽 — 이펙트 위치 참고값)


CARRY = {"idle": (140.0, -60.0), "walk": (140.0, -58.0), "run": (165.0, -25.0), "dash": (172.0, -15.0)}   # 역수로 내린 손: 날이 엉덩이 바깥·뒤로


def carry_frame(d, act, i, R):
    import math
    th, el = CARRY[act]
    if act == "walk":
        el += 4.0 * math.cos(math.pi * i / 4)
    L = K.Layer()
    gR = R.anchors["handR"]
    g = {"down": 2.0, "up": -2.0, "right": 6.0, "left": -6.0}[d]
    tip = draw_dagger(L, d, (gR[0], gR[1], g), K.dir3(th, el), "steel")
    return K.rasterize(L, R, hold_hands=("handR",)), tip


def gear_frame(d, name, k, R):
    L = K.Layer()
    v = K.dir3(k["th"], k["el"])
    gR = R.anchors["handR"]
    tip = draw_dagger(L, d, (gR[0], gR[1], K.to_screen(d, k["R"])[2]), v, k["state"])
    return K.rasterize(L, R, hold_hands=("handR",)), tip


DESIGN = dict(design="B 재 껍데기 송곳니 (53라운드 Q28) — 자기 재 껍데기에서 부러낸 송곳니 조각 · 균열 혼불 · 백열 끝 · 붕대 손잡이 + 녹슨 못 · 역수",
              designRef="parts/art/work/gemini/concept_weapons/raw_dagger_B.jpg (참고만 — 시안은 정수, 도트는 역수)",
              glowRule="53라운드 Q30: 평소 균열 1px(A21/A19) + 끝 A23 은은, 판정(glow) 프레임만 균열 A23 · 끝 A26",
              colorBudget=16, colorNote="무기 16색 이하, 전부 주인공 30색 팔레트 안(재 G · 호박 A · 붕대 PL, Q32)",
              reverseGrip=True, bladeLengthDots=19, hiltLengthDots=7)
