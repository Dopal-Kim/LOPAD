#!/usr/bin/env python3
"""무기 이펙트 v3 미리보기.

preview_sheets_<무기>.png   시트별 한 줄(오른쪽 행 또는 any), 1배 실픽셀, 어두운 바닥색 위 (구 → 새 비교는 cmp_)
preview_cmp_<무기>.png      구 시트(×4 최근접 = 같은 화면 크기) ↔ v3, 대표 프레임
preview_mock_<무기>.png     1배 조명 합성: 몸 + 무기 오버레이 + 이펙트(판정 프레임), 외곽 거리 바닥 albedo 위
gif/<무기>_combo<n>_<dir>.gif  몸 + 무기 + 이펙트 실제 ms(1배 → 2배 확대)
preview_branch_<무기>.png   갈래 비교(기본 / A / B), 판정 프레임 + 다음 프레임
사용: python3 preview.py [katana greatsword dagger bow branch]
"""
import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wkit as W                                      # noqa: E402

ROOT = W.ROOT
FX3 = W.OUT_FX
P3 = os.path.join(ROOT, "assets/sprites/player/v3")
WP3 = os.path.join(ROOT, "assets/sprites/weapons/v3")
BG = (34, 33, 38, 255)
GIF = os.path.join(HERE, "gif")
EMISSIVE = {W.hexrgb(c) for c in (W.A21, W.A23, W.A25, W.A26, W.X1, W.X0)}


def font():
    for p in ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "/usr/share/fonts/opentype/unifont/unifont.otf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, 12)
    return ImageFont.load_default()


FONT = font()


def label(d, x, y, t, col=(230, 230, 230)):
    d.text((x, y), t, fill=col, font=FONT)


def load(path_noext):
    j = json.load(open(path_noext + ".json", encoding="utf-8"))
    im = Image.open(path_noext + ".png").convert("RGBA")
    return j, im


def cell(j, im, d, i):
    dirs = j["directions"]
    r = dirs.index(d) if d in dirs else 0
    fw, fh = j["frameWidth"], j["frameHeight"]
    return im.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh))


SHEET_GROUPS = {
    "katana": ["katana_combo1", "katana_combo2", "katana_combo3", "katana_slash", "iai", "wide", "batto", "zangetsu", "dashcrit",
               "longinvuln"],
    "greatsword": ["greatsword_combo1", "greatsword_combo2", "greatsword_combo3", "greatsword_slash", "greatsword_slam", "crush",
                   "weight", "quake", "pulverize", "giant", "guard_wave", "ironwall"],
    "dagger": ["dagger_combo1", "dagger_combo2", "dagger_combo3", "dagger_combo1_heat1", "dagger_combo1_heat2", "dagger_combo1_heat3",
               "dagger_combo3_heat3", "dagger_slash", "twin", "gale", "dance", "assassin", "afterimage", "shadowstep_ghost", "bleed"],
    "bow": ["bow_arrow", "bow_arrow_aimed", "heavyarrow", "bow_arrow_rapid", "bow_arrow_aimed_rapid", "bow_arrow_snipe",
            "bow_arrow_aimed_snipe", "bow_arrow_snipe_lv1", "bow_arrow_snipe_lv2", "bow_arrow_snipe_lv3", "bow_muzzle_rapid",
            "aim_charge", "aim_line", "aim_line_snipe", "heavyarrow_hit", "flash", "pierce", "muzzle_flash"],
}


def sheets(group, d="right", scale=1, maxw=4200):
    rows = []
    for n in SHEET_GROUPS[group]:
        p = os.path.join(FX3, n)
        if not os.path.exists(p + ".png"):
            continue
        j, im = load(p)
        F = j["frames"]
        fw, fh = j["frameWidth"], j["frameHeight"]
        s = scale * (4 if fw <= 64 and fh <= 32 else 1)
        r = Image.new("RGBA", (min(maxw, F * (fw * s + 6) + 6), fh * s + 22), BG)
        dr = ImageDraw.Draw(r)
        label(dr, 4, 3, "%s  %dx%d  f%d  colors %d%s" % (n, fw, fh, F, j.get("colors", 0), "  (x%d)" % s if s > 1 else ""))
        for i in range(F):
            c = cell(j, im, d, i)
            if s > 1:
                c = c.resize((fw * s, fh * s), Image.NEAREST)
            bg = Image.new("RGBA", c.size, (42, 40, 46, 255) if i in j.get("glowFrames", []) else BG)
            bg.alpha_composite(c)
            r.alpha_composite(bg, (6 + i * (fw * s + 6), 20))
        rows.append(r)
    if not rows:
        return
    out = Image.new("RGBA", (max(r.width for r in rows), sum(r.height + 4 for r in rows)), (18, 18, 22, 255))
    y = 0
    for r in rows:
        out.alpha_composite(r, (0, y))
        y += r.height + 4
    out.save(os.path.join(HERE, "preview_sheets_%s.png" % group))


# ------------------------------------------------------------------ 조명 합성(목업)
def light_scene(albedo, lights, ambient=(0.425, 0.425, 0.475), scale=4):
    """곱하기 조명 + 발광색(호박·백열) 원색 복원 + 번짐. 53라운드 목업 주변광 0.425/0.425/0.475."""
    Wd, Hd = albedo.size
    lw, lh = Wd // scale, Hd // scale
    lm = Image.new("RGB", (lw, lh))
    lp = lm.load()
    for y in range(lh):
        for x in range(lw):
            r, g, b = ambient
            for L in lights:
                d2 = ((x - L["x"] / scale) ** 2 + ((y - L["y"] / scale) * 1.15) ** 2) / (L["radius"] / scale) ** 2
                if d2 < 1.0:
                    f = (1 - d2) ** 2 * L["intensity"]
                    c = W.hexrgb(L["color"])
                    r += c[0] / 255 * f
                    g += c[1] / 255 * f
                    b += c[2] / 255 * f
            lp[x, y] = (min(255, int(r * 255 / 1.6)), min(255, int(g * 255 / 1.6)), min(255, int(b * 255 / 1.6)))
    lm = lm.resize((Wd, Hd), Image.BILINEAR)
    lit = ImageChops.multiply(albedo.convert("RGB"), lm).point(lambda v: min(255, int(v * 1.6)))
    ap, lp2 = albedo.load(), lit.load()
    emask = Image.new("L", (Wd, Hd), 0)
    ep = emask.load()
    for y in range(Hd):
        for x in range(Wd):
            c = ap[x, y]
            if c[:3] in EMISSIVE:
                lp2[x, y] = c[:3]
                ep[x, y] = 255
    glow = Image.new("RGB", (Wd, Hd))
    glow.paste(lit, (0, 0), emask)
    glow = glow.filter(ImageFilter.GaussianBlur(5)).point(lambda v: int(v * 0.8))
    return ImageChops.add(lit, glow)


def floor(w, h):
    p = os.path.join(ROOT, "parts/art/work/v2_outer/preview_mock_albedo.png")
    if os.path.exists(p):
        alb = Image.open(p).convert("RGBA")
        strip = alb.crop((300, 338, 600, 473)).resize((600, 270), Image.NEAREST)
    else:
        strip = Image.new("RGBA", (600, 270), (70, 66, 64, 255))
    out = Image.new("RGBA", (w, h))
    for x in range(0, w, 600):
        for y in range(0, h, 270):
            out.paste(strip if (x // 600) % 2 == 0 else strip.transpose(Image.FLIP_LEFT_RIGHT), (x, y))
    return out


def comp_body(weapon, n, d, body_i, fx_name, fx_i, body_sheet=None, wsheet=None):
    """→ (RGBA, 발 피벗 x, y) 몸 + 무기 + 이펙트 한 장."""
    bj, bim = load(os.path.join(P3, body_sheet or "player_%s_combo%d" % (weapon, n)))
    wj, wim = load(os.path.join(WP3, wsheet or "%s_combo%d" % (weapon, n)))
    fj, fim = load(os.path.join(FX3, fx_name))
    S = 760
    c = Image.new("RGBA", (S, S))
    px, py = S // 2, S // 2 + 120
    fb = cell(bj, bim, d, body_i)
    fw = cell(wj, wim, d, body_i)
    ff = cell(fj, fim, d, fx_i)
    below = fj.get("depth") in ("below", "floor")
    if below:
        c.alpha_composite(ff, (px - fj["pivot"]["x"], py - fj["pivot"]["y"]))
    c.alpha_composite(fb, (px - bj["pivot"]["x"], py - bj["pivot"]["y"]))
    c.alpha_composite(fw, (px - wj["pivot"]["x"], py - wj["pivot"]["y"]))
    if not below:
        c.alpha_composite(ff, (px - fj["pivot"]["x"], py - fj["pivot"]["y"]))
    return c, (px, py)


def glow_body_frame(bj):
    st = bj.get("frameStates") or []
    for i, s in enumerate(st):
        if s in ("glow", "full", "release"):
            return i
    return bj.get("impactFrame") or 0


def mock(weapon, spots, name, step=340, h=440):
    """spots: [(라벨, RGBA 640, 피벗)] → 1배 조명 합성."""
    w = step * len(spots) + 40
    base = floor(w, h)
    lights = []
    for k, (lab, im, piv) in enumerate(spots):
        cx = 40 + step * k + step // 2 - 20
        gy = h - 110
        base.alpha_composite(im, (cx - piv[0], gy - piv[1]))
        lights.append(dict(x=cx, y=gy - 80, color="#b0611a", radius=150, intensity=0.75))   # 주인공 빛 r140·0.75(임시값)
    lit = light_scene(base, lights)
    out = Image.new("RGB", (w, h + 40), (18, 19, 22))
    out.paste(lit, (0, 40))
    d = ImageDraw.Draw(out)
    label(d, 6, 4, "1배(1920 내부 렌더) 조명 합성 · 몸 + 무기 v3 + 이펙트 v3(판정 프레임) · 외곽 거리 바닥 · 주변광 0.425/0.425/0.475")
    for k, (lab, im, piv) in enumerate(spots):
        label(d, 40 + step * k + step // 2 - 60, 22, lab)
    out.save(os.path.join(HERE, name))


def combo_mock(weapon, ncombo=3):
    spots = []
    for n in range(1, ncombo + 1):
        for d in ("right", "down"):
            bj, _ = load(os.path.join(P3, "player_%s_combo%d" % (weapon, n)))
            fj, _ = load(os.path.join(FX3, "%s_combo%d" % (weapon, n)))
            bi = glow_body_frame(bj)
            im, piv = comp_body(weapon, n, d, bi, "%s_combo%d" % (weapon, n), fj["impactFrame"])
            spots.append(("%d타 %s" % (n, d), im, piv))
    big = weapon == "greatsword"
    mock(weapon, spots, "preview_mock_%s.png" % weapon, step=520 if big else 340, h=560 if big else 440)


def combo_gif(weapon, n, d, fx_name=None, tag=None):
    """몸·무기 시트 시간축 위에 이펙트를 '몸 판정 프레임 시작 = 이펙트 impactFrame 시작' 으로 맞춰 재생."""
    fx_name = fx_name or "%s_combo%d" % (weapon, n)
    bj, bim = load(os.path.join(P3, "player_%s_combo%d" % (weapon, n)))
    wj, wim = load(os.path.join(WP3, "%s_combo%d" % (weapon, n)))
    fj, fim = load(os.path.join(FX3, fx_name))
    bms, fms = bj["frameDurationsMs"], fj["frameDurationsMs"]
    bi = glow_body_frame(bj)
    t_hit = sum(bms[:bi])
    t0 = t_hit - sum(fms[:fj["impactFrame"]])
    bounds = sorted(set([sum(bms[:k]) for k in range(len(bms) + 1)] + [t0 + sum(fms[:k]) for k in range(len(fms) + 1)]))
    end = max(sum(bms), t0 + sum(fms))
    frames, durs = [], []
    S = 760 if weapon == "greatsword" else 520
    for a, b in zip(bounds, bounds[1:]):
        if b <= a or a >= end:
            continue
        tb = a
        k = 0
        while k < len(bms) - 1 and tb >= sum(bms[:k + 1]):
            k += 1
        c = Image.new("RGBA", (S, S), BG)
        px, py = S // 2, S // 2 + 100
        fx_i = None
        if a >= t0:
            q = 0
            while q < len(fms) and a >= t0 + sum(fms[:q + 1]):
                q += 1
            fx_i = q if q < len(fms) else None
        below = fj.get("depth") in ("below", "floor")
        if fx_i is not None and below:
            c.alpha_composite(cell(fj, fim, d, fx_i), (px - fj["pivot"]["x"], py - fj["pivot"]["y"]))
        c.alpha_composite(cell(bj, bim, d, k), (px - bj["pivot"]["x"], py - bj["pivot"]["y"]))
        c.alpha_composite(cell(wj, wim, d, k), (px - wj["pivot"]["x"], py - wj["pivot"]["y"]))
        if fx_i is not None and not below:
            c.alpha_composite(cell(fj, fim, d, fx_i), (px - fj["pivot"]["x"], py - fj["pivot"]["y"]))
        frames.append(c.convert("RGB").quantize(colors=96, dither=Image.Dither.NONE))
        durs.append(max(20, b - a))
    os.makedirs(GIF, exist_ok=True)
    frames[0].save(os.path.join(GIF, "%s_%s.gif" % (tag or fx_name, d)), save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, disposal=2)


def cmp(group, names):
    """구(×4 최근접) ↔ v3, 각 시트의 판정(또는 가운데) 프레임, 오른쪽 행."""
    cells = []
    for n in names:
        p = os.path.join(FX3, n)
        if not os.path.exists(p + ".png"):
            continue
        j, im = load(p)
        oj, oim = load(os.path.join(W.OLD_FX, n))
        i = j.get("impactFrame", (j.get("glowFrames") or [j["frames"] // 2])[0])
        i = min(i + (1 if j["frames"] > 3 else 0), j["frames"] - 1)
        o = cell(oj, oim, "right", i).resize((oj["frameWidth"] * 4, oj["frameHeight"] * 4), Image.NEAREST)
        nw = cell(j, im, "right", i)
        cells.append((n, i, o, nw))
    if not cells:
        return
    wmax = max(c[2].width for c in cells)
    out = Image.new("RGBA", (len(cells) * (wmax + 8) + 8, 2 * max(c[2].height for c in cells) + 50), BG)
    dr = ImageDraw.Draw(out)
    for k, (n, i, o, nw) in enumerate(cells):
        x = 8 + k * (wmax + 8)
        label(dr, x, 2, "%s f%d (위 구 x4 · 아래 v3)" % (n, i))
        out.alpha_composite(o, (x, 20))
        out.alpha_composite(nw, (x, 30 + o.height))
    out.save(os.path.join(HERE, "preview_cmp_%s.png" % group))


def main(args):
    groups = args or ["katana", "greatsword", "dagger", "bow", "branch"]
    for g in groups:
        if g in SHEET_GROUPS:
            sheets(g)
            cmp(g, [n for n in SHEET_GROUPS[g] if "combo" in n][:3])
        if g in ("katana", "greatsword", "dagger"):
            combo_mock(g)
            for n in (1, 2, 3):
                combo_gif(g, n, "right")
            combo_gif(g, 3, "down")
        if g == "bow":
            import preview_bow
            preview_bow.main()
        if g == "branch":
            import preview_branch
            preview_branch.main()
        print("preview", g, "ok")


if __name__ == "__main__":
    main(sys.argv[1:])
