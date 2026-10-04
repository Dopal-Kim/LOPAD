"""56라운드 대검 몸·무기 8방향 렌더·내보내기 (Q5 무게 · Q6 8방향 · Q10 기본 차지/꽂아내리기).

산출(게임이 읽음):
  assets/sprites/player/v3/player_<동작>.png/.json     몸 96×144 · 피벗 (48,138) · pixelScale 0.5 · 8행
  assets/sprites/weapons/v3/<동작>.png/.json           대검 오버레이(6동작 합집합 한 틀) · 8행
  동작 = greatsword_sweep_cw · greatsword_cleave · greatsword_sweep_ccw · greatsword_charge · greatsword_charge_slam · greatsword_charge_plunge(신규)
행 순서: down, up, left, right, down-right, down-left, up-right, up-left (기존 4행 그대로 앞에, 대각 4행을 뒤에).
"""
import contextlib
import json
import math
import os

from PIL import Image

import rig8
from rig8 import DIRS4, DIAG, DIRS8, K, Q, EX, hero, wv3
import moves56 as MV
import greatsword as GS

HERE = rig8.HERE
SRC = "parts/art/work/combo56_body/build.py (56라운드 Q5·Q6·Q10 — 대검 무게·8방향·꽂아내리기)"
STATE = os.path.join(HERE, "state56.json")
V_TYPE = ("greatsword_cleave", "greatsword_charge_slam")
DIAG_V_CAP = -46.0          # 대각 내려찍기: 칼 기울기 하한(화면에서 대각으로 읽히게)
DIAG_V_TURN = 12.3          # 대각 내려찍기: 칼 수평 방향을 화면 45° 바닥 각보다 이만큼 더 옆으로
DIAG_TURN = ("down-right", "down-left")   # 위 대각(up-*)은 보정하지 않음 — 칼이 몸 뒤(화면 위쪽 땅)로 내려가 up 과 같이 대부분 가려진다.
                                          # 보정하면 칼끝이 바닥에 닿는 한 화면에서 '아래-옆'을 가리켜 조준(위-옆)과 어긋나 보임(비평 2회차)


@contextlib.contextmanager
def dirs8():
    """hero.DIRS(=EX·anim·wv3 공용 목록)를 잠시 8방향으로 — 내보내기 도구(시트·JSON·틀 맞춤)를 그대로 쓴다."""
    n = len(hero.DIRS)
    assert hero.DIRS == DIRS4
    hero.DIRS.extend(DIAG)
    try:
        yield
    finally:
        del hero.DIRS[n:]


def diag_turn(d):
    """대각 내려찍기 θ 보정(도) — 칼 수평 성분을 화면 대각 쪽으로 돌림(리그 바닥 각 70.7° → 32.7°)."""
    a = rig8.ground_deg(d)
    s = math.radians(rig8.SCREEN_DEG[d])
    a45 = math.degrees(math.atan2(math.copysign(1, math.sin(s)), math.copysign(1, math.cos(s))))
    h = a45 - math.copysign(DIAG_V_TURN, math.sin(math.radians(a45))) * math.copysign(1, math.cos(math.radians(a45)))
    return ((h - a + 180.0) % 360.0) - 180.0


def adjust_key(name, d, k):
    """대각 + 내려찍기류: 칼이 앞·아래를 향하는 프레임만 θ 를 돌리고 기울기를 DIAG_V_CAP 까지 세움(칼끝은 여전히 바닥에 닿음)."""
    if d not in DIAG_TURN or name not in V_TYPE or k is None:
        return k
    if abs(k["th"]) > 90 or k["el"] > -10:
        return k
    s = max(0.0, min(1.0, (-k["el"] - 10.0) / 40.0))
    o = dict(k)
    t = diag_turn(d) * s
    o["th"] = k["th"] + t
    if k.get("hth") is not None:
        o["hth"] = k["hth"] + t
    o["el"] = k["el"] + (max(k["el"], DIAG_V_CAP) - k["el"]) * s
    o["extra"] = dict(k.get("extra") or {})
    return o


def plant_point(d, k):
    """꽂아내리기: 수직 칼이 바닥에 닿는 점(몸 도트)."""
    f, r, _ = k["R"]
    q = K.to_screen(d, (f, r, 0.0))
    return hero.to_px(q[:2])


def clip_underground(im, d, k):
    """땅속(칼끝 z < 0)으로 들어간 수직 칼 부분을 지움(448 캔버스, 몸 도트 + CANVAS_OFF)."""
    gx, gy = plant_point(d, k)
    ox, oy = GS.CANVAS_OFF
    gx, gy = gx + ox, gy + oy
    px = im.load()
    for y in range(int(math.floor(gy)) + 1, im.height):
        for x in range(int(gx) - 14, int(gx) + 15):
            if 0 <= x < im.width and px[x, y][3]:
                px[x, y] = (0, 0, 0, 0)
    return im


def render(name):
    m = MV.GS[name]
    out = {}
    for d in DIRS8:
        lst = []
        for i, raw in enumerate(m["frames"]):
            k = Q.norm(adjust_key(name, d, raw))
            p = rig8.body_pose8(d, k, i)
            R = rig8.draw_rig8(d, p)
            im, tip = GS.gear_frame(d, name, k, R)
            plant = None
            if name == "greatsword_charge_plunge" and i in MV.PLANT_FRAMES:
                clip_underground(im, d, k)
                plant = plant_point(d, k)
            tip = hero.to_px(tip)
            if plant is not None:
                tip = plant                                 # 꽂힌 동안 보이는 칼끝 = 꽂힌 자리
            lst.append(dict(body=R.image, rig=R, weapon=im, tip=tip, state=k["state"], key=k, plant=plant))
        out[d] = lst
    return out


def check_tips(name, fr):
    m = MV.GS[name]
    for d in DIRS8:
        for i, f in enumerate(fr[d]):
            k = f["key"]
            z = Q.gs_tip_z(k)
            planted = k["el"] <= -40 or (name == "greatsword_charge_plunge" and i in MV.PLANT_FRAMES)
            assert planted or z >= -0.5, (name, d, i, round(z, 1))


# =============================================================================
# JSON
# =============================================================================
ROW_TABLE = [dict(row=i, direction=d, screenDeg=rig8.SCREEN_DEG[d],
                  body=("측면" if d in ("left", "right") else "정면" if d == "down" else "뒷면" if d == "up"
                        else ("정면 3/4" if d.startswith("down") else "뒷면 3/4"))) for i, d in enumerate(DIRS8)]
DIR_NOTE = ("56라운드 Q6 8방향: 행 = down, up, left, right, down-right, down-left, up-right, up-left (기존 4행 순서 그대로 앞에 두고 대각 4행을 뒤에 더함). "
            "대각 = 화면 45°(마우스 방향 8분할: 조준각 -22.5°~22.5° = right … 시계 방향). 대각 행은 회전·반전이 아니라 따로 그린 그림 — 판정·fx 각도는 그대로 조준각. "
            "대각 몸은 정면/뒷면 몸 Rig 에 3/4 단서(가슴 비틀림·머리·디딤발이 바라보는 쪽으로), 무기·손은 대각 바닥 각으로 투영(리그 바닥 압축 0.35 때문에 화면 45° = 바닥 70.7°). "
            "아래 대각 내려찍기(cleave·charge_slam, down-right·down-left)는 화면에서 대각으로 읽히도록 칼 수평 성분을 더 옆으로 돌리고(±38°) 기울기를 −46° 까지 세움(칼끝은 바닥에 닿음). "
            "위 대각(up-right·up-left)의 내려찍기는 up 과 같이 칼이 몸 너머 땅으로 내려가 대부분 가려진다 — 방향은 바닥 fx(균열·붓획)가 보여 줌.")


def hit_shape(m):
    if not m.get("hitShape"):
        return None
    hs = dict(m["hitShape"])
    Rd = MV.dots(MV.R_GS)
    hs["R"] = {"world": MV.R_GS, "dots": Rd}
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
    elif hs["type"] == "ring":
        hs["radiusPx"] = round(Rd * hs["radiusR"], 1)
    hs["units"] = "…Px = 도트(pixelScale 0.5, 월드 px = 도트 / 4). 각도: 조준 0°, 화면 시계 + (§17). 원점 = 판정 원점(피벗 위 40 도트)"
    hs["reference"] = "참고값 — 시스템 데이터(§17)가 기준"
    return hs


def meta_for(name, m, fr):
    tm = MV.timing(m)
    meta = dict(weapon="greatsword", version="v3-r56", comboSet="G-C 관성 순환", label=m["label"], timingMs=tm,
                frameStates=[f["state"] for f in fr[DIRS8[0]]], frameRoles=m["roles"],
                framesBasis="player_%s 프레임 번호(몸·무기·이펙트 공통 기준 = 몸 시트)" % name,
                weightNote="56라운드 Q5 무게: windup 들어 올림 → hold 머리 위/뒤에서 잠깐 버팀(긴 선딜) → heave → strike(판정) → drag 칼 무게에 몸이 끌려감 → catch 버팀",
                msNote="ms 는 아트 제안값. 55라운드 Q29(예전 템포 유지)대로 늘여 재생해도 impactFrame 시작 = hitAt 만 맞으면 그림은 맞는다(관성 공속은 재생 속도로). "
                       "무게를 살리려면 선딜(hold)과 drag 구간을 늘이고 strike 는 짧게 두기를 권장",
                directionRows=ROW_TABLE, directionNote=DIR_NOTE, dirTransform="drawn8",
                dirTransformNote="8방향 모두 그림이 있음(회전·반전 없음). 조준각을 8분할해 행을 고른다. 판정·fx 는 조준각 그대로(§17 회전 규칙)")
    if m.get("comboIndex"):
        meta["comboIndex"] = m["comboIndex"]
    if m.get("impact") is not None:
        st = MV.starts(m["ms"])
        meta.update(impactFrame=m["impact"], hitFrames=list(m["active"]), activeFrames=list(m["active"]),
                    glowFrames=sorted(set(m["active"]) | {m["impact"]}), cancelFromFrame=m.get("cancel"),
                    anticipationFrames=list(range(m["impact"])), recoverFrames=list(range(m["active"][-1] + 1, len(m["ms"]))),
                    holdFrames=[i for i, r in enumerate(m["roles"]) if r == "hold"],
                    dragFrames=[i for i, r in enumerate(m["roles"]) if r in ("drag", "planted")],
                    hitOrigin=EX.HIT_ORIGIN_NOTE)
        hs = hit_shape(m)
        if hs:
            meta["hitShape"] = hs
        if m["hitShape"]["type"] == "arc":
            meta.update(arcFromDeg=m["arc"][0], arcToDeg=m["arc"][1], arcDeg=abs(m["arc"][1] - m["arc"][0]),
                        arcNote="그림의 휘두름 방향(from → to). 화면각(조준 0°, 시계 +). 8방향 모두 조준 방향 기준")
        if m.get("step"):
            meta["stepPx"] = dict(world=m["step"]["world"], dots=MV.dots(m["step"]["world"]), frames=m["step"]["frames"],
                                  note="내딛기 참고값(§17, 월드 px) — 방향키를 누를 때만. 그림은 제자리, 이동은 시스템")
            meta["stepStartMs"] = st[m["step"]["frames"][0]]
        if m.get("dragStep"):
            ds = dict(m["dragStep"])
            ds["dots"] = MV.dots(ds["world"])
            ds["startMs"] = st[ds["frames"][0]]
            meta["dragStepPx"] = ds
    for k in ("phases", "loopFrames", "stages", "next", "startsFrom", "endsWith", "groundCrack", "waveSheet", "waveAt"):
        if k in m:
            meta[{"next": "nextMove"}.get(k, k)] = m[k]
    if "loopFrames" in m:
        meta.update(loopRange=[m["loopFrames"][0], m["loopFrames"][-1]], holdFrame=m["loopFrames"][0],
                    loopNote="f0~f2 들어 올림 1회 → 홀드 동안 loopFrames 반복(시스템이 loopRange 를 반복 재생). 시트 loop 값은 false")
    if name == "greatsword_charge_slam":
        meta["chargeBasicNote"] = ("56라운드 Q10: 기본 차지 = 칼로 직접 강하게 내려침, 충격파 링 없음(greatsword_charge_ring 은 쓰지 않음). "
                                   "땅 충격 = greatsword_ground_crack(1·2단 m, 3단 l)")
    if name == "greatsword_charge_plunge":
        meta.update(chargeAwakenedNote="56라운드 Q10: 개성 발현 후 차지 — 휘두르지 않고 칼을 땅에 수직으로 꽂아 마우스 방향 충격파(greatsword_plunge_wave)",
                    plantFrames=sorted(MV.PLANT_FRAMES),
                    plantNote="plantAnchors = 칼이 바닥에 꽂힌 점(몸 시트 도트, 꽂힌 프레임만, 나머지 null). 충격파·균열 fx 의 pivot 을 여기에. 땅속 칼 부분은 그리지 않음")
    return meta


def export_move(name, fr, frame):
    m = MV.GS[name]
    ms = m["ms"]
    meta = meta_for(name, m, fr)
    bname = "player_" + name
    bim = EX.sheet({d: [f["body"] for f in fr[d]] for d in DIRS8}, hero.FW, hero.FH)
    bim.save(os.path.join(EX.OUT_P, bname + ".png"))
    hands = {d: [{k: [round(c, 1) for c in hero.to_px(f["rig"].anchors[k])] for k in ("handR", "handL")} for f in fr[d]] for d in DIRS8}
    scars = EX.scar_list({d: [type("F", (), {"rig": f["rig"]}) for f in fr[d]] for d in DIRS8})
    if name == "greatsword_charge_plunge":
        meta["plantAnchors"] = {d: [None if f["plant"] is None else [round(c, 1) for c in f["plant"]] for f in fr[d]] for d in DIRS8}
    data = EX.base(bname + ".png", name, hero.FW, hero.FH, ms, False, hero.PIV, emissiveColors=EX.EMISSIVE, **meta,
                   handAnchors=hands, anchorNote="handAnchors = 프레임별 손 중심(몸 시트 도트, R 코등이 쪽 · L 손잡이 끝). 무기 시트 좌표 = 몸 + playerFrameOffset",
                   scarAnchor=scars, scarAnchorNote=EX.SCAR_NOTE + " 대각: down-* = 정면 3/4(visible:false), up-* = 뒷면 3/4(visible:true).",
                   weaponOverlayV3="weapons/v3/" + name,
                   note="56라운드 대검 몸(8방향). weapons/v3/%s 를 같은 프레임 번호·같은 시각에 겹친다. " % name + EX.BODY_NOTE)
    data["layout"] = "rows = directions (down, up, left, right, down-right, down-left, up-right, up-left), columns = frames"
    data["source"] = SRC
    EX.write_json(os.path.join(EX.OUT_P, bname + ".json"), data)
    fw, fh, ox, oy = frame
    tips = {d: [None if f["tip"] is None else [round(f["tip"][0] + ox, 1), round(f["tip"][1] + oy, 1)] for f in fr[d]] for d in DIRS8}
    local = {d: [{"thetaDeg": round(f["key"]["th"], 1), "elevDeg": round(f["key"]["el"], 1)} for f in fr[d]] for d in DIRS8}
    ex = dict(includesSheath=False, carryHidden="이 시트 동안 greatsword_carry_* 는 숨긴다(이 시트가 손의 대검을 그림).",
              stateNote="steel 평소(홈 혼불 1px 은은) · glow 판정(날 가장자리 A25/A23 + 홈 A26) · charge 홀드(평소 그림 — 단계 번쩍임은 fx)",
              **{k: v for k, v in GS.DESIGN.items() if k not in ("design", "designRef", "glowRule", "colorBudget", "colorNote")},
              bladeLocal=local[DIRS8[0]], bladeLocalByDirection=local,
              bladeLocalNote="몸 기준 무기 방향(θ: 0 = 앞, + = 해부 오른쪽 · elev: + = 위). 대각 내려찍기는 방향마다 다름(bladeLocalByDirection)",
              bladeTipAnchors=tips, bladeTipNote="칼끝(무기 시트 좌표). 8방향. 붓획 fx·칼끝 리본·차지 번쩍임 위치 참고",
              bodySheet=bname, source=SRC,
              overlay="%s 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 = 주인공 피벗 + playerFrameOffset." % bname)
    if name == "greatsword_charge_plunge":
        ex["plantAnchors"] = {d: [None if f["plant"] is None else [round(f["plant"][0] + ox, 1), round(f["plant"][1] + oy, 1)] for f in fr[d]]
                              for d in DIRS8}
    design = {k: GS.DESIGN[k] for k in ("design", "designRef", "glowRule", "colorBudget", "colorNote")}
    wv3.write_overlay(name, {d: [f["weapon"] for f in fr[d]] for d in DIRS8}, ms, False, name, "greatsword", hands, "handR", design,
                      extra=ex, body_meta=data, frame=frame)
    wj = os.path.join(EX.OUT_W, name + ".json")
    j = json.load(open(wj, encoding="utf-8"))
    j["layout"] = data["layout"]
    EX.write_json(wj, j)
    return data


def crop(all_frames):
    frame, box = wv3.fit_frame([{d: [f["weapon"] for f in fr[d]] for d in DIRS8} for fr in all_frames.values()], GS.CANVAS_OFF)
    for fr in all_frames.values():
        for d in DIRS8:
            for f in fr[d]:
                f["weapon"] = f["weapon"].crop(box)
    return frame


def check_colors(name, fr, pal):
    wc, bc, partial, edge = set(), set(), False, 0
    for d in DIRS8:
        for f in fr[d]:
            wc |= wv3.colors_of(f["weapon"])
            bc |= wv3.colors_of(f["body"])
            partial |= wv3.has_alpha_partial(f["weapon"]) or wv3.has_alpha_partial(f["body"])
            edge += EX.edge_pixels(f["weapon"])
    assert not (wc - pal) and not (bc - pal), (name, "색이 주인공 팔레트 밖")
    assert len(bc) <= 40 and len(wc) <= 16 and not partial and edge == 0, (name, len(bc), len(wc), partial, edge)
    return dict(weaponColors=len(wc), bodyColors=len(bc), edgePixels=edge)


def build(names=None):
    names = names or MV.ORDER
    assert set(names) == set(MV.ORDER), "틀(합집합)을 맞추려면 6동작을 함께 빌드"
    pal = wv3.hero_palette()
    frs = {}
    for n in names:
        frs[n] = render(n)
        check_tips(n, frs[n])
        print(n, "rendered")
    with dirs8():
        frame = crop(frs)
        print("greatsword r56 frame", frame)
        stats = {}
        for n in names:
            export_move(n, frs[n], frame)
            stats[n] = check_colors(n, frs[n], pal)
            print(n, "ok", MV.timing(MV.GS[n]), stats[n])
    ch = frs["greatsword_charge"]
    hold = MV.GS["greatsword_charge"]["loopFrames"][0]
    state = dict(gsFrame=list(frame), weaponStats=stats,
                 chargeBlade={d: [[round(c, 1) for c in hero.to_px(ch[d][hold]["rig"].anchors["handR"])], [round(c, 1) for c in ch[d][hold]["tip"]]]
                              for d in DIRS8})
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    return frs, frame
