"""단검 찌르기 계열 fx — '재 발톱' 바늘 획 + 짧고 많은 잔상 획 + X 섬광.

대상(틀·프레임·ms·피벗·행·판정 필드 그대로, 그림만):
  dagger_combo1~3 (+ _accel2·_accel3 · _awaken) · dagger_combo3_double(+_awaken) · dagger_flurry(+ _heat2·_heat3 · _awaken)
  dagger_combo1~3_twin(+_dance·_bleed) · dagger_combo1~3_gale(+_afterimage·_assassin) · dagger_backstab · hit_dagger(+_heavy)
판정 끝 L = fromPx + lengthPx(찌르기 원점 hitOriginInFrame 에서). 판정 칸의 발톱 끝 = L × 가속 배율(1 · 1.1 · 1.2) + 10 도트 —
61 단계 2·3 창끝(L × 배율 + 12)과 같은 자리(시스템 F 의 그림 기준 판정 유지).
"""
import math

import d5
from d5 import Cv, Frame, Rand

ROW_ROT = {"down": 90.0, "up": -90.0, "left": 180.0, "right": 0.0}


class Look:
    """색 9단 — core(백열) · hot · h3 · h2 · mid · body · dim · dark · ash · ink · ink2. 판정 칸 밖에서는 h2 이하만."""

    def __init__(self, core, hot, h3, h2, mid, body, dim, dark, ash, ink, ink2):
        self.core, self.hot, self.h3, self.h2, self.mid, self.body = core, hot, h3, h2, mid, body
        self.dim, self.dark, self.ash, self.ink, self.ink2 = dim, dark, ash, ink, ink2


EMBER = Look(d5.X0, d5.X1, d5.A26, d5.A25, d5.A23, d5.A21, d5.A19, d5.A18, d5.B3, d5.B1, d5.INK2)
# 각성(귀화, 60 Q19 각성 색): 보라 몸 + 청록 불혀
ONIBI = Look(d5.X0, d5.X1, d5.TEAL[10], d5.TEAL[9], d5.VIO[9], d5.VIO[7], d5.VIO[5], d5.VIO[3], d5.TEAL[3], d5.VIO[1], d5.INK)

# 가속 단계: 길이·폭·잔상 수·속도 틱 수
STAGES = {1: dict(len=1.0, wid=1.0, ghosts=3, ticks=6),
          2: dict(len=1.10, wid=1.15, ghosts=6, ticks=10),
          3: dict(len=1.20, wid=1.3, ghosts=9, ticks=14)}


def ghosts(f, Lx, n, w, hook, lk, seed, age, spread=1.0):
    """짧고 많은 잔상 발톱: 끝 근처 뒤쪽에 옆으로 비켜 선 짧은 획 n개. age 0 = 판정 칸, 1 = 다 그음, 2 = 식음."""
    r = Rand(seed)
    for k in range(n):
        side = 1 if k % 2 == 0 else -1
        lat = side * (7 + 5.5 * (k // 2) + 2.5 * r.f()) * spread
        back = 8 + 15 * (k // 2) + 10 * r.f()
        ln = Lx * (0.16 + 0.14 * r.f())
        u1 = Lx - back + 6 * age
        u0 = u1 - ln * (1.0 - 0.25 * age)
        if u0 < 18:
            continue
        ww = w * (0.36 - 0.025 * (k // 2)) * (1.0 - 0.25 * age)
        if age == 0:
            lay = [(1.0, lk.dim), (0.55, lk.mid)] if k < 4 else [(1.0, lk.dim), (0.5, lk.body)]
        elif age == 1:
            lay = [(1.0, lk.dark), (0.45, lk.dim)]
        else:
            lay = [(1.0, lk.ash)]
        if age >= 2 and k % 3 == 2:
            continue
        f.claw(u0, u1, max(1.3, ww), lay, hook=hook * 0.5, voff=lat, peak=0.7)


def ticks(f, Lx, n, w, lk, seed, age, hot=False):
    """속도 틱(1 도트 짧은 선) — 축과 나란히, 끝 쪽에 몰림."""
    r = Rand(seed + 77)
    for k in range(n):
        v = (r.f() * 2 - 1) * (w * 2.2 + 6)
        u1 = Lx * (0.45 + 0.5 * r.f()) + 4 * age
        ln = 8 + 18 * r.f()
        col = (lk.h2 if hot and abs(v) < w else lk.mid) if age == 0 else lk.dim if age == 1 else lk.dark
        f.line(u1 - ln, v, u1, v, col)


def main_claw(f, u0, Lx, w, hook, lk, age, glow, tipk=1.0):
    """본 발톱 획. age 0 = 판정(백열 심), 1 = 다 그음(식는 중), 2 = 마디로 끊김, 3 = 재."""
    if age == 0:
        lay = [(1.0, lk.dim), (0.86, lk.body), (0.64, lk.mid), (0.42, lk.h2)]
        if glow:
            lay += [(0.25, lk.hot), (0.1, lk.core)]
        f.claw(u0, Lx + 10 * tipk, w, lay, hook=hook, peak=0.78)
    elif age == 1:
        f.claw(u0 + 6, Lx + 12 * tipk, w * 0.78, [(1.0, lk.dark), (0.7, lk.dim), (0.42, lk.body), (0.2, lk.mid)], hook=hook * 1.05, peak=0.8)
    elif age == 2:
        segs = 6
        for k in range(segs):
            a0 = u0 + 10 + (Lx - u0) * k / segs
            a1 = a0 + (Lx - u0) / segs * 0.55
            if k % 3 == 1:
                continue
            t = (a0 - u0) / max(1.0, Lx - u0)
            f.claw(a0, a1, w * 0.4, [(1.0, lk.dark), (0.5, lk.dim)], hook=0, voff=hook * t ** 2.2, peak=0.5, back=0.3)
    else:
        r = Rand(int(Lx * 3 + hook))
        for k in range(10):
            t = r.f()
            u = u0 + 10 + (Lx - u0) * t
            v = hook * t ** 2.2 + (r.f() * 2 - 1) * 4 - 3
            f.put(u, v, lk.ash if k % 3 else lk.dark)


def tip_x(f, Lx, hook, lk, age, glow, big=1.0):
    """끝의 X 섬광(판정) → 작게 남는 X 흉터(다 그음) → 희미한 점."""
    u, v = Lx + 6, hook * 0.9
    if age == 0:
        arm = int(11 * big)
        if glow:
            f.xglint(u, v, arm, core=lk.core, mid=lk.hot, edge=lk.h2, tilt=40, long=1.0)
            f.xglint(u, v, int(arm * 0.55), core=lk.core, mid=lk.core, edge=lk.hot, tilt=40)
            for du, dv in ((0, -arm * 0.7), (0, arm * 0.7), (-arm * 0.6, 0)):
                f.put(u + du, v + dv, lk.h2)
        else:
            f.xglint(u, v, arm, core=lk.h2, mid=lk.mid, edge=lk.body, tilt=40)
    elif age == 1:
        f.xglint(u + 3, v, int(7 * big), core=lk.h2, mid=lk.mid, edge=lk.dim, tilt=46)
    elif age == 2:
        f.xglint(u + 5, v, int(4 * big), core=lk.dim, mid=lk.dark, edge=lk.dark, tilt=50)


def flecks(f, Lx, lk, seed, age, n=10, spread=14):
    """먹·재 부스러기(식는 칸) — 끝 앞쪽으로 흩어짐."""
    r = Rand(seed + 5)
    for k in range(n):
        u = Lx * (0.45 + 0.5 * r.f()) + 3 * age
        v = (r.f() * 2 - 1) * spread
        c = [lk.dim, lk.dark, lk.ink2, lk.ash][(k + age) % 4]
        f.put(u, v, c)
        if k % 3 == 0:
            f.put(u + 1, v, c)


# =============================================================================
# 연격 1~3 (+가속 · 각성 · 쌍격/질풍 1단·2단)
# =============================================================================
def combo_rows(m, n, stage, lk, variant=None):
    W, H = m["frameWidth"], m["frameHeight"]
    th = m["thrust"]
    o = m.get("hitOriginInFrame") or {"x": m["pivot"]["x"], "y": m["pivot"]["y"] - 40}
    L = th["fromPx"] + th["lengthPx"]
    st = STAGES[stage]
    Lx = L * st["len"]
    if variant:                                    # 갈래 시트(52라운드 틀, 판정 96/112): 옛 그림 끝(≈ L)에 X 섬광 끝을 맞춤
        Lx = L - 14
    big = 1.0 if n < 3 else 1.25
    w = (9.0 if n < 3 else 11.0) * st["wid"]
    nfr = m["frames"]
    glow = set(m.get("glowFrames") or [1])
    hk = {1: -9.0, 2: 9.0, 3: -7.0}[n]
    rows = []
    for d in m["directions"]:
        ang = th["angleDeg"] + ROW_ROT[d]
        hook = -hk if d == "left" else hk
        row = []
        for i in range(nfr):
            cv = Cv(W, H)
            f = Frame(cv, o["x"], o["y"], ang)
            age = i - 1
            seed = 600 + n * 10 + stage
            if i == 0:                                    # 예비: 바늘이 맺힘 + 모여드는 짧은 잔상 틱
                f.claw(16, Lx * 0.55, w * 0.32, [(1.0, lk.dim), (0.5, lk.body)], hook=hook * 0.3)
                r = Rand(seed)
                for k in range(3 + stage):
                    v = (r.f() * 2 - 1) * (w + 8)
                    u = Lx * (0.25 + 0.3 * r.f())
                    f.line(u, v, u + 10 + 6 * r.f(), v * 0.7, lk.dark)
            else:
                g = i in glow
                if variant in ("twin", "twin_dance", "twin_bleed"):
                    combo_twin(f, Lx, w, hook, lk, age, g, n, stage, seed, variant)
                elif variant in ("gale", "gale_afterimage", "gale_assassin"):
                    combo_gale(f, Lx, w, hook, lk, age, g, n, stage, seed, variant)
                else:
                    if age <= 2:
                        ghosts(f, Lx, st["ghosts"] + (2 if n == 3 else 0), w, hook, lk, seed, age)
                        ticks(f, Lx, st["ticks"] if age == 0 else st["ticks"] // 2, w, lk, seed + i, age, hot=g)
                    main_claw(f, 14, Lx, w, hook, lk, min(age, 3), g)
                    if n == 3 and age <= 1:               # 3타: 끝에서 엇갈린 둘째 발톱 → X
                        f.claw(Lx * 0.62, Lx + 6, w * 0.55, [(1.0, lk.dim), (0.6, lk.mid)] + ([(0.25, lk.hot)] if g else []),
                               hook=-hook * 1.6, voff=hook * 0.4, peak=0.7)
                    tip_x(f, Lx, hook, lk, age, g, big * (1 + 0.12 * (stage - 1)))
                    if age >= 1:
                        flecks(f, Lx, lk, seed, age, n=8 + 3 * stage)
            row.append(cv.im)
        rows.append(row)
    return rows


def combo_twin(f, Lx, w, hook, lk, age, g, n, stage, seed, variant):
    """쌍격: 두 발톱 바늘이 앞 60% 에서 X 로 교차 — 교차점 X 섬광, 식으며 X 흉터."""
    for sg in (1, -1):
        if age <= 1:
            lay = ([(1.0, lk.dim), (0.7, lk.body), (0.4, lk.mid)] + ([(0.2, lk.hot)] if g and sg == 1 else [])) if age == 0 else \
                [(1.0, lk.dark), (0.6, lk.dim), (0.3, lk.body)]
            f.claw(14, Lx + 8, w * 0.8, lay, hook=-sg * 14, voff=sg * 7, peak=0.75, hp=1.4)
        elif age == 2:
            for k in range(4):
                a0 = 24 + (Lx - 24) * k / 4.0
                t = (a0 - 14) / (Lx - 6)
                if k % 2 == 0:
                    f.claw(a0, a0 + (Lx - 24) / 7.0, w * 0.35, [(1.0, lk.dark)], voff=sg * 7 - sg * 14 * t ** 1.4, peak=0.5, back=0.3)
    cu = Lx * 0.62
    if age == 0:
        f.xglint(cu, 7 - 14 * 0.6 ** 1.4, 9, core=lk.core if g else lk.h2, mid=lk.hot if g else lk.mid, edge=lk.h2 if g else lk.body, tilt=45)
    elif age == 1:
        f.xglint(cu, 7 - 14 * 0.6 ** 1.4, 5, core=lk.h2, mid=lk.mid, edge=lk.dim, tilt=45)
    if variant == "twin_dance" and age <= 1:          # 난무: 엇갈린 둘째 X(작게) + 짧은 잔상 다발
        for sg in (1, -1):
            f.claw(Lx * 0.35, Lx * 0.9, w * 0.4, [(1.0, lk.dark), (0.5, lk.body)], hook=sg * 9, voff=-sg * 12, peak=0.7, hp=1.4)
        ghosts(f, Lx, 6, w, hook, lk, seed + 3, age, spread=1.4)
    if variant == "twin_bleed" and age >= 1:          # 출혈: X 에서 떨어지는 짙은 방울
        r = Rand(seed + 9)
        for k in range(5):
            x, y = f.P(cu + (r.f() * 2 - 1) * 12, 7 - 14 * 0.6 ** 1.4 + (r.f() * 2 - 1) * 4)
            ln = 2 + int(3 * r.f()) + 3 * age
            for j in range(ln):
                f.cv.put(x, y + j, lk.dark)
            f.cv.put(x, y + ln, lk.ink2)
            f.cv.put(x + 1, y + ln, lk.ink2)
            f.cv.put(x, y + ln + 1, lk.ink2)
    if age <= 2:
        ticks(f, Lx, 6 + 2 * stage, w, lk, seed, age, hot=g)
    if age >= 1:
        flecks(f, Lx, lk, seed, age, n=8)


def combo_gale(f, Lx, w, hook, lk, age, g, n, stage, seed, variant):
    """질풍: 가는 본 발톱 + 부채꼴로 펼친 바람 발톱(짧은 초승달 획 3~5)이 뒤로 흩날림."""
    main_claw(f, 14, Lx, w * 0.8, hook, lk, min(age, 3), g)
    nf = 5 if variant == "gale_afterimage" else 3
    if age <= 2:
        for k in range(nf):
            sg = -1 if k % 2 else 1
            off = sg * (8 + 7 * (k // 2 + (k % 2)))
            u1 = Lx * (0.75 - 0.1 * (k // 2)) + 6 * age
            ln = Lx * 0.32
            lay = [(1.0, lk.dim), (0.55, lk.body)] if age == 0 else [(1.0, lk.dark), (0.5, lk.dim)] if age == 1 else [(1.0, lk.ash)]
            f.claw(u1 - ln, u1, w * 0.55, lay, hook=-sg * 6, voff=off, peak=0.65, hp=1.6)
    if variant == "gale_afterimage" and age <= 1:
        ghosts(f, Lx, 8, w, hook, lk, seed + 4, age, spread=1.2)
    if variant == "gale_assassin":
        r = Rand(seed + 13)
        for k in range(3):
            x, y = f.P(Lx * (0.2 + 0.25 * k), (r.f() * 2 - 1) * 10)
            d5.ink_tendril(f.cv, x, y, math.atan2(f.s, f.c) + math.pi + (r.f() - 0.5), 18 + 8 * age, 3, lk.ink2 if age < 2 else lk.ash, k)
    tip_x(f, Lx, hook, lk, age, g, 0.6 if variant != "gale_assassin" else 0.75)
    if age <= 2:
        ticks(f, Lx, 6 + 2 * stage, w, lk, seed, age, hot=g)
    if age >= 1:
        flecks(f, Lx, lk, seed, age, n=8)


# =============================================================================
# 3타 쌍격 연격 변화 (dagger_combo3_double) — 엇갈린 두 찌르기 70ms 간격
# =============================================================================
def double_rows(m, lk):
    W, H = m["frameWidth"], m["frameHeight"]
    o = m.get("hitOriginInFrame")
    t1, t2 = m["thrust"]
    L1, L2 = t1["fromPx"] + t1["lengthPx"] - 14, t2["fromPx"] + t2["lengthPx"] - 14   # 57 틀(384): X 섬광 끝 ≈ 판정 끝
    glow = set(m.get("glowFrames") or [1, 3])
    rows = []
    for d in m["directions"]:
        row = []
        for i in range(m["frames"]):
            cv = Cv(W, H)
            g = i in glow
            f1 = Frame(cv, o["x"], o["y"], t1["angleDeg"] + ROW_ROT[d])
            f2 = Frame(cv, o["x"], o["y"], t2["angleDeg"] + ROW_ROT[d])
            h1, h2_ = (-4.0, 4.0) if d != "left" else (4.0, -4.0)
            a1 = i - 1
            a2 = i - 3
            if i == 0:
                f1.claw(16, L1 * 0.55, 2.0, [(1.0, lk.dim), (0.5, lk.body)], hook=h1 * 0.3)
            if a1 >= 0:
                ghosts(f1, L1, 3, 6.5, h1, lk, 701, min(a1, 2)) if a1 <= 2 else None
                main_claw(f1, 14, L1, 6.5, h1, lk, min(a1, 3), g and a1 == 0)
                tip_x(f1, L1, h1, lk, min(a1, 3), g and a1 == 0)
            if i == 2:
                f2.claw(16, L2 * 0.5, 2.0, [(1.0, lk.dim), (0.5, lk.body)], hook=h2_ * 0.3)
            if a2 >= 0:
                ghosts(f2, L2, 5, 7.5, h2_, lk, 703, min(a2, 2)) if a2 <= 2 else None
                main_claw(f2, 14, L2, 7.5, h2_, lk, min(a2, 3), g and a2 == 0)
                tip_x(f2, L2, h2_, lk, min(a2, 3), g and a2 == 0, 1.25)
                if a2 >= 1:
                    flecks(f2, L2, lk, 705, a2, n=10)
            row.append(cv.im)
        rows.append(row)
    return rows


# =============================================================================
# 고속 난타 (dagger_flurry + 열 단계 · 각성)
# =============================================================================
def flurry_rows(m, lk, heat=1):
    W, H = m["frameWidth"], m["frameHeight"]
    o = m["hitOriginInFrame"]
    th = m["thrust"]
    L = th["fromPx"] + th["lengthPx"]
    stab = {int(k): v for k, v in m["stabAngles"].items()}          # 2: −10, 4: 12, 6: 0
    glow = set(m.get("glowFrames") or [2, 4, 6])
    hooks = {2: -4.0, 4: 4.0, 6: -3.0}
    lens = {2: 0.92, 4: 0.97, 6: 1.0}
    ng = {1: 2, 2: 4, 3: 6}[heat]
    rows = []
    for d in m["directions"]:
        row = []
        for i in range(m["frames"]):
            cv = Cv(W, H)
            evs = []
            for s in (2, 4, 6):
                if i >= s:
                    evs.append((s, i - s))
                if 2 <= i <= 7 and s + 6 > i and i - (s - 6) <= 3 and s - 6 < 2:    # 루프 이음: 앞 바퀴의 찌르기가 마르는 중
                    evs.append((s, i - (s - 6)))
            for s, age in sorted(evs, key=lambda e: -e[1]):
                if age > 3:
                    continue
                f = Frame(cv, o["x"], o["y"], stab[s] + ROW_ROT[d])
                hk = -hooks[s] if d == "left" else hooks[s]
                Lx = L * lens[s] - 10 + {1: 0, 2: 9, 3: 12}[heat]      # 옛 획 끝(L+4 · +15 · +17)과 같은 자리
                g = (i in glow) and age == 0
                if age <= 1:
                    ghosts(f, Lx, ng, 5.0, hk, lk, 800 + s, age)
                main_claw(f, 18, Lx, 5.0 + 0.6 * (heat - 1), hk, lk, age, g)
                tip_x(f, Lx, hk, lk, age, g, 0.7 + 0.08 * heat)
                if age == 0:
                    ticks(f, Lx, 4 + 3 * heat, 5.0, lk, 820 + s, 0, hot=g)
            if i in (0, 1):                                              # 시작: 손 앞에 바늘이 맺힘
                f = Frame(cv, o["x"], o["y"], ROW_ROT[d])
                f.claw(16, L * (0.3 + 0.2 * i), 2.0 + i, [(1.0, lk.dim), (0.5, lk.body)], hook=-2.0)
            if heat >= 2 and 2 <= i <= 7:                                # 열 2·3: 손 둘레 재 아지랑이 점
                r = Rand(900 + i)
                f = Frame(cv, o["x"], o["y"], ROW_ROT[d])
                for k in range(4 * heat):
                    f.put(10 + 30 * r.f(), (r.f() * 2 - 1) * 18, lk.dim if k % 2 else lk.ash)
            row.append(cv.im)
        rows.append(row)
    return rows


# =============================================================================
# 등 뒤 치명 찌르기 (dagger_backstab) — 내리꽂는 발톱 + 큰 X + 잉크 튐 고리
# =============================================================================
def backstab_rows(m, lk):
    W, H = m["frameWidth"], m["frameHeight"]
    px, py = m["pivot"]["x"], m["pivot"]["y"]
    o = m["hitOriginInFrame"]
    glow = set(m.get("glowFrames") or [1])
    rows = []
    for d in m["directions"]:
        ca = m["critAnchors"][d]
        cx, cy = px + ca["x"] - 48, py + ca["y"] - 138
        ang = math.degrees(math.atan2(cy - o["y"], cx - o["x"]))
        dist = math.hypot(cx - o["x"], cy - o["y"])
        row = []
        for i in range(m["frames"]):
            cv = Cv(W, H)
            f = Frame(cv, o["x"], o["y"], ang)
            g = i in glow
            hk = 5.0 if d != "left" else -5.0
            if i == 0:
                f.claw(4, dist * 0.8, 3.0, [(1.0, lk.dim), (0.5, lk.body), (0.25, lk.mid)], hook=hk * 0.5)
            elif i <= 3:
                age = i - 1
                main_claw(f, 2, dist - 4, 7.0, hk, lk, min(age, 3), g, tipk=0.6)
                fx = Frame(cv, cx, cy, ang)
                if age == 0:
                    if g:
                        fx.xglint(0, 0, 26, core=lk.core, mid=lk.hot, edge=lk.h2, tilt=40)
                        fx.xglint(0, 0, 13, core=lk.core, mid=lk.core, edge=lk.hot, tilt=40)
                        for sg in (1, -1):                               # 박힌 방향으로 긴 바늘 섬광
                            fx.line(0, 0, sg * 30, 0, lk.h2)
                            fx.line(0, 0, sg * 16, 0, lk.hot)
                    else:
                        fx.xglint(0, 0, 16, core=lk.h2, mid=lk.mid, edge=lk.body, tilt=40)
                    for k in range(10):                                  # 잉크 튐 바늘(바깥으로)
                        a = 2 * math.pi * k / 10 + 0.3
                        r0, r1 = 7, 15 + 5 * (k % 3)
                        cv.line(cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.8, cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 0.8,
                                lk.ink2 if k % 2 else lk.dim)
                elif age == 1:
                    fx.xglint(0, 0, 18, core=lk.h2, mid=lk.mid, edge=lk.dim, tilt=46)
                    for k in range(12):
                        a = 2 * math.pi * k / 12
                        d5.ink_blot(cv, cx + math.cos(a) * 19, cy + math.sin(a) * 15, 1.6 + (k % 3) * 0.6, k, core=lk.dim, rim=lk.ink2)
                else:
                    fx.xglint(0, 0, 10, core=lk.dim, mid=lk.dark, edge=lk.dark, tilt=50)
                    for k in range(12):
                        if k % 3 == 0:
                            continue
                        a = 2 * math.pi * k / 12 + 0.2
                        d5.ink_blot(cv, cx + math.cos(a) * 24, cy + math.sin(a) * 19 + 2, 1.2, k, core=lk.ink2, rim=lk.ash, holes=0.3)
                    flecks(f, dist - 10, lk, 931, 2, n=10, spread=12)
            else:
                r = Rand(940 + i)
                for k in range(16 - 5 * (i - 4)):
                    a = r.f() * 2 * math.pi
                    rr = 10 + 18 * r.f() + 4 * (i - 4)
                    cv.put(cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.8 + 3 * (i - 3), [lk.ash, lk.dark, lk.ink2][k % 3])
            row.append(cv.im)
        rows.append(row)
    return rows


# =============================================================================
# 적중 (hit_dagger · _heavy) — X 베인 자국 + 앞으로 튀는 바늘 불티
# =============================================================================
def hit_rows(m, lk, heavy):
    W, H = m["frameWidth"], m["frameHeight"]
    px, py = m["pivot"]["x"], m["pivot"]["y"]
    glow = set(m.get("glowFrames") or [0, 1])
    K = 1.35 if heavy else 1.0
    reach = (W - px - 8)
    r = Rand(661 if heavy else 651)
    sp = [((r.f() * 2 - 1) * (0.7 if heavy else 0.55), 0.35 + r.f() * 0.65) for _ in range(16 if heavy else 10)]
    row = []
    for i in range(m["frames"]):
        cv = Cv(W, H)
        f = Frame(cv, px, py, 0)
        g = i in glow
        if i == 0:
            f.xglint(0, 0, int(11 * K), core=lk.core, mid=lk.hot, edge=lk.h2, tilt=40, long=1.0)
            f.claw(-4, reach * 0.7, 3.0 * K, [(1.0, lk.h2), (0.5, lk.hot)], hook=-2, peak=0.3)
            if heavy:
                f.xglint(6, 0, 7, core=lk.hot, mid=lk.h3, edge=lk.mid, tilt=20)
        elif i == 1:
            f.xglint(2, 0, int(8 * K), core=lk.hot if g else lk.h2, mid=lk.h3 if g else lk.mid, edge=lk.mid, tilt=46)
            for sg in ((1, -1) if heavy else (1,)):                     # 베인 발톱 자국
                f.claw(-10, 12, 3.0, [(1.0, lk.dim), (0.5, lk.mid)], hook=sg * 5, voff=sg * 4 - 2, peak=0.6)
        elif i == 2:
            f.xglint(4, 0, int(5 * K), core=lk.mid, mid=lk.body, edge=lk.dim, tilt=50)
            for sg in ((1, -1) if heavy else (1,)):
                f.claw(-9, 12, 2.4, [(1.0, lk.dark), (0.5, lk.dim)], hook=sg * 5, voff=sg * 4 - 2, peak=0.6)
        else:
            for sg in ((1, -1) if heavy else (1,)):
                f.claw(-8, 11, 1.6, [(1.0, lk.dark)], hook=sg * 5, voff=sg * 4 - 2, peak=0.6)
        t = (i + 1) / float(m["frames"])
        for k, (a, s) in enumerate(sp):                                 # 바늘 불티
            if i == 0 and s > 0.6:
                continue
            dd = reach * s * min(1.0, t * 1.5)
            if dd < 6:
                continue
            x, y = px + math.cos(a) * dd, py + math.sin(a) * dd
            ln = max(2, int((9 if k % 2 else 5) * K * (1.3 - 0.25 * i)))
            head, tail = ((lk.hot, lk.h2) if (i == 0 and g) else (lk.h2, lk.mid) if i <= 1 else (lk.mid, lk.body) if i == 2 else (lk.body, lk.dim))
            if i >= 3 and k % 2:
                cv.put(x, y, lk.dim)
                continue
            for j in range(ln):
                cv.put(x - math.cos(a) * j, y - math.sin(a) * j, head if j < max(1, ln // 3) else tail)
        if heavy and i >= 1:
            for k in range(5):
                a = -0.9 + 0.45 * k
                dd = 8 + 6 * i
                d5.ink_blot(cv, px + math.cos(a + math.pi) * dd * 0.6, py + math.sin(a) * dd * 0.5 + 2 * i, 1.0 + 0.3 * (k % 2), k,
                            core=lk.ink2, rim=lk.dark if i < 3 else lk.ash)
        row.append(cv.im)
    return [row]
