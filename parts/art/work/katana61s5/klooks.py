"""61 단계 5 칼 미리보기 정지 그림 looks/katana_* — 무기 시트와 같은 3D 칼 그리기(kdesign)로 −36° 정지 칼을 그려 192×192 에 정수 배율로.
파일 이름·looks/katana.json 구조는 61 단계 4(growth61) 그대로(UI 무수정)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kcommon as C  # noqa: E402
from PIL import Image  # noqa: E402

SIZE = 192
ANGLE = -36
OUT = os.path.join(C.SPR, "looks")
BR = [("senpu", "선풍", "무리 한가운데로 파고드는 칼", {"whirl": ("회오리", [196, 228, 255]), "zangetsu": ("잔월", [255, 212, 110])}),
      ("kabuto", "투구가르기", "한 놈을 쪼개는 칼", {"ittou": ("일도양단", [255, 92, 72]), "meikyo": ("명경", [200, 240, 255])}),
      ("mangetsu", "만월", "받아치는 칼", {"sakugetsu": ("삭월", [176, 150, 255]), "hozuki": ("보름", [255, 226, 140])})]


def tint(im, rgb):
    out = im.copy()
    px = im.load()
    po = out.load()
    for y in range(im.height):
        for x in range(im.width):
            c = px[x, y]
            if c[3]:
                po[x, y] = (c[0] * rgb[0] // 255, c[1] * rgb[1] // 255, c[2] * rgb[2] // 255, 255)
    return out


def still(layer, branch, ksrc, KD):
    import math
    K = ksrc.K
    KD.V.update(layer=layer, branch=branch, level=0, pad=(120, 120, 420, 420), phase=0, tn=8, glowframe=False, starts=None)
    L = K.Layer()
    a = math.radians(-ANGLE)
    v = (math.cos(a), 0.0, math.sin(a))
    K.draw_katana(L, "right", (20.0, 60.0, 0.0), v, "steel", seed=0)
    return K.rasterize(L, None)


def build():
    import ksrc
    import kdesign as KD
    KD.install(ksrc.K, ksrc.hero)
    base = still("base", None, ksrc, KD)
    L = {"base": base}
    for bid, ko, line, paths in BR:
        a1, a2, gl = (still(x, bid, ksrc, KD) for x in ("a1", "a2", "glow"))
        s1 = base.copy()
        s1.alpha_composite(a1)
        s2 = s1.copy()
        s2.alpha_composite(a2)
        L[bid + "_a1"] = s1
        L[bid + "_a2"] = s2
        L[bid + "_a2_glow"] = gl
        for pid, (pko, rgb) in paths.items():
            s3 = s2.copy()
            s3.alpha_composite(tint(gl, rgb))
            L["%s_a2_%s" % (bid, pid)] = s3
    box = None
    for im in L.values():
        b = im.getbbox()
        if b:
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    bw, bh = box[2] - box[0], box[3] - box[1]
    k = max(1, (SIZE - 8) // max(bw, bh))
    ox, oy = (SIZE - bw * k) // 2, (SIZE - bh * k) // 2
    files = {}
    for name, im in L.items():
        c = im.crop(box).resize((bw * k, bh * k), Image.NEAREST)
        o = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        o.alpha_composite(c, (ox, oy))
        fn = "katana_%s.png" % name
        o.save(os.path.join(OUT, fn), optimize=True)
        files[name] = fn
    jp = os.path.join(OUT, "katana.json")
    meta = json.load(open(jp, encoding="utf-8"))
    meta.update(version=C.VERSION_V4, angleDeg=ANGLE, source=C.SRC, displayScale=k,
                r61s5="61 단계 5: 은선 칼과 갈래 3 외형을 무기 시트와 같은 3D 그리기로 다시 그림(파일 이름·구조 그대로)")
    for bid, ko, line, paths in BR:
        b = meta["branches"][bid]
        b["design"] = {"a1": None}
    import wbuild
    for bid, ko, line, paths in BR:
        meta["branches"][bid]["design"] = {k_: wbuild.BR_DESIGN[bid][k_] for k_ in ("a1", "a2", "glow")}
    meta["baseDesign"] = wbuild.DESIGN_BASE
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return files, k


if __name__ == "__main__":
    print(build())
