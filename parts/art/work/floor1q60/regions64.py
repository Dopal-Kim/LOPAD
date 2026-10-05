"""60라운드 Q9·Q10 — 1층 5지역 바닥·엄폐 담 64도트 설계(지역 재질). fk64 도구로 그린다.

지역별 재질(60 Q10): 황무지 = 마른 흙 · 성문 = 따뜻한 회갈 판석 · 외곽 거리 = 포석(둥근 작은 돌) · 양조 구역 = 젖은 중립 판석 · 연회장 = 광택 돌판.
인덱스 뜻은 인덱스 표 v3·각 지역 JSON 그대로(roomFloorsNote·floorFeatures·stoneSet note):
  0~3 바닥 · 4 복도 · 23~26 start · 27~30 trial · 31~34 rest · 35~38 boss · 43 담 앞면 아랫단 · 44 윗단 · 45 윗면 · 46 아랫단 변형 · 60~62 바닥 특징.
명도: 지역 바닥 평균 루마를 현행(테두리 발치 땅에 맞춘 값)과 ±4 안으로(build 가 출력·검사).
"""
import math

from fk64 import (N, G, A, SL, WD, PL, CLEAR, h, hf, vnoise, fbm, new, rgba, flags, setts, dirt, soot, pool, straw, mud,
                  arrows, rush_mat, gold_trim, cup_engrave, ruts, grate, drain, gravel, shards, inlay_line, pebble, crack,
                  edge_window)
from PIL import Image

# ---------------------------------------------------------------- 램프(어두움 → 밝음, 루마 단조)
DIRT = [WD[0], WD[1], WD[2], WD[3], PL[0], PL[1], PL[2], PL[3]]
PEB = [G[2], G[3], G[4], PL[0], G[5], PL[1], G[6], G[7], G[8]]
WARM = [G[1], G[2], G[3], G[4], PL[0], PL[1], PL[2], PL[3], PL[4]]   # 3회차: 돌 몸에서 WD(채도 높은 갈색) 빼고 G·PL 만 — 갈색은 줄눈·흙에만
SETT = [WD[0], WD[1], WD[2], WD[3], PL[0], PL[1], PL[2], PL[3], PL[4]]   # 6회차: WD4(채도 높은 갈색) 빼 등불 아래 주황 융단처럼 보이던 것 완화
WET = [G[1], G[2], G[3], G[4], PL[0], G[5], PL[1], G[6], G[7], G[8], G[9]]
POLISH = [G[1], G[2], G[3], G[4], G[5], PL[1], G[6], G[7], G[8], G[9], G[10], G[11], G[12]]   # 2회차: 청회(SL) 빼고 중립 회색 — 현행 연회장 톤
BRICK = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[2], PL[3], PL[4]]
SACK = [WD[0], WD[1], WD[2], WD[3], PL[0], PL[1], PL[2], PL[3], PL[4]]
MORTAR = [G[1], G[2], SL[1]]
LIQ = [A[16], A[17], A[18], A[19], A[20], A[21]]
WATER_GATE = [SL[1], SL[2], A[18], A[19], A[20], A[21]]      # 문빛을 받은 물(호박 반사 — 비발광 단계만)
MUDC = [WD[0], WD[1], WD[2], WD[3], PL[1]]


def copy(im):
    return im.copy()


# ================================================================ 황무지(waste) — 마른 흙
WASTE_SHARED = 9101


DIRTC = {"base": PL[0], "cool": G[4], "warm": WD[3], "light": PL[1], "dark": WD[2], "darker": WD[1]}   # 3회차: 큰 얼룩 갈색(WD3) 제거 — 회갈↔중립 회색만


def waste_floor(v, **kw):
    """2회차 비평: 공유 잡음만 쓴 흙은 64마다 같은 얼룩이 되풀이되고, WD3↔PL1 큰 얼룩이 위장 무늬 → 같은 명도대 3색(PL0·G4·WD3) 얼룩 + 변형 잡음."""
    return dirt(WASTE_SHARED, 200 + v, DIRTC, peb_ramp=PEB, **kw)


def waste_tiles():
    t = {}
    t[0] = waste_floor(0, pebbles=5, cracks=1, grass=1)
    t[1] = waste_floor(1, pebbles=8, cracks=0, grass=0)
    t[2] = waste_floor(2, pebbles=3, cracks=2, grass=2)
    t[3] = waste_floor(3, pebbles=6, cracks=1, grass=0)
    # 4 복도 = 다져진 길: 같은 흙 + 가로로 눌린 결(밝은 줄) + 자갈 적게
    c = waste_floor(4, pebbles=2, cracks=0, grass=0)
    px = c.load()
    for y in range(N):
        for x in range(N):
            if vnoise(x, y * 3, 8, 4401, period=N) > 0.8:
                px[x, y] = rgba(PL[1])
            elif vnoise(x, y * 3, 8, 4402, period=N) < 0.12:
                px[x, y] = rgba(WD[2])
    t[4] = c
    # start = 그을린 흙·재
    for i in range(4):
        im = waste_floor(10 + i, pebbles=3, cracks=1)
        soot(im, 300 + i, amount=0.35 + 0.08 * i)
        t[23 + i] = im
    # trial = 진흙·웅덩이·금
    for i in range(4):
        im = waste_floor(20 + i, pebbles=4, cracks=2 + i % 2, damp=0.4)
        if i % 2 == 0:
            mud(im, 310 + i, 0.45 + 0.08 * i, 0.55, 0.26)
        t[27 + i] = im
    # rest = 다진 흙·지푸라기
    for i in range(4):
        im = waste_floor(30 + i, pebbles=2, cracks=0)
        straw(im, 320 + i, n=10 + 4 * i)
        t[31 + i] = im
    # boss = 짓밟힌 흙·부러진 화살
    for i in range(4):
        im = waste_floor(40 + i, pebbles=6, cracks=1, damp=0.3)
        arrows(im, 330 + i, n=1 + i % 2)
        t[35 + i] = im
    # 60 바퀴 자국 · 61 풀 · 62 자갈
    im = waste_floor(50, pebbles=2, cracks=0)
    ruts(im, 1, dark=(WD[1], WD[2]), lit=PL[1])
    t[60] = im
    t[61] = waste_floor(51, pebbles=2, cracks=0, grass=6)
    im = waste_floor(52, pebbles=10, cracks=0)
    gravel(im, 52, n=50, ramp=PEB[2:])
    t[62] = im
    t.update(sandbag_set())
    return t


def sandbag_set():
    """모래주머니 담: 자루 2단(엇갈림) · 묶은 끝 · 삼베 결 · 앞면 아래 땅 그늘 / 윗면 = 위에서 본 자루 등."""
    def sack_row(px, y0, hgt, off, seed, ymin=0, ymax=N):
        widths = []
        x = -off
        while x < N:
            w = 26 + int(hf(seed, len(widths)) * 10)
            widths.append((x, w))
            x += w
        for i, (x0, w) in enumerate(widths):
            cx, cy = x0 + w / 2, y0 + hgt / 2
            for y in range(max(ymin, y0), min(ymax, y0 + hgt + 1)):
                for xx in range(max(0, x0), min(N, x0 + w)):
                    u, v = (xx + 0.5 - cx) / (w / 2), (y + 0.5 - cy) / (hgt / 2)
                    if u ** 4 + v ** 2 > 1.0:
                        continue
                    dl = -0.55 * u - 0.83 * v
                    lv = 4 + (2 if dl > 0.7 else (1 if dl > 0.25 else (0 if dl > -0.3 else (-1 if dl > -0.7 else -2))))
                    if (xx + 2 * y) % 7 == 0 and hf(seed, xx, y) < 0.55 and lv > 1:
                        lv -= 1                                   # 삼베 결(사선 짜임)
                    if abs(u) > 0.86:
                        lv -= 1                                   # 묶은 끝 주름
                    px[xx, y] = rgba(SACK[max(0, min(8, lv + (1 if hf(seed, i, 5) > 0.7 else 0)))])
            # 묶은 끈(오른쪽 끝)
            tx = int(x0 + w - 4)
            for y in range(int(cy) - 2, int(cy) + 3):
                if 0 <= tx < N and ymin <= y < ymax:
                    px[tx, y] = rgba(WD[1])
    out = {}
    for idx, seed, ground in ((43, 61, True), (46, 67, True), (44, 63, False)):
        im = Image.new("RGBA", (N, N), rgba(WD[0]))
        px = im.load()
        sack_row(px, 0, 30, 6 if idx != 44 else 18, seed)
        sack_row(px, 32, 30, 20 if idx != 44 else 4, seed + 1)
        if idx == 44:
            for x in range(N):                                    # 윗면 밑 그늘
                for y in range(0, 3):
                    c = px[x, y]
                    px[x, y] = rgba(SACK[max(0, SACK.index(rgba(c)) - 2)]) if rgba(c) in SACK else c
        if ground:
            for x in range(N):
                for y in range(N - 3, N):
                    px[x, y] = rgba(WD[0] if y > N - 2 else WD[1])
        if idx == 46:                                             # 박은 나무 말뚝
            for y in range(4, N - 1):
                for x in range(40, 46):
                    lv = 4 if x == 40 else (3 if x < 44 else 2)
                    px[x, y] = rgba(BRICK[lv] if (y // 6) % 3 else BRICK[lv - 1])
            for x in range(39, 47):
                px[x, 3] = rgba(BRICK[5])
        out[idx] = im
    # 윗면: 위에서 본 자루 등(둥근 볼록 3개) + 앞 모서리 빛
    im = Image.new("RGBA", (N, N), rgba(WD[1]))
    px = im.load()
    for i, (x0, y0, w, hh) in enumerate(((0, 4, 30, 26), (30, 2, 34, 28), (12, 32, 36, 28), (-16, 32, 28, 28), (48, 32, 28, 28))):
        cx, cy = x0 + w / 2, y0 + hh / 2
        for y in range(max(0, y0), min(N, y0 + hh)):
            for x in range(max(0, x0), min(N, x0 + w)):
                u, v = (x + 0.5 - cx) / (w / 2), (y + 0.5 - cy) / (hh / 2)
                if u * u + v ** 4 > 1:
                    continue
                dl = -0.55 * u - 0.83 * v
                lv = 5 + (1 if dl > 0.4 else (-1 if dl < -0.4 else 0))
                if (x + y) % 6 == 0:
                    lv -= 1
                px[x, y] = rgba(SACK[max(0, min(8, lv))])
    for x in range(N):
        px[x, N - 2] = rgba(SACK[7])
        px[x, N - 1] = rgba(SACK[2])
    out[45] = im
    return out


# ================================================================ 성문(gate) — 따뜻한 회갈 판석
def gate_flag(seed, layout, **kw):
    return flags(seed, layout, WARM, WD[1], WD[0], base_lv=(4,), n_big=(0.88, 0.06), n_mid=(0.94, 0.04), bevel=1, **kw)  # 5회차: G4 판석이 푸른 판처럼 튐 → 한 색 + 테 약하게


def gate_tiles():
    t = {}
    for i, (lay, sd) in enumerate((("two_h", 1), ("three", 2), ("four", 3), ("two_v", 4))):
        t[i] = gate_flag(500 + sd, lay).im
    t[4] = gate_flag(510, "five", cracks=0.05).im
    for i, lay in enumerate(("two_h", "four", "three_b", "one")):     # start = 포석·짚
        f = gate_flag(520 + i, lay)
        straw(f.im, 521 + i, n=8 + 3 * i)
        t[23 + i] = f.im
    for i, lay in enumerate(("three", "two_v", "four", "one")):       # trial = 깨진 포석·문빛 웅덩이
        f = gate_flag(530 + i, lay, cracks=0.9, chip=0.9)
        if i % 2 == 1:
            pool(f.im, 531 + i, 0.5, 0.58, 0.24, WATER_GATE, gl=G[11], owner=f.owner)
        t[27 + i] = f.im
    for i, lay in enumerate(("two_h", "three", "four", "two_v")):      # rest = 진흙·짚
        f = gate_flag(540 + i, lay)
        mud(f.im, 541 + i, 0.4 + 0.1 * i, 0.5, 0.22, MUDC)
        straw(f.im, 545 + i, n=6)
        t[31 + i] = f.im
    for i in range(4):                                                 # boss = 성문 앞 큰 판석(_0 잔 문양)
        f = gate_flag(550 + i, "one", cracks=0.25)
        if i == 0:
            cup_engrave(f.im, dark=WD[1], lit=PL[2])
        t[35 + i] = f.im
    f = gate_flag(560, "two_h")
    ruts(f.im, 2, dark=(WD[0], WD[1]), lit=PL[1])
    t[60] = f.im
    f = gate_flag(561, "one")
    grate(f.im)
    t[61] = f.im
    f = gate_flag(562, "three")
    pool(f.im, 563, 0.5, 0.55, 0.3, WATER_GATE, gl=G[11], owner=f.owner)
    t[62] = f.im
    t.update(ashlar_set(WARM, seed=570))
    return t


def ashlar_set(ramp, seed, ring=True, rubble=False, top_ramp=None):
    """돌담: 큰 마름돌(3단, 엇갈림) — 정 자국·모서리 깨짐·위 모서리 빛 / rubble = 크기 들쭉날쭉한 막돌."""
    L = len(ramp) - 1

    def face(sd, part):
        im = Image.new("RGBA", (N, N), rgba(MORTAR[0]))
        px = im.load()
        rows = (21, 21, 22) if not rubble else (14, 18, 16, 16)
        y = 0
        for ri, rh in enumerate(rows):
            x = -int(hf(sd, ri, 1) * 20)
            bi = 0
            while x < N:
                w = (26 + int(hf(sd, ri, bi, 2) * 14)) if not rubble else (12 + int(hf(sd, ri, bi, 2) * 16))
                b = 4 + (1 if hf(sd, ri, bi, 3) > 0.65 else (-1 if hf(sd, ri, bi, 3) < 0.2 else 0))
                x0, x1, y0, y1 = x + 1, x + w - 1, y + 1, y + rh - 1
                for yy in range(max(0, y0), min(N, y1)):
                    for xx in range(max(0, x0), min(N, x1)):
                        cut = 2 if rubble else 1
                        if (xx - x0 < cut and yy - y0 < cut) or (x1 - 1 - xx < cut and y1 - 1 - yy < cut) or \
                                (rubble and ((x1 - 1 - xx < cut and yy - y0 < cut) or (xx - x0 < cut and y1 - 1 - yy < cut))):
                            continue
                        n = vnoise(xx, yy, 5, sd + ri * 7 + bi)
                        lv = b + (1 if n > 0.86 else (-1 if n < 0.12 else 0))   # 7회차: 밝은 얼룩 줄임
                        if yy - y0 < 2:
                            lv += 2 if yy == y0 else 1
                        elif xx - x0 < 1:
                            lv += 1
                        elif y1 - 1 - yy < 2:
                            lv -= 1 if yy < y1 - 1 else 2
                        elif x1 - 1 - xx < 1:
                            lv -= 1
                        if not rubble and (xx + yy * 2 + bi) % 9 == 0 and yy - y0 > 3 and y1 - yy > 3:
                            lv -= 1                                # 정 자국(사선 점)
                        px[xx, yy] = rgba(ramp[max(0, min(L, lv))])
                x += w
                bi += 1
            y += rh
        if part == "upper":
            for x in range(N):
                for yy in range(3):
                    c = rgba(px[x, yy])
                    px[x, yy] = rgba(MORTAR[0]) if yy == 0 else (rgba(ramp[max(0, ramp.index(c) - 2)]) if c in [rgba(r) for r in ramp] else c)
        if part in ("lower", "ring"):
            for x in range(N):
                for yy in range(N - 5, N):
                    c = rgba(px[x, yy])
                    rr = [rgba(r) for r in ramp]
                    if c in rr and vnoise(x, yy, 3, sd + 9) < (yy - (N - 5)) / 5 * 1.1:
                        px[x, yy] = rr[max(0, rr.index(c) - 1)]
                px[x, N - 1] = rgba(MORTAR[0])
        if part == "ring" and ring:                           # 쇠고리(말·수레 매는 고리)
            cx, cy = 32, 30
            for a in range(36):
                th = a / 36 * 6.283
                for r in (5.5, 6.5):
                    xx, yy = int(round(cx + math.cos(th) * r)), int(round(cy + math.sin(th) * r * 1.1))
                    px[xx, yy] = rgba(SL[7] if math.sin(th) < -0.2 else (SL[5] if math.cos(th) < 0 else SL[3]))
            for xx in range(29, 36):
                for yy in range(21, 26):
                    px[xx, yy] = rgba(SL[3] if yy > 23 else SL[5])
            px[30, 22] = rgba(G[12])
            for th in range(10):
                xx = int(round(cx + math.cos(0.3 + th * 0.25) * 6))
                yy = int(round(cy + math.sin(0.3 + th * 0.25) * 6.6)) + 1
                if 0 <= yy < N and px[xx, yy][:3] != SL[7][:3]:
                    px[xx, yy] = rgba(G[1])
        return im
    out = {43: face(seed, "lower"), 44: face(seed + 1, "upper"), 46: face(seed + 2, "ring")}
    # 윗면: 두꺼운 갓돌 2장(가로) — 위 모서리 그늘, 앞 모서리 가장 밝은 테 + 바로 아래 그늘
    im = Image.new("RGBA", (N, N), rgba(MORTAR[0]))
    px = im.load()
    ramp = top_ramp or ramp                                 # 6회차: 윗면은 무채·회갈 램프(포석 램프의 갈색 얼룩 방지)
    L = len(ramp) - 1
    split = 26 + int(hf(seed, 5) * 14)
    for y in range(N):
        for x in range(N):
            if split <= x < split + 2:
                continue
            k = 0 if x < split else 1
            n = vnoise(x, y, 8, seed * 3 + k)
            lv = 4 + (1 if n > 0.8 else (-1 if n < 0.15 else 0)) + (1 if k and hf(seed, 6) > 0.5 else 0)
            if y < 2:
                lv = 3
            elif y >= N - 3:
                lv = (9 if y == N - 3 else 8) if y < N - 1 else 2
            elif x in (split + 2,) or x == 0:
                lv += 1
            elif x == split - 1 or x == N - 1:
                lv -= 1
            if (x * 7 + y * 3) % 23 == 0:
                lv -= 1
            px[x, y] = rgba(ramp[max(0, min(L, lv))])
    out[45] = im
    return out


# ================================================================ 외곽 거리(outer) — 포석
def outer_sett(seed, **kw):
    kw.setdefault("base_lv", (3, 4, 4))
    return setts(seed, SETT, WD[2], WD[1], sand=PL[1], **kw)


def outer_tiles():
    t = {}
    rows_sets = ((13, 13, 12, 13, 13), (12, 13, 13, 13, 13), (13, 12, 13, 13, 13), (13, 13, 13, 12, 13))
    for i in range(4):
        t[i] = outer_sett(700 + i, rows=rows_sets[i]).im
    t[4] = outer_sett(710, rows=(11, 10, 11, 11, 10, 11), wmin=8, wmax=13, base_lv=(3, 4)).im     # 복도 = 작은 포석
    for i in range(4):                                         # start = 그을음·흙·자갈
        f = outer_sett(720 + i)
        soot(f.im, 721 + i, amount=0.3, ramp_dark=(WD[0], WD[1], WD[2]))
        gravel(f.im, 725 + i, n=14, ramp=PEB[3:])
        t[23 + i] = f.im
    for i in range(4):                                         # trial = 배수구·금
        f = outer_sett(730 + i)
        if i == 0:
            grate(f.im, 20, 22, 24, 18)
        else:
            px = f.im.load()
            for k in range(2 + i):
                kx = 6 + int(hf(731 + i, k) * 50)
                ky = 4 + int(hf(732 + i, k) * 50)
                own = lambda x, y, f=f: f.owner[y][x] if 0 <= x < N and 0 <= y < N else -1
                kk = own(kx, ky)
                if kk >= 0:
                    crack(px, own, kk, kx, ky, 8, 733 + i + k, SETT, f.base[kk], branch=False)
        t[27 + i] = f.im
    for i in range(4):                                         # rest = 다진 흙·짚 (포석 위 흙 덮임)
        f = outer_sett(740 + i)
        px = f.im.load()
        for y in range(N):
            for x in range(N):
                n = fbm(x, y, 741 + i, scales=(16, 6))
                if n * (0.35 + 0.65 * edge_window(x, y, 2)) > 0.5:
                    px[x, y] = rgba(DIRT[4] if vnoise(x, y, 3, 742 + i) > 0.3 else DIRT[3])
        straw(f.im, 745 + i, n=7)
        t[31 + i] = f.im
    for i, lay in enumerate(("one", "two_h", "two_v", "one")):   # boss = 광장 큰 포석(_0 잔 각인)
        f = flags(750 + i, lay, WARM, WD[1], WD[0], base_lv=(4, 4, 5), cracks=0.0 if i == 0 else 0.2, n_big=(0.86, 0.12), n_mid=(0.93, 0.05))
        if i == 0:
            cup_engrave(f.im, dark=WD[1], lit=PL[2])
        t[35 + i] = f.im
    f = outer_sett(760)
    drain(f.im, rim=(PL[1], PL[2], WD[1]))
    t[60] = f.im
    f = outer_sett(761)
    drain(f.im, rim=(PL[1], PL[2], WD[1]))
    grate(f.im, 22, 24, 20, 14)
    t[61] = f.im
    f = outer_sett(762)
    gravel(f.im, 763, n=70, ramp=PEB[2:])
    t[62] = f.im
    t.update(ashlar_set(SETT, seed=770, rubble=True, top_ramp=WARM))
    return t


# ================================================================ 양조 구역(brewery) — 젖은 중립 판석
def brew_flag(seed, layout, **kw):
    return flags(seed, layout, WET, SL[1], G[1], base_lv=(3, 3, 4), **kw)


def brewery_tiles():
    t = {}
    for i, (lay, sd) in enumerate((("four", 3), ("two_h", 5), ("three", 8), ("one", 11))):
        t[i] = brew_flag(900 + sd, lay).im
    t[4] = outer_like_setts_grey(910)
    for i, lay in enumerate(("two_h", "four", "three", "one")):    # start = 그을음
        f = brew_flag(920 + i, lay)
        soot(f.im, 921 + i, amount=0.4)
        t[23 + i] = f.im
    for i, (lay, st) in enumerate((("two_h", (0.48, 0.55, 0.26)), ("four", (0.62, 0.4, 0.2)), ("three", None), ("one", (0.5, 0.5, 0.32)))):
        f = brew_flag(930 + i, lay, cracks=0.5 if st is None else 0.15)   # trial = 술 얼룩·금
        if st:
            pool(f.im, 931 + i, *st, LIQ, gl=G[10], owner=f.owner)
        t[27 + i] = f.im
    for i, lay in enumerate(("three_b", "two_v", "four", "two_h")):   # rest = 짚
        f = brew_flag(940 + i, lay)
        straw(f.im, 941 + i, n=12 + 3 * i)
        t[31 + i] = f.im
    for i, lay in enumerate(("one", "two_h", "two_v", "one")):      # boss = 큰 술 얼룩
        f = brew_flag(950 + i, lay)
        pool(f.im, 951 + i, 0.5, 0.52, 0.42, LIQ, gl=G[10], owner=f.owner)
        t[35 + i] = f.im
    f = brew_flag(960, "two_h")
    drain(f.im, water=[LIQ[1], LIQ[2], LIQ[1], LIQ[0]])
    t[60] = f.im
    f = brew_flag(961, "two_h")
    drain(f.im, water=[LIQ[1], LIQ[2], LIQ[1], LIQ[0]])
    grate(f.im, 22, 24, 20, 14)
    t[61] = f.im
    f = brew_flag(962, "three")
    pool(f.im, 963, 0.46, 0.55, 0.3, LIQ, gl=G[10], owner=f.owner)
    t[62] = f.im
    t.update(brick_set(980))
    return t


def outer_like_setts_grey(seed):
    return setts(seed, WET, SL[1], G[1], rows=(11, 10, 11, 11, 10, 11), wmin=8, wmax=13, base_lv=(3, 4)).im


def brick_set(seed):
    def face(sd, part):
        im = Image.new("RGBA", (N, N), rgba(MORTAR[0]))
        px = im.load()
        rows, bh, bw = 4, 16, 32
        for y in range(N):
            r, yy = y // bh, y % bh
            off = (bw // 2) * (r % 2)
            for x in range(N):
                xx = (x + off) % bw
                bi = (x + off) // bw
                if yy < 2 or xx < 2:
                    px[x, y] = rgba(MORTAR[0] if (yy < 2 and xx >= 2) else MORTAR[1])
                    continue
                v = hf(sd, r, bi, 5)
                b = 2 + (1 if v > 0.72 else (-1 if v < 0.18 else 0))
                n = vnoise(x, y, 4, sd + r * 11 + bi)
                lv = b + (-1 if n < 0.16 else (1 if n > 0.9 else 0))
                if yy < 4:
                    lv += 2 if yy == 2 else 1
                elif yy >= bh - 1:
                    lv -= 1
                if xx < 3:
                    lv += 1
                elif xx >= bw - 1:
                    lv -= 1
                px[x, y] = rgba(BRICK[max(0, min(8, lv))])
        if part == "upper":
            for y in range(4):
                for x in range(N):
                    c = rgba(px[x, y])
                    px[x, y] = rgba(MORTAR[0]) if y < 2 else (rgba(BRICK[max(0, BRICK.index(c) - 2)]) if c in [rgba(b) for b in BRICK] else c)
        if part == "lower":
            bb = [rgba(b) for b in BRICK]
            for y in range(N - 12, N):
                for x in range(N):
                    c = rgba(px[x, y])
                    t = (y - (N - 12)) / 12
                    if c in bb and vnoise(x, y, 4, sd + 9) < t * 1.1:
                        px[x, y] = bb[max(0, bb.index(c) - (2 if t > 0.6 else 1))]
            for x in range(N):
                px[x, N - 1] = rgba(MORTAR[0])
        cx, cy = 8 + int(hf(sd, 81) * 44), 10 + int(hf(sd, 82) * 40)
        for j in range(4):
            for i in range(4 - j):
                px[cx + i, cy + j] = rgba(MORTAR[1])
        return im
    out = {43: face(seed, "lower"), 44: face(seed + 3, "upper")}
    im = face(seed + 6, "lower")                         # 46 = 쇠 띠를 두른 기둥 받침(벽돌 + 쇠 꺾쇠)
    px = im.load()
    for y in range(6, N - 2):
        for x in range(26, 38):
            lv = 4 if x < 28 else (3 if x < 34 else 2)
            px[x, y] = rgba(WD[lv] if (y // 5) % 4 else WD[lv - 1])
    for y in (14, 15, 40, 41):
        for x in range(25, 39):
            px[x, y] = rgba(SL[7] if y in (14, 40) else SL[3])
        px[27, y] = rgba(G[12])
    out[46] = im
    # 윗면 갓돌
    im = Image.new("RGBA", (N, N), rgba(MORTAR[0]))
    px = im.load()
    split = 30 + int(hf(seed, 1) * 12)
    for y in range(N):
        for x in range(N):
            if split <= x < split + 2:
                continue
            k = 0 if x < split else 1
            n = vnoise(x, y, 8, seed * 3 + k)
            lv = 4 + (1 if n > 0.7 else (-1 if n < 0.22 else 0)) + (1 if k and hf(seed, 2) > 0.5 else 0)
            if y < 2:
                lv = 2
            elif y >= N - 3:
                lv = (8 if y == N - 3 else 7) if y < N - 1 else 1
            elif x == split + 2 or x == 0:
                lv += 1
            px[x, y] = rgba(WET[max(0, min(10, lv))])
    for i in range(4):
        x, y = 6 + int(hf(seed, i, 91) * 50), 6 + int(hf(seed, i, 92) * 46)
        px[x, y] = rgba(LIQ[1])
        px[x + 1, y] = rgba(LIQ[1])
        px[x, y + 1] = rgba(LIQ[0])
    out[45] = im
    return out


# ================================================================ 연회장(hall) — 광택 돌판
def hall_slab(seed, layout, veins=2, sheen=True, **kw):
    f = flags(seed, layout, POLISH, G[1], G[0], base_lv=(4, 5), fleck=0.004, pits=0.2, chip=0.1, cracks=0.0, spec=0.0, bite=0.0,
              n_big=(0.86, 0.1), n_mid=(0.95, 0.03), **kw)
    px = f.im.load()
    L = len(POLISH) - 1
    own = lambda x, y: f.owner[y][x] if 0 <= x < N and 0 <= y < N else -1
    # 대리석 결: 구불구불한 가는 선(밝은 결 1 + 어두운 결 1)
    for v in range(veins):
        x, y = hf(seed, v, 1) * N, 4 + hf(seed, v, 2) * 20
        ang = 0.4 + hf(seed, v, 3) * 0.9
        dark = v % 2 == 1
        for i in range(70):
            ang += (vnoise(i, v, 6, seed + 3) - 0.5) * 0.5
            x += math.cos(ang)
            y += math.sin(ang) * 0.8
            xi, yi = int(x), int(y)
            k = own(xi, yi)
            if k < 0:
                if not (0 <= xi < N and 0 <= yi < N):
                    break
                continue
            px[xi, yi] = rgba(POLISH[max(0, f.base[k] - 2)] if dark else POLISH[min(L, f.base[k] + 2)])
    # 광택: 칸마다 왼쪽 위 → 오른쪽 아래 사선 반사 띠 2줄(한 단 밝게) — 위치는 변형마다 다름
    if sheen and hf(seed, 78) < 0.6:      # 7회차(조명 목업): 사선 2줄이 빗줄기처럼 보임 → 1줄·3도트, 변형 일부만
        off = int(hf(seed, 77) * 40) - 10
        for y in range(N):
            for x in range(N):
                k = own(x, y)
                if k < 0:
                    continue
                d = (x - y) - off
                if 0 <= d < 3:
                    c = rgba(px[x, y])
                    pp = [rgba(p) for p in POLISH]
                    if c in pp:
                        px[x, y] = pp[min(L, pp.index(c) + 1)]
    return f


def hall_tiles():
    t = {}
    for i, (lay, sd) in enumerate((("one", 1), ("two_h", 2), ("one", 3), ("two_v", 4))):
        t[i] = hall_slab(1100 + sd, lay).im
    t[4] = carpet(1110)
    for i, lay in enumerate(("one", "two_h", "two_v", "one")):     # start = 엎질러진 술
        f = hall_slab(1120 + i, lay)
        pool(f.im, 1121 + i, 0.45 + 0.05 * i, 0.55, 0.24 + 0.03 * i, LIQ, gl=G[12], owner=f.owner)
        t[23 + i] = f.im
    for i, lay in enumerate(("one", "two_h", "two_v", "one")):     # trial = 금 간 돌판
        f = hall_slab(1130 + i, lay)
        px = f.im.load()
        own = lambda x, y, f=f: f.owner[y][x] if 0 <= x < N and 0 <= y < N else -1
        for k in range(1 + i % 2):
            kx, ky = 14 + int(hf(1131 + i, k) * 36), 4
            kk = own(kx, ky + 2)
            if kk >= 0:
                crack(px, own, kk, kx, ky + 2, 40, 1132 + i + k, POLISH, f.base[kk])
        t[27 + i] = f.im
    for i, lay in enumerate(("one", "two_h", "two_v", "one")):     # rest = 골풀 깔개
        f = hall_slab(1140 + i, lay)
        rush_mat(f.im, 1141 + i, 6 + i, 8, 58 - i, 56 - (i % 2) * 4)
        t[31 + i] = f.im
    for i in range(4):                                             # boss = 금실 상감 테(같은 무늬)
        f = hall_slab(1150 + i, "one", veins=1)
        gold_trim(f.im)
        t[35 + i] = f.im
    f = hall_slab(1160, "one")
    pool(f.im, 1161, 0.5, 0.55, 0.3, LIQ, gl=G[12], owner=f.owner)
    t[60] = f.im
    f = hall_slab(1162, "one")
    inlay_line(f.im)
    t[61] = f.im
    f = hall_slab(1163, "two_h")
    shards(f.im, 1164)
    t[62] = f.im
    t.update(balustrade_set(1170))
    return t


def carpet(seed):
    """연회장 복도 양탄자(층 램프): 짜임 결 + 칸마다 마름모 무늬(가로·세로 이어짐) + 테두리 없음(복도가 이어지므로)."""
    im = new()
    px = im.load()
    C = [A[16], A[17], A[18], A[19], A[20], A[21]]
    for y in range(N):
        for x in range(N):
            v = 1 + (1 if (x + y) % 4 == 0 else 0) - (1 if (x * 3 + y) % 7 == 0 else 0)
            # 마름모: 칸 가운데
            d = abs(x - 31.5) + abs(y - 31.5)
            if 18 <= d < 20:
                v = 3
            elif 20 <= d < 21:
                v = 0
            elif d < 6:
                v = 4 if d < 3 else 2
            elif 10 <= d < 11:
                v = 3 if (x + y) % 2 == 0 else 2
            # 칸 모서리 사분 마름모(이웃 칸과 이어짐)
            dc = min(abs(x - c) + abs(y - r) for c in (0, 63) for r in (0, 63))
            if 6 <= dc < 8:
                v = 3
            elif dc < 3:
                v = 4
            px[x, y] = rgba(C[max(0, min(5, v))])
    return im


def balustrade_set(seed):
    """돌 난간: 43 = 받침돌 + 난간동자(병 모양) 아래 / 44 = 난간동자 위 + 손잡이 / 45 = 손잡이 윗면(광택 돌판) / 46 = 굵은 기둥 아래.
    난간동자 사이는 투명(0)."""
    L = len(POLISH) - 1

    def baluster_profile(t):          # t: 0 = 바닥, 1 = 손잡이 밑. 반폭(도트)
        return 4.0 + 3.4 * math.sin(math.pi * min(1.0, t * 1.25)) ** 1.5 * (1 if t < 0.8 else 0.6) + (2.5 if t < 0.08 else 0)

    def shade(x, cx, hw, base):
        u = (x + 0.5 - cx) / hw
        return base + (2 if u < -0.55 else (1 if u < -0.15 else (0 if u < 0.35 else (-1 if u < 0.75 else -2))))
    full_h = 2 * N
    tall = Image.new("RGBA", (N, full_h), CLEAR)
    px = tall.load()
    plinth_h, rail_h = 14, 14
    for y in range(full_h - plinth_h, full_h):                   # 받침돌
        for x in range(N):
            lv = 5 + (2 if y == full_h - plinth_h else (1 if y < full_h - plinth_h + 3 else 0)) - (2 if y >= full_h - 2 else 0)
            if (x * 5 + y) % 19 == 0:
                lv -= 1
            px[x, y] = rgba(POLISH[max(0, min(L, lv))])
    for y in range(0, rail_h):                                    # 손잡이(위)
        for x in range(N):
            lv = 6 + (2 if y < 2 else (1 if y < 4 else 0)) - (2 if y >= rail_h - 2 else (1 if y >= rail_h - 4 else 0))
            px[x, y] = rgba(POLISH[max(0, min(L, lv))])
    span = full_h - plinth_h - rail_h
    for cx in (16.0, 48.0):
        for y in range(rail_h, full_h - plinth_h):
            t = 1 - (y - rail_h) / span
            hw = baluster_profile(t)
            for x in range(int(cx - hw - 1), int(cx + hw + 2)):
                if abs(x + 0.5 - cx) <= hw:
                    px[x, y] = rgba(POLISH[max(0, min(L, shade(x, cx, hw, 5)))])
        for y in range(full_h - plinth_h - 3, full_h - plinth_h):  # 동자 발치 그늘
            for x in range(int(cx - 7), int(cx + 8)):
                if px[x, y][3]:
                    pass
    out = {44: tall.crop((0, 0, N, N)), 43: tall.crop((0, N, N, 2 * N))}
    # 46 굵은 기둥(아래 칸): 네모 기둥 + 받침
    im = Image.new("RGBA", (N, N), CLEAR)
    px = im.load()
    for y in range(N):
        for x in range(14, 50):
            if y >= N - plinth_h or True:
                pass
            lv = shade(x, 32, 18, 5)
            if y >= N - 10:
                if x < 10 or x > 53:
                    continue
            if (x * 3 + y * 5) % 23 == 0:
                lv -= 1
            px[x, y] = rgba(POLISH[max(0, min(L, lv))])
    for y in range(N - 10, N):
        for x in range(10, 54):
            lv = 6 + (2 if y == N - 10 else 0) - (2 if y >= N - 2 else 0)
            px[x, y] = rgba(POLISH[max(0, min(L, lv))])
    for y in range(N - plinth_h, N - 10):                        # 받침돌 띠(양옆)
        for x in list(range(0, 14)) + list(range(50, N)):
            px[x, y] = rgba(POLISH[6 if y == N - plinth_h else 5])
    out[46] = im
    # 45 손잡이 윗면: 광택 돌판(쇠시리 2줄)
    im = Image.new("RGBA", (N, N), rgba(G[1]))
    px = im.load()
    for y in range(N):
        for x in range(N):
            lv = 6
            if y < 2:
                lv = 4
            elif y in (10, 11) or y in (50, 51):
                lv = 4 if y in (11, 51) else 8
            elif y >= N - 3:
                lv = 10 if y == N - 3 else (9 if y == N - 2 else 3)
            n = vnoise(x, y, 9, seed + 5)
            lv += 1 if n > 0.72 else (-1 if n < 0.2 else 0)
            d = (x - y) - 8
            if 0 <= d < 5:
                lv += 1
            px[x, y] = rgba(POLISH[max(0, min(L, lv))])
    out[45] = im
    return out


REGIONS = {"waste": waste_tiles, "gate": gate_tiles, "outer": outer_tiles, "brewery": brewery_tiles, "hall": hall_tiles}
NEW_IDX = list(range(0, 5)) + list(range(23, 39)) + [43, 44, 45, 46, 60, 61, 62]
