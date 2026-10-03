"""4지역 쿼터뷰 바닥 타일셋 공용 도구 (53라운드 — 외곽 v2 와 같은 규칙: 32px, pixelScale 1).

- 이음 보장(무작위 이웃): 흙·진흙 같은 '면' 재질은 **공유 주기 잡음 P(주기 32) + 가장자리 창(window)으로 줄인 변형 잡음 V** 를 섞는다.
  가장자리 6px 안쪽은 모든 변형이 같은 P 로 수렴 → 어떤 변형끼리 붙어도 경계가 이어진다. 금·돌·풀 같은 특징은 안쪽에만.
- 판석 재질은 외곽 v2 의 `tiles.flag_tile`(왼쪽 열·위 행 = 줄눈) 을 그대로 쓰고 톤 램프만 지역별로 바꾼다.
- 색: kit.py 의 G·A·SL·WD·PL·NT 만(새 색 없음).
"""
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../v2_outer"))
sys.path.insert(0, os.path.join(HERE, "../props_v3"))
import tiles as TV2  # noqa: E402  (외곽 v2 타일 함수)
from kit import G, A, SL, WD, PL, NT, Canvas, Rand, CLEAR, hx, tohex, EMISSIVE  # noqa: E402,F401
from pk import qcol, clamp, BAYER  # noqa: E402,F401

T = 32


def new():
    return Canvas(T, T)


# ---------------------------------------------------------------------------
# 주기 값 잡음
# ---------------------------------------------------------------------------
def _h(seed, i, j):
    v = (i * 374761393 + j * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFF) / 32767.5 - 1.0


def _sm(t):
    return t * t * (3 - 2 * t)


def vnoise(seed, cell, x, y, period=T):
    n = max(1, period // cell)
    gx, gy = x / cell, y / cell
    i0, j0 = int(math.floor(gx)), int(math.floor(gy))
    fx, fy = _sm(gx - i0), _sm(gy - j0)
    a = _h(seed, i0 % n, j0 % n); b = _h(seed, (i0 + 1) % n, j0 % n)
    c = _h(seed, i0 % n, (j0 + 1) % n); d = _h(seed, (i0 + 1) % n, (j0 + 1) % n)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(seed, x, y, octaves=((16, 0.55), (8, 0.3), (4, 0.15))):
    return sum(w * vnoise(seed + k * 101, cs, x, y) for k, (cs, w) in enumerate(octaves))


def window(x, y, m=7):
    d = min(x, y, T - 1 - x, T - 1 - y)
    return _sm(clamp(d / m))


SH_OCT = ((8, 0.5), (4, 0.33), (2, 0.17))     # 공유(가장자리) — 고주파만: 큰 얼룩이 32px 마다 되풀이되지 않게
VAR_OCT = ((16, 0.35), (8, 0.4), (4, 0.25))   # 변형(안쪽)


def field(shared, var, x, y, varamp=1.0, m=8, octaves=None):
    """가장자리 = 공유 고주파 잡음(낮은 대비), 안쪽 = 변형 잡음(중주파)."""
    w = window(x, y, m)
    p = fbm(shared, x, y, octaves or SH_OCT)
    if var is None:
        return p
    v = fbm(var, x, y, VAR_OCT)
    return p * 0.3 + w * v * 0.6 * varamp


def surface(ramp, base, amp, shared, var, sharp=4.0, varamp=1.0, m=8, c=None):
    """면 재질 타일. ramp 위 위치 = base + amp*field."""
    c = c or new()
    for y in range(T):
        for x in range(T):
            s = base + amp * field(shared, var, x, y, varamp, m)
            c.px(x, y, qcol(ramp, s, x, y, sharp))
    return c


def mask_field(shared, var, thr, x, y, m=8):
    return field(shared, var, x, y, 1.0, m) > thr


# ---------------------------------------------------------------------------
# 특징(안쪽에만)
# ---------------------------------------------------------------------------
def crack(c, seed, x, y, n, dark, lip, margin=3, branch=0.3):
    """마른 흙 금: 방향을 오래 유지하는 1px 선(가끔 꺾임) + 아래쪽 빛 테. 가장자리 margin 안쪽만."""
    r = Rand(seed)
    dirs = [(1, 0), (1, 1), (0, 1), (-1, 1)]
    di = r.i(0, 3)
    for k in range(n):
        if not (margin <= x < T - margin and margin <= y < T - margin):
            break
        c.px(x, y, dark)
        if c.get(x, y + 1) != dark and r.f() < 0.7:
            c.px(x, y + 1, lip)
        if r.f() < branch and k > n // 3:
            crack(c, seed * 7 + k, x, y, n // 3, dark, lip, margin, 0)
            branch = 0
        if r.f() < 0.22:
            di = (di + r.choice([-1, 1])) % 4
        dx, dy = dirs[di]
        x += dx; y += dy


def pebbles(c, seed, n, ramp, margin=2, box=None):
    r = Rand(seed)
    x0, y0, x1, y1 = box or (margin, margin, T - 1 - margin - 2, T - 1 - margin - 2)
    for _ in range(n):
        x, y = r.i(x0, x1), r.i(y0, y1)
        big = r.f() < 0.35
        c.px(x, y, ramp[3]); c.px(x + 1, y, ramp[2]); c.px(x, y + 1, ramp[2]); c.px(x + 1, y + 1, ramp[1])
        if big:
            c.px(x + 2, y, ramp[2]); c.px(x + 2, y + 1, ramp[1]); c.px(x, y + 2, ramp[1]); c.px(x + 1, y + 2, ramp[0])
            c.px(x + 2, y + 2, ramp[0])


def tuft(c, seed, x, y, cols):
    """마른 풀포기: 부채꼴로 퍼진 줄기 5~8개(어두운 밑동 → 밝은 끝), 밑동 그늘 2px."""
    r = Rand(seed)
    n = r.i(5, 8)
    c.hline(x - 2, x + 2, y + 1, cols[0])
    for k in range(n):
        ang = -0.9 + 1.8 * k / max(1, n - 1) + (r.f() - 0.5) * 0.3
        h = r.i(3, 6)
        for j in range(h):
            xx = x + int(round(math.sin(ang) * j * 0.8))
            yy = y - int(round(math.cos(ang) * j))
            c.px(xx, yy, cols[min(len(cols) - 1, j * len(cols) // h)])


def soot(c, cx, cy, rx, ry, seed, col):
    r = Rand(seed)
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d < 1 and r.f() < (1 - d) * 0.9 and (x + y) % 2 == 0:
                c.px(x, y, col)


def stain(c, cx, cy, rx, ry, seed, ramp, glint=None):
    """얼룩(술·진흙): 덩어리 + 위 어두운 테 + 아래 밝은 테."""
    r = Rand(seed)
    pts = set()
    blobs = [(cx, cy, rx, ry)] + [(cx + r.i(-rx, rx), cy + r.i(-ry, ry), max(2, rx // 2), max(1, ry // 2)) for _ in range(3)]
    for (bx, by, bx_r, by_r) in blobs:
        for y in range(by - by_r, by + by_r + 1):
            for x in range(bx - bx_r, bx + bx_r + 1):
                if ((x - bx) / (bx_r + 0.5)) ** 2 + ((y - by) / (by_r + 0.5)) ** 2 <= 1 and 1 <= x < T - 1 and 1 <= y < T - 1:
                    pts.add((x, y))
    for (x, y) in pts:
        up, dn = (x, y - 1) not in pts, (x, y + 1) not in pts
        c.px(x, y, ramp[0] if up else (ramp[2] if dn else ramp[1]))
    if glint and pts:
        x, y = sorted(pts)[len(pts) // 2]
        c.px(x, y, glint); c.px(x + 1, y, glint)
    return pts


def dither_alpha(c, col, alpha_fn):
    """반투명 데칼 칠하기: alpha_fn(x,y) → 0..255."""
    for y in range(c.h):
        for x in range(c.w):
            a = alpha_fn(x, y)
            if a > 0:
                c.px(x, y, col[:3] + (int(a),))


# ---------------------------------------------------------------------------
# 판석(외곽 v2 함수 재사용, 톤만 교체)
# ---------------------------------------------------------------------------
def flags(layout, seed, tone, joint, joint_d, wet=0.2, flecks=1.0):
    """tone: 램프 5색(어두움→밝음). 외곽 v2 의 slab 규칙(빛 테 짧게·줄눈 왼/위)."""
    TV2.STONE["_r"] = tone
    old = (TV2.JOINT, TV2.JOINT_D)
    TV2.JOINT, TV2.JOINT_D = joint, joint_d
    try:
        c = TV2.flag_tile(layout, seed, wet=wet, tones=["_r"], flecks=flecks)
    finally:
        TV2.JOINT, TV2.JOINT_D = old
    return c


def recolor(c, mapping):
    p = c.im.load()
    for y in range(c.h):
        for x in range(c.w):
            q = p[x, y]
            if q[3] and q[:3] in mapping:
                p[x, y] = mapping[q[:3]] + (q[3],)
    return c


def add_rim(c, sides, rim_light, rim_mid, rim_dark):
    """윗면 타일 가장자리(바닥과 맞닿는 쪽)에 테: 바깥 1px 짙게, 안쪽 빛 1px."""
    if "e" in sides:
        c.vline(T - 1, 0, T - 1, rim_dark); c.vline(T - 2, 0, T - 1, rim_mid); c.vline(T - 3, 0, T - 1, rim_light)
    if "w" in sides:
        c.vline(0, 0, T - 1, rim_dark); c.vline(1, 0, T - 1, rim_light); c.vline(2, 0, T - 1, rim_mid)
    if "n" in sides:
        c.hline(0, T - 1, 0, rim_light); c.hline(0, T - 1, 1, rim_mid)
    if "s" in sides:
        c.hline(0, T - 1, T - 1, rim_dark); c.hline(0, T - 1, T - 2, rim_mid)
    return c


def bricks(c, y0, y1, seed, ramp, mortar, bw=10, bh=5, soot_top=0.0):
    """벽돌 앞면: 행마다 반 장 어긋남, 장마다 톤 약간 다름(디더 없음)."""
    r = Rand(seed)
    c.rect(0, y0, T - 1, y1, mortar)
    row = 0
    y = y0
    while y <= y1:
        off = (row % 2) * (bw // 2)
        x = -off
        while x < T:
            sx0, sx1 = max(0, x), min(T - 1, x + bw - 2)
            sy1 = min(y1, y + bh - 2)
            if sx1 >= sx0:
                k = r.i(1, len(ramp) - 2)
                if soot_top and (y - y0) / max(1, y1 - y0) < soot_top and r.f() < 0.6:
                    k = max(0, k - 1)
                c.rect(sx0, y, sx1, sy1, ramp[k])
                c.hline(sx0, sx1, y, ramp[min(len(ramp) - 1, k + 1)])
                if r.f() < 0.25:
                    c.px(sx0 + r.i(1, max(1, sx1 - sx0 - 1)), y + r.i(1, max(1, bh - 3)), ramp[max(0, k - 1)])
            x += bw
        y += bh
        row += 1
