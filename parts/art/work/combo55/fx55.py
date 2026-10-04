"""55라운드 새 연격 이펙트 v3 (계약 §13·§16·§17) — 원 전체가 아니라 판정 호를 따라 2~3프레임에 그려 나가는 부분 초승달.

원칙(55라운드 Q18~Q25 · 53라운드 Q61~Q68):
  · 머리(칼끝 자리)가 판정 호를 따라 달려 나가며 그 뒤로 혜성처럼 굵어지는 초승달을 남긴다 → 머리가 호 끝에 닿으면
    꼬리부터 80~120ms 안에 사라짐(재 조각·불티로 부서짐). 대각 베기는 진행에 따라 높이(화면 위)가 바뀌어 기울어진 호로 읽힌다.
  · 내려찍기(V)는 세로로 선 가는 호(머리 위 → 앞 지면) + 쐐기를 따라 갈라지는 바닥 금 + 끝점 충격(별도 시트, scale 허용).
  · 색: 주인공 재·호박 + 백열 X0/X1(판정 프레임만, Q65). 판정 밖 프레임은 A25(#eecc78) 이하(빌드 후처리 + 검사). 반투명 0,
    시트당 14색 이하, paletteSwap none.
좌표: 로컬 '오른쪽 보기'(x = 조준 방향, y = 화면 아래, 원점 = 판정 원점 = 피벗 위 40 도트) → 방향 변환.
  §17 각도(조준 0°, 화면 시계 +)를 그대로 쓰도록 모든 방향은 **회전**(left = 180° 회전 — 구 fx 의 좌우 반전과 다름).
높이 z(도트)는 방향과 무관하게 화면 위(-y)로 더한다.
"""
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "fx_weapons_v3")))
import wkit as W  # noqa: E402
from wkit import FK  # noqa: E402

DIRS = W.DIRS
HIT_UP = W.HIT_UP                                    # 40
ROT = {"right": (1, 0, 0, 1), "down": (0, -1, 1, 0), "up": (0, 1, -1, 0), "left": (-1, 0, 0, -1), "any": (1, 0, 0, 1)}
CANVAS = 1100
CO = (550, 560)                                       # 큰 캔버스의 판정 원점


class T(W.T):
    """wkit.T 와 같되 left = 180° 회전(§17 화면 시계 + 를 모든 방향에 그대로)."""

    def __init__(self, d, ox, oy):
        super().__init__("right", ox, oy)
        self.d = d
        self.m = ROT[d]


def zpt(t, p, z):
    x, y = t(p)
    return x, y - z


# =============================================================================
# 부분 초승달 (칼·대검 수평/대각)
# =============================================================================
STYLE = {
    "katana": dict(body=[W.A18, W.A19, W.A21, W.A23, W.A25, W.A26], veil=W.R_ASHG, fill=W.R_EDGE_SOFT, flake=W.R_ASHG,
                   edge_w=1.6, embers=9, flakes=10),
    "echo": dict(body=[W.S1, W.S2, W.S3, W.A21, W.A23], veil=W.R_ASHG, fill=[W.S0, W.S1, W.S2], flake=W.R_ASHG,
                 edge_w=1.3, embers=5, flakes=12),
    "gs": dict(body=W.R_RUST, veil=W.R_ASHB, fill=[W.B1, W.B2, W.B3, W.A18], flake=W.R_ASHB, edge_w=2.2, embers=12, flakes=9),
}


def comet(u, head_open):
    """폭 윤곽: 꼬리(u=0) 가늘게 → 머리 쪽 굵게 → 머리 끝 뾰족(그려 나가는 중) / 끝까지 그린 뒤엔 호 끝으로 가늘어짐."""
    a = u ** 0.85
    tip = 0.14 if head_open else 0.22
    b = min(1.0, (1 - u) / tip) ** 0.55
    return a * b


def band(L, t, R, a0, a1, s_tail, s_head, w, zfn, val, head_open=True, fill_to=None, fill=None, seed=1, dash=None):
    """호 a0→a1(rad) 의 s ∈ [s_tail, s_head] 구간에 초승달 띠를 점찍기(빈틈 없는 0.45 도트 간격).
    val(s, u, q, qn) → [(레이어, 값)] — q = 바깥 가장자리(R)에서 안쪽으로 깊이(도트), qn = q / 그 자리 폭. fill = 칼끝 쪽 결 레이어."""
    if s_head - s_tail <= 1e-4:
        return
    span = a1 - a0
    arclen = abs(span) * R
    ns = max(8, int(arclen * (s_head - s_tail) / 0.45))
    for i in range(ns + 1):
        s = s_tail + (s_head - s_tail) * i / ns
        u = (s - s_tail) / (s_head - s_tail)
        wk = w * comet(u, head_open)
        a = a0 + span * s
        ca, sa = math.cos(a), math.sin(a)
        z = zfn(s)
        if dash and FK.frac(s * arclen / dash[0] + dash[2]) > dash[1]:
            continue
        if wk > 0.25:
            nq = max(1, int(wk / 0.45))
            for j in range(nq + 1):
                q = wk * j / nq
                r = R - q
                x, y = zpt(t, (ca * r, sa * r), z)
                for lay, v in val(s, u, q, q / wk):
                    if v > 0:
                        lay.put(x, y, v)
        if fill_to and fill is not None and u > 0.05:
            # 칼끝 쪽 속도선: 띠 안쪽에 1px 호 몇 줄 — 깊을수록 짧고(머리 쪽에만) 어둡다
            r0 = R - w - 3.0                            # 띠 최대 폭 안쪽에서 시작하는 고정 반지름 줄(물결 없음)
            depth = r0 - fill_to
            for li, f in enumerate(FILL_LANES):
                q = depth * f
                if q > depth:
                    break
                start = 0.15 + 0.55 * f + 0.15 * W.h2(li, 1, seed)
                if u < start:
                    continue
                r = r0 - q
                x, y = zpt(t, (ca * r, sa * r), z)
                fill[0].put(x, y, fill[1] * (0.45 + 0.55 * (u - start) / max(1e-6, 1 - start)) * (1 - 0.45 * f))


FILL_LANES = (0.08, 0.3, 0.55, 0.85)


def crescent_frames(style, d, R, a0d, a1d, plan, wmax, zfn, fill_to=None, seed=1, embers_at=None):
    """plan = [(kind, dict)] kind: pre(head) · draw(tail, head, hot) · decay(tail, k) · ghost(v)."""
    st = STYLE[style]
    t = T(d, *CO)
    a0, a1 = math.radians(a0d), math.radians(a1d)
    sgn = 1 if a1 > a0 else -1
    deb = W.Debris(seed * 131 + 7)
    rng = deb.rng
    F = len(plan)
    first_decay = next((i for i, (k, _) in enumerate(plan) if k == "decay"), F)
    # 재 조각: 꼬리가 물러난 자리에서 떨어져 나감 · 불티: 호 끝에서 접선 방향으로
    prev = 0.0
    for i, (kind, p) in enumerate(plan):
        if kind != "decay":
            continue
        for j in range(st["flakes"]):
            s = rng.uniform(prev, p["tail"] + 0.05)
            a = a0 + (a1 - a0) * s
            rr = R - wmax * rng.uniform(0.2, 1.3)
            tang = (-math.sin(a) * sgn, math.cos(a) * sgn)
            sp = rng.uniform(1.0, 3.0)
            ov = rng.uniform(-0.6, 1.4)
            z = zfn(s)
            deb.spawn("flake", (math.cos(a) * rr, math.sin(a) * rr - 0.0),
                      (tang[0] * sp * 0.5 + math.cos(a) * ov, tang[1] * sp * 0.5 + math.sin(a) * ov),
                      i, F - i, size=rng.uniform(1.2, 3.0) * (1.4 if style == "gs" else 1.0), v=rng.uniform(0.45, 0.95), g=1.6)
            deb.items[-1]["z"] = z
        prev = p["tail"]
    for j in range(st["embers"]):
        s = rng.uniform(0.6, 1.0)
        a = a0 + (a1 - a0) * s
        rr = R - rng.uniform(0, wmax * 0.5)
        tang = (-math.sin(a) * sgn, math.cos(a) * sgn)
        sp = rng.uniform(5.0, 10.0) * (R / 130.0) ** 0.5
        spread = rng.uniform(-0.3, 0.6)
        deb.spawn("ember", (math.cos(a) * rr, math.sin(a) * rr), (tang[0] * sp + math.cos(a) * sp * spread, tang[1] * sp + math.sin(a) * sp * spread),
                  (embers_at if embers_at is not None else first_decay - 1) + (j % 2), rng.choice((2, 2, 3)),
                  size=rng.uniform(3.0, 6.5), v=rng.uniform(0.55, 0.95), g=1.1)
        deb.items[-1]["z"] = zfn(s)
    out = []
    for i, (kind, p) in enumerate(plan):
        fr = W.Frame(CANVAS, CANVAS, t)
        Lfill = fr.L(st["fill"])
        Lveil = fr.L(st["veil"])
        Lbody = fr.L(st["body"])
        Ledge = fr.L(W.R_EDGE)
        Lflake = fr.L(st["flake"])
        Lember = fr.L(W.R_EMBER)
        if kind == "pre":                             # 예비: 시작 쪽 가는 1px 선(판정 40ms 전 — A23 이하)
            band(Ledge, t, R - 2, a0, a1, 0.0, p["head"], 1.2, zfn, lambda s, u, q, qn: [(Ledge, 0.42 + 0.12 * u)], head_open=True)
        elif kind == "ghost":                          # 잔상 베기 전조: 호 전체에 끊긴 재 실선
            band(Lveil, t, R - 3, a0, a1, 0.0, 1.0, 1.1, zfn, lambda s, u, q, qn: [(Lveil, p["v"])], head_open=False,
                 dash=(11.0, 0.55, 0.3))
        else:
            hot = p.get("hot", False)
            k = p.get("k", 0.0)
            w = wmax * (1.0 if hot or kind == "draw" else max(0.35, 1 - 0.55 * k))
            heat = 1.0 if hot else max(0.3, 0.78 - 0.45 * k)
            head = p.get("head", 1.0)
            ew = st["edge_w"]

            def val(s, u, q, qn, hot=hot, heat=heat, head=head, k=k):
                res = []
                if q < ew:
                    if hot:
                        v = 0.62 + 0.36 * u ** 1.5         # 머리 쪽 날선 백열(X1/X0), 꼬리 쪽 호박
                    else:
                        v = min(0.62, heat * (0.55 + 0.35 * u))
                    res.append((Ledge, v))
                elif qn < 0.62:
                    v = heat * (1 - 0.8 * qn ** 0.8) * (0.55 + 0.45 * u)
                    if not hot:
                        v = min(v, 0.7)
                    if style == "gs" and abs(qn - 0.34) * wmax < (1.2 if hot else 0.8) and FK.frac(s * 7 + 0.3) < 0.88:
                        res.append((Ledge, (0.7 if hot else min(0.6, heat * 0.75)) * (0.6 + 0.4 * u)))   # 이 빠진 홈 혼불 한 줄
                    else:
                        res.append((Lbody, v))
                else:
                    n = W.h2(int(s * 900 / 6.0), int(q / 2.0), 3)
                    keep = 0.15 + 0.55 * k + 0.4 * (qn - 0.62) / 0.38
                    if n > keep:
                        res.append((Lveil, 0.35 + 0.55 * (1 - qn) * (0.5 + 0.5 * u)))
                return res
            dash = (8.0, 0.6, 0.15) if kind == "decay" and k >= 0.99 else None
            band(Lbody, t, R, a0, a1, p.get("tail", 0.0), head, w, zfn, val, head_open=(kind == "draw" and head < 0.999),
                 fill_to=fill_to if kind == "draw" or k < 0.5 else None, fill=(Lfill, 0.9 if hot else 0.7), seed=seed, dash=dash)
            if hot and head < 0.999:                    # 그려 나가는 머리: 칼끝 반짝
                a = a0 + (a1 - a0) * head
                x, y = zpt(t, (math.cos(a) * (R - 2), math.sin(a) * (R - 2)), zfn(head))
                Ledge.star4(x, y, 7 if style != "gs" else 10, w=0.9, v=0.95)
        # 파편(높이 z 반영)
        for it in deb.items:
            it.setdefault("z", 0.0)
        _debris(deb, fr, t, {"ember": Lember, "flake": Lflake}, i)
        out.append(fr.render())
    return out


def _debris(deb, f, t, layers, i):
    saved = []
    for it in deb.items:
        saved.append(it["p"])
    # Debris.draw 는 높이를 모름 → 화면 y 를 z 만큼 올린 임시 변환
    for it in deb.items:
        z = it.get("z", 0.0)
        it["_t"] = z
    class TZ:
        def __init__(self, base, z):
            self.base, self.z = base, z

        def __call__(self, p):
            x, y = self.base(p)
            return x, y - self.z
    for it in deb.items:
        sub = W.Debris(0)
        sub.items = [it]
        sub.draw(f, TZ(t, it["_t"]), layers, i)


# =============================================================================
# 세로 내려찍기 호 (V · 차지) — 머리 위 → 앞 지면
# =============================================================================
def vertical_frames(d, L, plan, wmax=16, lat=42.0, heavy=1.0, seed=3, crack=True, Rv=150.0):
    """L = 쐐기 길이(도트, 판정 원점 → 끝점). 호: φ 105°(머리 위 뒤) → 0°(앞 끝점). 높이 z(φ) = H sin φ.
    끝점·바닥 금은 판정 평면(판정 원점 높이)에 그린다 → 끝점 충격 시트(anchor hitbox_center)와 정확히 맞물림.
    plan: pre(head) · draw(head) · impact · decay(k)."""
    t = T(d, *CO)

    def P(phi):
        f = Rv * math.cos(phi)
        z = Rv * 1.05 * math.sin(phi)
        r = -lat * math.sin(phi) ** 0.7                  # 해부 오른손 쪽에서 내려옴(정면·뒷면에서도 곡선이 보이게)
        x, y = t((f, r))
        return x, y - z

    p0, p1 = math.radians(105), 0.0
    # 바깥 방향(띠 두께는 안쪽으로): 호의 중심(앞 0.25L, 높이 0) 반대쪽
    cx, cy = P(math.radians(40))
    ccx, ccy = t((Rv * 0.2, lat * 0.6))
    rng = W.Debris(seed).rng
    cracks = []
    if crack:
        # 쐐기 가운데 금 + 양옆 잔금(쐐기 40° 안), 로컬 지면 좌표
        main = W.jag(rng, (Rv * 0.75, 0.0), (L * 0.97, 0.0), n=9, amp=3.0 + L * 0.008)
        cracks.append((main, 1.9 * heavy, 0.0))
        for sgn in (-1, 1):
            for j in range(2):
                f0 = L * rng.uniform(0.45, 0.8)
                ang = sgn * math.radians(rng.uniform(8, 17))
                ln = L * rng.uniform(0.12, 0.22)
                q0 = (f0, 0.0)
                q1 = (f0 + math.cos(ang) * ln, math.sin(ang) * ln)
                cracks.append((W.jag(rng, q0, q1, n=4, amp=1.6), 0.9 * heavy, 0.25 + 0.2 * j))
    deb = W.Debris(seed * 17 + 1)
    for j in range(int(10 * heavy)):
        f = L * rng.uniform(0.7, 1.0)
        ang = rng.uniform(-2.6, -0.5)
        sp = rng.uniform(4, 9)
        deb.spawn("ember", (f, rng.uniform(-8, 8)), (math.cos(ang) * sp * 0.4, math.sin(ang) * sp), 2 + (j % 2), 2,
                  size=rng.uniform(3, 6), v=rng.uniform(0.6, 0.95), g=1.6)
    out = []
    for i, (kind, p) in enumerate(plan):
        fr = W.Frame(CANVAS, CANVAS, t)
        Lcrk = fr.L(W.R_EDGE)
        Lgr = fr.L([W.B0, W.B1, W.B2])
        Lbody = fr.L([W.A18, W.A19, W.A21, W.A23, W.A25, W.A26])
        Lveil = fr.L(W.R_ASHG)
        Ledge = fr.L(W.R_EDGE)
        Lember = fr.L(W.R_EMBER)
        Lflake = fr.L(W.R_ASHG)
        hot = kind == "impact"
        if kind == "pre":
            head, tail, w, heat = p["head"], 0.0, 1.2, 0.45
        elif kind == "draw":
            head, tail, w, heat = p["head"], 0.0, wmax * 0.8, 0.62
        elif kind == "impact":
            head, tail, w, heat = 1.0, 0.18, wmax, 1.0
        else:
            k = p["k"]
            head, tail, w, heat = 1.0, 0.35 + 0.6 * k, wmax * (1 - 0.5 * k), max(0.3, 0.7 - 0.4 * k)
        ns = 900
        prev = P(p0)
        for j in range(1, ns + 1):
            s = j / ns
            if s < tail or s > head:
                prev = P(p0 + (p1 - p0) * s)
                continue
            cur = P(p0 + (p1 - p0) * s)
            tx, ty = cur[0] - prev[0], cur[1] - prev[1]
            ln = math.hypot(tx, ty) or 1.0
            nx, ny = -ty / ln, tx / ln
            if (cur[0] - ccx) * nx + (cur[1] - ccy) * ny < 0:
                nx, ny = -nx, -ny
            u = (s - tail) / max(1e-6, head - tail)
            open_ = kind in ("pre", "draw")
            wk = w * comet(u, open_)
            if kind == "decay" and p["k"] >= 0.99 and FK.frac(s * 40) > 0.6:
                prev = cur
                continue
            nq = max(1, int(wk / 0.45))
            for q_i in range(nq + 1):
                q = wk * q_i / nq
                x, y = cur[0] - nx * q, cur[1] - ny * q
                if kind == "pre":
                    Ledge.put(x, y, 0.45 + 0.1 * u)
                elif q < 1.5:
                    Ledge.put(x, y, (0.62 + 0.36 * u ** 1.4) if hot else min(0.62, heat * (0.6 + 0.4 * u)))
                elif q / max(wk, 1e-6) < 0.6:
                    Lbody.put(x, y, heat * (1 - 0.7 * q / wk) * (0.6 + 0.4 * u) if hot else min(0.7, heat * (1 - 0.7 * q / wk)))
                elif W.h2(int(s * 300), int(q), 5) > 0.3 + 0.4 * (p.get("k", 0)):
                    Lveil.put(x, y, 0.4 + 0.4 * (1 - q / wk))
            prev = cur
        if kind in ("draw", "pre"):                      # 내려오는 머리 반짝(판정 전 — A25 이하)
            hx, hy = P(p0 + (p1 - p0) * head)
            Ledge.star4(hx, hy, 6 if kind == "draw" else 3, w=0.8, v=0.6)
        if kind == "impact":                           # 칼이 땅에 닿은 자리 → 쐐기 끝점까지 달려 나가는 충격 선(판정 순간 백열)
            a_ = t((Rv * 0.85, 0.0))
            b_ = t((L, 0.0))
            Ledge.stroke([a_, b_], 2.4 * heavy, prof=FK.tp_both(0.7, 0.75), v=0.98)
            Lbody.stroke([a_, b_], 4.5 * heavy, prof=FK.tp_both(0.6, 0.7), v=0.8)
        elif kind == "decay" and p["k"] < 0.5:
            a_ = t((Rv * 0.85 + (L - Rv * 0.85) * 0.5 * p["k"] * 2, 0.0))
            b_ = t((L, 0.0))
            Lbody.stroke([a_, b_], 2.5 * heavy, prof=FK.tp_both(0.6, 0.8), v=0.62)
        # 바닥 금(쐐기를 따라) — 충돌 순간 갈라지고 식으며 끊김
        if kind in ("impact", "decay") and crack:
            k = 0.0 if kind == "impact" else p["k"]
            for pts, wd, delay in cracks:
                if kind == "impact" and delay > 0.3:
                    continue
                scr = [(x, y) for x, y in t.pts(pts)]
                Lgr.stroke(scr, wd + 1.2, prof=FK.tp_both(0.5, 0.5), v=0.75 * (1 - 0.4 * k))
                v = 0.97 if kind == "impact" else min(0.62, 0.62 - 0.3 * k)
                Lcrk.stroke(scr, wd * (1 - 0.35 * k), prof=FK.tp_both(0.6, 0.6), v=v,
                            dash=(9.0, 0.75 - 0.3 * k, delay) if k > 0.3 else None)
        _debris(deb, fr, t, {"ember": Lember, "flake": Lflake}, i)
        out.append(fr.render())
    return out


# =============================================================================
# 끝점 충격(충격원 0.35R) · 충격파 링 · 차지 번쩍임
# =============================================================================
KY = 0.85                                             # 바닥 고리 세로 비율(판정 원은 원 — 그림만 살짝 눌러 바닥에 놓임)


def impact_frames(radius, seed=5, heavy=1.0):
    """anchor hitbox_center(충격원 중심) · directions any. f0 충돌 섬광 → 깨진 고리 퍼짐 → 먼지 링 → 가라앉음."""
    t = T("right", *CO)
    rng = W.Debris(seed).rng
    # 균열: 고르게 퍼진 바퀴살이 아니라 앞(+x)쪽으로 쏠린 굵은 금 3 + 짧은 금 4, 시작 반지름·길이·꺾임이 제각각, 일부 잔가지
    cr = []
    for k in range(7):
        main = k < 3
        a = (rng.uniform(-0.7, 0.7) if main else rng.uniform(0.9, 2 * math.pi - 0.9))
        cr.append((a, rng.uniform(0.95, 1.4) if main else rng.uniform(0.45, 0.8), rng.uniform(0.0, 0.6), main))
    deb = W.Debris(seed + 1)
    for j in range(int(14 * heavy)):
        a = rng.uniform(0, 2 * math.pi)
        r = radius * rng.uniform(0.6, 1.0)
        deb.spawn("dust", (math.cos(a) * r, math.sin(a) * r * KY), (math.cos(a) * 2.2, math.sin(a) * 1.0 - 0.3), 1 + j % 2, 3,
                  size=rng.uniform(5, 8) * (radius / 71) ** 0.5, v=rng.uniform(0.45, 0.75), g=-0.15)
    for j in range(int(12 * heavy)):
        a = rng.uniform(-math.pi, 0)
        sp = rng.uniform(5, 11)
        deb.spawn("ember", (rng.uniform(-8, 8), rng.uniform(-4, 4)), (math.cos(a) * sp, math.sin(a) * sp * 0.9 - 2), 0 + j % 2, 2,
                  size=rng.uniform(3, 6), v=rng.uniform(0.6, 1.0), g=1.8)
    for j in range(int(10 * heavy)):
        a = rng.uniform(-math.pi, 0)
        sp = rng.uniform(2, 5)
        deb.spawn("flake", (rng.uniform(-radius * 0.5, radius * 0.5), rng.uniform(-6, 6)), (math.cos(a) * sp, math.sin(a) * sp - 2),
                  1, 3, size=rng.uniform(1.4, 3.0), v=rng.uniform(0.5, 0.9), g=1.5)
    out = []
    ring_r = [0.82, 1.0, 1.08, 1.12, 1.14]
    for i in range(5):
        fr = W.Frame(CANVAS, CANVAS, t)
        Ldust = fr.L(W.R_DUST)
        Lgr = fr.L([W.B0, W.B1, W.B2])
        Lcrk = fr.L(W.R_EDGE)
        Lhot = fr.L(W.R_HOT)
        Lember = fr.L(W.R_EMBER)
        Lflake = fr.L(W.R_ASHB)
        c = CO
        k = i / 4
        # 방사 균열(시작 반지름 제각각, 잔가지 없이 짧게) — 바닥(눌린 타원)
        for a, ln, d0, main in cr:
            r0 = radius * (0.1 + 0.35 * d0)
            r1 = radius * ln * min(1.0, 0.6 + 0.4 * i)
            g = W.Debris(int(a * 1000) + 7).rng
            p0 = (c[0] + math.cos(a) * r0, c[1] + math.sin(a) * r0 * KY)
            p1 = (c[0] + math.cos(a + g.uniform(-0.25, 0.25)) * r1, c[1] + math.sin(a + g.uniform(-0.25, 0.25)) * r1 * KY)
            pts = W.jag(g, p0, p1, n=6, amp=2.6 + 1.5 * main)
            wd = (1.6 if main else 1.0) * heavy
            Lgr.stroke(pts, wd + 1.2, prof=FK.tp_tail(0.6), v=0.8)
            v = 0.97 if i == 0 else min(0.62, 0.62 - 0.1 * i)
            Lcrk.stroke(pts, wd * (1 - 0.12 * i), prof=FK.tp_tail(0.6), v=v, dash=(8.0, 0.8 - 0.12 * i, d0) if i >= 3 else None)
            if main and i >= 1:                         # 잔가지
                q = pts[3]
                ab = a + (0.6 if d0 > 0.3 else -0.6)
                q1 = (q[0] + math.cos(ab) * radius * 0.3, q[1] + math.sin(ab) * radius * 0.3 * KY)
                Lcrk.stroke(W.jag(g, q, q1, 3, 1.2), 0.8, prof=FK.tp_tail(0.7), v=min(0.62, v * 0.9))
        rr = radius * ring_r[i]
        if i == 0:
            Lhot.disc(c[0], c[1], radius * 0.28, radius * 0.28 * KY, v=1.0, edge=0.5)
            Lhot.arc(c[0], c[1], rr, rr * KY, 0, 2 * math.pi, 2.2, v=0.92, dash=(9, 0.8, 0.1))
        elif i <= 2:
            Lcrk.arc(c[0], c[1], rr, rr * KY, 0, 2 * math.pi, 1.6 - 0.4 * i, v=0.6 - 0.1 * i, dash=(11, 0.7 - 0.12 * i, 0.2 * i))
        saved = W.puff                                 # 먼지는 납작하게(바닥에 깔린 먼지 링 — 떠 있는 구름처럼 보이지 않게)
        W.puff = lambda L, x, y, r, v=1.0, flat=0.75, seed=0: L.cloud(x, y, r, v=v, flat=0.45, seed=seed)
        try:
            _debris(deb, fr, t, {"ember": Lember, "flake": Lflake, "dust": Ldust}, i)
        finally:
            W.puff = saved
        out.append(fr.render())
    return out


def ring_frames(radii, seed=9):
    """3단 차지 충격파 링(anchor hitbox_center, directions any). radii = 프레임별 판정 링 반지름(도트)."""
    t = T("right", *CO)
    rng = W.Debris(seed).rng
    out = []
    F = len(radii)
    for i, r in enumerate(radii):
        fr = W.Frame(CANVAS, CANVAS, t)
        Ldust = fr.L(W.R_DUST)
        Lring = fr.L(W.R_EDGE)
        Lin = fr.L([W.A18, W.A19, W.A21])
        c = CO
        k = i / (F - 1)
        hot = i <= 1
        w = 3.2 * (1 - 0.6 * k)
        Lring.arc(c[0], c[1], r, r * KY, 0, 2 * math.pi, w, v=(0.97 if hot else 0.6 - 0.25 * k),
                  dash=None if i < 3 else (14, 0.8 - 0.15 * (i - 3), 0.07 * i))
        Lin.arc(c[0], c[1], r - 6, (r - 6) * KY, 0, 2 * math.pi, 1.2, v=0.8 - 0.4 * k, dash=(20, 0.5, 0.3 + 0.1 * i))
        if i >= 1:
            for j in range(16):
                a = j * 2 * math.pi / 16 + W.h2(j, i, seed) * 0.3
                rr = r - 4 + W.h2(j, 3, seed) * 6
                if W.h2(j, i, seed + 1) < 0.6:
                    Ldust.cloud(c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr * KY, 5 + 4 * k, v=0.85 - 0.3 * k, flat=0.7, seed=j + i)
        out.append(fr.render())
    return out


def flash_frames(d, blade, level, seed=11):
    """차지 단계 도달 번쩍임(anchor player_pivot · 4방향). blade = (손잡이, 칼끝) 큰 캔버스 화면 좌표(이 방향 홀드 자세).
    lv1 작은 반짝(A23) · lv2 중간 + 날 따라 흐르는 호박(A25) — 판정 아님 → 백열 없음(Q65).
    lv3 = flash_frames_lv3(55라운드 Q27: 최대 차지 신호로 f0·f1 만 백열 허용)."""
    if level == 3:
        return flash_frames_lv3(d, blade, seed)
    t = T(d, *CO)
    (gx, gy), (tx, ty) = blade
    size = {1: 9, 2: 16, 3: 26}[level]
    vmax = {1: 0.5, 2: 0.62, 3: 0.62}[level]
    rng = W.Debris(seed + level).rng
    ms_n = 5
    out = []
    for i in range(ms_n):
        fr = W.Frame(CANVAS, CANVAS, t)
        Lb = fr.L([W.A19, W.A21, W.A23, W.A25])
        Ls = fr.L(W.R_EDGE)
        Le = fr.L(W.R_EMBER)
        k = [0.55, 1.0, 0.7, 0.4, 0.2][i]
        # 날을 따라 손잡이 → 칼끝으로 흐르는 빛(진행 i)
        prog = min(1.0, (i + 1) / 2.0)
        mx, my = gx + (tx - gx) * prog, gy + (ty - gy) * prog
        if level >= 2 and i <= 3:
            Lb.stroke([(gx, gy), (mx, my)], 1.4 + 0.6 * (level - 2), prof=FK.tp_head(0.6), v=0.95 * k)
        sz = size * (0.6 + 0.4 * k) if i < 4 else size * 0.35
        Ls.star4(tx, ty, sz, w=1.0 + 0.3 * (level - 1), v=vmax * k / 0.62 * 0.62 + 0.02, diag=0.5 if level == 3 else 0.0)
        if level == 3 and i >= 1:
            r = 14 + 9 * i
            Ls.arc(tx, ty, r, r * 0.9, 0, 2 * math.pi, 1.2, v=0.6 - 0.1 * i, dash=(10, 0.7, 0.05 * i))
        if level >= 2 and i in (1, 2):
            for j in range(4 * (level - 1)):
                a = rng.uniform(0, 2 * math.pi)
                ln = rng.uniform(6, 14) * level
                Le.stroke([(tx + math.cos(a) * 4, ty + math.sin(a) * 4), (tx + math.cos(a) * ln, ty + math.sin(a) * ln)], 0.8,
                          prof=FK.tp_tail(0.8), v=0.6)
        out.append(fr.render())
    return out


LV3_GLOW = [0, 1]                                     # 55라운드 Q27 — 3단 번쩍임 f0·f1 만 백열(X0/X1·A26). f2~ 는 A25 이하


def flash_frames_lv3(d, blade, seed=11):
    """차지 3단(최대 차지) 번쩍임 — Q27: Q65 '판정 순간만 백열'의 예외. lv1·lv2(호박까지)와 한눈에 갈리게:
      f0 30ms 점화: 날 전체가 손잡이→칼끝 백열 선으로 켜지고 칼끝에 X0 코어 + 긴 4빛살(끝으로 갈수록 호박)
      f1 40ms 정점: 8빛살 큰 별(코어 X0 → 빛살 끝 호박) + 칼끝을 감싸는 X1 실선 고리 + 불티 방사, 날은 칼끝 쪽 절반만 X1
      f2~f4: 백열 꺼짐 — 호박(A25 이하) 별 수축 · 고리가 끊긴 호박 고리로 퍼짐 · 불티 점이 밖으로 흩어지며 식음."""
    t = T(d, *CO)
    (gx, gy), (tx, ty) = blade
    rng = W.Debris(seed + 3).rng
    embers = [(j * 2 * math.pi / 14 + 0.2 + rng.uniform(-0.18, 0.18), rng.uniform(0.8, 1.2), rng.uniform(0.7, 1.0)) for j in range(14)]   # 고르게 방사
    bl = math.hypot(tx - gx, ty - gy) or 1.0
    ux, uy = (tx - gx) / bl, (ty - gy) / bl
    out = []
    for i in range(5):
        fr = W.Frame(CANVAS, CANVAS, t)
        Laura = fr.L([W.A19, W.A21, W.A23, W.A25])           # 날 둘레 호박 테(백열 선 뒤)
        Lring = fr.L(W.R_EDGE)
        Le = fr.L(W.R_EMBER)
        Ls = fr.L(W.R_EDGE)                                  # 별·날선(위)
        Lc = fr.L(W.R_HOT)                                   # 코어
        if i == 0:
            Laura.stroke([(gx, gy), (tx, ty)], 2.6, prof=FK.tp_head(0.5), v=0.95)
            Ls.stroke([(gx, gy), (tx, ty)], 1.1, prof=FK.tp_head(0.35), v=0.92, vprof=lambda u: 0.82 + 0.18 * u)
            for k in range(4):
                a = math.pi / 4 * 0 + k * math.pi / 2
                Ls.ray(tx, ty, a, 0, 34, 1.6, prof=FK.tp_tail(0.9), v=1.0, vprof=lambda u: 1.0 - 0.5 * u)
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2
                Ls.ray(tx, ty, a, 0, 15, 1.0, prof=FK.tp_tail(1.0), v=0.8, vprof=lambda u: 1.0 - 0.4 * u)
            Lc.disc(tx, ty, 5.5, v=1.0, edge=0.62)
        elif i == 1:
            h0 = 0.45                                        # 날은 칼끝 쪽 절반만 백열
            hx, hy = gx + (tx - gx) * h0, gy + (ty - gy) * h0
            Laura.stroke([(gx, gy), (tx, ty)], 2.2, prof=FK.tp_head(0.8), v=0.9)
            Ls.stroke([(hx, hy), (tx, ty)], 1.0, prof=FK.tp_head(0.6), v=0.86)
            for k in range(4):
                a = k * math.pi / 2
                Ls.ray(tx, ty, a, 0, 46, 2.0, prof=FK.tp_tail(0.85), v=1.0, vprof=lambda u: 1.0 - 0.52 * u)
            for k in range(4):
                a = math.pi / 4 + k * math.pi / 2
                Ls.ray(tx, ty, a, 0, 28, 1.3, prof=FK.tp_tail(0.95), v=0.86, vprof=lambda u: 1.0 - 0.42 * u)
            r = 18
            Lring.arc(tx, ty, r + 2.2, (r + 2.2) * 0.9, 0, 2 * math.pi, 1.6, v=0.6)
            Lring.arc(tx, ty, r, r * 0.9, 0, 2 * math.pi, 1.1, v=0.84)
            for a, sp, vv in embers:
                r0, r1 = 11 * sp, 32 * sp
                Le.stroke([(tx + math.cos(a) * r0, ty + math.sin(a) * r0), (tx + math.cos(a) * r1, ty + math.sin(a) * r1)], 0.9,
                          prof=FK.tp_tail(0.8), v=0.7 * vv + 0.25)
            Lc.disc(tx, ty, 7.0, v=1.0, edge=0.6)
        else:
            k = i - 2                                        # 0,1,2 — 식는 꼬리(A25 이하)
            Laura.stroke([(tx - ux * (36 - 10 * k), ty - uy * (36 - 10 * k)), (tx, ty)], 1.6 - 0.4 * k, prof=FK.tp_head(0.7),
                         v=0.9 - 0.25 * k)
            sz = [26, 13, 7][k]
            Ls.star4(tx, ty, sz, w=1.4 - 0.3 * k, v=[0.62, 0.55, 0.42][k], diag=0.55 if k == 0 else 0.0)
            r = [24, 33, 40][k]
            Lring.arc(tx, ty, r, r * 0.9, 0, 2 * math.pi, 1.3 - 0.3 * k, v=[0.62, 0.5, 0.36][k], dash=(12, 0.72 - 0.12 * k, 0.04 * k))
            for j, (a, sp, vv) in enumerate(embers):
                if k == 2 and j % 2:
                    continue
                rr = (34 + 9 * k) * sp
                ex, ey = tx + math.cos(a) * rr, ty + math.sin(a) * rr + 2.5 * k * k
                Le.stroke([(ex - math.cos(a) * (4 - k), ey - math.sin(a) * (4 - k)), (ex, ey)], 0.8, prof=FK.tp_head(0.8),
                          v=(0.62 - 0.17 * k) * vv + 0.1)
            if k == 0:
                Lc.disc(tx, ty, 3.0, v=0.58, edge=0.7)
        out.append(fr.render())
    return out


# =============================================================================
# 자르기 · 검사 · 쓰기
# =============================================================================
COOL = {W.hexrgb(W.X0): W.hexrgb(W.A25), W.hexrgb(W.X1): W.hexrgb(W.A25), W.hexrgb(W.A26): W.hexrgb(W.A25)}


def clamp_cool(frames, glow):
    for d, lst in frames.items():
        for i, im in enumerate(lst):
            if i in glow:
                continue
            px = im.load()
            bb = im.getbbox()
            if not bb:
                continue
            for y in range(bb[1], bb[3]):
                for x in range(bb[0], bb[2]):
                    c = px[x, y]
                    if c[3] and c[:3] in COOL:
                        px[x, y] = COOL[c[:3]] + (255,)
    return frames


def fit(frames, margin=3, step=8, include_pivot=False):
    """큰 캔버스 → 합집합 상자로 자름. → (잘린 프레임, 피벗(발) 좌표, 판정 원점 좌표).
    include_pivot = 주인공 발 피벗이 틀 안에 들게(작은 player_pivot 시트 — 엔진 원점이 틀 밖으로 나가지 않게)."""
    box = (CO[0], CO[1] + HIT_UP, CO[0] + 1, CO[1] + HIT_UP + 1) if include_pivot else None
    for lst in frames.values():
        for im in lst:
            b = im.getbbox()
            if b:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    x0, y0 = box[0] - margin, box[1] - margin
    Wd = -(-(box[2] + margin - x0) // step) * step
    Hd = -(-(box[3] + margin - y0) // step) * step
    out = {d: [im.crop((x0, y0, x0 + Wd, y0 + Hd)) for im in lst] for d, lst in frames.items()}
    origin = (CO[0] - x0, CO[1] - y0)
    return out, (origin[0], origin[1] + HIT_UP), origin


SRC = "parts/art/work/combo55/build.py (55라운드 Q18~Q25 · 계약 §17 새 연격 이펙트)"


def write(name, frames, dirs, ms, data, glow):
    frames = W.limit_colors(frames, W.COLOR_MAX, name)
    if glow is not None:
        frames = clamp_cool(frames, set(glow))
    fw, fh = frames[dirs[0]][0].size
    F = len(ms)
    sheet = Image.new("RGBA", (fw * F, fh * len(dirs)), (0, 0, 0, 0))
    for r, d in enumerate(dirs):
        assert len(frames[d]) == F, (name, d)
        for c, im in enumerate(frames[d]):
            sheet.alpha_composite(im, (c * fw, r * fh))
    cols = W.colors_of(sheet)
    assert not (cols - W.ALLOWED), (name, sorted(cols - W.ALLOWED))
    assert len(cols) <= W.COLOR_MAX, (name, len(cols))
    assert not W.has_partial(sheet), name
    assert sum(W.edge_touch(im) for d in dirs for im in frames[d]) == 0, (name, "edge")
    hotset = {W.X0, W.X1, W.A26}
    for d in dirs:                                   # 판정 밖 프레임 A25 이하 검사(Q64·Q65)
        for i, im in enumerate(frames[d]):
            if glow is not None and i not in glow:
                assert not (W.colors_of(im) & hotset), (name, d, i)
    j = dict(image=name + ".png", action=name, version="v3-r55", frameWidth=fw, frameHeight=fh, frames=F, directions=dirs,
             layout="rows = directions, columns = frames", frameIndex="row * frames + column",
             fps=round(1000 * F / sum(ms), 2), frameDurationsMs=list(ms), loop=False, pixelScale=0.5,
             paletteSwap="none", paletteSwapNote="53라운드 Q62 — fx 는 지역 바닥 팔레트 교체 제외",
             palette=W.PALETTE_NOTE, colors=len(cols), semiTransparent=False, source=SRC)
    j.update(data)
    if glow is not None:
        j["glowFrames"] = sorted(glow)
        j["glowRule"] = ("53라운드 Q65: 백열 X0/X1·A26 은 glowFrames(판정 순간)만. 그 밖 프레임은 A25(#eecc78) 이하 — 빌드 검사 통과")
    os.makedirs(W.OUT_FX, exist_ok=True)
    sheet.save(os.path.join(W.OUT_FX, name + ".png"), optimize=True)
    with open(os.path.join(W.OUT_FX, name + ".json"), "w", encoding="utf-8") as f:
        import json
        json.dump(j, f, ensure_ascii=False, indent=1)
    return sheet, j, frames
