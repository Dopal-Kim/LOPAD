"""술통 짐꾼이 굴려 보내는 술통 — structures/v3 (계약 §15 보스 술통과 같은 규약, 크기만 짐꾼 술통).

- porter_rolling_barrel           행 = 굴러가는 방향(down, up, left, right) × 8 회전 프레임(루프). 피벗 = 바닥 접점 가운데
- porter_rolling_barrel_returned  같은 틀·같은 회전 — 플레이어가 쳐서 되친 술통: 쇠테가 호박 발광 + 호박 테두리 + 뒤로 튀는 불티
- porter_barrel_break             벽·구조물·대상에 부딪혀 깨짐(1행 8프레임) → 마지막 프레임 뒤 fx/v3/pool_liquor 로 넘김
그림 도구: boss1_v3/props.py 의 barrel_side·barrel_end(보스 술통과 같은 그리기 — 크기만 r 15)를 import 만 한다.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../bundle2"))
sys.path.insert(0, os.path.join(HERE, "../boss1_v3"))
import b2  # noqa: E402
from b2 import Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_IRON, contact, splash  # noqa: E402
import props as bprops  # noqa: E402  (boss1_v3/props.py — 그리기 함수만 사용)
from PIL import Image, ImageChops, ImageFilter  # noqa: E402

W, H = 96, 80
PIV = (48, 72)
RB, LB = 15, 46                 # 2D 반지름(배부름 ×1.1 → 지름 약 33)·길이 — 짐꾼 리그 술통(BR 15 × 몸 배율 1.1)과 같은 화면 크기
DIRS = ["down", "up", "left", "right"]
MS = [60] * 8
CIRC_DOTS = math.pi * 2 * RB * 1.1          # 둘레(도트)
SRC = "parts/art/work/enemies61/barrel61.py (61라운드 P3 — 술통 짐꾼 투사체)"


def frame(d, i):
    cv = Canvas(W, H)
    contact(cv, PIV[0], PIV[1] - 1, 24, 4)
    if d in ("down", "up"):
        ph = (i / 8) * (1 if d == "down" else -1)
        bprops.barrel_side(cv, PIV[0], PIV[1] - 17, LB, RB, ph)
        ty = PIV[1] - 3 if d == "up" else PIV[1] - 33
        for (x, dy, col) in ((30 + (i * 5) % 18, i % 3, A[20]), (58 + (i * 3) % 10, 2, A[21]), (59 + (i * 3) % 10, 2, A[20])):
            cv.px(x, ty + dy, col)
    else:
        ph = (i / 8) * (1 if d == "right" else -1)
        bprops.barrel_end(cv, PIV[0], PIV[1] - 16, RB, LB, ph)
        sg = 1 if d == "right" else -1
        tx = 18 if d == "right" else 78
        for (x, y, col) in ((tx + ((i * 3) % 8) * sg, PIV[1] - 4, A[20]), (tx + 5 * sg, PIV[1] - 2, A[21]), (tx + 6 * sg, PIV[1] - 2, A[20])):
            cv.px(x, y, col)
    return cv.im


HOT = {G[2]: A[20], G[3]: A[21], G[4]: A[22], G[6]: A[24], G[8]: A[25]}


def returned(im, d, i):
    """되친 술통: 쇠테(R_IRON 무채)를 호박 발광으로 · 실루엣 바깥 1도트 A23 + 체커 A20 · 뒤쪽 불티 3점."""
    out = im.copy()
    px = out.load()
    for y in range(H):
        for x in range(W):
            c = px[x, y]
            if c[3] == 255 and c[:3] in {k[:3] for k in HOT}:
                k = next(k for k in HOT if k[:3] == c[:3])
                px[x, y] = HOT[k]
    a = out.getchannel("A").point(lambda v: 255 if v == 255 else 0)
    d1 = a.filter(ImageFilter.MaxFilter(3))
    d2 = a.filter(ImageFilter.MaxFilter(5))
    r1 = ImageChops.subtract(d1, a)
    r2 = ImageChops.subtract(d2, d1)
    m1, m2 = r1.load(), r2.load()
    for y in range(H):
        for x in range(W):
            if m1[x, y]:
                px[x, y] = A[23]
            elif m2[x, y] and (x + y + i) % 2 == 0:
                px[x, y] = A[20]
    # 불티(진행 반대쪽으로 흩어짐)
    r = Rand(17 + i)
    for k in range(4):
        if d == "down":
            x, y = PIV[0] - 20 + r.i(0, 40), PIV[1] - 40 - r.i(0, 8)
        elif d == "up":
            x, y = PIV[0] - 20 + r.i(0, 40), PIV[1] + 2 - r.i(0, 3)
        else:
            sg = 1 if d == "right" else -1
            x, y = PIV[0] - sg * (24 + r.i(0, 10)), PIV[1] - 6 - r.i(0, 26)
        if 0 <= x < W and 0 <= y < H and px[x, y][3] < 255:
            px[x, y] = [A[24], A[25], A[26], A[23]][(k + i) % 4]
    return out


BW, BH = 144, 112
BPIV = (72, 96)


def break_frames():
    """보스 barrel_break 와 같은 순서(첫 금 → 널 흩어짐 → 쇠테 굴러감 → 술 웅덩이), 크기 약 0.5배."""
    frames = []
    r = Rand(9)
    staves = [(r.f() * 2 * math.pi, 0.6 + 0.6 * r.f(), r.i(0, 3)) for _ in range(9)]
    K = 0.7
    n = 8
    for i in range(n):
        cv = Canvas(BW, BH)
        t = i / (n - 1)
        cx, cy = BPIV[0], BPIV[1] - 20
        if i == 0:
            contact(cv, BPIV[0], BPIV[1] - 1, 24, 4)
            bprops.barrel_side(cv, cx, cy + 3, LB - 4, RB + 1, 0.1)       # 부딪혀 납작해짐
            for k in range(8):                                              # 쪼개지는 금(밝게 번쩍)
                cv.px(cx - 14 + k * 4, cy - 12 + (k % 2) * 2 + k // 3, G[13])
                cv.px(cx - 13 + k * 4, cy - 11 + (k % 2) * 2 + k // 3, SL[0])
        else:
            pr = min(1.0, t * 1.5)
            if i <= 2:
                # 두 쪽으로 갈라져 벌어지는 통(1·2 프레임)
                tmp = Canvas(BW, BH)
                bprops.barrel_side(tmp, cx, cy + 3, LB - 4, RB + 1, 0.1)
                half_l = tmp.im.crop((0, 0, cx, BH))
                half_r = tmp.im.crop((cx, 0, BW, BH))
                off = 5 * i
                cv.im.alpha_composite(half_l.rotate(-8 * i, center=(cx, cy + 18)), (-off, -2 * i))
                cv.im.alpha_composite(half_r.rotate(8 * i, center=(0, cy + 18)), (cx + off, -2 * i))
                for k in range(6):
                    cv.px(cx - 1 + (k % 2), cy - 10 + k * 4, A[23] if k % 2 else A[22])
            splash(cv, cx, cy + 20, int((10 + 26 * pr)), int((4 + 7 * pr)), seed=3, blobs=5, glint=True)
            for (a, sp, kind) in staves:
                tt = min(t, 0.84)
                dd = (6 + 64 * sp * tt) * K
                x = cx + math.cos(a) * dd
                y = cy - 4 + math.sin(a) * dd * 0.5 - 30 * sp * tt * (1 - tt) * 2 + 22 * tt * tt
                if i <= 2:
                    continue
                ln = 12 if kind else 9
                ang = a + t * 6 * sp
                for j in range(ln):
                    px_, py_ = int(x + math.cos(ang) * (j - ln / 2)), int(y + math.sin(ang) * (j - ln / 2) * 0.6)
                    cv.px(px_, py_ - 1, R_WOOD[4]); cv.px(px_, py_, R_WOOD[3]); cv.px(px_, py_ + 1, R_WOOD[1])
                    if kind == 0 and j in (1, ln - 2):
                        cv.px(px_, py_ - 1, R_IRON[4]); cv.px(px_, py_, R_IRON[3])
            if i < n - 1:                                                   # 쇠테 고리 굴러감
                for k in range(48):
                    a = 2 * math.pi * k / 48
                    hx, hy = cx + 30 * K * t * 2 + 11 * math.cos(a), cy + 14 + 4 * math.sin(a)
                    cv.px(int(hx), int(hy), R_IRON[3] if k < 24 else R_IRON[1])
            for k in range(16 if i < 4 else 7):                             # 튀는 술 방울
                a = math.pi * (1.05 + 0.9 * (k / 16))
                dd = (5 + 30 * t * (0.5 + 0.5 * ((k * 7) % 5) / 4))
                X_, Y_ = int(cx + math.cos(a) * dd), int(cy + math.sin(a) * dd * 0.7 + 24 * t * t)
                cv.rect(X_, Y_, X_ + (1 if k % 3 else 0), Y_ + 1, [A[22], A[21], A[20]][k % 3])
        frames.append(cv.im)
    return frames


def build(prev):
    rows = [[frame(d, i) for i in range(8)] for d in DIRS]
    base_meta = {
        "directions": list(DIRS), "layout": "rows = 굴러가는 방향(down, up, left, right), columns = 회전 프레임",
        "pivot": {"x": PIV[0], "y": PIV[1]}, "version": "v3-r61", "owner": "porter",
        "footprint": [1, 1], "solid": True, "depth": "y", "occludeAbove": 24, "anchor": "projectile_ground",
        "anchorNote": "pivot = 술통 바닥 접점 가운데 = 짐꾼 attack barrelSpawnAnchors[방향][releaseFrame]. 대각선 이동은 가까운 축 방향 행",
        "rotationNote": "8프레임 = 한 바퀴. 시스템이 이동 속도/둘레(circumferencePx)로 재생 속도를 바꾼다(보스 술통과 같은 방식)",
        "circumferencePx": round(CIRC_DOTS / 2, 1), "diameterPx": round(RB * 1.1, 1), "lengthPx": round(LB / 2, 1),
        "sizeNote": "§15 보스 술통과 같은 단위(논리 px). 지름 약 33 도트 = 16.5 논리 px, 길이 46 도트 = 23 논리 px — 보스 술통(34·55)의 약 절반",
        "hitSuggestion": {"radiusTiles": 0.34, "speedTilesPerSec": 5.0, "note": "제안값 — 기준은 시스템 data"},
        "breakSheet": "structures/v3/porter_barrel_break", "floor": "stage1", "paletteSwap": False, "source": SRC,
        "emissiveColors": [],
    }
    m = dict(base_meta, role="enemy_projectile", returnedSheet="structures/v3/porter_rolling_barrel_returned",
             deflect=("플레이어 근접 공격이 닿으면 진행 방향을 뒤집고(또는 공격 방향) porter_rolling_barrel_returned 로 같은 열 번호에서 교체 — "
                      "보스 '술통 되치기' 예습. 되친 술통은 적에게만 피해"),
             usage="술통 짐꾼 굴리기 투사체 (61라운드 P3)")
    b2.write_sheet("structures", "porter_rolling_barrel", [f for r_ in rows for f in r_], W, H, m, rows=4, durations=MS, loop=True)
    rrows = [[returned(rows[j][i], d, i) for i in range(8)] for j, d in enumerate(DIRS)]
    mr = dict(base_meta, role="player_projectile", baseSheet="structures/v3/porter_rolling_barrel",
              usage="되친 술통 — 플레이어가 쳐서 돌려보낸 상태(적에게만 피해). 같은 프레임 번호·피벗",
              emissiveColors=["#e2a33c", "#e8b858", "#eecc78", "#f4de9b"],
              light={"color": "#e8b858", "radius": 70, "intensity": 0.5, "flicker": {"amp": 0.15, "hz": 6}, "offset": {"x": 48, "y": 56}},
              emissiveNote="쇠테 호박(A20~A25)·테두리 A23 은 자체 발광(조명 위 가산) — 어둠 속에서도 '내 편' 술통이 바로 읽힘",
              paletteSwap=False)
    b2.write_sheet("structures", "porter_rolling_barrel_returned", [f for r_ in rrows for f in r_], W, H, mr, rows=4, durations=MS, loop=True)
    br = break_frames()
    mb = {"directions": ["any"], "pivot": {"x": BPIV[0], "y": BPIV[1]}, "version": "v3-r61", "owner": "porter",
          "solid": False, "depth": "y", "states": {"break": list(range(8))}, "stateHold": {"break": 7},
          "usage": "굴러가던 술통이 벽·단단한 구조물·대상에 부딪혀 깨짐(되친 술통도 같은 시트)",
          "pivotNote": "pivot = 굴러가던 술통 바닥 접점과 같은 위치에 놓음", "flashFrame": 0, "shake": {"px": 2, "ms": 80},
          "handoff": "마지막 프레임 뒤 fx/v3/pool_liquor(술 웅덩이, 불이 닿으면 pool_liquor_fire)를 같은 피벗에 — 독주 행상 화염병과 엮이는 불 연계",
          "floor": "stage1", "paletteSwap": False, "source": SRC}
    b2.write_sheet("structures", "porter_barrel_break", br, BW, BH, mb, rows=1, durations=[40, 50, 60, 70, 80, 100, 120, 300])
    prev += [(rows[j][i], PIV) for j in range(4) for i in (0, 2)] + [(rrows[j][0], PIV) for j in range(4)] + [(f, BPIV) for f in br]
    return prev
