"""61라운드 AR-5 보스 '만취' 파훼 가독성 — 깰 수 있는 잔 · 기둥 균열 3단 · 되칠 수 있는 술통 · 다시 켤 촛대 · 무너진 동안 표시.

그림 도구: boss1_v3/props.py 의 기둥·술통·촛대 그리기 함수를 import 만 한다(고치지 않음, 그 파일의 main 은 부르지 않음).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "boss1_v3"))
sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))

from k61 import Cv, G, A, X, X0, X1, SL, WD, PL, Rand, dilate, alpha_mask  # noqa: E402
import props as P  # noqa: E402  (boss1_v3 — 그리기 함수만)
from pk import Canvas, stone_blob, R_NSTONE  # noqa: E402
import gridsheet  # noqa: E402

SRC = "parts/art/work/boss61/build.py (61라운드 AR-5 파훼 가독성)"
PAL_F = ("1층 램프 A17~A27 + 백열 X0 #ffffff / X1 #fff4dc + 무채 G — 새 색 없음. paletteSwap none")
EMIS = ["#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0", "#ffffff", "#fff4dc"]


def fx_common(**kw):
    d = dict(version="v3-r61", pixelScale=0.5, paletteSwap="none", drawOver="lightmap",
             drawOverNote="53라운드 Q63 — fx 는 조명 위에 그린다", palette=PAL_F, source=SRC, emissiveColors=EMIS)
    d.update(kw)
    return d


# =========================================================================================== 1. 깰 수 있는 잔
CG = 160
CGP = (80, 88)   # 61라운드 보스 1.5배 네이티브(잔 약 44×55) 기준


def _bracket(cv, cx, cy, hx, hy, arm, col, edge):
    """잔을 둘러싼 네 모서리 꺾쇠(두께 2 + 바깥 1 어두운 테)."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, y0 = cx + sx * hx, cy + sy * hy
            for k in range(arm):
                for t in range(3):
                    cv.put(x0 - sx * k, y0 - sy * t, col)       # 가로
                    cv.put(x0 - sx * t, y0 - sy * k, col)       # 세로
                cv.put(x0 - sx * k, y0 + sy, edge)
                cv.put(x0 + sx, y0 - sy * k, edge)
                if k >= 3:
                    cv.put(x0 - sx * k, y0 - sy * 3, edge)
                    cv.put(x0 - sx * 3, y0 - sy * k, edge)
            cv.put(x0 + sx, y0 + sy, edge)
            cv.put(x0 - sx * arm, y0, edge); cv.put(x0 - sx * arm, y0 - sy, edge); cv.put(x0 - sx * arm, y0 - sy * 2, edge)
            cv.put(x0, y0 - sy * arm, edge); cv.put(x0 - sx, y0 - sy * arm, edge); cv.put(x0 - sx * 2, y0 - sy * arm, edge)
            cv.put(x0, y0, X1)


def _chevron(cv, cx, top, col, edge):
    """잔 위 아래로 향한 쐐기(여기를 쳐라) — 폭 13, 높이 7."""
    for j in range(7):
        half = 6 - j
        for x in range(-half, half + 1):
            cv.put(cx + x, top + j, col if abs(x) < half or j == 0 else edge)
        cv.put(cx - half - 1, top + j, edge); cv.put(cx + half + 1, top + j, edge)
    cv.put(cx, top + 7, edge)
    for x in range(-7, 8):
        cv.put(cx + x, top - 1, edge)


def cup_glint():
    rows = []
    # glint 루프 8프레임
    pulse = [0, 1, 2, 3, 3, 2, 1, 0]
    row = []
    for i in range(8):
        cv = Cv(CG, CG)
        o = pulse[i]
        col = A[25] if o < 2 else A[26]
        _bracket(cv, CGP[0], CGP[1], 31 + o, 36 + o, 15, col, A[17])
        _chevron(cv, CGP[0], CGP[1] - 36 - 16 - [0, 1, 2, 3, 3, 2, 1, 0][i], col, A[17])
        # 빛 쓸기(잔 위 비스듬한 2도트 띠, 2~5)
        if 2 <= i <= 5:
            t = (i - 2) / 3.0
            off = -26 + 52 * t
            for y in range(-22, 23):
                for w in range(3):
                    x = int(off + w - y * 0.55)
                    if (x / 19.0) ** 2 + (y / 24.0) ** 2 <= 1.0:
                        cv.put(CGP[0] + x, CGP[1] + y, A[27] if w == 1 else A[25])
        # 반짝 별: 왼쪽 위(0~3) · 오른쪽 아래(4~7)
        sz = [5, 10, 14, 8, 0, 5, 10, 4][i]
        if i < 4 and sz:
            cv.star4(CGP[0] - 19, CGP[1] - 25, sz, diag=sz // 3)
        elif sz:
            cv.star4(CGP[0] + 21, CGP[1] + 13, sz, diag=sz // 3)
        row.append(cv.im)
    rows.append(row)
    # struck: 맞았지만 아직 안 깨짐(잔 체력이 남은 경우) 5프레임
    row = []
    r = Rand(61)
    sp = [(r.f() * 2 * math.pi, 0.6 + 0.6 * r.f()) for _ in range(10)]
    for i in range(5):
        cv = Cv(CG, CG)
        o = [-4, -2, 0, 1, 1][i]
        _bracket(cv, CGP[0], CGP[1], 31 + o, 36 + o, 15, [X1, A[27], A[26], A[25], A[25]][i], A[17])
        if i == 0:
            cv.disc(CGP[0], CGP[1], 10, X1)
            cv.disc(CGP[0], CGP[1], 6, X0)
            cv.star4(CGP[0], CGP[1], 24, diag=8)
        if 1 <= i <= 3:
            # 잔 위 금(어두운 갈래 3)
            for (ang, ln) in ((-1.9, 18), (0.4, 15), (2.6, 13)):
                x, y = CGP[0], CGP[1]
                for j in range(ln):
                    x += math.cos(ang) + (0.5 if j % 3 == 0 else 0)
                    y += math.sin(ang)
                    cv.put(x, y, A[17]); cv.put(x + 1, y, A[25] if i == 1 else A[23])
        for (a, s) in sp:
            d = (9 + 38 * s * (i + 1) / 5.0)
            if i < 4:
                cv.spark(CGP[0] + math.cos(a) * d, CGP[1] + math.sin(a) * d, a, 4 - i // 2, A[27] if i < 2 else A[25], A[23])
        row.append(cv.im)
    rows.append(row + [row[-1]] * 3)   # 8열 맞춤(빈 칸 대신 마지막 칸 반복 — 상태 프레임은 0~4만 씀)
    meta = fx_common(
        directions=["glint", "struck"], rowsAre="kinds", layout="row = 종류(glint 루프 · struck 1회), column = 프레임",
        pivot={"x": CGP[0], "y": CGP[1]}, anchor="cup_anchor",
        anchorNote="pivot = 술통 잔 중심 → 보스 drink·phase_drink 시트 cupAnchors 사각형 가운데(x + w/2, y + h/2, 보스 시트 도트 → 보스 피벗 기준 환산). "
                   "cupAnchors 가 null 이거나 visible false 인 프레임은 숨김. 보스와 함께 flipX 하지 않는다(대칭 그림)",
        followTarget=True, depth="above",
        kinds={"glint": {"frames": [0, 1, 2, 3, 4, 5, 6, 7], "frameDurationsMs": [70] * 8, "loop": True,
                         "use": "잔을 깰 수 있는 동안(drink lift 끝 ~ gulp 루프 동안 = cupAnchors.visible) 계속 반복"},
               "struck": {"frames": [0, 1, 2, 3, 4], "frameDurationsMs": [30, 40, 50, 60, 70], "loop": False,
                          "use": "잔이 맞았지만 아직 안 깨졌을 때 1회(잔 체력이 1보다 크면). 깨지면 boss1_cup_shatter"}},
        frameDurationsMsByKind={"glint": [70] * 8, "struck": [30, 40, 50, 60, 70, 70, 70, 70]},
        glowFrames=[0], glowNote="struck 0 = 백열 섬광",
        light={"color": "#eecc78", "radius": 70, "intensity": 0.6, "flicker": {"amp": 0.25, "hz": 7}, "note": "선택 — 어두운 3국면에서도 잔이 보이게"},
        design="파훼 대상 표시: 잔 둘레 네 모서리 꺾쇠가 숨 쉬듯 벌어졌다 오므라듦 + 잔 위를 비스듬히 쓸고 가는 빛 띠 + 4점 별 반짝임(왼쪽 위 → 오른쪽 아래). "
               "struck = 꺾쇠가 안으로 조였다가(맞음) 금 3갈래 + 불티",
    )
    return "fx", "boss1_cup_glint", rows, CG, CG, meta, [70] * 8, True


# =========================================================================================== 2. 기둥 균열 3단
PW, PH = P.PW, P.PH
IMPACT = (86, 262)          # 보스 배 높이(바닥에서 약 110 도트) — 기둥 정면 몸통


GRAYS = {c[:3] for c in G}


def _on_pillar(cv, x, y):
    """돌(무채) 픽셀만 — 휘장 천·놋 잔 문양에는 금을 긋지 않는다."""
    c = cv.get(x, y)
    return c[3] == 255 and c[:3] in GRAYS


def _crack(cv, pts, w, seed):
    """폴리라인 금: 어두운 홈(G1, 굵기 w) + 빛 받는 오른쪽·아래 벽(G8) + 위·왼쪽 그늘(G3)."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            x, y = int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t))
            for k in range(w):
                if _on_pillar(cv, x + k, y):
                    cv.put(x + k, y, G[1] if (k < w - 1 or w == 1) else G[2])
            if _on_pillar(cv, x + w, y + 1) and cv.get(x + w, y + 1)[:3] not in (G[1][:3], G[2][:3]):
                cv.put(x + w, y + 1, G[9] if w > 1 else G[8])
            if w > 1 and _on_pillar(cv, x - 1, y) and cv.get(x - 1, y)[:3] not in (G[1][:3], G[2][:3]):
                cv.put(x - 1, y, G[3])


def _crater(cv, cx, cy, r):
    """충격 패인 자리: 어두운 속(G2·G1) + 아래·오른쪽 밝은 테(G9) + 위 그늘."""
    for y in range(-r - 2, r + 3):
        for x in range(-r - 2, r + 3):
            d = math.hypot(x, y * 1.25)
            if not _on_pillar(cv, cx + x, cy + y):
                continue
            if d <= r * 0.55:
                cv.put(cx + x, cy + y, G[1])
            elif d <= r:
                cv.put(cx + x, cy + y, G[2] if (x + y) < 0 else G[4])
            elif d <= r + 1.2:
                cv.put(cx + x, cy + y, G[9] if (x + y) > 0 else G[3])


def _walk(x, y, ang, ln, seed, jit=0.5, step=3):
    r = Rand(seed)
    pts = [(x, y)]
    for j in range(ln // step):
        ang += (r.f() - 0.5) * jit
        x += math.cos(ang) * step
        y += math.sin(ang) * step
        pts.append((x, y))
    return pts


def _notch(cv, poly):
    """모서리 떨어져 나간 자리: 다각형 안 기둥 픽셀을 지우고, 새 가장자리 2도트를 깨진 돌 면으로."""
    from PIL import Image, ImageDraw
    m = Image.new("L", (cv.w, cv.h), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    mp = m.load()
    gone = set()
    for y in range(cv.h):
        for x in range(cv.w):
            if mp[x, y] and cv.p[x, y][3] == 255:
                cv.p[x, y] = (0, 0, 0, 0)
                gone.add((x, y))
    for (x, y) in list(gone):
        for dx in (-2, -1, 0, 1, 2):
            for dy in (-2, -1, 0, 1, 2):
                xx, yy = x + dx, y + dy
                if (xx, yy) in gone or not (0 <= xx < cv.w and 0 <= yy < cv.h) or cv.p[xx, yy][3] != 255:
                    continue
                dd = max(abs(dx), abs(dy))
                cv.p[xx, yy] = G[8] if dd == 1 and (xx + yy) % 3 else (G[6] if dd == 1 else G[2])


# (시작점, 각, 길이, 시드, 굵기)
CRACKS = {
    1: [(IMPACT, -1.95, 56, 11, 2), (IMPACT, 1.30, 50, 12, 2), (IMPACT, 0.15, 30, 13, 2), (IMPACT, 3.0, 26, 14, 2),
        (IMPACT, -0.9, 24, 15, 1), (IMPACT, 2.3, 22, 16, 1)],
    2: [((70, 214), -2.1, 50, 21, 2), ((98, 306), 1.6, 50, 22, 2), ((106, 258), -0.5, 20, 23, 1), ((62, 266), 2.6, 26, 24, 1),
        ((100, 300), 0.5, 22, 25, 1), ((72, 280), 1.9, 34, 26, 2), ((64, 230), -2.8, 18, 27, 1)],
    3: [((62, 168), -1.7, 70, 31, 2), ((94, 352), 1.4, 16, 32, 2), ((106, 330), 0.4, 18, 34, 1),
        ((72, 300), 2.6, 26, 37, 2), ((110, 210), -1.2, 40, 38, 1)],
}
NOTCH = {
    2: [[(121, 236), (110, 244), (111, 258), (121, 268)]],
    3: [[(121, 236), (106, 242), (103, 262), (112, 280), (121, 290)], [(39, 292), (52, 298), (55, 316), (46, 326), (39, 330)],
        [(39, 196), (47, 202), (45, 214), (39, 216)]],
}
SPLIT = {"a": -1.62, "b": 1.52}


def _shift_above(cv, pts, dx, dy):
    """갈라진 선(위·아래로 이어진 pts) 오른쪽 위 조각을 (dx, dy) 밀어 어긋나게 — '곧 무너질' 기둥."""
    from PIL import Image
    ys = {}
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            ys[int(round(y0 + (y1 - y0) * t))] = int(round(x0 + (x1 - x0) * t))
    src = cv.im.copy()
    sp = src.load()
    lo, hi = min(ys), max(ys)
    for y in range(lo, hi + 1):
        if y not in ys:
            continue
        xs = ys[y]
        for x in range(cv.w - 1, xs, -1):
            c = sp[x, y]
            if c[3] == 255 and c[:3] in GRAYS:
                cv.put(x + dx, y + dy, c)
        for k in range(dx):
            if _on_pillar(cv, xs + 1 + k, y):
                cv.put(xs + 1 + k, y, G[1])


def pillar_stage(stage):
    im = P.pillar_frame(0)
    cv = Cv.wrap(im)
    _crater(cv, IMPACT[0], IMPACT[1], 4 + 2 * stage)
    for s in range(1, stage + 1):
        for (st, ang, ln, seed, w) in CRACKS[s]:
            ww = w + (1 if (stage - s) >= 1 and w > 1 else 0)
            _crack(cv, _walk(st[0], st[1], ang, ln + 10 * (stage - s), seed), ww, seed)
        for poly in NOTCH.get(s, []):
            _notch(cv, poly)
    if stage >= 3:
        # 큰 갈라짐: 충격점에서 위아래로 몸통을 가르는 깊은 틈(4도트) + 오른쪽 조각이 2도트 어긋남
        up = _walk(IMPACT[0], IMPACT[1] - 8, SPLIT["a"], 196, 41, jit=0.3, step=4)
        dn = _walk(IMPACT[0], IMPACT[1] + 8, SPLIT["b"], 100, 42, jit=0.3, step=4)
        line = list(reversed(up)) + dn
        _shift_above(cv, line, 2, 0)
        _crack(cv, line, 4, 41)
        _crater(cv, IMPACT[0], IMPACT[1], 11)
    # 바닥 돌 부스러기(기단 윗면 위)
    c = Canvas(PW, PH)
    c.paste(cv.im, 0, 0)
    piles = [(104, 372, 5, 3), (96, 378, 3, 2)]
    if stage >= 2:
        piles += [(116, 380, 6, 4), (60, 378, 4, 3)]
    if stage >= 3:
        piles += [(50, 374, 8, 5), (130, 368, 9, 5), (70, 388, 5, 3), (90, 386, 6, 4), (120, 392, 4, 3)]
    for k, (x, y, rx, ry) in enumerate(piles):
        stone_blob(c, x, y, rx, ry, R_NSTONE, seed=50 + k)
    return c.im


def _dust(cv, t, seed, big=False, origin=IMPACT):
    """충돌 먼지 뭉치(둥근 덩이) + 튀는 돌 조각 — t 0 = 터짐, 1 = 가라앉음. 불투명."""
    r = Rand(seed)
    n = 14 if big else 8
    for k in range(n):
        a = r.f() * 2 * math.pi
        d = (8 + r.f() * (44 if big else 26)) * (0.35 + 0.8 * t)
        x = origin[0] + math.cos(a) * d * 1.2
        y = origin[1] + math.sin(a) * d * 0.7 + 26 * t * t
        rad = (9 if big else 5) * (1.0 - 0.55 * t) * (0.6 + 0.6 * r.f())
        col, hi = ((PL[3], G[12]) if t < 0.3 else (PL[2], PL[3]))
        cv.disc(x, y, rad, col)
        cv.disc(x - rad * 0.3, y - rad * 0.3, max(1, rad * 0.45), hi)
    for k in range(22 if big else 10):
        a = r.f() * 2 * math.pi
        d = (10 + r.f() * (60 if big else 36)) * (0.4 + 0.8 * t)
        x = origin[0] + math.cos(a) * d
        y = origin[1] + math.sin(a) * d * 0.6 + 50 * t * t * (0.5 + r.f())
        col = [G[9], G[6], G[11], G[7]][k % 4]
        cv.put(x, y, col); cv.put(x + 1, y, col)
        if k % 3 == 0:
            cv.put(x, y + 1, G[4]); cv.put(x + 1, y + 1, G[4])


def pillar_sheet():
    frames = [P.pillar_frame(0), P.pillar_frame(1), P.pillar_frame(2)]
    states = {"idle": [0], "hit": [1, 2]}
    hold = {}
    ms = [1000, 70, 120]
    for s in (1, 2, 3):
        base = pillar_stage(s)
        # 진입: 충격(먼지 터짐 + 충격점 하얀 돌가루) → 가라앉음 → 정지
        f0 = Cv.wrap(base.copy()); _dust(f0, 0.0, 100 + s, big=True)
        for k in range(10):
            f0.put(IMPACT[0] + (k % 5) - 2, IMPACT[1] + (k // 5) - 1, G[13])
        f1 = Cv.wrap(base.copy()); _dust(f1, 0.7, 100 + s, big=True)
        i0 = len(frames)
        frames += [f0.im, f1.im, base]
        states["crack%d" % s] = [i0, i0 + 1, i0 + 2]
        states["crack%d_idle" % s] = [i0 + 2]
        hold["crack%d" % s] = i0 + 2
        ms += [60, 130, 1000]
        h0 = Cv.wrap(base.copy()); _dust(h0, 0.15, 200 + s)
        h1 = Cv.wrap(base.copy()); _dust(h1, 0.8, 200 + s)
        j0 = len(frames)
        frames += [h0.im, h1.im]
        states["crack%d_hit" % s] = [j0, j0 + 1]
        ms += [70, 120]
    return frames, states, hold, ms


def pillar():
    frames, states, hold, ms = pillar_sheet()
    meta = {
        "directions": ["any"], "frameDurationsMs": ms, "footprint": [2, 2], "solid": True,
        "pivot": {"x": P.PPIV[0], "y": P.PPIV[1]}, "occludeAbove": 112, "depth": "y", "version": "v3-r61",
        "states": states, "stateHold": hold,
        "stages": {"0": {"idle": "idle", "hit": "hit"},
                   "1": {"enter": "crack1", "idle": "crack1_idle", "hit": "crack1_hit"},
                   "2": {"enter": "crack2", "idle": "crack2_idle", "hit": "crack2_hit"},
                   "3": {"enter": "crack3", "idle": "crack3_idle", "hit": "crack3_hit"}},
        "stateNote": ("61라운드 AR-5 균열 3단. 0~2 프레임은 54라운드 그대로(idle · hit). 보스 돌진이 기둥에 부딪힐 때마다 단계 +1 → "
                      "'crack<n>'(충격 → 먼지 가라앉음 → 그 단계 정지 그림, stateHold) 1회. 그 단계에서 술통이 튕기는 등 가벼운 충돌은 'crack<n>_hit' 후 "
                      "'crack<n>_idle'. 3단 = 깊게 갈라지고 모서리가 떨어져 나간 '다음엔 무너질' 모습. 3단 다음 처리(무너짐 없음 · 3단 유지)는 시스템 판단 — "
                      "무너짐 그림이 필요하면 아트에 요청"),
        "impactPoint": {"x": IMPACT[0], "y": IMPACT[1], "note": "균열 시작점(보스 배 높이) — 시트 도트. 먼지 fx 를 더 얹을 때 참고"},
        "pivotNote": "pivot = 발자국(2×2 = 128×128 도트) 맨 아래 줄 가운데, 바닥 위 4 도트(논리 2px) — 계약 §14 bigProps 와 같은 규칙",
        "placement": "보스방 기둥 짝 2쌍(54라운드 Q11) — 대칭 배치, 엄폐·술통 튕김. 테두리 북쪽 기둥과 3칸 이상 떨어지게",
        "floor": "stage1", "palette": P.PAL_S, "source": SRC + " · 0~2 = boss1_v3/props.py pillar_frame",
        "previous": "54라운드 3프레임(idle · hit) — 0~2 프레임 픽셀 그대로",
    }
    return "structures", "boss1_pillar", [frames], PW, PH, meta, ms, False


# =========================================================================================== 3. 되칠 수 있는 술통
BW, BH, BPIV = P.BW, P.BH, P.BPIV
DIRS = ["down", "up", "left", "right"]


def barrel_body(d, i):
    """props.rolling_barrel 과 같은 그리기(접지 그림자·술 자취 제외) — 테두리 계산용 몸 실루엣."""
    cv = Canvas(BW, BH)
    if d in ("down", "up"):
        P.barrel_side(cv, BPIV[0], BPIV[1] - 34, 110, 31, (i / 8) * (1 if d == "down" else -1))
    else:
        P.barrel_end(cv, BPIV[0], BPIV[1] - 35, 33, 110, (i / 8) * (1 if d == "right" else -1))
    return cv.im


def _rings(im, n=3):
    m0 = alpha_mask(im)
    ms = [m0] + [dilate(m0, r) for r in range(1, n + 1)]
    h, w = len(m0), len(m0[0])
    out = []
    for r in range(1, n + 1):
        out.append([(x, y) for y in range(h) for x in range(w) if ms[r][y][x] and not ms[r - 1][y][x]])
    return out


def _bbox(im):
    return im.getchannel("A").point(lambda v: 255 if v == 255 else 0).getbbox()


def barrel_rim():
    """되칠 수 있음 표시 — 술통 실루엣 바깥에 흐르는 점선 테(행진하는 빛 마디) + 반짝 별. 술통 위에 같은 프레임 번호로 겹침."""
    rows = []
    for d in DIRS:
        row = []
        for i in range(8):
            body = barrel_body(d, i)
            cv = Cv(BW, BH)
            r1, r2, r3 = _rings(body, 3)
            x0, y0, x1, y1 = _bbox(body)
            cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            s1, s2 = set(r1), set(r2)
            for (x, y) in r1 + r2 + r3:
                ang = math.degrees(math.atan2((y - cy) * 1.6, x - cx))
                on = int(((ang + 360 + i * 15) % 360) // 30) % 2 == 0
                if (x, y) in s1:
                    cv.put(x, y, A[27] if on else A[21])
                elif (x, y) in s2:
                    if on:
                        cv.put(x, y, A[26])
                elif on:
                    cv.put(x, y, A[23])
            # 반짝 별(왼쪽 위 모서리 바깥, 4프레임 주기)
            sz = [4, 8, 5, 0, 0, 0, 0, 0][i % 8] if i < 4 else [0, 0, 0, 0, 3, 7, 4, 0][i]
            if sz:
                sx, sy = (x0 - 5, y0 - 3) if i < 4 else (x1 + 5, y0 + 6)
                cv.star4(sx, sy, sz, diag=sz // 3)
            row.append(cv.im)
        rows.append(row)
    meta = {
        "directions": DIRS, "layout": "rows = 굴러가는 방향(down, up, left, right), columns = 회전 프레임 — boss1_rolling_barrel 과 같은 칸",
        "frameDurationsMs": [60] * 8, "loop": True, "pivot": {"x": BPIV[0], "y": BPIV[1]}, "version": "v3-r61",
        "overlayOf": "structures/v3/boss1_rolling_barrel", "depth": "above_target",
        "drawRule": ("boss1_rolling_barrel 과 같은 프레임 번호(행·열)·같은 피벗·같은 시각으로 술통 바로 위에 겹친다(테는 실루엣 바깥에만 있어 술통을 가리지 않음). "
                     "술통이 '되칠 수 있는' 동안만 켠다 — 시스템 판단(예: 굴러오는 동안 항상 / 플레이어 사거리 안일 때만). 되친 뒤에는 끄고 boss1_rolling_barrel_returned 로 교체"),
        "anchor": "projectile_ground", "paletteSwap": "none", "drawOver": "lightmap",
        "design": "되치기 가능 표시: 술통 실루엣 바깥 2도트 테가 점선 마디(밝은 X 담황 / 어두운 호박)로 굴러가는 방향과 무관하게 한 방향으로 흐름 + 바깥 3번째 줄 성긴 호박 점 + 모서리 반짝 별",
        "palette": PAL_F, "source": SRC, "emissiveColors": EMIS,
    }
    return "structures", "boss1_rolling_barrel_rim", rows, BW, BH, meta, [60] * 8, True


HOT = {G[2][:3]: A[20], G[3][:3]: A[21], G[4][:3]: A[22], G[6][:3]: A[24], G[8][:3]: A[25]}


def barrel_returned():
    """되친 술통(보스 1.25배 술통) — 짐꾼 porter_rolling_barrel_returned 와 같은 규칙: 쇠테 호박 발광 · 바깥 테 A23 + 체커 A20 · 뒤쪽 불티."""
    src = gridsheet.open_grid(os.path.join(P.ROOT, "assets/sprites/structures/v3/boss1_rolling_barrel.json"))
    rows = []
    for j, d in enumerate(DIRS):
        row = []
        for i in range(8):
            im = src.crop((i * BW, j * BH, (i + 1) * BW, (j + 1) * BH))
            px = im.load()
            for y in range(BH):
                for x in range(BW):
                    c = px[x, y]
                    if c[3] == 255 and c[:3] in HOT:
                        px[x, y] = HOT[c[:3]]
            body = barrel_body(d, i)
            r1, r2, r3 = _rings(body, 3)
            cv = Cv.wrap(im)
            s1 = set(r1)
            for (x, y) in r1 + r2:
                cv.put(x, y, A[23] if (x, y) in s1 else A[21])
            for (x, y) in r3:
                if (x + y + i) % 2 == 0:
                    cv.put(x, y, A[20])
            r = Rand(170 + i + 8 * j)
            x0, y0, x1, y1 = _bbox(body)
            for k in range(7):
                if d == "down":
                    x, y = x0 + r.i(0, x1 - x0), y0 - 4 - r.i(0, 10)
                elif d == "up":
                    x, y = x0 + r.i(0, x1 - x0), y1 + 3 + r.i(0, 3)
                else:
                    sg = 1 if d == "right" else -1
                    x, y = (x0 - 4 - r.i(0, 12)) if sg > 0 else (x1 + 4 + r.i(0, 12)), y0 + r.i(0, y1 - y0)
                if 1 <= x < BW - 1 and 1 <= y < BH - 1 and px[x, y][3] < 255:
                    px[x, y] = [A[24], A[25], A[26], A[23]][(k + i) % 4]
            row.append(im)
        rows.append(row)
    meta = {
        "directions": DIRS, "layout": "rows = 굴러가는 방향(down, up, left, right), columns = 회전 프레임 — boss1_rolling_barrel 과 같은 칸",
        "frameDurationsMs": [60] * 8, "loop": True, "pivot": {"x": BPIV[0], "y": BPIV[1]}, "version": "v3-r61",
        "pixelScale": 0.5, "footprint": [1, 1], "solid": True, "depth": "y", "occludeAbove": 50,
        "circumferencePx": 98, "diameterPx": 34, "lengthPx": 55, "anchor": "projectile_ground",
        "returnedOf": "structures/v3/boss1_rolling_barrel",
        "swapRule": "플레이어가 쳐서 되친 순간 같은 행·열 번호로 boss1_rolling_barrel → 이 시트로 바꿔 이어 재생(짐꾼 porter_rolling_barrel_returned 와 같은 규칙). 보스·기둥·벽에 닿으면 boss1_barrel_break",
        "light": {"color": "#e2a33c", "radius": 90, "intensity": 0.6, "flicker": {"amp": 0.2, "hz": 9}, "offset": {"x": BPIV[0], "y": BPIV[1] - 34}},
        "design": "되친 술통 = 내 편: 쇠테 호박 발광 + 실루엣 바깥 호박 테 + 체커 + 진행 반대쪽 불티(짐꾼 술통 되치기와 같은 말투)",
        "floor": "stage1", "palette": P.PAL_S, "source": SRC + " · 원 그림 = boss1_rolling_barrel", "emissiveColors": EMIS,
    }
    return "structures", "boss1_rolling_barrel_returned", rows, BW, BH, meta, [60] * 8, True


# =========================================================================================== 4. 다시 켤 촛대
CW, CH, CPIV = P.CW, P.CH, P.CPIV
TIPS = [(209, 190), (209, 202), (209, 213)]      # 누운 촛대 초 끝(심지) — 시트 도트


def candelabra_fix():
    """54라운드 relight·relit 프레임의 불꽃이 초 끝에서 약 40 도트 떨어져 떠 있던 것을 고침: 0~6 그대로, 7~9 를 초 끝(TIPS)에서 다시 그림."""
    src = gridsheet.open_grid(os.path.join(P.ROOT, "assets/sprites/structures/v3/boss1_candelabra.json"))
    frames = [src.crop((i * CW, 0, (i + 1) * CW, CH)) for i in range(10)]
    base = frames[6]

    def sparks(cv, n, seed):
        r = Rand(seed)
        for k in range(n):
            x, y = TIPS[k % 3][0] + r.i(-3, 6), TIPS[k % 3][1] - r.i(1, 9)
            cv.put(x, y, [A[25], A[26], A[24]][k % 3])

    f7 = Canvas(CW, CH); f7.paste(base, 0, 0); c7 = Cv.wrap(f7.im); sparks(c7, 9, 1)
    f8 = Canvas(CW, CH); f8.paste(base, 0, 0); c8 = Cv.wrap(f8.im); sparks(c8, 6, 2); P.lying_flames(f8, [(x + 1, y) for x, y in TIPS], 0, 1.0)
    f9 = Canvas(CW, CH); f9.paste(base, 0, 0); P.lying_flames(f9, [(x + 1, y) for x, y in TIPS], 1, 1.25)
    frames[7:10] = [f7.im, f8.im, f9.im]
    m = gridsheet.load_meta(os.path.join(P.ROOT, "assets/sprites/structures/v3/boss1_candelabra.json"))
    keep = {k: v for k, v in m.items() if k not in ("image", "frameWidth", "frameHeight", "frames", "directions", "frameDurationsMs", "loop", "pixelScale", "action", "layout", "frameIndex")}
    keep["lightByState"]["relight"]["offset"] = {"x": 210, "y": 196}
    keep["lightByState"]["relit"]["offset"] = {"x": 210, "y": 194}
    keep["wickAnchors"] = {"fallen": [{"x": x, "y": y} for x, y in TIPS],
                           "note": "누운 촛대(fall 4 · fallen_unlit · relight · relit) 초 끝 심지 — 시트 도트. flipX 면 x → 256 − x"}
    keep["fix61"] = "61라운드: relight·relit(7~9) 불꽃을 초 끝 심지 위치로 옮김(54라운드 그림은 초 끝에서 약 40 도트 오른쪽에 떠 있었음). 0~6 프레임 픽셀 그대로"
    keep["relightCue"] = "fx/v3/boss1_candle_glint — fallen_unlit 동안(다시 켤 수 있음) 이 시트 위에 같은 피벗·flipX 로 겹침"
    keep["version"] = "v3-r61"
    return "structures", "boss1_candelabra", [frames], CW, CH, keep, m["frameDurationsMs"], False


def candle_glint():
    """다시 켤 수 있는 촛대 표시(fallen_unlit 동안): 심지 3개 잔불이 숨 쉬듯 붉어짐 + 위로 오르는 불티 하나 + 점선 고리(E 상호작용) + 반짝 별."""
    row = []
    glow = [0, 1, 2, 3, 3, 2, 1, 0]
    cols = [A[20], A[21], A[23], A[25]]
    for i in range(8):
        cv = Cv(CW, CH)
        # 점선 고리(누운 초 다발 둘레, 바닥 타원) — 회전
        cv.ring(205, 206, 26, 2, A[23], ky=0.6, dash=(18, 12), phase=i * 7.5)
        for k, (x, y) in enumerate(TIPS):
            g = glow[(i + k * 3) % 8]
            c = cols[g]
            cv.put(x + 1, y, c); cv.put(x + 2, y, c); cv.put(x + 1, y + 1, cols[max(0, g - 1)]); cv.put(x + 2, y + 1, cols[max(0, g - 1)])
            if g >= 2:
                cv.put(x + 1, y - 1, cols[g - 1]); cv.put(x + 2, y - 1, cols[g - 1]); cv.put(x + 1, y - 2, A[21] if g == 3 else A[20])
                cv.put(x + 3, y, cols[g - 2])
        # 오르는 불티(한 개, 루프)
        tx, ty = TIPS[1][0] + 2, TIPS[1][1] - 3 - i * 4
        cv.put(tx + (1 if i % 4 < 2 else 0), ty, A[25] if i < 5 else A[23])
        # 반짝 별
        sz = [0, 3, 6, 4, 0, 0, 0, 0][i]
        if sz:
            cv.star4(TIPS[0][0] + 6, TIPS[0][1] - 8, sz, diag=sz // 3)
        row.append(cv.im)
    meta = fx_common(
        directions=["any"], layout="1행 루프", frameDurationsMs=[90] * 8, loop=True,
        pivot={"x": CPIV[0], "y": CPIV[1]}, anchor="structure_pivot",
        anchorNote="boss1_candelabra 와 같은 틀·같은 피벗(받침 밑 가운데) — 촛대 위치에 그대로 겹치고, 촛대를 flipX 했으면 이것도 flipX",
        overlayOf="structures/v3/boss1_candelabra", useWhen="fallen_unlit(다시 켤 수 있는 동안) 반복 → relight 시작하면 끈다",
        depth="above_target", wickAnchors=[{"x": x, "y": y} for x, y in TIPS],
        light={"color": "#d67a11", "radius": 60, "intensity": 0.45, "flicker": {"amp": 0.3, "hz": 3}, "offset": {"x": 210, "y": 200},
               "note": "선택 — 3국면 소등 중 꺼진 촛대 자리를 아주 작게 보여 줌"},
        design="다시 켤 수 있음: 꺼진 심지 3개가 엇갈려 붉게 숨 쉬는 잔불 + 위로 오르는 불티 하나 + 촛대 끝 둘레 바닥 점선 고리(회전) + 반짝 별",
    )
    return "fx", "boss1_candle_glint", [row], CW, CH, meta, [90] * 8, True


# =========================================================================================== 5. 무너진 동안(파훼 경직) 표시
DZ_W, DZ_H = 128, 56
DZP = (64, 48)          # pivot = 머리 꼭대기 점(아래쪽) — 고리는 그 위


def _tiny_cup(cv, x, y, lit):
    """작은 술통 잔 아이콘 7×8 (보스 잔과 같은 모양 말투)."""
    body = [A[19], A[20], A[21]] if not lit else [A[20], A[22], A[24]]
    for yy in range(8):
        w = 3 if yy in (0, 7) else 3
        for xx in range(-w, w + 1):
            cv.put(x + xx, y + yy, body[1] if abs(xx) < w else body[0])
    for xx in range(-3, 4):
        cv.put(x + xx, y + 2, G[6]); cv.put(x + xx, y + 5, G[6])
    for xx in range(-2, 3):
        cv.put(x + xx, y, A[25] if lit else A[23])
    cv.put(x + 4, y + 2, G[5]); cv.put(x + 5, y + 3, G[5]); cv.put(x + 5, y + 4, G[5]); cv.put(x + 4, y + 5, G[5])
    cv.put(x - 1, y + 3, body[2]); cv.put(x - 1, y + 4, body[2])


def head_tops():
    """보스 drink_break·fall·hurt 시트의 프레임별 머리 꼭대기(시트 도트) — 표시 fx 앵커."""
    out = {}
    for act in ("drink_break", "fall", "hurt", "idle", "attack", "stagger_dash"):
        jp = os.path.join(P.ROOT, "assets/sprites/bosses/v3/stage1_%s.json" % act)
        m = gridsheet.load_meta(jp)
        im = gridsheet.open_grid(jp)
        fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
        res = {}
        for j, d in enumerate(m["directions"]):
            lst = []
            for i in range(n):
                f = im.crop((i * fw, j * fh, (i + 1) * fw, (j + 1) * fh))
                p = f.load()
                top = None
                for y in range(fh):
                    xs = [x for x in range(fw) if p[x, y][3] == 255]
                    if len(xs) >= 3:
                        top = y
                        break
                if top is None:
                    lst.append(None)
                    continue
                xs = [x for y in range(top, min(fh, top + 10)) for x in range(fw) if p[x, y][3] == 255]
                lst.append([round(sum(xs) / len(xs)), top])
            res[d] = lst
        out[act] = res
    return out


def break_daze():
    """파훼로 무너진 동안(받는 피해 증가 창) 머리 위: 작은 술통 잔 3개 + 별 2개가 기울어진 타원 고리를 돌고, 고리 앞쪽 반은 밝게."""
    row = []
    n = 8
    for i in range(n):
        cv = Cv(DZ_W, DZ_H)
        cx, cy = DZP[0], DZP[1] - 16
        items = []
        for k in range(5):
            a = 2 * math.pi * (k / 5.0 + i / float(n) / 5.0 * 2)
            x = cx + math.cos(a) * 42
            y = cy + math.sin(a) * 10 - math.cos(a) * 4      # 기울어진 고리(취한 느낌)
            items.append((math.sin(a), k, x, y))
        # 고리 선(뒤쪽 반 어둡게 · 점선)
        for s in range(120):
            a = 2 * math.pi * s / 120
            if s % 3 == 2:
                continue
            x = cx + math.cos(a) * 42
            y = cy + math.sin(a) * 10 - math.cos(a) * 4
            cv.put(x, y, A[23] if math.sin(a) > 0 else A[19])
        for depth, k, x, y in sorted(items):
            front = depth > 0
            if k in (0, 2, 4):
                _tiny_cup(cv, x, y - 4, front)
            else:
                cv.star4(int(x), int(y), 4 if front else 2, core=X1 if front else A[25], mid=A[26] if front else A[23],
                         edge=A[25] if front else A[21])
        row.append(cv.im)
    meta = fx_common(
        directions=["any"], layout="1행 루프", frameDurationsMs=[90] * n, loop=True,
        pivot={"x": DZP[0], "y": DZP[1]}, anchor="boss_head_top", followTarget=True, depth="above",
        anchorNote=("pivot = 보스 머리 꼭대기. 보스 시트 프레임별 머리 꼭대기 = headTopAnchors[동작][방향][프레임] (보스 시트 도트, 보스 피벗 기준 = (x − 144, y − 330))"
                    " — 없는 동작은 idle 의 같은 방향 0 프레임 값. 누운 그림(fall 6~9 down 루프)은 머리가 바닥 쪽이라 그 값 그대로 쓰면 고리가 얼굴 위에 온다"),
        headTopAnchors=head_tops(),
        useWhen="파훼로 무너진 동안(받는 피해 ×1.5 창: 잔 깨짐 drink_break stagger · 기둥 충돌 경직 · 되친 술통 경직 · fall down 루프) 반복, 끝나면 끈다",
        design="머리 위를 도는 술통 잔 3개 + 4점 별 2개, 기울어진 점선 고리(앞 반 밝게·뒤 반 어둡게) — '지금 때려라' 창",
    )
    return "fx", "boss1_break_daze", [row], DZ_W, DZ_H, meta, [90] * n, True
