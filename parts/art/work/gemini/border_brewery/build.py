#!/usr/bin/env python3
"""53라운드 Q6 — 양조 구역 Gemini 외벽 테두리 + 골목 입구 조각 빌드 (계약 art-assets §13, 처리 = ../border_kit.py).

python3 parts/art/work/gemini/border_brewery/build.py
원본·프롬프트·호출 메타는 이 폴더(프롬프트 원문 = ../border_prompts.py). 게임 투입 PNG 는 손으로 고치지 않는다.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import border_kit as BK  # noqa: E402

BANDS = {
    "north": dict(parts=[("raw_north_a.jpg", (0, 0, 4128, 1024))], wrap="x", wrap_overlap=56,
                  baseline_src=996, curve="wall", light_cap=16),     # 증류소 기단 밑변
    "west": dict(parts=[("raw_west_a.jpg", (240, 0, 880, 4128))], wrap="y", wrap_overlap=72, curve="wall"),
    # 동: 술 수로가 띠 전체를 따라 흐름 — 52라운드 Q8(수로는 다리 근처만 밝게) 취지로 발광 0.55배, 광원 상한
    "east": dict(parts=[("raw_east_a.jpg", (0, 0, 640, 4128))], wrap="y", wrap_overlap=200, curve="wall",   # 72 → 200: 이음 11.3 → 3.7
                 emit_gain=0.55, light_cap=8),
    "south": dict(parts=[("raw_south_a.jpg", (0, 0, 5856, 520))], wrap="x", wrap_overlap=72,   # 64 → 72: 이음 10.0 → 4.6
                  baseline_src=210, bottom_fade=56, curve="fore"),
}
DOORS = {
    "north": dict(sheet="raw_doors_a.jpg", box=(92, 166, 872, 1256), scale=0.6, baseline_src=1178,
                  opening_src=(300, 660), curve="wall"),
    "south": dict(sheet="raw_doors_a.jpg", box=(1880, 523, 2660, 1371), scale=0.6, opening_src=(2166, 2428)),
    "west": dict(front_x=560, south_x=900, openingH=96, curve="wall"),
}
EXTRA = {}

def main():
    BK.build_region("brewery", HERE, BANDS, DOORS, extra=EXTRA)


if __name__ == "__main__":
    main()
