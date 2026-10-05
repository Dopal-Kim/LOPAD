"""무기 1차·2차 각성 오버레이 시트 — weapons/v4/<weapon>_<branch>_{a1,a2,a2_glow}_<동작>.

원 무기 시트(weapons/v3/<weapon>_<동작>) 프레임마다 render.render 를 돌려 세 층을 얻는다.
틀·피벗·프레임·ms·행 = 기존 weapons/v3/<weapon>_<동작>_awaken(60라운드)과 같다(같은 PAD, pivotDelta).
"""
import os
import sys

import g61 as Z
import render as RD
from g61 import PO, OV


def action(sheet):
    return sheet.split("_", 1)[1]


def names(weapon, bid, sheet):
    a = action(sheet)
    return "%s_%s_a1_%s" % (weapon, bid, a), "%s_%s_a2_%s" % (weapon, bid, a), "%s_%s_a2_glow_%s" % (weapon, bid, a)


def job(arg):
    weapon, sheet, bids = arg
    j, fr = Z.K57.grid_frames("weapons/v3/" + sheet)
    note = None
    try:
        blade_only = OV.body_in_overlay_masks(j, sheet, fr)
    except AssertionError as e:
        blade_only = {}
        note = "bodyInOverlayFrames 마스크 크기 불일치 — 몸이 든 칸은 오버레이 비움(%s)" % (e,)
    skip = set(j.get("bodyInOverlayFrames") or []) if (note and j.get("bodyInOverlayFrames")) else set()
    for (d, i), im in blade_only.items():
        fr[d][i] = im
    glow = set(j.get("glowFrames") or [])
    tips = j.get("bladeTipAnchors") if isinstance(j.get("bladeTipAnchors"), dict) else None
    grips = j.get("gripAnchors") if isinstance(j.get("gripAnchors"), dict) else None
    hands = j.get("handAnchors") if isinstance(j.get("handAnchors"), dict) else None
    states = j.get("frameStates")
    st_ms = Z.P.starts(j["frameDurationsMs"])
    out = {b: ({}, {}, {}) for b in bids}
    for d in j["directions"]:
        for b in bids:
            for k in range(3):
                out[b][k][d] = []
        for i, im in enumerate(fr[d]):
            tip = tips[d][i] if tips else None
            grip = grips[d][i] if grips and grips.get(d) else None
            hr = hands[d][i].get("handR") if hands and hands.get(d) and hands[d][i] else None
            sh = False
            refine = False
            if weapon == "katana":
                sh = (tips is not None and tip is None) or bool(states and states[i] in OV.SHEATHED_STATES)
                refine = bool(states) and not tips
            for b in bids:
                ims = RD.render(weapon, b, im, tip=tip, grip=grip, hand_r=hr, state=states[i] if states else None, glow=i in glow,
                                ms0=st_ms[i], sheathed=sh, refine=refine, skip=i in skip)
                for k in range(3):
                    out[b][k][d].append(ims[k])
    ox, oy = Z.P.PAD[weapon][0], Z.P.PAD[weapon][1]
    base = {k: j[k] for k in OV.COPY if k in j}
    for k in ("frames", "frameWidth", "frameHeight", "glowFrames"):
        base.pop(k, None)
    pv = j.get("pivot", {"x": 96, "y": 186})
    po = j.get("playerFrameOffset", {"x": 48, "y": 48})
    base["pivot"] = {"x": pv["x"] + ox, "y": pv["y"] + oy}
    base["playerFrameOffset"] = {"x": po["x"] + ox, "y": po["y"] + oy}
    base["weaponSheetPivot"] = pv
    base["pivotDelta"] = {"x": ox, "y": oy}
    if note:
        base["bodyInOverlayNote"] = note
    made = []
    for b in bids:
        import br61
        br = br61.REG[b]
        bid, ko, line, paths = Z.branch_info(weapon, b)
        n1, n2, n3 = names(weapon, b, sheet)
        tint = {pid: rgb for pid, (pko, rgb) in paths.items()}
        common = dict(base, weapon=weapon, branch=b, branchName=ko, branchLine=line, sameFrameAs="weapons/v3/%s_awaken" % sheet,
                      loopFrames=br.tn if not br.reuse else PO.LOOP[weapon][0], loopMs=80,
                      loopRule="순환 위상 = (그 프레임 시작 ms ÷ 80ms) mod loopFrames — 시트마다 같은 속도",
                      p12="61 단계 4 P12 — 계약 art §26, 설계 decisions/2026-10-05-P12-weapon-growth.md")
        drawRule = ("주인공 피벗에 이 시트 pivot 을 맞춰(원 무기 pivot + pivotDelta) 무기 시트 '%s' 와 같은 프레임 번호(row*atlas.grid.columns+col)·같은 시각으로 겹친다. "
                    "순서: 무기 → %s(1차) → %s(2차 덧붙임) → %s(2차 빛, pathTint 곱) → _ki/_grudge. 기존 _awaken 대신 쓴다(1차 각성 런에서만)") % (sheet, n1, n2, n3)
        m1 = dict(common, overlayOf="weapons/v3/" + sheet, depth="above_weapon", awakenStage=1, design=br.a1_design, drawRule=drawRule,
                  reusedFrom=("weapons/v3/%s_awaken" % sheet) if br.reuse else None,
                  glowRule="glowFrames(무기 시트 판정 순간)에 가장 밝음")
        if not br.reuse:
            m1.pop("reusedFrom")
        Z.write_sheet("weapons", n1, j["directions"], out[b][0], j["frameDurationsMs"], m1, loop=j.get("loop", False), glow=glow)
        m2 = dict(common, overlayOf="weapons/v4/" + n1, depth="above_a1", awakenStage=2, design=br.a2_design, drawRule=drawRule,
                  glowSheet="weapons/v4/" + n3, pathTint=tint, trailTint=tint,
                  trailRule="2차 각성 뒤 이 무기의 휘두름 궤적 fx 를 trailTint[길] 로 물들인다(새 시트 없음, 계약 §26)")
        Z.write_sheet("weapons", n2, j["directions"], out[b][1], j["frameDurationsMs"], m2, loop=j.get("loop", False), glow=glow)
        m3 = dict(common, overlayOf="weapons/v4/" + n2, depth="above_a2", awakenStage=2, design=br.glow_design, drawRule=drawRule,
                  tintable=True, pathTint=tint,
                  tintRule="회백 마스크(X0·무채 G11~G13). 고른 2차 길의 pathTint 를 setTint(곱)로 입혀 a2 위에 그린다. 블렌드 보통(NORMAL) 권장 — ADD 는 어둠 속에서 과함")
        Z.write_sheet("weapons", n3, j["directions"], out[b][2], j["frameDurationsMs"], m3, loop=j.get("loop", False), glow=glow)
        made += [n1, n2, n3]
    return sheet, made


def build(weapons=Z.WEAPONS, only=None, procs=4):
    from multiprocessing import Pool
    jobs = []
    for w in weapons:
        bids = [b[0] for b in Z.BRANCHES[w] if not os.environ.get("GROWTH_BRANCHES") or b[0] in os.environ["GROWTH_BRANCHES"].split(",")]
        if not bids:
            continue
        for s in Z.sheets_of(w):
            if only and not any(o in s for o in only):
                continue
            jobs.append((w, s, bids))
    with Pool(procs) as p:
        for s, made in p.imap_unordered(job, jobs):
            print(s, len(made), flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    ws = [x for x in a if x in Z.WEAPONS] or list(Z.WEAPONS)
    only = [x for x in a if x not in Z.WEAPONS] or None
    build(ws, only)
