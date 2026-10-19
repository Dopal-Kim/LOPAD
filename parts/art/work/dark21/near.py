"""근경(P21 다크) — 62 구도·주인공 형태 그대로. 도시 호박빛 반사 → 달 역광(차가운 회색 테)만, 등 균열은 작게 검붉게, 눈만 밝게.
시체 더미에 피 웅덩이·까마귀, 왼쪽에 피 묻은 연회장 잔해(엎어진 상·깨진 술독·식탁보)와 꺼진 등롱 장대.
원본 설명: 근경 — 시체 더미(탄생지) 위에 선 망령(뒷모습 3/4, 성벽 도시를 바라봄)과 꽂힌 무기 4종, 왼쪽 아래 어두운 풀·창.
논리 640×360 RGBA. 빛: 왼쪽 앞 = 도시 불빛(호박 테), 오른쪽 위 = 달(차가운 회색 테).

주인공 디자인 요소는 게임 도트(P20 hero20/rig20)와 같다: 숯빛 몸 · 숯빛 맨머리(금 없음) · 분노한 눈 하나 · 등 상흔 균열(호박) ·
왼어깨 견갑 + 혼불 · 꽂힌 부러진 화살 · 붕대 감은 팔뚝·정강이 · 찢긴 허리천 · 오른허리 일기장. 타이틀용으로 비율만 길게(7.5두신).
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from kit import A, B, G, W, H, WEAPON, Fbm, band, poly, stroke_poly, mask_new, edges, mix, weapon_ramp

HX, HY, HS = 490, 150, 1.88        # 주인공 원점(머리 꼭대기 가운데) · 단위 → 도트 배율 (키 100 단위 ≈ 188 도트)
FEET_Y = HY + 100 * HS


def P(u, v):
    return (HX + u * HS, HY + v * HS)


def PL(pts):
    return [P(u, v) for u, v in pts]


def limb(d, a, b, w0, w1, fill=255):
    poly(d, stroke_poly(P(*a), P(*b), w0 * HS, w1 * HS), fill)
    r = w1 * HS / 2
    x, y = P(*b)
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


# ------------------------------------------------------------------ 주인공
def hero_parts():
    """부위별 마스크(뒤 → 앞 순서). 8두신 · V자 상체 · 왼다리에 체중(오른 무릎이 살짝 굽음)."""
    parts = {}

    def new():
        m = mask_new()
        return m, ImageDraw.Draw(m)

    # 다리: 허벅지 → 무릎 → 장딴지 불룩 → 발목
    m, d = new()
    limb(d, (-4.4, 46.5), (-5.0, 60), 8.8, 7.8)
    limb(d, (-5.0, 60), (-5.3, 70), 7.8, 5.8)
    limb(d, (-5.3, 70), (-5.9, 77), 5.8, 6.4)
    limb(d, (-5.9, 77), (-6.3, 92), 6.4, 3.8)
    limb(d, (4.6, 46.5), (5.8, 59.5), 8.6, 7.6)
    limb(d, (5.8, 59.5), (6.6, 69.5), 7.6, 5.6)
    limb(d, (6.6, 69.5), (7.6, 76.5), 5.6, 6.2)
    limb(d, (7.6, 76.5), (9.0, 91.2), 6.2, 3.8)
    poly(d, PL([(-10.8, 100), (-10.0, 96.5), (-7.8, 93.0), (-4.6, 92.0), (-3.6, 96), (-3.0, 100)]), 255)
    poly(d, PL([(6.0, 99.6), (6.6, 95.0), (8.0, 91.0), (11.2, 92.6), (13.6, 96.6), (14.0, 99.6)]), 255)
    parts["legs"] = m
    # 오른팔(화면 오른쪽, 달 쪽) — 팔꿈치 살짝 굽음
    m, d = new()
    limb(d, (13.0, 19.5), (14.8, 26.0), 6.6, 6.0)
    limb(d, (14.8, 26.0), (15.8, 33.0), 6.0, 4.6)
    limb(d, (15.8, 33.0), (15.6, 37.5), 4.6, 5.2)
    limb(d, (15.6, 37.5), (14.6, 45.0), 5.2, 3.6)
    poly(d, PL([(12.6, 45.0), (16.4, 44.6), (16.8, 48.6), (15.2, 50.6), (12.8, 49.8), (12.2, 47.0)]), 255)
    parts["armR"] = m
    # 몸통(등) — 승모근 → 어깨 → 광배 → 허리 → 골반
    m, d = new()
    poly(d, PL([(-2.6, 11.6), (-8.8, 14.6), (-13.4, 16.8), (-15.0, 20.4), (-14.2, 25.0), (-11.8, 27.4), (-11.0, 32.0),
                (-9.2, 38.0), (-7.6, 43.0), (-9.0, 48.2), (9.4, 48.2), (8.0, 43.0), (9.6, 38.0), (11.4, 32.0), (12.2, 27.4),
                (14.6, 25.0), (15.4, 20.4), (13.8, 17.0), (9.4, 14.6), (3.0, 11.6)]), 255)
    parts["torso"] = m
    # 허리천(엉덩이 뒤로 길게, 바람에 오른쪽으로 날림)
    m, d = new()
    poly(d, PL([(-8.2, 42.4), (8.4, 42.4), (9.6, 46.6), (13.6, 51.0), (11.2, 51.8), (13.8, 57.2), (9.8, 55.6), (10.2, 61.8),
                (6.4, 57.8), (4.2, 64.2), (1.6, 58.6), (-1.2, 63.4), (-3.0, 58.2), (-5.8, 62.0), (-6.6, 56.6), (-9.6, 58.4),
                (-9.0, 52.0), (-10.0, 50.6), (-9.2, 46.6)]), 255)
    parts["cloth"] = m
    # 왼팔(화면 왼쪽, 도시 쪽) — 몸에서 조금 떨어져 늘어뜨림
    m, d = new()
    limb(d, (-13.0, 19.5), (-15.4, 26.0), 6.8, 6.2)
    limb(d, (-15.4, 26.0), (-16.6, 33.2), 6.2, 4.6)
    limb(d, (-16.6, 33.2), (-16.6, 37.6), 4.6, 5.4)
    limb(d, (-16.6, 37.6), (-16.0, 45.4), 5.4, 3.6)
    poly(d, PL([(-18.0, 45.0), (-14.2, 45.0), (-13.6, 49.2), (-15.0, 51.4), (-17.4, 50.6), (-18.4, 47.6)]), 255)
    parts["armL"] = m
    # 머리: 민머리 두개골(뒤 3/4), 고개를 왼쪽(도시)으로 돌려 눈썹뼈·광대·턱 윤곽이 왼쪽에 걸림
    m, d = new()
    x0, y0 = P(-4.2, 0.2)
    x1, y1 = P(5.2, 12.2)
    d.ellipse([x0, y0, x1, y1], fill=255)
    poly(d, PL([(-3.8, 3.6), (-5.2, 5.2), (-4.6, 6.6), (-5.4, 8.6), (-4.8, 10.4), (-3.6, 12.4), (-1.2, 13.2), (1.0, 12.0), (0.0, 5.0)]), 255)
    poly(d, PL([(-2.8, 11.0), (3.4, 11.0), (3.6, 14.2), (-2.8, 14.2)]), 255)
    parts["head"] = m
    # 왼어깨 견갑(둥근 판 두 겹)
    m, d = new()
    poly(d, PL([(-16.6, 18.6), (-14.6, 15.2), (-10.2, 13.8), (-6.6, 15.0), (-6.6, 18.0), (-9.6, 21.6), (-13.8, 23.8), (-16.4, 23.0)]), 255)
    parts["pauldron"] = m
    # 일기장(오른허리, 허리끈에 매달림)
    m, d = new()
    poly(d, PL([(7.0, 44.6), (12.6, 43.6), (13.6, 52.4), (8.0, 53.4)]), 255)
    parts["diary"] = m
    return parts


ARROWS = [((5.6, 21.0), (12.0, 7.0)), ((9.4, 26.0), (21.0, 16.4)), ((-3.0, 30.0), (-7.4, 19.0)), ((11.6, 22.0), (17.6, 10.0))]


def normals(mask, blur=1.6):
    """마스크 흐림의 기울기 → 바깥 방향 법선(nx, ny) 함수."""
    bl = mask.filter(ImageFilter.GaussianBlur(blur))
    bp = bl.load()
    w, h = mask.size

    def n(x, y):
        gx = bp[min(w - 1, x + 1), y] - bp[max(0, x - 1), y]
        gy = bp[x, min(h - 1, y + 1)] - bp[x, max(0, y - 1)]
        L = math.hypot(gx, gy) or 1
        return -gx / L, -gy / L
    return n


CITY_DIR = (-0.96, -0.28)       # 도시 불빛이 오는 쪽(왼쪽, 약간 위)
MOON_DIR = (0.45, -0.89)        # 달빛(오른쪽 위)


def draw_hero(im, emis, emis_eye):
    """im: RGBA 캔버스 · emis: 발광 마스크(RGBA, 색 = 빛 색)."""
    px = im.load()
    parts = hero_parts()
    order = ["legs", "armR", "torso", "cloth", "armL", "head", "pauldron", "diary"]
    sil = mask_new()
    for k in order:
        sil.paste(255, (0, 0), parts[k])
    tex = Fbm(91, 30, 50, 2)
    owner = {}
    for k in order:
        mp = parts[k].load()
        for y in range(max(0, int(HY) - 4), H):
            for x in range(int(HX - 45), int(HX + 45)):
                if 0 <= x < W and mp[x, y] > 127:
                    owner[x, y] = k
    pn = {k: normals(parts[k]) for k in order}
    # 부위 안 거리(가장자리에서 몇 칸 안인지) — 왼쪽 가장자리에서 2~3칸까지 따뜻한 반사
    def left_depth(x, y, k):
        for dd in range(1, 5):
            if owner.get((x - dd, y)) != k:
                return dd
        return 5
    skin = ("legs", "armR", "torso", "armL", "head")
    for (x, y), k in owner.items():
        j = tex.at(x / W, y / H) - 0.5
        v = (y - HY) / HS
        if k in skin:
            c = G[1] if j < 0.12 else G[2]
        elif k == "cloth":
            c = B[0] if v > 54 or j < -0.1 else G[1]         # 피에 절어 검붉은 허리천
            if v > 58 and j > 0.1:
                c = B[1]
        elif k == "pauldron":
            c = G[4] if v < 17 else (G[3] if v < 20.5 else G[2])
        else:
            u = (x - HX) / HS
            c = G[2] if u < 12.0 else G[5]
        px[x, y] = (*c, 255)
    # 부위 경계(앞 부위 가장자리 1도트 먹선)
    for k in ("cloth", "armL", "head", "pauldron", "diary", "armR"):
        e = edges(parts[k])
        for side in ("l", "r", "t", "b"):
            for (x, y) in e[side]:
                nx, ny = {"l": (x - 1, y), "r": (x + 1, y), "t": (x, y - 1), "b": (x, y + 1)}[side]
                if (nx, ny) in owner and owner[nx, ny] != k:
                    px[x, y] = (*G[1], 255) if k != "pauldron" else (*G[3], 255)
    d = ImageDraw.Draw(im)
    # 근육 결: 등뼈 골 · 견갑골 · 광배 · 삼두 · 장딴지
    d.line([P(0.4, 15), P(0.8, 22), P(0.4, 30), P(0.8, 38), P(0.5, 43)], fill=(*G[1], 255))
    for pts in ([(-10.6, 18.4), (-6.2, 21.0), (-4.0, 27.6)], [(10.8, 18.6), (6.6, 21.2), (4.6, 27.8)]):
        d.line([P(*p) for p in pts], fill=(*G[1], 255))
        d.line([P(p[0], p[1] - 0.7) for p in pts[:2]], fill=(*G[3], 255))
    d.line([P(-10.0, 33.0), P(-6.0, 40.0)], fill=(*G[1], 255))
    d.line([P(10.0, 33.0), P(6.2, 40.0)], fill=(*G[1], 255))
    d.line([P(-15.0, 23.0), P(-15.6, 30.0)], fill=(*G[1], 255))
    d.line([P(14.6, 23.0), P(15.0, 30.0)], fill=(*G[1], 255))
    d.line([P(-4.4, 72.0), P(-4.6, 80.0)], fill=(*G[1], 255))
    # 붕대(두 팔뚝 · 오른 정강이 · 두 발): 비스듬한 띠
    for (a, b, w, k) in (((-16.6, 37.4), (-16.0, 45.2), 5.4, "armL"), ((15.6, 37.4), (14.7, 45.0), 5.2, "armR"),
                         ((7.4, 76.0), (8.9, 90.6), 6.4, "legs"), ((-9.0, 93.0), (-4.0, 99.0), 7.0, "legs"), ((7.5, 92.4), (12.5, 98.8), 7.0, "legs")):
        n = 6 if k != "legs" else 7
        for i in range(n):
            t = (i + 0.4) / n
            cx, cy = P(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            hw = w * HS / 2
            for xx in range(int(cx - hw - 1), int(cx + hw) + 2):
                yy = int(cy + (xx - cx) * 0.35)
                for dy, col in ((0, G[4]), (1, G[3])):
                    if owner.get((xx, yy + dy)) == k:
                        stain = (xx * 3 + yy * 7) % 11 < 3                 # 붕대에 밴 피
                        px[xx, yy + dy] = (*(B[2] if stain and dy == 0 else col), 255)
    # 왼 정강이받이(쇠)
    for (x, y), k in owner.items():
        if k == "legs":
            u, v = (x - HX) / HS, (y - HY) / HS
            if -9.6 < u < -2.4 and 73 < v < 88:
                px[x, y] = (*(G[3] if (x + 2 * y) % 9 else G[4]), 255)
                if v > 87:
                    px[x, y] = (*G[2], 255)
    for (u, v) in ((-13.4, 18.0), (-9.6, 16.4), (-14.8, 21.4), (-7.6, 76.0), (-7.8, 84.0)):
        x, y = P(u, v)
        d.point((round(x), round(y)), fill=(*G[6], 255))
    # 견갑 아랫판 구분선
    d.line([P(-16.2, 20.4), P(-10.4, 18.8), P(-7.0, 16.4)], fill=(*G[3], 255))
    # 허리띠 · 일기장 걸쇠 · 허리천 주름
    for (x, y), k in owner.items():
        v = (y - HY) / HS
        if k == "cloth" and 42.4 <= v < 44.8:
            px[x, y] = (*G[1], 255)
    x, y = P(-1.0, 43.6)
    d.rectangle([round(x) - 1, round(y) - 1, round(x) + 2, round(y) + 1], fill=(*G[4], 255))
    x, y = P(10.2, 48.4)
    d.rectangle([round(x) - 1, round(y) - 1, round(x) + 1, round(y) + 1], fill=(*G[4], 255))
    d.line([P(12.0, 44.0), P(12.8, 52.6)], fill=(*G[6], 255))
    for (a, b) in (((-3.4, 46.0), (-4.4, 57.0)), ((6.4, 46.6), (9.0, 55.0))):
        d.line([P(*a), P(*b)], fill=(*G[1], 255))
    # 테두리 빛 — 법선이 도시 쪽이면 호박(위일수록 밝게), 달 쪽이면 차가운 회색
    nfun = normals(sil)
    e = edges(sil)
    rim = set(e["l"]) | set(e["t"]) | set(e["r"])
    rim_pts = []
    for (x, y) in rim:
        nx, ny = nfun(x, y)
        v = (y - HY) / HS
        up_ = -ny                                            # 달이 바로 뒤(머리 뒤) — 위·옆을 향한 가장자리에 역광
        dm = math.hypot(x - 491, y - 150)
        if v > 62:
            if abs(nx) > 0.6 and (x + y) % 3:                   # 다리 바깥 가장자리: 아주 약한 역광(실루엣 분리)
                px[x, y] = (*G[3], 255)
            continue
        if up_ < -0.3:
            continue
        if dm < 40 and up_ > -0.1:
            px[x, y] = (*G[7], 255)
            rim_pts.append((x, y))
        elif dm < 70:
            px[x, y] = (*G[5], 255)
            rim_pts.append((x, y))
        elif v < 50:
            px[x, y] = (*G[4], 255)
    # 부러진 화살(등·오른어깨) — 2도트 화살대 + 깃
    for (a, b) in ARROWS:
        x0, y0 = P(*a)
        x1, y1 = P(*b)
        d.line([(x0, y0), (x1, y1)], fill=(*G[1], 255), width=2)
        d.line([(x0 - 1, y0), (x1 - 1, y1)], fill=(*G[3], 255))
        dx, dy = (x1 - x0), (y1 - y0)
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        for s_ in (-1, 1):
            for k_ in range(3):
                bx, by = x1 - ux * (1 + k_ * 1.5), y1 - uy * (1 + k_ * 1.5)
                d.line([(bx, by), (bx - ux * 3 + s_ * uy * 3, by - uy * 3 - s_ * ux * 3)], fill=(*(G[4] if s_ < 0 else G[2]), 255))
        d.line([(x1, y1), (x1 + ux * 2, y1 + uy * 2)], fill=(*G[1], 255))
    # 등 상흔 균열(호박 발광) — P20: 번개 지그재그 → 찢긴 틈에서 새는 불(불규칙 테 + 안쪽 밝은 심). 두개골 실금 없음(숯빛 맨머리)
    ed = ImageDraw.Draw(emis)
    tear = [(-1.2, 19.0), (1.4, 20.8), (3.6, 21.4), (2.6, 23.6), (4.4, 26.2), (3.0, 28.6), (3.4, 31.8), (1.4, 33.6), (0.8, 36.6),
            (-0.8, 34.4), (-3.0, 33.0), (-2.4, 30.2), (-4.4, 27.6), (-3.0, 25.4), (-3.8, 22.6), (-1.8, 21.6)]
    core = [(-0.4, 21.6), (1.6, 23.4), (2.2, 26.4), (1.4, 29.6), (0.4, 32.4), (-1.2, 30.4), (-2.0, 27.2), (-1.4, 24.0)]
    twigs = [((3.6, 21.4), (6.2, 20.0)), ((-4.4, 27.6), (-6.8, 28.6)), ((3.4, 31.8), (5.6, 33.4)), ((-3.0, 33.0), (-4.6, 35.4))]
    sc = lambda pts, k=0.62, c=(0.0, 27.0): [(c[0] + (u - c[0]) * k, c[1] + (v - c[1]) * k) for u, v in pts]   # 62 판보다 작게
    d.polygon([P(*p) for p in sc(tear)], fill=(*B[3], 255), outline=(*B[2], 255))
    d.polygon([P(*p) for p in sc(core)], fill=(*B[5], 255))
    d.polygon([P(*p) for p in sc(((0.2, 23.6), (1.0, 26.2), (0.4, 29.4), (-0.6, 27.0)))], fill=(*A[6], 255))
    for a, b in twigs:
        d.line([P(*p) for p in sc((a, b))], fill=(*B[2], 255))
    ed.polygon([P(*p) for p in sc(core)], fill=(*B[5], 110))
    # 눈(옆얼굴 윤곽의 분노한 눈 하나)
    ex, ey = P(-4.6, 6.2)
    ex, ey = round(ex), round(ey)
    for (ox, oy, c) in ((0, 0, A[11]), (-1, 0, A[10]), (1, 0, A[9]), (1, -1, A[9]), (2, -1, A[8]), (-2, 0, A[7]), (-1, 1, A[5]), (0, 1, A[6])):
        px[ex + ox, ey + oy] = (*c, 255)
    ImageDraw.Draw(emis_eye).ellipse([ex - 1, ey - 1, ex + 2, ey + 1], fill=(*A[10], 255))
    for (x, y) in rim_pts:                                   # 달 역광 테의 차가운 번짐(약하게)
        ed.point((x, y), fill=(*G[11], 60))
    # 왼어깨 혼불
    fx, fy = P(-13.4, 15.6)                                  # 62 의 어깨 혼불 → 꺼져 가는 불씨 몇 점(재 연기)
    for (ox, oy, c) in ((0, -1, B[4]), (-1, -3, B[3]), (-2, -6, G[3]), (-1, -9, G[2]), (-3, -11, G[2])):
        px[round(fx) + ox, round(fy) + oy] = (*c, 255)
    return sil, owner


# ------------------------------------------------------------------ 무기 4종(꽂힘)
def outline_layer(im, layer, col=G[0]):
    """layer(RGBA) 를 im 위에 올리되 바깥 1도트 먹 외곽선을 먼저 깐다."""
    a = layer.split()[3]
    grown = a.filter(ImageFilter.MaxFilter(3))
    ol = Image.new("RGBA", im.size, (*col, 255))
    im.paste(ol, (0, 0), grown)
    im.alpha_composite(layer)


def blade_poly(p0, p1, w0, w1, curve=0.0, n=24):
    """p0 → p1 을 따라 굵기 w0 → w1, 옆으로 curve 만큼 휘는 다각형(왼변·오른변)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    left, right, mid = [], [], []
    for i in range(n + 1):
        t = i / n
        off = curve * 4 * t * (1 - t)
        cx, cy = p0[0] + dx * t + nx * off, p0[1] + dy * t + ny * off
        w = (w0 + (w1 - w0) * t) / 2
        left.append((cx + nx * w, cy + ny * w))
        right.append((cx - nx * w, cy - ny * w))
        mid.append((cx, cy))
    return left, right, mid


def draw_weapons(im, emis, wisps):
    """emis = {'katana': RGBA, ...} — 무기마다 따로(목소리가 차례로 울리게)."""

    def along(p0, ang, t):
        return (p0[0] + math.sin(ang) * t, p0[1] - math.cos(ang) * t)

    # ---- 대검(주인공 왼쪽) — 녹슨 양손검, 박힌 화살촉, 용암 균열
    gs = weapon_ramp("greatsword")
    ed = ImageDraw.Draw(emis["greatsword"])
    L_ = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(L_)
    ang = math.radians(-8)
    base = (414, 352)
    guard = along(base, ang, 70)
    left, right, mid = blade_poly(along(base, ang, -2), guard, 8, 12)
    poly(d, left + right[::-1], (*G[4], 255))
    poly(d, left + mid[::-1], (*G[6], 255))                       # 도시 쪽(왼) 빛 면
    d.line(mid, fill=(*G[2], 255))                                 # 가운데 홈
    d.line(left, fill=(*G[8], 255))
    d.line(right, fill=(*G[3], 255))
    r = random.Random(41)
    for t in (52, 60, 66):                                         # 날 위쪽에서 아래로 흘러내린 마른 피 줄기
        x, y = along(base, ang, t)
        x += r.randint(-3, 2)
        ln = r.randint(10, 22)
        d.line([(x, y), (x - ln * math.sin(ang) * 0.2, y + ln)], fill=(*B[2], 255))
        d.point((round(x - ln * math.sin(ang) * 0.2), round(y + ln + 1)), fill=(*B[3], 255))
    for t in (16, 40):                                             # 박힌 화살촉
        x, y = along(base, ang, t)
        poly(d, [(x + 3, y), (x + 9, y - 3), (x + 8, y + 1)], (*G[7], 255))
        d.line([(x + 9, y - 3), (x + 13, y - 5)], fill=(*G[2], 255))
    lava = [((4, -1), (13, 2), (20, -1)), ((30, 1), (36, -2), (43, 1)), ((52, -2), (60, 1))]
    for seg in lava:
        pts = []
        for t, o in seg:
            x, y = along(base, ang, t)
            pts.append((x + o * 1.3, y))
        d.line(pts, fill=(*gs[1], 255))
        d.point((round(pts[0][0]), round(pts[0][1])), fill=(*gs[2], 255))
        ed.line(pts, fill=(*gs[1], 255), width=2)
    g0, g1 = along(guard, ang - math.pi / 2, 16), along(guard, ang + math.pi / 2, 16)
    poly(d, stroke_poly(g0, g1, 5, 5), (*G[3], 255))
    d.line([(g0[0], g0[1] - 2), (g1[0], g1[1] - 2)], fill=(*G[6], 255))
    for gp in (g0, g1):
        d.ellipse([gp[0] - 3, gp[1] - 2, gp[0] + 3, gp[1] + 4], fill=(*G[3], 255))
        d.point((round(gp[0]) - 1, round(gp[1]) - 1), fill=(*G[7], 255))
    pom = along(base, ang, 94)
    poly(d, stroke_poly(along(base, ang, 72), along(base, ang, 90), 5, 5), (*G[1], 255))
    for t in range(73, 90, 3):
        x, y = along(base, ang, t)
        d.line([(x - 2, y + 1), (x + 2, y - 1)], fill=(*G[3], 255))
    d.ellipse([pom[0] - 4, pom[1] - 4, pom[0] + 4, pom[1] + 4], fill=(*G[4], 255))
    d.ellipse([pom[0] - 2, pom[1] - 2, pom[0] + 2, pom[1] + 2], fill=(*G[1], 255))
    d.point((round(pom[0]) - 3, round(pom[1]) - 1), fill=(*G[8], 255))
    outline_layer(im, L_)
    wisps.append(("greatsword", (pom[0], pom[1] - 5)))
    # ---- 칼 은선(주인공 오른쪽) — 가늘고 휜 날, 서리 날빛, 긴 손잡이와 술
    kt = weapon_ramp("katana")
    ed = ImageDraw.Draw(emis["katana"])
    L_ = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(L_)
    ang = math.radians(11)
    base = (566, 350)
    tsuba = along(base, ang, 66)
    left, right, mid = blade_poly(along(base, ang, -1), tsuba, 3, 5, curve=-3.0)
    poly(d, left + right[::-1], (*G[7], 255))
    d.line(right, fill=(*G[3], 255))                                # 칼등(그늘)
    d.line(left, fill=(*G[11], 255))                                # 날(빛)
    for i, p in enumerate(left[4:20]):
        if i % 3 != 2:
            d.point((round(p[0]), round(p[1])), fill=(*kt[2], 255))
    d.point((round(left[13][0]), round(left[13][1])), fill=(255, 255, 255, 255))
    ed.line(left[3:21], fill=(*kt[1], 255), width=2)
    d.ellipse([tsuba[0] - 6, tsuba[1] - 2, tsuba[0] + 6, tsuba[1] + 2], fill=(*G[1], 255))
    d.arc([tsuba[0] - 6, tsuba[1] - 2, tsuba[0] + 6, tsuba[1] + 2], 160, 300, fill=(*G[4], 255))
    hilt = along(tsuba, ang, 24)
    poly(d, stroke_poly(along(tsuba, ang, 1), hilt, 5, 5), (*G[1], 255))
    for t in range(3, 23, 3):                                       # 손잡이 감은 끈(마름모)
        x, y = along(tsuba, ang, t)
        d.point((round(x) - 1, round(y)), fill=(*G[5], 255))
        d.point((round(x) + 1, round(y) - 1), fill=(*G[4], 255))
    d.ellipse([hilt[0] - 2, hilt[1] - 2, hilt[0] + 2, hilt[1] + 2], fill=(*G[3], 255))
    for i, p in enumerate(left[2:10]):                              # 날 아래쪽에 흘러내린 피
        if i % 2 == 0:
            d.point((round(p[0]) + 1, round(p[1])), fill=(*B[3], 255))
    # 술(서리 색) — 바람에 오른쪽으로
    tas = [along(tsuba, ang, 20), (hilt[0] + 4, hilt[1] + 6), (hilt[0] + 9, hilt[1] + 9), (hilt[0] + 13, hilt[1] + 14)]
    d.line(tas, fill=(*kt[0], 255), width=2)
    d.line(tas[:3], fill=(*kt[1], 255))
    outline_layer(im, L_)
    wisps.append(("katana", (hilt[0], hilt[1] - 3)))
    # ---- 활(맨 오른쪽, 아래 끝이 땅에 박혀 기움) — 반곡궁, 비취 시위
    bw = weapon_ramp("bow")
    ed = ImageDraw.Draw(emis["bow"])
    L_ = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(L_)
    top, bot = (606, 256), (594, 350)
    limb_pts = []
    for i in range(49):
        t = i / 48
        x = top[0] + (bot[0] - top[0]) * t
        y = top[1] + (bot[1] - top[1]) * t
        x -= 12 * math.sin(math.pi * t)
        if t < 0.1:
            x += (0.1 - t) * 70
        if t > 0.9:
            x += (t - 0.9) * 70
        limb_pts.append((x, y))
    d.line(limb_pts, fill=(*G[2], 255), width=4)
    d.line([(p[0] - 1, p[1]) for p in limb_pts], fill=(*G[3], 255))
    d.line([(p[0] - 2, p[1]) for p in limb_pts[6:42]], fill=(*G[4], 255))
    mid = limb_pts[24]
    d.rectangle([mid[0] - 3, mid[1] - 5, mid[0] + 2, mid[1] + 5], fill=(*G[1], 255))
    for k in range(-4, 5, 2):
        d.point((round(mid[0]) - 1, round(mid[1]) + k), fill=(*G[5], 255))
    d.line([limb_pts[2], limb_pts[-3]], fill=(*bw[1], 255))
    ed.line([limb_pts[2], limb_pts[-3]], fill=(*bw[1], 255), width=2)
    outline_layer(im, L_)
    wisps.append(("bow", (limb_pts[1][0], limb_pts[1][1] - 2)))
    # ---- 단검 재 발톱(주인공 앞, 쓰러진 투구에 박힘) — 갈고리 발톱 날 + 독빛
    dg = weapon_ramp("dagger")
    ed = ImageDraw.Draw(emis["dagger"])
    L_ = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(L_)
    hx, hy = 450, 350
    d.ellipse([hx - 11, hy - 9, hx + 11, hy + 6], fill=(*G[2], 255))      # 투구
    d.arc([hx - 11, hy - 9, hx + 11, hy + 6], 230, 330, fill=(*G[4], 255))
    d.ellipse([hx - 9, hy + 1, hx + 4, hy + 6], fill=(*B[1], 255))          # 투구 밑 피
    d.line([(hx - 11, hy + 1), (hx + 11, hy + 1)], fill=(*G[1], 255))
    d.rectangle([hx - 6, hy - 1, hx - 2, hy], fill=(*G[0], 255))
    claw_out = [(hx + 2, hy - 6), (hx + 8, hy - 13), (hx + 10, hy - 21), (hx + 8, hy - 28), (hx + 3, hy - 32)]
    claw_in = [(hx + 2, hy - 6), (hx + 5, hy - 13), (hx + 6, hy - 20), (hx + 4, hy - 26), (hx + 3, hy - 32)]
    poly(d, claw_out + claw_in[::-1], (*G[5], 255))
    d.line(claw_out, fill=(*G[8], 255))
    d.line(claw_in, fill=(*dg[1], 255))
    ed.line(claw_in, fill=(*dg[1], 255), width=2)
    d.point((hx + 3, hy - 4), fill=(*dg[1], 255))                        # 독 방울
    d.point((hx + 3, hy - 3), fill=(*dg[0], 255))
    poly(d, stroke_poly((hx + 4, hy - 32), (hx + 7, hy - 44), 4, 4), (*G[1], 255))
    for k in range(34, 44, 3):
        d.point((hx + 4 + (k - 32) // 4, hy - k), fill=(*G[4], 255))
    d.ellipse([hx + 4, hy - 50, hx + 10, hy - 44], outline=(*G[4], 255))
    outline_layer(im, L_)
    wisps.append(("dagger", (hx + 7, hy - 51)))


def draw_wisp(im, emis, kind, at, seed):
    """원한의 목소리: 무기에서 피어오르는 무기 색 혼불 실(가늘고 휘어 오름)."""
    r = random.Random(seed)
    px = im.load()
    ramp = weapon_ramp(kind)
    x0, y0 = at
    ln = 18 if kind != "dagger" else 12
    ph = r.uniform(0, 6)
    for i in range(ln):
        t = i / ln
        x = x0 + math.sin(t * 5.0 + ph) * 3.2 * t + t * 6
        y = y0 - i * 1.2
        if not (0 <= x < W and 0 <= y < H):
            continue
        c = ramp[1] if t < 0.3 else ramp[0]
        if t > 0.6 and i % 2:
            continue
        xi, yi = round(x), round(y)
        px[xi, yi] = (*c, 255)
        emis[kind].putpixel((xi, yi), (*ramp[1], 255))


# ------------------------------------------------------------------ 시체 더미 · 왼쪽 아래 전경
MN = Fbm(95, 8, 1, 3)


def mound_top(x):
    n = MN.at(x / W, 0.5)
    base = 333 + ((x - 490) / 120) ** 2 * 18
    return base + (n - 0.5) * 8


def draw_mound(im):
    d = ImageDraw.Draw(im)
    px = im.load()
    r = random.Random(97)
    m = mask_new()
    md = ImageDraw.Draw(m)
    tops = {}
    for x in range(330, W):
        y = mound_top(x)
        tops[x] = y
        md.line([(x, int(y)), (x, H)], fill=255)
    # 더미의 덩어리들: 투구·방패·어깨·창대
    blobs = []
    for _ in range(26):
        x = r.randint(340, 636)
        y = tops[x] + r.uniform(-2, 4)
        kind = r.choice(["helm", "helm", "shield", "body", "body"])
        blobs.append((kind, x, y))
        if kind == "helm":
            md.ellipse([x - 5, y - 5, x + 5, y + 3], fill=255)
        elif kind == "shield":
            md.ellipse([x - 8, y - 6, x + 8, y + 4], fill=255)
        else:
            md.ellipse([x - 11, y - 4, x + 11, y + 4], fill=255)
    shafts = []
    for _ in range(9):
        x = r.randint(345, 636)
        y = tops[x]
        ang = math.radians(r.choice([-1, 1]) * r.uniform(20, 62))
        ln = r.randint(14, 36)
        x1, y1 = x + math.sin(ang) * ln, y - math.cos(ang) * ln
        shafts.append(((x, y), (x1, y1)))
    # 칠: 아래로 어두워짐
    f = Fbm(96, 20, 10, 3)
    mp = m.load()
    for y in range(280, H):
        for x in range(330, W):
            if mp[x, y] > 127:
                j = f.at(x / W, y / H) - 0.5
                t = (y - tops.get(x, y)) / 26
                px[x, y] = (*band([G[2], G[1], G[1], G[0]], max(0, min(1, t)), j * 0.8), 255)
    # 덩어리 윤곽선 + 윗면 빛
    for kind, x, y in blobs:
        if kind == "helm":
            d.arc([x - 5, y - 5, x + 5, y + 3], 220, 330, fill=(*G[4], 255) if x > 440 else (*G[3], 255))
            d.arc([x - 5, y - 5, x + 5, y + 3], 180, 220, fill=(*G[2], 255))
            d.line([(x - 5, y), (x + 5, y)], fill=(*G[0], 255))
            d.line([(x - 3, y - 1), (x + 1, y - 1)], fill=(*G[0], 255))
            d.point((x + 1, y - 4), fill=(*G[6], 255) if x > 440 else (*G[4], 255))
        elif kind == "shield":
            d.ellipse([x - 8, y - 6, x + 8, y + 4], outline=(*G[1], 255))
            d.arc([x - 8, y - 6, x + 8, y + 4], 220, 320, fill=(*G[3], 255))
            d.point((x, y - 1), fill=(*G[4], 255))
        else:
            d.arc([x - 11, y - 4, x + 11, y + 4], 190, 340, fill=(*G[3], 255))
    e = edges(m)
    for (x, y) in e["t"]:
        if x < 440:
            px[x, y] = (*G[2], 255)
        else:
            px[x, y] = (*G[4], 255) if (x // 3) % 4 else (*G[3], 255)        # 달 쪽 젖은 윗면
    for (p0, p1) in shafts:
        d.line([p0, p1], fill=(*G[1], 255), width=2)
        d.line([(p0[0] - 1, p0[1]), (p1[0] - 1, p1[1])], fill=(*G[2], 255))
        d.point((round(p1[0]), round(p1[1])), fill=(*G[4], 255))
    # 더미에서 위로 내민 손(망령이 일어난 자리 — 원한들)
    for (hx, hy, s_) in ((528, 344, 1), (382, 352, -1)):
        arm = [(hx, hy), (hx + 3 * s_, hy - 9), (hx + 4 * s_, hy - 16)]
        d.line(arm, fill=(*G[1], 255), width=3)
        d.line([(p[0] - 1, p[1]) for p in arm], fill=(*G[2], 255))
        fx, fy = arm[-1]
        for k, (ox, oy) in enumerate(((-3, -4), (-1, -6), (1, -6), (3, -4), (4, -1))):
            d.line([(fx, fy), (fx + ox * s_, fy + oy)], fill=(*G[1], 255))
        d.point((round(fx) - 2 * s_, round(fy) - 3), fill=(*G[3], 255))
    mound_blood(im, m, tops, r)
    for (p0, p1) in shafts[:3]:                                      # 창대 끝 까마귀
        crow(d, p1[0], p1[1], 1, 1 if p1[0] < p0[0] else -1)
    return m


def crow(d, x, y, s=1, face=1):
    """앉은 까마귀(근경 — 중경보다 크게). 몸 G0, 달빛 깃 윤기 G3, 눈 한 점."""
    c = (*G[0], 255)
    x, y = round(x), round(y)
    poly(d, [(x - 4 * face, y - 1), (x - 1 * face, y - 6), (x + 3 * face, y - 6), (x + 4 * face, y - 3), (x + 1 * face, y)], c)
    d.ellipse([x + 2 * face - 2, y - 9, x + 2 * face + 2, y - 5], fill=c)
    poly(d, [(x + 4 * face, y - 8), (x + 7 * face, y - 7), (x + 4 * face, y - 6)], c)
    poly(d, [(x - 4 * face, y - 1), (x - 9 * face, y + 1), (x - 8 * face, y - 1)], c)
    d.line([(x, y), (x, y + 2)], fill=c)
    d.line([(x - 1 * face, y - 5), (x + 2 * face, y - 5)], fill=(*G[3], 255))
    d.point((x + 3 * face, y - 7), fill=(*G[5], 255))


def mound_blood(im, m, tops, r):
    """시체 더미의 피: 윗면 웅덩이(검붉음 + 젖은 달빛 한 점) · 아래로 흐른 줄기."""
    px = im.load()
    mp = m.load()
    for _ in range(16):
        x = r.randint(345, 630)
        y = min(H - 2, int(tops[x]) + r.randint(2, 10))
        w = r.randint(3, 9)
        for xx in range(x - w, x + w + 1):
            for yy in (y, y + 1):
                if 0 <= xx < W and yy < H and mp[xx, yy] > 127:
                    px[xx, yy] = (*(B[2] if yy == y else B[1]), 255)
        if x + 1 < W and y < H:
            px[x + 1, y] = (*B[3], 255)
        if x > 470 and y < H:
            px[x - 2, y] = (*G[4], 255)                            # 웅덩이에 비친 달
        for k in range(r.randint(3, 12)):                           # 흘러내린 줄기
            yy = y + 2 + k
            if yy < H and mp[x, yy] > 127:
                px[x, yy] = (*B[1], 255)


def pool(im, cx, cy, rx, ry, seed):
    """불규칙한 피 웅덩이: 가장자리 B1, 안쪽 B2 조금, 달빛 반사 한 점."""
    px = im.load()
    n = Fbm(400 + seed, 6, 3, 2)
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 3), int(cx + rx + 4)):
            if not (0 <= x < W and 0 <= y < H):
                continue
            dd = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            v = n.at(x / W * 8, y / H * 8) - 0.5
            if dd + v * 0.9 > 1.0:
                continue
            px[x, y] = (*(B[2] if dd + v * 0.6 < 0.3 else B[1]), 255)
    px[int(cx - rx * 0.3), int(cy)] = (*G[3], 255)


def banquet(im):
    """피 묻은 연회장 잔해(시체 더미 왼쪽 발치 — 메뉴 틀과 주인공 사이): 엎어진 긴 상, 찢긴 식탁보, 깨진 술독, 뒤집힌 의자, 잔, 상에 기댄 시체."""
    d = ImageDraw.Draw(im)
    k0, k1, k2, k3 = (*G[0], 255), (*G[1], 255), (*G[2], 255), (*G[3], 255)
    b1, b2, b3 = (*B[1], 255), (*B[2], 255), (*B[3], 255)
    # 바닥에 번진 술·피(불규칙)
    pool(im, 246, 354, 52, 6, 1)
    pool(im, 292, 353, 14, 3, 2)
    # 엎어진 긴 상: 한쪽 끝이 시체 위에 걸려 비스듬히 선 상판 + 옆으로 뻗은 다리 둘
    poly(d, [(222, 318), (300, 336), (298, 344), (218, 326)], k1)
    d.line([(222, 318), (300, 336)], fill=(*G[4], 255))           # 상판 모서리(달빛)
    d.line([(222, 319), (300, 337)], fill=k3)
    d.line([(218, 326), (298, 344)], fill=k0)
    for i in range(4):                                              # 판자 이음
        x = 236 + i * 17
        d.line([(x, 321 + i * 4), (x - 2, 329 + i * 4)], fill=k0)
    for lx in (232, 284):
        ly = 326 + (lx - 218) * 0.225
        poly(d, [(lx, ly), (lx + 3, ly + 1), (lx - 8, ly + 18), (lx - 11, ly + 17)], k1)
        d.line([(lx + 3, ly + 1), (lx - 8, ly + 18)], fill=k2)
    # 찢긴 식탁보(상판 앞으로 늘어짐, 피 얼룩)
    poly(d, [(232, 323), (270, 332), (271, 341), (266, 339), (263, 347), (257, 341), (249, 350), (246, 340), (238, 346), (235, 338), (230, 342)], k1)
    d.line([(232, 323), (270, 332)], fill=k2)
    for x0 in (238, 247, 256, 264):                                 # 주름(세로 그늘)
        d.line([(x0, 326 + (x0 - 232) // 4), (x0 - 1, 340)], fill=k0)
    for (x, y, ln) in ((241, 327, 9), (252, 330, 13), (260, 332, 7)):   # 위에서 스며 흘러내린 피
        d.line([(x, y), (x, y + ln)], fill=b2)
        d.line([(x + 1, y), (x + 1, y + ln // 2)], fill=b1)
        d.point((x, y + ln + 2), fill=b2)
    # 상에 기대 앉은 시체(머리를 떨군)
    poly(d, [(286, 348), (290, 334), (297, 332), (300, 348)], k0)
    d.ellipse([293, 334, 300, 341], fill=k0)
    d.line([(288, 340), (281, 351)], fill=k0, width=2)
    d.line([(296, 336), (299, 335)], fill=k2)
    pool(im, 291, 353, 9, 2, 3)
    # 깨진 술독(쓰러져 쏟음) · 선 술독 · 잔
    d.ellipse([180, 344, 196, 356], fill=k1)
    d.arc([180, 344, 196, 356], 200, 300, fill=k3)
    poly(d, [(194, 346), (200, 344), (199, 352), (195, 354)], k0)  # 깨진 입
    d.line([(198, 352), (210, 356)], fill=b2)
    d.ellipse([304, 340, 314, 354], fill=k1)
    d.arc([304, 340, 314, 354], 230, 320, fill=k3)
    d.line([(305, 344), (313, 344)], fill=k0)
    for (x, y) in ((206, 344), (272, 356)):
        d.line([(x, y), (x + 3, y)], fill=k3)
        d.line([(x + 1, y + 1), (x + 2, y + 1)], fill=k2)
        d.line([(x + 1, y + 2), (x + 2, y + 3)], fill=k2)
    # 뒤집힌 의자(다리 넷)
    poly(d, [(318, 350), (330, 348), (331, 352), (319, 354)], k1)
    for lx in (319, 323, 327, 330):
        d.line([(lx, 350), (lx + 1, 341)], fill=k1)
    d.line([(318, 350), (330, 348)], fill=k2)


def lantern_pole(im):
    """연회 등롱 장대: 기운 장대 + 가로대, 꺼진 등롱 둘(하나는 찢김), 떨어져 깨진 등롱 하나, 꼭대기에 까마귀."""
    d = ImageDraw.Draw(im)
    k0, k1, k2, k3 = (*G[0], 255), (*G[1], 255), (*G[2], 255), (*G[3], 255)
    d.line([(198, 356), (206, 250)], fill=k0, width=3)
    d.line([(199, 356), (207, 252)], fill=k1)
    d.line([(203, 258), (246, 262)], fill=k0, width=2)
    d.line([(203, 257), (246, 261)], fill=k2)
    for (x, y, ln, torn) in ((222, 260, 9, False), (240, 262, 14, True)):
        d.line([(x, y), (x + 1, y + ln)], fill=k1)
        cx, cy = x + 1, y + ln
        if torn:
            poly(d, [(cx - 4, cy), (cx + 3, cy - 1), (cx + 5, cy + 6), (cx + 1, cy + 11), (cx - 2, cy + 7), (cx - 5, cy + 9)], k2)
            d.line([(cx - 3, cy + 4), (cx + 4, cy + 3)], fill=k1)
        else:
            d.ellipse([cx - 5, cy, cx + 5, cy + 12], fill=k2)
            for yy in (cy + 3, cy + 6, cy + 9):
                d.line([(cx - 4, yy), (cx + 4, yy)], fill=k1)
            d.line([(cx + 3, cy + 2), (cx + 3, cy + 9)], fill=k3)
            d.ellipse([cx - 3, cy + 7, cx, cy + 10], fill=(*G[1], 255))      # 그을린 자국
        d.rectangle([cx - 2, cy - 1, cx + 2, cy], fill=k0)
        d.rectangle([cx - 2, cy + 10, cx + 2, cy + 11], fill=k0)
    # 떨어져 짓밟힌 등롱
    poly(d, [(208, 352), (220, 350), (222, 355), (210, 357)], k2)
    d.line([(209, 353), (221, 351)], fill=k1)
    crow(d, 207, 249, 1, -1)


def draw_left_fg(im):
    """왼쪽 아래 구석: 아주 어두운 풀·부러진 창(메뉴 뒤 — 낮은 대비)."""
    d = ImageDraw.Draw(im)
    r = random.Random(99)
    f = Fbm(98, 6, 1, 3)
    for x in range(0, 300):
        top = 346 + (x / 300) ** 1.5 * 16 + (f.at(x / W, 0.4) - 0.5) * 10
        d.line([(x, int(top)), (x, H)], fill=(*G[0], 255))
    for _ in range(60):
        x = r.randint(0, 300)
        top = 346 + (x / 300) ** 1.5 * 16
        ln = r.randint(4, 12)
        ang = math.radians(r.uniform(-15, 35))
        poly(d, stroke_poly((x, top + 3), (x + math.sin(ang) * ln, top - math.cos(ang) * ln), 2.4, 0.6), (*G[0], 255))
    for (x, ln, a) in ((18, 64, 16),):
        ang = math.radians(a)
        p0 = (x, 352)
        p1 = (x + math.sin(ang) * ln, 352 - math.cos(ang) * ln)
        d.line([p0, p1], fill=(*G[1], 255), width=2)
        d.line([(p0[0] - 1, p0[1]), (p1[0] - 1, p1[1])], fill=(*G[2], 255))


def glow_layer(emis, k=3, radius=10, gain=1.5):
    """발광 마스크(논리) → 1920×1080 부드러운 빛무리(RGBA, 가산 혼합용). 색 = 빛 색, 알파 = 세기."""
    big = emis.resize((emis.width * k, emis.height * k), Image.NEAREST)
    a = big.split()[3].filter(ImageFilter.GaussianBlur(radius))
    a2 = big.split()[3].filter(ImageFilter.GaussianBlur(radius * 3))
    col = big.convert("RGB")
    # 색 번짐: 알파 가중 흐림
    pre = Image.composite(col, Image.new("RGB", big.size, (0, 0, 0)), big.split()[3]).filter(ImageFilter.GaussianBlur(radius * 2))
    na = big.split()[3].filter(ImageFilter.GaussianBlur(radius * 2))
    out = Image.new("RGBA", big.size, (0, 0, 0, 0))
    op, ap, a2p, pp, nap = out.load(), a.load(), a2.load(), pre.load(), na.load()
    for y in range(big.height):
        for x in range(big.width):
            v = min(255, int((ap[x, y] * 0.7 + a2p[x, y] * 0.6) * gain))
            if v < 3:
                continue
            n = nap[x, y] or 1
            c = pp[x, y]
            cc = tuple(min(255, int(ch * 255 / n)) for ch in c)
            m = max(cc) or 1
            cc = tuple(min(255, int(ch * 255 / m)) for ch in cc)
            op[x, y] = (*cc, v)
    return out


KINDS = ("katana", "greatsword", "dagger", "bow")


def draw_near():
    """반환: near(주인공 포함 RGBA), hero(주인공만 RGBA), emis{'hero', 무기 4} (논리 크기)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    emis = {k: Image.new("RGBA", (W, H), (0, 0, 0, 0)) for k in ("hero", "eye") + KINDS}
    draw_left_fg(im)
    lantern_pole(im)
    draw_mound(im)
    banquet(im)
    wisps = []
    draw_weapons(im, emis, wisps)
    hero = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_hero(hero, emis["hero"], emis["eye"])
    im.alpha_composite(hero)
    for i, (k, at) in enumerate(wisps):
        draw_wisp(im, emis, k, at, 300 + i)
    return im, hero, emis
