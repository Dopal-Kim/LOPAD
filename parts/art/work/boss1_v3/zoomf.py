"""작업용: python3 zoomf.py out.png act:i act:i ... → 4방향 4배."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "enemies_v3")); sys.path.insert(0, HERE)
import b1acts
from PIL import Image
k = int(os.environ.get("K", "3"))
rows = []
for spec in sys.argv[2:]:
    a, i = spec.split(":")
    rows.append([b1acts.render_full(d, b1acts.ACTIONS[a](d)[int(i)])[0] for d in ["down", "up", "left", "right"]])
W = Image.new("RGBA", (128 * 4 * k, 192 * k * len(rows)), (46, 48, 56, 255))
for r, ims in enumerate(rows):
    for c, im in enumerate(ims):
        W.alpha_composite(im.resize((128 * k, 192 * k), Image.NEAREST), (c * 128 * k, r * 192 * k))
W.save(sys.argv[1])
