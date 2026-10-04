"""58: 다시 낸 대검 시트의 기존 4행(down·up·left·right)이 이전 assets(백업, 아틀라스)와 픽셀이 같은지 — 틀이 늘었으면 offset 차이만큼 옮겨 대조."""
import json, os, sys
from PIL import Image, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))
import gridsheet
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))


def cells(path):
    m = gridsheet.load_meta(path)
    im = gridsheet.open_grid(path)
    fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
    return m, {d: [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r, d in enumerate(m["directions"])}


def compare(old_dir, rel_names, rows=("down", "up", "left", "right")):
    bad = []
    for rel in rel_names:
        om, oc = cells(os.path.join(old_dir, rel + ".json"))
        nm, nc = cells(os.path.join(ROOT, "assets/sprites", rel + ".json"))
        oo = om.get("playerFrameOffset", {"x": 0, "y": 0}); no = nm.get("playerFrameOffset", {"x": 0, "y": 0})
        dx, dy = no["x"] - oo["x"], no["y"] - oo["y"]
        nd = 0
        for d in rows:
            for a, b in zip(oc[d], nc[d]):
                c = Image.new("RGBA", b.size, (0, 0, 0, 0))
                c.alpha_composite(a, (dx, dy)) if dx >= 0 and dy >= 0 else c.paste(a, (dx, dy))
                if ImageChops.difference(c, b).getbbox():
                    nd += 1
        print(("OK  " if nd == 0 else "DIFF") + " %s (rows4 %d diff, offset +%d,+%d)" % (rel, nd, dx, dy))
        if nd:
            bad.append(rel)
    return bad


if __name__ == "__main__":
    old = sys.argv[1]
    names = sys.argv[2:]
    sys.exit(1 if compare(old, names) else 0)
