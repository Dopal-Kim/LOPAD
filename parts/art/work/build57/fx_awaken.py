"""최종 각성 4종(설계안 3.4 · 6.2 '무기 변형 4 · 시그니처 fx 4') — 칼 만월 · 대검 산붕 · 단검 백귀 · 활 유성.

무기 외형 변형 = 오버레이 시트 weapons/v3/<무기 시트>_awaken (56 Q14·Q15 검기·울분 오버레이와 같은 방식):
  무기 시트를 그린 바로 위(above_weapon)에 같은 프레임 번호·같은 시각·같은 피벗으로 겹친다. 무기 칸의 색을 덮어 바꾸고(색 변형),
  칼 밖으로 나가는 그림(만월 달빛 칼끝 연장·산붕 바위 등날·백귀 혼령 연기·유성 별똥 불티)을 더한다(형태 변형).
  검기·울분 오버레이가 있으면 그 위에(순서: 무기 → _awaken → _ki/_grudge).
시그니처 fx: katana_fullmoon · greatsword_landslide · dagger_hundred_ghosts · bow_meteor_arrow
"""
import math
import os
import random
import sys

from PIL import Image

import kit as K
from kit import W, FK, BR

sys.path.insert(0, os.path.join(K.WORK, "combo56_res"))
import overlay as OV  # noqa: E402  (칼날·대검 날 찾기 — 읽기만)

SRC = "parts/art/work/build57/build.py awaken (57라운드 최종 각성 — 무기 변형 오버레이 · 시그니처 fx)"

KATANA = [s for s in OV.KATANA_SHEETS] + ["katana_spin", "katana_guardbreak", "katana_thrust", "katana_issen_dash"]
GREAT = [s for s in OV.GS_SHEETS if s not in ("greatsword_charge_slam", "greatsword_charge_plunge")] + ["greatsword_charge_swing"]
DAGGER = ["dagger_carry_idle", "dagger_carry_walk", "dagger_carry_run", "dagger_carry_dash", "dagger_combo1", "dagger_combo2", "dagger_combo3",
          "dagger_backstab", "dagger_flurry", "dagger_special", "dagger_fan_throw"]
BOW = ["bow_carry_idle", "bow_carry_walk", "bow_carry_run", "bow_carry_dash", "bow_draw_hold", "bow_release", "bow_arrow_rain", "bow_rapid_loop",
       "bow_reload"]
SHEETS = [("katana", s) for s in KATANA] + [("greatsword", s) for s in GREAT] + [("dagger", s) for s in DAGGER] + [("bow", s) for s in BOW]


def h(*a):
    return OV.h2(*a)


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def outline_pts(pts):
    return {p for p in pts if any((p[0] + dx, p[1] + dy) not in pts for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def seg_mask(im, a, b, rad=7.0, umin=-0.05, umax=1.08):
    px = im.load()
    bb = im.getbbox()
    if not bb or a is None or b is None:
        return set()
    ex, ey = b[0] - a[0], b[1] - a[1]
    ll = ex * ex + ey * ey or 1.0
    out = set()
    for y in range(bb[1], bb[3]):
        for x in range(bb[0], bb[2]):
            if not px[x, y][3]:
                continue
            u = ((x + 0.5 - a[0]) * ex + (y + 0.5 - a[1]) * ey) / ll
            if u < umin or u > umax:
                continue
            dx, dy = x + 0.5 - (a[0] + ex * u), y + 0.5 - (a[1] + ey * u)
            if dx * dx + dy * dy <= rad * rad:
                out.add((x, y))
    return out


def all_pts(im):
    px = im.load()
    bb = im.getbbox()
    if not bb:
        return set()
    return {(x, y) for y in range(bb[1], bb[3]) for x in range(bb[0], bb[2]) if px[x, y][3]}


# =============================================================================
# 만월 — 칼날이 달빛 은재로, 날선 호박→A25, 칼끝 너머 달빛 연장, 떠오르는 달빛 조각
# =============================================================================
def moon_frame(im, tip, i, glow, refine, sheathed_state):
    fw, fh = im.size
    f = K.frame(fw, fh)
    px = im.load()
    rec = {}
    blade = None if sheathed_state else OV.katana_blade(im, tip, refine)
    if blade is None or (tip is None and not blade[1]):
        hot = [(x, y) for y in range(fh) for x in range(fw) if px[x, y][3] and px[x, y][:3] in OV.SHEATH_GLOW]
        for p in hot:
            rec[p] = K.S3 if (p[0] + p[1] + i) % 3 else K.A25
        if hot:
            x, y = hot[len(hot) // 2]
            Lg = f.L([K.S2, K.S3, K.A25])
            K.crescent(Lg, x, y - 6, 3.5, 2.0, 1.4, v=0.9, ang=-math.pi / 2)
    else:
        pts, edge, a, b = blade
        for p in pts:
            c = px[p][:3]
            L_ = lum(c)
            rec[p] = K.S1 if L_ < 40 else K.S2 if L_ < 70 else K.S3
        near = {(x + dx, y + dy) for (x, y) in edge for dx in (-1, 0, 1) for dy in (-1, 0, 1)} & pts
        for p in near:
            rec[p] = K.S3
        for p in edge:
            rec[p] = K.A26 if glow else K.A25
        if glow:
            for p in OV.pick(edge, max(2, len(edge) // 7), 31 + i):
                rec[p] = K.X1
        # 칼끝 너머 달빛 연장(가는 반투명 없는 선 — 형태 변형)
        ax, ay = a[0] - b[0], a[1] - b[1]
        ln = math.hypot(ax, ay) or 1.0
        ux, uy = ax / ln, ay / ln
        Lx = f.L([K.S2, K.S3, K.A23, K.A25])
        ext = 12 + 2 * math.sin(i * 1.3)
        Lx.stroke([(a[0] + 0.5 + ux * 1, a[1] + 0.5 + uy * 1), (a[0] + 0.5 + ux * ext, a[1] + 0.5 + uy * ext)], 0.9, prof=FK.tp_tail(0.8), v=0.95)
        # 칼등 쪽 가는 초승 호(달무리)
        nx, ny = -uy, ux
        mid = (b[0] + ax * 0.62, b[1] + ay * 0.62)
        Lm = f.L([K.S1, K.S2, K.S3])
        arc = [(mid[0] + ux * ln * 0.32 * math.cos(t_) + nx * 5 * math.sin(t_) + nx * 3, mid[1] + uy * ln * 0.32 * math.cos(t_) + ny * 5 * math.sin(t_) + ny * 3)
               for t_ in [math.pi * (0.1 + 0.8 * m / 16) for m in range(17)]]
        Lm.stroke(arc, 0.6, prof=FK.tp_both(0.6, 0.5), v=0.9, dash=(7, 0.7, (i * 0.17) % 1))
        # 떠오르는 달빛 조각
        Lf = f.L([K.S2, K.S3, K.A25])
        tops = OV.top_edge(pts)
        for k, (x, y) in enumerate(OV.pick(tops, 3, 41)):
            yy = y - 5 - ((i * 3 + k * 5) % 10)
            Lf.put(x + int(2 * math.sin(i + k)), yy, 0.9 - 0.2 * k)
    img = f.render()
    p = img.load()
    for (x, y), c in rec.items():
        p[x, y] = FK.hexrgb(c) + (255,)
    return img


# =============================================================================
# 산붕 — 대검 날이 바위로, 용암 금 3줄, 등날에 바위 조각(형태), 떨어지는 돌
# =============================================================================
def rock_frame(im, grip, tip, i, glow):
    fw, fh = im.size
    f = K.frame(fw, fh)
    if tip and not grip:
        comps = OV.components(im)
        if comps:
            c = min(comps, key=lambda cc: min((x - tip[0]) ** 2 + (y - tip[1]) ** 2 for x, y in cc))
            pm = max(c, key=lambda p: (p[0] - tip[0]) ** 2 + (p[1] - tip[1]) ** 2)
            grip = (pm[0] + (tip[0] - pm[0]) * 0.17, pm[1] + (tip[1] - pm[1]) * 0.17)
    pts = OV.gs_blade(im, grip, tip) if (grip and tip) else None
    if not pts:
        return f.render()
    px = im.load()
    rec = {}
    for p in pts:
        L_ = lum(px[p][:3])
        rec[p] = K.B1 if L_ < 45 else K.S0 if L_ < 75 else K.S1 if L_ < 110 else K.S2 if L_ < 140 else K.S3
    for p in outline_pts(pts):
        rec[p] = K.B0
    gx, gy = grip
    tx, ty = tip
    ex, ey = tx - gx, ty - gy
    ln = math.hypot(ex, ey) or 1.0
    ux, uy = ex / ln, ey / ln
    nx, ny = -uy, ux
    # 용암 금 3줄(날 위로만)
    Lv = K.FK.Layer(f, [K.A19, K.A21, K.A23] + ([K.A25, K.A26] if glow else []))
    r = random.Random(77)
    for j, (u0, u1, off) in enumerate(((0.2, 0.55, -1.5), (0.45, 0.85, 1.8), (0.7, 0.98, -0.6))):
        a = (gx + ex * u0 + nx * off, gy + ey * u0 + ny * off)
        b = (gx + ex * u1 + nx * off * 0.5, gy + ey * u1 + ny * off * 0.5)
        Lv.stroke(W.jag(r, a, b, n=5, amp=1.4), 0.3, prof=FK.tp_both(0.5, 0.5), v=0.75 + 0.25 * (0.5 + 0.5 * math.sin(i * 1.4 + j * 2)))
    Lv.v = {k: v for k, v in Lv.v.items() if k in pts}
    f.layers.append(Lv)
    # 등날 바위 조각(칼 바깥, 한쪽) — 형태 변형
    Lr = f.L([K.B0, K.B1, K.S0, K.S1, K.S2, K.S3])
    side = 1 if h(int(gx), int(gy), 3) > 0.5 else -1
    for j, u in enumerate((0.3, 0.46, 0.62, 0.78)):
        bx, by = gx + ex * u + nx * side * 4.5, gy + ey * u + ny * side * 4.5
        hgt = 8.0 + 3.0 * h(j, 9, 1)
        apex = (bx + nx * side * hgt + ux * 2.0, by + ny * side * hgt + uy * 2.0)
        base0 = (bx - ux * 4.5 - nx * side * 2, by - uy * 4.5 - ny * side * 2)
        base1 = (bx + ux * 4.5 - nx * side * 2, by + uy * 4.5 - ny * side * 2)
        _tri(Lr, base0, base1, apex, lit=(nx * side, ny * side))
    # 떨어지는 돌가루
    Lf = f.L(K.FLAKE_G)
    for k, (x, y) in enumerate(OV.pick(list(pts), 3, 5)):
        yy = y + 4 + ((i * 4 + k * 7) % 14)
        Lf.put(x + k - 1, yy, 0.85)
    img = f.render()
    p = img.load()
    for (x, y), c in rec.items():
        if p[x, y][3] == 0:
            p[x, y] = FK.hexrgb(c) + (255,)
    return img


def _tri(L, a, b, c, lit=None):
    """바위 조각(삼각): a·b = 밑변, c = 꼭짓점. 축(밑변 가운데 → 꼭짓점) 왼쪽 = 빛 받는 면(밝음·위로 갈수록 밝게), 오른쪽 = 그늘, 테 = 어둠."""
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    ax_, ay_ = c[0] - mx, c[1] - my
    alen = math.hypot(ax_, ay_) or 1.0
    xs = [a[0], b[0], c[0]]
    ys = [a[1], b[1], c[1]]
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            px_, py_ = x + 0.5, y + 0.5
            s = []
            for p, q in ((a, b), (b, c), (c, a)):
                s.append(((q[0] - p[0]) * (py_ - p[1]) - (q[1] - p[1]) * (px_ - p[0])) / (math.hypot(q[0] - p[0], q[1] - p[1]) or 1))
            if all(v >= 0 for v in s) or all(v <= 0 for v in s):
                if min(abs(v) for v in s) < 1.0:
                    L.put(x, y, 0.1)
                    continue
                side = ax_ * (py_ - my) - ay_ * (px_ - mx)
                up = ((px_ - mx) * ax_ + (py_ - my) * ay_) / (alen * alen)
                if side < 0:
                    v = 0.62 + 0.3 * up + (0.08 if (x + y) % 2 else 0)
                else:
                    v = 0.35 + 0.12 * up
                L.put(x, y, min(0.99, v))


# =============================================================================
# 백귀 — 단검 날이 그림자 재로, 날선만 호박, 날에서 피어오르는 혼령 연기(눈 두 점)
# =============================================================================
def ghost_frame(im, grip, tip, i, glow):
    fw, fh = im.size
    f = K.frame(fw, fh)
    pts = seg_mask(im, grip, tip, rad=5.5, umin=0.25) if (grip and tip) else set()
    if len(pts) < 6:
        return f.render()
    px = im.load()
    rec = {}
    for p in pts:
        c = px[p][:3]
        if c in OV.EDGE_COLS:
            rec[p] = K.A26 if glow else K.A23
        else:
            L_ = lum(c)
            rec[p] = K.K1 if L_ < 40 else K.K2 if L_ < 70 else K.S0
    Ls = f.L([K.S0, K.S1, K.S2])
    Le = f.L([K.A21, K.A23])
    tops = OV.top_edge(pts)
    for k, (x, y) in enumerate(OV.pick(tops, 2, 51)):
        ph = i * 0.9 + k * 2.4
        n = 9
        hh = 12 + 4 * k
        pts_ = [(x + 0.5 + 3.2 * math.sin(ph + u * 3.6) * u, y - hh * u) for u in [m / n for m in range(n + 1)]]
        Ls.stroke(pts_, 1.3, prof=lambda u: 0.45 + 0.55 * math.sin(math.pi * min(1.0, 0.25 + u)), v=0.95, vprof=lambda u: 1 - 0.4 * u)
        hx, hy = pts_[-1]
        Ls.stamp(hx, hy - 1, 2.0, 0.9, soft=0.3)          # 혼령 머리
        if (i + k) % 4 != 3:                              # 깜빡이는 눈
            Le.put(hx - 1, hy - 1, 1.0)
            Le.put(hx + 1, hy - 1, 1.0)
    img = f.render()
    p = img.load()
    for (x, y), c in rec.items():
        p[x, y] = FK.hexrgb(c) + (255,)
    return img


# =============================================================================
# 유성 — 활대 테두리가 호박 별빛, 양 끝에 별 반짝임, 활대를 따라 도는 별똥 불티
# =============================================================================
def star_frame(im, grip, i, glow):
    fw, fh = im.size
    f = K.frame(fw, fh)
    pts = all_pts(im)
    if len(pts) < 8 or grip is None:
        return f.render()
    px = im.load()
    rec = {}
    gx, gy = grip
    far = sorted(pts, key=lambda p: (p[0] - gx) ** 2 + (p[1] - gy) ** 2, reverse=True)
    p1 = far[0]
    a1 = math.atan2(p1[1] - gy, p1[0] - gx)
    p2 = next((p for p in far if abs(((math.atan2(p[1] - gy, p[0] - gx) - a1 + math.pi) % (2 * math.pi)) - math.pi) > 1.9), None)
    ol = outline_pts(pts)
    for p in ol:
        c = px[p][:3]
        if lum(c) < 90 and h(p[0], p[1], 7) < 0.45:
            rec[p] = K.A21
    for p in pts:
        c = px[p][:3]
        if c in OV.EDGE_COLS:
            rec[p] = K.A25
    Ls = f.L([K.A19, K.A21, K.A23, K.A25] + ([K.A26] if glow else []))
    for k, q in enumerate((p1, p2)):
        if q is None:
            continue
        sz = 3.5 + 1.5 * math.sin(i * 1.7 + k * 2.0)
        Ls.star4(q[0] + 0.5, q[1] + 0.5, sz, w=0.55, v=1.0 if glow else 0.92, diag=0.45 if (i + k) % 2 else 0)
    # 활대를 따라 도는 별똥 불티 1개(바깥 테두리 점 순서대로)
    olist = sorted(ol, key=lambda p: math.atan2(p[1] - gy, p[0] - gx))
    if olist:
        q = olist[(i * 7) % len(olist)]
        q2 = olist[(i * 7 - 3) % len(olist)]
        Ls.stroke([(q2[0] + 0.5, q2[1] + 0.5), (q[0] + 0.5, q[1] + 0.5)], 0.7, prof=FK.tp_head(0.8), v=0.95)
    img = f.render()
    p = img.load()
    for (x, y), c in rec.items():
        if p[x, y][3] == 0:
            p[x, y] = FK.hexrgb(c) + (255,)
    return img


# =============================================================================
DESIGN = {
    "katana": ("만월(滿月)", "칼날이 달빛 은재(S1~S3)로 바뀌고 날선은 A25, 칼끝 너머로 12 도트 달빛 연장 선 + 칼등 쪽 점선 달무리 호 + 떠오르는 달빛 조각. "
               "칼집 안 칸은 칼집 금이 은재·호박으로, 칼집 위 작은 초승달"),
    "greatsword": ("산붕(山崩)", "대검 날이 바위(흙 B1~B3·재 S2, 테 B0)로 바뀌고 용암 금 3줄이 맥박, 등날 한쪽에 바위 조각 4개가 솟음(형태) + 떨어지는 돌가루"),
    "dagger": ("백귀(百鬼)", "단검 날이 그림자 재(K1~S0)로 어두워지고 날선만 호박, 날에서 혼령 연기 두 가닥이 피어올라 머리에 깜빡이는 호박 눈 두 점"),
    "bow": ("유성(流星)", "활대 테두리 곳곳이 호박 별빛(A21), 시위·날선 A25, 활대 양 끝에 반짝이는 네 갈래 별 + 활대를 따라 도는 별똥 불티"),
}


def overlay_job(arg):
    weapon, sheet = arg
    j, fr = K.grid_frames("weapons/v3/" + sheet)
    fw, fh = j["frameWidth"], j["frameHeight"]
    note = None
    try:
        blade_only = OV.body_in_overlay_masks(j, sheet, fr)
    except AssertionError as e:                 # 58 재렌더로 마스크 크기가 맞지 않음 → 그 칸은 비움
        blade_only = {}
        note = "bodyInOverlayFrames 마스크(combo56_res/flipmask_*) 크기 불일치 — 몸이 든 칸은 오버레이 비움(%s)" % (e,)
    skip = set(j.get("bodyInOverlayFrames") or []) if (note and j.get("bodyInOverlayFrames")) else set()
    for (d, i), im in blade_only.items():
        fr[d][i] = im
    glow = set(j.get("glowFrames") or [])
    tips = j.get("bladeTipAnchors") if isinstance(j.get("bladeTipAnchors"), dict) else None
    grips = j.get("gripAnchors") if isinstance(j.get("gripAnchors"), dict) else None
    states = None if tips else j.get("frameStates")
    frames = {}
    for d in j["directions"]:
        lst = []
        for i, im in enumerate(fr[d]):
            tip = tips[d][i] if tips else None
            grip = grips[d][i] if grips and grips.get(d) else None
            g = i in glow
            if i in skip:
                lst.append(Image.new("RGBA", im.size, (0, 0, 0, 0)))
            elif weapon == "katana":
                sh = (tips is not None and tip is None) or bool(states and states[i] in OV.SHEATHED_STATES)
                lst.append(moon_frame(im, tip, i, g, bool(states), sh))
            elif weapon == "greatsword":
                lst.append(rock_frame(im, grip, tip, i, g))
            elif weapon == "dagger":
                if grip is None and tip is not None:
                    comps = OV.components(im)
                    c = min(comps, key=lambda cc: min((x - tip[0]) ** 2 + (y - tip[1]) ** 2 for x, y in cc)) if comps else None
                    grip = max(c, key=lambda p: (p[0] - tip[0]) ** 2 + (p[1] - tip[1]) ** 2) if c else None
                lst.append(ghost_frame(im, grip, tip, i, g))
            else:
                if grip is None:
                    bb = im.getbbox()
                    grip = ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2) if bb else None
                lst.append(star_frame(im, grip, i, g))
        frames[d] = lst
    name, design = sheet + "_awaken", DESIGN[weapon]
    meta = {k: j[k] for k in OV.COPY if k in j}
    for k in ("frames", "frameWidth", "frameHeight", "glowFrames"):
        meta.pop(k, None)
    meta.update(overlayOf="weapons/v3/" + sheet, depth="above_weapon", weapon=weapon, awakening=design[0], design=design[1],
                drawRule="무기 시트 '%s' 를 그린 바로 위에 같은 프레임 번호(row*atlas.grid.columns+col)·같은 시각·같은 피벗(주인공 피벗 + playerFrameOffset)으로 겹친다. "
                         "각성한 런에서만. 검기·울분 오버레이가 있으면 그 위(무기 → _awaken → _ki/_grudge)" % sheet,
                r57="57라운드 Q22~Q37 최종 각성(설계안 3.4 A안 — 무기당 1종, 무기 외형 변형) · 1층 단계는 무기 시험장에서만",
                glowFrames=sorted(glow), glowRule="백열(X1·A26)은 무기 시트 glowFrames(판정 순간)만 — 그 밖 A25 이하, 빌드 검사 통과")
    if note:
        meta["bodyInOverlayNote"] = note
    K.rk.SRC = SRC
    K.rk.write_sheet(name, K.OUT_W, j["directions"], frames, j["frameDurationsMs"], meta, glow=sorted(glow), loop=j.get("loop", False), edge_ok=True)
    return name


# =============================================================================
# 시그니처 fx
# =============================================================================
FM_MS = [40, 40, 50, 60, 70, 80, 90, 100, 110, 120]


def fullmoon(seed=6101):
    cx, cy = K.PV[0], K.PV[1] - 64
    R = 104
    out = []
    slashes = [(-35, 0.0), (20, 6.0), (-5, -5.0)]
    for i in range(len(FM_MS)):
        fr = K.frame()
        Lf = fr.L(K.FLAKE)
        Lm = fr.L([K.S1, K.S2, K.S3, K.A23, K.A25])
        Lb = fr.L(K.INK_K)
        Lh = fr.L(K.HOT)
        Lp = fr.L([K.S2, K.S3, K.A25])
        grow = [0.35, 0.75, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0][i]
        k = 0.0 if i <= 4 else (i - 4) / 5
        rr = R * grow
        # 달 — 열린 붓 원(위 왼쪽에 틈) + 안쪽 점선 달무리
        pts = [(cx + math.cos(math.radians(a)) * rr, cy + math.sin(math.radians(a)) * rr) for a in range(-110, 225, 3)]
        S = BR.Stroke(pts, 8.0, seed=seed, peak=0.5, dry_from=0.75, split=1.6, drops=4, start_w=0.2, end_w=0.5)
        if i <= 4:
            S.draw(Lm, head=1.0 if i else 0.5, vmax=0.95, drops=False)
        else:
            S.draw(Lm, head=1.0, tail=0.1 + 0.7 * k, vmax=0.9 - 0.3 * k, k=k, fall=8 * k)
            S.flakes(Lf, k, 0.0, 0.1 + 0.7 * k, 10, size=1.7, fall=14, seed=i)
        if i >= 1 and i <= 7:
            Lp.arc(cx, cy, rr * 0.78, rr * 0.78, 0, 2 * math.pi, 0.6, v=0.75 - 0.08 * i, dash=(18, 0.45, i * 0.05))
            for m in range(5):                                   # 달 표면 점(바다)
                a = 1.3 * m + 0.4
                Lp.stamp(cx + math.cos(a) * rr * 0.4, cy + math.sin(a) * rr * 0.32, 2.2 - 0.3 * m, 0.6, soft=0.3)
        # 연속 일섬 세 줄(달을 가로지름)
        for j, (ang, off) in enumerate(slashes):
            fj = 1 + j
            if i < fj:
                continue
            a = math.radians(ang)
            ln = R * 1.25
            p0 = (cx - math.cos(a) * ln + off, cy - math.sin(a) * ln * 0.6 + off)
            p1 = (cx + math.cos(a) * ln + off, cy + math.sin(a) * ln * 0.6 + off)
            Sl = BR.Stroke(K.line_pts(p0, p1, 30, bend=3), 5.0, seed=seed + 7 + j, peak=0.45, dry_from=0.7, split=1.6, drops=4, start_w=0.1, end_w=0.4)
            age = i - fj
            if age == 0:
                Sl.draw(Lb, head=1.0, vmax=0.95, hot=(i in (1, 2)), Lhot=Lh)
            else:
                kk = min(1.0, age / 6)
                Sl.draw(Lb, head=1.0, tail=0.1 + 0.8 * kk, vmax=0.85 - 0.3 * kk, k=kk, fall=6 * kk)
        if i == 2:
            Lh.star4(cx, cy, 12, w=0.9, v=1.0, diag=0.5)
        out.append(fr.render())
    return out


LS_MS = [30, 30, 30, 40, 50, 60, 80, 100, 120, 140]
DIRS8 = ["down", "up", "left", "right", "down-right", "down-left", "up-right", "up-left"]


def landslide(d, seed=6111):
    """바위 가시가 조준 방향(바닥 타원)으로 4칸 차례로 솟았다 무너짐 — 가시는 늘 화면 위로(8방향 직접 그림)."""
    ang = K.DIR_ANG[d]
    cx, cy = K.PV
    r = random.Random(seed)
    spikes = []
    for j in range(9):
        dist = 28 + 28 * j + r.uniform(-6, 6)
        lat = r.uniform(-14, 14)
        x = cx + math.cos(math.radians(ang)) * dist - math.sin(math.radians(ang)) * lat
        y = cy + (math.sin(math.radians(ang)) * dist + math.cos(math.radians(ang)) * lat) * K.KY
        spikes.append((x, y, r.uniform(48, 80) * (1.2 if j in (3, 6, 8) else 1.0), r.uniform(15, 22), j // 3, r.uniform(-0.22, 0.22)))
    spikes.sort(key=lambda s: s[1])            # 뒤(위)부터 그림
    out = []
    for i in range(len(LS_MS)):
        fr = K.frame()
        Ld = fr.L(W.R_DUST)
        Lgr = fr.L([K.B0, K.B1, K.B2])
        Lc = fr.L([K.A18, K.A19, K.A21, K.A23])
        Lf = fr.L(K.FLAKE_G)
        Lh = fr.L(K.HOT)
        rocks = []
        for (x, y, hgt, wd, grp, lean) in spikes:
            age = i - grp
            if age < 0:
                continue
            g = [0.55, 1.0, 1.0, 0.95, 0.85, 0.7, 0.45, 0.25, 0.1, 0.0][min(9, age)] if i < 7 else max(0.0, 0.6 - 0.2 * (i - 6))
            if g <= 0.05:
                continue
            hh = hgt * g
            Lgr.disc(x, y, wd * 0.9, wd * 0.35, v=0.8, edge=0.5)
            rocks.append((x, y, hh, wd, lean, age))
            if age == 0:
                Ld.cloud(x, y - 4, 8, v=0.65, flat=0.5, seed=int(x))
        for x, y, hh, wd, lean, age in rocks:
            fr2 = fr.L([K.B0, K.B2, K.B3, K.S2, K.S3])
            apex = (x + lean * hh, y - hh)
            _tri(fr2, (x - wd * 0.5, y), (x + wd * 0.5, y), apex, lit=(-0.7, -0.7))
            Lc.stroke(W.jag(random.Random(int(x)), (x + 0.5, y - 2), (x + lean * hh * 0.75, y - hh * 0.75), n=4, amp=1.6), 0.9, v=0.95 if age < 3 else 0.7)
        # 바닥 금(출발점 → 4칸)
        ex = cx + math.cos(math.radians(ang)) * 4 * K.TILE
        ey = cy + math.sin(math.radians(ang)) * 4 * K.TILE * K.KY
        main = W.jag(random.Random(seed), (cx, cy), (ex, ey), n=10, amp=3)
        lim = min(1.0, (i + 1) / 4)
        mp = main[:max(2, int(len(main) * lim))]
        kk = max(0.0, (i - 5) / 4)
        Lgr.stroke(mp, 2.4, prof=FK.tp_both(0.4, 0.5), v=0.8 - 0.3 * kk)
        Lc.stroke(mp, 0.9, prof=FK.tp_both(0.5, 0.5), v=0.95 - 0.5 * kk)
        if i == 0:
            Lh.stamp(cx, cy - 2, 2.0, 1.0, soft=0.5)
        if i >= 5:
            rr = random.Random(seed + i)
            for m in range(10):
                s = rr.choice(spikes)
                W.flake(Lf, s[0] + rr.uniform(-8, 8), s[1] - rr.uniform(0, 20) + 4 * (i - 5), rr.uniform(1.6, 2.8), m, v=0.85)
        out.append(fr.render())
    return out


HG_MS = [40, 40, 40, 30, 50, 60, 70, 90, 110]


def _wisp(Lb, Le, x, y, dirx, diry, scale, v, blink=True):
    """혼령: 둥근 머리 + 뒤로 흐르는 꼬리(재) + 호박 눈 두 점."""
    tail = [(x - dirx * 26 * scale * u + 3 * math.sin(u * 6) * diry, y - diry * 26 * scale * u - 3 * math.sin(u * 6) * dirx) for u in [m / 10 for m in range(11)]]
    Lb.stroke(tail, 4.2 * scale, prof=FK.tp_tail(0.7), v=v)
    Lb.stamp(x, y, 5.5 * scale, v, soft=0.35)
    if blink:
        Le.put(x - 2 * scale, y - 1, 1.0)
        Le.put(x + 2 * scale, y - 1, 1.0)


def hundred_ghosts(seed=6121):
    cx, cy = 110, 120
    out = []
    starts_ = [(-140.0, 1.0), (-20.0, 0.9), (100.0, 1.1)]
    for i in range(len(HG_MS)):
        fr = K.frame(220, 240)
        Lf = fr.L([K.K2, K.S0, K.S1, K.S2])
        Lb = fr.L([K.K1, K.K2, K.S0, K.S1])
        Le = fr.L([K.A21, K.A23])
        Li = fr.L(K.INK_K)
        Lh = fr.L(K.HOT)
        for j, (a, sc) in enumerate(starts_):
            ar = math.radians(a)
            if i <= 3:
                dist = [96, 62, 30, 10][i]
                x, y = cx + math.cos(ar) * dist, cy + math.sin(ar) * dist * 0.8
                _wisp(Lb, Le, x, y, -math.cos(ar), -math.sin(ar), sc, 0.95)
            elif i <= 5:
                dist = 10 + 26 * (i - 3)
                x, y = cx - math.cos(ar) * dist, cy - math.sin(ar) * dist * 0.8
                _wisp(Lb, Le, x, y, -math.cos(ar), -math.sin(ar), sc * (1 - 0.15 * (i - 3)), 0.8, blink=(i == 4))
        if i >= 3:                                         # 세 갈래 베기(중심 교차)
            k = (i - 3) / 5
            for j, (a, sc) in enumerate(starts_):
                ar = math.radians(a + 90)
                p0 = (cx - math.cos(ar) * 40, cy - math.sin(ar) * 40)
                p1 = (cx + math.cos(ar) * 40, cy + math.sin(ar) * 40)
                S = BR.Stroke(K.line_pts(p0, p1, 20, bend=4), 4.5, seed=seed + j, peak=0.45, dry_from=0.65, split=1.5, drops=3, start_w=0.1, end_w=0.4)
                if i == 3:
                    S.draw(Li, head=1.0, vmax=0.95, hot=True, Lhot=Lh)
                else:
                    S.draw(Li, head=1.0, tail=0.1 + 0.8 * k, vmax=0.85 - 0.3 * k, k=k, fall=6 * k)
            if i == 3:
                Lh.star4(cx, cy, 10, w=0.8, v=1.0, diag=0.5)
            r = random.Random(seed + i)
            for m in range(12):
                aa = r.uniform(0, 6.28)
                dd = 20 + 50 * k * r.uniform(0.5, 1.2)
                W.flake(Lf, cx + math.cos(aa) * dd, cy + math.sin(aa) * dd * 0.8 + 10 * k, r.uniform(1.3, 2.4), aa, v=0.85 - 0.3 * k)
        out.append(fr.render())
    return out


MA_MS = [40, 40, 40, 30, 50, 60, 80, 100, 120]


def meteor(seed=6131):
    cx, cy = 150, 300
    sx, sy = cx - 110, cy - 270
    out = []
    for i in range(len(MA_MS)):
        fr = K.frame(300, 340)
        Ld = fr.L(W.R_DUST)
        Lgr = fr.L([K.B0, K.B1, K.B2])
        Lt = fr.L([K.S0, K.S1, K.A17, K.A18, K.A19])
        Lf = fr.L([K.A19, K.A21, K.A23, K.A25])
        Le = fr.L(K.EMB_HI)
        Lfl = fr.L(K.FLAKE)
        Lh = fr.L(K.HOT)
        if i <= 2:
            u = [0.35, 0.7, 1.0][i]
            hx, hy = sx + (cx - sx) * u, sy + (cy - sy) * u
            tl = 130
            dx, dy = (cx - sx), (cy - sy)
            ln = math.hypot(dx, dy)
            ux, uy = dx / ln, dy / ln
            Lt.stroke([(hx - ux * tl, hy - uy * tl), (hx, hy)], 5.0, prof=FK.tp_head(0.7), v=0.95, vprof=lambda t: 0.4 + 0.6 * t)
            Lf.stroke([(hx - ux * tl * 0.5, hy - uy * tl * 0.5), (hx, hy)], 2.6, prof=FK.tp_head(0.6), v=1.0)
            Lf.stamp(hx, hy, 4.0, 1.0, soft=0.3)
            Lh.stroke([(hx - ux * 6, hy - uy * 6), (hx + ux * 2, hy + uy * 2)], 0.8, v=1.0) if i == 2 else None
            r = random.Random(seed + i)
            for m in range(6):
                t_ = r.uniform(0.1, 0.9)
                W.ember(Le, hx - ux * tl * t_ + r.uniform(-5, 5), hy - uy * tl * t_ + r.uniform(-5, 5), ux, uy, 3.0, w=0.6, v=0.85)
        else:
            k = (i - 3) / 5
            rr = 30 + 50 * min(1.0, k * 2.5)
            Lgr.disc(cx, cy, 22, 9, v=0.85 - 0.3 * k, edge=0.5)
            if i == 3:
                Lh.star4(cx, cy - 6, 18, w=1.1, v=1.0, diag=0.5)
                Lf.ring(cx, cy, 26, 1.2, ry=11, v=1.0)
            else:
                Lf.arc(cx, cy, rr, rr * 0.42, 0, 2 * math.pi, 1.3 * (1 - 0.6 * k), v=0.95 - 0.5 * k, dash=(14, 0.65 - 0.3 * k, 0.1))
            for m in range(8):
                a = math.radians(-160 + 140 * m / 7)
                dd = 10 + 50 * k
                Ld.cloud(cx + math.cos(a) * dd, cy + math.sin(a) * dd * 0.45 - 4, 7 * (1 - 0.4 * k), v=0.65 - 0.3 * k, flat=0.5, seed=m + i)
            if k < 0.7:
                _r = random.Random(seed + 9 + i)
                for m in range(10):
                    a = _r.uniform(-2.9, -0.25)
                    dd = (12 + 40 * k) * _r.uniform(0.5, 1.2)
                    W.ember(Le, cx + math.cos(a) * dd, cy - 6 + math.sin(a) * dd + 12 * k * k, math.cos(a), math.sin(a), 4.0 * (1 - 0.5 * k), w=0.6, v=0.9 - 0.3 * k)
            _r = random.Random(seed + 19 + i)
            for m in range(6):
                W.flake(Lfl, cx + _r.uniform(-30, 30), cy - _r.uniform(0, 30) + 10 * k, _r.uniform(1.3, 2.2), m, v=0.8 - 0.2 * k)
        out.append(fr.render())
    return out


def specs():
    T = {}
    T["katana_fullmoon"] = dict(rows=["any"], ms=FM_MS, glow=[1, 2], fn=lambda d: fullmoon(), anchor=K.PV, fit="pivot", meta=K.pp_meta(
        weapon="katana", awakening="만월(滿月)", followPlayer=False, depth="above",
        spawn="awaken_issen_chain", spawnNote="각성 '만월' 런에서 검기를 쓴 대쉬 일섬의 연속 일섬(최대 3회)이 끝난 순간, 마지막 도착 피벗에 1회. 각성 획득 연출로도 1회(시스템 선택)",
        impactFrame=1, frameRoles=["달이 떠오름", "첫 일섬(백열)", "둘째 일섬 · 큰 별(백열)", "셋째 일섬", "만월", "재로", "재로", "재로", "재로", "재"],
        design="주인공 뒤로 떠오르는 은재·호박 만월(열린 붓 원 — 위 왼쪽 틈) + 안쪽 점선 달무리·달 바다 점, 그 위를 가로지르는 연속 일섬 세 줄 → 재로 흩어짐"))
    T["greatsword_landslide"] = dict(rows=DIRS8, ms=LS_MS, glow=[0], fn=landslide, anchor=K.PV, fit="pivot", meta=dict(
        weapon="greatsword", awakening="산붕(山崩)", anchor="slam_point", dirTransform="drawn8", directionRows=DIRS8,
        directionRowsNote="대검 8방향 행 순서(계약 §18.3) — 몸 시트에서 고른 행 번호를 그대로. 바위 가시는 늘 화면 위로 솟음(회전하지 않음)",
        anchorNote="pivot = 칼끝이 바닥에 닿은 자리(4타 내려찍기 impactCircle 중심 · 차지 slamAnchors)", depth="Y 정렬 권장(바위가 서 있음) — 단순화하면 above",
        spawn="awaken_fourth_slam", spawnNote="각성 '산붕' 런에서 관성 순환 4타 내려찍기마다 꽂아내리기 충격파 대신 이 시트 1회(설계안 3.4)",
        impactFrame=0, hitShape=dict(type="rect", fromPx=0, lengthPx=4 * K.TILE, halfWidthPx=40, groups=[[0, 1, 2], [3, 4, 5], [6, 7, 8]],
                                     note="가시 세 무리가 30ms 간격으로 솟음(앞머리 = 무리) — 길이 4칸 참고값"),
        frameRoles=["첫 무리 솟음(핵 백열)", "둘째", "셋째", "다 솟음", "버팀", "금", "무너짐", "무너짐", "무너짐", "돌가루"],
        design="찍은 자리에서 조준 방향으로 바위 가시 아홉 개가 세 무리로 차례로 솟고(흙 테·호박 금) 바닥 금이 4칸 달린 뒤 돌가루로 무너짐"))
    T["dagger_hundred_ghosts"] = dict(rows=["any"], ms=HG_MS, glow=[3], fn=lambda d: hundred_ghosts(), anchor=(110, 120), fit="pivot", meta=dict(
        weapon="dagger", awakening="백귀(百鬼)", anchor="hitbox_center", followTarget=False, depth="above", spawn="brand_detonate",
        spawnNote="각성 '백귀' 런에서 낙인 기폭마다 dagger_brand_burst 와 함께 1회 — 분신 3체(설계안 3.4)", impactFrame=3, damageNote="분신 3체 피해는 시스템 데이터",
        frameRoles=["세 혼령 다가옴", "다가옴", "다가옴", "세 갈래 베기(백열)", "꿰뚫고 나감", "흩어짐", "재", "재", "재"],
        design="세 방향에서 날아드는 혼령(어두운 재 머리·흐르는 꼬리·호박 눈)이 대상을 꿰뚫으며 세 갈래 베기 → 재로 흩어짐"))
    T["bow_meteor_arrow"] = dict(rows=["any"], ms=MA_MS, glow=[2, 3], fn=lambda d: meteor(), anchor=(150, 300), fit="pivot", meta=dict(
        weapon="bow", awakening="유성(流星)", anchor="hitbox_center", followTarget=False, depth="above", spawn="awaken_perfect_release",
        anchorNote="pivot = 떨어지는 자리(완벽 놓기 화살이 맞은 적 발밑 · 화살비는 낙하점)", impactFrame=3, impactAtMs=sum(MA_MS[:3]),
        spawnNote="각성 '유성' 런에서 완벽 놓기 화살마다 하늘에서 1발 추가(설계안 3.4) — 적중 지점에 생성, f3 시작(120ms 뒤)이 판정",
        hitShape=dict(type="circle", radiusPx=56, note="착탄 반경 참고값"),
        frameRoles=["별똥 낙하", "낙하", "닿기 직전(백열 촉)", "착탄(백열 별)", "고리 퍼짐", "퍼짐", "식음", "재", "재"],
        design="왼쪽 위 하늘에서 호박 불꼬리를 끄는 별똥 화살이 떨어져 꽂히며 큰 별·고리 → 흙먼지·불티·재"))
    return T


SIG = ["katana_fullmoon", "greatsword_landslide", "dagger_hundred_ghosts", "bow_meteor_arrow"]
NAMES = SIG


def job(name):
    sp = specs()[name]
    frames = {d: sp["fn"](d) for d in sp["rows"]}
    res = K.write(name, frames, sp["rows"], sp["ms"], sp["glow"], sp["anchor"], fit=sp["fit"], meta=dict(sp["meta"]), src=SRC)
    if sp["meta"].get("anchor") == "player_pivot":
        import fx_combo
        fx_combo._hit_origin(name)
    return res
