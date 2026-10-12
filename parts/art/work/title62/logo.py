"""타이틀 로고 — 'LOPAD' + 부제 '바깥의 적' (글꼴 없음, 전부 직접 그린 획). 1200×400 RGBA.

- 글자 = 빛나는 먹 글씨(UI 키트 38라운드 '글씨가 빛나는 느낌'과 같은 결): 몸 A11→A8 호박 금빛, 안쪽 위·왼 빛 G15, 아래·오른 A6,
  1도트 먹 외곽선 G00, 바깥 부드러운 호박 빛무리.
- '이름이 번진다'(59 Q43): 글자 아래 1/4 이 먹물처럼 흘러내려 어두워지며 끊긴다.
- 부제: 붓 획(누름 → 삐침)으로 쓴 한글. 아래에 원한 4종 무기 색 불씨 4개.
논리 400×133(도트 1칸 = 3px)에서 4배 과표본 → 임계 → 도트, 빛무리만 1200 해상도.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

from kit import A, G, WEAPON, Fbm, poly, stroke_poly, up

LW, LH, K = 400, 133, 3
SS = 4                                   # 과표본


def _canvas():
    m = Image.new("L", (LW * SS, LH * SS), 0)
    return m, ImageDraw.Draw(m)


def S(pts, ox, oy, sc=1.0):
    return [((ox + x * sc) * SS, (oy + y * sc) * SS) for x, y in pts]


# ------------------------------------------------------------------ 라틴 대문자(52×64 상자)
def glyph(d, ch, ox, oy):
    def R(x0, y0, x1, y1):
        d.rectangle([(ox + x0) * SS, (oy + y0) * SS, (ox + x1) * SS, (oy + y1) * SS], fill=255)

    def Pg(pts):
        d.polygon(S(pts, ox, oy), fill=255)

    def E(x0, y0, x1, y1, f=255):
        d.ellipse([(ox + x0) * SS, (oy + y0) * SS, (ox + x1) * SS, (oy + y1) * SS], fill=f)

    if ch == "L":
        Pg([(6, 2), (18, 0), (17, 56), (7, 58)])               # 줄기(위가 굵게 눌림)
        Pg([(1, 0), (23, 0), (21, 5), (3, 5)])                 # 윗 세리프
        Pg([(4, 52), (44, 54), (52, 44), (50, 64), (2, 64)])   # 바닥 + 오른 끝 솟은 세리프
    elif ch == "O":
        E(1, 0, 51, 64)
        E(14, 9, 38, 55, 0)
        Pg([(30, -2), (40, -2), (35, 10), (29, 9)])            # 붓 시작 틈(불씨 자리) — 지움
    elif ch == "P":
        Pg([(6, 2), (18, 0), (17, 60), (7, 62)])
        Pg([(1, 0), (24, 0), (24, 5), (3, 5)])
        Pg([(1, 59), (24, 59), (23, 64), (2, 64)])
        E(6, 0, 50, 38)
        E(17, 8, 37, 29, 0)
        R(6, 8, 17, 29)
    elif ch == "A":
        Pg([(20, 0), (32, 0), (52, 64), (38, 64)])             # 오른 다리(굵게)
        Pg([(20, 0), (27, 0), (9, 64), (2, 64)])               # 왼 다리(가늘게)
        Pg([(12, 38), (40, 38), (41, 44), (11, 44)])           # 가로대
        Pg([(-1, 59), (16, 59), (15, 64), (-1, 64)])
        Pg([(34, 59), (54, 59), (54, 64), (35, 64)])
    elif ch == "D":
        Pg([(6, 2), (18, 0), (17, 60), (7, 62)])
        Pg([(1, 0), (24, 0), (24, 5), (3, 5)])
        Pg([(1, 59), (24, 59), (23, 64), (2, 64)])
        E(-14, 0, 51, 64)
        E(-6, 9, 37, 55, 0)
        R(-16, 0, 6, 64)  # 왼쪽 넘친 타원 잘라 냄(아래에서 줄기를 다시 그림)
        d.rectangle([(ox - 16) * SS, (oy) * SS, (ox + 5.9) * SS, (oy + 64) * SS], fill=0)
        Pg([(6, 2), (18, 0), (17, 60), (7, 62)])
        Pg([(1, 0), (24, 0), (24, 5), (3, 5)])
        Pg([(1, 59), (24, 59), (23, 64), (2, 64)])


# ------------------------------------------------------------------ 한글 붓 획(26×26 상자)
def brush(d, pts, ox, oy, sc, w, press=1.3, tail=0.35):
    """붓 획: 첫 점에서 눌러(굵게) 끝에서 빠진다(가늘게). 꺾임은 점 목록으로."""
    P = [((ox + x * sc), (oy + y * sc)) for x, y in pts]
    segs = list(zip(P, P[1:]))
    tot = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs) or 1
    acc = 0.0
    for a, b in segs:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        t0, t1 = acc / tot, (acc + L) / tot
        w0 = w * (press - (press - 1) * min(1, t0 * 4)) * (1 - (1 - tail) * max(0, (t0 - 0.7) / 0.3))
        w1 = w * (press - (press - 1) * min(1, t1 * 4)) * (1 - (1 - tail) * max(0, (t1 - 0.7) / 0.3))
        d.polygon([(x * SS, y * SS) for x, y in stroke_poly(a, b, w0, w1)], fill=255)
        for (x, y), ww in ((a, w0), (b, w1)):
            r = ww / 2 * SS
            d.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], fill=255)
        acc += L
    # 붓머리(누름 자국): 첫 점 왼쪽 위로 살짝 돋음
    x, y = P[0]
    r = w * 0.75 * SS
    d.ellipse([x * SS - r, y * SS - r * 1.1, x * SS + r * 0.6, y * SS + r * 0.6], fill=255)


HANGUL = {
    "바": [[(3.5, 4), (3.5, 22.5)], [(11, 3.5), (11, 22.5)], [(3.5, 12.5), (11, 12)], [(3.5, 22.5), (11.5, 22)],
          [(19.5, 1), (19.5, 25.5)], [(19.5, 12.5), (25, 12)]],
    "깥": [[(1.0, 2.0), (7.2, 1.6), (6.0, 9.6)], [(10.0, 2.0), (16.2, 1.6), (15.0, 9.6)], [(21.8, 0.2), (21.8, 12.6)], [(21.8, 6.2), (26.0, 6.0)],
          [(4.0, 15.0), (21.0, 14.6)], [(4.0, 15.0), (4.0, 25.2)], [(4.0, 20.1), (19.4, 19.8)], [(4.0, 25.2), (22.0, 24.8)]],
    "의": [[(21.5, 0.5), (21.5, 25.5)], [(1.5, 20.5), (17.5, 19.8)]],
    "적": [[(2, 3.2), (12.5, 2.6)], [(8, 3), (6, 8.5), (1.5, 13)], [(8.2, 6.5), (13.5, 12.5)], [(20.5, 0.5), (20.5, 15.5)],
          [(15, 7.5), (20.5, 7.2)], [(5, 18.2), (20.5, 17.8), (20.5, 25.5)]],
}


def hangul(d, ch, ox, oy, sc=1.0, w=2.9):
    for st in HANGUL[ch]:
        brush(d, st, ox, oy, sc, w)
    if ch == "의":                                    # ㅇ: 붓으로 한 바퀴(위에서 시작해 왼쪽으로 돌아 닫힘)
        cx, cy, r = 9.2, 9.0, 5.6
        pts = [(cx + r * math.sin(a), cy - r * math.cos(a)) for a in [math.radians(-10 - k * 24) for k in range(16)]]
        brush(d, pts, ox, oy, sc, w * 0.9, press=1.15, tail=0.8)


# ------------------------------------------------------------------ 마스크 → 도트
def to_pixels(m, rough_seed):
    """과표본 마스크 가장자리를 마른 붓처럼 흔든 뒤 논리 해상도 도트로."""
    n = Fbm(rough_seed, 60, 20, 2)
    w, h = m.size
    mp = m.load()
    bl = m.filter(ImageFilter.GaussianBlur(SS * 0.7)).load()
    out = Image.new("L", (LW, LH), 0)
    op = out.load()
    for y in range(LH):
        for x in range(LW):
            s = 0
            for dy in range(SS):
                for dx in range(SS):
                    s += bl[x * SS + dx, y * SS + dy]
            v = s / (SS * SS * 255)
            thr = 0.5 + (n.at(x / LW, y / LH) - 0.5) * 0.5
            if v > thr:
                op[x, y] = 255
    return out


def bleed(mask, seed):
    """글자 아래쪽에서 먹이 번진다: 가는 흘림 몇 줄(1도트, 짧게) — 고드름처럼 보이지 않게 드물게."""
    r = random.Random(seed)
    mp = mask.load()
    w, h = mask.size
    for x in range(w):
        ys = [y for y in range(h) if mp[x, y] > 127]
        if not ys or r.random() > 0.06:
            continue
        y1 = max(ys)
        ln = r.randint(3, 9)
        for k in range(1, ln + 1):
            if y1 + k < h and (k < ln - 2 or r.random() < 0.5):
                mp[x, y1 + k] = 255
    return mask


def letter_colors(mask, top, bottom, body=(A[11], A[10], A[9], A[8]), bleed_ramp=(A[6], A[4], A[3], A[2]), cut=0.72, seed=7):
    """마스크 → RGBA 도트: 세로 그라데이션 몸(경계는 잡음으로 흔들림) + 빛 테 + 아래 번짐(어두워지며 바스러짐)."""
    w, h = mask.size
    mp = mask.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    op = out.load()
    jn = Fbm(seed, 50, 18, 3)
    dn_ = Fbm(seed + 1, 90, 40, 2)
    for y in range(h):
        for x in range(w):
            if mp[x, y] < 128:
                continue
            j = (jn.at(x / w, y / h) - 0.5) * 0.22
            t = (y - top) / max(1, bottom - top) + j
            if t <= cut:
                c = body[max(0, min(len(body) - 1, int(t / cut * len(body))))]
            else:
                u = (t - cut) / (1 - cut + 0.3)
                i = max(0, min(len(bleed_ramp) - 1, int(u * len(bleed_ramp))))
                c = bleed_ramp[i]
                if dn_.at(x / w, y / h) < 0.18 + u * 0.55:     # 번짐: 아래로 갈수록 바스러져 빈다
                    continue
            up_ = y > 0 and mp[x, y - 1] < 128
            lf = x > 0 and mp[x - 1, y] < 128
            dn = y < h - 1 and mp[x, y + 1] < 128
            rt = x < w - 1 and mp[x + 1, y] < 128
            if t <= cut:
                if up_ or lf:
                    c = G[15] if t < 0.3 else A[11]
                elif dn or rt:
                    c = A[6]
            op[x, y] = (*c, 255)
    return out


def ink_outline(rgba, col=G[0]):
    a = rgba.split()[3]
    grown = a.filter(ImageFilter.MaxFilter(3))
    base = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    base.paste(Image.new("RGBA", rgba.size, (*col, 255)), (0, 0), grown)
    base.alpha_composite(rgba)
    return base


def cracks(img, segs, col=A[3]):
    d = ImageDraw.Draw(img)
    px = img.load()
    for pts in segs:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for i in range(n + 1):
                x = round(x0 + (x1 - x0) * i / n)
                y = round(y0 + (y1 - y0) * i / n)
                if px[x, y][3] and px[x, y][:3] != G[0]:
                    px[x, y] = (*col, 255)


def glow(img_big, color, radius, alpha):
    a = img_big.split()[3].filter(ImageFilter.GaussianBlur(radius))
    a = a.point(lambda v: int(min(255, v * alpha)))
    g = Image.new("RGBA", img_big.size, (*color, 0))
    g.putalpha(a)
    return g


LAYOUT = {
    "letters": {"x": 54, "y": 8, "advance": 60, "box": [52, 64]},
    "subtitle": {"x": 133, "y": 95, "advance": 30, "space": 12, "box": [26, 26]},
}


def draw_logo():
    # 1) LOPAD
    m, d = _canvas()
    L = LAYOUT["letters"]
    for i, ch in enumerate("LOPAD"):
        glyph(d, ch, L["x"] + i * L["advance"], L["y"])
    lm = to_pixels(m, 501)
    lm = bleed(lm, 502)
    letters = letter_colors(lm, L["y"], L["y"] + 64)
    # 균열(O·A·D 에 한 줄씩, 먹빛)
    ox = L["x"]
    cracks(letters, [
        [(ox + 60 + 6, L["y"] + 26), (ox + 60 + 10, L["y"] + 31), (ox + 60 + 8, L["y"] + 36), (ox + 60 + 12, L["y"] + 41)],
        [(ox + 180 + 40, L["y"] + 46), (ox + 180 + 43, L["y"] + 52), (ox + 180 + 41, L["y"] + 56)],
        [(ox + 240 + 41, L["y"] + 14), (ox + 240 + 44, L["y"] + 20), (ox + 240 + 42, L["y"] + 25), (ox + 240 + 45, L["y"] + 29)],
    ])
    letters = ink_outline(letters)
    # O 의 틈에 불씨 하나(혼불)
    lp = letters.load()
    ex, ey = ox + 60 + 34, L["y"] + 2
    for (dx, dy, c) in ((0, 0, A[11]), (1, 0, A[10]), (0, 1, A[9]), (1, 1, A[8]), (0, -1, A[9]), (-1, 0, A[7]), (1, -2, A[6]), (2, 1, A[6])):
        lp[ex + dx, ey + dy] = (*c, 255)
    # 2) 부제 '바깥의 적'
    m2, d2 = _canvas()
    Sb = LAYOUT["subtitle"]
    x = Sb["x"]
    for ch in "바깥의 적":
        if ch == " ":
            x += Sb["space"]
            continue
        hangul(d2, ch, x, Sb["y"])
        x += Sb["advance"]
    sub_right = x - (Sb["advance"] - Sb["box"][0])
    # 양옆 붓 줄(먹선 위 금빛)
    brush(d2, [(Sb["x"] - 40, Sb["y"] + 13.5), (Sb["x"] - 10, Sb["y"] + 12.6)], 0, 0, 1, 2.2, press=1.4, tail=0.2)
    brush(d2, [(sub_right + 10, Sb["y"] + 12.6), (sub_right + 40, Sb["y"] + 13.5)], 0, 0, 1, 2.2, press=1.4, tail=0.2)
    sm = to_pixels(m2, 503)
    sub = letter_colors(sm, Sb["y"], Sb["y"] + 26, body=(G[14], G[13], G[13], G[12]), bleed_ramp=(G[11], G[9]), cut=1.0)
    sub = ink_outline(sub)
    # 3) 원한 4종 불씨(칼 · 대검 · 단검 · 활) — 부제 아래 가운데
    embers = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    ep = embers.load()
    cx = (Sb["x"] + sub_right) // 2
    order = ["katana", "greatsword", "dagger", "bow"]
    ember_pos = []
    for i, k in enumerate(order):
        x0 = cx - 27 + i * 18
        y0 = Sb["y"] + 33
        c = WEAPON[k]
        hi = tuple(min(255, int(v + (255 - v) * 0.6)) for v in c)
        dk = tuple(int(v * 0.55) for v in c)
        for (dx, dy, col) in ((0, 0, hi), (1, 0, hi), (-1, 0, c), (2, 0, c), (0, 1, c), (1, 1, c), (0, -1, c), (1, -1, hi),
                              (1, -2, c), (1, -3, dk), (0, -2, dk), (2, -1, dk), (0, 2, dk), (1, 2, dk)):
            ep[x0 + dx, y0 + dy] = (*col, 255)
        ember_pos.append((k, x0, y0))
    embers = ink_outline(embers)
    # 4) 합치기 + 빛무리(1200 해상도)
    pix = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
    pix.alpha_composite(sub)
    pix.alpha_composite(letters)
    pix.alpha_composite(embers)
    big = up(pix, K)
    out = Image.new("RGBA", big.size, (0, 0, 0, 0))
    lb = up(letters, K)
    out.alpha_composite(glow(lb, A[6], 22, 0.55))
    out.alpha_composite(glow(lb, A[8], 7, 0.45))
    out.alpha_composite(glow(up(sub, K), A[7], 10, 0.35))
    for k, x0, y0 in ember_pos:
        e = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
        e.putpixel((x0, y0), (255, 255, 255, 255))
        e.putpixel((x0 + 1, y0 + 1), (255, 255, 255, 255))
        out.alpha_composite(glow(up(e, K), WEAPON[k], 9, 2.2))
    out.alpha_composite(big)
    meta = {
        "lettersBox": [L["x"] * K, L["y"] * K, (L["x"] + 4 * L["advance"] + 52) * K, (L["y"] + 64 + 16) * K],
        "subtitleBox": [(Sb["x"] - 40) * K, Sb["y"] * K, (sub_right + 40) * K, (Sb["y"] + 26) * K],
        "emberDots": {k: [x0 * K + K, y0 * K + K] for k, x0, y0 in ember_pos},
    }
    return out, meta
