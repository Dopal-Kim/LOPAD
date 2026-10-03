#!/usr/bin/env python3
"""53라운드 Q6 — 황무지(전장) Gemini 외벽 테두리 + 골목 입구 조각 빌드 (계약 art-assets §13, 처리 = ../border_kit.py).

python3 parts/art/work/gemini/border_waste/build.py
원본·프롬프트·호출 메타는 이 폴더(프롬프트 원문 = ../border_prompts.py). 게임 투입 PNG 는 손으로 고치지 않는다.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import border_kit as BK  # noqa: E402

# 원본 좌표 = raw jpg 픽셀. north = b 채택(a 는 오른쪽 절반이 흙둑 없이 원근 평야로 열려 벽으로 안 읽힘).
BANDS = {
    "north": dict(parts=[("raw_north_b.jpg", (0, 0, 4128, 770))], wrap="x", wrap_overlap=56,
                  baseline_src=690,            # 흙둑·말뚝 밑동(원본 y). 아래 잔해 바닥(y>770)은 버림(바닥 위 잡동사니로 오인)
                  curve="wall"),
    "west": dict(parts=[("raw_west_a.jpg", (340, 280, 980, 4128))], wrap="y", wrap_overlap=72, curve="wall"),   # 위 하늘 280 버림
    "east": dict(parts=[("raw_east_a.jpg", (0, 280, 640, 4128))], wrap="y", wrap_overlap=128, curve="wall"),   # 72 → 128: 이음 17.1 → 7.2
    "south": dict(parts=[("raw_south_a.jpg", (0, 0, 5856, 480))], wrap="x", wrap_overlap=64,
                  baseline_src=215, bottom_fade=56, curve="fore"),
}
DOORS = {
    "north": dict(sheet="raw_doors_a.jpg", box=(47, 203, 930, 880), scale=0.64, baseline_src=800,
                  opening_src=(380, 620), curve="wall"),
    "south": dict(sheet="raw_doors_a.jpg", box=(1870, 486, 2705, 1269), scale=0.64, opening_src=(2180, 2418)),
    "west": dict(front_x=320, south_x=600, openingH=96, curve="wall"),
}
EXTRA = {}

def main():
    BK.build_region("waste", HERE, BANDS, DOORS, extra=EXTRA)


if __name__ == "__main__":
    main()
