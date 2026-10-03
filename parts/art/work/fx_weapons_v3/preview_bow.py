"""활 미리보기 — 1배 조명 합성(가득 당김 + 조준선·차지 / 날아가는 화살·꼬리 / 적중) + 화살 4배 확대 띠."""
import os

from PIL import Image, ImageDraw

import preview as PV
import wkit as W

HERE = PV.HERE


def tile_line(j, im, i, length):
    fw, fh = j["frameWidth"], j["frameHeight"]
    c = PV.cell(j, im, "any", i)
    out = Image.new("RGBA", (length, fh))
    for x in range(0, length, fw):
        out.alpha_composite(c, (x, 0))
    return out


def scene(spots_y=330):
    w, h = 1500, 440
    base = PV.floor(w, h)
    lights = []
    gy = spots_y
    # 1) 가득 당김(오른쪽) + 조준 차지 + 조준선(기본 / 저격)
    for k, (line, cx, snipe) in enumerate((("aim_line", 160, False), ("aim_line_snipe", 760, True))):
        bj, bim = PV.load(os.path.join(PV.P3, "player_bow_aim"))
        wj, wim = PV.load(os.path.join(PV.WP3, "bow_aim"))
        fi = len(bj["frameDurationsMs"]) - 2
        lj, lim = PV.load(os.path.join(PV.FX3, line))
        ln = tile_line(lj, lim, lj["frames"] - 1, 300)
        base.alpha_composite(ln, (cx + 30, gy - 72 - lj["pivot"]["y"]))
        base.alpha_composite(PV.cell(bj, bim, "right", fi), (cx - bj["pivot"]["x"], gy - bj["pivot"]["y"]))
        base.alpha_composite(PV.cell(wj, wim, "right", fi), (cx - wj["pivot"]["x"], gy - wj["pivot"]["y"]))
        cj, cim = PV.load(os.path.join(PV.FX3, "aim_charge"))
        base.alpha_composite(PV.cell(cj, cim, "any", 5 if k else 3), (cx - cj["pivot"]["x"], gy - cj["pivot"]["y"] - 10))
        # 날아가는 화살 + 꼬리
        if snipe:
            tj, tim = PV.load(os.path.join(PV.FX3, "bow_arrow_snipe_lv3"))
            aj, aim = PV.load(os.path.join(PV.FX3, "bow_arrow_aimed_snipe"))
        else:
            tj, tim = PV.load(os.path.join(PV.FX3, "pierce"))
            aj, aim = PV.load(os.path.join(PV.FX3, "bow_arrow_aimed"))
        ax, ay = cx + 380, gy - 72
        base.alpha_composite(PV.cell(tj, tim, "any", 0), (ax - tj["pivot"]["x"], ay - tj["pivot"]["y"]))
        base.alpha_composite(PV.cell(aj, aim, "any", 0), (ax - aj["pivot"]["x"], ay - aj["pivot"]["y"]))
        lights.append(dict(x=cx, y=gy - 80, color="#b0611a", radius=150, intensity=0.75))
    # 2) 중시 적중
    hj, him = PV.load(os.path.join(PV.FX3, "heavyarrow_hit"))
    base.alpha_composite(PV.cell(hj, him, "any", 1), (1380 - hj["pivot"]["x"], gy - hj["pivot"]["y"]))
    lit = PV.light_scene(base, lights)
    out = Image.new("RGB", (w, h + 30), (18, 19, 22))
    out.paste(lit, (0, 30))
    d = ImageDraw.Draw(out)
    PV.label(d, 6, 6, "1배 조명 합성 · 활: 가득 당김 + 차지 + 조준선(기본 aim_line / 저격 aim_line_snipe 완료) + 화살·꼬리(관통 / 저격 lv3) · 중시 적중 f1")
    out.save(os.path.join(HERE, "preview_mock_bow.png"))


def arrows_zoom():
    names = ["bow_arrow", "bow_arrow_aimed", "heavyarrow", "bow_arrow_rapid", "bow_arrow_aimed_rapid", "bow_arrow_snipe",
             "bow_arrow_aimed_snipe", "bow_arrow_snipe_lv1", "bow_arrow_snipe_lv2", "bow_arrow_snipe_lv3", "flash", "pierce",
             "aim_line", "aim_line_snipe", "bow_muzzle_rapid", "muzzle_flash"]
    k = 4
    rows = []
    for n in names:
        j, im = PV.load(os.path.join(PV.FX3, n))
        oj, oim = PV.load(os.path.join(W.OLD_FX, n))
        F = j["frames"]
        fw, fh = j["frameWidth"], j["frameHeight"]
        r = Image.new("RGBA", (F * (fw * k + 8) + 300, fh * k + 22), PV.BG)
        dr = ImageDraw.Draw(r)
        PV.label(dr, 4, 2, "%s %dx%d (x4)   구 x16 →" % (n, fw, fh))
        for i in range(F):
            r.alpha_composite(PV.cell(j, im, j["directions"][-1], i).resize((fw * k, fh * k), Image.NEAREST), (4 + i * (fw * k + 8), 20))
        o = PV.cell(oj, oim, oj["directions"][-1], 0)
        o = o.resize((o.width * 16, o.height * 16), Image.NEAREST)
        r.alpha_composite(o.crop((0, 0, min(o.width, 290), min(o.height, fh * k))), (F * (fw * k + 8) + 4, 20))
        rows.append(r)
    out = Image.new("RGBA", (max(r.width for r in rows), sum(r.height + 4 for r in rows)), (18, 18, 22, 255))
    y = 0
    for r in rows:
        out.alpha_composite(r, (0, y))
        y += r.height + 4
    out.save(os.path.join(HERE, "preview_bow_x4.png"))


def main():
    scene()
    arrows_zoom()
