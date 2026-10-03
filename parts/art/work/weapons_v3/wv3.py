"""무기 v3 공통 (53라운드 Q26~Q32 무기 재디자인) — hero_v3 몸 Rig·칼 3D 도구를 그대로 쓴다.

좌표·각도 규약은 hero_v3/katana3.py 와 같다: 로컬 (f 앞, r 해부 오른쪽, z 위), θ(0 = 앞, + = 해부 오른쪽), elev(+ = 위).
무기 시트 192×192 · 피벗 (96,186) = 몸 피벗 (48,138) · playerFrameOffset (48,48) · pixelScale 0.5 · 항상 above + occlusionBaked.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HV3 = os.path.normpath(os.path.join(HERE, "..", "hero_v3"))
sys.path.insert(0, HV3)

import anim  # noqa: E402
import export as EX  # noqa: E402
import export2 as E2  # noqa: E402
import gear3 as Q  # noqa: E402
import hero  # noqa: E402
import katana3 as K  # noqa: E402
import motion  # noqa: E402
import preview as PV  # noqa: E402
from v3kit import kit, colors_of, has_alpha_partial  # noqa: E402

DIRS = hero.DIRS
G, A, SL, WD, PL, OUT = hero.G, hero.A, hero.SL, hero.WD, hero.PL, hero.OUT
SRC = "parts/art/work/weapons_v3/build.py (53라운드 Q26~Q32 무기 재디자인 — v3 도트 오버레이)"
PV.HERE = HERE                                     # 미리보기는 이 폴더에 쓴다


def hero_palette():
    st = json.load(open(os.path.join(HV3, "stats.json"), encoding="utf-8"))
    return {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in st["heroPalette"]}


def add(a, b, k=1.0):
    return K.add(a, b, k)


def norm3(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def rasterize(L, R, hold_hands=(), off=(K.OFF, K.OFF), size=(K.WF, K.WF)):
    """K.rasterize 와 같은 규칙(몸 뒤 픽셀은 실루엣으로 지움 · 쥔 손 위 손잡이 지움)을 임의 크기 캔버스에(대검 확대 틀)."""
    from PIL import Image
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    po = im.load()
    body = R.image.load()
    hands = [hero.to_px(R.anchors[n]) for n in hold_hands if R.anchors.get(n)]
    for (x, y), (c, gy, kind, prio) in L.px.items():
        inside = 0 <= x < hero.FW and 0 <= y < hero.FH and body[x, y][3] > 0
        if inside and gy < 0 and kind != "glint":
            continue
        if inside and kind in K.HIDE_UNDER_HAND and hands:
            part = R.part_at(x, y) or ""
            if part.startswith("hand") and any(math.hypot(x - hx_, y - hy) < 6.5 for hx_, hy in hands):
                continue
        wx, wy = x + off[0], y + off[1]
        if 0 <= wx < size[0] and 0 <= wy < size[1]:
            po[wx, wy] = c
    return im


fill_blade = K.fill_blade                         # 넓은 날 래스터(hero_v3/katana3.py — 칼·대검·단검 공용)


# =============================================================================
# 왼손이 빈 기본 자세 (53라운드 Q19) — 칼 외 무기의 대기·걷기·달리기 몸. 대쉬는 원래 왼손이 비어 있어 player_dash 를 같이 쓴다.
# =============================================================================
FREE = ("idle", "walk", "run")
FREE_NOTE = ("왼손이 빈 기본 자세(53라운드 Q19). player_<동작> 과 같은 골격·프레임·ms·보폭이며, 왼손만 칼집을 쥐지 않고 "
             "자연스럽게 내리거나(대기) 흔든다(걷기·달리기). 칼 외 무기(대검·단검·활)의 휴대 오버레이를 이 시트 위에 겹친다.")
BODY_RULE = {
    "katana": {"idle": "player_idle", "walk": "player_walk", "run": "player_run", "dash": "player_dash"},
    "greatsword": {"idle": "player_idle_free", "walk": "player_walk_free", "run": "player_run_free", "dash": "player_dash"},
    "dagger": {"idle": "player_idle_free", "walk": "player_walk_free", "run": "player_run_free", "dash": "player_dash"},
    "bow": {"idle": "player_idle_free", "walk": "player_walk_free", "run": "player_run_free", "dash": "player_dash"},
}
BODY_RULE_NOTE = ("무기별 이동 몸 시트 선택 규칙(아트 제안): bodySheetByWeapon[무기][동작]. 칼만 칼집을 쥔 player_<동작>, "
                  "나머지는 왼손이 빈 player_<동작>_free. 대쉬는 모든 무기가 player_dash. 오버레이는 <무기>_carry_<동작>"
                  "(대검·칼은 뽑아 든 상태면 <무기>_carry_drawn_<동작>).")


def render_free(act):
    gen, ms, loop = anim.BODY[act]
    out = {}
    for d in DIRS:
        frames = []
        for p in gen(d):
            R = hero.draw_rig(d, p)
            frames.append(anim.Frame(motion.apply_post(R.image, R, d, p), R, p))
        assert len(frames) == len(ms), (act, d)
        out[d] = frames
    return out


def export_free(act, frames):
    _, ms, loop = anim.BODY[act]
    im = EX.sheet({d: [f.image for f in frames[d]] for d in DIRS}, hero.FW, hero.FH)
    name = "player_%s_free" % act
    im.save(os.path.join(EX.OUT_P, name + ".png"))
    hands = {d: [anim.hands_px(f.rig) for f in frames[d]] for d in DIRS}
    data = EX.base(name + ".png", act + "_free", hero.FW, hero.FH, ms, loop, hero.PIV, emissiveColors=EX.EMISSIVE,
                   **EX.body_meta(act), handAnchors=hands,
                   anchorNote="handAnchors = 프레임별 손 중심(몸 시트 도트, 해부 기준 R 오른손 · L 왼손). 무기 시트 좌표 = 몸 + (48,48).",
                   scarAnchor=EX.scar_list(frames, act), scarAnchorNote=EX.SCAR_NOTE,
                   variantOf="player_%s" % act, freeLeftHand=True,
                   carryOverlays={w: "weapons/v3/%s_carry_%s" % (w, act) for w in ("greatsword", "dagger", "bow")},
                   carryDrawnOverlays={"greatsword": "weapons/v3/greatsword_carry_drawn_%s" % act},
                   bodySheetByWeapon={w: r[act] for w, r in BODY_RULE.items()}, bodySheetRuleNote=BODY_RULE_NOTE,
                   note=FREE_NOTE + " " + EX.BODY_NOTE)
    data["source"] = SRC
    EX.write_json(os.path.join(EX.OUT_P, name + ".json"), data)
    return im


# =============================================================================
# 오버레이 JSON (칼 v3 규약: pixelScale 0.5 · playerFrameOffset · gripAnchors · bladeLocal · occlusionBaked · carryHidden)
# =============================================================================
BODY_ONLY = {"image", "frameWidth", "frameHeight", "pivot", "handAnchors", "anchorNote", "scarAnchor", "scarAnchorNote",
             "emissiveColors", "weaponTipDots", "weaponTipNote", "oldWeapon", "weaponOverlayV3", "weaponOverlayNote", "note",
             "source", "weaponLocal", "weaponLocalNote", "impactOffsetPx", "unitNote", "timingCheck"}


def to_w(pt, off=(K.OFF, K.OFF)):
    return [round(pt[0] + off[0], 1), round(pt[1] + off[1], 1)]


STD_FRAME = (K.WF, K.WF, K.OFF, K.OFF)             # (폭, 높이, 몸 x 오프셋, 몸 y 오프셋) — 칼·단검·활


def write_overlay(name, imgs, ms, loop, action, weapon, hands, grip_hand, design, extra=None, body_meta=None, frame=STD_FRAME):
    """imgs: {dir: [RGBA 틀 크기]} · hands: {dir: [{handR, handL} 몸 도트]} → 시트·JSON. body_meta = 몸 JSON(타이밍 필드를 옮김).
    frame = (W, H, ox, oy): 피벗 = (ox + 48, oy + 138), playerFrameOffset = (ox, oy)."""
    fw, fh, ox, oy = frame
    piv = (ox + hero.PIV[0], oy + hero.PIV[1])
    im = EX.sheet(imgs, fw, fh)
    im.save(os.path.join(EX.OUT_W, name + ".png"))
    n = len(ms)
    meta = {k: v for k, v in (body_meta or {}).items() if k not in BODY_ONLY and k not in EX.base("", "", 0, 0, ms, loop, (0, 0))}
    whands = {d: [{k: to_w(v, (ox, oy)) for k, v in h.items()} for h in hands[d]] for d in DIRS}
    data = EX.base(name + ".png", action, fw, fh, ms, loop, piv, **meta)
    data.update(weapon=weapon, anchor="player_pivot", playerFrameOffset={"x": ox, "y": oy},
                depth={d: "above" for d in DIRS}, depthByFrame={d: ["above"] * n for d in DIRS}, occlusionBaked=True,
                depthNote="몸 뒤로 가는 무기 픽셀(몸 기준 카메라 반대쪽)은 몸 실루엣으로 지웠고, 쥔 손잡이는 주먹 픽셀로 가렸다 → 항상 above.",
                handAnchors=whands, gripAnchors={d: [h.get(grip_hand) for h in whands[d]] for d in DIRS},
                gripHand=grip_hand, source=SRC, **design)
    data.update(extra or {})
    EX.write_json(os.path.join(EX.OUT_W, name + ".json"), data)
    return im


def check_gear_timing(name, ms, body_json):
    """구 시트(16×24) 대조: 구 프레임 시작 ms·전체·timingMs 항목·판정 끝이 같다(export2.check_timing 재사용) + 몸 JSON 과 ms 동일."""
    seq, first, groups, old = Q.expand(name)
    assert [m for _, m, _ in seq] == list(ms) == body_json["frameDurationsMs"], (name, "ms")
    m = E2.remap_meta(old, first, groups, len(ms))
    return E2.check_timing(name, old, ms, first, m)


# =============================================================================
# 미리보기
# =============================================================================
def compose(body, weapon, frame=STD_FRAME):
    from PIL import Image
    c = Image.new("RGBA", frame[:2], (0, 0, 0, 0))
    c.alpha_composite(body, frame[2:])
    if weapon is not None:
        c.alpha_composite(weapon)
    return c


def previews(name, bodies, weapons, ms, states=None, active=(), impact=None, gif=True, frame=STD_FRAME):
    """hero_v3/preview 의 2배·3배 미리보기를 틀 크기에 맞춰 부른다(틀 상수를 잠시 바꿈 — 칼·단검·활은 192 그대로)."""
    comp = {d: [compose(b, w, frame) for b, w in zip(bodies[d], weapons[d])] for d in DIRS}
    saved = (K.WF, K.OFF, PV.PIV)
    K.WF, K.OFF = max(frame[:2]), frame[2]
    PV.PIV = (hero.PIV[0], hero.PIV[1] + frame[3] - frame[2])
    try:
        PV.frames_x2(name, comp, ms, impact=impact, active=active, states=states)
        if gif:
            PV.gif_x3(name, comp, ms)
    finally:
        K.WF, K.OFF, PV.PIV = saved
    return comp


def fit_frame(all_imgs, canvas_off, margin=2, step=8):
    """큰 캔버스 그림들의 합집합 상자(+ 몸 사각형) → (W, H, ox, oy, 자르기 상자). W·H 는 step 배수."""
    box = [canvas_off[0], canvas_off[1], canvas_off[0] + hero.FW, canvas_off[1] + hero.FH]
    for imgs in all_imgs:
        for d in DIRS:
            for im in imgs[d]:
                b = im.getbbox()
                if b:
                    box = [min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3])]
    x0, y0 = box[0] - margin, box[1] - margin
    W = -(-(box[2] + margin - x0) // step) * step
    H = -(-(box[3] + margin - y0) // step) * step
    return (W, H, canvas_off[0] - x0, canvas_off[1] - y0), (x0, y0, x0 + W, y0 + H)


def edge_px(imgs):
    return sum(EX.edge_pixels(f) for d in DIRS for f in imgs[d])
