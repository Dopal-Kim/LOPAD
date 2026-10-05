"""각성 fx — 시그니처 4종 재제작 · 각성 순간 전환 4종(새) · 각성 전용 궤적 19종(새, 기존 연격 fx 와 별개 시트).

  시그니처(기존 이름 교체, 프레임 수·ms·행·앵커·spawn 규칙은 57라운드 시트 그대로):
    katana_fullmoon        월인: 은빛 보름달 고리가 떠오르고 초승달 일섬 세 줄이 가로지른 뒤 달 조각으로 부서짐
    greatsword_landslide   핏빛: 현무암 가시 9개가 세 무리로 솟으며 가시마다 피가 뿜어 오르고, 4칸 균열에 피가 고였다 스밈(8방향)
    dagger_hundred_ghosts  귀화: 얼굴 달린 보라 도깨비불 셋이 날아들어 세 갈래 베기 → 청록 불티
    bow_meteor_arrow       혜성: 금빛 혜성 화살이 불꽃 깃을 끌고 떨어져 큰 별·불꽃 고리
  각성 순간 전환(새 키): <무기>_awaken_in — 주인공 머리 위에서 무기가 원래 색 → 각성 색으로 바뀌는 8×60ms + 머묾·사라짐
  각성 전용 궤적(새 키): <기본 fx>_awaken — 기본 연격 fx 와 같은 틀·프레임·ms·피벗(교체만 하면 됨), 그림은 각성 색·장식
"""
import json
import math
import os
import random
import sys

from PIL import Image

import prod_common as P
import kit60 as K6
from kit60 import Cv, F, G, A, SIL, CRI, VIO, TEAL, GOLD, X0, X1, INK, h2, vnoise, clamp, smooth
import katana as KM
import greatsword as GM
import dagger as DM
import bow as BM
import stage as ST
from concept import sparkle

K57 = P.K57
FA = None


def _fa():
    global FA
    if FA is None:
        import fx_awaken as m
        FA = m
    return FA


CANVAS = 1100
PV = K57.PV
KY = K57.KY
TILE = K57.TILE


def img(cv):
    return cv.image()


def write_fx(name, frames, rows, ms, anchor, meta, glow=(), fit="pivot", loop=False):
    if fit == "pivot":
        cut, pv = K57.rk.fit_frames(frames, anchor)
    elif fit == "center":
        cut, pv = K57.rk.fit_centered(frames, anchor)
    else:
        cut, pv = frames, anchor
    m = dict(meta)
    m["pivot"] = {"x": int(pv[0]), "y": int(pv[1])}
    j = P.write_sheet(name, P.STAGE_FX, rows, cut, ms, m, loop=loop, glow=list(glow))
    return name, j["frameWidth"], j["frameHeight"], j["colors"]


def old_meta(name, drop=("image", "action", "version", "frameWidth", "frameHeight", "framesPerDirection", "frames", "layout",
                         "frameIndex", "fps", "colors", "palette", "source", "semiTransparent", "atlas", "meta", "textures",
                         "paletteSwap", "paletteSwapNote", "pivot", "effectRule", "glowRule")):
    j = json.load(open(os.path.join(P.SPR, "fx/v3", name + ".json"), encoding="utf-8"))
    return {k: v for k, v in j.items() if k not in drop}, j


# =============================================================================
# 공용 그리기
# =============================================================================
def crescent_arc(cv, c, R, a0, a1, thick, ramp, core=None, z=0, seed=0, fade=0.0):
    """원(c, R) 위 a0 → a1 초승달 띠(머리 = a1 쪽 두꺼움). ramp = 어둠 → 밝음. fade 0..1 = 꼬리부터 픽셀이 빠짐."""
    span = a1 - a0

    def fn(tn, rn, x, y):
        th = 0.15 + 0.85 * math.sin(math.pi * min(1.0, tn * 1.05)) ** 0.7
        if rn < 1 - th:
            return None
        if fade > 0 and h2(x, y, seed) < fade * (1.2 - tn * 0.4):
            return None
        q = (rn - (1 - th)) / th
        if core and q > 0.86 and 0.3 < tn < 0.95:
            return core
        return ramp[min(len(ramp) - 1, int(q * len(ramp)))]
    cv.smear(c, R - thick, R, a0, a1, fn, z=z)


def glyph_moon(cv, x, y, z=3, big=False):
    g = [(0, 0, SIL[8]), (1, 0, SIL[10]), (2, 1, X1), (2, 2, SIL[9]), (1, 3, SIL[7]), (0, 3, SIL[5])]
    if big:
        g = [(0, 0, SIL[9]), (1, 0, SIL[10]), (2, 1, X1), (3, 2, X1), (3, 3, SIL[10]), (2, 4, SIL[8]), (1, 5, SIL[7]), (0, 5, SIL[6]),
             (1, 1, SIL[4]), (2, 2, SIL[4]), (2, 3, SIL[4]), (1, 4, SIL[4])]
    for dx, dy, c in g:
        cv.put(x + dx, y + dy, c, z, False)


def droplet(cv, x, y, big=False, z=2, glint=False):
    cv.put(x, y, X1 if glint else CRI[6], z, False)
    cv.put(x, y + 1, CRI[5], z, False)
    if big:
        cv.put(x + 1, y, CRI[6], z, False)
        cv.put(x + 1, y + 1, CRI[4], z, False)
        cv.put(x, y + 2, CRI[4], z, False)


def tri(cv, a, b, c, shade, z=0):
    """삼각 바위(a·b 밑변, c 꼭짓점): shade(side, up, edge) → 색."""
    xs = [a[0], b[0], c[0]]
    ys = [a[1], b[1], c[1]]
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    ax_, ay_ = c[0] - mx, c[1] - my
    alen = math.hypot(ax_, ay_) or 1
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            px, py = x + 0.5, y + 0.5
            s = []
            for p, q in ((a, b), (b, c), (c, a)):
                s.append(((q[0] - p[0]) * (py - p[1]) - (q[1] - p[1]) * (px - p[0])) / (math.hypot(q[0] - p[0], q[1] - p[1]) or 1))
            if all(v >= 0 for v in s) or all(v <= 0 for v in s):
                edge = min(abs(v) for v in s) < 1.0
                side = ax_ * (py - my) - ay_ * (px - mx)
                up = ((px - mx) * ax_ + (py - my) * ay_) / (alen * alen)
                cv.put(x, y, shade(side, up, edge, x, y), z, True)


# =============================================================================
# 시그니처 1 — katana_fullmoon (월인)
# =============================================================================
def fullmoon():
    FA_ = _fa()
    cx, cy = PV[0], PV[1] - 64
    R = 104
    out = []
    slashes = [(-35, 0.0), (20, 6.0), (-5, -5.0)]
    for i in range(len(FA_.FM_MS)):
        cv = Cv(CANVAS, CANVAS)
        grow = [0.35, 0.75, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0][i]
        k = 0.0 if i <= 4 else (i - 4) / 5
        rr = R * grow
        # 보름달 고리(두께 7) + 안쪽 성긴 달빛(체크 점) — 무너질 때 픽셀이 빠짐
        for y in range(int(cy - rr - 2), int(cy + rr + 3)):
            for x in range(int(cx - rr - 2), int(cx + rr + 3)):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d > rr:
                    continue
                if k > 0 and h2(x, y, 601) < k * 1.1:
                    continue
                if d > rr - 7:
                    q = (d - (rr - 7)) / 7
                    lit = (x - cx) * -0.6 + (y - cy) * -0.8 > 0
                    c = X1 if (q < 0.25 and i in (1, 2, 3)) else SIL[11] if (q < 0.45 and lit) else SIL[9] if q < 0.7 else SIL[5]
                    cv.put(x, y, c, 1, False)
                elif d > rr - 10:
                    cv.put(x, y, SIL[3], 0, False) if (x + y) % 2 == 0 else None
                elif i >= 1 and (x % 4 == 0 and y % 4 == (x // 4) % 2 * 2) and d < rr * 0.92:
                    cv.put(x, y, SIL[3] if d > rr * 0.5 else SIL[4], -1, False)
        # 달 바다 얼룩
        if 1 <= i <= 6:
            for m in range(5):
                a = 1.3 * m + 0.4
                mx, my = cx + math.cos(a) * rr * 0.42, cy + math.sin(a) * rr * 0.34
                rad = (11 - 1.5 * m) * grow
                for y in range(int(my - rad), int(my + rad) + 1):
                    for x in range(int(mx - rad), int(mx + rad) + 1):
                        if math.hypot(x - mx, (y - my) * 1.2) <= rad and (x + y) % 2 == 0 and not (k > 0 and h2(x, y, 602) < k):
                            cv.put(x, y, SIL[5], -1, False)
        # 초승달 일섬 세 줄
        for j, (ang, off) in enumerate(slashes):
            fj = 1 + j
            if i < fj:
                continue
            age = i - fj
            a = math.radians(ang)
            # 큰 원의 호로 근사한 초승달 일섬(지름 ~ 2.6R)
            Rs = R * 1.6
            ccx = cx - math.sin(a) * Rs * 0.82 + off
            ccy = cy + math.cos(a) * Rs * 0.82 + off
            mid = math.atan2(cy - ccy, cx - ccx)
            fade = 0.0 if age == 0 else min(1.0, age / 6)
            ramp = [SIL[4], SIL[6], SIL[8], SIL[10]] if age < 2 else [SIL[3], SIL[5], SIL[7]]
            crescent_arc(cv, (ccx, ccy), Rs, mid - 0.62, mid + 0.62, 9 if age == 0 else 7, ramp, core=X0 if age == 0 else X1 if age == 1 else None,
                         z=3, seed=610 + j, fade=fade)
        if i == 2:
            sparkle(cv, cx, cy, 12, X0, X1, z=5)
        # 부서진 달 조각이 떨어짐
        if i >= 5:
            r = random.Random(620 + i)
            for m in range(14):
                a = r.uniform(0, 2 * math.pi)
                d = R * r.uniform(0.6, 1.0)
                glyph_moon(cv, int(cx + math.cos(a) * d), int(cy + math.sin(a) * d + 8 * (i - 4) * k), big=m % 3 == 0)
        out.append(img(cv))
    return out


# =============================================================================
# 시그니처 2 — greatsword_landslide (핏빛)
# =============================================================================
def landslide(d, seed=6111):
    FA_ = _fa()
    ang = K57.DIR_ANG[d]
    cx, cy = PV
    r = random.Random(seed)
    spikes = []
    for j in range(9):
        dist = 28 + 28 * j + r.uniform(-6, 6)
        lat = r.uniform(-14, 14)
        x = cx + math.cos(math.radians(ang)) * dist - math.sin(math.radians(ang)) * lat
        y = cy + (math.sin(math.radians(ang)) * dist + math.cos(math.radians(ang)) * lat) * KY
        spikes.append((x, y, r.uniform(48, 80) * (1.2 if j in (3, 6, 8) else 1.0), r.uniform(15, 22), j // 3, r.uniform(-0.22, 0.22), j))
    spikes.sort(key=lambda s: s[1])
    ex = cx + math.cos(math.radians(ang)) * 4 * TILE
    ey = cy + math.sin(math.radians(ang)) * 4 * TILE * KY
    main = K57.W.jag(random.Random(seed), (cx, cy), (ex, ey), n=10, amp=3)
    out = []
    for i in range(len(FA_.LS_MS)):
        cv = Cv(CANVAS, CANVAS)
        kk = max(0.0, (i - 5) / 4)
        # 바닥 균열 — 피가 차오름(앞머리 = i) → 고였다 스밈
        lim = min(1.0, (i + 1) / 4)
        mp = main[:max(2, int(len(main) * lim))]
        cv.chain(mp, lambda t: 3.2 - 1.2 * t, lambda t, dd, x, y: (CRI[6] if dd < 0.35 else CRI[3] if dd < 0.7 else G[2])
                 if not (kk > 0 and h2(x, y, 631) < kk * 0.8) else (CRI[2] if dd < 0.5 else None), z=-2)
        rocks = []
        for (x, y, hgt, wd, grp, lean, jj) in spikes:
            age = i - grp
            if age < 0:
                continue
            g = [0.55, 1.0, 1.0, 0.95, 0.85, 0.7, 0.45, 0.25, 0.1, 0.0][min(9, age)] if i < 7 else max(0.0, 0.6 - 0.2 * (i - 6))
            # 핏물 웅덩이(가시 밑)
            pr = wd * (0.55 + 0.4 * min(1.0, age / 4))
            for yy in range(int(y - pr * 0.4) - 1, int(y + pr * 0.4) + 2):
                for xx in range(int(x - pr) - 1, int(x + pr) + 2):
                    e = ((xx - x) / pr) ** 2 + ((yy - y) / (pr * 0.4)) ** 2
                    if e <= 1:
                        cv.put(xx, yy, CRI[2] if e > 0.5 else CRI[3] if age > 1 else CRI[5], -1, False)
            if g <= 0.05:
                continue
            rocks.append((x, y, hgt * g, wd, lean, age, jj))
        for x, y, hh, wd, lean, age, jj in rocks:
            apex = (x + lean * hh, y - hh)

            def shade(side, up, edge, px_, py_):
                if edge:
                    return G[1]
                if side < 0:
                    return G[7] if up > 0.6 else G[6] if up > 0.3 or (px_ + py_) % 2 else G[5]
                return G[4] if up > 0.45 else G[3] if up > 0.15 else G[2]
            tri(cv, (x - wd * 0.7, y), (x + wd * 0.7, y), apex, shade, z=1)
            # 가시를 타고 오르는 핏줄기
            jagp = K57.W.jag(random.Random(int(x)), (x + 0.5, y - 2), (x + lean * hh * 0.8, y - hh * 0.8), n=4, amp=1.4)
            cv.chain(jagp, lambda t: 1.4 - 0.6 * t, lambda t, dd, px_, py_: (X1 if (age == 0 and t > 0.7 and dd < 0.5) else CRI[7] if age < 3 else CRI[5]), z=2)
            # 솟는 순간 피 분출(꼭짓점 위로 방울)
            if age <= 2:
                rr = random.Random(jj * 7 + i)
                if age == 0:                                # 꼭짓점에서 솟는 핏줄기
                    col_pts = [(apex[0] + 0.6 * math.sin(m), apex[1] - 3 * m) for m in range(9)]
                    cv.chain(col_pts, lambda t: 1.8 - 1.2 * t, lambda t, dd, px_, py_: CRI[7] if dd < 0.5 else CRI[5], z=3)
                for m in range(16):
                    hgt2 = rr.uniform(4, 30) * (1 + age * 0.6)
                    lat = rr.uniform(-10, 10) * (1 + age * 0.6)
                    fall = 3 * age * age
                    droplet(cv, int(apex[0] + lat), int(apex[1] - hgt2 + fall), big=m % 2 == 0, z=3, glint=(age == 0 and m < 2))
        if i == 0:
            sparkle(cv, cx, cy - 2, 6, X1, CRI[7], z=5)
        # 무너질 때 피 안개·돌
        if i >= 5:
            rr = random.Random(seed + i)
            for m in range(40):
                s = rr.choice(spikes)
                x = s[0] + rr.uniform(-22, 22)
                y = s[1] - rr.uniform(0, 40) + 4 * (i - 5)
                cv.put(x, y, CRI[2] if m % 2 else CRI[1], -1, False)
            for m in range(10):
                s = rr.choice(spikes)
                x, y = s[0] + rr.uniform(-8, 8), s[1] - rr.uniform(0, 20) + 4 * (i - 5)
                cv.put(x, y, G[3], 0, False)
                cv.put(x + 1, y, G[2], 0, False)
        out.append(img(cv))
    return out


# =============================================================================
# 시그니처 3 — dagger_hundred_ghosts (귀화)
# =============================================================================
def ghostfire(cv, x, y, dirx, diry, sc, i, blink=True, dim=False):
    """얼굴 달린 도깨비불: 머리(보라 불덩이) + 뒤로 흐르는 불꼬리(청록 끝) + 눈 두 점·입."""
    R = VIO
    for m in range(18):
        u = m / 17
        tx = x - dirx * 30 * sc * u + 3 * math.sin(u * 7 + i) * diry
        ty = y - diry * 30 * sc * u - 3 * math.sin(u * 7 + i) * dirx
        w = (5.5 * sc) * (1 - u) ** 0.8 + 0.4
        for yy in range(int(ty - w) - 1, int(ty + w) + 2):
            for xx in range(int(tx - w) - 1, int(tx + w) + 2):
                d = math.hypot(xx + 0.5 - tx, yy + 0.5 - ty)
                if d > w:
                    continue
                q = 1 - d / w
                RR = TEAL if u > 0.65 else R
                c = RR[11] if q > 0.7 and u < 0.3 else RR[9] if q > 0.45 else RR[7] if q > 0.2 else RR[4]
                if dim:
                    c = RR[6] if q > 0.45 else RR[3]
                cv.put(xx, yy, c, 2 - u, False)
    if blink:
        for dx in (-2, 2):
            cv.put(x + dx * sc, y - 1, VIO[1], 4, False)
        cv.put(x, y + 2, VIO[1], 4, False)


def hundred_ghosts(seed=6121):
    FA_ = _fa()
    cx, cy = 110, 120
    out = []
    starts_ = [(-140.0, 1.0), (-20.0, 0.9), (100.0, 1.1)]
    for i in range(len(FA_.HG_MS)):
        cv = Cv(220, 240)
        for j, (a, sc) in enumerate(starts_):
            ar = math.radians(a)
            if i <= 3:
                dist = [96, 62, 30, 10][i]
                x, y = cx + math.cos(ar) * dist, cy + math.sin(ar) * dist * 0.8
                ghostfire(cv, x, y, -math.cos(ar), -math.sin(ar), sc, i)
            elif i <= 5:
                dist = 10 + 26 * (i - 3)
                x, y = cx - math.cos(ar) * dist, cy - math.sin(ar) * dist * 0.8
                ghostfire(cv, x, y, -math.cos(ar), -math.sin(ar), sc * (1 - 0.15 * (i - 3)), i, blink=(i == 4), dim=True)
        if i >= 3:
            k = (i - 3) / 5
            for j, (a, sc) in enumerate(starts_):
                ar = math.radians(a + 90)
                # 세 갈래 베기: 짧은 초승달(중심 교차)
                c = (cx + math.cos(ar + math.pi / 2) * 60, cy + math.sin(ar + math.pi / 2) * 60)
                mid = math.atan2(cy - c[1], cx - c[0])
                ramp = [VIO[4], VIO[6], VIO[8], VIO[10]] if i < 5 else [TEAL[3], TEAL[5], TEAL[7]]
                crescent_arc(cv, c, 62, mid - 0.6, mid + 0.6, 6 if i == 3 else 5, ramp, core=X1 if i == 3 else None, z=5, seed=650 + j,
                             fade=0.0 if i == 3 else k)
            if i == 3:
                sparkle(cv, cx, cy, 10, X1, VIO[10], z=6)
            r = random.Random(seed + i)
            for m in range(16):
                aa = r.uniform(0, 6.28)
                dd = 20 + 54 * k * r.uniform(0.5, 1.2)
                x, y = cx + math.cos(aa) * dd, cy + math.sin(aa) * dd * 0.8 - 10 * k
                cv.put(x, y, TEAL[9] if m % 2 else VIO[9], 3, False)
                if m % 3 == 0:
                    cv.put(x, y - 1, TEAL[6], 3, False)
        out.append(img(cv))
    return out


# =============================================================================
# 시그니처 4 — bow_meteor_arrow (혜성)
# =============================================================================
def meteor(seed=6131):
    FA_ = _fa()
    cx, cy = 150, 300
    sx, sy = cx - 110, cy - 270
    out = []
    dx0, dy0 = (cx - sx), (cy - sy)
    ln = math.hypot(dx0, dy0)
    ux, uy = dx0 / ln, dy0 / ln
    for i in range(len(FA_.MA_MS)):
        cv = Cv(300, 340)
        if i <= 2:
            u = [0.35, 0.7, 1.0][i]
            hx_, hy_ = sx + (cx - sx) * u, sy + (cy - sy) * u
            tl = 150
            pts = [(hx_ - ux * tl * (1 - m / 24) + 2.5 * math.sin(m * 0.8) * -uy, hy_ - uy * tl * (1 - m / 24) + 2.5 * math.sin(m * 0.8) * ux)
                   for m in range(25)]

            def col(t, d, x, y):
                if t < 0.3 and h2(x, y, 661) > t * 3:
                    return None
                if d < 0.35 and t > 0.35:
                    return X1
                if t > 0.7:
                    return GOLD[10] if d < 0.7 else GOLD[7]
                if t > 0.4:
                    return GOLD[7] if d < 0.6 else A[5]
                return A[5] if d < 0.5 else A[3]
            cv.chain(pts, lambda t: 1.0 + 6.0 * t ** 1.3, col, z=1)
            # 불꽃 깃 두 줄(꼬리 양옆)
            for side in (-1, 1):
                fp = [(hx_ - ux * 70 * m / 12 + side * -uy * (5 + m * 1.6), hy_ - uy * 70 * m / 12 + side * ux * (5 + m * 1.6)) for m in range(13)]
                cv.chain(fp[::-1], lambda t: 0.6 + 2.0 * t, lambda t, d, x, y: (GOLD[9] if d < 0.4 else GOLD[6] if d < 0.8 else A[5])
                         if not (t < 0.35 and h2(x, y, 662 + side) > t * 2.5) else None, z=0)
            for dy in range(-5, 6):
                for dx in range(-5, 6):
                    rr = math.hypot(dx, dy)
                    if rr <= 4.6:
                        cv.put(hx_ + dx, hy_ + dy, X0 if rr < 1.8 else X1 if rr < 3 else GOLD[9], 4, False)
        else:
            k = (i - 3) / 5
            # 그을린 자국
            for yy in range(cy - 14, cy + 15):
                for xx in range(cx - 34, cx + 35):
                    e = ((xx - cx) / 34) ** 2 + ((yy - cy) / 13) ** 2
                    if e <= 1 and (e > 0.4 or (xx + yy) % 2 == 0):
                        cv.put(xx, yy, A[1] if e > 0.6 else A[2], -2, False)
            if i == 3:
                sparkle(cv, cx, cy - 6, 22, X0, X1, z=6)
                sparkle(cv, cx, cy - 6, 10, X0, GOLD[10], z=6)
            rr = 30 + 58 * min(1.0, k * 2.2)
            for m in range(120):
                a = 2 * math.pi * m / 120
                if (m // 4) % 3 == 2 and i > 3:
                    continue
                x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.42
                if k > 0.3 and h2(m, i, 663) < (k - 0.3) * 1.4:
                    continue
                cv.put(x, y, GOLD[10] if k < 0.3 else GOLD[7] if k < 0.6 else A[5], 1, False)
                cv.put(x, y + 1, GOLD[6] if k < 0.5 else A[4], 1, False)
            # 불꽃 꽃잎 6장이 바깥으로
            if k < 0.85:
                for m in range(6):
                    a = math.radians(-180 + 36 * m)
                    L = 14 + 34 * min(1.0, k * 1.6)
                    p0 = (cx + math.cos(a) * 6, cy - 6 + math.sin(a) * 6 * 0.6)
                    p1 = (cx + math.cos(a) * L, cy - 6 + math.sin(a) * L * 0.6 - 10 * k)
                    pts = [(p0[0] + (p1[0] - p0[0]) * t / 10, p0[1] + (p1[1] - p0[1]) * t / 10 - 4 * math.sin(math.pi * t / 10)) for t in range(11)]
                    cv.chain(pts, lambda t: 2.6 * (1 - t) + 0.5, lambda t, d, x, y: (X1 if d < 0.4 and t < 0.4 and k < 0.3 else GOLD[9] if d < 0.6 else GOLD[6])
                             if not (h2(x, y, 664) < k * 0.9) else None, z=2)
            _r = random.Random(seed + 19 + i)
            for m in range(14):
                a = _r.uniform(-2.9, -0.25)
                dd = (12 + 50 * k) * _r.uniform(0.5, 1.2)
                cv.put(cx + math.cos(a) * dd, cy - 6 + math.sin(a) * dd + 14 * k * k, GOLD[9] if m % 2 else A[5], 3, False)
        out.append(img(cv))
    return out


def sig_specs():
    FA_ = _fa()
    old = FA_.specs()
    T = {}
    designs = {
        "katana_fullmoon": ("만월(滿月) — 월인", "주인공 뒤로 은빛 보름달 고리(두께 7, 안쪽 성긴 달빛 점·달 바다)가 떠오르고, 초승달 일섬 세 줄이 차례로 가로지름(첫 프레임 X0 심) → 고리가 픽셀 단위로 빠지며 달 조각(초승 글리프)으로 부서져 떨어짐",
                            ["달이 떠오름", "첫 초승달 일섬(백열)", "둘째 일섬 · 큰 별(백열)", "셋째 일섬", "보름달", "부서짐", "부서짐", "달 조각", "달 조각", "흩어짐"]),
        "greatsword_landslide": ("산붕(山崩) — 핏빛 거암검", "찍은 자리에서 조준 방향으로 현무암 가시 아홉 개가 세 무리로 솟고, 솟는 순간 가시마다 피가 뿜어 오름(핏줄기가 가시를 타고 오름) · 4칸 균열에 피가 차오름 → 가시가 무너지며 핏물 웅덩이·피 안개·돌",
                                 ["첫 무리 솟음 · 피 분출", "둘째", "셋째", "다 솟음", "버팀", "피 고임", "무너짐", "무너짐", "무너짐", "피 안개"]),
        "dagger_hundred_ghosts": ("백귀(百鬼) — 귀화", "세 방향에서 얼굴 달린 보라 도깨비불(청록 불꼬리)이 날아들어 대상 한가운데서 세 갈래 초승달 베기(X1 심) → 꿰뚫고 나가 청록·보라 불티로 흩어짐",
                                  ["세 도깨비불 다가옴", "다가옴", "다가옴", "세 갈래 베기(백열)", "꿰뚫고 나감", "흩어짐", "불티", "불티", "불티"]),
        "bow_meteor_arrow": ("유성(流星) — 혜성 날개", "왼쪽 위 하늘에서 금빛 혜성 화살(X0 머리 · 150도트 꼬리 · 양옆 불꽃 깃)이 떨어져 꽂히며 큰 네 갈래 별 → 금빛 불꽃 고리가 퍼지고 불꽃 꽃잎 6장이 바깥으로 튐 · 그을린 자국",
                             ["혜성 낙하", "낙하", "닿기 직전", "착탄(큰 별)", "고리·꽃잎 퍼짐", "퍼짐", "식음", "불티", "불티"]),
    }
    fns = {"katana_fullmoon": lambda d: fullmoon(), "greatsword_landslide": landslide, "dagger_hundred_ghosts": lambda d: hundred_ghosts(),
           "bow_meteor_arrow": lambda d: meteor()}
    for name, sp in old.items():
        m = dict(sp["meta"])
        aw, ds, roles = designs[name]
        m.update(awakening=aw, design=ds, frameRoles=roles, previousDesign="57라운드 build57 재·호박판(60 Q15~Q21 로 교체)")
        T[name] = dict(rows=sp["rows"], ms=sp["ms"], glow=sp["glow"], fn=fns[name], anchor=sp["anchor"], fit=sp["fit"], meta=m)
    return T


def sig_job(name):
    sp = sig_specs()[name]
    frames = {d: sp["fn"](d) for d in sp["rows"]}
    return write_fx(name, frames, sp["rows"], sp["ms"], sp["anchor"], sp["meta"], glow=sp["glow"], fit=sp["fit"])


# =============================================================================
# 각성 순간 전환 — <무기>_awaken_in (새 키)
# =============================================================================
IN_CONCEPTS = {"katana": KM.KA(), "greatsword": GM.BLOOD, "dagger": DM.DA(), "bow": BM.BA()}
IN_MS = [60] * 8 + [100, 100, 80, 80]


def awaken_in(weapon):
    c = IN_CONCEPTS[weapon]
    out = []
    ang = {"bow": -math.pi / 2}.get(weapon, 0.0)
    for i in range(len(IN_MS)):
        cv = Cv(CANVAS, CANVAS)
        p = min(1.0, i / 7)
        f = F(p=p, t=max(0, i - 7), tn=c.tn, draw=0.0, glow=(i == 7))
        f.handR = None
        reach = c.reach
        g0 = (PV[0] - int(reach * 0.45 * math.cos(ang)), PV[1] - 150 - int(reach * 0.45 * math.sin(ang)))
        c.draw(cv, g0, ang, f)
        # 전환 끝 번쩍(고리)
        R_ = {"katana": SIL, "greatsword": CRI, "dagger": VIO, "bow": GOLD}[weapon]
        if i in (7, 8):
            rr = reach * (0.55 if i == 7 else 0.75)
            for m in range(160):
                a = 2 * math.pi * m / 160
                x, y = PV[0] + math.cos(a) * rr, PV[1] - 150 + math.sin(a) * rr * 0.5
                if i == 8 and m % 3 == 0:
                    continue
                cv.put(x, y, X1 if i == 7 else R_[8], 5, False)
        if i >= 10:                                   # 사라짐(픽셀 단위)
            k = (i - 9) / 3
            cv.px = {q: v for q, v in cv.px.items() if h2(q[0], q[1], 671) > k}
        out.append(img(cv))
    return out


def in_job(weapon):
    name = weapon + "_awaken_in"
    c = IN_CONCEPTS[weapon]
    meta = K57.pp_meta(weapon=weapon, awakening=c.name, followPlayer=True, depth="above",
                       spawn="awaken_acquired",
                       spawnNote="최종 각성을 얻은 순간 1회(진화 메뉴를 닫은 직후 주인공 머리 위). 같은 순간부터 무기 시트 위에 <무기 시트>_awaken 오버레이를 켠다(60 Q21 각성 순간 색 전환 8×60ms)",
                       frameRoles=["원래 무기"] + ["색 전환 %d" % k for k in range(1, 7)] + ["각성 완료(번쩍)", "고리 퍼짐", "머묾", "사라짐", "사라짐"],
                       design="주인공 머리 위(피벗 위 150도트)에 각성 무기가 나타나 시안의 전환 방식으로 원래 색 → 각성 색(8×60ms) → 번쩍·고리 → 픽셀 단위로 사라짐. 전환: " + c.color)
    frames = {"any": awaken_in(weapon)}
    return write_fx(name, frames, ["any"], IN_MS, PV, meta, glow=[7])


# =============================================================================
# 각성 전용 궤적 — <기본 fx>_awaken (새 키, 기본 fx 와 같은 틀·프레임·ms·피벗)
# =============================================================================
TRAILS = {
    "katana": ["katana_rise", "katana_fall", "katana_spin", "katana_thrust", "katana_issen_line_t1", "katana_issen_line_t2",
               "katana_issen_line_t3", "katana_issen_line_t4"],
    "greatsword": ["greatsword_sweep_cw", "greatsword_sweep_ccw", "greatsword_cleave", "greatsword_charge_swing"],
    "dagger": ["dagger_combo1", "dagger_combo2", "dagger_combo3", "dagger_flurry"],
    "bow": ["bow_arrow", "bow_arrow_rapid", "bow_arrow_snipe"],
}
TRAIL_RAMP = {
    "katana": [SIL[2], SIL[4], SIL[6], SIL[8], SIL[10], X1, X0],
    "greatsword": [CRI[1], CRI[2], CRI[4], CRI[5], CRI[6], CRI[7], X1],
    "dagger": [VIO[2], VIO[3], VIO[5], VIO[7], VIO[9], VIO[11], X1],
}


def _lum_rank(frames):
    """시트 전체 색을 밝기 순으로 → 0..1 위치(같은 색은 같은 단계)."""
    cols = set()
    for lst in frames.values():
        for im in lst:
            cols |= {px[:3] for px in im.getdata() if px[3]}
    srt = sorted(cols, key=P.lum)
    n = max(1, len(srt) - 1)
    return {c: i / n for i, c in enumerate(srt)}


def restyle(weapon, im, rank, i, glow_frame, nframes):
    px = im.load()
    W, H = im.size
    cv = Cv(W, H)
    ramp = TRAIL_RAMP[weapon]
    mask = set()
    bright = []
    for y in range(H):
        for x in range(W):
            c = px[x, y]
            if not c[3]:
                continue
            q = rank[c[:3]]
            k = min(len(ramp) - 1, int(q * len(ramp)))
            col = ramp[k]
            if not glow_frame and col in (X0,):
                col = ramp[-2]
            if weapon == "dagger" and q < 0.4 and h2(x // 3, y // 3, 681) > 0.4:
                col = [TEAL[3], TEAL[5], TEAL[7]][min(2, int(q * 7.5))]          # 식어 가는 꼬리는 청록
            cv.put(x, y, col, 0, False)
            mask.add((x, y))
            if q > 0.7:
                bright.append((x, y))
    if not mask:
        return im.copy()
    edge = [p for p in mask if any((p[0] + dx, p[1] + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    age = i / max(1, nframes - 1)
    if weapon == "katana":
        # 밝은 획 둘레 빛 번짐(체크 1겹) + 달 조각
        for (x, y) in bright:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
                q = (x + dx, y + dy)
                if q not in mask and (q[0] + q[1]) % 2 == 0 and 0 <= q[0] < W and 0 <= q[1] < H:
                    cv.put(q[0], q[1], SIL[3], -1, False)
        if edge and age > 0.25:
            r = random.Random(691 + i)
            for m in range(4):
                x, y = r.choice(edge)
                glyph_moon(cv, x + r.randint(-6, 6), y + r.randint(-6, 6) + int(6 * age))
    elif weapon == "greatsword":
        cxm = sum(p[0] for p in mask) / len(mask)
        cym = sum(p[1] for p in mask) / len(mask)
        r = random.Random(701 + i)
        sel = [edge[int(h2(m, 3, 702) * len(edge))] for m in range(min(len(edge), 26))]
        for m, (x, y) in enumerate(sel):
            nx, ny = x - cxm, y - cym
            ln = math.hypot(nx, ny) or 1
            dist = 2 + 10 * age + 4 * h2(m, 1, 703)
            X, Y = x + nx / ln * dist, y + ny / ln * dist + 6 * age * age
            if 0 <= X < W - 2 and 0 <= Y < H - 3:
                droplet(cv, int(X), int(Y), big=m % 4 == 0, z=2, glint=(glow_frame and m % 6 == 0))
        for (x, y) in edge:                              # 피 안개(성긴 점)
            for k in range(2):
                X, Y = x + r.randint(-5, 5), y + r.randint(-5, 5)
                if (X, Y) not in mask and 0 <= X < W and 0 <= Y < H and h2(X, Y, 704) > 0.86:
                    cv.put(X, Y, CRI[2] if h2(X, Y, 705) > 0.5 else CRI[1], -1, False)
    elif weapon == "dagger":
        for (x, y) in edge:                              # 위로 핥는 불혀
            if vnoise(x * 0.35 + i * 1.3, 711) > 0.62:
                n = 1 + int(3 * vnoise(x * 0.2 + y * 0.1, 712))
                for k in range(1, n + 1):
                    if (x, y - k) not in mask and 0 <= y - k < H:
                        cv.put(x, y - k, VIO[6] if k < n else TEAL[8], 1, False)
        if glow_frame and bright:                        # 판정 순간 도깨비 얼굴
            x, y = bright[len(bright) // 2]
            for dx, dy in ((-1, 0), (1, 0), (0, 2)):
                cv.put(x + dx, y + dy, VIO[1], 5, False)
    return cv.image()


def comet_arrow(w, h, pv, frames_n, scale=1.0, flick=0):
    """각성 혜성 화살(오른쪽 보기, 피벗 = 화살 중심). 꼬리는 피벗 뒤로 길게."""
    out = []
    for i in range(frames_n):
        cv = Cv(w, h)
        hx_ = min(pv[0] + int(18 * scale), w - 9)
        hy_ = pv[1]
        tail = pv[0] - 4
        pts = [(hx_ - (hx_ - 5) * (1 - m / 24), hy_ + 1.2 * math.sin(m * 0.9 + i * 1.7)) for m in range(25)]

        def col(t, d, x, y):
            if t < 0.3 and h2(x, y, 721 + i) > t * 3:
                return None
            if d < 0.35 and t > 0.45:
                return X1
            if t > 0.7:
                return GOLD[10] if d < 0.7 else GOLD[7]
            if t > 0.4:
                return GOLD[7] if d < 0.6 else A[5]
            return A[5] if d < 0.5 else A[3]
        cv.chain(pts, lambda t: 0.5 + (h / 2 - 4) * t ** 1.5 * 0.8, col, z=0)
        # 화살대(금) + 혜성 머리
        for x in range(pv[0] - int(20 * scale), hx_):
            cv.put(x, hy_, GOLD[8], 1, False)
        rr = 2.6 * scale + 0.4
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                r = math.hypot(dx, dy)
                if r <= rr:
                    cv.put(hx_ + dx, hy_ + dy, X0 if r < 1.1 else X1 if r < rr - 0.9 else GOLD[9], 3, False)
        for m in range(3):
            x = pv[0] - 10 - 9 * m - (i * 3) % 6
            y = hy_ + (3 + m) * (1 if (m + i) % 2 else -1)
            if 0 <= x < w and 0 <= y < h:
                cv.put(x, y, GOLD[9] if m % 2 else A[5], 2, False)
        out.append(cv.image())
    return out


def trail_job(arg):
    weapon, base = arg
    meta, j = old_meta(base)
    name = base + "_awaken"
    rows = j["directions"]
    ms = j["frameDurationsMs"]
    glow = set(j.get("glowFrames") or [])
    meta.update(awakenOf="fx/v3/" + base, awakeningTrail=True,
                swapRule="각성한 런에서 '%s' 대신 이 시트(같은 틀·프레임·ms·피벗·행 — 1:1 교체, 60 Q21 각성 전용 궤적)" % base)
    if weapon == "bow":
        W0, H0 = j["frameWidth"], j["frameHeight"]
        pv0 = (j["pivot"]["x"], j["pivot"]["y"])
        sc = {"bow_arrow": 1.0, "bow_arrow_rapid": 0.9, "bow_arrow_snipe": 1.25}[base]
        extra = int(72 * sc)
        Wn, Hn = W0 + extra, max(H0, 24)
        pvn = (pv0[0] + extra, Hn // 2)
        frames = {d: comet_arrow(Wn, Hn, pvn, len(ms), sc) for d in rows}
        meta.update(design="혜성 화살(혜성 날개 각성): X0·X1 혜성 머리 + 금빛 화살대 + 피벗 뒤로 %d도트 금빛 불꼬리(끝은 끊긴 불티) — 화살 중심 피벗은 그대로, 틀만 뒤로 김" % extra,
                    awakeningTrailNote="화살은 기본 시트보다 틀이 길다(꼬리). pivot = 화살 중심(원 시트와 같은 자리), rotate·drawnFacing 같음")
        return write_fx(name, frames, rows, ms, pvn, meta, glow=glow, fit="none")
    jj, fr = K57.grid_frames("fx/v3/" + base)
    rank = _lum_rank(fr)
    frames = {d: [restyle(weapon, im, rank, i, i in glow, len(fr[d])) for i, im in enumerate(fr[d])] for d in rows}
    meta["design"] = {"katana": "월인 궤적: 기본 획을 은백(SIL2~10)·X1/X0 심으로, 밝은 획 둘레 체크 빛 번짐 + 흩어지는 초승달 조각",
                      "greatsword": "핏빛 궤적: 기본 획을 진홍(CRI1~7)·젖은 반사 X1 로, 획 바깥으로 튀는 핏방울 26개(시간에 따라 멀어지며 떨어짐) + 성긴 피 안개",
                      "dagger": "귀화 궤적: 기본 획을 보라(VIO2~11)로, 식는 꼬리는 청록, 획 위로 핥는 불혀 + 판정 순간 도깨비 얼굴"}[weapon]
    return write_fx(name, frames, rows, ms, (j["pivot"]["x"], j["pivot"]["y"]), meta, glow=glow, fit="none")


JOBS = ([("sig", n) for n in ("katana_fullmoon", "greatsword_landslide", "dagger_hundred_ghosts", "bow_meteor_arrow")]
        + [("in", w) for w in ("katana", "greatsword", "dagger", "bow")]
        + [("trail", (w, b)) for w, lst in TRAILS.items() for b in lst])


def job(arg):
    kind, a = arg
    if kind == "sig":
        return sig_job(a)
    if kind == "in":
        return in_job(a)
    return trail_job(a)


def build(flt=None, procs=8):
    from multiprocessing import Pool
    jobs = [j for j in JOBS if not flt or any(x in str(j[1]) for x in flt)]
    with Pool(procs) as p:
        for r in p.imap_unordered(job, jobs):
            print(r, flush=True)


if __name__ == "__main__":
    build(sys.argv[1:])
