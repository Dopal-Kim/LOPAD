"""단검 개성 fx 16 장 + 공명 2 — '재 발톱' 언어(발톱 바늘 획·X 섬광·새긴 발톱 자국·먹 번짐).
각 함수 = 요청 표 한 줄(이름·크기·프레임·루프·앵커·광원 그대로)."""
import math

import tk
from tk import (Cv, Frame, Rand, h2, ink_blot, ink_tendril, sheet, tline, taper, ell, star4, sparks, shard, chain, hook,
                flame, X0, X1, A17, A18, A19, A21, A23, A25, A26, B0, B1, B2, B3, S0, S1, S2, S3, INK, INK2,
                N0, N1, N2, N3, N4, N5, R0, R1, R2, R3, R4)

W = "dagger"
EMB = [(1.0, A19), (0.62, A21), (0.32, A23)]           # 발톱 획 기본 층(바깥→심)
EMB_HOT = [(1.0, A21), (0.62, A23), (0.36, A25), (0.16, X1)]
DRAG = (R0, R2, R3, R4)                                  # 사슬 끌림(적갈) 마디 램프(테·몸·밝음·반짝)
DRAG_DIM = (R0, R1, R2, R3)
BIND = (N1, N2, N4, N5)                                  # 묶음(청회) 마디 램프
CUT_ANG = 62.0


def cut(cv, cx, cy, ln, w, core, border=INK2, ang=CUT_ANG, hk=2.5):
    """새긴 발톱 자국(낙인 시트와 같은 모양): 먹 테두리 + 불씨 심."""
    f = Frame(cv, cx, cy, ang)
    f.claw(-ln / 2, ln / 2, w + 1.6, [(1.0, border)], hook=hk, peak=0.55, back=0.2)
    f.claw(-ln / 2 + 1, ln / 2 - 1, w, [(1.0, core)], hook=hk, peak=0.55, back=0.2)


def ash_bits(cv, cx, cy, n, r0, r1, seed, ky=1.0, fall=0.0):
    sparks(cv, cx, cy, n, r0, r1, seed, [B2, B3, S1, A18], ky=ky, ln=2, fall=fall)


def meta_common(trait, part=None, **kw):
    d = {"weapon": W, "trait": trait}
    if part:
        d["part"] = part
    d.update(kw)
    return d


# =============================================================================
# 1. 뽑아 던지기 — 상처(발톱 자국)에서 발톱 날이 뽑혀 나가는 섬광
# =============================================================================
def pull_throw():
    fr = tk.frame_sheet(64, 64, 4)
    cx, cy = 30, 34
    for i, cv in enumerate(fr):
        f = Frame(cv, cx, cy, -38)                       # 오른쪽 위로 빠져나감
        # 남는 상처: 먹 테 + 불씨 (식어 감)
        core = [X1, A23, A21, A19][i]
        if i < 3:
            cut(cv, cx - 3, cy + 3, 15 - i, 1.6, core)
        else:
            cut(cv, cx - 3, cy + 3, 12, 1.0, A18, border=B1)
        if i == 0:                                       # 뽑히는 순간: 날 끝이 상처에서 튀어나옴 + X
            f.claw(-4, 20, 6, EMB_HOT, hook=-4, peak=0.7)
            f.xglint(2, 0, 7, core=X0, mid=X1, edge=A25)
            sparks(cv, cx, cy, 8, 6, 14, 11, [A23, A25, A21], ln=3)
        elif i == 1:                                     # 날이 빠져나간 길: 긴 발톱 바늘 + 꼬리 잔상
            f.claw(4, 30, 4.4, EMB + [(0.14, A25)], hook=-5, peak=0.78)
            f.claw(-2, 14, 2.2, [(1.0, A19)], hook=-2, voff=4, peak=0.8)
            f.claw(-2, 12, 2.0, [(1.0, A18)], hook=-2, voff=-4, peak=0.8)
            for k in range(5):                           # 먹 방울(뽑힐 때 튐)
                cv.disc(cx - 6 - k * 2.4, cy + 8 + k * 2.2 + (k % 2), 1.0 if k % 2 else 0.6, INK2)
        elif i == 2:                                     # 끝만 남고 마디로 끊김
            for k, (u0, u1) in enumerate(((14, 22), (25, 33))):
                f.claw(u0, u1, 2.6 - k * 0.6, [(1.0, A19), (0.5, A21)], hook=-1.5, peak=0.6)
            ash_bits(cv, cx + 4, cy - 2, 6, 6, 16, 23)
            for k in range(4):
                cv.disc(cx - 8 - k * 2.6, cy + 12 + k * 2.6, 0.8, INK2)
        else:
            ash_bits(cv, cx + 10, cy - 8, 6, 2, 12, 31, fall=3)
    return sheet("trait_dagger_d_pullThrow", fr, [30, 40, 50, 70], "hitbox_center", (32, 32),
                 "상처(새긴 발톱 자국)에서 발톱 날이 오른쪽 위로 뽑혀 나가는 섬광 — 뽑히는 칸 X 섬광, 지나간 길은 휜 바늘 획, 먹 방울이 반대쪽으로 튐. "
                 "투척 단검 그림은 dagger_thrown 그대로(이 시트는 출발 자리 표시)",
                 ["뽑힘(X 섬광)", "빠져나간 길", "끊김", "재"], glow=[0], **meta_common("d_pullThrow", spawn="trait_proc"))


# =============================================================================
# 2. 낙인 사슬 — 두 적 사이 적갈 사슬(양끝 발톱 갈고리) · 끌려와 부딪는 충돌
# =============================================================================
def brand_chain():
    fr = tk.frame_sheet(192, 48, 5)
    y = 24
    for i, cv in enumerate(fr):
        if i == 0:                                       # 양 낙인에서 사슬이 뻗어 나옴(가운데 비어 있음)
            chain(cv, 14, y, 74, y, DRAG)
            chain(cv, 118, y, 178, y, DRAG, phase=1)
            hook(cv, 74, y, 0, 13, DRAG, glow=True)
            hook(cv, 118, y, 180, 13, DRAG, glow=True)
            for x in (10, 182):
                cut(cv, x, y, 14, 1.6, X1, ang=62)
        elif i in (1, 2):                                # 걸림·팽팽: 마디에 빛이 흐름
            gl = set(range(i, 40, 3))
            chain(cv, 18, y, 174, y, DRAG, glint=gl, phase=i)
            for x, a in ((18, 180), (174, 0)):
                hook(cv, x, y, a, 13, DRAG, glow=(i == 1))
            if i == 1:
                star4(cv, 96, y - 1, 8, core=X0, mid=X1, edge=R4)
            else:                                        # 당김: 가운데 쪽으로 튀는 불티
                sparks(cv, 96, y, 12, 6, 70, 21, [R3, R4, A23], ky=0.15, ln=3)
        elif i == 3:                                     # 늘어짐(가운데로 감김)·마디 몇 개 빠짐
            chain(cv, 30, y, 162, y, DRAG_DIM, sag=5, broken={3, 9})
            hook(cv, 30, y, 180, 11, DRAG_DIM)
            hook(cv, 162, y, 0, 11, DRAG_DIM)
        else:                                            # 마디 띄엄띄엄 → 재
            chain(cv, 52, y, 140, y, (R0, R1, R1, R2), sag=6, broken={1, 2, 5, 6, 9})
            ash_bits(cv, 96, y + 2, 10, 10, 50, 7, ky=0.3)
    sheet("trait_dagger_d_brandChain", fr, [40, 50, 60, 70, 90], "contact", (96, 24),
          "두 낙인 적 사이에 걸리는 적갈 낙인 사슬 — 양 끝은 재 발톱 갈고리(물어뜯는 곡선), 걸리는 칸에 가운데 별 섬광·마디 빛, 다음 칸은 가운데로 끌어당기는 꺾쇠, "
          "늘어지며 마디가 빠져 재로. 오른쪽 = 끌려오는 적 쪽",
          ["뻗음(양쪽 갈고리)", "걸림(별 섬광)", "당김", "늘어짐", "끊겨 재"], glow=[0, 1],
          rotate=True, drawnFacing="right", flipY="allowed",
          anchorNote="contact = 두 적 사이 가운데(사슬 중심, 요청 표 '가운데'), 진행 각 = 낙인 적 → 끌려오는 적. 길이 192 도트(3칸) — 다른 거리는 x 로 늘리거나(scaleX 권장 0.6~1.6) 사슬 타일 trait_common_chain 행 drag 를 깔고 이 시트는 양끝만",
          tileFallback="trait_common_chain#drag",
          light={"color": "#b04848", "radius": 32, "intensity": 0.6, "ms": 260},
          **meta_common("d_brandChain", spawn="trait_proc"))

    fr = tk.frame_sheet(128, 128, 6)
    cx, cy = 64, 64
    for i, cv in enumerate(fr):
        t = i / 5.0
        if i == 0:                                       # 맞부딪힘: 두 발톱 초승달이 마주 닿음 + 큰 X
            for s in (-1, 1):
                f = Frame(cv, cx + s * 6, cy, 90)
                f.claw(-26, 26, 7, [(1.0, R2), (0.6, R3), (0.3, R4)], hook=-10 * s, peak=0.5, back=0.25)
            Frame(cv, cx, cy, 0).xglint(0, 0, 13, core=X0, mid=X1, edge=A25, long=1.0)
            sparks(cv, cx, cy, 14, 10, 30, 41, [A23, A25, R4], ln=3)
        else:
            r = 14 + 32 * t ** 0.7
            for s in (-1, 1):                            # 양쪽으로 벌어지는 반달(괄호) 두 겹
                f = Frame(cv, cx + s * r * 0.55, cy, 90)
                w = max(1.2, 7 - i * 1.2)
                lay = [(1.0, R1), (0.6, R2)] if i >= 3 else [(1.0, R2), (0.6, R3), (0.3, R4)]
                f.claw(-r * 0.8, r * 0.8, w, lay, hook=-r * 0.35 * s, peak=0.5, back=0.25)
            if i <= 3:                                   # 튀는 사슬 마디(작은 고리)
                R = Rand(70 + i)
                for k in range(6):
                    a = R.f() * 2 * math.pi
                    d = 18 + 30 * t + R.f() * 6
                    x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.8
                    ell(cv, x, y, 2.6, 1.6, R2 if i > 1 else R3)
                    cv.put(x, y - 1, R4 if i == 1 else R2)
                Frame(cv, cx, cy, 0).xglint(0, 0, 8 - i * 2, core=A25, mid=A23, edge=R3)
            ash_bits(cv, cx, cy, 6 + i * 3, 8 + r * 0.4, r + 6, 50 + i, fall=i * 1.5)
    sheet("trait_dagger_d_brandChain_impact", fr, [40, 50, 60, 70, 90, 120], "contact", (64, 64),
          "끌려온 적과 낙인 적이 부딪는 충돌 — 마주 닿는 두 발톱 반달 + 큰 X 섬광(재 발톱 표지) → 반달이 괄호처럼 양쪽으로 벌어지며 적갈 사슬 마디가 튐 → 재",
          ["맞부딪힘(X)", "벌어짐", "벌어짐", "마디 튐", "식음", "재"], glow=[0],
          rotate=True, drawnFacing="right", anchorNote="pivot = 두 적이 닿은 자리. 진행 각 = 끌려온 방향(대칭이라 돌려도 같은 인상)",
          **meta_common("d_brandChain", "impact", spawn="trait_proc"))


# =============================================================================
# 3. 그림자 매듭 — 매듭이 조여지는 섬광 · 적 발밑 그림자 매듭 고리(수명)
# =============================================================================
def knot_path(cx, cy, r, t, ky=1.0, n=3):
    """세 잎 매듭(트레포일) 곡선 점 t∈[0,1)."""
    a = 2 * math.pi * t
    rr = r * (0.62 + 0.38 * math.cos(n * a))
    return cx + rr * math.cos(a), cy + rr * math.sin(a) * ky, math.sin(n * a)


def shadow_knot():
    fr = tk.frame_sheet(96, 96, 5)
    cx, cy = 48, 48
    for i, cv in enumerate(fr):
        r = [30, 24, 18, 18, 17][i]
        rot = i * 0.06
        width = [3.2, 3.0, 2.6, 2.2, 1.6][i]
        # 매듭 줄: 먹 바탕 + 청회 테(묶음)
        pts = [knot_path(cx, cy, r, (k / 240.0 + rot) % 1.0) for k in range(240)]
        for k, (x, y, z) in enumerate(pts):
            if i == 4 and h2(k, 9) < 0.45:
                continue
            cv.disc(x, y, width / 2 + 0.6, INK if z < 0 else INK2)
        for k, (x, y, z) in enumerate(pts):
            if i == 4 and h2(k, 9) < 0.45:
                continue
            if z > -0.2:                                  # 위로 지나는 가닥만 밝은 테
                col = [N4, N5, N4, N3, N2][i]
                cv.put(x, y - width / 2, col)
        if i <= 2:                                       # 조여드는 가닥 끝(발톱 끝)
            for k in range(3):
                a = math.radians(90 + k * 120 + i * 18)
                f = Frame(cv, cx + math.cos(a) * (r + 4), cy + math.sin(a) * (r + 4), math.degrees(a) + 180)
                f.claw(0, 10 - i * 2, 3.0, [(1.0, INK2), (0.5, N3)], hook=3, peak=0.6)
        if i == 2:                                       # 조여진 순간: 가운데 X 섬광
            Frame(cv, cx, cy, 0).xglint(0, 0, 9, core=X0, mid=X1, edge=N4)
        if i == 3:
            Frame(cv, cx, cy, 0).xglint(0, 0, 5, core=N5, mid=N4, edge=N3)
        if i >= 3:
            ash_bits(cv, cx, cy, 8, 16, 30, 60 + i, fall=2)
    sheet("trait_dagger_d_shadowKnot", fr, [40, 50, 60, 70, 90], "hitbox_center", (48, 48),
          "먹 그림자 가닥이 세 잎 매듭으로 몸을 감아 조여짐 — 넓게 감김 → 조임(가닥 끝은 발톱 곡선) → 조여진 칸 가운데 X 섬광, 위로 지나는 가닥에 청회(묶음) 테 → 매듭이 굳고 먹이 부스러짐",
          ["감김", "조임", "조여짐(X)", "굳음", "부스러짐"], glow=[2], **meta_common("d_shadowKnot", spawn="trait_proc"))

    fr = tk.frame_sheet(128, 64, 4)
    cx, cy = 64, 34
    rx, ry = 46, 17
    for i, cv in enumerate(fr):
        ink_blot(cv, cx, cy, 30, 5, core=INK, rim=S0, ky=0.4, ragged=0.18)
        # 웅덩이 둘레를 감는 꼰 그림자 끈 두 가닥(서로 꼬임) — 위상이 돌며 조임
        ph = i * (math.pi / 2)
        pulse = 1.0 - 0.04 * (i % 2)
        segs = []
        for k in range(720):
            a = 2 * math.pi * k / 720
            for st in (0, 1):
                tw = math.sin(a * 9 + ph + st * math.pi)
                r = 1.0 + 0.07 * tw
                x = cx + math.cos(a) * rx * r * pulse
                y = cy + math.sin(a) * ry * r * pulse
                segs.append((math.cos(a * 9 + ph + st * math.pi), x, y, st, math.sin(a)))
        segs.sort(key=lambda t: t[0])                    # 뒤 가닥부터
        for z, x, y, st, sa in segs:
            cv.disc(x, y, 1.0, INK2 if z < 0 else N1)
        for z, x, y, st, sa in segs:
            if z > 0.55:
                cv.put(x, y - 1, N4 if z > 0.9 else N3)
        # 앞쪽 매듭 하나(주인공 쪽): 고리 두 개 + 늘어진 끝
        kx, ky_ = cx + 4, cy + ry - 1
        for s_ in (-1, 1):
            ell(cv, kx + s_ * 6, ky_, 6, 3.4, N1, w=2)
            ell(cv, kx + s_ * 6, ky_, 6, 3.4, N4 if (i + (s_ > 0)) % 2 == 0 else N3, a0=190, a1=350)
        cv.disc(kx, ky_, 2.0, N2)
        cv.put(kx, ky_ - 1, N5)
        for s_ in (-1, 1):
            tline(cv, kx + s_, ky_ + 2, kx + s_ * 5, ky_ + 8 + (i % 2), N1)
    sheet("trait_dagger_d_shadowKnot_bind", fr, [80, 80, 80, 80], "floor", (64, 34),
          "적 발밑 먹 그림자 웅덩이 + 둘레를 감는 꼰 그림자 끈(두 가닥이 서로 꼬임, 위로 오는 가닥에 청회 빛) + 앞쪽 나비 매듭 — 루프 내내 꼬임이 돌며 조였다 풂",
          ["루프", "루프", "루프", "루프"], loop=True, loopRange=[0, 3], depth="floor",
          lifeRule="묶여 있는 동안 0~3 루프(시스템 durationMs 로 끝냄 — 끝낼 때 알파 페이드 권장 120ms)",
          **meta_common("d_shadowKnot", "bind", spawn="trait_bind"))


# =============================================================================
# 4. 되짚어 걷기 — 사라짐(out) · 처음 자리에 나타남(in)
# =============================================================================
def sil_strips(cv, prog, direction, seed):
    """주인공 먹 실루엣을 6도트 가로 띠로 썰어 direction(−1 왼쪽) 쪽으로 밀어냄. prog 0 = 온전, 1 = 다 흩어짐.
    띠마다 출발이 달라 '되감기' 인상, 띠 뒤로 먹 끌림 줄, 띠 윗줄은 재 테(어두운 바닥에서 읽히게)."""
    m, orig = tk.hero_silhouette()
    mp = m.load()
    op = orig.load()
    for y in range(144):
        band = y // 6
        lag = h2(band, seed)
        p = max(0.0, min(1.0, prog * 1.7 - lag * 0.7))
        if p >= 1.0:
            continue
        dx = direction * (p ** 1.2) * 52
        xs = [x for x in range(96) if mp[x, y]]
        if not xs:
            continue
        for x in xs:
            if p > 0.45 and h2(x, y, seed) < (p - 0.45) * 2.0:
                continue
            c = op[x, y]
            col = INK if c[:3] == (0x14, 0x15, 0x16) else INK2
            if c[0] > 120:
                col = A21 if p < 0.4 else A19
            elif c[:3] == (0x45, 0x40, 0x3b):
                col = S0
            cv.put(x + dx, y, col)
        if p > 0.04:
            # 띠 윗줄 재 테 + 뒤로 끌리는 먹 줄(지나온 쪽)
            x0, x1 = xs[0] + dx, xs[-1] + dx
            for x in range(int(x0), int(x1) + 1):
                if y % 6 == 0:
                    cv.put(x, y, S0)
            ln = abs(dx) * 0.8
            if y % 3 == 0:
                tail = x1 if direction < 0 else x0
                for k in range(int(ln)):
                    if h2(k, y, seed + 3) < 0.25 + k / max(1, ln):
                        continue
                    cv.put(tail - direction * k, y, INK2 if k < ln * 0.5 else B1)


def rewind_hook(cv, cx, cy, r, prog, col_lay, glow=False, cw=1):
    """되돌아가는 발톱 고리(↺): 머리 위를 감아 도는 휜 바늘 획(가운데 굵고 양끝 뾰족)."""
    a0 = -20
    span = 250 * min(1.0, prog * 1.4)
    steps = int(math.radians(span) * r * 2) + 20
    for j, (fr_, c) in enumerate(col_lay):
        for k in range(steps):
            t = k / float(steps - 1)
            a = math.radians(a0 - cw * span * t)
            w = (1 + 3.2 * math.sin(math.pi * t) ** 0.7) * fr_
            if w < 0.7:
                continue
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * 0.5
            cv.disc(x, y, max(0.0, (w - 1) / 2), c)
    a = math.radians(a0 - cw * span)
    tip = (cx + math.cos(a) * r, cy + math.sin(a) * r * 0.5)
    if glow:
        Frame(cv, tip[0], tip[1], 0).xglint(0, 0, 5, core=X0, mid=X1, edge=A25)
    return tip


def step_back():
    ms = [40, 40, 50, 60, 70, 90]
    fr = tk.frame_sheet(96, 144, 6)
    for i, cv in enumerate(fr):
        prog = [0.0, 0.12, 0.3, 0.52, 0.76, 0.95][i]
        if i < 5:
            ink_blot(cv, 48, 136, 16 - i * 2, 31 + i, core=INK, rim=S0, ky=0.3, ragged=0.3, holes=0.1 * i)
        sil_strips(cv, prog, -1, 3)
        if 1 <= i <= 4:
            rewind_hook(cv, 48, 30, 30, (i - 0.5) / 3.5, [(1.0, A19), (0.6, A21), (0.3, A23)], glow=(i == 1))
        if i == 0:
            Frame(cv, 48, 70, 0).xglint(0, 0, 7, core=X0, mid=X1, edge=A25)
        if i >= 4:
            ash_bits(cv, 30, 70, 10, 4, 40, 80 + i, fall=6)
    sheet("trait_dagger_d_stepBack_out", fr, ms, "player_pivot", (48, 138),
          "그림자 걸음 끝 자리에서 사라짐 — 먹 실루엣이 6도트 가로 띠로 썰려 뒤(왼쪽)로 밀려 나가고(띠마다 출발이 달라 '되감기'), 띠 뒤로 먹 끌림 줄·띠 윗줄 재 테, "
          "머리 위로 되돌아가는 발톱 고리(↺)가 감기며 발밑 먹 웅덩이는 줄어듦. 첫 칸 가슴 X 섬광",
          ["떠남(X)", "되감기 시작", "띠 흩어짐", "띠 흩어짐", "고리 끝·재", "재"], glow=[0, 1],
          flipX="allowed", flipNote="그림은 처음 자리가 왼쪽일 때(띠가 왼쪽으로 감). 처음 자리가 오른쪽이면 flipX",
          **meta_common("d_stepBack", "out", spawn="trait_proc"))

    fr = tk.frame_sheet(96, 144, 6)
    for i, cv in enumerate(fr):
        prog = [0.95, 0.7, 0.42, 0.18, 0.04, 0.0][i]
        ink_blot(cv, 48, 136, 6 + i * 2.4, 41 + i, core=INK, rim=S0, ky=0.3, ragged=0.3, holes=0.5 if i == 5 else 0.0)
        if i < 5:
            sil_strips(cv, prog, 1, 9)                   # 오른쪽(지나온 쪽)에서 띠가 모여 듦
        else:                                            # 다 모인 뒤: 실루엣 대신 테만 남고 사라짐(본 몸이 그 자리에 그려짐)
            m, _ = tk.hero_silhouette()
            mp = m.load()
            for y in range(1, 143):
                for x in range(1, 95):
                    if mp[x, y] and (not mp[x - 1, y] or not mp[x + 1, y]) and (x + y) % 2 == 0:
                        cv.put(x, y, N3)
        if i <= 3:
            rewind_hook(cv, 48, 30, 30, 1.0 - i / 3.5, [(1.0, A18), (0.55, A19)] if i else [(1.0, A19), (0.6, A21)])
        if i == 4:                                       # 도착 순간 가슴 X 섬광 + 발톱 바늘(되돌아오며 벤 마지막 획)
            f = Frame(cv, 6, 84, -8)
            f.claw(0, 80, 4.0, [(1.0, A21), (0.6, A23), (0.3, A25), (0.12, X1)], hook=-6, peak=0.8)
            Frame(cv, 52, 72, 0).xglint(0, 0, 8, core=X0, mid=X1, edge=A25)
    sheet("trait_dagger_d_stepBack_in", fr, [40, 40, 50, 60, 80, 100], "player_pivot", (48, 138),
          "처음 자리에 되돌아와 나타남 — 가로 띠들이 지나온 쪽(오른쪽)에서 미끄러져 모여 먹 실루엣이 되고, 머리 위 발톱 고리가 풀리듯 줄어듦, 다 모인 칸에 "
          "되돌아오며 그은 마지막 발톱 바늘 + 가슴 X 섬광 → 청회 윤곽만 남고 사라짐(본 몸이 그 자리에). 지나는 길 베기 선은 시스템 윤곽",
          ["모여 듦", "모여 듦", "모여 듦", "거의 모임", "도착(X·바늘)", "윤곽만"], glow=[4],
          flipX="allowed", flipNote="그림은 지나온 길이 오른쪽일 때. 반대면 flipX",
          **meta_common("d_stepBack", "in", spawn="trait_proc"))


# =============================================================================
# 5. 스치는 낙인 — 스쳐 지나간 몸에 그어지는 짧은 낙인 자국
# =============================================================================
def dash_brand():
    fr = tk.frame_sheet(64, 64, 4)
    cx, cy = 32, 32
    for i, cv in enumerate(fr):
        if i == 0:                                       # 가로로 스치는 바늘(왼→오) — 끝 X
            f = Frame(cv, 4, cy + 4, -8)
            f.claw(0, 54, 4.2, EMB_HOT, hook=-3, peak=0.85)
            f.xglint(52, -3, 5, core=X0, mid=X1, edge=A25)
        elif i == 1:                                     # 그 자리에 발톱 자국이 지져짐(가로 낙인) + 스친 꼬리
            cut(cv, cx, cy + 1, 22, 2.0, A25, ang=-8, hk=-2)
            f = Frame(cv, 4, cy + 4, -8)
            for k in range(3):
                f.claw(k * 9, k * 9 + 6, 1.6, [(1.0, A19)], hook=0, voff=6, peak=0.5)
            sparks(cv, cx + 10, cy, 7, 4, 14, 13, [A23, A21, A25], ln=2, a0=-60, a1=60)
        elif i == 2:
            cut(cv, cx, cy + 1, 22, 1.8, A23, ang=-8, hk=-2)
            cv.put(cx + 4, cy - 6, A21)
            cv.put(cx - 7, cy - 4, A23)
        else:
            cut(cv, cx, cy + 1, 20, 1.4, A21, ang=-8, hk=-2)
            cv.put(cx + 2, cy - 9, A19)
    sheet("trait_dagger_d_dashBrand", fr, [30, 40, 60, 80], "hitbox_center", (32, 32),
          "대쉬로 스친 몸에 가로 발톱 바늘이 지나가고(끝 X) → 그 자리에 가로로 새긴 낙인 자국(먹 테 + 불씨 심)이 지져져 남음 — 낙인 시트(dagger_brand_mark)의 비스듬한 자국과 달리 가로로 누운 '스친' 자국",
          ["스침(X)", "지져짐", "남음", "식음"], glow=[0],
          flipX="allowed", flipNote="그림은 왼→오 대쉬. 반대 대쉬면 flipX", **meta_common("d_dashBrand", spawn="trait_proc"))


# =============================================================================
# 6. 꿰찌르기 — 두 적을 꿰는 긴 관통선 (회전, 왼끝 = 주인공)
# =============================================================================
def dash_pierce():
    fr = tk.frame_sheet(192, 48, 5)
    oy = 24
    for i, cv in enumerate(fr):
        f = Frame(cv, 6, oy, 0)
        if i == 0:                                       # 바늘이 뻗음(끝 백열)
            f.claw(0, 120, 6, EMB_HOT, hook=-3, peak=0.88)
            for v in (-6, 6):
                f.claw(10, 70, 1.6, [(1.0, A19)], voff=v, peak=0.8)
        elif i == 1:                                     # 다 꿰뚫음: 끝까지 + 두 적 자리 X 섬광
            f.claw(0, 182, 6.4, EMB_HOT, hook=-3, peak=0.9)
            for u in (68, 140):
                f.xglint(u, -0.5, 9, core=X0, mid=X1, edge=A25)
            for v in (-7, 7):
                f.claw(20, 110, 1.6, [(1.0, A19)], voff=v, peak=0.8)
        elif i == 2:                                     # 꿴 자리에서 발톱 자국이 위아래로 터짐
            f.claw(30, 182, 3.6, EMB, hook=-2, peak=0.92)
            for u in (68, 140):
                for s in (-1, 1):
                    g = Frame(cv, *f.P(u, 0), -90 * s + 20 * s)
                    g.claw(2, 15, 3.0, [(1.0, A19), (0.5, A23)], hook=3 * s, peak=0.55)
                Frame(cv, *f.P(u, 0), 0).xglint(0, 0, 5, core=A25, mid=A23, edge=A21)
        elif i == 3:                                     # 마디로 끊김
            for k, (u0, u1) in enumerate(((50, 76), (88, 118), (130, 156), (164, 180))):
                f.claw(u0, u1, 2.4, [(1.0, A19), (0.5, A21)], hook=-1, peak=0.6)
            for u in (68, 140):
                cut(cv, *f.P(u, 0), 9, 1.0, A21, ang=70)
        else:
            for u0 in (96, 150):
                f.claw(u0, u0 + 14, 1.6, [(1.0, A18)], peak=0.6)
            ash_bits(cv, 120, oy, 12, 4, 60, 77, ky=0.25)
    sheet("trait_dagger_d_dashPierce", fr, [40, 40, 50, 60, 80], "player_pivot", (6, 24),
          "대쉬 찌르기 바늘이 길게 뻗어 두 적을 한 줄로 꿰는 관통선 — 꿴 두 자리(68·140 도트)에 X 섬광, 다음 칸에 위아래로 발톱 자국이 터지고 선은 마디로 끊김",
          ["뻗음", "꿰뚫음(X 둘)", "자국 터짐", "끊김", "재"], glow=[0, 1],
          rotate=True, drawnFacing="right", flipY="allowed",
          anchorNote="pivot = 왼끝(주인공 피벗 높이 보정은 시스템 — 찌르기 높이). 꿴 자리 표시 u = 68·140 도트(약 1·2칸 앞)",
          pierceMarksU=[68, 140], **meta_common("d_dashPierce", spawn="trait_proc"))


# =============================================================================
# 7. 휘감는 난타 — 둘레로 감겨 드는 바람 소용돌이 (250ms 마다 짧게)
# =============================================================================
def flurry_pull():
    fr = tk.frame_sheet(160, 160, 4)
    cx, cy = 80, 84
    ky = 0.55
    for i, cv in enumerate(fr):
        rot = -i * 22.0
        for arm in range(4):
            a0 = arm * 90.0 + rot
            pts = []
            for k in range(60):
                t = k / 59.0                             # 바깥(t=0) → 안(t=1)
                r = 74 * (1 - t) + 12 * t
                a = math.radians(a0 + 160 * t)
                pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * ky, t))
            # 가는 바람 줄(재) → 안쪽 끝이 발톱 바늘(호박)로 굵어지며 가운데를 가리킴
            for x, y, t in pts:
                if t < 0.55:
                    if h2(int(x), int(y), arm + i) < 0.75:
                        cv.put(x, y, S1 if t < 0.25 else S2)
                else:
                    w = 1 + 2.6 * math.sin(math.pi * (t - 0.55) / 0.45 * 0.9) ** 0.8
                    cv.disc(x, y, max(0, (w - 1) / 2), A19 if t < 0.85 else A21)
            for x, y, t in pts:
                if 0.7 < t < 0.95:
                    cv.put(x, y - 1, A23)
        # 바깥 큰 줄 끝에 흩날리는 재 조각이 안으로 끌려 듦
        R = Rand(90 + i)
        for k in range(14):
            a = R.f() * 2 * math.pi
            r = 50 + R.f() * 26
            x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * ky
            tline(cv, x, y, x - math.cos(a + 0.5) * 4, y - math.sin(a + 0.5) * 4 * ky, B3)
    sheet("trait_dagger_d_flurryPull", fr, [50, 50, 50, 50], "floor", (80, 84),
          "난타 둘레 바닥 높이에서 안으로 감겨 드는 4갈래 바람 소용돌이 — 바깥은 끊기는 재 바람 줄, 안쪽 끝이 호박 발톱 바늘로 굵어지며 가운데(주인공)를 가리킴, "
          "바깥 재 조각이 안으로 끌려 듦. 칸마다 22° 돌아 연달아 틀면 계속 감기는 인상",
          ["감김", "감김", "감김", "감김"], depth="floor",
          spawnNote="고속 난타 중 250ms 마다 1회(4칸 200ms) — 이어 틀면 끊김 없이 돎",
          **meta_common("d_flurryPull", spawn="trait_proc_repeat"))


# =============================================================================
# 8. 불티 난타 — 난타 끝 흩날리는 불티 폭발
# =============================================================================
def spark_flurry():
    fr = tk.frame_sheet(160, 160, 6)
    cx, cy = 80, 78                                      # 가슴 높이(피벗 위 50 도트)
    for i, cv in enumerate(fr):
        t = i / 5.0
        if i == 0:
            Frame(cv, cx, cy, 0).xglint(0, 0, 14, core=X0, mid=X1, edge=A25)
            Frame(cv, cx, cy, 45).xglint(0, 0, 9, core=X0, mid=X1, edge=A23)
            sparks(cv, cx, cy, 16, 4, 22, 5, [A25, A23], ln=3)
        else:
            r = 16 + 52 * t ** 0.6
            # 바깥으로 휘며 나는 불꽃 발톱 8 (재 발톱 곡선, 불 램프)
            for k in range(8):
                a = k * 45 + 12 + i * 6
                f = Frame(cv, cx, cy, a)
                ln = 22 - i * 2.5
                if ln > 4:
                    lay = [(1.0, A19), (0.6, A21), (0.32, A23 if i < 3 else A21)]
                    f.claw(r - ln, r, 4.2 - i * 0.5, lay, hook=4 + i, peak=0.7)
            # 불티: 퍼지며 떨어짐
            sparks(cv, cx, cy, 30 - i * 3, r * 0.4, r + 10, 15 + i, [A25, A23, A21, A19] if i < 3 else [A21, A19, A18],
                   ln=2, fall=6 * i)
            if i <= 2:                                   # 작은 불혀 몇 개가 바닥(피벗)으로 떨어져 붙음
                for k, dx in enumerate((-30, -8, 18, 36)):
                    flame(cv, cx + dx, 128 - (2 - i) * 6, 8 + 4 * i, 5, lean=(-1) ** k, cols=(A19, A21, A23))
            elif i <= 4:
                for k, dx in enumerate((-30, -8, 18, 36)):
                    flame(cv, cx + dx, 130, 12 - (i - 2) * 4, 5, lean=(-1) ** k, cols=(A19, A21))
            if i >= 3:
                ash_bits(cv, cx, cy, 12, r * 0.5, r, 40 + i, fall=8)
    sheet("trait_dagger_d_sparkFlurry", fr, [40, 50, 60, 70, 90, 120], "player_pivot", (80, 128),
          "난타 끝 가슴 높이 겹 X 섬광 → 바깥으로 휘며 나는 불꽃 발톱 8 + 불티가 퍼져 떨어지고, 발밑 둘레에 작은 불혀 넷이 붙었다 사그라짐(술 점화는 시스템) — 불 = pool_liquor_fire 호박 램프",
          ["터짐(겹 X)", "불 발톱", "퍼짐", "떨어짐", "사그라짐", "재"], glow=[0],
          light={"color": "#e2a33c", "radius": 64, "intensity": 0.8, "ms": 200},
          **meta_common("d_sparkFlurry", spawn="trait_proc"))


# =============================================================================
# 9. 쌍낙인 — 옆 적에 낙인이 옮겨 붙는 표시(겹 자국)
# =============================================================================
def twin_brand():
    fr = tk.frame_sheet(64, 64, 4)
    cx, cy = 32, 34
    for i, cv in enumerate(fr):
        if i == 0:                                       # 분신 교차 X 가 와서 박힘
            for s in (-1, 1):
                f = Frame(cv, cx, cy, 45 * s)
                f.claw(-20, 20, 3.4, [(1.0, A21), (0.55, A25), (0.25, X1)], hook=-3 * s, peak=0.6)
            star4(cv, cx, cy, 6)
        else:
            # 겹 자국: 같은 X 두 벌(본·그림자)이 어긋나 새겨짐
            off = [0, 7, 6, 6][i]
            for s in (-1, 1):
                cut(cv, cx - off + 1, cy + off, 24, 1.6, S1 if i < 3 else S0, border=INK, ang=45 * s, hk=-2 * s)
            core = [None, A25, A23, A21][i]
            for s in (-1, 1):
                cut(cv, cx + off * 0.6, cy - off * 0.6, 24, 2.0, core, ang=45 * s, hk=-2 * s)
            if i == 1:
                sparks(cv, cx, cy, 8, 8, 18, 3, [A23, A25], ln=2)
            if i == 3:
                cv.put(cx + 8, cy - 14, A19)
    sheet("trait_dagger_twinBrand", fr, [30, 50, 80, 100], "hitbox_center", (32, 32),
          "분신 교차 베기의 X 가 옆 적에 박힘 → 같은 X 두 벌(불씨 X 와 재빛 그림자 X)이 어긋나 새겨진 '쌍' 낙인이 남음. 단일 낙인(비스듬한 나란 자국)과 실루엣이 다름",
          ["박힘(X 별)", "새겨짐(쌍 X)", "남음", "식음"], glow=[0], **meta_common("twinBrand", spawn="trait_proc"))


# =============================================================================
# 10. 분신 방패 — 분신이 대신 맞고 깨지는 실루엣
# =============================================================================
def clone_shield():
    m, orig = tk.hero_silhouette()
    mp = m.load()
    op = orig.load()
    hit = (62, 64)

    def inside(x, y):
        return 0 <= int(x) < 96 and 0 <= int(y) < 144 and mp[int(x), int(y)]

    # 금: 맞은 자리에서 방사로 뻗는 꺾은선 7 — 실루엣 안에서만
    cracks = []
    R = Rand(7)
    for k in range(7):
        a = k * (2 * math.pi / 7) + R.f() * 0.4
        pts = [hit]
        x, y = hit
        for _ in range(7):
            a += (R.f() - 0.5) * 0.6
            nx, ny = x + math.cos(a) * 8, y + math.sin(a) * 10
            if not inside(nx, ny):
                break
            x, y = nx, ny
            pts.append((x, y))
        cracks.append(pts)
    # 조각 중심: 실루엣 안 격자 점(맞은 자리 둘레)
    pieces = []
    R = Rand(19)
    for gy in range(10, 140, 15):
        for gx in range(6, 94, 13):
            x, y = gx + R.f() * 6, gy + R.f() * 6
            if inside(x, y):
                pieces.append((x, y, R.f()))
    cells, cell_of = {}, {}
    for y in range(144):
        for x in range(96):
            if mp[x, y]:
                j = min(range(len(pieces)), key=lambda q: (pieces[q][0] - x) ** 2 + (pieces[q][1] - y) ** 2)
                cells.setdefault(j, []).append((x, y))
                cell_of[(x, y)] = j
    edges = {p for p, j in cell_of.items() if any(cell_of.get((p[0] + a, p[1] + b)) != j for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    fr = tk.frame_sheet(96, 144, 6)
    for i, cv in enumerate(fr):
        if i <= 1:
            for y in range(144):
                for x in range(96):
                    if mp[x, y]:
                        c = op[x, y]
                        col = INK2 if c[0] < 60 else (S0 if c[0] < 100 else A19)
                        if (x + y) % 2 == 0 and col == INK2:
                            col = N1                     # 분신 = 청회 망점 몸(본 몸과 구별)
                        cv.put(x, y, col)
            for y in range(1, 143):
                for x in range(1, 95):
                    if mp[x, y] and (not mp[x - 1, y] or not mp[x + 1, y] or not mp[x, y - 1] or not mp[x, y + 1]):
                        cv.put(x, y, N4 if i == 0 else N3)
            for pts in cracks:
                upto = 3 if i == 0 else len(pts)
                for a_, b_ in list(zip(pts, pts[1:]))[:upto]:
                    tline(cv, a_[0], a_[1], b_[0], b_[1], X1 if i == 0 else N5)
            if i == 0:
                star4(cv, hit[0], hit[1], 10, edge=N5, diag=5)
            else:
                star4(cv, hit[0], hit[1], 5, core=N5, mid=N5, edge=N4)
        else:
            # 실루엣이 조각(보로노이 칸)으로 갈라져 → 틈이 벌어지고 → 맞은 쪽 반대(왼쪽)로 흩어지며 작아지고 떨어짐
            t = (i - 2) / 3.0
            for j, pts in cells.items():
                x0, y0, rr = pieces[j]
                a0 = math.atan2(y0 - hit[1], x0 - hit[0]) + 0.3 * (rr - 0.5)
                d = math.hypot(x0 - hit[0], y0 - hit[1])
                push = (1.5 + 2 * rr) + (10 + 26 * rr) * t ** 1.1 * (1.3 - d / 140.0)
                ox = math.cos(a0) * push - 12 * t * (0.5 + rr)
                oy = math.sin(a0) * push * 0.6 + 34 * t * t
                keep = 0.92 - 0.6 * t                     # 조각이 모양 그대로 작아짐
                rot = t * 1.2 * (rr - 0.5)
                cr, sr = math.cos(rot), math.sin(rot)
                for px, py in pts:
                    dx, dy = (px - x0) * keep, (py - y0) * keep
                    qx = x0 + ox + dx * cr - dy * sr
                    qy = y0 + oy + dx * sr + dy * cr
                    if qy > 141:
                        continue
                    if (px, py) in edges:
                        up = cell_of.get((px, py - 1)) != j
                        col = (N4 if up else N3) if t < 0.6 else S0
                    else:
                        col = (N1 if (px + py) % 2 else INK2) if t < 0.7 else B1
                    cv.put(qx, qy, col)
            ash_bits(cv, 40, 80, 8 + i * 2, 10, 46, 30 + i, fall=10 * t)
    sheet("trait_dagger_d_cloneShield", fr, [40, 40, 50, 60, 70, 90], "player_pivot", (48, 138),
          "주인공 앞에 선 분신(청회 망점 실루엣 + 청회 테)이 대신 맞음 — 맞은 자리 별 섬광 + 금이 몸 안으로 퍼짐 → 다음 칸 금이 다 그어지고 → 각진 조각(청회 모서리)으로 깨져 "
          "맞은 쪽 반대로 흩어지며 떨어짐. 재로 부서지는 frenzy_clone_out 과 달리 '유리처럼 깨짐'",
          ["맞음(별·금)", "금", "깨짐", "흩어짐", "흩어짐", "재"], glow=[0],
          flipX="allowed", flipNote="그림은 오른쪽에서 맞음(조각이 왼쪽으로). 왼쪽에서 맞으면 flipX",
          **meta_common("d_cloneShield", spawn="trait_proc"))


# =============================================================================
# 11. 돌아오는 칼 — 꿰여 끌려오는 갈고리 섬광
# =============================================================================
def jhook(cv, x, y, sc, lay, glow=False):
    """낚싯바늘 발톱: (x,y)에서 왼쪽으로 뻗는 자루 → 끝이 아래로 말려 위로 되감기는 J. lay = [(폭, 색)] 바깥→심."""
    pts = []
    for k in range(40):                                  # 자루(오른쪽 → 왼쪽)
        t = k / 39.0
        pts.append((x - 26 * sc * t, y + 1.5 * sc * t * t, 1 - 0.2 * t))
    cxh, cyh, r = x - 26 * sc, y + 1.5 * sc + 7 * sc, 7 * sc
    for k in range(1, 40):                               # 말림(위 → 왼쪽 → 아래 → 오른쪽 위)
        t = k / 39.0
        a = math.radians(-90 - 200 * t)
        pts.append((cxh + math.cos(a) * r, cyh + math.sin(a) * r, 0.8 * (1 - t) + 0.05))
    for fr_, col in lay:
        for px, py, w in pts:
            ww = 4.6 * sc * w * fr_
            if ww >= 0.8:
                cv.disc(px, py, max(0.0, (ww - 1) / 2), col)
    tx, ty = pts[-1][0], pts[-1][1]
    if glow:
        Frame(cv, tx, ty, 0).xglint(0, 0, 6, core=X0, mid=X1, edge=A25)
    return tx, ty


def gale_return():
    fr = tk.frame_sheet(64, 64, 4)
    cy = 26
    for i, cv in enumerate(fr):
        sh = [0, 6, 11, 14][i]
        lay = [(1.0, A21), (0.6, A23), (0.32, A25), (0.15, X1)] if i == 0 else \
            ([(1.0, A19), (0.6, A21), (0.3, A23)] if i < 3 else [(1.0, A18), (0.5, A19)])
        jhook(cv, 56 - sh, cy, 1.0, lay, glow=(i == 0))
        if i >= 1:                                       # 끌림 잔상 획(오른쪽으로 남음)
            for k, v in enumerate((-5, 0, 5)):
                ln = 8 + i * 4 - abs(v) * 0.6
                g = Frame(cv, 58 - sh, cy + 1 + v, 0)
                g.claw(0, ln, 1.6, [(1.0, A19 if i < 3 else A18)], peak=0.25, back=0.7)
        if i == 1:
            sparks(cv, 30 - sh, cy + 12, 6, 2, 10, 4, [A23, A21])
    sheet("trait_dagger_d_galeReturn", fr, [30, 40, 50, 70], "hitbox_center", (32, 32),
          "되돌아오는 단검이 적을 꿰어 거는 낚싯바늘 갈고리 — 재 발톱 곡선을 J 로 말아 끝에 X 섬광 → 갈고리가 왼쪽(주인공 쪽)으로 끌리며 뒤에 짧은 잔상 획 셋",
          ["걸림(X)", "끌림", "끌림", "식음"], glow=[0],
          flipX="allowed", flipNote="그림은 주인공이 왼쪽. 주인공이 오른쪽이면 flipX", rotate=False,
          **meta_common("d_galeReturn", spawn="trait_proc"))


# =============================================================================
# 12. 독주 투척 — 술병이 깨지며 술이 튀는 자국
# =============================================================================
def liquor_throw():
    fr = tk.frame_sheet(128, 96, 5)
    cx, cy = 64, 62
    for i, cv in enumerate(fr):
        t = i / 4.0
        if i >= 1:                                       # 바닥 술 자국(넓어짐)
            R = Rand(3)
            rr = [0, 18, 30, 36, 38][i]
            ink_blot(cv, cx, cy, rr, 12, core=A19, rim=A18, ky=0.4, ragged=0.28)
            ink_blot(cv, cx - 3, cy - 2, rr * 0.6, 13, core=A21, rim=A21, ky=0.35, ragged=0.25)
            for k in range(3):                           # 빛 띠(pool_liquor 말투)
                y = cy - 4 + k * 4
                tline(cv, cx - rr * 0.4 + k * 4, y, cx - rr * 0.1 + k * 6, y, A23 if i < 4 else A21)
            for k in range(10):                          # 튄 방울
                a = R.f() * 2 * math.pi
                d = rr + 4 + R.f() * 12
                cv.disc(cx + math.cos(a) * d, cy + math.sin(a) * d * 0.42, 1.0 if k % 3 else 1.6, A19 if k % 2 else A21)
        if i == 0:                                       # 깨지는 순간: 병 조각 + 술 왕관 섬광
            star4(cv, cx, cy - 6, 10, edge=A25, diag=5)
        if i <= 2:                                       # 술 왕관: 바깥으로 휘어 솟았다 떨어지는 방울 줄기 9
            for k in range(9):
                a = math.radians(180 + k * 22.5)
                ca, sa = math.cos(a), math.sin(a)
                L = [10, 18, 22][i]
                hgt = [12, 20, 12][i] * (0.7 + 0.3 * abs(math.sin(k * 1.7)))
                prev = None
                for j in range(12):
                    t = j / 11.0
                    d = 8 + i * 6 + L * t
                    x = cx + ca * d
                    y = cy - 4 + sa * d * 0.45 - hgt * 4 * t * (1 - t) * (1 if i < 2 else 1.4 - t)
                    if prev and t < 0.8:
                        tline(cv, prev[0], prev[1], x, y, A21 if t < 0.5 else A23)
                    prev = (x, y)
                cv.disc(prev[0], prev[1], 1.2, A23 if i < 2 else A21)
        # 유리 조각(재 회색 각진 조각) — 튀어 나갔다 떨어짐
        R = Rand(40)
        for k in range(8):
            a = math.radians(200 + R.f() * 140)
            d = 8 + 40 * t ** 0.7 + R.f() * 6
            x = cx + math.cos(a) * d
            y = cy - 4 + math.sin(a) * d * 0.5 + 60 * t * t * 0.5
            y = min(y, cy + 16)
            shard(cv, x, y, a + k, 3.2 - t, 1.6, S2 if k % 2 else S3)
            if i == 0:
                cv.put(x, y, X1)
    sheet("trait_dagger_liquorThrow", fr, [40, 50, 60, 80, 110], "floor", (64, 62),
          "술병이 깨지는 별 섬광 → 호박 술 왕관(바깥으로 휘어 솟는 방울 9줄기)과 재빛 유리 조각이 튀고 → 바닥에 넓게 번지는 술 자국(빛 띠 pool_liquor 말투) + 튄 방울. 끝 칸 뒤 시스템이 pool_liquor 로 이어 줌",
          ["깨짐(별)", "왕관", "튐", "번짐", "자리 잡음"], glow=[0], depth="floor",
          **meta_common("liquorThrow", spawn="trait_proc", next="pool_liquor"))


# =============================================================================
# 13. 그림자 사냥 — 적 발이 제 그림자에 붙잡히는 검은 손 고리(수명)
# =============================================================================
def grab_hand(cv, bx, by, sg, sc, flex, hi):
    """먹 손: 웅덩이에서 솟은 굵은 손목 + 갈퀴 손가락 셋(재 발톱 곡선)이 가운데(발목)로 크게 휘어 쥠.
    sg = +1 이면 왼쪽 손(오른쪽으로 쥠). sc = 크기, flex 0..1 = 오므림."""
    wx, wy = bx + sg * 2 * sc, by - 7 * sc
    taper(cv, bx, by + 1, wx, wy, 7 * sc, 5 * sc, INK)
    for k in range(3):
        ang = -90 - sg * (14 - k * 16) + sg * flex * 6
        L = (17 - abs(k - 1) * 3) * sc
        curl = sg * (8 + flex * 5) * sc
        f = Frame(cv, wx + sg * (k - 1) * 1.5, wy, ang)
        f.claw(0, L, 4.0 * sc, [(1.0, INK), (0.45, N2)], hook=curl, peak=0.22, back=1.0, hp=1.8)
        for u in range(int(L * 0.25), int(L * 0.9)):
            t = u / float(L)
            x, y = f.P(u, curl * t ** 1.8 - 1.6 * sg * sc * (1 - t))
            cv.put(x, y, N4 if t > 0.55 else N3)
        tx, ty = f.P(L, curl)
        cv.put(tx, ty, hi)


def ghost_bind():
    fr = tk.frame_sheet(128, 64, 4)
    cx, cy = 64, 44
    for i, cv in enumerate(fr):
        ell(cv, cx, cy, 44, 13, N3, dash=(16, 14), phase=i * 7, w=2)
        ell(cv, cx, cy, 44, 13, N5, dash=(3, 27), phase=i * 7 + 6)
        ink_blot(cv, cx, cy, 30, 21, core=INK, rim=S0, ky=0.36, ragged=0.22)
        flex = [0.0, 0.5, 1.0, 0.5][i]
        hi = N5 if i % 2 == 0 else N4
        grab_hand(cv, cx - 20, cy + 2, 1, 1.15, flex, hi)      # 좌우 손 둘이 발목을 양쪽에서 쥠
        grab_hand(cv, cx + 20, cy + 2, -1, 1.15, flex, hi)
    sheet("trait_dagger_d_ghostBind_bind", fr, [80, 80, 80, 80], "floor", (64, 44),
          "적 발밑 제 그림자(먹 웅덩이)에서 솟은 먹 손 둘이 양쪽에서 발목(가운데)을 움켜쥠 — 굵은 손목 + 재 발톱 곡선 손가락 셋이 갈퀴처럼 가운데로 휘어 오므림, 등 쪽 청회 빛줄·끝 청백 반짝. "
          "둘레 청회 점선 고리가 돎. 루프 내내 손가락이 오므렸다 폄. (그림자 매듭 bind 의 '꼰 끈'과 달리 '손')",
          ["루프", "루프", "루프", "루프"], loop=True, loopRange=[0, 3], depth="floor",
          lifeRule="묶여 있는 동안 0~3 루프(시스템 durationMs 로 끝냄 — 끝낼 때 알파 페이드 권장 120ms)",
          **meta_common("d_ghostBind", "bind", spawn="trait_bind"))


# =============================================================================
# 14. 취한 그림자 — 그림자가 지난 웅덩이에 불이 옮겨 붙는 불꽃
# =============================================================================
def ghost_fire():
    fr = tk.frame_sheet(96, 64, 5)
    cx, cy = 48, 46
    for i, cv in enumerate(fr):
        # 먹 그림자 가닥이 웅덩이를 가로질러 지나감(왼→오), 지난 자리에 불이 붙음
        reach = [60, 90, 90, 90, 90][i]
        for k in range(3):
            ink_tendril(cv, 4, cy - 2 + k * 3, -0.02 + k * 0.02, reach * (1 - k * 0.12), 4.5 - k, INK2 if k else INK, 5 + k, wav=0.3)
        for x in range(6, 4 + reach, 2):                 # 가닥 윗가장자리 재 테
            if h2(x, i, 4) < 0.7:
                cv.put(x, cy - 4 + int(1.5 * math.sin(x * 0.2)), S0)
        if i == 0:
            f = Frame(cv, 4 + reach, cy, 0)
            f.xglint(0, 0, 6, core=X0, mid=X1, edge=A25)
            sparks(cv, 4 + reach, cy, 6, 2, 8, 2, [A25, A23])
        else:
            hs = [[8, 12, 6], [16, 22, 14], [20, 26, 18], [12, 16, 10]][i - 1]
            for k, x in enumerate((20, 34, 48, 62, 76)):
                if i == 1 and x > 52:
                    continue
                h = hs[k % 3] * (1.0 - abs(x - 48) / 90.0)
                flame(cv, x, cy + 2 - (k % 2) * 3, h, 7 + (k % 2) * 2, lean=(-1) ** k * 0.6,
                      cols=(A19, A21, A23, A25) if i < 4 else (A19, A21, A23))
            sparks(cv, cx, cy - 18, 6 + 2 * i, 4, 22, 9 + i, [A23, A21, A25], ln=1, ky=0.7)
    sheet("trait_dagger_d_ghostFire", fr, [40, 60, 80, 90, 110], "floor", (48, 46),
          "먹 그림자 가닥이 웅덩이를 왼→오로 가로지르는 끝에 X 불씨 → 지난 자리를 따라 불혀 다섯이 차례로 솟음(pool_liquor_fire 램프). 끝 칸 뒤 시스템이 pool_liquor_fire 로 이어 줌",
          ["불씨(X)", "옮겨 붙음", "타오름", "타오름", "가라앉음"], glow=[0], depth="floor",
          light={"color": "#d67a11", "radius": 48, "intensity": 0.7, "ms": 300},
          flipX="allowed", flipNote="그림은 그림자가 왼→오. 반대면 flipX",
          **meta_common("d_ghostFire", spawn="trait_proc", next="pool_liquor_fire"))


# =============================================================================
# 15. 공명 얽힌 급소 — 낙인 폭발에서 옆 적으로 뻗는 사슬 끝
# =============================================================================
def res_vital():
    fr = tk.frame_sheet(96, 96, 5)
    cx, cy = 48, 48
    dirs = [-30, 60, 150, 240]
    for i, cv in enumerate(fr):
        # 가운데: 닫힌 발톱 고리(낙인 5 완성 모양)가 터짐
        r = [8, 11, 12, 12, 11][i]
        steps = 90
        for k in range(steps):
            t = k / float(steps - 1)
            a = math.radians(-215 + 290 * t)
            rr = r - 2.5 * t ** 3
            cv.disc(cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.85, 1.0, INK2)
        for k in range(steps):
            t = k / float(steps - 1)
            a = math.radians(-215 + 290 * t)
            rr = r - 2.5 * t ** 3
            cv.put(cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.85, [X1, A25, A23, A21, A19][i])
        if i == 0:
            star4(cv, cx, cy, 8, diag=4)
        else:
            ln = [0, 14, 24, 25, 22][i]
            for k, a in enumerate(dirs):
                rad = math.radians(a)
                x0, y0 = cx + math.cos(rad) * (r + 2), cy + math.sin(rad) * (r + 2)
                x1, y1 = cx + math.cos(rad) * (r + ln), cy + math.sin(rad) * (r + ln)
                ramp = DRAG if i < 3 else DRAG_DIM
                chain(cv, x0, y0, x1, y1, ramp, link=12, phase=k, glint={1, 3} if i == 2 else None,
                      broken={0} if i == 4 else None)
                hook(cv, x1, y1, a, 10, ramp, glow=(i == 1))
    sheet("trait_res_dagger_vital", fr, [40, 50, 60, 80, 100], "hitbox_center", (48, 48),
          "낙인 완성 고리(닫힌 발톱 고리)가 터지며 네 방향으로 적갈 사슬이 뻗어 끝 발톱 갈고리가 물어뜯음 — 실제 옆 적까지 이어지는 줄은 시스템 사슬(trait_common_chain#drag)",
          ["터짐(별)", "뻗음", "뻗음(마디 빛)", "걸림", "느슨"], glow=[0, 1],
          light={"color": "#b04848", "radius": 32, "intensity": 0.6, "ms": 250},
          weapon=W, resonance="res_dagger_vital", tag="vital", depth="above", spawn="resonance_proc")


# =============================================================================
# 16. 공명 그림자 길 — 그림자 길을 밟은 적에 붙는 낙인 그림자
# =============================================================================
def res_breach_mark():
    fr = tk.frame_sheet(64, 64, 4)
    cx, cy = 32, 30
    for i, cv in enumerate(fr):
        # 발밑에서 먹이 기어올라 몸에 비스듬한 자국 셋(그림자 낙인)을 그림
        rise = [0.4, 0.8, 1.0, 1.0][i]
        for k in range(3):
            x = cx - 6 + k * 6
            ink_tendril(cv, x - 2, 58, math.radians(-90 + 8 * (k - 1)), 26 * rise, 4.4, S0, 3 + k, wav=0.4)
            ink_tendril(cv, x - 2, 58, math.radians(-90 + 8 * (k - 1)), 26 * rise - 1, 2.6, INK, 3 + k, wav=0.4)
        if i >= 1:
            for k in range(3):
                core = [None, X1, A23, A21][i] if k == 1 else ([None, A23, A21, A19][i])
                cut(cv, cx - 5 + k * 5, cy - 2 + k, 16, 1.4, core, border=INK)
            for k in range(4):                           # 먹 방울이 아래로 흐름
                cv.disc(cx - 8 + k * 5, cy + 10 + (k * 3 + i) % 6, 0.8, INK2)
        if i == 1:
            Frame(cv, cx + 6, cy - 9, 0).xglint(0, 0, 4, core=X0, mid=X1, edge=A25)
    sheet("trait_res_dagger_breach_mark", fr, [40, 50, 70, 90], "hitbox_center", (32, 32),
          "그림자 길을 밟은 적의 발밑에서 먹 가닥 셋이 기어올라 몸에 비스듬한 먹 테 발톱 자국 셋을 새김(가운데 자국만 백열) — 먹 방울이 흘러내림. 길 자체(2.5초 띠)는 시스템 윤곽",
          ["기어오름", "새겨짐(X)", "남음", "식음"], glow=[1],
          weapon=W, resonance="res_dagger_breach", tag="breach", part="mark", depth="above", spawn="resonance_proc")


ALL = [pull_throw, brand_chain, shadow_knot, step_back, dash_brand, dash_pierce, flurry_pull, spark_flurry,
       twin_brand, clone_shield, gale_return, liquor_throw, ghost_bind, ghost_fire, res_vital, res_breach_mark]
