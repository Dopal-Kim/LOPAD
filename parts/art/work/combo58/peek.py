"""58라운드 작업용 미리보기 도구 — assets(아틀라스) 또는 격자 시트에서 몸+무기(+오버레이)를 합성한 줄 그림."""
import json, os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))
import gridsheet  # noqa
SPR = os.path.join(ROOT, "assets/sprites")
BG = (34, 30, 36, 255)


def load(rel):
    m = gridsheet.load_meta(os.path.join(SPR, rel + ".json"))
    im = gridsheet.open_grid(os.path.join(SPR, rel + ".json"))
    return m, im


def cells(m, im):
    fw, fh, F = m["frameWidth"], m["frameHeight"], m["frames"]
    out = {}
    for r, d in enumerate(m["directions"]):
        out[d] = [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(F)]
    return out


def compose(body, weapon=None, overlay=None, dirs=None, scale=2, pad=8, label=True, fx=None):
    """body/weapon/overlay = 'player/v3/player_x' 경로. fx = (경로, spawnFrameOfBody)"""
    bm, bi = load(body)
    bc = cells(bm, bi)
    layers = []
    if weapon:
        wm, wi = load(weapon)
        layers.append((wm, cells(wm, wi)))
    if overlay:
        om, oi = load(overlay)
        layers.append((om | {"playerFrameOffset": wm["playerFrameOffset"]}, cells(om, oi)))
    dirs = dirs or bm["directions"]
    F = bm["frames"]
    # 캔버스: 무기 틀 기준
    if weapon:
        W, H = wm["frameWidth"], wm["frameHeight"]
        ox, oy = wm["playerFrameOffset"]["x"], wm["playerFrameOffset"]["y"]
    else:
        W, H, ox, oy = 96, 144, 0, 0
    sheet = Image.new("RGBA", (W * F, H * len(dirs)), BG)
    for r, d in enumerate(dirs):
        for i in range(F):
            cell = Image.new("RGBA", (W, H), BG)
            cell.alpha_composite(bc[d][i], (ox, oy))
            for lm, lc in layers:
                cell.alpha_composite(lc[d][i], (0, 0))
            sheet.paste(cell, (i * W, r * H))
    sheet = sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)
    if label:
        dr = ImageDraw.Draw(sheet)
        for r, d in enumerate(dirs):
            dr.text((4, r * H * scale + 4), d, fill=(255, 255, 255, 255))
            for i in range(F):
                dr.text((i * W * scale + W * scale - 20, r * H * scale + 4), str(i), fill=(200, 200, 200, 255))
    return sheet


if __name__ == "__main__":
    name = sys.argv[1]
    dirs = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else None
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join("/tmp", name + ".png")
    sc = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    compose("player/v3/player_" + name, "weapons/v3/" + name, dirs=dirs, scale=sc).save(out)
    print(out)


def frame_at(ms_list, t):
    acc = 0
    for i, m in enumerate(ms_list):
        if t < acc + m:
            return i
        acc += m
    return None


def timeline(body, weapon=None, fxs=(), d="right", times=None, canvas=(640, 520), piv=(320, 330), overlay=None, bg=BG, extra=None):
    """몸·무기(·오버레이)·fx 를 같은 시각에 겹친 프레임 목록. fxs = [(경로, spawnAtMs, 행 키 또는 None, (dx, dy) 피벗 이동)].
    extra(img, t) 로 추가 그림. times 없으면 몸 프레임 시작 시각들."""
    bm, bi = load(body)
    bc = cells(bm, bi)
    wl = None
    if weapon:
        wm, wi = load(weapon)
        wl = (wm, cells(wm, wi))
    ol = None
    if overlay:
        om, oi = load(overlay)
        ol = (om, cells(om, oi))
    fl = []
    for path, spawn, row, off in fxs:
        fm, fi = load(path)
        fl.append((fm, cells(fm, fi), spawn, row, off))
    ms = bm["frameDurationsMs"]
    if times is None:
        times = [sum(ms[:i]) for i in range(len(ms))]
    out = []
    for t in times:
        im = Image.new("RGBA", canvas, bg)
        i = frame_at(ms, t)
        if i is None:
            i = len(ms) - 1
        layers_after = []
        for fm, fc, spawn, row, off in fl:
            ft = t - spawn
            if ft < 0:
                continue
            k = frame_at(fm["frameDurationsMs"], ft)
            if k is None:
                continue
            r = row or d
            c = fc[r][k]
            p = fm["pivot"]
            pos = (piv[0] - p["x"] + off[0], piv[1] - p["y"] + off[1])
            if fm.get("depth") in ("below_player",):
                im.alpha_composite(c, (int(pos[0]), int(pos[1])))
            else:
                layers_after.append((c, pos))
        im.alpha_composite(bc[d][i], (piv[0] - bm["pivot"]["x"], piv[1] - bm["pivot"]["y"]))
        if wl:
            wm, wc = wl
            o = wm["playerFrameOffset"]
            im.alpha_composite(wc[d][i], (piv[0] - bm["pivot"]["x"] - o["x"], piv[1] - bm["pivot"]["y"] - o["y"]))
            if ol:
                im.alpha_composite(ol[1][d][i], (piv[0] - bm["pivot"]["x"] - o["x"], piv[1] - bm["pivot"]["y"] - o["y"]))
        for c, pos in layers_after:
            im.alpha_composite(c, (int(pos[0]), int(pos[1])))
        if extra:
            extra(im, t)
        out.append(im)
    return out


def strip(frames, scale=1, labels=None):
    w, h = frames[0].size
    s = Image.new("RGBA", (w * len(frames), h), BG)
    for i, f in enumerate(frames):
        s.paste(f, (i * w, 0))
    s = s.resize((s.width * scale, s.height * scale), Image.NEAREST)
    if labels:
        dr = ImageDraw.Draw(s)
        for i, l in enumerate(labels):
            dr.text((i * w * scale + 4, 4), str(l), fill=(230, 230, 230, 255))
    return s


def grid(rows, scale=1):
    w = max(r.width for r in rows)
    h = sum(r.height for r in rows)
    g = Image.new("RGBA", (w, h), BG)
    y = 0
    for r in rows:
        g.paste(r, (0, y))
        y += r.height
    return g.resize((g.width * scale, g.height * scale), Image.NEAREST)


def save_gif(frames, path, ms, scale=1):
    fr = [f.convert("RGB").resize((f.width * scale, f.height * scale), Image.NEAREST) for f in frames]
    fr[0].save(path, save_all=True, append_images=fr[1:], duration=ms, loop=0, optimize=True)
