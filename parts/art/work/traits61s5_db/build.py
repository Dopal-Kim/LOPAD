#!/usr/bin/env python3
"""61 단계 5 (P13) 개성 전투 fx — 단검·활·공통(공명 켜짐 고리·묶음 사슬 타일). 결정적(시드 고정).

사용: python3 parts/art/work/traits61s5_db/build.py [--publish] [--only 이름부분 ...] [--set dagger bow common]
  기본: out/grid 에 격자 시트 + 미리보기 preview_<set>.png 만(assets 안 건드림)
  --publish: 검사 통과 시 assets/sprites/fx/v3/trait_*.png/json 트림 아틀라스로 게시(atlas57 전 프레임 대조)
요청 원본: parts/system/notes/trait-art-requests-61s5.md §0·§1 (읽기만), 계약 art §27.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import tk  # noqa: E402
import tview  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--set", nargs="*", default=["dagger", "bow", "common"])
    a = ap.parse_args()
    mods = {}
    if "dagger" in a.set:
        import fx_dagger
        mods["dagger"] = fx_dagger.ALL
    if "bow" in a.set:
        import fx_bow
        mods["bow"] = fx_bow.ALL
    if "common" in a.set:
        import fx_common
        mods["common"] = fx_common.ALL
    stats = {}
    for key, fns in mods.items():
        start = len(tk.SHEETS)
        for fn in fns:
            fn()
        items = tk.SHEETS[start:]
        if a.only:
            items = [it for it in items if any(o in it[0] for o in a.only)]
        board = []
        for name, rows, meta in items:
            allowed = tk.ALLOWED_TAGS if key == "common" else tk.ALLOWED_BASE
            meta["colors"] = tk.check(name, rows, meta, allowed, cap=16 if key != "common" else 18)
            tk.write_grid(name, rows, meta)
            board.append((name, rows, meta))
            fw, fh = rows[0][0].size
            stats[name] = dict(frame=[fw, fh], frames=len(rows[0]), rows=len(rows), colors=meta["colors"])
        if board:
            size = tview.sheet_board(board, os.path.join(HERE, "preview_%s.png" % key))
            print("preview_%s.png" % key, size, len(board), "시트")
    if not a.only and len(tk.SHEETS) > 40:
        print("preview_dark.png", tview.dark_board([(n, [[c for c in r] for r in rows], m) for n, rows, m in tk.SHEETS],
                                                  os.path.join(HERE, "preview_dark.png")))
    if a.publish:
        names = sorted(stats)
        log = tk.publish(names)
        tot = sum(x["gpuMB"] for x in log)
        big = max(log, key=lambda x: x["gpuMB"])
        print("publish %d 시트, 아틀라스 RGBA 합 %.2fMB, 최대 %s %.2fMB" % (len(log), tot, big["name"], big["gpuMB"]))
        with open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8") as f:
            json.dump({"sheets": stats, "publish": log}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
