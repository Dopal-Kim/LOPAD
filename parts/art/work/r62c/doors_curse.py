"""62 루프 3 (P17 묶음 B) — 위험 노드 '저주 길' 입구 그림 `paint/door_<지역>_curse.png` (640×360, §28 형식).

Gemini 402 → Claude 직접: 같은 지역 전투 입구 그림(61 단계 6 붓 그림)을 바탕으로
  1) 호박 강조를 눌러 차갑게(저주 — 불이 꺼져 가는 곳),
  2) 입구 안 빛을 '귀' 램프(floors[4], 둘째 강조 축 — 엘리트의 '적' 램프와 같은 규칙)로 바꾸고,
  3) 입구를 가로지르는 처진 줄에 부적(바랜 종이·먹 획) · 끊어진 쇠사슬 · 귀불(도깨비불) 셋을 2px 덩어리 도트로 덧그린다.
  입구 안쪽(doorRect) 가운데는 비워 둔다(§28: 입구 앞을 가리지 않음 — 부적 줄은 위 테 가까이만).
bundle2 위험 '저주': '들어서면 저주 하나를 반드시 받는다. 그 값으로 귀한 유품이 놓여 있다.' → 입구 안 깊은 곳에 귀불에 비친 유품 받침(희미한 금 한 점).
"""
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from c62 import AMB, GHOST, GRAY, PAINT, SRC, lerp, load_json, save_json

CURSE_OF = {"outer": "door_outer_battle", "brewery": "door_brewery_battle"}


def cool(im, keep=0.25):
    """호박 채도를 keep 만 남기고 명도는 그대로(재 회색 쪽으로)."""
    px = im.load()
    w, h = im.size
    out = Image.new("RGB", im.size)
    po = out.load()
    cache = {}
    for y in range(h):
        for x in range(w):
            c = px[x, y][:3]
            r = cache.get(c)
            if r is None:
                L = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
                r = tuple(int(round(L + (v - L) * keep)) for v in c)
                cache[c] = r
            po[x, y] = r
    return out


def ghost_glow(size, cx, cy, rx, ry, amount=0.7):
    g = Image.new("RGB", size, (0, 0, 0))
    d = ImageDraw.Draw(g)
    for i in range(20, 0, -1):
        t = i / 20
        a = amount * (1 - t) ** 1.7
        col = lerp(GHOST[3], GHOST[6], (1 - t) ** 2)
        d.ellipse((cx - rx * t, cy - ry * t, cx + rx * t, cy + ry * t), fill=tuple(int(c * a) for c in col))
    return g.filter(ImageFilter.GaussianBlur(min(rx, ry) * 0.3))


def talisman(d, x, y, h, seed, wcells=5):
    """부적 한 장(2px 도트): 폭 wcells 칸, 높이 h칸. 바랜 종이 + 먹 획 + 봉인 점 + 아래 찢김. 글자 아님(무늬)."""
    P = 2
    paper = [GRAY[8], GRAY[10], GRAY[11]]
    tear = [(seed * 7 + i * 3) % 3 for i in range(wcells)]
    for j in range(h):
        for i in range(wcells):
            if j >= h - tear[i]:
                continue                                    # 찢긴 아래
            c = paper[1]
            if i == 0 or j == 0:
                c = paper[2]
            if i == wcells - 1:
                c = paper[0]
            if (i * 5 + j * 3 + seed) % 11 == 0:
                c = paper[0]                                # 얼룩
            d.rectangle((x + i * P, y + j * P, x + i * P + P - 1, y + j * P + P - 1), fill=c)
    ink = GRAY[2]
    mid = x + (wcells // 2) * P
    for j in range(3, h - 3):
        d.rectangle((mid, y + j * P, mid + P - 1, y + j * P + P - 1), fill=ink)
    for j in (4 + seed % 2, 7 + seed % 3, h - 4):
        if j < h - 3:
            d.rectangle((x + 1 * P, y + j * P, x + (wcells - 1) * P - 1, y + j * P + 1), fill=ink)
    if seed % 2:
        d.rectangle((mid - P, y + (h - 5) * P, mid - 1, y + (h - 4) * P - 1), fill=ink)
    # 봉인 도장(귀 램프 짙은 칸) 2×2칸
    d.rectangle((mid - P // 2 - 1, y + 1 * P, mid + P + P // 2 - 2, y + 2 * P + P - 1), fill=GHOST[4])
    d.rectangle((mid, y + 1 * P + 1, mid + 1, y + 2 * P), fill=GHOST[6])


def hang(d, x, y, length, h, seed, wcells=5):
    """줄에 실로 매단 부적."""
    for k in range(0, length, 2):
        d.rectangle((x, y + k, x + 1, y + k + 1), fill=GRAY[6])
    talisman(d, x - (wcells // 2) * 2, y + length, h, seed, wcells)


def rope(d, x0, x1, y, sag, col):
    pts = []
    n = max(2, int((x1 - x0) / 2))
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + (x1 - x0) * t, y + sag * 4 * t * (1 - t)))
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        d.rectangle((int(ax) // 2 * 2, int(ay) // 2 * 2, int(ax) // 2 * 2 + 1, int(ay) // 2 * 2 + 1), fill=col)
    return pts


def chain(d, x, y, n, dx=0):
    """세로로 늘어진 끊어진 쇠사슬(2px 고리 번갈이)."""
    for k in range(n):
        cx = x + int(dx * k / max(1, n))
        cy = y + k * 5
        if k % 2 == 0:
            d.rectangle((cx, cy, cx + 3, cy + 5), outline=GRAY[6])
            d.point((cx + 1, cy + 1), fill=GRAY[9])
        else:
            d.rectangle((cx + 1, cy, cx + 2, cy + 5), fill=GRAY[5])


def wisp(im, x, y, r, amount=0.9):
    """귀불: 둥근 머리 + 위로 흔들리는 꼬리, 가운데 흰빛(2px 도트)."""
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for k in range(5):
        t = k / 5
        rr = r * (1 - t * 0.75)
        cx = x + math.sin(k * 1.3) * 2
        cy = y - k * r * 0.7
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=GHOST[6 + min(2, k // 2)] + (int(200 * (1 - t)),))
    d.ellipse((x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45), fill=GHOST[10] + (255,))
    small = lay.resize((im.size[0] // 2, im.size[1] // 2), Image.NEAREST).resize(im.size, Image.NEAREST)
    glow = Image.new("RGB", im.size, (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(10, 0, -1):
        t = i / 10
        a = amount * 0.5 * (1 - t) ** 2
        gd.ellipse((x - r * 4 * t, y - r * 4 * t, x + r * 4 * t, y + r * 4 * t), fill=tuple(int(c * a) for c in GHOST[5]))
    base = ImageChops.screen(im.convert("RGB"), glow.filter(ImageFilter.GaussianBlur(r)))
    out = base.convert("RGBA")
    out.alpha_composite(small)
    return out


def build_one(region):
    base_name = CURSE_OF[region]
    meta0 = load_json(os.path.join(PAINT, base_name + ".json"))
    im = Image.open(os.path.join(PAINT, base_name + ".png")).convert("RGB")
    dr = meta0["doorRect"]
    x0, y0, w0, h0 = dr["x"], dr["y"], dr["w"], dr["h"]
    cx, cy = x0 + w0 / 2, y0 + h0 / 2
    im = cool(im, 0.22)
    # 입구 안: 깊은 귀불 빛 + 유품 받침 금 한 점
    im = ImageChops.screen(im, ghost_glow(im.size, cx, y0 + h0 * 0.62, w0 * 0.42, h0 * 0.36, 0.75))
    d = ImageDraw.Draw(im)
    px, py = int(cx) // 2 * 2, int(y0 + h0 * 0.70) // 2 * 2
    d.rectangle((px - 6, py, px + 5, py + 3), fill=GRAY[3])                 # 받침
    d.rectangle((px - 4, py - 2, px + 3, py - 1), fill=GRAY[4])
    d.rectangle((px - 2, py - 6, px + 1, py - 3), fill=AMB[6])              # 유품(금빛 한 점)
    d.rectangle((px - 2, py - 6, px - 1, py - 5), fill=AMB[10])
    # 부적 줄: 입구 위 테 바로 아래, 양 기둥에 걸쳐 처짐
    ry = y0 + 4
    pts = rope(d, x0 - 18, x0 + w0 + 18, ry, h0 * 0.10, GRAY[7])
    rope(d, x0 - 12, x0 + w0 + 12, ry - 8, h0 * 0.06, GRAY[6])
    n = max(3, int(w0 / 28))
    for k in range(n):
        t = (k + 0.5) / n
        i = int(t * (len(pts) - 1))
        tx, ty = pts[i]
        hang(d, int(tx) // 2 * 2, int(ty) // 2 * 2, 2 + (k * 6) % 8, 11 + (k * 5) % 5, k)
    # 기둥 양옆 긴 부적 · 끊어진 쇠사슬
    for side, sx in ((0, x0 - 20), (1, x0 + w0 + 8)):
        talisman(d, int(sx) // 2 * 2, int(y0 + h0 * 0.22) // 2 * 2, 17, side + 3, 6)
        talisman(d, int(sx) // 2 * 2 + (-4 if side == 0 else 6), int(y0 + h0 * 0.22 + 40) // 2 * 2, 10, side + 5, 5)
    chain(d, int(x0 + 6), int(ry + h0 * 0.08), 9, dx=2)
    chain(d, int(x0 + w0 - 10), int(ry + h0 * 0.10), 6, dx=-2)
    # 귀불 셋(입구 앞 바닥 위·양옆)
    out = im.convert("RGBA")
    for (fx, fy, r) in ((x0 - 40, y0 + h0 * 0.82, 7), (x0 + w0 + 36, y0 + h0 * 0.66, 8), (cx + 10, y0 + h0 + 16, 5)):
        out = wisp(out, int(fx), int(fy), r)
    name = f"door_{region}_curse"
    out.save(os.path.join(PAINT, name + ".png"), optimize=True)
    light = {"color": "#9c58c0", "intensity": 0.5,
             "note": "입구 안 빛 색(아트 제안) — 귀불(‘귀’ 램프 floors[4]). 저주 길은 호박을 눌러 차갑게"}
    meta = {
        "image": name + ".png", "width": 640, "height": 360, "pixelScale": 1.0,
        "region": region, "nodeKind": "curse", "risk": "curse", "nameKo": "부적으로 봉한 문(저주 길)",
        "doorRect": dict(dr), "doorCenter": dict(meta0["doorCenter"]),
        "doorRectNote": meta0.get("doorRectNote"),
        "light": light,
        "palette": "바탕 = " + base_name + " (무채 + 1층 램프, 호박 채도 0.22 로 눌림) + '귀' 램프(floors[4]) 귀불·봉인 도장 — 둘째 강조 축(엘리트 '적' 과 같은 규칙)",
        "source": SRC + " · doors_curse.py (Claude 직접 — Gemini 402; 바탕 " + base_name + ".png)",
        "design": "부적 줄(입구 위 테) · 기둥 양옆 긴 부적 · 끊어진 쇠사슬 · 귀불 셋 · 입구 안 유품 받침(금 한 점 — '그 값으로 귀한 유품')",
    }
    save_json(os.path.join(PAINT, name + ".json"), meta)
    return name, meta


def build():
    return [build_one(r) for r in CURSE_OF]
