#!/usr/bin/env python3
"""61라운드 아트 2 — 보스 '만취' 파훼 가독성(AR-5)·결정타·쓰러짐 연출. 결정적(시드 고정).

사용: python3 parts/art/work/boss61/build.py [--dry] [--only 이름 …]
  --dry  : assets 를 건드리지 않고 미리보기만(parts/art/work/boss61/preview_*.png)
산출(assets/sprites/…/v3, 트림 아틀라스 — 계약 §19):
  fx/boss1_cup_glint · fx/boss1_candle_glint · fx/boss1_break_daze · fx/boss1_finisher_slash · fx/boss1_finisher_burst ·
  fx/boss1_defeat_shatter · fx/boss1_flame_snuff
  structures/boss1_pillar(균열 3단 추가) · structures/boss1_candelabra(다시 켠 불꽃 위치 고침) ·
  structures/boss1_rolling_barrel_rim(되칠 수 있음 테) · structures/boss1_rolling_barrel_returned(되친 술통)
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import k61  # noqa: E402
from k61 import b2  # noqa: E402
import readable as R  # noqa: E402
import finale as F  # noqa: E402
from PIL import Image  # noqa: E402

ITEMS = [R.cup_glint, R.pillar, R.barrel_rim, R.barrel_returned, R.candelabra_fix, R.candle_glint, R.break_daze,
         F.finisher_slash, F.finisher_burst, F.defeat_shatter, F.flame_snuff]
SEMI_OK = {"boss1_pillar", "boss1_candelabra", "boss1_rolling_barrel_returned"}   # 구조물 접지 그림자(54라운드 규칙)


def preview(name, rows, fw, fh, k):
    cols = len(rows[0])
    im = Image.new("RGBA", (cols * fw, len(rows) * fh), (30, 28, 34, 255))
    for j, r in enumerate(rows):
        for i, f in enumerate(r):
            im.alpha_composite(f, (i * fw, j * fh))
    while max(im.width, im.height) * k > 8000 and k > 1:
        k -= 1
    im = k61.scale(im, k)
    if max(im.size) > 8000:
        s = 8000.0 / max(im.size)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.NEAREST)
    p = os.path.join(HERE, "out", "preview_%s.png" % name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.convert("RGB").save(p)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    b2.DRY = a.dry
    stats = {}
    for fn in ITEMS:
        cat, name, rows, fw, fh, meta, ms, loop = fn()
        if a.only and name not in a.only:
            continue
        flat = [f for r in rows for f in r]
        ncol = k61.check_frames(flat, name, allow_semi=name in SEMI_OK, allow_edge=name == "boss1_candelabra")   # 54라운드 촛대 그림(0~6)은 접지 그림자가 아래 가장자리에 닿음 — 그대로
        meta = dict(meta)
        meta["colors"] = ncol
        b2.write_sheet(cat, name, flat, fw, fh, meta, rows=len(rows), durations=ms, loop=loop)
        stats[name] = dict(cat=cat, frame=[fw, fh], rows=len(rows), cols=len(rows[0]), colors=ncol)
        preview(name, rows, fw, fh, 2 if fw < 600 else 1)
        print(name, stats[name])
    if not a.dry:
        rep = k61.to_atlas()
        for r in rep:
            print("atlas", r)
        p = os.path.join(HERE, "stats.json")
        old = json.load(open(p)) if os.path.exists(p) else {}
        old.update(stats)
        json.dump(old, open(p, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
