"""대검(greatsword) 개성 fx 14 + 공명 2 — 26 시트. 언어 = 기존 대검 붓획(재·호박 넓은 띠, 시작 가늘고·가운데 굵고·끝 마른 붓 갈라짐)
+ 호박 금(갈래 금) + 갈색 흙먼지 덩이 + 돌 파편 + 불티. 개성 갈래 모양은 shapes.py."""
import math
import random

from kit import (A, B, CRIM, FIRE, G, LIQ, S, X0, X1, DUST_BROWN, DUST_ASH, Field, Fx, arc_pts, chunk, clamp, crack_tree,
                 densify, draw_cracks, embers, flame, ground_shadow, lerp, puff, smooth, star4)
from shapes import GS_RAMP, gs_band, gs_ring, land_ring, launch_column, wall_impact

SHEETS = {}


def sheet(name, size, ms, **kw):
    def deco(fn):
        SHEETS[name] = dict(fn=fn, size=size, ms=ms, **kw)
        return fn
    return deco


WHITE_LIGHT = "#fff4dc"
ORANGE = "#e2a33c"


# ------------------------------------------------------------------ 1 날려 보내기
@sheet("trait_greatsword_g_launch_launch", (128, 96), [40, 50, 60, 80, 100],
       anchor="hitbox_center", pivot=(102, 48), rotate=True, flipY="allowed", glow=[0], part="launch", trait="g_launch",
       replaces="hit_greatsword_heavy", depth="above",
       design="날아가는 적 뒤로 남는 충격 꼬리: 적 등 뒤(왼쪽)에 눌린 활꼴 충격파 ')'(대검 붓 띠, f0 백열 심) + 뒤로 길게 끌리는 호박 붓 줄 3 + 갈색 흙먼지 → 식으며 재",
       anchorNote="pivot = 날아가는 적 몸 중심(따라가지 않음 — 맞은 자리). 오른쪽 = 날아가는 방향")
def g_launch_launch(fs):
    px, py = 102, 48
    for k, fx in enumerate(fs):
        age = k / 4.0
        rng = random.Random(200 + k)
        # 뒤로 끌리는 붓 줄
        for j, (dy, L, r) in enumerate(((-13, 70, 3.6), (0, 96, 5.6), (13, 64, 3.6))):
            L2 = L * [0.55, 1.0, 1.0, 0.95, 0.85][k]
            x0 = px - 10 - k * 6
            gs_band(fx, [(x0 - L2, py + dy * (1 + 0.15 * k)), (x0, py + dy * 0.5)], r, age=age, hot=False, taper=0.5)
        # 충격 활꼴
        if k <= 2:
            cx = px - 10 - k * 8
            pts = arc_pts(cx - 14, py, 18 + 4 * k, 26 + 6 * k, -70, 70, 24)
            gs_band(fx, pts, 4.5 - k, age=age * 0.6, hot=(k == 0))
        if k == 0:
            star4(fx, px - 8, py, 7, hot=True)
        # 흙먼지
        for j in range(3 + k):
            x = px - 30 - j * 14 - k * 6 + rng.uniform(-4, 4)
            y = py + rng.uniform(-14, 14)
            puff(fx, x, y, rng.uniform(3, 5.5) * (1 - 0.15 * k), DUST_BROWN)
        if k <= 2:
            embers(fx, px - 20, py, 6, 22, rng)


@sheet("trait_greatsword_g_launch_impact", (160, 160), [40, 40, 50, 60, 70, 90, 120],
       anchor="contact", pivot=(108, 80), rotate=True, flipY="allowed", glow=[0], part="impact", trait="g_launch",
       replaces="hit_burst", depth="above", light=dict(color=WHITE_LIGHT, radius=64, intensity=1.0, ms=140, atFrame=0),
       design="처박힘(큰) = 오른쪽 세로 벽면에 눌린 호박 백열 섬광 → 면을 따라 거미줄처럼 번지는 굵은 호박 금 + 짙은 함몰 · 뒤로 튀는 돌 파편 12·갈색 흙먼지·불티 → 금이 재로 식음",
       anchorNote="pivot = 처박힌 자리(벽 면·기둥 면·부딪친 적). 오른쪽 = 날아간 방향 — 시스템이 충돌 방향으로 회전")
def g_launch_impact(fs):
    for k, fx in enumerate(fs):
        wall_impact(fx, k, len(fs), 108, 80, "greatsword", seed=210, scale=1.25, hot=(k == 0))


# ------------------------------------------------------------------ 2 쳐내기
@sheet("trait_greatsword_g_swatBack", (96, 96), [30, 40, 50, 70],
       anchor="projectile", pivot=(40, 48), rotate=True, flipY="allowed", glow=[0], part="", trait="g_swatBack",
       replaces="katana_whirl_reflect·hit_spark", depth="above", light=dict(color=WHITE_LIGHT, radius=32, intensity=0.9, ms=60, atFrame=0),
       design="둔탁한 금속 섬광: 대검 면(세로 넓은 판) 모양으로 눌린 백열·호박 판 + 오른쪽(되돌아가는 쪽)으로 퍼지는 뭉툭한 짧은 광선 5 + 되돌아가는 굵은 붓 줄 2 · 둥근 '쾅' 호 → 불티",
       anchorNote="pivot = 쳐 낸 투사체 자리. 오른쪽 = 되돌아가는 방향(던진 적 쪽)")
def g_swatBack(fs):
    px, py = 40, 48
    for k, fx in enumerate(fs):
        rng = random.Random(220 + k)
        # 대검 면 판(세로 렌즈)
        f = Field(fx.w, fx.h)
        hh = [24, 22, 18, 12][k]
        f.capsule(px, py - hh, px, py + hh, 2.0, 2.0, 0.9, 0.9)
        f.capsule(px, py - hh * 0.6, px, py + hh * 0.6, [6, 5, 3.5, 2][k], [6, 5, 3.5, 2][k], 1.0 - 0.18 * k, 1.0 - 0.18 * k)
        ramp = ([(0.93, X0), (0.8, X1)] if k == 0 else []) + GS_RAMP
        f.paint(fx, ramp, dither=0.15)
        # 뭉툭한 광선(오른쪽 부채)
        for j in range(5):
            a = math.radians((j - 2) * 22)
            L0 = 8 + 4 * k
            L1 = L0 + [16, 22, 18, 10][k] - abs(j - 2) * 3
            gs_band(fx, [(px + math.cos(a) * L0, py + math.sin(a) * L0), (px + math.cos(a) * L1, py + math.sin(a) * L1)],
                    [2.4, 2.2, 1.6, 1.0][k], age=k * 0.25, hot=(k == 0 and j == 2), dither=0.2)
        # 쾅 호
        if k in (1, 2):
            pts = arc_pts(px, py, 20 + 8 * k, 26 + 8 * k, -55, 55, 20)
            for i, (x, y) in enumerate(densify(pts)):
                if (i // 3) % 2 == 0:
                    fx.put(x, y, A[23] if k == 1 else A[21])
        # 되돌아가는 줄
        if k >= 1:
            for dy in (-6, 6):
                x0 = px + 18 + 6 * k
                gs_band(fx, [(x0, py + dy), (x0 + 22 + 4 * k, py + dy * 0.6)], 1.8, age=0.2 * k, dither=0.2)
        embers(fx, px + 12, py, 5 - k, 16 + 6 * k, rng)


# ------------------------------------------------------------------ 3 되받는 땅울림
@sheet("trait_greatsword_g_quakeGuard", (256, 96), [40, 50, 60, 70, 90, 120],
       anchor="player_pivot", pivot=(12, 56), rotate=True, flipY="allowed", glow=[0], part="", trait="g_quakeGuard",
       replaces="greatsword_charge_crack_line_t2", depth="below",
       design="막은 자리(왼끝)에서 앞으로 달리는 땅울림 금: 굵은 호박 줄기 금이 앞으로 자라며 양옆 잔가지 · 앞머리에 솟는 흙 둔덕(갈색 먼지 + 돌 조각) · 지나간 자리 마른 붓 띠가 바닥을 밝힘 → 재로 식음",
       anchorNote="pivot(왼끝) = 주인공 발(막은 자리). 오른쪽 = 막은 방향. 길이 236 도트 ≈ 3.7칸(설계 4칸)")
def g_quakeGuard(fs):
    px, py = 12, 56
    rng0 = random.Random(230)
    tree = crack_tree(px + 4, py, 0.0, 232, rng0, depth=2, jitter=0.28, step=3.0, branch_p=0.12)
    fronts = [0.3, 0.65, 1.0, 1.0, 1.0, 1.0]
    for k, fx in enumerate(fs):
        rng = random.Random(231 + k)
        g = fronts[k]
        fx_front = px + 4 + 232 * g
        # 금 위 마른 붓 빛(지나간 자리)
        if k <= 3:
            gs_band(fx, [(px + 8, py), (fx_front - 4, py)], [3.2, 3.6, 3.0, 2.0][k], age=[0.1, 0.15, 0.4, 0.7][k], dither=0.45, taper=0.3)
        core = [A[25], A[25], A[23], A[21], A[19], B[3]][k]
        # 가로 금(자란 만큼)
        part = []
        for pts, d in tree:
            P = [(x, y) for x, y in pts if x <= fx_front]
            if len(P) >= 2:
                part.append((P, d))
        draw_cracks(fx, part, core, B[0], sy=0.55, cx=px, cy=py, thick=True)
        # 앞머리 둔덕
        if k <= 2:
            for j in range(5):
                puff(fx, fx_front - 6 + rng.uniform(-6, 6), py - 4 + rng.uniform(-10, 6), rng.uniform(4, 7), DUST_BROWN)
            for j in range(4):
                chunk(fx, fx_front + rng.uniform(-8, 6), py - rng.uniform(6, 20), rng.uniform(2, 3.5), rng.uniform(0, 6), rng)
            embers(fx, fx_front, py - 6, 5, 14, rng)
        else:
            for j in range(6 - k):
                puff(fx, px + 40 + j * 40 + rng.uniform(-6, 6), py - 2 + rng.uniform(-8, 6), rng.uniform(3, 5) * (1.2 - 0.2 * (k - 3)), [B[0], B[1], B[2], B[3]])
        if k == 0:
            star4(fx, px + 6, py - 2, 6, hot=True)


@sheet("trait_greatsword_g_quakeGuard_launch", (96, 128), [40, 50, 60, 70, 90],
       anchor="mob_feet", pivot=(48, 116), glow=[], part="launch", trait="g_quakeGuard", replaces="dash_dust", depth="above",
       design="띄움 = 땅울림이 적 발밑에서 터짐: 호박 금 별(바닥) + 솟구치는 갈색 흙먼지 기둥 + 위로 튀는 돌 조각 · 발밑 체커 그림자(줄어듦)")
def g_quakeGuard_launch(fs):
    px, py = 48, 116
    rng0 = random.Random(240)
    trees = [crack_tree(px, py, j * math.pi / 3 + rng0.uniform(-0.2, 0.2), rng0.uniform(18, 30), random.Random(241 + j), depth=1) for j in range(6)]
    for k, fx in enumerate(fs):
        rng = random.Random(245 + k)
        for tr in trees:
            draw_cracks(fx, tr, [A[25], A[23], A[21], A[19], B[3]][k], B[0], sy=0.4, cx=px, cy=py, grow=min(1, 0.5 + 0.3 * k))
        launch_column(fx, k, len(fs), px, py, "greatsword", seed=246)
        for j in range(5):
            x = px + rng.uniform(-16, 16)
            y = py - 14 - (k + 1) * rng.uniform(10, 18)
            if k < 4:
                chunk(fx, x, y, rng.uniform(1.8, 3.2), rng.uniform(0, 6), rng)


@sheet("trait_greatsword_g_quakeGuard_land", (128, 64), [40, 50, 60, 80, 100, 140],
       anchor="floor", pivot=(64, 40), glow=[], part="land", trait="g_quakeGuard", replaces="crush", depth="below",
       design="착지 = 납작한 원형 갈색 흙먼지 고리 + 호박 바닥 금 5갈래(식어 재) — 칼 착지보다 흙빛")
def g_quakeGuard_land(fs):
    for k, fx in enumerate(fs):
        land_ring(fx, k, len(fs), 64, 40, "greatsword", seed=250)


# ------------------------------------------------------------------ 4 끌어당기기
def inward_chevron(fx, x, y, ang, size, col, col2):
    """안쪽(ang 방향)을 가리키는 갈매기표 '<' — 끌어당김 표지."""
    ca, sa = math.cos(ang), math.sin(ang)
    for s_ in (-1, 1):
        a2 = ang + s_ * 2.4
        x1, y1 = x + math.cos(a2) * size, y + math.sin(a2) * size * 0.6
        fx.line(x, y, x1, y1, col)
        fx.line(x - ca, y - sa, x1 - ca, y1 - sa, col2)


@sheet("trait_greatsword_g_guardPull", (192, 192), [40, 50, 60, 70, 90],
       anchor="floor", pivot=(96, 112), glow=[], part="", trait="g_guardPull", replaces="greatsword_brace_absorb",
       depth="below",
       design="끌어당김 = 바닥 고리가 안으로 오므라듦: 마른 붓 호박 고리(반지름 88 → 26) + 고리 위 안쪽을 가리키는 갈매기표 8 + 바깥에서 안으로 끌리는 흙 자국 줄 12 · 가운데로 모이는 먼지",
       anchorNote="pivot = 주인공 발(고리 중심, 바닥)")
def g_guardPull(fs):
    cx, cy = 96, 112
    radii = [88, 70, 52, 38, 26]
    for k, fx in enumerate(fs):
        rng = random.Random(260 + k)
        r = radii[k]
        # 끌리는 흙 자국(바깥 → 고리)
        for j in range(12):
            a = math.radians(j * 30 + 15)
            r0, r1 = r + 6, min(94, r + 30 + 6 * k)
            for q in range(int(r0), int(r1)):
                if (q + j) % 4 != 3:
                    fx.put(cx + math.cos(a) * q, cy + math.sin(a) * q * 0.5, B[3] if q < r0 + 10 else B[2])
        gs_ring(fx, cx, cy, r, r * 0.5, [5, 5.5, 5, 4, 3][k], age=k * 0.12, vfun=lambda a, k=k: 0.7 + 0.3 * math.cos(math.radians(a * 4 + k * 40)))
        for j in range(8):
            a = math.radians(j * 45 + k * 10)
            x, y = cx + math.cos(a) * (r + 12), cy + math.sin(a) * (r + 12) * 0.5
            inward_chevron(fx, x, y, a + math.pi, 7, A[25] if k < 3 else A[21], A[19])
        for j in range(6):
            a = rng.uniform(0, 2 * math.pi)
            rr = r * rng.uniform(0.3, 0.8)
            puff(fx, cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.5 - 2, rng.uniform(2.5, 4.5) * (0.6 + 0.1 * k), DUST_BROWN)


# ------------------------------------------------------------------ 5 어깨 너머
@sheet("trait_greatsword_g_shoulderFlip_launch", (128, 128), [40, 50, 60, 70, 90],
       anchor="mob_feet", pivot=(64, 120), glow=[1], part="launch", trait="g_shoulderFlip", replaces="dash_dust",
       depth="above", flipX="allowed",
       flipXNote="그림 = 오른쪽(주인공 쪽)에서 들어 올려 왼쪽(등 뒤)으로 넘김. 주인공이 적의 왼쪽에 있으면 flipX",
       design="어깨로 들어 넘기는 큰 반원 붓획(오른쪽 아래 → 머리 위 → 왼쪽 아래, f1 머리 백열) + 들린 자리 발밑 그림자·흙먼지 + 넘어가는 쪽 속도 호 2")
def g_shoulderFlip_launch(fs):
    px, py = 64, 120
    arc = arc_pts(64, 104, 48, 82, 10, -190, 60)
    for k, fx in enumerate(fs):
        rng = random.Random(270 + k)
        ground_shadow(fx, px + 20 - 10 * k, py, 16, 5)
        n = len(arc)
        upto = [0.4, 0.85, 1.0, 1.0, 1.0][k]
        gs_band(fx, arc[: max(2, int(n * upto))], [4.5, 6, 5, 3.5, 2.2][k], age=[0, 0, 0.3, 0.6, 0.8][k], hot=(k == 1))
        if k in (1, 2):
            for off in (8, 15):
                pts = arc_pts(64, 104, 48 + off, 82 + off, -60, -150, 16)
                for i, (x, y) in enumerate(densify(pts)):
                    if (i // 4) % 2 == 0:
                        fx.put(x, y, A[21] if off == 8 else A[19])
        if k == 1:
            x, y = arc[int(n * upto) - 1]
            star4(fx, x, y, 7, hot=True)
        for j in range(4):
            puff(fx, px + 20 + rng.uniform(-14, 10), py - 4 - rng.uniform(0, 8) - 3 * k, rng.uniform(3, 5.5) * (1 - 0.15 * k), DUST_BROWN)
        if k >= 3:
            for j in range(5):
                puff(fx, 18 + rng.uniform(-8, 8), py - 6 - rng.uniform(0, 10), rng.uniform(3, 5), DUST_BROWN)


@sheet("trait_greatsword_g_shoulderFlip_land", (128, 64), [40, 50, 60, 80, 100, 140],
       anchor="floor", pivot=(64, 40), glow=[0], part="land", trait="g_shoulderFlip", replaces="crush", depth="below",
       light=dict(color=WHITE_LIGHT, radius=48, intensity=0.85, ms=100, atFrame=0),
       design="등 뒤 바닥 메침 = 무거운 착지: 큰 흙먼지 고리(14 덩이) + 호박 금 7갈래 + f0 백열 충격 고리·별")
def g_shoulderFlip_land(fs):
    for k, fx in enumerate(fs):
        land_ring(fx, k, len(fs), 64, 40, "greatsword", seed=280, heavy=True, hot=(k == 0))


@sheet("trait_greatsword_g_shoulderFlip_impact", (160, 160), [40, 40, 50, 60, 70, 90, 120],
       anchor="contact", pivot=(108, 80), rotate=True, flipY="allowed", glow=[0], part="impact", trait="g_shoulderFlip",
       replaces="hit_burst", depth="above", light=dict(color=WHITE_LIGHT, radius=64, intensity=1.0, ms=140, atFrame=0),
       design="메친 적이 벽에 박힘 — 날려 보내기 impact 와 같은 벽 말투(다른 금 무늬·파편)")
def g_shoulderFlip_impact(fs):
    for k, fx in enumerate(fs):
        wall_impact(fx, k, len(fs), 108, 80, "greatsword", seed=290, scale=1.15, hot=(k == 0))


# ------------------------------------------------------------------ 6 들이받기
@sheet("trait_greatsword_g_ramWall_impact", (160, 160), [40, 40, 50, 60, 70, 90, 120],
       anchor="contact", pivot=(110, 80), rotate=True, flipY="allowed", glow=[0], part="impact", trait="g_ramWall",
       replaces="hit_burst·crush", depth="above", light=dict(color=WHITE_LIGHT, radius=64, intensity=1.0, ms=140, atFrame=0),
       design="밀고 간 적이 처박힘(가장 큰 충돌): 벽면 굵은 호박 금 + 함몰 + 뒤로 남은 바닥 긁힌 자국 2줄(밀고 온 길, 들이받기 표지) + 파편·흙먼지·불티")
def g_ramWall_impact(fs):
    for k, fx in enumerate(fs):
        wall_impact(fx, k, len(fs), 110, 80, "greatsword", seed=300, scale=1.3, hot=(k == 0), scrape=True)


# ------------------------------------------------------------------ 7 끓는 쇠
@sheet("trait_greatsword_g_boilingSteel_soak", (128, 128), [40, 50, 60, 70, 90],
       anchor="player_pivot", pivot=(64, 112), glow=[], part="soak", trait="g_boilingSteel",
       replaces="greatsword_charge_ring", depth="above",
       design="술이 칼날로 빨려 드는 소용돌이: 바깥에서 감겨 드는 술 줄기 4(pool_liquor 짙은 호박·갈색, 반짝 점) + 가운데 달아오르는 호박 심 + 오르는 김(재 점)",
       anchorNote="pivot = 주인공 발. 소용돌이 중심 = 발 위 40(대검 날 높이)")
def g_boilingSteel_soak(fs):
    cx, cy = 64, 72
    for k, fx in enumerate(fs):
        rng = random.Random(310 + k)
        f = Field(fx.w, fx.h)
        for j in range(4):
            pts = []
            for i in range(36):
                t = i / 35
                a = math.radians(j * 90 + k * 40 + t * 200)
                r = lerp(58, 6, t ** 0.9) * (1.0 - 0.12 * k) + 4
                pts.append((cx + r * math.cos(a), cy + r * 0.7 * math.sin(a)))
            st = min(0.85, 0.12 * k)
            pts = pts[int(len(pts) * st):]
            f.path(pts, lambda t: 0.8 + 3.6 * math.sin(math.pi * t ** 0.8), lambda t: 0.45 + 0.55 * t)
        f.paint(fx, [(0.82, A[23]), (0.62, A[19]), (0.4, A[18]), (0.16, A[17])], dither=0.12)
        hr = 4 + 2.5 * k
        g = Field(fx.w, fx.h)
        g.blob(cx, cy, hr, hr * 0.8, 1.0)
        g.paint(fx, [(0.7, A[25]), (0.4, A[23]), (0.1, A[21])])
        for j in range(5 + k):
            fx.put(cx + rng.uniform(-14, 14), cy - 10 - rng.uniform(0, 26) - 3 * k, S[2] if j % 2 else S[3])
        for j in range(8):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(20, 56)
            fx.put(cx + math.cos(a) * r, cy + math.sin(a) * r * 0.7, A[19] if j % 2 else A[23])


@sheet("trait_greatsword_g_boilingSteel_fire", (64, 96), [60, 60, 60, 60, 60, 60],
       anchor="floor", pivot=(32, 84), glow=[], part="fire", trait="g_boilingSteel", replaces="fire_pool",
       depth="above", loopRange=[1, 4], endFrames=[5, 5],
       light=dict(color=ORANGE, radius=48, intensity=0.85, flicker=dict(amp=0.25, hz=9)),
       lifeRule="f0 솟음 → f1~f4 루프(불길 수명, 시스템 durationMs — 균열 한 칸마다 하나) → f5 꺼짐",
       design="균열 한 칸에서 솟는 불기둥: 바닥 호박 금 한 줄 + pool_liquor_fire 계열 큰 혓바닥 2~3(최대 64 도트) + 작은 혓바닥·불티 · 칸마다 높이·기울기 출렁")
def g_boilingSteel_fire(fs):
    cx, cy = 32, 84
    tree = crack_tree(4, cy, 0.0, 56, random.Random(320), depth=1, jitter=0.3, step=2.5)
    for k, fx in enumerate(fs):
        rng = random.Random(321 + (k if k in (0, 5) else (k - 1) % 4 + 1))
        draw_cracks(fx, tree, A[23] if k < 5 else A[19], B[0], sy=0.6, cx=cx, cy=cy)
        f = Field(fx.w, fx.h)
        f.blob(cx, cy, 22, 5, 1.0)
        f.paint(fx, [(0.5, A[19]), (0.2, A[18])], dither=0.4, only_empty=True)
        s = [0.45, 1.0, 1.0, 1.0, 1.0, 0.35][k]
        ph = (k - 1) * math.pi / 2
        hs = [58 + 8 * math.sin(ph), 44 + 8 * math.cos(ph), 36 + 6 * math.sin(ph + 1)]
        xs = [cx, cx - 11, cx + 11]
        for j in range(3):
            flame(fx, xs[j] + rng.uniform(-1, 1), cy - 2, hs[j] * s, [11, 8, 8][j] * (0.7 + 0.3 * s), lean=rng.uniform(-6, 6))
        for j in range(4):
            flame(fx, cx + rng.uniform(-20, 20), cy, rng.uniform(8, 16) * s, 4, lean=rng.uniform(-4, 4))
        for j in range(5):
            fx.put(cx + rng.uniform(-16, 16), cy - rng.uniform(40, 78) * s, A[23] if j % 2 else A[21])


# ------------------------------------------------------------------ 8 빨아들이는 균열
@sheet("trait_greatsword_g_crackPull", (96, 48), [40, 50, 60, 80],
       anchor="mob_feet", pivot=(78, 26), rotate=True, flipY="allowed", glow=[], part="", trait="g_crackPull",
       replaces="윤곽 선", depth="below",
       design="적 발밑에서 균열 쪽(오른쪽)으로 끌리는 흙 자국: 바닥을 긁은 홈 2줄(짙은 홈 + 밝은 윗입술) + 발 앞에 밀린 흙 둔덕 + 끌린 방향 갈매기표 · 튀는 흙",
       anchorNote="pivot = 끌려간 적 발. 오른쪽 = 균열 방향(끌린 쪽)")
def g_crackPull(fs):
    px, py = 78, 26
    for k, fx in enumerate(fs):
        rng = random.Random(330 + k)
        L = [26, 52, 68, 68][k]
        for dy in (-5, 5):
            for x in range(px - 4 - L, px - 4):
                t = (x - (px - 4 - L)) / max(1, L)
                yy = py + dy + int(round(math.sin(x * 0.25) * 0.6))
                fx.put(x, yy + 1, B[0])
                fx.put(x, yy, [B[1], B[1], B[0], B[0]][k] if t < 0.3 else B[1])
                fx.put(x, yy - 1, [S[2], S[2], B[3], B[2]][k] if (x + k) % 5 else S[3])
        for j in range(3):
            puff(fx, px + 2 + rng.uniform(-3, 3), py + (j - 1) * 7, rng.uniform(3, 4.5) * (1 - 0.15 * k), DUST_BROWN)
        if k <= 2:
            for j in range(2):
                inward_chevron(fx, px - 24 - j * 18 + 6 * k, py, 0.0, 6, A[23] if k < 2 else A[21], A[19])
        for j in range(5):
            fx.put(px - rng.uniform(0, L), py + rng.uniform(-12, 12), B[3])


# ------------------------------------------------------------------ 9 갈라진 길
@sheet("trait_greatsword_splitRoad", (64, 64), [30, 40, 50, 70],
       anchor="projectile", pivot=(32, 46), glow=[0], part="", trait="splitRoad",
       replaces="katana_whirl_reflect·hit_spark", depth="above",
       design="균열에서 튀어 오른 돌 쐐기(세로로 솟는 돌 + 아래 호박 금)가 탄을 되받아치는 섬광(f0 백열 별) → 돌이 부서져 조각·흙먼지",
       anchorNote="pivot = 되받아친 탄 자리(바닥 금 위). 회전 없음")
def g_splitRoad(fs):
    px, py = 32, 46
    for k, fx in enumerate(fs):
        rng = random.Random(340 + k)
        draw_cracks(fx, crack_tree(px - 22, py + 4, 0.0, 44, random.Random(341), depth=1, jitter=0.35), [A[25], A[23], A[21], A[19]][k], B[0], sy=0.6, cx=px, cy=py + 4)
        h = [20, 28, 22, 0][k]
        if h:
            poly = [(px - 5, py + 4), (px - 3, py + 4 - h * 0.6), (px + 1, py + 4 - h), (px + 5, py + 4 - h * 0.5), (px + 6, py + 4)]
            from kit import fill_poly
            fill_poly(fx, poly, S[1])
            fx.line(px - 3, py + 4 - h * 0.6, px + 1, py + 4 - h, S[3])
            fx.line(px + 1, py + 4 - h, px + 5, py + 4 - h * 0.5, S[2])
            fx.line(px + 5, py + 4 - h * 0.5, px + 6, py + 4, B[0])
            fx.line(px - 5, py + 4, px - 3, py + 4 - h * 0.6, S[0])
        if k == 0:
            star4(fx, px + 1, py + 2 - h, 8, hot=True)
            star4(fx, px + 1, py + 2 - h, 4, hot=True, diag=True)
        elif k == 1:
            for j in range(6):
                a = math.radians(-90 + (j - 2.5) * 30)
                fx.line(px + 1 + math.cos(a) * 6, py - 24 + math.sin(a) * 6, px + 1 + math.cos(a) * 14, py - 24 + math.sin(a) * 14, A[25] if j % 2 else A[23])
        if k >= 2:
            for j in range(6):
                chunk(fx, px + rng.uniform(-10, 10), py - rng.uniform(0, 18) + 4 * k, rng.uniform(1.6, 2.8), rng.uniform(0, 6), rng)
            for j in range(3):
                puff(fx, px + rng.uniform(-10, 10), py + rng.uniform(-6, 2), rng.uniform(3, 4.5), DUST_BROWN)


# ------------------------------------------------------------------ 10 띄워 올리기
@sheet("trait_greatsword_g_leapToss_launch", (96, 128), [40, 50, 60, 70, 90],
       anchor="mob_feet", pivot=(48, 116), glow=[], part="launch", trait="g_leapToss", replaces="dash_dust", depth="above",
       design="띄움 = 착지 충격에 솟는 흙기둥: 발밑에서 바닥 판이 뾰족 쐐기 4개로 솟아오름(돌 면 밝은 윗테) + 그 사이로 솟구치는 갈색 먼지 기둥 + 체커 그림자 → 쐐기가 무너져 조각")
def g_leapToss_launch(fs):
    px, py = 48, 116
    spikes = [(-14, 0.7, -0.25), (-4, 1.0, -0.08), (7, 0.85, 0.12), (16, 0.55, 0.3)]
    from kit import fill_poly
    for k, fx in enumerate(fs):
        rng = random.Random(350 + k)
        launch_column(fx, k, len(fs), px, py, "greatsword", seed=351)
        hmul = [0.55, 1.0, 0.95, 0.5, 0.0][k]
        for dx, hh, lean in spikes:
            H = 40 * hh * hmul
            if H < 3:
                continue
            bx = px + dx
            tip = (bx + lean * H, py - H)
            poly = [(bx - 5, py + 2), tip, (bx + 5, py + 2)]
            fill_poly(fx, poly, B[2])
            fx.line(bx - 5, py + 2, tip[0], tip[1], S[3])
            fx.line(tip[0], tip[1], bx + 5, py + 2, B[1])
            fx.line(bx, py, tip[0] * 0.5 + bx * 0.5, (py + tip[1]) / 2, A[21] if k <= 1 else B[3])
        if k >= 3:
            for j in range(8):
                chunk(fx, px + rng.uniform(-20, 20), py - rng.uniform(4, 34) + 8 * (k - 3), rng.uniform(1.8, 3.2), rng.uniform(0, 6), rng)


@sheet("trait_greatsword_g_leapToss_land", (128, 64), [40, 50, 60, 80, 100, 140],
       anchor="floor", pivot=(64, 40), glow=[], part="land", trait="g_leapToss", replaces="crush", depth="below",
       design="떨어진 적의 착지 먼지 — 갈색 흙먼지 고리 + 호박 금(땅울림 착지와 금 무늬만 다름)")
def g_leapToss_land(fs):
    for k, fx in enumerate(fs):
        land_ring(fx, k, len(fs), 64, 40, "greatsword", seed=360)


# ------------------------------------------------------------------ 11 짓눌린 숨
@sheet("trait_greatsword_g_crushedBreath", (192, 192), [40, 50, 60, 70, 80, 100],
       anchor="floor", pivot=(96, 100), glow=[5], part="", trait="g_crushedBreath", replaces="윤곽",
       depth="below",
       design="끌어모으는 눌린 고리: 납작하게 눌린 굵은 대검 붓 고리가 한가운데로 조여듦(반지름 88 → 14) + 고리 위 짓누르는 세로 눌림표 '‖' 12 + 안으로 끌리는 먼지 → f5 가운데 짧은 백열 쿵",
       anchorNote="pivot = 진동 한가운데(바닥)")
def g_crushedBreath(fs):
    cx, cy = 96, 100
    radii = [88, 70, 50, 32, 20, 14]
    for k, fx in enumerate(fs):
        rng = random.Random(370 + k)
        r = radii[k]
        gs_ring(fx, cx, cy, r, r * 0.38, [6, 6.5, 6, 5, 4, 3][k], age=0.12 + 0.05 * k, hot=False,
                vfun=lambda a, k=k: 0.62 + 0.38 * (0.5 + 0.5 * math.sin(math.radians(a * 3 + k * 50))) ** 0.6)
        # 바깥 잔상 고리(가는 점선)
        if k >= 1:
            pr = radii[k - 1]
            pts = densify(arc_pts(cx, cy, pr, pr * 0.38, 0, 360, 80))
            for i, (x, y) in enumerate(pts):
                if (i // 3) % 3 == 0:
                    fx.put_if_empty(x, y, B[3])
        for j in range(12):
            if r < 24 and j % 2:
                continue
            a = math.radians(j * 30 + 15)
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.38
            for dx in (-2, 2):
                fx.line(x + dx, y - 8, x + dx, y - 3, A[25] if k < 4 else A[23])
                fx.put(x + dx, y - 9, A[21])
        for j in range(8):
            a = rng.uniform(0, 2 * math.pi)
            rr = r + rng.uniform(4, 20)
            puff(fx, cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.38 - 2, rng.uniform(2.5, 4.5), DUST_BROWN)
        if k == 5:
            star4(fx, cx, cy - 4, 10, hot=True)
            star4(fx, cx, cy - 4, 6, hot=True, diag=True)


@sheet("trait_greatsword_g_crushedBreath_impact", (128, 128), [40, 40, 50, 60, 80, 110],
       anchor="contact", pivot=(64, 64), rotate=True, flipY="allowed", glow=[0], part="impact", trait="g_crushedBreath",
       replaces="hit_burst", depth="above",
       design="모인 적끼리 부딪는 충돌: 두 적 사이 세로 면에 눌린 호박 섬광(양쪽으로 광선) + 면 금 + 양쪽으로 튀는 파편·흙먼지(벽 처박힘의 양면판)",
       anchorNote="pivot = 두 적 사이. 오른쪽·왼쪽 = 부딪친 두 적(대칭이라 회전은 부딪친 축만 맞추면 됨)")
def g_crushedBreath_impact(fs):
    for k, fx in enumerate(fs):
        wall_impact(fx, k, len(fs), 64, 64, "greatsword", seed=380, scale=0.95, hot=(k == 0), twin=True)


# ------------------------------------------------------------------ 12 술독 짓누르기
@sheet("trait_greatsword_jarCrush_burst", (192, 192), [40, 40, 50, 60, 70, 90, 120],
       anchor="floor", pivot=(96, 140), glow=[0, 1], part="burst", trait="jarCrush", replaces="fire_bottle_burst",
       depth="above", light=dict(color=ORANGE, radius=96, intensity=1.2, ms=300, atFrame=0, flicker=dict(amp=0.25, hz=8)),
       design="모인 술이 불붙어 터지는 술독 폭발: f0 백열 원반·바닥 충격 고리 → 불덩이(pool_liquor_fire 호박 램프, 바깥 혓바닥) + 사방으로 튀는 술독 조각(갈색 곡면 사금파리) + 술방울 → 바닥 불길 고리 · 재 연기 기둥 → 불티",
       anchorNote="pivot = 모인 술 웅덩이 중심(바닥). 반경 2칸(=128 도트) — 그림 불덩이 반경 ≈ 80")
def g_jarCrush_burst(fs):
    cx, cy = 96, 140
    for k, fx in enumerate(fs):
        rng = random.Random(390 + k)
        # 바닥 불길 고리(2칸부터)
        if k >= 2:
            rr = [0, 0, 56, 72, 80, 82, 84][k]
            for j in range(18):
                a = math.radians(j * 20 + rng.uniform(-6, 6))
                x, y = cx + math.cos(a) * rr * rng.uniform(0.85, 1.05), cy + math.sin(a) * rr * 0.4
                h = rng.uniform(8, 18) * [1, 1, 1.0, 1.0, 0.8, 0.55, 0.3][k]
                flame(fx, x, y, h, rng.uniform(3.5, 5.5), lean=rng.uniform(-5, 5))
        # 연기
        if k >= 3:
            for j in range(9):
                yy = cy - 30 - j * 9 - 6 * (k - 3)
                puff(fx, cx + rng.uniform(-22, 22) * (1 + 0.1 * j), yy, rng.uniform(5, 9) * (1 - 0.08 * (k - 3)), DUST_ASH)
        # 불덩이
        if k <= 4:
            R = [26, 46, 60, 56, 40][k]
            f = Field(fx.w, fx.h)
            f.blob(cx, cy - R * 0.55, R, R * 0.8, 1.0)
            for j in range(12):
                a = math.radians(j * 30 + rng.uniform(-10, 10))
                f.capsule(cx + math.cos(a) * R * 0.6, cy - R * 0.55 + math.sin(a) * R * 0.5, cx + math.cos(a) * R * 1.15,
                          cy - R * 0.55 + math.sin(a) * R * 0.9 - 6, R * 0.25, 1.0, 0.7, 0.3)
            if k == 0:
                ramp = [(0.75, X0), (0.55, X1), (0.35, A[25]), (0.15, A[23]), (0.03, A[21])]
            elif k == 1:
                ramp = [(0.8, X1), (0.6, A[25]), (0.42, A[23]), (0.24, A[21]), (0.08, A[19])]
            else:
                ramp = [(0.75, A[25]), (0.55, A[23]), (0.35, A[21]), (0.18, A[19]), (0.05, A[18])]
                if k == 4:
                    ramp = [(0.7, A[23]), (0.45, A[21]), (0.25, A[19]), (0.08, A[18])]
            f.paint(fx, ramp, dither=0.25)
        if k <= 1:
            gs_ring(fx, cx, cy, 40 + 30 * k, (40 + 30 * k) * 0.38, 3.5, hot=(k == 0))
        # 술독 조각(사금파리)
        rr0 = random.Random(395)
        for j in range(14):
            a = rr0.uniform(math.pi * 0.95, math.pi * 2.05)
            sp = rr0.uniform(40, 90)
            d = sp * smooth(min(1, (k + 0.5) / 5))
            x = cx + math.cos(a) * d
            y = cy - 30 + math.sin(a) * d * 0.8 + 10 * k * k * 0.25 * rr0.uniform(0.5, 1)
            if k == 0:
                continue
            ang = rr0.uniform(0, 6)
            arc = arc_pts(x, y, 4, 3, math.degrees(ang), math.degrees(ang) + 120, 5)
            for i, (qx, qy) in enumerate(densify(arc)):
                fx.put(qx, qy, B[3] if i < 3 else A[19])
                fx.put(qx, qy + 1, B[1])
        # 술방울
        for j in range(16 if k <= 3 else 6):
            a = rng.uniform(math.pi, 2 * math.pi)
            d = rng.uniform(30, 92) * min(1, (k + 1) / 4)
            fx.put(cx + math.cos(a) * d, cy - 20 + math.sin(a) * d * 0.8 + 3 * k * k, A[23] if j % 2 else A[21])


# ------------------------------------------------------------------ 13 포효
@sheet("trait_greatsword_g_rageRoar", (256, 256), [40, 50, 60, 70, 90, 110],
       anchor="player_pivot", pivot=(128, 178), glow=[], part="", trait="g_rageRoar", replaces="guard_wave",
       depth="above", light=dict(color="#d65457", radius=96, intensity=1.0, ms=200, atFrame=0),
       design="폭주 포효 음파: 머리 높이에서 퍼지는 톱니(지그재그) 고리 3겹 — 붉은 적갈 램프(#b04848) 마른 붓 + 바깥 테 호박 · 입에서 뻗는 짧은 함성 획 8 → 고리가 커지며 끊김",
       anchorNote="pivot = 주인공 발. 음파 중심 = 머리(발 위 58 도트)")
def g_rageRoar(fs):
    cx, cy = 128, 120
    CR = [(0.84, CRIM[5]), (0.62, CRIM[4]), (0.42, CRIM[3]), (0.22, CRIM[2])]
    for k, fx in enumerate(fs):
        rng = random.Random(400 + k)
        for j in range(3):
            r = 24 + k * 20 - j * 26
            if r < 14 or (k >= 4 and j == 2):
                continue
            age = clamp(k / 5.0 + j * 0.1)
            f = Field(fx.w, fx.h)
            zig = lambda a, r=r: 1.0 + 0.0 * a
            # 톱니: 각도마다 반지름 흔들기 → 점 목록으로 path
            pts = []
            for i in range(121):
                a = math.radians(i * 3)
                rr = r * (1 + 0.07 * (1 if (i // 2) % 2 else -1))
                pts.append((cx + rr * math.cos(a), cy + rr * 0.72 * math.sin(a)))
            f.path(pts, lambda t: (3.4 - 1.6 * age) * (0.7 + 0.3 * math.sin(t * 40)), lambda t: 1.0 - 0.6 * age)
            if k >= 3:
                for i in range(len(f.v)):
                    if f.v[i] and ((i % 256) // 9 + (i // 256) // 9 + j) % 4 == 0:
                        f.v[i] = 0
            f.paint(fx, CR, dither=0.3)
            if j == 0 and k <= 3:
                pts2 = densify(pts)
                for i, (x, y) in enumerate(pts2):
                    if (i // 5) % 2 == 0:
                        dx, dy = x - cx, y - cy
                        L = math.hypot(dx, dy) or 1
                        fx.put_if_empty(x + dx / L * 4, y + dy / L * 4, A[23] if k < 2 else A[21])
        if k <= 2:
            for j in range(8):
                a = math.radians(j * 45 + 22)
                r0, r1 = 10 + 6 * k, 22 + 10 * k
                gs = [(cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.72), (cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 0.72)]
                for q in densify(gs):
                    fx.put(q[0], q[1], CRIM[5] if k == 0 else CRIM[4])
        for j in range(10):
            a = rng.uniform(0, 2 * math.pi)
            rr = 30 + 20 * k + rng.uniform(-6, 10)
            fx.put(cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.72, A[21] if j % 2 else CRIM[3])


@sheet("trait_greatsword_g_rageRoar_impact", (128, 128), [40, 40, 50, 60, 80, 110],
       anchor="contact", pivot=(88, 64), rotate=True, flipY="allowed", glow=[0], part="impact", trait="g_rageRoar",
       replaces="hit_burst", depth="above",
       design="포효에 밀려난 적 충돌 — 벽 처박힘 말투(작게) + 적갈 불씨 점(포효 표지)")
def g_rageRoar_impact(fs):
    for k, fx in enumerate(fs):
        wall_impact(fx, k, len(fs), 88, 64, "greatsword", seed=410, scale=0.9, hot=(k == 0), accent=[CRIM[4], CRIM[5], CRIM[3]])


# ------------------------------------------------------------------ 14 술기운 폭주
@sheet("trait_greatsword_g_rageFire", (96, 64), [40, 50, 60, 80, 100],
       anchor="floor", pivot=(48, 44), glow=[0], part="", trait="g_rageFire", replaces="점 윤곽",
       depth="above", light=dict(color=ORANGE, radius=48, intensity=0.85, ms=400, atFrame=0),
       design="발밑 술에 불이 옮겨 붙는 순간: 술 웅덩이(짙은 호박 납작 타원) 가운데 불똥(f0) → 바깥으로 번지며 솟는 혓바닥 3 → 6 → 낮아지며 불티",
       anchorNote="pivot = 밟은 술 웅덩이 중심(주인공 발)")
def g_rageFire(fs):
    cx, cy = 48, 44
    for k, fx in enumerate(fs):
        rng = random.Random(420 + k)
        f = Field(fx.w, fx.h)
        f.blob(cx, cy, 34, 10, 1.0)
        f.paint(fx, [(0.55, A[18]), (0.25, A[17]), (0.03, A[16])], dither=0.35)
        for j in range(6):
            fx.put(cx + rng.uniform(-26, 26), cy + rng.uniform(-6, 6), A[19])
        if k == 0:
            star4(fx, cx, cy - 3, 6, hot=False, col=A[26])
            flame(fx, cx, cy, 10, 5)
        else:
            nflames = [0, 3, 6, 6, 4][k]
            spread = [0, 10, 22, 28, 30][k]
            hmul = [0, 1.0, 1.3, 0.9, 0.5][k]
            for j in range(nflames):
                x = cx + (j - (nflames - 1) / 2) * (2 * spread / max(1, nflames - 1)) + rng.uniform(-2, 2)
                h = (24 - abs(x - cx) * 0.4) * hmul * rng.uniform(0.8, 1.1)
                flame(fx, x, cy + rng.uniform(-2, 2), h, rng.uniform(5, 7), lean=rng.uniform(-5, 5))
        for j in range(3 + k):
            fx.put(cx + rng.uniform(-24, 24), cy - rng.uniform(14, 34), A[23] if j % 2 else A[21])


# ------------------------------------------------------------------ 공명
@sheet("trait_res_greatsword_weight", (192, 192), [40, 50, 60, 70, 90, 120],
       anchor="floor", pivot=(96, 100), glow=[0], part="", trait=None, resonance="res_greatsword_weight",
       replaces="greatsword_quake_fork·crush", depth="below",
       design="공명 무너뜨림 — 처박힌 자리 바닥이 갈라짐: 사방 굵은 호박 금 8갈래(바닥 납작) + 둘레 고리를 따라 튀어 오르는 바닥 판 조각 10(띄움 — 아래 체커 그림자) + 흙먼지 고리 → 금이 재로 식음",
       anchorNote="pivot = 처박힌 자리(contact 를 바닥 깊이로)")
def res_greatsword_weight(fs):
    cx, cy = 96, 100
    rng0 = random.Random(430)
    trees = [crack_tree(cx, cy, j * math.pi / 4 + rng0.uniform(-0.2, 0.2), rng0.uniform(60, 86), random.Random(431 + j), depth=2, jitter=0.3, step=2.6) for j in range(8)]
    for k, fx in enumerate(fs):
        rng = random.Random(440 + k)
        for tr in trees:
            draw_cracks(fx, tr, [A[25], A[25], A[23], A[21], A[19], B[3]][k], B[0], sy=0.45, cx=cx, cy=cy, grow=min(1, 0.35 + 0.3 * k), thick=True)
        R = [30, 46, 58, 62, 64, 64][k]
        lift = [0, 10, 16, 12, 5, 0][k]
        rr0 = random.Random(445)
        for j in range(10):
            a = j * 2 * math.pi / 10 + rr0.uniform(-0.15, 0.15)
            x, y = cx + math.cos(a) * R, cy + math.sin(a) * R * 0.45
            sz = rr0.uniform(4.5, 7.0)
            if lift:
                ground_shadow(fx, x, y + 2, sz + 1, 2, B[0])
            if k < 5:
                chunk(fx, x, y - lift * rr0.uniform(0.7, 1.2), sz * (1 - 0.1 * k), rr0.uniform(0, 6), rr0, [B[0], B[2], S[2], S[3]])
        if k >= 1:
            for j in range(12):
                a = rng.uniform(0, 2 * math.pi)
                rr = R * rng.uniform(0.9, 1.2)
                puff(fx, cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.45 - 3, rng.uniform(3, 5.5) * (1 - 0.12 * k), DUST_BROWN)
        if k == 0:
            star4(fx, cx, cy - 2, 9, hot=True)


@sheet("trait_res_greatsword_insight", (256, 256), [30, 40, 50, 70, 90],
       anchor="player_pivot", pivot=(128, 168), glow=[0], part="", trait=None, resonance="res_greatsword_insight",
       replaces="guard_perfect_fx·guard_wave", depth="above", light=dict(color=WHITE_LIGHT, radius=96, intensity=1.0, ms=100, atFrame=0),
       design="공명 막고 되치는 대검 — 주인공 둘레 360° 튕겨 내기 고리: 대검 면 모양 눌린 판 섬광 12(고리에 접선, f0 백열 심) + 판마다 바깥으로 뻗는 뭉툭한 되침 광선 + 마른 붓 고리 → 바깥으로 퍼지며 끊김",
       anchorNote="pivot = 주인공 발. 고리 중심 = 발 위 40 도트(128)")
def res_greatsword_insight(fs):
    cx, cy = 128, 128
    radii = [40, 64, 84, 100, 110]
    for k, fx in enumerate(fs):
        r = radii[k]
        gs_ring(fx, cx, cy, r, r * 0.78, [4, 4.5, 4, 3, 2][k], age=k * 0.18, hot=(k == 0),
                vfun=lambda a: 0.75 + 0.25 * math.cos(math.radians(a * 12)))
        for j in range(12):
            a = math.radians(j * 30)
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.78
            tx, ty = -math.sin(a), math.cos(a) * 0.78
            L = [7, 9, 8, 6, 4][k]
            f = Field(fx.w, fx.h)
            f.capsule(x - tx * L, y - ty * L, x + tx * L, y + ty * L, [3, 3, 2.4, 1.8, 1.2][k], [3, 3, 2.4, 1.8, 1.2][k], 1.0 - 0.15 * k, 1.0 - 0.15 * k)
            ramp = ([(0.9, X1)] if k == 0 else []) + GS_RAMP
            f.paint(fx, ramp, dither=0.15)
            if k <= 3:
                o0, o1 = 6 + 2 * k, 14 + 5 * k
                ox, oy = math.cos(a), math.sin(a) * 0.78
                gs_band(fx, [(x + ox * o0, y + oy * o0), (x + ox * o1, y + oy * o1)], [2.2, 2.2, 1.8, 1.2][k], age=0.2 * k, dither=0.2)
        if k <= 2:
            embers(fx, cx, cy, 10, r, random.Random(450 + k))
