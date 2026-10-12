"""원경 — 하늘·구름·달·먼 성벽 도시 '잔'(불투명). 논리 640×360."""
import math
import random

from PIL import Image, ImageDraw

from kit import A, G, W, H, Fbm, Noise, band, poly, mask_new, edges

HORIZON = 232
CITY_CX = 300          # 성문 가운데
GLOW = (300, 200, 230, 80)   # 도시 불빛이 연기·구름에 비친 자리 cx, cy, rx, ry
MOON = (491, 150, 31)


def glow_at(x, y):
    cx, cy, rx, ry = GLOW
    d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
    return math.exp(-d * 1.25)


def moon_halo(x, y):
    mx, my, r = MOON
    d = math.hypot(x - mx, (y - my) * 1.08) - r
    return math.exp(-max(d, 0) / 16.0) if d > 0 else 1.0


# 명도 단(L*)이 같은 무채 · 호박 쌍 — 하늘이 도시 쪽으로 '데워질' 때 밝기 점프 없이 색만 바뀐다
GRAYL = [G[1], G[2], G[3], G[4], G[5], G[6], G[7], G[8], G[9], G[10]]
WARML = [A[0], A[0], A[1], A[1], A[2], A[3], A[3], A[4], A[5], A[6]]


def sky_and_clouds(im):
    px = im.load()
    stroke = Fbm(11, 3, 14, 4)
    fine = Noise(12, 160, 90)
    cf = Fbm(21, 7, 9, 5)
    env = Fbm(22, 5, 1, 3)
    strata = [(84, 15), (150, 13), (194, 12)]
    lv, warm, cl = {}, {}, set()
    for y in range(HORIZON + 4):
        for x in range(W):
            t = y / HORIZON
            g = glow_at(x, y)
            m = moon_halo(x, y)
            j = (stroke.at(x / W, y / H) - 0.5) * 0.9 + (fine.at(x / W, y / H) - 0.5) * 0.35
            v = 0.3 + 2.6 * t ** 1.7 + 4.4 * g + 3.2 * m
            lv[x, y] = v + j * 1.1
            warm[x, y] = g + j * 0.28 > 0.2
            e = 0.0
            for k, (cy, hh) in enumerate(strata):
                cyx = cy + (env.at(x / W, 0.2 + k * 0.3) - 0.5) * 40
                e = max(e, math.exp(-((y - cyx) / hh) ** 2))
            if x < 300 and y < 125:
                e *= 0.3
            if cf.at(x / W, y / H) * 0.9 + e * 0.55 - 0.42 > 0.12 and 18 < y < HORIZON - 6:
                cl.add((x, y))
    for (x, y) in cl:
        g = glow_at(x, y)
        mo = moon_halo(x, y)
        below = sum(1 for k in range(1, 4) if (x, y + k) not in cl)
        above = sum(1 for k in range(1, 3) if (x, y - k) not in cl)
        v = lv[x, y] - 1.0
        brk = fine.at(x / W * 0.5, y / H) > 0.42          # 아랫변 빛을 군데군데 끊는다
        if below and g > 0.14 and brk:
            v = lv[x, y] + 0.4 + g * 2.6 + (0.9 if below >= 2 else 0)
            warm[x, y] = True
        elif above and mo > 0.12:
            v = lv[x, y] + (1.6 if above == 2 else 0.8) + mo * 2.5
            warm[x, y] = False
        elif above == 2:
            v = lv[x, y] + 0.6
        lv[x, y] = v
    for (x, y), v in lv.items():
        i = max(0, min(9, int(round(v))))
        px[x, y] = (WARML if warm[x, y] else GRAYL)[i]


def stars(im):
    r = random.Random(7)
    px = im.load()
    for _ in range(90):
        x, y = r.randrange(W), r.randrange(4, 150)
        if glow_at(x, y) > 0.08 or moon_halo(x, y) > 0.12:
            continue
        if px[x, y] not in (G[1], G[2]):
            continue
        px[x, y] = r.choice([G[6], G[7], G[8], G[10]])


def moon(im):
    mx, my, r = MOON
    px = im.load()
    n = Fbm(31, 5, 5, 3)
    for y in range(my - r - 1, my + r + 2):
        for x in range(mx - r - 1, mx + r + 2):
            d = math.hypot(x - mx, y - my)
            if d > r + 0.3:
                continue
            u, v = (x - mx) / r, (y - my) / r
            lit = 0.75 - 0.25 * (u * 0.6 + v * 0.8)          # 오른쪽 아래가 살짝 어둡다
            mare = n.at((u + 1) / 2, (v + 1) / 2)
            if mare > 0.58:
                lit -= 0.22
            elif mare > 0.52:
                lit -= 0.1
            if d > r - 1.2:
                c = G[12]
            else:
                c = band([G[10], G[11], G[12], G[13], G[14]], max(0, min(1, lit)), 0)
            px[x, y] = c


def hills(im):
    """지평선 뒤 낮은 먼 산등성(성벽보다 연하게)."""
    d = ImageDraw.Draw(im)
    n = Fbm(41, 6, 1, 3)
    for x in range(W):
        h = 10 + 16 * n.at(x / W, 0.3) - 6 * math.exp(-((x - CITY_CX) / 120) ** 2)
        y0 = HORIZON - int(h)
        c = G[3] if glow_at(x, y0) < 0.35 else A[1]
        d.line([(x, y0), (x, HORIZON)], fill=c)
        if glow_at(x, y0) > 0.25:
            im.putpixel((x, y0), A[2])


def wall_h(x):
    """성벽 높이(성문에서 멀어질수록 낮아져 지평선으로)."""
    return 24 - abs(x - CITY_CX) * 0.042


def city(im):
    """성벽(가로로 길게) + 탑 + 성 안 지붕·굴뚝·가운데 성채 + 열린 성문의 호박빛."""
    r = random.Random(5)
    px = im.load()
    sil = mask_new()
    sd = ImageDraw.Draw(sil)
    base = HORIZON - 18
    # 성 안 지붕들 — 가운데가 높고 양옆으로 낮아짐(두 줄: 뒷줄은 더 높고 연함)
    back = mask_new()
    bd = ImageDraw.Draw(back)
    for row, (dst, amp, x0, x1) in enumerate([(bd, 30, 176, 430), (sd, 20, 160, 444)]):
        x = x0
        while x < x1:
            bw = r.randint(7, 13)
            hgt = int(10 + amp * math.exp(-((x - 312) / 80) ** 2) + r.randint(-3, 4))
            top = base - hgt
            kind = r.choice(["gable", "gable", "gable", "flat", "tower"])
            if kind == "gable":
                poly(dst, [(x, base + 4), (x, top + 4), (x + bw / 2, top - 3), (x + bw, top + 4), (x + bw, base + 4)], 255)
            elif kind == "tower":
                poly(dst, [(x + 2, base), (x + 2, top), (x + bw / 2, top - 9), (x + bw - 2, top), (x + bw - 2, base)], 255)
            else:
                dst.rectangle([x, top + 2, x + bw, base + 4], fill=255)
            x += bw - r.randint(1, 3)
    # 가운데 성채(연회장): 높은 탑 + 깃대
    kx = 336
    for dst in (bd,):
        dst.rectangle([kx - 11, 160, kx + 11, base], fill=255)
        for cx in range(kx - 11, kx + 12, 4):
            dst.rectangle([cx, 156, cx + 1, 160], fill=255)
        dst.rectangle([kx - 5, 134, kx + 5, 160], fill=255)
        poly(dst, [(kx - 7, 136), (kx, 116), (kx + 7, 136)], 255)
        dst.line([(kx, 116), (kx, 104)], fill=255)
    stacks = [(258, 168), (284, 160), (378, 170)]
    for sx, sy in stacks:
        bd.rectangle([sx - 1, sy, sx + 2, base], fill=255)
    # 성벽
    for x in range(0, W):
        hgt = wall_h(x)
        if hgt < 3:
            continue
        top = HORIZON - int(hgt)
        sd.line([(x, top), (x, HORIZON + 1)], fill=255)
        if (x // 2) % 2 == 0 and hgt > 8:
            sd.line([(x, top - 2), (x, top - 1)], fill=255)
    towers = []
    tx = CITY_CX - 26 * 15
    while tx < W + 20:
        dist = abs(tx - CITY_CX)
        hgt = wall_h(tx)
        if hgt >= 4 and dist > 20:
            tw = max(3, int(9 - dist * 0.014))
            th = int(hgt + 8 - dist * 0.008)
            sd.rectangle([tx - tw // 2, HORIZON - th, tx + tw // 2, HORIZON], fill=255)
            for cx in range(tx - tw // 2 - 1, tx + tw // 2 + 2, 2):
                sd.line([(cx, HORIZON - th - 2), (cx, HORIZON - th)], fill=255)
            towers.append((tx, HORIZON - th))
        tx += 26 if dist < 140 else 34
    for gx in (CITY_CX - 16, CITY_CX + 16):
        sd.rectangle([gx - 6, HORIZON - 36, gx + 6, HORIZON], fill=255)
        poly(sd, [(gx - 8, HORIZON - 35), (gx, HORIZON - 48), (gx + 8, HORIZON - 35)], 255)
    # 칠하기: 뒷줄(연함) → 앞줄 · 성벽(어두움)
    bp, sp = back.load(), sil.load()
    for y in range(90, HORIZON + 2):
        for x in range(W):
            if sp[x, y] > 127:
                dist = abs(x - CITY_CX)
                if dist > 230:                      # 멀리 갈수록 안개에 묻힌다
                    px[x, y] = G[3] if (dist > 280 or (x + y) % 2) else G[2]
                elif dist > 170:
                    px[x, y] = G[2]
                else:
                    px[x, y] = G[1] if y > HORIZON - 14 else G[2]
            elif bp[x, y] > 127:
                g = glow_at(x, y)
                px[x, y] = A[0] if g > 0.55 else G[2]
    for msk, lit_hi, lit_lo in ((back, A[5], A[4]), (sil, A[4], A[3])):
        e = edges(msk)
        mp = msk.load()
        for (x, y) in e["t"]:
            if msk is back and sp[x, y] > 127:
                continue
            g = glow_at(x, y)
            px[x, y] = lit_hi if g > 0.72 else (lit_lo if g > 0.35 else G[5])
    # 성벽 아래쪽 돌 줄(가로 결) — 아주 옅게
    for y in range(HORIZON - 14, HORIZON, 4):
        for x in range(0, W):
            if sp[x, y] > 127 and (x * 7 + y) % 11 < 6 and abs(x - CITY_CX) <= 230:
                px[x, y] = G[2]
    # 창 불빛
    for _ in range(260):
        wx, wy = r.randrange(165, 445), r.randrange(150, base + 2)
        inside = (bp[wx, wy] > 127 and sp[wx, wy] < 128) or (sp[wx, wy] > 127 and wy < HORIZON - 26)
        if inside and (bp[wx, wy - 2] > 127 or sp[wx, wy - 2] > 127):
            px[wx, wy] = r.choice([A[6], A[7], A[8], A[5], A[9]])
            if r.random() < 0.45:
                px[wx, wy + 1] = A[4]
    # 성채 창 줄 + 깃발(잔 문양)
    for yy in (142, 150, 168, 176, 186):
        for xx in range(kx - 8, kx + 9, 5):
            if bp[xx, yy] > 127:
                px[xx, yy] = A[8]
                px[xx, yy + 1] = A[6]
    fx, fy = kx, 104
    for i in range(18):
        for j in range(8):
            yy = fy + j + int(1.4 * math.sin(i * 0.5))
            if j < 8 - i // 6:
                px[fx + 1 + i, yy] = G[2]
    for (dx, dy) in ((6, 2), (7, 2), (8, 2), (9, 2), (10, 2), (7, 3), (8, 3), (9, 3), (8, 4), (8, 5), (7, 6), (8, 6), (9, 6)):
        px[fx + dx, fy + dy + int(1.4 * math.sin(dx * 0.5))] = A[6]
    # 성벽 위 횃불
    for (tx, ty) in towers:
        if 0 <= tx < W:
            px[tx, ty - 3] = A[8] if abs(tx - CITY_CX) < 170 else A[6]
            if ty - 4 >= 0:
                px[tx, ty - 4] = A[5]
    for x in range(10, W - 4, 9):
        hgt = wall_h(x)
        if hgt < 7 or abs(x - CITY_CX) < 24:
            continue
        y = HORIZON - int(hgt) - 3
        if sp[x, y] < 128:
            px[x, y] = A[7] if abs(x - CITY_CX) < 150 else A[5]
    # 성문: 아치 안이 호박빛, 내리닫이 창살(세로 살)이 빛을 가른다
    gx0, gx1, gy0 = CITY_CX - 4, CITY_CX + 4, HORIZON - 12
    for y in range(gy0, HORIZON + 1):
        for x in range(gx0, gx1 + 1):
            dy = y - gy0
            if dy < 3 and abs(x - CITY_CX) > 4 - (3 - dy) * 1.4:
                continue
            c = A[5] if dy < 4 else (A[7] if dy < 8 else A[8])
            if (x - gx0) % 3 == 1 and dy < 9:
                c = A[2]
            if dy == 5:
                c = A[3]
            px[x, y] = c
    return stacks


def smoke(im, stacks):
    """굴뚝 연기: 넓게 퍼져 도시 위 불빛 구름과 섞인다. 아래는 데워진 호박, 위는 식은 무채."""
    px = im.load()
    n = Fbm(51, 6, 10, 4)
    for k, (sx, sy) in enumerate(stacks):
        for y in range(70, sy):
            rise = sy - y
            drift = rise * 0.42 + 5 * math.sin(rise * 0.06 + k * 2)
            wdt = 1.5 + rise * 0.16 + (rise / 60.0) ** 2 * 6
            for x in range(int(sx + drift - wdt - 4), int(sx + drift + wdt + 5)):
                if not (0 <= x < W):
                    continue
                dd = abs(x - (sx + drift)) / wdt
                nn = n.at(x / W + k * 0.13, y / H)
                keep = (1 - dd) * 0.9 + (nn - 0.5) * 1.3 - rise * 0.0055
                if keep < 0.18:
                    continue
                g = glow_at(x, y)
                if rise < 12:
                    c = A[4] if dd < 0.4 else A[3]
                elif g > 0.5:
                    c = A[3] if keep > 0.45 else A[2]
                elif g > 0.22:
                    c = A[2] if keep > 0.4 else A[1]
                else:
                    if keep < 0.4:
                        continue
                    c = G[3]
                px[x, y] = c


def plain(im):
    """지평선 아래 먼 들판(대부분 중경이 덮지만 불투명이어야 한다) — 성문 빛이 길에 비침."""
    px = im.load()
    f = Fbm(61, 8, 4, 3)
    for y in range(HORIZON + 1, H):
        for x in range(W):
            t = (y - HORIZON) / (H - HORIZON)
            j = (f.at(x / W, y / H) - 0.5) * 0.8
            px[x, y] = band([G[3], G[2], G[1]], min(1, t * 1.6), j)
            if abs(x - CITY_CX) < 5 + (y - HORIZON) * 0.6 and y < HORIZON + 10:
                px[x, y] = A[4] if y < HORIZON + 4 else A[2]


def draw_far():
    im = Image.new("RGB", (W, H), G[1])
    sky_and_clouds(im)
    stars(im)
    moon(im)
    hills(im)
    stacks = city(im)
    smoke(im, stacks)
    plain(im)
    return im
