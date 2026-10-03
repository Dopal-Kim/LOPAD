"""주인공 v3 '혼불이 새는 재 껍데기 망령' — 96×144, 피벗 (48,138) (53라운드 Q1: 1.5배. 52라운드 Q6~Q10 디자인 유지).

개념: parts/art/work/gemini/concept_char/hero3_b.jpg (확정). 생성 이미지 픽셀은 쓰지 않는다.
골격은 '설계 좌표'(64×96 판 치수, 피벗 (32,92))로 정의하고, Rig3 가 1.5배로 변환해 다시 래스터·셰이딩한다(최근접 확대 아님).
1.5배 해상도에서 새로 그린 세부(픽셀 좌표): 얼굴(눈두덩·분노한 눈·광대·입) · 정수리 균열 · 갈비 능선 · 쇄골 ·
  갑옷 파편 리벳·긁힘·가장자리 빛 · 붕대 감긴 결 · 허리천 주름·찢김 · 일기장 걸쇠·끈·종이 단면 · 혼불 10줄 모양.
Q10 반영: 금 간 두개골(관자놀이 패임·광대 돌출·턱각·재가 부스러진 가장자리 결손),
         숙인 전투 자세(말린 어깨·앞으로 빠진 목·굽힌 팔꿈치·가슴/허리 비틀림), 걷기 무게 이동.
해부학 좌우(화면 아님):
  왼쪽  = 분노한 호박 눈빛 · 왼어깨 견갑 + 혼불 · 흉갑 조각 · 왼팔뚝 완갑 · 왼정강이 붕대 · 왼허리 칼집
  오른쪽 = 꺼진 눈 · 오른어깨 뒤 화살 · 오른정강이 정강이받이 · 오른허리 일기장
  가운데 = 가슴 균열 혼불(앞), 등 아래 균열 혼불(뒤 — 등 가운데는 상흔 자리, 53라운드 Q4), 정수리 균열
방향: down = 정면(해부 왼쪽이 화면 오른쪽) / up = 뒷면 / left·right = 측면(거울 아님, 셰이딩 재계산).
"""
import math

from PIL import Image, ImageDraw

from v3kit import Rig3, Part, G, A, SL, WD, PL, OUT, ik2, raster_path

S = 1.5                  # 53라운드 Q1 — 설계 좌표 1 = 1.5 도트
FW, FH = 96, 144
PIV = (48, 138)
DPIV = (32, 92)          # 설계 좌표 피벗(64×96 판)


def new_rig():
    return Rig3(FW, FH, S=S, src=DPIV, dst=PIV)


def to_px(p):
    """설계 좌표 → 몸 시트 도트 좌표."""
    return (PIV[0] + S * (p[0] - DPIV[0]), PIV[1] + S * (p[1] - DPIV[1]))


# ---- 팔레트 (색 예산 30, 52라운드 Q7) -------------------------------------
ASH = [G[1], G[2], G[3], G[4], G[5], G[6], G[8]]   # 재 껍데기 몸 (본색 2~3)
FACE = [G[1], G[1], G[2], G[3], G[4]]             # 그늘진 얼굴(어두운 재 — 뼈 윤곽은 읽힘)
IRON = [SL[1], SL[2], SL[4], SL[6]]                # 갑옷 파편(어두운 청회 쇠 — Q10 현행 유지)
CLOTH = [WD[1], WD[2], WD[3], WD[4]]               # 찢긴 허리천·끈·화살대
BAND = [PL[0], PL[1], PL[2]]                       # 때 묻은 붕대
DIARY = [A[17], A[18], A[19], A[21]]               # 일기장 (층 램프 21 본색 — 바이블 4절)
FIRE = {".": A[19], "r": A[21], "o": A[23], "O": A[25], "H": A[26]}
EYE = [A[21], A[23], A[25], A[26]]
LIMB_BANDS = ((0.93, 2), (0.80, 1), (0.30, 0), (0.0, -1), (-9, -2))

# 골격 상수 (숙인 전투 자세 — 엉덩이가 낮고 무릎이 굽음)
HIP_Y = 61.0
FOOT_Y = 89.0
THIGH, SHIN = 16.0, 15.6
UPPER, FORE = 13.2, 12.8
STRIDE_A = 12.0         # 측면 발 앞뒤 진폭(설계) → 한 주기 이동 = 4A = 48 설계 = 72 도트 (53라운드: 9 → 12)
CYCLE_MS = 640          # 80ms × 8 (53라운드: 800 → 640) — NOTES '보폭' 참고

# 어깨 혼불 6모양 (픽셀, 7×10 — 1.5배 해상도에서 새로 그림. 아래가 발원점, 위 끝 혼불 조각이 떨어져 나감)
FLAMES = [
    ["    .  ", "   o   ", "   oo  ", "  oOo  ", "  oOo  ", " oOHo  ", " oOHOo ", " rOHOr ", "  rOr  ", "   r   "],
    ["   .   ", "   .o  ", "    o  ", "   oO  ", "  oOo  ", "  oHOo ", " oOHOo ", " rOHOr ", "  rOr  ", "   r   "],
    [" .     ", "       ", "  .    ", "  oo   ", "  oOo  ", " oOOo  ", " oOHOo ", " rOHOr ", "  rOr  ", "   r   "],
    ["   .   ", "   o.  ", "  oO   ", "  oOo  ", " oOHo  ", " oHHOo ", " oOHOo ", " rOHOr ", "  rOr  ", "   r   "],
    ["       ", "     . ", "    o  ", "   oo  ", "  oOo  ", "  oOHo ", " oOHOo ", " rOHOr ", "  rOr  ", "   r   "],
    ["  .    ", "   o   ", "  oOo  ", "  oHo  ", " oOHo  ", " oOHOo ", " oOHOo ", " rOOOr ", "  rOr  ", "   r   "],
]

# 두개골 윤곽 (정면, 머리 중심 기준 dx, dy; dx + = 해부 왼쪽) — 관자놀이 패임 · 광대 돌출 · 턱각 · 좁은 턱
SKULL_FRONT = [(0, -10), (4, -9.6), (6.8, -7.6), (7.9, -4.4), (7.6, -1.2), (6.5, 0.8), (7.5, 3.0), (7.0, 5.2),
               (5.9, 7.2), (3.6, 9.4), (1.4, 10.2), (-1.4, 10.2), (-3.6, 9.4), (-5.9, 7.2), (-7.0, 5.2), (-7.5, 3.0),
               (-6.5, 0.8), (-7.6, -1.2), (-7.9, -4.4), (-6.8, -7.6), (-4, -9.6)]
SKULL_BACK = [(0, -10), (4.2, -9.6), (7.0, -7.4), (8.0, -4), (7.6, 0), (6.6, 3.0), (5.6, 6.2), (3.8, 8.4), (-3.8, 8.4),
              (-5.6, 6.2), (-6.6, 3.0), (-7.6, 0), (-8.0, -4), (-7.0, -7.4), (-4.2, -9.6)]
# 얼굴 그늘 (이마뼈 M자 → 광대 안쪽 → 턱)
FACE_FRONT = [(-6.4, 1.2), (-5.4, -1.4), (-2.6, -0.4), (0, 1.0), (2.6, -0.4), (5.4, -1.4), (6.4, 1.2), (6.0, 4.6),
              (4.9, 7.0), (3.0, 9.0), (-3.0, 9.0), (-4.9, 7.0), (-6.0, 4.6)]
# 옆얼굴 두개 (dx + = 앞) — 뒤통수 · 정수리 · 이마뼈 돌출 · 눈구멍 패임 · 광대 · 윗턱 · 턱 · 턱각
SKULL_SIDE = [(-3, -9.4), (1.5, -9.8), (5, -7.6), (6.6, -4.2), (7.4, -1.6), (6.4, 0.4), (7.6, 2.4), (7.2, 4.6), (6.4, 6.0),
              (6.2, 8.6), (4.4, 9.6), (1.6, 9.2), (-0.6, 7.4), (-2.6, 5.0), (-5.6, 2.6), (-7.4, -1.4), (-6.8, -5.6)]
FACE_SIDE = [(2.6, -0.6), (6.4, -1.2), (7.0, 0.4), (7.4, 2.4), (7.0, 4.6), (6.2, 6.0), (6.0, 8.4), (4.2, 9.2), (2.2, 8.6),
             (2.0, 5.0)]


def P(name, ramp, base, **kw):
    return Part(name, ramp, base, **kw)


def pose(**kw):
    p = dict(bob=0, breath=0, head=0,
             shift=0.0,                 # 정면: 상체가 디딤발 쪽으로 쏠림(dx, 해부 왼쪽 +)
             ptilt=0.0,                 # 정면: 골반 기울기(+ = 왼쪽 엉덩이 올라감)
             stilt=0.0,                 # 정면: 어깨 기울기(+ = 왼어깨 내려감)
             twist=0.0,                 # 정면: 가슴 비틀림(가슴 중심 dx)
             lift=(0, 0), step=(0.0, 0.0),
             hand=((0, 0), (0, 0)),
             sway=0.0, flame=0, lean=0.0, pulse=0,
             foot=((0.0, 0.0), (0.0, 0.0)),   # 측면: (앞뒤 x, 들림) (먼, 가까운)
             lean_body=0.0, crouch=0.0,
             # --- 2단계 확장(기본값이면 1단계와 픽셀 동일) ---
             squash=0.0,                # 상체 세로 압축(0~0.3) — 정면/뒷면에서 카메라 쪽·반대쪽으로 숙임
             hdx=0.0,                   # 머리 화면 x 이동
             handAt=None,               # {"L": (x, y), "R": (x, y)} 해부 기준 손 목표(화면 좌표, IK)
             elbow=None,                # {"L": ±1, "R": ±1} 팔꿈치 굽는 쪽(화면 x 부호)
             armBack=(),                # 정면/뒷면: 몸통 뒤에 그릴 팔("L"/"R")
             farArmFront=False,         # 측면: 먼 팔을 몸통 앞에 그림(몸 앞을 가로지를 때)
             footdx=(0.0, 0.0),         # 정면/뒷면: 발 화면 x 이동 (L, R)
             glow=0,                    # 균열 혼불 2 = 백열(피격·사망 직전)
             eyeOff=False, flameOff=False, flameRows=None)
    p.update(kw)
    if p["handAt"] is None:
        p["handAt"] = {}
    return p


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def draw_flame(R, x0, y0, variant, lean, rows=None):
    """x0, y0 = 발원점(픽셀). lean = 설계 단위 기울기(1.5배로 환산). rows = 설계 줄 수(6 기준) → 픽셀 줄 수."""
    g = FLAMES[variant % len(FLAMES)]
    if rows:
        g = g[-max(1, round(rows * len(g) / 6.0)):]
    h = len(g)
    for r, row in enumerate(g):
        k = (h - 1 - r) / max(1, h - 1)
        sx = round(lean * S * k)
        for c, ch in enumerate(row):
            if ch != " ":
                R.px(x0 + (c - 3) + sx, y0 - (h - 1 - r), FIRE[ch])


def bite(R, cx, cy, r):
    """재가 떨어져 나간 결손(설계 좌표) — 원 안 픽셀을 비운다(셀아웃이 홈 둘레를 다시 감싼다)."""
    R.hole(cx, cy, r)


def path_px(R, pts, F):
    """설계 꺾은선(F(dx, y) → 설계 화면 좌표) → 끊김 없는 픽셀 목록. 구간을 2등분해 비선형 변형(숙임·비틀림)을 따라간다."""
    q = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for t in (0.0, 0.5):
            q.append(R.T(F(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)))
    q.append(R.T(F(*pts[-1])))
    return raster_path(q)


def crack(R, pts, F, pulse=0, thick=(1, 0), spill=True, glow=0):
    """균열 혼불: 중심선(23/25/26) + 한쪽 두께(21) + 가운데 바깥 1px 잔광(19) + 경로 주변 몸 빛 번짐. glow 2 = 백열."""
    seen = path_px(R, pts, F)
    if spill:
        R.spill_cells.extend(seen)
    n = len(seen)
    if thick != (0, 0):
        for i, (x, y) in enumerate(seen):
            R.px(x + thick[0], y + thick[1], A[23] if glow >= 2 else A[21])
            if 0.3 < i / n < 0.7 and i % 2 == 0:
                R.px(x + 2 * thick[0], y + 2 * thick[1], A[21] if glow >= 2 else A[19])
    for i, (x, y) in enumerate(seen):
        mid = 0.25 < i / n < 0.75
        if glow >= 2:
            R.px(x, y, A[26] if (mid or i % 2 == 0) else A[25])
            continue
        R.px(x, y, A[26] if (mid and pulse and i % 3 == 0) else (A[25] if mid else A[23]))


def groove(R, pts, F, hi=True):
    """재 껍데기 금: 어두운 홈 G01 + 홈 아래 가장자리 빛 G05(두 칸 걸러)."""
    for k, (x, y) in enumerate(path_px(R, pts, F)):
        R.px(x, y, G[1])
        if hi and k % 3 == 0:
            R.px(x + 1, y + 1, G[5])


def fline(R, pts, cols, part=None):
    """설계 좌표 꺾은선 → 픽셀 선. cols = 색 하나 또는 목록(선을 따라 단계). part 를 주면 그 부위 위에만."""
    cells = raster_path([R.T(q) for q in pts])
    n = len(cells)
    for i, (x, y) in enumerate(cells):
        c = cols if not isinstance(cols, list) else cols[min(len(cols) - 1, int(i * len(cols) / max(1, n)))]
        R.cdot(x, y, c, part)
    return cells


def fpoly(R, pts, c, part=None):
    """설계 좌표 다각형을 픽셀로 채운 덧칠(눈두덩·결손 그늘 등)."""
    q = [R.T(p) for p in pts]
    x0, y0 = int(min(p[0] for p in q)) - 1, int(min(p[1] for p in q)) - 1
    x1, y1 = int(max(p[0] for p in q)) + 2, int(max(p[1] for p in q)) + 2
    m = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(m).polygon([(round(x - x0), round(y - y0)) for x, y in q], fill=255)
    mp = m.load()
    for y in range(y1 - y0):
        for x in range(x1 - x0):
            if mp[x, y]:
                R.cdot(x + x0, y + y0, c, part)


def wraps(R, a, b, r, n, part, col=PL[0], slant=0.9):
    """붕대 감긴 결: 축 a→b 를 따라 n 개의 비스듬한 선(부위 안에만). 설계 좌표."""
    ax, ay = a
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    ux_, uy_ = dx / L, dy / L
    nx, ny = -uy_, ux_
    for k in range(n):
        t = (k + 0.5) / n
        cx, cy = ax + dx * t, ay + dy * t
        p0 = (cx - nx * r * 1.3 - ux_ * slant, cy - ny * r * 1.3 - uy_ * slant)
        p1 = (cx + nx * r * 1.3 + ux_ * slant, cy + ny * r * 1.3 + uy_ * slant)
        fline(R, [p0, p1], col, part)


def rivet(R, x, y):
    """갑옷 리벳(설계 좌표): 빛 1 + 그늘 1."""
    p = R.T((x, y))
    R.px(p[0], p[1], SL[6])
    R.px(p[0] + 1, p[1] + 1, SL[1])


def reach(sh, tgt, frac=0.97):
    """어깨에서 닿지 않는 목표는 팔 길이 안으로 당긴다."""
    dx, dy = tgt[0] - sh[0], tgt[1] - sh[1]
    d = math.hypot(dx, dy)
    L = (UPPER + FORE) * frac
    if d <= L or d == 0:
        return tgt
    return (sh[0] + dx * L / d, sh[1] + dy * L / d)


def arm_end(el, hand, k=2.0):
    dx, dy = hand[0] - el[0], hand[1] - el[1]
    d = math.hypot(dx, dy) or 1.0
    return (hand[0] - dx * k / d, hand[1] - dy * k / d)


# =============================================================================
# 정면(down) · 뒷면(up)
# =============================================================================
def draw_front(p, back=False):
    R = new_rig()
    m = -1 if back else 1
    X = lambda dx: 32 + m * dx                   # noqa: E731
    b, br, hd = p["bob"], p["breath"], p["head"]
    sh_, pt, st, tw = p["shift"], p["ptilt"], p["stilt"], p["twist"]
    cr = p["crouch"]
    sq = p["squash"]

    # 상체 좌표: 위로 갈수록 shift·twist 가 더 걸림 (허리 0 → 가슴 1) — 비틀림
    def ux(dx, y):
        k = max(0.0, min(1.0, (HIP_Y - y) / 24.0))
        return X(dx + sh_ * (0.4 + 0.6 * k) + tw * k)

    def uy(dx, y):
        t = 0.0
        if y < 47:
            t = (st if dx > 0 else -st) * min(1.0, abs(dx) / 16.0) - br * (47 - y) / 15.0
        elif y >= 52:
            t = -(pt if dx > 0 else -pt) * min(1.0, abs(dx) / 10.0)      # 골반 기울기
        if sq and y < HIP_Y:
            y = HIP_Y - (HIP_Y - y) * (1.0 - sq)
        return y + b + cr + t

    U = lambda dx, y: (ux(dx, y), uy(dx, y))     # noqa: E731

    # --- 화살 (정면: 오른어깨 뒤에서 위·바깥으로 솟음 — 몸 뒤) -------------------
    if not back:
        R.capsule(P("arrow", CLOTH, 2, flat=True, rim=False, cast=False), [U(-11, 36), U(-19.5, 23)], [0.6, 0.6])
        R.poly(P("fletch", ASH, 5, flat=True, rim=False, cast=False), [U(-19, 24), U(-22.5, 18), U(-21, 24.5)])
    details = []        # 렌더 순서와 무관한 1.5배 세부(덧칠) — 부위 위치를 모아 두었다가 마지막에 그림
    # --- 다리 (벌린 전투 자세: 발 ±8, 무릎이 살짝 바깥으로 굽음) -------------------------
    for side, s in (("L", 1), ("R", -1)):
        li = 0 if side == "L" else 1
        hip = (X(s * 5.4 + sh_ * 0.4), HIP_Y + b + cr - s * pt)
        lift = p["lift"][li]
        fy = FOOT_Y + p["step"][li] - lift
        foot = (X(s * 8.0) + p["footdx"][li], fy)
        knee = ((hip[0] + foot[0]) / 2 + m * s * (1.4 + 0.4 * lift), (hip[1] + foot[1]) / 2 - 0.4 * lift)
        R.capsule(P("leg" + side, ASH, 2, group="leg" + side, soft=2.0, vgrad=0.82, bands=LIMB_BANDS), [hip, knee, foot], [4.4, 3.3, 2.5])
        R.ellipse(P("foot" + side, ASH, 2, group="foot" + side, soft=1.2), foot[0] + m * s * 0.6, fy + 1.6 + max(0, p["step"][li]) * 0.2, 4.3, 2.3 + max(0, p["step"][li]) * 0.2)
        if side == "R":
            a0, a1 = lerp(knee, foot, 0.22), lerp(knee, foot, 0.84)
            R.poly(P("greave", IRON, 2, soft=1.4), [(a0[0] - 3.3, a0[1] + 1), (a0[0] + 3.1, a0[1]), (a1[0] + 2.5, a1[1] - 4), (a1[0] - 0.5, a1[1] - 1.5), (a1[0] - 3.0, a1[1] - 4.5)])
            R.ellipse(P("kneecap", IRON, 2, group="greave", soft=1.0), knee[0], knee[1] - 0.5, 2.6, 2.0)
            details.append(("greave", a0, a1, knee))
        else:
            q0, q1 = lerp(knee, foot, 0.3), lerp(knee, foot, 0.86)
            R.capsule(P("shinband", BAND, 1, soft=1.0, rim=False), [q0, q1], [3.2, 2.8])
            details.append(("shinband", q0, q1, knee))
    def front_arm(side):
        s = 1 if side == "L" else -1
        li = 0 if side == "L" else 1
        shj = U(s * 14.4, 39)
        tgt = p["handAt"].get(side)
        if tgt is None:
            hdx, hdy = p["hand"][li]
            hand = (ux(s * 13.6 + s * hdx, 58), 58.5 + b + cr + hdy - br * 0.5)
            el = (ux(s * 18.4 + s * 0.3 * hdy, 50), 49.5 + b + cr + hdy * 0.4 - br * 0.5)
            end = (hand[0], hand[1] - 2.0)
        else:
            hand = reach(shj, tgt)
            bend = (p["elbow"] or {}).get(side, m * s)
            el = ik2(shj, hand, UPPER, FORE, bend)
            end = arm_end(el, hand)
        R.capsule(P("arm" + side, ASH, 2, group="arm" + side, soft=1.8, vgrad=0.85, bands=LIMB_BANDS), [shj, el, end], [3.6, 3.0, 2.5])
        if side == "L":
            R.capsule(P("vamb", IRON, 2, soft=1.0), [lerp(el, hand, 0.25), lerp(el, hand, 0.66)], [3.2, 2.9])
            details.append(("vamb", lerp(el, hand, 0.25), lerp(el, hand, 0.66), el))
        R.ellipse(P("hand" + side, BAND, 1, soft=1.0, rim=False), hand[0], hand[1] + 0.4, 2.6, 2.8)
        details.append(("hand" + side, (hand[0], hand[1] - 2.2), (hand[0], hand[1] + 2.8), el))
        R.anchors["hand" + side] = (hand[0], hand[1] + 0.4)
        R.anchors["shoulder" + side] = shj

    for side in p["armBack"]:
        front_arm(side)
    # --- 몸통: 숙여서 짧아 보이는 가슴 · 말려 올라간 승모 · 비틀린 허리 ------------------
    torso = [(-5, 31), (5, 31), (11.5, 33.5), (15.6, 38), (15.6, 43), (12.8, 48.5), (9.8, 54), (9.0, 61), (-9.0, 61),
             (-9.8, 54), (-12.8, 48.5), (-15.6, 43), (-15.6, 38), (-11.5, 33.5)]
    R.poly(P("torso", ASH, 2, group="body", soft=4.5, vgrad=0.80), [U(dx, y) for dx, y in torso])
    # --- 허리천 (찢긴 천) — 골반 기울기를 따르고, 단은 한 박자 늦게 흔들림 ----------------
    sw = p["sway"]
    hem = [(10, 62), (9 + sw, 68.5), (6.5 + sw * 1.1, 66), (4.5 + sw * 1.2, 72), (1.5 + sw * 1.3, 67.5), (-1.5 + sw * 1.3, 71.5),
           (-4 + sw * 1.2, 66.5), (-6.5 + sw * 1.1, 70.5), (-9 + sw, 66.5), (-10, 62)]
    R.poly(P("loin", CLOTH, 0, soft=1.8), [U(-10, 57), U(10, 57)] + [(ux(dx, 57), uy(dx, 57) + (y - 57)) for dx, y in hem])
    details.append(("loin", [(ux(dx, 57), uy(dx, 57) + (y - 57)) for dx, y in hem], U(0, 57.5), None))
    R.capsule(P("belt", CLOTH, 2, soft=0.8), [U(-9.8, 57.6), U(9.8, 57.6)], [1.2, 1.2])
    # --- 일기장 (오른허리) — 천보다 반 박자 늦게 흔들림 -------------------------------------
    dx0 = -14.6 - 0.6 * sw
    d0 = U(dx0, 59)
    R.poly(P("diary", DIARY, 1, soft=1.0), [d0, (d0[0] + m * 4.5, d0[1] - 0.4), (d0[0] + m * 4.5, d0[1] + 5.6), (d0[0], d0[1] + 6)])
    # --- 흉갑 조각(앞) / 등 끈(뒤) -----------------------------------------------
    if not back:
        R.poly(P("plate", IRON, 2, soft=1.8), [U(dx, y) for dx, y in [(2, 38), (12.5, 36), (14.5, 42.5), (10.5, 49.5), (3, 47.5)]])
        R.capsule(P("strap", CLOTH, 1, soft=0.8, rim=False), [U(-12.5, 34.5), U(3, 43)], [1.1, 1.1])
    else:
        R.capsule(P("strap", CLOTH, 1, soft=0.8, rim=False), [U(13, 34.5), U(-8.5, 55)], [1.2, 1.2])
    # --- 팔: 굽힌 팔꿈치, 주먹은 앞·안쪽(전투 준비) ------------------------------------
    for side in ("L", "R"):
        if side not in p["armBack"]:
            front_arm(side)
    # --- 머리: 숙여서 어깨 사이로 내려온 금 간 두개골 ------------------------------------
    hx = ux(0, 30) + p["hdx"]
    hy = (22.5 if not sq else HIP_Y - (HIP_Y - 22.5) * (1.0 - sq)) + b + cr + hd - br * 0.6
    R.anchors.update(head=(hx, hy), chest=U(0, 45), hipL=U(10.5, 58.5), hipR=U(-10.5, 58.5))
    R.scar = scar_rect(U, SCAR_BACK, back)
    if not back:
        R.poly(P("head", ASH, 4, group="head", soft=2.6, vgrad=0.80), [(hx + m * dx, hy + dy) for dx, dy in SKULL_FRONT])
        R.poly(P("face", FACE, 3, group="head", soft=1.4, rim=False, cast=False, warm=True, vgrad=0.8),
               [(hx + m * dx, hy + dy) for dx, dy in FACE_FRONT])
    else:
        R.poly(P("head", ASH, 4, group="head", soft=2.6, vgrad=0.80), [(hx + m * dx, hy + dy) for dx, dy in SKULL_BACK])
    # 재가 부스러진 가장자리 결손 (해부 기준 위치 → 방향 따라 좌우 바뀜)
    bite(R, hx + m * 4.4, hy - 10.2, 1.7)        # 재가 떨어져 나간 결손: 정수리 균열 옆 얕은 홈(1.5배에서 뿔처럼 보이지 않게 얕게)
    bite(R, hx + m * 8.4, hy - 4.4, 1.8)          # 해부 왼쪽 옆머리 홈
    bite(R, hx - m * 8.4, hy - 2.6, 1.2)          # 관자놀이
    bite(R, hx - m * 6.8, hy + 7.0, 1.1)          # 턱각
    # --- 견갑 (왼어깨) ------------------------------------------------------
    pd = [U(dx, y) for dx, y in [(7.5, 32.5), (14, 32.5), (19, 36.5), (18.6, 42), (12.5, 41.6), (8, 37.5)]]
    R.poly(P("pauldron", IRON, 2, soft=1.8), pd)
    # --- 뒷면 화살 -------------------------------------------------------------
    if back:
        for (bx, by), (tx, ty), fl in (((-8, 41), (-16, 27), -1), ((9, 49), (16, 37), 1)):
            R.capsule(P("arrowb", CLOTH, 2, flat=True, rim=False, cast=False), [U(bx, by), U(tx, ty)], [0.6, 0.6])
            t0 = U(tx, ty)
            R.poly(P("fletchb", ASH, 5, flat=True, rim=False, cast=False), [t0, (t0[0] + m * fl * 2.5, t0[1] - 4.5), (t0[0] - m * fl * 1.0, t0[1] - 0.5)])

    # ======================= 덧칠 (1.5배 해상도 세부) =======================
    HF = lambda dx, dy: (hx + m * dx, hy + dy)   # noqa: E731
    HFs = lambda pts: [HF(dx, dy) for dx, dy in pts]   # noqa: E731
    # 정수리 빛(화면 좌상단, 방향 무관 → 화면 좌표로 고정)
    fpoly(R, [(hx - 5.6, hy - 6.0), (hx - 4.6, hy - 8.2), (hx - 2.6, hy - 9.5), (hx - 0.8, hy - 9.4), (hx - 2.4, hy - 8.0), (hx - 4.2, hy - 6.4)], G[8], "head")
    fline(R, [(hx - 6.6, hy - 3.0), (hx - 6.0, hy - 5.6)], G[6], "head")
    # 정수리 균열 혼불(해부 왼쪽) — 정수리 → 이마 → 분노한 눈두덩
    crown = HFs([(1.5, -9.6), (2.4, -8.0), (2.6, -6.8), (3.6, -5.8), (4.6, -4.8), (5.0, -3.6), (5.4, -2.4), (5.0, -1.4)])
    fline(R, [(q[0] + m * 0.7, q[1]) for q in crown[:6]], A[18], "head")       # 균열 옆 데워진 재
    fline(R, crown, [A[21], A[23], A[25], A[26] if p["pulse"] else A[25], A[25], A[23], A[21], A[19]])
    fline(R, HFs([(3.6, -5.8), (2.2, -4.6)]), A[21], "head")                     # 잔가지
    groove(R, [(-2, -9.5), (-3.5, -7), (-3, -5)], HF, hi=not back)
    groove(R, [(-7.2, -0.6), (-6.2, 1.6)], HF, hi=False)                          # 관자놀이 실금
    if not back:
        fline(R, [(hx - 6, hy - 0.2), (hx - 6, hy + 1.6)], G[2], "face")            # 관자놀이 패임
        fline(R, [(hx + 6, hy - 0.2), (hx + 6, hy + 1.6)], G[2], "face")
        fline(R, HFs([(-5.6, -2.2), (-4, -2.0), (-2.6, -1.0), (-1, -0.2), (1, -0.2), (2.6, -1.0), (4, -2.0), (5.6, -2.2)]), G[5])   # 이마뼈 윗면
        # 눈두덩 두 패임(콧등으로 갈라짐) — 분노한 쪽은 안쪽이 눌려 내려온 모양
        fpoly(R, HFs([(1.4, 1.4), (3.6, -0.6), (6.6, -1.0), (6.9, 1.2), (5.6, 2.9), (3.4, 3.7), (1.6, 3.3)]), OUT)
        fpoly(R, HFs([(-1.4, 1.2), (-3.8, -0.4), (-6.6, -0.2), (-6.9, 2.4), (-5.0, 3.6), (-2.4, 3.7)]), OUT)
        fline(R, HFs([(-5.2, 2.2), (-4.0, 2.4)]), G[1])                            # 꺼진 눈: 재 덮인 어둠 속 희미한 결
        fline(R, HFs([(0, 1.2), (0, 3.0)]), G[3], "face")                          # 콧등
        fline(R, HFs([(0, 3.6), (0, 4.8)]), G[2], "face")
        fline(R, HFs([(-0.6, 5.6), (1.0, 5.6)]), G[1], "face")                     # 코 밑 그늘
        fline(R, HFs([(-6.4, 4.0), (-4.2, 4.2)]), G[4], "face")                    # 광대(해부 오른쪽)
        fline(R, HFs([(4.4, 4.2), (6.2, 4.0)]), G[3], "face")
        fline(R, [(hx - 6.2, hy + 4.0), (hx - 5.4, hy + 3.4)], G[5], "face")        # 빛 쪽 광대 끝
        fline(R, HFs([(-4.8, 6.2), (-3.6, 7.4)]), G[1], "face")                    # 광대 아래 패임
        fline(R, HFs([(4.8, 6.2), (3.6, 7.4)]), G[1], "face")
        fline(R, HFs([(-2.4, 8.4), (2.4, 8.4)]), G[1], "face")                     # 닫힌 입
        fline(R, HFs([(-0.8, 8.4), (0.8, 8.4)]), OUT, "face")
        fline(R, [(hx - 3, hy + 9.7), (hx - 0.4, hy + 9.7)], G[3], "face")          # 턱 끝 윗면
        fline(R, [(hx + 0.4, hy + 9.7), (hx + 2, hy + 9.7)], G[2], "face")
        if not p["eyeOff"]:
            q = R.T(HF(4.2, 1.6))
            R.spill.append((q[0], q[1], 3.6))
            # 분노한 왼눈: 안쪽이 낮고 바깥이 치켜 올라간 가는 눈빛 + 아래 두께
            fline(R, HFs([(2.3, 2.5), (3.6, 1.8), (5.0, 1.0), (6.2, 0.2)]),
                  [EYE[0], EYE[1], EYE[2], EYE[3] if p["pulse"] else EYE[2], EYE[2], EYE[1]])
            fline(R, HFs([(3.0, 2.6), (4.6, 1.9)]), [EYE[0], EYE[1], EYE[2]])
            q = R.T(HF(5.0, 1.0))
            R.px(q[0], q[1] - 1, EYE[1])                                            # 위로 새는 눈빛 1px
        # 가슴 균열 · 갈비 · 쇄골 · 껍데기 금
        crack(R, [(-3, 37.5), (-1, 40.5), (-4.5, 43.5), (-1.5, 46.5), (-3.5, 50), (-1, 53)], U, pulse=p["pulse"], thick=(m, 0), glow=p["glow"])
        crack(R, [(-1, 40.5), (2.5, 41.5)], U, thick=(0, 1), spill=False, glow=p["glow"])
        crack(R, [(-3.5, 50), (-6.5, 51.5)], U, thick=(0, 0), spill=False, glow=p["glow"])     # (1.5배 세부) 아래 잔가지
        for y in (44.6, 47.6, 50.6):                                               # 갈비 능선(해부 오른쪽 — 빛 위, 그늘 아래)
            fline(R, [U(-12.2, y - 0.8), U(-10, y), U(-7.6, y + 0.5)], G[4], "torso")
            fline(R, [U(-12.0, y + 0.3), U(-9.8, y + 1.1), U(-7.6, y + 1.5)], G[1], "torso")
        for y in (51.0, 54.0):
            fline(R, [U(7.6, y), U(9.8, y + 0.4)], G[2], "torso")
        for s_ in (1, -1):                                                         # 쇄골
            if s_ == -1:
                fline(R, [U(-3.5, 34.0), U(-7, 34.6), U(-10, 34.2)], G[1], "torso")
                fline(R, [U(-4.0, 33.4), U(-8.5, 33.6)], G[5], "torso")
        groove(R, [(-15, 40), (-13, 42.5), (-14, 45.5), (-12.5, 48)], U)
        groove(R, [(6, 51), (7.5, 53.5), (6.5, 56)], U, hi=False)
        groove(R, [(-6, 52.5), (-8, 55.5)], U, hi=False)
        # 흉갑 조각: 리벳 · 긁힘 · 위 가장자리 빛
        for dx, y in ((4.0, 39.2), (11.6, 37.4), (6.0, 46.4)):
            rivet(R, *U(dx, y))
        fline(R, [U(3, 38.2), U(12, 36.4)], SL[6], "plate")
        fline(R, [U(7, 41), U(10.5, 45.5)], SL[1], "plate")
        fline(R, [U(5, 43), U(6.5, 44.5)], SL[1], "plate")
        rivet(R, *U(16.5, 55))
    else:
        # 등: 가운데(상흔 자리)는 비우고, 균열 혼불은 허리 쪽으로 내려 짧게(53라운드 Q4)
        crack(R, [(1.5, 48), (-1, 51), (1.5, 54), (0, 57)], U, pulse=p["pulse"], thick=(m, 0), glow=p["glow"])
        crack(R, [(1.5, 54), (5.5, 52.5)], U, thick=(0, 1), spill=False, glow=p["glow"])
        for s_ in (1, -1):                                                         # 견갑골 능선
            fline(R, [U(s_ * 5.5, 38.5), U(s_ * 9.5, 41.5), U(s_ * 11, 45)], G[1], "torso")
            fline(R, [U(s_ * 5.0, 37.6), U(s_ * 9.0, 40.4)], G[5], "torso")
        fline(R, [U(0, 35.5), U(0.5, 39), U(0, 43), U(0.4, 46)], G[2], "torso")    # 등뼈 골
        groove(R, [(-14, 46), (-12, 48.5), (-12.5, 51)], U)
        groove(R, [(11.5, 40), (13.5, 43), (12.5, 45)], U, hi=False)
        for dx, y in ((-4, 35), (6, 38), (-11, 47)):
            q = R.T(U(dx, y))
            R.px(q[0], q[1], SL[6]); R.px(q[0] + 1, q[1] + 1, SL[2])
    # 견갑: 리벳 · 위 가장자리 빛 · 찌그러진 금
    rivet(R, *U(10.0, 34.6))
    rivet(R, *U(16.0, 37.2))
    fline(R, [U(8.5, 33.4), U(13.5, 33.4), U(17.5, 36.4)], SL[6] if not back else SL[4], "pauldron")
    fline(R, [U(13, 38), U(15.5, 40.5)], SL[1], "pauldron")
    # 1.5배 세부: 정강이받이 리벳·능선 / 붕대 결 / 완갑 끈 / 허리천 주름
    for kind, a0, a1, kn in details:
        if kind == "greave":
            rivet(R, a0[0] + 1.6, a0[1] + 1.2)
            rivet(R, a0[0] - 1.8, a0[1] + 1.6)
            fline(R, [lerp(a0, a1, 0.15), lerp(a0, a1, 0.8)], SL[6], "greave")
        elif kind == "shinband":
            wraps(R, a0, a1, 3.0, 4, "shinband")
        elif kind == "vamb":
            wraps(R, a0, a1, 3.0, 2, "vamb", col=WD[2], slant=0.5)
        elif kind.startswith("hand"):
            wraps(R, a0, a1, 2.6, 2, kind, slant=0.6)
        elif kind == "loin":
            top = a1
            for j in (1, 3, 5, 7):
                fline(R, [(top[0] + (a0[j][0] - top[0]) * 0.25, top[1] + 1.2), a0[j]], WD[1], "loin")
            q = R.T(a0[4])
            R.px(q[0], q[1] - 3, OUT); R.px(q[0] + 1, q[1] - 3, OUT); R.px(q[0], q[1] - 4, WD[3])   # 찢긴 구멍
    # 일기장: 표지 테 · 종이 단면 · 걸쇠 · 끈 · 그을린 모서리
    dw = m * 4.5
    fline(R, [(d0[0] + dw, d0[1] + 0.2), (d0[0] + dw, d0[1] + 5.4)], PL[2], "diary")
    fline(R, [(d0[0] + 0.4, d0[1] + 5.4), (d0[0] + dw - m * 0.4, d0[1] + 5.2)], PL[1], "diary")
    fline(R, [(d0[0] + m * 0.6, d0[1] + 0.6), (d0[0] + dw - m * 0.6, d0[1] + 0.4)], DIARY[2], "diary")
    q = R.T((d0[0] + m * 2.25, d0[1] + 2.5))
    R.px(q[0], q[1], G[9]); R.px(q[0] + 1, q[1], G[7]); R.px(q[0], q[1] + 1, G[6])
    R.line([U(-10, 58), (d0[0] + m * 2.25, d0[1])], WD[3])
    q = R.T((d0[0], d0[1] + 6))
    R.px(q[0], q[1] - 1, A[19])
    kn = R.T(U(-2, 58.5))                                                        # 허리끈 매듭 + 늘어진 끝
    for dx, dy, c in ((0, 1, WD[4]), (1, 1, WD[4]), (1, 2, WD[3]), (0, 3, WD[3]), (2, 3, WD[3]), (0, 4, WD[2]), (2, 5, WD[2])):
        R.px(kn[0] + dx, kn[1] + dy, c)
    # 어깨 혼불 (해부 왼어깨 위)
    fx, fy = ux(13, 32), uy(13, 32)
    R.anchors["flame"] = (fx, fy)
    if not p["flameOff"]:
        q = R.T((fx, fy))
        R.px(q[0], q[1] + 1, A[19]); R.px(q[0] - 1, q[1] + 1, A[19])
        draw_flame(R, round(q[0]), round(q[1]), p["flame"], p["lean"], rows=p["flameRows"])
    return R


# =============================================================================
# 측면 (left / right)
# =============================================================================
def draw_side(p, facing):
    """facing = +1 오른쪽, -1 왼쪽. dx 는 '앞' 이 + 인 몸 좌표. 상체는 앞으로 숙이고 머리는 앞으로 빠진다."""
    R = new_rig()
    f = facing
    details = []
    X = lambda dx: 32 + f * dx                   # noqa: E731
    near = "R" if f == 1 else "L"
    b, br, hd, lb, cr = p["bob"], p["breath"], p["head"], p["lean_body"], p["crouch"]

    def ux(dx, y):                               # 숙임: 위로 갈수록 앞으로 (lean_body 가 클수록 더)
        k = max(0.0, (HIP_Y - y)) / 26.0
        return X(dx + lb * k * 3.0 + (br * 0.35 if dx > 0 and y < 48 else 0))

    def uy(dx, y):
        return y + b + cr - (br * (48 - y) / 15.0 if y < 48 else 0)

    U = lambda dx, y: (ux(dx, y), uy(dx, y))     # noqa: E731

    def anat(which):
        return near if which == "near" else ("L" if near == "R" else "R")

    def leg(which, shade):
        fxp, lift = p["foot"][0 if which == "far" else 1]
        hip = (X(-1.0), HIP_Y + b + cr)
        foot = (X(fxp), FOOT_Y - lift)
        knee = ik2(hip, foot, THIGH, SHIN, f)
        name = "leg_" + which
        R.capsule(P(name, ASH, 2 - shade, group=name, soft=2.0, vgrad=0.82, bands=LIMB_BANDS), [hip, knee, foot], [4.4, 3.3, 2.5])
        fy = 92 - lift
        R.poly(P("foot_" + which, ASH, 2 - shade, group="foot_" + which, soft=1.2),
               [(X(fxp - 3), fy - 3.6), (X(fxp + 2), fy - 3.6), (X(fxp + 6), fy - 1.4), (X(fxp + 6), fy), (X(fxp - 3.4), fy)])
        if anat(which) == "R":
            R.capsule(P("greave_" + which, IRON, 2 - shade, soft=1.3), [lerp(knee, foot, 0.22), lerp(knee, foot, 0.70)], [3.3, 2.8])
            details.append(("greave_" + which, lerp(knee, foot, 0.22), lerp(knee, foot, 0.70)))
        else:
            R.capsule(P("band_" + which, BAND, 1 - shade, soft=1.0, rim=False), [lerp(knee, foot, 0.3), lerp(knee, foot, 0.86)], [3.1, 2.7])
            details.append(("band_" + which, lerp(knee, foot, 0.3), lerp(knee, foot, 0.86)))

    def arm(which, shade, swing, dy=0.0):
        shj = U(3.0, 39)
        side = anat(which)
        tgt = p["handAt"].get(side)
        if tgt is None:
            hand = (X(8.5 + swing + lb * 2.0), 56.5 + b + cr - br * 0.5 - abs(swing) * 0.15 + dy)
            el = ik2(shj, hand, UPPER, FORE, (p["elbow"] or {}).get(side, -f))
            end = (hand[0] - f * 1.2, hand[1] - 1.6)
        else:
            hand = reach(shj, tgt)
            el = ik2(shj, hand, UPPER, FORE, (p["elbow"] or {}).get(side, -f))
            end = arm_end(el, hand)
        name = "arm_" + which
        R.capsule(P(name, ASH, 2 - shade, group=name, soft=1.8, vgrad=0.85, bands=LIMB_BANDS), [shj, el, end], [3.4, 2.9, 2.4])
        if side == "L":
            R.capsule(P("vamb_" + which, IRON, 2 - shade, soft=1.0), [lerp(el, hand, 0.25), lerp(el, hand, 0.66)], [3.1, 2.8])
            details.append(("vamb_" + which, lerp(el, hand, 0.25), lerp(el, hand, 0.66)))
        R.ellipse(P("hand_" + which, BAND, 1 - shade, soft=1.0, rim=False), hand[0], hand[1] + 0.2, 2.7, 2.7)
        details.append(("hand_" + which, (hand[0] - 2.0, hand[1] - 1.0), (hand[0] + 2.0, hand[1] + 1.6)))
        R.anchors["hand" + side] = (hand[0], hand[1] + 0.2)
        R.anchors["shoulder" + side] = shj

    swing = p["hand"]
    if near == "L":                                                          # 먼 쪽(오른어깨) 화살이 굽은 등 위로
        R.capsule(P("arrow_far", CLOTH, 1, flat=True, rim=False, cast=False), [U(-3.5, 37), U(-12, 24)], [0.6, 0.6])
        R.poly(P("fletch_far", ASH, 4, flat=True, rim=False, cast=False), [U(-11.5, 25), U(-14.5, 19.5), U(-12.5, 26)])
    if not p["farArmFront"]:
        arm("far", 1, swing[0][0], swing[0][1])
    leg("far", 1)
    # --- 몸통: 굽은 등(혹처럼 둥근 견갑 사이), 앞으로 말린 가슴 -------------------------
    torso = [(-7.2, 61), (-7.8, 54), (-6.6, 47), (-4.6, 41), (-2.2, 36.5), (1.5, 33.5), (6.0, 33.0), (9.6, 36.5), (10.4, 42),
             (8.6, 48), (6.4, 54), (5.6, 61)]
    R.poly(P("torso", ASH, 2, group="body", soft=4.0, vgrad=0.80), [U(dx, y) for dx, y in torso])
    hy = 24.0 + b + cr + hd - br * 0.5
    hx = 7.0 + lb * 2.2 + p["hdx"]
    R.anchors.update(head=(X(hx), hy), chest=U(2, 45), hipL=(X(0.5), 58.5 + b + cr), hipR=(X(0.5), 58.5 + b + cr))
    R.scar = scar_rect(U, SCAR_SIDE, True)
    R.capsule(P("neck", ASH, 2, group="body", soft=1.5), [U(3.5, 35), (X(hx - 2.5), hy + 5.5)], [3.4, 3.0])
    # --- 머리: 앞으로 빠진 금 간 두개(옆얼굴) ---------------------------------------------
    R.poly(P("head", ASH, 4, group="head", soft=2.6, vgrad=0.80), [(X(hx + dx), hy + dy) for dx, dy in SKULL_SIDE])
    R.poly(P("face", FACE, 3, group="head", soft=1.4, rim=False, cast=False, warm=True, vgrad=0.8), [(X(hx + dx), hy + dy) for dx, dy in FACE_SIDE])
    bite(R, X(hx + 2.2), hy - 10.2, 1.7)
    bite(R, X(hx - 7.2), hy - 3.2, 2.0)
    bite(R, X(hx + 6.0), hy + 9.0, 1.1)
    # --- 가까운 다리 · 허리천 · 일기장 ---------------------------------------------
    leg("near", 0)
    sw = p["sway"]
    loin = [(6.6, 57), (-7.4, 57), (-8.6 + sw, 66), (-7.0 + sw * 1.2, 70), (-3.6 + sw * 1.1, 68), (-0.4 + sw * 0.9, 72.5),
            (2.6 + sw * 0.6, 68.5), (5.4 + sw * 0.3, 71), (7.0, 65)]
    R.poly(P("loin", CLOTH, 0, soft=1.8), [(X(dx), y + b + cr) for dx, y in loin])
    details.append(("loin", [(X(dx), y + b + cr) for dx, y in loin], None))
    R.capsule(P("belt", CLOTH, 2, soft=0.8), [(X(-7.4), 57.6 + b + cr), (X(6.6), 57.6 + b + cr)], [1.3, 1.3])
    if near == "R":
        ddx = -4.4 + sw * 0.6
        dy0 = 59 + b + cr
        R.poly(P("diary", DIARY, 1, soft=1.0), [(X(ddx), dy0), (X(ddx + 4.5), dy0 - 0.4), (X(ddx + 4.5), dy0 + 5.6), (X(ddx), dy0 + 6)])
        R.capsule(P("arrow_near", CLOTH, 2, flat=True, rim=False, cast=False), [U(-3.5, 37), U(-12.5, 24)], [0.6, 0.6])
        R.poly(P("fletch_near", ASH, 5, flat=True, rim=False, cast=False), [U(-12, 25), U(-15, 19.5), U(-13, 26)])
    if p["farArmFront"]:
        arm("far", 1, swing[0][0], swing[0][1])
    arm("near", 0, swing[1][0], swing[1][1])
    if near == "L":
        R.poly(P("pauldron", IRON, 2, soft=1.8), [U(dx, y) for dx, y in [(-3.5, 34.5), (4.5, 33.5), (8.5, 37), (7.0, 43), (0, 44), (-4.5, 40)]])
        details.append(("pauldron", None, None))

    # ======================= 덧칠 (1.5배 해상도 세부) =======================
    HF = lambda dx, dy: (X(hx + dx), hy + dy)    # noqa: E731
    HFs = lambda pts: [HF(dx, dy) for dx, dy in pts]   # noqa: E731
    X0 = X(hx)
    fpoly(R, [(X0 - 4.6, hy - 6.4), (X0 - 3.6, hy - 8.4), (X0 - 1.6, hy - 9.6), (X0 - 0.2, hy - 9.4), (X0 - 1.8, hy - 8.0), (X0 - 3.4, hy - 6.6)], G[8], "head")
    crown = HFs([(-1, -9.6), (0, -8.2), (0.2, -7.0), (1.2, -6.0), (2.0, -4.8), (2.8, -3.8), (3.2, -2.6), (3.0, -1.4)])
    fline(R, [(q[0] + f * 0.7, q[1]) for q in crown[:6]], A[18], "head")
    fline(R, crown, [A[21], A[23], A[25], A[26] if p["pulse"] else A[25], A[25], A[23], A[21], A[19]])
    fline(R, HFs([(1.2, -6.0), (-0.6, -5.0)]), A[21], "head")
    groove(R, [(-4, -6), (-5.5, -3), (-5, 0)], HF)
    groove(R, [(-6.4, 2.0), (-4.6, 4.6)], HF, hi=False)                             # 뒤통수 아래 실금
    fline(R, HFs([(1.8, -0.6), (1.6, 1.0)]), G[2], "head")                         # 관자놀이 패임
    fline(R, HFs([(2.8, -1.4), (4.2, -1.4), (6.2, -2.4)]), G[5])                   # 이마뼈 윗면 빛
    fpoly(R, HFs([(2.8, -0.4), (6.6, -1.6), (6.8, 0.6), (5.8, 2.8), (3.6, 3.0), (2.6, 1.6)]), OUT)   # 눈두덩 그늘
    fline(R, HFs([(3.4, 3.8), (4.6, 3.4), (5.8, 3.4), (6.8, 2.8)]), [G[3], G[4], G[4], G[3]], "face")   # 광대 돌출 윗면 빛
    fline(R, HFs([(7.0, 0.8), (7.2, 2.4)]), G[3], "face")                          # 콧등
    fline(R, HFs([(2.4, 8.4), (4.6, 9.0)]), G[3], "face")                          # 턱선 빛
    fline(R, HFs([(3.0, 5.0), (4.2, 5.6)]), G[1], "face")                          # 광대 아래 패임
    fline(R, HFs([(4.0, 6.6), (5.6, 6.4)]), [OUT, OUT, G[1]], "face")              # 닫힌 입
    if near == "L" and not p["eyeOff"]:
        q = R.T(HF(4.6, 1.4))
        R.spill.append((q[0], q[1], 3.3))
        fline(R, HFs([(3.0, 2.4), (4.2, 1.6), (5.2, 0.9), (6.2, 0.1)]),
              [EYE[0], EYE[1], EYE[2], EYE[3] if p["pulse"] else EYE[2], EYE[2], EYE[1]])
        fline(R, HFs([(3.6, 2.6), (4.8, 1.8)]), [EYE[0], EYE[1]])
    else:
        fline(R, HFs([(4.0, 1.6), (5.4, 1.2)]), G[1])                               # 꺼진 눈: 어둠 속 결
    crack(R, [(7.2, 39), (8.6, 42), (7.0, 45), (7.6, 47)], U, pulse=p["pulse"], thick=(0, 0), spill=False, glow=p["glow"])
    fline(R, [U(7.6, 40.4), U(6.2, 41.2)], A[21])                                    # 가슴 균열 잔가지
    for y in (43.0, 46.0):                                                           # 옆구리 갈비 능선
        fline(R, [U(-1.5, y), U(2.5, y + 0.8), U(5.0, y + 0.6)], G[4], "torso")
        fline(R, [U(-1.3, y + 1.1), U(2.6, y + 1.9)], G[1], "torso")
    e1 = R.T(U(-6.2, 49))
    R.px(e1[0], e1[1], A[25] if p["glow"] >= 2 else A[23]); R.px(e1[0], e1[1] + 1, A[21]); R.px(e1[0], e1[1] + 2, A[19])   # 등 아래 균열 불빛(가장자리)
    groove(R, [(-3.5, 40), (-5, 44), (-4, 48)], U, hi=False)
    fline(R, [U(-2.4, 37.0), U(-5.0, 40.0)], G[5], "torso")                         # 굽은 등 견갑 능선 빛
    nh = R.T(U(-6.4, 52))
    R.px(nh[0], nh[1], SL[6]); R.px(nh[0] + f, nh[1] + 1, SL[2])
    for kind, a0, a1 in details:
        if kind.startswith("greave"):
            rivet(R, a0[0], a0[1] + 0.8)
            fline(R, [lerp(a0, a1, 0.1), lerp(a0, a1, 0.85)], SL[6] if kind.endswith("near") else SL[4], kind)
        elif kind.startswith("band"):
            wraps(R, a0, a1, 2.9, 4, kind)
        elif kind.startswith("vamb"):
            wraps(R, a0, a1, 2.9, 2, kind, col=WD[2], slant=0.5)
        elif kind.startswith("hand"):
            wraps(R, a0, a1, 2.4, 2, kind, slant=0.5)
        elif kind == "loin":
            top = a0[0]
            for j in (3, 5, 7):
                fline(R, [(a0[j][0] + (top[0] - a0[j][0]) * 0.1, top[1] + 1.5), a0[j]], WD[1], "loin")
        elif kind == "pauldron":
            rivet(R, *U(0.5, 36.0))
            rivet(R, *U(5.5, 37.6))
            fline(R, [U(-3, 34.2), U(4.5, 33.6), U(8, 36.6)], SL[6], "pauldron")
            fline(R, [U(2, 39), U(4.5, 41.5)], SL[1], "pauldron")
    if near == "R":
        ddx = -4.4 + sw * 0.6
        d0 = (X(ddx), 59 + b + cr)
        dw = f * 4.5
        fline(R, [(d0[0] + dw, d0[1] + 0.2), (d0[0] + dw, d0[1] + 5.4)], PL[2], "diary")
        fline(R, [(d0[0] + 0.4 * f, d0[1] + 5.4), (d0[0] + dw - f * 0.4, d0[1] + 5.2)], PL[1], "diary")
        fline(R, [(d0[0] + f * 0.6, d0[1] + 0.6), (d0[0] + dw - f * 0.6, d0[1] + 0.4)], DIARY[2], "diary")
        q = R.T((X(ddx + 2.25), 61.5 + b + cr))
        R.px(q[0], q[1], G[9]); R.px(q[0] + 1, q[1], G[7]); R.px(q[0], q[1] + 1, G[6])
    fx, fy = ux(-2.5, 33), uy(-2.5, 33)
    R.anchors["flame"] = (fx, fy)
    if not p["flameOff"]:
        q = R.T((fx, fy))
        R.px(q[0], q[1] + 1, A[19])
        rows = None if near == "L" else 4
        if p["flameRows"] is not None:
            rows = min(rows or 6, p["flameRows"])
        draw_flame(R, round(q[0]), round(q[1]), p["flame"], p["lean"] * f, rows=rows)
    return R


# 등 상흔 기준점 (53라운드 Q4, 계약 §13) — 설계 좌표 네 모서리 → 도트 좌표 {x, y(중심), w, h, rot, visible}
SCAR_BACK = (-8.5, 8.5, 36.5, 49.5)     # 뒷모습: 등 가운데(견갑골 사이 ~ 허리 위). 등 균열 혼불은 이 아래로 내림
SCAR_SIDE = (-6.8, -2.0, 40.5, 48.0)    # 측면: 굽은 등 어깨 아래 작은 사각형(견갑 갑옷 아래 — 갑옷 위에 상흔이 얹히지 않게)


def scar_rect(U, box, visible):
    x0, x1, y0, y1 = box
    tl, tr, bl, br = (to_px(U(x0, y0)), to_px(U(x1, y0)), to_px(U(x0, y1)), to_px(U(x1, y1)))
    tc, bc = ((tl[0] + tr[0]) / 2, (tl[1] + tr[1]) / 2), ((bl[0] + br[0]) / 2, (bl[1] + br[1]) / 2)
    w = (math.hypot(tr[0] - tl[0], tr[1] - tl[1]) + math.hypot(br[0] - bl[0], br[1] - bl[1])) / 2
    h = math.hypot(tc[0] - bc[0], tc[1] - bc[1])
    rot = math.degrees(math.atan2(tc[0] - bc[0], bc[1] - tc[1]))       # 위쪽 변이 오른쪽으로 기울면 +(시계 방향)
    return {"x": round((tc[0] + bc[0]) / 2, 1), "y": round((tc[1] + bc[1]) / 2, 1), "w": round(abs(w), 1), "h": round(h, 1),
            "rot": round(rot, 1), "visible": visible}


def build(direction, p):
    """부위·덧칠·기준점까지 만든 Rig3(렌더 전). 2단계는 기준점을 먼저 읽고 손 목표를 정한 뒤 다시 만든다."""
    if direction == "down":
        return draw_front(p, back=False)
    if direction == "up":
        return draw_front(p, back=True)
    return draw_side(p, 1 if direction == "right" else -1)


def draw_rig(direction, p):
    R = build(direction, p)
    R.render()
    return R


def draw(direction, p):
    return draw_rig(direction, p).image


# =============================================================================
# 동작 — 대기 6 · 걷기 8 (52라운드 Q8·Q10)
# =============================================================================
IDLE_MS = [200, 200, 180, 220, 200, 220]
WALK_MS = [CYCLE_MS // 8] * 8
DIRS = ["down", "up", "left", "right"]


def act_idle(direction):
    """전투 대기: 숨(가슴·어깨 0→2px) + 머리 한 박자 늦음 + 무게가 살짝 오가는 흔들림 + 혼불 깜빡임."""
    breath = [0, 1, 2, 2, 1, 0]
    rock = [0.0, 0.4, 0.8, 0.6, 0.0, -0.4]
    out = []
    for i in range(6):
        kw = dict(breath=breath[i], head=-round(breath[i - 1] * 0.5), flame=i, lean=[0, 1, 0, -1, 0, 1][i] * 1.0,
                  pulse=1 if i in (2, 3) else 0, sway=[0, 0.5, 1.0, 1.0, 0.5, 0][i], crouch=1.0)
        if direction in ("left", "right"):
            kw.update(foot=((-4.0, 0), (4.5, 0)), hand=((-1.0, 0), (1.5, 0)), lean_body=1.0 + 0.15 * breath[i])
        else:
            kw.update(shift=rock[i], twist=rock[i] * 0.5, stilt=rock[i] * 0.6)
        out.append(pose(**kw))
    return out


def walk_phase(i):
    phL = 2 * math.pi * (i % 8) / 8.0
    return phL, phL + math.pi


def act_walk(direction):
    bobs = [round(1 - 3 * abs(math.sin(walk_phase(i)[0]))) for i in range(8)]      # 접지 +1 · 교차 -2
    out = []
    for i in range(8):
        phL, phR = walk_phase(i)
        b, bp = bobs[i], bobs[i - 1]
        lag = walk_phase(i - 1)[0]
        lag2 = walk_phase(i - 2)[0]
        if direction in ("down", "up"):
            sgn = 1 if direction == "down" else -1
            liftL = round(max(0.0, -math.sin(phL)) * 5)
            liftR = round(max(0.0, -math.sin(phR)) * 5)
            stepL, stepR = 2.5 * math.cos(phL) * sgn, 2.5 * math.cos(phR) * sgn
            stance = math.sin(phL)                     # + = 왼발 디딤
            arm = 2.5 * math.cos(phL) * sgn
            out.append(pose(bob=b, head=round((bp - b) * 0.6), crouch=1.0,
                            shift=1.8 * stance, ptilt=1.4 * stance, stilt=1.6 * stance, twist=1.2 * math.cos(phL) * sgn,
                            lift=(liftL, liftR), step=(stepL, stepR),
                            hand=((0.5 * math.sin(phL), -arm), (-0.5 * math.sin(phL), arm)),
                            sway=2.6 * math.sin(lag), flame=i % 6, lean=-2.6 * math.sin(lag2), pulse=i % 4 == 0))
        else:
            near_ = (STRIDE_A * math.cos(phL), round(max(0.0, -math.sin(phL)) * 5.0))
            far_ = (STRIDE_A * math.cos(phR), round(max(0.0, -math.sin(phR)) * 5.0))
            out.append(pose(bob=b, head=round((bp - b) * 0.6), crouch=1.0, foot=(far_, near_),
                            hand=((-5.5 * math.cos(phR), 0), (-5.5 * math.cos(phL), 0)),
                            lean_body=1.4 + 0.6 * (b < 0),
                            sway=-2.0 - 1.8 * math.cos(2 * lag), flame=i % 6, lean=-2.6 - 1.0 * math.cos(2 * lag2),
                            pulse=i % 4 == 0))
    return out


ACTIONS = {"idle": (act_idle, IDLE_MS, True), "walk": (act_walk, WALK_MS, True)}
STRIDE = {"walk": {"px": round(4 * STRIDE_A * S), "cycleMs": CYCLE_MS}}
