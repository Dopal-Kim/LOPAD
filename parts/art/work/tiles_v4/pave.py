#!/usr/bin/env python3
"""LOPAD 바닥 타일 v4 공통 — '깨진 포장도로 뒷골목' (48라운드 Q5, 계약 art-assets §6.4).

원칙 (도영 님 원문: "바닥 타일도 너무 번잡해 눈에 피로도를 주지 않으면서 황폐한 뒷거리의 분위기")
  * 판단 기준은 **카메라 2배 확대 화면**(1타일 = 화면 32px, 한 화면 약 30x17타일).
  * 넓은 평면 + 낮은 대비의 줄눈. 1px 잡점(흩뿌림 노이즈) 0. 디테일은 덩어리(2px 이상)로만.
  * 시스템은 좌표 해시로 4변형을 **균등(각 25%)** 하게 섞는다 → 한 변형에 넣은 무늬는 화면 타일의 1/4 에 나온다.
    그래서 금·빠진 블록·그을음은 낮은 대비로 작게, 강조색(잔불)은 시련·보스 방의 한 변형에서 금 사이 1~2px 만.
    배수구·웅덩이처럼 '드물어야 하는' 것은 소품(maxPerRoom) 쪽으로 보낸다.
  * 덩어리 디테일은 타일 경계에서 잘리지 않게 1..14 안쪽에 둔다 (줄눈은 예외: 위·왼쪽 변이 줄눈).

인덱스 표 v3 / JSON 은 `tiles_floors/tilecommon2.py` 의 Sheet2 를 그대로 쓴다 (시스템 변경 없음).
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tiles_floors"))
import tilecommon2 as tc2  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

G, T, ROOT = tc2.G, tc2.T, tc2.ROOT
FONT = tc2.FONT
try:
    FONT_KR = ImageFont.truetype("/usr/share/fonts/truetype/unifont/unifont.ttf", 16)
except Exception:  # pragma: no cover
    FONT_KR = FONT


def colors(floor_no):
    """타일 팔레트 문자표. 무채 10 (K,1~7,9,C) + 층 강조 4 (19 S, 21 B, 23 L, 25 W) — 40라운드 예산 그대로."""
    A = tc2.ramp(floor_no)
    return {
        "K": G[0], "1": G[1], "2": G[2], "3": G[3], "4": G[4],
        "5": G[5], "6": G[6], "7": G[7], "9": G[9], "C": G[12],
        "S": A[3], "B": A[5], "L": A[7], "W": A[9],
    }


# ====================================================================== 포장 기본
class Pave:
    """face = 판석 면, joint = 줄눈. 줄눈은 언제나 타일의 위 변(y=0)·왼 변(x=0) → 어떤 조합으로도 닫힌 판석이 된다."""

    def __init__(self, ctx, face="2", joint="1"):
        self.ctx, self.C, self.face, self.joint = ctx, ctx.C, face, joint

    def new(self):
        return self.ctx.new()

    def base(self, s=None, edges=True):
        s = s or self.new()
        s.rect(0, 0, T - 1, T - 1, self.C[self.face])
        if edges:
            s.line(0, 0, T - 1, 0, self.C[self.joint])
            s.line(0, 0, 0, T - 1, self.C[self.joint])
        return s

    def hj(self, s, y, x0=0, x1=T - 1):
        s.line(x0, y, x1, y, self.C[self.joint])

    def vj(self, s, x, y0=0, y1=T - 1):
        s.line(x, y0, x, y1, self.C[self.joint])

    # ---------------------------------------------------------- 손상 (덩어리만)
    def crack(self, s, pts, col=None):
        """금: 꺾은선. 기본 줄눈색(낮은 대비). col='K' 면 깊은 금."""
        c = self.C[col or self.joint]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            s.line(x0, y0, x1, y1, c)

    def ember(self, s, x, y, hot=False):
        """금 사이 잔불: 어두운 강조 S 2px (가로), hot 이면 가운데 B 1px. 이 이상은 쓰지 않는다."""
        s.px(x, y, self.C["S"]); s.px(x + 1, y, self.C["S"])
        if hot:
            s.px(x, y, self.C["B"])

    def hole(self, s, x0, y0, x1, y1, dirt="1", lip="3"):
        """빠진 블록 자리: 안은 흙(dirt), 빛(좌상단)을 등진 위·왼 턱은 K 그늘, 아래·오른 턱은 빛 받는 lip 1px."""
        C = self.C
        s.rect(x0, y0, x1, y1, C[dirt])
        s.line(x0, y0, x1, y0, C["K"]); s.line(x0, y0, x0, y1, C["K"])
        s.line(x0 + 1, y1 + 1, x1 + 1, y1 + 1, C[lip]); s.line(x1 + 1, y0 + 1, x1 + 1, y1 + 1, C[lip])

    def blob(self, s, cx, cy, r, col, seed, core=None, squash=1.0):
        """매끈한 얼룩(그을음·흙·때): 각도별 반지름을 시드로 흔든 덩어리 — 1px 점이 생기지 않는다. core 면 안쪽 절반을 core 색."""
        rnd = random.Random(seed)
        radii = [r * (0.75 + 0.5 * rnd.random()) for _ in range(8)]

        def rad(a):
            k = a / (2 * math.pi) * 8
            i = int(k) % 8
            f = k - int(k)
            return radii[i] * (1 - f) + radii[(i + 1) % 8] * f

        pts = []
        for y in range(int(cy - r * 1.4) - 1, int(cy + r * 1.4) + 2):
            for x in range(int(cx - r * 1.4) - 1, int(cx + r * 1.4) + 2):
                dx, dy = x - cx, (y - cy) / squash
                d = math.hypot(dx, dy)
                a = math.atan2(dy, dx) % (2 * math.pi)
                if d <= rad(a) and 1 <= x <= T - 2 and 1 <= y <= T - 2:
                    pts.append((x, y, d / max(0.01, rad(a))))
        for x, y, f in pts:
            s.px(x, y, self.C[core] if (core and f < 0.45) else self.C[col])
        return s


# ====================================================================== 2배 목업 (preview_x2)
def load_frame(path_png, path_json, row=0, col=0):
    m = json.load(open(path_json, encoding="utf-8"))
    im = Image.open(path_png).convert("RGBA")
    fw, fh = m["frameWidth"], m["frameHeight"]
    return im.crop((col * fw, row * fh, col * fw + fw, row * fh + fh)), m


def sprite(rel, name, row=0, col=0):
    base = os.path.join(ROOT, "assets", "sprites", rel, name)
    return load_frame(base + ".png", base + ".json", row, col)


def ramp_swap(img, from_floor, to_floor):
    """런타임 팔레트 스왑 흉내: 강조 램프 12칸 1층 → to_floor (계약 §2)."""
    if from_floor == to_floor:
        return img
    A0 = [tc2.hexrgb(c) for c in tc2.ramp(from_floor)]
    A1 = [tc2.hexrgb(c) for c in tc2.ramp(to_floor)]
    m = dict(zip(A0, A1))
    out = img.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a and (r, g, b) in m:
                px[x, y] = m[(r, g, b)] + (a,)
    return out


class Scene:
    """한 화면(30x17타일 = 480x270 월드 px) 목업. 바닥 해시 = 시스템과 같은 '좌표 해시 균등 섞기' 흉내(정확한 해시식은 모름 → 결정적 의사난수)."""

    def __init__(self, tile_img, floor_names, world_w=40, world_h=24, seed=1):
        self.tile_img = tile_img
        self.W, self.H = world_w + 2, world_h + 2
        rnd = random.Random(seed)
        self.grid = [[None] * self.W for _ in range(self.H)]
        for y in range(self.H):
            for x in range(self.W):
                if y == 0:
                    self.grid[y][x] = "wall_top" if x in (0, self.W - 1) else rnd.choice(["wall", "wall", "wall_v1", "wall_v2", "wall"])
                elif y == self.H - 1 or x == 0 or x == self.W - 1:
                    self.grid[y][x] = "wall_top"
                else:
                    self.grid[y][x] = rnd.choice(floor_names)
        self.overlays = []   # (wx, wy, Image) — wy 는 발(바닥) 기준으로 y 정렬
        self.tiles_over = {}

    def put_tile(self, tx, ty, name):
        self.grid[ty][tx] = name

    def put_prop(self, tx, ty, name):
        self.tiles_over[(tx, ty)] = name

    def put_sprite(self, img, pivot, foot_x, foot_y):
        """foot_x/foot_y = 월드 px (발 위치). pivot = 스프라이트의 발 기준점."""
        self.overlays.append((foot_y, foot_x - pivot[0], foot_y - pivot[1], img))

    def render(self, view_tx, view_ty, vw=30, vh=17, extra_py=0):
        world = Image.new("RGBA", (self.W * T, self.H * T + T), (0, 0, 0, 255))
        for y in range(self.H):
            for x in range(self.W):
                world.alpha_composite(self.tile_img(self.grid[y][x]), (x * T, y * T))
        for (x, y), nm in self.tiles_over.items():
            world.alpha_composite(self.tile_img(nm), (x * T, y * T))
        for _, x, y, img in sorted(self.overlays, key=lambda o: o[0]):
            world.alpha_composite(img, (x, y))
        # 화면: vw x vh 타일 (17 타일 = 272 > 270 → 270 으로 자름)
        x0, y0 = view_tx * T, view_ty * T + extra_py
        canvas = Image.new("RGBA", (vw * T, 270), (0, 0, 0, 255))
        canvas.alpha_composite(world.crop((x0, y0, x0 + vw * T, y0 + 270)))
        return canvas


def label(img, text, xy=(6, 4)):
    d = ImageDraw.Draw(img)
    x, y = xy
    for dx, dy in ((1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((x + dx, y + dy), text, fill=(0, 0, 0), font=FONT_KR)
    d.text((x, y), text, fill=(235, 235, 235), font=FONT_KR)


def accent_ratio(img, floor_no):
    acc = set(tc2.hexrgb(c) for c in tc2.ramp(floor_no))
    n = sum(1 for p in img.getdata() if p[:3] in acc)
    return n / (img.width * img.height)
