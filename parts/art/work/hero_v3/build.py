#!/usr/bin/env python3
# [53라운드 Q73] 목업 속 캐릭터를 v3 그림으로 교체 — 1배 조명 합성의 비교 칸 '결사병 v2'(삭제된 enemies/v2/charger_idle) → '결사병 v3'(enemies/v3/charger_idle, 128×176 pivot (64,170), pixelScale 0.5 = 주인공과 같은 1:1).
"""주인공 v3 전체 시트 빌드 — 53라운드 Q1(1.5배 96×144)·Q4(등 상흔 기준점) 재출력.

최종 산출(게임이 읽음, 계약 §11·§13 v3 경로):
  assets/sprites/player/v3/player_{idle,walk,run,dash,hurt,death,katana_combo1..3,katana_draw,katana_sheathe,katana_special}.png/.json
  assets/sprites/weapons/v3/katana_{combo1..3, draw, sheathe, special, carry_<idle|walk|run|dash>, carry_drawn_<idle|walk|run|dash>}.png/.json
미리보기(이 폴더): preview_<동작>_x2.png · preview_<동작>_x3.gif · preview_mock_lit.png · preview_scar_x3.png · stats.json
모듈: hero.py(몸 Rig·대기·걷기) · motion.py(달리기·대쉬·피격·사망) · katana3.py(칼 3D·휴대·연격·뽑기·넣기·특수)
      anim.py(목록·렌더) · export.py(시트·JSON) · preview.py(미리보기) · v3kit.py(셰이딩 렌더러, 설계 → 도트 1.5배 변환)
사용: python3 parts/art/work/hero_v3/build.py            (전부)
      python3 parts/art/work/hero_v3/build.py walk combo1 (그 동작만 — 시트·미리보기만 다시, stats·목업은 전부일 때만)
"""
import json
import os
import sys

from PIL import Image

import anim
import export as EX
import hero
import katana3 as K
import preview as PV
import v3kit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
DIRS = anim.DIRS
FW, FH = hero.FW, hero.FH


def old_frame(path, fw, fh, col, row, scale=1):
    im = Image.open(path).convert("RGBA").crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))
    return im.resize((fw * scale, fh * scale), Image.NEAREST) if scale != 1 else im


def main(only=None):
    EX.ensure_dirs()
    full = not only
    want = lambda a: full or a in only          # noqa: E731
    hero_colors, weapon_colors, partial, clip, frames_count = set(), set(), False, {}, {}
    keep = {}

    for act in anim.BODY:
        if not want(act):
            continue
        fr = anim.render_body(act)
        keep[act] = fr
        im = EX.export_body(act, fr)
        hero_colors |= v3kit.colors_of(im)
        partial |= v3kit.has_alpha_partial(im)
        frames_count[act] = len(fr["down"])
        comp = {d: [PV.compose(f.image) for f in fr[d]] for d in DIRS}
        ms = anim.BODY[act][1]
        if act in anim.CARRY:
            wim, w = EX.export_carry(act, fr)
            dim, dw = EX.export_carry_drawn(act, fr)
            for x in (wim, dim):
                weapon_colors |= v3kit.colors_of(x)
                partial |= v3kit.has_alpha_partial(x)
            clip["katana_carry_" + act] = EX.edge_pixels(wim)
            clip["katana_carry_drawn_" + act] = EX.edge_pixels(dim)
            keep[act + "_carry"], keep[act + "_drawn"] = w, dw
            comp = {d: [PV.compose(f.image, w[d][i]) for i, f in enumerate(fr[d])] for d in DIRS}
            compd = {d: [PV.compose(f.image, dw[d][i]) for i, f in enumerate(fr[d])] for d in DIRS}
            PV.frames_x2("carry_drawn_" + act, compd, ms)
            PV.gif_x3("carry_drawn_" + act, compd, ms)
        PV.frames_x2(act, comp, ms)
        PV.gif_x3(act, comp, ms)

    jobs = [("combo", n, "katana_combo%d" % n) for n in anim.COMBOS] + [("move", k, "katana_" + k) for k in anim.MOVES]
    for kind, key, name in jobs:
        if not want(name.replace("katana_", "")) and not want(name):
            continue
        fr = anim.render_move(kind, key)
        keep[name] = fr
        if kind == "combo":
            bim, wim = EX.export_combo(key, fr)
            c = K.COMBO[key]
            impact, active = c["impact"], c["active"]
        else:
            bim, wim = EX.export_move(key, fr)
            c = K.MOVES[key]
            impact, active = c.get("holdFrame"), c["phases"].get("window", []) + c["phases"].get("riposte", [])
        hero_colors |= v3kit.colors_of(bim)
        weapon_colors |= v3kit.colors_of(wim)
        partial |= v3kit.has_alpha_partial(bim) or v3kit.has_alpha_partial(wim)
        frames_count["player_" + name] = len(fr["down"])
        clip[name] = sum(EX.edge_pixels(f.weapon) for d in DIRS for f in fr[d])
        comp = {d: [PV.compose(f.body, f.weapon) for f in fr[d]] for d in DIRS}
        PV.frames_x2(name, comp, c["ms"], impact=impact, active=active, states=[f["state"] for f in c["frames"]])
        PV.gif_x3(name, comp, c["ms"])

    if not full:
        print("partial build", sorted(keep), "hero colors (이 동작들)", len(hero_colors), "weapon", len(weapon_colors))
        print("weapon edge pixels", clip)
        return

    # ---- 1배 조명 합성: 64×96 이전 판 · 결사병 v3 · 96×144 새 판 -------------------------
    ref = os.path.join(HERE, "ref_64")
    old = old_frame(os.path.join(ref, "player_idle.png"), 64, 96, 0, 0)
    oldc = Image.new("RGBA", (128, 128))
    oldc.alpha_composite(old, (32, 32))
    oldc.alpha_composite(old_frame(os.path.join(ref, "katana_carry_idle.png"), 128, 128, 0, 0))
    with open(os.path.join(ROOT, "assets/sprites/enemies/v3/charger_idle.json"), encoding="utf-8") as f:
        cj = json.load(f)
    charger = old_frame(os.path.join(ROOT, "assets/sprites/enemies/v3/charger_idle.png"), cj["frameWidth"], cj["frameHeight"], 0, 0)
    cpiv = (cj["pivot"]["x"], cj["pivot"]["y"])   # v3 = pixelScale 0.5 (주인공과 같은 밀도) → 1배 렌더에 1:1
    b, cw, cd = keep["idle"], keep["idle_carry"], keep["idle_drawn"]
    piv = (hero.PIV[0] + K.OFF, hero.PIV[1] + K.OFF)
    spots = [("이전 64×96", oldc, (64, 124), True),
             ("결사병 v3", charger, cpiv, False),
             ("새 대기+칼", PV.compose(b["down"][2].image, cw["down"][2]), piv, True),
             ("걷기(옆)", PV.compose(keep["walk"]["left"][2].image, keep["walk_carry"]["left"][2]), piv, True),
             ("달리기", PV.compose(keep["run"]["right"][1].image, keep["run_carry"]["right"][1]), piv, True),
             ("뽑아 든 칼", PV.compose(b["down"][0].image, cd["down"][0]), piv, True),
             ("1타 판정", PV.compose(keep["katana_combo1"]["down"][2].body, keep["katana_combo1"]["down"][2].weapon), piv, True),
             ("패링", PV.compose(keep["katana_special"]["left"][4].body, keep["katana_special"]["left"][4].weapon), piv, True),
             ("사망 끝", PV.compose(keep["death"]["down"][9].image), piv, False)]
    PV.mock_lit(spots)

    # ---- 등 상흔 기준점 확인 ---------------------------------------------------------------
    sp = []
    for act, i in (("idle", 0), ("walk", 2), ("run", 3), ("dash", 2), ("hurt", 1)):
        for d in ("up", "left", "right", "down"):
            if act != "idle" and d == "down":
                continue
            f = keep[act][d][i]
            sp.append(("%s %s %d" % (act, d, i), PV.compose(f.image), f.rig.scar))
    for name, d, i in (("katana_combo3", "up", 2), ("katana_special", "up", 4), ("katana_combo1", "right", 4)):
        f = keep[name][d][i]
        sp.append(("%s %s %d" % (name.replace("katana_", ""), d, i), PV.compose(f.body, f.weapon), f.rig.scar))
    PV.scar_preview(sp)

    data = {"heroColors": len(hero_colors), "colorBudget": 30, "weaponColors": len(weapon_colors),
            "semiTransparent": partial, "frames": frames_count, "size": [FW, FH], "pivot": list(hero.PIV),
            "pixelScale": 0.5, "weaponSheet": [K.WF, K.WF], "weaponPivot": list(K.WPIV), "weaponEdgePixels": clip,
            "stride": {k: dict(v, naturalSpeed=EX.natural_speed(v)) for k, v in anim.STRIDE.items()},
            "heroPalette": sorted("#%02x%02x%02x" % c for c in hero_colors),
            "weaponPalette": sorted("#%02x%02x%02x" % c for c in weapon_colors)}
    with open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("hero colors", data["heroColors"], "/ 30 · weapon colors", data["weaponColors"], "· semiTransparent", partial)
    print("frames", frames_count)
    print("weapon edge pixels", clip)
    print("stride", data["stride"])


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
