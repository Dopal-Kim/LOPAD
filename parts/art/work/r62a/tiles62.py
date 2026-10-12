"""62a — 타일 보강 (P1-19 탄생 전장·버려진 길 / P1-17 수련장 밤 결).

황무지 `tiles/v2/stage1_waste`:
- start 23~26: 칸 경계에서 잘리던 검은 그을음 사각 → 칸 가운데 둥근 재 얼룩(가장자리 8도트는 바닥 0~3 그대로 = 어느 칸과도 이어짐).
- 바닥 변주 +4 (13~16, 옛 v2 소품 예약 칸 재사용): 마른 금 간 흙 · 마른 풀 포기 · 재와 뼈 조각 · 짓밟힌 진흙 — tiles["1"] 에 섞음.
- 엄폐 담 43~46: 같은 자갈 무늬 블록 → 모래주머니 3면(윗면 밝음 · 앞면 가운데 · 아랫단 그늘).
- 데칼: scorch(64) 둥근 알파 가장자리로 다시 + 새 데칼 4(피 웅덩이 · 재 고리 · 흩어진 뼈 · 짓밟힌 진흙).
수련장 `tiles/v2/stage1_training`: 베이지 모래 마당 → 밤 횃불 아래 다진 흙 모래(같은 갈퀴 결, 명도 두 단 낮춤 + 따뜻하게), 회색 석벽 두 단 어둡게.
입력 사본: work/r62a/before/ (첫 실행 때 assets 에서 복사 — 다시 돌려도 같은 결과).
"""
import json
import math
import os
import random
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../v2_outer"))
from kit import G, A, SL, WD, PL  # noqa: E402

from common import TILES, Noise, Fbm, dump  # noqa: E402

BEFORE = os.path.join(HERE, "before")
T = 64
CLEAR = (0, 0, 0, 0)


def src_copy(name):
    os.makedirs(BEFORE, exist_ok=True)
    for ext in ("png", "json"):
        dst = os.path.join(BEFORE, f"{name}.{ext}")
        if not os.path.exists(dst):
            shutil.copy(os.path.join(TILES, "v2", f"{name}.{ext}"), dst)
    return Image.open(os.path.join(BEFORE, f"{name}.png")).convert("RGBA"), json.load(open(os.path.join(BEFORE, f"{name}.json"), encoding="utf-8"))


def cell_box(i, cols=8):
    return ((i % cols) * T, (i // cols) * T)


def get_cell(im, i):
    x, y = cell_box(i)
    return im.crop((x, y, x + T, y + T))


def put_cell(im, i, c):
    x, y = cell_box(i)
    im.paste(c, (x, y))


# ------------------------------------------------------------------ 황무지
FLOOR_BASE = PL[0]


def edge_weight(x, y, margin=8, soft=10):
    """가장자리 margin 안은 0, 그 안쪽 soft 폭에 걸쳐 1 로."""
    d = min(x, y, T - 1 - x, T - 1 - y)
    return max(0.0, min(1.0, (d - margin) / soft))


def radial(x, y, n, rad=22.0, cx=32.0, cy=32.0, sq=0.8):
    """둥근 무게(가운데 1 → rad 에서 0), 잡음으로 가장자리 흔듦. 가장자리 8도트 밖은 0."""
    if edge_weight(x, y, 7, 1) <= 0:
        return 0.0
    d = math.hypot(x - cx, (y - cy) / sq) / rad + (n.at(x / T, y / T) - 0.5) * 0.6
    return max(0.0, 1 - d)


def soot_cell(base, seed, rx, ry, cx=32, cy=32):
    """둥근 재 얼룩: 가운데 짙은 그을음(SL0·G1) → 재 회색(G3) → 흩어진 재 점, 불씨 1~2점. 가장자리 8도트는 base 그대로."""
    c = base.copy()
    p = c.load()
    r = random.Random(seed)
    n = Fbm(seed, 4, 4, 3)
    for y in range(T):
        for x in range(T):
            w = edge_weight(x, y, 7, 8)
            if w <= 0:
                continue
            d = math.hypot((x - cx) / rx, (y - cy) / ry) + (n.at(x / T, y / T) - 0.5) * 0.7
            v = (1 - d) * w
            q = r.random()
            if v > 0.55:
                col = SL[0] if q < 0.7 else G[1]
            elif v > 0.35:
                col = G[1] if q < 0.55 else (SL[0] if q < 0.75 else G[2])
            elif v > 0.18:
                col = G[2] if q < 0.5 else (G[3] if q < 0.8 else None)
            elif v > 0.04:
                col = G[3] if q < 0.18 else (G[4] if q < 0.26 else None)
            else:
                col = None
            if col:
                p[x, y] = col
    # 재 위 밝은 재 조각 · 숯 덩이 · 불씨
    for _ in range(10):
        x, y = cx + r.randint(-rx + 3, rx - 3), cy + r.randint(-ry + 3, ry - 3)
        if edge_weight(x, y, 8, 1) > 0 and p[x, y][:3] in (SL[0][:3], G[1][:3]):
            p[x, y] = G[5]
            if r.random() < 0.4:
                p[x + 1, y] = G[4]
    for _ in range(r.randint(1, 2)):
        x, y = cx + r.randint(-4, 4), cy + r.randint(-3, 3)
        p[x, y] = A[19]
        p[x, y - 1] = A[18]
    return c


def feature_cell(base, kind, seed):
    """바닥 변주 4종 — 가장자리 8도트 밖은 base 그대로."""
    c = base.copy()
    p = c.load()
    r = random.Random(seed)
    n = Fbm(seed, 3, 3, 3)

    def ok(x, y, m=8):
        return m <= x < T - m and m <= y < T - m

    if kind == "cracked":          # 마른 금 간 흙: 한 단 밝고 따뜻한 판 + 다각 금
        for y in range(T):
            for x in range(T):
                w = radial(x, y, n, 21)
                if w > 0.12 and r.random() < 0.6 + w:
                    p[x, y] = PL[1] if (w > 0.3 or r.random() < 0.5) else WD[3]
        for _ in range(5):
            x, y = r.randint(16, 47), r.randint(16, 47)
            ang = r.uniform(0, 2 * math.pi)
            for k in range(r.randint(7, 13)):
                ang += r.uniform(-0.6, 0.6)
                x += math.cos(ang)
                y += math.sin(ang) * 0.7
                xi, yi = int(x), int(y)
                if ok(xi, yi, 9):
                    p[xi, yi] = WD[1]
                    if ok(xi, yi + 1, 9):
                        p[xi, yi + 1] = PL[2] if k % 3 == 0 else p[xi, yi + 1]
    elif kind == "grass":          # 마른 풀 포기 3~4 + 작은 돌
        for (gx, gy) in ((22, 26), (40, 22), (30, 42), (44, 40))[: r.randint(3, 4)]:
            for b in range(9):
                a = -math.pi / 2 + r.uniform(-0.9, 0.9)
                L = r.uniform(4, 9)
                for t in range(int(L)):
                    x = int(round(gx + math.cos(a) * t + (t * t * 0.03 * (1 if a > -math.pi / 2 else -1))))
                    y = int(round(gy + math.sin(a) * t))
                    if ok(x, y, 6):
                        p[x, y] = (WD[4] if t > L * 0.5 else PL[2]) if b % 3 else (PL[3] if t > L * 0.6 else WD[3])
            for dx in range(-3, 4):
                if ok(gx + dx, gy + 1, 6):
                    p[gx + dx, gy + 1] = WD[1]
        x, y = 34, 33
        for (dx, dy, col) in ((0, 0, G[5]), (1, 0, G[6]), (2, 0, G[5]), (0, 1, G[4]), (1, 1, G[4]), (2, 1, G[3]), (1, -1, G[7])):
            p[x + dx, y + dy] = col
    elif kind == "bones":          # 재 흩뿌림 + 갈비뼈 조각·두개골 조각
        for y in range(T):
            for x in range(T):
                w = radial(x, y, n, 20)
                if w > 0.1 and r.random() < 0.25 + w * 0.5:
                    p[x, y] = G[3] if r.random() < 0.6 else G[4]
        for k in range(4):                         # 갈비뼈 호
            cx, cy = 26 + k * 4, 30
            for t in range(9):
                a = math.pi * (0.15 + t / 10)
                x, y = int(cx + math.cos(a) * 7), int(cy + math.sin(a) * 4)
                if ok(x, y):
                    p[x, y] = PL[4] if t % 3 else PL[3]
                    if ok(x, y + 1):
                        p[x, y + 1] = PL[0] if t % 2 else p[x, y + 1]
        for (dx, dy) in ((0, 0), (1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (0, 2), (2, 2)):
            p[40 + dx, 40 + dy] = PL[4] if dy < 2 else PL[2]
        p[41, 41] = SL[0]
        p[43, 41] = SL[0]
    elif kind == "mud":            # 짓밟힌 진흙: 짙은 흙 + 발자국 2 + 젖은 반짝 1
        for y in range(T):
            for x in range(T):
                v = radial(x, y, n, 20)
                if v > 0.35:
                    p[x, y] = WD[1] if v > 0.55 else WD[2]
                elif v > 0.12 and r.random() < v * 2:
                    p[x, y] = WD[2]
        for (fx, fy) in ((24, 26), (36, 38)):
            for dy in range(-4, 5):
                for dx in range(-2, 3):
                    if (dx * dx) / 4.5 + (dy * dy) / 20 <= 1:
                        p[fx + dx, fy + dy] = SL[0] if dy > -3 else WD[0]
            p[fx - 1, fy - 4] = PL[1]
        p[31, 30] = PL[3]
        p[32, 30] = PL[2]
    return c


def sandbag_face(kind, seed):
    """모래주머니 담: kind lower/lower_b/upper = 앞면(납작한 자루 네 줄, 줄마다 반 자루 엇갈림), top = 윗면(자루 등을 위에서 본 면).
    가로 64 주기로 이어짐. 빛 = 좌상단: 자루 윗등 밝음 → 아래 1/3 그늘 → 이음 홈 먹. 윗면은 앞면보다 두 단 밝게(3면 구분)."""
    c = Image.new("RGBA", (T, T), CLEAR)
    p = c.load()
    r = random.Random(seed)
    n = Noise(seed, 16, 16)
    BH = 16                     # 자루 높이(앞면)
    BW = 32
    for y in range(T):
        for x in range(T):
            if kind == "top":
                row = y // 16
                off = (0, 11, 22, 7)[row]
                u = ((x + off) % BW) / BW
                v = (y % 16) / 16
                qx = min(u * BW, BW - u * BW)
                qy = min(v * 16, 16 - v * 16)
                if qx < 5 and qy < 5 and math.hypot(5 - qx, 5 - qy) > 5:
                    p[x, y] = WD[1]
                    continue
                prof = math.sin(u * math.pi) ** 0.5 * math.sin(v * math.pi) ** 0.6
                lit = prof * 0.9 + (0.08 if u < 0.45 else -0.05) + (n.at(x / T, y / T) - 0.5) * 0.15
                if u < 0.04 or u > 0.96 or v > 0.92:
                    col = WD[1]
                elif lit > 0.72:
                    col = PL[3]
                elif lit > 0.5:
                    col = PL[2]
                elif lit > 0.28:
                    col = PL[1]
                else:
                    col = PL[0]
            else:
                row = y // BH
                off = (0, 13, 5, 19)[row] + (8 if kind == "upper" else 0)
                u = ((x + off) % BW) / BW
                v = (y % BH) / BH
                bx, by = u * BW, v * BH                      # 자루 모서리 둥글게(반지름 5) — 벽돌처럼 안 보이게
                cr = 6.0
                qx = min(bx, BW - bx)
                qy = min(by, BH - by)
                if qx < cr and qy < cr and math.hypot(cr - qx, cr - qy) > cr:
                    p[x, y] = SL[0] if by < BH / 2 else WD[1]
                    continue
                prof = math.sin(u * math.pi) ** 0.8 * math.sin(min(1.0, v * 1.15) * math.pi) ** 0.5
                lit = prof * (1.0 - 0.45 * v) + (0.07 if u < 0.45 else -0.04) + (n.at(x / T, y / T) - 0.5) * 0.12
                if row == 3 and kind != "upper":
                    lit -= 0.1
                if v < 0.06 or u < 0.03 or u > 0.97:
                    col = SL[0]
                elif lit > 0.66:
                    col = PL[2]
                elif lit > 0.46:
                    col = PL[1]
                elif lit > 0.28:
                    col = PL[0]
                elif lit > 0.14:
                    col = WD[2]
                else:
                    col = WD[1]
            p[x, y] = col
    # 삼베 결(드문 점) · 묶은 끈 귀
    for y in range(1, T, 3):
        for x in range((y // 3) % 4, T, 5):
            cur = p[x, y][:3]
            if cur == PL[1][:3]:
                p[x, y] = PL[0]
            elif cur == PL[2][:3]:
                p[x, y] = PL[1]
    if kind != "top":
        for row in range(4):
            off = (0, 13, 5, 19)[row] + (8 if kind == "upper" else 0)
            for k in range(2):
                ex = (k * BW - off + BW - 2) % T
                y = row * BH + 3
                for (dx, dy, col) in ((0, 0, WD[4]), (1, 0, WD[3]), (0, 1, WD[3]), (1, 1, WD[2])):
                    p[(ex + dx) % T, y + dy] = col
    if kind in ("lower", "lower_b"):
        for _ in range(50 if kind == "lower" else 80):
            x, y = r.randint(0, T - 1), r.randint(54, 62)
            if p[x, y][:3] in (PL[0][:3], WD[3][:3], WD[2][:3]):
                p[x, y] = WD[1] if r.random() < 0.6 else WD[2]
        if kind == "lower_b":            # 터진 자루 — 모래가 흘러내림
            for k in range(14):
                for dx in range(-k // 3, k // 3 + 1):
                    x, y = 28 + dx, 40 + k
                    if y < T - 1:
                        p[x, y] = PL[1] if (dx + k) % 3 else PL[2]
            for (x, y) in ((26, 38), (27, 37), (30, 38), (31, 37), (28, 39)):
                p[x, y] = SL[0]
    return c


def decal(kind, w, h, seed):
    """둥근 알파 가장자리 데칼(바닥 위·소품 아래). 알파 6단(255·210·160·110·70·35) — 가장자리로 갈수록 옅게."""
    c = Image.new("RGBA", (w, h), CLEAR)
    p = c.load()
    r = random.Random(seed)
    n = Fbm(seed, 4, 3, 3)
    ALPH = [255, 210, 160, 110, 70, 35]
    cx, cy = w / 2, h / 2
    rx, ry = w / 2 - 6, h / 2 - 5
    for y in range(h):
        for x in range(w):
            d = math.hypot((x - cx) / rx, (y - cy) / ry) + (n.at(x / w, y / h) - 0.5) * 0.55
            if d >= 1.0:
                continue
            v = 1 - d
            if kind == "scorch":
                col = SL[0] if v > 0.45 else (G[1] if v > 0.25 else G[2])
                if v > 0.3 and r.random() < 0.06:
                    col = G[4]
            elif kind == "blood":
                col = A[17] if v > 0.12 else A[18]
                if v > 0.35 and r.random() < 0.08:
                    col = A[16]
                if 0.25 < v < 0.3 and r.random() < 0.3:
                    col = A[19]
            elif kind == "ash":
                ring = abs(d - 0.62)
                if ring > 0.24 and r.random() < 0.75:
                    continue
                col = G[4] if r.random() < 0.5 else G[3]
            elif kind == "mud":
                col = WD[0] if v > 0.5 else (WD[1] if v > 0.22 else WD[2])
            else:
                col = G[2]
            a_i = 0 if v > 0.30 else (1 if v > 0.22 else (2 if v > 0.15 else (3 if v > 0.09 else (4 if v > 0.04 else 5))))
            if kind == "ash":
                a_i = min(5, a_i + 1)
            p[x, y] = (col[0], col[1], col[2], ALPH[a_i])
    if kind == "blood":          # 젖은 반짝 2점 · 튄 방울
        for (x, y) in ((int(cx - rx * 0.3), int(cy - ry * 0.3)), (int(cx + rx * 0.1), int(cy - ry * 0.4))):
            p[x, y] = A[19]
            p[x + 1, y] = A[18]
        for _ in range(9):
            a = r.uniform(0, 2 * math.pi)
            x, y = int(cx + math.cos(a) * rx * r.uniform(0.95, 1.05)), int(cy + math.sin(a) * ry * r.uniform(0.95, 1.1))
            if 1 < x < w - 2 and 1 < y < h - 2:
                p[x, y] = A[17]
    if kind == "bones":
        pass
    return c


def bones_decal(w, h, seed):
    c = decal("ash", w, h, seed)
    p = c.load()
    r = random.Random(seed + 1)
    for k in range(7):          # 뼈 막대
        x, y = r.randint(14, w - 18), r.randint(12, h - 12)
        ang = r.uniform(-0.5, 0.5)
        L = r.randint(6, 12)
        for t in range(L):
            xx, yy = int(x + math.cos(ang) * t), int(y + math.sin(ang) * t * 0.6)
            p[xx, yy] = PL[4]
            p[xx, yy + 1] = PL[1]
        p[x - 1, y] = PL[3]
        p[int(x + math.cos(ang) * L), int(y + math.sin(ang) * L * 0.6)] = PL[3]
    x, y = w // 2 + 10, h // 2 - 4         # 두개골 조각
    for (dx, dy) in ((0, 0), (1, 0), (2, 0), (3, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (-1, 2), (0, 2), (2, 2), (4, 2), (0, 3), (1, 3), (2, 3), (3, 3)):
        p[x + dx, y + dy] = PL[4] if dy < 2 else PL[2]
    p[x + 1, y + 2] = SL[0]
    p[x + 3, y + 2] = SL[0]
    return c


WASTE_DECALS_NEW = [
    {"name": "blood_pool", "rect": {"x": 320, "y": 512, "w": 128, "h": 64}, "index": 69, "footprint": [2, 1],
     "note": "62a — 피 웅덩이(둥근 알파 가장자리). 쓰러진 병사·시체 더미 곁"},
    {"name": "ash_ring", "rect": {"x": 128, "y": 576, "w": 128, "h": 64}, "index": 74, "footprint": [2, 1],
     "note": "62a — 재 고리(불탄 자리 둘레에 흩어진 재)"},
    {"name": "bone_scatter", "rect": {"x": 256, "y": 576, "w": 128, "h": 64}, "index": 76, "footprint": [2, 1],
     "note": "62a — 흩어진 뼈·두개골 조각 + 재"},
    {"name": "trampled_mud", "rect": {"x": 384, "y": 576, "w": 128, "h": 64}, "index": 78, "footprint": [2, 1],
     "note": "62a — 짓밟힌 진흙(둥근 알파 가장자리)"},
]


def build_waste(dry=False):
    im, meta = src_copy("stage1_waste")
    base = [get_cell(im, i) for i in range(4)]
    # start 23~26 다시: 바닥 0~3 위에 둥근 재 얼룩(크기 4단)
    for k, (i, rx, ry) in enumerate(((23, 10, 8), (24, 15, 11), (25, 20, 14), (26, 24, 17))):
        put_cell(im, i, soot_cell(base[k % 4], 600 + i, rx, ry, 32 + (k % 2) * 2 - 1, 32 + (k // 2) - 1))
    # 바닥 변주 13~16
    feats = [(13, "cracked"), (14, "grass"), (15, "bones"), (16, "mud")]
    for k, (i, kind) in enumerate(feats):
        put_cell(im, i, feature_cell(base[(k + 1) % 4], kind, 620 + i))
    # 엄폐 담 43~46
    put_cell(im, 43, sandbag_face("lower", 643))
    put_cell(im, 44, sandbag_face("upper", 644))
    put_cell(im, 45, sandbag_face("top", 645))
    put_cell(im, 46, sandbag_face("lower_b", 646))
    # 데칼: scorch 다시 + 새 4
    x0, y0 = 0, 512
    im.paste(CLEAR, (0, 512, 128, 640))
    im.paste(decal("scorch", 128, 128, 664), (0, 512))
    im.paste(CLEAR, (320, 512, 448, 576))
    im.paste(decal("blood", 128, 64, 669), (320, 512))
    im.paste(CLEAR, (128, 576, 512, 640))
    im.paste(decal("ash", 128, 64, 674), (128, 576))
    im.paste(bones_decal(128, 64, 676), (256, 576))
    im.paste(decal("mud", 128, 64, 678), (384, 576))
    # JSON
    meta["tiles"]["1"] = [0, 0, 0, 1, 1, 2, 2, 3, 3, 13, 14, 15, 16]
    meta["tilesNote"] = ("목록 안 중복 = 가중치. 바닥 0~3 은 공유 주기 잡음으로 가장자리가 같아 어떤 변형끼리 붙어도 이어진다. "
                         "62a: 변주 13~16(마른 금 흙·마른 풀·재와 뼈·짓밟힌 진흙)을 더함 — 가장자리 8도트는 0~3 과 같아 이음 그대로")
    for i, kind in feats:
        meta["names"][str(i)] = f"floor_{kind}"
    meta["names"]["13"] = "floor_cracked"
    meta["walls"]["stoneSet"]["note"] = ("모래주머니 담(엄폐) — 62a 다시 그림: 윗면 45 밝은 삼베 자루 끝 · 앞면 43/46 자루 두 줄(위 빛 → 아래 그늘, 46 = 터진 자루) · "
                                          "윗단 44. 52라운드: 황무지는 1칸 낮은 담 허용 → upper 를 생략하고 lower+top 만 써도 된다")
    decals = [d for d in meta["decals"] if d["name"] != "scorch"]
    decals.insert(0, {"name": "scorch", "rect": {"x": 0, "y": 512, "w": 128, "h": 128}, "index": 64, "footprint": [2, 2],
                      "note": "그을린 자국(모닥불·불탄 수레 밑) — 62a 둥근 알파 가장자리(6단)로 다시"})
    meta["decals"] = decals + WASTE_DECALS_NEW
    meta["decalsNote"] = ("바닥 데칼(선택): rect 로 잘라 바닥 위·소품 아래에 겹침. footprint = 칸 수. 통과 가능. "
                          "62a: 데칼은 그림 자체에 알파 가장자리(255·210·160·110·70·35)가 있다 — 추가 반투명 없이 그대로 그려도 사각으로 잘리지 않음. "
                          "방마다 2~5개, 탄생지(birth)는 blood_pool·bone_scatter·scorch, 버려진 길은 trampled_mud·ash_ring·wheel_ruts 제안")
    meta["redrawn62a"] = [13, 14, 15, 16, 23, 24, 25, 26, 43, 44, 45, 46, 64, 65, 69, 72, 73, 74, 76, 78]
    meta["redrawn62aNote"] = "P1-19: start 23~26 칸 경계 잘림 → 둥근 재 얼룩 · 바닥 변주 13~16 · 모래주머니 담 3면 · 데칼 알파 가장자리"
    meta["roomFloorsNote"] = meta.get("roomFloorsNote", "") + " · 62a: start 4변형은 칸 가운데 둥근 재 얼룩(크기 4단, 가장자리 8도트는 바닥 그대로)"
    if not dry:
        im.save(os.path.join(TILES, "v2", "stage1_waste.png"), optimize=True)
        dump(meta, os.path.join(TILES, "v2", "stage1_waste.json"))
    return im, meta


# ------------------------------------------------------------------ 수련장
def lut_training():
    m = {}
    # 바닥 모래(베이지) → 밤 다진 흙 모래(따뜻하게 두 단 아래)
    m[PL[4][:3]] = PL[1]
    m[PL[3][:3]] = PL[0]
    m[PL[2][:3]] = WD[2]
    m[PL[1][:3]] = WD[1]
    m[PL[0][:3]] = WD[1]
    m[WD[5][:3]] = WD[3]
    m[WD[4][:3]] = WD[2]
    m[WD[3][:3]] = WD[2]
    m[WD[2][:3]] = WD[1]
    m[WD[1][:3]] = WD[0]
    for i in range(3, 16):
        m[G[i][:3]] = G[max(1, i - 2)]
    m[G[2][:3]] = G[1]
    m[SL[1][:3]] = SL[0]
    m[SL[2][:3]] = SL[1]
    m[SL[3][:3]] = SL[2]
    m[SL[4][:3]] = SL[2]
    return m


def lut_walls():
    m = {}
    for i in range(3, 16):
        m[G[i][:3]] = G[max(1, i - 2)]
    m[G[2][:3]] = G[1]
    m[PL[1][:3]] = G[4]
    m[PL[2][:3]] = PL[0]
    m[PL[3][:3]] = PL[1]
    m[PL[4][:3]] = PL[2]
    m[SL[1][:3]] = SL[0]
    return m


def apply_lut(cell, lut):
    p = cell.load()
    for y in range(cell.height):
        for x in range(cell.width):
            c = p[x, y]
            if c[3] and c[:3] in lut:
                n = lut[c[:3]]
                p[x, y] = (n[0], n[1], n[2], c[3])
    return cell


def straw_bits(cell, seed):
    """밤 마당의 지푸라기·작은 돌(가장자리 8도트 밖)."""
    p = cell.load()
    r = random.Random(seed)
    for _ in range(4):
        x, y = r.randint(10, 52), r.randint(10, 52)
        ang = r.uniform(-0.6, 0.6)
        for t in range(r.randint(3, 6)):
            xx, yy = int(x + math.cos(ang) * t), int(y + math.sin(ang) * t)
            if 8 <= xx < 56 and 8 <= yy < 56:
                p[xx, yy] = PL[2] if t % 2 else WD[4]
    return cell


TRAIN_FLOOR = [0, 1, 2, 3, 4] + list(range(23, 35))
TRAIN_WALL = [5, 21, 22, 63, 40, 41, 42, 6, 47, 48, 49, 50, 51, 52, 43, 44, 45, 46, 8, 9, 10, 11, 12, 61]


def build_training(dry=False):
    im, meta = src_copy("stage1_training")
    lf, lw = lut_training(), lut_walls()
    for i in TRAIN_FLOOR:
        c = apply_lut(get_cell(im, i), lf)
        if i in (1, 2, 3, 24, 25, 29, 31):
            straw_bits(c, 700 + i)
        put_cell(im, i, c)
    for i in TRAIN_WALL:
        put_cell(im, i, apply_lut(get_cell(im, i), lw))
    meta["version"] = ("62a (P1-17) — 밤 수련장: 모래 마당 명도 두 단 낮춤·따뜻하게(횃불 아래 다진 흙 모래), 석벽·문·덮개 두 단 어둡게. 이전: "
                       + meta.get("version", ""))
    meta["recolored62a"] = {"floor": TRAIN_FLOOR, "walls": TRAIN_WALL,
                            "note": "같은 갈퀴 결·인덱스·이음 그대로, 색만 1:1 바꿈(가장자리 이음 불변). 지푸라기 점은 1·3·25·29 칸 가운데에만"}
    tl = meta.get("tileLights", {})
    if "21" in tl:
        tl["21"]["radius"] = 220
        tl["21"]["intensity"] = 0.8
    meta["tileLights"] = tl
    meta["lightNote62a"] = "밤 결이므로 벽 횃불(21) 반경·세기를 올림(220·0.8). 수련장 walls.front.lower 목록에 21 이 1/5 — 방마다 횃불 2~3개가 보이게 배치 권장"
    if not dry:
        im.save(os.path.join(TILES, "v2", "stage1_training.png"), optimize=True)
        dump(meta, os.path.join(TILES, "v2", "stage1_training.json"))
    return im, meta


def build(dry=False):
    return {"waste": build_waste(dry), "training": build_training(dry)}
