"""56라운드 Q7·Q8 — 퍼펙트 가드·패링 섬광 fx/v3/guard_perfect_fx (문구 'PERFECT GUARD'·'PARRY' 는 시스템이 텍스트로).

행 = 종류(방향 아님): guard(퍼펙트 가드 — 튕겨내지 않고 피해 0) · parry(패링 성공 — 튕겨냄).
그림은 '오른쪽 = 공격이 들어온 쪽'으로 그렸다(drawnFacing right, rotate) — 시스템이 주인공 → 공격자 방향으로 돌린다.
  · 공통 f0: 맞닿은 점에 짧은 세로 백열 틈 + 작은 십자(판정 순간) → f1: 앞을 막는 재·호박 방패 호(가드 면)
  · guard: 호가 그 자리에 버티고(밀리지 않음), 불티는 호를 타고 아래로 흘러내려 떨어지고, 호는 재로 식어 부서진다 — '받아 냄'
  · parry: 호가 공격 쪽으로 튕겨 나가며 펴지고, 불티·빛살이 공격자 쪽 원뿔로 튄다 + 작은 글린트 — '쳐냄'
기존 parry_flash(가운데 동심 고리)·guard_wave 와 겹쳐 써도 되고 대신 써도 된다(질문 사항).
"""
import math
import random

import rk
from rk import W, FK

C = 240
MS = [30, 40, 50, 60, 70, 80, 90]
GLOW = [0, 1]


def arc_shield(L, cx, cy, r, half, w, v, open_=1.0, dash=None):
    """앞(오른쪽)을 막는 호: 중심 (cx - r, cy) 에서 반지름 r, ±half."""
    L.arc(cx - r, cy, r, r * 1.15, -half * open_, half * open_, w, prof=FK.tp_both(0.6, 0.5), v=v, dash=dash)


def frames(kind, seed):
    c = C / 2
    rng = random.Random(seed)
    out = []
    D = W.Debris(seed)
    T = W.T("any", c, c)
    if kind == "guard":
        for k in range(14):                                  # 호를 타고 흘러내리는 불티(아래로)
            a = rng.uniform(-0.9, 0.9)
            p = (math.cos(a) * 30 - 30 + 2, math.sin(a) * 34)
            D.spawn("ember", p, (rng.uniform(-0.6, 0.4), rng.uniform(0.5, 2.0)), born=1, life=5, size=rng.uniform(2, 3.5),
                    v=rng.uniform(0.7, 1.0), g=1.2)
        for k in range(8):
            a = rng.uniform(-1.0, 1.0)
            D.spawn("flake", (math.cos(a) * 30 - 30, math.sin(a) * 34), (rng.uniform(-0.8, 0.3), rng.uniform(0.2, 1.0)), born=3,
                    life=4, size=rng.uniform(1.2, 2.0), v=0.9, g=0.9)
    else:
        for k in range(20):                                  # 공격자 쪽 원뿔로 튀는 불티
            a = rng.uniform(-0.75, 0.75)
            sp = rng.uniform(5, 10)
            D.spawn("ember", (2, rng.uniform(-6, 6)), (math.cos(a) * sp, math.sin(a) * sp), born=1, life=4, size=rng.uniform(3, 5.5),
                    v=rng.uniform(0.75, 1.0), g=0.5)
        for k in range(6):
            a = rng.uniform(-1.2, 1.2)
            D.spawn("flake", (0, 0), (math.cos(a) * 3, math.sin(a) * 3), born=2, life=4, size=1.6, v=0.9, g=0.6)
    for i in range(len(MS)):
        f = rk.frame(C, C)
        Lk = f.L([rk.S0, rk.S1, rk.S2, rk.S3])
        La = f.L([rk.A17, rk.A18, rk.A19, rk.A21, rk.A23, rk.A25])
        Lh = f.L([rk.A25, rk.A26, rk.X1, rk.X0])
        Le = f.L([rk.A19, rk.A21, rk.A23, rk.A25])
        if i == 0:                                           # 맞닿은 순간: 세로 백열 틈 + 작은 십자
            Lh.stroke([(c, c - 16), (c, c + 16)], 1.6, prof=FK.tp_both(0.7, 0.5), v=1.0)
            Lh.ray(c, c, 0, 0, 14, 1.1, prof=FK.tp_tail(0.8), v=0.9)
            Lh.ray(c, c, math.pi, 0, 8, 1.0, prof=FK.tp_tail(0.8), v=0.8)
            La.stamp(c, c, 4.5, 0.9, soft=0.6)
        elif kind == "guard":
            k = (i - 1) / (len(MS) - 2)
            if i == 1:
                arc_shield(Lh, c + 2, c, 30, 0.95, 2.0, 0.9)
                arc_shield(La, c, c, 30, 1.0, 3.6, 0.95)
                Lh.stroke([(c + 1, c - 9), (c + 1, c + 9)], 1.0, prof=FK.tp_both(0.7, 0.5), v=0.8)
            elif i <= 3:
                arc_shield(La, c, c, 30, 1.0, 3.2 - 0.6 * (i - 2), 0.95 - 0.12 * (i - 2))
                arc_shield(Lk, c - 3, c, 30, 1.05, 1.4, 0.8)
            else:
                arc_shield(Lk, c, c + 2 * (i - 3), 30, 1.0, 2.6 - 0.4 * (i - 4), 0.85 - 0.15 * (i - 4),
                           dash=(14, 0.75 - 0.15 * (i - 4), 0.1 * i))
                if i == 4:
                    arc_shield(La, c, c, 30, 0.6, 1.4, 0.55, dash=(12, 0.5, 0.2))
        else:
            k = (i - 1) / (len(MS) - 2)
            push = 10 * k ** 0.6
            if i == 1:
                arc_shield(Lh, c + 3, c, 26, 0.9, 2.0, 0.9)
                arc_shield(La, c + 1, c, 26, 1.0, 3.8, 0.95)
                for a in (-0.5, 0.0, 0.5):                   # 공격자 쪽 빛살 3
                    Lh.ray(c + 4, c, a, 4, 26 if a == 0 else 18, 1.2, prof=FK.tp_tail(0.8), v=0.9)
            elif i <= 3:
                r = 26 + 10 * k                              # 호가 펴지며 앞으로 튕겨 나감
                arc_shield(La, c + push, c, r, 1.0, 3.2 - 0.8 * (i - 2), 0.95 - 0.15 * (i - 2))
                Le.star4(c + 18 + push, c - 12, 5 - (i - 2) * 2, w=0.7, v=0.85)
            else:
                r = 26 + 14 * k
                arc_shield(Lk, c + push, c, r, 1.05, 2.0 - 0.4 * (i - 4), 0.8 - 0.15 * (i - 4), dash=(12, 0.6 - 0.12 * (i - 4), 0.2))
        D.draw(f, T, {"ember": Le, "flake": Lk}, i)
        out.append(f.render())
    return out


def build():
    rows = ["guard", "parry"]
    fr = {"guard": frames("guard", 91), "parry": frames("parry", 92)}
    fr, piv = rk.fit_centered(fr, (C // 2, C // 2))
    meta = dict(weapon="any", rowsAre="kinds", rowBy="kind",
                directionsNote="directions 칸에 종류(guard·parry)를 넣었다 — 행 = 종류. 방향은 rotate 로(아래 drawnFacing)",
                kindInfo={"guard": "퍼펙트 가드(가드 누른 직후 0.15초 안 피격 — 피해 0, 튕겨내지 않음, 56라운드 Q7). 문구 'PERFECT GUARD' 는 시스템 텍스트",
                          "parry": "패링 성공(튕겨냄). 문구 'PARRY' 는 시스템 텍스트"},
                anchor="guard_contact", pivot={"x": piv[0], "y": piv[1]},
                pivotNote="pivot = 맞닿은 점(가드 면). 권장 위치 = 주인공 판정 원점(피벗 위 40 도트)에서 공격자 쪽으로 24 도트(논리 12px)",
                rotate=True, drawnFacing="right", flipY="allowed",
                rotateNote="그림의 오른쪽 = 공격이 들어온 쪽. 주인공 → 공격자(또는 투사체) 방향 각도로 돌린다. 위아래 대칭이라 flipY 해도 됨",
                depth="above", spawn="perfect_guard | parry_success", impactFrame=0, glowFrames=GLOW,
                frameRoles={"guard": ["맞닿음 백열 틈(판정)", "방패 호(받아 냄)", "호 버팀·불티 흘러내림", "버팀", "식어 부서짐", "재", "사라짐"],
                            "parry": ["맞닿음 백열 틈(판정)", "호 + 공격자 쪽 빛살", "호가 튕겨 나가며 펴짐·글린트", "튕겨 나감", "끊긴 재 호", "재", "사라짐"]},
                hitstopNote="히트스톱 정지 프레임 권장 = 열 1(holdFrame)", holdFrame=1,
                light={"color": "#eecc78", "radius": 90, "intensity": 0.9, "frames": [0, 1, 2]},
                shakeHint={"guard": {"px": 2, "ms": 70}, "parry": {"px": 3, "ms": 90}},
                pairsWith="퍼펙트 가드·패링 성공 순간에만 이 시트 — 그 순간의 parry_flash(가운데 동심 고리)·guard_wave 를 대체(56라운드 Q55). 일반 가드(퍼펙트 아님)의 guard_wave 는 그대로 유지(56라운드 Q62)",
                design="56라운드 Q7 퍼펙트 가드·패링 — 맞닿은 점의 짧은 세로 백열 틈 → 재·호박 방패 호. guard 는 버티고 불티가 흘러내림, parry 는 호가 공격 쪽으로 튕겨 나가며 불티 원뿔")
    return rk.write_sheet("guard_perfect_fx", rk.OUT_FX, rows, fr, MS, meta, glow=GLOW)


if __name__ == "__main__":
    s, j, _ = build()
    print(j["frameWidth"], j["frameHeight"], j["colors"])
