"""P19 바닥 재질 — 지역별 기본(매크로 8×8칸 = 512 도트 주기) · 흙 · 돌 덮개 재질.

모든 재질은 512×512 도트 주기 텍스처(가로·세로 이음매 없음)이고, 시트에는 8×8 칸으로 잘려 들어간다.
게임은 칸 (tx, ty) 에 macro[(ty mod 8)*8 + (tx mod 8)] 을 놓는다 → 같은 그림이 8칸마다만 되풀이되고,
돌 줄눈은 칸 경계와 무관한 불규칙 보로노이/석축이라 '격자'가 보이지 않는다. 줄눈 대비는 일부러 낮춘다(P19 진단 1-6).
셰이딩: 돌마다 높이장(경계거리 → 둥근 어깨) → 법선 → 왼쪽 위 빛. 램프는 한 색 계열(밝기만 다름) — 돌마다 두 램프 중 하나.
"""
import numpy as np
from scipy.ndimage import gaussian_filter

from tk import G, A, SL, WD, PL, voronoi, relax, jitter_grid, fbm, quant

M = 512
L3 = np.array([-0.5, -0.6, 0.62]); L3 = L3 / np.linalg.norm(L3)
LX, LY = -0.6, -0.8


def blur(a, s):
    return gaussian_filter(a, s, mode="wrap")


def shade_height(hgt, k=2.4):
    gy, gx = np.gradient(np.pad(hgt, 1, mode="wrap"))
    gx, gy = gx[1:-1, 1:-1], gy[1:-1, 1:-1]
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(hgt)
    n = np.sqrt(nx * nx + ny * ny + nz * nz)
    return (nx * L3[0] + ny * L3[1] + nz * L3[2]) / n - L3[2]


def grain(seed, amp, s=1.1, h=M, w=M):
    rng = np.random.default_rng(seed)
    g = blur(rng.random((h, w)).astype(np.float32), s)
    g = (g - g.mean()) / (g.std() + 1e-6)
    return amp * g


def macro_tone(seed, amp=0.08, h=M, w=M):
    return amp * (fbm(h, w, 2, 3, seed, gain=0.6) - 0.5) * 2


def cell_field(idv, e, mortar, R):
    """경계거리 → 돌 높이(둥근 어깨, 모서리도 둥글게)."""
    hgt = np.clip((e - mortar) / R, 0, 1)
    hgt = 1 - (1 - hgt) ** 2
    return blur(hgt, 1.1)


def stones(seed, pts, ramps, alt=0.3, base=0.6, tone=0.07, mortar=1.4, R=6.0, gain=0.55, mortar_v=0.2, grain_amp=0.022,
           aniso=(1.0, 1.0), chip=0.0, wear_amp=0.0):
    """보로노이 돌 → RGB. ramps = (주 램프, 보조 램프). 돌마다 alt 비율로 보조 램프."""
    rng = np.random.default_rng(seed)
    idv, d1, d2 = voronoi(M, M, pts, aniso=aniso)
    e = (d2 - d1) * 0.5
    hgt = cell_field(idv, e, mortar, R)
    if chip:
        ch = blur((rng.random((M, M)) < chip * 0.02).astype(np.float32), 1.2) > 0.04
        hgt = np.where(ch & (e < R * 0.8), hgt * 0.5, hgt)
    sh = shade_height(hgt * R * 0.35)
    tones = rng.normal(0, tone, len(pts)).astype(np.float32)
    v = base + tones[idv] + gain * sh + grain(seed + 1, grain_amp) + macro_tone(seed + 2, 0.07)
    if wear_amp:
        v += wear_amp * wear(seed + 3)
    mor = e < mortar + 0.4
    v = np.where(mor, mortar_v + grain(seed + 4, 0.03), v)
    useb = (rng.random(len(pts)) < alt)[idv] & ~mor
    return np.where(useb[..., None], quant(v, ramps[1]), quant(v, ramps[0])), e


def wear(seed):
    n = fbm(M, M, 3, 3, seed, aspect=2.0)
    return np.clip((n - 0.5) * 4, 0, 1)


def pebbles(v, seed, n, size=(1.2, 2.6), amp=0.2):
    rng = np.random.default_rng(seed)
    out = v.copy()
    for _ in range(int(n)):
        cx, cy = rng.uniform(0, M), rng.uniform(0, M)
        r = rng.uniform(*size)
        for y in range(int(cy - r - 2), int(cy + r + 3)):
            for x in range(int(cx - r - 2), int(cx + r + 3)):
                dx, dy = x - cx, (y - cy) * 1.25
                d = (dx * dx + dy * dy) ** 0.5
                if d <= r:
                    lt = -(dx * LX + dy * LY / 1.25) / (d + 0.5)
                    out[y % M, x % M] += amp * (0.55 + 0.6 * lt)
                elif d <= r + 1.3 and dy > 0:
                    out[y % M, x % M] -= amp * 0.9
    return out


def strands(v, seed, n, length=(5, 12), amp=0.3, dens=None, dirf=None):
    rng = np.random.default_rng(seed)
    out = v.copy()
    k = 0
    while k < n:
        x, y = rng.uniform(0, M), rng.uniform(0, M)
        if dens is not None and rng.random() > dens[int(y), int(x)]:
            continue
        k += 1
        a = dirf[int(y), int(x)] + rng.normal(0, 0.25) if dirf is not None else rng.uniform(0, np.pi)
        L = rng.integers(*length)
        for t in range(L):
            xi, yi = int(x + np.cos(a) * t) % M, int(y + np.sin(a) * t) % M
            out[yi, xi] += amp * (1.0 if t % 5 else 0.6)
            out[(yi + 1) % M, xi] -= amp * 0.45
    return out


def cracks(v, seed, n, amp=0.25, length=(10, 40)):
    rng = np.random.default_rng(seed)
    out = v.copy()
    for _ in range(n):
        x, y = rng.uniform(0, M), rng.uniform(0, M)
        a = rng.uniform(0, 2 * np.pi)
        for t in range(int(rng.integers(*length))):
            a += rng.normal(0, 0.35)
            x += np.cos(a); y += np.sin(a)
            xi, yi = int(x) % M, int(y) % M
            out[yi, xi] -= amp
            out[(yi + 1) % M, xi] += amp * 0.2
    return out


def ashlar_cells(seed, row_h, wmin, wmax, jog=0):
    """줄마다 높이가 다른 석축(판석 바닥) — 칸 id·경계거리. row_h 합 = 512, 줄마다 너비 무작위(주기 512)."""
    rng = np.random.default_rng(seed)
    assert sum(row_h) == M
    cid = np.zeros((M, M), np.int32)
    e = np.zeros((M, M), np.float32)
    y0, k = 0, 0
    xs_ = np.arange(M)
    for rh in row_h:
        # 너비 목록(합 512)
        ws = []
        while sum(ws) < M:
            ws.append(int(rng.integers(wmin, wmax + 1)))
        ws[-1] -= sum(ws) - M
        if ws[-1] < wmin // 2:
            ws[-2] += ws[-1]; ws.pop()
        off = int(rng.integers(0, M))
        edges = np.cumsum([0] + ws)
        for i in range(len(ws)):
            x0, x1 = edges[i], edges[i + 1]
            xx = (xs_ - off) % M
            m = (xx >= x0) & (xx < x1)
            lx = np.minimum(xx - x0, x1 - 1 - xx)
            for y in range(y0, y0 + rh):
                ly = min(y - y0, y0 + rh - 1 - y)
                cid[y, m] = k
                e[y, m] = np.minimum(lx[m], ly)
            k += 1
        y0 += rh
    return cid, e, k


def slabs(seed, cid, e, n, ramps, alt=0.3, base=0.6, tone=0.06, mortar=1.0, R=5.0, gain=0.45, mortar_v=0.25, veins=0.0):
    rng = np.random.default_rng(seed)
    hgt = cell_field(cid, e, mortar, R)
    sh = shade_height(hgt * R * 0.3)
    tones = rng.normal(0, tone, n).astype(np.float32)
    v = base + tones[cid] + gain * sh + grain(seed + 1, 0.03) + macro_tone(seed + 2, 0.06)
    if veins:
        vn = fbm(M, M, 5, 4, seed + 5)
        v += veins * np.clip(1 - np.abs(vn - 0.5) * 30, 0, 1)
    mor = e < mortar
    v = np.where(mor, mortar_v, v)
    useb = (rng.random(n) < alt)[cid] & ~mor
    return np.where(useb[..., None], quant(v, ramps[1]), quant(v, ramps[0])), e


def ground(seed, ramp, base=0.55, mottle=0.12, cells=6, grain_amp=0.06, aspect=1.0):
    v = base + mottle * (fbm(M, M, cells, 4, seed, aspect=aspect) - 0.5) * 2 + grain(seed + 1, grain_amp)
    return v


# ================================================================ 지역 램프 (어두움 → 밝음, 한 색 계열)
R_ = {
    "taupe": [WD[1], WD[2], PL[0], PL[1], PL[2], PL[3], PL[4]],
    "warm": [WD[1], WD[2], WD[3], WD[4], WD[5], PL[3], PL[4]],
    "earth": [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5], PL[3]],
    "slate": [SL[1], SL[2], SL[3], SL[4], SL[5], SL[6], SL[7], G[9]],
    "grey": [G[2], G[3], G[4], G[5], G[6], G[7], G[8], G[9]],
    "pale": [G[4], G[5], G[6], G[7], G[8], G[9], G[10], G[11], G[12]],
    "lime": [SL[3], PL[0], PL[1], PL[2], PL[3], PL[4], G[12]],
    "brick": [WD[1], A[17], A[18], WD[4], A[19], WD[5], PL[3]],
    "gravel": [SL[2], SL[3], PL[0], PL[1], PL[2], PL[3], PL[4]],
    "straw": [WD[1], WD[2], WD[3], WD[4], WD[5], PL[3], PL[4]],
}


def outer_base(seed=101):
    """외곽 거리: 손바닥만 한 회갈 포석(불규칙 setts, 행 엇갈림) + 닳은 흐름 + 줄눈 흙."""
    pts = relax(jitter_grid(M, M, 21, 25, 0.3, seed, stagger=0.5), M, M, 1)
    rgb, e = stones(seed, pts, (R_["taupe"], R_["warm"]), alt=0.32, base=0.6, tone=0.08, mortar=1.3, R=6.0,
                    mortar_v=0.2, chip=0.4, wear_amp=0.06)
    return rgb


def outer_dirt(seed=111):
    """흙에 반쯤 묻힌 포석 — 길 가운데는 진흙, 군데군데 돌이 드러남(닳은 길)."""
    v = ground(seed, None, base=0.56, mottle=0.15, cells=9, grain_amp=0.04)
    v = cracks(v, seed + 5, 30, amp=0.12, length=(6, 18))
    v = pebbles(v, seed + 2, 420, amp=0.2)
    mud = quant(v, R_["earth"])
    return sunk_stones(outer_base(), mud, seed + 9, keep=0.42)


def sunk_stones(stone_rgb, mud_rgb, seed, keep=0.4, cells=10):
    """흙 덮개 사이로 드러난 바닥 돌(같은 매크로 좌표라 바닥과 이어짐 — 흙 가장자리가 돌 사이로 스며 보임)."""
    n = fbm(M, M, cells, 3, seed)
    show = n > 1 - keep * 0.9
    show = blur(show.astype(np.float32), 1.2) > 0.5
    out = mud_rgb.copy()
    out[show] = stone_rgb[show]
    return out


def outer_stone(seed=121):
    """광장 큰 석회 판석(분수 둘레 무대)."""
    rng = np.random.default_rng(seed)
    pts = relax([(rng.uniform(0, M), rng.uniform(0, M)) for _ in range(150)], M, M, 3)
    rgb, e = stones(seed, pts, (R_["lime"], R_["pale"]), alt=0.25, base=0.6, tone=0.06, mortar=1.5, R=8.0, mortar_v=0.16,
                    chip=0.6)
    return rgb


def gate_base(seed=201):
    """성문: 크고 납작한 청회 판석(가로로 약간 긴) — 군화·수레로 닳은 흐름."""
    pts = relax(jitter_grid(M, M, 9, 13, 0.3, seed, stagger=0.5), M, M, 2)
    rgb, e = stones(seed, pts, (R_["slate"], R_["grey"]), alt=0.3, base=0.6, tone=0.06, mortar=1.4, R=8.0, mortar_v=0.2,
                    aniso=(0.8, 1.15), chip=0.7, wear_amp=0.06)
    return rgb


def gate_dirt(seed=211):
    v = ground(seed, None, base=0.5, mottle=0.12, cells=9, grain_amp=0.05)
    v = pebbles(v, seed + 2, 1400, size=(0.9, 2.2), amp=0.24)
    return sunk_stones(gate_base(), quant(v, R_["gravel"]), seed + 9, keep=0.3)


def gate_stone(seed=221):
    """성문 앞 길: 짙은 작은 포석."""
    pts = relax(jitter_grid(M, M, 30, 36, 0.3, seed, stagger=0.5), M, M, 1)
    rgb, e = stones(seed, pts, (R_["slate"], R_["grey"]), alt=0.25, base=0.55, tone=0.07, mortar=1.1, R=4.5, mortar_v=0.16)
    return rgb


def brewery_base(seed=301):
    """양조 구역: 젖은 회색 판석(중간 크기) + 축축한 얼룩."""
    rng = np.random.default_rng(seed)
    pts = relax([(rng.uniform(0, M), rng.uniform(0, M)) for _ in range(230)], M, M, 2)
    rgb, e = stones(seed, pts, (R_["grey"], R_["slate"]), alt=0.3, base=0.62, tone=0.06, mortar=1.3, R=6.5, mortar_v=0.18,
                    chip=0.6)
    return rgb


def brewery_dirt(seed=311):
    """엎질러진 술지게미·젖은 흙."""
    v = ground(seed, None, base=0.48, mottle=0.16, cells=10, grain_amp=0.04)
    v = pebbles(v, seed + 2, 300, amp=0.2)
    v = strands(v, seed + 6, 500, length=(3, 7), amp=0.18)
    return sunk_stones(brewery_base(), quant(v, R_["earth"]), seed + 9, keep=0.3)


def brewery_stone(seed=321):
    """벽돌 포장(어긋난 줄) — 작업 마당·부두."""
    rh = [16] * 32
    cid, e, n = ashlar_cells(seed, rh, 28, 40)
    rgb, _ = slabs(seed, cid, e, n, (R_["brick"], R_["warm"]), alt=0.45, base=0.5, tone=0.07, mortar=1.0, R=3.5,
                   mortar_v=0.22)
    return rgb


def hall_base(seed=401):
    """연회장: 큰 연마 판석 석축(줄 높이·너비 제각각) + 은은한 결."""
    rh = [48, 80, 56, 72, 48, 88, 56, 64]
    cid, e, n = ashlar_cells(seed, rh, 70, 150)
    rgb, _ = slabs(seed, cid, e, n, (R_["grey"], R_["pale"]), alt=0.12, base=0.62, tone=0.035, mortar=1.0, R=5.0,
                   mortar_v=0.28, veins=0.07)
    return rgb


def hall_dirt(seed=411):
    """연회 준비로 깔아 둔 골풀·짚 — 결이 흐르는 다발."""
    v = ground(seed, None, base=0.42, mottle=0.08, cells=6, grain_amp=0.05)
    dirf = (fbm(M, M, 3, 2, seed + 3) - 0.5) * 2 * np.pi
    dens = np.clip(fbm(M, M, 6, 2, seed + 4) * 1.6 - 0.3, 0.15, 1)
    v = strands(v, seed + 2, 3200, length=(7, 18), amp=0.17, dens=dens, dirf=dirf)
    return quant(v, R_["straw"])


def hall_stone(seed=421):
    """대리석 마름모(무대 중심) — 밝은 판 / 조금 어두운 판이 엇갈림. 마름모 간격 128(칸 격자와 45°)."""
    yy, xx = np.mgrid[0:M, 0:M].astype(np.float32)
    a = (xx + yy + 32) % 128
    b = (xx - yy + 32) % 128
    e = np.minimum(np.minimum(a, 128 - a), np.minimum(b, 128 - b)) / 1.414
    cid = (((xx + yy + 32) // 128).astype(int) * 7 + ((xx - yy + 32 + 512) // 128).astype(int)) % 64
    par = ((((xx + yy + 32) // 128) + ((xx - yy + 32 + 512) // 128)) % 2).astype(bool)
    rng = np.random.default_rng(seed)
    hgt = cell_field(cid, e, 1.0, 5.0)
    sh = shade_height(hgt * 1.5)
    vn = fbm(M, M, 5, 4, seed + 5)
    v = 0.6 + 0.45 * sh + grain(seed + 1, 0.025) + 0.08 * np.clip(1 - np.abs(vn - 0.5) * 30, 0, 1)
    v = np.where(e < 1.0, 0.25, v)
    return np.where((par & (e >= 1.0))[..., None], quant(v + 0.08, R_["grey"]), quant(v - 0.05, R_["pale"]))


def waste_base(seed=501):
    """황무지: 마른 흙 — 갈라진 판(실금 그물) + 자갈 + 마른 풀."""
    rng = np.random.default_rng(seed)
    pts = relax([(rng.uniform(0, M), rng.uniform(0, M)) for _ in range(90)], M, M, 2)
    idv, d1, d2 = voronoi(M, M, pts)
    e = (d2 - d1) * 0.5
    hgt = cell_field(idv, e, 0.6, 9.0)
    v = 0.56 + 0.25 * shade_height(hgt * 1.4) + ground(seed + 1, None, 0.0, 0.07, 6, 0.05)
    crack = (e < 0.75) & (fbm(M, M, 20, 2, seed + 3) > 0.4)
    v = np.where(crack, 0.18, v)
    v = pebbles(v, seed + 4, 60, amp=0.18)
    return quant(v, R_["warm"])


def waste_dirt(seed=511):
    """밟혀 다져진 진흙 길(바퀴 자국 결 — 가로로 긴 얼룩)."""
    v = ground(seed, None, base=0.5, mottle=0.16, cells=5, grain_amp=0.04, aspect=3.0)
    v = cracks(v, seed + 5, 40, amp=0.12, length=(6, 20))
    v = pebbles(v, seed + 3, 260, amp=0.2)
    return quant(v, R_["earth"])


def waste_stone(seed=521):
    """드러난 바위 판."""
    rng = np.random.default_rng(seed)
    pts = relax([(rng.uniform(0, M), rng.uniform(0, M)) for _ in range(40)], M, M, 2)
    rgb, e = stones(seed, pts, (R_["slate"], R_["taupe"]), alt=0.4, base=0.56, tone=0.07, mortar=1.6, R=10.0, mortar_v=0.16,
                    chip=1.0, grain_amp=0.05)
    return rgb


MATERIALS = {
    "outer": (outer_base, outer_dirt, outer_stone),
    "gate": (gate_base, gate_dirt, gate_stone),
    "brewery": (brewery_base, brewery_dirt, brewery_stone),
    "hall": (hall_base, hall_dirt, hall_stone),
    "waste": (waste_base, waste_dirt, waste_stone),
}
MAT_NAMES = {
    "outer": ("회갈 포석", "다져진 흙", "광장 석회 판석"),
    "gate": ("청회 판석", "자갈·진흙", "짙은 포석 길"),
    "brewery": ("젖은 판석", "술지게미 진흙", "벽돌 포장"),
    "hall": ("연마 판석 석축", "깔아 둔 골풀", "대리석 마름모"),
    "waste": ("마른 갈라진 흙", "다져진 진흙 길", "드러난 바위 판"),
}
