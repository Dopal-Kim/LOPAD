#!/usr/bin/env python3
"""61 단계 6 (P14 §2, 계약 art §28) 무기 색 정체성 — 칼 '서리'(청백 시안 #8fe3ff · 보조 은백) · 단검 '독'(자주·자홍 #c060ff · 보조 먹빛).
대검·활은 다른 아트 작업(이 스크립트는 katana·dagger 이름 시트와 shadowstep_ghost 만 씀). 자율 모드 — 아트 판단, 결정적, Gemini 미사용.

단계(인자 없으면 전부, 순서대로):
  kweapon  칼 기본 무기 시트 중 판정 칸이 있는 14 — 판정 칸 날 빛·칼끝 빛줄기만 서리(katana61s5 3D 경로를 불러 색만 바꿔 끼움, wkatana.py)
  dweapon  단검 기본 무기 시트 중 판정 칸이 있는 7 — 판정 칸의 호박 날선·불씨만 독(나머지 칸 = 주인공 호박 불씨 그대로)
  fx       무기 fx·적중·개성 fx·공명 켜짐 고리 — 램프 LUT(ramps.py)
  overlay  칼 검기 _ki1~3 · 각성 _awaken 날선 · 단검 _awaken·백귀/쌍격 1차 귀화 날선 — LUT
  tint     2차 길 pathTint·trailTint(v4 a1/a2/a2_glow JSON) — 무기 색 계열 두 변주
  looks    looks/<weapon>_* 귀화 날선 LUT + a2_<길> 다시 굽기 + looks/<weapon>.json
  cards    개성 카드 그림 강조 획(cards.py)
LUT 는 '원래 색 → 새 색' 1:1 이고 새 색은 원래 색 집합과 겹치지 않음 → 두 번 돌려도 그대로(멱등). 원본 빌드(katana61s5·dagger61s5·
traits61s5_*·traitcards61s5)를 다시 돌린 뒤에는 이 스크립트를 다시 돌리면 된다.
사용: python3 parts/art/work/color61s6/build.py [kweapon fx overlay tint looks cards]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import aio  # noqa: E402
import ramps as R  # noqa: E402
import recolor as RC  # noqa: E402
import targets as T  # noqa: E402

STEPS = ["kweapon", "dweapon", "fx", "overlay", "tint", "looks", "cards"]
TAG = "61 단계 6 P14 §2"

# ---------------------------------------------------------------- LUT 묶음
K_FX = R.merge(R.K_GREY, R.K_SL, R.K_X1, R.K_AMBER, R.FROST_SIL)
K_AMBER_BRIGHT = {k: v for k, v in R.K_AMBER.items() if k in ("#f4de9b", "#eecc78", "#e2a33c", "#d67a11")}
K_TRAIT = R.merge(R.K_GREY, R.K_X1, R.K_MOON, {"#7e8693": R.FROST["f1"], "#626a78": R.FROST["d2"]}, K_AMBER_BRIGHT)
K_TRAIT_FIRE = R.merge(R.K_GREY, R.K_X1, R.K_MOON, {"#7e8693": R.FROST["f1"], "#626a78": R.FROST["d2"]})   # 불·술·피는 그대로
K_FIRE_SHEETS = {"trait_katana_k_sparkCleave", "trait_katana_k_sparkCleave_spark", "trait_katana_liquorWhirl", "trait_katana_liquorWhirl_fire"}
# 공명 켜짐 고리(태그 색 고리 → 무기 색 고리, 문양 모양으로 태그 구별)
K_RING = {
    "trait_res_katana_breach_on": {"#d3fae8": R.FROST["ice"], "#95e0c6": R.FROST["pale"], "#64c7af": R.FROST["main"], "#42ad9f": R.FROST["f3"],
                                   "#387172": R.FROST["d2"], "#223337": R.FROST["d1"], "#fff4dc": R.FROST["white"]},
    "trait_res_katana_chain_on": {"#faf8c2": R.FROST["ice"], "#f1e87c": R.FROST["pale"], "#e9d441": R.FROST["main"], "#e0bf16": R.FROST["f3"],
                                  "#917126": R.FROST["d2"], "#41321f": R.FROST["d1"], "#fff4dc": R.FROST["white"]},
    "trait_res_katana_insight_on": {"#c8d8f0": R.FROST["ice"], "#9ab0d8": R.FROST["pale"], "#7e8693": R.FROST["main"], "#4e5563": R.FROST["f3"],
                                    "#323743": R.FROST["d2"], "#1d2028": R.FROST["d1"], "#fff4dc": R.FROST["white"]},
    "trait_res_dagger_vital_on": {"#fac7c2": R.POISON["a26"], "#e27774": R.POISON["pale"], "#ca3941": R.POISON["main"], "#b21227": R.POISON["p4"],
                                  "#751f33": R.POISON["p3"], "#381b25": R.POISON["p1"], "#fff4dc": R.POISON["white"]},
    "trait_res_dagger_breach_on": {"#d3fae8": R.POISON["a26"], "#95e0c6": R.POISON["pale"], "#64c7af": R.POISON["main"], "#42ad9f": R.POISON["p4"],
                                   "#387172": R.POISON["p3"], "#223337": R.POISON["p1"], "#fff4dc": R.POISON["white"]},
}
D_FX = R.merge(R.D_AMBER, R.D_ASH, R.D_TEAL)
D_FIRE_FX = {"dagger_hotwind_trail", "dagger_hotwind_burst", "dagger_overheat_burst"}          # 열풍·과열 = 불 메커니즘 그림
D_TRAIT = R.merge(R.D_AMBER, R.D_ASH)
D_FIRE_SHEETS = {"trait_dagger_liquorThrow", "trait_dagger_d_ghostFire", "trait_dagger_d_sparkFlurry"}
K_KI = R.merge(R.K_GREY, R.K_X1, R.K_AMBER, {"#7e8693": R.FROST["f1"]})
K_AWAKEN = {"#ebeced": R.FROST["pale"], "#fff4dc": R.FROST["white"]}                         # 월인 날선·반짝만(은 날 본체 그대로)
D_AWAKEN = R.merge(R.D_TEAL, {k: v for k, v in R.D_AMBER.items() if k in ("#fff4dc", "#e2a33c", "#d67a11")})
D_A1 = dict(R.D_TEAL)                                                                         # 쌍격·백귀 1차 날선 빛(청록) → 독

NOTE_K_FX = (TAG + " 칼 '서리' — 은선 램프(무채 G9~G14·청강 SL4~SL7)·호박 불티 → 서리 램프(머리·날선 #bff3ff · 몸 #8fe3ff · 꼬리 #5cc6ee→#1a3a58), "
             "백열 X1 → 서리 흰빛 #e6fcff(판정 칸만), X0 코어 그대로. 각성 은 램프 → 서리꽃 은백. 모양·틀·프레임·ms 그대로")
NOTE_K_TRAIT = (TAG + " 칼 '서리' — 은선 획·달 분신·호박 불티 → 서리 램프. 묶음 청회·먹 그림자·흙먼지·피·불·술은 그대로(메커니즘 색)")
NOTE_K_RING = TAG + " — 공명 켜짐 고리를 칼 서리 램프로(태그는 문양 모양으로 구별)"
NOTE_D_FX = (TAG + " 단검 '독' — 호박 발톱 획·X 불티·낙인 불씨 → 독 램프(머리 #ec9cff · 몸 #c060ff · 어둠 #9440d8→#2a1544), 재 부스러기 → 먹빛 보라, "
             "백귀 귀화(청록) → 독 불(자홍), 백열 X1 → #fbe0ff(판정 칸만), X0 그대로. 먹 그림자·칼 강철 그대로")
NOTE_D_TRAIT = TAG + " 단검 '독' — 발톱 획·X·낙인 불씨 → 독 램프, 재 테 → 먹빛 보라. 사슬 적갈·묶음 청회·먹·불·술은 그대로(메커니즘 색)"
NOTE_D_RING = TAG + " — 공명 켜짐 고리를 단검 독 램프로(태그는 문양 모양으로 구별)"
NOTE_KEEP = TAG + " — 불·열 메커니즘 그림이라 색 그대로(무기 색 대상 아님)"
NOTE_KI = TAG + " 칼 '서리' 검기 — 빛줄기·날선·불티를 서리 램프로(1단 #5cc6ee~#8fe3ff · 3단 날 #e0faff/#bff3ff), 판정 칸 X1 → #e6fcff"
NOTE_K_AW = TAG + " 칼 '서리' — 월인 날선 G14 → #bff3ff, 반짝 X1 → #e6fcff(은 날 본체 그대로)"
NOTE_D_AW = TAG + " 단검 '독' — 귀화 청록 불혀 날선·혼불 → 독 불 자홍, 호박 불씨 점 → 독. 보라 날 본체 그대로"
NOTE_D_A1 = TAG + " 단검 '독' — 1차 날선 빛(청록) → 독 불 자홍. 날 본체 그대로"


def step_kweapon():
    import wkatana
    print(len(wkatana.build()), "katana base sheets")


D_GLOW = {k: v for k, v in R.D_AMBER.items() if k in ("#fff4dc", "#f4de9b", "#eecc78", "#e2a33c", "#d67a11", "#8b4d22")}
NOTE_D_W = (TAG + " 단검 '독' — 판정 칸(glowFrames·frameStates glow)만 안쪽 날선 불씨·끝 반짝을 독 램프로(#8b4d22→#64289a … #eecc78→#ec9cff · "
            "A26→#f6c8ff · X1→#fbe0ff). 평소 칸의 호박 날선·혈관(주인공 균열과 한 식구)과 강철 날·손가락 고리는 그대로")


def step_dweapon():
    import glob
    for jp in sorted(glob.glob(os.path.join(RC.SPR, "weapons", "v3", "dagger_*.json"))):
        rel = os.path.relpath(jp, RC.SPR)[:-5]
        if rel.endswith("_awaken"):
            continue
        m = aio.read_json(jp)
        cols = set(m.get("glowFrames") or []) | {i for i, st in enumerate(m.get("frameStates") or []) if st == "glow"}
        if not cols:
            continue
        n, shared = RC.apply_sheet_frames(rel, D_GLOW, NOTE_D_W, cols)
        print(rel, "glow cols", sorted(cols), "px", n, "shared-skip", len(shared))


def step_fx():
    tot = 0
    for rel in T.katana_fx():
        tot += RC.apply_sheet(rel, K_FX, NOTE_K_FX)
    for rel in T.trait_fx("katana"):
        b = os.path.basename(rel)
        if b in K_RING:
            tot += RC.apply_sheet(rel, K_RING[b], NOTE_K_RING)
        else:
            tot += RC.apply_sheet(rel, K_TRAIT_FIRE if b in K_FIRE_SHEETS else K_TRAIT, NOTE_K_TRAIT)
    for rel in T.dagger_fx():
        b = os.path.basename(rel)
        if b in D_FIRE_FX:
            continue
        tot += RC.apply_sheet(rel, D_FX, NOTE_D_FX)
    for rel in T.trait_fx("dagger"):
        b = os.path.basename(rel)
        if b in K_RING:
            tot += RC.apply_sheet(rel, K_RING[b], NOTE_D_RING)
        elif b in D_FIRE_SHEETS:
            continue
        else:
            tot += RC.apply_sheet(rel, D_TRAIT, NOTE_D_TRAIT)
    print("fx pixels", tot)


def step_overlay():
    tot = 0
    for rel in T.ki_overlays():
        tot += RC.apply_sheet(rel, K_KI, NOTE_KI)
    for rel in T.awaken_overlays("katana"):
        tot += RC.apply_sheet(rel, K_AWAKEN, NOTE_K_AW)
    for rel in T.awaken_overlays("dagger"):
        tot += RC.apply_sheet(rel, D_AWAKEN, NOTE_D_AW)
    for rel in T.v4("dagger", "a1"):
        if "_twin_" in rel or "_hyakki_" in rel:
            tot += RC.apply_sheet(rel, D_A1, NOTE_D_A1)
    print("overlay pixels", tot)


def _tint_update(weapon, branch):
    pt = R.PATH_TINT[weapon][branch]

    def up(m):
        if "pathTint" in m:
            m["pathTint"] = {k: list(v) for k, v in pt.items()}
        if "trailTint" in m:
            m["trailTint"] = {k: list(v) for k, v in pt.items()}
        m["pathTintNote"] = TAG + (" 칼 '서리' — 2차 두 길 = 서리 계열 안 짙은 쪽 / 옅은 쪽" if weapon == "katana"
                                   else " 단검 '독' — 2차 두 길 = 독 계열 안 두 변주(보라 / 자홍)")
    return up


def step_tint():
    n = 0
    for weapon in ("katana", "dagger"):
        for layer in ("a1", "a2", "a2_glow"):
            for rel in T.v4(weapon, layer):
                jp = os.path.join(RC.SPR, rel + ".json")
                m = aio.read_json(jp)
                if "pathTint" not in m and "trailTint" not in m:
                    continue
                branch = m.get("branch") or os.path.basename(rel).split("_")[1]
                _tint_update(weapon, branch)(m)
                (aio.write_atlas_json if "atlas" in m else aio.write_plain_json)(jp, m)
                n += 1
    print("tint json", n)


def _tint(im, rgb):
    out = im.copy()
    p = out.load()
    for y in range(im.height):
        for x in range(im.width):
            c = p[x, y]
            if c[3]:
                p[x, y] = (c[0] * rgb[0] // 255, c[1] * rgb[1] // 255, c[2] * rgb[2] // 255, 255)
    return out


def step_looks():
    from PIL import Image
    d = os.path.join(RC.SPR, "looks")
    for rel in T.looks("dagger"):
        b = os.path.basename(rel)
        if b.startswith(("dagger_twin_a", "dagger_hyakki_a")) and "_glow" not in b:
            RC.apply_png(rel, D_A1)
    for weapon in ("katana", "dagger"):
        jp = os.path.join(d, weapon + ".json")
        meta = aio.read_json(jp)
        for bid, bd in meta["branches"].items():
            pt = R.PATH_TINT[weapon][bid]
            bd["pathTint"] = {k: list(v) for k, v in pt.items()}
            a2 = Image.open(os.path.join(d, bd["a2"])).convert("RGBA")
            gl = Image.open(os.path.join(d, bd["a2Glow"])).convert("RGBA")
            for pid, rgb in pt.items():
                s = a2.copy()
                s.alpha_composite(_tint(gl, rgb))
                s.save(os.path.join(d, bd["a2ByPath"][pid]), optimize=True)
        meta["color61s6"] = TAG + (" 칼 '서리' — 2차 길 pathTint 를 서리 계열 두 변주로, a2_<길> 다시 구움" if weapon == "katana"
                                   else " 단검 '독' — 쌍격·백귀 날선 빛(청록) → 독 자홍, 2차 길 pathTint 를 독 계열 두 변주로, a2_<길> 다시 구움")
        aio.write_plain_json(jp, meta)
    print("looks ok")


def step_cards():
    import cards
    for w in ("katana", "dagger"):
        r = cards.apply(w, T.cards(w))
        print(w, "cards", sum(1 for v in r.values() if v), "changed", r)


def main():
    for name in ("D_GLOW", "K_FX", "K_TRAIT", "K_TRAIT_FIRE", "D_FX", "D_TRAIT", "K_KI", "K_AWAKEN", "D_AWAKEN", "D_A1"):
        R.check_lut(globals()[name], name)
    for k, v in K_RING.items():
        R.check_lut(v, k)
    want = [a for a in sys.argv[1:] if a in STEPS] or STEPS
    for s in want:
        print("==", s, flush=True)
        globals()["step_" + s]()


if __name__ == "__main__":
    main()
