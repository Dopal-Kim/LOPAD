"""작업 D 미리보기 — 산출물마다 PNG/GIF 를 이 폴더에."""
import json
import os

from PIL import Image, ImageDraw

import prev
import rk


def fx_cells(path, rows=None, scale=1, bg=prev.BG):
    j, fr = prev.sheet(path)
    rows = rows or j["directions"]
    return j, {r: [_bg(im, bg) for im in fr[r]] for r in rows}


def _bg(im, bg):
    c = Image.new("RGBA", im.size, bg)
    c.alpha_composite(im)
    return c


def sheet_grid(path, out, scale=2, rows=None):
    j, cells = fx_cells(path, rows)
    rows = rows or j["directions"]
    flat, labels = [], []
    for r in rows:
        for i, im in enumerate(cells[r]):
            flat.append(im)
            labels.append("%s f%d %dms" % (r, i, j["frameDurationsMs"][i]))
    return prev.grid(flat, j["frames"], out, scale=scale, labels=labels,
                     title="%s · %d×%d · pivot (%d,%d) · glow %s" % (path.split("/")[-1], j["frameWidth"], j["frameHeight"],
                                                                    j["pivot"]["x"], j["pivot"]["y"], j.get("glowFrames")))


def gs8_preview():
    """대검 이펙트 8행 — 몸 시트 판정 프레임 + 이펙트 판정 프레임 합성(행마다 같은 directionRows)."""
    cells, labels = [], []
    for fx, body in [("greatsword_sweep_cw", "greatsword_sweep_cw"), ("greatsword_cleave", "greatsword_cleave"),
                     ("greatsword_charge_slam_lv2", "greatsword_charge_slam")]:
        fj, ff = prev.sheet("fx/v3/" + fx)
        bj, bf = prev.sheet("player/v3/player_" + body)
        wj, wf = prev.sheet("weapons/v3/" + body)
        bi = bj["impactFrame"]
        for d in fj["directions"]:
            W_, H_ = 640, 640
            o = (320, 400)
            cv = Image.new("RGBA", (W_, H_), prev.BG)
            cv.alpha_composite(bf[d][bi], (o[0] - bj["pivot"]["x"], o[1] - bj["pivot"]["y"]))
            off = wj["playerFrameOffset"]
            cv.alpha_composite(wf[d][bi], (o[0] - 48 - off["x"], o[1] - 138 - off["y"]))
            fi = fj["impactFrame"]
            cv.alpha_composite(ff[d][fi], (o[0] - fj["pivot"]["x"], o[1] - fj["pivot"]["y"]))
            cv = cv.crop((120, 120, 520, 520))
            cells.append(cv.resize((200, 200), Image.NEAREST))
            labels.append("%s r%d %s" % (fx.replace("greatsword_", "gs_"), fj["directions"].index(d), d))
    return prev.grid(cells, 8, "preview_gs8_rows.png", scale=1, labels=labels,
                     title="Q30 대검 이펙트 8행 — 행 = 몸 directionRows(down, up, left, right, down-right, down-left, up-right, up-left) · 몸 판정 프레임 + fx 판정 프레임 · 1/2 축소")


def overlay_preview(weapon_sheets, kind, out, frames_pick=None):
    cells, labels = [], []
    for w in weapon_sheets:
        j, _ = prev.sheet("weapons/v3/" + w)
        dirs = j["directions"][:4]
        for d in dirs:
            i = frames_pick(j) if frames_pick else 0
            for lv in (0, 1, 2, 3):
                ov = None if lv == 0 else "%s_%s%d" % (w, kind, lv)
                W_, H_, o = (240, 270, (120, 215)) if w.startswith("greatsword") else (200, 230, (100, 190))
                cells.append(prev.compose(w, ov, d, i, W=W_, H=H_, origin=o))
                labels.append("%s %s f%d %s" % (w.replace("greatsword_", "gs_").replace("katana_", "k_"), d, i, "base" if lv == 0 else "%s%d" % (kind, lv)))
    return prev.grid(cells, 8, out, scale=1, labels=labels)


def overlay_gif(w, kind, d, out, lv=3):
    j, _ = prev.sheet("weapons/v3/" + w)
    big = w.startswith("greatsword")
    W_, H_, o = (240, 270, (120, 215)) if big else (200, 230, (100, 190))
    frames = []
    for i in range(j["frames"]):
        row = [prev.compose(w, None if L == 0 else "%s_%s%d" % (w, kind, L), d, i, W=W_, H=H_, origin=o) for L in (0, 1, 2, 3)]
        cv = Image.new("RGBA", (W_ * 4, H_), prev.BG)
        for k, c in enumerate(row):
            cv.paste(c, (k * W_, 0))
        frames.append(cv)
    return prev.gif(frames, j["frameDurationsMs"], out, scale=2)


def fx_gif(path, row, out, scale=3, repeat=1):
    j, cells = fx_cells(path, [row])
    return prev.gif(cells[row] * repeat, j["frameDurationsMs"] * repeat, out, scale=scale)


def brand_mock():
    """적(결사병 v3 대기) 머리 위 표식 1~5 + 기폭 l 의 열 1·2 — 1배 합성."""
    ej, ef = prev.sheet("enemies/v3/charger_idle")
    mj, mf = prev.sheet("fx/v3/dagger_brand_mark")
    bj, bf = prev.sheet("fx/v3/dagger_brand_burst")
    cells, labels = [], []
    for n in range(1, 6):
        cv = Image.new("RGBA", (180, 240), prev.BG_FLOOR)
        e = ef["down"][0] if "down" in ef else list(ef.values())[0][0]
        ex, ey = 90 - ej["pivot"]["x"], 225 - ej["pivot"]["y"]
        cv.alpha_composite(e, (ex, ey))
        top = ey + (e.getbbox() or (0, 0, 0, 0))[1]
        m = mf[str(n)][3]
        cv.alpha_composite(m, (90 - mj["pivot"]["x"], top - 16 - mj["pivot"]["y"]))
        cells.append(cv)
        labels.append("낙인 %d (루프 f3)" % n)
    for i in (1, 2, 3):
        cv = Image.new("RGBA", (180, 240), prev.BG_FLOOR)
        e = ef["down"][0]
        ex, ey = 90 - ej["pivot"]["x"], 225 - ej["pivot"]["y"]
        cv.alpha_composite(e, (ex, ey))
        b = bf["l"][i]
        cv.alpha_composite(b, (90 - bj["pivot"]["x"], 225 - 60 - bj["pivot"]["y"]))
        cells.append(cv)
        labels.append("기폭 l f%d" % i)
    return prev.grid(cells, 8, "preview_brand_mock_x2.png", scale=2, labels=labels,
                     title="낙인 표식(적 머리 위) 1~5 + 기폭 폭발 l — 결사병 v3 위 합성 · 2배")


def guard_mock():
    """주인공 정면 대기 + 오른쪽에서 온 공격 → guard / parry 각 열."""
    pj, pf = prev.sheet("player/v3/player_idle_free")
    gj, gf = prev.sheet("fx/v3/guard_perfect_fx")
    cells, labels = [], []
    for kind in ("guard", "parry"):
        for i in range(gj["frames"]):
            cv = Image.new("RGBA", (200, 200), prev.BG_FLOOR)
            cv.alpha_composite(pf["right"][0], (80 - pj["pivot"]["x"], 185 - pj["pivot"]["y"]))
            cx, cy = 80 + 24, 185 - 40
            cv.alpha_composite(gf[kind][i], (cx - gj["pivot"]["x"], cy - gj["pivot"]["y"]))
            cells.append(cv)
            labels.append("%s f%d" % (kind, i))
    out = prev.grid(cells, gj["frames"], "preview_guard_perfect_mock_x2.png", scale=2, labels=labels,
                    title="guard_perfect_fx — 주인공(오른쪽 보기) 판정 원점에서 공격 쪽 24 도트 · 2배")
    frames = []
    for i in range(gj["frames"]):
        cv = Image.new("RGBA", (400, 200), prev.BG_FLOOR)
        cv.paste(cells[i], (0, 0))
        cv.paste(cells[gj["frames"] + i], (200, 0))
        frames.append(cv)
    prev.gif(frames + frames[-1:] * 3, gj["frameDurationsMs"] + [200] * 3, "guard_perfect_guard_parry.gif", scale=2)
    return out


def main():
    outs = [gs8_preview()]
    outs.append(sheet_grid("fx/v3/bow_arrow_weak", "preview_bow_arrow_weak_x8.png", scale=8))
    outs.append(fx_gif("fx/v3/bow_arrow_weak", "any", "bow_arrow_weak.gif", scale=8, repeat=4))
    outs.append(overlay_preview(["katana_rise", "katana_fall", "katana_issen", "katana_carry_drawn_idle", "katana_carry_idle"], "ki",
                                "preview_ki_overlay.png", frames_pick=lambda j: (j.get("glowFrames") or [0])[0]))
    outs.append(overlay_gif("katana_rise", "ki", "right", "ki_katana_rise_right.gif"))
    outs.append(overlay_gif("katana_issen", "ki", "right", "ki_katana_issen_right.gif"))
    outs.append(overlay_gif("katana_carry_drawn_idle", "ki", "down", "ki_katana_carry_drawn_idle_down.gif"))
    outs.append(overlay_gif("katana_carry_walk", "ki", "right", "ki_katana_carry_walk_right.gif"))
    outs.append(overlay_preview(["greatsword_sweep_cw", "greatsword_charge", "greatsword_carry_drawn_idle", "greatsword_carry_idle"], "grudge",
                                "preview_grudge_overlay.png", frames_pick=lambda j: (j.get("glowFrames") or [0])[0]))
    outs.append(overlay_gif("greatsword_charge", "grudge", "down-right", "grudge_greatsword_charge_downright.gif"))
    outs.append(overlay_gif("greatsword_carry_drawn_idle", "grudge", "right", "grudge_greatsword_carry_drawn_idle_right.gif"))
    for p, sc in (("fx/v3/dagger_brand_mark", 4), ("fx/v3/dagger_brand_burst", 2), ("fx/v3/dagger_overheat_burst", 1),
                  ("fx/v3/dagger_overheat_cool", 3), ("fx/v3/guard_perfect_fx", 3), ("fx/v3/player_groggy_swirl", 4)):
        outs.append(sheet_grid(p, "preview_%s_x%d.png" % (p.split("/")[-1], sc), scale=sc))
    outs.append(fx_gif("fx/v3/dagger_brand_mark", "5", "brand_mark_5.gif", scale=4, repeat=1))
    outs.append(fx_gif("fx/v3/dagger_brand_burst", "l", "brand_burst_l.gif", scale=2))
    outs.append(fx_gif("fx/v3/dagger_overheat_burst", "any", "overheat_burst.gif", scale=1))
    outs.append(brand_mock())
    outs.append(guard_mock())
    import prev_groggy
    outs += prev_groggy.main()
    return outs


if __name__ == "__main__":
    print("\n".join(main()))
