"""v2 (50라운드) 공통 도구 — 팔레트 v2 제안 블록, 픽셀 캔버스, 부위(파트) 셰이딩 리그, 조명 합성.

Pillow 만 사용. 모든 렌더는 결정적(시드 고정).
- 팔레트: 기존 lopad.json 의 gray 16 + 1층 램프 12 를 그대로 읽고, v2 재질 블록(제안, 임시)을 상수로 둔다.
  재질 블록은 `palette_v2_proposal.json` 으로도 내보낸다(build.py). lopad.json 은 건드리지 않는다.
- 리그: 부위를 마스크로 그려 넣으면 빛(좌상단) 방향 기준으로 하이라이트·그림자·겹침 그림자·셀아웃을 자동으로 칠한다.
  좌우 방향은 형태만 뒤집고 셰이딩은 다시 계산하므로 빛 방향이 항상 좌상단으로 유지된다(바이블 3절 LIGHT_SWAP 과 같은 효과).
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageChops, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(ROOT, ".claude/skills/pixel-art-studio/scripts"))

_PAL = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))


def hx(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def tohex(c):
    return "#%02x%02x%02x" % tuple(c[:3])


G = [hx(c) for c in _PAL["gray"]]                       # G00..G15 (고정)
A = {16 + i: hx(c) for i, c in enumerate(_PAL["floors"][0]["ramp"])}   # 1층 램프 슬롯 16..27 (런타임 스왑)
X = [hx(c) for c in _PAL["fx"]["core"]]                 # 백열 코어 (이펙트 전용 — 여기서는 목업 불티에만)

# ---------------------------------------------------------------------------
# v2 재질 블록 (제안 · 임시 · 층 스왑 대상 아님). 중간 톤을 넉넉히 둔 재질 램프.
# 어두운 쪽은 청색, 밝은 쪽은 황색으로 기울인 hue-shift 램프. 완전한 검정은 쓰지 않는다(§9 조명).
# ---------------------------------------------------------------------------
V2 = {
    # 판석·돌(차가운 청회) 8
    "SL": ["#14161c", "#1d2028", "#272b35", "#323743", "#3f4552", "#4e5563", "#626a78", "#7e8693"],
    # 나무(엄버) 6
    "WD": ["#1b1411", "#2a1e17", "#3b2a1f", "#4f3828", "#664a33", "#82623f"],
    # 회반죽·천(때 묻은 따뜻한 회색) 5
    "PL": ["#45403b", "#5c554e", "#756c62", "#90857a", "#ada08f"],
    # 밤 원경(void) 3
    "NT": ["#0b0c11", "#11141b", "#181c26"],
}
SL = [hx(c) for c in V2["SL"]]
WD = [hx(c) for c in V2["WD"]]
PL = [hx(c) for c in V2["PL"]]
NT = [hx(c) for c in V2["NT"]]

OUTLINE = SL[0]          # 캐릭터 셀아웃(완전한 검정 대신 아주 어두운 청흑)
CLEAR = (0, 0, 0, 0)

# 자체 발광(조명 계산에서 어둡혀지지 않는) 색 — 1층 램프 23~27 + 코어.
EMISSIVE = [A[i] for i in (23, 24, 25, 26, 27)] + X


def palette_v2_json():
    return {
        "name": "LOPAD v2 material block (proposal)",
        "status": "임시 제안 — 50라운드 시범(1층 외곽 거리). 도영 님 검수 전. lopad.json 미반영",
        "scope": "타일·소품·캐릭터 재질 중간 톤. 층 스왑 대상 아님(고정). 층 강조 램프 16~27 은 그대로 런타임 스왑",
        "blocks": V2,
        "roles": {
            "SL": "판석·돌담·쇠(차가운 청회) 0 줄눈/셀아웃 · 1~2 그늘 · 3~4 본색 · 5 빛 · 6~7 젖은 반사/모서리",
            "WD": "목재 기둥·문·술통·상자 0 틈 · 1~2 그늘 · 3 본색 · 4~5 빛",
            "PL": "회반죽 벽·천막·빨래 0 그늘 · 1~2 본색 · 3~4 빛",
            "NT": "void 밤 원경(지붕 바다·하늘) — 조명 밖 기본 어둠",
        },
        "emissive": [tohex(c) for c in EMISSIVE],
        "emissiveNote": "이 색 픽셀은 자체 발광(등불 불꽃·창 불빛·눈빛). 시스템 조명이 곱하기 방식이면 이 색만 가산 레이어로 다시 그려 어둠에 묻히지 않게(목업 방식)",
    }


# ---------------------------------------------------------------------------
# 캔버스
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg=CLEAR):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), bg)
        self.p = self.im.load()

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.p[x, y] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[x, y]
        return CLEAR

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.p[x, y] = c

    def hline(self, x0, x1, y, c):
        self.rect(min(x0, x1), y, max(x0, x1), y, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, min(y0, y1), x, max(y0, y1), c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy

    def mask_fill(self, mask, c, only=None):
        """mask: 'L' 이미지 같은 크기. only: 함수(rgba)->bool 로 덮을 픽셀 제한."""
        mp = mask.load()
        for y in range(self.h):
            for x in range(self.w):
                if mp[x, y] > 127:
                    if only is None or only(self.p[x, y]):
                        self.p[x, y] = c

    def poly(self, pts, c):
        m = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        self.mask_fill(m, c)

    def ellipse(self, box, c):
        m = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(m).ellipse(box, fill=255)
        self.mask_fill(m, c)

    def paste(self, im, x, y):
        self.im.alpha_composite(im, (x, y)) if x >= 0 and y >= 0 else _paste_clip(self.im, im, x, y)
        self.p = self.im.load()

    def noise(self, x0, y0, x1, y1, c, density, seed, only=None):
        r = Rand(seed)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if r.f() < density:
                    if only is None or self.get(x, y)[:3] == only[:3]:
                        self.px(x, y, c)


def _paste_clip(dst, src, x, y):
    sx0, sy0 = max(0, -x), max(0, -y)
    crop = src.crop((sx0, sy0, src.width, src.height))
    dst.alpha_composite(crop, (max(0, x), max(0, y)))


class Rand:
    """결정적 LCG."""
    def __init__(self, seed):
        self.s = (seed * 2654435761 + 12345) & 0xFFFFFFFF

    def f(self):
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF

    def i(self, a, b):
        return a + int(self.f() * (b - a + 1)) if b >= a else a

    def choice(self, seq):
        return seq[min(len(seq) - 1, int(self.f() * len(seq)))]


def shade(c, k):
    """색 c 를 k(−1..1) 만큼 어둡게/밝게 (팔레트 밖 색은 목업 조명에서만 쓴다)."""
    r, g, b, a = c
    if k >= 0:
        return (int(r + (255 - r) * k), int(g + (255 - g) * k), int(b + (255 - b) * k), a)
    k = -k
    return (int(r * (1 - k)), int(g * (1 - k)), int(b * (1 - k)), a)


# ---------------------------------------------------------------------------
# 부위 리그 (캐릭터·적)
# ---------------------------------------------------------------------------
class Part:
    __slots__ = ("name", "ramp", "base", "group", "hl", "sh", "edge", "flat", "cast")

    def __init__(self, name, ramp, base, group=None, hl=1, sh=1, edge=False, flat=False, cast=True):
        self.name, self.ramp, self.base = name, ramp, base
        self.group = group or name
        self.hl, self.sh = hl, sh          # 하이라이트 폭 · 그림자 폭(px)
        self.edge = edge                   # 뒤 부위와의 경계에 어두운 선
        self.flat = flat                   # 셰이딩 없이 base 만
        self.cast = cast                   # 뒤 부위에 겹침 그림자를 드리움


class Rig:
    """부위 마스크를 z 순서대로 쌓고 render() 로 셰이딩·셀아웃."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.pid = [[-1] * w for _ in range(h)]
        self.parts = []
        self.over = []      # 셰이딩 뒤 덧칠 (x, y, color)
        self.erase = set()

    def _id(self, part):
        self.parts.append(part)
        return len(self.parts) - 1

    def _stamp(self, part, mask):
        i = self._id(part)
        mp = mask.load()
        for y in range(self.h):
            row = self.pid[y]
            for x in range(self.w):
                if mp[x, y] > 127:
                    row[x] = i
        return i

    def _mask(self):
        return Image.new("L", (self.w, self.h), 0)

    def poly(self, part, pts):
        m = self._mask(); ImageDraw.Draw(m).polygon([(round(a), round(b)) for a, b in pts], fill=255)
        return self._stamp(part, m)

    def rect(self, part, x0, y0, x1, y1):
        m = self._mask(); ImageDraw.Draw(m).rectangle((round(x0), round(y0), round(x1), round(y1)), fill=255)
        return self._stamp(part, m)

    def ellipse(self, part, x0, y0, x1, y1):
        m = self._mask(); ImageDraw.Draw(m).ellipse((round(x0), round(y0), round(x1), round(y1)), fill=255)
        return self._stamp(part, m)

    def limb(self, part, pts, width):
        """관절 점 목록을 따라 굵은 선(팔·다리). width 정수."""
        m = self._mask(); d = ImageDraw.Draw(m)
        pts = [(round(a), round(b)) for a, b in pts]
        d.line(pts, fill=255, width=width)
        r = (width - 1) / 2
        for a, b in pts:
            d.ellipse((a - r, b - r, a + r, b + r), fill=255)
        return self._stamp(part, m)

    def pixels(self, part, coords):
        i = self._id(part)
        for x, y in coords:
            if 0 <= x < self.w and 0 <= y < self.h:
                self.pid[y][x] = i
        return i

    def dot(self, x, y, c):
        self.over.append((round(x), round(y), c))

    def render(self, outline=OUTLINE, rim=None, rim_side="rb", flash=None, light_left=True):
        """light_left: 빛이 화면 좌상단(항상 True — 좌우 반전 시에도 다시 계산)."""
        W, H, pid, parts = self.w, self.h, self.pid, self.parts

        def gid(x, y):
            if 0 <= x < W and 0 <= y < H and pid[y][x] >= 0:
                return parts[pid[y][x]].group
            return None

        def zid(x, y):
            if 0 <= x < W and 0 <= y < H:
                return pid[y][x]
            return -1

        out = Image.new("RGBA", (W, H), CLEAR)
        po = out.load()
        for y in range(H):
            for x in range(W):
                i = pid[y][x]
                if i < 0 or (x, y) in self.erase:
                    continue
                P = parts[i]
                g = P.group
                v = P.base
                if not P.flat:
                    # 빛 쪽(좌·상) 경계
                    if P.hl and (gid(x - 1, y) != g or gid(x, y - 1) != g):
                        v += 1
                    # 그림자 쪽(우·하) 경계 — 폭 sh
                    dark = False
                    for k in range(1, P.sh + 1):
                        if gid(x + k, y) != g or gid(x, y + k) != g:
                            dark = True
                            break
                    if dark:
                        v -= 1
                    # 겹침 그림자: 좌상단에 더 앞(z 큰) 다른 그룹이 있으면
                    for dx, dy in ((-1, -1), (-1, 0), (0, -1)):
                        j = zid(x + dx, y + dy)
                        if j > i and parts[j].group != g and parts[j].cast:
                            v -= 1
                            break
                v = max(0, min(len(P.ramp) - 1, v))
                c = P.ramp[v]
                # 앞 부위 경계선: 이 부위가 뒤 부위(z 작음, 다른 그룹)와 맞닿으면 그 뒤 픽셀을 어둡게
                po[x, y] = c
        # 경계선(edge): 앞 부위 둘레에 맞닿은 뒤 부위 픽셀을 가장 어두운 색으로
        for y in range(H):
            for x in range(W):
                i = pid[y][x]
                if i < 0 or po[x, y][3] == 0:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    j = zid(x + dx, y + dy)
                    if j > i and parts[j].edge and parts[j].group != parts[i].group:
                        po[x, y] = parts[i].ramp[0]
                        break
        # 셀아웃 (안쪽 1px)
        res = out.copy()
        pr = res.load()
        for y in range(H):
            for x in range(W):
                if po[x, y][3] == 0:
                    continue
                tl = (x == 0 or po[x - 1, y][3] == 0) or (y == 0 or po[x, y - 1][3] == 0)
                br = (x == W - 1 or po[x + 1, y][3] == 0) or (y == H - 1 or po[x, y + 1][3] == 0)
                if tl or br:
                    i = pid[y][x]
                    P = parts[i]
                    if br and rim is not None and ("r" in rim_side and (x == W - 1 or po[x + 1, y][3] == 0)
                                                  or "b" in rim_side and (y == H - 1 or po[x, y + 1][3] == 0)):
                        pr[x, y] = rim
                    elif tl and not br:
                        # 빛 쪽 셀아웃은 재질의 가장 어두운 색(셀렉티브 아웃라인)
                        pr[x, y] = P.ramp[0] if P.ramp[0] != P.ramp[min(1, len(P.ramp) - 1)] else outline
                    else:
                        pr[x, y] = outline
        for x, y, c in self.over:
            if 0 <= x < W and 0 <= y < H:
                pr[x, y] = c
        if flash is not None:
            for y in range(H):
                for x in range(W):
                    if pr[x, y][3]:
                        edge = any(not (0 <= x + dx < W and 0 <= y + dy < H) or pr[x + dx, y + dy][3] == 0
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                        pr[x, y] = outline if edge else flash
        return res


def silhouette(im):
    """불투명 영역 마스크(L)."""
    return im.split()[3].point(lambda a: 255 if a else 0)


def mirror(im):
    return im.transpose(Image.FLIP_LEFT_RIGHT)


# ---------------------------------------------------------------------------
# 시트·JSON
# ---------------------------------------------------------------------------
DIRS = ["down", "up", "left", "right"]


def sheet(frames_by_dir, fw, fh):
    """frames_by_dir: {dir: [Image]} → 행 = DIRS 순서."""
    n = len(frames_by_dir[DIRS[0]])
    out = Image.new("RGBA", (fw * n, fh * len(DIRS)), CLEAR)
    for r, d in enumerate(DIRS):
        for c, im in enumerate(frames_by_dir[d]):
            out.alpha_composite(im, (c * fw, r * fh))
    return out


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def colors_of(im):
    s = set()
    for c in im.getdata():
        if c[3]:
            s.add(c[:3])
    return s


def isolated(im):
    """4방향 이웃 중 같은 색이 하나도 없고 불투명 이웃이 0~1개인 외톨이(잡점) 수."""
    p = im.load(); w, h = im.size; n = 0
    for y in range(h):
        for x in range(w):
            c = p[x, y]
            if not c[3]:
                continue
            same = 0; opq = 0
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < w and 0 <= y + dy < h:
                    q = p[x + dx, y + dy]
                    if q[3]:
                        opq += 1
                        if q[:3] == c[:3]:
                            same += 1
            if opq <= 1 and same == 0:
                n += 1
    return n


def upscale(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


# ---------------------------------------------------------------------------
# 조명 합성 (목업 시뮬레이션) — 곱하기 조명 + 자체 발광 가산 + 빛 번짐 + 비네팅
# ---------------------------------------------------------------------------
def light_scene(albedo, lights, ambient=(0.26, 0.29, 0.40), vignette=0.55, scale=4,
                emissive=EMISSIVE, bloom=True):
    """albedo: RGBA(불투명). lights: [{x,y,color(hex),radius,intensity}]. 반환 RGB."""
    W, H = albedo.size
    lw, lh = W // scale, H // scale
    lm = Image.new("RGB", (lw, lh))
    lp = lm.load()
    Ls = []
    for L in lights:
        c = hx(L["color"])
        Ls.append((L["x"] / scale, L["y"] / scale, L["radius"] / scale, L["intensity"],
                   c[0] / 255, c[1] / 255, c[2] / 255))
    cx, cy = lw / 2, lh / 2
    for y in range(lh):
        for x in range(lw):
            r, g, b = ambient
            for (lx, ly, rad, it, cr, cg, cb) in Ls:
                d2 = ((x - lx) ** 2 + ((y - ly) * 1.15) ** 2) / (rad * rad)
                if d2 < 1.0:
                    f = (1 - d2) ** 2 * it
                    r += cr * f; g += cg * f; b += cb * f
            # 비네팅
            dv = (((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2) ** 0.5
            v = 1 - vignette * max(0.0, dv - 0.55) / 0.85
            v = max(0.25, v)
            lp[x, y] = (min(255, int(r * v * 255 / 1.6)), min(255, int(g * v * 255 / 1.6)),
                        min(255, int(b * v * 255 / 1.6)))
    lm = lm.resize((W, H), Image.BILINEAR)
    base = albedo.convert("RGB")
    lit = ImageChops.multiply(base, lm)
    # 1.6 배 과노출 여유: multiply 는 0..1 이므로 1.6 배로 키움(255/1.6 저장값 복원)
    lit = lit.point(lambda v: min(255, int(v * 1.6)))
    # 자체 발광 픽셀은 원색 그대로
    em = set(c[:3] for c in emissive)
    ap = albedo.load(); lp2 = lit.load()
    emask = Image.new("L", (W, H), 0); ep = emask.load()
    for y in range(H):
        for x in range(W):
            c = ap[x, y]
            if c[:3] in em:
                lp2[x, y] = c[:3]
                ep[x, y] = 255
    if bloom:
        glow = Image.new("RGB", (W, H), (0, 0, 0))
        glow.paste(lit, (0, 0), emask)
        glow = glow.filter(ImageFilter.GaussianBlur(6))
        glow = glow.point(lambda v: int(v * 0.9))
        lit = ImageChops.add(lit, glow)
    return lit
