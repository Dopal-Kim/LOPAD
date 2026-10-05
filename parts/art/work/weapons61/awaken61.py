"""61라운드 — 각성 궤적 1:1 교체 규칙(계약 §21: 근접은 틀·피벗·프레임·ms·행 동일, 화살은 피벗~촉 거리 동일·틀이 더 김)을
이번에 바꾼 기본 시트에 다시 맞춘다.

- fx/v3/dagger_combo1~3_awaken: 60라운드 각성 그림(귀화)은 그대로, 틀만 새 기본 시트(480×480 · 피벗 (240,280) / 3타 544×544 · (272,312))로
  옮김(피벗이 같은 자리에 오게 평행 이동 — 그림 픽셀 그대로). hitOriginInFrame 도 같이 옮김.
- fx/v3/bow_arrow_awaken: 기본 bow_arrow 가 128×28 · 피벗 (104,14) · 4프레임 50ms 루프가 되어, 각성 화살도 4프레임 50ms 루프 ·
  152×28 · 피벗 (128,14)(촉까지 24 도트 — 기본과 같음, 틀은 더 김). 그림은 60라운드 그대로 + 꼬리 쪽 깜빡이는 불씨 몇 점(그 그림의 색만).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wk61 import Rand, old_meta, old_grid, SPR, gridsheet  # noqa: E402
from PIL import Image  # noqa: E402

SRC = "parts/art/work/weapons61/build.py awaken (61라운드 각성 궤적 틀 맞춤 — 그림은 60라운드 그대로)"


def recanvas_dagger(n):
    name = "dagger_combo%d_awaken" % n
    m, g = old_meta("fx", name), old_grid("fx", name)          # prev/ 보관본(60라운드 틀) — 다시 빌드해도 겹치지 않게
    bm = gridsheet.load_meta(os.path.join(SPR, "fx", "v3", "dagger_combo%d.json" % n))   # 지금(61) 기본 시트 틀
    fw, fh, cols = m["frameWidth"], m["frameHeight"], m["frames"]
    W, H = bm["frameWidth"], bm["frameHeight"]
    dx, dy = bm["pivot"]["x"] - m["pivot"]["x"], bm["pivot"]["y"] - m["pivot"]["y"]
    rows = []
    for r in range(len(m["directions"])):
        row = []
        for i in range(cols):
            f = g.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh))
            out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            out.alpha_composite(f, (dx, dy))
            row.append(out)
        rows.append(row)
    meta = {k: v for k, v in m.items() if k not in ("source", "colors")}
    meta["pivot"] = dict(bm["pivot"])
    if "hitOriginInFrame" in m:
        meta["hitOriginInFrame"] = {"x": m["hitOriginInFrame"]["x"] + dx, "y": m["hitOriginInFrame"]["y"] + dy}
    meta.update(version="v3-r61", source=SRC + " · 그림 = " + m.get("source", ""),
                r61=("61라운드: 기본 dagger_combo%d 틀이 %d×%d · 피벗 (%d,%d) 로 바뀌어 각성 궤적도 같은 틀·피벗으로 옮김(그림 픽셀 그대로, 평행 이동 %+d,%+d). "
                     "60라운드 틀 %d×%d · 피벗 (%d,%d)") % (n, W, H, bm["pivot"]["x"], bm["pivot"]["y"], dx, dy, fw, fh, m["pivot"]["x"], m["pivot"]["y"]))
    return name, rows, W, H, meta, m["frameDurationsMs"], m.get("loop", False)


def bow_arrow_awaken():
    name = "bow_arrow_awaken"
    m, g = old_meta("fx", name), old_grid("fx", name)
    bm = gridsheet.load_meta(os.path.join(SPR, "fx", "v3", "bow_arrow.json"))
    tip = bm["frameWidth"] - bm["pivot"]["x"]                     # 24
    src = g.crop((0, 0, m["frameWidth"], m["frameHeight"]))
    W, H = 152, bm["frameHeight"]
    piv = (W - tip, bm["pivot"]["y"])
    dx, dy = piv[0] - m["pivot"]["x"], piv[1] - m["pivot"]["y"]
    p = src.load()
    pts = [(x, y, p[x, y]) for y in range(src.height) for x in range(src.width) if p[x, y][3] == 255]
    cols = sorted({c for _, _, c in pts}, key=lambda c: sum(c[:3]))
    tail_x = min(x for x, _, _ in pts) + dx
    frames = []
    for i in range(4):
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out.alpha_composite(src, (dx, dy))
        o = out.load()
        r = Rand(5200 + i)
        for k in range(7):                                         # 꼬리 쪽 깜빡이는 불씨(그림에 있는 밝은 색만)
            x = tail_x + r.i(0, 40) - 4
            y = piv[1] + r.i(-4, 4)
            if 1 <= x < W - 1 and 1 <= y < H - 1 and o[x, y][3] == 0:
                o[x, y] = cols[-1 - (k % 3)]
        frames.append(out)
    meta = {k: v for k, v in m.items() if k not in ("source", "colors", "fps")}
    meta.update(pivot={"x": piv[0], "y": piv[1]}, loop=True, anim="loop_move", version="v3-r61",
                source=SRC + " · 그림 = " + m.get("source", ""),
                r61=("61라운드: 기본 bow_arrow 가 128×28 · 피벗 (104,14) · 4프레임 50ms 루프로 바뀌어 각성 화살도 4프레임 50ms 루프 · "
                     "%d×%d · 피벗 (%d,%d)(피벗~촉 %d 도트 = 기본과 같음). 그림 그대로 + 꼬리 불씨 깜빡임") % (W, H, piv[0], piv[1], tip))
    return name, [frames], W, H, meta, [50, 50, 50, 50], True
