"""57라운드 Q38 이후 assets/sprites/**/v3 는 트림 아틀라스다. 옛 빌드·미리보기 스크립트처럼
'격자 시트(행·열 칸)'가 필요한 곳에서 쓰는 되돌리기 도구 (Pillow 만).

    import sys; sys.path.insert(0, "<저장소>/parts/art/work/atlas57")
    import gridsheet
    meta = gridsheet.load_meta(json_path)   # 격자 형식 메타(frames = 방향당 프레임 수 정수, atlas 블록 없음)
    im = gridsheet.open_grid(png_or_json)    # 격자 RGBA 시트(칸 = frameWidth×frameHeight, row*columns+column 순)

둘 다 아직 격자인 시트(JSON 에 atlas 블록 없음)는 그대로 읽는다.

명령행: python3 gridsheet.py unpack <assets 기준 경로 또는 이름 일부> [--out 폴더]
        → 격자 PNG + 격자 JSON 을 --out(기본 out/grid/<분류>/v3/)에 되살린다(미리보기·비교용, assets 에 다시 넣지 말 것).
"""
from __future__ import annotations

import argparse
import json
import os
from glob import glob

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
SPR = os.path.join(ROOT, "assets", "sprites")


def _paths(p):
    base = p[:-5] if p.endswith(".json") else p[:-4] if p.endswith(".png") else p
    return base + ".json", base + ".png"


def load_meta(path):
    jp, _ = _paths(path)
    m = json.load(open(jp, encoding="utf-8"))
    if "atlas" not in m:
        return m
    out = {}
    for k, v in m.items():
        if k in ("atlas", "meta", "textures"):
            continue
        if k == "framesPerDirection":
            out["frames"] = v
        elif k != "frames":
            out[k] = v
    if out.get("image") is None:
        out["image"] = os.path.basename(_paths(path)[1])
    return out


def open_grid(path) -> Image.Image:
    jp, pp = _paths(path)
    m = json.load(open(jp, encoding="utf-8"))
    if "atlas" not in m:
        return Image.open(pp).convert("RGBA")
    g = m["atlas"]["grid"]
    fw, fh, cols = g["frameWidth"], g["frameHeight"], g["columns"]
    sheet = Image.new("RGBA", (cols * fw, g["rows"] * fh), (0, 0, 0, 0))
    d = os.path.dirname(jp)
    if "textures" in m:
        entries = [(t["image"], e["filename"], e) for t in m["textures"] for e in t["frames"]]
    else:
        entries = [(m["meta"]["image"], k, e) for k, e in m["frames"].items()]
    pages = {}
    for img, name, e in entries:
        if img not in pages:
            pages[img] = Image.open(os.path.join(d, img)).convert("RGBA")
        f, s = e["frame"], e["spriteSourceSize"]
        r, c = divmod(int(name), cols)
        crop = pages[img].crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"]))
        sheet.paste(crop, (c * fw + s["x"], r * fh + s["y"]))
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["unpack"])
    ap.add_argument("name", help="예: player/v3/player_idle 또는 이름 일부(player_idle)")
    ap.add_argument("--out", default=os.path.join(HERE, "out", "grid"))
    args = ap.parse_args()
    cand = os.path.join(SPR, args.name)
    hits = [cand + ".json"] if os.path.exists(cand + ".json") else sorted(glob(os.path.join(SPR, "*", "v3", f"*{args.name}*.json")))
    for jp in hits:
        rel = os.path.relpath(jp, SPR)
        od = os.path.join(args.out, os.path.dirname(rel))
        os.makedirs(od, exist_ok=True)
        meta = load_meta(jp)
        open_grid(jp).save(os.path.join(od, os.path.basename(jp)[:-5] + ".png"), optimize=True)
        with open(os.path.join(od, os.path.basename(jp)), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        print("되살림:", os.path.relpath(os.path.join(od, os.path.basename(jp)), ROOT))


if __name__ == "__main__":
    main()
