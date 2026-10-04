"""57라운드 갈래 1단 이펙트 — 붓획(56 Q11) · 재·호박만 · 백열(X0/X1·A26)은 glowFrames(판정 순간)의 몇 도트만.

  katana_spin                 회전 베기 — 몸 둘레를 화면 시계 방향으로 한 바퀴 도는 열린 붓 한 획(닫힌 원 금지, 바닥 타원 groundKy 0.85)
  katana_spin_ready           회전 베기 홀드 0.4초 — 칼끝 작은 네 갈래 반짝임(1행 any, A25 이하)
  katana_guardbreak           가드 불가 내려베기 — 머리 위에서 앞 땅까지 세로 붓획 + 앞으로 3칸 갈라지는 땅 금
  greatsword_shatter_crack_t1~t5  대검 파쇄 1단 — 58 기본 균열 greatsword_charge_crack_line_t1~t5 의 '관통·탄 소멸' 강화판(같은 규격, 1:1 교체, rotate)
  greatsword_shatter_snuff    파쇄 균열이 적 투사체를 지우는 자리의 재 터짐(1행 any)
  greatsword_quake_ring       대검 중압 1단 — 원형 진동(lv1~3 = 반경 2.5/3/3.5칸), 퍼져 나간 뒤 안으로 끌어당기는 획
  dagger_fan_throw            부채꼴 투척 — 왼팔 역손 뿌리기 붓획 + 놓는 순간 부채꼴 세 줄
  dagger_thrown               투척 송곳니 투사체(1행 any, rotate, 루프)
  dagger_cross_clone          쌍격 1단 — 낙인 기폭 때 반대편에서 달려와 교차해 베고 재로 부서지는 그림자 분신 + X 붓획
  bow_arrow_pierce            저격 1단 관통 화살 — 완벽 놓기 화살 + 꿰뚫는 나선 꼬리(1행 any, rotate, 루프)
  bow_arrow_pierce_hit        관통 화살이 적을 꿰뚫고 나가는 순간(1행 any, rotate)
좌표: 로컬 '오른쪽 보기'(x = 조준, y = 화면 아래, 원점 = 판정 원점 = 피벗 위 40 도트) → combo56_fx/fx56.TA 로 방향 회전(4행 = down, up, left, right).
대검 fx 중 방향 있는 균열은 rotate(마우스 각) — 56 plunge_wave 와 같은 방식, 원형 진동은 방향 무관(rowsAre stages).
"""
import json
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "combo56_fx"))
sys.path.insert(0, os.path.join(WORK, "atlas57"))
sys.path.insert(0, HERE)
import fx56 as F  # noqa: E402
import brush as BR  # noqa: E402
from brush import W, FK  # noqa: E402
import gridsheet  # noqa: E402

ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets/sprites")
OUT_FX = os.path.join(SPR, "fx/v3")
SRC = "parts/art/work/branch57/build.py fx (57라운드 갈래 1단 수단 fx)"
F.SRC = SRC
F.VERSION = "v3-r57-branch"
CO = F.CO
HIT_UP = F.HIT_UP                     # 40
GROUND = HIT_UP
DIRS4 = F.DIRS4
DIR_ANG = F.DIR_ANG
KY = 0.85                             # 바닥 타원 세로 압축(greatsword_ground_crack · charge_ring 과 같음)
TILE_D = 64                           # 1칸 = 16 월드 px = 64 도트
EFFECT_RULE = ("56라운드 Q11 붓획(시작 가늘고·가운데 굵고·끝 갈라짐) — 닫힌 원 금지. 재·호박만(57 지시), 흰 픽셀(X0/X1·A26)은 판정 프레임의 "
               "획 머리 몇 도트만, 그 밖 프레임은 A25(#eecc78) 이하 — 빌드 검사 통과")
R57 = "57라운드 Q22~Q37 갈래 1단 수단(설계안 2.2~2.5 · 6.2)"


def body(rel):
    return gridsheet.load_meta(os.path.join(SPR, rel + ".json"))


def starts(ms):
    s, t = [], 0
    for m in ms:
        s.append(t)
        t += m
    return s


def zpts(t, pts):
    out = []
    for x, y, z in pts:
        sx, sy = t((x, y))
        out.append((sx, sy - z))
    return out


def ell(d, a_deg, r, z=0.0, ky=KY):
    """바닥 타원 위 점(화면): 조준각 + a_deg."""
    a = math.radians(DIR_ANG[d] + a_deg)
    return (CO[0] + math.cos(a) * r, CO[1] + math.sin(a) * r * ky - z)


def frame():
    return F.frame(None)


def _decay_k(i, first, n):
    return (i - first + 1) / (n - first)


# =============================================================================
# 칼 — 회전 베기
# =============================================================================
SPIN_R = 160.0                       # 반경 2.5칸(도트) — 붓획 바깥 가장자리
SPIN_MS = [40, 40, 40, 40, 40, 60, 70, 90]
SPIN_GLOW = [1, 2, 3, 4]
SPIN_A = (-50.0, 278.0)              # 조준 기준: 앞 약간 왼쪽에서 시작 → 화면 시계 방향 328°(시작 쪽 틈 32° — 닫힌 원 금지)
SPIN_PLAN = [("pre", dict(head=0.06)), ("draw", dict(head=0.3)), ("draw", dict(head=0.56)), ("draw", dict(head=0.8)),
             ("draw", dict(head=1.0)), ("decay", dict(k=0.33)), ("decay", dict(k=0.66)), ("decay", dict(k=1.0))]


def spin_frames(d, seed=571):
    wmax = 11.0
    r = SPIN_R - wmax * 0.45
    n = 220
    pts = []
    for i in range(n + 1):
        s = i / n
        a = SPIN_A[0] + (SPIN_A[1] - SPIN_A[0]) * s
        z = 8.0 + 6.0 * math.sin(math.pi * s)              # 허리 높이 — 가운데서 살짝 떠오름
        pts.append(ell(d, a, r, z))
    S = BR.Stroke(pts, wmax, seed=seed, peak=0.42, dry_from=0.66, split=2.1, drops=9, start_w=0.1, end_w=0.5)
    # 안쪽 바람 획(가는 보조 획 2개 — 회전 속도감, 판정 없음)
    winds = []
    for j, (a0, a1, rr) in enumerate(((10.0, 150.0, 0.62), (170.0, 300.0, 0.7))):
        wp = [ell(d, a0 + (a1 - a0) * i / 60, SPIN_R * rr, 10.0) for i in range(61)]
        winds.append(BR.Stroke(wp, 3.2, seed=seed + 3 + j, peak=0.5, dry_from=0.5, split=1.6, drops=2, start_w=0.15, end_w=0.3, lanes=4))
    st = dict(F.STYLE["katana"], drops=9, flakes=8)

    def extra(fr, i, kind, p):
        if kind == "draw" and p["head"] > 0.5:
            Lw = fr.L([W.A17, W.A18, W.A19])
            for j, wst in enumerate(winds):
                if (j == 0 and p["head"] > 0.5) or (j == 1 and p["head"] >= 0.99):
                    wst.draw(Lw, head=1.0, vmax=0.7, drops=False)
        if kind == "decay" and p["k"] < 0.5:
            Lw = fr.L([W.A17, W.A18, W.A19])
            for wst in winds:
                wst.draw(Lw, head=1.0, tail=0.5, vmax=0.5, k=p["k"], drops=False)
    return F._stroke_frames(S, st, SPIN_PLAN, seed, extra=extra)


READY_MS = [30, 40, 50, 60, 70]


def ready_frames():
    out = []
    for i, ms in enumerate(READY_MS):
        fr = frame()
        Lg = fr.L([W.A19, W.A21, W.A23, W.A25])
        Le = fr.L([W.A18, W.A19, W.A21])
        sz = [3.5, 7.5, 9.0, 7.0, 4.0][i]
        v = [0.7, 0.99, 0.9, 0.7, 0.5][i]
        cx, cy = CO
        Lg.star4(cx, cy, sz, w=0.8, v=v, rot=0.0, diag=0.45 if i in (1, 2) else 0.0)
        if i >= 2:
            r = random.Random(7 + i)
            for j in range(4):
                a = r.uniform(0, 6.28)
                dist = 4 + 3 * (i - 1)
                W.ember(Le, cx + math.cos(a) * dist, cy + math.sin(a) * dist - (i - 2) * 2, math.cos(a), math.sin(a), 2.0, w=0.5, v=0.8 - 0.1 * i)
        out.append(fr.render())
    return out


# =============================================================================
# 칼 — 가드 불가 내려베기
# =============================================================================
GB_MS = [30, 40, 40, 60, 70, 80, 100]
GB_GLOW = [2, 3]
GB_IMPACT = 2
GB_L = 192.0                          # 3칸
GB_W = 64.0                           # 1칸


def guardbreak_frames(d, seed=581):
    t = F.TA(d, *CO)
    Rv = 90.0
    lat = -22.0 if d == "up" else -6.0            # 뒷면(위) 행은 세로 획이 겹쳐 짧아 보이므로 옆으로 조금 휘게

    def P(phi):
        f = Rv * math.cos(phi)
        z = Rv * 1.08 * math.sin(phi) + 6
        x, y = t((f, lat * math.sin(phi)))
        return x, y - z
    p0, p1 = math.radians(98), math.radians(-14)
    vpts = [P(p0 + (p1 - p0) * i / 120) for i in range(121)]
    V = BR.Stroke(vpts, 9.0, seed=seed, peak=0.55, dry_from=0.82, split=0.8, drops=0, start_w=0.1, end_w=0.7)
    # 땅 가름: 칼이 닿은 자리(0.85Rv) → 3칸 끝. 가운데 금 + 양쪽으로 벌어지는 얇은 획 두 줄(쪼개진 땅)
    gx0 = Rv * 0.85
    G0 = BR.Stroke([t((gx0 + (GB_L - gx0) * i / 40, 0.0)) for i in range(41)], 7.0, seed=seed + 1, peak=0.2, dry_from=0.62,
                   split=1.4, drops=8, start_w=0.75, end_w=0.35)
    sides = []
    for sgn in (-1, 1):
        sp = [t((gx0 + 10 + (GB_L - 18 - gx0) * i / 30, sgn * (GB_W * 0.22) * math.sin(math.pi * i / 30) ** 0.7)) for i in range(31)]
        sides.append(BR.Stroke(sp, 3.0, seed=seed + 4 + sgn, peak=0.35, dry_from=0.55, split=1.3, drops=3, start_w=0.3, end_w=0.3, lanes=4))
    rng = random.Random(seed)
    crack = W.jag(rng, (gx0 - 6, 0.0), (GB_L + 6, 0.0), n=10, amp=2.5)
    shards = [(rng.uniform(gx0, GB_L), rng.uniform(-GB_W * 0.3, GB_W * 0.3), rng.uniform(1.6, 2.8), rng.uniform(-1, 1)) for _ in range(14)]
    out = []
    for i in range(len(GB_MS)):
        fr = frame()
        Lgr = fr.L([W.B0, W.B1, W.B2])
        Lcrk = fr.L([W.A18, W.A19, W.A21, W.A23])
        Lf = fr.L(BR.FLAKE_G)
        Lb = fr.L(BR.INK_K)
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        if i == 0:
            V.draw(Lb, head=0.3, vmax=0.6, drops=False)
        elif i == 1:
            V.draw(Lb, head=0.8, vmax=0.84, drops=False)
        elif i in (2, 3):
            V.draw(Lb, head=1.0, tail=0.1 if i == 2 else 0.35, vmax=0.88, drops=False)
            G0.draw(Lb, head=1.0 if i == 3 else 0.7, vmax=0.92, hot=True, Lhot=Lh)
            if i == 2:
                V.hot_head(Lh, 0.999)
            for s_ in sides:
                s_.draw(Lb, head=0.6 if i == 2 else 1.0, vmax=0.78)
        else:
            k = _decay_k(i, 4, len(GB_MS))
            V.draw(Lb, head=1.0, tail=0.5 + 0.45 * k, vmax=0.7 - 0.2 * k, wk=1 - 0.3 * k, k=k, drops=False)
            G0.draw(Lb, head=1.0, tail=0.1 + 0.6 * k, vmax=0.82 - 0.2 * k, wk=1 - 0.25 * k, k=k, fall=2 + 6 * k)
            for s_ in sides:
                s_.draw(Lb, head=1.0, tail=0.2 + 0.6 * k, vmax=0.7 - 0.2 * k, k=k)
            G0.flakes(Lf, k, 0.0, 1.0, 7, size=1.8, fall=8.0, seed=i)
        if i >= 2:
            kk = 0.0 if i < 4 else _decay_k(i, 4, len(GB_MS))
            scr = t.pts(crack)
            Lgr.stroke(scr, 2.2 * (1 - 0.3 * kk), prof=FK.tp_both(0.5, 0.5), v=0.8 * (1 - 0.3 * kk))
            Lcrk.stroke(scr, 1.0 * (1 - 0.3 * kk), prof=FK.tp_both(0.6, 0.6), v=0.95 - 0.5 * kk,
                        dash=(9.0, 0.75 - 0.3 * kk, 0.0) if kk > 0.3 else None)
            age = i - 2
            for x, y, sz, sp in shards:                      # 쪼개진 땅 조각이 튀어 오르고 떨어짐
                if x > (GB_L if i > 2 else GB_L * 0.7):
                    continue
                sx, sy = t((x, y))
                h = 10 * age - 3.2 * age * age
                if h < -4 or age > 4:
                    continue
                W.flake(Lf, sx + sp * age * 2, sy - max(0.0, h), sz * (1 - 0.12 * age), 0.6 * age + sp, v=0.9 - 0.12 * age)
            if i <= 4:
                r = random.Random(seed * 3 + i)
                for j in range(6):
                    x = r.uniform(gx0, GB_L)
                    sx, sy = t((x, 0))
                    a = r.uniform(-2.6, -0.5)
                    dist = r.uniform(4, 12) * (1 + 0.8 * age)
                    W.ember(Le, sx + math.cos(a) * dist, sy + math.sin(a) * dist, math.cos(a), math.sin(a), 3.2 * (1 - 0.2 * age), w=0.6, v=0.9 - 0.15 * age)
        out.append(fr.render())
    return out


# =============================================================================
# 대검 — 파쇄 직선 균열(강화판) · 탄 소멸 터짐
# =============================================================================
# 58라운드 기본 균열 greatsword_charge_crack_line_t1~t5(다른 작업)와 같은 규격 — 칸 수별 시트 · 12프레임 · 같은 ms · 앞머리 48 도트/30ms.
# 파쇄 1단이면 같은 tN 을 이 _shatter 시트로 1:1 교체(프레임 번호·시각·앵커 동일).
SH_MS = [30, 30, 30, 30, 30, 30, 30, 50, 60, 80, 100, 120]
SH_GLOW = []
SH_RUN = 7                                           # 앞머리 달림 f0~f6
SH_SPEED = 48                                        # 앞머리 도트/프레임(1.6 도트/ms)
SH_TILES = [1, 2, 3, 4, 5]


def sh_front(tiles):
    L = tiles * TILE_D
    return [min(L, SH_SPEED * (i + 1)) if i < SH_RUN else L for i in range(len(SH_MS))]


def shatter_frames(tiles, seed=601):
    t = F.TA("right", *CO)
    L = tiles * TILE_D
    rng = random.Random(seed + tiles)
    main = W.jag(rng, (0.0, 0.0), (L, 0.0), n=6 + tiles * 3, amp=3.0)
    branches = []
    for j in range(tiles * 3):
        f0 = L * (j + 0.6) / (tiles * 3)
        sgn = 1 if j % 2 else -1
        ang = sgn * math.radians(rng.uniform(25, 55))
        ln = rng.uniform(14, 26)
        branches.append((f0, W.jag(rng, (f0, 0.0), (f0 + math.cos(ang) * ln, math.sin(ang) * ln), n=3, amp=1.5)))
    # 솟는 돌 조각(파편) — 지나간 자리에서 튀어 오름: (x, 옆, 크기, 시작 프레임)
    spikes = [(L * (j + rng.uniform(0.1, 0.9)) / (tiles * 4), rng.uniform(-14, 14), rng.uniform(3.0, 5.0)) for j in range(tiles * 4)]
    # 균열 위 붓획(관통하는 힘의 선) — 흙·녹 붓
    S = BR.Stroke([t((x, 0.0)) for x in [L * i / 60 for i in range(61)]], 7.0, seed=seed, peak=0.3, dry_from=0.7, split=1.5, drops=10,
                  start_w=0.5, end_w=0.4)
    out = []
    for i in range(len(SH_MS)):
        fr = frame()
        Ld = fr.L(W.R_DUST)
        Lgr = fr.L([W.B0, W.B1, W.B2])
        Lcrk = fr.L([W.A18, W.A19, W.A21, W.A23, W.A25])
        Lf = fr.L(BR.FLAKE_G)
        Lb = fr.L(BR.INK_G)
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        front = sh_front(tiles)[i]
        hf = front / L
        k = 0.0 if i < SH_RUN else _decay_k(i, SH_RUN, len(SH_MS))
        # 금(가장자리 흙 + 호박 심) — 앞머리까지만
        seg = [p for p in main if p[0] <= front] + ([(front, 0.0)] if front < L else [])
        if len(seg) >= 2:
            scr = t.pts(seg)
            Lgr.stroke(scr, 3.6 * (1 - 0.25 * k), prof=FK.tp_both(0.3, 0.4), v=0.85 * (1 - 0.3 * k))
            Lcrk.stroke(scr, 1.5 * (1 - 0.3 * k), prof=FK.tp_both(0.4, 0.5), v=(0.97 if i < SH_RUN else 0.85 - 0.5 * k),
                        dash=(10.0, 0.8 - 0.35 * k, 0.0) if k > 0.3 else None)
        for f0, br in branches:
            if f0 > front - 8:
                continue
            scr = t.pts(br)
            Lgr.stroke(scr, 1.8 * (1 - 0.3 * k), prof=FK.tp_tail(0.9), v=0.7 * (1 - 0.3 * k))
            Lcrk.stroke(scr, 0.7, prof=FK.tp_tail(0.9), v=0.75 - 0.45 * k)
        if i < SH_RUN:                                # 앞머리를 따라 그어지는 붓(관통) — 앞머리가 끝에 닿으면 그 자리 머무름
            S.draw(Lb, head=hf, tail=max(0.0, hf - 0.45 * min(1.0, 3.0 / tiles)), vmax=0.86, drops=(front >= L))
            hx, hy = t((front, 0.0))
            for j in range(5):                        # 앞머리 흙먼지·불티
                a = math.radians(-150 + 50 * j + 10 * i)
                W.ember(Le, hx + math.cos(a) * (5 + 2 * j), hy + math.sin(a) * (4 + j) - 2, math.cos(a), math.sin(a), 3.5, w=0.6, v=0.9)
            Ld.cloud(hx - 6, hy - 2, 7 + min(i, 4), v=0.6, flat=0.6, seed=i)
        else:
            S.draw(Lb, head=1.0, tail=0.4 + 0.55 * k, vmax=0.7 - 0.25 * k, wk=1 - 0.3 * k, k=k, fall=2 + 5 * k)
        for x, y, sz in spikes:                       # 지나간 자리에서 돌 조각이 솟았다 떨어짐
            if x > front:
                continue
            born = max(0, int(x / SH_SPEED))
            age = i - born
            if age < 0 or age > 5:
                continue
            h = 12 * age - 3.0 * age * age
            if h < -3:
                continue
            sx, sy = t((x, y))
            W.flake(Lf, sx, sy - max(0.0, h), sz * (1 - 0.1 * age), 0.7 * age + x * 0.1, v=0.95 - 0.1 * age)
            if age <= 1:
                Ld.cloud(sx, sy + 1, 4 + 2 * age, v=0.55, flat=0.55, seed=int(x))
        out.append(fr.render())
    return out


SNUFF_MS = [30, 40, 50, 60, 70, 80]


def snuff_frames(seed=611):
    out = []
    cx, cy = CO
    r = random.Random(seed)
    parts = [(r.uniform(0, 6.28), r.uniform(5, 13), r.uniform(1.0, 2.0)) for _ in range(10)]
    for i, ms in enumerate(SNUFF_MS):
        fr = frame()
        Ld = fr.L(W.R_ASHG)
        Lf = fr.L(BR.FLAKE)
        Lc = fr.L([W.A18, W.A19, W.A21, W.A23])
        k = i / (len(SNUFF_MS) - 1)
        if i < 4:                                     # 깨진 고리(열린 호 두 개)
            rr = 5 + 9 * k
            Lc.arc(cx, cy, rr, rr * 0.9, -2.6, -0.4, 1.0 * (1 - 0.5 * k), prof=FK.tp_both(0.6, 0.5), v=0.95 - 0.5 * k)
            Lc.arc(cx, cy, rr, rr * 0.9, 0.6, 2.6, 0.9 * (1 - 0.5 * k), prof=FK.tp_both(0.6, 0.5), v=0.85 - 0.5 * k)
        if i < 5:
            Ld.cloud(cx, cy - 2 * i, 4 + 3 * i, v=0.75 - 0.12 * i, flat=0.8, seed=i)
        for a, dist, sz in parts:
            d_ = dist * (0.4 + k * 1.3)
            W.flake(Lf, cx + math.cos(a) * d_, cy + math.sin(a) * d_ * 0.8 + 8 * k * k, sz * (1 - 0.4 * k), a + i, v=0.9 - 0.4 * k)
        out.append(fr.render())
    return out


# =============================================================================
# 대검 — 중압 원형 진동(끌어당김)
# =============================================================================
QK_MS = [40, 50, 60, 70, 80, 80, 90, 100, 120]
QK_GLOW = [0, 1]
QK_STAGES = {"lv1": 2.5, "lv2": 3.0, "lv3": 3.5}    # 칸(설계안 2.3 반경 2.5/3/3.5칸)


def quake_frames(tiles, seed=621):
    R = tiles * TILE_D
    cx, cy = CO[0], CO[1] + GROUND                   # 바닥(내려찍은 자리) 기준
    rng = random.Random(seed + int(tiles * 10))
    # 바깥 고리 = 열린 붓획 4개(이음매 틈)
    arcs = []
    n_arc = 4
    for j in range(n_arc):
        a0 = j * 360.0 / n_arc + rng.uniform(8, 18)
        a1 = (j + 1) * 360.0 / n_arc - rng.uniform(10, 22)
        arcs.append((a0, a1, rng.randint(0, 999)))

    def ring_stroke(rr, a0, a1, w, sd):
        pts = []
        for i in range(61):
            a = math.radians(a0 + (a1 - a0) * i / 60)
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * KY))
        return BR.Stroke(pts, w, seed=sd, peak=0.45, dry_from=0.6, split=1.3, drops=3, start_w=0.2, end_w=0.4)
    # 끌어당김 획: 바깥에서 안쪽으로(머리 = 안쪽 끝)
    pulls = []
    n_pull = 10 + int(tiles * 2)
    for j in range(n_pull):
        a = math.radians(j * 360.0 / n_pull + rng.uniform(-8, 8))
        r0, r1 = R * rng.uniform(0.92, 1.05), R * rng.uniform(0.42, 0.55)
        bend = 0.28 + rng.uniform(-0.06, 0.06)
        pts = []
        for i in range(21):
            u = i / 20
            rr = r0 + (r1 - r0) * u
            aa = a + bend * math.sin(math.pi * u)
            pts.append((cx + math.cos(aa) * rr, cy + math.sin(aa) * rr * KY))
        pulls.append(BR.Stroke(pts, 4.5 + tiles, seed=seed + 50 + j, peak=0.8, dry_from=0.85, split=0.8, drops=0, start_w=0.1, end_w=0.9, lanes=4))
    radial = []
    for j in range(8):
        a = math.radians(j * 45 + rng.uniform(-12, 12))
        ln = R * rng.uniform(0.18, 0.3)
        pts = W.jag(rng, (math.cos(a) * 6, math.sin(a) * 6 * KY), (math.cos(a) * ln, math.sin(a) * ln * KY), n=4, amp=2.0)
        radial.append([(cx + x, cy + y) for x, y in pts])
    dust = [(rng.uniform(0, 6.28), rng.uniform(0.75, 1.0)) for _ in range(9 + int(tiles * 2))]
    out = []
    for i in range(len(QK_MS)):
        fr = frame()
        Ld = fr.L(W.R_DUST)
        Lgr = fr.L([W.B0, W.B1, W.B2])
        Lcrk = fr.L([W.A18, W.A19, W.A21, W.A23])
        Lf = fr.L(BR.FLAKE_G)
        Lb = fr.L(BR.INK_G)
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        # 가운데 패임·금(내내 남음)
        kk = max(0.0, (i - 5) / 3)
        for rp in radial:
            Lgr.stroke(rp, 2.2 * (1 - 0.3 * kk), prof=FK.tp_tail(0.8), v=0.8 * (1 - 0.3 * kk))
            Lcrk.stroke(rp, 0.9, prof=FK.tp_tail(0.8), v=(0.95 if i < 2 else 0.8 - 0.5 * kk))
        if i == 0:                                    # 내려찍은 순간 — 가운데 핵(몇 도트 백열) + 짧은 고리
            Lh.stamp(cx, cy - 2, 2.2, 1.0, soft=0.6)
            for a0, a1, sd in arcs:
                ring_stroke(R * 0.32, a0, a1, 6.0, sd).draw(Lb, head=1.0, vmax=0.9, drops=False)
            Ld.cloud(cx, cy - 4, 10 + 2 * tiles, v=0.7, flat=0.55, seed=1)
        elif i in (1, 2):                             # 진동이 퍼짐(1 = 0.7R · 2 = 1.0R 판정 가장자리)
            rr = R * (0.68 if i == 1 else 0.97)
            for a0, a1, sd in arcs:
                s_ = ring_stroke(rr, a0, a1, 8.0 + tiles, sd)
                s_.draw(Lb, head=1.0, vmax=0.9, hot=(i == 1), Lhot=Lh, drops=(i == 2))
            for a, rr2 in dust:
                ex, ey = cx + math.cos(a) * rr * rr2, cy + math.sin(a) * rr * rr2 * KY
                Ld.cloud(ex, ey - 3, 6 + tiles, v=0.6, flat=0.55, seed=int(a * 10))
        elif i in (3, 4, 5):                          # 끌어당김: 바깥 → 안쪽 획, 고리가 안으로 줄어듦
            q = (i - 3) / 2
            rr = R * (0.9 - 0.25 * q)
            for a0, a1, sd in arcs:
                ring_stroke(rr, a0 + 12 * q, a1 - 12 * q, (7.0 + tiles) * (1 - 0.35 * q), sd).draw(
                    Lb, head=1.0, tail=0.15 * q, vmax=0.8 - 0.15 * q, k=0.3 * q, drops=False)
            for p_ in pulls:
                p_.draw(Lb, head=0.55 + 0.45 * q, tail=0.25 * q, vmax=0.78, drops=False)
            for a, rr2 in dust:                       # 먼지가 안쪽으로 끌려옴
                rd = R * rr2 * (0.95 - 0.4 * q)
                ex, ey = cx + math.cos(a) * rd, cy + math.sin(a) * rd * KY
                Ld.cloud(ex, ey - 3, (5 + tiles) * (1 - 0.3 * q), v=0.55, flat=0.55, seed=int(a * 10) + i)
                W.ember(Le, ex, ey - 6, -math.cos(a), -math.sin(a) * KY, 3.0, w=0.6, v=0.8 - 0.2 * q)
        else:                                         # 가라앉음: 안쪽 잔물결(점선 호) · 재 조각
            k = (i - 5) / 3
            for a0, a1, sd in arcs:
                rr = R * (0.55 - 0.1 * k)
                Lcrk.arc(cx, cy, rr, rr * KY, math.radians(a0), math.radians(a1), 0.9, prof=FK.tp_both(0.6, 0.5),
                         v=0.7 - 0.4 * k, dash=(10, 0.6 - 0.25 * k, 0.1 * sd))
            for p_ in pulls:
                p_.draw(Lb, head=1.0, tail=0.4 + 0.55 * k, vmax=0.6 - 0.2 * k, k=0.4 + 0.6 * k, drops=False)
            r = random.Random(seed + i)
            for j in range(10):
                a = r.uniform(0, 6.28)
                rd = R * r.uniform(0.15, 0.6)
                W.flake(Lf, cx + math.cos(a) * rd, cy + math.sin(a) * rd * KY - 6 * (1 - k), r.uniform(1.4, 2.4) * (1 - 0.3 * k), a, v=0.85 - 0.3 * k)
        out.append(fr.render())
    return out


# =============================================================================
# 단검 — 부채꼴 투척(몸 fx) · 투척 송곳니
# =============================================================================
FT_MS = [40, 40, 50, 60, 70]
FT_GLOW = [1]
FAN = (-15.0, 0.0, 15.0)


def fan_throw_frames(d, seed=631):
    t = F.TA(d, *CO)
    path = [(-8.0, 30.0, 44.0), (8.0, 22.0, 48.0), (24.0, 6.0, 47.0), (34.0, -14.0, 44.0), (28.0, -36.0, 38.0)]
    pts = []
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        for k in range(10):
            u = k / 10
            pts.append(tuple(a[j] + (b[j] - a[j]) * u for j in range(3)))
    pts.append(path[-1])
    S = BR.Stroke(zpts(t, pts), 6.0, seed=seed, peak=0.45, dry_from=0.6, split=1.8, drops=5, start_w=0.12, end_w=0.4)
    rel = (32.0, -8.0, 45.0)
    lines = []
    for j, a in enumerate(FAN):
        ar = math.radians(a)
        ln = 54.0 + 8 * (j == 1)
        p0 = (rel[0] + math.cos(ar) * 10, rel[1] + math.sin(ar) * 10, rel[2])
        p1 = (rel[0] + math.cos(ar) * ln, rel[1] + math.sin(ar) * ln, rel[2] - 2)
        lines.append(BR.Stroke(zpts(t, [p0, p1]), 3.2, seed=seed + 5 + j, peak=0.2, dry_from=0.5, split=1.2, drops=2, start_w=0.5, end_w=0.25, lanes=4))
    out = []
    for i in range(len(FT_MS)):
        fr = frame()
        Lf = fr.L(BR.FLAKE)
        Lb = fr.L(BR.INK_K)
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        if i == 0:
            S.draw(Lb, head=0.55, vmax=0.7, drops=False)
        elif i == 1:                                  # 놓는 순간
            S.draw(Lb, head=1.0, vmax=0.88, drops=True)
            for ln_ in lines:
                ln_.draw(Lb, head=1.0, vmax=0.9, hot=True, Lhot=Lh, drops=False)
            sx, sy = zpts(t, [rel])[0]
            r = random.Random(seed)
            for j in range(6):
                a = r.uniform(-3.1, 3.1)
                W.flake(Lf, sx + math.cos(a) * 5, sy + math.sin(a) * 5, 1.5, a, v=0.9)
        else:
            k = _decay_k(i, 2, len(FT_MS))
            S.draw(Lb, head=1.0, tail=0.2 + 0.7 * k, vmax=0.78 - 0.2 * k, wk=1 - 0.3 * k, k=k, fall=2 + 6 * k)
            for ln_ in lines:
                ln_.draw(Lb, head=1.0, tail=0.3 + 0.65 * k, vmax=0.7 - 0.25 * k, k=k)
            S.flakes(Lf, k, 0.2, 1.0, 5, size=1.4, fall=8.0, seed=i)
        out.append(fr.render())
    return out


THROWN_MS = [50, 50, 50, 50]


def _hex(h):
    return W.hexrgb(h) + (255,)


def thrown_frames():
    """투척 송곳니(그림 오른쪽 = 진행 방향). 몸통 22 도트 · 붕대 손잡이 · 균열 호박 · 끝 A23 + 뒤로 재·불티 꼬리."""
    G_EDGE, G_FACE, G_SH, OUT_ = "#7d8084", "#5c5e62", "#4d4f52", "#141516"
    out = []
    for i in range(len(THROWN_MS)):
        fr = frame()
        Lt = fr.L([W.A17, W.A18, W.A19, W.A21])
        Lf = fr.L(BR.FLAKE)
        cx, cy = CO
        # 꼬리: 가는 호박 줄(흔들림) + 재 조각
        wob = [0, 1, 0, -1][i]
        Lt.stroke([(cx - 15, cy), (cx - 30, cy + wob * 0.5), (cx - 46, cy + wob)], 1.1, prof=FK.tp_tail(1.0), v=0.95)
        r = random.Random(41 + i)
        for j in range(4):
            x = cx - 20 - j * 8 - r.uniform(0, 4)
            W.flake(Lf, x, cy + r.uniform(-3, 3), 1.2 - 0.2 * j, r.uniform(0, 6), v=0.8 - 0.15 * j)
        im = fr.render()
        px = im.load()
        # 송곳니(직접 찍음) — x: -14(손잡이 끝) ~ +14(끝), 몸통 28 도트(손에 쥔 1.3배 단검 31 도트보다 조금 작게)
        for x in range(-14, 15):
            if x < -7:                                # 붕대 손잡이
                for y in (-1, 0, 1):
                    px[cx + x, cy + y] = _hex(W.B3 if (x + y) % 3 else W.B2)
                continue
            u = (x + 7) / 21.0
            half = 3.0 * (1 - u) ** 0.8 if u < 0.86 else 0.6
            top = -int(round(half + 0.4))
            bot = int(round(half * 0.7))
            for y in range(top, bot + 1):
                if y == top:
                    c = G_EDGE
                elif y == bot:
                    c = OUT_
                elif y == 0 and x % 3 != 1:
                    c = W.A21                                 # 균열 혼불
                else:
                    c = G_FACE if y < 0 else G_SH
                px[cx + x, cy + y] = _hex(c)
            if x >= 11:
                px[cx + x, cy - 1 if x < 14 else cy] = _hex(W.A23)
        px[cx - 8, cy - 2] = _hex(W.A19)                   # 녹슨 못
        out.append(im)
    return out


# =============================================================================
# 단검 — 그림자 분신 교차 베기(쌍격 1단)
# =============================================================================
CC_MS = [50, 40, 30, 40, 60, 60, 70, 80, 90]
CC_GLOW = [3]
CC_SLASH = 3
CC_PATH = [(52.0, -44.0), (52.0, -44.0), (28.0, -14.0), (4.0, 14.0), (-14.0, 44.0), (-15.0, 46.0), (-15.0, 46.0), (-15.0, 46.0), (-15.0, 46.0)]
CC_POSE = [0, 0, 0, 1, 2, 2, 2, 2, 2]
OPP = {"down": "up", "up": "down", "left": "right", "right": "left"}


def clone_poses():
    """분신 자세 3개(단검 역수): 0 돌진(칼을 높이 들고 낮게 파고듦) · 1 교차 베기(팔을 가로질러 그음) · 2 지나침(팔 끝까지)."""
    import bd
    K_ = bd.K_
    m = dict(frames=[
        K_(-60, 10, -20, 15, 58, off="back", lunge=1.2, crouch=7.5, tw=-0.8, lean=2.2),
        K_(20, -25, 10, 22, 46, off="back", lunge=1.5, crouch=8.5, tw=0.1, lean=2.6, state="glow"),
        K_(100, -30, 60, 18, 42, off="back", lunge=1.2, crouch=8.0, tw=0.9, lean=2.0)])
    return bd.render_dagger(m)


def cross_clone_frames(d, poses, seed=641):
    import shadow56 as SH
    t = F.TA(d, *CO)
    cd = OPP[d]                                      # 분신이 바라보는 방향(주인공 반대편에서 주인공 쪽으로)
    # 분신 경로(로컬) — 화면 진행 방향
    p_start, p_end = t(CC_PATH[0]), t(CC_PATH[4])
    mv = (p_end[0] - p_start[0], p_end[1] - p_start[1])
    dv = "right" if abs(mv[0]) >= abs(mv[1]) and mv[0] > 0 else "left" if abs(mv[0]) >= abs(mv[1]) else ("down" if mv[1] > 0 else "up")
    PAD = SH.PAD
    cells = []
    for k in range(3):
        f = poses[cd][k]
        c = Image.new("RGBA", (192 + 2 * PAD, 192 + 2 * PAD), (0, 0, 0, 0))
        c.alpha_composite(f["body"], (PAD + 48, PAD + 48))
        bm = c.getchannel("A").point(lambda a: 255 if a else 0)
        c.alpha_composite(f["weapon"], (PAD, PAD))
        cells.append((c, bm))
    # X 붓획: A = 분신 경로를 따라, B = 반대 대각(주인공 쪽 베기 — 기폭과 함께)
    A_pts = zpts(t, [(40.0, -34.0, 10.0), (12.0, 0.0, 6.0), (-14.0, 36.0, 2.0)])
    B_pts = zpts(t, [(36.0, 30.0, 12.0), (10.0, 2.0, 7.0), (-18.0, -28.0, 2.0)])
    SA = BR.Stroke(A_pts, 6.5, seed=seed, peak=0.45, dry_from=0.62, split=1.8, drops=6, start_w=0.12, end_w=0.45)
    SB = BR.Stroke(B_pts, 6.0, seed=seed + 1, peak=0.45, dry_from=0.62, split=1.8, drops=6, start_w=0.12, end_w=0.45)
    out = []
    for i in range(len(CC_MS)):
        big = Image.new("RGBA", (F.CANVAS, F.CANVAS), (0, 0, 0, 0))
        # 붓획 층(분신 아래)
        fr = frame()
        Lf = fr.L(BR.FLAKE)
        Lb = fr.L(BR.INK_K)
        Lh = fr.L(BR.HOT)
        if i == CC_SLASH:
            SA.draw(Lb, head=1.0, vmax=0.9, hot=True, Lhot=Lh)
            SB.draw(Lb, head=0.7, vmax=0.88, hot=True, Lhot=Lh, drops=False)
        elif i == CC_SLASH + 1:
            SA.draw(Lb, head=1.0, tail=0.05, vmax=0.86)
            SB.draw(Lb, head=1.0, vmax=0.86)
        elif i > CC_SLASH + 1:
            k = _decay_k(i, CC_SLASH + 2, len(CC_MS))
            for s_ in (SA, SB):
                s_.draw(Lb, head=1.0, tail=0.15 + 0.7 * k, vmax=0.76 - 0.22 * k, wk=1 - 0.3 * k, k=k, fall=2 + 6 * k)
                s_.flakes(Lf, k, 0.1, 1.0, 4, size=1.4, fall=8.0, seed=i)
        fr.render(big)
        # 분신
        c, bm = cells[CC_POSE[i]]
        if i == 0:
            s = SH.silhouette(c, bm, dv, False, 0.55, 640)
            s = SH.ash(s, dv, 0.3, 641)
        elif i in (1, 2, 3):
            s = SH.silhouette(c, bm, dv, i >= 2, 0.0, 640)
            if i >= 2:
                s = SH.streaks(s, dv, i, 643)
        elif i == 4:
            s = SH.silhouette(c, bm, dv, False, 0.0, 640)
        else:
            k = (i - 4) / (len(CC_MS) - 5)
            s = SH.silhouette(c, bm, dv, False, k, 644 + i)
            s = SH.ash(s, dv, k, 645)
        px_, py_ = t(CC_PATH[i])
        # 분신 발 = 경로 점 아래 40 도트(경로는 판정 원점 높이 = 적 히트박스 중심 높이)
        fx_, fy_ = px_, py_ + HIT_UP
        ox = int(round(fx_ - (PAD + 48 + 48)))
        oy = int(round(fy_ - (PAD + 48 + 138)))
        big.alpha_composite(s, (ox, oy))
        out.append(big)
    return out


# =============================================================================
# 활 — 관통 화살 · 꿰뚫음
# =============================================================================
PIERCE_MS = [50, 50, 50, 50]
PH_MS = [30, 40, 50, 60, 70, 80]
PH_GLOW = [0]


def _arrow_cells():
    m = gridsheet.load_meta(os.path.join(SPR, "fx/v3/bow_arrow.json"))
    im = gridsheet.open_grid(os.path.join(SPR, "fx/v3/bow_arrow.json"))
    cell = im.crop((0, 0, m["frameWidth"], m["frameHeight"]))
    return cell, (m["pivot"]["x"], m["pivot"]["y"])


def pierce_frames():
    arrow, piv = _arrow_cells()
    hot = {W.hexrgb(W.X0), W.hexrgb(W.X1), W.hexrgb(W.A26)}
    px = arrow.load()
    for y in range(arrow.height):                    # 투사체는 판정 순간이 아님 → 촉 백열은 A25 로
        for x in range(arrow.width):
            if px[x, y][3] and px[x, y][:3] in hot:
                px[x, y] = W.hexrgb(W.A25) + (255,)
    bb = arrow.getbbox()
    tail_x = bb[0] - piv[0]                           # 화살 꼬리(깃 끝) x (피벗 기준)
    out = []
    for i in range(len(PIERCE_MS)):
        fr = frame()
        Lt = fr.L([W.A17, W.A18, W.A19, W.A21, W.A23])
        La = fr.L(BR.FLAKE)
        cx, cy = CO
        x0 = cx + tail_x + 2
        Ln = 96.0
        ph = i * math.pi / 2
        for strand, (amp, v) in enumerate(((3.2, 0.95), (3.2, 0.7))):   # 꿰뚫는 나선 두 가닥(위상 반대) — 뒤로 갈수록 가늘고 넓게
            pts = []
            for k in range(0, 97):
                u = k / 96
                x = x0 - u * Ln
                yy = amp * (0.35 + 0.65 * u) * math.sin(u * 5.5 * math.pi + ph + strand * math.pi)
                pts.append((x, cy + yy))
            Lt.stroke(pts, 1.0, prof=FK.tp_tail(0.9), v=v)
        Lt.stroke([(x0, cy), (x0 - Ln * 0.55, cy)], 0.6, prof=FK.tp_tail(1.0), v=0.6)
        r = random.Random(60 + i)
        for j in range(5):
            x = x0 - 18 - j * 16 - r.uniform(0, 8)
            W.flake(La, x, cy + r.uniform(-5, 5), 1.3 - 0.15 * j, r.uniform(0, 6), v=0.8 - 0.1 * j)
        im = fr.render()
        im.alpha_composite(arrow, (cx - piv[0], cy - piv[1]))
        out.append(im)
    return out


def pierce_hit_frames(seed=651):
    out = []
    cx, cy = CO
    r = random.Random(seed)
    shards = [(r.uniform(-0.6, 0.6), r.uniform(8, 26), r.uniform(1.0, 2.0)) for _ in range(12)]
    for i in range(len(PH_MS)):
        fr = frame()
        Lf = fr.L(BR.FLAKE)
        Lc = fr.L([W.A18, W.A19, W.A21, W.A23, W.A25])
        Le = fr.L([W.A19, W.A21, W.A23])
        Lh = fr.L(BR.HOT)
        k = i / (len(PH_MS) - 1)
        if i == 0:                                    # 꿰뚫는 순간 — 작은 핵(백열 몇 도트) + 앞뒤 가는 선
            Lh.stamp(cx, cy, 1.6, 1.0, soft=0.5)
            Lc.stroke([(cx - 12, cy), (cx + 18, cy)], 1.0, prof=FK.tp_both(0.6, 0.6), v=0.9)
        if i < 4:                                     # 꿰뚫린 자리의 열린 고리(진행 방향에 수직 — 세로 타원, 위·아래 두 호)
            rx, ry = 3 + 3 * i, 7 + 6 * i
            Lc.arc(cx + 2 * i, cy, rx, ry, -2.4, -0.7, 1.0 * (1 - 0.4 * k), prof=FK.tp_both(0.6, 0.5), v=0.95 - 0.45 * k)
            Lc.arc(cx + 2 * i, cy, rx, ry, 0.7, 2.4, 1.0 * (1 - 0.4 * k), prof=FK.tp_both(0.6, 0.5), v=0.9 - 0.45 * k)
        for a, dist, sz in shards:                    # 앞으로 튀어 나가는 파편·불티
            d_ = dist * (0.3 + 1.2 * k)
            x, y = cx + math.cos(a) * d_, cy + math.sin(a) * d_ + 10 * k * k
            if i < 3:
                W.ember(Le, x, y, math.cos(a), math.sin(a), 3.5 * (1 - 0.3 * i), w=0.6, v=0.9 - 0.2 * i)
            else:
                W.flake(Lf, x, y, sz * (1 - 0.3 * k), a + i, v=0.85 - 0.3 * k)
        out.append(fr.render())
    return out


# =============================================================================
# 시트 표 · 쓰기
# =============================================================================
def common_pp(pivot, origin):
    return dict(anchor="player_pivot", pivot={"x": pivot[0], "y": pivot[1]}, hitOriginInFrame={"x": origin[0], "y": origin[1]},
                pivotNote="pivot = 주인공 발(몸 피벗)에 맞춘다. 판정 원점 = pivot 위 40 도트(hitOriginInFrame)",
                effectRule=EFFECT_RULE, brushStroke=True, r57=R57)


def spec_table():
    T = {}
    ks = body("player/v3/player_katana_spin")
    st = starts(ks["frameDurationsMs"])
    hit = ks["timingMs"]["hitAt"]
    T["katana_spin"] = dict(kind="pp", dirs=DIRS4, fn=spin_frames, ms=SPIN_MS, glow=SPIN_GLOW, meta=dict(
        weapon="katana", bodySheet="player_katana_spin", spawn="body_ms", spawnAtMs=hit - SPIN_MS[0], impactAtBodyMs=hit, impactFrame=1,
        spawnRule="spawnAtMs = 몸 hitAt − frameDurationsMs[0] (= 몸 releaseFrame f6 시작). fx f1~f4 = 몸 회전 f7~f10(같은 40ms)",
        spawnAtReleaseMs=0, spawnNote="좌클릭을 뗀 순간(몸 releaseFrame 시작)에 1회 — 주인공 발을 따라감(회전 중 이동은 시스템). 검기 2회전이면 2회째 회전 시작(f7 재생 시작)에 한 번 더(설계안 2.2)",
        followPlayer=True, hitShape=ks["hitShape"], groundKy=KY,
        drawnArc=dict(fromDeg=SPIN_A[0], toDeg=SPIN_A[1], radiusDots=SPIN_R, brushWidthDots=11.0, groundKy=KY,
                      note="조준 기준 −50° → +278°(화면 시계 방향 328°) — 시작 쪽에 32° 틈(닫힌 원 금지). 바닥 타원(세로 ×0.85) 허리 높이"),
        frameRoles=["pre(붓 끝 닿음 — 뗌)", "draw(판정 · 앞)", "draw(판정 · 오른쪽 반)", "draw(판정 · 뒤)", "draw(판정 · 한 바퀴 — 붓털 갈라짐)",
                    "decay", "decay", "decay(재)"],
        design="회전 베기 — 몸 둘레를 화면 시계 방향으로 한 바퀴 도는 열린 붓 한 획(끝이 재로 갈라짐) + 안쪽 가는 바람 획 2개. 키아트 칼 7번(분위기만)",
        designRef="parts/art/work/gemini/weapon_moves/sheet_katana.png 7번"))
    T["katana_spin_ready"] = dict(kind="center", dirs=["any"], fn=lambda d: ready_frames(), ms=READY_MS, glow=[], meta=dict(
        weapon="katana", bodySheet="player_katana_spin", anchor="blade_tip", spawn="hold_ready", readyAfterHoldMs=400,
        anchorNote="무기 weapons/v3/katana_spin 의 bladeTipAnchors[방향][지금 프레임](무기 시트 좌표, 몸 좌표 = − (48,48))에 pivot 을 맞춘다. 행 any(방향 무관)",
        spawnNote="좌클릭을 누른 지 0.4초(몸 readyAfterHoldMs)에 1회 — '떼면 회전 베기' 준비 신호(연출만)", depth="above",
        frameRoles=["반짝 시작", "가장 밝음(A25)", "퍼짐 · 불티", "식음", "사라짐"],
        design="칼끝 작은 네 갈래 반짝임 + 대각 짧은 빛 + 불티 몇 개(백열 없음, A25 이하)", effectRule=EFFECT_RULE, r57=R57))
    kg = body("player/v3/player_katana_guardbreak")
    hit = kg["timingMs"]["hitAt"]
    T["katana_guardbreak"] = dict(kind="pp", dirs=DIRS4, fn=guardbreak_frames, ms=GB_MS, glow=GB_GLOW, meta=dict(
        weapon="katana", bodySheet="player_katana_guardbreak", spawn="body_ms", spawnAtMs=hit - sum(GB_MS[:GB_IMPACT]), impactAtBodyMs=hit,
        impactFrame=GB_IMPACT, spawnRule="spawnAtMs = 몸 hitAt − sum(frameDurationsMs[:impactFrame]) (= 몸 releaseFrame f9 시작 근처)",
        spawnAtReleaseMs=0, spawnNote="좌클릭을 뗀 순간(몸 releaseFrame 시작)에 1회. 주인공 발에 놓고 따라가지 않음(땅 금이 그 자리에 남음)",
        anchor="release_pivot", hitShape=kg["hitShape"], groundSplit=dict(lengthDots=GB_L, widthDots=GB_W, tiles=[3, 1]),
        frameRoles=["pre(머리 위 — 내려옴)", "draw(앞으로 떨어짐)", "impact(판정 · 땅에 닿음 — 땅 가름 머리 백열)", "impact(판정 · 3칸 끝까지 갈라짐)",
                    "decay", "decay", "decay(재)"],
        design="가드 불가 내려베기 — 머리 위에서 앞 땅까지 그은 세로 붓획 + 앞으로 3칸 쪼개지며 벌어지는 땅(가운데 호박 금 · 양옆 갈라진 획 · 튀는 흙 조각). 키아트 칼 8번(분위기만)",
        designRef="parts/art/work/gemini/weapon_moves/sheet_katana.png 8번"))
    for tn in SH_TILES:
        L = tn * TILE_D
        T["greatsword_shatter_crack_t%d" % tn] = dict(kind="center", dirs=["any"], fn=(lambda d, n=tn: shatter_frames(n)), ms=SH_MS, glow=SH_GLOW, meta=dict(
            weapon="greatsword", move="greatsword_charge_swing", anchor="slam_point", rotate=True, drawnFacing="right", flipY="allowed", depth="above",
            pivotNote="pivot = 칼끝이 바닥에 닿은 자리(몸 slamAnchors[행][impactFrame]) — 기본 균열 greatsword_charge_crack_line_t%d 와 같은 점. "
                      "그림 오른쪽 = 진행 방향 → 찍은 자리에서 커서 쪽 각도로 회전" % tn,
            tiles=tn, lengthPx=L, lengthWorld=L / 4, impactFrame=0,
            replaces="greatsword_charge_crack_line_t%d" % tn,
            replaceRule="파쇄 1단을 고른 런에서만, 기본 균열과 같은 tN(칸 수 고르기 pickRule 그대로)을 이 시트로 1:1 교체 — 프레임 수·ms·앵커·회전 규칙이 같다",
            variants={"t%d" % k: "greatsword_shatter_crack_t%d" % k for k in SH_TILES},
            spawn="body_ms", spawnNote="greatsword_charge_swing 의 impactFrame 시작에 1회(기본 균열과 같은 시각). 함께 greatsword_ground_crack 은 기본과 같게",
            hitShape=dict(type="rect", fromPx=0, lengthPx=L, halfWidthPx=round(0.6 * TILE_D, 1), frontPxByFrame=sh_front(tn), activeFrames=list(range(SH_RUN)),
                          speedDotsPerMs=1.6, pierce=True, destroysProjectiles=True,
                          note="앞머리(frontPxByFrame)가 지나가는 칸만 맞는다(적마다 1회, 관통) · 앞머리가 지나간 선 위 적 투사체 소멸(→ greatsword_shatter_snuff). "
                               "폭 1.2칸(설계안 2.3 — 기본 균열 halfWidth 28 보다 넓음) — 참고값, 시스템 데이터 기준"),
            frameRoles=["앞머리 달림(흙·녹 붓이 앞머리를 끔)"] * SH_RUN + ["식는 금 · 돌 조각 떨어짐", "식는 금", "식는 금", "식는 금 · 재", "재"],
            holdLast="마지막 칸을 붙잡아 오래 남기려면 시스템이 끄는 시점을 정함(반투명 금지)", shakeHint={"px": 7, "ms": 180},
            design="파쇄 — 기본 균열의 '관통·탄 소멸' 강화판: 흙·녹 붓 한 획이 앞머리를 끌고 가며 호박 금 + 양옆 가지 금, 지나간 자리마다 돌 조각이 솟았다 떨어짐, "
                   "앞머리 흙먼지·불티. 판정 순간 흰 픽셀 없음(기본 균열과 같음 — A25 이하)",
            branch="파쇄(破碎) 1단 A", brushStroke=True, effectRule=EFFECT_RULE, r57=R57, directionNote="1행 any — rotate(진행 각도로 회전)",
            diagNote="방향 행 없음(rotate) — 58라운드 대각 3/4 리그 교체와 무관"))
    for nm, fn, ms, glow, stages, meta in (
        ("greatsword_quake_ring", quake_frames, QK_MS, QK_GLOW, QK_STAGES, dict(
            weapon="greatsword", move="greatsword_charge_swing", anchor="slam_point", rotate=False, depth="below_player", groundKy=KY,
            anchorNote="pivot = 칼끝이 바닥에 닿은 자리(몸 slamAnchors[행][impactFrame] — 기본 균열과 같은 점, 바닥). 방향 무관(원) — 회전·반전 없음",
            spawn="body_ms", spawnNote="greatsword_charge_swing 의 impactFrame 시작에 1회(차지 단계 행). 중압 1단일 때 기본 균열과 함께 또는 대신(인터뷰 항목 — 아트 제안: 대신)",
            radiusPxByStage={k: v * TILE_D for k, v in QK_STAGES.items()}, impactFrame=0, hitFrames=[0, 1, 2],
            pullFrames=[3, 4, 5], pullNote="f3~f5 = 끌어당김(당김 0.6칸·경직 0.5초 — 설계안 2.3, 시스템 데이터). 진동 판정은 f1~f2(퍼짐) 권장",
            hitShape=dict(type="ring", radiusPxByStage={k: v * TILE_D for k, v in QK_STAGES.items()}, innerRadiusPx=0,
                          note="원형 진동 반경 2.5/3/3.5칸(설계안 2.3) — 참고값"),
            frameRoles=["내려찍음(판정 · 가운데 핵 백열 몇 도트)", "진동 퍼짐 0.7R(판정)", "1.0R(판정 가장자리)", "끌어당김", "끌어당김", "끌어당김",
                        "가라앉음(잔물결)", "가라앉음", "재"],
            design="중압 — 내려찍은 자리에서 열린 붓 고리 4조각이 퍼져 판정 가장자리까지 → 바깥에서 안쪽으로 그어지는 획과 끌려오는 흙먼지(끌어당김) → 안쪽 점선 잔물결·재 조각. 가운데 방사 금",
            branch="중압(重壓) 1단 B", stageNote="행 = 차지 단계(rowsAre stages): lv1 = 반경 2.5칸 · lv2 = 3칸 · lv3 = 3.5칸")),
    ):
        T[nm] = dict(kind="stages", dirs=list(stages), fn=(lambda d, f=fn, s=stages: f(s[d])), ms=ms, glow=glow, meta=dict(meta, rowsAre="stages",
                     layout="rows = stages (lv1, lv2, lv3), columns = frames — 행을 차지 단계로 고른다",
                     directionsNote="directions 칸에 단계 키(lv1·lv2·lv3) — 행 = 차지 단계(greatsword_ground_crack 의 sizes 와 같은 규약)",
                     brushStroke=True, effectRule=EFFECT_RULE, r57=R57,
                     diagNote="방향 행 없음(rotate/원) — 58라운드 대각 3/4 리그 교체와 무관"))
    T["greatsword_shatter_snuff"] = dict(kind="center", dirs=["any"], fn=lambda d: snuff_frames(), ms=SNUFF_MS, glow=[], meta=dict(
        weapon="greatsword", anchor="projectile", rotate=False, depth="above", spawn="projectile_destroyed",
        spawnNote="파쇄 균열 앞머리가 적 투사체를 지울 때 그 투사체 자리에 1회", effectRule=EFFECT_RULE, r57=R57,
        frameRoles=["깨진 고리 · 재 연기", "퍼짐", "퍼짐", "흩어짐", "재 조각", "재"],
        design="투사체가 땅 균열에 삼켜져 꺼짐 — 깨진 호박 고리 두 호 + 재 연기 + 재 조각(백열 없음)", branch="파쇄(破碎) 1단 A"))
    db = body("player/v3/player_dagger_fan_throw")
    rel = db["releaseFrame"]
    rel_ms = starts(db["frameDurationsMs"])[rel]
    T["dagger_fan_throw"] = dict(kind="pp", dirs=DIRS4, fn=fan_throw_frames, ms=FT_MS, glow=FT_GLOW, meta=dict(
        weapon="dagger", bodySheet="player_dagger_fan_throw", spawn="body_ms", spawnAtMs=rel_ms - FT_MS[0], impactFrame=1, impactAtBodyMs=rel_ms,
        spawnRule="spawnAtMs = 몸 releaseFrame 시작 − frameDurationsMs[0]. fx f1 시작 = 투척 순간(투사체 생성)", followPlayer=True,
        frameRoles=["왼팔 뿌리기(감음 → 앞)", "놓는 순간 — 부채꼴 세 줄(머리 백열 몇 도트)", "decay", "decay", "decay(재)"],
        design="부채꼴 투척 — 오른어깨 뒤에서 앞·왼쪽으로 쓸어 낸 왼팔 역손 뿌리기 붓획 + 놓는 자리에서 −15°·0°·+15° 로 뻗는 가는 붓 세 줄. 키아트 단검 5번(분위기만)",
        designRef="parts/art/work/gemini/weapon_moves/sheet_dagger.png 5번", fanDeg=list(FAN), branch="질풍(疾風) 1단 B"))
    T["dagger_thrown"] = dict(kind="center", dirs=["any"], fn=lambda d: thrown_frames(), ms=THROWN_MS, glow=[], meta=dict(
        weapon="dagger", anchor="projectile", rotate=True, drawnFacing="right", flipY="allowed", depth="above", loop=True, anim="loop_move",
        spawn="dagger_fan_throw", spawnNote="몸 player_dagger_fan_throw releaseFrame 시작에 3개 — 위치 = 무기 JSON throwSpawnAnchors, 각도 = 조준각 + fanDeg(−15°·0°·+15°). "
                                         "시스템이 진행 각도로 회전·이동(사거리 6칸 — 설계안 2.4)",
        pivotNote="pivot = 송곳니 몸통 가운데(끝 = pivot 앞 14 도트)", effectRule=EFFECT_RULE, r57=R57,
        frameRoles=["날아감(꼬리 흔들림 루프)"] * 4, hitFx="fx/v3/hit_dagger (기존)", lengthDots=28,
        design="투척 송곳니 — 단검과 같은 재 껍데기 송곳니(28 도트 · 붕대 손잡이 · 균열 혼불 · 끝 A23) + 뒤로 가는 호박 꼬리 줄과 재 조각", branch="질풍(疾風) 1단 B"))
    T["dagger_cross_clone"] = dict(kind="clone", dirs=DIRS4, fn=None, ms=CC_MS, glow=CC_GLOW, meta=dict(
        weapon="dagger", anchor="hitbox_center", followTarget=False, depth="같은 Y 정렬(주인공처럼 — katana_issen_shadow 와 같음)", lit=False,
        anchorNote="pivot = 낙인 기폭 대상 적의 히트박스 중심(dagger_brand_burst 와 같은 점). 행 = 주인공이 그 적을 바라보는 방향(그림자 걸음으로 등 뒤에 선 방향). "
                   "분신은 적의 반대편(주인공 맞은편)에서 나타나 적을 대각으로 가로질러 주인공 옆쪽으로 빠져나감 — 이동은 시트 안에 그려져 있음(시스템은 움직이지 않음)",
        spawn="brand_detonate", spawnNote="쌍격 1단일 때, 그림자 걸음으로 낙인 적 등 뒤에 선 순간(낙인 기폭 dagger_brand_burst 와 같은 순간) 1회",
        slashFrame=CC_SLASH, impactFrame=CC_SLASH, slashAtMs=sum(CC_MS[:CC_SLASH]), damageScale=0.5,
        damageNote="분신 교차 베기 = 기폭 피해 ×0.5(설계안 2.4 — 쌍격 기폭 +30%% 별도), 대상 적 1회, slashFrame 시작(생성 + %dms)" % sum(CC_MS[:CC_SLASH]),
        travelFrames=[1, 2, 3, 4], vanishFrames=[5, 6, 7, 8], effectRule=EFFECT_RULE, r57=R57,
        frameRoles=["재가 뭉쳐 분신이 나타남(맞은편)", "분신 — 파고들 자세", "돌진(속도선)", "교차 베기(판정 · X 붓획 머리 백열)", "지나침(X 남음)",
                    "부서짐 1", "부서짐 2", "부서짐 3", "재"],
        design="쌍격 — 적 맞은편에서 재가 뭉쳐 나타난 그림자 분신(어두운 재 4단 디더 · 불씨 테)이 적을 대각으로 가로질러 베고, 주인공 쪽 베기와 X 로 교차하는 붓획 두 개가 남은 뒤 "
               "분신은 위부터 재로 부서짐. 키아트 단검 7번(분위기만) · 칼 그림자 분신(katana_issen_shadow) 기법 재사용",
        designRef="parts/art/work/gemini/weapon_moves/sheet_dagger.png 7번", basedOn="dagger 1.3배 몸·무기 리그(주인공 반대 방향) + combo56_fx/shadow56 실루엣",
        branch="쌍격(雙擊) 1단 A"))
    T["bow_arrow_pierce"] = dict(kind="arrow", dirs=["any"], fn=lambda d: pierce_frames(), ms=PIERCE_MS, glow=[], meta=dict(
        weapon="bow", anchor="projectile", rotate=True, drawnFacing="right", flipY="allowed", depth="above", loop=True, anim="loop_move",
        spawn="perfect_release", spawnNote="저격 1단일 때 완벽 놓기 화살(bow_arrow 대신) — 최대 3명 관통(설계안 2.5). 꿰뚫을 때마다 bow_arrow_pierce_hit",
        pivotNote="pivot = bow_arrow 와 같은 점(화살 그림은 bow_arrow 그대로, 꼬리만 뒤로 96 도트)", effectRule=EFFECT_RULE, r57=R57,
        frameRoles=["날아감(나선 꼬리 위상 0°)", "90°", "180°", "270°"], reuse="화살 그림 = fx/v3/bow_arrow(촉 백열 A26 → A25), 53 '관통' 자막은 이 화살 설명(57 Q22~Q37)",
        design="관통 화살 — 화살 뒤로 꿰뚫는 나선 두 가닥(호박·어두운 호박, 위상이 돌아감)과 가운데 가는 줄, 재 조각이 끌림", branch="저격(狙擊) 1단 B"))
    T["bow_arrow_pierce_hit"] = dict(kind="center", dirs=["any"], fn=lambda d: pierce_hit_frames(), ms=PH_MS, glow=PH_GLOW, meta=dict(
        weapon="bow", anchor="projectile", rotate=True, drawnFacing="right", flipY="allowed", depth="above", spawn="pierce",
        spawnNote="관통 화살이 적을 꿰뚫는 순간 그 자리(적 히트박스와 화살 진행선의 만남)에 1회 — 진행 각도로 회전. 마지막(3번째) 적 이후 화살이 사라지면 기존 hit_bow 로 마무리",
        impactFrame=0, effectRule=EFFECT_RULE, r57=R57,
        frameRoles=["꿰뚫음(핵 백열 몇 도트)", "열린 고리 · 불티 앞으로", "퍼짐", "퍼짐", "파편", "재"],
        design="꿰뚫고 나감 — 진행선에 수직인 열린 고리(위·아래 호) + 앞으로 튀는 불티·파편(뒤로 튀지 않음 — 관통 방향 강조)", branch="저격(狙擊) 1단 B"))
    return T


ORDER = ["katana_spin", "katana_spin_ready", "katana_guardbreak"] + ["greatsword_shatter_crack_t%d" % n for n in SH_TILES] + ["greatsword_shatter_snuff", "greatsword_quake_ring",
         "dagger_fan_throw", "dagger_thrown", "dagger_cross_clone", "bow_arrow_pierce", "bow_arrow_pierce_hit"]


def job(name):
    T = spec_table()
    sp = T[name]
    if sp["kind"] == "clone":
        poses = clone_poses()
        frames = {d: cross_clone_frames(d, poses) for d in sp["dirs"]}
    else:
        frames = {d: sp["fn"](d) for d in sp["dirs"]}
    for d in sp["dirs"]:
        assert len(frames[d]) == len(sp["ms"]), (name, d, len(frames[d]))
    meta = {k: v for k, v in sp["meta"].items() if v is not None}
    if sp["kind"] == "pp":
        cut, pivot, origin = F.X.fit(frames, include_pivot=True)
        upd = common_pp(pivot, origin)
        if meta.get("anchor"):
            upd["anchor"] = meta["anchor"]
        upd.update(meta)
        upd.update(dirTransform="drawn4", directionNote="4행 = 몸 시트 행 순서(down, up, left, right) — 조준 0° 그림을 행 각도로 회전해 다시 래스터(left = 180°, §17)")
    else:
        if sp["kind"] == "stages" and name == "greatsword_quake_ring":
            pv = (CO[0], CO[1] + GROUND)
        else:
            pv = CO
        cut, pivot = _fit_at(frames, pv)
        upd = dict(pivot={"x": pivot[0], "y": pivot[1]})
        upd.update(meta)
        if sp["kind"] == "clone":
            upd.update(dirTransform="drawn4", directionNote="4행 = 주인공이 대상 적을 바라보는 방향(down, up, left, right)")
        elif sp["kind"] != "stages":
            upd.update(directionNote="1행 any — 방향 무관" + (" (rotate: 진행 각도로 회전)" if meta.get("rotate") else ""))
    if sp["kind"] in ("center", "arrow", "stages") and meta.get("loop"):
        pass
    sheet, j, _ = F.write(name, cut, sp["dirs"], sp["ms"], None, upd, sp["glow"], OUT_FX)
    if meta.get("loop"):
        j["loop"] = True
        with open(os.path.join(OUT_FX, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(j, f, ensure_ascii=False, indent=1)
    return name, j["frameWidth"], j["frameHeight"], j["colors"]


def _fit_at(frames, pv, margin=3, step=8):
    box = (pv[0], pv[1], pv[0] + 1, pv[1] + 1)
    for lst in frames.values():
        for im in lst:
            b = im.getbbox()
            if b:
                box = (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    x0, y0 = box[0] - margin, box[1] - margin
    Wd = -(-(box[2] + margin - x0) // step) * step
    Hd = -(-(box[3] + margin - y0) // step) * step
    out = {d: [im.crop((x0, y0, x0 + Wd, y0 + Hd)) for im in lst] for d, lst in frames.items()}
    return out, (pv[0] - x0, pv[1] - y0)


def build(only=None):
    from multiprocessing import Pool
    names = [n for n in ORDER if not only or n in only]
    with Pool(6) as p:
        res = p.map(job, names, chunksize=1)
    stats = {}
    for name, fw, fh, cols in res:
        print("%-28s %4dx%-4d colors %2d" % (name, fw, fh, cols))
        stats[name] = dict(frame=[fw, fh], colors=cols)
    p = os.path.join(HERE, "stats_fx.json")
    old = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    old.update(stats)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(old.items())), f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    build(set(sys.argv[1:]) or None)
