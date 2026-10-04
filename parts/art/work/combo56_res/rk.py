"""56라운드 작업 D 공용 — 팔레트·캔버스·시트 쓰기·검사.

도구는 기존 것을 그대로 쓴다(읽기만): fx_v3/fxkit(레이어 램프 래스터) · fx_weapons_v3/wkit(팔레트·Frame·flake·ember).
색: 주인공 v3 재·호박 램프 + 백열 X0/X1(판정 순간만). 반투명 0. paletteSwap none.
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "fx_weapons_v3")))
import wkit as W  # noqa: E402
from wkit import FK  # noqa: E402

OUT_FX = os.path.join(ROOT, "assets/sprites/fx/v3")
OUT_W = os.path.join(ROOT, "assets/sprites/weapons/v3")
OUT_P = os.path.join(ROOT, "assets/sprites/player/v3")
SPR = os.path.join(ROOT, "assets/sprites")
VERSION = "v3-r56d"
SRC = "parts/art/work/combo56_res/build.py (56라운드 작업 D — 자원·가드·그로기 표시)"

X0, X1 = W.X0, W.X1
A17, A18, A19, A21, A23, A25, A26 = W.A17, W.A18, W.A19, W.A21, W.A23, W.A25, W.A26
B0, B1, B2, B3 = W.B0, W.B1, W.B2, W.B3
S0, S1, S2, S3 = W.S0, W.S1, W.S2, W.S3
HOT = {X0, X1, A26}
PALETTE_NOTE = W.PALETTE_NOTE


def hexrgb(h):
    return FK.hexrgb(h)


def frame(w, h):
    return W.Frame(w, h, None)


def colors_of(im):
    return W.colors_of(im)


def load_sheet(path):
    """path = 'weapons/v3/katana_rise' → (json, {dir: [frame RGBA]})."""
    j = json.load(open(os.path.join(SPR, path + ".json"), encoding="utf-8"))
    im = Image.open(os.path.join(SPR, path + ".png")).convert("RGBA")
    fw, fh, F = j["frameWidth"], j["frameHeight"], j["frames"]
    out = {}
    for r, d in enumerate(j["directions"]):
        out[d] = [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(F)]
    return j, out


def write_sheet(name, out_dir, rows, frames, ms, meta, glow=None, cap=14, loop=False, allowed=None, edge_ok=False,
                hot_ok_frames=None):
    """rows = 행 키 순서, frames = {행 키: [RGBA]}. glow = 백열(X0/X1/A26) 허용 프레임(None = 검사 안 함, [] = 전부 금지).
    hot_ok_frames = {행 키: [프레임]} 행마다 다른 허용(선택)."""
    frames = W.limit_colors(frames, cap, name)
    fw, fh = frames[rows[0]][0].size
    F = len(ms)
    sheet = Image.new("RGBA", (fw * F, fh * len(rows)), (0, 0, 0, 0))
    for r, d in enumerate(rows):
        assert len(frames[d]) == F, (name, d, len(frames[d]), F)
        for c, im in enumerate(frames[d]):
            assert im.size == (fw, fh), (name, d, c, im.size)
            sheet.alpha_composite(im, (c * fw, r * fh))
    cols = colors_of(sheet)
    ok = allowed or W.ALLOWED
    assert not (cols - ok), (name, sorted(cols - ok))
    assert len(cols) <= cap, (name, len(cols))
    assert not W.has_partial(sheet), name
    if not edge_ok:
        e = sum(W.edge_touch(im) for d in rows for im in frames[d])
        assert e == 0, (name, "edge", e)
    if glow is not None:
        for d in rows:
            okf = set(hot_ok_frames[d]) if hot_ok_frames and d in hot_ok_frames else set(glow)
            for i, im in enumerate(frames[d]):
                if i not in okf:
                    assert not (colors_of(im) & HOT), (name, d, i, sorted(colors_of(im) & HOT))
    j = dict(image=name + ".png", action=name, version=VERSION, frameWidth=fw, frameHeight=fh, frames=F, directions=list(rows),
             layout="rows = directions(또는 JSON 이 밝힌 행 키), columns = frames", frameIndex="row * frames + column",
             fps=round(1000 * F / max(1, sum(ms)), 2), frameDurationsMs=list(ms), loop=loop, pixelScale=0.5,
             paletteSwap="none", paletteSwapNote="53라운드 Q62·Q68 — fx·표시 오버레이는 지역 바닥 팔레트 교체 제외",
             palette=PALETTE_NOTE, colors=len(cols), semiTransparent=False, source=SRC)
    j.update(meta)
    if glow is not None and "glowFrames" not in meta:
        j["glowFrames"] = sorted(glow)
    if glow is not None and "glowRule" not in meta:
        j["glowRule"] = "53라운드 Q65: 백열 X0/X1·A26 은 glowFrames(판정 순간)만. 그 밖 프레임은 A25(#eecc78) 이하 — 빌드 검사 통과"
    os.makedirs(out_dir, exist_ok=True)
    sheet.save(os.path.join(out_dir, name + ".png"), optimize=True)
    with open(os.path.join(out_dir, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
    return sheet, j, frames


def fit_frames(frames, anchor, margin=3, step=8, keep_anchor=True):
    """큰 캔버스 프레임들 → 합집합 상자로 자름. anchor(캔버스 좌표) → 잘린 틀 좌표."""
    box = (anchor[0], anchor[1], anchor[0] + 1, anchor[1] + 1) if keep_anchor else None
    for lst in frames.values():
        for im in lst:
            b = im.getbbox()
            if b:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    x0, y0 = box[0] - margin, box[1] - margin
    Wd = -(-(box[2] + margin - x0) // step) * step
    Hd = -(-(box[3] + margin - y0) // step) * step
    out = {d: [im.crop((x0, y0, x0 + Wd, y0 + Hd)) for im in lst] for d, lst in frames.items()}
    return out, (anchor[0] - x0, anchor[1] - y0)


def fit_centered(frames, anchor, margin=3, step=8):
    """피벗이 틀 가운데(가로·세로 대칭)에 오도록 자름 — 회전하는 시트용."""
    rx = ry = 1
    for lst in frames.values():
        for im in lst:
            b = im.getbbox()
            if b:
                rx = max(rx, anchor[0] - b[0], b[2] - anchor[0])
                ry = max(ry, anchor[1] - b[1], b[3] - anchor[1])
    hw = -(-(rx + margin) // (step // 2)) * (step // 2)
    hh = -(-(ry + margin) // (step // 2)) * (step // 2)
    x0, y0 = anchor[0] - hw, anchor[1] - hh
    out = {d: [im.crop((x0, y0, x0 + 2 * hw, y0 + 2 * hh)) for im in lst] for d, lst in frames.items()}
    return out, (hw, hh)
