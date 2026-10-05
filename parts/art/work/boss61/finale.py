"""61라운드 보스 '만취' 마무리 연출 fx — 결정타(화면을 채우는 일격) · 쓰러짐(술병·잔 파편) · 불꽃 꺼짐.

색: 주인공 재·호박 램프(A17~A26 = 무기 fx v3 호박과 같은 hex) + 백열 X0/X1 + 재 S/B + 술병 유리(1층 램프) + 나무 WD·쇠 G. 반투명 0.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from k61 import Cv, G, A, X0, X1, S, B, WD, PL, Rand  # noqa: E402
from readable import fx_common  # noqa: E402


# =========================================================================================== 1. 결정타 일섬
FW, FH = 1280, 208
FP = (640, 104)


def _hash(x, y, s=0):
    return ((x * 73856093) ^ (y * 19349663) ^ (s * 83492791)) % 1000 / 1000.0


def _lens(cv, x0, x1, cy, wmax, layers, gaps=(), seed=0, power=0.7, curve=14.0, rough=0.18, crumble=0.0, lift=0.0):
    """가로로 살짝 휜 붓 렌즈(가운데 굵고 양 끝 뾰족). curve = 가운데가 아래로 처지는 정도(초승달 일섬),
    rough = 굵기 떨림(붓결), gaps = 끊긴 구간(끊긴 끝은 뾰족하게 좁아짐), crumble = 재로 부서져 빠지는 비율, lift = 끊긴 마디가 위로 뜨는 양."""
    for x in range(int(x0), int(x1) + 1):
        if any(a <= x <= b for a, b in gaps):
            continue
        t = (x - x0) / float(x1 - x0)
        w = wmax * (math.sin(math.pi * t) ** power)
        w *= 1.0 + rough * (math.sin(x * 0.043 + seed) * 0.55 + math.sin(x * 0.11 + seed * 2) * 0.25 + (_hash(x // 7, 1, seed) - 0.5) * 0.4)
        seg = 0
        if gaps:
            dmin = min(min(abs(x - a), abs(x - b)) for a, b in gaps)
            w *= min(1.0, dmin / 22.0) ** 0.6
            seg = sum(1 for a, b in gaps if b < x)
        yc = cy - curve * (2 * t - 1) ** 2 - lift * ((seg * 37) % 5) / 4.0
        for frac, col in layers:
            h = w * frac / 2.0
            if h < 0.5:
                continue
            for y in range(int(math.floor(yc - h)), int(math.ceil(yc + h)) + 1):
                if crumble and _hash(x, y, seed) < crumble * (0.6 + 0.8 * abs(y - yc) / max(1.0, h)):
                    continue
                cv.put(x, y, col)


def _speedlines(cv, seed, n, spread, lmin, lmax, cols, shift=0, thick=1, curve=14.0):
    """일섬을 따라 흐르는 속도선 — 머리(오른쪽) 밝고 두껍고, 꼬리 가늘게 사라짐. 일섬과 같은 휨."""
    r = Rand(seed)
    for k in range(n):
        off = (r.f() * 2 - 1) * spread
        if abs(off) < 18:
            off += 18 if off >= 0 else -18
        ln = lmin + r.f() * (lmax - lmin)
        x = 40 + r.f() * (FW - 80 - ln) + shift * (0.5 + r.f())
        x = max(4, min(FW - 5 - ln, x))
        head, tail = cols[k % len(cols)], cols[min(len(cols) - 1, k % len(cols) + 1)]
        th = thick + (1 if k % 4 == 0 else 0)
        for j in range(int(ln)):
            if j < ln * 0.25 and (j % 3 == 1):
                continue
            xx = x + j
            t = (xx - 0) / float(FW)
            yy = FP[1] + off * (1 - 0.3 * abs(2 * t - 1)) - curve * (2 * t - 1) ** 2
            col = head if j > ln * 0.7 else tail
            for tk in range(th if j > ln * 0.5 else 1):
                cv.put(xx, yy + tk, col)


def finisher_slash():
    frames = []
    ms = [30, 30, 40, 50, 60, 70, 80, 100]
    r = Rand(6101)
    gaps_seed = [(r.f(), r.f()) for _ in range(12)]
    for i in range(8):
        cv = Cv(FW, FH)
        cx, cy = FP
        if i == 0:
            _lens(cv, 30, FW - 30, cy, 10, [(1.0, A[27]), (0.7, X1), (0.35, X0)], power=0.35)
            cv.disc(cx, cy, 14, X1)
            cv.disc(cx, cy, 9, X0)
            for k in range(10):
                a = math.pi * 2 * k / 10 + 0.15
                ln = 70 if k % 2 == 0 else 44
                cv.line(cx + math.cos(a) * 12, cy + math.sin(a) * 12, cx + math.cos(a) * ln, cy + math.sin(a) * ln, X1, w=2 if k % 2 == 0 else 1)
            _speedlines(cv, 11, 10, 70, 120, 360, [A[26], A[25]])
        elif i == 1:
            _lens(cv, 12, FW - 12, cy, 44, [(1.0, A[23]), (0.8, A[25]), (0.55, A[27]), (0.3, X1), (0.1, X0)], power=0.55)
            _speedlines(cv, 12, 22, 92, 160, 520, [A[26], A[25], A[23]], shift=-20)
            cv.disc(cx, cy, 10, X1)
        elif i == 2:
            _lens(cv, 20, FW - 20, cy, 34, [(1.0, A[21]), (0.75, A[23]), (0.5, A[25]), (0.22, X1)], power=0.6)
            _speedlines(cv, 13, 22, 98, 120, 420, [A[25], A[23], A[21]], shift=-60)
        else:
            k = i - 3            # 0..4 식음 — 마디로 끊기고, 끊긴 끝이 뾰족해지며 재로 부서짐
            wmax = [24, 16, 10, 6, 3][k]
            lay = [[(1.0, A[19]), (0.7, A[21]), (0.4, A[23]), (0.15, A[25])],
                   [(1.0, A[19]), (0.6, A[21]), (0.3, A[23])],
                   [(1.0, B[3]), (0.6, A[19]), (0.3, A[21])],
                   [(1.0, S[1]), (0.5, A[19])],
                   [(1.0, S[0])]][k]
            # 렌즈가 마디로 끊김(재로 부서짐) — 끊긴 틈이 늘어남
            gaps = []
            for (a, b) in gaps_seed[: 3 + k * 2]:
                gx = 60 + a * (FW - 120)
                gaps.append((gx, gx + 10 + b * (20 + 30 * k)))
            _lens(cv, 30 + 30 * k, FW - 30 - 30 * k, cy, wmax, lay, gaps=gaps, power=0.6, seed=k + 3, crumble=[0.0, 0.12, 0.3, 0.5, 0.65][k], lift=2.0 * k)
            if k < 3:
                _speedlines(cv, 14 + k, 14 - 3 * k, 100, 60, 260 - 50 * k, [A[21], A[19], S[2]], shift=-90 - 30 * k)
            # 불티·재 조각(위로 떠오름)
            rr = Rand(70 + k)
            for e in range(40 - 6 * k):
                x = 60 + rr.f() * (FW - 120)
                y = max(4, cy + (rr.f() * 2 - 1) * 12 - (6 + rr.f() * 30) * (k + 1) * 0.5)
                col = [A[25], A[23], A[21], S[2], S[1]][min(4, (e % 3) + k // 2)]
                cv.put(x, y, col)
                if e % 4 == 0:
                    cv.put(x + 1, y, col)
        frames.append(cv.im)
    meta = fx_common(
        directions=["any"], layout="1행", frameDurationsMs=ms, loop=False, pivot={"x": FP[0], "y": FP[1]},
        anchor="hitbox_center", anchorNote="pivot = 결정타가 들어간 자리(보스 몸 중심 — 1.5배 보스 피벗 위 약 150 도트). 시트 가운데가 적중점이고 양쪽으로 640 도트씩 뻗는다",
        rotate=True, drawnFacing="right", flipY="allowed", depth="above", impactFrame=0, glowFrames=[0, 1, 2], holdFrame=1,
        spawn="finisher", spawnNote="파훼로 무너진 보스에게 결정타가 들어간 순간 1회(무기 무관 공용). 각도 = 주인공 → 보스",
        pairsWith="fx/v3/boss1_finisher_burst(같은 순간·같은 점)",
        systemHints={"hitstopMs": 180, "slowMo": {"scale": 0.3, "ms": 420}, "flash": {"color": "#fff4dc", "ms": 70, "note": "설정 flash 끔이면 생략"},
                     "shake": {"px": 10, "ms": 320}, "zoom": {"to": 1.08, "ms": 260},
                     "note": "아트 제안값 — 시스템이 정함. 화면을 '채우는' 느낌은 이 시트(가로 1280 도트 ≈ 화면 2/3) + 섬광 + 느린 시간으로"},
        light={"color": "#fff4dc", "radius": 520, "intensity": 1.0, "byFrame": [1.0, 0.9, 0.7, 0.45, 0.3, 0.15, 0.05, 0]},
        design="결정타 일섬: 백열 실선 + 가운데 별 섬광(0) → 화면을 가로지르는 두꺼운 빛 렌즈 + 속도선 다발(1) → 식으며 마디로 끊기고 재·불티로 흩어짐(3~7)",
    )
    return "fx", "boss1_finisher_slash", [frames], FW, FH, meta, ms, False


BW_, BH_ = 480, 480
BP = (240, 240)


def _ring_rough(cv, cx, cy, r, th, cols, seed, dash=None, phase=0.0):
    """굵기가 각도마다 들쭉날쭉한 충격 고리 — cols 바깥 → 안쪽 색."""
    steps = int(2 * math.pi * r * 1.5) + 16
    for i in range(steps):
        a = 2 * math.pi * i / steps
        deg = math.degrees(a)
        if dash and ((deg + phase) % (dash[0] + dash[1])) >= dash[0]:
            continue
        k = 0.55 + 0.9 * (0.5 + 0.5 * math.sin(a * 5 + seed) * 0.6 + 0.5 * math.sin(a * 11 + seed * 3) * 0.4)
        t = max(1.0, th * k)
        for q in range(int(t) + 1):
            rr = r - q
            col = cols[min(len(cols) - 1, int(q / max(1.0, t) * len(cols)))]
            cv.put(cx + math.cos(a) * rr, cy + math.sin(a) * rr, col)


def finisher_burst():
    frames = []
    ms = [30, 40, 50, 60, 70, 90, 110]
    rr = Rand(6111)
    sparks = [(rr.f() * 2 * math.pi, 0.5 + rr.f() * 0.7) for _ in range(54)]
    for i in range(7):
        cv = Cv(BW_, BH_)
        cx, cy = BP
        if i == 0:
            for k in range(16):
                a = math.pi * 2 * k / 16 + (0.08 if k % 3 == 0 else 0)
                ln = 214 if k % 2 == 0 else 130
                cv.taper(cx, cy, cx + math.cos(a) * ln, cy + math.sin(a) * ln, 12 if k % 2 == 0 else 7, 0.6, A[27])
                cv.taper(cx, cy, cx + math.cos(a) * ln * 0.75, cy + math.sin(a) * ln * 0.75, 5 if k % 2 == 0 else 3, 0.5, X1)
            _ring_rough(cv, cx, cy, 50, 8, [A[27], X1], 1)
            cv.disc(cx, cy, 38, X1)
            cv.disc(cx, cy, 27, X0)
        else:
            k = i - 1
            rad = [112, 166, 204, 224, 232, 235][k]
            th = [16, 11, 7, 4, 3, 2][k]
            cols = [[A[23], A[25], A[27], X1], [A[21], A[23], A[25]], [A[19], A[21], A[23]], [A[19], A[21]], [B[3], A[19]], [S[1]]][k]
            dash = None if k < 2 else ((40, 12) if k == 2 else (18, 16))
            _ring_rough(cv, cx, cy, rad, th, cols, 3 + k, dash=dash, phase=k * 9)
            if k == 0:
                cv.disc(cx, cy, 20, A[27]); cv.disc(cx, cy, 12, X1)
                for q in range(16):
                    a = math.pi * 2 * q / 16
                    ln = 96 if q % 2 == 0 else 64
                    cv.taper(cx + math.cos(a) * 24, cy + math.sin(a) * 24, cx + math.cos(a) * ln, cy + math.sin(a) * ln, 5 if q % 2 == 0 else 3, 0.5, A[25])
            for (a, s) in sparks:
                d = 40 + 205 * s * (k + 1) / 6.0
                if d > 228:
                    continue
                x, y = cx + math.cos(a) * d, cy + math.sin(a) * d + 6 * k * k * s * 0.3
                if not (20 < x < BW_ - 20 and 20 < y < BH_ - 20):
                    continue
                head = [A[27], A[25], A[23], A[21], A[19], S[2]][k]
                tail = [A[23], A[21], A[19], B[3], S[1], S[0]][k]
                ln = max(3, 16 - 3 * k)
                cv.spark(x, y, a, ln, head, tail)
                if k < 3:
                    cv.spark(x + math.sin(a), y - math.cos(a), a, ln // 2, head, tail)
        frames.append(cv.im)
    meta = fx_common(
        directions=["any"], layout="1행", frameDurationsMs=ms, loop=False, pivot={"x": BP[0], "y": BP[1]},
        anchor="hitbox_center", depth="above", impactFrame=0, glowFrames=[0, 1], rotate=False,
        spawn="finisher", spawnNote="boss1_finisher_slash 와 같은 순간·같은 점(보스 몸 중심)에 1회 — 일섬 위에 그린다",
        design="결정타 터짐: 백열 원반 + 16갈래 쐐기 빛살(0) → 넓어지는 들쭉날쭉한 충격 고리(호박 3겹) + 굵은 불티 사방(1~2) → 끊어진 고리·식는 불티(3~6). 화면 평면 원(바닥 압축 없음)",
    )
    return "fx", "boss1_finisher_burst", [frames], BW_, BH_, meta, ms, False


# =========================================================================================== 2. 쓰러짐 — 술병·잔 파편
DW, DH = 640, 520
DP = (320, 470)   # = 보스 피벗(1.5배 판 (144,330) 과 같은 점)           # = 보스 피벗(발 중앙)
CHEST = (320, 284)        # 보스 피벗 위 약 186 도트(배·앞치마 주머니 — 1.5배 판)
GLASS = [A[17], A[19], A[21], A[23], A[26]]


def _bottle(cv, x, y, ang, scale=1.0):
    """호박 유리 술병(길이 ~22) — 몸통 7·목 3·헝겊 마개. ang = 병 축 각."""
    ca, sa = math.cos(ang), math.sin(ang)
    L = int(22 * scale)
    for j in range(L):
        u = j - L / 2.0
        if j < 6:
            half, col = 1.5, (WD[3] if j < 3 else A[19])         # 마개·목
        elif j < 9:
            half, col = 2.5, A[19]
        else:
            half, col = 3.6, A[20]
        for v10 in range(int(-half * 10), int(half * 10) + 1, 5):
            v = v10 / 10.0
            px, py = x + ca * u - sa * v, y + sa * u + ca * v
            c = col
            if j >= 9 and v < -half + 1.4:
                c = A[23] if j % 4 else A[26]               # 빛 받는 쪽 반사
            elif j >= 9 and v > half - 1.0:
                c = A[17]
            cv.put(px, py, c)


def _cup(cv, x, y, ang):
    """작은 술통 잔(보스 잔과 같은 말투) — 널 WD + 쇠테 G."""
    ca, sa = math.cos(ang), math.sin(ang)
    for u in range(-5, 6):
        for v in range(-4, 5):
            col = WD[3] if v < 0 else WD[2]
            if u in (-3, 3):
                col = G[7] if v < 1 else G[5]
            if v == -4:
                col = A[22]
            cv.put(x + ca * u - sa * v, y + sa * u + ca * v, col)


GRAV = 1800.0


def _shards(cv, x, y, vx, vy, tt, seed, gy, glass=True, n=18):
    """깨진 자리에서 튀는 조각 — 포물선으로 떨어져 바닥(gy 근처)에 멈춰 눕는다."""
    r = Rand(seed)
    for k in range(n):
        a = r.f() * 2 * math.pi
        sp = 60 + r.f() * 160
        svx, svy = vx * 0.35 + math.cos(a) * sp, vy * 0.2 + math.sin(a) * sp * 0.8 - 80
        px = x + svx * tt
        py = y + svy * tt + 0.5 * GRAV * tt * tt
        g = gy + r.i(-10, 10)
        landed = py >= g
        if landed:
            # 착지 시각에서 x 를 멈춤
            disc = svy * svy + 2 * GRAV * (g - y)
            tl = (-svy + math.sqrt(max(0.0, disc))) / GRAV
            px, py = x + svx * tl, g
        px = max(6, min(DW - 8, px))
        py = max(6, py)
        if glass:
            col = [A[23], A[21], A[26], A[19]][k % 4]
        else:
            col = [WD[4], WD[3], G[7], WD[2]][k % 4]
        big = k % 3 == 0
        cv.put(px, py, col)
        cv.put(px + 1, py, col if big else (A[17] if glass else WD[1]))
        if big:
            cv.put(px, py - 1, col); cv.put(px + 2, py, A[17] if glass else WD[1])
            if glass and not landed and (k + seed) % 2 == 0:
                cv.put(px, py - 2, X1)
        if landed and glass and k % 5 == 0:
            cv.put(px, py - 1, A[26])


def _ground_y(seed):
    r = Rand(seed)
    return DP[1] - 2 + r.i(-16, 22)


def defeat_shatter():
    frames = []
    ms = [40, 50, 60, 70, 70, 80, 90, 100, 110, 130, 160, 240]
    r = Rand(6121)
    objs = []
    for k in range(9):
        side = -1 if k % 2 else 1
        vx = side * (90 + r.f() * 330)
        vy = -(330 + r.f() * 260)
        objs.append(dict(kind="bottle" if k % 3 else "cup", vx=vx, vy=vy, spin=(r.f() - 0.5) * 16,
                         ang=r.f() * 6.28, brk=0.22 + r.f() * 0.26, seed=900 + k, gy=_ground_y(77 + k)))
    T = [sum(ms[:i]) / 1000.0 for i in range(len(ms))]
    for i in range(len(ms)):
        cv = Cv(DW, DH)
        t = T[i]
        if i == 0:
            cv.disc(CHEST[0], CHEST[1], 26, A[26]); cv.disc(CHEST[0], CHEST[1], 17, X1); cv.disc(CHEST[0], CHEST[1], 9, X0)
            cv.star4(CHEST[0], CHEST[1], 40, diag=12)
        if i == 1:
            cv.disc(CHEST[0], CHEST[1], 12, A[25])
            cv.ring(CHEST[0], CHEST[1], 34, 4, A[23], dash=(22, 10))
        # 술 웅덩이 얼룩(파편 아래, 착지 뒤부터)
        for o in objs:
            if t > o["brk"] + 0.25:
                bx = CHEST[0] + o["vx"] * o["brk"]
                rr = 8 + 10 * min(1.0, (t - o["brk"] - 0.25) * 3)
                for q in range(-int(rr), int(rr) + 1):
                    for w in range(-4, 5):
                        if q * q / (rr * rr) + w * w / 16.0 <= 1:
                            xx = max(4, min(DW - 6, bx + q * 1.3))
                            cv.put(xx, o["gy"] + w, A[19] if (abs(w) < 2 and abs(q) < rr - 3) else A[18])
                            if w == -2 and q % 5 == 0:
                                cv.put(xx, o["gy"] + w, A[22])
        for o in objs:
            if t < o["brk"]:
                x = CHEST[0] + o["vx"] * t
                y = CHEST[1] + o["vy"] * t + 0.5 * GRAV * t * t
                if o["kind"] == "bottle":
                    _bottle(cv, x, y, o["ang"] + o["spin"] * t, 1.6)
                else:
                    _cup(cv, x, y, o["ang"] + o["spin"] * t)
            else:
                bt = o["brk"]
                bx = CHEST[0] + o["vx"] * bt
                by = CHEST[1] + o["vy"] * bt + 0.5 * GRAV * bt * bt
                bvy = o["vy"] + GRAV * bt
                tt = t - bt
                if tt < 0.06:
                    cv.disc(bx, by, 5, X1)
                    cv.star4(int(bx), int(by), 12, diag=4)
                # 술 방울
                rr = Rand(o["seed"] + 5)
                for q in range(10):
                    qa = rr.f() * 6.28
                    qvx, qvy = o["vx"] * 0.3 + math.cos(qa) * 120, bvy * 0.2 + math.sin(qa) * 100 - 60
                    qx = bx + qvx * tt
                    qy = by + qvy * tt + 0.5 * GRAV * tt * tt
                    if qy >= o["gy"]:
                        continue
                    cv.put(qx, qy, A[22] if q % 2 else A[21]); cv.put(qx, qy + 1, A[20])
                _shards(cv, bx, by, o["vx"], bvy, tt, o["seed"], o["gy"], glass=(o["kind"] == "bottle"))
        frames.append(cv.im)
    meta = fx_common(
        directions=["any"], layout="1행", frameDurationsMs=ms, loop=False, pivot={"x": DP[0], "y": DP[1]},
        anchor="boss_pivot", depth="above", glowFrames=[0], stateHold=len(ms) - 1,
        spawn="boss_death", spawnNote=("보스 death 시트 0 프레임 시작에 1회(보스와 같은 피벗). 앞치마·주머니의 술병 6·잔 3이 양옆 위로 튀어 회전하다 공중에서 깨지고 "
                                        "유리·널 조각이 바닥에 떨어져 눕고 술 얼룩이 번진다. 마지막 칸(파편·술 얼룩)은 시스템이 원하는 만큼 유지 후 끈다(반투명 금지 — 그냥 끔)"),
        flipX="allowed", pairsWith="fx/v3/boss1_flame_snuff(방의 촛불·횃불이 차례로 꺼짐)",
        design="쓰러짐: 가슴 백열 섬광(0) → 호박 유리 술병·작은 술통 잔이 양옆 위로 튀어 회전 → 공중에서 별 섬광과 함께 깨짐 → 유리·널 조각·술 방울이 떨어져 바닥에 눕고 술 얼룩",
    )
    return "fx", "boss1_defeat_shatter", [frames], DW, DH, meta, ms, False


# =========================================================================================== 3. 불꽃 꺼짐
SW, SH = 48, 104
SP = (24, 92)        # pivot = 불꽃 뿌리(심지)


def _flame(cv, x, y, h, lean):
    """물방울 불꽃: 아래 둥글고 위로 뾰족, lean 만큼 위쪽이 옆으로 휨."""
    for dy in range(-2, h):
        t = max(0.0, dy) / float(max(1, h))
        w = 4.2 * math.sin(math.pi * min(1.0, 0.22 + t * 0.95)) ** 0.8 * (1 - t) ** 0.35
        if dy < 0:
            w = 2.5 + dy * 0.6
        xx = x + lean * t * t * h * 0.3
        for dx10 in range(int(-w * 10), int(w * 10) + 1, 5):
            dx = dx10 / 10.0
            e = abs(dx) / max(0.5, w)
            col = A[27] if (e < 0.35 and 0.05 < t < 0.6) else (A[25] if e < 0.75 else A[23])
            if t > 0.8:
                col = A[23]
            cv.put(xx + dx, y - dy, col)
    cv.put(x, y + 2, A[21])


def _puff(cv, x, y, r, col, hi):
    cv.disc(x, y, r, col)
    if r >= 2:
        cv.disc(x - r * 0.35, y - r * 0.35, max(1, r * 0.45), hi)


def flame_snuff():
    frames = []
    ms = [70, 60, 60, 70, 90, 110, 130, 160]
    for i in range(8):
        cv = Cv(SW, SH)
        x, y = SP
        if i == 0:
            _flame(cv, x, y, 18, 0)
        elif i == 1:
            _flame(cv, x, y, 12, 2)
        elif i == 2:
            _flame(cv, x, y, 6, 3)
        else:
            k = i - 3
            if k < 2:
                cv.put(x, y, A[21] if k == 0 else A[19])
            # 연기 한 줄기 — 뭉게 덩이가 위로 오르며 커지고 꼬이고 성겨짐
            n = 7 + 5 * k
            for j in range(n):
                age = j / float(n)
                yy = y - 4 - j * (3.0 + k * 0.4)
                if yy < 6:
                    break
                xx = x + 4.0 * math.sin(j * 0.8 + k * 0.7) * (0.3 + age)
                r = round(1.6 + age * 3.0 + k * 0.25, 0) + 0.3
                if k >= 2 and (j * 7 + k) % 5 < k - 1 and age > 0.35:
                    continue
                shade = min(4, int(age * 3) + k // 2)
                _puff(cv, xx, yy, r, [G[7], G[6], G[5], G[4], G[3]][shade], [G[9], G[8], G[7], G[6], G[5]][shade])
        frames.append(cv.im)
    meta = fx_common(
        directions=["any"], layout="1행", frameDurationsMs=ms, loop=False, pivot={"x": SP[0], "y": SP[1]},
        anchor="flame_point", depth="above",
        anchorNote="pivot = 꺼지는 불꽃 뿌리(촛대·횃불·화로의 불 자리). 이 fx 가 시작될 때 그 광원을 끈다(또는 0~2 프레임 동안 줄인다)",
        spawn="boss_death_lights",
        spawnNote="보스가 쓰러질 때 방의 촛불·횃불을 보스에서 먼 순서로 60~90ms 간격으로 하나씩 끔(제안). 보스 불타는 오버레이는 boss1_onfire out 단계 그대로",
        lightByFrame=[0.9, 0.6, 0.3, 0.1, 0, 0, 0, 0],
        design="불꽃 꺼짐: 불꽃이 기울며 작아짐(0~2) → 심지 잔불(3·4) → 회색 연기 한 줄기가 꼬이며 올라 흩어짐(3~7)",
    )
    return "fx", "boss1_flame_snuff", [frames], SW, SH, meta, ms, False
