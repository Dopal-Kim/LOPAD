"""57라운드 아틀라스 검증 — 원 격자 시트와 픽셀 비교 + 형식 점검.

1) 무작위 프레임 N개(기본 20, 시드 57)를 아틀라스에서 복원해(sourceSize 투명 캔버스에 spriteSourceSize 위치로 붙임)
   원 격자 프레임과 RGBA 비교. 알파 0 픽셀은 RGB 무시(같은 것으로 본다).
2) --all 이면 모든 시트·모든 프레임을 같은 방식으로 비교.
3) 형식: 기존 메타 필드 보존(frames→framesPerDirection), 프레임 이름 0..N-1 전부, 텍스처 ≤ max,
   frame 사각형이 텍스처 안, 서로 다른 frame 사각형끼리 겹치지 않음, sourceSize = frameWidth/Height.

사용: python3 verify.py [--root out/sprites] [--n 20] [--seed 57] [--all] [--max 4096]
"""
from __future__ import annotations

import argparse
import json
import os
import random
from glob import glob

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
SRC = os.path.join(ROOT, "assets", "sprites")


def norm_bytes(im: Image.Image) -> bytes:
    im = im.convert("RGBA")
    mask = im.getchannel("A").point(lambda v: 255 if v == 0 else 0)
    im.paste((0, 0, 0, 0), (0, 0) + im.size, mask)
    return im.tobytes()


def frame_table(atlas: dict):
    """{이름: (이미지 파일, entry)}"""
    if "textures" in atlas:
        out = {}
        for t in atlas["textures"]:
            for e in t["frames"]:
                out[e["filename"]] = (t["image"], e)
        return out
    return {k: (atlas["meta"]["image"], v) for k, v in atlas["frames"].items()}


def rebuild(atlas_dir, image_name, e, cache):
    if image_name not in cache:
        cache[image_name] = Image.open(os.path.join(atlas_dir, image_name)).convert("RGBA")
    a = cache[image_name]
    f, s, ss = e["frame"], e["spriteSourceSize"], e["sourceSize"]
    crop = a.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"]))
    canvas = Image.new("RGBA", (ss["w"], ss["h"]), (0, 0, 0, 0))
    canvas.paste(crop, (s["x"], s["y"]))
    return canvas


def check_format(src_meta, atlas, max_side):
    errs = []
    for k, v in src_meta.items():
        if k == "frames":
            if atlas.get("framesPerDirection") != v:
                errs.append("framesPerDirection 불일치")
        elif k == "image":
            continue
        elif atlas.get(k) != v:
            errs.append(f"메타 필드 변경: {k}")
    cols = atlas["atlas"]["grid"]["columns"]
    rows = atlas["atlas"]["grid"]["rows"]
    table = frame_table(atlas)
    names = {str(i) for i in range(cols * rows)}
    if set(table) != names:
        errs.append(f"프레임 이름 불일치: {len(table)} vs {len(names)}")
    sizes = {}
    if "textures" in atlas:
        for t in atlas["textures"]:
            sizes[t["image"]] = (t["size"]["w"], t["size"]["h"])
    else:
        sizes[atlas["meta"]["image"]] = (atlas["meta"]["size"]["w"], atlas["meta"]["size"]["h"])
    for img, (w, h) in sizes.items():
        if w > max_side or h > max_side:
            errs.append(f"텍스처 초과 {img} {w}x{h}")
    rects = {}
    for name, (img, e) in table.items():
        f = e["frame"]
        W, H = sizes[img]
        if f["x"] < 0 or f["y"] < 0 or f["x"] + f["w"] > W or f["y"] + f["h"] > H:
            errs.append(f"프레임 {name} 텍스처 밖")
        if e["sourceSize"] != {"w": src_meta["frameWidth"], "h": src_meta["frameHeight"]}:
            errs.append(f"프레임 {name} sourceSize 불일치")
        s = e["spriteSourceSize"]
        if s["x"] + s["w"] > src_meta["frameWidth"] or s["y"] + s["h"] > src_meta["frameHeight"]:
            errs.append(f"프레임 {name} spriteSourceSize 범위 밖")
        rects.setdefault(img, set()).add((f["x"], f["y"], f["w"], f["h"]))
    for img, rs in rects.items():
        rs = sorted(rs)
        for i, a in enumerate(rs):
            for b in rs[i + 1:]:
                if b[0] >= a[0] + a[2]:
                    break
                if not (a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1]):
                    errs.append(f"겹침 {img} {a} {b}")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(HERE, "out", "sprites"))
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=57)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--max", type=int, default=4096)
    args = ap.parse_args()

    atlases = sorted(glob(os.path.join(args.root, "*", "v3", "*.json")))
    pairs = []
    fmt_errs = 0
    for ap_ in atlases:
        rel = os.path.relpath(ap_, args.root)
        sp = os.path.join(SRC, rel)
        src_meta = json.load(open(sp, encoding="utf-8"))
        atlas = json.load(open(ap_, encoding="utf-8"))
        errs = check_format(src_meta, atlas, args.max)
        if errs:
            fmt_errs += len(errs)
            print("형식 오류", rel, errs[:5])
        pairs.append((rel, sp, ap_, src_meta, atlas))
    print(f"형식 점검: 시트 {len(pairs)}개, 오류 {fmt_errs}")

    jobs = []
    if args.all:
        for p in pairs:
            g = p[4]["atlas"]["grid"]
            jobs += [(p, i) for i in range(g["columns"] * g["rows"])]
    else:
        rnd = random.Random(args.seed)
        for _ in range(args.n):
            p = rnd.choice(pairs)
            g = p[4]["atlas"]["grid"]
            jobs.append((p, rnd.randrange(g["columns"] * g["rows"])))

    bad = 0
    src_cache, at_cache = {}, {}
    last = None
    for (rel, sp, ap_, meta, atlas), i in jobs:
        if last != rel:
            at_cache.clear()
            last = rel
        png = sp[:-5] + ".png"
        if png not in src_cache:
            src_cache.clear()
            src_cache[png] = Image.open(png).convert("RGBA")
        sheet = src_cache[png]
        fw, fh = meta["frameWidth"], meta["frameHeight"]
        cols = sheet.width // fw
        r, c = divmod(i, cols)
        orig = sheet.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))
        img, e = frame_table(atlas)[str(i)]
        got = rebuild(os.path.dirname(ap_), img, e, at_cache)
        same = norm_bytes(orig) == norm_bytes(got)
        opaque = orig.getchannel("A").point(lambda v: 1 if v else 0).histogram()[1] if not args.all else 0
        if not same:
            bad += 1
        if not args.all:
            print(f"{'OK ' if same else 'DIFF'} {rel[:-5]} #{i} 원 {fw}x{fh} → 트림 {e['frame']['w']}x{e['frame']['h']}"
                  f" @({e['spriteSourceSize']['x']},{e['spriteSourceSize']['y']}) 불투명 {opaque}px")
    print(f"픽셀 비교: {len(jobs)}프레임 중 불일치 {bad}")
    return 1 if (bad or fmt_errs) else 0


if __name__ == "__main__":
    raise SystemExit(main())
