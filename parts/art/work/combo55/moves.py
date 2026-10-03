"""55라운드 Q18~Q25 · 계약 §17 — 칼 K-A 발도 초승달 · 대검 G-C 관성 순환 기본 연격의 동작 정의(몸·무기 공통 키).

좌표·각도는 hero_v3/katana3.py 규약: 로컬 (f 앞, r 해부 오른쪽, z 위), θ(0 = 앞, + = 해부 오른쪽), elev(+ = 위).
θ 는 화면각과 같은 부호다(어느 방향이든 + = 화면 시계 방향 = 해부 오른쪽) — §17 '조준 0°, 화면 시계 +' 와 같다.
칼 키 = katana3.COMBO 형식(state·th·el·hth·hr·hz·lunge·crouch·tw·lean·off, 칼집 단계는 along·slide).
대검 키 = gear3.K_(θ, elev, hth, hr, hz, …) 형식(두 손 off="two").

판정 수치(§17, 출발점 — 시스템 데이터가 기준): R 칼 33 · 대검 51 월드 px. 월드 px = 논리 px / 2 = 도트 / 4 (pixelScale 0.5).
ms 는 아트 제안값(시스템이 데이터로 조정 — 그림은 판정 프레임 시작 = hitAt 만 맞으면 된다).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WV3 = os.path.normpath(os.path.join(HERE, "..", "weapons_v3"))
sys.path.insert(0, WV3)

import wv3  # noqa: E402  (hero_v3 경로도 넣음)
from wv3 import Q  # noqa: E402

K_ = Q.K_
WORLD_TO_DOT = 4                    # 월드 px → 도트 (월드 10 = 논리 20 = 도트 40, export.HIT_ORIGIN_NOTE)
R_KATANA = 33                       # §17 판정 반경(월드 px)
R_GS = 51


def dots(world):
    return round(world * WORLD_TO_DOT, 1)


# =============================================================================
# 칼 K-A 발도 초승달
# =============================================================================
KATANA = {
    # 1타 대각 올려베기: 해부 오른쪽 아래(+70) → 왼쪽 위(-40). 뽑아 든 낮은 겨눔에서 오른쪽 아래로 감아 올려 벰.
    "katana_rise": dict(
        comboIndex=1, label="1타 대각 올려베기", ms=[40, 30, 20, 40, 30, 40, 60], impact=3, active=[3], cancel=5,
        arc=(70, -40), rScale=1.0, height=(6, 46), step=dict(world=5, frames=[1, 2, 3]),
        hitShape=dict(type="arc", startDeg=70, endDeg=-40, radiusR=1.0, innerR=0.0, note="비대칭 호 110° (§17 대각)"),
        next="katana_fall", startsFrom="katana_carry_drawn_idle 0 (뽑아 든 낮은 겨눔) · 3타 끝 f7",
        frames=[
            dict(state="steel", th=100, el=-34, hth=66, hr=14, hz=36, lunge=0.2, crouch=4.5, tw=0.85, lean=0.7, off="guard"),
            dict(state="steel", th=88, el=-26, hth=58, hr=17, hz=37, lunge=0.4, crouch=5.0, tw=0.8, lean=0.9, off="guard"),
            dict(state="steel", th=55, el=-12, hth=40, hr=20, hz=40, lunge=0.7, crouch=5.0, tw=0.5, lean=1.2, off="back"),
            dict(state="glow", th=-5, el=14, hth=5, hr=21, hz=46, lunge=1.0, crouch=4.5, tw=-0.1, lean=1.3, off="back"),
            dict(state="steel", th=-45, el=32, hth=-28, hr=18, hz=52, lunge=1.0, crouch=4.0, tw=-0.6, lean=1.1, off="back"),
            dict(state="steel", th=-62, el=40, hth=-40, hr=15, hz=55, lunge=0.9, crouch=3.5, tw=-0.8, lean=0.9, off="guard"),
            dict(state="fade", th=-55, el=34, hth=-36, hr=14, hz=53, lunge=0.6, crouch=3.0, tw=-0.7, lean=0.7, off="guard"),
        ]),
    # 2타 대각 내려베기: 왼쪽 위(-70) → 오른쪽 아래(+40) — 1타 역방향, 화면에서 1타 궤적과 X 로 교차.
    "katana_fall": dict(
        comboIndex=2, label="2타 대각 내려베기(X자)", ms=[20, 20, 40, 30, 40, 60], impact=2, active=[2], cancel=4,
        arc=(-70, 40), rScale=1.0, height=(50, 4), step=dict(world=5, frames=[1, 2]),
        hitShape=dict(type="arc", startDeg=-70, endDeg=40, radiusR=1.0, innerR=0.0, note="비대칭 호 110° (§17 대각, 1타 역방향)"),
        next="katana_crescent", startsFrom="katana_rise 끝(f6, 왼쪽 위로 든 칼)",
        frames=[
            dict(state="steel", th=-72, el=44, hth=-46, hr=14, hz=57, lunge=0.6, crouch=3.0, tw=-0.85, lean=0.8, off="guard"),
            dict(state="steel", th=-48, el=26, hth=-30, hr=18, hz=52, lunge=0.8, crouch=4.0, tw=-0.6, lean=1.1, off="guard"),
            dict(state="glow", th=-8, el=-4, hth=-4, hr=21, hz=44, lunge=1.0, crouch=5.0, tw=-0.1, lean=1.4, off="back"),
            dict(state="steel", th=38, el=-24, hth=30, hr=19, hz=39, lunge=1.0, crouch=5.5, tw=0.5, lean=1.4, off="back"),
            dict(state="steel", th=58, el=-32, hth=44, hr=16, hz=37, lunge=0.9, crouch=5.0, tw=0.7, lean=1.2, off="back"),
            dict(state="fade", th=48, el=-30, hth=36, hr=14, hz=37, lunge=0.6, crouch=4.0, tw=0.55, lean=0.9, off="guard"),
        ]),
    # 3타 수평 발도(마무리): 칼을 왼허리 칼집에 넣는 납도 자세(f0~f2) → 발도 150° 초승달(f3~f6) → 1타 시작 자세 근처로 회복(f7).
    # 휘두름 방향은 왼허리 칼집에서 뽑는 자연 방향(-75 → +75). 판정 부채꼴은 §17(+75 → -75)과 같은 범위(대칭) — 보고서 질문.
    "katana_crescent": dict(
        comboIndex=3, label="3타 수평 발도 초승달", ms=[40, 40, 90, 30, 40, 30, 50, 90], impact=4, active=[4], cancel=7,
        arc=(-75, 75), rScale=1.25, height=(14, 14), step=dict(world=15, frames=[3, 4, 5]),
        hitShape=dict(type="arc", startDeg=75, endDeg=-75, radiusR=1.25, innerR=0.45,
                      note="초승달 150° 내반경 있는 호 (§17). 그림의 휘두름은 -75 → +75(칼집 발도 방향) — 범위는 같음"),
        echo=dict(sheet="katana_crescent_echo", delayMs=150, damage=0.5),
        phases={"sheathe": [0, 1], "iaiStance": [2], "draw": [3, 4, 5], "recover": [6, 7]},
        next="katana_rise", startsFrom="katana_fall 끝(f5, 오른쪽 아래)",
        frames=[
            dict(state="steel", th=-128, el=-12, hth=-24, hr=18, hz=40, lunge=0.3, crouch=4.0, tw=-0.6, lean=0.7, off="saya"),
            dict(state="partial", along=30.0, slide=9.0, crouch=5.0, tw=-0.7, lean=0.9, off="saya"),
            dict(state="sheathed", along=7.0, slide=0.0, crouch=6.5, tw=-0.95, lean=1.3, off="saya"),
            dict(state="partial", along=27.0, slide=12.0, crouch=6.0, tw=-0.6, lean=1.5, lunge=0.5, off="saya"),
            dict(state="glow", th=-30, el=-4, hth=-20, hr=22, hz=41, lunge=1.0, crouch=6.0, tw=-0.1, lean=1.7, off="saya", slide=6.0),
            dict(state="steel", th=40, el=-8, hth=30, hr=22, hz=41, lunge=1.2, crouch=6.0, tw=0.5, lean=1.7, off="back"),
            dict(state="steel", th=92, el=-14, hth=64, hr=18, hz=40, lunge=1.2, crouch=5.5, tw=0.9, lean=1.4, off="back"),
            dict(state="steel", th=80, el=-26, hth=54, hr=15, hz=37, lunge=0.8, crouch=4.0, tw=0.75, lean=0.9, off="guard"),
        ]),
}

# =============================================================================
# 대검 G-C 관성 순환 — H1(시계) → V → H2(반시계) → V → H1 … (연결 포즈: H1 끝 = 오른쪽 · H2 끝 = 왼쪽 · V 끝 = 가운데)
# =============================================================================
LINK_R = K_(78, -4, 55, 12, 44, lunge=0.5, crouch=5, tw=0.8, lean=0.8, off="two")
LINK_L = K_(-78, 0, -50, 12, 46, lunge=0.5, crouch=5, tw=-0.8, lean=0.8, off="two")
LINK_C = K_(12, -14, 8, 14, 44, lunge=0.4, crouch=4.5, lean=0.9, off="two")


def _loop(i):
    a = [0.0, -1.5, -2.0, -0.6][i]
    c = [0.0, 0.5, 0.8, 0.3][i]
    return K_(180, 56 + a, 0, 5, 65.5 + a * 0.3, crouch=5 + c, lean=0.3, off="two", state="charge")


GS = {
    "greatsword_sweep_cw": dict(
        comboIndex=1, label="H1 수평 시계", ms=[70, 70, 40, 50, 40, 60, 70, 90], impact=3, active=[3, 4], cancel=6,
        arc=(-75, 75), rScale=1.0, height=(8, 8), step=dict(world=5, frames=[2, 3]),
        hitShape=dict(type="arc", startDeg=-75, endDeg=75, radiusR=1.0, innerR=0.35, note="수평 초승달 150° (§17)"),
        next="greatsword_cleave", endsWith="LINK_R (오른쪽 — V 의 들어 올림으로 이어짐)",
        startsFrom="greatsword_carry_drawn_idle 0 · greatsword_cleave 끝(가운데)",
        frames=[
            K_(-95, 18, -55, 11, 50, lunge=0.1, crouch=4, tw=-0.8, lean=0.4, off="two"),
            K_(-135, 26, -80, 8, 54, lunge=-0.15, crouch=5.5, tw=-1.1, lean=0.1, off="two"),
            K_(-80, 6, -50, 15, 46, lunge=0.4, crouch=6, tw=-0.7, lean=1.0, off="two"),
            K_(-22, -6, -15, 20, 42, lunge=1.0, crouch=7, tw=-0.1, lean=1.8, off="two", state="glow"),
            K_(40, -14, 30, 20, 40, lunge=1.0, crouch=7.5, tw=0.6, lean=1.8, off="two", state="glow"),
            K_(88, -22, 62, 15, 37, lunge=1.0, crouch=8.5, tw=1.0, lean=1.5, off="two"),
            K_(100, -20, 70, 13, 38, lunge=0.8, crouch=7, tw=1.05, lean=1.2, off="two"),
            LINK_R]),
    "greatsword_cleave": dict(
        comboIndex=2, label="V 정면 내려찍기", ms=[70, 80, 40, 40, 60, 80, 70, 90], impact=4, active=[4], cancel=6,
        arc=(0, 0), rScale=1.3, step=dict(world=12, frames=[2, 3, 4]),
        hitShape=dict(type="wedge", angleDeg=40, lengthR=1.3, impactCircle=dict(centerR=1.3, radiusR=0.35),
                      note="좁은 쐐기 40° ×1.3 + 끝점 충격원 0.35R (§17). 관성 최대 = 충격원 확대(impactSheet scale)"),
        next="greatsword_sweep_ccw | greatsword_sweep_cw (교대)", endsWith="LINK_C (가운데 낮게 — H1·H2 어느 쪽으로도 감아 올림)",
        startsFrom="greatsword_sweep_cw 끝(오른쪽) · greatsword_sweep_ccw 끝(왼쪽) — f0 은 앞에서 곧게 들어 올리는 칼(양쪽 공통)",
        frames=[
            K_(10, 68, 5, 9, 62, lunge=0.2, crouch=3, lean=0.2, off="two"),
            K_(180, 56, 0, 4, 70, lunge=-0.15, crouch=2, lean=-0.6, off="two"),
            K_(0, 40, 0, 14, 60, lunge=0.6, crouch=4, lean=1.2, off="two"),
            K_(0, -25, 0, 19, 42, lunge=1.0, crouch=9, lean=2.1, off="two"),
            K_(0, -58, 0, 19, 35, lunge=1.0, crouch=11, lean=2.3, off="two", state="glow"),
            K_(0, -61, 0, 19, 34, lunge=1.0, crouch=12, lean=2.5, off="two"),
            K_(8, -32, 5, 16, 41, lunge=0.6, crouch=7, lean=1.4, off="two"),
            LINK_C]),
    "greatsword_sweep_ccw": dict(
        comboIndex=3, label="H2 수평 반시계", ms=[70, 70, 40, 50, 40, 60, 70, 90], impact=3, active=[3, 4], cancel=6,
        arc=(75, -75), rScale=1.0, height=(8, 8), step=dict(world=5, frames=[2, 3]),
        hitShape=dict(type="arc", startDeg=75, endDeg=-75, radiusR=1.0, innerR=0.35, note="수평 초승달 150° (§17, H1 역방향)"),
        next="greatsword_cleave", endsWith="LINK_L (왼쪽 — V 의 들어 올림으로 이어짐)",
        startsFrom="greatsword_cleave 끝(가운데)",
        frames=[
            K_(95, 12, 60, 11, 46, lunge=0.1, crouch=5, tw=0.8, lean=0.5, off="two"),
            K_(135, 18, 85, 8, 50, lunge=-0.15, crouch=6, tw=1.1, lean=0.2, off="two"),
            K_(80, 2, 52, 15, 44, lunge=0.4, crouch=6, tw=0.7, lean=1.0, off="two"),
            K_(22, -6, 18, 20, 42, lunge=1.0, crouch=7, tw=0.1, lean=1.8, off="two", state="glow"),
            K_(-40, -10, -30, 19, 42, lunge=1.0, crouch=7, tw=-0.6, lean=1.7, off="two", state="glow"),
            K_(-88, -16, -60, 14, 41, lunge=1.0, crouch=7.5, tw=-1.0, lean=1.4, off="two"),
            K_(-100, -14, -66, 12, 42, lunge=0.8, crouch=6.5, tw=-1.05, lean=1.1, off="two"),
            LINK_L]),
    "greatsword_charge": dict(
        label="홀드 차지(들어 올림 → 유지 루프)", ms=[60, 70, 80, 100, 100, 100, 100], loopFrames=[3, 4, 5, 6],
        phases={"raise": [0, 1, 2], "hold": [3, 4, 5, 6]},
        stages=dict(sec=[0.4, 0.8, 1.2], flashSheets=["greatsword_charge_flash_lv1", "greatsword_charge_flash_lv2", "greatsword_charge_flash_lv3"]),
        startsFrom="아무 대검 자세(좌클릭 홀드 시작) — f0 은 앞에서 곧게 들어 올리는 칼", next="greatsword_charge_slam (좌클릭 뗌)",
        frames=[K_(10, 66, 5, 9, 62, crouch=3, lean=0.2, off="two"),
                K_(180, 60, 0, 4, 69, crouch=2.5, lean=-0.4, off="two"),
                K_(180, 58, 0, 5, 66, crouch=4.5, lean=0.2, off="two"),
                _loop(0), _loop(1), _loop(2), _loop(3)]),
    "greatsword_charge_slam": dict(
        label="차지 내려찍기(릴리즈)", ms=[40, 40, 40, 80, 100, 80, 100], impact=3, active=[3], cancel=None,
        arc=(0, 0), rScale=1.3, step=dict(world=12, frames=[1, 2, 3]),
        hitShape=dict(type="wedge", angleDeg=40, lengthRByStage=[1.3, 1.5, 1.8], impactCircle=dict(radiusR=0.35, atWedgeEnd=True),
                      ringStage3=dict(sheet="greatsword_charge_ring"), note="§17 차지: 쐐기 길이 ×1.3/1.5/1.8, 3단은 충격파 링"),
        startsFrom="greatsword_charge 루프 f3~f6 (머리 위로 든 칼)", endsWith="LINK_C 근처 → greatsword_carry_drawn_idle",
        frames=[
            K_(180, 50, 0, 3, 71, crouch=3, lean=-0.7, off="two"),
            K_(0, 42, 0, 14, 61, lunge=0.8, crouch=4, lean=1.3, off="two"),
            K_(0, -28, 0, 20, 41, lunge=1.2, crouch=10, lean=2.3, off="two"),
            K_(0, -60, 0, 20, 33, lunge=1.2, crouch=12.5, lean=2.6, off="two", state="glow"),
            K_(0, -62, 0, 20, 32, lunge=1.2, crouch=13, lean=2.7, off="two"),
            K_(15, -32, 8, 15, 41, lunge=0.6, crouch=7, lean=1.3, off="two"),
            K_(36, -24, 22, 13, 42, lunge=0.3, crouch=4, tw=0.2, lean=0.7, off="two")]),
}

ORDER_K = ["katana_rise", "katana_fall", "katana_crescent"]
ORDER_G = ["greatsword_sweep_cw", "greatsword_cleave", "greatsword_sweep_ccw", "greatsword_charge", "greatsword_charge_slam"]


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
