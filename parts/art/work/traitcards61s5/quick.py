"""반복 검수용 — 몇 장만 변환(build.OPTS 적용)해 원본 | 2배 | 1배 비교. TAG 환경변수로 원본 태그 지정(기본 = build.CHOICE)."""
import sys, os
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kit, cards as C
import importlib.util as _u
_s = _u.spec_from_file_location("tc_build", os.path.join(HERE, "build.py")); B = _u.module_from_spec(_s); _s.loader.exec_module(B)
S = sys.argv[1]
ids = sys.argv[2:]
rows = []
for cid in ids:
    tag = os.environ.get("TAG") or B.CHOICE.get(cid, B.DEFAULT_TAG)
    raw = Image.open(os.path.join(HERE, "raw", f"{cid}_{tag}.jpg"))
    im = B.make(cid, tag)
    row = Image.new("RGBA", (256 + 8 + 256 + 8 + 128, 256), (52, 44, 38, 255))
    row.paste(raw.resize((256, 256)), (0, 0))
    row.alpha_composite(im.resize((256, 256), Image.NEAREST), (264, 0))
    row.alpha_composite(im, (528, 64))
    rows.append(row)
cols = 2
W = rows[0].width + 12
c = Image.new("RGBA", (W * cols, 264 * ((len(rows) + cols - 1) // cols)), (20, 20, 24, 255))
for i, r in enumerate(rows):
    c.paste(r, ((i % cols) * W, 264 * (i // cols)))
c.save(S)
