#!/usr/bin/env python3
"""무기 v3 오버레이 빌드 (53라운드 Q19·Q26~Q32) — 결정적, Gemini 미사용.

산출:
  assets/sprites/player/v3/player_{idle,walk,run}_free.png/.json        왼손이 빈 기본 자세(칼 외 무기)
  assets/sprites/player/v3/player_greatsword_*.png/.json                2차 몸 시트 재출력(weaponOverlayV3 연결, 뽑기·넣기 끝 = idle_free)
  assets/sprites/weapons/v3/dagger_{combo1..3,special,carry_*}.png/.json · player_dagger_* 재출력(weaponOverlayV3 연결)
  assets/sprites/weapons/v3/greatsword_{combo1..3,dashslash,slam,draw,sheathe,special,carry_*,carry_drawn_*}.png/.json
칼 B 는 hero_v3/katana3.py 에서 그린다(python3 parts/art/work/hero_v3/build.py).
사용: python3 parts/art/work/weapons_v3/build.py [free] [greatsword] (인자 없으면 전부)
"""
import json
import os
import sys

import wv3
from wv3 import DIRS, EX, Q, anim, hero, colors_of, has_alpha_partial
import greatsword as GS
import dagger as DG

HERE = wv3.HERE
STATS = {}


def note_colors(weapon, imgs_list):
    s = STATS.setdefault(weapon, dict(colors=set(), partial=False, edge=0))
    for imgs in imgs_list:
        for d in DIRS:
            for f in imgs[d]:
                s["colors"] |= colors_of(f)
                s["partial"] |= has_alpha_partial(f)
                s["edge"] += EX.edge_pixels(f)


def build_free():
    out = {}
    for act in wv3.FREE:
        fr = wv3.render_free(act)
        im = wv3.export_free(act, fr)
        assert colors_of(im) <= wv3.hero_palette(), act
        out[act] = fr
        print("player_%s_free ok" % act)
    out["dash"] = anim.render_body("dash")
    return out


def body_imgs(fr):
    return {d: [f.image for f in fr[d]] for d in DIRS}


def build_carry(weapon, mod, bodies, kinds):
    """kinds: [(접미사, 프레임 함수(d, act, i, R) → (RGBA, 끝), 설명)]"""
    res = {}
    for act in ("idle", "walk", "run", "dash"):
        fr = bodies[act]
        _, ms, loop = anim.BODY[act]
        hands = {d: [anim.hands_px(f.rig) for f in fr[d]] for d in DIRS}
        for suffix, fn, extra in kinds:
            imgs, tips = {}, {}
            for d in DIRS:
                pairs = [fn(d, act, i, f.rig) for i, f in enumerate(fr[d])]
                imgs[d] = [p[0] for p in pairs]
                tips[d] = [None if p[1] is None else wv3.to_w(hero.to_px(p[1])) for p in pairs]
            name = "%s_carry%s_%s" % (weapon, suffix, act)
            ex = dict(extra(act), bodySheet=wv3.BODY_RULE[weapon][act], bodySheetByWeapon={w: r[act] for w, r in wv3.BODY_RULE.items()},
                      bodySheetRuleNote=wv3.BODY_RULE_NOTE, bladeTipAnchors=tips,
                      overlay="%s 와 같은 프레임 번호를 같은 시각에 겹친다. 피벗 (96,186) = 주인공 피벗 (48,138)." % wv3.BODY_RULE[weapon][act])
            wv3.write_overlay(name, imgs, ms, loop, "carry%s_%s" % (suffix, act), weapon, hands,
                              ex.pop("gripHand", "handR"), mod.DESIGN, extra=ex)
            note_colors(weapon, [imgs])
            wv3.previews(name, body_imgs(fr), imgs, ms, gif=True)
            res[name] = (fr, imgs)
            print(name, "ok")
    return res


def build_gear(weapon, mod, names, carry_hidden):
    res = {}
    for name in names:
        r = Q.render(name)
        imgs, tips = {}, {}
        for d in DIRS:
            pairs = [mod.gear_frame(d, name, f[4], f[1]) for f in r["frames"][d]]
            imgs[d] = [p[0] for p in pairs]
            tips[d] = [None if p[1] is None else wv3.to_w(hero.to_px(p[1])) for p in pairs]
        wname = Q.OLD_WEAPON[name]
        EX.sheet(imgs, wv3.K.WF, wv3.K.WF).save(os.path.join(EX.OUT_W, wname + ".png"))   # 먼저 두어야 몸 JSON 이 weaponOverlayV3 를 건다
        _, data = wv3.E2.export_gear(name, r)
        assert data["weaponOverlayV3"] == "weapons/v3/" + wname
        chk = wv3.check_gear_timing(name, r["ms"], data)
        hands = data["handAnchors"]
        ex = dict(bladeLocal=data["weaponLocal"], bladeLocalNote="몸 기준 무기 방향(θ: 0 = 앞, + = 해부 오른쪽 · elev: + = 위). null = 대기 0 그림(휴대).",
                  bladeTipAnchors=tips, bladeTipNote="무기 끝(무기 시트 좌표) — 이펙트 위치 참고",
                  bodySheet="player_" + name, timingCheck=chk, includesSheath=False, carryHidden=carry_hidden,
                  overlay="player_%s 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 (96,186) = 주인공 피벗 (48,138)." % name,
                  stateNote="steel 평소(균열·홈 1px 은은) · glow 판정 프레임(밝게) · fade 흐림 · embers 불티 · idle 대기 0 그림")
        if data.get("endsWith"):
            ex["endsWith"] = data["endsWith"].replace("player_idle_free", "player_idle_free + %s_carry%s_idle" %
                                                      (weapon, "" if name.endswith("sheathe") else "_drawn"))
        wv3.write_overlay(wname, imgs, r["ms"], False, data.get("action", name), weapon, hands, "handR", mod.DESIGN,
                          extra=ex, body_meta=data)
        note_colors(weapon, [imgs])
        bodies = {d: [f[0] for f in r["frames"][d]] for d in DIRS}
        act = data.get("activeFrames") or ([data["holdFrame"]] if data.get("holdFrame") is not None else [])
        wv3.previews(wname, bodies, imgs, r["ms"], states=data["frameStates"], active=act, impact=data.get("impactFrame"))
        res[wname] = (bodies, imgs, data)
        print(wname, len(r["ms"]), "frames ok · timing", chk["checked"])
    return res


DG_NAMES = ["dagger_combo1", "dagger_combo2", "dagger_combo3", "dagger_special"]
GS_NAMES = ["greatsword_combo1", "greatsword_combo2", "greatsword_combo3", "greatsword_dashslash", "greatsword_slam",
            "greatsword_draw", "greatsword_sheathe", "greatsword_special"]


def main(only=None):
    EX.ensure_dirs()
    want = lambda a: not only or a in only          # noqa: E731
    bodies = build_free() if (want("free") or want("greatsword") or want("dagger")) else None
    keep = {}
    if want("greatsword"):
        keep.update(build_carry("greatsword", GS, bodies, [
            ("", lambda d, act, i, R: GS.back_frame(d, R),
             lambda act: dict(carry="back, leather strap (등에 비스듬히 — 손잡이 오른어깨 위, 날 왼허리 뒤)", state="sheathed",
                              bladeLocal={"thetaDeg": GS.BACK_TH, "elevDeg": GS.BACK_EL}, gripHand=None)),
            ("_drawn", lambda d, act, i, R: GS.drawn_frame(d, act, i, R),
             lambda act: dict(carry="drawn, right hand (오른손 한 손으로 낮게 끎)", state="drawn",
                              bladeLocal={"thetaDeg": GS.DRAWN[act][0], "elevDeg": GS.DRAWN[act][1]},
                              stateNote="공격 뒤 넣기 전(비전투 타이머 동안) greatsword_carry_* 대신 사용."))]))
        keep.update(build_gear("greatsword", GS, GS_NAMES,
                               "이 시트 동안 greatsword_carry_* 는 숨긴다(등의 대검이 손으로 옮겨짐 — draw 첫 프레임·sheathe 끝 프레임은 이 시트가 등의 대검을 그림)."))
    if want("dagger"):
        keep.update(build_carry("dagger", DG, bodies, [
            ("", lambda d, act, i, R: DG.carry_frame(d, act, i, R),
             lambda act: dict(carry="hand, reverse grip (오른손 역수 — 날이 팔뚝을 따라 뒤로)", state="inHand",
                              bladeLocal={"thetaDeg": DG.CARRY[act][0], "elevDeg": DG.CARRY[act][1]}))]))
        keep.update(build_gear("dagger", DG, DG_NAMES, "이 시트 동안 dagger_carry_* 는 숨긴다(이 시트가 손의 단검을 그림)."))
    pal = wv3.hero_palette()
    for w, s in STATS.items():
        outside = s["colors"] - pal
        print(w, "colors", len(s["colors"]), "/ 16 · outside hero palette", sorted("#%02x%02x%02x" % c for c in outside),
              "· partial", s["partial"], "· edge px", s["edge"])
        assert len(s["colors"]) <= 16 and not outside and not s["partial"], w
    if not only:
        with open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8") as f:
            json.dump({w: dict(colors=len(s["colors"]), palette=sorted("#%02x%02x%02x" % c for c in s["colors"]),
                               edgePixels=s["edge"]) for w, s in STATS.items()}, f, ensure_ascii=False, indent=1)
    return keep


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
