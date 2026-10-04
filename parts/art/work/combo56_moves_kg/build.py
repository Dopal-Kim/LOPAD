#!/usr/bin/env python3
"""56라운드 작업 E1 빌드 — 새 기본기 6종(칼 2 · 대검 4) 몸·무기·fx. 결정적, Gemini 미사용(키아트 gemini/weapon_moves 는 참고만).

  katana   칼 몸·무기 4방향(kg_katana.py)     → player/v3/player_katana_{counter,iai} · weapons/v3/katana_{counter,iai}
  gs       대검 몸·무기 8방향(kg_gs.py)       → player/v3/player_greatsword_{tackle,brace_upswing,leap_slam,guard_rush} · weapons/v3/같은 이름
  fx       이펙트(kg_fx.py — 몸 JSON 타이밍을 읽으므로 katana·gs 뒤)
           → fx/v3/katana_counter · katana_iai · katana_iai_ready · greatsword_tackle · greatsword_brace_upswing(_ember) ·
             greatsword_brace_absorb · greatsword_leap_slam · greatsword_leap_slam_land · greatsword_guard_rush
  preview  미리보기 PNG(preview_<동작>_x1|x2.png) · GIF(gif/<동작>.gif)
사용: python3 parts/art/work/combo56_moves_kg/build.py [katana] [gs] [fx] [preview]   (인자 없으면 전부)
각 단계는 별도 프로세스(칼·대검이 combo55/hero_v3 모듈을 프로세스 안에서만 바꾸므로 섞이지 않게).
기존 시트(다른 작업 소유)는 쓰지 않는다 — 새 이름만 만든다.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = {
    "katana": "import kg_katana; kg_katana.build()",
    "gs": "import kg_gs; kg_gs.build()",
    "fx": "import kg_fx; kg_fx.build()",
    "preview": "import kg_preview; kg_preview.main()",
}


def run(step):
    t0 = time.time()
    subprocess.run([sys.executable, "-c", STEPS[step]], cwd=HERE, check=True)
    print("== %s %.1fs" % (step, time.time() - t0))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a in STEPS] or list(STEPS)
    for s in args:
        run(s)
