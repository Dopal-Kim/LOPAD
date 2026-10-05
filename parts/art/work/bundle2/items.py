"""(i) 층 테마 소모품 3종(1층 '잔') — 월드 드롭 그림 `items/v3/consumable_f1`.

행 = 종류(fire_bottle 화염 술병 · strong_swig 깡술 한 모금 · cold_water 냉수 한 바가지, 이름 임시),
열 = 바닥에서 둥실 루프 8프레임(그림자는 제자리, 물건만 위아래 3도트 + 반짝임 한 번).
실루엣으로 구분: 목 긴 병 + 헝겊 심지 / 납작한 흰 도기 술병 / 넓은 바가지(차가운 물빛).
"""
import math

from b2 import (Canvas, Rand, G, A, SL, WD, PL, CLEAR, contact, shade_mask, mask, flame, qcol, write_sheet,
                EMISSIVE_HEX, R_WOOD)

IW, IH = 64, 72
IPIV = (32, 64)
BOB = [0, 1, 2, 3, 3, 2, 1, 0]
R_GLASS = [SL[0], SL[1], SL[2], SL[3], SL[5], SL[7]]
R_GLAZE = [SL[1], PL[0], PL[1], PL[2], PL[3], PL[4], G[12]]
R_GOURD = [WD[1], WD[2], WD[3], PL[1], PL[2], PL[3], PL[4]]
R_WATER = [SL[1], SL[2], SL[3], SL[4], SL[5], SL[6], SL[7]]

KINDS = [("fire_bottle", "화염 술병"), ("strong_swig", "깡술 한 모금"), ("cold_water", "냉수 한 바가지")]


def glint(c, x, y, big):
    c.px(x, y, A[27] if big else A[25])
    if big:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.px(x + dx, y + dy, A[25])
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            c.px(x + dx, y + dy, A[23])


def fire_bottle(c, cx, by, k):
    """목 긴 짙은 유리병(호박 술) + 목에 쑤셔 넣은 헝겊 + 심지 끝 불씨."""
    m, d = mask(IW, IH)
    d.ellipse((cx - 10, by - 26, cx + 10, by), fill=255)
    d.rectangle((cx - 10, by - 18, cx + 10, by - 6), fill=255)
    d.polygon([(cx - 9, by - 24), (cx + 9, by - 24), (cx + 4, by - 32), (cx - 4, by - 32)], fill=255)
    d.rectangle((cx - 3, by - 42, cx + 3, by - 30), fill=255)
    shade_mask(c, m, R_GLASS, base=0.45, gain=0.9, soft=3)
    # 술(아래 2/3) — 비발광 호박
    for y in range(by - 17, by - 1):
        for x in range(cx - 8, cx + 9):
            if c.get(x, y)[3] and c.get(x, y) in R_GLASS:
                u = (x - cx) / 9
                c.px(x, y, qcol([A[18], A[19], A[20], A[21], A[22]], 0.7 - 0.6 * u - 0.15 * (y - (by - 17)) / 16, x, y))
    c.hline(cx - 8, cx + 8, by - 17, A[23])
    c.vline(cx - 6, by - 22, by - 6, G[11]); c.px(cx - 5, by - 23, G[13])   # 유리 빛
    # 헝겊 심지(병목에서 비죽, 늘어진 끝)
    rag = [(cx - 3, by - 44), (cx + 3, by - 44), (cx + 6, by - 50), (cx + 9, by - 47), (cx + 4, by - 40), (cx - 2, by - 40)]
    c.poly(rag, PL[2]); c.line(cx - 3, by - 44, cx + 6, by - 50, PL[4]); c.px(cx + 9, by - 47, PL[1])
    c.hline(cx - 4, cx + 4, by - 40, WD[1]); c.hline(cx - 4, cx + 4, by - 39, WD[3])   # 묶은 끈
    # 헝겊 끝에 붙은 작은 불(자체 발광, 프레임마다 일렁임)
    flame(c, cx + 8, by - 47, 9, 13 + (k % 3), seed=50 + k, tongues=2, core=False)
    c.px(cx + 9, by - 48, A[27])


def strong_swig(c, cx, by, k):
    """납작하고 둥근 흰 유약 도기 술병 + 코르크 + 붉은(호박) 끈 매듭 — 작고 독한 술."""
    m, d = mask(IW, IH)
    d.ellipse((cx - 14, by - 22, cx + 14, by), fill=255)
    d.rectangle((cx - 4, by - 28, cx + 4, by - 18), fill=255)
    d.ellipse((cx - 6, by - 31, cx + 6, by - 26), fill=255)
    shade_mask(c, m, R_GLAZE, base=0.68, gain=0.9, soft=4)
    # 유약 흘림(아래 갈색 띠)
    for x in range(cx - 13, cx + 14):
        y = by - 6 + int(2 * math.sin(x * 0.7))
        if c.get(x, y)[3]:
            c.px(x, y, WD[3]); c.px(x, y + 1, WD[2])
    # 코르크
    c.rect(cx - 3, by - 35, cx + 3, by - 30, WD[3]); c.hline(cx - 3, cx + 3, by - 35, WD[5]); c.vline(cx + 3, by - 35, by - 30, WD[1])
    # 목 끈 + 매듭 꼬리(호박 비발광)
    c.hline(cx - 5, cx + 5, by - 26, A[20]); c.hline(cx - 5, cx + 5, by - 25, A[18])
    c.line(cx + 5, by - 25, cx + 9, by - 18, A[20]); c.line(cx + 6, by - 25, cx + 10, by - 19, A[18])
    # 몸통 종이 딱지(비스듬) + 먹 두 획 — 독주 표시
    c.poly([(cx - 7, by - 15), (cx + 5, by - 17), (cx + 6, by - 7), (cx - 6, by - 5)], G[13])
    c.line(cx - 6, by - 15, cx + 5, by - 17, G[14]); c.line(cx + 6, by - 7, cx - 6, by - 5, PL[2])
    c.line(cx - 4, by - 9, cx + 3, by - 15, SL[1]); c.line(cx - 3, by - 9, cx + 4, by - 15, SL[2])   # 굵은 붓 한 획
    c.px(cx + 3, by - 8, A[20]); c.px(cx + 2, by - 8, A[19])                                         # 붉은 인주 점


def cold_water(c, cx, by, k):
    """반 가른 박 바가지(넓은 사발) 안 찬물(차가운 청회 + 흰 반짝)."""
    rx, ry = 22, 8
    top = by - 14
    m, d = mask(IW, IH)
    d.ellipse((cx - rx, top - ry, cx + rx, top + ry), fill=255)
    d.pieslice((cx - rx, top - 18, cx + rx, by + 2), 0, 180, fill=255)
    shade_mask(c, m, R_GOURD, base=0.5, gain=0.9, soft=4)
    # 테두리 + 물
    for x in range(cx - rx, cx + rx + 1):
        u = (x - cx) / rx
        yy = int(round(ry * math.sqrt(max(0, 1 - u * u))))
        for y in range(top - yy + 2, top + yy - 1):
            v = (y - top) / max(1, ry)
            c.px(x, y, qcol(R_WATER, 0.55 - 0.35 * u - 0.3 * v, x, y))
        c.px(x, top - yy, PL[4] if u < 0.3 else PL[2]); c.px(x, top - yy + 1, R_GOURD[2])
        c.px(x, top + yy, R_GOURD[5] if u < 0 else R_GOURD[3]); c.px(x, top + yy - 1, R_WATER[1])
    # 물결 고리(시간에 따라 퍼짐)
    rr = 3 + (k % 4) * 3
    for a in range(0, 360, 12):
        x = cx - 2 + rr * math.cos(math.radians(a))
        y = top + rr * 0.35 * math.sin(math.radians(a))
        if c.get(round(x), round(y)) in R_WATER:
            c.px(round(x), round(y), G[12] if a < 180 else R_WATER[5])
    # 꼭지 자리(박 꼭지 그루터기)
    c.rect(cx + rx - 1, top - 3, cx + rx + 2, top, WD[2]); c.px(cx + rx + 2, top - 3, WD[4])
    # 반사 줄(흰 하늘빛) + 테 너머 물방울
    c.hline(cx - 12, cx - 4, top - 3, G[14]); c.hline(cx - 10, cx - 6, top - 2, G[12]); c.px(cx - 8, top - 3, G[15])
    for (x, y) in ((cx + 15, top - 9 - (k % 4)), (cx - 18, top - 7 - ((k + 2) % 4))):
        if (k % 4) != 3:
            c.px(x, y, G[13]); c.px(x, y + 1, SL[6])


DRAW = [fire_bottle, strong_swig, cold_water]


def item_frame(i, k):
    c = Canvas(IW, IH)
    cx, by = IPIV
    lift = BOB[k]
    contact(c, cx + 1, by, 15 - lift, 4 - (lift > 2), a=100)
    DRAW[i](c, cx, by - 4 - lift, k)
    # 반짝임 한 번(3·4프레임, 왼쪽 위 어깨) — 줍는 물건 표시
    gx, gy = [(cx - 7, by - 34), (cx - 9, by - 28), (cx - 14, by - 22)][i]
    if k == 3:
        glint(c, gx, gy - lift, True)
    elif k in (2, 4):
        glint(c, gx, gy - lift, False)
    return c.im


def consumables():
    frames = [item_frame(i, k) for i in range(len(KINDS)) for k in range(8)]
    m = {
        "directions": ["any"] * len(KINDS), "rowsAre": "kinds",
        "kinds": [k for k, _ in KINDS], "kindNames": {k: n for k, n in KINDS},
        "kindNamesNote": "이름 임시(설계 i.1 — 정식명은 스토리). HUD·메뉴 아이콘은 UI 파트 몫",
        "usage": "2차 묶음 (i) 1층 '잔' 테마 소모품의 월드 드롭(바닥에 떨어진 것·상점/행상 진열 위). 줍기 판정은 시스템",
        "pivot": {"x": IPIV[0], "y": IPIV[1]}, "anchor": "ground",
        "anchorRule": "pivot = 바닥 접점(그림자 가운데). 진열대(event_peddler_mat.slotAnchors)에서도 같은 pivot",
        "depth": "y",
        "stateLoop": {"idle": True}, "states": {"idle": list(range(8))},
        "bobNote": "물건만 0~3 도트 둥실, 그림자는 제자리(그림에 포함)",
        "spawnNote": "떨어지는 포물선·튕김은 시스템 tween(그림 없음) — 착지 뒤 idle 루프",
        "emissiveColors": EMISSIVE_HEX,
        "emissiveNote": "화염 술병 심지 불씨·반짝임만 자체 발광. 물·술은 비발광",
        "floor": "stage1", "paletteSwap": False,
    }
    write_sheet("items", "consumable_f1", frames, IW, IH, m, rows=len(KINDS), durations=[110] * 8, loop=True)
    return frames
