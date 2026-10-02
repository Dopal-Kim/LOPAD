#!/usr/bin/env python3
"""LOPAD 1층 지역 타일셋 공통 키트 (49라운드 4-2·7, 계약 art-assets §7.3 · §2 인덱스 표 v3).

지역 = waste(황무지·전장) · gate(성문) · outer(외곽 거리) · brewery(양조 구역) · hall(지배자의 연회장).
산출 = assets/tiles/stage1_<region>.png/json — **인덱스 표 v3 그대로**(128x80, 8열x5행). JSON 은 tiles_floors/tilecommon2.Sheet2
       와 같은 키·값(이미지 이름·name·palette 문자열만 다름) → check_json.py 의 지역 검사 통과.

원칙 (v4 그대로 + 49라운드)
  * 판단 기준은 카메라 2배 화면(30x17타일). 넓은 평면 + 낮은 대비, 1px 흩뿌림 0, 디테일은 2px 이상 덩어리.
  * 4변형 균등(25%) 섞기 → 손상·얼룩은 방 종류당 변형 하나에 하나. 드물어야 하는 것은 소품(maxPerRoom).
  * **실내 느낌 금지**: 벽(5·21·22 정면, 6 윗면)은 지역의 '바깥 경계'(흙 둔덕·성벽·집 앞면·술통 더미·난간),
    void(7)는 투명 대신 **바깥 원경 색**(멀리 깔린 들판·해자·지붕들·술 수로·밤의 도시) — 방이 아니라 트인 곳에 서 있게.
  * void 는 한 장이 반복되므로(변형 없음) 가로 결(고랑·물결·기와 줄)만 쓴다 — 점 무늬는 16px 격자로 줄 선다.

색 문자 (팔레트 parts/art/palette/lopad.json): K,1..9 = G00..G09, T=G10 E=G11 C=G12 D=G13
  1층 램프(슬롯 16~27): i16 d17 e18 S19 f20 B21 g22 L23 h24 W25 X26 Y27
  지역 바닥의 '흙·나무·포도주' 같은 따뜻한 어둠은 램프 어두운 칸(16~18)으로 칠한다(48라운드 v4 의 남은 질문 3 을 지역 타일에서만 시험 — 임시).
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "tiles_v4"))
sys.path.insert(0, os.path.join(WORK, "tiles_floors"))
import pave  # noqa: E402
import tilecommon2 as tc2  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

G, T, ROOT = tc2.G, tc2.T, tc2.ROOT
A = tc2.ramp(1)
OUT_TILES = os.path.join(ROOT, "assets", "tiles")
SPR = os.path.join(ROOT, "assets", "sprites")
try:
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 14)
    FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 12)
except Exception:  # pragma: no cover
    FONT = FONT_S = tc2.FONT

C = {"K": G[0], "T": G[10], "E": G[11], "C": G[12], "D": G[13]}
for _i in range(1, 10):
    C[str(_i)] = G[_i]
for _ch, _k in zip("ideSfBgLhWXY", range(12)):
    C[_ch] = A[_k]
ACCENT_CH = "idSefBgLhWXY"
BRIGHT = set(A[3:])          # 슬롯 19~27 = '강조'(잔불·빛) — 비율 검사는 이것만 센다


class Ctx(tc2.Ctx):
    pass


ctx = Ctx(C)
new = ctx.new


def blit(s, rows, ox=0, oy=0, cmap=None):
    """문자 지도 찍기. '.'/' ' = 건너뜀. cmap 이 있으면 문자 → 색 문자 치환."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in ". ":
                continue
            if cmap:
                ch = cmap.get(ch, ch)
            x, y = ox + i, oy + j
            if 0 <= x < T and 0 <= y < T:
                s.px(x, y, C[ch])
    return s


def fill(ch):
    s = new()
    s.rect(0, 0, T - 1, T - 1, C[ch])
    return s


def blob(s, cx, cy, r, ch, seed, core=None, squash=1.0, lo=1, hi=T - 2):
    """매끈한 얼룩 (pave.Pave.blob 과 같은 규칙, 경계 lo..hi 안)."""
    rnd = random.Random(seed)
    radii = [r * (0.75 + 0.5 * rnd.random()) for _ in range(8)]

    def rad(a):
        k = a / (2 * math.pi) * 8
        i = int(k) % 8
        f = k - int(k)
        return radii[i] * (1 - f) + radii[(i + 1) % 8] * f

    for y in range(int(cy - r * 1.5) - 1, int(cy + r * 1.5) + 2):
        for x in range(int(cx - r * 1.5) - 1, int(cx + r * 1.5) + 2):
            dx, dy = x - cx, (y - cy) / squash
            d = math.hypot(dx, dy)
            a = math.atan2(dy, dx) % (2 * math.pi)
            if d <= rad(a) and lo <= x <= hi and lo <= y <= hi:
                f = d / max(0.01, rad(a))
                s.px(x, y, C[core] if (core and f < 0.45) else C[ch])
    return s


def pebble(s, x, y, top="5", body="4", shade="1"):
    """자갈 2x2 + 그늘: 빛 좌상단."""
    s.px(x, y, C[top]); s.px(x + 1, y, C[body]); s.px(x, y + 1, C[body])
    s.px(x + 1, y + 1, C[shade]) if shade else None
    return s


def line(s, pts, ch):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        s.line(x0, y0, x1, y1, C[ch])
    return s


def outline_in(s, ch="K"):
    s.outline(C[ch], where="inside")
    return s


# ====================================================================== 시트 (JSON = Sheet2 그대로, 파일 이름만 지역)
class RegionSheet(tc2.Sheet2):
    def __init__(self, region, name_kr, tiles, props, here):
        super().__init__(1, name_kr, tiles, props, [], here, 1)
        self.region = region
        self.image_name = "stage1_%s.png" % region

    def used_slots(self):
        used = set()
        for _, s in self.tiles:
            for (r, g, b), _n in s.used_colors().items():
                used.add("#%02x%02x%02x" % (r, g, b))
        gray = sorted(G.index(c) for c in used if c in G)
        acc = sorted(16 + A.index(c) for c in used if c in A)
        other = sorted(c for c in used if c not in G and c not in A)
        return gray, acc, other

    def build_sheet(self):
        IDX = self.idx
        sheet = Image.new("RGBA", (tc2.COLS * T, tc2.ROWS * T), (0, 0, 0, 0))
        for i, (name, s) in enumerate(self.tiles):
            r, c = divmod(i, tc2.COLS)
            sheet.alpha_composite(s.composite(1), (c * T, r * T))
        sheet.save(os.path.join(OUT_TILES, self.image_name))
        gray, acc, other = self.used_slots()
        assert not other, (self.region, other)
        meta = {
            "image": self.image_name,
            "stage": 1,
            "name": self.name_kr,
            "tileWidth": T, "tileHeight": T,
            "columns": tc2.COLS, "rows": tc2.ROWS,
            "indexFormula": "row * columns + column",
            "tiles": {
                "0": [IDX["void"]],
                "1": [IDX["floor_0"], IDX["floor_1"], IDX["floor_2"], IDX["floor_3"]],
                "2": [IDX["wall"], IDX["wall_v1"], IDX["wall_v2"]],
                "3": [IDX["door_open"]],
                "4": [IDX["door_closed"]],
                "5": [IDX["door_locked"]],
                "6": [IDX["corridor"]],
                "7": [IDX["exit"]],
                "8": [IDX["shop"]],
            },
            "tileIdNames": {"0": "void", "1": "floor", "2": "wall", "3": "door_open", "4": "door_closed",
                            "5": "door_locked", "6": "corridor", "7": "exit", "8": "shop"},
            "roomFloors": {k: [IDX["%s_%d" % (k, i)] for i in range(tc2.ROOM_VARIANTS)] for k in tc2.ROOM_KINDS},
            "roomFloorsNote": "방 종류별 바닥 4변형 (40라운드 v3). 키가 없거나 비면 tiles['1']. 복도 근처·기타 방은 tiles['1']. 좌표 해시로 4개를 균등하게 섞는다.",
            "walls": {
                "top": IDX["wall"], "bottom": IDX["wall_top"], "left": IDX["wall_top"], "right": IDX["wall_top"],
                "corner_tl": IDX["wall_top"], "corner_tr": IDX["wall_top"], "corner_bl": IDX["wall_top"], "corner_br": IDX["wall_top"],
                "variants": [IDX["wall"], IDX["wall_v1"], IDX["wall_v2"]],
                "note": "top = 위쪽(북) 경계: 정면이 보인다 (tiles['2'] 의 세 인덱스를 좌표 해시로 섞는다). 나머지 변·모서리는 윗면. "
                        "49라운드 지역 타일: 벽은 방의 벽이 아니라 그 지역의 바깥 경계(둔덕·성벽·집 앞면·술통 더미·난간), void(7)는 투명이 아니라 원경 색(불투명)."
            },
            "props": [
                {"index": IDX[pn], "name": short, "solid": bool(solid), "maxPerRoom": int(mpr), "weight": float(w)}
                for pn, (short, solid, mpr, w) in zip(self.prop_names, self.props)
            ],
            "propsNote": "40라운드: maxPerRoom = 방당 최대 개수, weight = 배치 가중치(기본 1). 시스템 tileskin 이 지원하면 쓰고, 없으면 기존 규칙.",
            "propsLayer": "overlay — 소품 타일은 배경이 투명하므로 바닥 레이어 위에 겹쳐 그린다",
            "names": {str(i): name for i, (name, _) in enumerate(self.tiles)},
            "palette": "parts/art/palette/lopad.json (gray G%s + floor 1 accent slots %s) — 49라운드 지역 '%s', 기본 stage1 폴백" % (
                ",".join("%02d" % g for g in gray), ",".join(str(a) for a in acc), self.region),
        }
        with open(os.path.join(OUT_TILES, "stage1_%s.json" % self.region), "w", encoding="utf-8") as fp:
            json.dump(meta, fp, ensure_ascii=False, indent=1)
        self.meta = meta
        return sheet, meta

    def report(self):
        gray, acc, other = self.used_slots()
        print("[%s] gray %d %s | accent %d %s" % (self.region, len(gray), gray, len(acc), acc))
        for name, s in self.tiles:
            info = s.stats(print_=False)
            if info["semi_alpha_px"]:
                print("  SEMI ALPHA %s %d" % (name, info["semi_alpha_px"]))


# ====================================================================== 2배 목업 (지역 화면)
def load_sprite(rel, name, col=0, row=0):
    base = os.path.join(SPR, rel, name)
    m = json.load(open(base + ".json", encoding="utf-8"))
    im = Image.open(base + ".png").convert("RGBA")
    fw, fh = m["frameWidth"], m["frameHeight"]
    return im.crop((col * fw, row * fh, col * fw + fw, row * fh + fh)), m


def state_sprite(rel, name, state="idle", k=0):
    im0, m = load_sprite(rel, name)
    st = (m.get("states") or {}).get(state) or (m.get("states") or {}).get("idle") or [0]
    f = st[min(k, len(st) - 1)]
    im, m = load_sprite(rel, name, col=f)
    return im, m


class Arena:
    """한 화면(30x17타일). 바깥은 void, 경계 1칸(북 = 정면 변형 섞음, 나머지·모서리 = 윗면), 안은 방 바닥 4변형 섞기.
    시스템의 좌표 해시 식은 모름 → 결정적 의사난수."""

    def __init__(self, sheet, kind, box, seed=1, vw=30, vh=18, floor_overrides=None):
        self.sh, self.vw, self.vh = sheet, vw, vh
        rnd = random.Random(seed)
        x0, y0, x1, y1 = box          # 안쪽 바닥 타일 범위 (포함)
        self.box = box
        g = [["void"] * vw for _ in range(vh)]
        for y in range(vh):
            for x in range(vw):
                inside = x0 <= x <= x1 and y0 <= y <= y1
                ring = (x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 1) and not inside
                if inside:
                    g[y][x] = (kind + "_%d" % rnd.randrange(4)) if kind != "floor" else "floor_%d" % rnd.randrange(4)
                elif ring:
                    if y == y0 - 1 and x0 <= x <= x1:
                        g[y][x] = rnd.choice(["wall", "wall", "wall", "wall_v1", "wall_v2"])
                    else:
                        g[y][x] = "wall_top"
        self.g = g
        self.props = {}
        self.floor_sprites = []
        self.sprites = []

    def tile(self, tx, ty, name):
        self.g[ty][tx] = name

    def prop(self, tx, ty, name):
        self.props[(tx, ty)] = name

    def put(self, img, pivot, fx, fy, floor=False):
        """fx, fy = 월드 px (피벗이 놓일 곳)."""
        item = (fy, fx - pivot[0], fy - pivot[1], img)
        (self.floor_sprites if floor else self.sprites).append(item)

    def put_struct(self, name, tx, ty, state="idle", k=0, rel="structures", dx=0, dy=0):
        """구조물: footprint 아래 변 가운데 = 피벗. (tx, ty) = footprint 왼쪽 아래 타일."""
        im, m = state_sprite(rel, name, state, k)
        fw = (m.get("footprint") or [1, 1])[0]
        fx = tx * T + fw * T // 2 + dx
        fy = (ty + 1) * T + dy
        self.put(im, (m["pivot"]["x"], m["pivot"]["y"]), fx, fy, floor=(m.get("depth") == "floor"))

    def put_char(self, rel, name, row, col, fx, fy):
        im, m = load_sprite(rel, name, col=col, row=row)
        self.put(im, (m["pivot"]["x"], m["pivot"]["y"]), fx, fy)

    def render(self):
        W, H = self.vw * T, self.vh * T
        img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        for y in range(self.vh):
            for x in range(self.vw):
                img.alpha_composite(self.sh.tile_img(self.g[y][x]), (x * T, y * T))
        for (x, y), nm in self.props.items():
            img.alpha_composite(self.sh.tile_img(nm), (x * T, y * T))
        for _, x, y, im in sorted(self.floor_sprites, key=lambda o: o[0]):
            img.alpha_composite(im, (x, y))
        for _, x, y, im in sorted(self.sprites, key=lambda o: o[0]):
            img.alpha_composite(im, (x, y))
        return img.crop((0, 0, W, 270))


def label(img, text, xy=(6, 4), font=None):
    d = ImageDraw.Draw(img)
    x, y = xy
    f = font or FONT
    for dx, dy in ((1, 1), (-1, 0), (1, 0), (0, -1), (0, 1), (2, 2)):
        d.text((x + dx, y + dy), text, fill=(0, 0, 0), font=f)
    d.text((x, y), text, fill=(240, 236, 228), font=f)


def bright_ratio(img):
    n = sum(1 for p in img.getdata() if p[3] and "#%02x%02x%02x" % p[:3] in BRIGHT)
    return n / (img.width * img.height)


def x2(img):
    return img.resize((img.width * 2, img.height * 2), Image.NEAREST)


def relief(s, bumps, base, lit, shade, t=0.18, deep=None, t_deep=0.55):
    """이음새 없는(토러스) 울퉁불퉁한 면: bumps = [(cx, cy, r, h)] 높이장을 16px 로 감아 더하고, 빛(좌상단) 방향 기울기로
    lit / base / shade 를 고른다. 가장자리에서 끊기지 않아 윗면·원경 반복에서도 타일 테두리가 안 보인다.
    deep 이 있으면 높이가 아주 낮은 골(t_deep 아래)을 deep 으로."""
    def h(x, y):
        v = 0.0
        for cx, cy, r, hh in bumps:
            for ox in (-T, 0, T):
                for oy in (-T, 0, T):
                    d2 = ((x - cx - ox) ** 2 + (y - cy - oy) ** 2) / (r * r)
                    if d2 < 1:
                        v += hh * (1 - d2) ** 2
        return v
    H = [[h(x, y) for x in range(T)] for y in range(T)]
    hmax = max(max(r) for r in H) or 1
    for y in range(T):
        for x in range(T):
            g = (H[y][x] - H[(y + 1) % T][(x + 1) % T]) / hmax
            if deep and H[y][x] / hmax < t_deep * 0.2:
                c = deep
            elif g > t:
                c = lit
            elif g < -t:
                c = shade
            else:
                c = base
            s.px(x, y, C[c])
    return s
