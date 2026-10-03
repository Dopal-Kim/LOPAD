#!/usr/bin/env python3
"""53라운드 Q6 — 성문 Gemini 외벽 테두리 + 골목 입구 조각 빌드 (계약 art-assets §13, 처리 = ../border_kit.py).

python3 parts/art/work/gemini/border_gate/build.py
원본·프롬프트·호출 메타는 이 폴더(프롬프트 원문 = ../border_prompts.py). 게임 투입 PNG 는 손으로 고치지 않는다.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import border_kit as BK  # noqa: E402

BANDS = {
    "north": dict(parts=[("raw_north_a.jpg", (0, 0, 4128, 1024))], wrap="x", wrap_overlap=56,
                  baseline_src=950, curve="wall"),        # 성벽 기단 밑변
    "west": dict(parts=[("raw_west_a.jpg", (230, 0, 870, 4128))], wrap="y", wrap_overlap=72, curve="wall"),   # 오른쪽 검은 틈 버림
    "east": dict(parts=[("raw_east_a.jpg", (0, 0, 640, 4128))], wrap="y", wrap_overlap=72, curve="wall"),
    "south": dict(parts=[("raw_south_a.jpg", (0, 0, 5856, 420))], wrap="x", wrap_overlap=64,
                  baseline_src=55, bottom_fade=56, curve="fore"),   # 해자 북쪽 둑 갓돌
}
DOORS = {
    "north": dict(sheet="raw_doors_a.jpg", box=(46, 327, 908, 1060), scale=0.67, baseline_src=975,
                  opening_src=(379, 594), curve="wall"),
    "south": dict(sheet="raw_doors_a.jpg", box=(1844, 401, 2706, 1271), scale=0.67, opening_src=(2034, 2558)),
    "west": dict(front_x=480, south_x=900, openingH=96, curve="wall"),
}
# 큰 성문(문 터널 빛)이 띠 가운데 — 시스템이 출구 문을 북쪽 가운데에 둘 때 맞추도록 기준 x 제공(선택)
EXTRA = {"north": {"focusX": 824.0, "focusNote": "성문 터널 가운데(띠 국소 논리 x). 선택: 바닥 가운데 또는 북쪽 출구 문 칸 가운데에 맞춰 띠의 반복 위상을 정한다."}}

def main():
    BK.build_region("gate", HERE, BANDS, DOORS, extra=EXTRA)


if __name__ == "__main__":
    main()
