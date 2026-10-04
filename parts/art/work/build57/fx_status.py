"""상태·세트·저주 표시 fx (설계안 1.4 세트 효과 · 1.6 패시브 · 취기 A안 · 4.2 저주 · 6.2 상태·공용 fx).

  status_mark          표식 1~3(표식 태그 — 행 = 스택)            status_burn       화상(루프)
  status_boil          끓음(출혈+화상 폭발, 상흔 4)               set_stasis_wave   정적 발동(간파 6 — 적·탄 감속 파동)
  status_slowed        정적 감속 중 표시(적·탄 루프)              pool_liquor       술 웅덩이(취기)
  pool_liquor_fire     술불(취기 6 — 대쉬 점화·번짐)              status_drunk      취기 상태(머리 위 술 김 루프)
  drunk_sway           취보 '휘청'(취기 4 — 확정 1회 흘림)         endure_last_stand 버팀 6(HP 0 버팀)
  chain_bloodlust      연쇄 6 '살기' 5초(루프)                     set_flash         세트 단계 발동 섬광(행 = 2·4·6, 태그 공용)
  dual_trait_get       이중 개성 획득                              perfect_dodge     완벽 회피 섬광(4행 = 대쉬 방향)
  curse_mark           저주 상태 표시(행 = 저주 7종, 머리 위)
불 웅덩이(잔불 심장)는 fx/v3/fire_pool(보스 '불붙은 술') 재사용 — 계약 메모 참고.
"""
import math
import random

from PIL import Image

import kit as K
from kit import W, FK, BR

SRC = "parts/art/work/build57/build.py status (57라운드 상태·세트·저주 표시 fx)"


def _embers(L, cx, cy, n, dist, k, seed, up=True, length=3.0):
    r = random.Random(seed)
    for _ in range(n):
        a = r.uniform(-2.8, -0.35) if up else r.uniform(0, 6.28)
        d = dist * r.uniform(0.4, 1.0) * (0.5 + k)
        W.ember(L, cx + math.cos(a) * d, cy + math.sin(a) * d + 6 * k * k, math.cos(a), math.sin(a), length * (1 - 0.5 * k), w=0.6, v=0.9 - 0.35 * k)


def _flames(L, base, i, seed, n, hmin, hmax, spread, w=2.0, ky=0.4):
    """작은 불혀 n개(base = 중심, spread = 가로 반폭) — 프레임마다 키·흔들림이 바뀜(루프 4프레임 위상)."""
    cx, cy = base
    for j in range(n):
        u = (j + 0.5) / n
        x = cx - spread + 2 * spread * u + 3 * math.sin(j * 2.1)
        y = cy + (math.sin(j * 1.7) * spread * ky * 0.4)
        ph = (i / 4 + W.h2(j, 3, seed)) % 1.0
        hh = hmin + (hmax - hmin) * (0.5 + 0.5 * math.sin(2 * math.pi * ph))
        sway = 2.2 * math.sin(2 * math.pi * ph + j)
        pts = [(x + sway * t * t, y - hh * t) for t in [m / 6 for m in range(7)]]
        L.stroke(pts, w, prof=FK.tp_tail(0.85), v=0.95, vprof=lambda t: 1 - 0.45 * t)


# =============================================================================
MK_MS = [40, 70, 120, 120, 120, 120]


def mark(n):
    cx, cy = 24, 22
    out = []
    for i in range(6):
        fr = K.frame(48, 44)
        Lo = fr.L([K.B0, K.B1])
        La = fr.L([K.A19, K.A21, K.A23, K.A25])
        s = [11, 8.5, 7, 7, 7, 7][i]
        v = [1.0, 0.95, 0.8, 0.88, 0.8, 0.74][i]
        dia = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy), (cx, cy - s)]
        Lo.stroke(dia, 1.7, v=0.9)
        La.stroke(dia, 0.8, v=v, dash=(9.5, 0.82, 0.12))
        La.stamp(cx, cy, 1.0, v, soft=0)
        for m in range(n):                           # 셈 획(아래)
            x = cx - (n - 1) * 3 + 6 * m
            Lo.stroke([(x - 1, cy + s + 4), (x + 1, cy + s + 10)], 1.4, v=0.9)
            La.stroke([(x - 1, cy + s + 4), (x + 1, cy + s + 10)], 0.6, v=1.0 if (i == 0 and m == n - 1) else 0.85)
        out.append(fr.render())
    return out


BURN_MS = [110] * 4


def burn(seed=6201):
    out = []
    for i in range(4):
        fr = K.frame(96, 112)
        Lf = fr.L([K.A18, K.A19, K.A21, K.A23, K.A25])
        Le = fr.L(K.EMB)
        for j, (x, y, hh) in enumerate(((30, 74, 16), (52, 62, 22), (66, 80, 14), (42, 46, 12), (60, 40, 10))):
            ph = (i / 4 + 0.27 * j) % 1.0
            h_ = hh * (0.7 + 0.3 * math.sin(2 * math.pi * ph))
            sw = 2 * math.sin(2 * math.pi * ph + j)
            pts = [(x + sw * t * t, y - h_ * t) for t in [m / 6 for m in range(7)]]
            Lf.stroke(pts, 2.6 - 0.25 * j, prof=FK.tp_tail(0.85), v=0.95, vprof=lambda t: 1 - 0.5 * t)
        r = random.Random(seed + i)
        for m in range(3):
            x = r.uniform(26, 70)
            y = 30 - ((i * 9 + m * 13) % 26)
            W.ember(Le, x, y, 0, -1, 2.5, w=0.55, v=0.85)
        out.append(fr.render())
    return out


BOIL_MS = [40, 40, 50, 60, 70, 80, 100, 120]


def boil(seed=6211):
    cx, cy = 80, 84
    R = 96.0
    r = random.Random(seed)
    blobs = [(r.uniform(0, 6.28), r.uniform(0.5, 1.0), r.uniform(2.0, 3.6)) for _ in range(14)]
    out = []
    for i in range(len(BOIL_MS)):
        fr = K.frame(200, 180)
        Ls = fr.L([K.S0, K.S1, K.S2])
        Lr = fr.L([K.A17, K.A18, K.A19])
        Lb = fr.L([K.A18, K.A19, K.A21, K.A23, K.A25])
        Lh = fr.L(K.HOT)
        k = 0.0 if i <= 2 else (i - 2) / 5
        prog = [0.2, 0.6, 1.0][i] if i <= 2 else 1.0
        if i == 0:
            Lh.stamp(cx, cy, 4.5, 1.0, soft=0.4)
            Lb.disc(cx, cy, 12, 10, v=0.9)
        if i <= 3:
            rr = R * prog * 0.5
            Lr.arc(cx, cy, rr, rr * 0.75, 0, 2 * math.pi, 2.0 - 0.3 * i, v=0.9, dash=(9, 0.7, 0.1 * i))
        for a, f, sz in blobs:                       # 끓어 튀는 방울
            d = R * 0.5 * f * min(1.0, (i + 1) / 3) * (1 + 0.2 * k)
            x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.75 - 18 * f * math.sin(math.pi * min(1, (i + 1) / 5)) + 14 * k * k
            if k > 0.75:
                continue
            Lb.stamp(x, y, sz * (1 - 0.5 * k), 0.95 - 0.35 * k, soft=0.35)
            if i == 1:
                Lh.put(x, y - 1, 1.0)
        if i >= 2:
            for j in range(3):
                ph = i + j * 2
                pts = [(cx - 16 + 16 * j + 3 * math.sin(ph + u * 4), cy - 10 - 60 * u * (0.5 + 0.5 * k)) for u in [m / 10 for m in range(11)]]
                Ls.stroke(pts, 1.3 - 0.5 * k, prof=lambda u: 0.5 + 0.5 * math.sin(math.pi * u), v=0.8 - 0.3 * k, dash=(8, 0.6, 0.2 * j + 0.1 * i))
        out.append(fr.render())
    return out


STW_MS = [40, 50, 60, 70, 80, 100, 120, 140, 160]


def stasis_wave():
    cx, cy = K.PV
    out = []
    for i in range(len(STW_MS)):
        fr = K.frame()
        Lg = fr.L([K.S0, K.S1, K.S2, K.S3])
        La = fr.L([K.A19, K.A21, K.A23])
        Lh = fr.L(K.HOT)
        k = i / 8
        r1 = 50 + 330 * (1 - (1 - min(1.0, i / 5)) ** 2)
        if i == 0:
            Lh.star4(cx, cy - 60, 12, w=0.9, v=1.0, diag=0.5)
        Lg.arc(cx, cy, r1, r1 * K.KY, 0, 2 * math.pi, 1.2 * (1 - 0.5 * k), v=0.95 - 0.4 * k, dash=(24, 0.7, 0.0))
        r2 = r1 * 0.66
        Lg.arc(cx, cy, r2, r2 * K.KY, 0, 2 * math.pi, 0.8, v=0.7 - 0.3 * k, dash=(16, 0.4, 0.5))
        for m in range(12):                          # 시계 눈금
            a = math.radians(30 * m)
            L = La if m % 3 == 0 else Lg
            p0 = K.ell(cx, cy, 30 * m, r1 - 6)
            p1 = K.ell(cx, cy, 30 * m, r1 + 6)
            L.stroke([p0, p1], 0.8, v=0.9 - 0.4 * k)
        if i >= 1:                                   # 바늘(멈칫)
            ang = -90 + [0, 30, 30, 36, 36, 36, 40, 40, 40][i]
            p1 = K.ell(cx, cy, ang, 40, z=0)
            La.stroke([(cx, cy), p1], 1.0, prof=FK.tp_tail(0.7), v=0.85 - 0.3 * k)
        out.append(fr.render())
    return out


SLW_MS = [120] * 6


def slowed():
    cx, cy = 32, 20
    out = []
    for i in range(6):
        fr = K.frame(64, 40)
        Lg = fr.L([K.S0, K.S1, K.S2])
        La = fr.L([K.A19, K.A21])
        ph = i / 6
        Lg.arc(cx, cy, 24, 11, 0, 2 * math.pi, 0.8, v=0.9, dash=(8, 0.45, ph))
        Lg.arc(cx, cy, 16, 7, 0, 2 * math.pi, 0.6, v=0.7, dash=(6, 0.35, -ph * 1.5))
        a = 2 * math.pi * ph
        La.stamp(cx + math.cos(a) * 24, cy + math.sin(a) * 11, 1.1, 1.0, soft=0)
        out.append(fr.render())
    return out


# =============================================================================
# 술 웅덩이 · 술불
# =============================================================================
PL_MS = [60, 70, 80, 140, 140, 140, 140, 100, 120, 140]
PL_RX, PL_RY = 64.0, 28.0


def _pool_shape(rx, ry, seed):
    r = random.Random(seed)
    lobes = [(r.uniform(0, 6.28), r.uniform(0.025, 0.06), r.randint(3, 7)) for _ in range(4)]

    def rad(a):
        return 1.0 + sum(amp * math.sin(n * a + ph) for ph, amp, n in lobes)
    return rad


def pool_frames(seed=6301, fire=False):
    cx, cy = 80, 60 if not fire else 80
    rad = _pool_shape(PL_RX, PL_RY, seed)
    ms = PF_MS if fire else PL_MS
    out = []
    for i in range(len(ms)):
        H = 120 if fire else 80
        fr = K.frame(160, H)
        Lp = fr.L([K.A17, K.A18, K.A19, K.A21])
        Lr = fr.L([K.A21, K.A23, K.A25])
        Ll = fr.L([K.A18, K.A19, K.A21, K.A23, K.A25])
        Le = fr.L(K.EMB_HI)
        Lh = fr.L(K.HOT)
        if not fire:
            g = [0.35, 0.7, 0.95, 1, 1, 1, 1, 0.9, 0.7, 0.45][i]
            dry = [0, 0, 0, 0, 0, 0, 0, 0.3, 0.6, 0.85][i]
        else:
            g, dry = 1.0, [0, 0, 0, 0, 0, 0, 0.3, 0.55, 0.8][i]
        rx, ry = PL_RX * g, PL_RY * g
        for y in range(int(cy - ry * 1.3) - 2, int(cy + ry * 1.3) + 3):
            for x in range(int(cx - rx * 1.3) - 2, int(cx + rx * 1.3) + 3):
                dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                q = math.hypot(dx, dy) / rad(math.atan2(dy, dx))
                if q > 1.0:
                    continue
                if dry and W.h2(x >> 1, y >> 1, seed + 3) < dry * (0.4 + 0.8 * q):
                    continue
                v = 0.15 if q > 0.88 else 0.4 + (0.22 if math.hypot(dx / 0.72, (dy + 0.32) / 0.4) < 1.0 else 0) + (0.12 if (x + y) % 2 and q < 0.45 else 0)
                if fire:
                    v = min(0.99, v + 0.3)
                Lp.put(x, y, v)
        # 흐르는 빛 띠(물결) + 반짝임
        if i >= 1 and dry < 0.6:
            for j in range(2):
                ph = (i * 0.35 + j * 0.5) % 1.0
                yy = cy - ry * 0.35 + ry * 0.55 * j
                x0 = cx - rx * 0.55 + rx * 0.3 * ph
                Lr.stroke([(x0, yy), (x0 + rx * 0.45, yy + 1)], 0.6, prof=FK.tp_both(0.6, 0.5), v=0.75)
            gx = cx - rx * 0.4 + (i * 13) % int(max(1, rx * 0.8))
            Lr.put(gx, cy - ry * 0.45, 1.0)
        if fire:
            if i == 0:
                Lh.star4(cx, cy - 6, 8, w=0.8, v=1.0)
                _flames(Ll, (cx, cy), i, seed, 5, 8, 14, rx * 0.5)
            elif i <= 5:
                _flames(Ll, (cx, cy - 2), i, seed, 7, 20, 38, rx * 0.75, w=4.4)
                _flames(Ll, (cx, cy + 8), i + 2, seed + 1, 5, 10, 20, rx * 0.6, w=2.6)
                _embers(Le, cx, cy - 30, 3, 20, 0.2, seed + i)
            else:
                k = (i - 5) / 3
                _flames(Ll, (cx, cy), i, seed, 5, 6 * (1 - k), 14 * (1 - k), rx * 0.6, w=1.8)
        out.append(fr.render())
    return out


PF_MS = [40, 60, 100, 100, 100, 100, 100, 120, 140]


# =============================================================================
# 취기 — 머리 위 술 김 · 휘청
# =============================================================================
DR_MS = [120] * 6


def drunk():
    cx, cy = 40, 64
    out = []
    for i in range(6):
        fr = K.frame(80, 80)
        Ls = fr.L([K.S1, K.S2, K.S3])
        La = fr.L([K.A21, K.A23])
        for j in range(2):
            ph = i / 6 * 2 * math.pi + j * 2.4
            x0 = cx - 8 + 16 * j
            pts = [(x0 + 4 * math.sin(ph + u * 5) * (0.4 + u), cy - 6 - 40 * u) for u in [m / 12 for m in range(13)]]
            Ls.stroke(pts, 1.3, prof=lambda u: 0.5 + 0.5 * math.sin(math.pi * min(1, u * 1.2)), v=0.95, vprof=lambda u: 1 - 0.55 * u,
                      dash=(9, 0.7, (i / 6 + j * 0.4) % 1))
        for m in range(3):                         # 떠오르는 거품(호박)
            y = cy - ((i * 7 + m * 14) % 40)
            x = cx - 10 + 10 * m + 2 * math.sin(i + m)
            La.put(x, y, 1.0 if m == 1 else 0.7)
            if (i + m) % 3 == 0:
                La.put(x + 1, y, 0.7)
        out.append(fr.render())
    return out


SW_MS = [30, 40, 50, 60, 70, 80, 90, 100]


def sway(seed=6401):
    cx, cy = K.PV
    out = []
    for i in range(len(SW_MS)):
        fr = K.frame()
        Ll = fr.L(K.LIQ)
        Lb = fr.L(K.INK_K)
        Lh = fr.L(K.HOT)
        Ld = fr.L([K.A19, K.A21, K.A23])
        k = i / 7
        pts = []
        for m in range(41):                       # 발밑 S 자 흘림(바닥 타원 위)
            u = m / 40
            a = 200 + 280 * u
            r = 44 + 14 * math.sin(u * math.pi * 2)
            pts.append(K.ell(cx, cy, a, r, ky=0.45))
        S = BR.Stroke(pts, 5.0, seed=seed, peak=0.4, dry_from=0.6, split=1.8, drops=6, start_w=0.1, end_w=0.5)
        if i == 0:
            S.draw(Lb, head=0.45, vmax=0.8, drops=False)
            Lh.star4(cx, cy - 70, 7, w=0.7, v=1.0)
        elif i <= 2:
            S.draw(Lb, head=1.0 if i == 2 else 0.8, vmax=0.88, drops=(i == 2))
        else:
            S.draw(Lb, head=1.0, tail=0.1 + 0.8 * k, vmax=0.85 - 0.3 * k, k=k, fall=4 * k)
        r = random.Random(seed)
        for m in range(10):                       # 튀는 술방울
            a = r.uniform(-3.0, -0.1)
            sp = r.uniform(30, 60)
            t = min(1.0, (i + 1) / 6)
            x = cx + math.cos(a) * sp * t
            y = cy - 50 + math.sin(a) * sp * t * 0.7 + 50 * t * t
            if i >= 7 and m % 2:
                continue
            Ll.stamp(x, y, 1.6 * (1 - 0.4 * k), 0.95 - 0.3 * k, soft=0.3)
            Ld.put(x, y - 1, 0.8 - 0.3 * k)
        out.append(fr.render())
    return out


# =============================================================================
# 버팀 6 · 연쇄 6 살기 · 세트 섬광 · 이중 개성 · 완벽 회피
# =============================================================================
LS_MS = [40, 40, 50, 60, 70, 80, 90, 100, 120, 140]


def last_stand(seed=6501):
    cx, cy = K.PV
    r = random.Random(seed)
    shards = [(r.uniform(0, 6.28), r.uniform(0.2, 1.0), r.uniform(2.0, 3.6)) for _ in range(26)]
    out = []
    for i in range(len(LS_MS)):
        fr = K.frame()
        Lsh = fr.L([K.K2, K.S0, K.S1, K.S2])
        Lc = fr.L([K.A19, K.A21, K.A23, K.A25])
        Lp = fr.L([K.A21, K.A23, K.A25])
        Lg = fr.L([K.B0, K.B1, K.A18])
        Lh = fr.L(K.HOT)
        k = 0.0 if i <= 2 else (i - 2) / 7
        if i <= 1:                                 # 재 고치(몸을 감쌈)
            for a, f, sz in shards:
                x = cx + math.cos(a) * 30 * (0.6 + 0.4 * f)
                y = cy - 60 + math.sin(a) * 66 * (0.6 + 0.4 * f) * (1 if i else 1.15)
                W.flake(Lsh, x, y, sz, a, v=0.9)
            if i == 1:
                for m in range(5):
                    a = math.radians(-90 + 72 * m)
                    Lc.stroke(W.jag(r, (cx, cy - 60), (cx + math.cos(a) * 30, cy - 60 + math.sin(a) * 60), n=4, amp=3), 0.8, v=1.0)
                Lh.stamp(cx, cy - 60, 3.0, 1.0, soft=0.4)
        else:
            for a, f, sz in shards:                # 터져 나감 → 떨어짐
                d = 30 + 90 * f * (1 - (1 - k) ** 2)
                x = cx + math.cos(a) * d
                y = cy - 60 + math.sin(a) * d * 0.8 + 70 * k * k
                if y > cy + 6 or (k > 0.8 and W.h2(int(a * 100), 1, seed) < 0.5):
                    continue
                W.flake(Lsh, x, y, sz * (1 - 0.3 * k), a + i, v=0.85 - 0.25 * k)
            if i <= 4:                             # 빛기둥(짧게)
                wpx = {2: 3.2, 3: 2.0, 4: 1.0}[i]
                Lp.stroke([(cx, cy + 2), (cx, cy - 150)], wpx, prof=FK.tp_tail(0.5), v=0.95 - 0.3 * k, dash=(14, 0.8 - 0.15 * (i - 2), 0.1) if i > 2 else None)
                if i == 2:
                    Lh.stroke([(cx, cy - 20), (cx, cy - 110)], 1.2, v=1.0)
            Lg.arc(cx, cy, 40 + 20 * k, (40 + 20 * k) * 0.45, 0, 2 * math.pi, 1.4, v=0.8 - 0.4 * k, dash=(12, 0.7, 0.2))
            if k < 0.8:
                _embers(Lc, cx, cy - 60, 8, 50, k, seed + i)
        out.append(fr.render())
    return out


BL_MS = [90] * 6


def bloodlust(seed=6601):
    cx, cy = K.PV
    out = []
    for i in range(6):
        fr = K.frame()
        Ld = fr.L([K.K0, K.A17, K.A18])
        La = fr.L([K.A18, K.A19, K.A21, K.A23])
        for m in range(10):                        # 발밑에서 솟는 날카로운 기운(갈퀴)
            a = 36 * m + 12 * math.sin(m)
            ph = (i / 6 + 0.3 * m) % 1.0
            base = K.ell(cx, cy, a, 34, ky=0.45)
            hh = 26 + 30 * math.sin(math.pi * ph)
            lean = 6 * math.cos(math.radians(a))
            pts = [(base[0] + lean * t, base[1] - hh * t) for t in [n / 6 for n in range(7)]]
            Ld.stroke(pts, 2.6, prof=FK.tp_tail(0.8), v=0.95)
            La.stroke(pts, 1.1, prof=FK.tp_tail(0.8), v=0.6 + 0.4 * math.sin(math.pi * ph))
        for m in range(2):                         # 허리 높이 도는 베인 자국
            a0 = 60 * i + 180 * m
            pts = K.ring_pts(cx, cy - 56, 46, a0, a0 + 70, ky=0.5)
            La.stroke(pts, 1.0, prof=FK.tp_both(0.6, 0.5), v=0.95)
        out.append(fr.render())
    return out


SF_MS = [30, 40, 50, 60, 70, 80, 90, 110]


def set_flash(stage, seed=6701):
    cx, cy = K.PV
    sc = {2: 0.7, 4: 0.9, 6: 1.15}[stage]
    rays = {2: 4, 4: 8, 6: 12}[stage]
    out = []
    for i in range(len(SF_MS)):
        fr = K.frame()
        Lg = fr.L([K.A17, K.A18, K.A19])
        La = fr.L([K.A19, K.A21, K.A23, K.A25])
        Lh = fr.L(K.HOT)
        k = i / 7
        rr = (30 + 70 * min(1.0, i / 3)) * sc
        La.arc(cx, cy, rr, rr * 0.45, 0, 2 * math.pi, 1.4 * (1 - 0.6 * k), v=0.95 - 0.4 * k, dash=(rays * 2, 0.6, 0.0))
        if stage == 6 and i >= 1:
            r2 = rr * 0.7
            Lg.arc(cx, cy, r2, r2 * 0.45, 0, 2 * math.pi, 0.9, v=0.8 - 0.4 * k, dash=(rays, 0.4, 0.5))
        for m in range(rays):
            a = 360 * m / rays
            p0 = K.ell(cx, cy, a, rr * 0.4, ky=0.45)
            p1 = K.ell(cx, cy, a, rr * (1.05 + 0.1 * (m % 2)), ky=0.45)
            if i <= 4:
                La.stroke([p0, p1], 0.9, prof=FK.tp_both(0.5, 0.6), v=0.9 - 0.15 * i)
        if i <= 2:                                # 빛기둥(짧게)
            wpx = (1.6 + 0.6 * (stage // 2)) * (1 - 0.3 * i) * sc
            La.stroke([(cx, cy + 2), (cx, cy - 160 * sc - 20)], wpx, prof=FK.tp_tail(0.6), v=0.95 - 0.12 * i)
            if i <= 1:
                Lh.stroke([(cx, cy - 10), (cx, cy - 120 * sc)], 0.9, v=1.0)
                Lh.star4(cx, cy - 140 * sc, 6 + 3 * stage / 2, w=0.8, v=1.0, diag=0.45 if stage >= 4 else 0)
        if i >= 2:
            _embers(La, cx, cy - 60, 3 + stage, 40 * sc, k, seed + i + stage)
        out.append(fr.render())
    return out


DT_MS = [40, 40, 50, 50, 60, 60, 70, 80, 90, 100, 110, 120]


def dual_trait(seed=6801):
    cx, cy = K.PV
    out = []
    H = 170.0
    for i in range(len(DT_MS)):
        fr = K.frame()
        Lb = fr.L(K.INK_K)
        Lg = fr.L([K.S0, K.S1, K.S2, K.S3])
        Lh = fr.L(K.HOT)
        Le = fr.L(K.EMB_HI)
        prog = min(1.0, (i + 1) / 7)
        for j, L in enumerate((Lb, Lg)):
            pts = []
            for m in range(81):
                u = m / 80
                if u > prog:
                    break
                a = 2 * math.pi * (1.6 * u) + math.pi * j
                rad = 40 * (1 - 0.75 * u)
                pts.append((cx + math.cos(a) * rad, cy - H * u + math.sin(a) * rad * 0.4))
            if len(pts) >= 3 and i <= 7:
                S = BR.Stroke(pts, 4.0 if j == 0 else 3.0, seed=seed + j, peak=0.7, dry_from=0.4, split=1.3, drops=0, start_w=0.2, end_w=0.7, lanes=5)
                S.draw(L, head=1.0, tail=max(0.0, (i - 4) * 0.15), vmax=0.9, drops=False)
        if i in (7, 8):
            Lh.star4(cx, cy - H - 6, 16 if i == 7 else 12, w=1.0, v=1.0, diag=0.55)
            Lb.ring(cx, cy - H - 6, 10 + 6 * (i - 7), 0.8, v=0.9)
        if i >= 8:
            k = (i - 8) / 3
            r = random.Random(seed + i)
            for m in range(10):
                x = cx + r.uniform(-30, 30)
                y = cy - H + 20 + 120 * k * r.uniform(0.6, 1.2)
                Le.put(x, y, 0.95 - 0.3 * k)
                if m % 3 == 0:
                    Le.put(x, y - 1, 0.6)
        out.append(fr.render())
    return out


PD_MS = [30, 40, 50, 60, 70, 90]


def perfect_dodge(d, dash_rows, seed=6901):
    t = K.TA(d, K.PV)
    sil_src = dash_rows[d][1]
    out = []
    for i in range(len(PD_MS)):
        img = Image.new("RGBA", (K.CANVAS, K.CANVAS), (0, 0, 0, 0))
        sil = K.silhouette(sil_src, "ash", erode=[0.0, 0.15, 0.35, 0.55, 0.75, 0.92][i], seed=seed + i, hot_frac=0.4)
        img.alpha_composite(sil, (K.PV[0] - 48, K.PV[1] - 138))
        fr = K.frame()
        Lg = fr.L([K.S1, K.S2, K.S3])
        La = fr.L([K.A21, K.A23, K.A25])
        Lh = fr.L(K.HOT)
        k = i / 5
        # 몸 옆을 스치는 가는 섬광 선(대쉬 방향과 나란히, 몸 높이)
        for s in (-1, 1):
            p0 = t((-30 - 10 * i, s * 22))
            p1 = t((60 + 20 * i, s * 22))
            L = La
            L.stroke([(p0[0], p0[1] - 70), (p1[0], p1[1] - 70)], 0.8 * (1 - 0.5 * k), prof=FK.tp_both(0.6, 0.6), v=1.0 - 0.4 * k,
                     dash=(30, 0.8 - 0.4 * k, 0.1 * s) if i >= 3 else None)
        if i <= 1:
            Lh.star4(K.PV[0], K.PV[1] - 70, 10 + 4 * i, w=0.9, v=1.0, diag=0.5)
        else:
            r = random.Random(seed + i)
            for m in range(8):
                W.flake(Lg, K.PV[0] + r.uniform(-30, 30), K.PV[1] - r.uniform(10, 130) - 10 * k, r.uniform(1.0, 2.0), m, v=0.85 - 0.3 * k)
        img.alpha_composite(fr.render())
        out.append(img)
    return out


# =============================================================================
# 저주 표시 — 16×16 도트 그림을 2배(32×32)로, 아래에 공용 어두운 재 연기 고리(저주 공통 표지)
# =============================================================================
PAL = {"k": K.K0, "d": K.S0, "g": K.S1, "G": K.S2, "L": K.S3, "r": K.A17, "R": K.A18, "a": K.A19, "o": K.A21, "y": K.A23, "w": K.A25,
       "b": K.B1, "B": K.B2, "c": K.B3}
ICONS = {
    "drunk_oath": [          # 만취 서약 — 기울어진 잔에서 넘치는 술
        "................",
        "..........yo....",
        ".........yoo....",
        "...kkkkkkoya....",
        "..kGLLLLGka.....",
        "..kGoyyoGk......",
        "..kgoooogk..o...",
        "...kgaaagk..a...",
        "...kGgggGk......",
        "....kkkkk...o...",
        ".....kgk........",
        ".....kgk....a...",
        "....kGLGk.......",
        "...kgggggk......",
        "...kkkkkkk......",
        "................"],
    "debt": [                # 외상 — 장부 쪽지 + 그어진 셈 획 + 금 간 동전
        "................",
        "..kkkkkkkk......",
        "..kLLLLLLk......",
        "..kLagaLLk......",
        "..kLaLaLLk......",
        "..kLaLaaak......",
        "..kLLLLLLk......",
        "..kLagagak......",
        "..kLLLLLLkkkk...",
        "..kkkkkkkoyyok..",
        ".........kyokyk.",
        "........kyoykok.",
        "........koyk.ak.",
        ".........kaoak..",
        "..........kkk...",
        "................"],
    "broken_cup": [          # 깨진 잔 — 금 간 잔, 떨어지는 조각
        "................",
        "..kkkkkkkkk.....",
        "..kGLLkLLGk.....",
        "..kgGLyLGgk..k..",
        "...kgGoGgk..kG..",
        "...kgGkyGk..k...",
        "....kgoGk.......",
        "....kgkGk...kk..",
        ".....kGk...kGk..",
        ".....kgk....k...",
        ".....kgk........",
        "....kGLGk.......",
        "...kgg.ggk......",
        "...kkk.kkk......",
        "................",
        "................"],
    "burning_tongue": [      # 불붙은 혀 — 혀 끝이 불꽃
        "......y.........",
        ".....yo...y.....",
        ".....ow..yo.....",
        "....oyw.yo......",
        "....aoyyoa......",
        "....kaooak......",
        "...krRaaRrk.....",
        "...kRaRRaRk.....",
        "...kRRaaRRk.....",
        "...kRRbbRRk.....",
        "....kRbbRk......",
        "....kRRRRk......",
        ".....kRRk.......",
        "......kk........",
        "................",
        "................"],
    "bare_hand": [           # 맨손 맹세 — 펼친 손바닥(빈손)
        "................",
        "......k.k.......",
        ".....kGkGkk.....",
        "..k..kGkGkGk....",
        ".kGk.kGkGkGk....",
        ".kGk.kGkGkGk....",
        ".kGGkkGkGkGk....",
        "..kGGLLLLLGk....",
        "..kGLLLoLLGk....",
        "...kGLoyoLGk....",
        "...kGLLoLLk.....",
        "....kGLLLGk.....",
        "....kgGGGgk.....",
        ".....kgggk......",
        ".....kkkkk......",
        "................"],
    "cursed_chest": [        # 저주 궤짝 — 사슬 감긴 작은 궤짝, 틈의 호박 빛
        "................",
        "...kkkkkkkkkk...",
        "..kBcccccccBk...",
        "..kBccBBBccBk...",
        "..kkkkkkkkkkk...",
        "..kyoyoyoyoyk...",
        "..kkkkkkkkkkk...",
        "..kBccBkkBcBk...",
        "..kBcGkLLkcBk...",
        "..kBcGkaakcBk...",
        "..kBcBGkkGcBk...",
        "..kBccBBBccBk...",
        "..kkkkkkkkkkk...",
        "...G.G.G.G.G....",
        "................",
        "................"],
    "bruise": [              # 피멍 — 어두운 멍 자국(번진 테), 가운데 짓눌린 호박 금
        "................",
        "......kkkk......",
        "....kkrrrRkk....",
        "...krrRaaRrrk...",
        "..krRaarraRRrk..",
        "..krarrkkrraRk..",
        ".krRarkdgkrarrk.",
        ".krRarkgdkraRrk.",
        ".krrRarkkrarRrk.",
        "..krRaarraRrrk..",
        "..krrRRaaRrrk...",
        "...kkrrRRrrkk...",
        ".....kkkkkk.....",
        "................",
        "................",
        "................"],
}
CURSES = ["drunk_oath", "debt", "broken_cup", "burning_tongue", "bare_hand", "cursed_chest", "bruise"]
CURSE_KO = {"drunk_oath": "만취 서약", "debt": "외상", "broken_cup": "깨진 잔", "burning_tongue": "불붙은 혀", "bare_hand": "맨손 맹세",
            "cursed_chest": "저주 궤짝", "bruise": "피멍"}
CM_MS = [120] * 6


def curse(kind):
    rows = ICONS[kind]
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), kind
    icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = icon.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                px[x, y] = FK.hexrgb(PAL[ch]) + (255,)
    icon2 = icon.resize((32, 32), Image.NEAREST)
    out = []
    bob = [0, -1, -2, -2, -1, 0]
    for i in range(6):
        fr = K.frame(56, 64)
        Ls = fr.L([K.K1, K.S0, K.S1])
        La = fr.L([K.A18, K.A19])
        cx, cy = 28, 54
        for j in range(2):                         # 공용 저주 표지: 아래로 감도는 어두운 연기 두 가닥
            ph = i / 6 * 2 * math.pi + j * math.pi
            pts = [(cx + 13 * math.cos(ph + u * 4.0) * (1 - 0.3 * u), cy - 4 * math.sin(ph + u * 4.0) - 10 * u) for u in [m / 14 for m in range(15)]]
            Ls.stroke(pts, 1.4, prof=lambda u: 0.4 + 0.6 * math.sin(math.pi * u), v=0.95)
        La.put(cx + 13 * math.cos(i / 6 * 2 * math.pi), cy - 4 * math.sin(i / 6 * 2 * math.pi), 1.0)
        img = fr.render()
        img.alpha_composite(icon2, (12, 10 + bob[i]))
        out.append(img)
    return out


# =============================================================================
def specs():
    T = {}
    T["status_mark"] = dict(rows=["1", "2", "3"], ms=MK_MS, glow=[], fn=lambda d: mark(int(d)), anchor=(24, 44), fit="pivot", meta=dict(
        tag="표식", rowsAre="stacks", anchor="enemy_head", followTarget=True, depth="above", loopRange=[2, 5],
        spawn="mark_stack_changed", spawnNote="표식이 오를 때마다 그 행 f0~f1 1회 → f2~f5 루프. 표식이 옮겨가면(표식 4) 새 적에 같은 행 stamp, 기폭(표식 6)·사망 때 지움. "
                                             "단검 낙인(dagger_brand_mark)과 같은 적에 겹치면 이 시트를 위로 18 도트",
        anchorNote="pivot = 마름모 아래 셈 획 밑(적 머리 위 enemy_head)", frameRoles=["찍힘(크게)", "줄어듦", "루프", "루프", "루프", "루프"],
        design="적 머리 위 호박 점선 마름모(분필 표적) + 아래 셈 획 1~3(새 획만 A25)"))
    T["status_burn"] = dict(rows=["any"], ms=BURN_MS, glow=[], fn=lambda d: burn(), anchor=(48, 80), fit="pivot", loop=True, meta=dict(
        tag="상흔", anchor="hitbox_center", followTarget=True, depth="above", spawn="burn_start",
        spawnNote="화상 상태 동안 루프(열풍 폭발·불붙은 혀·불붙은 소매 등 화상 공용). 끝나면 끔. 출혈(bleed)과 함께면 둘 다 — 끓음 조건",
        frameRoles=["루프"] * 4, design="몸에 붙은 작은 불혀 다섯 개가 일렁이고 불티가 오름(술불 지형과 달리 '적에게 걸린 상태')"))
    T["status_boil"] = dict(rows=["any"], ms=BOIL_MS, glow=[0, 1], fn=lambda d: boil(), anchor=(80, 84), fit="pivot", meta=dict(
        tag="상흔 4 '끓음'", anchor="hitbox_center", followTarget=False, depth="above", spawn="boil",
        spawnNote="출혈+화상이 함께 걸린 적의 남은 지속 피해가 즉시 터지는 순간 1회(설계안 1.4 상흔 4)", impactFrame=0, radiusPx=96,
        hitShape=dict(type="circle", radiusPx=96, note="반경 1.5칸 — 참고값"),
        frameRoles=["핵(백열)", "끓어 튐(백열 방울 몇 점)", "퍼짐", "김", "김", "방울 떨어짐", "김", "재"],
        design="몸 가운데서 호박 방울이 끓어 튀고 어두운 고리가 퍼진 뒤 김이 오름"))
    T["set_stasis_wave"] = dict(rows=["any"], ms=STW_MS, glow=[0], fn=lambda d: stasis_wave(), anchor=K.PV, fit="pivot", meta=K.pp_meta(
        tag="간파 6 '정적'", followPlayer=False, depth="below_player", spawn="stasis_start",
        spawnNote="완벽 성공 3회째에 1회 — 정적 1초(적·탄 40% 감속) 시작. 감속 중 적·탄 표시는 status_slowed. 화면 전체 연출(색 빼기 등)은 시스템 선택",
        frameRoles=["발동(별 백열)", "퍼짐", "퍼짐", "퍼짐", "퍼짐", "최대", "멈칫", "멈칫", "사라짐"],
        design="발밑에서 재 점선 고리 두 겹과 시계 눈금 12개가 크게 퍼지고 가운데 바늘이 멈칫거림"))
    T["status_slowed"] = dict(rows=["any"], ms=SLW_MS, glow=[], fn=lambda d: slowed(), anchor=(32, 20), fit="center", loop=True, meta=dict(
        tag="간파 6 '정적'", anchor="hitbox_center", followTarget=True, depth="above", spawn="slowed",
        spawnNote="정적·그 밖 감속 상태의 적·적 투사체에 루프(투사체는 scale 0.6 권장)", frameRoles=["루프"] * 6,
        design="대상 둘레를 느리게 도는 재 점선 고리 두 겹 + 호박 점 하나(시계)"))
    T["pool_liquor"] = dict(rows=["any"], ms=PL_MS, glow=[], fn=lambda d: pool_frames(), anchor=(80, 60), fit="pivot", meta=dict(
        tag="취기", anchor="hitbox_center", depth="floor", scale="allowed", radiusPx=PL_RX, groundRy=PL_RY, loopRange=[3, 6], endFrames=[7, 9],
        spawn="liquor_pool", lifeRule="f0~f2 퍼짐 → f3~f6 루프(6초 — 시스템) → f7~f9 마름. 반경 1칸 = 64 도트(취기 6 '술바다' 1.2칸이면 scale 1.2)",
        spawnNote="취기 패시브 '엎지른 술'·세트 6 처치·독주 술통 파괴·보스 술 뿌리기·적 사망(독주 행상·술통 짐꾼) 자리. 불이 닿으면 pool_liquor_fire 로 교체(같은 피벗)",
        pivotNote="pivot = 웅덩이 중심(바닥). fire_pool·boss1_liquor_splash 와 같은 바닥 깊이",
        frameRoles=["퍼짐", "퍼짐", "퍼짐", "루프", "루프", "루프", "루프", "마름", "마름", "마름"],
        design="호박 술 웅덩이(울퉁불퉁한 가장자리 · 어두운 테 · 위쪽 밝음) 위로 흐르는 빛 띠 두 줄과 반짝임 한 점. 불은 없음"))
    T["pool_liquor_fire"] = dict(rows=["any"], ms=PF_MS, glow=[0], fn=lambda d: pool_frames(fire=True), anchor=(80, 80), fit="pivot", meta=dict(
        tag="취기 6 '술바다' — 술불", anchor="hitbox_center", depth="floor", scale="allowed", radiusPx=PL_RX, loopRange=[2, 5], endFrames=[6, 8],
        spawn="liquor_ignite", lifeRule="f0~f1 점화(f0 별만 백열) → f2~f5 루프(3초, 0.5초마다 ×0.3 지형 피해 — 시스템) → f6~f8 꺼짐(웅덩이도 마름)",
        spawnNote="취기 중 대쉬가 지나간 웅덩이·불 웅덩이·증류 화로 불 무기·화상 적이 닿으면 pool_liquor 를 이 시트로 교체. 1칸 안 이웃 웅덩이로 번질 때 그 웅덩이도 f0부터(번짐 지연은 시스템, 0.15초 권장)",
        frameRoles=["점화(백열 별)", "붙음", "루프", "루프", "루프", "루프", "꺼짐", "꺼짐", "꺼짐"],
        design="밝아진 술 웅덩이 위 낮은 불혀 15개가 일렁임(화상 상태 아님 — 지형 불), 불티"))
    T["status_drunk"] = dict(rows=["any"], ms=DR_MS, glow=[], fn=lambda d: drunk(), anchor=(40, 64), fit="pivot", loop=True, meta=dict(
        tag="취기 상태", anchor="player_head_top", followPlayer=True, depth="above",
        anchorNote="pivot = 주인공 머리 꼭대기(그로기 headTopAnchors 가 없는 동작은 주인공 피벗 위 %d 도트 — 58 Q2 1.25배 렌더면 그 배율 곱)" % K.HEAD_UP,
        spawn="drunk_state", spawnNote="취기 상태(세트 2 '한 잔' 5초·카운터 취기 n단 — HUD drunk)인 동안 루프. 그로기 소용돌이와 겹치면 이 시트를 끔(그로기 우선)",
        frameRoles=["루프"] * 6, design="머리 위로 꼬불꼬불 오르는 재빛 술 김 두 가닥 + 떠오르는 호박 거품"))
    T["drunk_sway"] = dict(rows=["any"], ms=SW_MS, glow=[0], fn=lambda d: sway(), anchor=K.PV, fit="pivot", meta=K.pp_meta(
        tag="취기 4 '취보' — 휘청", followPlayer=True, depth="above", spawn="drunk_sway",
        spawnNote="취기 중 처음 받는 공격 1회를 흘리는 순간(피해 0·0.4초 무적·반 칸 미끄러짐) 1회. 미끄러짐 이동은 시스템. '취권 반격' 0.6초 창 표시는 이 시트 f2~f7",
        impactFrame=0, frameRoles=["흘림(백열 별)", "S 자 흘림", "흘림 · 술방울", "마름", "마름", "마름", "마름", "재"],
        design="발밑을 S 자로 휘감는 붓획 + 사방으로 튀는 술방울 — 비틀거리며 흘려 낸 순간"))
    T["endure_last_stand"] = dict(rows=["any"], ms=LS_MS, glow=[1, 2], fn=lambda d: last_stand(), anchor=K.PV, fit="pivot", meta=K.pp_meta(
        tag="버팀 6 — HP 0 버팀(층당 1회)", followPlayer=True, depth="above", spawn="last_stand",
        spawnNote="HP 0 → HP 25% 로 버티는 순간 1회(1초 무적). 패시브 '마지막 잔'(HP 1/10/25%)도 같은 시트",
        frameRoles=["재 고치", "고치 금(백열 핵)", "터짐 · 빛기둥(백열)", "조각", "조각", "조각", "조각", "떨어짐", "떨어짐", "재"],
        design="몸을 감싼 재 껍데기에 호박 금이 가고 터져 나가며 빛기둥이 솟음 — 조각이 떨어지고 발밑 고리"))
    T["chain_bloodlust"] = dict(rows=["any"], ms=BL_MS, glow=[], fn=lambda d: bloodlust(), anchor=K.PV, fit="pivot", loop=True, meta=K.pp_meta(
        tag="연쇄 6 '살기' — 5초 피해 +25%·개성 ×2", followPlayer=True, depth="below_player", spawn="bloodlust",
        spawnNote="3초 안 3처치 순간 set_flash(6행)와 함께 시작해 5초 루프. 끝나면 끔",
        frameRoles=["루프"] * 6, design="발밑에서 갈퀴처럼 솟는 어두운 호박 기운 10줄 + 허리 높이를 도는 베인 자국 두 개"))
    T["set_flash"] = dict(rows=["2", "4", "6"], ms=SF_MS, glow=[0, 1], fn=lambda d: set_flash(int(d)), anchor=K.PV, fit="pivot", meta=K.pp_meta(
        tag="공용(10태그)", rowsAre="stages", followPlayer=True, depth="above", spawn="set_tier_reached",
        rowNote="행 = 세트 단계 2·4·6(태그 공용 — 태그 구분은 UI 아이콘·문구). 단계가 클수록 기둥·고리·빛살이 큼(빛살 4/8/12)",
        spawnNote="태그 점수가 2·4·6 임계를 처음 넘은 순간 1회(보상 화면에서 고른 뒤 전투 복귀 시 재생 권장)",
        frameRoles=["발동(백열 기둥·별)", "백열", "퍼짐", "퍼짐", "퍼짐", "불티", "불티", "사라짐"],
        design="발밑 점선 고리와 방사 빛살이 퍼지며 몸을 꿰는 빛기둥과 머리 위 별 — 6단계는 안쪽 고리 한 겹 더"))
    T["dual_trait_get"] = dict(rows=["any"], ms=DT_MS, glow=[7, 8], fn=lambda d: dual_trait(), anchor=K.PV, fit="pivot", meta=K.pp_meta(
        tag="이중 개성", followPlayer=True, depth="above", spawn="dual_trait_acquired",
        spawnNote="이중 개성을 고른 순간(보상 화면을 닫고 전투 복귀) 1회 — 갈래 하나(호박 붓)와 태그 하나(재 붓)가 감겨 오르는 그림",
        frameRoles=["감겨 오름"] * 7 + ["머리 위 맞닿음(백열 별)", "별(백열)", "불씨 떨어짐", "불씨", "사라짐"],
        design="호박 붓 한 줄과 재 붓 한 줄이 주인공을 나선으로 감으며 올라가 머리 위에서 만나 큰 별, 불씨가 내려앉음"))
    T["perfect_dodge"] = dict(rows=K.DIRS4, ms=PD_MS, glow=[0, 1], fn=None, anchor=K.PV, fit="pivot", meta=K.pp_meta(
        tag="간파(완벽 성공)", anchor="dodge_start_pivot", followPlayer=False, depth="above", dirTransform="drawn4",
        anchorNote="pivot = 완벽 회피가 일어난 순간의 주인공 발(따라가지 않음). 행 = 대쉬·그림자 걸음 방향",
        spawn="perfect_dodge", spawnNote="적 공격 판정 직전 0.15초 안 대쉬·그림자 걸음 순간 1회(패링·퍼펙트 가드·완벽 놓기와 같은 '완벽 성공' 사건)",
        heroSource="player/v3/player_dash 열 1(방향 행별) 실루엣",
        frameRoles=["섬광(백열 선·별)", "백열", "재 잔상", "재 잔상", "부서짐", "재"],
        design="남겨진 재 잔상 양옆을 대쉬 방향으로 스치는 가는 섬광 선 두 줄과 가슴 높이 별"))
    T["curse_mark"] = dict(rows=CURSES, ms=CM_MS, glow=[], fn=curse, anchor=(28, 60), fit="pivot", loop=True, meta=dict(
        rowsAre="kinds", kinds={k: CURSE_KO[k] for k in CURSES}, anchor="player_head_top", followPlayer=True, depth="above",
        anchorNote="pivot = 그림 아래 가운데. 주인공 머리 꼭대기(피벗 위 %d 도트) 위에 놓음 — status_drunk 와 겹치면 이 시트를 위로 24 도트" % K.HEAD_UP,
        spawn="curse_active", spawnNote="저주가 걸려 있는 동안 그 저주 행을 루프(동시 1개 — 57 Q22~Q37). 남은 노드 수는 HUD(UI) 몫",
        iconNote="16×16 도트 그림을 2배 확대(32×32)한 몸 위 표시 — UI 아이콘(assets/ui) 은 UI 파트가 따로 그린다",
        frameRoles=["루프(둥실)"] * 6,
        design="머리 위 작은 그림(만취 서약 기울어진 잔 · 외상 장부·금 간 동전 · 깨진 잔 · 불붙은 혀 · 맨손 · 사슬 궤짝 · 피멍) + 아래를 감도는 어두운 재 연기 두 가닥(저주 공통 표지)"))
    return T


NAMES = ["status_mark", "status_burn", "status_boil", "set_stasis_wave", "status_slowed", "pool_liquor", "pool_liquor_fire", "status_drunk",
         "drunk_sway", "endure_last_stand", "chain_bloodlust", "set_flash", "dual_trait_get", "perfect_dodge", "curse_mark"]


def job(name):
    sp = specs()[name]
    if name == "perfect_dodge":
        _, dash = K.grid_frames("player/v3/player_dash")
        frames = {d: perfect_dodge(d, dash) for d in sp["rows"]}
    else:
        frames = {d: sp["fn"](d) for d in sp["rows"]}
    res = K.write(name, frames, sp["rows"], sp["ms"], sp["glow"], sp["anchor"], fit=sp["fit"], meta=dict(sp["meta"]), src=SRC,
                  loop=sp.get("loop", False))
    if sp["meta"].get("anchor") == "player_pivot" and sp["fit"] == "pivot":
        import fx_combo
        fx_combo._hit_origin(name)
    return res
