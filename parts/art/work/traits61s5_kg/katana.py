"""칼(katana) 개성 fx 14 + 공명 3 — 25 시트. 언어 = '은선'(가는 은빛 틈 · 머리만 밝고 뾰족 · 안쪽 끊긴 잔상 · 마디 소멸 · 호박 불티 점).
개성 갈래 모양은 shapes.py(띄움 기둥·착지 고리·벽면 금·묶음 고리·불·분신)."""
import math
import random

from kit import (A, BIND, CRIM, FIRE, G, LIQ, MOON, S, SL, X0, X1, DUST_ASH, Field, Fx, arc_pts, chunk, clamp, crack_tree,
                 densify, draw_cracks, draw_sil, embers, flame, ground_shadow, hero_mask, lerp, normals, puff, slit,
                 slit_decay, smooth, star4)
from shapes import (INK_RAMP, MOON_RAMP, SILVER_RAMP, ink_field, land_ring, launch_column, lens_arc, wall_impact)

SHEETS = {}


def sheet(name, size, ms, **kw):
    def deco(fn):
        SHEETS[name] = dict(fn=fn, size=size, ms=ms, **kw)
        return fn
    return deco


def frames(size, n):
    return [Fx(size[0], size[1]) for _ in range(n)]


# ------------------------------------------------------------------ 1 그림자 찌르기
def ink_wedge(fx, x0, y0, L, h, holes=0.0, seed=0):
    """먹 그림자 쐐기(앞으로 찌르는 낮은 분신) — 오른쪽이 뾰족."""
    f = Field(fx.w, fx.h)
    f.capsule(x0, y0, x0 + L, y0 - 1, h, 1.0, 1.0, 0.9, flat=0.5)
    f.capsule(x0 + L * 0.15, y0 - h * 0.7, x0 + L * 0.55, y0 - 2, h * 0.45, 1.0, 0.8, 0.7)   # 웅크린 등
    if holes:
        rng = random.Random(seed)
        for i in range(len(f.v)):
            if f.v[i] > 0 and rng.random() < holes:
                f.v[i] = 0
    ink_field(fx, f)
    # 몸을 가르는 속도 머리카락
    for dy in (-2, 2):
        fx.line(x0 + 4, y0 + dy, x0 + L * 0.8, y0 + dy - 1, SL[4], every=lambda q: q % 5 < 3)


@sheet("trait_katana_k_shadowThrust", (256, 64), [40, 40, 50, 60, 80, 100],
       anchor="contact", pivot=(14, 34), rotate=True, glow=[1], part="", trait="k_shadowThrust",
       replaces="afterimage + 윤곽 선", depth="above",
       design="먹 그림자 분신 쐐기(은빛 윗테)가 왼끝에서 웅크렸다 앞으로 찌름 → 가는 은선 직선 + 끝 4갈래 섬광(f1 백열) → 마디로 끊겨 엇갈림 + 먹 방울",
       anchorNote="pivot(왼끝) = 쓰러진 적 자리. 오른쪽 = 다음 적 방향으로 회전. 선 길이 222 도트(≈3.5칸) — 사거리 3칸이면 시스템이 x 배율로 줄여도 됨(선이 가늘어 늘임/줄임 티 적음)")
def k_shadowThrust(fs):
    px, py = 14, 34
    for k, fx in enumerate(fs):
        rng = random.Random(10 + k)
        if k == 0:
            ink_wedge(fx, 8, py, 30, 9)
            slit(fx, [(40, py - 1), (110, py - 1)], maxw=2, ghost=False)
        elif k == 1:
            ink_wedge(fx, 12, py, 44, 7)
            slit(fx, [(54, py - 1), (234, py - 1)], maxw=3, hot=True, ghost=True)
            star4(fx, 236, py - 1, 9, hot=True)
            star4(fx, 236, py - 1, 4, hot=True, diag=True)
            embers(fx, 236, py, 4, 6, rng)
        elif k == 2:
            ink_wedge(fx, 16, py, 40, 6, holes=0.25, seed=k)
            slit(fx, [(56, py - 1), (234, py - 1)], maxw=2, dim=1, ghost=True, phase=4)
            star4(fx, 236, py - 1, 6, hot=False)
            embers(fx, 232, py, 5, 10, rng)
        else:
            age = (k - 2) / 3.0
            if k < 5:
                ink_wedge(fx, 20 + 4 * k, py, 34 - 6 * k, 5 - k, holes=0.35 + 0.2 * k, seed=k)
            slit_decay(fx, [(56, py - 1), (234, py - 1)], age, seed=k)
            # 먹 방울
            for j in range(10 - 2 * k):
                fx.put(rng.uniform(10, 70), py + rng.uniform(-8, 6) - 3 * k, SL[2] if j % 2 else SL[3])
            if k < 5:
                embers(fx, 232, py, 3, 12, rng, cols=[A[23], A[21], A[19]])


# ------------------------------------------------------------------ 2 칼등 띄우기
@sheet("trait_katana_k_edgeLift_launch", (96, 128), [40, 50, 60, 70, 90],
       anchor="mob_feet", pivot=(48, 116), glow=[1], part="launch", trait="k_edgeLift", replaces="dash_dust",
       depth="above",
       design="띄움 = 발에서 솟구치는 재 먼지 기둥 + 발밑 체커 그림자(뜬 적 그림자, 줄어듦) + 칼등이 아래에서 위로 쳐올리는 은선 호(f1 머리 백열)")
def k_edgeLift_launch(fs):
    px, py = 48, 116
    arc = arc_pts(68, 96, 46, 78, 150, 260)   # 아래 왼쪽 → 위로 쳐올림
    for k, fx in enumerate(fs):
        launch_column(fx, k, len(fs), px, py, "katana", seed=21)
        if k == 0:
            slit(fx, arc[: len(arc) // 2], maxw=3, ghost=False, side=-1)
        elif k == 1:
            slit(fx, arc, maxw=4, hot=True, side=-1)
            x, y = arc[-1]
            star4(fx, x, y, 7, hot=True)
        elif k == 2:
            slit(fx, arc, maxw=3, dim=1, side=-1, phase=3)
        else:
            slit_decay(fx, arc, (k - 2) / 2.5, seed=k, side=-1)


@sheet("trait_katana_k_edgeLift_land", (128, 64), [40, 50, 60, 80, 100, 140],
       anchor="floor", pivot=(64, 40), glow=[0], part="land", trait="k_edgeLift", replaces="crush",
       depth="below", light=dict(color="#ffffff", radius=48, intensity=0.8, ms=100, atFrame=0),
       design="착지 = 납작한 원형 재 먼지 고리 + 바닥 은회 금(5갈래) + f0 가는 충격 고리·작은 별(백열)")
def k_edgeLift_land(fs):
    for k, fx in enumerate(fs):
        land_ring(fx, k, len(fs), 64, 40, "katana", seed=22, hot=(k == 0))


# ------------------------------------------------------------------ 3 흘려 밀기
@sheet("trait_katana_k_parryShove", (192, 192), [40, 50, 60, 80, 100],
       anchor="player_pivot", pivot=(96, 150), glow=[0], part="", trait="k_parryShove", replaces="guard_wave",
       depth="above",
       design="패링 자리(몸 가운데, 발 위 40)에서 둘레로 밀려 나가는 은빛 반달 6장(바깥 가장자리가 밝은 렌즈) + 안쪽 끊긴 잔상 호 · f0 가운데 백열 별",
       anchorNote="pivot = 주인공 발. 반달 중심 = 발 위 40 도트(110)")
def k_parryShove(fs):
    cx, cy = 96, 110
    radii = [26, 46, 62, 74, 82]
    for k, fx in enumerate(fs):
        r = radii[k]
        rot = k * 6
        for j in range(6):
            amid = j * 60 + 30 + rot
            w = [3.0, 4.5, 4.0, 3.0, 2.0][k]
            span = [70, 58, 50, 44, 36][k]
            lens_arc(fx, cx, cy, r, r * 0.72, amid, span, w, hot=(k == 0))
            if k >= 1:
                # 안쪽 잔상(끊긴 1도트 호)
                pts = arc_pts(cx, cy, r - 8, (r - 8) * 0.72, amid - span * 0.35, amid + span * 0.35, 10)
                D = densify(pts)
                for i, (x, y) in enumerate(D):
                    if (i // 4) % 2 == 0:
                        fx.put_if_empty(x, y, SL[6] if k < 3 else SL[5])
        if k == 0:
            star4(fx, cx, cy, 10, hot=True)
            star4(fx, cx, cy, 5, hot=True, diag=True)
        if k >= 3:
            rng = random.Random(30 + k)
            for j in range(14):
                a = rng.uniform(0, 2 * math.pi)
                rr = r + rng.uniform(2, 10)
                fx.put(cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.72, G[9] if j % 3 else A[23])


@sheet("trait_katana_k_parryShove_impact", (128, 128), [40, 50, 60, 70, 90, 120],
       anchor="contact", pivot=(86, 64), rotate=True, flipY="allowed", glow=[0], part="impact", trait="k_parryShove",
       replaces="hit_burst", depth="above", light=dict(color="#ffffff", radius=48, intensity=0.85, ms=120, atFrame=0),
       design="처박힘 = 오른쪽 세로 벽면(pivot)에 눌린 은빛 섬광(f0 백열) + 면을 따라 퍼지는 은회 금 + 뒤로 튀는 돌 파편·재 먼지",
       anchorNote="pivot = 박힌 자리(벽 면·두 적 사이). 그림 오른쪽 = 밀려 간 방향(벽 쪽) — 시스템이 충돌 방향으로 회전")
def k_parryShove_impact(fs):
    for k, fx in enumerate(fs):
        wall_impact(fx, k, len(fs), 86, 64, "katana", seed=31, scale=0.95, hot=(k == 0))


# ------------------------------------------------------------------ 4 칼 감기
@sheet("trait_katana_k_bladeBind", (96, 96), [40, 50, 60, 70, 90],
       anchor="hitbox_center", pivot=(48, 48), glow=[1], part="", trait="k_bladeBind", replaces="katana_counter",
       depth="above",
       design="끌어당김 = 바깥에서 안으로 1.5바퀴 감겨 드는 은선 나선(머리가 가운데로) → f1 가운데서 채는 X 섬광(백열) → 나선이 마디로 풀리며 호박 불티")
def k_bladeBind(fs):
    cx, cy = 48, 48

    def spiral(t0, t1, n=90):
        pts = []
        for i in range(n + 1):
            t = lerp(t0, t1, i / n)
            th = math.radians(200 + t * 540)
            r = 40 * (1 - t) + 4
            pts.append((cx + r * math.cos(th), cy + r * 0.82 * math.sin(th)))
        return pts
    for k, fx in enumerate(fs):
        rng = random.Random(40 + k)
        if k == 0:
            slit(fx, spiral(0.0, 0.5), maxw=3, ghost=True)
        elif k == 1:
            slit(fx, spiral(0.0, 1.0, 120), maxw=3, hot=True)
            star4(fx, cx, cy, 8, hot=True, diag=True)
            star4(fx, cx, cy, 4, hot=True)
            embers(fx, cx, cy, 5, 8, rng)
        elif k == 2:
            slit(fx, spiral(0.15, 1.0, 110), maxw=2, dim=1, phase=5)
            star4(fx, cx, cy, 6, hot=False, diag=True)
            embers(fx, cx, cy, 6, 14, rng)
        else:
            slit_decay(fx, spiral(0.2, 1.0, 110), (k - 2) / 2.2, seed=k, seg=7)
            embers(fx, cx, cy, 4, 18 + 6 * k, rng, cols=[A[23], A[21], A[19]])


# ------------------------------------------------------------------ 5 그림자 넘기
CUTS = (40, 66, 92, 116)
SLOPE = -0.32


def sliced_ink(fx, mask, lum, dx, dy, age, seed, cuts=CUTS, spread=1.0, flake_dir=(1, -1), lines=True):
    """먹 실루엣이 비스듬한 은선 틈(칼 베기 방향)으로 썰려, 띠마다 틈을 따라 엇갈려 미끄러지고 age 만큼 먹 조각으로 흩어진다."""
    def band_of(x, y):
        yy = y - SLOPE * (x - 48)
        b = 0
        for c in cuts:
            if yy >= c:
                b += 1
        return b, yy
    for (x, y) in sorted(mask):
        b, yy = band_of(x, y)
        if any(abs(yy - c) < 0.75 for c in cuts) and age < 0.8:
            continue
        sh = (1 if b % 2 else -1) * age * 14 * spread
        ox, oy = sh, sh * SLOPE
        hsh = ((x * 73856093) ^ (y * 19349663) ^ seed) & 1023
        if hsh / 1023.0 < age * (0.55 + 0.7 * (1 - y / 140.0)):
            if hsh % 6 == 0:
                fx.put(x + dx + ox + flake_dir[0] * age * 16 + (hsh % 5) - 2, y + dy + oy + flake_dir[1] * age * 14 - (hsh % 9), SL[3] if hsh % 2 else SL[4])
            continue
        edge = any((x + ax, y + ay) not in mask for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        c = SL[1] if lum.get((x, y), 0) < 0.35 else SL[2]
        if edge:
            c = (G[9] if age < 0.3 else SL[6]) if (x, y - 1) not in mask else SL[4]
        fx.put(x + dx + ox, y + dy + oy, c)
    if not lines or age > 0.7:
        return
    # 썰린 자리 은선(실루엣 밖으로 조금 뻗고, 오른쪽 끝이 머리)
    for c in cuts:
        x0, x1 = 12, 86
        cc = 0 if age < 0.2 else (1 if age < 0.45 else 2)
        slit(fx, [(x0 + dx, c + SLOPE * (x0 - 48) + dy), (x1 + dx, c + SLOPE * (x1 - 48) + dy)], maxw=2, ghost=False, dim=cc, side=-1)


@sheet("trait_katana_k_shadowVault_out", (96, 144), [40, 40, 50, 60, 70, 90],
       anchor="player_pivot", pivot=(48, 138), glow=[], part="out", trait="k_shadowVault",
       replaces="shadowstep_ghost·afterimage", depth="above",
       design="분신(그림자) = 주인공 먹 실루엣이 가는 은선 4줄로 썰려 띠마다 좌우로 엇갈려 밀리고 위로 먹 조각이 되어 흩어짐(단검 그림자 걸음의 '녹아내림'과 다르게 '썰림') · 발밑 작은 먹 자국",
       anchorNote="pivot (48,138) = 주인공 몸 시트 피벗과 같음 — 사라지는 자리의 주인공 발")
def k_shadowVault_out(fs):
    mask, lum, pv, _ = hero_mask("down", 0)
    ages = [0.0, 0.12, 0.3, 0.5, 0.72, 0.92]
    for k, fx in enumerate(fs):
        ground_shadow(fx, 48, 138, 16 - 2 * k, 4, SL[1])
        sliced_ink(fx, mask, lum, 0, 0, ages[k], 50)


@sheet("trait_katana_k_shadowVault_in", (128, 144), [40, 40, 50, 60, 80, 100],
       anchor="player_pivot", pivot=(64, 138), glow=[3], part="in", trait="k_shadowVault",
       replaces="katana_counter", depth="above",
       design="적 등 뒤에서 썰린 먹 띠가 엇갈림을 풀며 모여 실루엣이 됨(f0~f2) → f3 돌아서 베는 낮은 은선 초승달(머리 백열) → 실루엣 흩어짐·호 마디 소멸",
       anchorNote="pivot (64,138) = 나타나는 자리의 주인공 발(몸 시트 피벗과 같은 높이)")
def k_shadowVault_in(fs):
    mask, lum, pv, _ = hero_mask("down", 0)
    ages = [0.8, 0.45, 0.12, 0.0, 0.5, 0.85]
    arc = arc_pts(64, 92, 58, 30, 200, 345)
    for k, fx in enumerate(fs):
        if k <= 4:
            sliced_ink(fx, mask, lum, 16, 0, ages[k], 51, flake_dir=(-1, -1))
        if k == 3:
            slit(fx, arc, maxw=4, hot=True, side=1)
            x, y = arc[-1]
            star4(fx, x, y, 8, hot=True)
        elif k == 4:
            slit(fx, arc, maxw=3, dim=1, side=1, phase=3)
        elif k == 5:
            slit_decay(fx, arc, 0.7, seed=k)


# ------------------------------------------------------------------ 6 물러서며 베기
@sheet("trait_katana_k_issenBack", (192, 192), [30, 40, 50, 60, 80, 100],
       anchor="player_pivot", pivot=(96, 150), glow=[1], part="", trait="k_issenBack", replaces="katana_spin",
       depth="above",
       design="한 바퀴(360°) 닫히는 가는 은선 원 + 안쪽 끊긴 둘째 원(겹선) + 원 둘레 8곳 바깥으로 뻗는 짧은 눈금 틈(시계 눈금) — 회전 베기(열린 호)와 구별",
       anchorNote="pivot = 주인공 발(판정 원점). 원 중심 = 발 위 40 도트(110) · 반지름 1.4칸")
def k_issenBack(fs):
    cx, cy, rx, ry = 96, 110, 86, 64
    spans = [(270, 400), (270, 610), (270, 630), (270, 630)]
    for k, fx in enumerate(fs):
        if k <= 2:
            a0, a1 = spans[k]
            pts = arc_pts(cx, cy, rx, ry, a0, a1, 160)
            slit(fx, pts, maxw=3 if k else 2, hot=(k == 1), side=-1, dim=(1 if k == 2 else 0), phase=k * 3, ghost_off=6)
            if k == 1:
                x, y = pts[-1]
                star4(fx, x, y, 8, hot=True)
        else:
            pts = arc_pts(cx, cy, rx, ry, 270, 630, 160)
            slit_decay(fx, pts, (k - 2) / 3.0, seed=k, side=-1, seg=11)
        if k >= 1:
            # 눈금 틈 8
            for j in range(8):
                a = math.radians(j * 45 + 22.5)
                L = [0, 10, 8, 6, 4, 0][k]
                if L <= 0:
                    continue
                x0, y0 = cx + (rx + 3) * math.cos(a), cy + (ry + 3) * math.sin(a)
                x1, y1 = cx + (rx + 3 + L) * math.cos(a), cy + (ry + 3 + L * 0.75) * math.sin(a)
                fx.line(x0, y0, x1, y1, [G[13], G[13], G[11], SL[7], SL[6]][k])
        if k in (1, 2, 3):
            # 안쪽 둘째 원(끊긴 겹선)
            pts = densify(arc_pts(cx, cy, rx - 10, ry - 8, 270, 630, 140))
            for i, (x, y) in enumerate(pts):
                if ((i + 5 * k) // 6) % 2 == 0:
                    fx.put_if_empty(x, y, [SL[7], SL[7], SL[6], SL[5]][k])


# ------------------------------------------------------------------ 7 발도풍
@sheet("trait_katana_k_iaiWave_launch", (128, 128), [40, 50, 60, 80],
       anchor="player_pivot", pivot=(30, 64), rotate=True, flipY="allowed", glow=[0], part="launch", trait="k_iaiWave",
       replaces="katana_crescent", depth="above",
       anchorOffsetDots=dict(x=0, y=-40),
       design="발도 순간 앞으로 터지는 은빛·청백 초승달(f0 한 줄 백열 섬광 → f1 굵은 렌즈 → f2 떨어져 나가며 가늘어짐 → 마디 소멸) + 앞쪽 속도선 3",
       anchorNote="pivot = 초승달이 터지는 몸 가운데(발 위 40 도트). 주인공 발 피벗에 두려면 anchorOffsetDots (0,−40) 을 더한 뒤 진행 각도로 회전(제안)")
def k_iaiWave_launch(fs):
    cx, cy = 30, 64
    for k, fx in enumerate(fs):
        rng = random.Random(70 + k)
        if k == 0:
            pts = arc_pts(cx, cy, 44, 52, -62, 62, 60)
            slit(fx, pts, maxw=3, hot=True, side=-1, ghost=False)
            star4(fx, cx + 44, cy, 9, hot=True)
        elif k == 1:
            lens_arc(fx, cx + 4, cy, 56, 60, 0, 120, 7, ramp=MOON_RAMP)
            lens_arc(fx, cx + 4, cy, 56, 60, 0, 104, 3, ramp=SILVER_RAMP)
            for dy in (-14, 0, 14):
                fx.line(cx + 66, cy + dy, cx + 90 - abs(dy), cy + dy, MOON[4], every=lambda q: q % 6 < 4)
        elif k == 2:
            lens_arc(fx, cx + 18, cy, 58, 58, 0, 100, 4, ramp=MOON_RAMP)
            for dy in (-12, 0, 12):
                fx.line(cx + 40, cy + dy, cx + 64, cy + dy, MOON[2], every=lambda q: q % 5 < 2)
        else:
            pts = arc_pts(cx + 26, cy, 58, 56, -45, 45, 40)
            slit_decay(fx, pts, 0.6, seed=k, side=-1)
            embers(fx, cx + 70, cy, 4, 18, rng, cols=[MOON[3], MOON[2]])


@sheet("trait_katana_k_iaiWave_wave", (96, 64), [60, 60, 60, 60],
       anchor="projectile", pivot=(58, 32), rotate=True, flipY="allowed", glow=[], part="wave", trait="k_iaiWave",
       replaces="윤곽 사각형", depth="above", loop=True,
       light=dict(color="#c8d8f0", radius=40, intensity=0.7, flicker=dict(amp=0.15, hz=10)),
       design="날아가는 초승달 검풍(투사체 루프) — 볼록한 앞(오른쪽) 가장자리 청백 1도트·몸 청백 렌즈·뒤로 흐르는 끊긴 속도선 3(위상이 칸마다 흐름) · 끝이 반짝",
       anchorNote="pivot = 투사체 중심(판정 원 중심). 오른쪽 = 진행 방향")
def k_iaiWave_wave(fs):
    cx, cy = 34, 32
    for k, fx in enumerate(fs):
        w = 7 + (1 if k % 2 else 0)
        lens_arc(fx, cx, cy, 30, 28, 0, 128, w, ramp=MOON_RAMP)
        lens_arc(fx, cx, cy, 30, 28, 0, 100, 2.5, ramp=SILVER_RAMP)
        for j, dy in enumerate((-14, 0, 14)):
            L = 40 if dy == 0 else 30
            ph = k * 4 + j * 3
            for x in range(cx - L + 20, cx + 18):
                if ((x + ph) // 5) % 2 == 0:
                    fx.put_if_empty(x, cy + dy, MOON[2] if x < cx else MOON[3])
        # 끝 반짝(칸마다 위/아래 번갈아)
        a = math.radians(64 if k % 2 else -64)
        fx.put(cx + 30 * math.cos(a), cy + 28 * math.sin(a), MOON[5])
        fx.put(cx + 30, cy + (k % 3) - 1, G[14])


# ------------------------------------------------------------------ 8 연쇄 발도
@sheet("trait_katana_k_iaiChain", (192, 64), [40, 40, 50, 60, 80],
       anchor="player_pivot", pivot=(10, 46), rotate=True, flipY="allowed", glow=[], part="", trait="k_iaiChain",
       replaces="dash_trail·afterimage", depth="below",
       design="낮게 미끄러지는 잔상 줄: 바닥 가까이 나란한 은선 3줄(가운데가 길고 머리 밝음) + 먹 그림자 쐐기 잔상 3(뒤로 갈수록 성기게) → 마디 소멸",
       anchorNote="pivot(왼끝) = 출발한 주인공 발. 오른쪽 = 다음 적 방향. 길이 172 도트(≈2.7칸) — 거리에 맞춰 x 배율 가능")
def k_iaiChain(fs):
    px, py = 10, 46
    for k, fx in enumerate(fs):
        reach = [70, 150, 182, 182, 182][k]
        for j, (dy, L) in enumerate(((-6, 0.82), (0, 1.0), (6, 0.74))):
            if k <= 2:
                slit(fx, [(px + 6, py + dy), (px + 6 + (reach - 10) * L, py + dy)], maxw=2 if dy else 3, ghost=False,
                     dim=(1 if k == 2 else 0), head=True)
            else:
                st = px + 6 + j * 9
                slit_decay(fx, [(st, py + dy), (px + 6 + (reach - 10) * L, py + dy)], (k - 2) / 2.5, seed=k * 3 + j, seg=10 + 4 * j)
        for j, x in enumerate((40, 88, 136)):
            if x > reach - 20:
                continue
            holes = 0.15 + 0.25 * j + 0.25 * max(0, k - 1)
            if holes < 0.95:
                ink_wedge(fx, x - 22, py - 1, 26, 7 - j, holes=holes, seed=k * 10 + j)


# ------------------------------------------------------------------ 9 피바람
CRIM_RAMP = [(0.84, CRIM[6]), (0.68, CRIM[5]), (0.52, CRIM[4]), (0.36, CRIM[3]), (0.2, CRIM[2]), (0.06, CRIM[1])]


@sheet("trait_katana_bloodGale", (192, 192), [40, 40, 50, 60, 70, 90],
       anchor="floor", pivot=(96, 150), glow=[1], part="", trait="bloodGale", replaces="chain_bloodlust",
       depth="above",
       design="한 바퀴 더 도는 피바람 고리: 가는 적갈 바람 테 2줄(끊김이 돌며 흐름) + 테에 접선으로 박히는 짧고 날 선 피 칼날 8(꼬리 적갈 · 머리 은선, f1 백열) + 접선으로 줄지어 흩뿌리는 핏방울 — 술 회오리(굵은 액체 띠)와 달리 '잘게 끊긴 칼날 테'",
       anchorNote="pivot = 주인공 발. 고리 중심 = 발 위 40 도트(110)")
def bloodGale(fs):
    cx, cy, rx, ry = 96, 110, 80, 60
    for k, fx in enumerate(fs):
        rng = random.Random(90 + k)
        age = max(0, k - 2) / 3.0
        rot = k * 34
        # 바람 테 2줄(끊긴 실선, 돌며 흐름)
        for j, (dr, col) in enumerate(((0, CRIM[4]), (-9, CRIM[3]))):
            pts = densify(arc_pts(cx, cy, rx + dr, ry + dr * 0.75, 0, 360, 120))
            n = len(pts)
            for i, (x, y) in enumerate(pts):
                ph = int((i / n) * 360 - rot * (1 + j)) % 40
                if ph < (26 if k < 4 else 14):
                    fx.put(x, y, col if k < 4 else CRIM[2])
        # 피 칼날 8(접선 방향 짧은 초승 획)
        if k <= 4:
            f = Field(fx.w, fx.h)
            heads = []
            for j in range(8):
                h = j * 45 + rot + 20
                L = [24, 38, 40, 34, 24][k]
                pts = arc_pts(cx, cy, rx + 2, ry + 1.5, h - L, h, 12)
                f.path(pts, lambda t: (0.6 + 2.8 * math.sin(math.pi * t ** 0.6) ** 2) * (1 - 0.35 * age), lambda t: (0.35 + 0.65 * t) * (1 - 0.5 * age))
                heads.append(pts)
            f.paint(fx, CRIM_RAMP, dither=0.08)
            if k <= 2:
                for pts in heads:
                    slit(fx, pts[-5:], maxw=2, hot=(k == 1), ghost=False, side=-1)
        # 핏방울(접선으로 줄지어)
        for j in range(8):
            h = math.radians(j * 45 + rot + 20)
            tx, ty = -math.sin(h), math.cos(h) * 0.75
            ox, oy = math.cos(h), math.sin(h) * 0.75
            for q in range(3):
                d = 6 + q * 5 + 10 * k
                x = cx + (rx + 4) * math.cos(h) + tx * d + ox * (q * 2 + 3 * k)
                y = cy + (ry + 3) * math.sin(h) + ty * d + oy * (q * 2 + 3 * k) + (age * age * 16)
                if k >= 1:
                    fx.put(x, y, CRIM[5] if q == 0 else CRIM[4])
                    if q == 0:
                        fx.put(x + 1, y, CRIM[3])


# ------------------------------------------------------------------ 10 술 회오리
def liquor_whirl(fx, k, n, fire=False, seed=0):
    cx, cy, rx, ry = 96, 108, 68, 48
    rng = random.Random(seed + k)
    rot = k * 48
    shrink = [1.08, 1.03, 1.0, 1.0, 0.98, 0.96][k]
    age = max(0, k - 3) / 2.0
    f = Field(fx.w, fx.h)
    for j in range(3):
        a1 = rot + j * 120 + 140
        pts = []
        for i in range(40):
            t = i / 39
            a = math.radians(a1 - 150 * (1 - t))
            r = (0.72 + 0.5 * (1 - t)) * shrink
            pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a) - 8 * math.sin(math.pi * t)))
        f.path(pts, lambda t: (0.8 + 4.4 * math.sin(math.pi * t ** 0.7) ** 1.5) * (1 - 0.5 * age), lambda t: (0.4 + 0.6 * t) * (1 - 0.5 * age))
    if fire:
        ramp = [(0.8, A[25] if k != 1 else A[26]), (0.62, A[23]), (0.46, A[21]), (0.3, A[19]), (0.14, A[18])]
    else:
        ramp = [(0.82, A[23]), (0.62, A[19]), (0.4, A[18]), (0.16, A[17])]
    f.paint(fx, ramp, dither=0.12)
    # 칼을 따라가는 은선 머리
    if k <= 3 and not fire:
        for j in range(3):
            a1 = rot + j * 120 + 140
            pts = arc_pts(cx, cy, rx * shrink * 0.72 + 3, ry * shrink * 0.72 + 3, a1 - 28, a1, 10)
            slit(fx, pts, maxw=2, ghost=False, side=-1, dim=(1 if k >= 2 else 0))
    if fire and k <= 4:
        for j in range(16):
            a = math.radians(rot + j * 22.5 + rng.uniform(-8, 8))
            r = shrink * rng.uniform(0.7, 1.15)
            x, y = cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)
            h = rng.uniform(8, 18) * (1 - 0.5 * age) * (0.7 if k == 0 else 1.0)
            flame(fx, x, y, h, rng.uniform(3, 5), lean=rng.uniform(-6, 6), cols=FIRE)
    # 튀는 술방울
    for j in range(14):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.9, 1.25) * shrink
        x, y = cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a) + age * 14
        fx.put(x, y, (A[23] if fire else A[19]) if j % 2 else (A[21] if fire else A[18]))
        if not fire and j % 5 == 0:
            fx.put(x, y - 1, A[23])


@sheet("trait_katana_liquorWhirl", (192, 192), [40, 50, 50, 60, 70, 90],
       anchor="floor", pivot=(96, 150), glow=[], part="", trait="liquorWhirl", replaces="pool_liquor",
       depth="above",
       design="술 줄기 3가닥이 칼(은선 머리)을 따라 바깥에서 감겨 드는 회오리 — pool_liquor 술빛(짙은 호박·갈색, 반짝 점) · 마지막에 바닥으로 튀는 술방울",
       anchorNote="pivot = 주인공 발. 회오리 중심 = 발 위 38 도트")
def liquorWhirl(fs):
    for k, fx in enumerate(fs):
        liquor_whirl(fx, k, len(fs), False, 100)


@sheet("trait_katana_liquorWhirl_fire", (192, 192), [40, 50, 50, 60, 70, 90],
       anchor="floor", pivot=(96, 150), glow=[1], part="fire", trait="liquorWhirl", replaces="pool_liquor_fire",
       depth="above", light=dict(color="#e2a33c", radius=96, intensity=1.0, ms=300, atFrame=0, flicker=dict(amp=0.2, hz=9)),
       design="불붙은 술 회오리 — 같은 줄기가 pool_liquor_fire 호박 불길로 타오르고 둘레에 혓바닥 16(밑 둥글고 끝 뾰족) · f1 심만 백열에 가까운 호박")
def liquorWhirl_fire(fs):
    for k, fx in enumerate(fs):
        liquor_whirl(fx, k, len(fs), True, 110)


# ------------------------------------------------------------------ 11 불똥 내려베기
@sheet("trait_katana_k_sparkCleave", (96, 64), [60, 60, 60, 60, 60, 60],
       anchor="floor", pivot=(48, 40), glow=[], part="", trait="k_sparkCleave", replaces="fire_pool",
       depth="below", loopRange=[1, 4], endFrames=[5, 5],
       light=dict(color="#e2a33c", radius=48, intensity=0.7, flicker=dict(amp=0.25, hz=8)),
       lifeRule="f0 생김 → f1~f4 루프(시스템 durationMs 동안) → f5 꺼짐",
       design="선 끝에 남는 작은 불씨 웅덩이: 바닥 납작 타원(짙은 호박 테·숯 점) + 깜박이는 작은 혓바닥 3~4 + 위로 오르는 불티 — fire_pool 보다 작고 낮게(칼 선 끝 한 점)")
def k_sparkCleave(fs):
    cx, cy = 48, 40
    for k, fx in enumerate(fs):
        rng = random.Random(120 + k)
        s = [0.6, 1.0, 1.0, 1.0, 1.0, 0.8][k]
        f = Field(fx.w, fx.h)
        f.blob(cx, cy, 30 * s, 9 * s, 1.0)
        f.paint(fx, [(0.55, A[18]), (0.25, A[17]), (0.02, A[16])], dither=0.4)
        # 숯 점
        for j in range(18):
            a = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(0, 0.85)
            fx.put(cx + math.cos(a) * r * 28 * s, cy + math.sin(a) * r * 8 * s, rng.choice([A[19], A[21], A[21], A[23]]) if k < 5 else A[19])
        if k < 5:
            for j in range(4 if k else 2):
                x = cx + (j - 1.5) * 13 + rng.uniform(-3, 3)
                h = rng.uniform(9, 17) * s
                flame(fx, x, cy + rng.uniform(-2, 2), h, rng.uniform(4, 6), lean=rng.uniform(-5, 5))
            for j in range(4):
                fx.put(cx + rng.uniform(-24, 24), cy - rng.uniform(16, 30), A[23] if j % 2 else A[21])


@sheet("trait_katana_k_sparkCleave_spark", (48, 48), [40, 40, 50, 60],
       anchor="floor", pivot=(24, 38), glow=[0], part="spark", trait="k_sparkCleave", replaces="점 윤곽",
       depth="above", light=dict(color="#e2a33c", radius=24, intensity=0.8, ms=60, atFrame=0),
       design="바닥을 긁으며 부채꼴로 튀는 불똥 줄(1도트 꼬리 + 밝은 머리) + 바닥 긁힌 은선 한 줄")
def k_sparkCleave_spark(fs):
    cx, cy = 24, 38
    for k, fx in enumerate(fs):
        rng = random.Random(130)
        fx.line(cx - 14 + 2 * k, cy + 1, cx + 6, cy + 1, [G[13], G[11], SL[7], SL[6]][k])
        for j in range(9):
            a = math.radians(rng.uniform(-170, -20))
            sp = rng.uniform(10, 22)
            d0 = sp * (0.2 + 0.4 * k)
            d1 = d0 + 5 - k
            x0, y0 = cx + math.cos(a) * d0, cy + math.sin(a) * d0 + 2 * k * k * 0.5
            x1, y1 = cx + math.cos(a) * d1, cy + math.sin(a) * d1 + 2 * k * k * 0.5
            if k < 3:
                fx.line(x0, y0, x1, y1, A[21] if k else A[23])
            fx.put(x1, y1, [A[26], A[25], A[23], A[21]][k])
        if k == 0:
            star4(fx, cx, cy, 4, hot=False, col=A[26])


# ------------------------------------------------------------------ 12 땅에 박기
def stake(fx, x, y, h, cols):
    """작은 말뚝: 아래가 좁은 쐐기 + 윗면 밝음."""
    for k in range(h):
        w = 1 if k < h * 0.4 else 2
        for dx in range(-w + 1, w):
            fx.put(x + dx, y - k, cols[1] if dx < 0 else cols[2])
    fx.put(x, y - h, cols[3])
    fx.put(x - 1, y - h + 1, cols[3])
    fx.put(x, y + 1, cols[0])


@sheet("trait_katana_k_groundPin_bind", (128, 64), [80, 80, 80, 80],
       anchor="floor", pivot=(64, 40), glow=[], part="bind", trait="k_groundPin", replaces="katana_cleave_crack",
       depth="below", loopRange=[1, 3], endFrames=None,
       lifeRule="f0 박힘 → f1~f3 루프(묶인 동안, 시스템 durationMs) — 풀리면 _impact 로 넘김",
       design="묶음 = 적 발밑 청회(#9ab0d8) 납작 고리 + 고리 위 말뚝 4(앞뒤좌우) + 바닥 은회 금 6갈래 · 루프는 고리 위를 도는 밝은 마디")
def k_groundPin_bind(fs):
    cx, cy = 64, 40
    rng = random.Random(140)
    trees = [crack_tree(cx, cy, j * math.pi / 3 + rng.uniform(-0.2, 0.2), rng.uniform(24, 40), random.Random(141 + j), depth=1) for j in range(6)]
    for k, fx in enumerate(fs):
        for tr in trees:
            draw_cracks(fx, tr, G[10] if k == 0 else SL[7], G[1], sy=0.42, cx=cx, cy=cy, grow=1.0)
        f = Field(fx.w, fx.h)
        f.ring(cx, cy, 30, 11, 1.8, 1.0, vfun=lambda a, k=k: 0.55 + 0.45 * max(0, math.cos(math.radians(a - (k * 90 + 20)))) ** 3)
        f.paint(fx, [(0.85, BIND[5]), (0.62, BIND[4]), (0.38, BIND[3]), (0.12, BIND[2])])
        for j, (sx, sy_) in enumerate(((cx - 30, cy), (cx + 30, cy), (cx, cy - 11), (cx, cy + 11))):
            stake(fx, sx, sy_, 9 if j != 2 else 7, [BIND[0], BIND[2], BIND[3], BIND[5] if k == 0 else BIND[4]])
        if k == 0:
            star4(fx, cx, cy - 2, 5, hot=False, col=G[14])
            for j in range(8):
                a = rng.uniform(math.pi, 2 * math.pi)
                puff(fx, cx + math.cos(a) * 34, cy + math.sin(a) * 12, rng.uniform(2.5, 4), DUST_ASH)


@sheet("trait_katana_k_groundPin_impact", (128, 128), [40, 40, 50, 60, 80, 110],
       anchor="contact", pivot=(86, 64), rotate=True, flipY="allowed", glow=[0], part="impact", trait="k_groundPin",
       replaces="hit_burst", depth="above",
       design="묶임이 풀리며 튕겨 나가 처박힘: 청회 고리가 마디로 끊겨 뒤로 흩어짐 + 벽면 은회 금·돌 파편·재 먼지(흘려 밀기 impact 와 같은 벽 말투, 청회 조각이 표지)")
def k_groundPin_impact(fs):
    for k, fx in enumerate(fs):
        wall_impact(fx, k, len(fs), 86, 64, "katana", seed=150, scale=0.9, hot=(k == 0), accent=[BIND[4], BIND[3], BIND[5]])
        # 끊긴 고리 조각
        rng = random.Random(151)
        if k <= 4:
            for j in range(6):
                a0 = j * 60 + rng.uniform(-10, 10)
                d = 10 + 12 * k
                cx, cy = 60 - d * 0.8, 64 + (j - 2.5) * (6 + 4 * k)
                pts = arc_pts(cx, cy, 10, 4, a0, a0 + 50, 6)
                for x, y in densify(pts):
                    fx.put(x, y, [BIND[5], BIND[4], BIND[4], BIND[3], BIND[2]][k])


# ------------------------------------------------------------------ 13 달빛 잇기
def moon_glyph(fx, x, y, r, cols=None, hot=False):
    """작은 초승달(달 분신 표지)."""
    cols = cols or MOON
    for yy in range(int(y - r) - 1, int(y + r) + 2):
        for xx in range(int(x - r) - 1, int(x + r) + 2):
            d1 = math.hypot(xx - x, yy - y)
            d2 = math.hypot(xx - (x + r * 0.5), yy - (y - r * 0.25))
            if d1 <= r and d2 > r * 0.8:
                c = cols[4] if d1 > r - 1.2 else cols[3]
                if hot and d1 > r - 1.2 and xx < x:
                    c = X1
                fx.put(xx, yy, c)


@sheet("trait_katana_k_moonRelay", (256, 64), [40, 40, 50, 60, 80, 100],
       anchor="contact", pivot=(14, 32), rotate=True, flipY="allowed", glow=[1], part="", trait="k_moonRelay",
       replaces="katana_fullmoon", depth="above", light=dict(color="#c8d8f0", radius=32, intensity=0.7, ms=300, atFrame=0),
       design="달 분신(작은 청백 초승달)이 쓰러진 자리(왼끝)에서 다음 적으로 건너가며 긋는 청백 선 — 선 머리에 달, 지나간 선은 청백 은선 → 끝에서 달이 X 로 벰 → 점선 소멸",
       anchorNote="pivot(왼끝) = 쓰러진 적 자리. 오른쪽 = 다음 적 방향. 길이 230 도트(사거리 4칸=256 이면 x 배율 1.1)")
def k_moonRelay(fs):
    py = 32
    heads = [50, 150, 236, 236, 236, 236]
    for k, fx in enumerate(fs):
        h = heads[k]
        rng = random.Random(160 + k)
        if k <= 2:
            P = densify([(14, py), (h, py)])
            for i, (x, y) in enumerate(P):
                t = i / max(1, len(P) - 1)
                c = MOON[4] if t > 0.6 else (MOON[3] if t > 0.25 else MOON[2])
                fx.put(x, y, c)
                if t > 0.5:
                    fx.put(x, y - 1, MOON[2] if t < 0.85 else MOON[3])
                if ((i + 3 * k) // 6) % 3 == 0 and 0.1 < t < 0.85:
                    fx.put_if_empty(x, y + 3, MOON[1])
            moon_glyph(fx, h - 2, py - 1, 7, hot=(k == 1))
            if k == 2:
                star4(fx, h + 4, py, 7, hot=False, col=MOON[5], diag=True)
                fx.line(h - 4, py - 9, h + 12, py + 9, MOON[5])
                fx.line(h - 4, py + 9, h + 12, py - 9, MOON[4])
        else:
            age = (k - 2) / 3.0
            P = densify([(14, py), (236, py)])
            for i, (x, y) in enumerate(P):
                if (i // (8 - 2 * k + 6)) % 2 == 0 and rng.random() > age * 0.6:
                    fx.put(x, y + (1 if (i // 10) % 2 else -1) * int(age * 3), MOON[3] if age < 0.5 else MOON[2])
            moon_glyph(fx, 236, py - 2 - 4 * k, max(3, 7 - k), cols=[MOON[0], MOON[1], MOON[2], MOON[2], MOON[3]])


# ------------------------------------------------------------------ 14 취월 / 공명 되받는 달 — 달 분신 실루엣
def moon_sil(fx, mask, lum, dx, dy, clip_y=None, dith=0.0, seed=0):
    rng = random.Random(seed)
    for (x, y) in mask:
        if clip_y is not None and y + dy > clip_y:
            continue
        if dith and (((x + y) % 2 == 0) if dith < 0.6 else ((x * 3 + y) % 4 != 0)) and dith > 0.2:
            if dith >= 0.6 or (x + y) % 2 == 0:
                continue
        edge = any((x + ax, y + ay) not in mask for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        L = lum.get((x, y), 0)
        c = MOON[1] if L < 0.3 else MOON[2]
        if edge:
            c = MOON[4] if ((x, y - 1) not in mask or (x - 1, y) not in mask) else MOON[3]
        fx.put(x + dx, y + dy, c)


def scale_mask(mask, lum, sc, ax, ay):
    """실루엣을 (ax,ay) 기준으로 sc 배(최근접) 축소."""
    out, ol = set(), {}
    xs = [x for x, _ in mask]
    ys = [y for _, y in mask]
    for y in range(int(ay - (ay - min(ys)) * sc) - 1, ay + 2):
        for x in range(int(ax - (ax - min(xs)) * sc) - 1, int(ax + (max(xs) - ax) * sc) + 2):
            sx, sy = int(round(ax + (x - ax) / sc)), int(round(ay + (y - ay) / sc))
            if (sx, sy) in mask:
                out.add((x, y))
                ol[(x, y)] = lum.get((sx, sy), 0)
    return out, ol


@sheet("trait_katana_k_moonPools", (128, 160), [40, 40, 50, 60, 70, 80, 100],
       anchor="floor", pivot=(64, 140), glow=[4], part="", trait="k_moonPools", replaces="katana_fullmoon·katana_crescent",
       depth="above", light=dict(color="#c8d8f0", radius=48, intensity=0.75, ms=600, atFrame=0),
       design="술 웅덩이 수면의 달 그림자(청백 원) + 동심 물결 → 수면 아래서 청백 달 분신 실루엣이 솟아오름(수면선에서 잘림) → f4 청백 초승달 베기(머리 백열) → 실루엣이 체커로 바래며 물결만 남음",
       anchorNote="pivot = 웅덩이 중심(수면). 실루엣 발 = 수면")
def k_moonPools(fs):
    mask, lum, pv, _ = hero_mask("down", 0)
    cx, cy = 64, 140
    rise = [None, 70, 34, 6, 0, 0, 0]
    for k, fx in enumerate(fs):
        # 물결
        for j in range(3):
            r = 10 + j * 13 + k * 4
            if r > 60:
                continue
            pts = densify(arc_pts(cx, cy, r, r * 0.3, 0, 360, 60))
            col = [MOON[4], MOON[3], MOON[2]][j] if k < 5 else [MOON[2], MOON[1], MOON[1]][j]
            for i, (x, y) in enumerate(pts):
                if (i // (5 + j)) % 3 != 2:
                    fx.put(x, y, col)
        if k <= 3:
            # 수면의 달
            for yy in range(cy - 3, cy + 4):
                for xx in range(cx - 8, cx + 9):
                    if ((xx - cx) / 8) ** 2 + ((yy - cy) / 3) ** 2 <= 1:
                        fx.put(xx, yy, MOON[5] if yy <= cy - 1 else MOON[4])
        if rise[k] is not None:
            dith = 0.0 if k <= 4 else (0.4 if k == 5 else 0.8)
            if k < 6:
                moon_sil(fx, mask, lum, cx - 48, cy - 138 + rise[k], clip_y=cy - 1, dith=dith)
        if k == 3:
            fx.line(cx + 10, cy - 70, cx + 34, cy - 104, MOON[5])   # 든 칼
            fx.line(cx + 11, cy - 70, cx + 35, cy - 104, MOON[3])
        if k == 4:
            arc = arc_pts(cx, cy - 66, 50, 30, 200, 340, 50)
            slit(fx, arc, maxw=4, hot=True, side=1)
            lens_arc(fx, cx, cy - 66, 50, 30, 270, 120, 4, ramp=MOON_RAMP)
        if k == 5:
            arc = arc_pts(cx, cy - 66, 50, 30, 200, 340, 50)
            slit_decay(fx, arc, 0.5, seed=k)


@sheet("trait_res_katana_insight", (96, 144), [40, 40, 50, 60, 80, 100],
       anchor="contact", pivot=(80, 98), glow=[2], part="", trait=None, resonance="res_katana_insight",
       replaces="katana_fullmoon", depth="above", light=dict(color="#c8d8f0", radius=32, intensity=0.7, ms=400, atFrame=0),
       flipX="allowed", flipXNote="그림 = 분신이 적의 왼쪽에 서서 오른쪽(적)을 벰. 적이 주인공 왼쪽으로 밀렸으면 flipX 로 반대편에",
       design="공명 되받는 달 — 밀치거나 끌어온 적 옆(왼쪽 반 칸)에 작은(0.72배) 청백 달 분신: f0 머리 위 작은 초승달 표지 → f1 체커로 나타남 → f2 적 쪽으로 비스듬히 내려 베는 은선(머리 백열) → 바래며 초승달만 남음",
       anchorNote="pivot (80,98) = 밀치거나 끌어온 적의 몸 중심(발 위 40 — contact 점). 분신은 그 왼쪽 약 44 도트, 분신 발 = pivot 아래 40")
def res_katana_insight(fs):
    mask0, lum0, pv, _ = hero_mask("down", 0)
    mask, lum = scale_mask(mask0, lum0, 0.72, 48, 138)
    dx = -12
    path = [(64, 50), (78, 78), (92 - 4, 110)]
    for k, fx in enumerate(fs):
        if k <= 4:
            dith = [0.9, 0.4, 0.0, 0.0, 0.5][k]
            if k > 0:
                moon_sil(fx, mask, lum, dx, 0, dith=dith)
        if k in (0, 1, 5):
            moon_glyph(fx, 50 + dx, 52 - (6 if k == 5 else 0), 6, hot=False)
        if k == 2:
            slit(fx, path, maxw=4, hot=True, side=-1)
            star4(fx, path[-1][0], path[-1][1], 6, hot=True)
        elif k == 3:
            slit(fx, path, maxw=3, dim=1, side=-1)
        elif k == 4:
            slit_decay(fx, path, 0.6, seed=k)


# ------------------------------------------------------------------ 공명 칼바람 길(반복 타일)
@sheet("trait_res_katana_breach", (64, 64), [40, 40, 50, 60, 80, 100],
       anchor="path_start", pivot=(0, 32), rotate=True, flipY="allowed", glow=[1], part="", trait=None,
       resonance="res_katana_breach", replaces="katana_issen_line_t2_solo·윤곽 선", depth="below", tile=True,
       tileNote="tile: true — 가로 64 도트 주기로 이음새 없이 반복(TileSprite). 높이 64(=길 폭 1칸). 왼쪽 = 길 시작, 오른쪽 = 대쉬 방향",
       design="대쉬 길에 남는 바람 칼날 띠: 위아래 끊긴 은선 테 2줄 + 띠를 비스듬히 가르는 은선 칼날 '/' (32 도트마다) → f1 칼날 머리 백열(그 길을 다시 벰) → 칼날이 갈라져 마디 소멸")
def res_katana_breach(fs):
    W = 64
    for k, fx in enumerate(fs):
        big = Fx(W * 3, 64)
        dim = [2, 0, 1, 2, 3, 3][k]
        # 테 2줄
        for yy, ph in ((20, 0), (44, 4)):
            for x in range(W * 3):
                if ((x + ph + k * 4) // 8) % 4 != 3:
                    if k < 5 or x % 4 == 0:
                        big.put(x, yy, [SL[6], G[9], SL[7], SL[6], SL[5], SL[5]][k])
        for j in range(6):
            x0 = j * 32 + 4
            pts = [(x0, 42), (x0 + 22, 22)]
            if k <= 2:
                slit(big, pts, maxw=3 if k == 1 else 2, hot=(k == 1), side=-1, ghost=False, dim=dim if k != 1 else 0)
            elif k <= 4:
                slit_decay(big, pts, (k - 2) / 2.5, seed=j % 2, seg=5)
            else:
                big.put(x0 + 11, 32, SL[5])
        for y in range(64):
            for x in range(W):
                c = big.get(x + W, y)
                if c:
                    fx.put(x, y, c)


@sheet("trait_res_katana_chain", (160, 160), [40, 50, 60, 80, 100],
       anchor="hitbox_center", pivot=(80, 80), glow=[0], part="", trait=None, resonance="res_katana_chain",
       replaces="katana_spin", depth="above",
       design="공명 끊이지 않는 칼 — 쓰러진 자리에서 바깥으로 퍼지며 도는 은선 바람 칼날 8장(바람개비처럼 휜 짧은 호) · f0 가운데 백열 별 → 칼날이 커지며 엷어짐")
def res_katana_chain(fs):
    cx, cy = 80, 80
    radii = [12, 34, 52, 64, 72]
    for k, fx in enumerate(fs):
        r = radii[k]
        for j in range(8):
            a0 = j * 45 + k * 14
            pts = []
            for i in range(14):
                t = i / 13
                a = math.radians(a0 + t * 38)
                rr = r * (0.75 + 0.25 * t)
                pts.append((cx + rr * math.cos(a), cy + rr * 0.8 * math.sin(a)))
            if k <= 2:
                slit(fx, pts, maxw=3 if k == 1 else 2, ghost=False, side=-1, dim=(1 if k == 2 else 0))
            else:
                slit_decay(fx, pts, (k - 2) / 2.5, seed=j, seg=5)
        if k == 0:
            star4(fx, cx, cy, 9, hot=True)
            star4(fx, cx, cy, 5, hot=True, diag=True)
        if k in (1, 2):
            embers(fx, cx, cy, 6, r, random.Random(170 + k))
