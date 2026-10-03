"""갈래 비교 미리보기 — 무기별 (기본 / 갈래 A / 갈래 B) × 3타, 판정 프레임과 다음 프레임 + 몸·무기 겹침, 1배 조명 합성.
gif/branch_<무기>_combo<n>_right.gif = 기본·A·B 나란히 실제 ms."""
import os

from PIL import Image, ImageDraw

import preview as PV

HERE = PV.HERE
BR = {"katana": ("iai", "batto"), "greatsword": ("crush", "weight"), "dagger": ("twin", "gale")}


def compare(weapon):
    a, b = BR[weapon]
    spots = []
    for n in (1, 2, 3):
        bj, _ = PV.load(os.path.join(PV.P3, "player_%s_combo%d" % (weapon, n)))
        bi = PV.glow_body_frame(bj)
        for tag in ("", "_" + a, "_" + b):
            name = "%s_combo%d%s" % (weapon, n, tag)
            fj, _ = PV.load(os.path.join(PV.FX3, name))
            im, piv = PV.comp_body(weapon, n, "right", bi, name, fj["impactFrame"])
            spots.append(("%d타 %s" % (n, tag[1:] or "기본"), im, piv))
    big = weapon == "greatsword"
    step = 520 if big else 340
    # 3줄(타) × 3칸으로 나눠 조명 합성
    rows = []
    for r in range(3):
        PV.mock(weapon, spots[r * 3:(r + 1) * 3], "_tmp_branch.png", step=step, h=560 if big else 440)
        rows.append(Image.open(os.path.join(HERE, "_tmp_branch.png")).convert("RGB"))
    os.remove(os.path.join(HERE, "_tmp_branch.png"))
    out = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)))
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    out.save(os.path.join(HERE, "preview_branch_%s.png" % weapon))


def gif(weapon, n):
    a, b = BR[weapon]
    os.makedirs(PV.GIF, exist_ok=True)
    tags = ["", "_" + a, "_" + b]
    for tag in tags:
        PV.combo_gif(weapon, n, "right", fx_name="%s_combo%d%s" % (weapon, n, tag), tag="_br%s" % tag)
    ims = [Image.open(os.path.join(PV.GIF, "_br%s_right.gif" % tag)) for tag in tags]
    frames, durs = [], []
    k = 0
    while True:
        row = Image.new("RGB", (sum(im.width for im in ims), ims[0].height))
        x = 0
        alive = False
        dur = 40
        for im in ims:
            try:
                im.seek(min(k, im.n_frames - 1))
                alive |= k < im.n_frames
                dur = im.info.get("duration", 40)
            except EOFError:
                pass
            row.paste(im.convert("RGB"), (x, 0))
            x += im.width
        if not alive:
            break
        d = ImageDraw.Draw(row)
        for j, tag in enumerate(tags):
            PV.label(d, j * ims[0].width + 8, 8, "%s combo%d %s" % (weapon, n, tag[1:] or "base"))
        frames.append(row.quantize(colors=128, dither=Image.Dither.NONE))
        durs.append(dur)
        k += 1
    frames[0].save(os.path.join(PV.GIF, "branch_%s_combo%d_right.gif" % (weapon, n)), save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, disposal=2)
    for tag in tags:
        os.remove(os.path.join(PV.GIF, "_br%s_right.gif" % tag))


def main():
    for w in BR:
        compare(w)
        for n in (1, 2, 3):
            gif(w, n)
