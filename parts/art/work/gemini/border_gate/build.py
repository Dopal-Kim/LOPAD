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
    # 53라운드 Q22: 띠를 통째로 반복하면 성문이 두 개 보임 → 가운데 조각(성문·옆문·통행세 오두막, 원본 x 1080~3100)은 한 번만,
    # 좌(원본 60~1150: 끝 망루·깃발·상자)·우(3030~4100: 바리케이드·물통·끝 망루) 성벽 조각만 반복. 경계는 원래 그림에서 이어지는 자리.
    "north": dict(parts=[("raw_north_a.jpg", (0, 0, 4128, 1024))], wrap_overlap=56,
                  split={"left": (60, 1150), "right": (3030, 4100)},
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
# focusX = 성문 터널 가운데(가운데 조각 국소 논리 x) = (2060 × 0.8 − 864) / 2
EXTRA = {"north": {"focusX": 392.0, "focusNote": "성문 터널 가운데(가운데 조각 north.png 국소 논리 x). 바닥 가운데 x 에 맞춘다(필수). 북쪽 출구가 가운데면 이 성문이 출구 — door_north(옆문)는 가운데가 아닌 북쪽 문에만."}}

def main():
    BK.build_region("gate", HERE, BANDS, DOORS, extra=EXTRA)


if __name__ == "__main__":
    main()
