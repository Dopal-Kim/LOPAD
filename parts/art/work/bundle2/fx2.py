"""2차 묶음 아트 2단계(60라운드 Q13) — 엘리트 접두어별 fx + 화염 술병 투척·깨짐 fx (fx/v3, pixelScale 0.5).

엘리트 외곽선 시트(enemies/v3/*_elite)는 건드리지 않는다. 적 그림에 프레임을 맞춘 시트는 만들지 않는다
(적 3종을 다시 그려도 깨지지 않게) — 몸에 붙는 것은 적 pivot 기준 `bodyBoxByEnemy`(빌드 때 idle 에서 잼) + 배율로 놓는다.

| 시트 | 접두어/용도 |
|---|---|
| elite_barrel_armor        | 통 갑옷: 몸에 덧댄 술통 판자(뒤 행 · 앞 행 × idle 1 + 맞음 2) |
| elite_barrel_armor_break  | 통 갑옷: 첫 강공 적중 — 판자·쇠테가 터져 흩어짐(1회) |
| elite_drunk_vapor         | 고주망태: 머리 위 술 김 루프 |
| elite_ringleader_link     | 패거리 두목: 두목 → 주변 적 연결선(반복 타일, 흐르는 쐐기) |
| elite_ringleader_aura     | 패거리 두목: 강화받는 적 발밑 고리 루프 |
| elite_guzzle_trail        | 들이켜는: 죽은 적 → 들이켜는 엘리트로 날아오는 술 줄기(투사체) |
| elite_guzzle_drink        | 들이켜는: 마시는 순간(방울 모임 → 거품 터짐 → 커지는 고리, 1회) |
| fire_bottle_thrown        | 화염 술병 투사체(돌며 날아감) — 플레이어 소모품·독주 행상 공용 |
| fire_bottle_burst         | 화염 술병 깨짐(유리·술 튐 → 불 피어오름, 1회) → 이어서 fire_pool |
"""
import math
import os
import sys

from PIL import Image

from b2 import (Canvas, Rand, G, A, SL, WD, PL, X, CLEAR, R_WOOD, R_IRON, contact, shade_mask, mask, flame, embers,
                qcol, clamp, write_sheet, EMISSIVE_HEX, tohex, SPR, poly_mask)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../atlas57"))
import gridsheet  # noqa: E402

ENEMIES = ["dummy", "archer", "charger"]
FXNOTE = {
    "drawOver": "lightmap", "drawOverNote": "53라운드 Q63 — fx 는 조명 위에 그린다",
}
ELITE_SWAP = {"paletteSwap": True,
              "paletteSwapNote": "60 Q12 — 엘리트 표시는 층 램프 16~27 런타임 스왑(그 층 강조색). 지역 바닥 팔레트 교체는 받지 않음"}
FIRE_SWAP = {"paletteSwap": "none", "paletteSwapNote": "53라운드 Q62·Q68 — fx 는 지역 바닥 팔레트 교체 제외. 1층 소모품 불(호박) 고정"}
FL = [A[22], A[23], A[24], A[25], A[26], A[27]]


def body_boxes():
    """적 idle 첫 프레임에서 몸통 상자(피벗 기준 도트): 피벗 위 45~95 도트 줄의 가로 범위 중앙값."""
    out = {}
    for e in ENEMIES:
        jp = os.path.join(SPR, "enemies", "v3", f"{e}_idle.json")
        g, m = gridsheet.open_grid(jp), gridsheet.load_meta(jp)
        fw, fh = m["frameWidth"], m["frameHeight"]
        a = g.crop((0, 0, fw, fh)).getchannel("A").load()
        px, py = m["pivot"]["x"], m["pivot"]["y"]
        L_, R_ = [], []
        for dy in range(45, 96, 5):
            xs = [x for x in range(fw) if a[x, py - dy] > 0]
            if xs:
                L_.append(min(xs)); R_.append(max(xs))
        L_.sort(); R_.sort()
        l, r = L_[len(L_) // 2], R_[len(R_) // 2]
        w = r - l + 1
        out[e] = {"cx": (l + r) // 2 - px, "cy": -70, "w": w, "h": 50, "scale": round(w / 48, 2)}
    return out


# ====================================================================== 통 갑옷
AW, AH = 128, 112
APIV = (64, 92)      # = 몸통 중심(cx, cy) 아래 22 → 시스템은 pivot 을 '적 pivot + (cx, cy+22)×scale' 에 둔다


def plank(c, x0, y0, x1, y1, ramp, s0, hoopys=(), seed=1, edge_dark=None):
    """세로 판자 하나(살짝 휜 술통 널): 빛 = 왼쪽."""
    r = Rand(seed)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u = (x - x0) / max(1, x1 - x0)
            c.px(x, y, qcol(ramp, s0 + 0.18 - 0.36 * u, x, y))
        if r.f() < 0.08:
            xx = r.i(x0 + 1, x1 - 1)
            c.px(xx, y, ramp[1])
    c.vline(x0, y0, y1, ramp[4]); c.vline(x1, y0, y1, edge_dark or ramp[0])
    c.hline(x0, x1, y0, ramp[5]); c.hline(x0, x1, y1, ramp[0])
    for hy in hoopys:
        c.hline(x0 - 1, x1 + 1, hy, G[6]); c.hline(x0 - 1, x1 + 1, hy + 1, G[3]); c.px(x0 + 1, hy, G[9])


def armor_back(flash=0):
    """뒤 행: 어깨 너머·옆구리로 비죽 보이는 등판 널(어둡게)."""
    c = Canvas(AW, AH)
    cx, cy = 64, 70
    ramp = [SL[0], WD[0], WD[1], WD[2], WD[3], WD[4]]
    for i, dx in enumerate((-30, -19, 13, 24)):
        top = cy - 40 + abs(dx) // 4
        plank(c, cx + dx, top, cx + dx + 8, cy + 18, ramp, 0.45, hoopys=(top + 8, cy + 6), seed=10 + i)
    if flash:
        _flash_edges(c, flash)
    return c.im


def armor_front(flash=0):
    """앞 행: 양 어깨 판자 견갑 + 옆구리 판자 + 가운데를 비운 쇠테 띠 두 줄(얼굴·가슴 문양은 보이게)."""
    c = Canvas(AW, AH)
    cx, cy = 64, 70
    # 옆구리 판자(좌 3·우 3, 바깥으로 갈수록 기울어 둥근 통 느낌)
    for i, (dx, tilt) in enumerate(((-34, -3), (-26, -1), (-18, 0), (11, 0), (19, 1), (27, 3))):
        top, bot = cy - 22 + abs(dx) // 6, cy + 20
        x0 = cx + dx
        s0 = 0.62 if dx < 0 else 0.42
        for y in range(top, bot + 1):
            sh = int(round(tilt * (y - top) / max(1, bot - top)))
            for x in range(x0, x0 + 7):
                u = (x - x0) / 6
                c.px(x + sh, y, qcol(R_WOOD, s0 + 0.15 - 0.3 * u, x, y))
            c.px(x0 + sh, y, R_WOOD[4] if dx < 0 else R_WOOD[3]); c.px(x0 + 6 + sh, y, R_WOOD[0])
        c.hline(x0, x0 + 6, top, R_WOOD[5]); c.hline(x0, x0 + 6, bot, R_WOOD[0])
    # 쇠테 두 줄(앞쪽으로 휜 호, 가운데는 몸 위로 지나감 — 얇게)
    for hy in (cy - 12, cy + 10):
        for x in range(cx - 36, cx + 36):
            u = (x - cx) / 36
            y = hy + int(round(4 * math.sqrt(max(0, 1 - u * u))))
            c.px(x, y, G[7] if u < -0.2 else G[5]); c.px(x, y + 1, G[3]); c.px(x, y + 2, SL[0] if abs(u) > 0.35 else G[2])
        for u in (-0.85, -0.45, 0.45, 0.85):
            x = int(cx + 36 * u)
            c.px(x, hy + int(4 * math.sqrt(1 - u * u)), G[10])
    # 견갑: 반쪽 술통 뚜껑 판(어깨 위 둥근 판) + 가죽 끈
    for s in (-1, 1):
        ox = cx + s * 24
        m, d = mask(AW, AH)
        d.pieslice((ox - 15, cy - 40, ox + 15, cy - 14), 180, 360, fill=255)
        d.rectangle((ox - 15, cy - 28, ox + 15, cy - 23), fill=255)
        shade_mask(c, m, R_WOOD, base=0.55 if s < 0 else 0.42, gain=0.8, soft=3)
        for k in (-7, 0, 7):
            c.vline(ox + k, cy - 37 + abs(k) // 3, cy - 24, R_WOOD[1])
        c.hline(ox - 15, ox + 15, cy - 24, G[5]); c.hline(ox - 15, ox + 15, cy - 23, G[2])
        c.line(ox - s * 6, cy - 23, ox - s * 12, cy - 6, WD[2]); c.line(ox - s * 5, cy - 23, ox - s * 11, cy - 6, WD[4])
        # 술 표지 낙인(호박, 비발광) — 통 갑옷 = 술통
        c.px(ox, cy - 31, A[21]); c.px(ox + 1, cy - 31, A[20]); c.px(ox, cy - 30, A[19])
    if flash:
        _flash_edges(c, flash)
    return c.im


def _flash_edges(c, level):
    """맞음: 판자 위·왼쪽 가장자리를 밝게(1 = 호박 25, 2 = 백열 X0) — 막아냈다는 신호."""
    im = c.im
    a = im.getchannel("A").load()
    col = A[25] if level == 1 else X[0]
    pts = []
    for y in range(1, im.height):
        for x in range(1, im.width):
            if a[x, y] and (not a[x - 1, y] or not a[x, y - 1]):
                pts.append((x, y))
    for (x, y) in pts:
        if (x + y) % (2 if level == 2 else 3) == 0:
            c.px(x, y, col)


def barrel_armor(boxes):
    frames = [armor_back(0), armor_back(1), armor_back(2), armor_front(0), armor_front(2), armor_front(1)]
    m = {
        "directions": ["back", "front"], "rowsAre": "layers",
        "layers": {"back": "적 스프라이트 아래(외곽선 시트 위)", "front": "적 스프라이트 위"},
        "states": {"idle": [0], "hit": [1, 2]},
        "stateNote": "열 0 = 평소, 1·2 = 막아낸 맞음(일반 공격 적중 시 1회 재생 후 0으로). 첫 강공 적중 → 이 시트를 끄고 elite_barrel_armor_break",
        "pivot": {"x": APIV[0], "y": APIV[1]},
        "anchor": "enemy_body",
        "anchorRule": "pivot = 적 pivot + (bodyBoxByEnemy[적].cx, bodyBoxByEnemy[적].cy + 22) × 엘리트 배율. scale = bodyBoxByEnemy[적].scale × 엘리트 배율(1.15). 적이 좌우 뒤집히면 같이 flipX",
        "bodyBoxByEnemy": boxes,
        "bodyBoxNote": "적 v3 idle 첫 프레임 몸통(피벗 위 45~95 도트 줄) 가로 범위 — 도트, 피벗 기준. 적 시트를 다시 그리면 build.py --only elite_barrel 로 다시 잼",
        "followTarget": True, "depth": "body",
        "directionNote": "판자 띠는 둥근 통이라 4방향 공용. up(뒷모습)일 때는 back/front 행을 바꿔 그려도 된다(제안)",
        "usage": "엘리트 접두어 '통 갑옷'(임시) — 받는 피해 −30%·경직 면역 동안 몸에 덧댄 술통 판자(설계 g.2 #3)",
        "emissiveColors": [], **ELITE_SWAP, **FXNOTE,
    }
    write_sheet("fx", "elite_barrel_armor", frames, AW, AH, m, rows=2, durations=[100, 50, 70], loop=False)
    return frames


BKW, BKH = 208, 176
BKPIV = (104, 132)


def armor_break_frame(k):
    """판자 8장·쇠테 2개가 바깥으로 튐 + 나무 부스러기. k = 0..8."""
    c = Canvas(BKW, BKH)
    cx, cy = BKPIV[0], BKPIV[1] - 40
    t = k / 8
    r = Rand(5)
    if k <= 1:  # 깨지는 순간 섬광(백열은 0프레임만)
        rr = 18 + 10 * k
        for a_ in range(0, 360, 6):
            for d in range(4, rr, 3):
                x, y = cx + d * math.cos(math.radians(a_)), cy + d * 0.7 * math.sin(math.radians(a_))
                if (a_ // 6 + d) % 5 == 0:
                    c.px(round(x), round(y), X[0] if k == 0 else A[25])
    pieces = [(-150, 1.0), (-115, 0.8), (-70, 0.9), (-30, 1.1), (200, 1.0), (165, 0.9), (20, 1.0), (60, 0.85)]
    g = 140  # 중력(도트/단위²)
    for i, (ang, spd) in enumerate(pieces):
        a_ = math.radians(ang)
        vx, vy = math.cos(a_) * 90 * spd, math.sin(a_) * 70 * spd - 40
        x = cx + vx * t * 1.1
        y = cy + vy * t * 1.1 + g * t * t
        y = min(y, BKPIV[1] + 6 + (i % 3) * 3)
        rot = (ang / 40 + i) + t * (5 + i % 3) * (1 if i % 2 else -1)
        L_, Wd = 22, 5
        ca, sa = math.cos(rot), math.sin(rot)
        pts = [(-L_ / 2, -Wd / 2), (L_ / 2, -Wd / 2), (L_ / 2, Wd / 2), (-L_ / 2, Wd / 2)]
        poly = [(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts]
        if k >= 7 and (i + k) % 2:
            continue  # 마지막 두 프레임: 반씩 사라짐
        m_ = poly_mask(BKW, BKH, poly)
        shade_mask(c, m_, R_WOOD, base=0.55, gain=0.8, soft=1)
        if i % 3 == 0:  # 쇠테 조각
            c.line(round(poly[0][0]), round(poly[0][1]), round(poly[1][0]), round(poly[1][1]), G[7])
    # 쇠테 고리 2개: 찌그러진 타원이 아래로 떨어지며 굴러감
    for j, side in enumerate((-1, 1)):
        x = cx + side * (16 + 60 * t)
        y = min(cy + 6 + 50 * t * t * 2 - 20 * t, BKPIV[1] + 2)
        rx, ry = 14 - 2 * j, max(3, int(6 - 4 * t))
        for a_ in range(0, 360, 5):
            xx, yy = x + rx * math.cos(math.radians(a_ + k * 30 * side)), y + ry * math.sin(math.radians(a_ + k * 30 * side))
            c.px(round(xx), round(yy), G[8] if a_ < 180 else G[4])
    # 부스러기
    for n in range(28):
        a_ = math.radians(r.i(0, 359))
        sp = 30 + r.f() * 80
        x = cx + math.cos(a_) * sp * t
        y = cy + math.sin(a_) * sp * 0.7 * t + 60 * t * t
        if k < 8 and y < BKPIV[1] + 8:
            c.px(round(x), round(y), WD[4] if n % 3 else A[22])
    return c.im


def barrel_armor_break(boxes):
    frames = [armor_break_frame(k) for k in range(9)]
    m = {
        "pivot": {"x": BKPIV[0], "y": BKPIV[1]},
        "anchor": "enemy_body",
        "anchorRule": "pivot = 적 pivot + (bodyBoxByEnemy[적].cx, 0) × 엘리트 배율 — 곧 적 발밑 가로 가운데(조각이 바닥에 떨어짐). scale = bodyBoxByEnemy[적].scale",
        "bodyBoxByEnemy": boxes,
        "spawn": "elite_armor_break", "spawnNote": "통 갑옷 엘리트가 첫 강공에 맞은 순간 1회. 같은 순간 elite_barrel_armor 를 끄고, elite_emblem barrel_armor 행을 1열(깨짐)로",
        "flashFrame": 0, "shake": {"px": 4, "ms": 120},
        "depth": "above", "followTarget": False, "loop": False,
        "usage": "엘리트 접두어 '통 갑옷'(임시) 깨짐 fx(설계 g.3 '갑옷 깨짐 1')",
        "emissiveColors": [tohex(X[0]), tohex(A[25]), tohex(A[22])], **ELITE_SWAP, **FXNOTE,
    }
    write_sheet("fx", "elite_barrel_armor_break", frames, BKW, BKH, m, durations=[40, 50, 60, 60, 70, 80, 90, 110, 140])
    return frames


# ====================================================================== 고주망태 술 김
VW, VH = 112, 80
VPIV = (56, 74)


def _puff(c, x, y, rad, cols, dither=False):
    """작은 김 뭉치: 아래·오른쪽 어둡게, 위·왼쪽 밝게(cols = [어둠, 중간, 밝음])."""
    for dx in range(-rad, rad + 1):
        for dy in range(-rad, rad + 1):
            d2 = dx * dx + dy * dy
            if d2 > rad * rad:
                continue
            xx, yy = round(x + dx), round(y + dy)
            if dither and (xx + yy) % 2:
                continue
            lit = (dx + dy) < -rad * 0.3
            col = cols[2] if lit else (cols[0] if d2 > (rad - 1) ** 2 and (dx + dy) > 0 else cols[1])
            c.px(xx, yy, col)


def _cloud(c, puffs, cols):
    """겹친 김 뭉치들을 한 덩어리로: 1차 어두운 바탕 → 2차 중간(왼위로 1) → 3차 밝은 점(왼위로 2). 뭉치 사이 경계선 없음."""
    for layer, (dx0, dr) in enumerate(((0, 0), (-1, -1), (-2, -3))):
        col = cols[layer]
        for (x, y, rad, dith) in puffs:
            r_ = rad + dr
            if r_ < 1:
                continue
            for dx in range(-r_, r_ + 1):
                for dy in range(-r_, r_ + 1):
                    if dx * dx + dy * dy > r_ * r_:
                        continue
                    xx, yy = round(x + dx + dx0), round(y + dy + dx0)
                    if dith and (xx + yy) % 2:
                        continue
                    c.px(xx, yy, col)


def vapor_frame(k):
    c = Canvas(VW, VH)
    ph = k * 2 * math.pi / 8
    hx, hy = VPIV[0], VPIV[1] - 14          # 머리 꼭대기 근처를 도는 고리
    back, front = [], []
    for i in range(12):
        a = ph + i * 2 * math.pi / 12
        x = hx + 28 * math.cos(a)
        y = hy + 7 * math.sin(a) - 3 * math.sin(a * 3 + ph)
        rad = 5 + int(2 * (0.5 + 0.5 * math.sin(a * 2 + ph * 2)))
        (front if math.sin(a) > 0 else back).append((x, y, rad if math.sin(a) > 0 else rad - 1, False))
    # 위로 피어오르는 두 줄기(겹친 뭉치 — 작아지며 위쪽은 체커로 흩어짐)
    rise = []
    for s_ in (-1, 1):
        for j in range(9):
            t = ((k / 8) / 9 + j / 9) % 1.0
            x = hx + s_ * (12 + 5 * t) + 3 * math.sin(t * 7 + s_ + ph)
            y = hy - 10 - t * 46
            rise.append((x, y, max(1, int(5 - 4 * t)), t > 0.55))
    _cloud(c, back + rise, [SL[3], PL[0], PL[1]])
    _cloud(c, front, [PL[1], PL[2], PL[3]])
    # 앞쪽 김에 술 기운(호박, 비발광) 몇 점
    for (x, y, rad, _) in front[::3]:
        c.px(round(x) - 1, round(y) - 1, A[22]); c.px(round(x), round(y) - 1, A[21])
    # 딸꾹 거품(하나만 발광)
    tt = (k % 8) / 8
    bx, by = hx + 4, hy - 20 - tt * 30
    rr = 1 + int(tt * 3)
    if tt < 0.85:
        for a_ in range(0, 360, 30):
            c.px(round(bx + rr * math.cos(math.radians(a_))), round(by + rr * math.sin(math.radians(a_))), A[24])
        c.px(round(bx) - 1, round(by) - 1, A[26])
    return c.im


def drunk_vapor(heads):
    frames = [vapor_frame(k) for k in range(8)]
    m = {
        "pivot": {"x": VPIV[0], "y": VPIV[1]}, "anchor": "enemy_head",
        "anchorRule": "pivot = 적 pivot 위 headTopByEnemy[적] − 8 도트 × 엘리트 배율 → 김 고리(그림 pivot 위 14)가 머리 꼭대기를 감쌈. 문장(elite_emblem)보다 아래",
        "headTopByEnemy": heads, "followTarget": True, "depth": "above",
        "states": {"loop": list(range(8))}, "loop": True,
        "usage": "엘리트 접두어 '고주망태'(임시) 머리 위 술 김 루프(설계 g.2 #1 '머리 위 술 김'). 몸 흔들림은 코드 연출",
        "emissiveColors": [tohex(A[24]), tohex(A[26])], "emissiveNote": "거품 방울 일부만 발광 — 김 자체는 비발광(조명 받음)",
        **ELITE_SWAP, **FXNOTE,
    }
    write_sheet("fx", "elite_drunk_vapor", frames, VW, VH, m, durations=[110] * 8, loop=True)
    return frames


# ====================================================================== 패거리 두목
LW, LH = 64, 24
LPIV = (0, 12)


def link_frame(k):
    """반복 타일: 가는 끈 + 흐르는 쐐기(두목 → 적 방향 = +x). 주기 64 도트, 6프레임에 한 주기 흐름."""
    c = Canvas(LW, LH)
    y0 = LPIV[1]
    for x in range(LW):
        wob = int(round(1.2 * math.sin((x / LW) * 2 * math.pi)))
        c.px(x, y0 + wob, A[21] if x % 4 else A[23]); c.px(x, y0 + wob + 1, A[18] if x % 2 else CLEAR)
    off = int(k * LW / 6)
    for base in (0, 32):
        x = (base + off) % LW
        for d in range(6):
            for s in (-1, 1):
                xx = (x - d) % LW
                yy = y0 + s * d
                c.px(xx, yy, A[25] if d < 3 else A[23])
                c.px((xx - 1) % LW, yy, A[22])
        c.px(x % LW, y0, A[26])
    return c.im


def ringleader_link():
    frames = [link_frame(k) for k in range(6)]
    m = {
        "pivot": {"x": LPIV[0], "y": LPIV[1]}, "anchor": "line_start",
        "anchorNote": "pivot = 선 시작(두목 쪽) 타일 왼쪽 가운데. 시작 = 두목 pivot 위 60 도트, 끝 = 강화받는 적 pivot 위 60 도트(배율 반영)",
        "tile": True, "tileAxis": "x", "tilePeriodPx": 64, "rotate": True, "drawnFacing": "right",
        "lengthRule": "두 점 거리만큼 타일 반복(마지막 타일은 잘라 씀). 쐐기는 +x = 두목 → 적 방향으로 흐름",
        "states": {"loop": list(range(6))}, "loop": True, "depth": "above", "alpha": 0.85,
        "usage": "엘리트 접두어 '패거리 두목'(임시) — 주변 4칸 일반 적과의 연결선(설계 g.2 #5). 두목이 죽으면 끊김 → 적 경직은 기존 status_stagger",
        "emissiveColors": [tohex(A[23]), tohex(A[25]), tohex(A[26])], **ELITE_SWAP, **FXNOTE,
    }
    write_sheet("fx", "elite_ringleader_link", frames, LW, LH, m, durations=[90] * 6, loop=True)
    return frames


RW, RH = 136, 56
RPIV = (68, 28)


def aura_frame(k):
    c = Canvas(RW, RH)
    cx, cy = RPIV
    rx, ry = 56, 18
    ph = k * (2 * math.pi / 6) / 4
    for a in range(0, 360, 2):
        ar = math.radians(a)
        seg = int(((a / 360) * 12 + k / 6 * 2) % 2)  # 도는 점선
        if seg:
            continue
        x, y = cx + rx * math.cos(ar + ph), cy + ry * math.sin(ar + ph)
        back = math.sin(ar + ph) < 0
        c.px(round(x), round(y), A[20] if back else A[24])
        if not back:
            c.px(round(x), round(y) + 1, A[19])
    # 깃 쐐기 4개(고리 위에서 돎)
    for i in range(4):
        ar = ph * 2 + i * math.pi / 2
        x, y = cx + rx * math.cos(ar), cy + ry * math.sin(ar)
        if math.sin(ar) < 0:
            continue
        for d in range(5):
            c.px(round(x) - d // 2, round(y) - d, A[25] if d < 3 else A[23])
    return c.im


def ringleader_aura():
    frames = [aura_frame(k) for k in range(6)]
    m = {
        "pivot": {"x": RPIV[0], "y": RPIV[1]}, "anchor": "enemy_pivot",
        "anchorRule": "pivot = 강화받는 일반 적 발(pivot). scale = 결사병 1.25, 그 밖 1.0(제안)", "followTarget": True,
        "depth": "floor", "states": {"loop": list(range(6))}, "loop": True,
        "usage": "엘리트 접두어 '패거리 두목'(임시) — 강화(이동 +20%·공격 간격 −20%) 받는 적 발밑 고리",
        "emissiveColors": [tohex(A[24]), tohex(A[25])], **ELITE_SWAP, **FXNOTE,
    }
    write_sheet("fx", "elite_ringleader_aura", frames, RW, RH, m, durations=[100] * 6, loop=True)
    return frames


# ====================================================================== 들이켜는
TW, TH = 72, 28
TPIV = (56, 14)


def trail_frame(k):
    """술 줄기 투사체: 머리(오른쪽) 큰 방울 + 뒤로 가늘어지는 꼬리 + 떨어지는 작은 방울."""
    c = Canvas(TW, TH)
    hx, hy = TPIV
    for x in range(4, hx):
        t = (hx - x) / (hx - 4)
        w = max(0, int(4 * (1 - t)))
        yy = hy + int(round(2 * math.sin(x * 0.35 + k * 1.6) * t))
        for d in range(-w, w + 1):
            if t > 0.6 and (x + k) % 2:
                continue
            c.px(x, yy + d, A[22] if d <= 0 else A[20])
    c.ellipse((hx - 6, hy - 5, hx + 6, hy + 5), A[22])
    c.ellipse((hx - 4, hy - 4, hx + 3, hy + 2), A[24])
    c.px(hx - 2, hy - 3, A[26]); c.px(hx - 1, hy - 3, A[25])
    for i in range(2):
        x = hx - 18 - i * 16 - (k * 3) % 8
        c.px(x, hy + 6 + i, A[23]); c.px(x, hy + 7 + i, A[20])
    return c.im


def guzzle_trail():
    frames = [trail_frame(k) for k in range(4)]
    m = {
        "pivot": {"x": TPIV[0], "y": TPIV[1]}, "anchor": "projectile", "rotate": True, "drawnFacing": "right",
        "spawn": "elite_guzzle_source", "spawnNote": "들이켜는 엘리트 5칸 안에서 적이 죽은 순간, 죽은 적 pivot 위 60 도트에서 생성 → 엘리트 머리(headTop)로 0.35초 날아감(호 높이 30 도트 제안) → 도착 시 elite_guzzle_drink",
        "states": {"loop": list(range(4))}, "loop": True, "depth": "above",
        "usage": "엘리트 접두어 '들이켜는'(임시) — 죽은 적에게서 술을 빨아들이는 줄기(설계 g.2 #6)",
        "emissiveColors": [tohex(A[24]), tohex(A[25]), tohex(A[26])], **ELITE_SWAP, **FXNOTE,
    }
    write_sheet("fx", "elite_guzzle_trail", frames, TW, TH, m, durations=[60] * 4, loop=True)
    return frames


GW, GH = 128, 128
GPIV = (64, 100)


def drink_frame(k):
    c = Canvas(GW, GH)
    cx, cy = GPIV[0], GPIV[1] - 30      # 입 높이(머리 꼭대기 아래 30)
    r = Rand(3)
    if k <= 3:   # 방울이 나선으로 모여듦
        t = k / 3
        for i in range(10):
            a = i * 2 * math.pi / 10 + t * 2.2
            rr = 48 * (1 - t) + 6
            x, y = cx + rr * math.cos(a), cy + rr * 0.6 * math.sin(a) - 8 * (1 - t)
            c.rect(round(x), round(y), round(x) + 1, round(y) + 1, A[24]); c.px(round(x), round(y), A[26])
            c.px(round(x), round(y) + 2, A[21]); c.px(round(x) + 1, round(y) + 2, A[21])
    if 3 <= k <= 6:  # 거품 터짐(입 앞)
        t = (k - 3) / 3
        n = 14
        for i in range(n):
            a = i * 2 * math.pi / n + 0.3
            rr = 6 + 16 * t
            x, y = cx + rr * math.cos(a), cy + rr * 0.7 * math.sin(a) - 4 * t
            rad = 2 if t < 0.6 else 1
            for a2 in range(0, 360, 45):
                c.px(round(x + rad * math.cos(math.radians(a2))), round(y + rad * math.sin(math.radians(a2))), A[25] if k < 6 else A[23])
        if k == 4:
            c.ellipse((cx - 4, cy - 3, cx + 4, cy + 3), A[26])
    if k >= 4:   # 커지는 고리(크기 +5% 신호) — 발밑 쪽 타원
        t = (k - 4) / 4
        rx, ry = 24 + 30 * t, 8 + 8 * t
        for a in range(0, 360, 3):
            if (a // 3 + k) % 3 == 0 and t > 0.5:
                continue
            x, y = cx + rx * math.cos(math.radians(a)), GPIV[1] + 18 + ry * math.sin(math.radians(a))
            if 0 <= y < GH:
                c.px(round(x), round(y), A[25] if t < 0.5 else A[23])
        # 위로 오르는 회복 불티
        for i in range(6):
            x = cx - 20 + i * 8 + r.i(-2, 2)
            y = cy + 10 - t * 40 - (i % 3) * 6
            c.px(x, round(y), A[24] if i % 2 else A[26])
    return c.im


def guzzle_drink(heads):
    frames = [drink_frame(k) for k in range(9)]
    m = {
        "pivot": {"x": GPIV[0], "y": GPIV[1]}, "anchor": "enemy_head",
        "anchorRule": "pivot = 들이켜는 엘리트 pivot 위 headTopByEnemy[적] − 70 도트(그림의 입 높이 = pivot 위 30) × 엘리트 배율 — 고리는 몸통 아래쪽에 퍼짐",
        "headTopByEnemy": heads, "followTarget": True, "depth": "above",
        "spawn": "elite_guzzle", "spawnNote": "elite_guzzle_trail 도착 순간 1회. 회복(HP +15%)·크기 +5%는 시스템이 이 시트 4프레임째에 적용(제안)",
        "phaseFrames": {"gather": [0, 1, 2, 3], "burst": [3, 4, 5, 6], "ring": [4, 5, 6, 7, 8]},
        "healFrame": 4,
        "usage": "엘리트 접두어 '들이켜는'(임시) — 마시는 순간(설계 g.2 #6 '마시는 순간 술 김 fx')",
        "emissiveColors": [tohex(A[23]), tohex(A[24]), tohex(A[25]), tohex(A[26])], **ELITE_SWAP, **FXNOTE,
    }
    write_sheet("fx", "elite_guzzle_drink", frames, GW, GH, m, durations=[50, 50, 60, 60, 70, 80, 90, 100, 120])
    return frames


# ====================================================================== 화염 술병
BTW, BTH = 56, 56
BTPIV = (28, 28)
R_GLASS = [SL[0], SL[1], SL[2], SL[3], SL[5], SL[7]]


def bottle_sprite():
    """세운 병(오른쪽 위로 심지) 원본 32×44 — 회전용."""
    c = Canvas(32, 44)
    cx, by = 16, 42
    m, d = mask(32, 44)
    d.ellipse((cx - 9, by - 22, cx + 9, by), fill=255)
    d.polygon([(cx - 8, by - 20), (cx + 8, by - 20), (cx + 3, by - 28), (cx - 3, by - 28)], fill=255)
    d.rectangle((cx - 3, by - 37, cx + 3, by - 26), fill=255)
    shade_mask(c, m, R_GLASS, base=0.45, gain=0.9, soft=2)
    for y in range(by - 14, by - 1):
        for x in range(cx - 7, cx + 8):
            if c.get(x, y) in R_GLASS:
                c.px(x, y, A[21] if x < cx else A[19])
    c.hline(cx - 7, cx + 7, by - 14, A[23]); c.vline(cx - 5, by - 19, by - 6, G[11])
    c.poly([(cx - 3, by - 38), (cx + 3, by - 38), (cx + 5, by - 43), (cx - 1, by - 42)], PL[2])
    c.hline(cx - 3, cx + 3, by - 37, WD[1])
    return c.im


def thrown_frame(k, base):
    c = Canvas(BTW, BTH)
    rot = base.rotate(-45 * k, resample=Image.NEAREST, expand=True)
    c.paste(rot, BTPIV[0] - rot.width // 2, BTPIV[1] - rot.height // 2)
    # 심지 불: 회전한 심지 끝 위치에 작은 불꽃(위로 타오름) + 지나온 불티 2
    ang = math.radians(45 * k)
    tx = BTPIV[0] + 20 * math.sin(ang)
    ty = BTPIV[1] - 20 * math.cos(ang)
    flame(c, round(tx), round(ty) + 3, 9, 12 + (k % 2) * 2, seed=80 + k, tongues=2, core=False)
    c.px(round(tx), round(ty), A[27])
    for i in range(2):
        c.px(round(tx) - 6 - i * 5, round(ty) + 2 + i, A[24] if i == 0 else A[22])
    return c.im


def fire_bottle_thrown():
    base = bottle_sprite()
    frames = [thrown_frame(k, base) for k in range(8)]
    m = {
        "pivot": {"x": BTPIV[0], "y": BTPIV[1]}, "anchor": "projectile",
        "rotate": False, "spinDegPerFrame": 45, "spinNote": "돌기는 그림에 들어 있다(시계 방향 45°/프레임) — 시스템은 진행 각도로 회전하지 않음. 왼쪽으로 날아가면 flipX",
        "spawn": "throw_release", "spawnNote": "플레이어 소모품 투척 = 플레이어 손 높이(pivot 위 70 도트)에서 커서 방향 포물선 / 독주 행상 = 적 attack 의 손 앵커(그 시트가 생기면). 착지 시 fire_bottle_burst",
        "arcNote": "포물선 높이·그림자 원은 시스템(최대 6칸, 설계 i.1)",
        "sharedWith": ["consumable fire_bottle(플레이어)", "신규 적 독주 행상(S-7) 화염병 투척"],
        "states": {"loop": list(range(8))}, "loop": True, "depth": "above",
        "usage": "화염 술병 투사체(2차 묶음 (i) 화염 술병 · 독주 행상 공용, 설계 14.1 '술병 투척·깨짐 fx 1')",
        "light": {"color": "#e8b858", "radius": 70, "intensity": 0.6, "flicker": {"amp": 0.2, "hz": 9}, "offset": {"x": BTPIV[0], "y": BTPIV[1]}},
        "emissiveColors": EMISSIVE_HEX, **FIRE_SWAP, **FXNOTE,
    }
    write_sheet("fx", "fire_bottle_thrown", frames, BTW, BTH, m, durations=[50] * 8, loop=True)
    return frames


FBW, FBH = 240, 184
FBPIV = (120, 136)


def burst_frame(k):
    """0 깨짐 섬광 · 1~3 유리 조각·술 왕관 · 3~7 불이 번져 피어오름 · 8~9 불이 웅덩이로 가라앉음(→ fire_pool)."""
    c = Canvas(FBW, FBH)
    cx, cy = FBPIV
    r = Rand(21)
    t = k / 9
    # 바닥 술 웅덩이(점점 퍼짐, 1.5칸 = 반경 96 도트)
    pr = min(96, 20 + 26 * k)
    for y in range(cy - pr // 3, cy + pr // 3 + 1):
        for x in range(cx - pr, cx + pr + 1):
            d = ((x - cx) / pr) ** 2 + ((y - cy) / (pr / 3)) ** 2 + 0.12 * math.sin(x * 0.3 + y)
            if d <= 1:
                c.px(x, y, A[18] if d > 0.82 else qcol([A[19], A[20], A[21]], 0.75 - 0.6 * d, x, y))
    if k == 0:  # 섬광(백열은 0프레임만)
        for a in range(0, 360, 15):
            for d in range(2, 22):
                if d % 3 == 0:
                    c.px(round(cx + d * math.cos(math.radians(a))), round(cy - 6 + d * 0.6 * math.sin(math.radians(a))), X[0] if d < 12 else A[26])
    # 유리 조각(위로 튀었다 떨어짐)
    for i in range(12):
        a = math.radians(-160 + i * 12 + r.i(-5, 5))
        sp = 50 + r.f() * 40
        x = cx + math.cos(a) * sp * min(1, t * 2)
        y = cy - 6 + math.sin(a) * sp * 0.8 * min(1, t * 2) + 160 * max(0, t - 0.1) ** 2
        if k < 7 and y < cy + 12:
            c.px(round(x), round(y), G[12] if i % 3 else SL[7]); c.px(round(x) + 1, round(y) + 1, SL[3])
    # 술 왕관(1~3)
    if 1 <= k <= 3:
        for i in range(16):
            a = math.radians(-180 + i * 12)
            h = 20 + 10 * math.sin(i * 1.7)
            x = cx + math.cos(a) * (14 + 10 * k)
            for j in range(int(h * (1 - (k - 1) * 0.3))):
                c.px(round(x), cy - 4 - j, A[22] if j < h * 0.6 else A[24])
    # 불(2~9): 뒤 줄(작게) → 가운데 큰 불 → 앞 줄(중간). 키는 제각각, 커졌다 줄어듦
    if k >= 2:
        hscale = [0, 0, 0.35, 0.7, 1.0, 1.0, 0.9, 0.75, 0.5, 0.3][k]
        rr_ = Rand(300)
        spots = []
        for i in range(5):   # 뒤 줄
            u = (i - 2) / 2.2
            spots.append((cx + int(u * (pr - 20)), cy - pr // 6, 0.45 + 0.2 * rr_.f(), 16))
        spots.append((cx + 4, cy - 2, 1.0, 30))                 # 가운데 큰 불
        for i in range(4):   # 앞 줄
            u = (i - 1.5) / 1.8
            spots.append((cx + int(u * (pr - 26)), cy + pr // 6, 0.5 + 0.25 * rr_.f(), 20))
        for j, (fx, fy, hh, ww) in enumerate(spots):
            fh = int(78 * hh * hscale * (0.85 + 0.3 * math.sin(k * 1.3 + j)))
            if fh >= 6:
                flame(c, fx, fy, ww, fh, seed=100 + j * 7 + k, tongues=3 if ww > 20 else 2, core=fh > 50)
        if 3 <= k <= 6:
            embers(c, cx, cy - 64, 9, 40, 200 + k)
    return c.im


def fire_bottle_burst():
    frames = [burst_frame(k) for k in range(10)]
    m = {
        "pivot": {"x": FBPIV[0], "y": FBPIV[1]}, "anchor": "hitbox_center",
        "anchorNote": "pivot = 착탄 지점(바닥) = 불 웅덩이 판정 원 중심",
        "radiusPx": 96, "radiusNote": "웅덩이 그림 반경 96 도트 = 1.5칸(설계 i.1 착탄 반경 1.5칸). 판정 수치의 기준은 시스템 데이터",
        "scale": "allowed",
        "spawn": "fire_bottle_impact", "flashFrame": 0, "shake": {"px": 3, "ms": 100},
        "phaseFrames": {"shatter": [0, 1], "splash": [1, 2, 3], "ignite": [3, 4, 5, 6], "settle": [7, 8, 9]},
        "handoff": "마지막 프레임 뒤 fx/v3/fire_pool(1-1 불 웅덩이 루프, scale = 96/fire_pool 반경)로 이어 4초 — 취기 '술불' 점화원(설계 i.1). 잔불 끝은 fire_pool 규칙",
        "depth": "above", "depthNote": "웅덩이·불은 바닥 위, 유리 조각은 위로 튐 — 한 시트로 above. 바닥 데칼만 원하면 시스템이 fire_pool 로 빨리 넘김",
        "sharedWith": ["consumable fire_bottle(플레이어)", "신규 적 독주 행상(S-7) 화염병"],
        "light": {"color": "#eecc78", "radius": 260, "intensity": 1.2, "flicker": {"amp": 0.25, "hz": 8}, "offset": {"x": FBPIV[0], "y": FBPIV[1] - 30}},
        "lightByPhase": {"shatter": 0.6, "splash": 0.6, "ignite": 1.2, "settle": 0.8},
        "usage": "화염 술병 깨짐(설계 14.1 '술병 투척·깨짐 fx 1')",
        "emissiveColors": EMISSIVE_HEX, **FIRE_SWAP, **FXNOTE,
    }
    write_sheet("fx", "fire_bottle_burst", frames, FBW, FBH, m, durations=[40, 50, 60, 70, 80, 90, 100, 110, 120, 140])
    return frames


def build_all(want, heads):
    """want(이름)->bool. 반환: [(이름, 프레임 목록, 피벗)]."""
    out = []
    boxes = None
    for name, fn, piv, needs in (
            ("elite_barrel_armor", barrel_armor, APIV, "box"),
            ("elite_barrel_armor_break", barrel_armor_break, BKPIV, "box"),
            ("elite_drunk_vapor", drunk_vapor, VPIV, "head"),
            ("elite_ringleader_link", ringleader_link, LPIV, None),
            ("elite_ringleader_aura", ringleader_aura, RPIV, None),
            ("elite_guzzle_trail", guzzle_trail, TPIV, None),
            ("elite_guzzle_drink", guzzle_drink, GPIV, "head"),
            ("fire_bottle_thrown", fire_bottle_thrown, BTPIV, None),
            ("fire_bottle_burst", fire_bottle_burst, FBPIV, None)):
        if not want(name):
            continue
        if needs == "box":
            boxes = boxes or body_boxes()
            fr = fn(boxes)
        elif needs == "head":
            fr = fn(heads)
        else:
            fr = fn()
        out.append((name, fr, piv))
    return out
