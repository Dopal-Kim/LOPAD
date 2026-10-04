"""작업 E2 미리보기 — 이 폴더에만 쓴다(게임 산출물 아님).

  preview_mock_dagger_backstab.gif / _x2.png   결사병 등 뒤에서 치명 찌르기(몸 + 단검 + fx) — 4방향
  preview_mock_dagger_flurry.gif               고속 난타: 시작 → 루프 2바퀴 → 끝, 과열 1·2·3단 나란히(오른쪽·아래)
  preview_mock_bow_arrow_rain.gif / _x2.png    화살비 전체 장면: 하늘로 3발 → 예고 원 → 낙하 9발 → 원 사라짐(임시 타이밍)
  preview_fx_sheets.png                        새 fx 시트 7종 전 프레임(2배)
  gif/preview_<동작>_x2.png · _x3.gif          몸 + 무기 프레임 표(body 단계가 씀)
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
SP = os.path.join(ROOT, "assets/sprites")
BG = (38, 40, 46, 255)
FLOOR = (52, 50, 54, 255)
FONT = None
for f in ["/usr/share/fonts/truetype/unifont/unifont.ttf", "/usr/share/fonts/opentype/unifont/unifont.otf"]:
    if os.path.exists(f):
        FONT = ImageFont.truetype(f, 16)
        break
FONT = FONT or ImageFont.load_default()


def label(dr, x, y, t, col=(235, 236, 237)):
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        dr.text((x + dx, y + dy), t, font=FONT, fill=(0, 0, 0))
    dr.text((x, y), t, font=FONT, fill=col)


_CACHE = {}


def sheet(path):
    if path in _CACHE:
        return _CACHE[path]
    j = json.load(open(os.path.join(SP, path + ".json"), encoding="utf-8"))
    im = Image.open(os.path.join(SP, path + ".png")).convert("RGBA")
    fw, fh, n = j["frameWidth"], j["frameHeight"], j["frames"]
    rows = {r: [im.crop((c * fw, i * fh, (c + 1) * fw, (i + 1) * fh)) for c in range(n)] for i, r in enumerate(j["directions"])}
    _CACHE[path] = (j, rows)
    return j, rows


def paste(cv, path, row, i, at, flip=False):
    j, rows = sheet(path)
    fr = rows[row][min(i, len(rows[row]) - 1)]
    px, py = j["pivot"]["x"], j["pivot"]["y"]
    if flip:
        fr = fr.transpose(Image.FLIP_LEFT_RIGHT)
        px = j["frameWidth"] - 1 - px
    cv.alpha_composite(fr, (int(round(at[0] - px)), int(round(at[1] - py))))


def frame_at(ms, t):
    """시트 시작 후 t ms → 프레임 번호(끝나면 None)."""
    if t < 0:
        return None
    acc = 0
    for i, m in enumerate(ms):
        acc += m
        if t < acc:
            return i
    return None


def seq_index(seq, t):
    acc = 0
    for i, m in seq:
        acc += m
        if t < acc:
            return i
    return seq[-1][0]


def floor(w, h):
    cv = Image.new("RGBA", (w, h), BG)
    dr = ImageDraw.Draw(cv)
    for y in range(0, h, 64):
        for x in range(0, w, 64):
            if (x // 64 + y // 64) % 2:
                dr.rectangle([x, y, x + 63, y + 63], fill=FLOOR)
    return cv


def save_gif(frames, durs, path, scale=2):
    out, dd = [], []
    for f, d in zip(frames, durs):
        if out and list(f.getdata()) == list(out[-1].getdata()):
            dd[-1] += d
            continue
        out.append(f)
        dd.append(d)
    big = [f.resize((f.width * scale, f.height * scale), Image.NEAREST).convert("RGB") for f in out]
    big[0].save(path, save_all=True, append_images=big[1:], duration=dd, loop=0, disposal=1)


def player(cv, name, row, i, at):
    paste(cv, "player/v3/player_" + name, row, i, at)
    paste(cv, "weapons/v3/" + name, row, i, at)


# =============================================================================
DOFF = {"right": (1, 0), "left": (-1, 0), "down": (0, 1), "up": (0, -1)}


def mock_backstab():
    name = "dagger_backstab"
    bj, _ = sheet("player/v3/player_" + name)
    fj, _ = sheet("fx/v3/" + name)
    ms = bj["frameDurationsMs"]
    total = sum(ms) + 160
    W_, H_ = 220, 230
    gif, durs = [], []
    strip_rows = []
    for t in range(0, total, 10):
        row_imgs = []
        for d in ("right", "left", "down", "up"):
            cv = floor(W_, H_)
            pc = (110 - DOFF[d][0] * 26, 170 - DOFF[d][1] * 22)
            ec = (pc[0] + DOFF[d][0] * 52, pc[1] + DOFF[d][1] * 34)
            bi = frame_at(ms, t)
            bi = len(ms) - 1 if bi is None else bi
            items = [(ec[1], lambda cv=cv, d=d, ec=ec: paste(cv, "enemies/v3/charger_idle", d, 0, ec)),
                     (pc[1], lambda cv=cv, d=d, pc=pc, bi=bi: player(cv, name, d, bi, pc))]
            for _, fn in sorted(items, key=lambda x: x[0]):
                fn()
            fi = frame_at(fj["frameDurationsMs"], t - fj["spawnAtMs"])
            if fi is not None:
                paste(cv, "fx/v3/" + name, d, fi, pc)
            row_imgs.append(cv)
        comb = Image.new("RGBA", (W_ * 4, H_), BG)
        for k, im in enumerate(row_imgs):
            comb.alpha_composite(im, (k * W_, 0))
        gif.append(comb)
        durs.append(10)
    save_gif(gif, durs, os.path.join(HERE, "preview_mock_dagger_backstab.gif"), scale=2)
    # 정지 표: 몸 프레임 시작 시각마다
    st = [sum(ms[:i]) for i in range(len(ms))] + [sum(ms) + 60]
    tiles = [gif[min(len(gif) - 1, s // 10)] for s in st]
    big = Image.new("RGBA", (W_ * 4, H_ * len(tiles)), BG)
    for k, im in enumerate(tiles):
        big.alpha_composite(im, (0, k * H_))
    dr = ImageDraw.Draw(big)
    for k, s in enumerate(st):
        label(dr, 4, k * H_ + 4, "t=%dms  body f%d %s" % (s, min(k, len(ms) - 1), bj["frameRoles"][min(k, len(ms) - 1)]))
    big = big.resize((big.width * 2, big.height * 2), Image.NEAREST)
    big.save(os.path.join(HERE, "preview_mock_dagger_backstab_x2.png"))


def mock_flurry():
    name = "dagger_flurry"
    bj, _ = sheet("player/v3/player_" + name)
    ms = bj["frameDurationsMs"]
    lf = bj["loopFrames"]
    seq = [(0, ms[0]), (1, ms[1])] + [(i, ms[i]) for i in lf] * 3 + [(8, ms[8]), (9, ms[9]), (9, 200)]
    total = sum(m for _, m in seq)
    W_, H_ = 260, 250
    fxs = ["dagger_flurry", "dagger_flurry_heat2", "dagger_flurry_heat3"]
    gif, durs = [], []
    for t in range(0, total, 5):
        bi = seq_index(seq, t)
        comb = Image.new("RGBA", (W_ * 3, H_ * 2), BG)
        for r, d in enumerate(("right", "down")):
            for c, fx in enumerate(fxs):
                cv = floor(W_, H_)
                pc = (100 if d == "right" else 130, 180 if d == "right" else 120)
                ec = (pc[0] + DOFF[d][0] * 70, pc[1] + DOFF[d][1] * 44)
                if d == "down":
                    player(cv, name, d, bi, pc)
                    paste(cv, "enemies/v3/charger_idle", "up", 0, ec)
                else:
                    paste(cv, "enemies/v3/charger_idle", "left", 0, ec)
                    player(cv, name, d, bi, pc)
                paste(cv, "fx/v3/" + fx, d, bi, pc)
                comb.alpha_composite(cv, (c * W_, r * H_))
        dr = ImageDraw.Draw(comb)
        for c, fx in enumerate(fxs):
            label(dr, c * W_ + 4, 4, ["과열 1단", "과열 2단", "과열 3단"][c])
        gif.append(comb)
        durs.append(5)
    # GIF 최소 단위 10ms — 5ms 샘플을 두 개씩 묶음
    g2, d2 = gif[::2], [10] * len(gif[::2])
    save_gif(g2, d2, os.path.join(HERE, "preview_mock_dagger_flurry.gif"), scale=2)


# =============================================================================
RAIN_START_AFTER_RELEASE1 = 300     # 임시: 첫 화살을 쏜 뒤 0.3초에 낙하 시작
FALLS = 9
FALL_GAP = 40


def rain_events(center, R, seed=3):
    r = random.Random(seed)
    pts = []
    while len(pts) < FALLS:
        a = r.uniform(0, 2 * math.pi)
        d = R * math.sqrt(r.uniform(0.0, 0.9))
        pts.append((center[0] + math.cos(a) * d, center[1] + math.sin(a) * d, r.random() < 0.5))
    return pts


def mock_rain(d="right"):
    name = "bow_arrow_rain"
    bj, _ = sheet("player/v3/player_" + name)
    wj, _ = sheet("weapons/v3/" + name)
    rj, _ = sheet("fx/v3/bow_arrow_rain_rise")
    fj, _ = sheet("fx/v3/bow_arrow_rain_fall")
    mj, _ = sheet("fx/v3/bow_arrow_rain_mark")
    ms = bj["frameDurationsMs"]
    rel = bj["timingMs"]["releasesAt"]
    W_, H_ = 640, 460
    pc = (110, 300) if d == "right" else (320, 170)
    R = mj["sizeInfo"]["m"]["radiusPx"]
    center = (pc[0] + 340, pc[1] - 60) if d == "right" else (pc[0], pc[1] + 150)
    rain0 = rel[0] + RAIN_START_AFTER_RELEASE1
    pts = rain_events(center, R)
    fall_hit = sum(fj["frameDurationsMs"][:fj["impactFrame"]])
    last_end = rain0 + FALL_GAP * (FALLS - 1) + sum(fj["frameDurationsMs"])
    total = last_end + sum(mj["frameDurationsMs"][8:]) + 150
    ph = mj["phases"]
    gif, durs = [], []
    snaps = {}
    for t in range(0, total, 10):
        cv = floor(W_, H_)
        # 예고 원(바닥): 나타남 → 대기 루프 → 쏟아짐(낙하 동안) → 사라짐
        mt = t                                   # 임시: 좌클릭(몸 f0 시작)에 예고 원이 나타남
        if mt >= 0:
            mms = mj["frameDurationsMs"]
            app = mms[0] + mms[1]
            lastimp = rain0 + FALL_GAP * (FALLS - 1) + fall_hit
            if mt < app:
                mi = 0 if mt < mms[0] else 1
            elif t < rain0 + fall_hit:
                loop = sum(mms[2:6])
                q = (mt - app) % loop
                mi = 2 + (frame_at(mms[2:6], q) or 0)
            elif t < lastimp + 120:
                mi = 6 if (t - rain0) < 160 else 7
            else:
                q = t - (lastimp + 120)
                mi = 8 if q < mms[8] else (9 if q < mms[8] + mms[9] else None)
            if mi is not None:
                paste(cv, "fx/v3/bow_arrow_rain_mark", "m", mi, center)
        bi = frame_at(ms, t)
        bi = len(ms) - 1 if bi is None else bi
        player(cv, name, d, bi, pc)
        for k, rf in enumerate(bj["releaseFrames"]):
            fi = frame_at(rj["frameDurationsMs"], t - rel[k])
            if fi is not None:
                sp = wj["arrowSpawnAnchors"][d][rf]
                at = (pc[0] + sp[0] - wj["pivot"]["x"], pc[1] + sp[1] - wj["pivot"]["y"])
                paste(cv, "fx/v3/bow_arrow_rain_rise", d, fi, at)
        for k, (x, y, fl) in enumerate(sorted(pts, key=lambda p: p[1])):
            fi = frame_at(fj["frameDurationsMs"], t - (rain0 + FALL_GAP * k))
            if fi is not None:
                paste(cv, "fx/v3/bow_arrow_rain_fall", "any", fi, (x, y), flip=fl)
        dr = ImageDraw.Draw(cv)
        label(dr, 4, 4, "t=%4dms  body f%d" % (t, bi))
        gif.append(cv)
        durs.append(10)
        snaps[t] = cv
    save_gif(gif, durs, os.path.join(HERE, "preview_mock_bow_arrow_rain_%s.gif" % d), scale=2)
    keys = [0, 60, rel[0], rel[0] + 40, rel[1], rel[2], rel[2] + 80, rain0, rain0 + fall_hit, rain0 + fall_hit + 120,
            rain0 + 280, last_end - 60, last_end + 120]
    keys = [min(total - 10, k // 10 * 10) for k in keys]
    cols = 4
    rows = -(-len(keys) // cols)
    big = Image.new("RGBA", (W_ * cols, H_ * rows), BG)
    for k, t in enumerate(keys):
        big.alpha_composite(snaps[t], ((k % cols) * W_, (k // cols) * H_))
    big.resize((big.width * 2 // 2, big.height * 2 // 2), Image.NEAREST).save(os.path.join(HERE, "preview_mock_bow_arrow_rain_%s.png" % d))


def fx_sheets():
    names = ["dagger_backstab", "dagger_flurry", "dagger_flurry_heat2", "dagger_flurry_heat3", "bow_arrow_rain_rise",
             "bow_arrow_rain_fall", "bow_arrow_rain_mark"]
    blocks = []
    for n in names:
        j, rows = sheet("fx/v3/" + n)
        fw, fh = j["frameWidth"], j["frameHeight"]
        b = Image.new("RGBA", (fw * j["frames"] + 80, fh * len(rows) + 24), BG)
        dr = ImageDraw.Draw(b)
        label(dr, 2, 2, "%s  %dx%d  ms %s  glow %s" % (n, fw, fh, j["frameDurationsMs"], j.get("glowFrames")))
        for r, (rk, lst) in enumerate(rows.items()):
            label(dr, 2, 24 + r * fh + fh // 2, rk)
            for c, im in enumerate(lst):
                x, y = 80 + c * fw, 24 + r * fh
                dr.rectangle([x, y, x + fw - 1, y + fh - 1], outline=(60, 62, 70))
                b.alpha_composite(im, (x, y))
        blocks.append(b)
    Wd = max(b.width for b in blocks)
    Hd = sum(b.height for b in blocks)
    out = Image.new("RGBA", (Wd, Hd), BG)
    y = 0
    for b in blocks:
        out.alpha_composite(b, (0, y))
        y += b.height
    out.save(os.path.join(HERE, "preview_fx_sheets.png"))
    # 단검 fx 는 크기가 커서 2배 자르기(오른쪽 행만)도 따로
    for n in names[:4]:
        j, rows = sheet("fx/v3/" + n)
        lst = rows["right"]
        fw, fh = j["frameWidth"], j["frameHeight"]
        b = Image.new("RGBA", (fw * len(lst), fh), BG)
        for c, im in enumerate(lst):
            b.alpha_composite(im, (c * fw, 0))
        b.resize((b.width * 2, b.height * 2), Image.NEAREST).save(os.path.join(HERE, "wip", "fx_%s_right_x2.png" % n))


def main():
    os.makedirs(os.path.join(HERE, "wip"), exist_ok=True)
    fx_sheets()
    mock_backstab()
    mock_flurry()
    mock_rain("right")
    mock_rain("down")
    print("preview ok")


if __name__ == "__main__":
    main()
