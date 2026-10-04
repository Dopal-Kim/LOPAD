#!/usr/bin/env python3
"""56라운드 작업 D 빌드 — 자원·가드·그로기 표시 + 대검 이펙트 8행 정리. 결정적, Gemini 미사용(키아트는 참고만).

  gs8      Q30 대검 이펙트 8행 통일 — fx/v3/greatsword_{sweep_cw,sweep_ccw,cleave,charge_slam_lv1~3}.json 에 directionRows·timingCheck
           (PNG 는 작업 A 그대로 — 이미 8행)                                                                  gs8.py
  arrow    Q26 약한 화살 fx/v3/bow_arrow_weak                                                                   arrow.py
  flipmask Q55 공중제비 도약 찍기 bodyInOverlayFrames 칸의 '칼만' 마스크(E1 렌더 재현) → flipmask_greatsword_leap_slam.png  flipmask.py
  overlay  Q14 검기 weapons/v3/<칼 시트>_ki1~3 · Q15 울분 weapons/v3/<대검 시트>_grudge1~3                      overlay.py
           (Q55: 새 칼·대검 기본기 6종 + 게임이 쓰는 옛 칼 시트 draw·sheathe·special 포함 — overlay.KATANA_SHEETS/GS_SHEETS)
  brand    Q16·Q19 fx/v3/dagger_brand_mark · dagger_brand_burst · dagger_overheat_burst · dagger_overheat_cool      brand.py
  guard    Q7 fx/v3/guard_perfect_fx                                                                           guard.py
  groggy   Q7·Q18 player/v3/player_groggy · weapons/v3/{katana,greatsword}_carry_groggy · fx/v3/player_groggy_swirl groggy.py
  preview  미리보기 PNG·GIF(이 폴더, gif/)                                                                    prev_res.py
  preview55 Q55 새 동작 오버레이 미리보기(preview_q55_*.png, gif/q55_*.gif)                                   prev_q55.py
사용: python3 parts/art/work/combo56_res/build.py [단계 …] [시트 이름 …]   (인자 없으면 전부)
      overlay 는 시트 이름을 주면 그 시트만(예: build.py overlay katana_rise) — E1 이 새 칼·대검 시트를 내면 overlay.KATANA_SHEETS /
      GS_SHEETS 에 이름을 더하고 다시 돌린다.
각 단계는 별도 프로세스(groggy 가 hero_v3/weapons_v3 모듈 경로를 넣으므로 섞이지 않게).
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = {
    "gs8": "import gs8; print('\\n'.join(gs8.build()))",
    "arrow": "import arrow; arrow.build(); print('bow_arrow_weak ok')",
    "flipmask": "import flipmask; print('\\n'.join(flipmask.build()))",
    "overlay": "import overlay, sys; print(len(overlay.build(set(sys.argv[1:]) or None)), 'overlay sheets')",
    "brand": "import brand; print(brand.build())",
    "guard": "import guard; guard.build(); print('guard_perfect_fx ok')",
    "groggy": "import groggy; groggy.build(); print('groggy ok')",
    "preview": "import prev_res; print('\\n'.join(prev_res.main()))",
    "preview55": "import prev_q55; print('\\n'.join(prev_q55.main()))",
}


def run(step, extra):
    t0 = time.time()
    subprocess.run([sys.executable, "-c", STEPS[step]] + (extra if step == "overlay" else []), cwd=HERE, check=True)
    print("== %s %.1fs" % (step, time.time() - t0))


if __name__ == "__main__":
    args = sys.argv[1:]
    steps = [a for a in args if a in STEPS] or list(STEPS)
    extra = [a for a in args if a not in STEPS]
    for s in steps:
        run(s, extra)
