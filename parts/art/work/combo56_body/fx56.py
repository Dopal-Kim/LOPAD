"""56라운드 새 이펙트 v3 (작업 B) — 결정적, Gemini 미사용. 색: 주인공 재·호박 + 백열 X0/X1(판정 프레임만), 시트당 14색 이하, 반투명 0.

  greatsword_ground_crack   Q5 땅 충격 강화 — 무거운 V·차지·꽂아내리기 바닥 균열 + 솟는 파편 + 먼지 + 남는 금. 행 = 크기 s·m·l (방향 무관)
  greatsword_plunge_wave    Q10 개성 발현 차지 — 꽂힌 자리에서 마우스 방향으로 땅을 가르며 나가는 충격파(오른쪽 보기, rotate: true)
  bow_perfect_release       Q9 완벽 놓기 섬광 — 화살이 생기는 점(시위 앞)에서 백열 별 + 고리 + 앞쪽 불티(rotate: true)
그리기 도구 = combo55/fx55(→ fx_weapons_v3/wkit · fx_v3/fxkit) 그대로.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "combo55")))
import fx55 as X  # noqa: E402
from fx55 import W, FK  # noqa: E402

SRC = "parts/art/work/combo56_body/build.py fx (56라운드 Q5·Q9·Q10 작업 B)"
CO = X.CO
GKY = 0.85                       # 바닥 눌림(방향 무관 시트만 — 회전 시트는 원형 그대로)
R_GS = 51 * 4                    # 대검 R = 51 월드 px = 204 도트


def _write(name, frames, dirs, ms, data, glow):
    X.SRC = SRC
    sheet, j, out = X.write(name, frames, dirs, ms, data, glow)
    j["version"] = "v3-r56"
    j["source"] = SRC
    with open(os.path.join(W.OUT_FX, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
    return sheet, j, out


def _rubble(L, x, y, size, rot, v):
    W.flake(L, x, y, size, rot, v=v, lit=0.55)


# =============================================================================
# 바닥 균열 (s · m · l)
# =============================================================================
CRACK_SIZES = {"s": dict(radius=round(R_GS * 0.5), heavy=1.0, seed=101, use="V 정면 내려찍기(greatsword_cleave) — 관성 최대면 m"),
               "m": dict(radius=round(R_GS * 0.7), heavy=1.25, seed=102, use="차지 내려찍기 1·2단(greatsword_charge_slam)"),
               "l": dict(radius=round(R_GS * 1.0), heavy=1.6, seed=103, use="차지 내려찍기 3단 · 꽂아내리기(greatsword_charge_plunge)")}
CRACK_MS = [40, 50, 60, 80, 110, 150, 200, 260]
CRACK_GLOW = [0]


def crack_frames(radius, heavy, seed):
    """비평 반영: 금은 '검은 틈 + 안쪽만 달아오름'(바깥으로 갈수록 식음) — 나뭇가지·번개처럼 보이지 않게 잔가지는 굵은 금에 하나씩.
    가는 금은 굵은 금 사이에 고르게. 파편은 크게(윗면 밝은 재 판), 먼지는 납작하고 진하게. 식은 금은 점선 대신 가장 어두운 호박 실선."""
    t = X.T("right", *CO)
    rng = W.Debris(seed).rng
    c = CO
    n_main = 5
    base = rng.uniform(0, 6.28)
    cracks = []
    for k in range(n_main):
        a = base + k * 2 * math.pi / n_main + rng.uniform(-0.28, 0.28)
        cracks.append(dict(a=a, ln=rng.uniform(0.85, 1.0), d0=rng.uniform(0.0, 0.2), main=True, s=rng.randint(0, 9999)))
    for k in range(n_main):                               # 굵은 금 사이에 가는 금 하나씩
        a = base + (k + 0.5) * 2 * math.pi / n_main + rng.uniform(-0.25, 0.25)
        cracks.append(dict(a=a, ln=rng.uniform(0.4, 0.62), d0=rng.uniform(0.1, 0.3), main=False, s=rng.randint(0, 9999)))
    paths = []
    for cr in cracks:
        g = W.Debris(cr["s"]).rng
        r0 = radius * (0.14 + 0.25 * cr["d0"])
        r1 = radius * cr["ln"]
        a1 = cr["a"] + g.uniform(-0.18, 0.18)
        p0 = (c[0] + math.cos(cr["a"]) * r0, c[1] + math.sin(cr["a"]) * r0 * GKY)
        p1 = (c[0] + math.cos(a1) * r1, c[1] + math.sin(a1) * r1 * GKY)
        pts = W.jag(g, p0, p1, n=7 if cr["main"] else 4, amp=(3.4 if cr["main"] else 2.0) * heavy ** 0.5)
        twig = None
        if cr["main"]:
            q = pts[4]
            ab = cr["a"] + (0.75 if cr["s"] % 2 else -0.75)
            ln = radius * 0.24
            twig = W.jag(g, q, (q[0] + math.cos(ab) * ln, q[1] + math.sin(ab) * ln * GKY), 3, 1.5)
        paths.append((cr, pts, twig))

    def part(pts, f):
        """앞쪽 f 비율만(금이 달려 나가는 중)."""
        if f >= 1.0:
            return pts
        L = [0.0]
        for i in range(1, len(pts)):
            L.append(L[-1] + math.dist(pts[i - 1], pts[i]))
        cut = L[-1] * f
        out = [pts[0]]
        for i in range(1, len(pts)):
            if L[i] <= cut:
                out.append(pts[i])
            else:
                u = (cut - L[i - 1]) / max(1e-6, L[i] - L[i - 1])
                out.append((pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * u, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * u))
                break
        return out

    slabs = []
    for j in range(int(7 * heavy)):
        a = rng.uniform(0, 2 * math.pi)
        r = radius * rng.uniform(0.18, 0.55)
        slabs.append(dict(x=math.cos(a) * r, y=math.sin(a) * r * GKY, vx=math.cos(a) * rng.uniform(3, 6) * heavy,
                          vy=math.sin(a) * rng.uniform(1.5, 3.5), up=rng.uniform(16, 28) * heavy ** 0.7,
                          size=rng.uniform(5.0, 8.0) * heavy ** 0.5, rot=rng.uniform(0, 6.28), spin=rng.uniform(-0.9, 0.9)))
    pebbles = []
    for j in range(int(14 * heavy)):
        a = rng.uniform(0, 2 * math.pi)
        r = radius * rng.uniform(0.1, 0.45)
        pebbles.append(dict(x=math.cos(a) * r, y=math.sin(a) * r * GKY, vx=math.cos(a) * rng.uniform(4, 9) * heavy,
                            vy=math.sin(a) * rng.uniform(2, 5), up=rng.uniform(10, 20) * heavy ** 0.6, size=rng.uniform(1.6, 2.6)))
    embers = []
    for j in range(int(10 * heavy)):
        a = rng.uniform(-math.pi, 0)
        sp = rng.uniform(5, 11) * heavy ** 0.5
        embers.append((rng.uniform(-10, 10), rng.uniform(-4, 4), math.cos(a) * sp, math.sin(a) * sp * 0.9 - 2, rng.uniform(3, 6)))
    grow = [0.6, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    hot = [0.97, 0.74, 0.62, 0.52, 0.4, 0.3, 0.22, 0.0]
    T_UP = [0.35, 1.0, 1.7, 2.3, 9, 9, 9, 9]               # 파편 비행 시각(9 = 착지)
    out = []
    for i in range(len(CRACK_MS)):
        fr = W.Frame(X.CANVAS, X.CANVAS, t)
        Ldent = fr.L([W.B0, W.B1])
        Ldust = fr.L(W.R_DUST)
        Lgap = fr.L([W.B0])
        Lrim = fr.L([W.B1, W.B2])
        Lcrk = fr.L(W.R_EDGE)
        Lhot = fr.L(W.R_HOT)
        Lslab = fr.L([W.B0, W.B1, W.B2, W.S2])
        Lember = fr.L(W.R_EMBER)
        dr = radius * (0.2 + 0.03 * min(i, 2))
        Ldent.disc(c[0], c[1] + 1, dr, dr * GKY * 0.8, v=0.95, edge=0.55)
        Lrim.arc(c[0], c[1] + 1, dr + 1.5, dr * GKY * 0.8 + 1.5, math.pi * 1.05, math.pi * 1.95, 1.3, v=0.95)   # 패인 자리 먼 쪽 턱(빛)
        for cr, pts, twig in paths:
            seg = part(pts, grow[i] if cr["main"] else min(1.0, grow[i] * 1.2))
            wd = (2.1 if cr["main"] else 1.2) * heavy ** 0.6
            Lrim.stroke([(q[0], q[1] - 1.3) for q in seg], wd + 0.4, prof=FK.tp_tail(0.5), v=0.95)   # 틈 위 턱(빛) — 어두운 바닥에서 금이 읽히게
            Lgap.stroke(seg, wd + 1.0, prof=FK.tp_tail(0.5), v=1.0)
            if twig is not None and i >= 1:
                Lgap.stroke(twig, 1.4, prof=FK.tp_tail(0.6), v=1.0)
            if hot[i] > 0:
                inner = part(seg, 0.62 if cr["main"] else 0.45)   # 달아오른 건 안쪽만 — 바깥은 검은 틈
                vp = (lambda tt, h=hot[i]: max(0.3, 1.0 - 0.75 * tt))
                Lcrk.stroke(inner, max(0.6, wd * 0.5), prof=FK.tp_tail(0.7), v=hot[i], vprof=vp)
        if i == 0:                                      # 충돌 섬광(판정 순간만 백열)
            Lhot.disc(c[0], c[1], radius * 0.2, radius * 0.2 * GKY, v=1.0, edge=0.55)
            Lhot.arc(c[0], c[1], radius * 0.42, radius * 0.42 * GKY, 0, 2 * math.pi, 2.0, v=0.9, dash=(10, 0.7, 0.15))
        elif i == 1:
            Lcrk.arc(c[0], c[1], radius * 0.66, radius * 0.66 * GKY, 0, 2 * math.pi, 1.5, v=0.58, dash=(12, 0.5, 0.3))
        if 1 <= i <= 5:                                  # 먼지 링(바닥에 납작하게)
            k = (i - 1) / 4
            nd = int(22 * heavy ** 0.5)
            for j in range(nd):
                a = j * 2 * math.pi / nd + W.h2(j, 1, seed) * 0.3
                rr = radius * (0.5 + 0.45 * k) * (0.9 + 0.18 * W.h2(j, 2, seed))
                if W.h2(j, i, seed) < 0.95 - 0.12 * i:
                    Ldust.cloud(c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr * GKY, (9 + 5 * k) * heavy ** 0.5,
                                v=0.9 - 0.4 * k, flat=0.5, seed=j + i * 31)
        for s in slabs:
            tt = T_UP[i]
            land = tt >= 2.4
            tt = min(tt, 2.4)
            z = 0.0 if land else max(0.0, s["up"] * tt * (1 - tt / 2.4))
            x = c[0] + s["x"] + s["vx"] * tt
            y = c[1] + s["y"] + s["vy"] * tt - z
            if i >= 6 and W.h2(int(s["x"]), int(s["y"]), i) < 0.3 * (i - 5):
                continue
            if z > 2:                                     # 떠 있는 동안 바닥 그림자
                Lgap.stroke([(x - s["size"] * 0.6, y + z), (x + s["size"] * 0.6, y + z)], 0.9, v=1.0)
            _rubble(Lslab, x, y, s["size"] * (1.0 if i < 6 else 0.8), s["rot"] + s["spin"] * tt, 1.0 if not land else 0.75)
        for p in pebbles:
            if i == 0 or i >= 4:
                continue
            tt = T_UP[i] * 1.05
            z = max(0.0, p["up"] * tt * (1 - tt / 2.6))
            Lslab.stamp(c[0] + p["x"] + p["vx"] * tt, c[1] + p["y"] + p["vy"] * tt - z, p["size"] * 0.55, 0.85, soft=0)
        if i <= 2:
            for (ex, ey, vx, vy, ln) in embers:
                tt = i + 0.6
                x, y = c[0] + ex + vx * tt, c[1] + ey + vy * tt + 0.9 * tt * tt
                W.ember(Lember, x, y, vx, vy + 1.8 * tt, ln * (1.2 - 0.3 * i), w=0.8, v=0.95 - 0.25 * i)
        out.append(fr.render())
    return out


def build_ground_crack():
    rows = {}
    for key, sp in CRACK_SIZES.items():
        rows[key] = crack_frames(sp["radius"], sp["heavy"], sp["seed"])
    cut, _, origin = X.fit(rows)
    dirs = list(CRACK_SIZES)
    data = dict(weapon="greatsword", sizes=dirs, rowBy="size", rowsAre="sizes",
                layout="rows = sizes (s, m, l), columns = frames — 행을 크기로 고른다(방향 무관, 회전하지 않음)",
                anchor="hitbox_center", pivot={"x": origin[0], "y": origin[1]}, rotate=False, depth="above",
                pivotNote="pivot = 내려찍은 자리(V·차지 = 쐐기 끝점 충격원 중심, 꽂아내리기 = 꽂힌 자리 plantAnchors). 바닥 금·파편은 세로 0.85 로 눌러 바닥에 놓임",
                sizeInfo={k: dict(row=i, radiusPx=v["radius"], radiusR=round(v["radius"] / R_GS, 2), useFor=v["use"]) for i, (k, v) in enumerate(CRACK_SIZES.items())},
                spawn="impact", spawnNote="몸 시트 impactFrame 시작(=hitAt)에 1회. greatsword_cleave_impact 와 함께 써도 되고 대신 써도 된다(이쪽이 더 무겁고 오래 남음)",
                groundKy=GKY, impactFrame=0, frameRoles=["충돌 백열 + 금이 달려 나감", "금 끝까지·파편 솟음·먼지", "파편 정점", "파편 떨어짐",
                                                         "파편 남음·금 식음", "식은 금(점선 불씨)", "식은 금", "사라짐 직전"],
                lingerNote="f4~f7(약 0.7초)은 식은 금·남은 조각만 — 바닥 데칼처럼 오래 남기고 싶으면 마지막 프레임을 붙잡아 두고 서서히 지워도 된다(반투명 금지라 시스템이 끄는 시점만 정함)",
                shakeHint={"s": {"px": 4, "ms": 100}, "m": {"px": 6, "ms": 130}, "l": {"px": 8, "ms": 170}},
                design="Q5 땅 충격 강화 — 패인 자리 + 사방으로 꺾여 달리는 굵은 금 5·가는 금 6·잔가지, 솟았다 떨어져 남는 바닥 판 조각, 납작한 먼지 링, 불티",
                paletteSwap="none")
    data["directionsNote"] = "directions 칸에 크기 키(s·m·l)를 넣었다 — 행 = 크기. 방향으로 고르지 말 것(회전·반전 없음)"
    return _write("greatsword_ground_crack", cut, dirs, CRACK_MS, data, CRACK_GLOW)[1]


# =============================================================================
# 꽂아내리기 충격파 (오른쪽 보기, rotate)
# =============================================================================
WAVE_LEN = round(R_GS * 2.0)          # 408 도트 = 2R (참고값)
WAVE_HALF_W = 52                      # 판정 반폭 참고(도트)
WAVE_MS = [40, 40, 40, 50, 50, 60, 70, 90]
WAVE_FRONT = [70, 150, 230, 310, 380, 408, 408, 408]
WAVE_GLOW = [0, 1, 2, 3, 4]


def wave_frames(seed=201):
    """비평 반영: 앞머리 = 가운데가 두꺼운 채운 물결 띠(괄호·활처럼 가는 선 아님) + 뒤로 흩어지는 불티, 금은 앞머리 근처만 달아오르고
    뒤는 빨리 식음(어두운 호박 실선), 길 양옆 바위 가시 = 바깥을 향한 삼각 조각(빛 면 + 그늘 면), 끝난 뒤 먼지는 불규칙."""
    t = X.T("right", *CO)
    rng = W.Debris(seed).rng
    c = CO
    spine = W.jag(rng, (c[0] + 6, c[1]), (c[0] + WAVE_LEN, c[1]), n=26, amp=3.5)
    twigs = []
    for k in range(12):
        x0 = 24 + (WAVE_LEN - 48) * k / 11 + rng.uniform(-10, 10)
        side = 1 if k % 2 else -1
        twigs.append((x0, side, rng.uniform(12, 24), rng.randint(0, 9999)))
    spikes = []
    for k in range(16):
        x0 = 26 + (WAVE_LEN - 46) * k / 15 + rng.uniform(-5, 5)
        side = 1 if k % 2 == 0 else -1
        spikes.append(dict(x=x0, side=side, off=rng.uniform(6, 11), h=rng.uniform(20, 32), w=rng.uniform(8.0, 12.0),
                           lean=rng.uniform(-0.35, 0.35)))
    dusts = [(rng.uniform(20, WAVE_LEN - 10), rng.choice((-1, 1)) * rng.uniform(14, 34), rng.uniform(7, 12)) for _ in range(16)]

    def spine_until(x):
        pts = [p for p in spine if p[0] <= c[0] + x]
        return pts

    def shard(L, bx, by, side, h, w, lean, k):
        """바깥(side)을 향한 바위 조각 — 화면 좌표 삼각형 두 면."""
        tip = (bx + lean * h * k, by + side * h * k)
        l0, r0 = (bx - w * 0.5, by), (bx + w * 0.5, by)
        mid = (bx + lean * h * k * 0.4, by + side * h * k * 0.45)
        for tri, v in (((l0, tip, mid), 0.95), ((mid, tip, r0), 0.6), ((l0, mid, r0), 0.75)):
            xs = [q[0] for q in tri]
            ys = [q[1] for q in tri]
            for yy in range(int(min(ys)) - 1, int(max(ys)) + 2):
                for xx in range(int(min(xs)) - 1, int(max(xs)) + 2):
                    px_, py_ = xx + 0.5, yy + 0.5
                    sg = None
                    ok = True
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
                        L.put(xx, yy, v)

    out = []
    for i, front in enumerate(WAVE_FRONT):
        fr = W.Frame(X.CANVAS, X.CANVAS, t)
        Ldust = fr.L(W.R_DUST)
        Lgap = fr.L([W.B0])
        Lcool = fr.L([W.A18, W.A19])
        Lcrk = fr.L(W.R_EDGE)
        Lrock = fr.L([W.B1, W.B2, W.S1, W.S2])
        Lband = fr.L([W.A19, W.A21, W.A23, W.A25])
        Lcrest = fr.L(W.R_HOT)
        Lember = fr.L(W.R_EMBER)
        travelling = i <= 4
        pts = spine_until(front)
        if len(pts) >= 2:
            Lgap.stroke(pts, 3.0, prof=FK.tp_both(0.25, 0.75), v=1.0)
            n = len(pts)
            hot_n = 6 if travelling else 0
            cool = pts[:max(2, n - hot_n + 1)]
            Lcool.stroke(cool, 1.0, v=0.9 if i < 6 else 0.5)
            if hot_n and n > 2:
                Lcrk.stroke(pts[max(0, n - hot_n):], 1.8, prof=FK.tp_head(0.6), v=0.95 if i <= 1 else 0.86)
        for (x0, side, ln, s_) in twigs:
            if x0 > front - 12:
                continue
            g = W.Debris(s_).rng
            bp = W.jag(g, (c[0] + x0, c[1]), (c[0] + x0 + ln * 0.45, c[1] + side * ln), 3, 1.4)
            Lgap.stroke(bp, 1.5, prof=FK.tp_tail(0.6), v=1.0)
            if front - x0 < 90 and travelling:
                Lcool.stroke(bp, 0.7, prof=FK.tp_tail(0.7), v=0.9)
        for sp in spikes:
            dist = front - sp["x"]
            if dist < 4:
                continue
            k = min(1.0, 0.35 + dist / 40.0) * max(0.0, 1.0 - max(0.0, dist - 110) / 170.0) if i <= 5 else 0.0
            by = c[1] + sp["side"] * sp["off"]
            if k <= 0.15:
                if dist > 60:                              # 무너진 잔해
                    _rubble(Lrock, c[0] + sp["x"], by + sp["side"] * 4, sp["w"] * 0.45, sp["x"] * 0.1, 0.7)
                continue
            shard(Lrock, c[0] + sp["x"], by, sp["side"], sp["h"], sp["w"], sp["lean"], k)
        if travelling:
            r = 44.0
            cx = c[0] + front - r
            wmax = [9.0, 8.5, 8.0, 7.0, 6.0][i]
            # 채운 물결 띠: 가운데 두꺼움 → 위·아래 끝 뾰족
            Lband.arc(cx - wmax * 0.6, c[1], r, r * 1.12, -1.05, 1.05, wmax, prof=FK.tp_both(0.8, 0.5), v=0.9)
            Lcrest.arc(cx, c[1], r, r * 1.12, -1.0, 1.0, 2.2, prof=FK.tp_both(0.6, 0.5), v=0.95 if i <= 2 else 0.86)
            for j in range(9):                              # 불티: 앞머리 양 끝에서 바깥·뒤로 흩어짐
                a = (j - 4) * 0.24
                ex = c[0] + front - r + math.cos(a) * r - 4 - (j % 3) * 5
                ey = c[1] + math.sin(a) * r * 1.12
                vx, vy = -2.0, math.copysign(3.0, a) if abs(a) > 0.05 else 0.0
                W.ember(Lember, ex, ey + vy * 2, vx, vy + 0.01, 5 + 2 * (j % 3), w=0.8, v=0.9)
            for j in range(5):                              # 먼지가 앞머리 바로 뒤에서 일어남
                x = front - 34 - j * 24
                if x < 8:
                    continue
                for side in (-1, 1):
                    Ldust.cloud(c[0] + x, c[1] + side * (26 + j * 3 + 5 * W.h2(j, side, i)), 5 + j * 1.0, v=0.7 - 0.1 * j,
                                flat=0.8, seed=j * 7 + i + side)
        else:
            k = (i - 5) / 2
            for j, (x, y, r) in enumerate(dusts):
                if W.h2(j, 7, i) < 0.85 - 0.3 * k:
                    Ldust.cloud(c[0] + x, c[1] + y * (1 + 0.15 * k), r * (1 + 0.2 * k), v=0.65 - 0.2 * k, flat=0.8, seed=j * 5 + i)
        out.append(fr.render())
    return out


def build_plunge_wave():
    frames = {"any": wave_frames()}
    cut, _, origin = X.fit(frames)
    data = dict(weapon="greatsword", anchor="plant_point", pivot={"x": origin[0], "y": origin[1]}, rotate=True, drawnFacing="right",
                flipY="allowed", depth="above",
                pivotNote="pivot = 칼이 꽂힌 자리(몸 시트 plantAnchors, 무기 시트 plantAnchors). 마우스 방향 각도로 회전(조준 0° = 그림의 오른쪽). 중력 표현 없음 — 어느 각도로 돌려도 된다",
                spawn="impact", spawnNote="greatsword_charge_plunge 의 impactFrame 시작(=hitAt)에 1회. 함께 greatsword_ground_crack 행 l 을 꽂힌 자리에",
                hitShape=dict(type="rect", fromPx=0, lengthPx=WAVE_LEN, halfWidthPx=WAVE_HALF_W, lengthR=2.0,
                              frontPxByFrame=WAVE_FRONT, activeFrames=WAVE_GLOW,
                              note="참고값 — 앞머리(frontPxByFrame)가 지나간 칸만 맞게 하거나 판정 프레임 동안 전체 사각형. 시스템 데이터가 기준. 단위 도트(월드 px = 도트/4)"),
                impactFrame=0, frameRoles=["앞머리 출발(백열 물결)", "달림", "달림", "달림", "끝 근처", "끝 도달·식음", "가시 무너짐·먼지", "식은 금"],
                design="Q10 개성 발현 차지 — 칼을 꽂은 자리에서 땅을 가르는 금이 마우스 방향으로 달리고, 앞머리에 앞으로 볼록한 백열 물결·불티, 지나간 자리 양옆으로 바위 가시가 솟았다 무너짐 + 먼지",
                shakeHint={"px": 7, "ms": 160})
    return _write("greatsword_plunge_wave", cut, ["any"], WAVE_MS, data, WAVE_GLOW)[1]


# =============================================================================
# 완벽 놓기 섬광 (활)
# =============================================================================
PERFECT_MS = [30, 40, 50, 60, 80]
PERFECT_GLOW = [0, 1]


def perfect_frames(seed=301):
    t = X.T("right", *CO)
    rng = W.Debris(seed).rng
    c = (CO[0], CO[1])
    sparks = [(rng.uniform(-0.95, 0.95), rng.uniform(7, 17), rng.uniform(3, 7)) for _ in range(12)]
    back = [(math.pi + rng.uniform(-0.7, 0.7), rng.uniform(4, 8), rng.uniform(3, 5)) for _ in range(5)]
    out = []
    for i in range(len(PERFECT_MS)):
        fr = W.Frame(X.CANVAS, X.CANVAS, t)
        Lsmoke = fr.L(W.R_ASHG)
        Lring = fr.L(W.R_EDGE)
        Lhot = fr.L(W.R_HOT)
        Lember = fr.L(W.R_EMBER)
        if i == 0:
            Lhot.star4(c[0], c[1], 30, w=2.2, v=1.0, diag=0.45)
            Lhot.ray(c[0], c[1], 0.0, 0, 46, 2.0, prof=FK.tp_tail(0.8), v=1.0)          # 앞(화살 진행)으로 긴 빛살
            Lhot.disc(c[0], c[1], 5, 5, v=1.0, edge=0.7)
            Lring.ring(c[0], c[1], 9, 1.6, v=0.85)
        elif i == 1:
            Lhot.star4(c[0], c[1], 22, w=1.8, v=0.95, diag=0.25)
            Lhot.ray(c[0], c[1], 0.0, 4, 60, 1.6, prof=FK.tp_both(0.5, 0.35), v=0.95)
            Lring.ring(c[0], c[1], 17, 2.0, v=0.9, dash=(10, 0.8, 0.05))
            Lring.arc(c[0] + 10, c[1], 22, 26, -0.9, 0.9, 1.8, prof=FK.tp_both(0.6), v=0.85)      # 앞으로 밀리는 충격 호
        else:
            k = (i - 2) / 2
            Lring.ring(c[0], c[1], 24 + 8 * k, 1.4 - 0.4 * k, v=0.6 - 0.2 * k, dash=(10, 0.6 - 0.15 * k, 0.1 * i))
            Lring.arc(c[0] + 20 + 14 * k, c[1], 26 + 6 * k, 30 + 6 * k, -0.8, 0.8, 1.4 - 0.4 * k, prof=FK.tp_both(0.6), v=0.55 - 0.15 * k,
                      dash=(14, 0.7, 0.2) if i == 4 else None)
            if i == 2:
                Lring.star4(c[0], c[1], 12, w=1.2, v=0.6)
            if i <= 3:                                     # 시위 뒤로 작은 재 연기 두 덩이
                for j in (-1, 1):
                    Lsmoke.cloud(c[0] - 8 - 6 * k, c[1] + j * (5 + 3 * k), 3 + 2 * k, v=0.6 - 0.2 * k, flat=0.8, seed=j + i)
        for (a, sp, ln) in sparks:
            if i == 0:
                continue
            tt = i
            x, y = c[0] + math.cos(a) * sp * tt + 6, c[1] + math.sin(a) * sp * tt
            W.ember(Lember, x, y, math.cos(a), math.sin(a), ln * (1.3 - 0.25 * i), w=0.8, v=0.98 - 0.18 * i)
        for (a, sp, ln) in back:
            if 1 <= i <= 3:
                x, y = c[0] + math.cos(a) * sp * i, c[1] + math.sin(a) * sp * i
                W.ember(Lember, x, y, math.cos(a), math.sin(a), ln, w=0.7, v=0.8 - 0.2 * i)
        out.append(fr.render())
    return out


def build_perfect_release():
    frames = {"any": perfect_frames()}
    cut, _, origin = X.fit(frames)
    data = dict(weapon="bow", anchor="projectile", pivot={"x": origin[0], "y": origin[1]}, rotate=True, drawnFacing="right",
                depth="above", spawn="perfect_release",
                pivotNote="pivot = 화살이 생기는 점(활 시위 앞 — bow_muzzle_rapid 와 같은 자리, 무기 시트 arrowSpawnAnchors). 발사 각도로 회전",
                spawnNote="56라운드 Q9: 가득 당긴 직후 0.15초 창 안에 놓았을 때(완벽 놓기)만 1회. 일반 놓기는 없음(또는 bow_muzzle_rapid)",
                design="Q9 완벽 놓기 — f0 백열 4빛살 별 + 화살 진행 쪽 긴 빛살 + 작은 고리 → f1 별·빛살·고리 퍼짐 + 앞으로 밀리는 충격 호 → 식으며 끊긴 고리·재 연기·불티",
                glowNote="판정 순간 백열 허용(Q9 작업 지시) — glowFrames(f0·f1)만 X0/X1·A26, f2~ 는 A25 이하",
                frameRoles=["백열 별(판정)", "별·고리 퍼짐(판정)", "식음", "식음", "사라짐"])
    return _write("bow_perfect_release", cut, ["any"], PERFECT_MS, data, PERFECT_GLOW)[1]


def build_all():
    out = {}
    for fn in (build_ground_crack, build_plunge_wave, build_perfect_release):
        j = fn()
        out[j["image"][:-4]] = dict(frame=[j["frameWidth"], j["frameHeight"]], colors=j["colors"], pivot=j["pivot"])
        print("%-28s %dx%d colors %d" % (j["image"], j["frameWidth"], j["frameHeight"], j["colors"]))
    return out


if __name__ == "__main__":
    build_all()
