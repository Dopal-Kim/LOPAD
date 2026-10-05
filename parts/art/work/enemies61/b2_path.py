"""bundle2(b2·structs)·boss1_v3(props) import 경로 정리 — 61라운드 빌드 공용."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in ("../bundle2", "../boss1_v3"):
    q = os.path.normpath(os.path.join(HERE, p))
    if q not in sys.path:
        sys.path.insert(0, q)
