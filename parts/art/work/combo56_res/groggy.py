"""56라운드 Q7·Q18 — 그로기(기력 0, 칼·대검만) 몸 동작 + 머리 위 재 소용돌이 + 휴대 무기.

산출:
  player/v3/player_groggy            4방향 · 10프레임 × 150ms = 1500ms 루프(그로기 1.5초 = 한 주기). 왼손이 빈 몸(free) — 두 팔이 늘어짐.
                                     재 비틀거림: 무릎이 꺾여 낮게 · 상체가 좌우(측면은 앞뒤)로 휘청 · 머리가 늦게 따라 흔들림 · 눈빛이 두 번 꺼졌다 켜짐 ·
                                     어깨 혼불이 작게 눌림 · 팔 끝에서 재가 흘러 떨어짐(몸 밖 1~2 도트).
  weapons/v3/katana_carry_groggy     칼집에 든 칼(왼허리, 손을 놓아 흔들림) — 같은 Rig 로 그려 흔들림과 어긋나지 않음
  weapons/v3/greatsword_carry_groggy 등에 멘 대검 — 같은 Rig
  fx/v3/player_groggy_swirl          머리 위 재 소용돌이(납작한 궤도를 도는 재 덩이 3 + 불씨 1 + 끊긴 궤적), 6프레임 × 125ms 루프(1.5초에 2바퀴)
                                     위치 = 몸 JSON headTopAnchors(프레임별 머리 꼭대기) 위.
hero_v3 · weapons_v3 모듈은 읽기만(이 프로세스 안에서 호출). 결정적.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rk  # noqa: E402

sys.path.append(os.path.normpath(os.path.join(HERE, "..", "weapons_v3")))
import wv3  # noqa: E402  (hero_v3 경로도 넣음)
from wv3 import K, hero, anim, motion  # noqa: E402
import greatsword as GS  # noqa: E402

from PIL import Image  # noqa: E402

DIRS = hero.DIRS
N = 10
MS = [150] * N
SIDE = ("left", "right")
EYE_OFF = (6, 7)


def poses(d):
    out = []
    for i in range(N):
        ph = 2 * math.pi * i / N
        s, s_lag, s_lag2 = math.sin(ph), math.sin(ph - 0.7), math.sin(ph - 1.3)
        dip = abs(math.sin(ph))                      # 휘청일 때마다 무릎이 더 꺾임
        common = dict(crouch=3.0 + 1.2 * dip, head=5 + round(2.0 * dip), flameRows=3, flame=i % 6, pulse=0,
                      eyeOff=i in EYE_OFF, lean=-3.0 * s_lag2)
        if d in SIDE:
            p = hero.pose(**common, lean_body=3.2 + 2.2 * s, hdx=2.0 * s_lag, sway=-2.4 * s_lag,
                          foot=((-4.5 + 1.8 * s, 0), (4.5 + 1.2 * math.sin(ph + 1.0), round(max(0.0, -s) * 2))),
                          hand=((-0.8 + 1.2 * s_lag, 2.5), (0.8 + 1.2 * s_lag, 2.5)))
        else:
            sg = 1 if d == "down" else -1
            p = hero.pose(**common, shift=3.6 * s, twist=2.2 * s * sg, stilt=3.0 * s, ptilt=1.4 * s, squash=0.1,
                          hdx=3.4 * s_lag * sg, sway=2.6 * s_lag,
                          footdx=(0.9 * s, 0.9 * s), lift=(round(max(0.0, s) * 2), round(max(0.0, -s) * 2)),
                          hand=((0.6 * s_lag, 3.0), (0.6 * s_lag, 3.0)))
        p["post"] = ("drip", dict(i=i, seed={"down": 5, "up": 7, "left": 9, "right": 13}[d]))
        out.append(p)
    return out


ASH = [hero.G[4], hero.G[5], hero.G[6], hero.G[7]]


def post_drip(im, R, direction, i, seed):
    """팔 끝(손)·허리에서 흘러 떨어지는 재 — 프레임 위상으로 떨어지는 3줄기(루프가 이어지게). 몸 밖 빈칸에만."""
    px = im.load()
    Wd, Hd = im.size
    srcs = []
    for k in ("handR", "handL"):
        if k in R.anchors:
            srcs.append(hero.to_px(R.anchors[k]))
    if "hipL" in R.anchors:
        h = hero.to_px(R.anchors["hipL"])
        srcs.append((h[0], h[1] + 6))
    for j, (sx, sy) in enumerate(srcs):
        for m in range(2):                               # 줄기마다 두 조각(위상 반 바퀴 차이)
            ph = ((i / N) * 2 + j * 0.31 + m * 0.5) % 1.0
            x = round(sx + (j - 1) * 1.5 + math.sin(ph * 6.28 + j) * 1.2)
            y = round(sy + 4 + ph * 34)
            c = ASH[(j + m) % len(ASH)]
            cells = [(x, y)] + ([(x, y + 1)] if ph < 0.5 else [])
            if all(0 <= cx < Wd and 0 <= cy < Hd - 2 and px[cx, cy][3] == 0 for cx, cy in cells):
                for cx, cy in cells:
                    px[cx, cy] = c
    return im


motion.POSTS["drip"] = post_drip


def head_top(im):
    """머리 꼭대기(몸 도트): 가장 위 불투명 줄들 중 몸 가운데 띠의 x 평균."""
    px = im.load()
    bb = im.getbbox()
    for y in range(bb[1], bb[3]):
        xs = [x for x in range(20, 76) if px[x, y][3]]
        if len(xs) >= 4:
            return [round(sum(xs) / len(xs), 1), y]
    return [48, 20]


def render():
    out = {}
    for d in DIRS:
        fr = []
        for p in poses(d):
            R = hero.draw_rig(d, p)
            fr.append(anim.Frame(motion.apply_post(R.image, R, d, p), R, p))
        out[d] = fr
    return out


def build():
    fr = render()
    body = {d: [f.image for f in fr[d]] for d in DIRS}
    hands = {d: [anim.hands_px(f.rig) for f in fr[d]] for d in DIRS}
    heads = {d: [head_top(f.image) for f in fr[d]] for d in DIRS}
    scar = {d: [dict(f.rig.scar) for f in fr[d]] for d in DIRS}
    meta = dict(weapon="katana|greatsword", label="그로기(기력 0)",
                pivot={"x": hero.PIV[0], "y": hero.PIV[1]}, emissiveColors=["#e2a33c", "#eecc78", "#f4de9b"],
                palette="parts/art/palette/lopad.json (주인공 v3 30색) — 몸 시트 규칙(hero_v3)과 같음",
                timingMs={"total": sum(MS), "loopMs": sum(MS)},
                groggyNote="56라운드 Q7·Q18: 기력 0 → 그로기 1.5초(공격·대쉬 불가, 가드만), 1.5초 뒤에만 회복. 이 시트 한 주기 = 1.5초. "
                           "가드를 누르면 가드 몸(현행)으로 바꾸고, 가드를 떼면 이 시트의 같은 시각 프레임으로 돌아온다(권장)",
                bodyRule="왼손이 빈 몸(free) 하나를 칼·대검이 같이 쓴다. 휴대 무기 = weapons/v3/<weapon>_carry_groggy(같은 프레임 번호)",
                carryOverlay={"katana": "weapons/v3/katana_carry_groggy", "greatsword": "weapons/v3/greatsword_carry_groggy"},
                swirlFx="fx/v3/player_groggy_swirl",
                headTopAnchors=heads, headTopNote="프레임별 머리 꼭대기(몸 시트 도트). 소용돌이 fx 피벗을 여기서 위로 14 도트에 둔다(swirlOffsetY)",
                swirlOffsetY=-14,
                eyeOffFrames=list(EYE_OFF), phases={"swayRight": [0, 1, 2, 3, 4], "swayLeft": [5, 6, 7, 8, 9]},
                handAnchors=hands, anchorNote="handAnchors = 프레임별 손 중심(몸 시트 도트). 두 손 모두 비어 늘어짐",
                scarAnchor=scar, scarAnchorNote="53라운드 Q4 · 계약 §13 등 상흔 사각형(몸 시트 도트)",
                design="56라운드 그로기 — 재 껍데기가 무릎이 꺾인 채 좌우로 휘청이고 머리가 늦게 따라 흔들리며, 눈빛이 깜빡 꺼지고, 어깨 혼불이 눌리고, 늘어진 팔 끝에서 재가 흘러내림")
    rk.write_sheet("player_groggy", rk.OUT_P, DIRS, body, MS, meta, glow=None, cap=31, loop=True,
                   allowed={"#%02x%02x%02x" % c for c in wv3.hero_palette()}, edge_ok=True)
    # 휴대 무기 — 같은 Rig
    kat = {d: [K.carry_frame(d, f.pose, f.rig) for f in fr[d]] for d in DIRS}
    mouths = {d: [[round(c, 1) for c in hero.to_px(K.mouth_point(d, f.rig)[:2])] for f in fr[d]] for d in DIRS}
    kj = json.load(open(os.path.join(rk.OUT_W, "katana_carry_idle.json"), encoding="utf-8"))
    kmeta = {k: kj[k] for k in ("pivot", "playerFrameOffset", "anchor", "occlusionBaked", "design", "designRef", "glowRule",
                                "colorBudget", "colorNote", "weapon") if k in kj}
    kmeta.update(action="carry_groggy", carry="sheathed — 왼허리 칼집(손을 놓아 흔들림)", state="sheathed", bodySheet="player_groggy",
                 depth={d: kj["depth"][d] for d in DIRS} if isinstance(kj.get("depth"), dict) else kj.get("depth"),
                 sheathMouthAnchors=mouths,
                 overlay="player_groggy 와 같은 프레임 번호를 같은 시각에 겹친다. 피벗 = 주인공 피벗 + playerFrameOffset")
    hp = {"#%02x%02x%02x" % c for c in wv3.hero_palette()}
    rk.write_sheet("katana_carry_groggy", rk.OUT_W, DIRS, kat, MS, kmeta, glow=None, cap=16, loop=True, allowed=hp, edge_ok=True)
    gj = json.load(open(os.path.join(rk.OUT_W, "greatsword_carry_idle.json"), encoding="utf-8"))
    ox, oy = gj["playerFrameOffset"]["x"], gj["playerFrameOffset"]["y"]
    fw, fh = gj["frameWidth"], gj["frameHeight"]
    cx, cy = GS.CANVAS_OFF[0] - ox, GS.CANVAS_OFF[1] - oy
    gs, tips = {}, {}
    for d in DIRS:
        lst, tl = [], []
        for f in fr[d]:
            im, tip = GS.back_frame(d, f.rig)
            lst.append(im.crop((cx, cy, cx + fw, cy + fh)))
            t = hero.to_px(tip) if tip is not None else None
            tl.append(None if t is None else [round(t[0] + ox, 1), round(t[1] + oy, 1)])
        gs[d], tips[d] = lst, tl
    gmeta = {k: gj[k] for k in ("pivot", "playerFrameOffset", "anchor", "occlusionBaked", "design", "designRef", "glowRule",
                                "colorBudget", "colorNote", "weapon", "twoHanded", "bladeLengthDots", "hiltLengthDots", "depth") if k in gj}
    gmeta.update(action="carry_groggy", carry=gj.get("carry"), state="sheathed", bodySheet="player_groggy", bladeTipAnchors=tips,
                 overlay="player_groggy 와 같은 프레임 번호를 같은 시각에 겹친다. 피벗 = 주인공 피벗 + playerFrameOffset")
    rk.write_sheet("greatsword_carry_groggy", rk.OUT_W, DIRS, gs, MS, gmeta, glow=None, cap=16, loop=True, allowed=hp, edge_ok=True)
    swirl = build_swirl()
    return fr, kat, gs, heads


# =============================================================================
# 머리 위 재 소용돌이
# =============================================================================
SW_MS = [125] * 6


def build_swirl():
    C = 80
    out = []
    for i in range(6):
        f = rk.frame(C, C)
        Lt = f.L([rk.S0, rk.S1])
        Lb = f.L([rk.S0, rk.S1, rk.S2, rk.S3])
        Le = f.L([rk.A18, rk.A19, rk.A21])
        cx, cy, rx, ry = C / 2, C / 2, 15.0, 5.0
        base = 2 * math.pi * i / 6
        # 끊긴 궤적(앞쪽 반은 진하게)
        Lt.arc(cx, cy, rx, ry, base, base + 2 * math.pi, 0.6, dash=(3, 0.35, 0.0), v=0.9)
        for k in range(3):
            a = base + k * 2 * math.pi / 3
            x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry
            front = math.sin(a) > 0
            r = 2.8 if front else 1.9
            Lb.puff(x, y - 1, r, v=0.95 if front else 0.6, ry=r * 0.8)
            # 꼬리(지나온 자리 작은 조각 둘)
            for m in (1, 2):
                aa = a - 0.35 * m
                Lb.put(cx + math.cos(aa) * rx, cy + math.sin(aa) * ry - 1, (0.7 if front else 0.45) - 0.15 * m)
        a = base + math.pi / 3 + 0.4                     # 쫓아 도는 불씨 하나
        Le.stamp(cx + math.cos(a) * rx * 0.8, cy + math.sin(a) * ry * 0.8 - 2, 0.6, 0.9 if math.sin(a) > 0 else 0.5, soft=0)
        out.append(f.render())
    frames, piv = rk.fit_centered({"any": out}, (C // 2, C // 2), margin=2, step=4)
    meta = dict(anchor="player_head_top", pivot={"x": piv[0], "y": piv[1]},
                pivotNote="pivot = 소용돌이 궤도 중심. 위치 = 주인공 피벗 기준 몸 JSON headTopAnchors[방향][프레임] + (0, swirlOffsetY −14) — 몸 시트 도트 좌표를 그대로",
                rotate=False, depth="above", followTarget=True, glowFrames=[], weapon="katana|greatsword",
                playRule="그로기 동안 루프(6 × 125ms = 750ms, 1.5초에 2바퀴). 그로기 끝나면 끔",
                design="56라운드 그로기 — 머리 위 납작한 궤도를 도는 재 덩이 3(앞쪽은 크고 밝게, 뒤쪽은 작고 어둡게) + 쫓아 도는 어두운 불씨 + 끊긴 궤적")
    return rk.write_sheet("player_groggy_swirl", rk.OUT_FX, ["any"], frames, SW_MS, meta, glow=[], loop=True)


if __name__ == "__main__":
    build()
    print("groggy ok")
