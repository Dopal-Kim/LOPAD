"""1층 양조 구역 v3 소품 — 개념도 brewery b · 테두리 북(증류소·화구) (술통 피라미드·기중기 술통·쇠 저장통·솥·밧줄·팔레트·손수레)."""
import math
from common import (Prop, L, SMALL, PIV, barrel, crate, sacks, crate_c, barrel_c, sack_c, debris_c)
from outer import crate_stack
from pk import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_NSTONE, R_STONE, R_CLOTH, R_COPPER, R_LIQ,
                contact, cyl, face, grain, shade_mask, mask, poly_mask, ell_mask, flame, embers, splash, qcol, lam)


def rope_coil():
    c = Canvas(SMALL, SMALL)
    contact(c, 64, 106, 34, 8)
    for k in range(4):
        rx, ry = 30 - k * 6, 11 - k * 2
        cy = 102 - k * 3
        for i in range(200):
            a = 2 * math.pi * i / 200
            x, y = 64 + rx * math.cos(a), cy + ry * math.sin(a)
            tw = ((i // 4) % 2)
            col = PL[3] if (math.sin(a) < 0 and tw) else (PL[2] if math.sin(a) < 0 else (PL[1] if tw else PL[0]))
            c.px(int(x), int(y), col); c.px(int(x), int(y) + 1, PL[0] if tw else WD[2])
            c.px(int(x), int(y) + 2, WD[1])
    # 늘어진 끝
    for k in range(26):
        x, y = 92 + k, 104 + int(3 * math.sin(k / 5))
        c.px(x, y, PL[2]); c.px(x, y + 1, PL[0]); c.px(x, y + 2, WD[1])
    return Prop("rope_coil", c, PIV, solid=False, occlude=None, maxPerRoom=2, weight=0.7, depth="floor")


def liquor_stain():
    c = Canvas(SMALL, SMALL)
    splash(c, 64, 100, 46, 13, ramp=[WD[1], A[16], A[17], A[18], A[19], A[21]], seed=29, blobs=9)
    return Prop("liquor_stain", c, PIV, solid=False, occlude=None, maxPerRoom=3, weight=1.0, depth="floor",
                note="술 얼룩(층 램프, 비발광 — 글린트 1점만 밝은 램프)")


def cauldron():
    """뜨거운 솥(광원) — 돌 화덕 위 쇠솥 + 불."""
    c = Canvas(SMALL, SMALL)
    contact(c, 64, 120, 40, 6)
    # 돌 화덕(앞면 아치 + 불)
    face(c, 30, 92, 98, 120, R_NSTONE, 0.45, grad=0.2)
    for y in (100, 110):
        c.hline(30, 98, y, G[1])
    for x in (40, 58, 76, 92):
        c.vline(x + (6 if (x // 18) % 2 else 0), 92, 120, G[1])
    m, d = mask(30, 22)
    d.pieslice((0, 0, 29, 40), 180, 360, fill=255)
    for y in range(22):
        for x in range(30):
            if m.getpixel((x, y)) > 127:
                c.px(49 + x, 100 + y, SL[0])
    flame(c, 64, 120, 24, 18, seed=33, tongues=3, core=True)
    # 솥(구 + 테)
    m = ell_mask(68, 44, (0, 0, 67, 43))
    shade_mask(c, m, R_IRON, ox=30, oy=54, base=0.45, gain=0.8, soft=6)
    for x in range(28, 101):
        u = (x - 64) / 36
        if abs(u) <= 1:
            y = 58 - int(6 * math.sqrt(1 - u * u))
            c.px(x, y, G[7] if u < 0 else G[5]); c.px(x, y + 1, G[3])
    # 끓는 술(윗면)
    for y in range(54, 64):
        for x in range(30, 99):
            if ((x - 64) / 33) ** 2 + ((y - 59) / 5) ** 2 <= 1:
                c.px(x, y, A[21] if y < 57 else (A[22] if (x * 3 + y * 5) % 13 else A[24]))
    for (x, y) in ((50, 52), (70, 50), (82, 53)):
        c.px(x, y, A[24]); c.px(x + 1, y - 1, A[24])
    return Prop("cauldron", c, PIV, occlude=28, maxPerRoom=1, weight=0.5,
                light=L("#e8a33c", 300, 1.0, 64, 70, 0.14, 5))


def pallet():
    c = Canvas(SMALL, SMALL)
    contact(c, 64, 114, 52, 6)
    face(c, 12, 88, 116, 98, R_WOODG, 0.8)
    for x in range(12, 117, 15):
        c.vline(x, 88, 98, WD[1])
    face(c, 12, 99, 116, 110, R_WOODG, 0.4, grad=0.2)
    for x in (14, 60, 106):
        face(c, x, 99, x + 9, 110, R_WOODG, 0.55)
    c.hline(12, 116, 88, PL[2]); c.hline(12, 116, 110, SL[0])
    return Prop("pallet", c, PIV, solid=False, occlude=None, maxPerRoom=1, weight=0.6, depth="floor")


def steam_vent():
    c = Canvas(SMALL, SMALL)
    face(c, 34, 92, 94, 112, R_IRON, 0.5)
    for x in range(38, 92, 6):
        c.vline(x, 95, 109, SL[0]); c.vline(x + 1, 95, 109, G[2])
    c.hline(34, 94, 92, G[7]); c.hline(34, 94, 112, G[1])
    # 김(반투명 흰 회색 덩어리)
    r = Rand(5)
    for k in range(6):
        cx, cy, rr = 64 + r.i(-10, 10), 88 - k * 12, 8 + k * 2
        for y in range(cy - rr, cy + rr):
            for x in range(cx - rr, cx + rr):
                d = ((x - cx) ** 2 + (y - cy) ** 2) / (rr * rr)
                if d < 1 and (x + y + k) % 2 == 0 and c.get(x, y)[3] == 0:
                    c.px(x, y, G[10][:3] + (int(90 * (1 - d) * (1 - k / 7)),))
    return Prop("steam_vent", c, PIV, solid=False, occlude=None, maxPerRoom=1, weight=0.5, depth="floor")


def barrel_pyramid():
    """술통 피라미드(3칸): 3-2-1 단, 통 끝이 보이게 눕힘."""
    c = Canvas(192, 176)
    contact(c, 96, 168, 90, 8)
    rr = 26
    rows = [(3, 168 - rr), (2, 168 - rr - 2 * rr + 6), (1, 168 - rr - 4 * rr + 12)]
    for (n, cy) in rows:
        x0 = 96 - (n - 1) * rr
        for k in range(n):
            cx = x0 + k * 2 * rr
            for y in range(cy - rr, cy + rr + 1):
                for x in range(cx - rr, cx + rr + 1):
                    d = math.hypot(x - cx, (y - cy))
                    if d <= rr:
                        u, v = (x - cx) / rr, (y - cy) / rr
                        s = 0.55 - 0.25 * u - 0.3 * v
                        if d > rr - 4:                      # 쇠테(끝 테)
                            c.px(x, y, qcol(R_IRON, s + 0.1, x, y))
                        else:
                            c.px(x, y, qcol(R_WOOD, s + 0.1, x, y))
            # 널 이음(평행)
            for j in (-12, -4, 4, 12):
                for y in range(cy - rr + 5, cy + rr - 4):
                    if math.hypot(j, y - cy) < rr - 5:
                        c.px(cx + j, y, WD[2])
            c.rect(cx - 2, cy - 2, cx + 2, cy + 2, WD[1]); c.px(cx - 2, cy - 2, WD[4])
            for k2 in range(rr * 4):
                a = 2 * math.pi * k2 / (rr * 4)
                c.px(int(cx + rr * math.cos(a)), int(cy + rr * math.sin(a)), SL[0])
    # 술 흘린 자국
    for y in range(140, 168):
        c.px(118, y, A[19]); c.px(119, y, A[18])
    return Prop("barrel_pyramid", c, (96, 168), footprint=(3, 1), occlude=80, placement="floor (벽 앞·구석)")


def crane_barrel():
    """기중기 + 쇠사슬에 매달린 술통 (기둥 1칸, 팔이 오른쪽 1.5칸 위로 뻗음)."""
    c = Canvas(160, 272)
    contact(c, 30, 264, 18, 5)
    contact(c, 112, 264, 30, 6, a=70)          # 매달린 통의 바닥 그림자(흐림)
    # 기둥
    face(c, 22, 30, 37, 262, R_WOOD, 0.55)
    c.vline(22, 30, 262, WD[4]); c.vline(37, 30, 262, WD[1])
    grain(c, 23, 31, 36, 261, R_WOOD, 71, vertical=True, density=0.1)
    face(c, 16, 248, 43, 264, R_NSTONE, 0.5)
    # 팔 + 버팀
    face(c, 14, 30, 140, 41, R_WOOD, 0.7); c.hline(14, 140, 30, WD[5]); c.hline(14, 140, 41, WD[0])
    for k in range(48):
        x, y = 38 + k, 100 - k
        for j in range(5):
            c.px(x + j, y, R_WOOD[4 - j // 2])
    # 도르래 + 사슬
    cyl(c, 116, 44, 52, 6, R_IRON, ry=2)
    for y in range(54, 150, 4):
        c.rect(115, y, 117, y + 2, G[5]); c.px(116, y + 1, SL[0]); c.px(116, y + 3, G[3])
    # 매달린 술통
    barrel_c(c, 116, 226, rx=24, h=56, seed=8, spill=False)
    c.hline(100, 132, 160, G[4])
    return Prop("crane_barrel", c, (30, 264), footprint=(1, 1), occlude=100, placement="floor (벽 앞)",
                note="통은 공중(충돌 없음, 기둥 1칸만 막힘). 그림자 흔들림은 시스템 선택")


def steel_vat():
    """쇠 저장통(2칸) — 리벳 띠 + 사다리 + 관."""
    c = Canvas(144, 224)
    contact(c, 72, 214, 64, 8)
    cyl(c, 72, 40, 196, 52, R_IRON, ry=18, staves=0, hoops=((70, 3), (130, 3), (180, 3)), lid=True,
        lid_ramp=[SL[0], G[2], G[3], G[5], G[7], G[9]])
    for (hy) in (72, 132, 182):
        for k in range(10):
            u = -0.9 + k * 0.2
            x = int(72 + u * 52)
            y = hy + int(18 * math.sqrt(max(0, 1 - u * u)) * 0.9) + 1
            c.px(x, y, G[9] if u < 0 else G[6])
    # 구리 뚜껑 밸브 + 관(층 램프)
    cyl(c, 80, 30, 40, 8, R_COPPER, ry=3)
    for x in range(88, 140):
        c.px(x, 34, A[21]); c.px(x, 35, A[19]); c.px(x, 36, A[17])
    # 사다리(앞면 왼쪽)
    for x in (34, 48):
        c.vline(x, 60, 212, WD[3]); c.vline(x + 1, 60, 212, WD[1])
    for y in range(68, 212, 14):
        c.hline(34, 49, y, WD[4]); c.hline(34, 49, y + 1, WD[2])
    # 꼭지 + 똑똑 떨어지는 술
    c.rect(96, 186, 104, 190, G[4]); c.px(100, 192, A[20]); c.px(100, 198, A[19])
    splash(c, 104, 212, 14, 3, seed=3, blobs=2, glint=False)
    return Prop("steel_vat", c, (72, 214), footprint=(2, 1), occlude=80, placement="floor (벽 앞·구석)")


def handcart():
    c = Canvas(160, 112)
    contact(c, 76, 104, 62, 6)
    # 짐칸 기울어진 상자
    m = poly_mask(160, 112, [(20, 40), (112, 46), (110, 82), (22, 78)])
    shade_mask(c, m, R_WOODG, base=0.45, gain=0.5, soft=2)
    m = poly_mask(160, 112, [(20, 30), (112, 36), (112, 46), (20, 40)])
    shade_mask(c, m, R_WOODG, base=0.75, gain=0.4, soft=1)
    for x in range(26, 112, 16):
        c.line(x, 40 + (x - 20) * 6 // 92, x, 80, WD[1])
    # 바퀴 하나(앞)
    for k in range(80):
        a = 2 * math.pi * k / 80
        for rr in (22, 21, 20):
            c.px(int(100 + rr * math.cos(a) * 0.5), int(82 + rr * math.sin(a)), WD[3] if math.cos(a) < 0 else WD[1])
    for k in range(6):
        a = 2 * math.pi * k / 6
        c.line(100, 82, int(100 + 19 * math.cos(a) * 0.5), int(82 + 19 * math.sin(a)), WD[2])
    # 손잡이 2개 + 받침 다리
    for dy in (0, 6):
        c.line(20, 60 + dy, 0 + 4, 50 + dy, WD[4]); c.line(20, 61 + dy, 4, 51 + dy, WD[2])
    c.line(30, 78, 26, 102, WD[3]); c.line(31, 78, 27, 102, WD[1])
    # 위 자루 하나
    sack_c(c, 46, 14, 40, 26, R_CLOTH, 9)
    return Prop("handcart", c, (70, 104), footprint=(2, 1), occlude=30, placement="floor")


def small():
    return [barrel(), crate(), sacks(), rope_coil(), liquor_stain(), cauldron(), pallet(), steam_vent()]


def big():
    return [barrel_pyramid(), crane_barrel(), steel_vat(), handcart(), crate_stack()]
