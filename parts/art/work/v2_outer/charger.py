"""적 결사병(charger) v2 — 32×48, 피벗 (16,46), 4방향 (50라운드 시범).

정체성 유지: 통 투구(눈 틈 2) · 넓은 어깨 · 파비스 방패(문장 '잔' 층 램프 19/21, 몸 앞) · 어깨에 멘 큰 망치.
방향별 소지품: left = 망치 전부 / right = 망치 머리만 등 뒤로. 방패는 옆면 모두 몸 앞(보는 쪽).
공격: 예고(웅크림·뒤로·방패 내림) → 돌진(앞으로) → 망치 찍기 → 복귀. 사망: 투구가 굴러가고 방패가 문장 위로 납작하게.
"""
from kit import *

FW, FH = 32, 48
HELM = [SL[0], G[3], G[5], G[7], G[9]]
ARMOR = [SL[0], G[2], G[3], G[4], G[6]]
GAMB = [SL[0], SL[2], SL[3], SL[4], SL[5]]      # 누비옷(차가운 회청)
BOOT = [SL[0], G[1], G[2], G[3], G[4]]
LEATHER = [WD[0], WD[1], WD[2], WD[3], WD[4]]
SHIELD = [WD[0], WD[1], WD[2], WD[3], WD[4]]
IRON = [SL[0], G[4], G[6], G[8], G[10]]
HAFT = [WD[0], WD[2], WD[3], WD[4], WD[5]]
EMB = [A[17], A[19], A[21], A[22], A[23]]


def P(name, ramp, base, **kw):
    return Part(name, ramp, base, **kw)


def pose(**kw):
    p = dict(bob=0, lean=0, crouch=0, fl=(0, 0), fr=(0, 0), maul="shoulder", shield=0, eye=1, helm=True)
    p.update(kw)
    return p


def emblem(R, x0, y0):
    """'잔' 문양: 술잔 실루엣 5×6 (층 램프)."""
    for x in range(x0, x0 + 5):
        R.dot(x, y0, EMB[2])
    for x in range(x0 + 1, x0 + 4):
        R.dot(x, y0 + 1, EMB[2]); R.dot(x, y0 + 2, EMB[1])
    R.dot(x0 + 1, y0 + 1, EMB[3])
    R.dot(x0 + 2, y0 + 3, EMB[1]); R.dot(x0 + 2, y0 + 4, EMB[1])
    for x in range(x0 + 1, x0 + 4):
        R.dot(x, y0 + 5, EMB[1])


def maul(R, head_c, haft_end, front=True, z="m"):
    """망치: 자루 끝(손) haft_end → 머리 중심 head_c. 머리 9×7 쇠 덩어리."""
    R.limb(P("haft" + z, HAFT, 2, group="haft" + z, edge=front), [haft_end, head_c], 2)
    hx_, hy = head_c
    R.rect(P("mhead" + z, IRON, 2, group="mhead" + z, edge=True), hx_ - 5, hy - 3, hx_ + 4, hy + 3)
    R.dot(hx_ - 4, hy - 2, IRON[4]); R.dot(hx_ - 3, hy - 2, IRON[3])


def draw_down(p):
    R = Rig(FW, FH)
    b = p["bob"] + p["crouch"]
    # 망치(어깨 뒤: 화면 왼쪽)
    if p["maul"] == "shoulder":
        maul(R, (7, 6 + b), (6, 34 + b), front=False, z="b")
    for side, (dx, lift) in (("l", p["fl"]), ("r", p["fr"])):
        x0 = (9 if side == "l" else 18) + dx
        fy = 46 - lift
        R.rect(P("leg" + side, GAMB, 2, group="leg" + side, edge=True), x0, 35 + b // 2, x0 + 5, fy - 4)
        R.rect(P("boot" + side, BOOT, 1, group="boot" + side), x0 - 1, fy - 4, x0 + 5, fy)
    R.poly(P("skirt", GAMB, 2, group="body", sh=2), [(7, 30 + b), (25, 30 + b), (26, 38 + b), (6, 38 + b)])
    R.poly(P("torso", ARMOR, 2, group="body", sh=2), [(6, 17 + b), (26, 17 + b), (24, 31 + b), (8, 31 + b)])
    R.rect(P("belt", LEATHER, 2, group="belt"), 7, 29 + b, 25, 31 + b)
    # 어깨받이
    R.ellipse(P("paul_l", ARMOR, 3, group="paul_l", edge=True), 3, 15 + b, 12, 23 + b)
    R.ellipse(P("paul_r", ARMOR, 3, group="paul_r", edge=True), 20, 15 + b, 29, 23 + b)
    # 오른팔(화면 왼쪽) — 망치 자루를 쥠
    R.limb(P("arm_l", GAMB, 2, group="arm_l", edge=True), [(6, 21 + b), (5, 31 + b)], 5)
    R.rect(P("hand_l", LEATHER, 3, group="hand_l"), 4, 31 + b, 7, 34 + b)
    # 투구
    R.rect(P("helm", HELM, 2, group="helm", sh=2), 10, 3 + b, 21, 17 + b)
    R.rect(P("helmtop", HELM, 3, group="helm"), 11, 2 + b, 20, 3 + b)
    R.rect(P("rim", HELM, 1, group="rim", edge=True), 9, 15 + b, 22, 17 + b)
    # 눈 틈 + 숨구멍
    for x in range(11, 21):
        if x not in (15, 16):
            R.dot(x, 8 + b, SL[0])
    R.dot(12, 9 + b, HELM[1]); R.dot(19, 9 + b, HELM[1])
    for (x, y) in ((13, 12), (15, 12), (17, 12), (14, 13), (16, 13)):
        R.dot(x, y + b, SL[1])
    R.dot(15, 4 + b, HELM[4]); R.dot(15, 5 + b, HELM[3])
    # 방패(화면 오른쪽 앞) — shield: 0 = 들고, 1 = 내림
    sy = 19 + b + p["shield"] * 4
    R.rect(P("shield", SHIELD, 3, group="shield", sh=1, edge=True), 17, sy, 29, sy + 21)
    R.rect(P("srim", IRON, 1, group="shield"), 17, sy, 29, sy + 1)
    # 방패 널 이음
    for x in (21, 25):
        for y in range(sy + 2, sy + 21):
            R.dot(x, y, SHIELD[1])
    emblem(R, 21, sy + 6)
    if p["maul"] == "smash":
        maul(R, (16, 40), (12, 26 + b), front=True, z="f")
    elif p["maul"] == "raised":
        maul(R, (10, 2), (8, 22 + b), front=True, z="f")
    return R.render()


def draw_up(p):
    R = Rig(FW, FH)
    b = p["bob"] + p["crouch"]
    # 방패(앞쪽 = 화면 반대, 몸 뒤로 가장자리만)
    sy = 19 + b + p["shield"] * 4
    R.rect(P("shield", SHIELD, 2, group="shield", edge=False), 2, sy, 12, sy + 20)
    for side, (dx, lift) in (("l", p["fl"]), ("r", p["fr"])):
        x0 = (9 if side == "l" else 18) + dx
        fy = 46 - lift
        R.rect(P("leg" + side, GAMB, 2, group="leg" + side, edge=True), x0, 35 + b // 2, x0 + 5, fy - 4)
        R.rect(P("boot" + side, BOOT, 1, group="boot" + side), x0 - 1, fy - 4, x0 + 5, fy)
    R.poly(P("skirt", GAMB, 2, group="body", sh=2), [(7, 30 + b), (25, 30 + b), (26, 38 + b), (6, 38 + b)])
    R.poly(P("torso", ARMOR, 2, group="body", sh=2), [(6, 17 + b), (26, 17 + b), (24, 31 + b), (8, 31 + b)])
    R.rect(P("belt", LEATHER, 2, group="belt"), 7, 29 + b, 25, 31 + b)
    # 등 끈 X
    R.limb(P("strap1", LEATHER, 2, group="strap"), [(9, 18 + b), (23, 29 + b)], 2)
    R.ellipse(P("paul_l", ARMOR, 3, group="paul_l", edge=True), 3, 15 + b, 12, 23 + b)
    R.ellipse(P("paul_r", ARMOR, 3, group="paul_r", edge=True), 20, 15 + b, 29, 23 + b)
    R.limb(P("arm_r", GAMB, 2, group="arm_r", edge=True), [(26, 21 + b), (27, 31 + b)], 5)
    R.rect(P("hand_r", LEATHER, 3, group="hand_r"), 25, 31 + b, 28, 34 + b)
    R.rect(P("helm", HELM, 2, group="helm", sh=2), 10, 3 + b, 21, 17 + b)
    R.rect(P("helmtop", HELM, 3, group="helm"), 11, 2 + b, 20, 3 + b)
    R.rect(P("rim", HELM, 1, group="rim", edge=True), 9, 15 + b, 22, 17 + b)
    # 뒤 리벳 줄
    for y in range(5, 15, 3):
        R.dot(15, y + b, HELM[1]); R.dot(16, y + b, HELM[3])
    if p["maul"] == "shoulder":
        maul(R, (25, 6 + b), (26, 34 + b), front=True, z="f")
    elif p["maul"] == "raised":
        maul(R, (22, 3), (24, 22 + b), front=False, z="b")
    elif p["maul"] == "smash":
        maul(R, (16, 8), (20, 22 + b), front=False, z="b")
    return R.render()


def draw_side(p, f):
    R = Rig(FW, FH)
    b = p["bob"] + p["crouch"]
    lx = p["lean"] * f

    def X(dx):
        return 16 + dx * f

    # right(f=+1): 망치 머리만 등 뒤 / left(f=-1): 망치 전부(몸 위)
    if p["maul"] == "shoulder" and f > 0:
        maul(R, (X(-8) + lx, 7 + b), (X(-3) + lx, 22 + b), front=False, z="b")
    if p["maul"] == "raised":
        maul(R, (X(-9) + lx, 4 + b), (X(-1) + lx, 20 + b), front=False, z="b")
    for name, (dx, lift), z in (("legb", p["fr"], 0), ("legf", p["fl"], 1)):
        fx = X(dx)
        fy = 46 - lift
        ramp = GAMB if z else [SL[0], SL[1], SL[2], SL[3], SL[4]]
        R.limb(P(name, ramp, 2, group=name, edge=True), [(X(0) + lx // 2, 35 + b), (fx, fy - 4)], 6)
        R.poly(P("boot" + name, BOOT, 1 if z else 0, group="boot" + name),
               [(fx - 3 * f, fy - 5), (fx + 4 * f, fy - 3), (fx + 4 * f, fy), (fx - 3 * f, fy)])
    R.poly(P("skirt", GAMB, 2, group="body", sh=2), [(X(-7) + lx, 30 + b), (X(6) + lx, 30 + b), (X(7) + lx, 38 + b), (X(-8) + lx, 38 + b)])
    R.poly(P("torso", ARMOR, 2, group="body", sh=2), [(X(-8) + lx, 17 + b), (X(6) + lx, 17 + b), (X(6) + lx, 31 + b), (X(-7) + lx, 31 + b)])
    R.rect(P("belt", LEATHER, 2, group="belt"), min(X(-7), X(6)) + lx, 29 + b, max(X(-7), X(6)) + lx, 31 + b)
    R.ellipse(P("paul", ARMOR, 3, group="paul", edge=True), min(X(-6), X(4)) + lx, 15 + b, max(X(-6), X(4)) + lx, 23 + b)
    # 투구(옆): 눈 틈은 앞쪽 끝
    R.rect(P("helm", HELM, 2, group="helm", sh=2), min(X(-6), X(5)) + lx, 3 + b, max(X(-6), X(5)) + lx, 17 + b)
    R.rect(P("helmtop", HELM, 3, group="helm"), min(X(-5), X(4)) + lx, 2 + b, max(X(-5), X(4)) + lx, 3 + b)
    R.rect(P("rim", HELM, 1, group="rim", edge=True), min(X(-7), X(6)) + lx, 15 + b, max(X(-7), X(6)) + lx, 17 + b)
    for dx in range(1, 6):
        R.dot(X(dx) + lx, 8 + b, SL[0])
    R.dot(X(-3) + lx, 9 + b, HELM[1]); R.dot(X(-3) + lx, 10 + b, HELM[1])
    # 방패: 몸 앞 (보는 쪽)
    sy = 19 + b + p["shield"] * 4
    sx = X(7 + p.get("sfw", 0)) + lx
    R.rect(P("shield", SHIELD, 3, group="shield", edge=True), min(sx, sx + 3 * f), sy, max(sx, sx + 3 * f), sy + 21)
    R.rect(P("srim", IRON, 2, group="shield"), min(sx, sx + 3 * f), sy, max(sx, sx + 3 * f), sy + 1)
    R.dot(sx + 1 * f, sy + 9, EMB[2]); R.dot(sx + 1 * f, sy + 10, EMB[1]); R.dot(sx + 2 * f, sy + 9, EMB[2])
    # 앞팔(방패 뒤에서 손잡이)
    R.limb(P("arm", GAMB, 2, group="arm", edge=True), [(X(0) + lx, 21 + b), (X(5) + lx, 29 + b)], 5)
    if p["maul"] == "shoulder" and f < 0:
        maul(R, (X(-6) + lx, 5 + b), (X(4) + lx, 30 + b), front=True, z="f")
    if p["maul"] == "smash":
        maul(R, (X(11) + lx, 41), (X(3) + lx, 26 + b), front=True, z="f")
    return R.render()


def draw(d, p):
    if d == "down":
        return draw_down(p)
    if d == "up":
        return draw_up(p)
    return draw_side(p, 1 if d == "right" else -1)


def draw_dead(d, k):
    """k: 3 = 무너짐, 4 = 더미, 5 = 안착. 투구가 굴러가고(옆) 방패가 문장 위로 납작."""
    R = Rig(FW, FH)
    f = -1 if d == "left" else 1
    cx = 16
    top = 30 if k == 3 else (34 if k == 4 else 35)
    # 몸 더미: 엎어진 몸통(타원) + 어깨받이 + 다리
    R.rect(P("legs", GAMB, 2, group="legs", edge=True), cx - 15 * f if f < 0 else cx - 15, 40, (cx - 15 * f if f < 0 else cx - 15) + 6, 46)
    R.ellipse(P("body", ARMOR, 2, group="body", sh=2), cx - 11, top, cx + 9, 46)
    R.ellipse(P("paul", ARMOR, 3, group="paul", edge=True), cx - 2, top - 2, cx + 8, top + 6)
    R.rect(P("belt", LEATHER, 2, group="belt"), cx - 9, top + 6, cx - 7, 45)
    # 방패 납작(문장 위로 → 나무 뒷면만 보임)
    R.rect(P("shield", SHIELD, 2, group="shield", edge=True), cx - 3, 41, cx + 12, 46)
    for x in (cx + 1, cx + 6):
        R.dot(x, 43, SHIELD[1]); R.dot(x, 44, SHIELD[1])
    # 굴러간 투구
    hx_ = cx + (9 if k >= 4 else 4) * f
    R.rect(P("helm", HELM, 2, group="helm", edge=True), hx_ - 4, 38 if k >= 4 else 36, hx_ + 4, 45 if k >= 4 else 43)
    R.dot(hx_ - 2, 40 if k >= 4 else 38, SL[0]); R.dot(hx_ - 1, 40 if k >= 4 else 38, SL[0])
    # 망치
    maul(R, (cx - 10 * f, 44), (cx - 1 * f, 44), front=True, z="f")
    return R.render()


def act(name, d):
    side = d in ("left", "right")
    if name == "idle":
        bob = [0, 0, 1, 1, 0, 0]
        return [pose(bob=bob[i], fl=(2, 0) if side else (0, 0), fr=(-2, 0) if side else (0, 0)) for i in range(6)]
    if name == "walk":
        out = []
        for i in range(8):
            if side:
                seq = [(3, 0), (1, 0), (0, 1), (-2, 0), (-3, 0), (-1, 0), (0, 1), (2, 0)]
                a, bb = seq[i], seq[(i + 4) % 8]
                out.append(pose(bob=[0, 1, 0, 0, 0, 1, 0, 0][i], fl=a, fr=bb))
            else:
                out.append(pose(bob=[1, 0, 0, 0, 1, 0, 0, 0][i], fl=(0, [0, 1, 2, 1, 0, 0, 0, 0][i]), fr=(0, [0, 0, 0, 0, 0, 1, 2, 1][i])))
        return out
    if name == "attack":
        kw = dict(fl=(3, 0), fr=(-3, 0)) if side else {}
        return [pose(crouch=2, lean=-1, shield=1, maul="raised", **kw),
                pose(lean=3, sfw=1, maul="raised", fl=(6, 0) if side else (0, 0), fr=(-5, 0) if side else (0, 0)),
                pose(crouch=1, lean=3, maul="smash", fl=(6, 0) if side else (0, 0), fr=(-4, 0) if side else (0, 0)),
                pose(lean=1, **kw)]
    if name == "hurt":
        kw = dict(fl=(2, 0), fr=(-2, 0)) if side else {}
        return [pose(lean=-1, **kw), pose(crouch=1, lean=-1, **kw)]
    if name == "death":
        kw = dict(fl=(2, 0), fr=(-2, 0)) if side else {}
        return [pose(lean=-1, **kw), pose(crouch=3, lean=-1, shield=1, **kw), pose(crouch=6, shield=1, **kw),
                ("dead", 3), ("dead", 4), ("dead", 5)]


MS = {
    "idle": [240] * 6,
    "walk": [140] * 8,
    "attack": [180, 60, 120, 140],
    "hurt": [70, 90],
    "death": [100, 120, 120, 130, 150, 220],
}
LOOP = {"idle": True, "walk": True, "attack": False, "hurt": False, "death": False}


def render_action(name):
    import player as PY
    res = {}
    for d in DIRS:
        fr = []
        for i, ps in enumerate(act(name, d)):
            if isinstance(ps, tuple):
                fr.append(draw_dead(d, ps[1]))
            else:
                im = draw(d, ps)
                if name == "hurt" and i == 0:
                    im = PY.flash(im)
                fr.append(im)
        res[d] = fr
    return res
