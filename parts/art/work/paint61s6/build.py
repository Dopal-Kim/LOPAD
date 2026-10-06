#!/usr/bin/env python3
"""61 단계 6 (P14 §1·§3, 계약 art §28) — 그림 속 입구 · 먹 붓질 · 액자 · 수련장 지도 · 수련장 소품 · 수련장 타일. 결정적.

python3 parts/art/work/paint61s6/build.py [--only doors,map,brush,frame,props,tiles,preview] [--doors outer_shop,...] [--dry]
  doors  : assets/sprites/paint/door_<region>_<kind>.png/.json + doors.json (Gemini 원본 → 팔레트 색조 맞춤)
  map    : assets/sprites/paint/map_training.png/.json (방 8 자리 rooms)
  brush  : assets/sprites/paint/brush_reveal_{0..3}.png + brush_reveal.json
  frame  : assets/sprites/paint/frame.png/.json (9-slice)
  props  : assets/sprites/structures/v3/training_*  (트림 아틀라스, 64도트 = 1칸)
  tiles  : assets/tiles/v2/stage1_training.png/.json (성문 타일 변주 — 밝고 고요한 마당)
  preview: parts/art/work/paint61s6/preview_*.png
Gemini 다시 받기: gen.py (키 없이 — 프록시가 붙임).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

STAGES = ["doors", "map", "brush", "frame", "props", "tiles", "preview"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--doors", default="")
    ap.add_argument("--dry", action="store_true", help="props: assets 를 건드리지 않음")
    a = ap.parse_args()
    st = [s for s in a.only.split(",") if s] or STAGES
    if any(s in st for s in ("doors", "map", "brush", "frame")):
        import paint as P
        if "doors" in st:
            P.build_doors([d for d in a.doors.split(",") if d] or None)
        if "map" in st:
            P.build_map()
        if "brush" in st:
            P.build_brush()
        if "frame" in st:
            P.build_frame()
    if "props" in st:
        import tprops
        tprops.build(dry=a.dry)
    if "tiles" in st:
        import ttiles
        ttiles.build()
    if "preview" in st:
        import preview61s6
        preview61s6.run()


if __name__ == "__main__":
    main()
