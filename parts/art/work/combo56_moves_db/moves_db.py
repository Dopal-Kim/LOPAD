"""56라운드 Q40~Q43 새 기본기 3종 — 동작 정의(몸·무기 공통 키). 작업 E2.

  dagger_backstab   단검 기본기 '등 뒤 치명 찌르기'(Q43) — 그림자 걸음 직후 좌클릭. 역수로 높이 든 확정 치명 자세(dagger_special 끝)에서
                    두 손으로 적의 등에 깊게 내리꽂고 비틀어 뽑는다(키아트 단검 4번).
  dagger_flurry     단검 기본기 '고속 난타'(Q43) — 좌클릭 홀드 동안 빠른 찌르기 루프(키아트 단검 6번). 시작 2 · 루프 6(3찌르기) · 끝 2.
  bow_arrow_rain    활 기본기 '화살비'(Q43) — 우클릭으로 당긴 채 좌클릭 → 활을 하늘로 세워 3발 연속 쏘아 올림(키아트 활 3번).

키 형식 = hero_v3/gear3.K_ (θ, elev, hth, hr, hz, R, L, off, state, lunge, crouch, tw, lean, tuck, tension).
좌표: 로컬 (f 앞, r 해부 오른쪽, z 위) 설계 단위(1 = 1.5 도트). θ 0 = 앞, + = 해부 오른쪽, elev + = 위.
ms·판정은 아트 임시 제안(보고서 표) — 시스템 데이터가 기준.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "weapons_v3")))

import wv3  # noqa: E402
from wv3 import K, Q  # noqa: E402

K_ = Q.K_
READY_DG = Q.READY_DG
WORLD_TO_DOT = 4


def dots(world):
    return round(world * WORLD_TO_DOT, 1)


def pommel(R, th, el, k=5.5):
    """역수 단검: 날 = v 방향(새끼손가락 쪽), 손잡이 끝(폼멜) = 엄지 쪽(-v). 왼손바닥을 폼멜 위에 얹는 자리."""
    return K.add(R, K.dir3(th, el), -k)


def hand(hth, hr, hz):
    return K.hand_local(dict(hth=hth, hr=hr, hz=hz))


# =============================================================================
# 1. 단검 등 뒤 치명 찌르기 — 확정 치명 자세(높이 듦) → 더 높이 감음 → 두 손 내리꽂기 → 깊이 박혀 비틂 → 뽑음 → 겨눔
# =============================================================================
def _bs(th, el, R, two=False, **kw):
    L = pommel(R, th, el) if two else None
    return K_(th, el, R=R, L=L, **kw)


R_HIGH = hand(10, 12, 62)          # dagger_special 끝 손 자리(확정 치명 자세)
R_COIL = hand(4, 8, 79)
R_COIL2 = hand(2, 7, 81)
R_DRIVE = hand(2, 17, 60)
R_HIT = hand(0, 21, 53)
R_DEEP = hand(0, 22, 50)
R_TWIST = hand(-4, 21.5, 51)
R_RIP = hand(14, 15, 58)

BACKSTAB = dict(
    weapon="dagger", label="등 뒤 치명 찌르기",
    frames=[
        _bs(10, -75, R_HIGH, off="guard", lunge=0.3, crouch=4.5, lean=1.1),                                      # 0 확정 치명 자세(이어받음)
        _bs(4, -84, R_COIL, two=True, lunge=0.0, crouch=2.0, lean=-0.35, tw=0.25),                               # 1 coil 머리 위로 — 왼손이 폼멜을 덮음
        _bs(2, -86, R_COIL2, two=True, lunge=-0.15, crouch=2.6, lean=-0.5, tw=0.3, tuck=0.15),                               # 2 hold 버팀(1px 떨림·무릎)
        _bs(4, -68, R_DRIVE, two=True, lunge=0.9, crouch=7.0, lean=1.8, tw=0.0),                                 # 3 drive 내리꽂음
        _bs(2, -58, R_HIT, two=True, lunge=1.3, crouch=9.5, lean=2.5, tw=-0.1, state="glow"),                    # 4 impact(판정 · 치명 섬광)
        _bs(2, -55, R_DEEP, two=True, lunge=1.35, crouch=10.5, lean=2.65, tw=-0.15),                             # 5 deep 체중을 실어 더 박음
        _bs(-14, -52, R_TWIST, two=True, lunge=1.3, crouch=10.0, lean=2.5, tw=-0.4, state="embers"),             # 6 twist 비틂(불티)
        _bs(30, -30, R_RIP, off="guard", lunge=0.7, crouch=6.0, lean=1.4, tw=0.3, state="fade"),                 # 7 rip 뽑아 냄
        K_(110, -35, 35, 10, 47, lunge=0.4, crouch=3.5, tw=0.45, lean=0.9, off="guard"),                         # 8 recover
        READY_DG],                                                                                                 # 9 겨눔(dagger 기본 연격 끝과 같음)
    ms=[40, 50, 70, 30, 50, 60, 70, 50, 60, 80],
    roles=["entry", "coil", "hold", "drive", "impact", "deep", "twist", "rip", "recover", "ready"],
    impact=4, active=[4], hitFrames=[4], cancel=8,
    thrust=dict(lengthPx=150, widthPx=56, angleDeg=0, fromPx=24),
    hitNote="임시 제안: 그림자 걸음 직후 등 뒤 확정 치명 1회. 판정 = 정면 직사각(기본 3타 168 보다 짧고 넓음 — 바로 앞 적의 등). 피해·치명 배율은 시스템",
    startsFrom="dagger_special 끝 프레임(f8 확정 치명 자세, 역수로 높이 든 손) — f0 이 그 자세를 그대로 이어받음",
    endsWith="READY_DG(기본 연격 끝 겨눔) → dagger_carry_idle",
    phases={"entry": [0], "windup": [1, 2, 3], "strike": [4, 5, 6], "recover": [7, 8, 9]},
)

# =============================================================================
# 2. 단검 고속 난타 — 시작 2 · 루프 6(찌르기 3번: 위·아래·가운데, 각 찌름+당김) · 끝 2
# =============================================================================
def _stab(th, el, hth, hr, hz, **kw):
    return K_(th, el, hth, hr, hz, off="guard", **kw)


FLURRY = dict(
    weapon="dagger", label="고속 난타",
    frames=[
        _stab(150, -25, 30, 9, 46, lunge=0.4, crouch=4.5, tw=0.5, lean=1.1),                                      # 0 start 웅크려 파고듦
        _stab(165, -18, 55, 8, 47, lunge=0.6, crouch=5.5, tw=0.75, lean=1.5),                                      # 1 start 장전(날을 팔뚝에)
        _stab(-12, -30, -10, 23, 50, lunge=1.0, crouch=5.5, tw=-0.55, lean=1.9, state="glow"),                    # 2 stab A(높게, 살짝 위)
        _stab(120, -25, 40, 11, 47, lunge=0.75, crouch=5.5, tw=0.45, lean=1.6),                                    # 3 retract
        _stab(8, -55, 8, 23, 42, lunge=1.05, crouch=6.5, tw=0.3, lean=2.0, state="glow"),                          # 4 stab B(낮게)
        _stab(135, -20, 50, 10, 48, lunge=0.75, crouch=5.5, tw=0.6, lean=1.6),                                     # 5 retract
        _stab(-2, -40, -2, 24, 46, lunge=1.1, crouch=6.0, tw=-0.25, lean=2.05, state="glow"),                     # 6 stab C(가운데 · 가장 깊게)
        _stab(160, -20, 52, 8, 47, lunge=0.65, crouch=5.5, tw=0.72, lean=1.5),                                     # 7 retract → f2 로 이어짐
        _stab(80, -40, 25, 13, 45, lunge=0.5, crouch=4.0, tw=0.25, lean=1.0, state="fade"),                        # 8 end
        READY_DG],                                                                                                   # 9 end 겨눔
    ms=[40, 40, 45, 45, 45, 45, 45, 45, 60, 80],
    roles=["start", "start", "stab", "retract", "stab", "retract", "stab", "retract", "end", "end"],
    loopFrames=[2, 3, 4, 5, 6, 7], hitFrames=[2, 4, 6], impact=2, active=[2, 4, 6], cancel=None,
    thrust=dict(lengthPx=144, widthPx=48, angleDeg=0, fromPx=16),
    stabAngles={"2": -10, "4": 12, "6": 0},
    hitNote="임시 제안: 루프 한 바퀴(270ms)에 3타 = 초당 약 11타. 판정 = 정면 직사각(기본 1타 ×1.5 길이 144, 폭 48) — stabAngles 는 그림 각(판정은 0° 하나로 충분)",
    startsFrom="dagger_carry_idle / 기본 연격 아무 프레임(좌클릭 홀드 시작)",
    endsWith="READY_DG(겨눔) → dagger_carry_idle",
    phases={"start": [0, 1], "loop": [2, 3, 4, 5, 6, 7], "end": [8, 9]},
)

# =============================================================================
# 3. 활 화살비 — 가득 당긴(수평) 자세에서 활을 하늘로 세움 → 3발 연속(놓기 · 재가 맺혀 새 화살 · 당김) → 따라감 → 내림
# =============================================================================
PULL = 30.0                       # 가득 당김 길이(설계) — gear3.bow_draw 가득과 같음(줌통~시위 ≈ 31.9)


def aim_vec(ang, yaw=-18.0):
    """하늘 조준: 앞으로 ang° 들어 올림(elev). yaw = 해부 왼쪽으로 살짝(활 손 쪽) — gear3 가득 당김 L-R 의 r 성분과 비슷하게."""
    return K.dir3(yaw, ang)


def up_key(ang, p, state, lean=-0.95, crouch=3.0, tw=0.85, yaw=-18.0, jitter=(0.0, 0.0), tension=None):
    """ang = 하늘 각(°), p = 당김 진행도(0 = 시위에 손만, 1 = 가득)."""
    a = aim_vec(ang, yaw)
    reach = 31.0 - 3.0 * math.sin(math.radians(ang))          # 팔을 길게 뻗어 하늘로(높이 들수록 조금 덜)
    sh = (2.0, -4.0, 63.0)                                      # 왼어깨 근처(로컬)
    L = (sh[0] + a[0] * reach, sh[1] + a[1] * reach - 0.5, sh[2] + a[2] * reach)
    pull = 8.0 + (PULL - 8.0) * p
    R = (L[0] - a[0] * pull + jitter[0], L[1] - a[1] * pull + 1.0, L[2] - a[2] * pull + jitter[1])
    return K_(0, 0, R=R, L=L, crouch=crouch, tw=tw, lean=lean, tension=p if tension is None else tension, state=state)


ANG = (56.0, 64.0, 50.0)          # 3발 각(살짝 부채 — 하늘에서 퍼져 원 안에 흩뿌림)
bd = Q.bow_draw

RAIN = dict(
    weapon="bow", label="화살비",
    frames=[
        up_key(28, 1.0, "full", lean=-0.55, tw=0.75),                    # 0 raise 활을 들어 올림(가득 유지)
        up_key(ANG[0], 1.0, "full"),                                       # 1 aim 하늘로 가득
        up_key(ANG[0], 1.0, "release", tension=0.7),                      # 2 release 1
        up_key(ANG[1], 0.08, "draw", lean=-0.85),                         # 3 renock 재가 맺혀 새 화살
        up_key(ANG[1], 1.0, "full", lean=-1.0),                           # 4 draw 가득
        up_key(ANG[1], 1.0, "release", lean=-1.05, tension=0.7),         # 5 release 2
        up_key(ANG[2], 0.08, "draw", lean=-0.85),                         # 6 renock
        up_key(ANG[2], 1.0, "full", lean=-0.95),                          # 7 draw 가득
        up_key(ANG[2], 1.0, "release", lean=-1.0, tension=0.7),          # 8 release 3
        up_key(ANG[2] + 6, 0.9, "release", lean=-0.6, crouch=2.4, tension=0.35),   # 9 follow 따라감(시위 식음)
        bd(0.05, tension=0.1),                                             # 10 lower 수평으로 내림
        bd(0.0)],                                                          # 11 ready(= bow_draw_hold f0 근처)
    angles=[28, ANG[0], ANG[0], ANG[1], ANG[1], ANG[1], ANG[2], ANG[2], ANG[2], ANG[2] + 6, 0, 0],
    ms=[50, 60, 40, 40, 40, 40, 40, 40, 40, 70, 80, 100],
    roles=["raise", "aim", "release", "renock", "draw", "release", "renock", "draw", "release", "follow", "lower", "ready"],
    releaseFrames=[2, 5, 8], cancel=9,
    startsFrom="bow_draw_hold 가득(f5) 또는 유지 루프(f6~f9) — 우클릭으로 당긴 채 좌클릭",
    endsWith="bow_draw_hold f0 근처(우클릭을 계속 누르고 있으면 바로 bow_draw_hold, 아니면 bow_carry_idle)",
    phases={"raise": [0, 1], "volley": [2, 3, 4, 5, 6, 7, 8], "recover": [9, 10, 11]},
)

MOVES = {"dagger_backstab": BACKSTAB, "dagger_flurry": FLURRY, "bow_arrow_rain": RAIN}


def starts(ms):
    s, t = [], 0
    for m in ms:
        s.append(t)
        t += m
    return s
