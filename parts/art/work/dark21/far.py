"""원경(P21 다크) — 연기에 덮인 밤하늘·흐린 달·검은 실루엣 도시 '잔'·작고 검붉은 먼 불길(불투명). 논리 640×360.

62 판과 같은 구도(지평선·성문·달 자리)를 지키고 빛만 바꿨다: 도시를 감싸던 호박 빛무리 → 불길 세 군데의 작은 검붉은 번짐,
창 불빛·성벽 횃불 → 거의 꺼짐, 별 → 연기에 가려 몇 개만, 달 → 연기 띠가 가로지르는 흐린 회색.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from kit import A, B, G, W, H, Fbm, Noise, band, poly, mask_new, edges

HORIZON = 232
CITY_CX = 300          # 성문 가운데
MOON = (491, 150, 31)
FIRES = [(236, 206, 1.0), (352, 200, 0.8), (418, 212, 0.55)]    # 먼 불길 x, y, 세기(작게)


def glow_at(x, y):
    """먼 불길이 연기 밑면에 비친 세기(0..1) — 작고 국소적."""
    g = 0.0
    for fx, fy, s in FIRES:
        d = ((x - fx) / 34) ** 2 + ((y - fy) / 16) ** 2
        g = max(g, s * math.exp(-d * 1.6))
    return g


def moon_halo(x, y):
    mx, my, r = MOON
    d = math.hypot(x - mx, (y - my) * 1.08) - r
    return math.exp(-max(d, 0) / 11.0) if d > 0 else 1.0


GRAYL = [G[0], G[1], G[1], G[2], G[2], G[3], G[3], G[4], G[5], G[6]]
WARML = [G[1], B[0], B[1], B[1], B[2], B[2], B[3], B[3], B[4], B[4]]


def sky_and_clouds(im):
    px = im.load()
    stroke = Fbm(11, 3, 14, 4)
    fine = Noise(12, 160, 90)
    cf = Fbm(21, 7, 9, 5)
    env = Fbm(22, 5, 1, 3)
    strata = [(70, 18), (140, 16), (196, 12)]
    lv, warm, cl = {}, {}, set()
    for y in range(HORIZON + 4):
        for x in range(W):
            t = y / HORIZON
            g = glow_at(x, y)
            m = moon_halo(x, y)
            j = (stroke.at(x / W, y / H) - 0.5) * 0.9 + (fine.at(x / W, y / H) - 0.5) * 0.15
            v = 1.4 + 3.6 * t ** 1.6 + 3.0 * g + 2.2 * m
            lv[x, y] = v + j * 1.0
            warm[x, y] = g + j * 0.15 > 0.28
            e = 0.0
            for k, (cy, hh) in enumerate(strata):
                cyx = cy + (env.at(x / W, 0.2 + k * 0.3) - 0.5) * 40
                e = max(e, math.exp(-((y - cyx) / hh) ** 2))
            if cf.at(x / W, y / H) * 0.9 + e * 0.6 - 0.40 > 0.10 and 6 < y < HORIZON - 4:
                cl.add((x, y))
    for (x, y) in cl:
        g = glow_at(x, y)
        mo = moon_halo(x, y)
        below = sum(1 for k in range(1, 4) if (x, y + k) not in cl)
        above = sum(1 for k in range(1, 3) if (x, y - k) not in cl)
        v = lv[x, y] - 1.6                                   # 연기 구름은 하늘보다 검다
        brk = fine.at(x / W * 0.5, y / H) > 0.5
        if below and g > 0.25 and brk:
            v = lv[x, y] + g * 2.0
            warm[x, y] = True
        elif above and mo > 0.18:
            v = lv[x, y] + (1.0 if above == 2 else 0.4) + mo * 1.6
            warm[x, y] = False
        lv[x, y] = v
    for (x, y), v in lv.items():
        i = max(0, min(9, int(round(v))))
        px[x, y] = (WARML if warm[x, y] else GRAYL)[i]


def stars(im):
    """연기 틈의 별 몇 개."""
    r = random.Random(7)
    px = im.load()
    for _ in range(40):
        x, y = r.randrange(W), r.randrange(4, 110)
        if moon_halo(x, y) > 0.08 or px[x, y] not in (G[1],):
            continue
        px[x, y] = r.choice([G[4], G[5], G[6]])


def moon(im):
    """흐린 달 — 밝기를 두 단 내리고 연기 띠 두 줄이 가로지른다."""
    mx, my, r = MOON
    px = im.load()
    n = Fbm(31, 5, 5, 3)
    veil = Fbm(32, 3, 9, 3)
    for y in range(my - r - 1, my + r + 2):
        for x in range(mx - r - 1, mx + r + 2):
            d = math.hypot(x - mx, y - my)
            if d > r + 0.3:
                continue
            u, v = (x - mx) / r, (y - my) / r
            lit = 0.7 - 0.3 * (u * 0.6 + v * 0.8)
            mare = n.at((u + 1) / 2, (v + 1) / 2)
            if mare > 0.58:
                lit -= 0.25
            elif mare > 0.52:
                lit -= 0.12
            # 연기 띠(달 앞을 지나는 검은 연기)
            vb = veil.at(x / W * 3, y / H * 2)
            band_y = min(abs(y - (my - 9 + (x - mx) * 0.25)), abs(y - (my + 13 - (x - mx) * 0.15)))
            if band_y + (vb - 0.5) * 8 < 3.2:
                lit -= 0.55
            elif band_y + (vb - 0.5) * 8 < 5.5:
                lit -= 0.28
            if d > r - 1.2:
                c = G[7] if lit > 0.2 else G[4]
            else:
                c = band([G[3], G[4], G[5], G[6], G[7], G[8], G[9]], max(0, min(1, lit)), 0)
            px[x, y] = c


def hills(im):
    d = ImageDraw.Draw(im)
    n = Fbm(41, 6, 1, 3)
    for x in range(W):
        h = 10 + 16 * n.at(x / W, 0.3) - 6 * math.exp(-((x - CITY_CX) / 120) ** 2)
        y0 = HORIZON - int(h)
        d.line([(x, y0), (x, HORIZON)], fill=G[2])
        im.putpixel((x, y0), G[3] if glow_at(x, y0) < 0.3 else B[2])


def wall_h(x):
    return 24 - abs(x - CITY_CX) * 0.042


def city(im):
    """검은 성벽·지붕 실루엣. 창 불빛은 거의 꺼졌고, 불길 셋이 지붕을 핥는다. 성문 안쪽만 검붉게 남았다."""
    r = random.Random(5)
    px = im.load()
    sil = mask_new()
    sd = ImageDraw.Draw(sil)
    base = HORIZON - 18
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
    kx = 336
    bd.rectangle([kx - 11, 160, kx + 11, base], fill=255)
    for cx in range(kx - 11, kx + 12, 4):
        bd.rectangle([cx, 156, cx + 1, 160], fill=255)
    bd.rectangle([kx - 5, 134, kx + 5, 160], fill=255)
    poly(bd, [(kx - 7, 136), (kx, 116), (kx + 7, 136)], 255)
    bd.line([(kx, 116), (kx, 104)], fill=255)
    # 무너진 지붕: 불길 자리의 지붕 몇 채를 깎아 낸다(이빨 빠진 스카이라인)
    for fx, fy, s in FIRES:
        poly(bd, [(fx - 8, fy - 14), (fx + 9, fy - 12), (fx + 5, fy - 4), (fx - 5, fy - 6)], 0)
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
    bp, sp = back.load(), sil.load()
    for y in range(90, HORIZON + 2):
        for x in range(W):
            if sp[x, y] > 127:
                dist = abs(x - CITY_CX)
                px[x, y] = G[1] if (dist > 230 and (x + y) % 2) or (y > HORIZON - 14 and y % 4 == 0 and (x // 6 + y // 4) % 3) else (G[0] if y > HORIZON - 14 else G[1])
            elif bp[x, y] > 127:
                px[x, y] = G[0]
    # 윗변: 달 쪽(오른쪽)만 차가운 회색 한 도트, 불길 곁은 검붉게
    for msk in (back, sil):
        e = edges(msk)
        for (x, y) in e["t"]:
            if msk is back and sp[x, y] > 127:
                continue
            g = glow_at(x, y)
            if g > 0.35:
                px[x, y] = B[3] if g > 0.6 else B[2]
            elif x > 360 and (x * 5 + y) % 7 < 4:
                px[x, y] = G[3]
            else:
                px[x, y] = G[2] if (x + y) % 3 else G[1]
    # 꺼지지 않은 창 몇 개(검붉게 — 사람이 아니라 불이 남은 방)
    for _ in range(140):
        wx, wy = r.randrange(165, 445), r.randrange(150, base + 2)
        inside = (bp[wx, wy] > 127 and sp[wx, wy] < 128) or (sp[wx, wy] > 127 and wy < HORIZON - 26)
        if inside and (bp[wx, wy - 2] > 127 or sp[wx, wy - 2] > 127) and glow_at(wx, wy) > 0.12 and r.random() < 0.5:
            px[wx, wy] = r.choice([B[3], B[4], B[2]])
    # 성채 깃발: 찢겨 늘어진 검은 천(문양 없음)
    fx, fy = kx, 104
    for i in range(14):
        for j in range(9):
            yy = fy + j + i // 3
            if j < 9 - i // 3 and not (i > 8 and j % 3 == 1):
                px[fx + 1 + i, yy] = G[1]
    # 성벽 위 횃불: 다 꺼지고 둘만 남음
    for (tx, ty) in towers:
        if 0 <= tx < W and abs(tx - CITY_CX) in (26 * 3, 26 * 5):
            px[tx, ty - 3] = B[4]
    # 성문: 검은 아치 안쪽에 식은 숯 같은 검붉은 빛, 창살이 가른다(타이틀 → 첫 생 줌 중심 그대로)
    gx0, gx1, gy0 = CITY_CX - 4, CITY_CX + 4, HORIZON - 12
    for y in range(gy0, HORIZON + 1):
        for x in range(gx0, gx1 + 1):
            dy = y - gy0
            if dy < 3 and abs(x - CITY_CX) > 4 - (3 - dy) * 1.4:
                continue
            c = B[1] if dy < 4 else (B[2] if dy < 8 else B[3])
            if (x - gx0) % 3 == 1:
                c = G[0]
            if dy == 5:
                c = G[0]
            px[x, y] = c
    return [(fx_, fy_) for fx_, fy_, _ in FIRES]


def fires(im, spots):
    """먼 불길: 무너진 지붕 위로 작게 솟는 검붉은 불 혀 3~4갈래(심만 한 점 밝게)."""
    px = im.load()
    r = random.Random(57)
    for k, (sx, sy) in enumerate(spots):
        s = FIRES[k][2]
        for t in range(3 + (s > 0.7)):
            ox = r.randint(-5, 5)
            hgt = int((5 + 7 * s) * r.uniform(0.5, 1.0))
            lean = r.uniform(0.2, 0.6)
            for i in range(hgt):
                h = i / hgt
                cx = sx + ox + i * lean * 0.5
                wdt = max(0, int((1 - h) * (1.6 + s)))
                for x in range(int(cx - wdt), int(cx + wdt) + 1):
                    c = B[3] if h > 0.55 else (B[4] if abs(x - cx) >= wdt else B[5])
                    if px[x, sy + 2 - i] in (B[5], A[4]) and c != B[5]:
                        continue
                    px[x, sy + 2 - i] = c
        if s > 0.7:
            px[sx, sy + 1] = A[4]
        for x in range(sx - 7, sx + 8):                      # 불 밑 바닥 띠(타는 들보)
            px[x, sy + 3] = B[3] if (x + k) % 3 else B[4]


def smoke(im, spots):
    """검은 연기 기둥: 불길에서 오른쪽(바람)으로 기울며 넓게 퍼져 하늘을 덮는다. 밑동만 검붉게 데워짐."""
    px = im.load()
    n = Fbm(51, 6, 10, 4)
    for k, (sx, sy) in enumerate(spots):
        sy -= 8
        for y in range(10, sy):
            rise = sy - y
            drift = rise * 0.32 + 6 * math.sin(rise * 0.05 + k * 2)
            wdt = 3.0 + rise * 0.3 + (rise / 50.0) ** 2 * 8
            for x in range(int(sx + drift - wdt - 4), int(sx + drift + wdt + 5)):
                if not (0 <= x < W):
                    continue
                dd = abs(x - (sx + drift)) / wdt
                nn = n.at(x / W + k * 0.13, y / H)
                keep = (1 - dd) * 0.95 + (nn - 0.5) * 1.3 - rise * 0.0035
                if keep < 0.2:
                    continue
                if moon_halo(x, y) > 0.9 and keep < 0.5:
                    continue                                    # 달 원반 위는 moon() 의 연기 띠가 맡는다
                if rise < 8 and dd < 0.6:
                    c = B[1]
                else:
                    c = G[1] if keep > 0.5 or y < 150 else G[2]
                    if 0.2 < keep < 0.3 and moon_halo(x, y) > 0.2:
                        c = G[3]                                # 달빛 받는 연기 가장자리
                px[x, y] = c


def plain(im):
    px = im.load()
    f = Fbm(61, 8, 4, 3)
    for y in range(HORIZON + 1, H):
        for x in range(W):
            t = (y - HORIZON) / (H - HORIZON)
            j = (f.at(x / W, y / H) - 0.5) * 0.8
            px[x, y] = band([G[2], G[1], G[0]], min(1, t * 1.6), j)
            if abs(x - CITY_CX) < 4 + (y - HORIZON) * 0.5 and y < HORIZON + 6:
                px[x, y] = B[1]


def draw_far():
    im = Image.new("RGB", (W, H), G[1])
    sky_and_clouds(im)
    sky = im.crop((0, 0, W, 150)).filter(ImageFilter.ModeFilter(5))      # 구름 가장자리 잡티 정리(팔레트 색 그대로)
    im.paste(sky, (0, 0))
    stars(im)
    moon(im)
    hills(im)
    spots = city(im)
    smoke(im, spots)
    fires(im, spots)
    plain(im)
    return im
