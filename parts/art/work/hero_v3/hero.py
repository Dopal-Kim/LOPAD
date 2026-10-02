"""주인공 v3 '혼불이 새는 재 껍데기 망령' — 64×96, 피벗 (32,92) (52라운드 Q6~Q8, 1단계 검수용).

개념: parts/art/work/gemini/concept_char/hero3_b.jpg (확정). 생성 이미지 픽셀은 쓰지 않는다.
해부학 좌우(화면 아님):
  왼쪽  = 분노한 호박 눈빛 · 왼어깨 견갑 + 혼불 · 흉갑 조각(가슴 왼쪽) · 왼팔뚝 완갑 · 왼정강이 붕대
  오른쪽 = 꺼진 눈 · 오른어깨 뒤 화살 · 오른정강이 정강이받이 · 오른허리 일기장
  가운데 = 가슴 균열 혼불(앞), 등 균열 혼불(뒤), 정수리 균열(머리 위 왼쪽)
방향: down = 정면(해부 왼쪽이 화면 오른쪽) / up = 뒷면(해부 왼쪽이 화면 왼쪽) / left·right = 측면.
빛은 언제나 화면 좌상단 — 측면 좌우는 거울이 아니라 다시 그린다(셰이딩도 다시 계산).
비율: 머리 약 19px / 키 약 84px (≈1:4.4, 탑다운에서 머리·눈빛이 읽히도록).
"""
import math

from v3kit import Rig3, Part, G, A, SL, WD, PL, OUT, ik2

FW, FH = 64, 96
PIV = (32, 92)

# ---- 팔레트 (색 예산 30, 52라운드 Q7) -------------------------------------
ASH = [G[1], G[2], G[3], G[4], G[5], G[6], G[8]]   # 재 껍데기 몸 (본색 3 = G04)
FACE = [G[1], G[1], G[2], G[3], G[4]]             # 그늘진 얼굴 — 무늬 없는 검정이 아니라 어두운 재(광대·턱이 읽힘)
IRON = [SL[1], SL[2], SL[4], SL[6]]                # 갑옷 파편(어두운 녹슨 쇠 — 밝은 판금으로 읽히지 않게)
CLOTH = [WD[1], WD[2], WD[3], WD[4]]               # 찢긴 허리천·끈·화살대
BAND = [PL[0], PL[1], PL[2]]                       # 때 묻은 붕대(어둡게 — 흰 덩어리 방지)
DIARY = [A[17], A[18], A[19], A[21]]               # 일기장 (층 램프 21 본색 — 바이블 4절)
FIRE = {".": A[19], "r": A[21], "o": A[23], "O": A[25], "H": A[26]}
EYE = [A[21], A[23], A[25], A[26]]

# 골격 (정면 기준, dx = 해부 왼쪽 +)
HEAD_Y, HEAD_RX, HEAD_RY = 17.0, 7.6, 8.8
SH_Y = 35.0           # 어깨 관절
HIP_Y = 58.0
FOOT_Y = 89.0
THIGH, SHIN = 16.0, 15.6
UPPER, FORE = 13.6, 13.4
HAND_Y = 61.0
LIMB_BANDS = ((0.93, 2), (0.80, 1), (0.30, 0), (0.0, -1), (-9, -2))   # 팔다리: 몸통과 명도를 맞추려 빛 단계를 아낌

# 어깨 혼불 6모양 (아래가 발원점) — '작게 항상 깜빡임'(52라운드 Q6)
FLAMES = [
    ["  .  ", "  o  ", " oO  ", " oOo ", " rHr ", "  r  "],
    ["   . ", "  o  ", "  Oo ", " oOo ", " rHr ", "  r  "],
    ["     ", " .   ", " oo  ", " oOo ", " rOr ", "  r  "],
    ["  .  ", "  o. ", " oO  ", " OHo ", " rOr ", "  r  "],
    ["     ", "   . ", "  oo ", " oOo ", " rHr ", "  r  "],
    [" .   ", "  o  ", " oOo ", " oHo ", " rOr ", "  r  "],
]


def P(name, ramp, base, **kw):
    return Part(name, ramp, base, **kw)


def pose(**kw):
    p = dict(bob=0, breath=0, head=0, tilt=0.0,
             lift=(0, 0), step=(0.0, 0.0),        # 정면: (해부 왼, 오른)
             hand=((0, 0), (0, 0)),               # 정면: 손 오프셋 (왼, 오른) / 측면: ((먼 손 x, 0), (가까운 손 x, 0))
             sway=0.0, flame=0, lean=0.0, pulse=0,
             foot=((0.0, 0.0), (0.0, 0.0)),       # 측면: (앞뒤 x, 들림) (먼 다리, 가까운 다리)
             lean_body=0.0)
    p.update(kw)
    return p


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def draw_flame(R, x0, y0, variant, lean, rows=None):
    g = FLAMES[variant % len(FLAMES)]
    if rows:
        g = g[-rows:]
    h = len(g)
    for r, row in enumerate(g):
        k = (h - 1 - r) / max(1, h - 1)
        sx = round(lean * k)
        for c, ch in enumerate(row):
            if ch != " ":
                R.dot(x0 + (c - 2) + sx, y0 - (h - 1 - r), FIRE[ch])


def crack(R, pts, X, pulse=0, thick=(1, 0), spill=4.0):
    """균열 혼불: 점 경로 → 중심선(23/25/26) + 한쪽 두께(21) + 주변 몸 빛 번짐."""
    seen = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)))
        for k in range(n + 1):
            t = k / max(1, n)
            c = (round(X(x0 + (x1 - x0) * t)), round(y0 + (y1 - y0) * t))
            if c not in seen:
                seen.append(c)
    if spill:
        R.spill_cells.extend(seen)
    if thick != (0, 0):
        for x, y in seen:
            R.dot(x + thick[0], y + thick[1], A[21])
    n = len(seen)
    for i, (x, y) in enumerate(seen):
        mid = 0.25 < i / n < 0.75
        c = A[26] if (mid and pulse and i % 2 == 0) else (A[25] if mid else A[23])
        R.dot(x, y, c)


def groove(R, pts, X, Y, hi=True):
    """재 껍데기 금(어두운 홈 G01) + 홈 아래 오른쪽 가장자리 빛(G05) 한 칸씩 걸러."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)))
        for k in range(n + 1):
            t = k / max(1, n)
            dx, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            x, yy = round(X(dx)), round(Y(dx, y))
            R.dot(x, yy, G[1])
            if hi and k % 2 == 0:
                R.dot(x + 1, yy + 1, G[5])


# =============================================================================
# 정면(down) · 뒷면(up)
# =============================================================================
def draw_front(p, back=False):
    R = Rig3(FW, FH)
    m = -1 if back else 1                        # 해부 왼쪽(+dx) 의 화면 방향
    X = lambda dx: 32 + m * dx                   # noqa: E731
    b, br, hd, tilt = p["bob"], p["breath"], p["head"], p["tilt"]

    def sy(dx, y):                               # 어깨 기울기·숨: 가슴 위쪽만
        t = 0.0
        if y < 46:
            t = (tilt if dx > 0 else -tilt) * min(1.0, abs(dx) / 15.0) - br * (46 - y) / 15.0
        return y + b + t

    # --- 화살 (정면: 오른어깨 뒤에서 위·바깥으로 솟음 — 몸 뒤) -------------------
    if not back:
        a0, a1 = (X(-11), sy(-11, 33)), (X(-19), sy(-19, 20))
        R.capsule(P("arrow", CLOTH, 2, flat=True, rim=False, cast=False), [a0, a1], [0.6, 0.6])
        R.poly(P("fletch", ASH, 5, flat=True, rim=False, cast=False),
               [(X(-18.5), sy(-18.5, 21)), (X(-22), sy(-22, 15)), (X(-20.5), sy(-20.5, 21.5))])
    # --- 다리 --------------------------------------------------------------
    for side, s in (("L", 1), ("R", -1)):
        li = 0 if side == "L" else 1
        hip = (X(s * 5.2), HIP_Y + b)
        fy = FOOT_Y + p["step"][li] - p["lift"][li]
        foot = (X(s * 6.0), fy)
        # 정면 무릎은 카메라 쪽으로 굽어 보이지 않는다 — 들림만큼 살짝 바깥·위로(IK 옆꺾임 = O다리 방지)
        lift = p["lift"][li]
        knee = ((hip[0] + foot[0]) / 2 + m * s * 0.35 * lift, (hip[1] + foot[1]) / 2 - 0.3 * lift + 0.5)
        R.capsule(P("leg" + side, ASH, 2, group="leg" + side, soft=2.0, vgrad=0.82, bands=LIMB_BANDS), [hip, knee, foot], [4.4, 3.3, 2.5])
        R.ellipse(P("foot" + side, ASH, 2, group="foot" + side, soft=1.2), foot[0] + m * s * 0.5, fy + 1.6, 4.2, 2.3)
        sh, an = lerp(knee, foot, 0.18), lerp(knee, foot, 0.86)
        if side == "R":
            R.poly(P("greave", IRON, 2, soft=1.4), [(sh[0] - 3.4, sh[1] + 1), (sh[0] + 3.2, sh[1]), (an[0] + 2.6, an[1] - 4), (an[0] - 0.5, an[1] - 1.5), (an[0] - 3.0, an[1] - 4.5)])
            R.ellipse(P("kneecap", IRON, 2, group="greave", soft=1.0), knee[0], knee[1] - 0.5, 2.6, 2.0)
        else:
            R.capsule(P("shinband", BAND, 1, soft=1.0, rim=False), [lerp(knee, foot, 0.3), an], [3.2, 2.8])
            for k in range(3):
                q = lerp(lerp(knee, foot, 0.3), an, 0.2 + 0.3 * k)
                for ox in (-2, -1, 0):
                    R.dot(round(q[0]) + ox, round(q[1]) + (1 if ox == 0 else 0), PL[0])
    # --- 몸통 (굽은 등: 승모가 높고 머리가 어깨선에 걸림) ----------------------
    torso = [(-5.5, 27), (5.5, 27), (13, 31), (16.5, 35), (15.5, 43), (11, 50), (9.6, 57), (-9.6, 57), (-11, 50), (-15.5, 43), (-16.5, 35), (-13, 31)]
    R.poly(P("torso", ASH, 2, group="body", soft=4.5, vgrad=0.78), [(X(dx), sy(dx, y)) for dx, y in torso])
    # --- 허리천 (찢긴 천) — 한 박자 늦는 흔들림 sway ----------------------------
    sw = p["sway"]
    hem = [(11, 60), (10 + sw, 67), (7.5 + sw, 64.5), (5 + sw, 70), (1.5 + sw, 66), (-2 + sw, 69.5), (-5 + sw, 65), (-8 + sw, 69), (-10.5 + sw, 65), (-11, 60)]
    R.poly(P("loin", CLOTH, 1, soft=1.8), [(X(-11), 54 + b), (X(11), 54 + b)] + [(X(dx), y + b) for dx, y in hem])
    R.capsule(P("belt", CLOTH, 2, soft=0.8), [(X(-10.5), 54.5 + b), (X(10.5), 55 + b)], [1.3, 1.3])
    # --- 일기장 (오른허리) ---------------------------------------------------
    dx0 = -15.5 - 0.4 * sw
    R.poly(P("diary", DIARY, 2, soft=1.0), [(X(dx0), 56 + b), (X(dx0 + 5.5), 55.5 + b), (X(dx0 + 5.5), 62.5 + b), (X(dx0), 63 + b)])
    # --- 흉갑 조각(앞) / 등 끈(뒤) -----------------------------------------------
    if not back:
        R.poly(P("plate", IRON, 2, soft=1.8), [(X(dx), sy(dx, y)) for dx, y in [(2, 34.5), (12.5, 32.5), (14.5, 39.5), (10.5, 47), (3, 45)]])
        R.capsule(P("strap", CLOTH, 1, soft=0.8, rim=False), [(X(-12.5), sy(-12.5, 31)), (X(3), sy(3, 40))], [1.1, 1.1])
    else:
        R.capsule(P("strap", CLOTH, 1, soft=0.8, rim=False), [(X(13), sy(13, 31)), (X(-8.5), sy(-8.5, 52))], [1.2, 1.2])
    # --- 팔 ---------------------------------------------------------------
    for side, s in (("L", 1), ("R", -1)):
        li = 0 if side == "L" else 1
        sh_ = (X(s * 15.2), sy(s * 15.2, SH_Y))
        hd_ = (X(s * 17.6) + m * s * p["hand"][li][0], HAND_Y + b + p["hand"][li][1] - br * 0.5)
        el = lerp(sh_, hd_, 0.5)                    # 정면 팔은 앞뒤로 흔들려 단축만 보임 — 팔꿈치 옆꺾임 없음
        el = (el[0] + m * s * 1.2, el[1])
        R.capsule(P("arm" + side, ASH, 2, group="arm" + side, soft=1.8, vgrad=0.85, bands=LIMB_BANDS), [sh_, el, (hd_[0], hd_[1] - 2.2)], [3.5, 2.9, 2.4])
        if side == "L":
            R.capsule(P("vamb", IRON, 2, soft=1.0), [lerp(el, hd_, 0.30), lerp(el, hd_, 0.66)], [3.2, 2.9])
        R.ellipse(P("hand" + side, BAND, 1, soft=1.0, rim=False), hd_[0], hd_[1] + 0.4, 2.4, 3.0)
    # --- 목 · 머리 ---------------------------------------------------------
    hy = HEAD_Y + b + hd
    R.poly(P("neck", ASH, 2, group="body", soft=1.5), [(X(-3.6), hy + 6), (X(3.6), hy + 6), (X(4.2), sy(4.2, 30)), (X(-4.2), sy(-4.2, 30))])
    R.ellipse(P("head", ASH, 3, group="head", soft=3.4, vgrad=0.80), 32, hy, HEAD_RX, HEAD_RY)
    if not back:
        R.poly(P("jaw", ASH, 2, group="head", soft=1.8), [(X(-5.6), hy + 4), (X(5.6), hy + 4), (X(4.0), hy + 10), (X(-4.0), hy + 10)])
        R.poly(P("face", FACE, 2, group="head", soft=1.6, rim=False, cast=False, warm=True, vgrad=0.75),
               [(X(-6.9), hy + 1.5), (X(-5.5), hy - 0.8), (X(-2.5), hy + 0.2), (X(0), hy + 1.6), (X(2.5), hy + 0.2), (X(5.5), hy - 0.8),
                (X(6.9), hy + 1.5), (X(6.4), hy + 4.5), (X(4.4), hy + 9.6), (X(-4.4), hy + 9.6), (X(-6.4), hy + 4.5)])
    else:
        R.poly(P("nape", ASH, 2, group="head", soft=1.8), [(X(-5), hy + 4), (X(5), hy + 4), (X(3.8), hy + 9.5), (X(-3.8), hy + 9.5)])
    # --- 견갑 (왼어깨) ------------------------------------------------------
    R.poly(P("pauldron", IRON, 2, soft=1.8), [(X(dx), sy(dx, y)) for dx, y in [(8, 29.5), (15, 29.5), (20, 33.5), (19.5, 39), (13.5, 38.5), (8.5, 34)]])
    # --- 뒷면 화살 (등에 꽂힘 — 몸 앞으로 그림) -----------------------------------
    if back:
        for (bx, by), (tx, ty), fl in (((-8, 38), (-16, 24), -1), ((9, 46), (16, 34), 1)):
            R.capsule(P("arrowb", CLOTH, 2, flat=True, rim=False, cast=False), [(X(bx), sy(bx, by)), (X(tx), sy(tx, ty))], [0.6, 0.6])
            R.poly(P("fletchb", ASH, 5, flat=True, rim=False, cast=False),
                   [(X(tx), sy(tx, ty)), (X(tx + fl * 2.5), sy(tx, ty) - 4.5), (X(tx - fl * 1.0), sy(tx, ty) - 0.5)])

    # ======================= 덧칠 =======================
    # 정수리 빛(화면 좌상단) + 균열(해부 왼쪽 위)
    for ddx, dy in ((-4, -7), (-3, -7), (-2, -8), (-5, -6), (-4, -6)):
        R.dot(32 + ddx, hy + dy, G[8])
    for dx, dy, c in ((2, -8, A[19]), (3, -7, A[21]), (3, -6, A[23]), (4, -5, A[21]), (5, -4, A[19])):
        R.dot(X(dx), hy + dy, c)
    if not back:
        # 이마 그늘(분노: 미간 쪽으로 처짐) · 눈빛(왼눈) · 꺼진 눈(오른눈)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (2, -1), (3, -1), (4, -2), (-2, -1), (-3, -1), (-4, -2), (5, -2), (-5, -2)):
            R.dot(X(dx), hy + dy, G[5])                                                    # 이마뼈 윗면 빛(분노: 미간이 낮음)
        for dx, dy in ((1, 1), (2, 1), (3, 1), (4, 0), (5, 0), (6, 0), (-1, 1), (-2, 1), (-3, 1), (-4, 0), (-5, 0), (-6, 1)):
            R.dot(X(dx), hy + dy, OUT)                                                     # 이마뼈 아래 깊은 그늘(눈두덩)
        for dx, dy in ((-5, 6), (-4, 7), (5, 6), (4, 7)):
            R.dot(X(dx), hy + dy, G[1])                                                    # 광대 아래 패임
        for dx in (-2, -1, 0, 1, 2):
            R.dot(X(dx), hy + 8, G[1])                                                     # 닫힌 입(드러내지 않음)
        R.spill.append((X(4), hy + 2, 2.6))
        for dx, dy, c in ((2, 2, EYE[0]), (3, 2, EYE[1]), (4, 1, EYE[2]), (5, 1, EYE[3] if p["pulse"] else EYE[2]), (6, 0, EYE[1]),
                          (3, 3, EYE[0]), (4, 2, EYE[2]), (5, 2, EYE[1])):
            R.dot(X(dx), hy + dy, c)
        for dx, dy in ((-3, 2), (-4, 2), (-3, 3), (-4, 3), (-5, 2)):
            R.dot(X(dx), hy + dy, OUT)
        # 가슴 균열
        crack(R, [(-3, 35), (-1, 38), (-4.5, 41), (-1.5, 44), (-3.5, 48), (-1, 51)], lambda dx: X(dx), pulse=p["pulse"], thick=(m, 0), spill=5.0)
        crack(R, [(-1, 38), (2.5, 39)], lambda dx: X(dx), thick=(0, 1), spill=0.0)
        for dx, y in ((-11, 42), (-10, 42), (-11, 45), (-10, 45), (-9, 45), (-10, 48), (-9, 48), (8, 49), (9, 49), (9, 52), (8, 52)):   # 갈비 그늘
            R.dot(X(dx), sy(dx, y), G[2])
        for s_ in (1, -1):                                                                              # 쇄골 아래 그늘
            for k in range(7):
                dx = s_ * (3.5 + k)
                if not (s_ == 1 and dx > 3):                                                            # 흉갑 아래는 생략
                    R.dot(X(dx), sy(dx, 31 + k * 0.25), G[1])
        groove(R, [(-14.5, 37), (-12.5, 39.5), (-13.5, 42.5), (-12, 45)], X, sy)                         # 껍데기 금
        groove(R, [(6, 49), (7.5, 51.5), (6.5, 54)], X, sy, hi=False)
        R.dot(X(16), 52 + b, SL[6]); R.dot(X(17), 53 + b, SL[2])          # 팔뚝 위 못머리
    else:
        crack(R, [(1, 34), (-1.5, 38), (2, 42), (-1, 46), (1.5, 50), (0, 54)], lambda dx: X(dx), pulse=p["pulse"], thick=(m, 0), spill=6.0)
        crack(R, [(2, 42), (6.5, 40)], lambda dx: X(dx), thick=(0, 1), spill=0.0)
        for s_ in (1, -1):                                                                              # 견갑골 그늘
            for k in range(5):
                R.dot(X(s_ * (6 + k)), sy(s_ * (6 + k), 40 + k * 0.6), G[1])
        groove(R, [(-14, 43), (-12, 45.5), (-12.5, 48)], X, sy)
        groove(R, [(11.5, 37), (13.5, 40), (12.5, 42)], X, sy, hi=False)
        for dx, y in ((-4, 32), (6, 35), (-11, 44)):                                                   # 못머리
            R.dot(X(dx), sy(dx, y), SL[6]); R.dot(X(dx) + 1, sy(dx, y) + 1, SL[2])
    # 일기장 걸쇠 · 끈 · 허리끈 매듭
    R.dot(X(dx0 + 2.75), 59 + b, G[9])
    R.line([(X(-10), 55 + b), (X(dx0 + 2.75), 56 + b)], WD[3])
    R.dot(X(-2), 56 + b, WD[4]); R.dot(X(-1), 57 + b, WD[3]); R.dot(X(-2), 58 + b, WD[3])
    # 어깨 혼불 (해부 왼어깨 위)
    fx, fy = round(X(13)), round(sy(13, 29))
    R.dot(fx, fy + 1, A[19])
    draw_flame(R, fx, fy, p["flame"], p["lean"])
    return R.render()


# =============================================================================
# 측면 (left / right)
# =============================================================================
def draw_side(p, facing):
    """facing = +1 오른쪽, -1 왼쪽. dx 는 '앞' 이 + 인 몸 좌표."""
    R = Rig3(FW, FH)
    f = facing
    X = lambda dx: 32 + f * dx                   # noqa: E731
    near = "R" if f == 1 else "L"                # 화면 쪽에 보이는 해부 측
    b, br, hd, lb = p["bob"], p["breath"], p["head"], p["lean_body"]

    def ux(dx, y):                               # 상체 앞숙임(위로 갈수록 앞으로) + 숨(가슴 앞으로)
        return X(dx + lb * max(0.0, (HIP_Y - y)) / 28.0 + (br * 0.35 if dx > 0 and y < 46 else 0))

    def uy(y):
        return y + b - (br * (46 - y) / 15.0 if y < 46 else 0)

    def anat(which):
        return near if which == "near" else ("L" if near == "R" else "R")

    def leg(which, shade):
        fxp, lift = p["foot"][0 if which == "far" else 1]
        hip = (X(-0.5), HIP_Y + b)
        foot = (X(fxp), FOOT_Y - lift)
        knee = ik2(hip, foot, THIGH, SHIN, f)
        name = "leg_" + which
        R.capsule(P(name, ASH, 2 - shade, group=name, soft=2.0, vgrad=0.82, bands=LIMB_BANDS), [hip, knee, foot], [4.4, 3.3, 2.5])
        fy = 92 - lift
        R.poly(P("foot_" + which, ASH, 2 - shade, group="foot_" + which, soft=1.2),
               [(X(fxp - 3), fy - 3.6), (X(fxp + 2), fy - 3.6), (X(fxp + 6), fy - 1.4), (X(fxp + 6), fy), (X(fxp - 3.4), fy)])
        sh, an = lerp(knee, foot, 0.18), lerp(knee, foot, 0.86)
        if anat(which) == "R":
            R.capsule(P("greave_" + which, IRON, 2 - shade, soft=1.3), [lerp(knee, foot, 0.22), lerp(knee, foot, 0.70)], [3.3, 2.8])
        else:
            R.capsule(P("band_" + which, BAND, 1 - shade, soft=1.0, rim=False), [lerp(knee, foot, 0.3), an], [3.1, 2.7])

    def arm(which, shade, swing):
        sh_ = (ux(0.5, SH_Y), uy(SH_Y))
        hd_ = (X(swing + lb * 0.6), HAND_Y + b - br * 0.5)
        el = ik2(sh_, hd_, UPPER, FORE, -f)
        name = "arm_" + which
        R.capsule(P(name, ASH, 2 - shade, group=name, soft=1.8, vgrad=0.85, bands=LIMB_BANDS), [sh_, el, (hd_[0], hd_[1] - 2.2)], [3.3, 2.8, 2.3])
        if anat(which) == "L":
            R.capsule(P("vamb_" + which, IRON, 2 - shade, soft=1.0), [lerp(el, hd_, 0.30), lerp(el, hd_, 0.66)], [3.1, 2.8])
        R.ellipse(P("hand_" + which, BAND, 1 - shade, soft=1.0, rim=False), hd_[0], hd_[1] + 0.4, 2.4, 2.9)

    swing = p["hand"]
    # --- 먼 쪽 화살(왼쪽을 볼 때: 오른어깨 화살이 등 위로 솟음) ----------------------
    if near == "L":
        R.capsule(P("arrow_far", CLOTH, 1, flat=True, rim=False, cast=False), [(ux(-4, 33), uy(33)), (ux(-12, 19), uy(19))], [0.6, 0.6])
        R.poly(P("fletch_far", ASH, 4, flat=True, rim=False, cast=False), [(ux(-11.5, 20), uy(20)), (ux(-14.5, 14.5), uy(14.5)), (ux(-12.5, 21), uy(21))])
    # --- 먼 팔 · 먼 다리 ------------------------------------------------------
    arm("far", 1, swing[0][0])
    leg("far", 1)
    # --- 몸통 ---------------------------------------------------------------
    torso = [(-3, 27.5), (4.5, 27.5), (8, 32), (9, 38), (7.6, 45), (6, 57), (-6, 57), (-7.4, 50), (-8.8, 42), (-8.6, 35), (-6.2, 30)]
    R.poly(P("torso", ASH, 2, group="body", soft=4.0, vgrad=0.78), [(ux(dx, y), uy(y)) for dx, y in torso])
    hy = HEAD_Y + 0.5 + b + hd
    hx = 3.4 + lb * 1.1
    R.capsule(P("neck", ASH, 2, group="body", soft=1.5), [(ux(0.5, 31), uy(31)), (X(hx - 0.5), hy + 6)], [3.4, 3.0])
    # --- 머리 (앞으로 숙임) ---------------------------------------------------
    R.ellipse(P("head", ASH, 3, group="head", soft=3.2, vgrad=0.8), X(hx - 1.2), hy - 1.0, 7.2, 8.0)     # 두개
    # 옆얼굴: 이마뼈 → 콧등 → 윗입술 → 턱 → 턱각 (어둡게 그늘지되 윤곽은 뼈)
    prof = [(3.0, -1.0), (5.8, -2.0), (6.6, -0.4), (6.2, 0.8), (7.0, 3.0), (6.2, 4.2), (6.3, 5.4), (5.6, 6.2), (5.4, 8.0), (4.0, 8.9), (2.0, 8.4), (2.4, 4.0)]
    R.poly(P("face", FACE, 2, group="head", soft=1.6, rim=False, cast=False, warm=True, vgrad=0.75),
           [(X(hx + dx), hy + dy) for dx, dy in prof])
    # --- 가까운 다리 · 허리천 · 일기장 ---------------------------------------------
    leg("near", 0)
    sw = p["sway"]
    loin = [(6.6, 54), (-6.6, 54), (-7.6 + sw, 64), (-5.8 + sw, 67.5), (-2.6 + sw * 0.7, 65.5), (0.2 + sw * 0.5, 69.5), (3 + sw * 0.3, 65.5), (5.6, 68), (6.8, 62)]
    R.poly(P("loin", CLOTH, 1, soft=1.8), [(X(dx), y + b) for dx, y in loin])
    R.capsule(P("belt", CLOTH, 2, soft=0.8), [(X(-6.6), 54.6 + b), (X(6.6), 54.6 + b)], [1.3, 1.3])
    if near == "R":
        ddx = -4.2 + sw * 0.4
        R.poly(P("diary", DIARY, 2, soft=1.0), [(X(ddx), 56 + b), (X(ddx + 5.5), 55.5 + b), (X(ddx + 5.5), 62.5 + b), (X(ddx), 63 + b)])
    # --- 가까운 쪽 화살 (오른쪽을 볼 때: 오른어깨 뒤에서 위·뒤로) ---------------------
    if near == "R":
        R.capsule(P("arrow_near", CLOTH, 2, flat=True, rim=False, cast=False), [(ux(-4, 33), uy(33)), (ux(-12.5, 19), uy(19))], [0.6, 0.6])
        R.poly(P("fletch_near", ASH, 5, flat=True, rim=False, cast=False), [(ux(-12, 20), uy(20)), (ux(-15, 14.5), uy(14.5)), (ux(-13, 21), uy(21))])
    # --- 가까운 팔 · 견갑 -------------------------------------------------------
    arm("near", 0, swing[1][0])
    if near == "L":
        R.poly(P("pauldron", IRON, 2, soft=1.8), [(ux(dx, y), uy(y)) for dx, y in [(-5.5, 30.5), (3, 29.5), (7, 33), (5.6, 39.5), (-2, 40.5), (-6.5, 37)]])

    # ======================= 덧칠 =======================
    for ddx, dy in ((-3, -7), (-2, -8), (-1, -8), (-4, -6)):
        R.dot(round(X(hx)) + ddx, hy + dy, G[8])                   # 정수리 빛(화면 좌상단)
    for dx, dy, c in ((-1, -8, A[19]), (0, -7, A[21]), (0, -6, A[23]), (1, -5, A[21]), (2, -4, A[19])):
        R.dot(X(hx + dx), hy + dy, c)                               # 정수리 균열
    for dx, dy in ((3, 0), (4, 0), (5, 0), (6, -1)):
        R.dot(X(hx + dx), hy + dy, OUT)                             # 이마뼈 아래 그늘
    for dx, dy in ((3, -1), (4, -1), (5, -2), (6, -2)):
        R.dot(X(hx + dx), hy + dy, G[5])                            # 이마뼈 윗면 빛
    R.dot(X(hx + 3), hy + 6, OUT); R.dot(X(hx + 4), hy + 6, G[1])   # 입 그늘(닫힌 입)
    R.dot(X(hx + 0), hy + 2, G[2]); R.dot(X(hx - 1), hy + 3, G[2])   # 광대 아래 패임
    if near == "L":                                                 # 왼쪽을 보면 분노한 왼눈
        R.spill.append((X(hx + 4.5), hy + 1.5, 2.2))
        for dx, dy, c in ((3, 2, EYE[0]), (4, 1, EYE[2]), (5, 1, EYE[3] if p["pulse"] else EYE[2]), (6, 0, EYE[1]), (4, 2, EYE[1])):
            R.dot(X(hx + dx), hy + dy, c)
    else:                                                           # 오른쪽을 보면 꺼진 오른눈
        for dx, dy in ((4, 1), (5, 1), (4, 2), (5, 2)):
            R.dot(X(hx + dx), hy + dy, OUT)
    # 균열: 보이는 쪽만 — 가슴(앞 가장자리) 짧게, 등(뒤 가장자리) 짧게
    crack(R, [(5.6, 37), (6.6, 40), (5.2, 43)], lambda dx: ux(dx, 40), pulse=p["pulse"], thick=(0, 0), spill=0)
    # 등 균열은 측면에서 등 가장자리 불빛 2점만(선으로 그리면 몸 윤곽선처럼 읽힘)
    R.dot(round(ux(-7.2, 41)), uy(41), A[23]); R.dot(round(ux(-7.0, 42)), uy(42), A[21])
    if near == "R":
        R.dot(X(-1.5 + sw * 0.4), 59 + b, G[9])
        R.line([(X(-3), 55 + b), (X(-1.5 + sw * 0.4), 56 + b)], WD[3])
    R.dot(round(ux(-6.5, 50)), uy(50), SL[6]); R.dot(round(ux(-6.5, 50)) + f, uy(50) + 1, SL[2])   # 못머리
    # 어깨 혼불: 왼쪽을 볼 땐 가까운 어깨(전부), 오른쪽을 볼 땐 먼 어깨에서 등 위로 살짝(아래 4줄)
    fx, fy = round(ux(-4.5, 29)), round(uy(29))
    R.dot(fx, fy + 1, A[19])
    draw_flame(R, fx, fy, p["flame"], p["lean"] * f, rows=None if near == "L" else 4)   # 기울기 = 진행 반대(뒤)
    return R.render()


def draw(direction, p):
    if direction == "down":
        return draw_front(p, back=False)
    if direction == "up":
        return draw_front(p, back=True)
    return draw_side(p, 1 if direction == "right" else -1)


# =============================================================================
# 동작 — 대기 6 · 걷기 8 (52라운드 Q8)
# =============================================================================
IDLE_MS = [200, 200, 180, 220, 200, 220]
WALK_MS = [100] * 8
DIRS = ["down", "up", "left", "right"]


def act_idle(direction):
    breath = [0, 1, 2, 2, 1, 0]
    out = []
    for i in range(6):
        prev = breath[i - 1]
        kw = dict(breath=breath[i], head=-round(prev * 0.5), flame=i, lean=[0, 1, 0, -1, 0, 1][i] * 0.8,
                  pulse=1 if i in (2, 3) else 0, sway=[0, 0.4, 0.8, 0.8, 0.4, 0][i])
        if direction in ("left", "right"):
            kw.update(foot=((-3.0, 0), (3.0, 0)), hand=((-1.5, 0), (1.5, 0)), lean_body=1.0)
        out.append(pose(**kw))
    return out


def walk_phase(i):
    phL = 2 * math.pi * (i % 8) / 8.0
    return phL, phL + math.pi


def act_walk(direction):
    bobs = [round(1 - 3 * abs(math.sin(walk_phase(i)[0]))) for i in range(8)]   # 접지 +1 · 교차 -2 (3px)
    out = []
    for i in range(8):
        phL, phR = walk_phase(i)
        b, bp = bobs[i], bobs[i - 1]
        lag = walk_phase(i - 1)[0]                     # 한 박자 늦은 위상(천·혼불)
        if direction in ("down", "up"):
            liftL = round(max(0.0, -math.sin(phL)) * 4)
            liftR = round(max(0.0, -math.sin(phR)) * 4)
            stepL, stepR = 1.5 * math.cos(phL), 1.5 * math.cos(phR)
            if direction == "up":
                stepL, stepR = -stepL, -stepR
            arm = 2.0 * math.cos(phL) * (1 if direction == "down" else -1)
            out.append(pose(bob=b, head=round((bp - b) * 0.5), tilt=1.6 * math.sin(phL),
                            lift=(liftL, liftR), step=(stepL, stepR),
                            hand=((0.4 * math.sin(phL), -arm), (-0.4 * math.sin(phL), arm)),
                            sway=1.6 * math.sin(lag), flame=i % 6, lean=-1.6 * math.sin(lag), pulse=i % 4 == 0))
        else:
            A_ = 7.5
            near_ = (A_ * math.cos(phL), round(max(0.0, -math.sin(phL)) * 4.5))
            far_ = (A_ * math.cos(phR), round(max(0.0, -math.sin(phR)) * 4.5))
            out.append(pose(bob=b, head=round((bp - b) * 0.5), foot=(far_, near_),
                            hand=((-5.5 * math.cos(phR) + 1.0, 0), (-5.5 * math.cos(phL) + 1.0, 0)),
                            lean_body=1.5 + 0.5 * (b < 0),
                            sway=-1.5 - 1.3 * math.cos(2 * lag), flame=i % 6, lean=-2.0 - 0.8 * math.cos(2 * lag),
                            pulse=i % 4 == 0))
    return out


ACTIONS = {"idle": (act_idle, IDLE_MS, True), "walk": (act_walk, WALK_MS, True)}
