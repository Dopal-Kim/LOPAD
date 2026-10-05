"""60라운드 Q4 샘플 — 1층 양조 구역 바닥 판석·술 얼룩·낮은 벽돌 담(엄폐) 보강안 (assets 에 쓰지 않는다).

원본: assets/tiles/v2/stage1_brewery 의 0~3(바닥) · 27~30(trial = 술 얼룩) · 43~46(엄폐 담 stoneSet) · 62(술 얼룩 바닥).
진단(T1~T5) 대응:
  T1 격자 반복 — 같은 크기 사각 판석이 칸마다 되풀이 → 칸마다 다른 분할 틀 6종(1·2·3·4장, 엇갈림), 모서리 깨짐, 판석마다 명도 ±1.
  T2 체크 디더 얼룩 — 50% 바둑판 점이 '소금·후추' → 디더 0, 2~3톤 덩어리(cluster) 질감 + 닳은 결.
  T3 빛 반응 — 1px 테 → 판석 윗·왼 모서리 밝게 / 아래·오른 모서리 어둡게(쿼터뷰 높이) + 젖은 반짝임 점(G09·G10)이 등불을 받으면 산다.
  T4 술 얼룩 — 갈색 판 + 주황 1점 → 고인 술(어두운 호박) + 테두리 + 반사 점, 줄눈을 따라 스며든 줄.
  T5 엄폐 담 윗면이 바닥 판석과 같은 그림 → 두꺼운 갓돌(앞 모서리 빛) + 벽돌 앞면 그을음·벽돌마다 명도 차.
색: lopad gray(G) + 1층 램프 A16~22 + v2 재질 SL·WD·PL — 새 색 없음. 반투명 0.
N = 32(현행 규격 §11 '타일 32px', pixelScale 1) 이 기본. N = 64 는 2배 밀도 비교용(인터뷰 대상, pixelScale 0.5).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "../v2_outer")))
import kit  # noqa: E402

from PIL import Image  # noqa: E402

G, A, SL, WD, PL = kit.G, kit.A, kit.SL, kit.WD, kit.PL

# 판석 램프(어두움 → 밝음): 줄눈·그늘·본색 2·밝은 테·젖은 반짝임 — 젖은 중립 회색, 살짝 청회
GROUT = SL[1]
GROUT_DEEP = G[1]
STONE = [G[1], G[2], G[3], G[4], PL[0], G[5], PL[1], G[6], G[7], G[8], G[9]]
# 3회차 비평: WD1 이 G3 보다 어두워 갈색 얼룩(위장 무늬)이 됨 → 램프를 명도순으로, 따뜻함은 PL0·PL1 로만
# 2회차 비평(조명 목업): 청회 판석이 테두리 발치 땅보다 밝고 차가워 캐릭터가 묻힘 → 무채 + 따뜻한 회갈(PL·WD) 섞음, 평균 명도 ≈ 현행(약 62)
#        0     1      2     3      4     5      6     7     8     9      10
LIQ = [A[16], A[17], A[18], A[19], A[20], A[21], A[22]]


def h(*v):
    x = 2166136261
    for a in v:
        x = ((x ^ (int(a) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    x ^= x >> 13
    x = (x * 0x5bd1e995) & 0xFFFFFFFF
    return x ^ (x >> 15)


def hf(*v):
    return (h(*v) & 0xFFFF) / 65535.0


def vnoise(x, y, s, seed):
    """값 잡음(겹선형) — 덩어리 질감용. s = 격자 간격."""
    gx, gy = x / s, y / s
    x0, y0 = int(gx), int(gy)
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    def r(i, j):
        return hf(i, j, seed)
    a = r(x0, y0) + (r(x0 + 1, y0) - r(x0, y0)) * fx
    b = r(x0, y0 + 1) + (r(x0 + 1, y0 + 1) - r(x0, y0 + 1)) * fx
    return a + (b - a) * fy


# 분할 틀(칸 = 0~1 좌표). 줄눈은 칸 왼쪽·위쪽 가장자리에 1줄(이웃 칸 오른쪽·아래와 공유) + 틀 안쪽 선.
LAYOUTS = {
    "one": [(0, 0, 1, 1)],
    "two_h": [(0, 0, 1, 0.56), (0, 0.56, 1, 1)],
    "two_v": [(0, 0, 0.62, 1), (0.62, 0, 1, 1)],
    "three": [(0, 0, 1, 0.5), (0, 0.5, 0.44, 1), (0.44, 0.5, 1, 1)],
    "three_b": [(0, 0, 0.5, 0.62), (0.5, 0, 1, 0.62), (0, 0.62, 1, 1)],
    "four": [(0, 0, 0.56, 0.44), (0.56, 0, 1, 0.44), (0, 0.44, 0.38, 1), (0.38, 0.44, 1, 1)],
}


def stone_tile(N, seed, layout, stain=None, sunk=()):
    """판석 칸 하나. stain = None | (cx, cy, r) 0~1 좌표 술 웅덩이. sunk = 가라앉은(어두운) 판석 번호."""
    g = max(1, N // 32)                     # 줄눈 두께(32 → 1, 64 → 2)
    im = Image.new("RGBA", (N, N), (0, 0, 0, 255))
    px = im.load()
    rects = []
    for k, (a, b, c, d) in enumerate(LAYOUTS[layout]):
        x0, y0, x1, y1 = round(a * N), round(b * N), round(c * N), round(d * N)
        rects.append((k, x0, y0, x1, y1))
    owner = [[-1] * N for _ in range(N)]
    for k, x0, y0, x1, y1 in rects:
        for y in range(y0 + g, y1):
            for x in range(x0 + g, x1):
                owner[y][x] = k
    # 모서리 깨짐: 판석마다 1~2 모서리를 계단으로 깎음(줄눈 색으로)
    for k, x0, y0, x1, y1 in rects:
        for ci, (cx, cy, sx, sy) in enumerate(((x0 + g, y0 + g, 1, 1), (x1 - 1, y0 + g, -1, 1), (x0 + g, y1 - 1, 1, -1), (x1 - 1, y1 - 1, -1, -1))):
            if hf(seed, k, ci, 3) < 0.45:
                depth = (1 + int(hf(seed, k, ci, 4) * 2.5)) * g
                for j in range(depth):
                    for i in range(depth - j):
                        xx, yy = cx + sx * i, cy + sy * j
                        if 0 <= xx < N and 0 <= yy < N and owner[yy][xx] == k:
                            owner[yy][xx] = -1
    # 판석 본색: 판석마다 명도 차(±1) + 큰 덩어리 잡음 2~3톤
    base_of = {}
    for k, *_ in rects:
        v = hf(seed, k, 9)
        base_of[k] = 2 + (0 if v < 0.2 else (1 if v < 0.75 else 2)) - (1 if k in sunk else 0)
    for y in range(N):
        for x in range(N):
            k = owner[y][x]
            if k < 0:
                # 줄눈: 깊은 곳 점점이(덩어리)
                px[x, y] = GROUT_DEEP if vnoise(x, y, 3 * g, seed + 77) < 0.32 else GROUT
                continue
            b = base_of[k]
            n1 = vnoise(x, y, 6 * g, seed * 7 + k)
            n2 = vnoise(x, y, 2.5 * g, seed * 13 + k)
            lv = b + (1 if n1 > 0.74 else (-1 if n1 < 0.2 else 0)) + (1 if n2 > 0.9 else 0)
            px[x, y] = STONE[max(0, min(6, lv))]
    # 쿼터뷰 높이: 판석 윗·왼 모서리 밝게, 아래·오른 모서리 어둡게(빛 = 왼쪽 위)
    def own(x, y):
        return owner[y][x] if 0 <= x < N and 0 <= y < N else -2

    for y in range(N):
        for x in range(N):
            k = owner[y][x]
            if k < 0:
                continue
            b = base_of[k]
            up, lf = own(x, y - g), own(x - g, y)
            dn, rt = own(x, y + 1), own(x + 1, y)
            if up == -1 or lf == -1:
                # 바로 윗줄/왼줄이 줄눈 → 밝은 테. 64 에서는 2줄(바깥 더 밝게)
                outer = own(x, y - 1) == -1 or own(x - 1, y) == -1
                top = up == -1
                px[x, y] = STONE[min(8, b + ((2 if outer else 1) if top else 1))]
            elif dn in (-1, -2) and y == N - 1 or rt in (-1, -2) and x == N - 1:
                px[x, y] = STONE[max(0, b - 2)]          # 칸 오른쪽·아래 끝 = 이웃 칸 줄눈 직전 그늘
            elif dn == -1 or rt == -1:
                px[x, y] = STONE[max(0, b - 2)]
    # 닳은 결 + 움푹 팬 점 + 금(판석 하나 정도)
    for k, x0, y0, x1, y1 in rects:
        w, hh = x1 - x0, y1 - y0
        npits = int(w * hh / (220 * g * g)) * (3 if g > 1 else 1)
        pg = 1 if g > 1 else g           # 64 는 팬 점을 1 도트로(더 고운 세부)
        for i in range(npits):
            x = x0 + 2 * g + int(hf(seed, k, i, 21) * max(1, w - 4 * g))
            y = y0 + 2 * g + int(hf(seed, k, i, 22) * max(1, hh - 4 * g))
            if owner[y][x] == k:
                for dx in range(pg):
                    for dy in range(pg):
                        px[x + dx, y + dy] = STONE[max(0, base_of[k] - 2)]
                        if y + pg + dy < N and owner[y + pg + dy][x + dx] == k:
                            px[x + dx, y + pg + dy] = STONE[min(8, base_of[k] + 1)]
        if hf(seed, k, 31) < 0.14 and w > 10 * g and hh > 8 * g:
            x, y = x0 + w // 3 + int(hf(seed, k, 32) * w / 3), y0 + 2 * g
            dx = 1 if hf(seed, k, 33) < 0.5 else -1
            steps = int(hh * 0.6)
            for i in range(steps):
                if not (0 <= x < N and 0 <= y < N) or owner[y][x] != k:
                    break
                px[x, y] = STONE[0]
                if 0 <= x + 1 < N and owner[y][x + 1] == k:
                    px[x + 1, y] = STONE[min(8, base_of[k] + 1)]
                y += 1
                r_ = hf(seed, k, i, 34)
                if r_ < 0.3:
                    x += dx
                elif r_ > 0.88:
                    dx = -dx                 # 4회차 비평: 곧은 사선이 '/' 긁힘처럼 반복 → 방향을 가끔 꺾어 구불구불
        # 젖은 반짝임: 판석 왼쪽 위 사분면에 1~2점(64 는 2×1)
        for i in range(1 if (w * hh > 360 * g * g and hf(seed, k, 40) < 0.7) else 0):
            x = x0 + 2 * g + int(hf(seed, k, i, 41) * max(1, w // 2))
            y = y0 + 2 * g + int(hf(seed, k, i, 42) * max(1, hh // 2))
            if 0 <= x < N and 0 <= y < N and owner[y][x] == k:
                px[x, y] = STONE[9] if i == 0 else STONE[8]
                if g > 1 and x + 1 < N and owner[y][x + 1] == k:
                    px[x + 1, y] = STONE[8]
    if stain:
        liquor(px, owner, N, g, seed, *stain)
    return im


def liquor(px, owner, N, g, seed, cx, cy, r):
    """고인 술: 불규칙 덩어리(원 4개 합) — 가장자리 A19 테, 안쪽 A16~18, 반사 점 A21·A22·G10, 줄눈을 따라 스민 줄 A17."""
    blobs = [(cx, cy, r)] + [(cx + (hf(seed, i, 51) - 0.5) * r * 1.4, cy + (hf(seed, i, 52) - 0.5) * r * 0.9,
                               r * (0.45 + 0.35 * hf(seed, i, 53))) for i in range(3)]
    inside = [[False] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            u, v = (x + 0.5) / N, (y + 0.5) / N
            for bx, by, br in blobs:
                if ((u - bx) / br) ** 2 + ((v - by) / (br * 0.62)) ** 2 <= 1:
                    inside[y][x] = True
                    break
    for y in range(N):
        for x in range(N):
            if not inside[y][x]:
                continue
            edge = any(not (0 <= x + dx < N and 0 <= y + dy < N and inside[y + dy][x + dx])
                       for dx, dy in ((g, 0), (-g, 0), (0, g), (0, -g)))
            if owner[y][x] == -1:
                px[x, y] = LIQ[0]
            elif edge:
                top = not (0 <= y - g < N and inside[y - g][x])
                px[x, y] = LIQ[2] if top else LIQ[0]
            else:
                n = vnoise(x, y, 4 * g, seed + 61)
                px[x, y] = LIQ[1] if n > 0.45 else LIQ[0]
    # 반사: 웅덩이 왼쪽 위 가장자리 안쪽에 짧은 띠
    sx, sy = int((cx - r * 0.35) * N), int((cy - r * 0.18) * N)
    for i in range(3 * g):
        x, y = sx + i, sy + (i // (2 * g))
        if 0 <= x < N and 0 <= y < N and inside[y][x] and owner[y][x] >= 0:
            px[x, y] = LIQ[4] if i < 2 * g else LIQ[3]
    gx, gy = int((cx + r * 0.25) * N), int((cy + r * 0.1) * N)
    if 0 <= gx < N and 0 <= gy < N and inside[gy][gx]:
        px[gx, gy] = G[10]
    # 줄눈으로 스민 술(웅덩이에 닿은 줄눈을 따라 몇 칸)
    for y in range(N):
        for x in range(N):
            if owner[y][x] == -1 and not inside[y][x]:
                near = any(0 <= x + dx < N and 0 <= y + dy < N and inside[y + dy][x + dx]
                           for dx in range(-3 * g, 3 * g + 1) for dy in range(-g, g + 1))
                if near and hf(x, y, seed, 71) < 0.8:
                    px[x, y] = LIQ[1]


# ---- 낮은 벽돌 담(엄폐 stoneSet): 앞면 아랫단 lower · 윗단 upper · 윗면 top -----------------
BRICK = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[2], PL[3], PL[4]]
# 4회차 비평: 무채·갈색을 번갈아 둔 램프가 녹 얼룩처럼 시끄러움 → 갈색 명도순 램프, 벽돌마다 ±1 만
MORTAR = [G[1], G[2], SL[1]]


def brick_face(N, seed, part):
    """앞면(벽돌 4단, 엇갈림). part = 'upper'(위 칸: 갓돌 밑 그늘 띠) / 'lower'(아래 칸: 발치 그을음·땅 그늘)."""
    g = max(1, N // 32)
    im = Image.new("RGBA", (N, N), (0, 0, 0, 255))
    px = im.load()
    rows = 4
    bh = N // rows
    bw = N // 2
    for y in range(N):
        r = y // bh
        yy = y % bh
        off = (bw // 2) * (r % 2)
        for x in range(N):
            xx = (x + off) % bw
            bi = (x + off) // bw
            if yy < g or xx < g:
                px[x, y] = MORTAR[0] if (yy < g and xx >= g) else MORTAR[1]
                continue
            v = hf(seed, r, bi, 5)
            b = 2 + (1 if v > 0.72 else (-1 if v < 0.18 else 0))  # 5회차: 그을린 벽돌(테두리 벽돌 명도)로 한 단 낮춤
            n = vnoise(x, y, 3 * g, seed + r * 11 + bi)
            lv = b + (-1 if n < 0.16 else 0)
            if yy < 2 * g:                   # 벽돌 윗면 모서리 빛
                lv += 2
            elif yy >= bh - g:               # 아랫모서리 그늘
                lv -= 1
            if xx < 2 * g:
                lv += 1
            px[x, y] = BRICK[max(0, min(8, lv))]
    if part == "upper":
        for y in range(3 * g):               # 갓돌 밑 그늘 띠
            for x in range(N):
                c = px[x, y]
                px[x, y] = MORTAR[0] if y < g else (BRICK[max(0, BRICK.index(c[:3] + (255,)) - 2)] if c[:3] + (255,) in BRICK else c)
    if part == "lower":
        for y in range(N - 6 * g, N):         # 발치 그을음: 아래로 갈수록 한 단씩, 덩어리 경계
            for x in range(N):
                c = px[x, y]
                t = (y - (N - 6 * g)) / (6 * g)
                if c[:3] + (255,) in BRICK and vnoise(x, y, 3 * g, seed + 9) < t * 1.1:
                    px[x, y] = BRICK[max(0, BRICK.index(c[:3] + (255,)) - (2 if t > 0.6 else 1))]
        for x in range(N):
            px[x, N - 1] = MORTAR[0]
    # 떨어져 나간 벽돌 모서리 하나
    cx, cy = int(hf(seed, 81) * (N - 6 * g)) + 2 * g, int(hf(seed, 82) * (N - 8 * g)) + 4 * g
    for j in range(2 * g):
        for i in range(2 * g - j):
            if 0 <= cx + i < N and 0 <= cy + j < N:
                px[cx + i, cy + j] = MORTAR[1]
    return im


def cap_top(N, seed):
    """윗면 = 두꺼운 갓돌 2장(가로). 쿼터뷰라 윗면은 위에서 본 면: 위 모서리 밝음, 앞(아래) 모서리 가장 밝은 테 + 바로 아래 그늘."""
    g = max(1, N // 32)
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    px = im.load()
    split = int(N * (0.42 + 0.2 * hf(seed, 1)))
    top0 = 0
    for y in range(N):
        for x in range(N):
            k = 0 if x < split else 1
            edge_l = (x == 0 or x == split) or (g > 1 and (x == 1 or x == split + 1))
            if edge_l and x in (split, split + 1) and g == 1 and x == split + 1:
                edge_l = False
            if x in range(split, split + g):
                px[x, y] = MORTAR[0]
                continue
            n = vnoise(x, y, 5 * g, seed * 3 + k)
            lv = 3 + (1 if n > 0.7 else (-1 if n < 0.22 else 0)) + (1 if k and hf(seed, 2) > 0.5 else 0)
            if y < top0 + g:
                lv = 3                      # 뒤 모서리(멀리) 그늘
            elif y < top0 + 2 * g:
                lv += 1
            elif y >= N - 2 * g:
                lv = 9 if y < N - g else 2  # 앞 모서리 빛 + 바로 아래 그늘(앞면과 경계)
            elif x in range(split + g, split + 2 * g) or x < g:
                lv += 2
            px[x, y] = STONE[max(0, min(10, lv))]
    # 이끼 아닌 술때: 윗면 오목한 곳 어두운 호박 2~3점
    for i in range(2 + g):
        x, y = int(hf(seed, i, 91) * (N - 4 * g)) + 2 * g, int(hf(seed, i, 92) * (N - 8 * g)) + 3 * g
        for dx in range(g):
            px[x + dx, y] = LIQ[1]
            px[x + dx, y + g] = LIQ[0]
    return im


# ---- 세트 ----------------------------------------------------------------------
FLOOR_SET = [("floor_0", "four", 3, None, ()), ("floor_1", "two_h", 5, None, ()), ("floor_2", "three", 8, None, ()),
             ("floor_3", "one", 11, None, ()), ("floor_4", "two_v", 14, None, ()), ("floor_5", "three_b", 17, None, ())]
STAIN_SET = [("trial_0", "two_h", 21, (0.48, 0.55, 0.28)), ("trial_1", "four", 23, (0.62, 0.4, 0.22)),
             ("trial_2", "three", 27, (0.4, 0.68, 0.3)), ("trial_3", "one", 29, (0.5, 0.5, 0.36))]


def build_set(N):
    tiles = {}
    for name, lay, seed, st, sunk in FLOOR_SET:
        tiles[name] = stone_tile(N, seed, lay, st, sunk)
    for name, lay, seed, st in STAIN_SET:
        tiles[name] = stone_tile(N, seed, lay, st)
    tiles["cover_lower"] = brick_face(N, 41, "lower")
    tiles["cover_lower_b"] = brick_face(N, 47, "lower")
    tiles["cover_upper"] = brick_face(N, 43, "upper")
    tiles["cover_top"] = cap_top(N, 45)
    return tiles


ORDER = ["floor_0", "floor_1", "floor_2", "floor_3", "floor_4", "floor_5", "trial_0", "trial_1", "trial_2", "trial_3",
         "cover_lower", "cover_lower_b", "cover_upper", "cover_top"]


def sheet(tiles, N, cols=8):
    rows = (len(ORDER) + cols - 1) // cols
    im = Image.new("RGBA", (cols * N, rows * N), (0, 0, 0, 0))
    for i, k in enumerate(ORDER):
        im.alpha_composite(tiles[k], ((i % cols) * N, (i // cols) * N))
    return im


def check(tiles):
    cs = set()
    for k, t in tiles.items():
        for c in t.get_flattened_data():
            assert c[3] in (0, 255), (k, "반투명")
            if c[3]:
                cs.add(c[:3])
    return cs


def luma(tiles, keys):
    acc = n = 0
    for k in keys:
        for c in tiles[k].get_flattened_data():
            if c[3]:
                acc += 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
                n += 1
    return acc / max(1, n)


def compare_sheet():
    """전/후 타일 비교(6배) + 무작위 이어붙임 8×5칸(3배) — preview_tiles_before_after.png"""
    import json
    from PIL import ImageDraw, ImageFont
    f = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 20)
    ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
    p = os.path.join(ROOT, "assets/tiles/v2/stage1_brewery")
    sh = Image.open(p + ".png").convert("RGBA")
    meta = json.load(open(p + ".json", encoding="utf-8"))

    def oc(i):
        return sh.crop(((i % 8) * 32, (i // 8) * 32, (i % 8) * 32 + 32, (i // 8) * 32 + 32))
    new32, new64 = build_set(32), build_set(64)
    pairs = [("바닥 0", oc(0), "floor_0"), ("바닥 1", oc(1), "floor_1"), ("바닥 2", oc(2), "floor_2"), ("바닥 3", oc(3), "floor_3"),
             ("술 얼룩 27", oc(27), "trial_0"), ("술 얼룩 28", oc(28), "trial_1"),
             ("담 아랫단 43", oc(43), "cover_lower"), ("담 윗단 44", oc(44), "cover_upper"), ("담 윗면 45", oc(45), "cover_top")]
    cw = 32 * 6
    W = 150 + len(pairs) * (cw + 10)
    H = 50 + 3 * (cw + 34) + 30 + 5 * 32 * 3 + 20
    out = Image.new("RGB", (max(W, 3 * (8 * 96) + 60), H), (16, 16, 20))
    d = ImageDraw.Draw(out)
    d.text((10, 10), "양조 구역 바닥·엄폐 담 전/후 — 6배(32 도트는 6배, 64 도트는 3배 = 같은 화면 크기)", fill=(235, 225, 200), font=f)
    for r, lab in enumerate(("현행 v2 (32)", "보강안 A (32)", "보강안 B (64)")):
        y = 50 + r * (cw + 34)
        d.text((10, y + cw // 2), lab, fill=(232, 184, 88), font=f)
        for c, (name, o, k) in enumerate(pairs):
            x = 150 + c * (cw + 10)
            im = o.resize((cw, cw), Image.NEAREST) if r == 0 else (new32[k].resize((cw, cw), Image.NEAREST) if r == 1 else new64[k].resize((cw, cw), Image.NEAREST))
            out.paste(im.convert("RGB"), (x, y + 26))
            if r == 0:
                d.text((x + 2, y + 2), name, fill=(200, 190, 170), font=f)
    # 무작위 이어붙임
    y0 = 50 + 3 * (cw + 34) + 30
    fl_old = [oc(i) for i in meta["tiles"]["1"]]
    sets = [fl_old, [new32["floor_%d" % i] for i in range(6)], [new64["floor_%d" % i] for i in range(6)]]
    for s_i, fl in enumerate(sets):
        N = fl[0].width
        k = 96 // N
        x0 = 10 + s_i * (8 * 96 + 20)
        for ty in range(5):
            for tx in range(8):
                t = fl[h(tx, ty, 5) % len(fl)]
                if s_i and (tx, ty) in ((5, 1), (2, 3)):
                    t = (new32 if s_i == 1 else new64)["trial_%d" % ((tx + ty) % 4)]
                elif not s_i and (tx, ty) in ((5, 1), (2, 3)):
                    t = oc(27 + (tx + ty) % 4)
                out.paste(t.resize((96, 96), Image.NEAREST).convert("RGB"), (x0 + tx * 96, y0 + ty * 96))
    out.save(os.path.join(HERE, "preview_tiles_before_after.png"))
    print("compare", out.size)


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    compare_sheet()
    for N in (32, 64):
        t = build_set(N)
        cs = check(t)
        sheet(t, N).save(os.path.join(HERE, "out", "brewery60_%d.png" % N))
        print(N, "colors", len(cs), "floor luma %.1f" % luma(t, [k for k in ORDER if k.startswith("floor")]))
