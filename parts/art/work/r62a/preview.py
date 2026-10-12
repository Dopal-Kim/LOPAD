"""62a 미리보기 — preview_ritual(1920 렌더: 등 그림 + 먹 획 3 + 빛무리), preview_ritual_ui(960 논리 ×2: 일기장 첫 장·운명 액자·붓 시트·팻말),
preview_birth(탄생 전장 무대 목업: 새 바닥·데칼·birth_* 소품, 위 = 맨 그림 / 아래 = 어둠 + 불빛), preview_tiles(황무지·수련장 전/후)."""
import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))
import gridsheet  # noqa: E402
from common import SPR, TILES, A, G, S  # noqa: E402

FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"     # 미리보기 글자 전용(게임은 Galmuri)
RIT = os.path.join(SPR, "ritual")
T = 64


def font(sz):
    try:
        return ImageFont.truetype(FONT, sz)
    except OSError:
        return ImageFont.load_default()


def stamps():
    sheet = Image.open(os.path.join(RIT, "ink_brush.png")).convert("RGBA")
    meta = json.load(open(os.path.join(RIT, "ink_brush.json"), encoding="utf-8"))
    out = {}
    for k, v in meta["frames"].items():
        f = v["frame"]
        out[k] = sheet.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"]))
    return out


def tint(im, col):
    r, g, b, a = im.split()
    rr = r.point(lambda v: v * col[0] // 255)
    gg = g.point(lambda v: v * col[1] // 255)
    bb = b.point(lambda v: v * col[2] // 255)
    return Image.merge("RGBA", (rr, gg, bb, a))


def stamp_at(rt, st, x, y):
    rt.alpha_composite(st, (int(round(x - st.width / 2)), int(round(y - st.height / 2))))


def draw_stroke(rt, pts, col, st):
    """UI 가 할 일을 흉내: press → tip(속도에 따라 굵기) → 끝 15% dry → flick."""
    seg = []
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / 1.2))
        for i in range(n):
            t = i / n
            seg.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    seg.append(pts[-1])
    N = len(seg)
    stamp_at(rt, tint(st["press_d10"], col), *seg[0])
    for i, (x, y) in enumerate(seg):
        t = i / N
        if t > 0.85:
            ang = math.atan2(seg[min(N - 1, i + 1)][1] - y, seg[min(N - 1, i + 1)][0] - x)
            r = int(round(ang / (math.pi / 4))) % 8
            stamp_at(rt, tint(st[f"dry_d6_r{r}"], col), x, y)
        else:
            d = 8 if t < 0.15 else (6 if t < 0.6 else 5)
            stamp_at(rt, tint(st[f"tip_d{d}"], col), x, y)
    a, b = seg[-3], seg[-1]
    r = int(round(math.atan2(b[1] - a[1], b[0] - a[0]) / (math.pi / 4))) % 8
    stamp_at(rt, tint(st[f"flick_r{r}"], col), *seg[-1])


def preview_ritual():
    canvas = Image.open(os.path.join(RIT, "back_canvas.png")).convert("RGBA")
    meta = json.load(open(os.path.join(RIT, "back_canvas.json"), encoding="utf-8"))
    glow = Image.open(os.path.join(RIT, "back_canvas_glow.png")).convert("RGBA")
    st = stamps()
    rt = Image.new("RGBA", (640, 360), (0, 0, 0, 0))
    ink = (20, 21, 22)
    ember = (232, 184, 88)
    # 세 획: 1 = 막 그은 먹, 2·3 = 판정 뒤 불씨 먹
    s1 = [(262, 150), (290, 186), (308, 230), (318, 280)]
    s2 = [(372, 156), (352, 200), (340, 238)]
    s3 = [(268, 262), (320, 252), (382, 270)]
    halo = Image.new("RGBA", (640, 360), (0, 0, 0, 0))
    draw_stroke(halo, s2, (214, 122, 17), st)
    draw_stroke(halo, s3, (214, 122, 17), st)
    draw_stroke(rt, s2, ember, st)
    draw_stroke(rt, s3, ember, st)
    draw_stroke(rt, s1, ink, st)
    big = canvas.copy()
    gx, gy = meta["glow"]["x"], meta["glow"]["y"]
    g_full = Image.new("RGBA", big.size, (0, 0, 0, 0))
    g_full.alpha_composite(glow, (gx, gy))
    hb = halo.resize((1920, 1080), Image.NEAREST).filter(ImageFilter.GaussianBlur(14))
    for g in (g_full, hb):
        add = Image.merge("RGB", [ImageChops.multiply(ch, g.split()[3]) for ch in g.split()[:3]])
        big = Image.merge("RGBA", (*ImageChops.add(big.convert("RGB"), add).split(), Image.new("L", big.size, 255)))
    big.alpha_composite(rt.resize((1920, 1080), Image.NEAREST))
    d = ImageDraw.Draw(big)
    sa = meta["strokeArea"]
    d.rectangle([sa["x"], sa["y"], sa["x"] + sa["w"], sa["y"] + sa["h"]], outline=(120, 200, 255, 255), width=2)
    d.line([tuple(p) for p in meta["strokeClip"]] + [tuple(meta["strokeClip"][0])], fill=(80, 160, 220, 255), width=1)
    f = font(34)
    d.text((960, 48), "가장 강한 것을 떠올려라. 손이 먼저 기억한다.", font=f, fill=(216, 217, 219, 255), anchor="mm",
           stroke_width=2, stroke_fill=(0, 0, 0, 255))
    d.text((960, 1036), "끌어서 한 획  ·  2 / 3", font=font(26), fill=(178, 180, 184, 255), anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0, 255))
    big.convert("RGB").save(os.path.join(HERE, "preview_ritual.png"), optimize=True)


def nine(img, w, h, s):
    W_ = img.width
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cols = [(0, s, 0, s), (s, W_ - s, s, w - s), (W_ - s, W_, w - s, w)]
    rows = [(0, s, 0, s), (s, W_ - s, s, h - s), (W_ - s, W_, h - s, h)]
    for a in cols:
        for b in rows:
            out.alpha_composite(img.crop((a[0], b[0], a[1], b[1])).resize((a[3] - a[2], b[3] - b[2]), Image.NEAREST), (a[2], b[2]))
    return out


def glow_text(d, xy, text, f, body, halo, shade):
    x, y = xy
    for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2), (1, 1), (-1, 1), (1, -1), (-1, -1)):
        d.text((x + dx, y + dy), text, font=f, fill=shade)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        d.text((x + dx, y + dy), text, font=f, fill=halo)
    d.text((x, y), text, font=f, fill=body)


def preview_ritual_ui():
    W, H = 960, 540
    out = Image.new("RGBA", (W * 2, H), (14, 14, 16, 255))
    # 왼쪽 화면: 일기장 첫 장
    page = Image.open(os.path.join(RIT, "diary_first_page.png")).convert("RGBA")
    pm = json.load(open(os.path.join(RIT, "diary_first_page.json"), encoding="utf-8"))
    px0, py0 = pm["placement"]["x"], pm["placement"]["y"]
    scr = Image.new("RGBA", (W, H), (14, 14, 16, 255))
    scr.alpha_composite(page, (px0, py0))
    d = ImageDraw.Draw(scr)
    S5, S4, S2 = (198, 165, 139, 255), (106, 86, 69, 255), (64, 50, 39, 255)
    ta = pm["titleArea"]
    glow_text(d, (px0 + ta["x"] + 70, py0 + ta["y"] + 4), "이 일기의 주인", font(16), (255, 255, 255, 255), S4, S2)
    la = pm["nameLabel"]
    glow_text(d, (px0 + la["x"], py0 + la["y"] + 6), "이름", font(14), S5, S4, S2)
    nf = pm["nameField"]
    glow_text(d, (px0 + nf["x"] + 50, py0 + nf["y"] + 12), "도 영", font(26), (255, 255, 255, 255), (176, 97, 26, 128), S2)
    for i, line in enumerate(("벽 밖에서 눈을 떴다.", "가진 것은 이름 하나.")):
        glow_text(d, (px0 + 44, py0 + pm["bodyLines"][i] - 14), line, font(13), S5, S4, S2)
    d.text((W // 2, 506), "Enter · 클릭  이름을 새긴다", font=font(13), fill=(178, 180, 184, 255), anchor="mm")
    out.alpha_composite(scr, (0, 0))
    # 오른쪽 화면: 운명 액자 + 붓 시트 + 팻말
    scr = Image.new("RGBA", (W, H), (14, 14, 16, 255))
    fr = Image.open(os.path.join(RIT, "fate_frame.png")).convert("RGBA")
    fm = json.load(open(os.path.join(RIT, "fate_frame.json"), encoding="utf-8"))
    sz = fm["suggestedSize"]
    fx, fy = 348, 60
    back = Image.new("RGBA", (sz["w"] - 72, sz["h"] - 72), (20, 21, 22, 255))
    scr.alpha_composite(back, (fx + 36, fy + 36))
    look = os.path.join(SPR, "looks", "katana_base.png")
    if os.path.exists(look):
        scr.alpha_composite(Image.open(look).convert("RGBA"), (fx + 36, fy + 36))
    scr.alpha_composite(nine(fr, sz["w"], sz["h"], 40), (fx, fy))
    d = ImageDraw.Draw(scr)
    d.text((480, 346), "칼 — 은선", font=font(18), fill=(250, 238, 192, 255), anchor="mm", stroke_width=1, stroke_fill=(0, 0, 0, 255))
    d.text((480, 372), "망설임 없이 곧게 그었다.", font=font(13), fill=(178, 180, 184, 255), anchor="mm")
    sheet = Image.open(os.path.join(RIT, "ink_brush.png")).convert("RGBA")
    sb = Image.new("RGBA", sheet.size, (90, 92, 96, 255))
    sb.alpha_composite(sheet)
    scr.alpha_composite(sb.resize((sheet.width * 2 // 2, sheet.height)), (20, 380))
    pl = Image.open(os.path.join(SPR, "ui", "plank_label.png")).convert("RGBA")
    pk = nine(pl, 120, 24, 14) if False else None
    w = 120
    plank = Image.new("RGBA", (w, 24), (0, 0, 0, 0))
    plank.alpha_composite(pl.crop((0, 0, 14, 24)), (0, 0))
    plank.alpha_composite(pl.crop((14, 0, 34, 24)).resize((w - 28, 24), Image.NEAREST), (14, 0))
    plank.alpha_composite(pl.crop((34, 0, 48, 24)), (w - 14, 0))
    scr.alpha_composite(plank, (760, 420))
    d.text((820, 434), "사수 허수아비", font=font(11), fill=(235, 236, 237, 255), anchor="mm", stroke_width=1, stroke_fill=(0, 0, 0, 255))
    out.alpha_composite(scr, (W, 0))
    out = out.resize((out.width * 2 // 2 * 1, out.height), Image.NEAREST)
    out.resize((out.width, out.height)).convert("RGB").save(os.path.join(HERE, "preview_ritual_ui.png"), optimize=True)
    Image.open(os.path.join(HERE, "preview_ritual_ui.png")).resize((W * 4, H * 2), Image.NEAREST).save(os.path.join(HERE, "preview_ritual_ui_x2.png"), optimize=True)


def tileset(name):
    im = Image.open(os.path.join(TILES, "v2", f"{name}.png")).convert("RGBA")
    meta = json.load(open(os.path.join(TILES, "v2", f"{name}.json"), encoding="utf-8"))
    return im, meta


def cell(im, i):
    return im.crop(((i % 8) * T, (i // 8) * T, (i % 8) * T + T, (i // 8) * T + T))


def floor_mock(im, meta, w, h, seed, start_mix=0.0):
    r = random.Random(seed)
    out = Image.new("RGBA", (w * T, h * T))
    lst = meta["tiles"]["1"]
    rs = meta["roomFloors"]["start"]
    for y in range(h):
        for x in range(w):
            i = r.choice(rs) if r.random() < start_mix else r.choice(lst)
            out.paste(cell(im, i), (x * T, y * T))
    return out


def sheet_frame(name, k=0):
    p = os.path.join(SPR, "structures", "v3", name)
    m = gridsheet.load_meta(p + ".json")
    g = gridsheet.open_grid(p + ".png")
    fw, fh = m["frameWidth"], m["frameHeight"]
    return g.crop((k * fw, 0, k * fw + fw, fh)), (m["pivot"]["x"], m["pivot"]["y"])


def darken(im, lights, amb=0.32):
    """간이 조명: 주변광 amb + 광원(호박) — 미리보기 전용."""
    W_, H_ = im.size
    lm = Image.new("RGB", (W_, H_), tuple(int(255 * amb * c) for c in (0.85, 0.88, 1.0)))
    d = ImageDraw.Draw(lm)
    for (x, y, rad, col) in lights:
        for k in range(12, 0, -1):
            rr = rad * k / 12
            f = (1 - k / 12) ** 1.4
            c = tuple(min(255, int(255 * amb + f * cc)) for cc in col)
            d.ellipse([x - rr, y - rr * 0.8, x + rr, y + rr * 0.8], fill=c)
    lm = lm.filter(ImageFilter.GaussianBlur(10))
    return Image.merge("RGBA", (*ImageChops.multiply(im.convert("RGB"), lm).split(), Image.new("L", im.size, 255)))


def preview_birth():
    im, meta = tileset("stage1_waste")
    W_, H_ = 15, 9
    base = floor_mock(im, meta, W_, H_, 9, start_mix=0.10)
    dec = {d_["name"]: d_["rect"] for d_ in meta["decals"]}

    def put_dec(n, x, y):
        rc = dec[n]
        base.alpha_composite(im.crop((rc["x"], rc["y"], rc["x"] + rc["w"], rc["y"] + rc["h"])), (x, y))
    put_dec("scorch", 120, 300)
    put_dec("blood_pool", 520, 470)
    put_dec("bone_scatter", 760, 140)
    put_dec("trampled_mud", 300, 120)
    put_dec("ash_ring", 840, 420)
    # 모래주머니 담 (lower+top 1칸 높이, 3칸 폭)
    for x in range(3):
        base.alpha_composite(cell(im, 45), ((10 + x) * T, 5 * T))
        base.alpha_composite(cell(im, 43 if x != 1 else 46), ((10 + x) * T, 6 * T))
    items = [("birth_broken_spears", 0, 240, 520), ("birth_fallen_soldier", 0, 360, 600), ("birth_corpse_pile", 1, 300, 330),
             ("birth_corpse_mound", 2, 640, 300), ("birth_spear_thicket", 3, 520, 220), ("birth_banner_bloody", 2, 160, 230),
             ("birth_corpse_mound", 0, 820, 560), ("birth_spear_thicket", 0, 120, 520)]
    items.sort(key=lambda t: t[3])
    hero = None
    hp = os.path.join(SPR, "player", "v3", "player_idle")
    if os.path.exists(hp + ".json"):
        hm = gridsheet.load_meta(hp + ".json")
        hg = gridsheet.open_grid(hp + ".png")
        hero = (hg.crop((0, 0, hm["frameWidth"], hm["frameHeight"])), (hm["pivot"]["x"], hm["pivot"]["y"]))
    for name, k, x, y in items:
        fr, (pvx, pvy) = sheet_frame(name, k)
        base.alpha_composite(fr, (x - pvx, y - pvy))
        if hero and name == "birth_corpse_mound" and x == 640:
            h, (hx, hy) = hero
            base.alpha_composite(h, (x + 120 - hx, y + 80 - hy))
    lit = darken(base, [(300, 300, 160, (214, 122, 17)), (770, 380, 260, (200, 150, 90)), (160, 120, 120, (214, 122, 17))])
    out = Image.new("RGBA", (base.width, base.height * 2 + 8), (0, 0, 0, 255))
    out.alpha_composite(base, (0, 0))
    out.alpha_composite(lit, (0, base.height + 8))
    out.convert("RGB").save(os.path.join(HERE, "preview_birth.png"), optimize=True)


def preview_tiles():
    rows = []
    for name, sm in (("stage1_waste", 0.10), ("stage1_training", 0.0)):
        bim = Image.open(os.path.join(HERE, "before", f"{name}.png")).convert("RGBA")
        bmeta = json.load(open(os.path.join(HERE, "before", f"{name}.json"), encoding="utf-8"))
        aim, ameta = tileset(name)
        pair = []
        for im, meta in ((bim, bmeta), (aim, ameta)):
            m = floor_mock(im, meta, 8, 5, 4, start_mix=sm)
            ws = meta["walls"]["stoneSet"]
            for x in range(2):
                m.alpha_composite(cell(im, ws["top"]), ((5 + x) * T, 1 * T))
                m.alpha_composite(cell(im, ws["lower"][x % len(ws["lower"])]), ((5 + x) * T, 2 * T))
            if name == "stage1_training":
                for x in range(8):
                    m.paste(cell(im, meta["walls"]["front"]["upper"][x % 4]), (x * T, 0))
            pair.append(m)
        rows.append(pair)
    W_ = rows[0][0].width
    out = Image.new("RGB", (W_ * 2 + 16, sum(p[0].height for p in rows) + 16 * len(rows)), (0, 0, 0))
    y = 0
    for pair in rows:
        out.paste(pair[0].convert("RGB"), (0, y))
        out.paste(pair[1].convert("RGB"), (W_ + 16, y))
        y += pair[0].height + 16
    out.save(os.path.join(HERE, "preview_tiles.png"), optimize=True)


def main():
    preview_ritual()
    preview_ritual_ui()
    preview_birth()
    preview_tiles()


if __name__ == "__main__":
    main()
