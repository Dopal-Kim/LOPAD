"""58 Q4 대각 전후 비교 — 백업(56 판) vs 현재 assets(58 3/4 리그), 대각 4행, 몸+무기 합성."""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import peek
import gridcompat


def comp_rows(root, name, dirs, cols=None, cw=240, ch=310):
    import gridsheet
    bm = gridsheet.load_meta(os.path.join(root, "player/v3/player_%s.json" % name))
    bi = gridsheet.open_grid(os.path.join(root, "player/v3/player_%s.json" % name))
    wm = gridsheet.load_meta(os.path.join(root, "weapons/v3/%s.json" % name))
    wi = gridsheet.open_grid(os.path.join(root, "weapons/v3/%s.json" % name))
    F = bm["frames"]
    cols = cols or list(range(F))
    o = wm["playerFrameOffset"]
    out = Image.new("RGBA", (cw * len(cols), ch * len(dirs)), peek.BG)
    for r, d in enumerate(dirs):
        R = bm["directions"].index(d)
        for j, c in enumerate(cols):
            cell = Image.new("RGBA", (cw, ch), peek.BG)
            px, py = cw // 2 - 48, ch - 160
            b = bi.crop((c * 96, R * 144, (c + 1) * 96, (R + 1) * 144))
            w = wi.crop((c * wm["frameWidth"], R * wm["frameHeight"], (c + 1) * wm["frameWidth"], (R + 1) * wm["frameHeight"]))
            cell.alpha_composite(b, (px, py))
            cell.alpha_composite(w, (px - o["x"], py - o["y"])) if px - o["x"] >= 0 and py - o["y"] >= 0 else _paste(cell, w, px - o["x"], py - o["y"])
            out.paste(cell, (j * cw, r * ch))
    return out


def _paste(cell, w, x, y):
    tmp = Image.new("RGBA", cell.size, (0, 0, 0, 0))
    tmp.paste(w, (x, y), w)
    cell.alpha_composite(tmp)


def make(old_root, name, out, cols=None, scale=1):
    dirs = ["down-right", "down-left", "up-right", "up-left"]
    a = comp_rows(old_root, name, dirs, cols)
    b = comp_rows(os.path.join(peek.ROOT, "assets/sprites"), name, dirs, cols)
    g = Image.new("RGBA", (a.width, a.height + b.height + 24), peek.BG)
    g.paste(a, (0, 0)); g.paste(b, (0, a.height + 24))
    dr = ImageDraw.Draw(g)
    dr.text((4, 2), "%s  56 (front/back body + 3/4 cues)" % name, fill=(255, 210, 120, 255))
    dr.text((4, a.height + 6), "%s  58 true 3/4 rig" % name, fill=(255, 210, 120, 255))
    g = g.resize((g.width * scale, g.height * scale), Image.NEAREST)
    g.save(out)
    return out


if __name__ == "__main__":
    old, name, out = sys.argv[1:4]
    cols = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 and sys.argv[4] else None
    make(old, name, out, cols, int(sys.argv[5]) if len(sys.argv) > 5 else 1)
