"""62 루프 3 (P17 묶음 B) — 노드 지도 미리보기 카드용 입구 그림 `paint/door_<지역>_<종류>_small.png`.

UI 계약 §25: 미리보기 카드 256×144(논리), 렌더 배율 res 2 → 텍스처 512×288 을 1/2 로 그린다(1920 렌더에서 1:1).
그래서 '작은 판'은 512×288 = 원본 640×360 에서 **입구 둘레를 1:1 로 잘라낸 것**(재표본 없음 — 도트가 뭉개지지 않는다)에
밝기·대비를 한 단 올리고, 입구 빛을 조금 키운 판이다.

- 자르기: 입구 가운데(doorCenter)를 가로 가운데, 세로 42% 자리에 둔다(카드 아래 먹 띠가 그림 아래쪽 ~35%를 덮으므로 입구를 위로).
  가장자리에서 멈춘다(640×360 안).
- 보정(무채 축 유지 — 채도를 새로 만들지 않음): 명도 곡선(어둠 들어 올림 · 중간 대비) → 입구 빛 번짐(문 안 빛 색, screen) →
  가장자리 살짝 어둡게(카드 테와 떨어지게) → 날 세우기(unsharp, 작게).
- 종류 표식(kind cue)은 원본 그림이 이미 갖고 있다(사연 = 사당 문·초·제물, 장터 = 등불·간판, 쉼터 = 동굴 속 모닥불, 정예 = 붉은 깃발,
  군주의 방 = 연회장 큰 문). 작은 판은 그 표식이 먹 띠 위에 오도록 자르고 빛을 올린다 — `cue` 는 메타 기록용.
"""
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from c62 import AMB, PAINT, SRC, clamp, hx, load_json, save_json

W, H = 512, 288
DOOR_Y = 0.42

# 명도 곡선(0..255 → 0..255): 어둠 들어 올림, 중간 대비, 밝은 쪽은 거의 그대로
CURVE = [(0, 6), (16, 22), (40, 52), (72, 92), (110, 134), (160, 182), (210, 222), (255, 255)]

# 종류 표식(메타) · 입구 빛 세기(작은 판에서 더하는 양 0..1) · 반경(입구 대각 대비)
KIND_CUE = {
    "battle": ("부서진 무기·잔해 앞 어두운 입구", 0.18, 0.9),
    "elite": ("붉은 깃발·횃불 — 위협 표식", 0.26, 1.0),
    "event": ("사당 문·초·제물 — 인물·소품", 0.22, 0.9),
    "shop": ("문 옆 등불·간판 — 노점 불빛", 0.30, 1.1),
    "rest": ("동굴 속 모닥불", 0.32, 0.8),
    "boss": ("연회장 큰 문·잔 문장", 0.24, 1.2),
    "curse": ("부적·쇠사슬로 봉한 문, 귀불 — 저주 표식", 0.26, 1.0),
    "training": ("수련장 문", 0.12, 0.8),
}


def _lut():
    out = []
    for v in range(256):
        for (a, b), (c, d) in zip(CURVE, CURVE[1:]):
            if v <= c:
                out.append(int(round(b + (d - b) * (v - a) / max(1, c - a))))
                break
    return out


LUT = _lut()


def tone(im):
    """명도 곡선을 색조 보존으로: 휘도 비율로 RGB 를 함께 올린다."""
    rgb = im.convert("RGB")
    px = rgb.load()
    out = Image.new("RGB", rgb.size)
    po = out.load()
    cache = {}
    w, h = rgb.size
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            r = cache.get(c)
            if r is None:
                L = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
                L2 = LUT[int(L)]
                k = L2 / L if L > 0.5 else 0
                if k == 0:
                    r = (L2, L2, L2)
                else:
                    r = tuple(min(255, int(round(v * k))) for v in c)
                cache[c] = r
            po[x, y] = r
    return out


def glow_layer(size, cx, cy, rad, color, amount):
    """입구 빛 번짐(screen 합성용) — 가운데 color×amount 에서 바깥 0."""
    w, h = size
    g = Image.new("RGB", size, (0, 0, 0))
    d = ImageDraw.Draw(g)
    steps = 24
    for i in range(steps, 0, -1):
        t = i / steps
        r = rad * t
        a = amount * (1 - t) ** 1.6
        col = tuple(int(c * a) for c in color)
        d.ellipse((cx - r, cy - r * 0.9, cx + r, cy + r * 0.9), fill=col)
    return g.filter(ImageFilter.GaussianBlur(rad * 0.3))


def glow_color(h):
    """입구 빛 번짐 색: 옅은 호박(#e8b858·#eecc78·#f4de9b)을 회색 위에 screen 하면 올리브로 뜬다 → 진한 호박 쪽으로."""
    c = hx(h)
    if c[0] > 200 and c[1] > 150:          # 옅은 호박·금
        return AMB[5]
    return c


def vignette(im, strength=0.22):
    w, h = im.size
    m = Image.new("L", (w, h), 0)
    px = m.load()
    for y in range(h):
        for x in range(w):
            dx = (x - w / 2) / (w / 2)
            dy = (y - h / 2) / (h / 2)
            d = math.sqrt(dx * dx * 0.8 + dy * dy * 1.0)
            px[x, y] = int(255 * clamp((d - 0.72) / 0.5, 0, 1) * strength)
    dark = Image.new("RGB", (w, h), (10, 10, 12))
    return Image.composite(dark, im, m)


def crop_box(meta):
    cx = meta["doorCenter"]["x"]
    cy = meta["doorCenter"]["y"]
    sw, sh = meta["width"], meta["height"]
    left = int(clamp(round(cx - W / 2), 0, sw - W))
    top = int(clamp(round(cy - DOOR_Y * H), 0, sh - H))
    return left, top


def make_small(name, overlay=None):
    """name = 'door_outer_event' (확장자 없이). overlay(im, meta, box) → im 이 있으면 보정 뒤에 덧그린다."""
    meta = load_json(os.path.join(PAINT, name + ".json"))
    src = Image.open(os.path.join(PAINT, name + ".png")).convert("RGB")
    left, top = crop_box(meta)
    im = src.crop((left, top, left + W, top + H))
    im = tone(im)
    kind = meta.get("nodeKind", "battle")
    cue, amount, radk = KIND_CUE.get(kind, KIND_CUE["battle"])
    dr = meta["doorRect"]
    dcx = dr["x"] + dr["w"] / 2 - left
    dcy = dr["y"] + dr["h"] / 2 - top
    rad = math.hypot(dr["w"], dr["h"]) * radk
    light = glow_color(meta["light"]["color"])
    if kind == "training":
        im = Image.blend(src.crop((left, top, left + W, top + H)), im, 0.3)
    im = ImageChops.screen(im, glow_layer(im.size, dcx, dcy, rad, light, amount))
    im = vignette(im)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=40, threshold=2))
    if overlay:
        im = overlay(im, meta, (left, top))
    out = im.convert("RGBA")
    out.save(os.path.join(PAINT, name + "_small.png"), optimize=True)
    small = {
        "image": name + "_small.png", "width": W, "height": H, "pixelScale": 1.0,
        "smallOf": name, "region": meta.get("region"), "nodeKind": kind, "nameKo": meta.get("nameKo"),
        "use": "UI 계약 §25 지도 미리보기 카드(256×144 논리, res 2 → 512×288 텍스처를 1/2 로) — 원본을 1:1 로 자른 판이라 'cover' 맞춤이면 재표본 없음",
        "crop": {"x": left, "y": top, "w": W, "h": H, "scale": 1.0, "note": "원본 640×360 좌표에서 잘라낸 사각형"},
        "doorRect": {"x": dr["x"] - left, "y": dr["y"] - top, "w": dr["w"], "h": dr["h"]},
        "doorCenter": {"x": int(round(dcx)), "y": int(round(dcy))},
        "light": meta["light"],
        "cue": cue,
        "grade": "명도 곡선(어둠 들어 올림) + 입구 빛 번짐 %.2f + 가장자리 어둡게 0.22 + unsharp 1.0/40" % amount,
        "source": SRC + " · doors_small.py (원본 " + name + ".png)",
    }
    save_json(os.path.join(PAINT, name + "_small.json"), small)
    return out, small
