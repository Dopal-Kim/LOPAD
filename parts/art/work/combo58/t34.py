import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "combo56_body"))
import rig34
NEW = "--old" not in sys.argv
if NEW:
    rig34.install()
import gs56, rig8
from PIL import Image, ImageDraw
if NEW:
    pass
name = sys.argv[1]
dirs = sys.argv[2].split(",")
out = sys.argv[3]
fr = {}
for d in dirs:
    m = gs56.MV.GS[name]
    lst = []
    for i, raw in enumerate(m["frames"]):
        k = gs56.Q.norm(gs56.adjust_key(name, d, raw))
        p = rig8.body_pose8(d, k, i)
        R = rig8.draw_rig8(d, p)
        im, tip = gs56.GS.gear_frame(d, name, k, R)
        lst.append((R.image, im))
    fr[d] = lst
ox, oy = gs56.GS.CANVAS_OFF
CW, CH = 260, 300
x0, y0 = ox - 82, oy - 110
F = len(fr[dirs[0]])
sheet = Image.new("RGBA", (CW * F, CH * len(dirs)), (34, 30, 36, 255))
for r, d in enumerate(dirs):
    for i, (b, w) in enumerate(fr[d]):
        c = Image.new("RGBA", w.size, (0, 0, 0, 0))
        c.alpha_composite(b, (ox, oy))
        c.alpha_composite(w)
        sheet.alpha_composite(c.crop((x0, y0, x0 + CW, y0 + CH)), (i * CW, r * CH))
sc = int(sys.argv[4]) if len(sys.argv) > 4 else 1
sheet = sheet.resize((sheet.width * sc, sheet.height * sc), Image.NEAREST)
sheet.save(out)
