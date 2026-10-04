"""작업 중 빠른 실행: python3 run.py <모듈> [이름...]  → 격자 원본 빌드(병렬) + 미리보기(preview_<모듈>.png · gif/)."""
import importlib
import os
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def build(mod, names=None, preview=False):
    M = importlib.import_module(mod)
    names = names or M.NAMES
    with Pool(8) as p:
        for r in p.imap_unordered(M.job, names):
            print(r, flush=True)
    if preview:
        import pv57
        print(pv57.sheet_preview(names, os.path.join(pv57.K.HERE, "preview_%s.png" % mod)))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2:] or None, preview=True)
