"""미리보기 정지 그림 — assets/sprites/looks/dagger_*.png (192×192 투명, 무기만, 같은 위치·같은 정수 배율) + dagger.json 갱신.
게임 오버레이와 같은 경로(blade.paint + overlays 덧붙임)로 그린 1배 그림을 정수 배율로 키운다."""
import json
import math
import os

from PIL import Image

import d5
import blade as BL
import overlays as OV
from d5 import Cv

OUT = os.path.join(d5.SPR, "looks")
SIZE = 192
ANG = -42
LEN = 32.0
TINT_PATHS = {"twin": {"frenzy": [192, 226, 255], "bleed": [255, 72, 92]},
              "gale": {"flyblade": [172, 255, 150], "hotwind": [255, 150, 60]},
              "hyakki": {"nightwalk": [172, 132, 255], "onibi": [100, 240, 220]}}


def tint(im, rgb):
    out = im.copy()
    p = out.load()
    for y in range(im.height):
        for x in range(im.width):
            c = p[x, y]
            if c[3]:
                p[x, y] = (c[0] * rgb[0] // 255, c[1] * rgb[1] // 255, c[2] * rgb[2] // 255, 255)
    return out


def layers():
    W = 96
    g = (44.0, 52.0)
    a = math.radians(ANG)
    tip = (g[0] + LEN * math.cos(a), g[1] + LEN * math.sin(a))
    geo = BL.Geo(g, tip, facing=(1.0, 0.0))
    base = Cv(W + 2 * OV.PAD, W + 2 * OV.PAD)
    BL.paint(base, geo, BL.BaseSkin(), "steel", 0, OV.PAD, OV.PAD)
    out = {"base": base.im}
    for b in ("twin", "gale", "hyakki"):
        a1, a2, gl = OV.render(geo, b, "steel", 0, base.im.size)
        s1 = base.im.copy()
        s1.alpha_composite(a1)
        s2 = s1.copy()
        s2.alpha_composite(a2)
        out[b + "_a1"] = s1
        out[b + "_a2"] = s2
        out[b + "_a2_glow"] = gl
        for pid, rgb in TINT_PATHS[b].items():
            s3 = s2.copy()
            s3.alpha_composite(tint(gl, rgb))
            out["%s_a2_%s" % (b, pid)] = s3
    return out


def build():
    L = layers()
    box = None
    for im in L.values():
        bb = im.getbbox()
        if bb:
            box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
    bw, bh = box[2] - box[0], box[3] - box[1]
    k = max(1, (SIZE - 8) // max(bw, bh))
    ox, oy = (SIZE - bw * k) // 2, (SIZE - bh * k) // 2
    res = {}
    for name, im in L.items():
        c = im.crop(box).resize((bw * k, bh * k), Image.NEAREST)
        o = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        o.alpha_composite(c, (ox, oy))
        fn = "dagger_%s.png" % name
        o.save(os.path.join(OUT, fn), optimize=True)
        res[name] = o
    jp = os.path.join(OUT, "dagger.json")
    meta = json.load(open(jp, encoding="utf-8"))
    meta.update(angleDeg=ANG, displayScale=k, version="v4-r61s5", source=d5.SRC, r61s5=d5.R61S5,
                design="61 단계 5 '재 발톱' — 기본·갈래 1차/2차 모두 무기 시트와 같은 날(blade.paint)·덧붙임(overlays) 경로")
    meta["note"] = meta["note"].replace("배율 3", "배율 %d" % k)
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("looks", len(res), "k=%d" % k, "box", bw, bh)
    return res


if __name__ == "__main__":
    build()
