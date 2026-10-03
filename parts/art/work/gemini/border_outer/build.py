#!/usr/bin/env python3
"""53라운드 Q2·Q6 — 외곽 거리 Gemini 외벽 테두리 빌드 (계약 art-assets §13).

python3 parts/art/work/gemini/border_outer/build.py          # 산출 + 시범 목업(mock.py, 40×24)
python3 parts/art/work/gemini/border_outer/build.py --no-mock

처리는 ../border_kit.py 공용(Q6 확장 때 이 파일에서 옮김 — 띠 PNG 는 옮기기 전과 바이트 단위로 같음).
이 파일은 '어느 원본을 어떻게 잘라 어디로 내보내는지' 의 기준 표(BANDS·DOORS)만 가진다.
"""
import argparse, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import border_kit as BK  # noqa: E402

BANDS = {
    "north": dict(parts=[("raw_north_a.jpg", (0, 0, 4128, 1024)), ("raw_north_b.jpg", (176, 0, 3936, 1024))],
                  join_overlap=40, wrap="x", wrap_overlap=56,
                  baseline_src=942,            # 집 앞면 밑변(원본 y) — 두 장 공통
                  curve="wall"),
    "west": dict(parts=[("raw_west_a.jpg", (384, 0, 1024, 4128))], wrap="y", wrap_overlap=72, curve="wall"),
    "east": dict(parts=[("raw_east_a.jpg", (0, 0, 640, 4128))], wrap="y", wrap_overlap=72, curve="wall"),
    # 남쪽: c 채택(처마선이 끊기지 않음). c 아래 절반(원본 y>340)은 위 절반의 잔상이라 쓰지 않는다.
    "south": dict(parts=[("raw_south_c.jpg", (0, 0, 5856, 340))], wrap="x", wrap_overlap=64,
                  baseline_src=64, bottom_fade=56, curve="fore"),
}

# 골목 입구 조각 (53라운드 Q13). 시트 raw_doors_a.jpg 패널: 1 = 북(아치 골목), 2 = 서(대각 원근 → 미사용), 3 = 남(내려가는 계단)
DOORS = {
    "north": dict(sheet="raw_doors_a.jpg", box=(114, 184, 1111, 1460), scale=0.63, baseline_src=1381,
                  opening_src=(519, 721), curve="wall"),
    "south": dict(sheet="raw_doors_a.jpg", box=(1960, 640, 2600, 1366), scale=0.63, opening_src=(2129, 2439)),
    "west": dict(front_x=1830, south_x=1200, openingH=96, curve="wall"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-mock", action="store_true")
    a = ap.parse_args()
    BK.build_region("outer", HERE, BANDS, DOORS,
                    json_head={"version": "53라운드 시범 확정(Q6) + 골목 입구 조각(Q13)",
                               "source": "parts/art/work/gemini/border_outer/build.py (원본·프롬프트 같은 폴더)"})
    if not a.no_mock:
        import mock
        mock.run()


if __name__ == "__main__":
    main()
