"""56라운드 Q11 붓획 — '채운 초승달 면' 대신 붓으로 그은 한 획.

획 = 중심선(화면 좌표 폴리라인)을 따라 붓털(lane) 여러 가닥을 찍는다.
  · 폭 윤곽: 시작 가늘고(붓 끝이 닿음) → 가운데 굵고(눌러 그음) → 끝은 붓털이 갈라지며(가닥 사이가 벌어지고 짧게 끊김) 흩어짐 + 먹 튐 점.
  · 붓털 결: 가닥마다 밝기가 조금씩 달라 길이 방향 결이 생긴다. 가장자리 가닥은 어둡고(재) 가운데는 밝다(호박) — 바닥 위에서 테가 읽힘.
  · 백열(X0/X1/A26)은 판정 프레임의 획 머리 몇 도트만(Lhot). 획 몸은 A25 이하 → 흰 막대 없음.
  · 소멸(k): 시작 쪽부터 마르며 물러나고, 남은 몸은 디더로 부서져 재 조각으로 떨어진다(반투명 없음).
좌표: v3 도트(pixelScale 0.5). 값(0..1)은 레이어 램프로 양자화(fxkit).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "fx_weapons_v3")))
import wkit as W  # noqa: E402
from wkit import FK  # noqa: E402

# 램프(어둠 → 밝음) — 전부 주인공 v3 팔레트 안
INK_K = [W.B1, W.A17, W.A18, W.A19, W.A21, W.A23, W.A25]          # 칼·단검: 재 테 → 호박 심
INK_G = [W.B1, W.B2, W.A17, W.A18, W.A19, W.A21, W.A23, W.A25]    # 대검: 흙·녹 테가 더 넓음
HOT = [W.A25, W.A26, W.X1, W.X0]                                   # 획 머리 백열(판정 프레임만)
FLAKE = [W.S0, W.S1, W.S2]                                         # 재 조각
FLAKE_G = [W.B1, W.B2, W.B3]


def resample(pts, step=0.4):
    out = [pts[0]]
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        n = max(1, int(L / step))
        for i in range(1, n + 1):
            out.append((a[0] + dx * i / n, a[1] + dy * i / n))
            acc.append(acc[-1] + L / n)
    return out, acc


class Stroke:
    """한 획(결정적). pts = 화면 좌표 중심선. wmax = 가장 굵은 곳 전체 폭(도트)."""

    def __init__(self, pts, wmax, seed=1, peak=0.4, dry_from=0.64, split=1.1, lanes=None, start_w=0.1, end_w=0.55,
                 drops=7, side=1):
        self.p, acc = resample(pts)
        self.L = acc[-1] or 1.0
        self.s = [a / self.L for a in acc]
        n = len(self.p)
        self.nrm = []
        for i in range(n):
            a = self.p[max(0, i - 4)]
            b = self.p[min(n - 1, i + 4)]
            tx, ty = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(tx, ty) or 1.0
            self.nrm.append((-ty / ln, tx / ln))
        self.wmax, self.seed, self.peak, self.dry, self.split = wmax, seed, peak, dry_from, split
        self.start_w, self.end_w = start_w, end_w
        nl = lanes or max(4, int(round(wmax / 0.95)))
        self.nl = nl
        self.lanes = []
        for j in range(nl):
            o = (j + 0.5) / nl - 0.5                                  # -0.5..0.5
            h = W.h2(j, 7, seed)
            edge = abs(o) * 2
            # 끝 위치: 바깥 가닥일수록 일찍 끊김, 가운데 몇 가닥은 끝까지(갈라진 붓 끝)
            end = dry_from + (1 - dry_from) * (0.25 + 0.75 * (1 - edge) * (0.55 + 0.45 * h))
            if h > 0.8:
                end = min(1.0, end + 0.1)
            if abs(o) < 0.2:
                end = 1.0                                            # 가운데 가닥은 획 머리까지(백열 머리가 떨어져 보이지 않게)
            self.lanes.append(dict(o=o, h=h, end=min(1.0, end), streak=0.66 + 0.34 * W.h2(j, 3, seed)))
        # 먹 튐(끝 너머): (끝에서 앞 거리, 옆 거리, 크기)
        import random
        r = random.Random(seed * 31 + 5)
        self.drops = [(r.uniform(2, 9 + wmax * 0.5), r.uniform(-1.2, 1.2) * wmax * 0.9 * side + r.uniform(-1, 1), r.uniform(0.5, 1.4))
                      for _ in range(drops)]
        self.side = side

    def width(self, s):
        if s < self.peak:
            u = s / self.peak
            return self.start_w + (1 - self.start_w) * (u ** 0.75)
        u = (s - self.peak) / (1 - self.peak)
        return 1 - (1 - self.end_w) * u ** 1.2

    def at(self, s):
        i = min(len(self.p) - 1, max(0, int(round(s * (len(self.p) - 1)))))
        return self.p[i], self.nrm[i]

    def tangent_end(self):
        a = self.p[max(0, len(self.p) - 8)]
        b = self.p[-1]
        tx, ty = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, ty) or 1.0
        return tx / ln, ty / ln

    # ------------------------------------------------------------------ 그리기
    def draw(self, Lb, head=1.0, tail=0.0, vmax=0.86, wk=1.0, hot=None, k=0.0, drops=True, fall=0.0, Lhot=None,
             head_glint=0, vfloor=0.32):
        """Lb = 획 몸 레이어. hot = 판정 프레임(획 머리 백열, Lhot). k = 소멸(0..1): 몸 값·폭 감소 + 디더 부서짐.
        fall = 소멸 중 먹 튐이 떨어진 거리(도트)."""
        if head - tail < 1e-3:
            return
        put = Lb.put
        drawing = head < 0.999
        hw_head = 0.04
        ero = 0.0 if k <= 0 else 0.05 + 0.62 * k ** 1.4
        for idx, s in enumerate(self.s):
            if s < tail or s > head:
                continue
            (x, y), (nx, ny) = self.p[idx], self.nrm[idx]
            w = self.wmax * self.width(s) * wk
            if drawing and head - s < hw_head:                       # 그어 나가는 머리: 둥글게 모임
                w *= 0.45 + 0.55 * ((head - s) / hw_head) ** 0.5
            if tail > 0 and s - tail < 0.05:                         # 마르며 물러나는 꼬리: 뾰족
                w *= 0.3 + 0.7 * (s - tail) / 0.05
            d = max(0.0, (s - self.dry) / (1 - self.dry))
            spread = 1 + self.split * d ** 1.3
            lw = w / self.nl
            along = 0.82 + 0.18 * min(1.0, s / max(1e-6, head)) if hot else 0.9 + 0.1 * (1 - abs(s - 0.45))
            for j, ln in enumerate(self.lanes):
                if s > ln["end"]:
                    continue
                core = abs(ln["o"]) < 0.2 and s > 0.9
                if d > 0 and not core and W.h2(j, int(s * self.L / 3.5), self.seed + 9) < 0.85 * d:
                    continue                                         # 마른 붓: 가닥이 끊김(비백)
                if 0.3 < s < self.dry and abs(ln["o"]) > 0.2:      # 가운데 뒤쪽: 가장자리 가닥부터 마르기 시작
                    q = (s - 0.3) / (self.dry - 0.3)
                    if W.h2(j, int(s * self.L / 5.0), self.seed + 4) < 0.32 * q * (abs(ln["o"]) * 2):
                        continue
                off = ln["o"] * w * spread
                th = lw * (0.78 if d <= 0 else 0.62 * (1 - 0.5 * d))
                th *= min(1.0, (ln["end"] - s) / 0.035) ** 0.6 if ln["end"] < 0.999 else 1.0
                c = 1 - 0.62 * (abs(ln["o"]) * 2) ** 1.5
                v = vmax * max(vfloor, c) * ln["streak"] * along * (1 - 0.35 * k)
                cx, cy = x + nx * off, y + ny * off
                r = max(0.35, th)
                R = r + 0.42
                for yy in range(int(math.floor(cy - R)), int(math.ceil(cy + R)) + 1):
                    for xx in range(int(math.floor(cx - R)), int(math.ceil(cx + R)) + 1):
                        if (xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2 <= R * R:
                            if ero and W.h2(xx >> 1, yy >> 1, self.seed + int(k * 10)) < ero * (0.7 + 0.6 * abs(ln["o"])):
                                continue
                            put(xx, yy, v)
        # 먹 튐(붓 끝이 획을 떠나며)
        if drops and head >= 0.97:
            ex, ey = self.p[-1]
            tx, ty = self.tangent_end()
            nx, ny = -ty, tx
            for a, b, sz in self.drops:
                px = ex + tx * a + nx * b
                py = ey + ty * a + ny * b + fall * (0.6 + 0.4 * sz)
                if k > 0 and W.h2(int(a * 10), int(b * 10), self.seed) < k * 0.8:
                    continue
                Lb.stamp(px, py, sz * (1 - 0.3 * k), vmax * 0.62 * (1 - 0.4 * k), soft=0)
        # 획 머리 백열(몇 도트)
        if hot and Lhot is not None:
            self.hot_head(Lhot, head, head_glint)

    def hot_head(self, Lh, head, glint=0):
        """획 머리에서 뒤로 ~9 도트만 백열(굵기는 머리 폭의 40% 이하, 최대 1.6 도트 반지름)."""
        (x, y), _ = self.at(min(head, 0.999))
        n = len(self.p)
        i0 = min(n - 1, int(round(min(head, 0.999) * (n - 1))))
        back = int(9 / 0.4)
        for m in range(0, back, 2):
            i = i0 - m
            if i < 0:
                break
            u = m / back
            w = self.wmax * self.width(self.s[i]) * 0.2 * (1 - u)
            Lh.stamp(self.p[i][0], self.p[i][1], min(1.6, max(0.4, w)), 1.0 - 0.75 * u, soft=0.6)
        if glint:
            Lh.star4(x, y, glint, w=0.6, v=0.75)

    def flakes(self, Lf, frame_k, s0, s1, count, size=1.6, fall=6.0, seed=0):
        """소멸 중 재 조각: 획 [s0, s1] 구간에서 떨어져 나와 아래로 떨어짐(화면 좌표)."""
        import random
        r = random.Random(self.seed * 7 + seed)
        for _ in range(count):
            s = r.uniform(s0, s1)
            (x, y), (nx, ny) = self.at(s)
            off = r.uniform(-0.6, 0.6) * self.wmax * self.width(s)
            W.flake(Lf, x + nx * off + r.uniform(-2, 2), y + ny * off + fall * frame_k * r.uniform(0.6, 1.4),
                    r.uniform(0.7, 1.0) * size * (1 - 0.3 * frame_k), r.uniform(0, 6), v=r.uniform(0.55, 1.0))


def arc_points(t, R, a0d, a1d, zfn, n=None):
    """로컬 호(반지름 R, a0 → a1 도) → 화면 좌표. zfn(s) = 높이(화면 위로)."""
    a0, a1 = math.radians(a0d), math.radians(a1d)
    n = n or max(24, int(abs(a1 - a0) * R / 1.5))
    out = []
    for i in range(n + 1):
        s = i / n
        a = a0 + (a1 - a0) * s
        x, y = t((math.cos(a) * R, math.sin(a) * R))
        out.append((x, y - zfn(s)))
    return out
