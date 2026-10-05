"""61라운드 튜토리얼 허수아비 v3 (64도트 칸) — 맞으면 반응하는 'hit' 프레임(점검 15_greatsword_grid: '허수아비가 반응하지 않음').

구 `structures/battlefield_dummy`(16×32, 49라운드)를 2배 밀도 쿼터뷰 도트로 다시 그리고, 맞음 반응을 늘렸다:
idle(살짝 흔들림 루프) · hit(번쩍 → 밀려 기울었다 되돌아오는 흔들림 + 짚 부스러기) · hit_heavy(더 크게) · broken(기둥이 부러져 상체가 떨어짐).
기울기는 회전 대신 '발 기준 전단'(x += lean × 높이)으로 그려 픽셀이 깨지지 않게 했다. 맞은 쪽 반대로 기울이려면 flipX(피벗 x 대칭).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wk61 import Cv, Rand  # noqa: E402
from k61 import G, A, SL, WD, PL  # noqa: E402
from pk import Canvas, contact, qcol, BAYER  # noqa: E402

SRC = "parts/art/work/weapons61/build.py dummy (61라운드 튜토리얼 허수아비 hit)"
W, H = 272, 208
PIV = (136, 166)
LIGHT = (-0.5, -0.6, 0.62)
R_STRAW = [WD[2], PL[1], PL[2], A[22], PL[4], A[24]]
R_SACK = [WD[1], WD[2], WD[3], WD[4], PL[2], PL[3]]
R_POST = [WD[0], WD[1], WD[2], WD[3], WD[4]]
R_ROPE = [WD[1], WD[3], WD[4], PL[2]]


def _n(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


LN = _n(LIGHT)


class Dummy:
    def __init__(self, lean=0.0, squash=0.0, flash=False, top_fall=None):
        self.cv = Canvas(W, H)
        self.lean, self.squash, self.flash = lean, squash, flash
        self.top_fall = top_fall          # (dx, dy, extra_lean) 부러진 상체

    def X(self, x, y):
        """국소 좌표(곧게 선 허수아비, 피벗 (80,166)) → 시트 좌표. 위로 갈수록 lean 만큼 옆으로(전단), squash 만큼 눌림."""
        hgt = PIV[1] - y
        yy = PIV[1] - hgt * (1.0 - self.squash)
        lean = self.lean
        dx = 0
        if self.top_fall and y < 112:
            fx, fy, fl = self.top_fall
            lean += fl
            dx, yy = fx, yy + fy
        return x + lean * hgt + dx, yy

    def px(self, x, y, c):
        X, Y = self.X(x, y)
        self.cv.px(int(round(X)), int(round(Y)), c)

    def ellipse(self, cx, cy, rx, ry, ramp, base=0.5, gain=0.55, tex=None):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                u, v = (x - cx) / rx, (y - cy) / ry
                d = u * u + v * v
                if d > 1:
                    continue
                nz = math.sqrt(max(0.0, 1 - d))
                s = base + gain * (u * LN[0] + v * LN[1] + nz * LN[2]) - 0.25
                if tex:
                    s += tex(x, y)
                col = qcol(ramp, s, x, y)
                if d > 0.86 and (u * LN[0] + v * LN[1]) > 0:
                    col = ramp[0]
                self.px(x, y, col)

    def rect(self, x0, y0, x1, y1, ramp, vertical=True):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if vertical:
                    t = (x - x0) / max(1, x1 - x0)
                    s = 0.85 - 0.75 * t
                else:
                    t = (y - y0) / max(1, y1 - y0)
                    s = 0.85 - 0.7 * t
                s += 0.06 * math.sin(x * 1.7 + y * 0.31) * (1 if vertical else 0) + 0.06 * math.sin(y * 1.3 + x * 0.2) * (0 if vertical else 1)
                self.px(x, y, qcol(ramp, s, x, y))

    def line(self, x0, y0, x1, y1, c):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            self.px(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c)


def straw_tuft(d, x, y, ang, n, ln, seed):
    r = Rand(seed)
    for k in range(n):
        a = ang + (r.f() - 0.5) * 0.9
        l = ln * (0.6 + 0.5 * r.f())
        col = [PL[4], A[22], PL[3], A[24]][k % 4]
        d.line(x, y, x + math.cos(a) * l, y + math.sin(a) * l, col)


def draw(lean=0.0, squash=0.0, flash=False, top_fall=None, sway=0.0):
    d = Dummy(lean + sway, squash, flash, None)
    stump_only = top_fall is not None
    cx = PIV[0]
    # 흙 둔덕(기울지 않음)
    for y in range(158, 168):
        for x in range(cx - 20, cx + 21):
            u, v = (x - cx) / 20.0, (y - 162) / 5.0
            if u * u + v * v <= 1:
                d.cv.px(x, y, qcol([WD[0], WD[1], WD[2], PL[0]], 0.55 - 0.4 * v - 0.2 * u, x, y))
    # 기둥(바닥 → 머리 아래)
    post_top = 54 if not stump_only else 130
    d.rect(cx - 4, post_top, cx + 4, 160, R_POST)
    for y in range(post_top, 160, 11):
        d.px(cx - 2, y, WD[0]); d.px(cx + 1, y + 4, WD[1])
    if stump_only:
        # 부러진 기둥 끝(날카로운 쪼개짐)
        for k in range(-4, 5):
            d.px(cx + k, 130 - (k % 3) * 2, WD[4] if k < 0 else WD[3])
        contact(d.cv, cx, 164, 26, 5)
        return d.cv.im
    # 가로대(팔)
    d.rect(cx - 46, 74, cx + 46, 80, R_POST, vertical=False)
    for x in (cx - 46, cx + 46):
        straw_tuft(d, x, 77, math.pi if x < cx else 0.0, 7, 9, 11 + x)
    # 몸통 자루(짚을 채움) + 밧줄 허리
    d.ellipse(cx, 98, 24, 27, R_SACK, base=0.55, tex=lambda x, y: 0.08 * math.sin(x * 0.9 + y * 0.4) * math.sin(y * 1.1))
    for x in range(cx - 23, cx + 24):
        y = 116 + int(1.5 * math.sin(x * 0.3))
        d.px(x, y, R_ROPE[1]); d.px(x, y + 1, R_ROPE[0]); d.px(x, y - 1, R_ROPE[2] if x < cx else R_ROPE[1])
    straw_tuft(d, cx - 16, 122, math.pi * 0.62, 6, 9, 31)
    straw_tuft(d, cx + 10, 123, math.pi * 0.42, 6, 8, 32)
    straw_tuft(d, cx, 124, math.pi * 0.5, 5, 7, 33)
    # 가슴 과녁(호박 물감, 낡아 갈라짐)
    for a in range(0, 360, 3):
        rr = math.radians(a)
        for rad, col in ((10, A[21]), (9, A[20]), (4, A[21]), (3, A[22])):
            if (a // 3) % 11 == 5 and rad > 8:
                continue
            d.px(cx + 2 + math.cos(rr) * rad, 96 + math.sin(rr) * rad * 0.95, col)
    d.px(cx + 2, 96, A[23]); d.px(cx + 3, 96, A[22])
    # 기운 자국(X 바늘땀)
    for k in range(5):
        d.px(cx - 14 + k, 86 + k, WD[0]); d.px(cx - 10 - k, 86 + k, WD[0])
    # 목 밧줄
    for x in range(cx - 8, cx + 9):
        d.px(x, 70, R_ROPE[2]); d.px(x, 71, R_ROPE[1])
    d.line(cx + 6, 71, cx + 10, 80, R_ROPE[1]); d.line(cx + 7, 71, cx + 12, 79, R_ROPE[2])
    # 머리 자루
    d.ellipse(cx, 54, 16, 15, R_SACK, base=0.6)
    for k in range(-3, 4):                                    # 꿰맨 X 눈
        d.px(cx - 7 + k, 51 + k, WD[0]); d.px(cx - 7 + k, 51 - k, WD[0])
        d.px(cx + 6 + k, 51 + k, WD[0]); d.px(cx + 6 - k, 51 + k, WD[0])
    for x in range(cx - 6, cx + 7, 2):                         # 꿰맨 입
        d.px(x, 60, WD[0]); d.px(x + 1, 61, WD[1])
    straw_tuft(d, cx - 2, 40, -math.pi * 0.55, 8, 10, 41)
    # 낡은 천 조각(팔에 매달림)
    for y in range(80, 104):
        w = 5 - (y - 80) // 8
        for x in range(cx + 30, cx + 30 + w + (y * 7 % 3)):
            d.px(x + (y - 80) // 6, y, SL[3] if x < cx + 32 else SL[2])
    contact(d.cv, cx, 164, 26, 5)
    im = d.cv.im
    if flash:
        p = im.load()
        for y in range(H):
            for x in range(W):
                c = p[x, y]
                if c[3] == 255:
                    p[x, y] = G[14] if (x + y) % 5 else A[26]
    return im


def straw_bits(im, t, seed, n=16, strength=1.0):
    cv = Cv.wrap(im)
    r = Rand(seed)
    for k in range(n):
        a = -math.pi * (0.15 + 0.7 * r.f()) + (0.4 if k % 2 else -0.4)
        sp = (20 + 40 * r.f()) * strength
        x = PIV[0] + 6 + math.cos(a) * sp * t
        y = 96 + math.sin(a) * sp * t + 60 * t * t
        if not (2 < x < W - 3 and 2 < y < H - 3):
            continue
        col = [PL[4], A[22], PL[3], A[24]][k % 4]
        ang = r.f() * 3.14
        for j in range(3 + k % 3):
            cv.put(x + math.cos(ang) * j, y + math.sin(ang) * j, col)
    return im


def sheet():
    frames, states, ms, hold = [], {}, [], {}

    def add(state, ims, durs):
        i0 = len(frames)
        frames.extend(ims)
        ms.extend(durs)
        states[state] = list(range(i0, i0 + len(ims)))

    add("idle", [draw(sway=s) for s in (0.0, 0.012, 0.02, 0.012, 0.0, -0.012, -0.02, -0.012)], [180] * 8)
    # hit: 번쩍(밀림 시작) → 크게 기울고 눌림 → 반대로 → 작게 → 제자리
    seq = [(0.05, 0.04, True), (0.16, 0.06, False), (0.10, 0.02, False), (-0.06, 0.0, False), (0.03, 0.0, False), (0.0, 0.0, False)]
    ims = []
    for k, (ln, sq, fl) in enumerate(seq):
        im = draw(lean=ln, squash=sq, flash=fl)
        if 1 <= k <= 3:
            straw_bits(im, k / 3.0, 70 + k)
        ims.append(im)
    add("hit", ims, [50, 70, 80, 90, 90, 80])
    seq = [(0.07, 0.06, True), (0.26, 0.09, False), (0.20, 0.04, False), (-0.10, 0.0, False), (0.06, 0.0, False), (-0.03, 0.0, False), (0.0, 0.0, False)]
    ims = []
    for k, (ln, sq, fl) in enumerate(seq):
        im = draw(lean=ln, squash=sq, flash=fl)
        if 1 <= k <= 4:
            straw_bits(im, k / 4.0, 90 + k, n=28, strength=1.5)
        ims.append(im)
    add("hit_heavy", ims, [60, 80, 90, 100, 90, 90, 90])
    # broken: 기둥이 부러져 상체가 옆으로 넘어가 바닥에 눕는다(상체 그림을 꺾인 점 기준 회전 — 최근접)
    from PIL import Image
    whole = draw()
    stump = draw(top_fall=(0, 0, 0.0))
    top = whole.copy()
    tp = top.load()
    for y in range(130, H):
        for x in range(W):
            tp[x, y] = (0, 0, 0, 0)
    for y in range(H):                                 # 접지 그림자(반투명)는 상체에서 뺌
        for x in range(W):
            if 0 < tp[x, y][3] < 255:
                tp[x, y] = (0, 0, 0, 0)
    ims = []
    brk = (PIV[0] + 4, 130)
    for k, (deg, dy) in enumerate([(-8, 0), (-24, 2), (-50, 5), (-80, 9), (-92, 11)]):
        im = stump.copy()
        big = Image.new("RGBA", (W * 3, H * 3), (0, 0, 0, 0))
        big.alpha_composite(top, (W, H))
        r = big.rotate(deg, resample=Image.NEAREST, center=(W + brk[0], H + brk[1]))
        # 누운 몸통 아래 끝이 바닥(피벗 y 근처)에 닿게 dy 를 정함 — 가로대는 카메라 쪽으로 뻗어 화면 아래로 나온다(쿼터뷰)
        layer = r.crop((W, H - dy, 2 * W, 2 * H - dy))
        if k >= 3:
            sh = Canvas(W, H)
            sh.paste(im, 0, 0)
            contact(sh, brk[0] + 32, 162, 30, 5)
            im = sh.im
        im.alpha_composite(layer)
        if k in (1, 2):
            straw_bits(im, 0.4 * k, 120 + k, n=24, strength=1.3)
        ims.append(im)
    add("broken", ims, [60, 70, 80, 100, 600])
    hold["broken"] = states["broken"][-1]
    meta = {
        "directions": ["any"], "pivot": {"x": PIV[0], "y": PIV[1]}, "footprint": [1, 1], "solid": True, "depth": "y", "pixelScale": 0.5,
        "occludeAbove": 120, "version": "v3-r61", "states": states, "stateHold": hold,
        "stateLoop": {"idle": True, "hit": False, "hit_heavy": False, "broken": False},
        "flashFrames": [states["hit"][0], states["hit_heavy"][0]],
        "interact": "hit", "replaces": "structures/battlefield_dummy(16×32, 49라운드) — 같은 states(idle·hit·broken) + hit_heavy",
        "stateNote": ("idle 8프레임 흔들림 루프. 맞으면 hit(일반 타) 또는 hit_heavy(막타·강공·대검) 1회 후 idle 로. 첫 칸은 하얗게 번쩍(flashFrames). "
                      "맞은 방향 반대로 기울게 하려면 flipX — 그림은 오른쪽으로 밀림(왼쪽에서 맞음) 기준. broken 은 마지막 칸 유지(stateHold)"),
        "systemHints": {"knockbackPx": 0, "hitstopMs": "무기 히트스톱 그대로", "note": "허수아비는 제자리 — 넉백 대신 그림이 기운다. 피격 숫자·fx(hit_<무기>)는 그대로 띄운다"},
        "anchors": {"hitCenter": {"x": PIV[0] + 2, "y": 96, "note": "가슴 과녁 중심(시트 도트) — 적중 fx·피해 숫자 위치"}, "headTop": {"x": PIV[0], "y": 38}},
        "floor": "stage1", "paletteSwap": False,
        "palette": "parts/art/palette/lopad.json gray + 1층 램프 + v2 재질 WD·PL·SL — 새 색 없음",
        "design": "짚을 채운 자루 몸·머리(꿰맨 X 눈·입) + 나무 기둥·가로대 + 가슴의 낡은 호박 과녁 + 팔 끝 짚 다발·매단 천 조각. 쿼터뷰 64도트 칸 밀도",
        "source": SRC,
    }
    return "tutorial_dummy", [frames], W, H, meta, ms, False
