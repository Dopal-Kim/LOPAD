"""61라운드 아트 빌드 — 신규 적 2종 + 굴러가는 술통 + 서사 소품 3종 (단일 진입점).

    python3 parts/art/work/enemies61/build.py [--dry] [--skip-enemies] [--skip-structs]

순서: 1) enemy_build.py --assets (peddler·porter × idle/walk/attack/hurt/death → 격자 → atlas57)
      2) 구조물(porter_rolling_barrel·_returned·porter_barrel_break·clue_*) → 격자 → atlas57 (bundle2/b2 write_sheet·to_atlas)
      3) 엘리트 외곽선: python3 parts/art/work/bundle2/build.py --only elite (bundle2/elite.py ENEMIES 에 두 적 포함 — 따로 실행)
      4) 미리보기 preview_*.png (긴 변 8000 이하)
--dry: assets 에 쓰지 않고 미리보기만.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def main():
    dry = "--dry" in sys.argv
    if "--skip-enemies" not in sys.argv:
        cmd = [sys.executable, os.path.join(HERE, "enemy_build.py")] + ([] if dry else ["--assets"])
        subprocess.check_call(cmd)
    if "--skip-structs" not in sys.argv:
        import b2_path  # noqa: F401
        import b2
        b2.DRY = dry
        import barrel61
        import clues61
        prev = barrel61.build([])
        b2.preview(os.path.join(HERE, "preview_barrels.png"), prev, k=3, max_w=900)
        cp = []
        for fn in clues61.ALL:
            fr, piv = fn()
            cp += [(f, piv) for f in fr]
        b2.preview(os.path.join(HERE, "preview_clues.png"), cp, k=3, max_w=1300)
        if not dry:
            for cat, name, src, pages in b2.to_atlas():
                print(f"{cat}/v3/{name}: 격자 {src[0]}x{src[1]} -> 아틀라스 " + ", ".join(f"{w}x{h}" for w, h in pages))


if __name__ == "__main__":
    main()
