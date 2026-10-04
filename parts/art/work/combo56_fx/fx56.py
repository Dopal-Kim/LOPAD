"""56라운드 이펙트 그리기 — 붓획 연격(칼·대검·단검) · 일섬 선 · 그림자 분신.

좌표: 로컬 '오른쪽 보기'(x = 조준 방향, y = 화면 아래, 원점 = 판정 원점 = 피벗 위 40 도트) → 방향 각도로 회전(TA).
55라운드 규약 그대로: 모든 방향은 회전(left = 180°), 높이 z 는 화면 위(-y). 대검은 8방향 행을 직접 그림(대각 = 45° 회전 좌표로 다시 래스터, 작업 B 몸 행 순서).
"""
import json
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "combo55")))
import brush as BR  # noqa: E402
from brush import W, FK  # noqa: E402
import fx55 as X  # noqa: E402  (fit · clamp_cool — combo55, 읽기만)

CANVAS = X.CANVAS
CO = X.CO
HIT_UP = X.HIT_UP
DIRS4 = ["down", "up", "left", "right"]
DIRS8 = ["down", "up", "left", "right", "down-right", "down-left", "up-right", "up-left"]   # 작업 B 대검 몸·무기 8방향 행 순서
DIR_ANG = {"right": 0.0, "down": 90.0, "left": 180.0, "up": -90.0,
           "down-right": 45.0, "down-left": 135.0, "up-left": -135.0, "up-right": -45.0, "any": 0.0}
SRC = "parts/art/work/combo56_fx/build.py (56라운드 Q11 붓획 · Q1 칼 템포 · Q2 일섬 · Q3 그림자 분신)"
VERSION = "v3-r56"


class TA(W.T):
    def __init__(self, d, ox, oy):
        super().__init__("right", ox, oy)
        a = math.radians(DIR_ANG[d])
        c, s = math.cos(a), math.sin(a)
        self.m = (c, -s, s, c)
        self.d = d


def frame(t):
    return W.Frame(CANVAS, CANVAS, t)


# =============================================================================
# 호 붓획(칼 1·2타 · 대검 수평) — 6프레임: pre · draw(머리 55%) · draw(끝까지) · 소멸 ×3
# =============================================================================
STYLE = {
    "katana": dict(ink=BR.INK_K, flake=BR.FLAKE, vmax=0.9, split=2.2, dry=0.55, drops=7, flakes=5, flake_size=1.5, glint=0),
    "gs": dict(ink=BR.INK_G, flake=BR.FLAKE_G, vmax=0.9, split=1.4, dry=0.58, drops=12, flakes=9, flake_size=2.4, glint=0),
}

PLAN_ARC = [("pre", dict(head=0.1)), ("draw", dict(head=0.55)), ("draw", dict(head=1.0)),
            ("decay", dict(k=0.33)), ("decay", dict(k=0.66)), ("decay", dict(k=1.0))]


def arc_frames(style, d, R, a0, a1, wmax, z=(0, 0), seed=1, plan=PLAN_ARC):
    st = STYLE[style]
    t = TA(d, *CO)
    z0, z1 = z
    pts = BR.arc_points(t, R - wmax * 0.45, a0, a1, lambda s: z0 + (z1 - z0) * s)
    S = BR.Stroke(pts, wmax, seed=seed, split=st["split"], drops=st["drops"], dry_from=st["dry"])
    return _stroke_frames(S, st, plan, seed)


def _stroke_frames(S, st, plan, seed, extra=None):
    out = []
    prev_tail = 0.0
    for i, (kind, p) in enumerate(plan):
        fr = frame(None)
        Lf = fr.L(st["flake"])
        Lb = fr.L(st["ink"])
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        if kind == "pre":                                    # 붓 끝이 막 닿음(판정 전 — A23 이하)
            S.draw(Lb, head=p["head"], vmax=0.6, drops=False)
        elif kind == "draw":
            S.draw(Lb, head=p["head"], vmax=st["vmax"], hot=True, Lhot=Lh, head_glint=st["glint"])
            if p["head"] >= 0.999:
                _embers(Le, S, seed, 0)
        else:
            k = p["k"]
            tail = 0.12 + 0.62 * k
            S.draw(Lb, head=1.0, tail=tail, vmax=st["vmax"] * (0.9 - 0.2 * k), wk=1 - 0.28 * k, k=k, fall=3 + 9 * k)
            S.flakes(Lf, k, max(0.0, prev_tail - 0.05), tail + 0.08, st["flakes"], size=st["flake_size"], fall=10.0, seed=i)
            if k < 0.5:
                _embers(Le, S, seed, 1)
            prev_tail = tail
        if extra:
            extra(fr, i, kind, p)
        out.append(fr.render())
    return out



def _embers(Le, S, seed, age):
    """획 끝에서 접선 방향으로 튀는 불티 몇 개(짧은 바늘, A23 이하)."""
    r = random.Random(seed * 13 + 1)
    ex, ey = S.p[-1]
    tx, ty = S.tangent_end()
    for j in range(4):
        a = math.atan2(ty, tx) + r.uniform(-0.5, 0.5)
        dist = r.uniform(4, 10) + age * r.uniform(8, 14)
        x, y = ex + math.cos(a) * dist, ey + math.sin(a) * dist + age * age * 3
        W.ember(Le, x, y, math.cos(a), math.sin(a), r.uniform(2.5, 4.5) * (1 - 0.4 * age), w=0.6, v=0.9 - 0.3 * age)


# =============================================================================
# 단검 찌르기 붓획 — 짧게 튕겨 낸 획(丿), 4~5프레임: pre · hit(끝까지, 머리 백열) · 소멸
# =============================================================================
def thrust_frames(d, ang, x0, x1, wmax, bend, F, impact, seed):
    t = TA(d, *CO)
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    n = 40
    pts = []
    for i in range(n + 1):
        u = i / n
        along = x0 + (x1 - x0) * u
        lat = bend * math.sin(math.pi * u) * (1 - 0.3 * u)
        pts.append(t((ca * along - sa * lat, sa * along + ca * lat)))
    S = BR.Stroke(pts, wmax, seed=seed, peak=0.5, dry_from=0.7, split=1.0, drops=5, start_w=0.12, end_w=0.5)
    st = dict(ink=BR.INK_K, flake=BR.FLAKE, vmax=0.9, glint=0, flakes=4, flake_size=1.4)
    nd = F - 1 - impact
    plan = [("pre", dict(head=0.4))] * impact + [("draw", dict(head=1.0))] + \
           [("decay", dict(k=(j + 1) / nd)) for j in range(nd)]
    return _stroke_frames(S, st, plan, seed)


# =============================================================================
# 세로 붓획(대검 V 내려찍기 · 차지 내려찍기) — 머리 위 → 앞 지면, 지면에서 쐐기 끝까지 짧은 붓획 + 바닥 금
# =============================================================================
PLAN_V = [("pre", dict(head=0.15)), ("draw", dict(head=0.6)), ("impact", {}),
          ("decay", dict(k=0.33)), ("decay", dict(k=0.66)), ("decay", dict(k=1.0))]


def vertical_frames(d, L, wmax=18, lat=42.0, heavy=1.0, seed=3, Rv=150.0, plan=PLAN_V):
    t = TA(d, *CO)

    def P(phi):
        f = Rv * math.cos(phi)
        z = Rv * 1.05 * math.sin(phi)
        r = -lat * math.sin(phi) ** 0.7
        x, y = t((f, r))
        return x, y - z

    p0, p1 = math.radians(105), 0.0
    pts = [P(p0 + (p1 - p0) * i / 120) for i in range(121)]
    S = BR.Stroke(pts, wmax, seed=seed, peak=0.55, dry_from=0.8, split=0.6, drops=0, start_w=0.1, end_w=0.75)
    # 지면 붓획: 칼이 닿은 자리(0.85 Rv) → 쐐기 끝(L) — 끝에서 갈라짐
    gpts = [t((Rv * 0.85 + (L - Rv * 0.85) * i / 30, 0.0)) for i in range(31)]
    G = BR.Stroke(gpts, wmax * 0.55, seed=seed + 1, peak=0.25, dry_from=0.6, split=1.3, drops=8, start_w=0.7, end_w=0.4)
    rng = random.Random(seed)
    cracks = []
    main = W.jag(rng, (Rv * 0.75, 0.0), (L * 0.97, 0.0), n=9, amp=3.0 + L * 0.008)
    cracks.append((main, 1.4 * heavy, 0.0))
    for sgn in (-1, 1):
        for j in range(2):
            f0 = L * rng.uniform(0.45, 0.8)
            ang = sgn * math.radians(rng.uniform(8, 17))
            ln = L * rng.uniform(0.12, 0.22)
            cracks.append((W.jag(rng, (f0, 0.0), (f0 + math.cos(ang) * ln, math.sin(ang) * ln), n=4, amp=1.6), 0.8 * heavy, 0.25 + 0.2 * j))
    out = []
    for i, (kind, p) in enumerate(plan):
        fr = frame(t)
        Lgr = fr.L([W.B0, W.B1, W.B2])
        Lcrk = fr.L([W.A18, W.A19, W.A21, W.A23])
        Lf = fr.L(BR.FLAKE_G)
        Lb = fr.L(BR.INK_G)
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        if kind == "pre":
            S.draw(Lb, head=p["head"], vmax=0.6, drops=False)
        elif kind == "draw":
            S.draw(Lb, head=p["head"], vmax=0.82, drops=False)       # 내려오는 중(판정 전) — 백열 없음
        elif kind == "impact":
            S.draw(Lb, head=1.0, tail=0.15, vmax=0.88, drops=False)
            G.draw(Lb, head=1.0, vmax=0.9, hot=True, Lhot=Lh)
            S.hot_head(Lh, 0.999)                                     # 칼이 땅에 닿은 자리 몇 도트
        else:
            k = p["k"]
            S.draw(Lb, head=1.0, tail=0.3 + 0.6 * k, vmax=0.8 - 0.2 * k, wk=1 - 0.3 * k, k=k, drops=False)
            G.draw(Lb, head=1.0, tail=0.1 + 0.6 * k, vmax=0.82 - 0.2 * k, wk=1 - 0.25 * k, k=k, fall=2 + 6 * k)
            S.flakes(Lf, k, 0.3, 1.0, 5, size=2.2, fall=8.0, seed=i)
            G.flakes(Lf, k, 0.0, 1.0, 5, size=2.0, fall=6.0, seed=i + 9)
        if kind in ("impact", "decay"):
            k = 0.0 if kind == "impact" else p["k"]
            for pts_, wd, delay in cracks:
                if kind == "impact" and delay > 0.3:
                    continue
                scr = t.pts(pts_)
                Lgr.stroke(scr, wd + 1.0, prof=FK.tp_both(0.5, 0.5), v=0.75 * (1 - 0.4 * k))
                Lcrk.stroke(scr, wd * 0.6 * (1 - 0.3 * k), prof=FK.tp_both(0.6, 0.6), v=0.95 - 0.45 * k,
                            dash=(9.0, 0.75 - 0.3 * k, delay) if k > 0.3 else None)
            if kind == "impact" or k < 0.5:
                r = random.Random(seed * 3 + i)
                ex, ey = t((L * 0.95, 0.0))
                for j in range(int(6 * heavy)):
                    a = r.uniform(-2.6, -0.5)
                    dist = r.uniform(5, 16) * (1 + 1.4 * k)
                    W.ember(Le, ex + math.cos(a) * dist, ey + math.sin(a) * dist + 6 * k * k, math.cos(a), math.sin(a),
                            r.uniform(2.5, 5) * (1 - 0.4 * k), w=0.6, v=0.9 - 0.3 * k)
        out.append(fr.render())
    return out


# =============================================================================
# 일섬 선(Q2) — 출발 피벗에 놓이는 가는 일자 붓획: 돌진 중 그어짐 → 남음 → 분신이 지나며 다시 달아오름 → 터짐 → 재
# =============================================================================
ISSEN_MS = [30, 40, 40, 40, 50, 50, 50, 50, 50, 60, 80, 80]
ISSEN_GLOW = [1, 2, 8]
ISSEN_DASH_MS = 150
ISSEN_SHADOW_AT = 200
ISSEN_BURST_FRAME = 8


def issen_line_frames(d, L, seed=81, shadow=True):
    """L = 이동 거리(도트). 로컬: 원점 = 출발 시점 판정 원점, x = 돌진 방향. 획: x -14 → L + 40(칼끝이 도착 지점 앞까지)."""
    t = TA(d, *CO)
    xa, xb = -14.0, L + 40.0
    n = max(30, int((xb - xa) / 2))
    rng = random.Random(seed)
    pts = []
    for i in range(n + 1):
        u = i / n
        x = xa + (xb - xa) * u
        y = 1.6 * math.sin(u * math.pi * 1.0) - 1.2 * u          # 거의 일자(붓 떨림만 아주 조금)
        pts.append(t((x, y)))
    S = BR.Stroke(pts, 6.0, seed=seed, peak=0.45, dry_from=0.8, split=1.6, drops=6, start_w=0.15, end_w=0.5, lanes=5)
    for ln in S.lanes:
        ln["streak"] = 0.9 + 0.1 * ln["h"]                       # 일섬 선은 결을 약하게(고른 한 줄)
    Ltot = xb - xa

    def s_of(x):
        return max(0.0, min(1.0, (x - xa) / Ltot))
    # 터짐: 선을 따라 비스듬히 갈라지는 짧은 붓획(교차 베기 자국) — 선 위 위치·각도·길이
    cuts = []
    m = max(2, int(round(L / 52)) + 1)
    for j in range(m):
        u = (j + 0.5) / m
        x = xa + 20 + (L + 20) * u + rng.uniform(-6, 6)
        ang = math.radians((1 if j % 2 else -1) * rng.uniform(52, 68))
        ln = rng.uniform(26, 38)
        c0 = (x - math.cos(ang) * ln * 0.5, -math.sin(ang) * ln * 0.5)
        c1 = (x + math.cos(ang) * ln * 0.5, math.sin(ang) * ln * 0.5)
        cuts.append(BR.Stroke([t(c0), t(((c0[0] + c1[0]) / 2 + 2, (c0[1] + c1[1]) / 2)), t(c1)], 4.2, seed=seed + 10 + j,
                              peak=0.4, dry_from=0.6, split=1.4, drops=3, start_w=0.15, end_w=0.45, lanes=4))
    dash_t = [30, 70, 110, 150]                                   # 돌진 시작 기준 각 그림 프레임 끝 시각
    out = []
    for i, ms in enumerate(ISSEN_MS):
        fr = frame(t)
        Lf = fr.L(BR.FLAKE)
        Lb = fr.L(BR.INK_K)
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        if i <= 3:                                                # 돌진 중: 칼(주인공) 바로 뒤로 그어짐
            prog = dash_t[i] / ISSEN_DASH_MS
            head = 1.0 if i == 3 else s_of(prog * L + 26)
            S.draw(Lb, head=head, vmax=(0.62 if i == 0 else 0.9 if i < 3 else 0.8), hot=(i in (1, 2)), Lhot=Lh,
                   drops=(i == 3))
        elif i == 4:                                              # 남은 가는 선(식음)
            S.draw(Lb, head=1.0, vmax=0.66, wk=0.75, fall=2)
        elif i <= 7 and not shadow:                               # 분신 없음(검기 3단 아님): 남은 선이 조금씩 식으며 떨림
            S.draw(Lb, head=1.0, vmax=0.64 - 0.04 * (i - 4) + (0.04 if i == 6 else 0), wk=0.72, fall=2 + i - 4)
        elif i <= 7:                                              # 분신이 지나며 다시 달아오름(앞부분만, A25 이하)
            q = (i - 4) / 3.0
            S.draw(Lb, head=1.0, vmax=0.6, wk=0.7, fall=3)
            hs = s_of(q * L + 10)
            S.draw(Lb, head=hs, vmax=0.84, wk=0.95, drops=False)
        elif i == ISSEN_BURST_FRAME:                              # 터짐(판정 순간 — 백열은 교차 획 머리 몇 도트만)
            S.draw(Lb, head=1.0, vmax=0.9, wk=1.25, drops=True, fall=4)
            for c in cuts:
                c.draw(Lb, head=1.0, vmax=0.9, hot=True, Lhot=Lh)
            _burst_dust(Lf, Le, t, L, xa, rng_seed=seed, age=0)
        else:                                                     # 재로 부서짐
            k = (i - ISSEN_BURST_FRAME) / (len(ISSEN_MS) - 1 - ISSEN_BURST_FRAME)
            S.draw(Lb, head=1.0, tail=0.1 + 0.7 * k, vmax=0.78 - 0.2 * k, wk=1.1 - 0.4 * k, k=min(1.0, 0.35 + k * 0.65), fall=4 + 8 * k)
            for c in cuts:
                c.draw(Lb, head=1.0, tail=0.1 + 0.5 * k, vmax=0.78 - 0.25 * k, wk=1 - 0.3 * k, k=min(1.0, 0.3 + 0.7 * k), fall=3 + 6 * k)
            S.flakes(Lf, k, 0.05, 1.0, int(6 + L / 32), size=1.6, fall=12.0, seed=i)
            _burst_dust(Lf, Le, t, L, xa, rng_seed=seed, age=0.3 + 0.7 * k)
        out.append(fr.render())
    return out


def _burst_dust(Lf, Le, t, L, xa, rng_seed, age):
    """터짐: 선을 따라 재 조각이 위·옆으로 튀어 오르고(나중엔 떨어짐) 불티 바늘이 흩어짐(먼지 구름 없음)."""
    r = random.Random(rng_seed + 3)
    for j in range(int(10 + L / 14)):
        x = xa + 16 + (L + 40) * r.random()
        lat = r.uniform(-3, 3)
        vx, vy = r.uniform(-0.5, 0.5), r.uniform(-1.0, -0.35)
        sp = r.uniform(6, 16)
        dx = vx * sp * (0.4 + age) * 1.6
        dy = vy * sp * (0.4 + age) + 22 * age * age
        px, py = t((x, lat))
        if age > 0.85 and r.random() < 0.5:
            continue
        W.flake(Lf, px + dx, py + dy, r.uniform(1.0, 2.2) * (1 - 0.35 * age), r.uniform(0, 6), v=r.uniform(0.55, 1.0) * (1 - 0.3 * age))
    for j in range(int(5 + L / 32)):
        x = xa + 10 + (L + 40) * r.random()
        px, py = t((x, 0))
        a = r.uniform(-2.8, -0.35)
        dist = r.uniform(4, 12) * (1 + 1.5 * age)
        if age < 0.7:
            W.ember(Le, px + math.cos(a) * dist, py + math.sin(a) * dist + 8 * age * age, math.cos(a), math.sin(a),
                    r.uniform(2, 4) * (1 - 0.5 * age), w=0.6, v=0.9 - 0.4 * age)


# =============================================================================
# 자르기 · 쓰기
# =============================================================================
def write(name, frames, dirs, ms, base, upd, glow, out_dir):
    frames = W.limit_colors(frames, W.COLOR_MAX, name)
    if glow is not None:
        frames = X.clamp_cool(frames, set(glow))
    fw, fh = frames[dirs[0]][0].size
    F = len(ms)
    sheet = Image.new("RGBA", (fw * F, fh * len(dirs)), (0, 0, 0, 0))
    for r, d in enumerate(dirs):
        assert len(frames[d]) == F, (name, d, len(frames[d]), F)
        for c, im in enumerate(frames[d]):
            sheet.alpha_composite(im, (c * fw, r * fh))
    cols = W.colors_of(sheet)
    assert not (cols - W.ALLOWED), (name, sorted(cols - W.ALLOWED))
    assert len(cols) <= W.COLOR_MAX, (name, len(cols))
    assert not W.has_partial(sheet), name
    assert sum(W.edge_touch(im) for d in dirs for im in frames[d]) == 0, (name, "edge")
    hotset = {W.X0, W.X1, W.A26}
    if glow is not None:
        for d in dirs:
            for i, im in enumerate(frames[d]):
                if i not in glow:
                    assert not (W.colors_of(im) & hotset), (name, d, i)
    j = dict(base or {})
    for k in ("legacy", "note", "colors"):
        j.pop(k, None)
    j.update(image=name + ".png", action=name, version=VERSION, frameWidth=fw, frameHeight=fh, frames=F, directions=dirs,
             layout="rows = directions, columns = frames", frameIndex="row * frames + column",
             fps=round(1000 * F / sum(ms), 2), frameDurationsMs=list(ms), loop=False, pixelScale=0.5,
             paletteSwap="none", paletteSwapNote="53라운드 Q62 — fx 는 지역 바닥 팔레트 교체 제외",
             palette=W.PALETTE_NOTE, colors=len(cols), semiTransparent=False, source=SRC)
    j.update(upd)
    if glow is not None:
        j["glowFrames"] = sorted(glow)
        j["glowRule"] = ("53라운드 Q65 · 56라운드 Q11: 백열 X0/X1·A26 은 glowFrames(판정 순간)의 획 머리 몇 도트만. 획 몸은 A25 이하, "
                         "그 밖 프레임은 A25(#eecc78) 이하 — 빌드 검사 통과")
    os.makedirs(out_dir, exist_ok=True)
    sheet.save(os.path.join(out_dir, name + ".png"), optimize=True)
    with open(os.path.join(out_dir, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
    return sheet, j, frames
