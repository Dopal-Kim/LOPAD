#!/usr/bin/env python3
"""무기별 모음 미리보기 preview_<weapon>.png (개성 14 + 그 무기 공명) + 65장 검사.

검사: 128×128 RGBA · 알파 0/255 만 · 틀 가장자리 1도트 비어 있음 · 색 ⊂ 그 무기 허용 카드 팔레트(kit.ALLOW) · 내용 있음.
미리보기 줄: 위 = 2배(카드 바탕 세피아 S1 위), 아래 = 1배 띠(게임 화면 크기 64px 의 내부 렌더 128) — 바탕 S1·S3·G02 세 가지.
"""
import json, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit, cards as C  # noqa
from gkit import hex2rgb  # noqa

OUT = os.path.join(kit.ROOT, "assets/sprites/ui_traits")
SEPIA = kit.PAL["ui"]["ramp"]


def check(cid, weapon):
    p = os.path.join(OUT, cid + ".png")
    im = Image.open(p)
    errs = []
    if im.size != (128, 128):
        errs.append(f"size {im.size}")
    if im.mode != "RGBA":
        im = im.convert("RGBA")
        errs.append("mode")
    allowed = {hex2rgb(kit.NAMED[n]) for n in kit.ALLOW[weapon]}
    cols, n = set(), 0
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a not in (0, 255):
                errs.append("semi-alpha")
                break
            if a:
                n += 1
                cols.add((r, g, b))
                if x in (0, 127) or y in (0, 127):
                    errs.append("edge")
    bad = cols - allowed
    if bad:
        errs.append(f"off-palette {len(bad)}")
    return sorted(set(errs)), len(cols), n


def sheet(weapon):
    ids = [c[0] for c in C.CARDS if c[1] == weapon]
    cols = 6
    cell = 128 * 2 + 12
    rows = (len(ids) + cols - 1) // cols
    strip_h = 128 + 16
    W = max(cols * cell + 12, len(ids) * 134 + 12)
    H = rows * (cell + 14) + 12 + 3 * strip_h + 10
    c = Image.new("RGBA", (W, H), (20, 18, 16, 255))
    d = ImageDraw.Draw(c)
    for i, cid in enumerate(ids):
        im = Image.open(os.path.join(OUT, cid + ".png")).convert("RGBA")
        x, y = 12 + (i % cols) * cell, 12 + (i // cols) * (cell + 14)
        bg = Image.new("RGBA", (256, 256), hex2rgb(SEPIA[1]) + (255,))
        bg.alpha_composite(im.resize((256, 256), Image.NEAREST))
        c.paste(bg, (x, y))
        d.text((x, y + 258), cid.replace(weapon + "_", ""), fill=(200, 190, 170, 255))
    y0 = 12 + rows * (cell + 14) + 4
    for j, bgc in enumerate((SEPIA[1], SEPIA[3], kit.NAMED["G02"])):
        y = y0 + j * strip_h
        d.rectangle((0, y, W, y + strip_h - 4), fill=hex2rgb(bgc) + (255,))
        for i, cid in enumerate(ids):
            im = Image.open(os.path.join(OUT, cid + ".png")).convert("RGBA")
            x = 12 + i * 134
            if x + 128 > W:
                break
            c.alpha_composite(im, (x, y + 6))
    return c


def main():
    report = {}
    bad = 0
    for cid, weapon, *_ in C.CARDS:
        errs, ncol, npx = check(cid, weapon)
        report[cid] = {"colors": ncol, "opaquePx": npx, "errors": errs}
        if errs or npx < 2000:
            bad += 1
            print("FAIL", cid, errs, npx)
    for w in C.WEAPONS:
        sheet(w).save(os.path.join(HERE, f"preview_{w}.png"))
    json.dump({"cards": len(C.CARDS), "fail": bad, "report": report}, open(os.path.join(HERE, "check.json"), "w"),
              ensure_ascii=False, indent=1)
    print("checked", len(C.CARDS), "fail", bad)


if __name__ == "__main__":
    main()
