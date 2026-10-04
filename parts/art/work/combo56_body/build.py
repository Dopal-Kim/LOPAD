#!/usr/bin/env python3
"""56라운드 작업 B 빌드 (Q4 단검 · Q5 대검 무게 · Q6 대검 8방향 · Q9 활 · Q10 대검 차지) — 결정적, Gemini 미사용.

  gs      대검 몸·무기 8방향 6동작(gs56.py)                    → player/v3/player_greatsword_*, weapons/v3/greatsword_*
  fx      바닥 균열 s/m/l · 꽂아내리기 충격파 · 완벽 놓기 섬광(fx56.py) → fx/v3/greatsword_ground_crack, greatsword_plunge_wave, bow_perfect_release
  dagger  단검 1.3배 재출력 + 찌르기 판정 참고값 ×1.5(dagger56.py) → weapons/v3/dagger_*, player_dagger_combo1~3.json(hitReference56)
  bow     활 당기기 유지 · 놓기(bow56.py)                     → player/v3/player_bow_{draw_hold,release}, weapons/v3/bow_{draw_hold,release}
  preview 미리보기·GIF(preview56.py, dagger_compare.py)
사용: python3 parts/art/work/combo56_body/build.py [gs] [fx] [dagger] [bow] [preview]   (인자 없으면 전부)
각 단계는 별도 프로세스(단검·8방향이 hero_v3/weapons_v3 모듈을 프로세스 안에서만 바꾸므로 서로 섞이지 않게).
주의: combo55/build.py body 를 다시 돌리면 대검 시트가 55라운드 4방향판으로 덮인다 — 대검은 이 빌드가 기준.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = {
    "gs": "import gs56; gs56.build()",
    "fx": "import fx56; fx56.build_all()",
    "dagger": "import dagger56; print(dagger56.build())",
    "bow": "import bow56; bow56.build()",
    "preview": "import preview56 as P, dagger_compare as D; P.main(); P.main_bow(); D.main()",
}


def run(step):
    t0 = time.time()
    subprocess.run([sys.executable, "-c", STEPS[step]], cwd=HERE, check=True)
    print("== %s %.1fs" % (step, time.time() - t0))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a in STEPS] or list(STEPS)
    for s in args:
        run(s)
