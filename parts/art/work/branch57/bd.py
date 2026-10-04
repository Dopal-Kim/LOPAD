"""57라운드 갈래 1단 — 단검 부채꼴 투척 · 활 속사 연사 몸·무기 (설계안 2.4·2.5, 57 Q22~Q37 '단검 부채꼴 투척 입력 = 대쉬 공격 교체').

  dagger_fan_throw  질풍(疾風) 1단 B — 대쉬 직후 0.3초 안 좌클릭: 왼손에 재 송곳니 3자루가 맺히고(오른손 단검은 그대로 역수)
                    몸을 비틀어 왼손 역손 뿌리기로 부채꼴 3개(30°) 투척. 투사체 = fx/v3/dagger_thrown
  bow_rapid_loop    속사(速射) 1단 A — 좌클릭 홀드 연사: 반쯤 당겨 바로 놓기를 초당 5발(루프 400ms = 2발) — 시위 위에 재가 맺혀 새 화살

키 형식 = hero_v3/gear3.K_ (θ, elev, hth, hr, hz, R, L, off, state, lunge, crouch, tw, lean, tuck, tension).
로컬 (f 앞, r 해부 오른쪽, z 위) 설계 단위(1 = 1.5 도트). 단검은 combo56_body/dagger56.install()(56 Q4 1.3배) 위에서 그린다.
산출: player/v3/player_{dagger_fan_throw,bow_rapid_loop} · weapons/v3/{dagger_fan_throw,bow_rapid_loop}  (기존 시트는 건드리지 않음)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "weapons_v3"))
sys.path.insert(0, os.path.join(WORK, "combo56_body"))

import wv3  # noqa: E402
from wv3 import K, Q, EX, hero, DIRS, A, G  # noqa: E402
import dagger56  # noqa: E402
import dagger as DG  # noqa: E402
import bow as BW  # noqa: E402

dagger56.install()
SRC = "parts/art/work/branch57/build.py body (57라운드 갈래 1단 — 단검 부채꼴 투척 · 활 속사 연사)"
VERSION = "v3-r57-branch"
K_ = Q.K_
READY_DG = Q.READY_DG
bd = Q.bow_draw
FAN_DEG = (-15.0, 0.0, 15.0)        # 부채꼴 3개 30°(설계안 2.4 — 전체 폭 30°)


def starts(ms):
    s, t = [], 0
    for m in ms:
        s.append(t)
        t += m
    return s


# =============================================================================
# 1. 단검 부채꼴 투척
# =============================================================================
def _ft(L, fan, lunge, crouch, tw, lean, state="steel", th=150, el=-30, hth=30, hr=9, hz=45, **kw):
    return K_(th, el, hth, hr, hz, L=L, off="free", state=state, lunge=lunge, crouch=crouch, tw=tw, lean=lean, fan=fan, **kw)


FAN_THROW = dict(
    weapon="dagger", label="부채꼴 투척(질풍 1단 — 대쉬 직후 좌클릭)",
    frames=[
        # 0 gather — 대쉬에서 미끄러지며 멈춤, 왼손을 오른가슴 앞으로 — 손가락 사이에 재가 뭉쳐 송곳니 3자루가 맺힘(작게)
        _ft((7.0, 5.0, 50.0), "form", 0.3, 5.5, 0.35, 1.0),
        # 1 wind — 몸을 오른쪽으로 비틀며 왼손을 오른어깨 뒤로(역손 뿌리기 준비), 송곳니 다 맺힘
        _ft((-2.0, 13.0, 60.0), "held", -0.2, 6.8, 1.05, 0.5),
        # 2 release(투척 순간) — 왼팔이 앞·왼쪽으로 쓸려 나가며 3자루를 놓음
        _ft((25.0, -7.0, 55.0), "release", 0.9, 7.2, -0.6, 1.7),
        # 3 follow — 왼팔이 왼쪽으로 끝까지, 몸이 따라 돎
        _ft((14.0, -25.0, 52.0), None, 1.0, 7.2, -0.95, 1.5),
        # 4 recover — 왼손이 가드로 돌아옴
        _ft((10.0, -9.0, 47.0), None, 0.5, 5.0, -0.2, 1.1),
        READY_DG],
    ms=[40, 60, 40, 60, 80, 90],
    roles=["gather(송곳니가 맺힘)", "wind(비틀어 감음)", "release(투척 — 투사체 생성)", "follow", "recover", "ready"],
    releaseFrame=2, cancel=4,
    startsFrom="player_dash 끝(대쉬 직후 0.3초 안 좌클릭 — 대쉬 공격 교체, 57 Q22~Q37)",
    endsWith="READY_DG(기본 연격 끝 겨눔) → dagger_carry_idle",
    phases={"gather": [0], "wind": [1], "release": [2], "follow": [3], "recover": [4, 5]},
)


def fang_dirs(d, L_loc, fan):
    """왼손에 쥔 송곳니 3자루 방향(로컬). held/form = 손에서 앞·위로 부채처럼."""
    base_th = {"form": 40.0, "held": 70.0}[fan]
    out = []
    for j, off in enumerate((-22.0, 0.0, 22.0)):
        out.append(K.dir3(base_th + off, 10.0 - 6.0 * j))
    return out


def dagger_gear(d, k, Rg):
    """오른손 역수 단검(56 1.3배) + 왼손 송곳니 3자루(gather·wind 칸)."""
    Lr = K.Layer()
    v = K.dir3(k["th"], k["el"])
    gR = Rg.anchors["handR"]
    tip = DG.draw_dagger(Lr, d, (gR[0], gR[1], K.to_screen(d, k["R"])[2]), v, k["state"])
    fan = (k.get("extra") or {}).get("fan")
    hold = ("handR",)
    if fan in ("form", "held"):
        gL = Rg.anchors["handL"]
        zL = K.to_screen(d, k["L"])[2]
        saved = (DG.FANG, DG.GRIP)
        DG.FANG, DG.GRIP = saved[0] * (0.55 if fan == "form" else 0.72), saved[1] * 0.7
        try:
            for j, vv in enumerate(fang_dirs(d, k["L"], fan)):
                DG.draw_dagger(Lr, d, (gL[0], gL[1], zL + 0.3 * (j - 1)), vv, "fade" if fan == "form" else "steel")
        finally:
            DG.FANG, DG.GRIP = saved
        hold = ("handR", "handL")
    return K.rasterize(Lr, Rg, hold_hands=hold), tip


def render_dagger(m):
    out = {}
    for d in DIRS:
        lst = []
        for i, raw in enumerate(m["frames"]):
            raw = dict(raw)
            fan = raw.pop("fan", None) if "fan" in raw else (raw.get("extra") or {}).get("fan")
            ex = dict(raw.get("extra") or {})
            ex.pop("fan", None)
            raw["extra"] = ex
            kk = Q.norm(raw)
            kk["extra"] = dict(ex, fan=fan) if fan else ex
            p = Q.body_pose(d, dict(kk, extra=ex), i)
            Rg = hero.draw_rig(d, p)
            im, tip = dagger_gear(d, kk, Rg)
            lst.append(dict(body=Rg.image, rig=Rg, weapon=im, tip=hero.to_px(tip), key=kk, state=kk["state"], fan=fan))
        out[d] = lst
    return out


# =============================================================================
# 2. 활 속사 연사 — 시작 2 · 루프 8(2발: renock → draw(반) → release → follow) · 끝 2
# =============================================================================
def _half(p, j=(0.0, 0.0), **kw):
    R0 = tuple(a + (b - a) * p for a, b in zip((20.0, 0.5, 56.0), (-3.0, 5.5, 61.0)))
    R0 = (R0[0] + j[0], R0[1], R0[2] + j[1])
    d = dict(R=R0, crouch=2.6, tw=0.55, lean=-0.15, tension=p, state="draw")
    d.update(kw)
    return bd(p, **d)


def _rel(j=(0.0, 0.0), tension=0.62, **kw):
    d = dict(R=(1.5 + j[0], 7.5, 60.0 + j[1]), tension=tension, state="release", lean=-0.25, crouch=2.6, tw=0.6)
    d.update(kw)
    return bd(0.6, **d)


RAPID = dict(
    weapon="bow", label="속사 연사(속사 1단 — 좌클릭 홀드, 초당 5발)",
    keys=[
        _half(0.25, crouch=2.2, tw=0.4),                     # 0 start 활을 앞으로 들어 올림
        _half(0.45, crouch=2.4, tw=0.5),                     # 1 start 반쯤 당김(첫 발 직전)
        _half(0.08),                                          # 2 renock — 시위 위에 재가 맺혀 새 화살
        _half(0.6),                                           # 3 draw 반 당김(가득 아님 — 속사)
        _rel(),                                               # 4 release 1 (화살 생성)
        _rel((-1.0, -1.5), tension=0.3, lean=-0.1),          # 5 follow
        _half(0.08, (0.4, 0.3)),                              # 6 renock
        _half(0.6, (0.5, -0.4)),                              # 7 draw
        _rel((0.6, 0.4)),                                     # 8 release 2
        _rel((-0.6, -1.2), tension=0.3, lean=-0.1),          # 9 follow → f2 로 이어짐
        bd(0.05, tension=0.1),                                # 10 end 내림
        bd(0.0)],                                             # 11 end ready(= bow_draw_hold f0 근처)
    ms=[40, 40, 50, 50, 50, 50, 50, 50, 50, 50, 70, 90],
    roles=["start", "start", "renock", "draw(반)", "release(화살 생성)", "follow", "renock", "draw(반)", "release(화살 생성)", "follow",
           "end", "end"],
    loopFrames=[2, 3, 4, 5, 6, 7, 8, 9], releaseFrames=[4, 8], cancel=None,
    startsFrom="bow_carry_idle / bow_carry_walk(좌클릭 홀드 시작)",
    endsWith="bow_draw_hold f0 근처 → bow_carry_idle",
    phases={"start": [0, 1], "loop": [2, 3, 4, 5, 6, 7, 8, 9], "end": [10, 11]},
)


def render_bow(m):
    out = {}
    for d in DIRS:
        lst = []
        for i, raw in enumerate(m["keys"]):
            k = Q.norm(raw)
            p = Q.body_pose(d, k, i)
            Rg = hero.draw_rig(d, p)
            im, tip = BW.gear_frame(d, "bow_aim", k, Rg)
            spawn = None
            if k["state"] == "release" and k["tension"] > 0.5:
                h = hero.to_px(Rg.anchors["handL"])
                spawn = [round(h[0], 1), round(h[1], 1)]
            lst.append(dict(body=Rg.image, rig=Rg, weapon=im, tip=None if tip is None else hero.to_px(tip), key=k, spawn=spawn))
        out[d] = lst
    return out


# =============================================================================
# 검사 · 내보내기
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
    return dict(weaponColors=len(wc), bodyColors=len(bc))


def export(name, fr, ms, meta, weapon, grip, design, extra):
    bname = "player_" + name
    bim = EX.sheet({d: [f["body"] for f in fr[d]] for d in DIRS}, hero.FW, hero.FH)
    bim.save(os.path.join(EX.OUT_P, bname + ".png"))
    hands = {d: [{k: [round(c, 1) for c in hero.to_px(f["rig"].anchors[k])] for k in ("handR", "handL")} for f in fr[d]] for d in DIRS}
    scars = EX.scar_list({d: [type("F", (), {"rig": f["rig"]}) for f in fr[d]] for d in DIRS})
    data = EX.base(bname + ".png", name, hero.FW, hero.FH, ms, False, hero.PIV, emissiveColors=EX.EMISSIVE, **meta,
                   handAnchors=hands,
                   anchorNote="handAnchors = 프레임별 손 중심(몸 시트 도트, 해부 기준 R 오른손 · L 왼손). 무기 시트 좌표 = 몸 + (48,48)",
                   scarAnchor=scars, scarAnchorNote=EX.SCAR_NOTE, weaponOverlayV3="weapons/v3/" + name,
                   note="57라운드 갈래 1단 몸. weapons/v3/%s 를 같은 프레임 번호·같은 시각에 겹친다. " % name + EX.BODY_NOTE)
    data["source"] = SRC
    data["version"] = VERSION
    EX.write_json(os.path.join(EX.OUT_P, bname + ".json"), data)
    ex = dict(extra, bodySheet=bname, source=SRC,
              overlay="%s 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 = 주인공 피벗 + playerFrameOffset." % bname)
    wv3.write_overlay(name, {d: [f["weapon"] for f in fr[d]] for d in DIRS}, ms, False, name, weapon, hands, grip, design,
                      extra=ex, body_meta=data)
    wj = os.path.join(EX.OUT_W, name + ".json")
    j = json.load(open(wj, encoding="utf-8"))
    j["version"] = VERSION
    EX.write_json(wj, j)
    return data


def build_dagger():
    m = FAN_THROW
    fr = render_dagger(m)
    st = check("dagger_fan_throw", fr)
    s = starts(m["ms"])
    rel = m["releaseFrame"]
    off = (K.OFF, K.OFF)
    spawnL = {d: [None] * len(m["ms"]) for d in DIRS}
    for d in DIRS:
        h = hero.to_px(fr[d][rel]["rig"].anchors["handL"])
        spawnL[d][rel] = wv3.to_w(h, off)
    meta = dict(weapon="dagger", label=m["label"], branch="질풍(疾風) 1단 B", branchNameNote="갈래 이름은 임시(스토리 파트 확정 전)",
                r57="57라운드 Q22~Q37 갈래 1단 수단(설계안 2.4) — 부채꼴 투척, 입력 = 대쉬 공격 교체",
                input="대쉬 직후 0.3초 안 좌클릭(대쉬 공격 교체) — 질풍 1단을 고른 런에서만",
                timingMs=dict(total=sum(m["ms"]), releaseAt=s[rel], cancelAt=s[m["cancel"]]), frameRoles=m["roles"],
                frameStates=[f["state"] for f in fr[DIRS[0]]], fanFrames=[f["fan"] for f in fr[DIRS[0]]],
                framesBasis="player_dagger_fan_throw 프레임 번호(몸·무기·이펙트 공통 기준 = 몸 시트)",
                msNote="ms 는 아트 임시 제안 — 시스템이 바꿔도 releaseFrame 시작 = 투사체 생성이면 그림이 맞는다",
                phases=m["phases"], startsFrom=m["startsFrom"], endsWith=m["endsWith"], cancelFromFrame=m["cancel"],
                releaseFrame=rel, projectileCount=3, fanDeg=list(FAN_DEG), fanSpreadDeg=30,
                releaseNote="releaseFrame(f2) 시작에 투사체 3개 생성(fx/v3/dagger_thrown) — 위치 = 무기 JSON throwSpawnAnchors, "
                            "각도 = 조준각 + fanDeg(−15°·0°·+15°). 사거리 6칸·개당 ×0.6·적중 시 낙인 1(설계안 2.4 — 시스템 데이터)",
                projectile="fx/v3/dagger_thrown", fxSheet="fx/v3/dagger_fan_throw")
    extra = dict(bladeTipAnchors={d: [wv3.to_w(f["tip"], off) for f in fr[d]] for d in DIRS},
                 bladeTipNote="오른손 역수 단검 끝(무기 시트 좌표, 56 Q4 1.3배 그림)",
                 throwSpawnAnchors=spawnL, throwSpawnNote="투사체 생성 점(무기 시트 좌표 = 왼손, releaseFrame 만 값). 몸 좌표 = − (48,48)",
                 fangNote="gather(f0)·wind(f1) 칸은 왼손 손가락 사이에 작은 재 송곳니 3자루(0.55·0.72배)가 맺힌 그림 — 투척 뒤 칸에는 없음",
                 includesSheath=False, reverseGrip=True, carryHidden="이 시트 동안 dagger_carry_* 는 숨긴다(이 시트가 손의 단검을 그림).",
                 stateNote="steel 평소 · fade(송곳니가 맺히는 중)")
    export("dagger_fan_throw", fr, m["ms"], meta, "dagger", "handR", DG.DESIGN, extra)
    return fr, st


def build_bow():
    m = RAPID
    fr = render_bow(m)
    st = check("bow_rapid_loop", fr)
    s = starts(m["ms"])
    lf = m["loopFrames"]
    off = (K.OFF, K.OFF)
    meta = dict(weapon="bow", label=m["label"], branch="속사(速射) 1단 A", branchNameNote="갈래 이름은 53라운드 이름 유지(57 Q22~Q37)",
                r57="57라운드 Q22~Q37 갈래 1단 수단(설계안 2.5) — 속사 연사, 좌클릭 홀드",
                input="좌클릭 홀드 — 속사 1단을 고른 런에서 좌클릭 충전형 대신(누르는 동안 연사, 떼면 끝)",
                timingMs=dict(total=sum(m["ms"]), releasesAt=[s[i] for i in m["releaseFrames"]], loopStartAt=s[lf[0]],
                              loopMs=sum(m["ms"][i] for i in lf), endMs=sum(m["ms"][lf[-1] + 1:])),
                frameRoles=m["roles"], frameStates=[f["key"]["state"] for f in fr[DIRS[0]]],
                framesBasis="player_bow_rapid_loop 프레임 번호(몸·무기 공통)",
                msNote="루프 400ms 에 2발 = 초당 5발(설계안 2.5). 연사 속도를 바꾸면 루프 ms 를 같은 비율로 늘이거나 줄인다",
                phases=m["phases"], startsFrom=m["startsFrom"], endsWith=m["endsWith"],
                loopFrames=lf, loopRange=[lf[0], lf[-1]], startFrames=[0, 1], endFrames=[10, 11], releaseFrames=m["releaseFrames"],
                loopNote="좌클릭 홀드: f0~f1 1회 → 누르는 동안 loopFrames(f2~f9) 반복(f9 → f2) → 떼면 지금 발의 follow 까지 마치고 f10~f11. 시트 loop 값은 false",
                releaseNote="화살 생성 = releaseFrames(f4·f8) 시작, 위치 = 무기 JSON arrowSpawnAnchors. 화살 그림 = fx/v3/bow_arrow_rapid(기존), 입구 섬광 bow_muzzle_rapid(기존). "
                            "탄창이 비면 이 시트 대신 bow_reload(시스템). 연사 중 이동 ×0.5·숨 회복 없음(설계안 2.5 — 시스템 데이터)",
                arrowSheet="fx/v3/bow_arrow_rapid", muzzleFx="fx/v3/bow_muzzle_rapid", drawProgressByFrame=[round(f["key"]["tension"], 2) for f in fr[DIRS[0]]])
    spawn = {d: [None if f["spawn"] is None else wv3.to_w(f["spawn"], off) for f in fr[d]] for d in DIRS}
    extra = dict(bladeTipAnchors={d: [None if f["tip"] is None else wv3.to_w(f["tip"], off) for f in fr[d]] for d in DIRS},
                 bladeTipNote="화살촉 끝(무기 시트 좌표). null = 화살 없음",
                 arrowSpawnAnchors=spawn, arrowSpawnNote="화살 생성 점(무기 시트 좌표) — releaseFrames 의 줌통(왼손). bow_muzzle_rapid 의 pivot",
                 carryHidden="이 시트 동안 bow_carry_* 는 숨긴다(이 시트가 손의 활·화살을 그림).",
                 stateNote="draw 반 당김(시위 A21→A23) · renock 시위 위 재가 맺히는 새 화살 · release 놓는 순간(시위 A26 번쩍 — releaseFrames 만) · follow")
    export("bow_rapid_loop", fr, m["ms"], meta, "bow", "handL", BW.DESIGN, extra)
    return fr, st


def build():
    EX.ensure_dirs()
    a = build_dagger()
    b = build_bow()
    st = {"dagger_fan_throw": a[1], "bow_rapid_loop": b[1]}
    print(st)
    with open(os.path.join(HERE, "stats_body.json"), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)
    return {"dagger_fan_throw": a[0], "bow_rapid_loop": b[0]}


if __name__ == "__main__":
    build()
