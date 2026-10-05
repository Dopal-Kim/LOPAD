"""61라운드 시스템 D 요청 — 보스 '만취' v3 시트를 1.5배 네이티브 해상도로 다시 그림(최근접 확대 아님).

54라운드 boss1_v3 의 3D 골격·셰이딩 코드(b1body·b1acts)를 그대로 import 하고, 판 크기 상수만 바꿔 다시 래스터한다:
  192×240 · 피벗 (96,220) · SCALE 1.3  →  288×360 · 피벗 (144,330) · SCALE 1.95 (= 1.3 × 1.5)
픽셀 단위 덧칠 배율 K(눈·입·튐 거리)·잔 보임 기준 VIS_MIN 도 같이 바꾼다. 원본 파일은 고치지 않는다(모듈 상수만 이 프로세스에서 바꿈).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
B1 = os.path.normpath(os.path.join(HERE, "..", "boss1_v3"))
sys.path.insert(0, os.path.join(B1, "..", "enemies_v3"))
sys.path.insert(0, B1)

NATIVE = 1.5
import b1body  # noqa: E402

b1body.FW, b1body.FH, b1body.PIV = 288, 360, (144, 330)
b1body.SCALE = 1.3 * NATIVE
b1body.K = b1body.SCALE
b1body.VIS_MIN = int(round(20 * NATIVE * NATIVE))
import b1acts  # noqa: E402  (b1body 상수를 바꾼 뒤 import — from b1body import FW… 가 새 값을 받음)

assert b1acts.FW == 288 and b1acts.PIV == (144, 330)
