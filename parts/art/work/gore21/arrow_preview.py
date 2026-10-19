"""박힌 화살 5대 + 상흔 3단을 몸에 얹어 보기(앵커·각·깊이 확인)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "atlas57"))
import gridsheet
from PIL import Image
SPR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "assets", "sprites")

def cells(rel):
    m = gridsheet.load_meta(os.path.join(SPR, rel + ".json")); im = gridsheet.open_grid(os.path.join(SPR, rel + ".json"))
    fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
    return m, {d: [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r, d in enumerate(m["directions"])}

def compose(sheet, frame, stage=3):
    bm, body = cells("player/v3/" + sheet)
    wm, wo = cells("player/v3/hero_wound%d_%s" % (stage, sheet))
    am, ar = cells("fx/v5/stuck_arrow")
    piv = am["pivot"]
    out = []
    for d in bm["directions"]:
        b = body[d][frame]
        c = Image.new("RGBA", (b.width + 40, b.height + 20), (0, 0, 0, 0))
        anc = wm["arrowAnchors"][d][frame] or {}
        def put(a):
            im = ar["any"][a["frame"]]
            if a["flipX"]:
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            px = piv["x"] if not a["flipX"] else im.width - 1 - piv["x"]
            c.alpha_composite(im, (round(a["x"] - px) + 20, round(a["y"] - piv["y"]) + 10))
        for a in anc.values():
            if a["depth"] == "below": put(a)
        c.alpha_composite(b, (20, 10)); c.alpha_composite(wo[d][frame], (20, 10))
        for a in anc.values():
            if a["depth"] == "above": put(a)
        out.append(c)
    W = sum(o.width for o in out); H = out[0].height
    o = Image.new("RGB", (W, H), (30, 30, 34)); x = 0
    for c in out:
        o.paste(c, (x, 0), c); x += c.width
    return o.resize((W * 3, H * 3), Image.NEAREST)

if __name__ == "__main__":
    ims = [compose(s, int(f)) for s, f in (a.split(":") for a in sys.argv[1:])]
    W = max(i.width for i in ims); H = sum(i.height for i in ims)
    o = Image.new("RGB", (W, H)); y = 0
    for i in ims: o.paste(i, (0, y)); y += i.height
    o.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "preview", "arrows.png"))
