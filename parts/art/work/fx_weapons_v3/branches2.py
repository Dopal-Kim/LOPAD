"""2단 갈래 기본 공격 이펙트 v3.1 (55라운드 Q9 '2단 = 1단 모양 + 입자·빛·잔연, 크기 증가').

시트: fx/v3/<1단 시트>_<2단 id>  (예: katana_combo1_iai_wide · bow_arrow_snipe_lv3_deadeye)
틀: 1단 틀을 사방 32 도트(PAD2) 넓힘 — 근접은 frameWidth/Height +64, pivot +32 (판정 원점 = 피벗 위 40 도트 그대로).
프레임 수·ms·anchor·spawn·impact/hit/active/cancel·hitRadiusPx·arc·thrust = 1단(= 기본) 시트와 같다(판정 불변).
색은 재·호박 램프만, 백열 X0/X1·A26 은 판정 프레임만(빌드 clamp_cool). 1단 그림 함수를 그대로 쓰고 뒤(빛 번짐·잔상)와 앞(입자)을 더한다.

  칼  iai→wide 만월       = 빛살 묶음 +3줄·일섬 ×1.3 + 바깥 호를 감싼 호박 빛 번짐 띠 + 판정 바깥 R+14 에서 닫혀 가는 보름달 고리(닫히면 네 귀 글린트) + 바깥으로 튀는 불티
      iai→zangetsu 잔월   = 빛살 묶음(잔광 ×1.4 오래) + 바깥에 끝까지 남는 잿빛 초승달 그림자 + 피어오르는 재 연기 + 떨어지는 재 비늘
      batto→longinvuln 허보 = 반달 + 위아래로 어긋난 반달 허상 2(재 점선 윤곽) + 칼집 입 재 연기
      batto→dashcrit 급소 = 반달 + 칼집 입에서 판정 바깥까지 꿰뚫는 광선 7 + 현 가운데 급소 별(판정 백열 → 고리) + 바깥 빛 번짐 호 + 불티 소나기
  대검 crush→quake 지진   = 곤봉 호 + 균열 별 ×1.5 + 균열을 두르는 끊긴 고리 균열 + 앞 바닥에서 솟는 흙먼지 벽
      crush→pulverize 분쇄 = 곤봉 호 + 끝에서 부채꼴로 튀는 달군 돌 파편(호박) 다발 + 불티 줄기 + 흙 덩이
      weight→ironwall 철벽 = 눌린 부채 + 다각 테 꼭짓점마다 솟는 쇳빛 재 판석(호박 못) + 판석 뒤 재 연기
      weight→giant 거인   = 눌린 부채(테 ×1.4) + 판정 바깥으로 밀려나는 압력 고리 2겹 + 큰 흙먼지 + 불티
  단검 twin→dance 난무   = 교차 X + 엇갈린 두 번째 X(가는 호박) + 교차점 둘레 작은 베기 호 3 + 글린트 3 + 불티
      twin→bleed 출혈    = 교차 X + 교차점에서 튀어 떨어지는 핏빛(어두운 호박 A17~A19) 방울 + 바닥 핏자국
      gale→afterimage 잔상 = 회오리 꼬리 + 뒤로 밀린 재 바늘 허상 2(점선) + 재 비늘
      gale→assassin 암살  = 회오리 꼬리(진폭 ×1.3) + 어두운 그림자 나선 + 촉 큰 백열 글린트 + 뒤로 말리는 그림자 덩굴
활 2단은 bow_tiers.py (연궁·무한통·관통·필중).
"""
import math

import branches as B
import bow_tiers as BT
import common as C
import defs_dagger as DG
import parts as P
import swaps
import wkit as W
from wkit import FK

PAD = B.PAD2


def _design(sid):
    for l in __doc__.split("\n"):
        if ("→%s " % sid) in l:
            return l.strip()
    return BT.DESIGN2.get(sid, sid)


def tier2_extra(old, name1, sid, base_ex, frame_note):
    """2단 시트 JSON 추가 필드(시스템 연결 키)."""
    branch = old.get("branch") or ("rapid" if "rapid" in name1 else "snipe")
    sv = dict(swaps.SECONDARY[branch][sid])
    label = sv.pop("label", sid)
    sv.pop("colorSwap", None)
    note = sv.pop("note", None)
    if sid == "pierce":
        sv.pop("overlay", None)                 # 관통 꼬리 시트가 구 overlay(fx/pierce)를 대신한다
    ex = dict(base_ex)
    ex.update({
        "branch": branch, "branchLabel": old.get("branchLabel"), "branchTier": 2, "secondary": sid, "secondaryLabel": label,
        "baseSheet": old.get("baseSheet", "fx/" + name1),
        "tier1Sheet": "fx/%s" % name1,
        "replaces": "2단 갈래 '%s' 획득 시 fx/%s 대신 재생 — 프레임 수·ms·loop·anchor·spawn·impact/hit/active/cancel·판정 필드는 1단과 같다. %s"
                    % (label, name1, frame_note),
        "runtime": sv,
        "runtimeNote": "1단 secondaryVariants[%s] 의 colorSwap 은 이 시트에 이미 그려져 있으므로 적용하지 않는다. runtime 의 나머지"
                       "(overlay·flashOverride·holdLastFrameMs·shakeOverride·trailOverride·scaleHint)는 그대로 쓴다." % sid
                       + (" (구 메모: %s)" % note if note else ""),
        "tierDesign": _design(sid),
        "tierNote": "55라운드 Q9: 2단 = 1단 모양 + 입자·빛·잔연 + 큰 틀",
        "_drop": ["secondaryVariants", "secondaryNote"],
    })
    return ex


def _opts(name1, piv):
    return dict(old=name1, pivot=piv, tier2=True,
                legacyNote="2단 갈래 시트(55라운드) — 구 시트 없음. legacy 는 1단 구 시트(%s) 기준" % name1)


GROW = "틀은 1단보다 사방 %d 도트 넓다(frameWidth/Height +%d, pivot +%d) — JSON pivot 으로 맞출 것." % (PAD, 2 * PAD, PAD)


def _ctx(name1):
    old, size, piv, o = B.geo(name1, PAD)
    return old, size, piv, o, B.states(old)


def _compose(old, size, o, *draws):
    def draw(f, t, d, i, F):
        for g in draws:
            g(f, t, d, i, F)
    return C.frames(old, draw, size=size, origin=o)


def _out_embers(L, t, rng, n, R, a0, a1, age, sp=(20, 46), life_k=1.0, s_rng=(0.2, 1.0), v=1.0):
    """판정 가장자리에서 바깥으로 튀는 불티(로컬 → 화면)."""
    for m in range(n):
        s = rng.uniform(*s_rng)
        a = a0 + (a1 - a0) * s + rng.uniform(-0.05, 0.05)
        dist = R + rng.uniform(*sp) * (0.35 + age * life_k)
        p = t((math.cos(a) * dist, math.sin(a) * dist))
        vx, vy = DG._vec(t, a)
        W.ember(L, p[0], p[1] + 10 * age * age, vx, vy + 0.4 * age, rng.uniform(3, 7) * (1 - 0.5 * age),
                v=v * rng.uniform(0.6, 1.0) * (1 - 0.4 * age))


# ================================================================== 칼
def iai_wide(n):
    name1 = "katana_combo%d_iai" % n
    old, size, piv, o, st = _ctx(name1)
    R, a0, a1, sgn = B.arcinfo(old)
    fill, memo = C.trail_fill("katana_combo%d" % n, R)
    main = B.iai_main(old, n, fill, lines_extra=3, os_k=1.3)
    imp = old["impactFrame"]

    def behind(f, t, d, i, F):
        kind, k = st[i]
        if kind == "pre":
            return
        hot = kind == "hit"
        age = 0.0 if hot else k
        Lb = f.L([W.A17, W.A18, W.A19, W.A21])
        Lb.stroke(t.pts(W.arc_pts(R - 3, a0, a1)), 6.0 * (1 - 0.45 * age), prof=FK.tp_both(0.6, 0.72), v=0.95 - 0.45 * age)
        Lm = f.L(W.R_EDGE)
        prog = min(1.0, 0.5 + 0.9 * (i - imp) / max(1, F - 1 - imp))
        b = a0 + sgn * 2 * math.pi * prog
        Lm.stroke(t.pts(W.arc_pts(R + 14, a0, b)), 1.0, prof=FK.tp_head(0.3), v=(0.5 if hot else 0.46 - 0.18 * age),
                  dash=None if age < 0.6 else (16, 0.65, 0.0))
        if prog >= 1.0 and age < 0.95:
            Lg = f.L(W.R_HOT)
            for q in range(4):
                a = a0 + sgn * (math.pi / 4 + q * math.pi / 2)
                p = t((math.cos(a) * (R + 14), math.sin(a) * (R + 14)))
                P.glint(Lg, p[0], p[1], 8, v=0.6)

    def front(f, t, d, i, F):
        kind, k = st[i]
        if kind == "pre":
            return
        age = 0.0 if kind == "hit" else k
        _out_embers(f.L(W.R_EMBER), t, P.rng(1700 + n * 10 + i), 10 + int(6 * age), R, a0, a1, age, v=1.0 if age == 0 else 0.85)
    fr = _compose(old, size, o, behind, main, front)
    ex = dict(C.base_extra(old, "katana", C.bright_of(old)), trailFill=memo)
    ex["moonRing"] = {"radiusDots": R + 14, "note": "그림 메모 — 판정 바깥 R+14 의 보름달 고리(판정 아님)"}
    return fr, tier2_extra(old, name1, "wide", ex, GROW), _opts(name1, piv)


def iai_zangetsu(n):
    name1 = "katana_combo%d_iai" % n
    old, size, piv, o, st = _ctx(name1)
    R, a0, a1, sgn = B.arcinfo(old)
    fill, memo = C.trail_fill("katana_combo%d" % n, R)
    main = B.iai_main(old, n, fill, lines_extra=1, os_k=1.2, life_k=1.4)

    def behind(f, t, d, i, F):
        kind, k = st[i]
        if kind == "pre":
            return
        hot = kind == "hit"
        age = 0.0 if hot else k
        Lg = f.L([W.S0, W.S1, W.S2, W.S3])
        cut = 0.0 if hot else 0.35 * age

        def cb(x, y, s, dd, w):
            if s < cut:
                return
            if age > 0.6 and W.h2(int(s * 40), 0, 77) < (age - 0.6) * 1.6:
                return
            Lg.put(x, y, (1.0 - 0.45 * dd) * (0.7 + 0.3 * s) * (1 - 0.25 * age))
        W.crescent(f.w, f.h, t, R + 13, a0, a1, 9.0, FK.tp_both(0.6, 0.7), cb)
        Le = f.L([W.S2, W.S3])                    # 잿빛 초승달의 바깥 날 + 한 겹 더 바깥 메아리 점선
        Le.stroke(t.pts(W.arc_pts(R + 13, a0 + (a1 - a0) * cut, a1)), 0.8, prof=FK.tp_both(0.6, 0.7), v=0.95)
        Le.stroke(t.pts(W.arc_pts(R + 22, a0 + (a1 - a0) * (0.15 + cut), a1)), 0.6, prof=FK.tp_both(0.6, 0.7), v=0.8,
                  dash=(14, 0.6 - 0.25 * age, 0.0))
        Ls = f.L([W.S0, W.S1, W.S2])
        if not hot:                               # 피어오르는 재 연기
            rng = P.rng(1800 + n * 10 + i)
            for m in range(6):
                s = rng.uniform(0.2, 1.0)
                a = a0 + (a1 - a0) * s
                p = t((math.cos(a) * (R + 4), math.sin(a) * (R + 4)))
                W.puff(Ls, p[0], p[1] - 14 * age - 4 * m * age, 7 + 8 * age, v=0.9 - 0.35 * age, seed=m + i)

    def front(f, t, d, i, F):
        kind, k = st[i]
        if kind == "pre":
            return
        age = 0.0 if kind == "hit" else k
        Lf = f.L(W.R_ASHG)
        rng = P.rng(1900 + n * 10 + i)
        for m in range(10 + int(12 * age)):
            s = rng.uniform(0.1, 1.0)
            a = a0 + (a1 - a0) * s
            rr = R + rng.uniform(-30, 16)
            p = t((math.cos(a) * rr, math.sin(a) * rr))
            W.flake(Lf, p[0], p[1] + 16 * age * rng.uniform(0.5, 1.5), rng.uniform(1.2, 2.4), rng.uniform(0, 6), v=rng.uniform(0.55, 1.0))
    fr = _compose(old, size, o, behind, main, front)
    ex = dict(C.base_extra(old, "katana", C.bright_of(old)), trailFill=memo)
    return fr, tier2_extra(old, name1, "zangetsu", ex, GROW), _opts(name1, piv)


def _half_moon_outline(L, t, R, a0, a1, mid, c, off, v, dash):
    cm, sm = math.cos(mid), math.sin(mid)
    half = math.acos(max(-1.0, min(1.0, c / R)))
    pts = W.arc_pts(R, mid - half, mid + half)
    p0 = (math.cos(mid - half) * R, math.sin(mid - half) * R)
    pts = pts + [p0]
    pts = [(p[0] + off[0], p[1] + off[1]) for p in pts]
    L.stroke(t.pts(pts), 0.7, v=v, dash=dash)


def batto_longinvuln(n):
    name1 = "katana_combo%d_batto" % n
    old, size, piv, o, st = _ctx(name1)
    R, a0, a1, sgn, mid, c = B.batto_geom(old)
    main = B.batto_main(old, n)
    cm, sm = math.cos(mid), math.sin(mid)

    def behind(f, t, d, i, F):
        kind, k = st[i]
        if kind == "pre":
            return
        hot = kind == "hit"
        age = 0.0 if hot else k
        Lg = f.L([W.S1, W.S2, W.S3])
        La = f.L([W.A18, W.A19, W.A21])
        for j, s in enumerate((-1, 1)):
            sh = 30 + 12 * age
            off = (-sm * s * sh + cm * (14 + 10 * j), cm * s * sh + sm * (14 + 10 * j))
            _half_moon_outline(Lg, t, R * 0.94, a0, a1, mid, c * 0.94, off, 1.0 - 0.35 * age, (8, 0.7 - 0.25 * age, 0.2 * j))
            _half_moon_outline(La, t, R * 0.9, a0, a1, mid, c * 0.9, off, 0.7 - 0.3 * age, (8, 0.35, 0.5 + 0.2 * j))
        Ls = f.L([W.S0, W.S1, W.S2])
        rng = P.rng(2100 + n)
        for m in range(4):                        # 칼집 입 재 연기
            p = t((B.HIP[0] - 6 - rng.uniform(0, 12), B.HIP[1] + rng.uniform(-6, 6)))
            W.puff(Ls, p[0] - 6 * age * m, p[1] - 10 * age, 5 + 4 * age + m, v=0.8 - 0.3 * age, seed=m)
    fr = _compose(old, size, o, behind, main)
    ex = C.base_extra(old, "katana", C.bright_of(old))
    return fr, tier2_extra(old, name1, "longinvuln", ex, GROW), _opts(name1, piv)


def batto_dashcrit(n):
    name1 = "katana_combo%d_batto" % n
    old, size, piv, o, st = _ctx(name1)
    R, a0, a1, sgn, mid, c = B.batto_geom(old)
    main = B.batto_main(old, n)
    cm, sm = math.cos(mid), math.sin(mid)
    star = ((c + (R - c) * 0.42) * cm, (c + (R - c) * 0.42) * sm)

    def behind(f, t, d, i, F):
        kind, k = st[i]
        if kind == "pre":
            return
        age = 0.0 if kind == "hit" else k
        Lb = f.L([W.A17, W.A18, W.A19])
        Lb.stroke(t.pts(W.arc_pts(R + 9, a0 + (a1 - a0) * 0.05, a1 - (a1 - a0) * 0.05)), 4.0 * (1 - 0.5 * age),
                  prof=FK.tp_both(0.6, 0.6), v=0.9 - 0.4 * age)

    def front(f, t, d, i, F):
        kind, k = st[i]
        Lh = f.L(W.R_HOT)
        Lc = f.L(W.R_EDGE)
        if kind == "pre":
            return
        hot = kind == "hit"
        age = 0.0 if hot else k
        for j in range(7):                        # 칼집 입에서 판정 바깥까지 꿰뚫는 광선
            a = mid + (j - 3) * 0.19
            ln = (R + 22 - B.HIP[0]) * (1.0 if hot else 1.0 + 0.1 * age)
            q0 = (B.HIP[0] + math.cos(a) * (c * 0.6 + 50 * age), B.HIP[1] + math.sin(a) * (c * 0.6 + 50 * age))
            q1 = (B.HIP[0] + math.cos(a) * ln, B.HIP[1] + math.sin(a) * ln)
            (Lh if hot else Lc).stroke(t.pts([q0, q1]), 0.9 if j == 3 else 0.6, prof=FK.tp_both(0.7, 0.75),
                                       v=(0.95 if j % 2 == 1 else 0.8) if hot else 0.55 - 0.3 * age)
        p = t(star)
        if hot:
            P.glint(Lh, p[0], p[1], 20, v=1.0, diag=0.6, w=1.2)
        elif age < 0.95:
            Lc.ring(p[0], p[1], 8 + 26 * age, 1.1 * (1 - 0.4 * age), v=0.6 - 0.25 * age, dash=(10, 0.6, 0.0) if age > 0.4 else None)
        _out_embers(f.L(W.R_EMBER), t, P.rng(2200 + n * 10 + i), 14, R, a0 + (a1 - a0) * 0.1, a1 - (a1 - a0) * 0.1, age, sp=(18, 50))
    fr = _compose(old, size, o, behind, main, front)
    ex = C.base_extra(old, "katana", C.bright_of(old))
    ex["critStarLocalDots"] = [round(star[0], 1), round(star[1], 1)]
    return fr, tier2_extra(old, name1, "dashcrit", ex, GROW), _opts(name1, piv)


# ================================================================== 대검
def _crush_base(n, size, o, old, scale=1.0):
    import swing
    R, a0, a1, sgn = B.arcinfo(old)
    fill, memo = C.trail_fill("greatsword_combo%d" % n, R)
    fr = swing.swing_frames("gs", size, o, R, old["arcFromDeg"], old["arcToDeg"], old["frames"], old["impactFrame"],
                            bright=C.bright_of(old), wmax=B.GW[n] * 1.15 * scale, seed=600 + n, dust=3, gaps=B.CRUSH_GAPS,
                            fill_to=fill, prof_fn=B.club)
    return fr, memo


def crush_quake(n):
    name1 = "greatsword_combo%d_crush" % n
    old, size, piv, o, st = _ctx(name1)
    R, a0, a1, sgn = B.arcinfo(old)
    base, memo = _crush_base(n, size, o, old)
    cracks = B.crush_cracks(old, n, scale=1.5, seed=5)
    imp = old["impactFrame"]

    def ring(f, t, d, i, F):
        kind, k = st[i]
        if kind == "pre":
            return
        age = 0.0 if kind == "hit" else k
        Lc = f.L(W.R_EDGE)
        Ld = f.L(W.R_DUST)
        c = t(B.crack_pt(R))
        c = (c[0], c[1] + W.HIT_UP)
        grow = min(1.0, 0.6 + 0.5 * (i - imp))
        rr = 96 * grow
        rng = P.rng(2400 + n)
        a = 0.0
        while a < 2 * math.pi:                    # 끊긴 고리 균열(조각마다 굵기·끊김 제각각)
            da = rng.uniform(0.35, 0.7)
            if rng.random() > 0.25:
                pts = [(c[0] + math.cos(a + da * u / 6) * rr * (1 + rng.uniform(-0.04, 0.04)),
                        c[1] + math.sin(a + da * u / 6) * rr * P.KY * (1 + rng.uniform(-0.04, 0.04))) for u in range(7)]
                Lc.stroke(pts, 1.2 if age < 0.5 else 0.8, prof=FK.tp_both(0.6, 0.5), v=(0.95 if age == 0 else 0.58 - 0.2 * age))
            a += da + rng.uniform(0.08, 0.2)
        if age > 0:                               # 앞 바닥에서 솟는 흙먼지 벽
            rngd = P.rng(2450 + n)
            for m in range(9):
                aa = -math.pi + m * math.pi / 8 + rngd.uniform(-0.1, 0.1)
                p = (c[0] + math.cos(aa) * rr * 1.05, c[1] + math.sin(aa) * rr * P.KY)
                W.puff(Ld, p[0], p[1] - 12 * age - rngd.uniform(0, 8), 7 + 8 * age, v=0.85 - 0.35 * age, seed=m)
    top = C.frames(old, lambda f, t, d, i, F: (ring(f, t, d, i, F), cracks(f, t, d, i, F)), size=size, origin=o)
    ex = dict(C.base_extra(old, "greatsword", C.bright_of(old)), trailFill=memo)
    return B.over(base, top), tier2_extra(old, name1, "quake", ex, GROW), _opts(name1, piv)


def crush_pulverize(n):
    name1 = "greatsword_combo%d_crush" % n
    old, size, piv, o, st = _ctx(name1)
    R, a0, a1, sgn = B.arcinfo(old)
    base, memo = _crush_base(n, size, o, old)
    cracks = B.crush_cracks(old, n, scale=1.15, seed=9)

    def spray(f, t, d, i, F):
        kind, k = st[i]
        if kind == "pre":
            return
        hot = kind == "hit"
        age = 0.0 if hot else k
        Lh = f.L([W.A19, W.A21, W.A23, W.A25])
        Lr = f.L(W.R_ASHB)
        Le = f.L(W.R_EMBER)
        rng = P.rng(2500 + n)
        for m in range(34):                       # 곤봉 끝에서 부채꼴로 튀는 달군 돌 파편
            s = rng.uniform(0.6, 1.0)
            a = a0 + (a1 - a0) * s + rng.uniform(-0.25, 0.25)
            sp = rng.uniform(26, 62)
            tt = 0.35 + age * 1.3
            dist = R - 10 + sp * tt
            p = t((math.cos(a) * dist, math.sin(a) * dist))
            y = p[1] + 14 * tt * tt
            hotm = m % 3 != 0
            if p[0] < 8 or y < 8 or p[0] > f.w - 8 or y > f.h - 8:
                continue
            W.flake(Lh if hotm else Lr, p[0], y, rng.uniform(4.5, 7.5) * (1 - 0.3 * age), rng.uniform(0, 6) + tt,
                    v=(0.95 - 0.4 * age) if hotm else 0.95)
            if hotm and age < 0.7:
                vx, vy = DG._vec(t, a)
                W.ember(Le, p[0], y, vx, vy, 6 * (1 - age), v=0.85)
    top = C.frames(old, lambda f, t, d, i, F: (cracks(f, t, d, i, F), spray(f, t, d, i, F)), size=size, origin=o)
    ex = dict(C.base_extra(old, "greatsword", C.bright_of(old)), trailFill=memo)
    return B.over(base, top), tier2_extra(old, name1, "pulverize", ex, GROW), _opts(name1, piv)


def weight_ironwall(n):
    name1 = "greatsword_combo%d_weight" % n
    old, size, piv, o, st = _ctx(name1)
    R, a0, a1, sgn = B.arcinfo(old)
    main = B.weight_main(old, n, rim_k=1.2)
    nf = B.FACETS[n]

    def slabs(f, t, d, i, F):
        kind, k = st[i]
        if kind == "pre":
            return
        hot = kind == "hit"
        age = 0.0 if hot else k
        Li = f.L([W.B1, W.S1, W.S2])
        Lt = f.L([W.S1, W.S2])
        Lr = f.L(W.R_EDGE)
        Ls = f.L([W.B1, W.S1, W.S2])
        rise = min(1.0, 0.55 + 0.6 * (i - old["impactFrame"]))
        if age > 0.85:
            return
        verts = []
        for m in range(nf + 1):
            a = a0 + (a1 - a0) * (0.02 + 0.96 * m / nf)
            verts.append(t((math.cos(a) * (R - 5), math.sin(a) * (R - 5))))
        hb = 14 * rise * (1 - 0.3 * age)               # 판석 사이 낮은 쇳빛 담(테를 따라)
        for (x0, y0), (x1, y1) in zip(verts, verts[1:]):
            L = max(1, int(math.hypot(x1 - x0, y1 - y0)))
            for u in range(L + 1):
                x, y = x0 + (x1 - x0) * u / L, y0 + (y1 - y0) * u / L
                for yy in range(int(hb)):
                    Li.put(x, y - yy, (0.45 + 0.35 * (yy / max(1, hb))) * (1 - 0.3 * age))
                Lt.put(x, y - hb, 0.95)
        for m, b in enumerate(verts):                  # 꼭짓점마다 솟는 쇳빛 재 판석
            h = (44 + 10 * (m % 2)) * rise * (1 - 0.25 * age)
            w = 9
            for yy in range(int(h)):
                for xx in range(-w, w + 1):
                    q = abs(xx) / w
                    Li.put(b[0] + xx, b[1] - yy, (0.55 + 0.4 * (1 - q) - 0.35 * (xx > 4)) * (1 - 0.3 * age))
            Lt.stroke([(b[0] - w, b[1] - h), (b[0] + w, b[1] - h)], 1.0, v=0.95)
            Lt.stroke([(b[0] - w + 1, b[1] - h + 2), (b[0] - w + 1, b[1] - 3)], 0.5, v=0.7)
            for ry in (0.35, 0.7):                     # 호박 못
                Lr.stamp(b[0], b[1] - h * ry, 1.3, 0.6 if hot else 0.5 - 0.2 * age, soft=0)
            if not hot:
                W.puff(Ls, b[0] + 3, b[1] - h - 8 - 12 * age, 6 + 6 * age, v=0.75 - 0.3 * age, seed=m)
    fr = _compose(old, size, o, main, slabs)
    ex = C.base_extra(old, "greatsword", C.bright_of(old))
    return fr, tier2_extra(old, name1, "ironwall", ex, GROW), _opts(name1, piv)


def weight_giant(n):
    name1 = "greatsword_combo%d_weight" % n
    old, size, piv, o, st = _ctx(name1)
    R, a0, a1, sgn = B.arcinfo(old)
    main = B.weight_main(old, n, rim_k=1.4, ridge_k=1.2)

    def rings(f, t, d, i, F):
        kind, k = st[i]
        if kind == "pre":
            return
        hot = kind == "hit"
        age = 0.0 if hot else k
        Lb = f.L(W.R_RUST)
        Lc = f.L(W.R_EDGE)
        for j in range(2):                        # 판정 바깥으로 밀려나는 압력 고리 2겹
            rr = R + 8 + 12 * j + 10 * age
            if rr > min(f.w, f.h) / 2 - 10 + 32:
                continue
            Lb.stroke(t.pts(W.arc_pts(rr, a0 + 0.08, a1 - 0.08)), 3.0 - j, prof=FK.tp_both(0.6, 0.6), v=0.85 - 0.25 * j - 0.3 * age,
                      dash=None if age < 0.5 else (22, 0.7, 0.1 * j))
            Lc.stroke(t.pts(W.arc_pts(rr - 2, a0 + 0.14, a1 - 0.14)), 0.6, prof=FK.tp_both(0.6, 0.6), v=0.42 - 0.15 * age)
        Ld = f.L(W.R_DUST)
        rng = P.rng(2600 + n + i)
        if not hot:
            for m in range(7):
                s = rng.uniform(0.05, 1.0)
                a = a0 + (a1 - a0) * s
                p = t((math.cos(a) * (R + 6), math.sin(a) * (R + 6)))
                W.puff(Ld, p[0], p[1] + 8 * age, 10 + 8 * age, v=0.8 - 0.3 * age, seed=m)
        _out_embers(f.L(W.R_EMBER), t, P.rng(2650 + n * 10 + i), 8, R, a0, a1, age, sp=(10, 30))
    fr = _compose(old, size, o, main, rings)
    ex = C.base_extra(old, "greatsword", C.bright_of(old))
    return fr, tier2_extra(old, name1, "giant", ex, GROW), _opts(name1, piv)


# ================================================================== 단검
def twin_dance(n):
    name1 = "dagger_combo%d_twin" % n
    old, size, piv, o, st = _ctx(name1)
    lines, C_, ang, x1 = B.twin_geom(old, n)
    main = B.twin_main(old, n)
    dst = DG._states(old["frames"], old["impactFrame"])

    def extra(f, t, d, i, F):
        kind, k = dst[i]
        if kind == "pre":
            return
        hot = kind == "hit"
        Lc = f.L(W.R_EDGE)
        Lh = f.L(W.R_HOT)
        ca, sa = math.cos(ang + 0.5), math.sin(ang + 0.5)
        cb, sb = math.cos(ang - 0.5), math.sin(ang - 0.5)
        L2 = 46 * (1 if hot else 1 - 0.3 * k)
        for (cx, sx) in ((ca, sa), (cb, sb)):     # 엇갈린 두 번째 X(가는 호박)
            p0 = (C_[0] - cx * L2, C_[1] - sx * L2)
            p1 = (C_[0] + cx * L2, C_[1] + sx * L2)
            Lc.stroke(t.pts([p0, p1]), 1.1, prof=FK.tp_both(0.7, 0.5), v=(0.85 if hot else 0.55 - 0.3 * k),
                      dash=None if k < 0.5 else (8, 0.6, 0.0))
        rng = P.rng(3000 + n)
        for m in range(3):                        # 교차점 둘레 작은 베기 호
            a0 = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(16, 24)
            c = t(C_)
            Lc.arc(c[0], c[1], r, r, a0, a0 + 1.4, 0.9, prof=FK.tp_both(0.7, 0.6), v=(0.8 if hot else 0.5 - 0.3 * k))
            if hot:
                g = (c[0] + math.cos(a0 + 0.7) * r, c[1] + math.sin(a0 + 0.7) * r)
                P.glint(Lh, g[0], g[1], 6, v=0.95)
        c = t(C_)
        P.scatter_embers(f.L(W.R_EMBER), c, P.rng(3100 + i), 6, 10, 36 + 20 * k, v=(0.6, 1.0) if hot else (0.4, 0.75))
    fr = _compose(old, size, o, main, extra)
    ex = C.base_extra(old, "dagger", C.bright_of(old))
    return fr, tier2_extra(old, name1, "dance", ex, GROW), _opts(name1, piv)


def twin_bleed(n):
    name1 = "dagger_combo%d_twin" % n
    old, size, piv, o, st = _ctx(name1)
    lines, C_, ang, x1 = B.twin_geom(old, n)
    main = B.twin_main(old, n)
    dst = DG._states(old["frames"], old["impactFrame"])

    def blood(f, t, d, i, F):
        kind, k = dst[i]
        if kind == "pre":
            return
        hot = kind == "hit"
        Lb = f.L([W.A17, W.A18, W.A19, W.A21])
        Lp = f.L([W.A17, W.A18])
        c = t(C_)
        rng = P.rng(3200 + n)
        tt = 0.4 if hot else 0.4 + 1.6 * k
        if hot or k < 0.5:                        # 교차점에서 앞으로 뿜는 핏줄기 두 갈래
            for s_ in (-1, 1):
                a = t.ang(ang + s_ * 0.45)
                L_ = 30 + 26 * k
                Lb.stroke([c, (c[0] + math.cos(a) * L_, c[1] + math.sin(a) * L_ + 8 * k)], 2.6 * (1 - 0.5 * k),
                          prof=FK.tp_tail(0.6), v=0.95 - 0.3 * k, dash=None if hot else (9, 0.6, 0.0))
        for m in range(16):                       # 튀어 떨어지는 핏빛 방울
            a = t.ang(ang) + rng.uniform(-1.3, 1.3)
            sp = rng.uniform(16, 34)
            x = c[0] + math.cos(a) * sp * tt
            y = c[1] + math.sin(a) * sp * tt * 0.7 + 18 * tt * tt - 6 * tt
            r = rng.uniform(2.2, 3.6) * (1 - 0.2 * k)
            if not (10 < x < f.w - 10 and 10 < y < f.h - 10):
                continue
            Lb.stroke([(x - math.cos(a) * 4, y - 3), (x, y)], r, prof=FK.tp_head(0.7), v=0.95)
        if not hot:                               # 바닥 핏자국(발 높이)
            fy = c[1] + W.HIT_UP - 4
            for m in range(3):
                Lp.disc(c[0] + (m - 1) * 14 + rng.uniform(-3, 3), fy + rng.uniform(-2, 2), (5 + 3 * m % 2) * min(1, 0.4 + k), 2 * min(1, 0.4 + k),
                        v=0.8, edge=0.6)
    fr = _compose(old, size, o, main, blood)
    ex = C.base_extra(old, "dagger", C.bright_of(old))
    return fr, tier2_extra(old, name1, "bleed", ex, GROW), _opts(name1, piv)


def gale_afterimage(n):
    name1 = "dagger_combo%d_gale" % n
    old, size, piv, o, st = _ctx(name1)
    ang, x0, x1, A0 = B.gale_geom(old, n)
    main = B.gale_main(old, n)
    dst = DG._states(old["frames"], old["impactFrame"])
    ca, sa = math.cos(ang), math.sin(ang)

    def ghosts(f, t, d, i, F):
        kind, k = dst[i]
        if kind == "pre":
            return
        hot = kind == "hit"
        Lg = f.L([W.S1, W.S2, W.S3])
        La = f.L([W.A19, W.A21, W.A23])
        for j, (back, side) in enumerate(((14, 16), (30, -16), (44, 2))):
            sh = back + 10 * k
            off = (-ca * sh - sa * side, -sa * sh + ca * side)
            p0 = (ca * x0 + off[0], sa * x0 + off[1])
            p1 = (ca * x1 + off[0], sa * x1 + off[1])
            Lg.stroke(t.pts([p0, p1]), 2.8 - 0.5 * j, prof=FK.tp_both(0.75, 0.7), v=1.0 - 0.2 * j - 0.3 * k,
                      dash=None if hot else (10, 0.7 - 0.25 * k, 0.3 * j))
            La.stroke(t.pts([p0, p1]), 0.7, prof=FK.tp_both(0.75, 0.8), v=0.9 - 0.15 * j - 0.4 * k, dash=None if hot else (7, 0.5, 0.2 * j))
        if not hot:
            P.scatter_flakes(f.L(W.R_ASHG), t((x1 * 0.4, 0)), P.rng(3300 + i), 8, 6, 44, fall=10 * k)
    fr = _compose(old, size, o, ghosts, main)
    ex = C.base_extra(old, "dagger", C.bright_of(old))
    return fr, tier2_extra(old, name1, "afterimage", ex, GROW), _opts(name1, piv)


def gale_assassin(n):
    name1 = "dagger_combo%d_gale" % n
    old, size, piv, o, st = _ctx(name1)
    ang, x0, x1, A0 = B.gale_geom(old, n)
    main = B.gale_main(old, n, amp_k=1.45)
    dst = DG._states(old["frames"], old["impactFrame"])
    ca, sa = math.cos(ang), math.sin(ang)

    def P_(u, v):
        return (ca * u - sa * v, sa * u + ca * v)

    def shadow(f, t, d, i, F):
        kind, k = dst[i]
        if kind == "pre":
            return
        hot = kind == "hit"
        Ld = f.L([W.B0, W.B1, W.B2])
        A = A0 * 1.55
        pts = []
        for m in range(70):                       # 어두운 그림자 나선(굵음)
            q = m / 69
            u = 2 + (x1 * 0.8 - 2) * q + 10 * k
            pts.append(P_(u, A * (1 - q) ** 1.2 * math.sin(2 * math.pi * 1.6 * q + i * 1.1 + math.pi / 2)))
        Ld.stroke(t.pts(pts), 3.4 * (1 - 0.4 * k), prof=FK.tp_tail(0.6), v=0.95 - 0.3 * k, dash=None if k < 0.5 else (12, 0.6, 0.0))
        Lrim = f.L([W.S2, W.S3])                   # 그림자 나선 윗면 재빛 테(어둠에 묻히지 않게)
        Lrim.stroke(t.pts([(p[0], p[1] - 2.6) for p in pts]), 0.6, prof=FK.tp_tail(0.6), v=0.95 - 0.3 * k,
                    dash=None if k < 0.5 else (12, 0.6, 0.0))
        for s in (-1, 1):                         # 뒤로 말리는 그림자 덩굴
            p0 = P_(10, s * A * 0.6)
            p1 = P_(-12 - 12 * k, s * (A * 1.1))
            p2 = P_(-26 - 16 * k, s * A * 0.5)
            Ld.curve(t(p0), t(p1), t(p2), 1.4, prof=FK.tp_tail(0.7), v=0.85 - 0.3 * k)

    def tip(f, t, d, i, F):
        kind, k = dst[i]
        if kind != "hit":
            return
        p = t(P_(x1 - 2, 0))
        P.glint(f.L(W.R_HOT), p[0], p[1], 18, v=1.0, diag=0.5, w=1.1)
    fr = _compose(old, size, o, shadow, main, tip)
    ex = C.base_extra(old, "dagger", C.bright_of(old))
    return fr, tier2_extra(old, name1, "assassin", ex, GROW), _opts(name1, piv)


# ================================================================== 활 2단 (bow_tiers 그림 + 같은 JSON 규약)
def bow2(name1, sid):
    fr, old, piv = BT.TIER2[(name1, sid)]()
    ex = C.base_extra(old, "bow", set())
    note = "틀이 1단보다 넓다(왼쪽·위아래로 넓힘, 촉 쪽 기준 그대로) — JSON frameWidth/Height·pivot 을 읽을 것."
    ex = tier2_extra(old, name1, sid, ex, note)
    if "tailSheets" in old:
        ex["tailSheets"] = ["fx/bow_arrow_snipe_lv%d_%s" % (lv, sid) for lv in (1, 2, 3)]
    if "attachTo" in old:
        ex["attachTo"] = ["fx/bow_arrow_snipe_%s" % sid, "fx/bow_arrow_aimed_snipe_%s" % sid]
    return fr, ex, _opts(name1, piv)


MELEE = {
    ("katana", "iai"): {"wide": iai_wide, "zangetsu": iai_zangetsu},
    ("katana", "batto"): {"longinvuln": batto_longinvuln, "dashcrit": batto_dashcrit},
    ("greatsword", "crush"): {"quake": crush_quake, "pulverize": crush_pulverize},
    ("greatsword", "weight"): {"ironwall": weight_ironwall, "giant": weight_giant},
    ("dagger", "twin"): {"dance": twin_dance, "bleed": twin_bleed},
    ("dagger", "gale"): {"afterimage": gale_afterimage, "assassin": gale_assassin},
}

SHEETS = {}
for (_w, _b), _d in MELEE.items():
    for _sid, _fn in _d.items():
        for _n in (1, 2, 3):
            SHEETS["%s_combo%d_%s_%s" % (_w, _n, _b, _sid)] = (lambda fn, n: lambda: fn(n))(_fn, _n)
for (_n1, _sid) in BT.TIER2:
    SHEETS["%s_%s" % (_n1, _sid)] = (lambda a, b: lambda: bow2(a, b))(_n1, _sid)
NAMES = set(SHEETS)
