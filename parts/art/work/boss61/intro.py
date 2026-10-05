"""61라운드 시스템 D 요청 — 보스 '만취' 등장 포즈(intro, 인트로 약 5초 동안 재생).

비틀거리며 다가옴(걷기 루프, 시스템이 거리만큼 반복) → 멈칫 딸꾹 → 술통 잔을 머리 위로 치켜들어 건배(유지 루프)
→ 고개 젖혀 껄껄 포효(roarFrame — 보스 이름 카드·포효 효과음 시점) → 대기 자세로 이어짐(마지막 칸 ≈ idle 0).
54라운드 b1acts 의 자세 도구(P_·W·L)와 걷기 키를 import 해서 새 동작만 만든다(hires.py 가 판 크기를 1.5배로 바꾼 뒤 import).
"""
import math

import b1acts as BA
from b1acts import P_, W, L, TAU


def act_intro(d):
    base = P_()
    walk = []
    for i, k in enumerate(BA.act_walk(d)):
        a = TAU * i / 8
        walk.append(W(k, roll=k["roll"] * 1.7 + 3.0 * math.sin(a * 0.5), lean=-3.0, eye="half",
                      fx={"mouth": "grin", "jig": 1.2 * math.cos(2 * a)}))
    hic = W(BA.act_idle(d)[4], fx={"cup": {"slosh": 2}})
    toast = P_(root=(0.0, 0.0, -1.0), lean=-9.0, head=(-16.0, 0.0, 2.0), handR=(8.0, 28.0, 138.0), elbowR=(0.0, 1.0, -0.2),
               handL=(10.0, -40.0, 66.0), eye="wide",
               fx={"cup": {"axis": (0.05, 0.12, 1.0), "slosh": 2, "fill": 0.9}, "mouth": "grin", "jig": 1.2, "cape": (0.0, 1.0)})
    toast2 = W(toast, root=(0.0, 0.0, -2.0), handR=(9.0, 29.0, 140.0), fx={"cup": {"slosh": 1}, "jig": -0.6})
    roar = W(toast, root=(0.0, 0.0, -5.0), lean=-14.0, head=(-24.0, 0.0, 0.0), handL=(12.0, -46.0, 96.0), elbowL=(-0.2, -1.0, 0.0),
             fx={"mouth": "roar", "jig": 2.4, "cup": {"slosh": 2},
                 "splash": {"c": (10.0, 40.0, 132.0), "k": 0.6, "n": 10, "dirv": (0.0, -1.0), "spread": 2.2, "seed": 31}})
    roar2 = W(roar, root=(0.0, 0.0, -6.0), fx={"jig": 1.2, "splash": None})
    return walk + [hic, L(hic, toast, 0.5), toast, toast2, roar, roar2, L(roar2, base, 0.5), L(roar2, base, 0.85)]


META = dict(ms=[150] * 8 + [220, 110, 200, 200, 160, 280, 140, 160], loop=False,
            phaseFrames={"approach": [0, 1, 2, 3, 4, 5, 6, 7], "stumble": [8], "toast": [9, 10, 11], "roar": [12, 13], "settle": [14, 15]},
            walkLoop=[0, 7], toastLoop=[10, 11], roarFrame=12,
            stride={"px": 86, "cycleMs": 1200},
            note=("등장(인트로 약 5초): 휘청이며 다가옴(0~7 루프 — 시스템이 걸어 들어올 거리만큼 반복, stride) → 멈칫 딸꾹(8) → 술통 잔을 머리 위로 "
                  "치켜들어 건배(9 → 10~11 유지 루프) → 고개 젖혀 껄껄 포효(12 = roarFrame, 이름 카드·포효음) → 대기로(15 ≈ idle 0). "
                  "예: 걷기 2바퀴 2.4초 + 건배 유지 1.2초 + 나머지 0.96초 ≈ 4.6초"))


def install():
    BA.ACTIONS["intro"] = act_intro
    BA.META["intro"] = META
