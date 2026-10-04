#!/usr/bin/env python3
"""56라운드 작업 A 빌드 — 붓획 연격 이펙트(Q11) · 칼 템포(Q1) · 칼 3타 일섬(Q2) · 그림자 분신(Q3). 결정적, Gemini 미사용.

산출(게임이 읽음):
  몸·무기(칼만): player/v3/player_katana_{rise,fall,issen} · weapons/v3/katana_{rise,fall,issen}
  fx/v3 붓획(이름 유지, 55 시트를 덮어씀 — 판정 필드 유지):
      katana_rise · katana_fall · greatsword_sweep_cw · greatsword_sweep_ccw · greatsword_cleave · greatsword_charge_slam_lv1~3 ·
      dagger_combo1~3
  fx/v3 신규: katana_issen_line_t1~t4(+ _solo: 분신 없음) · katana_issen_shadow
  대검 fx 는 8행(작업 B 몸 행 순서 down, up, left, right, down-right, down-left, up-right, up-left)
  건드리지 않음: 대검 몸·무기, 활·단검 무기(작업 B), 갈래 시트, katana_crescent(_echo)(일섬으로 대체 — 파일은 남김)
이전(55) 시트 사본: prev55/ (비교 미리보기용)
사용: python3 parts/art/work/combo56_fx/build.py [body] [fx] [shadow] [preview] [<시트 이름>...]   (인자 없으면 전부)
"""
import json
import os
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
OUT_FX = os.path.join(ROOT, "assets/sprites/fx/v3")
P3 = os.path.join(ROOT, "assets/sprites/player/v3")
PREV = os.path.join(HERE, "prev55", "fx")

RK = 152.0                       # 칼 R 38 월드 px × 4 (Q1 ×1.15)
RG = 204.0                       # 대검 R 51 월드 px × 4
EFFECT_RULE = ("56라운드 Q11: 채운 초승달 면 대신 붓으로 그은 한 획 — 시작 가늘고 · 가운데 굵고 · 끝은 붓털이 갈라지며 흩어짐(먹 튐). "
               "판정 호를 따라 2~3프레임에 그어 나가고, 시작 쪽부터 말라 재로 부서짐. 재·호박만, 백열은 판정 프레임의 획 머리 몇 도트만(흰 막대 없음)")


def body_json(name):
    return json.load(open(os.path.join(P3, "player_%s.json" % name), encoding="utf-8"))


# =============================================================================
# 시트 정의
# =============================================================================
def _gs(name, **kw):
    return dict(base=name, weapon="greatsword", **kw)


FX = {
    # 칼 1·2타 — 가늘고 긴 붓획(R 152)
    "katana_rise": dict(kind="arc", style="katana", weapon="katana", move="katana_rise", R=RK, arc=(70, -40), wmax=9, z=(5, 37),
                        ms=[30, 25, 30, 60, 70, 80], impact=1, glow=[1, 2], seed=21,
                        design="1타 대각 올려베기 — 오른쪽 아래에서 왼쪽 위로 가늘고 길게 그은 붓 한 획(위로 기울어 올라감), 끝은 붓털이 갈라져 흩어짐"),
    "katana_fall": dict(kind="arc", style="katana", weapon="katana", move="katana_fall", R=RK, arc=(-70, 40), wmax=9, z=(41, 2),
                        ms=[50, 25, 30, 60, 70, 80], impact=1, glow=[1, 2], seed=22,
                        design="2타 대각 내려베기 — 왼쪽 위에서 오른쪽 아래로 그은 붓 한 획(1타와 X 교차)"),
    # 대검 — 굵은 흙·녹 붓획(R 204)
    "greatsword_sweep_cw": _gs("greatsword_sweep_cw", kind="arc", style="gs", move="greatsword_sweep_cw", R=RG, arc=(-75, 75), wmax=24,
                               z=(8, 8), ms=[40, 45, 45, 40, 40, 40], impact=1, glow=[1, 2], seed=31,
                               design="H1 수평 시계 — 굵은 흙·녹 붓 한 획, 가운데 호박 결, 끝은 마른 붓털로 갈라지며 흙먼지처럼 흩어짐"),
    "greatsword_sweep_ccw": _gs("greatsword_sweep_ccw", kind="arc", style="gs", move="greatsword_sweep_ccw", R=RG, arc=(75, -75), wmax=24,
                                z=(8, 8), ms=[40, 45, 45, 40, 40, 40], impact=1, glow=[1, 2], seed=32,
                                design="H2 수평 반시계 — H1 과 같은 붓, 반대 방향"),
    "greatsword_cleave": _gs("greatsword_cleave", kind="vertical", move="greatsword_cleave", L=round(RG * 1.3, 1), Rv=150, wmax=18,
                             heavy=1.0, ms=[40] * 6, impact=2, glow=[2], seed=41,
                             design="V 정면 내려찍기 — 머리 위에서 앞 지면으로 내리그은 세로 붓획 → 땅에 닿은 자리에서 쐐기 끝까지 짧게 끌린 붓획 + 바닥 금"),
    "greatsword_charge_slam_lv1": _gs("greatsword_charge_slam_lv1", kind="vertical", move="greatsword_charge_slam", L=round(RG * 1.3, 1),
                                      Rv=155, wmax=18, heavy=1.1, ms=[40, 40, 40, 40, 40, 50], impact=2, glow=[2], seed=51, stage=1,
                                      design="차지 1단 내려찍기 — 세로 붓획 + 지면 붓획(쐐기 ×1.3)"),
    "greatsword_charge_slam_lv2": _gs("greatsword_charge_slam_lv2", kind="vertical", move="greatsword_charge_slam", L=round(RG * 1.5, 1),
                                      Rv=165, wmax=21, heavy=1.3, ms=[40, 40, 40, 40, 50, 60], impact=2, glow=[2], seed=52, stage=2,
                                      design="차지 2단 내려찍기 — 더 굵은 붓(쐐기 ×1.5)"),
    "greatsword_charge_slam_lv3": _gs("greatsword_charge_slam_lv3", kind="vertical", move="greatsword_charge_slam", L=round(RG * 1.8, 1),
                                      Rv=178, wmax=25, heavy=1.6, ms=[40, 40, 40, 50, 60, 70], impact=2, glow=[2], seed=53, stage=3,
                                      design="차지 3단 내려찍기 — 가장 굵은 붓·금·불티(쐐기 ×1.8)"),
    # 단검 — 짧게 튕긴 찌르기 붓획(Q4 수평 사거리 ×1.5)
    "dagger_combo1": dict(kind="thrust", weapon="dagger", ang=-8, x0=16, length=144, wmax=7, bend=-6, seed=301,
                          design="단검 1타 — 앞으로 짧게 튕겨 낸 붓 한 획(살짝 위로 휨), 끝은 붓털이 갈라짐 · Q4 수평 사거리 ×1.5"),
    "dagger_combo2": dict(kind="thrust", weapon="dagger", ang=10, x0=16, length=144, wmax=7, bend=6, seed=302,
                          design="단검 2타 — 살짝 아래로 휜 짧은 붓 한 획 · Q4 ×1.5"),
    "dagger_combo3": dict(kind="thrust", weapon="dagger", ang=0, x0=16, length=168, wmax=8.5, bend=-4, seed=303,
                          design="단검 3타 — 정면으로 길게 뻗은 붓 한 획(가장 굵음) · Q4 ×1.5"),
}
for n in (1, 2, 3, 4):
    FX["katana_issen_line_t%d" % n] = dict(kind="issen", weapon="katana", tiles=n, seed=80 + n, shadow=True)
for n in (1, 2, 3, 4):
    FX["katana_issen_line_t%d_solo" % n] = dict(kind="issen", weapon="katana", tiles=n, seed=80 + n, shadow=False)
FX_ORDER = list(FX)


# =============================================================================
# 그리기 작업(프로세스 풀)
# =============================================================================
def fx_job(name):
    import fx56 as F
    sp = FX[name]
    t0 = time.time()
    dirs = F.DIRS8 if sp["weapon"] == "greatsword" else F.DIRS4
    frames = {}
    for d in dirs:
        if sp["kind"] == "arc":
            frames[d] = F.arc_frames(sp["style"], d, sp["R"], sp["arc"][0], sp["arc"][1], sp["wmax"], sp["z"], seed=sp["seed"])
        elif sp["kind"] == "vertical":
            frames[d] = F.vertical_frames(d, sp["L"], wmax=sp["wmax"], heavy=sp["heavy"], seed=sp["seed"], Rv=sp["Rv"])
        elif sp["kind"] == "thrust":
            pj = json.load(open(os.path.join(PREV, name + ".json"), encoding="utf-8"))
            frames[d] = F.thrust_frames(d, sp["ang"], sp["x0"], sp["length"] + 6, sp["wmax"], sp["bend"], pj["frames"], pj["impactFrame"],
                                        sp["seed"])
        elif sp["kind"] == "issen":
            frames[d] = F.issen_line_frames(d, sp["tiles"] * 64.0, seed=sp["seed"], shadow=sp["shadow"])
    cut, pivot, origin = F.X.fit(frames, include_pivot=True)
    base, upd, ms, glow = meta(name, sp, pivot, origin)
    sheet, j, _ = F.write(name, cut, dirs, ms, base, upd, glow, OUT_FX)
    return name, j["frameWidth"], j["frameHeight"], j["colors"], round(time.time() - t0, 1)


def meta(name, sp, pivot, origin):
    """→ (기존 JSON 바탕, 덮어쓸 필드, ms, glow)."""
    import fx56 as F
    common = dict(anchor="player_pivot", pivot={"x": pivot[0], "y": pivot[1]}, hitOriginInFrame={"x": origin[0], "y": origin[1]},
                  pivotNote="pivot = 주인공 발(몸 피벗)에 맞춘다. 판정 원점 = pivot 위 40 도트(hitOriginInFrame)",
                  effectRule=EFFECT_RULE, brushStroke=True, r56="56라운드 Q11 붓획")
    if sp["kind"] in ("arc", "vertical"):
        src = sp.get("base", name)
        base = json.load(open(os.path.join(PREV, src + ".json"), encoding="utf-8"))
        upd = dict(common, design=sp["design"], previous="prev55: 55라운드 부분 초승달(같은 이름) — parts/art/work/combo56_fx/prev55/fx/%s.png" % src)
        if sp["weapon"] == "katana":                         # Q1 새 템포 — 몸 JSON 에서 판정 시각·모양
            bj = body_json(sp["move"])
            hit = bj["timingMs"]["hitAt"]
            spawn = hit - sp["ms"][0]
            st = [sum(bj["frameDurationsMs"][:i]) for i in range(bj["frames"])]
            upd.update(spawn="body_ms", spawnAtMs=spawn, impactAtBodyMs=hit, hitShape=bj["hitShape"],
                       spawnBodyFrame=st.index(spawn) if spawn in st else None,
                       drawnArc=dict(fromDeg=sp["arc"][0], toDeg=sp["arc"][1], radiusDots=sp["R"], brushWidthDots=sp["wmax"],
                                     heightDots=list(sp["z"]), note="붓획 바깥 가장자리 ≈ 판정 반경(R 152 = 38 월드 px, Q1 ×1.15)"),
                       timingNote="spawnAtMs = 몸 시트(56 템포) 시작 기준. impactFrame 시작 = 몸 hitAt. 소멸 프레임은 잔심(정지 포즈) 동안 남는다")
            if upd["spawnBodyFrame"] is None:
                upd.pop("spawnBodyFrame")
        else:
            bj = body_json(sp["move"])                       # 작업 B 가 대검 몸 타이밍을 바꿈(Q5) — 현재 몸 JSON hitAt 에 맞춘다
            hit = bj["timingMs"]["hitAt"]
            spawn = hit - sum(sp["ms"][:sp["impact"]])
            st = [sum(bj["frameDurationsMs"][:i]) for i in range(bj["frames"])]
            upd.update(spawn="body_ms", spawnAtMs=spawn, impactAtBodyMs=hit, bodyTimingSource="player_%s %s" % (sp["move"], bj.get("version", "")),
                       spawnBodyFrame=st.index(spawn) if spawn in st else None)
            if upd["spawnBodyFrame"] is None:
                upd.pop("spawnBodyFrame")
                base.pop("spawnBodyFrame", None)
            if "hitShape" in bj and "stage" not in sp:
                upd["hitShape"] = bj["hitShape"]
            upd["drawnArc"] = (dict(fromDeg=sp["arc"][0], toDeg=sp["arc"][1], radiusDots=sp["R"], brushWidthDots=sp["wmax"],
                                    heightDots=list(sp["z"]), note="붓획 바깥 가장자리 ≈ 판정 반경")
                               if sp["kind"] == "arc" else
                               dict(wedgeLengthDots=sp["L"], verticalRadiusDots=sp["Rv"], brushWidthDots=sp["wmax"],
                                    note="세로 붓획(머리 위 → 앞 지면 Rv) + 지면 붓획 Rv → 쐐기 끝(L) + 바닥 금"))
        upd["spawnRule"] = "spawnAtMs = 몸 hitAt − sum(frameDurationsMs[:impactFrame]) (빌드 때 현재 몸 JSON 으로 계산). 몸 타이밍이 바뀌면 이 규칙으로 다시 계산하면 그림이 맞는다"
        upd["frameRoles"] = (["pre(붓 끝 닿음)", "draw(머리 55%)", "draw(끝까지 · 붓털 갈라짐)", "decay(시작부터 마름)", "decay", "decay(재)"]
                             if sp["kind"] == "arc" else
                             ["pre", "draw(내려옴)", "impact(지면 붓획 · 판정)", "decay", "decay", "decay"])
        if sp["weapon"] == "greatsword":
            upd.update(directions=F.DIRS8, dirTransform="drawn8",
                       dirTransformNote="56라운드 Q6 · 작업 B 대검 8방향 — 8행을 직접 그림(행 순서 = 몸·무기 시트: down, up, left, right, down-right, down-left, "
                                        "up-right, up-left). 대각 행 = 조준 방향 45°(화면각 down-right 45° · down-left 135° · up-right -45° · up-left -135°)로 "
                                        "§17 각도를 회전해 다시 그린 것(이미지 회전 아님). 시스템은 몸 시트와 같은 행을 고르면 된다")
        return base, upd, sp["ms"], sp["glow"]
    if sp["kind"] == "thrust":
        base = json.load(open(os.path.join(PREV, name + ".json"), encoding="utf-8"))
        th = dict(base["thrust"])
        prev_len = th["lengthPx"]
        th["lengthPx"] = sp["length"]
        upd = dict(common, design=sp["design"], thrust=th,
                   thrustNote="몸 중심에서 정면(right 기준 angleDeg)으로 fromPx~lengthPx, 폭 widthPx 의 직사각 판정. 56라운드 Q4: 수평 사거리 ×1.5(%d → %d 도트)" % (prev_len, sp["length"]),
                   hitNote="56라운드 Q4 — 판정 길이 ×1.5 참고값(시스템 데이터 기준). 붓획 끝 = lengthPx", previousThrust=base["thrust"],
                   previous="prev55: 재 송곳니 바늘 찌르기 — parts/art/work/combo56_fx/prev55/fx/%s.png" % name,
                   pivotNote="pivot = 발. 찌르기 원점 = pivot 위 40 도트(hitOriginInFrame)")
        upd.pop("hitOrigin", None)
        return base, upd, base["frameDurationsMs"], base.get("glowFrames", [base["impactFrame"]])
    # 일섬 선
    import k56
    n = sp["tiles"]
    bj = body_json("katana_issen")
    dash0 = bj["dash"]["startMs"]
    upd = dict(common, weapon="katana", anchor="dash_start_pivot",
               anchorNote="일섬 돌진을 시작한 순간의 주인공 발 위치(월드)에 고정 — 주인공을 따라가지 않는다. 행 = 돌진 방향",
               depth="below_player", depthNote="바닥 바로 위 · 주인공·적·그림자 분신 아래(선이 몸을 꿰뚫어 보이지 않게). 조명 위(fx 규칙)는 유지",
               pivotNote="pivot = 돌진 출발 발 위치. 선은 판정 원점 높이(pivot 위 40 도트)에서 돌진 방향으로 그어짐",
               design="일섬 선(%d칸) — 돌진하는 칼 바로 뒤로 그어지는 가는 일자 붓획 → 남음 → 그림자 분신이 지나며 다시 달아오름 → 비스듬한 교차 베기 자국과 함께 터짐 → 재" % n,
               bodySheet="player_katana_issen", tiles=n, travelPx={"world": 16 * n, "dots": 64 * n},
               pickRule="실제 이동 칸 수(벽에 막히면 줄어듦)를 내림해 t1~t4 중 고른다(4칸 = t4, 1칸 미만 = t1)",
               spawn="body_ms", spawnAtMs=dash0, spawnNote="katana_issen 돌진 시작(dash.startMs) — 출발 피벗에 1회",
               impactFrame=1, glowFrames=F.ISSEN_GLOW,
               shadowSheet="katana_issen_shadow", shadowStartAtLineMs=F.ISSEN_SHADOW_AT,
               burstFrame=F.ISSEN_BURST_FRAME, burstAtLineMs=sum(F.ISSEN_MS[:F.ISSEN_BURST_FRAME]),
               frameRoles=["돌진 0~30ms 그어짐", "돌진 판정(백열 머리)", "돌진 판정(백열 머리)", "도착 — 선 완성", "남은 가는 선",
                           "분신 지나감 1/3", "분신 2/3", "분신 3/3", "터짐(분신 판정 — 교차 획 머리 백열)", "재로 부서짐", "재", "재"],
               timingNote="선 시트 시각 0 = 돌진 시작. 돌진 150ms 동안 f0~f3 이 칼(주인공) 바로 뒤를 따라 그어진다(head = 이동 진행 + 칼끝 26 도트). "
                          "f5~f7 = 분신(+200ms 출발, 150ms 이동)이 지나간 부분만 다시 밝아짐, f8 = 분신 도착 순간 터짐")
    if not sp["shadow"]:
        upd.update(design="일섬 선(%d칸, 분신 없음) — 그어짐 → 남은 가는 선이 식으며 떨림 → 터짐 → 재. 검기 3단이 아닐 때(56라운드 Q14)" % n,
                   shadowSheet=None, withShadow="katana_issen_line_t%d" % n, glowFrames=[1, 2],
                   burstNote="분신이 없으면 터짐은 연출만(판정 없음 가정) — 백열 없이 A25 이하. 터짐에도 판정이 있으면 알려 주면 glowFrames 에 8 추가",
                   frameRoles=upd["frameRoles"][:5] + ["남은 선(식음)", "남은 선(떨림)", "남은 선(식음)"] + ["터짐(A25 이하)"] + upd["frameRoles"][9:])
        upd.pop("shadowStartAtLineMs", None)
        return None, upd, F.ISSEN_MS, [1, 2]
    upd["soloVariant"] = "katana_issen_line_t%d_solo" % n
    upd["variantNote"] = "56라운드 Q14: 그림자 분신은 검기 3단일 때만 — 분신이 따라오면 이 시트, 아니면 _solo 시트"
    return None, upd, F.ISSEN_MS, F.ISSEN_GLOW


# =============================================================================
# 그림자 분신 (Q3)
# =============================================================================
def build_shadow():
    import shadow56
    return shadow56.build()


def build_fx(only=None):
    names = [n for n in FX_ORDER if not only or n in only]
    with Pool(4) as p:
        res = p.map(fx_job, names, chunksize=1)
    stats_p = os.path.join(HERE, "stats.json")
    stats = json.load(open(stats_p, encoding="utf-8")) if os.path.exists(stats_p) else {}
    for name, fw, fh, cols, sec in res:
        print("%-34s %4dx%-4d colors %2d  %.1fs" % (name, fw, fh, cols, sec))
        stats[name] = dict(frame=[fw, fh], colors=cols)
    with open(stats_p, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(stats.items())), f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    args = set(sys.argv[1:])
    t0 = time.time()
    if not args or "body" in args:
        import bodies56
        bodies56.build()
    only = {a for a in args if a in FX}
    if not args or "fx" in args or only:
        build_fx(only or None)
    if not args or "shadow" in args:
        build_shadow()
    if not args or "preview" in args:
        import preview56
        preview56.main()
    print("done", round(time.time() - t0, 1), "s")
