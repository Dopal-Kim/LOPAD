"""props v3 공용 도구 (53라운드 Q12) — 2배 밀도(pixelScale 0.5) 소품을 빠르게 그리기 위한 셰이딩 도구.

- 팔레트: v2_outer/kit.py 의 G(무채 16)·A(1층 램프 16~27)·SL·WD·PL·NT 만 쓴다(새 색 없음).
- 빛: 좌상단 앞(바이블·v2 와 같음). L = (-0.5, -0.6, 0.62) (x 오른쪽, y 아래, z 화면 쪽).
- 형태: 마스크(L 이미지)를 그린 뒤 높이장(흐린 마스크)의 기울기로 법선을 만들어 램프 칸을 고른다(shade_mask).
  원통(술통)·상자 면은 해석적 법선으로(cyl, face).
- 램프 사이 경계만 좁게 4×4 바이어 디더(sharp 로 폭 조절) — 2배 밀도에서 부드럽게 보이되 잡점은 만들지 않음.
- 단위: 도트(1 도트 = 논리 0.5px). 64 도트 = 타일 1칸.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../v2_outer"))
from kit import G, A, SL, WD, PL, NT, X, EMISSIVE, Canvas, Rand, CLEAR, hx, tohex  # noqa: E402,F401

U = 64                      # 타일 1칸 = 64 도트
L = (-0.5, -0.6, 0.62)
_ln = math.sqrt(sum(v * v for v in L))
L = tuple(v / _ln for v in L)
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
CONTACT = (10, 11, 16, 110)

# 재질 램프 (어두움 → 밝음)
R_WOOD = [WD[0], WD[1], WD[2], WD[3], WD[4], WD[5]]
R_WOODG = [SL[0], WD[1], WD[2], PL[0], PL[1], PL[2]]            # 낡아 회색으로 바랜 나무
R_IRON = [SL[0], G[2], G[3], G[4], G[6], G[8]]
R_STONE = [SL[0], SL[1], SL[2], SL[3], SL[4], SL[5], SL[6]]
R_NSTONE = [G[1], G[2], G[3], G[4], G[5], G[6], G[7]]             # 중립 돌(연회장·성문)
R_WSTONE = [SL[0], G[2], G[3], PL[0], PL[1], PL[2], PL[3]]        # 따뜻한 돌(황무지)
R_CLOTH = [SL[1], PL[0], PL[1], PL[2], PL[3], PL[4]]
R_CLOTHG = [SL[0], G[3], G[5], G[6], G[8], G[10]]
R_EARTH = [SL[0], WD[1], WD[2], PL[0], WD[4], PL[1]]
R_COPPER = [A[16], A[17], A[18], A[19], A[20], A[22]]             # 구리(증류기) — 층 램프(스왑 대상)
R_LIQ = [A[17], A[18], A[19], A[20], A[21], A[22]]                # 술(비발광)
R_BONE = [SL[1], PL[0], PL[2], PL[3], PL[4], G[12]]
FLAME = [A[22], A[23], A[24], A[25], A[26], A[27]]                # 불꽃(23~27 은 자체 발광)


def clamp(v, a=0.0, b=1.0):
    return a if v < a else (b if v > b else v)


def qcol(ramp, s, x, y, sharp=3.0):
    """s(0..1) → 램프 색. 칸 경계만 디더."""
    n = len(ramp)
    v = clamp(s) * (n - 1)
    i = int(v)
    if i >= n - 1:
        return ramp[-1]
    f = clamp((v - i - 0.5) * sharp + 0.5)
    th = (BAYER[y % 4][x % 4] + 0.5) / 16
    return ramp[i + 1] if f > th else ramp[i]


def lam(nx, ny, nz):
    return nx * L[0] + ny * L[1] + nz * L[2]


def new(w, h):
    return Canvas(w, h)


def mask(w, h):
    m = Image.new("L", (w, h), 0)
    return m, ImageDraw.Draw(m)


def shade_mask(c, m, ramp, base=0.45, gain=0.55, soft=4, ox=0, oy=0, sharp=3.0, only_empty=False, rim=True,
               tilt=0.0, ao=0.0):
    """마스크 m 영역을 높이장 법선으로 셰이딩해 c 의 (ox,oy) 에 그린다.
    tilt: 위쪽(작은 y)일수록 밝게(+) — 윗면이 하늘을 보는 덩어리 느낌. ao: 가장자리 어둡힘."""
    w, h = m.size
    hf = m.filter(ImageFilter.GaussianBlur(soft)) if soft else m
    hp, mp = hf.load(), m.load()
    ys = [y for y in range(h) for x in range(w) if mp[x, y] > 127]
    if not ys:
        return
    y0, y1 = min(ys), max(ys)
    for y in range(h):
        for x in range(w):
            if mp[x, y] <= 127:
                continue
            if only_empty and c.get(ox + x, oy + y)[3]:
                continue
            gx = (hp[min(w - 1, x + 1), y] - hp[max(0, x - 1), y]) / 255.0
            gy = (hp[x, min(h - 1, y + 1)] - hp[x, max(0, y - 1)]) / 255.0
            nx, ny, nz = -gx * 2.2, -gy * 2.2, 1.0
            nl = math.sqrt(nx * nx + ny * ny + nz * nz)
            s = base + gain * (lam(nx / nl, ny / nl, nz / nl) - L[2])
            if tilt:
                s += tilt * (0.5 - (y - y0) / max(1, y1 - y0))
            if ao:
                s -= ao * (1 - hp[x, y] / 255.0)
            c.px(ox + x, oy + y, qcol(ramp, s, ox + x, oy + y, sharp))
    if rim:
        outline(c, m, ramp, ox, oy)


def outline(c, m, ramp, ox=0, oy=0, dark=None):
    """선택적 외곽선: 아래·오른쪽 가장자리 = 램프 0, 위·왼쪽 = 램프 1 (빛 쪽은 덜 진하게)."""
    w, h = m.size
    mp = m.load()
    d0 = dark or ramp[0]
    for y in range(h):
        for x in range(w):
            if mp[x, y] <= 127:
                continue
            edge_br = (x + 1 >= w or mp[x + 1, y] <= 127) or (y + 1 >= h or mp[x, y + 1] <= 127)
            edge_tl = (x - 1 < 0 or mp[x - 1, y] <= 127) or (y - 1 < 0 or mp[x, y - 1] <= 127)
            if edge_br:
                c.px(ox + x, oy + y, d0)
            elif edge_tl:
                cur = c.get(ox + x, oy + y)
                # 빛 쪽 외곽: 현재보다 한 단 어둡게
                if cur in ramp:
                    k = ramp.index(cur)
                    c.px(ox + x, oy + y, ramp[max(1, k - 1)])


def contact(c, cx, cy, rx, ry, a=110):
    """바닥 접지 그림자(반투명). 이미 칠한 픽셀은 건드리지 않는다."""
    for y in range(int(cy - ry), int(cy + ry) + 1):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            d = ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2
            if d <= 1 and c.get(x, y)[3] == 0:
                al = int(a * (0.55 + 0.45 * (1 - d)))
                c.px(x, y, (CONTACT[0], CONTACT[1], CONTACT[2], al))


def cyl(c, cx, top, bot, rx, ramp, bulge=0.0, ry=None, staves=0, hoops=(), hoop_ramp=None, seed=1,
        lid=True, lid_ramp=None, sharp=3.0):
    """세운 원통(술통·통·기둥). 3/4 시점: 윗면 타원 반높이 ry(기본 rx*0.42). top = 윗면 타원 중심 y, bot = 밑면 타원 중심 y."""
    ry = ry or max(2, int(rx * 0.42))
    hoop_ramp = hoop_ramp or R_IRON
    lid_ramp = lid_ramp or ramp
    r = Rand(seed)

    def rx_at(y):
        t = (y - top) / max(1, bot - top)
        return rx * (1 + bulge * math.sin(math.pi * clamp(t)))
    # 몸통(밑면 타원 아래 반까지)
    for y in range(top, bot + ry + 1):
        rr = rx_at(min(y, bot))
        for x in range(int(cx - rr - 1), int(cx + rr + 2)):
            u = (x + 0.5 - cx) / rr
            if abs(u) > 1:
                continue
            # 밑면 타원 바깥(아래 둥근 끝) 자르기
            if y > bot:
                if ((y - bot) / ry) ** 2 + u * u > 1:
                    continue
            nz = math.sqrt(max(0.0, 1 - u * u))
            t = (min(y, bot) - top) / max(1, bot - top)
            ny = -bulge * 2.2 * math.cos(math.pi * clamp(t)) * 0.5
            nl = math.sqrt(u * u + ny * ny + nz * nz)
            s = 0.42 + 0.62 * (lam(u / nl, ny / nl, nz / nl) - 0.15)
            col = qcol(ramp, s, x, y, sharp)
            c.px(x, y, col)
    # 널(세로 틈) — 원통 둘레 등각 위치
    if staves:
        for k in range(staves):
            th = -math.pi / 2 + math.pi * (k + 0.5) / staves
            u = math.sin(th)
            for y in range(top + 1, bot + ry):
                rr = rx_at(min(y, bot))
                x = int(round(cx + u * rr))
                if y > bot and ((y - bot) / ry) ** 2 + u * u > 1:
                    continue
                cur = c.get(x, y)
                if cur[3] and cur in ramp:
                    c.px(x, y, ramp[max(0, ramp.index(cur) - 1)])
                    if r.f() < 0.05:
                        c.px(x + (1 if u < 0 else -1), y, ramp[max(0, ramp.index(cur) - 1)])
    # 쇠테 — 3/4 시점에서 아래로 휜 곡선
    for (hy, hw) in hoops:
        for x in range(int(cx - rx * (1 + bulge) - 2), int(cx + rx * (1 + bulge) + 3)):
            rr = rx_at(hy)
            u = (x + 0.5 - cx) / rr
            if abs(u) > 1:
                continue
            yy = hy + int(round(ry * math.sqrt(max(0, 1 - u * u)) * 0.9))
            nz = math.sqrt(max(0, 1 - u * u))
            s = 0.45 + 0.6 * (lam(u, -0.2, nz) - 0.2)
            for k in range(hw):
                c.px(x, yy + k, qcol(hoop_ramp, s - 0.12 * k, x, yy + k, sharp))
            c.px(x, yy - 1, qcol(hoop_ramp, s + 0.25, x, yy - 1, sharp) if u < 0.2 else hoop_ramp[2])
            c.px(x, yy + hw, ramp[1] if c.get(x, yy + hw)[3] else CLEAR)
        # 리벳
        for u in (-0.55, 0.15):
            x = int(cx + u * rx_at(hy))
            yy = hy + int(round(ry * math.sqrt(1 - u * u) * 0.9))
            c.px(x, yy, hoop_ramp[-1] if u < 0 else hoop_ramp[-2])
    # 윗면 타원
    if lid:
        rt = rx_at(top)
        for y in range(top - ry, top + ry + 1):
            for x in range(int(cx - rt - 1), int(cx + rt + 2)):
                d = ((x + 0.5 - cx) / rt) ** 2 + ((y + 0.5 - top) / ry) ** 2
                if d <= 1:
                    s = 0.7 - 0.25 * ((x - cx) / rt) - 0.15 * ((y - top) / ry)
                    if d > 0.72:
                        s = 0.9 if y < top else 0.35            # 테두리(위 = 빛, 아래 = 홈)
                    c.px(x, y, qcol(lid_ramp, s, x, y, sharp))
        # 뚜껑 널 이음(가로)
        for k in (-0.35, 0.3):
            yy = int(top + k * ry)
            half = rt * math.sqrt(max(0, 1 - k * k)) * 0.82
            c.hline(int(cx - half), int(cx + half), yy, lid_ramp[2])


def face(c, x0, y0, x1, y1, ramp, s, sharp=3.0, grad=0.0):
    """평면 사각 면. grad: 위→아래 명도 변화."""
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        for x in range(x0, x1 + 1):
            c.px(x, y, qcol(ramp, s - grad * t, x, y, sharp))


def poly_mask(w, h, pts):
    m, d = mask(w, h)
    d.polygon(pts, fill=255)
    return m


def ell_mask(w, h, box):
    m, d = mask(w, h)
    d.ellipse(box, fill=255)
    return m


def grain(c, x0, y0, x1, y1, ramp, seed, vertical=True, density=0.05, length=(4, 12)):
    """나무결: 짧은 어두운 선. 이미 칠한 램프 색만 한 단 어둡게."""
    r = Rand(seed)
    n = int((x1 - x0 + 1) * (y1 - y0 + 1) * density / 6)
    for _ in range(n):
        x, y = r.i(x0, x1), r.i(y0, y1)
        ln = r.i(*length)
        for k in range(ln):
            xx, yy = (x, y + k) if vertical else (x + k, y)
            if xx > x1 or yy > y1:
                break
            cur = c.get(xx, yy)
            if cur[3] and cur in ramp:
                c.px(xx, yy, ramp[max(0, ramp.index(cur) - 1)])


def plank_box(c, x0, y0, w, h, top_h, ramp=R_WOOD, seed=1, planks=4, slats=True, brace=True):
    """나무 상자 3/4 시점: 윗면(top_h) + 앞면(h). (x0,y0) = 윗면 왼쪽 위."""
    x1 = x0 + w - 1
    # 윗면
    face(c, x0, y0, x1, y0 + top_h - 1, ramp, 0.82, grad=0.1)
    for k in range(1, planks):
        xx = x0 + k * w // planks
        c.vline(xx, y0 + 1, y0 + top_h - 2, ramp[2])
        c.vline(xx + 1, y0 + 1, y0 + top_h - 2, ramp[4])
    c.hline(x0, x1, y0, ramp[5])
    grain(c, x0 + 1, y0 + 1, x1 - 1, y0 + top_h - 2, ramp, seed, vertical=False, density=0.08, length=(3, 8))
    # 앞면
    fy0 = y0 + top_h
    fy1 = fy0 + h - 1
    face(c, x0, fy0, x1, fy1, ramp, 0.52, grad=0.18)
    if slats:
        n = max(2, h // 9)
        for k in range(1, n):
            yy = fy0 + k * h // n
            c.hline(x0, x1, yy, ramp[1])
            c.hline(x0, x1, yy + 1, ramp[3])
    grain(c, x0 + 2, fy0 + 2, x1 - 2, fy1 - 2, ramp, seed + 3, vertical=False, density=0.06, length=(4, 12))
    # 테두리 각목
    bw = max(3, w // 9)
    for (a, b) in ((x0, x0 + bw - 1), (x1 - bw + 1, x1)):
        face(c, a, fy0, b, fy1, ramp, 0.6 if a == x0 else 0.45, grad=0.2)
        c.vline(a, fy0, fy1, ramp[4] if a == x0 else ramp[2])
    face(c, x0, fy0, x1, fy0 + bw - 2, ramp, 0.66)
    face(c, x0, fy1 - bw + 2, x1, fy1, ramp, 0.4)
    c.hline(x0, x1, fy0, ramp[5])
    if brace:
        # 사선 버팀
        ax0, ax1 = x0 + bw, x1 - bw
        ay0, ay1 = fy1 - bw + 1, fy0 + bw - 1
        n = ax1 - ax0
        for k in range(n + 1):
            xx = ax0 + k
            yy = int(round(ay0 + (ay1 - ay0) * k / max(1, n)))
            for t in range(-1, 2):
                c.px(xx, yy + t, ramp[4] if t < 0 else ramp[3])
            c.px(xx, yy + 2, ramp[1])
    # 못
    for (xx, yy) in ((x0 + bw // 2, fy0 + bw // 2), (x1 - bw // 2, fy0 + bw // 2),
                     (x0 + bw // 2, fy1 - bw // 2), (x1 - bw // 2, fy1 - bw // 2)):
        c.px(xx, yy, G[8]); c.px(xx + 1, yy + 1, G[2])
    # 외곽
    c.hline(x0, x1, fy1, ramp[0])
    c.vline(x1, y0, fy1, ramp[0])
    c.vline(x0, y0, fy1, ramp[1])
    c.hline(x0, x1, y0 - 0, ramp[5])


def flame(c, cx, by, w, h, seed=1, core=True, tongues=4):
    """불꽃(자체 발광): 갈래 여러 개(물방울꼴)의 합. by = 불꽃 밑변 y."""
    r = Rand(seed)
    T_ = []
    for k in range(tongues):
        off = (k - (tongues - 1) / 2) / max(1, tongues - 1) * w * 0.55 + r.i(-2, 2)
        hh = h * (1.0 if abs(off) < w * 0.12 else 0.6 + 0.35 * r.f())
        ww = w * (0.30 if abs(off) < w * 0.12 else 0.22 + 0.06 * r.f())
        sway = (r.f() - 0.5) * w * 0.6
        T_.append((off, hh, ww, sway))
    heatmap = {}
    for (off, hh, ww, sway) in T_:
        for y in range(int(by - hh), by + 1):
            t = min(1.0, (by - y) / hh)
            half = ww * min(1.0, (t + 0.12) / 0.3) ** 0.5 * min(1.0, ((1 - t) / 0.8)) ** 1.25
            ctr = cx + off * (1 - 0.6 * t) + sway * math.sin(t * math.pi * 1.3)
            for x in range(int(ctr - half - 1), int(ctr + half + 2)):
                d = abs(x + 0.5 - ctr) / max(0.6, half)
                if d <= 1:
                    v = (1 - d) * (1 - t * 0.7)
                    heatmap[(x, y)] = max(heatmap.get((x, y), 0), v)
    for (x, y), v in heatmap.items():
        k = clamp(0.04 + v * 1.05)
        c.px(x, y, qcol(FLAME, k, x, y, 2.5))
    if core and w >= 30:
        c.hline(cx - w // 8, cx + w // 8, by - 2, A[27])


def embers(c, cx, cy, n, spread, seed):
    r = Rand(seed)
    for _ in range(n):
        x, y = cx + r.i(-spread, spread), cy - r.i(0, spread * 2)
        col = A[24] if r.f() < 0.5 else A[25]
        c.px(x, y, col)
        if r.f() < 0.5:
            c.px(x, y + 1, A[22])


def glass_lantern(c, cx, top, w, h, frame=R_IRON):
    """쇠틀 유리 등(자체 발광). top = 지붕 위끝."""
    x0, x1 = cx - w // 2, cx + w // 2
    # 지붕
    for k in range(h // 5):
        half = w // 2 - (h // 5 - k) + 1
        c.hline(cx - half, cx + half, top + k, frame[4] if k == 0 else frame[3])
    c.rect(cx - 1, top - 4, cx + 1, top - 1, frame[3]); c.px(cx - 1, top - 4, frame[5])
    gy0, gy1 = top + h // 5, top + h - 3
    c.rect(x0, gy0, x1, gy1, frame[1])
    # 유리 안 불빛(가운데가 가장 밝음)
    for y in range(gy0 + 1, gy1):
        for x in range(x0 + 1, x1):
            d = math.hypot((x - cx) / (w / 2), (y - (gy0 + gy1) / 2) / ((gy1 - gy0) / 2))
            c.px(x, y, qcol([A[22], A[23], A[24], A[25], A[26], A[27]], 1.05 - d * 0.75, x, y, 2.5))
    for x in (x0, x1, cx):
        c.vline(x, gy0, gy1, frame[2] if x != x0 else frame[4])
    c.hline(x0, x1, (gy0 + gy1) // 2, frame[2])
    c.rect(x0 - 1, gy1 + 1, x1 + 1, gy1 + 2, frame[3]); c.hline(x0 - 1, x1 + 1, gy1 + 1, frame[4])


def splash(c, cx, cy, rx, ry, ramp=R_LIQ, seed=1, glint=True, blobs=4):
    """엎질러진 술 웅덩이(비발광, 글린트 1~2점만 밝은 층 램프)."""
    r = Rand(seed)
    m, d = mask(c.w, c.h)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    for _ in range(blobs):
        bx, by = cx + r.i(-rx, rx), cy + r.i(-ry, ry)
        br = r.i(max(2, rx // 5), max(3, rx // 3))
        d.ellipse((bx - br, by - br * 0.5, bx + br, by + br * 0.5), fill=255)
    mp = m.load()
    for y in range(c.h):
        for x in range(c.w):
            if mp[x, y] > 127:
                up = y > 0 and mp[x, y - 1] <= 127
                dn = y + 1 < c.h and mp[x, y + 1] <= 127
                col = ramp[0] if up else (ramp[3] if dn else ramp[1])
                c.px(x, y, col)
    # 반사 줄
    for k in range(2):
        yy = cy - ry // 3 + k * ry // 2
        xx = cx - rx // 2 + k * rx // 3
        c.hline(xx, xx + rx // 3, yy, ramp[3])
        if glint:
            c.px(xx + rx // 6, yy, ramp[5])


def stone_blob(c, cx, cy, rx, ry, ramp, seed, soft=3):
    """돌덩이·잔해 한 개."""
    r = Rand(seed)
    m, d = mask(c.w, c.h)
    pts = []
    n = 9
    for k in range(n):
        a = 2 * math.pi * k / n
        f = 0.75 + 0.3 * r.f()
        pts.append((cx + math.cos(a) * rx * f, cy + math.sin(a) * ry * f))
    d.polygon(pts, fill=255)
    shade_mask(c, m, ramp, base=0.5, gain=0.7, soft=soft, tilt=0.25, sharp=2.5)


def save_sheet_preview(im, path, k=2, bg=(40, 42, 50)):
    out = Image.new("RGBA", im.size, bg + (255,))
    out.alpha_composite(im)
    out = out.resize((im.width * k, im.height * k), Image.NEAREST)
    out.convert("RGB").save(path)
