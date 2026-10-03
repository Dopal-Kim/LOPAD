"""적 v3 공용 리그 — 3D 골격 하나를 4방향으로 투영해 v3kit.Rig3 로 래스터·셰이딩한다(53라운드 Q33).

주인공 v3(hero_v3/hero.py)는 방향마다 손으로 그린 2D 골격이지만, 적 3종 × 4방향 × 5동작을 같은 밀도로 만들기 위해
여기서는 몸을 3D 관(tube: 단면 타원을 축을 따라 쌓은 것)·상자·판으로 만들고 방향별로 투영한다.
셰이딩(법선 근사·겹침 그림자·내부 선·셀아웃·가장자리 빛)은 v3kit.Rig3 그대로 — 주인공과 같은 렌더러 계열.
hero_v3 의 파일은 import 만 하고 고치지 않는다.

좌표:
  지역(local) = (f 앞, r 해부 오른쪽, u 위), 원점 = 발 피벗(바닥). 단위 = 도트(96×144 판 기준).
  세계(world) = (X 화면 오른쪽, D 카메라 쪽(남), U 위).
  화면 = (piv.x + s·X, piv.y + s·(−U + KZ·D)) — 쿼터뷰 사영(가까운 쪽이 아래). 깊이 = D·cos + U·sin.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "hero_v3"))
from v3kit import Rig3, Part, G, A, SL, WD, PL, OUT, raster_path, kit  # noqa: E402,F401

# hero_v3·v2_outer 에도 anim/preview/build 등이 있으므로 이 폴더를 다시 맨 앞에(이름 가림 방지)
sys.path.insert(0, HERE)

KZ = 0.36
CAMV = (0.0, 0.94, 0.34)          # 세계 좌표에서 카메라 쪽 방향
DIRS = ["down", "up", "left", "right"]


# ---- 벡터 -----------------------------------------------------------------
def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    n = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


def length(a):
    return math.sqrt(dot(a, a))


def lerp3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def rot(v, axis, deg):
    """로드리게스 회전(축은 단위 벡터)."""
    k = norm(axis)
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    kv = cross(k, v)
    kd = dot(k, v)
    return (v[0] * c + kv[0] * s + k[0] * kd * (1 - c),
            v[1] * c + kv[1] * s + k[1] * kd * (1 - c),
            v[2] * c + kv[2] * s + k[2] * kd * (1 - c))


def perp(t):
    """t 에 수직인 단위 벡터 둘."""
    h = (0.0, 0.0, 1.0) if abs(t[2]) < 0.9 else (1.0, 0.0, 0.0)
    a = norm(cross(t, h))
    b = norm(cross(t, a))
    return a, b


def ik3(root, target, l1, l2, pole):
    """3D 두 관절 IK — pole = 관절(무릎·팔꿈치)이 굽어 나갈 방향."""
    d = sub(target, root)
    L = length(d)
    L = max(0.5, min(L, l1 + l2 - 0.05))
    u = norm(d)
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    p = sub(pole, mul(u, dot(pole, u)))
    p = norm(p) if length(p) > 1e-6 else perp(u)[0]
    mid = add(add(root, mul(u, a)), mul(p, h))
    end = add(root, mul(u, L))
    return mid, end


FACING = {
    "down": lambda f, r, u: (-r, f, u),
    "up": lambda f, r, u: (r, -f, u),
    "right": lambda f, r, u: (f, r, u),
    "left": lambda f, r, u: (-f, -r, u),
}


class Body:
    """한 프레임 = Body 하나. 부위를 모아 깊이순으로 Rig3 에 넣고 render()."""

    def __init__(self, W, H, piv, scale, facing, xf=None):
        self.W, self.H, self.piv, self.s, self.facing = W, H, piv, scale, facing
        self.xf = xf                 # 지역 → 지역 전역 변형(쓰러짐 회전 등) 함수 또는 None
        self.R = Rig3(W, H)          # S=1: 픽셀 좌표 그대로
        self.items = []              # (depth, order, part, polys)
        self.decals = []             # 셰이딩 뒤 덧칠 함수(R) — 부위 이름이 정해진 뒤 실행
        self.post = []               # 렌더 뒤 이미지 덧칠 함수(im)
        self.anchors = {}
        self.noxf = False            # True 동안 추가하는 부위는 전역 변형 없이(바닥에 떨어진 소지품·웅덩이)

    # --- 변환 ------------------------------------------------------------------
    def L(self, p):
        return self.xf(p) if (self.xf and not self.noxf) else p

    def world(self, p):
        q = self.L(p)
        return FACING[self.facing](*q)

    def wvec(self, v):
        return sub(self.world(v), self.world((0.0, 0.0, 0.0)))

    def proj(self, p):
        X, D, U = self.world(p)
        return (self.piv[0] + self.s * X, self.piv[1] + self.s * (-U + KZ * D))

    def depth(self, p):
        X, D, U = self.world(p)
        return D * CAMV[1] + U * CAMV[2]

    def pvec(self, v):
        X, D, U = self.wvec(v)
        return (self.s * X, self.s * (-U + KZ * D))

    def faces_cam(self, n, th=0.0):
        return dot(norm(self.wvec(n)), CAMV) > th

    # --- 도형 ------------------------------------------------------------------
    def _disk(self, c, a, b, ra, rb, n=18):
        cx, cy = self.proj(c)
        ax, ay = self.pvec(a)
        bx, by = self.pvec(b)
        out = []
        for k in range(n):
            t = 2 * math.pi * k / n
            co, si = math.cos(t), math.sin(t)
            out.append((cx + (ax * ra * co + bx * rb * si), cy + (ay * ra * co + by * rb * si)))
        return out

    def _circle(self, c, r, n=18):
        cx, cy = self.proj(c)
        rr = r * self.s
        return [(cx + rr * math.cos(2 * math.pi * k / n), cy + rr * 1.04 * math.sin(2 * math.pi * k / n)) for k in range(n)]

    def add_part(self, part, polys, depth, bias=0.0):
        self.items.append([depth + bias, len(self.items), part, polys])
        return part

    def tube(self, part, pts, rads, axes=None, caps=True, bias=0.0, step=1.0):
        """pts: 지역 3D 점 목록, rads: 점별 반지름(수 또는 (ra, rb)).
        axes: None = 원형 단면(축에 수직) / (a, b) = 단면 축 고정(몸통: 옆·앞) / 점별 [(a, b), ...]."""
        polys, ds, prev = [], [], None
        rads = [(r, r) if not isinstance(r, tuple) else r for r in rads]
        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i + 1]
            seg = sub(p1, p0)
            Ls = length(seg)
            t = norm(seg) if Ls > 1e-6 else (0.0, 0.0, 1.0)
            n = max(1, int(Ls * self.s / step))
            for k in range(n + (1 if i == len(pts) - 2 else 0)):
                tt = k / n
                c = lerp3(p0, p1, tt)
                ra = rads[i][0] + (rads[i + 1][0] - rads[i][0]) * tt
                rb = rads[i][1] + (rads[i + 1][1] - rads[i][1]) * tt
                if axes is None:
                    a, b = perp(t)
                elif isinstance(axes, list):
                    a0, b0 = axes[i]
                    a1, b1 = axes[i + 1]
                    a, b = norm(lerp3(a0, a1, tt)), norm(lerp3(b0, b1, tt))
                else:
                    a, b = axes
                dk = self._disk(c, a, b, ra, rb)
                polys.append(hull(prev + dk) if prev else dk)
                prev = dk
                ds.append(self.depth(c))
        if caps and axes is None:
            polys.append(self._circle(pts[0], rads[0][0]))
            polys.append(self._circle(pts[-1], rads[-1][0]))
        return self.add_part(part, polys, sum(ds) / max(1, len(ds)), bias)

    def blob(self, part, c, up, ax, bx, rx, rz, ru, bias=0.0, n=14, prof=None):
        """타원체: 중심 c, 위 축 up, 단면 축 ax(옆)·bx(앞), 반지름 rx·rz·ru. prof(t)→단면 배율(기본 구)."""
        up = norm(up)
        polys, ds, prev = [], [], None
        steps = max(4, int(ru * 2 * self.s / 1.0))
        for k in range(steps + 1):
            t = -1 + 2 * k / steps
            m = prof(t) if prof else math.sqrt(max(0.0, 1 - t * t))
            if m <= 0.02:
                continue
            cc = add(c, mul(up, t * ru))
            dk = self._disk(cc, ax, bx, rx * m, rz * m)
            polys.append(hull(prev + dk) if prev else dk)
            prev = dk
            ds.append(self.depth(cc))
        return self.add_part(part, polys, sum(ds) / max(1, len(ds)), bias)

    def box(self, part, c, axes, half, bias=0.0):
        """상자: 중심 c, 축 3개(지역 단위 벡터), 반 크기 3개 → 투영 꼭짓점의 볼록 껍질."""
        pts = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    p = add(c, add(mul(axes[0], sx * half[0]), add(mul(axes[1], sy * half[1]), mul(axes[2], sz * half[2]))))
                    pts.append(self.proj(p))
        return self.add_part(part, [hull(pts)], self.depth(c), bias)

    def flat(self, part, pts3, bias=0.0):
        """평평한 다각형(모자 챙 등)."""
        q = [self.proj(p) for p in pts3]
        d = sum(self.depth(p) for p in pts3) / len(pts3)
        return self.add_part(part, [q], d, bias)

    def poly2(self, part, pts2, depth, bias=0.0):
        """화면 좌표 다각형(이미 투영된 것)."""
        return self.add_part(part, [pts2], depth, bias)

    # --- 덧칠 ------------------------------------------------------------------
    def dot3(self, p, c, part=None, n=None, th=0.0):
        """지역 3D 점 덧칠. n(표면 법선)을 주면 카메라 쪽일 때만."""
        if n is not None and not self.faces_cam(n, th):
            return
        x, y = self.proj(p)
        self.decals.append(lambda R, x=x, y=y: R.cdot(x, y, c, part))

    def line3(self, pts, c, part=None, n=None, th=0.0):
        if n is not None and not self.faces_cam(n, th):
            return
        q = [self.proj(p) for p in pts]
        cells = raster_path(q)
        cols = c if isinstance(c, list) else [c]
        m = len(cells)

        def f(R, cells=cells):
            for i, (x, y) in enumerate(cells):
                R.cdot(x, y, cols[min(len(cols) - 1, int(i * len(cols) / max(1, m)))], part)
        self.decals.append(f)

    def ring(self, c, a, b, ra, rb, colf, part=None, th=0.05, n=None):
        """3D 고리(술통 쇠테·모자 테): 카메라 쪽 반만. colf(cos, sin, 법선) → 색 또는 None."""
        cells = {}
        npts = n or int(max(ra, rb) * self.s * 7) + 12
        for k in range(npts):
            t = 2 * math.pi * k / npts
            co, si = math.cos(t), math.sin(t)
            nrm = add(mul(a, co), mul(b, si))
            if not self.faces_cam(nrm, th):
                continue
            p = add(c, add(mul(a, ra * co), mul(b, rb * si)))
            x, y = self.proj(p)
            col = colf(co, si, self.wvec(nrm))
            if col is not None:
                cells[(round(x), round(y))] = col
        self.decals.append(lambda R, cells=cells: [R.cdot(x, y, col, part) for (x, y), col in cells.items()])

    def fill3(self, pts3, colf, part=None):
        """지역 3D 다각형을 화면에 채운 덧칠(부위 위에만) — colf(x, y, 0~1 가로 위치) → 색."""
        from PIL import Image as _I, ImageDraw as _D
        q = [self.proj(p) for p in pts3]
        x0, y0 = int(min(p[0] for p in q)) - 1, int(min(p[1] for p in q)) - 1
        x1, y1 = int(max(p[0] for p in q)) + 2, int(max(p[1] for p in q)) + 2
        m = _I.new("L", (x1 - x0, y1 - y0), 0)
        _D.Draw(m).polygon([(round(x - x0), round(y - y0)) for x, y in q], fill=255)
        mp = m.load()
        cells = []
        for y in range(y1 - y0):
            row = [x for x in range(x1 - x0) if mp[x, y]]
            if not row:
                continue
            a, b = row[0], row[-1]
            for x in row:
                cells.append((x + x0, y + y0, colf(x + x0, y + y0, (x - a) / max(1, b - a))))
        self.decals.append(lambda R, cells=cells: [R.cdot(x, y, c, part) for x, y, c in cells if c is not None])

    def px(self, x, y, c, part=None):
        self.decals.append(lambda R: R.cdot(x, y, c, part))

    # --- 렌더 ------------------------------------------------------------------
    def render(self):
        R = self.R
        for d, _, part, polys in sorted(self.items, key=lambda it: (it[0], it[1])):
            def fn(dr, polys=polys):
                for q in polys:
                    if len(q) >= 3:
                        dr.polygon([(round(x), round(y)) for x, y in q], fill=255)
            part.soft = part.soft * self.s
            R.shape(part, fn)
        for f in self.decals:
            f(R)
        im = R.render()
        for f in self.post:
            f(im)
        return im


def hull(pts):
    pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
    if len(pts) <= 2:
        return pts

    def cr(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


# ---- 골격 -----------------------------------------------------------------
def pose(**kw):
    p = dict(root=(0.0, 0.0, 0.0),    # 골반 이동(f, r, u)
             lean=0.0,                # 상체 앞숙임(도, + 앞)
             roll=0.0,                # 상체 옆 기울기(도, + 해부 오른쪽으로)
             twist=0.0,               # 가슴 비틀림(도, + = 오른어깨가 뒤로)
             head=(0.0, 0.0, 0.0),    # 머리 (숙임, 돌림, 기울임) 도
             footL=(0.0, -8.0, 0.0), footR=(0.0, 8.0, 0.0),   # (f, r, 들림)
             handL=None, handR=None,  # 손 목표(지역 3D). None = 기본 늘어뜨림
             elbowL=None, elbowR=None,
             fall=None,               # (회전축 지역 벡터, 도, 축 기준점) — 쓰러짐
             sink=0.0,                # 전체 아래로(쓰러짐 마지막)
             flash=False, eye="open", fx=None)
    p.update(kw)
    return p


class Skel:
    """비율(P) + 자세(p) → 관절 위치(지역 3D)."""

    def __init__(self, P, p):
        self.P, self.p = P, p
        rf, rr, ru = p["root"]
        self.pel = (rf, rr, P["hip"] + ru)
        lean, roll = math.radians(p["lean"]), math.radians(p["roll"])
        self.up = norm((math.sin(lean), math.sin(roll), math.cos(lean) * math.cos(roll)))
        tw = p["twist"]
        self.rax = norm(rot((0.0, 1.0, 0.0), self.up, -tw))           # 가슴 옆 축(해부 오른쪽)
        self.fax = norm(cross(self.rax, self.up))                       # 가슴 앞 축
        if self.fax[0] < 0:
            self.fax = mul(self.fax, -1)
        self.waist = add(self.pel, mul(self.up, P["waist"]))
        self.chest = add(self.pel, mul(self.up, P["chest"]))
        self.neck = add(self.pel, mul(self.up, P["neck"]))
        hp, hy, hr = p["head"]
        hup = rot(self.up, self.rax, hp)
        hup = rot(hup, self.fax, hr)
        self.hup = norm(hup)
        self.hfax = norm(rot(rot(self.fax, self.rax, hp), self.hup, hy))
        self.hrax = norm(cross(self.hup, self.hfax))
        self.head = add(self.neck, mul(self.hup, P["head_up"]))
        self.head = add(self.head, mul(self.hfax, P.get("head_fwd", 0.0)))
        # 다리
        self.hipL = add(self.pel, (0.0, -P["hip_w"], 0.0))
        self.hipR = add(self.pel, (0.0, P["hip_w"], 0.0))
        self.legs = {}
        for s, hip, ft in (("L", self.hipL, p["footL"]), ("R", self.hipR, p["footR"])):
            ankle = (ft[0], ft[1], P["ankle"] + ft[2])
            knee, ank = ik3(hip, ankle, P["thigh"], P["shin"], (1.0, 0.25 * (1 if s == "R" else -1), 0.0))
            self.legs[s] = (hip, knee, ank, ft)
        # 팔
        self.shL = add(add(self.chest, mul(self.rax, -P["sh_w"])), mul(self.up, P["sh_up"]))
        self.shR = add(add(self.chest, mul(self.rax, P["sh_w"])), mul(self.up, P["sh_up"]))
        self.arms = {}
        for s, sh, h, el in (("L", self.shL, p["handL"], p["elbowL"]), ("R", self.shR, p["handR"], p["elbowR"])):
            sg = -1 if s == "L" else 1
            if h is None:
                h = add(sh, add(mul(self.up, -(P["upper"] + P["fore"]) * 0.92), add(mul(self.rax, sg * 3.0), mul(self.fax, 2.0))))
            pole = el if el is not None else add(mul(self.fax, -0.6), add(mul(self.rax, sg * 0.8), mul(self.up, -0.2)))
            elb, hand = ik3(sh, h, P["upper"], P["fore"], pole)
            self.arms[s] = (sh, elb, hand)


def fall_xf(axis, deg, about, sink=0.0):
    """쓰러짐: about 점 기준으로 axis 축 회전 후 아래로 sink."""
    def f(p):
        q = rot(sub(p, about), axis, deg)
        return (q[0] + about[0], q[1] + about[1], q[2] + about[2] - sink)
    return f


def lighten_flash(im):
    """피격 0프레임: 셀아웃은 두고 몸을 흰빛 두 단(G13/G14)으로 — v2 결사병 flashFrame 과 같은 방식(2배 밀도)."""
    out = im.copy()
    px = out.load()
    W, H = out.size
    outc = OUT[:3]
    for y in range(H):
        for x in range(W):
            c = px[x, y]
            if c[3] == 0 or c[:3] == outc:
                continue
            lum = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
            px[x, y] = G[14] if lum > 70 else G[12]
    return out


# ---- 쓰러짐(사망) ---------------------------------------------------------------
_NORTH = {"down": (-1.0, 0.0, 0.0), "up": (1.0, 0.0, 0.0), "right": (0.0, -1.0, 0.0), "left": (0.0, 1.0, 0.0)}


def north_local(direction):
    """세계 북쪽(화면 위·카메라 반대)을 가리키는 지역 수평 벡터 — 쓰러지는 쪽. 남쪽(카메라 쪽)으로 쓰러지면 시트 아래로 넘친다."""
    return _NORTH[direction]


def w2l(direction, X, D):
    """세계 바닥 (X, D) → 지역 (f, r)."""
    return {"down": (D, -X), "up": (-D, X), "right": (X, D), "left": (-X, -D)}[direction]


def fall_fn(direction, deg, lift):
    """발 피벗 기준으로 북쪽으로 deg 만큼 넘어지고 lift 만큼 띄움(누운 몸 두께)."""
    d = north_local(direction)
    axis = cross((0.0, 0.0, 1.0), d)

    def f(p):
        q = rot(p, axis, deg)
        return (q[0], q[1], q[2] + lift)
    return f
