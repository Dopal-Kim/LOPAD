"""62a — 첫 생 의식 '3획' 등 그림 `ritual/back_canvas` (타이틀 62 와 같은 붓 그림 결, 논리 640×360 → 3배 1920×1080).

장면: 탄생 전장의 밤, 시체 더미 위에 막 일어선 망령의 상반신 뒷모습(가까이). 등 한가운데는 비어 있다 — 플레이어가 먹 붓으로
세 획을 긋는 자리(`strokeArea`). 상흔 균열은 아직 없다(세 획이 곧 상흔이 된다). 디자인 요소는 타이틀·게임 도트와 같다:
재 몸 · 금 간 민머리(고개를 왼쪽으로 돌려 눈 하나가 윤곽에 걸림) · 왼어깨 견갑 + 혼불 · 오른어깨 부러진 화살 · 붕대 팔뚝.
빛: 왼쪽 아래 = 전장 모닥불(호박, 등 왼쪽을 데움) · 오른쪽 위 = 달(차가운 회색 테). 등 가운데 명도는 G05~G07 —
검은 먹(G01) 획이 또렷하게 읽히는 밝기로 맞췄다.
색: lopad 무채 16 + 1층 호박 램프 12 만(타이틀 원경·근경과 같은 규칙).
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from common import A, G, Fbm, Noise, mask, poly, stroke_poly, edges, mix

W, H = 640, 360

GRAYL = [G[1], G[2], G[3], G[4], G[5], G[6], G[7], G[8], G[9], G[10]]
WARML = [A[0], A[0], A[1], A[1], A[2], A[3], A[3], A[4], A[5], A[6]]
WARMB = [A[0], A[0], A[1], A[1], A[2], A[2], A[3], A[3], A[4], A[4]]     # 몸 안쪽(불빛을 받은 살갗) — 밝은 주황은 테에만

# 등 위에 획을 긋는 자리 (도트) — 몸통 안, 견갑 사이에서 허리까지
STROKE = (232, 128, 176, 212)        # x, y, w, h
FIRES = [(64, 296, 1.0), (600, 304, 0.55), (150, 318, 0.45)]   # 먼 모닥불 (x, y, 세기)


# ------------------------------------------------------------------ 배경
def fire_glow(x, y):
    g = 0.0
    for fx, fy, s in FIRES:
        d = ((x - fx) / 110.0) ** 2 + ((y - fy) / 62.0) ** 2
        g += s * math.exp(-d * 1.6)
    return g


def draw_bg(im, emis):
    px = im.load()
    st = Fbm(301, 3, 16, 4)
    fine = Noise(302, 180, 120)
    smoke = Fbm(303, 6, 4, 4)
    for y in range(H):
        for x in range(W):
            t = y / H
            g = fire_glow(x, y)
            j = (st.at(x / W, y / H) - 0.5) * 0.9 + (fine.at(x / W, y / H) - 0.5) * 0.35
            sm = smoke.at(x / W + y / H * 0.15, y / H)          # 기울어 오르는 연기
            plume = 0.0
            for fx, fy, s in FIRES:                              # 불 위로 오르는 연기 기둥(오른쪽으로 흐름)
                cx = fx + (fy - y) * 0.35
                wd = 18 + (fy - y) * 0.45
                if y < fy:
                    plume += s * math.exp(-((x - cx) / wd) ** 2) * min(1.0, (fy - y) / 40.0)
            v = 0.2 + 1.6 * t ** 2.2 + 4.2 * g + (sm - 0.5) * 2.0 + j * 1.0 + plume * (sm - 0.25) * 2.6
            warm = g + j * 0.25 + (sm - 0.5) * 0.2 > 0.22
            i = max(0, min(9, int(round(v))))
            px[x, y] = (*(WARML if warm else GRAYL)[i], 255)
    # 지평선: 꽂힌 창·찢긴 깃발·시체 더미 실루엣(불빛 앞 검은 그림자)
    d = ImageDraw.Draw(im)
    r = random.Random(305)
    hz = 300
    for x in range(W):
        hh = hz - 6 + int(6 * math.sin(x * 0.031) + 4 * math.sin(x * 0.087 + 1.3))
        for y in range(hh, H):
            px[x, y] = (*G[1], 255)
        if hh - 1 >= 0 and fire_glow(x, hh - 2) > 0.35:
            px[x, hh] = (*A[3], 255)
    for k in range(34):
        x = r.randint(0, W - 1)
        base = hz - 4 + r.randint(-3, 4)
        h = r.randint(14, 46)
        lean = r.uniform(-0.35, 0.35)
        d.line([(x, base), (x + lean * h, base - h)], fill=(*G[1], 255), width=1 if h < 30 else 2)
        if r.random() < 0.28:            # 깃발 조각
            fx, fy = x + lean * h, base - h
            dirn = 1 if r.random() < 0.5 else -1
            poly(d, [(fx, fy + 1), (fx + dirn * r.randint(7, 13), fy + 3), (fx + dirn * r.randint(4, 9), fy + 7),
                     (fx + dirn * r.randint(8, 12), fy + 10), (fx, fy + 9)], (*G[1], 255))
    # 불티(배경, 자체 발광)
    for k in range(70):
        x, y = r.randint(0, W - 1), r.randint(40, 300)
        if fire_glow(x, y + 30) < 0.12 and r.random() < 0.7:
            continue
        c = A[r.choice((7, 8, 9, 10))]
        px[x, y] = (*c, 255)
        emis.putpixel((x, y), (*A[8], 160))
    return im


# ------------------------------------------------------------------ 몸
def body_parts():
    parts = {}

    def new():
        return mask(W, H)

    m, d = new()      # 몸통(등) + 목 — 승모근이 두개골 아래에서 어깨 끝으로 비탈져 내려감
    poly(d, [(302, 92), (338, 92), (344, 108), (362, 118), (392, 128), (420, 136), (440, 146), (446, 168), (448, 198),
             (450, 226), (442, 262), (430, 300), (420, 338), (416, 360), (224, 360), (220, 338), (210, 300), (198, 262),
             (190, 226), (192, 198), (194, 168), (200, 146), (220, 136), (248, 128), (278, 118), (296, 108)], 255)
    parts["torso"] = m
    for side, sx in (("armL", -1), ("armR", 1)):
        m, d = new()
        cx = 320 + sx * 134
        d.ellipse([cx - 40, 128, cx + 40, 220], fill=255)                     # 삼각근
        a0 = (cx + sx * 2, 196)
        a1 = (cx + sx * 38, 372)
        poly(d, stroke_poly(a0, a1, 66, 52), 255)
        d.ellipse([a1[0] - 26, a1[1] - 26, a1[0] + 26, a1[1] + 26], fill=255)
        parts[side] = m
    m, d = new()      # 머리(뒤 3/4, 왼쪽으로 돌림)
    d.ellipse([286, 14, 356, 104], fill=255)
    poly(d, [(290, 52), (281, 60), (283, 68), (278, 76), (283, 84), (286, 94), (296, 104), (306, 108), (312, 80)], 255)
    parts["head"] = m
    m, d = new()      # 왼어깨 견갑(두 겹 판)
    poly(d, [(134, 170), (140, 148), (158, 132), (184, 124), (210, 128), (228, 140), (230, 154), (216, 170), (190, 184),
             (162, 192), (140, 188)], 255)
    parts["pauldron"] = m
    return parts


def inflate(m, radii=((3, 0.8), (8, 1.0), (18, 1.2), (40, 1.4))):
    """마스크를 부풀린 높이장(가장자리 0 → 안쪽 둥글게)."""
    out = Image.new("F", m.size, 0)
    op = out.load()
    tot = sum(w for _, w in radii)
    for r, wgt in radii:
        b = m.filter(ImageFilter.GaussianBlur(r)).load()
        for y in range(m.height):
            for x in range(m.width):
                op[x, y] += b[x, y] * wgt / tot
    return out


def heightfield(parts):
    """부위별 부풀림(팔은 몸통 위로 솟음) + 근육 덩이(견갑골·광배·승모·척추 골)."""
    hf = Image.new("F", (W, H), 0)
    hp = hf.load()
    for k, lift in (("torso", 0), ("head", 0), ("armL", 30), ("armR", 30)):
        f = inflate(parts[k]).load()
        mp = parts[k].load()
        for y in range(H):
            for x in range(W):
                if mp[x, y] > 127:
                    hp[x, y] = max(hp[x, y], f[x, y] + lift) if k.startswith("arm") else max(hp[x, y], f[x, y])
    mus = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mus)
    for cx, sx in ((270, -1), (370, 1)):                                    # 견갑골(비스듬한 삼각 덩이)
        poly(d, [(cx - sx * 34, 150), (cx + sx * 30, 146), (cx + sx * 10, 212)], 150)
    for cx in (232, 408):                                                   # 광배근
        d.ellipse([cx - 32, 214, cx + 32, 330], fill=110)
    poly(d, [(300, 100), (340, 100), (430, 142), (380, 150), (320, 134), (260, 150), (210, 142)], 120)   # 승모
    for cx in (276, 364):                                                   # 척추 세움근
        d.ellipse([cx - 22, 236, cx + 22, 372], fill=90)
    mus = mus.filter(ImageFilter.GaussianBlur(10))
    groove = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(groove)
    gd.line([(320, 128), (321, 200), (319, 270), (320, 360)], fill=170, width=6)       # 척추 골
    gd.line([(236, 206), (268, 218), (300, 206)], fill=90, width=4)                   # 견갑 아래 골
    gd.line([(404, 206), (372, 218), (340, 206)], fill=90, width=4)
    groove = groove.filter(ImageFilter.GaussianBlur(4))
    mp_, gp = mus.load(), groove.load()
    tm = parts["torso"].load()
    for y in range(H):
        for x in range(W):
            if tm[x, y] > 127:
                hp[x, y] += mp_[x, y] * 0.35 - gp[x, y] * 0.3
    return hf


LF = (-0.80, 0.25, 0.55)     # 모닥불(왼쪽 아래 앞)
LM = (0.50, -0.70, 0.50)     # 달(오른쪽 위)


def nrm(v):
    l = math.sqrt(sum(c * c for c in v))
    return tuple(c / l for c in v)


LF, LM = nrm(LF), nrm(LM)


def painted_values():
    """손으로 잡은 명암 덩이(도트 단위 값 더하기): 골·그늘(−), 근육 윗면 빛(+). 흐려서 붓 덩이처럼."""
    f = Image.new("F", (W, H), 0)
    fp = f.load()

    def add(shape_fn, amp, blur):
        m, d = mask(W, H)
        shape_fn(d)
        b = m.filter(ImageFilter.GaussianBlur(blur)).load()
        for y in range(H):
            for x in range(W):
                if b[x, y]:
                    fp[x, y] += amp * b[x, y] / 255.0
    # 그늘
    add(lambda d: d.line([(320, 126), (321, 190), (319, 260), (320, 360)], fill=255, width=9), -2.2, 3)       # 척추 골
    add(lambda d: d.line([(296, 152), (300, 186), (304, 214)], fill=255, width=6), -1.2, 3)                   # 견갑 안쪽 변
    add(lambda d: d.line([(344, 152), (340, 186), (336, 214)], fill=255, width=6), -1.2, 3)
    add(lambda d: d.line([(236, 204), (262, 220), (302, 216)], fill=255, width=8), -1.6, 4)                   # 견갑 아래 골
    add(lambda d: d.line([(404, 204), (378, 220), (338, 216)], fill=255, width=8), -1.6, 4)
    add(lambda d: d.line([(198, 206), (208, 246), (214, 290)], fill=255, width=10), -1.8, 5)                  # 겨드랑이·옆구리
    add(lambda d: d.line([(442, 206), (432, 246), (426, 290)], fill=255, width=10), -1.8, 5)
    add(lambda d: d.line([(300, 104), (320, 112), (340, 104)], fill=255, width=8), -1.6, 3)                   # 두개골 아래 목 그늘
    add(lambda d: d.rectangle([224, 330, 416, 360], fill=255), -1.0, 14)                                       # 허리 아래로 어둠
    for sx in (-1, 1):                                                                                          # 팔 안쪽(몸 쪽) 그늘 · 삼두 말굽
        cx = 320 + sx * 134
        add(lambda d, cx=cx, sx=sx: d.line([(cx - sx * 26, 214), (cx - sx * 14 + sx * 20, 360)], fill=255, width=14), -1.6, 6)
        add(lambda d, cx=cx, sx=sx: d.arc([cx - 26 + sx * 14, 222, cx + 26 + sx * 14, 290], 20, 160, fill=255, width=4), -1.2, 2)
    # 빛 덩이
    add(lambda d: d.polygon([(232, 150), (296, 146), (300, 196), (252, 200)], fill=255), 1.1, 8)                # 왼 견갑 윗면
    add(lambda d: d.polygon([(344, 146), (408, 150), (388, 200), (340, 196)], fill=255), 0.9, 8)                # 오른 견갑 윗면
    add(lambda d: d.polygon([(300, 108), (340, 108), (420, 140), (320, 132), (220, 140)], fill=255), 0.8, 6)    # 승모 윗면
    add(lambda d: d.ellipse([214, 232, 262, 318], fill=255), 0.7, 10)                                           # 광배
    add(lambda d: d.ellipse([378, 232, 426, 318], fill=255), 0.5, 10)
    add(lambda d: d.ellipse([270, 238, 306, 330], fill=255), 0.5, 8)                                            # 척추 세움근
    add(lambda d: d.ellipse([334, 238, 370, 330], fill=255), 0.5, 8)
    for sx in (-1, 1):
        cx = 320 + sx * 134
        add(lambda d, cx=cx: d.ellipse([cx - 26, 138, cx + 22, 186], fill=255), 1.0, 8)                         # 삼각근 머리
    return f


ARM = {"armL": ((184, 196), (148, 372), 33, 26, -1), "armR": ((456, 196), (492, 372), 33, 26, 1)}


def arm_normal(k, x, y, n0):
    """팔뚝 원통 법선(축에서의 거리 → 옆면)."""
    (x0, y0), (x1, y1), w0, w1, sx = ARM[k]
    t = max(0.0, min(1.0, (y - y0) / (y1 - y0)))
    cx = x0 + (x1 - x0) * t
    hw = w0 + (w1 - w0) * t
    u = max(-0.98, min(0.98, (x - cx) / hw))
    return nrm((u, -0.15, math.sqrt(1 - u * u)))


def draw_body(im, emis):
    px = im.load()
    parts = body_parts()
    order = ["torso", "head", "armL", "armR", "pauldron"]
    owner = {}
    for k in order:
        mp = parts[k].load()
        for y in range(H):
            for x in range(W):
                if mp[x, y] > 127:
                    owner[x, y] = k
    hf = heightfield(parts)
    hp = hf.load()
    brush = Fbm(311, 3, 26, 3)        # 가로로 늘인 붓 결
    brush2 = Fbm(312, 20, 4, 3)       # 세로 결(팔)
    fine = Noise(313, 220, 160)
    lumv, warmv = {}, {}
    for (x, y), k in owner.items():
        if k == "pauldron":
            continue
        gx = (hp[min(W - 1, x + 1), y] - hp[max(0, x - 1), y]) / 255.0
        gy = (hp[x, min(H - 1, y + 1)] - hp[x, max(0, y - 1)]) / 255.0
        n = nrm((-gx * 11.0, -gy * 11.0, 1.0))
        if k.startswith("arm") and y > 196:
            n = arm_normal(k, x, y, n)
        df = max(0.0, n[0] * LF[0] + n[1] * LF[1] + n[2] * LF[2])
        dm = max(0.0, n[0] * LM[0] + n[1] * LM[1] + n[2] * LM[2])
        fall = max(0.0, 1.2 - x / 400.0)                         # 불은 왼쪽에서
        fire = df * fall
        moon = dm
        front = n[2]
        j = (brush2.at(x / W, y / H) if k.startswith("arm") else brush.at(x / W, y / H)) - 0.5
        j = j * 1.4 + (fine.at(x / W, y / H) - 0.5) * 0.3
        v = -0.6 + 2.2 * front + 3.8 * fire + 2.6 * moon + j * 0.9 - (y - 150) / 280.0
        if k == "head":
            v -= 0.2 + max(0.0, (y - 62) / 34.0) * 1.6
            dmn = math.hypot(x - 352, y - 30)
            if dmn < 40 and moon > 0.45:
                v += 1.2
        lumv[x, y] = v
        warmv[x, y] = fire - moon * 0.45 + j * 0.06 + max(0.0, 0.3 - x / 1100.0) > 0.30
    sh = painted_values()
    shp = sh.load()
    for (x, y), v in lumv.items():
        v += shp[x, y]
        i = max(1, min(8, int(round(v))))
        px[x, y] = (*(WARMB if warmv[x, y] else GRAYL)[i], 255)
    # 겹친 부위 경계 먹선(앞 부위 가장자리)
    for k in ("armL", "armR", "head"):
        e = edges(parts[k])
        for side in ("l", "r", "t", "b"):
            for (x, y) in e[side]:
                nx, ny = {"l": (x - 1, y), "r": (x + 1, y), "t": (x, y - 1), "b": (x, y + 1)}[side]
                if owner.get((nx, ny)) == "torso":
                    px[x, y] = (*G[1], 255)
    draw_pauldron(im, parts, owner, emis)
    draw_details(im, parts, owner, emis)
    rim(im, parts, owner)
    return owner, parts


def draw_pauldron(im, parts, owner, emis):
    px = im.load()
    mp = parts["pauldron"]
    hf = mp.filter(ImageFilter.GaussianBlur(7)).load()
    br = Fbm(321, 10, 10, 2)
    for (x, y), k in owner.items():
        if k != "pauldron":
            continue
        gx = (hf[min(W - 1, x + 1), y] - hf[max(0, x - 1), y]) / 255.0
        gy = (hf[x, min(H - 1, y + 1)] - hf[x, max(0, y - 1)]) / 255.0
        n = nrm((-gx * 6, -gy * 6, 1))
        df = max(0.0, n[0] * LF[0] + n[1] * LF[1] + n[2] * LF[2])
        dm = max(0.0, n[0] * LM[0] + n[1] * LM[1] + n[2] * LM[2])
        j = (br.at(x / W, y / H) - 0.5) * 0.8
        v = 2.4 + 3.4 * df + 3.0 * dm + j
        i = max(2, min(9, int(round(v))))
        c = GRAYL[i]
        if df > dm * 1.5 and v > 4.6:
            c = WARML[i]
        px[x, y] = (*c, 255)
    d = ImageDraw.Draw(im)
    # 두 겹 판 경계 · 리벳 · 녹
    d.line([(120, 182), (146, 172), (176, 164), (204, 152)], fill=(*G[2], 255), width=2)
    d.line([(121, 180), (147, 170), (177, 162), (205, 150)], fill=(*G[7], 255))
    d.line([(126, 160), (150, 148), (180, 140), (206, 140)], fill=(*G[2], 255))
    for (x, y) in ((134, 152), (158, 140), (186, 136), (130, 178), (160, 170), (190, 160)):
        d.point((x, y), fill=(*G[9], 255))
        d.point((x + 1, y + 1), fill=(*G[2], 255))
    r = random.Random(322)
    for _ in range(40):
        x, y = r.randint(118, 210), r.randint(132, 196)
        if owner.get((x, y)) == "pauldron":
            px[x, y] = (*(A[1] if r.random() < 0.6 else A[2]), 255)
    # 바깥 테 먹선
    e = edges(mp)
    for side in ("l", "r", "t", "b"):
        for (x, y) in e[side]:
            px[x, y] = (*G[1], 255)
    # 혼불(견갑 위, 바람에 오른쪽으로 기움) — 혀 세 갈래
    flame(im, emis, 166, 134, 60, 8, 324)


def flame(im, emis, fx, fy, hgt, wid, seed):
    """혀 셋(가운데 길게 · 양옆 짧게)이 따로 끝나는 불꽃. 바람에 오른쪽으로 휨."""
    px = im.load()
    fb = Fbm(seed, 6, 14, 2)
    tongues = [(0.0, 1.0, 1.0, 0.0), (-0.95, 0.58, 0.62, 1.9), (0.9, 0.72, 0.6, 3.3)]   # 옆 위치 · 높이 · 굵기 · 위상
    for y in range(fy - hgt - 2, fy + 3):
        h = (fy - y) / hgt
        for x in range(fx - wid * 3, fx + wid * 3 + 22):
            best = 9.0
            core = 9.0
            for off, sh, sw, ph in tongues:
                if h > sh or h < -0.05:
                    continue
                hh = max(0.0, h) / sh
                cx = fx + off * wid * (1 - hh * 0.6) + math.sin(hh * 5.0 + ph) * 2.6 * hh + hh * hh * 13.0 * sh
                w = wid * sw * (1 - hh) ** 0.85 * (0.7 + 0.3 * math.sin(min(1.0, hh * 2.0 + 0.25) * math.pi / 2)) + 0.5
                dd = abs(x - cx) / w
                best = min(best, dd)
                core = min(core, dd + hh * 0.8)
            n = fb.at(x / W * 6, y / H * 2.5)
            if best + (0.5 - n) * 0.55 > 1.0:
                continue
            c = A[11] if core < 0.45 else (A[9] if core < 0.75 else (A[7] if best < 0.75 else A[5]))
            px[x, y] = (*c, 255)
            emis.putpixel((x, y), (*A[8], 255))


ARROWS = [((436, 176), (474, 118)), ((458, 198), (508, 156)), ((424, 204), (446, 150)), ((214, 262), (176, 214))]


def draw_details(im, parts, owner, emis):
    px = im.load()
    d = ImageDraw.Draw(im)
    r = random.Random(331)
    # 척추 · 견갑 아래 · 광배 결(먹 붓 선, 빛 쪽에 한 줄 밝게)
    for pts, c, hi in (                       ([(230, 194), (262, 212), (298, 206)], G[2], G[5]),
                       ([(410, 194), (378, 212), (342, 206)], G[2], G[5]),
                       ([(206, 236), (222, 280), (230, 330)], G[2], None),
                       ([(434, 236), (418, 280), (410, 330)], G[2], None),
                       ([(196, 214), (203, 236)], G[1], None), ([(444, 214), (437, 236)], G[1], None)):
        d.line(pts, fill=(*c, 255))
        if hi:
            d.line([(x - 1, y) for x, y in pts], fill=(*hi, 255))
    # 오래된 흉터(하얗게 아문 금) — 획 자리 밖, 어깨·팔에만
    for (x0, y0, x1, y1) in ((372, 148, 392, 160), (408, 166, 420, 186), (236, 150, 250, 142), (480, 230, 492, 252),
                             (150, 232, 160, 252), (462, 262, 470, 280)):
        d.line([(x0, y0), (x1, y1)], fill=(*G[8], 255))
        d.line([(x0, y0 + 1), (x1, y1 + 1)], fill=(*G[3], 255))
    # 재 껍질 부스러기(밝은 점·어두운 점)
    for _ in range(420):
        x, y = r.randint(170, 470), r.randint(110, 359)
        if owner.get((x, y)) in ("torso", "armL", "armR", "neck"):
            sx, sy, sw, sh = STROKE
            inside = sx + 6 < x < sx + sw - 6 and sy + 6 < y < sy + sh - 6
            if inside and r.random() < 0.65:
                continue
            cur = px[x, y][:3]
            if cur in GRAYL:
                i = GRAYL.index(cur)
                px[x, y] = (*GRAYL[max(1, min(9, i + (1 if r.random() < 0.5 else -1)))], 255)
    # 붕대(두 팔뚝 아래쪽) — 원통을 감은 띠: 가운데가 처진 호, 간격·기울기 들쭉날쭉, 빛 쪽 밝게
    for k in ("armL", "armR"):
        (x0, y0), (x1, y1), w0, w1, sx = ARM[k]
        yb = 262
        rr = random.Random(341 if sx < 0 else 342)
        while yb < 366:
            th = rr.randint(4, 6)
            tilt = rr.uniform(-0.12, 0.12) + 0.10 * sx
            t = (yb - y0) / (y1 - y0)
            cx = x0 + (x1 - x0) * t
            hw = w0 + (w1 - w0) * t + 1
            for xx in range(int(cx - hw), int(cx + hw) + 1):
                u = (xx - cx) / hw
                if abs(u) > 1:
                    continue
                yc = yb + 3.0 * (1 - u * u) + tilt * (xx - cx)
                lit = -u * 0.8 + 0.3 if sx < 0 else u * 0.35 + 0.1
                for dy in range(th):
                    p = (xx, int(round(yc)) + dy)
                    if owner.get(p) != k:
                        continue
                    edge = dy == 0
                    low = dy == th - 1
                    base = 7 if edge else (4 if low else 6)
                    vv = base + lit * 2 - abs(u) ** 3 * 2.2
                    i = max(2, min(9, int(round(vv))))
                    c = GRAYL[i]
                    if sx < 0 and u < -0.35 and not low:
                        c = WARMB[min(9, i + 1)] if u > -0.8 else WARML[min(8, i + 1)]
                    px[p] = (*c, 255)
            yb += th + rr.randint(1, 4)
    # 재 껍질 금(검게 탄 살갗의 잔금) — 획 자리 안은 드물게
    rr = random.Random(343)
    sx0, sy0, sw, sh = STROKE
    for _ in range(95):
        x, y = rr.randint(150, 490), rr.randint(110, 356)
        if owner.get((x, y)) not in ("torso", "armL", "armR"):
            continue
        inside = sx0 < x < sx0 + sw and sy0 < y < sy0 + sh
        if inside and rr.random() < 0.8:
            continue
        ang = rr.uniform(0, math.pi)
        pts = [(x, y)]
        for _s in range(rr.randint(2, 4)):
            ang += rr.uniform(-0.9, 0.9)
            L = rr.uniform(3, 8)
            x, y = x + math.cos(ang) * L, y + math.sin(ang) * L
            pts.append((x, y))
        for a, b in zip(pts, pts[1:]):
            d.line([a, b], fill=(*G[2], 255))
            d.line([(a[0], a[1] + 1), (b[0], b[1] + 1)], fill=(*G[6], 255)) if rr.random() < 0.5 else None
        for a, b in zip(pts, pts[1:]):
            d.line([a, b], fill=(*G[2], 255))
    # 머리: 두개골 실금(호박 발광) · 귀 · 분노한 눈(윤곽)
    crack = [(330, 18), (334, 30), (328, 40), (336, 52), (331, 60)]
    d.line(crack, fill=(*A[6], 255), width=2)
    d.line(crack, fill=(*A[10], 255))
    d.line([(334, 30), (344, 34), (348, 30)], fill=(*A[7], 255))
    ed = ImageDraw.Draw(emis)
    ed.line(crack, fill=(*A[8], 255), width=3)
    ex, ey = 281, 69
    for (ox, oy, c) in ((0, 0, A[11]), (-1, 0, A[10]), (1, 0, A[10]), (2, 0, A[9]), (1, -1, A[9]), (2, -1, A[8]), (3, -1, A[7]),
                        (-1, 1, A[6]), (0, 1, A[7])):
        px[ex + ox, ey + oy] = (*c, 255)
    ed.ellipse([ex - 4, ey - 4, ex + 6, ey + 4], fill=(*A[10], 255))
    d.line([(272, 66), (276, 64), (282, 66)], fill=(*G[1], 255))          # 찌푸린 눈썹뼈
    # 부러진 화살(오른어깨 · 왼 광배) — 3도트 화살대 + 깃
    for (a, b) in ARROWS:
        x0, y0 = a
        x1, y1 = b
        d.line([(x0, y0), (x1, y1)], fill=(*G[1], 255), width=3)
        d.line([(x0 - 1, y0), (x1 - 1, y1)], fill=(*A[2], 255))
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        for s_ in (-1, 1):
            for k_ in range(4):
                bx, by = x1 - ux * (2 + k_ * 2.2), y1 - uy * (2 + k_ * 2.2)
                d.line([(bx, by), (bx - ux * 5 + s_ * uy * 5, by - uy * 5 - s_ * ux * 5)],
                       fill=(*(G[7] if s_ < 0 else G[4]), 255))
        # 꺾인 끝(나무 결 쪼개짐)
        d.line([(x1, y1), (x1 + ux * 3 + uy * 2, y1 + uy * 3 - ux * 2)], fill=(*A[2], 255))
        # 박힌 자리: 검은 상처 + 호박 잔불 한 점
        d.ellipse([x0 - 3, y0 - 2, x0 + 3, y0 + 2], fill=(*G[1], 255))
        px[x0 + 1, y0] = (*A[4], 255)


def rim(im, parts, owner):
    """실루엣 테: 왼쪽(불) 호박 · 오른쪽 위(달) 회색. 아래로 갈수록 약하게."""
    px = im.load()
    sil = Image.new("L", (W, H), 0)
    for k in parts:
        sil.paste(255, (0, 0), parts[k])
    bl = sil.filter(ImageFilter.GaussianBlur(2)).load()
    e = edges(sil)
    cand = set(e["l"]) | set(e["t"]) | set(e["r"])
    for (x, y) in cand:
        if y >= H - 1:
            continue
        gx = bl[min(W - 1, x + 1), y] - bl[max(0, x - 1), y]
        gy = bl[x, min(H - 1, y + 1)] - bl[x, max(0, y - 1)]
        L = math.hypot(gx, gy) or 1
        nx, ny = -gx / L, -gy / L
        fire = nx * -0.94 + ny * 0.1
        moon = nx * 0.5 + ny * -0.86
        fall = 1.0 if y < 260 else max(0.3, 1 - (y - 260) / 140)
        if fire * fall > 0.6:
            c = A[7]
        elif fire * fall > 0.32:
            c = A[5]
        elif fire * fall > 0.1:
            c = A[3]
        elif moon > 0.55:
            c = G[9]
        elif moon > 0.2:
            c = G[6]
        else:
            continue
        px[x, y] = (*c, 255)
        if fire * fall > 0.6 and owner.get((x + 1, y)) and owner.get((x + 1, y)) != "pauldron":
            px[x + 1, y] = (*A[4], 255)


def vignette(im):
    """가장자리 한두 단 어둡게(붓 결 경계) — 시선이 등 가운데로."""
    px = im.load()
    fb = Fbm(351, 4, 18, 3)
    darker = {}
    for ramp in (GRAYL, WARML, WARMB):
        for i, c in enumerate(ramp):
            darker.setdefault(c, ramp[max(0, i - 1)])
    darker.setdefault(G[2], G[1])
    for y in range(H):
        for x in range(W):
            dx, dy = (x - 320) / 330.0, (y - 200) / 230.0
            v = dx * dx + dy * dy * 0.8
            j = (fb.at(x / W, y / H) - 0.5) * 0.25
            steps = (1 if v + j > 0.62 else 0) + (1 if v + j > 0.95 else 0)
            c = px[x, y][:3]
            if c in (A[7], A[8], A[9], A[10], A[11]):
                continue
            for _ in range(steps):
                c = darker.get(c, c)
            px[x, y] = (*c, 255)


def draw():
    """반환 (canvas RGBA 640×360 불투명, emis RGBA, parts)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    emis = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_bg(im, emis)
    owner, parts = draw_body(im, emis)
    vignette(im)
    return im, emis, parts
