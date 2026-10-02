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
        1: dict(frames=[(-115, 5, -1, 0, 0, "ghost"), (-15, 5, 1, 0, 0, "glow"), (60, 5, 1, 1, 0, "steel"), (95, 4, 0, 0, 0, "fade")],
                ms=[90, 40, 120, 100], hit=[1], cancel=3, arc=(-70, 70)),
        2: dict(frames=[(100, 5, 0, 0, 0, "steel"), (10, 5, 1, 0, 0, "glow"), (-85, 5, 0, 0, 0, "fade")],
                ms=[40, 40, 90], hit=[1], cancel=2, arc=(65, -65)),
        3: dict(frames=[(-125, 5, -1, 0, 0, "steel"), (-5, 5, 1, 0, 0, "glow"), (75, 5, 2, 1, 0, "steel"), (100, 4, 1, 1, 0, "embers")],
                ms=[40, 40, 100, 140], hit=[1], cancel=None, arc=(-85, 85)),
    },
    "greatsword": {   # "훙 훙 훙" — 셋 다 무겁고 고른 간격, 3타가 가장 크다(270°). 1·3타 위→아래, 2타 아래→위(교차)
        1: dict(frames=[(-135, 5, -1, 0, 0, "ghost"), (-35, 5, 0, 0, 0, "glow"), (55, 5, 1, 1, 0, "steel"), (90, 4, 1, 1, 0, "fade")],
                ms=[160, 60, 120, 140], hit=[1], cancel=3, arc=(-110, 80)),
        2: dict(frames=[(115, 5, 0, 1, 0, "steel"), (25, 5, 0, 0, 0, "glow"), (-80, 5, 0, 0, 0, "steel"), (-110, 4, -1, 0, 0, "fade")],
                ms=[140, 60, 120, 140], hit=[1], cancel=3, arc=(100, -100)),
        3: dict(frames=[(-165, 5, -1, 0, 0, "steel"), (-60, 5, 0, 0, 0, "glow"), (40, 5, 1, 1, 0, "glow"), (95, 5, 1, 2, 1, "steel"), (100, 4, 0, 1, 0, "embers")],
                ms=[200, 60, 70, 140, 180], hit=[1], active=[1, 2], cancel=None, arc=(-150, 120)),
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
    memo = combo_memo(wid, n)
    name = "%s_combo%d" % (wid, n)
    save_png_json(OUT_P, "player_" + name, bodies, PW, PH, ms, False, (8, 23), PAL_PLAYER,
                  dict(memo, note="무기를 든 연격 몸 동작. weapons/%s 를 같은 프레임 번호·같은 시각에 겹친다(§6.1)." % name), name)
    save_png_json(OUT_W, name, weapons, S, S, ms, False, wpivot, PAL_WEAPON,
                  dict(memo, anchor="player_pivot", depth=DEPTH, playerFrameOffset={"x": poff[0], "y": poff[1]},
                       overlay="player_%s 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 (%d,%d) = 주인공 피벗 (8,23)." % (name, wpivot[0], wpivot[1]),
                       frameStates=[f[5] for f in cb["frames"]],
                       stateNote="ghost 실체화(호박 윤곽) · steel · glow 판정 프레임(날끝 글로우) · fade 흩어짐(다음 타로 넘어가면 보이지 않음) · embers 불티(연격 끝)"),
                  name.split("_", 1)[1])
    check("player_" + name, "player", bodies)
    check("weapons/" + name, "weapon", weapons)
    # 이펙트
    fbd, fms, FS = FX_BUILDERS[wid](n)
    fpivot = (FS // 2, FS // 2 + BODY_CENTER_DY)
    extra = dict(memo, anchor="player_pivot", spawn="attack_frame2", impactFrame=1,
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
    return dict(bodies=bodies, weapons=weapons, fx=fbd, ms=ms, fms=fms, S=S, poff=poff, FS=FS, fpivot=fpivot, wpivot=wpivot)


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


# ============================================================ 9. 미리보기
FLOOR = (0x21, 0x22, 0x24, 255)


def scaled(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def compose_cell(d, body, weapon, S, poff, bg=FLOOR):
    cell = Image.new("RGBA", (S, S), bg)
    wim = weapon if isinstance(weapon, Image.Image) else weapon.im
    if DEPTH[d] == "below":
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
                cell = compose_cell(d, r["bodies"][d][c_], r["weapons"][d][c_], r["S"], r["poff"])
                blk.paste(scaled(cell, k_body).convert("RGB"), (60 + c_ * (cw + 4), y))
            ox = 60 + nf * (cw + 4) + 20
            # 이펙트 칸: 판정 프레임 몸+무기를 피벗에 맞춰 함께
            hb = r["bodies"][d][1]
            hw = r["weapons"][d][1].im
            for c_ in range(nfx):
                cell = Image.new("RGBA", (r["FS"], r["FS"]), FLOOR)
                px0 = r["fpivot"][0] - r["wpivot"][0]
                py0 = r["fpivot"][1] - r["wpivot"][1]
                tmp = Image.new("RGBA", (r["S"], r["S"]), (0, 0, 0, 0))
                if DEPTH[d] == "below":
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
                base = compose_cell(d, r["bodies"][d][c_], r["weapons"][d][c_], r["S"], r["poff"], bg=(0, 0, 0, 0))
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
    body = r["bodies"][d][bodyf]
    weap = r["weapons"][d][bodyf].im
    fx = r["fx"][d][fxf].im
    # 깊이 정렬: 발 y 가 작은 허수아비부터, 주인공, 이펙트(위)
    for (x, y) in dummies:
        if y <= foot[1]:
            put(img, dummy, x - 8, y - 23)
    if DEPTH[d] == "below":
        put(img, weap, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])
    put(img, body, foot[0] - 8, foot[1] - 23)
    if DEPTH[d] == "above":
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
            if DEPTH[d] == "below":
                put(img, r["weapons"][d][fi].im, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])
            put(img, r["bodies"][d][fi], foot[0] - 8, foot[1] - 23)
            if DEPTH[d] == "above":
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
                if DEPTH[d] == "below":
                    put(bg, r["weapons"][d][1].im, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])
                put(bg, r["bodies"][d][1], foot[0] - 8, foot[1] - 23)
                if DEPTH[d] == "above":
                    put(bg, r["weapons"][d][1].im, foot[0] - r["wpivot"][0], foot[1] - r["wpivot"][1])
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
    bad = [r for r in REPORT if not r[1]]
    print("\n%d sheets checked, %d CHECK" % (len(REPORT), len(bad)))


if __name__ == "__main__":
    main()
