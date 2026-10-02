"""Gemini 원본 → LOPAD 팔레트 도트 보정 도구 (Pillow 만, numpy 없음).

단계: 자르기 → 1/k 축소(LANCZOS) → 색 보정(명도 곡선·대비·채도) → Lab 최근접 감색(팔레트 고정)
      → 외톨이 점 제거 → (선택) 좌우 이음 보정 → k 배 최근접 확대.
"""
import json, math, os
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
PAL = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))
GRAY = PAL["gray"]
RAMP1 = PAL["floors"][0]["ramp"]          # 1층 '잔' 호박 램프 (슬롯 16~27)
SEPIA = PAL["ui"]["ramp"]                 # UI 세피아 S0~S5


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb2lab(rgb):
    r, g, b = (_lin(v) for v in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = (0.2126 * r + 0.7152 * g + 0.0722 * b)
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def palette(names):
    """names: 'G0-15', 'R16-27'(층 램프 슬롯 번호), 'S0-5'. 반환 [(slotname, rgb)]."""
    out = []
    for n in names:
        kind, rng = n[0], n[1:]
        a, b = (int(v) for v in rng.split("-")) if "-" in rng else (int(rng), int(rng))
        for i in range(a, b + 1):
            if kind == "G":
                out.append((f"G{i:02d}", hex2rgb(GRAY[i])))
            elif kind == "R":
                out.append((f"A{i}", hex2rgb(RAMP1[i - 16])))
            elif kind == "S":
                out.append((f"S{i}", hex2rgb(SEPIA[i])))
    return out


def _curve(pts, v):
    """명도 곡선: [(in, out), ...] 구간 선형."""
    for (a, b), (c, d) in zip(pts, pts[1:]):
        if v <= c:
            return b + (d - b) * (v - a) / max(1e-6, c - a)
    return pts[-1][1]


def grade(im, gamma=1.0, lift=0.0, gain=1.0, sat=1.0, warm_keep=0.0, curve=None):
    """명도 곡선 + 채도. warm_keep>0 이면 따뜻한 색(호박)만 채도를 남기고 나머지는 회색으로."""
    px = im.load()
    w, h = im.size
    out = Image.new("RGB", im.size)
    po = out.load()
    cache = {}
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            r = cache.get(c)
            if r is None:
                R, G, B = (v / 255 for v in c)
                L = 0.299 * R + 0.587 * G + 0.114 * B
                L2 = max(0.0, min(1.0, lift + gain * (L ** gamma)))
                if curve:
                    L2 = _curve(curve, L)
                # 채도 처리
                mx, mn = max(R, G, B), min(R, G, B)
                s = sat
                if warm_keep > 0:
                    warm = (R - B) > 0.06 and R >= G   # 호박 계열
                    s = sat if warm else sat * (1 - warm_keep)
                rr = [L + (v - L) * s for v in (R, G, B)]
                k = (L2 / L) if L > 1e-4 else 0
                rr = [max(0, min(1, v * k)) if L > 1e-4 else L2 for v in rr]
                r = tuple(int(round(v * 255)) for v in rr)
                cache[c] = r
            po[x, y] = r
    return out


def quantize(im, pal, chroma_w=1.0, light_w=1.0):
    """Lab 최근접(채도 가중) 감색. 반환 P 모드 이미지(팔레트 순서 = pal)."""
    labs = [rgb2lab(c) for _, c in pal]
    px = im.load()
    w, h = im.size
    out = Image.new("P", im.size)
    flat = []
    for _, c in pal:
        flat += list(c)
    out.putpalette(flat + [0] * (768 - len(flat)))
    po = out.load()
    cache = {}
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            key = (c[0] >> 2, c[1] >> 2, c[2] >> 2)
            i = cache.get(key)
            if i is None:
                L, A, B = rgb2lab(c)
                best, bi = 1e18, 0
                for j, (l2, a2, b2) in enumerate(labs):
                    d = light_w * (L - l2) ** 2 + chroma_w * ((A - a2) ** 2 + (B - b2) ** 2)
                    if d < best:
                        best, bi = d, j
                i = cache[key] = bi
            po[x, y] = i
    return out


def despeckle(p, passes=1, wrap_x=False):
    """4방향 이웃 중 같은 색이 하나도 없는 외톨이 점을 8이웃 최빈값으로."""
    w, h = p.size
    for _ in range(passes):
        src = p.copy()
        s = src.load()
        d = p.load()
        for y in range(h):
            for x in range(w):
                c = s[x, y]
                nb4, nb8 = [], []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        xx, yy = x + dx, y + dy
                        if wrap_x:
                            xx %= w
                        if 0 <= xx < w and 0 <= yy < h:
                            v = s[xx, yy]
                            nb8.append(v)
                            if dx == 0 or dy == 0:
                                nb4.append(v)
                if c not in nb4 and nb8:
                    d[x, y] = max(set(nb8), key=nb8.count)
    return p


def quilt_wrap(im, overlap):
    """좌우 반복 이음새 제거: 오른쪽 끝 overlap 열과 왼쪽 첫 overlap 열을 최소 오차 세로 경로로 잘라 붙인다.
    반환 폭 = W - overlap. 결과를 가로로 이어 붙이면 이음새가 없다."""
    w, h = im.size
    px = im.load()
    A = [[px[w - overlap + x, y] for x in range(overlap)] for y in range(h)]
    Bm = [[px[x, y] for x in range(overlap)] for y in range(h)]
    lo, hi = 2, overlap - 3
    def err(y, x):
        a, b = A[y][x], Bm[y][x]
        return sum((a[i] - b[i]) ** 2 for i in range(3))
    INF = 1e18
    cost = [[INF] * overlap for _ in range(h)]
    back = [[0] * overlap for _ in range(h)]
    for x in range(lo, hi + 1):
        cost[0][x] = err(0, x)
    for y in range(1, h):
        for x in range(lo, hi + 1):
            best, bx = INF, x
            for dx in (-1, 0, 1):
                xx = x + dx
                if lo <= xx <= hi and cost[y - 1][xx] < best:
                    best, bx = cost[y - 1][xx], xx
            cost[y][x] = best + err(y, x)
            back[y][x] = bx
    x = min(range(lo, hi + 1), key=lambda k: cost[h - 1][k])
    path = [0] * h
    for y in range(h - 1, -1, -1):
        path[y] = x
        x = back[y][x]
    out = Image.new(im.mode, (w - overlap, h))
    out.paste(im.crop((overlap, 0, w - overlap, h)), (overlap, 0))
    po = out.load()
    for y in range(h):
        for x in range(overlap):
            po[x, y] = A[y][x] if x < path[y] else Bm[y][x]
    return out, path


def seam_error(im):
    """좌우 반복 경계(마지막 열 ↔ 첫 열) 평균 차 vs 내부 인접 열 평균 차."""
    w, h = im.size
    px = im.convert("RGB").load()
    def coldiff(a, b):
        return sum(sum(abs(px[a, y][i] - px[b, y][i]) for i in range(3)) for y in range(h)) / h
    inner = sum(coldiff(x, x + 1) for x in range(0, w - 1, max(1, w // 64))) / len(range(0, w - 1, max(1, w // 64)))
    return coldiff(w - 1, 0), inner


def upscale(p, k):
    return p.resize((p.size[0] * k, p.size[1] * k), Image.NEAREST)


def fit_crop(im, w, h, anchor_y=0.5, anchor_x=0.5):
    """비율 맞춰 축소 후 (w,h) 로 자르기."""
    sw, sh = im.size
    s = max(w / sw, h / sh)
    nw, nh = max(w, round(sw * s)), max(h, round(sh * s))
    r = im.resize((nw, nh), Image.LANCZOS)
    x0 = round((nw - w) * anchor_x)
    y0 = round((nh - h) * anchor_y)
    return r.crop((x0, y0, x0 + w, y0 + h))


def stats(p, pal):
    hist = p.histogram()[:len(pal)]
    tot = sum(hist)
    return {pal[i][0]: round(100 * hist[i] / tot, 2) for i in range(len(pal)) if hist[i]}


def despeckle_soft(p, pal, max_size=4, max_dl=10.0, wrap_x=False):
    """작은 덩어리(4연결, max_size 이하) 중 주변 최빈색과 명도 차가 작은 것(=저대비 잡점)만 지운다.
    고대비 점(잔불·불씨·창끝)은 남긴다."""
    w, h = p.size
    px = p.load()
    Ls = [rgb2lab(c)[0] for _, c in pal]
    seen = bytearray(w * h)
    changes = 0
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0 * w + x0]:
                continue
            c = px[x0, y0]
            comp, stack = [], [(x0, y0)]
            seen[y0 * w + x0] = 1
            big = False
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                if len(comp) > max_size:
                    big = True
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if wrap_x:
                        xx %= w
                    if 0 <= xx < w and 0 <= yy < h and not seen[yy * w + xx] and px[xx, yy] == c:
                        seen[yy * w + xx] = 1
                        stack.append((xx, yy))
            if big:
                continue
            cs = set(comp)
            border = []
            for x, y in comp:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if wrap_x:
                        xx %= w
                    if 0 <= xx < w and 0 <= yy < h and (xx, yy) not in cs:
                        border.append(px[xx, yy])
            if not border:
                continue
            m = max(set(border), key=border.count)
            if abs(Ls[m] - Ls[c]) <= max_dl:
                for x, y in comp:
                    px[x, y] = m
                changes += 1
    return changes


# ---------------------------------------------------------------------------
# 톤 맞춤 (49라운드 방향 변경: 키아트는 도트화·감색 없이 고해상도 그대로, 색조만 LOPAD 팔레트에 맞춘다)
# 각 픽셀의 Lab 명도는 유지(또는 곡선), 색(a,b)만 '무채 축 ↔ 층 램프 곡선' 사이로 끌어당긴다.
# 호박색과 방향이 맞는 채도만 램프 쪽으로 남고, 그 밖의 색상(파랑·초록·보라)은 무채(또는 세피아) 축으로 간다.

def lab2rgb(lab):
    L, A, B = lab
    fy = (L + 16) / 116
    fx = fy + A / 500
    fz = fy - B / 200

    def finv(t):
        return t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    x, y, z = finv(fx) * 0.95047, finv(fy), finv(fz) * 1.08883
    r = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g = -0.9689 * x + 1.8758 * y + 0.0415 * z
    b = 0.0557 * x - 0.2040 * y + 1.0570 * z

    def enc(c):
        c = max(0.0, min(1.0, c))
        return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return tuple(int(round(enc(c) * 255)) for c in (r, g, b))


def _axis(colors):
    """색 목록 → L 오름차순 (L, a, b) 표."""
    return sorted(rgb2lab(hex2rgb(c) if isinstance(c, str) else c) for c in colors)


def _interp_ab(axis, L):
    if L <= axis[0][0]:
        return axis[0][1], axis[0][2]
    for (l0, a0, b0), (l1, a1, b1) in zip(axis, axis[1:]):
        if L <= l1:
            t = (L - l0) / max(1e-6, l1 - l0)
            return a0 + (a1 - a0) * t, b0 + (b1 - b0) * t
    return axis[-1][1], axis[-1][2]


def tone_match(im, neutral, accent, accent_gain=1.0, neutral_keep=0.0, L_range=None):
    """neutral: 무채 축 색 목록(gray 또는 sepia), accent: 층 램프 색 목록.
    accent_gain: 호박 방향 채도 배율, neutral_keep: 호박이 아닌 색의 남길 비율(0 = 완전히 축으로).
    L_range: (lo, hi) 이면 L* 를 이 범위로 선형 압축."""
    nax, aax = _axis(neutral), _axis(accent)
    px = im.load()
    w, h = im.size
    out = Image.new("RGB", im.size)
    po = out.load()
    cache = {}
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            key = (c[0] >> 1, c[1] >> 1, c[2] >> 1)
            r = cache.get(key)
            if r is None:
                L, A, B = rgb2lab(c)
                if L_range:
                    L = L_range[0] + (L_range[1] - L_range[0]) * L / 100.0
                na, nb = _interp_ab(nax, L)
                ra, rb = _interp_ab(aax, L)
                # 램프 방향(무채 축 기준)
                da, db = ra - na, rb - nb
                rc = math.hypot(da, db) or 1e-6
                pa, pb = A - na, B - nb
                proj = (pa * da + pb * db) / rc          # 램프 방향 성분
                t = max(0.0, min(1.0, accent_gain * proj / rc))
                # 램프 방향과 수직인 성분(다른 색상)은 neutral_keep 만큼만
                oa = pa - proj * da / rc if proj > 0 else pa
                ob = pb - proj * db / rc if proj > 0 else pb
                a2 = na + t * da + neutral_keep * oa
                b2 = nb + t * db + neutral_keep * ob
                r = cache[key] = lab2rgb((L, a2, b2))
            po[x, y] = r
    return out


def erase_dashes(im, band_min=0.30, drop=0.06, box=6, med=7):
    """밝은 길 띠 안의 가는 어두운 점선만 지운다(주변 평균이 band_min 이상이고 그보다 drop 이상 어두운 픽셀 → 중앙값).
    UI 가 노드 연결선을 따로 그리므로 지도 자체의 점선과 겹치지 않게."""
    from PIL import ImageChops
    L = im.convert("L")
    blur = L.filter(ImageFilter.BoxBlur(box))
    medi = im.filter(ImageFilter.MedianFilter(med))
    lp, bp = L.load(), blur.load()
    w, h = im.size
    mask = Image.new("L", im.size, 0)
    mp = mask.load()
    for y in range(h):
        for x in range(w):
            b = bp[x, y] / 255
            if b >= band_min and (bp[x, y] - lp[x, y]) / 255 >= drop:
                mp[x, y] = 255
    mask = mask.filter(ImageFilter.MaxFilter(3))
    return Image.composite(medi, im, mask), mask
