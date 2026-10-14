#!/usr/bin/env python3
"""P19 주인공 역동성 — 빌드 (도영 님 지시: '키아트 기반으로 역동성·민첩·무서운 느낌, 조작하는 느낌').

방식 b+(무기 오버레이 동기): 무기 그림은 다시 그리지 않는다. 몸만 새 자세로 다시 렌더하고, 프레임마다 정수 도트 오프셋으로
그 몸 시트를 쓰는 무기 오버레이 전부(weapons/v3·v4 — 휴대·뽑아 든·각성·검기·울분·1차/2차 각성 a1·a2·a2_glow)를 같이 옮긴다.
손은 '기존 손 기준점 + 같은 오프셋' 에 IK 로 고정 → 손잡이·칼집 입구·활 줌통이 손과 어긋나지 않는다. 프레임 수·ms·피벗 그대로.

사용: python3 parts/art/work/hero19/build.py [loco] [skid] [fx] [attack] [preview]   (인자 없으면 전부)
      원본은 항상 git sync19.SRC_REV — 다시 돌려도 결과가 같다(결정적).
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import body19 as B  # noqa: E402
import loco19 as L  # noqa: E402
import sync19 as S  # noqa: E402

SRC = "parts/art/work/hero19/build.py (P19 주인공 역동성 — hero_v3 리그 재자세 · 무기 오버레이 프레임 오프셋 동기)"
P19_NOTE = ("P19 주인공 역동성(2026-10-14): 키아트 hero3_b 의 낮게 웅크린 포식자 결로 몸만 다시 렌더. 프레임 수·ms·피벗·판정 시점 그대로. "
            "무기 오버레이는 다시 그리지 않고 프레임마다 weaponOffsetDots 만큼 통째로 옮겼다(handAnchors 도 같은 만큼) — 손·무기 동기 유지.")

LOCO = [  # (동작, 몸 시트)
    ("idle", "player_idle"), ("idle", "player_idle_free"),
    ("walk", "player_walk"), ("walk", "player_walk_free"),
    ("run", "player_run"), ("run", "player_run_free"),
    ("dash", "player_dash"),
    ("hurt", "player_hurt"), ("death", "player_death"),
]
LOG = {}
BODY_ONLY = False          # 'bodyonly' 인자: 몸 시트만 다시(오버레이 동기는 결정적이라 그대로 둠)


def body_meta(meta, fr, extra=None):
    m = dict(meta)
    m["handAnchors"] = {d: [f["hands"] for f in fr[d]] for d in fr}
    m["scarAnchor"] = {d: [B.scar_of(f["rig"]) for f in fr[d]] for d in fr}
    m["weaponOffsetDots"] = {d: [list(f["off"]) for f in fr[d]] for d in fr}
    m["weaponOffsetBackDots"] = {d: [list(f["back_off"]) for f in fr[d]] for d in fr}
    m["eyeAnchors"] = {d: [f["eye"] for f in fr[d]] for d in fr}
    m["chestAnchors"] = {d: [f["chest"] for f in fr[d]] for d in fr}
    m["fxAnchorNote"] = ("P19 fx 기준점(몸 도트): eyeAnchors = 분노한 눈 중심(fx/v3/hero_eye_trail 자리, null = 안 보임 — 뒷모습·눈 깜빡), "
                         "chestAnchors = 가슴 균열(fx/v3/hero_ember_breath 자리). 몸 피벗 기준 = (x − 48, y − 138)")
    m["p19"] = P19_NOTE
    m["source"] = SRC
    m["previousSource"] = meta.get("source")
    if extra:
        m.update(extra)
    return m


def colors_of(frames_by_dir):
    s = set()
    for lst in frames_by_dir.values():
        for im in lst:
            s |= {p[:3] for p in im.getdata() if p[3]}
    return s


def sync_family(body, fr, rename=None, src_body=None):
    """body 를 쓰는 오버레이 전부를 프레임 오프셋으로 옮겨 내보낸다. rename = [(옛, 새)] 면 새 이름의 시트로."""
    rels = S.family(src_body or body)
    lost_tot = 0
    for rel in rels:
        meta, im = S.src_grid(rel)
        n_old = meta["frames"]
        key = "back_off" if S.is_back_carry(rel) else "off"
        plan = {d: [(f["src"], f[key][0], f[key][1]) for f in fr[d]] for d in meta["directions"]}
        cells, lost = S.move_cells(meta, im, plan)
        m = S.remap_meta(meta, plan, n_old)
        m["p19"] = "P19 주인공 역동성: 몸 새 자세에 맞춰 프레임마다 %s 만큼 옮김(그림은 그대로)" % ("weaponOffsetBackDots(가슴 이동 — 등에 멘 대검)" if key == "back_off" else "weaponOffsetDots(왼허리 이동)")
        out_rel = rel
        if rename:
            m = S.rename_strings(m, rename)
            for a, b in rename:
                out_rel = out_rel.replace(a, b)
            m["frameDurationsMs"] = list(L.SKID_MS)
            m["fps"] = round(1000.0 * len(L.SKID_MS) / sum(L.SKID_MS), 2)
            m["loop"] = False
            m["derivedFrom"] = rel
        S.write_grid(out_rel, cells, m)
        lost_tot += lost
        if lost:
            print("  ! %s 틀 밖 %d px" % (out_rel, lost))
    return len(rels), lost_tot


def build_loco(only=None):
    for act, body in LOCO:
        if only and act not in only and body not in only:
            continue
        t0 = time.time()
        free = act in ("hurt", "death")
        fr = B.render_sheet(body, L.ACTS[act], L.OLD_ACTS[act], free_hands=free)
        meta = B.load_json("player/v3/" + body)
        frames = {d: [f["img"] for f in fr[d]] for d in fr}
        errs = max(f["err"] for d in fr for f in fr[d])
        assert errs < 1.2, (body, "손 IK 오차", errs)
        extra = {}
        if act == "idle":
            extra["eyeBlinkFrame"] = 5
            extra["p19Idle"] = "숨 들썩(2·3 프레임 가장 높음) · 균열 맥동 2·3 · 눈빛 치켜뜸 1~3 · 눈 깜빡 5"
        if act == "dash":
            extra["p19Dash"] = "키아트 LOW LUNGING DASH — 0 웅크림 · 1 박차 · 2·3 거의 수평 활공 · 4 제동. 잔상 fx = fx/v3/hero_dash_afterimage(1·2·3 프레임 시작에 같은 번호 변주), 제동(4) = fx/v3/hero_skid_dust(대쉬 방향 행), 눈빛 꼬리 = fx/v3/hero_eye_trail 16ms 마다"
        S.write_grid("player/v3/" + body, frames, body_meta(meta, fr, extra))
        n, lost = (0, 0) if (free or BODY_ONLY) else sync_family(body, fr)
        LOG[body] = dict(colors=len(colors_of(frames)), handErrMax=round(errs, 2), overlays=n, lostPx=lost,
                         offsets={d: [f["off"] for f in fr[d]] for d in ("down", "right")}, sec=round(time.time() - t0, 1))
        print(body, LOG[body])


SKID_SRC = [4, 4, 0, 0]          # 미끄럼 프레임이 손·무기 그림을 빌려 오는 대쉬 프레임(4 제동 · 0 웅크림)


def build_skid():
    fr = B.render_sheet("player_dash", L.act_turn_skid, L.OLD_ACTS["dash"], src_cols=SKID_SRC)
    meta = B.load_json("player/v3/player_dash")
    m = S.remap_meta(meta, {d: [(c, 0, 0) for c in SKID_SRC] for d in meta["directions"]}, meta["frames"])
    for k in ("phases", "fxNote", "v2Timing"):
        m.pop(k, None)
    m = S.rename_strings(m, [("player_dash", "player_turn_skid"), ("carry_drawn_dash", "carry_drawn_turn_skid"), ("carry_dash", "carry_turn_skid")])
    m.update(action="turn_skid", image="player_turn_skid.png", frameDurationsMs=list(L.SKID_MS), loop=False,
             fps=round(1000.0 * len(L.SKID_MS) / sum(L.SKID_MS), 2),
             note="P19 새 동작 — 방향 전환 미끄럼. 행 = 새로 향하는 방향. 0 앞발을 박고 몸이 뒤로 받침 → 1 미끄러지며 상체가 새 방향으로 → 2 뒷발로 박참 → 3 달리기 0 쪽. "
                  "모든 무기 공용 몸(대쉬처럼) — 오버레이 <무기>_carry_turn_skid · <무기>_carry_drawn_turn_skid(대쉬 휴대 그림을 프레임 오프셋으로 옮긴 것).",
             turnSkid={"trigger": "이동 중(달리기 속도의 60% 이상) 입력 방향이 135° 이상 꺾인 순간 1회. 이동·공격 입력을 막지 않는 장식 동작 — 공격·대쉬가 나가면 즉시 끊음",
                       "row": "새 방향(입력 방향) 4방향 행", "then": "player_run 0 (입력 유지) / player_idle 0 (입력 없음)",
                       "fx": "fx/v3/hero_skid_dust 를 0 프레임에 발 피벗(옛 진행 방향 쪽으로 흩날림)",
                       "srcDashFrames": SKID_SRC})
    frames = {d: [f["img"] for f in fr[d]] for d in fr}
    S.write_grid("player/v3/player_turn_skid", frames, body_meta(m, fr))
    n, lost = (0, 0) if BODY_ONLY else sync_family("player_turn_skid", fr, rename=[("player_dash", "player_turn_skid"), ("carry_drawn_dash", "carry_drawn_turn_skid"),
                                                          ("carry_dash", "carry_turn_skid")], src_body="player_dash")
    LOG["player_turn_skid"] = dict(colors=len(colors_of(frames)), overlays=n, lostPx=lost,
                                   offsets={d: [f["off"] for f in fr[d]] for d in ("down", "right")})
    print("player_turn_skid", LOG["player_turn_skid"])


def main(argv):
    global BODY_ONLY
    BODY_ONLY = "bodyonly" in argv
    argv = [a for a in argv if a != "bodyonly"]
    steps = argv or ["loco", "skid", "fx", "attack", "preview"]
    only = [a for a in argv if a.startswith("player_") or a in L.ACTS]
    if "loco" in steps or only:
        build_loco(only or None)
    if "skid" in steps:
        build_skid()
    if "fx" in steps:
        import fx19
        fx19.build()
    if "attack" in steps:
        import attack19
        attack19.build()
    if "preview" in steps:
        import gif19
        gif19.build()
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    lp = os.path.join(HERE, "stats.json")
    old = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else {}
    old.update({k: {kk: (vv if not isinstance(vv, dict) else {a: [list(x) for x in b] for a, b in vv.items()}) for kk, vv in v.items()} for k, v in LOG.items()})
    with open(lp, "w", encoding="utf-8") as f:
        json.dump(old, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
