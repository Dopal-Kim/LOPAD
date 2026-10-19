#!/usr/bin/env python3
"""P21 아트 A — 타일셋 v4 판독 점검: 칸 묶음(바닥·덮개·벽 윗면·앞면·테·낙하 등)의 평균 색을 grade_proposal 보정 전/후로 재고,
판독 짝(바닥↔낙하 채움, 바닥↔벽 윗면 등)의 명도 차·색 거리가 보정 뒤 기준 아래로 떨어지는 곳을 찾는다.

python3 parts/art/work/dark21/tiles_audit.py [--atlas-dir assets/tiles/v4] [--out tiles_audit.json]
기준: 명도 차(루마) ≥ 0.045 또는 색 거리(OKLab ΔE) ≥ 0.06 이면 '읽힘'. 주변광 변경은 지역 비율로 곱한다(grade.py 와 같음).
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, HERE)
import grade as GR  # noqa: E402

REGIONS = ["outer", "gate", "brewery", "hall", "waste"]
GROUPS = {"floor": range(96, 160), "dirt": range(160, 224), "stone": range(224, 288), "rim": range(320, 352),
          "decal": range(352, 368), "wallFront": range(376, 383), "wallTop": range(383, 388), "wallTopEdge": range(392, 408),
          "dropFill": range(408, 424), "bank": range(424, 440), "rail": range(444, 450), "bridge": range(450, 456),
          "ledgeLip": range(456, 472), "ledgeFace": range(472, 476), "stair": range(476, 482)}
PAIRS = [("floor", "dropFill", "낙하(물·낭떠러지) 경계 — 위험"), ("floor", "wallTop", "벽 윗면"), ("wallTop", "wallFront", "벽 높이감"),
         ("floor", "wallFront", "벽 발치"), ("floor", "dirt", "흙 덮개"), ("floor", "stone", "돌 덮개"), ("floor", "ledgeFace", "높은 단 앞면"),
         ("floor", "bank", "둑"), ("floor", "decal", "바닥 데칼"), ("floor", "rim", "덮개 테")]
LUMA_MIN, DE_MIN = 0.045, 0.06


def oklab(rgb):
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]])
    lms = np.cbrt(c @ M1.T)
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]])
    return lms @ M2.T


def group_means(im, ratio, g):
    a = np.asarray(im, np.float32) / 255
    cols = im.width // 64
    out = {}
    for name, rng in GROUPS.items():
        px = []
        for i in rng:
            ty, tx = divmod(i, cols)
            cell = a[ty * 64:(ty + 1) * 64, tx * 64:(tx + 1) * 64]
            if cell.shape[0] < 64:
                continue
            m = cell[..., 3] > 0.5
            if m.any():
                px.append(cell[..., :3][m])
        if not px:
            continue
        rgb = np.concatenate(px)
        before = rgb
        after = np.clip((rgb * ratio) @ GR.matrix(g)[:, :3].T + GR.matrix(g)[:, 3], 0, 1)
        out[name] = {k: {"luma": float((v @ np.array([0.2126, 0.7152, 0.0722])).mean()), "lab": oklab(v).mean(0).tolist(),
                         "chroma": float((v.max(1) - v.min(1)).mean())} for k, v in (("before", before), ("after", after))}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas-dir", default=os.path.join(ROOT, "assets/tiles/v4"))
    ap.add_argument("--out", default=os.path.join(HERE, "tiles_audit.json"))
    a = ap.parse_args()
    prop = json.load(open(os.path.join(HERE, "grade_proposal.json"), encoding="utf-8"))
    light = json.load(open(os.path.join(HERE, "lighting_proposal.json"), encoding="utf-8"))
    cur = light["_current"]
    rep, flags = {}, []
    for r in REGIONS:
        im = Image.open(os.path.join(a.atlas_dir, f"stage1_{r}.png")).convert("RGBA")
        g = GR.merged(prop, r)
        amb = light["regions"].get(r, light["default"])["ambient"]
        ratio = float(GR.hx(amb).mean() / GR.hx(cur.get(f"{r}.ambient", cur["default.ambient"])).mean())
        gm = group_means(im, ratio, g)
        pairs = {}
        for x, y, why in PAIRS:
            if x not in gm or y not in gm:
                continue
            res = {}
            for k in ("before", "after"):
                dl = abs(gm[x][k]["luma"] - gm[y][k]["luma"])
                de = float(np.linalg.norm(np.array(gm[x][k]["lab"]) - np.array(gm[y][k]["lab"])))
                res[k] = {"dLuma": round(dl, 4), "dE": round(de, 4)}
            ok_b = res["before"]["dLuma"] >= LUMA_MIN or res["before"]["dE"] >= DE_MIN
            ok_a = res["after"]["dLuma"] >= LUMA_MIN or res["after"]["dE"] >= DE_MIN
            res["readable"] = {"before": ok_b, "after": ok_a}
            pairs[f"{x}~{y}"] = res
            if ok_b and not ok_a:
                flags.append({"region": r, "pair": f"{x}~{y}", "why": why, **res})
        rep[r] = {"ambientRatio": round(ratio, 3),
                  "groups": {k: {kk: {"luma": round(vv["luma"], 4), "chroma": round(vv["chroma"], 4)} for kk, vv in v.items()} for k, v in gm.items()},
                  "pairs": pairs}
    json.dump({"criteria": {"dLuma": LUMA_MIN, "dE_oklab": DE_MIN}, "flags": flags, "regions": rep},
              open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for f in flags:
        print("FLAG", f["region"], f["pair"], f["why"], f["before"], f["after"])
    for r in REGIONS:
        gr = rep[r]["groups"]
        print(r, "floor", gr["floor"]["before"], "→", gr["floor"]["after"], "| wallTop", gr.get("wallTop", {}).get("before"), "→", gr.get("wallTop", {}).get("after"))
    return flags


if __name__ == "__main__":
    main()
