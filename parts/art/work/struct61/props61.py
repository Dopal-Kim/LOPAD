"""61라운드 방 다양화용 소품 군 — 지역마다 2~4종을 v3 소품 시트(tiles/v3/stage1_<region>_props, 계약 §14)에 덧붙인다.

규칙(props_v3 와 같음): 소품(props) = 128×128 칸 · pivot (64,120) · 바닥 데칼형은 depth floor. 큰 소품(bigProps) = rect·pivot(발자국 맨 아래 줄 가운데)·
footprint·solid·occludeAbove·placement. 새 항목에 `added61: true` · `variantTag`(방 배치 변주용 묶음 이름 제안)를 단다.
기존 그림·rect 는 한 픽셀도 바꾸지 않는다(시트 아래에 새 줄을 덧붙임).
"""
import math

from s61 import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_STONE, R_WSTONE, R_NSTONE, R_CLOTH,  # noqa: F401
                 R_CLOTHG, R_EARTH, R_LIQ, R_COPPER, R_BONE, R_GLASS, contact, cyl, plank_box, shade_mask, mask, splash,
                 stone_blob, face, grain, ell_mask, poly_mask, qcol, lam, flame, embers, glass_lantern)
from common import Prop, L, SMALL, PIV, barrel_c, crate_c, sack_c, tipped_barrel_c, debris_c  # props_v3
import hall as p_hall  # props_v3
import waste as p_waste  # props_v3
import structs  # bundle2
from structs61 import warm_flame, R_WOODD  # noqa: F401


def wheel(c, cx, cy, r, squash=0.55, spokes=6, ramp=R_WOOD, broken=False):
    for k in range(80):
        a = 2 * math.pi * k / 80
        if broken and 0.3 < a < 1.3:
            continue
        for rr in (r, r - 1, r - 2):
            x, y = int(round(cx + rr * math.cos(a) * squash)), int(round(cy + rr * math.sin(a)))
            c.px(x, y, ramp[4] if math.cos(a) < 0 else ramp[1])
    for k in range(spokes):
        a = 2 * math.pi * k / spokes + 0.3
        if broken and k == 1:
            continue
        c.line(cx, cy, int(cx + (r - 2) * math.cos(a) * squash), int(cy + (r - 2) * math.sin(a)), ramp[2])
    c.rect(cx - 2, cy - 2, cx + 2, cy + 2, G[4]); c.px(cx - 1, cy - 1, G[7])


# ====================================================================== 외곽 거리
def outer_broken_cart():
    """무너진 손수레: 바퀴 하나 빠져 짐칸이 기울고 술통·자루가 쏟아짐(불 없음 — 황무지 수레와 다름)."""
    c = Canvas(176, 144)
    contact(c, 90, 136, 76, 8)
    pts = [(20, 60), (138, 74), (140, 108), (22, 92)]
    m = poly_mask(176, 144, pts)
    shade_mask(c, m, R_WOODG, base=0.45, gain=0.5, soft=2, sharp=2)
    m = poly_mask(176, 144, [(20, 48), (138, 62), (138, 74), (20, 60)])
    shade_mask(c, m, R_WOODG, base=0.72, gain=0.4, soft=1, sharp=2)
    for k in range(5):
        x0 = 20 + k * 29
        c.line(x0, 60 + int(k * 3.4), x0, 92 + int(k * 3.4), WD[1])
    grain(c, 22, 50, 136, 104, R_WOODG, 9, vertical=False, density=0.06)
    wheel(c, 44, 108, 22)
    wheel(c, 140, 128, 24, squash=1.0, broken=True)                         # 빠져 누운 바퀴(납작하게)
    for y in range(120, 136):
        pass
    c.line(20, 86, 2, 112, WD[3]); c.line(20, 87, 2, 113, WD[1])              # 끌채
    tipped_barrel_c(c, 112, 96, length=46, r_=16, spill=True, seed=6)        # 쏟아진 술통
    sack_c(c, 60, 34, 34, 24, R_CLOTH, 3)
    sack_c(c, 88, 40, 30, 20, R_CLOTHG, 4)
    return Prop("broken_cart", c, (88, 136), footprint=(2, 1), occlude=36, placement="floor (가장자리·골목 입구)",
                note="61라운드 방 변주: 바퀴 빠져 기운 손수레 + 쏟아진 술통·자루")


def outer_laundry_line():
    """빨래줄: 양끝 장대 2 + 늘어진 줄 + 걸린 천 4장(바닥에 섬 — 지나갈 수 있음, 장대만 그림)."""
    c = Canvas(192, 176)
    for (px_, top) in ((10, 30), (180, 36)):
        contact(c, px_ + 2, 168, 8, 3)
        for y in range(top, 168):
            c.px(px_ - 1, y, WD[4]); c.px(px_, y, WD[3]); c.px(px_ + 1, y, WD[2]); c.px(px_ + 2, y, WD[1])
        c.rect(px_ - 3, top - 2, px_ + 4, top + 1, WD[3])
        stone_blob(c, px_ + 1, 166, 6, 3, R_WSTONE, px_)
    x0, y0, x1, y1 = 11, 34, 181, 40
    def line_y(x):
        t = (x - x0) / (x1 - x0)
        return y0 + (y1 - y0) * t + 14 * math.sin(math.pi * t)
    for x in range(x0, x1 + 1):
        c.px(x, int(line_y(x)), PL[2]); c.px(x, int(line_y(x)) + 1, WD[1])
    cloths = [(28, 26, 40, R_CLOTH), (62, 30, 52, R_CLOTHG), (104, 22, 36, [SL[1], A[16], A[17], A[18], A[19], WD[4]]), (134, 32, 48, R_CLOTH)]
    for (cx0, w, h, ramp) in cloths:
        ya = int(line_y(cx0)); yb = int(line_y(cx0 + w))
        pts = [(cx0, ya), (cx0 + w, yb), (cx0 + w - 2, yb + h - 6), (cx0 + w // 2, yb + h), (cx0 + 2, ya + h - 4)]
        m = poly_mask(192, 176, pts)
        shade_mask(c, m, ramp, base=0.5, gain=0.7, soft=3, sharp=2)
        for k in range(3):
            xx = cx0 + 4 + k * w // 3
            c.line(xx, int(line_y(xx)) + 3, xx + 1, int(line_y(xx)) + h - 8, ramp[1])
        for xx in (cx0 + 2, cx0 + w - 3):                                     # 빨래집게
            c.rect(xx, int(line_y(xx)) - 2, xx + 1, int(line_y(xx)) + 2, WD[4])
    return Prop("laundry_line", c, (96, 168), footprint=(3, 1), solid=False, occlude=60,
                placement="floor (방 가장자리·벽과 나란히) — 통과 가능(장대 2만 그림)",
                note="61라운드 방 변주: 바닥에 세운 빨래줄(외곽 v3 washing_line 은 벽 윗단 겹침용 — 이것은 바닥형)")


def outer_fallen_sign():
    """떨어진 선술집 간판(바닥, 통과): 부서진 판 + 잔 그림 + 끊어진 쇠사슬."""
    c = Canvas(SMALL, SMALL)
    m = poly_mask(SMALL, SMALL, [(22, 86), (96, 76), (106, 104), (30, 114)])
    shade_mask(c, m, R_WOOD, base=0.55, gain=0.5, soft=2, sharp=2)
    c.line(22, 86, 96, 76, WD[5]); c.line(30, 114, 106, 104, WD[0])
    c.line(60, 82, 66, 108, WD[1])                                           # 금 간 판
    for (dx, dy) in [(d, 0) for d in range(-6, 7)] + [(-4, 2), (4, 2), (-2, 4), (2, 4), (0, 6), (0, 8), (-3, 10), (-2, 10), (-1, 10), (0, 10), (1, 10), (2, 10), (3, 10)]:
        c.px(76 + dx, 86 + dy, A[19])
    for k in range(7):
        x, y = 30 + k * 3, 80 - k * 3
        c.px(x, y, G[7]); c.px(x + 1, y + 1, G[4])
    debris_c(c, 70, 112, 40, 8, 9, ramp=R_WSTONE, pottery=False)
    return Prop("fallen_sign", c, PIV, solid=False, maxPerRoom=1, weight=0.5, depth="floor",
                note="61라운드 방 변주: 바닥에 떨어진 간판(잔 그림) — 통과")


# ====================================================================== 양조 구역
def brew_still_column():
    """증류관: 구리 증류탑 + 감긴 냉각관(뱀관) + 받이 통. 1칸 막힘, 키 큼."""
    c = Canvas(128, 240)
    contact(c, 66, 232, 40, 7)
    RC = [SL[0], A[16], A[17], A[18], A[19], A[20]]                          # 오래 그을린 구리(밝은 칸 2단 낮춤)
    cyl(c, 54, 60, 196, 18, RC, ry=7, staves=0, hoops=((90, 3), (140, 3), (186, 3)), hoop_ramp=R_IRON)
    cyl(c, 54, 48, 60, 10, RC, ry=4)                                         # 꼭대기 돔
    for y in range(20, 48):                                                  # 백조목 관
        c.px(54, y, A[20]); c.px(55, y, A[18])
    for k in range(30):
        a = math.pi * k / 29
        x, y = int(76 + 22 * math.cos(math.pi - a)), int(20 - 10 * math.sin(a))
        c.px(x, y, A[20]); c.px(x, y + 1, A[17])
    for k in range(6):                                                       # 뱀관(냉각 코일) — 오른쪽
        yy = 70 + k * 18
        for x in range(82, 110):
            u = (x - 96) / 14
            c.px(x, yy + int(4 * u * u), A[21] if k % 2 == 0 else A[19]); c.px(x, yy + int(4 * u * u) + 1, A[17])
    for y in range(20, 180):
        c.px(98, y, A[18]); c.px(99, y, A[16])
    barrel_c(c, 100, 232, rx=16, h=32, seed=5, spill=False)                 # 받이 통
    for y in range(180, 196):
        c.px(100, y, A[22] if y % 4 == 0 else A[20])                         # 떨어지는 술 줄기(비발광)
    # 받침 벽돌 + 아궁이 잔불
    for y in range(204, 232):
        for x in range(30, 80):
            br = (y // 7) % 2
            q = 2 if ((x + br * 6) % 12 == 0 or y % 7 == 0) else 4
            c.px(x, y, [SL[0], WD[1], WD[2], A[17], WD[3], A[18]][q])
    c.rect(44, 216, 64, 231, SL[0])
    warm_flame(c, 54, 230, 16, 12, seed=4, tongues=3)
    return Prop("still_column", c, (54, 232), footprint=(1, 1), occlude=100, placement="floor (벽 앞·구석)",
                light=L("#e8a33c", 200, 0.8, 54, 220, 0.15, 6), note="61라운드 방 변주: 구리 증류탑 + 뱀관 + 받이 통(아궁이 잔불)")


def brew_liquor_sacks():
    """술 자루: 엿기름·누룩 자루 더미 + 젖은 얼룩(호박)."""
    c = Canvas(SMALL, SMALL)
    contact(c, 64, 118, 44, 7)
    splash(c, 80, 112, 20, 5, seed=3, blobs=4, glint=False)
    sack_c(c, 16, 74, 42, 42, R_CLOTH, 11)
    sack_c(c, 56, 70, 46, 46, R_CLOTHG, 12)
    sack_c(c, 34, 46, 40, 34, R_CLOTH, 13)
    for (x, y) in ((70, 96), (72, 100), (28, 102)):                          # 젖어 번진 술
        c.rect(x, y, x + 5, y + 2, A[17]); c.px(x + 1, y, A[18])
    for k in range(4):                                                       # 흘린 낟알
        c.px(40 + k * 7, 118, PL[3]); c.px(42 + k * 7, 117, A[19])
    return Prop("liquor_sacks", c, PIV, occlude=22, maxPerRoom=2, weight=0.7, note="61라운드 방 변주: 술 빚는 자루 더미(젖은 얼룩)")


def brew_mash_tub():
    """술 거르는 큰 나무 통(뚜껑 없음) — 안에 끓는 술밑(거품), 걸쳐 놓은 휘젓개."""
    c = Canvas(176, 144)
    contact(c, 90, 138, 76, 9)
    cyl(c, 88, 72, 118, 64, R_WOOD, bulge=0.02, ry=24, staves=12, seed=7, hoops=((84, 3), (108, 3)), lid=False)
    for y in range(72 - 24, 72 + 25):                                        # 통 입 + 술밑 면
        for x in range(88 - 64, 88 + 65):
            d = ((x + 0.5 - 88) / 64) ** 2 + ((y + 0.5 - 72) / 24) ** 2
            if d <= 1:
                if d > 0.86:
                    c.px(x, y, R_WOOD[5] if y < 72 else R_WOOD[2])
                else:
                    n = math.sin(x * 0.3) * math.sin(y * 0.5)
                    c.px(x, y, A[18] if n > 0.35 else (A[17] if n > -0.4 else WD[2]))
    for k in range(9):                                                       # 거품
        x, y = 50 + (k * 37) % 76, 64 + (k * 11) % 16
        c.ellipse((x - 2, y - 1, x + 2, y + 1), PL[3]); c.px(x - 1, y - 1, G[12])
    c.line(30, 40, 132, 84, WD[4]); c.line(30, 41, 132, 85, WD[2])          # 휘젓개(노)
    c.ellipse((120, 78, 140, 90), WD[3])
    return Prop("mash_tub", c, (88, 138), footprint=(2, 1), occlude=40, placement="floor",
                note="61라운드 방 변주: 술밑 거르는 큰 나무 통(거품) + 휘젓개")


def brew_bottle_crate():
    """병 상자: 짚 깐 나무 상자에 술병(어두운 유리·호박 술) + 옆에 쓰러진 병."""
    c = Canvas(SMALL, SMALL)
    contact(c, 66, 118, 40, 6)
    plank_box(c, 26, 70, 76, 30, 18, ramp=R_WOODG, seed=8, planks=4, slats=True, brace=False)
    for k in range(5):                                                       # 병 목
        bx = 34 + k * 14
        for y in range(52, 80):
            half = 1 if y < 62 else 4
            for x in range(bx - half, bx + half + 1):
                col = qcol(R_GLASS, 0.75 - 0.5 * (x - bx) / max(1, half), x, y)
                if y > 68 and k % 2 == 0:
                    col = A[19] if x > bx else A[21]
                c.px(x, y, col)
        c.rect(bx - 1, 49, bx + 1, 52, WD[3])
    for x in range(28, 100):
        c.px(x, 80, PL[2] if x % 3 else A[19])                               # 짚
    p_hall.bottle(c, 98, 120, tipped=True)
    return Prop("bottle_crate", c, PIV, occlude=22, maxPerRoom=2, weight=0.6, note="61라운드 방 변주: 술병 상자")


# ====================================================================== 연회장
def hall_overturned_table():
    """엎어진 식탁: 옆으로 쓰러진 상판(아랫면·다리가 보임) + 흩어진 식탁보·잔·접시 — 엄폐."""
    c = Canvas(176, 160)
    contact(c, 88, 152, 78, 8)
    # 상판(세워진 판 — 아랫면이 앞으로)
    face(c, 20, 52, 156, 128, R_WOODD, 0.42, grad=0.15)
    for x in range(20, 157, 17):
        c.vline(x, 52, 128, R_WOODD[1])
    c.hline(20, 156, 52, R_WOOD[4]); c.hline(20, 156, 128, R_WOODD[0]); c.vline(156, 52, 128, R_WOODD[0]); c.vline(20, 52, 128, R_WOOD[3])
    c.rect(28, 60, 148, 66, R_WOOD[2]); c.hline(28, 148, 60, R_WOOD[4])      # 앞치마 판(가장자리 띠)
    c.rect(28, 112, 148, 118, R_WOOD[2]); c.hline(28, 148, 118, R_WOODD[0])
    for (x0, y0) in ((34, 64), (138, 64), (34, 112), (138, 112)):           # 다리(보는 쪽으로 뻗어 나옴 — 짧게 줄여 보임)
        for k in range(18):
            for d in range(-4, 5):
                c.px(x0 + d, y0 + k, R_WOOD[4] if d < -1 else (R_WOOD[3] if d < 2 else R_WOOD[1]))
        c.ellipse((x0 - 5, y0 + 15, x0 + 5, y0 + 21), R_WOOD[5]); c.ellipse((x0 - 3, y0 + 16, x0 + 3, y0 + 20), R_WOOD[3])
    # 식탁보(위 모서리에서 흘러내림)
    m = poly_mask(176, 160, [(36, 44), (120, 44), (128, 58), (96, 64), (60, 60), (40, 62)])
    shade_mask(c, m, p_hall.R_LINEN, base=0.55, gain=0.6, soft=2)
    splash(c, 128, 146, 30, 7, ramp=[SL[0], A[16], A[16], A[17], A[17], A[18]], seed=6, blobs=6, glint=False)
    p_hall.goblet(c, 60, 146, tipped=True)
    c.ellipse((92, 138, 112, 146), G[6]); c.ellipse((94, 139, 110, 145), G[8])
    return Prop("overturned_table", c, (88, 152), footprint=(2, 1), occlude=60, placement="floor (엄폐 — 방 가운데 쪽)",
                note="61라운드 방 변주: 옆으로 쓰러진 연회 식탁(아랫면·다리) + 흘러내린 식탁보·엎질러진 술")


def hall_broken_chair():
    c = Canvas(SMALL, SMALL)
    contact(c, 64, 116, 30, 5)
    m = poly_mask(SMALL, SMALL, [(36, 92), (80, 86), (88, 100), (44, 108)])  # 쓰러진 의자 좌판
    shade_mask(c, m, R_WOOD, base=0.55, gain=0.5, soft=2)
    for (a, b) in (((40, 104), (30, 118)), ((84, 98), (98, 112)), ((60, 90), (52, 60)), ((76, 88), (72, 58))):
        c.line(a[0], a[1], b[0], b[1], WD[3]); c.line(a[0] + 1, a[1], b[0] + 1, b[1], WD[1])
    c.line(50, 60, 74, 56, WD[4]); c.line(50, 61, 74, 57, WD[2])             # 등받이 가로대
    for (x, y) in ((20, 114), (100, 118), (90, 108)):                          # 부러진 다리 조각
        c.line(x, y, x + 10, y - 2, WD[3])
    return Prop("broken_chair", c, PIV, occlude=20, maxPerRoom=2, weight=0.6, note="61라운드 방 변주: 쓰러져 부서진 의자")


def hall_spilled_platter():
    c = Canvas(SMALL, SMALL)
    splash(c, 64, 100, 34, 10, ramp=[SL[0], A[16], A[16], A[17], A[17], A[18]], seed=12, blobs=7, glint=False)
    c.ellipse((34, 84, 74, 104), G[5]); c.ellipse((36, 85, 72, 102), G[7]); c.ellipse((40, 88, 68, 100), G[6])  # 은쟁반
    c.ellipse((44, 86, 58, 96), WD[4]); c.hline(46, 56, 87, WD[5])            # 빵
    for (x, y) in ((76, 104), (88, 96), (26, 108)):                            # 굴러간 과일
        c.ellipse((x - 4, y - 3, x + 4, y + 3), A[18]); c.px(x - 2, y - 2, A[21])
    p_hall.goblet(c, 82, 90, tipped=True)
    return Prop("spilled_platter", c, PIV, solid=False, maxPerRoom=2, weight=0.8, depth="floor",
                note="61라운드 방 변주: 엎어진 은쟁반·빵·과일·잔 + 포도주(비발광)")


def hall_fallen_candelabra():
    c = Canvas(SMALL, SMALL)
    contact(c, 64, 112, 42, 4)
    R_GOLD = p_hall.R_GOLD
    for k in range(70):                                                        # 쓰러진 대
        x, y = 20 + k, 104 - k // 6
        c.px(x, y, R_GOLD[4]); c.px(x, y + 1, R_GOLD[2]); c.px(x, y + 2, R_GOLD[1])
    c.ellipse((10, 98, 26, 112), R_GOLD[2]); c.ellipse((12, 99, 24, 109), R_GOLD[4])   # 받침
    for (x, y) in ((90, 88), (96, 94)):                                        # 꺼진 초
        c.rect(x, y, x + 10, y + 3, PL[4]); c.hline(x, x + 10, y + 3, PL[2]); c.px(x + 11, y + 1, SL[0])
    for (x, y) in ((70, 108), (80, 112)):                                       # 녹은 촛농
        c.ellipse((x - 4, y - 2, x + 4, y + 2), PL[3])
    return Prop("fallen_candelabra", c, PIV, solid=False, maxPerRoom=1, weight=0.5, depth="floor",
                note="61라운드 방 변주: 쓰러진 놋쇠 촛대(꺼짐 — 빛 없음)")


# ====================================================================== 황무지
def waste_dead_tree():
    """죽은 나무: 갈라진 줄기 + 앙상한 가지 + 걸린 찢긴 천. 1칸 막힘, 키 큼."""
    c = Canvas(160, 256)
    contact(c, 80, 248, 30, 7)
    p_waste.mound(c, 78, 250, 26, 7, 4)
    TR = [SL[0], WD[0], WD[1], WD[2], PL[0], PL[1]]

    def limb(x0, y0, x1, y1, w0, w1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n + 1):
            t = k / n
            x = x0 + (x1 - x0) * t + math.sin(t * 5 + x0) * 2
            y = y0 + (y1 - y0) * t
            w = w0 + (w1 - w0) * t
            for d in range(-int(w), int(w) + 1):
                u = d / max(1, w)
                c.px(int(x + d), int(y), TR[max(0, min(5, 3 + (1 if u < -0.4 else 0) - (2 if u > 0.5 else 0)))])
    limb(78, 248, 74, 120, 9, 6)
    limb(74, 124, 40, 60, 5, 1.5)
    limb(76, 130, 118, 70, 5, 1.5)
    limb(74, 120, 80, 30, 4, 1)
    limb(48, 76, 22, 66, 2, 1)
    limb(110, 80, 136, 52, 2, 1)
    limb(78, 60, 96, 40, 2, 1)
    for y in range(160, 240, 9):                                                 # 줄기 갈라짐
        c.px(78 + (y % 3) - 1, y, SL[0]); c.px(78 + (y % 3) - 1, y + 1, SL[0])
    m = poly_mask(160, 256, [(112, 76), (126, 72), (124, 100), (118, 96), (114, 108)])
    shade_mask(c, m, [SL[0], SL[1], A[16], A[17], WD[3]], base=0.5, gain=0.6, soft=2)
    return Prop("dead_tree", c, (78, 248), footprint=(1, 1), occlude=80, placement="floor (가장자리·둑 앞)",
                note="61라운드 방 변주: 앙상한 죽은 나무 + 가지에 걸린 찢긴 깃발 천")


def waste_arrows_stuck():
    c = Canvas(SMALL, SMALL)
    r = Rand(3)
    for k in range(9):                                                         # 땅에 박힌 화살(기울기 제각각)
        x = 18 + r.i(0, 88); y = 84 + r.i(0, 30)
        dx = r.i(-8, 8); ln = r.i(18, 30)
        c.line(x, y, x + dx, y - ln, WD[4]); c.line(x + 1, y, x + dx + 1, y - ln, WD[2])
        for j in range(5):
            c.px(x + dx - 2 + (j % 2), y - ln + j, PL[3]); c.px(x + dx + 2, y - ln + j, PL[2])
        c.px(x, y + 1, WD[1]); c.px(x + 1, y + 1, WD[0])
    return Prop("arrows_stuck", c, PIV, solid=False, maxPerRoom=2, weight=0.8, depth="floor",
                note="61라운드 방 변주: 쏟아진 화살 비의 흔적(땅에 박힌 화살 9) — 통과(사수 노드 예고)")


def waste_pavise_row():
    """방패벽: 땅에 세운 큰 방패(파비스) 3장 + 받침대 — 엄폐 2칸."""
    c = Canvas(176, 160)
    contact(c, 88, 150, 74, 7)
    for k, x0 in enumerate((14, 64, 114)):
        w, top = 48, 52 + (k % 2) * 8
        m = poly_mask(176, 160, [(x0, top + 6), (x0 + w // 2, top), (x0 + w, top + 6), (x0 + w - 2, 146), (x0 + 2, 146)])
        shade_mask(c, m, R_WOODG, base=0.5, gain=0.55, soft=3, sharp=2)
        c.line(x0 + w // 2, top + 2, x0 + w // 2, 144, WD[1])
        for yy in (top + 26, 120):
            c.hline(x0 + 3, x0 + w - 3, yy, G[5]); c.hline(x0 + 3, x0 + w - 3, yy + 1, G[3])
        if k == 1:                                                              # 바랜 잔 문장
            for (dx, dy) in [(d, 0) for d in range(-7, 8)] + [(-5, 2), (5, 2), (-3, 4), (3, 4), (-1, 6), (1, 6), (0, 8), (0, 10), (-4, 12), (4, 12), (-3, 12), (3, 12), (-2, 12), (2, 12), (-1, 12), (1, 12), (0, 12)]:
                c.px(x0 + w // 2 + dx, top + 40 + dy, A[18])
        for (ax, ay) in ((x0 + 10, top + 30), (x0 + 34, top + 70)):            # 박힌 화살
            c.line(ax, ay, ax + 10, ay - 12, WD[3]); c.px(ax + 10, ay - 12, PL[3])
        c.line(x0 + w // 2, 120, x0 + w // 2 + 14, 150, WD[3])                 # 뒤 받침대
    return Prop("pavise_row", c, (88, 150), footprint=(2, 1), occlude=50, placement="floor (엄폐 — 방 가운데 쪽)",
                note="61라운드 방 변주: 땅에 세운 큰 방패 3장(화살 박힘) — 엄폐")


# ====================================================================== 성문
def gate_notice_post():
    """방(榜) 기둥: 지붕 달린 기둥 + 붙은 수배·징집 방문(글자 없음, 줄만) + 못."""
    c = Canvas(96, 208)
    contact(c, 50, 200, 22, 5)
    stone_blob(c, 48, 198, 14, 6, R_WSTONE, 3)
    for y in range(40, 196):
        c.px(44, y, WD[4]); c.px(45, y, WD[3]); c.px(46, y, WD[3]); c.px(47, y, WD[2]); c.px(48, y, WD[2]); c.px(49, y, WD[1])
    for y in range(26, 42):                                                     # 작은 지붕
        half = 10 + (y - 26)
        for x in range(46 - half, 47 + half):
            c.px(x, y, qcol(R_WOODD, 0.7 - 0.4 * (y - 26) / 16, x, y))
    c.hline(20, 72, 42, R_WOODD[0])
    r = Rand(5)
    for (x0, y0, w, h) in ((22, 56, 28, 36), (44, 62, 26, 30), (26, 100, 30, 38), (48, 108, 24, 26)):
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                c.px(x, y, qcol([PL[1], PL[2], PL[3], PL[4]], 0.7 - 0.4 * (y - y0) / h - 0.1 * (x - x0) / w, x, y))
        c.hline(x0, x0 + w - 1, y0 + h, PL[0]); c.vline(x0 + w, y0 + 1, y0 + h, PL[0])
        for j in range(4):
            yy = y0 + 6 + j * 7
            xx = x0 + 3
            while xx < x0 + w - 5:
                ln = r.i(2, 5)
                c.hline(xx, xx + ln, yy, SL[1]); xx += ln + 2
        c.px(x0 + w // 2, y0 + 1, G[3])
        if y0 == 56:                                                           # 붉은 인장(층 램프)
            c.rect(x0 + w - 8, y0 + h - 8, x0 + w - 4, y0 + h - 4, A[18])
    for (x, y) in ((30, 140), (60, 146)):                                       # 찢겨 떨어진 쪽
        m = poly_mask(96, 208, [(x, y), (x + 10, y + 2), (x + 8, y + 10), (x - 1, y + 8)])
        shade_mask(c, m, [PL[0], PL[1], PL[2], PL[3]], base=0.5, gain=0.4, soft=1)
    return Prop("notice_post", c, (48, 200), footprint=(1, 1), occlude=50, placement="floor (문·길 옆)",
                note="61라운드 방 변주: 방문(수배·징집) 붙은 기둥 — 글자 없음, 줄만")


def gate_chain_posts():
    """쇠사슬 말뚝 2개 + 늘어진 사슬 — 낮은 막힘(통행 통제선) 2칸."""
    c = Canvas(160, 112)
    for px_ in (18, 142):
        contact(c, px_ + 1, 104, 12, 4)
        cyl(c, px_, 54, 98, 8, R_NSTONE, ry=3, lid=True)
        c.rect(px_ - 3, 58, px_ + 3, 62, G[3]); c.hline(px_ - 3, px_ + 3, 58, G[7])
    for k in range(0, 125, 4):                                                  # 사슬(고리 번갈아)
        t = k / 124
        x = 20 + k
        y = int(60 + 22 * math.sin(math.pi * t))
        if (k // 4) % 2 == 0:
            c.ellipse((x - 2, y - 1, x + 2, y + 1), G[7]); c.px(x, y, G[2])
        else:
            c.vline(x, y - 2, y + 2, G[6]); c.px(x, y + 2, G[3])
    return Prop("chain_posts", c, (80, 104), footprint=(2, 1), occlude=30, placement="floor (길목 가로막기)",
                note="61라운드 방 변주: 돌 말뚝 2 + 늘어진 쇠사슬 — 낮은 막힘")


def gate_spear_rack():
    """창 거치대: 나무 틀 + 세워 둔 창 4 + 걸린 방패."""
    c = Canvas(96, 192)
    contact(c, 50, 184, 34, 6)
    for (x0) in (16, 76):
        for y in range(110, 184):
            c.px(x0, y, WD[4]); c.px(x0 + 1, y, WD[3]); c.px(x0 + 2, y, WD[1])
    for yy in (120, 170):
        c.hline(14, 80, yy, WD[3]); c.hline(14, 80, yy + 1, WD[1]); c.hline(14, 80, yy - 1, WD[5])
    for k, x in enumerate((26, 38, 52, 66)):
        p_waste.spear(c, x, 180, x + (k - 1.5) * 3, 34 + (k % 2) * 8)
    m = ell_mask(96, 192, (30, 128, 62, 166))
    shade_mask(c, m, R_WOODG, base=0.5, gain=0.6, soft=3)
    c.ellipse((42, 142, 50, 152), G[5]); c.px(44, 144, G[9])
    return Prop("spear_rack", c, (48, 184), footprint=(1, 1), occlude=50, placement="floor (벽 앞·초소 둘레)",
                note="61라운드 방 변주: 경비 창 거치대 + 방패")


NEW = {
    "outer": {"small": [outer_fallen_sign], "big": [outer_broken_cart, outer_laundry_line]},
    "brewery": {"small": [brew_liquor_sacks, brew_bottle_crate], "big": [brew_still_column, brew_mash_tub]},
    "hall": {"small": [hall_broken_chair, hall_spilled_platter, hall_fallen_candelabra], "big": [hall_overturned_table]},
    "waste": {"small": [waste_arrows_stuck], "big": [waste_dead_tree, waste_pavise_row]},
    "gate": {"small": [], "big": [gate_notice_post, gate_chain_posts, gate_spear_rack]},
}
TAGS = {
    "broken_cart": "outer_wreck", "laundry_line": "outer_backyard", "fallen_sign": "outer_wreck",
    "still_column": "brewery_works", "mash_tub": "brewery_works", "liquor_sacks": "brewery_store", "bottle_crate": "brewery_store",
    "overturned_table": "hall_brawl", "broken_chair": "hall_brawl", "spilled_platter": "hall_brawl", "fallen_candelabra": "hall_brawl",
    "dead_tree": "waste_dead", "arrows_stuck": "waste_volley", "pavise_row": "waste_volley",
    "notice_post": "gate_checkpoint", "chain_posts": "gate_checkpoint", "spear_rack": "gate_checkpoint",
}
