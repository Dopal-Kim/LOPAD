"""58라운드 대검 — Q4 진짜 3/4 대각 리그로 대검 8행 시트 전부의 대각 행 재작업 + Q3 차지 휘둘러 내리찍기(greatsword_charge_swing).

이 프로세스 안에서만 rig34.install()(대각 FACING 55° · 투영 KY 0.70 · 3/4 몸) 을 걸고, 56라운드 렌더·내보내기(gs56 · kg_gs)를 그대로 돌린다.
  기존 4행(down · up · left · right)은 코드가 같으므로 픽셀이 그대로다(빌드 뒤 assets 와 대조 — check_rows4).
  틀은 56라운드 값 고정(연격 240×280·offset (69,69) · 새 기본기 280×296·offset (91,68)) — 계약 §18.3·§18.8 그대로.
산출: player/v3/player_greatsword_* · weapons/v3/greatsword_*  (연격 6 + 새 기본기 4 = 10시트 재출력, + 새 charge_swing)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "combo56_body"))
sys.path.insert(0, os.path.join(WORK, "combo56_moves_kg"))
sys.path.insert(0, HERE)

import rig34  # noqa: E402

rig34.install()
import gs56  # noqa: E402
import moves56 as MV  # noqa: E402
from rig8 import DIRS8, DIAG, Q, EX, hero, wv3  # noqa: E402
import greatsword as GS  # noqa: E402

K_ = Q.K_
SRC58 = "parts/art/work/combo58/build.py gs (58라운드 Q3 차지 휘둘러 내리찍기 · Q4 진짜 3/4 대각 리그)"
FIXED = {"combo": (240, 280, 69, 69), "kg": (280, 296, 91, 68)}
USED = {}

DIR_NOTE58 = ("58라운드 Q4 진짜 3/4 대각: 대각 4행(down-right · down-left · up-right · up-left)은 전용 3/4 몸 리그(combo58/rig34.py — 몸을 높이별 단면으로 보고 "
              "45° 돌려 다시 그림: 얼굴·가슴 균열·견갑·일기장이 바라보는 쪽으로 돌아가고 먼 쪽 팔·다리는 몸 뒤)로 다시 그렸다. "
              "무기·손 투영도 대각만 바닥 압축 0.35 → 0.70(바닥 각 55° = 화면 45°)으로 바꿔 칼이 조준 대각으로 길게 읽힌다. "
              "행 순서·조준 8분할·판정 각도는 56라운드 그대로(down, up, left, right, down-right, down-left, up-right, up-left). 4행은 그대로.")


def fixed_crop(kind):
    W, H, ox, oy = FIXED[kind]
    cx, cy = GS.CANVAS_OFF
    box = (cx - ox, cy - oy, cx - ox + W, cy - oy + H)

    def crop(all_frames):
        fit, fbox = wv3.fit_frame([{d: [f["weapon"] for f in fr[d]] for d in DIRS8} for fr in all_frames.values()], GS.CANVAS_OFF)
        over = (fbox[0] < box[0], fbox[1] < box[1], fbox[2] > box[2], fbox[3] > box[3])
        print("frame fit", kind, fit, "fixed", FIXED[kind], "overflow" if any(over) else "ok", over)
        # 56 틀을 바탕으로, 3/4 대각 그림이 넘치는 쪽만 늘린다(8 배수) — 늘어나면 JSON frameWidth/Height·playerFrameOffset 이 바뀐다
        ub = [min(box[0], fbox[0]), min(box[1], fbox[1]), max(box[2], fbox[2]), max(box[3], fbox[3])]
        Wn, Hn = ub[2] - ub[0], ub[3] - ub[1]
        Wn, Hn = -(-Wn // 8) * 8, -(-Hn // 8) * 8
        ub = (ub[0], ub[1], ub[0] + Wn, ub[1] + Hn)
        frame = (Wn, Hn, cx - ub[0], cy - ub[1])
        USED[kind] = frame
        for fr in all_frames.values():
            for d in DIRS8:
                for f in fr[d]:
                    f["weapon"] = f["weapon"].crop(ub)
        return frame
    return crop


def patch_version(names, extra=None):
    for n in names:
        for path in (os.path.join(EX.OUT_P, "player_%s.json" % n), os.path.join(EX.OUT_W, "%s.json" % n)):
            j = json.load(open(path, encoding="utf-8"))
            j["directionNote"] = DIR_NOTE58
            if isinstance(j.get("directionRows"), list):
                for r in j["directionRows"]:
                    if r["direction"] in DIAG:
                        r["body"] = "3/4 (정면 쪽)" if r["direction"].startswith("down") else "3/4 (뒷면 쪽)"
            j["r58"] = "58라운드 Q4 진짜 3/4 대각 리그(대각 4행 재작업)" + (" · " + extra[n] if extra and n in extra else "")
            j["diagRig"] = dict(rig="combo58/rig34.py", bodyYawDeg={"down-right": 45, "down-left": -45, "up-right": 135, "up-left": -135},
                                weaponGroundDeg=round(rig34.ground_deg34("down-right"), 1), weaponKY=round(rig34.KY_DIAG, 3),
                                note="대각 몸 = 3/4 리그(ψ ±45°/±135°), 무기·손 = 바닥 각 55°·압축 0.70 투영. 56라운드 판(정면/뒷면 몸 + 3/4 단서)은 대체")
            j["version"] = "v3-r58"
            j["sourceR58"] = SRC58
            EX.write_json(path, j)


# =============================================================================
# 1. 연격 6시트(56 작업 B) — 3/4 리그로 다시
# =============================================================================
def build_combo():
    gs56.crop = fixed_crop("combo")
    frs, frame = gs56.build()
    patch_version(MV.ORDER)
    return frs, frame


# =============================================================================
# 2. 새 기본기 4시트(56 작업 E1) — 3/4 리그로 다시
# =============================================================================
def build_kg():
    import kg_gs
    gs56.crop = fixed_crop("kg")
    frs, frame = kg_gs.build()
    patch_version(kg_gs.ORDER)
    return frs, frame


# =============================================================================
# 3. 차지 휘둘러 내리찍기 (58 Q3) — 꽂기(plunge) 대체: 차지 유지(머리 뒤)에서 칼을 오른쪽 뒤로 떨어뜨려 크게 한 바퀴 휘둘러
#    머리 위를 넘겨 앞 바닥에 내리찍음 → 찍은 자리에서 균열이 마우스 방향으로 이어짐(fx greatsword_charge_crack_line_t1~t5)
# =============================================================================
SWING_FRAMES = [
    K_(180, 52, 0, 3, 71, crouch=3, lean=-0.8, off="two"),                                                  # 0 hold 끝(머리 위 뒤)
    K_(150, 8, 70, 10, 47, lunge=-0.35, crouch=5.5, tw=1.25, lean=-0.3, off="two"),                       # 1 drop 칼을 오른쪽 뒤로 떨어뜨림(몸 비틂)
    K_(105, -12, 58, 14, 44, lunge=-0.1, crouch=6.5, tw=1.15, lean=0.1, off="two"),                       # 2 sweep 오른쪽 옆 낮게 휘돌림
    K_(55, 30, 34, 16, 55, lunge=0.4, crouch=5.0, tw=0.65, lean=0.5, off="two"),                          # 3 rise 앞·위로 감아 올림
    K_(18, 72, 12, 10, 67, lunge=0.6, crouch=3.5, tw=0.2, lean=0.2, off="two"),                           # 4 apex 머리 위(가장 높이)
    K_(0, 5, 0, 17, 54, lunge=1.0, crouch=7.0, lean=1.6, off="two"),                                      # 5 crash 내려옴
    K_(0, -60, 0, 20, 33, lunge=1.3, crouch=12.8, lean=2.7, off="two", state="glow"),                     # 6 strike(판정 · 균열 출발)
    K_(0, -62, 0, 20.5, 32, lunge=1.4, crouch=13.8, lean=2.9, off="two"),                                 # 7 박힘(균열이 달림)
    K_(0, -63, 0, 21.5, 31, lunge=1.55, crouch=14.2, lean=3.05, off="two"),                               # 8 drag 몸이 칼 위로 끌려감
    K_(15, -34, 8, 15, 40, lunge=0.75, crouch=8.0, lean=1.5, off="two"),                                  # 9 catch 뽑음
    K_(36, -24, 22, 13, 42, lunge=0.3, crouch=4, tw=0.2, lean=0.7, off="two"),                            # 10 recover(휴대 각)
]
SWING_MS = [40, 70, 50, 40, 50, 40, 50, 110, 130, 100, 110]
SWING_IMPACT = 6
SLAM_FRAMES = [6, 7, 8]
CRACK_TILES_BY_STAGE = [3, 4, 5]          # 58 Q3: 차지 단계별 균열 최대 칸(1칸 = 16 월드 px = 64 도트)

SWING = dict(
    label="차지 휘둘러 내리찍기(마우스 방향 · 찍은 자리에서 균열이 커서 쪽으로)", frames=SWING_FRAMES, ms=SWING_MS, impact=SWING_IMPACT,
    active=[6], cancel=None,
    roles=["hold", "drop", "sweep", "rise", "apex", "heave", "strike", "planted", "drag", "catch", "recover"],
    arc=(0, 0), rScale=1.3, step=dict(world=12, frames=[4, 5, 6]),
    dragStep=dict(world=4, frames=[7, 8], note="박힌 칼 위로 몸이 쏠림(참고값)"),
    hitShape=dict(type="wedge", angleDeg=40, lengthRByStage=[1.3, 1.5, 1.8], impactCircle=dict(radiusR=0.35, atWedgeEnd=True),
                  note="찍은 자리 쐐기(차지 내려찍기와 같음) — 균열 판정은 crackLine(fx 앞머리)"),
    groundCrack=dict(sheet="greatsword_ground_crack", rowByStage=["m", "m", "l"], at="impactFrame 시작, slamAnchors(칼끝이 바닥에 닿은 자리)"),
    phases={"drop": [0, 1], "swing": [2, 3, 4, 5], "strike": [6], "planted": [7, 8], "recover": [9, 10]},
    startsFrom="greatsword_charge 루프 f3~f6 중 좌클릭 뗌(차지 단계 0.4/0.8/1.2초)", endsWith="greatsword_carry_drawn_idle",
)


def build_swing():
    name = "greatsword_charge_swing"
    MV.GS[name] = SWING
    gs56.V_TYPE = tuple(gs56.V_TYPE) + (name,)                     # 아래 대각 내려찍기 칼 방향 보정(56 규칙)
    fr = gs56.render(name)
    gs56.check_tips(name, fr)
    with gs56.dirs8():
        fit, box = wv3.fit_frame([{d: [f["weapon"] for f in fr[d]] for d in DIRS8}], GS.CANVAS_OFF)
        for d in DIRS8:
            for f in fr[d]:
                f["weapon"] = f["weapon"].crop(box)
        frame = fit
        print("charge_swing frame", frame)
        gs56.export_move(name, fr, frame)
    pal = wv3.hero_palette()
    st = gs56.check_colors(name, fr, pal)
    # 찍은 자리(칼끝이 바닥에 닿은 점) — 균열·땅 충격 fx 의 피벗
    slam = {d: [None] * len(SWING_MS) for d in DIRS8}
    for d in DIRS8:
        for i in SLAM_FRAMES:
            t = fr[d][i]["tip"]
            slam[d][i] = [round(t[0], 1), round(t[1], 1)]
    ox, oy = frame[2], frame[3]
    starts = MV.starts(SWING_MS)
    hit = starts[SWING_IMPACT]
    crack = crack_line_block(hit)
    upd = dict(r58="58라운드 Q3 대검 차지 = 마우스 방향으로 휘둘러 내리찍고 균열이 커서까지(꽂아내리기 greatsword_charge_plunge 대체)",
               chargeNote="58라운드 Q3: 꽂기 동작 폐기 — 차지를 떼면 이 동작. 차지 단계는 균열 최대 칸(3/4/5)·쐐기 길이·땅 충격 크기로",
               replaces="greatsword_charge_plunge (56 Q10 개성 발현 차지 — 시트는 보관)",
               slamFrames=SLAM_FRAMES, slamAnchors=slam,
               slamNote="slamAnchors = 칼끝이 바닥에 닿은 점(몸 시트 도트, slamFrames 만 값). 균열 선(crackLine)·땅 충격(greatsword_ground_crack) fx 의 pivot",
               crackLine=crack, swingFx="fx/v3/greatsword_charge_swing", version="v3-r58", source=SRC58,
               directionNote=DIR_NOTE58)
    for path, off in ((os.path.join(EX.OUT_P, "player_%s.json" % name), (0, 0)), (os.path.join(EX.OUT_W, "%s.json" % name), (ox, oy))):
        j = json.load(open(path, encoding="utf-8"))
        for k in ("arcFromDeg", "arcToDeg", "arcDeg", "arcNote"):
            j.pop(k, None)
        u = dict(upd)
        if off != (0, 0):
            u["slamAnchors"] = {d: [None if q is None else [round(q[0] + ox, 1), round(q[1] + oy, 1)] for q in v] for d, v in slam.items()}
            u["slamNote"] = "slamAnchors(무기 시트 좌표) = 몸 시트 좌표 + playerFrameOffset"
            u["frameNote"] = "차지 휘둘러 내리찍기 전용 틀 %dx%d · offset (%d,%d) — 연격 틀(240×280)과 다름. JSON frameWidth/frameHeight·pivot·playerFrameOffset 을 읽을 것" % frame
        j.update(u)
        EX.write_json(path, j)
    print(name, "ok", MV.timing(SWING), st)
    with open(os.path.join(HERE, "state_swing.json"), "w", encoding="utf-8") as f:
        json.dump(dict(frame=list(frame), slam=slam, stats=st, hitAt=hit), f, ensure_ascii=False, indent=1)
    return fr, frame


# 균열 선 규격(fx 와 공유 — gsfx58 이 같은 값으로 그림)
CRACK_TILE_DOTS = 64
CRACK_SPEED = 1.6                      # 도트/ms (= 0.4 월드 px/ms) — 5칸(320 도트)을 200ms 에
CRACK_MS = [30, 30, 30, 30, 30, 30, 30, 50, 60, 80, 100, 120]
CRACK_TRAVEL_FRAMES = 7


def crack_front(tiles):
    L = tiles * CRACK_TILE_DOTS
    out, t = [], 0
    for i, m in enumerate(CRACK_MS):
        t += m
        out.append(min(L, round(CRACK_SPEED * t)) if i < CRACK_TRAVEL_FRAMES else L)
    return out


def crack_line_block(hit):
    return dict(sheets={"t%d" % n: "fx/v3/greatsword_charge_crack_line_t%d" % n for n in (1, 2, 3, 4, 5)},
                maxTilesByStage=CRACK_TILES_BY_STAGE, tileDots=CRACK_TILE_DOTS,
                pickRule="칸 수 = min(차지 단계 최대(3/4/5), 찍은 자리 → 커서 거리 / 16 월드 px 를 반올림, 최소 1) → t1~t5. "
                         "벽에 막히면 막힌 곳까지의 칸 수로(내림)",
                anchor="slam_point", spawnAtMs=hit, spawnNote="impactFrame 시작(=hitAt)에 slamAnchors[행][impactFrame] 자리에 1회. 각도 = 찍은 자리 → 커서(rotate)",
                hitShape=dict(type="rect", fromPx=0, lengthPx="tiles × 64", halfWidthPx=28,
                              frontPxByFrame={("t%d" % n): crack_front(n) for n in (1, 2, 3, 4, 5)},
                              frameMs=CRACK_MS, speedDotsPerMs=CRACK_SPEED,
                              note="앞머리(frontPxByFrame)가 지나가는 칸만 맞는다(적마다 1회) — 참고값, 시스템 데이터 기준. 단위 도트(월드 px = 도트/4)"),
                lengthRule="58 Q3: 균열 최대 길이 = 차지 1단 3칸 · 2단 4칸 · 3단 5칸(찍은 자리부터 잼, 근접 유지)")


if __name__ == "__main__":
    args = sys.argv[1:] or ["combo", "kg", "swing"]
    if "combo" in args:
        build_combo()
    if "kg" in args:
        build_kg()
    if "swing" in args:
        build_swing()
