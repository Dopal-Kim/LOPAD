"""P21 아트 B 단계 3 — 잘린 조각 fx/v5/gore_parts_<적>: 행 head·arm·upper, 열 = 회전 8(45° 씩 시계 방향).

같은 리그(erig)로 대기 0 프레임(down)을 렌더해 부위만 남기거나(머리·오른팔) 허리에서 갈라(윗몸) 단면을 칠한다.
python3 parts/art/work/gore21/gore_parts.py [적…] [--no-assets]
"""
import importlib
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import enemy_death as ED  # noqa: E402  (리그 훅·단면 도구)
import gk  # noqa: E402
from gk import BL0, BL1, BL2, BL3, G  # noqa: E402
from PIL import Image  # noqa: E402

ROWS = ["head", "arm", "upper"]
PROPS = ("gun", "hammer", "shield", "flag", "pole", "drum", "stick", "jige", "spare", "crate", "lamp", "bottle", "gourd", "jar", "cork",
         "rope", "front", "club", "barrel", "strap")   # 들고·메고 있던 소품(윗몸 조각에서 뺌 — 1차 비평: 깃발·망치까지 날아감)


def stump(im, x, y, r=2.6):
    for c in gk.disc_cells(x, y, r, sy=0.7):
        ED.put(im, c[0], c[1], BL2)
    for c in gk.disc_cells(x, y, r - 1.0, sy=0.7):
        ED.put(im, c[0], c[1], BL0)
    ED.put(im, x, y, G[13])
    ED.put(im, x - 1, y - 1, BL3)


def pieces(eid):
    mod = importlib.import_module(ED.MODS[eid])
    p = mod.ACTIONS["idle"]("down")[0]
    out, spawn = {}, {}
    full, S, B = ED.render(mod, "down", p)
    piv = B.piv
    # 머리
    im, S, B = ED.render(mod, "down", p, ED.is_head)
    nx, ny = ED.scr(B, S.neck)
    stump(im, nx, ny + 1)
    out["head"] = im
    spawn["head"] = ED.scr(B, S.head)
    # 오른팔(어깨에서)
    arm = lambda n: n.startswith(("arm", "hand", "sleeve", "cuff", "mitt", "glove", "pauldron")) and n.endswith("R")  # noqa: E731
    im, S, B = ED.render(mod, "down", p, arm)
    if not im.getbbox():
        raise SystemExit(eid + ": 팔 부위 이름을 못 찾음")
    sx, sy = ED.scr(B, S.shR)
    stump(im, sx, sy, 2.4)
    out["arm"] = im
    spawn["arm"] = ED.scr(B, S.arms["R"][1])
    # 윗몸(허리에서 가름 — 머리 포함, 소품 뺌)
    full, S, B = ED.render(mod, "down", p, lambda n: not n.startswith(PROPS))
    wx, wy = ED.scr(B, S.waist)
    q = ED.scr(B, ED.erig.add(S.waist, ED.erig.mul(S.up, 10.0)))
    vl = math.hypot(q[0] - wx, q[1] - wy) or 1
    ux, uy = (q[0] - wx) / vl, (q[1] - wy) / vl
    rnd = random.Random(sum(map(ord, eid)))
    jv = [rnd.uniform(-1.2, 1.2) for _ in range(9)]
    jag = lambda a: jv[int(a // 5) % 9] if abs(a) < 40 else 0.0  # noqa: E731
    up, _ = ED.split_by_line(full, wx, wy, ux, uy, jag)
    ED.cut_face(up, wx, wy, ux, uy, jag, +1, rnd)
    out["upper"] = up
    spawn["upper"] = ED.scr(B, S.chest)
    return out, {k: {"x": round(v[0] - piv[0], 1), "y": round(v[1] - piv[1], 1)} for k, v in spawn.items()}


def despeckle(im):
    """외딴 점(몸 밖 먼지·불티 post) 지움 — 8이웃이 하나도 없는 픽셀."""
    px = im.load()
    W, H = im.size
    on = {(x, y) for y in range(H) for x in range(W) if px[x, y][3]}
    for (x, y) in on:
        if not any((x + dx, y + dy) in on for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
            px[x, y] = (0, 0, 0, 0)
    return im


def build(eid, assets):
    parts, spawn = pieces(eid)
    parts = {k: despeckle(v) for k, v in parts.items()}
    rots = {}
    for k in ROWS:
        im = parts[k].crop(parts[k].getbbox())
        pad = Image.new("RGBA", (im.width + 4, im.height + 4), (0, 0, 0, 0))
        pad.alpha_composite(im, (2, 2))
        rots[k] = [pad.rotate(-45 * i, resample=Image.NEAREST, expand=True) for i in range(8)]
    F = max(max(r.width, r.height) for lst in rots.values() for r in lst)
    F += F % 2
    rows = []
    for k in ROWS:
        row = []
        for r in rots[k]:
            fr = Image.new("RGBA", (F, F), (0, 0, 0, 0))
            fr.alpha_composite(r, ((F - r.width) // 2, (F - r.height) // 2))
            row.append(fr)
        rows.append(row)
    meta = {"action": "gore_parts", "enemy": eid, "directions": ROWS, "rowsAre": "조각 종류 head · arm(오른팔, 어깨에서) · upper(허리 위 윗몸 — 두 동강의 위)",
            "frameDurationsMs": [50] * 8, "loop": True, "pivot": {"x": F // 2, "y": F // 2},
            "rotationNote": "열 i = 45°×i 시계 방향 회전(0 = 선 자세 그대로). 나는 동안 루프(굴러 감), 멈추면 restFrame 에 고정",
            "restFrame": {"head": 2, "arm": 2, "upper": 2},
            "spawnFromEnemyPivot": spawn,
            "spawnNote": "적(down 대기) 피벗 기준 도트 — 머리 = 머리 중심, 팔 = 팔꿈치, 윗몸 = 가슴. 다른 방향은 x 를 방향에 맞춰 뒤집어 근사",
            "physicsHint": {"flightMs": [500, 900], "speedDots": [120, 260], "upDots": [20, 40], "bounce": 1,
                            "note": "계약 dark-brutal §6: 짧게 날아 튀고 바닥에 남아 시체 수에 포함. 떨어진 자리에 blood_decal_floor(0~3) 1장 + 끌린 자국(7·8) 제안"},
            "event": "ENEMY_DEATH_VARIANT behead → head · bisect → upper(사망 변형 시트가 윗몸을 이미 그림 — 날려 보낼 때만) · 대검 넘친 피해 절단 → arm(시스템 재량)",
            "gore": "settings.gore 2 에서만(1·0 은 조각 없음)",
            "source": "parts/art/work/gore21/gore_parts.py (같은 리그 erig — 대기 0 down 에서 부위만)",
            "palette": "적 본 색 + 피 7층 '적' 램프 어두운 4단(고정) + 뼈 G13. 새 색 없음", "depth": "floor_object"}
    name = "gore_parts_" + eid
    if assets:
        gk.write_sheet("fx", "v5", name, rows, meta)
    gk.preview(rows, os.path.join(HERE, "out", "preview", name + ".png"), scale=3, bg=(52, 50, 48))
    print("ok", name, F, flush=True)


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if not a.startswith("-")] or ED.ENEMIES
    for e in names:
        build(e, "--no-assets" not in sys.argv)
