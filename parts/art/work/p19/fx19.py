"""P19 1-A 반응 fx + 예고 색 언어 바닥 그림 (fx/v3, pixelScale 0.5, 트림 아틀라스, paletteSwap none, drawOver lightmap).

반응(계약 free-combat §1 이벤트에 붙임): react_wallslam_crack·_dust(ENEMY_WALL_SLAM) · react_bowl(ENEMY_BOWLED) · react_launch_dust·react_land_dust
(ENEMY_LAUNCHED/LANDED) · react_fall_splash(_liquor)·react_fall_chasm(ENEMY_FELL water/drop) · react_explode_s/m/l(HAZARD_EXPLODED chain)
· react_flinch_flash(ENEMY_STAGGERED). 예고(계약 §2 4색 — 계약 색 그대로, lopad 팔레트 밖 예외): tele_warn_fan·tele_warn_line ·
tele_danger_circle·tele_danger_fan · tele_ranged_path·tele_ranged_target · tele_chance_glint. 그리고 drum_aura(깃발 고수 오라).
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "bundle2"))
sys.path.insert(0, os.path.join(WORK, "atlas57"))
sys.path.insert(0, HERE)
import b2  # noqa: E402
from tk import G, A, SL, WD, PL, hx, bayer  # noqa: E402

SRC = "parts/art/work/p19/fx19.py (P19 1-A 반응 fx·예고 색)"
WHITE = G[15]
FLAME = [A[20], A[22], A[23], A[24], A[25], A[26], A[27], WHITE]   # 23~27·흰 = 발광
SMOKE = [SL[1], SL[2], SL[3], SL[4], SL[5], G[7]]
DUST = [WD[1], WD[2], PL[0], PL[1], PL[2], PL[3], PL[4]]
WATER = [SL[2], SL[4], SL[5], SL[6], SL[7], G[12], G[14]]
LIQ = [A[17], A[18], A[19], A[20], A[21], A[22], A[24]]
WARN, DANGER, RANGED, CHANCE = hx("#ffb347"), hx("#ff4a3a"), hx("#9fd8ff"), hx("#ffe08a")


def dk(c, k):
    return tuple(int(v * k) for v in c)


def lt(c, k):
    return tuple(int(v + (255 - v) * k) for v in c)


class F:
    def __init__(self, w, h):
        self.a = np.zeros((h, w, 4), np.uint8)
        self.h, self.w = h, w
        self.yy, self.xx = np.mgrid[0:h, 0:w].astype(np.float32)

    def put(self, m, c):
        self.a[m, :3] = c[:3]
        self.a[m, 3] = 255

    def disc(self, cx, cy, r, c, ry=None, only_empty=False):
        ry = ry or r
        m = ((self.xx - cx) / max(0.5, r)) ** 2 + ((self.yy - cy) / max(0.5, ry)) ** 2 <= 1
        if only_empty:
            m &= self.a[..., 3] == 0
        self.put(m, c)
        return m

    def ring(self, cx, cy, r, w, c, ry_k=1.0, dither=1.0):
        d = np.sqrt((self.xx - cx) ** 2 + ((self.yy - cy) / ry_k) ** 2)
        m = (np.abs(d - r) <= w / 2) & (bayer(self.h, self.w) < dither)
        self.put(m, c)

    def line(self, x0, y0, x1, y1, c, w=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for dx in range(-(w // 2), w - w // 2):
                for dy in range(-(w // 2), w - w // 2):
                    xi, yi = int(x) + dx, int(y) + dy
                    if 0 <= xi < self.w and 0 <= yi < self.h:
                        self.a[yi, xi] = (*c[:3], 255)

    def im(self):
        return Image.fromarray(self.a, "RGBA")


def rng(s):
    return np.random.default_rng(s)


# ================================================================ 반응 fx
def wallslam_crack(i):
    """벽·엄폐에 남는 금(0~2 자라고 3~5 그대로 — 마지막 프레임 hold 권장). 피벗 = 부딪친 점."""
    f = F(128, 128)
    r = rng(7)
    grow = min(1.0, (i + 1) / 3)
    for k in range(7):
        a = k / 7 * 6.283 + r.uniform(-0.3, 0.3)
        L_ = r.uniform(26, 50) * grow
        x, y = 64.0, 64.0
        for t in range(int(L_)):
            a += r.normal(0, 0.18)
            x += math.cos(a); y += math.sin(a) * 0.8
            f.put((np.abs(f.xx - x) < 0.8) & (np.abs(f.yy - y) < 0.8), G[1])
            if t % 3 == 0:
                f.put((np.abs(f.xx - x) < 0.6) & (np.abs(f.yy - (y + 1)) < 0.6), G[9])
            if t == int(L_ * 0.5) and r.random() < 0.6:
                b, bx, by = a + 0.8, x, y
                for _ in range(int(L_ * 0.3)):
                    bx += math.cos(b); by += math.sin(b) * 0.8
                    f.put((np.abs(f.xx - bx) < 0.6) & (np.abs(f.yy - by) < 0.6), G[2])
    f.disc(64, 64, 6 * grow, G[1])
    f.disc(63, 63, 3 * grow, G[3])
    if i <= 1:
        f.disc(64, 64, 12 - i * 4, WHITE, only_empty=False) if i == 0 else None
    return f.im()


def wallslam_dust(i, n=7):
    """벽꽝 먼지(옆으로 터지는 흙먼지 + 돌 부스러기). 피벗 = 부딪친 점(바닥 높이)."""
    f = F(192, 128)
    r = rng(3)
    t = i / (n - 1)
    for k in range(14):
        a = r.uniform(-math.pi, 0)
        sp = r.uniform(30, 80)
        x = 96 + math.cos(a) * sp * (0.3 + t)
        y = 96 + math.sin(a) * sp * 0.6 * (0.3 + t) + 10 * t * t
        rad = r.uniform(6, 14) * (0.6 + 0.8 * t) * (1 - 0.5 * t)
        if rad < 1:
            continue
        col = DUST[min(6, int(5 - 4 * t + r.integers(0, 2)))]
        f.disc(x, y, rad, col, ry=rad * 0.8)
        f.disc(x - rad * 0.3, y - rad * 0.3, rad * 0.5, lt(col, 0.15) if t < 0.5 else col)
    for k in range(10):
        a = r.uniform(-math.pi * 0.9, -0.1)
        sp = r.uniform(40, 90)
        x = 96 + math.cos(a) * sp * t * 1.2
        y = 96 + math.sin(a) * sp * t + 120 * t * t
        if y < 126:
            f.disc(x, y, 1.6, SL[3 + k % 3])
    if t > 0.6:
        m = f.a[..., 3] > 0
        f.a[m & (bayer(128, 192) < (t - 0.6) * 2.2), 3] = 0
    return f.im()


def bowl(i):
    """적끼리 부딪침: 흰 심 별 + 호박 충격 고리 + 짧은 줄 4."""
    f = F(128, 128)
    t = i / 5
    if i < 4:
        f.ring(64, 64, 10 + 40 * t, 4 - 2 * t, A[23] if i < 2 else PL[3], ry_k=0.75, dither=1.0 - 0.3 * t)
    for k in range(6):
        a = k / 6 * 6.283 + 0.3
        r0, r1 = 6 + 30 * t, 18 + 40 * t
        if i < 5:
            f.line(64 + math.cos(a) * r0, 64 + math.sin(a) * r0 * 0.75, 64 + math.cos(a) * r1, 64 + math.sin(a) * r1 * 0.75,
                   WHITE if i < 2 else A[24], 2 if i < 2 else 1)
    if i < 3:
        s = 14 - i * 4
        pts = [(64 + math.cos(k / 8 * 6.283) * (s if k % 2 == 0 else s * 0.4), 64 + math.sin(k / 8 * 6.283) * (s if k % 2 == 0 else s * 0.4))
               for k in range(8)]
        from PIL import ImageDraw
        im = Image.new("L", (128, 128), 0)
        ImageDraw.Draw(im).polygon(pts, fill=255)
        f.put(np.asarray(im) > 0, WHITE)
        f.disc(64, 64, s * 0.35, A[26])
    return f.im()


def launch_dust(i):
    f = F(160, 96)
    r = rng(5)
    t = i / 5
    for k in range(12):
        a = k / 12 * 6.283
        rr = 20 + 50 * t
        x, y = 80 + math.cos(a) * rr, 80 + math.sin(a) * rr * 0.35
        rad = (8 - 6 * t) * r.uniform(0.7, 1.2)
        if rad > 0.8:
            f.disc(x, y, rad, DUST[5 - int(3 * t)], ry=rad * 0.7)
    for k in range(5):
        x = 80 + r.uniform(-16, 16)
        y0 = 80 - 60 * t
        f.line(x, y0, x, y0 + 14 * (1 - t), PL[4] if i < 3 else PL[2], 1)
    return f.im()


def land_dust(i):
    f = F(192, 96)
    r = rng(9)
    t = i / 5
    for k in range(16):
        side = -1 if k % 2 else 1
        rr = (10 + 70 * t ** 0.7) * r.uniform(0.6, 1.0)
        x, y = 96 + side * rr, 82 - r.uniform(0, 14) * t
        rad = (10 - 8 * t) * r.uniform(0.7, 1.2)
        if rad > 0.8:
            f.disc(x, y, rad, DUST[5 - int(4 * t)], ry=rad * 0.6)
    for k in range(8):
        x = 96 + r.uniform(-60, 60) * t
        y = 84 - 30 * math.sin(math.pi * t) * r.uniform(0.3, 1)
        f.disc(x, y, 1.4, SL[4])
    f.ring(96, 86, 30 + 60 * t, 2, PL[2], ry_k=0.25, dither=0.8 - 0.6 * t)
    return f.im()


def fall_splash(i, ramp):
    """낙하 물보라: 0~3 물기둥 솟음 → 4~8 떨어지는 물방울 + 퍼지는 물결 고리. 피벗 = 수면 닿은 점(아래 중앙)."""
    f = F(128, 192)
    r = rng(11)
    t = i / 8
    base_y = 168
    hgt = 120 * math.sin(min(1.0, t * 2.2) * math.pi / 2) * (1 - max(0.0, t - 0.45) * 1.8)
    if hgt > 4:
        for k in range(7):
            x = 64 + (k - 3) * 6 + r.uniform(-2, 2)
            h = hgt * (1 - abs(k - 3) * 0.2) * r.uniform(0.8, 1.05)
            w0 = 6 - abs(k - 3) * 0.6
            lean = (k - 3) * 0.12
            tt = np.clip((base_y - f.yy) / max(1.0, h), 0, 1)
            w = w0 * (1 - tt * 0.75)
            m = (np.abs(f.xx - (x + lean * (base_y - f.yy))) <= w) & (f.yy >= base_y - h) & (f.yy <= base_y)
            f.put(m, ramp[3])
            f.put(m & (f.xx < x + lean * (base_y - f.yy) - w * 0.3), ramp[5])
            f.disc(x + lean * h, base_y - h, w0 * 0.45 + 1, ramp[6] if k % 2 else ramp[5])
    for k in range(18):
        a = r.uniform(-math.pi * 0.95, -math.pi * 0.05)
        sp = r.uniform(40, 110)
        x = 64 + math.cos(a) * sp * t * 0.8
        y = base_y + math.sin(a) * sp * t * 1.6 + 260 * t * t
        if y < base_y + 2:
            f.disc(x, y, 2.2 - t, ramp[5 + k % 2])
    for k in range(2):
        rr = 10 + 50 * t + k * 14
        f.ring(64, base_y + 4, rr, 2, ramp[4] if k == 0 else ramp[3], ry_k=0.3, dither=1.0 - 0.8 * t)
    return f.im()


def fall_chasm(i):
    """낭떠러지로 떨어짐: 가장자리 흙먼지 + 아래로 빨려 드는 줄 + 돌 부스러기. 피벗 = 떨어진 가장자리 점."""
    f = F(128, 160)
    r = rng(13)
    t = i / 7
    for k in range(10):
        x = 64 + r.uniform(-36, 36) * (0.4 + t)
        y = 40 - r.uniform(0, 14) * (1 - t)
        rad = 9 * (1 - t) * r.uniform(0.6, 1.1)
        if rad > 0.8:
            f.disc(x, y, rad, DUST[4 - int(3 * t)], ry=rad * 0.7)
    for k in range(9):
        x = 64 + r.uniform(-24, 24)
        y = 44 + 140 * t * t * r.uniform(0.6, 1.0)
        if y < 158:
            f.disc(x, y, 2.0, SL[3 + k % 3])
    for k in range(4):
        x = 52 + k * 8
        f.line(x, 50 + 60 * t, x, 50 + 60 * t + 30 * (1 - t), SL[5] if t < 0.5 else SL[3], 1)
    return f.im()


def explode(i, S):
    """연쇄 폭발: 0 흰 번쩍 · 1~3 불덩이(발광) · 4~6 불 → 연기 고리 · 7~8 연기·불티 흩어짐. 바닥 그을음은 hazard 잔해/데칼이 맡음."""
    f = F(S, S)
    c = S / 2
    R = S * 0.42
    r = rng(17 + S)
    if i == 0:
        f.disc(c, c, R * 0.35, WHITE)
        f.disc(c, c, R * 0.55, A[27], only_empty=True)
        for k in range(8):
            a = k / 8 * 6.283
            f.line(c, c, c + math.cos(a) * R * 0.8, c + math.sin(a) * R * 0.8 * 0.8, WHITE, 2)
        return f.im()
    t = (i - 1) / 7
    # 연기(바깥, 커짐)
    if i >= 3:
        for k in range(12):
            a = k / 12 * 6.283 + r.uniform(-0.2, 0.2)
            rr = R * (0.45 + 0.5 * t)
            x, y = c + math.cos(a) * rr, c + math.sin(a) * rr * 0.8 - R * 0.25 * t
            rad = R * (0.22 + 0.1 * r.random()) * (1.1 - 0.4 * t)
            col = SMOKE[min(5, 1 + int(4 * (1 - t)))]
            f.disc(x, y, rad, col, ry=rad * 0.85)
            f.disc(x - rad * 0.3, y - rad * 0.3, rad * 0.5, lt(col, 0.12))
    # 불덩이(가운데, 발광 → 줄어듦)
    fr = R * (0.75 - 0.55 * t) if i >= 1 else 0
    if fr > 2:
        for k in range(9):
            a = k / 9 * 6.283 + i
            x, y = c + math.cos(a) * fr * 0.45, c + math.sin(a) * fr * 0.4 - fr * 0.1
            f.disc(x, y, fr * 0.55, FLAME[2 if t > 0.4 else 3])
        f.disc(c, c - fr * 0.1, fr * 0.6, FLAME[4] if t < 0.5 else FLAME[3])
        f.disc(c - fr * 0.1, c - fr * 0.2, fr * 0.35, FLAME[6] if t < 0.3 else FLAME[5])
        if i <= 2:
            f.disc(c - fr * 0.1, c - fr * 0.2, fr * 0.18, WHITE)
    # 불티·파편
    for k in range(16):
        a = r.uniform(0, 6.283)
        sp = r.uniform(0.5, 1.0) * R * 1.1
        x, y = c + math.cos(a) * sp * min(1.0, t * 1.6), c + math.sin(a) * sp * min(1.0, t * 1.6) * 0.8 + R * 0.4 * t * t
        if 0 < x < S and 0 < y < S and i < 8:
            f.disc(x, y, 1.6 if k % 3 else 2.4, A[24] if k % 2 else (WD[2] if k % 3 == 0 else A[25]))
    if i >= 7:
        m = f.a[..., 3] > 0
        f.a[m & (bayer(S, S) < (i - 6) * 0.35), 3] = 0
    return f.im()


def flinch(i):
    f = F(64, 64)
    s = [16, 11, 6][i]
    for k in range(4):
        a = k / 4 * 6.283 + 0.78
        f.line(32 - math.cos(a) * s, 32 - math.sin(a) * s, 32 + math.cos(a) * s, 32 + math.sin(a) * s, WHITE if i < 2 else CHANCE, 1)
    f.line(32 - s * 1.3, 32, 32 + s * 1.3, 32, WHITE, 2 if i == 0 else 1)
    f.line(32, 32 - s * 1.3, 32, 32 + s * 1.3, WHITE, 2 if i == 0 else 1)
    f.disc(32, 32, 4 - i, A[26])
    return f.im()


# ================================================================ 예고 색 언어
def tele_fan(col, prog, S=192, deg=90, pulse=False):
    """부채꼴 예고(오른쪽 = 0°, drawnFacing right). prog 0..1 = 안쪽 채움이 바깥으로 자람. 피벗 = 원점(왼쪽 가운데가 아니라 시트 가운데)."""
    f = F(S, S)
    c = S / 2
    R = S / 2 - 3
    ang = np.degrees(np.arctan2(f.yy - c, f.xx - c))
    d = np.sqrt((f.xx - c) ** 2 + (f.yy - c) ** 2)
    inside = (np.abs(ang) <= deg / 2) & (d <= R)
    edge = inside & ((d > R - 2.5) | (np.abs(np.abs(ang) - deg / 2) * np.pi / 180 * d < 2.0))
    fill = inside & (d <= R * prog) & (bayer(S, S) < 0.5)
    front = inside & (np.abs(d - R * prog) < 1.5) & (prog < 1)
    f.put(fill, dk(col, 0.75))
    f.put(front, lt(col, 0.3))
    f.put(edge, col)
    if pulse:
        ring = (np.abs(ang) <= deg / 2 + 4) & (np.abs(d - R - 1) < 1)
        f.put(ring, lt(col, 0.5))
    return f.im()


def tele_circle(col, prog, S=192, pulse=0):
    f = F(S, S)
    c = S / 2
    R = S / 2 - 6
    d = np.sqrt((f.xx - c) ** 2 + (f.yy - c) ** 2)
    f.put((d <= R) & (bayer(S, S) < 0.5) & (d <= R * prog), dk(col, 0.75))
    f.put((d <= R) & (bayer(S, S) < 0.12), dk(col, 0.6))
    f.put((np.abs(d - R * prog) < 1.5) & (prog < 1), lt(col, 0.3))
    f.put(np.abs(d - R) < 1.5, col)
    if pulse:
        f.put(np.abs(d - R - 2 - pulse * 1.5) < 0.9, lt(col, 0.4))
    return f.im()


def tele_line(col):
    """반복 선(가로 64 주기, 세로 32) — 돌진 경로. 시스템이 회전·늘림."""
    f = F(64, 32)
    f.put((np.abs(f.yy - 16) <= 9) & (bayer(32, 64) < 0.4), dk(col, 0.75))
    f.put((np.abs(f.yy - 16) >= 9) & (np.abs(f.yy - 16) <= 10.5), col)
    for x0 in (8, 40):          # 진행 방향 갈매기(>)
        f.put((np.abs(f.yy - 16) <= 6) & (np.abs((f.xx - x0) - (6 - np.abs(f.yy - 16))) < 1.3), lt(col, 0.3))
    return f.im()


def tele_path(col):
    f = F(64, 16)
    for x0 in (4, 20, 36, 52):
        f.put((np.abs(f.xx - x0 - 4) <= 4) & (np.abs(f.yy - 8) <= 1.5), col)
        f.put((np.abs(f.xx - x0 - 4) <= 4) & (np.abs(f.yy - 8) <= 0.5), lt(col, 0.4))
    return f.im()


def tele_target(col, i):
    f = F(128, 128)
    c = 64
    d = np.sqrt((f.xx - c) ** 2 + ((f.yy - c) / 0.6) ** 2)
    R = 56 - [0, 3, 6, 3][i]
    f.put(np.abs(d - R) < 1.6, col)
    f.put((d < R) & (bayer(128, 128) < 0.18), dk(col, 0.7))
    f.put((np.abs(f.xx - c) < 1) & (np.abs(f.yy - c) < 10), lt(col, 0.3))
    f.put((np.abs(f.yy - c) < 1) & (np.abs(f.xx - c) < 16), lt(col, 0.3))
    return f.im()


def chance_glint(i):
    f = F(96, 64)
    r = rng(21)
    pts = [(r.uniform(14, 82), r.uniform(30, 58)) for _ in range(5)]
    for k, (x, y) in enumerate(pts):
        ph = (i - k) % 6
        s = [0, 3, 6, 4, 2, 0][ph]
        if s:
            f.line(x - s, y, x + s, y, CHANCE if s > 2 else lt(CHANCE, 0.4), 1)
            f.line(x, y - s, x, y + s, CHANCE if s > 2 else lt(CHANCE, 0.4), 1)
            f.disc(x, y, 1, WHITE)
    f.put((np.abs(np.sqrt((f.xx - 48) ** 2 + ((f.yy - 50) / 0.3) ** 2) - (30 + i * 2)) < 1) & (bayer(64, 96) < 0.6 - i * 0.08), CHANCE)
    return f.im()


def drum_aura(i):
    """깃발 고수 오라(반경 = 시트 128 도트 = 2칸 기준, 시스템이 반경에 맞춰 scale). 박자(beat) 때 0~2 맥박, 3~5 가라앉음."""
    f = F(288, 176)
    cx, cy = 144, 88
    d = np.sqrt((f.xx - cx) ** 2 + ((f.yy - cy) / 0.55) ** 2)
    R = 128
    puls = [8, 5, 2, 0, 0, 0][i]
    f.put(np.abs(d - R) < 1.5, A[20])
    f.put((np.abs(d - R + 3) < 0.8) & (bayer(176, 288) < 0.5), A[18])
    if puls:
        f.put(np.abs(d - (R - 30 + puls * 3)) < 1.2, A[23] if i == 0 else A[22])
    ang = np.arctan2((f.yy - cy) / 0.55, f.xx - cx)
    for k in range(8):                               # 북 박자 눈금(돌아감)
        a0 = k / 8 * 2 * np.pi + i * 0.13
        da = np.abs(((ang - a0 + np.pi) % (2 * np.pi)) - np.pi)
        f.put((da < 0.05) & (np.abs(d - R) < 5), A[22])
    return f.im()


# ================================================================ 시트
def build(dry=False):
    b2.DRY = dry
    prev = []
    base = {"paletteSwap": "none", "drawOver": "lightmap", "pixelScale": 0.5, "source": SRC, "version": "v3-p19"}

    def sheet(name, frames, meta, ms, loop=False):
        fw, fh = frames[0].size
        m = dict(base, **meta)
        b2.write_sheet("fx", name, frames, fw, fh, m, durations=ms, loop=loop)
        prev.extend([(f, (m["pivot"]["x"], m["pivot"]["y"])) for f in frames])

    sheet("react_wallslam_crack", [wallslam_crack(i) for i in range(6)], {
        "pivot": {"x": 64, "y": 64}, "anchor": "impact_point", "event": "ENEMY_WALL_SLAM", "depth": "above_wall_below_actors",
        "holdLastFrameMs": 1600, "fadeOutMs": 400, "note": "부딪친 벽·엄폐·구조물 면(적 피벗 높이 −24 도트)에 금. 마지막 프레임 1.6초 유지 후 사라짐. surface:'prop' 은 그 구조물 hit 상태와 같이"}, [40, 40, 50, 90, 90, 120])
    sheet("react_wallslam_dust", [wallslam_dust(i) for i in range(7)], {
        "pivot": {"x": 96, "y": 96}, "anchor": "impact_point_ground", "event": "ENEMY_WALL_SLAM", "flipByDir": True,
        "note": "벽에서 튀어나오는 먼지(위쪽 반원). 벽 방향으로 회전하지 말고 벽이 동·서면 flipX, 북쪽 벽은 그대로", "shake": {"px": 3, "ms": 120}}, [40, 50, 60, 70, 80, 90, 110])
    sheet("react_bowl", [bowl(i) for i in range(6)], {
        "pivot": {"x": 64, "y": 64}, "anchor": "contact_midpoint", "event": "ENEMY_BOWLED",
        "note": "두 적 사이 접점(가슴 높이)", "flash": {"color": "#ffffff", "alpha": 0.5, "ms": 50, "atFrame": 0}}, [40, 40, 50, 60, 70, 80])
    sheet("react_launch_dust", [launch_dust(i) for i in range(6)], {
        "pivot": {"x": 80, "y": 80}, "anchor": "enemy_feet", "event": "ENEMY_LAUNCHED", "depth": "floor"}, [40, 50, 60, 70, 80, 90])
    sheet("react_land_dust", [land_dust(i) for i in range(6)], {
        "pivot": {"x": 96, "y": 82}, "anchor": "enemy_feet", "event": "ENEMY_LANDED", "depth": "floor",
        "note": "slam:true 면 scale 1.3 + shake 2px 제안"}, [40, 50, 60, 70, 90, 110])
    sheet("react_fall_splash", [fall_splash(i, WATER) for i in range(9)], {
        "pivot": {"x": 64, "y": 168}, "anchor": "fall_point", "event": "ENEMY_FELL zone:'water'",
        "note": "수로 칸 안 떨어진 점. 적 스프라이트는 프레임 1까지 아래로 가라앉히며 지움(시스템)"}, [40, 50, 60, 70, 70, 80, 80, 90, 110])
    sheet("react_fall_splash_liquor", [fall_splash(i, LIQ) for i in range(9)], {
        "pivot": {"x": 64, "y": 168}, "anchor": "fall_point", "event": "ENEMY_FELL zone:'water' (양조·연회장 술 수로)",
        "note": "양조 구역·연회장 v4 낙하 칸(술)용 — 타일셋 v4.drop.kind 'water' 이고 지역이 brewery·hall 이면 이 시트"}, [40, 50, 60, 70, 70, 80, 80, 90, 110])
    sheet("react_fall_chasm", [fall_chasm(i) for i in range(8)], {
        "pivot": {"x": 64, "y": 44}, "anchor": "fall_edge_point", "event": "ENEMY_FELL zone:'drop'",
        "note": "낭떠러지(성벽·골짜기) — 적은 프레임 0~2 동안 아래로 미끄러지며 작아지고(scale 1→0.6) 어두워져 사라짐(시스템)"}, [40, 50, 60, 70, 80, 90, 100, 120])
    for name, S, light_r in (("react_explode_s", 128, 220), ("react_explode_m", 192, 320), ("react_explode_l", 288, 460)):
        sheet(name, [explode(i, S) for i in range(9)], {
            "pivot": {"x": S // 2, "y": S // 2}, "anchor": "hazard_center", "event": "HAZARD_EXPLODED",
            "lightByFrame": [{"color": "#fff4dc", "radius": light_r, "intensity": 1.3}] + [{"color": "#eebb6d", "radius": int(light_r * (1 - k / 9)), "intensity": 1.0 - k * 0.11} for k in range(1, 9)],
            "shake": {"px": {"react_explode_s": 2, "react_explode_m": 4, "react_explode_l": 6}[name], "ms": 160},
            "radiusTiles": {"react_explode_s": 1.2, "react_explode_m": 2.0, "react_explode_l": 3.0}[name],
            "note": "chain 0 = 첫 폭발, 1+ = 연쇄(0.3초 간격) — 작(술병·자폭병 작은 독)·중(술통 줄·증류기·자폭병)·대(술통 더미). 그을음은 위험물 wreck 상태/데칼"},
            [40, 50, 60, 60, 70, 80, 90, 100, 120])
    sheet("react_flinch_flash", [flinch(i) for i in range(3)], {
        "pivot": {"x": 32, "y": 32}, "anchor": "enemy_chest", "event": "ENEMY_STAGGERED",
        "note": "kind 'flinch' = 이것만, 'stagger'(버팀 깨짐) = 이것 + tele_chance_glint"}, [40, 40, 60])
    # 예고 색 언어
    tb = {"telegraph": True, "progressDriven": True, "depth": "floor", "colorRule": "계약 free-combat §2 색 그대로(lopad 팔레트 밖 — 계약 예외)"}
    sheet("tele_warn_fan", [tele_fan(WARN, p) for p in (0.15, 0.32, 0.5, 0.68, 0.85, 1.0)], dict(tb, **{
        "pivot": {"x": 96, "y": 96}, "anchor": "enemy_feet", "rotate": True, "drawnFacing": "right", "level": "warn", "color": "#ffb347",
        "radiusPx": 93, "arcDeg": 90, "note": "근접 휘두름(징집병 350ms 등) — frame = floor(진행도×5). 반경·각은 scale·여러 장 겹침으로 맞춤"}), [60] * 6)
    sheet("tele_danger_fan", [tele_fan(DANGER, p, pulse=(k % 2 == 1)) for k, p in enumerate((0.15, 0.32, 0.5, 0.68, 0.85, 1.0))], dict(tb, **{
        "pivot": {"x": 96, "y": 96}, "anchor": "enemy_feet", "rotate": True, "drawnFacing": "right", "level": "danger", "color": "#ff4a3a",
        "radiusPx": 93, "arcDeg": 90, "note": "막을 수 없는 부채꼴(≥500ms) — 홀수 프레임 바깥 테 맥박"}), [90] * 6)
    sheet("tele_danger_circle", [tele_circle(DANGER, p, pulse=k % 3) for k, p in enumerate((0.15, 0.32, 0.5, 0.68, 0.85, 1.0))], dict(tb, **{
        "pivot": {"x": 96, "y": 96}, "anchor": "hazard_or_enemy_center", "level": "danger", "color": "#ff4a3a", "radiusPx": 90,
        "scale": "allowed (반경 R 도트면 R/90)", "note": "폭발·광역(자폭병 1초·술통 lit·증류기 warn) — 진행도 구동 + 테 맥박"}), [90] * 6)
    sheet("tele_warn_line", [tele_line(WARN)], dict(tb, **{
        "pivot": {"x": 0, "y": 16}, "anchor": "path_start", "tile": True, "tilePeriodPx": 64, "rotate": True, "drawnFacing": "right",
        "level": "warn", "color": "#ffb347", "progressDriven": False, "note": "돌진 경로(결사병) — TileSprite 로 길이만큼 이어 그림, 진행도는 시스템이 길이로"}), [100])
    sheet("tele_ranged_path", [tele_path(RANGED)], dict(tb, **{
        "pivot": {"x": 0, "y": 8}, "anchor": "path_start", "tile": True, "tilePeriodPx": 64, "rotate": True, "drawnFacing": "right",
        "level": "ranged", "color": "#9fd8ff", "progressDriven": False, "note": "조준·투척 점선 궤적(사수 500ms·행상)"}), [100])
    sheet("tele_ranged_target", [tele_target(RANGED, i) for i in range(4)], dict(tb, **{
        "pivot": {"x": 64, "y": 64}, "anchor": "impact_point", "level": "ranged", "color": "#9fd8ff", "progressDriven": False,
        "radiusPx": 56, "scale": "allowed", "note": "착탄 원(술병 착지점) — 루프 4"}), [100] * 4, loop=True)
    sheet("tele_chance_glint", [chance_glint(i) for i in range(6)], dict(tb, **{
        "pivot": {"x": 48, "y": 50}, "anchor": "enemy_feet", "level": "chance", "color": "#ffe08a", "progressDriven": False,
        "note": "버팀이 깨짐·띄워짐(추가타 기회) — 적 발밑 짧은 반짝(1회 360ms 또는 기회 동안 루프)"}), [60] * 6, loop=True)
    sheet("drum_aura", [drum_aura(i) for i in range(6)], {
        "pivot": {"x": 144, "y": 88}, "anchor": "enemy_feet", "depth": "floor", "radiusPx": 128, "scale": "allowed (오라 반경 R 도트면 R/128)",
        "event": "깃발 고수 오라(살아 있는 동안 루프, beatFrames 에 0 프레임부터 다시)",
        "note": "북 박자 맥박(0~2) + 돌아가는 눈금. 오라 안 적에게는 시스템이 작은 표지(선택)"}, [70, 70, 80, 120, 120, 120], loop=True)
    b2.preview(os.path.join(HERE, "preview_fx19.png"), prev, k=2, max_w=2200)
    return b2.WRITTEN


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    build(dry)
    if not dry:
        for cat, name, src, pages in b2.to_atlas():
            print(f"{cat}/v3/{name}: {src} -> {pages}")
