#!/usr/bin/env python3
"""P21 아트 A — 타일셋 v4 바닥을 한 단 어둡고 차갑게(팔레트 안에서 램프 한 칸 내림). 벽 윗면·윗면 테·높은 단 테는 그대로.

python3 parts/art/work/dark21/tiles_dark.py [--src assets/tiles/v4] [--dst assets/tiles/v4]
  · 원본은 git(HEAD)의 v4 아틀라스 — 여러 번 돌려도 두 단 내려가지 않게 항상 --src-rev 커밋에서 읽는다(기본 HEAD).
  · 대상 칸: 바닥 매크로 96~159 만(덮개까지 내리면 흙 덮개·낙하 채움·데칼과 붙어 버림 — tiles_audit 로 비교해 고름).
  · 색 규칙: 같은 램프 한 칸 아래(G·A·WD·SL). PL(따뜻한 회반죽/판석) → 같은 순번의 SL(차가운 청회) 한 칸 아래 = '차갑게'.
    램프 맨 아래 색·램프 밖 색(발광 포함)은 그대로. 알파 그대로.
  · p19/tiles4.py 를 다시 돌리면 밝은 판으로 돌아가니 그 뒤에 이것을 다시 돌릴 것.
"""
import argparse
import io
import json
import os
import subprocess

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
REGIONS = ["outer", "gate", "brewery", "hall", "waste"]
CELLS = list(range(376, 383)) + list(range(388, 392)) + list(range(472, 476))   # 벽 앞면·앞면 끝·높은 단 앞면 — 세로면만 한 단 어둡게(윗면·테는 그대로)


def ramps():
    P = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))
    V2 = json.load(open(os.path.join(ROOT, "parts/art/work/v2_outer/palette_v2_proposal.json"), encoding="utf-8"))["blocks"]
    h = lambda s: tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))
    m = {}
    for r in (P["gray"], P["floors"][0]["ramp"], V2["WD"], V2["SL"]):
        for i in range(1, len(r)):
            m[h(r[i])] = h(r[i - 1])
    sl = V2["SL"]
    for i, c in enumerate(V2["PL"]):                 # PL 0..4 ≈ 명도 SL 3..7 → SL 한 칸 아래(2..6)
        m[h(c)] = h(sl[min(len(sl) - 1, i + 2)])
    for c in P["floors"][0]["ramp"][7:] + ["#ffffff", "#fff4dc"]:   # 발광 색은 그대로(emissive)
        m.pop(h(c), None)
    return m


def darken(im, m):
    a = np.array(im.convert("RGBA"))
    cols = im.width // 64
    for i in CELLS:
        ty, tx = divmod(i, cols)
        cell = a[ty * 64:(ty + 1) * 64, tx * 64:(tx + 1) * 64]      # 뷰 — 제자리에서 바꾼다
        for y in range(cell.shape[0]):
            for x in range(cell.shape[1]):
                if cell[y, x, 3] == 0:
                    continue
                c = (int(cell[y, x, 0]), int(cell[y, x, 1]), int(cell[y, x, 2]))
                if c in m:
                    cell[y, x, :3] = m[c]
    return Image.fromarray(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-rev", default="HEAD")
    ap.add_argument("--dst", default=os.path.join(ROOT, "assets/tiles/v4"))
    a = ap.parse_args()
    m = ramps()
    # 자체 검사: 매핑은 항상 더 어둡게
    lum = lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    assert all(lum(v) < lum(k) for k, v in m.items()), "어두워지지 않는 매핑"
    os.makedirs(a.dst, exist_ok=True)
    for r in REGIONS:
        rel = f"assets/tiles/v4/stage1_{r}.png"
        b = subprocess.run(["git", "-C", ROOT, "show", f"{a.src_rev}:{rel}"], capture_output=True, check=True).stdout
        out = darken(Image.open(io.BytesIO(b)), m)
        out.save(os.path.join(a.dst, f"stage1_{r}.png"), optimize=True)
        print("darkened", r)


if __name__ == "__main__":
    main()
