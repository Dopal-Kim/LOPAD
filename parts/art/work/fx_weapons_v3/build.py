#!/usr/bin/env python3
"""무기 이펙트 v3 빌드 (53라운드 Q5 · Q26~Q32 · Q42~Q43 · 51라운드 §1·§4) — 결정적, Gemini 미사용.

산출: assets/sprites/fx/v3/<구 시트와 같은 이름>.png/.json (pixelScale 0.5, 도트 ×4 = 구 시트와 같은 화면 크기)
사용: python3 parts/art/work/fx_weapons_v3/build.py [katana|greatsword|dagger|bow|branch|<시트 이름> …]  (인자 없으면 전부)
      → preview.py 로 미리보기
"""
import json
import os
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import wkit as W                                      # noqa: E402

GROUPS = {}


def registry():
    import defs_katana
    import defs_gs
    reg = {"katana": defs_katana.SHEETS, "greatsword": defs_gs.SHEETS}
    try:
        import defs_dagger
        reg["dagger"] = defs_dagger.SHEETS
    except ImportError:
        pass
    try:
        import defs_bow
        reg["bow"] = defs_bow.SHEETS
    except ImportError:
        pass
    try:
        import branches
        reg["branch"] = branches.SHEETS
    except ImportError:
        pass
    return reg


COOL = {W.hexrgb(W.X0): W.hexrgb(W.A25), W.hexrgb(W.X1): W.hexrgb(W.A25), W.hexrgb(W.A26): W.hexrgb(W.A25)}


def clamp_cool(frames, glow):
    """53라운드 Q27 빛 규칙: 판정(glowFrames) 밖 프레임은 A25 이하 — 남은 백열·A26 을 A25 로."""
    for d, lst in frames.items():
        for i, im in enumerate(lst):
            if i in glow:
                continue
            px = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    c = px[x, y]
                    if c[3] and c[:3] in COOL:
                        px[x, y] = COOL[c[:3]] + (255,)
    return frames


def job(args):
    try:
        return _job(args)
    except Exception as e:                        # noqa: BLE001
        import traceback
        return ("ERR", args[1], traceback.format_exc(limit=3), 0, 0, 0)


def _job(args):
    group, name = args
    reg = registry()
    fn = reg[group][name]
    t0 = time.time()
    res = fn()
    frames, extra = res[0], res[1]
    opts = res[2] if len(res) > 2 else {}
    old = W.old_json(opts.get("old", name))
    import swaps
    extra = dict(extra, **swaps.for_sheet(name, old))
    glow = extra.get("glowFrames") or []
    # 53라운드 Q64: 판정(glowFrames) 밖 프레임은 A25 이하. 루프라도 판정 틱 프레임이 정해진 시트(잔월 등)는 틱 사이 프레임을 낮춘다.
    # 예외: 투사체(화살·꼬리 — 시트 전체가 판정체)와 glowFrames 가 없는 지속 루프(거인 오라·질풍 바람 — 질문 중).
    if glow and old.get("anchor") != "projectile":
        frames = clamp_cool(frames, set(glow))
        extra["glowRule"] = extra.get("glowRule", "") + " (빌드 검사: glowFrames 밖 프레임에는 X0·X1·A26 없음 — A25 이하)"
    sheet, j = W.write_sheet(name, frames, old, extra=extra, swap=opts.get("swap", "none"),
                             pivot=opts.get("pivot"), legacy_note=opts.get("legacyNote"),
                             edge_ok=opts.get("edge_ok", False))
    st = swaps.stale(j)
    assert not st, (name, "구 보조색 hex 가 JSON 에 남음", st)
    cols = W.colors_of(sheet)
    miss = sorted({c["from"] for v in j.get("secondaryVariants", {}).values() for c in v.get("colorSwap", []) if c["from"] not in cols} |
                  {c["from"] for lv in (j.get("heatVariants") or {}).get("colorSwap", {}).values() for c in lv if c["from"] not in cols})
    if miss:
        print("  note", name, "colorSwap from 색이 시트에 없음(그 치환은 효과 없음):", miss)
    return name, j["colors"], j["frameWidth"], j["frameHeight"], j["frames"], round(time.time() - t0, 1)


def main(args):
    reg = registry()
    jobs = []
    for g, sheets in reg.items():
        for n in sheets:
            if not args or g in args or n in args:
                jobs.append((g, n))
    t0 = time.time()
    with Pool(4) as p:
        res = p.map(job, jobs, chunksize=1)
    stats_p = os.path.join(HERE, "stats.json")
    stats = json.load(open(stats_p, encoding="utf-8")) if os.path.exists(stats_p) else {}
    errs = [r for r in res if r[0] == "ERR"]
    res = [r for r in res if r[0] != "ERR"]
    for name, cols, fw, fh, F, sec in res:
        print("%-28s %3dx%-3d f%-2d colors %2d  %.1fs" % (name, fw, fh, F, cols, sec))
        stats[name] = dict(colors=cols, frame=[fw, fh], frames=F)
    with open(stats_p, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(stats.items())), f, ensure_ascii=False, indent=1)
    for e in errs:
        print("FAIL", e[1], e[2])
    print(len(res), "sheets OK,", len(errs), "failed", round(time.time() - t0, 1), "s")
    if errs:
        sys.exit(1)


if __name__ == "__main__":
    main(set(sys.argv[1:]))
