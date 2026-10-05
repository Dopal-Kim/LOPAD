"""looks 미리보기 묶음(검수용): 무기별 한 줄 = base · a1×3 · a2×3(구움 길 A) · a2 길 B."""
import json, os, sys
from PIL import Image, ImageDraw
import g61 as Z
D = os.path.join(Z.SPR, "looks")

def row(w, scale=2):
    m = json.load(open(os.path.join(D, w + ".json"), encoding="utf-8"))
    names = [m["base"]]
    for b, e in m["branches"].items():
        names.append(e["a1"])
    for b, e in m["branches"].items():
        names += list(e["a2ByPath"].values())
    ims = [Image.open(os.path.join(D, n)).convert("RGBA") for n in names]
    S = 192 * scale
    out = Image.new("RGBA", (len(ims) * (S + 4), S + 18), (24, 24, 30, 255))
    dr = ImageDraw.Draw(out)
    for i, (n, im) in enumerate(zip(names, ims)):
        bg = Image.new("RGBA", (192, 192), (34, 35, 42, 255))
        bg.alpha_composite(im)
        out.alpha_composite(bg.resize((S, S), Image.NEAREST), (i * (S + 4), 18))
        dr.text((i * (S + 4) + 2, 2), n.replace(".png", ""), fill=(200, 200, 200))
    return out

if __name__ == "__main__":
    ws = sys.argv[1:] or list(Z.WEAPONS)
    rows = [row(w) for w in ws]
    W = max(r.width for r in rows); H = sum(r.height + 4 for r in rows)
    o = Image.new("RGBA", (W, H), (10, 10, 12, 255)); y = 0
    for r in rows:
        o.alpha_composite(r, (0, y)); y += r.height + 4
    o.save(os.path.join(Z.HERE, "out", "looks_check.png"))
    print(o.size)
