"""60라운드 Q1 — 최종 각성 4종 외형 재디자인 시안 공용 도구 (Pillow 만, 결정적).

좌표: v3 도트(pixelScale 0.5, 무기 2배 밀도). 무기는 '로컬 좌표'(u = 쥔 손 → 칼끝, v = 법선)로 정의하고
Cv.shape 가 화면 픽셀마다 (u, v) 를 역산해 색을 고른다(katana3.fill_blade 와 같은 방식 — 기울어진 넓은 날에서 사다리 무늬 없음).
반투명 0 — 모든 픽셀은 불투명 팔레트 색. 색 전환도 알파 섞기가 아니라 '픽셀 단위 문턱(앞줄 X1)'으로 넘어간다.
팔레트: LOPAD lopad.json 의 무채색 16 + 층 램프(1 잔 호박 · 2 패 녹 · 3 붕 청록 · 4 계 황토 · 5 귀 보라 · 6 연 금 · 7 적 진홍 · 8 평상 은백)
        + 주인공 흉갑 SL · 붕대 PL + 백열 X0/X1. (각성 고유색에 층 램프를 고정색으로 쓰는 것은 인터뷰 대상 — 53 Q61 '재·호박만' 규칙의 예외.)
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
SPR = os.path.join(ROOT, "assets/sprites")
OUT = os.path.join(HERE, "out")
sys.path.insert(0, os.path.join(HERE, "../atlas57"))
import gridsheet  # noqa: E402  (읽기만)

_P = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))
G = _P["gray"]                                   # G[0]..G[15]
_FL = {f["floor"]: f["ramp"] for f in _P["floors"]}
A = _FL[1]      # 호박(주인공) — A[5] = A21, A[7] = A23, A[9] = A25, A[10] = A26
GRN = _FL[2]
TEAL = _FL[3]
OCH = _FL[4]
VIO = _FL[5]
GOLD = _FL[6]
CRI = _FL[7]
SIL = _FL[8]
SL = ["#14161c", "#1d2028", "#272b35", "#323743", "#3f4552", "#4e5563", "#626a78", "#7e8693"]
PL = ["#45403b", "#5c554e", "#756c62", "#90857a", "#ada08f"]
WD = ["#1b1411", "#2a1e17", "#3b2a1f", "#4f3828", "#664a33", "#82623f"]
X0, X1 = "#ffffff", "#fff4dc"
INK = "#141516"
BG = "#1b1c20"

FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"


def font(sz):
    try:
        return ImageFont.truetype(FONT_PATH, sz)
    except OSError:
        return ImageFont.load_default()


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def h2(x, y, s=0):
    """결정적 해시 잡음 0..1."""
    n = (int(x) * 374761393 + int(y) * 668265263 + int(s) * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


def vnoise(x, s=0):
    """1차원 값 잡음 0..1 (부드러움)."""
    i = math.floor(x)
    f = x - i
    a, b = h2(i, 7, s), h2(i + 1, 7, s)
    f = f * f * (3 - 2 * f)
    return a + (b - a) * f


def rp(ramp, t):
    """램프에서 t(0..1) 위치 색."""
    t = max(0.0, min(1.0, t))
    return ramp[min(len(ramp) - 1, int(t * (len(ramp) - 1) + 0.5))]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(a, b, x):
    t = clamp((x - a) / ((b - a) or 1e-6))
    return t * t * (3 - 2 * t)


# =============================================================================
# 캔버스 — 픽셀 = (색, z, solid). solid 픽셀만 바깥 셀아웃(INK)을 받는다(빛·불꽃은 테 없음).
# =============================================================================
class Cv:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = {}

    def put(self, x, y, c, z=0, solid=True):
        x, y = int(math.floor(x)), int(math.floor(y))
        if c is None or not (0 <= x < self.w and 0 <= y < self.h):
            return
        o = self.px.get((x, y))
        if o is None or z >= o[1]:
            self.px[(x, y)] = (c, z, solid)

    def shape(self, o, ang, box, fn, z=0, solid=True):
        """로컬 상자 box = (u0, u1, v0, v1) 안 픽셀마다 fn(u, v, x, y) → 색 | (색, solid) | None."""
        ca, sa = math.cos(ang), math.sin(ang)
        u0, u1, v0, v1 = box
        pts = [(o[0] + u * ca - v * sa, o[1] + u * sa + v * ca) for u in (u0, u1) for v in (v0, v1)]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for y in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 2):
            for x in range(int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 2):
                dx, dy = x + 0.5 - o[0], y + 0.5 - o[1]
                u = dx * ca + dy * sa
                v = -dx * sa + dy * ca
                if u0 - 0.5 <= u <= u1 + 0.5 and v0 - 0.5 <= v <= v1 + 0.5:
                    r = fn(u, v, x, y)
                    if r is None:
                        continue
                    if isinstance(r, tuple):
                        self.put(x, y, r[0], z, r[1])
                    else:
                        self.put(x, y, r, z, solid)

    def chain(self, pts, wfn, cfn, z=0, solid=False):
        """폴리라인 캡슐 사슬: wfn(t) = 반폭, cfn(t, d) → 색 (t = 0 시작 → 1 끝, d = 0 중심 → 1 가장자리)."""
        if len(pts) < 2:
            return
        seg = []
        tot = 0.0
        for a, b in zip(pts, pts[1:]):
            ln = math.hypot(b[0] - a[0], b[1] - a[1])
            seg.append((a, b, tot, ln))
            tot += ln
        tot = tot or 1.0
        wmax = max(wfn(i / 20) for i in range(21)) + 1
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for y in range(int(min(ys) - wmax) - 1, int(max(ys) + wmax) + 2):
            for x in range(int(min(xs) - wmax) - 1, int(max(xs) + wmax) + 2):
                px, py = x + 0.5, y + 0.5
                best = None
                for a, b, s0, ln in seg:
                    ex, ey = b[0] - a[0], b[1] - a[1]
                    ll = ln * ln or 1e-6
                    k = clamp(((px - a[0]) * ex + (py - a[1]) * ey) / ll)
                    dx, dy = px - (a[0] + ex * k), py - (a[1] + ey * k)
                    dd = math.hypot(dx, dy)
                    if best is None or dd < best[0]:
                        best = (dd, (s0 + ln * k) / tot)
                dd, t = best
                w = wfn(t)
                if w > 0 and dd <= w:
                    c = cfn(t, dd / w if w else 0, x, y)
                    if c:
                        self.put(x, y, c, z, solid)

    def smear(self, S, r1, r2, a0, a1, fn, z=-2, solid=False):
        """휘두름 궤적(반지름 r1..r2, 각 a0 → a1 라디안, 화면각): fn(tn, rn, x, y) → 색 (tn 0 꼬리 → 1 머리, rn 0 안 → 1 바깥)."""
        R = r2 + 2
        sgn = 1 if a1 >= a0 else -1
        span = abs(a1 - a0) or 1e-6
        for y in range(int(S[1] - R), int(S[1] + R) + 1):
            for x in range(int(S[0] - R), int(S[0] + R) + 1):
                dx, dy = x + 0.5 - S[0], y + 0.5 - S[1]
                r = math.hypot(dx, dy)
                if r < r1 - 1 or r > r2 + 1:
                    continue
                a = math.atan2(dy, dx)
                d = (a - a0) * sgn
                d = (d + math.pi * 4) % (2 * math.pi)
                if d > span:
                    continue
                tn = d / span
                rn = (r - r1) / ((r2 - r1) or 1)
                c = fn(tn, rn, x, y)
                if c:
                    self.put(x, y, c, z, solid)

    def outline(self, c=INK, z=-9):
        add = set()
        for (x, y), (_, _, sol) in self.px.items():
            if not sol:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in self.px and 0 <= q[0] < self.w and 0 <= q[1] < self.h:
                    add.add(q)
        for q in add:
            self.px[q] = (c, z, True)

    def merge(self, other):
        for k, v in other.px.items():
            o = self.px.get(k)
            if o is None or v[1] >= o[1]:
                self.px[k] = v

    def image(self):
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        p = im.load()
        for (x, y), (c, _, _) in self.px.items():
            p[x, y] = hexrgb(c) + (255,)
        return im

    def colors(self):
        return {c for c, _, _ in self.px.values()}


def L2W(o, ang, u, v):
    ca, sa = math.cos(ang), math.sin(ang)
    return (o[0] + u * ca - v * sa, o[1] + u * sa + v * ca)


# =============================================================================
# 전환 문턱 — 픽셀 단위로 원래 색 → (앞줄 X1) → 각성 색. 반투명 대신 시점이 픽셀마다 다르다.
# =============================================================================
FRONT = 0.12


def stage(p, thr):
    """p(0..1 진행) 와 픽셀 문턱 thr(0..1) → -1 원래 · 0 앞줄(번쩍) · 1 각성."""
    s = p * (1 + FRONT) - thr
    if s < 0:
        return -1
    if s < FRONT:
        return 0
    return 1


def pick(st, cb, ca, front=X1):
    if st < 0:
        return cb
    if st == 0:
        return front if (cb is not None or ca is not None) else None
    return ca


# =============================================================================
# 프레임 상태
# =============================================================================
class F:
    def __init__(self, p=1.0, t=0, glow=False, draw=0.0, release=False, flip=1, tn=8):
        self.p, self.t, self.glow, self.draw, self.release, self.flip, self.tn = p, t, glow, draw, release, flip, tn

    @property
    def ph(self):
        """순환 위상 0..1."""
        return (self.t % self.tn) / self.tn


# =============================================================================
# 주인공 몸 + 원래 무기 시트(날 부분만 지움) — 미리보기 맥락용(에셋은 읽기만)
# =============================================================================
_CACHE = {}


def sheet_frame(rel, i, d="right"):
    key = (rel, i, d)
    if key in _CACHE:
        return _CACHE[key]
    jp = os.path.join(SPR, rel + ".json")
    j = gridsheet.load_meta(jp)
    if rel not in _CACHE:
        _CACHE[rel] = (j, gridsheet.open_grid(jp))
    j, im = _CACHE[rel]
    fw, fh = j["frameWidth"], j["frameHeight"]
    r = j["directions"].index(d)
    i = min(i, j["frames"] - 1)
    f = im.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh))
    _CACHE[key] = (j, f)
    return j, f


def erase_seg(im, a, b, rad, umin=0.0, umax=1.08, extra=None):
    """원래 무기 시트에서 a→b 선분 근처(날) 픽셀을 지운다(주먹·칼집은 남김)."""
    im = im.copy()
    px = im.load()
    ex, ey = b[0] - a[0], b[1] - a[1]
    ll = ex * ex + ey * ey or 1.0
    ln = math.sqrt(ll)
    for y in range(im.height):
        for x in range(im.width):
            if not px[x, y][3]:
                continue
            u = ((x + 0.5 - a[0]) * ex + (y + 0.5 - a[1]) * ey) / ll
            dx, dy = x + 0.5 - (a[0] + ex * u), y + 0.5 - (a[1] + ey * u)
            dd = math.hypot(dx, dy)
            hit = umin <= u <= umax and dd <= rad
            if extra:
                ul = u * ln
                for (ua, ub, rr) in extra:
                    if ua <= ul <= ub and dd <= rr:
                        hit = True
            if hit:
                px[x, y] = (0, 0, 0, 0)
    return im


# =============================================================================
# 미리보기 조립
# =============================================================================
def up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def on_bg(im, bg=BG):
    b = Image.new("RGBA", im.size, hexrgb(bg) + (255,))
    b.alpha_composite(im)
    return b


def glow_bg(w, h, cx, cy, ramp_dark, r=60, seed=0):
    """미리보기 배경 조명(어둠 속 동적 조명 연출, 에셋 아님): 동심 디더 고리."""
    im = Image.new("RGBA", (w, h), hexrgb(BG) + (255,))
    p = im.load()
    cols = [hexrgb(c) for c in ramp_dark]
    for y in range(h):
        for x in range(w):
            d = math.hypot((x - cx) / 1.0, (y - cy) / 0.8) / r
            if d >= 1:
                continue
            lv = (1 - d) * len(cols)
            k = int(lv)
            fr = lv - k
            bay = ((x & 1) * 2 + (y & 1) * 3) % 4 / 4.0
            if fr > bay + 0.12:
                k += 1
            if k > 0:
                p[x, y] = cols[min(k, len(cols)) - 1] + (255,)
    return im


def text(img, xy, s, sz=16, fill=(220, 220, 214)):
    d = ImageDraw.Draw(img)
    d.text(xy, s, font=font(sz), fill=fill)


def chips(ramps, k=14):
    """색 칩 줄: ramps = [(이름, [hex...]), ...]."""
    w = max(len(r) for _, r in ramps) * k + 120
    im = Image.new("RGBA", (w, len(ramps) * (k + 4) + 4), hexrgb(BG) + (255,))
    d = ImageDraw.Draw(im)
    for i, (name, r) in enumerate(ramps):
        y = 4 + i * (k + 4)
        d.text((2, y - 1), name, font=font(12), fill=(200, 200, 194))
        for j, c in enumerate(r):
            d.rectangle([116 + j * k, y, 116 + j * k + k - 2, y + k - 2], fill=hexrgb(c))
    return im


def stack_v(ims, gap=10, bg=BG):
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new("RGBA", (w, h), hexrgb(bg) + (255,))
    y = 0
    for i in ims:
        out.alpha_composite(i, (0, y))
        y += i.height + gap
    return out


def stack_h(ims, gap=10, bg=BG):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    out = Image.new("RGBA", (w, h), hexrgb(bg) + (255,))
    x = 0
    for i in ims:
        out.alpha_composite(i, (x, 0))
        x += i.width + gap
    return out


def pad(im, m=10, bg=BG):
    out = Image.new("RGBA", (im.width + 2 * m, im.height + 2 * m), hexrgb(bg) + (255,))
    out.alpha_composite(im, (m, m))
    return out


def caption(im, s, sz=18, h=30, bg="#26272c"):
    out = Image.new("RGBA", (im.width, im.height + h), hexrgb(bg) + (255,))
    text(out, (8, (h - sz) // 2 - 1), s, sz)
    out.alpha_composite(im, (0, h))
    return out


def save_gif(frames, path, ms, k=3, bg=BG):
    ims = [up(on_bg(f, bg), k).convert("P", palette=Image.ADAPTIVE, colors=255) for f in frames]
    durs = ms if isinstance(ms, list) else [ms] * len(ims)
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durs, loop=0, disposal=2, optimize=False)


def wrap(s, sz, width):
    fnt = font(sz)
    lines, cur = [], ""
    for ch in s:
        if fnt.getlength(cur + ch) > width:
            lines.append(cur)
            cur = ch.lstrip()
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def text_block(width, items, bg="#26272c", pad_=10):
    """items = [(문자열, 크기, 색|None)] → 줄바꿈된 글 상자."""
    rows = []
    for s, sz, col in items:
        for ln in wrap(s, sz, width - 2 * pad_):
            rows.append((ln, sz, col or (215, 215, 208)))
    h = pad_ * 2 + sum(int(sz * 1.45) for _, sz, _ in rows)
    im = Image.new("RGBA", (width, h), hexrgb(bg) + (255,))
    y = pad_
    for ln, sz, col in rows:
        text(im, (pad_, y), ln, sz, fill=col)
        y += int(sz * 1.45)
    return im
