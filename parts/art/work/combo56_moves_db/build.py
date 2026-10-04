#!/usr/bin/env python3
"""56라운드 작업 E2 빌드 — 새 기본기 그림 3종(Q40~Q43). 결정적, Gemini 미사용(키아트 sheet_dagger 4·6번, sheet_bow 3번은 참고만).

산출(게임이 읽음, 전부 새 파일 — 기존 시트는 건드리지 않음):
  몸   player/v3/player_{dagger_backstab, dagger_flurry, bow_arrow_rain}
  무기 weapons/v3/{dagger_backstab, dagger_flurry, bow_arrow_rain}          (단검 = 56 Q4 1.3배 그림 · 활 = 활 B)
  fx   fx/v3/dagger_backstab · dagger_flurry · dagger_flurry_heat2 · dagger_flurry_heat3 ·
       bow_arrow_rain_rise · bow_arrow_rain_fall · bow_arrow_rain_mark
사용: python3 parts/art/work/combo56_moves_db/build.py [body] [fx] [preview]   (인자 없으면 전부. fx 는 body 가 쓴 JSON 기준점을 읽음)
각 단계는 별도 프로세스(단검 1.3배 설치가 프로세스 안에서만 모듈을 바꾸므로).
"""
import json
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
MOVES = ["dagger_backstab", "dagger_flurry", "bow_arrow_rain"]


# =============================================================================
# body
# =============================================================================
def build_body():
    import bodies_db as B
    from bodies_db import wv3, DIRS, M
    wv3.EX.ensure_dirs()
    wv3.PV.HERE = os.path.join(HERE, "gif")
    os.makedirs(wv3.PV.HERE, exist_ok=True)
    stats = {}
    for name in MOVES:
        fr = B.render(name)
        stats[name] = B.check(name, fr)
        B.export(name, fr)
        m = M.MOVES[name]
        wv3.previews(name, {d: [f["body"] for f in fr[d]] for d in DIRS}, {d: [f["weapon"] for f in fr[d]] for d in DIRS}, m["ms"],
                     states=[f["state"] for f in fr[DIRS[0]]], active=m.get("active") or m.get("releaseFrames", []), impact=m.get("impact"))
        print(name, stats[name])
    _stats("body", stats)


def _stats(key, val):
    p = os.path.join(HERE, "stats.json")
    st = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    st[key] = val
    with open(p, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1)


# =============================================================================
# fx
# =============================================================================
def build_fx():
    import fx_db as X
    from fx_db import F, W
    out = {}

    # ---- 1. 등 뒤 치명 찌르기
    bj, wj = X.bjson("dagger_backstab"), X.wjson("dagger_backstab")
    frames, crit = {}, {}
    for d in X.DIRS4:
        frames[d], crit[d] = X.backstab_frames(d, bj, wj)
    cut, pivot, origin = F.X.fit(frames, include_pivot=True)
    hit = bj["timingMs"]["hitAt"]
    upd = dict(X.COMMON, weapon="dagger", anchor="player_pivot", pivot={"x": pivot[0], "y": pivot[1]},
               hitOriginInFrame={"x": origin[0], "y": origin[1]}, depth="above", bodySheet="player_dagger_backstab",
               spawn="body_ms", spawnAtMs=hit - X.BS_MS[0], spawnBodyFrame=bj["impactFrame"] - 1, impactFrame=1, impactAtBodyMs=hit,
               hitFrames=[1], activeFrames=[1], thrust=bj["thrust"], hitShape=bj["hitShape"], timingMs=dict(hitAt=X.BS_MS[0], total=sum(X.BS_MS)),
               spawnRule="spawnAtMs = 몸 hitAt − frameDurationsMs[0] (= 몸 drive 프레임 시작). impactFrame 시작 = 몸 hitAt",
               critAnchors={d: {"x": crit[d][0], "y": crit[d][1]} for d in X.DIRS4},
               critAnchorNote="치명 섬광 중심(몸 시트 도트 = 칼날 70% 지점, 박힌 자리). 섬광은 이 시트에 이미 그려져 있음 — 전용 섬광만, "
                              "공용 치명 fx(hit_dagger_heavy·crit_burst)는 겹치지 않음(56라운드 Q55). 몸 피벗 기준 = (x−48, y−138)",
               frameRoles=X.BS_ROLES, holdFrame=1, hitstopHint=dict(ms=90, note="치명 일격 — 히트스톱 동안 holdFrame(백열 코어) 유지 권장(값은 시스템)"),
               shakeHint=dict(px=3, ms=110), flash=dict(color="#eecc78", ms=60, atFrame=1, note="선택: 화면 가장자리 호박 번쩍(시스템 판단)"),
               design="등 뒤 치명 찌르기 — 위에서 내리꽂는 칼끝 경로의 짧고 굵은 붓획(丿, 박히며 끝이 갈라짐) + 박힌 자리 치명 섬광: 세로로 긴 바늘 8갈래(백열은 "
                      "판정 프레임 코어 ~2 도트·바늘 뿌리만) → 호박 광선·점선 고리 → 불티가 튀고 고리가 벌어짐 → 재 조각이 떨어짐",
               designRef="parts/art/work/gemini/weapon_moves/sheet_dagger.png 4번(분위기만, 도트 직접)")
    s, j, _ = F.write("dagger_backstab", cut, X.DIRS4, X.BS_MS, None, upd, [1], X.OUT_FX)
    out["dagger_backstab"] = dict(frame=[j["frameWidth"], j["frameHeight"]], colors=j["colors"])

    # ---- 2. 고속 난타(과열 3단계)
    fb = X.bjson("dagger_flurry")
    for lv in (1, 2, 3):
        hp = X.HEAT[lv]
        frames = {d: X.flurry_frames(d, lv) for d in X.DIRS4}
        cut, pivot, origin = F.X.fit(frames, include_pivot=True)
        upd = dict(X.COMMON, weapon="dagger", anchor="player_pivot", pivot={"x": pivot[0], "y": pivot[1]},
                   hitOriginInFrame={"x": origin[0], "y": origin[1]}, depth="above", bodySheet="player_dagger_flurry",
                   spawn="body_ms", spawnAtMs=0, spawnNote="몸 시트와 같은 10프레임·같은 ms — 몸 f0 시작에 같이 시작하고 몸과 같은 프레임 번호를 같은 시각에 표시",
                   loopFrames=fb["loopFrames"], loopRange=fb["loopRange"], hitFrames=fb["hitFrames"], activeFrames=fb["activeFrames"],
                   impactFrame=fb["impactFrame"], thrust=fb["thrust"], hitShape=fb["hitShape"], timingMs=fb["timingMs"],
                   frameRoles=fb["frameRoles"], stabAngles=fb["stabAngles"],
                   loopNote="몸 loopRange 와 같이 반복. 루프 프레임은 이전 찌르기 획이 나이대로 마르는 모습까지 그려 이음새 없음(f7 → f2). 떼면 몸과 같이 f8~f9",
                   heatLevel=lv, heatLabel=hp["label"],
                   heatVariants={"1": "dagger_flurry", "2": "dagger_flurry_heat2", "3": "dagger_flurry_heat3"},
                   heatRule="임시 제안: 과열 0~39% = dagger_flurry, 40~79% = _heat2, 80~100% = _heat3. 단계가 바뀌면 같은 프레임 번호로 시트만 바꿔 이어 재생"
                            "(세 시트 프레임·ms·피벗 기준 동일). 100% 자동 폭발은 기존 과열 규칙(Q13~Q20)",
                   design="고속 난타 — 앞으로 짧게 튕긴 찌르기 붓획 3갈래(위·아래·가운데)가 엇갈려 남는 칼자국 다발. " + hp["label"],
                   designRef="parts/art/work/gemini/weapon_moves/sheet_dagger.png 6번(분위기만, 도트 직접)")
        if lv > 1:
            upd["heatOf"] = "dagger_flurry"
        name = hp["name"]
        s, j, _ = F.write(name, cut, X.DIRS4, X.FL_MS, None, upd, X.FL_GLOW, X.OUT_FX)
        out[name] = dict(frame=[j["frameWidth"], j["frameHeight"]], colors=j["colors"])

    # ---- 3a. 쏘아 올림
    rb, rw = X.bjson("bow_arrow_rain"), X.wjson("bow_arrow_rain")
    frames, angs = {}, {}
    for d in X.DIRS4:
        vs = []
        for i in (1, 4, 7):                                     # 가득 프레임: 시위 손(R) → 촉
            tip, hr = rw["bladeTipAnchors"][d][i], rw["handAnchors"][d][i]["handR"]
            vs.append(math.atan2(tip[1] - hr[1], tip[0] - hr[0]))
        a = math.atan2(sum(math.sin(v) for v in vs), sum(math.cos(v) for v in vs))
        angs[d] = a
        frames[d] = X.rise_frames(d, a)
    cut, piv = X.fit_at(frames, X.PV)
    upd = dict(X.COMMON, weapon="bow", anchor="arrow_spawn", pivot={"x": piv[0], "y": piv[1]}, depth="above", rotate=False,
               bodySheet="player_bow_arrow_rain",
               spawn="arrow_spawn", spawnAtBodyFrames=rb["releaseFrames"], spawnAtBodyMs=rb["timingMs"]["releasesAt"],
               spawnNote="화살비 몸 releaseFrames 시작마다 1회(3발) — pivot 을 무기 JSON arrowSpawnAnchors[방향][그 프레임](무기 시트 좌표 → 월드)에. 이동은 시트 안에 그려져 있음(시스템은 움직이지 않음)",
               screenAngleDeg={d: round(math.degrees(angs[d]), 1) for d in X.DIRS4},
               screenAngleNote="행별 솟는 화면 각(위 = −90°) — 몸 가득 프레임(1·4·7)의 시위 손 → 촉 방향 평균",
               riseDistancePx=X.RISE_DIST, frameRoles=["떠남(줌통 앞)", "솟음", "솟음(작아짐)", "하늘로 사라짐(꼬리 재)"],
               design="화살비 쏘아 올림 — 재 화살이 불티 꼬리를 끌며 하늘로 솟아 작아지며 사라짐(판정 없음 — 백열 없음)",
               designRef="parts/art/work/gemini/weapon_moves/sheet_bow.png 3번(분위기만)")
    s, j, _ = F.write("bow_arrow_rain_rise", cut, X.DIRS4, X.RISE_MS, None, upd, [], X.OUT_FX)
    out["bow_arrow_rain_rise"] = dict(frame=[j["frameWidth"], j["frameHeight"]], colors=j["colors"])

    # ---- 3b. 낙하
    frames = {"any": X.fall_frames()}
    cut, piv = X.fit_at(frames, X.PV)
    upd = dict(X.COMMON, weapon="bow", anchor="hitbox_center", pivot={"x": piv[0], "y": piv[1]}, depth="above", rotate=False,
               flipX="allowed", impactFrame=X.FALL_IMPACT, hitFrames=[X.FALL_IMPACT],
               timingMs=dict(hitAt=sum(X.FALL_MS[:X.FALL_IMPACT]), total=sum(X.FALL_MS)),
               fallHeightPx=X.FALL_H[0], fallSlantDeg=12,
               pivotNote="pivot = 화살이 꽂히는 바닥 점(예고 원 안의 낙하 지점). 화살은 그 위 fallHeightPx 도트에서 떨어짐(시트 안에 그려짐 — 시스템은 움직이지 않음)",
               spawn="rain", spawnNote="예고 원 rain 단계 시작부터 원 안 무작위 9곳에 40ms 간격으로 1곳씩 재생(화살 3발 연속 발사 640ms, 56라운드 Q52). "
                                       "낙하점마다 작은 판정 — 각 재생의 impactFrame 시작 = 그 점의 판정 순간(Q52). 낙하 화살 12° 고정 + flipX 로 좌우 섞기(Q55)",
               frameRoles=["떨어짐(높이 150)", "떨어짐(100)", "떨어짐(48) · 바닥 그림자 진해짐", "꽂힘(판정 — 촉 자리 백열 몇 도트 · 먼지)", "꽂혀 남음(불티)",
                           "위부터 재로 부서짐", "재"],
               design="화살비 낙하 — 재 화살이 불티 꼬리를 끌며 비스듬히 떨어져 바닥에 꽂히고(작은 먼지·섬광) 위에서부터 재로 부서짐",
               designRef="parts/art/work/gemini/weapon_moves/sheet_bow.png 3번(분위기만)")
    s, j, _ = F.write("bow_arrow_rain_fall", cut, ["any"], X.FALL_MS, None, upd, [X.FALL_IMPACT], X.OUT_FX)
    out["bow_arrow_rain_fall"] = dict(frame=[j["frameWidth"], j["frameHeight"]], colors=j["colors"])

    # ---- 3c. 예고 원
    rows = list(X.MARK_SIZES)
    frames = {r: X.mark_frames(X.MARK_SIZES[r]) for r in rows}
    cut, piv = X.fit_at(frames, X.PV)
    upd = dict(X.COMMON, weapon="bow", anchor="hitbox_center", pivot={"x": piv[0], "y": piv[1]}, depth="below", rotate=False,
               layout="rows = sizes (s, m, l), columns = frames — 행을 크기로 고른다(방향 무관)", sizes=rows, rowBy="size", rowsAre="sizes",
               directionsNote="directions 칸에 크기 키(s·m·l)를 넣었다 — 행 = 크기(greatsword_ground_crack 과 같은 규약)",
               sizeInfo={r: dict(row=i, radiusPx=X.MARK_SIZES[r], radiusWorld=X.MARK_SIZES[r] // 4) for i, r in enumerate(rows)},
               scale="allowed", scaleRule="원 크기 조절: 판정 반경 R(도트)에 가장 가까운 행을 고르고 scale = R / sizeInfo[행].radiusPx (0.85~1.2 안이면 선 굵기가 "
                                         "자연스러움). 테 굵기를 일정하게 두려고 크기별 행을 따로 그렸다",
               pivotNote="pivot = 원 중심 = 커서(낙하 범위 중심). 바닥 깊이(below) — 캐릭터·적 아래, 조명 위(fx 규칙)",
               phases=X.MARK_PHASES, loopFrames=X.MARK_PHASES["wait"], loopRange=[2, 5], frameRoles=X.MARK_ROLES,
               phaseNote="좌클릭(화살비 발동) 때 appear 1회 → 첫 화살이 떨어질 때까지 wait 반복 → 낙하 동안 rain(마지막 프레임 유지 가능) → out 1회",
               progressDriven=False, telegraph=True,
               design="화살비 낙하 지점 예고 원 — 바닥 그을음 테 + 호박 한 줄 테, 안쪽을 가리키는 화살촉 눈금 8개가 천천히 돎, 안쪽 점선·가운데 + 표식. "
                      "쏟아질 때 테가 달아오르고 안쪽 바닥에 그을음 점, 끝나면 테가 점선 재로 끊기며 식음(예고라 백열 없음)",
               designRef="parts/art/work/gemini/weapon_moves/sheet_bow.png 3번(바닥 원 분위기만)")
    s, j, _ = F.write("bow_arrow_rain_mark", cut, rows, X.MARK_MS, None, upd, [], X.OUT_FX)
    out["bow_arrow_rain_mark"] = dict(frame=[j["frameWidth"], j["frameHeight"]], colors=j["colors"])
    for k, v in out.items():
        print("%-26s %s" % (k, v))
    _stats("fx", out)


STEPS = {"body": "import build; build.build_body()", "fx": "import build; build.build_fx()",
         "preview": "import preview_db; preview_db.main()"}


def run(step):
    t0 = time.time()
    subprocess.run([sys.executable, "-c", STEPS[step]], cwd=HERE, check=True)
    print("== %s %.1fs" % (step, time.time() - t0))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a in STEPS] or list(STEPS)
    for s in args:
        run(s)
