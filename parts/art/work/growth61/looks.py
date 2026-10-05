"""미리보기 정지 그림 — assets/sprites/looks/ (UI 각성 선택 화면·성장도 나무용, 무기만·손 없음, 192×192 투명).

  <weapon>_base.png                  기본 무기
  <weapon>_<branch>_a1.png           1차 각성 모양
  <weapon>_<branch>_a2.png           2차 각성 모양(덧붙임까지, 빛 없음 — 빛은 아래 마스크를 UI 가 tint)
  <weapon>_<branch>_a2_glow.png      2차 빛 마스크(회백, 같은 위치) — pathTint 로 곱해 a2 위에
  <weapon>_<branch>_a2_<path>.png    길마다 빛을 미리 물들여 구운 완성 그림(바로 쓰기용)
  <weapon>.json                      목록 · pathTint · 배율
무기마다 같은 위치·같은 정수 배율(가장 큰 그림이 184 안에 들도록) — base → a1 → a2 를 겹쳐 비교할 수 있다.
"""
import json
import os

from PIL import Image

import g61 as Z
import render as RD

OUT = os.path.join(Z.SPR, "looks")
SIZE = 192
STILL_MS = {"greatsword": 400}          # 정지 그림 순환 위상(대검: 핏빛 균열이 찬 순간)


def tint(im, rgb):
    px = im.load()
    out = im.copy()
    po = out.load()
    for y in range(im.height):
        for x in range(im.width):
            c = px[x, y]
            if c[3]:
                po[x, y] = (c[0] * rgb[0] // 255, c[1] * rgb[1] // 255, c[2] * rgb[2] // 255, 255)
    return out


def layers(weapon, deg=None):
    im, tip, grip = RD.still_frame(weapon, deg)
    pad = Z.P.PAD[weapon]
    W, H = im.width + pad[0] + pad[2], im.height + pad[1] + pad[3]
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    base.alpha_composite(im, (pad[0], pad[1]))
    out = {"base": base}
    for bid, ko, line, paths in Z.BRANCHES[weapon]:
        a1, a2, gl = RD.render(weapon, bid, im, tip=tip, grip=grip, state=None, glow=False, ms0=STILL_MS.get(weapon, 0))
        s1 = base.copy()
        s1.alpha_composite(a1)
        s2 = s1.copy()
        s2.alpha_composite(a2)
        out[bid + "_a1"] = s1
        out[bid + "_a2"] = s2
        out[bid + "_a2_glow"] = gl
        for pid, (pko, rgb) in paths.items():
            s3 = s2.copy()
            s3.alpha_composite(tint(gl, rgb))
            out["%s_a2_%s" % (bid, pid)] = s3
    return out


def union(L):
    box = None
    for im in L.values():
        b = im.getbbox()
        if b:
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    return box


def build(weapons=Z.WEAPONS):
    os.makedirs(OUT, exist_ok=True)
    res = {}
    for w in weapons:
        best = None
        for deg in range(-24, -63, -3):                  # 가장 큰 정수 배율이 나오는 기울기(같으면 −42° 에 가까운 쪽)
            L_ = layers(w, deg)
            b_ = union(L_)
            k_ = max(1, (SIZE - 8) // max(b_[2] - b_[0], b_[3] - b_[1]))
            key = (k_, -abs(deg + 42))
            if best is None or key > best[0]:
                best = (key, deg, L_)
        L = best[2]
        box = None
        for im in L.values():
            b = im.getbbox()
            if b:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        bw, bh = box[2] - box[0], box[3] - box[1]
        k = max(1, (SIZE - 8) // max(bw, bh))
        ox = (SIZE - bw * k) // 2
        oy = (SIZE - bh * k) // 2
        files = {}
        for name, im in L.items():
            c = im.crop(box).resize((bw * k, bh * k), Image.NEAREST)
            o = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
            o.alpha_composite(c, (ox, oy))
            fn = "%s_%s.png" % (w, name)
            o.save(os.path.join(OUT, fn), optimize=True)
            files[name] = fn
            res[(w, name)] = o
        meta = dict(
            weapon=w, version=Z.VERSION, angleDeg=best[1], source=Z.SRC, size=[SIZE, SIZE], displayScale=k,
            note=("UI 각성 선택 화면·성장도 나무용 정지 그림(무기만·손 없음·투명). 같은 무기는 모두 같은 위치·같은 정수 배율 %d — 겹쳐 비교 가능. "
                  "a2 = 덧붙임까지(빛 없음), a2_glow = 빛 마스크(회백) → UI 가 pathTint 로 곱해(setTint) a2 위에 겹침. "
                  "a2_<길> = 길 강조색을 미리 구운 완성 그림(바로 쓰기)") % k,
            base=files["base"],
            branches={bid: dict(name=ko, line=line, a1=files[bid + "_a1"], a2=files[bid + "_a2"], a2Glow=files[bid + "_a2_glow"],
                                pathTint={pid: rgb for pid, (pko, rgb) in paths.items()},
                                pathNames={pid: pko for pid, (pko, rgb) in paths.items()},
                                a2ByPath={pid: files["%s_a2_%s" % (bid, pid)] for pid in paths})
                      for bid, ko, line, paths in Z.BRANCHES[w]})
        with open(os.path.join(OUT, w + ".json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        print(w, "deg=%d" % best[1], "k=%d" % k, "box", bw, bh, len(files), "장")
    return res


if __name__ == "__main__":
    import sys
    build([a for a in sys.argv[1:]] or Z.WEAPONS)
