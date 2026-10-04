"""58라운드 Q3 대검 차지 휘둘러 내리찍기 이펙트.

  fx/v3/greatsword_charge_swing          8행(drawn8) 붓획 — 오른쪽 뒤 낮은 곳에서 크게 한 바퀴 돌아 머리 위를 넘어 앞 바닥에 내리찍는 굵은 흙·녹 붓 한 획
                                         + 지면 붓획(찍은 자리 → 쐐기 끝). 칼 몸 시트 행 번호 그대로.
  fx/v3/greatsword_charge_crack_line_t1~t5  찍은 자리에서 마우스 방향으로 이어지는 땅 균열(1~5칸 = 64~320 도트). 1행 any · rotate(그림 오른쪽 = 진행 방향).
                                         앞머리가 일정 속도(1.6 도트/ms)로 달림(frontPxByFrame) — 앞머리 근처만 달아오르고 뒤는 식은 금,
                                         양옆 흙판이 솟았다 무너짐 + 앞머리 파편·불티 + 지나간 뒤 먼지. 백열(흰색) 없음.
도구 = combo56_fx/fx56(붓·회전) · combo55/fx55(W·FK·fit·write) — 56 꽂아내리기 충격파(combo56_body/fx56.wave_frames) 구성을 균열 중심으로 다시 짬.
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "combo56_fx"))
sys.path.insert(0, HERE)
import fx56 as F  # noqa: E402
from fx56 import BR, W, FK  # noqa: E402
X = F.X                                    # combo55/fx55

OUT_FX = os.path.normpath(os.path.join(WORK, "../../../assets/sprites/fx/v3"))
SRC = "parts/art/work/combo58/build.py gsfx (58라운드 Q3 대검 차지 휘둘러 내리찍기 · 균열 선)"
RG = 204.0
DIRS8 = F.DIRS8

# 몸 규격과 공유(gs58 의 값)
CRACK_TILE_DOTS = 64
CRACK_SPEED = 1.6
CRACK_MS = [30, 30, 30, 30, 30, 30, 30, 50, 60, 80, 100, 120]
CRACK_TRAVEL_FRAMES = 7


def crack_front(tiles):
    L = tiles * CRACK_TILE_DOTS
    out, t = [], 0
    for i, m in enumerate(CRACK_MS):
        t += m
        out.append(min(L, round(CRACK_SPEED * t)) if i < CRACK_TRAVEL_FRAMES else L)
    return out


# =============================================================================
# 1. 휘둘러 내리찍기 붓획 (8행)
# =============================================================================
SWING_MS = [50, 50, 40, 40, 60, 70, 80]
SWING_IMPACT = 3
SWING_PLAN = [("pre", 0.22), ("draw", 0.6), ("draw", 0.9), ("impact", 1.0), ("decay", 0.33), ("decay", 0.66), ("decay", 1.0)]
SWING_RV = 150.0                          # 내리찍는 반경(도트) — 칼끝이 바닥에 닿는 거리 근처
SWING_LAT = 62.0                          # 시작(오른쪽 뒤)의 옆 거리
SWING_L = round(RG * 1.3, 1)              # 지면 붓획 끝 = 1단 쐐기


def swing_frames(d, seed=581):
    t = F.TA(d, *F.CO)

    def P(phi_deg):
        phi = math.radians(phi_deg)
        f = SWING_RV * math.cos(phi)
        z = max(6.0, SWING_RV * 1.02 * math.sin(phi))
        r = SWING_LAT * (phi_deg / 215.0) ** 0.9                # + = 해부 오른쪽(오른쪽 보기에서 화면 아래)
        x, y = t((f, r))
        return x, y - z

    pts = [P(215.0 - 215.0 * i / 160) for i in range(161)]
    S = BR.Stroke(pts, 22.0, seed=seed, peak=0.62, dry_from=0.86, split=0.7, drops=0, start_w=0.08, end_w=0.8)
    gpts = [t((SWING_RV * 0.85 + (SWING_L - SWING_RV * 0.85) * i / 30, 0.0)) for i in range(31)]
    G = BR.Stroke(gpts, 13.0, seed=seed + 1, peak=0.25, dry_from=0.6, split=1.3, drops=8, start_w=0.7, end_w=0.4)
    rng = random.Random(seed)
    out = []
    for i, (kind, p) in enumerate(SWING_PLAN):
        fr = F.frame(t)
        Lf = fr.L(BR.FLAKE_G)
        Lb = fr.L(BR.INK_G)
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        if kind == "pre":
            S.draw(Lb, head=p, vmax=0.6, drops=False)
        elif kind == "draw":
            S.draw(Lb, head=p, tail=max(0.0, p - 0.75), vmax=0.84, drops=False)
        elif kind == "impact":
            S.draw(Lb, head=1.0, tail=0.35, vmax=0.88, drops=False)
            G.draw(Lb, head=1.0, vmax=0.9, hot=True, Lhot=Lh)
            S.hot_head(Lh, 0.999)
        else:
            k = p
            S.draw(Lb, head=1.0, tail=0.45 + 0.5 * k, vmax=0.8 - 0.2 * k, wk=1 - 0.3 * k, k=k, drops=False)
            G.draw(Lb, head=1.0, tail=0.1 + 0.6 * k, vmax=0.82 - 0.2 * k, wk=1 - 0.25 * k, k=k, fall=2 + 6 * k)
            S.flakes(Lf, k, 0.45, 1.0, 7, size=2.3, fall=9.0, seed=i)
            G.flakes(Lf, k, 0.0, 1.0, 5, size=2.0, fall=6.0, seed=i + 9)
        if kind in ("impact", "decay") and (kind == "impact" or p < 0.5):
            k = 0.0 if kind == "impact" else p
            r = random.Random(seed * 3 + i)
            ex, ey = t((SWING_RV * 0.9, 0.0))
            for j in range(9):
                a = r.uniform(-2.8, -0.35)
                dist = r.uniform(5, 18) * (1 + 1.4 * k)
                W.ember(Le, ex + math.cos(a) * dist, ey + math.sin(a) * dist + 6 * k * k, math.cos(a), math.sin(a),
                        r.uniform(2.5, 5) * (1 - 0.4 * k), w=0.6, v=0.9 - 0.3 * k)
        out.append(fr.render())
    return out


def build_swing():
    from gridcompat import body_meta
    bj = body_meta("player/v3/player_greatsword_charge_swing")
    hit = bj["timingMs"]["hitAt"]
    spawn = hit - sum(SWING_MS[:SWING_IMPACT])
    frames = {d: swing_frames(d) for d in DIRS8}
    cut, pivot, origin = X.fit(frames, include_pivot=True)
    upd = dict(anchor="player_pivot", pivot={"x": pivot[0], "y": pivot[1]}, hitOriginInFrame={"x": origin[0], "y": origin[1]},
               pivotNote="pivot = 주인공 발(몸 피벗). 판정 원점 = pivot 위 40 도트(hitOriginInFrame)",
               weapon="greatsword", move="greatsword_charge_swing", brushStroke=True,
               design="차지 휘둘러 내리찍기 — 오른쪽 뒤 낮은 곳에서 크게 한 바퀴(옆 → 머리 위)를 돌아 앞 바닥에 내리찍는 굵은 흙·녹 붓 한 획 + 찍은 자리에서 쐐기 끝까지 지면 붓획",
               r58="58라운드 Q3 — 꽂기 대체: 마우스 방향으로 휘둘러 내리찍기",
               drawnSwing=dict(radiusDots=SWING_RV, lateralStartDots=SWING_LAT, fromDeg=215, toDeg=0, groundEndDots=SWING_L,
                               note="세로면 각 215°(오른쪽 뒤 낮게) → 90°(머리 위) → 0°(앞 바닥) — 옆 거리는 시작 62 도트에서 0 으로"),
               spawn="body_ms", spawnAtMs=spawn, impactAtBodyMs=hit, impactFrame=SWING_IMPACT,
               spawnRule="spawnAtMs = 몸 hitAt − sum(frameDurationsMs[:impactFrame])",
               frameRoles=["pre(오른쪽 뒤에서 시작)", "draw(옆을 돌아 올라감)", "draw(머리 위를 넘음)", "impact(앞 바닥 · 지면 붓획 · 머리 백열)",
                           "decay", "decay", "decay(재)"],
               holdFrame=4, holdNote="히트스톱 정지 칸 = 다 그어진 다음 칸(56 Q37)",
               companions=dict(crackLine="fx/v3/greatsword_charge_crack_line_t1~t5 (찍은 자리 → 커서)", groundCrack="fx/v3/greatsword_ground_crack 행 m/m/l"),
               directions=DIRS8, dirTransform="drawn8",
               directionNote="8행 = 대검 몸 행 순서(down, up, left, right, down-right, down-left, up-right, up-left). 조준각 그림을 각 행 각도로 회전해 다시 래스터")
    F.SRC = SRC
    F.VERSION = "v3-r58"
    sheet, j, _ = F.write("greatsword_charge_swing", cut, DIRS8, SWING_MS, None, upd, [SWING_IMPACT], OUT_FX)
    print("greatsword_charge_swing", j["frameWidth"], j["frameHeight"], "colors", j["colors"], "spawn", spawn)
    return j


# =============================================================================
# 2. 균열 선 t1~t5 (오른쪽 보기, rotate)
# =============================================================================
def crack_frames(tiles, seed=5810):
    L = tiles * CRACK_TILE_DOTS
    fronts = crack_front(tiles)
    t = X.T("right", *X.CO)
    rng = W.Debris(seed + tiles).rng
    c = X.CO
    spine = W.jag(rng, (c[0] + 2, c[1]), (c[0] + L, c[1]), n=max(6, int(L / 13)), amp=3.2)
    twigs = []
    nt = max(2, int(L / 30))
    for k in range(nt):
        x0 = 14 + (L - 22) * k / max(1, nt - 1) + rng.uniform(-6, 6)
        side = 1 if k % 2 else -1
        twigs.append((x0, side, rng.uniform(9, 18), rng.randint(0, 9999)))
    slabs = []
    ns = max(3, int(L / 20))
    for k in range(ns):
        x0 = 10 + (L - 14) * k / max(1, ns - 1) + rng.uniform(-4, 4)
        side = 1 if k % 2 == 0 else -1
        slabs.append(dict(x=x0, side=side, off=rng.uniform(4, 7), h=rng.uniform(9, 15), w=rng.uniform(10.0, 14.0),
                          lean=rng.uniform(-0.4, 0.4)))
    dusts = [(rng.uniform(8, L), rng.choice((-1, 1)) * rng.uniform(8, 22), rng.uniform(5, 9)) for _ in range(max(4, int(L / 22)))]

    def spine_until(x):
        return [p for p in spine if p[0] <= c[0] + x]

    def shard(Lr, bx, by, side, h, w, lean, k):
        tip = (bx + lean * h * k, by + side * h * k)
        l0, r0 = (bx - w * 0.5, by), (bx + w * 0.5, by)
        mid = (bx + lean * h * k * 0.4, by + side * h * k * 0.45)
        for tri, v in (((l0, tip, mid), 0.95), ((mid, tip, r0), 0.6), ((l0, mid, r0), 0.75)):
            xs = [q[0] for q in tri]
            ys = [q[1] for q in tri]
            for yy in range(int(min(ys)) - 1, int(max(ys)) + 2):
                for xx in range(int(min(xs)) - 1, int(max(xs)) + 2):
                    px_, py_ = xx + 0.5, yy + 0.5
                    sg, ok = None, True
                    for i_ in range(3):
                        ax, ay = tri[i_]
                        bx2, by2 = tri[(i_ + 1) % 3]
                        cc = (bx2 - ax) * (py_ - ay) - (by2 - ay) * (px_ - ax)
                        if sg is None:
                            sg = cc >= 0
                        elif (cc >= 0) != sg and abs(cc) > 1e-9:
                            ok = False
                            break
                    if ok:
                        Lr.put(xx, yy, v)

    out = []
    for i, front in enumerate(fronts):
        fr = W.Frame(X.CANVAS, X.CANVAS, t)
        Ldust = fr.L(W.R_DUST)
        Lgap = fr.L([W.B0])
        Lcool = fr.L([W.A18, W.A19])
        Lcrk = fr.L([W.A19, W.A21, W.A23, W.A25])
        Lrock = fr.L([W.B0, W.B1, W.B2, W.B3])
        Lrim = fr.L([W.B2, W.B3])
        Lember = fr.L(W.R_EMBER[:5])
        travelling = i < CRACK_TRAVEL_FRAMES and (i == 0 or fronts[i - 1] < L)
        arrive = i < CRACK_TRAVEL_FRAMES
        age = 0.0 if arrive else (i - CRACK_TRAVEL_FRAMES + 1) / (len(fronts) - CRACK_TRAVEL_FRAMES)
        pts = spine_until(front)
        if len(pts) >= 2:
            # 틈: 찍은 자리 쪽이 넓고 앞머리로 갈수록 가늘게
            Lrim.stroke([(x, y - 2.6) for x, y in pts], 1.2, prof=lambda u: 1.0 - 0.5 * u, v=0.9 - 0.4 * age)   # 위 가장자리(빛 받는 턱)
            Lgap.stroke(pts, 4.6, prof=lambda u: 1.0 - 0.55 * u, v=1.0)
            n = len(pts)
            hot_n = 7 if travelling else 0
            if age < 0.95:
                cool = pts[:max(2, n - hot_n + 1)]
                Lcool.stroke(cool, 1.3, v=0.9 - 0.5 * age, dash=(10.0, 0.85 - 0.5 * age, 0.2) if age > 0.3 else None)
            if hot_n and n > 2:
                Lcrk.stroke(pts[max(0, n - hot_n):], 2.2, prof=FK.tp_head(0.6), v=0.95)
        for (x0, side, ln, s_) in twigs:
            if x0 > front - 8:
                continue
            g = W.Debris(s_).rng
            bp = W.jag(g, (c[0] + x0, c[1]), (c[0] + x0 + ln * 0.5, c[1] + side * ln), 3, 1.3)
            Lgap.stroke(bp, 1.3, prof=FK.tp_tail(0.6), v=1.0)
            if front - x0 < 50 and travelling:
                Lcool.stroke(bp, 0.6, prof=FK.tp_tail(0.7), v=0.85)
        for sp in slabs:
            dist = front - sp["x"]
            if dist < 2:
                continue
            k = min(1.0, 0.4 + dist / 26.0) * max(0.0, 1.0 - max(0.0, dist - 60) / 90.0) if arrive else 0.0
            by = c[1] + sp["side"] * sp["off"]
            if k <= 0.15:
                if dist > 30:
                    W.flake(Lrock, c[0] + sp["x"], by + sp["side"] * 3, sp["w"] * 0.4, sp["x"] * 0.1, v=0.7 * (1 - 0.4 * age), lit=0.55)
                continue
            shard(Lrock, c[0] + sp["x"], by, sp["side"], sp["h"], sp["w"], sp["lean"], k)
        if travelling:                                     # 앞머리: 달아오른 매듭 + 튀는 파편·불티
            hx = c[0] + front
            Lcrk.disc(hx - 2, c[1], 4.2, 3.4, v=0.9, edge=0.5)
            r = random.Random(seed * 7 + i)
            for j in range(6):
                a = r.uniform(-2.7, -0.4) if j % 2 else r.uniform(0.4, 2.7)
                dd = r.uniform(4, 11)
                W.ember(Lember, hx + math.cos(a) * dd - 3, c[1] + math.sin(a) * dd, -1.5 + math.cos(a), math.sin(a), r.uniform(3, 5),
                        w=0.7, v=0.85)
            for j in range(3):
                a = r.uniform(-2.6, -0.5) * (1 if j % 2 else -1)
                W.flake(Lrock, hx + math.cos(a) * 9 - 6, c[1] + math.sin(a) * 9, r.uniform(1.8, 2.8), r.uniform(0, 6), v=0.8, lit=0.55)
            for j in range(3):                             # 앞머리 바로 뒤 흙먼지
                x = front - 18 - j * 16
                if x < 6:
                    continue
                for side in (-1, 1):
                    Ldust.cloud(c[0] + x, c[1] + side * (13 + j * 2 + 3 * W.h2(j, side, i)), 4 + j * 0.8, v=0.65 - 0.1 * j,
                                flat=0.8, seed=j * 7 + i + side)
        elif not arrive or age > 0:
            for j, (x, y, rr) in enumerate(dusts):
                if x < front and W.h2(j, 7, i) < 0.85 - 0.45 * age:
                    Ldust.cloud(c[0] + x, c[1] + y * (1 + 0.2 * age), rr * (1 + 0.25 * age), v=0.6 - 0.25 * age, flat=0.8, seed=j * 5 + i)
        out.append(fr.render())
    return out


def build_crack(tiles_list=(1, 2, 3, 4, 5)):
    from gridcompat import body_meta
    bj = body_meta("player/v3/player_greatsword_charge_swing")
    hit = bj["timingMs"]["hitAt"]
    res = []
    for n in tiles_list:
        name = "greatsword_charge_crack_line_t%d" % n
        frames = {"any": crack_frames(n)}
        cut, _, origin = X.fit(frames)
        L = n * CRACK_TILE_DOTS
        data = dict(weapon="greatsword", move="greatsword_charge_swing", anchor="slam_point", pivot={"x": origin[0], "y": origin[1]},
                    rotate=True, drawnFacing="right", flipY="allowed", depth="above",
                    pivotNote="pivot = 칼끝이 바닥에 닿은 자리(몸 slamAnchors[행][impactFrame]). 그림 오른쪽 = 진행 방향 → 찍은 자리에서 커서 쪽 각도로 회전",
                    tiles=n, lengthPx=L, lengthWorld=L / 4,
                    pickRule="칸 수 = min(차지 단계 최대 3/4/5, 찍은 자리 → 커서 거리 / 16 월드 px 반올림, 최소 1) — 벽에 막히면 막힌 곳까지(내림). t%d = %d칸" % (n, n),
                    variants={"t%d" % k: "greatsword_charge_crack_line_t%d" % k for k in (1, 2, 3, 4, 5)},
                    spawn="body_ms", spawnAtMs=hit, impactFrame=0,
                    spawnNote="greatsword_charge_swing 의 impactFrame 시작(=hitAt %dms)에 1회. 함께 greatsword_ground_crack(행 m/m/l)을 같은 자리에" % hit,
                    hitShape=dict(type="rect", fromPx=0, lengthPx=L, halfWidthPx=28, frontPxByFrame=crack_front(n),
                                  activeFrames=list(range(CRACK_TRAVEL_FRAMES)), speedDotsPerMs=CRACK_SPEED,
                                  note="앞머리(frontPxByFrame)가 지나가는 칸만 맞는다(적마다 1회) — 참고값, 시스템 데이터 기준. 단위 도트(월드 px = 도트/4)"),
                    frameRoles=["앞머리 달림"] * CRACK_TRAVEL_FRAMES + ["식는 금 · 먼지"] * (len(CRACK_MS) - CRACK_TRAVEL_FRAMES),
                    holdLast="마지막 칸(식은 금)을 붙잡아 오래 남기려면 시스템이 끄는 시점을 정함(반투명 금지)",
                    design="찍은 자리에서 커서 쪽으로 땅이 갈라져 나감 — 검은 틈 + 앞머리 근처만 호박으로 달아오름(뒤는 식은 금), 양옆 흙판이 솟았다 무너짐, 앞머리에서 파편·불티, 지나간 뒤 흙먼지",
                    r58="58라운드 Q3 — 균열이 커서까지(차지 단계별 최대 3/4/5칸)", shakeHint={"px": 3 + n, "ms": 120 + 15 * n})
        X.SRC = SRC
        sheet, j, _ = X.write(name, cut, ["any"], CRACK_MS, data, [])
        j["version"] = "v3-r58"
        j["source"] = SRC
        with open(os.path.join(OUT_FX, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(j, f, ensure_ascii=False, indent=1)
        res.append((name, j["frameWidth"], j["frameHeight"], j["colors"]))
        print(name, j["frameWidth"], j["frameHeight"], "colors", j["colors"])
    return res


if __name__ == "__main__":
    a = sys.argv[1:] or ["swing", "crack"]
    if "swing" in a:
        build_swing()
    if "crack" in a:
        build_crack()
