"""61라운드 단계 4 (P12 무기 성장) 공용 — 1차·2차 각성 외형 오버레이 · 미리보기 정지 그림 · 각성 연출 fx.

설계 기준: parts/producer/decisions/2026-10-05-P12-weapon-growth.md, 계약 art §26.
틀·피벗·프레임·ms 는 기존 각성 오버레이(weapons/v3/<시트>_awaken, 60라운드 awaken60)와 같다 — 같은 PAD·같은 시트 목록
(폐기된 greatsword_guard_rush 만 뺌, 계약 §25 폐기 목록).

기존 도구는 읽기만 한다: awaken60(prod_overlay·prod_common·kit60 — Ctx·팔레트·셋째 갈래 그림), combo56_res/overlay(날 찾기),
build57(grid_frames·rk.write_sheet), atlas57(build.convert_sheet·apply_in_place·verify).
산출 스테이징은 이 폴더 out/ 아래만 쓴다(awaken60/out·props_v3/_atlas_tmp 공유 안 함).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets/sprites")
AW = os.path.join(WORK, "awaken60")
sys.path.insert(0, AW)
sys.path.insert(0, os.path.join(WORK, "build57"))
sys.path.insert(0, os.path.join(WORK, "atlas57"))

import prod_common as P  # noqa: E402
import prod_overlay as PO  # noqa: E402
import kit60 as K6  # noqa: E402
from kit60 import Cv, F, G, A, GRN, TEAL, OCH, VIO, GOLD, CRI, SIL, SL, PL, WD, X0, X1, INK, h2, clamp, smooth  # noqa: E402,F401

OV = PO.OV
FA = PO.FA
K57 = P.K57

VERSION = "v4-r61-growth"
SRC = "parts/art/work/growth61/build.py (61라운드 단계 4 P12 — 무기 1차·2차 각성 외형)"
STAGE = os.path.join(HERE, "out", "grid")
TMP = os.path.join(HERE, "out", "_atlas_tmp_growth61")
CAP = 24
PALETTE_NOTE = ("61 단계 4(P12): 각성 외형은 60라운드 Q19 규칙 그대로 — LOPAD 팔레트 무채 16 + 층 램프(고정색, 지역 교체 없음) "
                "+ 흉갑 SL·붕대 PL·흙 WD + 백열 X0/X1. 시트당 색 상한 24. _a2_glow 는 회백(무채 + X0)만 — 시스템 tint 대상")
ALLOWED = P.ALLOWED

# 갈래·길 (계약 §26 id). 길 강조색 = pathTint(RGB) — _a2_glow 시트에 곱하는 색, 2차 휘두름 궤적 trailTint 도 같은 값.
BRANCHES = {
    "katana": [
        ("senpu", "선풍", "무리 한가운데로 파고드는 칼", {"whirl": ("회오리", [196, 228, 255]), "zangetsu": ("잔월", [255, 212, 110])}),
        ("kabuto", "투구가르기", "한 놈을 쪼개는 칼", {"ittou": ("일도양단", [255, 92, 72]), "meikyo": ("명경", [200, 240, 255])}),
        ("mangetsu", "만월", "받아치는 칼", {"sakugetsu": ("삭월", [176, 150, 255]), "hozuki": ("보름", [255, 226, 140])}),
    ],
    "greatsword": [
        ("crush", "파쇄", "뛰어올라 땅을 깨는 대검", {"quake": ("지진", [255, 168, 60]), "echo": ("반향", [110, 232, 214])}),
        ("weight", "중압", "맞받아치는 벽", {"giant": ("거인", [255, 210, 100]), "congest": ("울혈", [232, 70, 84])}),
        ("berserk", "광전", "몰아치는 대검", {"bloodwind": ("혈풍", [255, 64, 64]), "ironpeak": ("철산", [170, 204, 255])}),
    ],
    "dagger": [
        ("twin", "쌍격", "둘이 싸우는 단검", {"frenzy": ("난무", [192, 226, 255]), "bleed": ("출혈", [255, 72, 92])}),
        ("gale", "질풍", "치고 빠지는 단검", {"flyblade": ("비도", [172, 255, 150]), "hotwind": ("열풍", [255, 150, 60])}),
        ("hyakki", "백귀", "사냥하는 단검", {"nightwalk": ("야행", [172, 132, 255]), "onibi": ("귀화", [100, 240, 220])}),
    ],
    "bow": [
        ("rapid", "속사", "쏟아붓는 활", {"split": ("연궁", [120, 236, 220]), "endless": ("무한통", [255, 212, 110])}),
        ("snipe", "저격", "한 발의 활", {"surehit": ("필중", [255, 80, 80]), "pierce": ("천공", [192, 230, 255])}),
        ("meteor", "유성", "하늘을 부르는 활", {"starfall": ("성우", [200, 222, 255]), "comet": ("혜성", [255, 150, 70])}),
    ],
}
WEAPONS = ("katana", "greatsword", "dagger", "bow")
DEPRECATED = {"greatsword_guard_rush"}            # 계약 §25 폐기(로드 제외) — v4 에서 만들지 않음


def sheets_of(weapon):
    return [s for w, s in FA.SHEETS if w == weapon and s not in DEPRECATED]


def branch_info(weapon, bid):
    for b in BRANCHES[weapon]:
        if b[0] == bid:
            return b
    raise KeyError((weapon, bid))


# =============================================================================
# 무기 축(geometry) — 프레임마다 날을 찾아 '설계 좌표'(u = 쥔 곳 → 끝, v = 법선)로 바꾸는 정보
# =============================================================================
class Geo:
    """weapon 프레임 하나의 축 정보. kind = blade | sheathed | bow | none."""

    def __init__(self, kind="none"):
        self.kind = kind
        self.pts = set()
        self.comp = set()
        self.near = {}
        self.g = (0.0, 0.0)
        self.ang = 0.0
        self.sc = 1.0
        self.flip = 1
        self.tip_vis = True
        self.tsu = []
        self.hot = []
        self.L = 0.0

    def near_set(self, r):
        r = round(r, 1)
        if r not in self.near:
            self.near[r] = PO.dilate(self.comp or self.pts, r)
        return self.near[r]

    def loc(self, x, y):
        """원 프레임 좌표 (x, y) 픽셀 중심 → 설계 (ud, vd)."""
        u, v = PO.local((x, y), self.g, self.ang)
        return u / self.sc, v * self.flip

    def w(self, ud, vd):
        """설계 (ud, vd) → 원 프레임 좌표."""
        return K6.L2W(self.g, self.ang, ud * self.sc, vd * self.flip)


def katana_geo(im, tip_a, grip_a, sheathed, refine):
    px = im.load()
    fw, fh = im.size
    if not sheathed:
        bl = OV.katana_blade(im, tip_a, refine)
    else:
        bl = None
    if bl is None or (tip_a is None and not bl[1]):
        gg = Geo("sheathed")
        gg.hot = [(x, y) for y in range(fh) for x in range(fw) if px[x, y][3] and px[x, y][:3] in OV.SHEATH_GLOW]
        gg.comp = {(x, y) for y in range(fh) for x in range(fw) if px[x, y][3]}
        return gg
    pts, edge, a, b = bl
    gg = Geo("blade")
    gg.pts = set(pts)
    gg.comp = set(pts)
    gg.edge = edge
    gg.tsu = [p for p in pts if P.hx(px[p]) in PO.SLSET]
    if grip_a:
        g = (grip_a[0], grip_a[1])
    elif gg.tsu:
        g = (sum(p[0] for p in gg.tsu) / len(gg.tsu), sum(p[1] for p in gg.tsu) / len(gg.tsu))
    else:
        g = (b[0] + 0.5, b[1] + 0.5)
    tip = (a[0] + 0.5, a[1] + 0.5)
    L = math.hypot(tip[0] - g[0], tip[1] - g[1])
    gg.g, gg.L = g, L
    gg.ang = math.atan2(tip[1] - g[1], tip[0] - g[0]) if L > 0.5 else 0.0
    gg.sc = clamp(L / 58.0, 0.12, 1.3)
    if edge:
        s = sum(PO.local(p, g, gg.ang)[1] for p in edge) / len(edge)
        gg.flip = 1 if s >= 0 else -1
    gg.tip_vis = tip_a is None or math.hypot(a[0] - tip_a[0], a[1] - tip_a[1]) < 6
    if L < 10:
        gg.kind = "short"
    return gg


def gs_geo(im, grip, tip):
    px = im.load()
    if tip and not grip:
        comps = OV.components(im)
        if comps:
            c = min(comps, key=lambda cc: min((x - tip[0]) ** 2 + (y - tip[1]) ** 2 for x, y in cc))
            pm = max(c, key=lambda p: (p[0] - tip[0]) ** 2 + (p[1] - tip[1]) ** 2)
            grip = (pm[0] + (tip[0] - pm[0]) * 0.17, pm[1] + (tip[1] - pm[1]) * 0.17)
    if not (grip and tip):
        return Geo("none")
    pts = OV.gs_blade(im, grip, tip)
    if not pts:
        return Geo("none")
    pts = {p for p in pts if P.hx(px[p]) not in PO.SLSET}
    if not pts:
        return Geo("none")
    gg = Geo("blade")
    gg.pts = pts
    gg.g = (grip[0], grip[1])
    L = math.hypot(tip[0] - grip[0], tip[1] - grip[1])
    if L < 4:
        return Geo("none")
    gg.L = L
    gg.ang = math.atan2(tip[1] - grip[1], tip[0] - grip[0])
    gg.sc = clamp(L / 93.0, 0.12, 1.3)
    gg.flip = PO.axis_flip_up(gg.ang)
    gg.tip_vis = min(math.hypot(p[0] - tip[0], p[1] - tip[1]) for p in pts) < 6
    # 손잡이·코등이(가죽·흉갑색)까지 포함한 덩어리(가드 장식 가림 판단용)
    comps = OV.components(im)
    if comps:
        c = min(comps, key=lambda cc: min((x - tip[0]) ** 2 + (y - tip[1]) ** 2 for x, y in cc))
        gg.comp = set(c) | pts
    else:
        gg.comp = set(pts)
    gg.tsu = [p for p in gg.comp if P.hx(px[p]) in PO.SLSET]
    return gg


def dagger_geo(im, grip, tip):
    px = im.load()
    if grip is None and tip is not None:
        comps = OV.components(im)
        c = min(comps, key=lambda cc: min((x - tip[0]) ** 2 + (y - tip[1]) ** 2 for x, y in cc)) if comps else None
        grip = max(c, key=lambda p: (p[0] - tip[0]) ** 2 + (p[1] - tip[1]) ** 2) if c else None
    if not (grip and tip):
        return Geo("none")
    pts = FA.seg_mask(im, grip, tip, rad=5.5, umin=0.25)
    pts = {p for p in pts if P.hx(px[p]) not in PO.PLSET}
    if len(pts) < 4:
        return Geo("none")
    gg = Geo("blade")
    gg.pts = pts
    gg.g = (grip[0], grip[1])
    L = math.hypot(tip[0] - grip[0], tip[1] - grip[1])
    gg.L = L
    gg.ang = math.atan2(tip[1] - grip[1], tip[0] - grip[0])
    gg.sc = clamp(L / 26.0, 0.2, 1.4)
    gg.flip = PO.axis_flip_up(gg.ang)
    gg.tip_vis = min(math.hypot(p[0] - tip[0], p[1] - tip[1]) for p in pts) < 5
    comps = OV.components(im)
    c = min(comps, key=lambda cc: min((x - tip[0]) ** 2 + (y - tip[1]) ** 2 for x, y in cc)) if comps else []
    gg.comp = set(c) | pts
    return gg


def bow_geo(im, grip, tip, hand_r, state):
    """bow_frame(awaken60) 과 같은 PCA 축: e = 활대 방향, n = 쏘는 방향. 설계 = (a = n 성분, s = 활대 성분 ±30 으로 맞춤)."""
    px = im.load()
    fw, fh = im.size
    allp = [(x, y) for y in range(fh) for x in range(fw) if px[x, y][3]]
    if len(allp) < 6:
        return Geo("none")
    if grip is None:
        grip = (sum(p[0] for p in allp) / len(allp), sum(p[1] for p in allp) / len(allp))
    g = (grip[0], grip[1])
    limb = [p for p in allp if P.hx(px[p]) not in PO.AMBER]
    aim_ref = None
    if hand_r is not None and state in ("draw", "full", "release") and math.hypot(hand_r[0] - g[0], hand_r[1] - g[1]) > 10:
        aim_ref = (g[0] - hand_r[0], g[1] - hand_r[1])
    elif tip is not None and math.hypot(tip[0] - g[0], tip[1] - g[1]) > 8:
        aim_ref = (tip[0] - g[0], tip[1] - g[1])
    if aim_ref is not None:
        ex, ey = aim_ref
        ll = math.hypot(ex, ey) or 1
        limb = [p for p in limb if abs(((p[0] + 0.5 - g[0]) * -ey + (p[1] + 0.5 - g[1]) * ex) / ll) > 2.5]
    if len(limb) < 14:
        return Geo("none")
    mx = sum(p[0] for p in limb) / len(limb)
    my = sum(p[1] for p in limb) / len(limb)
    sxx = sum((p[0] - mx) ** 2 for p in limb)
    syy = sum((p[1] - my) ** 2 for p in limb)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in limb)
    th = 0.5 * math.atan2(2 * sxy, sxx - syy)
    e = (math.cos(th), math.sin(th))
    n = (-e[1], e[0])
    offs = [((p[0] + 0.5 - g[0]) * n[0] + (p[1] + 0.5 - g[1]) * n[1]) for p in limb]
    if sum(offs) / len(offs) > 0:
        n = (-n[0], -n[1])
    if aim_ref is not None and aim_ref[0] * n[0] + aim_ref[1] * n[1] < 0:
        n = (-n[0], -n[1])
    ss = [((p[0] + 0.5 - g[0]) * e[0] + (p[1] + 0.5 - g[1]) * e[1]) for p in limb]
    smin, smax = min(ss), max(ss)
    if smax - smin < 18:
        return Geo("none")
    gg = Geo("bow")
    gg.g, gg.e, gg.n = g, e, n
    gg.smin, gg.smax = smin, smax
    gg.limb, gg.ss = limb, ss
    gg.pts = set(allp)
    gg.comp = set(allp)
    gg.scale = clamp((smax - smin) / 68.0, 0.4, 1.25)
    gg.tip = tip
    gg.state = state

    def limb_point(s_target):
        cand = [p for p, s in zip(limb, ss) if abs(s - s_target) < 1.6]
        if not cand:
            return None
        return (sum(p[0] for p in cand) / len(cand) + 0.5, sum(p[1] for p in cand) / len(cand) + 0.5)
    gg.limb_point = limb_point
    gg.ends = {}
    for sgn, s0 in ((1, smax), (-1, smin)):
        p_end = limb_point(s0 - sgn * 1.0)
        p_in = limb_point(s0 - sgn * 7.0)
        if p_end and p_in:
            dv = (p_end[0] - p_in[0], p_end[1] - p_in[1])
            ll = math.hypot(*dv) or 1
            gg.ends[sgn] = (p_end, (dv[0] / ll, dv[1] / ll))
    return gg


# =============================================================================
# 시트 쓰기 — 격자 원본(out/grid/<cat>) → publish 가 assets/<cat>/v4 트림 아틀라스로
# =============================================================================
def write_sheet(cat, name, rows, frames, ms, meta, loop=False, glow=None, cap=CAP):
    K57.rk.VERSION = VERSION
    K57.rk.SRC = SRC
    K57.rk.PALETTE_NOTE = PALETTE_NOTE
    m = dict(meta)
    m["palette"] = PALETTE_NOTE
    if glow is not None:
        m["glowFrames"] = sorted(glow)
    od = os.path.join(STAGE, cat)
    K57.rk.write_sheet(name, od, rows, frames, ms, m, glow=None, cap=cap, loop=loop, allowed=ALLOWED, edge_ok=True)
    return name


def hx(c):
    return "#%02x%02x%02x" % tuple(c[:3])


def rgb(h):
    return K6.hexrgb(h)
