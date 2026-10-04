"""56라운드 작업 B 미리보기 — assets 의 시트를 읽어 합성(빌드 산출물 그대로 확인).

  gif/gs8_chain.gif           대검 8방향(3×3) 연격 H1 → V → H2 → V (몸+무기, 1배 = 게임 화면 크기)
  gif/gs8_charge.gif          대검 8방향 홀드 차지 → 기본 차지 내려찍기 / 꽂아내리기
  gif/gs_fx_<dir>.gif         연격·차지·꽂아내리기 + 바닥 균열·충격파 fx (right · down-right · up-left)
  preview_gs8_<동작>_x1.png   8행 전 프레임(노란 테 = 판정 프레임, 하늘색 점 = 칼끝, 빨간 점 = 꽂힌 자리)
"""
import json
import math
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
SPR = os.path.join(ROOT, "assets/sprites")
GIF = os.path.join(HERE, "gif")
BG = (30, 30, 35, 255)
FLOOR = (44, 41, 40, 255)
HIT_UP = 40
DIRS8 = ["down", "up", "left", "right", "down-right", "down-left", "up-right", "up-left"]
SCREEN_DEG = {"right": 0.0, "down-right": 45.0, "down": 90.0, "down-left": 135.0, "left": 180.0, "up-left": -135.0, "up": -90.0, "up-right": -45.0}
GRID = [["up-left", "up", "up-right"], ["left", None, "right"], ["down-left", "down", "down-right"]]
_cache = {}


def load(path):
    if path not in _cache:
        j = json.load(open(os.path.join(SPR, path + ".json"), encoding="utf-8"))
        im = Image.open(os.path.join(SPR, path + ".png")).convert("RGBA")
        _cache[path] = (j, im)
    return _cache[path]


def cell(path, row_key, i):
    j, im = load(path)
    r = j["directions"].index(row_key) if row_key in j["directions"] else 0
    fw, fh = j["frameWidth"], j["frameHeight"]
    return im.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh)), (j["pivot"]["x"], j["pivot"]["y"])


def frame_at(ms, t):
    acc = 0
    for i, m in enumerate(ms):
        acc += m
        if t < acc:
            return i
    return None


def paste_piv(canvas, im, piv, at):
    canvas.alpha_composite(im, (int(round(at[0] - piv[0])), int(round(at[1] - piv[1]))))


def player(canvas, move, d, i, at):
    b, bp = cell("player/v3/player_" + move, d, i)
    w, wp = cell("weapons/v3/" + move, d, i)
    paste_piv(canvas, b, bp, at)
    paste_piv(canvas, w, wp, at)


def fx(canvas, name, row, i, at, rot_deg=0.0):
    im, piv = cell("fx/v3/" + name, row, i)
    if rot_deg:
        # 피벗 기준 회전(최근접) — 큰 캔버스에 피벗을 가운데로 옮겨 돌린 뒤 붙임
        S = int(2 * math.hypot(max(piv[0], im.width - piv[0]), max(piv[1], im.height - piv[1]))) + 4
        big = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        big.alpha_composite(im, (S // 2 - piv[0], S // 2 - piv[1]))
        big = big.rotate(-rot_deg, resample=Image.NEAREST, center=(S // 2, S // 2))
        im, piv = big, (S // 2, S // 2)
    paste_piv(canvas, im, piv, at)


# =============================================================================
# 시트 미리보기
# =============================================================================
def sheet_preview(move, scale=1):
    bj, _ = load("player/v3/player_" + move)
    wj, _ = load("weapons/v3/" + move)
    fw, fh = wj["frameWidth"], wj["frameHeight"]
    n = bj["frames"]
    act = set(bj.get("activeFrames") or [])
    img = Image.new("RGBA", (fw * n + 90, fh * len(DIRS8) + 16), BG)
    dr = ImageDraw.Draw(img)
    dr.text((4, 2), "%s · %d frames · ms %s · yellow = hit frame" % (move, n, bj["frameDurationsMs"]), fill=(230, 230, 230, 255))
    for r, d in enumerate(DIRS8):
        dr.text((4, 16 + r * fh + fh // 2), d, fill=(200, 200, 200, 255))
        for i in range(n):
            x0, y0 = 90 + i * fw, 16 + r * fh
            at = (x0 + wj["pivot"]["x"], y0 + wj["pivot"]["y"])
            player(img, move, d, i, at)
            if i in act:
                dr.rectangle((x0, y0, x0 + fw - 1, y0 + fh - 1), outline=(230, 190, 40, 255))
            tip = wj["bladeTipAnchors"][d][i]
            if tip:
                dr.ellipse((x0 + tip[0] - 2, y0 + tip[1] - 2, x0 + tip[0] + 2, y0 + tip[1] + 2), outline=(90, 230, 230, 255))
            pa = wj.get("plantAnchors", {}).get(d, [None] * n)[i]
            if pa:
                dr.ellipse((x0 + pa[0] - 3, y0 + pa[1] - 3, x0 + pa[0] + 3, y0 + pa[1] + 3), outline=(240, 60, 60, 255))
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    img.save(os.path.join(HERE, "preview_gs8_%s_x%d.png" % (move, scale)))


# =============================================================================
# GIF
# =============================================================================
def timeline(seq):
    """seq = [(move, …)] → [(move, startMs)], 끝 ms."""
    out, t = [], 0
    for mv in seq:
        bj, _ = load("player/v3/player_" + mv)
        out.append((mv, t))
        t += sum(bj["frameDurationsMs"])
    return out, t


def at_time(tl, t):
    for mv, s in reversed(tl):
        if t >= s:
            bj, _ = load("player/v3/player_" + mv)
            i = frame_at(bj["frameDurationsMs"], t - s)
            if i is not None:
                return mv, i, t - s
    return None


def save_gif(frames, path, step):
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=step, loop=0, disposal=2)


def grid_gif(seq, path, cw=240, ch=250, step=40, scale=1, title=""):
    tl, end = timeline(seq)
    frames = []
    t = 0
    while t < end:
        img = Image.new("RGBA", (cw * 3, ch * 3 + 14), BG)
        dr = ImageDraw.Draw(img)
        a = at_time(tl, t)
        dr.text((4, 2), "%s  %s f%d  t=%dms" % (title, a[0] if a else "", a[1] if a else -1, t), fill=(220, 220, 220, 255))
        for r, row in enumerate(GRID):
            for c, d in enumerate(row):
                if d is None:
                    continue
                at = (c * cw + cw // 2, 14 + r * ch + int(ch * 0.78))
                if a:
                    player(img, a[0], d, a[1], at)
                dr.text((c * cw + 4, 16 + r * ch), d, fill=(150, 150, 160, 255))
                ang = math.radians(SCREEN_DEG[d])
                o = (at[0], at[1] - HIT_UP)
                dr.line([(o[0] + math.cos(ang) * 70, o[1] + math.sin(ang) * 70), (o[0] + math.cos(ang) * 90, o[1] + math.sin(ang) * 90)],
                        fill=(90, 200, 220, 255), width=2)
        if scale != 1:
            img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=255))
        t += step
    save_gif(frames, path, step)


def fx_events(tl):
    """동작별 fx: V = 균열 s(쐐기 끝 1.3R), 차지 내려찍기 = 균열 m(쐐기 끝 1.5R), 꽂아내리기 = 충격파 + 균열 l(꽂힌 자리)."""
    ev = []
    R = 204
    for mv, s in tl:
        bj, _ = load("player/v3/player_" + mv)
        if bj.get("impactFrame") is None:
            continue
        hit = s + sum(bj["frameDurationsMs"][:bj["impactFrame"]])
        if mv == "greatsword_cleave":
            ev.append(dict(kind="crack", row="s", t=hit, dist=R * 1.3))
        elif mv == "greatsword_charge_slam":
            ev.append(dict(kind="crack", row="m", t=hit, dist=R * 1.5))
        elif mv == "greatsword_charge_plunge":
            ev.append(dict(kind="wave", t=hit, plant=(mv, bj["impactFrame"])))
            ev.append(dict(kind="crack", row="l", t=hit, plant=(mv, bj["impactFrame"])))
    return ev


def fx_gif(seq, d, path, W=720, H=560, step=40, title=""):
    tl, end = timeline(seq)
    ev = fx_events(tl)
    frames = []
    t = 0
    feet = (W // 2 - int(math.cos(math.radians(SCREEN_DEG[d])) * 150), H // 2 + 60 - int(math.sin(math.radians(SCREEN_DEG[d])) * 120))
    ang = SCREEN_DEG[d]
    while t < end + 600:
        img = Image.new("RGBA", (W, H + 14), FLOOR)
        dr = ImageDraw.Draw(img)
        a = at_time(tl, min(t, end - 1))
        dr.text((4, 2), "%s  [%s]  %s f%d  t=%dms" % (title, d, a[0] if a else "", a[1] if a else -1, t), fill=(220, 220, 220, 255))
        for e in ev:                                       # 바닥 fx 는 몸 아래
            if e["kind"] != "crack" or t < e["t"]:
                continue
            j, _ = load("fx/v3/greatsword_ground_crack")
            i = frame_at(j["frameDurationsMs"], t - e["t"])
            if i is None:
                continue
            if "plant" in e:
                wj, _ = load("player/v3/player_" + e["plant"][0])
                pa = wj["plantAnchors"][d][e["plant"][1]]
                pos = (feet[0] + pa[0] - 48, feet[1] + pa[1] - 138)
            else:
                pos = (feet[0] + math.cos(math.radians(ang)) * e["dist"], feet[1] - HIT_UP + math.sin(math.radians(ang)) * e["dist"])
            fx(img, "greatsword_ground_crack", e["row"], i, pos)
        if a:
            player(img, a[0], d, a[1], feet)
        for e in ev:
            if e["kind"] != "wave" or t < e["t"]:
                continue
            j, _ = load("fx/v3/greatsword_plunge_wave")
            i = frame_at(j["frameDurationsMs"], t - e["t"])
            if i is None:
                continue
            wj, _ = load("player/v3/player_" + e["plant"][0])
            pa = wj["plantAnchors"][d][e["plant"][1]]
            fx(img, "greatsword_plunge_wave", "any", i, (feet[0] + pa[0] - 48, feet[1] + pa[1] - 138), ang)
        frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=255))
        t += step
    save_gif(frames, path, step)


CHAIN = ["greatsword_sweep_cw", "greatsword_cleave", "greatsword_sweep_ccw", "greatsword_cleave"]
CHARGE = ["greatsword_charge", "greatsword_charge", "greatsword_charge_slam", "greatsword_charge", "greatsword_charge_plunge"]


def main():
    os.makedirs(GIF, exist_ok=True)
    for mv in ("greatsword_sweep_cw", "greatsword_cleave", "greatsword_sweep_ccw", "greatsword_charge", "greatsword_charge_slam",
               "greatsword_charge_plunge"):
        sheet_preview(mv)
    grid_gif(CHAIN, os.path.join(GIF, "gs8_chain.gif"), title="H1>V>H2>V")
    grid_gif(CHARGE, os.path.join(GIF, "gs8_charge.gif"), title="charge>slam / charge>plunge")
    for d in ("right", "down-right", "up-left"):
        fx_gif(CHAIN + CHARGE, d, os.path.join(GIF, "gs_fx_%s.gif" % d), title="chain + charge")


if __name__ == "__main__":
    main()


# =============================================================================
# 활 (4방향)
# =============================================================================
DIRS4 = ["down", "up", "left", "right"]


def sheet_preview4(move, scale=2):
    bj, _ = load("player/v3/player_" + move)
    wj, _ = load("weapons/v3/" + move)
    fw, fh = wj["frameWidth"], wj["frameHeight"]
    n = bj["frames"]
    img = Image.new("RGBA", (fw * n + 60, fh * 4 + 16), BG)
    dr = ImageDraw.Draw(img)
    dr.text((4, 2), "%s · ms %s · roles %s" % (move, bj["frameDurationsMs"], bj.get("frameRoles")), fill=(230, 230, 230, 255))
    for r, d in enumerate(DIRS4):
        dr.text((4, 16 + r * fh + fh // 2), d, fill=(200, 200, 200, 255))
        for i in range(n):
            x0, y0 = 60 + i * fw, 16 + r * fh
            player(img, move, d, i, (x0 + wj["pivot"]["x"], y0 + wj["pivot"]["y"]))
            sp = wj.get("arrowSpawnAnchors", {}).get(d, [None] * n)[i]
            if sp:
                dr.ellipse((x0 + sp[0] - 2, y0 + sp[1] - 2, x0 + sp[0] + 2, y0 + sp[1] + 2), outline=(240, 60, 60, 255))
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    img.save(os.path.join(HERE, "preview_%s_x%d.png" % (move, scale)))


def bow_gif(path, perfect=True, step=30, scale=2):
    """당김 f0~f5 → 가득 유지 루프 2바퀴 → 놓기(+ 완벽 섬광) → 다시 당길 준비. 4방향 가로."""
    dh, _ = load("player/v3/player_bow_draw_hold")
    rl, _ = load("player/v3/player_bow_release")
    wr, _ = load("weapons/v3/bow_release")
    seq = [("bow_draw_hold", i, dh["frameDurationsMs"][i]) for i in range(6)]
    seq += [("bow_draw_hold", 6 + (i % 4), dh["frameDurationsMs"][6 + i % 4]) for i in range(6)]
    seq += [("bow_release", i, rl["frameDurationsMs"][i]) for i in range(4)]
    rel_t = sum(m for _, _, m in seq[:12])
    end = sum(m for _, _, m in seq) + 200
    pj, _ = load("fx/v3/bow_perfect_release")
    W, H = 200, 200
    frames = []
    t = 0
    while t < end:
        img = Image.new("RGBA", (W * 4, H + 14), FLOOR)
        dr = ImageDraw.Draw(img)
        acc, cur = 0, seq[-1]
        for s in seq:
            if t < acc + s[2]:
                cur = s
                break
            acc += s[2]
        dr.text((4, 2), "bow  %s f%d  t=%dms%s" % (cur[0], cur[1], t, "  PERFECT" if perfect and t >= rel_t else ""), fill=(220, 220, 220, 255))
        for c, d in enumerate(DIRS4):
            at = (c * W + W // 2, 14 + int(H * 0.8))
            player(img, cur[0], d, cur[1], at)
            if perfect and t >= rel_t:
                i = frame_at(pj["frameDurationsMs"], t - rel_t)
                if i is not None:
                    sp = wr["arrowSpawnAnchors"][d][0]
                    pos = (at[0] + sp[0] - wr["pivot"]["x"], at[1] + sp[1] - wr["pivot"]["y"])
                    fx(img, "bow_perfect_release", "any", i, pos, SCREEN_DEG[d])
        img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=255))
        t += step
    save_gif(frames, path, step)


def main_bow():
    os.makedirs(GIF, exist_ok=True)
    sheet_preview4("bow_draw_hold")
    sheet_preview4("bow_release")
    bow_gif(os.path.join(GIF, "bow_draw_release_perfect.gif"), perfect=True)
