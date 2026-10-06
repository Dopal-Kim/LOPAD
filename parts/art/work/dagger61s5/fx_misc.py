"""단검 보조 fx — 그림자 걸음(먹 번짐) · 투척(작은 발톱) · 부채 투척 · 낙인(새긴 발톱 자국) · 기폭 · 출혈 · 옮김 · 꽂힌 날 ·
쌍격 분신 X · 백귀 세 갈래 · 각성 순간. 틀·프레임·ms·피벗·행 그대로."""
import math
import os
import sys

import d5
import blade as BL
import overlays as OV
import fx_thrust as T
from d5 import Cv, Frame, Rand, h2, clamp

EM = T.EMBER
sys.path.insert(0, os.path.join(d5.WORK, "atlas57"))
import gridsheet  # noqa: E402


def hero_frames(rel):
    jp = os.path.join(d5.SPR, rel + ".json")
    m = gridsheet.load_meta(jp)
    im = gridsheet.open_grid(jp)
    fw, fh = m["frameWidth"], m["frameHeight"]
    return m, [[im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(m["frames"])] for r in range(im.height // fh)]


AMBERS = {c[:3] for c in (d5.A19, d5.A21, d5.A23, d5.A25, d5.A26, d5.X0, d5.X1, d5.AR[4], d5.AR[6], d5.AR[8], d5.AR[11])}


def is_amber(c):
    return c[:3] in AMBERS or (c[0] > 150 and c[0] > c[2] + 60)


# =============================================================================
# 그림자 걸음 출발 잔상 — 먹 실루엣이 발밑 먹 웅덩이로 녹아 번짐
# =============================================================================
def shadowstep(m):
    hm, hf = hero_frames("player/v3/player_idle_free")
    W, H = m["frameWidth"], m["frameHeight"]
    px, py = m["pivot"]["x"], m["pivot"]["y"]
    rows = []
    for ri, d in enumerate(m["directions"]):
        src = hf[ri][0]
        sp = src.load()
        bb = src.getbbox()
        top, bot = bb[1], bb[3]
        row = []
        for i in range(m["frames"]):
            cv = Cv(W, H)
            # 발밑 먹 웅덩이 + 번지는 가닥
            prx = [14, 20, 25, 28][i]
            pry = [5, 7, 9, 10][i]
            d5.ink_blot(cv, px, py - 2, prx, 11 + ri, core=d5.INK, rim=d5.S0 if i < 2 else d5.B2, ky=pry / float(prx), ragged=0.25,
                        holes=[0, 0, 0.15, 0.45][i])
            if i >= 1:
                r = Rand(30 + ri)
                for k in range(5 + 2 * i):
                    a = r.f() * 2 * math.pi
                    x0 = px + math.cos(a) * prx * 0.8
                    y0 = py - 2 + math.sin(a) * pry * 0.8
                    d5.ink_tendril(cv, x0, y0, math.atan2(math.sin(a) * 0.35, math.cos(a)), 6 + 5 * i * r.f(), 2.4 - 0.3 * i,
                                   d5.INK if k % 2 else d5.INK2, k + ri, wav=0.5)
            # 실루엣: 먹 몸 + 밝은 재 테 + 호박 금 자리
            cut = [1.1, 0.55, 0.25, -1][i]                       # 이 높이 아래는 녹아 웅덩이로
            lift = [0, 1, 4, 8][i]
            hole = [0.0, 0.18, 0.55, 1.0][i]
            if i < 3:
                for y in range(top, bot):
                    fy = (y - top) / float(max(1, bot - top))
                    for x in range(bb[0], bb[2]):
                        c = sp[x, y]
                        if not c[3]:
                            continue
                        if fy > cut:
                            if (x * 3 + y) % 11 == 0 and h2(x, y, i) < 0.35:   # 흘러내리는 먹 줄
                                for j in range(0, int((bot - y) * 0.35)):
                                    if y + j >= py - 1:
                                        break
                                    cv.put(x, y + j, d5.INK2)
                            continue
                        if h2(x, y, 40 + i) < hole * (0.4 + fy):
                            continue
                        edge = any(not (0 <= x + dx < src.width and 0 <= y + dy < src.height) or not sp[x + dx, y + dy][3]
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                        if is_amber(c):
                            col = d5.A21 if i == 0 else d5.A19
                        elif edge:
                            col = d5.S0 if i == 0 else d5.B2
                        else:
                            col = d5.INK2 if (x + y) % 2 == 0 or i == 0 else d5.INK
                        cv.put(x, y - lift, col)
            # 떠오르는 먹 부스러기·불씨
            r = Rand(70 + ri * 3 + i)
            for k in range(4 + 4 * i):
                x = px + (r.f() * 2 - 1) * 20
                y = py - 20 - r.f() * (60 + 15 * i)
                c = [d5.INK2, d5.B1, d5.A19, d5.INK][k % 4] if i > 0 else d5.INK2
                cv.put(x, y, c)
                if k % 5 == 0 and i in (1, 2):
                    cv.put(x, y - 1, d5.A21)
            d5.clip_margin(cv.im, 2)
            row.append(cv.im)
        rows.append(row)
    return rows


# =============================================================================
# 투척 발톱 (dagger_thrown) — 작은 발톱 날이 끝부터 날아가며 짧은 잔상 획을 끈다
# =============================================================================
def thrown(m):
    W, H = m["frameWidth"], m["frameHeight"]
    px, py = m["pivot"]["x"], m["pivot"]["y"]
    rows = [[]]
    for i in range(m["frames"]):
        cv = Cv(W, H)
        f = Frame(cv, px - 4, py + 1.5, 0)
        r = Rand(500 + i)
        for k in range(3):                                      # 잔상 획(짧고 많게)
            u1 = -6 - 11 * k - 3 * ((i + k) % 2)
            v = [-2.5, 2.5, 0][k] * (1 if i % 2 else -1) * 0.6
            f.claw(u1 - 14 + 2 * k, u1, 2.2 - 0.4 * k, [(1.0, [d5.A19, d5.B3, d5.B2][k]), (0.5, [d5.A21, d5.A19, d5.B3][k])],
                   hook=-1.5, voff=v)
        f.line(-40, 0, -18, 0, d5.B2)
        g = BL.Geo((px - 6, py + 1.5), (px + 15, py + 0.5), facing=(0.0, -1.0) if i % 2 == 0 else (0.0, 1.0))
        sk = BL.BaseSkin()
        for (x, y), (part, s, dd) in BL.blade_px(g, 0.62, 0.72).items():
            c = sk.col(part, s, dd, "steel", x, y, 0)
            if c:
                cv.put(x, y, c)
        x, y = g.w(g.L - 0.5, 0)
        cv.put(x, y, d5.A25 if i % 2 == 0 else d5.A23)
        rows[0].append(cv.im)
    return rows


# =============================================================================
# 부채 투척 (dagger_fan_throw fx) — 왼팔 쓸어내는 발톱 호 + 놓는 자리에서 세 바늘(−15°·0°·+15°)
# =============================================================================
def fan_throw(m):
    W, H = m["frameWidth"], m["frameHeight"]
    wm, _ = d5.grid("weapons/v3/dagger_fan_throw")
    off = (m["pivot"]["x"] - wm["pivot"]["x"], m["pivot"]["y"] - wm["pivot"]["y"])
    rf = wm["releaseFrame"]
    glow = set(m.get("glowFrames") or [1])
    rows = []
    for d in m["directions"]:
        sa = wm["throwSpawnAnchors"][d][rf] if isinstance(wm["throwSpawnAnchors"][d], list) else wm["throwSpawnAnchors"][d]
        if isinstance(sa, dict):
            sa = (sa["x"], sa["y"])
        rx, ry = sa[0] + off[0], sa[1] + off[1]
        fx_, fy_ = BL.FACING[d]
        aim = math.degrees(math.atan2(fy_, fx_))
        hk = 1 if d != "left" else -1
        row = []
        for i in range(m["frames"]):
            cv = Cv(W, H)
            g = i in glow
            sw = Frame(cv, rx, ry, aim)
            if i <= 2:                                          # 쓸어내는 호(뒤 → 앞)
                lay = [(1.0, EM.dim), (0.55, EM.body)] if i == 0 else [(1.0, EM.dark), (0.5, EM.dim)] if i == 1 else [(1.0, EM.ash)]
                sw.claw(-34, 2, 5.0 - i, lay, hook=18 * hk, voff=-16 * hk, hp=1.3, peak=0.7)
            for k, fd in enumerate(wm["fanDeg"]):
                a = aim + fd
                ca, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
                room = min([(W - 6 - rx) / ca if ca > 0.01 else 1e9, (rx - 6) / -ca if ca < -0.01 else 1e9,
                            (H - 6 - ry) / sn if sn > 0.01 else 1e9, (ry - 6) / -sn if sn < -0.01 else 1e9])
                f = Frame(cv, rx, ry, a)
                head = min(room - 6, [0, 62, 88, 98, 104][i])
                if i == 0 or head < 12:
                    continue
                if i == 1:
                    f.claw(6, head, 3.6, [(1.0, EM.dim), (0.6, EM.mid)] + ([(0.3, EM.hot)] if g else [(0.3, EM.h2)]), hook=-2 * hk)
                    f.xglint(head + 2, -1.5 * hk, 4, core=EM.core if g else EM.h2, mid=EM.hot if g else EM.mid, edge=EM.h2 if g else EM.body)
                elif i == 2:
                    f.claw(head * 0.45, head, 2.6, [(1.0, EM.dark), (0.5, EM.body)], hook=-2 * hk)
                    f.xglint(head + 2, -1.5 * hk, 3, core=EM.mid, mid=EM.body, edge=EM.dim)
                else:
                    for j in range(3):
                        u = head * (0.55 + 0.15 * j)
                        if (j + i) % 2:
                            f.line(u, 0, u + 5, -0.5 * hk, EM.dark if i == 3 else EM.ash)
            row.append(cv.im)
        rows.append(row)
    return rows


# =============================================================================
# 낙인 — 적 몸에 새긴 발톱 자국 (스택 1~5)
# =============================================================================
CUT_ANG = 62.0          # 화면에서 오른쪽 위 → 왼쪽 아래로 그은 발톱 자국


def cut(cv, cx, cy, ln, w, core, border, ang=CUT_ANG, hook=2.5):
    """새긴 자국 하나: 먹 테두리(파인 그림자) + 안쪽 불씨 심."""
    f = Frame(cv, cx, cy, ang)
    f.claw(-ln / 2, ln / 2, w + 1.6, [(1.0, border)], hook=hook, peak=0.55, back=0.2)
    f.claw(-ln / 2 + 1, ln / 2 - 1, w, [(1.0, core)], hook=hook, peak=0.55, back=0.2)


def sigil(cv, cx, cy, n, newest_core, core_fn, scale=1.0, border=None):
    """n 스택 표식. core_fn(k) → k번째 자국 심 색(newest 는 newest_core)."""
    border = border or d5.INK2
    for k in range(min(n, 3)):
        c = newest_core if k == n - 1 else core_fn(k)
        cut(cv, cx + (k - 1) * 4.6 * scale, cy + (k - 1) * 0.8 * scale, 15 * scale, 1.5 * scale, c, border)
    if n >= 4:                                           # 가로지르는 넷째 자국 = X
        c = newest_core if n == 4 else core_fn(3)
        cut(cv, cx, cy + 0.5, 17 * scale, 1.4 * scale, c, border, ang=-28, hook=-2.0)
    if n >= 5:                                           # 다섯째 = 감싸 닫는 발톱 고리 (표식 완성)
        c = newest_core
        steps = 90
        for k in range(steps):                           # 끝이 갈고리로 말린 열린 고리(약 290°)
            t = k / float(steps - 1)
            a = math.radians(-215 + 290 * t)
            r = (11.8 - 2.5 * t ** 3) * scale
            for dr in (-1.0, 0.0, 1.0):
                cv.put(cx + math.cos(a) * (r + dr), cy + math.sin(a) * (r + dr) * 0.85, border)
        for k in range(steps):
            t = k / float(steps - 1)
            a = math.radians(-215 + 290 * t)
            r = (11.8 - 2.5 * t ** 3) * scale
            cv.put(cx + math.cos(a) * r, cy + math.sin(a) * r * 0.85, c)


def brand_mark(m):
    W, H = m["frameWidth"], m["frameHeight"]
    cx, cy = m["pivot"]["x"] + 2, m["pivot"]["y"] - 15
    rows = []
    for ri, key in enumerate(m["directions"]):
        n = int(key)
        row = []
        for i in range(m["frames"]):
            cv = Cv(W, H)
            if i == 0:
                newc = d5.X1
            elif i == 1:
                newc = d5.A25
            else:
                newc = d5.A23 if (i % 2 == 0) else d5.A21
            sigil(cv, cx, cy, n, newc, lambda k, i=i: d5.A21 if (k + i) % 2 else d5.A19)
            if i == 0:                                   # 지져지는 순간 작은 X 불꽃
                f = Frame(cv, cx + 6, cy - 7, 0)
                f.xglint(0, 0, 3, core=d5.X1, mid=d5.A26, edge=d5.A23)
            if i >= 2:                                   # 오르는 불씨
                r = Rand(n * 10 + i)
                x = cx - 6 + 12 * r.f()
                y = cy - 11 - 2 * (i - 2)
                cv.put(x, y, d5.A23 if i % 2 else d5.A21)
            row.append(cv.im)
        rows.append(row)
    return rows


def brand_burst(m):
    W, H = m["frameWidth"], m["frameHeight"]
    cx, cy = m["pivot"]["x"], m["pivot"]["y"]
    glow = set(m.get("glowFrames") or [1, 2])
    rows = []
    for ri, key in enumerate(m["directions"]):
        R = m["sizeInfo"][key]["radiusPx"]
        sc = R / 46.0
        n = {"s": 2, "m": 4, "l": 5}[key]
        row = []
        for i in range(m["frames"]):
            cv = Cv(W, H)
            g = i in glow
            if i == 0:                                   # 새긴 자국이 부풀며 갈라짐
                sigil(cv, cx, cy, n, d5.A25, lambda k: d5.A23, scale=1.3 * max(0.85, sc), border=d5.INK2)
                for k in range(8):
                    a = 2 * math.pi * k / 8 + 0.2
                    cv.line(cx + math.cos(a) * 8 * sc, cy + math.sin(a) * 7 * sc, cx + math.cos(a) * 14 * sc, cy + math.sin(a) * 12 * sc, d5.A21)
            elif i == 1:                                 # 터짐: 큰 X + 바깥으로 뻗는 발톱 바늘
                f = Frame(cv, cx, cy, 0)
                for k in range(8):
                    a = 360.0 * k / 8 + 22.5
                    fk = Frame(cv, cx, cy, a)
                    fk.claw(6, R * 0.62, 4.0 * sc, [(1.0, EM.mid), (0.55, EM.h2), (0.25, EM.hot)], hook=3 * sc, peak=0.6)
                f.xglint(0, 0, int(R * 0.62), core=EM.core, mid=EM.hot, edge=EM.h2, tilt=45)
                f.xglint(0, 0, int(R * 0.3), core=EM.core, mid=EM.core, edge=EM.hot, tilt=45)
                d5.ink_blot(cv, cx, cy, 4 * sc, 3, core=EM.core, rim=EM.hot)
            elif i <= 4:                                 # 발톱 고리가 돌며 퍼지고, 먹 튐이 고리로
                k0 = i - 2
                rr = R * (0.72 + 0.16 * k0)
                for k in range(6):
                    a = 360.0 * k / 6 + 25 * k0 + 10
                    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                    fk = Frame(cv, cx + ca * rr, cy + sa * rr * 0.86, a + 90)
                    lay = ([(1.0, EM.mid), (0.5, EM.h2), (0.22, EM.hot)] if g else [(1.0, EM.dim), (0.5, EM.body)]) if k0 == 0 else \
                        [(1.0, EM.dark), (0.5, EM.dim)] if k0 == 1 else [(1.0, EM.ash)]
                    if k0 == 2 and k % 2:
                        continue
                    fk.claw(-R * 0.32, R * 0.12, (4.2 - k0) * sc, lay, hook=-5 * sc, peak=0.7)
                if k0 == 0:
                    Frame(cv, cx, cy, 0).xglint(0, 0, int(R * 0.35), core=EM.h2 if not g else EM.hot, mid=EM.mid, edge=EM.dim, tilt=48)
                for k in range(10):                      # 먹 튐
                    a = 2 * math.pi * k / 10 + 0.4
                    rb = R * (0.42 + 0.2 * k0) + (k % 3) * 2
                    d5.ink_blot(cv, cx + math.cos(a) * rb, cy + math.sin(a) * rb * 0.86, (1.6 + (k % 3) * 0.7 + 0.4 * k0) * sc, k + ri,
                                core=EM.ink2, rim=EM.dark if k0 < 2 else EM.ash, holes=0.15 * k0)
            else:                                        # 마르는 먹·재 부스러기
                k0 = i - 5
                for k in range(10 - 3 * k0):
                    a = 2 * math.pi * k / 10 + 0.4
                    rb = R * (0.85 + 0.12 * k0) + (k % 3) * 2
                    d5.ink_blot(cv, cx + math.cos(a) * rb, cy + math.sin(a) * rb * 0.86 + 2 * k0, (1.4 + (k % 2) * 0.6) * sc, k + 7,
                                core=EM.ink2, rim=EM.ash, holes=0.35 + 0.2 * k0)
                r = Rand(ri * 31 + i)
                for k in range(14 - 4 * k0):
                    a = r.f() * 2 * math.pi
                    rb = R * (0.3 + 0.7 * r.f())
                    cv.put(cx + math.cos(a) * rb, cy + math.sin(a) * rb * 0.86 - 3 * k0, [EM.ash, EM.dark, EM.dim][k % 3])
            row.append(cv.im)
        rows.append(row)
    return rows


def brand_bleed(m):
    W, H = m["frameWidth"], m["frameHeight"]
    cx, cy = m["pivot"]["x"] + 2, m["pivot"]["y"] - 6
    rows = [[]]
    for i in range(m["frames"]):
        cv = Cv(W, H)
        sigil(cv, cx, cy, 3, d5.A21, lambda k: d5.A21 if (k + i) % 2 else d5.A19)
        for k in range(3):                               # 자국마다 떨어지는 호박 피 방울
            x = cx + (k - 1) * 4.6 - 3
            ph = (i * 8 + k * 13) % 40
            y0 = cy + 6 + ph
            if y0 + 4 < H - 1:
                for j in range(3):
                    cv.put(x, y0 - j, d5.A18 if j else d5.A19)
                cv.put(x, y0 + 1, d5.A21)
                cv.put(x + 1, y0 + 1, d5.A19)
            cv.put(x, cy + 6, d5.A19)
        rows[0].append(cv.im)
    return rows


def brand_hop(m):
    W, H = m["frameWidth"], m["frameHeight"]
    px, py = m["pivot"]["x"], m["pivot"]["y"]
    rows = [[]]
    for i in range(m["frames"]):
        cv = Cv(W, H)
        f = Frame(cv, px, py, 0)
        for k in range(3):
            u1 = 2 - 10 * k - 2 * ((i + k) % 2)
            f.claw(u1 - 16, u1, 2.4 - 0.5 * k, [(1.0, [d5.A19, d5.A18, d5.B2][k]), (0.5, [d5.A21, d5.A19, d5.B3][k])],
                   voff=[0, -2, 2][k] * (1 if i % 2 else -1), hook=-1.0)
        cx = px + 10
        cut(cv, cx, py, 15, 1.8, d5.A23 if i % 2 == 0 else d5.A25, d5.INK2, ang=50, hook=1.8)
        cut(cv, cx, py, 15, 1.8, d5.A23 if i % 2 else d5.A25, d5.INK2, ang=-50, hook=-1.8)
        rows[0].append(cv.im)
    return rows


# =============================================================================
# 꽂힌 날 (dagger_stuck_blade) — 땅에 비스듬히 박힌 발톱 날
# =============================================================================
def stuck_blade(m):
    W, H = m["frameWidth"], m["frameHeight"]
    gx, gy = m["pivot"]["x"], m["pivot"]["y"]
    rows = [[]]
    sk = BL.BaseSkin()
    for i in range(m["frames"]):
        cv = Cv(W, H)
        sink = [0, 2, 2, 2, 2, 2, 2, 2][i]
        geo = BL.Geo((gx - 4, gy - 22 + sink), (gx + 2, gy + 3 + sink), facing=(1.0, 0.0))
        pxs = BL.blade_px(geo, 0.85, 0.8)
        for (x, y), (part, s, dd) in pxs.items():
            if y >= gy:                                  # 땅 아래
                continue
            if i >= 6 and h2(x, y, i) < (0.45 if i == 6 else 0.8):
                continue
            c = sk.col(part, s, dd, "steel", x, y, 0)
            if i >= 6 and c:
                c = d5.B2 if part in ("body", "spine") else d5.B1 if part in ("out", "ring", "wrap", "guard") else d5.A19
            if c:
                cv.put(x, y, c)
        for k in range(-5, 6):                           # 패인 자리
            cv.put(gx + k, gy, d5.B1 if abs(k) < 4 else d5.B2)
        cv.put(gx - 2, gy + 1, d5.INK2)
        cv.put(gx + 2, gy + 1, d5.INK2)
        if i == 0:                                       # 흙먼지·불티
            for k in range(6):
                a = math.pi + k * math.pi / 5
                cv.put(gx + math.cos(a) * (6 + k % 2), gy - 2 + math.sin(a) * 4, d5.S1 if k % 2 else d5.S2)
            cv.put(gx + 3, gy - 6, d5.A23)
            cv.put(gx - 4, gy - 5, d5.A21)
        if 2 <= i <= 5:                                  # 날선을 타고 오르는 반짝임
            s = 0.8 - 0.17 * (i - 2)
            x, y = geo.w(geo.L * s, BL.vc_of(s, geo.L) + BL.hw_of(s, geo.L, 0.85) - 0.6)
            cv.put(x, y, d5.A25)
            if i == 4:
                f = Frame(cv, x, y, 0)
                f.xglint(0, 0, 2, core=d5.A25, mid=d5.A23, edge=d5.A21)
        if i == 7:
            for k in range(7):
                cv.put(gx - 3 + k, gy - 1 - (k % 2), d5.B2 if k % 2 else d5.S1)
        rows[0].append(cv.im)
    return rows


# =============================================================================
# 쌍격 분신 (dagger_cross_clone) — 분신은 먹빛으로, 교차 베기는 발톱 X 로 다시
# =============================================================================
def cross_clone(m, fr):
    W, H = m["frameWidth"], m["frameHeight"]
    glow = set(m.get("glowFrames") or [3])
    rows = []
    for ri, d in enumerate(m["directions"]):
        # 옛 X 붓획 = 호박 픽셀 중 분신 몸(비호박)에서 3 도트 넘게 떨어진 것
        def strokes(im):
            p = im.load()
            body = set((x, y) for y in range(im.height) for x in range(im.width) if p[x, y][3] and not is_amber(p[x, y]))
            near = set()
            for (x, y) in body:
                for dy in range(-3, 4):
                    for dx in range(-3, 4):
                        near.add((x + dx, y + dy))
            return [(x, y) for y in range(im.height) for x in range(im.width) if p[x, y][3] and is_amber(p[x, y]) and (x, y) not in near]
        s3 = strokes(fr[ri][4]) or strokes(fr[ri][3])
        if s3:
            cx = sum(p[0] for p in s3) / float(len(s3))
            cy = sum(p[1] for p in s3) / float(len(s3))
            ext = max(math.hypot(p[0] - cx, p[1] - cy) for p in s3)
        else:
            cx, cy, ext = W / 2.0, H / 2.0, 30
        row = []
        for i in range(m["frames"]):
            old = fr[ri][i]
            cv = Cv(W, H)
            p = old.load()
            st = set(strokes(old)) if i >= 3 else set()
            for y in range(H):                           # 분신 몸: 먹빛으로 바꿔 칠함(호박 테는 남김)
                for x in range(W):
                    c = p[x, y]
                    if not c[3] or (x, y) in st:
                        continue
                    if is_amber(c):
                        if i >= 3:                       # 몸 테가 아닌 호박(옛 붓획 찌꺼기)은 버림
                            nb = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                                     if 0 <= x + dx < W and 0 <= y + dy < H and p[x + dx, y + dy][3] and not is_amber(p[x + dx, y + dy]))
                            if nb < 2:
                                continue
                        col = c if c[:3] in d5.FX_ALLOWED and c[:3] not in d5.GLOW_ONLY else d5.A21
                        if i not in glow and col[:3] in d5.GLOW_ONLY:
                            col = d5.A25
                    else:
                        lum = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
                        col = d5.S0 if lum > 85 else d5.INK2 if lum > 40 else d5.INK
                    cv.put(x, y, col)
            if i >= 3:                                   # 교차 발톱 X
                age = i - 3
                fx, fy = BL.FACING.get(d, (1, 0))
                base = math.degrees(math.atan2(fy, fx))
                for sg in (1, -1):
                    f = Frame(cv, cx, cy, base + 42 * sg)
                    ln = min(ext * 0.95, 0.85 * min(cx, W - cx, cy, H - cy))
                    if age == 0:
                        f.claw(-ln, ln, 6.5, [(1.0, EM.dim), (0.7, EM.body), (0.45, EM.mid), (0.22, EM.hot if i in glow else EM.h2)],
                               hook=6 * sg, peak=0.75)
                    elif age == 1:
                        f.claw(-ln, ln, 5.0, [(1.0, EM.dark), (0.6, EM.dim), (0.3, EM.body)], hook=6 * sg, peak=0.75)
                    elif age <= 4:
                        for k in range(5):
                            if (k + age) % 2:
                                continue
                            a0 = -ln + 2 * ln * k / 5.0
                            f.claw(a0, a0 + ln * 0.25, 2.6, [(1.0, EM.dark if age < 4 else EM.ash)], hook=0, voff=6 * sg * ((a0 + ln) / (2 * ln)) ** 2.2,
                                   peak=0.5, back=0.3)
                if age == 0:
                    Frame(cv, cx, cy, 0).xglint(0, 0, 10, core=EM.core if i in glow else EM.h2, mid=EM.hot if i in glow else EM.mid, edge=EM.h2, tilt=45)
                elif age == 1:
                    Frame(cv, cx, cy, 0).xglint(0, 0, 6, core=EM.h2, mid=EM.mid, edge=EM.dim, tilt=45)
            d5.clip_margin(cv.im, 1)
            row.append(cv.im)
        rows.append(row)
    return rows


# =============================================================================
# 백귀 세 갈래 (dagger_hundred_ghosts) — 다가오는 혼불(옛 그림) → 세 갈래 발톱 베기 → 청록·보라 부스러기
# =============================================================================
def hundred_ghosts(m, fr):
    W, H = m["frameWidth"], m["frameHeight"]
    cx, cy = m["pivot"]["x"], m["pivot"]["y"]
    ON = T.ONIBI
    glow = set(m.get("glowFrames") or [3])
    row = []
    for i in range(m["frames"]):
        if i < 3:
            row.append(fr[0][i].copy())
            continue
        cv = Cv(W, H)
        age = i - 3
        for k in range(3):
            a = 120 * k - 90
            f = Frame(cv, cx, cy, a)
            if age == 0:
                f.claw(-46, 52, 8, [(1.0, ON.dim), (0.7, ON.body), (0.45, ON.mid), (0.25, ON.h2), (0.1, ON.hot)], hook=12, peak=0.72)
            elif age == 1:
                f.claw(-30 + 20, 70, 6, [(1.0, ON.dark), (0.6, ON.body), (0.3, ON.h3)], hook=14, peak=0.78)
            elif age == 2:
                for j in range(4):
                    if j % 2:
                        continue
                    u0 = 30 + 12 * j
                    f.claw(u0, u0 + 10, 3, [(1.0, ON.dim)], voff=14 * ((u0 + 30) / 100.0) ** 2.2, peak=0.5, back=0.3)
            r = Rand(300 + k * 7 + i)
            for q in range(10 - age):
                u = 30 + 50 * r.f() + 8 * age
                v = (r.f() * 2 - 1) * 12
                f.put(u, v, [ON.h2, ON.mid, ON.dim, ON.ash][(q + age) % 4])
        if age == 0:
            Frame(cv, cx, cy, 0).xglint(0, 0, 14, core=ON.core, mid=ON.hot, edge=ON.h2, tilt=45)
        elif age == 1:
            Frame(cv, cx, cy, 0).xglint(0, 0, 8, core=ON.h3, mid=ON.h2, edge=ON.mid, tilt=45)
        row.append(cv.im)
    return [row]


# =============================================================================
# 각성 순간 (dagger_awaken_in) — 머리 위 발톱 날이 끝부터 귀화로 타들어 감
# =============================================================================
def awaken_in(m, fr):
    W, H = m["frameWidth"], m["frameHeight"]
    geo = BL.Geo((15.0, 24.0), (47.0, 23.0), facing=(0.0, 1.0))
    base_sk, oni = BL.BaseSkin(), OV.OnibiSkin()
    glow = set(m.get("glowFrames") or [7])
    pxs = BL.blade_px(geo)
    row = []
    for i in range(m["frames"]):
        cv = Cv(W, H)
        st = "glow" if i in glow else "steel"
        t = 0 if i == 0 else min(1.0, i / 6.0) if i < 7 else 1.0
        gone = 0.0 if i < 10 else (0.45 if i == 10 else 0.8)
        for (x, y), (part, s, dd) in pxs.items():
            if gone and h2(x, y, 99) < gone:
                continue
            u, v = geo.loc(x, y)
            burn = (1.0 - u / geo.L) < t * 1.15 - 0.1 * h2(x, y, 5)    # 끝부터 귀화로
            sk = oni if burn or i >= 7 else base_sk
            c = sk.col(part, s, dd, st if i == 7 else "steel", x, y, i % 6)
            if c:
                cv.put(x, y, c)
        if 3 <= i <= 10:                                  # 등 위 혼불
            OVc = Cv(W, H)
            OV.onibi_wisps(OVc, geo, "steel", i % 6)
            for yy in range(H):
                for xx in range(W):
                    c = OVc.p[xx, yy]
                    if c[3] and 0 <= xx - OV.PAD < W and 0 <= yy - OV.PAD < H:
                        cv.put(xx - OV.PAD, yy - OV.PAD, c)
        if i == 7:
            Frame(cv, 47, 23, 0).xglint(0, 0, 8, core=d5.X0, mid=d5.X1, edge=d5.TEAL[10], tilt=45)
            cv.ring(31, 23, 19, d5.X1, ky=0.42)
        if i == 8:
            cv.ring(31, 23, 25, d5.VIO[8], ky=0.42, dash=(20, 14))
            cv.ring(31, 23, 22, d5.TEAL[8], ky=0.42, dash=(10, 24), phase=12)
        if i == 9:
            cv.ring(31, 23, 28, d5.VIO[5], ky=0.42, dash=(8, 22))
        row.append(cv.im)
    return [row]
