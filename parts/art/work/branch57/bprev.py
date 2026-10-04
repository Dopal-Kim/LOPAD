"""57라운드 갈래 1단 미리보기 — assets 시트(격자·아틀라스 양쪽, atlas57/gridsheet)를 시간축으로 합성한 GIF·대표 PNG.

출력(이 폴더): gif/<이름>.gif (×2, 어두운 바닥) · preview_<이름>.png (대표 칸 줄, ×2) · preview_fx_sheets.png(fx 시트 모음)
작업용 확인 그림이다 — assets 에 넣지 않는다. 미리보기 안의 적(회색 기둥)·투사체 이동은 시스템 동작을 흉내 낸 것(참고).
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "atlas57"))
import gridsheet  # noqa: E402

ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets/sprites")
GIF = os.path.join(HERE, "gif")
BG = (34, 30, 36, 255)
TILE = 64
_cache = {}


def sheet(rel):
    if rel not in _cache:
        p = os.path.join(SPR, rel + ".json")
        m = gridsheet.load_meta(p)
        _cache[rel] = (m, gridsheet.open_grid(p))
    return _cache[rel]


def cell(rel, row, i):
    m, im = sheet(rel)
    r = m["directions"].index(row) if isinstance(row, str) else row
    fw, fh = m["frameWidth"], m["frameHeight"]
    i = max(0, min(m["frames"] - 1, i))
    return im.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh)), (m["pivot"]["x"], m["pivot"]["y"])


def put(cv, rel, row, i, x, y, ang=0.0):
    im, (px, py) = cell(rel, row, i)
    if ang:
        R = int(math.hypot(max(px, im.width - px), max(py, im.height - py))) + 2
        big = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0))
        big.alpha_composite(im, (R - px, R - py))
        big = big.rotate(-ang, resample=Image.NEAREST)
        im, px, py = big, R, R
    cv.alpha_composite(im, (int(round(x - px)), int(round(y - py))))


def frame_at(ms, t, loop=False):
    tot = sum(ms)
    if loop:
        t %= tot
    acc = 0
    for i, m in enumerate(ms):
        if t < acc + m:
            return i
        acc += m
    return None


def meta(rel):
    return sheet(rel)[0]


def floor(w, h):
    cv = Image.new("RGBA", (w, h), BG)
    d = ImageDraw.Draw(cv)
    for x in range(0, w, TILE):
        d.line([(x, 0), (x, h)], fill=(40, 36, 42, 255))
    for y in range(0, h, TILE):
        d.line([(0, y), (w, y)], fill=(40, 36, 42, 255))
    return cv


def dummy(cv, x, y):
    d = ImageDraw.Draw(cv)
    d.ellipse([x - 22, y - 8, x + 22, y + 8], fill=(26, 24, 28, 255))
    d.rectangle([x - 16, y - 96, x + 16, y], fill=(70, 66, 72, 255), outline=(20, 20, 22, 255))


def save_gif(name, frames, step, scale=2):
    os.makedirs(GIF, exist_ok=True)
    out, durs = [], []
    for f in frames:
        f = f.resize((f.width * scale, f.height * scale), Image.NEAREST).convert("RGB")
        if out and out[-1].tobytes() == f.tobytes():
            durs[-1] += step
            continue
        out.append(f)
        durs.append(step)
    out[0].save(os.path.join(GIF, name + ".gif"), save_all=True, append_images=out[1:], duration=durs, loop=0, disposal=1)
    return os.path.join(GIF, name + ".gif")


def strip(name, frames, idx, scale=2, box=None):
    ims = [frames[i] if box is None else frames[i].crop(box) for i in idx]
    w, h = ims[0].size
    c = Image.new("RGBA", (w * len(ims), h), BG)
    for k, im in enumerate(ims):
        c.alpha_composite(im, (k * w, 0))
    c = c.resize((c.width * scale, c.height * scale), Image.NEAREST)
    p = os.path.join(HERE, "preview_%s.png" % name)
    c.save(p)
    return p


# =============================================================================
def body_track(body, row, t, hold_loops=0, hold=None, release=None):
    """몸 시트 시간 → 프레임(홀드 루프를 hold_loops 번 돈 뒤 releaseFrame 으로)."""
    m = meta("player/v3/player_" + body)
    ms = m["frameDurationsMs"]
    if hold is None:
        return frame_at(ms, t)
    pre = sum(ms[:hold[0]])
    lp = sum(ms[hold[0]:hold[-1] + 1])
    if t < pre:
        return frame_at(ms, t)
    if t < pre + lp * hold_loops:
        return hold[0] + frame_at(ms[hold[0]:hold[-1] + 1], (t - pre) % lp)
    t2 = t - pre - lp * hold_loops
    r = frame_at(ms[release:], t2)
    return None if r is None else release + r


def katana(name, row, hold_loops, fx_extra=None, ki=None):
    m = meta("player/v3/player_" + name)
    hold, rel = m["holdFrames"], m["releaseFrame"]
    ms = m["frameDurationsMs"]
    pre = sum(ms[:hold[0]])
    lp = sum(ms[hold[0]:hold[-1] + 1])
    t_rel = pre + lp * hold_loops
    total = t_rel + sum(ms[rel:]) + 300
    fxm = meta("fx/v3/" + name)
    st = [sum(ms[:k]) for k in range(len(ms))]
    fx_t0 = t_rel + (fxm["spawnAtMs"] - st[rel])
    W_, H_ = 560, 480
    cx, cy = W_ // 2, 300
    frames = []
    step = 10
    for t in range(0, total, step):
        cv = floor(W_, H_)
        if name == "katana_guardbreak":
            dummy(cv, cx + (TILE * 2 if row == "right" else 0), cy + (TILE * 2 if row == "down" else 0))
        i = body_track(name, row, t, hold_loops, hold, rel)
        fi = frame_at(fxm["frameDurationsMs"], t - fx_t0) if t >= fx_t0 else None
        if fi is not None and fxm.get("depth") == "below_player":
            put(cv, "fx/v3/" + name, row, fi, cx, cy)
        if i is not None:
            put(cv, "player/v3/player_" + name, row, i, cx, cy)
            put(cv, "weapons/v3/" + name, row, i, cx, cy)
            if ki:
                put(cv, "weapons/v3/%s_ki%d" % (name, ki), row, i, cx, cy)
        if fi is not None and fxm.get("depth") != "below_player":
            put(cv, "fx/v3/" + name, row, fi, cx, cy)
        if fx_extra:
            fx_extra(cv, t, cx, cy, i)
        frames.append(cv)
    return frames, step


def spin_ready(row):
    wm = meta("weapons/v3/katana_spin")
    rm = meta("fx/v3/katana_spin_ready")

    def f(cv, t, cx, cy, i):
        if 400 <= t < 400 + sum(rm["frameDurationsMs"]) and i is not None:
            tip = wm["bladeTipAnchors"][row][i]
            if tip:
                pv = wm["pivot"]
                put(cv, "fx/v3/katana_spin_ready", "any", frame_at(rm["frameDurationsMs"], t - 400), cx + tip[0] - pv["x"], cy + tip[1] - pv["y"])
    return f


def dagger_throw(row):
    name = "dagger_fan_throw"
    m = meta("player/v3/player_" + name)
    wm = meta("weapons/v3/" + name)
    fxm = meta("fx/v3/" + name)
    ms = m["frameDurationsMs"]
    rel_t = sum(ms[:m["releaseFrame"]])
    dash = meta("player/v3/player_dash")
    dms = dash["frameDurationsMs"]
    t_dash = sum(dms)
    total = t_dash + sum(ms) + 500
    W_, H_ = 640, 520
    cx, cy = 200 if row == "right" else 320, 300 if row == "right" else 160
    aim = {"right": 0, "down": 90, "left": 180, "up": -90}[row]
    sp = wm["throwSpawnAnchors"][row][m["releaseFrame"]]
    off = (sp[0] - wm["pivot"]["x"], sp[1] - wm["pivot"]["y"])
    frames, step = [], 10
    for t in range(0, total, step):
        cv = floor(W_, H_)
        for k in range(3):
            dummy(cv, int(cx + math.cos(math.radians(aim + (k - 1) * 15)) * TILE * 4.5),
                  int(cy + 40 + math.sin(math.radians(aim + (k - 1) * 15)) * TILE * 4.5)) if k == 1 else None
        if t < t_dash:
            dx = -TILE * 2 * (1 - t / t_dash)
            px_ = cx + dx * math.cos(math.radians(aim))
            py_ = cy + dx * math.sin(math.radians(aim))
            put(cv, "player/v3/player_dash", row, frame_at(dms, t), px_, py_)
            put(cv, "weapons/v3/dagger_carry_dash", row, frame_at(dms, t), px_, py_)
        else:
            tt = t - t_dash
            i = frame_at(ms, tt)
            if i is not None:
                put(cv, "player/v3/player_" + name, row, i, cx, cy)
                put(cv, "weapons/v3/" + name, row, i, cx, cy)
            fi = frame_at(fxm["frameDurationsMs"], tt - fxm["spawnAtMs"]) if tt >= fxm["spawnAtMs"] else None
            if fi is not None:
                put(cv, "fx/v3/" + name, row, fi, cx, cy)
            if tt >= rel_t:
                age = tt - rel_t
                dist = min(age * 1.0, TILE * 6)
                if dist < TILE * 6:
                    for a in m["fanDeg"]:
                        ang = aim + a
                        put(cv, "fx/v3/dagger_thrown", "any", (age // 50) % 4, cx + off[0] + math.cos(math.radians(ang)) * dist,
                            cy + off[1] + math.sin(math.radians(ang)) * dist, ang)
        frames.append(cv)
    return frames, step


def bow_rapid(row):
    name = "bow_rapid_loop"
    m = meta("player/v3/player_" + name)
    wm = meta("weapons/v3/" + name)
    ms = m["frameDurationsMs"]
    lf = m["loopFrames"]
    pre = sum(ms[:lf[0]])
    lp = sum(ms[lf[0]:lf[-1] + 1])
    loops = 2
    total = pre + lp * loops + sum(ms[lf[-1] + 1:]) + 300
    W_, H_ = 640, 360
    cx, cy = 160, 240
    aim = 0 if row == "right" else 90
    arrows = []
    frames, step = [], 10
    for t in range(0, total, step):
        cv = floor(W_, H_)
        if t < pre:
            i = frame_at(ms, t)
        elif t < pre + lp * loops:
            i = lf[0] + frame_at(ms[lf[0]:lf[-1] + 1], (t - pre) % lp)
        else:
            i = lf[-1] + 1 + (frame_at(ms[lf[-1] + 1:], t - pre - lp * loops) or 0)
            if t - pre - lp * loops >= sum(ms[lf[-1] + 1:]):
                i = len(ms) - 1
        if i in m["releaseFrames"] and t < pre + lp * loops and (not arrows or t - arrows[-1][0] > 60):
            sp = wm["arrowSpawnAnchors"][row][i]
            arrows.append((t, cx + sp[0] - wm["pivot"]["x"], cy + sp[1] - wm["pivot"]["y"]))
        put(cv, "player/v3/player_" + name, row, i, cx, cy)
        put(cv, "weapons/v3/" + name, row, i, cx, cy)
        for t0, ax, ay in arrows:
            age = t - t0
            if age < 60:
                put(cv, "fx/v3/bow_muzzle_rapid", "any", 0 if age < 30 else 1, ax, ay, aim)
            d_ = age * 1.6
            if d_ < 600:
                put(cv, "fx/v3/bow_arrow_rapid", "any", (age // 40) % 2, ax + math.cos(math.radians(aim)) * d_, ay + math.sin(math.radians(aim)) * d_, aim)
        frames.append(cv)
    return frames, step


def bow_pierce():
    W_, H_ = 720, 240
    y = 150
    xs = [260, 380, 500]
    hm = meta("fx/v3/bow_arrow_pierce_hit")
    pm = meta("fx/v3/bow_perfect_release")
    frames, step = [], 10
    for t in range(0, 900, step):
        cv = floor(W_, H_)
        for x in xs:
            dummy(cv, x, y + 40)
        if t < sum(pm["frameDurationsMs"]):
            put(cv, "fx/v3/bow_perfect_release", "any", frame_at(pm["frameDurationsMs"], t), 60, y)
        ax = 60 + t * 0.8
        for x in xs:
            hit_t = (x - 60) / 0.8
            if hit_t <= t < hit_t + sum(hm["frameDurationsMs"]):
                put(cv, "fx/v3/bow_arrow_pierce_hit", "any", frame_at(hm["frameDurationsMs"], t - hit_t), x, y)
        if ax < W_ + 40:
            put(cv, "fx/v3/bow_arrow_pierce", "any", (t // 50) % 4, ax, y)
        frames.append(cv)
    return frames, step


def cross_clone(row):
    W_, H_ = 560, 520
    ex, ey = 280, 280                                  # 적 히트박스 중심
    v = {"right": (1, 0), "down": (0, 1), "left": (-1, 0), "up": (0, -1)}[row]
    px_, py_ = ex - v[0] * 44, ey - v[1] * 44 + 40      # 주인공 발(적 등 뒤)
    cm = meta("fx/v3/dagger_cross_clone")
    bm = meta("fx/v3/dagger_brand_burst")
    km = meta("player/v3/player_dagger_backstab")
    frames, step = [], 10
    total = sum(cm["frameDurationsMs"]) + 200
    for t in range(0, total, step):
        cv = floor(W_, H_)
        items = [(ey + 40, "dummy"), (py_, "player")]
        ci = frame_at(cm["frameDurationsMs"], t)
        for _, kind in sorted(items):
            if kind == "dummy":
                dummy(cv, ex, ey + 40)
            else:
                put(cv, "player/v3/player_dagger_backstab", row, 0, px_, py_)
                put(cv, "weapons/v3/dagger_backstab", row, 0, px_, py_)
        bi = frame_at(bm["frameDurationsMs"], t)
        if bi is not None:
            put(cv, "fx/v3/dagger_brand_burst", "l", bi, ex, ey)
        if ci is not None:
            put(cv, "fx/v3/dagger_cross_clone", row, ci, ex, ey)
        frames.append(cv)
    return frames, step


def greatsword():
    W_, H_ = 760, 520
    frames, step = [], 10
    sm = meta("fx/v3/greatsword_shatter_crack_t5")
    qm = meta("fx/v3/greatsword_quake_ring")
    nm = meta("fx/v3/greatsword_shatter_snuff")
    bullet = (560, 140)
    total = 1100
    for t in range(0, total, step):
        cv = floor(W_, H_)
        # 왼쪽: 파쇄 lv3(5칸) 오른쪽 위로 30° — 탄 1발이 경로 위에서 지워짐
        si = frame_at(sm["frameDurationsMs"], t)
        if si is not None:
            put(cv, "fx/v3/greatsword_shatter_crack_t5", "any", si, 120, 300, -30)
        fr_ = sm["hitShape"]["frontPxByFrame"][si] if si is not None else 999
        if fr_ < 280:
            ImageDraw.Draw(cv).ellipse([bullet[0] - 46 - 5, 300 - 140 + 0, bullet[0] - 46 + 5, 300 - 140 + 10], fill=(200, 80, 60, 255))
        elif t < 400:
            put(cv, "fx/v3/greatsword_shatter_snuff", "any", frame_at(nm["frameDurationsMs"], t - 120) or 0, bullet[0] - 46, 300 - 135)
        qi = frame_at(qm["frameDurationsMs"], t - 150) if t >= 150 else None
        if qi is not None:
            put(cv, "fx/v3/greatsword_quake_ring", "lv2", qi, 560, 380)
        frames.append(cv)
    return frames, step


def fx_contact():
    names = ["katana_spin", "katana_guardbreak", "dagger_fan_throw", "dagger_cross_clone", "greatsword_shatter_crack_t3", "greatsword_shatter_crack_t5", "greatsword_quake_ring",
             "katana_spin_ready", "greatsword_shatter_snuff", "dagger_thrown", "bow_arrow_pierce", "bow_arrow_pierce_hit"]
    ims = []
    for n in names:
        m, im = sheet("fx/v3/" + n)
        bg = Image.new("RGBA", im.size, BG)
        bg.alpha_composite(im)
        d = ImageDraw.Draw(bg)
        d.text((2, 2), n, fill=(200, 200, 200, 255))
        if bg.width > 2400:
            bg = bg.resize((bg.width // 2, bg.height // 2), Image.NEAREST)
        ims.append(bg)
    W_ = max(i.width for i in ims)
    H_ = sum(i.height + 4 for i in ims)
    c = Image.new("RGBA", (W_, H_), (16, 16, 18, 255))
    y = 0
    for i in ims:
        c.alpha_composite(i, (0, y))
        y += i.height + 4
    p = os.path.join(HERE, "preview_fx_sheets.png")
    c.save(p)
    return p


def main():
    out = []
    for row in ("right", "down"):
        fr, st = katana("katana_spin", row, 2, fx_extra=spin_ready(row), ki=None)
        out.append(save_gif("katana_spin_%s" % row, fr, st))
        if row == "right":
            out.append(strip("katana_spin_right", fr, [5, 40, 69, 72, 76, 80, 84, 90, 100], box=(80, 110, 480, 460)))
        fr, st = katana("katana_spin", row, 1, ki=3)
        out.append(save_gif("katana_spin_ki3_%s" % row, fr, st))
        fr, st = katana("katana_guardbreak", row, 1)
        out.append(save_gif("katana_guardbreak_%s" % row, fr, st))
        if row == "right":
            out.append(strip("katana_guardbreak_right", fr, [10, 30, 45, 60, 100, 104, 108, 112, 120], box=(150, 120, 520, 400)))
        fr, st = dagger_throw(row)
        out.append(save_gif("dagger_fan_throw_%s" % row, fr, st))
        if row == "right":
            out.append(strip("dagger_fan_throw_right", fr, [5, 25, 30, 34, 38, 42, 46, 52, 60], box=(80, 140, 560, 380)))
        fr, st = bow_rapid(row)
        out.append(save_gif("bow_rapid_loop_%s" % row, fr, st))
        fr, st = cross_clone(row)
        out.append(save_gif("dagger_cross_clone_%s" % row, fr, st))
        if row == "right":
            out.append(strip("dagger_cross_clone_right", fr, [2, 7, 10, 13, 16, 20, 28, 36, 44], box=(130, 110, 450, 400)))
    fr, st = bow_pierce()
    out.append(save_gif("bow_arrow_pierce", fr, st))
    out.append(strip("bow_arrow_pierce", fr, [5, 30, 40, 50, 60, 70]))
    fr, st = greatsword()
    out.append(save_gif("greatsword_shatter_quake", fr, st))
    out.append(strip("greatsword_shatter_quake", fr, [4, 8, 12, 20, 24, 30, 40, 55, 80]))
    out.append(fx_contact())
    print("\n".join(out))
    return out


if __name__ == "__main__":
    main()
