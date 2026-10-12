"""기억의 소품 4장(64×64, pixelScale 0.5 → 화면 32px) — 62 루프 2 스토리 팩(text-pack-63-loop2 memory.keepsakes) 이름·art 메모에 맞춤.

파일 id(시스템이 씀)는 그대로 두고 그림만 스토리 확정 물건으로:
- brokenCup  → 찌그러진 투구 (스토리 키 dentedHelm) — "옆이 찌그러진 쇠 투구"
- oldVoucher → 접힌 전표   (foldedVoucher)         — "네 번 접힌 전표 묶음"
- knotCord   → 닳은 매듭 끈 (knotCord)              — "매듭이 줄줄이 진 가죽 끈"
- inkBrush   → 먹 묻은 붓   (inkBrush)              — "끝이 먹에 젖은 가는 붓"

유품 카드(cards.py)와 같은 결: 좌상단 빛, 1층 램프 + v2 재질(SL·WD·PL) + gray, 바깥 1도트 외곽(selout), 반투명 접지 그림자, 투명 배경.
화면 32px 에서 읽히도록 덩어리는 굵게, 디테일은 2~3군데만.
"""
import math

from PIL import Image, ImageDraw

from kit2 import (Canvas, G, A, SL, WD, PL, R_WOOD, R_IRON, R_HELM, R_LEATHER, R_PAPER, R_INKB, contact, pol, ell,
                  cap, line, selout, shade_mask, qcol)

S = 64


def _mask(fn):
    m = Image.new("L", (S, S), 0)
    fn(ImageDraw.Draw(m))
    return m


def _lit(nx, ny, nz):
    n = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx * LX + ny * LY + nz * LZ) / n


_l = math.sqrt(0.5 ** 2 + 0.6 ** 2 + 0.62 ** 2)
LX, LY, LZ = -0.5 / _l, -0.6 / _l, 0.62 / _l      # 좌상단 앞 빛(바이블 · pk.L 과 같음)


# ---------------------------------------------------------------- 찌그러진 투구
def k_dentedHelm():
    c = Canvas(S, S)
    contact(c, 31, 51, 26, 7)
    CX, BY, RX, RY, H = 30, 41, 23, 8, 28        # 밑 테 타원 중심·반지름, 돔 높이
    DX, DY, DS, DD = 20, 28, 5.5, 0.0            # 찌그러진 자리(빛 받는 왼쪽 옆구리 — 그늘 쪽이면 안 읽힘) 중심·폭·깊이

    def dome(d):
        d.ellipse((CX - RX, BY - H, CX + RX, BY + H), fill=255)
        d.rectangle((0, BY + 1, S, S), fill=0)
        d.ellipse((CX - RX, BY - RY, CX + RX, BY + RY), fill=255)
        d.ellipse((1 - 12, DY - 12, 1 + 12, DY + 12), fill=0)         # 옆 실루엣이 얕게 꺼짐
    m = _mask(dome)
    mp = m.load()
    for y in range(S):
        for x in range(S):
            if mp[x, y] <= 127:
                continue
            nx, ny = (x - CX) / RX, (y - BY) / H
            nz = math.sqrt(max(0.02, 1 - nx * nx - ny * ny))
            d = _lit(nx * nz ** -0.5, ny * nz ** -0.5, nz)
            s = 0.02 + 0.86 * max(0.0, d) + 0.05 * (1 - (y - (BY - H)) / H)
            col = qcol(R_HELM, s, x, y, sharp=4.0)
            if d > 0.975 and math.hypot(x - DX, y - DY) > DS + 3:
                col = R_HELM[5]
            c.px(x, y, col)
    # 오목한 자국(직접 칠함): 빛(좌상)을 등진 안쪽 위·왼 벽 = 그늘, 빛을 보는 아래·오른 벽 = 밝음,
    # 눌려 솟은 테두리는 위·왼이 빛을 받고 아래·오른이 그늘.
    for y in range(DY - 12, DY + 13):
        for x in range(DX - 12, DX + 13):
            if not (0 <= x < S and 0 <= y < S) or mp[x, y] <= 127:
                continue
            dx, dy = (x - DX) / (DS * 1.25), (y - DY) / (DS * 0.85)       # 옆으로 납작하게 눌린 자국
            r = math.hypot(dx, dy)
            if r > 1.35:
                continue
            k = (dx + dy) / max(r, 1e-6) * 0.7071           # +1 = 아래·오른쪽, -1 = 위·왼쪽
            if r < 1.0:
                s = 0.44 + 0.24 * k * min(1.0, r * 1.6)
            else:
                s = 0.62 - 0.4 * k
            c.px(x, y, qcol(R_HELM, s, x, y, sharp=4.0))
    for (x, y) in ((22, 16), (23, 15), (24, 15), (22, 17), (21, 18)):   # 쇠 윤(자국 위)
        c.px(x, y, R_HELM[5])
    # 찌그러질 때 생긴 금(자국 가장자리에서 퍼짐) — 골 진하게 + 바로 위 밝게
    for (a, b) in (((22, 20), (27, 16)), ((23, 32), (28, 35)), ((18, 34), (19, 38))):
        line(c, a, b, R_HELM[1])
        line(c, (a[0], a[1] - 1), (b[0], b[1] - 1), R_HELM[5])
    # 앞 이음매 능선(돔 가운데)
    for y in range(BY - H + 2, BY - 3):
        c.px(CX - 4, y, R_HELM[5] if y < BY - 12 else R_HELM[4])
        c.px(CX - 3, y, R_HELM[2])
    # 밑 테(띠) — 앞 반 타원, 찌그러진 쪽은 살짝 들림 + 리벳
    def lift(x):
        return 2 if 10 <= x <= 18 else (1 if x in (9, 19) else 0)
    for x in range(CX - RX, CX + RX + 1):
        u = (x - CX) / RX
        yb = BY + RY * math.sqrt(max(0.0, 1 - u * u))
        for k in range(6):
            yy = int(round(yb - 5 + k)) - lift(x)
            s = 0.62 - 0.5 * (u + 1) / 2
            s = 0.98 if k == 0 else (s - 0.4 if k == 5 else s)
            c.px(x, yy, qcol(R_HELM, s, x, yy))
    for x in range(CX - RX + 4, CX + RX - 2, 6):
        u = (x - CX) / RX
        yy = int(round(BY + RY * math.sqrt(max(0.0, 1 - u * u)) - 2.5)) - lift(x)
        c.px(x, yy, R_HELM[5]); c.px(x + 1, yy + 1, R_HELM[1])
    # 코 가리개(앞 가운데 아래로)
    nx0 = CX - 5
    pol(c, [(nx0 - 2, BY + 3), (nx0 + 3, BY + 3), (nx0 + 2, BY + 13), (nx0 - 1, BY + 13)], R_HELM, base=0.6, gain=0.9, soft=1)
    c.vline(nx0 - 1, BY + 4, BY + 12, R_HELM[4])
    # 녹·흙 몇 점(시체 더미에서 굴러온 것)
    for (x, y, col) in ((41, 30, WD[2]), (42, 31, WD[1]), (22, 46, WD[2]), (38, 45, WD[1]), (39, 44, WD[2]), (35, 18, WD[2])):
        c.px(x, y, col)
    # 1층 빛(호박) 반짝임 하나
    c.px(25, 17, A[22]); c.px(26, 16, A[21]); c.px(24, 18, A[20])
    im = c.im
    selout(im)
    return im


# ---------------------------------------------------------------- 접힌 전표
def k_foldedVoucher():
    c = Canvas(S, S)
    contact(c, 33, 49, 27, 7)

    def slip(ox, oy, base, th=2, rot=0):
        top = [(8 + ox, 29 + oy + rot), (40 + ox, 16 + oy), (58 + ox, 31 + oy - rot), (26 + ox, 44 + oy)]
        c.poly([top[3], top[2], (top[2][0], top[2][1] + th), (top[3][0], top[3][1] + th)], PL[0])
        c.poly([top[0], top[3], (top[3][0], top[3][1] + th), (top[0][0], top[0][1] + th)], PL[2])
        line(c, (top[0][0], top[0][1] + th), (top[3][0], top[3][1] + th), PL[0])
        pol(c, top, R_PAPER, base=base, gain=0.4, soft=2)
        return top
    slip(-4, 7, 0.5, rot=2)
    slip(3, 4, 0.56, rot=-2)
    t = slip(0, 0, 0.68, th=3)
    # 접힌 금(열십자) — 골은 진하게, 옆 산은 밝게
    m1 = ((t[0][0] + t[1][0]) // 2, (t[0][1] + t[1][1]) // 2)
    m2 = ((t[2][0] + t[3][0]) // 2, (t[2][1] + t[3][1]) // 2)
    m3 = ((t[1][0] + t[2][0]) // 2, (t[1][1] + t[2][1]) // 2)
    m4 = ((t[3][0] + t[0][0]) // 2, (t[3][1] + t[0][1]) // 2)
    line(c, (m1[0] + 1, m1[1] + 1), (m2[0], m2[1] - 1), PL[0])
    line(c, (m1[0] + 2, m1[1] + 1), (m2[0] + 1, m2[1] - 1), PL[4])
    line(c, (m4[0] + 1, m4[1]), (m3[0] - 1, m3[1]), PL[0])
    line(c, (m4[0] + 1, m4[1] - 1), (m3[0] - 1, m3[1] - 1), PL[4])
    # 묶은 노끈(접힌 금 하나 아래로 비껴 한 바퀴)
    a0, a1 = (m4[0] - 1, m4[1] + 4), (m3[0] + 1, m3[1] + 4)
    line(c, a0, a1, WD[4])
    line(c, (a0[0], a0[1] + 1), (a1[0], a1[1] + 1), WD[2])
    c.vline(a0[0], a0[1], a0[1] + 4, WD[3])
    c.vline(a1[0], a1[1], a1[1] + 4, WD[1])
    # 매듭 + 늘어진 꼬리 둘
    kx, ky = (a0[0] + a1[0]) // 2 + 2, (a0[1] + a1[1]) // 2
    ell(c, (kx - 3, ky - 2, kx + 3, ky + 3), [SL[0], WD[1], WD[2], WD[3], WD[4], WD[5]], base=0.6, soft=1)
    line(c, (kx + 2, ky + 3), (kx + 6, ky + 11), WD[3])
    line(c, (kx - 1, ky + 3), (kx - 3, ky + 10), WD[2])
    # 잔 도장(호박, 반쯤 번짐) — 왼쪽 칸
    sx, sy = 17, 28
    for (dx, dy) in ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (0, 1), (4, 1), (1, 2), (3, 2), (2, 3), (2, 4), (1, 5), (2, 5), (3, 5)):
        c.px(sx + dx, sy + dy, A[18] if (dx * 3 + dy) % 4 else A[17])
    # 글줄 둘(먹) — 위 칸
    line(c, (30, 21), (38, 18), SL[2])
    line(c, (32, 24), (42, 20), SL[2])
    # 젖혀진 귀퉁이(오른쪽 위 — 접힌 종이임을 보여 줌)
    bx, by = t[1]
    pol(c, [(bx - 8, by + 4), (bx, by), (bx + 3, by + 8)], [SL[0], PL[0], PL[1], PL[2], PL[3]], base=0.35, soft=0)
    line(c, (bx - 8, by + 4), (bx + 3, by + 8), PL[4])
    im = c.im
    selout(im)
    return im


# ---------------------------------------------------------------- 닳은 매듭 끈
def k_knotCord():
    """손목에 감던 끈 — 느슨한 고리로 바닥에 놓이고 매듭 다섯이 고리를 따라 줄줄이, 꼬리 둘이 늘어진다."""
    c = Canvas(S, S)
    CX, CY, RX, RY = 30, 31, 21, 12
    R_STRAP = [SL[0], WD[1], WD[2], WD[3], WD[4], WD[5]]
    contact(c, CX + 2, CY + 6, RX + 4, RY + 4, a=70)

    def ring_pt(a):
        return CX + RX * math.cos(a), CY + RY * math.sin(a)

    def strap(pts, base):
        m = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(m)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            d.ellipse((min(x0, x1) - 2.0, min(y0, y1) - 2.0, max(x0, x1) + 2.0, max(y0, y1) + 2.0), fill=255)
        shade_mask(c, m, R_STRAP, base=base, gain=0.9, soft=1)
    # 뒤 반 고리(먼저, 조금 어둡게) → 앞 반 고리
    back = [ring_pt(math.pi + math.pi * i / 40) for i in range(41)]
    front = [ring_pt(math.pi * i / 40) for i in range(41)]
    strap(back, 0.5)
    strap(front, 0.64)
    # 꼬리 둘(앞 오른쪽 매듭에서 바닥으로 늘어짐)
    tails = ([(46, 40), (50, 46), (53, 52), (58, 55)], [(44, 41), (45, 48), (43, 54), (45, 59)])
    for tl in tails:
        pts = []
        for a, b in zip(tl, tl[1:]):
            pts += [(a[0] + (b[0] - a[0]) * k / 6, a[1] + (b[1] - a[1]) * k / 6) for k in range(7)]
        contact(c, tl[-1][0] + 1, tl[-1][1] + 2, 4, 2, a=90)
        strap(pts, 0.6)
    for (x, y), (dx0, dy0) in (((58, 55), (1, 0)), ((45, 59), (0, 1))):
        for k, (dx, dy) in enumerate(((2, -1), (2, 1), (1, 2), (3, 0))):
            c.px(x + dx * dx0 + dy * dy0 + (dx if dy0 else 0), y + dy * dx0 + dx * dy0, WD[4] if k % 2 else WD[2])
    # 닳은 자리(가죽 겉이 일어나 밝다)
    for i in range(3, 40, 7):
        x, y = front[i]
        c.px(int(x), int(y) - 1, PL[2])
    for i in range(5, 40, 9):
        x, y = back[i]
        c.px(int(x), int(y) - 1, WD[5])
    # 매듭 다섯 — 고리를 따라 줄줄이(뒤 둘 → 앞 셋 순)
    knots = [(math.radians(a), base) for a, base in ((215, 0.5), (295, 0.52), (25, 0.6), (95, 0.62), (160, 0.6))]
    for j, (a, base) in enumerate(sorted(knots, key=lambda k: math.sin(k[0]))):
        x, y = ring_pt(a)
        x, y = int(round(x)), int(round(y))
        ell(c, (x - 5, y - 5, x + 5, y + 4), R_LEATHER, base=base, gain=1.0, soft=2)
        line(c, (x - 4, y + 2), (x + 2, y - 4), WD[0])          # 감아 넘긴 골
        line(c, (x - 3, y + 2), (x + 3, y - 4), WD[5])          # 감긴 띠 윗날
        c.px(x - 3, y - 2, PL[2]); c.px(x - 2, y - 3, WD[5])
    c.px(34, 41, A[21]); c.px(35, 41, A[20])                     # 1층 빛 한 점(앞 매듭)
    im = c.im
    selout(im)
    return im


# ---------------------------------------------------------------- 먹 묻은 붓
def k_inkBrush():
    c = Canvas(S, S)
    ax, ay, bx, by = 25, 39, 59, 7             # 대: 물림 → 꼭지
    for k in range(0, 41, 4):
        t = k / 40
        contact(c, ax + (bx - ax) * t + 1, ay + (by - ay) * t + 4, 4, 2, a=95)
    contact(c, 16, 54, 10, 3, a=95)
    # 먹 자국(붓끝이 닿은 자리, 작게)
    for y in range(52, 61):
        for x in range(3, 24):
            dd = math.hypot((x - 12) / 9.5, (y - 56.5) / 3.6)
            if dd < 1 and ((x * 7 + y * 3) % 13) > 1:
                c.px(x, y, G[1] if dd < 0.7 else G[2])
    c.px(7, 55, G[4]); c.px(8, 55, G[3])
    # 대(가는 대나무) — 캡슐 셰이딩 + 마디 셋
    cap(c, [(ax, ay), (bx, by)], 1.7, R_WOOD, base=0.55, gain=0.9, soft=1)
    for t in (0.3, 0.58, 0.84):
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        line(c, (int(x) - 1, int(y) - 2), (int(x) + 2, int(y) + 1), R_WOOD[1])
        c.px(int(x) - 1, int(y) - 1, R_WOOD[5])
    # 물림(감은 실)
    pol(c, [(20, 40), (24, 35), (29, 40), (25, 45)], [SL[0], WD[1], WD[2], WD[3], WD[4]], base=0.55, gain=0.9, soft=1)
    line(c, (22, 41), (26, 37), WD[1]); line(c, (23, 43), (27, 39), WD[1])
    # 털: 뿌리(마른 담색) → 끝(먹에 젖은 검정, 뾰족)
    tuft = [(20, 41), (25, 45), (21, 50), (14, 55), (9, 57), (12, 52), (17, 45)]
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).polygon(tuft, fill=255)
    mp = m.load()
    for y in range(S):
        for x in range(S):
            if mp[x, y] <= 127:
                continue
            dist = math.hypot(x - 23, y - 43)          # 물림에서 거리
            lit = (x - y) > -26                        # 위·오른쪽 가장자리가 빛 쪽(대략)
            if dist < 5:
                col = PL[3] if lit else PL[1]
            elif dist < 7:
                col = PL[1] if (x + y) % 2 else G[3]
            else:
                col = G[2] if lit else G[1]
            c.px(x, y, col)
    line(c, (19, 47), (12, 54), G[5])                  # 젖은 털 윤
    c.px(18, 47, G[6])
    # 떨어지는 먹 방울
    c.px(9, 59, G[1]); c.px(9, 60, G[0])
    # 1층 빛(호박) 한 점 — 대 위
    c.px(44, 20, A[22]); c.px(45, 19, A[21])
    im = c.im
    selout(im)
    return im


KEEPSAKES = {
    # 파일 id: (그리는 함수, 스토리 키, 이름, 메모)
    "brokenCup": (k_dentedHelm, "dentedHelm", "찌그러진 투구", "옆이 찌그러진 쇠 투구 — 생마다 첫 피격 피해 0(한 번)"),
    "oldVoucher": (k_foldedVoucher, "foldedVoucher", "접힌 전표", "네 번 접힌 전표 묶음(노끈·잔 도장) — 시작 전표 +n"),
    "knotCord": (k_knotCord, "knotCord", "닳은 매듭 끈", "매듭 다섯이 줄줄이 진 가죽 끈 — 대쉬 충전 +1"),
    "inkBrush": (k_inkBrush, "inkBrush", "먹 묻은 붓", "끝이 먹에 젖은 가는 붓 — 첫 개성 발현 카드 +1"),
}
