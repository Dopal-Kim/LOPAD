"""61 단계 5 칼 fx 시트 — 고치기 전 그림(kcommon.SRC_REV)에서 경로·칸별 머리/꼬리를 따서 '은선 베기'로 다시 그린다(kfx 조각)."""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kfx as F  # noqa: E402
from kfx import G, SL, SIL, X0, X1, A21, A23, A25, Pal  # noqa: E402

DIR_VEC = {"right": (1, 0), "down": (0, 1), "left": (-1, 0), "up": (0, -1)}


def role_of(txt):
    t = txt.lower()
    if "터짐" in t:
        return "burst"
    if "분신" in t:
        return "shadow"
    if "잔심" in t or "남은" in t:
        return "linger"
    if "재" in t or "decay" in t or "마름" in t:
        return "decay"
    if "꿰뚫음" in t:
        return "hold"
    if t.startswith("pre") or "닿음" in t and "draw" not in t:
        return "pre"
    return "draw"


# 시트 사양: kind(arc/line/issen/iai/guard), 옵션
SPEC = {
    "katana_rise": dict(kind="arc", wmax=3.0, hair=[-5]),
    "katana_fall": dict(kind="arc", wmax=3.0, hair=[-5]),
    "katana_counter": dict(kind="arc", wmax=2.6, hair=[-4]),
    "katana_fall_wide": dict(kind="arc", wmax=3.4, hair=[-5, -10, -15]),
    "katana_spin": dict(kind="arc", wmax=3.2, hair=[-5, -9]),
    "katana_thrust": dict(kind="line", wmax=3.0, hair=[-4, 4], ring=True),
    "katana_thrust_ki1": dict(kind="line", wmax=3.0, hair=[-4, 4, -8], ring=True),
    "katana_thrust_ki2": dict(kind="line", wmax=3.4, hair=[-4, 4, -8, 8], ring=True),
    "katana_thrust_ki3": dict(kind="line", wmax=3.8, hair=[-4, 4, -8, 8, -12, 12], ring=True),
    "katana_iai": dict(kind="iai", wmax=3.0, hair=[-5], level=0),
    "katana_iai_ki1": dict(kind="iai", wmax=3.0, hair=[-5, 5], level=1),
    "katana_iai_ki2": dict(kind="iai", wmax=3.4, hair=[-5, 5, -9], level=2),
    "katana_iai_ki3": dict(kind="iai", wmax=3.8, hair=[-5, 5, -9, 9], level=3),
    "katana_guardbreak": dict(kind="guard", wmax=3.4, hair=[-5]),
}
for _t in (1, 2, 3, 4):
    SPEC["katana_issen_line_t%d" % _t] = dict(kind="issen", wmax=3.0, hair=[-4], solo=False)
    SPEC["katana_issen_line_t%d_solo" % _t] = dict(kind="issen", wmax=3.0, hair=[-4], solo=True)
for _b in ("katana_rise", "katana_fall", "katana_fall_wide", "katana_spin", "katana_thrust", "katana_issen_line_t1", "katana_issen_line_t2",
           "katana_issen_line_t3", "katana_issen_line_t4"):
    SPEC[_b + "_awaken"] = dict(SPEC[_b], moon=True)

DESIGN = {
    "arc": "은선 베기 — 판정 호를 따라 날끝(머리)에서 끌리는 가는 빛 틈(바깥 날선 쪽이 가장 밝은 1~3도트, 꼬리로 1도트) + 안쪽 1도트 잔상 실선. "
           "판정 머리 백열 + 접선으로 곧게 뻗는 섬광 바늘 + 첫 판정 칸 4갈래 별 · 호박 불티 · 소멸은 선이 마디로 끊기며 엇갈려 벌어지는 베인 자국",
    "line": "은선 찌르기 — 칼끝을 따라 곧게 뻗는 가는 빛 바늘(머리 뾰족) + 양옆 평행 잔상 실선(검기 단수만큼) + 판정 머리 백열·섬광 바늘·4갈래 별 + 칼끝 앞 공기 고리 · 베인 자국 소멸",
    "iai": "발도 일섬 — 앞을 비스듬히 가로지르는 한 줄 섬광(머리 백열) → 잔심 동안 가는 선으로 남아 떨림 → 납도 딸깍 칸에 늦게 터짐: 선이 두 줄로 갈라지며 비스듬한 베인 자국들이 열림(백열 없음) → 마디로 끊겨 식음",
    "issen": "일섬 선 — 돌진 뒤로 곧게 그어지는 가는 빛 선(머리 백열) → 남은 가는 선 → (분신) 지나간 부분만 다시 밝아짐 → 터짐: 두 줄로 갈라지며 비스듬한 베인 자국 → 마디로 끊겨 식음",
    "guard": "가드 불가 내려베기 — 머리 위에서 앞 땅까지 떨어지는 가는 빛 호 → 땅에 닿는 순간 앞으로 3칸 곧게 갈라지는 땅 틈(두 줄로 벌어지며 비스듬한 베인 자국) → 베인 자국 소멸",
}


def _px(im):
    return [(x, y) for x, y, c in F.opaque(im)]


def render_sheet(name, meta, old):
    sp = SPEC[name]
    pal = Pal(moon=sp.get("moon", False))
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    n = meta["frames"]
    roles = [role_of(t) for t in meta.get("frameRoles", [])] or ["draw"] * n
    glow = set(meta.get("glowFrames") or [])
    hit = meta.get("hitOriginInFrame") or meta.get("pivot")
    center = (hit["x"], hit["y"])
    out = {}
    for ri, d in enumerate(meta["directions"]):
        pix = [_px(im) for im in old[d]]
        seed = sum(map(ord, name)) * 7 + ri * 101
        if sp["kind"] == "guard":
            out[d] = guard_row(sp, meta, pix, roles, glow, d, center, pal, seed)
            continue
        ref_frames = [i for i in range(n) if roles[i] in ("pre", "draw", "hold")]
        union = [p for i in ref_frames for p in pix[i]]
        if sp["kind"] == "arc":
            path = F.trace_arc(union, center)
        else:
            path = F.trace_line(union)
        path = F.orient(path, [pix[i] for i in ref_frames], center if sp["kind"] != "arc" else None)
        covs = [F.coverage(path, pix[i]) for i in range(n)]
        out[d] = row_frames(sp, roles, glow, path, covs, fw, fh, pal, seed, n)
    return out


def _decay_k(roles, i, kinds=("decay",)):
    idx = [j for j, r in enumerate(roles) if r in kinds]
    if i not in idx:
        return 0.0
    return (idx.index(i) + 1) / float(len(idx))


def moon_glints(cv, path, u0, u1, pal, shift, pr=4):
    """각성(만월) 궤적: 획 바깥에 작은 초승달 반짝."""
    L = (u1 - u0) * path.L
    k = 0
    pos = 18 + (shift * 7) % 20
    while pos < L - 6:
        (x, y), (tx, ty), (nx, ny) = path.at(u0 + pos / path.L)
        cx, cy = x + nx * 6, y + ny * 6
        for a in range(-60, 61, 30):
            r = math.radians(a)
            dx, dy = nx * math.cos(r) + tx * math.sin(r), ny * math.cos(r) + ty * math.sin(r)
            cv.put(cx + dx * 2.2, cy + dy * 2.2, SIL[11] if abs(a) < 40 else SIL[8], pr)
        pos += 38
        k += 1


def row_frames(sp, roles, glow, path, covs, fw, fh, pal, seed, n):
    frames = []
    first_glow = min(glow) if glow else None
    full = (0.0, 1.0)
    hair = sp.get("hair", [-5])
    for i in range(n):
        cv = F.Cv(fw, fh)
        role = roles[i] if i < len(roles) else "decay"
        cov = covs[i]
        hot = i in glow
        u0, u1 = (cov[0], cov[1]) if cov else (None, None)
        if role in ("pre", "draw", "hold") and cov:
            if role == "pre":
                F.slit(cv, path, u0, u1, pal, hot=False, wmax=sp["wmax"] * 0.7, bright=0.7)
            else:
                F.slit(cv, path, u0, u1, pal, hot=hot, wmax=sp["wmax"], bright=1.0 if role == "draw" else 0.92)
                for j, off in enumerate(hair):
                    a = u0 + (u1 - u0) * (0.3 + 0.08 * j)
                    F.hairline(cv, path, a, u1 - (u1 - u0) * 0.03, off, pal.col(0.5 - 0.06 * j), dash=(6, 3) if j else (9, 2), shift=i * 3 + j)
                (x, y), (tx, ty), (nx, ny) = path.at(u1)
                if hot:
                    F.needle(cv, x + tx, y + ty, tx, ty, 13 if i == first_glow else 8, [X1, G[13], G[12], G[11], G[9]] if i == first_glow else [G[13], G[11], G[9]])
                    if i == first_glow:
                        F.star(cv, x, y, 3)
                if role == "draw":
                    F.sparks(cv, x, y, tx, ty, nx, ny, seed + i, n=3 if not hot else 5)
                if sp.get("ring") and (hot or role == "hold"):
                    thrust_ring(cv, x + tx * (6 if hot else 9), y + ty * (6 if hot else 9), tx, ty, nx, ny, 5 if hot else 7, pal)
                if pal.moon:
                    moon_glints(cv, path, u0, u1, pal, i)
        elif role == "decay" and cov:
            k = _decay_k(roles, i)
            F.cut_marks(cv, path, u0, u1, k, pal, seed + i)
            if k < 0.5:
                F.hairline(cv, path, u0 + (u1 - u0) * 0.4, u1, hair[0], pal.col(0.3), dash=(3, 4), shift=i * 2)
        elif role == "decay" and not cov and i > 0:
            pass
        frames.append(cv.image())
    return frames


def thrust_ring(cv, x, y, tx, ty, nx, ny, r, pal):
    """찌르기 칼끝 앞 공기 고리(납작한 타원 1도트, 앞쪽 반만 밝게)."""
    for a in range(0, 360, 12):
        t = math.radians(a)
        px_ = x + tx * math.cos(t) * r * 0.35 + nx * math.sin(t) * r
        py_ = y + ty * math.cos(t) * r * 0.35 + ny * math.sin(t) * r
        cv.put(px_, py_, pal.col(0.62 if math.cos(t) > 0 else 0.38), 3)


# =============================================================================
# 발도(iai) · 일섬(issen)
# =============================================================================
def render_long(name, meta, old):
    sp = SPEC[name]
    pal = Pal(moon=sp.get("moon", False))
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    n = meta["frames"]
    roles = [role_of(t) for t in meta["frameRoles"]]
    glow = set(meta.get("glowFrames") or [])
    hit = meta.get("hitOriginInFrame") or meta.get("pivot")
    origin = (hit["x"], hit["y"])
    out = {}
    lvl = sp.get("level", 0)
    for ri, d in enumerate(meta["directions"]):
        pix = [_px(im) for im in old[d]]
        seed = sum(map(ord, name)) * 7 + ri * 101
        ref = [i for i in range(n) if roles[i] in ("pre", "draw")]
        union = [p for i in ref for p in pix[i]]
        path = F.orient(F.trace_line(union), [pix[i] for i in ref], origin)
        covs = [F.coverage(path, pix[i]) for i in range(n)]
        frames = []
        burst_i = roles.index("burst") if "burst" in roles else None
        first_glow = min(glow) if glow else None
        Ltot = path.L
        ncut = max(3, min(8, int(Ltot / 36)))
        for i in range(n):
            cv = F.Cv(fw, fh)
            role = roles[i]
            cov = covs[i]
            hot = i in glow
            if role in ("pre", "draw"):
                if cov:
                    u0, u1 = cov[0], cov[1]
                    F.slit(cv, path, u0, u1, pal, hot=hot, wmax=sp["wmax"], bright=1.0 if role == "draw" else 0.7)
                    for j, off in enumerate(sp["hair"]):
                        F.hairline(cv, path, u0 + (u1 - u0) * 0.25, u1, off, pal.col(0.5 - 0.05 * j), dash=(8, 3), shift=i * 3 + j)
                    (x, y), (tx, ty), (nx, ny) = path.at(u1)
                    if hot:
                        F.needle(cv, x + tx, y + ty, tx, ty, 14 if i == first_glow else 8, [X1, G[13], G[12], G[11]] if i == first_glow else [G[13], G[11]])
                        if i == first_glow:
                            F.star(cv, x, y, 3)
                    F.sparks(cv, x, y, tx, ty, nx, ny, seed + i, n=4 + lvl)
                    if pal.moon:
                        moon_glints(cv, path, u0, u1, pal, i)
            elif role == "linger":
                # 남은 가는 선: 1도트 G11 + 떨리는 반짝이 흐름 + 검기 단수만큼 옅은 평행선
                ph = i * 5
                F.hairline(cv, path, 0.0, 1.0, 0, pal.col(0.6), dash=None, taper=False, pr=2)
                k = 0
                Ls = path.L
                pos = ph % 11
                while pos < Ls:
                    (x, y), _, (nx, ny) = path.at(pos / Ls)
                    cv.put(x, y, pal.col(0.9), 3)
                    pos += 11
                for j, off in enumerate(sp["hair"][:1 + lvl]):
                    F.hairline(cv, path, 0.15, 0.95, off * 0.6, pal.col(0.3), dash=(4, 5), shift=i * 2 + j)
            elif role == "shadow":
                # 분신이 지나간 만큼 다시 밝아짐
                j = [q for q, r in enumerate(roles) if r == "shadow"].index(i)
                frac = (j + 1) / 3.0
                F.hairline(cv, path, 0.0, 1.0, 0, pal.col(0.6), dash=None, taper=False, pr=1)
                F.slit(cv, path, max(0.0, frac - 0.45), frac, pal, hot=False, wmax=2.2, bright=0.95)
                (x, y), (tx, ty), (nx, ny) = path.at(frac)
                F.sparks(cv, x, y, tx, ty, nx, ny, seed + i, n=3)
            elif role == "burst":
                hot_b = hot and not sp.get("solo")
                maxv = 0.86 if (sp["kind"] == "iai" or sp.get("solo")) else 1.0
                F.hairline(cv, path, 0.02, 0.98, 3, pal.col(0.86 * maxv), dash=None, taper=True, pr=3)
                F.hairline(cv, path, 0.02, 0.98, -3, pal.col(0.72 * maxv), dash=None, taper=True, pr=3)
                F.hairline(cv, path, 0.1, 0.9, 0, pal.col(0.4), dash=(3, 3), taper=False, pr=2)
                F.cross_cuts(cv, path, 0.0, pal, seed, hot=hot_b, n=ncut + lvl, ln=26 + 3 * lvl, max_v=maxv)
                if lvl:
                    for j, off in enumerate(sp["hair"][1:]):
                        F.hairline(cv, path, 0.1, 0.9, off * 1.2, pal.col(0.42), dash=(5, 3), shift=j)
            elif role == "decay":
                after = [q for q, r in enumerate(roles) if r == "decay" and (burst_i is None or q > burst_i)]
                k = (after.index(i) + 1) / float(len(after)) if i in after else 0.5
                F.cut_marks(cv, path, 0.0 + 0.2 * k, 1.0 - 0.1 * k, 0.35 + 0.65 * k, pal, seed + i)
                F.cross_cuts(cv, path, 0.4 + 0.6 * k, pal, seed, hot=False, n=ncut + lvl, ln=26 + 3 * lvl, spark=k < 0.4, max_v=0.8)
            frames.append(cv.image())
        out[d] = frames
    return out


# =============================================================================
# 가드 불가 내려베기 — 떨어지는 호 + 땅 틈
# =============================================================================
def guard_row(sp, meta, pix, roles, glow, d, center, pal, seed):
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    n = meta["frames"]
    piv = (meta["pivot"]["x"], meta["pivot"]["y"])
    vx, vy = DIR_VEC[d]
    # 땅 틈 = 마지막 두 소멸 칸에 남는 곧은 선(가장 확실하게 땅 틈만 남는 칸)
    gpix = pix[n - 1] + pix[n - 2]
    gpath = F.trace_line(gpix) if len(gpix) > 8 else None
    if gpath:
        a_, b_ = gpath.p[0], gpath.p[-1]
        if math.hypot(b_[0] - center[0], b_[1] - center[1]) < math.hypot(a_[0] - center[0], a_[1] - center[1]):
            gpath = F.Path(list(reversed(gpath.p)), None)
    gset = set()
    if gpath:
        g0, g1 = gpath.p[0], gpath.p[-1]
        gl = math.hypot(g1[0] - g0[0], g1[1] - g0[1]) or 1.0
        gx, gy_ = (g1[0] - g0[0]) / gl, (g1[1] - g0[1]) / gl
        for i in range(n):
            for x, y in pix[i]:
                t = (x + 0.5 - g0[0]) * gx + (y + 0.5 - g0[1]) * gy_
                lat = abs((x + 0.5 - g0[0]) * -gy_ + (y + 0.5 - g0[1]) * gx)
                if -4 <= t <= gl + 6 and lat < 12:
                    gset.add((x, y))
    fg = min(glow) if glow else n
    arc_pix = [p for i in range(fg) if roles[i] in ("pre", "draw") for p in pix[i] if p not in gset]
    angs = sorted(math.degrees(math.atan2(y - center[1], x - center[0])) for x, y in arc_pix)
    gaps = [(angs[(i + 1) % len(angs)] - angs[i]) % 360 for i in range(len(angs))] if angs else [360]
    spread = 360 - max(gaps)
    if spread > 25:
        apath = F.trace_arc(arc_pix, center)
    else:
        apath = F.trace_line(arc_pix)
    apath = F.orient(apath, [[p for p in pix[i] if p not in gset] for i in range(fg) if roles[i] in ("pre", "draw")], None)
    if gpath and apath:                                 # 호 끝을 땅 틈 시작점까지 잇는다(땅에 닿음)
        e, g0 = apath.p[-1], gpath.p[0]
        dd = math.hypot(g0[0] - e[0], g0[1] - e[1])
        if dd > 2:
            k = max(2, int(dd / 2))
            apath = F.Path(apath.p + [(e[0] + (g0[0] - e[0]) * j / k, e[1] + (g0[1] - e[1]) * j / k) for j in range(1, k + 1)], apath.center)
    acov = [F.coverage(apath, [p for p in pix[i] if p not in gset]) for i in range(n)]
    for i in range(fg, n):                              # 땅에 닿은 뒤: 호는 끝까지
        if roles[i] in ("pre", "draw") and acov[i]:
            acov[i] = (acov[i][0], 1.0, acov[i][2])
    gcov = [F.coverage(gpath, pix[i], tol=5.0) if gpath else None for i in range(n)]
    frames = []
    first_glow = min(glow) if glow else None
    for i in range(n):
        cv = F.Cv(fw, fh)
        role = roles[i]
        hot = i in glow
        if role in ("pre", "draw"):
            c = acov[i]
            if c:
                F.slit(cv, apath, c[0], c[1], pal, hot=hot, wmax=sp["wmax"] * (0.7 if role == "pre" else 1.0), bright=0.7 if role == "pre" else 1.0)
                F.hairline(cv, apath, c[0] + (c[1] - c[0]) * 0.35, c[1], -5, pal.col(0.48), dash=(8, 3), shift=i * 3)
                (x, y), (tx, ty), (nx, ny) = apath.at(c[1])
                if hot and i == first_glow:
                    F.star(cv, x, y, 3)
                F.sparks(cv, x, y, tx, ty, nx, ny, seed + i, n=3)
            g = gcov[i] if hot else None
            if g and gpath:
                F.slit(cv, gpath, 0.0, g[1], pal, hot=hot, wmax=3.0, bright=1.0)
                (x, y), (tx, ty), (nx, ny) = gpath.at(g[1])
                F.needle(cv, x + tx, y + ty, tx, ty, 10, [X1, G[13], G[11]] if hot else [G[13], G[11]])
                if i != first_glow:
                    F.hairline(cv, gpath, 0.05, g[1] * 0.95, 2, pal.col(0.7), dash=None, pr=3)
                    F.hairline(cv, gpath, 0.05, g[1] * 0.95, -2, pal.col(0.55), dash=None, pr=3)
                    F.cross_cuts(cv, gpath, 0.0, pal, seed, hot=hot, n=5, ln=14)
        elif role == "decay":
            k = _decay_k(roles, i)
            c = acov[i] or (0.3 + 0.5 * k, 1.0, 0)
            F.cut_marks(cv, apath, max(c[0], 0.2 + 0.6 * k), 1.0, k, pal, seed + i)
            if gpath:
                F.cut_marks(cv, gpath, 0.0, 1.0 - 0.2 * k, 0.3 + 0.7 * k, pal, seed + 50 + i)
                F.cross_cuts(cv, gpath, 0.35 + 0.65 * k, pal, seed, hot=False, n=5, ln=14, spark=k < 0.4, max_v=0.8)
        frames.append(cv.image())
    return frames


# =============================================================================
# 적중 섬광 hit_katana(_heavy) — 적중점을 가르는 은빛 바늘 → 두 쪽이 미끄러지며 갈라짐 → 마디 소멸
# =============================================================================
def lens(cv, cx, cy, dx, dy, half, wmax, v0, hot, pal, pr=3, skip=0, dash=False):
    """가운데 굵고(wmax) 양끝 1도트 바늘로 모이는 렌즈 획. skip = 가운데 비움(갈라짐)."""
    nx, ny = -dy, dx
    m = int(half)
    for j in range(-m, m + 1):
        if abs(j) < skip:
            continue
        s = abs(j) / float(m)
        if dash and (abs(j) // 3) % 2:
            continue
        w = 1.0 + (wmax - 1.0) * (1 - s) ** 1.6
        hw = w / 2.0
        o = -hw
        while o <= hw + 1e-6:
            q = 1 - (abs(o) / (hw + 0.6)) ** 2
            v = v0 * (0.62 + 0.38 * q) * (0.86 + 0.14 * (1 - s)) + (0.08 if q > 0.8 else 0.0)
            cv.put(cx + dx * j + nx * o, cy + dy * j + ny * o, pal.col(min(1.0, v), hot and s < 0.7 and q > 0.45), pr)
            o += 0.5


def render_hit(name, meta, old):
    """적중 섬광: 적중점을 앞위로 비스듬히 가르는 은빛 렌즈 바늘 + 공격 방향 바늘 + 별 → 가운데서 갈라져 양쪽으로 미끄러짐 → 끊긴 마디로 식음."""
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    n = meta["frames"]
    piv = (meta["pivot"]["x"], meta["pivot"]["y"])
    heavy = "heavy" in name
    glow = set(meta.get("glowFrames") or [])
    pal = Pal()
    frames = []
    ang = math.radians(-62)
    dx, dy = math.cos(ang), math.sin(ang)
    half = min(fh * 0.46, fw * 0.6) if not heavy else min(fh * 0.47, fw * 0.45)
    cx, cy = piv
    for i in range(n):
        cv = F.Cv(fw, fh)
        hot = i in glow
        k = i / float(max(1, n - 1))
        if i == 0:
            lens(cv, cx, cy, dx, dy, half, 5.0 if heavy else 4.0, 1.0, hot, pal)
            hl = fw * (0.26 if heavy else 0.24)
            lens(cv, cx + 4 + hl, cy, 1, 0, hl, 3.0, 0.95, hot, pal, pr=2)
            if heavy:
                a2 = math.radians(30)
                lens(cv, cx, cy, math.cos(a2), math.sin(a2), half * 0.75, 4.0, 0.95, hot, pal, pr=2)
            F.star(cv, cx, cy, 5 if heavy else 4, hot=hot)
        else:
            slide = 3.0 * i
            sep = 1.0 + 1.2 * i
            for sgn in (1, -1):
                ox = dx * slide * sgn - dy * sep * sgn
                oy = dy * slide * sgn + dx * sep * sgn
                hx_ = cx + ox + dx * half * 0.5 * sgn
                hy_ = cy + oy + dy * half * 0.5 * sgn
                lens(cv, hx_, hy_, dx, dy, half * 0.5 * (1 - 0.25 * k), (3.0 if heavy else 2.4) * (1 - 0.5 * k), 0.95 - 0.5 * k,
                     hot, pal, dash=k > 0.45)
            if heavy and i < n - 1:
                a2 = math.radians(30)
                ex, ey = math.cos(a2), math.sin(a2)
                for sgn in (1, -1):
                    lens(cv, cx + ex * (half * 0.4 + slide) * sgn, cy + ey * (half * 0.4 + slide) * sgn, ex, ey, half * 0.3 * (1 - 0.3 * k),
                         2.0, 0.85 - 0.5 * k, hot, pal, dash=k > 0.4)
            if i <= 2:
                hl = fw * 0.18 * (1 - 0.3 * i)
                lens(cv, cx + 8 + 5 * i + hl, cy, 1, 0, hl, 2.0, 0.8 - 0.2 * i, hot, pal, pr=2, dash=i == 2)
        if i < 4:
            F.sparks(cv, cx + 6 + 6 * i, cy, 1, 0, 0, -1, 17 + i * 3, n=(10 if heavy else 7) - i, age=i / 4.0)
            F.sparks(cv, cx + 6 + 6 * i, cy, 0.8, -0.6, 0.6, 0.8, 91 + i * 3, n=(6 if heavy else 4) - i // 2, age=i / 4.0)
        frames.append(cv.image())
    return {meta["directions"][0]: frames}


def render(name, meta, old):
    if name.startswith("hit_katana"):
        return render_hit(name, meta, old)
    sp = SPEC[name]
    if sp["kind"] in ("iai", "issen"):
        return render_long(name, meta, old)
    return render_sheet(name, meta, old)


def design_of(name):
    if name.startswith("hit_katana"):
        return ("은선 적중 — 적중점을 앞위로 비스듬히 가르는 은빛 바늘 + 공격 방향 바늘 + 4갈래 별(판정) → 바늘이 가운데서 갈라져 양쪽으로 미끄러짐 → 마디로 끊겨 식음"
                + (" · 막타: 반대 사선 바늘을 더해 X 자" if "heavy" in name else ""))
    sp = SPEC[name]
    d = DESIGN[{"arc": "arc", "line": "line", "iai": "iai", "issen": "issen", "guard": "guard"}[sp["kind"]]]
    if sp.get("moon"):
        d = "각성(만월) 궤적 — " + d + " · 은빛 램프 + 획 바깥 작은 초승달 반짝"
    if sp.get("level"):
        d += " · 검기 %d단: 평행 잔상 실선 %d줄 · 불티 +%d" % (sp["level"], len(sp["hair"]), sp["level"])
    if name.startswith("katana_thrust_ki"):
        d += " · 검기 %s단: 평행 잔상 실선 %d줄" % (name[-1], len(sp["hair"]))
    return d
