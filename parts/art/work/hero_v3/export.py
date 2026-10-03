"""주인공 v3 시트 내보내기 — assets/sprites/player/v3/*, assets/sprites/weapons/v3/katana_* (계약 §1·§3.1·§6.1·§6.2·§7.1·§11·§12·§13).

몸 시트 96×144 · 피벗 (48,138) · pixelScale 0.5 (53라운드 Q1). 무기 시트 192×192 · 피벗 (96,186) = 몸 피벗 · playerFrameOffset (48,48).
판정 시점 고정: 연격의 hitAt·cancelAt·total(ms)은 v2 시트와 같다(아래 assert).
"""
import json
import os

from PIL import Image

import anim
import hero
import katana3 as K
import motion
from v3kit import kit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
OUT_P = os.path.join(ROOT, "assets/sprites/player/v3")
OUT_W = os.path.join(ROOT, "assets/sprites/weapons/v3")
V2_P = os.path.join(ROOT, "assets/sprites/player/v2")
FW, FH, PIV = hero.FW, hero.FH, hero.PIV
DIRS = anim.DIRS
SRC = "parts/art/work/hero_v3/build.py (53라운드 Q1·Q4 — 96×144 1.5배 재출력)"
# 53라운드 Q70: 근접 판정 원점 메모 = 시스템 HIT_ORIGIN_UP_PX 10 월드 px = 논리 20px = 40 도트(pixelScale 0.5). 구 메모 '60 도트' 정정
HIT_ORIGIN_NOTE = "몸 중심 = 피벗(발)에서 위로 40 도트 (96×144 몸 기준 · 시스템 HIT_ORIGIN_UP_PX 10 월드 px = 논리 20px, 53라운드 Q70)"
OLD_P = os.path.join(ROOT, "assets/sprites/player")
SCAR_NOTE = ("53라운드 Q4 · 계약 §13: 프레임별 등 상흔 사각형(몸 시트 도트 좌표). x·y = 사각형 중심, w·h = 회전 전 크기, "
             "rot = 도(위쪽 변이 오른쪽으로 기울면 +, 시계 방향), visible = 이 프레임에 상흔을 그림. "
             "up = 등 가운데(visible), left·right = 굽은 등 위 어깨 쪽 작은 사각형(visible), down = 가슴 쪽 자리(visible:false). "
             "사망 4프레임부터(재 무덤으로 가라앉음)는 false.")
PALETTE = ("parts/art/palette/lopad.json (gray + 1층 램프 16~27, 런타임 스왑) + v2 재질 블록 SL·WD·PL "
           "(parts/art/work/v2_outer/palette_v2_proposal.json, 임시·고정색)")
EMISSIVE = [kit.tohex(c) for c in (kit.A[23], kit.A[25], kit.A[26])]
ANCHOR_NOTE = ("handAnchors = 프레임별 손 중심(몸 시트 도트 좌표, 해부 기준 R = 오른손 · L = 왼손). "
               "무기 시트 좌표 = 몸 좌표 + playerFrameOffset(48,48). 칼은 오른손(R)이 쥔다. "
               "대기·걷기·달리기에서 왼손(L)은 칼집 입구를 쥔다(53라운드).")
BODY_NOTE = "v3 · 53라운드 Q1 1.5배 — 96×144 도트, 화면 48×72 (pixelScale 0.5, 계약 §13). 개념 gemini/concept_char/hero3_b."
WDESIGN = dict(design="B 재 칼날 (53라운드 Q26) — 검은 재 칼날 + 날선 호박 균열 1줄 + 흉갑 조각 코등이 + 붕대 손잡이 + 금 간 재·흙 칼집",
               designRef="parts/art/work/gemini/concept_weapons/raw_katana_B2.jpg (참고만, 도트는 직접)",
               glowRule="53라운드 Q30: 평소 날선·칼집 금만 1px 은은(A21/A19), 판정(glow) 프레임만 날선 A25/A26 + 날 몸 A21",
               colorBudget=16, colorNote="무기 16색 이하, 전부 주인공 30색 팔레트 안(재 G·호박 A·흉갑 SL·붕대 PL 램프 공유, Q32). 백열 코어 X 미사용")
ARC_NOTE = "right 방향 화면각(0 = 정면, + = 아래, from→to = 휘두름 방향). down = +90° 회전, up = -90°, left = 좌우 반전(180-θ)"


def sheet(frames_by_dir, fw, fh):
    n = len(frames_by_dir[DIRS[0]])
    im = Image.new("RGBA", (fw * n, fh * len(DIRS)), (0, 0, 0, 0))
    for r, d in enumerate(DIRS):
        for c, f in enumerate(frames_by_dir[d]):
            im.paste(f, (c * fw, r * fh))
    return im


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def base(image, action, fw, fh, ms, loop, pivot, **extra):
    n = len(ms)
    d = {"image": image, "action": action, "frameWidth": fw, "frameHeight": fh, "frames": n, "directions": DIRS,
         "layout": "rows = directions (down, up, left, right), columns = frames", "frameIndex": "row * frames + column",
         "fps": round(1000 * n / sum(ms), 2), "frameDurationsMs": list(ms), "loop": loop,
         "pivot": {"x": pivot[0], "y": pivot[1]}, "pixelScale": 0.5, "palette": PALETTE, "source": SRC}
    d.update(extra)
    return d


def starts(ms):
    s, t = [], 0
    for m in ms:
        s.append(t)
        t += m
    return s


# ---------------------------------------------------------------------------
# 몸 동작
# ---------------------------------------------------------------------------
def scar_list(frames, act=None):
    out = {}
    for d in DIRS:
        lst = []
        for i, f in enumerate(frames[d]):
            sc = dict(f.rig.scar)
            if act == "death" and i >= 4:
                sc["visible"] = False
            lst.append(sc)
        out[d] = lst
    return out


def natural_speed(st):
    return round(st["px"] * 0.5 / st["cycleMs"] * 1000, 1)


def body_meta(act):
    _, ms, loop = anim.BODY[act]
    m = {}
    if act in anim.STRIDE:
        st = anim.STRIDE[act]
        m["stride"] = st
        m["strideNaturalSpeed"] = natural_speed(st)
        m["strideNote"] = ("계약 §12(52라운드 Q10): 한 주기(8프레임) 동안 디딤발이 바닥을 미는 거리(도트, pixelScale 0.5 → 논리 px = ×0.5) / 주기 ms. "
                           "시스템이 실제 이동 속도에 맞춰 재생 속도를 조절. strideNaturalSpeed = 배속 1 일 때 발이 미끄러지지 않는 논리 px/s")
    if act == "run":
        m["speedVsWalk"] = round(natural_speed(motion.STRIDE_RUN) / natural_speed(hero.STRIDE["walk"]), 2)
        m["flightFrames"] = list(motion.RUN_FLIGHT)
    if act == "dash":
        m["phases"] = {"crouch": [0], "launch": [1], "glide": [2, 3], "brake": [4]}
        m["fxNote"] = "잔상·재 꼬리는 이펙트(fx) 몫 — 이 시트는 몸 동작만"
    if act == "hurt":
        m["flashFrame"] = 0
        m["note2"] = "0 균열 백열 + 재 튐 · 1 젖힘(어깨 혼불 눌림) · 2 회복. 재 조각은 시트에 포함(몸 밖 1~2px)"
    if act == "death":
        m["eyeOffFrame"] = motion.DEATH_EYE_OFF
        m["flameOffFrame"] = motion.DEATH_EYE_OFF
        m["diaryOnlyFrame"] = len(ms) - 1
        m["phases"] = {"stagger": [0, 1], "kneel": [2, 3], "sinkIntoAsh": [4, 5, 6, 7], "ashScatter": [8], "diaryOnly": [9]}
    v2 = os.path.join(V2_P, "player_%s.json" % act)
    if os.path.exists(v2):
        o = json.load(open(v2, encoding="utf-8"))
        m["v2Timing"] = {"frames": o["frames"], "frameDurationsMs": o["frameDurationsMs"], "totalMs": sum(o["frameDurationsMs"])}
    else:   # 53라운드: player/v2 시트 삭제됨 → 이미 낸 v3 JSON 의 v2Timing 을 그대로 이어 쓴다(재빌드 때 기록이 사라지지 않게)
        cur = os.path.join(OUT_P, "player_%s.json" % act)
        if os.path.exists(cur):
            o = json.load(open(cur, encoding="utf-8"))
            if "v2Timing" in o:
                m["v2Timing"] = o["v2Timing"]
    return m


def export_body(act, frames):
    _, ms, loop = anim.BODY[act]
    im = sheet({d: [f.image for f in frames[d]] for d in DIRS}, FW, FH)
    name = "player_%s" % act
    im.save(os.path.join(OUT_P, name + ".png"))
    hands = {d: [anim.hands_px(f.rig) for f in frames[d]] for d in DIRS}
    write_json(os.path.join(OUT_P, name + ".json"),
               base(name + ".png", act, FW, FH, ms, loop, PIV, emissiveColors=EMISSIVE, **body_meta(act),
                    handAnchors=hands, anchorNote=ANCHOR_NOTE,
                    scarAnchor=scar_list(frames, act), scarAnchorNote=SCAR_NOTE,
                    carryOverlay="weapons/v3/katana_carry_%s" % act if act in anim.CARRY else None,
                    carryDrawnOverlay="weapons/v3/katana_carry_drawn_%s" % act if act in anim.CARRY else None,
                    note=BODY_NOTE))
    return im


# ---------------------------------------------------------------------------
# 칼 휴대 오버레이
# ---------------------------------------------------------------------------
def export_carry(act, frames):
    w, mouths = anim.render_carry(act, frames)
    _, ms, loop = anim.BODY[act]
    im = sheet(w, K.WF, K.WF)
    name = "katana_carry_%s" % act
    im.save(os.path.join(OUT_W, name + ".png"))
    n = len(ms)
    write_json(os.path.join(OUT_W, name + ".json"),
               base(name + ".png", "carry_%s" % act, K.WF, K.WF, ms, loop, K.WPIV, weapon="katana",
                    carry="waist sheath (해부 왼허리 칼집 — 일기장은 오른허리)", bodySheet="player_%s" % act,
                    anchor="player_pivot", **WDESIGN, playerFrameOffset={"x": K.OFF, "y": K.OFF},
                    depth={d: "above" for d in DIRS}, depthByFrame={d: ["above"] * n for d in DIRS}, occlusionBaked=True,
                    depthNote="몸 뒤로 가는 칼집·손잡이 픽셀은 몸 실루엣으로 지워 두었다 → 항상 몸 위에 겹친다(above). "
                              "right 는 칼집이 먼 허리라 몸 밖으로 나온 칼집 끝만 보인다.",
                    sheathMouthAnchors={d: [[x + K.OFF, y + K.OFF] for x, y in mouths[d]] for d in DIRS},
                    sheathMouthNote="칼집 입구(무기 시트 좌표) — 뽑기 이펙트·손 위치 참고용",
                    overlay="player_%s 와 같은 프레임 번호를 같은 시각에 겹친다. 피벗 (96,186) = 주인공 피벗 (48,138)." % act,
                    leftHandGrip=act in anim.SAYA_HOLD,
                    leftHandNote="대기·걷기·달리기: 왼손이 칼집 입구 바로 뒤를 쥐고 엄지로 코등이를 누른다(손 픽셀 위 칼집·코등이는 지워 둠)."))
    return im, w


def export_carry_drawn(act, frames):
    w = anim.render_carry_drawn(act, frames)
    _, ms, loop = anim.BODY[act]
    im = sheet(w, K.WF, K.WF)
    name = "katana_carry_drawn_%s" % act
    im.save(os.path.join(OUT_W, name + ".png"))
    n = len(ms)
    write_json(os.path.join(OUT_W, name + ".json"),
               base(name + ".png", "carry_drawn_%s" % act, K.WF, K.WF, ms, loop, K.WPIV, weapon="katana",
                    carry="drawn, in right hand (뽑아 든 상태) + 빈 칼집(왼허리)", state="drawn", bodySheet="player_%s" % act,
                    anchor="player_pivot", **WDESIGN, playerFrameOffset={"x": K.OFF, "y": K.OFF},
                    depth={d: "above" for d in DIRS}, depthByFrame={d: ["above"] * n for d in DIRS}, occlusionBaked=True,
                    bladeLocal={"thetaDeg": K.DRAWN[act][0], "elevDeg": K.DRAWN[act][1]},
                    bladeNote="대기·걷기 = 앞·아래·바깥으로 낮게 든 칼, 달리기 = 뒤로 끌며 낮게, 대쉬 = 뒤로 곧게. 오른손 = 몸 시트 handAnchors.R",
                    stateNote="공격 뒤 납도 전(비전투 타이머 동안) 이동·대기 때 katana_carry_* 대신 사용(구 시트와 같은 쓰임).",
                    overlay="player_%s 와 같은 프레임 번호를 같은 시각에 겹친다. 피벗 (96,186) = 주인공 피벗 (48,138)." % act))
    return im, w


# ---------------------------------------------------------------------------
# 칼 3연격 (몸 + 무기)
# ---------------------------------------------------------------------------
def combo_meta(n):
    c = K.COMBO[n]
    ms = c["ms"]
    st = starts(ms)
    imp, act_, can = c["impact"], c["active"], c["cancel"]
    hitAt = st[imp]
    activeEnd = st[act_[-1]] + ms[act_[-1]]
    cancelAt = st[can] if can is not None else None
    v2 = K.V2_TIMING[n]
    assert hitAt == v2["hitAt"] and cancelAt == v2["cancelAt"] and sum(ms) == v2["total"], ("v2 timing mismatch", n)
    p2 = os.path.join(V2_P, "player_katana_combo%d.json" % n)        # v2 시트가 지워지면 old_sheets/ 사본으로 대조
    if not os.path.exists(p2):
        p2 = os.path.join(HERE, "old_sheets", "v2_player_katana_combo%d.json" % n)
    o = json.load(open(p2, encoding="utf-8"))
    v2st = starts(o["frameDurationsMs"])
    v2activeEnd = v2st[o["activeFrames"][-1]] + o["frameDurationsMs"][o["activeFrames"][-1]]
    assert activeEnd == v2activeEnd, ("active window mismatch", n, activeEnd, v2activeEnd)
    return dict(weapon="katana", comboIndex=n, comboLength=3, impactFrame=imp, hitFrames=list(act_), activeFrames=list(act_),
                cancelFromFrame=can, anticipationFrames=list(range(imp)),
                recoverFrames=list(range(act_[-1] + 1, len(ms))),
                timingMs={"hitAt": hitAt, "activeEndAt": activeEnd, "cancelAt": cancelAt, "total": sum(ms)},
                v2Timing={"frames": o["frames"], "frameDurationsMs": o["frameDurationsMs"], "hitFrames": o["hitFrames"],
                          "cancelFromFrame": o["cancelFromFrame"], "timingMs": o["timingMs"]},
                timingNote="v3 는 프레임이 늘었지만 판정 시작(hitAt)·판정 끝·캔슬 시작(cancelAt)·전체(total) ms 는 v2 와 같다 — 판정 시점 불변.",
                **K.ARC[n], hitOrigin=HIT_ORIGIN_NOTE,
                hitRadiusPx=132, hitNote="임시(아트 메모). v2 66px(pixelScale 1) = v3 132 도트(pixelScale 0.5) — 논리 크기 같음. 시스템 실제 판정값이 우선",
                arcAngleNote=ARC_NOTE, framesBasis="player_katana_combo%d 프레임 번호 (무기·몸·이펙트 공통 기준 = 몸 시트)" % n,
                frameStates=[f["state"] for f in c["frames"]])


def export_combo(n, frames):
    c = K.COMBO[n]
    ms = c["ms"]
    meta = combo_meta(n)
    bim = sheet({d: [f.body for f in frames[d]] for d in DIRS}, FW, FH)
    scars = scar_list({d: frames[d] for d in DIRS})
    wim = sheet({d: [f.weapon for f in frames[d]] for d in DIRS}, K.WF, K.WF)
    bname, wname = "player_katana_combo%d" % n, "katana_combo%d" % n
    bim.save(os.path.join(OUT_P, bname + ".png"))
    wim.save(os.path.join(OUT_W, wname + ".png"))
    hands = {d: [f.hands for f in frames[d]] for d in DIRS}
    write_json(os.path.join(OUT_P, bname + ".json"),
               base(bname + ".png", "katana_combo%d" % n, FW, FH, ms, False, PIV, emissiveColors=EMISSIVE, **meta,
                    handAnchors=hands, anchorNote=ANCHOR_NOTE, scarAnchor=scars, scarAnchorNote=SCAR_NOTE,
                    nextComboSheet=K.ARC[n]["nextCombo"] and "player_" + K.ARC[n]["nextCombo"],
                    note="무기를 든 연격 몸 동작. weapons/v3/katana_combo%d 를 같은 프레임 번호·같은 시각에 겹친다(§6.1)." % n))
    nf = len(ms)
    whands = {d: [{k: [v[0] + K.OFF, v[1] + K.OFF] for k, v in h.items()} for h in hands[d]] for d in DIRS}
    write_json(os.path.join(OUT_W, wname + ".json"),
               base(wname + ".png", "combo%d" % n, K.WF, K.WF, ms, False, K.WPIV, **meta,
                    anchor="player_pivot", **WDESIGN, playerFrameOffset={"x": K.OFF, "y": K.OFF},
                    depth={d: "above" for d in DIRS}, depthByFrame={d: ["above"] * nf for d in DIRS}, occlusionBaked=True,
                    depthNote="칼·칼집이 몸 뒤로 가는 부분(몸 기준 카메라 반대쪽)은 몸 실루엣으로 지웠고, 쥔 손잡이는 주먹 픽셀로 가렸다 → 항상 above.",
                    handAnchors=whands, gripAnchors={d: [h["handR"] for h in whands[d]] for d in DIRS},
                    handAnchorNote="무기 시트 좌표. gripAnchors = 칼을 쥔 오른손(코등이 바로 뒤). combo3 은 양손(L = 손잡이 끝 쪽).",
                    bladeLocal=[{"thetaDeg": f.get("th"), "elevDeg": f.get("el")} for f in c["frames"]],
                    bladeLocalNote="몸 기준 칼 방향(θ: 0 = 앞, + = 해부 오른쪽 · elev: + = 위). sheathed 프레임은 칼집 안(null).",
                    includesSheath=True, carryHidden="연격 시트에 빈 칼집(허리)이 들어 있으므로 연격 동안 katana_carry_* 는 숨긴다.",
                    overlay="player_katana_combo%d 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 (96,186) = 주인공 피벗 (48,138)." % n,
                    stateNote="sheathed 칼집 안(손잡이를 쥠) · steel 실물 · glow 판정 프레임(날 호박 글로우, 끝 1px 백열 코어) · fade 다음 타로 넘어가는 흐림 · embers 불티",
                    fxNote="베기 이펙트(fx) v3 는 이번 범위 밖 — 기존 fx/katana_combo<n> 을 쓰거나 2배 재출력(계약 §11)"))
    return bim, wim


# ---------------------------------------------------------------------------
# 칼 뽑기 · 넣기 · 특수(패링) (몸 + 무기) — 53라운드 신규, 구 시트 ms 단계 유지
# ---------------------------------------------------------------------------
def move_meta(key):
    mv = K.MOVES[key]
    ms = mv["ms"]
    st = starts(ms)
    ot = K.OLD_TIMING[key]
    op = os.path.join(OLD_P, "player_katana_%s.json" % key)        # 구 시트는 사용처가 없어지면 지워질 수 있음 → 있으면 대조
    old = json.load(open(op, encoding="utf-8")) if os.path.exists(op) else dict(K.OLD_SHEET[key])
    assert sum(ms) == ot["total"] == sum(old["frameDurationsMs"]), ("total mismatch", key)
    pstart = {ph: st[fr[0]] for ph, fr in mv["phases"].items()}
    assert pstart == ot["phaseStart"], ("phase start mismatch", key, pstart, ot["phaseStart"])
    ost = starts(old["frameDurationsMs"])
    assert {ph: ost[fr[0]] for ph, fr in old["phases"].items()} == ot["phaseStart"], ("old sheet phase", key)
    m = dict(weapon="katana", phases=mv["phases"], phaseStartMs=pstart,
             oldTiming={"frames": old["frames"], "frameDurationsMs": old["frameDurationsMs"], "phases": old["phases"]},
             timingNote="구 시트(16×24)와 단계 시작 ms·전체 ms 가 같다(프레임만 늘림).",
             frameStates=[f["state"] for f in mv["frames"]],
             framesBasis="player_katana_%s 프레임 번호 (몸·무기 공통)" % key)
    if key == "draw":
        m.update(usage=old.get("usage"), note2="0 쥠 → 1 코이구치(엄지로 밀어 날 조금) → 2·3 왼손이 칼집을 뒤로 당기며 뽑음 → 4 앞·아래로 내림 → 5 = katana_carry_drawn_idle 0 과 같은 그림",
                 endsWith="katana_carry_drawn_idle 0")
    if key == "sheathe":
        m.update(usage=old.get("usage"), note2="0·1 피 털기(재·불티 튐) → 2 칼끝을 입구에 → 3·4·5 밀어 넣음 → 6 딸깍(코등이 반짝) → 7 = katana_carry_idle 0 과 같은 그림",
                 endsWith="katana_carry_idle 0")
    if key == "special":
        old_fx = old.get("overlayFx", [])
        m.update(secondaryAction=old.get("secondaryAction"), holdFrame=mv["holdFrame"],
                 holdNote="패링 창이 프레임 합보다 길면 f%d 유지. 성공 = f5~f8, 실패(창 종료) = f7~f8" % mv["holdFrame"],
                 overlayFx=[dict(o, atFrame=mv["phases"]["riposte"][0]) for o in old_fx],
                 windowMs={"start": pstart["window"], "end": pstart["riposte"]},
                 startsFrom="katana_carry_drawn (뽑아 든 상태에서 시작 — 칼집에 있으면 draw 먼저)", endsWith="katana_carry_drawn_idle 0")
    return m


def export_move(key, frames):
    mv = K.MOVES[key]
    ms = mv["ms"]
    meta = move_meta(key)
    bim = sheet({d: [f.body for f in frames[d]] for d in DIRS}, FW, FH)
    wim = sheet({d: [f.weapon for f in frames[d]] for d in DIRS}, K.WF, K.WF)
    bname, wname = "player_katana_%s" % key, "katana_%s" % key
    bim.save(os.path.join(OUT_P, bname + ".png"))
    wim.save(os.path.join(OUT_W, wname + ".png"))
    hands = {d: [f.hands for f in frames[d]] for d in DIRS}
    write_json(os.path.join(OUT_P, bname + ".json"),
               base(bname + ".png", "katana_%s" % key, FW, FH, ms, False, PIV, emissiveColors=EMISSIVE, **meta,
                    handAnchors=hands, anchorNote=ANCHOR_NOTE, scarAnchor=scar_list(frames), scarAnchorNote=SCAR_NOTE,
                    note="무기를 든 몸 동작(§6.2·§7.1). weapons/v3/katana_%s 를 같은 프레임 번호·같은 시각에 겹친다. " % key + BODY_NOTE))
    nf = len(ms)
    whands = {d: [{k: [v[0] + K.OFF, v[1] + K.OFF] for k, v in h.items()} for h in hands[d]] for d in DIRS}
    write_json(os.path.join(OUT_W, wname + ".json"),
               base(wname + ".png", key, K.WF, K.WF, ms, False, K.WPIV, **meta,
                    anchor="player_pivot", **WDESIGN, playerFrameOffset={"x": K.OFF, "y": K.OFF},
                    depth={d: "above" for d in DIRS}, depthByFrame={d: ["above"] * nf for d in DIRS}, occlusionBaked=True,
                    handAnchors=whands, gripAnchors={d: [h["handR"] for h in whands[d]] for d in DIRS},
                    includesSheath=True, carryHidden="이 시트에 칼집(빈 칼집 또는 칼이 든 칼집)이 들어 있으므로 재생 동안 katana_carry_* 는 숨긴다.",
                    overlay="player_katana_%s 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 (96,186) = 주인공 피벗 (48,138)." % key,
                    stateNote="sheathed 칼집 안 · partial 칼집 축을 따라 날 일부만 밖 · steel 실물 · glow 패링 대기/반격(날 호박, 끝 1px 백열) · "
                              "fade 흐림 · embers 피 털기 불티 · click 넣기 끝 코등이 반짝"))
    return bim, wim


def edge_pixels(im):
    """무기 시트 프레임 가장자리에 닿은 픽셀 수(잘림 점검)."""
    n = 0
    W, H = im.size
    px = im.load()
    for x in range(W):
        for y in (0, H - 1):
            n += px[x, y][3] > 0
    for y in range(H):
        for x in (0, W - 1):
            n += px[x, y][3] > 0
    return n


def ensure_dirs():
    os.makedirs(OUT_P, exist_ok=True)
    os.makedirs(OUT_W, exist_ok=True)
