"""주인공 v3 시트 내보내기 — assets/sprites/player/v3/*, assets/sprites/weapons/v3/katana_* (계약 §1·§3.1·§6.1·§7.1·§11·§12).

몸 시트 64×96 · 피벗 (32,92) · pixelScale 0.5. 무기 시트 128×128 · 피벗 (64,124) = 몸 피벗 · playerFrameOffset (32,32).
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
SRC = "parts/art/work/hero_v3/build.py (52라운드 Q12 2단계)"
PALETTE = ("parts/art/palette/lopad.json (gray + 1층 램프 16~27, 런타임 스왑) + v2 재질 블록 SL·WD·PL "
           "(parts/art/work/v2_outer/palette_v2_proposal.json, 임시·고정색)")
EMISSIVE = [kit.tohex(c) for c in (kit.A[23], kit.A[25], kit.A[26])]
ANCHOR_NOTE = ("handAnchors = 프레임별 손 중심(몸 시트 도트 좌표, 해부 기준 R = 오른손 · L = 왼손). "
               "무기 시트 좌표 = 몸 좌표 + playerFrameOffset(32,32). 칼은 오른손(R)이 쥔다.")
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
def body_meta(act):
    _, ms, loop = anim.BODY[act]
    m = {}
    if act in anim.STRIDE:
        m["stride"] = anim.STRIDE[act]
        m["strideNote"] = ("계약 §12(52라운드 Q10): 한 주기(8프레임) 동안 디딤발이 바닥을 미는 거리(도트, pixelScale 0.5 → 논리 px = ×0.5) / 주기 ms. "
                           "시스템이 실제 이동 속도에 맞춰 재생 속도를 조절")
    if act == "run":
        m["speedVsWalk"] = round((motion.STRIDE_RUN["px"] / motion.STRIDE_RUN["cycleMs"]) / (hero.STRIDE["walk"]["px"] / hero.STRIDE["walk"]["cycleMs"]), 2)
        m["flightFrames"] = [3, 7]
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
    return m


def export_body(act, frames):
    _, ms, loop = anim.BODY[act]
    im = sheet({d: [f.image for f in frames[d]] for d in DIRS}, FW, FH)
    name = "player_%s" % act
    im.save(os.path.join(OUT_P, name + ".png"))
    hands = {d: [anim._hands(f.rig) for f in frames[d]] for d in DIRS}
    write_json(os.path.join(OUT_P, name + ".json"),
               base(name + ".png", act, FW, FH, ms, loop, PIV, emissiveColors=EMISSIVE, **body_meta(act),
                    handAnchors=hands, anchorNote=ANCHOR_NOTE,
                    carryOverlay="weapons/v3/katana_carry_%s" % act if act in anim.CARRY else None,
                    note="v3 2배 밀도 — 64×96 도트, 화면상 32×48 (계약 §11). 개념 gemini/concept_char/hero3_b."))
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
                    anchor="player_pivot", playerFrameOffset={"x": K.OFF, "y": K.OFF},
                    depth={d: "above" for d in DIRS}, depthByFrame={d: ["above"] * n for d in DIRS}, occlusionBaked=True,
                    depthNote="몸 뒤로 가는 칼집·손잡이 픽셀은 몸 실루엣으로 지워 두었다 → 항상 몸 위에 겹친다(above). "
                              "right 는 칼집이 먼 허리라 몸 밖으로 나온 칼집 끝만 보인다.",
                    sheathMouthAnchors={d: [[x + K.OFF, y + K.OFF] for x, y in mouths[d]] for d in DIRS},
                    sheathMouthNote="칼집 입구(무기 시트 좌표) — 뽑기 이펙트·손 위치 참고용",
                    overlay="player_%s 와 같은 프레임 번호를 같은 시각에 겹친다. 피벗 (64,124) = 주인공 피벗 (32,92)." % act))
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
    o = json.load(open(os.path.join(V2_P, "player_katana_combo%d.json" % n), encoding="utf-8"))
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
                **K.ARC[n], hitOrigin="몸 중심 = 피벗(발)에서 위로 40 도트 (v3 시트 도트 = v2 20px)",
                hitRadiusPx=132, hitNote="임시(아트 메모). v2 66px(pixelScale 1) = v3 132 도트(pixelScale 0.5) — 논리 크기 같음. 시스템 실제 판정값이 우선",
                arcAngleNote=ARC_NOTE, framesBasis="player_katana_combo%d 프레임 번호 (무기·몸·이펙트 공통 기준 = 몸 시트)" % n,
                frameStates=[f["state"] for f in c["frames"]])


def export_combo(n, frames):
    c = K.COMBO[n]
    ms = c["ms"]
    meta = combo_meta(n)
    bim = sheet({d: [f.body for f in frames[d]] for d in DIRS}, FW, FH)
    wim = sheet({d: [f.weapon for f in frames[d]] for d in DIRS}, K.WF, K.WF)
    bname, wname = "player_katana_combo%d" % n, "katana_combo%d" % n
    bim.save(os.path.join(OUT_P, bname + ".png"))
    wim.save(os.path.join(OUT_W, wname + ".png"))
    hands = {d: [f.hands for f in frames[d]] for d in DIRS}
    write_json(os.path.join(OUT_P, bname + ".json"),
               base(bname + ".png", "katana_combo%d" % n, FW, FH, ms, False, PIV, emissiveColors=EMISSIVE, **meta,
                    handAnchors=hands, anchorNote=ANCHOR_NOTE, nextComboSheet=K.ARC[n]["nextCombo"] and "player_" + K.ARC[n]["nextCombo"],
                    note="무기를 든 연격 몸 동작. weapons/v3/katana_combo%d 를 같은 프레임 번호·같은 시각에 겹친다(§6.1)." % n))
    nf = len(ms)
    whands = {d: [{k: [v[0] + K.OFF, v[1] + K.OFF] for k, v in h.items()} for h in hands[d]] for d in DIRS}
    write_json(os.path.join(OUT_W, wname + ".json"),
               base(wname + ".png", "combo%d" % n, K.WF, K.WF, ms, False, K.WPIV, **meta,
                    anchor="player_pivot", playerFrameOffset={"x": K.OFF, "y": K.OFF},
                    depth={d: "above" for d in DIRS}, depthByFrame={d: ["above"] * nf for d in DIRS}, occlusionBaked=True,
                    depthNote="칼·칼집이 몸 뒤로 가는 부분(몸 기준 카메라 반대쪽)은 몸 실루엣으로 지웠고, 쥔 손잡이는 주먹 픽셀로 가렸다 → 항상 above.",
                    handAnchors=whands, gripAnchors={d: [h["handR"] for h in whands[d]] for d in DIRS},
                    handAnchorNote="무기 시트 좌표. gripAnchors = 칼을 쥔 오른손(코등이 바로 뒤). combo3 은 양손(L = 손잡이 끝 쪽).",
                    bladeLocal=[{"thetaDeg": f.get("th"), "elevDeg": f.get("el")} for f in c["frames"]],
                    bladeLocalNote="몸 기준 칼 방향(θ: 0 = 앞, + = 해부 오른쪽 · elev: + = 위). sheathed 프레임은 칼집 안(null).",
                    includesSheath=True, carryHidden="연격 시트에 빈 칼집(허리)이 들어 있으므로 연격 동안 katana_carry_* 는 숨긴다.",
                    overlay="player_katana_combo%d 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 (64,124) = 주인공 피벗 (32,92)." % n,
                    stateNote="sheathed 칼집 안(손잡이를 쥠) · steel 실물 · glow 판정 프레임(날 호박 글로우, 끝 1px 백열 코어) · fade 다음 타로 넘어가는 흐림 · embers 불티",
                    fxNote="베기 이펙트(fx) v3 는 이번 범위 밖 — 기존 fx/katana_combo<n> 을 쓰거나 2배 재출력(계약 §11)"))
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
