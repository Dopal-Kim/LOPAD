"""61라운드 P3 — 지역별 장애물 벽(앞면 아랫단 5·21·22·63 / 윗단 40·41·42) · 윗면(6) · 처마(47) · 가장자리(48~52) · 공허(7·58·59).

벽 앞면은 64×128(윗단 위·아랫단 아래)로 한 번에 그려 줄눈이 두 칸에 걸쳐 이어지게 한 뒤 자른다.
변형(21·22·63 / 41·42)은 같은 바탕 위에 소품을 얹는다 — 가장자리 줄눈이 같아 어떤 변형끼리 붙어도 이어진다.
tileLights 의 offset(지역 JSON)은 그대로 두고, 불빛 그림을 그 자리에 맞췄다.
"""
import math

from PIL import Image

import tk61
from tk61 import Tile, N, G, A, SL, WD, PL, rgba, lv, hf, vnoise, fbm, block_rows, foot_damp, edge_overlay, lip_overlay
import fk64
import regions64 as R64

FL = [A[22], A[23], A[24], A[25], A[26]]


def small_flame(t, cx, by, w=7, h_=12, seed=1):
    """벽등·횃불 불꽃(자체 발광 23~26, 심 1점)."""
    for y in range(by - h_, by + 1):
        tt = (by - y) / h_
        half = w * 0.5 * math.sin(math.pi * min(1, (tt + 0.15) / 1.1)) * (1 - tt) ** 0.3
        sw = math.sin(tt * 3 + seed) * tt * 1.5
        for x in range(int(cx - half - 1), int(cx + half + 2)):
            d = abs(x + 0.5 - cx - sw) / max(0.6, half)
            if d <= 1:
                v = (1 - d) * (1 - tt * 0.8)
                t.set(x, y, FL[0] if v < 0.15 else FL[1] if v < 0.35 else FL[2] if v < 0.55 else FL[3])
    t.set(cx, by - 2, A[26])


def banner(t, x0, x1, y0, y1, ramp, emblem=True, torn=True, seed=3):
    """걸린 깃발(천 접힘 세로 띠 + 찢긴 끝 + 잔 문양)."""
    w = x1 - x0
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u = (x - x0) / w
            fold = math.sin(u * math.pi * 3 + 0.6)
            q = 2 + (1 if fold > 0.45 else (-1 if fold < -0.55 else 0)) - (1 if (y - y0) > (y1 - y0) * 0.8 else 0)
            if torn and y > y1 - 8:
                cut = y1 - 8 + int(7 * abs(math.sin(x * 0.9 + seed)))
                if y > cut:
                    continue
            t.set(x, y, lv(ramp, q))
        t.set(x0, y, lv(ramp, 4)); t.set(x1, y, lv(ramp, 0))
    for x in range(x0 - 3, x1 + 4):                                      # 깃대(가로)
        t.set(x, y0 - 2, WD[4]); t.set(x, y0 - 1, WD[2])
    if emblem:
        cx, cy = (x0 + x1) // 2, y0 + (y1 - y0) // 3
        for dx in range(-5, 6):
            t.set(cx + dx, cy, A[22])
        for (dx, dy) in ((-4, 1), (4, 1), (-3, 2), (3, 2), (-2, 3), (2, 3), (-1, 4), (1, 4), (0, 5), (0, 6), (0, 7), (0, 8),
                         (-3, 9), (-2, 9), (-1, 9), (0, 9), (1, 9), (2, 9), (3, 9)):
            t.set(cx + dx, cy + dy, A[21] if dy < 5 else A[20])
        for dx in range(-3, 4):
            t.set(cx + dx, cy + 1, A[19])


def bracket_torch(t, cx, fy, wall_ramp=None):
    """쇠 벽걸이 + 짧은 횃대 + 불꽃(불꽃 밑 fy). 벽에 불빛 반사(한 단 밝게)."""
    t.rect(cx - 3, fy + 14, cx + 3, fy + 18, G[3]); t.hline(cx - 3, cx + 3, fy + 14, G[6])
    t.line(cx, fy + 14, cx, fy + 6, G[5]); t.line(cx + 1, fy + 14, cx + 1, fy + 6, G[3])
    t.rect(cx - 3, fy + 1, cx + 3, fy + 6, WD[2]); t.hline(cx - 3, cx + 3, fy + 1, WD[4]); t.rect(cx - 2, fy - 1, cx + 2, fy, A[18])
    small_flame(t, cx, fy - 1, w=9, h_=14, seed=cx)
    if wall_ramp:
        rr = [rgba(r) for r in wall_ramp]
        for y in range(fy - 18, fy + 24):
            for x in range(cx - 16, cx + 17):
                d = math.hypot((x - cx) / 16, (y - fy) / 20)
                c = t.get(x, y)
                if d < 0.9 and c in rr and (x + y) % 3 != 0:
                    t.set(x, y, rr[min(len(rr) - 1, rr.index(c) + (2 if d < 0.45 else 1))])


def top_from(base_im, rim, rim2, drop, drop2, under, under2):
    """윗면 6 → 47(아래 변 꺾임) · 48 e · 49 w · 50 n · 51 ne · 52 nw."""
    out = {6: base_im, 47: lip_overlay(base_im, rim, rim2, under, under2)}
    for idx, side in ((48, "e"), (49, "w"), (50, "n"), (51, "ne"), (52, "nw")):
        out[idx] = edge_overlay(base_im, side, rim, rim2, drop, drop2)
    return out


def split(front):
    return front.crop(0), front.crop(N)


# ====================================================================== 성문(gate) — 큰 회색 마름돌 성벽
GATE_R = [SL[0], G[1], G[2], G[3], G[4], G[5], G[6], G[7], G[8], G[9]]
GATE_EDGE = [3, 17, 9, 25, 14, 30]


def gate_front(var, seed=811):
    t = Tile(N, 2 * N)
    block_rows(t, GATE_R, G[1], [22, 21, 21, 22, 21, 21], 0, seed, var, base=4, edge_cut=GATE_EDGE, wmin=24, wmax=40, mortar2=SL[0])
    foot_damp(t, GATE_R, 2 * N - 12, 2 * N, seed + 3)
    for x in range(N):                                                    # 갓 아래 그늘(윗단 위 2줄)
        t.shift_ramp(x, 0, GATE_R, -2); t.shift_ramp(x, 1, GATE_R, -1)
    return t


def gate_walls():
    out = {}
    base = gate_front(0)
    up, lo = split(base)
    out[40], out[5] = up, lo
    # 21 횃불 벽걸이(tileLights offset (32,18))
    t = gate_front(1); bracket_torch(t, 32, N + 18, GATE_R)
    out[21] = t.crop(N)
    # 22 쇠고리(말 매는 고리 2) + 녹물 자국
    t = gate_front(2)
    for (cx, cy) in ((20, N + 30), (44, N + 30)):
        t.rect(cx - 2, cy - 7, cx + 2, cy - 4, G[4]); t.set(cx - 1, cy - 6, G[8])
        for a in range(28):
            th = a / 28 * 2 * math.pi
            t.set(int(round(cx + 5 * math.cos(th))), int(round(cy + 6 * math.sin(th))), G[8] if math.sin(th) < -0.2 else (G[6] if math.cos(th) < 0 else G[3]))
        for k in range(10):
            t.set(cx + (k % 2), cy + 7 + k, WD[2] if k < 6 else WD[1])
    out[22] = t.crop(N)
    # 63 아치 배수 구멍(쇠창살) — 발치
    t = gate_front(3)
    cx, base_y = 32, 2 * N - 2
    for y in range(base_y - 22, base_y + 1):
        for x in range(cx - 13, cx + 14):
            dx = (x - cx) / 13
            top = base_y - 14 - int(8 * math.sqrt(max(0, 1 - dx * dx)))
            if y >= top:
                t.set(x, y, SL[0] if y > top + 1 else G[1])
    for y in range(base_y - 22, base_y + 1):                              # 아치 돌테
        for x in range(cx - 15, cx + 16):
            dx = (x - cx) / 15
            top = base_y - 14 - int(9 * math.sqrt(max(0, 1 - dx * dx)))
            if top - 2 <= y < top and abs(dx) <= 1:
                t.set(x, y, G[7] if y == top - 2 else G[5])
    for x in range(cx - 11, cx + 12, 4):
        for y in range(base_y - 20, base_y):
            if t.get(x, y)[:3] == SL[0][:3]:
                t.set(x, y, G[5]); t.set(x + 1, y, G[2])
    for x in range(cx - 12, cx + 13):
        t.set(x, base_y - 1, WD[1])
    out[63] = t.crop(N)
    # 41 십자 화살 구멍(돌테 + 안쪽 어둠)
    t = gate_front(4)
    def slit(x0, x1, y0, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                t.set(x, y, SL[0] if x > x0 else SL[1])
        for y in range(y0 - 1, y1 + 2):
            t.set(x0 - 1, y, G[7]); t.set(x1 + 1, y, G[3])
        t.hline(x0 - 1, x1 + 1, y0 - 1, G[8]); t.hline(x0 - 1, x1 + 1, y1 + 1, G[2])
    slit(30, 34, 8, 54)
    slit(22, 42, 28, 32)
    for y in range(9, 54):
        t.set(31, y, SL[1])
    out[41] = t.crop(0)
    # 42 잔 문양 깃발
    t = gate_front(5)
    banner(t, 18, 46, 6, 58, [A[16], A[17], A[18], A[19], A[20]], seed=4)
    out[42] = t.crop(0)
    # 윗면: 큰 판석 2장(중립 회색) — 성벽 위 걷는 길
    top = fk64.flags(820, "three", GATE_R + [G[10]], G[2], G[1], base_lv=(5, 6), cracks=0.0, spec=0.0, pits=0.4, bevel=1, n_big=(0.9, 0.06)).im
    out.update(top_from(top, G[8], G[7], SL[0], G[2], G[3], G[1]))
    return out


GATE_VOID = [SL[0], SL[1]]


# ====================================================================== 황무지(waste) — 흙둑(다진 흙 + 돌 + 뿌리 + 말뚝 울)
EARTH = [WD[0], WD[1], WD[2], WD[3], WD[4], PL[1], PL[2], PL[3]]
GRASS = [WD[1], PL[0], PL[1], PL[2], PL[3]]
STN = [SL[0], G[2], G[3], G[4], PL[0], PL[1], PL[2], PL[3]]


def earth_front(var, seed=611):
    """64×128 흙 벽: 가로 지층(64 주기 잡음) + 박힌 돌 + 뿌리 + 위 풀 처마 + 발치 젖음."""
    t = Tile(N, 2 * N)
    for y in range(2 * N):
        for x in range(N):
            band = vnoise(0, y, 8, seed + 1) * 2 + vnoise(x, y, 16, seed + 2, period=N)
            n = vnoise(x, y, 4, seed + 3, period=N)
            q = 3 + (1 if band > 1.75 else (-1 if band < 0.9 else 0)) + (1 if n > 0.82 else (-1 if n < 0.14 else 0))
            if y % 22 in (0,) and n > 0.3:
                q -= 1                                                    # 다짐 층 경계
            t.set(x, y, lv(EARTH, q))
    # 박힌 돌(공유 + 변형) — 가장자리를 넘지 않게 칸 안쪽에만
    for k in range(3):
        sx = 8 + int(hf(seed, var, k, 1) * 48)
        sy = 10 + int(hf(seed, var, k, 2) * 108)
        rx, ry = 3 + int(hf(seed, var, k, 3) * 4), 2 + int(hf(seed, var, k, 4) * 3)
        for y in range(sy - ry, sy + ry + 1):
            for x in range(sx - rx, sx + rx + 1):
                d = ((x - sx) / rx) ** 2 + ((y - sy) / ry) ** 2
                if d <= 1:
                    q = 4 + (2 if y - sy < -ry * 0.4 else (-1 if y - sy > ry * 0.4 else 0)) - (1 if x - sx > rx * 0.5 else 0)
                    t.set(x, y, lv(STN, q))
        t.hline(sx - rx + 1, sx + rx - 1, sy + ry + 1, WD[0])
    # 뿌리(위에서 아래로 늘어진 가는 선)
    for k in range(3):
        x = 6 + int(hf(seed, var, k, 7) * 52)
        y = 6 + int(hf(seed, var, k, 8) * 30)
        for j in range(14 + int(hf(seed, var, k, 9) * 18)):
            t.set(x, y + j, WD[0] if j % 5 else WD[1]); t.set(x + 1, y + j, WD[3])
            if hf(seed, var, k, j) < 0.3:
                x += 1 if hf(seed, k, j, 2) < 0.5 else -1
    # 위 풀 처마(윗단 꼭대기 8 도트) — 64 주기
    for x in range(N):
        hh = 4 + int(vnoise(x, 0, 4, seed + 5, period=N) * 5)
        for y in range(0, hh):
            t.set(x, y, lv(GRASS, 3 if y < 2 else 2))
        t.set(x, hh, GRASS[0]); t.set(x, hh + 1, WD[0])
        if (x * 7) % 5 == 0:
            for j in range(3):
                t.set(x, hh + 1 + j, GRASS[1])                           # 늘어진 풀잎
    foot_damp(t, EARTH, 2 * N - 14, 2 * N, seed + 4)
    for x in range(N):
        t.set(x, 2 * N - 1, WD[0])
    return t


def stake_fence(t, y0, y1, seed, sharp_top=False):
    """세로 말뚝 울(통나무 5) — 새끼줄 2줄. 64 주기로 말뚝 간격 고정."""
    for i, x0 in enumerate((1, 14, 27, 40, 53)):
        w = 11
        top = y0 + (int(hf(seed, i) * 4) if sharp_top else 0)
        for y in range(top, y1):
            for x in range(x0, x0 + w):
                u = (x - x0) / (w - 1)
                q = 3 + (1 if u < 0.25 else 0) - (1 if u > 0.75 else 0) - (1 if (y + i * 5) % 17 == 0 else 0)
                t.set(x, y, lv([WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]], q))
            t.set(x0 + w - 1, y, WD[0])
        if sharp_top:
            for k in range(6):                                            # 깎은 끝
                for x in range(x0 + k, x0 + w - k):
                    t.set(x, top - 6 + k, WD[4] if x < x0 + w // 2 else WD[2])
    for ry in ((y0 + y1) // 3, (y0 + y1) * 2 // 3):
        for x in range(N):
            t.set(x, ry, PL[2] if x % 3 else PL[1]); t.set(x, ry + 1, WD[1])


def waste_walls():
    out = {}
    up, lo = split(earth_front(0))
    out[40], out[5] = up, lo
    # 21 꽂힌 횃불(tileLights offset (32,22))
    t = earth_front(1)
    for k in range(26):
        x, y = 34 - k // 5, N + 24 + k
        t.set(x, y, WD[4]); t.set(x + 1, y, WD[2]); t.set(x - 1, y, WD[3])
    t.rect(29, N + 18, 35, N + 24, WD[1]); t.hline(29, 35, N + 18, A[18])
    small_flame(t, 32, N + 22, w=10, h_=16, seed=2)
    out[21] = t.crop(N)
    # 22 말뚝 울(아랫단) / 41 말뚝 울(윗단, 뾰족한 끝)
    t = earth_front(2)
    stake_fence(t, N + 0, 2 * N - 2, 3)
    stake_fence(t, 8, N, 3, sharp_top=True)
    out[22] = t.crop(N)
    out[41] = t.crop(0)
    # 63 박힌 해골 + 부러진 칼
    t = earth_front(3)
    cx, cy = 22, N + 34
    for y in range(cy - 8, cy + 8):
        for x in range(cx - 8, cx + 8):
            d = ((x - cx) / 8) ** 2 + ((y - cy) / 7.5) ** 2
            if d <= 1:
                t.set(x, y, lv([PL[1], PL[2], PL[3], PL[4], G[12]], 3 - (1 if x > cx + 3 else 0) + (1 if y < cy - 3 else 0)))
    for (ex, ey) in ((cx - 4, cy), (cx + 3, cy)):
        t.rect(ex - 1, ey - 1, ex + 1, ey + 2, SL[0])
    t.rect(cx - 1, cy + 4, cx, cy + 5, SL[1])
    for x in range(cx - 4, cx + 5, 2):
        t.set(x, cy + 7, SL[0])
    for k in range(30):                                                   # 칼날(비스듬히, 녹)
        x, y = 34 + k, N + 22 + k // 3
        t.set(x, y, G[9] if k % 7 else WD[3]); t.set(x, y + 1, G[6]); t.set(x, y + 2, G[3])
    t.rect(30, N + 19, 34, N + 26, WD[2]); t.hline(29, 35, N + 22, G[7])
    out[63] = t.crop(N)
    # 42 찢긴 깃발(장대에 꽂혀 늘어짐)
    t = earth_front(4)
    for y in range(0, N):
        t.set(14, y, WD[4]); t.set(15, y, WD[2])
    for y in range(6, 46):
        for x in range(16, 16 + max(4, 26 - (y - 6) // 2)):
            if y > 38 and (x * 3 + y) % 5 < 2:
                continue
            q = 2 + (1 if (x // 4) % 2 == 0 else 0) - (1 if y > 30 else 0)
            t.set(x, y, lv([SL[0], SL[1], A[16], A[17], A[18]], q))
    for (dx, dy) in ((0, 0), (1, 1), (2, 2), (-1, 1), (-2, 2), (0, 3), (0, 4)):
        t.set(26 + dx, 16 + dy, A[20])
    out[42] = t.crop(0)
    # 윗면: 둑 위 흙(바닥보다 따뜻한 갈색) + 흙덩이 + 마른 풀 — fk64.dirt(이음 보장)
    BANK = {"base": WD[3], "cool": PL[0], "warm": WD[2], "light": PL[1], "dark": WD[2], "darker": WD[1]}
    top_im = fk64.dirt(6601, 6602, BANK, pebbles=3, cracks=0, grass=2, peb_ramp=R64.PEB, grass_cols=[WD[2], PL[1], PL[2], PL[3]])
    class _T: pass
    top = _T(); top.im = top_im
    out.update(top_from(top.im, PL[2], PL[1], WD[0], WD[1], WD[1], WD[0]))
    return out


# ====================================================================== 외곽 거리(outer) — 목조 회벽 집 + 돌 기단 / 지붕
PLASTER = [SL[1], PL[0], PL[1], PL[2], PL[3], PL[4]]
TIMBER = [WD[0], WD[1], WD[2], WD[3], WD[4]]
PLINTH = [SL[0], WD[1], WD[2], PL[0], PL[1], PL[2], PL[3]]
ROOF = [SL[0], SL[1], SL[2], SL[3], SL[4], SL[5], SL[6]]


def plaster_front(var, seed=711):
    t = Tile(N, 2 * N)
    for y in range(2 * N):
        for x in range(N):
            n = vnoise(x, y, 8, seed, period=N)
            n2 = vnoise(x, y, 4, seed + 1, period=N)
            q = 3 + (1 if n > 0.72 else (-1 if n < 0.2 else 0)) - (1 if n2 < 0.1 else 0)
            t.set(x, y, lv(PLASTER, q))
    # 회벽 벗겨진 자리(안쪽 벽돌 보임)
    if var in (0, 3):
        cx, cy = 18 + var * 6, 30 + var * 12
        for y in range(cy - 5, cy + 6):
            for x in range(cx - 8, cx + 9):
                if ((x - cx) / 8) ** 2 + ((y - cy) / 5) ** 2 <= 1:
                    t.set(x, y, WD[2] if (y % 4 == 0 or (x + (y // 4) * 4) % 9 == 0) else WD[3])
    # 기둥(가장자리 x=0..5 — 이웃 칸과 이어짐) + 띠 보(윗단 위 · 윗단/아랫단 사이)
    for y in range(2 * N):
        for x in range(0, 6):
            t.set(x, y, lv(TIMBER, 3 if x < 2 else (2 if x < 4 else 1)))
        t.set(6, y, PLASTER[0])
    for (y0, h_) in ((0, 7), (N - 4, 8)):
        for y in range(y0, y0 + h_):
            for x in range(N):
                ly = y - y0
                t.set(x, y, lv(TIMBER, 4 if ly == 0 else (3 if ly < 3 else (2 if ly < h_ - 1 else 0))))
        for x in range(4, N, 13):
            t.set(x, y0 + 3, G[7])
    # 돌 기단(아랫단 바닥 18 도트)
    block_rows(t, PLINTH, WD[0], [9, 9], 2 * N - 18, seed + 5, 0, base=3, edge_cut=[5, 21], wmin=14, wmax=22, chisel=False)
    for x in range(N):
        t.set(x, 2 * N - 19, TIMBER[0])
    return t


def brace(t, x0, y0, x1, y1):
    n = max(abs(x1 - x0), abs(y1 - y0))
    for k in range(n + 1):
        x = int(round(x0 + (x1 - x0) * k / n)); y = int(round(y0 + (y1 - y0) * k / n))
        for d in range(-2, 3):
            t.set(x + d, y, lv(TIMBER, 3 if d < 0 else (2 if d < 2 else 0)))


def window(t, x0, y0, w, h_, lit, shutters=False):
    t.rect(x0 - 3, y0 - 3, x0 + w + 2, y0 + h_ + 2, TIMBER[1])
    t.hline(x0 - 3, x0 + w + 2, y0 - 3, TIMBER[3]); t.hline(x0 - 4, x0 + w + 3, y0 + h_ + 3, TIMBER[4])
    t.hline(x0 - 4, x0 + w + 3, y0 + h_ + 4, TIMBER[0])
    for y in range(y0, y0 + h_):
        for x in range(x0, x0 + w):
            if lit:
                d = math.hypot((x - x0 - w / 2) / (w / 2), (y - y0 - h_ / 2) / (h_ / 2))
                t.set(x, y, A[25] if d < 0.45 else (A[24] if d < 0.8 else A[23]))
            else:
                t.set(x, y, SL[1] if (x + y) % 9 else SL[2])
    t.vline(x0 + w // 2, y0, y0 + h_ - 1, TIMBER[1]); t.hline(x0, x0 + w - 1, y0 + h_ // 2, TIMBER[1])
    if shutters:
        for (sx, sgn) in ((x0, 1), (x0 + w // 2, -1)):
            for x in range(sx, sx + w // 2):
                for y in range(y0, y0 + h_):
                    t.set(x, y, lv(TIMBER, 2 + (1 if (x - sx) % 4 == 0 else 0)))
        t.vline(x0 + w // 2, y0, y0 + h_ - 1, TIMBER[0])


def outer_walls():
    out = {}
    t = plaster_front(0)
    brace(t, 8, 8, 60, N - 6)                                             # 윗단 X 버팀
    brace(t, 8, N - 6, 60, 8)
    brace(t, 8, N + 6, 46, 2 * N - 22)                                    # 아랫단 사선 버팀
    out[40], out[5] = split(t)
    # 21 불 켜진 창(아랫단) — tileLights offset (32,52)
    t = plaster_front(1); window(t, 20, N + 14, 24, 22, True)
    for y in range(N + 40, N + 46):                                       # 창턱 아래 불빛 번짐(벽 한 단 밝게)
        for x in range(18, 47):
            t.shift_ramp(x, y, PLASTER, 1)
    out[21] = t.crop(N)
    # 22 문(틈 사이 불빛 — tileLights offset (52,60))
    t = plaster_front(2)
    dx0, dx1, dy0 = 18, 50, N + 8
    for y in range(dy0, 2 * N - 1):
        for x in range(dx0, dx1 + 1):
            lx = (x - dx0) % 8
            t.set(x, y, lv(TIMBER, 2 + (1 if lx == 0 else 0) - (1 if lx == 7 else 0)))
    for x in range(dx0 - 3, dx1 + 4):
        t.set(x, dy0 - 3, TIMBER[4]); t.set(x, dy0 - 2, TIMBER[3]); t.set(x, dy0 - 1, TIMBER[1])
    for y in range(dy0 - 3, 2 * N - 1):
        t.set(dx0 - 3, y, TIMBER[3]); t.set(dx0 - 2, y, TIMBER[2]); t.set(dx1 + 2, y, TIMBER[1]); t.set(dx1 + 3, y, TIMBER[0])
    for y in (dy0 + 10, 2 * N - 12):
        t.hline(dx0, dx1, y, G[5]); t.hline(dx0, dx1, y + 1, G[3])
    for y in range(dy0 + 2, 2 * N - 2):                                   # 문틈 빛(오른쪽 세로)
        t.set(dx1 + 1, y, A[23] if y > 2 * N - 20 else A[21])
    t.hline(dx0, dx1 + 1, 2 * N - 2, A[23]); t.set(dx1 + 1, 2 * N - 3, A[24])
    t.rect(dx1 - 7, N + 34, dx1 - 5, N + 37, G[7])
    out[22] = t.crop(N)
    # 63 덧문 닫힌 창(어두움)
    t = plaster_front(3); window(t, 20, N + 14, 24, 22, False, shutters=True)
    out[63] = t.crop(N)
    # 41 어두운 창(윗단)
    t = plaster_front(4); window(t, 22, 16, 20, 24, False)
    out[41] = t.crop(0)
    # 42 걸린 간판(쇠 팔 + 잔 그림 판)
    t = plaster_front(5)
    brace(t, 8, 8, 60, N - 6)
    for x in range(12, 52):
        t.set(x, 14, G[6]); t.set(x, 15, G[3])
    t.line(14, 15, 22, 22, G[5])
    for y in range(22, 50):
        for x in range(20, 46):
            t.set(x, y, lv(TIMBER, 3 if y < 24 else 2))
    t.rect(22, 24, 43, 47, TIMBER[1])
    for (dx, dy) in [(d, 0) for d in range(-6, 7)] + [(-5, 1), (5, 1), (-4, 2), (4, 2), (-3, 3), (3, 3), (-2, 4), (2, 4), (-1, 5), (1, 5), (0, 6), (0, 7), (0, 8), (0, 9), (-4, 10), (-3, 10), (-2, 10), (-1, 10), (0, 10), (1, 10), (2, 10), (3, 10), (4, 10)]:
        t.set(33 + dx, 29 + dy, A[21] if dy < 6 else A[20])
    for x in (24, 41):
        t.vline(x, 15, 22, G[5])
    out[42] = t.crop(0)
    # 윗면 = 지붕(널빤지 기와 — 아래로 겹쳐 내려오는 줄, 64 주기)
    top = Tile()
    for y in range(N):
        row = y // 10
        off = (row % 2) * 8
        ly = y % 10
        for x in range(N):
            X = (x + off) % N
            sx = X % 16
            q = 3 + (1 if ly < 2 else 0) - (2 if ly >= 8 else (1 if ly >= 6 else 0)) - (1 if sx == 15 else 0)
            if hf(731, row, X // 16) > 0.7:
                q += 1
            if vnoise(x, y, 4, 733, period=N) < 0.12:
                q -= 1
            top.set(x, y, lv(ROOF, q))
    out.update(top_from(top.im, TIMBER[4], TIMBER[3], TIMBER[0], TIMBER[1], TIMBER[1], TIMBER[0]))
    return out


# ====================================================================== 양조 구역(brewery) — 그을린 벽돌
BRK = [SL[0], WD[0], WD[1], WD[2], A[17], WD[3], A[18], WD[4], PL[2]]
BRK_MORTAR = SL[1]
COPPER = [A[16], A[17], A[18], A[19], A[20], A[21]]


def brick_front(var, seed=911):
    t = Tile(N, 2 * N)
    block_rows(t, BRK, BRK_MORTAR, [12] * 10 + [8], 0, seed, var, base=3,
               edge_cut=[(0 if r % 2 == 0 else 14) for r in range(11)], wmin=26, wmax=30, chisel=False, chip=0)
    # 그을음(위로 갈수록 짙음 — 화구 연기)
    rr = [rgba(r) for r in BRK]
    for y in range(2 * N):
        for x in range(N):
            c = t.get(x, y)
            if c in rr and vnoise(x, y, 8, seed + 7, period=N) < 0.42 - y / (2 * N) * 0.3:
                t.set(x, y, rr[max(1, rr.index(c) - 1)])
    foot_damp(t, BRK, 2 * N - 12, 2 * N, seed + 3)
    for x in range(N):
        t.set(x, 0, SL[0]); t.set(x, 1, BRK[1])
    return t


def pipe_h(t, y, x0=6, x1=N - 7, r=4):
    for x in range(x0, x1 + 1):
        for d in range(-r, r + 1):
            q = 3 + (2 if d < -r + 2 else (1 if d < 0 else (-1 if d > r - 2 else 0)))
            t.set(x, y + d, lv(COPPER, q))
    for x in (x0 + 12, x1 - 15):                                           # 쇠 꺾쇠
        t.rect(x, y - r - 2, x + 3, y + r + 2, G[3]); t.vline(x, y - r - 2, y + r + 2, G[6])
    for (fx, sgn) in ((x0, -1), (x1, 1)):                                  # 벽으로 꺾여 들어가는 이음(플랜지)
        t.rect(fx - 1 if sgn < 0 else fx - 1, y - r - 3, fx + 1, y + r + 3, G[4]); t.vline(fx - 1, y - r - 3, y + r + 3, G[7])
        for d in range(-r + 1, r):
            t.set(fx + sgn * 2, y + d, COPPER[0]); t.set(fx + sgn * 3, y + d, SL[0])


def brewery_walls():
    out = {}
    out[40], out[5] = split(brick_front(0))
    # 21 화구(아치 + 타는 불) — tileLights offset (32,40)
    t = brick_front(1)
    cx, by = 32, 2 * N - 6
    for y in range(by - 34, by + 1):
        for x in range(cx - 17, cx + 18):
            dx = (x - cx) / 17
            top = by - 22 - int(12 * math.sqrt(max(0, 1 - dx * dx)))
            if top - 3 <= y < top:
                t.set(x, y, G[5] if y == top - 3 else G[3])               # 쇠 아치 테
            elif y >= top:
                t.set(x, y, SL[0])
    for y in range(by - 30, by + 1):                                       # 안쪽 불빛 그러데이션
        for x in range(cx - 14, cx + 15):
            if t.get(x, y)[:3] == SL[0][:3]:
                d = math.hypot((x - cx) / 14, (y - by + 4) / 20)
                if d < 1:
                    t.set(x, y, A[19] if d > 0.75 else A[21])
    for k, sx in enumerate((cx - 7, cx, cx + 6)):
        small_flame(t, sx, by - 3, w=9, h_=14 + (4 if k == 1 else 0), seed=k)
    for x in range(cx - 14, cx + 15):                                      # 숯
        t.set(x, by - 1, A[20] if x % 3 else A[24]); t.set(x, by, A[18])
    t.rect(cx - 19, by + 1, cx + 19, by + 5, G[3]); t.hline(cx - 19, cx + 19, by + 1, G[6])
    out[21] = t.crop(N)
    # 22 세로 구리관 + 밸브 바퀴
    t = brick_front(2)
    for y in range(0, 2 * N):
        for d in range(-4, 5):
            q = 3 + (2 if d < -2 else (1 if d < 0 else (-1 if d > 2 else 0)))
            t.set(40 + d, y, lv(COPPER, q))
    for y in (N + 4, 2 * N - 14):
        t.rect(34, y, 46, y + 3, G[3]); t.hline(34, 46, y, G[6])
    cx, cy = 40, N + 30
    for a in range(48):
        th = a / 48 * 2 * math.pi
        for r in (8, 9):
            t.set(int(round(cx + r * math.cos(th))), int(round(cy + r * 0.9 * math.sin(th))), G[7] if math.sin(th) < 0 else G[4])
    t.line(cx - 8, cy, cx + 8, cy, G[5]); t.line(cx, cy - 8, cx, cy + 8, G[5]); t.rect(cx - 1, cy - 1, cx + 1, cy + 1, G[8])
    out[22] = t.crop(N)
    out[41] = t.crop(0)                                                    # 윗단: 관이 이어져 올라감(41)
    # 63 발치 환기 창살(쇠틀 + 가로 살)
    t = brick_front(3)
    x0, x1, y0, y1 = 16, 48, 2 * N - 26, 2 * N - 6
    t.rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2, G[4]); t.hline(x0 - 2, x1 + 2, y0 - 2, G[7]); t.hline(x0 - 2, x1 + 2, y1 + 2, G[2])
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            t.set(x, y, SL[0] if (y - y0) % 4 else G[5])
    for x in range(x0, x1 + 1, 8):
        t.vline(x, y0, y1, G[3])
    for y in range(y0 + 1, y1, 4):                                         # 안쪽 희미한 호박(저장고 불)
        t.set(x0 + 10, y, A[18]); t.set(x0 + 20, y + 1, A[17])
    out[63] = t.crop(N)
    # 42 가로 구리관(윗단)
    t = brick_front(4); pipe_h(t, 34)
    out[42] = t.crop(0)
    # 윗면: 벽 위 회반죽 갓돌(그을음·술 얼룩) — 벽돌 앞면과 다른 재질로 '위'가 읽히게
    class _T: pass
    top = _T()
    top.im = fk64.flags(940, "three", R64.WET, SL[1], SL[0], base_lv=(2, 3), cracks=0.1, spec=0.3, pits=0.6, bevel=1, n_big=(0.88, 0.08)).im
    tp = top.im.load()
    for k in range(5):                                                     # 술 얼룩 점
        x, y = 8 + int(hf(941, k) * 46), 8 + int(hf(942, k) * 46)
        tp[x, y] = rgba(A[17]); tp[x + 1, y] = rgba(A[17]); tp[x, y + 1] = rgba(A[16])
    out.update(top_from(top.im, R64.WET[8], R64.WET[7], SL[0], SL[1], SL[2], SL[0]))
    return out


# ====================================================================== 연회장(hall) — 광택 돌 판벽 + 휘장
POL = R64.POLISH
CURTAIN = [A[16], SL[0], A[17], WD[1], A[18], WD[2], A[19]]


def panel_front(var, seed=1011):
    """윗단 = 매끈한 큰 돌(가로 2단) + 처마 몰딩 / 아랫단 = 굽도리(징두리) 판: 테 몰딩 + 걸레받이."""
    t = Tile(N, 2 * N)
    block_rows(t, POL, G[1], [32, 32], 0, seed, var, base=6, edge_cut=[0, 32], wmin=60, wmax=64, chisel=False, chip=0,
               x_period=N)
    for y in range(N, 2 * N):
        for x in range(N):
            n = vnoise(x, y, 8, seed + 3, period=N)
            t.set(x, y, lv(POL, 5 + (1 if n > 0.75 else (-1 if n < 0.2 else 0))))
    for y in range(0, 6):                                                  # 위 쇠시리(코니스)
        for x in range(N):
            t.set(x, y, lv(POL, (9, 10, 7, 5, 3, 2)[y]))
    for y in range(N - 6, N + 2):                                          # 판벽 위 갓띠(의자 높이 몰딩)
        for x in range(N):
            t.set(x, y, lv(POL, (3, 9, 10, 8, 6, 5, 3, 1)[y - (N - 6)]))
    # 판(테 몰딩 사각 — 칸 안쪽, 가장자리 2 도트는 공유 기둥)
    px0, px1, py0, py1 = 8, 55, N + 8, 2 * N - 14
    for y in range(py0, py1 + 1):
        for x in range(px0, px1 + 1):
            if y in (py0, py0 + 1) or x in (px0, px0 + 1):
                t.set(x, y, POL[3])
            elif y in (py1, py1 - 1) or x in (px1, px1 - 1):
                t.set(x, y, POL[9])
            elif y in (py0 + 2,) or x == px0 + 2:
                t.set(x, y, POL[8])
    for x in (0, 1, 62, 63):                                               # 판 사이 기둥(이웃과 이어짐)
        for y in range(N + 2, 2 * N - 10):
            t.set(x, y, POL[7] if x in (1, 62) else POL[3])
    for y in range(2 * N - 10, 2 * N):                                     # 걸레받이
        for x in range(N):
            t.set(x, y, lv(POL, (9, 7, 6, 6, 5, 5, 4, 3, 2, 1)[y - (2 * N - 10)]))
    return t


def candle_sconce(t, cx, fy):
    """촛대 벽등(놋쇠 받침 + 초 + 불꽃, 불꽃 밑 fy) + 벽 불빛."""
    rr = [rgba(r) for r in POL]
    for y in range(fy - 10, fy + 30):
        for x in range(cx - 14, cx + 15):
            d = math.hypot((x - cx) / 14, (y - fy) / 22)
            c = t.get(x, y)
            if d < 0.95 and c in rr:
                t.set(x, y, rr[min(len(rr) - 1, rr.index(c) + (2 if d < 0.5 else 1))])
    t.rect(cx - 2, fy + 1, cx + 2, fy + 16, PL[4]); t.vline(cx - 2, fy + 1, fy + 16, G[13]); t.vline(cx + 2, fy + 1, fy + 16, PL[2])
    t.rect(cx - 6, fy + 17, cx + 6, fy + 19, A[20]); t.hline(cx - 6, cx + 6, fy + 17, A[22])
    t.line(cx, fy + 20, cx, fy + 26, A[19]); t.rect(cx - 3, fy + 26, cx + 3, fy + 28, A[19])
    small_flame(t, cx, fy, w=6, h_=10, seed=cx)


def hall_walls():
    out = {}
    out[40], out[5] = split(panel_front(0))
    # 21 촛대 벽등(tileLights offset (32,10)) — 아랫단 위쪽
    t = panel_front(1); candle_sconce(t, 32, N + 10)
    out[21] = t.crop(N)
    # 22 판 가운데 잔 문양 부조
    t = panel_front(2)
    cx, cy = 32, N + 26
    for (dx, dy) in [(d, 0) for d in range(-7, 8)] + [(-6, 1), (6, 1), (-5, 2), (5, 2), (-4, 3), (4, 3), (-3, 4), (3, 4), (-2, 5), (2, 5), (-1, 6), (1, 6), (0, 7), (0, 8), (0, 9), (0, 10), (-5, 11), (-4, 11), (-3, 11), (-2, 11), (-1, 11), (0, 11), (1, 11), (2, 11), (3, 11), (4, 11), (5, 11)]:
        t.set(cx + dx, cy + dy, POL[3]); t.set(cx + dx + 1, cy + dy + 1, POL[10])
    out[22] = t.crop(N)
    # 63 벽감(아치 + 안쪽 어둠 + 금잔)
    t = panel_front(3)
    cx, by = 32, 2 * N - 11
    for y in range(by - 40, by + 1):
        for x in range(cx - 14, cx + 15):
            dx = (x - cx) / 14
            top = by - 28 - int(12 * math.sqrt(max(0, 1 - dx * dx)))
            if top - 3 <= y < top:
                t.set(x, y, POL[9] if y == top - 3 else POL[7])
            elif y >= top:
                t.set(x, y, SL[0] if y < by - 4 else POL[4])
    structs_goblet(t, cx, by - 5)
    out[63] = t.crop(N)
    # 41 휘장(윗단 — 주름 세로 띠, 아래가 묶여 처짐)
    t = panel_front(4)
    for y in range(6, N):
        sag = int(6 * math.sin(math.pi * min(1, y / N)))
        for x in range(8 + sag // 2, 56 - sag // 2):
            u = (x - 8) / 48
            f = math.sin(u * math.pi * 6)
            q = 3 + (2 if f > 0.6 else (1 if f > 0.1 else (-1 if f < -0.5 else 0))) - (1 if y > 50 else 0)
            t.set(x, y, lv(CURTAIN, q))
    for x in range(6, 58):
        t.set(x, 5, A[21]); t.set(x, 6, A[19]); t.set(x, 4, G[7])
    for x in range(8, 56, 6):
        t.set(x, 7, A[22])
    out[41] = t.crop(0)
    # 42 잔 문장 깃발
    t = panel_front(5)
    banner(t, 20, 44, 8, 60, CURTAIN[2:] + [A[20]], seed=7)
    out[42] = t.crop(0)
    top = fk64.flags(1020, "three_b", POL, G[1], G[0], base_lv=(6, 7), cracks=0.0, spec=0.6, pits=0.2, bevel=1, n_big=(0.9, 0.06)).im
    out.update(top_from(top, POL[10], POL[9], G[1], POL[2], POL[3], G[1]))
    return out


def structs_goblet(t, cx, by):
    """벽감 속 작은 금잔(층 램프, 비발광)."""
    for y in range(by - 14, by - 6):
        half = 5 - (y - (by - 14)) // 2
        for x in range(cx - half, cx + half + 1):
            t.set(x, y, A[21] if x < cx else A[19])
    t.vline(cx, by - 6, by - 2, A[19]); t.hline(cx - 4, cx + 4, by - 1, A[20]); t.hline(cx - 5, cx + 5, by - 14, A[22])


# ====================================================================== 공허(7·58·59) — 지역마다
def voids(rid):
    out = {}
    base = {"waste": [WD[0], SL[0]], "gate": [SL[0], SL[1]], "outer": [SL[0], SL[1]], "brewery": [SL[0], WD[0]], "hall": [SL[0], G[1]]}[rid]
    t7 = Tile(fill=base[0])
    for k in range(10):                                                   # 어둠 속 희미한 덩어리(2~4 도트)
        x, y = 4 + int(hf(71, len(rid), k, 1) * 54), 4 + int(hf(71, len(rid), k, 2) * 54)
        w_, h_ = 2 + int(hf(71, k, 3) * 3), 1 + int(hf(71, k, 4) * 2)
        t7.rect(x, y, x + w_, y + h_, base[1])
    t58 = Tile(); t58.im.paste(t7.im, (0, 0)); t58.p = t58.im.load()
    if rid == "outer":                                                    # 먼 지붕 줄 + 굴뚝 끝
        for y in range(N):
            for x in range(N):
                if y % 10 == 9:
                    t7.set(x, y, SL[0]); t58.set(x, y, SL[0])
                elif y % 10 == 0:
                    t7.set(x, y, SL[2]); t58.set(x, y, SL[2])
        t58.rect(24, 18, 40, 44, WD[1]); t58.rect(26, 18, 38, 22, WD[2]); t58.rect(28, 20, 36, 22, SL[0])
        t58.set(31, 16, PL[1]); t58.set(32, 13, PL[0]); t58.set(31, 10, PL[0])
    elif rid == "waste":                                                  # 마른 가시덤불 그림자
        for k in range(30):
            x, y = int(hf(581, k) * 60), int(hf(582, k) * 60)
            t58.line(x, y, x + int(hf(583, k) * 8) - 4, y - 5, WD[1])
    elif rid == "gate":                                                   # 먼 성벽 화톳불 한 점
        t58.set(34, 30, A[19]); t58.set(35, 30, A[18])
    elif rid == "brewery":                                                # 깊은 곳 화구 잔광
        for x in range(26, 38):
            t58.set(x, 40, A[17]); t58.set(x, 41, A[16])
    elif rid == "hall":                                                   # 깊은 바닥 줄(검은 돌판)
        for y in range(40, 64, 6):
            for x in range(N):
                t58.set(x, y, G[2])
    t59 = Tile(fill=SL[0])
    out[7], out[58], out[59] = t7.im, t58.im, t59.im
    return out


# ====================================================================== 데칼·수로(지역 고유 칸)
def ragged_blob(w, h_, cx, cy, rx, ry, seed, lumps=7):
    m = [[0.0] * w for _ in range(h_)]
    pts = [(cx, cy, rx, ry)]
    for k in range(lumps):
        a = hf(seed, k, 1) * 2 * math.pi
        d = 0.45 + 0.4 * hf(seed, k, 2)
        pts.append((cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d, rx * (0.3 + 0.3 * hf(seed, k, 3)), ry * (0.3 + 0.3 * hf(seed, k, 4))))
    for y in range(h_):
        for x in range(w):
            v = 0.0
            for (px_, py_, a, b) in pts:
                d = ((x - px_) / a) ** 2 + ((y - py_) / b) ** 2
                v = max(v, 1 - d)
            v += (vnoise(x, y, 4, seed + 9) - 0.5) * 0.35
            m[y][x] = v
    return m


def scorch(w=128, h_=128, seed=641):
    t = Tile(w, h_)
    m = ragged_blob(w, h_, w / 2, h_ / 2, w * 0.42, h_ * 0.36, seed)
    for y in range(h_):
        for x in range(w):
            v = m[y][x]
            if v > 0.62:
                t.set(x, y, SL[0] if vnoise(x, y, 4, seed + 2) > 0.3 else G[2])
            elif v > 0.4:
                t.set(x, y, G[2] if vnoise(x, y, 4, seed + 3) > 0.45 else WD[1])
            elif v > 0.22 and (x * 3 + y * 5) % 7 < 3:
                t.set(x, y, WD[1])                                           # 가장자리 흩뿌린 재(점)
    for k in range(12):                                                    # 숯 조각 + 식은 불씨
        x, y = int(w * 0.25 + hf(seed, k, 7) * w * 0.5), int(h_ * 0.3 + hf(seed, k, 8) * h_ * 0.4)
        t.rect(x, y, x + 2, y + 1, G[1]); t.set(x, y, G[4])
        if k % 4 == 0:
            t.set(x + 1, y + 1, A[17])
    return t.im


def ruts(w, h_, seed, dark=(WD[0], WD[1]), lit=PL[1], ys=(20, 42), water=None):
    t = Tile(w, h_)
    for y0 in ys:
        for x in range(w):
            fade = min(1.0, x / 26, (w - 1 - x) / 26)
            wob = int(round(1.5 * math.sin(x * 0.07 + y0)))
            depth = 5 if fade > 0.6 else (3 if fade > 0.25 else 1)
            for d in range(depth):
                yy = y0 + wob + d
                if water and d in (1, 2) and fade > 0.7 and vnoise(x, yy, 8, seed + y0) > 0.5:
                    t.set(x, yy, water[2] if d == 1 else water[1])
                else:
                    t.set(x, yy, dark[0] if d > 0 and d < depth - 1 else dark[1])
            if fade > 0.3:
                t.set(x, y0 + wob - 1, lit)                                  # 밀려 올라온 둑(빛)
                t.set(x, y0 + wob + depth, lit if x % 3 else dark[1])
    return t.im


def puddles(w, h_, seed, ramp):
    t = Tile(w, h_)
    for (cx, cy, rx, ry, sd) in ((34, 30, 22, 10, 1), (92, 38, 26, 12, 2)):
        m = ragged_blob(w, h_, cx, cy, rx, ry, seed + sd, lumps=4)
        for y in range(h_):
            for x in range(w):
                v = m[y][x]
                if v > 0.25:
                    up = m[y - 1][x] <= 0.25 if y > 0 else True
                    q = 0 if up else (3 if v > 0.75 else (2 if v > 0.5 else 1))
                    t.set(x, y, ramp[q])
        for k in range(3):                                                   # 반사 줄(문빛)
            yy = cy - 3 + k * 3
            t.hline(cx - rx // 2 + k * 3, cx - rx // 2 + k * 3 + rx // 2, yy, ramp[4] if k == 1 else ramp[3])
        t.set(cx - 2, cy - 2, ramp[5])
    return t.im


def liquor_trail(w, h_, seed, ramp=(A[16], A[17], A[18], A[19], A[20], A[22])):
    t = Tile(w, h_)
    for x in range(w):
        fade = min(1.0, x / 30, (w - 1 - x) / 20)
        if fade <= 0:
            continue
        cy = h_ / 2 + 8 * math.sin(x * 0.045 + seed)
        half = 3 + 6 * fade * (0.6 + 0.4 * vnoise(x, 0, 8, seed))
        for y in range(int(cy - half), int(cy + half) + 1):
            d = abs(y - cy) / half
            t.set(x, y, ramp[0] if d > 0.8 else (ramp[2] if d < 0.3 else ramp[1]))
        if x % 9 == 0 and fade > 0.6:
            t.set(x, int(cy - half / 3), ramp[5])
    for k in range(6):                                                     # 튄 방울
        x, y = int(hf(seed, k, 1) * w), int(hf(seed, k, 2) * h_)
        t.rect(x, y, x + 1, y + 1, ramp[1])
    return t.im


CANAL_DARK = [SL[0], A[16], A[17], A[17], A[18], A[19], A[20]]
CANAL_LIT = [A[16], A[17], A[18], A[19], A[20], A[21], A[23]]
CURB = [SL[0], SL[1], G[3], G[4], G[5], G[6], G[7]]


def canal_frame(k, lit):
    """술 수로 1칸(가로로 이어짐): 위 돌턱(빛) · 술(동쪽으로 흐르는 물결 — 3프레임 위상) · 아래 돌턱(앞면, 그늘)."""
    t = Tile()
    ramp = CANAL_LIT if lit else CANAL_DARK
    for y in range(N):
        for x in range(N):
            if y < 8:                                                        # 위 돌턱(윗면)
                q = 5 if y < 2 else (4 if y < 6 else 2)
                if (x + 7) % 16 == 0 and y < 6:
                    q = 1
                t.set(x, y, lv(CURB, q))
            elif y >= N - 10:                                                # 아래 돌턱(앞면이 보임)
                ly = y - (N - 10)
                q = 6 if ly == 0 else (5 if ly < 3 else (3 if ly < 8 else 1))
                if (x + 3) % 16 == 0 and ly > 1:
                    q = 1
                t.set(x, y, lv(CURB, q))
            else:
                depth = (y - 8) / (N - 18)
                ph = 2 * math.pi * (x / 32 - k / 3) + 0.9 * math.sin(2 * math.pi * x / 64 + y * 0.21) + y * 0.13
                wv = math.sin(ph) * 0.5 + 0.5
                base = 2 + (1 if 0.3 < depth < 0.75 else 0)
                q = base + (1 if wv > 0.86 else (-1 if wv < 0.1 else 0))
                if y in (8, 9):
                    q = 0                                                    # 돌턱 밑 그늘
                t.set(x, y, lv(ramp, q))
                if wv > 0.94 and (y % 5 == 2):
                    t.set(x, y, ramp[-1] if lit else ramp[-2])               # 물결 반짝임
    return t.im


def bridge(side):
    """나무 다리 반쪽(left/right) — 남북으로 깐 널 + 바깥쪽 난간 기둥. 아래 돌턱은 칸 위·아래 그대로."""
    t = Tile(); t.im.paste(canal_frame(0, True), (0, 0)); t.p = t.im.load()
    P = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]]
    for x in range(N):
        X = x if side == "left" else x + N
        lx = X % 10
        for y in range(4, N - 4):
            q = 3 + (1 if lx < 2 else 0) - (2 if lx == 9 else 0) + (1 if hf(677, X // 10) > 0.6 else 0)
            if vnoise(X, y, 4, 678) < 0.13:
                q -= 1
            t.set(x, y, lv(P, q))
        t.set(x, 4, P[5]); t.set(x, N - 5, P[0]); t.set(x, N - 4, P[1])
    for y in (14, N - 16):                                                 # 가로 받침 못줄
        for x in range(1, N, 10):
            t.set(x, y, G[7])
    rx = 2 if side == "left" else N - 8                                    # 바깥 난간(가로대 + 기둥)
    for y in range(0, N - 2):
        for x in range(rx, rx + 6):
            t.set(x, y, lv(P, 4 if x < rx + 2 else (3 if x < rx + 4 else 1)))
    for y in (0, N // 2 - 3, N - 8):
        t.rect(rx - 1, y, rx + 6, y + 6, P[2]); t.hline(rx - 1, rx + 6, y, P[5]); t.hline(rx - 1, rx + 6, y + 6, P[0])
    return t.im


def cup_inlay(seed=1101):
    """연회장 가운데 잔 문장 상감 4×4칸(256): 둥근 테 2줄 + 큰 잔 — 층 램프 금실(비발광), 배경 투명."""
    W = 256
    t = Tile(W, W)
    cx, cy = 128, 128
    for y in range(W):
        for x in range(W):
            d = math.hypot((x + 0.5 - cx) / 118, (y + 0.5 - cy) / 118)
            if 0.94 <= d <= 1.0:
                t.set(x, y, A[20] if d < 0.97 else A[18])
            elif 0.86 <= d <= 0.88:
                t.set(x, y, A[19])
    for k in range(16):                                                    # 테 사이 점 무늬
        a = k / 16 * 2 * math.pi
        x, y = int(cx + math.cos(a) * 107), int(cy + math.sin(a) * 107)
        t.rect(x - 1, y - 1, x + 1, y + 1, A[21])
    # 잔(넓은 잔몸 + 대 + 받침)
    for y in range(64, 132):
        tt = (y - 64) / 68
        half = int(round(56 * (1 - tt ** 1.6)))
        for x in range(cx - half, cx + half + 1):
            edge = abs(x - cx) >= half - 2 or y < 67
            t.set(x, y, A[21] if edge else (A[17] if (x + y) % 2 == 0 and False else A[18]))
        t.set(cx - half, y, A[22])
    for y in range(64, 70):
        t.hline(cx - 56, cx + 56, y, A[20] if y > 65 else A[22])
    for y in range(132, 178):
        t.hline(cx - 4, cx + 4, y, A[19]); t.set(cx - 4, y, A[21]); t.set(cx + 4, y, A[17])
    for y in range(178, 192):
        half = int(8 + (y - 178) * 2.4)
        t.hline(cx - half, cx + half, y, A[19] if y < 190 else A[17]); t.set(cx - half, y, A[21])
    t.hline(cx - 40, cx + 40, 192, A[17])
    return t.im


def region_decals(rid):
    """반환: {(x, y): 이미지} — 시트 도트 좌표에 붙인다(JSON decals rect·canal 인덱스와 같은 자리)."""
    out = {}
    if rid == "waste":
        out[(0, 512)] = scorch()
        out[(128, 512)] = ruts(192, 64, 661)
    elif rid == "gate":
        out[(0, 512)] = ruts(192, 64, 671, ys=(18, 40), water=R64.WATER_GATE)
        out[(192, 512)] = puddles(128, 64, 672, R64.WATER_GATE)
    elif rid == "brewery":
        for i, k in enumerate((0, 1, 2)):
            out[(i * 64, 512)] = canal_frame(k, False)
            out[(320 + i * 64, 512)] = canal_frame(k, True)
        out[(192, 512)] = bridge("left")
        out[(256, 512)] = bridge("right")
        out[(0, 576)] = liquor_trail(128, 64, 691)
    elif rid == "hall":
        out[(0, 512)] = cup_inlay()
        out[(256, 512)] = liquor_trail(128, 64, 1111, ramp=(A[16], A[16], A[17], A[18], A[19], A[21]))
    return out
