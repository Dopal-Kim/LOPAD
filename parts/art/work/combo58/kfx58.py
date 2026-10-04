"""58라운드 칼 3타 찌르기 이펙트 — 붓 한 획 찌르기(丿 가 아니라 곧게 뻗은 一) · 검기 단수(0~3)별 4변형.

  fx/v3/katana_thrust       검기 0 — 재 테·호박 심의 가늘고 긴 붓 찌르기(1.3R)
  fx/v3/katana_thrust_ki1   검기 1 — 더 길게(1.5R) · 획 위로 재 연기 두 줄
  fx/v3/katana_thrust_ki2   검기 2 — 1.7R · 굵고 호박 심이 밝음 · 획을 따라 불티
  fx/v3/katana_thrust_ki3   검기 3 — 1.9R · 가장 굵음 · 칼끝 앞에서 꿰뚫는 불꽃 고리 + 획 위 불꽃 혀 · 백열은 판정 2칸의 획 머리만
4행 = 칼 몸 행(down, up, left, right). 그림은 조준 0°(right)를 각 행 각도로 회전해 다시 래스터(left = 180°, 거울 아님 — §17 규칙).
좌표·도구 = combo56_fx/fx56.py(TA 회전 · Frame · write) — 붓은 brush.Stroke.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "combo56_fx"))
sys.path.insert(0, HERE)
import fx56 as F  # noqa: E402
from fx56 import BR, W  # noqa: E402

OUT_FX = os.path.normpath(os.path.join(WORK, "../../../assets/sprites/fx/v3"))
SRC = "parts/art/work/combo58/build.py kfx (58라운드 Q1 칼 3타 찌르기 붓획 · 검기 단수별)"

MS = [30, 40, 40, 60, 70, 80]                 # pre · draw(판정) · 꿰뚫음 유지 · 소멸 ×3
IMPACT = 1
LV = {
    0: dict(name="katana_thrust", wmax=8.0, ink=BR.INK_K, glow=[1], smoke=0, embers=0, ring=False, flames=False, seed=581),
    1: dict(name="katana_thrust_ki1", wmax=9.0, ink=BR.INK_K, glow=[1], smoke=3, embers=3, ring=False, flames=False, seed=582),
    2: dict(name="katana_thrust_ki2", wmax=10.5, ink=[W.A17, W.A18, W.A19, W.A21, W.A23, W.A25], glow=[1], smoke=1, embers=7,
            ring=False, flames=False, seed=583),
    3: dict(name="katana_thrust_ki3", wmax=12.5, ink=[W.A18, W.A19, W.A21, W.A23, W.A25], glow=[1], smoke=1, embers=10,
            ring=True, flames=True, seed=584),
}
DESIGN = {
    0: "3타 찌르기(검기 0) — 칼끝을 따라 앞으로 곧게 뻗은 가는 붓 한 획(시작 가늘고 · 가운데 굵고 · 끝은 붓털이 갈라짐), 재 테·호박 심",
    1: "검기 1 — 0단보다 길고(1.5R) 조금 굵은 획 · 획 위로 가는 재 연기 두 줄",
    2: "검기 2 — 1.7R · 획 몸이 호박으로 달아오름 · 획을 따라 불티가 튐",
    3: "검기 3 — 1.9R · 가장 굵은 호박 획 · 획 위 불꽃 혀 · 칼끝 앞에서 꿰뚫는 불꽃 고리(판정 칸 머리만 백열)",
}


BLADE_LIFT = {"left": 20.0, "right": 20.0}
START_DOTS = {"up": 58.0}            # 몸 f4 칼끝 높이(무기 bladeTipAnchors) − 판정 원점 높이


def thrust_len(lv):
    import k58  # noqa: F401  (판정 길이 표 — 몸 JSON 과 같은 값)
    return k58.RD * k58.THRUST_LEN_R[lv]


def _len_only(lv):
    R = 152.0
    return R * {0: 1.30, 1: 1.50, 2: 1.70, 3: 1.90}[lv]


def frames_for(d, lv):
    cfg = LV[lv]
    t = F.TA(d, *F.CO)
    x0, x1 = START_DOTS.get(d, 16.0), _len_only(lv) + 4.0     # 뒷면(up)은 몸·머리 뒤를 지나는 앞부분을 비움(fx 가 몸 위에 그려지므로)
    n = 60
    lift = BLADE_LIFT.get(d, 0.0)                       # 옆 방향: 칼날 높이(판정 원점 위 ~20 도트)에 맞춤
    pts = [t((x0 + (x1 - x0) * i / n, 0.6 * math.sin(math.pi * i / n))) for i in range(n + 1)]
    pts = [(x, y - lift) for x, y in pts]
    S = BR.Stroke(pts, cfg["wmax"], seed=cfg["seed"], peak=0.55, dry_from=0.78, split=0.8, drops=5 + 2 * lv,
                  start_w=0.1, end_w=0.6)
    plan = [("pre", 0.35), ("draw", 1.0), ("hold", 1.0), ("decay", 0.33), ("decay", 0.66), ("decay", 1.0)]
    r = random.Random(cfg["seed"])
    out = []
    prev_tail = 0.0
    for i, (kind, p) in enumerate(plan):
        fr = F.frame(None)
        Lf = fr.L(BR.FLAKE)
        Ls = fr.L([W.S0, W.S1, W.S2])
        Lb = fr.L(cfg["ink"])
        Le = fr.L([W.A19, W.A21, W.A23])
        Lfl = fr.L([W.A18, W.A19, W.A21, W.A23, W.A25])
        Lh = fr.L(BR.HOT)
        hot = i in cfg["glow"]
        if kind == "pre":
            S.draw(Lb, head=p, vmax=0.6, drops=False)
        elif kind in ("draw", "hold"):
            S.draw(Lb, head=1.0, vmax=0.92, hot=hot, Lhot=Lh if hot else None)
        else:
            tail = 0.15 + 0.6 * p
            S.draw(Lb, head=1.0, tail=tail, vmax=0.9 * (0.9 - 0.2 * p), wk=1 - 0.3 * p, k=p, fall=2 + 6 * p)
            S.flakes(Lf, p, max(0.0, prev_tail - 0.05), tail + 0.08, 3 + lv, size=1.4, fall=8.0, seed=i)
            prev_tail = tail
        # 연기(검기 1~3): 획 위에서 위로 꼬불꼬불(화면 위 = 불·연기는 위로)
        if cfg["smoke"] and i >= 1:
            for k in range(cfg["smoke"]):
                s0 = 0.35 + 0.3 * k
                (sx, sy), _ = S.at(s0)
                age = (i - 1) / 4.0
                pts_ = [(sx + 2.6 * math.sin(i * 1.3 + k * 2 + u * 4.0) * u, sy - 3 - (10 + 16 * age) * u) for u in [j / 8 for j in range(9)]]
                Ls.stroke(pts_, 1.05, prof=lambda u: 0.6 + 0.4 * math.sin(math.pi * min(1, u * 1.4)), v=1.0 - 0.4 * age, vprof=lambda u: 1.0 - 0.6 * u, soft=0.2)
        # 불티(검기 1~3): 획을 따라 앞·위로 튐
        if cfg["embers"] and 1 <= i <= 4:
            rr = random.Random(cfg["seed"] * 7)
            age = (i - 1) / 3.0
            for k in range(cfg["embers"]):
                s = rr.uniform(0.3, 1.0)
                (ex, ey), (nx, ny) = S.at(s)
                tx, ty = S.tangent_end()
                a = math.atan2(ty, tx) + rr.uniform(-0.9, 0.9) - 0.5
                dist = rr.uniform(2, 6) + age * rr.uniform(10, 18)
                W.ember(Le, ex + math.cos(a) * dist, ey + math.sin(a) * dist - age * rr.uniform(4, 10) + age * age * 6,
                        math.cos(a), math.sin(a), rr.uniform(2.0, 3.5) * (1 - 0.5 * age), w=0.6, v=0.95 - 0.35 * age)
        # 불꽃 혀(검기 3): 획 윗면에서 화면 위로
        if cfg["flames"] and 1 <= i <= 4:
            rr = random.Random(cfg["seed"] + 3)
            age = (i - 1) / 3.0
            for k in range(7):
                s = 0.25 + 0.7 * k / 6 + rr.uniform(-0.03, 0.03)
                if i >= 3 and s < 0.15 + 0.6 * plan[i][1]:
                    continue
                (fx_, fy_), (nx, ny) = S.at(s)
                hh = (5 + 6 * rr.random()) * (1 - 0.45 * age)
                ph = rr.random() * 6.28 + i * 1.7
                tip = [(fx_ + 1.2 * math.sin(ph + u * 2.6) * u, fy_ - cfg["wmax"] * 0.25 - hh * u) for u in [j / 6 for j in range(7)]]
                Lfl.stroke(tip, 1.3, prof=lambda u: 1.0 - 0.9 * u, v=0.85, vprof=lambda u: 1.0 - 0.8 * u, soft=0.3)
        # 꿰뚫는 불꽃 고리(검기 3): 칼끝 바로 앞, 진행 방향으로 납작한 고리(판정 칸 ~ 소멸 1)
        if cfg["ring"] and 1 <= i <= 3:
            ex, ey = S.p[-1]
            tx, ty = S.tangent_end()
            nx, ny = -ty, tx
            rad = [7, 11, 14][i - 1]
            cx, cy = ex + tx * (4 + 3 * (i - 1)), ey + ty * (4 + 3 * (i - 1))
            ring = []
            for j in range(33):
                a = 2 * math.pi * j / 32
                ring.append((cx + tx * math.cos(a) * rad * 0.35 + nx * math.sin(a) * rad,
                             cy + ty * math.cos(a) * rad * 0.35 + ny * math.sin(a) * rad))
            Lfl.stroke(ring, [1.1, 0.9, 0.7][i - 1], v=[0.55, 0.75, 0.55][i - 1], soft=0.2,
                                             dash=(6.0, 0.7, 0.1 * i) if i > 1 else None)
        out.append(fr.render())
    return out


def build(levels=(0, 1, 2, 3)):
    import json
    from gridcompat import body_meta
    bj = body_meta("player/v3/player_katana_thrust")
    hit = bj["timingMs"]["hitAt"]
    spawn = hit - sum(MS[:IMPACT])
    res = []
    for lv in levels:
        cfg = LV[lv]
        frames = {d: frames_for(d, lv) for d in F.DIRS4}
        cut, pivot, origin = F.X.fit(frames, include_pivot=True)
        hs = dict(bj["hitShape"]["byKiLevel"][str(lv)])
        upd = dict(anchor="player_pivot", pivot={"x": pivot[0], "y": pivot[1]}, hitOriginInFrame={"x": origin[0], "y": origin[1]},
                   pivotNote="pivot = 주인공 발(몸 피벗). 판정 원점 = pivot 위 40 도트(hitOriginInFrame)",
                   effectRule=F.X.__dict__.get("EFFECT_RULE", "56라운드 Q11 붓획 규칙"), brushStroke=True,
                   weapon="katana", move="katana_thrust", kiLevel=lv, design=DESIGN[lv],
                   r58="58라운드 Q1 — 3타 찌르기 · 검기 단수만큼 사거리·위력↑(이 시트 = 소모 단수 %d)" % lv,
                   kiRule="이번 찌르기에 소모한 검기 단수로 고른다: 0 = katana_thrust, 1~3 = katana_thrust_ki1~3. 길이 = 몸 JSON hitShape.byKiLevel",
                   variants={"0": "katana_thrust", "1": "katana_thrust_ki1", "2": "katana_thrust_ki2", "3": "katana_thrust_ki3"},
                   hitShape=hs, drawnThrust=dict(fromDots=16.0, fromDotsByDirection={"up": 58.0}, toDots=round(_len_only(lv) + 4, 1), brushWidthDots=cfg["wmax"],
                                                  note="붓획 끝 = 판정 lengthPx(+4 도트 붓털)"),
                   spawn="body_ms", spawnAtMs=spawn, impactAtBodyMs=hit, impactFrame=IMPACT,
                   spawnRule="spawnAtMs = 몸 hitAt − sum(frameDurationsMs[:impactFrame])",
                   frameRoles=["pre(칼끝을 따라 그어 나감)", "draw(끝까지 · 판정 · 머리 백열)", "꿰뚫음 유지(히트스톱 정지 칸)", "decay(뒤부터 마름)", "decay", "decay(재)"],
                   holdFrame=2, holdNote="히트스톱 정지 칸 = 다 그어진 다음 칸(56라운드 Q37)",
                   directions=F.DIRS4, dirTransform="drawn4",
                   directionNote="4행 = 칼 몸 행 순서(down, up, left, right). 조준 0° 그림을 각 행 각도로 회전해 다시 그림(left = 180°, 거울 아님)")
        F.SRC = SRC
        F.VERSION = "v3-r58"
        sheet, j, _ = F.write(cfg["name"], cut, F.DIRS4, MS, None, upd, cfg["glow"], OUT_FX)
        res.append((cfg["name"], j["frameWidth"], j["frameHeight"], j["colors"]))
        print(cfg["name"], j["frameWidth"], j["frameHeight"], "colors", j["colors"])
    return res


if __name__ == "__main__":
    build()
