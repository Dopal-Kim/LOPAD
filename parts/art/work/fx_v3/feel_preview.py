"""feel_preview — 55라운드 작업 B 미리보기 (feel/ 폴더).

- feel/hits_compare_x2.png   : 4무기 적중 스파크(일반·막타) 프레임 나열, 내부 렌더 픽셀 ×2
- feel/hits_rotated_x2.png   : 공격 방향 8각 회전 시험(f1)
- feel/hits_mock_1x.png      : 바닥 위 주인공·적 크기와 함께 1배
- feel/gif/<name>_1x.gif     : 실제 ms
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw

import feel_kit as K

FEEL = os.path.join(K.HERE, "feel")
FLOOR = os.path.join(K.ROOT, "assets", "tiles", "v2", "stage1_outer.png")
BG = (24, 22, 22, 255)


def floor_patch(w, h, seed=3, dim=0.55):
    t = Image.open(FLOOR).convert("RGBA")
    tiles = [t.crop(((i % 8) * 32, (i // 8) * 32, (i % 8) * 32 + 32, (i // 8) * 32 + 32))
             .resize((64, 64), Image.NEAREST) for i in (0, 1, 2, 3)]
    R = random.Random(seed)
    im = Image.new("RGBA", (w, h))
    for y in range(0, h, 64):
        for x in range(0, w, 64):
            im.alpha_composite(tiles[R.choice((0, 0, 0, 1, 2, 3))], (x, y))
    px = im.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            px[x, y] = (int(r * dim), int(g * dim), int(b * dim * 1.05), 255)
    return im


def frames(name, row=0):
    j, im = K.load_sheet(name)
    return j, [K.cell(im, j, row, c) for c in range(j["frames"])]


def strip(name, z=2, row=0, gap=6, bg=None, label=True):
    j, fr = frames(name, row)
    fw, fh = j["frameWidth"], j["frameHeight"]
    W = (fw * z + gap) * len(fr) + gap
    Hh = fh * z + gap * 2 + (14 if label else 0)
    out = Image.new("RGBA", (W, Hh), bg or BG)
    dr = ImageDraw.Draw(out)
    top = 14 if label else gap
    for i, f in enumerate(fr):
        x = gap + i * (fw * z + gap)
        dr.rectangle([x - 1, top - 1, x + fw * z, top + fh * z], outline=(48, 44, 44))
        out.alpha_composite(f.resize((fw * z, fh * z), Image.NEAREST), (x, top))
        if label:
            dr.text((x, 2), f"f{i} {j['frameDurationsMs'][i]}ms", fill=(170, 170, 170))
        px, py = j["pivot"]["x"] * z + x, j["pivot"]["y"] * z + top
        dr.point([(px, py)], fill=(90, 200, 255))
    return out


def stack(images, path, title=None, gap=8):
    W = max(i.width for i in images) + gap * 2
    Hh = sum(i.height for i in images) + gap * (len(images) + 1) + (16 if title else 0)
    out = Image.new("RGBA", (W, Hh), BG)
    dr = ImageDraw.Draw(out)
    y = gap
    if title:
        dr.text((gap, 3), title, fill=(220, 220, 220))
        y += 16
    for im in images:
        out.alpha_composite(im, (gap, y))
        y += im.height + gap
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path)
    return out


def labeled(im, text):
    out = Image.new("RGBA", (im.width, im.height + 14), BG)
    ImageDraw.Draw(out).text((4, 1), text, fill=(230, 200, 150))
    out.alpha_composite(im, (0, 14))
    return out


def hits_compare():
    rows = []
    for w in ("katana", "greatsword", "dagger", "bow"):
        rows.append(labeled(strip(f"hit_{w}"), f"hit_{w}  (blue dot = pivot = hit point, attack -> right)"))
        rows.append(labeled(strip(f"hit_{w}_heavy"), f"hit_{w}_heavy"))
    stack(rows, os.path.join(FEEL, "hits_compare_x2.png"),
          "55R Q8 hit sparks v3 — internal-render px x2 (1 dot = 2 px)")


def hits_rotated():
    """8 attack angles, f1 (and f0) — checks that rotation reads (nearest rotate like Phaser pixelArt)."""
    rows = []
    for w in ("katana", "greatsword", "dagger", "bow"):
        for heavy in ("", "_heavy"):
            j, fr = frames(f"hit_{w}{heavy}")
            cellw = 200 if heavy else 140
            out = Image.new("RGBA", (cellw * 8, cellw), BG)
            for k in range(8):
                ang = k * 45
                f = fr[1].copy()
                big = Image.new("RGBA", (cellw, cellw))
                big.alpha_composite(f, (cellw // 2 - j["pivot"]["x"], cellw // 2 - j["pivot"]["y"]))
                big = big.rotate(-ang, resample=Image.NEAREST, center=(cellw // 2, cellw // 2))
                out.alpha_composite(big, (k * cellw, 0))
            rows.append(labeled(out, f"hit_{w}{heavy} f1 rotated 0..315 (screen angle, cw)"))
    stack(rows, os.path.join(FEEL, "hits_rotated_x1.png"), "rotation check x1 (nearest)")


def gif(name, row=0, pad=10, scale=1, path=None):
    j, fr = frames(name, row)
    fw, fh = j["frameWidth"], j["frameHeight"]
    bg = floor_patch(fw + pad * 2, fh + pad * 2, seed=7)
    out = []
    for f in fr:
        im = bg.copy()
        im.alpha_composite(f, (pad, pad))
        if scale != 1:
            im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        out.append(im.convert("RGB"))
    hold = list(j["frameDurationsMs"])
    if not j.get("loop"):
        e = bg.resize((bg.width * scale, bg.height * scale), Image.NEAREST) if scale != 1 else bg
        out.append(e.convert("RGB"))
        hold.append(300)
    os.makedirs(os.path.join(FEEL, "gif"), exist_ok=True)
    out[0].save(path or os.path.join(FEEL, "gif", f"{name}_x{scale}.gif"), save_all=True,
                append_images=out[1:], duration=[max(20, h) for h in hold], loop=0)


def hits_mock():
    """1x internal render: hero v3 + enemy-sized dummy, each weapon's hit at f1 on a target."""
    im = floor_patch(960, 360)
    hero = Image.open(os.path.join(K.HERO, "player_idle.png")).convert("RGBA").crop((3 * 96, 0, 4 * 96, 144))
    dr = ImageDraw.Draw(im)
    for i, w in enumerate(("katana", "greatsword", "dagger", "bow")):
        x0 = 30 + i * 235
        im.alpha_composite(hero, (x0, 170))
        tx, ty = x0 + 160, 170 + 138 - 40          # target body centre ~ judgement origin 40 dots up
        # stand-in enemy: dark silhouette box 96x144 like enemies v3
        dr.rectangle([tx - 30, 170 + 20, tx + 30, 170 + 138], fill=(36, 30, 30, 255))
        heavy = "_heavy" if i % 2 else ""
        j, fr = frames(f"hit_{w}{heavy}")
        im.alpha_composite(fr[1], (tx - 18 - j["pivot"]["x"], ty - 30 - j["pivot"]["y"]))
        j2, fr2 = frames(f"hit_{w}")
        im.alpha_composite(fr2[0], (tx - 18 - j2["pivot"]["x"], ty + 30 - j2["pivot"]["y"]))
        dr.text((x0, 150), f"{w}: f1{heavy or ''} / f0", fill=(220, 220, 220))
    dr.text((6, 4), "1x internal px (960x540 = 480x270 logical); hero v3 96x144; dark box = enemy body", fill=(220, 220, 220))
    os.makedirs(FEEL, exist_ok=True)
    im.save(os.path.join(FEEL, "hits_mock_1x.png"))


def particles_preview():
    j, im = K.load_sheet("particles_ash")
    z = 8
    rows = []
    for name, k in j["kinds"].items():
        a, b = k["frames"]
        n = b - a + 1
        out = Image.new("RGBA", (n * (16 * z + 6) + 260, 16 * z + 8), BG)
        dr = ImageDraw.Draw(out)
        for i in range(n):
            c = K.cell(im, j, 0, a + i).resize((16 * z, 16 * z), Image.NEAREST)
            x = i * (16 * z + 6)
            dr.rectangle([x, 4, x + 16 * z - 1, 4 + 16 * z - 1], fill=(34, 31, 31))
            out.alpha_composite(c, (x, 4))
        dr.text((n * (16 * z + 6) + 6, 10), f"{name}  frames {a}-{b}  {k['frameMode']}", fill=(230, 200, 150))
        dr.text((n * (16 * z + 6) + 6, 26), f"life {k['lifeMs']}ms  g {k['gravityPxPerSec2']}", fill=(170, 170, 170))
        rows.append(out)
    stack(rows, os.path.join(FEEL, "particles_ash_x8.png"), "particles_ash  (16x16 cells, x8)")
    # simulated burst at 1x and x3 (internal px): greatsword_heavy recipe, t = 0, 120, 260, 420 ms
    rec = j["recipes"]["hit_greatsword_heavy"]
    R = random.Random(5)
    parts = []
    for name, cnt in rec.items():
        if name == "coneDeg":
            continue
        k = j["kinds"][name]
        for _ in range(cnt):
            ang = math.radians(R.uniform(-rec["coneDeg"] / 2, rec["coneDeg"] / 2))
            sp = R.uniform(*k["speedPxPerSec"])
            parts.append((name, k, ang, sp, R.uniform(*k["lifeMs"]), R.random()))
    W, Hh = 240, 160
    shots = []
    for t in (0.04, 0.12, 0.26, 0.42, 0.7):
        bg = floor_patch(W, Hh, seed=9)
        for name, k, ang, sp, life, ph in parts:
            if t * 1000 > life:
                continue
            drag = k["dragPerSec"]
            dist = sp * (1 - math.exp(-drag * t)) / drag
            gx = 0.5 * k["gravityPxPerSec2"] * t * t
            x = 70 + math.cos(ang) * dist * 2                 # logical -> internal x2
            y = 80 + math.sin(ang) * dist * 2 + gx * 2
            a, b = k["frames"]
            n = b - a + 1
            if k["frameMode"] == "life":
                fi = a + min(n - 1, int(t * 1000 / life * n))
            else:
                fi = a + int((t * 1000 + ph * 300) / k["frameMs"]) % n
            c = K.cell(im, j, 0, fi)
            if k.get("rotate"):
                vx, vy = math.cos(ang) * sp, math.sin(ang) * sp + k["gravityPxPerSec2"] * t
                c = c.rotate(-math.degrees(math.atan2(vy, vx)), resample=Image.NEAREST)
            bg.alpha_composite(c, (int(x) - 8, int(y) - 8))
        ImageDraw.Draw(bg).text((4, 4), f"t={int(t * 1000)}ms", fill=(220, 220, 220))
        shots.append(bg.resize((W * 2, Hh * 2), Image.NEAREST))
    out = Image.new("RGBA", (W * 2 * len(shots) + 8 * (len(shots) + 1), Hh * 2 + 16), BG)
    for i, sh in enumerate(shots):
        out.alpha_composite(sh, (8 + i * (W * 2 + 8), 8))
    out.save(os.path.join(FEEL, "particles_burst_sim_x2.png"))


def ribbon_preview():
    rows = []
    for name in ("ribbon_ash", "ribbon_ash_thin"):
        j, im = K.load_sheet(name)
        z = 12
        out = Image.new("RGBA", (64 * z + 200, (j["frameHeight"] * z + 10) * 4 + 10), BG)
        dr = ImageDraw.Draw(out)
        for f in range(4):
            c = K.cell(im, j, 0, f).resize((64 * z, j["frameHeight"] * z), Image.NEAREST)
            y = 6 + f * (j["frameHeight"] * z + 10)
            dr.rectangle([0, y, 64 * z - 1, y + j["frameHeight"] * z - 1], fill=(34, 31, 31))
            out.alpha_composite(c, (0, y))
            dr.text((64 * z + 8, y), f"{name} age f{f} ({[0, 33, 66, 100][f]}ms)", fill=(230, 200, 150))
        rows.append(out)
    # ribbon laid along a swing arc (nearest stretch), x3 of internal px, tail -> head
    j, im = K.load_sheet("ribbon_ash")
    W, Hh = 220, 160
    bg = floor_patch(W, Hh, seed=4)
    px = bg.load()
    cx, cy, r = 70, 120, 90
    a0, a1 = math.radians(-150), math.radians(-20)      # tail .. head
    L = int(r * (a1 - a0))
    for s in range(L):
        u = s / (L - 1)
        a = a0 + (a1 - a0) * u
        # older part of the ribbon = later age frame
        age = 3 if u < 0.25 else 2 if u < 0.5 else 1 if u < 0.75 else 0
        tex = K.cell(im, j, 0, age)
        tx = min(63, int(u * 64))
        for k in range(3):
            c = tex.getpixel((tx, k))
            if c[3]:
                rr = r + (k - 1)
                x, y = int(cx + math.cos(a) * rr), int(cy + math.sin(a) * rr)
                if 0 <= x < W and 0 <= y < Hh:
                    px[x, y] = c
    ImageDraw.Draw(bg).text((4, 4), "ribbon on a swing arc (age by segment)", fill=(220, 220, 220))
    rows.append(bg.resize((W * 3, Hh * 3), Image.NEAREST))
    stack(rows, os.path.join(FEEL, "ribbon_ash_x12.png"), "ribbon_ash / ribbon_ash_thin (x12) + arc mock (x3)")


MOTION = ["dash_trail", "dash_dust", "parry_flash", "guard_wave", "ironwall", "shadowstep_ghost", "aim_charge"]
BEFORE = os.path.join(K.HERE, "feel", "before")


def _load(path_dir, name):
    j = json.load(open(os.path.join(path_dir, name + ".json")))
    im = Image.open(os.path.join(path_dir, name + ".png")).convert("RGBA")
    return j, im


def motion_compare(name):
    jb, ib = _load(BEFORE, name)
    ja, ia = _load(K.OUT, name)
    z = 2 if ia.width * 2 <= 2400 else 1
    rows = []
    for tag, j, im in (("before", jb, ib), ("after (55R)", ja, ia)):
        big = Image.new("RGBA", (im.width * z, im.height * z), (34, 31, 31, 255))
        big.alpha_composite(im.resize((im.width * z, im.height * z), Image.NEAREST))
        dr = ImageDraw.Draw(big)
        fw, fh = j["frameWidth"] * z, j["frameHeight"] * z
        for c in range(1, len(j["frameDurationsMs"])):
            dr.line([(c * fw, 0), (c * fw, big.height)], fill=(60, 56, 56))
        for r in range(1, len(j["directions"])):
            dr.line([(0, r * fh), (big.width, r * fh)], fill=(60, 56, 56))
        rows.append(labeled(big, f"{name} {tag}: {len(j['frameDurationsMs'])}f {j['frameDurationsMs']} ms, "
                                 f"{j['frameWidth']}x{j['frameHeight']}, colors {j.get('colors')}"))
    stack(rows, os.path.join(FEEL, "motion", f"cmp_{name}_x{z}.png"))


HERO_ATTACHED = {"dash_trail": ("player_dash", 2), "dash_dust": ("player_dash", 1),
                 "shadowstep_ghost": ("player_idle_free", 0), "guard_wave": ("player_greatsword_special", 0),
                 "ironwall": ("player_greatsword_special", 0), "aim_charge": ("player_bow_aim", 0)}


def motion_gif(name, row_name="right", scale=2):
    """before | after side by side on floor, real ms (10 ms timeline)."""
    jb, ib = _load(BEFORE, name)
    ja, ia = _load(K.OUT, name)
    W = max(ja["frameWidth"], jb["frameWidth"]) + (110 if name in ("dash_trail", "shadowstep_ghost") else 40)
    Hh = max(ja["frameHeight"], jb["frameHeight"]) + 40
    if name in ("dash_dust",):
        Hh += 110
    hero = None
    if name in HERO_ATTACHED:
        sh, col = HERO_ATTACHED[name]
        hj = json.load(open(os.path.join(K.HERO, sh + ".json")))
        him = Image.open(os.path.join(K.HERO, sh + ".png")).convert("RGBA")
        r = hj["directions"].index(row_name) if row_name in hj["directions"] else 0
        hero = (him.crop((col * hj["frameWidth"], r * hj["frameHeight"], (col + 1) * hj["frameWidth"],
                          (r + 1) * hj["frameHeight"])), hj["pivot"])
    floor = floor_patch(W, Hh, seed=11)

    def panel(j, im, t):
        bg = floor.copy()
        rr = j["directions"].index(row_name) if row_name in j["directions"] else 0
        ms = j["frameDurationsMs"]
        if j.get("progressDriven"):
            fi = min(len(ms) - 1, int(t / 600 * (len(ms) - 1) + 0.0)) if t < 700 else None
        else:
            acc, fi = 0, None
            for i, m in enumerate(ms):
                if t < acc + m:
                    fi = i
                    break
                acc += m
        ax, ay = W // 2 - (30 if name in ("dash_trail", "shadowstep_ghost") else 0), Hh - 30 if name != "parry_flash" else Hh // 2
        if name in ("aim_charge",):
            ay = Hh // 2 + 40
        hero_xy = (ax, ay if name not in ("aim_charge",) else ay)
        trail = name in ("dash_trail", "shadowstep_ghost")
        if hero and not trail:
            hi, hp = hero
            bg.alpha_composite(hi, (hero_xy[0] - hp["x"], hero_xy[1] - hp["y"]))
        if fi is not None:
            c = K.cell(im, j, rr, fi)
            px_, py_ = j["pivot"]["x"], j["pivot"]["y"]
            ox = ax - px_ - (36 if trail else 0)
            oy = (ay - px_ * 0 - py_) if name != "aim_charge" else (ay - 40 - py_)
            bg.alpha_composite(c, (ox, oy))
        if hero and trail:
            hi, hp = hero
            bg.alpha_composite(hi, (hero_xy[0] + 40 - hp["x"], hero_xy[1] - hp["y"]))
        return bg

    total = max(sum(ja["frameDurationsMs"]), sum(jb["frameDurationsMs"]))
    if ja.get("progressDriven"):
        total = 700
    frames, durs, last = [], [], None
    for t in range(0, total + 300, 10):
        a, b = panel(jb, ib, t), panel(ja, ia, t)
        out = Image.new("RGBA", (W * 2 + 6, Hh + 14), BG)
        out.alpha_composite(a, (0, 14))                 # a = before (jb)
        out.alpha_composite(b, (W + 6, 14))             # b = after (ja)
        dr = ImageDraw.Draw(out)
        dr.text((4, 1), "before", fill=(200, 200, 200))
        dr.text((W + 10, 1), "after 55R", fill=(230, 200, 150))
        out = out.resize((out.width * scale, out.height * scale), Image.NEAREST).convert("RGB")
        if last is not None and list(out.getdata()) == last:
            durs[-1] += 10
            continue
        frames.append(out)
        durs.append(10)
        last = list(out.getdata())
    os.makedirs(os.path.join(FEEL, "motion"), exist_ok=True)
    durs = [max(20, d) for d in durs]
    frames[0].save(os.path.join(FEEL, "motion", f"ba_{name}_{row_name}_x{scale}.gif"), save_all=True,
                   append_images=frames[1:], duration=durs, loop=0)


def scene_mock():
    """1x internal render 960x540: hero + enemies stand-ins with every new fx in context."""
    im = floor_patch(960, 540, seed=21)
    dr = ImageDraw.Draw(im)

    def hero_cell(sheet, col, row="right"):
        hj = json.load(open(os.path.join(K.HERO, sheet + ".json")))
        him = Image.open(os.path.join(K.HERO, sheet + ".png")).convert("RGBA")
        r = hj["directions"].index(row)
        return him.crop((col * hj["frameWidth"], r * hj["frameHeight"], (col + 1) * hj["frameWidth"],
                         (r + 1) * hj["frameHeight"])), hj["pivot"]

    def place(name, x, y, row=0, f=0):
        j, im2 = K.load_sheet(name)
        im.alpha_composite(K.cell(im2, j, row, f), (x - j["pivot"]["x"], y - j["pivot"]["y"]))

    def enemy(x, y):
        dr.rectangle([x - 28, y - 118, x + 28, y], fill=(40, 33, 32, 255), outline=(70, 58, 52, 255))

    # 1) dash: trail f0,f1,f2 behind hero + dust
    place("dash_trail", 70, 250, 3, 2)
    place("dash_trail", 110, 250, 3, 1)
    place("dash_trail", 150, 250, 3, 0)
    place("dash_dust", 175, 250, 3, 1)
    hc, hp = hero_cell("player_dash", 2)
    im.alpha_composite(hc, (200 - hp["x"], 250 - hp["y"]))
    # 2) katana hits + ribbon arc + particles
    hc, hp = hero_cell("player_idle", 0)
    im.alpha_composite(hc, (330 - hp["x"], 250 - hp["y"]))
    enemy(450, 250)
    place("hit_katana", 440, 210, 0, 1)
    rj, rim = K.load_sheet("ribbon_ash")
    px = im.load()
    cx, cy, r = 340, 205, 96
    a0, a1 = math.radians(-120), math.radians(30)
    L = int(r * (a1 - a0))
    for st in range(L):
        u = st / (L - 1)
        a = a0 + (a1 - a0) * u
        age = 3 if u < 0.25 else 2 if u < 0.5 else 1 if u < 0.75 else 0
        tex = K.cell(rim, rj, 0, age)
        for k in range(3):
            c = tex.getpixel((min(63, int(u * 64)), k))
            if c[3]:
                x, y = int(cx + math.cos(a) * (r + k - 1)), int(cy + math.sin(a) * (r + k - 1))
                px[x, y] = c
    pj, pim = K.load_sheet("particles_ash")
    R = random.Random(3)
    for name, n in (("ember_streak", 4), ("ember_s", 3), ("ash_s", 3), ("ash_m", 2)):
        a_, b_ = pj["kinds"][name]["frames"]
        for _ in range(n):
            ang = R.uniform(-0.5, 0.5)
            d = R.uniform(30, 70)
            c = K.cell(pim, pj, 0, R.randint(a_, b_))
            if name == "ember_streak":
                c = c.rotate(-math.degrees(ang), resample=Image.NEAREST)
            im.alpha_composite(c, (int(440 + math.cos(ang) * d) - 8, int(210 + math.sin(ang) * d + d * 0.3) - 8))
    # 3) greatsword heavy hit + guard wave + ironwall
    enemy(640, 250)
    place("hit_greatsword_heavy", 630, 200, 0, 2)
    hc, hp = hero_cell("player_idle_free", 0, "down")
    im.alpha_composite(hc, (800 - hp["x"], 250 - hp["y"]))
    place("guard_wave", 800, 250, 0, 2)
    place("ironwall", 800, 250, 0, 1)
    # 4) dagger / bow hits + parry + aim charge + shadowstep
    enemy(150, 500)
    place("hit_dagger_heavy", 140, 450, 0, 1)
    place("hit_dagger", 160, 420, 0, 0)
    enemy(360, 500)
    place("hit_bow", 345, 440, 0, 0)
    place("hit_bow_heavy", 360, 470, 0, 1)
    place("shadowstep_ghost", 520, 500, 3, 1)
    hc, hp = hero_cell("player_idle_free", 0)
    im.alpha_composite(hc, (600 - hp["x"], 500 - hp["y"]))
    hc, hp = hero_cell("player_bow_aim", 0)
    im.alpha_composite(hc, (760 - hp["x"], 500 - hp["y"]))
    place("aim_charge", 760, 460, 0, 3)
    place("parry_flash", 900, 420, 0, 1)
    dr.text((6, 4), "55R task B mock — 1x internal px (960x540 = 480x270 logical). fx unlit, floor dim 0.55. "
                    "dark boxes = enemy stand-ins", fill=(220, 220, 220))
    im.save(os.path.join(FEEL, "scene_mock_1x.png"))


def hits_gif4(scale=2):
    """4 weapons side by side (top normal, bottom heavy), real ms on a 10 ms timeline."""
    ws = ("katana", "greatsword", "dagger", "bow")
    cw, ch = 200, 200
    floor = floor_patch(cw * 4, ch * 2, seed=13)
    sheets = {f"hit_{w}{h}": K.load_sheet(f"hit_{w}{h}") for w in ws for h in ("", "_heavy")}
    total = max(sum(j["frameDurationsMs"]) for j, _ in sheets.values()) + 250
    frames, durs, last = [], [], None
    for t in range(0, total, 10):
        im = floor.copy()
        dr = ImageDraw.Draw(im)
        for i, w in enumerate(ws):
            for r, h in enumerate(("", "_heavy")):
                j, sh = sheets[f"hit_{w}{h}"]
                acc, fi = 0, None
                for k, m in enumerate(j["frameDurationsMs"]):
                    if t < acc + m:
                        fi = k
                        break
                    acc += m
                cx, cy = i * cw + 80, r * ch + 100
                dr.rectangle([cx - 26, cy - 60, cx + 26, cy + 50], fill=(40, 33, 32), outline=(70, 58, 52))
                if fi is not None:
                    im.alpha_composite(K.cell(sh, j, 0, fi), (cx - j["pivot"]["x"], cy - j["pivot"]["y"]))
                dr.text((i * cw + 4, r * ch + 4), f"{w}{h}", fill=(220, 220, 220))
        out = im.resize((im.width * scale // 2 * 2 // 2, im.height * scale // 2 * 2 // 2), Image.NEAREST).convert("RGB") if scale == 1 else im.convert("RGB")
        data = out.tobytes()
        if last == data:
            durs[-1] += 10
            continue
        frames.append(out)
        durs.append(10)
        last = data
    durs = [max(20, d) for d in durs]
    frames[0].save(os.path.join(FEEL, "gif", "hits_4weapons_1x.gif"), save_all=True, append_images=frames[1:],
                   duration=durs, loop=0)


if __name__ == "__main__":
    import sys
    what = sys.argv[1:] or ["hits", "particles", "ribbon", "motion"]
    if "hits" in what:
        hits_compare()
        hits_rotated()
        hits_mock()
        for n in ("hit_katana", "hit_greatsword", "hit_dagger", "hit_bow", "hit_katana_heavy",
                  "hit_greatsword_heavy", "hit_dagger_heavy", "hit_bow_heavy"):
            gif(n, scale=2)
        hits_gif4(1)
    if "particles" in what:
        particles_preview()
    if "ribbon" in what:
        ribbon_preview()
    if "mock" in what or not sys.argv[1:]:
        scene_mock()
    if "motion" in what:
        for n in MOTION:
            motion_compare(n)
            for rn in (("right", "down") if n not in ("parry_flash", "aim_charge") else ("any",)):
                motion_gif(n, rn, scale=1 if n in ("guard_wave", "ironwall", "parry_flash") else 2)
    _ = (json, math)
