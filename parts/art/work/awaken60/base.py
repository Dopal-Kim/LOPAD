"""원래 무기(각성 전) 로컬 도트 정의 — 전환 띠의 출발 색·형태. weapons_v3 규격(칼 날 55 · 대검 날 90 × 폭 9 · 단검 24 × 7 · 활 60)을 근사.

로컬 좌표: u = 쥔 손(0) → 칼끝, v = 법선(+ = 날선 쪽). 반환 = 색 hex | None.
"""
import math

from kit60 import G, A, SL, PL, WD, h2, clamp

# ---------------------------------------------------------------- 칼
K_U0, K_U1 = 5.0, 58.0       # 날 시작·끝
K_HW = 2.6


def k_curve(u):
    un = (u - K_U0) / (K_U1 - K_U0)
    return -2.0 * max(0.0, un) ** 2


def k_lane(u, v, u0=K_U0, u1=K_U1, hw=K_HW, curve=k_curve, tip=0.10):
    """칼날 차선: (un, dn, edge, back) | None. dn 0 = 등 → 1 = 날선."""
    if u < u0 or u > u1:
        return None
    un = (u - u0) / (u1 - u0)
    d = v - curve(u)
    top = hw
    if un > 1 - tip:
        top = hw - (un - (1 - tip)) / tip * 2 * hw
    if d < -hw or d > top:
        return None
    dn = (d + hw) / (2 * hw)
    return un, dn, d > top - 1.0, d < -hw + 1.0


def katana_hilt(u, v):
    """손잡이·코등이·하바키 (모든 칼 시안 공통 — 손잡이는 그대로 두어 '내 칼'임을 유지)."""
    if -15 <= u < 0 and abs(v) <= 2.0:
        if abs(v) > 1.4:
            return G[2]
        return PL[2] if (int(u) + int(v + 4)) % 4 < 2 else PL[1]
    if -17 <= u < -15 and abs(v) <= 2.4:
        return G[4]
    if 0 <= u < 2.5 and abs(v) <= 4.5:
        if abs(v) > 3.6 and u < 1.2 and v > 0:
            return None                                    # 한쪽 모서리 깨짐
        return SL[6] if v < -2 else SL[4] if v < 2 else SL[2]
    if 2.5 <= u < K_U0 and abs(v) <= 2.6:
        return G[7] if v < 0 else G[5]
    return None


def katana_blade(u, v, glow=False):
    r = k_lane(u, v)
    if r is None:
        return None
    un, dn, edge, back = r
    if edge:
        return A[9] if glow else (A[3] if int(u) % 7 == 3 else A[5])
    if back and 0.4 < un < 0.55 and int(u) % 3 == 0:
        return None                                        # 등 쪽 재 결손
    return G[6] if dn > 0.72 else G[5] if dn > 0.45 else G[4] if dn > 0.18 else G[3]


def katana(u, v, glow=False):
    return katana_hilt(u, v) or katana_blade(u, v, glow)


# ---------------------------------------------------------------- 대검
GS_U0, GS_U1, GS_HW = 3.0, 93.0, 4.5


def gs_hilt(u, v):
    if -21 <= u < 0 and abs(v) <= 2.0:
        if abs(v) > 1.4:
            return WD[1]
        return WD[4] if (int(u) + int(v + 4)) % 3 == 0 else WD[3]
    if -25 <= u < -21 and math.hypot(u + 23, v) <= 2.8:
        return G[7] if v < 0 else G[5]
    if 0 <= u < 3 and abs(v) <= 10:
        return SL[6] if v < -1 else SL[4] if v < 3 else SL[2]
    if 3 <= u < 7 and 7 <= abs(v) <= 10:                   # 코등이 끝이 날 쪽으로 굽음
        return SL[4]
    return None


def gs_lane(u, v, u0=GS_U0, u1=GS_U1, hw=GS_HW):
    if u < u0 or u > u1:
        return None
    un = (u - u0) / (u1 - u0)
    w = hw if un < 0.86 else hw * (1 - (un - 0.86) / 0.14)
    if abs(v) > w:
        return None
    return un, (v + w) / (2 * w if w else 1), w


def gs_blade(u, v, glow=False):
    if 3 <= u < 10 and abs(v) <= 3:
        return WD[3] if int(u + v) % 3 else WD[4]           # 가죽 리카소
    r = gs_lane(u, v)
    if r is None:
        return None
    un, dn, w = r
    if dn < 0.12:
        return A[9] if glow else G[8]
    if dn > 0.88:
        return G[4]
    if abs(v) < 0.6:
        return A[5] if int(u) == 40 else G[5]
    if h2(int(u / 4), int(v / 3), 11) > 0.86:
        return A[2]                                          # 녹 얼룩
    return G[7] if dn < 0.25 else G[6]


def greatsword(u, v, glow=False):
    return gs_hilt(u, v) or gs_blade(u, v, glow)


# ---------------------------------------------------------------- 단검
D_U0, D_U1 = 1.5, 26.0


def d_hw(un):
    return max(0.0, 3.5 * math.sin(math.pi * clamp(un * 0.85 + 0.12)) ** 0.8)


def d_lane(u, v, u0=D_U0, u1=D_U1, hwf=d_hw):
    if u < u0 or u > u1:
        return None
    un = (u - u0) / (u1 - u0)
    w = hwf(un)
    c = 0.8 * un                                            # 끝이 빛 쪽으로 치우침
    d = v - c
    if abs(d) > w or w <= 0.2:
        return None
    return un, (d + w) / (2 * w), w


def dagger_hilt(u, v):
    if -9 <= u < 0 and abs(v) <= 1.6:
        if abs(u + 4) < 0.6:
            return A[2]                                      # 녹슨 못
        return PL[2] if int(u + v + 9) % 3 else PL[1]
    if 0 <= u < 1.5 and abs(v) <= 3.0:
        return G[4]
    return None


def dagger_blade(u, v, glow=False):
    r = d_lane(u, v)
    if r is None:
        return None
    un, dn, w = r
    if un > 0.84:
        return A[9] if (glow or un > 0.92) else A[7]
    return G[7] if dn > 0.75 else G[5] if dn > 0.45 else G[4] if dn > 0.2 else G[3]


def dagger(u, v, glow=False):
    return dagger_hilt(u, v) or dagger_blade(u, v, glow)


# ---------------------------------------------------------------- 활 (로컬: u = 조준 방향, v = 활대 방향, 줌통 = 원점)
B_HALF = 30.0


def bow_uc(v, bend, half=B_HALF):
    return -bend * (abs(v) / half) ** 2


def bow_limb(u, v, draw=0.0, half=B_HALF):
    bend = 5 + 15 * draw
    if abs(v) > half:
        return None
    d = u - bow_uc(v, bend, half)
    hw = 2.1 - 0.9 * abs(v) / half
    if abs(v) <= 4 and abs(d) <= 2.6:
        return PL[2] if int(v + 9) % 3 else PL[1]
    if abs(d) > hw:
        return None
    if abs(v) > half - 4:
        return SL[6] if d > 0 else SL[3]
    if int(abs(v)) in (9, 17, 23) and abs(d) < 0.8:
        return A[5]
    return G[6] if d > 0.9 else G[5] if d > -0.3 else WD[3]
