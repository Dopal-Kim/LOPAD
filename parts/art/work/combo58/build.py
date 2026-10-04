#!/usr/bin/env python3
"""58라운드 무기 피드백 2(칼·대검) 아트 빌드 — 결정적, Gemini 미사용.

  katana    Q1 칼 3타 찌르기 katana_thrust · 대쉬 일섬 katana_issen_dash (몸·무기, 4행)          k58.py
  kfx       Q1 찌르기 붓획 fx katana_thrust + _ki1~3(검기 단수별 사거리)                         kfx58.py
  gs        Q4 진짜 3/4 대각 리그로 대검 10시트 재출력(4행은 픽셀 그대로) + Q3 greatsword_charge_swing  gs58.py (rig34.py)
  flipmask  공중제비(leap_slam) 몸 든 칸의 칼 마스크 — 3/4 리그로 다시(combo56_res/flipmask.py)
  gsfx      Q3 휘둘러 내리찍기 붓획 fx(8행) · 균열 선 greatsword_charge_crack_line_t1~t5              gsfx58.py
  overlay   검기 _ki1~3(칼 새 2시트) · 울분 _grudge1~3(대검 11시트)                                 ov58.py (combo56_res/overlay.py)
  atlas     atlas57 파이프라인 --in-place(격자로 나온 시트만 변환 · 전 프레임 대조)                   ../atlas57/build.py
  preview   preview/ 미리보기 PNG·GIF                                                              preview58.py (diag 비교는 56 판 백업 폴더 인자)
순서가 중요: gs → flipmask → gsfx(몸 JSON 타이밍을 읽음) → overlay → atlas. 각 단계는 별도 프로세스(리그·투영 패치가 프로세스 안에서만 걸림).
점검: check4.py <56 판 백업 폴더> <시트…> — 다시 낸 대검 시트의 기존 4행이 56 판과 픽셀 같음(틀이 늘면 offset 만큼 옮겨 대조).
사용: python3 parts/art/work/combo58/build.py [단계 …]   (인자 없으면 preview 를 뺀 전부)
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
STEPS = {
    "katana": [sys.executable, "-c", "import k58; k58.build()"],
    "kfx": [sys.executable, "kfx58.py"],
    "gs": [sys.executable, "gs58.py", "combo", "kg", "swing"],
    "flipmask": [sys.executable, "-c", "import sys; sys.path.insert(0,'.'); import rig34; rig34.install(); "
                                       "sys.path.insert(0,'../combo56_res'); import flipmask; print(len(flipmask.build()), 'flip cells')"],
    "gsfx": [sys.executable, "gsfx58.py"],
    "overlay": [sys.executable, "ov58.py"],
    "atlas": [sys.executable, os.path.join(ROOT, "parts/art/work/atlas57/build.py"), "--in-place", "--cats", "player,weapons,fx"],
    "preview": [sys.executable, "preview58.py"],
}
DEFAULT = ["katana", "kfx", "gs", "flipmask", "gsfx", "overlay", "atlas"]


if __name__ == "__main__":
    steps = [a for a in sys.argv[1:] if a in STEPS] or DEFAULT
    for s in steps:
        t0 = time.time()
        subprocess.run(STEPS[s], cwd=HERE, check=True)
        print("== %s %.1fs" % (s, time.time() - t0))
