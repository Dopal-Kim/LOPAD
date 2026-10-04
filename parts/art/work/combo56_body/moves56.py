"""56라운드 대검 동작 정의 — Q5 무게(긴 선딜 · 휘두른 뒤 몸이 끌려감) · Q6 8방향 · Q10 기본 차지 vs 개성 발현 차지(꽂아내리기).

키 형식 = combo55/moves.py(gear3.K_) 그대로. 좌표·각도: 로컬 (f 앞, r 해부 오른쪽, z 위), θ(0 = 앞, + = 해부 오른쪽 = 화면 시계), elev(+ = 위).
판정 수치(§17 출발점): R 대검 51 월드 px. ms 는 아트 제안값 — 시스템은 55라운드 Q29(예전 템포 유지)대로 두 구간 맞춤으로 늘여 재생하되
impactFrame 시작 = hitAt 이 맞으면 그림은 맞는다.

무게 연출(Q5) 프레임 역할:
  windup  = 들어 올림(수평은 뒤로 감아 당김, V·차지는 머리 위)
  hold    = 머리 위/뒤에서 잠깐 버팀(떨림 1px · 무릎이 더 굽음) — '긴 선딜'
  heave   = 무게를 싣고 내려오기 시작
  strike  = 판정(glow)
  drag    = 휘두른 뒤 칼 무게에 몸이 끌려감(앞발이 더 나가고 상체가 칼 쪽으로 쏠림 · 칼끝이 더 감김)
  catch   = 버티며 무게를 받아냄 → 연결 자세
"""
from rig8 import M55, Q

K_ = Q.K_
LINK_R, LINK_L, LINK_C = M55.LINK_R, M55.LINK_L, M55.LINK_C
R_GS = M55.R_GS
dots = M55.dots


def mirror(k):
    """수평 반시계(H2) = H1 의 좌우(해부) 대칭."""
    o = dict(k)
    o["th"] = -k["th"]
    if k.get("hth") is not None:
        o["hth"] = -k["hth"]
    o["tw"] = -k["tw"]
    o["extra"] = dict(k.get("extra") or {})
    return o


H1_FRAMES = [
    K_(-95, 18, -55, 11, 50, lunge=0.1, crouch=4, tw=-0.8, lean=0.4, off="two"),                       # 0 windup 시작(연결 자세에서)
    K_(-128, 28, -78, 8, 55, lunge=-0.2, crouch=5, tw=-1.1, lean=0.0, off="two"),                      # 1 windup 뒤로 감아 당김
    K_(-142, 33, -86, 7, 57, lunge=-0.35, crouch=6, tw=-1.3, lean=-0.25, off="two"),                   # 2 hold 버팀
    K_(-140, 31, -85, 7, 56.5, lunge=-0.35, crouch=6.6, tw=-1.28, lean=-0.18, off="two"),              # 3 hold 떨림(무릎 더 굽음)
    K_(-92, 10, -56, 14, 48, lunge=0.4, crouch=6.5, tw=-0.8, lean=1.0, off="two"),                     # 4 heave
    K_(-22, -6, -15, 20, 42, lunge=1.0, crouch=7, tw=-0.1, lean=1.8, off="two", state="glow"),         # 5 strike(판정)
    K_(40, -14, 30, 20, 40, lunge=1.05, crouch=7.5, tw=0.6, lean=1.85, off="two", state="glow"),       # 6 strike
    K_(95, -24, 66, 16, 37, lunge=1.25, crouch=9, tw=1.15, lean=2.0, off="two"),                       # 7 drag 칼이 더 감김
    K_(118, -30, 78, 13, 36, lunge=1.4, crouch=10, tw=1.32, lean=2.15, off="two"),                     # 8 drag 몸이 끌려감
    K_(108, -26, 72, 13, 37, lunge=1.05, crouch=8.5, tw=1.15, lean=1.5, off="two"),                    # 9 catch 버팀
    LINK_R]                                                                                              # 10 연결(오른쪽)

V_FRAMES = [
    K_(10, 68, 5, 9, 62, lunge=0.2, crouch=3, lean=0.2, off="two"),                                    # 0 windup 앞에서 곧게 들어 올림
    K_(180, 58, 0, 4, 70, lunge=-0.15, crouch=2, lean=-0.6, off="two"),                                # 1 windup 머리 위
    K_(180, 63, 0, 3, 72.5, lunge=-0.3, crouch=1.4, lean=-0.85, off="two"),                            # 2 hold 가장 높이(뒤로 젖힘)
    K_(180, 61, 0, 3.5, 71.5, lunge=-0.3, crouch=2.3, lean=-0.78, off="two"),                          # 3 hold 떨림
    K_(0, 40, 0, 14, 60, lunge=0.6, crouch=4, lean=1.2, off="two"),                                    # 4 heave
    K_(0, -25, 0, 19, 42, lunge=1.0, crouch=9, lean=2.1, off="two"),                                   # 5 heave(내려옴)
    K_(0, -58, 0, 19, 35, lunge=1.0, crouch=11, lean=2.3, off="two", state="glow"),                    # 6 strike(판정)
    K_(0, -61, 0, 19.5, 34, lunge=1.15, crouch=12.5, lean=2.6, off="two"),                             # 7 박힘
    K_(0, -62, 0, 20.5, 33, lunge=1.35, crouch=13.2, lean=2.85, off="two"),                            # 8 drag 몸이 칼 위로 쏠림
    K_(6, -40, 4, 17, 39, lunge=0.9, crouch=9, lean=1.8, off="two"),                                   # 9 catch 칼을 비틀어 뽑음
    K_(8, -32, 5, 16, 41, lunge=0.6, crouch=7, lean=1.4, off="two"),                                   # 10 catch
    LINK_C]                                                                                              # 11 연결(가운데)


def _loop(i):
    a = [0.0, -1.5, -2.0, -0.6][i]
    c = [0.0, 0.5, 0.8, 0.3][i]
    return K_(180, 56 + a, 0, 5, 65.5 + a * 0.3, crouch=5 + c, lean=0.3, off="two", state="charge")


# 꽂아내리기(개성 발현 후 차지) — 칼을 거꾸로 세워(칼끝 아래 · 폼멜 위) 두 손으로 들어 올렸다가 땅에 수직으로 박음. 휘두르지 않음.
PLUNGE_F = 11.0          # 칼이 꽂히는 자리(몸 앞, 설계) — 칼이 수직이라 바닥 점 = 손의 (f, r)
PLUNGE_R = 2.0

PLUNGE_FRAMES = [
    _loop(0),                                                                                            # 0 차지 유지 자세(머리 위 뒤로)
    K_(0, 12, R=(8.0, PLUNGE_R, 70.0), crouch=4.0, lean=0.2, off="two"),                               # 1 turn 칼을 앞으로 넘겨 돌림
    K_(0, -78, R=(PLUNGE_F - 3.0, PLUNGE_R, 82.0), crouch=1.6, lean=-0.7, tuck=0.35, off="two"),       # 2 raise 거꾸로 높이 듦(살짝 뜀, 칼끝 약간 앞)
    K_(0, -80, R=(PLUNGE_F - 3.0, PLUNGE_R, 81.0), crouch=2.2, lean=-0.65, tuck=0.4, off="two"),       # 3 hold 버팀
    K_(0, -89, R=(PLUNGE_F, PLUNGE_R, 52.0), lunge=0.5, crouch=8.0, lean=1.3, off="two", state="glow"),   # 4 plunge(판정 · 충격파 발생)
    K_(0, -89, R=(PLUNGE_F, PLUNGE_R, 42.0), lunge=0.8, crouch=13.0, lean=1.9, off="two"),             # 5 박힘 — 무릎 꿇듯 칼에 체중
    K_(0, -89, R=(PLUNGE_F, PLUNGE_R, 41.0), lunge=0.8, crouch=13.6, lean=2.0, off="two"),             # 6 유지(충격파가 나가는 동안)
    K_(0, -89, R=(PLUNGE_F, PLUNGE_R, 60.0), lunge=0.4, crouch=6.0, lean=0.9, off="two"),              # 7 뽑음
    K_(36, -24, 22, 13, 42, lunge=0.3, crouch=4, tw=0.2, lean=0.7, off="two"),                          # 8 회복(휴대 각으로)
]
PLANT_FRAMES = {4, 5, 6, 7}            # 칼끝이 바닥 아래(땅속 부분은 그리지 않음)

GS = {
    "greatsword_sweep_cw": dict(
        comboIndex=1, label="H1 수평 시계", frames=H1_FRAMES,
        ms=[60, 80, 110, 70, 60, 40, 50, 70, 90, 90, 100], impact=5, active=[5, 6], cancel=9,
        roles=["windup", "windup", "hold", "hold", "heave", "strike", "strike", "drag", "drag", "catch", "link"],
        arc=(-75, 75), rScale=1.0, height=(8, 8), step=dict(world=5, frames=[4, 5]),
        dragStep=dict(world=6, frames=[7, 8], note="휘두른 뒤 칼 무게에 끌려 앞으로 미끄러짐(참고값, 방향키와 무관 — 시스템 판단)"),
        hitShape=dict(type="arc", startDeg=-75, endDeg=75, radiusR=1.0, innerR=0.35, note="수평 초승달 150° (§17)"),
        next="greatsword_cleave", endsWith="LINK_R (오른쪽 — V 의 들어 올림으로 이어짐)",
        startsFrom="greatsword_carry_drawn_idle 0 · greatsword_cleave 끝(가운데)"),
    "greatsword_cleave": dict(
        comboIndex=2, label="V 정면 내려찍기", frames=V_FRAMES,
        ms=[60, 90, 120, 80, 50, 40, 40, 70, 100, 90, 80, 100], impact=6, active=[6], cancel=10,
        roles=["windup", "windup", "hold", "hold", "heave", "heave", "strike", "planted", "drag", "catch", "catch", "link"],
        arc=(0, 0), rScale=1.3, step=dict(world=12, frames=[4, 5, 6]),
        dragStep=dict(world=4, frames=[7, 8], note="박힌 칼 위로 몸이 쏠림(참고값)"),
        hitShape=dict(type="wedge", angleDeg=40, lengthR=1.3, impactCircle=dict(centerR=1.3, radiusR=0.35),
                      note="좁은 쐐기 40° ×1.3 + 끝점 충격원 0.35R (§17)"),
        groundCrack=dict(sheet="greatsword_ground_crack", row="s", at="impactFrame 시작, 쐐기 끝점(충격원 중심)"),
        next="greatsword_sweep_ccw | greatsword_sweep_cw (교대)", endsWith="LINK_C (가운데 낮게)",
        startsFrom="greatsword_sweep_cw 끝(오른쪽) · greatsword_sweep_ccw 끝(왼쪽)"),
    "greatsword_sweep_ccw": dict(
        comboIndex=3, label="H2 수평 반시계", frames=[mirror(k) for k in H1_FRAMES[:-1]] + [LINK_L],
        ms=[60, 80, 110, 70, 60, 40, 50, 70, 90, 90, 100], impact=5, active=[5, 6], cancel=9,
        roles=["windup", "windup", "hold", "hold", "heave", "strike", "strike", "drag", "drag", "catch", "link"],
        arc=(75, -75), rScale=1.0, height=(8, 8), step=dict(world=5, frames=[4, 5]),
        dragStep=dict(world=6, frames=[7, 8], note="H1 과 같음"),
        hitShape=dict(type="arc", startDeg=75, endDeg=-75, radiusR=1.0, innerR=0.35, note="수평 초승달 150° (§17, H1 역방향)"),
        next="greatsword_cleave", endsWith="LINK_L (왼쪽 — V 의 들어 올림으로 이어짐)", startsFrom="greatsword_cleave 끝(가운데)"),
    "greatsword_charge": dict(
        label="홀드 차지(들어 올림 → 버팀 루프)", frames=[
            K_(10, 66, 5, 9, 62, crouch=3, lean=0.2, off="two"),
            K_(180, 60, 0, 4, 69, crouch=2.5, lean=-0.4, off="two"),
            K_(180, 58, 0, 5, 66, crouch=4.5, lean=0.2, off="two"),
            _loop(0), _loop(1), _loop(2), _loop(3)],
        ms=[80, 100, 120, 100, 100, 100, 100], loopFrames=[3, 4, 5, 6],
        roles=["windup", "windup", "hold", "loop", "loop", "loop", "loop"],
        phases={"raise": [0, 1, 2], "hold": [3, 4, 5, 6]},
        stages=dict(sec=[0.4, 0.8, 1.2], flashSheets=["greatsword_charge_flash_lv1", "greatsword_charge_flash_lv2", "greatsword_charge_flash_lv3"]),
        startsFrom="아무 대검 자세(좌클릭 홀드 시작)", next="greatsword_charge_slam (기본) | greatsword_charge_plunge (개성 발현 후)"),
    "greatsword_charge_slam": dict(
        label="차지 내려찍기(기본 — 칼로 직접 강하게, 충격파 없음)", frames=[
            K_(180, 52, 0, 3, 71, crouch=3, lean=-0.8, off="two"),                                      # 0 hold 끝(머리 위)
            K_(180, 57, 0, 2.5, 73, lunge=-0.2, crouch=2, lean=-1.05, off="two"),                       # 1 windup 한 번 더 젖힘(반동)
            K_(0, 45, 0, 14, 62, lunge=0.8, crouch=4, lean=1.3, off="two"),                              # 2 heave
            K_(0, -28, 0, 20, 41, lunge=1.2, crouch=10, lean=2.3, off="two"),                            # 3 heave
            K_(0, -60, 0, 20, 33, lunge=1.2, crouch=12.5, lean=2.6, off="two", state="glow"),            # 4 strike(판정)
            K_(0, -62, 0, 20.5, 32, lunge=1.35, crouch=13.5, lean=2.85, off="two"),                      # 5 박힘
            K_(0, -63, 0, 21.5, 31, lunge=1.5, crouch=14, lean=3.05, off="two"),                         # 6 drag 몸이 칼 위로 끌려감
            K_(15, -34, 8, 15, 40, lunge=0.7, crouch=8, lean=1.5, off="two"),                            # 7 catch 뽑음
            K_(36, -24, 22, 13, 42, lunge=0.3, crouch=4, tw=0.2, lean=0.7, off="two")],                 # 8 회복
        ms=[40, 60, 40, 40, 80, 110, 120, 100, 110], impact=4, active=[4], cancel=None,
        roles=["hold", "windup", "heave", "heave", "strike", "planted", "drag", "catch", "recover"],
        arc=(0, 0), rScale=1.3, step=dict(world=12, frames=[2, 3, 4]),
        hitShape=dict(type="wedge", angleDeg=40, lengthRByStage=[1.3, 1.5, 1.8], impactCircle=dict(radiusR=0.35, atWedgeEnd=True),
                      note="§17 차지: 쐐기 길이 ×1.3/1.5/1.8. 56라운드 Q10: 기본 차지는 충격파 링 없음(greatsword_charge_ring 은 쓰지 않음)"),
        groundCrack=dict(sheet="greatsword_ground_crack", rowByStage=["m", "m", "l"], at="impactFrame 시작, 쐐기 끝점"),
        startsFrom="greatsword_charge 루프 f3~f6 (머리 위로 든 칼)", endsWith="greatsword_carry_drawn_idle"),
    "greatsword_charge_plunge": dict(
        label="꽂아내리기(개성 발현 후 차지 — 휘두르지 않고 칼을 땅에 박아 마우스 방향 충격파)", frames=PLUNGE_FRAMES,
        ms=[40, 70, 80, 90, 40, 90, 160, 110, 120], impact=4, active=[4], cancel=None,
        roles=["hold", "turn", "raise", "hold", "plunge", "planted", "planted", "pull", "recover"],
        arc=(0, 0), rScale=0.0, step=None,
        hitShape=dict(type="ring", centerAt="plant point (body front)", radiusR=0.45,
                      note="꽂힌 자리 작은 충격원(참고값) — 본 판정은 충격파 fx greatsword_plunge_wave(rect, 마우스 방향)"),
        plantPointDots=None,
        waveSheet="greatsword_plunge_wave", waveAt="impactFrame 시작, 꽂힌 자리(plantAnchors)에서 마우스 방향으로",
        groundCrack=dict(sheet="greatsword_ground_crack", row="l", at="impactFrame 시작, 꽂힌 자리(plantAnchors)"),
        startsFrom="greatsword_charge 루프 f3~f6 (머리 위로 든 칼) — f0 = 루프 f3 과 같은 자세", endsWith="greatsword_carry_drawn_idle"),
}
ORDER = ["greatsword_sweep_cw", "greatsword_cleave", "greatsword_sweep_ccw", "greatsword_charge", "greatsword_charge_slam",
         "greatsword_charge_plunge"]


def starts(ms):
    s, t = [], 0
    for m in ms:
        s.append(t)
        t += m
    return s


def timing(m):
    st = starts(m["ms"])
    out = {"total": sum(m["ms"])}
    if m.get("impact") is not None:
        out["hitAt"] = st[m["impact"]]
        a = m["active"][-1]
        out["activeEndAt"] = st[a] + m["ms"][a]
    out["cancelAt"] = st[m["cancel"]] if m.get("cancel") is not None else None
    return out
