"""56라운드 Q16·Q19 — 단검 낙인(烙印) 표식 · 기폭 폭발 · 과열 100% 일괄 폭발.

dagger_brand_mark      적 머리 위(또는 몸)에 붙는 표식. 행 = 스택 1~5. 모양 = 붓으로 지진 '바를 정' 셈 획(1~4 세로 획, 5 = 비스듬히 긋는 획) —
                       키아트 sheet_dagger 3번(등에 남은 타는 손톱 자국)을 셈 표시로 정리. 같은 적을 칠 때마다 획이 하나씩 늘어난다.
                       열 0~1 = 새 획이 지져지는 순간(스택이 오를 때 1회), 열 2~5 = 남아서 타는 루프.
dagger_brand_burst     그림자 걸음으로 적 뒤에 서면 표식 전부 폭발. 행 = 크기 s(1~2 스택)·m(3~4)·l(5).
dagger_overheat_burst  과열 100% — 주인공 중심으로 열이 터져 나가는 고리(주변 낙인 일괄 폭발의 방아쇠). 각 적의 폭발은 dagger_brand_burst.
dagger_overheat_cool   과열 식는 동안(잠깐 느려짐) 주인공 몸에서 오르는 재 김 — 루프.
"""
import math
import random

import rk
from rk import W, FK

# =============================================================================
# 표식
# =============================================================================
MARK_C = 80
MARK_MS = [40, 70, 120, 120, 120, 120]
SCAR = [rk.A17, rk.A18, rk.A19, rk.A21, rk.A23]            # 지진 자국: 어두운 테 → 호박 심
SCAR_HOT = [rk.A18, rk.A19, rk.A21, rk.A23, rk.A25, rk.A26]


def strokes(n):
    """셈 획(로컬, 피벗 = 표식 아래 가운데). 세로 획 4개 간격 7, 5번째는 왼아래 → 오른위로 긋는 획."""
    out = []
    xs = [-10.5, -3.5, 3.5, 10.5]
    for k in range(min(n, 4)):
        x = xs[k] + (0.6 if k % 2 else -0.4)
        out.append([(x - 1.2, -3.0), (x + 0.4, -12.5), (x + 1.6, -21.0)])     # 살짝 기운 붓 획(아래 → 위)
    if n >= 5:
        out.append([(-15.0, -6.0), (0.0, -12.5), (15.5, -19.5)])
    else:                                              # 1~4 획은 가운데 정렬(피벗 = 표식 가운데)
        cx = sum(xs[:n]) / n
        out = [[(x - cx, y) for x, y in st] for st in out]
    return out


def draw_stroke(L, pts, ox, oy, w, v, prof=None):
    P = [(ox + x, oy + y) for x, y in pts]
    L.stroke(P, w, prof=prof or FK.tp_both(0.55, 0.42), v=v, vprof=lambda u: 0.75 + 0.25 * math.sin(math.pi * u), soft=0.8)


def mark_frames(n):
    out = []
    ox, oy = MARK_C / 2, MARK_C - 16
    S = strokes(n)
    for i in range(len(MARK_MS)):
        f = rk.frame(MARK_C, MARK_C)
        Lr = f.L([rk.B0, rk.A17])                         # 그을린 테(어두운)
        Lc = f.L(SCAR)
        Lh = f.L(SCAR_HOT)
        Le = f.L([rk.A19, rk.A21, rk.A23])
        for k, st in enumerate(S):
            new = (k == n - 1)
            fl = 0.84 + 0.14 * W.h2(k, i, 3 + n)           # 루프 깜빡임
            draw_stroke(Lr, st, ox, oy, 2.6, 0.9)
            if new and i == 0:                             # 지져지는 순간(판정) — 새 획만 뜨겁게
                draw_stroke(Lh, st, ox, oy, 1.6, 1.0)
            elif new and i == 1:
                draw_stroke(Lh, st, ox, oy, 1.4, 0.8)
            else:
                draw_stroke(Lc, st, ox, oy, 1.35, fl)
        # 획 위로 오르는 불티·연기(루프 프레임만, 위상 이동)
        if i >= 2:
            for k in range(min(n, 3)):
                x = ox + [-6, 4, 12][k] + int(1.5 * math.sin(i * 1.7 + k))
                y = oy - 24 - ((i * 4 + k * 5) % 10)
                Le.put(x, y, 0.7 - 0.15 * k)
        if i == 0:                                         # 새 획 끝에서 튀는 불꽃
            st = S[-1]
            ex, ey = ox + st[-1][0], oy + st[-1][1]
            for a in range(6):
                ang = -math.pi / 2 + (a - 2.5) * 0.55
                Lh.ray(ex, ey, ang, 2, 6 + (a % 2) * 2, 0.7, prof=FK.tp_tail(0.9), v=0.85)
        if n >= 5 and i >= 2:                              # 꽉 찬 표식: 획 사이 잔불이 더 밝게 숨 쉼
            Le.put(ox, oy - 8, 0.9 if i % 2 else 0.6)
        out.append(f.render())
    return out


def build_mark():
    rows = ["1", "2", "3", "4", "5"]
    frames = {r: mark_frames(int(r)) for r in rows}
    frames, piv = rk.fit_frames(frames, (MARK_C // 2, MARK_C - 16), margin=2, step=4)
    meta = dict(weapon="dagger", rowsAre="stacks", rowBy="stack", sizes=rows,
                directionsNote="directions 칸에 스택 수(1~5)를 넣었다 — 행 = 낙인 스택. 방향으로 고르지 말 것(회전·반전 없음)",
                anchor="enemy_head", pivot={"x": piv[0], "y": piv[1]},
                pivotNote="pivot = 표식 아래 가운데. 적 머리 위(적 시트 윗변 + 여백 8 논리 px 권장)에 놓는다. 몸에 붙이고 싶으면 anchor 를 enemy_body(몸 중심)로 — 그림은 같다",
                rotate=False, depth="above", followTarget=True,
                phaseFrames={"stamp": [0, 1], "loop": [2, 5]}, loopRange=[2, 5],
                playRule="스택이 오를 때마다 그 스택 행의 열 0→1 을 1회 재생한 뒤 열 2~5 를 루프. 스택이 그대로면 루프만. 기폭·과열 폭발·대상 사망 때 지움",
                glowFrames=[0], glowRule="53라운드 Q65: 백열(A26)은 새 획이 지져지는 열 0(타격 판정 순간)만. 그 밖은 A25 이하 — 빌드 검사 통과",
                design="56라운드 Q16 낙인 — 붓으로 지진 셈 획(1~4 세로 획, 5 = 가로질러 긋는 획 = '꽉 참'). 새 획은 지져지는 순간 뜨겁게 번쩍, 남은 획은 호박 잔불로 깜빡이고 불티가 오른다",
                keyArt="parts/art/work/gemini/weapon_moves/raw_dagger_A2.jpg 패널 3(sheet_dagger 3번)",
                sizeNote="화면 약 %d×%d 논리 px — 적 결사병(화면 64×88) 머리 위에서 읽히는 크기" % (frames["1"][0].width // 2, frames["1"][0].height // 2))
    return rk.write_sheet("dagger_brand_mark", rk.OUT_FX, rows, frames, MARK_MS, meta, glow=[0], loop=False)


# =============================================================================
# 기폭 폭발
# =============================================================================
BURST_C = 260
BURST_MS = [40, 40, 50, 60, 70, 80, 100, 120]
BURST_R = {"s": 34, "m": 46, "l": 60}
BURST_N = {"s": 2, "m": 4, "l": 5}


def burst_frames(size, seed):
    R = BURST_R[size]
    n = BURST_N[size]
    c = BURST_C / 2
    rng = random.Random(seed)
    out = []
    D = W.Debris(seed)
    for k in range(10 + 4 * n):
        a = rng.uniform(0, 2 * math.pi)
        sp = rng.uniform(0.35, 0.6) * R / 3
        D.spawn("ember", (math.cos(a) * R * 0.3, math.sin(a) * R * 0.3 * 0.8), (math.cos(a) * sp, math.sin(a) * sp * 0.8 - 2),
                born=1, life=5, size=rng.uniform(2.0, 4.0), v=rng.uniform(0.7, 1.0), g=1.1)
    for k in range(6 + 2 * n):
        a = rng.uniform(0, 2 * math.pi)
        sp = rng.uniform(0.2, 0.45) * R / 3
        D.spawn("flake", (math.cos(a) * R * 0.4, math.sin(a) * R * 0.3), (math.cos(a) * sp, math.sin(a) * sp * 0.7 - 1.5),
                born=2, life=6, size=rng.uniform(1.2, 2.2), v=rng.uniform(0.6, 1.0), g=0.8)
    T = W.T("any", c, c)
    S = strokes(n)
    blobs = [(0, 0, 0.5)] + [(math.cos(a) * rng.uniform(0.3, 0.5), math.sin(a) * rng.uniform(0.25, 0.4), rng.uniform(0.22, 0.34))
                             for a in [k * 2 * math.pi / 6 + rng.uniform(-0.3, 0.3) for k in range(6)]]
    puffs = [(math.cos(a) * rng.uniform(0.45, 0.75), math.sin(a) * rng.uniform(0.3, 0.55), rng.uniform(0.17, 0.3))
             for a in [k * 2 * math.pi / 8 + rng.uniform(-0.35, 0.35) for k in range(8)]]
    for i in range(len(BURST_MS)):
        f = rk.frame(BURST_C, BURST_C)
        Ls = f.L([rk.S0, rk.S1, rk.S2])                    # 연기
        Lf = f.L([rk.A17, rk.A18, rk.A19, rk.A21, rk.A23, rk.A25])
        Lh = f.L([rk.A25, rk.A26, rk.X1, rk.X0])
        Lr = f.L([rk.A18, rk.A19, rk.A21, rk.A23])
        Le = f.L([rk.A19, rk.A21, rk.A23])
        Lk = f.L([rk.S0, rk.S1, rk.S2, rk.S3])
        if i == 0:                                         # 셈 획이 부풀며 갈라짐(아직 판정 전)
            for st in S:
                draw_stroke(Lf, [(x * 1.7, y * 1.7 + 14) for x, y in st], c, c, 2.0, 0.95)
        elif i == 1:                                       # 폭발 판정 — 백열 핵 + 획 방향 빛살
            Lh.disc(c, c, R * 0.17, R * 0.14, v=1.0, edge=0.3)
            for dx, dy, rr in blobs[:5]:
                Lf.puff(c + dx * R * 0.55, c + dy * R * 0.55, rr * R * 0.6, v=0.9, ry=rr * R * 0.5)
            for k in range(8):
                a = k * math.pi / 4 + 0.2
                Lh.ray(c, c, a, R * 0.2, R * (0.75 if k % 2 else 0.55), 1.4, prof=FK.tp_tail(0.8), v=0.9)
        elif i == 2:                                       # 불덩이: 겹친 덩이(원판 아님) + 끊긴 충격 호
            for k, (dx, dy, rr) in enumerate(blobs):
                Lf.puff(c + dx * R, c + dy * R, rr * R, v=0.95 - 0.08 * (k % 3), ry=rr * R * 0.85, light=0.45)
            Lh.puff(c + 1, c - 2, R * 0.16, v=0.75, ry=R * 0.12)
            Lr.arc(c, c, R * 0.98, R * 0.8, 0, 2 * math.pi, 1.5, dash=(7, 0.7, 0.05), v=0.9)
        elif i == 3:
            for k, (dx, dy, rr) in enumerate(puffs):
                Ls.puff(c + dx * R, c + dy * R - 3, rr * R, v=0.9 - 0.1 * (k % 2), ry=rr * R * 0.8)
            for k, (dx, dy, rr) in enumerate(blobs[:4]):
                Lf.puff(c + dx * R * 0.7, c + dy * R * 0.7 - 2, rr * R * 0.7, v=0.7, ry=rr * R * 0.6)
            Lr.arc(c, c, R * 1.08, R * 0.88, 0, 2 * math.pi, 1.1, dash=(9, 0.4, 0.1), v=0.7)
        else:
            k2 = (i - 4) / 3.0
            for k, (dx, dy, rr) in enumerate(puffs):
                if k2 > 0.5 and k % 3 == 0:
                    continue
                Ls.puff(c + dx * R * (1 + 0.35 * k2), c + dy * R * (1 + 0.2 * k2) - 6 - 16 * k2 - 3 * (k % 2),
                        rr * R * (1 - 0.35 * k2), v=0.85 - 0.3 * k2, ry=rr * R * (1 - 0.35 * k2) * 0.8)
            if i == 4:
                Lf.puff(c, c - 5, R * 0.22, v=0.5, ry=R * 0.18)
        D.draw(f, T, {"ember": Le, "flake": Lk}, i)
        out.append(f.render())
    return out


def build_burst():
    rows = ["s", "m", "l"]
    frames = {r: burst_frames(r, 61 + k) for k, r in enumerate(rows)}
    frames, piv = rk.fit_centered(frames, (BURST_C // 2, BURST_C // 2))
    meta = dict(weapon="dagger", rowsAre="sizes", rowBy="stack", sizes=rows,
                sizeInfo={"s": {"stacks": [1, 2], "radiusPx": BURST_R["s"]}, "m": {"stacks": [3, 4], "radiusPx": BURST_R["m"]},
                          "l": {"stacks": [5], "radiusPx": BURST_R["l"]}},
                directionsNote="directions 칸에 크기 키(s·m·l)를 넣었다 — 행 = 낙인 스택으로 고른 크기. 방향으로 고르지 말 것",
                anchor="hitbox_center", pivot={"x": piv[0], "y": piv[1]}, pivotNote="pivot = 폭발 중심(적 몸 중심). radiusPx = 그림 반경(도트) — 판정 반경은 시스템 데이터",
                rotate=False, depth="above", spawn="brand_detonate",
                spawnNote="그림자 걸음으로 낙인 적의 등 뒤에 선 순간(기폭) 1회 + 과열 100% 일괄 폭발 때 낙인 적마다 1회(가까운 적부터 40ms 간격 권장)",
                impactFrame=1, glowFrames=[1, 2], frameRoles=["셈 획이 부풀어 갈라짐", "폭발(판정) 백열 핵·빛살", "불덩이·충격 고리", "연기 고리·끊긴 고리",
                                                            "연기 오름", "연기", "연기", "사라짐"],
                shakeHint={"s": {"px": 2, "ms": 80}, "m": {"px": 3, "ms": 100}, "l": {"px": 5, "ms": 130}},
                light={"color": "#e2a33c", "radius": 120, "intensity": 0.9, "frames": [1, 2, 3]},
                design="56라운드 Q16 낙인 기폭 — 적에게 지진 셈 획이 부풀며 갈라졌다가 백열 핵으로 터지고, 호박 불덩이·충격 고리 → 회색 재 연기·불티·재 조각",
                keyArt="parts/art/work/gemini/weapon_moves/raw_dagger_B.jpg 패널 4")
    return rk.write_sheet("dagger_brand_burst", rk.OUT_FX, rows, frames, BURST_MS, meta, glow=[1, 2])


# =============================================================================
# 과열 100%
# =============================================================================
OH_C = 360
OH_MS = [40, 40, 50, 60, 70, 80, 90, 110]
OH_R = 92


def overheat_frames(seed=71):
    c = OH_C / 2
    cy = c + 10                                            # 바닥 고리 중심(발)
    ky = 0.55                                              # 바닥 눌림
    out = []
    rng = random.Random(seed)
    tongues = [(k * 2 * math.pi / 22 + rng.uniform(-0.12, 0.12), rng.uniform(0.35, 1.0), rng.uniform(-1, 1)) for k in range(22)]
    sparks = [(rng.uniform(0, 2 * math.pi), rng.uniform(0.6, 1.0)) for _ in range(18)]
    for i in range(len(OH_MS)):
        f = rk.frame(OH_C, OH_C)
        Ls = f.L([rk.S0, rk.S1, rk.S2])
        Lf = f.L([rk.A18, rk.A19, rk.A21, rk.A23, rk.A25])
        Lh = f.L([rk.A25, rk.A26, rk.X1, rk.X0])
        Lr = f.L([rk.A17, rk.A18, rk.A19, rk.A21])
        Le = f.L([rk.A19, rk.A21, rk.A23])
        chest = (c, cy - 40)
        if i == 0:                                         # 몸 속 열이 터짐(판정) — 백열은 작은 핵만
            Lh.disc(chest[0], chest[1], 3.5, 4.5, v=1.0, edge=0.5)
            for k in range(7):
                Lf.ray(chest[0], chest[1], -math.pi / 2 + (k - 3) * 0.45, 5, 16 + (k % 2) * 8, 1.4, prof=FK.tp_tail(0.8), v=0.95)
            Lr.arc(c, cy, OH_R * 0.25, OH_R * 0.25 * ky, 0, 2 * math.pi, 1.6, dash=(10, 0.7, 0.0), v=0.95)
        else:
            k = (i - 1) / (len(OH_MS) - 2)
            r = OH_R * (0.4 + 0.75 * k ** 0.7)
            v = 1.0 - 0.7 * k
            if i <= 4:                                     # 바닥을 따라 퍼지는 불꽃 혀(바깥으로 기움, 키 제각각)
                for a, s_, lean in tongues:
                    front = math.sin(a) > 0
                    x, y = c + math.cos(a) * r, cy + math.sin(a) * r * ky
                    h = (6 + 18 * s_) * (1 - 0.55 * k) * (1.0 if front else 0.65)
                    ox = math.cos(a) * 5 + lean * 2
                    Lf.stroke([(x, y), (x + ox * 0.5, y - h * 0.5), (x + ox, y - h)], (3.4 if front else 2.2) * (1 - 0.3 * k),
                              prof=FK.tp_tail(0.8), v=v * (1.0 if front else 0.8), vprof=lambda u: 1 - 0.75 * u)
                Lr.arc(c, cy, r * 0.97, r * 0.97 * ky, 0, math.pi, 2.0, dash=(14, 0.8, 0.1 * i), v=v)       # 앞쪽 반 굵게
                Lr.arc(c, cy, r * 0.97, r * 0.97 * ky, math.pi, 2 * math.pi, 1.2, dash=(14, 0.6, 0.3 + 0.1 * i), v=v * 0.8)
                for a, sp in sparks:                       # 바깥으로 튀는 불티
                    rr = r * (1.05 + 0.25 * sp)
                    W.ember(Le, c + math.cos(a) * rr, cy + math.sin(a) * rr * ky - 6 * sp, math.cos(a), math.sin(a) * ky,
                            3.0 * (1 - 0.4 * k), w=0.6, v=0.9 - 0.4 * k)
                if i == 1:
                    Lh.disc(chest[0], chest[1], 2.5, 3.0, v=0.85, edge=0.6)
            else:                                          # 끊긴 고리 → 재 김
                Lr.arc(c, cy, r, r * ky, 0, 2 * math.pi, 1.2, dash=(12, 0.4, k), v=0.6)
                for j in range(10):
                    a = j * 2 * math.pi / 10 + 0.3 + rng.uniform(-0.1, 0.1)
                    rad = 6 + 3 * W.h2(j, 2, 9) - 3 * k
                    Ls.puff(c + math.cos(a) * r * 0.9, cy + math.sin(a) * r * ky * 0.9 - 6 - 12 * k - 4 * W.h2(j, 5, 9), rad,
                            v=0.8 - 0.3 * k, ry=rad * 0.8)
        out.append(f.render())
    return out


def build_overheat():
    frames = {"any": overheat_frames()}
    frames, piv = rk.fit_frames(frames, (OH_C // 2, OH_C // 2 + 10))
    meta = dict(weapon="dagger", anchor="player_pivot", pivot={"x": piv[0], "y": piv[1]},
                pivotNote="pivot = 주인공 발. 바닥 고리(세로 0.55 눌림) + 가슴에서 터지는 열", rotate=False, depth="above",
                spawn="overheat_full", impactFrame=0, glowFrames=[0, 1], radiusPx=OH_R,
                spawnNote="56라운드 Q19: 과열 100% 순간 1회. 주변 낙인 적의 폭발은 각 적에 dagger_brand_burst(스택 크기 행)를 이 시트 열 1 시작부터 가까운 순서로",
                frameRoles=["가슴의 열이 터짐(판정)", "불꽃 고리 퍼짐", "퍼짐", "퍼짐", "퍼짐(식음)", "끊긴 고리·재 김", "재 김", "사라짐"],
                light={"color": "#e2a33c", "radius": 180, "intensity": 1.0, "frames": [0, 1, 2, 3]},
                shakeHint={"px": 4, "ms": 140}, coolSheet="dagger_overheat_cool",
                design="56라운드 Q19 과열 100% — 몸 안의 열이 가슴에서 터지고 발밑을 따라 불꽃 혀 고리가 퍼졌다가 끊겨 재 김으로 식음")
    return rk.write_sheet("dagger_overheat_burst", rk.OUT_FX, ["any"], frames, OH_MS, meta, glow=[0, 1])


COOL_MS = [110] * 6


def cool_frames():
    C = 140
    out = []
    for i in range(6):
        f = rk.frame(C, C)
        Ls = f.L([rk.S0, rk.S1, rk.S2])
        Le = f.L([rk.A18, rk.A19])
        for k, (x0, y0) in enumerate([(-14, -64), (12, -70), (-4, -84), (20, -46), (-22, -40)]):
            ph = (i / 6.0 + k * 0.37) % 1.0
            x = C / 2 + x0 + 3 * math.sin(ph * 6.28 + k)
            y = C - 10 + y0 - 26 * ph
            r = 4.5 + 3.0 * ph
            Ls.puff(x, y, r, v=0.85 - 0.5 * ph, ry=r * 0.8)
            if k < 2 and ph < 0.5:
                Le.put(x + 1, y + r + 2, 0.8)
        out.append(f.render())
    return out


def build_cool():
    frames = {"any": cool_frames()}
    frames, piv = rk.fit_frames(frames, (70, 130))
    meta = dict(weapon="dagger", anchor="player_pivot", pivot={"x": piv[0], "y": piv[1]}, pivotNote="pivot = 주인공 발",
                rotate=False, depth="above", followTarget=True, glowFrames=[],
                playRule="과열 식는 동안(잠깐 느려짐) 루프. 끝나면 마지막 열에서 끔(반투명 금지)",
                design="56라운드 Q19 식힘 — 어깨·팔에서 회색 재 김이 피어올라 흩어짐, 어두운 불씨 한두 점")
    return rk.write_sheet("dagger_overheat_cool", rk.OUT_FX, ["any"], frames, COOL_MS, meta, glow=[], loop=True)


def build():
    return [build_mark()[1]["action"], build_burst()[1]["action"], build_overheat()[1]["action"], build_cool()[1]["action"]]


if __name__ == "__main__":
    print(build())
