"""반복 검수용: 기둥 15(crack3) + collapse 10 + rubble 2 를 어두운 바탕에 나란히 (assets 미변경)."""
import sys
from PIL import Image
import pillar5 as P
from kit5 import scale
k = int(sys.argv[1]) if len(sys.argv) > 1 else 1
old, col = P.collapse_frames()
fr = [old[15]] + col + P.rubble_frames()
im = Image.new("RGBA", (P.PW * len(fr), P.PH), (28, 26, 32, 255))
for i, f in enumerate(fr):
    im.alpha_composite(f, (i * P.PW, 0))
scale(im, k).convert("RGB").save("out/quick_pillar.png")
