"""61라운드 아트 2 공용 — fx 도트 그리기 도구(Pillow 만, 반투명 0).

- 색: 1층 램프 A16~A27 · 무채 G · 백열 X0/X1 · 재 S/B(무기 fx v3 팔레트) — 모두 기존 팔레트(새 색 없음).
- 시트 쓰기·아틀라스 변환·미리보기는 bundle2/b2.py(write_sheet·to_atlas·preview)를 import 만 해서 쓴다.
- 좌표 단위: 도트(pixelScale 0.5).
"""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
sys.path.insert(0, os.path.join(WORK, "bundle2"))
sys.path.insert(0, os.path.join(WORK, "atlas57"))

import b2  # noqa: E402
from b2 import G, A, X, SL, WD, PL, Rand  # noqa: E402,F401

# 무기 fx v3 재 램프 (lopad.json fx.v3_weapon_fx)
S = [(0x45, 0x40, 0x3b, 255), (0x5c, 0x55, 0x4e, 255), (0x75, 0x6c, 0x62, 255), (0x90, 0x85, 0x7a, 255)]
B = [(0x2a, 0x1e, 0x17, 255), (0x3b, 0x2a, 0x1f, 255), (0x4f, 0x38, 0x28, 255), (0x66, 0x4a, 0x33, 255)]
# 무기 fx v3 호박(주인공 램프) — 이름은 1층 램프 번호에 맞춤
WA = {17: (0x3f, 0x27, 0x1d, 255), 18: (0x65, 0x3b, 0x24, 255), 19: (0x8b, 0x4d, 0x22, 255), 21: (0xd6, 0x7a, 0x11, 255),
      23: (0xe2, 0xa3, 0x3c, 255), 25: (0xee, 0xcc, 0x78, 255), 26: (0xf4, 0xde, 0x9b, 255)}
X0, X1 = X[0], X[1]
GLOW_ONLY = {X0[:3], X1[:3], WA[26][:3], A[26][:3], A[27][:3]}   # 판정(glowFrames) 프레임에만 허용하는 색(무기 fx 규칙)


def tohex(c):
    return "#%02x%02x%02x" % c[:3]


class Cv:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.im.load()

    @classmethod
    def wrap(cls, im):
        c = cls.__new__(cls)
        c.im = im
        c.w, c.h = im.size
        c.p = im.load()
        return c

    def put(self, x, y, c, only_empty=False, prio=None):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            if only_empty and self.p[x, y][3]:
                return
            self.p[x, y] = c

    def get(self, x, y):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[x, y]
        return (0, 0, 0, 0)

    def disc(self, cx, cy, r, c, ky=1.0, only_empty=False):
        ri = int(math.ceil(r)) + 1
        for y in range(-ri, ri + 1):
            for x in range(-ri, ri + 1):
                if (x * x + (y / ky) ** 2) <= r * r + 0.3:
                    self.put(cx + x, cy + y, c, only_empty)

    def line(self, x0, y0, x1, y1, c, w=1, only_empty=False):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if w <= 1:
                self.put(x, y, c, only_empty)
            else:
                self.disc(x, y, w / 2.0, c, only_empty=only_empty)

    def poly(self, pts, c):
        """채운 다각형(앤티앨리어스 없음 — 마스크 0/255 로 붙임)."""
        m = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(m).polygon([(float(x), float(y)) for x, y in pts], fill=255)
        self.im.paste(tuple(c), (0, 0), m)

    def taper(self, x0, y0, x1, y1, w0, w1, c, bulge=0.0):
        """x0→x1 굵기 w0→w1 (bulge>0 이면 가운데가 더 굵음) 채운 붓획."""
        n = int(math.hypot(x1 - x0, y1 - y0)) * 2 + 2
        for i in range(n + 1):
            t = i / n
            w = w0 + (w1 - w0) * t + bulge * math.sin(math.pi * t)
            if w <= 0.2:
                continue
            self.disc(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, w / 2.0, c)

    def star4(self, cx, cy, arm, core=None, mid=None, edge=None, diag=0):
        """4점 별(십자 + 짧은 대각)."""
        core = core or X0
        mid = mid or X1
        edge = edge or A[25]
        for k in range(1, arm + 1):
            col = mid if k <= arm * 0.45 else edge
            for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                self.put(cx + dx, cy + dy, col)
        for k in range(1, diag + 1):
            for dx, dy in ((k, k), (-k, k), (k, -k), (-k, -k)):
                self.put(cx + dx, cy + dy, edge)
        self.put(cx, cy, core)
        if arm >= 4:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                self.put(cx + dx, cy + dy, mid if arm < 7 else core)

    def ring(self, cx, cy, r, th, c, ky=1.0, dash=None, phase=0.0, only_empty=False):
        """ellipse ring. dash = (켜진 각도°, 꺼진 각도°)."""
        steps = int(2 * math.pi * r * 1.6) + 16
        for i in range(steps):
            a = 2 * math.pi * i / steps
            if dash:
                on, off = dash
                deg = (math.degrees(a) + phase) % (on + off)
                if deg >= on:
                    continue
            for t in range(th):
                rr = r - th / 2.0 + t + 0.5
                self.put(cx + math.cos(a) * rr, cy + math.sin(a) * rr * ky, c, only_empty)

    def spark(self, x, y, ang, ln, head, tail):
        """진행 방향 ang 으로 머리 head·꼬리 tail 색 짧은 줄."""
        for j in range(ln):
            col = head if j < max(1, ln // 3) else tail
            self.put(x - math.cos(ang) * j, y - math.sin(ang) * j, col)

    def outline_outside(self, c, dist=1, only=None):
        """현재 실루엣 바깥 dist 도트 테두리."""
        a = [[self.p[x, y][3] == 255 for x in range(self.w)] for y in range(self.h)]
        add = []
        for y in range(self.h):
            for x in range(self.w):
                if a[y][x]:
                    continue
                hit = False
                for dy in range(-dist, dist + 1):
                    for dx in range(-dist, dist + 1):
                        if abs(dx) + abs(dy) > dist:
                            continue
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < self.h and 0 <= xx < self.w and a[yy][xx]:
                            hit = True
                            break
                    if hit:
                        break
                if hit:
                    add.append((x, y))
        for x, y in add:
            self.p[x, y] = c


def alpha_mask(im):
    w, h = im.size
    p = im.load()
    return [[p[x, y][3] == 255 for x in range(w)] for y in range(h)]


def dilate(mask, r):
    h, w = len(mask), len(mask[0])
    out = [[False] * w for _ in range(h)]
    offs = [(dx, dy) for dy in range(-r, r + 1) for dx in range(-r, r + 1) if dx * dx + dy * dy <= r * r + 0.5]
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                for dx, dy in offs:
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h:
                        out[yy][xx] = True
    return out


def check_frames(frames, name, allow_semi=False, allow_edge=False):
    """반투명 0(구조물 접지 그림자는 allow_semi) · 가장자리 잘림 0. 색 수(불투명) 반환."""
    cols = set()
    for i, im in enumerate(frames):
        w, h = im.size
        p = im.load()
        for y in range(h):
            for x in range(w):
                c = p[x, y]
                if 0 < c[3] < 255 and not allow_semi:
                    raise AssertionError((name, i, "semi", x, y))
                if c[3]:
                    if c[3] == 255:
                        cols.add(c[:3])
                    if not allow_edge and (x in (0, w - 1) or y in (0, h - 1)):
                        raise AssertionError((name, i, "edge", x, y))
    return len(cols)


def check_glow(frames_by_col, glow_cols, name):
    """frames_by_col: [(열 번호, 이미지)]. 무기 fx 규칙: glow 열 밖에는 X0/X1/A26/A27 없음."""
    for col, im in frames_by_col:
        if col in glow_cols:
            continue
        bad = {c[:3] for c in im.getdata() if c[3] and c[:3] in GLOW_ONLY}
        assert not bad, (name, col, "glow color outside glowFrames", bad)


def on_dark(im, bg=(28, 26, 32)):
    out = Image.new("RGBA", im.size, bg + (255,))
    out.alpha_composite(im)
    return out


def scale(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def to_atlas():
    """b2.to_atlas 와 같은 변환이지만 임시 폴더를 이 작업 전용(boss61/_atlas_tmp_<pid>)으로 — 다른 아트 작업과 같은 임시 폴더(props_v3/_atlas_tmp)를 지우지 않게."""
    import importlib.util
    import shutil
    spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(WORK, "atlas57", "build.py"))
    ab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ab)
    tmp_root = os.path.join(HERE, "_atlas_tmp_%d" % os.getpid())
    rep = []
    try:
        for cat, name in b2.WRITTEN:
            src_dir = os.path.join(ROOT, "assets", "sprites", cat, "v3")
            jp, pp = os.path.join(src_dir, name + ".json"), os.path.join(src_dir, name + ".png")
            out_dir = os.path.join(tmp_root, cat, "v3")
            os.makedirs(out_dir, exist_ok=True)
            res = ab.convert_sheet(pp, jp, out_dir, 2, 4096, True)
            ab.apply_in_place(res, out_dir, src_dir, pp, jp, 4096)
            rep.append((cat, name, res["srcSize"], [(w, h) for _, w, h in res["pages"]]))
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    b2.WRITTEN.clear()
    return rep
