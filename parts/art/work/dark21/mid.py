"""중경(P21 다크) — 62 구도 그대로, 빛만 밤으로: 횃불 꺼진 행렬·길가의 시체·까마귀·꺼진 등롱. 원본 설명: 중경 — 벽 밖 전장 들판(위쪽 투명). 언덕 3겹, 성문에서 왼쪽 밖으로 휘어 나가는 길,
횃불 든 출병 행렬('나간 자 칸만 있고 돌아온 자 칸은 없다'), 꽂힌 창·찢긴 깃발·부서진 수레·마른 나무.
논리 640×360 RGBA."""
import math
import random

from PIL import Image, ImageDraw

from kit import A, B, G, W, H, Fbm, band, poly, stroke_poly
from far import CITY_CX, HORIZON, glow_at

NA = Fbm(71, 6, 1, 4)
NB = Fbm(72, 5, 1, 4)
NC = Fbm(75, 4, 1, 4)


def hill_a(x):
    return 250 + 10 * (NA.at(x / W, 0.5) - 0.5) - 4 * math.exp(-((x - 470) / 60) ** 2)


def hill_b(x):
    return 266 + 0.05 * x + 16 * (NB.at(x / W, 0.5) - 0.5) - 10 * math.exp(-((x - 80) / 90) ** 2)


def hill_c(x):
    return 322 - 0.02 * x + 14 * (NC.at(x / W, 0.5) - 0.5)


# 길: 성문에서 나와 왼쪽 밖으로 (y 가 클수록 가깝다)
ROAD = [(CITY_CX, HORIZON + 1, 2), (292, 242, 4), (262, 256, 8), (214, 270, 13), (150, 286, 19), (70, 302, 25), (-30, 318, 30)]


def road_samples(step=0.5):
    out = []
    for (x0, y0, w0), (x1, y1, w1) in zip(ROAD, ROAD[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) / step)
        for i in range(n):
            t = i / n
            out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, w0 + (w1 - w0) * t))
    return out


def soldier(d, px, x, y, h, torch, step, r):
    """왼쪽으로 걸어가는 병사 실루엣. h = 키(도트)."""
    c = (*G[0], 255)
    x, y = int(round(x)), int(round(y))
    hd = max(1, h // 6)
    # 다리(걸음 교차)
    leg = max(2, h // 3)
    s = 1 if step else -1
    d.line([(x, y - leg), (x - s, y)], fill=c)
    d.line([(x + 1, y - leg), (x + 1 + s, y)], fill=c)
    # 몸통
    poly(d, [(x - 1, y - leg), (x + 2, y - leg), (x + 2, y - h + hd + 1), (x - 1, y - h + hd + 1)], c)
    # 등짐(빚 장부를 지고 나가는 자들 — 큰 짐 보따리)
    if h >= 9:
        d.rectangle([x + 2, y - h + hd + 2, x + 3, y - leg - 1], fill=c)
    # 머리 · 투구 테
    d.rectangle([x - 1, y - h, x - 1 + hd, y - h + hd], fill=c)
    d.point((x - 2, y - h + hd), fill=c)
    # 창(어깨에 메고 뒤로 기움)
    d.line([(x + 1, y - leg - 1), (x + 4 + h // 4, y - h - h // 2)], fill=c)
    if torch:
        tx, ty = x - 2, y - h + hd + 1
        d.line([(tx, ty), (tx - 1, ty - 3)], fill=c)
        fl = [(-1, -4, B[4]), (-1, -5, B[3]), (-2, -4, B[2])]       # 다 타 가는 마지막 횃불
        for ox, oy, col in fl:
            d.point((tx + ox, ty + oy), fill=(*col, 255))


def draw_mid():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = im.load()
    f = Fbm(73, 10, 6, 4)
    fine = Fbm(74, 48, 30, 2)
    for y in range(HORIZON + 1, H):
        for x in range(W):
            j = (f.at(x / W, y / H) - 0.5) * 0.9 + (fine.at(x / W, y / H) - 0.5) * 0.3
            ya, yb, yc = hill_a(x), hill_b(x), hill_c(x)
            gate = math.exp(-((x - CITY_CX) / 22) ** 2) * max(0.0, 1 - (y - HORIZON) / 7)
            if y >= yc:
                t = (y - yc) / 30
                c = band([G[1], G[0], G[0]], min(1, t), j)
            elif y >= yb:
                t = (y - yb) / max(8, yc - yb)
                c = band([G[1], G[1], G[0]], min(1, t), j)
            elif y >= ya:
                t = (y - ya) / max(6, yb - ya)
                c = band([G[2], G[1], G[1]], min(1, t), j)
            else:
                t = (y - HORIZON) / max(4, ya - HORIZON)
                if gate + j * 0.2 > 0.3:
                    c = band([B[1], B[0]], t, j)
                else:
                    c = band([G[3], G[2]], t, j)
            px[x, y] = (*c, 255)
    # 능선 윗변 빛: 언덕 A 만 성문 근처 호박, 나머지는 달빛 회색(군데군데 끊김)
    brk = Fbm(77, 30, 1, 2)
    for x in range(W):
        for fn, cool_c, lim in ((hill_a, G[3], 0.0), (hill_b, G[2], 0.45), (hill_c, G[2], 0.55)):
            y = int(fn(x))
            if not (HORIZON < y < H) or brk.at(x / W, 0.3 + lim) < lim:
                continue
            g = glow_at(x, HORIZON)
            if fn is hill_a and abs(x - CITY_CX) < 14:
                px[x, y] = (*B[2], 255)
            else:
                px[x, y] = (*cool_c, 255)
    # 풀 결(능선 아래 짧은 세로 획)
    r = random.Random(82)
    for _ in range(1400):
        x = r.randrange(W)
        fn = r.choice((hill_a, hill_b, hill_b, hill_c))
        y0 = int(fn(x)) + r.randint(1, 10)
        if y0 >= H:
            continue
        ln = r.randint(1, 3 if fn is hill_a else 5)
        col = px[x, y0]
        for k in range(ln):
            if 0 <= y0 - k < H:
                px[x, y0 - k] = col
        if 0 <= y0 - ln < H and r.random() < 0.5:
            px[x, y0 - ln] = (*G[1], 255)
    # 길
    fine2 = Fbm(76, 60, 40, 2)
    samples = road_samples()
    road = {}
    for (cx, cy, hw) in samples:
        ry = max(1.0, hw * 0.28)
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - hw - 2), int(cx + hw + 3)):
                if not (0 <= x < W and HORIZON < y < H):
                    continue
                dd = math.hypot((x - cx) / hw, (y - cy) / ry)
                j = fine2.at(x / W, y / H) - 0.5
                if dd + j * 0.5 > 1.0:
                    continue
                if (x, y) not in road or road[x, y][0] > dd:
                    road[x, y] = (dd, abs(y - cy) / ry, j)
    for (x, y), (dd, side, j) in road.items():
        t = (y - HORIZON) / 90
        if y < HORIZON + 7:
            c = B[2] if dd < 0.6 else B[1]
        else:
            c = band([B[0], G[2], G[1], G[1]], min(1, t * 0.9 + dd * 0.45), j)    # 젖은 진흙 길
            if 0.3 < side < 0.42 or 0.66 < side < 0.76:
                c = G[0]
        px[x, y] = (*c, 255)
    # 길 위 웅덩이(성문 빛·횃불 반사)
    for _ in range(40):
        cx, cy, hw = samples[r.randrange(len(samples))]
        x = int(cx + r.uniform(-0.5, 0.5) * hw)
        y = int(cy)
        lw = r.randint(2, 3 + int(hw / 5))
        for k in range(lw):
            if 0 <= x + k < W and HORIZON < y < H:
                px[x + k, y] = (*(B[2] if y < 262 else (G[4] if k == 0 else G[3])), 255)   # 웅덩이: 먼 불은 검붉게, 가까이는 흐린 하늘
    d = ImageDraw.Draw(im)
    # 꽂힌 창·찢긴 깃발: 언덕 A(작게) · B(크게)
    groups = [(hill_a, 30, 5, 10), (hill_a, 120, 4, 9), (hill_a, 420, 4, 10), (hill_a, 560, 5, 10), (hill_a, 620, 3, 9),
              (hill_b, 40, 4, 26), (hill_b, 335, 3, 24), (hill_b, 470, 5, 30), (hill_b, 600, 4, 28)]
    for fn, gx, n, size in groups:
        for k in range(n):
            x = gx + r.randint(-18, 18)
            if not (0 <= x < W):
                continue
            base = int(fn(x) + r.randint(1, 4))
            ln = int(size * r.uniform(0.7, 1.25))
            ang = math.radians(r.uniform(-26, 26))
            top = (x + math.sin(ang) * ln, base - math.cos(ang) * ln)
            col = (*G[0], 255) if fn is hill_b else (*G[1], 255)
            d.line([(x, base), (round(top[0]), round(top[1]))], fill=col)
            if size > 20:
                d.line([(x + 1, base), (round(top[0]) + 1, round(top[1]))], fill=col)
                d.point((round(top[0]), round(top[1]) - 1), fill=col)
                d.point((round(top[0]), round(top[1]) - 2), fill=col)
            if r.random() < 0.5:
                fl = int(size * r.uniform(0.35, 0.5))
                fh = max(3, int(size * 0.22))
                tx, ty = top
                pts = [(tx + 1, ty + 1), (tx + fl, ty + 2 + r.randint(-1, 1)), (tx + fl - fl // 3, ty + fh // 2 + 1),
                       (tx + fl - 1, ty + fh + 2), (tx + fl // 2, ty + fh), (tx + 1, ty + fh + 1)]
                poly(d, pts, col)
    # 부서진 수레(언덕 B 왼쪽, 메뉴 뒤쪽이라 어둡게)
    cx = 240
    cy = int(hill_b(cx)) + 3
    c1 = (*G[0], 255)
    poly(d, [(cx - 20, cy - 3), (cx + 10, cy - 13), (cx + 13, cy - 9), (cx - 17, cy + 1)], c1)
    d.line([(cx + 10, cy - 13), (cx + 26, cy - 24)], fill=c1)
    d.line([(cx + 11, cy - 12), (cx + 27, cy - 23)], fill=c1)
    d.ellipse([cx - 8, cy - 15, cx + 6, cy - 1], outline=c1)
    d.ellipse([cx - 7, cy - 14, cx + 5, cy - 2], outline=c1)
    for a in range(0, 180, 45):
        ra = math.radians(a)
        d.line([(cx - 1 - 6 * math.cos(ra), cy - 8 - 6 * math.sin(ra)), (cx - 1 + 6 * math.cos(ra), cy - 8 + 6 * math.sin(ra))], fill=c1)
    # 마른 나무(언덕 B 오른쪽)
    tx, ty = 404, int(hill_b(404)) + 2
    br = [((tx, ty), (tx + 3, ty - 44), 5, 3), ((tx + 3, ty - 44), (tx - 10, ty - 64), 3, 1), ((tx + 3, ty - 44), (tx + 16, ty - 66), 3, 1),
          ((tx + 2, ty - 26), (tx + 20, ty - 36), 2, 1), ((tx - 10, ty - 64), (tx - 18, ty - 72), 1, 1), ((tx + 16, ty - 66), (tx + 13, ty - 78), 1, 1),
          ((tx + 16, ty - 66), (tx + 25, ty - 71), 1, 1), ((tx + 20, ty - 36), (tx + 27, ty - 44), 1, 1), ((tx + 1, ty - 34), (tx - 9, ty - 40), 1, 1)]
    for p0, p1, w0, w1 in br:
        poly(d, stroke_poly(p0, p1, w0, w1), c1)
    d.line([(tx + 20, ty - 36), (tx + 20, ty - 28)], fill=(*G[1], 255))     # 가지에 걸린 투구
    d.ellipse([tx + 18, ty - 28, tx + 22, ty - 24], fill=c1)
    d.point((tx + 19, ty - 27), fill=(*G[4], 255))
    # 출병 행렬 — 성문에서 나와 길을 따라 왼쪽 밖으로(돌아오는 자는 없다)
    k = 0
    for i, (cx, cy, hw) in enumerate(samples):
        if i % 26 != 0 or cy < HORIZON + 6 or cx < 120:
            continue
        h = int(3 + (cy - HORIZON) * 0.24)
        side = 0.3 if k % 2 else -0.25
        sx, sy, torch = cx + side * hw * 0.5, cy + 1 + (k % 2), k == 0
        if torch:
            rr = 3 + h * 0.6
            for yy in range(int(sy - rr * 0.35), int(sy + rr * 0.35) + 1):
                for xx in range(int(sx - rr), int(sx + rr) + 1):
                    if 0 <= xx < W and HORIZON < yy < H and math.hypot((xx - sx) / rr, (yy - sy) / (rr * 0.35)) < 1:
                        cur = px[xx, yy][:3]
                        if cur in G[:4]:
                            px[xx, yy] = (*B[0], 255)
        soldier(d, px, sx, sy, h, torch, k % 2 == 0, r)
        k += 1
    dark_props(im, d, r)
    return im


def crow(d, x, y, s=1, face=1, sheen=G[2]):
    """앉은 까마귀 실루엣(s = 배율, face = 1 오른쪽)."""
    c = (*G[0], 255)
    x, y = round(x), round(y)
    d.ellipse([x - 2 * s, y - 3 * s, x + 2 * s, y], fill=c)                          # 몸
    d.ellipse([x + face * 1 * s - s, y - 5 * s, x + face * 1 * s + s, y - 3 * s], fill=c)   # 머리
    d.line([(x + face * 2 * s, y - 4 * s), (x + face * 3 * s, y - 4 * s)], fill=c)    # 부리
    d.line([(x - face * 2 * s, y - 1), (x - face * 4 * s, y + s)], fill=c)            # 꼬리
    d.point((x - face * s, y - 2 * s), fill=(*sheen, 255))                         # 깃 윤기(달빛)


def corpse(d, x, y, s=1.0, face=1):
    """엎어진 시체 실루엣(가로로 길게) + 밑에 검은 피."""
    c = (*G[0], 255)
    L = 9 * s
    d.ellipse([x - L, y - 2 * s, x + L * 0.4, y + 1], fill=(*B[1], 255))             # 피 웅덩이
    poly(d, [(x - L * 0.7 * face, y - 2.2 * s), (x + L * 0.5 * face, y - 2.6 * s), (x + L * 0.6 * face, y), (x - L * 0.8 * face, y)], c)
    d.ellipse([x + L * 0.5 * face - 1.4 * s, y - 3 * s, x + L * 0.5 * face + 1.4 * s, y], fill=c)   # 머리
    d.line([(x - L * 0.1 * face, y - 2 * s), (x + L * 0.1 * face, y - 5 * s)], fill=c)     # 뻗은 팔


def lantern(d, x, y, s=1, torn=False):
    """꺼진 종이 등롱(줄에 매달림). 불 없음 — 검게 그을린 종이."""
    d.line([(x, y - 4 * s), (x, y)], fill=(*G[1], 255))
    body = [x - 2 * s, y, x + 2 * s, y + 5 * s]
    if torn:
        poly(d, [(x - 2 * s, y + 1), (x + 2 * s, y), (x + 3 * s, y + 4 * s), (x, y + 6 * s), (x - 2 * s, y + 4 * s)], (*G[2], 255))
    else:
        d.ellipse(body, fill=(*G[2], 255))
    d.line([(x - 2 * s, y + 2 * s), (x + 2 * s, y + 2 * s)], fill=(*G[1], 255))
    d.point((x - s, y + s), fill=(*G[3], 255))
    d.line([(x, y + 5 * s), (x, y + 6 * s)], fill=(*G[1], 255))


def dark_props(im, d, r):
    """P21: 길가·들판의 시체, 까마귀, 마른 나무에 매달린 꺼진 등롱."""
    for (x, fn, s, face) in ((96, hill_b, 1.0, 1), (178, hill_b, 0.9, -1), (300, hill_c, 1.4, 1), (352, hill_b, 1.0, 1),
                             (530, hill_b, 1.1, -1), (585, hill_c, 1.4, 1), (60, hill_c, 1.5, -1), (456, hill_a, 0.6, 1),
                             (140, hill_a, 0.6, -1), (226, hill_c, 1.3, -1)):
        corpse(d, x, int(fn(x)) + 4 + int(4 * s), s, face)
    tx, ty = 404, int(hill_b(404)) + 2
    lantern(d, tx - 10, ty - 63, 1)
    lantern(d, tx + 14, ty - 62, 1, torn=True)
    lantern(d, tx + 25, ty - 70, 1)
    for (x, y, s, face) in ((tx + 4, ty - 45, 1, -1), (tx - 17, ty - 72, 1, 1), (tx + 13, ty - 78, 1, 1)):
        crow(d, x, y, s, face)
    for (x, fn, face) in ((470, hill_b, 1), (40, hill_b, -1), (600, hill_b, -1)):     # 창 끝·땅 위의 까마귀
        crow(d, x + r.randint(-6, 6), int(fn(x)) - 1, 1, face)
