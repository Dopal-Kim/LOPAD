"""61 단계 5 (P13 §4) 드랍 아이템 — `items/v3/<id>`: voucher(전표, 행 small/mid/large) · potion(잔의 독주) · fire_bottle(화염 술병).

한 시트 = 행(kinds) × 열 24: idle 0~7(반짝임 루프) · spawn 8~15(튀어 올라 떨어짐) · pickup 16~21(흡수 팝) · magnet 22~23(끌려가며 늘어남).
틀 64×96 · 피벗 (32,88) = 바닥 접점(그림자 가운데). 물건은 '쉴 때 그림(rest)' 하나를 그리고, 높이·늘임·그림자만 바꿔 프레임을 만든다.
"""
import math

from PIL import Image

from kit5 import (Canvas, Rand, G, A, SL, WD, PL, R, X0, X1, CONTACT, flame, outline_out, crop_rest, star, disc,
                  contact_shadow, lighten_map)

FW, FH = 80, 96
PIV = (40, 88)
OUT = SL[0]                       # 바깥 외곽선(어두운 남회색) — 밝은 바닥에서도 테가 남는다

# 열 배치
IDLE = list(range(0, 8))
SPAWN = list(range(8, 16))
PICKUP = list(range(16, 22))
MAGNET = [22, 23]
NCOL = 24
MS = ([120, 110, 100, 90, 90, 100, 110, 130] +          # idle (750ms 루프)
      [50, 60, 60, 70, 70, 60, 70, 90] +                # spawn 530ms
      [40, 40, 40, 50, 60, 70] +                        # pickup 300ms
      [70, 70])                                         # magnet 루프
GLOW_COLS = [8, 18, 19]                                 # 백열 X0/X1 이 있는 열(스폰 팝 · 흡수 섬광)

# ---------------------------------------------------------------------------------------------- 전표
P_FACE = [PL[3], PL[4], G[12], G[13]]          # 종이 면 그늘 → 빛 (밝은 회백 — 따뜻한 갈색 바닥과 명도·색이 갈리게)
P_EDGE = [PL[1], PL[2], PL[3]]                 # 쌓인 종이 옆면 줄
BRAND = ["#######", ".#####.", "..###..", "...#...", "...#...", "..###.."]   # 잔(盞) 낙인


def _rot(pts, cx, cy, ang, ky=0.78):
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + x * ca - y * sa, cy + (x * sa + y * ca) * ky) for x, y in pts]


def slip(c, cx, cy, w, h, ang, thick=1, seal=True, cord=False, seed=1):
    """한 장(또는 묶음) 종이 표. 바닥에 누운 직사각형(쿼터뷰 y 0.78 눌림) + 아래로 두께 줄 + 낙인·붉은 인주."""
    hw, hh = w / 2.0, h / 2.0
    face = _rot([(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)], cx, cy, ang)
    # 옆면(두께) — 아래쪽으로 한 줄씩, 종이 겹 줄무늬
    for t in range(thick, 0, -1):
        pts = [(x, y + t) for x, y in face]
        c.poly(pts, P_EDGE[(t + seed) % 2 + (1 if t == thick else 0)] if thick > 1 else PL[1])
    c.poly(face, P_FACE[2])
    # 면 셰이딩: 왼쪽 위 가장자리 빛, 오른쪽 아래 그늘(1도트 안쪽)
    inner = _rot([(-hw + 1, -hh + 1), (hw - 1, -hh + 1), (hw - 1, hh - 1), (-hw + 1, hh - 1)], cx, cy, ang)
    xs = [p[0] for p in face]
    ys = [p[1] for p in face]
    x0, x1, y0, y1 = int(min(xs)) - 1, int(max(xs)) + 2, int(min(ys)) - 1, int(max(ys)) + 2
    from PIL import ImageDraw
    m = Image.new("L", (c.w, c.h), 0)
    ImageDraw.Draw(m).polygon(face, fill=255)
    mi = Image.new("L", (c.w, c.h), 0)
    ImageDraw.Draw(mi).polygon(inner, fill=255)
    mp, mip = m.load(), mi.load()
    for y in range(max(0, y0), min(c.h, y1)):
        for x in range(max(0, x0), min(c.w, x1)):
            if mp[x, y] > 127 and mip[x, y] <= 127:
                up = y - 1 < 0 or mp[x, y - 1] <= 127
                left = x - 1 < 0 or mp[x - 1, y] <= 127
                c.px(x, y, P_FACE[3] if (up or left) else P_FACE[1])
    # 인쇄 테두리(안쪽 2도트)
    bor = _rot([(-hw + 2.5, -hh + 2.5), (hw - 2.5, -hh + 2.5), (hw - 2.5, hh - 2.5), (-hw + 2.5, hh - 2.5)], cx, cy, ang)
    for (ax, ay), (bx, by) in zip(bor, bor[1:] + bor[:1]):
        c.line(int(round(ax)), int(round(ay)), int(round(bx)), int(round(by)), A[20])
    # 잔 낙인(그을린 갈색 + 호박 테 한 점) — 가운데
    bx0, by0 = int(round(cx)) - 3, int(round(cy)) - 3
    for j, row in enumerate(BRAND):
        for i, ch in enumerate(row):
            if ch == "#":
                c.px(bx0 + i, by0 + j, A[17] if j else A[18])
    c.px(bx0 + 1, by0 + 1, A[19])
    if seal:   # 붉은 인주(오른쪽 위 모서리 안)
        sx, sy = _rot([(hw - 5, -hh + 4)], cx, cy, ang)[0]
        sx, sy = int(round(sx)), int(round(sy))
        c.rect(sx - 1, sy - 1, sx + 1, sy, R[5])
        c.px(sx - 1, sy - 1, R[7]); c.px(sx + 1, sy, R[3])
    if cord:   # 묶음 끈(짧은 축 가로지름 + 옆면으로 내려감)
        a0 = _rot([(-1, -hh - 0.5), (-1, hh + 0.5)], cx, cy, ang)
        (ax, ay), (bx, by) = a0
        for k in (0, 1):
            c.line(int(round(ax)) + k, int(round(ay)), int(round(bx)) + k, int(round(by)), A[19] if k == 0 else A[18])
        for t in range(1, thick + 1):
            c.px(int(round(bx)), int(round(by)) + t, A[19]); c.px(int(round(bx)) + 1, int(round(by)) + t, A[18])
        # 매듭
        kx, ky_ = int(round((ax + bx) / 2)), int(round((ay + by) / 2))
        c.rect(kx - 1, ky_ - 1, kx + 2, ky_ + 1, A[19]); c.px(kx - 1, ky_ - 1, A[20]); c.px(kx + 2, ky_ + 1, A[17])
        c.line(kx + 2, ky_ + 1, kx + 5, ky_ + 4, A[18]); c.line(kx + 1, ky_ + 1, kx + 2, ky_ + 5, A[19])


def voucher_rest(size):
    c = Canvas(64, 64)
    cx, by = 32, 58
    if size == "small":
        slip(c, cx - 4, by - 7, 19, 12, -0.32, thick=1, seed=1)
        slip(c, cx + 4, by - 5, 19, 12, 0.22, thick=1, seal=False, seed=2)
    elif size == "mid":
        slip(c, cx - 2, by - 9, 23, 14, -0.12, thick=5, cord=True, seed=3)
        slip(c, cx + 8, by - 4, 17, 11, 0.55, thick=1, seed=4)
    else:
        slip(c, cx - 9, by - 9, 23, 14, 0.10, thick=5, cord=True, seed=5)
        slip(c, cx + 10, by - 8, 23, 14, -0.18, thick=5, cord=True, seed=6)
        slip(c, cx + 1, by - 17, 23, 14, 0.38, thick=5, cord=True, seed=7)
        slip(c, cx - 13, by - 2, 16, 10, -0.6, thick=1, seal=False, seed=8)
        slip(c, cx + 13, by - 1, 16, 10, 0.5, thick=1, seed=9)
    outline_out(c.im, OUT)
    return c.im


# ---------------------------------------------------------------------------------------------- 물약(잔의 독주)
def potion_rest():
    """둥근 몸 + 짧은 목 + 코르크 + 검붉은 밀랍. 붉은 술이 몸 3/4 을 채우고 속에서 빛남(자체 발광 R8~R11)."""
    c = Canvas(64, 64)
    cx, by = 32, 58
    ccx, ccy, r = cx, by - 11, 11
    # 유리 몸(어두운 유리)
    disc(c, ccx, ccy, r, SL[3])
    disc(c, ccx, ccy, r - 1, SL[2])
    # 술(아래 3/4): 원 안 y >= 액면
    lvl = ccy - 4
    for y in range(int(ccy - r), int(ccy + r) + 1):
        for x in range(int(ccx - r), int(ccx + r) + 1):
            d = math.hypot(x - ccx, (y - ccy))
            if d <= r - 1.2 and y >= lvl:
                # 속 빛: 아래 가운데 쪽이 가장 밝고 가장자리 어둡게
                gl = 1.0 - math.hypot((x - ccx + 1) / (r * 0.9), (y - (ccy + 2)) / (r * 0.75))
                if d > r - 2.2:
                    col = R[3] if (x - ccx) + (y - ccy) > 0 else R[4]
                elif gl > 0.55:
                    col = R[9]
                elif gl > 0.32:
                    col = R[8]
                elif gl > 0.1:
                    col = R[6]
                else:
                    col = R[5]
                c.px(x, y, col)
    for x in range(int(ccx - r + 2), int(ccx + r - 1)):
        if c.get(x, lvl)[:3] in {q[:3] for q in R}:
            c.px(x, lvl, R[10])                                # 액면 반짝 줄
    # 목
    c.rect(cx - 3, by - 27, cx + 3, by - 21, SL[2]); c.vline(cx - 3, by - 27, by - 21, SL[3]); c.vline(cx + 3, by - 27, by - 21, SL[1])
    c.vline(cx - 2, by - 26, by - 22, SL[4])
    c.rect(cx - 4, by - 29, cx + 4, by - 28, SL[4]); c.hline(cx - 4, cx + 4, by - 29, SL[6])   # 입술 테
    # 코르크
    c.rect(cx - 3, by - 33, cx + 3, by - 30, WD[3]); c.hline(cx - 3, cx + 3, by - 33, WD[5]); c.vline(cx + 3, by - 33, by - 30, WD[1])
    c.px(cx - 1, by - 32, WD[4])
    # 검붉은 밀랍 — 입술 위로 덮고 목으로 한 줄 흘러내림
    c.rect(cx - 4, by - 31, cx + 4, by - 29, R[3]); c.hline(cx - 4, cx + 3, by - 31, R[5]); c.px(cx - 3, by - 31, R[7])
    c.vline(cx + 2, by - 28, by - 24, R[3]); c.px(cx + 2, by - 23, R[2]); c.vline(cx - 3, by - 28, by - 27, R[4])
    # 목 끈 + 작은 잔 패(놋쇠 — 호박 비발광)
    c.hline(cx - 3, cx + 3, by - 22, WD[4])
    c.line(cx + 3, by - 22, cx + 7, by - 17, WD[4])
    c.rect(cx + 6, by - 17, cx + 9, by - 14, A[20]); c.hline(cx + 6, cx + 9, by - 17, A[22]); c.px(cx + 9, by - 14, A[18])
    # 유리 빛(왼쪽 위 호 + 점) — 무채 밝은 색(비발광)
    for a in range(200, 262, 9):
        t = math.radians(a)
        c.px(int(round(ccx + math.cos(t) * (r - 3))), int(round(ccy + math.sin(t) * (r - 3))), G[13])
    c.px(ccx - 4, ccy - 7, G[14]); c.px(ccx - 3, ccy - 8, G[12])
    c.px(ccx + 6, ccy + 4, R[7])                                   # 오른쪽 아래 반사광
    outline_out(c.im, OUT)
    return c.im


# ---------------------------------------------------------------------------------------------- 화염 술병
def fire_bottle_rest(k=0):
    """목 긴 짙은 유리병(호박 술, 비발광) + 목의 헝겊 심지 + 심지 끝 작은 불(자체 발광, k 로 일렁임)."""
    c = Canvas(64, 64)
    cx, by = 32, 58
    # 몸
    c.rect(cx - 7, by - 17, cx + 7, by - 1, SL[2])
    c.rect(cx - 6, by - 18, cx + 6, by, SL[2])
    c.poly([(cx - 7, by - 17), (cx + 7, by - 17), (cx + 3, by - 24), (cx - 3, by - 24)], SL[2])
    c.rect(cx - 2, by - 31, cx + 2, by - 23, SL[2])
    c.vline(cx - 7, by - 17, by - 1, SL[3]); c.vline(cx - 2, by - 31, by - 24, SL[3])
    c.vline(cx + 7, by - 16, by - 1, SL[1]); c.vline(cx + 2, by - 31, by - 24, SL[1])
    # 술(아래 2/3) 호박 비발광
    for y in range(by - 11, by):
        for x in range(cx - 6, cx + 7):
            u = (x - cx) / 7.0
            s = 0.75 - 0.55 * u - 0.25 * (y - (by - 11)) / 11
            col = [A[18], A[19], A[20], A[21], A[22]][max(0, min(4, int(s * 5)))]
            c.px(x, y, col)
    c.hline(cx - 6, cx + 6, by - 12, A[22])
    c.hline(cx - 5, cx + 6, by - 1, A[18]); c.vline(cx + 6, by - 11, by - 1, A[18])
    # 유리 빛
    c.vline(cx - 5, by - 16, by - 4, G[11]); c.px(cx - 5, by - 17, G[13]); c.vline(cx - 1, by - 29, by - 25, G[9])
    # 헝겊 심지(병목에서 비죽 + 늘어진 끝) + 묶은 끈
    rag = [(cx - 2, by - 33), (cx + 2, by - 33), (cx + 6, by - 38), (cx + 8, by - 35), (cx + 3, by - 30), (cx - 2, by - 30)]
    c.poly(rag, WD[4]); c.line(cx - 2, by - 33, cx + 6, by - 38, WD[5]); c.line(cx - 1, by - 31, cx + 3, by - 31, WD[3])
    c.px(cx + 3, by - 30, WD[2]); c.px(cx + 7, by - 36, WD[1]); c.px(cx + 8, by - 35, WD[1]); c.px(cx + 6, by - 35, WD[2])   # 그을린 끝
    c.hline(cx - 3, cx + 3, by - 30, WD[1]); c.hline(cx - 3, cx + 3, by - 29, WD[3])
    # 잔 낙인 딱지(몸 위쪽, 바랜 종이)
    c.rect(cx - 4, by - 16, cx + 3, by - 12, PL[3]); c.hline(cx - 4, cx + 3, by - 16, PL[4])
    c.hline(cx - 3, cx + 2, by - 15, A[17]); c.hline(cx - 2, cx + 1, by - 14, A[17]); c.px(cx - 1, by - 13, A[17]); c.px(cx, by - 13, A[17])
    outline_out(c.im, OUT)
    # 불(외곽선 뒤에 그려 불꽃 테는 밝게)
    flame(c, cx + 7, by - 36, 8, 11 + (k % 3), seed=60 + (k % 4), tongues=2, core=False)
    c.px(cx + 7, by - 37, A[27]); c.px(cx + 8, by - 36, A[25])
    return c.im


# ---------------------------------------------------------------------------------------------- 종류 정의
KINDS = {
    "voucher": dict(rows=["small", "mid", "large"], bob=[0, 0, 1, 1, 1, 1, 0, 0],
                    ring=(A[25], A[23], A[21]), shadow_rx={"small": 13, "mid": 15, "large": 22}),
    "potion": dict(rows=["potion"], bob=[0, 1, 1, 2, 2, 2, 1, 0], ring=(R[10], R[8], R[6]), shadow_rx={"potion": 9}),
    "fire_bottle": dict(rows=["fire_bottle"], bob=[0, 1, 1, 2, 2, 2, 1, 0], ring=(A[25], A[23], A[21]),
                        shadow_rx={"fire_bottle": 8}),
}
LIGHT = lighten_map(P_FACE, P_EDGE, [A[17], A[18], A[19], A[20], A[21], A[22], A[23]], [R[3], R[4], R[5], R[6], R[8], R[9], R[10], R[11]],
                    [SL[1], SL[2], SL[3], SL[4], SL[6], SL[7]], [WD[1], WD[3], WD[4], WD[5]], step=1)


def rest_of(kind, row, k=0):
    if kind == "voucher":
        return voucher_rest(row)
    if kind == "potion":
        return potion_rest()
    return fire_bottle_rest(k)


# 반짝임 자리(바닥점 기준) — 종류·행별 2곳, idle 3·4·5 열에 별
SPARK = {"small": [(-8, -14), (9, -9)], "mid": [(-11, -18), (11, -10)], "large": [(-10, -28), (16, -17)],
         "potion": [(-5, -20), (6, -27)], "fire_bottle": [(-5, -20), (4, -28)]}


def _glint_sweep(im, phase, width=3):
    """물건 위를 왼쪽 위 → 오른쪽 아래로 지나가는 빛 띠: 띠 안 픽셀을 램프 한 단 밝게."""
    p = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            c = p[x, y]
            if c[3] != 255:
                continue
            v = x + y * 0.7 - phase
            if 0 <= v < width and c[:3] in LIGHT:
                p[x, y] = LIGHT[c[:3]]
    return im


def _place(c, im, off, h, sx=1.0, sy=1.0):
    """rest 그림 im(오프셋 off = 바닥점 기준 왼쪽 위)을 늘여 바닥점에서 h 만큼 띄워 놓는다(아래 가운데 고정)."""
    w0, h0 = im.size
    if (sx, sy) != (1.0, 1.0):
        nw, nh = max(1, int(round(w0 * sx))), max(1, int(round(h0 * sy)))
        im = im.resize((nw, nh), Image.NEAREST)
    else:
        nw, nh = w0, h0
    # 바닥점 아래 가운데 기준: 원래 그림 바닥(off[1]+h0)은 바닥점 근처
    cx0 = PIV[0] + off[0] + w0 / 2.0
    bot = PIV[1] - 1 + (off[1] + h0 - 0) - h
    x = int(round(cx0 - nw / 2.0))
    y = int(round(bot - nh))
    c.paste(im, x, y)


def _dust(c, t, seed, spread):
    """착지 먼지(불투명 작은 덩이) — t 0 퍼짐, 1 가라앉음."""
    r = Rand(seed)
    for k in range(8):
        side = -1 if k % 2 == 0 else 1
        x = PIV[0] + side * (spread + 2 + 4 * t + (k // 2) * 3 + r.i(0, 1))
        y = PIV[1] - (k // 2) % 2 - 1 * t
        rad = (2.2 - 1.0 * t - 0.3 * (k // 2)) * (0.8 + 0.3 * r.f())
        if rad < 0.7:
            c.px(int(x), int(y), PL[2])
            continue
        disc(c, x, y, rad * 1.3, PL[3] if t < 0.5 else PL[2], ky=0.45)
        c.px(int(x) - 1, int(y - 1), PL[4] if t < 0.5 else PL[3])


def _ring(c, cx, cy, r, cols, dash=1, ky=0.55):
    n = max(8, int(2 * math.pi * r))
    for i in range(n):
        if dash > 1 and (i // dash) % 2:
            continue
        a = 2 * math.pi * i / n
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r * ky
        c.px(int(round(x)), int(round(y)), cols[0] if math.sin(a) < 0.2 else cols[1])


def frames_for(kind, row):
    spec = KINDS[kind]
    rx = spec["shadow_rx"][row]
    ry = max(3, int(round(rx * 0.32)))
    ring = spec["ring"]
    rest0 = rest_of(kind, row, 0)
    im0, off0 = crop_rest(rest0)
    hgt = im0.size[1]
    out = []

    def base_frame(h, sx=1.0, sy=1.0, k=0, shadow=1.0, sweep=None, sparks=()):
        c = Canvas(FW, FH)
        if shadow > 0:
            contact_shadow(c, PIV[0], PIV[1] - 1, max(2, rx * shadow), max(1, ry * shadow))
        im, off = crop_rest(rest_of(kind, row, k)) if kind == "fire_bottle" else (im0.copy(), off0)
        if sweep is not None:
            im = _glint_sweep(im.copy(), sweep)
        _place(c, im, off, h, sx, sy)
        for (sx_, sy_, arm) in sparks:
            star(c, PIV[0] + sx_, PIV[1] + sy_ - h, arm, A[27], A[25], A[23])
        return c

    # idle: 둥실 + 빛 띠 지나감(2~5) + 별(3·4 / 6)
    sp = SPARK[row]
    for i in IDLE:
        h = spec["bob"][i]
        sweep = {2: -4, 3: 6, 4: 16, 5: 26}.get(i)
        sparks = []
        if i == 3:
            sparks.append((sp[0][0], sp[0][1], 1))
        if i == 4:
            sparks.append((sp[0][0], sp[0][1], 2))
        if i == 5:
            sparks.append((sp[0][0], sp[0][1], 1))
        if i == 6:
            sparks.append((sp[1][0], sp[1][1], 1))
        c = base_frame(h, k=i, shadow=1.0 - 0.06 * h, sweep=sweep, sparks=sparks)
        if kind == "voucher" and i not in (3, 4, 5, 6):   # 별이 없는 칸엔 모서리 한 점 반짝(자체 발광) — 어둠에서 자리 표시
            gx, gy = sp[1 - (i // 4) % 2]
            c.px(PIV[0] + gx, PIV[1] + gy - h, A[25] if i % 2 else A[24])
        out.append(c.im)
    # spawn: 바닥 팝(작게) → 늘어나며 솟음 → 꼭대기 → 떨어짐 → 착지 눌림 + 먼지 → 제자리
    seq = [(0, 0.55, 0.55), (10, 0.9, 1.18), (18, 1.0, 1.06), (22, 1.0, 1.0), (19, 1.0, 1.02), (10, 0.94, 1.12), (0, 1.22, 0.78), (0, 1.0, 1.0)]
    for j, (h, sx, sy) in enumerate(seq):
        c = base_frame(h, sx, sy, k=j, shadow=max(0.35, 1.0 - h / 30.0))
        if j == 0:   # 팝 섬광(백열) + 짧은 빛살
            cy = PIV[1] - 4
            star(c, PIV[0], cy - hgt // 3, 3, X0, X1, A[25])
            for dx, dy in ((-7, -2), (7, -2), (-5, -8), (5, -8)):
                c.px(PIV[0] + dx, cy + dy, A[25]); c.px(PIV[0] + dx + (1 if dx > 0 else -1), cy + dy - 1, A[23])
        if j == 1:
            _dust(c, 0.6, 71, rx * 0.5)   # 솟을 때 바닥에 남는 작은 먼지
        if j == 6:
            _dust(c, 0.0, 70, rx * 0.8)
        if j == 7:
            _dust(c, 1.0, 70, rx * 0.8)
            star(c, PIV[0] + sp[1][0], PIV[1] + sp[1][1], 1, A[27], A[25], A[23])
        out.append(c.im)
    # pickup: 눌림 → 위로 늘어남 → 가늘게 빨려 듦 + 백열 → 별 터짐 + 고리 → 고리 퍼짐 · 불티 → 남은 점
    cyc = PIV[1] - hgt // 2 - 8
    for j in range(6):
        if j == 0:
            c = base_frame(0, 1.16, 0.84, k=j, shadow=1.0)
        elif j == 1:
            c = base_frame(5, 0.72, 1.38, k=j, shadow=0.6)
        elif j == 2:
            c = base_frame(12, 0.36, 1.7, k=j, shadow=0.0)
            star(c, PIV[0], cyc, 3, X0, X1, ring[0])
        else:
            c = Canvas(FW, FH)
            if j == 3:   # 백열 알맹이 + 8갈래 짧은 빛살(고리 없음 — 조준점처럼 보이지 않게)
                disc(c, PIV[0], cyc, 2.2, X1)
                c.px(PIV[0], cyc, X0); c.px(PIV[0] - 1, cyc, X0); c.px(PIV[0], cyc - 1, X0)
                for a in range(8):
                    t = math.radians(22.5 + 45 * a)
                    for rr in range(5, 10):
                        col = ring[0] if rr < 7 else (ring[1] if rr < 9 else ring[2])
                        c.px(int(round(PIV[0] + math.cos(t) * rr)), int(round(cyc + math.sin(t) * rr * 0.8)), col)
            elif j == 4:
                _ring(c, PIV[0], cyc, 16, (ring[1], ring[2]), dash=3)
                for a in range(4):
                    t = math.radians(45 + 90 * a)
                    star(c, int(PIV[0] + math.cos(t) * 11), int(cyc - 4 + math.sin(t) * 8), 1, ring[0], ring[1], ring[2])
            else:
                for a in range(4):
                    t = math.radians(45 + 90 * a)
                    c.px(int(PIV[0] + math.cos(t) * 15), int(cyc - 8 + math.sin(t) * 10), ring[1])
                    c.px(int(PIV[0] + math.cos(t) * 15), int(cyc - 7 + math.sin(t) * 10), ring[2])
        out.append(c.im)
    # magnet: 그림자 없이 떠서 위(그린 축)로 늘어남 + 꼬리 속도선 — 시스템이 그린 축(위)을 주인공 쪽으로 돌림
    for j, (sx, sy) in enumerate([(0.82, 1.28), (0.88, 1.2)]):
        c = base_frame(8, sx, sy, k=j, shadow=0.0)
        for dx in (-5, 0, 5):
            ln = 2 + (j + abs(dx)) % 2
            y0 = PIV[1] - 5 + (2 if dx else 0) + 2 * j
            c.vline(PIV[0] + dx, y0, y0 + ln, ring[2] if dx else ring[1])
        out.append(c.im)
    assert len(out) == NCOL
    return out
