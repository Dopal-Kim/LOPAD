"""전/후 비교 → parts/art/work/color61s6/preview_<weapon>.png (+ _misc). 전 = git HEAD(이 작업 전 커밋), 후 = 작업 트리.
  preview_<weapon>.png      1) 1층 어두운 연회장 바닥 + 호박 램프 빛 위 장면(몸·무기·fx 같은 시각, fx 는 조명 위) 전/후
                            2) 주요 무기 fx 줄(오른쪽 행) 전/후 — 어두운 바닥 0.5
  preview_<weapon>_misc.png 개성 fx · 오버레이(검기·각성·귀화) · looks · 카드 그림 전/후
사용: python3 preview.py [katana dagger] [--rev HEAD]"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view as V  # noqa: E402

REV = "HEAD"
BG = (14, 13, 16, 255)


def starts(ms):
    o, t = [], 0
    for m in ms:
        o.append(t)
        t += m
    return o


_cache = {}


def sheet(rel, rev):
    k = (rel, rev)
    if k not in _cache:
        _cache[k] = V.load(rel, rev)
    return _cache[k]


def frame(rel, rev, row, col):
    m, sh = sheet(rel, rev)
    dirs = m.get("directions") or ["any"]
    fw = m.get("frameWidth") or m["atlas"]["grid"]["frameWidth"]
    fh = m.get("frameHeight") or m["atlas"]["grid"]["frameHeight"]
    r = row if len(dirs) > 1 else 0
    return sh.crop((col * fw, r * fh, (col + 1) * fw, (r + 1) * fh)), m


def lamp_floor(w, h, lamp=(0.25, 0.3), dark=0.32):
    """1층 연회장 바닥 — 어둠 + 호박 램프 한 개(왼쪽 위) 빛."""
    bg = V.floor_bg(w, h, 1.0)
    px = bg.load()
    lx, ly = lamp[0] * w, lamp[1] * h
    R = max(w, h) * 0.55
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - lx, y - ly) / R
            f = max(0.0, 1.0 - d) ** 1.6
            r, g, b, a = px[x, y]
            px[x, y] = (min(255, int(r * (dark + 0.85 * f))), min(255, int(g * (dark + 0.6 * f))), min(255, int(b * (dark + 0.3 * f))), 255)
    return bg


def light_sprite(im, k=(0.62, 0.52, 0.42)):
    """몸·무기는 조명 아래(호박 램프 + 어둠) — 대충 곱."""
    out = im.copy()
    p = out.load()
    for y in range(im.height):
        for x in range(im.width):
            c = p[x, y]
            if c[3]:
                p[x, y] = (int(c[0] * k[0]), int(c[1] * k[1]), int(c[2] * k[2]), c[3])
    return out


def fx_col(body_m, fx_m, col):
    sp = fx_m.get("spawnAtMs")
    if sp is None:
        return None
    t = starts(body_m["frameDurationsMs"])[col] + 1
    dt = t - sp
    if dt < 0:
        return None
    st = starts(fx_m["frameDurationsMs"])
    for i in range(len(st) - 1, -1, -1):
        if dt >= st[i]:
            return i if dt < st[i] + fx_m["frameDurationsMs"][i] else None
    return None


def scene(rev, body, layers, fx, row, col, fxc=None, size=(520, 440), anchor=(260, 300)):
    cv = lamp_floor(*size)
    b, bm = frame("player/v3/" + body, REV, row, col)          # 몸은 바뀌지 않음
    bp = bm.get("pivot", {"x": 48, "y": 138})
    cv.alpha_composite(light_sprite(b), (anchor[0] - bp["x"], anchor[1] - bp["y"]))
    for rel in layers:
        w, wm = frame(rel, rev, row, col)
        p = wm.get("pivot", {"x": 96, "y": 186})
        lit = rel.endswith(("_ki1", "_ki2", "_ki3")) or "_glow" in rel
        cv.alpha_composite(w if lit else light_sprite(w), (anchor[0] - p["x"], anchor[1] - p["y"]))
    if fx:
        fm, _ = sheet(fx, rev)
        c = fxc if fxc is not None else fx_col(bm, fm, col)
        if c is not None:
            f, fm = frame(fx, rev, row, c)
            p = fm["pivot"]
            cv.alpha_composite(f, (anchor[0] - p["x"], anchor[1] - p["y"]))
    return cv


def label(im, text, scale=1):
    out = Image.new("RGBA", (im.width, im.height + 14), BG)
    out.paste(im, (0, 14))
    ImageDraw.Draw(out).text((3, 1), text, fill=(240, 236, 200, 255))
    return out


def row_of(cells, pad=4):
    W = sum(c.width for c in cells) + pad * (len(cells) - 1)
    H = max(c.height for c in cells)
    out = Image.new("RGBA", (W, H), BG)
    x = 0
    for c in cells:
        out.paste(c, (x, 0))
        x += c.width + pad
    return out


def x2(im, k=2):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def fit(im, maxw=7900):
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.NEAREST)
    return im


SCENES = {
    "katana": [  # (몸, 무기 층, fx, 몸 칸들, fx 칸 고정 or None)
        ("player_katana_rise", ["weapons/v3/katana_rise"], "fx/v3/katana_rise", [3, 4, 5], None),
        ("player_katana_spin", ["weapons/v3/katana_spin", "weapons/v3/katana_spin_ki3"], "fx/v3/katana_spin", [9, 10, 11], None),
        ("player_katana_thrust", ["weapons/v3/katana_thrust", "weapons/v3/katana_thrust_ki2"], "fx/v3/katana_thrust_ki2", [3, 4, 5], None),
        ("player_katana_fall", ["weapons/v3/katana_fall", "weapons/v3/katana_fall_awaken"], "fx/v3/katana_fall_awaken", [1, 2, 3], None),
    ],
    "dagger": [
        ("player_dagger_combo1", ["weapons/v3/dagger_combo1"], "fx/v3/dagger_combo1", [2, 3, 4], "glow"),
        ("player_dagger_combo3", ["weapons/v3/dagger_combo3"], "fx/v3/dagger_combo3_accel3", [2, 3, 4], "glow"),
        ("player_dagger_flurry", ["weapons/v3/dagger_flurry"], "fx/v3/dagger_flurry", [2, 3, 4], "glow"),
        ("player_dagger_combo2", ["weapons/v3/dagger_combo2", "weapons/v3/dagger_combo2_awaken"], "fx/v3/dagger_combo2_awaken", [2, 3, 4], "glow"),
    ],
}
FX = {
    "katana": ["fx/v3/katana_rise", "fx/v3/katana_spin", "fx/v3/katana_iai_ki3", "fx/v3/katana_issen_line_t2", "fx/v3/katana_guardbreak",
               "fx/v3/katana_spin_awaken", "fx/v3/hit_katana", "fx/v3/hit_katana_heavy", "fx/v3/katana_whirl_loop", "fx/v3/katana_fullmoon"],
    "dagger": ["fx/v3/dagger_combo1", "fx/v3/dagger_combo3_accel3", "fx/v3/dagger_flurry_heat3", "fx/v3/dagger_backstab", "fx/v3/dagger_brand_mark",
               "fx/v3/dagger_brand_burst", "fx/v3/shadowstep_ghost", "fx/v3/dagger_fan_throw", "fx/v3/hit_dagger_heavy", "fx/v3/dagger_combo1_awaken",
               "fx/v3/dagger_hundred_ghosts"],
}
MISC = {
    "katana": ["fx/v3/trait_katana_k_issenBack", "fx/v3/trait_katana_k_moonPools", "fx/v3/trait_katana_k_shadowVault_out", "fx/v3/trait_katana_bloodGale",
               "fx/v3/trait_katana_k_iaiWave_launch", "fx/v3/trait_res_katana_chain", "fx/v3/trait_res_katana_insight_on",
               "weapons/v3/katana_iai_ki1", "weapons/v3/katana_iai_ki3", "weapons/v3/katana_iai_awaken"],
    "dagger": ["fx/v3/trait_dagger_d_brandChain", "fx/v3/trait_dagger_twinBrand", "fx/v3/trait_dagger_d_stepBack_out", "fx/v3/trait_dagger_d_dashPierce",
               "fx/v3/trait_res_dagger_vital", "fx/v3/trait_res_dagger_vital_on", "weapons/v3/dagger_combo1_awaken", "weapons/v4/dagger_twin_a1_combo1",
               "weapons/v4/dagger_hyakki_a1_carry_idle"],
}


def glow_col(rel, rev):
    m, _ = sheet(rel, rev)
    g = m.get("glowFrames") or [0]
    return g[0]


def main_preview(w):
    parts = []
    for body, layers, fx, cols, fxc in SCENES[w]:
        for row, rn in ((3, "right"), (0, "down")):
            line = []
            for rev, tag in ((REV, "before"), (None, "after")):
                for c in cols:
                    fc = None
                    if fxc == "glow":
                        fc = glow_col(fx, rev) + (c - cols[1])
                        m, _ = sheet(fx, rev)
                        if not (0 <= fc < (m.get("framesPerDirection") or m.get("frames"))):
                            fc = None
                        im = scene(rev, body, layers, fx if fc is not None else None, row, c, fc)
                    else:
                        im = scene(rev, body, layers, fx, row, c)
                    line.append(label(x2(im), "%s %s %s f%d" % (tag, body.replace("player_", ""), rn, c)))
            parts.append(row_of(line))
    for fx in FX[w]:
        for rev, tag in ((REV, "before"), (None, "after")):
            parts.append(label(V.strip(fx, rev, "right", 1, 0.5, 9, label=False), "%s %s (dark floor 0.5, 1x)" % (tag, fx.split("/")[-1])))
    return V.stack([fit(p) for p in parts], BG)


def misc_preview(w):
    parts = []
    for rel in MISC[w]:
        for rev, tag in ((REV, "before"), (None, "after")):
            parts.append(label(V.strip(rel, rev, "right", 1, 0.5, 9, label=False), "%s %s" % (tag, rel.split("/")[-1])))
    # looks
    import glob
    d = os.path.join(V.SPR, "looks")
    names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(d, w + "_*.png")))
    for rev, tag in ((REV, "before"), (None, "after")):
        cells = []
        for n in names:
            b = V.git_read(rev, "assets/sprites/looks/" + n) if rev else open(os.path.join(d, n), "rb").read()
            import io
            im = Image.open(io.BytesIO(b)).convert("RGBA")
            bg = Image.new("RGBA", im.size, (40, 36, 34, 255))
            bg.alpha_composite(im)
            cells.append(label(bg, n[:-4].replace(w + "_", "")))
        parts.append(label(row_of(cells), tag + " looks"))
    # cards (2배)
    names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(V.SPR, "ui_traits", w + "_*.png"))
                   + glob.glob(os.path.join(V.SPR, "ui_traits", "res_" + w + "_*.png")))
    for rev, tag in ((REV, "before"), (None, "after")):
        cells = []
        for n in names:
            import io
            b = V.git_read(rev, "assets/sprites/ui_traits/" + n) if rev else open(os.path.join(V.SPR, "ui_traits", n), "rb").read()
            im = Image.open(io.BytesIO(b)).convert("RGBA")
            bg = Image.new("RGBA", im.size, (46, 38, 30, 255))
            bg.alpha_composite(im)
            cells.append(label(x2(bg), n[:-4]))
        parts.append(label(row_of(cells), tag + " cards 2x"))
    return V.stack([fit(p) for p in parts], BG)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--rev" in sys.argv:
        REV = sys.argv[sys.argv.index("--rev") + 1]
        args = [a for a in args if a != REV]
    for w in args or ["katana", "dagger"]:
        p = os.path.join(HERE, "preview_%s.png" % w)
        main_preview(w).save(p, optimize=True)
        p2 = os.path.join(HERE, "preview_%s_misc.png" % w)
        misc_preview(w).save(p2, optimize=True)
        print(p, p2)
