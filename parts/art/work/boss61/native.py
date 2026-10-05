#!/usr/bin/env python3
"""61라운드 단계 4 아트 — 보스 '만취' 마무리: 불타는 오버레이·잔 깨짐 1.5배 네이티브 재그림 · 가벼운 림(대검 런용). 결정적.

사용: python3 parts/art/work/boss61/native.py [onfire] [down] [cup] [rimlite] [--dry]   (인자 없으면 전부)
  onfire  : fx/v3/boss1_onfire        288×360 · 피벗 (144,330) · 4행 × 16 — 54라운드 onfire.py 의 연료장·불꽃 식을 1.5배 판에서 다시 래스터
  down    : fx/v3/boss1_onfire_down   288×360 · 피벗 (144,330) · 1행 × 16 — 54라운드 onfire_down.py 같은 방식(누운 몸 윤곽 = 1.5배 fall·death 시트)
  cup     : fx/v3/boss1_cup_shatter   192×192 · 피벗 (96,90) · 8 — 1.5배 잔(약 44×55)에 맞춰 새로 그림(54 그림의 동작·시간 그대로)
  rimlite : bosses/v3/stage1_<동작>_rim_lite  144×180 · 피벗 (72,165) · pixelScale 1.0 — 림 시트 반 해상도(메모리 약 1/4)
(서 있는 꺼진 촛대는 readable.candelabra_fix → build.py --only boss1_candelabra)

방식(불길): 연료장(fuel_map)·위로 번짐(smear)은 54라운드 코드를 그대로 192×240 '원 좌표'에서 만들고, 불꽃은 288×360 의 각 도트에서
원 좌표 (X/1.5, Y/1.5)로 연속 표본(세기장 쌍선형 보간 + 같은 물결·무늬 식)을 떠서 다시 문턱 → 최근접 확대처럼 2·1 칸 계단이 생기지 않고
혀 끝·가장자리가 1 도트 단위로 다듬어진다. 몸 윤곽은 1.5배 보스 시트(idle·walk / fall·death)에서 다시 잼. 혀 무늬에 짧은 주기 한 겹(밀도용) 추가.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "boss1_v3"))
sys.path.insert(0, os.path.join(HERE, "..", "v2_outer"))
sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))

import k61  # noqa: E402
from k61 import b2, Cv, G, A, X, ROOT  # noqa: E402
import gridsheet  # noqa: E402
import onfire as OF  # noqa: E402   (54라운드 — 연료장·색 함수만 쓴다. main 은 부르지 않음)
import onfire_down as OD  # noqa: E402
from kit import Rand  # noqa: E402
from PIL import Image  # noqa: E402

K = 1.5
FW, FH = 288, 360
PIV = (144, 330)
SW, SH = OF.FW, OF.FH            # 원 좌표(192×240)
DIRS = OF.DIRS
BOSS = os.path.join(ROOT, "assets", "sprites", "bosses", "v3")
FX = os.path.join(ROOT, "assets", "sprites", "fx", "v3")
SRC = "parts/art/work/boss61/native.py (61라운드 단계 4 — 1.5배 네이티브 재그림)"
PREV = {"frameWidth": 192, "frameHeight": 240, "pivot": {"x": 96, "y": 220}}


# ------------------------------------------------------------------------------------------- 공용
def frames_of(act, row=None):
    jp = os.path.join(BOSS, "stage1_%s.json" % act)
    m = gridsheet.load_meta(jp)
    g = gridsheet.open_grid(jp)
    n = m["frames"]
    rows = range(len(m["directions"])) if row is None else [row]
    return [[g.crop((c * FW, r * FH, (c + 1) * FW, (r + 1) * FH)) for c in range(n)] for r in rows]


def smooth_env(lo, hi):
    e = {}
    for y in lo:
        ys = [yy for yy in range(y - 2, y + 3) if yy in lo]
        e[y] = (sum(lo[yy] for yy in ys) / len(ys), sum(hi[yy] for yy in ys) / len(ys))
    return e


def bilerp(S, x, y):
    x0, y0 = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - x0, y - y0
    v = 0.0
    for dx, dy, w in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        xx, yy = x0 + dx, y0 + dy
        if 0 <= xx < SW and 0 <= yy < SH and w:
            v += S[yy][xx] * w
    return v


def fire_hd(cv, S, t, gain=1.0, ycut=None, seed=0.0):
    """OF.fire 와 같은 식을 288×360 각 도트에서 원 좌표로 표본. 밀도용으로 짧은 주기 무늬 한 겹(+0.06)."""
    T = 2 * math.pi * t
    for Y in range(FH):
        y = (Y + 0.5) / K - 0.5
        if ycut is not None and y < ycut:
            continue
        wy = 2.4 * math.sin(0.085 * y + 2 * T + seed) + 0.8 * math.sin(0.17 * y + 3 * T + 1.3 + seed)
        stretch = 1 + 0.0025 * (SH - y)
        for Xp in range(FW):
            x = (Xp + 0.5) / K - 0.5
            xs = x + wy * stretch
            if not (-1 < xs < SW):
                continue
            s = bilerp(S, xs, y)
            if s <= 0.2:
                continue
            xw = x + wy
            c = (0.5 * math.sin(0.47 * xw + 2 * T + seed) + 0.3 * math.sin(0.83 * xw - 3 * T + 1.0 + seed)
                 + 0.2 * math.sin(0.29 * xw + 1 * T + 2.3 + seed)) * 0.5 + 0.5
            fl = 0.1 * math.sin(0.23 * y + 4 * T + 0.37 * x) + 0.06 * math.sin(1.31 * xw + 0.4 * y - 4 * T + seed)
            v = s * gain * (0.5 + 0.62 * c + fl)
            col = OF.ramp_col(v)
            if col is not None:
                cv.put(Xp, Y, col)
    # 외톨이 점·한 도트 가시 정리(4 이웃 중 불 ≤ 1 이고 위아래가 다 비면 지움)
    px = cv.im.load()
    kill = []
    for Y in range(1, FH - 1):
        for Xp in range(1, FW - 1):
            if not px[Xp, Y][3]:
                continue
            nb = (px[Xp - 1, Y][3] > 0) + (px[Xp + 1, Y][3] > 0) + (px[Xp, Y - 1][3] > 0) + (px[Xp, Y + 1][3] > 0)
            if nb == 0:
                kill.append((Xp, Y))
    for Xp, Y in kill:
        px[Xp, Y] = (0, 0, 0, 0)


def embers_hd(cv, pts, t, n, seed, rise=70, k=1):
    """OF.embers 와 같은 난수 순서·궤적(원 좌표) → 1.5배 자리에 머리 1 도트 + 아래 꼬리 1 도트(식은 색)."""
    r = Rand(seed)
    for j in range(n):
        bx, by = pts[r.i(0, len(pts) - 1)]
        s = r.f()
        q = (k * t + s) % 1.0
        x = bx + r.i(-6, 6) + 4 * math.sin(2 * math.pi * (q + s))
        y = by - 6 - q * rise
        ci = min(3, int(q * 4))
        X_, Y_ = int(round(x * K)), int(round(y * K))
        cv.put(X_, Y_, OF.EMBER[ci])
        cv.put(X_, Y_ + 1, OF.EMBER[min(3, ci + 1)])
        if q < 0.35 and j % 3 == 0:
            cv.put(X_, Y_ - 1, OF.EMBER[0])


def ash_hd(cv, pts, t, n, seed):
    r = Rand(seed)
    for j in range(n):
        bx, by = pts[r.i(0, len(pts) - 1)]
        s = r.f()
        q = (t + s) % 1.0
        x = bx + r.i(-8, 8) + 5 * math.sin(2 * math.pi * (q + s))
        y = by - 6 - q * 46
        col = OF.ASH[min(2, int(q * 3))]
        X_, Y_ = int(round(x * K)), int(round(y * K))
        cv.put(X_, Y_, col)
        if j % 2 == 0:
            cv.put(X_ + 1, Y_, col)
        if j % 3 == 0:
            cv.put(X_, Y_ - 1, col)


def phase_params(phase, i, ycuts_ign, ycuts_out):
    if phase == "ignite":
        return ycuts_ign[i], [0.66, 0.84, 0.95, 1.0][i], (i - OF.N_IGN) / OF.N_LOOP
    if phase == "out":
        return ycuts_out[i], [0.92, 0.8, 0.66, 0.5][i], (OF.N_LOOP + i) / OF.N_LOOP
    return None, 1.0, i / OF.N_LOOP


PHASES = [("ignite", i) for i in range(OF.N_IGN)] + [("loop", i) for i in range(OF.N_LOOP)] + [("out", i) for i in range(OF.N_OUT)]


# ------------------------------------------------------------------------------------------- 서 있는 불길
def stand_envelopes():
    """1.5배 idle·walk 전 프레임 윤곽 합집합 → 원 좌표 높이별 (왼, 오) (54 envelopes 와 같은 뜻)."""
    sheets = [frames_of("idle"), frames_of("walk")]
    env = {}
    for r, d in enumerate(DIRS):
        lo, hi = {}, {}
        for sh in sheets:
            for im in sh[r]:
                al = im.getchannel("A").load()
                for Y in range(FH):
                    xs = [Xp for Xp in range(FW) if al[Xp, Y] == 255]
                    if xs:
                        y = int(Y / K)
                        lo[y] = min(lo.get(y, 999), xs[0] / K)
                        hi[y] = max(hi.get(y, -1), xs[-1] / K)
        env[d] = smooth_env(lo, hi)
    return env


def build_onfire():
    env = stand_envelopes()
    rows = []
    for d in DIRS:
        fu = OF.fuel_map(d, env[d])
        S0 = OF.smear(fu)
        roots = sorted({(x, y) for (x, y) in fu if (x + 3 * y) % 23 == 0}, key=lambda p: (p[1], p[0]))
        row = []
        for phase, i in PHASES:
            cv = Cv(FW, FH)
            ycut, gain, t = phase_params(phase, i, [206, 176, 136, 96], [120, 160, 192, 214])
            S = S0 if ycut is None else OF.smear({p: v for p, v in fu.items() if p[1] >= ycut})
            fire_hd(cv, S, t, gain)
            live = [(x, y) for (x, y) in roots if ycut is None or y >= ycut]
            if phase == "ignite":
                embers_hd(cv, [(OF.PIV[0] + dx, 222) for dx in range(-44, 45, 8)], 0.3 + 0.2 * i, 18 - 3 * i, 5 + i, rise=40 + 30 * i)
            elif phase == "out":
                ash_hd(cv, roots[::3], 0.22 * i, 10 + 6 * i, 40 + i)
                if live:
                    embers_hd(cv, live, 0.15 * i, max(0, 14 - 3 * i), 50 + i, rise=60)
            else:
                embers_hd(cv, roots, t, 26, 21, rise=80)
            row.append(cv.im)
        rows.append(row)
        print("onfire", d)
    m = gridsheet.load_meta(os.path.join(FX, "boss1_onfire.json"))
    meta = {k: v for k, v in m.items() if k not in ("image", "frameWidth", "frameHeight", "frames", "frameDurationsMs", "loop", "pixelScale")}
    meta["anchorNote"] = m["anchorNote"].replace("192×240, 피벗 (96,220)", "288×360, 피벗 (144,330)")
    meta.update(nativeNote=("61라운드 단계 4: 1.5배 네이티브 재그림 — 54라운드 연료장·불꽃 식을 288×360 판에서 다시 래스터(최근접 확대 아님), "
                            "몸 윤곽은 1.5배 idle·walk 에서 다시 잼. 틀·피벗·열 배치·ms·light·lightByPhase 는 61 단계 3 값 그대로"),
                source=SRC, previousSize=PREV, version="v3-r61", action="onfire")
    return "fx", "boss1_onfire", rows, meta, m["frameDurationsMs"], m.get("loop", True)


# ------------------------------------------------------------------------------------------- 누운 불길
def body_pts(act, im):
    """OD.body_alpha 와 같은 제외 규칙(원 좌표)을 1.5배 그림에 적용 → 원 좌표 점 목록(실수)."""
    a = im.getchannel("A").load()
    out = []
    for Y in range(FH):
        for Xp in range(FW):
            if a[Xp, Y] != 255:
                continue
            x, y = Xp / K, Y / K
            if act == "fall" and x < 64 and y < 108:
                continue
            if act == "death" and (y >= 212 or x >= 172 or (x < 66 and y > 196)):
                continue
            out.append((Xp, Y, x, y))
    return out


def lying_envelope(ff, df):
    def env_of(act, frames):
        lo, hi = {}, {}
        for im in frames:
            for _, _, x, y in body_pts(act, im):
                yi = int(y)
                lo[yi] = min(lo.get(yi, 999), x)
                hi[yi] = max(hi.get(yi, -1), x)
        return lo, hi
    l1, h1 = env_of("fall", [ff[i] for i in OD.FALL_LYING])
    l2, h2 = env_of("death", [df[i] for i in OD.DEATH_LYING])
    lo, hi = {}, {}
    for y in set(l1) & set(l2):
        a, b = max(l1[y], l2[y]), min(h1[y], h2[y])
        if b - a >= 6:
            lo[y], hi[y] = a, b
    return smooth_env(lo, hi)


def frame_offsets(ff, df):
    """누운 불길을 쓰는 보스 프레임별 [dx, dy](1.5배 도트) — 몸 아랫선(폭 90 도트 이상 줄)을 fall 6 에 맞춤."""
    frames = {"fall": ff, "death": df}

    def bottom(act, im):
        rows = {}
        for Xp, Y, _, _ in body_pts(act, im):
            rows.setdefault(Y, []).append(Xp)
        return max(Y for Y, xs in rows.items() if len(xs) >= 90)
    y0 = bottom(OD.REF[0], frames[OD.REF[0]][OD.REF[1]])
    out = {}
    for act, idx in OD.USE_DOWN.items():
        out[act] = {}
        for i in idx:
            dy = bottom(act, frames[act][i]) - y0
            out[act][str(i)] = [0, 0 if abs(dy) <= 3 else dy]
    return out


def build_onfire_down():
    ff = frames_of("fall", 0)[0]
    df = frames_of("death", 0)[0]
    e = lying_envelope(ff, df)
    fu = OD.fuel_map(e)
    S0 = OD.masked_smear(fu)
    roots = sorted({(x, y) for (x, y) in fu if (x + 3 * y) % 23 == 0}, key=lambda p: (p[1], p[0]))
    ring = [(OF.PIV[0] + dx, 222) for dx in range(-56, 57, 8)]
    row = []
    for phase, i in PHASES:
        cv = Cv(FW, FH)
        ycut, gain, t = phase_params(phase, i, [208, 188, 160, 122], [148, 176, 198, 214])
        S = S0 if ycut is None else OD.masked_smear({p: v for p, v in fu.items() if p[1] >= ycut})
        fire_hd(cv, S, t, gain)
        live = [(x, y) for (x, y) in roots if ycut is None or y >= ycut]
        if phase == "ignite":
            embers_hd(cv, ring, 0.3 + 0.2 * i, 18 - 3 * i, 85 + i, rise=34 + 22 * i)
        elif phase == "out":
            ash_hd(cv, roots[::3], 0.22 * i, 10 + 6 * i, 90 + i)
            if live:
                embers_hd(cv, live, 0.15 * i, max(0, 14 - 3 * i), 95 + i, rise=52)
        else:
            embers_hd(cv, roots, t, 26, 81, rise=70)
        px = cv.im.load()
        for Y in range(FH):
            for Xp in range(FW):
                if px[Xp, Y][3] and OD.in_face(Xp / K, Y / K, 1):
                    px[Xp, Y] = (0, 0, 0, 0)
        row.append(cv.im)
    m = gridsheet.load_meta(os.path.join(FX, "boss1_onfire_down.json"))
    meta = {k: v for k, v in m.items() if k not in ("image", "frameWidth", "frameHeight", "frames", "frameDurationsMs", "loop", "pixelScale")}
    meta["frameOffsets"] = frame_offsets(ff, df)
    meta.update(nativeNote=("61라운드 단계 4: 1.5배 네이티브 재그림 — 누운 몸 윤곽을 1.5배 fall·death 에서 다시 재고 288×360 판에서 다시 래스터"
                            "(최근접 확대 아님). frameOffsets 도 1.5배 판에서 다시 잼(도트). 틀·피벗·열 배치·ms·light 는 그대로"),
                source=SRC, previousSize=PREV, version="v3-r61", action="onfire_down")
    print("onfire_down", meta["frameOffsets"])
    return "fx", "boss1_onfire_down", [row], meta, m["frameDurationsMs"], m.get("loop", True)


# ------------------------------------------------------------------------------------------- 잔 깨짐
CS = 192
CSP = (96, 90)
WD_, IR_ = None, None


def _piece(cv, pts_cols, dark):
    """pts_cols: {(x, y): 색} — 조각 하나. 바깥 1 도트 어두운 테(조각끼리 섞여도 읽히게) → 속 칠."""
    s = set(pts_cols)
    for (x, y) in s:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in s:
                cv.put(q[0], q[1], dark)
    for (x, y), c in pts_cols.items():
        cv.put(x, y, c)


def _stave(cx, cy, ang, ln, wd, bend, wood, iron_at=None, iron=None):
    """휜 널 조각: 길이 ln · 폭 wd(도트). 바깥 면(위) 밝게 → 본색 → 안쪽 그늘, 끝 마구리 어둡게, 결 1 줄. iron_at = 쇠테 조각 위치(0~1)."""
    ca, sa = math.cos(ang), math.sin(ang)
    out = {}
    n = int(ln * 2) + 1
    for i in range(n):
        u = -ln / 2 + ln * i / max(1, n - 1)
        b = bend * (u / (ln / 2)) ** 2
        for k in range(int(wd * 2) + 1):
            v = -wd / 2 + wd * k / max(1, int(wd * 2))
            vv = v + b
            x, y = cx + ca * u - sa * vv, cy + sa * u + ca * vv
            key = (int(round(x)), int(round(y)))
            fv = (v + wd / 2) / wd                     # 0 = 바깥 면, 1 = 안쪽
            end = abs(u) > ln / 2 - 1.2
            if iron_at is not None and abs(u - (iron_at - 0.5) * ln) < 1.3:
                col = iron[4] if fv < 0.35 else (iron[3] if fv < 0.75 else iron[1])
            elif end:
                col = wood[1] if fv < 0.5 else wood[0]
            else:
                col = wood[4] if fv < 0.22 else (wood[3] if fv < 0.62 else (wood[2] if fv < 0.85 else wood[1]))
                if abs(fv - 0.5) < 0.12 and (i // 3) % 3 == 1:
                    col = wood[2]                       # 결
            if key not in out or (iron is not None and col in (iron[4], iron[3])):
                out[key] = col
    return out


def build_cup_shatter():
    """1.5배 잔(약 44×55 · 널 8장 · 쇠테 3줄 · 호박 술면)에 맞춰 새로 그림. 54라운드 그림의 동작·시간(8 × 40~120ms)·판정 프레임 0 그대로.
    0 = 잔 윤곽을 따라 갈라지는 백열 금 + 십자 섬광 / 1~7 = 널 9장이 회전하며 솟았다 떨어짐(일부 쇠테 조각 붙음) · 쇠테 3줄이 기울어 벌어지며
    끊겨 떨어짐 · 술 덩이(밝은 점 있는 2~4 도트 방울)가 솟았다 떨어짐 · 첫 두 칸 술 고리 · 나뭇조각."""
    from pk import R_WOOD, R_IRON  # noqa: F401
    WOOD_HI = [R_WOOD[1], R_WOOD[2], R_WOOD[3], R_WOOD[4], R_WOOD[5]]     # 잔 널(1.5배 보스 잔과 같은 밝기 — 54 조각보다 한 단 밝게)
    IRON_HI = [G[4], G[6], G[7], G[9], G[11]]                             # 잔 쇠테(밝은 회색)
    r = Rand(3)
    cx, cy = CSP
    RX, RY = 22, 27                                    # 잔 반폭·반높이(1.5배 보스 cupAnchors 44×55)
    staves = [((k + r.f() * 0.5) * 2 * math.pi / 9, 0.55 + 0.6 * r.f(), 15 + r.i(0, 7), r.f() * 3.0, k % 3 == 0) for k in range(9)]
    chips = [(r.f() * 2 * math.pi, 0.4 + r.f() * 0.8) for _ in range(18)]
    drops = [(math.pi * (1.0 + r.f()), 0.4 + r.f() * 0.8) for _ in range(26)]
    frames = []
    for i in range(8):
        cv = Cv(CS, CS)
        t = i / 7
        if i == 0:
            # 잔이 갈라지는 순간: 가운데에서 잔 테두리까지 뻗는 들쭉날쭉한 백열 금 5갈래 + 십자 섬광(판정 프레임). 잔 그림은 보스 시트가 그린다
            rc = Rand(11)
            for k in range(5):
                a0 = -math.pi / 2 + (k - 2) * 0.95 + (rc.f() - 0.5) * 0.4
                x, y = float(cx), float(cy)
                steps = 9
                for st in range(steps):
                    a1 = a0 + (rc.f() - 0.5) * 0.9
                    seg = 3.2 + rc.f() * 1.6
                    nx, ny = x + math.cos(a1) * seg * RX / 18, y + math.sin(a1) * seg * RY / 18
                    col = X[0] if st < 2 else (A[26] if st < 5 else A[24])
                    cv.line(x, y, nx, ny, col, w=2 if st < 4 else 1)
                    x, y = nx, ny
            arm = 30
            for k in range(-arm, arm + 1):
                c = X[0] if abs(k) < 9 else (A[26] if abs(k) < 20 else A[24])
                cv.put(cx + k, cy, c); cv.put(cx, cy + k, c)
            for k in range(-5, 6):                      # 가운데 굵게
                cv.put(cx + k, cy - 1, X[1]); cv.put(cx + k, cy + 1, X[1]); cv.put(cx - 1, cy + k, X[1]); cv.put(cx + 1, cy + k, X[1])
            for k in range(-11, 12):
                c = A[25] if abs(k) > 4 else X[1]
                cv.put(cx + k, cy + k, c); cv.put(cx + k, cy - k, c)
            cv.disc(cx, cy, 2.5, X[0])
        else:
            # 술 고리(처음 두 칸)
            if i < 3:
                rad = 18 + 21 * t
                cv.ring(cx, cy, rad, 2, A[23] if i < 2 else A[21], ky=0.8, dash=(26, 9), phase=i * 11)
            # 술 덩이(솟았다 떨어짐) — 큰 것은 밝은 점·그늘 점
            for (a, sp) in drops:
                d = 9 + 72 * sp * min(1.0, t * 1.4)
                x = cx + math.cos(a) * d
                y = cy + math.sin(a) * d * 0.9 + 66 * t * t
                big = sp > 0.6 and t < 0.7
                col = A[24] if t < 0.3 else (A[22] if t < 0.6 else A[20])
                if big:
                    cv.disc(x, y, 2.1 if t < 0.4 else 1.6, col)
                    cv.put(x - 1, y - 1, A[25] if t < 0.6 else A[23])
                else:
                    cv.put(x, y, col); cv.put(x, y + 1, col)
                    if sp > 0.55:
                        cv.put(x + 1, y, col)
            # 쇠테: 2줄은 기울어 벌어지며 떨어지고(끊긴 자리 하나씩), 1줄은 반쪽 호로 부러져 반대편으로 — 2 도트 띠(앞 밝음 · 뒤 어둠)
            HOOPS = ((-14, -10, 0.4, 0.4, -1.0, 1.0), (16, 6, -0.6, 0.46, 1.2, 1.0), (-4, 18, 0.25, 0.42, -0.7, 0.5))
            for j, (ox, oy, rot0, sq, spin, frac) in enumerate(HOOPS):
                if i >= 6 and j == 1:
                    continue
                hx = cx + ox * (1 + 1.8 * t)
                hy = cy + oy + (-8 + 10 * j) * t + 52 * t * t
                rr = 19 + 5 * t
                rot_ = rot0 + spin * t
                cr, sr = math.cos(rot_), math.sin(rot_)
                gap0 = 0.12 + 0.3 * j
                for k in range(200):
                    u = k / 200
                    if u > frac or (frac == 1.0 and gap0 <= u < gap0 + 0.11):
                        continue
                    a_ = 2 * math.pi * u + (0.0 if frac == 1.0 else math.pi * 0.1)
                    ex, ey = math.cos(a_) * rr, math.sin(a_) * rr * sq
                    front = math.sin(a_) > 0
                    px_, py_ = hx + ex * cr - ey * sr, hy + ex * sr + ey * cr
                    cv.put(px_, py_ + 1, G[7] if front else G[4])
                    cv.put(px_, py_, G[11] if front else G[6])
            # 널 조각
            for (a, sp, ln, spin, iron) in staves:
                d = 12 + 69 * sp * t
                x = cx + math.cos(a) * d
                y = cy + math.sin(a) * d * (0.75 if math.sin(a) < 0 else 0.42) - 45 * sp * t * (1 - t) * 2 + 48 * t * t   # 아래로 튄 것은 바닥이 가까워 짧게
                ang = a + math.pi / 2 + t * (4 + spin)
                pc = _stave(x, y, ang, ln, 4.5, 1.6, WOOD_HI, iron_at=0.33 if iron else None, iron=IRON_HI)
                _piece(cv, pc, R_WOOD[1])
            # 나뭇조각
            W_ = [R_WOOD[2], R_WOOD[4], R_WOOD[5]]
            for (a, sp) in chips:
                d = 9 + 75 * sp * t
                x = cx + math.cos(a) * d
                y = cy + math.sin(a) * d * (0.8 if math.sin(a) < 0 else 0.4) + 56 * t * t
                c0 = W_[int(sp * 10) % 3]
                cv.put(x, y, c0)
                cv.put(x + 1, y, W_[(int(sp * 10) + 1) % 3])
                if sp > 0.8:
                    cv.put(x, y + 1, R_WOOD[1])
        frames.append(cv.im)
    m = gridsheet.load_meta(os.path.join(FX, "boss1_cup_shatter.json"))
    meta = {k: v for k, v in m.items() if k not in ("image", "frameWidth", "frameHeight", "frames", "frameDurationsMs", "loop", "pixelScale")}
    meta.update(nativeNote=("61라운드 단계 4: 1.5배 네이티브 재그림 — 1.5배 보스 잔(약 44×55 · 쇠테 3줄)에 맞춰 새로 그림(최근접 확대 아님). "
                            "널 조각 4~5 도트 폭(밝은 면·본색·그늘·결·어두운 테) · 쇠테 2 도트 띠 3줄 · 술 방울 밝은 점. "
                            "틀 192×192 · 피벗 (96,90) · 8프레임 · ms · glowFrames [0] 그대로"),
                source=SRC, previousSize={"frameWidth": 128, "frameHeight": 128, "pivot": {"x": 64, "y": 60}}, version="v3-r61")
    return "fx", "boss1_cup_shatter", [frames], meta, m["frameDurationsMs"], m.get("loop", False)


# ------------------------------------------------------------------------------------------- 가벼운 림(대검 런용)
RIM_ACTS = ["idle", "walk", "attack", "stagger_dash", "hurt"]
LW, LH, LPIV = FW // 2, FH // 2, (PIV[0] // 2, PIV[1] // 2)
RIM_OUT, RIM_IN, RIM_HI = A[23], A[21], A[25]


def rim_lite_frame(im):
    """보스 프레임(288×360)을 2×2 다수결(4 중 2 이상 불투명) 실루엣(144×180)으로 줄이고, 그 안쪽 가장자리 1 도트(= 원 판 2 도트)에 역광:
    위·오른쪽 A23(모서리 A25), 아래·왼쪽 A21 성긴 점선(3칸에 1) — 원 림(위·오른쪽 2 도트 + 아래·왼쪽 1 도트 점선)과 화면에서 비슷한 굵기·세기."""
    a = im.getchannel("A").load()
    m = [[sum(a[2 * x + dx, 2 * y + dy] == 255 for dx in (0, 1) for dy in (0, 1)) >= 2 for x in range(LW)] for y in range(LH)]
    out = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    o = out.load()
    on = lambda x, y: 0 <= x < LW and 0 <= y < LH and m[y][x]  # noqa: E731
    for y in range(LH):
        for x in range(LW):
            if not m[y][x]:
                continue
            up, rt, lf, dn = not on(x, y - 1), not on(x + 1, y), not on(x - 1, y), not on(x, y + 1)
            if up or rt:
                o[x, y] = RIM_HI if (up and rt) else RIM_OUT
            elif (lf or dn) and (x + y) % 3 == 0:      # 반 해상도에서 점 하나가 2 도트라 원 림(격자 점선)보다 성기게
                o[x, y] = RIM_IN
    return out


def build_rim_lite():
    res = []
    for act in RIM_ACTS:
        base = "stage1_%s" % act
        jp = os.path.join(BOSS, base + ".json")
        m = gridsheet.load_meta(jp)
        g = gridsheet.open_grid(jp)
        n = m["frames"]
        rows = [[rim_lite_frame(g.crop((i * FW, r * FH, (i + 1) * FW, (r + 1) * FH))) for i in range(n)] for r in range(len(m["directions"]))]
        meta = {
            "directions": m["directions"], "pivot": {"x": LPIV[0], "y": LPIV[1]}, "version": "v3-r61",
            "pixelScale": 1.0, "renderScaleHint": 1.0, "liteScale": 2,
            "overlayOf": "bosses/v3/" + base, "liteOf": "bosses/v3/" + base + "_rim",
            "drawRule": ("가벼운 림(대검 런 등 VRAM 이 빠듯할 때 _rim 대신). 원 림 시트(288×360·피벗 (144,330)·pixelScale 0.5)의 반 해상도판: "
                         "144×180·피벗 (72,165)·pixelScale 1.0 → 논리 크기·논리 피벗이 원 림·보스와 같다(144×180 논리 px, 피벗 (72,165) 논리 px). "
                         "겹침 규칙: ① 보스 시트와 같은 프레임 번호(row*columns+column)·같은 시각·같은 flip ② 원점(origin) = 피벗/프레임 = (0.5, 0.91667) — 보스와 같음 "
                         "③ 표시 배율 = 보스 스프라이트 배율 × 2(이 시트 도트가 보스 도트의 2배 크기 — pixelScale 을 읽는 로더면 자동) ④ depth above_target, "
                         "drawOver lightmap, 3국면 소등 동안만. _rim 과 _rim_lite 는 둘 중 하나만 로드"),
            "drawOver": "lightmap", "paletteSwap": "none", "depth": "above_target",
            "emissiveColors": ["#e2a33c", "#d67a11", "#eecc78"],
            "design": "보스 실루엣 2×2 다수결 축소 → 안쪽 가장자리 1 도트(= 원 판 2 도트): 위·오른쪽 A23(모서리 A25), 아래·왼쪽 A21 성긴 점선(3칸에 1)",
            "memoryNote": "프레임 넓이 1/4 — 아틀라스 페이지 약 1/4(원 림 5시트 약 42MB → 약 10MB, RGBA 기준)",
            "source": SRC + " · rim_lite", "palette": "1층 램프 A21·A23·A25 — 새 색 없음",
        }
        res.append(("bosses", base + "_rim_lite", rows, meta, m["frameDurationsMs"], m.get("loop", False), (LW, LH)))
        print(base + "_rim_lite", len(rows), n)
    return res


# ------------------------------------------------------------------------------------------- 실행
def write(cat, name, rows, meta, ms, loop, size=(FW, FH), allow_edge=False):
    flat = [f for r in rows for f in r]
    meta = dict(meta)
    meta["colors"] = k61.check_frames(flat, name, allow_edge=allow_edge)
    b2.write_sheet(cat, name, flat, size[0], size[1], meta, rows=len(rows), durations=ms, loop=loop)
    return flat


def preview_strip(name, rows, size, k=2, bg=(30, 28, 34, 255), under=None, cols=None):
    fw, fh = size
    cols = cols or list(range(len(rows[0])))
    im = Image.new("RGBA", (len(cols) * fw, len(rows) * fh), bg)
    for j, r in enumerate(rows):
        for c_i, c in enumerate(cols):
            if under is not None:
                im.alpha_composite(under[j][c] if isinstance(under[j], list) else under[j], (c_i * fw, j * fh))
            im.alpha_composite(r[c], (c_i * fw, j * fh))
    while max(im.size) * k > 8000 and k > 1:
        k -= 1
    im = k61.scale(im, k)
    p = os.path.join(HERE, "out", "preview_native_%s.png" % name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.convert("RGB").save(p)
    return p


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    b2.DRY = "--dry" in sys.argv
    steps = args or ["onfire", "down", "cup", "rimlite"]
    stats = {}
    if "onfire" in steps:
        cat, name, rows, meta, ms, loop = build_onfire()
        write(cat, name, rows, meta, ms, loop)
        idle = frames_of("idle")
        preview_strip(name, rows, (FW, FH), 1, under=[[r[0]] * 16 for r in idle])
        stats[name] = dict(cat=cat, frame=[FW, FH], rows=4, cols=16)
    if "down" in steps:
        cat, name, rows, meta, ms, loop = build_onfire_down()
        write(cat, name, rows, meta, ms, loop)
        ff = frames_of("fall", 0)[0]
        preview_strip(name, rows, (FW, FH), 1, under=[ff[6]])
        stats[name] = dict(cat=cat, frame=[FW, FH], rows=1, cols=16)
    if "cup" in steps:
        cat, name, rows, meta, ms, loop = build_cup_shatter()
        write(cat, name, rows, meta, ms, loop, size=(CS, CS))
        preview_strip(name, rows, (CS, CS), 3)
        stats[name] = dict(cat=cat, frame=[CS, CS], rows=1, cols=8)
    if "rimlite" in steps:
        for cat, name, rows, meta, ms, loop, size in build_rim_lite():
            write(cat, name, rows, meta, ms, loop, size=size)
            stats[name] = dict(cat=cat, frame=list(size), rows=len(rows), cols=len(rows[0]))
    if not b2.DRY:
        for r in k61.to_atlas():
            print("atlas", r)
        p = os.path.join(HERE, "stats.json")
        old = json.load(open(p)) if os.path.exists(p) else {}
        old.update(stats)
        json.dump(old, open(p, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
