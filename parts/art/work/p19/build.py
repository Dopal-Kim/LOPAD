"""P19 1-A 아트 · 전장 — 단일 진입점.

    python3 parts/art/work/p19/build.py [--skip-tiles] [--skip-props] [--skip-enemies] [--skip-fx] [--skip-mock]

순서
1) tiles4.py   → assets/tiles/v4/stage1_<outer|gate|brewery|hall|waste>.png/.json (칸 0~95 = v2 복사, 96~ = v4 새 그림)
2) props19.py  → assets/sprites/structures/v3/stage_* (무대 중심 7) · hazard_* (위험물 3) — 트림 아틀라스
3) enemy19.py  → assets/sprites/enemies/v3/{drummer,bomber}_<동작>(+_rim) — 트림 아틀라스
4) fx19.py     → assets/sprites/fx/v3/react_* · tele_* · drum_aura — 트림 아틀라스(반복 선 2종은 tile:true 트림 안 함)
5) scene19.py  → shots/<형태>_z175·_z160.png, preview_shapes.png, luminance.json, lighting_proposal.json (형태 9 목업 + 휘도)
필요: Pillow, numpy, scipy (pip install numpy scipy). Gemini 미사용(이번 범위는 모두 직접 도트).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [("tiles", ["tiles4.py"]), ("props", ["props19.py"]), ("enemies", ["enemy19.py", "--assets"]), ("fx", ["fx19.py"]),
         ("mock", ["scene19.py"])]

if __name__ == "__main__":
    for key, cmd in STEPS:
        if "--skip-" + key in sys.argv:
            continue
        print("==", key)
        subprocess.check_call([sys.executable, os.path.join(HERE, cmd[0])] + cmd[1:], cwd=HERE)
