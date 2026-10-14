"""P19 주인공 역동성 — 이동·피격·사망·방향 전환 자세 (hero_v3 리그 그대로, 새 pose 키 tilt·kneeIK·stanceW·eyeHot).

키아트 parts/art/work/gemini/concept_char/hero3_b.jpg 의 'LOW LUNGING DASH'·'OVERHEAD SLASH' 결:
  낮게 웅크린 포식자(무릎 굽힘·넓은 발·앞으로 숙인 상체·어깨 사이로 내려앉은 머리), 앞으로 기운 질주, 거의 수평으로 파고드는 대쉬.
모든 함수는 direction → [pose dict] (hero.pose). 손은 여기서 정하지 않는다 — build 단계에서 기존 손 기준점 + 프레임 오프셋으로 고정(무기 오버레이 동기).
프레임 수·ms 는 기존 시트와 같다(대기 6 · 걷기 8 · 달리기 8 · 대쉬 5 · 피격 3 · 사망 10). 방향 전환 미끄럼 4 는 새 시트.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hero_v3"))
import hero  # noqa: E402
import motion  # noqa: E402
from hero import pose  # noqa: E402

SIDE = ("left", "right")


# =============================================================================
# 대기 6 — 낮게 웅크린 포식자: 숨에 어깨가 들썩, 머리는 한 박자 늦게, 균열 맥동, 눈빛 깜빡(5)
# =============================================================================
def act_idle(d):
    breath = [0, 1, 3, 3, 1, 0]                       # 들숨이 크고 날숨이 빠름 → '으르렁'
    out = []
    for i in range(6):
        br = breath[i]
        kw = dict(breath=br, head=1 - round(breath[i - 1] * 0.5), flame=i, crouch=4.5, kneeIK=True,
                  pulse=1 if i in (2, 3) else 0, glow=0, eyeHot=1 if i in (1, 2, 3) else 0, eyeOff=(i == 5),
                  sway=[0.0, 0.6, 1.2, 1.2, 0.6, 0.0][i], lean=[0, 1, 0, -1, 0, 1][i] * 1.0)
        if d in SIDE:
            kw.update(foot=((-8.5, 0), (7.5, 0)), tilt=13.0 + 1.5 * br, lean_body=0.8, hdx=2.0)
        else:
            rock = [0.0, 0.5, 1.0, 0.8, 0.0, -0.5][i]
            sg = 1 if d == "down" else -1
            kw.update(stanceW=1.5, squash=0.11 + 0.012 * br, shift=rock - 1.0, twist=rock * 0.6 - 1.2, stilt=rock * 0.8 - 0.5 * br,
                      tilt=rock * 1.2, step=(2.5 * sg, -2.0 * sg), footdx=(1.0, -0.5), head=2 - round(breath[i - 1] * 0.5))
        out.append(pose(**kw))
    return out


# =============================================================================
# 걷기 8 — 낮게 스며드는 사냥 걸음. 발 궤적·보폭은 이전과 같음(stride 72 도트 / 640ms) — 몸만 낮고 앞으로.
# =============================================================================
def act_walk(d):
    base = hero.act_walk(d)
    out = []
    for i, p in enumerate(base):
        q = dict(p)
        phL = 2 * math.pi * (i % 8) / 8.0
        q.update(crouch=3.5, kneeIK=True, eyeHot=1 if i % 4 in (1, 2) else 0)
        if d in SIDE:
            q.update(tilt=11.0 + 2.0 * math.cos(2 * phL), lean_body=1.0, hdx=2.5, head=p["head"] + 1)
        else:
            q.update(stanceW=1.5, squash=0.07, head=p["head"] + 1, tilt=2.0 * math.sin(phL), shift=p["shift"] * 1.4,
                     stilt=p["stilt"] * 1.3)
        out.append(q)
    return out


# =============================================================================
# 달리기 8 — 앞으로 기운 낮은 질주(발 궤적 그대로 = stride 200 도트 / 520ms), 큰 무릎 드라이브, 머리 앞으로
# =============================================================================
def act_run(d):
    base = motion.act_run(d)
    out = []
    for i, p in enumerate(base):
        q = dict(p)
        q.update(crouch=6.0, eyeHot=1, kneeIK=True)
        if d in SIDE:
            q.update(tilt=25.0 + 3.0 * (i % 4 in (2, 3)), lean_body=1.4, hdx=0.5, head=p["head"] + 2, gdx=-5.0)
        else:
            q.update(squash=0.10, head=p["head"] + 2, tilt=1.2 * p["shift"] / 2.2, stanceW=1.0)
        out.append(q)
    return out


# =============================================================================
# 대쉬 5 — 'LOW LUNGING DASH': 웅크림 → 박차 거의 수평으로 늘어남 → 활공 → 제동(앞발 박고 몸이 뒤로 받침)
# =============================================================================
def act_dash(d):
    if d in SIDE:
        K = [  # crouch, tilt, lean_body, hdx, head, far foot, near foot, flame lean, sway
            (8.0, 22.0, 1.0, 2.0, 2, (-9.0, 0), (7.0, 0), -3.0, -2.0, -2.0),
            (10.0, 34.0, 1.0, 2.5, 3, (-17.0, 0), (13.0, 2), -6.0, -6.0, -7.0),
            (11.0, 40.0, 1.0, 3.0, 4, (-18.0, 3), (12.0, 0), -7.5, -8.0, -8.5),
            (10.5, 38.0, 1.0, 3.0, 4, (-17.0, 5), (13.0, 0), -7.5, -7.0, -8.0),
            (8.5, 6.0, 0.3, 0.5, 2, (-12.0, 1), (16.0, 0), -1.0, 3.0, -1.5),
        ]
        return [pose(crouch=cr, tilt=tl, lean_body=lb, hdx=hdx, head=hd, foot=(ff, fn), sway=sw, flame=i + 1, gdx=gx,
                     lean=fl, pulse=i in (1, 2, 3), eyeHot=1, glow=1 if i in (1, 2) else 0, kneeIK=True)
                for i, (cr, tl, lb, hdx, hd, ff, fn, fl, sw, gx) in enumerate(K)]
    sgn = 1 if d == "down" else -1
    K = [  # crouch, squash, head, step L, step R, lift L, lift R, flame lean, sway, footdx, stanceW
        (7.0, 0.14, 2, 1.5, -1.5, 0, 0, -1.0, 0.5, (1.0, -1.0), 2.5),
        (11.0, 0.30, 4, 6.0, -5.0, 0, 3, -2.0, 2.0, (2.5, -2.5), 3.5),
        (13.0, 0.36, 5, 6.5, -5.5, 5, 4, -2.5, 3.0, (3.0, -3.0), 4.0),
        (12.5, 0.34, 5, 6.0, -5.0, 4, 6, 2.5, 2.0, (3.0, -3.0), 4.0),
        (8.0, 0.16, 2, 5.0, -1.5, 0, 0, 1.0, 0.5, (2.0, -1.5), 3.0),
    ]
    return [pose(crouch=cr, squash=sq, head=hd, step=(sL * sgn, sR * sgn), lift=(lL, lR), footdx=fdx, stanceW=sw_,
                 kneeIK=True, sway=sw, flame=i + 1, lean=fl, pulse=i in (1, 2, 3), eyeHot=1, glow=1 if i in (1, 2) else 0,
                 shift=0.8 * (i % 2 * 2 - 1) if i in (2, 3) else 0.0)
            for i, (cr, sq, hd, sL, sR, lL, lR, fl, sw, fdx, sw_) in enumerate(K)]


# =============================================================================
# 피격 3 — 짐승처럼 뒤로 꺾임(척추가 젖혀지고 머리가 튐, 균열 백열·재 튐) → 웅크려 받음 → 이를 드러내듯 다시 숙임
# 손은 자유(이 시트를 몸으로 쓰는 무기 오버레이 없음)
# =============================================================================
def act_hurt(d):
    seed = {"down": 11, "up": 23, "left": 37, "right": 41}[d]
    chips = [dict(t=0.25, n=26, seed=seed, ember=4), dict(t=0.6, n=16, seed=seed, ember=2), dict(t=0.95, n=7, seed=seed, ember=0)]
    if d in SIDE:
        K = [  # crouch, tilt, lean_body, head, hdx, feet(far, near), hands(far, near), flame lean, rows, glow, sway
            (2.5, -22.0, -0.5, -3, -3.5, ((-8.0, 0), (8.0, 0)), ((-9.0, -9.0), (-7.0, -11.0)), 6.0, 4, 2, 4.0),
            (5.5, -6.0, 0.0, -1, -1.0, ((-9.0, 0), (7.0, 0)), ((-5.0, -4.0), (-3.0, -5.0)), 3.0, 3, 1, 2.0),
            (5.0, 15.0, 0.8, 1, 2.0, ((-8.5, 0), (7.5, 0)), ((2.0, -2.0), (4.0, -3.0)), -2.0, None, 0, -1.0),
        ]
        return [pose(crouch=cr, tilt=tl, lean_body=lb, head=hd, hdx=hdx, foot=ft, hand=hn, lean=fl, flameRows=fr, glow=gl,
                     pulse=1, flame=i * 2, sway=sw, eyeHot=1 if i == 2 else 0, kneeIK=True, gdx=[6.0, 2.0, -1.0][i], post=("chips", chips[i]))
                for i, (cr, tl, lb, hd, hdx, ft, hn, fl, fr, gl, sw) in enumerate(K)]
    K = [  # crouch, head, bob, squash, handL, handR, flame lean, rows, glow, shift, tilt
        (1.5, -5, -3, -0.10, (9.0, -10.0), (8.5, -9.0), 4.0, 4, 2, 0.0, 6.0 if d == "down" else -6.0),
        (5.0, -1, -1, 0.02, (5.0, -4.5), (4.5, -4.0), -3.0, 3, 1, 0.8, -2.0 if d == "down" else 2.0),
        (4.5, 1, 0, 0.08, (1.5, -1.0), (1.5, -1.0), 1.5, None, 0, 0.0, 0.0),
    ]
    return [pose(crouch=cr, head=hd, bob=b, squash=sq, hand=(hL, hR), lean=fl, flameRows=fr, glow=gl, pulse=1, flame=i * 2,
                 shift=sh, tilt=tl, sway=[2.0, -1.0, 0.5][i], footdx=(0.5, -0.5), stanceW=2.0, kneeIK=True,
                 eyeHot=1 if i == 2 else 0, post=("chips", chips[i]))
            for i, (cr, hd, b, sq, hL, hR, fl, fr, gl, sh, tl) in enumerate(K)]


# =============================================================================
# 사망 10 — 뒤로 꺾여 비틀 → 무릎 꺾임 → 앞으로 무너져 주저앉음 → 재 무덤(이전 덧칠 그대로) → 눈빛·혼불 꺼짐 → 일기장
# =============================================================================
def act_death(d):
    base = motion.act_death(d)
    out = []
    for i, p in enumerate(base):
        q = dict(p)
        q["kneeIK"] = True
        side = d in SIDE
        if i == 0:
            q.update(tilt=-20.0 if side else (5.0 if d == "down" else -5.0), head=-4, glow=2, eyeHot=1, gdx=5.0 if side else 0.0)
        elif i == 1:
            q.update(tilt=-6.0 if side else 0.0, head=0, gdx=2.0 if side else 0.0)
        elif i == 2:
            q.update(tilt=8.0 if side else 0.0, gdx=-3.0 if side else 0.0)
        elif side:
            q.update(tilt=10.0, gdx=-5.0)
        out.append(q)
    return out


# =============================================================================
# 방향 전환 미끄럼 4 (새 시트 player_turn_skid) — 행 = 새로 향하는 방향. 앞발을 박고 미끄러지며(먼지·불티 fx)
# 몸은 새 방향으로 먼저 틀어 낮게 → 박차고 달리기 0 으로 이어짐. 40·50·50·40 = 180ms(입력은 막지 않는 장식 동작)
# =============================================================================
SKID_MS = [40, 50, 50, 40]


def act_turn_skid(d):
    if d in SIDE:
        K = [  # crouch, tilt, lean_body, hdx, head, far foot, near foot, sway, flame lean
            (7.0, -10.0, 0.0, -1.0, 1, (14.0, 0), (6.0, 0), 5.0, 5.0),     # 미는 발이 새 방향 앞으로 박힘, 몸은 뒤로 받침
            (8.5, 4.0, 0.5, 1.0, 2, (12.0, 0), (-2.0, 0), 4.0, 3.0),      # 미끄러지며 상체가 새 방향으로 넘어옴
            (7.5, 20.0, 1.5, 3.0, 2, (4.0, 0), (-12.0, 3), 0.0, -3.0),     # 뒷발로 박참
            (5.5, 21.0, 2.0, 3.0, 1, (-6.0, 5), (13.0, 2), -3.0, -4.5),    # 달리기 0 쪽으로
        ]
        return [pose(crouch=cr, tilt=tl, lean_body=lb, hdx=hdx, head=hd, foot=(ff, fn), sway=sw, lean=fl, flame=i + 2,
                     pulse=1, eyeHot=1, kneeIK=True)
                for i, (cr, tl, lb, hdx, hd, ff, fn, sw, fl) in enumerate(K)]
    sgn = 1 if d == "down" else -1
    K = [  # crouch, squash, head, step L, step R, footdx, stanceW, shift, twist, tilt, sway
        (7.0, -0.02, 0, -4.0, -3.0, (2.0, -2.0), 4.0, 1.5, 2.0, 4.0, -3.0),
        (8.5, 0.08, 1, -2.0, -4.5, (2.5, -2.5), 4.0, -1.0, -1.5, -3.0, -2.0),
        (7.5, 0.16, 2, 3.0, -2.0, (2.0, -1.5), 3.0, 1.5, 1.0, 2.0, 1.0),
        (5.5, 0.16, 2, 3.5, -1.0, (1.0, -1.0), 1.5, 0.5, 0.5, 0.0, 2.0),
    ]
    return [pose(crouch=cr, squash=sq, head=hd, step=(sL * sgn, sR * sgn), footdx=fdx, stanceW=sw_, shift=sh, twist=tw,
                 tilt=tl, sway=sw, flame=i + 2, pulse=1, eyeHot=1, kneeIK=True)
            for i, (cr, sq, hd, sL, sR, fdx, sw_, sh, tw, tl, sw) in enumerate(K)]


ACTS = {"idle": act_idle, "walk": act_walk, "run": act_run, "dash": act_dash, "hurt": act_hurt, "death": act_death,
        "turn_skid": act_turn_skid}
OLD_ACTS = {"idle": hero.act_idle, "walk": hero.act_walk, "run": motion.act_run, "dash": motion.act_dash,
            "hurt": motion.act_hurt, "death": motion.act_death}
