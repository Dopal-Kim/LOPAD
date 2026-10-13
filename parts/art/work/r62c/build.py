#!/usr/bin/env python3
"""62 루프 3 아트(P17 묶음 B·C·D) — 결정적·멱등.

python3 parts/art/work/r62c/build.py [--only doors,memory,favicon,boss,smear,preview]
  doors   : paint/door_{outer,brewery}_curse + paint/door_*_small(512×288 카드판) + doors.json (doors.py)
  memory  : ui_relics/memory_{ink,bellows,hp,attack,dash,empty}.png + relics.json memory[] (memory.py)
  favicon : parts/art/work/favicon/favicon_{16,32,48}.png + favicon.ico (favicon.py)
  boss    : bosses/v3/stage1_* 재도트 (boss.py)
  trails  : fx/v3/dagger_combo{1..3}_smear · bow 발사 섬광·궤적 (smear.py)
  preview : parts/art/work/r62c/preview_*.png
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

STAGES = ["doors", "memory", "favicon", "boss", "trails", "preview"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    st = [s for s in a.only.split(",") if s] or STAGES
    for s in st:
        try:
            mod = __import__(s if s != "preview" else "previews")
        except ModuleNotFoundError as e:
            print("건너뜀:", s, e)
            continue
        print(s, "→", mod.build())


if __name__ == "__main__":
    main()
