"""2차 묶음 구조물·소품 (structures/v3, pixelScale 0.5, 64 도트 = 1칸).

- challenge_banner : (f) 도전 성소 = C4 전장 깃발 — 말린 깃발 → 세우기 → 휘날림 루프(등불 켜짐) → 끝남
- still            : 1-2 증류 화로 v3(57 Q43 '2차 묶음') — 벽돌 아궁이 + 구리 단지 + 백조목 관 + 받이 단지
- event_*          : (c) 이벤트 노드 소품(E1·E2·E5·E7/숨은 보물방·E8·E9). E3·E4·E6 은 기존 그림 재사용(아래 REUSE)
- clue_*           : (d) 숨은 노드 단서 소품 2종(술 냄새 나는 배수구 · 금 간 술독)

규칙(structures/NOTES·props_v3 와 같음): 빛 = 좌상단 앞, 상호작용 표지 = 층 강조 25 한 점 + 23 받침(쓰면 꺼짐),
자체 발광 = 램프 23~27(조명 위 가산), 층 테마 구조물은 1층 램프로 그리고 paletteSwap false.
"""
import math

from PIL import Image

from b2 import (Canvas, Rand, G, A, SL, WD, PL, X, U, CLEAR, R_WOOD, R_WOODG, R_IRON, R_STONE, R_NSTONE, R_WSTONE,
                R_CLOTH, R_CLOTHG, R_EARTH, R_COPPER, R_LIQ, R_BONE, FLAME, contact, cyl, plank_box, shade_mask, mask,
                splash, flame, embers, glass_lantern, stone_blob, face, grain, ell_mask, poly_mask, outline, qcol,
                clamp, lam, write_sheet, EMISSIVE_HEX, tohex, pcommon)

R_CLAY = [SL[0], WD[1], WD[2], PL[0], PL[1], PL[2], PL[3]]           # 옹기·도기(어두운 흙)
R_GLAZE = [SL[1], PL[0], PL[1], PL[2], PL[3], PL[4], G[12]]          # 흰 유약 도기
R_BRICK = [SL[0], WD[1], WD[2], A[17], A[18], WD[4], PL[1]]          # 그을린 벽돌(층 램프 어두운 칸 섞음)
R_BANNER = [A[16], A[17], A[18], A[19], A[20], A[21]]                # 깃발 천(층 램프 비발광 칸)
R_GLASS = [SL[0], SL[1], SL[2], SL[3], SL[5], SL[7]]                 # 어두운 유리
MARK, MARK_BASE, MARK_OFF, MARK_OFF2 = A[25], A[23], A[19], A[17]

REUSE = {
    "E3 버려진 징집병": "적 v3 dummy_death 마지막 프레임(누운 모습) — 설계 c.1 재사용",
    "E4 일기장의 빈 쪽": "UI 일기장 키트(UI 파트) — 월드 소품 없음",
    "E6 술독 깨기 내기": "1-1 독주 술통 barrel ×6 + fx fire_pool — 새 그림 없음",
    "E2·E5 카운터": "1-5 counter(기존) 옆에 event_last_cup·event_tasting_tray 를 둔다",
    "E8 묘": "C3 grave(기존) 앞에 event_offering_cup",
    "E7 숨은 벽": "1-6 cellar_wall(기존) 뒤 저장고에 event_cache",
}


def mark(c, x, y, on=True):
    """상호작용 표지: 25 한 점 + 아래 23 받침(쓰면 19/17 로 식음)."""
    c.px(x, y, MARK if on else MARK_OFF)
    c.px(x, y + 1, MARK_BASE if on else MARK_OFF2)


def L(color, radius, intensity, ox, oy, amp=0.1, hz=5):
    return {"color": color, "radius": radius, "intensity": intensity, "flicker": {"amp": amp, "hz": hz},
            "offset": {"x": ox, "y": oy}}


def states_json(names_counts):
    """[(이름, 프레임 수, loop)] → states·stateLoop (프레임 번호 연속 배정)."""
    st, lp, i = {}, {}, 0
    for n, k, loop in names_counts:
        st[n] = list(range(i, i + k)); lp[n] = loop; i += k
    return st, lp


# ====================================================================== 도전 성소 깃발
BW, BH = 192, 300
BPIV = (96, 292)


def cairn(c, cx, by, seed=3):
    """깃대 밑 돌무더기."""
    contact(c, cx + 3, by - 2, 44, 9)
    r = Rand(seed)
    pts = [(-26, -6, 13, 9), (22, -6, 14, 9), (-4, -4, 16, 9), (-15, -16, 11, 8), (12, -17, 12, 8), (-1, -25, 10, 7),
           (30, -2, 8, 5), (-33, -1, 7, 5)]
    for (dx, dy, rx, ry) in pts:
        stone_blob(c, cx + dx, by + dy, rx + r.i(-1, 1), ry, R_STONE, seed * 13 + dx, soft=2)


def pole(c, cx, top, by):
    for y in range(top, by - 18):
        c.hline(cx - 3, cx - 2, y, WD[4]); c.hline(cx - 1, cx + 1, y, WD[3]); c.px(cx + 2, y, WD[1]); c.px(cx + 3, y, WD[0])
        if y % 23 == 0:
            c.hline(cx - 2, cx + 1, y, WD[2])
    # 꼭대기 쇠 촉
    c.poly([(cx - 4, top), (cx + 4, top), (cx, top - 12)], G[5]); c.line(cx - 3, top - 1, cx, top - 11, G[8])
    c.hline(cx - 4, cx + 4, top + 1, G[3])


def crossbar(c, cx, y, half=40):
    for x in range(cx - half, cx + half + 1):
        c.px(x, y, WD[4]); c.px(x, y + 1, WD[3]); c.px(x, y + 2, WD[3]); c.px(x, y + 3, WD[1])
    for x in (cx - half, cx + half):
        c.rect(x - 1, y - 1, x + 1, y + 4, G[4]); c.px(x - 1, y - 1, G[7])
    # 묶은 끈(가로대-깃대)
    for k in range(5):
        c.line(cx - 4, y - 2 + k, cx + 4, y + 2 + k, WD[2] if k % 2 else WD[4])


def banner_cloth(w, h):
    """평평한 깃발 천(무늬·문장 포함) — 휘날림은 warp 로. 아래는 제비꼬리 + 찢김."""
    c = Canvas(w, h)
    r = Rand(17)
    cut = [int(14 * (1 - abs((x / (w - 1)) - 0.5) * 2)) for x in range(w)]  # 가운데 파인 제비꼬리
    rag = [r.i(0, 3) for _ in range(w)]
    for x in range(w):
        for y in range(h - cut[x] - rag[x]):
            u = x / (w - 1)
            s = 0.62 - 0.25 * u + 0.08 * math.sin(y * 0.3 + x * 0.05)
            c.px(x, y, qcol(R_BANNER, s, x, y))
    # 가장자리 테(어두운 단)
    for x in range(w):
        c.px(x, 0, R_BANNER[1]); c.px(x, 1, R_BANNER[4]); c.px(x, 4, R_BANNER[2])
    for y in range(h):
        for x in (0, w - 1):
            if c.get(x, y)[3]:
                c.px(x, y, R_BANNER[1])
        for x in (3, w - 4):
            if c.get(x, y)[3]:
                c.px(x, y, R_BANNER[2])
    # 문장: 엇갈린 두 칼 + 위 잔(뼈빛 물감, 비발광)
    cx, cy = w // 2, int(h * 0.42)
    paint, paint_d = PL[4], PL[2]
    for s_ in (-1, 1):
        for t in range(-16, 17):
            x, y = cx + s_ * t * 0.75, cy + t
            c.px(round(x), round(y), paint); c.px(round(x) + 1, round(y), paint_d)
        c.hline(cx + s_ * 9 - 4, cx + s_ * 9 + 4, cy + 10, paint)   # 코등이
    c.poly([(cx - 8, cy - 22), (cx + 8, cy - 22), (cx + 5, cy - 15), (cx - 5, cy - 15)], paint)
    c.vline(cx, cy - 15, cy - 11, paint); c.hline(cx - 4, cx + 4, cy - 10, paint_d)
    # 낡은 얼룩·구멍
    for k in range(6):
        x, y = r.i(6, w - 7), r.i(10, h - 26)
        c.px(x, y, R_BANNER[1]); c.px(x + 1, y, R_BANNER[2])
    for (x, y) in ((w - 14, h - 34), (10, h - 44)):
        c.ellipse((x - 2, y - 2, x + 2, y + 2), CLEAR)
    return c.im


BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def warp_cloth(cloth, phase, amp):
    """윗변 고정, 아래로 갈수록 세로 물결이 가로로 흔들림 + 기울기 셰이딩."""
    w, h = cloth.size
    out = Image.new("RGBA", (w + 2 * amp + 4, h), (0, 0, 0, 0))
    src = cloth.load()
    dst = out.load()
    for y in range(h):
        t = y / h
        dx = amp * t * math.sin(phase - y * 0.09) + amp * 0.3 * t
        for x in range(w):
            px = src[x, y]
            if not px[3]:
                continue
            # 가로 주름: x 따라 물결 → 밝기 바꿈
            wave = math.sin(phase * 1.3 + x * 0.16 - y * 0.05) * (0.25 + 0.75 * t) * (amp / 10)
            col = px
            if px in R_BANNER:
                k = R_BANNER.index(px)
                th = (BAYER4[y % 4][x % 4] + 0.5) / 16
                w6 = wave * 0.6
                step = (1 if w6 > th else 0) if w6 >= 0 else (-1 if -w6 > th else 0)
                k2 = max(1, min(len(R_BANNER) - 1, k + step))
                col = R_BANNER[k2]
            xx = int(round(x + dx + amp + 2))
            if 0 <= xx < out.width:
                dst[xx, y] = col
    return out


def banner_frame(state, k=0):
    c = Canvas(BW, BH)
    cx, by = BPIV
    top = by - 252
    bar_y = top + 14
    cairn(c, cx, by)
    pole(c, cx, top, by)
    crossbar(c, cx, bar_y, 50)
    cloth_w, cloth_h = 70, 118
    lit = state in ("active", "raise") and (state == "active" or k >= 4)
    if state == "idle":
        # 말린 깃발: 가로대에 감겨 매달린 두루마리 + 끈 매듭(표지)
        for x in range(cx - 38, cx + 39):
            if abs(x - cx) < 5:
                continue
            for y in range(bar_y + 4, bar_y + 16):
                v = (y - (bar_y + 10)) / 6
                c.px(x, y, qcol(R_BANNER, 0.75 - 0.6 * v, x, y))
        for x in (cx - 26, cx + 26):
            c.vline(x, bar_y + 3, bar_y + 17, WD[1]); c.vline(x + 1, bar_y + 3, bar_y + 17, WD[4])
        c.vline(cx + 26, bar_y + 17, bar_y + 25, WD[3])
        mark(c, cx + 26, bar_y + 26, True)
    else:
        if state == "raise":
            frac = (k + 1) / 5
            amp = 3 + k
            phase = k * 0.9
        elif state == "active":
            frac, amp, phase = 1.0, 7, k * (2 * math.pi / 6)
        else:
            frac, amp, phase = 1.0, 1, 0.4
        cl = banner_cloth(cloth_w, cloth_h)
        hh = max(8, int(cloth_h * frac))
        cl = cl.crop((0, cloth_h - hh, cloth_w, cloth_h)) if state == "raise" else cl
        wv = warp_cloth(cl, phase, amp)
        c.paste(wv, cx - cloth_w // 2 - amp - 2, bar_y + 4)
        # 남은 말린 부분(세우는 중)
        if state == "raise" and frac < 1:
            for x in range(cx - cloth_w // 2, cx + cloth_w // 2):
                for y in range(bar_y + 4, bar_y + 10):
                    v = (y - (bar_y + 7)) / 3
                    c.px(x, y, qcol(R_BANNER, 0.75 - 0.6 * v, x, y))
    # 가로대 왼끝에 매단 등불
    lx, ly = cx - 48, bar_y + 6
    c.vline(lx, ly, ly + 8, G[4])
    if lit:
        glass_lantern(c, lx, ly + 9, 16, 26)
    else:
        glass_lantern(c, lx, ly + 9, 16, 26)
        gy0, gy1 = ly + 9 + 26 // 5 + 1, ly + 9 + 26 - 4
        for y in range(gy0, gy1):
            for x in range(lx - 7, lx + 8):
                if c.get(x, y) and c.get(x, y)[:3] in [A[i][:3] for i in range(22, 28)]:
                    c.px(x, y, R_GLASS[2] if (x + y) % 3 else R_GLASS[3])
        c.px(lx - 3, gy0 + 2, G[8])
    if state == "active":
        embers(c, lx, ly + 8, 3, 5, 40 + k)
    return c.im


def challenge_banner():
    frames = [banner_frame("idle")] + [banner_frame("raise", k) for k in range(5)] + \
             [banner_frame("active", k) for k in range(6)] + [banner_frame("cleared")]
    st, lp = states_json([("idle", 1, False), ("raise", 5, False), ("active", 6, True), ("cleared", 1, False)])
    durs = [100] + [90, 90, 100, 110, 140] + [120] * 6 + [100]
    lx, ly = BPIV[0] - 48, BPIV[1] - 252 + 14 + 6 + 9 + 13
    m = {
        "id": "challenge_banner", "kind": "C4", "name": "도전 성소 — 전장 깃발(임시)",
        "usage": "2차 묶음 (f) 도전 성소: 잔 일반 전투 노드 35%에 놓임. 첫 웨이브 전 E 로 세우면 엘리트 1 + 웨이브 +1 (57 Q38)",
        "footprint": [1, 1], "solid": True, "depth": "y", "pivot": {"x": BPIV[0], "y": BPIV[1]}, "occludeAbove": 60,
        "states": st, "stateLoop": lp,
        "stateFlow": "idle(말린 깃발, 표지 켜짐) → E → raise(5f, 끝에 등불 켜짐) → active(휘날림 루프, 도전 중) → 클리어 시 cleared(늘어진 깃발, 등불 꺼짐)",
        "interact": "E", "interactMark": {"x": BPIV[0] + 26, "y": BPIV[1] - 252 + 14 + 26},
        "light": L("#e8b858", 220, 0.9, lx, ly, 0.12, 6),
        "lightByState": {"idle": None, "raise": "마지막 프레임부터", "active": "켜짐", "cleared": None},
        "emissiveColors": EMISSIVE_HEX,
        "floor": "common", "paletteSwap": True,
        "paletteSwapNote": "깃발 천·등불은 층 램프(16~27) → 층마다 그 층 강조색 깃발(C 공용 구조물 규칙)",
        "replaces": "structures/battlefield_banner(49 v1 장식)는 그대로 둔다 — 이 시트는 상호작용 성소 전용",
    }
    write_sheet("structures", "challenge_banner", frames, BW, BH, m, rows=1, durations=durs, loop=False)
    return frames, BPIV


# ====================================================================== 증류 화로 v3
SW, SH = 192, 240
SPIV = (80, 232)


def brick_box(c, x0, y0, x1, y1, seed=5):
    """그을린 벽돌 아궁이(정면 + 윗면 얇게)."""
    r = Rand(seed)
    for y in range(y0, y1 + 1):
        row = (y - y0) // 9
        for x in range(x0, x1 + 1):
            off = 0 if row % 2 else 9
            mortar = (y - y0) % 9 == 0 or (x - x0 + off) % 18 == 0
            t = (x - x0) / max(1, x1 - x0)
            s = 0.62 - 0.35 * t + (0.08 if (x * 7 + row * 13) % 5 == 0 else 0) - 0.1 * ((y - y0) / (y1 - y0))
            c.px(x, y, R_BRICK[1] if mortar else qcol(R_BRICK, s, x, y))
    for x in range(x0, x1 + 1):
        c.px(x, y0, R_BRICK[5]); c.px(x, y0 + 1, R_BRICK[4])
    c.vline(x1, y0, y1, SL[0]); c.hline(x0, x1, y1, SL[0]); c.vline(x0, y0, y1, R_BRICK[2])
    # 그을음
    for k in range(40):
        x, y = r.i(x0 + 2, x1 - 2), r.i(y0 + 2, y0 + 16)
        if c.get(x, y) in R_BRICK:
            c.px(x, y, R_BRICK[max(0, R_BRICK.index(c.get(x, y)) - 1)])


def still_frame(k, lit=True):
    c = Canvas(SW, SH)
    cx, by = SPIV
    contact(c, cx + 18, by - 2, 70, 10)
    # 아궁이 (폭 76)
    x0, x1, y0 = cx - 38, cx + 38, by - 64
    brick_box(c, x0, y0, x1, by - 2)
    # 아치 불구멍
    ax0, ax1, ay = cx - 20, cx + 20, by - 40
    m, d = mask(SW, SH)
    d.rectangle((ax0, ay, ax1, by - 6), fill=255)
    d.pieslice((ax0, ay - 16, ax1, ay + 16), 180, 360, fill=255)
    c.mask_fill(m, SL[0])
    if lit:
        flame(c, cx, by - 6, 34, 34 + (k % 3) * 3, seed=20 + k, tongues=5)
        for x in range(ax0 + 2, ax1 - 1):        # 숯
            c.px(x, by - 7, A[22] if (x + k) % 3 else A[25]); c.px(x, by - 6, A[19])
    else:
        for x in range(ax0 + 2, ax1 - 1):
            c.px(x, by - 7, A[18] if (x % 4) else A[20]); c.px(x, by - 6, SL[1])
    # 아치 테두리 벽돌(쐐기)
    for t in range(0, 181, 12):
        a = math.radians(180 + t)
        for rr in (21, 22, 23):
            xx, yy = cx + rr * math.cos(a), ay + rr * math.sin(a) * 0.76
            c.px(round(xx), round(yy), R_BRICK[5] if t < 90 else R_BRICK[3])
    # 구리 단지(양파꼴) — 윗면에 앉음
    pot_cy, prx = y0 - 26, 30
    pm = Image.new("L", (SW, SH), 0)
    from PIL import ImageDraw
    dd = ImageDraw.Draw(pm)
    dd.ellipse((cx - prx, pot_cy - 26, cx + prx, pot_cy + 26), fill=255)
    dd.rectangle((cx - 20, pot_cy + 14, cx + 20, y0 + 2), fill=255)
    dd.polygon([(cx - 9, pot_cy - 24), (cx + 9, pot_cy - 24), (cx + 5, pot_cy - 46), (cx - 5, pot_cy - 46)], fill=255)
    shade_mask(c, pm, R_COPPER, base=0.5, gain=0.95, soft=6, tilt=0.12)
    # 구리 띠·리벳
    for yy in (pot_cy - 2, pot_cy + 14):
        for x in range(cx - prx + 2, cx + prx - 1):
            u = (x - cx) / prx
            if c.get(x, yy + int(4 * math.sqrt(max(0, 1 - u * u))))[3]:
                c.px(x, yy + int(4 * math.sqrt(max(0, 1 - u * u))), R_COPPER[1])
    for u in (-0.6, -0.2, 0.2, 0.6):
        c.px(int(cx + u * prx), pot_cy + 3, A[23]); c.px(int(cx + u * prx) + 1, pot_cy + 4, R_COPPER[0])
    # 백조목 관: 단지 목 위 → 오른쪽 아래 받이 단지로
    pts = []
    for i in range(60):
        t = i / 59
        x = cx + 2 + t * 74
        y = (pot_cy - 46) - 10 * math.sin(math.pi * min(1, t * 1.6)) + max(0, t - 0.55) * 120
        pts.append((x, y))
    for i, (x, y) in enumerate(pts):
        for dy in range(-2, 3):
            col = R_COPPER[4] if dy < -1 else (R_COPPER[3] if dy < 1 else R_COPPER[1])
            c.px(round(x), round(y) + dy, col)
    # 냉각 통(관을 감싼 나무 통 — 오른쪽)
    vx, vtop, vbot = cx + 70, by - 70, by - 26
    cyl(c, vx, vtop, vbot, 15, R_WOOD, bulge=0.06, staves=5, hoops=((vtop + 5, 2), (vbot - 6, 2)), seed=8)
    # 받이 단지 + 꼭지 방울(표지)
    jx, jby = cx + 92, by - 2
    contact(c, jx + 2, jby, 14, 4)
    jm = Image.new("L", (SW, SH), 0)
    dj = ImageDraw.Draw(jm)
    dj.ellipse((jx - 10, jby - 22, jx + 10, jby), fill=255)
    dj.rectangle((jx - 4, jby - 28, jx + 4, jby - 18), fill=255)
    shade_mask(c, jm, R_CLAY, base=0.5, gain=0.8, soft=3)
    tap_x, tap_y = vx + 13, vbot - 4
    c.hline(tap_x, tap_x + 5, tap_y, G[6]); c.px(tap_x + 5, tap_y + 1, G[4])
    drip_y = tap_y + 3 + (k * 4) % 18
    if lit:
        mark(c, tap_x + 5, tap_y + 2, True)
        if drip_y < jby - 28:
            c.px(tap_x + 5, drip_y, A[24]); c.px(tap_x + 5, drip_y + 1, A[22])
        # 김(단지 꼭대기 위로)
        r = Rand(60 + k)
        for j in range(10):
            yy = pot_cy - 52 - j * 4 - (k * 3) % 4
            xx = cx + int(5 * math.sin(j * 0.8 + k * 1.05)) + r.i(-1, 1)
            col = PL[3] if j < 4 else PL[2]
            if (j + k) % 2 == 0 or j < 3:
                c.px(xx, yy, col); c.px(xx + 1, yy - 1, PL[1])
    else:
        mark(c, tap_x + 5, tap_y + 2, False)
    return c.im


def still():
    frames = [still_frame(k) for k in range(6)] + [still_frame(0, lit=False)]
    st, lp = states_json([("active", 6, True), ("used", 1, False)])
    st["idle"] = [0]; lp["idle"] = False
    cx, by = SPIV
    m = {
        "id": "still", "kind": "1-2", "name": "증류 화로(임시)",
        "usage": "1-2 증류 화로 v3 — 통과하면 무기에 불 6초(fireWeapon, 계약 ui §9.2). 57 Q43 '증류 화로 구조물은 2차 묶음', 빌드 축 저주 ★4 '불붙은 혀' 획득처",
        "replaces": "structures/still (47 v1 16×32) — v3 → 구 순 우선 로드",
        "footprint": [1, 1], "solid": True, "depth": "y", "pivot": {"x": cx, "y": by}, "occludeAbove": 70,
        "footprintNote": "막힘 = 아궁이 아래 1칸(v1 과 같음). 오른쪽 냉각 통·받이 단지(약 1.3칸)는 그림만 — 통과 가능(제안)",
        "states": st, "stateLoop": lp,
        "stateNote": "idle = active 0번(늘 불이 있음, v1 과 같음) · used = 불 꺼짐(시스템이 재사용 대기·층 소진을 쓸 때만)",
        "interact": "pass",
        "fireBox": {"x": cx - 18, "y": by - 44, "w": 36, "h": 38, "note": "불꽃 영역(프레임 도트 좌표). 무기 궤적 통과 판정용 참고값(v1 fireBox 와 같은 뜻)"},
        "light": L("#eecc78", 300, 1.1, cx, by - 24, 0.18, 7),
        "lightByState": {"active": "켜짐", "used": None},
        "emissiveColors": EMISSIVE_HEX,
        "floor": "stage1", "paletteSwap": False,
    }
    write_sheet("structures", "still", frames, SW, SH, m, rows=1, durations=[110, 120, 100, 130, 110, 120, 200], loop=False)
    return frames, SPIV


# ====================================================================== 이벤트 소품
def round_table(c, cx, by, rx=34, h=40, seed=4):
    """외다리 원탁: 다리 + 둥근 상판(3/4 시점 타원)."""
    contact(c, cx + 3, by - 1, rx - 4, 6)
    ry = int(rx * 0.42)
    top = by - h
    # 다리(굵은 기둥 + 받침 십자)
    for y in range(top + ry, by - 4):
        c.hline(cx - 4, cx - 2, y, WD[4]); c.hline(cx - 1, cx + 2, y, WD[3]); c.hline(cx + 3, cx + 4, y, WD[1])
    c.poly([(cx - 18, by - 1), (cx + 18, by - 1), (cx + 6, by - 7), (cx - 6, by - 7)], WD[2])
    c.hline(cx - 18, cx + 18, by - 1, WD[0]); c.hline(cx - 6, cx + 6, by - 7, WD[4])
    # 상판 두께
    for y in range(top, top + 5):
        for x in range(cx - rx, cx + rx + 1):
            u = (x - cx) / rx
            yy = y + int(round(ry * math.sqrt(max(0, 1 - u * u))))
            c.px(x, yy, qcol(R_WOOD, 0.45 - 0.3 * u, x, yy))
    for y in range(top - ry, top + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - top) / ry) ** 2
            if d <= 1:
                s = 0.78 - 0.25 * ((x - cx) / rx) - 0.12 * ((y - top) / ry)
                if d > 0.86:
                    s = 0.95 if y < top else 0.4
                c.px(x, y, qcol(R_WOOD, s, x, y))
    grain(c, cx - rx + 4, top - ry + 3, cx + rx - 4, top + ry - 3, R_WOOD, seed, vertical=False, density=0.05)
    return top, ry


def goblet(c, cx, by, h=34, full=True, glow=True):
    """굽 높은 백랍 잔(큰 잔). by = 굽 밑."""
    rx = 11
    # 굽
    c.hline(cx - 8, cx + 8, by, G[3]); c.hline(cx - 7, cx + 7, by - 1, G[6]); c.hline(cx - 5, cx + 5, by - 2, G[5])
    for y in range(by - 14, by - 2):
        c.hline(cx - 2, cx - 1, y, G[8]); c.px(cx, y, G[6]); c.px(cx + 1, y, G[4]); c.px(cx + 2, y, G[3])
    c.hline(cx - 4, cx + 4, by - 9, G[7])
    # 잔 몸
    top = by - h
    for y in range(top, by - 13):
        t = (y - top) / (h - 13)
        half = int(round(rx * (1 - 0.55 * t ** 2)))
        for x in range(cx - half, cx + half + 1):
            u = (x - cx) / max(1, half)
            c.px(x, y, qcol(R_IRON, 0.62 - 0.45 * u + 0.1 * (1 - t), x, y))
        c.px(cx - half, y, G[8]); c.px(cx + half, y, G[2])
    # 입 테 + 술면
    for x in range(cx - rx, cx + rx + 1):
        u = (x - cx) / rx
        yy = int(round(3 * math.sqrt(max(0, 1 - u * u))))
        c.px(x, top - yy, G[10]); c.px(x, top + yy, G[6])
        if full:
            for y in range(top - yy + 1, top + yy):
                c.px(x, y, A[22] if u < -0.2 else A[20])
        else:
            for y in range(top - yy + 1, top + yy):
                c.px(x, y, SL[1])
    if full and glow:
        mark(c, cx - 4, top - 1, True)
    # 장식 띠(호박 점)
    c.hline(cx - 8, cx + 8, top + 7, G[3]); c.px(cx - 3, top + 7, A[21]); c.px(cx + 3, top + 7, A[19])


def tipped_goblet(c, x, y):
    """옆으로 쓰러진 빈 잔 + 엎질러진 자국. (x,y)=잔 입 왼쪽."""
    splash(c, x - 10, y + 4, 12, 3, seed=9, blobs=3)
    for k in range(22):
        t = k / 21
        half = int(round(6 * (1 - 0.5 * t ** 2)))
        for d in range(-half, half + 1):
            c.px(x + k, y + d, qcol(R_IRON, 0.6 - 0.08 * d, x + k, y + d))
    c.ellipse((x - 2, y - 6, x + 2, y + 6), SL[1]); c.vline(x - 2, y - 5, y + 5, G[8])
    c.hline(x + 22, x + 30, y, G[6]); c.vline(x + 31, y - 5, y + 5, G[5])


def event_last_cup():
    W, H, piv = 128, 144, (64, 136)
    fr = []
    for used in (False, True):
        c = Canvas(W, H)
        top, ry = round_table(c, 64, 136, rx=38, h=58)
        if not used:
            goblet(c, 60, top + 4, h=40, full=True)
            # 촛농 녹은 짧은 초(분위기·약한 빛)
            c.rect(84, top - 10, 87, top + 1, PL[4]); c.vline(84, top - 10, top + 1, G[13]); c.px(86, top - 11, A[26]); c.px(86, top - 12, A[25])
        else:
            tipped_goblet(c, 44, top - 2)
            c.rect(84, top - 10, 87, top + 1, PL[4]); c.vline(84, top - 10, top + 1, G[13]); c.px(86, top - 11, SL[2])
        fr.append(c.im)
    m = {
        "id": "event_last_cup", "event": "E2 마지막 한 잔(임시)",
        "usage": "이벤트 노드 E2 — 탁자 위 큰 잔. 1-5 카운터 옆/전투장 가운데. E → 이벤트 메뉴(구조물 메뉴 틀 재사용, 설계 c.2)",
        "footprint": [1, 1], "solid": True, "depth": "y", "pivot": {"x": piv[0], "y": piv[1]}, "occludeAbove": 40,
        "states": {"idle": [0], "used": [1]}, "interact": "E",
        "light": L("#eecc78", 90, 0.5, 86, 136 - 58 - 11, 0.15, 6), "lightByState": {"idle": "켜짐", "used": None},
        "emissiveColors": EMISSIVE_HEX, "floor": "stage1", "paletteSwap": False,
    }
    write_sheet("structures", "event_last_cup", fr, W, H, m, durations=[100, 100])
    return fr, piv


def small_cup(c, cx, by, fill):
    """작은 시음 잔(도기 흰 유약). fill 0..1."""
    for y in range(by - 10, by + 1):
        t = (y - (by - 10)) / 10
        half = int(round(5 - 1.5 * t))
        for x in range(cx - half, cx + half + 1):
            c.px(x, y, qcol(R_GLAZE, 0.75 - 0.5 * (x - cx) / max(1, half), x, y))
    for x in range(cx - 5, cx + 6):
        c.px(x, by - 11, G[12]); c.px(x, by - 10, (A[21] if fill > 0.5 else A[19]) if fill > 0 and abs(x - cx) < 5 else R_GLAZE[1])
    c.hline(cx - 4, cx + 4, by + 1, SL[1])


def event_tasting_tray():
    W, H, piv = 128, 160, (64, 152)
    fr = []
    for used in (False, True):
        c = Canvas(W, H)
        pcommon.barrel_c(c, 64, 152, rx=28, h=64, seed=3, spill=False)
        top = 152 - int(28 * 0.42) - 64 + 9   # 쟁반을 뚜껑에 얹힘(떠 보이지 않게)
        # 쟁반(나무 판, 3/4) — 통 뚜껑 위
        plank_box(c, 26, top - 18, 76, 6, 14, ramp=R_WOODG, seed=6, planks=3, slats=False, brace=False)
        fills = (1.0, 0.7, 0.4) if not used else (0.0, 0.0, 0.0)
        for i, (x, f) in enumerate(zip((40, 58, 76), fills)):
            if used and i == 2:
                # 쓰러진 잔
                c.ellipse((70, top - 14, 80, top - 8), R_GLAZE[3]); c.ellipse((78, top - 14, 82, top - 8), SL[1])
                continue
            small_cup(c, x, top - 8, f)
        # 병(짙은 유리, 호박 술)
        bx = 92
        for y in range(top - 46, top - 6):
            half = 2 if y < top - 34 else 6
            for x in range(bx - half, bx + half + 1):
                col = qcol(R_GLASS, 0.7 - 0.5 * (x - bx) / max(1, half), x, y)
                if not used and y > top - 26 and abs(x - bx) < half:
                    col = A[20] if x > bx else A[22]
                c.px(x, y, col)
        c.rect(bx - 2, top - 50, bx + 2, top - 46, WD[3])
        if not used:
            mark(c, 58, top - 21, True)
        fr.append(c.im)
    m = {
        "id": "event_tasting_tray", "event": "E5 양조장 시음회(임시)",
        "usage": "이벤트 노드 E5 — 술통 위 시음 쟁반(잔 3 + 병). 1-5 카운터와 함께 놓는다(설계 c.1 재사용 '카운터 + 술통')",
        "footprint": [1, 1], "solid": True, "depth": "y", "pivot": {"x": piv[0], "y": piv[1]}, "occludeAbove": 30,
        "states": {"idle": [0], "used": [1]}, "interact": "E",
        "emissiveColors": EMISSIVE_HEX, "floor": "stage1", "paletteSwap": False,
    }
    write_sheet("structures", "event_tasting_tray", fr, W, H, m, durations=[100, 100])
    return fr, piv


def event_peddler_mat():
    W, H, piv = 224, 160, (112, 150)
    c = Canvas(W, H)
    # 깔개(바닥 천, 3/4 평행사변형) + 술 장식 끝
    mx0, mx1, my0, my1 = 30, 200, 112, 150
    for y in range(my0, my1):
        t = (y - my0) / (my1 - my0)
        sk = int(10 * (1 - t))
        for x in range(mx0 + sk, mx1 + sk - 10):
            stripe = ((x - sk) // 14) % 3
            ramp = R_CLOTH if stripe != 1 else R_BANNER
            c.px(x, y, qcol(ramp, 0.62 - 0.25 * t + (0.06 if (x + y) % 9 == 0 else 0), x, y))
    for x in range(mx0, mx1):
        c.px(x + 10, my0, PL[4]); c.px(x, my1 - 1, SL[1])
    for x in range(mx0 + 2, mx1 - 8, 5):
        c.vline(x, my1, my1 + 2, PL[1])
    # 짐 보따리(뒤쪽, 왼편): 지게 틀 + 큰 자루 + 매단 병들
    contact(c, 60, 112, 36, 7)
    for x in (40, 78):
        c.vline(x, 40, 112, WD[3]); c.vline(x + 1, 40, 112, WD[1]); c.px(x, 40, WD[5])
    for y in (60, 92):
        c.hline(40, 79, y, WD[4]); c.hline(40, 79, y + 1, WD[1])
    pcommon.sack_c(c, 36, 44, 48, 60, R_CLOTH, 11)
    pcommon.sack_c(c, 44, 18, 32, 32, R_CLOTHG, 12)
    for (x, y) in ((34, 70), (86, 66)):       # 매단 병
        c.vline(x, y - 8, y, WD[1])
        c.ellipse((x - 4, y, x + 4, y + 12), R_GLASS[2]); c.ellipse((x - 3, y + 5, x + 3, y + 11), A[20]); c.px(x - 2, y + 2, G[10])
    # 진열 자리 3: 작은 나무 접시
    slots = [(116, 128), (146, 128), (176, 128)]
    for (x, y) in slots:
        c.ellipse((x - 12, y - 4, x + 12, y + 5), WD[1]); c.ellipse((x - 11, y - 4, x + 11, y + 3), WD[3]); c.hline(x - 8, x + 4, y - 3, WD[5])
    mark(c, 200, 116, True)
    m = {
        "id": "event_peddler_mat", "event": "E1 떠돌이 독주 행상(임시) · 숨은 노드 행상",
        "usage": "이벤트 노드 E1 — 행상 깔개 + 짐 보따리. 행상 NPC 는 신규 적 '독주 행상'(S-7) 그림의 비적대 변형이 옆에 선다(설계 c.1). 진열 3칸 위에 층 소모품·독주 월드 그림을 얹는다",
        "footprint": [3, 1], "solid": False, "solidNote": "깔개는 통과. 보따리 1칸(왼쪽)만 막힘을 원하면 시스템이 blockTiles 사용(제안)",
        "blockTiles": [[0, 0]], "depth": "y", "pivot": {"x": piv[0], "y": piv[1]}, "occludeAbove": 40,
        "slotAnchors": [{"x": x, "y": y} for (x, y) in slots],
        "slotNote": "진열 칸 중심(도트). 아이템 그림(items/v3/consumable_f1 등)의 pivot 을 여기에 둔다 — 고르면 그 칸을 비운다",
        "states": {"idle": [0]}, "interact": "E",
        "interactMark": {"x": 200, "y": 116},
        "emissiveColors": EMISSIVE_HEX, "floor": "stage1", "paletteSwap": False,
    }
    write_sheet("structures", "event_peddler_mat", [c.im], W, H, m, durations=[100])
    return [c.im], piv


def bottle(c, x, by, h=26, liquor=True, seed=1):
    for y in range(by - h, by + 1):
        t = (y - (by - h)) / h
        half = 2 if t < 0.35 else 5
        for xx in range(x - half, x + half + 1):
            col = qcol(R_GLASS, 0.7 - 0.5 * (xx - x) / max(1, half), xx, y)
            if liquor and t > 0.55 and abs(xx - x) < half:
                col = A[21] if xx < x else A[19]
            c.px(xx, y, col)
    c.rect(x - 2, by - h - 3, x + 2, by - h, WD[3]); c.px(x - 3, by - h + 12, G[10])


def event_cache():
    W, H, piv = 160, 144, (80, 136)
    fr = []
    for state in ("closed", "open", "used"):
        c = Canvas(W, H)
        contact(c, 82, 135, 66, 9)
        # 짚 깔린 바닥
        r = Rand(4)
        for k in range(160):
            x, y = r.i(16, 146), r.i(118, 136)
            c.line(x, y, x + r.i(2, 6), y + r.i(-1, 1), PL[2] if k % 3 else PL[3])
        # 큰 궤짝(나무 + 쇠 모서리)
        plank_box(c, 30, 64, 100, 44, 26, ramp=R_WOOD, seed=13, planks=5)
        for (x, y) in ((30, 90), (125, 90), (30, 127), (125, 127)):
            c.rect(x, y - 6, x + 5, y, G[4]); c.px(x + 1, y - 5, G[8])
        if state == "closed":
            # 덮은 짚단·자루 + 밀랍 봉인(표지)
            pcommon.sack_c(c, 92, 40, 34, 30, R_CLOTH, 5)
            for k in range(60):
                x, y = r.i(36, 96), r.i(62, 72)
                c.line(x, y, x + r.i(3, 8), y - r.i(0, 3), PL[3] if k % 2 else PL[1])
            c.ellipse((76, 94, 86, 104), A[19]); c.ellipse((78, 95, 84, 101), A[21]); mark(c, 80, 97, True)
        else:
            # 열린 안쪽(어둠) + 병목들 / 비면 빈 칸
            c.rect(33, 66, 127, 88, SL[0])
            c.rect(33, 66, 127, 68, SL[1])
            if state == "open":
                for i, x in enumerate(range(44, 122, 13)):
                    bottle(c, x, 86, h=22 + (i % 2) * 4, seed=i)
                    if i % 2 == 0:
                        c.px(x - 1, 86 - 22 - (i % 2) * 4 + 6, A[25])  # 병 어깨 반짝임(자체 발광 — 보물감)
                mark(c, 120, 60, True)
            # 열린 뚜껑(뒤로 젖혀 세움)
            # 뒤로 젖혀 세운 뚜껑: 안쪽 면(어두운 판) + 쇠띠 + 위 모서리 빛
            for y in range(40, 65):
                for x in range(32, 129):
                    t = (y - 40) / 24
                    col = qcol(R_WOOD, 0.42 - 0.2 * t - 0.15 * (x - 32) / 96, x, y)
                    c.px(x, y, col)
            for x in range(32, 129, 19):
                c.vline(x, 41, 64, WD[1])
            for yy in (46, 58):
                c.hline(32, 128, yy, G[3]); c.hline(32, 128, yy + 1, G[2])
            c.hline(32, 128, 40, WD[5]); c.hline(32, 128, 39, WD[3]); c.vline(128, 40, 64, WD[0])
            if state == "used":
                c.ellipse((76, 94, 86, 104), A[17]); c.ellipse((78, 95, 84, 101), A[18])
        fr.append(c.im)
    m = {
        "id": "event_cache", "event": "E7 밀주 저장고(임시) · 숨은 노드 '밀주 저장고 보물방'",
        "usage": "E7: 1-6 숨은 벽(cellar_wall)을 부수면 나오는 저장고 궤짝 / 숨은 노드 보물방(전투 없음). 열면 독주·소모품·전표(시스템)",
        "footprint": [2, 1], "solid": True, "depth": "y", "pivot": {"x": piv[0], "y": piv[1]}, "occludeAbove": 36,
        "states": {"idle": [0], "open": [1], "used": [2]}, "interact": "E",
        "stateNote": "idle = 짚·자루로 덮고 밀랍 봉인(표지) · open = 연 순간~보상 줍기 전(병 반짝임) · used = 빔",
        "emissiveColors": EMISSIVE_HEX, "floor": "stage1", "paletteSwap": False,
    }
    write_sheet("structures", "event_cache", fr, W, H, m, durations=[100, 100, 100])
    return fr, piv


def event_offering_cup():
    W, H, piv = 112, 128, (56, 120)
    fr = []
    seq = [("idle", 0)] + [("pray", k) for k in range(4)] + [("used", 0)]
    for st, k in seq:
        c = Canvas(W, H)
        contact(c, 58, 119, 40, 7)
        # 낮은 돌 판(제단)
        m_, d = mask(W, H)
        d.polygon([(18, 104), (94, 104), (98, 118), (14, 118)], fill=255)
        shade_mask(c, m_, R_STONE, base=0.5, gain=0.7, soft=2, tilt=0.3)
        for x in range(18, 95):
            c.px(x, 104, SL[6]); c.px(x, 105, SL[5])
        # 술잔(작은 백랍 잔)
        goblet(c, 50, 103, h=22, full=(st != "used"), glow=False)
        # 짧은 초
        cx_ = 76
        c.rect(cx_ - 3, 90, cx_ + 3, 103, PL[4]); c.vline(cx_ - 3, 90, 103, G[13]); c.vline(cx_ + 3, 90, 103, PL[2])
        c.px(cx_ - 1, 90, PL[2]); c.px(cx_ + 1, 91, PL[3])
        if st != "used":
            flame(c, cx_, 89, 6, 12 + (k % 2), seed=30 + k, tongues=2, core=False)
            mark(c, 50, 103 - 22 - 1, st == "idle")
        else:
            c.vline(cx_, 86, 89, SL[3]); c.px(cx_ + 1, 84, PL[1])
        if st == "pray":
            # 기도 중: 잔에서 올라오는 넋의 김(자체 발광, 위로 흩어짐)
            r = Rand(70 + k)
            for j in range(14):
                yy = 76 - j * 4 - k * 2
                xx = 50 + int(6 * math.sin(j * 0.7 + k)) + r.i(-1, 1)
                col = A[26] if j < 4 else (A[25] if j < 9 else A[23])
                if yy > 2:
                    c.px(xx, yy, col)
                    if j % 3 == 0:
                        c.px(xx + 1, yy, A[24])
        fr.append(c.im)
    st, lp = states_json([("idle", 1, False), ("pray", 4, True), ("used", 1, False)])
    m = {
        "id": "event_offering_cup", "event": "E8 무명 전사의 술잔(임시)",
        "usage": "E8 — C3 묘(grave) 바로 앞(남쪽 1칸)에 둔다. E 2초 기도(hold) 동안 pray 루프, 끝나면 메뉴 → used",
        "footprint": [1, 1], "solid": False, "depth": "y", "pivot": {"x": piv[0], "y": piv[1]}, "occludeAbove": 20,
        "states": st, "stateLoop": lp, "interact": "E(hold 2000ms)",
        "light": L("#eecc78", 110, 0.6, 76, 82, 0.2, 7),
        "lightByState": {"idle": "켜짐", "pray": "켜짐(intensity ×1.4 권장)", "used": None},
        "emissiveColors": EMISSIVE_HEX, "floor": "stage1", "paletteSwap": False,
    }
    write_sheet("structures", "event_offering_cup", fr, W, H, m, durations=[100, 140, 140, 140, 140, 100])
    return fr, piv


def ledger_book(c, cx, cy, crossed=False, seal=True):
    """바닥에 펼쳐진 장부(3/4) — 두 쪽 + 가죽 표지."""
    # 표지(바닥 위 그림자 쪽)
    c.poly([(cx - 34, cy - 10), (cx + 34, cy - 14), (cx + 38, cy + 12), (cx - 30, cy + 16)], WD[1])
    # 두 쪽(종이)
    for (pts, base) in (([(cx - 31, cy - 10), (cx, cy - 12), (cx + 1, cy + 11), (cx - 28, cy + 13)], 0.75),
                        ([(cx + 1, cy - 12), (cx + 32, cy - 13), (cx + 35, cy + 9), (cx + 2, cy + 11)], 0.62)):
        m_ = poly_mask(c.w, c.h, pts)
        shade_mask(c, m_, R_BONE, base=base, gain=0.4, soft=1, rim=False)
    c.line(cx, cy - 12, cx + 1, cy + 11, PL[1])
    # 글줄(먹)
    for j in range(5):
        y = cy - 7 + j * 4
        c.hline(cx - 26 + j // 3, cx - 5, y, PL[1] if j % 2 else SL[3])
        c.hline(cx + 6, cx + 28 - j // 2, y - 1, PL[1] if j % 2 else SL[3])
    if crossed:
        for t in range(0, 30):
            x, y = cx - 26 + t * 2, cy - 8 + t * 0.6
            c.px(round(x), round(y), A[19]); c.px(round(x) + 1, round(y), A[18])
    if seal:
        c.ellipse((cx + 24, cy + 6, cx + 32, cy + 13), A[19]); c.ellipse((cx + 25, cy + 7, cx + 31, cy + 11), A[21])
        mark(c, cx + 28, cy + 8, True)
    # 흩어진 쪽 2장
    c.poly([(cx - 52, cy + 8), (cx - 38, cy + 5), (cx - 36, cy + 14), (cx - 50, cy + 17)], PL[3])
    c.line(cx - 48, cy + 10, cx - 40, cy + 9, PL[1])
    c.poly([(cx + 42, cy - 18), (cx + 56, cy - 16), (cx + 54, cy - 8), (cx + 41, cy - 10)], PL[2])


def event_dropped_ledger():
    W, H, piv = 144, 80, (72, 64)
    fr = []
    for st in ("idle", "crossed", "burnt"):
        c = Canvas(W, H)
        if st == "burnt":
            r = Rand(9)
            stoneR = [SL[0], SL[1], SL[2], PL[0], PL[1]]
            splash(c, 72, 52, 34, 10, ramp=stoneR, seed=3, glint=False, blobs=6)
            for k in range(26):
                x, y = 72 + r.i(-28, 28), 50 + r.i(-6, 8)
                c.px(x, y, A[23] if k % 4 == 0 else (A[19] if k % 2 else SL[0]))
            for k in range(5):  # 탄 종이 조각 테두리
                x, y = 72 + r.i(-24, 24), 48 + r.i(-6, 6)
                c.hline(x, x + 4, y, A[20]); c.hline(x, x + 4, y + 1, SL[1])
        else:
            ledger_book(c, 72, 50, crossed=(st == "crossed"), seal=(st == "idle"))
        fr.append(c.im)
    m = {
        "id": "event_dropped_ledger", "event": "E9 떨어진 외상 장부(임시)",
        "usage": "E9 — 바닥에 떨어진 장부(1-3 장부대 소품의 떨어진 판). 돌려줌 = 시스템이 지움 / 긋는다 = crossed / 태운다 = burnt",
        "footprint": [1, 1], "solid": False, "depth": "floor", "pivot": {"x": piv[0], "y": piv[1]},
        "states": {"idle": [0], "crossed": [1], "burnt": [2]}, "interact": "E",
        "light": None, "lightByState": {"burnt": "선택: 잔불 약한 빛 #e2a33c 반경 60 도트 1.5초"},
        "emissiveColors": EMISSIVE_HEX, "floor": "stage1", "paletteSwap": False,
    }
    write_sheet("structures", "event_dropped_ledger", fr, W, H, m, durations=[100, 100, 100])
    return fr, piv


# ====================================================================== 숨은 노드 단서
def drain_base(c, cx, cy):
    """판석에 박힌 쇠 배수 격자(바닥 데칼)."""
    m_, d = mask(c.w, c.h)
    d.polygon([(cx - 34, cy - 14), (cx + 30, cy - 16), (cx + 36, cy + 14), (cx - 30, cy + 16)], fill=255)
    shade_mask(c, m_, R_STONE, base=0.45, gain=0.6, soft=2, tilt=0.2)
    gx0, gx1, gy0, gy1 = cx - 22, cx + 24, cy - 8, cy + 9
    c.rect(gx0, gy0, gx1, gy1, SL[0])
    for x in range(gx0 + 2, gx1, 5):
        c.line(x, gy0 + 1, x + 1, gy1 - 1, G[4]); c.line(x + 1, gy0 + 1, x + 2, gy1 - 1, G[2])
    c.hline(gx0, gx1, gy0, G[6]); c.hline(gx0, gx1, gy1, G[2]); c.vline(gx0, gy0, gy1, G[5]); c.vline(gx1, gy0, gy1, G[2])
    # 격자 틈 속 술빛(아주 어둡게) + 가장자리 술 얼룩
    for x in range(gx0 + 4, gx1 - 1, 5):
        c.px(x, (gy0 + gy1) // 2, A[18]); c.px(x, (gy0 + gy1) // 2 + 1, A[17])
    for (x, y) in ((cx + 26, cy + 10), (cx + 30, cy + 12), (cx - 26, cy + 11)):
        c.px(x, y, A[18]); c.px(x + 1, y, A[17])


def clue_drain():
    W, H, piv = 128, 128, (64, 112)
    fr = []
    for k in range(6):
        c = Canvas(W, H)
        drain_base(c, 64, 96)
        # 술 냄새 김: 격자에서 올라와 흔들리며 흩어짐 — 따뜻한 회색 줄 + 호박 점(비발광)
        for strand in range(3):
            x0 = 50 + strand * 13
            for j in range(34):
                y = 90 - j * 2 - ((k * 2 + strand * 3) % 4)
                x = x0 + int(round((2 + j * 0.12) * math.sin(j * 0.28 + k * 1.05 + strand * 2)))
                fade = j / 34
                if (j + k) % 9 == 0 or (fade > 0.6 and (x + y) % 2):
                    continue
                col = PL[3] if fade < 0.3 else (PL[2] if fade < 0.65 else PL[1])
                if j % 7 == 3:
                    col = A[21]
                c.px(x, y, col)
                if fade < 0.45:
                    c.px(x + 1, y, PL[1])
        fr.append(c.im)
    c = Canvas(W, H)
    drain_base(c, 64, 96)
    # 조사됨: 격자 위 긁힌 화살표(호박, 자체 발광) — '숨은 길' 방향 표시
    for t in range(0, 22):
        c.px(46 + t, 96 - t // 4, A[25]); c.px(46 + t, 97 - t // 4, A[22])
    c.line(67, 91, 61, 87, A[25]); c.line(67, 91, 61, 95, A[25])
    fr.append(c.im)
    st, lp = states_json([("idle", 6, True), ("found", 1, False)])
    m = {
        "id": "clue_drain", "clue": "숨은 노드 단서 — 술 냄새 나는 배수구(임시)",
        "usage": "2차 묶음 (d) 숨은 노드 A안: 갈라지는 노드 전투장에 단서 1개. 전투 끝난 뒤 E 로 조사 → found(지도에 숨은 길)",
        "footprint": [1, 1], "solid": False, "depth": "floor", "pivot": {"x": piv[0], "y": piv[1]},
        "states": st, "stateLoop": lp, "interact": "E(전투 후)",
        "stateNote": "idle 김 루프는 비발광(조명 받아야 보임 — 횃불·등 가까이에 두면 발견 쉬움). found 화살표만 자체 발광",
        "emissiveColors": EMISSIVE_HEX, "floor": "stage1", "paletteSwap": False,
    }
    write_sheet("structures", "clue_drain", fr, W, H, m, durations=[160] * 6 + [100])
    return fr, piv


def jar(c, cx, by, rx=34, h=92, seed=7):
    """옹기 술독(어깨 넓고 입 좁은 독)."""
    contact(c, cx + 3, by - 1, rx + 6, 8)
    m_, d = mask(c.w, c.h)
    top = by - h
    KEYS = [(0, 0.44), (0.07, 0.56), (0.3, 0.95), (0.45, 1.0), (0.75, 0.84), (1.0, 0.62)]

    def prof(t):
        for (t0, a), (t1, b) in zip(KEYS, KEYS[1:]):
            if t <= t1:
                u = (t - t0) / (t1 - t0)
                u = u * u * (3 - 2 * u)
                return a + (b - a) * u
        return KEYS[-1][1]
    pts = []
    for i in range(41):
        t = i / 40
        pts.append((cx - rx * prof(t), top + t * h))
    pts2 = [(2 * cx - x, y) for (x, y) in reversed(pts)]
    d.polygon(pts + pts2, fill=255)
    d.ellipse((cx - rx * 0.62, by - 10, cx + rx * 0.62, by + 2), fill=255)
    shade_mask(c, m_, R_CLAY, base=0.5, gain=0.95, soft=7, tilt=0.1)
    # 입(타원 테)
    for x in range(int(cx - rx * 0.44), int(cx + rx * 0.44) + 1):
        u = (x - cx) / (rx * 0.44)
        yy = int(round(5 * math.sqrt(max(0, 1 - u * u))))
        c.px(x, top - yy, PL[3]); c.px(x, top + yy, R_CLAY[2])
        for y in range(top - yy + 1, top + yy):
            c.px(x, y, SL[0])
    # 유약 흘림 띠
    for x in range(cx - rx + 4, cx + rx - 3):
        y = top + 26 + int(3 * math.sin(x * 0.4))
        if c.get(x, y) in R_CLAY:
            c.px(x, y, R_CLAY[1]); c.px(x, y + 1, R_CLAY[3])


def clue_cracked_cask():
    W, H, piv = 128, 160, (64, 152)
    crack = [(70, 76), (66, 86), (71, 95), (64, 104), (69, 114), (65, 124), (68, 133)]
    fr = []
    for k in range(7):
        found = k == 6
        c = Canvas(W, H)
        jar(c, 64, 152, rx=40, h=96)
        for (a, b) in zip(crack, crack[1:]):
            c.line(a[0], a[1], b[0], b[1], SL[0])
            c.line(a[0] + 1, a[1], b[0] + 1, b[1], A[25] if found else A[18])
        for (x, y) in ((66, 86), (64, 104)):      # 곁가지 금
            c.line(x, y, x - 6, y + 4, SL[0])
        # 스며 흐르는 술 줄 + 바닥 웅덩이
        sx = 68
        for y in range(134, 150):
            c.px(sx, y, A[19] if not found else A[22]); c.px(sx + 1, y, A[18])
        splash(c, 76, 152, 14 + (k % 6) // 3, 3, seed=12, blobs=3)
        if not found:
            dy = 136 + (k * 3) % 16
            c.px(sx + 1, dy, A[22]); c.px(sx + 1, dy + 1, A[20])
        else:
            mark(c, 70, 72, True)
        fr.append(c.im)
    st, lp = states_json([("idle", 6, True), ("found", 1, False)])
    m = {
        "id": "clue_cracked_cask", "clue": "숨은 노드 단서 — 금 간 술독(임시)",
        "usage": "2차 묶음 (d) 숨은 노드 단서 2번(설계 d.1 '금 간 술독 벽'). 전투장 벽 가까이에 둔다. E 조사 → found(금이 빛남)",
        "footprint": [1, 1], "solid": True, "depth": "y", "pivot": {"x": piv[0], "y": piv[1]}, "occludeAbove": 40,
        "states": st, "stateLoop": lp, "interact": "E(전투 후)",
        "stateNote": "부서지지 않는다(타격 무시 제안) — 조사형. idle = 금에서 술이 스며 똑똑 떨어짐, found = 금이 호박빛",
        "light": None, "lightByState": {"found": L("#e2a33c", 70, 0.5, 68, 104, 0.05, 2)},
        "emissiveColors": EMISSIVE_HEX, "floor": "stage1", "paletteSwap": False,
    }
    write_sheet("structures", "clue_cracked_cask", fr, W, H, m, durations=[180] * 6 + [100])
    return fr, piv


ALL = [challenge_banner, still, event_last_cup, event_tasting_tray, event_peddler_mat, event_cache,
       event_offering_cup, event_dropped_ledger, clue_drain, clue_cracked_cask]
