"""각성 오버레이 미리보기(격자 원본 out/grid 기준): 행마다 [몸+무기 | 몸+무기+각성] — python3 prod_preview.py out.png 시트... [--dirs right,down]"""
import json
import os
import sys

from PIL import Image, ImageDraw

import prod_common as P
import kit60 as K6


def grid(path):
    j = json.load(open(path + ".json", encoding="utf-8"))
    im = Image.open(path + ".png").convert("RGBA")
    fw, fh, n = j["frameWidth"], j["frameHeight"], j["frames"]
    return j, {d: [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r, d in enumerate(j["directions"])}


def body_for(j, sheet):
    bs = j.get("bodySheet")
    if not bs:
        bw = j.get("bodySheetByWeapon")
        if isinstance(bw, dict):
            for v in bw.values():
                if isinstance(v, dict):
                    bs = v.get(sheet.split("_")[0])
        if not bs:
            act = sheet.split("_carry_")[-1] if "_carry_" in sheet else None
            if act:
                act = act.replace("drawn_", "")
                bs = ("player_%s" % act) if sheet.startswith("katana") else ("player_%s_free" % act if act != "dash" else "player_dash")
    if not bs:
        return None
    try:
        return P.K57.grid_frames("player/v3/" + bs)
    except Exception:
        return None


def main(out, sheets, dirs=("right", "down"), scale=2, frames_max=16):
    blocks = []
    for s in sheets:
        j, wf = P.K57.grid_frames("weapons/v3/" + s)
        oj, of = grid(os.path.join(P.STAGE_W, s + "_awaken"))
        bj = body_for(j, s)
        ox, oy = oj["pivotDelta"]["x"], oj["pivotDelta"]["y"]
        W, H = oj["frameWidth"], oj["frameHeight"]
        n = min(frames_max, j["frames"])
        dd = [d for d in dirs if d in wf]
        img = Image.new("RGBA", (n * (W * scale + 4) + 90, 22 + len(dd) * 2 * (H * scale + 4)), (18, 17, 20, 255))
        dr = ImageDraw.Draw(img)
        dr.text((4, 4), "%s_awaken  %dx%d  colors=%s glow=%s" % (s, W, H, oj.get("colors"), oj.get("glowFrames")), fill=(220, 220, 220))
        y = 22
        po = j.get("playerFrameOffset", {"x": 48, "y": 48})
        for d in dd:
            for mode in (0, 1):
                dr.text((4, y + 4), d + (" +aw" if mode else ""), fill=(160, 160, 160))
                for c in range(n):
                    t = Image.new("RGBA", (W, H), K6.hexrgb(K6.BG) + (255,))
                    if bj:
                        bjj, bf = bj
                        if d in bf:
                            t.alpha_composite(bf[d][min(c, len(bf[d]) - 1)], (po["x"] + ox, po["y"] + oy))
                    t.alpha_composite(wf[d][c], (ox, oy))
                    if mode:
                        t.alpha_composite(of[d][c])
                    img.alpha_composite(t.resize((W * scale, H * scale), Image.NEAREST), (90 + c * (W * scale + 4), y))
                y += H * scale + 4
        blocks.append(img)
    W_ = max(b.width for b in blocks)
    H_ = sum(b.height + 6 for b in blocks)
    sh = Image.new("RGBA", (W_, H_), (10, 10, 12, 255))
    y = 0
    for b in blocks:
        sh.alpha_composite(b, (0, y))
        y += b.height + 6
    if max(sh.size) > 8000:
        k = 8000 / max(sh.size)
        sh = sh.resize((int(sh.width * k), int(sh.height * k)), Image.NEAREST)
    sh.save(out)
    return sh.size


if __name__ == "__main__":
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    dirs = ("right", "down")
    for a in sys.argv[2:]:
        if a.startswith("--dirs="):
            dirs = tuple(a[7:].split(","))
    print(main(sys.argv[1], args, dirs))


def fx_preview(out, names, rows_max=2, scale=2, bg=(18, 17, 20, 255)):
    blocks = []
    for n in names:
        j, fr = grid(os.path.join(P.STAGE_FX, n))
        W, H = j["frameWidth"], j["frameHeight"]
        k = scale if max(W, H) <= 320 else 1
        rows = j["directions"][:rows_max]
        img = Image.new("RGBA", (j["frames"] * (W * k + 4) + 90, 22 + len(rows) * (H * k + 4)), bg)
        dr = ImageDraw.Draw(img)
        dr.text((4, 4), "%s  %dx%d  colors=%s glow=%s ms=%s" % (n, W, H, j.get("colors"), j.get("glowFrames"), j["frameDurationsMs"]), fill=(220, 220, 220))
        y = 22
        for d in rows:
            dr.text((4, y + 4), d, fill=(160, 160, 160))
            for c in range(j["frames"]):
                t = Image.new("RGBA", (W, H), K6.hexrgb(K6.BG) + (255,))
                t.alpha_composite(fr[d][c])
                pv = j.get("pivot")
                if pv:
                    t.putpixel((min(W - 1, pv["x"]), min(H - 1, pv["y"])), (0, 255, 255, 255))
                img.alpha_composite(t.resize((W * k, H * k), Image.NEAREST), (90 + c * (W * k + 4), y))
            y += H * k + 4
        blocks.append(img)
    W_ = max(b.width for b in blocks)
    H_ = sum(b.height + 6 for b in blocks)
    sh = Image.new("RGBA", (W_, H_), (10, 10, 12, 255))
    y = 0
    for b in blocks:
        sh.alpha_composite(b, (0, y))
        y += b.height + 6
    if max(sh.size) > 8000:
        kk = 8000 / max(sh.size)
        sh = sh.resize((int(sh.width * kk), int(sh.height * kk)), Image.NEAREST)
    sh.save(out)
    return sh.size
