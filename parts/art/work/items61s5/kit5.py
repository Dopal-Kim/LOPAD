"""61 단계 5 (P13) 아트 공용 — 드랍 아이템·기둥 무너짐. Pillow 만, 결정적(시드 고정).

- 팔레트: props_v3/pk(= v2_outer/kit) 의 G·A·SL·WD·PL + lopad.json floors[6] '적' 램프(R, 물약 붉은 술) — 새 색 없음.
- 단위: 도트(pixelScale 0.5, 64 도트 = 1칸).
- 시트 쓰기: 격자 PNG+JSON 을 assets 에 쓴 직후 atlas57 convert_sheet → apply_in_place(계약 §19.5).
  임시 폴더는 이 작업 전용 `items61s5/_atlas_tmp_<pid>` — 같은 시간에 도는 다른 아트 작업(무기·fx)의 임시 폴더를 건드리지 않는다.
"""
import json
import math
import os
import shutil
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
sys.path.insert(0, os.path.join(WORK, "props_v3"))
sys.path.insert(0, os.path.join(WORK, "atlas57"))

from pk import (Canvas, Rand, G, A, SL, WD, PL, X, EMISSIVE, CONTACT, R_NSTONE, stone_blob, flame, qcol,  # noqa: E402,F401
                mask, shade_mask, tohex)
import gridsheet  # noqa: E402

_PAL = json.load(open(os.path.join(WORK, "..", "palette", "lopad.json"), encoding="utf-8"))
R = [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for h in _PAL["floors"][6]["ramp"]]   # '적' 램프 12
X0, X1 = X[0], X[1]
SPR = os.path.join(ROOT, "assets", "sprites")
DRY = False
WRITTEN = []


def lighten_map(*ramps, step=2):
    m = {}
    for r in ramps:
        for i, c in enumerate(r):
            m.setdefault(c[:3], r[min(len(r) - 1, i + step)])
    return m


def outline_out(im, col):
    """알파 경계 바깥 1도트(4방향) 외곽선."""
    w, h = im.size
    p = im.load()
    add = []
    for y in range(h):
        for x in range(w):
            if p[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and p[xx, yy][3] == 255:
                    add.append((x, y))
                    break
    for x, y in add:
        p[x, y] = col
    return im


def crop_rest(im):
    """그린 물건(64×64, 바닥점 (32,58))을 경계 상자로 잘라 (그림, 바닥점 기준 왼쪽 위 오프셋)."""
    bb = im.getbbox()
    return im.crop(bb), (bb[0] - 32, bb[1] - 58)


def star(c, x, y, arm, core, mid, edge):
    c.px(x, y, core)
    for k in range(1, arm + 1):
        col = mid if k < arm else edge
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.px(x + dx, y + dy, col)


def disc(c, cx, cy, r, col, ky=1.0, only_empty=False):
    for y in range(int(cy - r * ky) - 1, int(cy + r * ky) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if ((x - cx) / max(0.5, r)) ** 2 + ((y - cy) / max(0.5, r * ky)) ** 2 <= 1.0:
                if only_empty and c.get(x, y)[3]:
                    continue
                c.px(x, y, col)


def contact_shadow(c, cx, cy, rx, ry, a=110):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            d = ((x + 0.5 - cx) / (rx + 0.5)) ** 2 + ((y + 0.5 - cy) / (ry + 0.5)) ** 2
            if d <= 1 and c.get(x, y)[3] == 0:
                c.px(x, y, (CONTACT[0], CONTACT[1], CONTACT[2], int(a * (0.55 + 0.45 * (1 - d)))))


def check_frames(frames, name, allow_semi_rgb=(CONTACT[:3],), allow_edge=False):
    """반투명은 접지 그림자 색만 · 가장자리 잘림 0(불투명 픽셀 — 구조물 접지 그림자는 54라운드 기둥처럼 아래 가장자리에 닿을 수 있음). 불투명 색 수 반환."""
    cols = set()
    for i, im in enumerate(frames):
        w, h = im.size
        p = im.load()
        for y in range(h):
            for x in range(w):
                c = p[x, y]
                if not c[3]:
                    continue
                if c[3] < 255 and c[:3] not in allow_semi_rgb:
                    raise AssertionError((name, i, "semi", x, y, c))
                if c[3] == 255:
                    cols.add(c[:3])
                if not allow_edge and (x in (0, w - 1) or y in (0, h - 1)) and c[3] == 255:
                    raise AssertionError((name, i, "edge", x, y))
    return cols


def palette_set():
    s = {c[:3] for c in G} | {c[:3] for c in A.values()} | {c[:3] for c in SL} | {c[:3] for c in WD} | \
        {c[:3] for c in PL} | {c[:3] for c in R} | {X0[:3], X1[:3]}
    return s


def write_grid(cat, name, frames, fw, fh, meta, rows, durations, loop):
    cols = len(frames) // rows
    assert cols * rows == len(frames), name
    sheet = Image.new("RGBA", (cols * fw, rows * fh), (0, 0, 0, 0))
    for i, im in enumerate(frames):
        assert im.size == (fw, fh), (name, i, im.size)
        sheet.alpha_composite(im, ((i % cols) * fw, (i // cols) * fh))
    out = {"image": f"{name}.png", "action": name, "frameWidth": fw, "frameHeight": fh, "frames": cols}
    out.update(meta)
    out["frameDurationsMs"] = durations
    out["loop"] = loop
    out["pixelScale"] = 0.5
    if DRY:
        return sheet
    d = os.path.join(SPR, cat, "v3")
    os.makedirs(d, exist_ok=True)
    sheet.save(os.path.join(d, f"{name}.png"))
    with open(os.path.join(d, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    WRITTEN.append((cat, name))
    return sheet


def to_atlas():
    import importlib.util
    spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(WORK, "atlas57", "build.py"))
    ab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ab)
    tmp_root = os.path.join(HERE, "_atlas_tmp_%d" % os.getpid())
    rep = []
    try:
        for cat, name in WRITTEN:
            src_dir = os.path.join(SPR, cat, "v3")
            jp, pp = os.path.join(src_dir, name + ".json"), os.path.join(src_dir, name + ".png")
            out_dir = os.path.join(tmp_root, cat, "v3")
            os.makedirs(out_dir, exist_ok=True)
            res = ab.convert_sheet(pp, jp, out_dir, 2, 4096, True)
            ab.apply_in_place(res, out_dir, src_dir, pp, jp, 4096)
            rep.append((cat, name, res["srcSize"], [(w, h) for _, w, h in res["pages"]]))
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    WRITTEN.clear()
    return rep


def scale(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)
