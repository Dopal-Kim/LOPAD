"""61라운드 P3 — 1층 5지역 타일셋 임시 2배 칸(upscaled60)을 64도트 설계로 다시 그리는 공용 도구.

원칙(floor1q60/fk64 와 같음): 디더 0 · 큰 덩어리(12~16) / 중간 결(4~6) / 1도트 점의 3단 세부 · 쿼터뷰 높이(윗변 밝게·아랫변 어둡게) ·
가로 이음 = 64 주기 잡음 + 모든 변형이 같은 '가장자리 줄눈'을 공유(아무 변형끼리 붙어도 이어짐).
그늘(53~57)만 반투명(알파 단계) — 나머지 벽·바닥 칸은 반투명 0.
"""
import math

from PIL import Image

import s61  # noqa: F401  (경로)
import fk64
from fk64 import h, hf, vnoise, fbm  # noqa: F401

G, A, SL, WD, PL = fk64.G, fk64.A, fk64.SL, fk64.WD, fk64.PL
N = 64
CLEAR = (0, 0, 0, 0)


def rgba(c):
    return tuple(c[:3]) + (255,)


class Tile:
    def __init__(self, w=N, h_=N, fill=None):
        self.im = Image.new("RGBA", (w, h_), rgba(fill) if fill else CLEAR)
        self.p = self.im.load()
        self.w, self.h = w, h_

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.p[x, y] = rgba(c) if len(c) >= 3 and (len(c) == 3 or c[3] == 255) else c

    def get(self, x, y):
        return self.p[x, y] if 0 <= x < self.w and 0 <= y < self.h else CLEAR

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def hline(self, x0, x1, y, c):
        self.rect(min(x0, x1), y, max(x0, x1), y, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, min(y0, y1), x, max(y0, y1), c)

    def line(self, x0, y0, x1, y1, c):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for k in range(n + 1):
            self.set(int(round(x0 + (x1 - x0) * k / n)), int(round(y0 + (y1 - y0) * k / n)), c)

    def crop(self, y0, y1=None):
        y1 = y0 + N if y1 is None else y1
        return self.im.crop((0, y0, self.w, y1))

    def shift_ramp(self, x, y, ramp, d):
        c = self.get(x, y)
        rr = [rgba(r) for r in ramp]
        if c in rr:
            self.set(x, y, rr[max(0, min(len(rr) - 1, rr.index(c) + d))])


def lv(ramp, i):
    return ramp[max(0, min(len(ramp) - 1, int(i)))]


# ---------------------------------------------------------------- 블록 벽(마름돌·벽돌)
def block_rows(t, ramp, mortar, rows, y0, seed, var, base=None, edge_cut=None, wmin=22, wmax=36, chisel=True, chip=1,
               mortar2=None, x_period=N):
    """rows = 행 높이 목록(y0 부터). 각 행: 가장자리 줄눈(edge_cut[r]) 은 모든 변형이 공유, 안쪽 줄눈은 var 로 다름.
    블록 명도·결 잡음은 64 주기(가로 이음)."""
    L = len(ramp) - 1
    base = base if base is not None else L // 2
    mortar2 = mortar2 or mortar
    y = y0
    for ri, rh in enumerate(rows):
        a = edge_cut[ri] if edge_cut else int(hf(seed, ri, 1) * 28)
        cuts = [a]
        x = a
        k = 0
        while True:
            w = wmin + int(hf(seed, var, ri, k, 2) * (wmax - wmin))
            if x + w > a + x_period - wmin:
                break
            x += w
            cuts.append(x)
            k += 1
        cuts.append(a + x_period)
        for bi in range(len(cuts) - 1):
            bx0, bx1 = cuts[bi], cuts[bi + 1]
            edge_block = bi == len(cuts) - 2           # a+64 를 넘어 다음 칸으로 감기는 블록(공유 시드)
            bseed = (seed, ri, 99) if edge_block else (seed, var, ri, bi)
            v = hf(*bseed, 3)
            b = base + (1 if v > 0.7 else (-1 if v < 0.22 else 0))
            for yy in range(y, y + rh):
                for xx in range(bx0, bx1):
                    X = xx % x_period
                    if yy == y + rh - 1 or xx == bx0:
                        t.set(X, yy, mortar if yy == y + rh - 1 else mortar2)
                        continue
                    ly, lx = yy - y, xx - bx0
                    ry_, rx_ = y + rh - 2 - yy, bx1 - 1 - xx
                    if chip and ((lx < chip and ly < chip) or (rx_ < chip and ry_ < chip)):
                        t.set(X, yy, mortar)
                        continue
                    n = vnoise(X, yy, 4, hash(bseed) & 0xFFFF, period=x_period)
                    q = b + (1 if n > 0.84 else (-1 if n < 0.14 else 0))
                    if ly == 0:
                        q += 2
                    elif ly == 1 or lx == 1:
                        q += 1
                    elif ry_ == 0:
                        q -= 2
                    elif ry_ == 1 or rx_ == 0:
                        q -= 1
                    if chisel and (X + yy * 2 + bi) % 11 == 0 and 3 < ly < rh - 4:
                        q -= 1
                    t.set(X, yy, lv(ramp, q))
        y += rh


def foot_damp(t, ramp, y0, y1, seed):
    """벽 발치 젖음·그을음: 아래로 갈수록 한 단 어둡게(잡음 경계)."""
    rr = [rgba(r) for r in ramp]
    for y in range(y0, y1):
        tt = (y - y0) / max(1, y1 - y0)
        for x in range(N):
            c = t.get(x, y)
            if c in rr and vnoise(x, y, 4, seed, period=N) < tt * 1.1:
                t.set(x, y, rr[max(0, rr.index(c) - (2 if tt > 0.65 else 1))])


def crack(t, x, y, n, seed, ramp, dark):
    r = seed
    for k in range(n):
        t.set(x, y, dark)
        nb = t.get(x + 1, y)
        if nb in [rgba(q) for q in ramp]:
            t.shift_ramp(x + 1, y, ramp, 1)
        y += 1
        x += (-1 if hf(r, k) < 0.33 else (1 if hf(r, k) > 0.66 else 0))


# ---------------------------------------------------------------- 윗면·가장자리
def edge_overlay(top_im, side, rim, rim2, drop, drop2):
    """윗면 칸에 가장자리(바닥 쪽으로 떨어지는 변) 테두리: side in e/w/n/ne/nw.
    바깥 2 도트 = 떨어지는 옆면(어둠), 그 안 2 도트 = 밝은 테."""
    t = Tile(); t.im.paste(top_im, (0, 0)); t.p = t.im.load()
    sides = {"e": ["e"], "w": ["w"], "n": ["n"], "ne": ["n", "e"], "nw": ["n", "w"]}[side]
    for s in sides:
        for k in range(N):
            for d in range(5):
                if s == "e":
                    x, y = N - 1 - d, k
                elif s == "w":
                    x, y = d, k
                else:
                    x, y = k, d
                col = drop if d == 0 else (drop2 if d == 1 else (rim if d == 2 else rim2 if d == 3 else None))
                if col is None:
                    continue
                # 모서리 겹침: 이미 떨어지는 면이면 유지
                cur = t.get(x, y)
                if cur[:3] in (drop[:3], drop2[:3]) and col not in (drop, drop2):
                    continue
                t.set(x, y, col)
    return t.im


def lip_overlay(top_im, rim, rim2, under, under2):
    """topAboveFront(47): 아래 변 = 앞면으로 꺾이는 모서리 — 밝은 테 2 + 그 아래 그늘 2(앞면 윗단과 맞닿음)."""
    t = Tile(); t.im.paste(top_im, (0, 0)); t.p = t.im.load()
    for x in range(N):
        t.set(x, N - 5, rim2); t.set(x, N - 4, rim); t.set(x, N - 3, rim)
        t.set(x, N - 2, under); t.set(x, N - 1, under2)
    return t.im


# ---------------------------------------------------------------- 그늘(53~57, 공용 · 반투명)
SHADOW_RGB = (10, 11, 16)


def shadows():
    """n = 북쪽 벽 발치 24 도트 · w/e = 16 도트 · nw/ne = 모서리. 알파 6 단계(덩어리 경계, 디더 없음)."""
    steps = [150, 118, 90, 64, 40, 20]
    out = {}

    def depth_alpha(d, span, x, y, seed):
        f = d / span + (vnoise(x, y, 4, seed, period=N) - 0.5) * 0.18
        k = int(f * len(steps))
        return 0 if k >= len(steps) or f < 0 and False else steps[max(0, k)]
    for idx, kind in ((53, "n"), (54, "w"), (55, "e"), (56, "nw"), (57, "ne")):
        im = Image.new("RGBA", (N, N), CLEAR)
        p = im.load()
        for y in range(N):
            for x in range(N):
                a = 0
                if "n" in kind:
                    a = max(a, depth_alpha(y, 24, x, y, 531))
                if kind in ("w", "nw"):
                    a = max(a, depth_alpha(x, 16, x, y, 541))
                if kind in ("e", "ne"):
                    a = max(a, depth_alpha(N - 1 - x, 16, x, y, 551))
                if a:
                    p[x, y] = SHADOW_RGB + (a,)
        out[idx] = im
    return out


# ---------------------------------------------------------------- 문·출구·상점(8~12, 5지역 공용 그림)
FRAME = [SL[0], G[2], G[3], G[4], G[5], G[6], G[7], G[8]]
DOORW = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]]


def door_frame(t):
    """돌 문틀(양옆 기둥 + 위 인방) — 아랫단 벽 자리."""
    for y in range(N):
        for x in list(range(0, 10)) + list(range(54, N)):
            right = x >= 54
            lx = x if not right else x - 54
            q = 4 + (1 if lx == 1 else 0) - (1 if lx == 9 else 0) - (1 if right else 0)
            if y % 16 == 15:
                q = 1
            elif y % 16 == 0:
                q += 1
            if (x * 3 + y * 5) % 17 == 0:
                q -= 1
            t.set(x, y, lv(FRAME, q))
        t.set(9 if True else 0, y, FRAME[1]); t.set(54, y, FRAME[5])
    for y in range(0, 8):                                                 # 인방
        for x in range(10, 54):
            t.set(x, y, lv(FRAME, 5 if y < 2 else (4 if y < 6 else 2)))
    t.hline(10, 53, 8, FRAME[0])


def door_tiles():
    out = {}
    # 8 열린 문: 어두운 통로 + 문짝이 안쪽으로 젖혀진 옆모서리
    t = Tile(fill=SL[0]); door_frame(t)
    for y in range(9, N):
        for x in range(10, 54):
            d = (y - 9) / 55
            t.set(x, y, SL[0] if d < 0.55 else (SL[1] if d < 0.85 else SL[2]))
    for y in range(9, N):                                                # 젖힌 문짝(왼쪽 안)
        for x in range(10, 17):
            t.set(x, y, lv(DOORW, 2 if x < 15 else 1))
        t.set(16, y, DOORW[3])
    for y in (20, 46):
        t.hline(10, 16, y, G[5])
    for x in range(18, 52, 3):                                            # 문턱 돌
        pass
    t.rect(10, N - 4, 53, N - 1, FRAME[4]); t.hline(10, 53, N - 4, FRAME[6]); t.hline(10, 53, N - 1, FRAME[1])
    out[8] = t.im

    def closed(locked):
        t = Tile(fill=SL[0]); door_frame(t)
        for x in range(10, 54):                                          # 세로 널 4장
            k = (x - 10) // 11
            lx = (x - 10) % 11
            for y in range(9, N - 3):
                q = 3 + (1 if lx == 0 else 0) - (1 if lx == 10 else 0) + (1 if k == 0 else 0)
                n = vnoise(x, y * 0.3, 3, 81 + k)
                if n < 0.15:
                    q -= 1
                t.set(x, y, lv(DOORW, q))
            t.set(x, 9, DOORW[1])
        for y in (18, 48):                                                # 쇠띠 + 못
            for x in range(10, 54):
                t.set(x, y, G[6]); t.set(x, y + 1, G[5]); t.set(x, y + 2, G[3])
            for x in range(13, 54, 10):
                t.set(x, y + 1, G[10])
        t.rect(10, N - 3, 53, N - 1, FRAME[3]); t.hline(10, 53, N - 3, FRAME[5])
        # 고리 손잡이
        cx, cy = 44, 34
        for a in range(24):
            th = a / 24 * 2 * math.pi
            t.set(int(round(cx + 4 * math.cos(th))), int(round(cy + 5 * math.sin(th))), G[7] if math.sin(th) < 0 else G[4])
        t.rect(43, 28, 45, 30, G[5])
        if locked:                                                        # 자물쇠(호박 열쇠 구멍 — 층 강조)
            t.rect(26, 30, 38, 42, G[4]); t.rect(27, 31, 37, 41, G[6]); t.hline(27, 37, 31, G[9])
            for a in range(14):
                th = math.pi + a / 13 * math.pi
                t.set(int(round(32 + 4 * math.cos(th))), int(round(30 + 5 * math.sin(th))), G[7])
            t.rect(31, 34, 33, 38, SL[0]); t.set(32, 35, A[23]); t.set(32, 36, A[21])
        return t.im
    out[9] = closed(False)
    out[10] = closed(True)
    # 11 출구: 문 너머 아래로 내려가는 돌계단(먼 단일수록 어둠) + 첫 단 모서리 호박 점(길잡이)
    t = Tile(fill=SL[0]); door_frame(t)
    steps = [(9, 17, 1), (17, 26, 2), (26, 36, 3), (36, 47, 4), (47, 59, 5), (59, 64, 6)]
    for (y0, y1, q) in steps:
        for y in range(y0, y1):
            ly = y - y0
            for x in range(10, 54):
                qq = q + (2 if ly == 0 else (1 if ly < 3 else (-1 if ly >= (y1 - y0) - 3 else 0)))
                if ly >= 3 and ly < (y1 - y0) - 3:
                    qq = q - 2                                          # 챌면(세로, 어두움)
                if (x * 5 + y) % 13 == 0:
                    qq -= 1
                t.set(x, y, lv(FRAME, qq))
    for x in range(14, 51, 9):
        t.set(x, 47, A[23]); t.set(x + 1, 47, A[21])
    out[11] = t.im
    # 12 상점 바닥: 나무 판 마루(가로 널, 64 주기 이음)
    t = Tile()
    for y in range(N):
        row = y // 8
        off = int(hf(12, row) * 40)
        for x in range(N):
            X = (x + off) % N
            ly = y % 8
            q = 3 + (1 if hf(12, row, 2) > 0.6 else 0) + (1 if ly == 0 else 0) - (2 if ly == 7 else 0)
            if X in (0, 1) or (row % 2 and X in (31, 32)):
                q = 1 if X == 0 or X == 31 else 4
            n = vnoise(x, y * 0.25, 4, 12 + row, period=N)
            if n < 0.18 and ly not in (0, 7):
                q -= 1
            t.set(x, y, lv(DOORW, q))
        if y % 8 == 4:
            for x in range(4, N, 16):
                t.set((x + off) % N, y, G[6])
    out[12] = t.im
    return out


# ---------------------------------------------------------------- 공허(void)
def void(ramp, seed, kind):
    """바닥 밖 어둠: base = 아주 어두운 지역색 덩어리 / 'b' = 희미한 형체 / 'c' = 거의 검정."""
    t = Tile()
    for y in range(N):
        for x in range(N):
            n = fbm(x, y, seed, period=N, scales=(16, 8))
            if kind == "c":
                q = 0
            else:
                q = 1 if n > 0.62 else 0
            t.set(x, y, ramp[q])
    return t
