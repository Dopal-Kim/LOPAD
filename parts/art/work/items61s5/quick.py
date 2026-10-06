"""반복 검수용: 아이템 프레임을 어두운 바탕에 4배로 늘어놓기 (assets 미변경)."""
import sys
from PIL import Image
import items5 as I
from kit5 import scale
k = int(sys.argv[1]) if len(sys.argv) > 1 else 4
rows = []
for kind, spec in I.KINDS.items():
    for row in spec["rows"]:
        rows.append(I.frames_for(kind, row))
im = Image.new("RGBA", (I.FW * I.NCOL, I.FH * len(rows)), (24, 23, 28, 255))
for j, r in enumerate(rows):
    for i, f in enumerate(r):
        im.alpha_composite(f, (i * I.FW, j * I.FH))
scale(im, k).convert("RGB").save("out/quick.png")
# idle 0 확대만
im2 = Image.new("RGBA", (I.FW * 8, I.FH * len(rows)), (24, 23, 28, 255))
for j, r in enumerate(rows):
    for i in range(8):
        im2.alpha_composite(r[[0, 4, 8, 11, 14, 16, 18, 22][i]], (i * I.FW, j * I.FH))
scale(im2, 4).convert("RGB").save("out/quick_key.png")
