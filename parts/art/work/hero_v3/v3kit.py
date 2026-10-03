"""v3 (52라운드 Q8, 2배 밀도) 캐릭터 렌더러 — Pillow 만 사용, 결정적.

v2 kit.Rig 는 부위 경계 1px 만 밝히고 어둡게 해서 64×96 에서는 면이 납작하게 보인다.
v3 는 부위 마스크를 흐려 기울기로 법선을 근사하고(빛 = 화면 좌상단), 단계로 나눠(4~6단) 부피를 만든다.
- 겹침 그림자: 앞 부위가 뒤 부위 위로 오른쪽 아래 1~2px 그늘을 드리움(한 단 어둡게)
- 내부 선: 앞 부위와 맞닿은 뒤 부위 픽셀을 두 단 어둡게(검은 선 대신 재질 그늘 = 안티앨리어싱 수준)
- 셀아웃: 실루엣 바깥 1px. 빛 쪽(위·왼쪽만 비어 있음)은 재질의 가장 어두운 색, 나머지는 OUT
- 가장자리 빛(rim): 셀아웃 바로 안쪽 1px 을 한 단 밝게 — 어두운 바닥에서 실루엣이 산다(52라운드 지시)
- 반투명 0. 덧칠(dot)은 셰이딩 뒤 원색 그대로(눈빛·균열 혼불 등 자체 발광).
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE_V3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE_V3, "..", "v2_outer"))
import kit  # noqa: E402  (팔레트: kit.G, kit.A, kit.SL, kit.WD, kit.PL, 조명 목업 kit.light_scene)

G, A, SL, WD, PL = kit.G, kit.A, kit.SL, kit.WD, kit.PL
OUT = SL[0]
CLEAR = (0, 0, 0, 0)

_L = (-0.58, -0.70, 0.62)
_n = math.sqrt(sum(c * c for c in _L))
LIGHT = tuple(c / _n for c in _L)


class Part:
    __slots__ = ("name", "ramp", "base", "group", "soft", "rim", "cast", "flat", "mask", "z", "bands", "vgrad", "warm")

    def __init__(self, name, ramp, base, group=None, soft=2.0, rim=True, cast=True, flat=False, bands=None,
                 vgrad=0.0, warm=None):
        self.name, self.ramp, self.base = name, ramp, base
        self.group = group or name
        self.soft = soft          # 법선 근사용 흐림 반경(px) — 두꺼운 부위일수록 크게
        self.rim = rim
        self.cast = cast
        self.flat = flat
        self.bands = bands        # (빛 단계 임계값) 기본 BANDS
        self.vgrad = vgrad        # 0 아님: 부위 아래쪽 이 비율부터 한 단 어둡게(바닥 쪽 그늘·부피)
        self.warm = rim if warm is None else warm   # 혼불 빛 번짐을 받는 재질
        self.mask = None
        self.z = 0


BANDS = ((0.86, 2), (0.70, 1), (0.40, 0), (0.12, -1), (-9, -2))


class Rig3:
    """S·src·dst: 설계 좌표(64×96 골격, 피벗 src) → 픽셀 좌표(피벗 dst) 변환. 53라운드 Q1 = 1.5배(96×144, 피벗 (48,138)).
    도형(poly·ellipse·capsule)·반지름·흐림은 S 배로 다시 래스터·셰이딩한다(최근접 확대 아님).
    dot()/line() 은 설계 좌표, px()/pline() 은 픽셀 좌표(1.5배 해상도에서 새로 그린 세부)."""

    def __init__(self, w, h, S=1.0, src=(0.0, 0.0), dst=(0.0, 0.0)):
        self.w, self.h = w, h
        self.S, self.src, self.dst = S, src, dst
        self.parts = []
        self.dots = []      # (x, y, color) 셰이딩 뒤 덧칠
        self.spill = []     # (x, y, radius) 혼불 빛 번짐(주변 몸 픽셀을 따뜻한 어둠으로)
        self.spill_cells = []   # 균열 경로 픽셀 — 경로를 따라 1.5px 안 A18, 2.5px 안 A17
        self.holes = set()      # 강제로 비우는 픽셀 — 재가 부스러져 떨어진 가장자리 결손
        self.anchors = {}       # 2단계: 이름 → (x, y) 화면 좌표(손·엉덩이·어깨 등, 무기 오버레이 기준점)
        self.owner = self.outline = self.image = None

    # --- 좌표 변환 ----------------------------------------------------------
    def T(self, p):
        return (self.dst[0] + self.S * (p[0] - self.src[0]), self.dst[1] + self.S * (p[1] - self.src[1]))

    # --- 마스크 그리기 ------------------------------------------------------
    def _new(self, part):
        part.soft *= self.S
        part.mask = Image.new("L", (self.w, self.h), 0)
        part.z = len(self.parts)
        self.parts.append(part)
        return ImageDraw.Draw(part.mask)

    def poly(self, part, pts):
        pts = [self.T(q) for q in pts]
        self._new(part).polygon([(round(x), round(y)) for x, y in pts], fill=255)
        return part

    def ellipse(self, part, cx, cy, rx, ry):
        cx, cy = self.T((cx, cy))
        rx, ry = rx * self.S, ry * self.S
        self._new(part).ellipse((round(cx - rx), round(cy - ry), round(cx + rx), round(cy + ry)), fill=255)
        return part

    def capsule(self, part, pts, radii):
        """관절 점 목록 + 점별 반지름 → 가늘어지는 팔다리."""
        d = self._new(part)
        capsule_on(d, [self.T(q) for q in pts], [r * self.S for r in radii])
        return part

    def shape(self, part, fn):
        """fn(draw) 로 자유 도형(픽셀 좌표)."""
        fn(self._new(part))
        return part

    def dot(self, x, y, c):
        x, y = self.T((x, y))
        self.dots.append((round(x), round(y), c))

    def px(self, x, y, c):
        self.dots.append((round(x), round(y), c))

    def cdot(self, x, y, c, part=None):
        """픽셀 덧칠 — part(부위 이름 앞부분)를 주면 그 부위가 차지한 픽셀(셀아웃 제외)에만 칠한다."""
        if part is None:
            self.dots.append((round(x), round(y), c))
        else:
            self.dots.append((round(x), round(y), c, part))

    def line(self, pts, c):
        self.pline([self.T(q) for q in pts], c)

    def pline(self, pts, c):
        for x, y in raster_path(pts):
            self.dots.append((x, y, c))

    def hole(self, cx, cy, r):
        """설계 좌표 원 결손 → 픽셀."""
        cx, cy = self.T((cx, cy))
        r *= self.S
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    self.holes.add((x, y))

    # --- 렌더 ---------------------------------------------------------------
    def render(self, rim=True):
        W, H = self.w, self.h
        owner = [[-1] * W for _ in range(H)]
        mp = [p.mask.load() for p in self.parts]
        for i, p in enumerate(self.parts):
            m = mp[i]
            for y in range(H):
                row = owner[y]
                for x in range(W):
                    if m[x, y] > 127:
                        row[x] = i
        for x, y in self.holes:
            if 0 <= x < W and 0 <= y < H:
                owner[y][x] = -1
        level = [[0] * W for _ in range(H)]
        # 1) 법선 셰이딩
        for i, p in enumerate(self.parts):
            if p.flat:
                for y in range(H):
                    for x in range(W):
                        if owner[y][x] == i:
                            level[y][x] = p.base
                continue
            blur = p.mask.filter(ImageFilter.GaussianBlur(p.soft)).load()
            bands = p.bands or BANDS
            bb = p.mask.getbbox() or (0, 0, 1, 1)
            vcut = bb[1] + (bb[3] - bb[1]) * p.vgrad if p.vgrad else 1e9
            for y in range(H):
                for x in range(W):
                    if owner[y][x] != i:
                        continue
                    gx = (blur[min(W - 1, x + 1), y] - blur[max(0, x - 1), y]) / 255.0
                    gy = (blur[x, min(H - 1, y + 1)] - blur[x, max(0, y - 1)]) / 255.0
                    nx, ny, nz = -gx, -gy, 0.55
                    n = math.sqrt(nx * nx + ny * ny + nz * nz)
                    dl = (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / n
                    off = -2
                    for th, o in bands:
                        if dl > th:
                            off = o
                            break
                    level[y][x] = p.base + off - (1 if y >= vcut else 0)
        # 2) 겹침 그림자 + 내부 선
        for y in range(H):
            for x in range(W):
                i = owner[y][x]
                if i < 0:
                    continue
                g = self.parts[i].group
                for dx, dy in ((-1, -1), (-2, -2), (-1, 0), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < W and 0 <= yy < H:
                        j = owner[yy][xx]
                        if j > i and self.parts[j].group != g and self.parts[j].cast:
                            level[y][x] -= 1
                            break
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < W and 0 <= yy < H:
                        j = owner[yy][xx]
                        if j > i and self.parts[j].group != g:
                            level[y][x] -= 1
                            break
        # 3) 셀아웃 판정
        def opaque(x, y):
            return 0 <= x < W and 0 <= y < H and owner[y][x] >= 0

        outline = [[0] * W for _ in range(H)]   # 0 아님, 1 빛 쪽, 2 그늘 쪽
        for y in range(H):
            for x in range(W):
                if owner[y][x] < 0:
                    continue
                tl = not opaque(x - 1, y) or not opaque(x, y - 1)
                br = not opaque(x + 1, y) or not opaque(x, y + 1)
                if br:
                    outline[y][x] = 2
                elif tl:
                    outline[y][x] = 1
        # 4) 가장자리 빛: 셀아웃 바로 안쪽
        if rim:
            for y in range(H):
                for x in range(W):
                    i = owner[y][x]
                    if i < 0 or outline[y][x] or not self.parts[i].rim:
                        continue
                    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                        xx, yy = x + dx, y + dy
                        if 0 <= xx < W and 0 <= yy < H and outline[yy][xx]:
                            level[y][x] = max(level[y][x] + 1, self.parts[i].base)
                            break
        # 5) 색 칠하기
        out = Image.new("RGBA", (W, H), CLEAR)
        po = out.load()
        for y in range(H):
            for x in range(W):
                i = owner[y][x]
                if i < 0:
                    continue
                p = self.parts[i]
                if outline[y][x] == 2:
                    po[x, y] = OUT
                elif outline[y][x] == 1:
                    po[x, y] = p.ramp[0]
                else:
                    po[x, y] = p.ramp[max(0, min(len(p.ramp) - 1, level[y][x]))]
        # 6) 혼불 빛 번짐 (몸 픽셀만, 셀아웃 제외)
        for sx, sy, r in self.spill:
            for y in range(int(sy - r), int(sy + r) + 1):
                for x in range(int(sx - r), int(sx + r) + 1):
                    if not (0 <= x < W and 0 <= y < H) or owner[y][x] < 0 or outline[y][x]:
                        continue
                    d = math.hypot(x - sx, y - sy)
                    if d <= r and self.parts[owner[y][x]].warm:
                        po[x, y] = A[18] if d <= r * 0.55 else A[17]
        if self.spill_cells:
            best = {}
            for cx, cy in self.spill_cells:
                for yy in range(cy - 3, cy + 4):
                    for xx in range(cx - 3, cx + 4):
                        d = (xx - cx) ** 2 + (yy - cy) ** 2
                        if d <= 6.25 and d < best.get((xx, yy), 99):
                            best[(xx, yy)] = d
            for (x, y), d in best.items():
                if not (0 <= x < W and 0 <= y < H) or owner[y][x] < 0 or outline[y][x] or not self.parts[owner[y][x]].warm:
                    continue
                po[x, y] = A[18] if d <= 2.25 else A[17]
        # 7) 덧칠
        for dt in self.dots:
            x, y, c = dt[0], dt[1], dt[2]
            if 0 <= x < W and 0 <= y < H and (x, y) not in self.holes:      # 결손 칸엔 덧칠하지 않음(떠 있는 점 방지)
                if len(dt) == 4:
                    i = owner[y][x]
                    if i < 0 or outline[y][x] or not self.parts[i].name.startswith(dt[3]):
                        continue
                po[x, y] = c
        # 2단계(무기 오버레이·가림 계산)용: 픽셀별 부위 소유 · 셀아웃 판정 · 결과 보관
        self.owner, self.outline, self.image = owner, outline, out
        return out

    def part_at(self, x, y):
        """render() 뒤: (x, y) 픽셀을 차지한 부위 이름(없으면 None)."""
        if not (0 <= x < self.w and 0 <= y < self.h):
            return None
        i = self.owner[y][x]
        return self.parts[i].name if i >= 0 else None


def raster_path(pts):
    """픽셀 좌표 꺾은선 → 끊김 없는 픽셀 목록(중복 없음, 순서 유지)."""
    seen, out = set(), []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 1.5) + 1
        for k in range(n + 1):
            t = k / n
            c = (round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t))
            if c not in seen:
                seen.add(c)
                out.append(c)
    if len(pts) == 1:
        out = [(round(pts[0][0]), round(pts[0][1]))]
    return out


def capsule_on(d, pts, radii):
    for (x0, y0), (x1, y1), r0, r1 in zip(pts, pts[1:], radii, radii[1:]):
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        d.polygon([(round(x0 + nx * r0), round(y0 + ny * r0)), (round(x1 + nx * r1), round(y1 + ny * r1)),
                   (round(x1 - nx * r1), round(y1 - ny * r1)), (round(x0 - nx * r0), round(y0 - ny * r0))], fill=255)
    for (x, y), r in zip(pts, radii):
        d.ellipse((round(x - r), round(y - r), round(x + r), round(y + r)), fill=255)


def ik2(hip, foot, l1, l2, bend):
    """2관절 IK — bend = +1/-1 (무릎·팔꿈치가 굽는 쪽: 진행 방향 기준 x 부호)."""
    hx_, hy = hip
    fx, fy = foot
    dx, dy = fx - hx_, fy - hy
    d = math.hypot(dx, dy)
    d = min(d, l1 + l2 - 0.01)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / (math.hypot(dx, dy) or 1), dy / (math.hypot(dx, dy) or 1)
    mx, my = hx_ + ux * a, hy + uy * a
    # 수직 방향 중 bend 쪽
    px, py = -uy, ux
    if px * bend < 0:
        px, py = -px, -py
    return (mx + px * h, my + py * h)


def colors_of(im):
    return {c[:3] for c in im.getdata() if c[3]}


def has_alpha_partial(im):
    return any(0 < c[3] < 255 for c in im.getdata())
