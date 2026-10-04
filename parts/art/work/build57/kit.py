"""57라운드 빌드 축 아트 공용 도구 — 캔버스·방향 변환·붓획·자르기·시트 쓰기.

기존 도구를 읽기만 하고 그대로 쓴다(고치지 않음):
  fx_v3/fxkit(레이어 램프 래스터) · fx_weapons_v3/wkit(팔레트·Frame·flake·ember·jag) · combo56_fx/brush(붓획 Stroke)·fx56(TA 회전)
  · combo56_res/rk(시트 쓰기·검사 write_sheet·fit) · atlas57/gridsheet(아틀라스 → 격자 읽기).
색: 주인공 v3 30색 안의 재·호박 + 백열 X0/X1·A26 은 glowFrames(판정 순간)의 몇 도트만. 반투명 0.
좌표: v3 도트(pixelScale 0.5). 1.25배(58 Q2)는 시스템 렌더 배율 — 이 시트는 96×144 몸 기준 도트로 그린다.
"""
import json
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets/sprites")
for p in ("combo56_fx", "combo56_res", "atlas57", "fx_weapons_v3", "fx_v3", "branch57"):
    sys.path.insert(0, os.path.join(WORK, p))
import fx56 as F  # noqa: E402
import brush as BR  # noqa: E402
from brush import W, FK  # noqa: E402
import rk  # noqa: E402
import gridsheet  # noqa: E402

VERSION = "v3-r57-build"
rk.VERSION = VERSION
STAGE = os.path.join(HERE, "out", "grid")          # 격자 원본(작업 폴더) — publish 가 assets 에 아틀라스로 반영(§19.5)
OUT_FX = os.path.join(STAGE, "fx")
OUT_W = os.path.join(STAGE, "weapons")

CANVAS = 1100
CO = (550, 560)                 # 판정 원점(캔버스)
HIT_UP = 40
PV = (CO[0], CO[1] + HIT_UP)    # 주인공 발 피벗(캔버스)
KY = 0.85                       # 바닥 타원 세로 압축(기존 균열·진동과 같음)
TILE = 64                       # 1칸 = 16 월드 px = 64 도트
HEAD_UP = 124                   # 주인공 머리 꼭대기 바로 위(피벗 위 도트, player_idle 머리 꼭대기 y20 / 피벗 y138)
DIRS4 = ["down", "up", "left", "right"]
DIR_ANG = F.DIR_ANG

X0, X1 = W.X0, W.X1
A17, A18, A19, A21, A23, A25, A26 = W.A17, W.A18, W.A19, W.A21, W.A23, W.A25, W.A26
B0, B1, B2, B3 = W.B0, W.B1, W.B2, W.B3
S0, S1, S2, S3 = W.S0, W.S1, W.S2, W.S3
K0, K1, K2 = "#141516", "#1d2028", "#272b35"          # 주인공 팔레트 가장 어두운 쇠·그림자
INK_K, INK_G, HOT, FLAKE, FLAKE_G = BR.INK_K, BR.INK_G, BR.HOT, BR.FLAKE, BR.FLAKE_G
EMB = [A19, A21, A23]
EMB_HI = [A19, A21, A23, A25]
LIQ = [A17, A18, A19, A21, A23]                      # 술(호박 액체)
LIQ_HI = [A21, A23, A25]
ASH = [S0, S1, S2, S3]
SHADOW = [K0, K1, S0, S1]

EFFECT_RULE = ("57라운드 빌드 축 — 재·호박 팔레트만(주인공 v3 30색 안), 반투명 없음. 흰 픽셀(X0/X1·A26)은 glowFrames(판정·발동 순간)의 "
               "몇 도트만, 그 밖 프레임은 A25(#eecc78) 이하 — 빌드 검사 통과. 연격·갈래 획은 56라운드 Q11 붓획(닫힌 원 금지)")
R57 = "57라운드 Q22~Q39 빌드 축(설계안 design-2026-10-04-build-axis.md · -chwigi.md)"


def frame(w=CANVAS, h=CANVAS):
    return W.Frame(w, h, None)


def TA(d, o=CO):
    return F.TA(d, *o)


def starts(ms):
    s, t = [], 0
    for m in ms:
        s.append(t)
        t += m
    return s


def body(rel):
    return gridsheet.load_meta(os.path.join(SPR, rel + ".json"))


def grid_frames(rel):
    """assets 의 시트(아틀라스 또는 격자) → (격자 메타, {행: [프레임 RGBA]})."""
    jp = os.path.join(SPR, rel + ".json")
    j = gridsheet.load_meta(jp)
    im = gridsheet.open_grid(jp)
    fw, fh, n = j["frameWidth"], j["frameHeight"], j["frames"]
    return j, {d: [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r, d in enumerate(j["directions"])}


def ell(cx, cy, a_deg, r, ky=KY, z=0.0):
    a = math.radians(a_deg)
    return (cx + math.cos(a) * r, cy + math.sin(a) * r * ky - z)


def ring_pts(cx, cy, r, a0, a1, ky=KY, n=None, z=0.0):
    n = n or max(16, int(abs(a1 - a0) * r / 90))
    return [ell(cx, cy, a0 + (a1 - a0) * i / n, r, ky, z) for i in range(n + 1)]


def stroke(pts, w, seed=1, **kw):
    return BR.Stroke(pts, w, seed=seed, **kw)


def line_pts(p0, p1, n=24, bend=0.0):
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    return [(x0 + dx * i / n + nx * bend * math.sin(math.pi * i / n), y0 + dy * i / n + ny * bend * math.sin(math.pi * i / n)) for i in range(n + 1)]


def rot(p, a_deg, o=(0.0, 0.0)):
    a = math.radians(a_deg)
    x, y = p[0] - o[0], p[1] - o[1]
    return (o[0] + x * math.cos(a) - y * math.sin(a), o[1] + x * math.sin(a) + y * math.cos(a))


# =============================================================================
# 균열(땅 금) — 로컬 x 방향으로 달리는 금 + 양옆 가지 + 흙 테. 회전 시트(오른쪽 = 진행 방향)
# =============================================================================
class Crack:
    def __init__(self, x0, length, seed, amp=3.0, branches=4, width=1.4, ky=1.0):
        self.rng = random.Random(seed)
        r = self.rng
        self.x0, self.L = x0, length
        self.main = W.jag(r, (x0, 0.0), (x0 + length, 0.0), n=max(4, int(length / 18)), amp=amp)
        self.br = []
        for j in range(branches):
            f = x0 + length * r.uniform(0.15, 0.9)
            sgn = 1 if j % 2 else -1
            a = math.radians(sgn * r.uniform(22, 48))
            ln = r.uniform(10, 18) + length * 0.06
            self.br.append((f, W.jag(r, (f, 0.0), (f + math.cos(a) * ln, math.sin(a) * ln), n=3, amp=1.4)))
        self.width = width
        self.ky = ky

    def _xf(self, pts, t):
        return [t((x, y * self.ky)) for x, y in pts]

    def draw(self, Lgr, Lc, t, front=None, k=0.0, v=0.95, hot=None):
        """front = 앞머리 x(로컬, None = 끝까지). k = 식음 0..1."""
        lim = self.x0 + self.L if front is None else front
        pts = [p for p in self.main if p[0] <= lim + 0.01]
        if front is not None and front < self.x0 + self.L and len(pts) >= 1:
            pts = pts + [(front, pts[-1][1] * 0.5)]
        if len(pts) >= 2:
            scr = self._xf(pts, t)
            Lgr.stroke(scr, self.width + 1.2, prof=FK.tp_both(0.4, 0.5), v=0.8 * (1 - 0.35 * k))
            Lc.stroke(scr, self.width * 0.65 * (1 - 0.3 * k), prof=FK.tp_both(0.5, 0.5), v=v - 0.5 * k,
                      dash=(9.0, 0.78 - 0.35 * k, 0.2) if k > 0.35 else None)
            if hot is not None and front is not None:
                hx, hy = scr[-1]
                hot.stamp(hx, hy, 1.4, 1.0, soft=0.6)
        for f, bp in self.br:
            if f > lim:
                continue
            scr = self._xf(bp, t)
            Lgr.stroke(scr, self.width * 0.6 + 0.8, prof=FK.tp_tail(0.8), v=0.75 * (1 - 0.35 * k))
            Lc.stroke(scr, self.width * 0.4, prof=FK.tp_tail(0.8), v=(0.85 - 0.5 * k))


def ground_layers(fr):
    """균열용 레이어 묶음(아래 → 위)."""
    return dict(dust=fr.L(W.R_DUST), gr=fr.L([B0, B1, B2]), crk=fr.L([A18, A19, A21, A23]), flake=fr.L(FLAKE_G),
                ink=fr.L(INK_G), emb=fr.L(EMB), hot=fr.L(HOT))


def stones(L, t, pts, frame_i, born, seed, size=2.4, rise=7.0):
    """균열 위로 솟았다 떨어지는 돌 조각. pts = [(로컬 x, y)] — born 프레임에 솟음."""
    r = random.Random(seed)
    for (x, y), b in zip(pts, born):
        age = frame_i - b
        if age < 0 or age > 4:
            continue
        sx, sy = t((x, y))
        h = rise * (age * (3 - age)) / 2.25 if age <= 3 else -1.0
        W.flake(L, sx + r.uniform(-1, 1), sy - h, size * (1 - 0.15 * age), r.uniform(0, 6), v=0.95 - 0.12 * age)


# =============================================================================
# 실루엣(그림자 분신·잔상) — 몸 시트 프레임 → 재 껍데기
# =============================================================================
AMBERS = {(0xd6, 0x7a, 0x11), (0xe2, 0xa3, 0x3c), (0xee, 0xcc, 0x78), (0x8b, 0x4d, 0x22), (0xf4, 0xde, 0x9b)}


def silhouette(im, tone="ash", erode=0.0, seed=0, cracks=True, rise=0, hot_frac=1.0):
    """몸 프레임 → 어두운 재 실루엣(체크 디더 2단 + 밝은 재 테 + 금 자리 호박 점). erode 0..1 = 아래부터 체크 구멍으로 빔."""
    px = im.load()
    w, h = im.size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    po = out.load()
    bb = im.getbbox()
    if not bb:
        return out
    fill = {"ash": (S0, K2), "dark": (K2, K1), "hot": (A17, B1)}[tone]
    rim = {"ash": S2, "dark": S2, "hot": A19}[tone]
    hot = {"ash": A21, "dark": A21, "hot": A23}[tone]
    top, bot = bb[1], bb[3]
    for y in range(bb[1], bb[3]):
        for x in range(bb[0], bb[2]):
            c = px[x, y]
            if not c[3]:
                continue
            yy = y - rise
            if erode > 0:
                q = (bot - y) / max(1, bot - top)          # 0 발 → 1 머리
                if W.h2(x >> 1, y >> 1, seed) < erode * 1.6 - q * 0.9:
                    continue
            edge = any(not (0 <= x + dx < w and 0 <= y + dy < h) or not px[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if cracks and c[:3] in AMBERS and W.h2(x >> 1, y >> 1, 101) < hot_frac:
                col = hot
            elif edge:
                col = rim
            else:
                col = fill[(x + y) & 1]
            if 0 <= yy < h:
                po[x, yy] = FK.hexrgb(col) + (255,)
    return out


# =============================================================================
# 자르기 · 쓰기
# =============================================================================
def write(name, frames, rows, ms, glow, anchor, fit="pivot", meta=None, out_dir=OUT_FX, loop=False, cap=14, edge_ok=False,
          hot_ok=None, src="parts/art/work/build57/build.py"):
    """frames = {행: [큰 캔버스 RGBA]}. anchor = 캔버스 위 피벗. fit = 'pivot'(피벗이 틀 안) | 'center'(피벗이 틀 가운데 — 회전 시트) | 'none'."""
    for d in rows:
        assert len(frames[d]) == len(ms), (name, d, len(frames[d]), len(ms))
    if fit == "center":
        cut, pv = rk.fit_centered(frames, anchor)
    elif fit == "none":
        cut, pv = frames, anchor
    else:
        cut, pv = rk.fit_frames(frames, anchor)
    rk.SRC = src
    m = dict(pivot={"x": int(pv[0]), "y": int(pv[1])})
    m.update(meta or {})
    m.setdefault("effectRule", EFFECT_RULE)
    m.setdefault("r57", R57)
    sheet, j, _ = rk.write_sheet(name, out_dir, rows, cut, ms, m, glow=glow, cap=cap, loop=loop, edge_ok=edge_ok, hot_ok_frames=hot_ok)
    return name, j["frameWidth"], j["frameHeight"], j["colors"], len(rows), len(ms)


def pp_meta(**kw):
    """주인공 발 피벗 시트 공통."""
    m = dict(anchor="player_pivot", pivotNote="pivot = 주인공 발(몸 피벗). 판정 원점 = pivot 위 40 도트")
    m.update(kw)
    return m


class TR:
    """로컬 (x, y) → 캔버스: 각 a_deg 회전 + 원점 o (화면 시계 방향 +)."""

    def __init__(self, a_deg=0.0, o=CO):
        a = math.radians(a_deg)
        self.c, self.s, self.o = math.cos(a), math.sin(a), o

    def __call__(self, p):
        return (self.o[0] + p[0] * self.c - p[1] * self.s, self.o[1] + p[0] * self.s + p[1] * self.c)

    def pts(self, pts):
        return [self(p) for p in pts]


def crescent(L, cx, cy, rx, ry, thick, v=1.0, ang=0.0, vin=None):
    """초승달(바닥 위 납작): 타원(rx, ry) 안 − 같은 타원을 ang 방향 반대로 thick 만큼 옮긴 것. 볼록한 쪽 = ang 방향."""
    ca, sa = math.cos(ang), math.sin(ang)
    ox, oy = -ca * thick, -sa * thick * (ry / rx)
    for y in range(int(cy - ry - 2), int(cy + ry + 3)):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            q1 = (px / rx) ** 2 + (py / ry) ** 2
            q2 = ((px - ox) / rx) ** 2 + ((py - oy) / ry) ** 2
            if q1 <= 1.0 and q2 > 1.0:
                d = min(1.0, (q2 - 1.0) * 2.2)
                L.put(x, y, v * (0.55 + 0.45 * d) if vin is None else vin(px, py, d))


def paste(dst, src, xy):
    dst.alpha_composite(src, (int(round(xy[0])), int(round(xy[1]))))
