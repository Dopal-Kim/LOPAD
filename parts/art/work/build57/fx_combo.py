"""1단 갈래 '연격 한 타 변화' fx (설계안 2.2~2.5 각 1단 연격 변화 · 6.2 '1단 연격 변화 fx').

  katana_fall_wide          칼 선풍 1단 — 2타 내려베기 호 110°→180° 넓은 붓획 + 안쪽 바람 획(katana_fall 과 같은 프레임·ms, 1:1 교체)
  status_stagger            경직 표시(공용) — 칼 투구가르기 1단 1타 올려베기 적중 경직 0.2초 · 대검 중압 1단 수평 베기 경직 0.25초
  greatsword_cleave_crack   대검 파쇄 1단 — 4타(V 내려찍기) 끝 짧은 균열 2칸
  dagger_combo3_double      단검 쌍격 1단 — 3타가 2연 찌르기(dagger_combo3 대신)
  dagger_gale_wind          단검 질풍 1단 — 이동 잔상(재 실루엣 + 바람 획), 이동 중 일정 간격으로 찍음
  aim_charge_quick          활 속사 1단 — 좌클릭 충전 시간 −30% 표시(aim_charge 와 같은 규격, 진행도 구동)
  bow_snipe_full            활 저격 1단 — 가득 당김(+0.1초) 완벽 놓기 창이 열린 순간 화살촉 반짝임
"""
import math
import random

import kit as K
from PIL import Image
from kit import W, FK, BR, F

SRC = "parts/art/work/build57/build.py combo (57라운드 1단 연격 변화 fx)"


def st_draw(S, fr, state, st=None, Lf=None, Lb=None, Lh=None, Le=None, seed=0, prev_tail=0.0, i=0):
    """붓획 한 개를 상태로 그림. state = ('pre', head) | ('draw', head) | ('decay', k)."""
    st = st or F.STYLE["katana"]
    Lf = Lf or fr.L(st["flake"])
    Lb = Lb or fr.L(st["ink"])
    Le = Le or fr.L(K.EMB)
    Lh = Lh or fr.L(K.HOT)
    kind = state[0]
    if kind == "pre":
        S.draw(Lb, head=state[1], vmax=0.6, drops=False)
    elif kind == "draw":
        S.draw(Lb, head=state[1], vmax=st["vmax"], hot=True, Lhot=Lh)
        if state[1] >= 0.999:
            F._embers(Le, S, seed, 0)
    elif kind == "decay":
        k = state[1]
        tail = 0.12 + 0.62 * k
        S.draw(Lb, head=1.0, tail=tail, vmax=st["vmax"] * (0.9 - 0.2 * k), wk=1 - 0.28 * k, k=k, fall=3 + 9 * k)
        S.flakes(Lf, k, 0.0, tail + 0.08, st["flakes"], size=st["flake_size"], fall=10.0, seed=i)
        if k < 0.5:
            F._embers(Le, S, seed, 1)
    return Lf, Lb, Lh, Le


# =============================================================================
# 칼 선풍 — 2타 넓은 호
# =============================================================================
FALLW_MS = [50, 25, 30, 60, 70, 80]          # katana_fall fx 와 같음
FALLW_A = (-100.0, 80.0)                      # 180° (katana_fall −70°→+40° 110° 대체)
FALLW_R = 152.0


def fall_wide(d, seed=5701):
    t = K.TA(d)
    st = F.STYLE["katana"]
    pts = BR.arc_points(t, FALLW_R - 9 * 0.45, FALLW_A[0], FALLW_A[1], lambda s: 41 + (2 - 41) * s)
    S = BR.Stroke(pts, 10.0, seed=seed, split=st["split"], drops=st["drops"], dry_from=st["dry"])
    wp = BR.arc_points(t, FALLW_R * 0.66, FALLW_A[0] + 30, FALLW_A[1] - 10, lambda s: 30 - 26 * s)
    Wd = BR.Stroke(wp, 3.2, seed=seed + 3, peak=0.5, dry_from=0.5, split=1.6, drops=2, start_w=0.15, end_w=0.3, lanes=4)

    def extra(fr, i, kind, p):
        Lw = fr.L([W.A17, W.A18, W.A19])
        if kind == "draw" and p["head"] >= 0.999:
            Wd.draw(Lw, head=1.0, vmax=0.7, drops=False)
        elif kind == "decay" and p["k"] < 0.5:
            Wd.draw(Lw, head=1.0, tail=0.5, vmax=0.5, k=p["k"], drops=False)
    return F._stroke_frames(S, st, F.PLAN_ARC, seed, extra=extra)


# =============================================================================
# 경직 표시(공용)
# =============================================================================
STAG_MS = [30, 40, 60, 60, 70]


def stagger(seed=5711):
    out = []
    cx, cy = 80, 100
    r = random.Random(seed)
    ticks = [(-140, 10), (-95, 14), (-52, 11), (-20, 7), (-165, 7)]
    for i in range(len(STAG_MS)):
        fr = K.frame(160, 160)
        Lg = fr.L([K.B1, K.B2, K.S1])
        Lc = fr.L([K.A19, K.A21, K.A23, K.A25])
        Lf = fr.L(K.FLAKE)
        grow = [0.55, 1.0, 0.95, 1.0, 0.7][i]
        jit = [0, 0, 1, -1, 0][i]
        for j, (a, ln) in enumerate(ticks):
            aa = math.radians(a + jit * (4 if j % 2 else -4))
            r0 = 7 + (1 if i >= 2 else 0)
            p0 = (cx + math.cos(aa) * r0, cy + math.sin(aa) * r0)
            p1 = (cx + math.cos(aa) * (r0 + ln * grow), cy + math.sin(aa) * (r0 + ln * grow))
            rr = random.Random(seed + j)
            pts = W.jag(rr, p0, p1, n=3, amp=1.6)
            Lg.stroke(pts, 1.7, prof=FK.tp_tail(0.7), v=0.9)
            v = [0.85, 1.0, 0.8, 0.88, 0.55][i]
            Lc.stroke(pts, 0.85, prof=FK.tp_tail(0.7), v=v)
        if i >= 3:
            for j in range(4):
                a = r.uniform(-3.0, -0.2)
                W.flake(Lf, cx + math.cos(a) * (16 + 4 * i), cy + math.sin(a) * (14 + 3 * i) + 3 * (i - 3), 1.3, a, v=0.8)
        out.append(fr.render())
    return out


# =============================================================================
# 대검 파쇄 — 4타 끝 짧은 균열
# =============================================================================
CC_MS = [30, 30, 30, 50, 70, 90, 110, 130]
CC_L = 2 * K.TILE
CC_FRONT = [48, 96, 128]


def cleave_crack(seed=5721):
    t = K.TA("right", K.CO)
    ox, oy = K.CO
    C = K.Crack(0.0, CC_L, seed, amp=2.6, branches=4, width=1.5)
    r = random.Random(seed)
    st_pts = [(r.uniform(8, CC_L - 6), r.uniform(-10, 10)) for _ in range(7)]
    born = [min(2, int(p[0] / 48)) for p in st_pts]
    out = []
    for i in range(len(CC_MS)):
        fr = K.frame()
        G = K.ground_layers(fr)
        k = 0.0 if i <= 3 else (i - 3) / 4
        front = CC_FRONT[i] if i < 3 else None
        C.draw(G["gr"], G["crk"], t, front=front, k=k)
        K.stones(G["flake"], t, st_pts, i, born, seed)
        if i <= 2:
            fx, fy = t((CC_FRONT[i], 0))
            G["dust"].cloud(fx, fy - 3, 6 + i, v=0.6, flat=0.55, seed=i)
            rr = random.Random(seed + i)
            for j in range(3):
                a = rr.uniform(-2.6, -0.5)
                W.ember(G["emb"], fx + math.cos(a) * 6, fy + math.sin(a) * 6, math.cos(a), math.sin(a), 3.0, w=0.6, v=0.85)
        if i == 0:
            G["dust"].cloud(ox + 4, oy - 4, 9, v=0.65, flat=0.5, seed=7)
        out.append(fr.render())
    return out


# =============================================================================
# 단검 쌍격 — 3타 2연 찌르기
# =============================================================================
DD_MS = [40, 40, 30, 40, 50, 60, 90]
DD_GLOW = [1, 3]


def _thrust(t, ang, x0, x1, wmax, bend, seed):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for i in range(41):
        u = i / 40
        along = x0 + (x1 - x0) * u
        lat = bend * math.sin(math.pi * u) * (1 - 0.3 * u)
        pts.append(t((ca * along - sa * lat, sa * along + ca * lat - 2)))
    return BR.Stroke(pts, wmax, seed=seed, peak=0.5, dry_from=0.7, split=1.0, drops=5, start_w=0.12, end_w=0.5)


def dagger_double(d, seed=5731):
    t = K.TA(d)
    S1 = _thrust(t, -7, 14, 156, 8.5, 3.0, seed)
    S2 = _thrust(t, 7, 14, 170, 10.0, -3.0, seed + 7)
    st = dict(F.STYLE["katana"], flakes=4, flake_size=1.4)
    plan1 = [("pre", 0.4), ("draw", 1.0), ("decay", 0.3), ("decay", 0.55), ("decay", 0.8), ("decay", 1.0), None]
    plan2 = [None, None, ("pre", 0.45), ("draw", 1.0), ("decay", 0.33), ("decay", 0.66), ("decay", 1.0)]
    out = []
    for i in range(len(DD_MS)):
        fr = K.frame()
        Lf = fr.L(st["flake"])
        Lb = fr.L(st["ink"])
        Le = fr.L(K.EMB)
        Lh = fr.L(K.HOT)
        for S, plan, sd in ((S1, plan1, seed), (S2, plan2, seed + 7)):
            if plan[i]:
                st_draw(S, fr, plan[i], st, Lf, Lb, Lh, Le, seed=sd, i=i)
        out.append(fr.render())
    return out


# =============================================================================
# 단검 질풍 — 이동 잔상
# =============================================================================
GW_MS = [40, 50, 70, 90]


def gale_wind(d, run_rows, seed=5741):
    sil_src = run_rows[d][2]
    t = K.TA(d, K.PV)
    out = []
    lanes = [(-30, 54, 70), (28, 30, 56), (-24, 84, 46)]       # (옆, 높이 z, 길이) — 몸 양옆으로
    for i in range(len(GW_MS)):
        fr = K.frame()
        Lw = fr.L([K.S1, K.S2, K.A18, K.A19, K.A21])
        Lf = fr.L(K.FLAKE)
        k = i / (len(GW_MS) - 1)
        for j, (lat, z, ln) in enumerate(lanes):
            back = 6 + 10 * i
            pts = []
            for m in range(21):
                u = m / 20
                x = -back - ln * u * (1 - 0.25 * k)
                sx, sy = t((x, lat + 1.5 * math.sin(u * 5 + j)))
                pts.append((sx, sy - z))
            S = BR.Stroke(pts[::-1], 3.0 - 0.6 * j, seed=seed + j, peak=0.75, dry_from=0.4, split=1.4, drops=0, start_w=0.1,
                          end_w=0.6, lanes=4)
            S.draw(Lw, head=1.0, tail=0.15 + 0.6 * k, vmax=0.8 - 0.25 * k, k=0.2 + 0.7 * k, drops=False)
        r = random.Random(seed + i)
        for j in range(3 + i):
            sx, sy = t((-r.uniform(8, 40) - 6 * i, r.uniform(-14, 14)))
            W.flake(Lf, sx, sy - r.uniform(20, 90) - 4 * i, r.uniform(1.0, 1.8), r.uniform(0, 6), v=0.8 - 0.1 * i)
        img = fr.render()
        sil = K.silhouette(sil_src, "ash", erode=[0.0, 0.3, 0.6, 0.85][i], seed=seed + i, hot_frac=0.3)
        dx, dy = t((-4 * i, 0))
        img2 = Image.new("RGBA", img.size, (0, 0, 0, 0))
        img2.alpha_composite(sil, (int(dx - 48), int(dy - 138)))
        img2.alpha_composite(img)        # 바람 획이 실루엣 위
        out.append(img2)
    return out


# =============================================================================
# 활 속사 — 충전 단축 표시(aim_charge 규격)
# =============================================================================
QC_MS = [70, 70, 70, 70, 70, 100]           # aim_charge 100ms × 6 의 70% (진행도 구동 — 실제 속도는 시스템)


def quick_charge():
    out = []
    cx, cy, R = 64, 64, 40
    for i in range(6):
        fr = K.frame(128, 128)
        Lg = fr.L([K.S0, K.S1])
        La = fr.L([K.A18, K.A19, K.A21, K.A23, K.A25])
        Le = fr.L(K.EMB_HI)
        Lh = fr.L(K.HOT)
        Lg.arc(cx, cy, R, R, 0, 2 * math.pi, 0.8, v=0.9, dash=(12, 0.45, 0.0))
        p = i / 5
        a0 = -math.pi / 2
        a1 = a0 + 2 * math.pi * max(0.04, p) * 0.985
        if i > 0:
            La.arc(cx, cy, R, R, a0, a1, 1.6, prof=FK.tp_head(0.5), v=0.95)
            La.arc(cx, cy, R - 5, R - 5, a0 + (a1 - a0) * 0.35, a1, 0.8, prof=FK.tp_head(0.8), v=0.7)
        hx, hy = cx + math.cos(a1) * R, cy + math.sin(a1) * R
        tx, ty = -math.sin(a1), math.cos(a1)
        for m in range(2):                      # 속도 쐐기 » 두 개(머리 앞)
            bx, by = hx + tx * (5 + 5 * m), hy + ty * (5 + 5 * m)
            nx, ny = math.cos(a1), math.sin(a1)
            Le.stroke([(bx - tx * 4 + nx * 3.5, by - ty * 4 + ny * 3.5), (bx, by), (bx - tx * 4 - nx * 3.5, by - ty * 4 - ny * 3.5)],
                      0.7, v=0.95 - 0.25 * m)
        if i == 5:
            Lh.star4(cx, cy - R, 6, w=0.8, v=1.0, diag=0.4)
            La.ring(cx, cy, R + 4, 0.6, v=0.6)
        else:
            Le.stamp(hx, hy, 1.4, 0.95, soft=0.3)
        out.append(fr.render())
    return out


# =============================================================================
# 활 저격 — 가득 당김 반짝임(완벽 놓기 창 열림)
# =============================================================================
SF_MS = [30, 40, 60, 80, 100]


def snipe_full():
    out = []
    cx, cy = 40, 40
    for i in range(len(SF_MS)):
        fr = K.frame(80, 80)
        La = fr.L([K.A18, K.A19, K.A21, K.A23, K.A25])
        Lg = fr.L([K.A19, K.A21, K.A23, K.A25])
        rr = [18, 12, 8, 7, 6][i]
        v = [0.7, 0.9, 1.0, 0.8, 0.55][i]
        for s in (-1, 1):                      # 좁혀 드는 괄호 두 개
            a0 = math.radians(90 * s - 55)
            a1 = math.radians(90 * s + 55)
            La.arc(cx, cy, rr, rr, a0, a1, 0.8, prof=FK.tp_both(0.6, 0.5), v=v)
        if i >= 1:
            Lg.star4(cx, cy, [0, 8, 11, 8, 5][i], w=0.7, v=[0, 0.95, 1.0, 0.85, 0.6][i], diag=0.4 if i == 2 else 0)
        out.append(fr.render())
    return out


# =============================================================================
def specs():
    T = {}
    kf = K.body("player/v3/player_katana_fall")
    hit = kf["timingMs"]["hitAt"]
    T["katana_fall_wide"] = dict(rows=K.DIRS4, ms=FALLW_MS, glow=[1, 2], fn=fall_wide, anchor=K.PV, fit="pivot", meta=K.pp_meta(
        weapon="katana", branch="선풍(旋風) 1단 A — 연격 변화", replaces="fx/v3/katana_fall",
        replaceRule="선풍 1단을 고른 런에서 2타 fx 를 이 시트로 1:1 교체(프레임 수·ms·impactFrame·spawn 같음). 몸·무기 시트는 그대로",
        bodySheet="player_katana_fall", spawn="body_ms", spawnAtMs=hit - FALLW_MS[0], impactAtBodyMs=hit, impactFrame=1,
        dirTransform="rotate", followPlayer=False,
        hitShape=dict(type="arc", startDeg=FALLW_A[0], endDeg=FALLW_A[1], radiusR=1.0, innerR=0.0, damageScale=1.2,
                      note="설계안 2.2: 2타 내려베기 호 130°→180°(56 실제 110°에서 180°), 판정 ×1.2 — 참고값, 시스템 데이터 기준"),
        drawnArc=dict(fromDeg=FALLW_A[0], toDeg=FALLW_A[1], radiusDots=FALLW_R, brushWidthDots=10, heightDots=[41, 2]),
        frameRoles=["pre", "draw(머리 55% · 판정)", "draw(끝까지 · 안쪽 바람 획)", "decay", "decay", "decay(재)"],
        design="2타 내려베기를 180°로 크게 휘두른 붓 한 획 + 안쪽에 같은 방향 가는 바람 획(선풍 = 회전의 예고)"))
    T["status_stagger"] = dict(rows=["any"], ms=STAG_MS, glow=[], fn=lambda d: stagger(), anchor=(80, 100), fit="pivot", meta=dict(
        anchor="enemy_head", followTarget=True, depth="above", spawn="stagger_start",
        loopRange=[2, 3], loopNote="경직 동안 f2~f3 반복, 경직이 끝나면 f4 1회 후 끔(경직 0.2초면 f0~f1 + f4 만 써도 됨)",
        usedBy={"투구가르기 1단 1타 올려베기 적중": "경직 0.2초", "중압 1단 수평 베기(sweep_cw·ccw) 적중": "경직 0.25초",
                "그 밖": "갈래·패시브 경직(중량 4 등) 공용"},
        anchorNote="pivot = 적 머리 위(dagger_brand_mark 와 같은 enemy_head). 낙인 표식과 겹치면 이 시트를 위로 20 도트",
        frameRoles=["톡 튐", "가장 큼", "떨림 루프", "떨림 루프", "흩어짐"],
        design="머리 위로 튀는 꺾인 호박 금 5줄(흙 테) — 그로기 소용돌이(player_groggy_swirl)와 다른 '짧은 충격' 모양. 백열 없음"))
    gc = K.body("player/v3/player_greatsword_cleave")
    T["greatsword_cleave_crack"] = dict(rows=["any"], ms=CC_MS, glow=[], fn=lambda d: cleave_crack(), anchor=K.CO, fit="center", meta=dict(
        weapon="greatsword", branch="파쇄(破碎) 1단 A — 연격 변화", bodySheet="player_greatsword_cleave", anchor="hitbox_center",
        anchorNote="pivot = V 내려찍기 끝점 충격원 중심(hitShape.impactCircle — 판정 원점에서 조준 방향 265.2 도트). greatsword_cleave_impact 와 같은 점",
        rotate=True, drawnFacing="right", flipY="allowed", depth="above", spawn="body_ms", spawnAtMs=gc["timingMs"]["hitAt"], impactFrame=0,
        spawnNote="파쇄 1단 런에서 V 내려찍기(관성 순환 2·4타 = greatsword_cleave) impactFrame 시작에 1회, 조준 방향으로 회전",
        hitShape=dict(type="rect", fromPx=0, lengthPx=CC_L, halfWidthPx=24, frontPxByFrame=CC_FRONT + [CC_L] * 5, activeFrames=[0, 1, 2],
                      damageScale=0.5, pierce=True, note="설계안 2.3 '4타 균열 2칸 ×0.5' — 앞머리가 지나간 칸만, 적마다 1회. 참고값"),
        tiles=2, lengthPx=CC_L, frameRoles=["앞머리 1칸 미만", "1.5칸", "2칸(끝)", "다 갈라짐", "식음", "식음", "식음", "재"],
        holdLast="마지막 칸을 붙잡아 오래 남기려면 시스템이 끄는 시점을 정함(반투명 금지)", shakeHint={"px": 3, "ms": 90},
        design="파쇄 균열(greatsword_shatter_crack)의 짧은 판 — 흙 테 호박 금 + 가지 금 4 + 솟았다 떨어지는 돌 조각, 앞머리 흙먼지·불티. 백열 없음"))
    dc = K.body("player/v3/player_dagger_combo3")
    h1 = dc["timingMs"]["hitAt"]
    T["dagger_combo3_double"] = dict(rows=K.DIRS4, ms=DD_MS, glow=DD_GLOW, fn=dagger_double, anchor=K.PV, fit="pivot", meta=K.pp_meta(
        weapon="dagger", branch="쌍격(雙擊) 1단 A — 연격 변화", replaces="fx/v3/dagger_combo3", bodySheet="player_dagger_combo3",
        spawn="body_ms", spawnAtMs=h1 - DD_MS[0], impactFrame=1, hitFrames=[1, 3], hitsAtBodyMs=[h1, h1 + sum(DD_MS[1:3])],
        dirTransform="rotate", depth="above",
        thrust=[dict(lengthPx=156, widthPx=36, angleDeg=-7, fromPx=14), dict(lengthPx=170, widthPx=40, angleDeg=7, fromPx=14)],
        thrustNote="두 찌르기 = 판정 2회(각 낙인 +1 → 3타 합 낙인 +2, 설계안 2.4). 길이·폭은 56 3타(168·40) 기준 참고값",
        bodyNote="몸·무기 시트는 dagger_combo3 그대로(한 번 찌르는 동작) — 두 번째 찌르기는 fx 로만 보임. 몸까지 2연으로 바꿀지는 인터뷰 항목",
        frameRoles=["pre 1", "찌르기 1(판정)", "1 마름 · pre 2", "찌르기 2(판정)", "decay", "decay", "decay(재)"],
        design="−7°·+7° 로 엇갈린 두 찌르기 붓획이 70ms 간격으로 — 두 번째가 더 길고 굵다"))
    T["dagger_gale_wind"] = dict(rows=K.DIRS4, ms=GW_MS, glow=[], fn=None, anchor=K.PV, fit="pivot", meta=K.pp_meta(
        weapon="dagger", branch="질풍(疾風) 1단 B — 연격 변화(이동 +15%·연격 중 감속 없음)", followPlayer=False, depth="below_player",
        spawn="move_interval", spawnIntervalMs=90,
        spawnNote="질풍 1단 런에서 걷기·달리기·연격 중 이동할 때 90ms마다 그 순간의 발 피벗에 1회(따라가지 않음). 행 = 이동 방향(4방향 중 가까운 것)",
        heroSource="player/v3/player_run_free 열 2(방향 행별) 실루엣 — 단검 몸과 자세가 달라도 재 실루엣이라 무방",
        frameRoles=["재 실루엣 + 바람 획 3", "아래부터 부서짐", "부서짐", "거의 사라짐"],
        design="달리는 몸 뒤에 남는 재 실루엣(어두운 재 디더 · 밝은 재 테 · 금 자리 호박)과 뒤로 끌리는 가는 바람 붓획 3줄, 재 조각이 떠오름"))
    T["aim_charge_quick"] = dict(rows=["any"], ms=QC_MS, glow=[5], fn=lambda d: quick_charge(), anchor=(64, 64), fit="none", meta=dict(
        weapon="bow", branch="속사(速射) 1단 A — 연격 변화(좌클릭 충전 시간 −30%)", replaces="fx/v3/aim_charge", anchor="player_pivot",
        anchorNote="aim_charge 와 같은 자리·같은 규격(128×128 · 피벗 = 고리 중심 · 반지름 40 도트) — 속사 1단 런에서 1:1 교체",
        progressDriven=True, progressRule="frame = min(5, floor(progress × 5)) (aim_charge 와 같음). 충전 속도(−30%)는 시스템 데이터",
        spawn="aim_charge", depth="above", glowNote="f5(가득) 고리 위 별만 백열",
        frameRoles=["0%", "20%", "40%", "60%", "80%", "가득"],
        design="점선 안내 고리를 혼불 고리가 시계 방향으로 채우는데 머리 앞에 속도 쐐기 » 두 개 + 안쪽 짧은 둘째 줄(빠름 표시)"))
    T["bow_snipe_full"] = dict(rows=["any"], ms=SF_MS, glow=[], fn=lambda d: snipe_full(), anchor=(40, 40), fit="center", meta=dict(
        weapon="bow", branch="저격(狙擊) 1단 B — 연격 변화(가득 당김 +0.1초 · 완벽 놓기 피해 +25%)", anchor="blade_tip",
        anchorNote="무기 weapons/v3/bow_draw_hold 의 bladeTipAnchors[방향][지금 프레임](= 화살촉 끝, 무기 시트 좌표 — 몸 좌표 = −(48,48))",
        followTarget=True, depth="above", spawn="perfect_window_open",
        spawnNote="저격 1단 런에서 가득(fullFrame 5) 도달 순간 1회 — 완벽 놓기 0.15초 창이 열렸다는 신호(연출만). 창이 닫히면 이미 꺼져 있음(총 310ms)",
        frameRoles=["괄호 좁혀 듦", "반짝", "가장 밝음(A25)", "식음", "사라짐"],
        design="화살촉 위로 좁혀 드는 호박 괄호 두 개 + 네 갈래 반짝임(백열 없음)"))
    return T


def job(name):
    T = specs()
    sp = T[name]
    if name == "dagger_gale_wind":
        _, run = K.grid_frames("player/v3/player_run_free")
        frames = {d: gale_wind(d, run) for d in sp["rows"]}
    else:
        frames = {d: sp["fn"](d) for d in sp["rows"]}
    meta = dict(sp["meta"])
    if meta.get("anchor") == "player_pivot" and sp["fit"] == "pivot":
        pass
    res = K.write(name, frames, sp["rows"], sp["ms"], sp["glow"], sp["anchor"], fit=sp["fit"], meta=meta, src=SRC)
    if meta.get("anchor") == "player_pivot" and sp["fit"] == "pivot":
        _hit_origin(name)
    return res


def _hit_origin(name):
    import json
    import os
    p = os.path.join(K.OUT_FX, name + ".json")
    j = json.load(open(p, encoding="utf-8"))
    j["hitOriginInFrame"] = {"x": j["pivot"]["x"], "y": j["pivot"]["y"] - K.HIT_UP}
    json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


NAMES = ["katana_fall_wide", "status_stagger", "greatsword_cleave_crack", "dagger_combo3_double", "dagger_gale_wind", "aim_charge_quick",
         "bow_snipe_full"]
