#!/usr/bin/env python3
# [53라운드 보관] 이 스크립트가 미리보기·목업·마스크 입력으로 읽던 구 시트(assets/sprites/player/player_*, player/v2/*, enemies/{dummy,archer,charger}_*, enemies/v2/*, weapons/katana_* 중 아이콘 외, weapons/v2/*)는 삭제됨 — 해당 단계는 재실행 시 FileNotFoundError.
"""LOPAD 35라운드: 피격 피드백 이펙트 · 적 공격 예고 마커 · 적 투사체 — 단일 소스.

실행: python3 parts/art/work/combat_fx/build.py
입력: parts/art/palette/lopad.json, assets/sprites/player/player_idle.png, assets/sprites/enemies/{dummy,archer}_idle.png (미리보기용)
산출 (assets/sprites/fx/):
  hit_spark        16x16 any  4f 40ms      적중 섬광 (흰 십자 + 22 테두리 → 흩어짐)
  blood            24x24 4방향 5f 50ms     피 튀김 (방향 = 공격 진행 방향, 마지막 프레임 = 바닥 얼룩만, tailFrames 1)
  crit_burst       32x32 any  5f 45ms      치명타 (방사선 8 + 고리)
  knock_dust       16x8  4방향 4f 60ms     넉백 끝 먼지 (G06/G09, 바닥 깊이)
  player_hit       24x24 any  3f 50ms      플레이어 피격 (G13 균열 섬광, 강조 0)
  telegraph_line   8x8   any  2f 120ms 루프 점선 (tile, rotate, scale x)
  telegraph_circle 32x32 any  2f 120ms 루프 원형 범위 외곽선 (scale)
  telegraph_cone   32x32 4방향 2f 120ms 루프 부채꼴 외곽선 (scale)
  enemy_bullet     8x8   any  1f           화승총 탄 (G01 구슬 + 22 꼬리, rotate)
  boss_fan_shot    10x10 any  2f 80ms 루프 부채꼴 탄 (21 코어 + G13 림)
  muzzle_flash     12x12 4방향 2f 40/60ms  사수 총구 화염 (23/25)
  parts/art/work/combat_fx/preview.png, preview_blood_dirs.png, preview_1x.png

설계 메모
  - 전부 1층 '잔' 호박 램프(인덱스 16~27)로 그리고 시스템이 층 램프로 스왑한다. 피도 층 색이다 (팔레트 notes).
  - 색 예산: 무채 <=4 + 강조 <=8 (이펙트 하나 기준).
  - 피격 피드백 앵커는 hitbox_center. 방향 있는 것은 4행(down/up/left/right), 없는 것은 any 1행.
  - 반투명 0, 고립 픽셀 0 (불티는 2px 쌍).
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OUT_FX = os.path.join(ROOT, "assets", "sprites", "fx")
PLAYER = os.path.join(ROOT, "assets", "sprites", "player")
ENEMIES = os.path.join(ROOT, "assets", "sprites", "enemies")
os.makedirs(OUT_FX, exist_ok=True)

with open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8") as fp:
    PAL = json.load(fp)
GRAY = PAL["gray"]
RAMP = PAL["floors"][0]["ramp"]
DIRS = ["down", "up", "left", "right"]
DVEC = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
FLOOR_BG = (0x3e, 0x3f, 0x42, 255)  # G04
PALETTE_NOTE = "parts/art/palette/lopad.json (gray + floor 1 accent slots 16-27, runtime swap)"


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def G(i):
    return hx(GRAY[i])


def C(i):
    """강조 램프 인덱스 16~27."""
    return hx(RAMP[i - 16])


# ============================================================ 캔버스 유틸 (weapons/build.py 와 동일 규약)
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.im.load()

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.p[x, y] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            v = self.p[x, y]
            return v if v[3] else None
        return None

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        x, y = x0, y0
        while True:
            self.px(x, y, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x += sx
            if e2 <= dx:
                err += dx; y += sy

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.25:
                    self.px(x, y, c)

    def ring(self, cx, cy, r, c, thick=1.0, a0=None, a1=None, dash=None):
        """반지름 r 중심선 둘레 1px(thick) 고리. a0..a1 (deg, 화면 좌표 0=우 90=하) 구간 제한, dash=(on,off) 는 각도 단위."""
        for y in range(self.h):
            for x in range(self.w):
                d = math.hypot(x - cx, y - cy)
                if abs(d - r) > thick / 2.0:
                    continue
                if a0 is not None:
                    th = math.degrees(math.atan2(y - cy, x - cx))
                    if (th - a0) % 360 > (a1 - a0) % 360 and (a1 - a0) % 360 != 0:
                        continue
                if dash:
                    th = math.degrees(math.atan2(y - cy, x - cx)) % 360
                    if th % (dash[0] + dash[1]) >= dash[0]:
                        continue
                self.px(x, y, c)

    def blit(self, rows, ox, oy, legend):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    self.px(ox + i, oy + j, legend[ch])

    def pair(self, x, y, c, horiz=True):
        """2픽셀 불티 (고립 금지)."""
        self.px(x, y, c)
        self.px(x + (1 if horiz else 0), y + (0 if horiz else 1), c)

    def despeckle8(self):
        rm = []
        for y in range(self.h):
            for x in range(self.w):
                if self.p[x, y][3] and not any(self.get(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)):
                    rm.append((x, y))
        for x, y in rm:
            self.p[x, y] = (0, 0, 0, 0)
        return len(rm)

    def isolated(self):
        n = 0
        for y in range(self.h):
            for x in range(self.w):
                if self.p[x, y][3] and not any(self.get(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)):
                    n += 1
        return n

    def rot90(self, k):
        """캔버스를 90도 단위로 회전한 새 캔버스 (픽셀 밀도 유지 — 90도 회전은 허용)."""
        im = self.im.rotate(90 * k, expand=True)
        cv = Canvas(im.width, im.height)
        cv.im, cv.p = im, im.load()
        return cv

    def flip_x(self):
        im = self.im.transpose(Image.FLIP_LEFT_RIGHT)
        cv = Canvas(im.width, im.height)
        cv.im, cv.p = im, im.load()
        return cv


def rot_pt(cx, cy, x, y, d):
    """'right' 기준으로 그린 좌표 (x,y) 를 방향 d 로 돌린다 (중심 cx,cy). 정수 좌표만."""
    dx, dy = x - cx, y - cy
    if d == "right":
        return x, y
    if d == "left":
        return cx - dx, cy + dy
    if d == "down":
        return cx + dy, cy + dx   # 우 → 하 (시계 방향 90)
    if d == "up":
        return cx + dy, cy - dx
    raise ValueError(d)


# ============================================================ 시트 저장
def save_sheet(name, frames_by_dir, dirs, w, h, durations, loop, pivot, extra, action=None):
    n = len(durations)
    sheet = Image.new("RGBA", (w * n, h * len(dirs)), (0, 0, 0, 0))
    for r, d in enumerate(dirs):
        for c, cv in enumerate(frames_by_dir[d]):
            sheet.alpha_composite(cv.im, (c * w, r * h))
    sheet.save(os.path.join(OUT_FX, name + ".png"))
    meta = {
        "image": name + ".png",
        "action": action or name,
        "frameWidth": w, "frameHeight": h,
        "frames": n,
        "directions": dirs,
        "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column",
        "fps": round(1000.0 / (sum(durations) / n)) if sum(durations) else 0,
        "frameDurationsMs": durations,
        "loop": loop,
        "pivot": {"x": pivot[0], "y": pivot[1]},
        "palette": PALETTE_NOTE,
    }
    meta.update(extra)
    with open(os.path.join(OUT_FX, name + ".json"), "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    return sheet


def color_report(name, frames_by_dir, gray_budget=4, accent_budget=8):
    cols = set()
    iso = semi = 0
    for d, fr in frames_by_dir.items():
        for cv in fr:
            iso += cv.isolated()
            for px in cv.im.getdata():
                if px[3] == 255:
                    cols.add(px[:3])
                elif px[3]:
                    semi += 1
    gs = [G(i)[:3] for i in range(16)]
    cs = [C(i)[:3] for i in range(16, 28)]
    grays = sorted(gs.index(c) for c in cols if c in gs)
    accents = sorted(16 + cs.index(c) for c in cols if c in cs)
    other = [c for c in cols if c not in gs and c not in cs]
    flag = ""
    if len(grays) > gray_budget or len(accents) > accent_budget or other or iso or semi:
        flag = "  <-- CHECK"
    print("%-17s gray%s accent%s other=%d iso=%d semi=%d%s" % (name, grays, accents, len(other), iso, semi, flag))


# ============================================================ 1. hit_spark 16x16 any 4f
def hit_spark_frames():
    cx, cy = 8, 8
    W, L, E = G(15), G(13), C(22)   # 흰 코어 / 밝은 쇠 / 강조 테두리
    frames = []
    # f0 압축된 코어: 3x3 흰 + 십자 팁 + 테두리
    cv = Canvas(16, 16)
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        cv.px(cx + dx, cy + dy, W)
    for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        cv.px(cx + dx, cy + dy, L)
    for dx, dy in ((3, 0), (-3, 0), (0, 3), (0, -3), (1, 1), (-1, 1), (1, -1), (-1, -1)):
        cv.px(cx + dx, cy + dy, E)
    frames.append(cv)
    # f1 최대 십자: 팔 길이 6, 중심 3x3 흰, 팔은 흰→G13, 끝 1px 22. 대각 짧은 보조선 22
    cv = Canvas(16, 16)
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            cv.px(cx + dx, cy + dy, W)
    for k in range(2, 7):
        col = W if k <= 3 else L
        if k == 6:
            col = E
        cv.px(cx + k, cy, col); cv.px(cx - k, cy, col); cv.px(cx, cy + k, col); cv.px(cx, cy - k, col)
    # 팔 옆 1px 두께감 (k=2..3) 22
    for k in (2, 3):
        cv.px(cx + k, cy - 1, E); cv.px(cx + k, cy + 1, E); cv.px(cx - k, cy - 1, E); cv.px(cx - k, cy + 1, E)
        cv.px(cx - 1, cy + k, E); cv.px(cx + 1, cy + k, E); cv.px(cx - 1, cy - k, E); cv.px(cx + 1, cy - k, E)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cv.px(cx + 2 * sx, cy + 2 * sy, E); cv.px(cx + 3 * sx, cy + 3 * sy, E)
    frames.append(cv)
    # f2 끊어진 십자: 중심 비고, 팔이 바깥쪽 조각(2~3px)으로. 색 G13 + 22
    cv = Canvas(16, 16)
    for k in range(4, 8):
        col = L if k < 6 else E
        cv.px(cx + k, cy, col); cv.px(cx - k, cy, col); cv.px(cx, cy + k, col); cv.px(cx, cy - k, col)
    cv.px(cx, cy, E); cv.px(cx + 1, cy, E)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cv.px(cx + 3 * sx, cy + 3 * sy, E); cv.px(cx + 4 * sx, cy + 4 * sy, E)
    frames.append(cv)
    # f3 흩어짐: 2px 쌍 6개, 22/21
    cv = Canvas(16, 16)
    cv.pair(cx + 6, cy - 1, C(22)); cv.pair(cx - 7, cy + 1, C(22))
    cv.pair(cx - 1, cy + 6, C(21), horiz=False); cv.pair(cx + 1, cy - 7, C(21), horiz=False)
    cv.pair(cx + 4, cy + 4, C(21)); cv.pair(cx - 5, cy - 5, C(21))
    frames.append(cv)
    for f in frames:
        f.despeckle8()
    return {"any": frames}


# ============================================================ 2. blood 24x24 4방향 5f
def blood_frames():
    """방울 5개가 진행 방향(±35°)으로 날아가며 작아지고, 바닥에 2px 얼룩 2개를 남긴다. 마지막 프레임은 얼룩만."""
    cx, cy = 12, 12
    rnd = random.Random(35)
    # 방울: (각도 오프셋 deg, 속도 px/frame, 시작 반지름)
    drops = [(-30, 2.6, 1.6), (-10, 3.2, 1.2), (8, 2.2, 1.9), (26, 3.0, 1.1), (38, 1.7, 1.0)]
    BODY, DARK, LIGHT, GLINT = C(19), C(17), C(20), C(22)
    STAIN_D, STAIN = C(17), C(18)
    stains = [(-12, 5.5), (18, 9.0)]   # (각도, 거리) — 바닥 얼룩 위치
    out = {}
    for d in DIRS:
        base = {"right": 0, "left": 180, "down": 90, "up": 270}[d]
        frames = []
        for f in range(5):
            cv = Canvas(24, 24)
            # 얼룩: f>=2 첫 번째, f>=3 두 번째 (방울이 그 자리에 떨어진 뒤)
            for si, (sa, sd) in enumerate(stains):
                if f >= 2 + si:
                    a = math.radians(base + sa)
                    sx, sy = int(round(cx + sd * math.cos(a))), int(round(cy + sd * math.sin(a)))
                    cv.pair(sx, sy, STAIN_D if f == 4 else STAIN)
                    if f < 4:
                        cv.px(sx + 1, sy + 1, STAIN_D)   # 신선할 때는 3px
            if f == 4:
                # 얼룩만 남음 (중심 쪽 작은 점 하나 추가 — 2px 쌍)
                a = math.radians(base + 5)
                cv.pair(int(round(cx + 2 * math.cos(a))), int(round(cy + 2 * math.sin(a))), STAIN_D)
                frames.append(cv)
                continue
            if f == 0:
                # 터짐: 진행 방향으로 늘어진 울퉁불퉁한 덩어리 (원형 금지)
                a = math.radians(base)
                ux, uy = math.cos(a), math.sin(a)
                cv.disc(cx - 0.6 * ux, cy - 0.6 * uy, 1.9, DARK)
                cv.disc(cx + 1.4 * ux, cy + 1.4 * uy, 1.6, BODY)
                cv.disc(cx + 0.2 * ux, cy + 0.2 * uy, 1.2, BODY)
                # 가장자리 톱니: 수직 방향으로 1px 돌기 2개, 뒤쪽 1px
                vx, vy = -uy, ux
                cv.px(int(round(cx + 2.6 * vx + 0.5 * ux)), int(round(cy + 2.6 * vy + 0.5 * uy)), DARK)
                cv.px(int(round(cx - 2.6 * vx + 1.0 * ux)), int(round(cy - 2.6 * vy + 1.0 * uy)), DARK)
                cv.px(int(round(cx - 2.8 * ux)), int(round(cy - 2.8 * uy)), DARK)
                cv.px(int(round(cx + 0.8 * ux - 0.8 * vx)), int(round(cy + 0.8 * uy - 0.8 * vy)), LIGHT)
                cv.px(int(round(cx + 1.2 * ux)), int(round(cy + 1.2 * uy)), GLINT)
            for di, (ang, spd, r0) in enumerate(drops):
                a = math.radians(base + ang)
                dist = 1.5 + spd * f * 1.15
                r = max(0.6, r0 - 0.35 * f)
                if f >= 3 and di in (0, 3):
                    continue   # 일부 방울은 바닥에 떨어졌다(얼룩으로 전환)
                x, y = cx + dist * math.cos(a), cy + dist * math.sin(a)
                col = BODY if f < 3 else DARK
                cv.disc(x, y, r, col)
                if r >= 1.2:
                    cv.px(int(round(x - 0.7)), int(round(y - 0.7)), LIGHT)
                    # 꼬리 1~2px (진행 반대 방향)
                    tx, ty = int(round(x - 1.6 * math.cos(a))), int(round(y - 1.6 * math.sin(a)))
                    cv.px(tx, ty, DARK)
                elif r < 1.0:
                    # 작은 방울은 2px 쌍 (고립 방지)
                    cv.px(int(round(x - math.cos(a))), int(round(y - math.sin(a))), DARK)
            if f == 1:
                cv.px(cx, cy, DARK); cv.px(cx + 1, cy, DARK)
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


# ============================================================ 3. crit_burst 32x32 any 5f
def crit_burst_frames():
    cx, cy = 16, 16
    W, A25, A23, A22, A21, A19 = G(15), C(25), C(23), C(22), C(21), C(19)
    seq = [
        dict(core=2.6, core_c=W, rim=A25, lines=(2, 5), lc=(A25, A23), ring=None),
        dict(core=1.6, core_c=W, rim=A25, lines=(3, 9), lc=(A25, A23), ring=(5.5, A25, None)),
        dict(core=0.0, core_c=None, rim=None, lines=(7, 12), lc=(A23, A22), ring=(9.5, A23, None)),
        dict(core=0.0, core_c=None, rim=None, lines=(11, 14), lc=(A22, A21), ring=(12.5, A21, (20, 12))),
        dict(core=0.0, core_c=None, rim=None, lines=None, lc=None, ring=(14.5, A19, (12, 24))),
    ]
    frames = []
    for i, st in enumerate(seq):
        cv = Canvas(32, 32)
        if st["ring"]:
            r, c, dash = st["ring"]
            cv.ring(cx, cy, r, c, 1.0, dash=dash)
        if st["lines"]:
            r0, r1 = st["lines"]
            for k in range(8):
                ang = math.radians(k * 45)
                # 축 방향(상하좌우)은 안쪽 색을 더 길게 = 십자가 강조
                mid = r0 + (r1 - r0) * (0.6 if k % 2 == 0 else 0.4)
                for rr in range(r0, r1 + 1):
                    x, y = int(round(cx + rr * math.cos(ang))), int(round(cy + rr * math.sin(ang)))
                    cv.px(x, y, st["lc"][0] if rr <= mid else st["lc"][1])
                if i <= 1 and k % 2 == 0:
                    # 축 선 2px 두께 (안쪽 절반)
                    for rr in range(r0, int(mid) + 1):
                        x, y = cx + rr * math.cos(ang), cy + rr * math.sin(ang)
                        px_, py_ = int(round(x - math.sin(ang))), int(round(y + math.cos(ang)))
                        cv.px(px_, py_, A23)
        if st["core"] > 0:
            cv.disc(cx, cy, st["core"] + 1.0, st["rim"])
            cv.disc(cx, cy, st["core"], st["core_c"])
        if i == 2:
            cv.pair(cx, cy, A22)
        if i == 4:
            cv.pair(cx + 13, cy - 4, A21); cv.pair(cx - 14, cy + 3, A21, horiz=False)
            cv.pair(cx + 3, cy + 14, A19); cv.pair(cx - 4, cy - 14, A19)
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


# ============================================================ 4. knock_dust 16x8 4방향 4f
def knock_dust_frames():
    """넉백이 멈춘 자리 발 앞에서 먼지가 일어난다. 'right' 기준으로 그린 뒤 left 는 좌우 반전,
    down/up 은 좌우 대칭형(진행 방향이 화면 상하라 앞뒤 구분이 안 되므로) 으로 별도 그림."""
    D, M = G(6), G(9)
    out = {}
    # 우향: 피벗 (8,6) = 발 접지점. 먼지는 진행 방향(오른쪽) 앞으로 밀리고, 뒤로 작은 꼬리
    seq_r = [
        [("disc", 9, 6, 1.6, M), ("disc", 11, 6, 1.2, D), ("pair", 5, 6, D)],
        [("disc", 11, 5, 2.0, D), ("disc", 12, 4, 1.4, M), ("disc", 8, 6, 1.4, M), ("pair", 4, 6, D)],
        [("disc", 13, 4, 1.8, D), ("disc", 14, 3, 1.0, M), ("disc", 9, 5, 1.2, D), ("pair", 10, 3, M), ("pair", 5, 5, D)],
        [("disc", 14, 3, 1.2, D), ("pair", 12, 2, M), ("pair", 9, 4, D), ("pair", 6, 5, D)],
    ]
    seq_v = [   # 상하: 양옆으로 대칭 퍼짐 (down: 위쪽으로 떠오름 / up: 같은 그림을 상하 반전)
        [("disc", 6, 6, 1.4, M), ("disc", 10, 6, 1.4, M), ("pair", 8, 6, D)],
        [("disc", 4, 5, 1.8, D), ("disc", 12, 5, 1.8, D), ("disc", 5, 4, 1.0, M), ("disc", 11, 4, 1.0, M), ("pair", 7, 6, M)],
        [("disc", 3, 4, 1.6, D), ("disc", 13, 4, 1.6, D), ("pair", 2, 3, M), ("pair", 13, 3, M), ("pair", 7, 5, D)],
        [("pair", 2, 3, D), ("pair", 13, 3, D), ("pair", 5, 4, M), ("pair", 10, 4, M)],
    ]

    def build(seq):
        fr = []
        for ops in seq:
            cv = Canvas(16, 8)
            for op in ops:
                if op[0] == "disc":
                    cv.disc(op[1], op[2], op[3], op[4])
                else:
                    cv.pair(op[1], op[2], op[3])
            cv.despeckle8()
            fr.append(cv)
        return fr

    right = build(seq_r)
    out["right"] = right
    out["left"] = [cv.flip_x() for cv in right]
    down = build(seq_v)
    out["down"] = down
    # up: 먼지가 캐릭터 발 앞(= 화면 위쪽)이지만 그림은 바닥에 깔리는 것이라 같은 모양을 쓰고 1px 위로
    up = []
    for cv in down:
        c2 = Canvas(16, 8)
        c2.im.alpha_composite(cv.im, (0, 0))
        c2.p = c2.im.load()
        up.append(c2)
    out["up"] = up
    return out


# ============================================================ 5. player_hit 24x24 any 3f
def player_hit_frames():
    """무채 균열 섬광. 중심에서 5갈래 꺾인 금. G15 코어 → G13 금 → G09 끝 → G06 잔재."""
    cx, cy = 12, 12
    W, L, M, D = G(15), G(13), G(9), G(6)
    # 금: (시작 각도, 길이1, 꺾임 각도, 길이2) — 'right' 기준이 아니라 절대 각도 (any 방향)
    cracks = [(-80, 4, 35, 4), (-20, 5, -40, 3), (40, 4, 45, 4), (120, 5, -30, 3), (200, 4, 40, 4), (260, 3, -45, 3)]

    def crack_pts(ang, l1, bend, l2, scale=1.0):
        pts = []
        a = math.radians(ang)
        x, y = cx, cy
        x1, y1 = x + l1 * scale * math.cos(a), y + l1 * scale * math.sin(a)
        pts.append(((x, y), (x1, y1)))
        a2 = math.radians(ang + bend)
        x2, y2 = x1 + l2 * scale * math.cos(a2), y1 + l2 * scale * math.sin(a2)
        pts.append(((x1, y1), (x2, y2)))
        return pts

    frames = []
    # f0: 코어 + 짧은 금
    cv = Canvas(24, 24)
    for ang, l1, bend, l2 in cracks:
        segs = crack_pts(ang, l1, bend, l2, 0.9)
        (x0, y0), (x1, y1) = segs[0]
        cv.line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)), L)
    cv.disc(cx, cy, 2.2, L)
    cv.disc(cx, cy, 1.3, W)
    frames.append(cv)
    # f1: 금 최대, 코어 작아짐, 끝은 G09
    cv = Canvas(24, 24)
    for ang, l1, bend, l2 in cracks:
        segs = crack_pts(ang, l1, bend, l2, 1.0)
        (x0, y0), (x1, y1) = segs[0]
        (x1b, y1b), (x2, y2) = segs[1]
        cv.line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)), L)
        cv.line(int(round(x1b)), int(round(y1b)), int(round(x2)), int(round(y2)), M)
    cv.disc(cx, cy, 1.4, L)
    cv.px(cx, cy, W)
    # 금 안쪽에 두께: 코어 근처 2px
    for ang, l1, bend, l2 in cracks:
        a = math.radians(ang)
        cv.px(int(round(cx + 2 * math.cos(a) - math.sin(a))), int(round(cy + 2 * math.sin(a) + math.cos(a))), L)
    frames.append(cv)
    # f2: 바깥 조각만 남아 어두워짐 (G09/G06), 코어 없음
    cv = Canvas(24, 24)
    for ang, l1, bend, l2 in cracks:
        segs = crack_pts(ang, l1, bend, l2, 1.15)
        (x1b, y1b), (x2, y2) = segs[1]
        mx, my = (x1b + x2) / 2, (y1b + y2) / 2
        cv.line(int(round(mx)), int(round(my)), int(round(x2)), int(round(y2)), M)
        cv.px(int(round(x2)), int(round(y2)), D)
    cv.pair(cx - 1, cy, D)
    frames.append(cv)
    for f in frames:
        f.despeckle8()
    return {"any": frames}


# ============================================================ 6. telegraph 마커
def telegraph_line_frames():
    """8x8 타일. 우향, 2px 두께 점선 (3 on 1 off, 8 주기로 이어붙임 가능). f0 밝음 / f1 어두움 = 깜빡."""
    frames = []
    for bright in (True, False):
        cv = Canvas(8, 8)
        top, bot = (C(22), C(20)) if bright else (C(20), C(18))
        for x in range(8):
            if x % 4 == 3:
                continue
            cv.px(x, 3, top)
            cv.px(x, 4, bot)
        frames.append(cv)
    return {"any": frames}


def telegraph_circle_frames():
    cx, cy = 16, 16
    frames = []
    # f0: 22 고리 r14.5 + 안쪽 4 눈금(21) / f1: 20 고리 점선 + 눈금 18
    cv = Canvas(32, 32)
    cv.ring(cx - 0.5, cy - 0.5, 14.5, C(22), 1.1)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k in (12, 13):
            cv.px(int(round(cx - 0.5 + dx * k)), int(round(cy - 0.5 + dy * k)), C(21))
    cv.pair(cx - 1, cy, C(21)); cv.pair(cx - 1, cy - 1, C(21))
    frames.append(cv)
    cv = Canvas(32, 32)
    cv.ring(cx - 0.5, cy - 0.5, 14.5, C(20), 1.1, dash=(24, 12))
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for k in (12, 13):
            cv.px(int(round(cx - 0.5 + dx * k)), int(round(cy - 0.5 + dy * k)), C(18))
    cv.pair(cx - 1, cy, C(18)); cv.pair(cx - 1, cy - 1, C(18))
    frames.append(cv)
    for f in frames:
        f.despeckle8()
    return {"any": frames}


def telegraph_cone_frames(half=32):
    """꼭짓점 = 중심 (16,16), 반지름 15, 반각 half°. 외곽선만: 두 변 + 호. 우향 그린 뒤 90도 회전."""
    cx, cy = 16, 16
    out = {}
    base = []
    for bright in (True, False):
        cv = Canvas(32, 32)
        edge, arc_c = (C(22), C(22)) if bright else (C(20), C(19))
        r = 14.5
        for s in (-1, 1):
            a = math.radians(s * half)
            cv.line(cx, cy, int(round(cx + (r + 1.0) * math.cos(a))), int(round(cy + (r + 1.0) * math.sin(a))), edge)
        cv.ring(cx, cy, r, arc_c, 1.1, a0=-half, a1=half, dash=None if bright else (18, 9))
        # 꼭짓점 2x2 + 중심선 점 3개 (안쪽 방향 지시)
        cv.px(cx, cy, edge); cv.px(cx, cy + 1, edge); cv.px(cx + 1, cy, edge); cv.px(cx + 1, cy + 1, edge)
        for k in (5, 6, 9, 10):
            cv.px(cx + k, cy, C(20) if bright else C(18))
        cv.despeckle8()
        base.append(cv)
    out["right"] = base
    out["left"] = [cv.flip_x() for cv in base]
    # 90도 회전: right → down 은 시계 방향 90 = PIL rotate(-90)
    out["down"] = [cv.rot90(-1) for cv in base]
    out["up"] = [cv.rot90(1) for cv in base]
    return out


# ============================================================ 7. 적 투사체
def enemy_bullet_frames():
    """8x8 우향. G01 구슬(3x3) + G09 글린트 1px + 22 꼬리 2px (뒤 = 왼쪽)."""
    cv = Canvas(8, 8)
    rows = [
        "........",
        "........",
        ".....KK.",
        ".ttgKKKK",
        "..tKKKKK",
        ".....KK.",
        "........",
        "........",
    ]
    cv.blit(rows, 0, 0, {"K": G(1), "g": G(9), "t": C(22)})
    return {"any": [cv]}


def boss_fan_shot_frames():
    """10x10. 21 코어 r2 + G13 림 1px. f1 은 코어 22 + 24 중심 1px (맥동)."""
    frames = []
    f0 = [
        "..........",
        "...RRRR...",
        "..RccccR..",
        ".RcchcccR.",
        ".RchhcccR.",
        ".RcccccdR.",
        ".RccccddR.",
        "..RcdddR..",
        "...RRRR...",
        "..........",
    ]
    f1 = [
        "..........",
        "...RRRR...",
        "..RbbbbR..",
        ".RbbHbbbR.",
        ".RbHHHbbR.",
        ".RbbHbbbR.",
        ".RbbbbbcR.",
        "..RbbccR..",
        "...RRRR...",
        "..........",
    ]
    leg = {"R": G(13), "c": C(21), "h": C(23), "d": C(19), "b": C(22), "H": C(24)}
    for rows in (f0, f1):
        cv = Canvas(10, 10)
        cv.blit(rows, 0, 0, leg)
        frames.append(cv)
    return {"any": frames}


def muzzle_flash_frames():
    """12x12, 피벗 (6,6) = 총구. 우향: 총구에서 오른쪽으로 뻗는 불꽃(25 코어, 23 가장자리, 27 팁 1px)."""
    base = []
    # 총구 (6,6). W=27 코어, a=25, b=23, c=22. 앞으로 뻗는 쐐기 + 앞쪽 대각 광선 2개 + 위아래 짧은 불티
    f0 = [
        "............",
        "............",
        ".........b..",
        ".......bb.b.",
        ".....ab..b..",
        ".....Waa.bb.",
        "....aWWWaab.",
        ".....Waa.bb.",
        ".....ab..b..",
        ".......bb.b.",
        ".........b..",
        "............",
    ]
    f1 = [
        "............",
        "............",
        "............",
        "............",
        "......b.b...",
        ".....abbc...",
        ".....aaac...",
        ".....abbc...",
        "......b.b...",
        "............",
        "............",
        "............",
    ]
    leg = {"W": C(27), "a": C(25), "b": C(23), "c": C(22)}
    for rows in (f0, f1):
        cv = Canvas(12, 12)
        cv.blit(rows, 0, 0, leg)
        base.append(cv)
    for f in base:
        f.despeckle8()
    out = {"right": base, "left": [cv.flip_x() for cv in base],
           "down": [cv.rot90(-1) for cv in base], "up": [cv.rot90(1) for cv in base]}
    return out


# ============================================================ 미리보기
def label(d, xy, text, col=(230, 230, 230)):
    d.text(xy, text, fill=col, font=FONT)


def scaled(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def sheet_block(name, fbd, dirs, w, h, pivot, durs, k=3):
    n = len(durs)
    cw, ch = w * k, h * k
    gap = 3
    bw = 60 + n * (cw + gap)
    bh = 16 + len(dirs) * (ch + gap)
    blk = Image.new("RGB", (bw, bh), (34, 34, 38))
    d = ImageDraw.Draw(blk)
    label(d, (4, 1), "%s %dx%d %s pivot(%d,%d) %s" % (name, w, h, "/".join(dirs), pivot[0], pivot[1], durs))
    for r, dd in enumerate(dirs):
        label(d, (4, 16 + r * (ch + gap) + ch // 2 - 6), dd)
        for c in range(n):
            cell = Image.new("RGBA", (w, h), FLOOR_BG)
            cell.alpha_composite(fbd[dd][c].im)
            blk.paste(scaled(cell, k).convert("RGB"), (60 + c * (cw + gap), 16 + r * (ch + gap)))
    return blk


def scene_block(fx, k=3):
    """바닥 G04 위에 주인공 + 더미 + 사수를 놓고 이펙트를 실제 위치에 얹은 배치 예 (3배와 1배)."""
    pidle = Image.open(os.path.join(PLAYER, "player_idle.png")).convert("RGBA")
    didle = Image.open(os.path.join(ENEMIES, "dummy_idle.png")).convert("RGBA")
    aidle = Image.open(os.path.join(ENEMIES, "archer_idle.png")).convert("RGBA")
    pf = pidle.crop((0, 0, 16, 24))                 # down
    df = didle.crop((0, 0, 16, 24))
    af = aidle.crop((0, 2 * 24, 16, 3 * 24))        # left
    W, H = 232, 72
    scene = Image.new("RGBA", (W, H), FLOOR_BG)
    # 바닥 격자 느낌 (G03 점) — 1배 가독 확인용 배경 노이즈
    sp = scene.load()
    for y in range(0, H, 8):
        for x in range(0, W, 8):
            sp[x, y] = (0x2f, 0x30, 0x33, 255)

    def put(im, x, y):
        scene.alpha_composite(im, (x, y))

    def fx_at(name, d, f, hx_, hy_):
        """이펙트 프레임 f 를 피벗이 (hx_,hy_) 에 오게 얹는다."""
        fbd, dirs, w, h, pivot = fx[name][1], fx[name][2], fx[name][3], fx[name][4], fx[name][5]
        put(fbd[d][f].im, hx_ - pivot[0], hy_ - pivot[1])

    # 1) 더미 A: hit_spark f1 + blood right f1 (히트박스 중심 = 몸 중심 (8,13))
    x, y = 24, 24
    put(df, x, y)
    fx_at("knock_dust", "right", 1, x + 8, y + 23)
    fx_at("blood", "right", 1, x + 8, y + 13)
    fx_at("hit_spark", "any", 1, x + 8, y + 13)
    # 2) 더미 B: crit_burst f1 + blood down f2
    x, y = 70, 24
    put(df, x, y)
    fx_at("blood", "down", 2, x + 8, y + 13)
    fx_at("crit_burst", "any", 1, x + 8, y + 13)
    # 3) 주인공: player_hit f1
    x, y = 112, 26
    put(pf, x, y)
    fx_at("player_hit", "any", 1, x + 8, y + 13)
    # 4) 사수: 좌향, muzzle_flash left f0, enemy_bullet 날아감, telegraph_line 3타일
    x, y = 200, 22
    for i in range(3):
        fx_at("telegraph_line", "any", 0, x - 2 - (i + 1) * 8, y + 13 - 4)   # 왼쪽으로 3타일 (피벗 (0,4))
    put(af, x, y)
    fx_at("muzzle_flash", "left", 0, x - 1, y + 11)
    fx_at("enemy_bullet", "any", 0, x - 14, y + 11)   # 우향 그림, 좌향은 시스템이 회전 — 여기선 미반전 참고
    # 5) 바닥 예고: telegraph_circle f0 (좌하), telegraph_cone down f0 (사수 아래)
    fx_at("telegraph_circle", "any", 0, 160, 50)
    fx_at("telegraph_cone", "down", 0, 200 + 8, 50)
    fx_at("boss_fan_shot", "any", 0, 150, 18)
    fx_at("boss_fan_shot", "any", 1, 164, 14)
    big = scaled(scene, k).convert("RGB")
    blk = Image.new("RGB", (big.width + 16 + scene.width, big.height + 20), (24, 24, 28))
    d = ImageDraw.Draw(blk)
    label(d, (4, 2), "scene x%d (floor G04; dummy: knock_dust+blood+hit_spark / dummy: crit+blood / player_hit / archer: telegraph_line, muzzle, bullet / circle, cone, fan_shot)   right: 1x" % k)
    blk.paste(big, (0, 18))
    blk.paste(scene.convert("RGB"), (big.width + 12, 18))
    return blk


def preview_all(fx):
    blocks = [sheet_block(n, *v[1:7]) for n, v in fx.items()]
    scene = scene_block(fx)
    col_w = max(max(b.width for b in blocks), scene.width // 2)
    half = (len(blocks) + 1) // 2
    cols = [blocks[:half], blocks[half:]]
    heights = [sum(b.height + 6 for b in c) for c in cols]
    img = Image.new("RGB", (max(col_w * 2 + 24, scene.width + 16), max(heights) + scene.height + 32), (24, 24, 28))
    img.paste(scene, (8, 8))
    for ci, c in enumerate(cols):
        y = scene.height + 20
        for b in c:
            img.paste(b, (8 + ci * (col_w + 8), y))
            y += b.height + 6
    img.save(os.path.join(HERE, "preview.png"))


def preview_blood(fx):
    """피 4방향 x 5프레임, 더미 위에 얹어 4배. 오른쪽에 1배."""
    k = 4
    didle = Image.open(os.path.join(ENEMIES, "dummy_idle.png")).convert("RGBA")
    fbd = fx["blood"][1]
    w, h, pivot = 24, 24, fx["blood"][5]
    durs = fx["blood"][6]
    cw, ch, gap = w * k, h * k, 4
    img = Image.new("RGB", (60 + 5 * (cw + gap) + 8 + 5 * (w + 2), 20 + 4 * (ch + gap)), (24, 24, 28))
    d = ImageDraw.Draw(img)
    label(d, (4, 2), "blood 24x24 4dir x 5f %s  (dir = attack travel direction; last frame = stain only, tailFrames 1)  right: 1x" % durs)
    for r, dd in enumerate(DIRS):
        label(d, (4, 20 + r * (ch + gap) + ch // 2 - 6), dd)
        row = DIRS.index(dd)
        df = didle.crop((0, row * 24, 16, row * 24 + 24))
        for c in range(5):
            cell = Image.new("RGBA", (w, h), FLOOR_BG)
            cell.alpha_composite(df, (pivot[0] - 8, pivot[1] - 13))
            cell.alpha_composite(fbd[dd][c].im)
            img.paste(scaled(cell, k).convert("RGB"), (60 + c * (cw + gap), 20 + r * (ch + gap)))
            img.paste(cell.convert("RGB"), (60 + 5 * (cw + gap) + 8 + c * (w + 2), 20 + r * (ch + gap)))
    img.save(os.path.join(HERE, "preview_blood_dirs.png"))


def preview_1x(fx):
    """1배 가독성 점검: 각 이펙트 프레임을 바닥 G04 위에 1배로 나열한 뒤, 그 전체를 2배로만 키운 그림."""
    strips = []
    for name, v in fx.items():
        fbd, dirs, w, h = v[1], v[2], v[3], v[4]
        n = len(v[6])
        st = Image.new("RGBA", (n * (w + 2) + 2, h + 2), FLOOR_BG)
        for c in range(n):
            st.alpha_composite(fbd[dirs[0] if dirs[0] != "any" else "any"][c].im, (2 + c * (w + 2), 1))
        strips.append((name, st))
    W = max(s.width for _, s in strips) + 120
    H = sum(s.height + 6 for _, s in strips) + 8
    img = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(img)
    y = 4
    for name, st in strips:
        label(d, (4, y + st.height // 2 - 6), name)
        img.paste(st.convert("RGB"), (116, y))
        y += st.height + 6
    scaled(img, 2).save(os.path.join(HERE, "preview_1x.png"))


# ============================================================ main
def main():
    fx = {}
    # name: (action, frames_by_dir, dirs, w, h, pivot, durations, loop, extra)
    fx["hit_spark"] = ("hit_spark", hit_spark_frames(), ["any"], 16, 16, (8, 8), [40, 40, 40, 40], False,
                       {"anchor": "hitbox_center", "spawn": "hit",
                        "note": "피격 판정 즉시 1회. 적중 지점(히트박스 중심 또는 공격 접점)에. 플레이어 위 깊이."})
    fx["blood"] = ("blood", blood_frames(), DIRS, 24, 24, (12, 12), [50, 50, 50, 50, 50], False,
                   {"anchor": "hitbox_center", "spawn": "hit", "tailFrames": 1,
                    "directionMeaning": "피가 튀는 방향 = 공격 진행 방향 (플레이어 → 적 벡터를 4방향으로 양자화)",
                    "note": "마지막 프레임(index 4)은 바닥 얼룩만 — 시스템이 원하면 그 프레임을 300~800ms 유지 후 페이드 가능. 바닥 깊이(캐릭터 아래) 권장. 피 색 = 현재 층 강조 램프 17~23 (런타임 스왑)."})
    fx["crit_burst"] = ("crit_burst", crit_burst_frames(), ["any"], 32, 32, (16, 16), [45, 45, 45, 45, 45], False,
                        {"anchor": "hitbox_center", "spawn": "hit_crit",
                         "note": "치명타 시 hit_spark 대신(또는 hit_spark 위에) 재생. 플레이어 위 깊이."})
    fx["knock_dust"] = ("knock_dust", knock_dust_frames(), DIRS, 16, 8, (8, 6), [60, 60, 60, 60], False,
                        {"anchor": "hitbox_center", "spawn": "knockback_end",
                         "pivotNote": "피벗 (8,6) = 발 접지점. 히트박스 중심에서 아래로 히트박스 반높이(16x24 적이면 약 +10px) 내려 놓는다.",
                         "directionMeaning": "넉백 진행 방향 (밀려간 방향). 먼지는 그 앞쪽으로 밀린다.",
                         "note": "바닥 깊이(캐릭터 아래). 무채만 쓰므로 층 스왑 영향 없음."})
    fx["player_hit"] = ("player_hit", player_hit_frames(), ["any"], 24, 24, (12, 12), [50, 50, 50], False,
                        {"anchor": "hitbox_center", "spawn": "player_hurt",
                         "note": "플레이어 피격 시 player_hurt 1프레임과 동시에. 강조색 0 — 주인공은 피를 흘리지 않는다(반 시체). 플레이어 위 깊이."})
    fx["telegraph_line"] = ("telegraph_line", telegraph_line_frames(), ["any"], 8, 8, (0, 4), [120, 120], True,
                            {"anchor": "hitbox_center", "spawn": "telegraph", "tile": True, "rotate": True, "drawnFacing": "right",
                             "scale": "allowed",
                             "pivotNote": "피벗 (0,4) = 선의 시작점(공격자). 공격자 히트박스 중심에 두고 목표 방향으로 회전, x 방향으로 사거리/8 만큼 타일링(TileSprite) 또는 scaleX.",
                             "note": "2프레임 깜빡 120ms 루프. 바닥 깊이. 세로 8 중 3~4행만 쓰므로 두께 2px."})
    fx["telegraph_circle"] = ("telegraph_circle", telegraph_circle_frames(), ["any"], 32, 32, (16, 16), [120, 120], True,
                              {"anchor": "hitbox_center", "spawn": "telegraph", "scale": "allowed",
                               "pivotNote": "피벗 (16,16) = 범위 중심. 원 지름 30px 기준, 실제 범위 반지름 R 이면 scale = R/15.",
                               "note": "외곽선만. 2프레임 깜빡 루프. 바닥 깊이. 정수 배가 아니면 선이 고르지 않을 수 있으니 1배·2배 우선."})
    fx["telegraph_cone"] = ("telegraph_cone", telegraph_cone_frames(), DIRS, 32, 32, (16, 16), [120, 120], True,
                            {"anchor": "hitbox_center", "spawn": "telegraph", "scale": "allowed",
                             "pivotNote": "피벗 (16,16) = 부채꼴 꼭짓점(공격자). 반지름 15px, 반각 32도. 사거리 R 이면 scale = R/15.",
                             "note": "외곽선만. 방향 = 공격 방향 4종. 캔버스 절반만 쓰는 대신 꼭짓점이 피벗과 일치한다."})
    fx["enemy_bullet"] = ("enemy_bullet", enemy_bullet_frames(), ["any"], 8, 8, (5, 4), [0], False,
                          {"anchor": "projectile", "rotate": True, "drawnFacing": "right",
                           "pivotNote": "피벗 (5,4) = 구슬 중심(4x4 구슬 x4..7, y2..5). 꼬리는 뒤(왼쪽)로 3px.",
                           "note": "화승총 탄. G01 구슬 + 22 꼬리. 플레이어 위 깊이."})
    fx["boss_fan_shot"] = ("boss_fan_shot", boss_fan_shot_frames(), ["any"], 10, 10, (5, 5), [80, 80], True,
                           {"anchor": "projectile", "rotate": False,
                            "note": "부채꼴 탄. 21 코어 + G13 림, 2프레임 맥동 루프. 회전 불필요(원형)."})
    fx["muzzle_flash"] = ("muzzle_flash", muzzle_flash_frames(), DIRS, 12, 12, (6, 6), [40, 60], False,
                          {"anchor": "hitbox_center", "spawn": "enemy_shoot",
                           "pivotNote": "피벗 (6,6) = 총구. 사수 히트박스 중심에서 총구 오프셋(방향별 약 ±8px 전방, -2px 위)을 더해 놓는다.",
                           "note": "사수 발사 프레임 시작과 동시에. 사수 위 깊이. enemy_bullet 생성 시점 = 이 이펙트 시작."})

    print("%-17s %s" % ("name", "colors / isolated / semi"))
    for name, (action, fbd, dirs, w, h, pivot, durs, loop, extra) in fx.items():
        save_sheet(name, fbd, dirs, w, h, durs, loop, pivot, extra, action=action)
        color_report(name, fbd)
    preview_all(fx)
    preview_blood(fx)
    preview_1x(fx)
    print("wrote", OUT_FX, "and previews in", HERE)


if __name__ == "__main__":
    main()
