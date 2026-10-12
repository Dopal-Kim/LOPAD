"""62a — 먹 붓 획 스탬프 시트 `ritual/ink_brush` (UI 가 3획·이름 붓글씨를 그릴 때 찍는 붓 자국).

도트 단위(1 도트 = back_canvas 도트 = 1920 렌더 3px). 모든 칸 흰색(255) 몸만 — UI 가 tint 로 색을 입힌다
(먹 = G01 #141516 / 불씨 먹 = 호박 #e8b858 + ADD 할로). 알파는 0/255 만(반투명 없음, 최근접 확대).
종류:
- tip_d{2,3,4,5,6,8,10}   둥근 붓끝(가장자리 들쭉날쭉) — 획 몸통을 1~2 도트 간격으로 찍는다(굵기 = 속도·누름에 따라).
- press_d{6,8,10}         누름(획 시작 먹 고임, 번진 가시) — 획 첫 점에 1회.
- dry_d{4,6,8}_r{0..7}    마른 붓 털 자국(털 줄 사이 빈틈) — 빠른 구간·끝 구간에 tip 대신. r = 진행 방향 45° 단위(0 = 오른쪽, 2 = 아래).
- flick_r{0..7}           삐침(끝이 가늘어지며 빠지는 꼬리, 길이 18) — 획 마지막 점에 진행 방향으로 1회.
- splat_{0..3}            먹 튐(작은 점 무리) — 빠른 획 끝·누름 옆에 선택.
"""
import math
import random

from PIL import Image

WHITE = (255, 255, 255, 255)
EDGE = (176, 176, 176, 255)
CLEAR = (0, 0, 0, 0)

DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def _finish(cells):
    """몸 가장자리 1도트 = EDGE(젖은 가장자리)."""
    for im in cells.values():
        p = im.load()
        w, h = im.size
        edge = []
        for y in range(h):
            for x in range(w):
                if p[x, y][3] == 0:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < w and 0 <= yy < h) or p[xx, yy][3] == 0:
                        edge.append((x, y))
                        break
        for (x, y) in edge:
            p[x, y] = EDGE
    return cells


def tip(d, seed):
    s = d + 4
    im = Image.new("RGBA", (s, s), CLEAR)
    p = im.load()
    r = random.Random(seed)
    c = (s - 1) / 2.0
    rad = d / 2.0
    jag = [r.uniform(-0.45, 0.25) for _ in range(16)]
    for y in range(s):
        for x in range(s):
            a = math.atan2(y - c, x - c)
            k = int((a + math.pi) / (2 * math.pi) * 16) % 16
            if math.hypot(x - c, y - c) <= rad + jag[k] * (0.5 + d / 12.0):
                p[x, y] = WHITE
    return im


def press(d, seed):
    """누름: 조금 납작한 먹 고임 + 가장자리에 붙은 짧은 번짐 가시 3~5."""
    s = d + 8
    im = Image.new("RGBA", (s, s), CLEAR)
    p = im.load()
    r = random.Random(seed)
    c = (s - 1) / 2.0
    rad = d / 2.0 + 0.5
    ph = [r.uniform(0, 2 * math.pi) for _ in range(3)]
    for y in range(s):
        for x in range(s):
            a = math.atan2(y - c, x - c)
            rr = rad * (1 + 0.10 * math.sin(2 * a + ph[0]) + 0.07 * math.sin(3 * a + ph[1]) + 0.05 * math.sin(5 * a + ph[2]))
            if math.hypot((x - c) * 0.92, (y - c) * 1.08) <= rr:
                p[x, y] = WHITE
    for _ in range(3 + d // 4):
        a = r.uniform(0, 2 * math.pi)
        L = r.uniform(1.5, 3.0)
        k = rad - 1.0
        while k <= rad + L:
            x = int(round(c + math.cos(a) * k))
            y = int(round(c + math.sin(a) * k))
            if 0 <= x < s and 0 <= y < s:
                p[x, y] = WHITE
            k += 0.5
    return im


def dry(d, rot, seed):
    """털 줄 n 개가 진행 방향으로 길이 다르게 — 줄 사이 1도트 빈틈."""
    s = d + 10
    im = Image.new("RGBA", (s, s), CLEAR)
    p = im.load()
    r = random.Random(seed * 13 + rot)
    c = (s - 1) / 2.0
    ang = rot * math.pi / 4
    ux, uy = math.cos(ang), math.sin(ang)
    vx, vy = -uy, ux
    n = max(2, d // 2 + 1)
    for i in range(n):
        off = (i - (n - 1) / 2.0) * (d / max(1, n - 1)) * 0.95 if n > 1 else 0
        L0 = r.uniform(-d * 0.3, 0.0) - 1.5
        L1 = r.uniform(1.5, d * 0.55 + 3)
        if r.random() < 0.25:                 # 끊긴 털
            L1 = r.uniform(0.0, 1.5)
        t = L0
        while t <= L1:
            x = int(round(c + ux * t + vx * off))
            y = int(round(c + uy * t + vy * off))
            if 0 <= x < s and 0 <= y < s:
                p[x, y] = WHITE
            t += 0.5
    return im


def flick(rot, seed, length=18, w0=3.6):
    """삐침: 시작(칸 가운데)이 굵고 진행 방향으로 가늘어지며 살짝 휘어 빠짐 → 끝 두 가닥."""
    s = length * 2 + 8
    im = Image.new("RGBA", (s, s), CLEAR)
    p = im.load()
    r = random.Random(seed + rot)
    c = (s - 1) / 2.0
    ang = rot * math.pi / 4
    ux, uy = math.cos(ang), math.sin(ang)
    vx, vy = -uy, ux
    bend = 3.0 * (1 if rot % 2 == 0 else -1)

    def at(t):
        k = t / length
        return c + ux * t + vx * bend * k * k, c + uy * t + vy * bend * k * k

    t = 0.0
    while t <= length:
        x0, y0 = at(t)
        k = t / length
        w = w0 * (1 - k) ** 1.1 + 0.45
        for yy in range(int(y0 - w - 1), int(y0 + w + 2)):
            for xx in range(int(x0 - w - 1), int(x0 + w + 2)):
                if math.hypot(xx - x0, yy - y0) <= w * 0.6 and 0 <= xx < s and 0 <= yy < s:
                    p[xx, yy] = WHITE
        t += 0.35
    ex, ey = at(length)
    for side in (-1, 1):
        for k in range(1, 5):
            x = int(round(ex + ux * k + vx * side * k * 0.45))
            y = int(round(ey + uy * k + vy * side * k * 0.45))
            if 0 <= x < s and 0 <= y < s and (k < 4 or r.random() < 0.6):
                p[x, y] = WHITE
    return im


def splat(seed):
    s = 20
    im = Image.new("RGBA", (s, s), CLEAR)
    p = im.load()
    r = random.Random(seed)
    for _ in range(r.randint(6, 10)):
        x, y = r.randint(2, s - 3), r.randint(2, s - 3)
        p[x, y] = WHITE
        if r.random() < 0.35:
            p[x + 1, y] = WHITE
            p[x, y + 1] = WHITE
            p[x + 1, y + 1] = WHITE
    return im


def build():
    cells = {}
    for d in (2, 3, 4, 5, 6, 8, 10):
        cells[f"tip_d{d}"] = tip(d, 400 + d)
    for d in (6, 8, 10):
        cells[f"press_d{d}"] = press(d, 420 + d)
    for d in (4, 6, 8):
        for rot in range(8):
            cells[f"dry_d{d}_r{rot}"] = dry(d, rot, 440 + d)
    for rot in range(8):
        cells[f"flick_r{rot}"] = flick(rot, 470)
    for k in range(4):
        cells[f"splat_{k}"] = splat(490 + k)
    # 아주 작은 붓끝(2·3)은 가장자리 회색이 몸을 다 먹으므로 흰 몸 유지
    small = {k: v for k, v in cells.items() if k in ("tip_d2", "tip_d3") or k.startswith("splat") or k.startswith("dry")}
    rest = {k: v for k, v in cells.items() if k not in small}
    # 젖은 가장자리 링은 쓰지 않는다(62a 2회차 비평: 겹쳐 찍을 때 앞 스탬프 몸 위에 링이 남아 구슬 꿰듯 보임) — 몸 전부 흰색
    cells.update(rest)
    return cells


def pack(cells, pad=2, width=256):
    """줄 단위 선반 배치 → (시트, frames{이름: {x,y,w,h}})."""
    x = y = pad
    row_h = 0
    pos = {}
    for name, im in cells.items():
        w, h = im.size
        if x + w + pad > width:
            x = pad
            y += row_h + pad
            row_h = 0
        pos[name] = (x, y, w, h)
        x += w + pad
        row_h = max(row_h, h)
    H = y + row_h + pad
    sheet = Image.new("RGBA", (width, H), CLEAR)
    for name, im in cells.items():
        sheet.alpha_composite(im, pos[name][:2])
    return sheet, pos
