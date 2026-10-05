#!/usr/bin/env python3
"""61라운드 무기 그림 요청(시스템 61 보고) — 결정적.

사용: python3 parts/art/work/weapons61/build.py [--dry] [--only 이름 …]
산출(assets/sprites/…/v3, 트림 아틀라스 — 계약 §19):
  fx/dagger_combo1~3(다시 그림) · fx/dagger_combo1~3_accel2·_accel3(가속 단계 — 새 시트) · fx/hit_dagger·hit_dagger_heavy(불꽃, 다시 그림)
  fx/greatsword_sweep_cw·sweep_ccw·cleave·charge_swing(붓획 + 휘두른 자리 잔상 덧칠)
  fx/bow_arrow(불티 꼬리 · 4프레임 루프)
  player/player_bow_arrow_rain_stand · weapons/bow_arrow_rain_stand(서서 시작하는 화살비 — 새 시트)
  fx/katana_iai_ki1~3(발도 검기 단수별 — 새 시트, 선택 요청)
  fx/dagger_combo1~3_awaken·bow_arrow_awaken(각성 궤적 — 바뀐 기본 시트와 같은 틀·피벗·프레임으로 옮김, 그림 그대로)
  structures/tutorial_dummy(튜토리얼 허수아비 v3 — idle·hit·hit_heavy·broken, 새 시트)
고치기 전 그림은 prev/<분류>/v3/<이름>.png(격자)로 한 번만 보관한다.
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import wk61  # noqa: E402
from wk61 import b2, gridsheet, SPR  # noqa: E402
import k61  # noqa: E402
import dagger61 as DG  # noqa: E402
import gs61  # noqa: E402
import bow61  # noqa: E402
import dummy61  # noqa: E402
import katana61  # noqa: E402
import awaken61  # noqa: E402

PREV = os.path.join(HERE, "prev")


def backup(cat, name):
    jp = os.path.join(SPR, cat, "v3", name + ".json")
    out = os.path.join(PREV, cat, "v3")
    if os.path.exists(os.path.join(out, name + ".png")) or not os.path.exists(jp):
        return
    os.makedirs(out, exist_ok=True)
    gridsheet.open_grid(jp).save(os.path.join(out, name + ".png"))
    with open(os.path.join(out, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(gridsheet.load_meta(jp), f, ensure_ascii=False, indent=1)


def jobs():
    for n in (1, 2, 3):
        for st in (1, 2, 3):
            yield ("fx", lambda n=n, st=st: DG.combo_sheet(n, st), [1], None)
    yield ("fx", lambda: DG.hit_frames(False), [0, 1], None)
    yield ("fx", lambda: DG.hit_frames(True), [0, 1], None)
    for nm in gs61.SHEETS:
        yield ("fx", lambda nm=nm: gs61.enhance(nm), None, None)
    yield ("fx", bow61.arrow_frames, [0, 1, 2, 3], None)
    for lv in (1, 2, 3):
        yield ("fx", lambda lv=lv: katana61.kiframes(lv), None, None)
    for n in (1, 2, 3):
        yield ("fx", lambda n=n: awaken61.recanvas_dagger(n), None, "raw")
    yield ("fx", awaken61.bow_arrow_awaken, None, "raw")
    yield ("structures", dummy61.sheet, None, "struct")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    b2.DRY = a.dry
    stats = {}
    if not a.dry:
        for n in ("dagger_combo1", "dagger_combo2", "dagger_combo3", "hit_dagger", "hit_dagger_heavy", "bow_arrow", "dagger_combo1_awaken", "dagger_combo2_awaken", "dagger_combo3_awaken",
                  "bow_arrow_awaken") + tuple(gs61.SHEETS):
            backup("fx", n)
    for cat, fn, glow, kind in jobs():
        name, rows, fw, fh, meta, ms, loop = fn()
        if a.only and name not in a.only:
            continue
        if kind == "struct":
            ncol = k61.check_frames([f for r in rows for f in r], name, allow_semi=True)
        elif kind == "raw":       # 60라운드 각성 그림(각성 색 상한 24 — 무기 fx 14색 규칙 밖)을 옮기기만
            ncol = k61.check_frames([f for r in rows for f in r], name)
        else:
            g = glow if glow is not None else meta.get("glowFrames", [])
            ncol = wk61.check_weapon_fx(name, rows, g)
        meta = dict(meta)
        meta["colors"] = ncol
        wk61.write(cat, name, rows, fw, fh, meta, ms, loop)
        stats[name] = dict(cat=cat, frame=[fw, fh], rows=len(rows), cols=len(rows[0]), colors=ncol)
        wk61.preview_rows(os.path.join(HERE, "out", "preview_%s.png" % name), rows, 1 if fw > 300 else 2)
        print(name, stats[name])
    if not a.dry and (not a.only or "bow_arrow_rain_stand" in a.only):
        for cat, name in bow61.build_rain_stand():
            b2.WRITTEN.append((cat, name))
            stats[name] = dict(cat=cat)
    if not a.dry:
        for r in k61.to_atlas():
            print("atlas", r)
        p = os.path.join(HERE, "stats.json")
        old = json.load(open(p)) if os.path.exists(p) else {}
        old.update(stats)
        json.dump(old, open(p, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
