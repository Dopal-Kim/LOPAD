"""단계 비교 미리보기 (55라운드 Q9) — 무기별 '기본 → 1단 갈래 A → A 의 2단 2종 → 1단 갈래 B → B 의 2단 2종'.

preview_tiers_<무기>.png              1배 조명 합성, 행 = 1·2·3타(판정 프레임), 열 = 7단계, 주인공 v3 몸 + 무기 v3 + 이펙트
preview_tiers_<무기>_after.png        같은 배치, 판정 다음 프레임(잔광·입자가 쌓이는 모습)
gif/tiers_<무기>_combo<n>_right.gif   7칸 나란히 실제 ms(몸 판정 프레임 시작 = 이펙트 impactFrame 시작)
preview_tiers_bow.png · gif/tiers_bow.gif  활: 기본 / 속사 / 연궁 / 무한통 / 저격(lv3) / 관통 / 필중 — 1배 조명 + ×4 확대
사용: python3 preview_tiers.py [katana greatsword dagger bow]
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import preview as PV                                  # noqa: E402

TIERS = {"katana": ("iai", ("wide", "zangetsu"), "batto", ("longinvuln", "dashcrit")),
         "greatsword": ("crush", ("quake", "pulverize"), "weight", ("ironwall", "giant")),
         "dagger": ("twin", ("dance", "bleed"), "gale", ("afterimage", "assassin"))}
LABEL = {"iai": "거합", "wide": "만월", "zangetsu": "잔월", "batto": "발도", "longinvuln": "허보", "dashcrit": "급소",
         "crush": "파쇄", "quake": "지진", "pulverize": "분쇄", "weight": "중압", "ironwall": "철벽", "giant": "거인",
         "twin": "쌍격", "dance": "난무", "bleed": "출혈", "gale": "질풍", "afterimage": "잔상", "assassin": "암살"}


def columns(weapon):
    a, (a1, a2), b, (b1, b2) = TIERS[weapon]
    return [("", "기본"), ("_" + a, "1단 " + LABEL[a]), ("_%s_%s" % (a, a1), "2단 " + LABEL[a1]), ("_%s_%s" % (a, a2), "2단 " + LABEL[a2]),
            ("_" + b, "1단 " + LABEL[b]), ("_%s_%s" % (b, b1), "2단 " + LABEL[b1]), ("_%s_%s" % (b, b2), "2단 " + LABEL[b2])]


def mock(spots, path, step, h, gy):
    """PV.mock 과 같은 조명 합성, 발 높이 gy 지정(대검 호가 아래로 잘리지 않게)."""
    w = step * len(spots) + 40
    base = PV.floor(w, h)
    lights = []
    for k, (lab, im, piv) in enumerate(spots):
        cx = 40 + step * k + step // 2 - 20
        base.alpha_composite(im, (cx - piv[0], gy - piv[1]))
        lights.append(dict(x=cx, y=gy - 80, color="#b0611a", radius=150, intensity=0.75))
    lit = PV.light_scene(base, lights)
    out = Image.new("RGB", (w, h + 40), (18, 19, 22))
    out.paste(lit, (0, 40))
    d = ImageDraw.Draw(out)
    PV.label(d, 6, 4, "1배 조명 합성 · 몸 + 무기 v3 + 이펙트 v3 · 외곽 거리 바닥 · 주변광 0.425/0.425/0.475 · 주인공 빛 r150·0.75(목업 임시)")
    for k, (lab, im, piv) in enumerate(spots):
        PV.label(d, 40 + step * k + step // 2 - 60, 22, lab)
    out.save(path)


def grid(weapon, after=False):
    big = weapon == "greatsword"
    step = 520 if big else 340
    h = 660 if big else 470
    gy = 380 if big else 290
    rows = []
    for n in (1, 2, 3):
        bj, _ = PV.load(os.path.join(PV.P3, "player_%s_combo%d" % (weapon, n)))
        bi = PV.glow_body_frame(bj)
        spots = []
        for tag, lab in columns(weapon):
            name = "%s_combo%d%s" % (weapon, n, tag)
            fj, _ = PV.load(os.path.join(PV.FX3, name))
            fi = min(fj["impactFrame"] + (1 if after else 0), fj["frames"] - 1)
            im, piv = PV.comp_body(weapon, n, "right", bi if not after else min(bi + 1, len(bj["frameDurationsMs"]) - 1), name, fi)
            spots.append(("%d타 %s" % (n, lab), im, piv))
        mock(spots, os.path.join(HERE, "_tmp_tiers.png"), step, h, gy)
        rows.append(Image.open(os.path.join(HERE, "_tmp_tiers.png")).convert("RGB"))
    os.remove(os.path.join(HERE, "_tmp_tiers.png"))
    out = Image.new("RGB", (max(r.width for r in rows), sum(r.height for r in rows)))
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    out.save(os.path.join(HERE, "preview_tiers_%s%s.png" % (weapon, "_after" if after else "")))


def gif(weapon, n):
    cols = columns(weapon)
    crop = {"greatsword": 600, "katana": 440, "dagger": 330}[weapon]
    ims = []
    for tag, lab in cols:
        PV.combo_gif(weapon, n, "right", fx_name="%s_combo%d%s" % (weapon, n, tag), tag="_tier%s" % tag)
        ims.append((Image.open(os.path.join(PV.GIF, "_tier%s_right.gif" % tag)), lab))
    frames, durs = [], []
    k = 0
    while True:
        alive = False
        S = ims[0][0].width
        row = Image.new("RGB", (crop * len(ims), crop))
        dur = 40
        for j, (im, lab) in enumerate(ims):
            fi = min(k, im.n_frames - 1)
            alive |= k < im.n_frames
            im.seek(fi)
            if k < im.n_frames:
                dur = im.info.get("duration", 40)
            c = im.convert("RGB")
            x0 = (S - crop) // 2 + crop // 8
            y0 = (S - crop) // 2 + 30
            row.paste(c.crop((x0, y0, x0 + crop, y0 + crop)), (j * crop, 0))
        if not alive:
            break
        d = ImageDraw.Draw(row)
        for j, (im, lab) in enumerate(ims):
            PV.label(d, j * crop + 8, 6, "%d타 %s" % (n, lab))
        frames.append(row.quantize(colors=160, dither=Image.Dither.NONE))
        durs.append(dur)
        k += 1
    frames[0].save(os.path.join(PV.GIF, "tiers_%s_combo%d_right.gif" % (weapon, n)), save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, disposal=2)
    for tag, _ in cols:
        os.remove(os.path.join(PV.GIF, "_tier%s_right.gif" % tag))


# ------------------------------------------------------------------ 활
BOW_ROWS = [("기본", "bow_arrow_aimed", None), ("1단 속사", "bow_arrow_aimed_rapid", None),
            ("2단 연궁", "bow_arrow_aimed_rapid_volley", None), ("2단 무한통", "bow_arrow_aimed_rapid_quiver", None),
            ("1단 저격 lv1·lv2·lv3", "bow_arrow_aimed_snipe", "bow_arrow_snipe_lv%d"),
            ("2단 관통 lv1·lv2·lv3", "bow_arrow_aimed_snipe_pierce", "bow_arrow_snipe_lv%d_pierce"),
            ("2단 필중 lv1·lv2·lv3", "bow_arrow_aimed_snipe_deadeye", "bow_arrow_snipe_lv%d_deadeye")]


def _arrow_strip(i, rowh=44, w=1500, zoom=1):
    """한 줄: 화살(+꼬리 lv1·2·3)을 1배로 배치. i = 루프 프레임."""
    out = Image.new("RGBA", (w, rowh * len(BOW_ROWS)))
    for r, (lab, arrow, tail) in enumerate(BOW_ROWS):
        y = r * rowh + rowh // 2
        aj, aim = PV.load(os.path.join(PV.FX3, arrow))
        xs = (420, 900, 1380) if tail else (420,)
        for k, x in enumerate(xs):
            if tail:
                tj, tim = PV.load(os.path.join(PV.FX3, tail % (k + 1)))
                out.alpha_composite(PV.cell(tj, tim, "any", i % tj["frames"]), (x - tj["pivot"]["x"], y - tj["pivot"]["y"]))
            out.alpha_composite(PV.cell(aj, aim, "any", i % aj["frames"]), (x - aj["pivot"]["x"], y - aj["pivot"]["y"]))
    return out


def bow():
    w, rowh = 1500, 44
    base = PV.floor(w, rowh * len(BOW_ROWS) + 20)
    base.alpha_composite(_arrow_strip(0, rowh, w), (0, 10))
    lit = PV.light_scene(base, [dict(x=x, y=160, color="#b0611a", radius=200, intensity=0.5) for x in (420, 900, 1380)])
    out = Image.new("RGB", (w + 150, lit.height + 30), (18, 19, 22))
    out.paste(lit, (150, 30))
    d = ImageDraw.Draw(out)
    PV.label(d, 6, 6, "1배 조명 합성 · 활 갈래 단계 (조준 화살 기준, 저격 꼬리는 왼쪽부터 lv1·lv2·lv3)")
    for r, (lab, _, _) in enumerate(BOW_ROWS):
        PV.label(d, 6, 30 + 10 + r * rowh + rowh // 2 - 6, lab)
    # ×4 확대(lv3 / 속사 화살)
    zrows = []
    for lab, arrow, tail in BOW_ROWS:
        aj, aim = PV.load(os.path.join(PV.FX3, arrow))
        c = Image.new("RGBA", (360, 44), PV.BG)
        if tail:
            tj, tim = PV.load(os.path.join(PV.FX3, tail % 3))
            tc = PV.cell(tj, tim, "any", 0)
            c.alpha_composite(tc, (300 - tj["pivot"]["x"], 22 - tj["pivot"]["y"]))
        c.alpha_composite(PV.cell(aj, aim, "any", 0), (300 - aj["pivot"]["x"], 22 - aj["pivot"]["y"]))
        c = c.crop((150, 0, 360, 44)).resize((840, 176), Image.NEAREST)
        zrows.append((lab, c))
    zw = 840 + 150
    z = Image.new("RGB", (zw, len(zrows) * 182 + 24), (18, 19, 22))
    dz = ImageDraw.Draw(z)
    PV.label(dz, 6, 4, "×4 확대 (저격 계열은 lv3 꼬리 겹침)")
    for k, (lab, c) in enumerate(zrows):
        z.paste(c.convert("RGB"), (150, 24 + k * 182))
        PV.label(dz, 6, 24 + k * 182 + 80, lab)
    full = Image.new("RGB", (max(out.width, z.width), out.height + z.height), (18, 19, 22))
    full.paste(out, (0, 0))
    full.paste(z, (0, out.height))
    full.save(os.path.join(HERE, "preview_tiers_bow.png"))
    # GIF: 화살이 날아가며 루프(6프레임 = 50ms 단위)
    frames = []
    for i in range(12):
        b = PV.floor(w, rowh * len(BOW_ROWS) + 20)
        strip = _arrow_strip(i, rowh, w)
        b.alpha_composite(strip, (-60 + 10 * i, 10))
        fr = Image.new("RGB", (w + 150, b.height), (18, 19, 22))
        fr.paste(b.convert("RGB"), (150, 0))
        dd = ImageDraw.Draw(fr)
        for r, (lab, _, _) in enumerate(BOW_ROWS):
            PV.label(dd, 6, 10 + r * rowh + rowh // 2 - 6, lab)
        frames.append(fr.quantize(colors=128, dither=Image.Dither.NONE))
    os.makedirs(PV.GIF, exist_ok=True)
    frames[0].save(os.path.join(PV.GIF, "tiers_bow.gif"), save_all=True, append_images=frames[1:], duration=50, loop=0, disposal=2)


def main(args):
    for w in (args or ["katana", "greatsword", "dagger", "bow"]):
        if w == "bow":
            bow()
        else:
            grid(w)
            grid(w, after=True)
            for n in (1, 2, 3):
                gif(w, n)
        print("preview tiers", w, "ok")


if __name__ == "__main__":
    main(sys.argv[1:])
