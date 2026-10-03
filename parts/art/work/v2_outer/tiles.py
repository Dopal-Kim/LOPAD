"""tiles/v2/stage1_outer — 1층 '잔' 외곽 거리, 32×32 쿼터뷰 타일셋 (50라운드 시범, 계약 §9).

시트: 8열 × 10행 (256×320). 인덱스 = row*8+col.
  0~39  인덱스 표 v3 의미 그대로 (0~3 바닥, 4 복도, 5 벽 앞면 아랫단, 6 벽 윗면, 7 void, 8~10 문, 11 출구, 12 상점,
        13~20 소품, 21~22 벽 앞면 아랫단 변형, 23~38 roomFloors, 39 예비)
  40~63 v2 신규 (앞면 윗단·돌담·윗면 가장자리·바닥 그늘·void 변형·배수로)
  64~79 큰 소품 영역(rect 로 지정: 가로등·상자 더미·노점·우물·빨래줄)
"""
from kit import *

T = 32
COLS, ROWS = 8, 10

# 바탕 판석(0~3)에 방 종류 바닥(roomFloors 23~38)을 섞는 비율 → JSON roomFloorMix (계약 §12 · 52라운드 Q9, 0~1).
# 근거: 목업(scene.py) 바닥 288칸은 전부 판석 0~3, 바닥에 붙는 강조(웅덩이 3 · 잔해 2)만 5칸 = 1.7%.
# 방 종류 바닥도 그 정도 밀도의 '드문 강조'로 보이게 0.02 (방 26×11 기준 약 6칸). 없으면 시스템 기본 0.06.
ROOM_FLOOR_MIX = 0.02

# 53라운드 Q51~Q54 세부안: 바닥을 Gemini 테두리 톤(따뜻한 갈색)에 맞춰 다시 칠함.
# 판석·줄눈·배수로의 청회 SL 램프만 같은 명도의 따뜻한 색(어두운 쪽 = WD 엄버, 밝은 쪽 = PL 회갈)으로 바꾼다.
# 무채 G·층 램프 A(잔 각인·술)·벽·지붕·소품·그늘은 그대로. 새 색 없음(v2 재질 블록 안).
WARM_FLOOR_IDX = set(range(0, 5)) | set(range(23, 39)) | {60, 61, 62}
WARM_FLOOR_MAP = {SL[0][:3]: WD[0], SL[1][:3]: WD[0], SL[2][:3]: WD[1], SL[3][:3]: WD[3],
                  SL[4][:3]: PL[0], SL[5][:3]: PL[1], SL[6][:3]: PL[2], SL[7][:3]: PL[3]}


def warm_floor(im):
    """바닥 칸의 청회 → 따뜻한 갈색(같은 명도 단계, 알파 유지)."""
    im = im.copy()
    p = im.load()
    for y in range(im.height):
        for x in range(im.width):
            q = p[x, y]
            if q[3] and q[:3] in WARM_FLOOR_MAP:
                p[x, y] = WARM_FLOOR_MAP[q[:3]][:3] + (q[3],)
    return im

# 재질 램프 묶음 (어두움 → 밝음)
STONE = {
    "cool": [SL[2], SL[3], SL[4], SL[5], SL[6]],
    "neut": [G[2], G[3], G[4], G[5], G[6]],
    "dark": [SL[1], SL[2], SL[3], SL[4], SL[5]],
    # 바닥 판석 전용: 본색 SL4/G04 를 섞고 빛 테는 한 단만 (격자 띠 방지)
    "flagA": [SL[2], SL[3], SL[4], SL[5], SL[6]],
    "flagB": [SL[2], SL[3], SL[4], SL[5], SL[6]],
}
JOINT, JOINT_D = SL[2], SL[1]


def new():
    return Canvas(T, T)


# ---------------------------------------------------------------------------
# 바닥 판석
# ---------------------------------------------------------------------------
def slab(c, x0, y0, x1, y1, tone, seed, wet=0.0, flecks=1.0, worn=True):
    """한 장의 판석 (x0..x1, y0..y1 포함). tone: STONE 키."""
    r = Rand(seed)
    R = STONE[tone]
    c.rect(x0, y0, x1, y1, R[2])
    w, h = x1 - x0 + 1, y1 - y0 + 1
    # 면 안의 약한 명도 얼룩: 50% 바둑 디더 덩어리(대비 낮음) 1~2개 + 판석 전체 밝기 차는 디더 밀도로
    dens = {"flagA": 0.0, "flagB": 0.22}.get(tone, 0.0)
    if dens:
        for yy in range(y0 + 1, y1):
            for xx in range(x0 + 1, x1):
                if (xx + yy) % 2 == 0 and r.f() < dens * 2:
                    c.px(xx, yy, R[1])
    for _ in range(r.i(1, 2)):
        bw, bh = r.i(5, min(11, max(5, w - 3))), r.i(3, min(7, max(3, h - 3)))
        bx = x0 + r.i(1, max(1, w - bw - 1)); by = y0 + r.i(1, max(1, h - bh - 1))
        for yy in range(by, by + bh):
            for xx in range(bx, bx + bw):
                corner = (yy in (by, by + bh - 1)) and (xx in (bx, bx + bw - 1))
                if not corner and (xx + yy) % 2 == 0 and x0 < xx < x1 and y0 < yy < y1:
                    c.px(xx, yy, R[1])
    # 빛 쪽 모서리(위) — 짧은 구간만, 그늘 쪽(아래·오른) 1px 은 홈 느낌으로 유지
    run = 0
    for x in range(x0 + 1, x1):
        if run <= 0 and r.f() < 0.10:
            run = r.i(3, 7)
        if run > 0:
            c.px(x, y0, R[3]); run -= 1
    for x in range(x0, x1 + 1):
        if r.f() > 0.06:
            c.px(x, y1, R[1])
    for y in range(y0 + 1, y1 + 1):
        if r.f() > 0.1:
            c.px(x1, y, R[1])
    # 잔점(2px 묶음) — 고립 픽셀 금지라 2px 이상
    n = int(w * h / 140 * flecks)
    for _ in range(n):
        fx, fy = r.i(x0 + 2, x1 - 3), r.i(y0 + 2, y1 - 2)
        col = R[1] if r.f() < 0.75 else R[3]
        c.px(fx, fy, col)
        c.px(fx + 1, fy, col) if r.f() < 0.6 else c.px(fx, fy + 1, col)
    # 젖은 반사: 왼쪽 위에서 짧은 사선 하이라이트 + 중앙 글린트
    if r.f() < wet:
        sx, sy = r.i(x0 + 2, x0 + max(2, w // 2)), r.i(y0 + 2, y0 + max(2, h // 2))
        ln = r.i(3, 6)
        for k in range(ln):
            c.px(sx + k, sy + (k // 3), R[3])
        c.px(sx + ln // 2, sy + (ln // 2) // 3, R[4])
        c.px(sx + ln // 2 + 1, sy + (ln // 2 + 1) // 3, R[4])
    # 닳은 모서리
    if worn:
        for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            p = r.f()
            if p < 0.55:
                c.px(cx, cy, JOINT)
            if p < 0.18:
                c.px(cx + dx, cy, JOINT); c.px(cx, cy + dy, JOINT)


def joints(c, seed, extra=()):
    """타일 왼쪽 열·위쪽 행 = 줄눈(이어붙임 보장). 깊은 틈 몇 점."""
    r = Rand(seed)
    c.rect(0, 0, T - 1, T - 1, JOINT)
    for _ in range(5):
        x = r.i(0, T - 1)
        c.px(x, 0, JOINT_D)
    for _ in range(5):
        y = r.i(0, T - 1)
        c.px(0, y, JOINT_D)


def flag_tile(layout, seed, wet=0.35, tones=None, flecks=1.0):
    """layout: [(x0,y0,x1,y1)] 판석 사각형(줄눈 1px 포함 안 함)."""
    c = new()
    joints(c, seed)
    r = Rand(seed + 7)
    tones = tones or ["flagA", "flagA", "flagA", "flagB"]
    for i, (x0, y0, x1, y1) in enumerate(layout):
        slab(c, x0, y0, x1, y1, r.choice(tones), seed * 31 + i, wet=wet, flecks=flecks)
    return c


FLOOR_LAYOUTS = [
    [(1, 1, 31, 31)],                                     # 큰 판석 1장
    [(1, 1, 31, 12), (1, 14, 20, 31), (22, 14, 31, 31)],  # 위 긴 판석 + 아래 2장
    [(1, 1, 18, 31), (20, 1, 31, 19), (20, 21, 31, 31)],  # 왼 긴 판석 + 오른 2장
    [(1, 1, 31, 18), (1, 20, 31, 31)],                    # 가로 2장 (비대칭)
]


def floor(i, seed_base=100, **kw):
    return flag_tile(FLOOR_LAYOUTS[i], seed_base + i * 13, **kw)


def gravel(c, x0, y0, x1, y1, seed, density=0.16):
    """자갈: 2~3px 둥근 알갱이(위 빛·아래 그늘)."""
    r = Rand(seed)
    n = int((x1 - x0) * (y1 - y0) * density / 4)
    for _ in range(n):
        x, y = r.i(x0, x1 - 2), r.i(y0, y1 - 2)
        R = STONE[r.choice(["cool", "neut", "dark"])]
        c.px(x, y, R[3]); c.px(x + 1, y, R[2])
        c.px(x, y + 1, R[2]); c.px(x + 1, y + 1, R[1])
        if r.f() < 0.4:
            c.px(x + 2, y + 1, R[1])


def corridor():
    """복도: 작은 사각 포석(돌길) — 판석보다 잘게, 자갈 몇 알."""
    c = new()
    joints(c, 400)
    r = Rand(401)
    # 8×8 포석 4×4, 행마다 반 칸 어긋남(타일 안에서 닫히게 가장자리 줄눈 유지)
    for row in range(4):
        y0 = row * 8 + 1
        off = 0 if row % 2 == 0 else 4
        xs = [1] + [x for x in range(off + 1, 32, 8) if x > 1] if off else [1, 9, 17, 25]
        xs = sorted(set(xs))
        for k, x0 in enumerate(xs):
            x1 = (xs[k + 1] - 2) if k + 1 < len(xs) else 31
            if x1 - x0 < 2:
                continue
            slab(c, x0, y0, x1, y0 + 6, r.choice(["flagA", "flagB"]), 410 + row * 9 + k,
                 wet=0.1, flecks=0.3)
    return c


# ---------------------------------------------------------------------------
# 반목조 건물 앞면 (쿼터뷰 2칸: 윗단 40~42 + 아랫단 5·21·22)
# ---------------------------------------------------------------------------
def post(c, x, y0, y1, w=3):
    """세로 기둥 (빛 왼쪽)."""
    c.rect(x, y0, x + w - 1, y1, WD[3])
    c.vline(x, y0, y1, WD[4])
    c.vline(x + w - 1, y0, y1, WD[1])


def beam(c, y, x0=0, x1=T - 1, h=3, jetty=False):
    c.rect(x0, y, x1, y + h - 1, WD[3])
    c.hline(x0, x1, y, WD[5] if jetty else WD[4])
    c.hline(x0, x1, y + h - 1, WD[1])


def plaster(c, x0, y0, x1, y1, seed, grime_from=None):
    r = Rand(seed)
    c.rect(x0, y0, x1, y1, PL[2])
    # 위쪽은 빛(PL3) 띠 약간, 아래로 갈수록 때(PL1)
    for x in range(x0, x1 + 1):
        if r.f() < 0.7:
            c.px(x, y0, PL[3])
    gf = grime_from if grime_from is not None else y1 - 4
    for y in range(gf, y1 + 1):
        p = (y - gf + 1) / (y1 - gf + 2)
        for x in range(x0, x1 + 1):
            if r.f() < p * 0.8:
                c.px(x, y, PL[1])
    # 얼룩·금 2px 이상 묶음
    for _ in range(int((x1 - x0) * (y1 - y0) / 70)):
        x, y = r.i(x0 + 1, max(x0 + 1, x1 - 2)), r.i(y0 + 1, max(y0 + 1, y1 - 2))
        c.px(x, y, PL[1]); c.px(x + 1, y, PL[1])


def plaster_crack(c, x, y, seed, n=6):
    """회반죽이 떨어져 나간 자리: 불규칙한 작은 덩어리(안쪽 PL0 + 아래 가장자리 SL3 돌)."""
    r = Rand(seed)
    w = 3 + n // 2
    for yy in range(y, y + 3):
        inset = 1 if yy in (y, y + 2) else 0
        for xx in range(x + inset + r.i(0, 1), x + w - inset):
            c.px(xx, yy, PL[0])
    c.hline(x + 1, x + w - 2, y + 3, PL[1])
    c.px(x + 1, y + 1, SL[3]); c.px(x + 2, y + 1, SL[3])


def plinth(c, y0, seed, x0=0, x1=T - 1):
    """돌 기단 (y0..31): 4px 높이 블록 2단 + 위 문턱 빛."""
    r = Rand(seed)
    c.rect(x0, y0, x1, T - 1, SL[1])
    c.hline(x0, x1, y0, SL[5])
    rows = [(y0 + 1, y0 + 4), (y0 + 5, T - 1)]
    for ri, (a, b) in enumerate(rows):
        x = x0 + (0 if ri == 0 else -5)
        while x <= x1:
            w = r.i(7, 11)
            sx0, sx1 = max(x0, x), min(x1, x + w - 2)
            if sx1 - sx0 >= 1:
                R = STONE[r.choice(["cool", "neut", "dark"])]
                c.rect(sx0, a, sx1, b, R[2])
                c.hline(sx0, sx1, a, R[3])
                c.vline(sx0, a, b, R[3])
                c.hline(sx0, sx1, b, R[1])
            x += w
    c.hline(x0, x1, T - 1, SL[0])


def brace(c, x0, y0, x1, y1, w=3):
    """굵은 사선 목재. 세로로 w px 두께: 맨 위 빛(WD4) · 가운데 본색(WD3) · 맨 아래 그늘(WD1)."""
    n = max(abs(x1 - x0), abs(y1 - y0))
    for k in range(n + 1):
        x = x0 + round((x1 - x0) * k / n)
        y = y0 + round((y1 - y0) * k / n)
        for j in range(w):
            col = WD[4] if j == 0 else (WD[1] if j == w - 1 else WD[3])
            c.px(x, y + j, col)


def window_lit(c, wx0, wy0, wx1, wy1, lit=True):
    c.rect(wx0 - 1, wy0 - 1, wx1 + 1, wy1 + 1, WD[1])
    if lit:
        c.rect(wx0, wy0, wx1, wy1, A[23])
        c.rect(wx0 + 1, wy0 + 1, wx1 - 1, wy1 - 1, A[24])
        c.rect(wx0 + 2, wy0 + 3, wx1 - 3, wy1 - 4, A[25])
        c.hline(wx0, wx1, wy0, A[21])
        c.vline(wx0, wy0, wy1, A[22])
    else:
        c.rect(wx0, wy0, wx1, wy1, SL[1])
        c.rect(wx0 + 1, wy0 + 1, wx1 - 1, wy1 - 1, SL[2])
        c.hline(wx0, wx1, wy0, SL[0])
        c.px(wx0 + 2, wy0 + 2, SL[4]); c.px(wx0 + 3, wy0 + 2, SL[4])
    c.vline((wx0 + wx1) // 2, wy0, wy1, WD[1])
    c.hline(wx0, wx1, (wy0 + wy1) // 2, WD[1])


def front_lower(kind, seed):
    """아랫단(1층 지면층, 32×32). kind: plain / window / door / dark_window.
    공통 뼈대: 위 2px 돌출 보 그늘 · 왼쪽 기둥 3px(x0~2) · 바닥보(y21~23) · 돌 기단(y24~31)."""
    c = new()
    plaster(c, 0, 0, T - 1, 20, seed, grime_from=15)
    c.hline(0, T - 1, 0, WD[0]); c.hline(0, T - 1, 1, PL[0])
    for x in range(1, T, 3):
        c.px(x, 2, PL[1])
    plinth(c, 24, seed + 3)
    beam(c, 21, h=3)
    post(c, 0, 0, 23)
    if kind == "plain":
        post(c, 15, 2, 20, w=3)
        brace(c, 3, 18, 14, 7)
        if seed % 2:
            plaster_crack(c, 22, 9, seed + 9, n=4)
    elif kind in ("window", "dark_window"):
        wx0, wy0, wx1, wy1 = 9, 4, 23, 16
        window_lit(c, wx0, wy0, wx1, wy1, lit=(kind == "window"))
        # 덧창 (열림 / 닫힘)
        if kind == "window":
            for sx in (wx0 - 5, wx1 + 2):
                c.rect(sx, wy0 - 1, sx + 3, wy1 + 1, WD[3])
                c.vline(sx, wy0 - 1, wy1 + 1, WD[4])
                c.vline(sx + 3, wy0 - 1, wy1 + 1, WD[1])
                c.hline(sx, sx + 3, wy0 + 2, WD[1]); c.hline(sx, sx + 3, wy1 - 2, WD[1])
        else:
            # 닫힌 덧창 두 짝(널 + 쇠 경첩) — 빛 없음
            c.rect(wx0, wy0, wx1, wy1, WD[2])
            for x in range(wx0, wx1 + 1, 4):
                c.vline(x, wy0, wy1, WD[3]); c.vline(x + 1, wy0, wy1, WD[3])
            c.vline((wx0 + wx1) // 2, wy0, wy1, WD[0])
            c.hline(wx0, wx1, wy0, WD[4])
            c.hline(wx0, wx1, wy1, WD[1])
            for y in (wy0 + 3, wy1 - 3):
                c.hline(wx0, wx0 + 3, y, G[5]); c.hline(wx1 - 3, wx1, y, G[5])
        # 돌 창턱
        c.rect(wx0 - 2, wy1 + 2, wx1 + 2, wy1 + 3, SL[5])
        c.hline(wx0 - 2, wx1 + 2, wy1 + 3, SL[3])
        if kind == "window":
            for x in range(wx0, wx1 + 1):
                c.px(x, wy1 + 4, PL[3])
    elif kind == "door":
        dx0, dx1, dy0 = 9, 24, 3
        c.rect(dx0 - 2, dy0 - 1, dx1 + 2, T - 1, WD[1])
        c.hline(dx0 - 2, dx1 + 2, dy0 - 1, WD[4])
        c.vline(dx0 - 2, dy0, T - 1, WD[3])
        c.rect(dx0, dy0 + 1, dx1, T - 2, WD[2])
        for x in range(dx0, dx1 + 1, 4):
            c.vline(x, dy0 + 1, T - 2, WD[3])
            c.vline(x + 1, dy0 + 1, T - 2, WD[3])
            c.vline(x + 3, dy0 + 1, T - 2, WD[1])
        for y in (dy0 + 6, T - 8):
            c.hline(dx0, dx1, y, G[4]); c.hline(dx0, dx1, y - 1, G[6])
        c.px(dx1 - 3, 17, G[8]); c.px(dx1 - 2, 17, G[6]); c.px(dx1 - 3, 18, G[5]); c.px(dx1 - 2, 18, G[5])
        # 문 틈 빛 (자체 발광)
        c.vline(dx1 + 1, dy0 + 2, T - 3, A[23])
        c.hline(dx0, dx1, T - 2, A[24])
        c.rect(dx0 - 2, T - 1, dx1 + 2, T - 1, SL[5])
    return c


def front_upper(kind, seed):
    """윗단(2층, 32×32): 처마 그늘(y0~3) → 상인방(y4~6) → 회반죽+목재 → 돌출 보 jetty(y28~31)."""
    c = new()
    plaster(c, 0, 7, T - 1, 27, seed, grime_from=40)
    # 처마 밑 그늘 + 서까래 끝
    c.rect(0, 0, T - 1, 3, SL[1])
    c.hline(0, T - 1, 0, WD[0])
    for x in range(2, T, 8):
        c.rect(x, 0, x + 2, 2, WD[2]); c.px(x, 0, WD[3])
    beam(c, 4, h=3)
    post(c, 0, 7, 27)
    beam(c, 28, h=4, jetty=True)
    if kind == "plain":
        brace(c, 3, 8, 30, 24)
        brace(c, 3, 24, 30, 8)
    elif kind == "window":
        window_lit(c, 9, 10, 23, 23, lit=False)
        c.rect(7, 25, 25, 25, WD[4])
        brace(c, 3, 9, 8, 13, w=2)
        brace(c, 25, 13, 30, 9, w=2)
    elif kind == "sign":
        brace(c, 3, 24, 30, 8)
        # 쇠 까치발 + 매달린 나무 간판(술잔 문양 — 층 램프 21)
        c.hline(3, 17, 10, G[7]); c.hline(3, 17, 11, G[4])
        c.line(3, 17, 10, 11, G[5])
        c.vline(8, 12, 13, G[6]); c.vline(16, 12, 13, G[6])
        sx0, sy0, sx1, sy1 = 5, 14, 19, 26
        c.rect(sx0, sy0, sx1, sy1, WD[0])
        c.rect(sx0 + 1, sy0 + 1, sx1 - 1, sy1 - 1, WD[3])
        c.hline(sx0 + 1, sx1 - 1, sy0 + 1, WD[4])
        c.hline(sx0 + 1, sx1 - 1, sy1 - 1, WD[2])
        mx = (sx0 + sx1) // 2
        c.rect(mx - 3, sy0 + 3, mx + 2, sy0 + 3, A[21])
        c.rect(mx - 2, sy0 + 4, mx + 1, sy0 + 6, A[20])
        c.px(mx - 1, sy0 + 4, A[22])
        c.vline(mx - 1, sy0 + 7, sy0 + 8, A[19]); c.vline(mx, sy0 + 7, sy0 + 8, A[19])
        c.hline(mx - 3, mx + 2, sy0 + 9, A[19])
    return c


# ---------------------------------------------------------------------------
# 지붕(윗면) · 가장자리
# ---------------------------------------------------------------------------
ROOF = [SL[1], G[2], G[3], G[4], PL[0]]   # 지붕 널판(슬레이트): 그늘 → 빛


def roof(seed, patch=False, eave=False):
    """위에서 본 지붕: 5px 줄의 겹친 널판. 줄 아래 1px 겹침 그늘, 위 1px 빛, 세로 틈은 짧고 흐리게.
    가로·세로 이어붙임(5px×? 줄이 32 를 나누지 못하므로 32px 주기로 닫히게 행 높이 5,5,5,5,6,6)."""
    c = new()
    r = Rand(seed)
    c.rect(0, 0, T - 1, T - 1, ROOF[2])
    heights = [5, 5, 6, 5, 5, 6]
    y0 = 0
    for row, hgt in enumerate(heights):
        off = (row * 4) % 7
        x = -off
        while x < T:
            w = r.i(6, 8)
            tone = r.f()
            base = ROOF[2] if tone < 0.7 else (ROOF[1] if tone < 0.85 else ROOF[3])
            for yy in range(y0, y0 + hgt):
                for xx in range(max(0, x), min(T, x + w)):
                    c.px(xx, yy, base)
            # 위 빛 1px (끝 1px 비움)
            for xx in range(max(0, x + 1), min(T, x + w - 1)):
                c.px(xx, y0, ROOF[3] if base != ROOF[3] else ROOF[4])
            # 세로 틈 (아래 절반만, 짧게)
            if 0 <= x < T:
                for yy in range(y0 + hgt // 2, y0 + hgt - 1):
                    c.px(x, yy, ROOF[1])
            # 아래 모서리 둥글게(겹침 그늘)
            for xx in (x, x + w - 1):
                if 0 <= xx < T:
                    c.px(xx, y0 + hgt - 2, ROOF[1])
            x += w
        # 다음 줄이 덮는 겹침 그늘
        c.hline(0, T - 1, y0 + hgt - 1, ROOF[0])
        y0 += hgt
    if patch:
        # 덧댄 판자 조각
        c.rect(9, 12, 22, 19, WD[2])
        c.hline(9, 22, 12, WD[3]); c.hline(9, 22, 16, WD[1])
        c.hline(9, 22, 19, ROOF[0])
        c.px(10, 14, G[6]); c.px(21, 14, G[6])
    if eave:
        # 앞면 쪽(아래) 처마 끝: 낙수받이 나무판 + 빛 테 + 아래 짙은 그늘
        c.rect(0, T - 6, T - 1, T - 1, WD[2])
        c.hline(0, T - 1, T - 6, ROOF[4])
        c.hline(0, T - 1, T - 5, WD[4])
        c.hline(0, T - 1, T - 2, WD[1])
        c.hline(0, T - 1, T - 1, WD[0])
        for x in range(3, T, 8):
            c.px(x, T - 3, WD[1]); c.px(x, T - 4, WD[3])
    return c


def roof_edge(sides, seed):
    """sides: 'n','e','w' 조합 — 그 쪽이 바닥과 맞닿는 처마 끝(나무 테 + 빛 테 + 바깥 짙은 선)."""
    c = roof(seed)
    if "e" in sides:
        c.rect(T - 5, 0, T - 1, T - 1, WD[2])
        c.vline(T - 5, 0, T - 1, ROOF[0])
        c.vline(T - 4, 0, T - 1, WD[4])
        c.vline(T - 1, 0, T - 1, WD[0])
    if "w" in sides:
        c.rect(0, 0, 4, T - 1, WD[2])
        c.vline(0, 0, T - 1, WD[1])
        c.vline(1, 0, T - 1, WD[4])
        c.vline(4, 0, T - 1, ROOF[0])
    if "n" in sides:
        c.rect(0, 0, T - 1, 4, WD[2])
        c.hline(0, T - 1, 0, WD[4])
        c.hline(0, T - 1, 1, WD[3])
        c.hline(0, T - 1, 4, ROOF[0])
        if "e" in sides:
            c.rect(T - 5, 0, T - 1, 4, WD[2]); c.vline(T - 1, 0, T - 1, WD[0])
        if "w" in sides:
            c.rect(0, 0, 4, 4, WD[2]); c.vline(1, 0, T - 1, WD[4])
    return c


# ---------------------------------------------------------------------------
# 돌담 세트 (앞면 2칸 + 윗면)
# ---------------------------------------------------------------------------
def ashlar(c, y0, y1, seed, course=6):
    r = Rand(seed)
    c.rect(0, y0, T - 1, y1, SL[1])
    y = y0
    row = 0
    while y <= y1:
        h = min(course, y1 - y + 1)
        x = -(row % 2) * 6 - r.i(0, 3)
        while x < T:
            w = r.i(8, 13)
            sx0, sx1 = max(0, x), min(T - 1, x + w - 2)
            if sx1 - sx0 >= 1 and h >= 3:
                R = STONE[r.choice(["cool", "neut", "dark", "cool"])]
                c.rect(sx0, y, sx1, y + h - 2, R[2])
                c.hline(sx0, sx1, y, R[3])
                c.vline(sx0, y, y + h - 2, R[3])
                c.hline(sx0, sx1, y + h - 2, R[1])
                if sx1 - sx0 > 5 and r.f() < 0.4:
                    c.px(sx0 + r.i(2, sx1 - sx0 - 2), y + r.i(1, max(1, h - 3)), R[1])
            x += w
        y += h
        row += 1


def stone_lower(seed, ring=False):
    c = new()
    ashlar(c, 0, T - 1, seed)
    c.hline(0, T - 1, T - 1, SL[0])
    if ring:
        # 말 매는 쇠고리
        c.px(15, 12, G[5]); c.px(16, 12, G[5]); c.rect(14, 13, 17, 13, G[7])
        for (x, y) in ((13, 14), (13, 15), (13, 16), (18, 14), (18, 15), (18, 16), (14, 17), (15, 17), (16, 17), (17, 17)):
            c.px(x, y, G[6])
        c.px(14, 14, G[8])
    return c


def stone_upper(seed):
    c = new()
    ashlar(c, 6, T - 1, seed + 1)
    # 갓돌(위로 튀어나온 판) — 위에서 살짝 보이는 윗면 + 앞면 띠
    c.rect(0, 0, T - 1, 2, SL[5])
    c.hline(0, T - 1, 0, SL[6])
    c.rect(0, 3, T - 1, 5, SL[3])
    c.hline(0, T - 1, 5, SL[0])
    for x in range(0, T, 11):
        c.vline(x, 0, 5, SL[1])
    return c


def stone_top(seed):
    """돌담 윗면: 거친 갓돌(어두운 SL2~3, 바닥 판석과 구분) + 이음 틈."""
    c = new()
    r = Rand(seed)
    c.rect(0, 0, T - 1, T - 1, SL[1])
    y = 0
    for row, hgt in enumerate((8, 8, 8, 8)):
        x = -(row % 2) * 7
        while x < T:
            w = r.i(9, 14)
            x0, x1 = max(0, x), min(T - 1, x + w - 2)
            if x1 - x0 >= 1:
                R = STONE["dark"]
                c.rect(x0, y, x1, y + hgt - 2, R[1] if r.f() < 0.5 else R[2])
                c.hline(x0, x1, y, R[3])
                c.hline(x0, x1, y + hgt - 2, R[0])
                c.vline(x1, y, y + hgt - 2, R[0])
            x += w
        y += hgt
    return c


# ---------------------------------------------------------------------------
# 바닥 그늘(겹침 · 반투명) — 벽 발치
# ---------------------------------------------------------------------------
SHADOW = (14, 16, 24)


def _shadow_alpha(d, side):
    """벽 발치로부터 거리 d(px) → 알파. 4단 계단(픽셀 느낌)."""
    if side == "n":
        steps = ((3, 150), (6, 105), (9, 68), (12, 36))
    else:
        steps = ((2, 120), (4, 82), (6, 48), (8, 24))
    for lim, a in steps:
        if d < lim:
            return a
    return 0


def shadow(kind):
    c = new()
    p = c.p
    for y in range(T):
        for x in range(T):
            a = 0
            if "n" in kind:
                a = max(a, _shadow_alpha(y, "n"))
            if "w" in kind:
                a = max(a, _shadow_alpha(x, "s"))
            if "e" in kind:
                a = max(a, _shadow_alpha(T - 1 - x, "s"))
            if a:
                p[x, y] = SHADOW + (a,)
    return c


# ---------------------------------------------------------------------------
# void: 밤 지붕 원경
# ---------------------------------------------------------------------------
def void(kind, seed):
    c = new()
    r = Rand(seed)
    c.rect(0, 0, T - 1, T - 1, NT[1])
    if kind in ("roofs", "chimney"):
        for row in range(8):
            y0 = row * 4
            off = 0 if row % 2 == 0 else 3
            for x in range(-off, T, 6):
                for xx in range(x, x + 5):
                    if 0 <= xx < T:
                        c.px(xx, y0, NT[2])
            c.hline(0, T - 1, y0 + 3, NT[0])
        # 지붕 사이 골목(어두운 틈) — 가로 이음 유지 위해 세로로만
        if kind == "chimney":
            # 굴뚝 머리(위에서 본 어두운 사각 + 위 빛 1줄)
            c.rect(11, 9, 20, 18, NT[0])
            c.rect(12, 10, 19, 16, NT[2])
            c.hline(12, 19, 10, SL[2])
            c.rect(14, 12, 17, 14, NT[0])
    else:  # 'gap' — 지붕 사이 깊은 골목(평평한 어둠)
        c.rect(0, 0, T - 1, T - 1, NT[0])
    return c


# ---------------------------------------------------------------------------
# 문 · 출구 · 상점
# ---------------------------------------------------------------------------
def gate(kind):
    c = new()
    # 공통: 돌 문설주 + 나무 상인방
    for x0 in (0, T - 5):
        c.rect(x0, 0, x0 + 4, T - 1, SL[3])
        c.vline(x0, 0, T - 1, SL[5])
        c.vline(x0 + 4, 0, T - 1, SL[1])
        for y in range(5, T, 7):
            c.hline(x0, x0 + 4, y, SL[1])
    c.rect(0, 0, T - 1, 4, WD[3]); c.hline(0, T - 1, 0, WD[4]); c.hline(0, T - 1, 4, WD[0])
    ix0, ix1 = 5, T - 6
    if kind == "open":
        # 안쪽 통로: 위로 갈수록 어두운 판석 + 활짝 열린 문짝
        for y in range(5, T):
            t = (y - 5) / (T - 5)
            col = NT[1] if t < 0.25 else (SL[1] if t < 0.55 else SL[2])
            c.hline(ix0, ix1, y, col)
        for y in (14, 22, 29):
            c.hline(ix0 + 2, ix1 - 2, y, SL[3] if y > 20 else SL[2])
        for x0 in (ix0, ix1 - 2):
            c.rect(x0, 5, x0 + 2, T - 1, WD[3])
            c.vline(x0, 5, T - 1, WD[4]); c.vline(x0 + 2, 5, T - 1, WD[1])
    else:
        c.rect(ix0, 5, ix1, T - 1, WD[2])
        for x in range(ix0, ix1 + 1, 4):
            c.vline(x, 5, T - 1, WD[3]); c.vline(x + 3, 5, T - 1, WD[1])
        c.vline((ix0 + ix1) // 2, 5, T - 1, WD[0])
        for y in (10, 24):
            c.hline(ix0, ix1, y, G[4]); c.hline(ix0, ix1, y - 1, G[7])
            for x in (ix0 + 2, ix1 - 2):
                c.px(x, y - 1, G[9])
        if kind == "locked":
            c.rect(ix0 - 1, 15, ix1 + 1, 18, WD[4]); c.hline(ix0 - 1, ix1 + 1, 15, WD[5])
            c.hline(ix0 - 1, ix1 + 1, 18, WD[1])
            mx = (ix0 + ix1) // 2
            c.rect(mx - 3, 17, mx + 2, 23, G[5]); c.rect(mx - 2, 18, mx + 1, 22, G[7])
            c.hline(mx - 2, mx + 1, 18, G[9])
            c.px(mx - 1, 20, A[23]); c.px(mx - 1, 21, A[21])
            c.rect(mx - 2, 14, mx + 1, 14, G[6]); c.px(mx - 2, 15, G[6]); c.px(mx + 1, 15, G[6])
        else:
            c.px((ix0 + ix1) // 2 - 2, 17, G[8]); c.px((ix0 + ix1) // 2 + 2, 17, G[8])
    return c


def exit_steps():
    """앞으로 이어지는 돌계단 (2×2 반복) — 디딤판 빛 + 챌판 그늘, 가운데 닳은 자리, 호박 길잡이 점."""
    c = new()
    r = Rand(611)
    for k in range(4):
        y0 = k * 8
        c.rect(0, y0, T - 1, y0 + 4, SL[5])
        c.hline(0, T - 1, y0, SL[6])
        c.rect(0, y0 + 5, T - 1, y0 + 7, SL[2])
        c.hline(0, T - 1, y0 + 7, SL[1])
        for x in range(10, 22):
            if r.f() < 0.5:
                c.px(x, y0 + 2, SL[6])
        c.vline(0, y0, y0 + 7, SL[1])
        c.px(r.i(3, 8), y0 + 3, SL[4]); c.px(r.i(23, 28), y0 + 3, SL[4])
    c.px(15, 2, A[21]); c.px(16, 2, A[21]); c.px(15, 18, A[21]); c.px(16, 18, A[21])
    return c


def shop_deck():
    c = new()
    r = Rand(621)
    for k in range(4):
        x0 = k * 8
        c.rect(x0, 0, x0 + 7, T - 1, WD[3])
        c.vline(x0, 0, T - 1, WD[4])
        c.vline(x0 + 7, 0, T - 1, WD[1])
        for y in range(r.i(2, 6), T, r.i(9, 12)):
            c.px(x0 + r.i(2, 5), y, WD[2]); c.px(x0 + r.i(2, 5), y + 1, WD[2])
        cut = r.i(8, 24)
        c.hline(x0, x0 + 7, cut, WD[1])
        c.px(x0 + 2, cut + 2, G[6]); c.px(x0 + 5, cut + 2, G[6])
    return c


# ---------------------------------------------------------------------------
# 소품 (32×32, 배경 투명, 피벗 = 바닥 접점 아래 가운데)
# ---------------------------------------------------------------------------
CONTACT = (12, 14, 20, 120)


def contact_shadow(c, cx, cy, rx, ry=2):
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1:
                if c.get(x, y)[3] == 0:
                    c.px(x, y, CONTACT)


def barrel(c, ox=0, oy=0, tipped=False):
    """세운 참나무 술통 3/4 시점. 폭 20, 높이 26."""
    x0, x1 = ox + 6, ox + 25
    top, bot = oy + 4, oy + 29
    contact_shadow(c, ox + 16, oy + 30, 11, 2)
    # 몸통(살짝 불룩)
    for y in range(top + 3, bot + 1):
        t = (y - top) / (bot - top)
        bulge = 1 if 0.25 < t < 0.75 else 0
        a, b = x0 - bulge, x1 + bulge
        for x in range(a, b + 1):
            u = (x - a) / max(1, b - a)
            if u < 0.15:
                col = WD[2]
            elif u < 0.38:
                col = WD[4]
            elif u < 0.7:
                col = WD[3]
            elif u < 0.88:
                col = WD[2]
            else:
                col = WD[1]
            c.px(x, y, col)
        c.px(a, y, WD[0]); c.px(b, y, WD[0])
    # 널 이음(세로 틈)
    for sx in (x0 + 4, x0 + 9, x0 + 14):
        for y in range(top + 4, bot):
            if c.get(sx, y)[3]:
                c.px(sx, y, WD[1])
    # 쇠테 3줄
    for hy in (top + 6, (top + bot) // 2 + 1, bot - 4):
        for x in range(x0 - 1, x1 + 2):
            if c.get(x, hy)[3]:
                c.px(x, hy, G[4])
                c.px(x, hy - 1, G[6] if x < x0 + 9 else G[5])
        c.px(x0 + 4, hy - 1, G[9])
    # 뚜껑(타원)
    for y in range(top, top + 6):
        dy = (y - (top + 2.5)) / 3.0
        half = int(round(10 * (1 - dy * dy) ** 0.5)) if abs(dy) < 1 else 0
        for x in range(ox + 16 - half, ox + 16 + half):
            c.px(x, y, WD[4] if y < top + 3 else WD[3])
        if half:
            c.px(ox + 16 - half, y, WD[1]); c.px(ox + 16 + half - 1, y, WD[1])
    c.hline(ox + 9, ox + 22, top, WD[2])
    c.hline(ox + 8, ox + 23, top + 5, G[5])
    c.px(ox + 12, top + 2, WD[5]); c.px(ox + 13, top + 2, WD[5]); c.px(ox + 18, top + 3, WD[2]); c.px(ox + 19, top + 3, WD[2])
    # 마개 + 술 방울(층 램프)
    c.px(ox + 16, top + 2, WD[1]); c.px(ox + 17, top + 2, WD[1])
    c.px(ox + 20, bot - 8, A[21]); c.px(ox + 20, bot - 7, A[19])
    # 바닥 접지선
    c.hline(x0 + 1, x1 - 1, bot, WD[0])


def crate(c, ox=0, oy=0, w=22, h=20, top_h=7, seed=0):
    x0, y0 = ox + (32 - w) // 2, oy + 30 - h - top_h
    contact_shadow(c, ox + 16, oy + 30, w // 2 + 1, 2)
    # 윗면
    c.rect(x0, y0, x0 + w - 1, y0 + top_h - 1, WD[4])
    c.hline(x0, x0 + w - 1, y0, WD[5])
    for x in range(x0 + 5, x0 + w - 1, 5):
        c.vline(x, y0 + 1, y0 + top_h - 1, WD[3])
    c.rect(x0, y0, x0, y0 + top_h - 1, WD[2])
    # 앞면
    fy0 = y0 + top_h
    c.rect(x0, fy0, x0 + w - 1, fy0 + h - 1, WD[3])
    for y in range(fy0 + 4, fy0 + h - 1, 5):
        c.hline(x0, x0 + w - 1, y, WD[2])
    # 테두리 각목 + 사선 버팀
    for (a, b) in ((x0, x0 + 2), (x0 + w - 3, x0 + w - 1)):
        c.rect(a, fy0, b, fy0 + h - 1, WD[2])
        c.vline(a, fy0, fy0 + h - 1, WD[4])
    c.rect(x0, fy0, x0 + w - 1, fy0 + 1, WD[4])
    c.hline(x0, x0 + w - 1, fy0, WD[5])
    c.rect(x0, fy0 + h - 2, x0 + w - 1, fy0 + h - 1, WD[2])
    for k in range(w - 6):
        x = x0 + 3 + k
        y = fy0 + h - 3 - k * (h - 5) // (w - 6)
        c.px(x, y, WD[4]); c.px(x, y + 1, WD[1])
    c.hline(x0, x0 + w - 1, fy0 + h - 1, WD[0])
    c.vline(x0 + w - 1, y0, fy0 + h - 1, WD[1])
    for (x, y) in ((x0 + 1, fy0 + 3), (x0 + w - 2, fy0 + 3), (x0 + 1, fy0 + h - 4), (x0 + w - 2, fy0 + h - 4)):
        c.px(x, y, G[7])


def puddle(c, seed=5):
    r = Rand(seed)
    # 불규칙한 납작 타원 2개 겹침
    blobs = [(15, 20, 11, 5), (10, 17, 6, 3), (22, 23, 6, 3)]
    for (cx, cy, rx, ry) in blobs:
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    c.px(x, y, SL[2])
    # 가장자리 젖은 테(위·왼은 어둡게, 아래·오른은 반사 빛)
    p = c.p
    pts = [(x, y) for y in range(T) for x in range(T) if p[x, y][3]]
    for (x, y) in pts:
        if c.get(x, y - 1)[3] == 0:
            c.px(x, y, SL[1])
        elif c.get(x, y + 1)[3] == 0:
            c.px(x, y, SL[4])
    # 하늘·불빛 반사 줄 (가로)
    for (x, y, n) in ((9, 18, 5), (16, 21, 7), (21, 24, 3)):
        c.hline(x, x + n - 1, y, SL[6])
        c.px(x + n // 2, y, SL[7])
    c.hline(12, 14, 16, SL[5])


def lantern(c, ox=0, oy=0):
    """바닥에 놓인 쇠 등불(자체 발광 코어)."""
    cx = ox + 16
    contact_shadow(c, cx, oy + 30, 6, 1)
    # 받침
    c.rect(cx - 5, oy + 27, cx + 4, oy + 29, G[3]); c.hline(cx - 5, cx + 4, oy + 27, G[6])
    c.hline(cx - 5, cx + 4, oy + 29, G[1])
    # 몸통 유리 + 쇠살
    c.rect(cx - 4, oy + 13, cx + 3, oy + 26, G[2])
    c.rect(cx - 3, oy + 14, cx + 2, oy + 25, A[24])
    c.rect(cx - 2, oy + 16, cx + 1, oy + 23, A[25])
    c.rect(cx - 1, oy + 18, cx, oy + 21, A[26])
    c.px(cx - 1, oy + 19, A[27]); c.px(cx, oy + 20, A[27])
    for x in (cx - 4, cx + 3):
        c.vline(x, oy + 13, oy + 26, G[3])
    c.vline(cx - 4, oy + 13, oy + 26, G[5])
    c.hline(cx - 4, cx + 3, oy + 19, G[3])
    # 지붕 + 고리
    c.rect(cx - 5, oy + 10, cx + 4, oy + 12, G[3]); c.hline(cx - 4, cx + 3, oy + 10, G[6])
    c.rect(cx - 3, oy + 8, cx + 2, oy + 9, G[4])
    c.hline(cx - 2, cx + 1, oy + 5, G[6]); c.px(cx - 3, oy + 6, G[6]); c.px(cx + 2, oy + 6, G[5])
    c.px(cx - 3, oy + 7, G[5]); c.px(cx + 2, oy + 7, G[4])


def brazier(c, ox=0, oy=0):
    cx = ox + 16
    contact_shadow(c, cx, oy + 30, 9, 2)
    # 세발 다리
    c.line(cx - 7, oy + 29, cx - 4, oy + 21, G[4]); c.line(cx - 6, oy + 29, cx - 3, oy + 21, G[2])
    c.line(cx + 6, oy + 29, cx + 3, oy + 21, G[3]); c.line(cx + 5, oy + 29, cx + 2, oy + 21, G[1])
    c.vline(cx, oy + 22, oy + 29, G[3]); c.vline(cx - 1, oy + 22, oy + 29, G[5])
    # 그릇
    c.rect(cx - 9, oy + 15, cx + 8, oy + 20, G[3])
    c.hline(cx - 9, cx + 8, oy + 15, G[7]); c.hline(cx - 8, cx + 7, oy + 20, G[1])
    c.hline(cx - 9, cx - 2, oy + 16, G[5])
    for x in range(cx - 7, cx + 7, 4):
        c.px(x, oy + 18, G[1]); c.px(x + 1, oy + 18, G[1])
    # 숯 + 불꽃 (자체 발광)
    c.rect(cx - 8, oy + 13, cx + 7, oy + 14, A[18])
    for x in range(cx - 7, cx + 7, 3):
        c.px(x, oy + 13, A[22]); c.px(x + 1, oy + 14, A[20])
    flame = [
        "....5.......",
        "...565...5..",
        "...5665.56..",
        "..566765665.",
        ".5667776765.",
        ".5677777765.",
        "566777777665",
        "556677776655",
    ]
    cmap = {"5": A[23], "6": A[25], "7": A[26]}
    for j, row in enumerate(flame):
        for i, ch in enumerate(row):
            if ch in cmap:
                c.px(cx - 6 + i, oy + 5 + j, cmap[ch])
    c.px(cx - 1, oy + 9, A[27]); c.px(cx, oy + 10, A[27]); c.px(cx - 1, oy + 10, A[27])
    # 불티
    c.px(cx + 4, oy + 2, A[24]); c.px(cx - 4, oy + 1, A[23])


def sacks(c):
    contact_shadow(c, 16, 30, 13, 2)

    def sack(x0, y0, w, h, tone):
        R = [PL[0], PL[1], PL[2], PL[3]] if tone else [G[5], G[6], G[7], G[8]]
        for y in range(y0, y0 + h):
            t = (y - y0) / h
            inset = 2 if t < 0.15 else (1 if t < 0.3 or t > 0.9 else 0)
            for x in range(x0 + inset, x0 + w - inset):
                u = (x - x0) / w
                col = R[3] if (u < 0.35 and t < 0.6) else (R[1] if u > 0.75 or t > 0.85 else R[2])
                c.px(x, y, col)
        # 묶은 목
        c.hline(x0 + w // 2 - 2, x0 + w // 2 + 1, y0 - 1, R[1])
        c.px(x0 + w // 2 - 1, y0 - 2, R[2]); c.px(x0 + w // 2, y0 - 2, R[2])
        c.hline(x0 + w // 2 - 2, x0 + w // 2 + 1, y0 + 1, WD[1])
        # 바닥 접지
        c.hline(x0 + 1, x0 + w - 2, y0 + h - 1, R[0])
    sack(3, 16, 13, 14, True)
    sack(16, 15, 13, 15, False)
    sack(9, 7, 13, 12, True)


def tipped_barrel(c):
    """쓰러진 술통 + 쏟아진 술(층 램프 — 비발광)."""
    # 쏟아진 술 웅덩이
    for (cx, cy, rx, ry) in ((19, 26, 11, 3), (26, 23, 5, 2)):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    c.px(x, y, A[18])
    c.hline(13, 20, 25, A[20]); c.hline(23, 28, 23, A[20]); c.px(16, 25, A[22]); c.px(17, 25, A[22])
    c.hline(10, 27, 28, A[17])
    # 옆으로 누운 통 (원통 가로)
    x0, x1, y0, y1 = 3, 22, 11, 25
    for y in range(y0, y1 + 1):
        t = (y - y0) / (y1 - y0)
        col = WD[4] if t < 0.3 else (WD[3] if t < 0.65 else (WD[2] if t < 0.85 else WD[1]))
        c.hline(x0, x1, y, col)
    for hx_ in (x0 + 4, x0 + 11, x1 - 3):
        c.vline(hx_, y0, y1, G[4]); c.vline(hx_ - 1, y0, y1, G[6])
    c.hline(x0, x1, y0, WD[5]); c.hline(x0, x1, y1, WD[0])
    # 열린 끝(타원, 오른쪽)
    for y in range(y0, y1 + 1):
        dy = (y - (y0 + y1) / 2) / ((y1 - y0) / 2 + 0.5)
        half = int(round(3.5 * max(0.0, 1 - dy * dy) ** 0.5))
        for x in range(x1, x1 + half + 1):
            c.px(x, y, WD[1] if x < x1 + half else WD[3])
    c.rect(x1 + 1, y0 + 4, x1 + 2, y1 - 4, A[19])
    contact_shadow(c, 12, 26, 10, 1)


def debris(c):
    """자갈 + 깨진 잔 조각 (통과 가능, 낮게)."""
    gravel(c, 4, 14, 28, 29, 701, density=0.55)
    # 깨진 도기 잔
    c.rect(12, 20, 17, 23, PL[3]); c.hline(12, 17, 20, PL[4]); c.hline(12, 17, 23, PL[1])
    c.px(18, 22, PL[2]); c.px(18, 21, PL[2])
    c.rect(13, 21, 16, 21, PL[0])
    c.px(20, 25, PL[3]); c.px(21, 25, PL[2]); c.px(9, 24, PL[3]); c.px(10, 24, PL[2])


# ---------------------------------------------------------------------------
# 큰 소품 (rect)
# ---------------------------------------------------------------------------
def lamp_post():
    c = Canvas(32, 64)
    cx = 13
    contact_shadow(c, cx + 1, 62, 6, 1)
    # 돌 받침
    c.rect(cx - 4, 57, cx + 5, 62, SL[3]); c.hline(cx - 4, cx + 5, 57, SL[5]); c.vline(cx - 4, 57, 62, SL[4])
    c.hline(cx - 4, cx + 5, 62, SL[1]); c.vline(cx + 5, 57, 62, SL[2])
    # 쇠기둥
    c.rect(cx, 12, cx + 1, 56, G[3]); c.vline(cx, 12, 56, G[6])
    c.rect(cx - 1, 50, cx + 2, 56, G[3]); c.vline(cx - 1, 50, 56, G[5])
    # 까치발 팔
    c.hline(cx, cx + 12, 12, G[5]); c.hline(cx, cx + 12, 13, G[2])
    c.line(cx + 1, 20, cx + 8, 13, G[4])
    c.px(cx + 1, 11, G[7]); c.px(cx, 10, G[6]); c.px(cx + 1, 10, G[5])
    # 매달린 등불
    lx = cx + 11
    c.vline(lx, 14, 15, G[5])
    c.rect(lx - 3, 16, lx + 3, 17, G[4]); c.hline(lx - 2, lx + 2, 16, G[7])
    c.rect(lx - 3, 18, lx + 3, 27, G[2])
    c.rect(lx - 2, 19, lx + 2, 26, A[24])
    c.rect(lx - 1, 20, lx + 1, 25, A[25])
    c.vline(lx, 21, 24, A[26]); c.px(lx, 22, A[27])
    c.vline(lx - 3, 18, 27, G[5])
    c.hline(lx - 3, lx + 3, 28, G[3]); c.px(lx, 29, G[4])
    return c


def crate_stack():
    c = Canvas(32, 64)
    crate(c, 0, 32, w=24, h=18, top_h=6)
    crate(c, 1, 12, w=20, h=14, top_h=6)
    # 위 상자는 아래 상자 위에 얹힘 → 아래 상자 윗면에 그림자
    for x in range(7, 26):
        if c.get(x, 39)[3]:
            c.px(x, 39, WD[2])
    return c


def stall():
    """노점: 찢긴 천막 + 기둥 + 술병 좌판 (64×64, 바닥 접점 y=62)."""
    c = Canvas(64, 64)
    contact_shadow(c, 32, 62, 27, 2)
    # 좌판 (카운터)
    cy0 = 40
    c.rect(8, cy0, 55, cy0 + 4, WD[4]); c.hline(8, 55, cy0, WD[5])
    c.rect(8, cy0 + 5, 55, 61, WD[3])
    for x in range(8, 56, 6):
        c.vline(x, cy0 + 5, 61, WD[2]); c.vline(x + 1, cy0 + 5, 61, WD[4])
    c.hline(8, 55, 61, WD[0]); c.vline(55, cy0, 61, WD[1])
    c.hline(8, 55, cy0 + 5, WD[1])
    # 술병들 (층 램프 21·19, 비발광 + 하이라이트 1px)
    for i, x in enumerate(range(13, 52, 7)):
        h = 7 if i % 2 == 0 else 5
        c.rect(x, cy0 - h, x + 2, cy0 - 1, A[19] if i % 3 else WD[2])
        c.px(x, cy0 - h + 1, A[22] if i % 3 else WD[4])
        c.rect(x + 1, cy0 - h - 2, x + 1, cy0 - h - 1, G[5])
        if i % 3:
            c.px(x + 2, cy0 - 3, A[21])
    # 기둥
    for x in (9, 52):
        c.rect(x, 8, x + 2, cy0 - 1, WD[3]); c.vline(x, 8, cy0 - 1, WD[4]); c.vline(x + 2, 8, cy0 - 1, WD[1])
    # 천막 (위에서 비스듬히 보이는 면 + 늘어진 찢긴 앞자락)
    for y in range(4, 16):
        t = (y - 4) / 12
        for x in range(4 + int(2 * (1 - t)), 60 - int(2 * (1 - t))):
            stripe = ((x // 6) % 2 == 0)
            col = (PL[3] if stripe else PL[2]) if t < 0.5 else (PL[2] if stripe else PL[1])
            c.px(x, y, col)
    c.hline(5, 58, 4, PL[4])
    # 앞자락: 톱니처럼 찢긴 끝
    r = Rand(77)
    for x in range(4, 60):
        drop = 16 + r.i(2, 7) + (3 if 20 < x < 27 else 0)
        for y in range(16, drop):
            stripe = ((x // 6) % 2 == 0)
            c.px(x, y, PL[1] if stripe else PL[0])
        c.px(x, drop, PL[0] if r.f() < 0.5 else CLEAR)
    c.hline(4, 59, 16, PL[3])
    # 구멍
    c.rect(30, 9, 33, 11, CLEAR); c.px(29, 10, PL[0]); c.px(34, 10, PL[0])
    return c


def well():
    c = Canvas(64, 64)
    contact_shadow(c, 32, 61, 22, 2)
    cx = 32
    # 돌 우물 몸통(원통) — 앞면
    for y in range(36, 61):
        for x in range(cx - 18, cx + 18):
            u = (x - (cx - 18)) / 36
            col = SL[5] if u < 0.25 else (SL[4] if u < 0.6 else (SL[3] if u < 0.85 else SL[2]))
            c.px(x, y, col)
    # 돌 줄눈
    r = Rand(91)
    for row, y in enumerate(range(40, 61, 5)):
        c.hline(cx - 18, cx + 17, y, SL[1])
        for x in range(cx - 18 + (row % 2) * 4, cx + 18, 8):
            c.vline(x, y - 4 if y > 40 else 37, y, SL[1])
    c.hline(cx - 17, cx + 16, 60, SL[0])
    # 윗테(타원 고리) + 어두운 우물 구멍
    for y in range(28, 40):
        dy = (y - 34) / 6.5
        half = int(round(19 * max(0, 1 - dy * dy) ** 0.5))
        for x in range(cx - half, cx + half):
            c.px(x, y, SL[6] if y < 33 else SL[5])
    for y in range(31, 38):
        dy = (y - 34.5) / 3.8
        half = int(round(14 * max(0, 1 - dy * dy) ** 0.5))
        for x in range(cx - half, cx + half):
            c.px(x, y, NT[0] if y < 36 else SL[1])
    c.hline(cx - 6, cx + 4, 36, SL[3])  # 물빛
    # 나무 틀 + 지붕보 + 도르래 + 두레박
    for x in (cx - 20, cx + 18):
        c.rect(x, 6, x + 2, 50, WD[3]); c.vline(x, 6, 50, WD[4]); c.vline(x + 2, 6, 50, WD[1])
    c.rect(cx - 23, 4, cx + 23, 8, WD[3]); c.hline(cx - 23, cx + 23, 4, WD[5]); c.hline(cx - 23, cx + 23, 8, WD[1])
    c.rect(cx - 2, 9, cx + 1, 12, G[4]); c.hline(cx - 2, cx + 1, 9, G[7])
    c.vline(cx, 13, 24, PL[2])
    c.rect(cx - 3, 25, cx + 3, 30, WD[3]); c.hline(cx - 3, cx + 3, 25, G[6]); c.hline(cx - 3, cx + 3, 30, WD[1])
    c.vline(cx - 3, 25, 30, WD[4])
    return c


def washing_line(seed=3):
    """벽 앞면 윗단에 거는 빨래줄 (64×32 겹침 장식, 가로 반복 가능)."""
    c = Canvas(64, 32)
    # 처진 줄
    pts = []
    for x in range(64):
        y = 4 + int(round(5 * math.sin(math.pi * x / 63)))
        pts.append((x, y))
        c.px(x, y, G[6])
    r = Rand(seed)
    x = 4
    while x < 58:
        w = r.i(6, 10)
        h = r.i(10, 18)
        tone = r.choice([PL, [G[8], G[9], G[10], G[11], G[12]], PL])
        y0 = pts[min(63, x + w // 2)][1] + 1
        for yy in range(y0, y0 + h):
            for xx in range(x, x + w):
                u = (xx - x) / w
                col = tone[3] if u < 0.3 else (tone[1] if u > 0.75 else tone[2])
                if yy == y0 + h - 1 and r.f() < 0.4:
                    continue
                c.px(xx, yy, col)
        c.hline(x, x + w - 1, y0, tone[4] if len(tone) > 4 else tone[3])
        c.hline(x, x + w - 1, y0 + h - 1, tone[0])
        c.px(x + 1, y0 - 1, WD[3]); c.px(x + w - 2, y0 - 1, WD[3])
        x += w + r.i(3, 7)
    return c


# ---------------------------------------------------------------------------
# 시트 조립
# ---------------------------------------------------------------------------
def build_sheet():
    sheet = Image.new("RGBA", (COLS * T, ROWS * T), CLEAR)
    cells = {}

    def put(idx, can):
        im = warm_floor(can.im) if idx in WARM_FLOOR_IDX else can.im
        cells[idx] = im
        sheet.alpha_composite(im, ((idx % COLS) * T, (idx // COLS) * T))

    for i in range(4):
        put(i, floor(i))
    put(4, corridor())
    put(5, front_lower("plain", 501))
    put(6, roof(601))
    put(7, void("roofs", 701))
    put(8, gate("open")); put(9, gate("closed")); put(10, gate("locked"))
    put(11, exit_steps()); put(12, shop_deck())
    p = new(); barrel(p); put(13, p)
    p = new(); crate(p); put(14, p)
    p = new(); puddle(p); put(15, p)
    p = new(); lantern(p); put(16, p)
    p = new(); brazier(p); put(17, p)
    p = new(); sacks(p); put(18, p)
    p = new(); tipped_barrel(p); put(19, p)
    p = new(); debris(p); put(20, p)
    put(21, front_lower("window", 521))
    put(22, front_lower("door", 522))
    # roomFloors
    # start: 황폐한 평화지역 — 흙·잔해·그을음
    put(23, room_start(0)); put(24, room_start(1)); put(25, room_start(2)); put(26, room_start(3))
    put(27, room_trial(0)); put(28, room_trial(1)); put(29, room_trial(2)); put(30, room_trial(3))
    put(31, room_rest(0)); put(32, room_rest(1)); put(33, room_rest(2)); put(34, room_rest(3))
    put(35, room_boss(0)); put(36, room_boss(1)); put(37, room_boss(2)); put(38, room_boss(3))
    # 39 예비(투명)
    put(40, front_upper("plain", 540)); put(41, front_upper("window", 541)); put(42, front_upper("sign", 542))
    put(43, stone_lower(543)); put(44, stone_upper(544)); put(45, stone_top(545)); put(46, stone_lower(546, ring=True))
    put(47, roof(647, eave=True))
    put(48, roof_edge("e", 648)); put(49, roof_edge("w", 649)); put(50, roof_edge("n", 650))
    put(51, roof_edge("ne", 651)); put(52, roof_edge("nw", 652))
    put(53, shadow("n")); put(54, shadow("w")); put(55, shadow("e")); put(56, shadow("nw")); put(57, shadow("ne"))
    put(58, void("chimney", 758)); put(59, void("gap", 759))
    put(60, drain(False)); put(61, drain(True)); put(62, gravel_floor()); put(63, front_lower("dark_window", 563))
    # 큰 소품 (64~79)
    big = {
        "lamp_post": (lamp_post(), 64, 1, 2),
        "crate_stack": (crate_stack(), 65, 1, 2),
        "stall": (stall(), 66, 2, 2),
        "well": (well(), 68, 2, 2),
        "washing_line": (washing_line(3), 70, 2, 1),
        "washing_line_b": (washing_line(8), 78, 2, 1),
    }
    rects = {}
    for name, (can, idx, cw, ch) in big.items():
        x, y = (idx % COLS) * T, (idx // COLS) * T
        sheet.alpha_composite(can.im, (x, y))
        rects[name] = {"index": idx, "x": x, "y": y, "w": cw * T, "h": ch * T}
    return sheet, cells, rects


# --- roomFloors ------------------------------------------------------------
def soot(c, cx, cy, rx, ry, seed):
    r = Rand(seed)
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1 and r.f() < (1.1 - d):
                cur = c.get(x, y)
                if cur[3] and cur[:3] != JOINT[:3]:
                    c.px(x, y, SL[1] if d < 0.45 else SL[2])


def dirt_patch(c, cx, cy, rx, ry, seed):
    r = Rand(seed)
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1 and r.f() < (1.15 - d * 0.6):
                c.px(x, y, WD[2] if r.f() < 0.6 else WD[1])
    gravel(c, cx - rx + 1, cy - ry + 1, cx + rx - 1, cy + ry - 1, seed + 1, density=0.25)


def room_start(i):
    c = floor(i, seed_base=230, wet=0.15)
    if i == 0:
        soot(c, 15, 16, 10, 8, 2301)
        c.px(14, 15, A[17]); c.px(15, 15, A[17]); c.px(16, 17, A[18]); c.px(17, 17, A[17])
    elif i == 1:
        dirt_patch(c, 18, 20, 9, 6, 2311)
    elif i == 2:
        gravel(c, 3, 3, 13, 11, 2321, density=0.3)
    else:
        gravel(c, 18, 20, 28, 28, 2331, density=0.3)
    return c


def room_trial(i):
    c = floor(i, seed_base=270, wet=0.3)
    if i == 0:
        # 배수구 철망
        c.rect(10, 10, 21, 21, SL[0])
        c.rect(11, 11, 20, 20, G[2])
        for x in range(12, 20, 2):
            c.vline(x, 11, 20, G[5])
        c.hline(11, 20, 11, G[7]); c.vline(11, 11, 20, G[6]); c.hline(11, 20, 20, G[1])
    elif i == 1:
        # 갈라진 판석 금
        pts = [(4, 6), (8, 9), (11, 10), (13, 14), (17, 16), (19, 21), (24, 23)]
        for (a, b), (cc, d) in zip(pts, pts[1:]):
            c.line(a, b, cc, d, SL[1])
        for (a, b) in pts[1:-1]:
            c.px(a + 1, b, SL[5])
    elif i == 2:
        gravel(c, 18, 4, 29, 12, 2721, density=0.25)
    else:
        c.px(9, 22, SL[1]); c.px(10, 22, SL[1]); c.px(22, 8, SL[1]); c.px(22, 9, SL[1])
    return c


def mottle(c, col, n, seed, x0=0, y0=0, x1=T - 1, y1=T - 1, size=(2, 4)):
    """2~4px 덩어리 얼룩 (잡점 대신)."""
    r = Rand(seed)
    for _ in range(n):
        x, y = r.i(x0, x1 - 1), r.i(y0, y1 - 1)
        w, h = r.i(*size), r.i(1, 2)
        for yy in range(y, y + h):
            for xx in range(x + (1 if yy > y else 0), x + w):
                if x0 <= xx <= x1 and y0 <= yy <= y1:
                    c.px(xx, yy, col)


def room_rest(i):
    """휴식 방: 다져진 흙(엄버) + 짚 + 판석 몇 장. 덩어리 얼룩만, 잡점 없음."""
    c = new()
    c.rect(0, 0, T - 1, T - 1, WD[2])
    mottle(c, WD[1], 9, 3100 + i)
    mottle(c, WD[3], 6, 3150 + i)
    if i == 0:
        slab(c, 4, 5, 16, 14, "flagB", 3101, wet=0.0, flecks=0.4)
        slab(c, 18, 18, 28, 27, "flagA", 3102, wet=0.0, flecks=0.4)
    elif i == 1:
        for (x, y, n) in ((5, 8, 5), (16, 20, 6), (21, 6, 4), (9, 25, 5)):
            c.line(x, y, x + n, y - 1, PL[3]); c.line(x + 1, y + 1, x + n, y, WD[4])
    elif i == 2:
        gravel(c, 8, 8, 24, 24, 3121, density=0.10)
    return c


def room_boss(i):
    """광장 포석: 큰 정사각 판석 + 가운데 문양(_0) — 2×2 로 이어지는 원형 홈."""
    c = new()
    joints(c, 350 + i)
    tones = ["neut", "cool", "neut", "dark"]
    slab(c, 1, 1, 31, 31, tones[i], 3500 + i, wet=0.25, flecks=0.6)
    if i == 0:
        # 판석 가운데 각인(잔 문양, 비발광 층 램프 어두운 칸)
        c.rect(11, 10, 20, 11, SL[2]); c.rect(12, 12, 19, 15, SL[2]); c.rect(15, 16, 16, 19, SL[2])
        c.rect(12, 20, 19, 21, SL[2])
        c.hline(12, 19, 12, A[17]); c.hline(13, 18, 15, A[17])
    elif i == 1:
        for (a, b) in ((6, 6), (24, 6), (6, 24), (24, 24)):
            c.px(a, b, SL[2]); c.px(a + 1, b, SL[2]); c.px(a, b + 1, SL[2]); c.px(a + 1, b + 1, SL[5])
    return c


def drain(grate):
    """배수로(가로 이어붙임): 판석 사이 얕은 돌 홈. grate=True 면 쇠 창살 덮개."""
    c = floor(1, seed_base=600, wet=0.2)
    y0, y1 = 12, 19
    c.rect(0, y0, T - 1, y1, SL[1])
    c.hline(0, T - 1, y0, SL[5])          # 위 모서리 빛
    c.hline(0, T - 1, y0 + 1, SL[2])
    c.rect(0, y0 + 2, T - 1, y1 - 1, SL[0])
    # 물줄기
    for x in range(0, T, 5):
        c.hline(x, x + 2, y0 + 4, SL[3])
    c.hline(0, T - 1, y1, SL[3])
    if grate:
        c.rect(6, y0 - 1, 25, y1 + 1, G[2])
        for x in range(7, 25, 3):
            c.vline(x, y0, y1, G[6]); c.vline(x + 1, y0, y1, G[4])
        c.hline(6, 25, y0 - 1, G[7]); c.hline(6, 25, y1 + 1, G[1])
    return c


def gravel_floor():
    """자갈 바닥(바닥 변형 선택): 바탕 SL3 + 자갈 알갱이 중간 밀도."""
    c = new()
    c.rect(0, 0, T - 1, T - 1, SL[3])
    mottle(c, SL[2], 14, 622)
    gravel(c, 0, 0, T, T, 621, density=0.35)
    return c
