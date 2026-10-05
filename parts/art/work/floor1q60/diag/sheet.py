"""60라운드 Q4 진단용 — 1층 적 v3 시트를 격자로 되살려 동작별 프레임을 한 장에 늘어놓는다."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../../.."))
sys.path.insert(0, os.path.join(ROOT, "parts/art/work/atlas57"))
import gridsheet
from PIL import Image, ImageDraw

SPR = os.path.join(ROOT, "assets/sprites")
BG = (38, 34, 36, 255)

def frames(path):
    meta = gridsheet.load_meta(path + ".json")
    im = gridsheet.open_grid(path + ".png")
    fw, fh, n = meta["frameWidth"], meta["frameHeight"], meta["frames"]
    rows = im.height // fh
    out = [[im.crop((c*fw, r*fh, (c+1)*fw, (r+1)*fh)) for c in range(n)] for r in range(rows)]
    return meta, out

def strip(cells, scale, bg=BG, gap=4):
    w = sum(c.width for c in cells)*scale + gap*(len(cells)+1)
    h = max(c.height for c in cells)*scale + gap*2
    o = Image.new("RGBA", (w, h), bg)
    x = gap
    for c in cells:
        cc = c.resize((c.width*scale, c.height*scale), Image.NEAREST)
        o.alpha_composite(cc, (x, gap)); x += cc.width + gap
    return o

if __name__ == "__main__":
    which = sys.argv[1]; scale = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    rows_sel = [int(x) for x in sys.argv[3].split(",")] if len(sys.argv) > 3 else None
    acts = ["idle", "walk", "attack", "hurt", "death"]
    tiles = []
    for a in acts:
        p = os.path.join(SPR, "enemies/v3", f"{which}_{a}")
        meta, fr = frames(p)
        for ri, row in enumerate(fr):
            if rows_sel and ri not in rows_sel: continue
            tiles.append(strip(row, scale))
    W = max(t.width for t in tiles); H = sum(t.height for t in tiles)
    o = Image.new("RGBA", (W, H), (20, 20, 20, 255)); y = 0
    for t in tiles: o.alpha_composite(t, (0, y)); y += t.height
    o.save(os.path.join(HERE, f"enemy_{which}.png")); print(o.size)
