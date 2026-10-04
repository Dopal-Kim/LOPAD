"""새 기본기 3종 이펙트 v3 — 56라운드 Q11 붓획 · 재·호박만 · 백열은 판정 순간 몇 도트(Q65). 작업 E2.

  dagger_backstab            등 뒤 치명 찌르기: 내리꽂는 짧은 붓획(丿) + 박힌 자리 치명 섬광(바늘 광선 → 점선 고리 → 불티 → 재)  4방향
  dagger_flurry(_heat2/3)    고속 난타: 찌르기 붓획 3갈래가 엇갈리며 남는 루프(몸 시트와 같은 10프레임·loopFrames) · 과열 3단계        4방향
  bow_arrow_rain_rise        화살비 쏘아 올림: 줌통 앞에서 하늘로 솟는 재 화살 + 불티 꼬리(화살 1발 = 1회 재생)                  4방향
  bow_arrow_rain_fall        화살비 낙하: 하늘에서 떨어져 꽂히는 화살 1발(피벗 = 꽂히는 바닥 점) → 재로 부서짐                     any
  bow_arrow_rain_mark        낙하 지점 예고 원(바닥): 나타남 → 대기 루프 → 쏟아짐 → 사라짐 · 행 = 크기 s·m·l(+ scale 허용)         sizes

좌표: v3 도트(pixelScale 0.5). 근접 fx 는 combo56_fx/fx56 규약(로컬 오른쪽 보기 → 방향 회전 TA, 원점 = 판정 원점 = 피벗 위 40 도트).
화면 고정 fx(치명 섬광·화살)는 몸 JSON 기준점(bladeTipAnchors·arrowSpawnAnchors)을 화면 좌표로 그대로 쓴다.
"""
import json
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "combo56_fx")))
import fx56 as F  # noqa: E402
from fx56 import BR, W, FK, TA, CO, HIT_UP  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
OUT_FX = os.path.join(ROOT, "assets/sprites/fx/v3")
P3 = os.path.join(ROOT, "assets/sprites/player/v3")
W3 = os.path.join(ROOT, "assets/sprites/weapons/v3")
SRC = "parts/art/work/combo56_moves_db/build.py fx (56라운드 Q40~Q43 새 기본기 — 작업 E2)"
DIRS4 = F.DIRS4
F.SRC = SRC                                         # write() 가 source 로 씀(이 프로세스 안에서만)
BODY_PIV = (48, 138)
PV = (CO[0], CO[1] + HIT_UP)                        # 큰 캔버스 위 주인공 발(몸 피벗)

HOT7 = [W.A19, W.A21, W.A23, W.A25, W.A26, W.X1, W.X0]   # v ≥ .857 X0 · ≥ .714 X1 · ≥ .571 A26 → 판정 프레임 밖은 v < .57
COOL4 = [W.A18, W.A19, W.A21, W.A23, W.A25]


def bjson(name):
    return json.load(open(os.path.join(P3, "player_%s.json" % name), encoding="utf-8"))


def wjson(name):
    return json.load(open(os.path.join(W3, "%s.json" % name), encoding="utf-8"))


def body_to_canvas(p):
    """몸 시트 도트 → 큰 캔버스(발 = PV)."""
    return (PV[0] + p[0] - BODY_PIV[0], PV[1] + p[1] - BODY_PIV[1])


def wpt_to_body(p):
    return (p[0] - 48.0, p[1] - 48.0)


def rays(L, cx, cy, n, r0, r1, w, v0, v1=0.15, rot=0.0, jitter=0.0, seed=0, long_every=2, long_k=1.6):
    """바늘 광선 n 갈래 — 값이 안쪽 v0 → 바깥 v1 로 떨어짐(백열이 바늘 전체로 번지지 않게)."""
    r = random.Random(seed)
    for k in range(n):
        a = rot + 2 * math.pi * k / n + r.uniform(-jitter, jitter)
        rr = r1 * (long_k if k % long_every == 0 else 1.0) * r.uniform(0.85, 1.1)
        L.ray(cx, cy, a, r0, rr, w, prof=FK.tp_tail(0.9), v=v0, vprof=lambda t, v0=v0, v1=v1: (v1 + (v0 - v1) * (1 - t) ** 1.4) / v0)


# =============================================================================
# 1. 등 뒤 치명 찌르기
# =============================================================================
BS_MS = [30, 50, 60, 70, 60, 80]
BS_ROLES = ["pre(내리꽂는 중 — 칼끝 빛이 모임)", "impact(판정 · 치명 섬광 — 백열 몇 도트)", "burst(바늘 광선 퍼짐 · 붓획 완성)",
            "ring(점선 고리 · 불티 · 박힌 채 비틂)", "decay(재 조각 떨어짐)", "ash(재)"]


def backstab_frames(d, bj, wj):
    tips = [wpt_to_body(p) for p in wj["bladeTipAnchors"][d]]
    hands = [h["handR"] for h in bj["handAnchors"][d]]
    imp = bj["impactFrame"]
    t3, t4, t5 = (body_to_canvas(tips[i]) for i in (imp - 1, imp, imp + 1))
    h4 = body_to_canvas(hands[imp])
    # 박힌 자리(칼날 58% — 적의 등 표면) = 섬광 중심
    cx, cy = h4[0] + (t4[0] - h4[0]) * 0.58, h4[1] + (t4[1] - h4[1]) * 0.58
    # 붓획: 내리꽂는 칼끝 경로(위에서 t3 → t4 → t5 너머로 짧게 박힘)
    ux, uy = t5[0] - t3[0], t5[1] - t3[1]
    n = math.hypot(ux, uy) or 1.0
    ux, uy = ux / n, uy / n
    a = (t3[0] - ux * 44, t3[1] - uy * 44)
    b = (t5[0] + ux * 6, t5[1] + uy * 6)
    pts = [(a[0] + (b[0] - a[0]) * i / 30 + (-uy) * 3 * math.sin(math.pi * i / 30),
            a[1] + (b[1] - a[1]) * i / 30 + ux * 3 * math.sin(math.pi * i / 30)) for i in range(31)]
    S = BR.Stroke(pts, 12.0, seed=401, peak=0.55, dry_from=0.72, split=1.0, drops=5, start_w=0.12, end_w=0.55)
    out = []
    rr = random.Random(41)
    sparks = [(rr.uniform(0, 2 * math.pi), rr.uniform(10, 22), rr.uniform(2.5, 5.0)) for _ in range(12)]
    for i in range(len(BS_MS)):
        fr = F.frame(None)
        Lf = fr.L(BR.FLAKE)
        Lb = fr.L(BR.INK_K)
        Lr = fr.L(COOL4)                               # 광선·고리(식은 쪽)
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(HOT7)                                # 판정 프레임 섬광(값으로 백열 범위 제한)
        if i == 0:
            S.draw(Lb, head=0.45, vmax=0.6, drops=False)
            Lr.stamp(t3[0], t3[1], 2.0, 0.7, soft=0.6)
        elif i == 1:
            S.draw(Lb, head=1.0, vmax=0.9, hot=True, Lhot=Lh)
            rays(Lh, cx, cy, 8, 2, 22, 1.3, 0.74, 0.2, rot=math.radians(-90), jitter=0.08, seed=3, long_k=1.9)
            Lh.stamp(cx, cy, 2.6, 0.9, soft=0.35)      # 백열 코어 — 반지름 ~2 도트
            Lr.ring(cx, cy, 9, 0.9, v=0.75)
        elif i == 2:
            S.draw(Lb, head=1.0, tail=0.05, vmax=0.88)
            rays(Lr, cx, cy, 8, 7, 34, 1.1, 0.95, 0.25, rot=math.radians(-90), jitter=0.1, seed=3, long_k=1.7)
            rays(Lr, cx, cy, 8, 10, 18, 0.8, 0.7, 0.2, rot=math.radians(-67.5), seed=5, long_k=1.0)
            Lr.ring(cx, cy, 16, 1.0, v=0.85, dash=(10, 0.7, 0.0))
            Lr.stamp(cx, cy, 2.4, 0.95, soft=0.4)
            for ang, dist, ln in sparks[:6]:
                W.ember(Le, cx + math.cos(ang) * dist, cy + math.sin(ang) * dist, math.cos(ang), math.sin(ang), ln, w=0.6, v=0.95)
        elif i == 3:
            S.draw(Lb, head=1.0, tail=0.25, vmax=0.8, wk=0.85, k=0.3, fall=4)
            Lr.ring(cx, cy, 24, 0.9, v=0.7, dash=(14, 0.45, 0.1))
            rays(Lr, cx, cy, 4, 14, 26, 0.7, 0.55, 0.15, rot=math.radians(-45), seed=7, long_k=1.0)
            for ang, dist, ln in sparks:
                W.ember(Le, cx + math.cos(ang) * dist * 1.7, cy + math.sin(ang) * dist * 1.7 + 4, math.cos(ang), math.sin(ang) + 0.3,
                        ln * 0.9, w=0.6, v=0.85)
            S.flakes(Lf, 0.3, 0.0, 0.5, 4, size=1.5, fall=8.0, seed=i)
        else:
            k = 0.6 if i == 4 else 1.0
            S.draw(Lb, head=1.0, tail=0.35 + 0.5 * k, vmax=0.72 - 0.15 * k, wk=0.8 - 0.2 * k, k=k, fall=6 + 8 * k)
            S.flakes(Lf, k, 0.2, 1.0, 6, size=1.6, fall=12.0, seed=i)
            if i == 4:
                for ang, dist, ln in sparks[::2]:
                    W.ember(Le, cx + math.cos(ang) * dist * 2.2, cy + math.sin(ang) * dist * 2.0 + 10, 0.2 * math.cos(ang), 1.0, 2.5, w=0.6, v=0.6)
                Lr.ring(cx, cy, 28, 0.7, v=0.45, dash=(16, 0.3, 0.2))
            for j in range(5):
                W.flake(Lf, cx + rr.uniform(-14, 14), cy + 6 + 10 * k + rr.uniform(0, 10), rr.uniform(1.0, 1.8), rr.uniform(0, 6), v=0.7)
        out.append(fr.render())
    return out, (round(cx - PV[0] + BODY_PIV[0], 1), round(cy - PV[1] + BODY_PIV[1], 1))


# =============================================================================
# 2. 고속 난타 — 루프 프레임(2~7)에서 찌르기 3갈래(2·4·6)가 나이에 따라 마름. 루프 이음새 없음(나이 = (f − s) mod 6)
# =============================================================================
FLURRY_STABS = {2: dict(ang=-10, bend=-5, x1=146, seed=511), 4: dict(ang=12, bend=6, x1=138, seed=512), 6: dict(ang=0, bend=-3, x1=154, seed=513)}
HEAT = {
    1: dict(name="dagger_flurry", ink=BR.INK_K, wmax=6.0, vmax=0.8, vfloor=0.32, ext=0, embers=0, ghost=False, smoke=0, maxAge=3,
            label="1단(과열 0~39%) — 재 테 + 호박 심의 가는 붓획"),
    2: dict(name="dagger_flurry_heat2", ink=[W.B1, W.A18, W.A19, W.A21, W.A23, W.A25], wmax=7.0, vmax=0.88, vfloor=0.4, ext=10, embers=3,
            ghost=False, smoke=0, maxAge=3, label="2단(40~79%) — 붓획이 더 굵고 길고 호박이 넓음 · 획 끝 불티"),
    3: dict(name="dagger_flurry_heat3", ink=[W.A18, W.A19, W.A21, W.A23, W.A25], wmax=8.0, vmax=0.95, vfloor=0.55, ext=18, embers=6,
            ghost=True, smoke=5, maxAge=4, label="3단(80~100%) — 달아오른 획(재 테 거의 없음) · 팔 잔상 획 · 불티 다발 · 손 둘레 아지랑이 재"),
}
FL_MS = [40, 40, 45, 45, 45, 45, 45, 45, 60, 80]
FL_GLOW = [2, 4, 6]
AGE_K = [0.0, 0.3, 0.55, 0.78, 0.95]


def _thrust_pts(t, ang, x0, x1, bend):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for i in range(41):
        u = i / 40
        along = x0 + (x1 - x0) * u
        lat = bend * math.sin(math.pi * u) * (1 - 0.3 * u)
        pts.append(t((ca * along - sa * lat, sa * along + ca * lat)))
    return pts


def flurry_frames(d, lv):
    hp = HEAT[lv]
    t = TA(d, *CO)
    strokes = {}
    for s, sp in FLURRY_STABS.items():
        strokes[s] = BR.Stroke(_thrust_pts(t, sp["ang"], 16, sp["x1"] + hp["ext"], sp["bend"]), hp["wmax"], seed=sp["seed"] + lv * 7,
                               peak=0.5, dry_from=0.7, split=1.0, drops=4 + lv, start_w=0.12, end_w=0.5)
        if hp["ghost"]:
            strokes[(s, "g")] = BR.Stroke(_thrust_pts(t, sp["ang"] - 9, 10, sp["x1"] * 0.8, -sp["bend"]), hp["wmax"] * 0.7,
                                          seed=sp["seed"] + 90, peak=0.45, dry_from=0.6, split=1.2, drops=0, start_w=0.2, end_w=0.4)
    st = dict(flake=BR.FLAKE, glint=0)
    out = []
    for f in range(len(FL_MS)):
        fr = F.frame(t)
        Lsm = fr.L([W.S0, W.S1, W.S2])
        Lf = fr.L(st["flake"])
        Lg = fr.L([W.S0, W.S1, W.S2, W.S3])
        Lb = fr.L(hp["ink"])
        Le = fr.L([W.A19, W.A21, W.A23, W.A25])
        Lh = fr.L(BR.HOT)
        vis = []                                       # (찌르기 프레임, 나이)
        if 2 <= f <= 7:
            for s in FLURRY_STABS:
                age = (f - s) % 6
                if age <= hp["maxAge"]:
                    vis.append((s, age))
        elif f == 1:
            vis = []
        elif f >= 8:
            vis = [(6, f - 6), (4, f - 4)] if f - 4 <= hp["maxAge"] else [(6, f - 6)]
        for s, age in sorted(vis, key=lambda x: -x[1]):
            S = strokes[s]
            if age == 0:
                S.draw(Lb, head=1.0, vmax=hp["vmax"], hot=True, Lhot=Lh, vfloor=hp["vfloor"])
                if hp["ghost"]:
                    strokes[(s, "g")].draw(Lg, head=1.0, vmax=0.8, drops=False)
                rr = random.Random(s * 13 + lv)
                ex, ey = S.p[-1]
                tx, ty = S.tangent_end()
                for j in range(hp["embers"]):
                    a = math.atan2(ty, tx) + rr.uniform(-0.7, 0.7)
                    dist = rr.uniform(3, 10)
                    W.ember(Le, ex + math.cos(a) * dist, ey + math.sin(a) * dist, math.cos(a), math.sin(a), rr.uniform(2.5, 5), w=0.6, v=0.9)
            else:
                k = AGE_K[min(age, 4)]
                tail = 0.12 + 0.7 * k
                S.draw(Lb, head=1.0, tail=tail, vmax=hp["vmax"] * (0.9 - 0.25 * k), wk=1 - 0.3 * k, k=k, fall=2 + 8 * k,
                       vfloor=hp["vfloor"] * (1 - 0.4 * k))
                if hp["ghost"] and age == 1:
                    strokes[(s, "g")].draw(Lg, head=1.0, tail=0.4, vmax=0.55, k=0.5, drops=False)
                S.flakes(Lf, k, max(0.0, tail - 0.3), tail + 0.05, 2 + lv, size=1.3, fall=8.0, seed=s * 10 + f)
                if hp["embers"] and age == 1:
                    rr = random.Random(s * 31 + f)
                    ex, ey = S.p[-1]
                    for j in range(hp["embers"] // 2 + 1):
                        W.ember(Le, ex + rr.uniform(-6, 10), ey + rr.uniform(-8, 6) + 4, rr.uniform(-0.3, 0.3), 1.0, 2.5, w=0.6, v=0.7)
        if f == 1:                                     # 시작: 손 앞에 재가 모임(판정 전)
            hx, hy = t((18, -2))
            for j in range(3 + lv):
                rr = random.Random(j + lv * 5)
                W.flake(Lf, hx + rr.uniform(-6, 8), hy + rr.uniform(-6, 6), rr.uniform(0.8, 1.4), rr.uniform(0, 6), v=0.7)
        if hp["smoke"] and f >= 1:                     # 3단 아지랑이: 손 둘레에서 위로 피는 재 연기(화면 위쪽으로)
            rr = random.Random(77 + f)
            hx, hy = t((22, 0))
            for j in range(hp["smoke"]):
                ph = (f * 0.37 + j * 0.21) % 1.0
                Lsm.puff(hx + rr.uniform(-16, 16), hy - 6 - 26 * ph, 2.2 + 2.5 * ph, v=0.85 - 0.5 * ph, light=0.4)
        out.append(fr.render())
    return out


# =============================================================================
# 3. 화살비 — 쏘아 올림(rise) · 낙하(fall) · 예고 원(mark)
# =============================================================================
def arrow(Ls, Lhd, Lfl, x, y, ux, uy, length=26.0, head_v=0.8, shaft_v=0.85, k=1.0):
    """재 화살(화면): 꼬리 (x,y)에서 (ux,uy) 방향. 촉 = 호박(head_v), 대 = 재, 깃 = 회색 재."""
    nx, ny = -uy, ux
    hx, hy = x + ux * length, y + uy * length
    hl = 5 * k
    Ls.stroke([(x, y), (hx - ux * hl * 0.8, hy - uy * hl * 0.8)], 0.75 * k, v=shaft_v)
    Lhd.stroke([(hx - ux * hl, hy - uy * hl), (hx, hy)], 1.4 * k, prof=FK.tp_tail(0.9), v=head_v)
    Lhd.stroke([(hx - ux * hl + nx * 1.6 * k, hy - uy * hl + ny * 1.6 * k), (hx - ux * hl - nx * 1.6 * k, hy - uy * hl - ny * 1.6 * k)],
               0.6 * k, v=head_v * 0.7)
    for sg in (1, -1):
        Lfl.stroke([(x + ux * 5 * k, y + uy * 5 * k), (x - ux * 1 + nx * 2.6 * k * sg, y - uy * 1 + ny * 2.6 * k * sg)], 0.6 * k, v=0.8)
    return hx, hy


RISE_MS = [40, 40, 40, 50]
RISE_DIST = [8, 58, 118, 178]


def rise_frames(d, ang):
    """ang = 화면 진행각(rad, 위 = -π/2). 원점 = 화살 생성 점(PV 자리에 둠)."""
    ux, uy = math.cos(ang), math.sin(ang)
    out = []
    for i, dist in enumerate(RISE_DIST):
        fr = F.frame(None)
        Ltr = fr.L([W.S0, W.S1, W.S2])
        Le = fr.L([W.A18, W.A19, W.A21, W.A23])
        Ls = fr.L([W.S0, W.S1, W.S2, W.S3])
        Lhd = fr.L([W.A19, W.A21, W.A23, W.A25])
        Lfl = fr.L([W.S1, W.S2, W.S3])
        x, y = PV[0] + ux * dist, PV[1] + uy * dist
        if i < 3:
            length = 34 - 6 * i                         # 멀어지며(하늘로) 작아짐
            arrow(Ls, Lhd, Lfl, x, y, ux, uy, length=length, head_v=0.95 - 0.12 * i, shaft_v=0.95, k=1.25 - 0.15 * i)
            tl = min(dist, 20 + 22 * i)
            Ltr.stroke([(x - ux * tl, y - uy * tl), (x, y)], 1.2, prof=FK.tp_head(0.9), v=0.8 - 0.1 * i, dash=(7, 0.6, 0.1 * i))
            rr = random.Random(9 + i)
            for j in range(2 + i):
                q = rr.uniform(0.2, 1.0) * tl
                W.ember(Le, x - ux * q + rr.uniform(-2, 2), y - uy * q + rr.uniform(-2, 2) + 2 * i, -ux * 0.3, -uy * 0.3 + 0.5, 2.0, w=0.6,
                        v=0.85 - 0.15 * i)
        else:                                           # 하늘로 사라짐: 짧은 촉 점 + 흩어지는 꼬리 재
            Lhd.stamp(x, y, 1.0, 0.55, soft=0)
            Ltr.stroke([(x - ux * 40, y - uy * 40), (x - ux * 6, y - uy * 6)], 1.0, prof=FK.tp_head(0.9), v=0.5, dash=(9, 0.45, 0.3))
        out.append(fr.render())
    return out


FALL_MS = [40, 40, 40, 40, 60, 80, 100]
FALL_IMPACT = 3
FALL_H = [150, 100, 48, 0]
AL = 40.0                                             # 낙하 화살 길이(도트) — 활 화살(51)보다 조금 짧게(멀리서 보는 느낌)
FALL_SLANT = math.radians(12)                         # 수직에서 12° — 오른쪽 아래로 떨어짐(flipX 허용)


def fall_frames():
    ux, uy = math.sin(FALL_SLANT), math.cos(FALL_SLANT)
    gx, gy = PV
    out = []
    rr = random.Random(5)
    flakes = [(rr.uniform(-8, 8), rr.uniform(-20, -2), rr.uniform(0.9, 1.6), rr.uniform(0, 6)) for _ in range(8)]
    for i in range(len(FALL_MS)):
        fr = F.frame(None)
        Lgr = fr.L([W.B0, W.B1, W.B2])
        Ldu = fr.L([W.B1, W.B2, W.B3, W.S1])
        Ltr = fr.L([W.S0, W.S1, W.S2])
        Lf = fr.L(BR.FLAKE)
        Ls = fr.L([W.S0, W.S1, W.S2, W.S3])
        Lhd = fr.L([W.A19, W.A21, W.A23, W.A25])
        Lfl = fr.L([W.S1, W.S2, W.S3])
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(HOT7)
        if i < FALL_IMPACT:                            # 떨어지는 중(촉이 아래)
            h = FALL_H[i]
            tipx, tipy = gx - ux * h, gy - uy * h
            tx, ty = tipx - ux * AL, tipy - uy * AL
            arrow(Ls, Lhd, Lfl, tx, ty, ux, uy, length=AL, head_v=0.8 + 0.05 * i, shaft_v=0.95, k=1.35)
            Ltr.stroke([(tx - ux * (30 + 10 * i), ty - uy * (30 + 10 * i)), (tx, ty)], 1.4, prof=FK.tp_head(0.9), v=0.75, dash=(8, 0.65, 0.2 * i))
            Lgr.disc(gx, gy + 1, 3 + i * 1.5, 1.2 + 0.5 * i, v=0.5 + 0.1 * i)   # 바닥 그림자(가까워질수록 진해짐)
        else:
            k = i - FALL_IMPACT                         # 0 꽂힘(판정) · 1 남음 · 2 부서짐 · 3 재
            depth = 11                                 # 촉이 바닥에 박힌 깊이(보이지 않음)
            tx, ty = gx - ux * (AL - depth), gy - uy * (AL - depth)
            if k <= 1:
                Lgr.disc(gx, gy + 1, 5.5, 2.2, v=0.6)
                ash = 0.0
                arrow(Ls, Lhd, Lfl, tx, ty, ux, uy, length=AL - depth, head_v=0.45, shaft_v=0.95, k=1.35)
                if k == 0:
                    Lh.stamp(gx, gy, 1.6, 0.92, soft=0.4)            # 꽂힌 순간 촉 자리 백열 몇 도트
                    rays(Lh, gx, gy, 6, 2, 9, 0.8, 0.62, 0.2, rot=math.radians(-90), seed=11, long_k=1.5)
                    for sg in (-1, 1):
                        Ldu.puff(gx + sg * 6, gy - 1, 3.5, v=0.85, ry=2.2)
                else:
                    for sg in (-1, 1):
                        Ldu.puff(gx + sg * 10, gy - 2, 3.0, v=0.6, ry=2.0)
                    rays(Le, gx, gy, 4, 4, 9, 0.6, 0.6, 0.2, rot=math.radians(-135), seed=12, long_k=1.0)
            else:
                Lgr.disc(gx, gy + 1, 5.0, 2.0, v=0.45 - 0.1 * (k - 2))
                keep = 0.55 if k == 2 else 0.2
                L2 = AL - depth
                n_seg = 6
                for j in range(n_seg):                  # 아래(박힌 쪽)부터 남고 위는 재로 흩어짐
                    if j / n_seg > keep:
                        continue
                    a0 = L2 - L2 * j / n_seg
                    a1 = L2 - L2 * (j + 0.8) / n_seg
                    Ls.stroke([(tx + ux * (L2 - a0), ty + uy * (L2 - a0)), (tx + ux * (L2 - a1), ty + uy * (L2 - a1))], 0.7, v=0.7)
                for fx_, fy_, sz, rot in flakes[: 4 + 2 * (k - 2)]:
                    W.flake(Lf, gx + fx_ - ux * 10, gy + fy_ * (1.2 - 0.5 * (k - 2)) + 6 * (k - 2), sz, rot + k, v=0.75)
                if k == 2:
                    W.ember(Le, gx - 3, gy - 18, 0.0, -1.0, 2.5, w=0.6, v=0.6)
        out.append(fr.render())
    return out


MARK_SIZES = {"s": 96, "m": 128, "l": 176}            # 반지름 도트(월드 24·32·44 px)
MARK_MS = [50, 60, 90, 90, 90, 90, 60, 60, 70, 90]
MARK_PHASES = {"appear": [0, 1], "wait": [2, 3, 4, 5], "rain": [6, 7], "out": [8, 9]}
MARK_ROLES = ["appear(바깥 점선이 조여 옴)", "appear", "wait 루프", "wait 루프", "wait 루프", "wait 루프", "rain(쏟아짐 — 테가 달아오름)",
              "rain", "out(식음)", "out(재 점선)"]


def mark_frames(R):
    cx, cy = PV
    out = []
    ticks = 8
    for i in range(len(MARK_MS)):
        fr = F.frame(None)
        Lbase = fr.L([W.B0, W.B1, W.B2])               # 바닥 그을음 테(어둠 위에서 읽히는 바탕)
        Lsoot = fr.L([W.B0, W.B1])
        Lring = fr.L([W.A18, W.A19, W.A21, W.A23, W.A25])
        Ltick = fr.L([W.A19, W.A21, W.A23, W.A25])
        Lf = fr.L(BR.FLAKE)
        if i <= 1:                                     # 나타남: 바깥에서 조여 들어오는 점선 테
            rr_ = R * (1.22 if i == 0 else 1.08)
            Lring.ring(cx, cy, rr_, 1.3, v=0.55 + 0.15 * i, dash=(20, 0.55, 0.0))
            if i == 1:
                Lbase.ring(cx, cy, R, 3.2, v=0.7)
                Lring.ring(cx, cy, R, 0.8, v=0.55)
        elif i <= 5:                                   # 대기 루프: 테 + 회전하는 화살촉 눈금 + 안쪽 점선 + 가운데 표식
            ph = (i - 2) / 4.0
            Lbase.ring(cx, cy, R, 3.4, v=0.75)
            Lring.ring(cx, cy, R, 1.0, v=0.72 + 0.08 * math.sin(2 * math.pi * ph))
            Lring.ring(cx, cy, R * 0.62, 0.7, v=0.45, dash=(28, 0.35, ph))
            for k in range(ticks):                     # 안쪽을 가리키는 화살촉 ▼ 8개(4프레임에 한 칸 회전)
                a = 2 * math.pi * (k + ph) / ticks
                ox, oy = cx + math.cos(a) * (R - 3), cy + math.sin(a) * (R - 3)
                ix, iy = cx + math.cos(a) * (R - 13), cy + math.sin(a) * (R - 13)
                nx, ny = -math.sin(a) * 4, math.cos(a) * 4
                Ltick.stroke([(ox + nx, oy + ny), (ix, iy)], 0.8, v=0.8)
                Ltick.stroke([(ox - nx, oy - ny), (ix, iy)], 0.8, v=0.8)
            for k in range(4):                          # 가운데 작은 + 표식
                a = math.pi / 2 * k
                Ltick.stroke([(cx + math.cos(a) * 3, cy + math.sin(a) * 3), (cx + math.cos(a) * 8, cy + math.sin(a) * 8)], 0.7, v=0.6)
        elif i <= 7:                                   # 쏟아짐: 테가 달아오르고 안쪽 바닥이 그을림(백열 없음 — 예고는 판정 아님)
            Lbase.ring(cx, cy, R, 4.0, v=0.85)
            Lring.ring(cx, cy, R, 1.5, v=0.95)
            rr = random.Random(int(R) + i)
            for j in range(int(R / 7)):
                a = rr.uniform(0, 2 * math.pi)
                d = R * math.sqrt(rr.uniform(0.02, 0.85))
                Lsoot.stamp(cx + math.cos(a) * d, cy + math.sin(a) * d, rr.uniform(1.0, 2.2), 0.8, soft=0)
            Lring.ring(cx, cy, R * (0.8 if i == 6 else 0.9), 0.6, v=0.5, dash=(18, 0.4, 0.3 * i))
        else:                                          # 사라짐: 테가 점선 재로 끊기며 식음
            k = i - 8
            Lbase.ring(cx, cy, R, 2.8 - k, v=0.6 - 0.2 * k, dash=(16, 0.7 - 0.25 * k, 0.1))
            Lring.ring(cx, cy, R, 0.7, v=0.45 - 0.15 * k, dash=(16, 0.5 - 0.2 * k, 0.1))
            rr = random.Random(int(R) * 3 + i)
            for j in range(int(R / 12)):
                a = rr.uniform(0, 2 * math.pi)
                W.flake(Lf, cx + math.cos(a) * R, cy + math.sin(a) * R + 3 * k, rr.uniform(0.8, 1.4), rr.uniform(0, 6), v=0.7)
        out.append(fr.render())
    return out


# =============================================================================
# 자르기(임의 피벗) · 쓰기
# =============================================================================
def fit_at(frames, pivot_canvas, margin=3, step=8):
    box = (pivot_canvas[0], pivot_canvas[1], pivot_canvas[0] + 1, pivot_canvas[1] + 1)
    for lst in frames.values():
        for im in lst:
            b = im.getbbox()
            if b:
                box = (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    x0, y0 = box[0] - margin, box[1] - margin
    Wd = -(-(box[2] + margin - x0) // step) * step
    Hd = -(-(box[3] + margin - y0) // step) * step
    out = {d: [im.crop((x0, y0, x0 + Wd, y0 + Hd)) for im in lst] for d, lst in frames.items()}
    return out, (pivot_canvas[0] - x0, pivot_canvas[1] - y0)


COMMON = dict(effectRule="56라운드 Q11 붓획 · 재·호박만 · 백열 X0/X1·A26 은 glowFrames 의 몇 도트만(흰 막대 없음)", r56="56라운드 Q40~Q43 새 기본기(작업 E2)",
              palette=W.PALETTE_NOTE)
