"""53라운드 외벽 테두리 목업 — 1920×1080 렌더(논리 960×540 × 2).

외곽 v2 바닥 도트(assets/tiles/v2/stage1_outer, 32px → 렌더 64px) + Gemini 테두리(assets/tiles/border/outer, 렌더 1:1)
+ 캐릭터(주인공 v3 64×96 → 53라운드 Q1 크기 96×144 로 1.5배 근사, 결사병 v2 ×2) → 곱하기 조명 + 발광 가산 + 번짐 + 비네팅.
시스템 구현을 모르므로(교차 참조 금지) border.json 의 drawOrder·place 규칙만으로 쌓는다. 산출: parts/art/work/gemini/preview_border_outer*.png
"""
import json, math, os
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../../.."))
GEM = os.path.dirname(HERE)
TILES = os.path.join(ROOT, "assets/tiles/v2/stage1_outer")
BORDER = os.path.join(ROOT, "assets/tiles/border/outer")
SPR = os.path.join(ROOT, "assets/sprites")

R = 2                       # 렌더 px / 논리 px
T = 32                      # 타일 논리 px
FW, FH = 40, 24             # 전투장 바닥 칸
VIEW = (960, 540)           # 논리 화면
AMBIENT = (0.26, 0.29, 0.40)   # v2 목업과 같은 주변광(×1.6 여유)
AMBIENT_NEUTRAL = (0.34, 0.34, 0.38)   # 비교안: 키아트(숯빛 무채)에 가까운 중립 주변광 — 인터뷰 대상
try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 26)
except Exception:  # noqa
    FONT = None


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def label(im, text, xy, size=None):
    d = ImageDraw.Draw(im)
    f = FONT
    x, y = xy
    d.text((x + 2, y + 2), text, fill=(0, 0, 0), font=f)
    d.text((x, y), text, fill=(238, 226, 196), font=f)


def h2(x, y, n):
    v = (x * 73856093) ^ (y * 19349663) ^ 0x5bd1e995
    v = (v * 2654435761) & 0xFFFFFFFF
    return (v >> 13) % n


# ---------------------------------------------------------------------------
class World:
    """세계 좌표(논리 px, 바닥 왼쪽 위 = 0,0) → 렌더 캔버스. 알베도와 발광을 같은 순서로 쌓는다."""

    def __init__(self, bj):
        self.bj = bj
        b = bj["bands"]
        self.x0 = -b["west"]["width"]
        self.y0 = -b["north"]["baselineY"]
        self.x1 = FW * T + b["east"]["width"]
        self.y1 = FH * T - b["south"]["baselineY"] + b["south"]["height"]
        self.W = int((self.x1 - self.x0) * R)
        self.H = int((self.y1 - self.y0) * R)
        self.alb = Image.new("RGBA", (self.W, self.H), (14, 15, 20, 255))
        self.emi = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 255))
        self.lights = []

    def rp(self, x, y):
        return int(round((x - self.x0) * R)), int(round((y - self.y0) * R))

    def put(self, im, x, y, emissive=None, occlude=True):
        """im: 렌더 해상도 RGBA, (x,y) = 왼쪽 위 논리 좌표."""
        px, py = self.rp(x, y)
        self.alb.alpha_composite(im, (px, py)) if px >= 0 and py >= 0 else self._clip(self.alb, im, px, py)
        if occlude:
            blk = Image.new("RGBA", im.size, (0, 0, 0, 0))
            blk.putalpha(im.getchannel("A"))
            self._clip(self.emi, blk, px, py)
        if emissive is not None:
            self._clip(self.emi, emissive, px, py)

    @staticmethod
    def _clip(dst, src, x, y):
        sx, sy = max(0, -x), max(0, -y)
        if sx >= src.width or sy >= src.height:
            return
        dst.alpha_composite(src.crop((sx, sy, src.width, src.height)), (x + sx, y + sy))

    def light(self, x, y, color, radius, intensity):
        self.lights.append((x, y, color, radius, intensity))

    def lit(self, ambient=AMBIENT):
        s = 8
        lw, lh = self.W // s + 1, self.H // s + 1
        acc = [[list(ambient) for _ in range(lw)] for _ in range(lh)]
        for (x, y, col, rad, it) in self.lights:
            c = [v / 255 for v in hx(col)]
            cx, cy = (x - self.x0) * R / s, (y - self.y0) * R / s
            rr = rad * R / s
            for gy in range(max(0, int(cy - rr / 1.15) - 1), min(lh, int(cy + rr / 1.15) + 2)):
                for gx in range(max(0, int(cx - rr) - 1), min(lw, int(cx + rr) + 2)):
                    d2 = ((gx - cx) ** 2 + ((gy - cy) * 1.15) ** 2) / (rr * rr)
                    if d2 < 1:
                        f = (1 - d2) ** 2 * it
                        a = acc[gy][gx]
                        a[0] += c[0] * f; a[1] += c[1] * f; a[2] += c[2] * f
        lm = Image.new("RGB", (lw, lh))
        lp = lm.load()
        for gy in range(lh):
            for gx in range(lw):
                a = acc[gy][gx]
                lp[gx, gy] = tuple(min(255, int(v * 255 / 1.6)) for v in a)
        lm = lm.resize((lw * s, lh * s), Image.BILINEAR).crop((0, 0, self.W, self.H))
        base = ImageChops.multiply(self.alb.convert("RGB"), lm).point(lambda v: min(255, int(v * 1.6)))
        em = self.emi.convert("RGB")
        out = ImageChops.add(base, em)
        glow = em.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.85))
        return ImageChops.add(out, glow)


# ---------------------------------------------------------------------------
def load_tiles():
    sheet = Image.open(TILES + ".png").convert("RGBA")
    meta = json.load(open(TILES + ".json", encoding="utf-8"))
    cols = meta["columns"]
    emc = set(hx(c) for c in meta["emissiveColors"])

    def cell(i):
        return sheet.crop(((i % cols) * T, (i // cols) * T, (i % cols) * T + T, (i // cols) * T + T))

    def big(name):
        for b in meta["bigProps"]:
            if b["name"] == name:
                r = b["rect"]
                return sheet.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"])), b
        raise KeyError(name)
    return meta, cell, big, emc


def up(im, k=R):
    return im.resize((int(im.width * k), int(im.height * k)), Image.NEAREST)


def emissive_of(im, emc):
    """색 일치 픽셀 = 발광."""
    e = Image.new("RGBA", im.size, (0, 0, 0, 0))
    p, q = im.load(), e.load()
    for y in range(im.height):
        for x in range(im.width):
            c = p[x, y]
            if c[3] > 0 and c[:3] in emc:
                q[x, y] = c
    return e


def frame(path, row, col):
    j = json.load(open(path + ".json", encoding="utf-8"))
    im = Image.open(path + ".png").convert("RGBA")
    fw, fh = j["frameWidth"], j["frameHeight"]
    return im.crop((col * fw, row * fh, col * fw + fw, row * fh + fh)), j


def band_tiles(world, name, img, em):
    b = world.bj["bands"][name]
    W, H = b["width"], b["height"]
    if name == "north":
        y = -b["baselineY"]
        x = world.x0
        while x < world.x1:
            world.put(img, x, y, em, occlude=True)
            for L in b["lights"]:
                world.light(x + L["x"], y + L["y"], L["color"], L["radius"], L["intensity"])
            x += W
    elif name == "south":
        y = FH * T - b["baselineY"]
        x = world.x0
        while x < world.x1:
            world.put(img, x, y, em, occlude=True)
            for L in b["lights"]:
                world.light(x + L["x"], y + L["y"], L["color"], L["radius"], L["intensity"])
            x += W
    else:
        x = world.x0 if name == "west" else FW * T
        y = world.y0 - 120          # 위상을 조금 밀어 이음 위치를 바닥 가운데에서 피함(시스템 임의)
        while y < world.y1:
            world.put(img, x, y, em, occlude=True)
            for L in b["lights"]:
                ly = y + L["y"]
                if 0 <= ly <= FH * T:          # 북·남 띠에 가려진 자리의 광원은 등록하지 않음(lightsRule)
                    world.light(x + L["x"], ly, L["color"], L["radius"], L["intensity"])
            y += H


def build_world():
    bj = json.load(open(os.path.join(BORDER, "border.json"), encoding="utf-8"))
    world = World(bj)
    meta, cell, big, emc = load_tiles()
    cache = {}

    def tile(i):
        if i not in cache:
            c = cell(i)
            cache[i] = (up(c), up(emissive_of(c, emc)))
        return cache[i]

    # 1. 바닥 (판석 0~3 + 드문 방 바닥 섞기 + 바닥 데칼)
    for ty in range(FH):
        for tx in range(FW):
            i = [0, 1, 2, 3][h2(tx, ty, 4)]
            if h2(tx + 7, ty + 3, 100) < 2:
                i = [27, 28, 35, 36][h2(tx, ty, 4)]
            im, em = tile(i)
            world.put(im, tx * T, ty * T, em, occlude=False)
    for (i, tx, ty) in ((15, 12, 8), (15, 22, 15), (15, 31, 6), (20, 7, 11), (20, 16, 17), (20, 34, 19),
                        (60, 15, 21), (60, 16, 21), (61, 17, 21), (60, 18, 21), (62, 27, 3), (62, 5, 19)):
        im, em = tile(i)
        world.put(im, tx * T, ty * T, em, occlude=False)
    # 바닥 그늘(벽 발치) — 시스템 floorShadows
    for tx in range(FW):
        world.put(tile(53)[0], tx * T, 0, occlude=False)
    for ty in range(FH):
        world.put(tile(54)[0], 0, ty * T, occlude=False)
        world.put(tile(55)[0], (FW - 1) * T, ty * T, occlude=False)

    # 2. 테두리 배경 띠 (서·동 → 북)
    bands = {}
    for n in ("west", "east", "north", "south"):
        bands[n] = (Image.open(os.path.join(BORDER, f"{n}.png")).convert("RGBA"),
                    Image.open(os.path.join(BORDER, f"{n}_emissive.png")).convert("RGBA"))
    for n in ("west", "east", "north"):
        band_tiles(world, n, *bands[n])

    # 3. Y 정렬 (소품·큰 소품·캐릭터)
    items = []   # (바닥 y 논리, x 논리(pivot), 렌더 이미지, 렌더 pivot, emissive, shadow, light)

    def prop(i, tx, ty):
        p = next((q for q in meta["props"] if q["index"] == i), {})
        im, em = tile(i)
        piv = p.get("pivot", {"x": 16, "y": 30})
        L = p.get("light")
        items.append((ty * T + piv["y"], tx * T + piv["x"], im, (piv["x"] * R, piv["y"] * R), em, False,
                      (L, tx * T, ty * T) if L else None))

    def bigp(name, x, y):
        im0, b = big(name)
        piv = b["pivot"]
        L = b.get("light")
        items.append((y, x, up(im0), (piv["x"] * R, piv["y"] * R), up(emissive_of(im0, emc)), False,
                      (L, x - piv["x"], y - piv["y"]) if L else None))
    for (i, tx, ty) in ((13, 2, 0), (13, 3, 0), (14, 2, 1), (18, 6, 0), (13, 21, 0), (19, 23, 1), (14, 30, 0),
                        (13, 31, 0), (16, 11, 0), (16, 27, 0), (17, 19, 12), (13, 36, 9), (14, 37, 10), (18, 3, 15),
                        (13, 1, 22), (14, 2, 22), (19, 38, 21), (17, 9, 19)):
        prop(i, tx, ty)
    bigp("stall", 15 * T, 1 * T + 30)
    bigp("lamp_post", 8 * T + 16, 2 * T + 28)
    bigp("lamp_post", 33 * T + 16, 2 * T + 28)
    bigp("lamp_post", 6 * T + 16, 14 * T + 28)
    bigp("well", 26 * T, 12 * T + 30)
    bigp("crate_stack", 35 * T + 16, 15 * T + 30)
    bigp("crate_stack", 4 * T + 16, 20 * T + 30)

    # 캐릭터
    hero, hj = frame(os.path.join(SPR, "player/v3/player_katana_combo1"), 3, 3)
    hk = 1.5 if hj["frameWidth"] == 64 else 1.0       # 53라운드 Q1: 화면 48×72 (96×144 도트). 아직 64×96 이면 1.5배 근사
    hero_r = up(hero, hk)
    hp = (int(hj["pivot"]["x"] * hk), int(hj["pivot"]["y"] * hk))
    idle, ij = frame(os.path.join(SPR, "player/v3/player_idle"), 0, 0)
    idle_r = up(idle, hk)
    ip = (int(ij["pivot"]["x"] * hk), int(ij["pivot"]["y"] * hk))

    def ch(path, row, col):
        im, j = frame(os.path.join(SPR, path), row, col)
        r = up(im, R * j.get("pixelScale", 1))          # v2(pixelScale 1) = ×2, v3(0.5) = ×1
        return r, (int(j["pivot"]["x"] * r.width / im.width), int(j["pivot"]["y"] * r.height / im.height))

    def add_char(im_piv, x, y, light=None):
        im, piv = im_piv
        items.append((y, x, im, piv, up(emissive_of(im, emc), 1), True, light))
    # 북쪽 벽 근처 장면
    add_char((hero_r, hp), 20 * T, 2 * T + 20, ({"color": "#b0611a", "radius": 90, "intensity": 0.55}, 20 * T - 16, 2 * T - 40))
    add_char(ch("enemies/v2/charger_walk", 2, 2), 24 * T + 8, 3 * T + 8)
    add_char(ch("enemies/v2/charger_attack", 2, 1), 23 * T + 20, 1 * T + 24)
    add_char(ch("enemies/v2/charger_walk", 3, 5), 14 * T, 4 * T + 10)
    # 광장 가운데 장면
    add_char((idle_r, ip), 20 * T + 16, 12 * T - 10, ({"color": "#b0611a", "radius": 90, "intensity": 0.55}, 20 * T, 12 * T - 60))
    add_char(ch("enemies/v2/charger_walk", 2, 4), 24 * T, 10 * T)
    add_char(ch("enemies/v2/charger_attack", 3, 2), 16 * T, 14 * T)
    add_char(ch("enemies/v2/charger_death", 0, 5), 22 * T, 15 * T + 8)
    # 남서 모서리
    add_char(ch("enemies/v2/charger_walk", 0, 3), 5 * T, 22 * T + 20)
    add_char(ch("enemies/v2/charger_idle", 1, 0), 9 * T, 23 * T + 24)

    items.sort(key=lambda t: t[0])
    for (fy, fx, im, piv, em, shadow, L) in items:
        if shadow:
            sw = int(im.width * 0.55)
            sh = Image.new("RGBA", (sw, 16), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse((0, 0, sw - 1, 15), fill=(10, 12, 18, 120))
            world.put(sh, fx - sw / (2 * R), fy - 5, occlude=False)
        world.put(im, fx - piv[0] / R, fy - piv[1] / R, em, occlude=True)
        if L:
            l, ox, oy = L
            off = l.get("offset", {"x": 0, "y": 0})
            world.light(ox + off["x"], oy + off["y"], l["color"], l["radius"], l["intensity"])
    # 4. 전경 남쪽 띠
    band_tiles(world, "south", *bands["south"])
    return world


def vignette(view, strength=0.5):
    w, h = view.size
    m = Image.new("L", (w // 8, h // 8))
    p = m.load()
    cx, cy = m.width / 2, m.height / 2
    for y in range(m.height):
        for x in range(m.width):
            dv = (((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2) ** 0.5
            v = 1 - strength * max(0.0, dv - 0.55) / 0.85
            p[x, y] = int(255 * max(0.25, v))
    m = m.resize((w, h), Image.BILINEAR)
    return ImageChops.multiply(view, Image.merge("RGB", (m, m, m)))


def view(world, lit, cx, cy):
    """논리 카메라 중심 (cx, cy) → 1920×1080."""
    x = int(round((cx - VIEW[0] / 2 - world.x0) * R))
    y = int(round((cy - VIEW[1] / 2 - world.y0) * R))
    return vignette(lit.crop((x, y, x + VIEW[0] * R, y + VIEW[1] * R)))


def run():
    world = build_world()
    lit = world.lit()
    out = GEM
    shots = {
        # 북쪽 벽 근처: 주인공 y≈84 → 카메라 위 치우침 제안(-110) 적용
        "preview_border_outer_north.png": (20 * T, 2 * T + 20 - 110, "북쪽 벽 근처 (카메라 위로 110 치우침 제안)"),
        "preview_border_outer_north_nobias.png": (20 * T, 2 * T + 20, "북쪽 벽 근처 (카메라 = 주인공 중심)"),
        "preview_border_outer_center.png": (20 * T + 16, 12 * T - 30, "광장 중앙"),
        "preview_border_outer_sw.png": (-200 + 480, world.y1 - 270, "남서 모서리 (카메라 한계)"),
    }
    views = {}
    for fn, (cx, cy, txt) in shots.items():
        v = view(world, lit, cx, cy)
        views[fn] = v
        v.save(os.path.join(out, fn))
    # 전체 조감(논리 1배 = 렌더 1/2) + 카메라 사각형
    ov = lit.resize((world.W // 2, world.H // 2), Image.LANCZOS)
    d = ImageDraw.Draw(ov)
    for fn, (cx, cy, txt) in shots.items():
        if "nobias" in fn:
            continue
        x0 = (cx - VIEW[0] / 2 - world.x0)
        y0 = (cy - VIEW[1] / 2 - world.y0)
        d.rectangle((x0, y0, x0 + VIEW[0], y0 + VIEW[1]), outline=(232, 184, 88), width=3)
        label(ov, txt, (x0 + 8, y0 + 6))
    fx0, fy0 = -world.x0, -world.y0
    d.rectangle((fx0, fy0, fx0 + FW * T, fy0 + FH * T), outline=(120, 160, 200), width=2)
    label(ov, "바닥 40×24칸 (파랑 테)", (fx0 + 8, fy0 + FH * T - 36))
    ov.save(os.path.join(out, "preview_border_outer_overview.png"))
    lit_n = world.lit(AMBIENT_NEUTRAL)
    cx, cy, _ = shots["preview_border_outer_north.png"]
    vn = view(world, lit_n, cx, cy)
    vn.save(os.path.join(out, "preview_border_outer_north_neutral.png"))
    # 키아트와 나란히
    ka = Image.open(os.path.join(GEM, "keyart_outer/raw_a.jpg")).convert("RGB").resize((1920, 1072), Image.LANCZOS)
    ka = ka.crop((0, 0, 1920, 1080)) if ka.height >= 1080 else ka
    cmp_ = Image.new("RGB", (1920 * 2 + 24, 1080 * 2 + 24 + 60), (12, 12, 16))
    cmp_.paste(ka, (0, 60))
    cmp_.paste(views["preview_border_outer_north.png"], (1944, 60))
    cmp_.paste(vn, (0, 1080 + 84))
    cmp_.paste(views["preview_border_outer_sw.png"], (1944, 1080 + 84))
    small = cmp_.resize((cmp_.width // 2, cmp_.height // 2), Image.LANCZOS)
    label(small, "keyart_outer 원본 (Gemini, 49라운드)", (8, 4))
    label(small, "목업: 북쪽 벽 근처 — v2 주변광(청색)", (980, 4))
    label(small, "목업: 북쪽 벽 근처 — 중립 주변광 비교안", (8, 556))
    label(small, "목업: 남서 모서리 (서쪽 골목 계단 + 남쪽 지붕 전경)", (980, 556))
    small.save(os.path.join(out, "preview_border_outer_vs_keyart.png"))
    # 이전 v2 목업과 비교(같은 위치 근사)
    old = os.path.join(ROOT, "parts/art/work/v2_outer/preview_mock_lit.png")
    if os.path.exists(old):
        c2 = Image.new("RGB", (1920 * 2 + 24, 1080 + 60), (12, 12, 16))
        c2.paste(Image.open(old).convert("RGB").resize((1920, 1080), Image.NEAREST), (0, 60))
        c2.paste(views["preview_border_outer_north.png"], (1944, 60))
        c2 = c2.resize((c2.width // 2, c2.height // 2), Image.LANCZOS)
        label(c2, "이전: v2 타일 벽(앞면 2칸) 목업", (8, 2))
        label(c2, "53라운드: Gemini 테두리 + v2 바닥", (980, 2))
        c2.save(os.path.join(out, "preview_border_outer_vs_old.png"))
    print("mock saved", list(shots))


if __name__ == "__main__":
    run()
