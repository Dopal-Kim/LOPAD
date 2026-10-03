#!/usr/bin/env python3
"""53라운드 Q2 — 외곽 거리 Gemini 외벽 테두리 빌드 (계약 art-assets §13).

python3 parts/art/work/gemini/border_outer/build.py          # 산출 + 목업
python3 parts/art/work/gemini/border_outer/build.py --no-mock

원본(raw_*.jpg)은 이 폴더. 아래 BANDS 표가 '어느 원본을 어떻게 잘라 어디로 내보내는지'의 유일한 기준.
게임 투입 PNG 는 손으로 고치지 않는다. Pillow 만 사용(numpy 없음).

단계(띠마다):
  1. 자르기·축소(LANCZOS, 원본 1px → 저장 0.8px) — 저장 해상도 = 논리 px × 2 (pixelScale 0.5, 1920 렌더 1:1)
  2. 이음: 북쪽 = a·b 두 장을 최소 오차 세로 경로로 이어 붙인 뒤 좌우 감싸기(quilt), 서·동 = 위아래 감싸기, 남 = 좌우 감싸기
  3. 발광 마스크: 밝고 따뜻한(호박) 픽셀 → *_emissive.png (RGBA, 알파 = 발광 세기)
  4. 색조: gkit.tone_match 와 같은 사영(무채 G00~G15 ↔ 1층 램프 16~27)을 3D LUT 로 — 도트화·감색 없음
  5. 알베도 명도: 바닥 v2 알베도와 같은 조명 공간. 하이라이트(구운 빛 웅덩이)는 눌러 굽지 않는다. 발광 자리는 어둡게(빛은 emissive 가 더한다)
  6. 알파: 북 = 기준선 아래 앞치마(포석) 페이드, 남 = 기준선 위 하늘 제거, 서·동 = 불투명
  7. 광원: 발광 마스크 덩어리 → lights[] (띠 국소 논리 px)
"""
import argparse, json, math, os, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
GEM = os.path.dirname(HERE)
sys.path.insert(0, GEM)
import gkit as K  # noqa: E402

ROOT = K.ROOT
OUT = os.path.join(ROOT, "assets/tiles/border/outer")
PS = 0.5                    # pixelScale: 저장 px 1 = 논리 px 0.5
KS = 0.8                    # 원본 1px → 저장 0.8px (모든 띠 같은 축척 → 건물·술통 크기 통일)

# ---------------------------------------------------------------------------
# 띠 정의 (원본 좌표 = raw jpg 픽셀)
# ---------------------------------------------------------------------------
BANDS = {
    "north": dict(parts=[("raw_north_a.jpg", (0, 0, 4128, 1024)), ("raw_north_b.jpg", (176, 0, 3936, 1024))],
                  join_overlap=40, wrap="x", wrap_overlap=56,
                  baseline_src=942,            # 집 앞면 밑변(원본 y) — 두 장 공통
                  curve="wall"),
    "west": dict(parts=[("raw_west_a.jpg", (384, 0, 1024, 4128))], wrap="y", wrap_overlap=72, curve="wall"),
    "east": dict(parts=[("raw_east_a.jpg", (0, 0, 640, 4128))], wrap="y", wrap_overlap=72, curve="wall"),
    # 남쪽: c 채택(처마선이 끊기지 않음). c 아래 절반(원본 y>340)은 위 절반의 잔상이라 쓰지 않는다.
    # b(지붕선 들쭉날쭉 → 하늘 틈이 기준선 아래로 내려와 검은 판이 됨)는 비교안으로만 보관.
    "south": dict(parts=[("raw_south_c.jpg", (0, 0, 5856, 340))], wrap="x", wrap_overlap=64,
                  baseline_src=64,             # 바닥 남쪽 끝과 맞닿는 선(원본 y). 용마루·처마 ≈ 44 → 겹침 약 8논리 px, 굴뚝은 더 위
                  bottom_fade=56,              # 띠 아래 끝 저장 px — 바깥 어둠으로
                  curve="fore"),
}

# 명도 곡선(8bit 루마 in → out). wall = 바닥 알베도(평균 64)의 약 0.85 배, 하이라이트 압축.
CURVES = {
    "wall": [(0, 0), (20, 26), (40, 50), (70, 74), (100, 90), (150, 104), (255, 118)],
    "fore": [(0, 0), (20, 19), (40, 36), (70, 52), (110, 64), (255, 76)],   # 전경: 어둡게(실루엣 + 테 하이라이트)
}
EMIT_DARK = 0.30            # 발광 자리 알베도 배율(빛은 emissive 가 더함)


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


def emit_strength(c):
    """밝고 따뜻한 픽셀 = 발광(창·문빛·등불). 0..1"""
    lum = _luma(c)
    warm = c[0] - c[2]
    a = max(0.0, min(1.0, (lum - 100) / 55))
    b = max(0.0, min(1.0, (warm - 55) / 45))
    return a * b


def make_luts(curve):
    pts = CURVES[curve]

    def tone(r, g, b):
        t = _tone_rgb((r * 255, g * 255, b * 255))
        return tuple(v / 255 for v in t)

    def albedo(r, g, b):
        c = (r * 255, g * 255, b * 255)
        t = _tone_rgb(c)
        l0 = max(1e-3, _luma(t))
        k = _curve(pts, l0) / l0
        e = emit_strength(c)
        k *= (1 - e) + e * EMIT_DARK
        return tuple(max(0.0, min(1.0, v * k / 255)) for v in t)

    def emit(r, g, b):
        e = emit_strength((r * 255, g * 255, b * 255))
        return (e, e, e)
    gen = ImageFilter.Color3DLUT.generate
    return gen(33, tone), gen(33, albedo), gen(33, emit)


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
def detect_lights(emit_l, tone_rgb, cell=8, thr=0.18, min_cells=2, wrap=None):
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
            # 색은 램프 쪽으로 밝힌다(창 안쪽 평균색 → 광원색)
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


def light_radius(area):
    """발광 면적(논리 px²) → 반경. 창 ≈ 500 → 110, 문·등불 ≥ 1500 → 150(상한). 2회차 비평: 면적 합으로 창도 170 이 되던 문제."""
    return int(max(50, min(150, 40 + 3.2 * math.sqrt(area))))


def light_int(area):
    return round(max(0.4, min(0.95, 0.4 + 0.015 * math.sqrt(area))), 2)


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


# ---------------------------------------------------------------------------
# 띠 빌드
# ---------------------------------------------------------------------------
def load_part(fn, box):
    im = Image.open(os.path.join(HERE, fn)).convert("RGB").crop(box)
    w, h = round(im.width * KS), round(im.height * KS)
    w -= w % 2
    h -= h % 2
    return im.resize((w, h), Image.LANCZOS)


def build_band(name, cfg):
    parts = [load_part(fn, box) for fn, box in cfg["parts"]]
    if len(parts) > 1:
        H = min(p.height for p in parts)
        parts = [p.crop((0, 0, p.width, H)) for p in parts]
        src = parts[0]
        for p in parts[1:]:
            src = join_h(src, p, cfg["join_overlap"])
    else:
        src = parts[0]
    before = seam_err_h(src) if cfg["wrap"] == "x" else seam_err_h(src.transpose(Image.Transpose.TRANSPOSE))
    src = wrap_h(src, cfg["wrap_overlap"]) if cfg["wrap"] == "x" else wrap_v(src, cfg["wrap_overlap"])
    if src.width % 2:
        src = src.crop((0, 0, src.width - 1, src.height))
    if src.height % 2:
        src = src.crop((0, 0, src.width, src.height - 1))
    after = seam_err_h(src) if cfg["wrap"] == "x" else seam_err_h(src.transpose(Image.Transpose.TRANSPOSE))

    lut_tone, lut_alb, lut_emit = make_luts(cfg["curve"])
    tone = src.filter(lut_tone)
    alb = src.filter(lut_alb)
    emit = src.filter(lut_emit).convert("L").filter(ImageFilter.GaussianBlur(0.8))

    W, H = src.size
    alpha = Image.new("L", (W, H), 255)
    info = {}
    if name == "north":
        base = round(cfg["baseline_src"] * KS)
        base -= base % 2
        ap = alpha.load()
        for y in range(base, H):
            t = (y - base) / max(1, H - 1 - base)
            v = int(255 * max(0.0, 1 - t) ** 1.6) if y > base + 4 else 255
            for x in range(W):
                ap[x, y] = v
        info["baselineY"] = base * PS
        info["apronBelow"] = (H - base) * PS
    elif name == "south":
        base = round(cfg["baseline_src"] * KS)
        base -= base % 2
        alpha = sky_alpha(src, base)
        info["baselineY"] = base * PS
    # 발광 = 톤 맞춘 원색 × 마스크 (가산용, 알파에 세기)
    emit = ImageChops.multiply(emit, alpha)
    em = tone.copy().convert("RGBA")
    em.putalpha(emit)
    out = alb.convert("RGBA")
    out.putalpha(alpha)
    if cfg.get("bottom_fade"):
        f = cfg["bottom_fade"]
        g = Image.new("L", (1, H), 0)
        for y in range(H - f, H):
            g.putpixel((0, y), int(255 * ((y - (H - f)) / f) ** 1.2))
        g = g.resize((W, H))
        voidc = Image.new("RGBA", (W, H), (14, 15, 20, 255))
        voidc.putalpha(out.getchannel("A"))
        out = Image.composite(voidc, out, g)
        em.putalpha(ImageChops.multiply(em.getchannel("A"), ImageChops.invert(g)))
    if name == "south":
        # 기준선 아래 하늘 빛깔(뚫린 틈)은 어두운 골목으로 — 알베도에 이미 곡선이 걸려 있으므로 남은 회색 평면을 더 누름
        out = crush_sky_below(src, out, base)
    info.update(seamBefore=before, seamAfter=after)
    return out, em, tone, emit, info


def sky_alpha(src, base):
    """남쪽 띠: 기준선 위에서 위쪽 가장자리와 이어진 '하늘색' 영역을 투명으로."""
    W, H = src.size
    px = src.load()
    # 하늘 기준색: 맨 위 몇 줄 평균
    acc = [0, 0, 0]
    n = 0
    for x in range(0, W, 5):
        for y in range(2, 14, 3):
            c = px[x, y]
            acc = [a + v for a, v in zip(acc, c)]
            n += 1
    sky = [a / n for a in acc]
    edges = src.convert("L").filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3)).load()
    a = Image.new("L", (W, H), 255)
    ap = a.load()
    # 열마다 위에서 아래로: 하늘과 비슷하고 윤곽이 약하면 투명 — 처음 '물체'를 만나면 멈춤(아래는 불투명)
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
    a = a.filter(ImageFilter.MedianFilter(5))
    return a


def crush_sky_below(src, out, base):
    """기준선 아래로 이어지는 '하늘 틈'(위 하늘과 맞닿은 하늘색 영역)만 어두운 골목으로 누른다.
    평지붕 납판처럼 하늘과 색이 비슷해도 이어지지 않은 곳은 건드리지 않는다(1회차 비평: 얼룩)."""
    W, H = src.size
    px = src.load()
    acc = [0, 0, 0]
    n = 0
    for x in range(0, W, 5):
        for y in range(2, 14, 3):
            acc = [a + v for a, v in zip(acc, px[x, y])]
            n += 1
    sky = [a / n for a in acc]
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


def band_lights(name, emit, tone, W, H):
    L = detect_lights(emit, tone)
    L = merge_lights(L, 26)
    for l in L:
        # 띠마다 깜빡임: 창 = 거의 없음, 등불·문빛(큰 덩어리) = 약하게
        big = l["areaPx"] >= 1200
        l["flicker"] = {"amp": 0.08 if big else 0.04, "hz": 3}
        l["kind"] = "door_or_lantern" if big else "window"
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-mock", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    meta = {}
    imgs = {}
    for name, cfg in BANDS.items():
        out, em, tone, emit, info = build_band(name, cfg)
        out.save(os.path.join(OUT, f"{name}.png"), optimize=True)
        nz = em.getchannel("A").point(lambda v: 255 if v > 2 else 0)
        em = Image.composite(em, Image.new("RGBA", em.size, (0, 0, 0, 0)), nz)   # 알파 0 자리 색 비움(용량)
        em.save(os.path.join(OUT, f"{name}_emissive.png"), optimize=True)
        W, H = out.size
        lights = band_lights(name, emit, tone, W, H)
        meta[name] = dict(info, size=(W, H), lights=lights)
        imgs[name] = (out, em)
        print(name, (W, H), "logical", (W * PS, H * PS), "lights", len(lights), "seam", info["seamBefore"], "->", info["seamAfter"])
    write_json(meta)
    json.dump({k: {kk: vv for kk, vv in v.items() if kk != "lights"} for k, v in meta.items()},
              open(os.path.join(HERE, "build_info.json"), "w"), ensure_ascii=False, indent=1)
    if not a.no_mock:
        import mock
        mock.run()


def write_json(meta):
    n, s, w, e = (meta[k] for k in ("north", "south", "west", "east"))

    def lg(v):
        return v * PS

    def L(lst):
        return [{k: v for k, v in l.items() if k != "areaPx"} for l in lst]
    data = {
        "region": "outer", "stage": 1, "version": "53라운드 시범 (Gemini 테두리)",
        "source": "parts/art/work/gemini/border_outer/build.py (원본·프롬프트 같은 폴더)",
        "pixelScale": PS,
        "units": "모든 길이·좌표 = 논리 px(960×540 기준). 이미지 픽셀 = 논리 px / pixelScale(=2배). 1920 렌더에서 1:1.",
        "lighting": "albedo 는 바닥 v2 타일과 같은 조명 공간(곱하기 조명을 받는다). *_emissive.png 는 조명 뒤 가산(알파 = 세기, 어둠에 묻히지 않음). lights[] 는 띠 국소 좌표의 광원 — 반복 띠는 주기마다 반복 등록.",
        "lightsRule": "lights[] 좌표 = 띠 이미지 왼쪽 위 기준 논리 px. 반복 띠는 주기마다 등록. 서·동 띠 광원 중 바닥 세로 범위(북쪽 기준선 ~ 남쪽 기준선) 밖에 오는 것은 다른 띠에 가려지므로 등록하지 않는다. flicker 는 계약 §12 형식.",
        "drawOrder": ["floor", "floorDecals+floorShadows", "west", "east", "north", "ySorted(props, characters, fx)", "south", "lighting", "emissive(add)", "ui"],
        "bands": {
            "north": {
                "image": "north.png", "emissive": "north_emissive.png",
                "width": lg(n["size"][0]), "height": lg(n["size"][1]),
                "repeat": "x", "anchor": "floorTop",
                "baselineY": n["baselineY"], "apronBelow": n["apronBelow"],
                "place": "띠의 baselineY 줄 = 바닥 북쪽 끝(북쪽 벽 앞면 아랫단의 밑변). x 는 (바닥 왼쪽 - west.width) 부터 반복해 (바닥 오른쪽 + east.width) 까지 덮는다.",
                "apron": "baselineY 아래 apronBelow 는 포석·술통 밑동이 알파로 사라지는 앞치마 — 바닥 위에 겹쳐 그린다(충돌 없음).",
                "depth": "background", "lights": L(n["lights"]),
            },
            "south": {
                "image": "south.png", "emissive": "south_emissive.png",
                "width": lg(s["size"][0]), "height": lg(s["size"][1]),
                "repeat": "x", "anchor": "floorBottom",
                "baselineY": s["baselineY"],
                "place": "띠의 baselineY 줄 = 바닥 남쪽 끝. 그 위(0~baselineY)는 처마·굴뚝이 바닥을 덮는 겹침(투명 하늘 제외).",
                "depth": "foreground",
                "occlusion": {"fadeAlpha": 0.45, "rule": "플레이어 몸 사각형이 띠의 불투명 픽셀과 겹치면 띠 전체(또는 그 구간)를 fadeAlpha 로 반투명"},
                "lights": L(s["lights"]),
            },
            "west": {
                "image": "west.png", "emissive": "west_emissive.png",
                "width": lg(w["size"][0]), "height": lg(w["size"][1]),
                "repeat": "y", "anchor": "floorLeft", "baselineX": lg(w["size"][0]),
                "place": "띠의 오른쪽 끝(baselineX) = 바닥 서쪽 끝(서쪽 벽 칸의 동쪽 변). y 는 북쪽 띠 위끝부터 남쪽 띠 아래끝까지 반복(북쪽 띠·남쪽 띠가 위에 덮임).",
                "depth": "background", "lights": L(w["lights"]),
            },
            "east": {
                "image": "east.png", "emissive": "east_emissive.png",
                "width": lg(e["size"][0]), "height": lg(e["size"][1]),
                "repeat": "y", "anchor": "floorRight", "baselineX": 0,
                "place": "띠의 왼쪽 끝 = 바닥 동쪽 끝. 나머지는 west 와 같음.",
                "depth": "background", "lights": L(e["lights"]),
            },
        },
        "corners": "별도 모서리 그림 없음 — north·south 가 좌우 띠 폭까지 덮는다(그리기 순서로 해결).",
        "collision": "충돌은 기존 격자 그대로(벽 칸 = 막힘). 테두리 그림은 벽 칸 위에 덮는 그림일 뿐이며, 테두리가 있는 지역에서는 벽 타일(앞면·윗면·가장자리)을 그리지 않는다. 문·출구 칸은 아래 미정 항목.",
        "camera": {"bounds": {"top": -n["baselineY"], "bottom": "floorBottom + %g" % (lg(s["size"][1]) - s["baselineY"]), "left": -200, "right": "floorRight + 200"}, "northLookUp": 110, "note": "제안(임시, 인터뷰 대상): 위 = 북쪽 띠 위끝(바닥 북쪽 끝 기준 -baselineY), 아래 = 남쪽 띠 아래끝, 좌우 = 바닥 끝 ± 200(띠 폭 256 중 바깥 56 은 화면 밖). northLookUp: 주인공이 북쪽 끝에서 200 이내면 카메라 중심을 최대 110 위로 끌어 집 위층·지붕이 보이게."},
        "open": ["문·출구가 벽에 뚫릴 때 테두리 표현(53라운드 시범 NOTES 인터뷰 Q)"],
    }
    path = os.path.join(OUT, "border.json")
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
