"""61라운드 대검 베기 궤적 가독성 — 56라운드 붓획(굵기 24 도트)이 어두운 바닥·1배 화면에서 '가는 선'으로만 보임(점검 15_greatsword_grid).

방법: 지금 시트(붓획 그림·프레임·ms·판정 프레임·8행 drawn8)를 그대로 두고, 붓획 안쪽(판정 원점 쪽)으로 '휘두른 자리 잔상(wake)'을
디더로 채워 넣어 초승달 덩어리로 읽히게 하고, 붓획 바깥 가장자리를 1~2 도트 두껍게 한다. 색은 A18~A23(백열 아님 — glowFrames 규칙 그대로).
프레임 역할별 세기: pre 0 · draw(머리) 0.6 · draw(끝)·impact 1.0 · decay 0.55 / 0.25 / 0.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wk61 import (A17, A18, A19, A21, A23, A25, B2, B3, S1, S2, old_meta, old_grid)  # noqa: E402
from pk import BAYER  # noqa: E402

SRC = "parts/art/work/weapons61/build.py greatsword (61라운드 대검 궤적 가독성 — 56라운드 붓획 위 잔상 덧칠)"
SHEETS = {
    # 이름: (잔상 깊이 도트, 프레임별 세기)
    "greatsword_sweep_cw": (46, [0.0, 0.6, 1.0, 0.55, 0.25, 0.0]),
    "greatsword_sweep_ccw": (46, [0.0, 0.6, 1.0, 0.55, 0.25, 0.0]),
    "greatsword_cleave": (36, [0.0, 0.7, 1.0, 0.55, 0.25, 0.0]),
    "greatsword_charge_swing": (40, [0.0, 0.5, 0.8, 1.0, 0.55, 0.25, 0.0]),
}
AMBER = {c[:3] for c in (A18, A19, A21, A23, A25)}
HOT = AMBER | {(0xf4, 0xde, 0x9b), (0xff, 0xf4, 0xdc), (0xff, 0xff, 0xff)}


def enhance(name):
    meta = old_meta("fx", name)
    grid = old_grid("fx", name)
    fw, fh, n = meta["frameWidth"], meta["frameHeight"], meta["frames"]
    rows_n = len(meta["directions"])
    depth, power = SHEETS[name]
    o = meta.get("hitOriginInFrame") or {"x": meta["pivot"]["x"], "y": meta["pivot"]["y"] - 40}
    ox, oy = o["x"], o["y"]
    rows = []
    for j in range(rows_n):
        row = []
        for i in range(n):
            im = grid.crop((i * fw, j * fh, (i + 1) * fw, (j + 1) * fh))
            k = power[i] if i < len(power) else 0.0
            if k > 0:
                im = _wake(im, ox, oy, depth * k, k)
            row.append(im)
        rows.append(row)
    keep = {kk: v for kk, v in meta.items() if kk not in ("source",)}
    keep.update(source=SRC + " · 원 붓획 = " + meta.get("source", ""), version="v3-r61",
                r61=("61라운드: 붓획 안쪽으로 휘두른 자리 잔상(디더, 깊이 %d 도트 × 프레임 세기 %s) + 바깥 가장자리 1~2 도트 보강. "
                     "프레임·ms·피벗·행·판정 프레임·glowFrames 그대로 — 56라운드 그림은 parts/art/work/weapons61/prev/fx/%s.png") % (depth, power, name),
                wake61={"depthDots": depth, "strengthByFrame": power})
    return name, rows, fw, fh, keep, meta["frameDurationsMs"], meta.get("loop", False)


def _wake(im, ox, oy, depth, k):
    w, h = im.size
    p = im.load()
    src = [(x, y) for y in range(h) for x in range(w) if p[x, y][3] == 255 and p[x, y][:3] in HOT]
    if not src:
        return im
    out = im.copy()
    q = out.load()
    # 바깥 가장자리 보강(원점에서 먼 쪽 1~2 도트)
    for (x, y) in src:
        dx, dy = x - ox, y - oy
        d = (dx * dx + dy * dy) ** 0.5 or 1.0
        for s in (1, 2) if k >= 0.9 else (1,):
            xx, yy = int(round(x + dx / d * s)), int(round(y + dy / d * s))
            if 1 <= xx < w - 1 and 1 <= yy < h - 1 and q[xx, yy][3] == 0:
                q[xx, yy] = A21 if s == 1 else A19
    # 안쪽 잔상(원점 쪽으로 depth 만큼, 멀수록 성기고 어둡게)
    L = int(depth)
    for (x, y) in src:
        dx, dy = ox - x, oy - y
        d = (dx * dx + dy * dy) ** 0.5 or 1.0
        ux, uy = dx / d, dy / d
        for s in range(2, min(L, int(d) - 30)):
            xx, yy = int(round(x + ux * s)), int(round(y + uy * s))
            if not (1 <= xx < w - 1 and 1 <= yy < h - 1) or q[xx, yy][3]:
                continue
            t = s / float(L)
            dens = (1.0 - t) ** 1.3 * (0.85 if k >= 0.9 else 0.65)
            if (BAYER[yy % 4][xx % 4] + 0.5) / 16.0 >= dens:
                continue
            if k < 0.4:
                col = B3 if t < 0.5 else B2
            else:
                col = A21 if t < 0.22 else (A19 if t < 0.55 else A18)
            q[xx, yy] = col
    return out
