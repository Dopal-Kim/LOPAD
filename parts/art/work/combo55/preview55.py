#!/usr/bin/env python3
"""55라운드 새 연격 미리보기 — 이 폴더에만 쓴다.

gif/katana_chain_<dirs>.gif           칼 1타 → 2타 → 3타(+잔상 베기) 실제 ms(다음 타는 앞 타 cancelAt 에서 시작), ×2
gif/katana_chain_<dirs>_hit.gif       같은 것 + 위에서 본 판정 모양(시안 선: 판정 프레임 동안 · 잔상 베기 2차 판정 포함)
gif/greatsword_chain_<dirs>.gif       H1 → V → H2 → V(관성 +5%씩 빨라짐) → 홀드 차지(0.4/0.8/1.2초 번쩍임) → 3단 차지 내려찍기 + 충격파 링, ×1
gif/greatsword_chain_<dirs>_hit.gif   같은 것 + 판정 모양(쐐기·끝점 충격원·링)
preview_mock_<무기>.png               1배 조명 합성(외곽 거리 바닥) — 동작별 판정 프레임, right · down
preview_fx_sheets.png                 새 이펙트 시트 전 프레임(right 또는 any 행) 1배
preview_body_<동작>_x2.png            몸 + 무기 전 프레임 2배(노란 테 = 판정 프레임)
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "fx_weapons_v3")))
import moves as M  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("fxw3_preview", os.path.join(HERE, "..", "fx_weapons_v3", "preview.py"))
FXP = importlib.util.module_from_spec(_spec)      # fx_weapons_v3/preview (조명 합성·바닥·글꼴) — 이름 충돌(hero_v3/preview) 피함
_spec.loader.exec_module(FXP)

ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
P3 = os.path.join(ROOT, "assets/sprites/player/v3")
W3 = os.path.join(ROOT, "assets/sprites/weapons/v3")
F3 = os.path.join(ROOT, "assets/sprites/fx/v3")
GIF = os.path.join(HERE, "gif")
BG = (30, 30, 35, 255)
HIT = (90, 230, 230, 255)
HIT2 = (120, 160, 255, 255)
BASE = {"right": 0.0, "down": 90.0, "left": 180.0, "up": -90.0}
HIT_UP = 40
_cache = {}


def load(folder, name):
    k = (folder, name)
    if k not in _cache:
        j = json.load(open(os.path.join(folder, name + ".json"), encoding="utf-8"))
        im = Image.open(os.path.join(folder, name + ".png")).convert("RGBA")
        _cache[k] = (j, im)
    return _cache[k]


def cell(j, im, d, i):
    dirs = j["directions"]
    r = dirs.index(d) if d in dirs else 0
    fw, fh = j["frameWidth"], j["frameHeight"]
    return im.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh))


def frame_at(ms, t):
    acc = 0
    for i, m in enumerate(ms):
        if t < acc + m:
            return i
        acc += m
    return None


# =============================================================================
# 타임라인
# =============================================================================
def katana_events():
    ev, t = [], 0
    for name in M.ORDER_K:
        mv = M.KATANA[name]
        ev.append(dict(move=name, start=t, rate=1.0))
        tm = M.timing(mv)
        t += tm["cancelAt"] if name != "katana_crescent" else tm["total"]
    fx = []
    for e in ev:
        for fname in FX_OF[e["move"]]:
            fx.append(fx_inst(fname, e))
    return ev, fx, t + 200


def gs_events():
    ev, t, rate = [], 0, 1.0
    seq = ["greatsword_sweep_cw", "greatsword_cleave", "greatsword_sweep_ccw", "greatsword_cleave"]
    for k, name in enumerate(seq):
        rate = 1.0 + min(0.20, 0.05 * k)               # 관성: 이어지는 타마다 +5%(최대 +20%)
        ev.append(dict(move=name, start=t, rate=rate))
        t += M.timing(M.GS[name])["cancelAt"] / rate
    hold0 = t
    ch = M.GS["greatsword_charge"]
    ev.append(dict(move="greatsword_charge", start=t, rate=1.0, hold=1300))
    t += 1300
    ev.append(dict(move="greatsword_charge_slam", start=t, rate=1.0, stage=3))
    end = t + M.timing(M.GS["greatsword_charge_slam"])["total"] + 120
    fx = []
    for e in ev:
        for fname in FX_OF[e["move"]]:
            if fname.startswith("greatsword_charge_slam_lv") and not fname.endswith(str(e.get("stage", 3))):
                continue
            fx.append(fx_inst(fname, e))
    for lv, sec in ((1, 0.4), (2, 0.8), (3, 1.2)):
        fx.append(dict(name="greatsword_charge_flash_lv%d" % lv, start=hold0 + sec * 1000, rate=1.0, ev=ev[-2]))
    return ev, fx, end


FX_OF = {"katana_rise": ["katana_rise"], "katana_fall": ["katana_fall"], "katana_crescent": ["katana_crescent", "katana_crescent_echo"],
         "greatsword_sweep_cw": ["greatsword_sweep_cw"], "greatsword_sweep_ccw": ["greatsword_sweep_ccw"],
         "greatsword_cleave": ["greatsword_cleave", "greatsword_cleave_impact"], "greatsword_charge": [],
         "greatsword_charge_slam": ["greatsword_charge_slam_lv3", "greatsword_cleave_impact", "greatsword_charge_ring"]}


def fx_inst(fname, e):
    j, _ = load(F3, fname)
    if "spawnAtMs" in j:
        st = j["spawnAtMs"]
    else:                                              # 끝점 시트: 몸 hitAt
        st = M.timing(M.KATANA.get(e["move"]) or M.GS[e["move"]])["hitAt"]
    scale = 1.0
    if fname == "greatsword_cleave_impact":
        scale = 1.3 if e["move"] == "greatsword_charge_slam" or e["rate"] >= 1.2 else 1.0
    return dict(name=fname, start=e["start"] + st / e["rate"], rate=e["rate"], ev=e, scale=scale)


def move_of(ev, t):
    cur = None
    for e in ev:
        if e["start"] <= t:
            cur = e
    return cur


def body_frame(e, t):
    mv = M.KATANA.get(e["move"]) or M.GS[e["move"]]
    lt = (t - e["start"]) * e["rate"]
    if "hold" in e:                                    # 차지: 들어 올림 후 루프
        ms = mv["ms"]
        lf = mv["loopFrames"]
        enter = sum(ms[:lf[0]])
        if lt < enter:
            return frame_at(ms, lt)
        per = sum(ms[i] for i in lf)
        q = (lt - enter) % per
        return lf[frame_at([ms[i] for i in lf], q)]
    i = frame_at(mv["ms"], lt)
    return len(mv["ms"]) - 1 if i is None else i


def wedge_len(e):
    hs = (M.GS[e["move"]])["hitShape"]
    R = M.dots(M.R_GS)
    if "lengthR" in hs:
        return R * hs["lengthR"]
    return R * hs["lengthRByStage"][e.get("stage", 3) - 1]


# =============================================================================
# 판정 모양(위에서 본) — 시안 선
# =============================================================================
def draw_hit(dr, e, d, origin, t, ox=0, oy=0):
    mv = M.KATANA.get(e["move"]) or M.GS[e["move"]]
    if mv.get("impact") is None:
        return
    tm = M.timing(mv)
    lt = (t - e["start"]) * e["rate"]
    shown = []
    if tm["hitAt"] <= lt < max(tm["activeEndAt"], tm["hitAt"] + 80):
        shown.append(("main", 1.0))
    if "echo" in mv:
        ea = tm["hitAt"] + mv["echo"]["delayMs"]
        if ea <= lt < ea + 70:
            shown.append(("echo", 1.0))
    if not shown:
        return
    base = math.radians(BASE[d])
    R = M.dots(M.R_KATANA if e["move"].startswith("katana") else M.R_GS)
    hs = mv["hitShape"]
    cx, cy = origin

    def P(a, r):
        return (cx + math.cos(base + math.radians(a)) * r, cy + math.sin(base + math.radians(a)) * r)
    for kind, _ in shown:
        col = HIT if kind == "main" else HIT2
        if hs["type"] == "arc":
            ro, ri = R * hs["radiusR"], R * hs["radiusR"] * hs["innerR"]
            a0, a1 = sorted((hs["startDeg"], hs["endDeg"]))
            pts = [P(a0 + (a1 - a0) * k / 40, ro) for k in range(41)]
            if ri > 1:
                pts += [P(a1 - (a1 - a0) * k / 40, ri) for k in range(41)]
            else:
                pts.append((cx, cy))
            dr.line(pts + [pts[0]], fill=col, width=2)
        else:
            L = wedge_len(e)
            half = hs["angleDeg"] / 2
            pts = [(cx, cy)] + [P(-half + 2 * half * k / 10, L) for k in range(11)] + [(cx, cy)]
            dr.line(pts, fill=col, width=2)
            rr = R * hs["impactCircle"]["radiusR"] * (1.3 if (e["rate"] >= 1.2 and e["move"] == "greatsword_cleave") else 1.0)
            ex, ey = P(0, L)
            dr.ellipse((ex - rr, ey - rr, ex + rr, ey + rr), outline=col, width=2)
            if e["move"] == "greatsword_charge_slam" and e.get("stage") == 3:
                pass


def draw_ring(dr, inst, d, origin, t):
    j, _ = load(F3, inst["name"])
    i = frame_at(j["frameDurationsMs"], (t - inst["start"]) * inst["rate"])
    if i is None or i > 2:
        return
    base = math.radians(BASE[d])
    L = wedge_len(inst["ev"])
    ex, ey = origin[0] + math.cos(base) * L, origin[1] + math.sin(base) * L
    r = j["ringRadiusPxByFrame"][i]
    dr.ellipse((ex - r, ey - r, ex + r, ey + r), outline=HIT2, width=2)


# =============================================================================
# 합성
# =============================================================================
def compose(ev, fx, t, d, S, hit=False, center=None):
    c = Image.new("RGBA", S, BG)
    px, py = center or (S[0] // 2, S[1] // 2 + 60)
    origin = (px, py - HIT_UP)
    e = move_of(ev, t)
    bj, bim = load(P3, "player_" + e["move"])
    wj, wim = load(W3, e["move"])
    i = body_frame(e, t)
    c.alpha_composite(cell(bj, bim, d, i), (px - bj["pivot"]["x"], py - bj["pivot"]["y"]))
    c.alpha_composite(cell(wj, wim, d, i), (px - wj["pivot"]["x"], py - wj["pivot"]["y"]))
    for inst in fx:
        if t < inst["start"]:
            continue
        j, im = load(F3, inst["name"])
        k = frame_at(j["frameDurationsMs"], (t - inst["start"]) * inst["rate"])
        if k is None:
            continue
        f = cell(j, im, d, k)
        if j["anchor"] == "player_pivot":
            c.alpha_composite(f, (px - j["pivot"]["x"], py - j["pivot"]["y"]))
        else:
            sc = inst.get("scale", 1.0)
            if sc != 1.0:
                f = f.resize((round(f.width * sc), round(f.height * sc)), Image.NEAREST)
            L = wedge_len(inst["ev"])
            base = math.radians(BASE[d])
            ex, ey = origin[0] + math.cos(base) * L, origin[1] + math.sin(base) * L
            c.alpha_composite(f, (round(ex - j["pivot"]["x"] * sc), round(ey - j["pivot"]["y"] * sc)))
    if hit:
        dr = ImageDraw.Draw(c)
        draw_hit(dr, e, d, origin, t)
        for inst in fx:
            if inst["name"] == "greatsword_charge_ring" and t >= inst["start"]:
                draw_ring(dr, inst, d, origin, t)
        dr.ellipse((origin[0] - 2, origin[1] - 2, origin[0] + 2, origin[1] + 2), fill=HIT)
    return c


def chain_gif(tag, ev, fx, end, dirs, S, scale, hit, title):
    bounds = {0.0, float(end)}
    for e in ev:
        mv = M.KATANA.get(e["move"]) or M.GS[e["move"]]
        acc = 0
        n = 40 if "hold" in e else 1
        for _ in range(n):
            for m in mv["ms"]:
                bounds.add(e["start"] + acc / e["rate"])
                acc += m
        bounds.add(e["start"] + acc / e["rate"])
    for inst in fx:
        j, _ = load(F3, inst["name"])
        acc = 0
        for m in j["frameDurationsMs"] + [0]:
            bounds.add(inst["start"] + acc / inst["rate"])
            acc += m
    if hit:
        for e in ev:
            mv = M.KATANA.get(e["move"]) or M.GS[e["move"]]
            if mv.get("impact") is not None:
                tm = M.timing(mv)
                for x in (tm["hitAt"], max(tm["activeEndAt"], tm["hitAt"] + 80)):
                    bounds.add(e["start"] + x / e["rate"])
                if "echo" in mv:
                    ea = tm["hitAt"] + mv["echo"]["delayMs"]
                    bounds.add(e["start"] + ea / e["rate"])
                    bounds.add(e["start"] + (ea + 70) / e["rate"])
    bs = sorted(b for b in bounds if 0 <= b <= end)
    frames, durs = [], []
    for a, b in zip(bs, bs[1:]):
        if b - a < 1:
            continue
        t = (a + b) / 2
        row = Image.new("RGBA", (S[0] * len(dirs) * scale, S[1] * scale + 22 * scale), BG)
        for k, d in enumerate(dirs):
            im = compose(ev, fx, t, d, S, hit)
            if scale != 1:
                im = im.resize((S[0] * scale, S[1] * scale), Image.NEAREST)
            row.alpha_composite(im, (k * S[0] * scale, 22 * scale))
        dr = ImageDraw.Draw(row)
        e = move_of(ev, t)
        FXP.label(dr, 6, 4, "%s · %s · t=%dms · %s%s" % (title, e["move"], t, "·".join(dirs),
                                                          ("  ×%.2f" % e["rate"]) if e["rate"] != 1 else ""))
        frames.append(row.convert("RGB").quantize(colors=128, dither=Image.Dither.NONE))
        durs.append(max(10, round(b - a)))
    # GIF 는 10ms 단위 — 반올림 오차를 마지막 프레임에서 흡수하지 않고 그대로 둔다(실제 ms 근사)
    os.makedirs(GIF, exist_ok=True)
    out = os.path.join(GIF, "%s_%s%s.gif" % (tag, "_".join(dirs), "_hit" if hit else ""))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=2, optimize=False)
    return out, len(frames), sum(durs)


# =============================================================================
# 1배 조명 목업
# =============================================================================
def mock(weapon):
    """1배 조명 합성 격자: 열 = 동작(판정 순간 hitAt + 15ms), 행 = right · down. 외곽 거리 바닥 albedo, 주변광 0.425/0.425/0.475."""
    names = M.ORDER_K + ["echo"] if weapon == "katana" else ["greatsword_sweep_cw", "greatsword_cleave", "greatsword_sweep_ccw",
                                                              "greatsword_charge_slam"]
    cw, ch = (420, 470) if weapon == "katana" else (700, 720)
    PIVS = {"right": (cw // 2, ch // 2 + 20), "down": (cw // 2, ch // 2 - 20)} if weapon == "katana" else \
        {"right": (int(cw * 0.3), ch // 2 + 30), "down": (cw // 2, int(ch * 0.3))}
    dirs = ("right", "down")
    W_, H_ = cw * len(names), ch * len(dirs)
    base = FXP.floor(W_, H_)
    lights, labels = [], []
    for c, name in enumerate(names):
        for r, d in enumerate(dirs):
            piv = PIVS[d]
            mvn = "katana_crescent" if name == "echo" else name
            mv = M.KATANA.get(mvn) or M.GS[mvn]
            e = dict(move=mvn, start=0, rate=1.0, stage=3)
            if name == "echo":
                fx = [fx_inst("katana_crescent_echo", e)]
                t = M.timing(mv)["hitAt"] + 150 + 15
                lab = "잔상 베기(+150ms) " + d
            else:
                fx = [fx_inst(f, e) for f in FX_OF[name] if not f.endswith("_echo") and f != "greatsword_charge_ring"]
                t = M.timing(mv)["hitAt"] + 15
                lab = "%s %s" % (mv["label"], d)
            im = _transparent(compose([e], fx, t, d, (cw, ch), center=piv))
            x0, y0 = c * cw, r * ch
            base.alpha_composite(im, (x0, y0))
            lights.append(dict(x=x0 + piv[0], y=y0 + piv[1] - 80, color="#b0611a", radius=150, intensity=0.75))
            labels.append((x0 + 8, y0 + 4, lab))
    lit = FXP.light_scene(base, lights)
    out = Image.new("RGB", (W_, H_ + 24), (18, 19, 22))
    out.paste(lit, (0, 24))
    dr = ImageDraw.Draw(out)
    FXP.label(dr, 6, 4, "1배(1920 내부 렌더) 조명 합성 · 몸 + 무기 + 새 이펙트(판정 순간 hitAt+15ms) · 외곽 거리 바닥 · 주변광 0.425/0.425/0.475 · 주인공 빛 r150 임시")
    for x, y, lab in labels:
        FXP.label(dr, x, y + 24, lab)
    for c in range(1, len(names)):
        dr.line((c * cw, 24, c * cw, H_ + 24), fill=(60, 60, 70))
    dr.line((0, ch + 24, W_, ch + 24), fill=(60, 60, 70))
    out.save(os.path.join(HERE, "preview_mock_%s.png" % weapon))


def _transparent(im):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y] == BG:
                px[x, y] = (0, 0, 0, 0)
    return im


# =============================================================================
# 시트 미리보기
# =============================================================================
def fx_sheets():
    import importlib.util
    spec = importlib.util.spec_from_file_location("build55", os.path.join(HERE, "build.py"))
    BLD = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(BLD)
    rows = []
    for n in BLD.FX_ORDER:
        j, im = load(F3, n)
        d = "right" if "right" in j["directions"] else "any"
        F = j["frames"]
        fw, fh = j["frameWidth"], j["frameHeight"]
        r = Image.new("RGBA", (F * (fw + 6) + 6, fh + 22), (24, 24, 28, 255))
        dr = ImageDraw.Draw(r)
        FXP.label(dr, 4, 3, "%s  %dx%d  f%d  ms %s  colors %d  glow %s  impact f%s" % (n, fw, fh, F, j["frameDurationsMs"], j["colors"],
                                                                                    j.get("glowFrames"), j.get("impactFrame")))
        for i in range(F):
            bg = Image.new("RGBA", (fw, fh), (44, 40, 46, 255) if i in (j.get("glowFrames") or []) else BG)
            bg.alpha_composite(cell(j, im, d, i))
            r.alpha_composite(bg, (6 + i * (fw + 6), 20))
        rows.append(r)
    W = max(r.width for r in rows)
    out = Image.new("RGBA", (W, sum(r.height + 4 for r in rows)), (12, 12, 14, 255))
    y = 0
    for r in rows:
        out.alpha_composite(r, (0, y))
        y += r.height + 4
    out.save(os.path.join(HERE, "preview_fx_sheets.png"))


def body_sheets():
    for name in M.ORDER_K + M.ORDER_G:
        bj, bim = load(P3, "player_" + name)
        wj, wim = load(W3, name)
        n = bj["frames"]
        fw, fh = wj["frameWidth"], wj["frameHeight"]
        ox, oy = wj["playerFrameOffset"]["x"], wj["playerFrameOffset"]["y"]
        k = 2
        out = Image.new("RGBA", (n * (fw * k + 6) + 70, 4 * (fh * k + 6) + 40), (46, 48, 56, 255))
        dr = ImageDraw.Draw(out)
        FXP.label(dr, 6, 6, "%s · %d프레임 · ms %s · 노란 테 = 판정(glowFrames) · 점 = 칼끝(bladeTipAnchors)" % (name, n, bj["frameDurationsMs"]))
        gl = set(bj.get("glowFrames") or [])
        for r, d in enumerate(bj["directions"]):
            y = 30 + r * (fh * k + 6)
            FXP.label(dr, 6, y + fh * k // 2, d)
            for i in range(n):
                x = 70 + i * (fw * k + 6)
                c = Image.new("RGBA", (fw, fh))
                c.alpha_composite(cell(bj, bim, d, i), (ox, oy))
                c.alpha_composite(cell(wj, wim, d, i))
                out.alpha_composite(c.resize((fw * k, fh * k), Image.NEAREST), (x, y))
                if i in gl:
                    dr.rectangle((x - 2, y - 2, x + fw * k + 1, y + fh * k + 1), outline=(240, 200, 60, 255), width=2)
                tip = wj["bladeTipAnchors"][d][i]
                if tip:
                    dr.ellipse((x + tip[0] * k - 3, y + tip[1] * k - 3, x + tip[0] * k + 3, y + tip[1] * k + 3), outline=(90, 230, 230, 255))
        out.save(os.path.join(HERE, "preview_body_%s_x2.png" % name))


def main(args=()):
    args = set(args)
    if not args or "sheets" in args:
        fx_sheets()
        body_sheets()
    if not args or "gif" in args:
        ev, fx, end = katana_events()
        for dirs in (("right", "down"), ("left", "up")):
            for hit in (False, True):
                print(chain_gif("katana_chain", ev, fx, end, dirs, (440, 440), 2, hit, "칼 K-A"))
        ev, fx, end = gs_events()
        for dirs in (("right", "down"), ("left", "up")):
            for hit in (False, True):
                print(chain_gif("greatsword_chain", ev, fx, end, dirs, (820, 820), 1, hit, "대검 G-C"))
    if not args or "mock" in args:
        mock("katana")
        mock("greatsword")
    print("preview ok")


if __name__ == "__main__":
    main(sys.argv[1:])
