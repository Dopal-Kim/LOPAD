"""53라운드 Gemini 외벽 테두리 공용 빌드 키트 (계약 art-assets §13).

border_outer/build.py 에 있던 처리를 지역 공용으로 옮겼다(외곽 산출물은 바이트 단위로 같음 — NOTES 확인).
지역별 build.py 는 BANDS·DOORS 표와 json 추가 키만 가진다. Pillow 만 사용(numpy 없음).

띠 단계: 자르기·축소(원본 1px → 저장 KS px) → 이음/감싸기 → 발광 마스크 → 톤 LUT → 알베도 곡선 → 알파 → 광원.
골목 입구 조각(doors): north·south = Gemini 조각 시트 패널, west = 그 지역 북·남 띠 원본을 같은 축척으로 조립, east = west 좌우 반전.
"""
import json, math, os, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

GEM = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GEM)
import gkit as K  # noqa: E402

ROOT = K.ROOT
PS = 0.5                    # pixelScale: 저장 px 1 = 논리 px 0.5
KS = 0.8                    # 원본 1px → 저장 0.8px (모든 띠 같은 축척 → 건물·술통 크기 통일)

# 명도 곡선(8bit 루마 in → out). wall = 바닥 알베도(평균 64)의 약 0.85 배, 하이라이트 압축.
CURVES = {
    "wall": [(0, 0), (20, 26), (40, 50), (70, 74), (100, 90), (150, 104), (255, 118)],
    "fore": [(0, 0), (20, 19), (40, 36), (70, 52), (110, 64), (255, 76)],   # 전경: 어둡게(실루엣 + 테 하이라이트)
}
EMIT_DARK = 0.30            # 발광 자리 알베도 배율(빛은 emissive 가 더함)
VOID = (14, 15, 20)


# ---------------------------------------------------------------------------
# 색 변환 LUT
# ---------------------------------------------------------------------------
_NAX = K._axis(K.GRAY)
_AAX = K._axis(K.RAMP1)


def _tone_rgb(c):
    """gkit.tone_match 의 한 색 버전 (accent_gain 1, neutral_keep 0)."""
    L, A, B = K.rgb2lab(c)
    na, nb = K._interp_ab(_NAX, L)
    ra, rb = K._interp_ab(_AAX, L)
    da, db = ra - na, rb - nb
    rc = math.hypot(da, db) or 1e-6
    pa, pb = A - na, B - nb
    proj = (pa * da + pb * db) / rc
    t = max(0.0, min(1.0, proj / rc))
    return K.lab2rgb((L, na + t * da, nb + t * db))


def _curve(pts, v):
    for (a, b), (c, d) in zip(pts, pts[1:]):
        if v <= c:
            return b + (d - b) * (v - a) / max(1e-6, c - a)
    return pts[-1][1]


def _luma(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def emit_strength(c, lum0=100, warm0=55):
    """밝고 따뜻한 픽셀 = 발광(창·문빛·등불). 0..1"""
    lum = _luma(c)
    warm = c[0] - c[2]
    a = max(0.0, min(1.0, (lum - lum0) / 55))
    b = max(0.0, min(1.0, (warm - warm0) / 45))
    return a * b


_LUT_CACHE = {}


def make_luts(curve, lum0=100, warm0=55):
    key = (curve, lum0, warm0)
    if key in _LUT_CACHE:
        return _LUT_CACHE[key]
    pts = CURVES[curve]

    def tone(r, g, b):
        t = _tone_rgb((r * 255, g * 255, b * 255))
        return tuple(v / 255 for v in t)

    def albedo(r, g, b):
        c = (r * 255, g * 255, b * 255)
        t = _tone_rgb(c)
        l0 = max(1e-3, _luma(t))
        k = _curve(pts, l0) / l0
        e = emit_strength(c, lum0, warm0)
        k *= (1 - e) + e * EMIT_DARK
        return tuple(max(0.0, min(1.0, v * k / 255)) for v in t)

    def emit(r, g, b):
        e = emit_strength((r * 255, g * 255, b * 255), lum0, warm0)
        return (e, e, e)
    gen = ImageFilter.Color3DLUT.generate
    _LUT_CACHE[key] = (gen(33, tone), gen(33, albedo), gen(33, emit))
    return _LUT_CACHE[key]


# ---------------------------------------------------------------------------
# 이음 (최소 오차 경로)
# ---------------------------------------------------------------------------
def _min_cut(A, B, ov):
    """A, B: 같은 크기(ov × h) RGB. 세로 최소 오차 경로 x[y] 반환."""
    w, h = A.size
    pa, pb = A.load(), B.load()
    lo, hi = 2, ov - 3
    INF = 1e18
    prev = [INF] * ov
    back = []
    for y in range(h):
        cur = [INF] * ov
        bk = [0] * ov
        for x in range(lo, hi + 1):
            a, b = pa[x, y], pb[x, y]
            e = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
            if y == 0:
                cur[x] = e
                continue
            best, bx = INF, x
            for dx in (-1, 0, 1):
                xx = x + dx
                if lo <= xx <= hi and prev[xx] < best:
                    best, bx = prev[xx], xx
            cur[x] = best + e
            bk[x] = bx
        back.append(bk)
        prev = cur
    x = min(range(lo, hi + 1), key=lambda k: prev[k])
    path = [0] * h
    for y in range(h - 1, -1, -1):
        path[y] = x
        x = back[y][x]
    return path


def _cut_mask(path, ov, h, feather=3):
    """경로 왼쪽 = 0(A), 오른쪽 = 255(B), 경계 feather px 부드럽게."""
    m = Image.new("L", (ov, h), 0)
    p = m.load()
    for y in range(h):
        for x in range(ov):
            d = x - path[y]
            p[x, y] = int(max(0, min(255, 127.5 + d * 255 / (2 * feather))))
    return m


def join_h(L, R, ov):
    """L 의 오른쪽 ov 열과 R 의 왼쪽 ov 열을 겹쳐 최소 오차 경로로 잇는다. 반환 폭 = wL + wR - ov."""
    h = L.height
    A = L.crop((L.width - ov, 0, L.width, h)).convert("RGB")
    B = R.crop((0, 0, ov, h)).convert("RGB")
    path = _min_cut(A, B, ov)
    seam = Image.composite(R.crop((0, 0, ov, h)), L.crop((L.width - ov, 0, L.width, h)), _cut_mask(path, ov, h))
    out = Image.new(L.mode, (L.width + R.width - ov, h))
    out.paste(L.crop((0, 0, L.width - ov, h)), (0, 0))
    out.paste(seam, (L.width - ov, 0))
    out.paste(R.crop((ov, 0, R.width, h)), (L.width, 0))
    return out


def wrap_h(im, ov):
    """좌우 감싸기: 오른쪽 끝 ov 열을 왼쪽 처음 ov 열에 최소 오차 경로로 겹친다. 폭 - ov."""
    h = im.height
    A = im.crop((im.width - ov, 0, im.width, h)).convert("RGB")
    B = im.crop((0, 0, ov, h)).convert("RGB")
    path = _min_cut(A, B, ov)
    seam = Image.composite(im.crop((0, 0, ov, h)), im.crop((im.width - ov, 0, im.width, h)), _cut_mask(path, ov, h))
    out = im.crop((0, 0, im.width - ov, h))
    out.paste(seam, (0, 0))
    return out


def wrap_v(im, ov):
    t = im.transpose(Image.Transpose.TRANSPOSE)
    return wrap_h(t, ov).transpose(Image.Transpose.TRANSPOSE)


def seam_err_h(im):
    a, inner = K.seam_error(im)
    return round(a, 1), round(inner, 1)


# ---------------------------------------------------------------------------
# 광원 검출
# ---------------------------------------------------------------------------
def light_radius(area):
    """발광 면적(논리 px²) → 반경. 창 ≈ 500 → 110, 문·등불 ≥ 1500 → 150(상한)."""
    return int(max(50, min(150, 40 + 3.2 * math.sqrt(area))))


def light_int(area):
    return round(max(0.4, min(0.95, 0.4 + 0.015 * math.sqrt(area))), 2)


def detect_lights(emit_l, tone_rgb, cell=8, thr=0.18, min_cells=2):
    """emit_l: L 마스크(저장 해상도). cell 저장 px 격자로 묶어 덩어리 → 광원(논리 px)."""
    w, h = emit_l.size
    gw, gh = w // cell, h // cell
    small = emit_l.resize((gw, gh), Image.BOX)
    sp = small.load()
    col = tone_rgb.resize((gw, gh), Image.BOX).load()
    seen = set()
    lights = []
    for y0 in range(gh):
        for x0 in range(gw):
            if (x0, y0) in seen or sp[x0, y0] / 255 < thr:
                continue
            comp, st = [], [(x0, y0)]
            seen.add((x0, y0))
            while st:
                x, y = st.pop()
                comp.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < gw and 0 <= yy < gh and (xx, yy) not in seen and sp[xx, yy] / 255 >= thr:
                        seen.add((xx, yy))
                        st.append((xx, yy))
            if len(comp) < min_cells:
                continue
            wsum = sum(sp[x, y] for x, y in comp) / 255
            cx = sum((x + .5) * sp[x, y] for x, y in comp) / 255 / wsum
            cy = sum((y + .5) * sp[x, y] for x, y in comp) / 255 / wsum
            r = g = b = 0.0
            for x, y in comp:
                c = col[x, y]
                f = sp[x, y] / 255
                r += c[0] * f; g += c[1] * f; b += c[2] * f
            r, g, b = (v / wsum for v in (r, g, b))
            m = max(r, g, b, 1)
            r, g, b = (min(255, int(v * 238 / m)) for v in (r, g, b))
            area_l = wsum * (cell * PS) ** 2          # 논리 px²
            lights.append({
                "x": round(cx * cell * PS, 1), "y": round(cy * cell * PS, 1),
                "color": "#%02x%02x%02x" % (r, g, b),
                "radius": light_radius(area_l), "intensity": light_int(area_l),
                "areaPx": int(area_l),
            })
    lights.sort(key=lambda L: (L["x"], L["y"]))
    return lights


def merge_lights(lights, dist):
    out = []
    for L in sorted(lights, key=lambda L: -L["areaPx"]):
        for M in out:
            if math.hypot(L["x"] - M["x"], L["y"] - M["y"]) < dist:
                tot = M["areaPx"] + L["areaPx"]
                M["x"] = round((M["x"] * M["areaPx"] + L["x"] * L["areaPx"]) / tot, 1)
                M["y"] = round((M["y"] * M["areaPx"] + L["y"] * L["areaPx"]) / tot, 1)
                M["areaPx"] = tot
                M["radius"] = light_radius(tot)
                M["intensity"] = light_int(tot)
                break
        else:
            out.append(dict(L))
    out.sort(key=lambda L: (L["x"], L["y"]))
    return out


def band_lights(emit, tone, merge=26, cap=None):
    L = merge_lights(detect_lights(emit, tone), merge)
    for l in L:
        big = l["areaPx"] >= 1200
        l["flicker"] = {"amp": 0.08 if big else 0.04, "hz": 3}
        l["kind"] = "door_or_lantern" if big else "window"
    if cap:      # 큰 순서로 cap 개만 (작은 별빛 같은 원경 창은 발광 PNG 만으로 충분)
        L = sorted(sorted(L, key=lambda l: -l["areaPx"])[:cap], key=lambda l: (l["x"], l["y"]))
    return L


# ---------------------------------------------------------------------------
# 띠 빌드
# ---------------------------------------------------------------------------
def load_part(src_dir, fn, box, ks=KS):
    im = Image.open(os.path.join(src_dir, fn)).convert("RGB").crop(box)
    w, h = round(im.width * ks), round(im.height * ks)
    w -= w % 2
    h -= h % 2
    return im.resize((w, h), Image.LANCZOS)


def sky_ref(src):
    px = src.load()
    acc = [0, 0, 0]
    n = 0
    for x in range(0, src.width, 5):
        for y in range(2, 14, 3):
            acc = [a + v for a, v in zip(acc, px[x, y])]
            n += 1
    return [a / n for a in acc]


def sky_alpha(src, base):
    """남쪽 띠: 기준선 위에서 위쪽 가장자리와 이어진 '하늘색' 영역을 투명으로."""
    W, H = src.size
    px = src.load()
    sky = sky_ref(src)
    edges = src.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3)).load()
    a = Image.new("L", (W, H), 255)
    ap = a.load()
    for x in range(W):
        y = 0
        run = 0
        while y < base:
            c = px[x, y]
            d = abs(c[0] - sky[0]) + abs(c[1] - sky[1]) + abs(c[2] - sky[2])
            if d > 34 or edges[x, y] > 60:
                run += 1
                if run >= 3:
                    y -= 2
                    break
            else:
                run = 0
            ap[x, y] = 0
            y += 1
        for yy in range(max(0, y), min(base, y + 1)):
            ap[x, yy] = 255
    return a.filter(ImageFilter.MedianFilter(5))


def white_key_alpha(src, lo=150, hi=205):
    """흰 바탕(난간 사이 틈 등) → 투명. 밝고 채도 낮은 픽셀일수록 알파 0."""
    W, H = src.size
    a = Image.new("L", (W, H), 255)
    sp, ap = src.load(), a.load()
    for y in range(H):
        for x in range(W):
            c = sp[x, y]
            l = _luma(c)
            sat = max(c) - min(c)
            if l > lo and sat < 40:
                ap[x, y] = int(255 * max(0.0, min(1.0, (hi - l) / (hi - lo))))
    return a


def crush_sky_below(src, out, base):
    """기준선 아래로 이어지는 '하늘 틈'(위 하늘과 맞닿은 하늘색 영역)만 어두운 골목으로 누른다."""
    W, H = src.size
    px = src.load()
    sky = sky_ref(src)
    alpha = out.getchannel("A").load()

    def is_sky(x, y):
        c = px[x, y]
        return abs(c[0] - sky[0]) + abs(c[1] - sky[1]) + abs(c[2] - sky[2]) < 26
    m = Image.new("L", (W, H), 0)
    mp = m.load()
    st = [(x, base) for x in range(W) if alpha[x, base - 3] < 128 and is_sky(x, base)]
    for x, y in st:
        mp[x, y] = 255
    while st:
        x, y = st.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1)):
            xx, yy = x + dx, y + dy
            if 0 <= xx < W and base <= yy < H and not mp[xx, yy] and is_sky(xx, yy):
                mp[xx, yy] = 255
                st.append((xx, yy))
    m = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.5))
    dark = out.point(lambda v: int(v * 0.6))
    dark.putalpha(out.getchannel("A"))
    return Image.composite(dark, out, m)


def bottom_fade(out, em, f):
    W, H = out.size
    g = Image.new("L", (1, H), 0)
    for y in range(H - f, H):
        g.putpixel((0, y), int(255 * ((y - (H - f)) / f) ** 1.2))
    g = g.resize((W, H))
    voidc = Image.new("RGBA", (W, H), VOID + (255,))
    voidc.putalpha(out.getchannel("A"))
    out = Image.composite(voidc, out, g)
    em.putalpha(ImageChops.multiply(em.getchannel("A"), ImageChops.invert(g)))
    return out, em


def apron_alpha(W, H, base):
    alpha = Image.new("L", (W, H), 255)
    ap = alpha.load()
    for y in range(base, H):
        t = (y - base) / max(1, H - 1 - base)
        v = int(255 * max(0.0, 1 - t) ** 1.6) if y > base + 4 else 255
        for x in range(W):
            ap[x, y] = v
    return alpha


def tone_split(src, cfg):
    """src(RGB, 저장 해상도) → (tone, albedo, emit L)"""
    lut_tone, lut_alb, lut_emit = make_luts(cfg.get("curve", "wall"), cfg.get("emit_lum", 100), cfg.get("emit_warm", 55))
    tone = src.filter(lut_tone)
    alb = src.filter(lut_alb)
    emit = src.filter(lut_emit).convert("L").filter(ImageFilter.GaussianBlur(0.8))
    if cfg.get("emit_gain", 1.0) != 1.0:
        g = cfg["emit_gain"]
        emit = emit.point(lambda v: int(v * g))
    return tone, alb, emit


def band_source(src_dir, cfg):
    parts = [load_part(src_dir, fn, box) for fn, box in cfg["parts"]]
    if len(parts) > 1:
        H = min(p.height for p in parts)
        parts = [p.crop((0, 0, p.width, H)) for p in parts]
        src = parts[0]
        for p in parts[1:]:
            src = join_h(src, p, cfg["join_overlap"])
    else:
        src = parts[0]
    return src


def build_band(src_dir, name, cfg):
    src = band_source(src_dir, cfg)
    T = Image.Transpose.TRANSPOSE
    before = seam_err_h(src) if cfg["wrap"] == "x" else seam_err_h(src.transpose(T))
    src = wrap_h(src, cfg["wrap_overlap"]) if cfg["wrap"] == "x" else wrap_v(src, cfg["wrap_overlap"])
    if src.width % 2:
        src = src.crop((0, 0, src.width - 1, src.height))
    if src.height % 2:
        src = src.crop((0, 0, src.width, src.height - 1))
    after = seam_err_h(src) if cfg["wrap"] == "x" else seam_err_h(src.transpose(T))

    tone, alb, emit = tone_split(src, cfg)
    W, H = src.size
    alpha = Image.new("L", (W, H), 255)
    info = {}
    if name == "north":
        base = round(cfg["baseline_src"] * KS)
        base -= base % 2
        alpha = apron_alpha(W, H, base)
        info["baselineY"] = base * PS
        info["apronBelow"] = (H - base) * PS
    elif name == "south":
        base = round(cfg["baseline_src"] * KS)
        base -= base % 2
        alpha = sky_alpha(src, base)
        if cfg.get("white_key"):
            alpha = ImageChops.multiply(alpha, white_key_alpha(src))
        info["baselineY"] = base * PS
    emit = ImageChops.multiply(emit, alpha)
    em = tone.copy().convert("RGBA")
    em.putalpha(emit)
    out = alb.convert("RGBA")
    out.putalpha(alpha)
    if cfg.get("bottom_fade"):
        out, em = bottom_fade(out, em, cfg["bottom_fade"])
    if name == "south" and not cfg.get("white_key"):
        out = crush_sky_below(src, out, base)
    info.update(seamBefore=before, seamAfter=after)
    return out, em, tone, emit, info


def _even(v):
    v = int(round(v))
    return v - v % 2


def build_north_split(src_dir, cfg):
    """북 띠를 가운데 조각(한 번만) + 좌·우 반복 조각으로 (repeat 'sides', Q22 성문).
    원본 좌표 split = {left:(a,b), right:(c,d)}. 저장 px 로 바꿔
      left  = wrap_h(src[a:b])                 → 끝이 src[b-ov] 로 이어짐
      center= src[b-ov : c+ov]                 → 원래 그림 그대로(이음새 없음)
      right = flip(wrap_h(flip(src[c:d])))     → 시작이 src[c+ov] 로 이어짐
    반환: {left|center|right: (out, em, tone, emit)}, info"""
    src = band_source(src_dir, cfg)
    ov = cfg["wrap_overlap"]
    (a, b), (c, d) = cfg["split"]["left"], cfg["split"]["right"]
    a, b, c, d = (_even(v * KS) for v in (a, b, c, d))
    H = src.height
    segL = src.crop((a, 0, b, H))
    segR = ImageOps.mirror(src.crop((c, 0, d, H)))
    pieces = {
        "left": wrap_h(segL, ov),
        "center": src.crop((b - ov, 0, c + ov, H)),
        "right": ImageOps.mirror(wrap_h(segR, ov)),
    }
    base = _even(cfg["baseline_src"] * KS)
    info = {"baselineY": base * PS, "apronBelow": (H - base) * PS,
            "seamLeftWrap": seam_err_h(pieces["left"]), "seamRightWrap": seam_err_h(pieces["right"]),
            "centerStartSrc": (b - ov) / KS, "splitStorage": [a, b, c, d]}
    # 이음 확인: left 끝 → center 시작, center 끝 → right 시작 (인접 열 차이)
    def coldiff(A, B):
        pa, pb = A.load(), B.load()
        return round(sum(sum(abs(x - y) for x, y in zip(pa[0, yy], pb[0, yy])) for yy in range(H)) / (3 * H), 1)
    L, C, R = (pieces[k].convert("RGB") for k in ("left", "center", "right"))
    info["joinLC"] = coldiff(L.crop((L.width - 1, 0, L.width, H)), C.crop((0, 0, 1, H)))
    info["joinCR"] = coldiff(C.crop((C.width - 1, 0, C.width, H)), R.crop((0, 0, 1, H)))
    out = {}
    for k, im in pieces.items():
        tone, alb, emit = tone_split(im, cfg)
        alpha = apron_alpha(im.width, H, base)
        emit = ImageChops.multiply(emit, alpha)
        em = tone.copy().convert("RGBA")
        em.putalpha(emit)
        o = alb.convert("RGBA")
        o.putalpha(alpha)
        out[k] = (o, em, tone, emit)
    return out, info


def strip_emissive(em):
    nz = em.getchannel("A").point(lambda v: 255 if v > 2 else 0)
    return Image.composite(em, Image.new("RGBA", em.size, (0, 0, 0, 0)), nz)


# ---------------------------------------------------------------------------
# 골목 입구 조각
# ---------------------------------------------------------------------------
def feather_mask(W, H, left=0, right=0, top=0, bottom=0, gamma=1.3):
    """가장자리 페이드 알파(L)."""
    col = Image.new("L", (W, 1), 255)
    for x in range(W):
        v = 1.0
        if left and x < left:
            v = min(v, x / left)
        if right and x >= W - right:
            v = min(v, (W - 1 - x) / right)
        col.putpixel((x, 0), int(255 * max(0.0, v) ** gamma))
    row = Image.new("L", (1, H), 255)
    for y in range(H):
        v = 1.0
        if top and y < top:
            v = min(v, y / top)
        if bottom and y >= H - bottom:
            v = min(v, (H - 1 - y) / bottom)
        row.putpixel((0, y), int(255 * max(0.0, v) ** gamma))
    return ImageChops.multiply(col.resize((W, H)), row.resize((W, H)))


def _finish_piece(src, alpha, cfg):
    tone, alb, emit = tone_split(src, cfg)
    emit = ImageChops.multiply(emit, alpha)
    em = tone.convert("RGBA")
    em.putalpha(emit)
    out = alb.convert("RGBA")
    out.putalpha(alpha)
    return out, strip_emissive(em), tone, emit


def door_panel(src_dir, d):
    """Gemini 조각 시트 패널 → (src RGB 저장 해상도, 축척)"""
    return load_part(src_dir, d["sheet"], d["box"], d["scale"]), d["scale"]


def build_door_north(src_dir, d):
    src, s = door_panel(src_dir, d)
    W, H = src.size
    x0, y0 = d["box"][:2]
    base = round((d["baseline_src"] - y0) * s)
    base -= base % 2
    alpha = feather_mask(W, H, left=int(W * 0.22), right=int(W * 0.22), top=int(H * 0.18))
    ap = apron_alpha(W, H, base)
    alpha = ImageChops.multiply(alpha, ap)
    out, em, tone, emit = _finish_piece(src, alpha, d)
    cx = (d["opening_src"][0] - x0) * s
    ow = (d["opening_src"][1] - d["opening_src"][0]) * s
    meta = {"w": W * PS, "h": H * PS, "baselineY": base * PS, "openingX": round((cx + ow / 2) * PS, 1),
            "openingW": round(ow * PS, 1)}
    return out, em, tone, emit, meta


def build_door_south(src_dir, d):
    src, s = door_panel(src_dir, d)
    W, H = src.size
    x0, y0 = d["box"][:2]
    alpha = feather_mask(W, H, left=int(W * 0.2), right=int(W * 0.2), top=d.get("top_fade", 24), bottom=int(H * 0.25))
    out, em, tone, emit = _finish_piece(src, alpha, dict(d, curve="fore"))
    cx = (d["opening_src"][0] - x0) * s
    ow = (d["opening_src"][1] - d["opening_src"][0]) * s
    meta = {"w": W * PS, "h": H * PS, "baselineY": d.get("baselineY", 12), "openingX": round((cx + ow / 2) * PS, 1),
            "openingW": round(ow * PS, 1)}
    return out, em, tone, emit, meta


def build_door_west(src_dir, d, bands):
    """서쪽 골목 입구 = 같은 지역 띠 원본 조립(같은 축척·카메라):
    위 = 북 띠의 건물/둑 앞면(골목 북쪽 면, 아래를 향함), 가운데 = 골목 바닥(북 띠 기준선 아래 땅 줄을 세로로 이어 붙임,
    서쪽으로 갈수록 어둠), 아래 = 남 띠 윗단(골목 남쪽 건물의 지붕·둑이 골목 남쪽 가장자리를 덮음). 오른쪽 끝 = 바닥 서쪽 끝."""
    W = 512                                         # 저장 px = 논리 256 (서 띠 폭)
    OH = d.get("openingH", 96) * 2                  # 골목 폭(세로, 저장 px)
    FH = d.get("frontH", 240)                       # 북쪽 면 높이(저장 px)
    SH = d.get("southH", 110)                       # 남쪽 덮개 높이(저장 px)
    TOPF = 60                                       # 위 페이드
    nb = band_source(src_dir, bands["north"])
    nbase = round(bands["north"]["baseline_src"] * KS)
    fx = d["front_x"]                               # 북 띠(저장 px)에서 골목 북쪽 면으로 쓸 구간 왼쪽
    front = nb.crop((fx, nbase - FH - TOPF, fx + W, nbase))
    # 골목 바닥: 북 띠 기준선 아래 땅 줄(높이 g)을 반전하며 쌓음
    g = max(8, min(36, nb.height - nbase - 2))
    gstrip = nb.crop((fx, nbase + 2, fx + W, nbase + 2 + g))
    # 1회차 비평: 땅 줄을 그대로 쌓으면 줄무늬·소품이 반복돼 보임 → 세로로 평균 낸 색 + 흐린 질감(반복 안 보이게)
    lane = Image.new("RGB", (W, OH))
    y = 0
    k = 0
    while y < OH:
        piece = gstrip if k % 2 == 0 else ImageOps.flip(gstrip)
        lane.paste(piece, (0, y))
        y += g
        k += 1
    lane = lane.filter(ImageFilter.GaussianBlur(7))
    avg = gstrip.resize((max(1, W // 64), 1), Image.BOX).resize((W, OH), Image.BILINEAR)
    lane = Image.blend(avg, lane, 0.35)
    sb = band_source(src_dir, bands["south"])
    sbase = round(bands["south"]["baseline_src"] * KS)
    sx = d["south_x"]
    south = sb.crop((sx, max(0, sbase - 30), sx + W, max(0, sbase - 30) + SH))
    H = TOPF + FH + OH + SH - 20
    src = Image.new("RGB", (W, H), VOID)
    src.paste(front, (0, 0))
    src.paste(lane, (0, TOPF + FH))
    # 골목 바닥 명암: 서쪽(왼쪽)으로 어둠, 북쪽 면 발치 그늘
    shade = Image.new("L", (W, OH))
    sp = shade.load()
    for yy in range(OH):
        for xx in range(W):
            t = xx / (W - 1)
            v = 0.30 + 0.70 * t ** 1.6          # 2회차 비평: 0.10 이면 '잘라낸 어둠' 띠로 읽힘
            v *= 0.55 + 0.45 * min(1.0, yy / (OH * 0.35))
            sp[xx, yy] = int(255 * v)
    lane_sh = ImageChops.multiply(src.crop((0, TOPF + FH, W, TOPF + FH + OH)), Image.merge("RGB", (shade,) * 3))
    src.paste(lane_sh, (0, TOPF + FH))
    # 남쪽 덮개: 남 띠의 하늘 알파를 써서 지붕/둑만 얹음
    s_full = sky_alpha(sb, sbase)
    if bands["south"].get("white_key"):
        s_full = ImageChops.multiply(s_full, white_key_alpha(sb))
    s_alpha = s_full.crop((sx, max(0, sbase - 30), sx + W, max(0, sbase - 30) + SH))
    src.paste(south, (0, TOPF + FH + OH - 20), s_alpha)
    # 북쪽 면 전체도 서쪽으로 약간 어둡게(골목 속으로 들어감)
    grad = Image.new("L", (W, 1))
    for xx in range(W):
        grad.putpixel((xx, 0), int(255 * (0.6 + 0.4 * (xx / (W - 1)) ** 0.8)))
    src = ImageChops.multiply(src, Image.merge("RGB", (grad.resize((W, H)),) * 3))
    alpha = feather_mask(W, H, left=90, top=TOPF, bottom=40)
    out, em, tone, emit = _finish_piece(src, alpha, d)
    meta = {"w": W * PS, "h": H * PS, "baselineX": W * PS, "openingY": round((TOPF + FH + OH / 2) * PS, 1),
            "openingH": OH * PS}
    return out, em, tone, emit, meta


def mirror_door(out, em, meta):
    m = dict(meta)
    m["baselineX"] = 0
    return ImageOps.mirror(out), ImageOps.mirror(em), m


# ---------------------------------------------------------------------------
# 지역 빌드
# ---------------------------------------------------------------------------
def lg(v):
    return v * PS


def _L(lst):
    return [{k: v for k, v in l.items() if k != "areaPx"} for l in lst]


def build_region(region, src_dir, bands, doors=None, extra=None, json_head=None):
    """bands: {north, west, east, south} cfg. doors: {north, south, west} cfg (east = west 반전). 반환 meta."""
    out_dir = os.path.join(ROOT, "assets/tiles/border", region)
    os.makedirs(out_dir, exist_ok=True)
    meta = {}
    for name, cfg in bands.items():
        if name == "north" and cfg.get("split"):
            parts, info = build_north_split(src_dir, cfg)
            files = {"center": "north", "left": "north_left", "right": "north_right"}
            pm = {}
            for k, (o, em, tone, emit) in parts.items():
                o.save(os.path.join(out_dir, f"{files[k]}.png"), optimize=True)
                strip_emissive(em).save(os.path.join(out_dir, f"{files[k]}_emissive.png"), optimize=True)
                pm[k] = dict(size=o.size, lights=band_lights(emit, tone, cap=cfg.get("light_cap")), file=files[k])
            meta[name] = dict(info, size=pm["center"]["size"], lights=pm["center"]["lights"], sides=pm)
            print(region, "north split", {k: v["size"] for k, v in pm.items()}, "wrapL", info["seamLeftWrap"],
                  "wrapR", info["seamRightWrap"], "joinLC", info["joinLC"], "joinCR", info["joinCR"])
            continue
        out, em, tone, emit, info = build_band(src_dir, name, cfg)
        out.save(os.path.join(out_dir, f"{name}.png"), optimize=True)
        em = strip_emissive(em)
        em.save(os.path.join(out_dir, f"{name}_emissive.png"), optimize=True)
        W, H = out.size
        lights = band_lights(emit, tone, cap=cfg.get("light_cap"))
        meta[name] = dict(info, size=(W, H), lights=lights)
        print(region, name, (W, H), "logical", (W * PS, H * PS), "lights", len(lights), "seam", info["seamBefore"], "->", info["seamAfter"])
    dmeta = {}
    if doors:
        for side, d in doors.items():
            if side == "north":
                out, em, tone, emit, m = build_door_north(src_dir, d)
            elif side == "south":
                out, em, tone, emit, m = build_door_south(src_dir, d)
            elif side == "west":
                out, em, tone, emit, m = build_door_west(src_dir, d, bands)
            else:
                continue
            L = band_lights(emit, tone, cap=4)
            m["lights"] = _L(L)
            out.save(os.path.join(out_dir, f"door_{side}.png"), optimize=True)
            em.save(os.path.join(out_dir, f"door_{side}_emissive.png"), optimize=True)
            m.update(file=f"door_{side}.png", emissive=f"door_{side}_emissive.png")
            dmeta[side] = m
            if side == "west":
                o2, e2, m2 = mirror_door(out, em, m)
                m2["lights"] = [dict(l, x=round(m2["w"] - l["x"], 1)) for l in m["lights"]]
                m2.update(file="door_east.png", emissive="door_east_emissive.png", mirrorOf="door_west.png")
                o2.save(os.path.join(out_dir, "door_east.png"), optimize=True)
                e2.save(os.path.join(out_dir, "door_east_emissive.png"), optimize=True)
                dmeta["east"] = m2
            print(region, "door", side, m["w"], m["h"], "lights", len(m["lights"]))
    write_json(region, out_dir, meta, dmeta, extra or {}, json_head or {})
    json.dump({k: {kk: vv for kk, vv in v.items() if kk != "lights"} for k, v in meta.items()},
              open(os.path.join(src_dir, "build_info.json"), "w"), ensure_ascii=False, indent=1)
    return meta, dmeta


DOORS_DOC = ("골목 입구 조각(53라운드 Q13, 키 이름은 시스템과 확정 대상). 문·출구 칸 위에 띠 다음에 덧그린다(같은 depth·조명·발광 규칙). "
             "north: baselineY 줄 = 바닥 북쪽 끝, openingX(조각 국소 x) = 문 칸들의 가운데 x 에 맞춤, openingW = 그림 속 통로 폭(참고). "
             "south: baselineY 줄 = 바닥 남쪽 끝, openingX 를 문 칸 가운데에. 남 띠와 같은 전경(foreground)·가림 규칙. "
             "west: 오른쪽 끝(baselineX) = 바닥 서쪽 끝, openingY(조각 국소 y) = 문 칸들의 가운데 y, openingH = 그림 속 골목 폭. "
             "east: west 의 좌우 반전(baselineX 0 = 바닥 동쪽 끝). lights[] = 조각 국소 좌표, 띠 광원 중 조각에 가려지는 것은 빼지 않아도 된다(약함).")


def write_json(region, out_dir, meta, dmeta, extra, head):
    n, s, w, e = (meta[k] for k in ("north", "south", "west", "east"))
    data = {
        "region": region, "stage": 1, "version": head.get("version", "53라운드 (Gemini 테두리)"),
        "source": head.get("source", f"parts/art/work/gemini/border_{region}/build.py (원본·프롬프트 같은 폴더)"),
        "pixelScale": PS,
        "units": "모든 길이·좌표 = 논리 px(960×540 기준). 이미지 픽셀 = 논리 px / pixelScale(=2배). 1920 렌더에서 1:1.",
        "lighting": "albedo 는 바닥 v2 타일과 같은 조명 공간(곱하기 조명을 받는다). *_emissive.png 는 조명 뒤 가산(알파 = 세기, 어둠에 묻히지 않음). lights[] 는 띠 국소 좌표의 광원 — 반복 띠는 주기마다 반복 등록.",
        "lightsRule": "lights[] 좌표 = 띠 이미지 왼쪽 위 기준 논리 px. 반복 띠는 주기마다 등록. 서·동 띠 광원 중 바닥 세로 범위(북쪽 기준선 ~ 남쪽 기준선) 밖에 오는 것은 다른 띠에 가려지므로 등록하지 않는다. flicker 는 계약 §12 형식.",
        "drawOrder": ["floor", "floorDecals+floorShadows", "west", "east", "north", "doors(west,east,north)", "ySorted(props, characters, fx)", "south", "doors(south)", "lighting", "emissive(add)", "ui"],
        "bands": {
            "north": {
                "image": "north.png", "emissive": "north_emissive.png",
                "width": lg(n["size"][0]), "height": lg(n["size"][1]),
                "repeat": "x", "anchor": "floorTop",
                "baselineY": n["baselineY"], "apronBelow": n["apronBelow"],
                "place": "띠의 baselineY 줄 = 바닥 북쪽 끝(북쪽 벽 앞면 아랫단의 밑변). x 는 (바닥 왼쪽 - west.width) 부터 반복해 (바닥 오른쪽 + east.width) 까지 덮는다.",
                "apron": "baselineY 아래 apronBelow 는 땅·소품 밑동이 알파로 사라지는 앞치마 — 바닥 위에 겹쳐 그린다(충돌 없음).",
                "depth": "background", "lights": _L(n["lights"]),
            },
            "south": {
                "image": "south.png", "emissive": "south_emissive.png",
                "width": lg(s["size"][0]), "height": lg(s["size"][1]),
                "repeat": "x", "anchor": "floorBottom",
                "baselineY": s["baselineY"],
                "place": "띠의 baselineY 줄 = 바닥 남쪽 끝. 그 위(0~baselineY)는 전경이 바닥을 덮는 겹침(투명 하늘 제외).",
                "depth": "foreground",
                "occlusion": {"fadeAlpha": 0.45, "rule": "플레이어 몸 사각형이 띠의 불투명 픽셀과 겹치면 띠 전체(또는 그 구간)를 fadeAlpha 로 반투명"},
                "lights": _L(s["lights"]),
            },
            "west": {
                "image": "west.png", "emissive": "west_emissive.png",
                "width": lg(w["size"][0]), "height": lg(w["size"][1]),
                "repeat": "y", "anchor": "floorLeft", "baselineX": lg(w["size"][0]),
                "place": "띠의 오른쪽 끝(baselineX) = 바닥 서쪽 끝(서쪽 벽 칸의 동쪽 변). y 는 북쪽 띠 위끝부터 남쪽 띠 아래끝까지 반복(북쪽 띠·남쪽 띠가 위에 덮임).",
                "depth": "background", "lights": _L(w["lights"]),
            },
            "east": {
                "image": "east.png", "emissive": "east_emissive.png",
                "width": lg(e["size"][0]), "height": lg(e["size"][1]),
                "repeat": "y", "anchor": "floorRight", "baselineX": 0,
                "place": "띠의 왼쪽 끝 = 바닥 동쪽 끝. 나머지는 west 와 같음.",
                "depth": "background", "lights": _L(e["lights"]),
            },
        },
        "corners": "별도 모서리 그림 없음 — north·south 가 좌우 띠 폭까지 덮는다(그리기 순서로 해결).",
        "collision": "충돌은 기존 격자 그대로(벽 칸 = 막힘). 테두리 그림은 벽 칸 위에 덮는 그림일 뿐이며, 테두리가 있는 지역에서는 벽 타일(앞면·윗면·가장자리)을 그리지 않는다. 문·출구 칸은 doors 조각을 덧그린다(통행은 격자대로).",
        "camera": {"bounds": {"top": -n["baselineY"], "bottom": "floorBottom + %g" % (lg(s["size"][1]) - s["baselineY"]), "left": -200, "right": "floorRight + 200"}, "northLookUp": 110, "note": "53라운드 Q8 결정: 북쪽 끝 200 안에서 최대 110 위로. 위 = 북쪽 띠 위끝(바닥 북쪽 끝 기준 -baselineY), 아래 = 남쪽 띠 아래끝, 좌우 = 바닥 끝 ± 200."},
        "ambient": {"rgb": [0.34, 0.34, 0.38], "note": "53라운드 Q9 결정(중립 숯빛)"},
    }
    if n.get("sides"):
        sd = n["sides"]
        nn = data["bands"]["north"]
        nn.update({
            "repeat": "sides",
            "place": "repeat 'sides': 가운데 조각(image)은 한 번만 — focusX 가 바닥 가운데 x 에 오게 둔다. 그 왼쪽 끝에 sides.left 를 오른쪽 끝을 맞춰 붙이고 왼쪽으로 (바닥 왼쪽 - west.width) 까지 반복, 오른쪽 끝에 sides.right 를 붙여 오른쪽으로 (바닥 오른쪽 + east.width) 까지 반복. 세 조각 모두 같은 높이·baselineY.",
            "sides": {k: {"image": f"{sd[k]['file']}.png", "emissive": f"{sd[k]['file']}_emissive.png",
                          "width": lg(sd[k]["size"][0]), "repeat": "x", "lights": _L(sd[k]["lights"])}
                      for k in ("left", "right")},
        })
    data["bands"]["north"].update(extra.get("north", {}))
    if dmeta:
        data["doors"] = dict(dmeta, doc=DOORS_DOC)
    for k, v in extra.items():
        if k not in ("north",):
            data[k] = v
    json.dump(data, open(os.path.join(out_dir, "border.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
