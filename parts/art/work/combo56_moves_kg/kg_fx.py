"""E1 이펙트 — 새 기본기 6종의 fx v3 (56라운드 Q11 붓획 · Q5 땅 충격 · 재·호박만).

  katana_counter                   간파 반격 — 가늘고 날카로운 袈裟 붓 한 획(130°)
  katana_iai                       대치 일격 — 앞을 비스듬히 가로지르는 가는 일자 붓획 → 잔심 동안 남음 → 납도 딸깍에 터짐
  katana_iai_ready                 대치 유지 0.5초 '준비됨' — 칼집 입구 작은 반짝임(1행 any)
  greatsword_tackle                어깨 태클 — 어깨 앞 짧은 충격 붓획 2 + 뒤로 흐르는 재 줄 + 발밑 흙먼지
  greatsword_brace_upswing(_ember) 버티기 올려베기 — 앞 바닥에서 머리 위로 올려 그은 굵은 붓획(+흙 퍼 올림) · _ember = 울분 잔불 판
  greatsword_brace_absorb          버티는 중 피격 — 몸에서 재 조각이 튀어 떨어짐(1행 any)
  greatsword_leap_slam             공중제비 — 칼끝이 그리는 열린 나선 붓획(도약 출발 자리 고정, 앞으로 나가며 한 바퀴 반)
  greatsword_leap_slam_land        착지 내려찍기 — 세로 붓획 + 지면 붓획 + 금(균열은 greatsword_ground_crack 재사용)
  greatsword_guard_rush            막다가 떼면 돌진 — 칼끝이 바닥에 판 홈(돌진 출발 자리 고정) + 끝 흙 무더기

좌표: 로컬 '오른쪽 보기'(x = 조준, y = 화면 아래, 원점 = 판정 원점 = 피벗 위 40 도트) → fx56.TA 로 방향 회전(대검 8행 = 작업 B 행 순서).
흰 픽셀(X0/X1·A26)은 glowFrames(판정 순간)의 획 머리 몇 도트만 — fx56.write 가 검사.
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "combo56_fx")))
import fx56 as F  # noqa: E402  (combo56_fx — TA · frame · arc_frames · vertical_frames · write)
import brush as BR  # noqa: E402
from brush import W, FK  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
OUT_FX = os.path.join(ROOT, "assets/sprites/fx/v3")
P3 = os.path.join(ROOT, "assets/sprites/player/v3")
SRC = "parts/art/work/combo56_moves_kg/build.py fx (56라운드 Q21·Q22·Q40 새 기본기 fx — 작업 E1)"
F.SRC = SRC
F.VERSION = "v3-r56-e1"
HIT_UP = F.HIT_UP                       # 40
GROUND = HIT_UP                         # 로컬 화면 y: 원점 아래 40 = 발(바닥)
RK = 152.0                              # 칼 R 38 월드 px
RG = 204.0                              # 대검 R 51 월드 px
DIRS4, DIRS8 = F.DIRS4, F.DIRS8
EFFECT_RULE = ("56라운드 Q11: 붓으로 그은 한 획(시작 가늘고·가운데 굵고·끝 갈라짐) — 닫힌 원 금지. 재·호박만, 백열은 판정 프레임의 획 머리 몇 도트만. "
               "판정 밖 프레임은 A25(#eecc78) 이하")


def body(name):
    return json.load(open(os.path.join(P3, "player_%s.json" % name), encoding="utf-8"))


def starts(ms):
    s, t = [], 0
    for m in ms:
        s.append(t)
        t += m
    return s


def zpts(t, pts):
    """[(x, y, z)] 로컬 → 화면(z = 위)."""
    out = []
    for x, y, z in pts:
        sx, sy = t((x, y))
        out.append((sx, sy - z))
    return out


# =============================================================================
# 칼 — 간파 반격 · 대치 일격 · 준비 반짝임
# =============================================================================
COUNTER_MS = [30, 20, 30, 70, 80, 90]


def counter_frames(d):
    return F.arc_frames("katana", d, round(RK * 1.1, 1), -80, 50, 7.5, (46, 4), seed=401)


IAI_MS = [30, 30, 40, 80, 80, 70, 60, 60, 70, 80, 90]
IAI_GLOW = [1, 2]
IAI_BURST = 7


def iai_frames(d, line, seed=411):
    near, far, half, z0, z1 = line["nearR"], line["farR"], line["halfWidthR"], line["heightDots"][0], line["heightDots"][1]
    t = F.TA(d, *F.CO)
    p0 = (RK * near, -RK * half)
    p1 = (RK * far, RK * half)
    n = 60
    pts = []
    for i in range(n + 1):
        u = i / n
        x = p0[0] + (p1[0] - p0[0]) * u
        y = p0[1] + (p1[1] - p0[1]) * u
        bow = 5.0 * math.sin(math.pi * u)                     # 아주 약한 휨(붓 떨림)
        pts.append((x + bow, y, z0 + (z1 - z0) * u + 2.0 * math.sin(math.pi * u)))
    S = BR.Stroke(zpts(t, pts), 6.5, seed=seed, peak=0.42, dry_from=0.78, split=1.8, drops=6, start_w=0.12, end_w=0.5, lanes=5)
    for ln in S.lanes:
        ln["streak"] = 0.9 + 0.1 * ln["h"]
    rng = random.Random(seed)
    cuts = []
    for j, u in enumerate((0.27, 0.52, 0.76)):
        cx = p0[0] + (p1[0] - p0[0]) * u + rng.uniform(-4, 4)
        cy = p0[1] + (p1[1] - p0[1]) * u
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0]) + math.radians((1 if j % 2 else -1) * rng.uniform(55, 70))
        ln = rng.uniform(26, 36)
        z = z0 + (z1 - z0) * u
        a = (cx - math.cos(ang) * ln * 0.5, cy - math.sin(ang) * ln * 0.5, z)
        b = (cx + math.cos(ang) * ln * 0.5, cy + math.sin(ang) * ln * 0.5, z)
        m = ((a[0] + b[0]) / 2 + 2, (a[1] + b[1]) / 2, z)
        cuts.append(BR.Stroke(zpts(t, [a, m, b]), 4.0, seed=seed + 10 + j, peak=0.4, dry_from=0.6, split=1.4, drops=3,
                              start_w=0.15, end_w=0.45, lanes=4))
    out = []
    for i in range(len(IAI_MS)):
        fr = F.frame(t)
        Lf = fr.L(BR.FLAKE)
        Lb = fr.L(BR.INK_K)
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        if i == 0:
            S.draw(Lb, head=0.15, vmax=0.6, drops=False)
        elif i in (1, 2):
            S.draw(Lb, head=0.7 if i == 1 else 1.0, vmax=0.9, hot=True, Lhot=Lh, drops=(i == 2))
        elif i < IAI_BURST:                                   # 잔심 — 남은 가는 선이 식으며 떨림
            S.draw(Lb, head=1.0, vmax=0.7 - 0.03 * (i - 3) + (0.03 if i == 5 else 0), wk=0.72, fall=1 + i - 3)
        elif i == IAI_BURST:                                  # 납도 딸깍 — 터짐(연출, 백열 없음)
            S.draw(Lb, head=1.0, vmax=0.88, wk=1.3, drops=True, fall=4)
            for c in cuts:
                c.draw(Lb, head=1.0, vmax=0.86)
            _line_burst(Lf, Le, S, seed, 0.0)
        else:
            k = (i - IAI_BURST) / (len(IAI_MS) - 1 - IAI_BURST)
            S.draw(Lb, head=1.0, tail=0.1 + 0.7 * k, vmax=0.78 - 0.2 * k, wk=1.1 - 0.4 * k, k=min(1.0, 0.35 + 0.65 * k), fall=4 + 8 * k)
            for c in cuts:
                c.draw(Lb, head=1.0, tail=0.1 + 0.5 * k, vmax=0.76 - 0.25 * k, wk=1 - 0.3 * k, k=min(1.0, 0.3 + 0.7 * k), fall=3 + 6 * k)
            S.flakes(Lf, k, 0.05, 1.0, 9, size=1.6, fall=12.0, seed=i)
            _line_burst(Lf, Le, S, seed, 0.3 + 0.7 * k)
        out.append(fr.render())
    return out


def _line_burst(Lf, Le, S, seed, age):
    """선을 따라 재 조각이 튀어 오르고(나중엔 떨어짐) 불티 바늘이 흩어짐."""
    r = random.Random(seed + 3)
    for _ in range(16):
        s = r.uniform(0.05, 0.98)
        (x, y), _n = S.at(s)
        vx, vy = r.uniform(-0.5, 0.5), r.uniform(-1.0, -0.35)
        sp = r.uniform(6, 16)
        if age > 0.85 and r.random() < 0.5:
            continue
        W.flake(Lf, x + vx * sp * (0.4 + age) * 1.6, y + vy * sp * (0.4 + age) + 22 * age * age,
                r.uniform(1.0, 2.2) * (1 - 0.35 * age), r.uniform(0, 6), v=r.uniform(0.55, 1.0) * (1 - 0.3 * age))
    if age < 0.7:
        for _ in range(6):
            s = r.uniform(0.05, 0.98)
            (x, y), _n = S.at(s)
            a = r.uniform(-2.8, -0.35)
            dist = r.uniform(4, 12) * (1 + 1.5 * age)
            W.ember(Le, x + math.cos(a) * dist, y + math.sin(a) * dist + 8 * age * age, math.cos(a), math.sin(a),
                    r.uniform(2, 4) * (1 - 0.5 * age), w=0.6, v=0.9 - 0.4 * age)


READY_MS = [30, 40, 50, 60, 70]


def ready_frames():
    """칼집 입구 '준비됨' — 가는 가로 빛 한 줄 + 작은 네 갈래 반짝임(A25 이하). 원점 = 반짝임 중심."""
    t = F.TA("right", *F.CO)
    out = []
    cx, cy = F.CO
    for i in range(len(READY_MS)):
        fr = F.frame(t)
        Le = fr.L([W.A19, W.A21, W.A23, W.A25])
        Lf = fr.L(BR.FLAKE)
        k = i / (len(READY_MS) - 1)
        r = [3.0, 6.0, 5.0, 3.5, 2.0][i]
        v = [0.8, 1.0, 0.85, 0.6, 0.4][i]
        Le.star4(cx, cy, r, w=0.6, v=v)
        hl = [6, 14, 18, 12, 6][i]
        Le.stroke([(cx - hl, cy), (cx + hl, cy)], 0.7, prof=FK.tp_both(0.5, 0.5), v=0.75 * v)
        if i >= 2:
            rr = random.Random(7 + i)
            for _ in range(3):
                W.flake(Lf, cx + rr.uniform(-8, 8), cy + 3 + 6 * k * rr.uniform(0.6, 1.4), 1.0, rr.uniform(0, 6), v=0.7)
        out.append(fr.render())
    return out


# =============================================================================
# 대검 — 어깨 태클
# =============================================================================
TACKLE_MS = [40, 40, 50, 60, 70, 80]


def tackle_frames(d, seed=501):
    t = F.TA(d, *F.CO)
    zc = 30.0                                                     # 어깨 높이(원점 위)
    arcA = BR.Stroke(BR.arc_points(t, RG * 0.32, -50, 50, lambda s: zc + 6 * math.sin(math.pi * s)), 11.0, seed=seed,
                     peak=0.5, dry_from=0.7, split=1.2, drops=5, start_w=0.15, end_w=0.4)
    arcB = BR.Stroke(BR.arc_points(t, RG * 0.46, -34, 34, lambda s: zc + 4 * math.sin(math.pi * s)), 6.0, seed=seed + 1,
                     peak=0.5, dry_from=0.65, split=1.4, drops=4, start_w=0.15, end_w=0.4)
    streaks = []
    for j, (y, z, ln) in enumerate(((-12, 40, 104), (10, 12, 72))):
        streaks.append(BR.Stroke(zpts(t, [(-34, y, z), (-34 - ln * 0.5, y + 2, z + 3), (-34 - ln, y + 3, z + 2)]), 4.0, seed=seed + 5 + j,
                                 peak=0.15, dry_from=0.5, split=1.6, drops=2, start_w=0.6, end_w=0.3, lanes=4))
    rng = random.Random(seed)
    dust = [(rng.uniform(-70, 10), rng.uniform(-14, 14), rng.uniform(4, 9)) for _ in range(7)]
    out = []
    for i in range(len(TACKLE_MS)):
        fr = F.frame(t)
        Ld = fr.L(W.R_DUST)
        Lf = fr.L(BR.FLAKE_G)
        Lb = fr.L(BR.INK_G)
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        k = i / (len(TACKLE_MS) - 1)
        for x, y, r in dust:                                      # 발밑 흙먼지(바닥)
            sx, sy = t((x - 18 * k, y))
            if i < 5:
                Ld.cloud(sx, sy + GROUND - 2, r * (0.7 + 0.8 * k), v=0.7 * (1 - 0.5 * k), flat=0.55, seed=int(x * 10) % 97)
        if i == 0:                                                # 들이받는 순간(판정) — 충격 획 머리만 백열
            arcA.draw(Lb, head=1.0, vmax=0.9, hot=True, Lhot=Lh, drops=False)
            for s_ in streaks:
                s_.draw(Lb, head=1.0, vmax=0.62)
        elif i == 1:
            arcA.draw(Lb, head=1.0, vmax=0.86, wk=1.15)
            arcB.draw(Lb, head=1.0, vmax=0.8)
            for s_ in streaks:
                s_.draw(Lb, head=1.0, tail=0.3, vmax=0.55, k=0.3)
            _sparks(Le, t, RG * 0.36, zc, seed, 0.0)
        else:
            kk = (i - 1) / (len(TACKLE_MS) - 2)
            arcA.draw(Lb, head=1.0, tail=0.2 + 0.6 * kk, vmax=0.8 - 0.2 * kk, wk=1.1 - 0.35 * kk, k=kk, fall=2 + 8 * kk)
            arcB.draw(Lb, head=1.0, tail=0.2 + 0.6 * kk, vmax=0.74 - 0.2 * kk, wk=1 - 0.3 * kk, k=kk, fall=2 + 6 * kk)
            arcA.flakes(Lf, kk, 0.0, 1.0, 6, size=2.0, fall=10.0, seed=i)
            if kk < 0.6:
                _sparks(Le, t, RG * 0.36, zc, seed, kk)
        out.append(fr.render())
    return out


def _sparks(Le, t, x, z, seed, age):
    r = random.Random(seed * 3 + 1)
    for _ in range(6):
        a = math.radians(r.uniform(-60, 60))
        dist = r.uniform(8, 18) * (1 + 1.4 * age)
        sx, sy = t((x + math.cos(a) * dist, math.sin(a) * dist))
        sx0, sy0 = t((x, 0.0))
        vx, vy = sx - sx0, sy - sy0
        W.ember(Le, sx, sy - z + 10 * age * age, vx, vy, r.uniform(3, 5) * (1 - 0.4 * age), w=0.6, v=0.9 - 0.3 * age)


# =============================================================================
# 대검 — 버티기 올려베기(+울분 잔불) · 버티는 중 피격
# =============================================================================
UPSWING_MS = [40, 40, 50, 60, 70, 80]
UPSWING_GLOW = [1, 2]


def upswing_frames(d, ember=False, seed=521):
    t = F.TA(d, *F.CO)
    Rx, Rz = (RG * 0.9, 145.0) if ember else (RG * 0.75, 125.0)     # 앞 바닥 → 머리 위(세로 타원 — 몸 크기에 맞춤)
    cx, cz = RG * 0.05, 4.0
    lat = 30.0
    pts = []
    for i in range(121):
        phi = math.radians(-14 + 114 * i / 120)
        pts.append((cx + Rx * math.cos(phi), lat * math.cos(phi), max(-GROUND + 4, cz + Rz * math.sin(phi))))
    wmax = 26.0 if ember else 20.0
    ink = BR.INK_K if ember else BR.INK_G
    S = BR.Stroke(zpts(t, pts), wmax, seed=seed, peak=0.45, dry_from=0.72, split=1.3, drops=10 if ember else 7,
                  start_w=0.25, end_w=0.5)
    gx, gy = t((pts[0][0], pts[0][1]))
    gy = gy - pts[0][2]
    rng = random.Random(seed)
    clods = [(rng.uniform(-0.6, 0.6), rng.uniform(-2.4, -1.1), rng.uniform(1.4, 2.8)) for _ in range(10)]
    out = []
    for i, (kind, p) in enumerate(F.PLAN_ARC):
        fr = F.frame(t)
        Ld = fr.L(W.R_DUST)
        Lf = fr.L(BR.FLAKE_G)
        Lb = fr.L(ink)
        Le = fr.L([W.A19, W.A21, W.A23, W.A25] if ember else [W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        k = i / 5.0
        # 퍼 올린 흙(시작점에서 위로 튀었다 떨어짐)
        if i >= 1:
            age = (i - 1) / 4.0
            for vx, vy, sz in clods:
                x = gx + vx * 26 * (0.4 + age)
                y = gy + vy * 22 * (0.3 + age) + 40 * age * age
                W.flake(Lf, x, y, sz * (1 - 0.3 * age), vx * 5, v=0.85 - 0.3 * age)
            if i <= 3:
                Ld.cloud(gx, gy + 4, 7 + 7 * age, v=0.6 * (1 - age), flat=0.5, seed=i)
        if kind == "pre":
            S.draw(Lb, head=p["head"], vmax=0.6, drops=False)
        elif kind == "draw":
            S.draw(Lb, head=p["head"], vmax=0.9, hot=True, Lhot=Lh)
        else:
            kk = p["k"]
            S.draw(Lb, head=1.0, tail=0.12 + 0.62 * kk, vmax=0.86 - 0.2 * kk, wk=1 - 0.28 * kk, k=kk, fall=3 + 9 * kk)
            S.flakes(Lf, kk, 0.0, 0.12 + 0.7 * kk, 7, size=2.2, fall=10.0, seed=i)
        if ember and i >= 1:                                       # 울분 잔불 — 획을 따라 불티가 떠오르고 오래 남음
            r = random.Random(seed + 77)
            if kind == "decay":                                    # 마른 자리에 남아 깜박이는 잔불 알갱이
                rc = random.Random(seed + 91 + i)
                for j in range(26):
                    s = rc.uniform(0.02, 0.98)
                    (x, y), (nx, ny) = S.at(s)
                    off = rc.uniform(-0.5, 0.5) * wmax
                    if rc.random() < 0.25 + 0.5 * p["k"]:
                        continue
                    Le.stamp(x + nx * off, y + ny * off + 6 * p["k"] * rc.random(), rc.uniform(0.7, 1.4), rc.uniform(0.55, 0.95), soft=0)
            for j in range(34):
                s = r.uniform(0.05, 0.98)
                if kind == "draw" and s > p["head"]:
                    continue
                (x, y), _n = S.at(s)
                age = max(0.0, k - 0.15)
                W.ember(Le, x + r.uniform(-8, 8), y - 14 * age * r.uniform(0.6, 1.6) + r.uniform(-6, 6), r.uniform(-0.3, 0.3), -1,
                        r.uniform(2.5, 5) * (1 - 0.3 * age), w=0.7, v=(0.95 if i in UPSWING_GLOW else 0.82) - 0.25 * age)
        out.append(fr.render())
    return out


ABSORB_MS = [30, 40, 50, 60, 70]


def absorb_frames(seed=531):
    """버티는 중 피격 — 몸 가운데(원점 위 30)에서 재 조각이 바깥으로 튀어 떨어지고 짧은 호박 금 반짝임(A25 이하)."""
    t = F.TA("right", *F.CO)
    cx, cy = F.CO[0], F.CO[1] - 30
    r = random.Random(seed)
    parts = [(r.uniform(0, 2 * math.pi), r.uniform(14, 26), r.uniform(1.4, 2.6)) for _ in range(14)]
    out = []
    for i in range(len(ABSORB_MS)):
        fr = F.frame(t)
        Lf = fr.L(BR.FLAKE + [W.S3])
        Le = fr.L([W.A19, W.A21, W.A23, W.A25])
        k = i / (len(ABSORB_MS) - 1)
        for a, sp, sz in parts:
            dist = sp * (0.35 + 0.9 * k)
            W.flake(Lf, cx + math.cos(a) * dist * 1.2, cy + math.sin(a) * dist * 0.8 + 30 * k * k, sz * (1 - 0.3 * k), a, v=0.95 - 0.3 * k)
        if i <= 2:
            for j in range(3):
                a = math.radians(-60 + 60 * j + 25 * i)
                ln = [7, 10, 6][i]
                Le.stroke([(cx, cy), (cx + math.cos(a) * ln, cy + math.sin(a) * ln)], 0.8, prof=FK.tp_head(0.7), v=[0.9, 1.0, 0.7][i])
        out.append(fr.render())
    return out


# =============================================================================
# 대검 — 공중제비 도약 찍기(나선 칼끝 붓획 · 착지)
# =============================================================================
LEAP_MS = [50, 50, 50, 50, 40, 60, 70, 80]          # body f3~f7 · 착지 f8 · 소멸 2
TIP_R = 92.0
TRAIL_MS = 70                                       # 꼬리 길이(시간) — 늘 반 바퀴 미만만 보이게(닫힌 원 금지)


def leap_trail_frames(d, bj, seed=541):
    t = F.TA(d, *F.CO)
    st = starts(bj["frameDurationsMs"])
    ms = bj["frameDurationsMs"]
    air = bj["airOffsetPx"]["byFrame"]
    lp = bj["leapPx"]
    t_take, t_land = st[2], st[bj["impactFrame"]]
    mid = [st[i] + ms[i] / 2.0 for i in range(len(ms))]
    ang_key = [(mid[2], 114.0), (mid[3], 0.0), (mid[4], -90.0), (mid[5], -180.0), (mid[6], -242.0), (mid[7], -325.0), (t_land, -420.0)]
    air_key = [(st[2], 0.0)] + [(mid[i], float(air[i])) for i in range(2, bj["impactFrame"])] + [(t_land, 0.0)]

    def interp(keys, x):
        if x <= keys[0][0]:
            return keys[0][1]
        for (x0, y0), (x1, y1) in zip(keys, keys[1:]):
            if x <= x1:
                return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        return keys[-1][1]
    T0, T1 = mid[2], t_land - 6
    samples, times = [], []
    tt = T0
    while tt <= T1:
        a = math.radians(interp(ang_key, tt))
        fwd = lp["dots"] * max(0.0, min(1.0, (tt - t_take) / (t_land - t_take)))
        zc = 62.0 + interp(air_key, tt) - HIT_UP
        x = fwd + 6 + TIP_R * math.cos(a)
        z = zc + TIP_R * 1.0 * math.sin(a)
        y = 16.0 * math.sin(a)
        samples.append((x, y, max(-GROUND + 2, z)))
        times.append(tt)
        tt += 1.5
    S = BR.Stroke(zpts(t, samples), 15.0, seed=seed, peak=0.55, dry_from=0.9, split=0.9, drops=0, start_w=0.15, end_w=0.7)
    n = len(times)

    def s_at(T):
        if T <= times[0]:
            return 0.0
        if T >= times[-1]:
            return 1.0
        return (T - times[0]) / (times[-1] - times[0]) * 1.0
    # 시트 시각 0 = body f3 시작(st[3])
    t0 = st[3]
    ends = [t0 + sum(LEAP_MS[:i + 1]) for i in range(len(LEAP_MS))]
    out = []
    for i, e in enumerate(ends):
        fr = F.frame(t)
        Lf = fr.L(BR.FLAKE_G)
        Lb = fr.L(BR.INK_G)
        Le = fr.L([W.A19, W.A21, W.A23])
        head = s_at(min(e, T1))
        if e <= t_land:
            tail = s_at(e - TRAIL_MS)
            S.draw(Lb, head=head, tail=tail, vmax=0.84, drops=False)
            if i >= 1:
                S.flakes(Lf, 0.3, max(0.0, tail - 0.08), tail + 0.02, 4, size=2.0, fall=8.0, seed=i)
        else:
            kk = (e - t_land) / (ends[-1] - t_land)
            tail = min(0.995, s_at(t_land - TRAIL_MS) + (1 - s_at(t_land - TRAIL_MS)) * (0.3 + 0.7 * kk))
            S.draw(Lb, head=1.0, tail=tail, vmax=0.78 - 0.2 * kk, wk=1 - 0.3 * kk, k=min(1.0, 0.3 + 0.7 * kk), drops=False)
            S.flakes(Lf, kk, 0.6, 1.0, 6, size=2.0, fall=10.0, seed=i)
        if 0 < i <= 4:                                            # 칼끝에서 튀는 불티(A23 이하)
            (x, y), _n = S.at(head)
            r = random.Random(seed + i)
            for _ in range(3):
                a = r.uniform(0, 2 * math.pi)
                W.ember(Le, x + math.cos(a) * 6, y + math.sin(a) * 6, math.cos(a), math.sin(a), r.uniform(2, 4), w=0.6, v=0.8)
        out.append(fr.render())
    return out


LAND_PLAN = [("draw", dict(head=0.6)), ("impact", {}), ("decay", dict(k=0.33)), ("decay", dict(k=0.66)), ("decay", dict(k=1.0))]
LAND_MS = [40, 50, 60, 70, 90]


def land_frames(d):
    return F.vertical_frames(d, round(RG * 1.3, 1), wmax=20, heavy=1.3, seed=551, Rv=160.0, plan=LAND_PLAN)


# =============================================================================
# 대검 — 막다가 떼면 돌진(바닥 홈)
# =============================================================================
RUSH_MS = [40, 40, 40, 60, 90, 90, 100, 120]


def rush_frames(d, bj, seed=561):
    t = F.TA(d, *F.CO)
    st = starts(bj["frameDurationsMs"])
    dp = bj["dashPx"]
    L = dp["dots"]
    x0, lat = 84.0, 14.0                                          # 칼끝이 닿은 자리(출발 피벗 기준 앞 · 해부 오른쪽)
    xa, xb = x0 - 10, x0 + L + 10
    rng = random.Random(seed)
    groove = W.jag(rng, (xa, lat), (xb, lat + 3), n=14, amp=2.2)
    gpts = [(x, y + GROUND) for x, y in groove]                    # 바닥 높이
    rim = [(x, y - 3.0) for x, y in gpts]

    def scr(pts):
        out = []
        for x, y in pts:
            sx, sy = t((x, y - GROUND))
            out.append((sx, sy + GROUND))
        return out
    sg, sr = scr(gpts), scr(rim)
    dash_t = [st[i] + bj["frameDurationsMs"][i] for i in dp["frames"]]
    t0 = st[dp["frames"][0]]
    ends = [t0 + sum(RUSH_MS[:i + 1]) for i in range(len(RUSH_MS))]
    heap = (xb + 6, lat)
    out = []
    for i, e in enumerate(ends):
        fr = F.frame(t)
        Lg = fr.L([W.B0, W.B1, W.B2])
        Lr = fr.L([W.B2, W.B3, W.S2])
        Lc = fr.L([W.A18, W.A19, W.A21, W.A23])
        Lf = fr.L(BR.FLAKE_G)
        Le = fr.L([W.A19, W.A21, W.A23])
        Ld = fr.L(W.R_DUST)
        u = max(0.0, min(1.0, (e - t0) / (dp["endMs"] - t0)))
        k = 0.0 if i < 4 else (i - 3) / (len(RUSH_MS) - 4)
        n = max(2, int(len(sg) * u))
        Lg.stroke(sg[:n], 5.5, prof=FK.tp_both(0.15, 0.35), v=0.85 - 0.25 * k)
        Lr.stroke(sr[:n], 1.6, prof=FK.tp_both(0.2, 0.3), v=0.7 - 0.2 * k)
        cool = 0.9 - 0.75 * k
        if cool > 0.2:                                            # 갓 판 홈 속 달아오른 쇳빛(머리 쪽이 밝고 꼬리는 식음)
            seg = sg[max(0, n - 7):n] if i < 4 else sg[:n]
            Lc.stroke(seg, 1.4, prof=FK.tp_head(0.6), v=cool, dash=(7.0, 0.7, 0.0) if i >= 4 else None)
        hx, hy = sg[n - 1]
        if i < 4:                                                 # 칼끝 불티 · 흙 튐
            r = random.Random(seed + i)
            for _ in range(4):
                a = math.atan2(sg[n - 1][1] - sg[max(0, n - 4)][1], sg[n - 1][0] - sg[max(0, n - 4)][0]) + math.pi + r.uniform(-0.8, 0.8)
                W.ember(Le, hx + math.cos(a) * r.uniform(4, 12), hy + math.sin(a) * r.uniform(4, 12) - r.uniform(2, 8),
                        math.cos(a), math.sin(a) - 0.5, r.uniform(2.5, 4.5), w=0.6, v=0.85)
            for _ in range(3):
                W.flake(Lf, hx + r.uniform(-10, 4), hy - r.uniform(2, 10), r.uniform(1.2, 2.2), r.uniform(0, 6), v=0.8)
        if i >= 3:                                                # 끝 흙 무더기·먼지
            hs, hy2 = scr([(heap[0], heap[1] + GROUND)])[0]
            r = random.Random(seed + 50)
            for j in range(8):
                W.flake(Lf, hs + r.uniform(-10, 10), hy2 - r.uniform(0, 6) + 4 * k, r.uniform(1.6, 3.0) * (1 - 0.3 * k), r.uniform(0, 6),
                        v=0.85 - 0.3 * k)
            if k < 0.7:
                Ld.cloud(hs, hy2 - 2, 9 + 10 * k, v=0.65 * (1 - k), flat=0.5, seed=i)
        out.append(fr.render())
    return out


# =============================================================================
# 시트 표 · 메타
# =============================================================================
def common(pivot, origin):
    return dict(anchor="player_pivot", pivot={"x": pivot[0], "y": pivot[1]}, hitOriginInFrame={"x": origin[0], "y": origin[1]},
                pivotNote="pivot = 주인공 발(몸 피벗)에 맞춘다. 판정 원점 = pivot 위 40 도트(hitOriginInFrame)",
                effectRule=EFFECT_RULE, brushStroke=True, r56="56라운드 Q21·Q22·Q40 새 기본기(작업 E1)")


def spec_table():
    bk = {n: body(n) for n in ("katana_counter", "katana_iai", "greatsword_tackle", "greatsword_brace_upswing",
                               "greatsword_leap_slam", "greatsword_guard_rush")}
    T = {}
    b = bk["katana_counter"]
    hit = b["timingMs"]["hitAt"]
    T["katana_counter"] = dict(dirs=DIRS4, fn=counter_frames, ms=COUNTER_MS, glow=[1, 2], meta=dict(
        weapon="katana", bodySheet="player_katana_counter", spawn="body_ms", spawnAtMs=hit - COUNTER_MS[0], impactAtBodyMs=hit,
        impactFrame=1, hitShape=b["hitShape"],
        drawnArc=dict(fromDeg=-80, toDeg=50, radiusDots=round(RK * 1.1, 1), brushWidthDots=7.5, heightDots=[46, 4]),
        frameRoles=["pre(붓 끝 닿음)", "draw(머리 55% · 판정)", "draw(끝까지 · 붓털 갈라짐)", "decay", "decay", "decay(재)"],
        design="간파 반격 — 받아 흘린 직후 왼쪽 위에서 오른쪽 아래로 짧고 날카롭게 그은 가는 붓 한 획(1·2타보다 가늘고 짧음)",
        spawnRule="spawnAtMs = 몸 hitAt − frameDurationsMs[0]"))
    b = bk["katana_iai"]
    rel = b["releaseFrame"]
    st = starts(b["frameDurationsMs"])
    T["katana_iai"] = dict(dirs=DIRS4, fn=(lambda d, ln=b["drawnLine"]: iai_frames(d, ln)), ms=IAI_MS, glow=IAI_GLOW, meta=dict(
        weapon="katana", bodySheet="player_katana_iai", spawn="release", spawnAtMs=st[rel], spawnAtReleaseMs=0,
        spawnNote="좌클릭을 뗀 순간(몸 releaseFrame 시작)에 1회 — 주인공 발에 놓고 따라가지 않음(world 고정, 일격 선이 그 자리에 남음). "
                  "spawnAtMs 는 유지 루프 1회 기준 시트 시각",
        anchor="release_pivot", impactFrame=1, burstFrame=IAI_BURST, burstAtLineMs=sum(IAI_MS[:IAI_BURST]),
        burstNote="납도 딸깍(몸 clickFrame)과 같은 시각. 연출만(백열 없음) — 터짐에 피해를 주면 glowFrames 에 7 추가 가능",
        hitShape=b["hitShape"], depth="below_player",
        frameRoles=["pre", "draw(판정 · 머리 백열)", "draw(끝까지 · 판정)", "잔심 남은 선", "잔심(떨림)", "잔심", "잔심",
                    "납도 딸깍 — 터짐(교차 베기 자국)", "재로 부서짐", "재", "재"],
        design="대치 일격 — 발도와 동시에 앞을 비스듬히 가로지르는 가는 일자 붓획 → 잔심 동안 식으며 남음 → 칼을 넣는 딸깍에 교차 베기 자국과 함께 터짐"))
    T["katana_iai_ready"] = dict(dirs=["any"], fn=lambda d: ready_frames(), ms=READY_MS, glow=[], meta=dict(
        weapon="katana", bodySheet="player_katana_iai", anchor="koiguchi", spawn="hold_ready",
        anchorNote="몸 JSON koiguchiAnchors[방향][프레임](몸 시트 도트) 위치에 pivot 을 맞춘다(행 any — 방향 무관)",
        spawnNote="대치 유지가 readyAfterHoldMs(임시 500ms)에 닿을 때 1회", depth="above",
        frameRoles=["반짝 시작", "가장 밝음(A25)", "퍼짐", "식음", "사라짐"],
        design="칼집 입구에서 가는 가로 빛 한 줄 + 작은 네 갈래 반짝임 — '준비됨'(백열 없음, A25 이하)"))
    b = bk["greatsword_tackle"]
    T["greatsword_tackle"] = dict(dirs=DIRS8, fn=tackle_frames, ms=TACKLE_MS, glow=[0], meta=dict(
        weapon="greatsword", bodySheet="player_greatsword_tackle", spawn="body_ms", spawnAtMs=b["timingMs"]["hitAt"],
        spawnAlt="첫 적중(접촉) 순간에 띄워도 된다 — 빗나가면 생략 가능", impactFrame=0, followPlayer=True,
        anchorNote="주인공 발을 따라감(돌진 중 몸과 함께 이동)", hitShape=b["hitShape"],
        frameRoles=["들이받음(판정 · 충격 획 머리 백열)", "충격 획 둘 · 불티", "소멸", "소멸", "소멸", "재"],
        design="어깨 앞 짧은 충격 붓획 2(앞으로 볼록) + 몸 뒤로 흐르는 재 줄 3 + 발밑 흙먼지 — 칼 궤적 없음(어깨로 받음)"))
    b = bk["greatsword_brace_upswing"]
    hit = b["timingMs"]["hitAt"]
    for ember in (False, True):
        n = "greatsword_brace_upswing" + ("_ember" if ember else "")
        T[n] = dict(dirs=DIRS8, fn=(lambda d, e=ember: upswing_frames(d, ember=e)), ms=UPSWING_MS, glow=UPSWING_GLOW, meta=dict(
            weapon="greatsword", bodySheet="player_greatsword_brace_upswing", spawn="body_ms", spawnAtMs=hit - UPSWING_MS[0],
            impactAtBodyMs=hit, impactFrame=1,
            hitShape=dict(b["hitShape"], **({"lengthR": 1.5, "angleDeg": 60, "lengthPx": round(RG * 1.5, 1), "note": "울분 소모 판(임시) ×1.5 · 60°"}
                                             if ember else {})),
            variant=("rage" if ember else "base"), variantOf=("greatsword_brace_upswing" if ember else None),
            useWhen=("울분을 소모해 강화했을 때" if ember else "평소"),
            drawnArc=dict(fromDeg=-14, toDeg=100, forwardRadiusDots=round(RG * (0.9 if ember else 0.75), 1), heightRadiusDots=145 if ember else 125,
                          brushWidthDots=26 if ember else 20,
                          note="앞 바닥(−14°)에서 머리 위(100°)까지 세로 타원으로 올려 그은 획 — 위에서 보면 앞으로 뻗었다 몸 쪽으로 감기는 획"),
            frameRoles=["pre(앞 바닥에서 흙을 퍼 올림)", "draw(판정 · 획 머리 백열)", "draw(머리 위까지)", "decay", "decay", "decay(재)"],
            design=("울분 판 — 더 굵고 긴 호박 붓획, 획을 따라 잔불(불티)이 떠오르고 오래 남음" if ember
                    else "버티기 올려베기 — 앞 바닥에서 흙을 퍼 올리며 머리 위로 크게 올려 그은 굵은 흙·녹 붓획")))
    T["greatsword_brace_absorb"] = dict(dirs=["any"], fn=lambda d: absorb_frames(), ms=ABSORB_MS, glow=[], meta=dict(
        weapon="greatsword", bodySheet="player_greatsword_brace_upswing", spawn="on_hit_during_super_armor", followPlayer=True,
        spawnNote="몸 superArmorFrames 동안 맞을 때마다 1회(주인공 발 기준, 따라감)", depth="above",
        frameRoles=["맞음 — 호박 금 반짝", "재 조각 튐", "튐", "떨어짐", "사라짐"],
        design="버티는 몸에서 재 조각이 튀어 떨어지고 짧은 호박 금이 반짝 — 밀리지 않고 받아낸 느낌(A25 이하)"))
    b = bk["greatsword_leap_slam"]
    st = starts(b["frameDurationsMs"])
    T["greatsword_leap_slam"] = dict(dirs=DIRS8, fn=(lambda d, bb=b: leap_trail_frames(d, bb)), ms=LEAP_MS, glow=[], meta=dict(
        weapon="greatsword", bodySheet="player_greatsword_leap_slam", spawn="body_ms", spawnAtMs=st[3], anchor="leap_start_pivot",
        anchorNote="도약 출발(몸 leapPx.startMs) 순간의 주인공 발 위치에 고정(world) — 나선이 앞으로 나가며 그려짐(leapPx 48 월드 px 기준). "
                   "벽에 막혀 짧게 뛰면 생략하거나 그대로 둬도 됨(연출만)",
        bakedTravelDots=b["leapPx"]["dots"], airBaked=True, depth="above",
        frameRoles=["회전 90°(칼끝 앞)", "180°(칼끝 아래)", "270°(칼끝 뒤)", "머리 위 뒤", "내려침", "착지(나선 끝)", "소멸", "재"],
        design="공중제비 — 칼끝이 그리는 열린 나선 붓획(앞으로 나가며 한 바퀴 반 · 꼬리부터 말라 늘 반 바퀴 남짓만 보임, 닫힌 원 없음). 판정 없음(A25 이하)"))
    hit = b["timingMs"]["hitAt"]
    T["greatsword_leap_slam_land"] = dict(dirs=DIRS8, fn=land_frames, ms=LAND_MS, glow=[1], meta=dict(
        weapon="greatsword", bodySheet="player_greatsword_leap_slam", spawn="body_ms", spawnAtMs=hit - LAND_MS[0], impactAtBodyMs=hit,
        impactFrame=1, followPlayer=True, hitShape=b["hitShape"], groundCrack=b.get("groundCrack"),
        frameRoles=["내려옴", "착지 내려찍기(판정 · 지면 붓획)", "decay", "decay", "decay"],
        design="착지 내려찍기 — 세로 붓획 + 지면 붓획 + 금. 바닥 균열은 greatsword_ground_crack(차지 단계 m·m·l)을 같은 시각에 함께"))
    b = bk["greatsword_guard_rush"]
    T["greatsword_guard_rush"] = dict(dirs=DIRS8, fn=(lambda d, bb=b: rush_frames(d, bb)), ms=RUSH_MS, glow=[], meta=dict(
        weapon="greatsword", bodySheet="player_greatsword_guard_rush", spawn="body_ms", spawnAtMs=b["dashPx"]["startMs"],
        anchor="dash_start_pivot", depth="below_player",
        anchorNote="돌진 시작 순간의 주인공 발 위치에 고정(world). 홈 길이 = dashPx(56 월드 px) 기준 — 벽에 막히면 남은 칸은 그려지기 전에 끊어도 됨(마지막 프레임 그대로 짧게)",
        bakedTravelDots=b["dashPx"]["dots"],
        frameRoles=["홈 그어짐 1/4", "2/4", "3/4", "끝 — 흙 무더기", "홈 남음(식음)", "식음", "식음", "사라짐 직전"],
        design="칼끝이 바닥을 긁어 판 홈(갈색 재 홈 + 갓 판 자리의 달아오른 쇳빛, 머리에 불티·흙) → 끝에 흙 무더기. 판정 없음(A25 이하) — 판정은 몸 hitShape"))
    return T


def job(name):
    T = spec_table()
    sp = T[name]
    frames = {d: sp["fn"](d) for d in sp["dirs"]}
    for d in sp["dirs"]:
        assert len(frames[d]) == len(sp["ms"]), (name, d, len(frames[d]))
    cut, pivot, origin = F.X.fit(frames, include_pivot=True)
    upd = common(pivot, origin)
    upd.update({k: v for k, v in sp["meta"].items() if v is not None})
    if upd.get("anchor") == "koiguchi":                      # 반짝임 중심 = pivot (발이 아님)
        upd.update(pivot={"x": origin[0], "y": origin[1]}, pivotNote="pivot = 반짝임 중심 — 몸 koiguchiAnchors 점에 맞춘다")
        upd.pop("hitOriginInFrame", None)
    if sp["dirs"] == DIRS8:
        upd.update(dirTransform="drawn8", directionNote="8행 = 작업 B 대검 몸 행 순서(down, up, left, right, down-right, down-left, up-right, up-left). "
                                                         "대각 행 = 조준 45° 로 다시 그린 것(이미지 회전 아님)")
    elif sp["dirs"] == DIRS4:
        upd.update(dirTransform="drawn4", directionNote="4행 = 칼 몸 시트 행 순서(down, up, left, right) — left 는 180° 회전 규칙(§17)")
    else:
        upd.update(directionNote="1행 any — 방향 무관")
    sheet, j, _ = F.write(name, cut, sp["dirs"], sp["ms"], None, upd, sp["glow"], OUT_FX)
    return name, j["frameWidth"], j["frameHeight"], j["colors"]


ORDER = ["katana_counter", "katana_iai", "katana_iai_ready", "greatsword_tackle", "greatsword_brace_upswing", "greatsword_brace_upswing_ember",
         "greatsword_brace_absorb", "greatsword_leap_slam", "greatsword_leap_slam_land", "greatsword_guard_rush"]


def build(only=None):
    from multiprocessing import Pool
    names = [n for n in ORDER if not only or n in only]
    with Pool(4) as p:
        res = p.map(job, names, chunksize=1)
    stats = {}
    for name, fw, fh, cols in res:
        print("%-34s %4dx%-4d colors %2d" % (name, fw, fh, cols))
        stats[name] = dict(frame=[fw, fh], colors=cols)
    p = os.path.join(HERE, "stats_fx.json")
    old = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    old.update(stats)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(old.items())), f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    build(set(sys.argv[1:]) or None)
