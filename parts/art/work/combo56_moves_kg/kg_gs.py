"""56라운드 E1 — 대검 새 기본기 4종(Q22 · Q40), 8방향(작업 B 와 같은 directionRows).

  greatsword_tackle          어깨 태클(대쉬 공격 교체)
  greatsword_brace_upswing   버티기 올려베기(가드 중 좌클릭, 맞아도 안 끊김)
  greatsword_leap_slam       공중제비 도약 찍기(차지 중 스페이스)
  greatsword_guard_rush      막다가 떼면 돌진(퍼펙트 가드 직후 우클릭 뗌)

렌더·내보내기 = combo56_body(rig8 8방향 리그 · gs56.export_move · moves56 키 형식 gear3.K_) 를 그대로 쓰고 이 정의를 끼워 넣는다(이 프로세스 안에서만).
무게(Q5) 역할 이름: windup · hold · heave · strike · drag · catch (+ 이 작업: brace · launch · dash · impact · air · flip · land · rush).
공중제비 프레임(flipFrames): 몸과 무기를 한 그림으로 합쳐 무기 오버레이에 그린다(몸 시트 그 칸은 비움) — 몸 틀(96×144)보다 커지는 회전 그림이라서.
  측면(left·right) = 웅크린 몸+칼을 90° 단위로 회전(정확한 픽셀 회전) · 정면/뒷면/대각 = 앞 90°·270° 웅크림 그림 + 180° = 반대쪽 몸을 180° 회전(거꾸로 뒤집힌 등).
공중 높이는 그림에 넣지 않고 JSON airOffsetPx(프레임별, 도트, 위 +)로 — 시스템이 몸·무기를 그만큼 올려 그리고 그림자·피벗은 바닥에 둔다.

산출: assets/sprites/player/v3/player_<동작>.png/.json · assets/sprites/weapons/v3/<동작>.png/.json (새 4동작만, 기존 시트는 건드리지 않음)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "combo56_body")))
sys.path.insert(0, HERE)

from PIL import Image  # noqa: E402

import rig8  # noqa: E402
from rig8 import DIRS8, Q, EX, hero, wv3  # noqa: E402
import moves56 as MV  # noqa: E402
import gs56  # noqa: E402
import greatsword as GS  # noqa: E402

SRC = "parts/art/work/combo56_moves_kg/build.py gs (56라운드 Q22·Q40 대검 새 기본기 — combo56_body 8방향 리그)"
gs56.SRC = SRC
K_ = Q.K_
R_GS = MV.R_GS                 # 51 월드 px
RD = MV.dots(R_GS)             # 204 도트
dots = MV.dots
GUARD = K_(-55, 52, 15, 13, 45, lunge=-0.2, crouch=6, lean=0.6, off="blade")          # greatsword_special 가드 자세(막는 칼)
DRAWN_END = K_(36, -24, 22, 13, 42, lunge=0.3, crouch=4, tw=0.2, lean=0.7, off="two")  # charge_slam 끝(휴대 각 근처)
LOOP0 = MV._loop(0)                                                                    # 차지 유지 루프 f3 자세

# =============================================================================
# 3. 어깨 태클 — 칼을 오른손에 뒤로 끌며(칼끝이 바닥을 긁음) 왼어깨로 들이받음
# =============================================================================
TACKLE = [
    K_(150, -18, 110, 10, 38, lunge=-0.2, crouch=7, tw=1.0, lean=0.7, off="guard"),                    # 0 windup 칼을 뒤로 넘기며 어깨를 낮춤
    K_(160, -22, 120, 9, 37, lunge=-0.4, crouch=9.5, tw=1.25, lean=1.0, off="guard"),                  # 1 hold 웅크려 버팀(긴 선딜)
    K_(152, -28, 116, 10, 36.5, lunge=0.9, crouch=8.5, tw=1.2, lean=2.3, off="guard"),                 # 2 launch 박차고 나감
    K_(148, -30, 112, 9, 37, lunge=1.45, crouch=8, tw=1.32, lean=2.9, off="guard"),                    # 3 dash 어깨 앞(판정 시작)
    K_(150, -30, 114, 9, 37, lunge=1.55, crouch=7.5, tw=1.4, lean=3.1, off="guard", pulse=1),          # 4 impact 들이받음
    K_(146, -31, 110, 9, 37, lunge=1.3, crouch=9, tw=1.2, lean=2.4, off="guard", pulse=1),             # 5 impact 반동(몸이 눌림)
    K_(142, -34, 106, 10, 36.5, lunge=1.5, crouch=10.5, tw=1.0, lean=2.1, off="guard"),                # 6 drag 칼 무게에 끌려 미끄러짐(칼끝이 바닥)
    K_(120, -27, 90, 12, 37, lunge=1.0, crouch=8, tw=0.7, lean=1.3, off="hip"),                        # 7 catch 버팀
    K_(58, -30, R=(4.0, 12.0, 34.0), lunge=0.2, crouch=2.5, tw=0.2, lean=0.4, off="hip"),              # 8 recover(휴대 각)
]

# =============================================================================
# 4. 버티기 올려베기 — 가드 자세에서 칼을 세운 채 낮게 버팀(맞아도 밀리지 않음) → 앞 바닥에서 머리 위로 크게 올려벰
# =============================================================================
BRACE = [
    GUARD,                                                                                              # 0 guard(가드 중 좌클릭)
    K_(-42, 32, 10, 13, 40, lunge=-0.3, crouch=10, lean=0.9, off="blade", tension=0.5),               # 1 brace 칼을 세운 채 가라앉음
    K_(-40, 29, 9, 13, 39.5, lunge=-0.35, crouch=10.8, lean=1.0, off="blade", tension=0.8),           # 2 brace 버팀(재가 떨어짐)
    K_(-41, 30, 10, 13, 39.8, lunge=-0.3, crouch=10.4, lean=0.95, off="blade", tension=0.8),          # 3 brace 떨림
    K_(10, -36, 8, 16, 37.5, lunge=0.6, crouch=12, lean=2.0, off="two"),                               # 4 heave 칼을 앞 바닥으로 떨어뜨려 퍼 올릴 준비
    K_(0, 18, 0, 19, 50, lunge=1.0, crouch=7, lean=1.3, off="two", state="glow"),                       # 5 strike 올려벰(판정)
    K_(0, 62, 0, 15, 64, lunge=1.0, crouch=3, lean=-0.2, off="two", state="glow"),                      # 6 strike 머리 위까지
    K_(180, 70, 0, 6, 70, lunge=0.7, crouch=2.5, lean=-0.8, off="two"),                                # 7 drag 칼 무게가 뒤로 넘어감
    K_(180, 60, 0, 5, 68, lunge=0.5, crouch=4.5, lean=-0.5, off="two"),                                # 8 drag 버팀
    K_(20, 10, 10, 14, 48, lunge=0.4, crouch=5, lean=0.6, off="two"),                                  # 9 catch 앞으로 내림
    MV.LINK_C,                                                                                           # 10 link(가운데 낮게 — 연격 V/H 로 이어짐)
]

# =============================================================================
# 5. 공중제비 도약 찍기 — 차지 유지 자세에서 뛰어올라 앞으로 한 바퀴(칼과 함께) → 착지하며 내려찍음
# =============================================================================
FLIP_SIDE = K_(0, 85, 0, 8, 56, crouch=12.5, tuck=1.0, lean=2.4, off="two")       # 측면 회전용 웅크림(칼이 머리 위로 곧게)
FLIP_FRONT = {90: K_(0, 4, 0, 14, 52, crouch=9, tuck=1.0, lean=2.2, off="two"),   # 정면/뒷면: 칼이 앞으로 누움(머리가 앞으로 숙음)
              270: K_(180, 4, 0, 6, 60, crouch=9, tuck=1.0, lean=0.6, off="two")}  # 칼이 뒤로 누움(몸이 다시 서기 직전)
LEAP = [
    LOOP0,                                                                                               # 0 hold 차지 유지 자세(스페이스)
    K_(180, 50, 0, 5, 60, crouch=10, lean=0.8, off="two", state="charge"),                              # 1 crouch 웅크려 도약 준비
    K_(180, 66, 0, 4, 72, crouch=1.5, lean=-0.4, tuck=0.3, off="two"),                                  # 2 launch 박차고 뜀
    FLIP_SIDE, FLIP_SIDE, FLIP_SIDE,                                                                    # 3~5 flip 90° · 180° · 270°
    K_(180, 62, 0, 3, 72, crouch=2, lean=-0.6, tuck=0.5, off="two"),                                    # 6 air 한 바퀴 돌아 칼이 머리 위 뒤로
    K_(0, 35, 0, 15, 60, tuck=0.4, crouch=3, lean=1.4, off="two"),                                      # 7 heave 떨어지며 내려침
    K_(0, -60, 0, 20, 33, lunge=1.2, crouch=13, lean=2.7, off="two", state="glow"),                     # 8 land 착지 + 내려찍기(판정)
    K_(0, -62, 0, 20.5, 32, lunge=1.35, crouch=14, lean=2.9, off="two"),                                # 9 planted
    K_(0, -63, 0, 21.5, 31, lunge=1.5, crouch=14.5, lean=3.1, off="two"),                               # 10 drag 몸이 칼 위로 끌려감
    K_(15, -34, 8, 15, 40, lunge=0.7, crouch=8, lean=1.5, off="two"),                                   # 11 catch 뽑음
    DRAWN_END,                                                                                           # 12 recover
]
FLIP = {3: 90, 4: 180, 5: 270}
AIR = [0, 0, 18, 58, 76, 64, 34, 12, 0, 0, 0, 0, 0]                                                    # 공중 높이(도트, 위 +)

# =============================================================================
# 6. 막다가 떼면 돌진 — 퍼펙트 가드 자세에서 칼을 오른쪽 아래로 떨궈 끌며(바닥에 홈) 낮게 돌진, 적 줄을 밀어붙임
# =============================================================================
RUSH = [
    GUARD,                                                                                               # 0 guard(퍼펙트 가드 직후 우클릭 뗌)
    K_(60, -10, 40, 14, 40, lunge=0.2, crouch=9, tw=0.6, lean=1.4, off="two"),                          # 1 shove 가드를 풀며 칼을 오른쪽 아래로
    K_(40, -33, 30, 16, 37, lunge=1.0, crouch=11, tw=0.4, lean=2.4, off="two"),                         # 2 launch 낮게 박차고 나감(칼끝 바닥)
    K_(30, -34, 22, 18, 37.5, lunge=1.4, crouch=12, tw=0.3, lean=2.9, off="two", state="glow"),          # 3 rush(판정)
    K_(26, -34, 20, 19, 37.5, lunge=1.5, crouch=12, tw=0.25, lean=3.0, off="two", state="glow"),         # 4 rush(판정)
    K_(10, -12, 8, 18, 42, lunge=1.3, crouch=9, lean=2.0, off="two", state="glow"),                      # 5 heave 멈추며 칼을 퍼 올려 밀어냄(판정 끝)
    K_(20, -30, 12, 17, 38, lunge=1.5, crouch=11, lean=2.3, off="two"),                                 # 6 drag 미끄러짐
    K_(40, -26, 25, 14, 40, lunge=0.9, crouch=7, tw=0.3, lean=1.3, off="two"),                          # 7 catch
    DRAWN_END,                                                                                          # 8 recover
]

GS_NEW = {
    "greatsword_tackle": dict(
        label="어깨 태클(대쉬 공격 교체)", frames=TACKLE,
        ms=[60, 90, 40, 40, 40, 70, 90, 90, 100], impact=3, active=[3, 4], cancel=7,
        roles=["windup", "hold", "launch", "dash", "impact", "impact", "drag", "catch", "recover"],
        arc=(0, 0), rScale=0.0, step=None,
        dash=dict(world=40, frames=[2, 3, 4], note="태클 돌진 — 조준 방향으로 40 월드 px(2.5칸, 임시). 벽·큰 적에 막히면 멈춤"),
        dragStep=dict(world=6, frames=[6], note="부딪힌 뒤 칼 무게에 끌려 미끄러짐(참고값)"),
        hitShape=dict(type="rect", fromR=0.0, lengthR=0.6, widthR=0.8, travelsWithPlayer=True,
                      note="몸 앞 사각형(앞 0~0.6R, 폭 0.8R) — 돌진하는 동안 몸과 함께 이동, 적마다 1회. 가드·방패 자세 무너뜨림(임시 제안)"),
        next="아무 대검 동작(cancel 이후)", startsFrom="대쉬 중 좌클릭(대검) — 대쉬 공격 greatsword_dashslash 를 대신함",
        endsWith="greatsword_carry_drawn_idle"),
    "greatsword_brace_upswing": dict(
        label="버티기 올려베기(가드 중 좌클릭 — 맞아도 안 끊김)", frames=BRACE,
        ms=[40, 70, 100, 100, 60, 40, 50, 80, 100, 90, 100], impact=5, active=[5, 6], cancel=9,
        roles=["guard", "brace", "brace", "brace", "heave", "strike", "strike", "drag", "drag", "catch", "link"],
        arc=(0, 0), rScale=1.2, step=dict(world=6, frames=[4, 5]),
        superArmorFrames=[0, 1, 2, 3, 4, 5, 6],
        hitShape=dict(type="wedge", angleDeg=50, lengthR=1.2, impactCircle=dict(centerR=0.9, radiusR=0.3),
                      launch=True, note="앞 쐐기 50° ×1.2(아래 → 위 올려벰, 적을 띄움) — 임시 제안. 울분 소모 시 ×1.5 · 60°(fx _ember)"),
        rageVariant=dict(fx="greatsword_brace_upswing_ember", lengthR=1.5, angleDeg=60,
                         note="울분 소모 시(임시): 판정 ×1.5·60°, fx 를 잔불 판으로. 몸·무기 그림은 같음"),
        next="greatsword_cleave | greatsword_sweep_cw (link 이후)", startsFrom="가드 자세(greatsword_special 막는 칼) 중 좌클릭",
        endsWith="LINK_C (가운데 낮게)"),
    "greatsword_leap_slam": dict(
        label="공중제비 도약 찍기(차지 중 스페이스 — 차지 단계 유지)", frames=LEAP,
        ms=[40, 80, 50, 50, 50, 50, 50, 40, 60, 110, 120, 100, 110], impact=8, active=[8], cancel=None,
        roles=["hold", "crouch", "launch", "flip", "flip", "flip", "air", "heave", "land", "planted", "drag", "catch", "recover"],
        arc=(0, 0), rScale=1.3, step=None,
        leap=dict(world=48, frames=[2, 3, 4, 5, 6, 7], note="도약 거리 — 조준 방향으로 48 월드 px(3칸, 임시). 벽에 막히면 그 자리에 착지"),
        hitShape=dict(type="wedge", angleDeg=40, lengthRByStage=[1.3, 1.5, 1.8], impactCircle=dict(radiusR=0.45, atWedgeEnd=True),
                      landingRing=dict(radiusR=0.6, note="착지 발밑 둥근 판정(임시) — 공중에서 내려앉는 충격"),
                      note="차지 내려찍기와 같은 쐐기(차지 단계별 ×1.3/1.5/1.8) + 착지 충격원 — 임시 제안"),
        groundCrack=dict(sheet="greatsword_ground_crack", rowByStage=["m", "m", "l"], at="impactFrame 시작, 쐐기 끝점"),
        next=None, startsFrom="greatsword_charge 루프 f3~f6 중 스페이스 — f0 = 루프 f3 자세", endsWith="greatsword_carry_drawn_idle"),
    "greatsword_guard_rush": dict(
        label="막다가 떼면 돌진(퍼펙트 가드 직후 우클릭 뗌)", frames=RUSH,
        ms=[40, 50, 40, 40, 40, 60, 90, 90, 100], impact=3, active=[3, 4, 5], cancel=7,
        roles=["guard", "shove", "launch", "rush", "rush", "heave", "drag", "catch", "recover"],
        arc=(0, 0), rScale=0.0, step=None,
        dash=dict(world=56, frames=[2, 3, 4, 5], note="낮은 돌진 — 조준 방향으로 56 월드 px(3.5칸, 임시). 벽에 막히면 멈춤"),
        dragStep=dict(world=6, frames=[6], note="멈춘 뒤 미끄러짐(참고값)"),
        hitShape=dict(type="rect", fromR=0.0, lengthR=0.75, widthR=0.9, travelsWithPlayer=True, carry=True,
                      note="몸 앞 사각형(앞 0~0.75R, 폭 0.9R) — 돌진과 함께 이동하며 적을 앞으로 밀고 감(크게 튕기지 않음 · Q5), 적마다 1회. 마지막 f5 퍼 올림에서 놓음(임시 제안)"),
        next="아무 대검 동작(cancel 이후)", startsFrom="퍼펙트 가드 직후 우클릭 뗌 — 밀쳐내기(greatsword_special) 대신",
        endsWith="greatsword_carry_drawn_idle"),
}
ORDER = list(GS_NEW)
OPP = {"down": "up", "up": "down", "down-right": "up-left", "up-left": "down-right", "down-left": "up-right", "up-right": "down-left"}


def install():
    for n, m in GS_NEW.items():
        MV.GS[n] = m
    gs56.V_TYPE = tuple(gs56.V_TYPE) + ("greatsword_leap_slam",)      # 아래 대각 내려찍기 보정(착지 내려찍기)


install()


# =============================================================================
# 렌더
# =============================================================================
class FakeRig:
    """공중제비 합성 프레임용 — 내보내기가 읽는 anchors·scar 만."""

    def __init__(self, anchors, scar):
        self.anchors = anchors
        self.scar = scar
        self.image = Image.new("RGBA", (hero.FW, hero.FH), (0, 0, 0, 0))


def from_px(q):
    return (hero.DPIV[0] + (q[0] - hero.PIV[0]) / hero.S, hero.DPIV[1] + (q[1] - hero.PIV[1]) / hero.S)


def _one(name, d, raw, i):
    k = Q.norm(gs56.adjust_key(name, d, raw))
    p = rig8.body_pose8(d, k, i)
    R = rig8.draw_rig8(d, p)
    im, tip = GS.gear_frame(d, name, k, R)
    return k, R, im, hero.to_px(tip)


def _rot_pt(pt, c, deg):
    """화면 좌표 점을 c 둘레로 deg(반시계 +, PIL 과 같음) 회전."""
    a = math.radians(deg)
    x, y = pt[0] - c[0], pt[1] - c[1]
    return (c[0] + x * math.cos(a) + y * math.sin(a), c[1] - x * math.sin(a) + y * math.cos(a))


def flip_frame(name, d, i, angle):
    """공중제비 한 칸 → (합성 RGBA 448 캔버스, 칼끝(몸 도트), 손(몸 도트), 키)."""
    ox, oy = GS.CANVAS_OFF
    side = d in ("left", "right")
    if side:
        src_d, key, rot = d, FLIP_SIDE, (-angle if d == "right" else angle)
    elif angle == 180:
        src_d, key, rot = OPP[d], FLIP_SIDE, 180
    else:
        src_d, key, rot = d, FLIP_FRONT[angle], 0
    k, R, im, tip = _one(name, src_d, key, i)
    comp = Image.new("RGBA", GS.CANVAS, (0, 0, 0, 0))
    comp.alpha_composite(R.image, (ox, oy))
    comp.alpha_composite(im)
    bb = R.image.getbbox()
    c = (ox + (bb[0] + bb[2]) / 2.0, oy + (bb[1] + bb[3]) / 2.0)
    c = (round(c[0]), round(c[1]))
    hands = {h: hero.to_px(R.anchors[h]) for h in ("handR", "handL")}
    if rot:
        comp = comp.rotate(rot, resample=Image.NEAREST, center=c)
        tip = _rot_pt((tip[0] + ox, tip[1] + oy), c, rot)
        tip = (tip[0] - ox, tip[1] - oy)
        hands = {h: (lambda q: (q[0] - ox, q[1] - oy))(_rot_pt((v[0] + ox, v[1] + oy), c, rot)) for h, v in hands.items()}
    rig = FakeRig({h: from_px(v) for h, v in hands.items()}, dict(R.scar, visible=False))
    return comp, tip, rig, k, dict(source=src_d, rotateDeg=rot, center=[c[0] - ox, c[1] - oy])


def render(name):
    m = MV.GS[name]
    flips = FLIP if name == "greatsword_leap_slam" else {}
    out, info = {}, {}
    for d in DIRS8:
        lst = []
        for i, raw in enumerate(m["frames"]):
            if i in flips:
                comp, tip, rig, k, inf = flip_frame(name, d, i, flips[i])
                info.setdefault(d, {})[i] = inf
                lst.append(dict(body=rig.image, rig=rig, weapon=comp, tip=tip, state=k["state"], key=k, plant=None))
                continue
            k, R, im, tip = _one(name, d, raw, i)
            lst.append(dict(body=R.image, rig=R, weapon=im, tip=tip, state=k["state"], key=k, plant=None))
        out[d] = lst
    return out, info


def check_tips(name, fr):
    flips = FLIP if name == "greatsword_leap_slam" else {}
    for d in DIRS8:
        for i, f in enumerate(fr[d]):
            if i in flips:
                continue
            k = f["key"]
            z = Q.gs_tip_z(k)
            assert k["el"] <= -40 or z >= -0.5, (name, d, i, round(z, 1))


# =============================================================================
# JSON 보강
# =============================================================================
def hit_px(hs):
    hs = dict(hs)
    hs["R"] = {"world": R_GS, "dots": RD}
    if hs["type"] == "rect":
        hs.update(fromPx=round(RD * hs["fromR"], 1), lengthPx=round(RD * hs["lengthR"], 1), widthPx=round(RD * hs["widthR"], 1), angleDeg=0)
    elif hs["type"] == "wedge":
        if "lengthR" in hs:
            hs["lengthPx"] = round(RD * hs["lengthR"], 1)
            ic = dict(hs["impactCircle"])
            ic.update(centerDistPx=round(RD * ic["centerR"], 1), radiusPx=round(RD * ic["radiusR"], 1))
            hs["impactCircle"] = ic
        else:
            hs["lengthPxByStage"] = [round(RD * k, 1) for k in hs["lengthRByStage"]]
            ic = dict(hs["impactCircle"])
            ic["radiusPx"] = round(RD * ic["radiusR"], 1)
            hs["impactCircle"] = ic
        if "landingRing" in hs:
            lr = dict(hs["landingRing"])
            lr["radiusPx"] = round(RD * lr["radiusR"], 1)
            hs["landingRing"] = lr
    hs["units"] = "…Px = 도트(pixelScale 0.5, 월드 px = 도트 / 4). 각도: 조준 0°, 화면 시계 + (§17). 원점 = 판정 원점(피벗 위 40 도트)"
    hs["reference"] = "임시 제안값 — 시스템 데이터가 기준"
    return hs


def extra_meta(name, m):
    st = MV.starts(m["ms"])
    upd = dict(frameRoles=m["roles"], r56="56라운드 Q22·Q40 대검 새 기본기(작업 E1)", version="v3-r56-e1", source=SRC,
               hitShape=hit_px(m["hitShape"]), fxSheet="fx/v3/" + name,
               weightNote="56라운드 Q5 무게: 긴 선딜(hold/brace/crouch) → 짧은 판정 → drag(칼 무게에 끌림) → catch. 판정은 짧게, 앞뒤는 길게")
    for key in ("dash", "leap"):
        if key in m:
            dd = dict(m[key])
            dd.update(dots=dots(dd["world"]), startMs=st[dd["frames"][0]],
                      endMs=st[dd["frames"][-1]] + m["ms"][dd["frames"][-1]], easing="easeOut" if key == "dash" else "linear",
                      stopsAtWall=True)
            upd[{"dash": "dashPx", "leap": "leapPx"}[key]] = dd
    if "superArmorFrames" in m:
        sa = m["superArmorFrames"]
        upd.update(superArmorFrames=sa, superArmorMs=[st[sa[0]], st[sa[-1]] + m["ms"][sa[-1]]],
                   braceFrames=[i for i, r in enumerate(m["roles"]) if r == "brace"],
                   superArmorNote="superArmorMs 구간(0.46초) 동안 맞아도 동작이 끊기지 않음 — 피해는 그대로 받고 울분으로 쌓임(56라운드 Q54·Q61). "
                                  "버티는 자세는 braceFrames 0.27초 고정, 가드를 오래 눌러도 늘지 않음(Q54·Q61). 맞을 때마다 fx/v3/greatsword_brace_absorb 를 몸 위에 1회",
                   rageVariant=m["rageVariant"])
    if name == "greatsword_leap_slam":
        upd.update(airOffsetPx=dict(byFrame=AIR, unit="dots(pixelScale 0.5) — 위 +",
                                    note="시스템이 몸·무기 시트를 이 높이만큼 위로 올려 그린다(그림자·피벗·판정 원점은 바닥). 프레임 사이는 보간해도 됨"),
                   flipFrames=sorted(FLIP), flipAngles={str(k): v for k, v in FLIP.items()},
                   bodyInOverlayFrames=sorted(FLIP),
                   flipNote="공중제비 칸(f3~f5)은 몸이 무기 오버레이 안에 함께 그려져 있고 몸 시트 칸은 비어 있다(회전 그림이 몸 틀보다 커서). "
                            "두 시트를 늘 겹쳐 그리면 그대로 맞는다. 측면 = 90° 단위 회전, 정면·뒷면·대각 = 웅크림 + 180° 칸은 반대쪽 몸을 거꾸로",
                   airborneFrames=[i for i, a in enumerate(AIR) if a > 0],
                   chargeStageKept="차지 단계(0.4/0.8/1.2초)를 유지한 채 뜀 — 착지 쐐기·균열 크기는 그 단계로(hitShape.lengthPxByStage · groundCrack.rowByStage)",
                   groundCrack=m["groundCrack"], landAtMs=st[m["impact"]])
    return upd


def build():
    pal = wv3.hero_palette()
    frs, infos = {}, {}
    for n in ORDER:
        frs[n], infos[n] = render(n)
        check_tips(n, frs[n])
        print(n, "rendered")
    with gs56.dirs8():
        frame = gs56.crop(frs)
        print("E1 greatsword frame", frame)
        stats = {}
        for n in ORDER:
            gs56.export_move(n, frs[n], frame)
            m = MV.GS[n]
            upd = extra_meta(n, m)
            if n == "greatsword_leap_slam":
                upd["flipRender"] = infos[n]
            for path in (os.path.join(EX.OUT_P, "player_%s.json" % n), os.path.join(EX.OUT_W, "%s.json" % n)):
                j = json.load(open(path, encoding="utf-8"))
                for k in ("arcFromDeg", "arcToDeg", "arcDeg", "arcNote"):
                    j.pop(k, None)
                j.update(upd)
                if path.endswith("weapons/v3/%s.json" % n):
                    j["frameNote"] = ("E1 새 대검 4동작 합집합 틀 %dx%d · offset (%d,%d) — 작업 B 연격 틀(240×280)과 다름. "
                                      "시스템은 JSON frameWidth/frameHeight·pivot·playerFrameOffset 을 읽을 것" % frame)
                EX.write_json(path, j)
            wc, bc = set(), set()
            for d in DIRS8:
                for f in frs[n][d]:
                    wc |= wv3.colors_of(f["weapon"])
                    bc |= wv3.colors_of(f["body"])
                    assert not wv3.has_alpha_partial(f["weapon"]) and not wv3.has_alpha_partial(f["body"])
                    assert EX.edge_pixels(f["weapon"]) == 0, (n, d)
            assert not (wc - pal) and not (bc - pal), n
            stats[n] = dict(weaponColors=len(wc), bodyColors=len(bc), timing=MV.timing(m))
            print(n, "ok", stats[n])
    state = dict(frame=list(frame), stats=stats,
                 tips={n: {d: [None if f["tip"] is None else [round(f["tip"][0], 1), round(f["tip"][1], 1)] for f in frs[n][d]] for d in DIRS8}
                       for n in ORDER})
    with open(os.path.join(HERE, "state_gs.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    return frs, frame


if __name__ == "__main__":
    build()
