"""2단 갈래 전용 fx (설계안 2.2~2.5 2단 α = 1단 동작 심화 · β = 자원 규칙 전환 표시, 6.2 '2단 전용 fx 16').

칼   회오리 α  katana_whirl_loop · katana_whirl_reflect        잔월 β  katana_moon_trail
     일도양단 α katana_cleave_crack · katana_execute            명경 β  katana_mirror_ki · katana_mirror_parry (+ 분신 2체 = katana_issen_shadow 재사용)
대검 지진 α  greatsword_quake_fork (+ 공중제비 착지 균열 = greatsword_shatter_crack_t2 재사용)
     반향 β  greatsword_echo_counter      거인 α  greatsword_giant_ring · greatsword_charge_flash_lv4      울혈 β  greatsword_congest_aura · greatsword_congest_burst
단검 난무 α  dagger_frenzy_clone_in · dagger_frenzy_clone_out (+ 상주 분신 = 몸·무기 시트 그림자 색 교체 shadowPalette)
     출혈 β  dagger_brand_bleed · dagger_brand_hop     비도 α  dagger_stuck_blade (+ 투척 5개 = dagger_thrown 재사용)
     열풍 β  dagger_hotwind_trail · dagger_hotwind_burst (+ 화상 = status_burn)
활   연궁 α  bow_arrow_split     무한통 β  bow_arrow_stuck · bow_arrow_recall     필중 α  bow_deadeye_scope
     천공 β  bow_link_stack · bow_skypierce_line
"""
import math
import random

from PIL import Image

import kit as K
from kit import W, FK, BR, F

SRC = "parts/art/work/build57/build.py branch (57라운드 2단 갈래 fx)"
Rk = 152.0                      # 칼 판정 반경 R(도트)


def _ash_flakes(L, cx, cy, n, spread, fall, k, seed, size=1.6, ky=1.0):
    r = random.Random(seed)
    for _ in range(n):
        a = r.uniform(0, 6.28)
        d = spread * r.uniform(0.2, 1.0)
        W.flake(L, cx + math.cos(a) * d, cy + math.sin(a) * d * ky + fall * k * r.uniform(0.6, 1.3), size * r.uniform(0.7, 1.1) * (1 - 0.3 * k),
                r.uniform(0, 6), v=r.uniform(0.6, 1.0) * (1 - 0.3 * k))


def _embers(L, cx, cy, n, dist, k, seed, up=True, length=3.0):
    r = random.Random(seed)
    for _ in range(n):
        a = r.uniform(-2.8, -0.35) if up else r.uniform(0, 6.28)
        d = dist * r.uniform(0.4, 1.0) * (0.5 + k)
        W.ember(L, cx + math.cos(a) * d, cy + math.sin(a) * d + 6 * k * k, math.cos(a), math.sin(a), length * (1 - 0.5 * k), w=0.6, v=0.9 - 0.35 * k)


# =============================================================================
# 칼 회오리 α — 지속 회전 루프 · 투사체 반사
# =============================================================================
WH_MS = [40, 40, 40, 40, 40, 40]


def whirl_loop(seed=5801):
    cx, cy = K.CO
    out = []
    R = 158.0
    for i in range(6):
        fr = K.frame()
        Lw = fr.L([K.A17, K.A18, K.A19])
        Lf = fr.L(K.FLAKE)
        Lb = fr.L(K.INK_K)
        Le = fr.L(K.EMB)
        ph = 60.0 * i
        for j in range(2):
            a0 = ph + 180 * j - 150
            pts = K.ring_pts(cx, cy, R - 5, a0, a0 + 150, z=12, n=60)[::-1]     # 앞머리(시계 방향 끝)에서 시작 → 꼬리가 마르며 갈라짐
            S = BR.Stroke(pts, 10.0, seed=seed + j, peak=0.6, dry_from=0.4, split=2.0, drops=4, start_w=0.05, end_w=0.7)
            S.draw(Lb, head=1.0, vmax=0.86, drops=False)
            hx, hy = pts[0]
            for m in range(3):
                a = math.radians(a0 + 150 + 90) + random.Random(seed + i * 7 + m + j * 3).uniform(-0.4, 0.4)
                W.ember(Le, hx + math.cos(a) * 6 * (m + 1), hy + math.sin(a) * 6 * (m + 1) * K.KY, math.cos(a), math.sin(a), 3.0, w=0.6, v=0.85 - 0.15 * m)
            wp = K.ring_pts(cx, cy, R * 0.6, a0 + 40, a0 + 140, z=16, n=40)
            BR.Stroke(wp, 3.0, seed=seed + 9 + j, peak=0.6, dry_from=0.4, split=1.5, drops=0, start_w=0.1, end_w=0.4, lanes=4).draw(
                Lw, head=1.0, vmax=0.7, drops=False)
        r = random.Random(seed + i)
        for m in range(6):
            a = math.radians(r.uniform(0, 360))
            d = R * r.uniform(0.85, 1.15)
            W.flake(Lf, cx + math.cos(a) * d, cy + math.sin(a) * d * K.KY - 10, r.uniform(1.2, 2.0), a, v=0.75)
        out.append(fr.render())
    return out


RF_MS = [30, 40, 50, 60, 70]


def whirl_reflect(seed=5811):
    out = []
    t = K.TR(0, K.CO)
    for i in range(len(RF_MS)):
        fr = K.frame()
        Lb = fr.L(K.INK_K)
        Le = fr.L(K.EMB_HI)
        Lf = fr.L(K.FLAKE)
        Lh = fr.L(K.HOT)
        k = i / 4
        pts = t.pts([(math.cos(math.radians(a)) * 16 - 10, math.sin(math.radians(a)) * 22) for a in range(-70, 71, 5)])
        S = BR.Stroke(pts, 4.5, seed=seed, peak=0.5, dry_from=0.6, split=1.5, drops=3, start_w=0.2, end_w=0.4, lanes=5)
        if i == 0:
            S.draw(Lb, head=1.0, vmax=0.9, drops=False)
            Lh.star4(*t((6, 0)), 5, w=0.7, v=1.0)
        else:
            S.draw(Lb, head=1.0, tail=0.15 * i, vmax=0.85 - 0.15 * i, k=0.25 * i, drops=False)
        # 되돌아 나가는 줄(오른쪽 = 반사 방향)
        x0 = 8 + 14 * i
        Le.stroke(t.pts([(x0, 0), (x0 + 26 - 4 * i, 0)]), 1.1, prof=FK.tp_head(0.8), v=0.95 - 0.15 * i)
        for s in (-1, 1):
            Le.stroke(t.pts([(x0 - 4, s * 3), (x0 + 12 - 2 * i, s * (6 + 2 * i))]), 0.7, prof=FK.tp_head(0.8), v=0.8 - 0.15 * i)
        if i >= 2:
            _ash_flakes(Lf, *t((0, 0)), 4, 14, 8, k, seed + i, 1.2)
        out.append(fr.render())
    return out


# =============================================================================
# 칼 잔월 β — 달 궤적(경로 위에 남는 초승달)
# =============================================================================
MT_MS = [50, 50, 75, 75, 75, 75, 80, 90, 110]


def moon_trail(seed=5821):
    cx, cy = 60, 40
    out = []
    for i in range(len(MT_MS)):
        fr = K.frame(120, 80)
        Lg = fr.L([K.A17, K.A18, K.A19])
        Lm = fr.L([K.A19, K.A21, K.A23, K.A25])
        Lf = fr.L(K.FLAKE)
        Ls = fr.L([K.A21, K.A23, K.A25])
        if i == 0:
            K.crescent(Lm, cx, cy, 14, 6, 3, v=0.6, ang=math.pi / 2)
        elif i <= 5:
            pulse = 1.0 if i == 2 else 0.85
            K.crescent(Lg, cx, cy + 1, 25, 10, 7, v=0.8, ang=math.pi / 2)
            K.crescent(Lm, cx, cy, 22, 8, 4, v=pulse, ang=math.pi / 2)
            # 초승달을 따라 도는 밝은 점(루프 위상)
            if i >= 2:
                u = (i - 2) / 4
                a = math.pi * (0.15 + 0.7 * u)
                Ls.stamp(cx - math.cos(a) * 20, cy + math.sin(a) * 7, 1.1, 1.0, soft=0)
            if i == 2:
                for s in (-1, 1):
                    Ls.star4(cx + s * 22, cy - 1, 3, w=0.5, v=0.9)
        else:
            k = (i - 5) / 3
            K.crescent(Lg, cx, cy + 1, 25 * (1 - 0.2 * k), 10, 7, v=0.7 - 0.3 * k, ang=math.pi / 2)
            K.crescent(Lm, cx, cy, 22 * (1 - 0.25 * k), 8, 4, v=0.7 - 0.45 * k, ang=math.pi / 2)
            _ash_flakes(Lf, cx, cy - 4, 5, 20, 10, k, seed + i, 1.3, 0.4)
            for m, v in Lm.v.items():
                if W.h2(m[0] >> 1, m[1], seed + i) < 0.55 * k:
                    Lm.v[m] = 0
        out.append(fr.render())
    return out


# =============================================================================
# 칼 일도양단 α — 내려베기 끝 직선 균열 4칸 · 처형
# =============================================================================
CL_MS = [30, 30, 30, 30, 40, 60, 80, 100, 120]
CL_X0 = 192.0
CL_L = 4 * K.TILE


def cleave_line(d, seed=5831):
    t = K.TA(d)
    C = K.Crack(CL_X0, CL_L, seed, amp=3.2, branches=7, width=1.9)
    r = random.Random(seed)
    st = [(CL_X0 + r.uniform(4, CL_L), r.uniform(-12, 12)) for _ in range(10)]
    born = [min(3, int((p[0] - CL_X0) / 64)) for p in st]
    out = []
    for i in range(len(CL_MS)):
        fr = K.frame()
        G = K.ground_layers(fr)
        front = CL_X0 + 64 * (i + 1) if i < 4 else None
        k = 0.0 if i <= 4 else (i - 4) / 4
        C.draw(G["gr"], G["crk"], t, front=front, k=k)
        K.stones(G["flake"], t, st, i, born, seed, size=2.6, rise=9)
        if i < 4:
            fx, fy = t((front, 0))
            G["dust"].cloud(fx, fy - 4, 8, v=0.6, flat=0.55, seed=i)
            _embers(G["emb"], fx, fy, 4, 10, 0.2, seed + i)
        out.append(fr.render())
    return out


EX_MS = [30, 40, 50, 60, 70, 90, 110]


def execute(seed=5841):
    cx, cy = 100, 140
    out = []
    for i in range(len(EX_MS)):
        fr = K.frame(200, 240)
        Lgr = fr.L([K.B0, K.B1, K.B2])
        Lf = fr.L(K.FLAKE)
        Lb = fr.L(K.INK_K)
        Le = fr.L(K.EMB_HI)
        Lh = fr.L(K.HOT)
        vpts = [(cx + 2 * math.sin(u * 3), cy - 78 + 140 * u) for u in [m / 40 for m in range(41)]]
        V = BR.Stroke(vpts, 7.0, seed=seed, peak=0.45, dry_from=0.75, split=1.2, drops=5, start_w=0.1, end_w=0.5)
        hpts = [(cx - 26 + 52 * m / 20, cy - 8 + 3 * math.sin(m / 20 * 3.1)) for m in range(21)]
        Hs = BR.Stroke(hpts, 4.0, seed=seed + 1, peak=0.4, dry_from=0.6, split=1.4, drops=3, start_w=0.2, end_w=0.4, lanes=5)
        if i == 0:
            V.draw(Lb, head=1.0, vmax=0.9, wk=0.45, hot=True, Lhot=Lh, drops=False)
            Lh.stroke(vpts[8:32], 0.8, prof=FK.tp_both(0.6, 0.5), v=1.0)
        elif i == 1:
            V.draw(Lb, head=1.0, vmax=0.92, hot=True, Lhot=Lh)
            Hs.draw(Lb, head=1.0, vmax=0.9, drops=False)
            Lh.star4(cx, cy - 8, 9, w=0.8, v=1.0, diag=0.4)
        else:
            k = (i - 2) / 4
            sp = 3 + 9 * k                                   # 두 쪽으로 갈라짐
            for s in (-1, 1):
                pts = [(x + s * sp, y + 4 * k) for x, y in vpts]
                BR.Stroke(pts, 4.5, seed=seed + 3 + s, peak=0.45, dry_from=0.6, split=1.4, drops=4, start_w=0.1, end_w=0.5).draw(
                    Lb, head=1.0, tail=0.05 + 0.5 * k, vmax=0.85 - 0.25 * k, k=0.2 + 0.7 * k, fall=6 * k)
            Hs.draw(Lb, head=1.0, tail=0.2 + 0.6 * k, vmax=0.75 - 0.3 * k, k=0.3 + 0.6 * k, drops=False)
            _ash_flakes(Lf, cx, cy - 10, 10, 34, 24, k, seed + i)
            if k < 0.6:
                _embers(Le, cx, cy - 20, 8, 30, k, seed + 9 + i, up=False)
        if i >= 1:                                            # 발밑 짧은 금
            kk = max(0.0, (i - 3) / 3)
            Lgr.stroke([(cx - 18, cy + 64), (cx - 4, cy + 61), (cx + 6, cy + 65), (cx + 20, cy + 62)], 1.4, prof=FK.tp_both(0.5, 0.5), v=0.8 - 0.3 * kk)
        out.append(fr.render())
    return out


# =============================================================================
# 칼 명경 β — 검기 5단 표시 · 패링 2단 충전
# =============================================================================
MK_MS = [110] * 6


def mirror_ki(n):
    cx, cy = K.PV
    out = []
    for i in range(6):
        fr = K.frame()
        Ld = fr.L([K.K1, K.S0, K.S1])
        Lm = fr.L([K.A19, K.A21, K.A23, K.A25])
        for m in range(5):
            a = 90 + 72 * m
            x, y = K.ell(cx, cy, a, 50, ky=0.5)
            lit = m < n
            if lit:
                v = 1.0 if (i % 5) == m or (i == 5 and m == n - 1) else 0.78
                K.crescent(Lm, x, y, 6.5, 3.2, 2.2, v=v, ang=math.radians(a))
            else:
                K.crescent(Ld, x, y, 6.0, 3.0, 2.0, v=0.7, ang=math.radians(a))
        # 다 찼을 때(5) 가는 고리 이음
        if n == 5:
            Lm.arc(cx, cy, 50, 25, 0, 2 * math.pi, 0.5, v=0.5, dash=(10, 0.35, i / 6))
        out.append(fr.render())
    return out


MP_MS = [30, 40, 50, 60, 70, 90]


def mirror_parry(seed=5851):
    t = K.TR(0, K.CO)
    out = []
    for i in range(len(MP_MS)):
        fr = K.frame()
        Lg = fr.L([K.S1, K.S2, K.S3])
        Lm = fr.L([K.A19, K.A21, K.A23, K.A25])
        Lf = fr.L(K.FLAKE)
        Lh = fr.L(K.HOT)
        k = i / 5
        if i <= 1:
            Lg.stroke(t.pts([(0, -34), (0, 34)]), 1.6, prof=FK.tp_both(0.6, 0.5), v=0.9)
            Lm.stroke(t.pts([(0, -30), (0, 30)]), 0.9, prof=FK.tp_both(0.6, 0.5), v=1.0)
            Lh.stroke(t.pts([(0, -12), (0, 12)]), 0.7, prof=FK.tp_both(0.6, 0.5), v=1.0)
            Lh.star4(*t((0, 0)), 7 + 3 * i, w=0.8, v=1.0)
        else:
            for s in (-1, 1):                                 # 거울이 두 조각으로 갈라져 주인공 쪽(−x)으로 날아감
                q = (i - 1) / 4
                x = -10 - 46 * q
                y = s * (16 - 10 * q)
                K.crescent(Lm, *t((x, y)), 7, 3.5, 2.5, v=0.95 - 0.3 * q, ang=math.pi)
                Lg.stroke(t.pts([(x + 6, y), (x + 22 - 10 * q, y + s * 3)]), 0.7, prof=FK.tp_head(0.8), v=0.7 - 0.3 * q)
            Lg.stroke(t.pts([(0, -30 + 10 * k), (0, -8)]), 0.9, v=0.6 - 0.4 * k, dash=(6, 0.5, 0))
            Lg.stroke(t.pts([(0, 8), (0, 30 - 10 * k)]), 0.9, v=0.6 - 0.4 * k, dash=(6, 0.5, 0.3))
            _ash_flakes(Lf, *t((0, 0)), 4, 18, 8, k, seed + i, 1.2)
        out.append(fr.render())
    return out


# =============================================================================
# 대검 지진 α — 균열 끝 3갈래
# =============================================================================
QF_MS = [30, 30, 30, 30, 60, 80, 100, 120, 140]


def quake_fork(seed=5861):
    cracks = [(a, K.Crack(0.0, 2 * K.TILE, seed + j, amp=3.0, branches=3, width=1.8)) for j, a in enumerate((-25.0, 0.0, 25.0))]
    r = random.Random(seed)
    out = []
    for i in range(len(QF_MS)):
        fr = K.frame()
        G = K.ground_layers(fr)
        front = [44, 88, 128, None][i] if i < 4 else None
        k = 0.0 if i <= 3 else (i - 3) / 5
        for a, C in cracks:
            t = K.TR(a, K.CO)
            C.draw(G["gr"], G["crk"], t, front=front, k=k)
            if i < 3:
                fx, fy = t((front, 0))
                G["dust"].cloud(fx, fy - 3, 6, v=0.6, flat=0.55, seed=i + int(a))
                _embers(G["emb"], fx, fy, 2, 8, 0.2, seed + i + int(a))
            st = [(r.uniform(10, 120), r.uniform(-8, 8)) for _ in range(4)]
            K.stones(G["flake"], t, st, i, [min(2, int(p[0] / 44)) for p in st], seed + int(a))
        if i == 0:
            G["dust"].cloud(K.CO[0], K.CO[1] - 4, 10, v=0.65, flat=0.5, seed=3)
        out.append(fr.render())
    return out


# =============================================================================
# 대검 반향 β — 퍼펙트 가드 균열 반격
# =============================================================================
EC_MS = [30, 30, 30, 40, 60, 80, 100, 120]


def echo_counter(seed=5871):
    t = K.TR(0, K.CO)
    C = K.Crack(34.0, 3 * K.TILE, seed, amp=3.0, branches=5, width=1.8)
    out = []
    for i in range(len(EC_MS)):
        fr = K.frame()
        G = K.ground_layers(fr)
        k = 0.0 if i <= 3 else (i - 3) / 4
        front = 34 + 64 * (i + 1) if i < 3 else None
        C.draw(G["gr"], G["crk"], t, front=front, k=k, hot=G["hot"] if i == 0 else None)
        # 메아리 호 두 겹(막은 자리에서 앞으로 퍼짐)
        for m, base in enumerate((22, 34)):
            rr = base + 12 * i
            if i > 5:
                continue
            pts = [t((math.cos(math.radians(a)) * rr, math.sin(math.radians(a)) * rr * K.KY)) for a in range(-60, 61, 4)]
            S = BR.Stroke(pts, 5.0 - m, seed=seed + m, peak=0.5, dry_from=0.6, split=1.4, drops=2, start_w=0.2, end_w=0.3, lanes=5)
            S.draw(G["ink"], head=1.0, vmax=0.9 - 0.12 * i, k=0.15 * i, drops=False, hot=(i == 0 and m == 0), Lhot=G["hot"])
        if i < 3:
            fx, fy = t((front, 0))
            G["dust"].cloud(fx, fy - 3, 7, v=0.6, flat=0.55, seed=i)
        out.append(fr.render())
    return out


# =============================================================================
# 대검 거인 α — 차지 4단(번쩍임 · 진동 반경 5칸)
# =============================================================================
CF4_MS = [30, 40, 50, 60, 70, 90]


def charge_flash4(seed=5881):
    cx, cy = 80, 80
    out = []
    for i in range(len(CF4_MS)):
        fr = K.frame(160, 160)
        La = fr.L([K.A18, K.A19, K.A21, K.A23, K.A25])
        Le = fr.L(K.EMB_HI)
        Lh = fr.L(K.HOT)
        sz = [14, 30, 24, 18, 12, 7][i]
        if i <= 1:
            Lh.star4(cx, cy, sz, w=1.1, v=1.0, diag=0.55)
            Lh.star4(cx, cy, sz * 0.6, w=0.9, v=1.0, rot=math.pi / 8)
            La.ring(cx, cy, 10 + 12 * i, 0.9, v=0.95)
        else:
            La.star4(cx, cy, sz, w=0.9, v=1.0 - 0.12 * i, diag=0.5)
            La.arc(cx, cy, 30 + 6 * i, 30 + 6 * i, 0, 2 * math.pi, 0.7, v=0.8 - 0.12 * i, dash=(10, 0.5 - 0.06 * i, 0.1 * i))
        _embers(Le, cx, cy, 10, 40, i / 5, seed + i, up=False, length=4)
        out.append(fr.render())
    return out


def giant_ring():
    import bfx
    return bfx.quake_frames(5.0, seed=5891)


# =============================================================================
# 대검 울혈 β — 그로기 중 맺힘 · 풀리는 순간 폭발
# =============================================================================
CA_MS = [125] * 6


def congest_aura(seed=5901):
    cx, cy = K.PV
    r = random.Random(seed)
    veins = []
    for j in range(7):
        a = 360 * j / 7 + r.uniform(-12, 12)
        p0 = K.ell(cx, cy, a, 8, ky=0.5)
        p1 = K.ell(cx, cy, a + r.uniform(-15, 15), r.uniform(34, 50), ky=0.5)
        veins.append(W.jag(r, p0, p1, n=4, amp=2.0))
    out = []
    for i in range(6):
        fr = K.frame()
        Ld = fr.L([K.K0, K.B0, K.A17])
        Lv = fr.L([K.A17, K.A18, K.A19, K.A21, K.A23])
        Ls = fr.L([K.S0, K.S1, K.S2])
        Le = fr.L(K.EMB)
        pulse = 0.5 + 0.5 * math.cos(2 * math.pi * i / 6)
        Ld.disc(cx, cy, 30, 13, v=0.8, edge=0.5)
        for j, vp in enumerate(veins):
            Lv.stroke(vp, 1.2, prof=FK.tp_tail(0.7), v=0.55 + 0.4 * pulse * (0.7 + 0.3 * ((j + i) % 2)))
        for j in range(3):                          # 오르는 연기 줄
            x0 = cx - 24 + 24 * j
            ph = i * 1.05 + j * 2.1
            pts = [(x0 + 3 * math.sin(ph + u * 4), cy - 10 - 70 * u) for u in [m / 12 for m in range(13)]]
            Ls.stroke(pts, 1.0, prof=lambda u: 0.6 + 0.4 * math.sin(math.pi * min(1, u * 1.3)), v=0.9, vprof=lambda u: 1 - 0.6 * u,
                      dash=(7, 0.6, (i / 6 + j * 0.3) % 1.0))
        rr = random.Random(seed + i)
        for j in range(4):
            x = cx + rr.uniform(-30, 30)
            y = cy - 20 - ((i * 14 + j * 23) % 80)
            W.ember(Le, x, y, 0, -1, 3.0, w=0.6, v=0.8)
        out.append(fr.render())
    return out


CB_MS = [40, 40, 50, 60, 70, 80, 100, 120]
CB_R = 144.0


def congest_burst(seed=5911):
    cx, cy = K.PV
    r = random.Random(seed)
    arcs = [(j * 90 + r.uniform(6, 16), (j + 1) * 90 - r.uniform(8, 20)) for j in range(4)]
    spikes = [(r.uniform(0, 360), r.uniform(0.55, 0.95)) for _ in range(14)]
    out = []
    for i in range(len(CB_MS)):
        fr = K.frame()
        Ld = fr.L(W.R_DUST)
        Lgr = fr.L([K.B0, K.B1, K.B2])
        Lf = fr.L(K.FLAKE_G)
        Lb = fr.L(K.INK_G)
        Le = fr.L(K.EMB_HI)
        Lh = fr.L(K.HOT)
        if i == 0:
            Lh.star4(cx, cy - 50, 16, w=1.1, v=1.0, diag=0.5)
            Lh.stamp(cx, cy - 50, 3, 1.0, soft=0.5)
            for a0, a1 in arcs:
                BR.Stroke(K.ring_pts(cx, cy, CB_R * 0.35, a0, a1), 6, seed=seed).draw(Lb, head=1.0, vmax=0.92, drops=False)
        elif i <= 2:
            rr = CB_R * (0.7 if i == 1 else 1.0)
            for j, (a0, a1) in enumerate(arcs):
                BR.Stroke(K.ring_pts(cx, cy, rr, a0, a1), 9, seed=seed + j, peak=0.45, dry_from=0.6, split=1.3, drops=3).draw(
                    Lb, head=1.0, vmax=0.9, hot=(i == 1), Lhot=Lh, drops=(i == 2))
            for a, f in spikes:
                p0 = K.ell(cx, cy, a, rr * 0.3)
                p1 = K.ell(cx, cy, a, rr * f)
                Lb.stroke([p0, p1], 2.2, prof=FK.tp_tail(0.7), v=0.8)
            for j in range(10):
                a = 36 * j
                x, y = K.ell(cx, cy, a, rr * 0.95)
                Ld.cloud(x, y - 3, 7, v=0.6, flat=0.55, seed=j + i)
            # 솟는 불기둥(몸 높이)
            Lb.stroke([(cx, cy), (cx, cy - 90 - 20 * i)], 7 - i, prof=FK.tp_tail(0.6), v=0.85)
        else:
            k = (i - 2) / 5
            for j, (a0, a1) in enumerate(arcs):
                rr = CB_R * (1.0 + 0.05 * k)
                Lgr.arc(cx, cy, rr, rr * K.KY, math.radians(a0), math.radians(a1), 1.2, prof=FK.tp_both(0.6, 0.5), v=0.8 - 0.4 * k,
                        dash=(12, 0.7 - 0.3 * k, 0.1 * j))
            for j in range(3):
                ph = i + j * 2
                pts = [(cx - 20 + 20 * j + 4 * math.sin(ph + u * 4), cy - 30 - 110 * u * (0.6 + 0.4 * k)) for u in [m / 12 for m in range(13)]]
                Ld.stroke(pts, 4 - 2 * k, prof=lambda u: 0.5 + 0.5 * math.sin(math.pi * u), v=0.75 - 0.3 * k)
            _ash_flakes(Lf, cx, cy - 40, 14, CB_R * 0.8, 30, k, seed + i, 2.0, 0.6)
            if k < 0.6:
                _embers(Le, cx, cy - 40, 10, 60, k, seed + i, up=True, length=4)
        out.append(fr.render())
    return out


# =============================================================================
# 단검 난무 α — 분신 등장·소멸(상주 분신은 몸·무기 시트 그림자 색 교체)
# =============================================================================
FC_IN_MS = [40, 50, 60, 70]
FC_OUT_MS = [50, 60, 80, 100, 120]


def _dagger_pose(d, body, weap, i=0):
    b = body[d][i]
    img = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    img.alpha_composite(b, (48, 48))
    w = weap[d][i]
    if weap["_depth"].get(d) == "below":
        base = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
        base.alpha_composite(w)
        base.alpha_composite(img)
        img = base
    else:
        img.alpha_composite(w)
    return img


def frenzy_clone(d, body, weap, out_=False, seed=5921):
    pose = _dagger_pose(d, body, weap)
    ms = FC_OUT_MS if out_ else FC_IN_MS
    out = []
    for i in range(len(ms)):
        img = Image.new("RGBA", (K.CANVAS, K.CANVAS), (0, 0, 0, 0))
        if out_:
            er = [0.05, 0.3, 0.55, 0.8, 1.0][i]
        else:
            er = [0.85, 0.55, 0.25, 0.0][i]
        sil = K.silhouette(pose, "dark", erode=er, seed=seed + (i if out_ else 0), hot_frac=0.5)
        img.alpha_composite(sil, (K.PV[0] - 96, K.PV[1] - 186))
        fr = K.frame()
        Lf = fr.L([K.K2, K.S0, K.S1, K.S2])
        Le = fr.L(K.EMB)
        Lp = fr.L([K.K0, K.K1, K.S0])
        k = i / (len(ms) - 1)
        cx, cy = K.PV
        Lp.disc(cx, cy, 24 * (0.6 + 0.4 * (1 - k if out_ else k)), 7, v=0.8, edge=0.5)
        rr = random.Random(seed + i)
        for m in range(10):
            a = rr.uniform(0, 6.28)
            if out_:
                dd = 10 + 30 * k * rr.uniform(0.5, 1.2)
                x, y = cx + math.cos(a) * dd * 0.6, cy - 20 - rr.uniform(0, 100) - 30 * k
            else:
                dd = 40 * (1 - k) * rr.uniform(0.6, 1.2)
                x, y = cx + math.cos(a) * dd, cy - 30 - rr.uniform(0, 80) + math.sin(a) * dd * 0.5
            W.flake(Lf, x, y, rr.uniform(1.2, 2.2), a, v=0.85)
        if (not out_ and i == 3) or (out_ and i <= 1):
            _embers(Le, cx, cy - 60, 3, 20, 0.3, seed + i)
        img.alpha_composite(fr.render())
        out.append(img)
    return out


def shadow_palette():
    """주인공 v3 30색 → 그림자 분신 색(밝기 순서를 유지한 어두운 재 + 호박 금은 A19~A21) — 시스템 런타임 색 교체용."""
    dark = [K.K0, K.K1, K.K2, K.S0, K.S1, K.S2]
    amb = {"#d67a11": K.A21, "#e2a33c": K.A21, "#eecc78": K.A23, "#f4de9b": K.A23, "#8b4d22": K.A19, "#653b24": K.A18, "#3f271d": K.A17}

    def lum(h):
        r, g, b = FK.hexrgb(h)
        return 0.3 * r + 0.59 * g + 0.11 * b
    cols = sorted(W.HERO_PAL, key=lum)
    out = {}
    others = [c for c in cols if c not in amb]
    for j, c in enumerate(others):
        out[c] = dark[min(len(dark) - 1, int(j / len(others) * len(dark)))]
    out.update(amb)
    return out


# =============================================================================
# 단검 출혈 β — 낙인 → 출혈 · 낙인이 옮겨감
# =============================================================================
BB_MS = [110] * 6


def brand_bleed(seed=5931):
    cx, cy = 48, 56
    out = []
    marks = [(-10, -16, -8), (2, -10, 6), (12, -18, -4)]
    for i in range(6):
        fr = K.frame(96, 128)
        Lm = fr.L([K.A17, K.A18, K.A19, K.A21])
        Ld = fr.L([K.A17, K.A18, K.A19])
        Lc = fr.L([K.A19, K.A21, K.A23])
        for j, (x, y, tilt) in enumerate(marks):
            Lm.stroke([(cx + x - tilt * 0.3, cy + y - 7), (cx + x + tilt * 0.3, cy + y + 7)], 1.3, prof=FK.tp_both(0.6, 0.5), v=0.95)
            Lc.stroke([(cx + x - tilt * 0.3, cy + y - 4), (cx + x + tilt * 0.2, cy + y + 3)], 0.6, v=0.6 + 0.4 * ((i + j) % 3 == 0))
            for m in range(2):                    # 떨어지는 방울(루프)
                ph = ((i + m * 3 + j * 2) % 6) / 6
                dy = 10 + 40 * ph
                Ld.stamp(cx + x + (tilt * 0.3) + m, cy + y + dy, 1.2 - 0.4 * ph, 0.95 - 0.4 * ph, soft=0.2)
                Ld.put(cx + x + (tilt * 0.3) + m, cy + y + dy - 2, 0.6 - 0.3 * ph)
        out.append(fr.render())
    return out


BH_MS = [50] * 4


def brand_hop(seed=5941):
    cx, cy = 60, 24
    out = []
    for i in range(4):
        fr = K.frame(96, 48)
        Lt = fr.L([K.A17, K.A18, K.A19, K.A21])
        Lm = fr.L([K.A19, K.A21, K.A23, K.A25])
        pts = [(cx - 44 * u, cy + 3 * math.sin(u * 6 + i * 1.6) * u) for u in [m / 16 for m in range(17)]]
        Lt.stroke(pts, 1.6, prof=FK.tp_tail(0.6), v=0.95, vprof=lambda u: 1 - 0.7 * u, dash=(8, 0.75, i * 0.25))
        Lm.stroke([(cx - 4, cy - 6), (cx + 4, cy + 6)], 1.1, v=1.0)
        Lm.stroke([(cx + 4, cy - 6), (cx - 4, cy + 6)], 1.1, v=0.9)
        Lm.stamp(cx, cy, 1.0, 1.0, soft=0)
        out.append(fr.render())
    return out


# =============================================================================
# 단검 비도 α — 박힌 단검
# =============================================================================
SB_MS = [40, 50, 120, 120, 120, 120, 80, 100]


def _stuck(src, tilt_deg, cx, cy, i, seed, ash=False):
    """투사체 그림(오른쪽 보기) → 촉을 아래로 세워 땅에 박음: 촉 쪽 40% 를 땅 아래로 숨김."""
    im = src.rotate(-(90 - tilt_deg), resample=Image.NEAREST, expand=True)
    bb = im.getbbox()
    im = im.crop(bb)
    h = im.height
    vis = im.crop((0, 0, im.width, int(h * 0.62)))
    return vis


def stuck_blade(src, seed=5951, ms=SB_MS, kind="dagger"):
    cx, cy = 60, 70
    blade = _stuck(src, 14 if kind == "dagger" else 10, cx, cy, 0, seed)
    out = []
    for i in range(len(ms)):
        fr = K.frame(120, 100)
        Lc = fr.L([K.K0, K.B0, K.B1])
        Lr = fr.L([K.B1, K.B2, K.B3])
        Ld = fr.L(W.R_DUST)
        Lf = fr.L(K.FLAKE_G)
        Lg = fr.L([K.A21, K.A23, K.A25])
        Lc.disc(cx, cy, 9, 3.5, v=0.9, edge=0.6)
        Lr.arc(cx, cy, 10, 4, math.pi * 1.05, math.pi * 1.95, 0.9, v=0.9)
        if i == 0:
            Ld.cloud(cx, cy - 4, 9, v=0.7, flat=0.5, seed=1)
            _embers(Lg, cx, cy - 6, 5, 12, 0.2, seed)
        elif i == 1:
            Ld.cloud(cx + 2, cy - 6, 7, v=0.55, flat=0.5, seed=2)
        img = Image.new("RGBA", (120, 100), (0, 0, 0, 0))
        base = fr.render()
        img.alpha_composite(base)
        bl = blade
        if i >= 6:
            k = (i - 5) / 2
            bl = K.silhouette(blade, "ash", erode=0.45 * k + 0.2, seed=seed + i, cracks=True)
        img.alpha_composite(bl, (int(cx - bl.width / 2 + 2), int(cy + 1 - bl.height)))
        fr2 = K.frame(120, 100)
        Lg2 = fr2.L([K.A21, K.A23, K.A25])
        Lf2 = fr2.L(K.FLAKE)
        if 2 <= i <= 5:                           # 반짝임이 칼날을 타고 오름(루프)
            q = (i - 2) / 4
            Lg2.stamp(cx + 2 - 2 * q, cy - 6 - (bl.height - 10) * q, 1.0, 1.0, soft=0)
            if i == 4:
                Lg2.star4(cx, cy - bl.height + 4, 4, w=0.5, v=0.9)
        if i >= 6:
            _ash_flakes(Lf2, cx, cy - bl.height / 2, 6, 10, 12, (i - 5) / 2, seed + i, 1.3)
        img.alpha_composite(fr2.render())
        out.append(img)
    return out


# =============================================================================
# 단검 열풍 β — 과열 50% 이상 이동 불꽃 · 커진 과열 폭발
# =============================================================================
HT_MS = [70, 70, 70, 70]


def hotwind_trail(d, seed=5961):
    t = K.TA(d, K.PV)
    out = []
    for i in range(4):
        fr = K.frame()
        Ls = fr.L([K.A17, K.A18])
        Lf = fr.L([K.A18, K.A19, K.A21, K.A23])
        for j in range(7):
            ph = (i / 4 + j * 0.37) % 1.0
            x = -8 - 60 * ph
            lat = [-14, 10, -4, 16, -18, 4, 12][j]
            hgt = (12 + 6 * (j % 3)) * (1 - ph)
            bx, by = t((x, lat * 0.5))
            pts = [(bx + 4 * math.sin(u * 3 + j) * u, by - hgt * u) for u in [m / 6 for m in range(7)]]
            Lf.stroke(pts, 2.2 * (1 - 0.5 * ph), prof=FK.tp_tail(0.9), v=0.95 - 0.5 * ph, vprof=lambda u: 1 - 0.6 * u)
        for j in range(2):                        # 열 아지랑이
            ph = i * 1.6 + j * 2
            bx, by = t((-20 - 18 * j, 0))
            pts = [(bx + 3 * math.sin(ph + u * 6), by - 40 - 50 * u) for u in [m / 10 for m in range(11)]]
            Ls.stroke(pts, 0.7, v=0.8, dash=(6, 0.5, (i / 4 + j * 0.5) % 1))
        out.append(fr.render())
    return out


HB_MS = [40, 40, 50, 60, 70, 80, 90, 110, 130]
HB_R = 184.0


def hotwind_burst(seed=5971):
    cx, cy = K.PV
    r = random.Random(seed)
    arcs = [(j * 60 + r.uniform(4, 12), (j + 1) * 60 - r.uniform(6, 14)) for j in range(6)]
    tongues = [(r.uniform(0, 360), r.uniform(0.7, 1.0)) for _ in range(18)]
    out = []
    for i in range(len(HB_MS)):
        fr = K.frame()
        Lsc = fr.L([K.K0, K.B0, K.B1])
        Lf = fr.L(K.FLAKE)
        Lb = fr.L(K.INK_K)
        Lfl = fr.L([K.A18, K.A19, K.A21, K.A23, K.A25])
        Le = fr.L(K.EMB_HI)
        Lh = fr.L(K.HOT)
        prog = [0.25, 0.6, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0][i]
        k = 0.0 if i <= 2 else (i - 2) / 6
        rr = HB_R * prog
        if i >= 2:
            Lsc.arc(cx, cy, rr * 0.85, rr * 0.85 * K.KY, 0, 2 * math.pi, 3.0, v=0.7 - 0.3 * k, dash=(18, 0.6, 0.05))
        if i <= 4:
            for j, (a0, a1) in enumerate(arcs):
                BR.Stroke(K.ring_pts(cx, cy, rr, a0 + 8 * k, a1 - 8 * k), 9 * (1 - 0.4 * k), seed=seed + j, peak=0.45, dry_from=0.6,
                          split=1.4, drops=2).draw(Lb, head=1.0, tail=0.3 * k, vmax=0.9 - 0.2 * k, k=0.6 * k, hot=(i == 1), Lhot=Lh, drops=False)
        for a, f in tongues:                       # 바깥으로 눕는 불혀
            if i > 6:
                break
            bx, by = K.ell(cx, cy, a, rr * f * 0.9)
            ln = (16 + 10 * f) * (1 - 0.6 * k)
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a)) * K.KY
            pts = [(bx + ca * ln * u * 0.6, by + sa * ln * u * 0.6 - ln * u) for u in [m / 6 for m in range(7)]]
            Lfl.stroke(pts, 2.6 * (1 - 0.4 * k), prof=FK.tp_tail(0.9), v=0.95 - 0.4 * k)
        if i == 0:
            Lh.star4(cx, cy - 40, 14, w=1.0, v=1.0, diag=0.5)
        if i >= 3:
            _ash_flakes(Lf, cx, cy - 30, 12, rr * 0.8, 30, k, seed + i, 1.6, 0.6)
            if k < 0.7:
                _embers(Le, cx, cy - 30, 10, rr * 0.5, k, seed + i, up=True, length=4)
        out.append(fr.render())
    return out


# =============================================================================
# 활 연궁 α — 분열 · 무한통 β — 박힌 화살·회수 · 필중 α — 정밀 조준 · 천공 β — 연결 스택·벽 관통 선
# =============================================================================
SP_MS = [30, 40, 50, 60]


def arrow_split(seed=5981):
    t = K.TR(0, (60, 40))
    out = []
    for i in range(4):
        fr = K.frame(120, 80)
        Lb = fr.L(K.INK_K)
        Le = fr.L(K.EMB_HI)
        Lh = fr.L(K.HOT)
        k = i / 3
        S0_ = BR.Stroke(t.pts([(-36, 0), (0, 0)]), 2.6, seed=seed, peak=0.8, dry_from=0.9, split=0.5, drops=0, start_w=0.1, end_w=0.8, lanes=4)
        S0_.draw(Lb, head=1.0, tail=0.3 * k, vmax=0.8 - 0.2 * k, k=0.4 * k, drops=False)
        for s in (-1, 1):
            ln = 18 + 10 * i
            Sb = BR.Stroke(t.pts([(0, 0), (ln * 0.5, s * ln * 0.08), (ln, s * ln * 0.21)]), 2.2, seed=seed + s, peak=0.4, dry_from=0.6,
                           split=1.2, drops=2, start_w=0.6, end_w=0.3, lanes=4)
            Sb.draw(Lb, head=1.0, tail=0.25 * k, vmax=0.9 - 0.2 * k, k=0.3 * k, drops=False)
        if i == 0:
            Lh.star4(*t((0, 0)), 6, w=0.7, v=1.0)
        else:
            _embers(Le, *t((2, 0)), 5, 10, k, seed + i, up=False, length=2.5)
        out.append(fr.render())
    return out


AR_MS = [40, 50, 60, 70, 80, 90]


def arrow_recall(seed=5991):
    cx, cy = 48, 88
    out = []
    for i in range(len(AR_MS)):
        fr = K.frame(96, 112)
        Lr = fr.L([K.A18, K.A19, K.A21])
        Lm = fr.L([K.A19, K.A21, K.A23, K.A25])
        k = i / 5
        Lr.arc(cx, cy, 10 + 12 * k, (10 + 12 * k) * 0.45, 0, 2 * math.pi, 0.8, v=0.9 - 0.5 * k, dash=(8, 0.55, 0.1))
        for m in range(5):
            a = math.radians(-90 + (m - 2) * 26)
            h = 10 + 60 * (k ** 0.8) * (1 - 0.1 * abs(m - 2)) + 3 * (m % 2)
            x = cx + (m - 2) * 5 * (1 + 0.8 * k) + 1.5 * math.sin(i + m)
            y = cy - h
            Lm.stamp(x, y, 1.2 * (1 - 0.4 * k), 1.0 - 0.3 * k, soft=0)
            Lm.stroke([(x, y), (x, y + 6 * (1 - k) + 2)], 0.5, prof=FK.tp_head(0.8), v=0.7)
        if i == 1:
            Lm.star4(cx, cy - 12, 5, w=0.6, v=0.9)
        out.append(fr.render())
    return out


DE_MS = [60] * 6 + [90] * 4


def deadeye_scope(seed=6001):
    cx, cy = 64, 64
    out = []
    for i in range(10):
        fr = K.frame(128, 128)
        Lg = fr.L([K.S0, K.S1, K.S2])
        La = fr.L([K.A18, K.A19, K.A21, K.A23, K.A25])
        if i <= 5:
            p = i / 5
            rr = 56 - 36 * p
            rotd = 45 * (1 - p)
        else:
            rr = 20
            rotd = [0, 6, 0, -6][i - 6]
        for m in range(4):                        # 괄호 4개(좁혀 듦)
            a = math.radians(rotd + 90 * m)
            La.arc(cx, cy, rr, rr, a - 0.42, a + 0.42, 1.0 if i >= 5 else 0.8, prof=FK.tp_both(0.6, 0.5), v=0.75 + 0.25 * (i >= 5))
            tx, ty = cx + math.cos(a) * (rr + 3), cy + math.sin(a) * (rr + 3)
            Lg.stroke([(tx, ty), (cx + math.cos(a) * (rr + 9), cy + math.sin(a) * (rr + 9))], 0.7, v=0.9)
        Lg.ring(cx, cy, 56, 0.5, v=0.6 if i <= 5 else 0.4, dash=(24, 0.25, 0.0))
        if i >= 5:
            La.stamp(cx, cy, 1.2, 0.95 if i % 2 == 0 else 0.8, soft=0)
        out.append(fr.render())
    return out


LS_MS = [110] * 6


def link_stack(n):
    cx, cy = K.PV
    out = []
    for i in range(6):
        fr = K.frame()
        Ld = fr.L([K.K1, K.S0, K.S1])
        La = fr.L([K.A19, K.A21, K.A23, K.A25])
        for m in range(3):
            a = 90 + 120 * m
            x, y = K.ell(cx, cy, a, 46, ky=0.5)
            L = La if m < n else Ld
            v = (1.0 if (i % 3) == m else 0.8) if m < n else 0.7
            ang = math.radians(a + 90)              # 화살촉이 시계 방향으로 이어짐
            ca, sa = math.cos(ang), math.sin(ang) * 0.5
            tip = (x + ca * 6, y + sa * 6)
            L.stroke([(x - ca * 5 - sa * 4, y - sa * 5 + ca * 2), tip, (x - ca * 5 + sa * 4, y - sa * 5 - ca * 2)], 1.0, v=v)
            L.stroke([(x - ca * 9, y - sa * 9), tip], 0.7, v=v * 0.9)
        if n == 3:
            La.arc(cx, cy, 46, 23, 0, 2 * math.pi, 0.5, v=0.55, dash=(9, 0.4, i / 6))
        out.append(fr.render())
    return out


SK_MS = [125, 125, 125, 125, 40, 60, 80, 100]
SK_P = 64


def skypierce_line(seed=6011):
    """반복 타일 64 도트(가로 이음매 없음) — 화살이 지나간 선 위에 이어 깐다."""
    out = []
    H = 48
    cy = 24
    r = random.Random(seed)
    cuts = [(r.uniform(0, SK_P), r.choice((-1, 1)) * r.uniform(50, 65), r.uniform(14, 22)) for _ in range(2)]
    for i in range(len(SK_MS)):
        fr = K.frame(SK_P * 3, H)
        Lb = fr.L(K.INK_K)
        Lf = fr.L(K.FLAKE)
        Le = fr.L(K.EMB_HI)
        Lh = fr.L(K.HOT)
        for rep in range(3):
            ox = rep * SK_P
            if i <= 3:
                Lb.stroke([(ox - 2, cy), (ox + SK_P + 2, cy)], 0.9, v=0.55 + 0.05 * (i % 2))
                sx = ox + (SK_P * (i / 4) + 9) % SK_P
                Lb.stamp(sx, cy, 1.0, 0.85, soft=0)
                Lb.stamp((sx + 32) % SK_P + ox, cy, 0.8, 0.7, soft=0)
            elif i == 4:
                Lb.stroke([(ox - 2, cy), (ox + SK_P + 2, cy)], 2.4, v=0.9)
                Lh.stroke([(ox - 2, cy), (ox + SK_P + 2, cy)], 0.7, v=1.0)
                for x, a, ln in cuts:
                    c0 = (ox + x - math.cos(math.radians(a)) * ln / 2, cy - math.sin(math.radians(a)) * ln / 2)
                    c1 = (ox + x + math.cos(math.radians(a)) * ln / 2, cy + math.sin(math.radians(a)) * ln / 2)
                    Lb.stroke([c0, c1], 1.6, prof=FK.tp_both(0.6, 0.5), v=0.9)
            else:
                k = (i - 4) / 3
                Lb.stroke([(ox - 2, cy), (ox + SK_P + 2, cy)], 1.6 * (1 - 0.5 * k), v=0.8 - 0.3 * k, dash=(10, 0.8 - 0.4 * k, 0.0))
                for x, a, ln in cuts:
                    c0 = (ox + x - math.cos(math.radians(a)) * ln / 2, cy - math.sin(math.radians(a)) * ln / 2 + 3 * k)
                    c1 = (ox + x + math.cos(math.radians(a)) * ln / 2, cy + math.sin(math.radians(a)) * ln / 2 + 3 * k)
                    Lb.stroke([c0, c1], 1.2 * (1 - 0.5 * k), v=0.75 - 0.35 * k, dash=(6, 0.7 - 0.3 * k, 0.2))
                rr = random.Random(seed + i)
                for m in range(3):
                    x = ox + (m * 21 + 7) % SK_P
                    W.flake(Lf, x, cy - 4 + 10 * k + rr.uniform(-2, 2), 1.3, m, v=0.8 - 0.3 * k)
                    if k < 0.6:
                        W.ember(Le, x + 3, cy - 6 - 6 * k, 0.2, -1, 2.5, w=0.5, v=0.85)
        img = fr.render().crop((SK_P, 0, 2 * SK_P, H))
        out.append(img)
    return out


# =============================================================================
def specs():
    T = {}
    kg = K.body("player/v3/player_katana_guardbreak")
    T["katana_whirl_loop"] = dict(rows=["any"], ms=WH_MS, glow=[], fn=lambda d: whirl_loop(), anchor=K.PV, fit="pivot", loop=True, meta=K.pp_meta(
        weapon="katana", branch="회오리(旋渦) 2단 A-α", followPlayer=True, depth="above", spawn="spin_hold_continue",
        spawnNote="회전 베기 홀드를 이어 갈 때(최대 1.5초) katana_spin 1회 뒤 이 루프를 홀드 끝까지 반복. 손을 떼면 마지막 칸에서 끔(잔상은 katana_spin decay 재사용 가능)",
        hitTiming="루프 240ms 마다 f0 시작 = 판정 1회(초당 약 4타 ×0.5 — 설계안 2.2, 시스템 데이터)", loopRange=[0, 5],
        hitShape=dict(type="ring", radiusPx=160, note="반경 2.5칸(katana_spin 과 같음) 참고값"),
        reflectFx="fx/v3/katana_whirl_reflect", groundKy=K.KY,
        design="몸 둘레를 시계 방향으로 도는 열린 붓획 두 개(150°씩, 180° 엇갈림 — 닫힌 원 아님) + 안쪽 가는 바람 획 + 바깥으로 튀는 재. 백열 없음(초당 4타라 깜빡임 방지)"))
    T["katana_whirl_reflect"] = dict(rows=["any"], ms=RF_MS, glow=[0], fn=lambda d: whirl_reflect(), anchor=K.CO, fit="center", meta=dict(
        weapon="katana", branch="회오리(旋渦) 2단 A-α", anchor="projectile", rotate=True, drawnFacing="right", flipY="allowed", depth="above",
        spawn="projectile_reflected", spawnNote="회오리 회전 중 적 투사체를 되받아칠 때 그 투사체 자리에 1회 — 그림 오른쪽 = 되돌아 나가는 방향",
        impactFrame=0, frameRoles=["받아 침(핵 백열)", "되돌아 나감", "흩어짐", "재", "재"],
        design="되받는 짧은 호 붓획 + 되돌아 나가는 호박 줄 세 갈래 + 재"))
    T["katana_moon_trail"] = dict(rows=["any"], ms=MT_MS, glow=[], fn=lambda d: moon_trail(), anchor=(60, 40), fit="center", meta=dict(
        weapon="katana", branch="잔월(殘月) 2단 A-β", anchor="path_point", rotate=True, drawnFacing="right", flipY="allowed", depth="below_player",
        anchorNote="pivot = 궤적 위 한 점. 검기를 쓴 일섬(katana_issen_dash 선)·회전 베기(원 둘레)가 지나간 자리를 따라 48 도트 간격으로 하나씩 놓고, "
                   "그 자리의 진행 방향 각도로 회전(초승달 긴 쪽이 궤적을 따라감)",
        spawn="ki_spent_path", loopRange=[2, 5], tickFrame=2,
        lifeRule="f0~f1 생김(100ms) → f2~f5 루프(300ms = 0.3초 틱 1회, 1.2초면 3회 반복) → f6~f8 사라짐(280ms). 지속 1.2초·0.3초마다 ×0.3(설계안 2.2) — 시스템 데이터",
        hitShape=dict(type="circle", radiusPx=26, note="초승달 하나 = 반경 26 도트 판정(참고값). 겹친 초승달끼리는 같은 적 한 틱 1회 권장"),
        frameRoles=["생김", "생김", "틱(밝음)", "루프", "루프", "루프", "사라짐", "사라짐", "재"],
        design="바닥에 눕힌 호박 초승달(흙 그림자) — 루프 동안 밝은 점이 달을 따라 돌고 틱 순간 양끝 반짝, 사라질 때 재로 부서짐. 백열 없음"))
    T["katana_cleave_crack"] = dict(rows=K.DIRS4, ms=CL_MS, glow=[], fn=cleave_line, anchor=K.PV, fit="pivot", meta=K.pp_meta(
        weapon="katana", branch="일도양단(一刀兩斷) 2단 B-α", anchor="release_pivot", bodySheet="player_katana_guardbreak", dirTransform="drawn4",
        anchorNote="katana_guardbreak fx 와 같은 자리(좌클릭을 뗀 순간 주인공 발, 따라가지 않음)·같은 4행. 균열은 내려베기 땅 가름 끝(3칸)에서 시작해 4칸 더",
        spawn="body_ms", spawnAtMs=kg["timingMs"]["hitAt"] + 40, spawnNote="katana_guardbreak fx 가 3칸 끝까지 갈라진 순간(몸 hitAt + 40ms)에 1회",
        hitShape=dict(type="rect", fromPx=CL_X0, lengthPx=CL_L, halfWidthPx=24, frontPxByFrame=[CL_X0 + 64 * (n + 1) for n in range(4)], activeFrames=[0, 1, 2, 3],
                      damageScale=1.2, executeBelowHp=0.3, note="설계안 2.2: 직선 균열 4칸 ×1.2, HP 30% 이하 일반 적 처형(→ katana_execute). 판정 원점 기준 도트 — 참고값"),
        frameRoles=["1칸", "2칸", "3칸", "4칸(끝)", "다 갈라짐", "식음", "식음", "식음", "재"],
        holdLast="마지막 칸을 붙잡아 오래 남기려면 시스템이 끄는 시점을 정함(반투명 금지)", shakeHint={"px": 5, "ms": 140},
        design="땅 가름 끝에서 곧게 4칸 더 달리는 굵은 호박 금(흙 테·가지 금 7) + 솟았다 떨어지는 돌 조각, 앞머리 흙먼지·불티"))
    T["katana_execute"] = dict(rows=["any"], ms=EX_MS, glow=[0, 1], fn=lambda d: execute(), anchor=(100, 140), fit="pivot", meta=dict(
        weapon="katana", branch="일도양단(一刀兩斷) 2단 B-α", anchor="hitbox_center", followTarget=False, depth="above", spawn="execute",
        spawnNote="HP 30% 이하 일반 적을 내려베기·균열로 처형하는 순간 그 적 히트박스 중심에 1회(적은 이 시트 f2부터 사라지게 — 시스템 처리). 보스·엘리트는 처형 대신 피해 ×1.5(이 시트 없음)",
        impactFrame=0, hitstopHint=80, shakeHint={"px": 4, "ms": 120},
        frameRoles=["세로 한 줄(백열)", "붓획 + 가로 一 + 별(백열)", "두 쪽으로 갈라짐", "갈라짐", "재", "재", "재"],
        design="적을 세로로 가르는 붓 한 줄과 가로 一 자 — 두 쪽이 양옆으로 벌어지며 재로 부서지고 불티가 흩어짐, 발밑 짧은 금"))
    T["katana_mirror_ki"] = dict(rows=["1", "2", "3", "4", "5"], ms=MK_MS, glow=[], fn=lambda d: mirror_ki(int(d)), anchor=K.PV, fit="pivot", loop=True,
                                 meta=K.pp_meta(
        weapon="katana", branch="명경(明鏡) 2단 B-β — 검기 상한 5단", rowsAre="stacks", followPlayer=True, depth="below_player",
        rowNote="행 = 검기 단수 1~5(방향 무관). 무기 위 검기 오버레이(_ki1~3)는 그대로 쓰고, 4·5단은 오버레이 _ki3 + 이 발밑 고리로 구분",
        spawn="ki_changed", spawnNote="명경 런에서 검기가 1단 이상이면 상시 루프(단수가 바뀌면 같은 프레임 번호로 행만 바꿈), 0단이면 끔",
        cloneRule="검기 5단 일섬(대쉬 일섬 katana_issen_dash) = 분신 2체: katana_issen_shadow 를 두 번 — 1체는 그대로, 2체는 spawnAtMs +90ms·"
                  "일섬 선과 수직으로 ±24 도트 비켜서(설계안 2.2). 피해 규칙은 시스템 데이터",
        frameRoles=["루프"] * 6,
        design="발밑 타원 위 다섯 개의 작은 초승달(달 모양) — 찬 단수만큼 호박으로 켜지고 하나씩 돌아가며 반짝, 5단이면 가는 점선 고리로 이어짐. 빈 칸은 어두운 재"))
    T["katana_mirror_parry"] = dict(rows=["any"], ms=MP_MS, glow=[0, 1], fn=lambda d: mirror_parry(), anchor=K.CO, fit="center", meta=dict(
        weapon="katana", branch="명경(明鏡) 2단 B-β — 패링 시 검기 2단 충전", anchor="guard_contact", rotate=True, drawnFacing="right", flipY="allowed",
        depth="above", spawn="parry_success", spawnNote="명경 런에서 패링 성공 순간 guard_perfect_fx(parry 행)와 함께 1회 — 그림 오른쪽 = 공격이 들어온 쪽",
        impactFrame=0, frameRoles=["거울 면(백열)", "거울 면 · 큰 별(백열)", "두 조각이 주인공 쪽으로", "날아옴", "닿음", "재"],
        design="맞닿은 자리에 선 세로 거울 면(가는 재 테 + 호박 + 몇 도트 백열)이 두 초승달 조각으로 갈라져 주인공 쪽으로 날아듦 = 검기 2단"))
    T["greatsword_quake_fork"] = dict(rows=["any"], ms=QF_MS, glow=[], fn=lambda d: quake_fork(), anchor=K.CO, fit="center", meta=dict(
        weapon="greatsword", branch="지진(地震) 2단 A-α", anchor="crack_end", rotate=True, drawnFacing="right", flipY="allowed", depth="above",
        anchorNote="pivot = 파쇄 균열(greatsword_shatter_crack_tN) 앞머리가 멈춘 끝점 — 그 균열과 같은 각도로 회전",
        spawn="crack_front_end", spawnNote="지진 런에서 파쇄 균열 앞머리가 끝에 닿은 순간 1회. 공중제비 착지 균열 1줄은 greatsword_shatter_crack_t2 를 착지점·조준 방향으로 재사용",
        hitShape=dict(type="rays", anglesDeg=[-25, 0, 25], lengthPx=2 * K.TILE, halfWidthPx=20, frontPxByFrame=[44, 88, 128], activeFrames=[0, 1, 2],
                      damageScale=0.6, note="설계안 2.3 갈래 ±25°·각 ×0.6 — 길이 2칸은 아트 제안, 참고값"),
        frameRoles=["갈라짐", "갈라짐", "2칸(끝)", "다 갈라짐", "식음", "식음", "식음", "식음", "재"],
        design="균열 끝에서 −25°·0°·+25° 세 갈래로 다시 터져 나가는 호박 금(흙 테·가지 금·돌 조각·흙먼지)"))
    T["greatsword_echo_counter"] = dict(rows=["any"], ms=EC_MS, glow=[0], fn=lambda d: echo_counter(), anchor=K.CO, fit="center", meta=dict(
        weapon="greatsword", branch="반향(反響) 2단 A-β — 울분 30% 소모 균열 반격", anchor="player_pivot_ground", rotate=True, drawnFacing="right",
        flipY="allowed", depth="above", anchorNote="pivot = 주인공 발(바닥). 그림 오른쪽 = 막은 방향(주인공 → 공격자 각도)",
        spawn="perfect_guard", spawnNote="반향 런에서 퍼펙트 가드 순간 울분 30% 이상이면 guard_perfect_fx(guard 행)와 함께 1회(30% 미만이면 없음)",
        impactFrame=0, hitShape=dict(type="rect", fromPx=34, lengthPx=3 * K.TILE, halfWidthPx=26, frontPxByFrame=[98, 162, 226], activeFrames=[0, 1, 2],
                                     note="반격 = 차지 1단 위력(설계안 2.3), 3칸 — 참고값"),
        frameRoles=["메아리 호(백열 몇 도트) · 균열 시작", "1칸", "2칸", "3칸(끝)", "식음", "식음", "식음", "재"],
        design="막은 자리에서 앞으로 퍼지는 메아리 호 두 겹 + 땅이 되받아치듯 앞으로 3칸 달리는 균열"))
    T["greatsword_giant_ring"] = dict(rows=["lv4"], ms=[40, 50, 60, 70, 80, 80, 90, 100, 120], glow=[0, 1], fn=lambda d: giant_ring(), anchor=K.PV,
                                      fit="pivot", meta=dict(
        weapon="greatsword", branch="거인(巨人) 2단 B-α — 차지 4단", anchor="slam_point", rotate=False, depth="below_player", groundKy=K.KY, rowsAre="stages",
        anchorNote="greatsword_quake_ring(중압 lv1~3) 와 같은 규격·같은 점(몸 slamAnchors[행][impactFrame]) — 행 lv4 하나(반경 5칸)",
        spawn="body_ms", spawnNote="거인 런에서 차지 4단(1.6초) 휘둘러 내리찍기 impactFrame 시작에 1회",
        radiusPx=5 * K.TILE, hitFrames=[0, 1, 2], pullFrames=[3, 4, 5],
        hitShape=dict(type="ring", radiusPx=5 * K.TILE, note="설계안 2.3 '4단 ×3.8·진동 반경 5칸' — 참고값"),
        reuse="branch57/bfx.quake_frames(5.0) — 중압 진동 그림의 4단 크기판", design="중압 원형 진동의 5칸 판(퍼짐 → 끌어당김 → 가라앉음)"))
    T["greatsword_charge_flash_lv4"] = dict(rows=["any"], ms=CF4_MS, glow=[0, 1], fn=lambda d: charge_flash4(), anchor=(80, 80), fit="center", meta=dict(
        weapon="greatsword", branch="거인(巨人) 2단 B-α — 차지 4단 도달", anchor="blade_tip",
        anchorNote="무기 weapons/v3/greatsword_charge 의 bladeTipAnchors[행][지금 프레임](무기 시트 좌표 → 주인공 피벗 + playerFrameOffset). 행 any",
        depth="above", spawn="charge_stage_reached", stage=4,
        spawnNote="greatsword_charge_flash_lv1~3 처럼 차지 4단(1.6초) 도달 순간 1회. 거인 런에서 차지 중 받는 피해 −50%·끊기지 않음 표시는 greatsword_brace_absorb 재사용",
        frameRoles=["점화(백열)", "큰 별 + 고리(백열)", "호박 별", "수축", "수축", "사라짐"],
        design="칼끝에서 터지는 8빛살 겹별(lv3 보다 큼) + 고리 + 사방 불티"))
    T["greatsword_congest_aura"] = dict(rows=["any"], ms=CA_MS, glow=[], fn=lambda d: congest_aura(), anchor=K.PV, fit="pivot", loop=True, meta=K.pp_meta(
        weapon="greatsword", branch="울혈(鬱血) 2단 B-β — 그로기 중 울분 맺힘", followPlayer=True, depth="below_player",
        spawn="groggy_start", spawnNote="울혈 런에서 그로기 동안 루프(750ms × 2 = 그로기 1.5초), player_groggy_swirl 과 함께. 그로기 중 퍼펙트 가드 창 2배는 시스템",
        frameRoles=["맥동 루프"] * 6,
        design="발밑 어두운 웅덩이에서 뻗는 호박 혈관 금 7줄이 맥박처럼 밝아졌다 어두워지고, 가는 재 연기·불티가 오름"))
    T["greatsword_congest_burst"] = dict(rows=["any"], ms=CB_MS, glow=[0, 1], fn=lambda d: congest_burst(), anchor=K.PV, fit="pivot", meta=K.pp_meta(
        weapon="greatsword", branch="울혈(鬱血) 2단 B-β — 그로기 풀리는 순간 자동 진동 폭발", depth="above", spawn="groggy_end_full_grudge",
        spawnNote="울혈 런에서 그로기가 풀리는 순간 울분 100%면 1회(울분 전부 소모)", impactFrame=0, radiusPx=CB_R,
        hitShape=dict(type="ring", radiusPx=CB_R, note="폭발 = 차지 2단 위력(설계안 2.3), 반경 2.25칸 — 아트 제안 참고값"), shakeHint={"px": 7, "ms": 180},
        frameRoles=["핵(백열)", "0.7R(판정)", "1.0R", "식음 · 연기 기둥", "식음", "식음", "재", "재"],
        design="허리 높이 핵 → 열린 붓 고리 4조각 + 방사 가시가 퍼지고 몸 높이 불기둥 · 흙먼지 → 연기 기둥과 재 조각"))
    T["dagger_frenzy_clone_in"] = dict(rows=K.DIRS4, ms=FC_IN_MS, glow=[], fn=None, anchor=K.PV, fit="pivot", meta=K.pp_meta(
        weapon="dagger", branch="난무(亂舞) 2단 A-α — 분신 상주 3초", anchor="clone_pivot", depth="같은 Y 정렬(주인공처럼)",
        anchorNote="pivot = 분신의 발. 분신은 낙인 5스택 기폭 뒤 주인공 맞은편(대상 적 건너편)에 3초 상주", spawn="brand_detonate_5",
        cloneRender="상주 분신 = 주인공 단검 몸·무기 시트를 shadowPalette 로 색 교체해 반대편에서 같은 프레임 재생(설계안 2.4 '연격을 반대편에서 따라 함'). "
                    "등장·소멸만 이 시트",
        frameRoles=["재가 모임", "모임", "형태", "완성(상주 분신으로 넘김)"],
        design="재 조각이 모여 어두운 단검 분신(그림자 재 · 호박 금 절반)이 위로 차오름, 발밑 그림자"))
    T["dagger_frenzy_clone_out"] = dict(rows=K.DIRS4, ms=FC_OUT_MS, glow=[], fn=None, anchor=K.PV, fit="pivot", meta=K.pp_meta(
        weapon="dagger", branch="난무(亂舞) 2단 A-α — 분신 소멸", anchor="clone_pivot", depth="같은 Y 정렬(주인공처럼)", spawn="clone_expire",
        frameRoles=["부서짐 시작", "부서짐", "부서짐", "거의", "재"], design="상주 분신이 발부터 재로 부서져 위로 흩어짐"))
    T["dagger_brand_bleed"] = dict(rows=["any"], ms=BB_MS, glow=[], fn=lambda d: brand_bleed(), anchor=(48, 56), fit="pivot", loop=True, meta=dict(
        weapon="dagger", branch="출혈(出血) 2단 A-β — 기폭 = 즉시 60% + 4초 출혈", anchor="hitbox_center", followTarget=True, depth="above",
        spawn="brand_bleed_start", spawnNote="출혈 런에서 낙인 기폭 순간부터 4초 루프(dagger_brand_burst 뒤). 출혈 0.5초 틱마다 같은 시트 그대로(틱 표시는 피격 번쩍임 — 시스템)",
        frameRoles=["루프"] * 6, transferFx="fx/v3/dagger_brand_hop",
        design="몸에 남은 낙인 획 세 줄에서 호박빛 피가 방울로 뚝뚝 떨어지는 루프(공용 bleed 보다 굵은 낙인 획)"))
    T["dagger_brand_hop"] = dict(rows=["any"], ms=BH_MS, glow=[], fn=lambda d: brand_hop(), anchor=(60, 24), fit="center", loop=True, meta=dict(
        weapon="dagger", branch="출혈(出血) 2단 A-β — 출혈 중 처치 시 낙인이 반경 3칸 적 1명에게 옮겨감", anchor="projectile", rotate=True,
        drawnFacing="right", flipY="allowed", depth="above", anim="loop_move", spawn="brand_transfer",
        spawnNote="죽은 적 → 새 적으로 시스템이 이동(약 0.2초 권장), 도착하면 dagger_brand_mark 스택 행 stamp",
        frameRoles=["날아감 루프"] * 4, design="X 낙인 한 개가 호박 꼬리 줄을 끌며 날아감"))
    T["dagger_stuck_blade"] = dict(rows=["any"], ms=SB_MS, glow=[], fn=None, anchor=(60, 70), fit="pivot", meta=dict(
        weapon="dagger", branch="비도(飛刀) 2단 B-α — 박힌 단검 2초 · 그 위치로 그림자 걸음", anchor="ground_point", rotate=False, flipX="allowed",
        depth="Y 정렬(바닥 위 물체)", anchorNote="pivot = 단검이 박힌 바닥 점. 회전하지 않고 세워 그림 — 던진 방향이 왼쪽이면 flipX",
        spawn="thrown_land", loopRange=[2, 5], endFrames=[6, 7],
        lifeRule="f0~f1 박힘 → f2~f5 루프(2초 동안) → 수명 끝·그 위치로 그림자 걸음 시 f6~f7 재로 부서짐. 그림자 걸음 도착은 shadowstep_ghost 재사용",
        reuse="단검 그림 = fx/v3/dagger_thrown f0 를 촉 아래로 세워 촉 38% 를 땅에 묻음(같은 송곳니)",
        frameRoles=["박힘 · 흙먼지 · 불티", "가라앉음", "반짝임 오름(루프)", "루프", "루프(별)", "루프", "재로", "재"],
        design="땅에 비스듬히 꽂힌 재 송곳니 단검 + 작은 패임, 날을 타고 오르는 호박 반짝임"))
    T["dagger_hotwind_trail"] = dict(rows=K.DIRS4, ms=HT_MS, glow=[], fn=hotwind_trail, anchor=K.PV, fit="pivot", loop=True, meta=K.pp_meta(
        weapon="dagger", branch="열풍(熱風) 2단 B-β — 과열 50% 이상 이동·공속 +20%", followPlayer=True, depth="below_player", spawn="heat_over_50",
        spawnNote="열풍 런에서 과열 50% 이상이고 이동 중이면 루프(행 = 이동 방향), 멈추거나 50% 미만이면 끔",
        frameRoles=["루프"] * 4, design="발 뒤로 흘러가는 낮은 불혀 일곱 갈래 + 열 아지랑이 두 줄"))
    T["dagger_hotwind_burst"] = dict(rows=["any"], ms=HB_MS, glow=[0, 1], fn=lambda d: hotwind_burst(), anchor=K.PV, fit="pivot", meta=K.pp_meta(
        weapon="dagger", branch="열풍(熱風) 2단 B-β — 과열 100% 폭발 ×2·화상·무적 0.5초", depth="above", spawn="overheat_100",
        replaces="fx/v3/dagger_overheat_burst", replaceRule="열풍 런에서만 과열 폭발 fx 를 이 시트로(반경 ×2 = 184 도트). 맞은 적에 status_burn 3초",
        impactFrame=0, radiusPx=HB_R, hitShape=dict(type="ring", radiusPx=HB_R, note="dagger_overheat_burst radiusPx 92 ×2(설계안 2.4) — 참고값"),
        invulnMs=500, shakeHint={"px": 6, "ms": 170},
        frameRoles=["핵(백열)", "0.6R(판정 · 백열 획 머리)", "1.0R", "불혀 · 그을음", "식음", "식음", "재", "재", "재"],
        design="열린 붓 고리 6조각이 반경 184 도트까지 퍼지고 바깥으로 눕는 불혀 18 + 그을린 바닥 고리 + 재·불티"))
    T["bow_arrow_split"] = dict(rows=["any"], ms=SP_MS, glow=[0], fn=lambda d: arrow_split(), anchor=(60, 40), fit="center", meta=dict(
        weapon="bow", branch="연궁(連弓) 2단 A-α — 연사 3발마다 1발 2갈래 분열", anchor="projectile", rotate=True, drawnFacing="right", flipY="allowed",
        depth="above", spawn="arrow_split", spawnNote="분열하는 순간 그 화살 자리에 1회. 갈라진 화살은 bow_arrow_rapid(각 ×0.3, ±12°)",
        impactFrame=0, splitDeg=[-12, 12], frameRoles=["갈라짐(백열 별)", "Y 획", "Y 획 · 불티", "재"],
        design="한 줄이 Y 자 두 붓획으로 갈라지며 갈림목에 작은 별"))
    T["bow_arrow_stuck"] = dict(rows=["any"], ms=[40, 50, 150, 150, 150, 150, 80, 100], glow=[], fn=None, anchor=(60, 70), fit="pivot", meta=dict(
        weapon="bow", branch="무한통(無限筒) 2단 A-β — 박힌 화살을 밟으면 회수", anchor="ground_point", rotate=False, flipX="allowed",
        depth="Y 정렬(바닥 위 물체)", spawn="arrow_land", loopRange=[2, 5], endFrames=[6, 7],
        lifeRule="빗나간 화살이 땅에 떨어진 자리에 f0~f1 → 루프(줍기 전까지·수명은 시스템) → 밟으면 bow_arrow_recall + 이 시트 f6~f7",
        reuse="화살 그림 = fx/v3/bow_arrow f0 를 세워 촉을 묻음", frameRoles=["박힘", "가라앉음", "반짝(루프)", "루프", "루프(별)", "루프", "재로", "재"],
        design="땅에 꽂힌 재 화살 + 작은 패임, 화살대를 타고 오르는 반짝임"))
    T["bow_arrow_recall"] = dict(rows=["any"], ms=AR_MS, glow=[], fn=lambda d: arrow_recall(), anchor=(48, 88), fit="pivot", meta=dict(
        weapon="bow", branch="무한통(無限筒) 2단 A-β — 처치 시 화살 +3 · 밟으면 +1", anchor="ground_point", depth="above", spawn="arrow_recovered",
        spawnNote="박힌 화살을 밟은 자리 · 처치한 적 발밑에 1회(처치 +3 이면 한 번만)",
        frameRoles=["고리 · 불씨 오름", "별", "오름", "오름", "흩어짐", "사라짐"],
        design="바닥 점선 고리가 퍼지며 호박 불씨 다섯 개가 위로 솟아 사라짐(화살이 화살통으로 돌아감)"))
    T["bow_deadeye_scope"] = dict(rows=["any"], ms=DE_MS, glow=[], fn=lambda d: deadeye_scope(), anchor=(64, 64), fit="none", meta=dict(
        weapon="bow", branch="필중(必中) 2단 B-α — 정밀 조준 1.2→2.0초", anchor="aim_cursor", depth="above", progressDriven=True,
        progressRule="f0~f5 = 정밀 조준 진행도(frame = min(5, floor(p × 5))), 다 차면 f6~f9 루프(loopRange). 이 동안 완벽 놓기 = 치명 확정 — 섬광은 bow_perfect_release",
        loopRange=[6, 9], spawn="precision_aim",
        frameRoles=["0%", "20%", "40%", "60%", "80%", "가득", "루프", "루프", "루프", "루프"],
        design="커서 위 괄호 네 개가 돌며 좁혀 들고 바깥 눈금, 다 좁혀지면 가운데 점이 맥박"))
    T["bow_link_stack"] = dict(rows=["1", "2", "3"], ms=LS_MS, glow=[], fn=lambda d: link_stack(int(d)), anchor=K.PV, fit="pivot", loop=True, meta=K.pp_meta(
        weapon="bow", branch="천공(穿空) 2단 B-β — 완벽 놓기 연결 스택", rowsAre="stacks", followPlayer=True, depth="below_player",
        spawn="link_changed", spawnNote="연결 1스택 이상이면 상시 루프(행 = 스택), 놓치면 0 → 끔",
        frameRoles=["루프"] * 6, design="발밑 타원 위 화살촉 세 개가 시계 방향으로 이어짐 — 스택만큼 호박으로 켜짐, 3이면 점선 고리"))
    T["bow_skypierce_line"] = dict(rows=["any"], ms=SK_MS, glow=[4], fn=lambda d: skypierce_line(), anchor=(0, 24), fit="none", edge_ok=True, meta=dict(
        weapon="bow", branch="천공(穿空) 2단 B-β — 3스택 화살 벽 관통 + 지나간 선이 늦게 터짐", tile=True, tileAxis="x", tilePeriodPx=SK_P,
        anchor="line_start", rotate=True, drawnFacing="right", depth="above",
        anchorNote="pivot = 선 시작(발사점) 쪽 타일 왼쪽 가운데. 화살이 지나간 선(벽 너머 포함)을 64 도트 타일로 이어 깔고 진행 각도로 회전 — telegraph_line 같은 반복 타일(트림 안 함)",
        spawn="pierce3_arrow_path", burstFrame=4, burstAtMs=sum(SK_MS[:4]),
        hitShape=dict(type="line", halfWidthPx=16, damageScale=0.8, atMs=500, note="0.5초 뒤 선 전체 ×0.8(설계안 2.5) — 참고값"),
        frameRoles=["남은 선(루프 느낌)", "남은 선", "남은 선", "남은 선", "터짐(백열 심)", "재", "재", "재"],
        design="화살이 지나간 가는 호박 선 위로 반짝임이 흐르다 0.5초에 굵게 터지며 비스듬한 베인 자국이 남고 재로 부서짐(칼 일섬 선 연출 재사용 방향)"))
    return T


NAMES = ["katana_whirl_loop", "katana_whirl_reflect", "katana_moon_trail", "katana_cleave_crack", "katana_execute", "katana_mirror_ki",
         "katana_mirror_parry", "greatsword_quake_fork", "greatsword_echo_counter", "greatsword_giant_ring", "greatsword_charge_flash_lv4",
         "greatsword_congest_aura", "greatsword_congest_burst", "dagger_frenzy_clone_in", "dagger_frenzy_clone_out", "dagger_brand_bleed",
         "dagger_brand_hop", "dagger_stuck_blade", "dagger_hotwind_trail", "dagger_hotwind_burst", "bow_arrow_split", "bow_arrow_stuck",
         "bow_arrow_recall", "bow_deadeye_scope", "bow_link_stack", "bow_skypierce_line"]


def _src_projectile(rel):
    j, fr = K.grid_frames(rel)
    return fr[j["directions"][0]][0]


def job(name):
    sp = specs()[name]
    if name in ("dagger_frenzy_clone_in", "dagger_frenzy_clone_out"):
        _, body = K.grid_frames("player/v3/player_idle")
        wj, weap = K.grid_frames("weapons/v3/dagger_carry_idle")
        dep = wj.get("depth")
        weap["_depth"] = dep if isinstance(dep, dict) else ({"up": "below"} if dep is None else {})
        frames = {d: frenzy_clone(d, body, weap, out_=name.endswith("out")) for d in sp["rows"]}
    elif name == "dagger_stuck_blade":
        frames = {"any": stuck_blade(_src_projectile("fx/v3/dagger_thrown"))}
    elif name == "bow_arrow_stuck":
        frames = {"any": stuck_blade(_src_projectile("fx/v3/bow_arrow"), seed=6021, ms=sp["ms"], kind="arrow")}
    else:
        frames = {d: sp["fn"](d) for d in sp["rows"]}
    meta = dict(sp["meta"])
    if name == "dagger_frenzy_clone_in":
        meta["shadowPalette"] = shadow_palette()
        meta["shadowPaletteNote"] = "주인공 v3 30색 → 분신 색(밝기 순서 유지 · 호박 금은 A17~A23). 시스템 런타임 색 교체(계약 §2 팔레트 교체와 같은 방식)로 상주 분신을 그린다"
    res = K.write(name, frames, sp["rows"], sp["ms"], sp["glow"], sp["anchor"], fit=sp["fit"], meta=meta, src=SRC, loop=sp.get("loop", False),
                  edge_ok=sp.get("edge_ok", False))
    if meta.get("anchor") == "player_pivot" and sp["fit"] == "pivot":
        import fx_combo
        fx_combo._hit_origin(name)
    return res
