"""미리보기 — 격자 원본(out/grid)을 읽어 시트별 행×프레임 접촉 시트 PNG 와 GIF.

  python3 prev.py <묶음 이름> name1 name2 ...   → preview_<묶음>.png
  주인공 피벗 시트(anchor player_pivot)는 크기 비교용으로 주인공 대기 몸(어두운 회색)을 피벗에 깔아 보여 준다.
"""
import json
import os
import sys

from PIL import Image, ImageDraw

import kit as K

BG = (30, 28, 34, 255)


def load(name, cat="fx"):
    d = os.path.join(K.STAGE, cat)
    j = json.load(open(os.path.join(d, name + ".json"), encoding="utf-8"))
    im = Image.open(os.path.join(d, name + ".png")).convert("RGBA")
    fw, fh, n = j["frameWidth"], j["frameHeight"], j["frames"]
    rows = {r: [im.crop((c * fw, i * fh, (c + 1) * fw, (i + 1) * fh)) for c in range(n)] for i, r in enumerate(j["directions"])}
    return j, rows


_HERO = {}


def hero(d):
    if not _HERO:
        _, fr = K.grid_frames("player/v3/player_idle")
        for r, lst in fr.items():
            im = lst[0]
            g = Image.new("RGBA", im.size, (0, 0, 0, 0))
            px, pg = im.load(), g.load()
            for y in range(im.height):
                for x in range(im.width):
                    if px[x, y][3]:
                        pg[x, y] = (70, 70, 78, 255)
            _HERO[r] = g
    return _HERO.get(d, _HERO["down"])


def tile(j, im, d, scale, show_hero):
    bg = Image.new("RGBA", im.size, BG)
    if show_hero:
        h = hero(d if d in K.DIRS4 else "down")
        bg.alpha_composite(h, (j["pivot"]["x"] - 48, j["pivot"]["y"] - 138))
    bg.alpha_composite(im)
    if scale != 1:
        bg = bg.resize((bg.width * scale, bg.height * scale), Image.NEAREST)
    return bg


def sheet_preview(names, out, cat="fx", maxw=4000, gif=True):
    blocks = []
    for name in names:
        j, rows = load(name, cat)
        fw, fh = j["frameWidth"], j["frameHeight"]
        scale = 3 if max(fw, fh) <= 96 else 2 if max(fw, fh) <= 260 else 1
        show_hero = j.get("anchor") == "player_pivot" or cat == "weapons"
        cw, ch = fw * scale + 4, fh * scale + 4
        n = j["frames"]
        W_ = min(maxw, cw * n + 120)
        img = Image.new("RGBA", (W_, 22 + ch * len(rows)), (18, 17, 20, 255))
        dr = ImageDraw.Draw(img)
        dr.text((4, 4), "%s  %dx%d  x%d  ms=%s  glow=%s" % (name, fw, fh, scale, j["frameDurationsMs"], j.get("glowFrames")), fill=(220, 220, 220))
        for ri, (r, lst) in enumerate(rows.items()):
            dr.text((4, 22 + ri * ch + 4), str(r)[:10], fill=(160, 160, 160))
            for c, im in enumerate(lst):
                x = 80 + c * cw
                if x + cw > W_:
                    break
                img.alpha_composite(tile(j, im, r, scale, show_hero), (x, 22 + ri * ch))
        blocks.append(img)
        if gif:
            gd = os.path.join(K.HERE, "gif")
            os.makedirs(gd, exist_ok=True)
            r0 = list(rows)[-1] if "right" not in rows else "right"
            fr = [tile(j, im, r0, scale, show_hero).convert("P", palette=Image.ADAPTIVE) for im in rows[r0]]
            fr[0].save(os.path.join(gd, name + ".gif"), save_all=True, append_images=fr[1:], duration=[max(20, m * 2) for m in j["frameDurationsMs"]],
                       loop=0, disposal=2)
    W_ = max(b.width for b in blocks)
    H_ = sum(b.height + 6 for b in blocks)
    sheet = Image.new("RGBA", (W_, H_), (10, 10, 12, 255))
    y = 0
    for b in blocks:
        sheet.alpha_composite(b, (0, y))
        y += b.height + 6
    sheet.save(out)
    return out


if __name__ == "__main__":
    tag, *names = sys.argv[1:]
    cat = "weapons" if tag.startswith("w_") else "fx"
    print(sheet_preview(names, os.path.join(K.HERE, "preview_%s.png" % tag), cat))
