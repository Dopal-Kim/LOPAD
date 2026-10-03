"""1층 보스방(연회장) 소품 · fx v3 (54라운드 Q8·Q11 · 계약 §5·§13·§15) — python3 parts/art/work/boss1_v3/props.py

산출(모두 pixelScale 0.5, 길이 = 도트):
  assets/sprites/structures/v3/boss1_pillar          기둥(2×2 발자국, solid) · states idle / hit
  assets/sprites/structures/v3/boss1_candelabra      바닥 촛대 · states lit / fall / fallen_unlit / relight / relit
  assets/sprites/structures/v3/boss1_rolling_barrel  굴러가는 술통 · 행 = down/up/left/right(굴러가는 방향) · 8프레임 회전 루프
  assets/sprites/structures/v3/boss1_barrel_break    술통이 기둥·벽에 부딪혀 터짐(1행)
  assets/sprites/fx/v3/boss1_torch                   횃불 투사체(회전, drawnFacing right, 루프)
  assets/sprites/fx/v3/boss1_cup_shatter             술통 잔 부서짐(약점 잔이 깨질 때, cupAnchors 중심 — 54라운드 Q13 널·쇠테 조각)
  assets/sprites/fx/v3/boss1_liquor_splash           술 튀김(머리 위로 뒤집어씀·바닥 착지)
  assets/sprites/fx/v3/boss1_liquor_glob             뿌린 술 방울 투사체(회전, 루프)
도구: props_v3/pk·common·hall 을 import 만(고치지 않음). 접지 그림자(반투명)는 props_v3 와 같은 규칙(구조물만, fx 는 반투명 0).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(HERE, "..", "props_v3"))
from pk import (Canvas, Rand, G, A, SL, WD, PL, X, R_WOOD, R_IRON, R_NSTONE, R_LIQ, contact, cyl, face, grain,  # noqa: E402
                shade_mask, mask, poly_mask, ell_mask, splash, qcol, lam, clamp, outline)
import hall  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

OUT_S = os.path.join(ROOT, "assets/sprites/structures/v3")
OUT_F = os.path.join(ROOT, "assets/sprites/fx/v3")
R_GOLD = hall.R_GOLD
EMISSIVE = ["#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0", "#ffffff", "#fff4dc"]
SRC = "parts/art/work/boss1_v3/props.py (54라운드 Q8·Q11 — 1층 보스방)"
PAL_S = ("parts/art/palette/lopad.json gray + 1층 램프 16~27 + v2 재질 SL·WD·PL — 새 색 없음. 연회장 소품 v3(tiles/v3/stage1_hall_props)와 같은 재질 램프. "
         "floor: stage1(층 테마 구조물 — 1층 램프로 그림)")
PAL_F = ("v3 이펙트: 주인공 재·호박 램프(#3f271d~#f4de9b = 1층 램프 A17~A26) + 백열 X0 #ffffff / X1 #fff4dc + 술통 널(WD)·쇠테(G). "
         "paletteSwap none")


def strip(frames, rows=1):
    w, h = frames[0][0].size
    n = len(frames[0])
    im = Image.new("RGBA", (w * n, h * rows), (0, 0, 0, 0))
    for r in range(rows):
        for c, f in enumerate(frames[r]):
            im.alpha_composite(f, (c * w, r * h))
    return im


def save(path_dir, name, frames, meta, rows=1):
    os.makedirs(path_dir, exist_ok=True)
    strip(frames, rows).save(os.path.join(path_dir, name + ".png"))
    with open(os.path.join(path_dir, name + ".json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


def ncolors(frames):
    cs = set()
    for row in frames:
        for im in row:
            cs |= {c for c in im.getdata() if c[3] == 255}
    return len({c[:3] for c in cs})


def no_partial(frames):
    for row in frames:
        for im in row:
            assert not any(0 < a < 255 for a in im.getchannel("A").getdata()), "fx 반투명"


# =========================================================================================== 기둥 2×2
PW, PH = 160, 448
PPIV = (80, 440)


def pillar_frame(hit=0):
    c = Canvas(PW, PH)
    contact(c, 80, 438, 76, 8)
    # 2단 기단(발자국 2×2 = 화면 128×128): 아랫단 앞면 + 윗면, 윗단
    x0, x1 = 16, 143
    face(c, x0, 414, x1, 439, R_NSTONE, 0.45, grad=0.3)
    c.hline(x0, x1, 414, G[8]); c.hline(x0, x1, 439, G[1])
    face(c, x0, 318, x1, 413, R_NSTONE, 0.62, grad=0.18)          # 윗면(빛을 받는 넓은 판)
    for y in (350, 382):                                           # 판석 이음매
        c.hline(x0 + 2, x1 - 2, y, G[3])
    c.vline(80, 318, 413, G[3])
    c.hline(x0, x1, 318, G[9]); c.vline(x0, 318, 439, G[2]); c.vline(x1, 318, 439, G[1])
    x2, x3 = 30, 129
    face(c, x2, 380, x3, 398, R_NSTONE, 0.5, grad=0.25)
    face(c, x2, 330, x3, 379, R_NSTONE, 0.72, grad=0.15)
    c.hline(x2, x3, 330, G[10]); c.hline(x2, x3, 398, G[1]); c.vline(x3, 330, 398, G[1])
    # 몸통: 세로 홈 원기둥(반지름 40)
    cx, rx = 80, 40
    top, bot = 70, 360
    for x in range(cx - rx, cx + rx + 1):
        u = (x - cx) / rx
        nz = math.sqrt(max(0.0, 1 - u * u))
        flute = 0.09 if (x - (cx - rx)) % 9 in (0, 1) else 0.0
        yb = bot + int(10 * nz)
        for y in range(top, yb):
            s = 0.42 + 0.62 * (lam(u, 0, nz) - 0.15) - flute - 0.12 * (y - top) / (yb - top)
            c.px(x, y, qcol(R_NSTONE, s, x, y))
        c.px(x, yb, G[1])
    c.vline(cx - rx, top, bot + 2, G[2]); c.vline(cx + rx, top, bot + 2, G[1])
    # 주두(두 단)
    face(c, 34, 50, 125, 70, R_NSTONE, 0.66, grad=0.3); c.hline(34, 125, 50, G[9]); c.hline(34, 125, 70, G[1])
    face(c, 26, 26, 133, 49, R_NSTONE, 0.8, grad=0.25); c.hline(26, 133, 26, G[11]); c.hline(26, 133, 49, G[2])
    face(c, 26, 14, 133, 25, R_NSTONE, 0.92, grad=0.1); c.hline(26, 133, 14, G[12])
    # 잔 문양 휘장(호박 비단 + 놋 잔)
    m = poly_mask(56, 150, [(0, 0), (55, 0), (55, 124), (28, 148), (0, 124)])
    shade_mask(c, m, [SL[0], A[16], A[17], A[18], WD[4]], ox=52, oy=86, base=0.45, gain=0.5, soft=3)
    for y in range(108, 136):
        t = (y - 108) / 28
        half = int(13 * (1 - t) ** 0.6)
        c.hline(80 - half, 80 + half, y, R_GOLD[3] if y > 110 else R_GOLD[4])
        c.px(80 - half, y, R_GOLD[4])
    c.vline(80, 136, 150, R_GOLD[3]); c.vline(81, 136, 150, R_GOLD[1]); c.hline(70, 90, 151, R_GOLD[3]); c.hline(70, 90, 152, R_GOLD[1])
    c.hline(54, 106, 92, R_GOLD[2]); c.hline(54, 106, 93, R_GOLD[4])
    # 금(얕은 금 + 이미 부딪힌 자국)
    r = Rand(7)
    for k in range(3):
        x, y = 60 + k * 18, 220 + k * 30
        for j in range(14):
            c.px(x, y, G[1])
            x += r.i(-1, 1)
            y += 1
    if hit:
        # 돌진 충돌: 새 금 + 돌가루(불투명 점) + 모서리 빛
        x, y = 104, 250
        for j in range(40):
            c.px(x, y, SL[0]); c.px(x + 1, y, G[6])
            x += [-1, 0, 1, 0][j % 4] - (1 if j % 7 == 0 else 0)
            y += 1
        for k in range(26 if hit == 1 else 14):
            a = r.f() * math.pi * 2
            d = (10 + r.f() * 28) * (1.0 if hit == 1 else 1.6)
            px, py = int(104 + math.cos(a) * d), int(270 + math.sin(a) * d * 0.7 + (0 if hit == 1 else 10))
            col = [G[8], G[6], G[10], PL[2]][k % 4]
            c.rect(px, py, px + (1 if k % 3 else 2), py + 1, col)
        if hit == 1:
            c.vline(cx - rx + 1, top, bot, G[10])
    return c.im


def pillar():
    frames = [[pillar_frame(0), pillar_frame(1), pillar_frame(2)]]
    meta = {
        "image": "boss1_pillar.png", "frameWidth": PW, "frameHeight": PH, "frames": 3, "directions": ["any"],
        "frameDurationsMs": [1000, 70, 120], "footprint": [2, 2], "solid": True, "pivot": {"x": PPIV[0], "y": PPIV[1]},
        "occludeAbove": 112, "depth": "y", "pixelScale": 0.5, "version": "v3",
        "states": {"idle": [0], "hit": [1, 2]},
        "stateNote": "hit = 돌진 충돌(보스 경직)·술통 튕김 순간 1회 재생 후 idle. 금은 그림에만(내구도 없음)",
        "pivotNote": "pivot = 발자국(2×2 = 128×128 도트) 맨 아래 줄 가운데, 바닥 위 4 도트(논리 2px) — 계약 §14 bigProps 와 같은 규칙",
        "placement": "보스방 기둥 짝 2쌍(54라운드 Q11) — 대칭 배치, 엄폐·술통 튕김. 테두리 북쪽 기둥과 3칸 이상 떨어지게",
        "floor": "stage1", "palette": PAL_S, "source": SRC,
        "colors": ncolors(frames),
    }
    save(OUT_S, "boss1_pillar", frames, meta)
    return frames


# =========================================================================================== 촛대
CW, CH = 256, 224
CPIV = (64, 216)


def candelabra_upright(lit=True, smoke=0):
    c = Canvas(96, 208)
    for (dx, col) in ((-14, R_GOLD[3]), (14, R_GOLD[1]), (-6, R_GOLD[2])):
        for k in range(3):
            c.line(48 + dx, 202 - k, 48, 186 - k, col)
    hall.candelabra_c(c, 48, 190, h=130, arms=2, big=True)
    im = c.im
    if not lit:
        px = im.load()
        flames = {tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in EMISSIVE}
        for y in range(im.height):
            for x in range(im.width):
                p = px[x, y]
                if p[3] and p[:3] in flames:
                    px[x, y] = (0, 0, 0, 0)
    return im


def candle_flames(im, lit_cols=True):
    """회전된 촛대 위에 촛불(불꽃은 항상 위로) — 심지 위치(초 꼭대기 PL4 가장 위 점) 찾기 대신 지정 점 사용."""
    return im


def rot_place(src, deg, cx_src, cy_src, dst, at):
    """src 를 (cx_src, cy_src) 기준 deg(반시계 +) 회전해 dst 의 at 에 그 점이 오도록 붙임(최근접)."""
    big = Image.new("RGBA", (src.width * 3, src.height * 3), (0, 0, 0, 0))
    big.alpha_composite(src, (src.width, src.height))
    piv = (src.width + cx_src, src.height + cy_src)
    r = big.rotate(deg, resample=Image.NEAREST, center=piv)
    dst.alpha_composite(r, (int(at[0] - piv[0]), int(at[1] - piv[1])))


def wisp(c, x, y, k, seed):
    r = Rand(seed)
    for j in range(8 + 3 * k):
        yy = y - j * 2
        xx = x + int(2.5 * math.sin(j * 0.7 + seed))
        c.px(xx, yy, [G[7], G[6], G[5], G[4]][min(3, j // 4)])
        if j % 3 == 0:
            c.px(xx + 1, yy, G[5])


def lying_flames(c, pts, phase=0, size=1.0):
    for i, (x, y) in enumerate(pts):
        h = int((7 + (i + phase) % 3) * size)
        for dy in range(h):
            t = dy / max(1, h)
            w = max(0, int(round(2.2 * size * (1 - t) * (1 if t > 0.15 else 0.8))))
            for dx in range(-w, w + 1):
                col = A[27] if (abs(dx) == 0 and t < 0.5) else (A[25] if abs(dx) <= w - 1 else A[23])
                c.px(x + dx, y - dy, col)


def candelabra():
    up_lit = candelabra_upright(True)
    up_out = candelabra_upright(False)
    # 받침 밑 가운데 = (48, 202) → 시트 (64, 216). 넘어지는 방향 = 동쪽(오른쪽). 서쪽은 시스템이 flipX
    frames = []
    tips_lying = [(64 + k, 216 - 10) for k in ()]

    def frame(deg, src, extra=None):
        cv = Canvas(CW, CH)
        contact(cv, 64 + int(deg * 0.9), 214, 24 + int(deg * 0.9), 5)
        rot_place(src, -deg, 48, 202, cv.im, (64, 216 - (6 if 0 < deg < 90 else 0)))
        if extra:
            extra(cv)
        return cv.im
    # 0 lit
    frames.append(frame(0, up_lit))
    # 1~4 fall (불꽃 꺼지며 연기)
    frames.append(frame(18, up_lit))
    frames.append(frame(48, up_out, lambda cv: wisp(cv, 64 + 96, 216 - 150, 1, 3)))
    frames.append(frame(82, up_out, lambda cv: [wisp(cv, 64 + 168, 216 - 50, 1, 4), wisp(cv, 64 + 150, 216 - 70, 1, 5)]))
    frames.append(frame(90, up_out, lambda cv: [wisp(cv, 64 + 176, 216 - 30, 2, 6), wisp(cv, 64 + 160, 216 - 48, 2, 7),
                                                 splash_dust(cv, 150, 214)]))
    # 5 fallen_unlit(연기 남음) · 6 fallen_unlit(정지)
    frames.append(frame(90, up_out, lambda cv: [wisp(cv, 64 + 178, 216 - 36, 1, 8), wisp(cv, 64 + 162, 216 - 52, 1, 9)]))
    frames.append(frame(90, up_out))
    # 초 끝 위치(누운 촛대): 90° 회전 → (x, y) 는 받침에서 오른쪽으로. 큰 초 3개 끝 근사
    lt = [(64 + 170, 216 - 2), (64 + 160, 216 - 16), (64 + 158, 216 + 12 - 26)]
    # 7·8 relight(불티 → 붙음) · 9 relit
    def sparks(cv, n, seed):
        r = Rand(seed)
        for k in range(n):
            x, y = lt[k % 3][0] + r.i(-6, 6), lt[k % 3][1] - r.i(0, 10)
            cv.px(x, y, [A[25], A[26], A[24]][k % 3])
    frames.append(frame(90, up_out, lambda cv: sparks(cv, 9, 1)))
    frames.append(frame(90, up_out, lambda cv: [sparks(cv, 6, 2), lying_flames(cv, lt, 0, 1.0)]))
    frames.append(frame(90, up_out, lambda cv: lying_flames(cv, lt, 1, 1.7)))
    fr = [frames]
    LIT = {"color": "#f4de9b", "radius": 280, "intensity": 0.9, "flicker": {"amp": 0.1, "hz": 6}, "offset": {"x": 64, "y": 66}}
    meta = {
        "image": "boss1_candelabra.png", "frameWidth": CW, "frameHeight": CH, "frames": len(frames), "directions": ["any"],
        "frameDurationsMs": [1000, 70, 70, 70, 90, 300, 1000, 80, 80, 1000], "footprint": [1, 1],
        "solid": True, "solidByState": {"lit": True, "fall": True, "fallen_unlit": False, "relight": False, "relit": False},
        "pivot": {"x": CPIV[0], "y": CPIV[1]}, "occludeAbove": 60, "depth": "y", "pixelScale": 0.5, "version": "v3",
        "states": {"lit": [0], "fall": [1, 2, 3, 4], "fallen_unlit": [5, 6], "relight": [7, 8], "relit": [9]},
        "stateHold": {"fallen_unlit": 6, "relit": 9},
        "lightByState": {
            "lit": LIT,
            "fall": None, "fallen_unlit": None,
            "relight": {"color": "#e8b858", "radius": 120, "intensity": 0.5, "flicker": {"amp": 0.3, "hz": 10}, "offset": {"x": 224, "y": 206}},
            "relit": {"color": "#f4de9b", "radius": 240, "intensity": 0.85, "flicker": {"amp": 0.12, "hz": 6}, "offset": {"x": 224, "y": 204}},
        },
        "light": LIT,
        "stateNote": ("54라운드 Q8 등불 끄기: lit(서 있음, 광원) → fall(동쪽으로 쓰러지며 촛불이 꺼지고 연기) → fallen_unlit(통과, 광원 없음, 6 유지) "
                      "→ 치거나 E 로 relight(불티 → 불 붙음) → relit(누운 채 다시 켜짐, 광원 — 12초 뒤 시스템이 lit 로 복구할 때는 그냥 0 프레임). "
                      "서쪽으로 쓰러지게 하려면 flipX(피벗 x 는 그대로 64 → 시트 폭 256 기준 거울 위치 192)."),
        "anchorNote": "pivot = 받침 밑 가운데(서 있을 때 발자국 1칸 가운데 아래). 누우면 그림이 오른쪽으로 약 3칸 뻗는다(통과)",
        "floor": "stage1", "palette": PAL_S, "source": SRC, "colors": ncolors(fr),
    }
    save(OUT_S, "boss1_candelabra", fr, meta)
    return fr


def splash_dust(cv, x, y):
    r = Rand(31)
    for k in range(16):
        a = math.pi * (0.1 + 0.8 * r.f())
        d = 6 + r.f() * 22
        cv.rect(int(x + math.cos(a) * d * (1 if k % 2 else -1)), int(y - math.sin(a) * d * 0.4), int(x + math.cos(a) * d * (1 if k % 2 else -1)) + 1,
                int(y - math.sin(a) * d * 0.4), [PL[2], PL[1], G[6]][k % 3])


# =========================================================================================== 굴러가는 술통
BW, BH = 128, 112
BPIV = (64, 104)


def barrel_side(cv, cx, cy, length, r_, phase):
    """가로로 누운 술통(축 = 화면 좌우) — 아래·위로 굴러감. phase(0~1) = 회전 각/2π."""
    x0 = cx - length // 2
    for x in range(x0, x0 + length + 1):
        t = (x - x0) / length
        rr = r_ * (1 + 0.1 * math.sin(math.pi * t))
        for y in range(int(cy - rr), int(cy + rr) + 1):
            v = (y + 0.5 - cy) / rr
            if abs(v) > 1:
                continue
            nz = math.sqrt(max(0, 1 - v * v))
            s = 0.42 + 0.62 * (lam(0.0, v, nz) - 0.15)
            cv.px(x, y, qcol(R_WOOD, s, x, y))
    # 널 틈 — 회전에 따라 위아래로 흐름(앞쪽 반원만)
    for k in range(8):
        th = 2 * math.pi * (k / 8 + phase)
        if math.cos(th) <= 0.05:
            continue
        v = math.sin(th)
        for x in range(x0 + 2, x0 + length - 1):
            t = (x - x0) / length
            y = int(round(cy + v * r_ * (1 + 0.1 * math.sin(math.pi * t))))
            cur = cv.get(x, y)
            if cur in R_WOOD:
                cv.px(x, y, R_WOOD[max(0, R_WOOD.index(cur) - 2)])
    # 마개 구멍 — 앞을 지날 때만
    thb = 2 * math.pi * (0.3 + phase)
    if math.cos(thb) > 0.2:
        y = int(round(cy + math.sin(thb) * r_))
        cv.rect(cx + 6, y - 2, cx + 11, y + 1, WD[0]); cv.hline(cx + 6, cx + 11, y - 2, WD[3])
        # 새는 술(마개에서)
        cv.px(cx + 8, y + 2, A[21]); cv.px(cx + 8, y + 3, A[20])
    # 쇠테(세로)
    for hx_ in (x0 + 8, x0 + length // 2 - 12, x0 + length // 2 + 12, x0 + length - 8):
        t = (hx_ - x0) / length
        rr = r_ * (1 + 0.1 * math.sin(math.pi * t))
        for y in range(int(cy - rr), int(cy + rr) + 1):
            v = (y - cy) / rr
            s = 0.5 + 0.5 * (lam(0, v, math.sqrt(max(0, 1 - v * v))) - 0.2)
            cv.px(hx_, y, qcol(R_IRON, s, hx_, y)); cv.px(hx_ + 1, y, qcol(R_IRON, s - 0.15, hx_ + 1, y))
    # 양 끝 뚜껑 가장자리(어둡게)
    for ex, col in ((x0, WD[1]), (x0 + length, WD[0])):
        for y in range(int(cy - r_), int(cy + r_) + 1):
            cv.px(ex, y, col)
    outline(cv, mask_of(cv), R_WOOD, dark=SL[0])


def mask_of(cv):
    a = cv.im.getchannel("A").point(lambda v: 255 if v == 255 else 0)
    return a


def barrel_end(cv, cx, cy, r_, length, phase):
    """축이 화면 위아래(남북)인 술통 — 좌우로 굴러감: 남쪽 뚜껑(세운 원판)이 보이고 몸통은 위로 짧게."""
    body = int(length * 0.42)
    # 몸통(뚜껑 위로 보이는 윗면 쪽) — 가로 원통의 윗부분을 위로 끌어올린 띠
    for x in range(cx - r_ - 2, cx + r_ + 3):
        u = (x - cx) / (r_ + 2)
        if abs(u) > 1:
            continue
        nz = math.sqrt(max(0, 1 - u * u))
        ytop = int(cy - (r_ + 2) * nz * 0.98) - body
        for y in range(ytop, int(cy)):
            s = 0.4 + 0.6 * (lam(u, -0.6, nz) - 0.1)
            cv.px(x, y, qcol(R_WOOD, s, x, y))
    # 몸통 널(회전 방향으로 가로 이동) + 쇠테
    for k in range(8):
        th = 2 * math.pi * (k / 8 + phase)
        if math.cos(th) <= 0.0:
            continue
        x = int(round(cx + math.sin(th) * (r_ + 2)))
        for y in range(int(cy - body - (r_ + 2) * math.cos(th) * 0.98), int(cy - r_ * 0.6)):
            cur = cv.get(x, y)
            if cur in R_WOOD:
                cv.px(x, y, R_WOOD[max(0, R_WOOD.index(cur) - 2)])
    for yy in (int(cy - body * 0.35 - r_ * 0.7), int(cy - body * 0.8 - r_ * 0.8)):
        for x in range(cx - r_ - 2, cx + r_ + 3):
            cur = cv.get(x, yy)
            if cur[3]:
                cv.px(x, yy, R_IRON[3]); cv.px(x, yy + 1, R_IRON[1])
    # 남쪽 뚜껑(원판)
    for y in range(cy - r_, cy + r_ + 1):
        for x in range(cx - r_, cx + r_ + 1):
            d = ((x - cx) ** 2 + (y - cy) ** 2) / (r_ * r_)
            if d <= 1.0:
                s = 0.62 - 0.25 * d + 0.12 * (-(x - cx) - (y - cy)) / r_
                cv.px(x, y, qcol(R_WOOD, s, x, y))
    # 뚜껑 판자 선(회전)
    ang = 2 * math.pi * phase
    for off in (-0.36, 0.0, 0.36):
        for t in range(-r_, r_ + 1):
            ca, sa = math.cos(ang), math.sin(ang)
            x = cx + t * ca - off * r_ * sa
            y = cy + t * sa + off * r_ * ca
            if (x - cx) ** 2 + (y - cy) ** 2 < (r_ - 3) ** 2:
                cv.px(int(round(x)), int(round(y)), WD[1])
    # 마개(회전)
    bx, by = cx + 0.55 * r_ * math.cos(ang + 1.0), cy + 0.55 * r_ * math.sin(ang + 1.0)
    cv.rect(int(bx) - 2, int(by) - 2, int(bx) + 2, int(by) + 2, WD[0]); cv.px(int(bx) - 2, int(by) - 2, WD[3])
    # 쇠테(뚜껑 둘레)
    for k in range(120):
        a = 2 * math.pi * k / 120
        x, y = cx + (r_ + 0.5) * math.cos(a), cy + (r_ + 0.5) * math.sin(a)
        cv.px(int(round(x)), int(round(y)), R_IRON[4] if (math.cos(a) < 0 and math.sin(a) < 0.3) else R_IRON[2])
    outline(cv, mask_of(cv), R_WOOD, dark=SL[0])


def drip_trail(cv, pts):
    for (x, y, col) in pts:
        cv.px(x, y, col)


def rolling_barrel():
    rows = []
    for d in ("down", "up", "left", "right"):
        row = []
        for i in range(8):
            cv = Canvas(BW, BH)
            contact(cv, 64, 102, 44, 6)
            if d in ("down", "up"):
                ph = (i / 8) * (1 if d == "down" else -1)
                barrel_side(cv, 64, 78, 88, 25, ph)
                # 술 방울 자취(굴러온 쪽 = 반대 방향)
                ty = 100 if d == "up" else 54
                drip_trail(cv, [(40 + (i * 7) % 40, ty + (i % 3), A[20]), (70 + (i * 5) % 20, ty + 3, A[21])])
            else:
                ph = (i / 8) * (1 if d == "right" else -1)
                barrel_end(cv, 64, 76, 26, 88, ph)
                tx = 20 if d == "right" else 104
                drip_trail(cv, [(tx + ((i * 3) % 6) * (1 if d == "right" else -1), 98, A[20]), (tx + 4, 100, A[21])])
            row.append(cv.im)
        rows.append(row)
    meta = {
        "image": "boss1_rolling_barrel.png", "frameWidth": BW, "frameHeight": BH, "frames": 8,
        "directions": ["down", "up", "left", "right"], "layout": "rows = 굴러가는 방향(down, up, left, right), columns = 회전 프레임",
        "frameDurationsMs": [60] * 8, "loop": True, "pivot": {"x": BPIV[0], "y": BPIV[1]}, "pixelScale": 0.5, "version": "v3",
        "footprint": [1, 1], "solid": True, "depth": "y", "occludeAbove": 40,
        "rotationNote": ("8프레임 = 한 바퀴. 이동 속도에 맞추려면 한 바퀴 = 둘레 약 157 도트(78 논리 px) → 프레임당 약 10 논리 px 이동일 때 60ms. "
                         "시스템이 속도/둘레로 재생 속도를 바꿔도 됨(stride 와 같은 방식: circumferencePx)"),
        "circumferencePx": 78, "anchor": "projectile_ground",
        "anchorNote": "pivot = 술통 바닥 접점 가운데. 대각선 이동은 가까운 축 방향 행을 쓴다. 기둥·벽에 닿으면 boss1_barrel_break 재생",
        "floor": "stage1", "palette": PAL_S, "source": SRC, "colors": ncolors(rows),
    }
    save(OUT_S, "boss1_rolling_barrel", rows, meta, rows=4)
    return rows


def barrel_break():
    frames = []
    r = Rand(5)
    staves = [(r.f() * 2 * math.pi, 0.6 + 0.6 * r.f(), r.i(0, 3)) for _ in range(12)]
    for i in range(7):
        cv = Canvas(160, 128)
        t = i / 6
        cx, cy = 80, 84
        if i == 0:
            barrel_side(cv, cx, cy - 6, 84, 25, 0.1)
            for k in range(10):
                cv.px(cx - 30 + k * 6, cy - 32 - (k % 2), G[12])
        else:
            # 술 터짐(바닥 웅덩이로)
            splash(cv, cx, cy + 22, int(20 + 40 * min(1, t * 1.6)), int(6 + 9 * min(1, t * 1.6)), seed=3, blobs=6, glint=True)
            # 날아가는 널
            for (a, sp, kind) in staves:
                d = 10 + 70 * sp * t
                x = cx + math.cos(a) * d
                y = cy - 10 + math.sin(a) * d * 0.5 - 40 * sp * t * (1 - t) * 2 + 28 * t * t
                ln = 12 if kind else 9
                ang = a + t * 6 * sp
                for j in range(ln):
                    px, py = int(x + math.cos(ang) * (j - ln / 2)), int(y + math.sin(ang) * (j - ln / 2) * 0.6)
                    cv.px(px, py, R_WOOD[3]); cv.px(px, py + 1, R_WOOD[1])
                    if kind == 0 and j in (2, ln - 3):
                        cv.px(px, py, R_IRON[3])
            # 쇠테 고리(굴러감)
            if i < 6:
                for k in range(40):
                    a = 2 * math.pi * k / 40
                    cv.px(int(cx + 26 * t * 2 + 16 * math.cos(a)), int(cy + 18 + 6 * math.sin(a)), R_IRON[3] if k < 20 else R_IRON[1])
            # 튀는 술 방울
            for k in range(18 if i < 4 else 8):
                a = math.pi * (1.05 + 0.9 * (k / 18))
                d = 8 + 44 * t * (0.5 + 0.5 * ((k * 7) % 5) / 4)
                cv.rect(int(cx + math.cos(a) * d), int(cy + math.sin(a) * d * 0.7 + 30 * t * t),
                        int(cx + math.cos(a) * d) + (1 if k % 3 else 0), int(cy + math.sin(a) * d * 0.7 + 30 * t * t) + 1,
                        [A[22], A[21], A[20]][k % 3])
        frames.append(cv.im)
    meta = {
        "image": "boss1_barrel_break.png", "frameWidth": 160, "frameHeight": 128, "frames": 7, "directions": ["any"],
        "frameDurationsMs": [40, 50, 60, 70, 90, 110, 400], "loop": False, "pivot": {"x": 80, "y": 112}, "pixelScale": 0.5,
        "version": "v3", "solid": False, "depth": "y", "states": {"break": [0, 1, 2, 3, 4, 5, 6]}, "stateHold": {"break": 6},
        "note": "굴러가던 술통이 기둥·벽·주인공에 부딪혀 터짐 → 술 웅덩이(마지막 프레임 유지 후 시스템이 fire_pool 등 웅덩이로 교체 가능)",
        "floor": "stage1", "palette": PAL_S, "source": SRC, "colors": ncolors([frames]),
    }
    save(OUT_S, "boss1_barrel_break", [frames], meta)
    return [frames]


# =========================================================================================== fx
def fx_meta(name, fw, fh, n, ms, pivot, anchor, spawn, loop, note, extra=None, frames=None):
    j = {"image": name + ".png", "action": name, "frameWidth": fw, "frameHeight": fh, "frames": n, "directions": ["any"],
         "layout": "1행", "frameIndex": "column", "fps": round(1000.0 * n / sum(ms), 2), "frameDurationsMs": ms, "loop": loop,
         "pivot": {"x": pivot[0], "y": pivot[1]}, "anchor": anchor, "spawn": spawn, "version": "v3", "pixelScale": 0.5,
         "paletteSwap": "none", "paletteSwapNote": "53라운드 Q62·Q68 — fx 는 지역 바닥 팔레트 교체 제외", "palette": PAL_F,
         "drawOver": "lightmap", "drawOverNote": "53라운드 Q63 — fx 는 조명 위에 그린다", "source": SRC, "note": note}
    if frames is not None:
        j["colors"] = ncolors(frames)
    if extra:
        j.update(extra)
    return j


def torch_fx():
    frames = []
    for i in range(4):
        cv = Canvas(96, 48)
        cx, cy = 58, 24
        # 자루(오른쪽으로 날아감: 불 머리가 오른쪽, 자루는 왼쪽) — 회전하며 날아가는 대신 약간 흔들림
        wob = [0, 1, 0, -1][i]
        for k in range(-22, 4):
            y = cy + int(k * 0.08 * wob)
            cv.px(cx + k, y, WD[3]); cv.px(cx + k, y + 1, WD[2]); cv.px(cx + k, y + 2, WD[1])
        cv.rect(cx + 2, cy - 3, cx + 9, cy + 4, WD[1]); cv.hline(cx + 2, cx + 9, cy - 3, A[18])
        # 불꽃: 머리에서 뒤(왼쪽)로 끌리는 꼬리 + 위로 날림
        r = Rand(10 + i)
        for k in range(42):
            t = k / 42
            x = cx + 8 - int(t * 44)
            w = (7.5 * (1 - t) ** 0.8) + 1.5 * math.sin(t * 9 + i * 1.6)
            yc = cy - 1 - int(t * 6) + int(2 * math.sin(t * 7 + i))
            for dy in range(-int(w), int(w) + 1):
                rr = abs(dy) / max(1.0, w)
                col = X[0] if (rr < 0.3 and t < 0.25) else (A[26] if rr < 0.5 and t < 0.45 else (A[24] if rr < 0.75 else A[22]))
                if t > 0.7:
                    col = A[21] if rr < 0.6 else A[20]
                cv.px(x, yc + dy, col)
        for k in range(6):
            cv.px(cx - 20 - r.i(0, 18), cy - 8 - r.i(0, 8), [A[25], A[23], A[21]][k % 3])
        frames.append(cv.im)
    fr = [frames]
    no_partial(fr)
    meta = fx_meta("boss1_torch", 96, 48, 4, [60, 60, 60, 60], (62, 24), "projectile", "boss_throw_torch_release", True,
                   "횃불 투사체(54라운드 '불붙은 술' — 웅덩이 점화). 불 머리 = 진행 방향(drawnFacing right), 꼬리 불꽃이 뒤로 끌림",
                   {"rotate": True, "drawnFacing": "right", "light": {"color": "#e8b858", "radius": 160, "intensity": 0.8,
                                                                       "flicker": {"amp": 0.25, "hz": 9}, "offset": {"x": 62, "y": 22}},
                    "emissiveColors": EMISSIVE, "spawnNote": "보스 stage1_throw_torch releaseFrame 의 handAnchors 점에서 생성. 착지하면 fx/fire_pool(웅덩이 점화)"},
                   fr)
    save(OUT_F, "boss1_torch", fr, meta)
    return fr


def cup_shatter():
    """술통 잔이 부서짐(54라운드 Q13): 0 = 백열 섬광 + 통에 금(판정 프레임) → 널 조각이 회전하며 솟았다 떨어짐 ·
    쇠테 2개가 기울어 벌어지며 떨어짐 · 나뭇조각 · 술 덩어리. 보스 192×240 시트의 술통 잔(약 29×27 도트)에 맞춘 크기."""
    frames = []
    r = Rand(3)
    staves = [((k + r.f() * 0.5) * 2 * math.pi / 10, 0.55 + 0.6 * r.f(), 9 + r.i(0, 5), r.f() * 3.0, k % 3 == 0) for k in range(10)]
    chips = [(r.f() * 2 * math.pi, 0.4 + r.f() * 0.8) for _ in range(14)]
    drops = [(math.pi * (1.0 + r.f()), 0.4 + r.f() * 0.8) for _ in range(24)]
    W_ = [R_WOOD[1], R_WOOD[3], R_WOOD[4]]
    for i in range(8):
        cv = Canvas(128, 128)
        cx, cy = 64, 60
        t = i / 7
        if i == 0:
            # 통 윤곽 위로 금이 번쩍 — 백열 섬광 십자 + 널 사이 갈라짐
            for y in range(-13, 14):
                for x in range(-14, 15):
                    if (x / 14.5) ** 2 + (y / 13.5) ** 2 <= 1 and ((x / 14.5) ** 2 + (y / 13.5) ** 2 > 0.82):
                        cv.px(cx + x, cy + y, R_WOOD[1])
            for k in range(-18, 19):
                cv.px(cx + k, cy, X[0] if abs(k) < 6 else A[26])
                cv.px(cx, cy + k, X[0] if abs(k) < 6 else A[26])
            for k in range(-9, 10):
                cv.px(cx + k, cy + k, A[25]); cv.px(cx + k, cy - k, A[25])
            for x0 in (-9, -4, 5, 10):
                for y in range(-11, 12, 2):
                    cv.px(cx + x0 + (y // 5) % 2, cy + y, A[24])
        else:
            # 술 덩어리 터짐(위로 솟았다 떨어짐)
            for (a, sp) in drops:
                d = 6 + 48 * sp * min(1.0, t * 1.4)
                x = cx + math.cos(a) * d
                y = cy + math.sin(a) * d * 0.9 + 70 * t * t
                sz = 2 if sp > 0.8 and t < 0.6 else 1
                col = A[24] if t < 0.3 else (A[22] if t < 0.6 else A[20])
                cv.rect(int(x), int(y), int(x) + sz, int(y) + sz, col)
            if i < 3:
                rad = int(12 + 14 * t)
                for k in range(80):
                    a = 2 * math.pi * k / 80
                    cv.px(int(cx + rad * math.cos(a)), int(cy + rad * 0.8 * math.sin(a)), A[23] if i < 2 else A[21])
            # 쇠테 2개(기울어 벌어지며 떨어짐, 한쪽 끊김)
            for j, (ox, rot0, sq) in enumerate(((-6, 0.4, 0.4), (7, -0.6, 0.5))):
                if i >= 6 and j == 1:
                    continue
                hx, hy = cx + ox * (1 + 2 * t), cy + (-4 + 10 * j) * t + 52 * t * t
                rr = 15 + 5 * t
                rot_ = rot0 + (1.2 if j else -1.0) * t
                cr, sr = math.cos(rot_), math.sin(rot_)
                for k in range(120):
                    a = 2 * math.pi * k / 120
                    if (0.15 + 0.45 * j) <= k / 120 < (0.27 + 0.45 * j):
                        continue
                    ex, ey = math.cos(a) * rr, math.sin(a) * rr * sq
                    cv.px(int(round(hx + ex * cr - ey * sr)), int(round(hy + ex * sr + ey * cr)), R_IRON[5] if math.sin(a) > 0 else R_IRON[3])
            # 널 조각: 3도트 폭 휜 판(밝은 면·본색·그늘), 일부는 쇠테 조각이 붙음
            for (a, sp, ln, spin, iron) in staves:
                d = 8 + 46 * sp * t
                x = cx + math.cos(a) * d
                y = cy + math.sin(a) * d * 0.75 - 30 * sp * t * (1 - t) * 2 + 48 * t * t
                ang = a + math.pi / 2 + t * (4 + spin)
                ca, sa = math.cos(ang), math.sin(ang)
                for jj in range(ln):
                    u = jj - ln / 2
                    bend = 0.05 * u * u
                    X_, Y_ = x + ca * u - sa * bend, y + sa * u + ca * bend
                    end = jj in (0, ln - 1)
                    cv.px(int(round(X_ + sa)), int(round(Y_ - ca)), R_WOOD[2] if end else R_WOOD[4])
                    cv.px(int(round(X_)), int(round(Y_)), R_WOOD[2] if end else R_WOOD[3])
                    cv.px(int(round(X_ - sa)), int(round(Y_ + ca)), R_WOOD[0] if end else R_WOOD[1])
                if iron:
                    for jj in (ln // 3, ln // 3 + 1):
                        u = jj - ln / 2
                        X_, Y_ = x + ca * u, y + sa * u
                        cv.px(int(round(X_ + sa)), int(round(Y_ - ca)), R_IRON[5])
                        cv.px(int(round(X_)), int(round(Y_)), R_IRON[4])
                        cv.px(int(round(X_ - sa)), int(round(Y_ + ca)), R_IRON[2])
            # 나뭇조각
            for (a, sp) in chips:
                d = 6 + 50 * sp * t
                x = cx + math.cos(a) * d
                y = cy + math.sin(a) * d * 0.8 + 56 * t * t
                cv.px(int(x), int(y), W_[int(sp * 10) % 3])
                if sp > 0.8:
                    cv.px(int(x) + 1, int(y), W_[(int(sp * 10) + 1) % 3])
        frames.append(cv.im)
    fr = [frames]
    no_partial(fr)
    meta = fx_meta("boss1_cup_shatter", 128, 128, 8, [40, 50, 60, 70, 80, 90, 100, 120], (64, 60), "cup_anchor",
                   "drink_break_frame0", False,
                   "약점 술통 잔이 부서짐(54라운드 Q6 '한 잔 더' · Q13 술통 잔): 0 = 백열 섬광 + 통에 금(판정 프레임), "
                   "1~ = 널 조각이 회전하며 튀고 쇠테 2개가 벌어져 떨어짐 · 나뭇조각 · 술 덩어리가 솟았다 떨어짐",
                   {"anchorNote": "pivot = 술통 잔 중심. 보스 drink 시트 cupAnchors 사각형(왼쪽 위 x,y + w,h) 가운데(x + w/2, y + h/2 — 시트 도트 → 보스 피벗 기준 환산)에 놓는다",
                    "glowFrames": [0], "emissiveColors": EMISSIVE}, fr)
    save(OUT_F, "boss1_cup_shatter", fr, meta)
    return fr


def liquor_splash():
    frames = []
    r = Rand(9)
    drops = [(math.pi * (1.0 + r.f()), 0.4 + r.f() * 0.9) for _ in range(30)]
    for i in range(7):
        cv = Canvas(160, 96)
        cx, cy = 80, 76
        t = i / 6
        # 왕관 모양으로 솟는 술(0~3) → 바닥 웅덩이로 퍼짐(3~6)
        if i <= 3:
            hgt = int(34 * math.sin(math.pi * min(1, t * 2)))
            for k in range(-24, 25):
                u = k / 24
                h = int(hgt * (0.55 + 0.45 * abs(math.sin(u * 5.5 + 0.4))) * (1 - u * u * 0.6))
                for y in range(h):
                    col = A[23] if y > h - 3 else (A[21] if abs(k) > 18 else A[22])
                    cv.px(cx + k, cy - y - 2, col)
        pr = int(14 + 50 * min(1, t * 1.3))
        for y in range(-12, 13):
            for x in range(-pr - 6, pr + 7):
                wob = 1 + 0.12 * math.sin(3 * math.atan2(y, x + 0.01) + 1.2)
                if (x / (pr * wob)) ** 2 + (y / (pr * 0.24 * wob + 1)) ** 2 <= 1:
                    edge = (x / (pr * wob)) ** 2 + (y / (pr * 0.24 * wob + 1)) ** 2 > 0.75
                    cv.px(cx + x, cy + y, A[18] if edge else (A[20] if y < 0 else A[19]))
        for k in range(5):
            cv.px(cx - pr // 2 + k * 7, cy - 2 + (k % 2), A[24] if i < 5 else A[22])
        for (a, sp) in drops:
            if i == 6:
                break
            d = 6 + 60 * sp * t
            x = cx + math.cos(a) * d
            y = cy - 6 + math.sin(a) * d * 0.7 + 60 * t * t
            cv.rect(int(x), int(y), int(x) + (1 if sp > 0.9 else 0), int(y) + 1, A[22] if t < 0.5 else A[21])
        frames.append(cv.im)
    fr = [frames]
    no_partial(fr)
    meta = fx_meta("boss1_liquor_splash", 160, 96, 7, [50, 60, 70, 80, 90, 110, 160], (80, 76), "hitbox_center", "hit", False,
                   "술 튀김: 솟는 술 왕관 → 바닥 웅덩이로 퍼짐. 술 뿌리기 방울 착지·술통 터짐·뒤집어씀(머리 위 재생 시 scale 0.6 권장)",
                   {"depth": "floor", "emissiveColors": EMISSIVE[:2]}, fr)
    save(OUT_F, "boss1_liquor_splash", fr, meta)
    return fr


def liquor_glob():
    frames = []
    for i in range(4):
        cv = Canvas(48, 32)
        cx, cy = 30, 16
        # 진행 방향(오른쪽)으로 둥근 머리 + 뒤로 늘어지는 꼬리
        for x in range(-22, 9):
            t = (x + 22) / 30
            w = 6.5 * math.sqrt(max(0.0, 1 - ((x - 2) / 7.0) ** 2)) if x > -5 else 3.5 * t + 0.6 * math.sin(x * 0.8 + i * 1.7)
            for y in range(-int(w), int(w) + 1):
                rr = abs(y) / max(1.0, w)
                col = A[23] if (y < 0 and rr > 0.35 and x > -2) else (A[21] if rr < 0.7 else A[19])
                cv.px(cx + x, cy + y + (1 if x < -10 and i % 2 else 0), col)
        cv.px(cx + 2, cy - 4, A[25]); cv.px(cx + 3, cy - 4, A[24])
        for k in range(3):
            cv.px(cx - 24 - k * 4 - i, cy + (k % 2) * 3 - 1, A[21])
        frames.append(cv.im)
    fr = [frames]
    no_partial(fr)
    meta = fx_meta("boss1_liquor_glob", 48, 32, 4, [70, 70, 70, 70], (30, 16), "projectile", "boss_throw_release", True,
                   "뿌린 술 방울 투사체(술 뿌리기). 착지하면 boss1_liquor_splash + 술 웅덩이(불붙은 술 패턴의 연료)",
                   {"rotate": True, "drawnFacing": "right", "emissiveColors": EMISSIVE[:1],
                    "spawnNote": "보스 stage1_throw releaseFrame 의 handAnchors(잔 테) 점에서 부채꼴로 생성"}, fr)
    save(OUT_F, "boss1_liquor_glob", fr, meta)
    return fr


def main():
    out = {"pillar": pillar(), "candelabra": candelabra(), "rolling_barrel": rolling_barrel(), "barrel_break": barrel_break(),
           "torch": torch_fx(), "cup_shatter": cup_shatter(), "liquor_splash": liquor_splash(), "liquor_glob": liquor_glob()}
    for k, v in out.items():
        print(k, "colors", ncolors(v))
    return out


if __name__ == "__main__":
    main()
