"""주인공 '전장의 망령' v2 — 32×48, 피벗 (16,46), 4방향 (50라운드 시범).

정체성 유지: 검은 케틀햇(넓은 챙) · 붕대 얼굴 · 왼눈 잔불(1층 램프 23/25) · 검은 긴 외투 · 각반 · 검은 장화 · 오른 허리 일기장(21).
2배 해상도에서 더한 것: 높은 깃, 외투 앞섶 갈라짐, 가죽 허리띠(WD), 모자띠의 꺼질 듯한 잔불 1점(21), 손 붕대.
그리는 방식: kit.Rig 부위 마스크 → 자동 셰이딩(빛 좌상단) → 셀아웃. 좌·우는 facing 부호로 기하만 뒤집고 셰이딩은 다시 계산.
draw() 는 (이미지, 앵커) 를 돌려준다 — 앵커 hand_f/hand_b(앞·뒤 손), hip(칼집 자리) 는 무기 오버레이가 쓴다.
"""
from kit import *

FW, FH = 32, 48
PIV = (16, 46)

COAT = [SL[0], SL[1], SL[2], SL[3], SL[4]]
COAT_IN = [SL[0], SL[0], SL[1], SL[2], SL[3]]          # 외투 안감·그늘진 앞섶
HAT = [SL[0], G[1], G[2], G[4], G[6]]
BAND = [PL[2], PL[3], PL[4], G[11], G[13]]             # 붕대(때 묻은 흰 천 — 어둠 속 얼굴이 초점)
CLOTH = [SL[1], G[3], G[5], G[6], G[8]]                # 각반
BOOT = [SL[0], G[1], G[2], G[3], G[4]]
LEATHER = [WD[0], WD[1], WD[2], WD[3], WD[4]]
DIARY = [A[17], A[19], A[21], A[22], A[23]]

EYE, EYE_HI = A[23], A[25]
EMBER = A[21]


def P(name, ramp, base, **kw):
    return Part(name, ramp, base, **kw)


# ---------------------------------------------------------------------------
# 포즈 기본값
# ---------------------------------------------------------------------------
def pose(**kw):
    p = dict(bob=0, lean=0, hat=0, hem=0, crouch=0,
             fl=(0, 0), fr=(0, 0),            # 발 오프셋 (dx, -lift)
             hl=(0, 0), hr=(0, 0),            # 손 오프셋 (dx, dy) — 옆면은 hl = 앞 손, hr = 뒤 손
             arm_f=None, arm_b=None,          # 손 절대 위치 지정(공격 등) — 몸 기준 좌표
             eye=1, ember=1, flare=0, tilt=0)
    p.update(kw)
    return p


# ---------------------------------------------------------------------------
# 정면 (down)
# ---------------------------------------------------------------------------
def draw_down(p):
    R = Rig(FW, FH)
    b = p["bob"] + p["crouch"]
    lx = p["lean"]
    cx = 16
    # 다리·장화
    for side, (dx, lift) in (("l", p["fl"]), ("r", p["fr"])):
        x0 = (11 if side == "l" else 17) + dx
        fy = 46 - lift
        R.rect(P("leg" + side, CLOTH, 2, group="leg" + side, edge=True), x0, 36 + b // 2, x0 + 3, fy - 3)
        R.poly(P("boot" + side, BOOT, 1, group="boot" + side), [(x0 - 1, fy - 4), (x0 + 4, fy - 4), (x0 + 4, fy), (x0 - 1, fy)])
    # 외투 자락 (앞섶 갈라짐)
    hem = 40 + p["hem"]
    sk = [(9 + lx, 29 + b), (23 + lx, 29 + b), (24 + lx + p["flare"], hem), (8 + lx - p["flare"], hem)]
    R.poly(P("skirt", COAT, 2, group="coat", sh=2), sk)
    R.poly(P("split", COAT_IN, 2, group="split", flat=True), [(15 + lx, 31 + b), (17 + lx, 31 + b), (18 + lx, hem), (14 + lx, hem)])
    # 몸통
    R.poly(P("torso", COAT, 2, group="coat", sh=2), [(8 + lx, 21 + b), (24 + lx, 21 + b), (23 + lx, 31 + b), (9 + lx, 31 + b)])
    # 허리띠 + 버클 + 일기장(오른 허리)
    R.rect(P("belt", LEATHER, 2, group="belt"), 9 + lx, 29 + b, 23 + lx, 30 + b)
    R.rect(P("diary", DIARY, 1, group="diary"), 20 + lx, 31 + b, 22 + lx, 34 + b)
    # 팔 (손 = 붕대)
    hand_l = (7 + lx + p["hl"][0], 34 + b + p["hl"][1])
    hand_r = (25 + lx + p["hr"][0], 34 + b + p["hr"][1])
    if p["arm_b"] is not None:
        hand_l = p["arm_b"]
    if p["arm_f"] is not None:
        hand_r = p["arm_f"]
    R.limb(P("arml", COAT, 2, group="arml", edge=True), [(9 + lx, 23 + b), (hand_l[0], hand_l[1] - 2)], 4)
    R.limb(P("armr", COAT, 2, group="armr", edge=True), [(23 + lx, 23 + b), (hand_r[0], hand_r[1] - 2)], 4)
    R.rect(P("handl", BAND, 2, group="handl"), hand_l[0] - 1, hand_l[1] - 1, hand_l[0] + 1, hand_l[1] + 1)
    R.rect(P("handr", BAND, 2, group="handr"), hand_r[0] - 1, hand_r[1] - 1, hand_r[0] + 1, hand_r[1] + 1)
    # 깃
    R.poly(P("collar", COAT, 3, group="collar", edge=True), [(10 + lx, 18 + b), (22 + lx, 18 + b), (23 + lx, 23 + b), (16 + lx, 25 + b), (9 + lx, 23 + b)])
    # 얼굴(붕대)
    hb = b + p["hat"]
    R.rect(P("face", BAND, 3, group="face"), 11 + lx, 12 + b, 20 + lx, 20 + b)
    # 모자: 정수리 + 띠 + 챙
    R.ellipse(P("crown", HAT, 2, group="hat", sh=2), 10 + lx, 2 + hb, 21 + lx, 12 + hb)
    R.rect(P("crown2", HAT, 2, group="hat", sh=2), 11 + lx, 4 + hb, 20 + lx, 9 + hb)
    R.rect(P("band", HAT, 1, group="band", flat=True), 10 + lx, 8 + hb, 21 + lx, 9 + hb)
    R.ellipse(P("brim", HAT, 2, group="brim", edge=True), 4 + lx, 9 + hb, 27 + lx, 14 + hb)
    # 덧칠: 챙 그늘(얼굴 맨 위 2줄), 붕대 감은 줄, 눈
    for x in range(11 + lx, 21 + lx):
        R.dot(x, 14 + b, BAND[0])                       # 챙 그늘
    for x in range(11 + lx, 21 + lx):
        R.dot(x, 18 + b, BAND[1] if (x + 1) % 3 else BAND[2])   # 붕대 감은 줄
    if p["eye"]:
        R.dot(13 + lx, 16 + b, EYE if p["eye"] == 1 else EYE_HI)
        R.dot(14 + lx, 16 + b, EYE_HI if p["eye"] == 2 else EYE)
        R.dot(13 + lx, 15 + b, BAND[1])
    R.dot(17 + lx, 16 + b, SL[0]); R.dot(18 + lx, 16 + b, BAND[0])        # 꺼진 오른눈
    if p["ember"]:
        R.dot(13 + lx, 8 + hb, EMBER)
    # 버클
    R.dot(15 + lx, 29 + b, G[9]); R.dot(16 + lx, 29 + b, G[7])
    im = R.render()
    anchors = {"hand_f": hand_r, "hand_b": hand_l, "hip": (10 + lx, 30 + b), "body_mask": None}
    return im, anchors


# ---------------------------------------------------------------------------
# 뒷면 (up)
# ---------------------------------------------------------------------------
def draw_up(p):
    R = Rig(FW, FH)
    b = p["bob"] + p["crouch"]
    lx = p["lean"]
    for side, (dx, lift) in (("l", p["fl"]), ("r", p["fr"])):
        x0 = (11 if side == "l" else 17) + dx
        fy = 46 - lift
        R.rect(P("leg" + side, CLOTH, 2, group="leg" + side, edge=True), x0, 36 + b // 2, x0 + 3, fy - 3)
        R.poly(P("boot" + side, BOOT, 1, group="boot" + side), [(x0 - 1, fy - 4), (x0 + 4, fy - 4), (x0 + 4, fy), (x0 - 1, fy)])
    hem = 41 + p["hem"]
    R.poly(P("skirt", COAT, 2, group="coat", sh=2), [(9 + lx, 29 + b), (23 + lx, 29 + b), (24 + lx + p["flare"], hem), (8 + lx - p["flare"], hem)])
    R.poly(P("torso", COAT, 2, group="coat", sh=2), [(8 + lx, 21 + b), (24 + lx, 21 + b), (23 + lx, 31 + b), (9 + lx, 31 + b)])
    # 등솔기 트임
    R.poly(P("vent", COAT_IN, 2, group="vent", flat=True), [(16 + lx, 33 + b), (17 + lx, 33 + b), (17 + lx, hem), (15 + lx, hem)])
    R.rect(P("belt", LEATHER, 2, group="belt"), 9 + lx, 29 + b, 23 + lx, 30 + b)
    hand_l = (7 + lx + p["hl"][0], 34 + b + p["hl"][1])
    hand_r = (25 + lx + p["hr"][0], 34 + b + p["hr"][1])
    if p["arm_b"] is not None:
        hand_r = p["arm_b"]
    if p["arm_f"] is not None:
        hand_l = p["arm_f"]
    R.limb(P("arml", COAT, 2, group="arml", edge=True), [(9 + lx, 23 + b), (hand_l[0], hand_l[1] - 2)], 4)
    R.limb(P("armr", COAT, 2, group="armr", edge=True), [(23 + lx, 23 + b), (hand_r[0], hand_r[1] - 2)], 4)
    R.rect(P("handl", BAND, 2, group="handl"), hand_l[0] - 1, hand_l[1] - 1, hand_l[0] + 1, hand_l[1] + 1)
    R.rect(P("handr", BAND, 2, group="handr"), hand_r[0] - 1, hand_r[1] - 1, hand_r[0] + 1, hand_r[1] + 1)
    # 사선 끈(등) — 왼 어깨 → 오른 허리
    R.limb(P("strap", LEATHER, 2, group="strap"), [(11 + lx, 21 + b), (21 + lx, 29 + b)], 2)
    R.poly(P("collar", COAT, 3, group="collar", edge=True), [(10 + lx, 18 + b), (22 + lx, 18 + b), (23 + lx, 22 + b), (9 + lx, 22 + b)])
    hb = b + p["hat"]
    R.rect(P("head", BAND, 1, group="face"), 11 + lx, 12 + b, 20 + lx, 19 + b)
    R.ellipse(P("crown", HAT, 2, group="hat", sh=2), 10 + lx, 2 + hb, 21 + lx, 12 + hb)
    R.rect(P("crown2", HAT, 2, group="hat", sh=2), 11 + lx, 4 + hb, 20 + lx, 9 + hb)
    R.rect(P("band", HAT, 1, group="band", flat=True), 10 + lx, 8 + hb, 21 + lx, 9 + hb)
    R.ellipse(P("brim", HAT, 2, group="brim", edge=True), 4 + lx, 8 + hb, 27 + lx, 13 + hb)
    # 붕대 매듭(뒤통수)
    for x in range(12 + lx, 20 + lx):
        R.dot(x, 16 + b, BAND[0] if x % 2 else BAND[1])
    R.dot(15 + lx, 17 + b, BAND[3]); R.dot(16 + lx, 18 + b, BAND[2]); R.dot(15 + lx, 18 + b, BAND[2])
    im = R.render()
    anchors = {"hand_f": hand_l, "hand_b": hand_r, "hip": (22 + lx, 30 + b)}
    return im, anchors


# ---------------------------------------------------------------------------
# 옆면 (left / right) — f = +1 오른쪽, -1 왼쪽. 몸 중심 cx=16.
# ---------------------------------------------------------------------------
def draw_side(p, f):
    R = Rig(FW, FH)
    b = p["bob"] + p["crouch"]
    lx = p["lean"] * f
    cx = 16

    def X(dx):
        return cx + dx * f

    # 뒤 다리 → 뒤 팔 → 자락 → 몸통 → 앞 다리? (외투가 다리를 덮으므로 다리 먼저)
    for name, (dx, lift), z in (("legb", p["fr"], 0), ("legf", p["fl"], 1)):
        fx = X(dx) + (0 if z else -0 * f)
        fy = 46 - lift
        hipx = X(0) + lx // 2
        ramp = CLOTH if z else [SL[1], SL[1], G[3], G[5], G[6]]
        R.limb(P(name, ramp, 2, group=name, edge=True), [(hipx, 36 + b), (fx, fy - 3)], 4)
        boot = [(fx - 2 * f, fy - 4), (fx + 4 * f, fy - 2), (fx + 4 * f, fy), (fx - 2 * f, fy)]
        R.poly(P("boot" + name, BOOT, 1 if z else 0, group="boot" + name), boot)
    # 뒤 팔
    hand_b = (X(-3) + lx + p["hr"][0] * f, 33 + b + p["hr"][1])
    if p["arm_b"] is not None:
        hand_b = p["arm_b"]
    R.limb(P("armb", [SL[0], SL[0], SL[1], SL[2], SL[3]], 2, group="armb", edge=True), [(X(-1) + lx, 23 + b), (hand_b[0], hand_b[1] - 2)], 4)
    R.rect(P("handb", [PL[0], PL[1], PL[2], PL[3], PL[4]], 1, group="handb"), hand_b[0] - 1, hand_b[1] - 1, hand_b[0] + 1, hand_b[1] + 1)
    # 자락 (뒤로 펄럭: flare)
    hem = 40 + p["hem"]
    back = X(-7 - p["flare"])
    front = X(5)
    sk = [(X(-5) + lx, 29 + b), (X(4) + lx, 29 + b), (front + lx // 2, hem), (back, hem - p["flare"] // 2)]
    R.poly(P("skirt", COAT, 2, group="coat", sh=2), sk)
    # 몸통 (옆면 폭 11)
    R.poly(P("torso", COAT, 2, group="coat", sh=2), [(X(-5) + lx, 21 + b), (X(5) + lx, 21 + b), (X(5) + lx, 31 + b), (X(-5) + lx, 31 + b)])
    R.rect(P("belt", LEATHER, 2, group="belt"), min(X(-5), X(5)) + lx, 29 + b, max(X(-5), X(5)) + lx, 30 + b)
    # 일기장: 오른쪽을 볼 때(몸 오른편이 보임) 보임
    if f > 0:
        R.rect(P("diary", DIARY, 1, group="diary"), min(X(0), X(2)) + lx, 31 + b, max(X(0), X(2)) + lx, 34 + b)
    # 깃
    R.poly(P("collar", COAT, 3, group="collar", edge=True), [(X(-4) + lx, 18 + b), (X(4) + lx, 18 + b), (X(5) + lx, 23 + b), (X(-5) + lx, 23 + b)])
    # 머리
    hb = b + p["hat"]
    R.rect(P("face", BAND, 3, group="face"), min(X(-3), X(3)) + lx, 12 + b, max(X(-3), X(3)) + lx, 20 + b)
    R.rect(P("nose", BAND, 3, group="face"), min(X(4), X(4)) + lx, 14 + b, max(X(4), X(4)) + lx, 18 + b)
    R.rect(P("nape", COAT_IN, 2, group="nape", flat=True), min(X(-4), X(-3)) + lx, 13 + b, max(X(-4), X(-3)) + lx, 18 + b)
    R.ellipse(P("crown", HAT, 2, group="hat", sh=2), min(X(-5), X(5)) + lx, 2 + hb, max(X(-5), X(5)) + lx, 12 + hb)
    R.rect(P("crown2", HAT, 2, group="hat", sh=2), min(X(-4), X(4)) + lx, 4 + hb, max(X(-4), X(4)) + lx, 9 + hb)
    R.rect(P("band", HAT, 1, group="band", flat=True), min(X(-5), X(5)) + lx, 8 + hb, max(X(-5), X(5)) + lx, 9 + hb)
    R.ellipse(P("brim", HAT, 2, group="brim", edge=True), min(X(-9), X(10)) + lx, 9 + hb, max(X(-9), X(10)) + lx, 14 + hb)
    # 앞 팔 (몸 위)
    hand_f = (X(2) + lx + p["hl"][0] * f, 34 + b + p["hl"][1])
    if p["arm_f"] is not None:
        hand_f = p["arm_f"]
    R.limb(P("armf", COAT, 2, group="armf", edge=True), [(X(0) + lx, 23 + b), (hand_f[0], hand_f[1] - 2)], 4)
    R.rect(P("handf", BAND, 2, group="handf"), hand_f[0] - 1, hand_f[1] - 1, hand_f[0] + 1, hand_f[1] + 1)
    # 덧칠: 챙 그늘 · 붕대 줄 · 눈
    for dx in range(-3, 6):
        R.dot(X(dx) + lx, 14 + b, BAND[0])
        R.dot(X(dx) + lx, 18 + b, BAND[1] if (dx + 1) % 3 else BAND[2])
    # 귀 쪽 붕대 매듭 그늘
    R.dot(X(-2) + lx, 16 + b, BAND[1]); R.dot(X(-2) + lx, 17 + b, BAND[1])
    if f < 0:
        if p["eye"]:
            R.dot(X(3) + lx, 16 + b, EYE if p["eye"] == 1 else EYE_HI)
            R.dot(X(4) + lx, 16 + b, EYE_HI if p["eye"] == 2 else EYE)
    else:
        R.dot(X(3) + lx, 16 + b, SL[0]); R.dot(X(4) + lx, 16 + b, BAND[0])
    if p["ember"]:
        R.dot(X(-3) + lx, 8 + hb, EMBER)
    im = R.render()
    anchors = {"hand_f": hand_f, "hand_b": hand_b, "hip": (X(-2) + lx, 30 + b)}
    return im, anchors


def draw(d, p):
    if d == "down":
        return draw_down(p)
    if d == "up":
        return draw_up(p)
    return draw_side(p, 1 if d == "right" else -1)


# ---------------------------------------------------------------------------
# 사망 후반(쓰러진 더미) — 방향별 직접 그림
# ---------------------------------------------------------------------------
def draw_heap(d, flat, eye):
    """flat: 0 = 무너지는 중, 1 = 안착. eye: 눈빛 남음 여부."""
    R = Rig(FW, FH)
    f = {"right": 1, "left": -1}.get(d, 0)
    if f:
        cx = 16
        hx_ = cx + 8 * f          # 머리 쪽(보는 방향)
        # 외투 더미(가로)
        top = 35 + flat
        R.poly(P("coat", COAT, 2, group="coat", sh=2),
               [(cx - 12 * f, 45), (cx - 10 * f, top + 2), (cx + 2 * f, top), (cx + 9 * f, top + 3), (cx + 11 * f, 45)])
        R.poly(P("boots", BOOT, 1, group="boots"), [(cx - 14 * f, 46), (cx - 14 * f, 42), (cx - 10 * f, 42), (cx - 10 * f, 46)])
        R.rect(P("face", BAND, 2, group="face"), min(hx_, hx_ + 4 * f), 40 + max(-2, flat), max(hx_, hx_ + 4 * f), 45)
        # 떨어진 모자
        hx2 = cx + 13 * f
        R.ellipse(P("brim", HAT, 2, group="brim", edge=True), min(hx2 - 5, hx2 + 3), 40, max(hx2 - 5, hx2 + 3), 46)
        R.ellipse(P("crown", HAT, 2, group="hat"), min(hx2 - 3, hx2 + 1), 37, max(hx2 - 3, hx2 + 1), 43)
        R.rect(P("hand", BAND, 2, group="hand"), cx - 2 * f - 1, 44, cx - 2 * f + 1, 45)
        R.rect(P("diary", DIARY, 1, group="diary"), min(cx - 5 * f, cx - 3 * f), 41 + max(0, flat), max(cx - 5 * f, cx - 3 * f), 44)
        if eye:
            R.dot(hx_ + 2 * f, 42 + max(-2, flat), EYE); R.dot(hx_ + 3 * f, 42 + max(-2, flat), EYE_HI if flat < 1 else EYE)
    else:
        # 정면·뒷면: 앞으로 엎어진 더미(위에서 본 등) — down 은 머리가 아래(화면 앞), up 은 위
        down = d == "down"
        R.poly(P("coat", COAT, 2, group="coat", sh=2),
               [(6, 44), (8, 35 + flat), (24, 35 + flat), (26, 44), (16, 46)])
        R.rect(P("split", COAT_IN, 2, group="split", flat=True), 15, 37 + flat, 16, 44)
        if down:
            R.rect(P("face", BAND, 2, group="face"), 13, 42 + max(0, flat), 18, 46)
            R.ellipse(P("brim", HAT, 2, group="brim", edge=True), 19, 40, 30, 46)
            R.ellipse(P("crown", HAT, 2, group="hat"), 21, 37, 28, 43)
            R.rect(P("handl", BAND, 2, group="hl"), 4, 43, 6, 45)
            R.rect(P("diary", DIARY, 1, group="diary"), 21, 35 + flat, 23, 38 + flat)
            if eye:
                R.dot(14, 44, EYE); R.dot(15, 44, EYE_HI if flat < 1 else EYE)
        else:
            R.ellipse(P("brim", HAT, 2, group="brim", edge=True), 9, 31 + flat, 22, 37 + flat)
            R.ellipse(P("crown", HAT, 2, group="hat"), 12, 28 + flat, 19, 34 + flat)
            R.rect(P("boots", BOOT, 1, group="boots"), 11, 43, 20, 46)
            R.rect(P("handr", BAND, 2, group="hr"), 25, 41, 27, 43)
            R.limb(P("strap", LEATHER, 2, group="strap"), [(10, 37 + flat), (21, 43)], 2)
    return R.render(), {"hand_f": (16, 44), "hand_b": (16, 44), "hip": (16, 42)}


def draw_kneel(d, p):
    """사망 3프레임: 무릎 꿇음 — 서 있는 그림을 아래로 내리고 다리를 접는다(크기 변경 없음)."""
    q = dict(p)
    q["crouch"] = p.get("crouch", 6)
    q["fl"] = (0, 0); q["fr"] = (0, 0)
    im, an = draw(d, q)
    # 접힌 다리: 내려온 외투 자락 아래 장화를 옆으로 눕혀 다시 칠함
    c = Canvas(FW, FH)
    c.paste(im, 0, 0)
    for y in range(43, 47):
        for x in range(FW):
            if c.get(x, y)[3] and c.get(x, y)[:3] in (BOOT[1][:3], BOOT[0][:3], BOOT[2][:3], BOOT[3][:3], CLOTH[2][:3]):
                c.px(x, y, CLEAR)
    return c.im, an


# ---------------------------------------------------------------------------
# 동작 정의 — (포즈 목록, ms)
# ---------------------------------------------------------------------------
def walk_side_feet(i):
    seq = [(4, 0), (2, 0), (0, 0), (-2, 0), (-4, 0), (-2, 2), (0, 3), (2, 1)]
    a = seq[i % 8]
    b = seq[(i + 4) % 8]
    return a, b


ACTIONS = {}


def act_idle(d):
    bob = [0, 0, 1, 1, 1, 0]
    hat = [0, 0, -1, 0, 0, 1]
    eye = [1, 1, 1, 2, 1, 1]
    side = d in ("left", "right")
    out = []
    for i in range(6):
        kw = dict(bob=bob[i], hat=hat[i], eye=eye[i], hem=1 if i in (2, 3, 4) else 0)
        if side:
            kw.update(fl=(2, 0), fr=(-2, 0))
        out.append(pose(**kw))
    return out


def act_walk(d):
    out = []
    side = d in ("left", "right")
    bob = [0, 0, -1, 0, 0, 0, -1, 0]
    for i in range(8):
        if side:
            a, b = walk_side_feet(i)
            arm = -a[0] // 2
            out.append(pose(bob=bob[i], fl=a, fr=b, hl=(arm, 0), hr=(-arm, 0), flare=1 + (i % 4 == 2),
                            hat=1 if i in (3, 7) else 0))
        else:
            lift_l = [0, 1, 2, 1, 0, 0, 0, 0][i]
            lift_r = [0, 0, 0, 0, 0, 1, 2, 1][i]
            sw = [0, -1, -1, 0, 0, 1, 1, 0][i]
            out.append(pose(bob=bob[i], fl=(0, lift_l), fr=(0, lift_r), hl=(0, sw), hr=(0, -sw),
                            hem=[0, 0, 1, 0, 0, 0, 1, 0][i], hat=1 if i in (3, 7) else 0))
    return out


def act_dash(d):
    side = d in ("left", "right")
    if side:
        return [pose(crouch=1, lean=-1, fl=(2, 0), fr=(-2, 0), hl=(-1, -1)),
                pose(lean=3, flare=4, hem=-1, fl=(6, 1), fr=(-6, 0), hl=(3, -2), hr=(-3, -1), hat=1),
                pose(lean=1, flare=2, fl=(3, 0), fr=(-3, 0), hl=(1, -1))]
    return [pose(crouch=1, hl=(1, -2), hr=(-1, -2)),
            pose(crouch=-1, flare=3, hem=-1, fl=(0, 2), hl=(-2, -3), hr=(2, -3), hat=1),
            pose(flare=1, hl=(-1, -1), hr=(1, -1))]


def act_hurt(d):
    side = d in ("left", "right")
    kw = dict(fl=(2, 0), fr=(-2, 0)) if side else {}
    return [pose(lean=-1, hat=-1, eye=2, **kw), pose(crouch=1, lean=-1, hl=(0, -2), hr=(0, -2), **kw)]


def act_death(d):
    side = d in ("left", "right")
    kw = dict(fl=(2, 0), fr=(-2, 0)) if side else {}
    return [pose(lean=-1, eye=2, hat=-1, **kw),
            pose(crouch=3, lean=0, hl=(0, 1), hr=(0, 1), hem=1, **kw),
            ("kneel", pose(crouch=6, hl=(0, 2), hr=(0, 2), hem=1, lean=1)),
            ("heap", -4, True),
            ("heap", 0, True),
            ("heap", 1, False)]


MS = {
    "idle": [220, 220, 220, 180, 220, 220],
    "walk": [110] * 8,
    "dash": [60, 90, 90],
    "hurt": [70, 90],
    "death": [90, 110, 110, 120, 140, 200],
}
LOOP = {"idle": True, "walk": True, "dash": False, "hurt": False, "death": False}
GEN = {"idle": act_idle, "walk": act_walk, "dash": act_dash, "hurt": act_hurt, "death": act_death}


def render_action(name):
    """반환 {dir: [(img, anchors)]}"""
    res = {}
    for d in DIRS:
        frames = []
        for i, ps in enumerate(GEN[name](d)):
            if isinstance(ps, tuple) and ps[0] == "kneel":
                frames.append(draw_kneel(d, ps[1]))
            elif isinstance(ps, tuple) and ps[0] == "heap":
                frames.append(draw_heap(d, ps[1], ps[2]))
            else:
                im, an = draw(d, ps)
                if name == "hurt" and i == 0:
                    im = flash(im)
                frames.append((im, an))
        res[d] = frames
    return res


def flash(im):
    """피격 플래시: 실루엣을 G14 로, 셀아웃은 유지."""
    out = im.copy()
    p = out.load(); w, h = out.size
    src = im.load()
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                edge = any(not (0 <= x + dx < w and 0 <= y + dy < h) or src[x + dx, y + dy][3] == 0
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                p[x, y] = OUTLINE if edge else G[14]
    return out
