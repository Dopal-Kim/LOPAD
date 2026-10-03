"""55라운드 새 연격 — 몸 v3 + 무기 v3 오버레이 렌더·내보내기 (계약 §11·§13·§17).

몸 96×144 · 피벗 (48,138) · pixelScale 0.5 (hero_v3 와 같은 Rig). 칼 오버레이 192×192 · 피벗 (96,186) · playerFrameOffset (48,48).
대검 오버레이 = 448 캔버스에 그려 새 대검 시트 5종 합집합으로 자른 한 틀(JSON frameWidth/Height·pivot·playerFrameOffset 을 읽을 것).
칼은 칼집(왼허리) 포함 — 연격 동안 katana_carry_* 숨김. bladeTipAnchors = 칼끝(무기 시트 좌표, 칼집 안이면 null).
"""
import math
import os

import moves as M
from moves import wv3
from wv3 import K, Q, EX, hero, DIRS

import greatsword as GS

SRC = "parts/art/work/combo55/build.py (55라운드 Q18~Q25 · 계약 §17 새 연격)"
HIT_UP = 40                                            # 판정 원점 = 피벗 위 40 도트(export.HIT_ORIGIN_NOTE)


def katana_tip(d, grip, v):
    tsuba = K.add(grip, K.project(d, v), 3.0)
    return hero.to_px(K.add(tsuba, K.project(d, v), K.BLADE_LEN)[:2])


def katana_frame(d, fr, i, seed):
    """katana3.move_frame 과 같은 그림(칼집 포함) + 칼끝(몸 도트)."""
    p, hand, v, state, visible = K.combo_pose(d, fr, i)
    R = hero.draw_rig(d, p)
    L = K.Layer()
    slide = fr.get("slide", 0.0)
    K.draw_saya(L, d, K.mouth_point(d, R), K.saya_vec(p["sway"] * 0.5), with_hilt=(state in ("sheathed", "click")), slide=slide)
    tip = None
    if state not in ("sheathed", "click"):
        gR = R.anchors["handR"]
        grip = (gR[0], gR[1], K.to_screen(d, hand)[2])
        if state == "partial":
            m = K.add(K.mouth_point(d, R), K.project(d, K.SAYA_DIR), slide)
            grip = K.add(m, K.project(d, K.HILT_DIR), fr["along"])
            K.draw_katana(L, d, grip, K.SAYA_DIR, "steel", seed=seed + i, visible=visible)
        else:
            K.draw_katana(L, d, grip, v, state, seed=seed + i)
            tip = katana_tip(d, grip, v)
    hold = ("handR", "handL") if fr["off"] in ("two", "saya") else ("handR",)
    im = K.rasterize(L, R, hold_hands=hold)
    return R, im, tip, state


def render_katana(name):
    m = M.KATANA[name]
    out = {}
    for d in DIRS:
        lst = []
        for i, fr in enumerate(m["frames"]):
            R, im, tip, st = katana_frame(d, fr, i, K.ember_seed("k55", name))
            lst.append(dict(body=R.image, rig=R, weapon=im, tip=tip, state=st))
        out[d] = lst
    return out


def render_gs(name):
    m = M.GS[name]
    keys = [Q.norm(k) for k in m["frames"]]
    out = {}
    for d in DIRS:
        lst = []
        for i, k in enumerate(keys):
            p = Q.body_pose(d, dict(k, state="glow" if k["state"] == "glow" else k["state"]), i)
            R = hero.draw_rig(d, p)
            im, tip = GS.gear_frame(d, name, k, R)
            lst.append(dict(body=R.image, rig=R, weapon=im, tip=hero.to_px(tip), state=k["state"], key=k))
        out[d] = lst
    return out, keys


# =============================================================================
# JSON
# =============================================================================
def hit_shape(m, R_world):
    hs = dict(m["hitShape"])
    Rd = M.dots(R_world)
    hs["R"] = {"world": R_world, "dots": Rd}
    if hs["type"] == "arc":
        hs["outerRadiusPx"] = round(Rd * hs["radiusR"], 1)
        hs["innerRadiusPx"] = round(Rd * hs["innerR"] * hs["radiusR"], 1)
    elif hs["type"] == "wedge":
        if "lengthR" in hs:
            hs["lengthPx"] = round(Rd * hs["lengthR"], 1)
            ic = dict(hs["impactCircle"])
            ic["centerDistPx"] = round(Rd * ic["centerR"], 1)
            ic["radiusPx"] = round(Rd * ic["radiusR"], 1)
            hs["impactCircle"] = ic
        else:
            hs["lengthPxByStage"] = [round(Rd * k, 1) for k in hs["lengthRByStage"]]
            ic = dict(hs["impactCircle"])
            ic["radiusPx"] = round(Rd * ic["radiusR"], 1)
            hs["impactCircle"] = ic
    hs["units"] = "…Px = 도트(pixelScale 0.5, 월드 px = 도트 / 4). 각도: 조준 0°, 화면 시계 + (§17). 원점 = 판정 원점(피벗 위 40 도트)"
    hs["reference"] = "참고값 — 시스템 데이터(§17)가 기준"
    return hs


def meta_for(name, m, weapon, R_world):
    tm = M.timing(m)
    meta = dict(weapon=weapon, version="v3-r55", comboSet="K-A 발도 초승달" if weapon == "katana" else "G-C 관성 순환",
                label=m["label"], timingMs=tm, frameStates=None, framesBasis="player_%s 프레임 번호(몸·무기·이펙트 공통 기준 = 몸 시트)" % name,
                msNote="ms 는 아트 제안값. 시스템이 데이터로 바꿔도 impactFrame 시작 = hitAt 이 맞으면 그림은 맞는다(관성 공속은 재생 속도로).")
    if m.get("comboIndex"):
        meta["comboIndex"] = m["comboIndex"]
    if m.get("impact") is not None:
        st = M.starts(m["ms"])
        meta.update(impactFrame=m["impact"], hitFrames=list(m["active"]), activeFrames=list(m["active"]),
                    glowFrames=sorted(set(m["active"]) | {m["impact"]}), cancelFromFrame=m.get("cancel"),
                    anticipationFrames=list(range(m["impact"])), recoverFrames=list(range(m["active"][-1] + 1, len(m["ms"]))),
                    hitShape=hit_shape(m, R_world), hitOrigin=EX.HIT_ORIGIN_NOTE)
        if m["hitShape"]["type"] == "arc":
            meta.update(arcFromDeg=m["arc"][0], arcToDeg=m["arc"][1], arcDeg=abs(m["arc"][1] - m["arc"][0]),
                        arcNote="그림의 휘두름 방향(from → to). 화면각(조준 0°, 시계 +). 모든 방향 = 조준 방향 기준 회전(left 도 회전, 좌우 반전 아님)")
        meta["stepPx"] = dict(world=m["step"]["world"], dots=M.dots(m["step"]["world"]), frames=m["step"]["frames"],
                              note="내딛기 참고값(§17, 월드 px) — 방향키를 누를 때만. frames = 몸이 앞으로 나가는 프레임(그림은 제자리, 이동은 시스템)")
        meta["stepStartMs"] = st[m["step"]["frames"][0]]
    for k in ("phases", "loopFrames", "stages", "echo", "next", "startsFrom", "endsWith"):
        if k in m:
            meta[{"next": "nextMove"}.get(k, k)] = m[k]
    if "loopFrames" in m:
        meta.update(loopRange=[m["loopFrames"][0], m["loopFrames"][-1]], holdFrame=m["loopFrames"][0],
                    loopNote="f0~f2 들어 올림 1회 → 홀드 동안 loopFrames 반복(시스템이 loopRange 를 반복 재생). 시트 loop 값은 false")
    return meta


def export_move(name, frames, weapon, frame=None, design=None):
    m = M.KATANA.get(name) or M.GS[name]
    R_world = M.R_KATANA if weapon == "katana" else M.R_GS
    ms = m["ms"]
    meta = meta_for(name, m, weapon, R_world)
    meta["frameStates"] = [f["state"] for f in frames[DIRS[0]]]
    bname = "player_" + name
    bim = EX.sheet({d: [f["body"] for f in frames[d]] for d in DIRS}, hero.FW, hero.FH)
    bim.save(os.path.join(EX.OUT_P, bname + ".png"))
    hands = {d: [{k: [round(c, 1) for c in hero.to_px(f["rig"].anchors[k])] for k in ("handR", "handL")} for f in frames[d]] for d in DIRS}
    scars = EX.scar_list({d: [type("F", (), {"rig": f["rig"]}) for f in frames[d]] for d in DIRS})
    data = EX.base(bname + ".png", name, hero.FW, hero.FH, ms, False, hero.PIV, emissiveColors=EX.EMISSIVE, **meta,
                   handAnchors=hands, anchorNote=EX.ANCHOR_NOTE.replace("대기·걷기·달리기에서 왼손(L)은 칼집 입구를 쥔다(53라운드).", ""),
                   scarAnchor=scars, scarAnchorNote=EX.SCAR_NOTE,
                   weaponOverlayV3="weapons/v3/" + name,
                   note="55라운드 새 연격(§17) 몸. weapons/v3/%s 를 같은 프레임 번호·같은 시각에 겹친다. " % name + EX.BODY_NOTE)
    data["source"] = SRC
    EX.write_json(os.path.join(EX.OUT_P, bname + ".json"), data)
    # 무기 오버레이
    fw, fh, ox, oy = frame
    tips = {d: [None if f["tip"] is None else [round(f["tip"][0] + ox, 1), round(f["tip"][1] + oy, 1)] for f in frames[d]] for d in DIRS}
    if weapon == "katana":
        local = [{"thetaDeg": fr.get("th"), "elevDeg": fr.get("el")} if fr["state"] not in ("sheathed", "partial", "click") else None
                 for fr in m["frames"]]
        ex = dict(includesSheath=True, carryHidden="연격 시트에 칼집(빈 칼집 또는 칼이 든 칼집)이 들어 있으므로 재생 동안 katana_carry_* 는 숨긴다.",
                  stateNote="steel 실물 · glow 판정(날선 A25/A26) · fade 흐림 · partial 칼집 축을 따라 날 일부만 밖 · sheathed 칼집 안(손잡이를 쥠)")
    else:
        local = [{"thetaDeg": round(k["th"], 1), "elevDeg": round(k["el"], 1)} for k in (Q.norm(x) for x in m["frames"])]
        ex = dict(includesSheath=False, carryHidden="이 시트 동안 greatsword_carry_* 는 숨긴다(이 시트가 손의 대검을 그림).",
                  stateNote="steel 평소(홈 혼불 1px 은은) · glow 판정(날 가장자리 A25/A23 + 홈 A26) · charge 홀드(평소 그림 — 단계 번쩍임은 fx)",
                  **{k: v for k, v in GS.DESIGN.items() if k not in ("design", "designRef", "glowRule", "colorBudget", "colorNote")})
    ex.update(bladeLocal=local, bladeLocalNote="몸 기준 무기 방향(θ: 0 = 앞, + = 해부 오른쪽 · elev: + = 위). null = 칼집 안",
              bladeTipAnchors=tips, bladeTipNote="칼끝(무기 시트 좌표, 55라운드 시스템 요청 — 칼 포함). null = 날이 칼집 안. 칼끝 리본(§16 ribbon_ash)의 머리 위치로 쓸 수 있다",
              bodySheet=bname, source=SRC,
              overlay="%s 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 = 주인공 피벗 + playerFrameOffset." % bname)
    design = design or (EX.WDESIGN if weapon == "katana" else {k: GS.DESIGN[k] for k in ("design", "designRef", "glowRule", "colorBudget", "colorNote")})
    wv3.write_overlay(name, {d: [f["weapon"] for f in frames[d]] for d in DIRS}, ms, False, name, weapon, hands, "handR", design,
                      extra=ex, body_meta=data, frame=frame)
    return data


def crop_gs(all_frames):
    """대검 새 시트 합집합 틀 → 각 무기 그림을 자름. → frame (W, H, ox, oy)."""
    frame, box = wv3.fit_frame([{d: [f["weapon"] for f in fr[d]] for d in DIRS} for fr in all_frames.values()], GS.CANVAS_OFF)
    for fr in all_frames.values():
        for d in DIRS:
            for f in fr[d]:
                f["weapon"] = f["weapon"].crop(box)
                if f["tip"] is not None:
                    f["tip"] = (f["tip"][0], f["tip"][1])
    return frame


def tip_z_gs(k):
    return Q.gs_tip_z(k)
