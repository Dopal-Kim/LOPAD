#!/usr/bin/env python3
"""55라운드 새 연격 빌드 (Q18~Q25 · 계약 §17) — 칼 K-A 발도 초승달 · 대검 G-C 관성 순환. 결정적, Gemini 미사용.

산출(게임이 읽음):
  assets/sprites/player/v3/player_<동작>.png/.json      몸 96×144 · 피벗 (48,138) · pixelScale 0.5
  assets/sprites/weapons/v3/<동작>.png/.json            무기 오버레이(칼 192 틀 · 대검 새 합집합 틀)
  assets/sprites/fx/v3/<이펙트>.png/.json                부분 초승달·세로 호·끝점 충격·충격파 링·차지 번쩍임
  동작 = katana_rise · katana_fall · katana_crescent · greatsword_sweep_cw · greatsword_cleave · greatsword_sweep_ccw ·
         greatsword_charge · greatsword_charge_slam
기존 시트(연격 combo1~3·갈래 *_combo<n>_<branch>)는 건드리지 않는다(새 이름).
사용: python3 parts/art/work/combo55/build.py [body] [fx] [preview]   (인자 없으면 전부) — 미리보기는 preview55.py
"""
import json
import os
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import moves as M  # noqa: E402

STATE = os.path.join(HERE, "state.json")             # 몸 빌드가 남기는 값(대검 틀·차지 칼 위치) — fx 빌드가 읽음


# =============================================================================
# 몸 + 무기
# =============================================================================
def build_bodies():
    import bodies as B
    from wv3 import DIRS, colors_of, has_alpha_partial, hero
    import wv3
    pal = wv3.hero_palette()
    stats = {}
    out_state = {}
    for name in M.ORDER_K:
        fr = B.render_katana(name)
        data = B.export_move(name, fr, "katana", frame=wv3.STD_FRAME)
        stats[name] = _check(name, fr, pal, colors_of, has_alpha_partial)
        print(name, "ok", data["timingMs"])
    gs = {}
    for name in M.ORDER_G:
        fr, keys = B.render_gs(name)
        gs[name] = fr
        planted = {i for i, k in enumerate(keys) if k["el"] <= -55}      # 내려찍기 박힘 프레임만 칼끝이 바닥 아래(의도)
        for i, k in enumerate(keys):
            z = M.Q.gs_tip_z(k)
            assert i in planted or z >= -0.5, (name, i, round(z, 1))
    frame = B.crop_gs(gs)
    print("greatsword r55 frame", frame)
    for name in M.ORDER_G:
        data = B.export_move(name, gs[name], "greatsword", frame=frame)
        stats[name] = _check(name, gs[name], pal, colors_of, has_alpha_partial)
        print(name, "ok", data["timingMs"])
    # 차지 홀드 자세의 손잡이·칼끝(몸 도트) — 번쩍임 fx 위치
    ch = gs["greatsword_charge"]
    hold = M.GS["greatsword_charge"]["loopFrames"][0]
    out_state["chargeBlade"] = {d: [[round(c, 1) for c in hero.to_px(ch[d][hold]["rig"].anchors["handR"])],
                                    [round(c, 1) for c in ch[d][hold]["tip"]]] for d in DIRS}
    out_state["gsFrame"] = list(frame)
    out_state["weaponStats"] = stats
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(out_state, f, ensure_ascii=False, indent=1)


def _check(name, fr, pal, colors_of, has_alpha_partial):
    from wv3 import DIRS, EX
    wc, bc, partial, edge = set(), set(), False, 0
    for d in DIRS:
        for f in fr[d]:
            wc |= colors_of(f["weapon"])
            bc |= colors_of(f["body"])
            partial |= has_alpha_partial(f["weapon"]) or has_alpha_partial(f["body"])
            edge += EX.edge_pixels(f["weapon"])
    assert not (wc - pal) and not (bc - pal), (name, "색이 주인공 팔레트 밖")
    assert len(wc) <= 16 and not partial and edge == 0, (name, len(wc), partial, edge)
    return dict(weaponColors=len(wc), bodyColors=len(bc), edgePixels=edge)


# =============================================================================
# 이펙트 정의 (시트 이름 → 그리기 · 시점)
# =============================================================================
def PLAN_SWEEP():
    return [("pre", dict(head=0.12)), ("draw", dict(head=0.55, hot=True)), ("draw", dict(tail=0.12, head=1.0, hot=True)),
            ("decay", dict(tail=0.4, k=0.33)), ("decay", dict(tail=0.7, k=0.66)), ("decay", dict(tail=0.9, k=1.0))]


def PLAN_V():
    return [("pre", dict(head=0.15)), ("draw", dict(head=0.6)), ("impact", {}),
            ("decay", dict(k=0.33)), ("decay", dict(k=0.66)), ("decay", dict(k=1.0))]


def PLAN_ECHO():
    return [("ghost", dict(v=0.55)), ("draw", dict(head=0.6, hot=True)), ("draw", dict(tail=0.12, head=1.0, hot=True)),
            ("decay", dict(tail=0.5, k=0.5)), ("decay", dict(tail=0.85, k=1.0))]


RK, RG = M.dots(M.R_KATANA), M.dots(M.R_GS)           # 132 · 204 도트

FX = {
    # 칼 — 부분 초승달(대각은 진행에 따라 높이가 바뀌어 기울어진 호)
    "katana_rise": dict(kind="crescent", move="katana_rise", style="katana", R=RK, arc=(70, -40), wmax=20, z=(4, 32), fill_to=80,
                        ms=[20, 30, 30, 30, 30, 30], impact=1, glow=[1, 2], spawnBodyFrame=2, seed=21,
                        design="대각 올려베기 — 오른쪽 아래에서 왼쪽 위로 달려 나가며(호가 화면 위로 기울어 올라감) 혜성처럼 굵어지는 가는 초승달 + 칼끝 쪽 속도선 4줄"),
    "katana_fall": dict(kind="crescent", move="katana_fall", style="katana", R=RK, arc=(-70, 40), wmax=20, z=(36, 2), fill_to=80,
                        ms=[20, 30, 30, 30, 30, 30], impact=1, glow=[1, 2], spawnBodyFrame=1, seed=22,
                        design="대각 내려베기 — 왼쪽 위에서 오른쪽 아래로(1타 궤적과 화면에서 X 로 교차)"),
    "katana_crescent": dict(kind="crescent", move="katana_crescent", style="katana", R=round(RK * 1.25, 1), arc=(-75, 75), wmax=26,
                            z=(14, 14), fill_to=80, ms=[30, 30, 30, 40, 40, 40], impact=1, glow=[1, 2], spawnBodyFrame=3, seed=23,
                            design="수평 발도 150° 초승달 ×1.25 — 칼집에서 뽑으며 수평으로 그어 나감, 마무리라 가장 굵고 김"),
    "katana_crescent_echo": dict(kind="crescent", move="katana_crescent", style="echo", R=round(RK * 1.25 - 5, 1), arc=(-75, 75), wmax=13,
                                 z=(14, 14), fill_to=None, ms=[30, 30, 30, 40, 40], impact=1, glow=[1, 2], spawnAtMs=320, seed=24,
                                 plan="echo",
                                 design="잔상 베기 — 150ms 뒤 같은 호에 끊긴 재 실선이 먼저 맺히고(f0) 재빛 초승달이 같은 방향으로 다시 그어짐(f1·f2 백열 날선) → 재로 부서짐"),
    # 대검 — 넓은 녹·흙 부분 초승달
    "greatsword_sweep_cw": dict(kind="crescent", move="greatsword_sweep_cw", style="gs", R=RG, arc=(-75, 75), wmax=42, z=(8, 8),
                                fill_to=112, ms=[40, 45, 45, 40, 40, 40], impact=1, glow=[1, 2], spawnBodyFrame=2, seed=31,
                                design="H1 수평 시계 — 녹·흙 넓은 초승달 + 이 빠진 홈 혼불 한 줄 + 칼끝 쪽 속도선, 꼬리부터 재·불씨로 부서짐"),
    "greatsword_sweep_ccw": dict(kind="crescent", move="greatsword_sweep_ccw", style="gs", R=RG, arc=(75, -75), wmax=42, z=(8, 8),
                                 fill_to=112, ms=[40, 45, 45, 40, 40, 40], impact=1, glow=[1, 2], spawnBodyFrame=2, seed=32,
                                 design="H2 수평 반시계 — H1 과 같은 문체, 반대 방향"),
    "greatsword_cleave": dict(kind="vertical", move="greatsword_cleave", L=round(RG * 1.3, 1), Rv=150, wmax=16, heavy=1.0,
                              ms=[40, 40, 40, 40, 40, 40], impact=2, glow=[2], spawnBodyFrame=2, seed=41,
                              design="V 정면 내려찍기 — 머리 위에서 앞 지면으로 세로로 선 가는 호 → 칼이 닿은 자리에서 쐐기 끝점까지 달려 나가는 백열 충격 선 + 쐐기를 따라 갈라지는 바닥 금"),
    "greatsword_cleave_impact": dict(kind="impact", move="greatsword_cleave", radius=round(RG * 0.35, 1), heavy=1.0,
                                     ms=[40, 50, 60, 70, 80], impact=0, glow=[0], seed=42,
                                     design="끝점 충격원 0.35R — 백열 충돌 섬광 + 깨진 고리 → 방사 균열 + 먼지 링 → 가라앉음"),
    "greatsword_charge_slam_lv1": dict(kind="vertical", move="greatsword_charge_slam", L=round(RG * 1.3, 1), Rv=155, wmax=17, heavy=1.1,
                                       ms=[40, 40, 40, 40, 40, 50], impact=2, glow=[2], spawnBodyFrame=1, seed=51, stage=1,
                                       design="차지 1단 내려찍기 — 쐐기 ×1.3"),
    "greatsword_charge_slam_lv2": dict(kind="vertical", move="greatsword_charge_slam", L=round(RG * 1.5, 1), Rv=165, wmax=21, heavy=1.3,
                                       ms=[40, 40, 40, 40, 50, 60], impact=2, glow=[2], spawnBodyFrame=1, seed=52, stage=2,
                                       design="차지 2단 내려찍기 — 쐐기 ×1.5, 더 굵은 호·금"),
    "greatsword_charge_slam_lv3": dict(kind="vertical", move="greatsword_charge_slam", L=round(RG * 1.8, 1), Rv=178, wmax=26, heavy=1.6,
                                       ms=[40, 40, 40, 50, 60, 70], impact=2, glow=[2], spawnBodyFrame=1, seed=53, stage=3,
                                       design="차지 3단 내려찍기 — 쐐기 ×1.8, 가장 굵은 호·금·불티(+ 충격파 링 시트)"),
    "greatsword_charge_ring": dict(kind="ring", move="greatsword_charge_slam", radii=[80, 110, 140, 170, 195, 204],
                                   ms=[40, 40, 50, 50, 60, 60], impact=0, glow=[0, 1], seed=61,
                                   design="3단 충격파 링 — 끝점에서 0.35R → 1.0R 로 퍼지는 백열→호박 고리 + 고리 따라 먼지"),
    "greatsword_charge_flash_lv1": dict(kind="flash", move="greatsword_charge", level=1, ms=[30, 40, 50, 60, 70], seed=71,
                                        design="차지 1단(0.4초) — 칼끝 작은 반짝(A23 까지)"),
    "greatsword_charge_flash_lv2": dict(kind="flash", move="greatsword_charge", level=2, ms=[30, 40, 50, 60, 70], seed=72,
                                        design="차지 2단(0.8초) — 날을 따라 손잡이 → 칼끝으로 흐르는 호박 + 중간 별 + 불티(A25 까지)"),
    "greatsword_charge_flash_lv3": dict(kind="flash", move="greatsword_charge", level=3, ms=[30, 40, 50, 60, 70], seed=73,
                                        design="차지 3단(1.2초) — 큰 별(대각 빛살) + 퍼지는 고리 + 불티 다발(A25 까지, 백열 없음 — Q65)"),
}
FX_ORDER = list(FX)


def fx_job(name):
    import fx55 as X
    sp = FX[name]
    st = json.load(open(STATE, encoding="utf-8"))
    t0 = time.time()
    dirs = X.DIRS if sp["kind"] in ("crescent", "vertical", "flash") else ["any"]
    frames = {}
    for d in dirs:
        if sp["kind"] == "crescent":
            z0, z1 = sp["z"]
            plan = PLAN_ECHO() if sp.get("plan") == "echo" else PLAN_SWEEP()
            frames[d] = X.crescent_frames(sp["style"], d, sp["R"], sp["arc"][0], sp["arc"][1], plan, sp["wmax"],
                                          lambda s, z0=z0, z1=z1: z0 + (z1 - z0) * s, fill_to=sp["fill_to"], seed=sp["seed"])
        elif sp["kind"] == "vertical":
            frames[d] = X.vertical_frames(d, sp["L"], PLAN_V(), wmax=sp["wmax"], heavy=sp["heavy"], seed=sp["seed"], Rv=sp["Rv"])
        elif sp["kind"] == "impact":
            frames[d] = X.impact_frames(sp["radius"], seed=sp["seed"], heavy=sp["heavy"])
        elif sp["kind"] == "ring":
            frames[d] = X.ring_frames(sp["radii"], seed=sp["seed"])
        else:
            g, tip = st["chargeBlade"][d]
            px = lambda p: (X.CO[0] + p[0] - 48, X.CO[1] + X.HIT_UP + p[1] - 138)   # noqa: E731  몸 도트 → 큰 캔버스
            frames[d] = X.flash_frames(d, (px(g), px(tip)), sp["level"], seed=sp["seed"])
        assert len(frames[d]) == len(sp["ms"]), name
    cut, pivot, origin = X.fit(frames, include_pivot=sp["kind"] in ("crescent", "vertical", "flash"))
    data = fx_meta(name, sp, pivot, origin)
    glow = sp.get("glow")
    if sp["kind"] == "flash":
        glow = []                                       # 판정 아님 — 전 프레임 A25 이하
    sheet, j, _ = X.write(name, cut, dirs, sp["ms"], data, glow)
    return name, j["frameWidth"], j["frameHeight"], j["colors"], round(time.time() - t0, 1)


def fx_meta(name, sp, pivot, origin):
    mv = M.KATANA.get(sp["move"]) or M.GS[sp["move"]]
    tm = M.timing(mv)
    st = M.starts(mv["ms"])
    d = dict(weapon="katana" if name.startswith("katana") else "greatsword", design=sp["design"], bodySheet="player_" + sp["move"],
             weaponSheet="weapons/v3/" + sp["move"], comboSet="K-A 발도 초승달" if name.startswith("katana") else "G-C 관성 순환",
             dirTransform="rotate", dirTransformNote="§17 각도(조준 0°, 화면 시계 +)를 모든 방향에 회전으로 적용 — left = right 를 180° 회전(구 fx 의 좌우 반전 아님). 몸 시트의 휘두름 방향과 같다",
             effectRule="55라운드: 원 전체가 아니라 판정 호를 따라 2~3프레임에 그려 나가는 부분 초승달, 80~120ms 소멸, 재·호박만, 판정 순간만 백열")
    if sp["kind"] in ("crescent", "vertical", "flash"):
        d.update(anchor="player_pivot", pivot={"x": pivot[0], "y": pivot[1]},
                 hitOriginInFrame={"x": origin[0], "y": origin[1]},
                 pivotNote="pivot = 주인공 발(몸 피벗)에 맞춘다. 판정 원점 = pivot 위 40 도트(hitOriginInFrame)")
    else:
        d.update(anchor="hitbox_center", pivot={"x": origin[0], "y": origin[1]}, rotate=False,
                 pivotNote="pivot = 판정 원(충격원·충격파 링) 중심. 방향 무관(any) — 시스템이 끝점(판정 원점 + 조준 방향 × 쐐기 길이)에 놓는다")
    if sp["kind"] in ("crescent", "vertical"):
        if "spawnAtMs" in sp:
            spawn_ms = sp["spawnAtMs"]
            d.update(spawn="body_ms", spawnAtMs=spawn_ms)
        else:
            spawn_ms = st[sp["spawnBodyFrame"]]
            d.update(spawn="body_frame", spawnBodyFrame=sp["spawnBodyFrame"], spawnAtMs=spawn_ms)
        imp_ms = spawn_ms + sum(sp["ms"][:sp["impact"]])
        if name == "katana_crescent_echo":
            assert imp_ms == tm["hitAt"] + mv["echo"]["delayMs"], (name, imp_ms)
            d.update(echoOf="katana_crescent", delayMs=mv["echo"]["delayMs"], damageScale=mv["echo"]["damage"],
                     hitShape=dict(_body_hit(sp["move"]), note="본 타격과 같은 호(§17) — 2차 판정, 피해 50%"),
                     impactAtBodyMs=imp_ms)
        else:
            assert imp_ms == tm["hitAt"], (name, imp_ms, tm["hitAt"])
            d["impactAtBodyMs"] = imp_ms
            if not name.startswith("greatsword_charge_slam"):
                d["hitShape"] = _body_hit(sp["move"])
        d.update(impactFrame=sp["impact"],
                 timingNote="spawnAtMs = 몸 시트 시작 기준 이 시트를 띄우는 시각. impactFrame 시작 = 몸 hitAt(판정). 관성 공속은 몸·fx 를 같은 배율로 재생")
    if sp["kind"] == "crescent":
        d.update(drawnArc=dict(fromDeg=sp["arc"][0], toDeg=sp["arc"][1], radiusDots=sp["R"], bandWidthDots=sp["wmax"],
                               innerSpeedLinesToDots=sp["fill_to"], heightDots=list(sp["z"]),
                               note="그림 메모: 바깥 가장자리 = 판정 반경. heightDots = 휘두름 시작→끝 높이(화면 위로 더함, 대각 기울기)"),
                 frameRoles=["pre", "draw(머리 55%)", "draw(끝까지)", "decay", "decay", "decay"][:len(sp["ms"])])
        if sp.get("plan") == "echo":
            d["frameRoles"] = ["ghost(끊긴 재 실선)", "draw(머리 60%)", "draw(끝까지)", "decay", "decay"]
    if sp["kind"] == "vertical":
        d.update(drawnArc=dict(wedgeLengthDots=sp["L"], verticalRadiusDots=sp["Rv"],
                               note="세로 호(머리 위 → 칼이 닿는 앞 지면 Rv) + Rv → 쐐기 끝(L) 충격 선 + 바닥 금"),
                 frameRoles=["pre", "draw(내려옴)", "impact(백열 — 판정)", "decay", "decay", "decay"],
                 impactSheet="greatsword_cleave_impact", impactSheetAt="impactFrame 시작, 쐐기 끝점(hitbox_center)")
        if "stage" in sp:
            d.update(chargeStage=sp["stage"], wedgeLengthR=[1.3, 1.5, 1.8][sp["stage"] - 1],
                     hitShape=dict(_body_hit(sp["move"]), lengthPx=sp["L"], stage=sp["stage"]),
                     impactSheetScale=[1.0, 1.15, 1.3][sp["stage"] - 1],
                     impactSheetScaleNote="끝점 충격 시트 scale 참고값(충격원 반경도 키울지는 시스템 데이터)")
            if sp["stage"] == 3:
                d["ringSheet"] = "greatsword_charge_ring"
        else:
            d.update(inertiaMaxImpactScale=1.3, inertiaNote="§17 관성 최대(+20%)일 때 끝점 충격 시트를 scale 1.3 으로(참고값)")
    if sp["kind"] == "impact":
        d.update(spawn="impact", spawnNote="greatsword_cleave·greatsword_charge_slam 의 impactFrame 시작(=hitAt)에 끝점에서 1회",
                 impactFrame=0, impactCircleRadiusPx=sp["radius"], scale="allowed",
                 scaleHints={"inertiaMax": 1.3, "chargeStage": [1.0, 1.15, 1.3]},
                 groundKy=0.85, groundNote="고리·균열은 세로 0.85 로 눌러 바닥에 놓인 느낌(판정 원은 원 — 가로 반지름 = 판정 반지름)",
                 shakeHint={"px": 4, "ms": 90}, frameRoles=["impact 백열 섬광·깨진 고리", "고리 퍼짐·균열", "먼지 링", "가라앉음", "식은 금"])
    if sp["kind"] == "ring":
        d.update(spawn="impact", spawnNote="차지 3단 내려찍기 impactFrame 시작(=hitAt)에 끝점에서 1회", impactFrame=0,
                 ringRadiusPxByFrame=sp["radii"], groundKy=0.85,
                 hitShape=dict(type="ring", centerAt="wedge end (impact circle center)", radiusPxByFrame=sp["radii"],
                               fromR=0.35, toR=1.0, R={"world": M.R_GS, "dots": RG},
                               note="충격파 링 판정 참고값 — 프레임별 반지름(도트), 두께는 시스템 데이터"),
                 shakeHint={"px": 6, "ms": 140})
    if sp["kind"] == "flash":
        lv = sp["level"]
        d.update(spawn="charge_stage_reached", chargeStage=lv, atHoldSec=[0.4, 0.8, 1.2][lv - 1],
                 spawnNote="홀드 시작부터 %.1f초에 1회(차지 몸 greatsword_charge 의 어느 프레임이든 — 홀드 루프 자세의 칼끝 기준 그림)" % [0.4, 0.8, 1.2][lv - 1],
                 glowNote="판정 아님 — 전 프레임 A25 이하(Q65). 단계 차이는 크기·빛살 수·고리·불티로")
    return d


def _body_hit(move):
    import bodies as B
    mv = M.KATANA.get(move) or M.GS[move]
    return B.hit_shape(mv, M.R_KATANA if move.startswith("katana") else M.R_GS)


def build_fx(only=None):
    names = [n for n in FX_ORDER if not only or n in only]
    with Pool(4) as p:
        res = p.map(fx_job, names, chunksize=1)
    stats_p = os.path.join(HERE, "stats.json")
    stats = json.load(open(stats_p, encoding="utf-8")) if os.path.exists(stats_p) else {}
    for name, fw, fh, cols, sec in res:
        print("%-30s %4dx%-4d colors %2d  %.1fs" % (name, fw, fh, cols, sec))
        stats[name] = dict(frame=[fw, fh], colors=cols)
    st = json.load(open(STATE, encoding="utf-8"))
    stats.update(st.get("weaponStats", {}))
    with open(stats_p, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(stats.items())), f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    args = set(sys.argv[1:])
    t0 = time.time()
    if not args or "body" in args:
        build_bodies()
    fx_only = {a for a in args if a in FX}
    if not args or "fx" in args or fx_only:
        build_fx(fx_only or None)
    if not args or "preview" in args:
        import preview55
        preview55.main()
    print("done", round(time.time() - t0, 1), "s")
