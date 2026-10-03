"""작업용: python3 zoomf.py /절대/경로/out.png act:i act:i ... → 4방향 K배(기본 3). 출력 경로는 절대 경로만(저장소 밖 빈 경로 방지)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "enemies_v3")); sys.path.insert(0, HERE)
import b1acts
from b1body import FW, FH
from PIL import Image
out = sys.argv[1]
assert os.path.isabs(out) and os.path.isdir(os.path.dirname(out)), "절대 경로(존재하는 폴더)만: %r" % out
k = int(os.environ.get("K", "3"))
dirs = os.environ.get("DIRS", "down,up,left,right").split(",")
rows = []
for spec in sys.argv[2:]:
    a, i = spec.split(":")
    rows.append([b1acts.render_full(d, b1acts.ACTIONS[a](d)[int(i)])[0] for d in dirs])
W = Image.new("RGBA", (FW * len(dirs) * k, FH * k * len(rows)), (46, 48, 56, 255))
for r, ims in enumerate(rows):
    for c, im in enumerate(ims):
        W.alpha_composite(im.resize((FW * k, FH * k), Image.NEAREST), (c * FW * k, r * FH * k))
W.save(out)
print(out)
