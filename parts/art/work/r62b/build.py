"""62 루프 2 아트(P16) 빌드.

    python3 parts/art/work/r62b/build.py [--only smear,spawn,rim,cards,event,world,doors] [--dry]

--dry : assets 에 쓰지 않고 미리보기만(work/r62b/preview_*.png).
결과 시트는 격자로 쓴 직후 atlas57 변환(트림 아틀라스, 계약 §19.5)을 거친다. 타일·UI 1배 그림은 PNG 그대로.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import common  # noqa: E402
from common import b2  # noqa: E402

STEPS = ["smear", "spawn", "rim", "cards", "event", "world", "doors"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=",".join(STEPS))
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    only = a.only.split(",")
    b2.DRY = a.dry
    common.DRY = a.dry
    if "smear" in only:
        import smear
        out = smear.build_all()
        smear.preview(out, os.path.join(HERE, "preview_smear.png"))
    if "spawn" in only:
        import spawn
        spawn.build(os.path.join(HERE, "preview_spawn.png"))
    if "rim" in only:
        import rim
        rim.build(os.path.join(HERE, "preview_rim.png"))
    if "cards" in only:
        import cards
        cards.build(os.path.join(HERE, "preview_cards.png"))
    if "event" in only:
        import event
        event.build(os.path.join(HERE, "preview_event.png"))
    if "world" in only:
        import world
        world.build(os.path.join(HERE, "preview_world.png"))
    if "doors" in only:
        import doors
        doors.build(os.path.join(HERE, "preview_doors.png"))
    if not a.dry:
        rep = b2.to_atlas()
        for r in rep:
            print("atlas", r)
        b2.WRITTEN.clear()


if __name__ == "__main__":
    main()
