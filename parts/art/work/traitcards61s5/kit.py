"""카드 도트 변환 도구 — 마젠타 키 → 잘라 맞춤 → 128 축소 → 등급 → LOPAD 팔레트 양자화 → 외톨이 정리 → 외곽선.
Pillow 만(numpy 없음). gemini/gkit.py 의 Lab 함수만 가져다 씀(읽기 전용).
"""
import json, math, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.append(os.path.join(ROOT, "parts/art/work/gemini"))
from gkit import rgb2lab, hex2rgb  # noqa

PAL = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))
V2 = json.load(open(os.path.join(ROOT, "parts/art/work/v2_outer/palette_v2_proposal.json"), encoding="utf-8"))["blocks"]

SIZE = 128

# 카드 팔레트(이름 → hex). 새 색은 요청 노트 §0 색 규칙의 사슬 적갈·묶음 청회·달 청백 3 + 적갈 그늘 2 + 청회 그늘 1.
NAMED = {}
for i, h in enumerate(PAL["gray"]):
    NAMED[f"G{i:02d}"] = h
for i, h in enumerate(PAL["floors"][0]["ramp"]):
    NAMED[f"A{16 + i}"] = h
for blk in ("SL", "WD", "PL"):
    for i, h in enumerate(V2[blk]):
        NAMED[f"{blk}{i}"] = h
NAMED["X1"] = PAL["fx"]["core"][1]
SPECIAL = {"R0": "#3a1719", "R1": "#6e2a2c", "R2": "#b04848",      # 낙인·피 (요청 §0 사슬 끌림 적갈 #b04848)
           "C0": "#5a6a8a", "C1": "#9ab0d8",                     # 묶음·사슬 청회 (#9ab0d8)
           "M0": "#c8d8f0"}                                      # 달 청백 (#c8d8f0)
NAMED.update(SPECIAL)

BASE = [k for k in NAMED if k[0] in "GA" or k[:2] in ("SL", "WD", "PL") or k == "X1"]
ALLOW = {
    "katana": BASE + ["R0", "R1", "R2", "C0", "C1", "M0"],
    "greatsword": BASE + ["R0", "R1", "R2"],
    "dagger": BASE + ["R0", "R1", "R2"],
    "bow": BASE + ["C0", "C1", "M0"],
}


def key_magenta(im, lo=40, hi=110):
    """마젠타 정도 k = min(r,b) - g. k>=hi → 투명, k<=lo → 불투명, 사이는 반투명 + 색 번짐 제거."""
    im = im.convert("RGB")
    w, h = im.size
    src = im.load()
    out = Image.new("RGBA", (w, h))
    po = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b = src[x, y]
            k = min(r, b) - g
            if k >= hi:
                po[x, y] = (0, 0, 0, 0)
                continue
            a = 255 if k <= lo else int(255 * (hi - k) / (hi - lo))
            if k > 0:  # 번짐 제거: r·b 를 g 쪽으로
                m = max(g, min(r, b) - k)
                r, b = min(r, m + max(0, r - b)), min(b, m)
            po[x, y] = (r, g, b, a)
    return out


def drop_small(im, min_px=60):
    """작은 떨어진 조각(마젠타 키 찌꺼기) 제거 — 알파>0 연결 요소."""
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0 or seen[y * w + x]:
                continue
            stack, comp = [(x, y)], []
            seen[y * w + x] = 1
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and px[nx, ny][3] > 0:
                        seen[ny * w + nx] = 1
                        stack.append((nx, ny))
            if len(comp) < min_px:
                for cx, cy in comp:
                    px[cx, cy] = (0, 0, 0, 0)
    return im


def fit(im, size=SIZE, margin=3, crop=None, zoom=1.0, dx=0, dy=0):
    """내용 경계 상자를 정사각 틀에 맞춤(긴 변 = size-2*margin), 프리멀티 축소. crop=(x0,y0,x1,y1) 512 좌표로 먼저 자름."""
    if crop:
        im = im.crop(crop)
    bb = im.getbbox()
    im = im.crop(bb)
    side = max(im.size) / zoom
    tgt = size - 2 * margin
    s = tgt / side
    nw, nh = max(1, round(im.width * s)), max(1, round(im.height * s))
    # 프리멀티 알파로 축소(가장자리 어둡게 번지는 것 방지)
    pm = Image.new("RGBA", im.size)
    a = im.getchannel("A")
    rgb = Image.composite(im.convert("RGB"), Image.new("RGB", im.size), a)
    small_rgb = rgb.resize((nw, nh), Image.LANCZOS)
    small_a = a.resize((nw, nh), Image.LANCZOS)
    sp, sa = small_rgb.load(), small_a.load()
    out = Image.new("RGBA", (size, size))
    po = out.load()
    ox, oy = (size - nw) // 2 + dx, (size - nh) // 2 + dy
    for y in range(nh):
        for x in range(nw):
            al = sa[x, y]
            if al < 110:
                continue
            r, g, b = sp[x, y]
            k = 255 / max(al, 1)
            X, Y = ox + x, oy + y
            if 0 <= X < size and 0 <= Y < size:
                po[X, Y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)), 255)
    return out


def fit_darkpri(im, **kw):
    """fit + 어두운 선 보존: MinFilter(3) 원본을 같은 방식으로 줄인 값이 훨씬 어두운 칸은 그쪽으로 2/3 섞음
    (LANCZOS 만 쓰면 Gemini 그림의 검은 외곽선이 녹아 인물이 바닥에 묻힌다 — 1회차 비평)."""
    from PIL import ImageFilter
    f = fit(im, **kw)
    mn = im.convert("RGB").filter(ImageFilter.MinFilter(3))
    g = fit(Image.merge("RGBA", (*mn.split(), im.getchannel("A"))), **kw)
    fp, gp = f.load(), g.load()
    for y in range(f.height):
        for x in range(f.width):
            a, b = fp[x, y], gp[x, y]
            if a[3] and b[3] and sum(b[:3]) < sum(a[:3]) * 0.55:
                fp[x, y] = tuple((a[i] + b[i] * 2) // 3 for i in range(3)) + (255,)
    return f


def grade(im, contrast=1.12, lift=0.0, sat=1.1, gamma=1.0, gray_gamma=1.0):
    """gray_gamma: 저채도(무채·돌·바닥) 칸만 명도 감마 — 바닥 판이 시선을 뺏지 않게 가라앉힘, 발광색은 그대로."""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            L = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            mx, mn = max(r, g, b), min(r, g, b)
            gg = gray_gamma if (mx - mn) < 0.16 * max(mx, 1) + 6 else 1.0
            L2 = max(0.0, min(1.0, ((L ** (gamma * gg)) - 0.5) * contrast + 0.5 + lift))
            c = [L + (v / 255 - L) * sat for v in (r, g, b)]
            k = L2 / L if L > 1e-4 else 0
            c = [max(0, min(1, v * k)) if L > 1e-4 else L2 for v in c]
            px[x, y] = tuple(int(v * 255 + 0.5) for v in c) + (255,)
    return im


def quantize(im, names, chroma_w=1.6):
    labs = [(n, hex2rgb(NAMED[n]), rgb2lab(hex2rgb(NAMED[n]))) for n in names]
    px = im.load()
    cache = {}
    idx = [[None] * im.width for _ in range(im.height)]
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            key = (r >> 2, g >> 2, b >> 2)
            n = cache.get(key)
            if n is None:
                L, A, B = rgb2lab((r, g, b))
                best = None
                for nm, _, (l2, a2, b2) in labs:
                    d = (L - l2) ** 2 + chroma_w * ((A - a2) ** 2 + (B - b2) ** 2)
                    if best is None or d < best[0]:
                        best = (d, nm)
                n = cache[key] = best[1]
            idx[y][x] = n
    return idx


def despeckle(idx, passes=1):
    """4이웃에 같은 색이 없는 외톨이 점 → 8이웃 최빈 색(투명 포함)."""
    h, w = len(idx), len(idx[0])
    for _ in range(passes):
        src = [row[:] for row in idx]
        for y in range(h):
            for x in range(w):
                c = src[y][x]
                if c is None:
                    continue
                nb4, nb8 = [], []
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == dy == 0:
                            continue
                        X, Y = x + dx, y + dy
                        v = src[Y][X] if 0 <= X < w and 0 <= Y < h else None
                        nb8.append(v)
                        if dx == 0 or dy == 0:
                            nb4.append(v)
                if c not in nb4:
                    # 밝은 강조점(빛·불티)은 남김 — 어두운 바탕 위 1점 반짝임은 의도
                    if c in ("G15", "G14", "X1", "A27", "A26", "M0"):
                        continue
                    # 동률은 이웃 순서(첫 등장)로 — set 순서는 문자열 해시 무작위화로 실행마다 달라짐(결정성)
                    best = max(dict.fromkeys(nb8), key=nb8.count)
                    idx[y][x] = best
    return idx


def outline(idx, color="G01"):
    """바깥 1도트 외곽선(알파 경계 바깥쪽). 틀 가장자리까지 그림이 닿지 않게 그 전에 margin 확보."""
    h, w = len(idx), len(idx[0])
    src = [row[:] for row in idx]
    for y in range(h):
        for x in range(w):
            if src[y][x] is not None:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < w and 0 <= Y < h and src[Y][X] is not None and src[Y][X] != color:
                    idx[y][x] = color
                    break
    return idx


def to_image(idx):
    h, w = len(idx), len(idx[0])
    out = Image.new("RGBA", (w, h))
    po = out.load()
    for y in range(h):
        for x in range(w):
            n = idx[y][x]
            if n is not None:
                po[x, y] = hex2rgb(NAMED[n]) + (255,)
    return out


def from_image(im):
    rev = {hex2rgb(h): n for n, h in NAMED.items()}
    px = im.load()
    return [[(rev[px[x, y][:3]] if px[x, y][3] else None) for x in range(im.width)] for y in range(im.height)]


# ---- 카드 변환(채택 방식: 512 에서 양자화 → 블록 최빈값, 어두운 선·발광 점 우선) ----
EMIT = {"A23", "A24", "A25", "A26", "A27", "X1", "G14", "G15", "M0", "C1", "R2"}
_LUM = {n: sum(hex2rgb(h)) for n, h in NAMED.items()}


def median(im, n=3):
    from PIL import ImageFilter
    rgb = im.convert("RGB").filter(ImageFilter.MedianFilter(n))
    return Image.merge("RGBA", (*rgb.split(), im.getchannel("A")))


def card_pixels(raw, weapon, crop=None, zoom=1.0, dx=0, dy=0, margin=3, contrast=1.0, sat=1.05, lift=0.0,
                dark_t=0.30, emit_t=0.25, med=3, gray_gamma=1.25):
    """raw(512 RGB) → 128×128 색 이름 격자. zoom>1 이면 내용 상자를 더 크게(넘치는 쪽은 잘림 — crop 과 함께 씀)."""
    from collections import Counter
    k = drop_small(key_magenta(raw))
    if crop:
        k = k.crop(crop)
    k = k.crop(k.getbbox())
    side = max(k.size)
    big = Image.new("RGBA", (side, side))
    big.paste(k, ((side - k.width) // 2, (side - k.height) // 2))
    if med:
        big = median(big, med)
    big = grade(big, contrast=contrast, sat=sat, lift=lift, gray_gamma=gray_gamma)
    idx = quantize(big, ALLOW[weapon])
    tgt = (SIZE - 2 * margin) * zoom
    s = side / tgt
    out = [[None] * SIZE for _ in range(SIZE)]
    off = (SIZE - tgt) / 2
    for Y in range(SIZE):
        for X in range(SIZE):
            fx, fy = (X - off - dx) * s, (Y - off - dy) * s
            x0, y0 = int(fx), int(fy)
            x1, y1 = max(x0 + 1, int(fx + s)), max(y0 + 1, int(fy + s))
            if x1 <= 0 or y1 <= 0 or x0 >= side or y0 >= side:
                continue
            cs = [idx[yy][xx] for yy in range(max(0, y0), min(y1, side)) for xx in range(max(0, x0), min(x1, side))]
            n = len(cs)
            if not n:
                continue
            cnt = Counter(cs)
            if cnt.get(None, 0) > n * 0.5:
                continue
            cnt.pop(None, None)
            dark_n = sum(v for c, v in cnt.items() if _LUM[c] < 90)
            emit_n = sum(v for c, v in cnt.items() if c in EMIT)
            if emit_n >= n * emit_t and emit_n >= dark_n * 0.7:
                c = max((c for c in cnt if c in EMIT), key=lambda c: cnt[c])
            elif dark_n >= n * dark_t:
                c = max((c for c in cnt if _LUM[c] < 90), key=lambda c: cnt[c])
            else:
                c = cnt.most_common(1)[0][0]
            out[Y][X] = c
    # 틀 가장자리 1도트는 비움(외곽선 자리)
    for i in range(SIZE):
        out[0][i] = out[SIZE - 1][i] = out[i][0] = out[i][SIZE - 1] = None
    out = despeckle(out)
    return outline(out)
