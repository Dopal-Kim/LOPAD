"""개성 fx 공용 모양 — 무기 언어(칼 '은선' / 대검 붓획) 위에 '개성 갈래' 고유 모양을 얹는다.

갈래별 고유 모양(한눈에 구별):
  띄움(launch)  = 솟구치는 먼지 기둥 + 발밑 그림자(체커) + 위로 긋는 속도선
  착지(land)    = 납작한 원형 먼지 고리 + 바닥 금
  처박힘(impact)= 벽면(그림 오른쪽 세로면)에 퍼지는 금 + 뒤로 튀는 파편·먼지 + 면을 따라 눌린 섬광
  끌어당김(pull)= 안쪽을 가리키는 갈매기표·당기는 줄
  묶음(bind)    = 청회 고리 + 말뚝
  불(fire)      = pool_liquor_fire 계열 혓바닥
  분신(clone)   = 먹(칼 그림자)·청백(달) 실루엣
"""
import math
import random

from kit import (A, B, BIND, CRIM, G, MOON, S, SL, X0, X1, DUST_ASH, DUST_BROWN, DUST_COOL, Field, chunk, clamp,
                 crack_tree, densify, draw_cracks, embers, ground_shadow, lerp, normals, puff, smooth, star4)

# ---------------------------------------------------------------- 대검 붓획
GS_RAMP = [(0.84, A[25]), (0.7, A[23]), (0.56, A[21]), (0.42, A[19]), (0.28, B[3]), (0.14, B[2])]


def gs_band(fx, pts, rmax, age=0.0, hot=False, taper=0.6, dither=0.3, rmin=0.6):
    """대검 붓획: 시작 가늘고·가운데 굵고·끝 갈라짐(마른 붓 디더). age 0~1 = 식음(값·폭이 줄어듦)."""
    f = Field(fx.w, fx.h)
    v0 = 1.0 - age * 0.62
    f.path(pts, lambda t: max(rmin, rmax * (math.sin(math.pi * clamp(t * 0.85 + 0.08)) ** taper) * (1 - age * 0.35)),
           lambda t: v0 * (0.75 + 0.25 * math.sin(math.pi * t)))
    ramp = list(GS_RAMP)
    if hot:
        ramp = [(0.95, X1)] + ramp
    f.paint(fx, ramp, dither=dither)
    return f


def gs_ring(fx, cx, cy, rx, ry, width, age=0.0, hot=False, a0=None, a1=None, vfun=None, dither=0.3):
    f = Field(fx.w, fx.h)
    f.ring(cx, cy, rx, ry, width, 1.0 - age * 0.62, a0, a1, vfun)
    ramp = list(GS_RAMP)
    if hot:
        ramp = [(0.95, X1)] + ramp
    f.paint(fx, ramp, dither=dither)


# ---------------------------------------------------------------- 칼 은선 고리·초승달
SILVER_RAMP = [(0.86, G[14]), (0.7, G[13]), (0.52, G[11]), (0.34, G[9]), (0.16, SL[6])]
MOON_RAMP = [(0.86, MOON[5]), (0.66, MOON[4]), (0.46, MOON[3]), (0.26, MOON[2]), (0.1, MOON[1])]


def lens_arc(fx, cx, cy, rx, ry, amid, span, width, ramp=None, hot=False, outer_bright=True, dither=0.0):
    """초승달(렌즈) 호: 가운데 굵고 양끝 1도트. 바깥 가장자리가 가장 밝다."""
    ramp = ramp or SILVER_RAMP
    f = Field(fx.w, fx.h)
    a0 = amid - span / 2
    n = max(12, int(span / 2))
    for k in range(n + 1):
        t = k / n
        a = math.radians(a0 + span * t)
        w = max(0.6, width * math.sin(math.pi * t) ** 0.8)
        # 바깥으로 치우친 두께: 중심선 = 반지름 - w/2
        rr = 1.0 - (w * 0.5) / rx
        x, y = cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a)
        f.capsule(x, y, x, y, w * 0.55, w * 0.55, 0.55 + 0.45 * math.sin(math.pi * t), 0.55 + 0.45 * math.sin(math.pi * t), flat=0.2)
    # 바깥 1도트 가장자리 강조
    rp = list(ramp)
    if hot:
        rp = [(0.93, X0)] + rp
    f.paint(fx, rp, dither=dither)
    if outer_bright:
        for k in range(n + 1):
            t = k / n
            if 0.12 < t < 0.88:
                a = math.radians(a0 + span * t)
                fx.put(cx + rx * math.cos(a), cy + ry * math.sin(a), (X1 if hot and 0.35 < t < 0.65 else ramp[0][1]))


# ---------------------------------------------------------------- 먹(그림자) 덩이
INK_RAMP = [(0.7, SL[2]), (0.35, SL[1]), (0.06, G[1])]


def ink_field(fx, f, rim=SL[5], rim2=G[10]):
    """먹 덩이: 몸 SL1~2 · 바깥 테 SL5 · 윗 테 은빛(칼 그림자도 '은선'으로 테두리) — 어두운 바닥에서도 실루엣이 읽히게."""
    f.paint(fx, INK_RAMP)
    w, h = fx.w, fx.h
    th = 0.06
    for i, v in enumerate(f.v):
        if v <= th:
            continue
        x, y = i % w, i // w
        up = y > 0 and f.v[i - w] <= th
        edge = up or (x > 0 and f.v[i - 1] <= th) or (x < w - 1 and f.v[i + 1] <= th) or (y < h - 1 and f.v[i + w] <= th)
        if up:
            fx.put(x, y, rim2 if v > 0.4 else SL[7])
        elif edge:
            fx.put(x, y, rim)


# ---------------------------------------------------------------- 띄움: 솟구치는 기둥 + 그림자
def launch_column(fx, k, n, px, py, style="katana", seed=1):
    """k = 칸 번호(0..n-1). 먼지 기둥이 발에서 위로 솟고 발밑 그림자가 남는다."""
    rng = random.Random(seed * 31 + k)
    t = k / max(1, n - 1)
    dust = DUST_ASH if style == "katana" else DUST_BROWN
    # 발밑 그림자(뜬 적의 그림자 — 줄어듦)
    ground_shadow(fx, px, py, 19 - 5 * t, 6 - 1.5 * t)
    top = py - lerp(30, 104, smooth(min(1.0, (k + 0.6) / (n - 1.5))))
    # 기둥: 아래가 넓고 위로 가늘게, 칸이 갈수록 흩어짐
    m = 15
    for j in range(m):
        u = j / (m - 1)
        y = lerp(py - 4, top, u ** 0.9)
        r = lerp(9, 3.2, u) * (1 + 0.25 * t) * (1 - 0.5 * max(0, t - 0.6))
        x = px + rng.uniform(-3, 3) * (1 + 2 * t) + math.sin(u * 7 + k) * 3
        if t > 0.7 and rng.random() < (t - 0.6):
            continue
        puff(fx, x, y, r, dust if t < 0.75 else [dust[0], dust[0], dust[1], dust[2]])
    # 위로 긋는 속도선(가는 선 — 칼은 은빛, 대검은 호박)
    lc = [G[11], SL[7], SL[6]] if style == "katana" else [A[23], A[21], A[19]]
    if t < 0.85:
        for j in (range(5) if style == "katana" else (0, 2, 4)):
            x = px + (j - 2) * 7 + rng.randint(-1, 1)
            y0 = py - 8 - rng.randint(0, 10) - 20 * t
            L = rng.randint(14, 26) * (1 - 0.5 * t)
            c = lc[min(2, int(t * 3))]
            fx.line(x, y0, x, y0 - L, c, every=lambda q, L=L: q < L * 0.8 or q % 2 == 0)
    # 바닥 튐 알갱이
    for j in range(6 + int(4 * (1 - t))):
        a = rng.uniform(math.pi * 1.05, math.pi * 1.95)
        r = rng.uniform(10, 22) * (0.5 + t)
        fx.put(px + math.cos(a) * r, py + math.sin(a) * r * 0.6 - 10 * t, dust[2] if rng.random() < 0.5 else dust[3])


# ---------------------------------------------------------------- 착지: 원형 먼지 + 금
def land_ring(fx, k, n, px, py, style="katana", seed=2, heavy=False, hot=False):
    rng = random.Random(seed)
    t = k / max(1, n - 1)
    dust = DUST_ASH if style == "katana" else DUST_BROWN
    sy = 0.36
    R = lerp(18, 54, smooth(min(1, (k + 0.5) / 3.0))) + (4 if heavy else 0)
    # 금(바닥, 납작)
    trees = []
    for j in range(7 if heavy else 5):
        ang = j * 2 * math.pi / (7 if heavy else 5) + rng.uniform(-0.3, 0.3)
        trees.append(crack_tree(px, py, ang, rng.uniform(22, 40) * (1.2 if heavy else 1.0), random.Random(seed * 7 + j), depth=1, jitter=0.4))
    if style == "katana":
        core = [G[10], G[9], SL[7], SL[6], SL[5], SL[4]][min(5, k)]
        sh = G[1]
    else:
        core = [A[23], A[21], A[19], B[3], B[3], B[2]][min(5, k)]
        sh = B[0]
    grow = min(1.0, 0.35 + 0.35 * k)
    if k < n - 1 or heavy:
        for tr in trees:
            draw_cracks(fx, tr, core, sh, sy=sy * 1.3, cx=px, cy=py, grow=grow)
    # 충격 고리(첫 칸들만, 가는 선)
    if k <= 1:
        f = Field(fx.w, fx.h)
        f.ring(px, py, R * 0.8, R * 0.8 * sy, 2.2 if k == 0 else 1.5, 1.0 if k == 0 else 0.7)
        ramp = ([(0.85, X1 if hot else G[14]), (0.5, G[12]), (0.2, G[9])] if style == "katana"
                else [(0.85, X1 if hot else A[25]), (0.5, A[23]), (0.2, A[19])])
        f.paint(fx, ramp)
    if k == 0:
        star4(fx, px, py - 2, 6 if heavy else 4, hot=hot, col=None)
    # 먼지 덩이 고리
    m = 14 if heavy else 11
    for j in range(m):
        a = j * 2 * math.pi / m + rng.uniform(-0.15, 0.15)
        rr = R * rng.uniform(0.85, 1.08)
        x, y = px + math.cos(a) * rr, py + math.sin(a) * rr * sy - 2 - 3 * t
        r = (rng.uniform(3.5, 6.0) + (1.5 if heavy else 0)) * (1 - 0.55 * t) * (0.7 + 0.3 * abs(math.sin(a)) + 0.3)
        if t > 0.6 and rng.random() < (t - 0.5):
            continue
        puff(fx, x, y, r, dust if t < 0.6 else [dust[0], dust[0], dust[1], dust[2]])
    for j in range(10):
        a = rng.uniform(math.pi, 2 * math.pi)
        rr = R * rng.uniform(0.6, 1.3)
        fx.put(px + math.cos(a) * rr, py + math.sin(a) * rr * sy - 6 * t - rng.randint(0, 4), dust[3])


# ---------------------------------------------------------------- 처박힘: 벽면 금 + 파편
def wall_impact(fx, k, n, px, py, style="katana", seed=3, scale=1.0, hot=False, scrape=False, twin=False, accent=None):
    """그림 오른쪽 = 벽(진행 방향). px = 벽면. 금은 벽면(세로)을 따라 납작하게, 파편·먼지는 뒤(왼쪽)로 튄다.
    twin = 두 적 사이 충돌(양쪽으로 튐)."""
    rng = random.Random(seed)
    t = k / max(1, n - 1)
    sc = scale
    if style == "katana":
        core_seq = [G[12], G[11], G[10], SL[7], SL[6], SL[5], SL[4]]
        sh = G[1]
        dust = DUST_ASH
        chunk_ramp = [G[1], S[1], S[3], G[11]]
        flash_ramp = [(0.88, X0 if hot else G[14]), (0.66, G[13]), (0.44, G[11]), (0.22, SL[6])]
    else:
        core_seq = [A[25], A[23], A[21], A[19], B[3], B[3], B[2]]
        sh = B[0]
        dust = DUST_BROWN
        chunk_ramp = [B[0], S[0], S[2], S[3]]
        flash_ramp = [(0.88, X0 if hot else A[25]), (0.66, A[23]), (0.44, A[21]), (0.22, A[19])]
    # 벽면 금 — 세로로 퍼지는 거미줄(가로는 0.32 로 눌림) + 굵은 줄기
    nb = 9 if style != "katana" else 8
    grow = min(1.0, 0.5 + 0.35 * k)
    core = core_seq[min(len(core_seq) - 1, k)]
    for j in range(nb):
        ang = (j / nb) * 2 * math.pi + rng.uniform(-0.2, 0.2)
        vert = abs(math.sin(ang))
        L = rng.uniform(34, 54) * sc * (0.55 + 0.6 * vert)
        tr = crack_tree(px, py, ang, L, random.Random(seed * 13 + j), depth=2, jitter=0.4, step=2.2, branch_p=0.22)
        tr2 = [([(px + (x - px) * 0.32, y) for x, y in pts], d) for pts, d in tr]
        draw_cracks(fx, tr2, core, sh, grow=grow, thick=(vert > 0.6))
    # 벽면 함몰(가운데 짙은 홈 + 테)
    if k >= 1:
        for yy in range(int(py - 9 * sc), int(py + 10 * sc)):
            ww = int(2 + 2 * sc * (1 - abs(yy - py) / (10 * sc)))
            for xx in range(px - ww, px + 1):
                fx.put(xx, yy, sh)
            fx.put(px - ww - 1, yy, core_seq[min(6, k + 1)])
    # 벽면 눌린 섬광(세로 렌즈) — 첫 칸들
    if k <= 1:
        f = Field(fx.w, fx.h)
        hh = (34 if k == 0 else 24) * sc
        f.capsule(px - 1, py - hh, px - 1, py + hh, 1.0, 1.0, 0.5, 0.5)
        f.capsule(px - 1, py, px - 1, py, 7 * sc if k == 0 else 4 * sc, 7 * sc if k == 0 else 4 * sc, 1.0, 1.0)
        f.capsule(px - 1, py - hh * 0.6, px - 1, py + hh * 0.6, 2.4 * sc, 2.4 * sc, 0.8 if k == 0 else 0.55, 0.8 if k == 0 else 0.55)
        f.paint(fx, flash_ramp)
        if k == 0:
            # 뒤로 터지는 짧은 광선
            for j in range(7):
                a = math.pi + (j - 3) * 0.32
                L = (14 + 8 * (j % 2)) * sc
                fx.line(px - 2, py, px - 2 + math.cos(a) * L, py + math.sin(a) * L, flash_ramp[1][1] if j % 2 else flash_ramp[2][1])
            if twin:
                for j in range(7):
                    a = (j - 3) * 0.32
                    L = (14 + 8 * (j % 2)) * sc
                    fx.line(px + 2, py, px + 2 + math.cos(a) * L, py + math.sin(a) * L, flash_ramp[1][1] if j % 2 else flash_ramp[2][1])
    # 파편 — 뒤(왼쪽)로 포물선
    nc = int((12 if style != "katana" else 9) * sc)
    sides = [-1, 1] if twin else [-1]
    for side in sides:
        rr = random.Random(seed * 5 + side)
        for j in range(nc):
            a = math.pi + rr.uniform(-1.1, 1.1) if side < 0 else rr.uniform(-1.1, 1.1)
            sp = rr.uniform(28, 62) * sc
            d = sp * (0.18 + 0.82 * smooth(min(1, (k + 0.4) / (n - 1))))
            x = px + math.cos(a) * d
            y = py + math.sin(a) * d * 0.8 + 30 * sc * t * t * rr.uniform(0.3, 1.0)
            if k == 0 and rr.random() < 0.5:
                continue
            r = rr.uniform(2.2, 4.4 if style != "katana" else 3.4) * sc * (1 - 0.3 * t)
            if t > 0.8 and rr.random() < 0.5:
                fx.put(x, y, chunk_ramp[1])
                continue
            chunk(fx, x, y, r, rr.uniform(0, 6), rr, chunk_ramp)
    # 먼지 — 벽 밑동 위아래로 피고 뒤로 번짐
    if k >= 1:
        m = 8 if style != "katana" else 6
        for side in sides:
            rr = random.Random(seed * 9 + side)
            for j in range(m):
                a = (math.pi if side < 0 else 0) + rr.uniform(-1.4, 1.4)
                d = rr.uniform(8, 26) * sc * (0.5 + 0.9 * t)
                x = px + math.cos(a) * d * 0.7 + side * 3
                y = py + math.sin(a) * d
                r = rr.uniform(3, 6.5) * sc * (1 - 0.45 * t) * (1.2 if style != "katana" else 0.9)
                if t > 0.7 and rr.random() < 0.4:
                    continue
                puff(fx, x, y, r, dust if t < 0.65 else [dust[0], dust[0], dust[1], dust[2]])
    # 긁힌 자국(밀고 간 길)
    if scrape:
        for dy in (-7, 7):
            L = int(lerp(40, px - 8, min(1.0, 0.5 + 0.3 * k)))
            c = [A[21], A[19], B[3], B[2], B[2], B[1], B[1]][min(6, k)]
            for x in range(int(px - 8 - L), int(px - 8)):
                if (x * 7 + dy) % 11 < 9:
                    fx.put_if_empty(x, py + dy + (1 if x % 13 < 4 else 0), c)
                    fx.put_if_empty(x, py + dy + 1 + (1 if x % 13 < 4 else 0), B[0])
    if accent and k <= 3:
        rr = random.Random(seed * 17)
        for j in range(10 - 2 * k):
            a = math.pi + rr.uniform(-1.3, 1.3)
            d = rr.uniform(10, 40) * sc * (0.4 + t)
            fx.put(px + math.cos(a) * d, py + math.sin(a) * d, rr.choice(accent))
    # 불티
    if style != "katana" and k <= 3:
        embers(fx, px - 10 * sc, py, 6 - k, 24 * sc * (0.6 + t), random.Random(seed + k))
