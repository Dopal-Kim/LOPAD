#!/usr/bin/env python3
"""61라운드 아트 2 미리보기(assets 를 읽기만) — 긴 변 8000 이하.

  boss61/preview_readability.png  파훼 표시 모음(1배 어두운 연회장 바닥 위 + 2배 확대)
  boss61/preview_finale.png       결정타 일섬·터짐 + 쓰러짐 파편 + 불꽃 꺼짐(보스 death 위)
  weapons61/preview_weapons.png   단검 가속 1~3 · hit_dagger 전/후 · 대검 궤적 전/후 · 화살 전/후 · 발도 검기 0~3 · 허수아비 · 서서 시작 화살비
사용: python3 parts/art/work/boss61/preview61.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import k61  # noqa: E402
from k61 import ROOT  # noqa: E402
import gridsheet  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SPR = os.path.join(ROOT, "assets", "sprites")
W61 = os.path.join(HERE, "..", "weapons61")
BG = (22, 20, 26, 255)


def sheet(cat, name, prev=False):
    if prev:
        p = os.path.join(W61, "prev", cat, "v3", name + ".json")
        return gridsheet.load_meta(p), gridsheet.open_grid(p)
    jp = os.path.join(SPR, cat, "v3", name + ".json")
    return gridsheet.load_meta(jp), gridsheet.open_grid(jp)


def frame(cat, name, i, row=0, prev=False):
    m, g = sheet(cat, name, prev)
    fw, fh = m["frameWidth"], m["frameHeight"]
    return g.crop((i * fw, row * fh, (i + 1) * fw, (row + 1) * fh)), (m["pivot"]["x"], m["pivot"]["y"])


def floor(w, h):
    """연회장 비슷한 어두운 돌 바닥(미리보기용)."""
    im = Image.new("RGBA", (w, h), BG)
    d = ImageDraw.Draw(im)
    for y in range(0, h, 32):
        for x in range(0, w, 64):
            o = 32 if (y // 32) % 2 else 0
            d.rectangle([x + o, y, x + o + 62, y + 30], fill=(34, 32, 38, 255))
    return im


def place(dst, im, piv, at):
    dst.alpha_composite(im, (int(at[0] - piv[0]), int(at[1] - piv[1])))


def label(dst, text, xy):
    ImageDraw.Draw(dst).text(xy, text, fill=(220, 210, 190, 255))


def readability():
    W, H = 1900, 600
    im = floor(W, H)
    # 1 보스 들이켜기 + 잔 반짝임
    m, g = sheet("bosses", "stage1_drink")
    for k, fi in enumerate((4, 6)):
        f, bp = frame("bosses", "stage1_drink", fi)
        at = (150 + k * 260, 380)
        place(im, f, bp, at)
        ca = m["cupAnchors"]["down"][fi]
        gl, gp = frame("fx", "boss1_cup_glint", 2 + k * 3, 0)
        place(im, gl, gp, (at[0] - bp[0] + ca["x"] + ca["w"] / 2, at[1] - bp[1] + ca["y"] + ca["h"] / 2))
    label(im, "cup_glint (drink 4 / 6)", (40, 320))
    # 2 기둥 균열 0~3
    for k, fi in enumerate((0, 5, 10, 15)):
        f, p = frame("structures", "boss1_pillar", fi)
        place(im, f, p, (500 + k * 150, 500))
    label(im, "pillar idle / crack1 / crack2 / crack3", (430, 510))
    # 3 술통: 보통 / 되칠 수 있음 테 / 되친 술통
    b, bp = frame("structures", "boss1_rolling_barrel", 2, 3)
    rim, _ = frame("structures", "boss1_rolling_barrel_rim", 2, 3)
    rt, _ = frame("structures", "boss1_rolling_barrel_returned", 2, 3)
    place(im, b, bp, (1150, 200)); place(im, b, bp, (1320, 200)); place(im, rim, bp, (1320, 200)); place(im, rt, bp, (1490, 200))
    label(im, "barrel / rim(returnable) / returned", (1090, 215))
    # 4 촛대: 꺼져 누움 + 반짝임 / 다시 켜짐
    c6, cp = frame("structures", "boss1_candelabra", 6)
    cg, _ = frame("fx", "boss1_candle_glint", 2)
    c9, _ = frame("structures", "boss1_candelabra", 9)
    place(im, c6, cp, (1100, 470)); place(im, cg, cp, (1100, 470)); place(im, c9, cp, (1400, 470))
    label(im, "candelabra fallen + glint / relit(fixed)", (1100, 500))
    # 5 무너진 동안 표시
    m2, g2 = sheet("bosses", "stage1_drink_break")
    fi = 7
    f, bp = frame("bosses", "stage1_drink_break", fi)
    place(im, f, bp, (1760, 420))
    dz, dp = frame("fx", "boss1_break_daze", 3)
    ht = gridsheet.load_meta(os.path.join(SPR, "fx", "v3", "boss1_break_daze.json"))["headTopAnchors"]["drink_break"]["down"][fi]
    place(im, dz, dp, (1760 - bp[0] + ht[0], 420 - bp[1] + ht[1]))
    label(im, "break_daze", (1740, 320))
    out = Image.new("RGBA", (W, H * 2), BG)
    out.alpha_composite(im, (0, 0))
    z = k61.scale(im.crop((0, 0, W // 2, H)), 2)
    out.alpha_composite(z, (0, H))
    p = os.path.join(HERE, "preview_readability.png")
    out.convert("RGB").save(p)
    return p


def finale():
    W, H = 1920, 1080
    out = Image.new("RGBA", (W, H), BG)
    top = floor(W, 540)
    # 결정타: 보스 drink_break(무너짐) 위 일섬 + 터짐 (1 · 2 프레임)
    m, g = sheet("bosses", "stage1_drink_break")
    for k, (si, bi) in enumerate(((1, 0), (3, 2))):
        at = (480 + k * 960, 330)
        f, bp = frame("bosses", "stage1_drink_break", 7)
        place(top, f, bp, (at[0], at[1] + 60))
        s, sp = frame("fx", "boss1_finisher_slash", si)
        s = s.rotate(-12, resample=Image.NEAREST, expand=False)
        place(top, s, sp, (at[0], at[1] - 100))
        b, bpv = frame("fx", "boss1_finisher_burst", bi)
        place(top, b, bpv, (at[0], at[1] - 100))
    label(top, "finisher slash+burst f1 / f3 (1x)", (20, 20))
    out.alpha_composite(top, (0, 0))
    bot = floor(W, 540)
    bot = floor(W, 540)
    md, gd = sheet("bosses", "stage1_death")
    for k, (di, fi) in enumerate(((1, 2), (4, 5), (8, 8), (13, 11))):
        at = (240 + k * 480, 500)
        f0, bp = frame("bosses", "stage1_death", di)
        place(bot, f0, bp, at)
        f, p = frame("fx", "boss1_defeat_shatter", fi)
        place(bot, f, p, at)
    for k in range(8):
        f, p = frame("fx", "boss1_flame_snuff", k)
        place(bot, f, p, (1500 + k * 50, 120))
    label(bot, "defeat_shatter over death (1x) · flame_snuff 0~7", (20, 20))
    out.alpha_composite(bot, (0, 540))
    p = os.path.join(HERE, "preview_finale.png")
    out.convert("RGB").save(p)
    return p


def weapons():
    rows = []
    # 단검 가속 1~3 (right 행, 판정 프레임 1·2) + 옛 그림
    r = Image.new("RGBA", (1900, 260), BG)
    old, op = frame("fx", "dagger_combo1", 1, 3, prev=True)
    place(r, old, op, (120, 200))
    for k, nm in enumerate(("dagger_combo1", "dagger_combo1_accel2", "dagger_combo1_accel3")):
        for q, fi in enumerate((1, 2)):
            f, p = frame("fx", nm, fi, 3)
            place(r, f, p, (420 + k * 500 + q * 230, 200))
    label(r, "dagger combo1: old | accel1 f1 f2 | accel2 | accel3", (10, 10))
    rows.append(r)
    r = Image.new("RGBA", (1900, 200), BG)
    for k, (nm, pv) in enumerate((("hit_dagger", True), ("hit_dagger", False), ("hit_dagger_heavy", True), ("hit_dagger_heavy", False))):
        for fi in range(4):
            f, p = frame("fx", nm, fi, 0, prev=pv)
            place(r, k61.scale(f, 2), (p[0] * 2, p[1] * 2), (40 + k * 470 + fi * 110, 110))
    label(r, "hit_dagger old | new | heavy old | new (2x)", (10, 10))
    rows.append(r)
    r = Image.new("RGBA", (1900, 480), BG)
    for k, pv in enumerate((True, False)):
        for q, fi in enumerate((1, 2, 3)):
            f, p = frame("fx", "greatsword_sweep_cw", fi, 3, prev=pv)
            place(r, f, p, (230 + k * 950 + q * 300, 340))
    label(r, "greatsword_sweep_cw old | new (right, f1~3)", (10, 10))
    rows.append(r)
    r = Image.new("RGBA", (1900, 140), (16, 14, 18, 255))
    f, p = frame("fx", "bow_arrow", 0, 0, prev=True)
    place(r, k61.scale(f, 3), (p[0] * 3, p[1] * 3), (200, 70))
    for fi in range(4):
        f, p = frame("fx", "bow_arrow", fi)
        place(r, k61.scale(f, 3), (p[0] * 3, p[1] * 3), (700 + fi * 300, 70))
    label(r, "bow_arrow old | new f0~3 (3x)", (10, 10))
    rows.append(r)
    r = Image.new("RGBA", (1900, 420), BG)
    for k, nm in enumerate(("katana_iai", "katana_iai_ki1", "katana_iai_ki2", "katana_iai_ki3")):
        f, p = frame("fx", nm, 2, 3)
        place(r, f, p, (240 + k * 460, 330))
    label(r, "katana_iai ki0 | ki1 | ki2 | ki3 (right f2)", (10, 10))
    rows.append(r)
    r = Image.new("RGBA", (1900, 240), (44, 40, 36, 255))
    md = gridsheet.load_meta(os.path.join(SPR, "structures", "v3", "tutorial_dummy.json"))
    sel = [0, md["states"]["hit"][0], md["states"]["hit"][1], md["states"]["hit"][2], md["states"]["hit_heavy"][1]] + md["states"]["broken"][2:]
    for k, fi in enumerate(sel):
        f, p = frame("structures", "tutorial_dummy", fi)
        place(r, f, p, (110 + k * 230, 220))
    label(r, "tutorial_dummy idle | hit 0~2 | hit_heavy 1 | broken", (10, 10))
    rows.append(r)
    r = Image.new("RGBA", (1900, 220), BG)
    mb, gb = sheet("player", "player_bow_arrow_rain_stand")
    mw, gw = sheet("weapons", "bow_arrow_rain_stand")
    for k, fi in enumerate(range(0, 14, 2)):
        for q, row in enumerate((3, 0)):
            x = 60 + k * 260 + q * 120
            place(r, gb.crop((fi * 96, row * 144, (fi + 1) * 96, (row + 1) * 144)), (48, 138), (x, 200))
            place(r, gw.crop((fi * 192, row * 192, (fi + 1) * 192, (row + 1) * 192)), (96, 186), (x, 200))
    label(r, "bow_arrow_rain_stand f0,2,4..12 (right/down)", (10, 10))
    rows.append(r)
    Ht = sum(x.height for x in rows)
    out = Image.new("RGBA", (1900, Ht), BG)
    y = 0
    for x in rows:
        out.alpha_composite(x, (0, y))
        y += x.height
    p = os.path.normpath(os.path.join(W61, "preview_weapons.png"))
    out.convert("RGB").save(p)
    return p


if __name__ == "__main__":
    for fn in (readability, finale, weapons):
        p = fn()
        print(p, Image.open(p).size)
