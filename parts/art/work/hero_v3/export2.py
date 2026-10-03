"""주인공 v3 2차 시트 내보내기 — assets/sprites/player/v3/player_{greatsword_*,dagger_*,bow_*,attack,birth}.png/.json

구 시트(16×24) JSON 의 메모 필드를 옮기고, 프레임 번호 필드는 새 프레임 번호로 바꾼다(구 프레임 → 그 구간의 새 프레임들).
판정 시점 assert: 구 프레임마다 '시작 ms' 가 같고(= hitAt·cancelAt·hold·release·leap·recover 시작 불변), 전체 ms 가 같다.
"""
import copy
import json
import os

import anim
import birth3 as B
import export as EX
import gear3 as Q
import hero

SRC2 = "parts/art/work/hero_v3/build2.py (53라운드 4번 — 옛 주인공 시트를 v3 몸으로 교체, 2차)"
STD = {"image", "action", "frameWidth", "frameHeight", "frames", "directions", "layout", "frameIndex", "fps",
       "frameDurationsMs", "loop", "pivot", "palette", "source", "pivotNote"}
FIRST = ("impactFrame", "cancelFromFrame", "holdFrame", "releaseFrame", "refillFrame", "burstFrame", "eyeOpenFrame")
LAST = ("teleportAfterFrame",)
ALL = ("hitFrames", "activeFrames", "recoverFrames", "leapFrames", "loopFrames", "progressFrames")
PERFRAME = ("drawPx",)
HIT_FIELDS = ("hitRadiusPx", "impactDistancePx")
UNIT_NOTE = ("v3 도트 단위(pixelScale 0.5). 판정 길이(hitRadiusPx·thrust·impactDistancePx)는 구 값 ×4 = 칼 v3 와 같은 환산"
             "(구 33 → v2 66 논리 → v3 132 도트), 몸 그림 기준 오프셋(leapOffsetsPx·impactOffsetPx)은 몸 비율 ×6. 시스템 실제 판정값이 우선.")
ANCHOR2 = ("handAnchors = 프레임별 손 중심(몸 시트 도트, 해부 기준 R 오른손 · L 왼손). 대검 = 두 손(R 코등이 쪽 · L 손잡이 끝), "
           "단검 = R(역수), 활 = L 줌통 · R 시위. 구 무기 시트를 붙일 때는 oldWeapon 참고.")


def remap_meta(old, first, groups, n_new):
    """구 JSON 메모 → 새 프레임 번호. 반환 (meta, 알 수 없는 필드 목록)."""
    m = {}
    for k, v in old.items():
        if k in STD:
            continue
        if k in FIRST and v is not None:
            m[k] = first[v]
        elif k in LAST and v is not None:
            m[k] = groups[v][-1]
        elif k in ALL and isinstance(v, list):
            m[k] = [j for i in v for j in groups[i]]
        elif k in PERFRAME and isinstance(v, list):
            m[k] = [v[i] if i < len(v) else None for i, g in enumerate(groups) for _ in g]
        elif k == "phases":
            if old.get("action") == "birth":            # 구 탄생 시트는 [시작, 끝] 범위
                m[k] = {ph: [j for i in range(a, b + 1) for j in groups[i]] for ph, (a, b) in v.items()}
            else:
                m[k] = {ph: [j for i in fr for j in groups[i]] for ph, fr in v.items()}
        elif k == "overlayFx":
            m[k] = [dict(o, atFrame=first[o["atFrame"]]) if "atFrame" in o else dict(o) for o in v]
        elif k == "fx" and isinstance(v, dict):
            m[k] = {a: (first[b] if a.endswith("Frame") and isinstance(b, int) else b) for a, b in v.items()}
        elif k in HIT_FIELDS and isinstance(v, (int, float)):
            m[k] = v * Q.HIT_SCALE
        elif k == "thrust":
            m[k] = {a: (b * Q.HIT_SCALE if a in ("lengthPx", "widthPx", "fromPx") else b) for a, b in v.items()}
        elif k == "leapOffsetsPx":
            m[k] = {str(j): v[s] * Q.OLD_SCALE for s in v for j in groups[int(s)]}
        elif k == "hitOrigin":
            m[k] = "몸 중심 = 피벗(발)에서 위로 60 도트 (96×144 몸 기준)"
        else:
            m[k] = copy.deepcopy(v)
    if "hitFrames" in old and old["hitFrames"] and "impactFrame" not in m:
        m["impactFrame"] = first[old["hitFrames"][0]]
    m["oldTiming"] = {"frames": old["frames"], "frameDurationsMs": old["frameDurationsMs"],
                      "framesMap": [list(g) for g in groups]}
    return m


def check_timing(name, old, ms, first, m):
    st, ost = EX.starts(ms), EX.starts(old["frameDurationsMs"])
    assert sum(ms) == sum(old["frameDurationsMs"]), (name, "total")
    for i, f in enumerate(first):
        assert st[f] == ost[i], (name, "old frame start", i, st[f], ost[i])
    t = old.get("timingMs") or {}
    probe = {"hitAt": m.get("impactFrame"), "cancelAt": m.get("cancelFromFrame"), "impactAt": m.get("impactFrame"),
             "leapStart": (m.get("leapFrames") or [None])[0], "recoverFrom": (m.get("recoverFrames") or [None])[0]}
    for k, v in t.items():
        if k == "total":
            assert v == sum(ms), (name, k)
        elif k in probe:
            got = None if probe[k] is None else st[probe[k]]
            assert got == v, (name, k, got, v)
    if m.get("activeFrames"):
        a = m["activeFrames"][-1]
        oa = old["activeFrames"][-1]
        assert st[a] + ms[a] == ost[oa] + old["frameDurationsMs"][oa], (name, "active end")
    return {"checked": sorted(t) + ["frameStarts", "activeEnd"] if t else ["frameStarts", "total"]}


def export_gear(name, r):
    old, first, groups, ms = r["old"], r["first"], r["groups"], r["ms"]
    fr = r["frames"]
    n = len(ms)
    m = remap_meta(old, first, groups, n)
    chk = check_timing(name, old, ms, first, m)
    if "timingMs" in m:
        st = EX.starts(ms)
        if m.get("activeFrames"):
            m["timingMs"]["activeEndAt"] = st[m["activeFrames"][-1]] + ms[m["activeFrames"][-1]]
    if "impactOffsetPx" in m:                     # 구 '칼끝 실제 위치' → 새 그림의 무기 끝(안내선) 위치
        imp = m["impactFrame"]
        m["impactOffsetPx"] = {d: {"x": round(fr[d][imp][3][0] - hero.PIV[0]), "y": round(fr[d][imp][3][1] - hero.PIV[1])}
                               for d in hero.DIRS if fr[d][imp][3]}
    wsrc = Q.old_weapon_frames(name)
    old_map = [oi for (_, _, _, _, _, oi) in fr["down"]]
    ow = None
    if wsrc:
        est = {d: [Q.old_grip_estimate(f, wsrc["off"], r["weapon"]) for f in wsrc["frames"][d]] for d in hero.DIRS}
        ow = {"sheet": "weapons/" + wsrc["sheet"], "oldFrameForFrame": old_map, "scaleDots": Q.OLD_SCALE,
              "oldPivot": list(wsrc["pivot"]), "gripHand": Q.GRIP_HAND[r["weapon"]], "oldGripEstimate": est,
              "note": "구 무기 시트를 v3 몸에 임시로 붙이는 법(무기 재디자인 전까지): 새 프레임 i → 구 무기 프레임 oldFrameForFrame[i], "
                      "도트 ×6 최근접 확대(논리 ×3) 후 oldGripEstimate×6 이 handAnchors[gripHand] 에 오도록 평행 이동. "
                      "oldGripEstimate 는 구 몸 중심에 가장 가까운 무기 픽셀(자동 추정, ±1px)."}
    hands = {d: [anim.hands_px(f[1]) for f in fr[d]] for d in hero.DIRS}
    scars = {d: [dict(f[1].scar) for f in fr[d]] for d in hero.DIRS}
    v3w = "weapons/v3/%s" % Q.OLD_WEAPON[name] if os.path.exists(os.path.join(EX.OUT_W, Q.OLD_WEAPON[name] + ".png")) else None
    wl = [None if k == Q.IDLE else {"thetaDeg": round(k["th"], 1), "elevDeg": round(k["el"], 1)} for (_, _, _, _, k, _) in fr["right"]]
    tips = {d: [None if f[3] is None else [round(f[3][0], 1), round(f[3][1], 1)] for f in fr[d]] for d in hero.DIRS}
    states = ["idle" if k == Q.IDLE else k["state"] for (_, _, _, _, k, _) in fr["right"]]
    bname = "player_%s" % name
    im = EX.sheet({d: [f[0] for f in fr[d]] for d in hero.DIRS}, hero.FW, hero.FH)
    im.save(os.path.join(EX.OUT_P, bname + ".png"))
    data = EX.base(bname + ".png", old.get("action", name), hero.FW, hero.FH, ms, False, hero.PIV, emissiveColors=EX.EMISSIVE, **m)
    data["source"] = SRC2
    data.update(timingCheck=chk, timingNote="구 시트(16×24)의 프레임마다 시작 ms·전체 ms 가 같다 — 한 구 프레임을 oldTiming.framesMap 의 새 프레임들로 나눠 보간.",
                unitNote=UNIT_NOTE, frameStates=states, handAnchors=hands, anchorNote=ANCHOR2,
                scarAnchor=scars, scarAnchorNote=EX.SCAR_NOTE,
                weaponLocal=wl, weaponLocalNote="프레임별 무기 방향(몸 기준 θ: 0 = 앞, + = 해부 오른쪽 · elev + = 위). 무기 재디자인 때 이 방향으로 그린다. idle = 대기 0 그림.",
                weaponTipDots=tips, weaponTipNote="안내선(미리보기용 임시 무기 길이) 끝 위치(몸 시트 도트) — 이펙트 위치 참고",
                weapon=r["weapon"], oldWeapon=ow if not v3w else None, weaponOverlayV3=v3w,
                weaponOverlayNote=("weapons/v3/%s 를 같은 프레임 번호·같은 시각에 겹친다(53라운드 무기 재디자인, weapons_v3). oldWeapon 은 더 쓰지 않는다." % Q.OLD_WEAPON[name])
                if v3w else "v3 무기 오버레이 없음 — 53라운드 번외(키아트 기준 무기 재디자인) 때 새로 그림. 그때까지 oldWeapon 방식 임시.",
                note=BODY2_NOTE.get(r["weapon"], "") + " " + EX.BODY_NOTE)
    if name == "bow_reload":
        data["progressFormula"] = "frame = min(%d, floor(progress*%d)) — 구 5프레임 → %d프레임(refillFrame 시각 동일)" % (n - 1, n, n)
    if name == "attack":
        data.update(releaseFrame=first[2], releaseAtMs=EX.starts(ms)[first[2]],
                    attackKind="bow quick shot (구 frameNotes: 0 실체화 · 1 시위 당김 · 2 발사(화살 생성) · 3 불티)",
                    attackNote="구 기본 공격은 무기 공통 4프레임이었다. 지금 연격이 없는 무기는 활뿐이라 활 빠른 사격 몸으로 그렸다(질문 올림). "
                               "근접 무기가 이 시트를 쓰면 왼손 줌통 자세가 어색하다.")
    if name in ("greatsword_draw", "greatsword_sheathe"):
        data["endsWith"] = ("player_idle_free down/up/left/right 0 (마지막 프레임 = 왼손이 빈 대기 0 과 같은 몸, 53라운드 Q19)"
                            if Q.GEAR[name].get("idleBody") == "free" else "player_idle down/up/left/right 0 (마지막 프레임 = 대기 0 과 같은 몸)")
    EX.write_json(os.path.join(EX.OUT_P, bname + ".json"), data)
    return im, data


BODY2_NOTE = {"greatsword": "대검: 두 손으로 쥔다(왼손이 손잡이 끝).",
              "dagger": "단검: 역수(날이 새끼손가락 쪽) — 장전 때 날을 팔뚝에 붙이고, 찌를 때 손목을 꺾어 앞·아래로 박는다.",
              "bow": "활: 왼손(완갑 낀 팔) = 줌통, 오른손 = 시위. 당길수록 어깨·등 긴장(승모·견갑 능선)."}


def export_birth(frames, ms, first, groups, old, idle0):
    n = len(ms)
    m = remap_meta(old, first, groups, n)
    check_timing("birth", old, ms, first, m)
    last = frames[-1][0].crop((B.OFF, B.OFF, B.OFF + hero.FW, B.OFF + hero.FH))
    assert last.tobytes() == idle0.tobytes(), "birth last frame != player_idle down 0"
    im = EX.sheet({"down": [f[0] for f in frames], "up": [], "left": [], "right": []}, B.W, B.W).crop((0, 0, B.W * n, B.W))

    def off(h):
        return {k: [v[0] + B.OFF, v[1] + B.OFF] for k, v in h.items()}
    hands = [None if R is None else off(anim.hands_px(R)) for _, R, _ in frames]
    scars = [None if R is None else dict(R.scar, x=R.scar["x"] + B.OFF, y=R.scar["y"] + B.OFF, visible=False) for _, R, _ in frames]
    im.save(os.path.join(EX.OUT_P, "player_birth.png"))
    data = EX.base("player_birth.png", "birth", B.W, B.W, ms, False, B.PIV, emissiveColors=EX.EMISSIVE, **m)
    data.update(directions=["down"], source=SRC2, totalMs=sum(ms),
                pivotNote="피벗 (96,186) = 주인공 발. 몸 96×144 는 (48,48) 에 놓인다(bodyOffset) — player_* v3 피벗 (48,138) 과 같은 점.",
                bodyOffset={"x": B.OFF, "y": B.OFF},
                endsWith="player_idle_down frame 0 (마지막 프레임의 몸 = v3 player_idle down 0 과 픽셀 동일, assert)",
                timingNote="구 시트(32×32, 18프레임) 의 프레임마다 시작 ms·전체 ms 가 같다. burstFrame·eyeOpenFrame 시각 불변.",
                handAnchors={"down": hands}, scarAnchor={"down": scars},
                scarAnchorNote="탄생은 정면(down)뿐 — 상흔은 아직 없음(visible false). 좌표는 이 시트(192) 기준.",
                anchorNote="handAnchors 는 이 시트(192×192) 좌표. 형체가 없는 프레임은 null.",
                version="v3 (53라운드 4번) — 혼불 7개 나선 + 바닥 재 소용돌이 → 혼불 덩이·재 무덤 → 흙빛 형체가 아래부터 굳음 → 껍데기 터짐(백열 균열·불티) → 무릎 → 일어섬",
                note=EX.BODY_NOTE)
    data["layout"] = "1 row (down), columns = frames"
    if "ambientNote" in data.get("fx", {}):
        data["fx"]["ambientNote"] = data["fx"]["ambientNote"].replace("f0~f4", "f0~f%d" % groups[4][-1])
    EX.write_json(os.path.join(EX.OUT_P, "player_birth.json"), data)
    return im, data

