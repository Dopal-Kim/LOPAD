"""검수용 빠른 보기: 시트(들)의 한 행을 1층 연회장 바닥(어둡게) 위에 펼쳐 PNG 로. git rev 를 주면 그 커밋 그림.
사용: python3 view.py out.png <rel> [<rel> ...] [--rev HEAD] [--row right] [--scale 2] [--dark 0.5] [--max 10]
"""
import io
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets", "sprites")


def git_read(rev, rel):
    r = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (rev, rel)], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def load(rel, rev=None):
    """rel = 'fx/v3/katana_rise' → (meta, grid RGBA). rev 없으면 작업 트리."""
    def rd(p):
        if rev:
            return git_read(rev, "assets/sprites/" + p)
        fp = os.path.join(SPR, p)
        return open(fp, "rb").read() if os.path.exists(fp) else None
    m = json.loads(rd(rel + ".json"))
    d = os.path.dirname(rel)
    if "atlas" not in m:
        return m, Image.open(io.BytesIO(rd(rel + ".png"))).convert("RGBA")
    g = m["atlas"]["grid"]
    fw, fh, cols = g["frameWidth"], g["frameHeight"], g["columns"]
    sheet = Image.new("RGBA", (cols * fw, g["rows"] * fh), (0, 0, 0, 0))
    if "textures" in m:
        entries = [(t["image"], e["filename"], e) for t in m["textures"] for e in t["frames"]]
    else:
        entries = [(m["meta"]["image"], k, e) for k, e in m["frames"].items()]
    pages = {}
    for img, name, e in entries:
        if img not in pages:
            pages[img] = Image.open(io.BytesIO(rd(d + "/" + img))).convert("RGBA")
        f, s = e["frame"], e["spriteSourceSize"]
        r, c = divmod(int(name), cols)
        sheet.paste(pages[img].crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])), (c * fw + s["x"], r * fh + s["y"]))
    return m, sheet


_FLOOR = {}


def floor_bg(w, h, dark=0.5):
    key = (w, h, dark)
    if key not in _FLOOR:
        ts = Image.open(os.path.join(ROOT, "assets", "tiles", "v2", "stage1_hall.png")).convert("RGBA")
        tiles = [ts.crop((i * 64, 0, i * 64 + 64, 64)) for i in range(4)]
        bg = Image.new("RGBA", (w, h))
        for y in range(0, h, 64):
            for x in range(0, w, 64):
                bg.paste(tiles[((x // 64) * 7 + (y // 64) * 3) % 4], (x, y))
        px = bg.load()
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                px[x, y] = (int(r * dark), int(g * dark), int(b * dark), 255)
        _FLOOR[key] = bg
    return _FLOOR[key].copy()


def frames_of(m, sheet, row=None):
    fw, fh = m.get("frameWidth") or m["atlas"]["grid"]["frameWidth"], m.get("frameHeight") or m["atlas"]["grid"]["frameHeight"]
    dirs = m.get("directions") or ["any"]
    n = sheet.width // fw
    r = dirs.index(row) if row in dirs else 0
    return [sheet.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)]


def strip(rel, rev=None, row="right", scale=2, dark=0.5, maxn=10, label=True):
    m, sh = load(rel, rev)
    fr = frames_of(m, sh, row)[:maxn]
    fw, fh = fr[0].size
    out = floor_bg(fw * len(fr), fh, dark)
    for i, f in enumerate(fr):
        out.alpha_composite(f, (i * fw, 0))
    out = out.resize((out.width * scale, out.height * scale), Image.NEAREST)
    if label:
        ImageDraw.Draw(out).text((2, 2), rel.split("/")[-1] + (" @" + rev if rev else ""), fill=(255, 255, 160, 255))
    return out


def stack(ims, bg=(12, 12, 14, 255)):
    W = max(i.width for i in ims)
    H = sum(i.height for i in ims) + 4 * len(ims)
    out = Image.new("RGBA", (W, H), bg)
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + 4
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    opts = {"--rev": None, "--row": "right", "--scale": "2", "--dark": "0.5", "--max": "10"}
    rels = []
    i = 1
    out = a[0]
    while i < len(a):
        if a[i] in opts:
            opts[a[i]] = a[i + 1]
            i += 2
        else:
            rels.append(a[i])
            i += 1
    ims = []
    for r in rels:
        if opts["--rev"]:
            ims.append(strip(r, opts["--rev"], opts["--row"], int(opts["--scale"]), float(opts["--dark"]), int(opts["--max"])))
        ims.append(strip(r, None, opts["--row"], int(opts["--scale"]), float(opts["--dark"]), int(opts["--max"])))
    stack(ims).save(out)
    print(out)
