"""56라운드 Q14·Q15 — 무기 위에 겹치는 자원 표시 오버레이(무기 시트와 같은 틀·같은 프레임 번호·같은 시각).

  칼 검기(劍氣) 3단  weapons/v3/<칼 시트>_ki1|ki2|ki3       재 → 호박 → 백열(3단은 불꽃 흔들림) — 키아트 sheet_katana 4번
  대검 울분(鬱憤) 3단 weapons/v3/<대검 시트>_grudge1|2|3    막은 자국이 재 → 잔불로 — 키아트 sheet_greatsword 4번

방식(제안): '오버레이 시트'. 시스템은 무기 시트를 그린 바로 위에 같은 프레임 번호의 오버레이를 같은 피벗·offset 으로 겹친다.
  · 팔레트 교체 맵은 칼날·칼집·손잡이가 같은 재/호박 색을 나눠 써서 칼날만 바꿀 수 없고, 불꽃·연기처럼 칼 밖으로 나가는 그림을 못 넣는다.
  · 오버레이는 원본 무기 시트를 건드리지 않으므로 다른 작업(E1 새 동작)이 무기 시트를 다시 내도 이 빌드만 다시 돌리면 맞는다.
칼날 찾기(원본 무기 시트에서 자동):
  · 칼: 프레임의 불투명 덩어리(8연결) 중 칼끝(bladeTipAnchors)이 든 덩어리 — 칼끝 기준점이 없는 시트(carry_drawn)는 날선 호박(#d67a11)이
    가장 많은 덩어리. 칼끝이 null(칼집 안)인 프레임은 칼집 금(호박 점)만 단계 색으로 달군다.
  · 대검: gripAnchors(손) → bladeTipAnchors(칼끝) 선분에서 7 도트 안의 불투명 쇠·녹 픽셀(가죽 손잡이 제외).
"""
import json
import math
import os
import sys
from collections import deque
from multiprocessing import Pool

from PIL import Image

import rk
from rk import W, FK

KATANA_SHEETS = ["katana_rise", "katana_fall", "katana_issen",
                 "katana_carry_idle", "katana_carry_walk", "katana_carry_run", "katana_carry_dash",
                 "katana_carry_drawn_idle", "katana_carry_drawn_walk", "katana_carry_drawn_run", "katana_carry_drawn_dash",
                 # 56라운드 Q55 — E1 새 칼 기본기
                 "katana_counter", "katana_iai",
                 # 56라운드 Q55 — 계약 §7.1(뽑기·넣기)·§6.2(무기 든 보조 동작)로 게임이 여전히 쓰는 옛 칼 시트.
                 # katana_combo1~3 은 §17 새 연격(katana_rise·fall·issen)으로 대체되어 제외
                 "katana_draw", "katana_sheathe", "katana_special"]
GS_SHEETS = ["greatsword_sweep_cw", "greatsword_sweep_ccw", "greatsword_cleave", "greatsword_charge", "greatsword_charge_slam",
             "greatsword_charge_plunge",
             "greatsword_carry_idle", "greatsword_carry_walk", "greatsword_carry_run", "greatsword_carry_dash",
             "greatsword_carry_drawn_idle", "greatsword_carry_drawn_walk", "greatsword_carry_drawn_run", "greatsword_carry_drawn_dash",
             # 56라운드 Q55 — E1 새 대검 기본기(280×296 틀)
             "greatsword_tackle", "greatsword_brace_upswing", "greatsword_leap_slam", "greatsword_guard_rush"]

EDGE_COLS = {(0xd6, 0x7a, 0x11), (0xe2, 0xa3, 0x3c), (0xee, 0xcc, 0x78), (0xf4, 0xde, 0x9b)}
SHEATH_GLOW = {(0xd6, 0x7a, 0x11), (0x8b, 0x4d, 0x22)}
LEATHER = {(0x3b, 0x2a, 0x1f), (0x4f, 0x38, 0x28), (0x14, 0x16, 0x1c)}


def h2(*a):
    s = 0
    for k, v in enumerate(a):
        s = s * 131 + int(v) * (k + 7)
    return W.h2(s & 0xFFFF, (s >> 16) & 0xFFFF, 77)


# =============================================================================
# 칼날 마스크
# =============================================================================
def components(im):
    px = im.load()
    w, h = im.size
    seen = set()
    comps = []
    bb = im.getbbox()
    if not bb:
        return comps
    for y in range(bb[1], bb[3]):
        for x in range(bb[0], bb[2]):
            if px[x, y][3] and (x, y) not in seen:
                q = deque([(x, y)])
                seen.add((x, y))
                comp = []
                while q:
                    cx, cy = q.popleft()
                    comp.append((cx, cy))
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and px[nx, ny][3]:
                                seen.add((nx, ny))
                                q.append((nx, ny))
                comps.append(comp)
    return comps


def edge_runs(edge, min_len=5):
    """날선 픽셀 중 길게 이어진 줄(8연결 덩어리 min_len 이상)만 — 칼집 금(호박 점 1~3개)과 가른다."""
    left, out = set(edge), set()
    while left:
        q = [left.pop()]
        comp = set(q)
        while q:
            x, y = q.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (x + dx, y + dy)
                    if n in left:
                        left.discard(n)
                        comp.add(n)
                        q.append(n)
        if len(comp) >= min_len:
            out |= comp
    return out


def katana_blade(im, tip, refine=False):
    """→ (칼날 픽셀 set, 날선 픽셀 set, 칼끝, 손잡이 끝) 또는 None.
    refine(56라운드 Q55 — 칼끝 기준점이 없고 칼집과 칼날이 한 덩어리로 붙는 뽑기·넣기 시트): 길게 이어진 날선 줄에서 4 도트 안의
    픽셀만 칼날로 본다(칼집 몸통·칼집 금은 제외). 긴 날선 줄이 없으면 None(= 칼집 안 취급)."""
    px = im.load()
    comps = components(im)
    if not comps:
        return None
    if tip is not None:
        tx, ty = tip
        best = min(comps, key=lambda c: min((x - tx) ** 2 + (y - ty) ** 2 for x, y in c))
    else:
        best = max(comps, key=lambda c: sum(1 for x, y in c if px[x, y][:3] in EDGE_COLS))
        if sum(1 for x, y in best if px[x, y][:3] in EDGE_COLS) < 6:
            return None
    pts = set(best)
    edge = {p for p in pts if px[p][:3] in EDGE_COLS}
    if refine:
        edge = edge_runs(edge)
        if not edge:
            return None
        pts = {p for p in pts if any((p[0] - e[0]) ** 2 + (p[1] - e[1]) ** 2 <= 16 for e in edge)}
    # 축: 가장 먼 두 점
    a = max(pts, key=lambda p: (p[0] - 96) ** 2 + (p[1] - 130) ** 2) if tip is None else min(pts, key=lambda p: (p[0] - tip[0]) ** 2 + (p[1] - tip[1]) ** 2)
    b = max(pts, key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2)
    return pts, edge, a, b


def gs_blade(im, grip, tip):
    px = im.load()
    gx, gy = grip
    tx, ty = tip
    ex, ey = tx - gx, ty - gy
    ll = ex * ex + ey * ey or 1.0
    bb = im.getbbox()
    pts = set()
    if not bb:
        return None
    for y in range(bb[1], bb[3]):
        for x in range(bb[0], bb[2]):
            c = px[x, y]
            if not c[3] or c[:3] in LEATHER:
                continue
            u = ((x + 0.5 - gx) * ex + (y + 0.5 - gy) * ey) / ll
            if u < 0.12 or u > 1.04:
                continue
            dx, dy = x + 0.5 - (gx + ex * u), y + 0.5 - (gy + ey * u)
            if dx * dx + dy * dy <= 49:
                pts.add((x, y))
    if len(pts) < 10:
        return None
    return pts


# =============================================================================
# 그리기 조각
# =============================================================================
def top_edge(pts):
    return [p for p in pts if (p[0], p[1] - 1) not in pts]


def flames(L, base_pts, i, seed, hmin, hmax, density, sway=1.2, w=1.3):
    """불꽃 혀: 칼날 윗면 픽셀에서 화면 위로(불은 위로 탄다). 프레임마다 키·흔들림이 바뀜."""
    for (x, y) in base_pts:
        if h2(x, y, seed) > density:
            continue
        hh = hmin + (hmax - hmin) * h2(x, y, seed + i * 3 + 1)
        ph = h2(x, y, seed + 5) * 6.28 + i * 1.7
        pts = []
        n = 6
        for k in range(n + 1):
            u = k / n
            pts.append((x + 0.5 + sway * math.sin(ph + u * 2.6) * u, y + 0.5 - hh * u))
        L.stroke(pts, w, prof=FK.tp_tail(0.9), v=0.8 + 0.2 * h2(x, y, seed + i), vprof=lambda u: 1.0 - 0.8 * u, soft=0.3)


def smoke(L, starts, i, seed, height=14, w=0.8):
    """가는 재 연기 줄: 꼬불꼬불 위로, 프레임마다 위상 이동."""
    for k, (x, y) in enumerate(starts):
        ph = i * 1.1 + k * 2.3
        pts = []
        n = 10
        for m in range(n + 1):
            u = m / n
            pts.append((x + 0.5 + 2.2 * math.sin(ph + u * 4.2) * u, y - 1 - height * u))
        L.stroke(pts, w, prof=lambda u: 0.6 + 0.4 * math.sin(math.pi * min(1, u * 1.4)), v=1.0,
                 vprof=lambda u: 1.0 - 0.6 * u, soft=0.2, dash=(5.0, 0.62, (i * 0.37 + k * 0.5) % 1.0))


def pick(pts, n, seed):
    lst = sorted(pts, key=lambda p: h2(p[0], p[1], seed))
    return lst[:n]


# =============================================================================
# 칼 검기
# =============================================================================
KI_LV = {
    1: dict(edge=rk.S3, body=None, smoke=[rk.S0, rk.S1, rk.S2], flame=None),
    2: dict(edge=rk.A23, body=rk.A21, smoke=None, flame=[rk.A18, rk.A19, rk.A21, rk.A23], fh=(3, 7), dens=0.33),
    3: dict(edge=rk.A25, body=rk.A21, smoke=[rk.S0, rk.S1], flame=[rk.A18, rk.A19, rk.A21, rk.A23, rk.A25], fh=(5, 13), dens=0.5),
}


def ki_frame(im, tip, lv, i, glow, fw, fh, refine=False):
    cfg = KI_LV[lv]
    f = rk.frame(fw, fh)
    blade = katana_blade(im, tip, refine)
    px = im.load()
    if tip is None and blade is not None and not blade[1]:
        blade = None
    sheathed = blade is None
    seed = 11 + lv
    out_recolor = {}
    if sheathed:
        # 칼집 안 — 칼집 금(호박 점)만 달굼 + (1단 연기 / 2·3단 칼집 입구 쪽 작은 불)
        hot = [(x, y) for y in range(fh) for x in range(fw) if px[x, y][3] and px[x, y][:3] in SHEATH_GLOW]
        col = {1: rk.S3, 2: rk.A23, 3: rk.A25}[lv]
        for p in hot:
            out_recolor[p] = col
        if hot:
            if lv == 1:
                Ls = f.L(cfg["smoke"])
                smoke(Ls, pick(hot, 1, seed), i, seed, height=9, w=0.7)
            else:
                Lf = f.L(cfg["flame"])
                flames(Lf, pick(top_edge(set(hot)), 3 if lv == 2 else 5, seed), i, seed, 2, 4 if lv == 2 else 7, 1.0, sway=0.8, w=1.0)
    else:
        pts, edge, a, b = blade
        ax, ay = a[0] - b[0], a[1] - b[1]
        al = (ax * ax + ay * ay) or 1
        tops = [q for q in top_edge(pts) if ((q[0] - b[0]) * ax + (q[1] - b[1]) * ay) / al > 0.22]   # 손잡이·코등이 쪽 제외
        if cfg["flame"]:
            Lf = f.L(cfg["flame"])
            flames(Lf, tops, i, seed, cfg["fh"][0], cfg["fh"][1], cfg["dens"], sway=1.4 if lv == 3 else 1.0,
                   w=1.5 if lv == 3 else 1.2)
        if cfg["smoke"]:
            Ls = f.L(cfg["smoke"])
            if lv == 1:
                smoke(Ls, pick(tops, 2, seed), i, seed, height=18, w=0.6)
            else:
                smoke(Ls, pick(tops, 1, seed + 3), i, seed, height=20, w=0.7)
        # 칼날 색: 날선 = edge, 날선 옆 한 줄 = body (3단은 날 몸 전체)
        near = set()
        for (x, y) in edge:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if (x + dx, y + dy) in pts:
                        near.add((x + dx, y + dy))
        if cfg["body"]:
            for p in near:
                out_recolor[p] = cfg["body"]
        for p in edge:
            out_recolor[p] = cfg["edge"]
        if lv == 3 and glow:                           # 판정 프레임만: 날선 가운데 백열 몇 도트 + 날선 A26
            for p in edge:
                out_recolor[p] = rk.A26
            for p in pick(edge, max(2, len(edge) // 6), seed + i):
                out_recolor[p] = rk.X1
        if lv == 3:                                    # 떨어져 나가 위로 뜨는 불티
            Le = f.L([rk.A19, rk.A21, rk.A23])
            for k, (x, y) in enumerate(pick(tops, 3, seed + 9)):
                yy = y - 9 - ((i * 3 + k * 5) % 9)
                xx = x + int(2 * math.sin(i + k))
                Le.put(xx, yy, 0.8 - 0.25 * k)
        if refine:                                     # 칼집이 같은 덩어리인 칸: 칼집 금은 칼집 안 칸과 같은 단계 색(이어 보이게, 불꽃 없음)
            col = {1: rk.S3, 2: rk.A23, 3: rk.A25}[lv]
            for (x, y) in components_pts(im):
                if (x, y) not in pts and px[x, y][:3] in SHEATH_GLOW:
                    out_recolor[(x, y)] = col
    img = f.render()
    p = img.load()
    for (x, y), c in out_recolor.items():
        p[x, y] = rk.hexrgb(c) + (255,)
    return img


# =============================================================================
# 대검 울분
# =============================================================================
MARKS = [(0.34, -0.25, 50), (0.47, 0.3, -40), (0.58, -0.1, 62), (0.66, 0.35, -55), (0.74, -0.3, 35), (0.82, 0.12, -65),
         (0.9, -0.05, 48)]
GR_LV = {
    1: dict(n=3, ramp=[rk.B0, rk.S2, rk.S3], flame=None),
    2: dict(n=5, ramp=[rk.B0, rk.A17, rk.A18, rk.A19, rk.A21], flame=None, smoke=True),
    3: dict(n=7, ramp=[rk.A17, rk.A19, rk.A21, rk.A23, rk.A25], flame=[rk.A18, rk.A19, rk.A21, rk.A23]),
}


def grudge_frame(im, grip, tip, lv, i, glow, fw, fh):
    cfg = GR_LV[lv]
    f = rk.frame(fw, fh)
    if tip and not grip:                               # 휴대(등에 멘) 시트: 손이 없음 → 칼끝 덩어리의 반대 끝(폼멜)에서 손잡이 길이만큼
        comps = components(im)
        if comps:
            c = min(comps, key=lambda cc: min((x - tip[0]) ** 2 + (y - tip[1]) ** 2 for x, y in cc))
            pm = max(c, key=lambda p: (p[0] - tip[0]) ** 2 + (p[1] - tip[1]) ** 2)
            grip = (pm[0] + (tip[0] - pm[0]) * 0.17, pm[1] + (tip[1] - pm[1]) * 0.17)
    pts = gs_blade(im, grip, tip) if (grip and tip) else None
    if not pts:
        return f.render()
    gx, gy = grip
    tx, ty = tip
    ex, ey = tx - gx, ty - gy
    ln = math.hypot(ex, ey) or 1.0
    ux, uy = ex / ln, ey / ln
    Lm = rk.FK.Layer(f, cfg["ramp"])
    marks = []
    for k, (t, lat, ang) in enumerate(MARKS[:cfg["n"]]):
        cx, cy = gx + ex * t - uy * lat * 4, gy + ey * t + ux * lat * 4
        a = math.atan2(uy, ux) + math.radians(90 + ang * 0.5)
        L = 6.5 + 2.0 * h2(k, 3, lv)
        p0 = (cx - math.cos(a) * L / 2, cy - math.sin(a) * L / 2)
        p1 = (cx + math.cos(a) * L / 2, cy + math.sin(a) * L / 2)
        flick = 1.0 if lv == 1 else 0.82 + 0.18 * h2(k, i, 5 + lv)
        Lm.stroke([p0, p1], 1.45 if lv == 1 else 1.25, prof=FK.tp_both(0.7, 0.5), v=flick, soft=0.7)
        marks.append((cx, cy))
    img_layer = {}
    for (x, y), v in Lm.v.items():                     # 칼날 위로만(자국이 칼 밖으로 나가지 않게)
        if (x, y) in pts:
            img_layer[(x, y)] = v
    Lm.v = img_layer
    f.layers.append(Lm)
    # 이 빠진 자리(어두운 B0 한 점) — 1단부터
    Ln = f.L([rk.B0])
    for k, (cx, cy) in enumerate(marks):
        q = (int(cx + uy * 3), int(cy - ux * 3))
        if q in pts and k % 2 == 0:
            Ln.put(q[0], q[1], 1.0)
    if cfg.get("smoke"):
        Ls = f.L([rk.S0, rk.S1, rk.S2])
        smoke(Ls, [(int(x), int(y)) for x, y in marks[1:4:2]], i, 31, height=10, w=0.7)
    if cfg.get("flame"):
        Lf = f.L(cfg["flame"])
        bases = [(int(x), int(y)) for x, y in marks[::2]]
        flames(Lf, bases, i, 41, 4, 8, 1.0, sway=1.2, w=1.3)
        Le = f.L([rk.A19, rk.A21, rk.A23])
        for k, (x, y) in enumerate(bases[:3]):
            Le.put(x + int(2 * math.sin(i * 1.3 + k)), y - 10 - ((i * 2 + k * 4) % 8), 0.85 - 0.2 * k)
    img = f.render()
    if lv == 3 and glow:                               # 판정 프레임: 자국 한가운데 A26 한 점씩
        p = img.load()
        for cx, cy in marks:
            q = (int(cx), int(cy))
            if q in pts:
                p[q] = rk.hexrgb(rk.A26) + (255,)
    return img


# =============================================================================
# 시트
# =============================================================================
COPY = ("frameWidth", "frameHeight", "frames", "directions", "directionRows", "layout", "frameIndex", "fps", "frameDurationsMs",
        "loop", "pivot", "playerFrameOffset", "anchor", "bodySheet", "dirTransform", "framesBasis", "timingMs", "glowFrames")


def components_pts(im):
    px = im.load()
    bb = im.getbbox()
    if not bb:
        return []
    return [(x, y) for y in range(bb[1], bb[3]) for x in range(bb[0], bb[2]) if px[x, y][3]]


SHEATHED_STATES = ("sheathed", "click")


def tips_of(j, d):
    t = j.get("bladeTipAnchors")
    if isinstance(t, dict):
        return t[d]
    return [None] * j["frames"]


def body_in_overlay_masks(j, sheet, fr):
    """bodyInOverlayFrames(몸이 무기 시트 칸에 함께 그려진 칸 — 공중제비 도약 찍기) → 칸마다 몸 픽셀을 지운 '칼만' 그림.
    마스크는 flipmask.py(build.py flipmask)가 E1 렌더로 다시 그린 칼 층. 없으면 실패(몸까지 달구지 않게)."""
    frames = j.get("bodyInOverlayFrames") or []
    if not frames:
        return {}
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flipmask_%s.png" % sheet)
    assert os.path.exists(path), (sheet, "bodyInOverlayFrames 마스크 없음 — build.py flipmask 먼저")
    mk = Image.open(path).convert("L")
    fw, fh = j["frameWidth"], j["frameHeight"]
    assert mk.size == (fw * j["frames"], fh * len(j["directions"])), (sheet, mk.size)
    out = {}
    for r, d in enumerate(j["directions"]):
        for i in frames:
            m = mk.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh))
            im = fr[d][i].copy()
            im.putalpha(Image.composite(im.getchannel("A"), Image.new("L", im.size, 0), m))
            out[(d, i)] = im
    return out


def job(args):
    kind, sheet = args
    j, fr = rk.load_sheet("weapons/v3/" + sheet)
    fw, fh = j["frameWidth"], j["frameHeight"]
    blade_only = body_in_overlay_masks(j, sheet, fr)
    for (d, i), im in blade_only.items():               # 몸이 든 칸은 칼만 남긴 그림으로 칼날을 찾는다(오버레이는 칼날만 달굼)
        fr[d][i] = im
    glow = set(j.get("glowFrames") or [])
    has_tip = isinstance(j.get("bladeTipAnchors"), dict)
    states = None if has_tip else j.get("frameStates")   # 칼끝 기준점 없는 옛 칼 시트(draw·sheathe·special)만 상태로 칼집 칸을 가름
    refine = bool(states)                                # 휴대 시트(frameStates 없음)는 예전 방식 그대로
    out = []
    for lv in (1, 2, 3):
        frames = {}
        for d in j["directions"]:
            lst = []
            tips = tips_of(j, d)
            grips = (j.get("gripAnchors") or {}).get(d) if kind == "grudge" else None
            for i, im in enumerate(fr[d]):
                if kind == "ki":
                    tip = tips[i] if has_tip else None
                    if has_tip and tip is None:          # 칼끝 null = 칼집 안 → 칼집 금만
                        lst.append(ki_sheathed(im, lv, i, fw, fh))
                    elif states and states[i] in SHEATHED_STATES:   # 칼끝 기준점 없는 뽑기·넣기 시트의 칼집 안 칸(Q55)
                        lst.append(ki_sheathed(im, lv, i, fw, fh))
                    else:
                        lst.append(ki_frame(im, tip, lv, i, i in glow, fw, fh, refine=refine))
                else:
                    lst.append(grudge_frame(im, grips[i] if grips else None, tips[i], lv, i, i in glow, fw, fh))
            frames[d] = lst
        name = "%s_%s%d" % (sheet, "ki" if kind == "ki" else "grudge", lv)
        meta = {k: j[k] for k in COPY if k in j}
        meta.pop("frames", None)
        meta.pop("frameWidth", None)
        meta.pop("frameHeight", None)
        meta.pop("glowFrames", None)
        if blade_only:
            meta.update(bodyInOverlayFrames=sorted(j["bodyInOverlayFrames"]),
                        bodyInOverlayNote="무기 시트의 이 칸들은 몸이 함께 그려져 있다(공중제비). 오버레이는 칼날만 달군다 — 몸 픽셀은 "
                                          "flipmask_%s.png(E1 렌더로 다시 그린 칼 층)로 빼고 칼날을 찾음. 불꽃·불티는 칼날 위로 올라가 몸에 겹칠 수 있음" % sheet)
        meta.update(overlayOf="weapons/v3/" + sheet, level=lv, depth="above_weapon",
                    drawRule="무기 시트 '%s' 를 그린 바로 위에, 같은 프레임 번호(row*frames+col)·같은 시각·같은 피벗(주인공 피벗 + playerFrameOffset)으로 겹친다. "
                             "자원 단계가 바뀌면 같은 프레임 번호로 오버레이만 바꿔 낀다(0단 = 오버레이 없음)" % sheet,
                    weapon=j.get("weapon", sheet.split("_")[0]))
        if kind == "ki":
            meta.update(resource="검기(劍氣)", resourceRef="56라운드 Q14", design={
                1: "1단 재 — 날선이 잿빛(S3)으로 식어 보이고 칼등에서 가는 재 연기 두 줄이 오름",
                2: "2단 호박 — 날선 A23·날선 옆 A21 로 달아오르고 칼등을 따라 작은 호박 불꽃 혀가 흔들림",
                3: "3단 백열 — 날 몸 전체 A23·날선 A25, 칼등 전체에 큰 불꽃이 흔들리고 불티가 떠오름. 백열(X1·A26)은 판정 프레임의 날선만"}[lv],
                sheathNote="칼끝이 null(칼집 안)인 프레임·칼집 휴대 시트는 칼집 금(호박 점)을 단계 색으로 달구고 1단 연기 / 2·3단 작은 불만",
                keyArt="parts/art/work/gemini/weapon_moves/raw_katana_A.jpg 패널 4(sheet_katana 4번)")
        else:
            meta.update(resource="울분(鬱憤)", resourceRef="56라운드 Q15", design={
                1: "1단 재 — 칼 몸에 막은 자국 3개(잿빛 긁힘 + 이 빠진 어두운 점)",
                2: "2단 잔불 — 자국 5개, 자국 가운데가 어두운 호박 잔불(A19~A21)로 깜빡이고 가는 연기",
                3: "3단 불씨 — 자국 7개가 호박(A23~A25)으로 달아오르고 자국 위로 작은 불꽃·불티. 판정 프레임만 자국 가운데 A26 한 점"}[lv],
                keyArt="parts/art/work/gemini/weapon_moves/raw_greatsword_A.jpg 패널 4(sheet_greatsword 4번)",
                stageNote="단계 = 울분 게이지 구간(임시: 1~33% · 34~66% · 67~100%, 시스템 데이터). 차지 내려찍기로 전부 소모하면 오버레이 없음")
        glow_ok = sorted(glow) if (lv == 3) else []
        meta["glowFrames"] = glow_ok
        meta["glowRule"] = ("53라운드 Q65 · 56라운드: 백열 X0/X1·A26 은 3단의 판정 프레임(무기 시트 glowFrames)만. 그 밖은 A25 이하 — 빌드 검사 통과")
        rk.write_sheet(name, rk.OUT_W, j["directions"], frames, j["frameDurationsMs"], meta, glow=glow_ok,
                       loop=j.get("loop", False), edge_ok=True)
        out.append(name)
    return out


def ki_sheathed(im, lv, i, fw, fh):
    """칼집 안 프레임 — 칼집 금(호박 점)만 달굼."""
    cfg = KI_LV[lv]
    px = im.load()
    f = rk.frame(fw, fh)
    hot = [(x, y) for y in range(fh) for x in range(fw) if px[x, y][3] and px[x, y][:3] in SHEATH_GLOW]
    if hot:
        if lv == 1:
            smoke(f.L(cfg["smoke"]), pick(hot, 1, 12), i, 12, height=9, w=0.7)
        else:
            flames(f.L(cfg["flame"]), pick(top_edge(set(hot)), 3 if lv == 2 else 5, 13), i, 13, 2, 4 if lv == 2 else 7, 1.0,
                   sway=0.8, w=1.0)
    img = f.render()
    p = img.load()
    col = {1: rk.S3, 2: rk.A23, 3: rk.A25}[lv]
    for q in hot:
        p[q] = rk.hexrgb(col) + (255,)
    return img


def build(only=None, procs=6):
    jobs = [("ki", s) for s in KATANA_SHEETS] + [("grudge", s) for s in GS_SHEETS]
    if only:
        jobs = [jb for jb in jobs if jb[1] in only or jb[0] in only]
    with Pool(procs) as p:
        res = p.map(job, jobs, chunksize=1)
    return [n for r in res for n in r]


if __name__ == "__main__":
    print("\n".join(build(set(sys.argv[1:]) or None)))
