"""무기별 비교 그림 out/../preview_<weapon>.png (긴 변 8000 이하, 검수용):
  윗줄  정지 그림 base → a1(갈래 3) → a2(갈래 3 × 길 2색)  (looks, 2배)
  아래  게임 합성(몸 + 무기 + a1 + a2 + tint 빛) — 시트 2~3개 × 방향 2 × 프레임 몇 장, 갈래마다 [a1 | a2 길A | a2 길B]
"""
import json
import os
import sys

from PIL import Image, ImageDraw

import g61 as Z
import sheets as SH
import looks as LK
sys.path.insert(0, Z.AW)
import prod_preview as PP  # noqa: E402

BG = (27, 28, 33, 255)
SAMPLES = {
    "katana": [("katana_carry_drawn_idle", (0, 3)), ("katana_rise", (2, 4, 6)), ("katana_carry_idle", (0,))],
    "greatsword": [("greatsword_carry_drawn_idle", (0, 3)), ("greatsword_sweep_cw", (3, 5, 8)), ("greatsword_carry_idle", (0,))],
    "dagger": [("dagger_carry_idle", (0, 3)), ("dagger_combo1", (1, 3, 5))],
    "bow": [("bow_carry_idle", (0, 3)), ("bow_draw_hold", (4, 10, 13))],
}
DIRS = ("right", "down")


def grid(name):
    return PP.grid(os.path.join(Z.STAGE, "weapons", name))


def label(img, xy, s):
    ImageDraw.Draw(img).text(xy, s, fill=(210, 210, 210))


def looks_row(w):
    m = json.load(open(os.path.join(LK.OUT, w + ".json"), encoding="utf-8"))
    items = [("base", m["base"])]
    for b, e in m["branches"].items():
        items.append((b + " a1", e["a1"]))
    for b, e in m["branches"].items():
        for pid, fn in e["a2ByPath"].items():
            items.append((b + " a2 " + pid, fn))
    S = 384
    out = Image.new("RGBA", (len(items) * (S + 4), S + 16), BG)
    for i, (t, fn) in enumerate(items):
        im = Image.open(os.path.join(LK.OUT, fn)).convert("RGBA")
        bg = Image.new("RGBA", im.size, (36, 37, 44, 255))
        bg.alpha_composite(im)
        out.alpha_composite(bg.resize((S, S), Image.NEAREST), (i * (S + 4), 16))
        label(out, (i * (S + 4) + 2, 2), t)
    return out


def game_block(w, sheet, frames, scale=2):
    j, wf = Z.K57.grid_frames("weapons/v3/" + sheet)
    bj = PP.body_for(j, sheet)
    po = j.get("playerFrameOffset", {"x": 48, "y": 48})
    ox, oy = Z.P.PAD[w][0], Z.P.PAD[w][1]
    cols = [("a1", None, None)]
    variants = []
    for bid, ko, line, paths in Z.BRANCHES[w]:
        n1, n2, n3 = SH.names(w, bid, sheet)
        g1, g2, g3 = grid(n1), grid(n2), grid(n3)
        variants.append((bid + " a1", g1, None, None, None))
        for pid, (pko, rgb) in paths.items():
            variants.append((bid + " a2 " + pid, g1, g2, g3, rgb))
    W, H = g1[0]["frameWidth"], g1[0]["frameHeight"]
    cw, ch = W * scale, H * scale
    tiles = []
    for d in DIRS:
        if d not in wf:
            continue
        for c in frames:
            c = min(c, len(wf[d]) - 1)
            row = []
            base = Image.new("RGBA", (W, H), BG)
            if bj and d in bj[1]:
                base.alpha_composite(bj[1][d][min(c, len(bj[1][d]) - 1)], (po["x"] + ox, po["y"] + oy))
            base.alpha_composite(wf[d][c], (ox, oy))
            row.append(("base", base))
            for t, a, b2, b3, rgb in variants:
                im = base.copy()
                im.alpha_composite(a[1][d][c])
                if b2:
                    im.alpha_composite(b2[1][d][c])
                    im.alpha_composite(LK.tint(b3[1][d][c], rgb))
                row.append((t, im))
            tiles.append(("%s %s #%d" % (sheet, d, c), row))
    n = len(tiles[0][1])
    out = Image.new("RGBA", (120 + n * (cw + 3), len(tiles) * (ch + 3) + 16), (14, 14, 17, 255))
    for k, (t, _) in enumerate(tiles[0][1]):
        label(out, (120 + k * (cw + 3) + 2, 2), t)
    for r, (t, row) in enumerate(tiles):
        y = 16 + r * (ch + 3)
        label(out, (2, y + 4), t.replace(" ", "\n", 1))
        for k, (_, im) in enumerate(row):
            out.alpha_composite(im.resize((cw, ch), Image.NEAREST), (120 + k * (cw + 3), y))
    return out


def build(w, scale=2):
    blocks = [looks_row(w)]
    for s, fr in SAMPLES[w]:
        blocks.append(game_block(w, s, fr, scale))
    Wd = max(b.width for b in blocks)
    Hd = sum(b.height + 8 for b in blocks)
    o = Image.new("RGBA", (Wd, Hd), (10, 10, 12, 255))
    y = 0
    for b in blocks:
        o.alpha_composite(b, (0, y))
        y += b.height + 8
    if max(o.size) > 8000:
        k = 8000 / max(o.size)
        o = o.resize((int(o.width * k), int(o.height * k)), Image.NEAREST)
    p = os.path.join(Z.HERE, "preview_%s.png" % w)
    o.convert("RGB").save(p, optimize=True)
    return p, o.size


if __name__ == "__main__":
    for w in (sys.argv[1:] or Z.WEAPONS):
        print(build(w))
