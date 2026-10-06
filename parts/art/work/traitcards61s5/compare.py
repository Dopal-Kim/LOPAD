"""반복 검수용 — 태그별 변환 결과를 나란히(2배). python3 compare.py out.png b,c id ..."""
import sys, os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import importlib.util as _u
_s = _u.spec_from_file_location("tc_build", os.path.join(HERE, "build.py")); B = _u.module_from_spec(_s); _s.loader.exec_module(B)
out, tags, ids = sys.argv[1], sys.argv[2].split(","), sys.argv[3:]
cw = len(tags) * 262 + 20
cols = 2
c = Image.new("RGBA", (cw * cols, 276 * ((len(ids) + cols - 1) // cols)), (20, 18, 16, 255))
d = ImageDraw.Draw(c)
for i, cid in enumerate(ids):
    x0, y0 = (i % cols) * cw, (i // cols) * 276
    for j, t in enumerate(tags):
        if not os.path.exists(os.path.join(HERE, "raw", f"{cid}_{t}.jpg")):
            continue
        bg = Image.new("RGBA", (256, 256), (48, 38, 30, 255))
        bg.alpha_composite(B.make(cid, t).resize((256, 256), Image.NEAREST))
        c.paste(bg, (x0 + j * 262, y0))
        d.text((x0 + j * 262 + 2, y0 + 258), f"{cid} [{t}]", fill=(220, 200, 170, 255))
c.save(out)
