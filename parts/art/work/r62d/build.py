#!/usr/bin/env python3
"""62 루프 4 아트(P18 §2·§3) — 결정적.

python3 parts/art/work/r62d/build.py [--only smear,boss]
  smear : fx/v3/katana_{spin,guardbreak,fall_wide}_smear (smear_branch.py)
  boss  : bosses/v3/stage1_* 15시트 새 도트 + _rim·_rim_lite + fx/v3/boss1_onfire·_down + ui_portraits/boss1 (boss_body.py · boss_build.py)
          BOSS_STEPS="body rim lite onfire portrait preview" 로 일부만
  traits: fx/v3/trait_<weapon>_<id>[_부위] 13시트 + ui_traits/<weapon>_<id>.png 8장 + ui_relics/drunkFist.png (traits_build.py)
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

STAGES = {"smear": "smear_branch", "boss": "boss_build", "traits": "traits_build"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    st = [s for s in a.only.split(",") if s] or list(STAGES)
    for s in st:
        mod = __import__(STAGES[s])
        print(s, "→", mod.build())


if __name__ == "__main__":
    main()
