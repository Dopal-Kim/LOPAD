#!/usr/bin/env python3
"""53라운드 Q6 — 연회장(보스) Gemini 외벽 테두리 + 골목 입구 조각 빌드 (계약 art-assets §13, 처리 = ../border_kit.py).

python3 parts/art/work/gemini/border_hall/build.py
원본·프롬프트·호출 메타는 이 폴더(프롬프트 원문 = ../border_prompts.py). 게임 투입 PNG 는 손으로 고치지 않는다.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import border_kit as BK  # noqa: E402

BANDS = {
    "north": dict(parts=[("raw_north_a.jpg", (0, 0, 4128, 1024))], wrap="x", wrap_overlap=56,
                  baseline_src=950, curve="wall", light_cap=14),     # 단상 계단·기둥 밑변. 아래 술 웅덩이는 앞치마
    "west": dict(parts=[("raw_west_a.jpg", (150, 0, 790, 4128))], wrap="y", wrap_overlap=72, curve="wall", light_cap=6),
    "east": dict(parts=[("raw_east_a.jpg", (0, 0, 640, 4128))], wrap="y", wrap_overlap=72, curve="wall", light_cap=6),
    # 남: 흰 바탕(난간 사이 = 난간 너머로 보이는 바닥 자리) → 투명. 가운데 번진 구간을 피해 깨끗한 기둥 1주기(1478)만 사용
    "south": dict(parts=[("raw_south_a.jpg", (78, 0, 1630, 480))], wrap="x", wrap_overlap=64,   # 1630 = 주기 1478 + 겹침 80(원본) → 위상 일치
                  baseline_src=300, bottom_fade=56, curve="fore", white_key=True),
}
DOORS = {
    "north": dict(sheet="raw_doors_a.jpg", box=(84, 236, 1021, 1314), scale=0.45, baseline_src=1283,
                  opening_src=(330, 780), curve="wall"),
    "south": dict(sheet="raw_doors_a.jpg", box=(1966, 470, 2633, 1195), scale=0.45, opening_src=(2192, 2514)),
    "west": dict(front_x=560, south_x=300, openingH=96, curve="wall"),   # 기둥·촛대 구간(800 은 단상 계단이 잘려 와 어색 — 3회차 비평)
}
# 52라운드 연회장 배치: 보스는 단상 위 왕좌에서 시작 → 왕좌가 바닥 가운데 위에 오도록 focusX 를 바닥 가운데 x 에 맞춘다(필수 제안)
EXTRA = {"north": {"focusX": 821.3, "focusNote": "술통 왕좌·화로 가운데(띠 국소 논리 x). 바닥 가운데 x 에 맞춰 반복 위상을 정한다(보스 시작 위치 = 왕좌 바로 앞 바닥)."}}

def main():
    BK.build_region("hall", HERE, BANDS, DOORS, extra=EXTRA)


if __name__ == "__main__":
    main()
