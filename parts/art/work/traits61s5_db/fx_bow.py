"""활 개성 fx 21 장 + 공명 2 — 활 화살·화살비 언어(재 화살대 + 호박 촉 + 갈매기 깃, 불티 꼬리, 적중 = 초승달 호).
묶음(덫·그물·말뚝 고리) = 청회, 불 = pool_liquor_fire 호박 램프, 별 = 금빛(호박 밝은 쪽 + 백열)."""
import math

import tk
from tk import (Cv, Frame, Rand, h2, sheet, tline, taper, ell, star4, sparks, shard, chain, arrow, ember_tail, puff,
                crescent, flame, X0, X1, A17, A18, A19, A21, A23, A25, A26, B0, B1, B2, B3, S0, S1, S2, S3, INK, INK2,
                N0, N1, N2, N3, N4, N5)

W = "bow"
BIND = (N1, N2, N4, N5)


def mc(trait, part=None, **kw):
    d = {"weapon": W, "trait": trait}
    if part:
        d["part"] = part
    d.update(kw)
    return d


def ash_bits(cv, cx, cy, n, r0, r1, seed, ky=1.0, fall=0.0):
    sparks(cv, cx, cy, n, r0, r1, seed, [B2, B3, S1, A18], ky=ky, ln=2, fall=fall)


def stone_bits(cv, cx, cy, n, r0, r1, seed, a0, a1, fall=0.0, sz=2.6):
    """돌 파편(각진 조각, 재·흙)."""
    R = Rand(seed)
    for k in range(n):
        a = math.radians(a0 + (a1 - a0) * R.f())
        d = r0 + (r1 - r0) * R.f()
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d + fall * (d / max(1.0, r1)) ** 2
        s_ = sz * (0.6 + R.f() * 0.8)
        shard(cv, x, y, a + k, s_, s_ * 0.6, [S0, S1, B2, B3][k % 4])
        cv.put(x - 1, y - 1, S2)


def wall_crack(cv, x, cy, h, seed, col_lo=B1, col_hi=A19, glow=False, spread=1.0):
    """벽 면(세로선 x, 위에서 본 벽이라 면이 세로로 납작)에 생기는 금: 위아래로 길게 갈라지는 번개 금 2 +
    짧은 가지 4 + 벽 면 패임(세로 2도트)."""
    R = Rand(seed)
    for dy in range(-int(h * 0.45), int(h * 0.45) + 1):
        cv.put(x + 1, cy + dy, B0)
    for s_ in (-1, 1):
        px, py = x, cy
        for k in range(6):
            ny = py + s_ * (h / 6.0) * (0.8 + 0.4 * R.f())
            nx = x + (R.f() - 0.5) * 6 * spread
            tline(cv, px, py, nx, ny, col_hi if (glow and k < 2) else col_lo, w=2 if k < 2 else 1)
            if k in (1, 3):                              # 가지: 뒤(왼쪽)로 짧게
                bx, by = nx - (4 + R.f() * 5) * spread, ny + s_ * (2 + R.f() * 4)
                tline(cv, nx, ny, bx, by, col_lo)
            px, py = nx, ny


# =============================================================================
# 1. 코앞 사격 — 적을 날리는 충격 원뿔 (회전) · 벽·적에 처박힘
# =============================================================================
def point_blank():
    fr = tk.frame_sheet(96, 96, 4)
    cx, cy = 30, 48
    for i, cv in enumerate(fr):
        if i == 0:                                       # 코앞 섬광 + 화살 끝이 박히는 점
            arrow(cv, cx + 10, cy, 0, 18, glow=True)
            star4(cv, cx + 10, cy, 12, edge=A25, diag=5)
            sparks(cv, cx + 10, cy, 10, 4, 16, 3, [A25, A23], ln=3)
        else:
            # 앞으로 열리는 원뿔: 겹 초승달(>) 세 줄 + 원뿔 테두리 속도선
            t = i / 3.0
            for k in range(3):
                r = 14 + k * 11 + t * 22
                span = 70 - k * 8
                cols = [A19, A21, A23] if i == 1 else ([A18, A19, A21] if i == 2 else [A18, A19])
                if i == 3 and k == 0:
                    continue
                crescent(cv, cx, cy, r, 0, span, 4.2 - k * 0.8 - (i - 1) * 0.8, cols)
            for s in (-1, 1):                            # 원뿔 테두리
                a = math.radians(s * 34)
                r0, r1 = 16 + t * 14, 52 + t * 14
                for u in range(int(r0), int(r1)):
                    if h2(u, s, i) < 0.25 + 0.2 * i:
                        continue
                    cv.put(cx + math.cos(a) * u, cy + math.sin(a) * u, S2 if i < 3 else S1)
            ash_bits(cv, cx + 40, cy, 6 + i * 3, 4, 30, 10 + i, ky=0.6)
    sheet("trait_bow_b_pointBlank", fr, [30, 40, 50, 70], "hitbox_center", (48, 48),
          "코앞 화살이 박히는 별 섬광 → 앞으로 열리는 충격 원뿔(겹 초승달 셋 = hit_bow 호 말투 + 원뿔 테두리 끊긴 속도선), 앞쪽으로 재가 밀려 남",
          ["박힘(별)", "원뿔", "원뿔", "흩어짐"], glow=[0], rotate=True, drawnFacing="right", flipY="allowed",
          anchorNote="pivot = 맞은 적 몸 중심. 진행 각 = 화살 방향(적이 날아갈 쪽)", **mc("b_pointBlank", spawn="trait_proc"))

    fr = tk.frame_sheet(128, 128, 6)
    wx, cy = 82, 64                                      # 벽 면 x = 82 (오른쪽이 벽)
    for i, cv in enumerate(fr):
        t = i / 5.0
        clo = [A21, A21, A19, B3, S0, S0][i]
        wall_crack(cv, wx, cy, 30 + min(i, 3) * 5, 5, col_lo=clo, col_hi=A23 if i else A25, glow=(i <= 1), spread=0.8 + min(i, 3) * 0.15)
        if i == 0:
            star4(cv, wx - 2, cy, 16, edge=A25, diag=7)
            crescent(cv, wx - 4, cy, 18, 180, 120, 5, [A21, A23, A25])
        elif i <= 3:                                     # 되튀는 반달(왼쪽으로 열림) + 돌 파편
            crescent(cv, wx - 2, cy, 16 + 16 * t, 180, 110 - 10 * i, 5 - i, [A19, A21, A23][:4 - i] or [A19])
            stone_bits(cv, wx - 4, cy, 8, 6 + 30 * t, 14 + 44 * t, 20 + i, 120, 240, fall=10 * t * t * 4)
            for k in range(3):                           # 먼지(재빛, 작게)
                tk.puff(cv, wx - 8 - k * 7, cy - 14 + k * 14, 2.5 + i * 0.8, 30 + k + i, cols=(S0, S1, S2, S3))
        else:
            stone_bits(cv, wx - 6, cy + 10, 5, 30, 56, 20 + i, 140, 220, fall=24, sz=2)
            for k in range(3):
                tk.puff(cv, wx - 14 - k * 7, cy - 10 + k * 14, 4.5 - (i - 4) * 1.5, 30 + k, cols=(B0, S0, S1, S1))
        if i in (1, 2):
            sparks(cv, wx - 2, cy, 10, 6, 26, 40 + i, [A23, A21], ln=2, a0=110, a1=250)
    sheet("trait_bow_b_pointBlank_impact", fr, [40, 50, 60, 70, 90, 120], "contact", (82, 64),
          "날아간 적이 벽·기둥·적에 처박힘 — 벽 면(오른쪽)에 큰 별 섬광 + 금이 위아래로 갈라지고, 왼쪽으로 되튀는 반달 + 돌 파편·먼지가 튐 → 금만 어둡게 남음",
          ["처박힘(별)", "되튐", "파편", "파편", "먼지", "금"], glow=[0, 1],
          rotate=True, drawnFacing="right", flipY="allowed",
          anchorNote="pivot = 박힌 자리(벽 면). 진행 각 = 날아온 방향(벽은 그 앞쪽). 적끼리 부딪힐 때도 같은 시트",
          light={"color": "#fff4dc", "radius": 48, "intensity": 0.8, "ms": 120},
          **mc("b_pointBlank", "impact", spawn="trait_proc"))


# =============================================================================
# 2. 튕기는 화살 — 쓰러진 적에서 꺾여 튀는 섬광
# =============================================================================
def ricochet():
    fr = tk.frame_sheet(64, 64, 4)
    kx, ky = 30, 38                                      # 꺾이는 점
    for i, cv in enumerate(fr):
        if i == 0:
            tline(cv, 4, 48, kx, ky, A21, w=2)
            star4(cv, kx, ky, 9, edge=A25, diag=4)
            crescent(cv, kx, ky, 8, 200, 100, 3, [A21, A23])
        else:
            # 들어온 선(재, 식음) + 나간 선(위 오른쪽, 호박) 끝에 갈매기 깃 >
            col_in = [None, S2, S1, S0][i]
            for k in range(0, 28, 2):
                t = k / 28.0
                if h2(k, i) < 0.2 * i:
                    continue
                cv.put(4 + (kx - 4) * t, 48 + (ky - 48) * t, col_in)
            L = [0, 22, 30, 30][i]
            ang = -50
            ex, ey = kx + math.cos(math.radians(ang)) * L, ky + math.sin(math.radians(ang)) * L
            tline(cv, kx, ky, ex, ey, A21 if i < 3 else A19, w=2)
            f = Frame(cv, ex, ey, ang)
            for s in (-1, 1):
                for k in range(6):
                    f.put(-k, s * k * 0.9, A23 if i < 3 else A19)
            # 꺾인 자리: 작은 반달 + 불티
            crescent(cv, kx, ky, 6 + i * 2, 200, 90, 3 - i * 0.6, [A19, A21][: 3 - i] or [A19])
            sparks(cv, kx, ky, 5, 3, 10 + i * 3, 8 + i, [A23, A21, A19], ln=2)
    sheet("trait_bow_b_ricochet", fr, [30, 40, 50, 70], "hitbox_center", (32, 32),
          "쓰러진 적 자리에서 화살길이 꺾여 튐 — 들어온 줄(왼아래) → 꺾인 점 별 섬광·작은 반달 → 위오른쪽으로 나가는 호박 줄 끝에 갈매기 깃(>) 표지",
          ["꺾임(별)", "튀어 나감", "튀어 나감", "식음"], glow=[0], rotate=False, flipX="allowed",
          rotateNote="회전 없음(요청 표). 그림은 −50°(오른쪽 위)로 튐 — 튀는 쪽이 왼쪽이면 flipX. 굳이 맞추려면 angle + 50° 로 돌려도 됨",
          **mc("b_ricochet", spawn="trait_proc"))


# =============================================================================
# 3. 꿰어 박기 — 꽂혀 떨리는 굵은 화살(수명) · 꽂힌 적 발밑 고리(수명) · 화살째 벽에 박힘
# =============================================================================
def perfect_pin():
    fr = tk.frame_sheet(96, 48, 6)
    tx, ty = 80, 24                                      # 촉이 박힌 자리(벽 면)
    for i, cv in enumerate(fr):
        # 벽 면 패임
        for dy in range(-6, 7):
            cv.put(tx + 1 + abs(dy) % 2, ty + dy, B1)
        if i == 0:
            arrow(cv, tx + 4, ty, 0, 54, head=14, thick=3, glow=True)
            star4(cv, tx, ty, 8, edge=A25)
            sparks(cv, tx, ty, 8, 3, 12, 5, [A23, A25], ln=2, a0=120, a1=240)
        elif i <= 4:
            wob = [0, 3, -2, 1.5, -1][i]
            # 꼬리 쪽이 떨림: 화살대를 두 토막(앞은 곧게, 뒤는 wob 만큼 기움)
            f = arrow(cv, tx + 4, ty, 0, 22, head=14, thick=3, fletch=False)
            ang = math.degrees(math.atan2(wob, 34))
            bx, by = tx + 4 - 14 - 22, ty
            g = Frame(cv, bx, by, 180 + ang)
            for v in range(3):
                col = S3 if v == 0 else (S1 if v == 2 else S2)
                g.line(0, v - 1, 32, v - 1, col)
            for k, base in enumerate((26, 32)):          # 깃(굵게, 호박 깃 끝)
                for j in range(6):
                    g.put(base + j, -2 - j * 0.9, S1 if j < 5 else A21)
                    g.put(base + j, 2 + j * 0.9, S1 if j < 5 else A21)
            # 떨림 잔상선
            if abs(wob) > 1:
                ex, ey = g.P(32, 0)
                cv.put(ex - 1, ey - math.copysign(3, wob), S1)
                cv.put(ex + 2, ey - math.copysign(4, wob), S0)
            if i % 2 == 1:
                cv.put(tx - 16, ty - 2, A25)
        else:                                            # 사라짐: 재로 부서짐
            g = Frame(cv, tx, ty, 180)
            for u in range(0, 60, 1):
                if h2(u, 7) < 0.55:
                    continue
                g.put(u, (h2(u, 3) - 0.5) * 3, [S1, B2, S0][u % 3])
            ash_bits(cv, tx - 30, ty, 10, 2, 26, 9, ky=0.4, fall=4)
    sheet("trait_bow_b_perfectPin", fr, [40, 60, 60, 60, 60, 120], "contact", (80, 24),
          "벽·바닥에 꽂힌 굵은 화살(화살대 3도트·촉 14) — 박히는 칸 별 섬광, 수명 동안 꼬리가 좌우로 떨리며(잔상 점) 깃 끝 호박, 끝 칸 재로 부서짐. 벽 면에 작은 패임",
          ["박힘(별)", "떨림", "떨림", "떨림", "떨림", "재로"], glow=[0], loop=False, loopRange=[1, 4], endFrames=[5],
          rotate=True, drawnFacing="right", flipY="allowed",
          lifeRule="f0 박힘 → f1~f4 루프(시스템 durationMs) → f5 사라짐",
          anchorNote="pivot = 촉이 박힌 자리(벽 면·바닥 점). 진행 각 = 화살 방향", **mc("b_perfectPin", spawn="trait_proc"))

    fr = tk.frame_sheet(128, 64, 4)
    cx, cy = 64, 36
    for i, cv in enumerate(fr):
        # 발밑 말뚝 고리: 겹 청회 고리 + 대각 4방향 밧줄을 땅에 박힌 짧은 화살(깃만)이 붙잡음
        for k in range(4):
            a = math.radians(k * 90 + 45)
            ex, ey = cx + math.cos(a) * 46, cy + math.sin(a) * 18
            sx, sy = cx + math.cos(a) * 26, cy + math.sin(a) * 10
            tline(cv, sx, sy, ex, ey, N1, w=2)
            tline(cv, sx, sy - 1, ex, ey - 1, N3)
            t = ((i + k) % 4) / 4.0
            cv.put(sx + (ex - sx) * t, sy + (ey - sy) * t - 1, N5)
            cv.disc(ex, ey + 1, 1.6, B1)
            g = Frame(cv, ex, ey, -90)                   # 박힌 짧은 화살(깃이 위로)
            for u in range(9):
                g.put(u, 0, S3)
                g.put(u, 1, S1)
            for j in range(4):
                g.put(5 + j, -1 - j * 0.8, S1 if j < 3 else A21)
                g.put(5 + j, 2 + j * 0.8, S1 if j < 3 else A21)
        ell(cv, cx, cy, 26, 10, N1, w=3)
        ell(cv, cx, cy, 26, 10, N3, a0=180, a1=360)
        ell(cv, cx, cy, 26, 10, N4, a0=200, a1=340)
        ell(cv, cx, cy, 18, 7, N2, dash=(24, 12), phase=-i * 9)
        ell(cv, cx, cy, 26, 10, N5, dash=(5, 50), phase=i * 22)
    sheet("trait_bow_b_perfectPin_bind", fr, [80, 80, 80, 80], "floor", (64, 36),
          "꽂힌 적 발밑 말뚝 고리 — 굵은 겹 청회 고리 + 대각 4방향 밧줄 끝을 땅에 박힌 짧은 화살(깃만 보임)이 붙잡음, 밧줄 빛이 흐르고 고리 반짝·안쪽 점선이 돎",
          ["루프", "루프", "루프", "루프"], loop=True, loopRange=[0, 3], depth="floor",
          lifeRule="묶여 있는 동안 0~3 루프(시스템 durationMs 로 끝냄)", **mc("b_perfectPin", "bind", spawn="trait_bind"))

    fr = tk.frame_sheet(128, 128, 6)
    wx, cy = 88, 64
    for i, cv in enumerate(fr):
        t = i / 5.0
        clo = [A21, A21, A19, B3, S0, S0][i]
        wall_crack(cv, wx, cy, 30 + min(i, 3) * 5, 11, col_lo=clo, col_hi=A23 if i else A25, glow=(i <= 1), spread=0.8 + min(i, 3) * 0.15)
        # 벽에 박힌 굵은 화살(내내 남음) — 화살째 박힘이 표지
        arrow(cv, wx + 6, cy, 0, 44, head=14, thick=3, glow=(i == 0))
        if i == 0:
            star4(cv, wx - 4, cy, 16, edge=A25, diag=6)
        elif i <= 3:
            crescent(cv, wx - 6, cy, 18 + 16 * t, 180, 120, 5 - i, [A19, A21, A23][:4 - i] or [A19])
            stone_bits(cv, wx - 6, cy, 8, 6 + 26 * t, 14 + 40 * t, 50 + i, 110, 250, fall=30 * t * t)
        else:
            stone_bits(cv, wx - 8, cy + 10, 4, 26, 50, 50 + i, 140, 220, fall=20, sz=2)
            for k in range(2):
                tk.puff(cv, wx - 14 - k * 8, cy + 8 + k * 6, 4 - (i - 4) * 1.5, 60 + k, cols=(B0, S0, S1, S1))
    sheet("trait_bow_b_perfectPin_impact", fr, [40, 50, 60, 70, 90, 120], "contact", (88, 64),
          "화살째 밀려간 적이 벽에 박힘 — 벽 면 금 한가운데 굵은 화살이 꽂혀 남고(코앞 사격 충돌과 구별되는 표지), 왼쪽으로 반달·돌 파편",
          ["박힘(별)", "되튐", "파편", "파편", "먼지", "금"], glow=[0, 1],
          rotate=True, drawnFacing="right", flipY="allowed",
          light={"color": "#fff4dc", "radius": 48, "intensity": 0.8, "ms": 120},
          anchorNote="pivot = 박힌 자리(벽 면). 진행 각 = 화살 방향", **mc("b_perfectPin", "impact", spawn="trait_proc"))


# =============================================================================
# 4. 되튀는 화살 — 끝에 닿아 되튀는 섬광
# =============================================================================
def full_bounce():
    fr = tk.frame_sheet(64, 64, 4)
    wx, cy = 50, 32
    for i, cv in enumerate(fr):
        if i == 0:
            arrow(cv, wx, cy, 0, 24, glow=True)
            star4(cv, wx, cy, 10, edge=A25, diag=4)
            for dy in range(-12, 13, 3):
                cv.put(wx + 2, cy + dy, A23)
        else:
            # 머리핀 호: 들어온 줄(위) → 끝에서 반원으로 돌아 → 아래 줄로 되돌아 나감 + 되돌아가는 갈매기 깃(<)
            r = 7
            prog = [0, 0.6, 1.0, 1.0][i]
            col = A23 if i < 3 else A19
            tline(cv, 10, cy - r, wx - r, cy - r, S2 if i < 3 else S1)
            ell(cv, wx - r, cy, r, r, col, a0=-90, a1=-90 + 180 * min(1.0, prog * 1.5), w=2)
            if prog >= 0.6:
                L = 30 * prog
                tline(cv, wx - r, cy + r, wx - r - L, cy + r, col, w=2)
                ex = wx - r - L
                for s in (-1, 1):
                    for k in range(6):
                        cv.put(ex + k, cy + r + s * k * 0.9, A25 if i < 3 else A21)
            for dy in range(-12, 13, 3):
                if (dy // 3 + i) % 2 == 0:
                    cv.put(wx + 2, cy + dy, B3 if i < 3 else B2)
            sparks(cv, wx, cy, 4, 3, 10, 3 + i, [A21, A23], ln=1, a0=100, a1=260)
    sheet("trait_bow_b_fullBounce", fr, [30, 40, 50, 70], "projectile", (32, 32),
          "가득 당긴 화살이 끝(사거리 끝·벽 면, 오른쪽 점선)에 닿는 별 섬광 → 머리핀처럼 반원을 그리며 되돌아 나가는 호박 줄 + 되돌아가는 갈매기 깃(<)",
          ["닿음(별)", "돌아섬", "되튐", "식음"], glow=[0], rotate=True, drawnFacing="right", flipY="allowed",
          anchorNote="pivot = 화살이 끝에 닿은 자리 근처(그림 가운데). 진행 각 = 원래 날아가던 방향(되튀는 쪽은 그 반대)",
          **mc("b_fullBounce", spawn="trait_proc"))


# =============================================================================
# 5. 낙하 사격 · 공명 덫 비 · 이어지는 비 — 하늘에서 꽂히는 화살
# =============================================================================
def floor_mark(cv, cx, cy, r, prog, cols, tick=True):
    """바닥 표식: 납작 고리 + 가운데를 가리키는 갈매기 눈금 3."""
    ell(cv, cx, cy, r, r * 0.4, cols[0], dash=(30, 10), phase=prog * 40)
    if tick:
        for k in range(3):
            a = math.radians(-90 + k * 120 + prog * 30)
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.4
            f = Frame(cv, x, y, math.degrees(a) + 180)
            for j in range(5):
                f.put(j * 0.8, -j * 0.8, cols[1])
                f.put(j * 0.8, j * 0.8, cols[1])


def sky_arrow(cv, x, y, ang, L, seed, glow=False, tail=40):
    arrow(cv, x, y, ang, L, glow=glow)
    ember_tail(cv, *Frame(cv, x, y, ang).P(-12 - L, 0), ang, tail, seed)


def drop_frames(kind):
    fr = tk.frame_sheet(96, 192, 6)
    cx, gy = 48, 176
    ang = 80
    for i, cv in enumerate(fr):
        if kind == "trap" and i <= 3:                    # 덫 비: 묶인 적 발밑 덫 세모 끈이 먼저 빛남
            for k in range(3):
                a0 = math.radians(-90 + k * 120)
                a1 = math.radians(-90 + (k + 1) * 120)
                tline(cv, cx + math.cos(a0) * 22, gy + math.sin(a0) * 9, cx + math.cos(a1) * 22, gy + math.sin(a1) * 9, N3 if i < 3 else N4)
        if kind == "drop":
            floor_mark(cv, cx, gy, 22 - i * 1.5 if i < 3 else 18, i, (A19 if i < 3 else A21, A21 if i < 3 else A23))
        elif kind == "trap":
            floor_mark(cv, cx, gy, 24, i, (N2 if i < 3 else N3, N3), tick=False)
        if i < 3:
            ty = [58, 108, 156][i]
            tx = cx - (gy - ty) / math.tan(math.radians(ang)) * 0.9
            if kind == "echo":
                for k, (dx, dy) in enumerate(((-9, 4), (-3, -2), (3, 3), (9, -1), (0, 8))):
                    sky_arrow(cv, tx + dx, ty + dy, ang, 26, 11 + k, tail=20 + 6 * k % 14)
                f = Frame(cv, tx, ty, ang)
                for v in range(-11, 12):
                    x, y = f.P(-26, v)
                    cv.put(x, y, N3 if kind == "trap" else A19)
            else:
                sky_arrow(cv, tx, ty, ang, 34 if kind == "drop" else 30, 3, tail=60)
                if kind == "drop":                       # 낙하 사격: 화살 둘레 아래 방향 갈매기 줄(가속)
                    for k in range(2):
                        f = Frame(cv, tx, ty - 20 - k * 12, ang)
                        for s in (-1, 1):
                            for j in range(5):
                                f.put(-j, s * j, S2)
        elif i == 3:                                     # 판정: 꽂힘 별
            if kind == "echo":
                for k, dx in enumerate((-12, -4, 4, 12, 0)):
                    arrow(cv, cx + dx, gy - 2 + (k % 2) * 3, ang + (dx * 1.2), 22, glow=(k == 4))
                star4(cv, cx, gy - 4, 14, edge=A25, diag=6)
            else:
                arrow(cv, cx + 1, gy - 2, ang, 30, glow=True)
                star4(cv, cx, gy - 2, 13, edge=A25, diag=6)
            sparks(cv, cx, gy - 2, 12, 4, 22, 33, [A25, A23], ln=3, a0=180, a1=360, ky=0.6)
            if kind == "trap":
                for k in range(3):                       # 덫 끈이 조이며 빛남
                    a0 = math.radians(-90 + k * 120)
                    tline(cv, cx + math.cos(a0) * 16, gy + math.sin(a0) * 7, cx, gy, N5)
        else:                                            # 꽂힌 화살 + 먼지 고리 → 재
            n_ar = 5 if kind == "echo" else 1
            for k in range(n_ar):
                dx = [0, -12, -4, 4, 12][k] if n_ar > 1 else 0
                a = ang + dx * 1.2
                f = Frame(cv, cx + dx, gy - 4, a)
                for u in range(6, 34 - (i - 4) * 10):
                    if i == 5 and h2(u, k) < 0.45:
                        continue
                    f.put(-u, 0, S2 if i == 4 else S1)
                    f.put(-u, 1, S1 if i == 4 else S0)
            r = 18 + (i - 3) * 8
            ell(cv, cx, gy, r, r * 0.35, B2 if i == 4 else B1, dash=(20, 16), w=2)
            for k in range(4):
                a = math.radians(k * 90 + 45)
                puff(cv, cx + math.cos(a) * r, gy + math.sin(a) * r * 0.35, 4 - (i - 4) * 1.5, 7 + k)
    return fr


def drop_shot():
    fr = drop_frames("drop")
    sheet("trait_bow_b_dropShot", fr, [40, 40, 40, 40, 70, 100], "floor", (48, 176),
          "하늘에서 꽂히는 화살 한 발 — 바닥에 갈매기 눈금 셋 달린 표식 고리가 먼저 좁혀 들고, 화살이 불티 꼬리 + 아래로 겹친 갈매기 줄(가속)을 끌며 떨어져 f3 꽂힘 별 → 먼지 고리 → 재",
          ["낙하", "낙하", "닿기 직전", "꽂힘(판정)", "먼지", "재"], glow=[3],
          impactFrame=3, impactAtMs=120, spawnNote="떨어질 자리에 생성 — f3 시작(120ms 뒤)이 판정. 세 발이면 시차를 두고 세 번",
          **mc("b_dropShot", spawn="trait_proc"))


def rain_echo():
    fr = drop_frames("echo")
    sheet("trait_bow_b_rainEcho", fr, [40, 40, 40, 40, 70, 100], "floor", (48, 176),
          "쓰러진 자리에 떨어지는 화살 한 다발 — 다섯 발이 호박 끈에 묶인 다발로 불티 꼬리를 끌며 떨어져 f3 부채꼴로 꽂히며 큰 별 → 먼지 고리 → 재. 바닥 표식 없음(낙하 사격·덫 비와 구별)",
          ["낙하", "낙하", "닿기 직전", "꽂힘(판정)", "먼지", "재"], glow=[3],
          impactFrame=3, impactAtMs=120, **mc("b_rainEcho", spawn="trait_proc"))


def res_breach():
    fr = drop_frames("trap")
    sheet("trait_res_bow_breach", fr, [40, 40, 40, 40, 70, 100], "floor", (48, 176),
          "덫에 묶인 적 위로 떨어지는 하늘 화살 — 발밑 덫 세모 청회 끈이 빛나는 가운데 화살이 떨어져 f3 꽂힘 별 + 세모 끈이 가운데로 조이며 청백으로 번쩍 → 먼지 → 재",
          ["낙하(덫 빛)", "낙하", "닿기 직전", "꽂힘(판정)", "먼지", "재"], glow=[3],
          impactFrame=3, impactAtMs=120, weapon=W, resonance="res_bow_breach", tag="breach", spawn="resonance_proc")


# =============================================================================
# 6. 화살 덫 — 세워진 화살 셋(수명) · 밟으면 접혀 묶는 닫힘
# =============================================================================
def trap_arrow(cv, bx, by, ang, L, glint=False):
    """바닥에 촉을 묻고 깃이 위로 선 화살(ang = 화살대가 바닥에서 뻗는 방향)."""
    f = Frame(cv, bx, by, ang)
    for u in range(L):
        f.put(u, 0, S3 if u < L - 1 else S2)
        f.put(u, 1, S1)
    for j in range(5):
        f.put(L - 5 + j, -1 - j * 0.8, S1 if j < 4 else A21)
        f.put(L - 5 + j, 2 + j * 0.8, S1 if j < 4 else A21)
    cv.put(bx, by, A19)
    cv.put(bx + 1, by, B1)
    if glint:
        x, y = f.P(L * 0.5, 0)
        cv.put(x, y, A25)


def arrow_trap():
    fr = tk.frame_sheet(64, 64, 4)
    cx, cy = 32, 46
    pts = [(cx + math.cos(math.radians(a)) * 14, cy + math.sin(math.radians(a)) * 6) for a in (-90, 30, 150)]
    for i, cv in enumerate(fr):
        ell(cv, cx, cy, 16, 6.5, B1, w=2)
        for k in range(3):                               # 덫 끈(청회) 세모
            a, b = pts[k], pts[(k + 1) % 3]
            tline(cv, a[0], a[1] - 1, b[0], b[1] - 1, N2)
        tline(cv, *pts[(i) % 3], *pts[(i + 1) % 3], N4)
        for k, (x, y) in enumerate(pts):                 # 가운데로 기운 화살 셋
            lean = math.degrees(math.atan2(-24, (cx - x) * 0.6))
            trap_arrow(cv, x, y, lean, 22, glint=(k == i % 3))
    sheet("trait_bow_b_arrowTrap", fr, [120, 120, 120, 120], "floor", (32, 46),
          "대쉬로 떠난 자리 바닥에 촉을 묻고 가운데로 기운 화살 셋(세발 덫) + 발치를 잇는 청회 덫 끈 세모, 빛이 끈과 화살대를 차례로 돎",
          ["루프", "루프", "루프", "루프"], loop=True, loopRange=[0, 3], depth="ysort",
          depthNote="바닥 위 물체(Y 정렬, bow_arrow_stuck 과 같음)",
          lifeRule="덫이 남아 있는 동안 0~3 루프(시스템 durationMs) — 밟히면 이 시트를 끄고 _snap", **mc("b_arrowTrap", spawn="trait_place"))

    fr = tk.frame_sheet(96, 96, 5)
    cx, cy = 48, 66
    for i, cv in enumerate(fr):
        close = [0.0, 0.45, 1.0, 1.0, 1.0][i]
        r = 22 * (1 - close) + 7 * close
        pts = [(cx + math.cos(math.radians(a)) * r, cy + math.sin(math.radians(a)) * r * 0.42) for a in (-90, 30, 150)]
        if i == 0:
            star4(cv, cx, cy - 6, 12, edge=A25, diag=5)
        for k, (x, y) in enumerate(pts):                 # 화살이 가운데로 접혀 엇갈림(우리 모양)
            tip_x, tip_y = cx + (cx - x) * 0.8 * close, cy - 34 + 8 * (1 - close)
            ang = math.degrees(math.atan2(tip_y - y, tip_x - x))
            L = int(math.hypot(tip_x - x, tip_y - y))
            if i <= 3:
                trap_arrow(cv, x, y, ang, L)
            else:
                f = Frame(cv, x, y, ang)
                for u in range(0, L, 2):
                    f.put(u, 0, S1)
        if i >= 2:                                       # 청회 끈이 감겨 묶음(나선 3바퀴)
            for k in range(160):
                t = k / 159.0
                a = t * 6 * math.pi + i
                yy = cy - 4 - t * 24
                rr = 9 - t * 3
                x = cx + math.cos(a) * rr
                y = yy + math.sin(a) * rr * 0.35
                if math.sin(a) > -0.2:
                    col = N4 if i == 2 else (N3 if i == 3 else N2)
                    if i == 4 and h2(k, 1) < 0.5:
                        continue
                    cv.put(x, y, col)
            if i == 2:
                for k in range(3):
                    cv.put(cx - 6 + k * 6, cy - 16 - k * 3, N5)
        if i == 1:
            sparks(cv, cx, cy - 6, 10, 4, 18, 9, [A23, A21], ln=2)
        if i >= 3:
            ash_bits(cv, cx, cy - 14, 6, 6, 20, 30 + i, fall=4)
    sheet("trait_bow_b_arrowTrap_snap", fr, [30, 40, 60, 80, 110], "floor", (48, 66),
          "덫을 밟는 순간 별 섬광 → 세 화살이 가운데로 접혀 엇갈려 우리 모양 → 청회 끈이 나선으로 감겨 묶음(반짝) → 끈만 남고 화살은 재로",
          ["밟힘(별)", "접힘", "감김", "묶음", "풀림"], glow=[0], **mc("b_arrowTrap", "snap", spawn="trait_proc"))


# =============================================================================
# 7. 화살 그물 — 그물이 오므라드는 고리 · 묶인 적 발밑 그물 고리(수명)
# =============================================================================
def rain_snare():
    fr = tk.frame_sheet(192, 192, 6)
    cx, cy = 96, 104
    ky = 0.55
    for i, cv in enumerate(fr):
        r = [88, 70, 50, 34, 26, 24][i]
        n = 12
        pts = [(cx + math.cos(2 * math.pi * k / n) * r, cy + math.sin(2 * math.pi * k / n) * r * ky) for k in range(n)]
        col_net = [N3, N4, N4, N3, N2, N1][i]
        for k in range(n):                               # 바깥 고리 + 가운데로 모이는 날줄
            a, b = pts[k], pts[(k + 1) % n]
            tline(cv, a[0], a[1], b[0], b[1], col_net)
            if k % 2 == 0:
                tline(cv, a[0], a[1], cx + (a[0] - cx) * 0.3, cy + (a[1] - cy) * 0.3, N2 if i < 4 else N1)
        for k in range(n):                               # 안쪽 씨줄 고리(그물눈)
            a = pts[k]
            b = pts[(k + 1) % n]
            m1 = (cx + (a[0] - cx) * 0.62, cy + (a[1] - cy) * 0.62)
            m2 = (cx + (b[0] - cx) * 0.62, cy + (b[1] - cy) * 0.62)
            tline(cv, m1[0], m1[1], m2[0], m2[1], N2 if i < 4 else N1)
        if i <= 3:                                       # 그물 끝마다 화살이 가운데를 가리키며 끌어당김
            for k in range(0, n, 2):
                x, y = pts[k]
                ang = math.degrees(math.atan2(cy - y, cx - x))
                arrow(cv, x + math.cos(math.radians(ang)) * 8, y + math.sin(math.radians(ang)) * 8, ang, 10, head=8,
                      glow=(i == 0))
        if i == 0:
            star4(cv, cx, cy, 10, core=X0, mid=X1, edge=N5)
        if i == 3:                                       # 다 오므림: 가운데 매듭 반짝
            star4(cv, cx, cy, 7, core=N5, mid=N5, edge=N4)
        if i >= 4:
            ash_bits(cv, cx, cy, 10, 20, 40, 60 + i, ky=0.5)
    sheet("trait_bow_b_rainSnare", fr, [40, 50, 60, 70, 90, 120], "floor", (96, 104),
          "화살비 한가운데로 그물이 오므라듦 — 12각 청회 그물(바깥 고리·날줄·안쪽 씨줄) 끝마다 가운데를 가리키는 화살 여섯이 끌어당기며 반지름 88 → 24 로 좁혀 들고, 다 오므리면 가운데 매듭 반짝",
          ["펼침(별)", "오므림", "오므림", "묶음(매듭)", "남음", "풀림"], glow=[0], depth="floor",
          **mc("b_rainSnare", spawn="trait_proc"))

    fr = tk.frame_sheet(128, 64, 4)
    cx, cy = 64, 36
    for i, cv in enumerate(fr):
        rx, ry = 42 - (i % 2), 15
        # 그물 격자(마름모) — 타원 안만
        for d in range(-60, 61, 8):
            for s in (-1, 1):
                for u in range(-50, 51):
                    x = cx + u
                    y = cy + (u * s + d + i * 2) * 0.36
                    if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                        cv.put(x, y, N2)
        ell(cv, cx, cy, rx, ry, N1, w=2)
        ell(cv, cx, cy, rx, ry, N3, a0=180, a1=360)
        for k in range(8):                               # 둘레 매듭 + 화살 깃 말뚝
            a = math.radians(k * 45 + i * 6)
            x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry
            cv.disc(x, y, 1.0, N4 if (k + i) % 2 == 0 else N3)
            if k % 2 == 0:
                for j in range(4):
                    cv.put(x - j * 0.7, y - 2 - j, S1)
                    cv.put(x + j * 0.7, y - 2 - j, S1)
        cv.put(cx + math.cos(i * 1.57) * 20, cy + math.sin(i * 1.57) * 7, N5)
    sheet("trait_bow_b_rainSnare_bind", fr, [80, 80, 80, 80], "floor", (64, 36),
          "묶인 적 발밑 그물 고리 — 타원 안 마름모 그물눈(청회) + 둘레 매듭 8 + 화살 깃 말뚝 넷, 그물이 살짝 숨 쉬듯 조였다 풂(꽂힘 말뚝 고리와 달리 '그물 면')",
          ["루프", "루프", "루프", "루프"], loop=True, loopRange=[0, 3], depth="floor",
          lifeRule="묶여 있는 동안 0~3 루프(시스템 durationMs 로 끝냄)", **mc("b_rainSnare", "bind", spawn="trait_bind"))


# =============================================================================
# 8. 흩날리는 살 — 사방으로 흩어지는 화살 꽃
# =============================================================================
def scatter_volley():
    fr = tk.frame_sheet(128, 128, 5)
    cx, cy = 64, 64
    for i, cv in enumerate(fr):
        if i == 0:
            star4(cv, cx, cy, 14, edge=A25, diag=7)
            for k in range(8):                           # 꽃잎 자리(짧은 화살촉 8)
                a = k * 45 + 22.5
                x, y = cx + math.cos(math.radians(a)) * 10, cy + math.sin(math.radians(a)) * 10
                arrow(cv, x, y, a, 0, head=8, fletch=False)
            continue
        d = [0, 18, 34, 48, 56][i]
        for k in range(8):
            a = k * 45 + 22.5 + i * 4                    # 살짝 돌며 퍼짐(꽃잎 소용돌이)
            rad = math.radians(a)
            x, y = cx + math.cos(rad) * d, cy + math.sin(rad) * d
            if i <= 3:
                arrow(cv, x, y, a, 10, head=8)
                ember_tail(cv, *Frame(cv, x, y, a).P(-20, 0), a, 4 + d * 0.4, 5 + k, dots=2)
            else:
                f = Frame(cv, x, y, a)
                for u in range(0, 14, 2):
                    f.put(-u, 0, S1)
        # 가운데 꽃술: 호박 고리(식음)
        if i <= 2:
            ell(cv, cx, cy, 6 + i * 3, 6 + i * 3, [None, A23, A21][i], dash=(30, 15))
        sparks(cv, cx, cy, 6, 4, d * 0.7 + 4, 70 + i, [A21, A19, B3], ln=1)
    sheet("trait_bow_b_scatterVolley", fr, [30, 40, 50, 60, 80], "hitbox_center", (64, 64),
          "쓰러진 자리 별 섬광 안에 화살촉 8 이 꽃잎처럼 모였다가 → 살짝 돌며 사방으로 흩어지는 화살 꽃(불티 꼬리) + 가운데 호박 꽃술 고리 → 화살대 자국만 남음. 날아가는 화살 자체는 bow_arrow_rapid",
          ["모임(별)", "핌", "퍼짐", "퍼짐", "사라짐"], glow=[0], **mc("b_scatterVolley", spawn="trait_proc"))


# =============================================================================
# 9. 걸으며 연사 — 발밑 짧은 먼지 (선택 요청)
# =============================================================================
def rapid_stride():
    fr = tk.frame_sheet(64, 32, 4)
    cx, cy = 32, 24
    for i, cv in enumerate(fr):
        r = [3, 5, 6, 5][i]
        for k, dx in enumerate((-9, 0, 9)):
            if i == 3 and k == 1:
                continue
            puff(cv, cx + dx - i * 1.5, cy - (k % 2) - i * 0.6, r - (k % 2), 4 + k + i * 3,
                 cols=(B1, B2, B3, S1) if i < 3 else (B0, B1, B2, B2))
        if i <= 1:                                       # 연사 반동: 뒤로 튀는 작은 재 점
            for k in range(3):
                cv.put(cx - 14 - k * 3 - i * 3, cy - 4 - k, S1)
    sheet("trait_bow_b_rapidStride", fr, [40, 50, 60, 80], "player_pivot", (32, 24),
          "연사 중 걸음마다 발밑에 이는 짧은 먼지 셋(dash_dust 말투, 작게) + 반동으로 뒤로 튀는 재 점 — 이동 개성 선택 요청분",
          ["일어남", "퍼짐", "퍼짐", "가라앉음"], depth="floor", flipX="allowed",
          flipNote="그림은 오른쪽으로 걸음(먼지가 왼쪽으로 처짐). 왼쪽이면 flipX",
          spawnNote="연사 중 걸음 한 번(또는 300ms)마다 1회 권장", **mc("b_rapidStride", spawn="trait_step"))


# =============================================================================
# 10. 꿰미 — 꿰인 적들이 화살 끝으로 끌려가는 꼬챙이 섬광 (회전) · 서로 부딪힘
# =============================================================================
def skewer():
    fr = tk.frame_sheet(128, 64, 5)
    cy = 32
    for i, cv in enumerate(fr):
        # 꼬챙이(긴 화살대) — 앞으로 끌려감
        shift = [0, 6, 12, 16, 18][i]
        tip = 116
        tline(cv, 6 + shift, cy, tip - 12, cy, S3)
        tline(cv, 6 + shift, cy + 1, tip - 12, cy + 1, S1)
        arrow(cv, tip, cy, 0, 0, head=14, thick=2, glow=(i == 0), fletch=False)
        # 꿴 두 자리: 세로 초승달 고리(관통 링 — bow_arrow_pierce_hit 말투), 앞쪽으로 끌리며 겹쳐짐
        for k, ux in enumerate((40, 76)):
            x = ux + shift * (1.6 if k == 0 else 1.0)
            if i == 0:
                star4(cv, x, cy, 9, edge=A25)
            else:
                cols = [A19, A21, A23] if i < 3 else [A18, A19]
                crescent(cv, x, cy, 10 - i, 180, 120, 3, cols, ky=1.4)
                crescent(cv, x + 2, cy, 10 - i, 0, 80, 2, cols[:2], ky=1.4)
            # 끌림 속도선(뒤로)
            for v in (-8, 8):
                L = 6 + i * 5
                for u in range(L):
                    if h2(u, v, i) < 0.3:
                        continue
                    cv.put(x - 10 - u, cy + v * (0.6 + 0.1 * k), S1 if u > L * 0.5 else S2)
        if i >= 3:
            ash_bits(cv, 60, cy, 8, 6, 40, 7 + i, ky=0.4)
    sheet("trait_bow_b_skewer", fr, [30, 40, 50, 60, 80], "hitbox_center", (64, 32),
          "관통 화살이 꼬챙이처럼 두 적을 꿰어 화살 끝 쪽(오른쪽)으로 끌고 감 — 꿴 두 자리 별 → 세로 초승달 고리가 앞으로 끌리며 간격이 좁혀짐 + 뒤로 끊긴 속도선",
          ["꿰임(별)", "끌림", "끌림", "좁혀짐", "식음"], glow=[0], rotate=True, drawnFacing="right", flipY="allowed",
          anchorNote="pivot = 그림 가운데(꿴 두 적 사이 쯤). 진행 각 = 화살 방향", **mc("b_skewer", spawn="trait_proc"))

    fr = tk.frame_sheet(128, 128, 6)
    cx, cy = 64, 64
    for i, cv in enumerate(fr):
        t = i / 5.0
        if i == 0:
            for s in (-1, 1):
                crescent(cv, cx + s * 4, cy, 20, 90 - 90 * s, 120, 6, [A21, A23, A25])
            star4(cv, cx, cy, 16, edge=A25, diag=8)
            # 가운데를 지나는 화살대(꼬챙이)
            tline(cv, cx - 40, cy, cx + 40, cy, S3)
            tline(cv, cx - 40, cy + 1, cx + 40, cy + 1, S1)
        else:
            r = 18 + 30 * t ** 0.7
            for s in (-1, 1):                            # 양쪽으로 벌어지는 세로 반달 두 겹(괄호)
                crescent(cv, cx, cy, r, 90 - 90 * s, 110 - i * 8, max(1.2, 6 - i), [A19, A21, A23][: max(1, 4 - i)])
                if i <= 3:
                    crescent(cv, cx, cy, r * 0.7, 90 - 90 * s, 80, max(1.0, 4 - i), [A18, A19])
            if i <= 3:                                   # 부러진 화살 토막이 위아래로 튐
                for k, s in enumerate((-1, 1)):
                    x = cx + s * (6 + 12 * t)
                    y = cy + s * (8 + 26 * t) * (1 if k else -1) * -1
                    f = Frame(cv, x, y, 20 * s + i * 30 * s)
                    f.line(-6, 0, 6, 0, S3)
                    f.line(-6, 1, 6, 1, S1)
            ash_bits(cv, cx, cy, 6 + i * 3, r * 0.5, r + 8, 60 + i, fall=i * 1.5)
    sheet("trait_bow_b_skewer_impact", fr, [40, 50, 60, 70, 90, 120], "contact", (64, 64),
          "꿰여 끌려온 적들이 서로 부딪힘 — 화살대(꼬챙이)를 사이에 둔 맞붙은 반달 둘 + 큰 별 → 반달이 괄호처럼 양쪽으로 벌어지고 부러진 화살 토막이 위아래로 튐",
          ["맞부딪힘(별)", "벌어짐", "토막 튐", "벌어짐", "식음", "재"], glow=[0],
          rotate=True, drawnFacing="right", anchorNote="pivot = 부딪힌 자리. 진행 각 = 끌려온 방향(화살대 방향)",
          **mc("b_skewer", "impact", spawn="trait_proc"))


# =============================================================================
# 11. 불화살 한 발 · 술별 — 웅덩이 점화
# =============================================================================
def fire_arrow():
    fr = tk.frame_sheet(96, 64, 5)
    cy = 44
    for i, cv in enumerate(fr):
        if i == 0:                                       # 화살이 수면을 스치는 불씨(왼쪽) + 꼬리
            ember_tail(cv, 30, cy - 2, 0, 26, 3)
            arrow(cv, 34, cy - 2, 0, 0, head=10, fletch=False, glow=True)
            star4(cv, 26, cy, 9, edge=A25, diag=4)
        reach = [20, 46, 80, 90, 90][i]
        for k, x in enumerate(range(10, 10 + reach, 8)):  # 왼→오로 번지는 불혀 줄
            age = (reach - (x - 10)) / 30.0
            h = min(1.0, age) * (16 + 6 * math.sin(k * 1.9)) * (1.0 if i < 4 else 0.6)
            if h < 3:
                continue
            flame(cv, x, cy + 2 + (k % 2) * 2, h, 7 + (k % 2) * 2, lean=0.8,
                  cols=(A19, A21, A23, A25) if i < 4 else (A19, A21, A23))
        if 1 <= i <= 3:                                  # 불길 앞머리: 앞으로 누운 갈매기 불꽃(화살 말투)
            hx = 10 + reach
            f = Frame(cv, min(hx, 88), cy - 4, 0)
            for s in (-1, 1):
                for j in range(6):
                    f.put(-j, s * j * 0.9, A25 if i < 3 else A23)
        sparks(cv, 48, cy - 16, 4 + i * 2, 4, 30, 20 + i, [A23, A21, A25], ln=1, ky=0.5)
    sheet("trait_bow_fireArrow", fr, [40, 50, 60, 80, 100], "floor", (48, 44),
          "완벽 놓기 화살이 웅덩이를 스치는 불씨 → 불길이 왼→오로 확 번져 불혀 줄(pool_liquor_fire 램프) + 앞머리 갈매기 불꽃(>) → 가라앉음. 끝 칸 뒤 시스템이 pool_liquor_fire 로 이어 줌",
          ["불씨(별)", "번짐", "번짐", "타오름", "가라앉음"], glow=[0], rotate=False, flipX="allowed",
          rotateNote="회전 없음(요청 표) — 그림은 왼→오 번짐, 화살이 왼쪽으로 가면 flipX",
          light={"color": "#d67a11", "radius": 48, "intensity": 0.75, "ms": 300},
          **mc("fireArrow", spawn="trait_proc", next="pool_liquor_fire"))


def star_drunk():
    fr = tk.frame_sheet(96, 64, 5)
    cx, cy = 48, 46
    for i, cv in enumerate(fr):
        if i == 0:                                       # 하늘 화살 끝이 수면에 닿음: 금빛 별 + 술 왕관 시작
            arrow(cv, cx, cy - 2, 80, 22, glow=True)
            star4(cv, cx, cy - 2, 12, edge=A25, diag=6)
        if 1 <= i <= 3:                                  # 술 왕관이 솟으며 불이 붙음(왕관 끝마다 불혀)
            for k in range(7):
                a = math.radians(180 + k * 30)
                d = 8 + i * 5
                bx = cx + math.cos(a) * d
                by = cy + math.sin(a) * d * 0.4
                h = [0, 14, 20, 14][i] * (0.6 + 0.4 * abs(math.cos(k)))
                flame(cv, bx, by, h, 6, lean=math.cos(a) * 1.2, cols=(A19, A21, A23, A25) if i < 3 else (A19, A21, A23))
            ell(cv, cx, cy, 10 + i * 6, (10 + i * 6) * 0.4, A21, dash=(20, 10), phase=i * 9)
        if i == 4:
            for k in range(5):
                flame(cv, cx - 20 + k * 10, cy, 8, 5, cols=(A19, A21))
        if i >= 1:                                       # 금빛 별 조각이 위로 튐
            R = Rand(5 + i)
            for k in range(6):
                x = cx - 24 + R.f() * 48
                y = cy - 14 - i * 5 - R.f() * 10
                cv.put(x, y, A25 if i < 3 else A23)
                if k % 2 == 0 and i < 3:
                    cv.put(x + 1, y, A23)
                    cv.put(x - 1, y, A23)
                    cv.put(x, y - 1, A23)
                    cv.put(x, y + 1, A23)
    sheet("trait_bow_b_starDrunk", fr, [40, 50, 60, 80, 100], "floor", (48, 46),
          "하늘 화살이 술 웅덩이에 꽂히는 금빛 별 → 술 왕관이 솟으며 왕관 끝마다 불혀(둥글게 핀 불꽃 꽃) + 금빛 별 조각이 위로 튐 → 낮은 불로. 불화살 한 발의 '가로 번짐'과 달리 '둥근 꽃'",
          ["꽂힘(별)", "불꽃 핌", "핌", "튐", "가라앉음"], glow=[0],
          light={"color": "#d67a11", "radius": 48, "intensity": 0.75, "ms": 300},
          **mc("b_starDrunk", spawn="trait_proc", next="pool_liquor_fire"))


# =============================================================================
# 12. 별 표적 — 하늘 화살 자리로 빨려 드는 별빛 소용돌이
# =============================================================================
def star_well():
    fr = tk.frame_sheet(192, 192, 6)
    cx, cy = 96, 100
    ky = 0.55
    for i, cv in enumerate(fr):
        rot = i * 26
        for arm in range(5):
            for k in range(70):
                t = k / 69.0                             # 바깥 → 안
                r = 86 * (1 - t) ** 0.9 + 4
                a = math.radians(arm * 72 + rot + 200 * t)
                x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * ky
                if t < 0.3:
                    if k % 2 == 0:
                        cv.put(x, y, A19)
                elif t < 0.7:
                    cv.put(x, y, A21)
                    cv.put(x, y + 1, A19)
                else:
                    cv.disc(x, y, 1.0, A21)
                    cv.put(x, y - 1, A23)
            # 팔마다 별 하나가 안으로 끌려 듦
            tt = ((i / 6.0) + arm * 0.2) % 1.0
            r = 86 * (1 - tt) ** 0.9 + 6
            a = math.radians(arm * 72 + rot + 200 * tt)
            sx, sy = cx + math.cos(a) * r, cy + math.sin(a) * r * ky
            star4(cv, sx, sy, 3 + 2 * (1 - tt), core=A26, mid=A25, edge=A23)
        # 가운데: 하늘 화살 자리 금빛 별(꽂힌 화살 + 큰 별)
        arrow(cv, cx + 2, cy - 2, 80, 20, glow=(i <= 1))
        star4(cv, cx, cy, [16, 12, 10, 10, 9, 8][i], core=X0 if i <= 1 else A26, mid=X1 if i <= 1 else A25, edge=A23, diag=[8, 6, 4, 4, 3, 3][i])
        ell(cv, cx, cy, 14, 14 * ky, A21, dash=(20, 20), phase=-rot)
    sheet("trait_bow_b_starWell", fr, [40, 50, 50, 60, 70, 90], "floor", (96, 100),
          "하늘 화살이 꽂힌 자리(가운데 금빛 큰 별 + 꽂힌 화살)로 바닥 높이 5갈래 별빛 소용돌이가 감겨 듦 — 팔마다 작은 별 하나가 안으로 끌려 들고, 칸마다 26° 돎",
          ["빨아들임(큰 별)", "빨아들임", "빨아들임", "빨아들임", "빨아들임", "식음"], glow=[0, 1], depth="floor",
          light={"color": "#eecc78", "radius": 64, "intensity": 0.8, "ms": 200},
          **mc("b_starWell", spawn="trait_proc"))


# =============================================================================
# 13. 공명 말뚝 박기 — 위에서 꽂히는 말뚝 화살 + 묶음 고리
# =============================================================================
def res_weight():
    fr = tk.frame_sheet(64, 96, 5)
    cx, cy = 32, 64                                      # 몸 중심
    for i, cv in enumerate(fr):
        if i == 0:                                       # 위에서 떨어지는 굵은 화살(아래로)
            arrow(cv, cx, 30, 90, 22, head=12, thick=3)
            ember_tail(cv, cx, 30 - 34, 90, 10, 3, dots=2)
        elif i == 1:                                     # 몸 중심에 꽂힘: 별 + 청회 고리 번쩍
            arrow(cv, cx, cy + 4, 90, 26, head=12, thick=3, glow=True)
            star4(cv, cx, cy + 2, 11, core=X0, mid=X1, edge=N5, diag=5)
            ell(cv, cx, cy + 14, 20, 7, N5, w=2)
        else:
            arrow(cv, cx, cy + 4, 90, 26, head=12, thick=3)
            # 청회 묶음 고리 둘이 화살대를 따라 조여 내려옴
            for k in range(2):
                rr = [0, 0, 16, 12, 11][i] - k * 3
                yy = cy - 6 + k * 10 + (i - 2) * 3
                col = N4 if i < 4 else N3
                ell(cv, cx, yy, rr, rr * 0.35, N1, w=2)
                ell(cv, cx, yy, rr, rr * 0.35, col, a0=180, a1=360)
            if i == 2:
                sparks(cv, cx, cy + 4, 8, 4, 16, 5, [A23, A21, N4], ln=2)
            if i == 4:
                ash_bits(cv, cx, cy, 6, 4, 18, 9, fall=4)
    sheet("trait_res_bow_weight", fr, [40, 40, 60, 80, 100], "hitbox_center", (32, 64),
          "밀리거나 끌려온 적에게 위에서 굵은 말뚝 화살이 꽂힘 — 몸 중심에 청회 별 + 발치 청회 고리 번쩍 → 청회 묶음 고리 둘이 화살대를 따라 조여 내려옴",
          ["낙하", "꽂힘(별)", "묶음", "조임", "남음"], glow=[1],
          weapon=W, resonance="res_bow_weight", tag="weight", depth="above", spawn="resonance_proc")


ALL = [point_blank, ricochet, perfect_pin, full_bounce, drop_shot, arrow_trap, rain_snare, rain_echo, scatter_volley,
       rapid_stride, skewer, fire_arrow, star_well, star_drunk, res_weight, res_breach]
