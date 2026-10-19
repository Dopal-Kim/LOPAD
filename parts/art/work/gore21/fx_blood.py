"""P21 아트 B 단계 1 — 피 fx v5 (assets/sprites/fx/v5/, 계약 dark-brutal §8 이름 그대로).

python3 parts/art/work/gore21/fx_blood.py [이름…] [--no-assets]
  이름 없으면 전부: blood_spray_{slash,stab,crush,pierce} blood_drip blood_pool blood_decal_floor blood_decal_wall
                   tar_ember_hit ash_chips wound_cut stuck_arrow ink_ash_burst
미리보기: out/preview/<이름>.png (어두운 바닥 위 3배)
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gk  # noqa: E402
from gk import BL0, BL1, BL2, BL3, BL4, G, A, Canvas, Drop  # noqa: E402

SRC = "parts/art/work/gore21/fx_blood.py (P21 잔혹 전투 — 피 fx v5)"
SPRAY_MS = [30, 35, 40, 45, 50, 60, 70, 90]
SPD, DRG = 1.7, 0.8      # 1차 비평: 사거리가 짧아 둥근 터짐으로 읽힘 → 멀리·길게
WET = (BL1, BL2, BL3, BL4)
CLOT = (BL0, BL1, BL2, BL3)
AMOUNT = [0.5, 1.0, 1.7]
OUTP = os.path.join(HERE, "out", "preview")


def common(extra):
    m = {"palette": gk.PALETTE_NOTE, "source": SRC, "paletteSwap": "none",
         "paletteSwapNote": "53라운드 Q62 — fx 는 층·지역 바닥 팔레트 교체에서 제외(그린 색 그대로)",
         "unitNote": "길이 필드(pivot 등)는 이 시트 도트 단위. 논리 px = 도트 × pixelScale(0.5)"}
    m.update(extra)
    return m


# ============================================================ 분출 4종
def spray_drops(kind, amount, seed):
    rnd = random.Random(seed)
    m = AMOUNT[amount]
    D = []

    def add(n, ang, spd, rad, land, drag=3.4, t0=(0.0, 0.0), chain=-1, cols=WET):
        for i in range(max(1, int(round(n * m)))):
            a = math.radians(rnd.uniform(*ang))
            s = rnd.uniform(*spd)
            d = Drop(0.0, 0.0, math.cos(a) * s, math.sin(a) * s, rnd.uniform(*rad), rnd.uniform(*t0), rnd.uniform(*land), drag,
                     chain, i, "clot" if cols is CLOT else "blood")
            D.append(d)
    if kind == "slash":
        # 베기: 칼이 지나간 길을 따라 넓게 펼쳐진 띠(초반 이어진 줄기) → 방울로 끊어져 부채꼴로 흩어짐
        n = int(14 * m) + 4
        for i in range(n):
            u = i / (n - 1) - 0.5
            a = math.radians(u * 78 + rnd.uniform(-3, 3))
            s = 470 - 260 * abs(u) * 1.6 + rnd.uniform(-30, 30)
            D.append(Drop(0.0, u * 6.0, math.cos(a) * s, math.sin(a) * s, 1.25 + 0.7 * (1 - abs(u) * 2) * rnd.uniform(0.6, 1.0),
                          abs(u) * 0.02, rnd.uniform(0.2, 0.3), 3.2, 0, i))
        add(10, (-45, 45), (180, 420), (1.0, 1.9), (0.12, 0.28))
        add(22, (-55, 55), (260, 640), (0.5, 0.8), (0.1, 0.26), 3.8)
        add(3, (-25, 25), (90, 160), (1.6, 2.2), (0.08, 0.16), 4.0, cols=CLOT)
    elif kind == "stab":
        # 찌르기: 좁은 줄기가 뿜어져 나옴(0 → 끊김) + 두 번째 맥박 + 뒤로 짧게 튐
        n = int(16 * m) + 5
        for i in range(n):
            a = math.radians(rnd.uniform(-4, 4))
            s = 640 - i * (260 / n) + rnd.uniform(-20, 20)
            D.append(Drop(0.0, 0.0, math.cos(a) * s, math.sin(a) * s, 1.9 - 0.9 * i / n, i * 0.007, rnd.uniform(0.22, 0.3), 3.0, 0, i))
        n2 = int(9 * m) + 3
        for i in range(n2):
            a = math.radians(rnd.uniform(-7, 7))
            s = 430 - i * (180 / n2)
            D.append(Drop(0.0, 0.0, math.cos(a) * s, math.sin(a) * s, 1.5 - 0.6 * i / n2, 0.11 + i * 0.008, rnd.uniform(0.18, 0.26), 3.2, 1, i))
        add(12, (-14, 14), (300, 700), (0.5, 0.9), (0.12, 0.28), 3.6)
        add(4, (160, 200), (80, 160), (0.6, 1.2), (0.06, 0.14), 4.0)
    elif kind == "crush":
        # 부숨: 짧고 굵은 방사 터짐 + 덩어리(검붉은 응혈) + 왕관 모양 고리
        add(12, (-100, 100), (140, 330), (1.6, 2.6), (0.08, 0.2), 4.2)
        add(6, (-80, 80), (90, 200), (1.8, 2.4), (0.06, 0.14), 4.5, cols=CLOT)
        add(26, (-120, 120), (200, 520), (0.5, 1.0), (0.08, 0.22), 4.0)
        n = int(12 * m) + 6
        for i in range(n):
            a = math.radians(-150 + 300 * i / (n - 1) + rnd.uniform(-5, 5))
            sp = rnd.uniform(90, 200)     # 2차 비평: 같은 속도면 완벽한 동그라미 자국이 남음 → 들쭉날쭉
            D.append(Drop(0.0, 0.0, math.cos(a) * sp, math.sin(a) * sp * 0.8, rnd.uniform(0.5, 1.2), 0.0, rnd.uniform(0.05, 0.1), 6.0, 0, i))
    elif kind == "pierce":
        # 꿰뚫음(화살): 나간 쪽으로 가늘고 긴 원뿔 안개 + 굵은 방울 몇 + 들어간 쪽 작은 튐
        add(30, (-11, 11), (480, 860), (0.5, 0.9), (0.14, 0.3), 3.0)
        add(7, (-7, 7), (380, 600), (1.2, 1.8), (0.18, 0.3), 3.0)
        n = int(10 * m) + 4
        for i in range(n):
            a = math.radians(rnd.uniform(-2, 2))
            s = 720 - 30 * i
            D.append(Drop(0.0, 0.0, math.cos(a) * s, math.sin(a) * s, 1.1 - 0.05 * i, i * 0.006, 0.22, 3.0, 0, i))
        add(6, (150, 210), (70, 150), (0.5, 1.0), (0.05, 0.12), 4.0)
    return D


SPRAYS = {  # 틀·피벗(피벗 = 적중점, 오른쪽 = 공격 진행 방향)
    "slash": ((208, 144), (30, 72)),
    "stab": ((224, 80), (22, 40)),
    "crush": ((176, 176), (60, 88)),
    "pierce": ((248, 80), (22, 40)),
}
SPRAY_NOTE = {
    "slash": "베기 — 칼길을 따라 이어진 넓은 피 띠(0~1) → 끊어진 방울이 ±40° 부채꼴로 날아 바닥에 떨어져 납작해지고(4~) 스며든다(6~7)",
    "stab": "찌르기 — 좁은 줄기가 앞으로 뿜어짐(0~2), 두 번째 맥박(3~4), 뒤로 짧게 튐",
    "crush": "부숨(대검·둔기) — 짧고 굵은 방사 터짐 + 검붉은 응혈 덩어리 + 둘레 왕관 고리(0~1)",
    "pierce": "꿰뚫음(화살) — 나간 쪽으로 가늘고 긴 원뿔 안개 + 굵은 방울 몇, 들어간 쪽 작은 튐",
}


def render_spray(kind, amount):
    (W, H), (px, py) = SPRAYS[kind]
    D = spray_drops(kind, amount, seed=2100 + 10 * amount + {"slash": 1, "stab": 2, "crush": 3, "pierce": 4}[kind])
    T = gk.frame_times(SPRAY_MS)
    end_t = T[-1]
    frames = []
    rnd = random.Random(77 + amount)
    for k, t in enumerate(T):
        cv = Canvas(W, H)
        tt = t - SPRAY_MS[k] / 2000.0       # 프레임 가운데 시각
        # 터짐 심(0~1 프레임): 적중점 덩어리
        if k <= 1:
            r = (3.4 if kind != "pierce" else 2.2) * (1.0 + 0.25 * amount) * (1.0 if k == 0 else 0.6)
            cells = gk.blob_cells(px + 2 + 2 * k, py, r, random.Random(5 + k), lobes=6, sy=0.9)
            gk.shade_wet(cv, cells, rnd=rnd)
        SD = [Drop(d.x + px, d.y + py, d.vx * SPD, d.vy * SPD, d.r, d.t0, d.land, d.drag * DRG, d.chain, d.seed, d.kind) for d in D]
        if k < (3 if kind != "crush" else 1):
            gk.draw_ligaments(cv, [d for d in SD if d.chain in (0, 1)], tt, BL2, max_gap=8.0)
        for dd in sorted(SD, key=lambda d: d.r):
            gk.draw_drop(cv, dd, tt, CLOT if dd.kind == "clot" else WET, end_t, soak=0.16)
        frames.append(cv.image())
    return frames


def build_sprays(assets):
    for kind in SPRAYS:
        rows = [render_spray(kind, a) for a in range(3)]
        name = "blood_spray_" + kind
        (W, H), (px, py) = SPRAYS[kind]
        meta = common({
            "action": name, "directions": ["amount1", "amount2", "amount3"],
            "rowsAre": "ENEMY_GORE.amount 1|2|3 (행 0~2). gore 1 = amount1 행만 + 시스템 틴트 어둡게",
            "frameDurationsMs": SPRAY_MS, "loop": False, "pivot": {"x": px, "y": py},
            "anchor": "hitbox_center", "event": "ENEMY_GORE", "cut": kind, "rotate": True, "drawnFacing": "right",
            "flipY": "allowed", "depth": "above",
            "note": SPRAY_NOTE[kind] + ". 피벗 = 적중점. 시스템은 (dirX, dirY) 각도로 회전, 무작위 flipY 로 변주. 바닥에 떨어진 자리에는 끝(6~7 프레임) 무렵 blood_decal_floor 를 남길 것(제안: amount 당 1~3장, 적중점에서 진행 방향 20~70 도트)",
            "decalHint": {"count": [1, 2, 3], "distDots": [20, 70], "spawnAtFrame": 6},
        })
        if assets:
            gk.write_sheet("fx", "v5", name, rows, meta)
        gk.preview(rows, os.path.join(OUTP, name + ".png"))


# ============================================================ 바닥 웅덩이 3변형(퍼짐)
POOL_MS = [120, 140, 160, 180, 200, 220, 240, 240]   # 합 1500 = 계약 §6 1.5초


def pool_cells(rnd, scale, W, H, cx, cy, n=7, base=34.0):
    """여러 타원(메타볼 근사)의 합집합 — 쿼터뷰라 세로 0.55."""
    cells = set()
    lobes = []
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(0, base * 0.55)
        lobes.append((math.cos(a) * d, math.sin(a) * d * 0.55, base * rnd.uniform(0.35, 0.65)))
    lobes.append((0.0, 0.0, base * 0.7))
    for (ox, oy, r) in lobes:
        rr = r * scale
        if rr < 0.8:
            continue
        cells |= gk.disc_cells(cx + ox * scale, cy + oy * scale, rr, sy=0.55)
    return {c for c in cells if 0 <= c[0] < W and 0 <= c[1] < H}


def shade_pool(cv, cells, rnd, hi=2):
    """웅덩이(2차): 테 = BL1(어두운 물가) · 1~2칸 = BL2(얇은 피) · 안쪽으로 갈수록 BL1 → BL0(두꺼운 피, 체크 디더로 경계 흐림),
    윗왼쪽 안쪽에 끊어진 젖은 빛 호(BL3) + 깊은 곳 반사 하이라이트(BL3 2~3 + BL4 hi 도트). 밝은 테두리 고리 금지(1차 비평: 구멍처럼 읽힘)."""
    if not cells:
        return
    import collections
    dist = {}
    q = collections.deque()
    for c in cells:
        x, y = c
        if any((x + dx, y + dy) not in cells for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            dist[c] = 0
            q.append(c)
    while q:
        c = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + dx, c[1] + dy)
            if n in cells and n not in dist:
                dist[n] = dist[c] + 1
                q.append(n)
    dmax = max(dist.values())
    for c, dd in dist.items():
        x, y = c
        chk = (x + y) % 2
        lit_edge = (x - 1, y) not in cells or (x, y - 1) not in cells
        if dd == 0:
            col = BL2 if lit_edge else BL0
        else:
            th = max(6, dmax * 0.6) + 1.3 * math.sin(x * 0.42 + 1.7 * math.cos(y * 0.5)) + 0.8 * math.cos(y * 0.9 - x * 0.2)   # 깊은 곳만, 경계는 들쭉날쭉(동심원 고리 금지 — 2차 비평)
            col = BL0 if dd >= th else BL1
        cv.put(x, y, col)
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    arc = sorted((c for c, dd in dist.items() if dd == 2 and c[1] < cy - 1 and c[0] < cx), key=lambda c: c[0])
    for i, c in enumerate(arc[len(arc) // 4: len(arc) * 3 // 4]):
        if (i // 3) % 2 == 0:
            cv.put(c[0], c[1], BL2)
    if dmax >= 4:
        deep = sorted((c for c, dd in dist.items() if dd >= 3 and c[1] < cy), key=lambda c: (c[0] - (cx - 5)) ** 2 + 3 * (c[1] - (cy - 2)) ** 2)
        if deep:
            x0, y0 = deep[0]
            for dx in range(-1, 2):
                if (x0 + dx, y0) in cells:
                    cv.put(x0 + dx, y0, BL3)
            for c in deep[:hi]:
                cv.put(c[0] - 1, c[1], BL4)


def spikes(cv, cells, rnd, n, lmin, lmax, sy=0.6):
    """튐 가시: 덩어리 가장자리에서 바깥으로 가는 줄 + 끝 방울(왕관 튐)."""
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    rx, ry = (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        x0, y0 = cx + math.cos(a) * rx * 0.8, cy + math.sin(a) * ry * 0.8
        L = rnd.uniform(lmin, lmax)
        x1, y1 = x0 + math.cos(a) * L, y0 + math.sin(a) * L * sy
        for c in gk.line_cells(x0, y0, x1, y1):
            cv.under(c[0], c[1], BL1)
        for c in gk.disc_cells(x1, y1, rnd.uniform(0.6, 1.5), sy=0.8):
            cv.under(c[0], c[1], BL2 if rnd.random() < 0.5 else BL1)


def build_pool(assets):
    W, H = 200, 120
    cx, cy = 100, 60
    rows = []
    for v in range(3):
        rnd0 = random.Random(310 + v * 7)
        state = rnd0.getstate()
        fr = []
        T = gk.frame_times(POOL_MS)
        for k, t in enumerate(T):
            rnd0.setstate(state)
            u = t / T[-1]
            scale = 0.3 + 0.7 * (1 - (1 - u) ** 2.2)
            cells = pool_cells(rnd0, scale, W, H, cx, cy, n=6 + v * 2, base=[44.0, 52.0, 38.0][v])
            cv = Canvas(W, H)
            shade_pool(cv, cells, random.Random(v))
            # 가장자리 위성 방울(퍼지며 이어 붙음)
            r2 = random.Random(900 + v)
            for i in range(8):
                a = r2.uniform(0, 2 * math.pi)
                dd = [60, 70, 52][v] * r2.uniform(0.75, 1.05)
                c2 = gk.disc_cells(cx + math.cos(a) * dd, cy + math.sin(a) * dd * 0.55, r2.uniform(1.0, 2.2), sy=0.6)
                for c in c2:
                    cv.under(c[0], c[1], BL1)
            fr.append(cv.image())
        rows.append(fr)
    meta = common({
        "action": "blood_pool", "directions": ["v0", "v1", "v2"], "rowsAre": "웅덩이 모양 변형 3 (시체마다 무작위)",
        "frameDurationsMs": POOL_MS, "loop": False, "holdLastFrame": True, "pivot": {"x": cx, "y": cy},
        "anchor": "corpse_center", "depth": "floor_decal",
        "spreadNote": "프레임이 퍼짐(0.3 → 1.0)을 그린다 — 이 시트를 재생하면 스케일 트윈 없이 1.0 으로 둘 것(계약 §6 의 1.5초 퍼짐 = 프레임 합 1500ms). 마지막 프레임 유지",
        "note": "시체 밑 피 웅덩이: 가운데 깊고 검은 피(BL0) → 가장자리 얇은 테(BL2), 윗쪽 안쪽 젖은 빛 줄 + 하이라이트 2도트. 둘레 위성 방울은 퍼지며 본 웅덩이에 붙는다. 무작위 flipX 허용",
        "flipX": "allowed",
    })
    if assets:
        gk.write_sheet("fx", "v5", "blood_pool", rows, meta)
    gk.preview(rows, os.path.join(OUTP, "blood_pool.png"), scale=2)


# ============================================================ 바닥 데칼 12 · 벽 데칼 6
def decal_floor(v):
    W, H = 96, 64
    cx, cy = 48, 32
    rnd = random.Random(4000 + v)
    cv = Canvas(W, H)
    kind = ["splat", "splat", "splat", "splat", "spatter", "spatter", "spatter", "smear", "smear", "drops", "drops", "puddle"][v]
    if kind == "splat":            # 둥근 튐 + 위성 방울
        cells = gk.blob_cells(cx, cy, rnd.uniform(9, 13), rnd, lobes=9, sy=0.6, rough=0.7)
        shade_pool(cv, cells, rnd, hi=1)
        spikes(cv, cells, rnd, rnd.randint(5, 9), 4, 12)
        for i in range(rnd.randint(6, 11)):
            a = rnd.uniform(0, 2 * math.pi)
            d = rnd.uniform(11, 24)
            for c in gk.disc_cells(cx + math.cos(a) * d, cy + math.sin(a) * d * 0.6, rnd.uniform(0.6, 1.8), sy=0.7):
                cv.put(c[0], c[1], BL1 if rnd.random() < 0.6 else BL2)
    elif kind == "spatter":        # 방향 튐(오른쪽으로 날아간 방울 꼬리)
        cells = gk.blob_cells(cx - 22, cy, rnd.uniform(4, 6), rnd, lobes=5, sy=0.6)
        shade_pool(cv, cells, rnd, hi=1)
        for i in range(rnd.randint(9, 15)):
            a = math.radians(rnd.uniform(-22, 22))
            d = rnd.uniform(8, 58)
            x, y = cx - 22 + math.cos(a) * d, cy + math.sin(a) * d * 0.6
            r = rnd.uniform(0.6, 2.0) * (1.2 - d / 70)
            tail = 1 + int(r * 2.5)
            for k in range(tail):
                for c in gk.disc_cells(x + k * 0.9, y, max(0.5, r * (1 - k / (tail + 1)))):
                    cv.put(c[0], c[1], BL2 if k == 0 else BL1)
            if r > 1.4:
                cv.put(x - 1, y - 1, BL3)
    elif kind == "smear":          # 끌린 자국(몸이 미끄러진 줄) — 오른쪽으로 갈수록 옅어져 줄무늬로 갈라짐
        y0 = cy + rnd.uniform(-3, 3)
        for x in range(10, 88):
            u = (x - 10) / 78
            w = 7.5 * (1 - u * 0.75) + rnd.uniform(-0.6, 0.6)
            for y in range(int(y0 - w * 0.6), int(y0 + w * 0.6) + 1):
                stripe = (y * 3 + int(u * 7)) % 5
                if u > 0.35 and stripe in (0, 3) and rnd.random() < u:
                    continue
                cv.put(x, y, BL1 if (y - y0) * (y - y0) < (w * 0.3) ** 2 else BL2)
            y0 += rnd.uniform(-0.25, 0.25)
        for c in gk.blob_cells(14, cy, 6, rnd, lobes=4, sy=0.6):
            cv.put(c[0], c[1], BL1)
        cv.put(16, cy - 2, BL3)
        cv.put(17, cy - 2, BL4)
    elif kind == "drops":          # 걸으며 떨어진 방울 줄(절뚝 흘림)
        x = 12.0
        y = cy + rnd.uniform(-4, 4)
        while x < 86:
            r = rnd.uniform(0.9, 2.1)
            cells = gk.disc_cells(x, y, r, sy=0.7)
            for c in cells:
                cv.put(c[0], c[1], BL2)
            for c in cells:
                if (c[0] + 1, c[1]) not in cells or (c[0], c[1] + 1) not in cells:
                    cv.put(c[0], c[1], BL1)
            if r > 1.6:
                cv.put(int(x) - 1, int(y) - 1, BL3)
            for i in range(rnd.randint(0, 2)):
                cv.put(x + rnd.uniform(-4, 4), y + rnd.uniform(-2, 2), BL1)
            x += rnd.uniform(5, 11)
            y += rnd.uniform(-2.5, 2.5)
    else:                          # 작은 고인 웅덩이
        cells = pool_cells(rnd, 1.0, W, H, cx, cy, n=5, base=17.0)
        shade_pool(cv, cells, rnd, hi=1)
    return cv.image(), kind


def decal_wall(v):
    W, H = 72, 112
    cx, cy = 36, 30
    rnd = random.Random(5000 + v)
    cv = Canvas(W, H)
    # 벽에 튄 자국: 가운데 튐(세로로 긴 면) + 방사 방울 + 아래로 흘러내린 줄(굵기·길이 다름)
    r0 = rnd.uniform(5, 8) * (0.8 if v in (3, 5) else 1.0)
    cells = gk.blob_cells(cx, cy, r0, rnd, lobes=7, sy=1.0, rough=0.6)
    gk.shade_wet(cv, cells, base=BL1, lit=BL2, dark=BL0, edge=BL0, hi=BL3, hi_n=1, rnd=rnd)
    for i in range(rnd.randint(10, 18)):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(r0 + 2, r0 + 20)
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        r = rnd.uniform(0.5, 1.6)
        for k in range(1 + int(r * 2)):
            for c in gk.disc_cells(x + math.cos(a) * k * 0.8, y + math.sin(a) * k * 0.8, max(0.5, r * (1 - 0.3 * k))):
                cv.put(c[0], c[1], BL1 if k else BL2)
    runs = rnd.randint(3, 5) + (2 if v in (1, 4) else 0)
    for i in range(runs):
        x = cx + rnd.uniform(-r0 * 0.9, r0 * 0.9)
        L = rnd.uniform(14, 70) * (1.3 if i == 0 else 1.0)
        w = 2 if rnd.random() < 0.45 else 1
        y = cy + rnd.uniform(0, r0 * 0.6)
        yy = y
        while yy < min(H - 3, y + L):
            for dx in range(w):
                cv.put(x + dx, yy, BL1 if dx == 0 else BL2)
            if rnd.random() < 0.07:
                x += rnd.choice((-1, 1))
            yy += 1
        # 흘러내린 끝 방울
        for c in gk.disc_cells(x + (w - 1) * 0.5, yy, 1.2 + 0.3 * w):
            cv.put(c[0], c[1], BL2)
        cv.put(x, yy - 1, BL3)
    return cv.image()


def build_decals(assets):
    fr, kinds = [], []
    for v in range(12):
        im, k = decal_floor(v)
        fr.append(im)
        kinds.append(k)
    meta = common({
        "action": "blood_decal_floor", "directions": ["any"], "frameDurationsMs": [0] * 12, "loop": False,
        "pivot": {"x": 48, "y": 32}, "anchor": "floor_point", "depth": "floor_decal", "static": True,
        "variants": kinds, "directional": [i for i, k in enumerate(kinds) if k in ("spatter", "smear", "drops")],
        "rotateNote": "directional 프레임(튐·끌림·방울 줄)은 오른쪽 = 피가 날아간/끌린 방향 — 시스템이 회전. 나머지는 무작위 회전·flip 허용",
        "byCut": {"slash": [0, 1, 4, 5, 6], "stab": [2, 4, 9], "crush": [0, 1, 2, 3, 11], "pierce": [5, 6, 9], "drag": [7, 8],
                  "limp": [9, 10], "pool_small": [11]},
        "note": "바닥 피 데칼 12변형(한 아틀라스, 정지 그림 — 프레임 = 변형 번호). 노드당 최대 160장(계약 §6). 깊이: 그림자 위·몸 아래",
    })
    if assets:
        gk.write_sheet("fx", "v5", "blood_decal_floor", [fr], meta)
    gk.preview([fr[:6], fr[6:]], os.path.join(OUTP, "blood_decal_floor.png"), scale=3)
    wf = [decal_wall(v) for v in range(6)]
    meta = common({
        "action": "blood_decal_wall", "directions": ["any"], "frameDurationsMs": [0] * 6, "loop": False,
        "pivot": {"x": 36, "y": 30}, "anchor": "wall_face_hit_point", "depth": "wall_decal", "static": True,
        "note": "벽 튐 데칼 6변형(정지). 피벗 = 맞은 높이의 벽면 점, 아래로 흘러내린 줄(최대 ~80도트)은 벽 앞면 위에서만 보이게(바닥 아래로 내려가면 시스템이 벽 앞면 높이로 자를 것). flipX 허용, 회전 금지(중력)",
        "flipX": "allowed", "rotate": False,
    })
    if assets:
        gk.write_sheet("fx", "v5", "blood_decal_wall", [wf], meta)
    gk.preview([wf], os.path.join(OUTP, "blood_decal_wall.png"), scale=3)


# ============================================================ 방울(흘림)
DRIP_MS = [90, 80, 60, 40, 40, 40, 60, 80]


def build_drip(assets):
    W, H = 24, 64
    px, py = 12, 6
    floor = 56
    fr = []
    for k in range(8):
        cv = Canvas(W, H)
        if k <= 2:   # 맺힘 → 늘어남
            r = 1.2 + 0.4 * k
            for c in gk.disc_cells(px, py + 1 + k * 1.5, r, sy=1.0 + 0.3 * k):
                cv.put(c[0], c[1], BL2)
            for y in range(py, py + 1 + k * 2):
                cv.put(px, y, BL1)
            cv.put(px - 1, py + k * 1.5, BL3)
        elif k <= 5:  # 떨어짐(가속)
            y = py + 4 + [0, 14, 34][k - 3]
            for yy in range(int(y - 3 - (k - 3) * 2), int(y)):
                cv.put(px, yy, BL1)
            for c in gk.disc_cells(px, y, 1.4, sy=1.3):
                cv.put(c[0], c[1], BL2)
            cv.put(px, y - 1, BL3)
        else:         # 바닥에 떨어져 퍼짐
            w = 3 + (k - 6) * 2
            for x in range(px - w, px + w + 1):
                cv.put(x, floor, BL1 if abs(x - px) == w else BL2)
            for x in range(px - w + 2, px + w - 1):
                cv.put(x, floor - 1, BL2)
            if k == 6:
                cv.put(px - 3, floor - 4, BL2)
                cv.put(px + 4, floor - 3, BL1)
            cv.put(px - 1, floor - 1, BL3)
        fr.append(cv.image())
    meta = common({
        "action": "blood_drip", "directions": ["any"], "frameDurationsMs": DRIP_MS, "loop": False,
        "pivot": {"x": px, "y": py}, "anchor": "wound_point", "floorDots": floor - py, "depth": "above",
        "note": "적 stage 2 피 흘림(계약 §3: 걸을 때 0.4초마다): 상처에서 방울이 맺혀(0~2) 떨어지고(3~5) 바닥에 퍼짐(6~7). 피벗 = 상처 점, 바닥 = 피벗 아래 floorDots(50) — 상처 높이가 다르면 3~5 프레임을 그 거리만큼 늘이지 말고 그대로(작아서 차이 안 보임). 끝 프레임 자리에 blood_decal_floor 변형 9·10 중 하나",
    })
    if assets:
        gk.write_sheet("fx", "v5", "blood_drip", [fr], meta)
    gk.preview([fr], os.path.join(OUTP, "blood_drip.png"), scale=4)


# ============================================================ 주인공 피격 — 타르 + 불씨 + 재
TAR_MS = [30, 40, 45, 50, 60, 70, 80]


def build_tar(assets):
    W, H = 160, 112
    px, py = 34, 56
    rnd = random.Random(61)
    tar, embers, ash = [], [], []
    for i in range(22):
        a = math.radians(rnd.uniform(-60, 60))
        s = rnd.uniform(140, 380)
        tar.append(Drop(0, 0, math.cos(a) * s, math.sin(a) * s, rnd.uniform(1.4, 3.0), 0.0, rnd.uniform(0.12, 0.26), 4.0, -1, i))
    for i in range(14):
        a = math.radians(rnd.uniform(-80, 80))
        s = rnd.uniform(260, 620)
        embers.append(Drop(0, 0, math.cos(a) * s, math.sin(a) * s, 0.5, rnd.uniform(0, 0.03), rnd.uniform(0.18, 0.36), 3.0, -1, i))
    for i in range(12):
        a = math.radians(rnd.uniform(-100, 100))
        s = rnd.uniform(60, 200)
        ash.append(Drop(0, 0, math.cos(a) * s, math.sin(a) * s, rnd.uniform(0.6, 1.3), rnd.uniform(0, 0.08), 0.4, 2.5, -1, i))
    T = gk.frame_times(TAR_MS)
    fr = []
    for k, t in enumerate(T):
        tt = t - TAR_MS[k] / 2000.0
        cv = Canvas(W, H)
        if k <= 1:   # 균열이 터지는 심: 검은 타르 덩어리 + 안쪽 불빛
            cells = gk.blob_cells(px + 2, py, 4.2 - 1.6 * k, random.Random(9 + k), lobes=6, sy=0.9)
            gk.shade_wet(cv, cells, base=G[1], lit=G[2], dark=G[0], edge=G[0], hi=G[4], hi_n=1)
            if k == 0:
                for c in gk.disc_cells(px + 3, py, 1.6):
                    cv.put(c[0], c[1], A[25])
                cv.put(px + 3, py, A[26])
            else:
                cv.put(px + 4, py, A[23])
        for d in ash:   # 재: 천천히 퍼지며 아래로(쿼터뷰 낙하 — 이 fx 는 회전해도 짧아서 괜찮음)
            if not d.alive(tt):
                continue
            x, y = d.pos(tt)
            y += 40 * max(0.0, tt - d.t0) ** 2 * 10
            c = gk.ASHC[(d.seed + k) % 3]
            for q in gk.disc_cells(x + px, y + py, d.r if k < 5 else d.r * 0.6):
                cv.put(q[0], q[1], c)
        for d in tar:
            dd = Drop(d.x + px, d.y + py, d.vx, d.vy, d.r, d.t0, d.land, d.drag, -1, d.seed)
            gk.draw_drop(cv, dd, tt, (G[0], G[1], G[3], G[5]), T[-1], soak=0.12)   # 2차: 타르가 어둠에 묻힘 → 빛 쪽 G3·하이라이트 G5
        for d in embers:  # 불씨: 밝은 머리 + 식는 꼬리, 늦게는 어두워져 꺼짐
            if not d.alive(tt):
                continue
            age = tt - d.t0
            if age > d.land + 0.05:
                continue
            x, y = d.pos(tt)
            vx, vy = d.vel(tt)
            sp = math.hypot(vx, vy) or 1
            ln = min(7, sp * 0.02)
            hot = age < d.land * 0.5
            cols = [A[19], A[21], A[23]] if hot else [A[18], A[19], A[21]]
            cells = gk.line_cells(x + px - vx / sp * ln, y + py - vy / sp * ln, x + px, y + py)
            for i, c in enumerate(cells):
                cv.put(c[0], c[1], cols[min(2, int(3 * i / max(1, len(cells))))])
            cv.put(x + px, y + py, A[25] if hot else A[21])
        fr.append(cv.image())
    meta = common({
        "action": "tar_ember_hit", "directions": ["any"], "frameDurationsMs": TAR_MS, "loop": False, "pivot": {"x": px, "y": py},
        "anchor": "player_hit_point", "event": "PLAYER_DAMAGED (주인공 피격 — 붉은 피 대신)", "rotate": True, "drawnFacing": "right",
        "flipY": "allowed", "depth": "above",
        "note": "숯빛 망령의 피: 균열이 터지며 검은 타르 덩어리(G0~G2, 하이라이트 G4 1도트)가 공격 진행 방향으로 튀고, 호박 불씨(A19~A26)가 꼬리를 끌며 식고, 재(G5~G8)가 천천히 흩어져 내린다. 피벗 = 맞은 점. 불씨 머리는 보정 영향이 적은 층(가산) 권장(계약 §7)",
        "glowFrames": [0, 1, 2], "emissiveColors": [A[21], A[23], A[25], A[26]],
    })
    if assets:
        gk.write_sheet("fx", "v5", "tar_ember_hit", [fr], meta)
    gk.preview([fr], os.path.join(OUTP, "tar_ember_hit.png"), scale=3)


ASH_MS = [60, 70, 80, 90, 100, 110, 120, 130]


def build_ash(assets):
    """재 부스러기: 주인공 상흔 1단 '재 떨어짐'·피격 뒤 몸에서 떨어지는 숯 조각(아래로 떨어지며 뒤집힘). 회전 금지."""
    W, H = 48, 72
    px, py = 24, 10
    rnd = random.Random(88)
    chips = []
    for i in range(7):
        chips.append(dict(x=rnd.uniform(-8, 8), vx=rnd.uniform(-14, 14), g=rnd.uniform(60, 110), w=rnd.choice((1, 2, 2, 3)),
                          ph=rnd.randint(0, 3), t0=rnd.uniform(0, 0.15)))
    T = gk.frame_times(ASH_MS)
    fr = []
    for k, t in enumerate(T):
        cv = Canvas(W, H)
        for c in chips:
            tt = t - c["t0"]
            if tt < 0:
                continue
            x = px + c["x"] + c["vx"] * tt + 2 * math.sin(tt * 9 + c["ph"])
            y = py + 0.5 * c["g"] * tt * tt * 2
            if y > H - 2:
                continue
            flip = (k + c["ph"]) % 4
            w = c["w"]
            cols = (G[3], G[5], G[7])
            if flip in (0, 2):
                for dx in range(w):
                    cv.put(x + dx, y, cols[1] if dx else cols[2] if flip == 0 else cols[0])
                if w >= 2:
                    cv.put(x, y + 1, cols[0])
            elif flip == 1:
                cv.put(x, y, cols[1])
                cv.put(x, y + 1, cols[0])
            else:
                cv.put(x, y, cols[2])
        fr.append(cv.image())
    meta = common({
        "action": "ash_chips", "directions": ["any"], "frameDurationsMs": ASH_MS, "loop": False, "pivot": {"x": px, "y": py},
        "anchor": "player_wound_point (chestAnchors 또는 박힌 화살 앵커)", "rotate": False, "depth": "above",
        "note": "숯 부스러기 7조각이 뒤집히며 아래로 떨어진다(재 G3·G5·G7). 주인공 상흔 1단 이상일 때 대기·걷기 중 1.2~2초마다 chestAnchors 에서 1회(2단 0.8초·3단 0.5초 제안), 피격 때 tar_ember_hit 과 함께 1회",
        "suggestIntervalMs": {"stage1": [1200, 2000], "stage2": [800, 1200], "stage3": [500, 800]},
    })
    if assets:
        gk.write_sheet("fx", "v5", "ash_chips", [fr], meta)
    gk.preview([fr], os.path.join(OUTP, "ash_chips.png"), scale=4)


# ============================================================ 적 상처 스탬프 10
def wound(v):
    W = H = 24
    c0 = 12
    rnd = random.Random(7000 + v)
    cv = Canvas(W, H)
    kind = ["slash"] * 4 + ["stab"] * 2 + ["crush"] * 2 + ["pierce"] * 2
    k = kind[v]
    if k == "slash":
        L = [17, 20, 14, 22][v]
        ang = math.radians([-20, 15, -35, 5][v])
        ux, uy = math.cos(ang), math.sin(ang)
        nx, ny = -uy, ux
        pts = []
        for i in range(L):
            u = i / (L - 1) - 0.5
            w = (1 - (2 * u) ** 2) * (2.2 if v != 2 else 1.6)
            x = c0 + ux * u * L
            y = c0 + uy * u * L
            pts.append((x, y, w))
        # 피 젖음 테(BL2) → 벌어진 살(BL3 위 가장자리) → 검은 틈(BL0)
        for x, y, w in pts:
            for s in range(-int(w + 2), int(w + 2) + 1):
                cv.under(x + nx * s, y + ny * s, BL2 if abs(s) > w else BL1)
        for x, y, w in pts:
            for s in range(-int(w), int(w) + 1):
                cv.put(x + nx * s, y + ny * s, BL0 if abs(s) < max(1, w - 1) else BL1)
            cv.put(x - nx * (w + 1), y - ny * (w + 1), BL3)
        x, y, w = pts[len(pts) // 2]
        cv.put(x - nx * (w + 1) - ux, y - ny * (w + 1) - uy, BL4)
        # 흘러내림
        for i in range(rnd.randint(1, 3)):
            x, y, w = pts[rnd.randint(2, len(pts) - 3)]
            for dy in range(1, rnd.randint(3, 7)):
                cv.under(x, y + w + dy, BL1)
    elif k == "stab":
        r = [2.6, 2.0][v - 4]
        for c in gk.disc_cells(c0, c0, r + 2.4, sy=1.0):
            cv.put(c[0], c[1], BL2)
        for c in gk.disc_cells(c0, c0, r + 0.8):
            cv.put(c[0], c[1], BL1)
        for c in gk.disc_cells(c0, c0, r * 0.7):
            cv.put(c[0], c[1], BL0)
        cv.put(c0 - 2, c0 - 2, BL3)
        cv.put(c0 - 3, c0 - 1, BL4)
        for dy in range(3, 10 + 3 * (v - 4)):
            cv.put(c0 + (1 if dy > 6 else 0), c0 + dy, BL1 if dy % 4 else BL2)
    elif k == "crush":
        # 짓눌린 멍 + 터진 상처: 넓고 어두운 얼룩(BL0/BL1) + 갈라진 짧은 틈 2~3
        cells = gk.blob_cells(c0, c0, 6.0 if v == 6 else 5.0, rnd, lobes=6, sy=0.85, rough=0.6)
        for c in cells:
            cv.put(c[0], c[1], BL1 if (c[0] + c[1]) % 5 else BL0)
        for j in range(3 if v == 6 else 2):
            a = rnd.uniform(0, math.pi)
            for t in range(-3, 4):
                cv.put(c0 + math.cos(a) * t + rnd.uniform(-0.4, 0.4), c0 + math.sin(a) * t, BL0)
        cv.put(c0 - 2, c0 - 3, BL3)
        cv.put(c0 - 1, c0 - 3, BL4)
    else:  # pierce — 화살·탄 구멍(작은 구멍 + 흘러내린 줄 두 갈래)
        cx = c0 + (2 if v == 9 else 0)
        for c in gk.disc_cells(cx, c0 - 3, 2.4):
            cv.put(c[0], c[1], BL2)
        for c in gk.disc_cells(cx, c0 - 3, 1.2):
            cv.put(c[0], c[1], BL0)
        cv.put(cx - 1, c0 - 5, BL4)
        for dy in range(0, 12):
            cv.put(cx - 1 + (dy // 5), c0 - 1 + dy, BL1)
            if dy < 8 and v == 8:
                cv.put(cx + 1, c0 - 1 + dy, BL2 if dy % 3 else BL1)
    return cv.image(), k


def build_wounds(assets):
    fr, kinds = [], []
    for v in range(10):
        im, k = wound(v)
        fr.append(im)
        kinds.append(k)
    meta = common({
        "action": "wound_cut", "directions": ["any"], "frameDurationsMs": [0] * 10, "loop": False, "pivot": {"x": 12, "y": 12},
        "anchor": "enemy_body_hit_point", "static": True, "variants": kinds,
        "byCut": {"slash": [0, 1, 2, 3], "stab": [4, 5], "crush": [6, 7], "pierce": [8, 9]},
        "rotate": "slash 0~3 만(칼길 각도에 맞춰 ±30°), 나머지 회전 금지(흘러내림 = 아래)",
        "drawRule": "적 몸 위(몸 스프라이트 바로 위 깊이)에, 적 실루엣 안에만(마스크 권장 — 바깥으로 1~3도트 나갈 수 있음). 적중 방향 쪽 몸 가장자리에서 6~14도트 안으로. 적이 방향을 바꾸면 스탬프도 좌우를 뒤집어 같은 쪽에(4방향 단순화 허용)",
        "note": "적 상처 스탬프 10(16~22도트): 베인 자국 4(검은 틈 + 벌어진 살 테 + 피 젖음 + 흘러내림) · 찔린 구멍 2 · 짓눌린 터짐 2 · 화살 구멍 2. stage 1 = 2~3장, stage 2 = 4~6장(계약 §3)",
    })
    if assets:
        gk.write_sheet("fx", "v5", "wound_cut", [fr], meta)
    gk.preview([fr], os.path.join(OUTP, "wound_cut.png"), scale=5, bg=(92, 84, 70))


# ============================================================ 박힌 화살 5각도
ARROW_ANG = [-90, -120, -150, 180, 150]   # 화면 각(오른쪽 0, 위 −90): 박힌 점 → 깃 쪽


def build_stuck_arrow(assets):
    import sys as _s
    _s.path.insert(0, os.path.join(HERE, "..", "v2_outer"))
    import kit
    WD = kit.WD
    W = H = 56
    px, py = 28, 28
    fr = []
    for ang in ARROW_ANG:
        cv = Canvas(W, H)
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        L = 22
        shaft = gk.line_cells(px + ux * 1, py + uy * 1, px + ux * L, py + uy * L)
        for i, c in enumerate(shaft):
            cv.put(c[0], c[1], WD[3] if i % 6 else WD[2])
        for i, c in enumerate(shaft[:len(shaft) // 2]):          # 그늘 한 줄(빛 = 왼위)
            q = (c[0] + (1 if nx > 0 else -1) * (abs(nx) > 0.5), c[1] + (1 if ny > 0 else -1) * (abs(ny) > 0.5))
            if q not in cv.p:
                pass
        # 깃(뼈빛 회색 G6·G8 — 삼각 두 장)
        for k in range(5):
            bx, by = px + ux * (L - 1 - k), py + uy * (L - 1 - k)
            w = 2 if k < 3 else 1
            for s in (1, -1):
                for j in range(1, w + 1):
                    cv.put(bx + nx * s * j + ux * j * 0.6, by + ny * s * j + uy * j * 0.6, G[8] if s > 0 else G[6])
        cv.put(px + ux * (L + 1), py + uy * (L + 1), WD[1])   # 오늬
        # 박힌 자리: 검은 타르 + 불씨 1(숯빛 망령) — 몸 위에만 보이도록 작게
        cv.put(px, py, G[0])                                   # 2차 비평: 3×3 검은 점이 총알 구멍처럼 읽힘 → 2도트 + 불씨 1
        cv.put(px + ux, py + uy, G[0])
        cv.put(px - round(nx), py - round(ny), A[21])
        fr.append(cv.image())
    meta = common({
        "action": "stuck_arrow", "directions": ["any"], "frameDurationsMs": [0] * 5, "loop": False, "pivot": {"x": px, "y": py},
        "anchor": "hero arrowAnchors (player/v3/hero_wound*_<몸 시트>.json 의 arrowAnchors)", "static": True,
        "angles": ARROW_ANG, "angleNote": "프레임 i = 화면 각 angles[i](오른쪽 0°, 위 −90°) — 박힌 점(피벗)에서 깃 쪽 방향. flipX 하면 180−각(오른쪽으로 뻗는 화살)",
        "note": "주인공 몸에 박힌 화살(원거리 피격마다 1대, 최대 5 — 계약 §3). 박힌 자리 타르 + 불씨 1도트. 각 앵커의 프레임별 variant(=프레임)·flipX·depth(above = 몸 위, below = 몸 뒤)는 오버레이 JSON arrowAnchors 를 따른다",
    })
    if assets:
        gk.write_sheet("fx", "v5", "stuck_arrow", [fr], meta)
    gk.preview([fr], os.path.join(OUTP, "stuck_arrow.png"), scale=5, bg=(60, 60, 64))


# ============================================================ gore 0 대체 — 먹·재
def build_ink(assets):
    (W, H), (px, py) = (176, 112), (28, 56)
    rnd = random.Random(404)
    ink, ash = [], []
    for i in range(18):
        a = math.radians(rnd.uniform(-45, 45))
        s = rnd.uniform(160, 460)
        ink.append(Drop(0, 0, math.cos(a) * s, math.sin(a) * s, rnd.uniform(0.6, 2.0), 0.0, rnd.uniform(0.12, 0.28), 3.5, -1, i))
    for i in range(14):
        a = math.radians(rnd.uniform(-70, 70))
        s = rnd.uniform(80, 240)
        ash.append(Drop(0, 0, math.cos(a) * s, math.sin(a) * s, rnd.uniform(1.0, 2.2), rnd.uniform(0, 0.05), 0.42, 2.2, -1, i))
    T = gk.frame_times(SPRAY_MS)
    fr = []
    for k, t in enumerate(T):
        tt = t - SPRAY_MS[k] / 2000.0
        cv = Canvas(W, H)
        if k <= 1:
            for c in gk.blob_cells(px + 2, py, 3.6 - k, random.Random(3 + k), lobes=5):
                cv.put(c[0], c[1], G[1])
        for d in ash:
            if not d.alive(tt):
                continue
            x, y = d.pos(tt)
            r = d.r * (1 + 0.6 * (tt - d.t0) / 0.42)
            col = G[6] if k < 4 else (G[5] if k < 6 else G[4])
            if k >= 7 and d.seed % 2:
                continue
            for c in gk.disc_cells(x + px, y + py, r):
                if (c[0] + c[1] + d.seed) % 3:
                    cv.under(c[0], c[1], col)
        for d in ink:
            dd = Drop(d.x + px, d.y + py, d.vx, d.vy, d.r, d.t0, d.land, d.drag, -1, d.seed)
            gk.draw_drop(cv, dd, tt, (G[0], G[1], G[2], G[3]), T[-1], soak=0.16)
        fr.append(cv.image())
    meta = common({
        "action": "ink_ash_burst", "directions": ["any"], "frameDurationsMs": SPRAY_MS, "loop": False, "pivot": {"x": px, "y": py},
        "anchor": "hitbox_center", "event": "ENEMY_GORE (settings.gore 0 일 때 blood_spray_* 대신)", "rotate": True,
        "drawnFacing": "right", "flipY": "allowed", "depth": "above",
        "note": "고어 끔(gore 0) 대체: 피 대신 먹물 방울(G0~G2)이 튀고 재 연기(G4~G6, 성긴 도트)가 퍼지며 식는다. 데칼 남기지 않음",
    })
    if assets:
        gk.write_sheet("fx", "v5", "ink_ash_burst", [fr], meta)
    gk.preview([fr], os.path.join(OUTP, "ink_ash_burst.png"), scale=3)


STEPS = {"blood_spray": build_sprays, "blood_pool": build_pool, "blood_decal": build_decals, "blood_drip": build_drip,
         "tar_ember_hit": build_tar, "ash_chips": build_ash, "wound_cut": build_wounds, "stuck_arrow": build_stuck_arrow,
         "ink_ash_burst": build_ink}

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    assets = "--no-assets" not in sys.argv
    for k, fn in STEPS.items():
        if not args or any(a in k or k in a for a in args):
            fn(assets)
            print("ok", k)
