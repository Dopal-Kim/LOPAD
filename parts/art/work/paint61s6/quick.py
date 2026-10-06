"""반복 검수용: 소품 프레임을 바닥색 위에 k 배로 늘어놓기 (assets 안 건드림)."""
import sys
from PIL import Image
import tprops

def run(names=None, k=2, out="/tmp/claude-0/-home-user-LOPAD/a2d5d0a8-4b51-57bb-8cb0-fde4dda6c52c/scratchpad/props.png"):
    fr = tprops.build(dry=True, only=names)
    rows = []
    for n, f in fr.items():
        w, h = f[0].size
        row = Image.new("RGBA", (w * 6, h), (58, 60, 66, 255))
        for i, im in enumerate(f):
            row.alpha_composite(im, (i * w, 0))
        rows.append(row)
    W = max(r.width for r in rows); H = sum(r.height for r in rows)
    s = Image.new("RGBA", (W, H), (30, 30, 34, 255)); y = 0
    for r in rows:
        s.paste(r, (0, y)); y += r.height
    s.resize((W * k, H * k), Image.NEAREST).save(out)

if __name__ == "__main__":
    run(sys.argv[1:] or None)
