"""60라운드 Q9 B안 — 64도트 = 1칸(pixelScale 0.5) 바닥·엄폐 담 공용 도구 (Pillow 만, 결정적).

설계 원칙(진짜 2배 밀도 — 32 그림을 키운 것이 아님):
- 세부 크기 3단: 큰 명도 덩어리(12~16도트) · 중간 결(4~6) · 1도트 반점/광물 알갱이. 32 판에서 2도트였던 줄눈·테는 1~2도트로 가늘게.
- 디더(바둑판) 0. 모든 질감은 덩어리(cluster)와 손으로 찍은 점.
- 쿼터뷰 높이: 판석·포석·벽돌은 윗변 2도트(바깥 +2·안 +1)·왼변 1도트 밝게, 아랫변 2도트·오른변 1도트 어둡게 → 등불을 받으면 모서리가 산다.
- 무작위 이웃 이음: '면' 재질(흙)은 칸 주기(64)로 감기는 공유 잡음 + 가장자리 4도트 안쪽에만 변형 세부. 판석·포석은 칸 왼·위 줄눈 공유.
- 색: lopad gray(G) + 1층 램프 A16~22(발광 23~ 은 바닥에 쓰지 않음) + v2 재질 SL·WD·PL. 새 색 없음. 반투명 0(바닥 칸).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "../v2_outer")))
import kit  # noqa: E402
from PIL import Image  # noqa: E402

G, A, SL, WD, PL = kit.G, kit.A, kit.SL, kit.WD, kit.PL
N = 64
CLEAR = (0, 0, 0, 0)


# ---------------------------------------------------------------- 난수·잡음
def h(*v):
    x = 2166136261
    for a in v:
        x = ((x ^ (int(a) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    x ^= x >> 13
    x = (x * 0x5bd1e995) & 0xFFFFFFFF
    return x ^ (x >> 15)


def hf(*v):
    return (h(*v) & 0xFFFF) / 65535.0


def vnoise(x, y, s, seed, period=None):
    """값 잡음(겹선형). period(도트) 를 주면 그 주기로 감김 — 칸 이음용(period 는 s 의 배수)."""
    gx, gy = x / s, y / s
    x0, y0 = math.floor(gx), math.floor(gy)
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    P = int(round(period / s)) if period else None

    def r(i, j):
        if P:
            i, j = i % P, j % P
        return hf(i, j, seed)
    a = r(x0, y0) + (r(x0 + 1, y0) - r(x0, y0)) * fx
    b = r(x0, y0 + 1) + (r(x0 + 1, y0 + 1) - r(x0, y0 + 1)) * fx
    return a + (b - a) * fy


def fbm(x, y, seed, period=None, scales=(16, 8, 4)):
    tot, w = 0.0, 0.0
    for k, s in enumerate(scales):
        a = 1.0 / (k + 1)
        tot += vnoise(x, y, s, seed + 31 * k, period) * a
        w += a
    return tot / w


def new():
    return Image.new("RGBA", (N, N), CLEAR)


def rgba(c):
    return tuple(c[:3]) + (255,)


# ---------------------------------------------------------------- 판석
FLAG_LAYOUTS = {
    "one": [(0, 0, 1, 1)],
    "two_h": [(0, 0, 1, 0.53), (0, 0.53, 1, 1)],
    "two_v": [(0, 0, 0.59, 1), (0.59, 0, 1, 1)],
    "three": [(0, 0, 1, 0.47), (0, 0.47, 0.42, 1), (0.42, 0.47, 1, 1)],
    "three_b": [(0, 0, 0.47, 0.59), (0.47, 0, 1, 0.59), (0, 0.59, 1, 1)],
    "four": [(0, 0, 0.56, 0.42), (0.56, 0, 1, 0.42), (0, 0.42, 0.36, 1), (0.36, 0.42, 1, 1)],
    "five": [(0, 0, 0.5, 0.36), (0.5, 0, 1, 0.36), (0, 0.36, 0.3, 1), (0.3, 0.36, 0.72, 0.7), (0.72, 0.36, 1, 1),
             (0.3, 0.7, 0.72, 1)],
}


class Flag:
    """판석 칸 결과: im + owner(판석 번호, -1 = 줄눈) + base(판석별 본색 단계)."""

    def __init__(self, im, owner, base, ramp):
        self.im, self.owner, self.base, self.ramp = im, owner, base, ramp


def flags(seed, layout, ramp, grout, grout_deep, base_lv=(3, 4, 5), chip=0.5, pits=1.0, cracks=0.18, spec=0.8,
          fleck=0.012, wear=False, gw=2, rounded=1, bite=0.16, n_big=(0.8, 0.15), n_mid=(0.9, 0.07), bevel=2):
    """ramp: 어두움→밝음(10칸 이상 권장). base_lv: 판석 본색 후보(가중 균등)."""
    im = new()
    px = im.load()
    rects = [(k, round(a * N), round(b * N), round(c * N), round(d * N)) for k, (a, b, c, d) in enumerate(FLAG_LAYOUTS[layout])]
    owner = [[-1] * N for _ in range(N)]
    for k, x0, y0, x1, y1 in rects:
        for y in range(y0 + gw, y1):
            for x in range(x0 + gw, x1):
                owner[y][x] = k
    # 줄눈 가장자리 들쭉날쭉(1도트 물림) + 모서리 깨짐
    for k, x0, y0, x1, y1 in rects:
        for x in range(x0 + gw, x1):
            for (yy, side) in ((y0 + gw, 0), (y1 - 1, 1)):
                if hf(seed, k, x, side, 1) < bite and owner[yy][x] == k:
                    owner[yy][x] = -1
        for y in range(y0 + gw, y1):
            for (xx, side) in ((x0 + gw, 2), (x1 - 1, 3)):
                if hf(seed, k, y, side, 2) < bite and owner[y][xx] == k:
                    owner[y][xx] = -1
        for ci, (cx, cy, sx, sy) in enumerate(((x0 + gw, y0 + gw, 1, 1), (x1 - 1, y0 + gw, -1, 1), (x0 + gw, y1 - 1, 1, -1),
                                               (x1 - 1, y1 - 1, -1, -1))):
            depth = rounded + (int(hf(seed, k, ci, 4) * 4) if hf(seed, k, ci, 3) < chip else 0)
            for j in range(depth):
                for i in range(depth - j):
                    xx, yy = cx + sx * i, cy + sy * j
                    if 0 <= xx < N and 0 <= yy < N and owner[yy][xx] == k:
                        owner[yy][xx] = -1
    base = {}
    for k, *_ in rects:
        base[k] = base_lv[int(hf(seed, k, 9) * len(base_lv)) % len(base_lv)]
    L = len(ramp) - 1
    for y in range(N):
        for x in range(N):
            k = owner[y][x]
            if k < 0:
                px[x, y] = rgba(grout_deep if vnoise(x, y, 3, seed + 77) < 0.36 else grout)
                continue
            b = base[k]
            n1 = vnoise(x, y, 14, seed * 7 + k)          # 큰 덩어리
            n2 = vnoise(x, y, 5, seed * 13 + k)          # 중간 결
            lv = b + (1 if n1 > n_big[0] else (-1 if n1 < n_big[1] else 0)) + (1 if n2 > n_mid[0] else (-1 if n2 < n_mid[1] else 0))
            if wear:
                rx, ry = rects[k][1:3], rects[k][3:5]
                cxm, cym = (rects[k][1] + rects[k][3]) / 2, (rects[k][2] + rects[k][4]) / 2
                dd = math.hypot((x - cxm) / max(1, rects[k][3] - rects[k][1]), (y - cym) / max(1, rects[k][4] - rects[k][2]))
                if dd < 0.22 and n2 > 0.45:
                    lv += 1                               # 닳아 반들한 가운데
            px[x, y] = rgba(ramp[max(0, min(L, lv))])
    # 1도트 광물 알갱이(밝·어두)
    for y in range(N):
        for x in range(N):
            k = owner[y][x]
            if k >= 0 and hf(seed, x, y, 5) < fleck:
                px[x, y] = rgba(ramp[min(L, base[k] + 2)] if hf(seed, x, y, 6) < 0.5 else ramp[max(0, base[k] - 2)])

    def own(x, y):
        return owner[y][x] if 0 <= x < N and 0 <= y < N else -1
    # 높이 테
    for y in range(N):
        for x in range(N):
            k = owner[y][x]
            if k < 0:
                continue
            b = base[k]
            if own(x, y - 1) == -1:
                px[x, y] = rgba(ramp[min(L, b + bevel)])
            elif own(x, y - 2) == -1:
                px[x, y] = rgba(ramp[min(L, b + 1)])
            elif own(x - 1, y) == -1:
                px[x, y] = rgba(ramp[min(L, b + 1)])
            if own(x, y + 1) == -1 and not (y == N - 1):
                px[x, y] = rgba(ramp[max(0, b - 2)])
            elif own(x, y + 2) == -1 and y < N - 2:
                px[x, y] = rgba(ramp[max(0, b - 1)])
            elif own(x + 1, y) == -1 and x < N - 1:
                px[x, y] = rgba(ramp[max(0, b - 1)])
            if y == N - 1 or x == N - 1:           # 다음 칸 줄눈 직전 그늘
                px[x, y] = rgba(ramp[max(0, b - (2 if y == N - 1 else 1))])
            elif y == N - 2:
                px[x, y] = rgba(ramp[max(0, b - 1)])
    # 팬 점(1도트 어두움 + 아래 1도트 밝음) · 금 · 젖은 반짝임
    for k, x0, y0, x1, y1 in rects:
        w, hh = x1 - x0, y1 - y0
        for i in range(int(w * hh / 260 * pits)):
            x = x0 + 4 + int(hf(seed, k, i, 21) * max(1, w - 8))
            y = y0 + 4 + int(hf(seed, k, i, 22) * max(1, hh - 8))
            if own(x, y) == k and own(x, y + 1) == k:
                px[x, y] = rgba(ramp[max(0, base[k] - 2)])
                px[x, y + 1] = rgba(ramp[min(L, base[k] + 1)])
        if hf(seed, k, 31) < cracks and w > 20 and hh > 16:
            crack(px, own, k, x0 + w // 4 + int(hf(seed, k, 32) * w / 2), y0 + 3, int(hh * 0.7), seed + k, ramp, base[k])
        if hf(seed, k, 40) < spec and w * hh > 500:
            x = x0 + 4 + int(hf(seed, k, 41) * max(1, w // 2 - 4))
            y = y0 + 4 + int(hf(seed, k, 42) * max(1, hh // 2 - 4))
            for dx in (0, 1):
                if own(x + dx, y) == k:
                    px[x + dx, y] = rgba(ramp[min(L, base[k] + 3 - dx)])
    return Flag(im, owner, base, ramp)


def crack(px, own, k, x, y, steps, seed, ramp, b, branch=True):
    dx = 1 if hf(seed, 33) < 0.5 else -1
    L = len(ramp) - 1
    for i in range(steps):
        if own(x, y) != k:
            break
        px[x, y] = rgba(ramp[0])
        if own(x + 1, y) == k:
            px[x + 1, y] = rgba(ramp[min(L, b + 1)])
        y += 1
        r = hf(seed, i, 34)
        if r < 0.3:
            x += dx
        elif r > 0.9:
            dx = -dx
        if branch and i == steps // 2:
            crack(px, own, k, x, y, steps // 3, seed + 7, ramp, b, branch=False)


# ---------------------------------------------------------------- 포석(작은 둥근 돌)
def setts(seed, ramp, joint, joint_deep, rows=(13, 13, 12, 13, 13), wmin=10, wmax=17, base_lv=(3, 4, 5), sand=None, strong=False):
    """줄마다 엇갈린 둥근 포석. 칸 왼·위 끝은 항상 줄눈(공유). joint = 줄눈 흙, sand = 줄눈 위 모래 점 색."""
    im = new()
    px = im.load()
    owner = [[-1] * N for _ in range(N)]
    stones = []
    y = 0
    for ri, rh in enumerate(rows):
        x = 0
        widths = []
        while x < N:
            w = wmin + int(hf(seed, ri, len(widths), 1) * (wmax - wmin + 1))
            if N - (x + w) < wmin:
                w = N - x
            widths.append(w)
            x += w
        x = 0
        for wi, w in enumerate(widths):
            k = len(stones)
            stones.append((k, x, y, x + w, y + rh))
            x += w
        y += rh
    L = len(ramp) - 1
    base = {}

    def dome(dl):     # 6회차(조명 목업): ±2 돔이 등불 아래 지글거림 → 기본 ±1, 가장 밝은 1단은 왼쪽 위 좁게
        if strong:
            return 2 if dl > 0.75 else (1 if dl > 0.3 else (0 if dl > -0.35 else (-1 if dl > -0.75 else -2)))
        return 2 if dl > 0.9 else (1 if dl > 0.45 else (0 if dl > -0.55 else -1))
    for k, x0, y0, x1, y1 in stones:
        base[k] = base_lv[int(hf(seed, k, 9) * len(base_lv)) % len(base_lv)]
        cx, cy = (x0 + x1 - 1) / 2 + 0.5, (y0 + y1 - 1) / 2 + 0.5
        rx, ry = (x1 - x0) / 2 - 1.0, (y1 - y0) / 2 - 1.0
        for yy in range(y0 + 1, y1):
            for xx in range(x0 + 1, x1):
                # 둥근 사각(초타원) — 모서리 2~3도트 깎임
                u, v = abs(xx + 0.5 - cx) / rx, abs(yy + 0.5 - cy) / ry
                if u ** 3.2 + v ** 3.2 <= 1.0 + 0.12 * (hf(seed, k, xx, yy) - 0.5):
                    owner[yy][xx] = k
    for yy in range(N):
        for xx in range(N):
            k = owner[yy][xx]
            if k < 0:
                c = joint_deep if vnoise(xx, yy, 3, seed + 5) < 0.4 else joint
                if sand and hf(seed, xx, yy, 7) < 0.07:
                    c = sand
                px[xx, yy] = rgba(c)
                continue
            _, x0, y0, x1, y1 = stones[k]
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
            # 돔 셰이딩: 빛 = 왼쪽 위
            u, v = (xx + 0.5 - cx) / rx, (yy + 0.5 - cy) / ry
            dl = -0.62 * u - 0.78 * v
            lv = base[k] + dome(dl)
            n = vnoise(xx, yy, 4, seed + k * 3)
            lv += 1 if n > 0.88 else (-1 if n < 0.08 else 0)
            px[xx, yy] = rgba(ramp[max(0, min(L, lv))])
        # 반짝임: 돌마다 왼쪽 위 1~2도트
    for k, x0, y0, x1, y1 in stones:
        if hf(seed, k, 50) < 0.55:
            x, y = x0 + 3 + int((x1 - x0) * 0.2), y0 + 3
            if 0 <= x < N and 0 <= y < N and owner[y][x] == k:
                px[x, y] = rgba(ramp[min(L, base[k] + 3)])
    return Flag(im, owner, base, ramp)


# ---------------------------------------------------------------- 흙(면 재질, 칸 주기 잡음)
def dirt(seed_shared, seed_var, cols, pebbles=6, cracks=2, grass=0, damp=0.0, grass_cols=None, peb_ramp=None, crack_ramp=None,
         clods=26):
    """흙(면 재질). cols = {base, cool, warm, light, dark, darker}.
    4회차 비평: 큰 얼룩은 변형 4장이 되풀이돼 무늬로 읽힘 → 큰 얼룩은 아주 옅게(같은 명도 2색), 대신 칸 전체에 고르게 흙덩이(2~4도트,
    윗면 밝음·밑 그늘)를 촘촘히 뿌려 되풀이를 가린다. 흙덩이는 가장자리 2도트 안쪽(이음 보장). 1도트 알갱이는 공유 주기 잡음."""
    im = new()
    px = im.load()
    for y in range(N):
        for x in range(N):
            w = edge_window(x, y, 1)
            va = fbm(x, y, seed_var + 1000, scales=(18, 8))
            b = 0.5 * (1 - w) + va * w
            c = cols["base"]                      # 5회차: 큰 얼룩(G4)이 고리 무늬로 되풀이 → 제거, 흙덩이·알갱이로만
            f = vnoise(x, y, 2, seed_shared + 9, period=N)
            if f > 0.93:
                c = cols["light"]
            elif f < 0.06:
                c = cols["warm"]
            if damp and w > 0.85 and vnoise(x, y, 10, seed_var + 3) < damp * 0.6:
                c = cols["dark"]
            px[x, y] = rgba(c)
    for i in range(clods):
        x = 3 + int(hf(seed_var, i, 61) * (N - 7))
        y = 3 + int(hf(seed_var, i, 62) * (N - 7))
        w_ = 2 + int(hf(seed_var, i, 63) * 3)
        h_ = 1 + int(hf(seed_var, i, 64) * 2)
        for yy in range(y, y + h_ + 1):
            for xx in range(x, x + w_):
                if (xx in (x, x + w_ - 1)) and yy == y:
                    continue
                px[xx, yy] = rgba(cols["light"] if yy == y else cols["base"])
        for xx in range(x, x + w_ + 1):
            px[xx, y + h_ + 1] = rgba(cols["dark"] if hf(seed_var, i, xx) < 0.7 else cols["darker"])
    pr = peb_ramp
    for i in range(pebbles):
        x = 6 + int(hf(seed_var, i, 1) * (N - 12))
        y = 6 + int(hf(seed_var, i, 2) * (N - 12))
        r = 1 + int(hf(seed_var, i, 3) * 2.2)
        pebble(px, x, y, r, pr, 4 + (1 if hf(seed_var, i, 4) < 0.5 else 0))
    cr = crack_ramp or [cols["darker"], cols["dark"], cols["warm"], cols["base"], cols["light"]]
    for i in range(cracks):
        x = 8 + int(hf(seed_var, i, 11) * (N - 16))
        y = 8 + int(hf(seed_var, i, 12) * (N - 16))
        dry_crack(px, x, y, seed_var + i, cr, 3)
    for i in range(grass):
        x = 7 + int(hf(seed_var, i, 21) * (N - 14))
        y = 9 + int(hf(seed_var, i, 22) * (N - 16))
        tuft(px, x, y, seed_var + i, grass_cols or [WD[2], WD[4], PL[2], PL[3]])
    return im


def edge_window(x, y, m=4):
    d = min(x, y, N - 1 - x, N - 1 - y)
    return max(0.0, min(1.0, (d - m) / 6.0))


def pebble(px, x, y, r, ramp, b):
    L = len(ramp) - 1
    for yy in range(y - r - 1, y + r + 2):
        for xx in range(x - r - 1, x + r + 2):
            d = math.hypot((xx - x) / (r + 0.5), (yy - y) / (r * 0.8 + 0.5))
            if d <= 1.0 and 0 <= xx < N and 0 <= yy < N:
                u, v = (xx - x) / (r + 0.5), (yy - y) / (r + 0.5)
                lv = b + (1 if -0.6 * u - 0.8 * v > 0.25 else (-1 if -0.6 * u - 0.8 * v < -0.35 else 0))
                px[xx, yy] = rgba(ramp[max(0, min(L, lv))])
    # 그림자(오른쪽 아래 1도트)
    for xx in range(x - r + 1, x + r + 2):
        yy = y + int(r * 0.8) + 1
        if 0 <= xx < N and 0 <= yy < N:
            c = px[xx, yy]
            px[xx, yy] = rgba(ramp[max(0, b - 3)]) if c[3] else c


def dry_crack(px, x, y, seed, ramp, b):
    """마른 흙 금: 갈라지는 2~3 가지, 어두운 선 + 아래 1도트 밝음."""
    for br in range(2 + (1 if hf(seed, 1) < 0.5 else 0)):
        ang = hf(seed, br, 2) * 6.283
        cx, cy = float(x), float(y)
        for i in range(6 + int(hf(seed, br, 3) * 8)):
            ang += (hf(seed, br, i, 4) - 0.5) * 0.9
            cx += math.cos(ang)
            cy += math.sin(ang) * 0.6
            xi, yi = int(round(cx)), int(round(cy))
            if not (3 <= xi < N - 3 and 3 <= yi < N - 3):
                break
            px[xi, yi] = rgba(ramp[max(0, b - 3)])
            if yi + 1 < N:
                c = px[xi, yi + 1]
                if c[:3] != tuple(ramp[max(0, b - 3)][:3]):
                    px[xi, yi + 1] = rgba(ramp[min(len(ramp) - 1, b + 1)])


def tuft(px, x, y, seed, cols):
    """마른 풀포기: 아래에서 퍼지는 잎 4~6가닥(1도트), 밑동 그늘."""
    for i in range(4 + int(hf(seed, 1) * 3)):
        ang = -math.pi / 2 + (i - 2.5) * 0.32 + (hf(seed, i, 2) - 0.5) * 0.3
        L = 3 + int(hf(seed, i, 3) * 4)
        for t in range(L):
            xi = int(round(x + math.cos(ang) * t))
            yi = int(round(y + math.sin(ang) * t))
            if 0 <= xi < N and 0 <= yi < N:
                px[xi, yi] = rgba(cols[min(len(cols) - 1, t * len(cols) // L)])
    for dx in (-1, 0, 1):
        if 0 <= x + dx < N and y + 1 < N:
            px[x + dx, y + 1] = rgba(WD[0])


# ---------------------------------------------------------------- 덧칠(방 종류 바닥·바닥 특징)
def soot(im, seed, amount=0.45, ramp_dark=(G[1], G[2], WD[1])):
    """그을음: 큰 덩어리 어둡게(경계는 계단 2단) + 재 알갱이."""
    px = im.load()
    for y in range(N):
        for x in range(N):
            n = fbm(x, y, seed, scales=(14, 6))
            w = edge_window(x, y, 3)
            if n * (0.4 + 0.6 * w) > 1 - amount:
                c = px[x, y]
                if c[3]:
                    px[x, y] = rgba(ramp_dark[0] if n > 1 - amount * 0.55 else ramp_dark[1])
            elif n * (0.4 + 0.6 * w) > 1 - amount * 1.25 and hf(seed, x, y) < 0.25:
                px[x, y] = rgba(ramp_dark[2])
    for i in range(10):
        x, y = 8 + int(hf(seed, i, 1) * 48), 8 + int(hf(seed, i, 2) * 48)
        px[x, y] = rgba(G[6])


def pool(im, seed, cx, cy, r, cols, gl=None, owner=None, seep=True):
    """고인 액체(술·물·진흙): 원 4개 합, 위 테 밝게, 반사 띠·점, 줄눈 스밈(owner 있으면).
    cols = [가장 어두움, 어두움, 중간, 위 테, 반사, 반사 밝음]"""
    px = im.load()
    blobs = [(cx, cy, r)] + [(cx + (hf(seed, i, 51) - 0.5) * r * 1.5, cy + (hf(seed, i, 52) - 0.5) * r * 0.9,
                               r * (0.45 + 0.35 * hf(seed, i, 53))) for i in range(3)]
    inside = [[False] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            u, v = (x + 0.5) / N, (y + 0.5) / N
            for bx, by, br in blobs:
                if ((u - bx) / br) ** 2 + ((v - by) / (br * 0.6)) ** 2 <= 1:
                    inside[y][x] = True
                    break
            if inside[y][x] and min(x, y, N - 1 - x, N - 1 - y) < 2:
                inside[y][x] = False
    for y in range(N):
        for x in range(N):
            if not inside[y][x]:
                continue
            top = not (y - 1 >= 0 and inside[y - 1][x])
            bot = not (y + 1 < N and inside[y + 1][x])
            side = not (x - 1 >= 0 and inside[y][x - 1]) or not (x + 1 < N and inside[y][x + 1])
            if top or (y - 2 >= 0 and not inside[y - 2][x]):
                px[x, y] = rgba(cols[3] if top else cols[2])
            elif bot or side:
                px[x, y] = rgba(cols[0])
            else:
                # 7회차: 안쪽 두 색 얼룩이 '점박이 과자'처럼 보임 → 위 테 바로 아래 3도트만 한 단 밝게(반사), 나머지 한 색
                near_top = any(y - d >= 0 and not inside[y - d][x] for d in (3, 4, 5))
                px[x, y] = rgba(cols[1] if near_top else cols[0])
    sx, sy = int((cx - r * 0.3) * N), int((cy - r * 0.15) * N)
    for i in range(8):
        x, y = sx + i, sy + i // 5
        if 0 <= x < N and 0 <= y < N and inside[y][x]:
            px[x, y] = rgba(cols[5] if 2 <= i <= 4 else cols[4])
    for i in range(3):
        x, y = int((cx + r * (0.1 + 0.15 * i)) * N), int((cy + r * 0.12) * N) + i % 2
        if 0 <= x < N and 0 <= y < N and inside[y][x]:
            px[x, y] = rgba(gl or cols[5])
    if seep and owner is not None:
        for y in range(N):
            for x in range(N):
                if owner[y][x] == -1 and not inside[y][x]:
                    near = any(0 <= x + dx < N and 0 <= y + dy < N and inside[y + dy][x + dx]
                               for dx in range(-6, 7, 2) for dy in (-2, 0, 2))
                    if near and hf(x, y, seed, 71) < 0.85:
                        px[x, y] = rgba(cols[0])
    return inside


def straw(im, seed, n=14, cols=(WD[3], WD[4], WD[5], PL[3], A[19])):
    """흩어진 짚: 3~7도트 가는 줄기(밝은 쪽 끝), 몇 가닥은 겹쳐 덩어리."""
    px = im.load()
    for i in range(n):
        x, y = 6 + hf(seed, i, 1) * 52, 6 + hf(seed, i, 2) * 52
        ang = hf(seed, i, 3) * math.pi
        L = 3 + int(hf(seed, i, 4) * 5)
        col_i = int(hf(seed, i, 5) * (len(cols) - 1))
        for t in range(L):
            xi, yi = int(round(x + math.cos(ang) * t)), int(round(y + math.sin(ang) * t * 0.7))
            if 2 <= xi < N - 2 and 2 <= yi < N - 2:
                px[xi, yi] = rgba(cols[min(len(cols) - 1, col_i + (1 if t > L * 0.6 else 0))])
                if t == 0 and yi + 1 < N:
                    px[xi, yi + 1] = rgba(WD[1])


def mud(im, seed, cx, cy, r, ramp=(WD[0], WD[1], WD[2], WD[3], PL[1])):
    pool(im, seed, cx, cy, r, [ramp[0], ramp[1], ramp[2], ramp[3], ramp[4], ramp[4]], gl=ramp[3], seep=False)


def arrows(im, seed, n=2):
    """부러진 화살: 나무 대(WD3~5) + 깃(PL3/G9) + 쇠촉(SL6)."""
    px = im.load()
    for i in range(n):
        x, y = 12 + hf(seed, i, 1) * 40, 14 + hf(seed, i, 2) * 36
        ang = hf(seed, i, 3) * math.pi
        L = 12 + int(hf(seed, i, 4) * 8)
        for t in range(L):
            xi, yi = int(round(x + math.cos(ang) * t)), int(round(y + math.sin(ang) * t * 0.6))
            if 2 <= xi < N - 2 and 2 <= yi < N - 3:
                px[xi, yi] = rgba(WD[5] if t % 4 else WD[4])
                px[xi, yi + 1] = rgba(WD[1])
                if t < 3:
                    px[xi, yi] = rgba(SL[6] if t else G[11])
                if t > L - 4:
                    px[xi, yi - 1] = rgba(PL[3] if t % 2 else G[9])
        # 부러진 끝 쪼가리
        xi, yi = int(x + math.cos(ang) * (L + 2)), int(y + math.sin(ang) * (L + 2) * 0.6)
        if 2 <= xi < N - 2 and 2 <= yi < N - 2:
            px[xi, yi] = rgba(WD[4])


def rush_mat(im, seed, x0=6, y0=8, x1=58, y1=56):
    """골풀 깔개: 엮은 가로 띠(2도트) + 세로 날실, 가장자리 해짐."""
    px = im.load()
    cols = [WD[2], WD[3], WD[4], PL[2], PL[3]]
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x in (x0, x1 - 1) or y in (y0, y1 - 1)) and hf(seed, x, y) < 0.4:
                continue
            band = (y - y0) // 3
            weave = ((x - x0) // 4 + band) % 2
            v = 2 + weave + (1 if (y - y0) % 3 == 0 else 0) - (1 if (y - y0) % 3 == 2 else 0)
            if hf(seed, x, y, 2) < 0.04:
                v -= 1
            px[x, y] = rgba(cols[max(0, min(4, v))])
    for x in range(x0, x1):
        if x < N and y1 < N:
            px[x, y1] = rgba(WD[0])


def gold_trim(im, inset=4):
    """금실 상감 테: 칸 둘레 안쪽 사각 선(놋쇠 A20 + 아래·오른 그늘 A18 + 모서리 A21)."""
    px = im.load()
    a, b = inset, N - 1 - inset
    for t in range(a, b + 1):
        px[t, a] = rgba(A[21])
        px[t, a + 1] = rgba(A[18])
        px[t, b] = rgba(A[20])
        px[a, t] = rgba(A[21])
        px[a + 1, t] = rgba(A[18])
        px[b, t] = rgba(A[20])
    for (x, y) in ((a, a), (b, a), (a, b), (b, b)):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if abs(dx) + abs(dy) == 1:
                    px[x + dx, y + dy] = rgba(A[22])


def cup_engrave(im, cx=32, cy=30, s=1.0, dark=G[2], lit=G[8]):
    """잔 문양 새김: 잔 윤곽(어두운 홈 + 아래 1도트 밝은 턱)."""
    px = im.load()
    pts = []
    for t in range(-12, 13):
        u = t / 12
        pts.append((cx + t * s, cy - 10 * s + int(abs(u) ** 2 * 2)))        # 잔 윗변(살짝 휨)
    for v in range(0, 11):
        w = 12 * s * (1 - (v / 10) ** 1.6 * 0.85)
        pts.append((cx - w, cy - 10 * s + v * s))
        pts.append((cx + w, cy - 10 * s + v * s))
    for v in range(0, 9):
        pts.append((cx - 1, cy + v * s))
        pts.append((cx + 1, cy + v * s))
    for t in range(-7, 8):
        pts.append((cx + t * s, cy + 9 * s))
    for x, y in pts:
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < N and 0 <= yi + 1 < N:
            px[xi, yi] = rgba(dark)
            c = px[xi, yi + 1]
            if c[:3] != tuple(dark[:3]):
                px[xi, yi + 1] = rgba(lit)


def ruts(im, seed, ys=(22, 42), dark=(WD[0], WD[1]), lit=PL[1]):
    """바퀴 자국: 칸을 가로지르는 홈 2줄(같은 행 이어 붙임) — 홈 3도트, 아래 턱 밝음, 위 그늘."""
    px = im.load()
    for y0 in ys:
        for x in range(N):
            wob = int(round(math.sin((x + seed) * 0.21) * 0.6))
            y = y0 + wob
            px[x, y - 1] = rgba(dark[1])
            px[x, y] = rgba(dark[0])
            px[x, y + 1] = rgba(dark[0] if hf(seed, x, 1) < 0.6 else dark[1])
            px[x, y + 2] = rgba(lit)


def grate(im, x0=18, y0=20, w=28, h=22):
    """쇠 창살 배수구: 테두리 쇠(밝은 윗변) + 세로 창살 5 + 사이 어둠."""
    px = im.load()
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            edge = y in (y0, y0 + 1, y0 + h - 1, y0 + h - 2) or x in (x0, x0 + 1, x0 + w - 1, x0 + w - 2)
            if edge:
                c = SL[7] if y in (y0,) else (SL[5] if y == y0 + 1 or x in (x0, x0 + 1) else SL[3])
            else:
                bar = (x - x0 - 2) % 5 in (0, 1)
                c = (SL[6] if (x - x0 - 2) % 5 == 0 else SL[4]) if bar else (G[0] if y < y0 + h - 5 else G[1])
            px[x, y] = rgba(c)
    for x in range(x0 + 1, x0 + w + 1):
        if y0 + h < N:
            px[x, y0 + h] = rgba(G[1])


def drain(im, y0=26, h=12, rim=(SL[5], SL[7], SL[3]), water=None):
    """가로 배수로(같은 행 이어 붙임): 위 턱(밝음)·바닥 홈(어두움)·젖은 줄."""
    px = im.load()
    for x in range(N):
        px[x, y0] = rgba(rim[1])
        px[x, y0 + 1] = rgba(rim[0])
        for y in range(y0 + 2, y0 + h - 2):
            c = G[1] if y < y0 + 4 else G[2]
            if water and y in (y0 + h - 5, y0 + h - 4):
                c = water[(x // 5 + y) % len(water)]
            px[x, y] = rgba(c)
        px[x, y0 + h - 2] = rgba(rim[2])
        px[x, y0 + h - 1] = rgba(rim[0])


def gravel(im, seed, n=40, ramp=(G[3], G[5], G[7], G[9], PL[2], PL[3])):
    px = im.load()
    for i in range(n):
        x, y = 4 + int(hf(seed, i, 1) * 56), 4 + int(hf(seed, i, 2) * 56)
        c = ramp[int(hf(seed, i, 3) * len(ramp))]
        px[x, y] = rgba(c)
        if hf(seed, i, 4) < 0.5 and x + 1 < N:
            px[x + 1, y] = rgba(c)
        if y + 1 < N:
            px[x, y + 1] = rgba(G[1])


def shards(im, seed, n=7):
    """깨진 잔 조각: 2~4도트 삼각 조각(유리 G11~14 + 호박 술 A19~21) + 그늘."""
    px = im.load()
    for i in range(n):
        x, y = 8 + int(hf(seed, i, 1) * 48), 8 + int(hf(seed, i, 2) * 46)
        glass = hf(seed, i, 3) < 0.5
        L = 2 + int(hf(seed, i, 4) * 3)
        for j in range(L):
            for k in range(L - j):
                c = (G[13] if j == 0 else G[11]) if glass else (A[21] if j == 0 else A[19])
                px[x + k, y + j] = rgba(c)
        px[x + 1, y + L] = rgba(G[1])


def inlay_line(im, y0=31):
    """가로 금실 상감(이어 붙임): 놋쇠 1도트 + 위 밝음·아래 그늘."""
    px = im.load()
    for x in range(N):
        px[x, y0 - 1] = rgba(A[18])
        px[x, y0] = rgba(A[21] if (x // 8) % 2 else A[20])
        px[x, y0 + 1] = rgba(A[17])


def upscale2(im):
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def luma(ims):
    acc = n = 0
    for im in ims:
        for c in im.get_flattened_data():
            if c[3]:
                acc += 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
                n += 1
    return acc / max(1, n)
