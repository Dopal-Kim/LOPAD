"""2차 묶음 아트(57라운드 Q38 · 60라운드 Q4) 공용 — 시트 쓰기·아틀라스 변환·미리보기.

- 그림 도구는 props_v3 의 pk.py·common.py(2배 밀도 셰이딩, 1층 램프 + v2 재질 블록)를 그대로 가져다 쓴다(읽기만).
- 단위: 도트. pixelScale 0.5 → 64 도트 = 타일 1칸(논리 32px).
- 시트는 격자로 assets 에 쓴 직후 atlas57 의 convert_sheet → apply_in_place 로 트림 아틀라스로 바꾼다(계약 §19.5).
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(HERE, "../props_v3"))
sys.path.insert(0, os.path.join(HERE, "../atlas57"))

from pk import *  # noqa: F401,F403,E402
from pk import (U, Canvas, Rand, G, A, SL, WD, PL, X, EMISSIVE, CLEAR, R_WOOD, R_WOODG, R_IRON, R_STONE,  # noqa: E402,F401
                R_NSTONE, R_WSTONE, R_CLOTH, R_CLOTHG, R_EARTH, R_COPPER, R_LIQ, R_BONE, FLAME, contact, cyl,
                plank_box, shade_mask, mask, splash, flame, embers, glass_lantern, stone_blob, face, grain,
                ell_mask, poly_mask, outline, qcol, clamp, lam, tohex)
import common as pcommon  # noqa: E402  (props_v3 공용 소품: barrel_c·crate_c·sack_c·debris_c·brazier_c·tipped_barrel_c)

SPR = os.path.join(ROOT, "assets", "sprites")
PALETTE_NOTE = ("parts/art/palette/lopad.json (gray + 1층 램프 16~27) + v2 재질 블록 SL·WD·PL "
                "(parts/art/work/v2_outer/palette_v2_proposal.json, 임시·고정색) — 새 색 없음")
EMISSIVE_HEX = [tohex(c) for c in EMISSIVE]
WRITTEN = []   # (cat, name) — 이번 실행에서 쓴 시트
DRY = False    # True 면 assets 에 쓰지 않는다(미리보기 반복용)


def write_sheet(cat, name, frames, fw, fh, meta, rows=1, durations=None, loop=False):
    """frames: 행 우선 목록(rows × cols). meta: 기존 계약 필드(pivot 등). 격자 PNG+JSON 을 assets/sprites/<cat>/v3/ 에."""
    cols = len(frames) // rows
    assert cols * rows == len(frames), name
    sheet = Image.new("RGBA", (cols * fw, rows * fh), (0, 0, 0, 0))
    for i, im in enumerate(frames):
        assert im.size == (fw, fh), (name, i, im.size)
        sheet.alpha_composite(im, ((i % cols) * fw, (i // cols) * fh))
    d = os.path.join(SPR, cat, "v3")
    out = {"image": f"{name}.png", "action": name, "frameWidth": fw, "frameHeight": fh, "frames": cols,
           "directions": meta.pop("directions", ["any"] * rows if rows == 1 else ["any"]),
           "layout": meta.pop("layout", "row = direction/kind (directions·rowsAre 순서), column = frame index"),
           "frameIndex": "row * columns + column (§19 아틀라스 키)",
           "frameDurationsMs": durations or [100] * cols, "loop": loop, "pixelScale": 0.5}
    out.update(meta)
    out.setdefault("palette", PALETTE_NOTE)
    out.setdefault("source", "parts/art/work/bundle2/build.py (57라운드 Q38 2차 묶음 · 60라운드 Q4)")
    if DRY:
        return sheet
    os.makedirs(d, exist_ok=True)
    sheet.save(os.path.join(d, f"{name}.png"))
    with open(os.path.join(d, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    WRITTEN.append((cat, name))
    return sheet


def to_atlas():
    """이번 실행에서 쓴 격자 시트만 트림 아틀라스로(전 프레임 대조 통과 시 assets 교체)."""
    import importlib.util  # atlas57/build.py (이름이 이 폴더 build.py 와 같아 경로로 읽는다)
    spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(HERE, "../atlas57/build.py"))
    atlas_build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(atlas_build)
    tmp_root = os.path.join(HERE, "_atlas_tmp")
    rep = []
    for cat, name in WRITTEN:
        src_dir = os.path.join(SPR, cat, "v3")
        jp, pp = os.path.join(src_dir, name + ".json"), os.path.join(src_dir, name + ".png")
        out_dir = os.path.join(tmp_root, cat, "v3")
        res = atlas_build.convert_sheet(pp, jp, out_dir, 2, 4096, True)
        atlas_build.apply_in_place(res, out_dir, src_dir, pp, jp, 4096)
        rep.append((cat, name, res["srcSize"], [(w, h) for _, w, h in res["pages"]]))
    import shutil
    shutil.rmtree(tmp_root, ignore_errors=True)
    return rep


def colors_of(im):
    return {c for c in im.getdata() if c[3] > 0}


def preview(path, items, bg=(40, 42, 50), k=2, pad=12, label_h=0, max_w=3800):
    """items: [(PIL 이미지, 피벗 or None)] 를 줄 바꿈으로 늘어놓고 k 배 확대(긴 변 8000 이하)."""
    rows, cur, x, h = [], [], 0, 0
    for im, piv in items:
        if x + im.width > max_w and cur:
            rows.append((cur, h)); cur, x, h = [], 0, 0
        cur.append((x, im, piv)); x += im.width + pad; h = max(h, im.height)
    if cur:
        rows.append((cur, h))
    W = max(sum(i.width + pad for _, i, _ in r) for r, _ in rows) + pad
    H = sum(h + pad for _, h in rows) + pad
    out = Image.new("RGBA", (W, H), bg + (255,))
    y = pad
    for r, h in rows:
        for x0, im, piv in r:
            out.alpha_composite(im, (x0 + pad, y + h - im.height))
            if piv:
                px_, py_ = x0 + pad + piv[0], y + h - im.height + piv[1]
                for d in range(-3, 4):
                    out.putpixel((min(W - 1, px_ + d), py_), (255, 60, 60, 255))
                    out.putpixel((px_, min(H - 1, max(0, py_ + d))), (255, 60, 60, 255))
        y += h + pad
    k = min(k, max(1, 8000 // max(W, H)))
    out = out.resize((W * k, H * k), Image.NEAREST)
    out.convert("RGB").save(path)
    return out.size
