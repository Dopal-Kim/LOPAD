"""참고용: 기존 fx 시트를 어두운 1층 바닥 위에 펼쳐 본다(읽기만). python3 view.py out/ref_x.png name1 name2 ... [--k 2]"""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))
import gridsheet

BG = (27, 28, 32, 255)


def frames(name, cat="fx"):
    jp = os.path.join(ROOT, "assets/sprites", cat, "v3", name + ".json")
    m = gridsheet.load_meta(jp)
    im = gridsheet.open_grid(jp)
    fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
    rows = im.height // fh
    return m, [[im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r in range(rows)]


def main():
    args = sys.argv[1:]
    k = 2
    if "--k" in args:
        i = args.index("--k"); k = int(args[i + 1]); del args[i:i + 2]
    out, names = args[0], args[1:]
    strips = []
    for nm in names:
        cat = "fx"
        if ":" in nm:
            cat, nm = nm.split(":")
        m, fr = frames(nm, cat)
        row = fr[0] if len(fr) == 1 else fr[0]
        fw, fh = row[0].size
        W = len(row) * (fw + 4) * k
        s = Image.new("RGBA", (max(W, 300), fh * k + 16), BG)
        ImageDraw.Draw(s).text((2, 2), "%s %dx%d %s" % (nm, fw, fh, m.get("frameDurationsMs")), fill=(200, 200, 200))
        for i, f in enumerate(row):
            fb = Image.new("RGBA", (fw, fh), BG); fb.alpha_composite(f)
            ImageDraw.Draw(fb).rectangle((0, 0, fw - 1, fh - 1), outline=(50, 52, 58))
            s.paste(fb.resize((fw * k, fh * k), Image.NEAREST), (i * (fw + 4) * k, 14))
        strips.append(s)
    W = max(s.width for s in strips); H = sum(s.height + 4 for s in strips)
    sheet = Image.new("RGBA", (W, H), BG)
    y = 0
    for s in strips:
        sheet.paste(s, (0, y)); y += s.height + 4
    sheet.save(out)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
