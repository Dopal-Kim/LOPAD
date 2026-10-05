"""60라운드 Q8 — 적 3종 공용 타격 연출(몸 렌더 뒤 post): 휘두름 잔상 · 바닥 금 · 술/파편 튐. 반투명 없음.

drunk60(징집병)·musket60(사수)·bulwark60(결사병)이 import 한다.
"""
import math

from erig import add, mul, norm, lerp3, G, A, SL, WD, PL


def ground_crack(B, tip_fr, k, scale=1.0):
    """D4 내리꽂기: 곤봉 끝 주변 바닥 금(빈 픽셀에만) — k = 1(짧음)·2(뻗음)."""
    gx, gy = B.proj((tip_fr[0], tip_fr[1], 0.0))
    rays = [(-1.0, 0.25, 6), (1.0, 0.3, 7), (-0.6, 0.55, 4), (0.7, 0.6, 5), (0.1, 0.7, 3)]

    def post(im, gx=gx, gy=gy, k=k):
        px = im.load()
        W, Hh = im.size
        for dx, dy, L in rays:
            L = int(L * (0.7 + 0.5 * k) * scale)
            x, y = gx, gy + 1
            for i in range(L):
                x += dx
                y += dy * 0.6 + (0.4 if i % 3 == 2 else 0.0)
                xi, yi = int(round(x)), int(round(y))
                if 0 <= xi < W and 0 <= yi < Hh and px[xi, yi][3] == 0:
                    px[xi, yi] = (WD[0] if i < L - 2 else WD[1]) if True else None
                    if i < 2 and 0 <= yi + 1 < Hh and px[xi, yi + 1][3] == 0:
                        px[xi, yi + 1] = PL[0]
    B.post.append(post)


def smear(B, hand, dirs, cd_now, L=29.0, t0=0.55, ok=("barrel", "shirt", "pants", "rope", "arm"), skip=("arm_skin",),
          cols=None):
    """D4 휘두름 잔상: 손 기준 곤봉 방향 dirs[0] → 현재까지의 호를 띠 3겹(다각형 채움)으로.
    바깥 G12 · 가운데 PL4 · 안쪽 PL3, 오래된 끝(t=0)으로 갈수록 안쪽 반지름이 커져 가늘어진다. 반투명 없음.
    빈 픽셀 + 몸통(술통·셔츠·바지) 위에 칠한다(머리·모자·손·곤봉은 가리지 않음) — 정면·뒷면에서도 호가 읽히게."""
    from PIL import Image as _I, ImageDraw as _D
    d0, d1 = norm(dirs[0]), norm(cd_now)
    N = 24
    # 2회차 비평: 머리 뒤를 지나는 앞쪽 절반은 머리에 가려 '뿔'처럼 두 동강 → 최근 쪽 45%만(머리 앞 호)
    T0 = t0
    k = L / 29.0                       # 기준(징집병 곤봉 29) 대비 길이 배율
    cols = cols or (G[12], PL[4], PL[3])

    def arc(rf, t0=0.0):
        pts = []
        for i in range(N + 1):
            t = t0 + (1 - t0) * i / N
            d = norm(lerp3(d0, d1, t))
            pts.append((t, B.proj(add(hand, mul(d, rf(t))))))
        return pts
    bands = [  # (바깥 반지름 함수, 안쪽 반지름 함수, 색)
        (lambda t: 29.0 * k, lambda t: (26.0 + (1 - t) * 2.0) * k, cols[0]),
        (lambda t: (26.0 + (1 - t) * 2.0) * k, lambda t: (21.0 + (1 - t) * 4.0) * k, cols[1]),
        (lambda t: (21.0 + (1 - t) * 4.0) * k, lambda t: (15.0 + (1 - t) * 10.0) * k, cols[2]),
    ]
    W, Hh = B.W, B.H
    layers = []
    for ro, ri, col in bands:
        o = [p for _, p in arc(ro, T0)]
        i = [p for _, p in arc(ri, T0)][::-1]
        m = _I.new("L", (W, Hh), 0)
        _D.Draw(m).polygon([(round(x), round(y)) for x, y in o + i], fill=255)
        layers.append((m, col))
    OK = tuple(ok)
    SKIP = tuple(skip)

    def post(im, layers=layers):
        px = im.load()
        R = B.R
        cover = set()
        for m, col in layers:
            mp = m.load()
            for y in range(Hh):
                for x in range(W):
                    if not mp[x, y]:
                        continue
                    if px[x, y][3] == 0:
                        px[x, y] = col
                        cover.add((x, y))
                    else:
                        i = R.owner[y][x]
                        if i >= 0 and not R.outline[y][x] and R.parts[i].name.startswith(OK) and not R.parts[i].name.startswith(SKIP):
                            px[x, y] = col
                            cover.add((x, y))
        for (x, y) in list(cover):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if (xx, yy) not in cover and 0 <= xx < W and 0 <= yy < Hh and px[xx, yy][3] == 0:
                    px[xx, yy] = SL[0]
    B.post.append(post)


def slosh(B, mouth, k):
    """D4·D5 병 주둥이에서 튀는 술 방울(빈 픽셀만, 호박 램프): k = 1·2 단계."""
    mx, my = B.proj(mouth)
    drops = [(-3, -4, A[21]), (-5, -2, A[20]), (2, -5, A[22]), (-7, 1, A[19]), (4, -2, A[20]), (-2, -7, A[21])]

    def post(im, k=k):
        px = im.load()
        W, Hh = im.size
        for i, (dx, dy, c) in enumerate(drops[:3 + 2 * k]):
            x, y = int(round(mx + dx * k * 0.9)), int(round(my + dy * k * 0.8 + (k - 1) * 3))
            for (ox, oy) in ((0, 0), (0, 1)) if i % 2 == 0 else ((0, 0),):
                if 0 <= x + ox < W and 0 <= y + oy < Hh and px[x + ox, y + oy][3] == 0:
                    px[x + ox, y + oy] = c if oy == 0 else A[18]
    B.post.append(post)


