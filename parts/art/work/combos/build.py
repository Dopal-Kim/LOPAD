#!/usr/bin/env python3
"""LOPAD 48라운드 Q2 — 근접 3연격(칼·대검·단검 × 1·2·3타) + 무기 든 특수 동작(패링·가드·그림자 걸음·조준) — 단일 소스.

실행: python3 parts/art/work/combos/build.py
근거: decisions/2026-10-02-round-48-playfeel-route.md Q2, contracts/art-assets.md §6.1·§6.2 (+ §3·3.1·3.2 겹침·이펙트 규약),
      parts/art/fx-design.md (인페르노 언어: W0 가장자리 → 보조 램프 몸체 → 1px 백열 코어, 겹 1프레임 지연), parts/art/art-bible.md.
입력 (읽기만): parts/art/palette/lopad.json, parts/art/work/player/build.py (몸 리그), parts/art/work/weapons/build.py (칼날·활 어휘),
      parts/art/work/fx_concept/build.py (Canvas·호·광선·꼬리), assets/sprites/{enemies/dummy_idle, fx/parry_flash, fx/guard_wave,
      fx/shadowstep_ghost, fx/aim_charge}.png, assets/tiles/stage1.png (목업 바닥, 없거나 읽기 실패면 단색)
산출:
  assets/sprites/player/player_<w>_combo<n>.png/.json   16x24 4방향 (w = katana·greatsword·dagger, n = 1·2·3)
  assets/sprites/weapons/<w>_combo<n>.png/.json         48x48 (대검 64x64) 같은 프레임·같은 ms, 피벗 = 주인공 피벗
  assets/sprites/fx/<w>_combo<n>.png/.json              칼 96 · 대검 128 · 단검 64, anchor player_pivot, impactFrame 1
  assets/sprites/player/player_<w>_special + weapons/<w>_special (katana 패링 · greatsword 가드 · dagger 그림자 걸음)
  assets/sprites/player/player_bow_aim + weapons/bow_aim (시위 당김, 진행도 프레임 0~5 + 발사 6)
  parts/art/work/combos/preview_<w>.png, preview_specials.png, preview_mock_1x.png / preview_mock_2x.png (카메라 2배), gif/*.gif
기존 player_attack · weapons/<w>_attack · fx/<w>_slash 는 건드리지 않는다.

49라운드 개정 (decisions/2026-10-02-round-49-playtest2.md 4·5절, art §7.2) — 10절:
  대검 combo1~3 재제작(두 손 큰 휘두름, 판정 f2, recoverFrames) · 칼 combo1 = 발도 베기(허리 칼집)
  player_greatsword_slam + weapons/greatsword_slam + fx/greatsword_slam (leapFrames · impactFrame)
  player_greatsword_dashslash + weapons/greatsword_dashslash (recoverFrames)
  fx/dagger_combo<n>_heat<k> (k = 1·2·3, 80 캔버스) · player_bow_reload + weapons/bow_reload
  공용 기하 = combos/gear.py (carry/build.py 와 공유). 미리보기 preview_r49_actions · preview_dagger_heat · preview_mock_r49_*.
"""
import importlib.util
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
SPR = os.path.join(ROOT, "assets", "sprites")
OUT_P = os.path.join(SPR, "player")
OUT_W = os.path.join(SPR, "weapons")
OUT_FX = os.path.join(SPR, "fx")
os.makedirs(os.path.join(HERE, "gif"), exist_ok=True)


def _load(name, rel, extra_path=None):
    if extra_path:
        sys.path.insert(0, extra_path)
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


P = _load("lopad_player", "parts/art/work/player/build.py", os.path.join(ROOT, "parts", "art", "work", "player"))
WP = _load("lopad_weapons", "parts/art/work/weapons/build.py")
K = _load("lopad_fx_concept", "parts/art/work/fx_concept/build.py")

G, C, W, X0, X1 = K.G, K.C, K.W, K.X0, K.X1
DIRS = ["down", "up", "left", "right"]
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
FONTB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 12)
PAL_PLAYER = "parts/art/palette/lopad.json (gray + floor 1 accent slots 21, 23; rim G04)"
PAL_WEAPON = "parts/art/palette/lopad.json (gray G00 G05 G08 G13 + floor 1 accent 16-27, runtime swap)"
PAL_FX = ("parts/art/palette/lopad.json (gray + floor 1 accent 16-27 runtime swap + fx block: core X0/X1 + "
          "weapon secondary W0-W3 fixed)")
DEPTH = {"down": "above", "left": "above", "right": "above", "up": "below"}
SRC = "parts/art/work/combos/build.py (48라운드 Q2)"

# ============================================================ 1. 판정 수치 (임시 — NOTES.md 3절)
# 공개 결정 로그의 기존 근접 판정(11b·14라운드): 칼 24x16 리치 14 / 대검 36x28 리치 20 / 단검 16x12 리치 10.
# '먼 끝' = 리치 + 짧은 변/2 (칼 22 · 대검 34 · 단검 16) → x1.5 = 칼 33 · 대검 51 · 단검 24.
# 호의 바깥 가장자리 = hitRadiusPx (그림 = 판정). 반경 원점 = 몸 중심 = 피벗(발)에서 위로 10px.
BODY_CENTER_DY = 10
HIT = {"katana": 33, "greatsword": 51, "dagger": 24}

# 화면 각(0 = 오른쪽, +90 = 아래). right 방향 기준 θ 를 방향별로 바꾼다 (fx 는 right 그림을 90° 회전·좌우 반전 — 같은 규약).
def to_screen(d, th):
    return {"right": th, "down": th + 90, "up": th - 90, "left": 180 - th}[d]


def unit(deg):
    a = math.radians(deg)
    return math.cos(a), math.sin(a)


# ============================================================ 2. 주인공 몸 (16x24, player/build.py 리그 재사용)
PW, PH = 16, 24


def shoulder(d, p, which):
    """draw_front / draw_side 의 어깨 좌표와 동일."""
    if d in ("down", "up"):
        x = (11 if which == "r" else 4) + p.body_dx
    else:
        m = 1 if d == "right" else -1
        x = (9 if m > 0 else 6) + p.body_dx * m
    return x, 10 + p.body_dy + p.crouch


def clamp_hand(x, y):
    return max(0, min(15, int(round(x)))), max(1, min(22, int(round(y))))


def render_body(d, p, extra_arms=()):
    """extra_arms: [(sx, sy, hx, hy)] — 리그가 그리지 않는 두 번째 팔(활 시위 손, 대검 가드의 왼손)."""
    s = P.Sprite(PW, PH, palette=P.PALETTE)
    if d == "down":
        P.draw_front(s, p, back=False)
    elif d == "up":
        P.draw_front(s, p, back=True)
    elif d == "right":
        P.draw_side(s, p, +1)
    else:
        P.draw_side(s, p, -1)
    for sx, sy, hx_, hy_ in extra_arms:
        P.draw_arm(s, sx, sy, hx_, hy_)
    P.finish(s, p)
    return s.composite(1)


def combo_pose(wid, d, fr, combo):
    """fr = (θ 칼날·팔 각, 팔 길이 L, fwd 앞으로, dip 내려앉음, crouch, state). 손 = 어깨 + L·(cosφ, sinφ)."""
    th, L, fwd, dip, crouch, state = fr
    phi = to_screen(d, th)
    if d in ("down", "up") and state in ("fade", "embers"):
        # 정면·후면 복귀 프레임: 옆면의 '내린 칼'(θ≈90)이 정면에서는 어깨 높이 가로가 되어 얼굴을 가린다 → 화면 아래(90°)로 60% 끌어내림
        diff = ((90 - phi + 180) % 360) - 180
        phi = phi + diff * 0.6
        L = min(L, 4)
    p = P.Pose(body_dy=dip, crouch=crouch)
    side = d in ("left", "right")
    if side:
        p.body_dx = max(-1, min(1, fwd))
        p.lean = fwd
        p.r_arm = "pos"
        if wid == "greatsword":
            p.l_dx, p.r_dx = 1, -1                 # 넓게 벌린 발
        if wid == "dagger" and combo == 3 and fwd >= 2:
            p.l_dx, p.r_dx = 2, -1                 # 찌르며 내딛음
    else:
        which = "r" if d == "down" else "l"
        if which == "r":
            p.r_arm = "pos"
        else:
            p.l_arm = "pos"
        if wid == "greatsword":
            p.l_arm = p.r_arm = "pos"              # 두 손 잡기
    which = "r" if d != "up" else "l"
    sx, sy = shoulder(d, p, which)
    ux, uy = unit(phi)
    hand = clamp_hand(sx + L * ux, sy + L * uy)
    if not side:
        # 정면·후면: 손이 몸 바깥쪽에 있으면 상체를 그쪽으로 1px
        p.body_dx = 1 if hand[0] >= 13 else (-1 if hand[0] <= 2 else 0)
        sx, sy = shoulder(d, p, which)
        hand = clamp_hand(sx + L * ux, sy + L * uy)
    p.hand_pos = hand
    return p, hand, phi, state


# ============================================================ 3. 손에 든 무기 (weapons/build.py 어휘: 쇠 G13/G08/G05 + 날밑 G00 + 감개 21)
SPEC = {
    "katana":     dict(length=11, width=2, hilt=3, guard=1, wrap=(1, 3), canvas=48),
    "greatsword": dict(length=17, width=3, hilt=4, guard=2, wrap=(4,), canvas=64),
    "dagger":     dict(length=6, width=2, hilt=2, guard=1, wrap=(2,), canvas=48),
}


def wcanvas(wid):
    n = SPEC[wid]["canvas"] if wid in SPEC else 48
    off = (n - 16) // 2                    # 48 → (16,16), 64 → (24,24)
    return n, (off, off), (off + 8, off + 23)


def qdir(phi, step=22.5):
    q = round(phi / step) * step
    return unit(q)


def perp_light(dx, dy):
    """빛 좌상단: 밝은 줄이 놓일 1px 오프셋."""
    if abs(dx) >= 2 * abs(dy):
        return (0, -1)
    if abs(dy) >= 2 * abs(dx):
        return (-1, 0)
    return (0, -1) if dx * dy < 0 else (-1, 0)


def draw_blade(cv, grip, phi, spec, col, tip_glow=False):
    dx, dy = qdir(phi)
    gx, gy = grip
    L = spec["length"]
    def at(t):
        return int(round(gx + dx * t)), int(round(gy + dy * t))
    px_, py_ = perp_light(dx, dy)
    # 손잡이·감개
    hx0, hy0 = at(-1)
    hx1, hy1 = at(-spec["hilt"])
    cv.line(hx0, hy0, hx1, hy1, col["dark"])
    for k in spec["wrap"]:
        x, y = at(-k)
        cv.px(x, y, col["wrap"])
    # 날밑
    for k in range(-spec["guard"], spec["guard"] + 1):
        cv.px(gx + px_ * k, gy + py_ * k, col["ink"])
    if spec["guard"] >= 2:
        cv.px(gx, gy, col["dark"])
    bx, by = at(1)
    tx, ty = at(L)
    if spec["width"] == 1:
        cv.line(bx, by, tx, ty, col["edge"])
    else:
        cv.line(bx, by, tx, ty, col["body"])
        cv.line(bx + px_, by + py_, tx + px_, ty + py_, col["edge"])
        if spec["width"] >= 3:
            cv.line(bx - px_, by - py_, tx - px_, ty - py_, col["dark"])
    cv.px(tx, ty, col["tip"])
    if spec["width"] >= 2:
        cv.px(tx + px_, ty + py_, col["tip"] if tip_glow else col["edge"])
    if tip_glow:
        ex, ey = at(L + 1)
        cv.px(ex, ey, col["glow"])
        cv.px(ex + px_, ey + py_, col["glow"])


def draw_weapon_state(cv, wid, grip, phi, state):
    spec = SPEC[wid]
    if state == "embers":
        dx, dy = qdir(phi)
        x, y = grip
        k = spec["length"] // 2
        mx, my = int(round(x + dx * k)), int(round(y + dy * k))
        cv.pair(mx - 2, my - 2, C(24))
        cv.pair(mx + 1, my - 4, C(22), horiz=False)
        cv.pair(mx + 3, my, C(24))
        cv.pair(x - 1, y + 1, C(22))
        return
    col = WP.GHOST if state in ("ghost", "fade") else WP.STEEL
    draw_blade(cv, grip, phi, spec, col, tip_glow=(state == "glow"))


# ============================================================ 4. 3연격 표 (θ, L, fwd, dip, crouch, 무기 상태) + ms + 판정 메모
# 상태: ghost = 실체화(호박 윤곽) / steel / glow = 휘두름 + 날끝 글로우(판정 프레임) / fade = 흩어지는 호박 윤곽 / embers = 불티만
COMBOS = {
    "katana": {   # "씽 · 씽씽" — 1타 뒤 쉼(취소 f3 = 250ms), 2·3타는 붙어서(취소 f2 = 80ms)
        # 49라운드: 1타 = 발도 베기. f0 = 허리 칼집 손잡이를 쥐고 낮게(칼은 칼집 안), f1 = 뽑으며 벰(판정), 칼집은 빈 채 허리에.
        1: dict(frames=[(None, 0, 0, 1, 1, "sheathed", {}), (-15, 5, 1, 0, 0, "glow", {}), (60, 5, 1, 1, 0, "steel", {}),
                        (95, 4, 0, 0, 0, "steel", {"pull": 0.6})],
                ms=[90, 40, 120, 100], hit=[1], cancel=3, arc=(-70, 70), r49=True),
        2: dict(frames=[(100, 5, 0, 0, 0, "steel"), (10, 5, 1, 0, 0, "glow"), (-85, 5, 0, 0, 0, "fade")],
                ms=[40, 40, 90], hit=[1], cancel=2, arc=(65, -65)),
        3: dict(frames=[(-125, 5, -1, 0, 0, "steel"), (-5, 5, 1, 0, 0, "glow"), (75, 5, 2, 1, 0, "steel"), (100, 4, 1, 1, 0, "embers")],
                ms=[40, 40, 100, 140], hit=[1], cancel=None, arc=(-85, 85)),
    },
    # 49라운드 Q4·Q5 재제작: 두 손 큰 휘두름. 프레임 = (θ, L, fwd, dip, crouch, 상태, opt). 무기는 이제 등에서 꺼내 든 실물(실체화 윤곽 없음).
    # 2단 예비(끌어올림 → 최대 비틀림, 무게 뒤) → 훙(판정, 무게 앞) → 끝까지 휘두름 → 버팀(회복) → 자세 회복. 판정 = f2.
    "greatsword": {   # "훙 훙 훙" — 1·3타 위→아래, 2타 아래→위(교차), 3타 270° 가장 큼
        1: dict(frames=[(-150, 4, -1, 0, 0, "steel", {}), (-172, 3, -1, 1, 1, "steel", {}), (-30, 5, 1, 0, 0, "glow", {}),
                        (60, 5, 2, 1, 1, "steel", {"pull": 0.5}), (95, 5, 1, 2, 1, "steel", {"pull": 0.7}), (110, 3, 0, 0, 0, "steel", {"pull": 0.7})],
                ms=[90, 100, 60, 110, 140, 130], hit=[2], cancel=4, recover=[4, 5], arc=(-110, 80)),
        2: dict(frames=[(110, 4, 0, 1, 1, "steel", {"pull": 0.6}), (165, 3, -1, 1, 1, "steel", {}), (30, 5, 1, 0, 0, "glow", {}),
                        (-80, 5, 1, -1, 0, "steel", {}), (-120, 4, 0, 0, 0, "steel", {}), (-140, 4, -1, 0, 0, "steel", {})],
                ms=[80, 90, 60, 110, 140, 120], hit=[2], cancel=4, recover=[4, 5], arc=(100, -100)),
        3: dict(frames=[(-120, 5, -1, -1, 0, "steel", {}), (-178, 3, -1, 1, 1, "steel", {}), (-60, 5, 1, 0, 0, "glow", {}),
                        (40, 5, 2, 1, 0, "glow", {"pull": 0.4}), (95, 5, 2, 2, 2, "steel", {"pull": 0.7}),
                        (100, 4, 1, 1, 1, "steel", {"pull": 0.7}), (110, 3, 0, 0, 0, "steel", {"pull": 0.7})],
                ms=[100, 120, 60, 70, 150, 160, 160], hit=[2], active=[2, 3], cancel=None, recover=[4, 5, 6], arc=(-150, 120)),
    },
    "dagger": {   # "슈슈슉" — 찌르기 3줄기(위로 8° · 아래로 10° · 정면 길게)
        1: dict(frames=[(-8, 1, -1, 0, 0, "ghost"), (-8, 6, 1, 0, 0, "glow"), (-8, 3, 0, 0, 0, "fade")],
                ms=[50, 40, 70], hit=[1], cancel=2, thrust=dict(angle=-8, length=24, width=8)),
        2: dict(frames=[(10, 1, 0, 0, 0, "steel"), (10, 6, 1, 0, 0, "glow"), (10, 3, 0, 0, 0, "fade")],
                ms=[40, 40, 70], hit=[1], cancel=2, thrust=dict(angle=10, length=24, width=8)),
        3: dict(frames=[(0, 0, -1, 1, 1, "steel"), (0, 7, 2, 0, 0, "glow"), (0, 7, 2, 0, 0, "steel"), (20, 3, 0, 0, 0, "embers")],
                ms=[60, 40, 70, 110], hit=[1], cancel=None, thrust=dict(angle=0, length=28, width=10)),
    },
}


def combo_memo(wid, n, for_fx=False):
    cb = COMBOS[wid][n]
    ms = cb["ms"]
    memo = {
        "weapon": wid,
        "comboIndex": n,
        "comboLength": 3,
        "nextCombo": ("%s_combo%d" % (wid, n + 1)) if n < 3 else None,
        "hitFrames": cb["hit"],
        "activeFrames": cb.get("active", cb["hit"]),
        "cancelFromFrame": cb["cancel"],
        "framesBasis": "player_%s_combo%d 프레임 번호 (무기·몸·이펙트 공통 기준 = 몸 시트)" % (wid, n),
        "timingMs": {"hitAt": sum(ms[:cb["hit"][0]]), "cancelAt": (sum(ms[:cb["cancel"]]) if cb["cancel"] is not None else None), "total": sum(ms)},
        "hitOrigin": "몸 중심 = 피벗(발)에서 위로 %dpx" % BODY_CENTER_DY,
        "hitNote": "임시(아트 메모). 기존 판정 먼 끝(리치 + 짧은 변/2) x1.5. 시스템 실제값이 다르면 시스템 값 우선 — 알려 주면 호 반경을 맞춰 재빌드",
    }
    if wid == "greatsword" or cb.get("r49"):
        memo["fxSpawnAtMs"] = sum(ms[:cb["hit"][0]]) - 40
    if "recover" in cb:
        memo["recoverFrames"] = cb["recover"]
        memo["recoverNote"] = ("임시(아트 제안): 휘두른 뒤 무게를 버티고 자세를 되찾는 프레임. 이동 제약·기력 소모 구간의 시각 기준 "
                               "(실제 이동 제약 시간은 시스템). 취소(cancelFromFrame)가 들어오면 생략된다.")
    if wid == "greatsword" or cb.get("r49"):
        memo["revision"] = "49라운드 재제작 (%s)" % ("두 손 큰 휘두름 + 몸 비틀림·무게 중심 이동·회복 프레임" if wid == "greatsword" else "발도 베기 — 허리 칼집에서 뽑으며 벰")
    if "arc" in cb:
        a0, a1 = cb["arc"]
        memo.update({"hitRadiusPx": HIT[wid], "arcDeg": abs(a1 - a0), "arcFromDeg": a0, "arcToDeg": a1,
                     "arcAngleNote": "right 방향 화면각(0 = 정면, + = 아래, from→to = 휘두름 방향). down = +90° 회전, up = -90°, left = 좌우 반전(180-θ)"})
    else:
        t = cb["thrust"]
        memo.update({"thrust": {"lengthPx": t["length"], "widthPx": t["width"], "angleDeg": t["angle"], "fromPx": 4},
                     "thrustNote": "몸 중심에서 정면(right 기준 angleDeg)으로 fromPx~lengthPx, 폭 widthPx 의 직사각 판정. 방향 변환은 호와 같은 규약"})
    return memo


# ============================================================ 5. 특수 동작 표 (방향별 화면 좌표: 손, 칼날 화면각 φ, 몸 파라미터, 상태)
# 항목: (hand(x,y), phi, dict(body), state)
def mirror_lr(rows):
    out = []
    for (hx_, hy_), phi, body, st in rows:
        out.append(((15 - hx_, hy_), 180 - phi, body, st))
    return out


KATANA_SPECIAL_R = [  # 패링: 준비 → 받아냄(창) → 버팀(창) → 되받아 튕김 → 내림
    ((12, 11), -60, dict(), "ghost"),
    ((12, 10), -90, dict(body_dx=-1, lean=-1), "steel"),
    ((11, 10), -100, dict(body_dx=-1, lean=-1, body_dy=1), "glow"),
    ((14, 12), 0, dict(body_dx=1, lean=1), "glow"),
    ((12, 15), 60, dict(lean=1), "fade"),
]
KATANA_SPECIAL = {
    "right": KATANA_SPECIAL_R,
    "left": mirror_lr(KATANA_SPECIAL_R),
    "down": [((11, 13), 190, dict(), "ghost"), ((12, 12), 200, dict(body_dy=-1), "steel"), ((12, 12), 205, dict(), "glow"),
             ((12, 17), 90, dict(body_dy=1), "glow"), ((13, 16), 60, dict(), "fade")],
    "up": [((4, 9), -10, dict(), "ghost"), ((3, 8), -15, dict(body_dy=1), "steel"), ((3, 9), -20, dict(body_dy=1), "glow"),
           ((4, 4), -90, dict(body_dy=-1), "glow"), ((2, 13), 120, dict(), "fade")],
}
GS_SPECIAL_R = [  # 가드: 세움 → 버팀(루프 1·2) → 밀쳐냄 → 뻗음 → 내림
    ((12, 12), -80, dict(l_dx=1, r_dx=-1), "ghost"),
    ((12, 13), -90, dict(l_dx=1, r_dx=-1, crouch=1), "steel"),
    ((12, 13), -90, dict(l_dx=1, r_dx=-1, crouch=1, body_dy=1), "steel"),
    ((13, 13), -80, dict(l_dx=2, r_dx=-1, body_dx=1, lean=1), "steel"),
    ((15, 13), -70, dict(l_dx=2, r_dx=-1, body_dx=1, lean=2), "glow"),
    ((12, 15), 70, dict(l_dx=1, r_dx=-1), "fade"),
]
GS_SPECIAL = {
    "right": GS_SPECIAL_R,
    "left": mirror_lr(GS_SPECIAL_R),
    # 정면: 칼을 허리 높이에 가로로 들어 벽처럼 (왼손은 날밑 쪽 x4 근처)
    "down": [((12, 13), 180, dict(), "ghost"), ((12, 14), 180, dict(crouch=1), "steel"), ((12, 14), 180, dict(crouch=1, body_dy=1), "steel"),
             ((12, 15), 180, dict(body_dy=1), "steel"), ((12, 17), 180, dict(body_dy=1), "glow"), ((13, 16), 110, dict(), "fade")],
    "up": [((3, 10), 0, dict(), "ghost"), ((3, 10), 0, dict(crouch=1), "steel"), ((3, 10), 0, dict(crouch=1, body_dy=1), "steel"),
           ((3, 8), 0, dict(body_dy=-1), "steel"), ((3, 6), 0, dict(body_dy=-1), "glow"), ((2, 13), 70, dict(), "fade")],
}
DG_SPECIAL_R = [  # 그림자 걸음: 웅크림(역수) → 돌입(사라짐 직전) → 착지(적 뒤) → 일어섬 → 확정 치명 자세
    ((10, 13), 150, dict(crouch=1), "ghost"),
    ((14, 14), 20, dict(crouch=1, body_dx=1, lean=2, l_dx=2, r_dx=-2, tail=3), "steel"),
    ((12, 15), -120, dict(crouch=2, body_dy=1, l_dx=1, r_dx=-1), "steel"),
    ((12, 12), -150, dict(crouch=1, l_dx=1, r_dx=-1), "steel"),
    ((13, 11), -30, dict(), "glow"),
]
DG_SPECIAL = {
    "right": DG_SPECIAL_R,
    "left": mirror_lr(DG_SPECIAL_R),
    "down": [((12, 14), -70, dict(crouch=1), "ghost"), ((11, 17), 90, dict(crouch=1, l_lift=1), "steel"),
             ((12, 16), -60, dict(crouch=2, body_dy=1), "steel"), ((12, 14), -80, dict(crouch=1), "steel"), ((13, 12), 60, dict(), "glow")],
    "up": [((3, 12), 110, dict(crouch=1), "ghost"), ((4, 6), -90, dict(crouch=1, r_lift=1), "steel"),
           ((3, 13), 120, dict(crouch=2, body_dy=1), "steel"), ((3, 11), 100, dict(crouch=1), "steel"), ((2, 9), -120, dict(), "glow")],
}
SPECIALS = {
    "katana": dict(rows=KATANA_SPECIAL, ms=[50, 90, 120, 70, 110], loop=False, kind="parry",
                   memo={"secondaryAction": "parry (우클릭 패링)",
                         "phases": {"ready": [0], "window": [1, 2], "riposte": [3], "recover": [4]},
                         "holdFrame": 2, "holdNote": "패링 창이 프레임 합보다 길면 f2 유지. 성공 = f3·f4, 실패(창 종료) = f4",
                         "overlayFx": [{"id": "parry_flash", "spawn": "parry_success", "atFrame": 3, "anchor": "hitbox_center (접점)"}]}),
    "greatsword": dict(rows=GS_SPECIAL, ms=[80, 160, 160, 60, 90, 130], loop=False, kind="guard",
                       memo={"secondaryAction": "guard (우클릭 가드 · 떼면 밀쳐내기)",
                             "phases": {"enter": [0], "hold": [1, 2], "release": [3, 4], "recover": [5]},
                             "loopFrames": [1, 2], "loopNote": "누르는 동안 f1↔f2 반복(160ms씩). 떼는 순간 f3 부터",
                             "overlayFx": [{"id": "guard_wave", "spawn": "guard_release", "atFrame": 4, "anchor": "player_pivot"},
                                           {"id": "ironwall", "spawn": "guard_release", "atFrame": 4, "note": "철벽 노드일 때"}]}),
    "dagger": dict(rows=DG_SPECIAL, ms=[50, 60, 70, 80, 140], loop=False, kind="shadowstep",
                   memo={"secondaryAction": "shadowstep (우클릭 그림자 걸음 · 분신 돌입)",
                         "phases": {"depart": [0, 1], "arrive": [2, 3], "primed": [4]},
                         "teleportAfterFrame": 1, "teleportNote": "f1 끝에 순간이동, f2 부터 착지 위치(적 뒤)·적을 향한 방향으로 재생",
                         "holdFrame": 4, "holdNote": "확정 치명 유효 시간(primeMs) 동안 f4 유지 가능",
                         "overlayFx": [{"id": "shadowstep_ghost", "spawn": "shadowstep_start", "atFrame": 2, "anchor": "player_pivot (출발점 고정)"},
                                       {"id": "afterimage", "spawn": "dash_start", "note": "잔상 노드 대쉬 때도 이 시트 f0~f1 을 돌입 자세로 쓸 수 있음"}]}),
}


def special_pose(wid, d, row):
    (hx_, hy_), phi, body, state = row
    p = P.Pose(**body)
    extra = []
    if d in ("left", "right"):
        p.r_arm = "pos"
    else:
        if d == "down":
            p.r_arm = "pos"
        else:
            p.l_arm = "pos"
        if wid == "greatsword":
            # 가로로 든 대검: 두 번째 손은 날밑에서 칼날 쪽 4px (몸 반대편 어깨에서)
            dx, dy = qdir(phi)
            g2 = clamp_hand(hx_ + dx * 4, hy_ + dy * 4) if abs(dx) > 0.5 else (hx_, hy_)
            other = "l" if d == "down" else "r"
            sx, sy = shoulder(d, p, other)
            extra.append((sx, sy, g2[0], g2[1]))
    p.hand_pos = (hx_, hy_)
    return p, (hx_, hy_), phi, state, extra


# 활 조준: 방향별 활 중심(주인공 좌표, weapons/build.py BOW_POS)과 당김(0..5px)
BOW_POS = WP.BOW_POS
BOW_DRAW = [0, 1, 2, 3, 4, 5, 0]
BOW_MS = [100, 100, 100, 100, 100, 120, 80]


def bow_geom(d, draw):
    """(앞팔 손 = 활 잡이, 시위 손 = 깃 위치) 주인공 좌표."""
    cx, cy = BOW_POS[d]
    if d == "right":
        return (cx - 1, cy), (cx - 1 - draw, cy)
    if d == "left":
        return (cx + 1, cy), (cx + 1 + draw, cy)
    if d == "down":
        return (cx + 1, cy - 1), (cx, cy - 1 - draw)
    return (cx - 1, cy + 1), (cx, cy + 1 + draw)


def bow_pose(d, f):
    draw = BOW_DRAW[f]
    grip, nock = bow_geom(d, draw)
    p = P.Pose()
    extra = []
    if f == 6:   # 발사: 시위 손이 뒤로 튐
        nock = {"right": (nock[0] - 2, nock[1] - 1), "left": (nock[0] + 2, nock[1] - 1),
                "down": (nock[0] + 2, max(1, nock[1] - 2)), "up": (nock[0] + 2, nock[1] + 2)}[d]
    nock = clamp_hand(*nock)
    grip = clamp_hand(*grip)
    if d in ("left", "right"):
        p.r_arm = "pos"
        p.hand_pos = grip
        m = 1 if d == "right" else -1
        sx = (9 if m > 0 else 6) - m           # 먼 어깨(뒤쪽) 에서 시위 손
        extra.append((sx, 10, nock[0], nock[1]))
        p.lean = 0 if draw < 3 else -1
    else:
        if d == "down":
            p.r_arm = "pos"
            p.hand_pos = grip
            extra.append((4, 10, nock[0], nock[1]))
        else:
            p.l_arm = "pos"
            p.hand_pos = grip
            extra.append((11, 10, nock[0], min(22, nock[1])))
    return p, extra


def draw_bow_aim(cv, d, f, poff):
    """weapons/build.py draw_bow 의 기하를 진행도(당김 0..5)로 확장. f0 화살 = 실체화(호박), f5 완료 글린트, f6 발사."""
    col = WP.STEEL
    cx, cy = BOW_POS[d]
    cx += poff[0]
    cy += poff[1]
    M = WP.bow_map(d, cx, cy)
    for a, b in enumerate(WP.BOW_BULGE):
        x, y = M(a, b)
        cv.px(x, y, col["dark"] if 5 <= a <= 7 else col["edge"])
        if 1 <= a <= 11:
            x2, y2 = M(a, b - 1)
            cv.px(x2, y2, col["dark"] if 5 <= a <= 7 else col["body"])
    x0, y0 = M(0, -1)
    x1, y1 = M(12, -1)
    if f == 6:
        cv.line(x0, y0, x1, y1, col["edge"])
        for a in (5, 6):
            x, y = M(a, -2)
            cv.px(x, y, C(25))
        for c_ in (8, 9):
            x, y = M(6, c_)
            cv.px(x, y, C(24))
        return
    draw = BOW_DRAW[f]
    nx, ny = M(6, -1 - draw)
    s_col = col["edge"]
    cv.line(x0, y0, nx, ny, s_col)
    cv.line(nx, ny, x1, y1, s_col)
    # 화살: 깃(시위) → 촉. 촉은 활 앞 +6 (당김과 무관하게 같은 자리 — 화살이 뒤로 끌려온다)
    ghost = f == 0
    shaft = C(24) if ghost else G(13)
    ax0, ay0 = M(6, -1 - draw + 1)
    ax1, ay1 = M(6, 5)
    cv.line(ax0, ay0, ax1, ay1, shaft)
    tx, ty = M(6, 6)
    cv.px(tx, ty, C(25) if ghost else C(27))
    for a in (5, 7):
        x, y = M(a, -1 - draw + 1)
        cv.px(x, y, C(19) if ghost else C(21))
    if f == 5:   # 완료: 촉 앞 글린트 2px + 시위 손 끝 불티
        for c_ in (7, 8):
            x, y = M(6, c_)
            cv.px(x, y, C(25))
        for a in (5, 7):
            x, y = M(a, 7)
            cv.px(x, y, C(27))


# ============================================================ 6. 이펙트 (right 기준 그림 → 4방향 회전·반전)
def crescent(cv, c, a0, a1, t0, t1, r, tk, wid, mode="normal", head=0.7):
    Wd = [W(wid, i) for i in range(4)]
    if t1 <= t0:
        return
    if mode == "hot":
        cv.arc(c, c, a0, a1, t0, t1, r, tk, [Wd[0], Wd[3], X1, X0, X1, Wd[3]], head=head, head_boost=0)
        return
    if mode == "cool":
        cv.arc(c, c, a0, a1, t0, t1, r, tk, [Wd[0], Wd[1], Wd[2], Wd[1]], head=2, min_t=1.0)
        return
    cv.arc(c, c, a0, a1, t0, t1, r, tk, [Wd[0], Wd[1], Wd[2], Wd[3], Wd[2], Wd[1]], head=head, head_boost=0)
    core = [X1, X0] if mode == "normal" else [Wd[3], X1]
    cv.arc(c, c, a0, a1, t0 + 0.04, t1 - 0.02, r + 0.5, 1.0, core, head=head, head_boost=1, min_t=1.0, taper=0.0)


def ghost_band(cv, c, a0, a1, t0, t1, r, tk, wid, cols=None):
    if t1 > t0:
        cv.arc(c, c, a0, a1, t0, t1, r, tk, cols or [W(wid, 0), W(wid, 1), W(wid, 2)], head=2, min_t=1.0)


def pre_line(cv, c, a0, a1, t1, r, wid, tk=1.6):
    cv.arc(c, c, a0, a1, 0.0, t1, r, tk, [W(wid, 1), X1], head=0.3, min_t=1.0)
    K.head_glint(cv, c, c, a0, a1, t1, r + 1, C(27))


def at_arc(c, a0, a1, t, r):
    a = math.radians(a0 + (a1 - a0) * t)
    return c + r * math.cos(a), c + r * math.sin(a)


def sparks(cv, pts, cols):
    for k, (x, y) in enumerate(pts):
        cv.pair(x, y, cols[k % len(cols)], horiz=(k % 2 == 0))


def katana_fx(n):
    wid, S = "katana", 96
    c = (S - 1) / 2.0
    a0, a1 = COMBOS[wid][n]["arc"]
    R = HIT[wid]
    fr = []
    if n in (1, 2):
        tk = 6.0 if n == 1 else 5.0
        r = R - tk / 2
        gr = r - 6
        cv = K.Canvas(S, S); pre_line(cv, c, a0, a1, 0.4 if n == 1 else 0.45, r, wid); fr.append(cv)
        cv = K.Canvas(S, S)
        ghost_band(cv, c, a0, a1, 0.0, 0.45, gr, 3.0, wid)
        crescent(cv, c, a0, a1, 0.0, 1.0, r, tk, wid, "normal", head=0.65)
        K.head_glint(cv, c, c, a0, a1, 0.97, r + 1, C(27))
        fr.append(cv)
        cv = K.Canvas(S, S)
        ghost_band(cv, c, a0, a1, 0.0, 1.0, gr, 3.0, wid)
        crescent(cv, c, a0, a1, 0.1 if n == 1 else 0.2, 1.0, r, tk * 0.9, wid, "warm", head=0.8)
        K.spill_rays(cv, c, c, a0, a1, 0.98, r, wid, n=2, length=5 if n == 1 else 4, seed=3 + n, cols=[(1, W(wid, 0)), (0, C(27))])
        fr.append(cv)
        if n == 1:
            cv = K.Canvas(S, S)
            ghost_band(cv, c, a0, a1, 0.15, 1.0, gr, 2.0, wid, [W(wid, 0), W(wid, 1)])
            crescent(cv, c, a0, a1, 0.3, 1.0, r, tk * 0.6, wid, "cool")
            x, y = at_arc(c, a0, a1, 0.92, r + 3)
            cv.pair(x, y, C(24))
            fr.append(cv)
        cv = K.Canvas(S, S)
        K.remnant(cv, c, c, a0, a1, 0.45, 1.0, r, wid, mod=4, keep=(0, 1, 2))
        K.remnant(cv, c, c, a0, a1, 0.3, 0.95, gr, wid, mod=5, keep=(0, 1), seed=2, cols=[W(wid, 0), W(wid, 0)])
        x, y = at_arc(c, a0, a1, 0.85, r + 2); cv.pair(x, y, C(22), horiz=False)
        x, y = at_arc(c, a0, a1, 0.6, r - 3); cv.pair(x, y, C(22))
        fr.append(cv)
        ms = [40, 50, 60, 70, 90] if n == 1 else [40, 40, 50, 80]
    else:
        tk = 7.0
        r = R - tk / 2
        g1, g2 = r - 6, r - 10
        cv = K.Canvas(S, S); pre_line(cv, c, a0, a1, 0.4, r, wid, tk=2.0); fr.append(cv)
        cv = K.Canvas(S, S)   # f1 섬광: 몸체 전체 백열
        ghost_band(cv, c, a0, a1, 0.0, 0.5, g1, 3.0, wid)
        crescent(cv, c, a0, a1, 0.0, 1.0, r, tk, wid, "hot", head=0.6)
        K.head_glint(cv, c, c, a0, a1, 0.97, r + 1, C(27))
        K.head_glint(cv, c, c, a0, a1, 0.55, r + 3, C(27), horiz=False)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 본 띠 + 바깥/안쪽 겹 + 광선 3
        ghost_band(cv, c, a0, a1, 0.0, 0.55, g2, 2.4, wid, [W(wid, 0), W(wid, 1)])
        ghost_band(cv, c, a0, a1, 0.0, 1.0, g1, 3.0, wid)
        crescent(cv, c, a0, a1, 0.05, 1.0, r, tk, wid, "normal", head=0.75)
        K.spill_rays(cv, c, c, a0, a1, 0.98, r, wid, n=3, length=6, seed=11, cols=[(1, W(wid, 0)), (0, X0)])
        fr.append(cv)
        cv = K.Canvas(S, S)   # f3 식음
        ghost_band(cv, c, a0, a1, 0.0, 1.0, g2, 2.4, wid, [W(wid, 0), W(wid, 1)])
        ghost_band(cv, c, a0, a1, 0.1, 1.0, g1, 2.4, wid, [W(wid, 0), W(wid, 1)])
        crescent(cv, c, a0, a1, 0.2, 1.0, r, tk * 0.8, wid, "warm", head=0.85)
        x, y = at_arc(c, a0, a1, 0.9, r + 3); cv.pair(x, y, C(24))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f4 어두운 띠
        crescent(cv, c, a0, a1, 0.4, 1.0, r, tk * 0.5, wid, "cool")
        K.remnant(cv, c, c, a0, a1, 0.2, 1.0, g1, wid, mod=4, keep=(0, 1, 2), seed=1)
        x, y = at_arc(c, a0, a1, 0.8, r + 3); cv.pair(x, y, C(24), horiz=False)
        x, y = at_arc(c, a0, a1, 0.55, r + 1); cv.pair(x, y, C(22))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f5 꼬리
        K.remnant(cv, c, c, a0, a1, 0.55, 1.0, r, wid, mod=4, keep=(0, 1))
        K.remnant(cv, c, c, a0, a1, 0.4, 0.95, g1, wid, mod=5, keep=(0, 1), seed=2, cols=[W(wid, 0), W(wid, 0)])
        x, y = at_arc(c, a0, a1, 0.95, r + 4); cv.pair(x, y, C(22))
        fr.append(cv)
        ms = [40, 40, 60, 80, 100, 120]
    for cv in fr:
        cv.despeckle8()
    return K.four_dirs_from_right(fr), ms, S


def crack(cv, x0, y0, ang, L, cols, seed):
    a = math.radians(ang)
    pts = K.zigzag(x0, y0, x0 + L * math.cos(a), y0 + L * math.sin(a) * 0.7, 3, 1.6, seed)
    cv.bolt(pts, cols)


def greatsword_fx(n):
    wid, S = "greatsword", 128
    c = (S - 1) / 2.0
    a0, a1 = COMBOS[wid][n]["arc"]
    R = HIT[wid]
    fr = []
    ASH = [G(6), G(9)]
    if n in (1, 2):
        tk = 10.0
        r = R - tk / 2
        gr = r - 8
        cv = K.Canvas(S, S); pre_line(cv, c, a0, a1, 0.35, r, wid, tk=2.2); fr.append(cv)
        cv = K.Canvas(S, S)
        ghost_band(cv, c, a0, a1, 0.0, 0.4, gr, 4.0, wid)
        crescent(cv, c, a0, a1, 0.0, 1.0, r, tk, wid, "normal", head=0.65)
        K.head_glint(cv, c, c, a0, a1, 0.97, r + 2, C(27))
        fr.append(cv)
        cv = K.Canvas(S, S)
        ghost_band(cv, c, a0, a1, 0.0, 1.0, gr, 4.0, wid)
        crescent(cv, c, a0, a1, 0.1, 1.0, r, tk * 0.9, wid, "warm", head=0.8)
        K.spill_rays(cv, c, c, a0, a1, 0.98, r, wid, n=2, length=6, seed=5 + n, cols=[(1, W(wid, 0)), (0, C(27))])
        pts = [at_arc(c, a0, a1, t, r + rr) for t, rr in ((0.9, 6), (0.75, 7), (0.6, 6))]
        sparks(cv, pts, [C(27), C(24), W(wid, 3)])
        fr.append(cv)
        cv = K.Canvas(S, S)
        ghost_band(cv, c, a0, a1, 0.15, 1.0, gr, 3.0, wid, [W(wid, 0), W(wid, 1)])
        crescent(cv, c, a0, a1, 0.3, 1.0, r, tk * 0.6, wid, "cool")
        pts = [at_arc(c, a0, a1, t, r + rr) for t, rr in ((0.95, 8), (0.8, 9), (0.65, 8), (0.5, 7))]
        sparks(cv, pts, [C(24), W(wid, 2), G(9), C(24)])
        fr.append(cv)
        cv = K.Canvas(S, S)
        K.remnant(cv, c, c, a0, a1, 0.45, 1.0, r, wid, mod=4, keep=(0, 1, 2))
        K.remnant(cv, c, c, a0, a1, 0.3, 0.95, gr, wid, mod=5, keep=(0, 1), seed=2, cols=[W(wid, 0), W(wid, 0)])
        pts = [at_arc(c, a0, a1, t, r + rr) for t, rr in ((0.98, 10), (0.85, 11), (0.7, 10))]
        sparks(cv, pts, [G(6), C(24), G(9)])
        fr.append(cv)
        cv = K.Canvas(S, S)
        K.remnant(cv, c, c, a0, a1, 0.65, 1.0, r, wid, mod=5, keep=(0, 1), seed=1, cols=[W(wid, 0), W(wid, 0)])
        pts = [at_arc(c, a0, a1, t, r + rr) for t, rr in ((0.9, 12), (0.75, 13))]
        sparks(cv, pts, ASH)
        fr.append(cv)
        ms = [40, 60, 70, 80, 100, 120]
    else:
        tk = 12.0
        r = R - tk / 2
        g1, g2 = r - 9, r - 15
        imp = at_arc(c, a0, a1, (75 - a0) / float(a1 - a0), r - 2)   # 앞-아래(75°) 바닥을 긁는 지점
        cv = K.Canvas(S, S); pre_line(cv, c, a0, a1, 0.3, r, wid, tk=2.4); fr.append(cv)
        cv = K.Canvas(S, S)   # f1 섬광
        ghost_band(cv, c, a0, a1, 0.0, 0.45, g1, 4.0, wid)
        crescent(cv, c, a0, a1, 0.0, 1.0, r, tk, wid, "hot", head=0.6)
        K.head_glint(cv, c, c, a0, a1, 0.98, r + 2, C(27))
        K.head_glint(cv, c, c, a0, a1, 0.5, r + 5, C(27), horiz=False)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 3겹 + 광선 3 + 바닥 균열
        ghost_band(cv, c, a0, a1, 0.0, 0.5, g2, 3.0, wid, [W(wid, 0), W(wid, 1)])
        ghost_band(cv, c, a0, a1, 0.0, 1.0, g1, 4.0, wid)
        crescent(cv, c, a0, a1, 0.05, 1.0, r, tk, wid, "normal", head=0.75)
        K.spill_rays(cv, c, c, a0, a1, 0.98, r, wid, n=3, length=8, seed=21, cols=[(1, W(wid, 0)), (0, X0)])
        for k, (ang, L) in enumerate(((40, 12), (95, 10), (150, 9))):
            crack(cv, imp[0], imp[1] + 3, ang, L, [(1, W(wid, 0)), (0, W(wid, 2))], 40 + k)
        sparks(cv, [(imp[0] + 9, imp[1] - 3), (imp[0] - 8, imp[1] + 1), (imp[0] + 3, imp[1] + 12)], [C(27), W(wid, 3), C(24)])
        fr.append(cv)
        cv = K.Canvas(S, S)   # f3 식음 + 균열 식음 + 재
        ghost_band(cv, c, a0, a1, 0.0, 1.0, g2, 3.0, wid, [W(wid, 0), W(wid, 1)])
        ghost_band(cv, c, a0, a1, 0.1, 1.0, g1, 3.0, wid, [W(wid, 0), W(wid, 1)])
        crescent(cv, c, a0, a1, 0.2, 1.0, r, tk * 0.8, wid, "warm", head=0.85)
        for k, (ang, L) in enumerate(((40, 12), (95, 10), (150, 9))):
            crack(cv, imp[0], imp[1] + 3, ang, L, [(1, W(wid, 0)), (0, W(wid, 1))], 40 + k)
        sparks(cv, [(imp[0] + 12, imp[1] - 6), (imp[0] - 11, imp[1] - 2), (imp[0] + 5, imp[1] + 15), (imp[0] - 4, imp[1] - 9)],
               [C(24), G(9), W(wid, 2), G(6)])
        fr.append(cv)
        cv = K.Canvas(S, S)   # f4 어두운 띠
        crescent(cv, c, a0, a1, 0.35, 1.0, r, tk * 0.5, wid, "cool")
        K.remnant(cv, c, c, a0, a1, 0.15, 1.0, g1, wid, mod=4, keep=(0, 1, 2), seed=1)
        for k, (ang, L) in enumerate(((40, 12), (95, 10), (150, 9))):
            crack(cv, imp[0], imp[1] + 3, ang, L, [(0, W(wid, 0))], 40 + k)
        sparks(cv, [(imp[0] + 14, imp[1] - 9), (imp[0] - 13, imp[1] - 5), (imp[0] + 2, imp[1] - 12)], [G(9), G(6), C(24)])
        fr.append(cv)
        cv = K.Canvas(S, S)   # f5 꼬리
        K.remnant(cv, c, c, a0, a1, 0.5, 1.0, r, wid, mod=4, keep=(0, 1, 2))
        K.remnant(cv, c, c, a0, a1, 0.3, 0.95, g1, wid, mod=5, keep=(0, 1), seed=2, cols=[W(wid, 0), W(wid, 0)])
        sparks(cv, [(imp[0] + 15, imp[1] - 12), (imp[0] - 14, imp[1] - 8)], ASH)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f6 남은 재
        K.remnant(cv, c, c, a0, a1, 0.7, 1.0, r, wid, mod=5, keep=(0, 1), seed=3, cols=[W(wid, 0), W(wid, 0)])
        sparks(cv, [(imp[0] + 16, imp[1] - 15), (imp[0] - 15, imp[1] - 11)], ASH)
        fr.append(cv)
        ms = [40, 50, 70, 90, 110, 130, 160]
    for cv in fr:
        cv.despeckle8()
    return K.four_dirs_from_right(fr), ms, S


def spindle(cv, c, ang, s0, s1, wmax, cols, t_from=0.0, t_to=1.0, poff=0.0, core=None, core_from=0.55):
    """찌르기 줄기: 몸 중심에서 ang 방향 s0→s1, 뒤는 가늘고 앞 70% 에서 가장 굵다가 촉으로 뾰족. cols 바깥→안쪽."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for y in range(cv.h):
        for x in range(cv.w):
            dx, dy = x - c, y - c
            s = dx * ca + dy * sa
            p = -dx * sa + dy * ca - poff
            u = (s - s0) / float(s1 - s0)
            if u < t_from or u > t_to:
                continue
            hw = (wmax / 2.0) * ((u / 0.7) ** 0.6 if u < 0.7 else ((1 - u) / 0.3) ** 0.8)
            hw = max(hw, 0.55)
            if abs(p) > hw:
                continue
            k = abs(p) / hw
            col = cols[max(0, min(len(cols) - 1, int((1 - k) * len(cols))))]
            if core is not None and abs(p) < 0.5:
                col = core[1] if u >= core_from else core[0]
            cv.px(x, y, col)


def merge(cv, tmp):
    for y in range(cv.h):
        for x in range(cv.w):
            if tmp.p[x, y][3]:
                cv.px(x, y, tmp.p[x, y])


def dash_out(cv, mod=4, keep=(0, 1, 2), seed=0):
    cv.dash_pattern(mod=mod, keep=keep, seed=seed)


def tip_point(c, ang, s):
    a = math.radians(ang)
    return c + s * math.cos(a), c + s * math.sin(a)


def dagger_fx(n):
    wid, S = "dagger", 64
    c = (S - 1) / 2.0
    t = COMBOS[wid][n]["thrust"]
    ang, s1 = t["angle"], t["length"]
    s0 = 7
    Wd = [W(wid, i) for i in range(4)]
    NORMAL = [Wd[0], Wd[1], Wd[2], Wd[3]]
    HOT = [Wd[0], Wd[3], X1]
    COOL = [Wd[0], Wd[1], Wd[2]]
    SHADOW = [Wd[0], Wd[1]]
    side = 1 if ang <= 0 else -1          # 그림자 줄기가 놓이는 쪽(위로 찌르면 아래에)
    fr = []
    tipx, tipy = tip_point(c, ang, s1 + 1)
    if n in (1, 2):
        wmax = 7.0
        cv = K.Canvas(S, S)   # f0 예비: 가는 코어 줄 앞 45%
        spindle(cv, c, ang, s0, s1, 2.0, [Wd[2], X1], t_to=0.45)
        x, y = tip_point(c, ang, s0 + 0.45 * (s1 - s0) + 1); cv.pair(x, y, C(27))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f1 본 줄기 + 코어 + 촉 글린트
        spindle(cv, c, ang, s0 + 1, s1 - 2, 4.0, SHADOW, poff=4.5 * side, t_to=0.5)
        spindle(cv, c, ang, s0, s1, wmax, NORMAL, core=[X1, X0])
        cv.pair(tipx, tipy, C(27), horiz=abs(ang) < 45)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 앞쪽만 남아 식음 + 그림자 줄기 + 촉 광선 2
        spindle(cv, c, ang, s0 + 1, s1 - 2, 4.0, SHADOW, poff=4.5 * side)
        spindle(cv, c, ang, s0, s1, wmax * 0.9, NORMAL, t_from=0.3, core=[Wd[3], X1])
        K.spill_rays(cv, c, c, ang, ang, 0.0, s1, wid, n=2, length=4, seed=7 + n, cols=[(1, Wd[0]), (0, C(27))])
        fr.append(cv)
        cv = K.Canvas(S, S)   # f3 꼬리 점선 + 불티
        spindle(cv, c, ang, s0, s1, 3.0, SHADOW, t_from=0.35)
        dash_out(cv, mod=4, keep=(0, 1, 2), seed=n)
        tmp = K.Canvas(S, S)
        spindle(tmp, c, ang, s0 + 1, s1 - 3, 2.6, [Wd[0]], poff=4.5 * side, t_from=0.3)
        tmp.dash_pattern(mod=5, keep=(0, 1), seed=2)
        merge(cv, tmp)
        x, y = tip_point(c, ang + 12 * side, s1 + 2); cv.pair(x, y, C(24))
        fr.append(cv)
        ms = [40, 40, 50, 70]
    else:
        wmax = 8.5
        cv = K.Canvas(S, S)   # f0 예비: 더 긴 코어 줄
        spindle(cv, c, ang, s0, s1, 2.2, [Wd[2], X1], t_to=0.5)
        x, y = tip_point(c, ang, s0 + 0.5 * (s1 - s0) + 1); cv.pair(x, y, C(27))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f1 섬광: 몸체 백열
        spindle(cv, c, ang, s0, s1, wmax, HOT)
        cv.pair(tipx, tipy, C(27))
        x, y = tip_point(c, ang, s1 + 3); cv.pair(x, y, C(27))
        fr.append(cv)
        cv = K.Canvas(S, S)   # f2 본 줄기 + 부채꼴 그림자 줄기 둘(±9°) = '슈슈슉' 세 줄
        for da in (-9, 9):
            spindle(cv, c, ang + da, s0 + 2, s1 - 3, 4.0, SHADOW)
        spindle(cv, c, ang, s0, s1, wmax, NORMAL, core=[X1, X0])
        K.spill_rays(cv, c, c, ang, ang, 0.0, s1, wid, n=3, length=5, seed=31, cols=[(1, Wd[0]), (0, X0)])
        fr.append(cv)
        cv = K.Canvas(S, S)   # f3 식음
        for da in (-9, 9):
            spindle(cv, c, ang + da, s0 + 3, s1 - 4, 2.4, [Wd[0]], t_from=0.3)
        spindle(cv, c, ang, s0, s1, wmax * 0.8, COOL, t_from=0.25)
        x, y = tip_point(c, ang - 20, s1 + 2); cv.pair(x, y, C(24))
        x, y = tip_point(c, ang + 22, s1); cv.pair(x, y, C(22), horiz=False)
        fr.append(cv)
        cv = K.Canvas(S, S)   # f4 꼬리
        spindle(cv, c, ang, s0, s1, 3.0, SHADOW, t_from=0.4)
        dash_out(cv, mod=4, keep=(0, 1, 2), seed=3)
        tmp = K.Canvas(S, S)
        for da in (-9, 9):
            spindle(tmp, c, ang + da, s0 + 3, s1 - 4, 2.0, [Wd[0]], t_from=0.45)
        tmp.dash_pattern(mod=5, keep=(0, 1), seed=1)
        merge(cv, tmp)
        x, y = tip_point(c, ang + 15, s1 + 3); cv.pair(x, y, C(22))
        fr.append(cv)
        ms = [40, 40, 50, 60, 90]
    for cv in fr:
        cv.despeckle8()
    return K.four_dirs_from_right(fr), ms, S


FX_BUILDERS = {"katana": katana_fx, "greatsword": greatsword_fx, "dagger": dagger_fx}


# ============================================================ 7. 저장 · 검사
def save_png_json(folder, name, frames_by_dir, w, h, durations, loop, pivot, palette_note, extra, action):
    n = len(durations)
    sheet = Image.new("RGBA", (w * n, h * len(DIRS)), (0, 0, 0, 0))
    for r, d in enumerate(DIRS):
        assert len(frames_by_dir[d]) == n, (name, d)
        for c_, im in enumerate(frames_by_dir[d]):
            im = im if isinstance(im, Image.Image) else im.im
            assert im.size == (w, h), (name, im.size)
            sheet.alpha_composite(im, (c_ * w, r * h))
    sheet.save(os.path.join(folder, name + ".png"))
    meta = {
        "image": name + ".png",
        "action": action,
        "frameWidth": w, "frameHeight": h,
        "frames": n,
        "directions": DIRS,
        "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column",
        "fps": round(1000.0 / (sum(durations) / n)),
        "frameDurationsMs": durations,
        "loop": loop,
        "pivot": {"x": pivot[0], "y": pivot[1]},
        "palette": palette_note,
        "source": SRC,
    }
    meta.update(extra)
    with open(os.path.join(folder, name + ".json"), "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    return sheet


GS_ = [G(i)[:3] for i in range(16)]
CS_ = [C(i)[:3] for i in range(16, 28)]
XS_ = [X0[:3], X1[:3]]
WS_ = {wid: [W(wid, i)[:3] for i in range(4)] for wid in K.FX["weapons"]}
PLAYER_OK = set(tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in P.PALETTE) | {G(4)[:3], (0xeb, 0xec, 0xed)}
REPORT = []


def isolated(im):
    px = im.load()
    n = 0
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][3]:
                if not any(0 <= x + dx < im.width and 0 <= y + dy < im.height and px[x + dx, y + dy][3]
                           for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)):
                    n += 1
    return n


def check(name, kind, frames_by_dir, wid=None):
    cols = set()
    semi = iso = 0
    for d in frames_by_dir:
        for im in frames_by_dir[d]:
            im = im if isinstance(im, Image.Image) else im.im
            iso += isolated(im)
            for px in (im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()):
                if px[3] == 255:
                    cols.add(px[:3])
                elif px[3]:
                    semi += 1
    if kind == "fx":
        grays = sorted(GS_.index(c) for c in cols if c in GS_ and c not in XS_)
        core = sorted(XS_.index(c) for c in cols if c in XS_)
    else:   # 캐릭터·무기: 순백은 G15(글린트)로 센다
        grays = sorted(GS_.index(c) for c in cols if c in GS_)
        core = sorted(XS_.index(c) for c in cols if c in XS_ and c not in GS_)
    acc = sorted(16 + CS_.index(c) for c in cols if c in CS_)
    sec = {}
    other = []
    for c in cols:
        if c in GS_ or c in CS_ or c in XS_:
            continue
        hit = [(k, v.index(c)) for k, v in WS_.items() if c in v]
        if hit:
            sec.setdefault(hit[0][0], []).append(hit[0][1])
        else:
            other.append(c)
    bad = bool(semi or other)
    if kind == "player":
        bad = bad or not cols <= PLAYER_OK or len(grays) > 11 or len(acc) > 2 or sec or core
        # 1px 사선 팔(셀아웃 후 남는 손 1px)은 리그와 같은 규칙 — 고립 검사는 정보로만
    elif kind == "weapon":
        bad = bad or not set(grays) <= {0, 5, 8, 13} or len(acc) > 7 or sec or core or iso
    else:
        total = len(grays) + len(acc) + len(core) + sum(len(v) for v in sec.values())
        bad = bad or len(grays) > 2 or len(acc) > 3 or len(sec) != 1 or (wid not in sec) or total > 11 or iso
    tot = len(grays) + len(acc) + len(core) + sum(len(v) for v in sec.values())
    line = "%-26s %-6s gray%s acc%s core%s sec%s total=%d iso=%d semi=%d other=%d %s" % (
        name, kind, grays, acc, core, {k: sorted(v) for k, v in sec.items()}, tot, iso, semi, len(other), "<-- CHECK" if bad else "OK")
    print(line)
    REPORT.append((name, not bad, line))
    return not bad


# ============================================================ 8. 빌드
def build_combo(wid, n):
    cb = COMBOS[wid][n]
    ms = cb["ms"]
    S, poff, wpivot = wcanvas(wid)
    r49 = wid == "greatsword" or cb.get("r49")
    if r49:
        bodies, weapons, depth = r49_combo_frames(wid, n)
        wextra = dict(depthByFrame={d: [depth[d]] * len(ms) for d in DIRS}, occlusionBaked=True,
                      depthNote="몸 뒤로 가는 날·칼집은 그 프레임 몸 실루엣으로 이미 지워 두었다(49라운드). 방향 안에서 프레임마다 같다.",
                      stateNote="sheathed 칼집 안(손잡이를 쥠) · steel 실물 · glow 판정 프레임(날끝 글로우). 49라운드부터 무기는 휴대 실물이라 실체화·흩어짐 없음")
    else:
        bodies, weapons, hands = {}, {}, {}
        for d in DIRS:
            bodies[d], weapons[d], hands[d] = [], [], []
            for fr in cb["frames"]:
                p, hand, phi, state = combo_pose(wid, d, fr, n)
                bodies[d].append(render_body(d, p))
                cv = WP.Canvas(S, S)
                draw_weapon_state(cv, wid, (hand[0] + poff[0], hand[1] + poff[1]), phi, state)
                weapons[d].append(cv)
                hands[d].append(hand)
        depth = DEPTH
        wextra = dict(stateNote="ghost 실체화(호박 윤곽) · steel · glow 판정 프레임(날끝 글로우) · fade 흩어짐(다음 타로 넘어가면 보이지 않음) · embers 불티(연격 끝)")
    memo = combo_memo(wid, n)
    name = "%s_combo%d" % (wid, n)
    save_png_json(OUT_P, "player_" + name, bodies, PW, PH, ms, False, (8, 23), PAL_PLAYER,
                  dict(memo, note="무기를 든 연격 몸 동작. weapons/%s 를 같은 프레임 번호·같은 시각에 겹친다(§6.1)." % name), name)
    wmeta = dict(memo, anchor="player_pivot", depth=depth, playerFrameOffset={"x": poff[0], "y": poff[1]},
                 overlay="player_%s 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 (%d,%d) = 주인공 피벗 (8,23)." % (name, wpivot[0], wpivot[1]),
                 frameStates=[f[5] for f in cb["frames"]])
    wmeta.update(wextra)
    save_png_json(OUT_W, name, weapons, S, S, ms, False, wpivot, PAL_WEAPON, wmeta, name.split("_", 1)[1])
    check("player_" + name, "player", bodies)
    check("weapons/" + name, "weapon", weapons)
    # 이펙트
    fbd, fms, FS = FX_BUILDERS[wid](n)
    fpivot = (FS // 2, FS // 2 + BODY_CENTER_DY)
    extra = dict(memo, anchor="player_pivot", spawn="attack_frame%d" % (cb["hit"][0] + 1), impactFrame=1,
                 spawnNote="f0(예비 40ms)는 몸 시트 f%d 시작(=판정) 40ms 전에 재생, f1 시작 = 판정. 몸 시트 1프레임째 길이 >= 40ms." % cb["hit"][0],
                 depth="above", secondary="fx.weapons.%s" % wid,
                 pivotNote="피벗 (%d,%d) = 발. 호·찌르기 원점 = 몸 중심 (%d,%d) (발 위 %dpx)." % (fpivot[0], fpivot[1], FS // 2, FS // 2, BODY_CENTER_DY))
    if wid == "katana":
        extra["trail"] = {"color": K.FX["weapons"][wid]["ramp"][1], "alpha": 0.6 if n < 3 else 0.7, "ms": 120 if n < 3 else 180, "fromFrame": 2,
                          "note": "W1 잔상 트레일, 반지름 = hitRadiusPx - 띠 두께/2"}
        if n == 3:
            extra["flash"] = {"color": K.FX["core"][1], "alpha": 0.12, "ms": 40, "atFrame": 1}
            extra["shake"] = {"px": 1, "ms": 50}
        extra["note"] = ["씽(1타, 140°) · 씽(2타 역방향 130°, 얇고 빠름) · 씽(3타 170°, f1 섬광 + 3겹 + 광선 3)"][0]
    elif wid == "greatsword":
        extra["trail"] = {"color": K.FX["weapons"][wid]["ramp"][1], "alpha": 0.6 if n < 3 else 0.7, "ms": 160 if n < 3 else 220, "fromFrame": 2,
                          "note": "W1 잔상 트레일, 반지름 = hitRadiusPx - 띠 두께/2"}
        extra["shake"] = {"px": 2, "ms": 60} if n < 3 else {"px": 3, "ms": 90}
        if n == 3:
            extra["flash"] = {"color": K.FX["weapons"][wid]["ramp"][3], "alpha": 0.12, "ms": 40, "atFrame": 1}
        extra["note"] = "훙: 두께 10 호 + 안쪽 겹 + 바닥 불티·재. 3타 = 270° 두께 12, f1 섬광, 3겹, 광선 3, 앞-아래 바닥 균열 3줄"
    else:
        extra["note"] = "슈슈슉: 호가 아니라 앞으로 뻗는 찌르기 줄기(뒤 가늘고 앞 70% 굵고 촉 뾰족) + 옆 그림자 줄기. 1타 위 8° · 2타 아래 10° · 3타 정면 길게 + 부채꼴 그림자 둘(±9°)"
        if n == 3:
            extra["shake"] = {"px": 1, "ms": 40}
    save_png_json(OUT_FX, name, fbd, FS, FS, fms, False, fpivot, PAL_FX, extra, name)
    check("fx/" + name, "fx", fbd, wid)
    out = dict(bodies=bodies, weapons=weapons, fx=fbd, ms=ms, fms=fms, S=S, poff=poff, FS=FS, fpivot=fpivot, wpivot=wpivot, hitf=cb["hit"][0])
    if r49:
        out["depth"] = depth
    return out


def build_special(wid):
    sp = SPECIALS[wid]
    S, poff, wpivot = wcanvas(wid)
    bodies, weapons = {}, {}
    for d in DIRS:
        bodies[d], weapons[d] = [], []
        for row in sp["rows"][d]:
            p, hand, phi, state, extra = special_pose(wid, d, row)
            bodies[d].append(render_body(d, p, extra))
            cv = WP.Canvas(S, S)
            draw_weapon_state(cv, wid, (hand[0] + poff[0], hand[1] + poff[1]), phi, state)
            weapons[d].append(cv)
    name = "%s_special" % wid
    memo = dict(sp["memo"], weapon=wid, framesBasis="player_%s 프레임 번호 (몸·무기 공통)" % name,
                note="무기를 든 채 보조 동작을 하는 몸·무기 자세(§6.2). 기존 보조 fx 는 그대로 겹친다(overlayFx).")
    save_png_json(OUT_P, "player_" + name, bodies, PW, PH, sp["ms"], sp["loop"], (8, 23), PAL_PLAYER, memo, name)
    save_png_json(OUT_W, name, weapons, S, S, sp["ms"], sp["loop"], wpivot, PAL_WEAPON,
                  dict(memo, anchor="player_pivot", depth=DEPTH, playerFrameOffset={"x": poff[0], "y": poff[1]},
                       frameStates=[r[3] for r in sp["rows"]["right"]]), "special")
    check("player_" + name, "player", bodies)
    check("weapons/" + name, "weapon", weapons)
    return dict(bodies=bodies, weapons=weapons, ms=sp["ms"], S=S, poff=poff)


def build_bow_aim():
    S, poff, wpivot = 48, (16, 16), (24, 39)
    bodies, weapons = {}, {}
    for d in DIRS:
        bodies[d], weapons[d] = [], []
        for f in range(len(BOW_MS)):
            p, extra = bow_pose(d, f)
            bodies[d].append(render_body(d, p, extra))
            cv = WP.Canvas(S, S)
            draw_bow_aim(cv, d, f, poff)
            weapons[d].append(cv)
    memo = {"weapon": "bow", "secondaryAction": "aimed shot (우클릭 조준 사격)",
            "progressDriven": True, "progressFrames": [0, 1, 2, 3, 4, 5],
            "progressFormula": "frame = min(5, floor(progress*5)) — aim_charge 와 같은 식 (f5 = 완료)",
            "releaseFrame": 6, "releaseNote": "발사 순간 f6 을 80ms 재생 후 종료. 화살 생성 = f6 시작. 취소(먼저 뗌)면 f6 없이 종료",
            "drawPx": BOW_DRAW[:6], "framesBasis": "player_bow_aim 프레임 번호 (몸·무기 공통)",
            "overlayFx": [{"id": "aim_charge", "anchor": "player_pivot", "note": "같은 진행도로 동기"},
                          {"id": "aim_line", "note": "조준선"}],
            "note": "시위 당김 자세. 활은 방향별 고정 위치(weapons/bow_attack 과 같음), 시위 손이 진행도만큼 뒤로. f0 화살 실체화(호박), f5 촉 글린트."}
    save_png_json(OUT_P, "player_bow_aim", bodies, PW, PH, BOW_MS, False, (8, 23), PAL_PLAYER, memo, "bow_aim")
    save_png_json(OUT_W, "bow_aim", weapons, S, S, BOW_MS, False, wpivot, PAL_WEAPON,
                  dict(memo, anchor="player_pivot", depth=DEPTH, playerFrameOffset={"x": 16, "y": 16}), "aim")
    check("player_bow_aim", "player", bodies)
    check("weapons/bow_aim", "weapon", weapons)
    return dict(bodies=bodies, weapons=weapons, ms=BOW_MS, S=S, poff=poff)


# ============================================================ 10. 49라운드 (decisions/2026-10-02-round-49-playtest2.md 4·5절, art §7.2)
# 두 손 대검 연격 · 발도 베기 · 내리찍기 · 대쉬 베기 · 단검 가열 이펙트 · 활 장전. 공용 기하 = gear.py (carry/build.py 와 공유).
sys.path.insert(0, HERE)
import gear as GR  # noqa: E402

SRC49 = "parts/art/work/combos/build.py (49라운드 4·5절 · art §7.2)"


def _gs_pose(d, th, L, fwd, dip, crouch, opt):
    phi = None
    if "phi" in opt and d in opt["phi"]:
        phi = opt["phi"][d]
    legs = opt.get("legs")
    if legs is None and d in ("left", "right") and fwd < 0:
        legs = (1, -2)                      # 예비: 뒷발에 무게
    return GR.twohand_pose(d, th, L, fwd, dip, crouch, pull=opt.get("pull", 0.0), legs=legs,
                           extra=opt.get("extra"), phi=phi)


def r49_combo_frames(wid, n):
    """대검 1~3타(두 손) · 칼 1타(발도). 반환 (bodies, baked weapons, depth)."""
    cb = COMBOS[wid][n]
    S, poff, wpivot = wcanvas(wid)
    spec = SPEC[wid]
    bodies, weapons, depth = {}, {}, {}
    for d in DIRS:
        bl, ll = [], []
        for th, L, fwd, dip, crouch, state, opt in cb["frames"]:
            ly = GR.Layers(S, poff)
            if wid == "greatsword":
                p, under, over, hand, phi = _gs_pose(d, th, L, fwd, dip, crouch, opt)
                GR.blade(ly, hand, phi, spec, GR.blade_layer(d, phi), tip_glow=(state == "glow"))
                body = GR.render_body(d, p, under, over)
            elif state == "sheathed":       # 발도 직전: 칼집 손잡이를 쥐고 낮게
                p = P.Pose(body_dy=dip, crouch=crouch)
                if d in ("left", "right"):
                    p.lean = 1
                    p.l_dx, p.r_dx = 1, -1
                g = GR.sheath_geo(d, p)
                GR.draw_scabbard(ly, g, empty=False)
                GR.draw_katana_hilt(ly, g)
                if d == "up":
                    p.l_arm = "pos"
                else:
                    p.r_arm = "pos"
                p.hand_pos = GR.clamp_hand(*GR.katana_hilt_grip(d, p))
                body = GR.render_body(d, p)
            else:
                p, under, over, hand, phi = GR.twohand_pose(d, th, L, fwd, dip, crouch, pull=opt.get("pull", 0.0),
                                                            legs=(0, 0), two=False)
                GR.draw_scabbard(ly, GR.sheath_geo(d, p), empty=True)
                GR.blade(ly, hand, phi, spec, GR.blade_layer(d, phi), tip_glow=(state == "glow"))
                body = GR.render_body(d, p)
            bl.append(body)
            ll.append(ly)
        weapons[d], depth[d] = GR.bake_dir(ll, bl)
        bodies[d] = bl
    return bodies, weapons, depth


# ---------------------------------------------------------------- 대검 내리찍기 / 대쉬 베기 (몸 + 무기)
GS_TUCK = {"l_sl": 2, "r_sl": 2, "l_lift": 2, "r_lift": 2}
GS_HALF = {"l_sl": 1, "r_sl": 0, "l_lift": 1, "r_lift": 0}
SLAM = dict(  # (θ, L, fwd, dip, crouch, 상태, opt), ms
    frames=[(-125, 4, 0, 0, 1, "steel", {"phi": {"down": -105, "up": -75}}),                                   # 0 웅크려 칼을 등 위로
            (-95, 6, 0, -1, 0, "steel", {"phi": {"down": -90, "up": -90}}),                                     # 1 머리 위로 높이 듦
            (-100, 6, 0, -1, 0, "steel", {"extra": GS_TUCK, "phi": {"down": -90, "up": -90}}),                  # 2 도약(다리 접음)
            (-20, 5, 1, 0, 0, "glow", {"extra": GS_HALF, "phi": {"down": 45, "up": -135}}),                     # 3 떨어지며 내려침
            (25, 5, 2, 2, 2, "glow", {"phi": {"down": 90, "up": -90}, "flen": {"up": 10}}),                     # 4 착지 + 내려찍음 = 충격
            (28, 5, 2, 2, 2, "steel", {"phi": {"down": 90, "up": -90}, "flen": {"up": 10}}),                    # 5 박힌 채 버팀
            (60, 4, 1, 1, 1, "steel", {"pull": 0.5}),                                                           # 6 뽑아 올림
            (110, 3, 0, 0, 0, "steel", {"pull": 0.7})],                                                         # 7 자세 회복
    ms=[90, 110, 90, 60, 90, 160, 120, 130], leap=[2, 3], impact=4, recover=[5, 6, 7])
DASHSLASH = dict(
    frames=[(165, 3, 1, 0, 1, "steel", {"legs": (2, -2), "extra": {"tail": 2}}),                     # 0 박차고 나감, 칼은 뒤로 낮게
            (175, 4, 2, 0, 1, "steel", {"legs": (2, -2), "extra": {"tail": 3, "lean": 2}}),          # 1 달려듦
            (10, 5, 2, 0, 0, "glow", {"legs": (2, -1), "extra": {"tail": 2}}),                       # 2 훙 (판정)
            (-80, 5, 1, -1, 0, "steel", {"legs": (2, -1), "extra": {"tail": 1}}),                    # 3 끝까지 휘두름
            (-120, 4, -1, 0, 2, "steel", {"legs": (2, -2), "extra": {"lean": -1}}),                  # 4 미끄러지며 멈춤
            (-60, 4, 0, 1, 1, "steel", {}),                                                           # 5 자세 잡고 대기
            (110, 3, 0, 0, 0, "steel", {"pull": 0.7})],                                               # 6 회복
    ms=[70, 90, 60, 90, 120, 160, 140], hit=[2], recover=[4, 5, 6], arc=(110, -100))


def gs_action_frames(table):
    S, poff, wpivot = wcanvas("greatsword")
    spec = SPEC["greatsword"]
    bodies, weapons, depth, tips = {}, {}, {}, {}
    for d in DIRS:
        bl, ll, tl = [], [], []
        for th, L, fwd, dip, crouch, state, opt in table["frames"]:
            ly = GR.Layers(S, poff)
            p, under, over, hand, phi = _gs_pose(d, th, L, fwd, dip, crouch, opt)
            sp = dict(spec, length=opt["flen"][d]) if d in opt.get("flen", {}) else spec   # 원근 단축(멀어지는 칼날)
            GR.blade(ly, hand, phi, sp, GR.blade_layer(d, phi), tip_glow=(state == "glow"))
            qx, qy = GR.qdir(phi)
            tl.append((round(hand[0] + qx * sp["length"]), round(hand[1] + qy * sp["length"])))
            bl.append(GR.render_body(d, p, under, over))
            ll.append(ly)
        weapons[d], depth[d] = GR.bake_dir(ll, bl)
        bodies[d] = bl
        tips[d] = tl
    return dict(bodies=bodies, weapons=weapons, depth=depth, ms=table["ms"], S=S, poff=poff, wpivot=wpivot, tips=tips)


def slam_fx(d):
    """96×96, 피벗 (48,48) = 내려찍은 자리 = 충격파 판정 원 중심. 바닥 원근 ky 0.6. 균열은 정면(d)으로 쏠린 부채꼴."""
    wid = "greatsword"
    S = 96
    cx, cy = 48, 48
    fwd = {"right": 0, "left": 180, "down": 90, "up": -90}[d]
    cracks = [(-20, 22), (25, 20), (-60, 15), (65, 14), (0, 26), (-110, 10), (115, 9), (180, 7)]

    def crack_lines(cv, scale, cols, dashed=False):
        tmp = K.Canvas(S, S)
        for i, (a, L) in enumerate(cracks):
            ang = math.radians(fwd + a)
            L2 = L * scale
            pts = K.zigzag(cx + 3 * math.cos(ang), cy + 3 * math.sin(ang) * 0.6, cx + L2 * math.cos(ang), cy + L2 * math.sin(ang) * 0.6,
                           4, 2.0, 90 + i)
            tmp.bolt(pts, cols)
        if dashed:
            tmp.dash_pattern(mod=3, keep=(0, 1), seed=1)
        merge(cv, tmp)

    def debris(cv, rr, cols, k0=0, n=5, lift=2):
        for k in range(n):
            a = math.radians(fwd + (-75 + k * 150 / max(1, n - 1)))
            cv.pair(cx + rr * math.cos(a), cy + rr * math.sin(a) * 0.6 - lift, cols[(k + k0) % len(cols)], horiz=(k % 2 == 0))

    fr = []
    cv = K.Canvas(S, S)   # f0 충격 섬광: 백열 원 + 짧은 별빛 + 첫 고리 r5
    for a in range(0, 360, 45):
        ang = math.radians(a)
        L = 7 if a % 90 == 0 else 5
        cv.line(cx, cy, cx + L * math.cos(ang), cy + L * math.sin(ang) * 0.6, C(27))
    cv.ring(cx, cy, 5, W(wid, 3), thick=1.6, ky=0.6)
    cv.disc(cx, cy, 2.6, X0, ky=0.6)
    fr.append(cv)
    cv = K.Canvas(S, S)   # f1 고리 r12 + 균열 시작(용암) + 파편
    cv.ring(cx, cy, 12, W(wid, 0), thick=3.2, ky=0.6)
    cv.ring(cx, cy, 12, W(wid, 3), thick=1.8, ky=0.6)
    cv.ring(cx, cy, 12, X1, thick=1.0, ky=0.6, dash=(50, 40), phase=fwd - 25)
    crack_lines(cv, 0.45, [(1, W(wid, 0)), (0, W(wid, 2))])
    cv.disc(cx, cy, 2.4, X1, ky=0.6)
    debris(cv, 15, [C(27), W(wid, 3)], n=4, lift=3)
    fr.append(cv)
    cv = K.Canvas(S, S)   # f2 고리 r22 + 균열 전체 + 불티
    cv.ring(cx, cy, 22, W(wid, 0), thick=3.6, ky=0.6)
    cv.ring(cx, cy, 22, W(wid, 2), thick=2.0, ky=0.6)
    cv.ring(cx, cy, 22, X1, thick=1.0, ky=0.6, dash=(30, 60), phase=fwd - 15)
    crack_lines(cv, 0.85, [(1, W(wid, 0)), (0, W(wid, 2))])
    cv.disc(cx, cy, 2.6, W(wid, 3), ky=0.6)
    cv.px(cx, cy, X1)
    debris(cv, 25, [C(27), W(wid, 3), C(26)], n=5, lift=4)
    fr.append(cv)
    cv = K.Canvas(S, S)   # f3 고리 r31(점선) + 균열 식음 + 재
    cv.ring(cx, cy, 31, W(wid, 0), thick=3.0, ky=0.6)
    cv.ring(cx, cy, 31, W(wid, 2), thick=1.2, ky=0.6, dash=(30, 12))
    crack_lines(cv, 1.0, [(1, W(wid, 0)), (0, W(wid, 1))])
    cv.disc(cx, cy, 2.0, W(wid, 2), ky=0.6)
    debris(cv, 33, [G(9), C(26), G(6)], n=5, lift=6)
    fr.append(cv)
    cv = K.Canvas(S, S)   # f4 고리 r37 흩어짐 + 균열 W0
    cv.ring(cx, cy, 37, W(wid, 0), thick=1.6, ky=0.6, dash=(14, 12))
    crack_lines(cv, 1.0, [(0, W(wid, 0))])
    for k, (a, L) in enumerate(cracks[:5]):
        ang = math.radians(fwd + a)
        cv.pair(cx + L * 0.55 * math.cos(ang), cy + L * 0.55 * math.sin(ang) * 0.6, W(wid, 1), horiz=(k % 2 == 0))
    debris(cv, 38, [G(6), G(9)], n=4, lift=8)
    fr.append(cv)
    cv = K.Canvas(S, S)   # f5 남은 균열 점선 + 불씨
    crack_lines(cv, 1.0, [(0, W(wid, 0))], dashed=True)
    for k, (a, L) in enumerate(cracks[:4]):
        ang = math.radians(fwd + a)
        cv.pair(cx + L * 0.4 * math.cos(ang), cy + L * 0.4 * math.sin(ang) * 0.6, W(wid, 1), horiz=(k % 2 == 1))
    fr.append(cv)
    for c_ in fr:
        c_.despeckle8()
    return fr, [50, 60, 80, 100, 120, 150], S


def build_slam():
    r = gs_action_frames(SLAM)
    ms = SLAM["ms"]
    imp = SLAM["impact"]
    offs = {d: {"x": r["tips"][d][imp][0] - 8, "y": r["tips"][d][imp][1] - 23} for d in DIRS}
    dist = round(sum(math.hypot(o["x"], o["y"]) for o in offs.values()) / 4.0)
    memo = {"weapon": "greatsword", "action": "slam (개성 발현 후 충격파: 마우스 방향으로 짧게 도약해 내려찍기)",
            "leapFrames": SLAM["leap"], "impactFrame": imp, "recoverFrames": SLAM["recover"],
            "timingMs": {"leapStart": sum(ms[:SLAM["leap"][0]]), "impactAt": sum(ms[:imp]), "total": sum(ms)},
            "leapNote": "임시(아트 제안): 도약 프레임 동안 시스템이 마우스 방향으로 이동(거리·속도는 시스템). 스프라이트는 다리를 접은 자세만 — "
                        "몸을 띄우는 화면 y 오프셋은 시스템이 그린다(제안 leapOffsetsPx).",
            "leapOffsetsPx": {"2": -3, "3": -2},
            "impactOffsetPx": offs,
            "impactDistancePx": dist,
            "impactNote": "충격파 중심(= fx/greatsword_slam 피벗) = 발 피벗 + 정면(마우스 방향) × impactDistancePx. impactOffsetPx 는 4방향 그림의 칼끝 실제 위치(참고).",
            "fx": {"id": "greatsword_slam", "spawn": "impactFrame", "anchor": "hitbox_center"},
            "framesBasis": "player_greatsword_slam 프레임 번호 (몸·무기 공통)"}
    save_png_json(OUT_P, "player_greatsword_slam", r["bodies"], PW, PH, ms, False, (8, 23), PAL_PLAYER, dict(memo, source=SRC49), "greatsword_slam")
    save_png_json(OUT_W, "greatsword_slam", r["weapons"], r["S"], r["S"], ms, False, r["wpivot"], PAL_WEAPON,
                  dict(memo, anchor="player_pivot", depth=r["depth"], depthByFrame={d: [r["depth"][d]] * len(ms) for d in DIRS},
                       occlusionBaked=True, playerFrameOffset={"x": r["poff"][0], "y": r["poff"][1]},
                       frameStates=[f[5] for f in SLAM["frames"]], source=SRC49), "slam")
    check("player_greatsword_slam", "player", r["bodies"])
    check("weapons/greatsword_slam", "weapon", r["weapons"])
    fxd, fms = {}, None
    for d in DIRS:
        fxd[d], fms, FS = slam_fx(d)
    fx_memo = {"weapon": "greatsword", "anchor": "hitbox_center", "spawn": "greatsword_slam_impact",
               "spawnNote": "player_greatsword_slam 의 impactFrame(f%d) 시작에 재생. 피벗 (48,48) = 충격파 판정 원 중심." % imp,
               "depth": "floor", "depthNote": "바닥 깊이(몸 아래). 파편 불티는 바닥 위 2~8px 로 그려 두었다.",
               "secondary": "fx.weapons.greatsword",
               "scale": "allowed", "scaleNote": "그림 고리 최대 반경 37~38px(바깥 끝) ≈ 반경 40 기준. 판정 반경 R 이면 scale = R/40 (정수 배율 권장, boss_slam 과 같은 규약)",
               "drawnRadiusPx": 38, "ringKy": 0.6,
               "flash": {"color": K.FX["core"][1], "alpha": 0.16, "ms": 60, "atFrame": 0},
               "shake": {"px": 4, "ms": 120},
               "note": "대검 내리찍기 충격파: 백열 섬광 → 납작한 고리(용암) 확산 → 정면 쪽으로 쏠린 균열 부채꼴 → 재·불씨. 층 강조는 26·27(불티)만.",
               "source": SRC49}
    save_png_json(OUT_FX, "greatsword_slam", fxd, FS, FS, fms, False, (48, 48), PAL_FX, fx_memo, "greatsword_slam")
    check("fx/greatsword_slam", "fx", fxd, "greatsword")
    r.update(fx=fxd, fms=fms, FS=FS, fpivot=(48, 48), offs=offs)
    return r


def build_dashslash():
    r = gs_action_frames(DASHSLASH)
    ms = DASHSLASH["ms"]
    a0, a1 = DASHSLASH["arc"]
    memo = {"weapon": "greatsword", "action": "dash slash (달려들며 크게 한 번 휘두르고 멈춰 자세 잡음)",
            "hitFrames": DASHSLASH["hit"], "activeFrames": DASHSLASH["hit"], "recoverFrames": DASHSLASH["recover"],
            "timingMs": {"hitAt": sum(ms[:2]), "recoverFrom": sum(ms[:4]), "total": sum(ms)},
            "hitRadiusPx": HIT["greatsword"], "arcDeg": abs(a1 - a0), "arcFromDeg": a0, "arcToDeg": a1,
            "arcAngleNote": "right 방향 화면각(0 = 정면, + = 아래). down = +90°, up = -90°, left = 180-θ. 아래→위로 크게 쓸어 올림",
            "moveNote": "임시(아트 제안): f0~f2 는 대쉬 이동 중(박차고 나감·달려듦·훙), f3 에서 감속, f4 미끄러지며 정지, f5 '공격하기 위해 대기'(자세 잡음), f6 회복. "
                        "이동 거리·정지 시점·대기 시간은 시스템. 대기를 늘리려면 f5 를 유지(holdFrame 5).",
            "holdFrame": 5,
            "fxReuse": {"id": "greatsword_combo2", "spawnAtMs": sum(ms[:2]) - 40,
                        "note": "전용 이펙트 시트는 이번 범위 밖 — 호가 같은 방향(아래→위 100→-100)인 2타 이펙트를 재사용 제안"},
            "framesBasis": "player_greatsword_dashslash 프레임 번호 (몸·무기 공통)", "source": SRC49}
    save_png_json(OUT_P, "player_greatsword_dashslash", r["bodies"], PW, PH, ms, False, (8, 23), PAL_PLAYER, memo, "greatsword_dashslash")
    save_png_json(OUT_W, "greatsword_dashslash", r["weapons"], r["S"], r["S"], ms, False, r["wpivot"], PAL_WEAPON,
                  dict(memo, anchor="player_pivot", depth=r["depth"], depthByFrame={d: [r["depth"][d]] * len(ms) for d in DIRS},
                       occlusionBaked=True, playerFrameOffset={"x": r["poff"][0], "y": r["poff"][1]},
                       frameStates=[f[5] for f in DASHSLASH["frames"]]), "dashslash")
    check("player_greatsword_dashslash", "player", r["bodies"])
    check("weapons/greatsword_dashslash", "weapon", r["weapons"])
    return r


# ---------------------------------------------------------------- 단검 가열 (heat 1·2·3: 점점 밝고 길게, 보라 → 백열)
HEAT_RATE = {1: 1.15, 2: 1.3, 3: 1.5}


def dagger_heat_fx(n, k):
    wid, S = "dagger", 80                    # 가열 줄기·광선이 길어 64 에서 잘린다 → 80 (피벗 (40,50))
    c = (S - 1) / 2.0
    t = COMBOS[wid][n]["thrust"]
    ang = t["angle"]
    s1 = t["length"] + 2 * k                 # 그림 길이만 늘린다(판정은 thrust 그대로)
    s0 = 7
    Wd = [W(wid, i) for i in range(4)]
    body = {1: [Wd[0], Wd[1], Wd[3], X1], 2: [Wd[0], Wd[2], Wd[3], X1], 3: [Wd[0], Wd[3], X1, X0]}[k]
    hot = {1: [Wd[0], Wd[2], Wd[3], X1], 2: [Wd[0], Wd[3], X1, X0], 3: [Wd[0], Wd[3], X1, X0]}[k]
    cool = {1: [Wd[0], Wd[1], Wd[2]], 2: [Wd[0], Wd[2], Wd[3]], 3: [Wd[0], Wd[3], X1]}[k]
    shadow = {1: [Wd[0], Wd[1]], 2: [Wd[0], Wd[2]], 3: [Wd[1], Wd[3]]}[k]
    core = {1: ([X1, X0], 0.3), 2: ([X1, X0], 0.15), 3: ([X0, X0], 0.0)}[k]
    side = 1 if ang <= 0 else -1
    tipx, tipy = tip_point(c, ang, s1 + 1)
    wbase = 7.0 if n < 3 else 8.5
    wmax = wbase + 0.5 * k
    fr = []

    def echo(cv, back, cols, width, t_to=1.0):
        """가열 잔상: 같은 줄기를 뒤로 back px 밀어 한 겹 더(열기가 길게 남음)."""
        tmp = K.Canvas(S, S)
        spindle(tmp, c, ang, s0 - back, s1 - back, width, cols, t_to=t_to)
        tmp.dash_pattern(mod=4, keep=(0, 1, 2), seed=k)
        merge(cv, tmp)

    cv = K.Canvas(S, S)   # f0 예비 코어 줄 (가열될수록 길다)
    spindle(cv, c, ang, s0, s1, 2.0 + 0.2 * k, [Wd[2] if k < 3 else Wd[3], X1], t_to=0.45 + 0.1 * k)
    x, y = tip_point(c, ang, s0 + (0.45 + 0.1 * k) * (s1 - s0) + 1)
    cv.pair(x, y, C(27))
    fr.append(cv)
    cv = K.Canvas(S, S)   # f1 본 줄기(판정)
    if k >= 2:
        echo(cv, 4, [Wd[0], Wd[1]] if k == 2 else [Wd[1], Wd[2]], wmax * 0.7)
    if n < 3:
        spindle(cv, c, ang, s0 + 1, s1 - 2, 4.0, shadow, poff=4.5 * side, t_to=0.5)
        spindle(cv, c, ang, s0, s1, wmax, body, core=core[0], core_from=core[1])
    else:
        spindle(cv, c, ang, s0, s1, wmax + (1.0 if k == 3 else 0.0), hot, core=[X1, X0] if k >= 2 else None, core_from=0.3)
    cv.pair(tipx, tipy, C(27))
    if k >= 2:
        x, y = tip_point(c, ang, s1 + 3)
        cv.pair(x, y, C(27))
    fr.append(cv)
    cv = K.Canvas(S, S)   # f2 식기 시작 + 광선 (가열될수록 많고 길다)
    if k >= 2:
        echo(cv, 3, [Wd[0], Wd[1]], wmax * 0.6, t_to=0.8)
    if n < 3:
        spindle(cv, c, ang, s0 + 1, s1 - 2, 4.0, shadow, poff=4.5 * side)
        spindle(cv, c, ang, s0, s1, wmax * 0.9, body, t_from=0.3 - 0.08 * k, core=[core[0][0], X1 if k < 3 else X0])
    else:
        for da in (-9, 9):
            spindle(cv, c, ang + da, s0 + 2, s1 - 3, 4.0 + 0.3 * k, shadow)
        spindle(cv, c, ang, s0, s1, wmax, body, core=core[0], core_from=core[1])
    K.spill_rays(cv, c, c, ang, ang, 0.0, s1, wid, n=2 + k, length=4 + min(k, 2), seed=7 + n + 10 * k,
                 cols=[(1, Wd[0] if k < 3 else Wd[1]), (0, C(27) if k < 3 else X0)])
    fr.append(cv)
    cv = K.Canvas(S, S)   # f3 꼬리 (가열될수록 밝게 남는다)
    spindle(cv, c, ang, s0, s1, 3.0 + 0.4 * k, cool if n < 3 else cool, t_from=0.35 - 0.05 * k)
    dash_out(cv, mod=4, keep=(0, 1, 2), seed=n + k)
    tmp = K.Canvas(S, S)
    spindle(tmp, c, ang, s0 + 1, s1 - 3, 2.6, [shadow[0]], poff=4.5 * side, t_from=0.3)
    tmp.dash_pattern(mod=5, keep=(0, 1), seed=2)
    merge(cv, tmp)
    x, y = tip_point(c, ang + 12 * side, s1 + 2)
    cv.pair(x, y, C(24) if k < 3 else C(27))
    if k == 3:
        x, y = tip_point(c, ang - 14 * side, s1)
        cv.pair(x, y, C(24), horiz=False)
    fr.append(cv)
    if n == 3:
        cv = K.Canvas(S, S)   # f4 (3타) 남은 열 꼬리
        spindle(cv, c, ang, s0, s1, 3.0, shadow, t_from=0.4)
        dash_out(cv, mod=4, keep=(0, 1, 2), seed=3)
        x, y = tip_point(c, ang + 15, s1 + 3)
        cv.pair(x, y, C(22) if k < 3 else C(24))
        fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    ms = [40, 40, 50, 70] if n < 3 else [40, 40, 50, 60, 90]
    return K.four_dirs_from_right(fr), ms, S


def build_dagger_heat():
    out = {}
    for n in (1, 2, 3):
        base = json.load(open(os.path.join(OUT_FX, "dagger_combo%d.json" % n), encoding="utf-8"))
        for k in (1, 2, 3):
            fbd, fms, FS = dagger_heat_fx(n, k)
            assert fms == base["frameDurationsMs"], (n, k)
            name = "dagger_combo%d_heat%d" % (n, k)
            meta = {kk: base[kk] for kk in ("weapon", "comboIndex", "comboLength", "hitFrames", "activeFrames", "cancelFromFrame",
                                            "timingMs", "hitOrigin", "thrust", "thrustNote", "anchor", "spawn", "impactFrame",
                                            "spawnNote", "depth", "secondary", "pivotNote") if kk in base}
            meta.update({"heatLevel": k, "heatOf": "dagger_combo%d" % n, "visualLengthPx": COMBOS["dagger"][n]["thrust"]["length"] + 2 * k,
                         "heatNote": "가열(과열 기능) 단계 k 일 때 dagger_combo%d 대신 재생. 판정(thrust)은 그대로, 그림만 길고 밝다 "
                                     "(1 = 보라 몸체 + 코어 확장, 2 = 보라→백열 + 잔상 한 겹, 3 = 백열 몸체 + 보라 가장자리만)." % n,
                         "playbackRateHint": HEAT_RATE[k],
                         "playbackRateNote": "임시(아트 제안): '후반 갈수록 공격 속도가 빨라지는 느낌' — 몸·무기·이펙트 재생 배속 제안. 실제 공격 속도 배율은 시스템",
                         "source": SRC49})
            meta["pivotNote"] = "피벗 (%d,%d) = 발. 찌르기 원점 = 몸 중심 (%d,%d) (발 위 %dpx). 가열 줄기가 길어 기본(64)보다 큰 %d 캔버스." % (
                FS // 2, FS // 2 + BODY_CENTER_DY, FS // 2, FS // 2, BODY_CENTER_DY, FS)
            if k == 3:
                meta["shake"] = {"px": 1, "ms": 40}
            save_png_json(OUT_FX, name, fbd, FS, FS, fms, False, (FS // 2, FS // 2 + BODY_CENTER_DY), PAL_FX, meta, name)
            check("fx/" + name, "fx", fbd, "dagger")
            out[(n, k)] = dict(fx=fbd, fms=fms, FS=FS)
    return out


# ---------------------------------------------------------------- 활 장전 (화살 탄창 채움)
RELOAD_MS = [90, 100, 120, 100, 90]


def arrows(ly, hand, deg, ghost, layer="front", L=6, spread=20, parallel=False):
    """손에 쥔 화살 묶음. ghost = 실체화 중(호박 윤곽). parallel: 나란한 화살 2개(사이 1px), 아니면 3개 부채."""
    shaft = C(22) if ghost else G(13)
    tip = C(25) if ghost else C(27)
    fl = C(19) if ghost else C(21)
    hx_, hy_ = hand
    a0 = math.radians(deg)
    ca0, sa0 = math.cos(a0), math.sin(a0)
    if parallel:
        nx_, ny_ = -sa0, ca0
        for k in (-1, 1):
            ox, oy = hx_ + nx_ * k, hy_ + ny_ * k
            GR.LN(ly, ox, oy, ox + ca0 * (L - 1), oy + sa0 * (L - 1), shaft, layer)
            GR.P2(ly, ox + ca0 * L, oy + sa0 * L, tip, layer)
            GR.P2(ly, ox - ca0, oy - sa0, fl, layer)
        return
    for da in (-spread, 0, spread):
        a = math.radians(deg + da)
        ca, sa = math.cos(a), math.sin(a)
        LL = L + (1 if da == 0 else 0)
        GR.LN(ly, hx_, hy_, hx_ + ca * (LL - 1), hy_ + sa * (LL - 1), shaft, layer)
        GR.P2(ly, hx_ + ca * LL, hy_ + sa * LL, tip, layer)
    GR.P2(ly, hx_ - ca0, hy_ - sa0, fl, layer)


def build_bow_reload():
    S, poff, wpivot = 48, (16, 16), (24, 39)
    bodies, weapons, depth = {}, {}, {}
    for d in DIRS:
        bl, ll = [], []
        for f in range(5):
            p = P.Pose(body_dy=1 if f == 3 else 0)
            ly = GR.Layers(S, poff)
            hand = GR.weapon_hand_rest(d, p)
            under, over = [], []
            side = d in ("left", "right")
            m = 1 if d == "right" else -1
            # 손이 닿는 곳: f0 어깨 뒤로 뻗음 → f1 화살 실체화(머리 옆 위) → f2 가슴 앞으로 → f3 활 그립에 끼움(충전) → f4 내림
            if d == "down":
                reach = [(3, 5), (3, 3), (8, 12), (12, 14), None][f]
            elif d == "up":
                reach = [(12, 5), (12, 3), (7, 12), (3, 14), None][f]
            else:
                reach = [(7 - 3 * m, 4), (7 - 3 * m, 2), (7 + 3 * m, 12), (hand[0] + 2 * m, hand[1] - 1), None][f]
            if reach is not None:
                sx, sy = GR.off_shoulder(d, p)
                arm = (sx, sy, reach[0], reach[1])
                if side and f <= 1:
                    under.append(arm)
                elif side:
                    over.append(arm)
                elif d == "down":
                    p.l_arm = "pos"
                    p.hand_pos = reach
                else:
                    p.r_arm = "pos"
                    p.hand_pos = reach
            GR.draw_bow_hand(ly, d, hand)
            if f == 0:
                GR.P2(ly, reach[0], reach[1] - 2, C(24), "front")
                GR.P2(ly, reach[0] + 1, reach[1] - 2, C(22), "front")
            elif f == 1:
                arrows(ly, reach, -90, True)
            elif f == 2:
                gx = hand[0] + (3 * m if side else (1 if d == "down" else -1))
                tdeg = math.degrees(math.atan2(hand[1] - 4 - reach[1], gx - reach[0]))
                arrows(ly, (reach[0] - math.cos(math.radians(tdeg)) * 2, reach[1] - math.sin(math.radians(tdeg)) * 2), tdeg, False, parallel=True)
            elif f == 3:
                gx, gy = hand[0] + (3 * m if side else (1 if d == "down" else -1)), hand[1]
                arrows(ly, (gx + (1 if not side else 0) * (1 if d == "down" else -1), gy - 1), -90, False, L=5, parallel=True)
                GR.P2(ly, gx - 1, gy - 7, C(27), "front")
                GR.P2(ly, gx + 1, gy - 7, C(25), "front")
            elif f == 4:
                gx = hand[0] + (3 * m if side else (1 if d == "down" else -1))
                GR.P2(ly, gx, hand[1] - 7, C(27), "front")
                GR.P2(ly, gx, hand[1] - 6, C(25), "front")
            bl.append(GR.render_body(d, p, under, over))
            ll.append(ly)
        weapons[d], depth[d] = GR.bake_dir(ll, bl)
        bodies[d] = bl
    memo = {"weapon": "bow", "action": "reload (화살 탄창 채움)",
            "phases": {"reach": [0], "materialize": [1], "bring": [2], "refill": [3], "settle": [4]},
            "refillFrame": 3, "refillNote": "탄창이 다시 차는 시점 = f3 시작 (활 그립에 화살 묶음을 끼우며 글린트)",
            "progressDriven": "optional",
            "progressFormula": "장전 시간이 시스템에서 정해지면 frame = min(4, floor(progress*5)) 로 진행도에 맞춰 재생해도 된다",
            "note": "활은 휴대 자리(손) 그대로, 다른 손이 어깨 뒤로 뻗어 호박빛으로 화살 3개를 실체화(f1) → 가져와(f2) 그립에 끼운다(f3). 화살통은 그리지 않는다(무기 실체화 언어).",
            "framesBasis": "player_bow_reload 프레임 번호 (몸·무기 공통)", "source": SRC49}
    save_png_json(OUT_P, "player_bow_reload", bodies, PW, PH, RELOAD_MS, False, (8, 23), PAL_PLAYER, memo, "bow_reload")
    save_png_json(OUT_W, "bow_reload", weapons, S, S, RELOAD_MS, False, wpivot, PAL_WEAPON,
                  dict(memo, anchor="player_pivot", depth=depth, depthByFrame={d: [depth[d]] * 5 for d in DIRS}, occlusionBaked=True,
                       playerFrameOffset={"x": poff[0], "y": poff[1]}), "reload")
    check("player_bow_reload", "player", bodies)
    check("weapons/bow_reload", "weapon", weapons)
    return dict(bodies=bodies, weapons=weapons, depth=depth, ms=RELOAD_MS, S=S, poff=poff, wpivot=wpivot)


# ---------------------------------------------------------------- 49라운드 미리보기
def _body_weapon(img, r, d, f, foot):
    wim = r["weapons"][d][f].im
    if dep(r, d) == "below":
        put(img, wim, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])
    put(img, r["bodies"][d][f], foot[0] - 8, foot[1] - 23)
    if dep(r, d) == "above":
        put(img, wim, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])


def preview_actions(items, path, k=4, cell=64):
    """items: [(title, res, fx_by_frame or None)] → 블록 = 4행(방향) × 프레임. fx_by_frame: {body frame: (fx res key frames...)}"""
    blocks = []
    for title, r, fxmap in items:
        nf = len(r["ms"])
        cw = cell * k
        blk = Image.new("RGB", (60 + nf * (cw + 3), 18 + 4 * (cw + 3)), (34, 34, 38))
        dr = ImageDraw.Draw(blk)
        dr.text((4, 2), "%s  %s ms" % (title, r["ms"]), fill=(235, 235, 235), font=FONT)
        for ri, d in enumerate(DIRS):
            y = 18 + ri * (cw + 3)
            dr.text((4, y + cw // 2 - 6), d, fill=(220, 220, 220), font=FONT)
            for f in range(nf):
                img = Image.new("RGBA", (cell, cell), FLOOR)
                foot = (cell // 2, cell // 2 + 14)
                if fxmap and f in fxmap:
                    fxr, fi, off = fxmap[f]
                    o = off(d) if callable(off) else (0, 0)
                    fxim = fxr["fx"][d][fi].im
                    put(img, fxim, foot[0] + o[0] - fxr["fpivot"][0], foot[1] + o[1] - fxr["fpivot"][1])
                _body_weapon(img, r, d, f, foot)
                blk.paste(scaled(img, k).convert("RGB"), (60 + f * (cw + 3), y))
        blocks.append(blk)
    Wd = max(b.width for b in blocks) + 16
    Hd = sum(b.height + 6 for b in blocks) + 10
    img = Image.new("RGB", (Wd, Hd), (22, 22, 26))
    y = 6
    for b in blocks:
        img.paste(b, (8, y))
        y += b.height + 6
    img.save(path)


def preview_heat(heat, k=3):
    """단검 가열: 행 = 1·2·3타, 열 = heat0(기존)·1·2·3 의 판정 프레임(f1)·f2 (right)."""
    S = 80
    img = Image.new("RGB", (70 + 8 * (S * k + 4), 20 + 3 * (S * k + 4)), (22, 22, 26))
    dr = ImageDraw.Draw(img)
    for n in (1, 2, 3):
        base = load_frames(os.path.join(OUT_FX, "dagger_combo%d.png" % n), 64, 64, DIRS)
        for hk in range(4):
            for j, fi in enumerate((1, 2)):
                cell = Image.new("RGBA", (S, S), FLOOR)
                if hk == 0:
                    cell.alpha_composite(base["right"][fi], (8, 8))
                else:
                    cell.alpha_composite(heat[(n, hk)]["fx"]["right"][fi].im)
                x = 70 + (hk * 2 + j) * (S * k + 4)
                img.paste(scaled(cell, k).convert("RGB"), (x, 20 + (n - 1) * (S * k + 4)))
                if n == 1:
                    dr.text((x + 4, 4), "heat%d f%d" % (hk, fi), fill=(235, 235, 235), font=FONT)
        dr.text((4, 20 + (n - 1) * (S * k + 4) + 90), "combo%d" % n, fill=(235, 235, 235), font=FONT)
    img.save(os.path.join(HERE, "preview_dagger_heat.png"))


def preview_mock_r49(res, slam, dash, reload_, heat):
    """월드 480×270 (카메라 2배 = 960×540): 위 = 대검 내리찍기 충격 순간 · 대쉬 베기 판정 · 칼 발도 판정, 아래 = 단검 3타 heat0→3 · 활 장전 f2/f3."""
    tiles = floor_tile()
    dummy = load_frames(os.path.join(SPR, "enemies", "dummy_idle.png"), 16, 24, DIRS)["left"][0]
    world = scene(480, 270, tiles, seed=21)
    # 대검 내리찍기 (충격 f4 + fx f2)
    foot = (70, 110)
    imp = slam["offs"]["right"]
    put(world, dummy, foot[0] + 40 - 8, foot[1] - 23 - 4)
    put(world, slam["fx"]["right"][2].im, foot[0] + imp["x"] - 48, foot[1] + imp["y"] - 48)
    _body_weapon(world, slam, "right", 4, foot)
    # 대쉬 베기 판정 f2 + 2타 fx f2
    foot = (230, 100)
    r2 = res["greatsword"][2]
    put(world, dummy, foot[0] + 34 - 8, foot[1] - 23)
    _body_weapon(world, dash, "right", 2, foot)
    put(world, r2["fx"]["right"][2].im, foot[0] - r2["fpivot"][0], foot[1] - r2["fpivot"][1])
    # 칼 발도 판정 f1 + fx f1
    foot = (390, 100)
    r1 = res["katana"][1]
    put(world, dummy, foot[0] + 24 - 8, foot[1] - 23)
    _body_weapon(world, r1, "right", 1, foot)
    put(world, r1["fx"]["right"][1].im, foot[0] - r1["fpivot"][0], foot[1] - r1["fpivot"][1])
    # 단검 3타 heat0..3
    r3 = res["dagger"][3]
    base = load_frames(os.path.join(OUT_FX, "dagger_combo3.png"), 64, 64, DIRS)
    for hk in range(4):
        foot = (30 + hk * 80, 225)
        _body_weapon(world, r3, "right", 1, foot)
        if hk == 0:
            put(world, base["right"][1], foot[0] - 32, foot[1] - 42)
        else:
            put(world, heat[(3, hk)]["fx"]["right"][1].im, foot[0] - 40, foot[1] - 50)
    # 활 장전
    for j, f in enumerate((1, 3)):
        _body_weapon(world, reload_, "down", f, (370 + j * 40, 225))
    world.save(os.path.join(HERE, "preview_mock_r49_1x.png"))
    big = scaled(world, 2)
    dr = ImageDraw.Draw(big)
    for (x, y, t) in ((20, 20, "greatsword slam (impact f4 + fx f2)"), (360, 20, "greatsword dashslash (hit f2 + combo2 fx)"),
                      (680, 20, "katana combo1 draw-cut (hit f1)"), (20, 290, "dagger combo3: heat0 / heat1 / heat2 / heat3"),
                      (700, 290, "bow reload f1 / f3")):
        dr.text((x, y), t, fill=(235, 235, 235), font=FONT)
    big.save(os.path.join(HERE, "preview_mock_r49_2x.png"))


def timeline_gif(name, r, d="right", fx=None, fx_at=None, fx_off=(0, 0), leap=None, k=3, W_=128, H_=80, travel=None):
    """몸+무기 시간축 GIF. fx 는 fx_at(ms)부터 겹침. leap = {frame: y오프셋}, travel = {frame: x 누적 이동} (시스템이 할 이동을 흉내)."""
    tiles = floor_tile()
    frames, durs = [], []
    t = 0
    for f, ms in enumerate(r["ms"]):
        for sub in range(0, ms, 10):
            tm = t + sub
            img = scene(W_, H_, tiles, seed=9)
            ox = (travel or {}).get(f, 0)
            foot = (40 + ox, H_ - 22)
            if fx is not None and fx_at is not None and tm >= fx_at:
                acc, fi = fx_at, None
                for j, m in enumerate(fx["fms"]):
                    if tm < acc + m:
                        fi = j
                        break
                    acc += m
                if fi is not None:
                    o = fx_off(d) if callable(fx_off) else fx_off
                    put(img, fx["fx"][d][fi].im, foot[0] + o[0] - fx["fpivot"][0], foot[1] + o[1] - fx["fpivot"][1])
            ly_ = (leap or {}).get(f, 0)
            _body_weapon(img, r, d, f, (foot[0], foot[1] + ly_))
            frames.append(scaled(img, k).convert("RGB").convert("P", palette=Image.ADAPTIVE))
            durs.append(10)
        t += ms
    # 같은 그림 합치기
    out, od = [], []
    for fr_, du in zip(frames, durs):
        if out and list(fr_.getdata()) == list(out[-1].getdata()):
            od[-1] += du
        else:
            out.append(fr_)
            od.append(du)
    od[-1] = max(od[-1], 500)
    out[0].save(os.path.join(HERE, "gif", "%s_%s.gif" % (name, d)), save_all=True, append_images=out[1:],
                duration=[max(20, x) for x in od], loop=0, disposal=2)


# ============================================================ 9. 미리보기
FLOOR = (0x21, 0x22, 0x24, 255)


def scaled(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def dep(r, d):
    """시트별 depth (49라운드: 가림을 구운 시트는 res["depth"]), 없으면 기존 규칙."""
    return r["depth"][d] if isinstance(r, dict) and "depth" in r else DEPTH[d]


def compose_cell(d, body, weapon, S, poff, bg=FLOOR, depth=None):
    cell = Image.new("RGBA", (S, S), bg)
    wim = weapon if isinstance(weapon, Image.Image) else weapon.im
    if (depth or DEPTH[d]) == "below":
        cell.alpha_composite(wim)
        cell.alpha_composite(body, poff)
    else:
        cell.alpha_composite(body, poff)
        cell.alpha_composite(wim)
    return cell


def load_frames(path, fw, fh, dirs):
    im = Image.open(path).convert("RGBA")
    n = im.width // fw
    return {d: [im.crop((c * fw, r * fh, c * fw + fw, r * fh + fh)) for c in range(n)] for r, d in enumerate(dirs)}


def preview_weapon(wid, res):
    k_body, k_fx = 4, 2
    blocks = []
    for n in (1, 2, 3):
        r = res[n]
        nf = len(r["ms"])
        cw = r["S"] * k_body
        nfx = len(r["fms"])
        fw = r["FS"] * k_fx
        width = 60 + nf * (cw + 4) + 20 + nfx * (fw + 4)
        height = 34 + 4 * (max(cw, fw) + 4)
        blk = Image.new("RGB", (width, height), (34, 34, 38))
        dr = ImageDraw.Draw(blk)
        memo = combo_memo(wid, n)
        rng = ("R%d arc %d°" % (memo["hitRadiusPx"], memo["arcDeg"])) if "hitRadiusPx" in memo else \
              ("thrust %dx%d" % (memo["thrust"]["lengthPx"], memo["thrust"]["widthPx"]))
        dr.text((4, 2), "%s_combo%d  body+weapon %s ms · hit f%s · cancel f%s · %s   |   fx %dx%d %s ms (f1 = hit)" % (
            wid, n, r["ms"], memo["hitFrames"], memo["cancelFromFrame"], rng, r["FS"], r["FS"], r["fms"]), fill=(235, 235, 235), font=FONT)
        for ri, d in enumerate(DIRS):
            y = 30 + ri * (max(cw, fw) + 4)
            dr.text((4, y + 20), d, fill=(220, 220, 220), font=FONT)
            for c_ in range(nf):
                cell = compose_cell(d, r["bodies"][d][c_], r["weapons"][d][c_], r["S"], r["poff"], depth=dep(r, d))
                blk.paste(scaled(cell, k_body).convert("RGB"), (60 + c_ * (cw + 4), y))
            ox = 60 + nf * (cw + 4) + 20
            # 이펙트 칸: 판정 프레임 몸+무기를 피벗에 맞춰 함께
            hb = r["bodies"][d][r.get("hitf", 1)]
            hw = r["weapons"][d][r.get("hitf", 1)].im
            for c_ in range(nfx):
                cell = Image.new("RGBA", (r["FS"], r["FS"]), FLOOR)
                px0 = r["fpivot"][0] - r["wpivot"][0]
                py0 = r["fpivot"][1] - r["wpivot"][1]
                tmp = Image.new("RGBA", (r["S"], r["S"]), (0, 0, 0, 0))
                if dep(r, d) == "below":
                    tmp.alpha_composite(hw); tmp.alpha_composite(hb, r["poff"])
                else:
                    tmp.alpha_composite(hb, r["poff"]); tmp.alpha_composite(hw)
                cell.alpha_composite(tmp, (px0, py0))
                cell.alpha_composite(r["fx"][d][c_].im)
                blk.paste(scaled(cell, k_fx).convert("RGB"), (ox + c_ * (fw + 4), y))
        blocks.append(blk)
    Wd = max(b.width for b in blocks) + 16
    Hd = sum(b.height + 8 for b in blocks) + 8
    img = Image.new("RGB", (Wd, Hd), (22, 22, 26))
    y = 8
    for b in blocks:
        img.paste(b, (8, y)); y += b.height + 8
    img.save(os.path.join(HERE, "preview_%s.png" % wid))


def preview_specials(sres, bres):
    k = 4
    over = {
        "parry_flash": load_frames(os.path.join(SPR, "fx", "parry_flash.png"), 48, 48, ["any"]),
        "guard_wave": load_frames(os.path.join(SPR, "fx", "guard_wave.png"), 64, 32, DIRS),
        "shadowstep_ghost": load_frames(os.path.join(SPR, "fx", "shadowstep_ghost.png"), 16, 24, DIRS),
        "aim_charge": load_frames(os.path.join(SPR, "fx", "aim_charge.png"), 32, 32, ["any"]),
    }
    blocks = []
    items = [("katana_special", sres["katana"]), ("greatsword_special", sres["greatsword"]),
             ("dagger_special", sres["dagger"]), ("bow_aim", bres)]
    for name, r in items:
        nf = len(r["ms"])
        S = 64
        cw = S * k
        blk = Image.new("RGB", (60 + 2 * nf * (cw + 4) + 30, 24 + 4 * (cw + 4)), (34, 34, 38))
        dr = ImageDraw.Draw(blk)
        dr.text((4, 2), "%s  %s ms   (left: body+weapon  |  right: + existing aux fx overlay)" % (name, r["ms"]), fill=(235, 235, 235), font=FONT)
        for ri, d in enumerate(DIRS):
            y = 22 + ri * (cw + 4)
            dr.text((4, y + 20), d, fill=(220, 220, 220), font=FONT)
            for c_ in range(nf):
                base = compose_cell(d, r["bodies"][d][c_], r["weapons"][d][c_], r["S"], r["poff"], bg=(0, 0, 0, 0), depth=dep(r, d))
                cell = Image.new("RGBA", (S, S), FLOOR)
                o = (S - r["S"]) // 2
                cell.alpha_composite(base, (o, o))
                blk.paste(scaled(cell, k).convert("RGB"), (60 + c_ * (cw + 4), y))
                # 오버레이
                cell2 = cell.copy()
                foot = (S // 2, S // 2 + 15)   # 64 칸에서 주인공 발 = (32, 47)
                if name == "katana_special" and c_ in (2, 3):
                    fxf = over["parry_flash"]["any"][min(c_ - 2, 4)]
                    fv = {"right": (12, 0), "left": (-12, 0), "down": (0, 6), "up": (0, -16)}[d]
                    cell2.alpha_composite(fxf, (foot[0] - 24 + fv[0], foot[1] - 10 - 24 + fv[1]))
                if name == "greatsword_special" and c_ >= 4:
                    gw = over["guard_wave"][d][min(c_ - 4, 3)]
                    tmp = Image.new("RGBA", (S, S), (0, 0, 0, 0))
                    tmp.alpha_composite(gw, (foot[0] - 32, foot[1] - 16))
                    under = Image.new("RGBA", (S, S), FLOOR)
                    under.alpha_composite(tmp)
                    under.alpha_composite(base, (o, o))
                    cell2 = under
                if name == "dagger_special" and c_ >= 2:
                    gh = over["shadowstep_ghost"][d][min(c_ - 2, 2)]
                    back = {"right": -18, "left": 18, "down": 0, "up": 0}[d]
                    backy = {"down": -14, "up": 14}.get(d, 0)
                    under = Image.new("RGBA", (S, S), FLOOR)
                    under.alpha_composite(gh, (foot[0] - 8 + back, foot[1] - 23 + backy))
                    under.alpha_composite(base, (o, o))
                    cell2 = under
                if name == "bow_aim" and c_ <= 5:
                    ac = over["aim_charge"]["any"][min(5, c_)]
                    cell2.alpha_composite(ac, (foot[0] - 16, foot[1] - 10 - 16))
                blk.paste(scaled(cell2, k).convert("RGB"), (60 + nf * (cw + 4) + 30 + c_ * (cw + 4), y))
        blocks.append(blk)
    Wd = max(b.width for b in blocks) + 16
    Hd = sum(b.height + 8 for b in blocks) + 8
    img = Image.new("RGB", (Wd, Hd), (22, 22, 26))
    y = 8
    for b in blocks:
        img.paste(b, (8, y)); y += b.height + 8
    img.save(os.path.join(HERE, "preview_specials.png"))


def floor_tile():
    """목업 바닥: 1층 시트의 바닥 0번(다른 에이전트가 고치는 중일 수 있어 실패하면 G02 단색)."""
    try:
        im = Image.open(os.path.join(ROOT, "assets", "tiles", "stage1.png")).convert("RGBA")
        with open(os.path.join(ROOT, "assets", "tiles", "stage1.json"), encoding="utf-8") as fp:
            j = json.load(fp)
        idx = j["tiles"]["1"]
        cols = im.width // 16
        return [im.crop(((i % cols) * 16, (i // cols) * 16, (i % cols) * 16 + 16, (i // cols) * 16 + 16)) for i in idx]
    except Exception:
        t = Image.new("RGBA", (16, 16), G(2))
        return [t]


def scene(w, h, tiles, seed=0):
    img = Image.new("RGBA", (w, h), G(1))
    for ty in range(0, h, 16):
        for tx in range(0, w, 16):
            hsh = ((tx * 73856093) ^ (ty * 19349663) ^ seed) & 0xffff
            img.alpha_composite(tiles[hsh % len(tiles)], (tx, ty))
    return img


def put(img, sprite, x, y):
    """음수 좌표도 허용(잘라서 붙임)."""
    x, y = int(round(x)), int(round(y))
    sx, sy = max(0, -x), max(0, -y)
    if sx >= sprite.width or sy >= sprite.height:
        return
    src = sprite.crop((sx, sy, sprite.width, sprite.height))
    x, y = x + sx, y + sy
    if x >= img.width or y >= img.height:
        return
    src = src.crop((0, 0, min(src.width, img.width - x), min(src.height, img.height - y)))
    img.alpha_composite(src, (x, y))


def mock_snapshot(wid, n, res, dummy, tiles, fxf=1, bodyf=1, d="right", w=160, h=90):
    """월드 w×h. 주인공 발 = (54, 58) 근처, 오른쪽(또는 d)을 보고 n타 판정 순간. 허수아비 3개를 판정 반경 근처에."""
    r = res[n]
    img = scene(w, h, tiles, seed=n * 7 + len(wid))
    foot = (52, 60) if d == "right" else (w // 2, 30)
    cx, cy = foot[0], foot[1] - BODY_CENTER_DY
    R = HIT[wid] if wid in HIT else 24
    memo = combo_memo(wid, n)
    if "arcFromDeg" in memo:
        a0, a1 = memo["arcFromDeg"], memo["arcToDeg"]
        angs = [to_screen(d, a0 + (a1 - a0) * t) for t in (0.2, 0.5, 0.85)]
        dists = [R - 6, R - 4, R - 7]
    else:
        th = memo["thrust"]["angleDeg"]
        angs = [to_screen(d, th)]
        dists = [memo["thrust"]["lengthPx"] - 5]
        angs += [to_screen(d, 70), to_screen(d, -60)]
        dists += [R + 14, R + 16]
    dummies = []
    for a, dist in zip(angs, dists):
        ux, uy = unit(a)
        dummies.append((cx + ux * dist, cy + uy * dist + BODY_CENTER_DY))
    dummies.sort(key=lambda p: p[1])
    bodyf = r.get("hitf", bodyf)
    body = r["bodies"][d][bodyf]
    weap = r["weapons"][d][bodyf].im
    fx = r["fx"][d][fxf].im
    # 깊이 정렬: 발 y 가 작은 허수아비부터, 주인공, 이펙트(위)
    for (x, y) in dummies:
        if y <= foot[1]:
            put(img, dummy, x - 8, y - 23)
    if dep(r, d) == "below":
        put(img, weap, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])
    put(img, body, foot[0] - 8, foot[1] - 23)
    if dep(r, d) == "above":
        put(img, weap, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])
    for (x, y) in dummies:
        if y > foot[1]:
            put(img, dummy, x - 8, y - 23)
    put(img, fx, foot[0] - r["fpivot"][0], foot[1] - r["fpivot"][1])
    return img


def preview_mock(allres):
    """카메라 2배: 월드 480×270 = 화면 960×540. 3행(무기) × 3열(1·2·3타 판정 순간) 미니 장면 160×90."""
    tiles = floor_tile()
    dummy = load_frames(os.path.join(SPR, "enemies", "dummy_idle.png"), 16, 24, DIRS)["left"][0]
    world = Image.new("RGBA", (480, 270), (0, 0, 0, 255))
    for ri, wid in enumerate(("katana", "greatsword", "dagger")):
        for n in (1, 2, 3):
            snap = mock_snapshot(wid, n, allres[wid], dummy, tiles, fxf=1 if wid != "greatsword" else 2)
            world.alpha_composite(snap, ((n - 1) * 160, ri * 90))
    d = ImageDraw.Draw(world)
    for i in (1, 2):
        d.line([(i * 160, 0), (i * 160, 269)], fill=(0, 0, 0, 255))
        d.line([(0, i * 90), (479, i * 90)], fill=(0, 0, 0, 255))
    world.save(os.path.join(HERE, "preview_mock_1x.png"))
    big = scaled(world, 2)
    dr = ImageDraw.Draw(big)
    for ri, wid in enumerate(("katana", "greatsword", "dagger")):
        for n in (1, 2, 3):
            dr.text(((n - 1) * 320 + 6, ri * 180 + 4), "%s %d" % (wid, n), fill=(235, 235, 235), font=FONT)
    big.save(os.path.join(HERE, "preview_mock_2x.png"))
    # 아래 방향도 한 장 (회전 이펙트 확인)
    world2 = Image.new("RGBA", (480, 270), (0, 0, 0, 255))
    for ri, wid in enumerate(("katana", "greatsword", "dagger")):
        for n in (1, 2, 3):
            snap = mock_snapshot(wid, n, allres[wid], dummy, tiles, fxf=1 if wid != "greatsword" else 2, d="down", w=160, h=90)
            world2.alpha_composite(snap, ((n - 1) * 160, ri * 90))
    scaled(world2, 2).save(os.path.join(HERE, "preview_mock_2x_down.png"))


def chain_gif(wid, res, d="right", k=3):
    """1→2→3타를 가장 빠른 취소 시각으로 이은 시간축 GIF (카메라 2배 × 보기용 1.5 = 3배). 10ms 단위로 상태 변화마다 프레임."""
    tiles = floor_tile()
    dummy = load_frames(os.path.join(SPR, "enemies", "dummy_idle.png"), 16, 24, DIRS)["left"][0]
    segs = []
    t = 0
    for n in (1, 2, 3):
        cb = COMBOS[wid][n]
        end = sum(cb["ms"][:cb["cancel"]]) if cb["cancel"] is not None else sum(cb["ms"])
        segs.append((n, t, end))
        t += end
    total = t + 400
    # 이펙트: 판정 시각 - 40ms 부터
    fx_starts = []
    for n, t0, _ in segs:
        hit_at = t0 + sum(COMBOS[wid][n]["ms"][:COMBOS[wid][n]["hit"][0]])
        fx_starts.append((n, hit_at - 40))
    frames, durs = [], []
    last_key = None
    for tm in range(0, total, 10):
        cur = None
        for n, t0, end in segs:
            if t0 <= tm < t0 + (end if n < 3 else sum(COMBOS[wid][n]["ms"])):
                cur = (n, tm - t0)
        body_state = None
        if cur:
            n, dt = cur
            ms = COMBOS[wid][n]["ms"]
            acc = 0
            for fi, m in enumerate(ms):
                if dt < acc + m:
                    body_state = (n, fi)
                    break
                acc += m
        fx_state = []
        for n, s in fx_starts:
            fms = res[n]["fms"]
            if s <= tm < s + sum(fms):
                acc = 0
                for fi, m in enumerate(fms):
                    if tm - s < acc + m:
                        fx_state.append((n, fi))
                        break
                    acc += m
        key = (body_state, tuple(fx_state))
        if key == last_key:
            durs[-1] += 10
            continue
        last_key = key
        img = scene(200, 110, tiles, seed=3)
        foot = (70, 70)
        R = HIT[wid]
        for a, dist in ((-30, R - 6), (10, R - 4), (45, R - 7)):
            ux, uy = unit(to_screen(d, a))
            put(img, dummy, foot[0] + ux * dist - 8, foot[1] - BODY_CENTER_DY + uy * dist - 13)
        if body_state:
            n, fi = body_state
            r = res[n]
            if dep(r, d) == "below":
                put(img, r["weapons"][d][fi].im, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])
            put(img, r["bodies"][d][fi], foot[0] - 8, foot[1] - 23)
            if dep(r, d) == "above":
                put(img, r["weapons"][d][fi].im, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])
        else:
            idle = load_frames(os.path.join(SPR, "player", "player_idle.png"), 16, 24, DIRS)[d][0]
            put(img, idle, foot[0] - 8, foot[1] - 23)
        for n, fi in fx_state:
            r = res[n]
            put(img, r["fx"][d][fi].im, foot[0] - r["fpivot"][0], foot[1] - r["fpivot"][1])
        frames.append(scaled(img, k).convert("RGB").convert("P", palette=Image.ADAPTIVE))
        durs.append(10)
    durs = [max(20, x) for x in durs]
    durs[-1] = 500
    frames[0].save(os.path.join(HERE, "gif", "%s_chain_%s.gif" % (wid, d)), save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, disposal=2)


def preview_strip_1x(allres):
    """1배 실크기 띠: 각 무기 1·2·3타 판정 프레임(몸+무기+fx f1) 4방향."""
    tiles = floor_tile()
    cell = 128
    img = Image.new("RGBA", (cell * 4 * 3 + 40, cell * 3 + 10), (0, 0, 0, 255))
    for ri, wid in enumerate(("katana", "greatsword", "dagger")):
        for n in (1, 2, 3):
            r = allres[wid][n]
            for di, d in enumerate(DIRS):
                bg = scene(cell, cell, tiles, seed=di)
                foot = (64, 74)
                hf = r.get("hitf", 1)
                if dep(r, d) == "below":
                    put(bg, r["weapons"][d][hf].im, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])
                put(bg, r["bodies"][d][hf], foot[0] - 8, foot[1] - 23)
                if dep(r, d) == "above":
                    put(bg, r["weapons"][d][hf].im, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])
                put(bg, r["fx"][d][1 if wid != "greatsword" else 2].im, foot[0] - r["fpivot"][0], foot[1] - r["fpivot"][1])
                img.alpha_composite(bg, (((n - 1) * 4 + di) * cell + (n - 1) * 20, ri * cell + ri * 5))
    img.save(os.path.join(HERE, "preview_strip_1x.png"))


def main():
    allres = {}
    for wid in ("katana", "greatsword", "dagger"):
        allres[wid] = {}
        for n in (1, 2, 3):
            allres[wid][n] = build_combo(wid, n)
    sres = {wid: build_special(wid) for wid in ("katana", "greatsword", "dagger")}
    bres = build_bow_aim()
    for wid in ("katana", "greatsword", "dagger"):
        preview_weapon(wid, allres[wid])
        chain_gif(wid, allres[wid])
    preview_specials(sres, bres)
    preview_mock(allres)
    preview_strip_1x(allres)
    # 49라운드
    slam = build_slam()
    dash = build_dashslash()
    heat = build_dagger_heat()
    rel = build_bow_reload()
    imp = SLAM["impact"]
    preview_actions([("player_greatsword_slam + weapons + fx/greatsword_slam (impact f%d)" % imp, slam,
                      {f: (slam, f - imp, lambda d: (slam["offs"][d]["x"], slam["offs"][d]["y"])) for f in range(imp, imp + 4)}),
                     ("player_greatsword_dashslash + weapons (fx = greatsword_combo2 reuse)", dash,
                      {2: (allres["greatsword"][2], 1, None), 3: (allres["greatsword"][2], 2, None)}),
                     ("player_bow_reload + weapons/bow_reload", rel, None)],
                    os.path.join(HERE, "preview_r49_actions.png"), cell=80)
    preview_heat(heat)
    preview_mock_r49(allres, slam, dash, rel, heat)
    timeline_gif("greatsword_slam", slam, fx=slam, fx_at=sum(SLAM["ms"][:imp]),
                 fx_off=lambda d: (slam["offs"][d]["x"], slam["offs"][d]["y"]), leap={2: -3, 3: -2},
                 travel={2: 6, 3: 12, 4: 14, 5: 14, 6: 14, 7: 14}, W_=150)
    timeline_gif("greatsword_dashslash", dash, fx=dict(allres["greatsword"][2], fms=allres["greatsword"][2]["fms"]),
                 fx_at=sum(DASHSLASH["ms"][:2]) - 40, travel={0: 6, 1: 20, 2: 34, 3: 42, 4: 46, 5: 46, 6: 46}, W_=170)
    timeline_gif("bow_reload", rel, d="down")
    bad = [r for r in REPORT if not r[1]]
    print("\n%d sheets checked, %d CHECK" % (len(REPORT), len(bad)))


if __name__ == "__main__":
    main()
