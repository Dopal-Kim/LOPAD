"""미리보기 판 — 카드 흉내(256×144 논리 = 512×288 렌더, 아래 먹 띠) · 원본 대비."""
import glob
import os

from PIL import Image, ImageDraw

from c62 import PAINT, HERE


def card(im, band=0.36):
    im = im.convert("RGB").resize((512, 288), Image.LANCZOS) if im.size != (512, 288) else im.convert("RGB")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    top = int(288 * (1 - band))
    for i in range(4):
        d.rectangle((0, top - (4 - i) * 10, 512, top - (3 - i) * 10), fill=(20, 21, 22, int(255 * 0.78 * (i + 1) / 5)))
    d.rectangle((0, top, 512, 288), fill=(20, 21, 22, int(255 * 0.78)))
    d.rectangle((24, top + 14, 200, top + 30), fill=(198, 165, 139, 255))
    d.rectangle((24, top + 44, 380, top + 54), fill=(110, 100, 90, 255))
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def doors(names, out, cols=2):
    tiles = []
    for n in names:
        full = Image.open(os.path.join(PAINT, n + ".png"))
        sp = os.path.join(PAINT, n + "_small.png")
        small = Image.open(sp) if os.path.exists(sp) else full
        tiles.append((card(full), card(small)))
    pad = 8
    tw = 512 * 2 + pad * 3
    th = 288 + pad
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, th * rows + pad), (64, 52, 40))
    for i, (a, b) in enumerate(tiles):
        x = (i % cols) * tw + pad
        y = (i // cols) * th + pad
        sheet.paste(a, (x, y))
        sheet.paste(b, (x + 512 + pad, y))
    sheet.save(out)
    return out
