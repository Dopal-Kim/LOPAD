"""미리보기 도우미 — 몸 + 무기 + 오버레이 합성, 격자·GIF."""
import json
import os

from PIL import Image, ImageDraw, ImageFont

import rk

BG = (34, 32, 36, 255)
BG_FLOOR = (52, 48, 46, 255)
HERE = rk.HERE
_cache = {}


def sheet(path):
    if path not in _cache:
        _cache[path] = rk.load_sheet(path)
    return _cache[path]


def font(sz=12):
    for p in ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
              "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def body_for(wj, wname):
    b = wj.get("bodySheet")
    if b:
        return "player/v3/" + b
    if "carry" in wname:
        act = wname.split("_carry_")[1].replace("drawn_", "")
        if wname.startswith("katana"):
            return "player/v3/player_%s" % act
        return "player/v3/player_%s_free" % act if act != "dash" else "player/v3/player_dash"
    return None


def compose(wname, overlay, d, i, W=260, H=300, origin=(130, 250)):
    """origin = 캔버스 속 주인공 피벗."""
    wj, wf = sheet("weapons/v3/" + wname)
    cv = Image.new("RGBA", (W, H), BG)
    bpath = body_for(wj, wname)
    if bpath and os.path.exists(os.path.join(rk.SPR, bpath + ".json")):
        bj, bf = sheet(bpath)
        if d in bf:
            bi = min(i, bj["frames"] - 1)
            cv.alpha_composite(bf[d][bi], (origin[0] - bj["pivot"]["x"], origin[1] - bj["pivot"]["y"]))
    off = wj["playerFrameOffset"]
    wx, wy = origin[0] - 48 - off["x"], origin[1] - 138 - off["y"]
    cv.alpha_composite(wf[d][i], (wx, wy))
    if overlay:
        oj, of = sheet("weapons/v3/" + overlay)
        cv.alpha_composite(of[d][i], (wx, wy))
    return cv


def grid(cells, cols, out, scale=2, labels=None, title=None):
    cw, ch = cells[0].size
    rows = (len(cells) + cols - 1) // cols
    top = 22 if title else 0
    lab = 16 if labels else 0
    im = Image.new("RGBA", (cw * scale * cols, top + (ch * scale + lab) * rows), (16, 16, 18, 255))
    dr = ImageDraw.Draw(im)
    f = font(12)
    if title:
        dr.text((6, 4), title, fill=(230, 230, 230), font=f)
    for k, c in enumerate(cells):
        x, y = (k % cols) * cw * scale, top + (k // cols) * (ch * scale + lab)
        im.paste(c.resize((cw * scale, ch * scale), Image.NEAREST), (x, y + lab))
        if labels:
            dr.text((x + 3, y + 1), labels[k], fill=(210, 210, 210), font=f)
    im.save(os.path.join(HERE, out))
    return out


def gif(frames, ms, out, scale=3):
    fr = [f.resize((f.width * scale, f.height * scale), Image.NEAREST).convert("RGB") for f in frames]
    fr[0].save(os.path.join(HERE, "gif", out), save_all=True, append_images=fr[1:], duration=ms, loop=0, disposal=1)
    return "gif/" + out
