#!/usr/bin/env python3
"""56라운드 미리보기 — 이 폴더에만 쓴다.

preview_body_<동작>_x2.png          칼 몸 + 무기 전 프레임 2배(노란 테 = 판정, 파란 테 = 돌진)
preview_fx_sheets.png                새 붓획 이펙트 시트 전 프레임(right 행) 1배
gif/brush_<무기>_<dirs>.gif          무기별 붓획 연격(실제 ms, 다음 타는 앞 타 cancelAt 에서 시작)
gif/issen_<dirs>.gif                 칼 3연격(1타 → 2타 → 일섬 + 그림자 분신) 실제 ms, 돌진 이동 포함
preview_cmp_55_56_<무기>.png         55(이전) ↔ 56 같은 시각 비교(판정 순간 hitAt+15ms, 1배 조명 합성)
preview_mock_issen.png               일섬·분신 단계별 1배 조명 합성
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("fxw3_preview", os.path.join(HERE, "..", "fx_weapons_v3", "preview.py"))
FXP = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(FXP)

ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
P3 = os.path.join(ROOT, "assets/sprites/player/v3")
W3 = os.path.join(ROOT, "assets/sprites/weapons/v3")
F3 = os.path.join(ROOT, "assets/sprites/fx/v3")
OLD = os.path.join(HERE, "prev55")
GIF = os.path.join(HERE, "gif")
BG = (30, 30, 35, 255)
BASE = {"right": 0.0, "down": 90.0, "left": 180.0, "up": -90.0}
DV = {"right": (1, 0), "left": (-1, 0), "down": (0, 1), "up": (0, -1)}
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


def starts(ms):
    s, t = [], 0
    for m in ms:
        s.append(t)
        t += m
    return s


# =============================================================================
# 몸 시트
# =============================================================================
def body_sheets(names=("katana_rise", "katana_fall", "katana_issen")):
    for name in names:
        bj, bim = load(P3, "player_" + name)
        wj, wim = load(W3, name)
        n = bj["frames"]
        fw, fh = wj["frameWidth"], wj["frameHeight"]
        ox, oy = wj["playerFrameOffset"]["x"], wj["playerFrameOffset"]["y"]
        k = 2
        out = Image.new("RGBA", (n * (fw * k + 6) + 70, 4 * (fh * k + 6) + 40), (46, 48, 56, 255))
        dr = ImageDraw.Draw(out)
        FXP.label(dr, 6, 6, "%s · %d프레임 · ms %s · 노란 테 = 판정 · 파란 테 = 돌진(dashFrames)" % (name, n, bj["frameDurationsMs"]))
        gl = set(bj.get("glowFrames") or [])
        dash = set(bj.get("dashFrames") or [])
        for r, d in enumerate(bj["directions"]):
            y = 30 + r * (fh * k + 6)
            FXP.label(dr, 6, y + fh * k // 2, d)
            for i in range(n):
                x = 70 + i * (fw * k + 6)
                c = Image.new("RGBA", (fw, fh))
                c.alpha_composite(cell(bj, bim, d, i), (ox, oy))
                c.alpha_composite(cell(wj, wim, d, i))
                out.alpha_composite(c.resize((fw * k, fh * k), Image.NEAREST), (x, y))
                if i in dash:
                    dr.rectangle((x - 4, y - 4, x + fw * k + 3, y + fh * k + 3), outline=(90, 140, 255, 255), width=2)
                if i in gl:
                    dr.rectangle((x - 2, y - 2, x + fw * k + 1, y + fh * k + 1), outline=(240, 200, 60, 255), width=2)
        out.save(os.path.join(HERE, "preview_body_%s_x2.png" % name))


# =============================================================================
# fx 시트
# =============================================================================
def fx_sheets(names=None, out="preview_fx_sheets.png", row=None, k=1):
    spec = importlib.util.spec_from_file_location("build56", os.path.join(HERE, "build.py"))
    BLD = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(BLD)
    names = names or BLD.FX_ORDER + ["katana_issen_shadow"]
    rows = []
    for n in names:
        if not os.path.exists(os.path.join(F3, n + ".json")):
            continue
        j, im = load(F3, n)
        d = row or ("right" if "right" in j["directions"] else j["directions"][0])
        if d not in j["directions"]:
            d = j["directions"][0]
        F = j["frames"]
        fw, fh = j["frameWidth"], j["frameHeight"]
        r = Image.new("RGBA", ((F * (fw + 6) + 6) * k, fh * k + 22), (24, 24, 28, 255))
        dr = ImageDraw.Draw(r)
        FXP.label(dr, 4, 3, "%s [%s]  %dx%d  f%d  ms %s  colors %d  glow %s  impact f%s" % (n, d, fw, fh, F, j["frameDurationsMs"], j["colors"],
                                                                                      j.get("glowFrames"), j.get("impactFrame")))
        for i in range(F):
            bg = Image.new("RGBA", (fw, fh), (44, 40, 46, 255) if i in (j.get("glowFrames") or []) else BG)
            bg.alpha_composite(cell(j, im, d, i))
            if k != 1:
                bg = bg.resize((fw * k, fh * k), Image.NEAREST)
            r.alpha_composite(bg, ((6 + i * (fw + 6)) * k, 20))
        rows.append(r)
    W = max(r.width for r in rows)
    img = Image.new("RGBA", (W, sum(r.height + 4 for r in rows)), (12, 12, 14, 255))
    y = 0
    for r in rows:
        img.alpha_composite(r, (0, y))
        y += r.height + 4
    img.save(os.path.join(HERE, out))
    return os.path.join(HERE, out)


# =============================================================================
# 타임라인(몸·무기·fx 합성)
# =============================================================================
def mv_json(folder_p, name):
    return load(folder_p, "player_" + name)


def tm(j):
    return j["timingMs"]


def fx_start_for(fj, ev, bj, align=False):
    """fx 시트 시작 시각(몸 기준) — spawnAtMs 가 있으면 그것, 없으면(단검 등) hitAt − impactFrame 앞 프레임 합.
    align = 55 사본 비교용: 몸 타이밍이 바뀌었으므로(작업 B 대검) 판정 프레임을 현재 몸 hitAt 에 맞춤."""
    if align and fj.get("anchor") == "player_pivot" and "impactFrame" in fj:
        return tm(bj)["hitAt"] - sum(fj["frameDurationsMs"][:fj["impactFrame"]])
    if "spawnAtMs" in fj and fj.get("anchor") != "hitbox_center":
        return fj["spawnAtMs"]
    if fj.get("anchor") == "hitbox_center":
        return tm(bj)["hitAt"]
    return tm(bj)["hitAt"] - sum(fj["frameDurationsMs"][:fj.get("impactFrame", 1)])


def make_events(seq, P=P3, Wd=W3, Fd=F3, fx_of=None, rates=None, gap=0, align=False):
    """seq = [동작] — 다음 동작은 앞 동작 cancelAt(없으면 total)에서 시작."""
    ev, fx, t = [], [], 0
    for k, name in enumerate(seq):
        bj, _ = load(P, "player_" + name)
        rate = rates[k] if rates else 1.0
        e = dict(move=name, start=t, rate=rate, P=P, Wd=Wd)
        ev.append(e)
        for fname in (fx_of or {}).get(name, []):
            fd = Fd if os.path.exists(os.path.join(Fd, fname + ".json")) else F3     # 55 사본에 없는 시트(끝점 충격 등)는 현행
            fj, _ = load(fd, fname)
            fx.append(dict(name=fname, start=t + fx_start_for(fj, e, bj, align) / rate, rate=rate, ev=e, F=fd))
        c = tm(bj).get("cancelAt") or tm(bj)["total"]
        t += (c if k < len(seq) - 1 else tm(bj)["total"]) / rate + gap
    return ev, fx, t + 160


def move_of(ev, t):
    cur = ev[0]
    for e in ev:
        if e["start"] <= t:
            cur = e
    return cur


def player_offset(ev, t, d):
    """일섬 돌진 이동(도트) — 그 앞 동작은 0, 일섬 dash 동안 선형, 그 뒤 최종 거리."""
    off = 0.0
    for e in ev:
        if e["move"] != "katana_issen" or t < e["start"]:
            continue
        bj, _ = load(e["P"], "player_katana_issen")
        ds = bj["dash"]
        lt = (t - e["start"]) * e["rate"]
        L = ds["distancePx"]["dots"]
        off = 0.0 if lt < ds["startMs"] else L if lt >= ds["endMs"] else L * (lt - ds["startMs"]) / (ds["endMs"] - ds["startMs"])
    dx, dy = DV[d]
    return dx * off, dy * off


def issen_points(ev, d):
    for e in ev:
        if e["move"] == "katana_issen":
            bj, _ = load(e["P"], "player_katana_issen")
            L = bj["dash"]["distancePx"]["dots"]
            return (0.0, 0.0), (DV[d][0] * L, DV[d][1] * L), e
    return None


def compose(ev, fx, t, d, S, center):
    c = Image.new("RGBA", S, BG)
    e = move_of(ev, t)
    ox, oy = player_offset(ev, t, d)
    px, py = round(center[0] + ox), round(center[1] + oy)
    bj, bim = load(e["P"], "player_" + e["move"])
    wj, wim = load(e["Wd"], e["move"])
    lt = (t - e["start"]) * e["rate"]
    i = frame_at(bj["frameDurationsMs"], lt)
    i = bj["frames"] - 1 if i is None else i
    under, over = [], []
    for inst in fx:
        if t < inst["start"]:
            continue
        j, im = load(inst["F"], inst["name"])
        k = frame_at(j["frameDurationsMs"], (t - inst["start"]) * inst["rate"])
        if k is None:
            continue
        f = cell(j, im, d, k)
        if j["anchor"] in ("dash_start_pivot",):
            pos = (center[0] - j["pivot"]["x"], center[1] - j["pivot"]["y"])
            under.append((f, pos))                            # depth below_player
            continue
        elif j["anchor"] == "issen_shadow_path":
            (sx, sy), (ex, ey), _ = issen_points(ev, d)
            lt2 = (t - inst["start"]) * inst["rate"]
            q = min(1.0, lt2 / j["travelMs"])
            pos = (round(center[0] + sx + (ex - sx) * q - j["pivot"]["x"]), round(center[1] + sy + (ey - sy) * q - j["pivot"]["y"]))
            under.append((f, pos))
            continue
        elif j["anchor"] == "hitbox_center":
            bjj, _ = load(inst["ev"]["P"], "player_" + inst["ev"]["move"])
            hs = bjj.get("hitShape", {})
            L = hs.get("lengthPx") or (hs.get("lengthPxByStage") or [0, 0, 0])[-1]
            base = math.radians(BASE[d])
            pos = (round(px + math.cos(base) * L - j["pivot"]["x"]), round(py - HIT_UP + math.sin(base) * L - j["pivot"]["y"]))
        else:
            ipx, ipy = player_offset(ev, inst["start"] + 1, d)
            pos = (round(center[0] + ipx - j["pivot"]["x"]), round(center[1] + ipy - j["pivot"]["y"]))
        over.append((f, pos))
    for f, pos in under:
        c.alpha_composite(f, pos)
    c.alpha_composite(cell(bj, bim, d, i), (px - bj["pivot"]["x"], py - bj["pivot"]["y"]))
    c.alpha_composite(cell(wj, wim, d, i), (px - wj["pivot"]["x"], py - wj["pivot"]["y"]))
    for f, pos in over:
        c.alpha_composite(f, pos)
    return c


def chain_gif(tag, ev, fx, end, dirs, S, centers, title, scale=1):
    bounds = {0.0, float(end)}
    for e in ev:
        bj, _ = load(e["P"], "player_" + e["move"])
        acc = 0
        for m in bj["frameDurationsMs"] + [0]:
            bounds.add(e["start"] + acc / e["rate"])
            acc += m
        if e["move"] == "katana_issen":                      # 돌진 이동은 10ms 단위로 촘촘히
            for x in range(bj["dash"]["startMs"], bj["dash"]["endMs"], 20):
                bounds.add(e["start"] + x)
    for inst in fx:
        j, _ = load(inst["F"], inst["name"])
        acc = 0
        for m in j["frameDurationsMs"] + [0]:
            bounds.add(inst["start"] + acc / inst["rate"])
            acc += m
        if j.get("anchor") == "issen_shadow_path":
            for x in range(0, j["travelMs"], 20):
                bounds.add(inst["start"] + x)
    bs = sorted(b for b in bounds if 0 <= b <= end)
    frames, durs = [], []
    for a, b in zip(bs, bs[1:]):
        if b - a < 1:
            continue
        t = (a + b) / 2
        row = Image.new("RGBA", (S[0] * len(dirs) * scale, S[1] * scale + 22), BG)
        for k, d in enumerate(dirs):
            im = compose(ev, fx, t, d, S, centers[d])
            if scale != 1:
                im = im.resize((S[0] * scale, S[1] * scale), Image.NEAREST)
            row.alpha_composite(im, (k * S[0] * scale, 22))
        dr = ImageDraw.Draw(row)
        e = move_of(ev, t)
        FXP.label(dr, 6, 4, "%s · %s · t=%dms%s" % (title, e["move"], t, ("  ×%.2f" % e["rate"]) if e["rate"] != 1 else ""))
        frames.append(row.convert("RGB").quantize(colors=160, dither=Image.Dither.NONE))
        durs.append(max(10, round(b - a)))
    os.makedirs(GIF, exist_ok=True)
    out = os.path.join(GIF, "%s_%s.gif" % (tag, "_".join(dirs)))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=2, optimize=False)
    return out, len(frames), sum(durs)


FX56 = {"katana_rise": ["katana_rise"], "katana_fall": ["katana_fall"],
        "katana_issen": ["katana_issen_line_t4", "katana_issen_shadow"],
        "greatsword_sweep_cw": ["greatsword_sweep_cw"], "greatsword_sweep_ccw": ["greatsword_sweep_ccw"],
        "greatsword_cleave": ["greatsword_cleave", "greatsword_cleave_impact"],
        "greatsword_charge_slam": ["greatsword_charge_slam_lv3", "greatsword_cleave_impact"],
        "dagger_combo1": ["dagger_combo1"], "dagger_combo2": ["dagger_combo2"], "dagger_combo3": ["dagger_combo3"]}
FX55 = dict(FX56, katana_crescent=["katana_crescent", "katana_crescent_echo"])
GS_SEQ = ["greatsword_sweep_cw", "greatsword_cleave", "greatsword_sweep_ccw", "greatsword_cleave"]
GS_RATES = [1.0, 1.05, 1.10, 1.15]


def gifs():
    res = []
    # 칼: 1타 → 2타 → 일섬(+ 일섬 선 · 그림자 분신)
    ev, fx, end = make_events(["katana_rise", "katana_fall", "katana_issen"], fx_of=FX56)
    for dirs in (("right", "down"), ("left", "up")):
        res.append(chain_gif("issen_chain", ev, fx, end + 200, dirs, (560, 640),
                             {"right": (130, 360), "left": (430, 360), "down": (280, 150), "up": (280, 560)}, "칼 56 · 1타→2타→일섬+분신"))
    # 칼 1·2타 붓획만 2배
    ev2, fx2, end2 = make_events(["katana_rise", "katana_fall"], fx_of=FX56)
    res.append(chain_gif("brush_katana", ev2, fx2, end2, ("right", "down"), (420, 420), {"right": (200, 250), "down": (210, 190)},
                         "칼 붓획(56 템포)", scale=2))
    # 대검 H1 → V → H2 → V(관성)
    ev3, fx3, end3 = make_events(GS_SEQ, fx_of=FX56, rates=GS_RATES)
    res.append(chain_gif("brush_greatsword", ev3, fx3, end3, ("right", "down"), (760, 760), {"right": (300, 420), "down": (380, 300)},
                         "대검 붓획"))
    # 단검 1 → 2 → 3
    ev4, fx4, end4 = make_events(["dagger_combo1", "dagger_combo2", "dagger_combo3"], fx_of=FX56)
    res.append(chain_gif("brush_dagger", ev4, fx4, end4 + 200, ("right", "down"), (420, 360), {"right": (150, 220), "down": (210, 140)},
                         "단검 붓획(Q4 ×1.5)", scale=2))
    # 55 대비 같은 연격(55 시트, 55 템포)
    P55 = os.path.join(OLD, "player")
    W55 = os.path.join(OLD, "weapons")
    F55 = os.path.join(OLD, "fx")
    ev5, fx5, end5 = make_events(["katana_rise", "katana_fall", "katana_crescent"], P=P55, Wd=W55, Fd=F55, fx_of=FX55)
    res.append(chain_gif("prev55_katana", ev5, fx5, end5, ("right", "down"), (420, 420), {"right": (200, 250), "down": (210, 190)},
                         "칼 55(이전)", scale=2))
    for r in res:
        print(r)
    return res


# =============================================================================
# 1배 조명 합성 — 55 ↔ 56 비교 · 일섬 단계
# =============================================================================
def _transparent(im):
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y] == BG:
                px[x, y] = (0, 0, 0, 0)
    return im


def lit_grid(cells, cw, ch, ncol, nrow, title, out):
    """cells = [(col, row, ev, fx, t, d, center, label)]."""
    W_, H_ = cw * ncol, ch * nrow
    base = FXP.floor(W_, H_)
    lights, labels = [], []
    for c, r, ev, fx, t, d, cen, lab in cells:
        im = _transparent(compose(ev, fx, t, d, (cw, ch), cen))
        x0, y0 = c * cw, r * ch
        base.alpha_composite(im, (x0, y0))
        ox, oy = player_offset(ev, t, d)
        lights.append(dict(x=x0 + cen[0] + ox, y=y0 + cen[1] + oy - 80, color="#b0611a", radius=150, intensity=0.75))
        labels.append((x0 + 8, y0 + 4, lab))
    lit = FXP.light_scene(base, lights)
    img = Image.new("RGB", (W_, H_ + 24), (18, 19, 22))
    img.paste(lit, (0, 24))
    dr = ImageDraw.Draw(img)
    FXP.label(dr, 6, 4, title)
    for x, y, lab in labels:
        FXP.label(dr, x, y + 24, lab)
    for c in range(1, ncol):
        dr.line((c * cw, 24, c * cw, H_ + 24), fill=(60, 60, 70))
    for r in range(1, nrow):
        dr.line((0, r * ch + 24, W_, r * ch + 24), fill=(60, 60, 70))
    img.save(os.path.join(HERE, out))
    return os.path.join(HERE, out)


def cmp_55_56():
    P55, W55, F55 = (os.path.join(OLD, k) for k in ("player", "weapons", "fx"))
    outs = []
    specs = {
        "katana": (["katana_rise", "katana_fall"], dict(P=P55, Wd=W55, Fd=F55), (440, 440), {"right": (200, 250), "down": (220, 190)}),
        "greatsword": (["greatsword_sweep_cw", "greatsword_cleave", "greatsword_sweep_ccw"], dict(Fd=F55, align=True), (720, 720),
                       {"right": (230, 380), "down": (360, 230)}),
        "dagger": (["dagger_combo1", "dagger_combo2", "dagger_combo3"], dict(Fd=F55, align=True), (420, 360), {"right": (130, 220), "down": (210, 110)}),
    }
    for weapon, (seq, old_kw, S, cen) in specs.items():
        cells = []
        for c, name in enumerate(seq):
            for k, (ver, kw) in enumerate((("55", old_kw), ("56", {}))):
                ev, fx, _ = make_events([name], fx_of=FX56, **kw)
                bj, _ = load(ev[0]["P"], "player_" + name)
                for r2, (dt, tag) in enumerate(((15, "판정 +15ms"), (95, "+95ms"))):
                    t = tm(bj)["hitAt"] + dt
                    for r3, d in enumerate(("right", "down")):
                        row = (r3 * 2 + r2) * 2 + k
                        cells.append((c, row, ev, fx, t, d, cen[d], "%s %s %s %s" % (ver, name, d, tag)))
        outs.append(lit_grid(cells, S[0], S[1], len(seq), 8,
                             "55(이전 부분 초승달) ↔ 56(붓획) · %s · 1배 조명 합성 · 같은 행 쌍 = 같은 시각 · 칼 56 은 사거리 ×1.15·새 템포" % weapon,
                             "preview_cmp_55_56_%s.png" % weapon))
    return outs


def issen_mock():
    ev, fx, _ = make_events(["katana_issen"], fx_of=FX56)
    bj, _ = load(P3, "player_katana_issen")
    d0 = bj["dash"]["startMs"]
    stages = [(d0 - 60, "발도 자세"), (d0 + 50, "돌진 판정(백열 머리)"), (d0 + 130, "도착 · 선 완성"), (d0 + 225, "분신 출발"),
              (d0 + 300, "분신 지나감"), (d0 + 365, "터짐(분신 판정)"), (d0 + 470, "재")]
    cen = {"right": (110, 300), "left": (560, 300), "down": (330, 110), "up": (330, 560)}
    cells = []
    for c, (t, lab) in enumerate(stages):
        for r, d in enumerate(("right", "left", "down", "up")):
            cells.append((c, r, ev, fx, t, d, cen[d], "%s %s t=%d" % (lab, d, t - d0)))
    return lit_grid(cells, 680, 680, len(stages), 4,
                    "일섬(4칸 = 256 도트) + 그림자 분신 · 1배 조명 합성 · t = 돌진 시작 기준 ms", "preview_mock_issen.png")


def main(args=()):
    args = set(args)
    if not args or "sheets" in args:
        body_sheets()
        fx_sheets()
    if not args or "gif" in args:
        gifs()
    if not args or "mock" in args:
        print(cmp_55_56())
        print(issen_mock())
    print("preview ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "fx":
        print(fx_sheets(a[1:] or None, out="preview_fx_tmp.png" if len(a) > 1 else "preview_fx_sheets.png"))
    else:
        main(a)
