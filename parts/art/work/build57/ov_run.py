"""각성 무기 오버레이 일괄 빌드: python3 ov_run.py [시트 이름 부분...]"""
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fx_awaken as A  # noqa: E402

def build(flt=None):
    jobs = [s for s in A.SHEETS if not flt or any(f in s[1] for f in flt)]
    with Pool(8) as p:
        for r in p.imap_unordered(A.overlay_job, jobs):
            print(r, flush=True)


if __name__ == "__main__":
    build(sys.argv[1:])
