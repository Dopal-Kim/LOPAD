"""61라운드 활 — 화살 가시성(어둠에서) · 서 있는 자세에서 시작하는 화살비(bow_arrow_rain_stand).

1) fx/v3/bow_arrow: 48×24 한 장 → 128×28 4프레임 루프. 화살 픽셀은 피벗 기준 같은 자리(옛 그림 그대로, 화살대만 한 단 밝힘 + 혼불 실 한 줄),
   깃 뒤로 길게 끌리는 불티 꼬리(호박 → 재)와 깜빡이는 불씨 — 어두운 방에서도 날아가는 길이 보이게. 시스템 광원 제안(light).
2) 화살비 서서 시작: combo56_moves_db 의 몸·무기 리그(활 B)를 import 만 해서, '서 있는(활을 내려 든) 자세 → 들어 올려 화살 맺힘' 2프레임을
   기존 화살비 12프레임 앞에 붙인 14프레임 몸·무기 시트를 새 이름으로 만든다(기존 bow_arrow_rain 은 그대로 — 당긴 채 좌클릭 경로).
"""
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wk61 import (Cv, Rand, A17, A18, A19, A21, A23, A25, S0, S1, S2, S3, B2, B3, old_meta, old_grid)  # noqa: E402

SRC = "parts/art/work/weapons61/build.py bow (61라운드 활 화살 가시성 · 서서 시작하는 화살비)"
AW, AH = 128, 28
APIV = (104, 14)


def arrow_frames():
    m = old_meta("fx", "bow_arrow")
    old = old_grid("fx", "bow_arrow").crop((0, 0, m["frameWidth"], m["frameHeight"]))
    ox, oy = APIV[0] - m["pivot"]["x"], APIV[1] - m["pivot"]["y"]
    lift = {S0[:3]: S1, S1[:3]: S2, S2[:3]: S3}
    op = old.load()
    pts = [(x, y, op[x, y]) for y in range(old.height) for x in range(old.width) if op[x, y][3] == 255]
    tail_x = min(x for x, y, c in pts) + ox            # 깃 끝
    frames = []
    for i in range(4):
        cv = Cv(AW, AH)
        r = Rand(4100 + i)
        cy = APIV[1]
        # 꼬리(먼저 — 화살 아래)
        L = tail_x - 6
        for x in range(6, tail_x + 2):
            t = (tail_x - x) / float(L)                # 0 = 화살 쪽, 1 = 꼬리 끝
            wob = 1 if ((x + i * 3) // 5) % 3 == 0 else 0
            if t < 0.18:
                core, side = A25, A23
            elif t < 0.4:
                core, side = A23, A21
            elif t < 0.65:
                core, side = A21, A19
            elif t < 0.85:
                core, side = A19, A18
            else:
                core, side = S1, S0
            if t > 0.85 and (x + i) % 2:
                continue
            cv.put(x, cy + wob * (1 if t > 0.5 else 0), core)
            if t < 0.6:
                cv.put(x, cy - 1, side)
                if t < 0.35 or (x + i) % 2 == 0:
                    cv.put(x, cy + 1, side)
        # 깜빡이는 불씨(꼬리를 따라 흩어짐, 프레임마다 자리 바뀜)
        for k in range(9):
            x = 10 + r.i(0, tail_x - 14)
            t = (tail_x - x) / float(L)
            y = cy + r.i(-4, 4) * (0.5 + t)
            cv.put(x, y, [A25, A23, A21, A19][min(3, int(t * 4))])
        # 화살(옛 그림 그대로, 회색 한 단 밝게)
        for (x, y, c) in pts:
            cv.put(x + ox, y + oy, lift.get(c[:3], c))
        # 혼불 실(화살대 윗면 한 줄) + 촉 반짝(프레임 교대)
        shaft = [(x + ox, y + oy) for (x, y, c) in pts if c[:3] in lift and abs(y + oy - cy) <= 1]
        if shaft:
            ys = min(y for x, y in shaft)
            xs = sorted(x for x, y in shaft if y == ys)
            for x in xs[len(xs) // 3:]:
                if (x + i) % 4 != 0:
                    cv.put(x, ys, A21)
        tip = max(x for x, y, c in pts) + ox
        cv.put(tip + 1, cy if i % 2 == 0 else cy - 1, A25)
        frames.append(cv.im)
    meta = {k: v for k, v in m.items() if k not in ("design", "note", "colors", "source", "fps", "glowRule")}
    meta.update(
        pivot={"x": APIV[0], "y": APIV[1]}, loop=True, anim="loop_move", version="v3-r61", source=SRC, depth="above", flipY="allowed",
        glowFrames=[0, 1, 2, 3], glowRule="투사체는 나는 동안 계속 판정 — 옛 그림의 촉 A26 을 그대로 둠(53라운드 그림과 같음)",
        design=("재 화살(옛 그림 — 대만 한 단 밝힘 + 혼불 실 한 줄) + 깃 뒤로 약 90 도트 끌리는 불티 꼬리(호박 A25 → A19 → 재) + 꼬리를 따라 깜빡이는 불씨 9점. "
                "어두운 방에서도 화살이 지나간 길이 보이게(점검 61_bow_grid '화살이 가늘고 짧게 살아 있어 비행이 잘 보이지 않음')"),
        axisNote="옛 bow_arrow(48×24, 피벗 (24,12)) 와 같은 축 — 화살 픽셀은 피벗 기준 같은 자리, 꼬리 쪽(왼쪽)으로 80 도트·위아래 2 도트 넓힘",
        light={"color": "#e2a33c", "radius": 56, "intensity": 0.55, "flicker": {"amp": 0.2, "hz": 12}, "offset": {"x": APIV[0] - 8, "y": APIV[1]},
               "note": "제안 — 날아가는 화살에 작은 광원(어둠 3국면·어두운 방). 시스템 광원 수 상한에 걸리면 생략"},
        previous="parts/art/work/weapons61/prev/fx/bow_arrow.png (48×24 한 장)",
        r61="61라운드 시스템 보고 — 활 화살 가시성(어둠에서)",
    )
    return "bow_arrow", [frames], AW, AH, meta, [50, 50, 50, 50], True


# =========================================================================================== 화살비 서서 시작
STAND_JOB = r'''
import json, os, sys
sys.path.insert(0, %(db)r)
sys.path.insert(0, os.path.join(%(db)r, "..", "combo56_body"))
import moves_db as M
import bodies_db as B
from gear3 import K_
bd = M.bd
src = M.RAIN
# 서 있는 자세: 왼손에 활을 몸 앞에 내려 듦(휴대와 비슷, 시위에 손 없음) → 들어 올리며 오른손이 시위로, 재가 맺혀 화살(가득 전)
stand = [
    K_(0, 0, R=(4.0, 9.0, 40.0), L=(14.0, -7.0, 44.0), crouch=1.5, tw=0.1, lean=0.2, tension=0.0, state="settle"),
    M.up_key(14, 0.45, "draw", lean=-0.25, crouch=2.2, tw=0.55, tension=0.45),
]
n = len(stand)
RS = dict(src)
RS["label"] = "화살비(서서 시작)"
RS["frames"] = stand + list(src["frames"])
RS["angles"] = [0, 14] + list(src["angles"])
RS["ms"] = [70, 60] + list(src["ms"])
RS["roles"] = ["stand", "raise_nock"] + list(src["roles"])
RS["releaseFrames"] = [i + n for i in src["releaseFrames"]]
RS["cancel"] = src["cancel"] + n
RS["phases"] = {"stand": [0, 1], "raise": [i + n for i in src["phases"]["raise"]], "volley": [i + n for i in src["phases"]["volley"]],
                "recover": [i + n for i in src["phases"]["recover"]]}
RS["startsFrom"] = "bow_carry_idle·bow_carry_walk(서 있거나 걷는 중 — 당기지 않은 상태)에서 화살비 입력"
RS["endsWith"] = src["endsWith"]
M.MOVES["bow_arrow_rain_stand"] = RS
B.SRC = %(src)r
fr = B.render("bow_arrow_rain_stand")
st = B.check("bow_arrow_rain_stand", fr)
data = B.export("bow_arrow_rain_stand", fr)
print(json.dumps(st))
'''


def build_rain_stand():
    """하위 프로세스에서(그 빌드는 모듈 상태를 바꿈) 몸·무기 격자 시트를 assets 에 쓴다. 반환: 쓴 시트 이름."""
    db = os.path.normpath(os.path.join(HERE, "..", "combo56_moves_db"))
    code = STAND_JOB % {"db": db, "src": SRC}
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=db)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-3000:])
    print("rain_stand", r.stdout.strip()[-400:])
    return [("player", "player_bow_arrow_rain_stand"), ("weapons", "bow_arrow_rain_stand")]
