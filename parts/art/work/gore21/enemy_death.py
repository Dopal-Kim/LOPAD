"""P21 아트 B 단계 3 — 적 사망 변형(collapse·behead·bisect·pinned·burn) + 잘린 조각(gore_parts).

같은 3D 리그(enemies_v3 erig — 적별 모듈 musket60·bulwark60·peddler61·porter61·drummer19·bomber19)로 렌더한다:
  - behead: 사망 자세 그대로, 머리 쪽 부위(머리·모자·머리카락·투구·두건·턱수염…)를 빼고 목 단면 + 동맥 분출
  - bisect: 사망 자세 그림을 허리선(골격 waist, 몸 위 축에 수직)으로 갈라 윗몸이 더 멀리(북쪽) 떨어지게 + 단면·피 끌림
  - pinned: 벽에 화살로 박혀 선 채로 늘어짐(사망 0 → 뒤로 튕김 → 늘어져 고개 숙임) + 가슴 화살대 + 흘러내리는 피
  - burn: 사망 자세 + 불길(호박 램프)이 타오르며 몸이 숯빛으로 그을림 → 연기·불씨
  - collapse: 사망 자세 + 상처·옷 피 젖음 번짐 + 작은 분출
  drown 은 기존 낙하 연출(react_fall_splash) 재사용 — 만들지 않음.
조각: fx/v5/gore_parts_<적> — 행 head·arm·upper, 열 = 회전 8(0·45·…·315°).

python3 parts/art/work/gore21/enemy_death.py [적…] [--variants=behead,bisect] [--no-assets] [--parts-only]
"""
import importlib
import json
import math
import os
import random
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "enemies61"))
import kit61  # noqa: E402,F401  (enemies_v3·floor1q60·enemies61 경로)
sys.path.insert(0, os.path.join(WORK, "p19"))
import erig  # noqa: E402
sys.path.insert(0, HERE)
import gk  # noqa: E402
from gk import BL0, BL1, BL2, BL3, BL4, G, A  # noqa: E402
from PIL import Image  # noqa: E402

MODS = {"archer": "musket60", "charger": "bulwark60", "peddler": "peddler61", "porter": "porter61", "drummer": "drummer19",
        "bomber": "bomber19"}
ENEMIES = list(MODS)
VARIANTS = ["collapse", "behead", "bisect", "pinned", "burn"]
DIRS = erig.DIRS
SRC = "parts/art/work/gore21/enemy_death.py (P21 잔혹 전투 — 적 사망 변형, 같은 3D 리그 erig)"
HEAD_PREFIX = ("head", "hair", "helm", "beard", "kerch", "scarfmask", "bandtail", "cap", "ear")


def is_head(name):
    if name.startswith(("hat_ground", "hatg")):
        return False
    return name.startswith(HEAD_PREFIX) or name.startswith("hat")


# ---------------------------------------------------------------- 리그 훅(전역 — 이 프로세스 안에서만)
_STATE = {"filter": None, "skel": None, "body": None}
_skel_init = erig.Skel.__init__
_body_init = erig.Body.__init__
_body_render = erig.Body.render


def _si(self, *a, **k):
    _skel_init(self, *a, **k)
    _STATE["skel"] = self


def _bi(self, *a, **k):
    _body_init(self, *a, **k)
    _STATE["body"] = self


def _br(self):
    f = _STATE["filter"]
    if f is not None:
        self.items = [it for it in self.items if f(it[2].name)]
    return _body_render(self)


erig.Skel.__init__, erig.Body.__init__, erig.Body.render = _si, _bi, _br


def render(mod, d, p, keep=None):
    """→ (RGBA, skel, body). keep(part_name) → bool 이면 그 부위만 남긴다."""
    _STATE["filter"] = keep
    try:
        B, info = mod.draw(d, p)
        S = _STATE["skel"]
        im = B.render()
    finally:
        _STATE["filter"] = None
    return im, S, B


def scr(B, p3):
    x, y = B.proj(p3)
    return x, y


# ---------------------------------------------------------------- 픽셀 도구
def opaque(im):
    px = im.load()
    W, H = im.size
    return {(x, y) for y in range(H) for x in range(W) if px[x, y][3]}


def put(im, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), gk.hexrgb(c))


def put_on(im, body, x, y, c):
    x, y = int(round(x)), int(round(y))
    if (x, y) in body:
        im.putpixel((x, y), gk.hexrgb(c))


def put_under(im, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < im.width and 0 <= y < im.height and im.getpixel((x, y))[3] == 0:
        im.putpixel((x, y), gk.hexrgb(c))


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


class Ballistic:
    """화면 공간 피 방울(중력 아래 +y, 바닥 y 에서 납작해져 멈춤)."""

    def __init__(self, x, y, vx, vy, r, t0, ground, g=900.0):
        self.x, self.y, self.vx, self.vy, self.r, self.t0, self.ground, self.g = x, y, vx, vy, r, t0, ground, g

    def at(self, t):
        tt = t - self.t0
        if tt < 0:
            return None
        x = self.x + self.vx * tt
        y = self.y + self.vy * tt + 0.5 * self.g * tt * tt
        if y >= self.ground:
            # 바닥에 닿은 시각 이후는 그 자리
            a, b, c = 0.5 * self.g, self.vy, self.y - self.ground
            disc = max(0.0, b * b - 4 * a * c)
            tl = (-b + math.sqrt(disc)) / (2 * a)
            return (self.x + self.vx * tl, self.ground, True, (self.vx, 0))
        return (x, y, False, (self.vx, self.vy + self.g * tt))

    def draw(self, im, t):
        q = self.at(t)
        if q is None:
            return
        x, y, landed, (vx, vy) = q
        if landed:
            for k in range(1 + int(self.r * 1.5)):
                put(im, x + (k if vx >= 0 else -k), y, BL1 if k else BL2)
            if self.r >= 1.3:
                put(im, x, y - 1, BL1)
            return
        sp = math.hypot(vx, vy) or 1
        ln = min(6, sp * 0.012)
        for i, (cx, cy) in enumerate(gk.line_cells(x - vx / sp * ln, y - vy / sp * ln, x, y)):
            put(im, cx, cy, BL1)
        for cx, cy in gk.disc_cells(x, y, self.r):
            put(im, cx, cy, BL2)
        if self.r >= 1.2:
            put(im, x, y, BL3)


def times(ms):
    out, t = [], 0
    for m in ms:
        out.append((t + m * 0.5) / 1000.0)
        t += m
    return out


# ---------------------------------------------------------------- 공통: 상처 스탬프·피 젖음
def stain(im, body, cx, cy, radius, rnd, down=1.6, dens=1.0):
    """옷 피 젖음: 상처 점에서 아래로 길쭉하게 번진 영역의 몸 픽셀을 어둡게 붉힘(밝기 단계 유지 — 원래 명암 결이 남게)."""
    px = im.load()
    for (x, y) in body:
        dx, dy = x - cx, y - cy
        if dy < 0:
            dd = math.hypot(dx, dy * 1.4)
        else:
            dd = math.hypot(dx, dy / down)
        n = ((x * 73856093) ^ (y * 19349663)) % 1000 / 1000.0
        if dd + n * 3.0 * dens < radius:
            c = px[x, y]
            if c[:3] == gk.hexrgb(G[0])[:3] or c[3] == 0:
                continue
            L = lum(c)
            px[x, y] = gk.hexrgb(BL0 if L < 80 else (BL1 if L < 140 else BL2))   # 2차 비평: 밝은 셔츠가 선홍 판으로 → 한 단 어둡게


def gash(im, body, cx, cy, ang, L, rnd):
    """몸 위 베인 상처(검은 틈 + 벌어진 살 테 + 하이라이트)."""
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    for i in range(L):
        u = i / max(1, L - 1) - 0.5
        x, y = cx + ux * u * L, cy + uy * u * L
        w = 1.2 * (1 - (2 * u) ** 2)
        put_on(im, body, x - nx * (w + 1), y - ny * (w + 1), BL3)
        put_on(im, body, x + nx * (w + 1), y + ny * (w + 1), BL2)
        put_on(im, body, x, y, BL0)
        if w > 0.7:
            put_on(im, body, x + nx, y + ny, BL1)
    put_on(im, body, cx - nx * 2, cy - ny * 2, BL4)


# ---------------------------------------------------------------- 변형
def v_collapse(mod, d, poses, ms, rnd):
    out = []
    T = times(ms)
    drops = []
    for k, p in enumerate(poses):
        im, S, B = render(mod, d, p)
        body = opaque(im)
        cx, cy = scr(B, S.chest)
        wx, wy = scr(B, erig.add(S.chest, erig.mul(S.up, -5.0)))
        if k == 0:
            for i in range(9):
                a = rnd.uniform(-math.pi * 0.9, -math.pi * 0.1)
                s = rnd.uniform(60, 160)
                drops.append(Ballistic(cx, cy, math.cos(a) * s, math.sin(a) * s, rnd.uniform(0.6, 1.4), 0.0, B.piv[1] + rnd.uniform(-14, 4)))
        stain(im, body, cx, cy + 2, min(9.5, 4 + 1.0 * k), rnd, dens=0.9)
        gash(im, body, cx - 1, cy, -0.5, 9, rnd)
        gash(im, body, wx + 3, wy, 0.4, 7, rnd)
        for dr in drops:
            dr.draw(im, T[k])
        out.append(im)
    return out


def neck_stump(im, B, S, big=True):
    nx, ny = scr(B, S.neck)
    ux, uy = scr(B, erig.add(S.neck, erig.mul(S.up, 4.0)))
    vx, vy = ux - nx, uy - ny
    vl = math.hypot(vx, vy) or 1
    ax, ay = -vy / vl, vx / vl
    r = 4.2 if big else 3.4
    for t in range(-int(r), int(r) + 1):
        for s in (0, 1):
            x, y = nx + ax * t + vx / vl * s * 0.8, ny + ay * t + vy / vl * s * 0.8
            put(im, x, y, BL1 if abs(t) >= r - 1 else BL2)
    for t in range(-int(r) + 1, int(r)):
        put(im, nx + ax * t + vx / vl * 1.6, ny + ay * t + vy / vl * 1.6, BL0 if abs(t) > 1 else BL3)
    put(im, nx, ny, G[13])          # 목뼈
    put(im, nx + ax, ny + ay, BL3)
    return nx, ny, vx / vl, vy / vl


def v_behead(mod, d, poses, ms, rnd):
    out = []
    T = times(ms)
    jets = []
    keep = lambda n: not is_head(n)  # noqa: E731
    for k, p in enumerate(poses):
        im, S, B = render(mod, d, p, keep)
        nx, ny, ux, uy = neck_stump(im, B, S)
        gy = B.piv[1]           # 바닥 = 발 피벗 줄(쓰러짐 변형 xf 를 거치지 않게 — 1차 비평: 방울이 공중에 멈춤)
        # 동맥 분출: 0~5 프레임 맥박 3번 — 목 위 축 방향으로 솟구쳐 떨어짐
        if k <= 5:
            pulse = k in (0, 2, 4)
            for i in range((10 if k < 3 else 6) if pulse else 3):
                spread = rnd.uniform(-0.16, 0.16)
                s = rnd.uniform(110, 190) * (1.0 if k < 3 else 0.75)
                vx = (ux + spread) * s + rnd.uniform(-15, 15)
                vy = uy * s - rnd.uniform(5, 20)
                jets.append(Ballistic(nx + ux * i * 0.6, ny + uy * i * 0.6, vx, vy, rnd.uniform(0.9, 1.8), T[k] - 0.025,
                                      gy + rnd.uniform(-16, 4), g=1500.0))
            # 줄기(이어진 피): 목에서 위로 짧은 기둥
            L = [14, 9, 15, 8, 11, 5][k]
            for j in range(L):
                put(im, nx + ux * j + (j * j) * 0.03, ny + uy * j + (j * j) * 0.06, BL2 if j % 3 else BL1)
                if j < L * 0.5:
                    put(im, nx + ux * j + 1, ny + uy * j, BL3 if j % 4 == 0 else BL2)
        for jd in jets:
            jd.draw(im, T[k])
        if k >= 6:   # 쓰러진 뒤 목에서 번지는 피(바닥 — 몸 뒤 빈 칸에만)
            r = 2 + 2.0 * (k - 5)
            for c in gk.disc_cells(nx + ux * 3, ny + uy * 3 + 1, r, sy=0.6):
                put_under(im, c[0], c[1], BL1 if (c[0] + c[1]) % 5 else BL0)
        out.append(im)
    return out


def split_by_line(im, px, py, ux, uy, jag):
    """(px,py) 를 지나고 위 축 (ux,uy) 에 수직인 선으로 가름 → (위쪽 그림, 아래쪽 그림). jag = 가장자리 들쭉날쭉 함수."""
    up = Image.new("RGBA", im.size, (0, 0, 0, 0))
    lo = Image.new("RGBA", im.size, (0, 0, 0, 0))
    s, upx, lox = im.load(), up.load(), lo.load()
    W, H = im.size
    for y in range(H):
        for x in range(W):
            c = s[x, y]
            if not c[3]:
                continue
            along = (x - px) * (-uy) + (y - py) * ux
            h = (x - px) * ux + (y - py) * uy + jag(along)
            (upx if h > 0 else lox)[x, y] = c
    return up, lo


def cut_face(im, px, py, ux, uy, jag, side, rnd):
    """단면: 가른 선을 따라 몸 픽셀에 피 테(BL2/BL3) + 검은 속(BL0) + 뼈(G13)·창자(BL3/BL2 고리) 몇 도트."""
    body = opaque(im)
    edge = []
    for (x, y) in body:
        along = (x - px) * (-uy) + (y - py) * ux
        h = (x - px) * ux + (y - py) * uy + jag(along)
        if (side > 0 and 0 < h <= 2.2) or (side < 0 and -2.2 <= h <= 0):
            edge.append((x, y, along, abs(h)))
    if not edge:
        return
    for x, y, al, hh in edge:
        put(im, x, y, BL0 if hh < 1.1 else (BL2 if (int(al) % 3) else BL3))
    edge.sort(key=lambda e: e[2])
    mid = edge[len(edge) // 2]
    put(im, mid[0], mid[1], G[13])
    put(im, mid[0] + 1, mid[1], G[11])
    for e in edge[len(edge) // 4: len(edge) // 4 + 3]:
        put(im, e[0], e[1], BL3)


def v_bisect(mod, d, poses, ms, rnd):
    """2차: 윗몸은 0 프레임 그림을 허리에서 떼어 앞(남·카메라 쪽)으로 꺾여 떨어지고, 다리는 원래 사망 자세로 북쪽에 쓰러짐 → 두 조각이 갈라져 보임."""
    out = []
    T = times(ms)
    jagv = [rnd.uniform(-1.2, 1.2) for _ in range(9)]
    jag = lambda a: jagv[int(a // 5) % 9] if abs(a) < 40 else 0.0  # noqa: E731
    sg = 1 if d in ("down", "right") else -1
    ang = [0, 6, 16, 32, 52, 70, 82, 88, 90, 90]
    full0, S0, B0 = render(mod, d, poses[0])
    wx0, wy0 = scr(B0, S0.waist)
    q = scr(B0, erig.add(S0.waist, erig.mul(S0.up, 10.0)))
    vl = math.hypot(q[0] - wx0, q[1] - wy0) or 1
    ux0, uy0 = (q[0] - wx0) / vl, (q[1] - wy0) / vl
    up0, _ = split_by_line(full0, wx0, wy0, ux0, uy0, jag)
    cut_face(up0, wx0, wy0, ux0, uy0, jag, +1, rnd)
    land_y = B0.piv[1] - 6
    drops, puddle = [], []
    for k, p in enumerate(poses):
        full, S, B = render(mod, d, p)
        if k == 0:
            im = full
            body = opaque(full)
            for t in range(-16, 17):
                put_on(im, body, wx0 + (-uy0) * t, wy0 + ux0 * t, BL3 if t % 4 else BL4)
            for i in range(12):
                a = rnd.uniform(-math.pi, 0)
                s_ = rnd.uniform(70, 170)
                drops.append(Ballistic(wx0 + rnd.uniform(-8, 8), wy0, math.cos(a) * s_, math.sin(a) * s_, rnd.uniform(0.6, 1.6),
                                       T[0], B.piv[1] + rnd.uniform(-14, 4), g=1200.0))
            out.append(im)
            continue
        wx, wy = scr(B, S.waist)
        q = scr(B, erig.add(S.waist, erig.mul(S.up, 10.0)))
        vl = math.hypot(q[0] - wx, q[1] - wy) or 1
        ux, uy = (q[0] - wx) / vl, (q[1] - wy) / vl
        _, lo = split_by_line(full, wx, wy, ux, uy, jag)
        cut_face(lo, wx, wy, ux, uy, jag, -1, rnd)
        im = Image.new("RGBA", full.size, (0, 0, 0, 0))
        # 바닥 피(다리 허리 단면 아래 + 윗몸 떨어진 자리) — 몸 뒤 빈 칸
        if k >= 3:
            for c in gk.disc_cells(wx, wy + 3, 2 + 1.2 * (k - 2), sy=0.6):
                put_under(im, c[0], c[1], BL1 if (c[0] * 3 + c[1]) % 7 else BL0)
        im.alpha_composite(lo)
        # 떨어지는 윗몸: 허리 기준 회전 + 아래로(바닥까지) 낙하
        u = min(1.0, (k / 6.0) ** 1.6)
        ty = (land_y - wy0) * u
        tx = sg * 10 * u
        rot = up0.rotate(-sg * ang[k], resample=Image.NEAREST, center=(wx0, wy0), translate=(tx, ty))
        for _ in range(12):           # 틀 밖으로 잘리지 않게(3차 비평: 머리가 오른쪽 끝에서 잘림) — 안쪽으로 당김
            bb = rot.getbbox()
            if not bb or (bb[0] > 0 and bb[2] < rot.width and bb[1] > 0):
                break
            tx += 2 if bb[0] == 0 else (-2 if bb[2] >= rot.width else 0)
            ty += 2 if bb[1] == 0 else 0
            rot = up0.rotate(-sg * ang[k], resample=Image.NEAREST, center=(wx0, wy0), translate=(tx, ty))
        if k >= 5:
            for c in gk.disc_cells(wx0 + tx, wy0 + ty + 2, 1.5 + 1.1 * (k - 4), sy=0.55):
                put_under(im, c[0], c[1], BL1 if (c[0] + 2 * c[1]) % 5 else BL0)
        im.alpha_composite(rot)
        if 1 <= k <= 4:   # 다리 쪽 단면에서 솟는 피
            for j in range([10, 8, 6, 4][k - 1]):
                put(im, wx + ux * j + (j % 2), wy + uy * j, BL2 if j % 3 else BL1)
        for dr in drops:
            dr.draw(im, T[k])
        out.append(im)
    return out


def pinned_poses(mod, d, poses):
    base = dict(poses[2])
    q = []
    for k in range(10):
        if k == 0:
            q.append(poses[0])
            continue
        p = dict(base)
        u = min(1.0, k / 6.0)
        p["fall"] = None
        p["sink"] = 0.0
        p["root"] = (-1.5, 0.0, -2.0 - 3.0 * u)
        p["lean"] = -10.0 + 4.0 * u
        p["roll"] = 4.0 * u
        p["twist"] = 0.0
        p["head"] = (18.0 + 26.0 * u, 6.0, 10.0 + 6 * u)
        p["handL"] = p["handR"] = None
        p["elbowL"] = p["elbowR"] = None
        p["footL"] = (2.0, -8.0, 0.0)
        p["footR"] = (-1.0, 8.5, 0.0)
        p["eye"] = "x"
        q.append(p)
    return q


def v_pinned(mod, d, poses, ms, rnd):
    import kit
    out = []
    qs = pinned_poses(mod, d, poses)
    for k, p in enumerate(qs):
        im, S, B = render(mod, d, p)
        body = opaque(im)
        if k == 1:      # 뒤로 튕겨 벽에 박힘(2도트 북쪽으로)
            im2 = Image.new("RGBA", im.size, (0, 0, 0, 0))
            im2.alpha_composite(im, (0, -2))
            im = im2
            body = opaque(im)
        cx, cy = scr(B, erig.add(S.chest, erig.mul(S.fax, 6.0)))
        if k == 1:
            cy -= 2
        adir = erig.norm(erig.add(erig.add(S.fax, erig.mul(S.rax, 0.65)), erig.mul(S.up, 0.35)))   # 3차: 정면에서 화살이 셔츠에 묻힘 → 옆·위로 비스듬히
        fx, fy = scr(B, erig.add(S.chest, erig.mul(adir, 26.0)))
        # 피 흘러내림(가슴 상처 → 아래), 프레임마다 길어짐
        if k >= 1:
            stain(im, body, cx, cy + 3, min(7.0, 3 + 0.6 * k), rnd, down=3.2, dens=0.6)
        # 화살대: 가슴에서 카메라·앞 쪽으로(앞 축) — 화면에 짧게 보이면 최소 10도트
        dx, dy = fx - cx, fy - cy
        L = math.hypot(dx, dy)
        if L < 16:
            dx, dy = (dx / (L or 1)) * 16 if L else 0, (dy / (L or 1)) * 16 if L else -16
            fx, fy = cx + dx, cy + dy
        cells = gk.line_cells(cx, cy, fx, fy)
        for i, (x, y) in enumerate(cells):
            put(im, x, y, kit.WD[4] if i % 5 else kit.WD[3])
        ex, ey = cells[-1]
        sl = math.hypot(dx, dy) or 1
        nx_, ny_ = -dy / sl, dx / sl
        for j in range(1, 4):
            put(im, ex - dx / sl * j + nx_ * 1.5, ey - dy / sl * j + ny_ * 1.5, G[10])
            put(im, ex - dx / sl * j - nx_ * 1.5, ey - dy / sl * j - ny_ * 1.5, G[6])
        put(im, cx, cy, BL0)
        put(im, cx + 1, cy, BL3)
        # 등 뒤로 벽까지 꿰뚫은 화살 끝(몸 뒤 빈 칸에만)
        bx, by = scr(B, erig.add(S.chest, erig.mul(S.fax, -14.0)))
        for (x, y) in gk.line_cells(cx, cy, bx, by):
            put_under(im, x, y, gk.hexrgb(kit.WD[2]))
        # 발밑 방울(4~)
        if k >= 4:
            gx, gy = scr(B, (S.pel[0], S.pel[1], 0.0))
            for c in gk.disc_cells(gx + 2, gy - 1, 1.0 + 0.6 * (k - 4), sy=0.5):
                put_under(im, c[0], c[1], BL1)
        out.append(im)
    return out


def char(im, c, rnd_seed):
    """숯빛 그을림: 노이즈 < c 인 몸 픽셀을 밝기에 따라 G1~G4 로(셀아웃은 그대로)."""
    px = im.load()
    W, H = im.size
    for y in range(H):
        for x in range(W):
            p = px[x, y]
            if not p[3]:
                continue
            n = (((x // 2) * 92837111) ^ ((y // 2) * 689287499) ^ rnd_seed) % 1000 / 1000.0
            yy = 1 - y / H                      # 아래(발)부터 타오름
            if n * 0.7 + yy * 0.3 < c:
                L = lum(p)
                px[x, y] = gk.hexrgb(G[1] if L < 40 else (G[2] if L < 80 else (G[3] if L < 130 else G[4])))


def flames(im, body, k, n, rnd, hot=1.0):
    """불길 혀: 몸 픽셀 중 위쪽 가장자리에서 위로 4~10도트(겉 A19/21 → A23 → 심 A25/26)."""
    tops = [(x, y) for (x, y) in body if (x, y - 1) not in body]
    if not tops:
        return
    r2 = random.Random(1000 + k)
    for i in range(n):
        x, y = tops[r2.randrange(len(tops))]
        h = int(r2.uniform(4, 11) * hot)
        sway = r2.uniform(-0.25, 0.25)
        for j in range(h):
            w = max(0, int((1 - j / h) * 2.2))
            xx = x + sway * j
            for dx in range(-w, w + 1):
                col = A[26] if (abs(dx) == 0 and j < h * 0.35) else (A[25] if abs(dx) <= 0 and j < h * 0.6 else
                                                                      (A[23] if abs(dx) < w or j < h * 0.4 else A[21]))
                if j >= h - 2:
                    col = A[21] if j == h - 2 else A[19]
                put(im, xx + dx, y - j, col)


def v_burn(mod, d, poses, ms, rnd):
    out = []
    cc = [0.0, 0.12, 0.25, 0.4, 0.55, 0.68, 0.8, 0.9, 1.0, 1.05]
    nf = [10, 14, 16, 16, 15, 13, 10, 6, 3, 0]
    for k, p in enumerate(poses):
        im, S, B = render(mod, d, p)
        body = opaque(im)
        char(im, cc[k], 4021)
        flames(im, body, k, nf[k], rnd, hot=1.0 if k < 7 else 0.6)
        if k >= 7:   # 남은 불씨·연기
            r2 = random.Random(77 + k)
            bl = list(body)
            for i in range(10 if k < 9 else 6):
                x, y = bl[r2.randrange(len(bl))]
                put(im, x, y, A[21] if i % 3 else A[23])
            for i in range(5):
                x, y = bl[r2.randrange(len(bl))]
                for j in range(2, 6 + (k - 7) * 2):
                    put_under(im, x + math.sin(j * 0.8 + i) * 1.2, y - j - (k - 7) * 2, G[4] if j % 2 else G[3])
        out.append(im)
    return out


VFN = {"collapse": v_collapse, "behead": v_behead, "bisect": v_bisect, "pinned": v_pinned, "burn": v_burn}
VNOTE = {
    "collapse": "쓰러짐(기본) — 원래 사망 자세 + 가슴 베인 상처 2 + 옷이 피에 젖어 번짐 + 0 프레임 작은 분출. 시체 밑 웅덩이는 fx/v5/blood_pool",
    "behead": "목 잘림 — 머리 쪽 부위가 없는 몸이 비틀거리다 무릎 꿇고 뒤로 쓰러짐. 목 단면(목뼈) + 0~5 동맥 분출 3맥박 + 6~ 목에서 번지는 피. 머리는 fx/v5/gore_parts_<적> 행 head 를 시스템이 날림",
    "bisect": "두 동강 — 0 허리를 가르는 피 선 → 윗몸이 북쪽으로 미끄러져 떨어지고(최대 16도트) 다리는 원래 사망 자세로 쓰러짐. 단면(척추 뼈 1 · 피 테) + 둘 사이 끌린 피",
    "pinned": "화살로 벽에 박힘 — 0 맞음 → 1 뒤로 튕겨 박힘 → 선 채로 늘어져 고개 숙임(시체로 남음, 마지막 프레임 유지). 가슴 화살대 + 흘러내리는 피 + 발밑 방울",
    "burn": "불탐 — 불길(호박 램프 A19~A26)이 몸 위로 타오르며 발부터 숯빛(G1~G4)으로 그을림 → 7~ 불길 잦아들고 연기·불씨. 불 픽셀은 emissive",
}


def death_meta(eid, v, bm):
    m = {k: bm[k] for k in ("directions", "frameDurationsMs", "pivot", "pixelScale") if k in bm}
    m.update({"action": "death_" + v, "loop": False, "holdLastFrame": True, "enemy": eid, "variant": v,
              "baseSheet": "enemies/v3/%s_death" % eid, "event": "ENEMY_DEATH_VARIANT.variant = %s" % v,
              "note": VNOTE[v], "source": SRC,
              "palette": "parts/art/palette/lopad.json — 적 본 색(같은 리그) + 피 7층 '적' 램프 어두운 5단(고정) + 불 1층 호박 램프 + 숯 G. 새 색 없음",
              "paletteSwap": "none", "rim": "없음(_rim·_elite 사망 변형은 만들지 않음 — 시스템은 변형 재생 중 림 오버레이를 끔)"})
    if v == "burn":
        m["emissiveColors"] = [A[21], A[23], A[25], A[26]]
        m["glowFrames"] = [1, 2, 3, 4, 5, 6, 7]
    if v == "behead":
        m["detachFrame"] = 0
        m["detachNote"] = "0 프레임 시작에 gore_parts 행 head 를 목 자리에서 띄움(시스템 — 0.5~0.9초 날아 바닥에 남음, 시체 수 포함)"
    if v == "bisect":
        m["detachFrame"] = 1
    return m


def build_enemy(args):
    eid, variants, assets = args
    mod = importlib.import_module(MODS[eid])
    bm = json.load(open(os.path.join(gk.SPR, "enemies", "v3", eid + "_death.json"), encoding="utf-8"))
    ms = bm["frameDurationsMs"]
    res = {}
    for v in variants:
        rows = []
        for d in DIRS:
            poses = mod.ACTIONS["death"](d)
            assert len(poses) == len(ms), (eid, len(poses), len(ms))
            fr = VFN[v](mod, d, poses, ms, random.Random(sum(map(ord, eid)) * 131 + DIRS.index(d) * 7 + VARIANTS.index(v)))
            rows.append([f.tobytes() for f in fr])
        res[v] = (rows, fr[0].size)
    return eid, res


def main(argv):
    names = [a for a in argv if not a.startswith("-")] or ENEMIES
    variants = VARIANTS
    for a in argv:
        if a.startswith("--variants="):
            variants = a.split("=")[1].split(",")
    assets = "--no-assets" not in argv
    with Pool(4) as pool:
        out = pool.map(build_enemy, [(e, variants, assets) for e in names], chunksize=1)
    for eid, res in out:
        bm = json.load(open(os.path.join(gk.SPR, "enemies", "v3", eid + "_death.json"), encoding="utf-8"))
        for v, (rows, size) in res.items():
            imgs = [[Image.frombytes("RGBA", size, b) for b in row] for row in rows]
            name = "%s_death_%s" % (eid, v)
            if assets:
                gk.write_sheet("enemies", "v4", name, imgs, death_meta(eid, v, bm))
            gk.preview(imgs, os.path.join(HERE, "out", "preview", name + ".png"), scale=2, bg=(52, 50, 48))
            print("ok", name, flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
