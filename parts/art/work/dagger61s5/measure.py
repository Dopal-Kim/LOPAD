"""찌르기 fx 의 그림 끝(판정 원점에서 행 방향으로 가장 먼 불투명 도트) 측정 — 전/후 같아야 한다."""
import math
import sys

import view

ROW_ROT = {"down": 90.0, "up": -90.0, "left": 180.0, "right": 0.0}


def reach(rel, root=view.SPR, alpha_min=1):
    m, fr = view.frames(rel, root)
    o = m.get("hitOriginInFrame") or {"x": m["pivot"]["x"], "y": m["pivot"]["y"] - 40}
    th = m.get("thrust") or {}
    ang0 = (th[0] if isinstance(th, list) else th).get("angleDeg", 0)
    out = {}
    for ri, d in enumerate(m["directions"]):
        a = math.radians(ROW_ROT.get(d, 0) + (ang0 if d in ("right", "down") else -ang0 if d in ("left", "up") else 0))
        ux, uy = math.cos(a), math.sin(a)
        row = []
        for im in fr[ri]:
            px = im.load()
            best = None
            for y in range(im.height):
                for x in range(im.width):
                    if px[x, y][3] >= alpha_min:
                        p = (x - o["x"]) * ux + (y - o["y"]) * uy
                        best = p if best is None or p > best else best
            row.append(None if best is None else round(best))
        out[d] = row
    return out


if __name__ == "__main__":
    for n in sys.argv[1:]:
        print(n, reach("fx/v3/" + n))
