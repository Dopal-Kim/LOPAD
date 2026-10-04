"""각성 오버레이 미리보기: 행마다 [무기만 | 무기+오버레이] — python3 pv_ov.py out.png 시트... (방향 right·down)"""
import os
import sys

from PIL import Image, ImageDraw

import kit as K
import pv57


def main(out, sheets, dirs=("right", "down"), scale=2):
    blocks = []
    for s in sheets:
        j, wf = K.grid_frames("weapons/v3/" + s)
        oj, of = pv57.load(s + "_awaken", "weapons")
        fw, fh = j["frameWidth"], j["frameHeight"]
        n = j["frames"]
        dd = [d for d in dirs if d in wf]
        img = Image.new("RGBA", (n * (fw * scale + 4) + 90, 20 + len(dd) * 2 * (fh * scale + 4)), (18, 17, 20, 255))
        dr = ImageDraw.Draw(img)
        dr.text((4, 4), s + "_awaken  glow=%s" % oj.get("glowFrames"), fill=(220, 220, 220))
        y = 20
        for d in dd:
            for mode in (0, 1):
                dr.text((4, y + 4), d + (" +aw" if mode else ""), fill=(160, 160, 160))
                for c in range(n):
                    t = Image.new("RGBA", (fw, fh), pv57.BG)
                    t.alpha_composite(wf[d][c])
                    if mode:
                        t.alpha_composite(of[d][c])
                    img.alpha_composite(t.resize((fw * scale, fh * scale), Image.NEAREST), (90 + c * (fw * scale + 4), y))
                y += fh * scale + 4
        blocks.append(img)
    W_ = max(b.width for b in blocks)
    H_ = sum(b.height + 6 for b in blocks)
    sh = Image.new("RGBA", (W_, H_), (10, 10, 12, 255))
    y = 0
    for b in blocks:
        sh.alpha_composite(b, (0, y))
        y += b.height + 6
    sh.save(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
