"""62 루프 4 (P18 §3) 칼 갈래 시트용 스미어 — §31-1 규칙(r62b smear.py 같은 코드·같은 형식).

- `fx/v3/katana_spin_smear`       선풍 1단 A 회전 베기 — 무기 weapons/v3/katana_spin 과 같은 틀·피벗·프레임(15)·ms.
                                   칼끝이 몸을 한 바퀴 도는 동작이라 칸 사이 칼끝을 직선(Catmull-Rom)으로 이으면 몸을 가로지른다 →
                                   회전 중심(판정 원점 = 피벗 위 40도트) 둘레 극좌표로 보간(각은 화면 시계 방향, 반지름은 선형).
- `fx/v3/katana_guardbreak_smear` 투구가르기 1단 B 내려치기 — weapons/v3/katana_guardbreak 과 같은 틀(15칸). 위에서 땅까지 곧게.
- `fx/v3/katana_fall_wide_smear`  선풍 1단 A 연격 변화(2타 호 180°, fx katana_fall_wide ↔ katana_fall 1:1 교체) — 몸·무기 시트는
                                   katana_fall 그대로라 틀·프레임·ms 도 weapons/v3/katana_fall. 기본 katana_fall_smear 보다 굵고(폭 ×1.45)
                                   꼬리를 한 칸 더 끌며(0칸 칼끝부터) 사라짐이 한 칸 늦다. 시스템: 갈래 런에서 katana_fall_smear 대신 이것.
색 = 칼 '서리' 램프(§28), 흰 끝은 무기 glowFrames 칸만.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "r62b"))
import common as rc  # noqa: E402
import smear as S  # noqa: E402

SRC = "parts/art/work/r62d/build.py (62 루프 4 · P18 §3) · smear_branch.py → r62b smear.py 같은 코드"

SPIN = dict(weapon="katana", ramp=rc.FROST, sweep=[7, 8, 9, 10, 11], decay=[12, 13], width=0.5, hit=None)
GUARD = dict(weapon="katana", ramp=rc.FROST, sweep=[9, 10, 11], decay=[12, 13], width=0.55, hit=None)
WIDE = dict(weapon="katana", ramp=rc.FROST, sweep=[1, 2, 3], decay=[4, 5], width=0.46 * 1.45, hit=2)


def polar_samples(tips, grips, k, steps, c, cw=True):
    """칸 k-1 → k 칼끝을 중심 c 둘레 극좌표로 보간(시계 방향 cw). 손잡이는 직선."""
    a0 = math.atan2(tips[k - 1][1] - c[1], tips[k - 1][0] - c[0])
    a1 = math.atan2(tips[k][1] - c[1], tips[k][0] - c[0])
    da = a1 - a0
    if cw:                       # 화면 좌표(y 아래)에서 시계 방향 = 각 증가
        while da <= 0:
            da += 2 * math.pi
    else:
        while da >= 0:
            da -= 2 * math.pi
    r0 = math.dist(tips[k - 1], c)
    r1 = math.dist(tips[k], c)
    steps = max(steps, int(abs(da) * max(r0, r1) * 1.6))      # 호 길이 1도트당 1.6 표본(빗살 방지)
    out = []
    for i in range(steps + 1):
        t = i / steps
        a = a0 + da * t
        r = r0 + (r1 - r0) * t
        out.append(((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r * 0.92), S.lerp(grips[k - 1], grips[k], t)))
    return out


def build_spin():
    """회전 베기: 극좌표 띠. 칸마다 지난 두 마디(≈180°)를 꼬리로."""
    name = "katana_spin"
    wm, wg = S.load_grid("weapons/v3/" + name)
    fw, fh, n, dirs = wm["frameWidth"], wm["frameHeight"], wm["frames"], wm["directions"]
    piv = (wm["pivot"]["x"], wm["pivot"]["y"])
    c = (piv[0], piv[1] - 40)
    glow = set(wm.get("glowFrames", []))
    cfg = SPIN
    frames, head, tail, drawn = [], {}, {}, set()
    for d in dirs:
        tips, grips = wm["bladeTipAnchors"][d], wm["gripAnchors"][d]
        lmax = max(math.dist(t, g) for t, g in zip(tips, grips) if t)
        head[d], tail[d] = [None] * n, [None] * n
        sw = cfg["sweep"]
        for f in range(n):
            buf = S.Buf(fw, fh)
            fade, dissolve, active = 1.0, 0.0, False
            if f in sw:
                segs = [k for k in (f - 1, f) if k in sw]
                if len(segs) == 2:
                    S.paint_band(buf, polar_samples(tips, grips, segs[0], 50, c), 0.0, 0.42, lmax, cfg["width"])
                    S.paint_band(buf, polar_samples(tips, grips, segs[1], 60, c), 0.42, 1.0, lmax, cfg["width"])
                else:
                    S.paint_band(buf, polar_samples(tips, grips, f, 70, c), 0.0, 1.0, lmax, cfg["width"])
                active = True
                head[d][f] = list(tips[f])
                tail[d][f] = list(tips[segs[0] - 1])
            elif f in cfg["decay"]:
                i = cfg["decay"].index(f)
                last = sw[-1]
                cut = [0.8, 0.58][i]
                S.paint_band(buf, polar_samples(tips, grips, last - 1, 50, c), 0.0, 0.42 * cut, lmax, cfg["width"] * 0.8)
                pts = polar_samples(tips, grips, last, 60, c)
                S.paint_band(buf, pts[:int(60 * cut)], 0.42 * cut, cut, lmax, cfg["width"] * 0.8)
                fade, dissolve = [0.72, 0.5][i], [0.3, 0.6][i]
                active = True
                head[d][f] = [round(v, 1) for v in pts[int(59 * cut)][0]]
                tail[d][f] = list(tips[last - 2])
            if active:
                im = S.render(buf, cfg["ramp"], f in glow, fade, dissolve, seed=f)
                drawn.add(f)
            else:
                im = S.Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            frames.append(im)
    return write(name, name + "_smear", wm, frames, cfg, drawn, head, tail,
                 "회전 베기 스미어 — 칼끝이 몸 둘레를 시계 방향으로 도는 띠(회전 중심 = 판정 원점, 극좌표 보간). 칸마다 지난 두 마디(약 반 바퀴)가 "
                 "꼬리로 식고, 끝나면 제자리에서 마디로 부서진다.")


def build_linear(weapon_name, out_name, cfg, design, extra=None):
    """기본 r62b build_move 를 그대로 쓰되 출력 이름만 바꾼다(갈래 fall_wide 는 무기 시트가 katana_fall)."""
    orig_write = S.b2.write_sheet
    got = {}

    def _write(cat, name, frames, fw, fh, meta, **kw):
        got["frames"] = frames
        got["meta"] = meta
        return None
    S.b2.write_sheet = _write
    try:
        frames, wm, sf = S.build_move(weapon_name, cfg)
    finally:
        S.b2.write_sheet = orig_write
    meta = got["meta"]
    head, tail = meta["smearHeadAnchors"], meta["smearTailAnchors"]
    return write(weapon_name, out_name, wm, frames, cfg, set(sf), head, tail, design, extra)


def build_fall_wide():
    """기본 katana_fall_smear 와 같은 코드, 폭 ×1.45 + 0칸 칼끝부터 꼬리 + 사라짐 칸 덜 깎임."""
    orig_band = S.paint_band
    orig_samples = S.sweep_samples

    def band(buf, samples, s0, s1, lmax, width, taper=1.2):
        return orig_band(buf, samples, s0, s1, lmax, width, taper=0.9)     # 꼬리도 덜 가늘게(넓은 호)
    S.paint_band = band
    try:
        res = build_linear("katana_fall", "katana_fall_wide_smear", WIDE,
                           "선풍 연격 변화(2타 호 180°) 스미어 — 기본 katana_fall_smear 와 같은 칼끝 궤적, 폭 ×1.45·꼬리 덜 가늘게. "
                           "사라짐 칸은 칼에서 떨어져 제자리에서 식는다.",
                           {"branch": "선풍(旋風) 1단 A — 연격 변화", "replaces": "fx/v3/katana_fall_smear",
                            "replaceRule": "fx/v3/katana_fall_wide 를 쓰는 갈래 런에서 katana_fall_smear 대신 이 시트(같은 틀·프레임·ms — 1:1). "
                                           "몸·무기 시트는 katana_fall 그대로"})
    finally:
        S.paint_band = orig_band
        S.sweep_samples = orig_samples
    return res


def streak(buf, samples, s0, s1, hw0):
    """칼끝 길을 따라 가로 폭이 있는 줄기(칼날이 제 축 방향으로 떨어지는 내려치기 — 칼끝→손잡이 띠만으로는 1도트 선이 된다)."""
    m = len(samples)
    for i, (tip, _) in enumerate(samples):
        s = s0 + (s1 - s0) * (i / max(1, m - 1))
        hw = max(0.8, hw0 * (s ** 1.1))
        r = int(hw) + 1
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                d = math.hypot(dx, dy)
                if d <= hw:
                    buf.put(tip[0] + dx, tip[1] + dy, s, 1.0 - d / (hw + 0.01))


def build_guard():
    orig_band = S.paint_band

    def band(buf, samples, s0, s1, lmax, width, taper=1.2):
        orig_band(buf, samples, s0, s1, lmax, width, taper)
        streak(buf, samples, s0, s1, 7.0 * (0.8 if width < GUARD["width"] else 1.0))
    S.paint_band = band
    try:
        return build_linear("katana_guardbreak", "katana_guardbreak_smear", GUARD,
                            "투구가르기 내려치기 스미어 — 상단에서 땅까지 곧게 떨어지는 굵은 줄기(머리 = 지금 칼끝, 폭 약 14도트 → 꼬리 1도트) + 칼날 띠. "
                            "판정 두 칸(10·11)에 흰 끝.")
    finally:
        S.paint_band = orig_band


def write(weapon_name, out_name, wm, frames, cfg, drawn, head, tail, design, extra=None):
    fw, fh, dirs = wm["frameWidth"], wm["frameHeight"], wm["directions"]
    sf = sorted(drawn)
    glow = set(wm.get("glowFrames", []))
    meta = {
        "directions": dirs,
        "layout": wm.get("layout", "rows = directions, columns = frames"),
        "pivot": wm["pivot"],
        "playerFrameOffset": wm.get("playerFrameOffset"),
        "anchor": "player_pivot",
        "overlayOf": "weapons/v3/" + weapon_name,
        "sameFrameAs": "weapons/v3/" + weapon_name,
        "overlay": f"player_{weapon_name} · weapons/v3/{weapon_name} 와 **같은 프레임 번호를 같은 시각에** 겹친다(같은 틀 {fw}×{fh}·피벗·"
                   "playerFrameOffset·방향 행). 각성 외형(weapons/v4/katana_*_<동작>)도 프레임이 같아 그대로 겹친다.",
        "depth": wm.get("depth"),
        "depthRule": "무기 오버레이 바로 아래(같은 depth 규칙의 무기 직전). 무기가 몸 뒤로 가는 방향 행이면 스미어도 몸 뒤.",
        "blendMode": "NORMAL",
        "drawOver": "lightmap",
        "dirTransform": wm.get("dirTransform", "drawn4"),
        "smearFrames": sf,
        "sweepFrames": cfg["sweep"],
        "decayFrames": cfg["decay"],
        "glowFrames": sorted(glow & set(sf)),
        "impactFrame": wm.get("impactFrame"),
        "hitFrames": wm.get("hitFrames"),
        "timingMs": wm.get("timingMs"),
        "bladeTipAnchors": wm["bladeTipAnchors"],
        "gripAnchors": wm["gripAnchors"],
        "smearHeadAnchors": head,
        "smearTailAnchors": tail,
        "anchorNote": "§31-1 과 같다 — 좌표는 이 시트(= 무기 시트) 원 프레임 도트. null = 그 칸에 스미어 없음.",
        "weapon": "katana",
        "weaponColor": "서리 #8fe3ff(흰 끝 #e6fcff 는 판정 칸만)",
        "palette": "무기 색 램프(계약 §28 서리) + 판정 칸 X0 날선 — 새 색 없음. paletteSwap none",
        "paletteSwap": "none",
        "version": "v3-r62d",
        "source": SRC,
        "design": design,
    }
    if extra:
        meta.update(extra)
    rc.b2.write_sheet("fx", out_name, frames, fw, fh, meta, rows=len(dirs), durations=list(wm["frameDurationsMs"]), loop=False)
    return out_name, sf


def preview(path):
    from PIL import Image
    items = []
    for wname, sname in (("katana_spin", "katana_spin_smear"), ("katana_guardbreak", "katana_guardbreak_smear"),
                         ("katana_fall", "katana_fall_wide_smear"), ("katana_fall", "katana_fall_smear")):
        bm, bg = rc.load_grid("player/v3/player_" + wname)
        wm, wg = rc.load_grid("weapons/v3/" + wname)
        sm, sg = rc.load_grid("fx/v3/" + sname)
        fw, fh, n = wm["frameWidth"], wm["frameHeight"], wm["frames"]
        sf = sm["smearFrames"]
        cols = list(range(max(0, sf[0] - 1), min(n, sf[-1] + 2)))
        for r in range(len(wm["directions"])):
            strip = Image.new("RGBA", (len(cols) * fw, fh), (52, 46, 40, 255))
            for i, c in enumerate(cols):
                ox = i * fw
                body = rc.cell(bm, bg, r, c)
                strip.alpha_composite(body, (ox + wm["pivot"]["x"] - bm["pivot"]["x"], wm["pivot"]["y"] - bm["pivot"]["y"]))
                strip.alpha_composite(rc.cell(sm, sg, r, c), (ox, 0))
                strip.alpha_composite(rc.cell(wm, wg, r, c), (ox, 0))
            items.append(strip)
    rc.board(items, k=1, max_w=3000).save(path)


def build():
    res = [build_spin(), build_guard(), build_fall_wide()]
    rep = rc.b2.to_atlas()
    preview(os.path.join(HERE, "preview_smear_branch.png"))
    return res, rep
