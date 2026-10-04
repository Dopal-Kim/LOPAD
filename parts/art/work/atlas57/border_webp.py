"""57라운드 Q17: 외벽 그림(assets/tiles/border/**) PNG → WebP 손실 압축 + 4096px 초과 분할.

출력(스테이징): parts/art/work/atlas57/border_webp/<region>/  — assets 는 바꾸지 않는다.
- albedo: WebP 손실(--q, 기본 90, method 6), 알파는 무손실(alpha_quality 100) — 알파 오차 0.
- emissive(*_emissive.png): --emissive lossy|lossless (기본 lossless — 차이 0.3MB 로 가산 발광을 정확히 유지). 알파 = 세기라 알파는 항상 무손실.
- 가로나 세로가 --max(4096) 를 넘으면 긴 축으로 짝수 px 경계에서 n 등분 → <이름>_<i>.webp (+ <이름>_<i>_emissive.webp).
  border.json 의 해당 띠(bands.<방향> 또는 bands.north.sides.<left|right>)에서 image/emissive 를 빼고
  pieces[] = [{image, emissive, x, y, width, height}] (논리 px, 띠 왼쪽 위 기준)를 넣는다.
- 그 밖의 *.png 참조(image·emissive·file·mirrorOf)는 확장자만 .webp 로.
- border.json 최상위에 imageFormat 블록을 더한다.
- 비교 미리보기: border_webp/preview/compare_<region>.png (원본 | WebP | 차이×8, 4배 확대 크롭)

사용: python3 border_webp.py [--q 90] [--emissive lossy] [--max 4096] [--no-preview]
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import math
import os
from glob import glob

from PIL import Image, ImageChops, ImageDraw, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
SRC = os.path.join(ROOT, "assets", "tiles", "border")
OUT = os.path.join(HERE, "border_webp")


def encode(im: Image.Image, q: int, lossless: bool) -> bytes:
    buf = io.BytesIO()
    if lossless:
        im.save(buf, "WEBP", lossless=True, quality=100, method=6, exact=False)
    else:
        im.save(buf, "WEBP", quality=q, method=6, alpha_quality=100)
    return buf.getvalue()


def split_ranges(n_px: int, max_side: int):
    if n_px <= max_side:
        return [(0, n_px)]
    n = math.ceil(n_px / max_side)
    step = math.ceil(n_px / n)
    step += step % 2  # 짝수 경계(논리 px 정수)
    out, s = [], 0
    while s < n_px:
        e = min(n_px, s + step)
        out.append((s, e))
        s = e
    return out


def metrics(a: Image.Image, b: Image.Image):
    bg = Image.new("RGBA", a.size, (128, 128, 128, 255))
    ca = Image.alpha_composite(bg, a).convert("RGB")
    cb = Image.alpha_composite(bg, b.convert("RGBA")).convert("RGB")
    d = ImageChops.difference(ca, cb)
    mse = sum(x * x for x in ImageStat.Stat(d).rms) / 3
    psnr = 99.0 if mse == 0 else 10 * math.log10(255 ** 2 / mse)
    h = d.convert("L").histogram()
    n, c, p999 = sum(h), 0, 0
    for i, v in enumerate(h):
        c += v
        if c >= 0.999 * n:
            p999 = i
            break
    aerr = ImageChops.difference(a.getchannel("A"), b.convert("RGBA").getchannel("A")).getextrema()[1]
    return round(psnr, 2), p999, aerr


def convert_region(region_dir, out_dir, q, emissive_mode, max_side):
    os.makedirs(out_dir, exist_ok=True)
    region = os.path.basename(region_dir)
    files = {}
    stats = []
    for p in sorted(glob(os.path.join(region_dir, "*.png"))):
        name = os.path.basename(p)[:-4]
        im = Image.open(p).convert("RGBA")
        is_em = name.endswith("_emissive")
        lossless = is_em and emissive_mode == "lossless"
        axis = "x" if im.width >= im.height else "y"
        rngs = split_ranges(im.width if axis == "x" else im.height, max_side)
        pieces = []
        for i, (s, e) in enumerate(rngs):
            box = (s, 0, e, im.height) if axis == "x" else (0, s, im.width, e)
            part = im.crop(box)
            if len(rngs) == 1:
                fn = f"{name}.webp"
            elif is_em:
                fn = f"{name[:-len('_emissive')]}_{i}_emissive.webp"
            else:
                fn = f"{name}_{i}.webp"
            data = encode(part, q, lossless)
            with open(os.path.join(out_dir, fn), "wb") as f:
                f.write(data)
            back = Image.open(io.BytesIO(data))
            psnr, p999, aerr = metrics(part, back)
            pieces.append({"file": fn, "box": box, "psnr": psnr, "p999": p999, "alphaErr": aerr, "bytes": len(data)})
        files[name] = {"size": im.size, "axis": axis, "pieces": pieces}
        stats.append({"region": region, "file": name + ".png", "size": list(im.size), "pngBytes": os.path.getsize(p),
                      "webpBytes": sum(x["bytes"] for x in pieces), "pieces": [x["file"] for x in pieces],
                      "psnrMin": min(x["psnr"] for x in pieces), "p999Max": max(x["p999"] for x in pieces),
                      "alphaErrMax": max(x["alphaErr"] for x in pieces), "lossless": lossless})
    # JSON
    jp = os.path.join(region_dir, "border.json")
    meta = json.load(open(jp, encoding="utf-8"))
    out = copy.deepcopy(meta)
    pscale = float(meta.get("pixelScale", 0.5))

    def fix_band(band):
        img = band.get("image")
        if not isinstance(img, str) or not img.endswith(".png"):
            return
        stem = img[:-4]
        info = files.get(stem)
        if info and len(info["pieces"]) > 1:
            em = band.get("emissive")
            em_info = files.get(em[:-4]) if isinstance(em, str) else None
            plist = []
            for i, pc in enumerate(info["pieces"]):
                x0, y0, x1, y1 = pc["box"]
                entry = {"image": pc["file"]}
                if em_info:
                    entry["emissive"] = em_info["pieces"][i]["file"]
                entry.update({"x": x0 * pscale, "y": y0 * pscale, "width": (x1 - x0) * pscale, "height": (y1 - y0) * pscale})
                plist.append(entry)
            band.pop("image", None)
            band.pop("emissive", None)
            band["pieces"] = plist
            band["piecesNote"] = (f"57라운드 Q17: 원 그림 {info['size'][0]}×{info['size'][1]}px 가 4096 을 넘어 {info['axis']} 축 {len(plist)}조각. "
                                  "조각을 x/y(띠 국소 논리 px) 에 이어 붙이면 원 띠 한 장(width×height)과 같다. 반복·focusX·lights 는 원 띠 기준 그대로")

    def walk(o):
        if isinstance(o, dict):
            if "image" in o:
                fix_band(o)
            for k, v in list(o.items()):
                if isinstance(v, str) and v.endswith(".png") and k in ("image", "emissive", "file", "mirrorOf"):
                    o[k] = v[:-4] + ".webp"
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(out.get("bands", {}))
    walk(out.get("doors", {}))
    out["imageFormat"] = {
        "round": 57,
        "format": "webp",
        "albedo": f"lossy q{q}, alpha lossless",
        "emissive": "lossless" if emissive_mode == "lossless" else f"lossy q{q}, alpha lossless",
        "maxTextureSide": max_side,
        "pieces": "가로·세로 4096px 초과 그림은 bands.*.pieces[] 로 분할(그 띠는 image/emissive 키 없음)",
        "source": "parts/art/work/atlas57/border_webp.py (원본 PNG 는 assets/tiles/border 에 그대로)",
    }
    with open(os.path.join(out_dir, "border.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return files, stats


def zoom(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def compare_preview(region_dir, out_dir, files, q, prev_dir):
    """원본 | WebP | 차이×8 (회색 바탕 합성) — 크롭 3곳, 4배."""
    region = os.path.basename(region_dir)
    picks = [("north", 0.35, 0.25), ("north", 0.5, 0.75), ("west", 0.5, 0.2), ("door_north", 0.5, 0.4), ("north_emissive", None, None)]
    rows = []
    crop = 120
    S = 4
    for name, fx, fy in picks:
        if name not in files:
            continue
        orig = Image.open(os.path.join(region_dir, name + ".png")).convert("RGBA")
        if fx is None:  # 발광: 알파 가장 큰 곳 근처
            small = orig.getchannel("A").reduce(16)
            px = small.load()
            best = max(((px[x, y], x, y) for y in range(small.height) for x in range(small.width)))
            cx, cy = best[1] * 16 + 8, best[2] * 16 + 8
        else:
            cx, cy = int(orig.width * fx), int(orig.height * fy)
        x0 = max(0, min(orig.width - crop, cx - crop // 2))
        y0 = max(0, min(orig.height - crop, cy - crop // 2))
        # 조각에서 같은 영역 찾기
        info = files[name]
        web = Image.new("RGBA", orig.size, (0, 0, 0, 0))
        for pc in info["pieces"]:
            web.paste(Image.open(os.path.join(out_dir, pc["file"])).convert("RGBA"), pc["box"][:2])
        box = (x0, y0, x0 + crop, y0 + crop)
        bg = (128, 128, 128, 255) if not name.endswith("emissive") else (16, 16, 20, 255)
        co = Image.alpha_composite(Image.new("RGBA", (crop, crop), bg), orig.crop(box))
        cw = Image.alpha_composite(Image.new("RGBA", (crop, crop), bg), web.crop(box))
        d = ImageChops.difference(co.convert("RGB"), cw.convert("RGB")).point(lambda v: min(255, v * 8))
        rows.append((f"{name} ({x0},{y0})", [zoom(co, S), zoom(cw, S), zoom(d.convert("RGBA"), S)]))
    W = crop * S * 3 + 40
    H = sum(crop * S + 22 for _ in rows) + 24
    sheet = Image.new("RGBA", (W, H), (30, 30, 34, 255))
    dr = ImageDraw.Draw(sheet)
    dr.text((6, 4), f"{region}: original PNG | WebP q{q} | |diff| x8   (4x zoom, 1 image px = 1 screen px at 1920)", fill=(230, 230, 230))
    y = 24
    for label, ims in rows:
        dr.text((6, y), label, fill=(200, 200, 200))
        y += 18
        for i, im in enumerate(ims):
            sheet.paste(im, (10 + i * (crop * S + 10), y))
        y += crop * S + 4
    os.makedirs(prev_dir, exist_ok=True)
    sheet.convert("RGB").save(os.path.join(prev_dir, f"compare_{region}.png"), optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", type=int, default=90)
    ap.add_argument("--emissive", choices=["lossy", "lossless"], default="lossless")
    ap.add_argument("--max", type=int, default=4096)
    ap.add_argument("--no-preview", action="store_true")
    args = ap.parse_args()

    all_stats = []
    for rd in sorted(glob(os.path.join(SRC, "*"))):
        if not os.path.isdir(rd):
            continue
        od = os.path.join(OUT, os.path.basename(rd))
        files, stats = convert_region(rd, od, args.q, args.emissive, args.max)
        all_stats += stats
        if not args.no_preview:
            compare_preview(rd, od, files, args.q, os.path.join(OUT, "preview"))
        print(os.path.basename(rd), "완료")
    with open(os.path.join(OUT, "report.json"), "w", encoding="utf-8") as f:
        json.dump({"q": args.q, "emissive": args.emissive, "max": args.max, "files": all_stats}, f, ensure_ascii=False, indent=1)

    print("\n| 지역 | PNG(MB) | WebP(MB) | 비율 | PSNR 최저(dB) | 99.9% 오차 최대 | 알파 오차 |")
    print("|---|---|---|---|---|---|---|")
    regions = sorted({s["region"] for s in all_stats})
    tp = tw = 0
    for r in regions + ["합계"]:
        ss = all_stats if r == "합계" else [s for s in all_stats if s["region"] == r]
        p = sum(s["pngBytes"] for s in ss)
        w = sum(s["webpBytes"] for s in ss)
        print(f"| {r} | {p/1e6:.2f} | {w/1e6:.2f} | {100*w/p:.1f}% | {min(s['psnrMin'] for s in ss):.1f} | "
              f"{max(s['p999Max'] for s in ss)} | {max(s['alphaErrMax'] for s in ss)} |")
    for kind in ("albedo", "emissive"):
        ss = [s for s in all_stats if ("_emissive" in s["file"]) == (kind == "emissive")]
        p = sum(s["pngBytes"] for s in ss)
        w = sum(s["webpBytes"] for s in ss)
        print(f"  {kind}: {p/1e6:.2f}MB → {w/1e6:.2f}MB")
    split = [s for s in all_stats if len(s["pieces"]) > 1]
    print("\n분할:", ", ".join(f"{s['region']}/{s['file']} {s['size'][0]}x{s['size'][1]} → {len(s['pieces'])}조각" for s in split))


if __name__ == "__main__":
    main()
