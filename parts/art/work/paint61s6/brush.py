"""61 단계 6 (P14 §3) — 먹 붓질 걷힘 마스크 4종 `paint/brush_reveal_{0..3}.png` (960×540, L 흑백).

뜻: 픽셀 값 v(0..255) = 그 픽셀이 '걷히는' 시각. 진행도 p(0..1) 에서 v <= p·255 인 곳이 새 장면(방)을 보인다.
    검정(0) = 가장 먼저 걷힘, 흰색(255) = 마지막. 붓 한 획씩: 획 i 는 시간 창 [t0, t1] 을 갖고, 획 안에서는 붓이 지나간
    순서대로(획 시작 → 끝) 값이 커진다. 붓털 결: 획을 가로지르는 방향으로 털마다 늦음(마른 붓 틈) → 같은 획 안에서도
    줄무늬로 늦게 걷히는 결이 남는다. 획 가장자리는 털 길이 차로 들쭉날쭉.
구현: 획 경로를 따라 '붓 도장'을 찍되 도장 값 = 그 순간 시각, 합성은 최솟값(먼저 닿은 시각이 남음). Pillow 만, 결정적.
"""
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter

W, H = 960, 540


class R:
    def __init__(self, seed):
        self.s = (seed * 2654435761 + 977) & 0xFFFFFFFF

    def f(self):
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF

    def u(self, a, b):
        return a + (b - a) * self.f()


def bristles(seed, n=84):
    """붓털 프로필: 가로 위치 u(-1..1)별 (늦음 0..1, 털 끝 길이 0.7..1)."""
    r = R(seed)
    prof = []
    dry = 0.0
    for i in range(n):
        dry = 0.65 * dry + 0.35 * r.f()
        gap = 1.0 if r.f() < 0.10 else 0.0           # 마른 붓 틈(크게 늦음)
        prof.append((min(1.0, dry * 0.6 + gap), 0.78 + 0.22 * r.f()))
    return prof


def bezier(pts, n):
    """카트멀롬 → 촘촘한 점 목록."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out


def stroke(acc, pts, width, t0, t1, seed, spread=0.10, taper=(0.25, 0.35)):
    """acc: 'L' 누적(최솟값). pts: 경로 제어점. width: 붓 폭(px). t0,t1: 0..1 시간 창. spread: 털 늦음 폭(시간)."""
    path = bezier(pts, 40)
    # 호 길이
    L = [0.0]
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        L.append(L[-1] + math.hypot(x1 - x0, y1 - y0))
    total = L[-1] or 1.0
    prof = bristles(seed)
    nb = len(prof)
    r = R(seed + 7)
    step = 3.0
    s = 0.0
    j = 0
    while s <= total:
        while j < len(L) - 2 and L[j + 1] < s:
            j += 1
        seg = max(1e-6, L[j + 1] - L[j])
        f = (s - L[j]) / seg
        x = path[j][0] + (path[j + 1][0] - path[j][0]) * f
        y = path[j][1] + (path[j + 1][1] - path[j][1]) * f
        dx, dy = path[j + 1][0] - path[j][0], path[j + 1][1] - path[j][1]
        dl = math.hypot(dx, dy) or 1.0
        tx, ty = dx / dl, dy / dl
        nx, ny = -ty, tx
        q = s / total
        # 붓 압력: 시작에서 눌러 넓어지고 끝에서 가늘어짐(꼬리)
        a_in, a_out = taper
        pw = min(1.0, 0.55 + 0.45 * q / a_in) if q < a_in else (1.0 if q < 1 - a_out else max(0.18, (1 - q) / a_out))
        hw = width * 0.5 * pw * (0.94 + 0.06 * math.sin(s * 0.05 + seed))
        tval = t0 + (t1 - t0) * q
        # 털마다 짧은 선분(진행 방향으로 step+1 길이)을 찍는다
        rad = int(hw) + 3
        x0, y0 = int(x - rad - step - 2), int(y - rad - step - 2)
        pw_ = 2 * (rad + int(step) + 3)
        patch = Image.new("L", (pw_, pw_), 255)
        d = ImageDraw.Draw(patch)
        for b in range(nb):
            u = -1 + 2 * (b + 0.5) / nb
            late, tip = prof[b]
            if abs(u) > tip * (0.9 + 0.1 * r.f()):
                continue
            ox, oy = x + nx * u * hw - x0, y + ny * u * hw - y0
            v = tval + spread * late + 0.025 * u * u + 0.012 * r.f()
            col = max(0, min(254, int(round(v * 254))))
            bw = max(1.0, hw * 2 / nb + 1.0)
            jx, jy = (r.f() - 0.5) * 1.5, (r.f() - 0.5) * 1.5
            d.line([(ox - tx * (step + 2) + jx, oy - ty * (step + 2) + jy), (ox + tx + jx, oy + ty + jy)], fill=col, width=int(math.ceil(bw)))
        box = (x0, y0, x0 + pw_, y0 + pw_)
        cx0, cy0 = max(0, box[0]), max(0, box[1])
        cx1, cy1 = min(W, box[2]), min(H, box[3])
        if cx1 > cx0 and cy1 > cy0:
            sub = patch.crop((cx0 - x0, cy0 - y0, cx1 - x0, cy1 - y0))
            cur = acc.crop((cx0, cy0, cx1, cy1))
            acc.paste(ImageChops.darker(cur, sub), (cx0, cy0))
        s += step


# 각 변형: 획 목록 (제어점, 폭, 시드). 시간 창은 획 순서대로 자동 배분(약간 겹침).
def _rows(top_to_bottom=True, n=6, seed=1):
    r = R(seed)
    out = []
    band = H / n
    for i in range(n):
        y = band * (i + 0.5) + r.u(-12, 12)
        ltr = i % 2 == 0
        xs = [-260, W * 0.2, W * 0.5, W * 0.8, W + 260]
        pts = [(x, y + r.u(-26, 26) + (8 if k % 2 else -8)) for k, x in enumerate(xs)]
        if not ltr:
            pts = pts[::-1]
        out.append((pts, band * 2.1, seed * 10 + i))
    return out


def _diag(seed=2, n=7):
    r = R(seed)
    out = []
    for i in range(n):
        c = -H * 0.6 + (W + H * 1.2) * (i + 0.5) / n          # x 절편 이동(왼쪽 위 → 오른쪽 아래)
        p0 = (c + 120 + r.u(-20, 20), -260)
        p3 = (c - H * 0.75 - 120 + r.u(-20, 20), H + 260)
        mid = ((p0[0] + p3[0]) / 2 + r.u(-30, 30), H / 2 + r.u(-30, 30))
        pts = [p0, mid, p3] if i % 2 == 0 else [p3, mid, p0]
        out.append((pts, (W + H) / n * 1.35, seed * 10 + i))
    return out


def _center(seed=3, n=7):
    """가운데(입구 자리) 가로 굵은 한 획 → 위·아래로 번갈아 바깥으로 퍼지는 가로 획."""
    r = R(seed)
    band = H / n
    order = [3, 2, 4, 1, 5, 0, 6]
    out = []
    for k, i in enumerate(order):
        y = band * (i + 0.5) + r.u(-10, 10)
        xs = [-260, W * 0.2, W * 0.5, W * 0.8, W + 260]
        pts = [(x, y + r.u(-22, 22)) for x in xs]
        if k % 2:
            pts = pts[::-1]
        out.append((pts, band * (2.6 if k == 0 else 2.0), seed * 10 + k))
    return out


def _cols(seed=4, n=7):
    r = R(seed)
    out = []
    band = W / n
    for i in range(n):
        x = band * (i + 0.5) + r.u(-10, 10)
        pts = [(x + r.u(-30, 30), -240), (x + r.u(-40, 40), H * 0.35), (x + r.u(-40, 40), H * 0.7), (x + r.u(-30, 30), H + 240)]
        if i % 2:
            pts = pts[::-1]
        out.append((pts, band * 2.0, seed * 10 + i))
    return out


VARIANTS = {
    0: ("rows", "가로 획 6 — 위에서 아래로, 왼→오 / 오→왼 번갈아(글씨 쓰듯)", _rows),
    1: ("diagonal", "사선 획 7 — 왼쪽 위에서 오른쪽 아래로 쓸어 내림", _diag),
    2: ("center", "가운데(입구 자리) 굵은 한 획 → 바깥으로 휘감는 6 획", _center),
    3: ("columns", "세로 획 7 — 왼쪽에서 오른쪽으로, 위↓ 아래↑ 번갈아", _cols),
}


def build(vi, overlap=0.35):
    name, note, fn = VARIANTS[vi]
    strokes = fn()
    n = len(strokes)
    acc = Image.new("L", (W, H), 255)
    span = 0.92 / (n - overlap * (n - 1))        # 획 하나 시간 폭 — 끝 0.92 + 털 늦음
    windows = []
    for i, (pts, width, seed) in enumerate(strokes):
        t0 = i * span * (1 - overlap)
        t1 = t0 + span
        stroke(acc, pts, width, t0, t1, seed)
        windows.append([round(t0, 3), round(t1, 3)])
    # 덮이지 않은 틈: 주변 획 값 + 조금(마지막에 걷힘) — 아주 작은 구멍만 남음
    hole = acc.point(lambda v: 255 if v >= 255 else 0)
    cover = 1 - sum(1 for v in hole.getdata() if v) / (W * H)
    filled = acc.filter(ImageFilter.MinFilter(9)).filter(ImageFilter.MaxFilter(3))
    late = filled.point(lambda v: min(255, v + 30))
    acc = Image.composite(late, acc, hole)
    acc = Image.composite(Image.new("L", (W, H), 255), acc, acc.point(lambda v: 255 if v >= 255 else 0))
    acc = equalize(acc)
    meta = {"index": vi, "name": name, "note": note, "strokes": n, "windows": windows,
            "coverageByStrokes": round(cover, 4)}
    return acc, meta


def equalize(im, mix=0.7, lo=2, hi=250):
    """순서를 지키는 단조 재배치: 화면 밖에서 쓴 시간을 없애고 걷히는 넓이가 시간에 고르게(mix=누적 분포 비율)."""
    h = im.histogram()
    tot = sum(h)
    vs = [v for v in range(256) if h[v]]
    vmin, vmax = vs[0], vs[-1]
    cdf, c = [0.0] * 256, 0
    for v in range(256):
        c += h[v]
        cdf[v] = c / tot
    lut = []
    for v in range(256):
        lin = (v - vmin) / max(1, vmax - vmin)
        t = mix * cdf[v] + (1 - mix) * max(0.0, min(1.0, lin))
        lut.append(int(round(lo + (hi - lo) * t)))
    return im.point(lut)


def histogram_spread(im):
    h = im.histogram()
    tot = sum(h)
    q = []
    c = 0
    for v in range(256):
        c += h[v]
        q.append(c / tot)
    return {"p10": next(v for v in range(256) if q[v] >= 0.10), "p50": next(v for v in range(256) if q[v] >= 0.5),
            "p90": next(v for v in range(256) if q[v] >= 0.9), "white255": round(h[255] / tot, 4)}
