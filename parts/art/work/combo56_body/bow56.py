"""56라운드 Q9 활 '누르면 당기고 떼면 발사' — 몸·무기 v3 (4방향, 기존 활 규칙 그대로).

  player_bow_draw_hold + weapons/v3/bow_draw_hold   당김 진행 f0~f5(진행도로 프레임 선택) → 가득 유지 루프 f6~f9 → (선택) 오래 쥠 흔들림 루프 f10~f13
  player_bow_release   + weapons/v3/bow_release     놓기 f0(화살 생성·시위 번쩍) → 따라가기 → 다시 당길 준비 자세(= draw_hold f0 근처)
그림 규칙: weapons_v3/bow.py(활 B · 재 화살 · 혼불 시위)와 gear3.bow_draw(당김 자세) 그대로 — 새 디자인 없음.
시위 빛(Q30): 당김 A21→A23 · 가득 A25(화살촉 끝 A26) · 놓는 순간 A26 번쩍 · 오래 쥠(흔들림) A23 으로 식음.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "weapons_v3")))

import wv3  # noqa: E402
from wv3 import Q, EX, hero, K, DIRS  # noqa: E402
import bow as BW  # noqa: E402

SRC = "parts/art/work/combo56_body/build.py bow (56라운드 Q9 — 활 당겨 떼기)"
bd = Q.bow_draw
K_ = Q.K_

PROG = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
JIT = [(0.0, 0.0), (0.3, -0.2), (0.1, 0.3), (-0.25, 0.1)]                   # 가득 유지: 1px 안팎 떨림
STRAIN = [(0.0, 0.0, 0.0), (0.9, -0.7, 0.5), (-0.6, 0.8, -0.4), (0.7, 0.4, 0.7)]   # 오래 쥠: 화살·활이 흔들림

DRAW_HOLD = dict(
    keys=[bd(p) for p in PROG]
    + [bd(1.0, R=(-3.0 + jx, 5.5, 61.0 + jz)) for jx, jz in JIT]
    + [bd(1.0, R=(-3.0 + sx, 5.5 + sy * 0.4, 61.0 + sz), L=(27.0, -4.5 + sy, 57.0 + sz * 0.6), crouch=3.0, state="draw", tension=0.9)
       for sx, sy, sz in STRAIN],
    ms=[90, 90, 90, 90, 90, 90] + [90, 90, 90, 90] + [70, 70, 70, 70],
    roles=["draw"] * 5 + ["full"] + ["hold"] * 4 + ["strain"] * 4)
RELEASE = dict(
    keys=[bd(1.0, R=(-7.0, 9.5, 62.0), tension=0.7, state="release", lean=-0.4),
          bd(1.0, R=(-4.0, 11.0, 55.0), tension=0.35, state="release", lean=-0.1),
          bd(0.05, tension=0.1),
          bd(0.0)],
    ms=[40, 60, 80, 100],
    roles=["release", "follow", "recover", "ready"])


def render(keys, name_for_gear="bow_aim"):
    out = {}
    for d in DIRS:
        lst = []
        for i, raw in enumerate(keys):
            k = Q.norm(raw)
            p = Q.body_pose(d, k, i)
            R = hero.draw_rig(d, p)
            im, tip = BW.gear_frame(d, name_for_gear, k, R)
            if tip is not None and k["state"] in ("full", "draw") and k["tension"] >= 0.6:
                head_on_top(im, d, k, hero.to_px(tip), A26=k["state"] == "full")
            lst.append(dict(body=R.image, rig=R, weapon=im, tip=None if tip is None else hero.to_px(tip), key=k))
        out[d] = lst
    return out


def head_on_top(im, d, k, tip, A26=True):
    """가득 당김에서 화살촉이 활 팔(몸 실루엣) 뒤로 가려 안 보이던 것(비평) — 촉 3칸만 가림 무시하고 위에 다시 찍음."""
    a = wv3.norm3(tuple(l - r for l, r in zip(k["L"], k["R"])))
    sx, sy, _ = K.project(d, a)
    n = (sx * sx + sy * sy) ** 0.5 or 1.0
    ux, uy = sx / n, sy / n
    px = im.load()
    from wv3 import A
    cols = [A[26] if A26 else A[25], A[25], A[23]]
    for j, c in enumerate(cols):
        x, y = round(tip[0] - ux * j + K.OFF), round(tip[1] - uy * j + K.OFF)
        if 0 <= x < im.width and 0 <= y < im.height:
            px[x, y] = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,) if isinstance(c, str) else c


def grip_spawn(fr, d, i):
    """화살 생성 점(몸 도트) — 줌통(왼손) 앞. 놓기 f0 의 활 손 위치."""
    h = hero.to_px(fr[d][i]["rig"].anchors["handL"])
    return [round(h[0], 1), round(h[1], 1)]


def export(name, spec, fr, extra_meta):
    ms = spec["ms"]
    bname = "player_" + name
    bim = EX.sheet({d: [f["body"] for f in fr[d]] for d in DIRS}, hero.FW, hero.FH)
    bim.save(os.path.join(EX.OUT_P, bname + ".png"))
    hands = {d: [{k: [round(c, 1) for c in hero.to_px(f["rig"].anchors[k])] for k in ("handR", "handL")} for f in fr[d]] for d in DIRS}
    scars = EX.scar_list({d: [type("F", (), {"rig": f["rig"]}) for f in fr[d]] for d in DIRS})
    meta = dict(weapon="bow", version="v3-r56", frameRoles=spec["roles"], frameStates=[f["key"]["state"] for f in fr[DIRS[0]]],
                framesBasis="%s 프레임 번호(몸·무기 공통)" % bname, **extra_meta)
    data = EX.base(bname + ".png", name, hero.FW, hero.FH, ms, False, hero.PIV, emissiveColors=EX.EMISSIVE, **meta,
                   handAnchors=hands, anchorNote="handAnchors = 프레임별 손 중심(몸 시트 도트, L 줌통 · R 시위). 무기 시트 좌표 = 몸 + (48,48)",
                   scarAnchor=scars, scarAnchorNote=EX.SCAR_NOTE, weaponOverlayV3="weapons/v3/" + name,
                   note="56라운드 Q9 활 몸. weapons/v3/%s 를 같은 프레임 번호·같은 시각에 겹친다. " % name + EX.BODY_NOTE)
    data["source"] = SRC
    EX.write_json(os.path.join(EX.OUT_P, bname + ".json"), data)
    off = (K.OFF, K.OFF)
    ex = dict(bladeTipAnchors={d: [None if f["tip"] is None else wv3.to_w(f["tip"], off) for f in fr[d]] for d in DIRS},
              bladeTipNote="화살촉 끝(무기 시트 좌표). 없으면 null(화살 없음)",
              bodySheet=bname, carryHidden="이 시트 동안 bow_carry_* 는 숨긴다(이 시트가 손의 활·화살을 그림).",
              overlay="%s 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 = 주인공 피벗 + playerFrameOffset." % bname,
              stateNote="draw 당김(시위 A21→A23) · full 가득(시위 A25 · 촉 끝 A26) · release 놓는 순간(시위 A26 번쩍) · settle/ready 내림·다시 당길 준비",
              source=SRC)
    if name == "bow_release":
        ex["arrowSpawnAnchors"] = {d: [wv3.to_w(grip_spawn(fr, d, 0), off)] + [None] * (len(ms) - 1) for d in DIRS}
        ex["arrowSpawnNote"] = "화살 생성 점(무기 시트 좌표) — 놓기 f0 의 줌통 앞. bow_perfect_release·bow_muzzle_rapid 의 pivot 을 여기에"
    wv3.write_overlay(name, {d: [f["weapon"] for f in fr[d]] for d in DIRS}, ms, False, name, "bow", hands, "handL", BW.DESIGN,
                      extra=ex, body_meta=data)
    return data


def check(name, fr, pal):
    wc, bc, partial, edge = set(), set(), False, 0
    for d in DIRS:
        for f in fr[d]:
            wc |= wv3.colors_of(f["weapon"])
            bc |= wv3.colors_of(f["body"])
            partial |= wv3.has_alpha_partial(f["weapon"]) or wv3.has_alpha_partial(f["body"])
            edge += EX.edge_pixels(f["weapon"])
    assert not (wc - pal) and not (bc - pal), name
    assert len(bc) <= 40 and len(wc) <= 16 and not partial and edge == 0, (name, len(bc), len(wc), partial, edge)
    return dict(weaponColors=len(wc), bodyColors=len(bc))


def build():
    pal = wv3.hero_palette()
    dh = render(DRAW_HOLD["keys"])
    export("bow_draw_hold", DRAW_HOLD, dh, dict(
        secondaryAction="우클릭 누르는 동안 당김(56라운드 Q9 — 자동 발사 없음)",
        progressDriven=True, progressFrames=[0, 1, 2, 3, 4, 5],
        progressFormula="당김 진행도 p(0~1) → frame = min(5, floor(p*5)) · f5 = 가득(full)",
        fullFrame=5, holdLoop=[6, 9], holdLoopNote="가득 도달 뒤 계속 누르고 있으면 f6~f9 반복(시위 A25 · 1px 떨림)",
        strainLoop=[10, 13], strainLoopNote="채택(56라운드 Q20·Q27) — 너무 오래 쥐면 조준선 흔들림·위력 감소: 화살·활이 흔들리고 시위가 A23 으로 식음. 시작 시점·감소량은 시스템 데이터, 그 시점부터 이 구간을 반복",
        perfectWindowNote="56라운드 Q9: 가득(f5 도달) 직후 0.15초 안에 떼면 '완벽' — 놓는 순간 bow_release + fx bow_perfect_release. 그 전에 떼면 약한 화살",
        drawProgressByFrame=PROG + [1.0] * 4 + [1.0] * 4,
        releaseSheet="bow_release", replaces="bow_aim(우클릭 조준 → 자동 발사) 대신"))
    rl = render(RELEASE["keys"])
    export("bow_release", RELEASE, rl, dict(
        releaseFrame=0, releaseNote="놓는 순간 = f0 시작 → 화살 생성(arrowSpawnAnchors). 일찍 놓은 약한 화살도 같은 시트(시위 번쩍임은 같음 — 화살 fx 로 구분)",
        endsWith="bow_draw_hold f0 근처(다시 당길 준비) — 계속 우클릭이면 바로 bow_draw_hold 로, 아니면 bow_carry_idle",
        perfectFx="bow_perfect_release (완벽 놓기일 때만, f0 시작, arrowSpawnAnchors)"))
    st = dict(bow_draw_hold=check("bow_draw_hold", dh, pal), bow_release=check("bow_release", rl, pal))
    print(st)
    return dh, rl, st


if __name__ == "__main__":
    build()
