"""57라운드 Q16: 격자 스프라이트시트 → 트림 아틀라스 변환 (Pillow 만 사용).

입력: assets/sprites/<분류>/v3/<이름>.png + .json (격자 시트, 계약 art-assets §1)
출력: 기본은 parts/art/work/atlas57/out/sprites/<분류>/v3/ (스테이징).
      --in-place 면 assets 를 직접 교체한다(57라운드 Q38): 아직 격자인 시트만 변환 → 전 프레임 픽셀 대조 →
      통과하면 원 격자 PNG·JSON 을 아틀라스로 덮어쓴다(원 격자는 남기지 않는다. 이미 아틀라스면 건너뜀).

- 프레임마다 알파>0 경계 상자로 잘라(trim) MaxRects(BSSF)로 빽빽하게 다시 담는다.
- 프레임 이름 = 기존 격자 번호(row * columns + column) 정수 문자열 → 프레임 인덱스 호환.
- 피벗·앵커 등 기존 메타 필드는 원 프레임(sourceSize) 좌표 그대로 둔다.
- 기존 정수 필드 `frames`(방향당 프레임 수)는 아틀라스 `frames` 와 겹치므로 `framesPerDirection` 으로 옮긴다.
- 한 장 4096×4096 이하. 넘치면 멀티 아틀라스(`textures[]`, Phaser JSONArray 형식).
- 반복 타일(`tile: true`)·리본(`ribbon`) 시트는 트림하지 않는다(trimmed:false, 원 프레임 크기 그대로 배치).
- 빈 프레임은 공용 1×1 투명 칸을 가리킨다. 같은 픽셀 프레임은 같은 frame 좌표를 공유한다.
- 알파 0 픽셀의 RGB 는 0 으로 정규화(보이지 않는 값).

사용: python3 build.py [--in-place] [--cats player,weapons,fx,enemies,bosses,structures] [--only 이름부분]
                      [--pad 2] [--max 4096] [--no-dedup]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import sys
from glob import glob

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
SRC = os.path.join(ROOT, "assets", "sprites")
OUT = os.path.join(HERE, "out", "sprites")

ATLAS_VERSION = "atlas57-1"
CATS = "player,weapons,fx,enemies,bosses,structures"


# ---------------------------------------------------------------- MaxRects
class MaxRects:
    """MaxRects Best-Short-Side-Fit. 회전 없음."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.free = [(0, 0, w, h)]

    def insert(self, w: int, h: int):
        best = None
        for (fx, fy, fw, fh) in self.free:
            if w <= fw and h <= fh:
                short = min(fw - w, fh - h)
                long_ = max(fw - w, fh - h)
                key = (short, long_, fy, fx)
                if best is None or key < best[0]:
                    best = (key, fx, fy)
        if best is None:
            return None
        _, x, y = best
        self._split(x, y, w, h)
        return x, y

    def _split(self, x, y, w, h):
        new_free = []
        for fr in self.free:
            fx, fy, fw, fh = fr
            if x >= fx + fw or x + w <= fx or y >= fy + fh or y + h <= fy:
                new_free.append(fr)
                continue
            if x > fx:
                new_free.append((fx, fy, x - fx, fh))
            if x + w < fx + fw:
                new_free.append((x + w, fy, fx + fw - (x + w), fh))
            if y > fy:
                new_free.append((fx, fy, fw, y - fy))
            if y + h < fy + fh:
                new_free.append((fx, y + h, fw, fy + fh - (y + h)))
        # 포함된 사각형 제거
        new_free = [r for r in new_free if r[2] > 0 and r[3] > 0]
        pruned = []
        for i, a in enumerate(new_free):
            contained = False
            for j, b in enumerate(new_free):
                if i != j and a[0] >= b[0] and a[1] >= b[1] and a[0] + a[2] <= b[0] + b[2] and a[1] + a[3] <= b[1] + b[3]:
                    if a != b or i > j:
                        contained = True
                        break
            if not contained:
                pruned.append(a)
        self.free = pruned


def pack(rects, bin_w, bin_h, pad):
    """rects: [(id, w, h)] → (placements {id:(x,y)}, used_w, used_h, leftovers[])
    패딩은 오른쪽·아래에 pad 만큼 띄운다(경계 bin 은 +pad 로 보정)."""
    mr = MaxRects(bin_w + pad, bin_h + pad)
    place, left = {}, []
    uw = uh = 0
    for rid, w, h in rects:
        p = mr.insert(w + pad, h + pad)
        if p is None:
            left.append((rid, w, h))
            continue
        place[rid] = p
        uw = max(uw, p[0] + w)
        uh = max(uh, p[1] + h)
    return place, uw, uh, left


def best_pack(rects, max_side, pad):
    """한 장에 다 들어가는 가장 작은 면적 배치를 찾는다. 못 넣으면 None."""
    if not rects:
        return None
    maxw = max(r[1] for r in rects)
    area = sum((r[1] + pad) * (r[2] + pad) for r in rects)
    base = math.sqrt(area)
    cands = {min(max_side, max(maxw, int(base * f))) for f in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.4, 1.6, 2.0, 2.5, 3.0)}
    cands.add(maxw)
    cands.add(max_side)
    orders = [
        sorted(rects, key=lambda r: (-max(r[1], r[2]), -r[1] * r[2])),
        sorted(rects, key=lambda r: (-r[2], -r[1])),
        sorted(rects, key=lambda r: (-r[1] * r[2])),
    ]
    best = None
    for bw in sorted(cands):
        for order in orders:
            place, uw, uh, left = pack(order, bw, max_side, pad)
            if left:
                continue
            key = (uw * uh, max(uw, uh))
            if best is None or key < best[0]:
                best = (key, place, uw, uh)
    if best is None:
        return None
    return best[1], best[2], best[3]


def multi_pack(rects, max_side, pad):
    """여러 장으로 나눈다: 큰 것부터 4096 bin 을 채우고, 각 장은 다시 최소 면적으로 재배치."""
    order = sorted(rects, key=lambda r: (-r[1] * r[2]))
    pages = []
    remaining = order
    while remaining:
        place, _, _, left = pack(remaining, max_side, max_side, pad)
        if not place:
            raise RuntimeError("프레임 하나가 최대 텍스처보다 큽니다: %r" % (remaining[0],))
        subset = [r for r in remaining if r[0] in place]
        res = best_pack(subset, max_side, pad)
        if res is None:
            res = (place, max(place[r[0]][0] + r[1] for r in subset), max(place[r[0]][1] + r[2] for r in subset))
        pages.append((subset, res))
        remaining = left
    return pages


# ---------------------------------------------------------------- 변환
def normalize(im: Image.Image) -> Image.Image:
    """알파 0 픽셀의 RGB 를 0 으로."""
    im = im.convert("RGBA")
    a = im.getchannel("A")
    mask = a.point(lambda v: 255 if v == 0 else 0)
    blank = Image.new("RGBA", im.size, (0, 0, 0, 0))
    im.paste(blank, (0, 0), mask)
    return im


def save_png(im: Image.Image, path: str):
    """무손실: RGBA 고유색 ≤256 이면 팔레트 PNG(tRNS) 시도, 더 작은 쪽 저장."""
    im.save(path, optimize=True)
    size_rgba = os.path.getsize(path)
    colors = im.getcolors(256)
    if colors is None:
        return
    pal_colors = [c for _, c in colors]
    # 투명(0,0,0,0)을 0번에
    pal_colors.sort(key=lambda c: (c[3] != 0, c))
    idx = {c: i for i, c in enumerate(pal_colors)}
    p = Image.new("P", im.size)
    flat = []
    for c in pal_colors:
        flat.extend(c[:3])
    p.putpalette(flat + [0] * (768 - len(flat)))
    bidx = {bytes(c): i for c, i in idx.items()}
    raw = im.tobytes()
    p.frombytes(bytes(bidx[raw[j:j + 4]] for j in range(0, len(raw), 4)))
    tmp = path + ".p.png"
    p.save(tmp, optimize=True, transparency=bytes(c[3] for c in pal_colors))
    # 왕복 확인 후 더 작으면 채택
    back = Image.open(tmp).convert("RGBA")
    if os.path.getsize(tmp) < size_rgba and back.tobytes() == im.tobytes():
        os.replace(tmp, path)
    else:
        os.remove(tmp)


def dump_json(out) -> str:
    """기존 메타는 들여쓰기 그대로, 프레임 항목은 한 줄씩(용량 절약)."""
    compact = lambda v: json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    lines = ["{"]
    keys = list(out.keys())
    for n, k in enumerate(keys):
        v = out[k]
        tail = "," if n < len(keys) - 1 else ""
        if k == "frames" and isinstance(v, dict):
            items = list(v.items())
            body = ",\n".join(f"  {json.dumps(fk)}:{compact(fv)}" for fk, fv in items)
            lines.append(f" \"frames\": {{\n{body}\n }}{tail}")
        elif k == "textures":
            parts = []
            for t in v:
                head = {kk: vv for kk, vv in t.items() if kk != "frames"}
                fr = ",\n".join(f"    {compact(e)}" for e in t["frames"])
                parts.append("  " + compact(head)[:-1] + f',"frames":[\n{fr}\n  ]}}')
            lines.append(" \"textures\": [\n" + ",\n".join(parts) + f"\n ]{tail}")
        else:
            body = json.dumps(v, ensure_ascii=False, indent=1).replace("\n", "\n ")
            lines.append(f" {json.dumps(k, ensure_ascii=False)}: {body}{tail}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def convert_sheet(png_path, json_path, out_dir, pad, max_side, dedup):
    meta = json.load(open(json_path, encoding="utf-8"))
    sheet = normalize(Image.open(png_path))
    fw, fh = int(meta["frameWidth"]), int(meta["frameHeight"])
    cols, rows = sheet.width // fw, sheet.height // fh
    name = os.path.splitext(os.path.basename(png_path))[0]
    # 반복(TileSprite)·리본(늘이기) 시트는 프레임 경계가 의미를 가지므로 트림하지 않는다(빽빽한 배치만)
    no_trim = meta.get("tile") is True or "ribbon" in meta

    frames = {}  # idx -> dict(trim box, key)
    uniq = {}    # key -> (img, w, h)
    empty = []
    dup_count = 0
    for r in range(rows):
        for c in range(cols):
            i = r * cols + c
            crop = sheet.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))
            bbox = crop.getchannel("A").getbbox()
            if no_trim:
                bbox = (0, 0, fw, fh)
            if bbox is None:
                empty.append(i)
                frames[i] = {"key": "__empty__", "sss": (0, 0, 1, 1)}
                continue
            t = crop.crop(bbox)
            if dedup:
                key = hashlib.sha1(t.tobytes() + bytes(str(t.size), "ascii")).hexdigest()
            else:
                key = "f%d" % i
            if key in uniq:
                dup_count += 1
            else:
                uniq[key] = t
            frames[i] = {"key": key, "sss": (bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1])}
    if empty:
        uniq["__empty__"] = Image.new("RGBA", (1, 1), (0, 0, 0, 0))

    rects = [(k, im.width, im.height) for k, im in uniq.items()]
    single = best_pack(rects, max_side, pad)
    pages = [(rects, single)] if single else multi_pack(rects, max_side, pad)

    os.makedirs(out_dir, exist_ok=True)
    page_info = []  # (image name, w, h, {key:(x,y)})
    for pi, (subset, (place, uw, uh)) in enumerate(pages):
        img_name = f"{name}.png" if len(pages) == 1 else f"{name}_{pi}.png"
        atlas = Image.new("RGBA", (max(uw, 1), max(uh, 1)), (0, 0, 0, 0))
        for k, w, h in subset:
            atlas.paste(uniq[k], place[k])
        save_png(atlas, os.path.join(out_dir, img_name))
        page_info.append((img_name, atlas.width, atlas.height, place))

    def frame_entry(i, x, y):
        f = frames[i]
        im = uniq[f["key"]]
        sx, sy, sw, sh = f["sss"]
        return {
            "frame": {"x": x, "y": y, "w": im.width, "h": im.height},
            "rotated": False,
            "trimmed": not no_trim,
            "spriteSourceSize": {"x": sx, "y": sy, "w": sw, "h": sh},
            "sourceSize": {"w": fw, "h": fh},
        }

    out = {}
    for k, v in meta.items():
        if k == "frames":
            out["framesPerDirection"] = v
        else:
            out[k] = v
    atlas_block = {
        "version": ATLAS_VERSION,
        "format": "phaser-json-hash" if len(page_info) == 1 else "phaser-multiatlas",
        "source": f"parts/art/work/atlas57/build.py (원 격자 시트 {name}.png)",
        "grid": {"columns": cols, "rows": rows, "frameWidth": fw, "frameHeight": fh, "frameCount": cols * rows},
        "frameName": "row * columns + column (정수 문자열) — 기존 격자 프레임 번호와 같다",
        "trim": "알파>0 경계 상자. spriteSourceSize = 원 프레임 안 위치, sourceSize = 원 프레임 크기. pivot·앵커는 원 프레임 좌표 그대로",
        "padding": pad,
        "noTrim": no_trim,
        "emptyFrames": empty,
        "dedupedFrames": dup_count,
        "pages": len(page_info),
    }
    out["atlas"] = atlas_block

    if len(page_info) == 1:
        img_name, aw, ah, place = page_info[0]
        out["image"] = img_name
        out["frames"] = {str(i): frame_entry(i, *place[frames[i]["key"]]) for i in sorted(frames)}
        out["meta"] = {"app": "LOPAD atlas57 (Pillow)", "version": ATLAS_VERSION, "image": img_name,
                       "format": "RGBA8888", "size": {"w": aw, "h": ah}, "scale": "1"}
    else:
        out["image"] = None
        textures = []
        for img_name, aw, ah, place in page_info:
            fl = []
            for i in sorted(frames):
                k = frames[i]["key"]
                if k in place:
                    e = frame_entry(i, *place[k])
                    fl.append({"filename": str(i), **e})
            textures.append({"image": img_name, "format": "RGBA8888", "size": {"w": aw, "h": ah}, "scale": 1, "frames": fl})
        out["textures"] = textures
        out["meta"] = {"app": "LOPAD atlas57 (Pillow)", "version": ATLAS_VERSION}

    with open(os.path.join(out_dir, f"{name}.json"), "w", encoding="utf-8") as f:
        f.write(dump_json(out))

    before_bytes = sheet.width * sheet.height * 4
    after_bytes = sum(w * h * 4 for _, w, h, _ in page_info)
    return {
        "name": name,
        "src": os.path.relpath(png_path, ROOT),
        "srcSize": [sheet.width, sheet.height],
        "frames": cols * rows,
        "empty": len(empty),
        "deduped": dup_count,
        "pages": [[n, w, h] for n, w, h, _ in page_info],
        "gpuBefore": before_bytes,
        "gpuAfter": after_bytes,
        "fileBefore": os.path.getsize(png_path),
        "fileAfter": sum(os.path.getsize(os.path.join(out_dir, n)) for n, _, _, _ in page_info),
        "jsonBefore": os.path.getsize(json_path),
        "jsonAfter": os.path.getsize(os.path.join(out_dir, f"{name}.json")),
    }


def sheet_state(json_path) -> str:
    """'grid' = 격자(변환 대상) / 'atlas' = 변환 끝 / 'mixed' = JSON 과 PNG 가 어긋남(옛 스크립트가 아틀라스 JSON 을
    읽어 격자 PNG 와 함께 다시 쓴 경우 등 — 변환하지 않고 오류로 알린다)."""
    m = json.load(open(json_path, encoding="utf-8"))
    if "atlas" not in m and not isinstance(m.get("frames"), dict) and "framesPerDirection" not in m:
        return "grid"
    if "atlas" not in m or not isinstance(m.get("frames", m.get("textures")), (dict, list)):
        return "mixed"
    pages = [(t["image"], t["size"]) for t in m["textures"]] if "textures" in m else [(m["meta"]["image"], m["meta"]["size"])]
    d = os.path.dirname(json_path)
    for img, size in pages:
        p = os.path.join(d, img)
        if not os.path.exists(p) or Image.open(p).size != (size["w"], size["h"]):
            return "mixed"
    return "atlas"


def apply_in_place(res, tmp_dir, dst_dir, png_path, json_path, max_side):
    """스테이징(tmp_dir) 결과를 전 프레임 대조한 뒤 assets 로 옮긴다. 불일치면 예외(원본 그대로)."""
    import verify  # 같은 폴더
    name = res["name"]
    meta = json.load(open(json_path, encoding="utf-8"))
    atlas = json.load(open(os.path.join(tmp_dir, name + ".json"), encoding="utf-8"))
    errs = verify.check_format(meta, atlas, max_side)
    sheet = Image.open(png_path).convert("RGBA")
    bad = verify.compare_sheet(sheet, meta, atlas, tmp_dir)
    if errs or bad:
        raise RuntimeError(f"{name}: 형식 오류 {errs[:3]} / 픽셀 불일치 {bad}프레임 — assets 는 바꾸지 않았다")
    pages = [n for n, _, _ in res["pages"]]
    if name + ".png" not in pages:
        os.remove(png_path)  # 멀티 아틀라스: <이름>_<i>.png 로 대체
    for n in pages:
        shutil.move(os.path.join(tmp_dir, n), os.path.join(dst_dir, n))
    shutil.move(os.path.join(tmp_dir, name + ".json"), json_path)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cats", default=CATS)
    ap.add_argument("--only", default="")
    ap.add_argument("--pad", type=int, default=2)
    ap.add_argument("--max", type=int, default=4096)
    ap.add_argument("--no-dedup", action="store_true")
    ap.add_argument("--out", default=OUT, help="출력 루트(기본 out/sprites, --in-place 면 무시)")
    ap.add_argument("--in-place", action="store_true", help="assets/sprites 를 직접 교체(전 프레임 대조 통과 시)")
    args = ap.parse_args()

    results, skipped, mixed = [], 0, []
    tmp_root = os.path.join(HERE, "out", "_inplace_tmp")
    for cat in args.cats.split(","):
        src_dir = os.path.join(SRC, cat, "v3")
        out_dir = os.path.join(tmp_root if args.in_place else args.out, cat, "v3")
        for jp in sorted(glob(os.path.join(src_dir, "*.json"))):
            pp = jp[:-5] + ".png"
            if args.only and args.only not in os.path.basename(jp):
                continue
            state = sheet_state(jp)
            if state == "atlas":
                skipped += 1  # 이미 아틀라스(재변환하지 않는다)
                continue
            if state == "mixed":
                mixed.append(os.path.relpath(jp, ROOT))
                continue
            if not os.path.exists(pp):
                print("PNG 없음, 건너뜀:", jp)
                continue
            res = convert_sheet(pp, jp, out_dir, args.pad, args.max, not args.no_dedup)
            res["cat"] = cat
            if args.in_place:
                apply_in_place(res, out_dir, src_dir, pp, jp, args.max)
            results.append(res)
            print(f"{cat}/{res['name']}: {res['srcSize'][0]}x{res['srcSize'][1]} -> "
                  + ", ".join(f"{w}x{h}" for _, w, h in res["pages"])
                  + f"  GPU {res['gpuBefore']/2**20:.1f}->{res['gpuAfter']/2**20:.2f}MB"
                  + (f"  빈{res['empty']}" if res["empty"] else "")
                  + (f"  중복{res['deduped']}" if res["deduped"] else "")
                  + ("  [assets 교체]" if args.in_place else ""))
    if args.in_place:
        shutil.rmtree(tmp_root, ignore_errors=True)
    if skipped:
        print(f"이미 아틀라스라 건너뜀: {skipped}개")
    if mixed:
        print("오류 — JSON·PNG 형식이 어긋나 변환하지 않음(격자 JSON 을 다시 만들고 재실행):", ", ".join(mixed))
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    rp = os.path.join(HERE, "out", "report.json")
    if results and (args.in_place or (not args.only and os.path.abspath(args.out) == os.path.abspath(OUT))):
        # 변환 기록은 누적한다(분류/이름 기준 덮어쓰기) — 이미 아틀라스가 된 시트의 '전' 수치를 잃지 않게
        old = json.load(open(rp, encoding="utf-8")) if os.path.exists(rp) else {"sheets": []}
        keep = {(r["cat"], r["name"]): r for r in old.get("sheets", [])}
        for r in results:
            keep[(r["cat"], r["name"])] = r
        with open(rp, "w", encoding="utf-8") as f:
            json.dump({"version": ATLAS_VERSION, "pad": args.pad, "max": args.max, "sheets": list(keep.values())},
                      f, ensure_ascii=False, indent=1)
    summarize(results)


def summarize(results):
    cats = {}
    for r in results:
        c = cats.setdefault(r["cat"], [0, 0, 0, 0, 0, 0, 0])
        c[0] += 1
        c[1] += r["gpuBefore"]; c[2] += r["gpuAfter"]
        c[3] += r["fileBefore"]; c[4] += r["fileAfter"]
        c[5] += r["jsonBefore"]; c[6] += r["jsonAfter"]
    tot = [0] * 7
    print("\n| 분류 | 시트 | GPU 전(MB) | GPU 후(MB) | PNG 전(MB) | PNG 후(MB) | JSON 전(KB) | JSON 후(KB) |")
    print("|---|---|---|---|---|---|---|---|")
    for k, c in list(cats.items()) + [("합계", None)]:
        if c is None:
            c = tot
        else:
            tot = [a + b for a, b in zip(tot, c)]
        print(f"| {k} | {c[0]} | {c[1]/2**20:.1f} | {c[2]/2**20:.1f} | {c[3]/1e6:.2f} | {c[4]/1e6:.2f} | {c[5]/1e3:.0f} | {c[6]/1e3:.0f} |")
    multi = [r for r in results if len(r["pages"]) > 1]
    if multi:
        print("\n멀티 아틀라스:", ", ".join(f"{r['cat']}/{r['name']}({len(r['pages'])}장)" for r in multi))


if __name__ == "__main__":
    raise SystemExit(main())
