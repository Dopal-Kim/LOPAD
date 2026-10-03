#!/usr/bin/env python3
"""무기 v3 오버레이 빌드 (53라운드 Q19·Q26~Q32·Q44~Q46) — 결정적, Gemini 미사용.

산출:
  assets/sprites/player/v3/player_{idle,walk,run}_free.png/.json        왼손이 빈 기본 자세(칼 외 무기)
  assets/sprites/player/v3/player_{greatsword_*,dagger_*,bow_aim,bow_reload,attack}.png/.json   2차 몸 재출력(weaponOverlayV3 연결)
  assets/sprites/weapons/v3/greatsword_{combo1..3,dashslash,slam,draw,sheathe,special,carry_*,carry_drawn_*}  ← 대검만 확대 틀(Q45)
  assets/sprites/weapons/v3/dagger_{combo1..3,special,carry_*}
  assets/sprites/weapons/v3/bow_{aim,reload,attack,carry_*}
칼 B 는 hero_v3/katana3.py 에서 그린다(python3 parts/art/work/hero_v3/build.py).
사용: python3 parts/art/work/weapons_v3/build.py [free] [greatsword] [dagger] [bow] (인자 없으면 전부) → compare.py
"""
import json
import os
import sys

import wv3
from wv3 import DIRS, EX, Q, anim, hero, colors_of, has_alpha_partial
import bow as BW
import dagger as DG
import greatsword as GS

HERE = wv3.HERE
STATS = {}


def note_colors(weapon, imgs, frame):
    s = STATS.setdefault(weapon, dict(colors=set(), partial=False, edge=0, frame=list(frame)))
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


def carry_jobs(weapon, bodies, kinds):
    """kinds: [(접미사, 프레임 함수(d, act, i, R) → (RGBA, 끝 설계 좌표 | None), 추가 필드 함수)] → 작업 목록."""
    jobs = []
    for act in ("idle", "walk", "run", "dash"):
        fr = bodies[act]
        _, ms, loop = anim.BODY[act]
        hands = {d: [anim.hands_px(f.rig) for f in fr[d]] for d in DIRS}
        for suffix, fn, extra in kinds:
            imgs, tips = {}, {}
            for d in DIRS:
                pairs = [fn(d, act, i, f.rig) for i, f in enumerate(fr[d])]
                imgs[d] = [p[0] for p in pairs]
                tips[d] = [None if p[1] is None else hero.to_px(p[1]) for p in pairs]
            ex = dict(extra(act), bodySheet=wv3.BODY_RULE[weapon][act], bodySheetByWeapon={w: r[act] for w, r in wv3.BODY_RULE.items()},
                      bodySheetRuleNote=wv3.BODY_RULE_NOTE,
                      overlay="%s 와 같은 프레임 번호를 같은 시각에 겹친다. 피벗 = 주인공 피벗 + playerFrameOffset." % wv3.BODY_RULE[weapon][act])
            jobs.append(dict(name="%s_carry%s_%s" % (weapon, suffix, act), imgs=imgs, tips=tips, ms=ms, loop=loop,
                             action="carry%s_%s" % (suffix, act), hands=hands, grip=ex.pop("gripHand", "handR"), extra=ex,
                             bodies={d: [f.image for f in fr[d]] for d in DIRS}, meta=None, prev=dict(gif=True)))
    return jobs


def gear_jobs(weapon, mod, names, carry_hidden):
    jobs = []
    for name in names:
        r = Q.render(name)
        imgs, tips = {}, {}
        for d in DIRS:
            pairs = [mod.gear_frame(d, name, f[4], f[1]) for f in r["frames"][d]]
            imgs[d] = [p[0] for p in pairs]
            tips[d] = [None if p[1] is None else hero.to_px(p[1]) for p in pairs]
        if weapon == "greatsword":                  # 53라운드 Q55: 칼끝이 바닥 아래로 들어가지 않음(내리찍기 박힘 구간 제외)
            planted = {4, 5} if name == "greatsword_slam" else set()
            for k, _, oi in Q.expand(name)[0]:
                assert k == Q.IDLE or oi in planted or Q.gs_tip_z(k) >= 0, (name, oi, round(Q.gs_tip_z(k), 1))
        wname = Q.OLD_WEAPON[name]
        imgs[DIRS[0]][0].save(os.path.join(EX.OUT_W, wname + ".png"))   # 자리표(몸 JSON 이 weaponOverlayV3 를 걸게) — flush 가 덮어씀
        _, data = wv3.E2.export_gear(name, r)
        assert data["weaponOverlayV3"] == "weapons/v3/" + wname
        chk = wv3.check_gear_timing(name, r["ms"], data)
        ex = dict(bladeLocal=data["weaponLocal"], bladeLocalNote="몸 기준 무기 방향(θ: 0 = 앞, + = 해부 오른쪽 · elev: + = 위). null = 대기 0 그림(휴대).",
                  bodySheet="player_" + name, timingCheck=chk, includesSheath=False, carryHidden=carry_hidden,
                  overlay="player_%s 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 = 주인공 피벗 + playerFrameOffset." % name,
                  stateNote="steel 평소(균열·홈·시위 1px 은은) · glow/full/release 판정·발사(밝게) · fade 흐림 · embers 불티 · idle 대기 0 그림")
        if data.get("endsWith"):
            ex["endsWith"] = data["endsWith"].replace("player_idle_free", "player_idle_free + %s_carry%s_idle" %
                                                      (weapon, "" if name.endswith("sheathe") else "_drawn"))
        act = data.get("activeFrames") or ([data["holdFrame"]] if data.get("holdFrame") is not None else []) \
            or ([data["releaseFrame"]] if data.get("releaseFrame") is not None else []) or ([data["refillFrame"]] if data.get("refillFrame") is not None else [])
        jobs.append(dict(name=wname, imgs=imgs, tips=tips, ms=r["ms"], loop=False, action=data.get("action", name),
                         hands=data["handAnchors"], grip="handL" if weapon == "bow" else "handR", extra=ex, meta=data,
                         bodies={d: [f[0] for f in r["frames"][d]] for d in DIRS},
                         prev=dict(states=data["frameStates"], active=act, impact=data.get("impactFrame"))))
        print(wname, len(r["ms"]), "frames · timing", chk["checked"])
    return jobs


def flush(weapon, mod, jobs):
    """큰 캔버스 무기(대검)는 전 시트 합집합으로 한 틀을 정해 자른 뒤 쓴다. 나머지는 192 틀 그대로."""
    if hasattr(mod, "CANVAS"):
        frame, crop = wv3.fit_frame([j["imgs"] for j in jobs], mod.CANVAS_OFF)
        for j in jobs:
            j["imgs"] = {d: [im.crop(crop) for im in j["imgs"][d]] for d in DIRS}
        print(weapon, "frame", frame[:2], "playerFrameOffset", frame[2:], "pivot", (frame[2] + hero.PIV[0], frame[3] + hero.PIV[1]))
    else:
        frame = wv3.STD_FRAME
    off = frame[2:]
    for j in jobs:
        ex = dict(j["extra"], bladeTipAnchors={d: [None if t is None else wv3.to_w(t, off) for t in j["tips"][d]] for d in DIRS},
                  bladeTipNote="무기 끝(무기 시트 좌표) — 이펙트 위치 참고")
        wv3.write_overlay(j["name"], j["imgs"], j["ms"], j["loop"], j["action"], weapon, j["hands"], j["grip"], mod.DESIGN,
                          extra=ex, body_meta=j["meta"], frame=frame)
        note_colors(weapon, j["imgs"], frame)
        wv3.previews(j["name"], j["bodies"], j["imgs"], j["ms"], frame=frame, **j["prev"])
    return frame


GS_END_JUMP_MAX = 11.0                              # 도트 — 연격 끝 칼끝 ↔ 뽑아 든 휴대 대기 0 칼끝 (Q55, 측면·정면 공통)


def check_gs_end(jobs):
    """53라운드 Q55: 연격·특수 끝 프레임 칼끝이 greatsword_carry_drawn_idle 0 칼끝과 가까워 휴대로 넘어갈 때 날이 튀지 않음."""
    by = {j["name"]: j for j in jobs}
    ref = by["greatsword_carry_drawn_idle"]["tips"]
    for n in ("greatsword_combo1", "greatsword_combo3", "greatsword_dashslash", "greatsword_slam", "greatsword_special"):
        for d in DIRS:
            a, b = by[n]["tips"][d][-1], ref[d][0]
            dist = ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
            print("  Q55 end tip", n, d, round(dist, 1))
            assert dist <= GS_END_JUMP_MAX, (n, d, round(dist, 1))


DG_NAMES = ["dagger_combo1", "dagger_combo2", "dagger_combo3", "dagger_special"]
GS_NAMES = ["greatsword_combo1", "greatsword_combo2", "greatsword_combo3", "greatsword_dashslash", "greatsword_slam",
            "greatsword_draw", "greatsword_sheathe", "greatsword_special"]
BW_NAMES = ["bow_aim", "bow_reload", "attack"]


def main(only=None):
    EX.ensure_dirs()
    want = lambda a: not only or a in only          # noqa: E731
    bodies = build_free() if any(want(a) for a in ("free", "greatsword", "dagger", "bow")) else None
    if want("greatsword"):
        jobs = carry_jobs("greatsword", bodies, [
            ("", lambda d, act, i, R: GS.back_frame(d, R),
             lambda act: dict(carry="back, leather strap (등에 비스듬히 — 손잡이 오른어깨 위, 날 왼허리 뒤)", state="sheathed",
                              bladeLocal={"thetaDeg": GS.BACK_TH, "elevDeg": GS.BACK_EL}, gripHand=None)),
            ("_drawn", lambda d, act, i, R: GS.drawn_frame(d, act, i, R),
             lambda act: dict(carry="drawn, right hand (오른손 한 손으로 낮게 끎 — Q46 확정)", state="drawn",
                              bladeLocal={"thetaDeg": GS.DRAWN[act][0], "elevDeg": GS.DRAWN[act][1]},
                              stateNote="공격 뒤 넣기 전(비전투 타이머 동안) greatsword_carry_* 대신 사용."))])
        jobs += gear_jobs("greatsword", GS, GS_NAMES,
                          "이 시트 동안 greatsword_carry_* 는 숨긴다(등의 대검이 손으로 옮겨짐 — draw 첫 프레임·sheathe 끝 프레임은 이 시트가 등의 대검을 그림).")
        flush("greatsword", GS, jobs)
        check_gs_end(jobs)
    if want("dagger"):
        jobs = carry_jobs("dagger", bodies, [
            ("", lambda d, act, i, R: DG.carry_frame(d, act, i, R),
             lambda act: dict(carry="hand, reverse grip (오른손 역수 — 날이 팔뚝을 따라 뒤로)", state="inHand",
                              bladeLocal={"thetaDeg": DG.CARRY[act][0], "elevDeg": DG.CARRY[act][1]}))])
        jobs += gear_jobs("dagger", DG, DG_NAMES, "이 시트 동안 dagger_carry_* 는 숨긴다(이 시트가 손의 단검을 그림).")
        flush("dagger", DG, jobs)
    if want("bow"):
        jobs = carry_jobs("bow", bodies, [
            ("", lambda d, act, i, R: BW.carry_frame(d, act, i, R),
             lambda act: dict(carry="left hand, lowered (왼손에 내려 든 활 — 시위 A21 은은)", state="inHand", gripHand="handL",
                              bowLocal={"aimThetaDeg": BW.CARRY[act][0], "aimElevDeg": BW.CARRY[act][1]}))])
        jobs += gear_jobs("bow", BW, BW_NAMES, "이 시트 동안 bow_carry_* 는 숨긴다(이 시트가 손의 활·화살을 그림).")
        for j in jobs:
            if j["name"] == "bow_reload":
                j["extra"].update(reloadNote="오른어깨 뒤에 꽂힌 자기 화살을 뽑아(f2 쥠 · f3 뽑음) 앞으로 가져와(f4·f5) 시위에 대면 재로 부서져 "
                                             "시위에 스민다(f6 refill · 시위 A25) → f8 시위 A23 → f9 뽑힌 자리에서 재가 메워 화살이 다시 돋음(불티). "
                                             "몸 시트 f3~f8 은 그 화살을 그리지 않는다(arrowOut).")
        flush("bow", BW, jobs)
    pal = wv3.hero_palette()
    for w, s in STATS.items():
        outside = s["colors"] - pal
        print(w, "colors", len(s["colors"]), "/ 16 · outside hero palette", sorted("#%02x%02x%02x" % c for c in outside),
              "· partial", s["partial"], "· edge px", s["edge"], "· frame", s["frame"][:2])
        assert len(s["colors"]) <= 16 and not outside and not s["partial"], w
        assert s["edge"] == 0, (w, "edge pixels — 틀 밖으로 잘림")
    if not only:
        with open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8") as f:
            json.dump({w: dict(colors=len(s["colors"]), palette=sorted("#%02x%02x%02x" % c for c in s["colors"]),
                               edgePixels=s["edge"], frame=s["frame"]) for w, s in STATS.items()}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
