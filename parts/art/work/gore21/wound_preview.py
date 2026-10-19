"""상흔 미리보기: 본 몸 + 단계 0~3 (어두운 바닥, 4배) — 행 = 방향, 열 = 단계."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hero_harness as hh
from PIL import Image

def make(sheet, frame=0, scale=4, out=None):
    meta, af = hh.asset_frames(sheet)
    rows = []
    stages = {k: hh.render(sheet, k)[0] for k in (1, 2, 3)}
    for d in meta["directions"]:
        b = af[d][frame].convert("RGBA")
        row = [b] + [stages[k][d][frame] for k in (1, 2, 3)]
        rows.append(row)
    fw, fh = rows[0][0].size
    o = Image.new("RGB", (4 * fw * scale, len(rows) * fh * scale), (30, 30, 34))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            o.paste(im.resize((fw * scale, fh * scale), Image.NEAREST), (c * fw * scale, r * fh * scale), im.resize((fw * scale, fh * scale), Image.NEAREST))
    o.save(out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "preview", "wound_%s_f%d.png" % (sheet, frame)))

if __name__ == "__main__":
    make(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0)
