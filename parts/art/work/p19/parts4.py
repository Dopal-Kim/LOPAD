"""P19 타일셋 v4 조각 — 덮개 가면(코너 왕 16)·가장자리 테·데칼·벽(앞면 2칸·윗면)·낙하 구역·다리·난간·높은 단·계단.

모든 함수는 64×64 RGBA 배열(np.uint8 (64,64,4))을 돌려준다. 색은 tk 팔레트만.
이음 규칙
- 덮개 가면(wang16): 칸 네 모서리(꼭짓점) 재질 비트 NW=1·NE=2·SW=4·SE=8. 가장자리 모양은 그 변의 두 꼭짓점 + 64 주기 노이즈로만
  정해지므로 어떤 이웃과도 이어진다(꼭짓점 값은 항상 비트 그대로).
- 칸 단위 자동 타일(낙하 둑·벽 윗면 테·높은 단 테): 이웃 비트 N=1·E=2·S=4·W=8 (= 그 쪽 이웃이 '다른 것').
- 벽 앞면: 줄(코스) 높이 고정 + 칸 경계를 걸치는 돌은 모든 변형에서 같은 그림 → 변형을 섞어도 이음매 없음.
"""
import numpy as np
from scipy.ndimage import binary_erosion, binary_dilation, gaussian_filter

from tk import G, A, SL, WD, PL, NT, U, quant, fbm, vnoise, bayer

T = U
L3 = np.array([-0.5, -0.6, 0.62]); L3 = L3 / np.linalg.norm(L3)


def empty():
    return np.zeros((T, T, 4), np.uint8)


def put(dst, rgb, m):
    """m: bool (T,T) 영역에 rgb (T,T,3) 를 불투명으로."""
    dst[m, :3] = rgb[m]
    dst[m, 3] = 255
    return dst


def col(dst, m, c):
    dst[m, :3] = c
    dst[m, 3] = 255
    return dst


def over(dst, src):
    m = src[..., 3] > 0
    dst[m] = src[m]
    return dst


def pnoise(seed, cells=2, oct_=3, h=T, w=T):
    return fbm(h, w, cells, oct_, seed)


def rnd_field(seed, h=T, w=T):
    return np.random.default_rng(seed).random((h, w))


YY, XX = np.mgrid[0:T, 0:T].astype(np.float32)


# ================================================================ 덮개 가면 (코너 왕 16)
def wang_mask(cfg, seed, amp=0.7, cells=2, variant=0):
    nw, ne, sw, se = (cfg >> 0) & 1, (cfg >> 1) & 1, (cfg >> 2) & 1, (cfg >> 3) & 1
    u = (XX + 0.5) / T
    v = (YY + 0.5) / T
    su = u * u * (3 - 2 * u)
    sv = v * v * (3 - 2 * v)
    top = nw + (ne - nw) * su
    bot = sw + (se - sw) * su
    val = top + (bot - top) * sv
    n = np.clip((pnoise(seed, cells, 3) - 0.5) * amp, -0.45, 0.45)
    if variant:
        edge = np.minimum(np.minimum(XX, T - 1 - XX), np.minimum(YY, T - 1 - YY))
        w = np.clip((edge - 6) / 10, 0, 1)
        n = n * (1 - w) + (pnoise(seed + 31 * variant, cells + 1, 3) - 0.5) * amp * w
    return (val + n) > 0.5


def mask_tile(m):
    out = empty()
    out[m] = (255, 255, 255, 255)
    return out


def _er(m, it=1):
    return binary_erosion(m, iterations=it, border_value=1)


def _di(m, it=1):
    return binary_dilation(m, iterations=it, border_value=0)


def rim_dirt(m, ramp, seed):
    """흙 덮개 테: 안쪽 1도트 성긴 짙은 테 + 바깥 3도트 흩뿌린 흙 부스러기(주기 랜덤장 — 이웃 칸과 이어짐)."""
    out = empty()
    if m.all() or not m.any():
        return out
    rf = rnd_field(seed)
    inner = m & ~_er(m)
    ring1 = _di(m, 1) & ~m
    ring3 = _di(m, 3) & ~m
    col(out, inner & (rf < 0.55), ramp[1])
    col(out, ring1 & (rf < 0.45), ramp[2])
    col(out, ring3 & ~ring1 & (rf < 0.14), ramp[3])
    return out


def rim_stone(m, dark, light, seed):
    """돌 덮개 테: 경계 안쪽 1도트 줄눈(dark) + 그 안쪽 1도트 연석 빛(light, 위·왼쪽을 향한 곳만)."""
    out = empty()
    if m.all() or not m.any():
        return out
    inner = m & ~_er(m)
    in2 = _er(m) & ~_er(m, 2)
    # 빛 쪽: 바깥(비가면)이 위 또는 왼쪽에 있는 칸
    up_out = np.roll(~m, 1, axis=0); up_out[0, :] = False
    left_out = np.roll(~m, 1, axis=1); left_out[:, 0] = False
    col(out, inner, dark)
    col(out, in2 & (np.roll(up_out, 1, 0) | np.roll(left_out, 1, 1)), light)
    return out


# ================================================================ 데칼
def _dither_blob(cx, cy, rx, ry, seed, dens=1.0, edge=0.35):
    n = pnoise(seed, 3, 3)
    d = np.sqrt(((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2) + (n - 0.5) * edge * 2
    th = bayer(T, T)
    return d < 1.0 - (1 - dens) * th, d


def d_crack(ramp, seed, n=2):
    out = empty()
    rng = np.random.default_rng(seed)
    for k in range(n):
        x, y = rng.uniform(16, 48), rng.uniform(16, 48)
        a = rng.uniform(0, 2 * np.pi)
        for t in range(int(rng.integers(18, 34))):
            a += rng.normal(0, 0.4)
            x += np.cos(a); y += np.sin(a)
            xi, yi = int(x), int(y)
            if 1 <= xi < T - 1 and 1 <= yi < T - 2:
                out[yi, xi] = (*ramp[0], 255)
                if out[yi + 1, xi, 3] == 0:
                    out[yi + 1, xi] = (*ramp[2], 255)
            if rng.random() < 0.08:
                b = a + rng.choice([-1, 1]) * 0.9
                bx, by = x, y
                for _ in range(int(rng.integers(4, 9))):
                    bx += np.cos(b); by += np.sin(b)
                    if 1 <= bx < T - 1 and 1 <= by < T - 1:
                        out[int(by), int(bx)] = (*ramp[1], 255)
    return out


def d_stain(c_dark, c_mid, seed, r=20):
    out = empty()
    m, d = _dither_blob(32, 34, r, r * 0.7, seed, dens=0.75)
    col(out, m & (d > 0.55), c_mid)
    col(out, m & (d <= 0.55) & (bayer(T, T) < 0.5), c_dark)
    return out


def d_puddle(ramp, glint, seed, r=18):
    """물·술 웅덩이: 짙은 몸 + 위쪽 테 빛 + 반짝 2점(위험물 아님 — 통과)."""
    out = empty()
    m, d = _dither_blob(32, 36, r, r * 0.55, seed, dens=1.0, edge=0.25)
    col(out, m, ramp[1])
    col(out, m & (d < 0.75), ramp[2])
    top = m & ~np.roll(m, 1, axis=0)
    col(out, top, ramp[3])
    rng = np.random.default_rng(seed)
    for _ in range(3):
        ys, xs = np.nonzero(m & (d < 0.6))
        if len(xs):
            i = rng.integers(len(xs))
            out[ys[i], xs[i]] = (*glint, 255)
            if xs[i] + 1 < T:
                out[ys[i], xs[i] + 1] = (*glint, 255)
    return out


def d_pebbles(ramp, seed, n=9):
    out = empty()
    rng = np.random.default_rng(seed)
    for _ in range(n):
        cx, cy = rng.uniform(10, 54), rng.uniform(10, 54)
        r = rng.uniform(1.4, 3.4)
        d = np.sqrt((XX - cx) ** 2 + ((YY - cy) * 1.3) ** 2)
        m = d <= r
        sh = ((XX - cx) * -0.6 + (YY - cy) * -0.8) / (d + 0.5)
        col(out, (d <= r + 1.2) & ~m & (YY > cy), ramp[0])
        col(out, m, ramp[2])
        col(out, m & (sh > 0.3), ramp[3])
        col(out, m & (sh < -0.5), ramp[1])
    return out


def d_strands(ramp, seed, n=40, spread=14, length=(5, 11), cx=32, cy=34):
    out = empty()
    rng = np.random.default_rng(seed)
    base = rng.uniform(0, np.pi)
    for _ in range(n):
        x, y = rng.normal(cx, spread), rng.normal(cy, spread * 0.7)
        a = base + rng.normal(0, 0.5)
        L = rng.integers(*length)
        c = ramp[rng.integers(2, len(ramp))]
        for t in range(L):
            xi, yi = int(x + np.cos(a) * t), int(y + np.sin(a) * t)
            if 0 <= xi < T and 0 <= yi < T - 1:
                out[yi, xi] = (*c, 255)
                if out[yi + 1, xi, 3] == 0:
                    out[yi + 1, xi] = (*ramp[0], 255)
    return out


def d_leaves(colors, seed, n=7):
    out = empty()
    rng = np.random.default_rng(seed)
    for _ in range(n):
        cx, cy = rng.uniform(8, 56), rng.uniform(8, 56)
        a = rng.uniform(0, np.pi)
        ca, sa = np.cos(a), np.sin(a)
        u = (XX - cx) * ca + (YY - cy) * sa
        v = -(XX - cx) * sa + (YY - cy) * ca
        m = (u / 4.2) ** 2 + (v / 2.2) ** 2 <= 1
        c = colors[rng.integers(len(colors))]
        col(out, m, c)
        col(out, m & (np.abs(v) < 0.6), colors[0])
    return out


def d_tuft(ramp, seed, n=3):
    """마른 풀 다발(황무지·외곽 틈): 아래 그늘 + 위로 뻗은 잎."""
    out = empty()
    rng = np.random.default_rng(seed)
    for _ in range(n):
        bx, by = rng.uniform(14, 50), rng.uniform(26, 54)
        col(out, ((XX - bx) / 6) ** 2 + ((YY - by) / 2) ** 2 <= 1, ramp[0])
        for k in range(9):
            a = -np.pi / 2 + rng.normal(0, 0.55)
            L = rng.integers(6, 13)
            c = ramp[rng.integers(2, len(ramp))]
            for t in range(L):
                xi, yi = int(bx + np.cos(a) * t + rng.normal(0, 0.2)), int(by + np.sin(a) * t)
                if 0 <= xi < T and 0 <= yi < T:
                    out[yi, xi] = (*c, 255)
    return out


def d_bones(c_bone, c_shadow, seed):
    out = empty()
    rng = np.random.default_rng(seed)
    for _ in range(3):
        cx, cy = rng.uniform(16, 48), rng.uniform(18, 48)
        a = rng.uniform(0, np.pi)
        L = rng.uniform(7, 13)
        for t in np.linspace(-L, L, 60):
            x, y = cx + np.cos(a) * t, cy + np.sin(a) * t
            r = 1.0 if abs(t) < L - 2 else 2.0
            m = (XX - x) ** 2 + (YY - y) ** 2 <= r * r
            col(out, np.roll(m, 1, 0) & (out[..., 3] == 0), c_shadow)
            col(out, m, c_bone)
    # 해골 1
    cx, cy = rng.uniform(22, 42), rng.uniform(24, 40)
    m = ((XX - cx) / 5) ** 2 + ((YY - cy) / 4.4) ** 2 <= 1
    col(out, np.roll(m, 2, 0), c_shadow)
    col(out, m, c_bone)
    for dx in (-2, 2):
        out[int(cy), int(cx + dx)] = (*c_shadow, 255)
    return out


def d_shards(colors, seed, n=8):
    out = empty()
    rng = np.random.default_rng(seed)
    for _ in range(n):
        cx, cy = rng.uniform(10, 54), rng.uniform(12, 54)
        pts = [(cx + rng.uniform(-4, 4), cy + rng.uniform(-3, 3)) for _ in range(3)]
        from PIL import Image, ImageDraw
        im = Image.new("L", (T, T), 0)
        ImageDraw.Draw(im).polygon(pts, fill=255)
        m = np.asarray(im) > 0
        col(out, m, colors[rng.integers(1, len(colors))])
        col(out, m & ~np.roll(m, 1, 0), colors[-1])
        col(out, np.roll(m, 1, 0) & ~m, colors[0])
    return out


def d_scorch(ramp, seed):
    out = empty()
    m, d = _dither_blob(32, 34, 24, 16, seed, dens=0.9, edge=0.5)
    col(out, m & (d > 0.65) & (bayer(T, T) < 0.5), ramp[1])
    col(out, m & (d <= 0.65), ramp[0])
    rng = np.random.default_rng(seed)
    for _ in range(10):
        a = rng.uniform(0, 2 * np.pi)
        for t in range(int(rng.integers(14, 26))):
            x, y = 32 + np.cos(a) * t, 34 + np.sin(a) * t * 0.7
            if 0 <= x < T and 0 <= y < T and bayer(T, T)[int(y), int(x)] < 0.6:
                out[int(y), int(x)] = (*ramp[1], 255)
    return out


def d_grate(c_dark, c_frame, c_light):
    """배수구 쇠살(바닥 홈)."""
    out = empty()
    m = (np.abs(XX - 32) <= 13) & (np.abs(YY - 33) <= 8)
    col(out, m, c_frame)
    col(out, (np.abs(XX - 32) <= 11) & (np.abs(YY - 33) <= 6), c_dark)
    for x in range(22, 44, 4):
        col(out, (np.abs(XX - x) <= 0.6) & (np.abs(YY - 33) <= 6), c_frame)
    col(out, m & (YY == 25), c_light)
    return out


def d_ruts(ramp, seed):
    """바퀴 자국 두 줄(가로)."""
    out = empty()
    n = pnoise(seed, 2, 2)
    for y0 in (22, 44):
        yc = y0 + (n[:, :] - 0.5) * 3
        m = np.abs(YY - yc) < 2.2
        col(out, m, ramp[1])
        col(out, np.abs(YY - (yc - 2.6)) < 0.6, ramp[3])
        col(out, np.abs(YY - (yc + 2.6)) < 0.6, ramp[0])
    return out


def d_streak(c, seed):
    """닳은 흐름(밝은 결) — 걸음이 많은 길 위."""
    out = empty()
    n = pnoise(seed, 2, 3)
    m = (np.abs(YY - 32 - (n - 0.5) * 16) < 9) & (bayer(T, T) < 0.22 + 0.25 * n)
    col(out, m, c)
    return out


def d_wax(c_wax, c_dark, seed):
    out = empty()
    rng = np.random.default_rng(seed)
    for _ in range(6):
        cx, cy = rng.uniform(12, 52), rng.uniform(12, 52)
        r = rng.uniform(1.5, 3.5)
        m = (XX - cx) ** 2 + ((YY - cy) * 1.3) ** 2 <= r * r
        col(out, np.roll(m, 1, 0) & ~m, c_dark)
        col(out, m, c_wax)
    return out


def d_inlay(c_line, c_dark):
    """잔(盞) 상감 띠 조각(연회장 대리석 위 호박 줄) — 가로 띠."""
    out = empty()
    col(out, np.abs(YY - 32) <= 1, c_line)
    col(out, np.abs(YY - 34) <= 0, c_dark)
    for x in range(4, 64, 16):
        col(out, (np.abs(XX - x) <= 2) & (np.abs(YY - 32) <= 3) & (np.abs(XX - x) + np.abs(YY - 32) <= 3), c_line)
    return out


# ================================================================ 벽 앞면·윗면
COURSES = [12, 14, 12, 14, 12]           # 64 도트 = 5줄 (아랫단·윗단 같은 규격 → 2칸 높이로 이어짐)
EDGE_SPLIT = [(10, 14), (22, 6), (6, 18), (18, 10), (14, 22)]   # 줄마다 칸 경계를 걸치는 돌: 왼쪽 칸 끝 c, 오른쪽 칸 앞 d


def masonry(seed, ramp, variant, base=0.55, tone=0.07, mortar_v=0.18, R=3.0, courses=COURSES, split=EDGE_SPLIT,
            rough=0.0):
    """벽 앞면 64×64: 줄 높이 고정, 경계 걸친 돌은 고정 그림, 안쪽 돌만 변형마다 다르게."""
    rng_fixed = np.random.default_rng(seed)
    rng_var = np.random.default_rng(seed + 1000 * (variant + 1))
    cid = np.zeros((T, T), np.int32)
    e = np.zeros((T, T), np.float32)
    tones = []
    y0, k = 0, 0
    for ci, ch in enumerate(courses):
        c, d = split[ci % len(split)]
        # 경계 걸친 돌: [64-c, 64) ∪ [0, d)  → 같은 id (tone 고정)
        t_fixed = rng_fixed.normal(0, tone)
        inner_l, inner_r = d, T - c
        joints = [inner_l]
        x = inner_l
        while True:
            wdt = int(rng_var.integers(14, 30))
            if x + wdt >= inner_r - 8:
                break
            x += wdt
            joints.append(x)
        joints.append(inner_r)
        for y in range(y0, y0 + ch):
            ly = min(y - y0, y0 + ch - 1 - y)
            # 걸친 돌
            for xx in list(range(0, d)) + list(range(T - c, T)):
                lx = min(xx + c, d - 1 - xx) if xx < d else min(xx - (T - c), (T - 1 - xx) + d)
                cid[y, xx] = k
                e[y, xx] = min(lx, ly)
        tones.append(t_fixed)
        k += 1
        for j in range(len(joints) - 1):
            a, b = joints[j], joints[j + 1]
            tv = rng_var.normal(0, tone)
            for y in range(y0, y0 + ch):
                ly = min(y - y0, y0 + ch - 1 - y)
                for xx in range(a, b):
                    cid[y, xx] = k
                    e[y, xx] = min(min(xx - a, b - 1 - xx), ly)
            tones.append(tv)
            k += 1
        y0 += ch
    tones = np.array(tones, np.float32)
    hgt = np.clip((e - 0.6) / R, 0, 1)
    hgt = 1 - (1 - hgt) ** 2
    gy, gx = np.gradient(hgt * R * 0.5)
    nx, ny, nz = -gx * 2.0, -gy * 2.0, np.ones_like(hgt)
    nn = np.sqrt(nx * nx + ny * ny + nz * nz)
    sh = (nx * L3[0] + ny * L3[1] + nz * L3[2]) / nn - L3[2]
    gr = pnoise(seed + 7, 8, 2) - 0.5          # 64 주기(변형 공통) — 경계 이음 보장
    v = base + tones[cid] + 0.5 * sh + 0.08 * gr
    if rough:
        v += rough * (pnoise(seed + 9, 4, 3) - 0.5)
    v = np.where(e < 0.6, mortar_v, v)
    return quant(v, ramp), e < 0.6


def front_tile(reg, seed, variant, upper, P):
    """벽 앞면 한 칸. P = 지역 벽 설정(dict)."""
    rgb, joint = masonry(seed + (50 if upper else 0), P["ramp"], variant, base=P.get("base", 0.55), rough=P.get("rough", 0.0))
    out = empty()
    put(out, rgb, np.ones((T, T), bool))
    if not upper:
        # 아랫단: 바닥 맞닿는 굽(받침돌) 6 + 바닥 접지 짙은 1
        col(out, YY >= T - 7, P["ramp"][1])
        col(out, (YY == T - 7), P["ramp"][3])
        col(out, YY >= T - 2, P["ramp"][0])
        # 아래쪽 습기·때(디더) — 벽이 땅에서 올라온 느낌
        gm = (YY > T - 20) & (YY < T - 7) & (bayer(T, T) < (YY - (T - 20)) / 26)
        col(out, gm, P["ramp"][1])
    else:
        # 윗단 맨 위: 처마·코니스 8 도트(빛 받는 윗면 1 + 그늘 2)
        col(out, YY < 8, P["cap"][2])
        col(out, YY < 2, P["cap"][3])
        col(out, (YY >= 8) & (YY < 11), P["ramp"][0])
    feat = P.get("feat_upper" if upper else "feat_lower", {}).get(variant)
    if feat:
        feat(out, seed + variant)
    return out


def front_end(P, side, upper):
    """벽 앞면 끝(모퉁이 돌) 덧칠 — side 'L'/'R'. 끝 6 도트 = 모서리 돌(밝은/어두운 면)."""
    out = empty()
    if side == "L":
        col(out, XX < 6, P["ramp"][4] if not upper or True else P["ramp"][4])
        col(out, XX < 1, P["ramp"][1])
        col(out, (XX == 6), P["ramp"][1])
        for y in range(0, T, 12):
            col(out, (XX < 6) & (YY == y), P["ramp"][2])
    else:
        col(out, XX > T - 7, P["ramp"][2])
        col(out, XX > T - 2, P["ramp"][0])
        col(out, XX == T - 7, P["ramp"][1])
        for y in range(6, T, 12):
            col(out, (XX > T - 7) & (YY == y), P["ramp"][1])
    if upper:
        col(out, (YY < 8) & ((XX < 6) if side == "L" else (XX > T - 7)), P["cap"][2])
    return out


def top_fill(P, variant, seed):
    return P["top"](variant, seed)


def top_edge(P, bits, seed, fill):
    """윗면 테(자동 타일): bits N=1,E=2,S=4,W=8 = 그 쪽이 벽이 아님 → 그 변을 마감."""
    out = fill.copy()
    t = P.get("edge_w", 5)
    cap = P["cap"]
    if bits & 1:
        col(out, YY < t, cap[2]); col(out, YY < 1, cap[3]); col(out, YY == t, cap[0])
    if bits & 8:
        col(out, XX < t, cap[2]); col(out, XX < 1, cap[3]); col(out, XX == t, cap[0])
    if bits & 2:
        col(out, XX > T - 1 - t, cap[1]); col(out, XX > T - 2, cap[0]); col(out, XX == T - 1 - t, cap[2])
    if bits & 4:
        col(out, YY > T - 1 - t, cap[1]); col(out, YY > T - 2, cap[0])
    if P.get("crenel") and bits:
        P["crenel"](out, bits)
    return out


def top_above_front(P, fill):
    """처마(윗면 남쪽 끝이 앞면 윗단과 만나는 칸): 아래 8 도트 = 앞으로 내민 처마 그늘."""
    out = fill.copy()
    cap = P["cap"]
    col(out, YY > T - 7, cap[1])
    col(out, YY == T - 7, cap[3])
    col(out, YY > T - 2, cap[0])
    return out


# ================================================================ 낙하 구역
def water_fill(ramp, glint, frame, nframes, seed, size=128):
    """물(또는 술) 128×128 주기 × nframes — 잔잔한 물결 무늬(짧은 빛 줄이 흐름) + 깊이 얼룩. 대비 낮게."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    ph = frame / nframes
    deep = fbm(size, size, 2, 3, seed)
    v = 0.42 + 0.14 * (deep - 0.5)
    # 물결 빛: 가로로 짧은 줄(노이즈 위상), 프레임마다 오른쪽으로 흐름(주기 이음)
    n = fbm(size, size, 4, 2, seed + 5, aspect=3.0)
    wave = np.sin(2 * np.pi * (yy / size * 10 + n * 2.0 + ph))
    streak = (wave > 0.86) & (np.sin(2 * np.pi * (xx / size * 4 - ph + n * 1.5)) > 0.1)
    trough = (wave < -0.9) & (np.sin(2 * np.pi * (xx / size * 3 + ph + n)) > 0.3)
    v = np.where(streak, v + 0.2, v)
    v = np.where(trough, v - 0.1, v)
    rgb = quant(v, ramp, sharp=6.0)
    gl = streak & (np.sin(2 * np.pi * (xx / size * 8 - 2 * ph + n * 3)) > 0.93)
    rgb[gl] = glint
    return rgb


def _wrapd(a, c, size):
    return ((a - c + size / 2) % size) - size / 2


def chasm_fill(kind, seed, size=256):
    """낭떠러지 아래 풍경(검정 void 금지, 대비 낮게 — '멀리' 읽히게).
    city = 아득히 아래 성 밑 마을(작은 지붕 + 창 불빛 + 가로 안개 줄), ravine = 마른 골짜기(바위 비탈 + 먼지 안개)."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    rng = np.random.default_rng(seed)
    if kind == "city":
        v = 0.42 + 0.10 * (fbm(size, size, 2, 3, seed) - 0.5)
        rgb = quant(v, [NT[2], SL[1], SL[2], SL[3], SL[4]], sharp=6.0)
        for _ in range(48):
            cx, cy = rng.uniform(0, size), rng.uniform(0, size)
            w, h = rng.integers(10, 22), rng.integers(6, 10)
            dx, dy = _wrapd(xx, cx, size), _wrapd(yy, cy, size)
            body = (np.abs(dx) <= w / 2) & (dy >= 0) & (dy <= h)
            roof = (np.abs(dx) <= w / 2 + 1) & (dy < 0) & (dy >= -h * 0.7 + np.abs(dx) * 0.25)
            rgb[body] = SL[1]
            rgb[roof] = SL[3]
            rgb[roof & (dy > -2)] = SL[2]
            rgb[roof & (dx < -w / 4) & (dy < -2)] = SL[4]
            if rng.random() < 0.6:
                wx, wy = int(cx + rng.integers(-w // 3, w // 3 + 1)) % size, int(cy + h // 2) % size
                rgb[wy, wx] = A[23]
                rgb[wy, (wx + 1) % size] = A[22]
        mist = fbm(size, size, 2, 3, seed + 9, aspect=4.0)
        band = (mist > 0.56) & ((bayer(size, size) < (mist - 0.56) * 4))
        rgb[band] = SL[4]
        return rgb
    v = 0.45 + 0.14 * (fbm(size, size, 3, 4, seed) - 0.5)
    rgb = quant(v, [WD[1], WD[2], WD[3], PL[0]], sharp=6.0)
    for _ in range(40):
        cx, cy = rng.uniform(0, size), rng.uniform(0, size)
        r = rng.uniform(4, 11)
        dx, dy = _wrapd(xx, cx, size), _wrapd(yy, cy, size) * 1.5
        d = np.sqrt(dx * dx + dy * dy)
        m = d < r
        rgb[m] = WD[2]
        rgb[m & (dx + dy < -r * 0.3)] = PL[0]
        rgb[m & (dx + dy > r * 0.6)] = WD[1]
        rgb[(d >= r) & (d < r + 1.5) & (dy > 0)] = WD[0]
    mist = fbm(size, size, 2, 3, seed + 9, aspect=4.0)
    band = (mist > 0.55) & ((bayer(size, size) < (mist - 0.55) * 4))
    rgb[band] = PL[1]
    return rgb


def bank_tile(bits, D, seed):
    """낙하 칸 둑(자동 타일): bits N=1,E=2,S=4,W=8 = 그 쪽 이웃이 땅. D = 지역 낙하 설정."""
    out = empty()
    fh = D["face_h"]
    face = D["face"]                     # (T, fh, 3) 앞면 그림 (가로 64 주기)
    if bits & 1:
        put(out, np.pad(face, ((0, T - fh), (0, 0), (0, 0))), YY < fh)
        # 수면/안개 경계: 짙은 젖은 줄 + 반사 빛
        col(out, YY == fh, D["waterline"][0])
        col(out, (YY == fh + 1) & (bayer(T, T) < 0.5), D["waterline"][1])
    cw = D["curb_w"]
    curb = D["curb"]
    y_top = fh if bits & 1 else 0
    if bits & 8:
        col(out, (XX < cw) & (YY >= y_top), curb[2])
        col(out, (XX == cw - 1) & (YY >= y_top), curb[3])
        col(out, (XX == cw) & (YY >= y_top) & (bayer(T, T) < 0.6), D["waterline"][0])
    if bits & 2:
        col(out, (XX > T - 1 - cw) & (YY >= y_top), curb[1])
        col(out, (XX == T - cw) & (YY >= y_top), curb[0])
        col(out, (XX == T - 1 - cw) & (YY >= y_top), D["waterline"][0])
    if bits & 4:
        col(out, YY > T - 1 - cw, curb[2])
        col(out, YY == T - cw, curb[3])
        col(out, (YY == T - 1 - cw) & (bayer(T, T) < 0.7), D["waterline"][0])
        if bits & 8:
            col(out, (XX < cw) & (YY > T - 1 - cw), curb[2])
    if (bits & 1) and (bits & 8):
        col(out, (XX < cw) & (YY < fh), D["face_side"])
    if (bits & 1) and (bits & 2):
        col(out, (XX > T - 1 - cw) & (YY < fh), D["face_side"])
    return out


def inner_corner(which, D):
    """대각선만 땅인 모서리 조각 — which: 'nw','ne','sw','se'."""
    out = empty()
    cw, fh = D["curb_w"], D["face_h"]
    curb = D["curb"]
    if which in ("nw", "ne"):
        xm = (XX < cw) if which == "nw" else (XX > T - 1 - cw)
        put(out, np.pad(D["face"], ((0, T - fh), (0, 0), (0, 0))), xm & (YY < fh))
        col(out, xm & (YY < fh) & ((XX == cw - 1) if which == "nw" else (XX == T - cw)), D["face_side"])
        col(out, xm & (YY == fh), D["waterline"][0])
    else:
        xm = (XX < cw) if which == "sw" else (XX > T - 1 - cw)
        col(out, xm & (YY > T - 1 - cw), curb[2])
        col(out, xm & (YY == T - cw), curb[3])
    return out


# ================================================================ 다리·난간
def plank_deck(ramp, seed, vertical_boards, w=T, h=T):
    """널 판 바닥 64×64. vertical_boards=True 면 세로 널(가로 다리)."""
    rng = np.random.default_rng(seed)
    a = XX if vertical_boards else YY
    bw = 9
    idx = (a // bw).astype(int)
    tones = rng.normal(0, 0.06, 16)
    gr = pnoise(seed + 3, 8, 2) - 0.5
    v = 0.55 + tones[idx] + 0.07 * gr
    lx = a % bw
    v = np.where(lx == 0, 0.15, v)
    v = np.where(lx == 1, v + 0.12, v)
    v = np.where(lx == bw - 1, v - 0.1, v)
    rgb = quant(v, ramp)
    # 못
    b = YY if vertical_boards else XX
    nails = ((lx == 4) & ((b == 10) | (b == 53)))
    rgb[nails] = ramp[0]
    return rgb


def bridge_tile(kind, end, D, seed):
    """kind 'h'(동서로 건넘)/'v'(남북). end: None/'W'/'E'/'N'/'S'. 다리는 물 위(물 채움 위에 그림)."""
    out = empty()
    ramp = D["wood"]
    if kind == "h":
        deck = plank_deck(ramp, seed, True)
        m = (YY >= 8) & (YY < T - 6)
        put(out, deck, m)
        # 위·아래 난간(위 = 뒤 난간 낮게, 아래 = 앞 난간 + 그늘)
        col(out, (YY >= 4) & (YY < 8), ramp[3]); col(out, YY == 4, ramp[5])
        col(out, (YY >= T - 6) & (YY < T - 3), ramp[2]); col(out, YY == T - 6, ramp[4]); col(out, YY >= T - 3, ramp[0])
        for x in (4, 36):
            col(out, (np.abs(XX - x) <= 2) & (YY < 9), ramp[2]); col(out, (XX == x - 2) & (YY < 9), ramp[4])
            col(out, (np.abs(XX - x) <= 2) & (YY >= T - 12), ramp[1]); col(out, (XX == x - 2) & (YY >= T - 12), ramp[3])
        col(out, (YY == T - 1) & (XX % 3 == 0), D["waterline"][0])
        if end in ("W", "E"):
            xm = (XX < 12) if end == "W" else (XX > T - 13)
            put(out, D["abut"], xm)
    else:
        deck = plank_deck(ramp, seed, False)
        m = (XX >= 7) & (XX < T - 7)
        put(out, deck, m)
        col(out, (XX >= 3) & (XX < 7), ramp[4]); col(out, XX == 3, ramp[5])
        col(out, (XX >= T - 7) & (XX < T - 3), ramp[2]); col(out, XX >= T - 3, ramp[0])
        for y in (6, 38):
            col(out, (np.abs(YY - y) <= 3) & ((XX < 8) | (XX >= T - 8)), ramp[2])
            col(out, (YY == y - 3) & ((XX < 8) | (XX >= T - 8)), ramp[5])
        if end in ("N", "S"):
            ym = (YY < 12) if end == "N" else (YY > T - 13)
            put(out, D["abut"], ym)
    return out


def railing(kind, R, seed):
    """난간(땅 칸 가장자리 덧그림). kind: s/n/w/e/s_broken/post. R = 지역 난간 설정."""
    out = empty()
    ramp = R["ramp"]
    rng = np.random.default_rng(seed)
    if kind in ("s", "s_broken", "n"):
        y_base = T - 2 if kind != "n" else 16
        hgt = R["h"]
        yt = y_base - hgt
        posts = [6, 32, 58] if kind != "s_broken" else [6, 58]
        for x in posts:
            col(out, (np.abs(XX - x) <= R["post_w"]) & (YY > yt - 2) & (YY <= y_base), ramp[2])
            col(out, (XX == x - R["post_w"]) & (YY > yt - 2) & (YY <= y_base), ramp[4])
            col(out, (XX == x + R["post_w"]) & (YY > yt - 2) & (YY <= y_base), ramp[0])
            col(out, (np.abs(XX - x) <= R["post_w"] + 1) & (YY >= yt - 3) & (YY <= yt - 1), ramp[5])
        if kind == "s_broken":
            col(out, (YY >= yt) & (YY < yt + 3) & (XX < 18), ramp[3])
            col(out, (YY == yt) & (XX < 18), ramp[5])
            col(out, (YY >= yt + 2) & (YY < yt + 5) & (XX > 46), ramp[3])
            for k in range(6):
                x = int(rng.uniform(20, 44)); y = int(rng.uniform(y_base - 4, y_base))
                col(out, (np.abs(XX - x) <= 1) & (YY == y), ramp[3])
        else:
            for yy_ in (yt, yt + hgt // 2):
                col(out, (YY >= yy_) & (YY < yy_ + 3), ramp[3])
                col(out, YY == yy_, ramp[5])
                col(out, (YY == yy_ + 3), ramp[0])
        if R.get("baluster") and kind != "s_broken":
            for x in range(10, 56, 6):
                if all(abs(x - p) > 4 for p in posts):
                    col(out, (np.abs(XX - x) <= 1) & (YY > yt + 2) & (YY <= y_base), ramp[3])
                    col(out, (XX == x - 1) & (YY > yt + 2) & (YY <= y_base), ramp[4])
    elif kind in ("w", "e"):
        x0 = 4 if kind == "w" else T - 6
        col(out, (XX >= x0) & (XX < x0 + 3), ramp[3])
        col(out, XX == x0, ramp[5])
        for y in (4, 36):
            col(out, (np.abs(XX - (x0 + 1)) <= 2) & (np.abs(YY - y) <= 2), ramp[2])
            col(out, (np.abs(XX - (x0 + 1)) <= 2) & (YY == y - 2), ramp[5])
    else:
        x = 32
        y_base = T - 2
        col(out, (np.abs(XX - x) <= 3) & (YY > y_base - R["h"] - 2) & (YY <= y_base), ramp[2])
        col(out, (XX == x - 3) & (YY > y_base - R["h"] - 2), ramp[4])
        col(out, (np.abs(XX - x) <= 4) & (YY >= y_base - R["h"] - 4) & (YY <= y_base - R["h"] - 2), ramp[5])
    return out


# ================================================================ 높은 단·계단
def lip_tile(bits, Tz):
    """높은 단(^) 칸 테. bits N=1,E=2,S=4,W=8 = 그 쪽이 낮은 땅. 남쪽 = 앞면 위 갓돌(밝은 윗선 + 내민 모서리)."""
    out = empty()
    c = Tz["cap"]
    if bits & 1:
        col(out, YY < 2, c[0]); col(out, YY == 2, c[3])
    if bits & 8:
        col(out, XX < 4, c[1]); col(out, XX == 0, c[0]); col(out, XX == 4, c[3])
    if bits & 2:
        col(out, XX > T - 5, c[1]); col(out, XX == T - 1, c[0])
    if bits & 4:
        col(out, YY > T - 9, c[3])
        col(out, (YY > T - 9) & (bayer(T, T) < 0.3), c[2])
        col(out, YY == T - 9, c[4])
        col(out, YY == T - 8, c[4])
        col(out, YY > T - 3, c[2])
        col(out, YY == T - 1, c[1])
        for x in range(0, T, 16):                      # 갓돌 이음
            col(out, (XX == x) & (YY > T - 9), c[1])
    return out


def face_tile(end, Tz, seed):
    """낮은 칸 위쪽에 드리운 높은 단 앞면(높이 face_h) + 갓돌 밑 그늘 + 아래 낮은 땅에 떨어지는 그림자(남동, 12 도트 디더).
    end: None/'L'/'R'/'LR'(옆 끝 모퉁이)."""
    out = empty()
    fh = Tz["face_h"]
    rgb, joint = masonry(seed, Tz["ramp"], 0, base=0.62, courses=[9, 10, 10, 11, 24], split=EDGE_SPLIT)
    put(out, rgb, YY < fh)
    # 위 → 아래 어두워짐(디더) — 높이 읽힘
    for y in range(fh):
        k = y / fh
        col(out, (YY == y) & (bayer(T, T) < k * 0.45) & ~joint, Tz["ramp"][2])
    col(out, YY < 3, Tz["ramp"][0])                   # 갓돌 밑 그늘
    col(out, (YY >= fh - 4) & (YY < fh), Tz["ramp"][1])
    col(out, YY == fh - 4, Tz["ramp"][3])
    # 떨어지는 그림자
    sh = (YY >= fh) & (YY < fh + 12) & (bayer(T, T) < 0.75 - (YY - fh) * 0.06)
    col(out, sh, Tz["shadow"])
    if end in ("L", "LR"):
        col(out, (XX < 5) & (YY < fh), Tz["ramp"][4]); col(out, (XX == 5) & (YY < fh), Tz["ramp"][1])
        col(out, (XX < 5) & (YY >= fh), 0) if False else None
    if end in ("R", "LR"):
        col(out, (XX > T - 6) & (YY < fh), Tz["ramp"][1]); col(out, (XX == T - 1) & (YY < fh), Tz["ramp"][0])
        col(out, (XX > T - 6) & (YY >= fh) & (YY < fh + 12) & (bayer(T, T) < 0.5), Tz["shadow"])
    return out


def stair_tile(end, Tz, seed, dirn="S"):
    """계단(높은 단 → 낮은 땅). dirn 'S' = 남쪽으로 내려감(앞면 자리, 위 face_h 도트에 디딤 5단).
    'E'/'W' = 옆으로 내려감(칸 전체)."""
    out = empty()
    r = Tz["step"]
    fh = Tz["face_h"]
    if dirn == "S":
        n = 5
        sh_ = fh // n
        for k in range(n):
            y0 = k * sh_
            col(out, (YY >= y0) & (YY < y0 + 3), r[4])               # 디딤 앞 모서리 빛
            col(out, (YY >= y0 + 3) & (YY < y0 + sh_), r[2])          # 챌면
            col(out, (YY == y0 + sh_ - 1), r[1])
            col(out, (YY >= y0 + 3) & (YY < y0 + sh_) & (bayer(T, T) < 0.2), r[3])
        col(out, (YY >= fh) & (YY < fh + 12) & (bayer(T, T) < 0.75 - (YY - fh) * 0.06), Tz["shadow"])
        if end in ("L", "LR"):
            col(out, (XX < 5) & (YY < fh + 2), Tz["ramp"][3]); col(out, (XX == 5) & (YY < fh + 2), Tz["ramp"][0])
            col(out, (XX < 5) & (YY < 3), Tz["cap"][3])
        if end in ("R", "LR"):
            col(out, (XX > T - 6) & (YY < fh + 2), Tz["ramp"][2]); col(out, (XX == T - 6) & (YY < fh + 2), Tz["ramp"][0])
            col(out, (XX > T - 6) & (YY < 3), Tz["cap"][3])
    else:
        n = 6
        sw = T // n
        for k in range(n):
            x0 = k * sw if dirn == "E" else T - (k + 1) * sw
            col(out, (XX >= x0) & (XX < x0 + sw), r[3 - (k % 2)])
            edge = (XX == x0 + sw - 1) if dirn == "E" else (XX == x0)
            col(out, edge, r[1])
            col(out, (XX >= x0) & (XX < x0 + sw) & (YY < 3), r[4])
        col(out, YY > T - 4, Tz["ramp"][1])
        col(out, YY < 2, Tz["cap"][3])
    return out
