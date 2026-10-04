"""56라운드 Q6 — 주인공 v3 8방향 투영 (대각 4방향 추가). hero_v3·weapons_v3·combo55 모듈은 고치지 않고 이 프로세스 안에서만 확장한다.

대각 = 화면 45° (마우스 방향과 휘두르는 방향 일치, Q6).
  리그 투영(katana3.project)은 바닥 깊이를 KY(0.35)로 눌러 그린다 → 화면 45° 로 보이는 '바라보는 방향'은 바닥 각 a(tan a = tan 45° / KY ≈ 70.7°).
  즉 화면 대각을 보는 몸은 정면(또는 뒷면)에서 약 19° 돌아선 자세다 → 대각 몸 = 정면/뒷면 몸 Rig(draw_front)에
  3/4 단서(가슴 비틀림·머리·발을 바라보는 쪽으로)를 더해 그리고, 무기·손은 대각 바닥 각으로 투영한다.
행 순서(시트): down, up, left, right, down-right, down-left, up-right, up-left (기존 4행 뒤에 대각 4행).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
C55 = os.path.normpath(os.path.join(HERE, "..", "combo55"))
sys.path.insert(0, C55)

import moves as M55  # noqa: E402  (weapons_v3·hero_v3 경로도 넣음)
from moves import wv3, Q  # noqa: E402
from wv3 import K, EX, hero  # noqa: E402

DIRS4 = ["down", "up", "left", "right"]
DIAG = ["down-right", "down-left", "up-right", "up-left"]
DIRS8 = DIRS4 + DIAG
SCREEN_DEG = {"right": 0.0, "down-right": 45.0, "down": 90.0, "down-left": 135.0, "left": 180.0,
              "up-left": -135.0, "up": -90.0, "up-right": -45.0}
BASE = {"down-right": "down", "down-left": "down", "up-right": "up", "up-left": "up"}
SX = {"down-right": 1, "down-left": -1, "up-right": 1, "up-left": -1}           # 바라보는 쪽 화면 x 부호


def ground_deg(d):
    """화면 각 → 리그 바닥 각(바닥 깊이 KY 압축을 되돌림)."""
    s = math.radians(SCREEN_DEG[d])
    return math.degrees(math.atan2(math.sin(s) / K.KY, math.cos(s)))


def _install():
    for d in DIAG:
        a = math.radians(ground_deg(d))
        F = (math.cos(a), math.sin(a))
        Rv = (-F[1], F[0])                     # 해부 오른쪽 = 바라보는 방향을 화면 시계 방향으로 90°(기존 4방향과 같은 규칙)
        K.FACING[d] = (F, Rv)
    # 기존 4방향이 같은 규칙인지 확인(오른쪽 = 시계 90°)
    for d in DIRS4:
        F, Rv = K.FACING[d]
        assert (round(-F[1], 6), round(F[0], 6)) == (round(Rv[0], 6), round(Rv[1], 6)), d


_install()

# 3/4 단서 세기(설계 단위) — 대각 몸만
TWIST_BIAS = 2.4        # 가슴 중심이 바라보는 쪽으로
HEAD_BIAS = 1.6         # 머리 화면 x
FOOT_BIAS = 2.2         # 디딤발이 바라보는 쪽으로


def body_pose8(d, k, i):
    """gear3.body_pose 와 같은 규칙 + 대각(정면/뒷면 몸 + 3/4 단서)."""
    if d in DIRS4:
        return Q.body_pose(d, k, i)
    base = BASE[d]
    sx = SX[d]
    hR = K.to_screen(d, k["R"])
    hL = K.to_screen(d, k["L"])
    m = 1 if base == "down" else -1           # draw_front 의 X(dx) = 32 + m*dx
    kw = dict(handAt={"R": hR[:2], "L": hL[:2]}, crouch=k["crouch"], flame=i % 6,
              pulse=1 if k["state"] in ("glow", "full", "materialize") else 0,
              lean=-2.0 * k["tw"] - 1.5 * sx, tension=k["tension"])
    lg, tuck = k["lunge"], k["tuck"]
    sgn = 1 if base == "down" else -1
    kw.update(step=(-2.0 * lg * sgn, 4.5 * lg * sgn),
              footdx=(1.0 * lg + sx * FOOT_BIAS * (0.4 + 0.6 * lg), -1.0 * lg + sx * FOOT_BIAS * (0.2 + 0.8 * lg)),
              twist=-3.2 * k["tw"] + m * sx * TWIST_BIAS, shift=-1.0 * k["tw"] + m * sx * 0.8, stilt=-1.2 * k["tw"],
              squash=0.05 * k["lean"], head=round(k["lean"]), hdx=sx * HEAD_BIAS + sx * 0.5 * k["lean"],
              sway=2.0 * k["tw"] + 2.5 * tuck - sx * 1.0,
              lift=(round(tuck * 7.0), round(tuck * 7.0)))
    kw["armBack"] = tuple(s for s, h in (("R", hR), ("L", hL)) if h[2] < -3.0)
    kw.update(k.get("extra") or {})
    return hero.pose(**kw)


def draw_rig8(d, p):
    if d in DIRS4:
        return hero.draw_rig(d, p)
    R = hero.draw_front(p, back=(BASE[d] == "up"))
    R.render()
    return R
