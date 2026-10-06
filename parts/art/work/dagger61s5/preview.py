"""전/후 비교 미리보기 — parts/art/work/dagger61s5/preview_*.png (위 = 고치기 전 git BEFORE_REV, 아래 = 지금 assets)."""
import os

from PIL import Image, ImageDraw

import d5
import view
import ovprev
import weapons as WP

OUT = d5.HERE
FLOOR = (44, 40, 38, 255)
BODY = {"dagger_carry_idle": "player_idle_free", "dagger_carry_walk": "player_walk_free", "dagger_carry_run": "player_run_free",
        "dagger_carry_dash": "player_dash"}


def body_of(sheet):
    return "player/v3/" + BODY.get(sheet, "player_" + sheet)


def label(im, text):
    import kit60
    out = Image.new("RGBA", (im.width, im.height + 18), view.BG)
    out.alpha_composite(im, (0, 18))
    ImageDraw.Draw(out).text((3, 1), text, fill=(235, 225, 205, 255), font=kit60.font(13))
    return out


def weapons_sheet():
    B, A = d5.before_root(), d5.SPR
    blocks = []
    for s in WP.SHEETS:
        m, _ = view.frames("weapons/v3/" + s, A)
        cells = [(3, i) for i in range(0, m["frames"], max(1, m["frames"] // 5))][:5] + [(0, min(1, m["frames"] - 1))]
        a = view.zoom_grip("weapons/v3/" + s, cells, B, body_of(s), 26, 4)
        b = view.zoom_grip("weapons/v3/" + s, cells, A, body_of(s), 26, 4)
        blocks.append(label(view.stack([a, b], pad=2), s + "  (위 전 / 아래 후)"))
    half = (len(blocks) + 1) // 2
    im = view.side([view.stack(blocks[:half]), view.stack(blocks[half:])], pad=16)
    im.save(os.path.join(OUT, "preview_weapons.png"))


def overlays_sheet():
    out = []
    for s, cells in (("dagger_combo1", [(3, 2), (0, 1), (2, 3)]), ("dagger_carry_idle", [(3, 0), (0, 0)]), ("dagger_flurry", [(3, 2), (1, 4)])):
        for b in ("awaken", "twin", "gale", "hyakki"):
            row = []
            for root in (d5.before_root(), d5.SPR):
                row.append(view.side([ovprev.comp(root, s, b, r, c, body=body_of(s), half=30, sc=4) for r, c in cells], pad=3))
            out.append(label(view.side(row, pad=24), "%s · %s  (왼 전 / 오른 후, 2차까지·빛 tint)" % (s, b)))
    view.stack(out).save(os.path.join(OUT, "preview_overlays.png"))


def fx_sheet(names, path, scale=2):
    blocks = []
    for n, r in names:
        a = view.tight("fx/v3/" + n, r, scale, root=d5.before_root(), label=n + " 전")
        b = view.tight("fx/v3/" + n, r, scale, root=d5.SPR, label=n + " 후")
        blocks.append(view.stack([a, b], pad=2))
    view.stack(blocks, pad=10).save(path)


def looks_sheet():
    import glob
    Bd, Ad = os.path.join(d5.before_root(), "looks"), os.path.join(d5.SPR, "looks")
    names = sorted(os.path.basename(f) for f in glob.glob(Ad + "/dagger_*.png"))
    out = Image.new("RGBA", (192 * 8, 212 * 4), view.BG)
    d = ImageDraw.Draw(out)
    for i, n in enumerate(names):
        for j, root in enumerate((Bd, Ad)):
            im = Image.open(os.path.join(root, n)).convert("RGBA")
            x, y = (i % 8) * 192, ((i // 8) * 2 + j) * 212
            out.alpha_composite(im, (x, y + 20))
            import kit60
            d.text((x + 2, y + 2), ("전 " if j == 0 else "후 ") + n[7:-4], fill=(230, 220, 200, 255), font=kit60.font(13))
    out.save(os.path.join(OUT, "preview_looks.png"))


def fight_sheet():
    """게임 합성 목업: 몸 + 무기 + fx 를 주인공 피벗에 맞춰 바닥 위에 — 도트 1:1(= 1920 렌더 화면) 과 2배."""
    shots = [("dagger_combo1", "dagger_combo1", 3, 2, 1), ("dagger_combo2", "dagger_combo2_accel2", 3, 2, 1),
             ("dagger_combo3", "dagger_combo3_accel3", 0, 2, 1), ("dagger_flurry", "dagger_flurry", 3, 4, 4),
             ("dagger_backstab", "dagger_backstab", 2, 4, 1), ("dagger_combo1", "dagger_combo1_awaken", 3, 2, 1)]
    out_rows = []
    for root, tag in ((d5.before_root(), "전"), (d5.SPR, "후")):
        cells = []
        for ws, fx, r, wc, fc in shots:
            W, H = 420, 300
            cv = Image.new("RGBA", (W, H), FLOOR)
            P = (150, 230)
            bm, bf = view.frames(body_of(ws))
            wm, wf = view.frames("weapons/v3/" + ws, root)
            fm, ff = view.frames("fx/v3/" + fx, root)
            cv.alpha_composite(bf[r][wc], (P[0] - bm["pivot"]["x"], P[1] - bm["pivot"]["y"]))
            cv.alpha_composite(wf[r][wc], (P[0] - wm["pivot"]["x"], P[1] - wm["pivot"]["y"]))
            if fx.endswith("_awaken"):
                am, af = view.frames("weapons/v3/%s_awaken" % ws, root)
                cv.alpha_composite(af[r][wc], (P[0] - am["pivot"]["x"], P[1] - am["pivot"]["y"]))
            fi = min(fc, fm["frames"] - 1)
            big = Image.new("RGBA", (W + 800, H + 800), (0, 0, 0, 0))
            big.alpha_composite(ff[r][fi], (400 + P[0] - fm["pivot"]["x"], 400 + P[1] - fm["pivot"]["y"]))
            cv.alpha_composite(big.crop((400, 400, 400 + W, 400 + H)))
            cells.append(label(cv, "%s %s · %s 칸 %d" % (tag, ws, fx, fi)))
        out_rows.append(view.side(cells, pad=6))
    one = view.stack(out_rows, pad=10)
    one.save(os.path.join(OUT, "preview_fight.png"))
    one.resize((one.width * 2, one.height * 2), Image.NEAREST).crop((0, 0, min(one.width * 2, 3000), one.height * 2)).save(
        os.path.join(OUT, "preview_fight_2x.png"))


def build():
    weapons_sheet()
    overlays_sheet()
    fx_sheet([("dagger_combo1", 3), ("dagger_combo1_accel2", 3), ("dagger_combo1_accel3", 3), ("dagger_combo2", 0), ("dagger_combo3", 3),
              ("dagger_combo3_accel3", 3), ("dagger_combo1_awaken", 3), ("dagger_flurry", 3), ("dagger_flurry_heat3", 3),
              ("dagger_backstab", 3), ("hit_dagger", 0), ("hit_dagger_heavy", 0)], os.path.join(OUT, "preview_fx.png"))
    fx_sheet([("dagger_combo1_twin", 3), ("dagger_combo3_twin_dance", 3), ("dagger_combo1_twin_bleed", 3), ("dagger_combo1_gale", 3),
              ("dagger_combo2_gale_afterimage", 3), ("dagger_combo3_gale_assassin", 3), ("dagger_combo3_double", 3)],
             os.path.join(OUT, "preview_fx_branch.png"))
    fx_sheet([("shadowstep_ghost", 3), ("dagger_thrown", 0), ("dagger_fan_throw", 3), ("dagger_brand_mark", 2), ("dagger_brand_mark", 4),
              ("dagger_brand_burst", 2), ("dagger_brand_bleed", 0), ("dagger_brand_hop", 0), ("dagger_stuck_blade", 0),
              ("dagger_cross_clone", 3), ("dagger_hundred_ghosts", 0), ("dagger_awaken_in", 0)], os.path.join(OUT, "preview_misc.png"), 2)
    looks_sheet()
    fight_sheet()
    print("preview 8장")


if __name__ == "__main__":
    build()
