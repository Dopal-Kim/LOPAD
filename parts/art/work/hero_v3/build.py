#!/usr/bin/env python3
"""주인공 v3 전체 시트 빌드 (52라운드 Q7·Q8·Q10·Q12) — 1단계 대기 6·걷기 8 + 2단계 달리기 8·대쉬 5·칼 연격 3종·피격 3·사망 10 × 4방향.

최종 산출(게임이 읽음, 계약 §11 v3 경로):
  assets/sprites/player/v3/player_{idle,walk,run,dash,hurt,death,katana_combo1..3}.png/.json
  assets/sprites/weapons/v3/katana_{combo1..3, carry_idle, carry_walk, carry_run, carry_dash}.png/.json
미리보기(이 폴더): preview_<동작>_x2.png · preview_<동작>_x3.gif · preview_mock_lit.png · preview_compare_v1_v2.png · stats.json
모듈: hero.py(몸 Rig·대기·걷기) · motion.py(달리기·대쉬·피격·사망) · katana3.py(칼 3D·휴대·연격) · anim.py(목록·렌더)
      export.py(시트·JSON) · preview.py(미리보기) · v3kit.py(셰이딩 렌더러)
사용: python3 parts/art/work/hero_v3/build.py
"""
import json
import os

from PIL import Image, ImageDraw

import anim
import export as EX
import hero
import katana3 as K
import preview as PV
import v3kit

HERE = os.path.dirname(os.path.abspath(__file__))
DIRS = anim.DIRS
FW, FH = hero.FW, hero.FH


def compare_v1(body):
    """1차본(ref_v1/, 커밋 2710d7d 출력 사본)과 현재본 — 대기 0 · 걷기 2 · 걷기 6, 4방향, 2배 (1단계 검수 기록 유지)."""
    k, pad = 2, 8
    v1 = {a: Image.open(os.path.join(HERE, "ref_v1", "player_%s_v1.png" % a)) for a in ("idle", "walk")}
    picks = [("idle", 0), ("walk", 2), ("walk", 6)]
    W = 70 + len(picks) * 2 * (FW * k + pad) + len(picks) * 12
    H = 30 + len(DIRS) * (FH * k + pad)
    out = Image.new("RGBA", (W, H), PV.BG)
    d = ImageDraw.Draw(out)
    for j, dname in enumerate(DIRS):
        y = 30 + j * (FH * k + pad)
        PV.label(d, 6, y + FH * k // 2 - 8, dname)
        for i, (act, fi) in enumerate(picks):
            x = 70 + i * (2 * (FW * k + pad) + 12)
            if j == 0:
                PV.label(d, x, 6, "%s %d: 1차 | 2차" % (act, fi))
            old = v1[act].crop((fi * FW, j * FH, (fi + 1) * FW, (j + 1) * FH))
            out.alpha_composite(old.resize((FW * k, FH * k), Image.NEAREST), (x, y))
            out.alpha_composite(body[act][dname][fi].image.resize((FW * k, FH * k), Image.NEAREST), (x + FW * k + pad, y))
    out.save(os.path.join(HERE, "preview_compare_v1_v2.png"))


def main():
    EX.ensure_dirs()
    body = {act: anim.render_body(act) for act in anim.BODY}
    combos = {n: anim.render_combo(n) for n in anim.COMBOS}
    hero_colors, weapon_colors, partial, clip = set(), set(), False, {}
    frames_count = {}

    for act, fr in body.items():
        im = EX.export_body(act, fr)
        hero_colors |= v3kit.colors_of(im)
        partial |= v3kit.has_alpha_partial(im)
        frames_count[act] = len(fr["down"])
        comp = {d: [PV.compose(f.image) for f in fr[d]] for d in DIRS}
        if act in anim.CARRY:
            wim, w = EX.export_carry(act, fr)
            weapon_colors |= v3kit.colors_of(wim)
            partial |= v3kit.has_alpha_partial(wim)
            clip["katana_carry_" + act] = EX.edge_pixels(wim)
            comp = {d: [PV.compose(f.image, w[d][i]) for i, f in enumerate(fr[d])] for d in DIRS}
        ms = anim.BODY[act][1]
        PV.frames_x2(act, comp, ms)
        PV.gif_x3(act, comp, ms)

    for n, fr in combos.items():
        bim, wim = EX.export_combo(n, fr)
        hero_colors |= v3kit.colors_of(bim)
        weapon_colors |= v3kit.colors_of(wim)
        partial |= v3kit.has_alpha_partial(bim) or v3kit.has_alpha_partial(wim)
        frames_count["katana_combo%d" % n] = len(fr["down"])
        # 프레임 단위 잘림 점검(가장자리 픽셀)
        clip["katana_combo%d" % n] = sum(EX.edge_pixels(f.weapon) for d in DIRS for f in fr[d])
        c = K.COMBO[n]
        comp = {d: [PV.compose(f.body, f.weapon) for f in fr[d]] for d in DIRS}
        PV.frames_x2("katana_combo%d" % n, comp, c["ms"], impact=c["impact"], active=c["active"],
                     states=[f["state"] for f in c["frames"]])
        PV.gif_x3("katana_combo%d" % n, comp, c["ms"])

    # 외곽 바닥 위 1배 조명 합성
    carry_idle, _ = anim.render_carry("idle", body["idle"])
    carry_run, _ = anim.render_carry("run", body["run"])
    c1 = combos[1]
    spots = [("대기+칼", PV.compose(body["idle"]["down"][2].image, carry_idle["down"][2]), True),
             ("달리기", PV.compose(body["run"]["right"][3].image, carry_run["right"][3]), True),
             ("대쉬", PV.compose(body["dash"]["left"][2].image), True),
             ("1타 판정", PV.compose(c1["down"][2].body, c1["down"][2].weapon), True),
             ("3타 판정", PV.compose(combos[3]["right"][2].body, combos[3]["right"][2].weapon), True),
             ("피격", PV.compose(body["hurt"]["up"][0].image), True),
             ("사망 끝", PV.compose(body["death"]["down"][9].image), False)]
    PV.mock_lit(spots)
    compare_v1(body)

    data = {"heroColors": len(hero_colors), "colorBudget": 30, "weaponColors": len(weapon_colors),
            "semiTransparent": partial, "frames": frames_count, "size": [FW, FH], "pivot": list(hero.PIV),
            "pixelScale": 0.5, "weaponSheet": [K.WF, K.WF], "weaponPivot": list(K.WPIV), "weaponEdgePixels": clip,
            "heroPalette": sorted("#%02x%02x%02x" % c for c in hero_colors),
            "weaponPalette": sorted("#%02x%02x%02x" % c for c in weapon_colors)}
    with open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("hero colors", data["heroColors"], "/ 30 · weapon colors", data["weaponColors"], "· semiTransparent", partial)
    print("frames", frames_count)
    print("weapon edge pixels", clip)


if __name__ == "__main__":
    main()
