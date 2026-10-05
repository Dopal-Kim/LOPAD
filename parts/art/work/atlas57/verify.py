"""57라운드 아틀라스·외벽 WebP 검증 — 원 격자 시트/원 PNG 와 픽셀 비교 + 형식 점검.

스프라이트 (기본):
1) 무작위 프레임 N개(기본 20, 시드 57)를 아틀라스에서 복원해(sourceSize 투명 캔버스에 spriteSourceSize 위치로 붙임)
   원 격자 프레임과 RGBA 비교. 알파 0 픽셀은 RGB 무시(같은 것으로 본다).
2) --all 이면 모든 시트·모든 프레임을 같은 방식으로 비교.
3) 형식: 기존 메타 필드 보존(frames→framesPerDirection), 프레임 이름 0..N-1 전부, 텍스처 ≤ max,
   frame 사각형이 텍스처 안, 서로 다른 frame 사각형끼리 겹치지 않음, sourceSize = frameWidth/Height.
   --root 아래에 아직 격자(아틀라스 아님) 시트가 남아 있으면 형식 오류로 센다.

원본(격자 시트)은 assets 에서 지워졌으므로 git 에서 읽는다: --git-rev (기본 GRID_REV = 격자 시트가 남아 있던 마지막 커밋).
그 커밋에 없는(이후 새로 만든) 시트는 픽셀 대조 없이 형식만 본다 — 새 시트는 build.py --in-place 가 변환 때 전 프레임을 대조한다.
--src <폴더> 를 주면 git 대신 그 폴더(격자 시트 사본)를 원본으로 쓴다.

기준 갱신(60라운드): GRID_REV 뒤에 다시 그린 시트(58라운드 대검 3/4 대각 리그 등)와 새로 만든 시트는
baseline.json 의 `sheets{시트: 커밋}` 에 적힌 커밋의 **아틀라스**를 기준으로 삼는다(그 커밋의 아틀라스를 프레임별로
되살려 현재 아틀라스와 RGBA 대조, 메타 필드도 그 커밋 기준). baseline.json 에 없는 시트는 예전처럼 GRID_REV 격자와 대조
(GRID_REV 에도 없으면 형식만). 시트를 의도적으로 다시 그려 커밋했으면 기준을 옮긴다:
  python3 verify.py --rebase [--rev HEAD] [--only 이름부분 ...]
  --only 없이 돌리면 "현재 기준과 어긋나는 시트 + 기준이 없는 시트" 중 rev 에 커밋된 것만 자동으로 옮긴다
  (rev 의 파일과 작업 트리 파일이 다른 시트는 옮기지 않고 알린다 — 커밋 안 된 변경을 기준으로 삼지 않기 위함).

외벽 (--border): assets/tiles/border/<지역>/border.json 의 모든 그림 참조가 .webp 로 존재하는지, PNG 가 남지 않았는지,
   텍스처 ≤ max 인지, pieces[] 를 이어 붙인 그림이 원 PNG 와 같은지(albedo: 알파 오차 0·PSNR ≥ --psnr, 발광·알파: 무손실 0 차이).

사용: python3 verify.py [--root assets/sprites] [--all] [--n 20] [--seed 57] [--git-rev 5bfcf2e | --src 폴더] [--border] [--max 4096]
      python3 verify.py --rebase [--rev HEAD] [--only 이름부분 ...]   (기준 갱신 → baseline.json)
"""
from __future__ import annotations

import argparse
import io
import json
import math
import os
import random
import subprocess
from glob import glob

from PIL import Image, ImageChops, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
SRC = os.path.join(ROOT, "assets", "sprites")
BORDER = os.path.join(ROOT, "assets", "tiles", "border")
GRID_REV = "5bfcf2e"  # 격자 시트·외벽 PNG 가 assets 에 남아 있던 마지막 커밋(57라운드 Q38 교체 직전)
BASELINE = os.path.join(HERE, "baseline.json")  # 시트별 아틀라스 기준 커밋(60라운드 기준 갱신)


def load_baseline():
    if not os.path.exists(BASELINE):
        return {}
    return json.load(open(BASELINE, encoding="utf-8")).get("sheets", {})


def git_bytes(rev, rel):
    r = subprocess.run(["git", "-C", ROOT, "show", f"{rev}:{rel}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


# ---------------------------------------------------------------- 원본 읽기
class Originals:
    """원본 파일을 폴더(--src) 또는 git 커밋(--git-rev)에서 읽는다. rel = 저장소 루트 기준 경로."""

    def __init__(self, src_dir=None, rev=None):
        self.src_dir, self.rev = src_dir, rev

    def read(self, rel):
        if self.src_dir:
            p = os.path.join(self.src_dir, os.path.relpath(rel, "assets/sprites"))
            return open(p, "rb").read() if os.path.exists(p) else None
        r = subprocess.run(["git", "-C", ROOT, "show", f"{self.rev}:{rel}"], capture_output=True)
        return r.stdout if r.returncode == 0 else None

    def json(self, rel):
        b = self.read(rel)
        return None if b is None else json.loads(b.decode("utf-8"))

    def image(self, rel):
        b = self.read(rel)
        return None if b is None else Image.open(io.BytesIO(b)).convert("RGBA")


# ---------------------------------------------------------------- 스프라이트
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


def rebuild(atlas_dir, image_name, e, cache, loader=None):
    if image_name not in cache:
        cache[image_name] = (loader(image_name) if loader else
                             Image.open(os.path.join(atlas_dir, image_name)).convert("RGBA"))
    a = cache[image_name]
    f, s, ss = e["frame"], e["spriteSourceSize"], e["sourceSize"]
    crop = a.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"]))
    canvas = Image.new("RGBA", (ss["w"], ss["h"]), (0, 0, 0, 0))
    canvas.paste(crop, (s["x"], s["y"]))
    return canvas


def grid_meta_of(atlas: dict) -> dict:
    """아틀라스 JSON 에서 원 격자 메타를 되돌린다(원본이 없을 때 형식 점검용)."""
    out = {}
    for k, v in atlas.items():
        if k in ("atlas", "meta", "textures"):
            continue
        if k == "framesPerDirection":
            out["frames"] = v
        elif k != "frames":
            out[k] = v
    return out


def check_format(src_meta, atlas, max_side):
    errs = []
    if "atlas" not in atlas:
        return ["아틀라스 아님(격자 그대로)"]
    for k, v in src_meta.items():
        if k == "frames":
            if atlas.get("framesPerDirection") != v:
                errs.append("framesPerDirection 불일치")
        elif k == "image":
            continue
        elif atlas.get(k) != v:
            errs.append(f"메타 필드 변경: {k}")
    if isinstance(atlas.get("framesPerDirection"), dict) or not isinstance(atlas.get("frames"), (dict, type(None))):
        errs.append("frames/framesPerDirection 형식")
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
        if atlas.get("image") != atlas["meta"]["image"]:
            errs.append("image 와 meta.image 불일치")
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


def compare_sheet(sheet, meta, atlas, atlas_dir, indices=None):
    """원 격자 시트(Image)와 아틀라스를 프레임별 비교 → 불일치 프레임 수."""
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    cols = sheet.width // fw
    table = frame_table(atlas)
    g = atlas["atlas"]["grid"]
    if indices is None:
        indices = range(g["columns"] * g["rows"])
    cache, bad = {}, 0
    for i in indices:
        r, c = divmod(i, cols)
        orig = sheet.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))
        img, e = table[str(i)]
        if norm_bytes(orig) != norm_bytes(rebuild(atlas_dir, img, e, cache)):
            bad += 1
    return bad


def compare_atlas(base, base_loader, atlas, atlas_dir, indices=None):
    """기준 아틀라스(커밋)와 현재 아틀라스를 프레임별 비교 → 불일치 프레임 수(격자 크기가 다르면 전부 불일치)."""
    gb, g = base["atlas"]["grid"], atlas["atlas"]["grid"]
    n = g["columns"] * g["rows"]
    if (gb["columns"], gb["rows"], gb["frameWidth"], gb["frameHeight"]) != (g["columns"], g["rows"], g["frameWidth"], g["frameHeight"]):
        return n if indices is None else len(indices)
    tb, tc = frame_table(base), frame_table(atlas)
    cb, cc, bad = {}, {}, 0
    for i in (range(n) if indices is None else indices):
        ib, eb = tb[str(i)]
        ic, ec = tc[str(i)]
        if norm_bytes(rebuild(None, ib, eb, cb, base_loader)) != norm_bytes(rebuild(atlas_dir, ic, ec, cc)):
            bad += 1
    return bad


def atlas_loader(rev, rel_dir):
    def load(name):
        b = git_bytes(rev, f"{rel_dir}/{name}")
        if b is None:
            raise FileNotFoundError(f"{rev}:{rel_dir}/{name}")
        return Image.open(io.BytesIO(b)).convert("RGBA")
    return load


def verify_sprites(args, orig):
    atlases = sorted(glob(os.path.join(args.root, "*", "v3", "*.json")) + glob(os.path.join(args.root, "*", "v4", "*.json")))  # 61 단계 4: v4(각성 외형) 포함
    pairs, fmt_errs, no_orig = [], 0, []
    based = load_baseline() if not args.src else {}
    apairs = []  # (rel, 현재 경로, 기준 커밋, 기준 아틀라스, 현재 아틀라스)
    for ap_ in atlases:
        rel = os.path.relpath(ap_, args.root)
        atlas = json.load(open(ap_, encoding="utf-8"))
        if rel in based:
            rev = based[rel]
            b = git_bytes(rev, f"assets/sprites/{rel}")
            base = json.loads(b.decode("utf-8")) if b else None
            if base is None or "atlas" not in base:
                errs = [f"기준 커밋 {rev} 에 아틀라스 없음"]
            elif "atlas" not in atlas:
                errs = ["아틀라스 아님(격자 그대로)"]
            else:
                errs = check_format(grid_meta_of(base), atlas, args.max)
                if base["atlas"]["grid"] != atlas["atlas"]["grid"]:
                    errs.append("격자(grid) 변경 — 다시 그렸으면 --rebase")
            if "atlas" in atlas and not errs:
                for img, size in ([(t["image"], t["size"]) for t in atlas["textures"]] if "textures" in atlas
                                  else [(atlas["meta"]["image"], atlas["meta"]["size"])]):
                    p = os.path.join(os.path.dirname(ap_), img)
                    if not os.path.exists(p) or Image.open(p).size != (size["w"], size["h"]):
                        errs.append(f"텍스처 파일 없음/크기 불일치 {img}")
            if errs:
                fmt_errs += len(errs)
                print("형식 오류", rel, errs[:5])
            else:
                apairs.append((rel, ap_, rev, base, atlas))
            continue
        src_meta = orig.json(f"assets/sprites/{rel}")
        if src_meta is not None and "atlas" in src_meta:
            src_meta = None  # 원본 커밋에서도 이미 아틀라스 → 픽셀 원본 없음
        if src_meta is None:
            no_orig.append(rel)
            errs = check_format(grid_meta_of(atlas), atlas, args.max) if "atlas" in atlas else ["아틀라스 아님(격자 그대로)"]
        else:
            errs = check_format(src_meta, atlas, args.max)
        if "atlas" in atlas and not errs:
            pages = ([(t["image"], t["size"]) for t in atlas["textures"]] if "textures" in atlas
                     else [(atlas["meta"]["image"], atlas["meta"]["size"])])
            for img, size in pages:
                p = os.path.join(os.path.dirname(ap_), img)
                if not os.path.exists(p) or Image.open(p).size != (size["w"], size["h"]):
                    errs.append(f"텍스처 파일 없음/크기 불일치 {img}")
        if errs:
            fmt_errs += len(errs)
            print("형식 오류", rel, errs[:5])
        if src_meta is not None and "atlas" in atlas:
            pairs.append((rel, ap_, src_meta, atlas))
    print(f"형식 점검: 시트 {len(atlases)}개, 오류 {fmt_errs}" + (f" (원본 없음 {len(no_orig)}개: 형식만)" if no_orig else "")
          + (f" (아틀라스 기준 {len(apairs)}개: baseline.json)" if based else ""))
    missing = (sorted(set(based) - {os.path.relpath(a, args.root) for a in atlases})
               if os.path.abspath(args.root) == SRC else [])  # 다른 --root(부분 사본)에서는 생략
    if missing:
        fmt_errs += len(missing)
        print(f"기준에 있는데 시트가 없음 {len(missing)}개: {missing[:5]}")

    jobs = {}
    if args.all:
        for p in pairs:
            g = p[3]["atlas"]["grid"]
            jobs[p[0]] = (p, list(range(g["columns"] * g["rows"])))
    else:
        rnd = random.Random(args.seed)
        for _ in range(min(args.n, 10 ** 9) if pairs else 0):
            p = rnd.choice(pairs)
            g = p[3]["atlas"]["grid"]
            jobs.setdefault(p[0], (p, []))[1].append(rnd.randrange(g["columns"] * g["rows"]))
    bad = total = 0
    bad_sheets = []
    for rel, ((_, ap_, meta, atlas), idx) in jobs.items():
        sheet = orig.image(f"assets/sprites/{rel[:-5]}.png")
        b = compare_sheet(sheet, meta, atlas, os.path.dirname(ap_), idx)
        total += len(idx)
        bad += b
        if b:
            bad_sheets.append(f"{rel}({b})")
        if not args.all:
            print(f"{'OK ' if not b else 'DIFF'} {rel[:-5]} #{','.join(map(str, idx))}")
    print(f"픽셀 비교(격자 {orig.rev or orig.src_dir}): 시트 {len(jobs)}개 {total}프레임 중 불일치 {bad}" + (f" — {', '.join(bad_sheets[:10])}" if bad_sheets else ""))

    if apairs:
        rnd = random.Random(args.seed + 1)
        abad = atotal = 0
        abad_sheets = []
        sel = {}
        if args.all:
            for p in apairs:
                sel[p[0]] = (p, None)
        else:
            for _ in range(args.n):
                p = rnd.choice(apairs)
                g = p[4]["atlas"]["grid"]
                sel.setdefault(p[0], (p, []))[1].append(rnd.randrange(g["columns"] * g["rows"]))
        for rel, ((_, ap_, rev, base, atlas), idx) in sel.items():
            g = atlas["atlas"]["grid"]
            n = g["columns"] * g["rows"] if idx is None else len(idx)
            b = compare_atlas(base, atlas_loader(rev, os.path.dirname(f"assets/sprites/{rel}")), atlas, os.path.dirname(ap_), idx)
            atotal += n
            abad += b
            if b:
                abad_sheets.append(f"{rel}({b})")
            if not args.all:
                print(f"{'OK ' if not b else 'DIFF'} {rel[:-5]} @{rev[:7]} #{','.join(map(str, idx))}")
        revs = sorted({p[2][:7] for p in apairs})
        print(f"픽셀 비교(아틀라스 기준 {','.join(revs)}): 시트 {len(sel)}개 {atotal}프레임 중 불일치 {abad}"
              + (f" — {', '.join(abad_sheets[:10])}" if abad_sheets else ""))
        bad += abad
    return bad, fmt_errs


def rebase(args, orig):
    """기준 갱신: 지정(또는 자동 선별) 시트의 기준을 rev 커밋의 아틀라스로 옮겨 baseline.json 에 쓴다."""
    rev = subprocess.run(["git", "-C", ROOT, "rev-parse", args.rev], capture_output=True, text=True, check=True).stdout.strip()
    data = json.load(open(BASELINE, encoding="utf-8")) if os.path.exists(BASELINE) else {}
    sheets = dict(data.get("sheets", {}))
    atlases = sorted(glob(os.path.join(args.root, "*", "v3", "*.json")) + glob(os.path.join(args.root, "*", "v4", "*.json")))  # 61 단계 4: v4(각성 외형) 포함
    moved, skipped = [], []
    for ap_ in atlases:
        rel = os.path.relpath(ap_, args.root)
        if args.only and not any(o in rel for o in args.only):
            continue
        relp = f"assets/sprites/{rel}"
        cur = json.load(open(ap_, encoding="utf-8"))
        bj = git_bytes(rev, relp)
        if bj is None or "atlas" not in cur:
            continue
        committed = json.loads(bj.decode("utf-8"))
        if "atlas" not in committed:
            continue
        pages = [t["image"] for t in cur["textures"]] if "textures" in cur else [cur["meta"]["image"]]
        dirty = committed != cur or any(
            git_bytes(rev, f"{os.path.dirname(relp)}/{img}") != open(os.path.join(os.path.dirname(ap_), img), "rb").read()
            for img in pages)
        if dirty:
            skipped.append(rel)
            continue
        if not args.only:
            if rel in sheets:
                if sheets[rel] == rev:
                    continue
                old = json.loads(git_bytes(sheets[rel], relp).decode("utf-8"))
                if (old.get("atlas", {}).get("grid") == cur["atlas"]["grid"] and
                        compare_atlas(old, atlas_loader(sheets[rel], os.path.dirname(relp)), cur, os.path.dirname(ap_)) == 0
                        and not check_format(grid_meta_of(old), cur, args.max)):
                    continue  # 기준과 같다 → 그대로
            else:
                src_meta = orig.json(relp)
                if src_meta is not None and "atlas" not in src_meta:
                    sheet = orig.image(relp[:-5] + ".png")
                    if not check_format(src_meta, cur, args.max) and compare_sheet(sheet, src_meta, cur, os.path.dirname(ap_)) == 0:
                        continue  # 격자 기준과 같다 → 격자 기준 유지
        sheets[rel] = rev
        moved.append(rel)
    data = {
        "_doc": "atlas57/verify.py 시트별 픽셀 기준. 여기 적힌 시트는 해당 커밋의 아틀라스와 대조, 없는 시트는 gridRev 격자와 대조. 갱신: verify.py --rebase",
        "gridRev": GRID_REV,
        "sheets": dict(sorted(sheets.items())),
    }
    with open(BASELINE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"기준 갱신 @{rev[:7]}: 옮김 {len(moved)}개, 커밋과 작업 트리가 달라 건너뜀 {len(skipped)}개, 기준 총 {len(sheets)}개")
    for r in moved[:20]:
        print("  옮김", r)
    for r in skipped[:20]:
        print("  건너뜀(미커밋 변경)", r)
    return 0


# ---------------------------------------------------------------- 외벽
def psnr_alpha(a: Image.Image, b: Image.Image):
    bg = Image.new("RGBA", a.size, (128, 128, 128, 255))
    d = ImageChops.difference(Image.alpha_composite(bg, a).convert("RGB"), Image.alpha_composite(bg, b).convert("RGB"))
    mse = sum(x * x for x in ImageStat.Stat(d).rms) / 3
    psnr = 99.0 if mse == 0 else 10 * math.log10(255 ** 2 / mse)
    aerr = ImageChops.difference(a.getchannel("A"), b.getchannel("A")).getextrema()[1]
    return psnr, aerr


def verify_border(args, orig):
    regions = sorted(d for d in glob(os.path.join(BORDER, "*")) if os.path.isdir(d))
    fmt, bad, n_img, psnr_min = 0, 0, 0, 99.0
    for rd in regions:
        region = os.path.basename(rd)
        bj = json.load(open(os.path.join(rd, "border.json"), encoding="utf-8"))
        old = orig.json(f"assets/tiles/border/{region}/border.json")
        errs = []
        if "imageFormat" not in bj:
            errs.append("imageFormat 없음(미변환)")
        left_png = [os.path.basename(p) for p in glob(os.path.join(rd, "*.png"))]
        if left_png:
            errs.append(f"PNG 남음 {left_png[:3]}")
        pscale = float(bj.get("pixelScale", 0.5))
        refs = set()

        def tex(name):
            refs.add(name)
            p = os.path.join(rd, name)
            if not name.endswith(".webp"):
                errs.append(f"webp 아님: {name}")
                return None
            if not os.path.exists(p):
                errs.append(f"파일 없음: {name}")
                return None
            im = Image.open(p)
            if max(im.size) > args.max:
                errs.append(f"텍스처 초과 {name} {im.size}")
            return im.convert("RGBA")

        def assemble(node, key):
            """띠 노드에서 key(image|emissive) 그림을 한 장으로(원 px)."""
            if "pieces" in node:
                ims = [(tex(pc[key]), pc) for pc in node["pieces"] if key in pc]
                if not ims or any(im is None for im, _ in ims):
                    return None
                W = round(node["width"] / pscale)
                H = round(node["height"] / pscale)
                canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                covered = 0
                for im, pc in ims:
                    if (round(pc["width"] / pscale), round(pc["height"] / pscale)) != im.size:
                        errs.append(f"조각 크기 불일치 {pc[key]}")
                    canvas.paste(im, (round(pc["x"] / pscale), round(pc["y"] / pscale)))
                    covered += im.width * im.height
                if covered != W * H:
                    errs.append(f"조각 면적 {covered} != 띠 {W * H}")
                return canvas
            return tex(node[key]) if key in node else None

        def compare(new_im, old_name, lossless):
            nonlocal bad, n_img, psnr_min
            if old_name is None or new_im is None:
                return
            o = orig.image(f"assets/tiles/border/{region}/{old_name}")
            if o is None:
                return
            n_img += 1
            if o.size != new_im.size:
                bad += 1
                errs.append(f"크기 불일치 {old_name} {o.size} vs {new_im.size}")
                return
            if lossless:
                if norm_bytes(o) != norm_bytes(new_im):
                    bad += 1
                    errs.append(f"무손실 불일치 {old_name}")
                return
            p, aerr = psnr_alpha(o, new_im)
            psnr_min = min(psnr_min, p)
            if aerr or p < args.psnr:
                bad += 1
                errs.append(f"{old_name}: PSNR {p:.1f} 알파오차 {aerr}")

        def walk(n_new, n_old):
            if isinstance(n_new, dict) and isinstance(n_old, dict):
                if "image" in n_old and isinstance(n_old["image"], str):
                    compare(assemble(n_new, "image"), n_old["image"], False)
                    if "emissive" in n_old:
                        compare(assemble(n_new, "emissive"), n_old["emissive"], True)
                if "file" in n_old and isinstance(n_old["file"], str):
                    compare(tex(n_new["file"]), n_old["file"], False)
                    if "emissive" in n_old:
                        compare(tex(n_new["emissive"]), n_old["emissive"], True)
                if "mirrorOf" in n_old:
                    if n_new.get("mirrorOf") != n_old["mirrorOf"][:-4] + ".webp":
                        errs.append("mirrorOf 불일치")
                    else:
                        tex(n_new["mirrorOf"])
                for k, v in n_old.items():
                    if k in n_new and isinstance(v, (dict, list)):
                        walk(n_new[k], v)
            elif isinstance(n_new, list) and isinstance(n_old, list):
                for a, b in zip(n_new, n_old):
                    walk(a, b)

        if old is None or "imageFormat" in old:
            errs.append("원본 border.json 없음(픽셀 대조 생략)")
        else:
            walk(bj.get("bands", {}), old.get("bands", {}))
            walk(bj.get("doors", {}), old.get("doors", {}))
        unused = sorted({os.path.basename(p) for p in glob(os.path.join(rd, "*.webp"))} - refs)
        if unused:
            errs.append(f"참조 없는 webp {unused[:3]}")
        fmt += len(errs)
        print(f"외벽 {region}: 그림 {len(refs)}개 " + ("OK" if not errs else f"오류 {errs[:6]}"))
    print(f"외벽 점검: 지역 {len(regions)}개, 원본 대조 {n_img}장, 불일치 {bad}, 오류 {fmt}, albedo PSNR 최저 {psnr_min:.1f}dB")
    return bad, fmt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=SRC)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=57)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--max", type=int, default=4096)
    ap.add_argument("--git-rev", default=GRID_REV)
    ap.add_argument("--src", default=None, help="원 격자 시트 폴더(주면 git 대신 사용)")
    ap.add_argument("--border", action="store_true", help="외벽 WebP 점검도 한다")
    ap.add_argument("--psnr", type=float, default=38.0)
    ap.add_argument("--rebase", action="store_true", help="기준 갱신(baseline.json)")
    ap.add_argument("--rev", default="HEAD", help="--rebase 기준 커밋")
    ap.add_argument("--only", nargs="*", default=None, help="--rebase 대상 시트 이름 부분")
    args = ap.parse_args()

    orig = Originals(args.src, None if args.src else args.git_rev)
    if args.rebase:
        return rebase(args, orig)
    bad, fmt = verify_sprites(args, orig)
    if args.border:
        b2, f2 = verify_border(args, orig)
        bad, fmt = bad + b2, fmt + f2
    return 1 if (bad or fmt) else 0


if __name__ == "__main__":
    raise SystemExit(main())
