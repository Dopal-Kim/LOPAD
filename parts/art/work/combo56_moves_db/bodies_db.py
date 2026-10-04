"""새 기본기 3종 몸 v3 + 무기 v3 오버레이 렌더·내보내기 (계약 §13·§17, 56라운드 Q4 단검 1.3배 · Q9 활 규칙).

몸 96×144 · 피벗 (48,138) · pixelScale 0.5. 무기 오버레이 192×192 · 피벗 (96,186) · playerFrameOffset (48,48)(단검·활 표준 틀).
단검은 combo56_body/dagger56.install()(1.3배 치수)을 이 프로세스에 설치한 뒤 weapons_v3/dagger.gear_frame 으로 그린다.
활은 weapons_v3/bow 의 draw_bow·draw_arrow(활 B · 재 화살 · 혼불 시위) 그대로 — 하늘 조준 놓기만 이 파일에서(bow.gear_frame 의 놓기는 수평 고정).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "combo56_body")))

import moves_db as M  # noqa: E402
import wv3  # noqa: E402
from wv3 import K, Q, EX, hero, DIRS, A  # noqa: E402
import dagger56  # noqa: E402
import dagger as DG  # noqa: E402
import bow as BW  # noqa: E402

SRC = "parts/art/work/combo56_moves_db/build.py body (56라운드 Q40~Q43 새 기본기 — 작업 E2)"
_INSTALLED = False


def install():
    global _INSTALLED
    if not _INSTALLED:
        dagger56.install()
        _INSTALLED = True


# =============================================================================
# 렌더
# =============================================================================
def render_dagger(name):
    install()
    m = M.MOVES[name]
    out = {}
    for d in DIRS:
        lst = []
        for i, raw in enumerate(m["frames"]):
            k = Q.norm(raw)
            p = Q.body_pose(d, k, i)
            R = hero.draw_rig(d, p)
            im, tip = DG.gear_frame(d, name, k, R)
            lst.append(dict(body=R.image, rig=R, weapon=im, tip=hero.to_px(tip), key=k, state=k["state"]))
        out[d] = lst
    return out


def _grips(d, k, R):
    gL, gR = R.anchors["handL"], R.anchors["handR"]
    return (gL[0], gL[1], K.to_screen(d, k["L"])[2]), (gR[0], gR[1], K.to_screen(d, k["R"])[2])


def bow_up_frame(d, k, R, ang, first_release=False):
    """하늘 조준 활. draw/full = bow.gear_frame('bow_aim')(조준 = L−R 방향, 당김이 작으면 재가 맺히는 화살),
    release = 같은 하늘 방향으로 곧은 시위 + 놓는 순간 번쩍(시위 A26 는 tension>0.5 인 놓기 프레임만)."""
    st = k["state"]
    if st in ("draw", "full"):
        im, tip = BW.gear_frame(d, "bow_aim", k, R)
        if tip is not None and st == "full":
            _head_on_top(im, d, k, hero.to_px(tip))
        return im, (None if tip is None else hero.to_px(tip)), None
    if st == "release":
        L = K.Layer()
        gripL, _ = _grips(d, k, R)
        a = wv3.norm3(tuple(l - r for l, r in zip(k["L"], k["R"])))
        flash = k["tension"] > 0.5
        BW.draw_bow(L, d, gripL, a, 4.5, A[26] if flash else A[23], flash=flash)
        im = K.rasterize(L, R, hold_hands=("handL",))
        sx, sy, _ = BW.scr(d, gripL, tuple(c * 3.0 for c in a))      # 화살 생성 점 = 줌통 앞 3(설계)
        return im, None, (sx, sy)
    im, tip = BW.gear_frame(d, "bow_aim", k, R)
    return im, (None if tip is None else hero.to_px(tip)), None


def _head_on_top(im, d, k, tip):
    """가득 당김에서 촉이 활 팔 실루엣 뒤로 가려지는 것 방지(bow56.head_on_top 과 같은 규칙) — 촉 3칸만 위에 다시 찍음."""
    a = wv3.norm3(tuple(l - r for l, r in zip(k["L"], k["R"])))
    sx, sy, _ = K.project(d, a)
    n = math.hypot(sx, sy) or 1.0
    ux, uy = sx / n, sy / n
    px = im.load()
    for j, c in enumerate([A[26], A[25], A[23]]):
        x, y = round(tip[0] - ux * j + K.OFF), round(tip[1] - uy * j + K.OFF)
        if 0 <= x < im.width and 0 <= y < im.height:
            px[x, y] = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,) if isinstance(c, str) else c


def render_bow(name):
    m = M.MOVES[name]
    out = {}
    for d in DIRS:
        lst = []
        for i, raw in enumerate(m["frames"]):
            k = Q.norm(raw)
            p = Q.body_pose(d, k, i)
            R = hero.draw_rig(d, p)
            im, tip, spawn = bow_up_frame(d, k, R, m["angles"][i])
            lst.append(dict(body=R.image, rig=R, weapon=im, tip=tip, spawn=spawn, key=k, state=k["state"]))
        out[d] = lst
    return out


def render(name):
    return render_bow(name) if M.MOVES[name]["weapon"] == "bow" else render_dagger(name)


# =============================================================================
# 검사
# =============================================================================
def check(name, fr):
    pal = wv3.hero_palette()
    wc, bc, partial, edge = set(), set(), False, 0
    for d in DIRS:
        for f in fr[d]:
            wc |= wv3.colors_of(f["weapon"])
            bc |= wv3.colors_of(f["body"])
            partial |= wv3.has_alpha_partial(f["weapon"]) or wv3.has_alpha_partial(f["body"])
            edge += EX.edge_pixels(f["weapon"])
    assert not (wc - pal) and not (bc - pal), (name, "palette")
    assert len(bc) <= 40 and len(wc) <= 16 and not partial and edge == 0, (name, len(bc), len(wc), partial, edge)
    return dict(weaponColors=len(wc), bodyColors=len(bc), edgePixels=edge)


# =============================================================================
# JSON · 내보내기
# =============================================================================
def timing(m):
    st = M.starts(m["ms"])
    total = sum(m["ms"])
    t = dict(total=total)
    if m.get("impact") is not None:
        t["hitAt"] = st[m["impact"]]
        t["activeEndAt"] = st[m["active"][-1]] + m["ms"][m["active"][-1]]
    if m.get("hitFrames"):
        t["hitsAt"] = [st[i] for i in m["hitFrames"]]
    if m.get("releaseFrames"):
        t["releasesAt"] = [st[i] for i in m["releaseFrames"]]
    t["cancelAt"] = st[m["cancel"]] if m.get("cancel") is not None else None
    if m.get("loopFrames"):
        lf = m["loopFrames"]
        t["loopStartAt"] = st[lf[0]]
        t["loopMs"] = sum(m["ms"][i] for i in lf)
        t["startMs"] = st[lf[0]]
        t["endMs"] = sum(m["ms"][lf[-1] + 1:])
    return t


def meta_for(name, m, fr):
    meta = dict(weapon=m["weapon"], version="v3-r56", label=m["label"], basicMove=True,
                r56="56라운드 Q40~Q43 새 기본기(작업 E2)", timingMs=timing(m), frameRoles=m["roles"],
                frameStates=[f["state"] for f in fr[DIRS[0]]],
                framesBasis="player_%s 프레임 번호(몸·무기·이펙트 공통 기준 = 몸 시트)" % name,
                msNote="ms·판정은 아트 임시 제안(보고서 표). 시스템이 바꿔도 판정 프레임 시작 = hitAt 이 맞으면 그림은 맞는다",
                phases=m["phases"], startsFrom=m["startsFrom"], endsWith=m["endsWith"])
    if m.get("cancel") is not None:
        meta["cancelFromFrame"] = m["cancel"]
    if m.get("impact") is not None:
        meta.update(impactFrame=m["impact"], hitFrames=list(m["hitFrames"]), activeFrames=list(m["active"]),
                    glowFrames=sorted(set(m["active"])), anticipationFrames=list(range(m["impact"])),
                    thrust=m["thrust"], thrustNote="몸 중심(판정 원점 = 피벗 위 40 도트)에서 정면(right 기준 angleDeg)으로 fromPx~lengthPx, "
                                                   "폭 widthPx 의 직사각 판정(도트, 월드 px = 도트/4). 참고값 — 시스템 데이터가 기준",
                    hitShape=dict(type="rect", lengthPx=m["thrust"]["lengthPx"], widthPx=m["thrust"]["widthPx"], fromPx=m["thrust"]["fromPx"],
                                  angleDeg=m["thrust"]["angleDeg"], note="§17 판정 모양 rect(찌르기)"),
                    hitOrigin=EX.HIT_ORIGIN_NOTE, hitNote=m["hitNote"])
    if m.get("loopFrames"):
        lf = m["loopFrames"]
        meta.update(loopFrames=lf, loopRange=[lf[0], lf[-1]], startFrames=list(range(lf[0])),
                    endFrames=list(range(lf[-1] + 1, len(m["ms"]))),
                    loopNote="좌클릭 홀드: f0~f1(시작) 1회 → 홀드 동안 loopFrames 반복(f7 끝 → f2) → 떼면 지금 찌르기의 당김 프레임까지 마치고 f8~f9(끝). "
                             "시트 loop 값은 false(시스템이 loopRange 를 반복). 과열 단계는 fx 시트만 바꿈(몸·무기 같음)",
                    stabAngles=m["stabAngles"], stabAnglesNote="각 찌르기 그림 각(화면, 조준 0° 시계 +) — 이펙트 붓획 각과 같음")
    if m.get("releaseFrames"):
        meta.update(releaseFrames=m["releaseFrames"], arrowCount=3,
                    releaseNote="화살 생성 = releaseFrames 시작(timingMs.releasesAt) · arrowSpawnAnchors 위치에서 하늘로(bow_arrow_rain_rise). "
                                "renock 프레임은 시위 위에서 재가 뭉쳐 새 화살이 맺힘(몸에서 뽑지 않음 — 탄창 3 소모는 시스템 수치)",
                    skyAngleDeg=m["angles"], skyAngleNote="프레임별 활 조준의 하늘 각(몸 기준 elev°). 0 = 수평(bow_draw_hold 와 같음)")
    return meta


def export(name, fr):
    m = M.MOVES[name]
    ms = m["ms"]
    meta = meta_for(name, m, fr)
    bname = "player_" + name
    bim = EX.sheet({d: [f["body"] for f in fr[d]] for d in DIRS}, hero.FW, hero.FH)
    bim.save(os.path.join(EX.OUT_P, bname + ".png"))
    hands = {d: [{k: [round(c, 1) for c in hero.to_px(f["rig"].anchors[k])] for k in ("handR", "handL")} for f in fr[d]] for d in DIRS}
    scars = EX.scar_list({d: [type("F", (), {"rig": f["rig"]}) for f in fr[d]] for d in DIRS})
    note = ("56라운드 새 기본기 몸. weapons/v3/%s 를 같은 프레임 번호·같은 시각에 겹친다. " % name) + EX.BODY_NOTE
    data = EX.base(bname + ".png", name, hero.FW, hero.FH, ms, False, hero.PIV, emissiveColors=EX.EMISSIVE, **meta,
                   handAnchors=hands,
                   anchorNote="handAnchors = 프레임별 손 중심(몸 시트 도트, 해부 기준 R 오른손 · L 왼손 — 단검 R 역수 · 활 L 줌통/R 시위). 무기 시트 좌표 = 몸 + (48,48)",
                   scarAnchor=scars, scarAnchorNote=EX.SCAR_NOTE, weaponOverlayV3="weapons/v3/" + name, note=note)
    data["source"] = SRC
    EX.write_json(os.path.join(EX.OUT_P, bname + ".json"), data)
    off = (K.OFF, K.OFF)
    tips = {d: [None if f["tip"] is None else wv3.to_w(f["tip"], off) for f in fr[d]] for d in DIRS}
    if m["weapon"] == "dagger":
        local = [{"thetaDeg": round(f["key"]["th"], 1), "elevDeg": round(f["key"]["el"], 1)} for f in fr[DIRS[0]]]
        design = DG.DESIGN
        ex = dict(bladeLocal=local, bladeLocalNote="몸 기준 무기 방향(θ: 0 = 앞, + = 해부 오른쪽 · elev: + = 위)",
                  bladeTipAnchors=tips, bladeTipNote="단검 끝(무기 시트 좌표) — 이펙트·치명 섬광 위치 참고(56 Q4 1.3배 그림 기준)",
                  includesSheath=False, reverseGrip=True, carryHidden="이 시트 동안 dagger_carry_* 는 숨긴다(이 시트가 손의 단검을 그림).",
                  stateNote="steel 평소 · glow 판정(균열 A23 · 끝 A26 — 판정 프레임만) · embers 불티 · fade 흐림")
        grip = "handR"
    else:
        design = BW.DESIGN
        spawn = {d: [None if f["spawn"] is None else wv3.to_w(f["spawn"], off) for f in fr[d]] for d in DIRS}
        ex = dict(bladeTipAnchors=tips, bladeTipNote="화살촉 끝(무기 시트 좌표). null = 화살 없음(놓기·내림)",
                  arrowSpawnAnchors=spawn,
                  arrowSpawnNote="화살 생성 점(무기 시트 좌표) — releaseFrames 의 줌통 앞. bow_arrow_rain_rise 의 pivot 을 여기에(그 프레임 시작에 1회씩, 3발)",
                  carryHidden="이 시트 동안 bow_carry_* 는 숨긴다(이 시트가 손의 활·화살을 그림).",
                  stateNote="full 가득(시위 A25 · 촉 A26 점) · release 놓는 순간(시위 A26 번쩍 — 3번) · draw/renock 재가 맺히는 새 화살(A21→A23) · settle 내림")
        grip = "handL"
    ex.update(bodySheet=bname, source=SRC,
              overlay="%s 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 = 주인공 피벗 + playerFrameOffset." % bname)
    wv3.write_overlay(name, {d: [f["weapon"] for f in fr[d]] for d in DIRS}, ms, False, name, m["weapon"], hands, grip, design,
                      extra=ex, body_meta=data)
    return data
