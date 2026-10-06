"""전/후 비교 그림 — preview_<weapon>.png.

줄마다 시트 하나: 왼쪽 = 전(git 기준 커밋), 오른쪽 = 후(작업 트리). 바닥 = 1층 연회장 바닥 타일(어둠 0.5),
오른쪽 절반에 1층 호박 등불 빛(램프와 섞일 때 무기 색이 앞에 서는지 보려고). 1배 = 1080p 렌더 실제 크기.
아래쪽: looks(무기 정지 그림 — base · a1 · a2 · a2_<길> 2) 2배, 카드 그림 1배·2배.

사용: python3 parts/art/work/color61s6_gb/preview.py [--rev a2def0f] [--weapon greatsword bow]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
SPR = os.path.join(ROOT, "assets", "sprites")
sys.path.insert(0, os.path.join(ROOT, "parts", "art", "work", "atlas57"))
import gridsheet  # noqa: E402

REV = "a2def0f"   # 61 단계 6 시작 커밋(색 바꾸기 전)

SHEETS = {
    "greatsword": [
        ("fx/v3/greatsword_sweep_cw", [2, 3, 4]), ("fx/v3/greatsword_combo1", [2, 3, 5]), ("fx/v3/greatsword_cleave", [2, 3, 4]),
        ("fx/v3/hit_greatsword", [0, 1, 2]), ("fx/v3/hit_greatsword_heavy", [0, 1, 3]), ("fx/v3/greatsword_ground_crack", [0, 1, 4]),
        ("fx/v3/greatsword_charge_flash_lv3", [0, 1, 2]), ("fx/v3/greatsword_leap_slam_land", [0, 2, 4]),
        ("fx/v3/trait_greatsword_g_quakeGuard", [1, 3, 5]), ("fx/v3/trait_greatsword_jarCrush_burst", [1, 3, 5]),
        ("fx/v3/trait_res_greatsword_weight_on", [1, 2, 4]), ("weapons/v3/greatsword_sweep_cw_grudge3", [2, 3, 4]),
        ("weapons/v3/greatsword_sweep_cw_awaken", [2, 3, 4]),
    ],
    "bow": [
        ("fx/v3/bow_arrow", [0, 1, 2]), ("fx/v3/bow_arrow_aimed", [0]), ("fx/v3/bow_arrow_snipe_lv3", [0]),
        ("fx/v3/hit_bow", [0, 1, 2]), ("fx/v3/hit_bow_heavy", [0, 1, 2]), ("fx/v3/bow_perfect_release", [0, 1, 2]),
        ("fx/v3/bow_arrow_rain_fall", [2, 4, 5]), ("fx/v3/bow_arrow_rain_mark", [0, 3, 6]), ("fx/v3/bow_arrow_awaken", [0, 1]),
        ("fx/v3/bow_meteor_arrow", [1, 4, 6]), ("fx/v3/bow_awaken_in", [3, 5, 7]),
        ("fx/v3/trait_bow_b_scatterVolley", [1, 2, 3]), ("fx/v3/trait_bow_b_starWell", [1, 3, 5]),
        ("fx/v3/trait_res_bow_breach_on", [1, 2, 4]), ("weapons/v3/bow_release_awaken", [0, 2]),
    ],
}


def floor(w, h, lamp=True):
    ts = Image.open(os.path.join(ROOT, "assets", "tiles", "v2", "stage1_hall.png")).convert("RGBA")
    tiles = [ts.crop((i * 64, 0, i * 64 + 64, 64)) for i in range(4)]
    bg = Image.new("RGBA", (w, h))
    for y in range(0, h, 64):
        for x in range(0, w, 64):
            bg.paste(tiles[((x // 64) * 7 + (y // 64) * 3) % 4], (x, y))
    px = bg.load()
    cx, cy, rad = w * 0.82, h * 0.5, max(80, h * 0.9)
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            k = 0.5
            add = 0.0
            if lamp:
                d = math.hypot(x - cx, y - cy) / rad
                if d < 1:
                    add = (1 - d) ** 1.6
            # 1층 등불 = 호박 빛(#d67a11 쪽) 더하기
            px[x, y] = (min(255, int(r * (k + 0.5 * add) + 70 * add)), min(255, int(g * (k + 0.3 * add) + 34 * add)),
                        min(255, int(b * k + 4 * add)), 255)
    return bg


def load(name, rev=None):
    if rev is None:
        jp = os.path.join(SPR, name + ".json")
        return gridsheet.load_meta(jp), gridsheet.open_grid(jp)
    tmp = tempfile.mkdtemp(prefix="c61gb_")
    rel = f"assets/sprites/{name}.json"
    jb = subprocess.run(["git", "-C", ROOT, "show", f"{rev}:{rel}"], capture_output=True).stdout
    m = json.loads(jb)
    jp = os.path.join(tmp, os.path.basename(rel))
    open(jp, "wb").write(jb)
    imgs = [t["image"] for t in m["textures"]] if "textures" in m else [m["meta"]["image"]]
    for im in imgs:
        b = subprocess.run(["git", "-C", ROOT, "show", f"{rev}:assets/sprites/{os.path.dirname(name)}/{im}"], capture_output=True).stdout
        open(os.path.join(tmp, im), "wb").write(b)
    return gridsheet.load_meta(jp), gridsheet.open_grid(jp)


def frames(meta, grid, idx):
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    cols = grid.width // fw
    out = []
    for i in idx:
        r, c = divmod(i, cols)
        if r * fh < grid.height:
            out.append(grid.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)))
    # 빈 둘레 잘라 붙이기(모든 칸 공통 상자)
    box = None
    for f in out:
        b = f.getbbox()
        if b:
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    if box is None:
        return out
    box = (max(0, box[0] - 6), max(0, box[1] - 6), min(fw, box[2] + 6), min(fh, box[3] + 6))
    return [f.crop(box) for f in out]


def strip(fr, scale):
    w = sum(f.width for f in fr) + 4 * (len(fr) - 1)
    h = max(f.height for f in fr)
    bg = floor(w, h)
    x = 0
    for f in fr:
        bg.alpha_composite(f, (x, (h - f.height) // 2))
        x += f.width + 4
    if scale != 1:
        bg = bg.resize((bg.width * scale, bg.height * scale), Image.NEAREST)
    return bg


def stack(rows, gap=6, bgc=(16, 14, 12, 255)):
    W = max(r.width for r in rows)
    H = sum(r.height for r in rows) + gap * (len(rows) - 1)
    im = Image.new("RGBA", (W, H), bgc)
    y = 0
    for r in rows:
        im.paste(r, (0, y))
        y += r.height + gap
    return im


def label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 7 * len(text) + 4, 12), fill=(0, 0, 0, 200))
    d.text((2, 0), text, fill=(230, 230, 230, 255))
    return im


def git_png(path, rev):
    b = subprocess.run(["git", "-C", ROOT, "show", f"{rev}:{path}"], capture_output=True).stdout
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.write(b)
    tmp.close()
    return Image.open(tmp.name).convert("RGBA")


def looks_rows(weapon, rev):
    meta = json.load(open(os.path.join(SPR, "looks", weapon + ".json"), encoding="utf-8"))
    rows = []
    for bid, br in meta["branches"].items():
        names = [meta["base"], br["a1"], br["a2"]] + list(br["a2ByPath"].values())
        pair = []
        for side in (rev, None):
            ims = [git_png(f"assets/sprites/looks/{n}", rev) if side else Image.open(os.path.join(SPR, "looks", n)).convert("RGBA") for n in names]
            pair.append(strip([i.crop((24, 24, 168, 168)) for i in ims], 1))
        rows.append((bid, pair))
    return rows


def cards_rows(weapon, rev, pick):
    pair = []
    for side in (rev, None):
        ims = [git_png(f"assets/sprites/ui_traits/{n}.png", rev) if side else Image.open(os.path.join(SPR, "ui_traits", n + ".png")).convert("RGBA") for n in pick]
        pair.append(stack([strip(ims, 1), strip([i.resize((64, 64), Image.NEAREST) for i in ims], 1)], gap=2))
    return pair


CARDS = {"greatsword": ["greatsword_g_launch", "greatsword_g_rageFire", "greatsword_jarCrush", "greatsword_g_shoulderFlip", "res_greatsword_weight"],
         "bow": ["bow_b_perfectPin", "bow_b_scatterVolley", "bow_b_starWell", "bow_fireArrow", "res_bow_breach"]}


def build(weapon, rev):
    rows = []
    for name, idx in SHEETS[weapon]:
        try:
            mb, gb = load(name, rev)
            ma, ga = load(name)
        except Exception as e:  # noqa: BLE001
            print("건너뜀", name, e)
            continue
        b = strip(frames(mb, gb, idx), 1)
        a = strip(frames(ma, ga, idx), 1)
        row = Image.new("RGBA", (b.width + a.width + 16, max(b.height, a.height) + 14), (16, 14, 12, 255))
        row.paste(b, (0, 14))
        row.paste(a, (b.width + 16, 14))
        label(row, name.split("/")[-1] + "   전 | 후")
        rows.append(row)
    for bid, (b, a) in looks_rows(weapon, rev):
        b2 = b.resize((b.width * 2, b.height * 2), Image.NEAREST)
        a2 = a.resize((a.width * 2, a.height * 2), Image.NEAREST)
        rows.append(label(stack([Image.new("RGBA", (10, 14), (16, 14, 12, 255)), b2, a2], gap=2), f"looks {bid}: base a1 a2 a2_길×2 (위 전 / 아래 후)"))
    b, a = cards_rows(weapon, rev, CARDS[weapon])
    rows.append(label(stack([Image.new("RGBA", (10, 14), (16, 14, 12, 255)), b, a], gap=4), "카드 128·64 (위 전 / 아래 후)"))
    out = os.path.join(HERE, f"preview_{weapon}.png")
    stack(rows).save(out)
    print(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rev", default=REV)
    ap.add_argument("--weapon", nargs="*", default=["greatsword", "bow"])
    a = ap.parse_args()
    for w in a.weapon:
        build(w, a.rev)


if __name__ == "__main__":
    main()
