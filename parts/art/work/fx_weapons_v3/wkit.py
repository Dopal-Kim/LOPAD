"""fx_weapons_v3 그리기 도구 — 무기별 기본 공격·특수·갈래 이펙트 v3 (53라운드 Q5 · Q26~Q32 · Q42~Q43).

좌표: v3 도트(pixelScale 0.5). 이펙트는 '오른쪽 보기' 로컬 좌표(원점 = 판정 원점, x = 정면, y = 아래)로 정의하고
방향 변환 T(d) 로 최종 프레임에 옮긴다(계약 arcAngleNote: down = +90°, up = -90°, left = 좌우 반전).
떨어지는 재·불티(중력)는 변환 뒤 화면 좌표에서 더한다 → 어느 방향이든 아래로 떨어짐.
획 래스터는 fx_v3/fxkit(캡슐 사슬, 레이어 안 최댓값 → 램프 양자화)을 그대로 쓴다. 반투명 0.
"""
import json
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(HERE, "../fx_v3"))
import fxkit as FK                                    # noqa: E402

OLD_FX = os.path.join(ROOT, "assets/sprites/fx")
OUT_FX = os.path.join(ROOT, "assets/sprites/fx/v3")
HERO_P = os.path.join(ROOT, "assets/sprites/player/v3")
DIRS = ["down", "up", "left", "right"]
K4 = 4                                                # 구 fx(pixelScale 2) → v3(0.5): 도트 ×4 = 같은 화면 크기
HIT_UP = 10 * K4                                      # 판정 원점 = 피벗(발)에서 위로 구 10px → 40 도트

# ---------------------------------------------------------------- 팔레트 (주인공 v3 30색 안 + 백열 코어 X0/X1)
X0, X1 = "#ffffff", "#fff4dc"
A17, A18, A19, A21, A23, A25, A26 = "#3f271d", "#653b24", "#8b4d22", "#d67a11", "#e2a33c", "#eecc78", "#f4de9b"
B0, B1, B2, B3 = "#2a1e17", "#3b2a1f", "#4f3828", "#664a33"          # 갈색 재(흙)
S0, S1, S2, S3 = "#45403b", "#5c554e", "#756c62", "#90857a"          # 회색 재
G3, G4, G5, G6, G7, G8 = "#3e3f42", "#4d4f52", "#5c5e62", "#6c6f73", "#7d8084", "#8e9195"   # 쇠(갑옷·녹슨 날 회색)
HERO_PAL = {"#141516", "#14161c", "#1d2028", "#212224", "#272b35", "#2a1e17", "#2f3033", "#3b2a1f", "#3e3f42", "#3f271d",
            "#3f4552", "#45403b", "#4d4f52", "#4e5563", "#4f3828", "#5c554e", "#5c5e62", "#626a78", "#653b24", "#664a33",
            "#6c6f73", "#756c62", "#7d8084", "#8b4d22", "#8e9195", "#90857a", "#d67a11", "#e2a33c", "#eecc78", "#f4de9b"}
ALLOWED = HERO_PAL | {X0, X1}
COLOR_MAX = 14

# 램프(어둠 → 밝음)
R_EDGE = [A18, A19, A21, A23, A25, A26, X1, X0]       # 혼불 날선·궤적 (판정 = 위쪽 끝까지)
R_EDGE_SOFT = [A18, A19, A21, A23]                     # 식은 궤적
R_EMBER = [A18, A19, A21, A23, A25, A26]               # 불티
R_ASHG = [S0, S1, S2, S3]                              # 회색 재 장막·조각
R_ASHB = [B0, B1, B2, B3]                              # 갈색 재·흙먼지
R_DUST = [B1, B2, B3, S1, S2]                          # 흙먼지 구름(윗면 밝게)
R_RUST = [B2, B3, A18, A19, A21]                       # 녹 슨 띠(흙·녹 → 날선 쪽 녹빛·혼불)
R_HOT = [A19, A21, A23, A25, A26, X1, X0]              # 섬광·광선


def hexrgb(h):
    return FK.hexrgb(h)


def h2(x, y, s=0):
    """결정적 해시 잡음 0..1."""
    n = (int(x) * 374761393 + int(y) * 668265263 + s * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


# ---------------------------------------------------------------- 방향 변환
MAT = {"right": (1, 0, 0, 1), "down": (0, -1, 1, 0), "up": (0, 1, -1, 0), "left": (-1, 0, 0, 1), "any": (1, 0, 0, 1)}


class T:
    """로컬(오른쪽 보기, 원점 기준) ↔ 최종 프레임 좌표."""

    def __init__(self, d, ox, oy):
        self.d, self.ox, self.oy = d, ox, oy
        self.m = MAT[d]

    def __call__(self, p):
        a, b, c, dd = self.m
        return (self.ox + a * p[0] + b * p[1], self.oy + c * p[0] + dd * p[1])

    def inv(self, x, y):
        a, b, c, dd = self.m
        u, v = x - self.ox, y - self.oy
        det = a * dd - b * c
        return ((dd * u - b * v) / det, (-c * u + a * v) / det)

    def ang(self, a):
        """로컬 각(rad) → 화면 각."""
        x, y = math.cos(a), math.sin(a)
        p0 = self((0, 0))
        p1 = self((x, y))
        return math.atan2(p1[1] - p0[1], p1[0] - p0[0])

    def pts(self, pts):
        return [self(p) for p in pts]


# ---------------------------------------------------------------- 프레임 캔버스
class Frame(FK.Canvas):
    def __init__(self, w, h, t):
        super().__init__(w, h)
        self.t = t

    def L(self, ramp, gamma=1.0, vmin=0.04):
        return self.layer(ramp, gamma, vmin)


def tstroke(L, t, pts, w, **kw):
    L.stroke(t.pts(pts), w, **kw)


def arc_pts(r, a0, a1, cx=0.0, cy=0.0, ry=None, n=None):
    ry = r if ry is None else ry
    n = n or max(8, int(abs(a1 - a0) * r / 0.5))
    return [(cx + math.cos(a0 + (a1 - a0) * i / n) * r, cy + math.sin(a0 + (a1 - a0) * i / n) * ry) for i in range(n + 1)]


def crescent(W, H, t, R, a0, a1, wmax, prof, cb, tmin=0.0, tmax=1.0, ry=1.0, inner_pad=0.0):
    """초승달 띠 훑기: 바깥 가장자리 = 반지름 R(판정 가장자리), 안쪽으로 폭 w(s)=wmax·prof(s).
    s = 휘두름 진행(0 = 시작 a0, 1 = 끝 a1 = 칼이 지나간 마지막 자리), d = 깊이(0 바깥 → 1 안쪽, inner_pad 만큼 더 안쪽까지).
    cb(x, y, s, d, w) 를 픽셀마다 부른다. ry < 1 = 세로로 눌린 타원(바닥 고리)."""
    span = a1 - a0
    xs, ys = [], []
    reach = wmax * (1 + inner_pad) + 1
    for k in range(0, 49):
        a = a0 + span * k / 48
        for q in (R + 1.5, max(0.0, R - reach)):
            p = t((math.cos(a) * q, math.sin(a) * q * ry))
            xs.append(p[0])
            ys.append(p[1])
    x0, x1 = int(min(xs)) - 2, int(max(xs)) + 3
    y0, y1 = int(min(ys)) - 2, int(max(ys)) + 3
    tw = 2 * math.pi
    for y in range(max(0, y0), min(H, y1)):
        for x in range(max(0, x0), min(W, x1)):
            lx, ly = t.inv(x + 0.5, y + 0.5)
            ly /= ry
            r = math.hypot(lx, ly)
            if r > R + 0.6 or r < R - reach:
                continue
            a = math.atan2(ly, lx)
            s = (a - a0) / span
            if not 0 <= s <= 1:
                s2 = (a + tw - a0) / span
                s3 = (a - tw - a0) / span
                s = s2 if 0 <= s2 <= 1 else s3
            if not tmin <= s <= tmax:
                continue
            w = wmax * prof(s)
            if w <= 0.3:
                continue
            d = (R - r) / w
            if -0.08 <= d <= 1.0 + inner_pad:
                cb(x, y, s, max(0.0, d), w)


def needle(L, t, p0, p1, w, v=1.0, peak=0.5, p=0.7, vprof=None):
    """양끝이 바늘처럼 모이는 획."""
    L.stroke(t.pts([p0, p1]), w, prof=FK.tp_both(p, peak), v=v, vprof=vprof)


def jag(rng, p0, p1, n=6, amp=2.0):
    """번개·균열처럼 꺾인 선(로컬)."""
    out = [p0]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    for i in range(1, n):
        f = i / n
        o = rng.uniform(-amp, amp)
        out.append((p0[0] + dx * f + nx * o, p0[1] + dy * f + ny * o))
    out.append(p1)
    return out


def flake(L, cx, cy, size, rot, v=1.0, lit=0.35):
    """재 조각(삼각 비늘) — 화면 좌표. 윗변이 밝음."""
    pts = [(cx + math.cos(rot + k * 2.2 + (0.3 if k == 1 else 0)) * size * (1.0 if k != 2 else 0.6),
            cy + math.sin(rot + k * 2.2 + (0.3 if k == 1 else 0)) * size * (1.0 if k != 2 else 0.6)) for k in range(3)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            px, py = x + 0.5, y + 0.5
            ok = True
            sgn = None
            for i in range(3):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % 3]
                c = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
                if sgn is None:
                    sgn = c >= 0
                elif (c >= 0) != sgn:
                    ok = False
                    break
            if ok:
                L.put(x, y, v * FK.clamp(0.75 - lit * (py - cy) / max(1.0, size), 0.2, 1.0))
    if size < 1.2:
        L.put(cx, cy, v * 0.7)


def ember(L, x, y, vx, vy, length, w=0.9, v=1.0):
    """불티: 진행 방향 반대쪽으로 꼬리가 가늘어지는 짧은 획(화면 좌표)."""
    n = math.hypot(vx, vy) or 1
    tx, ty = x - vx / n * length, y - vy / n * length
    if length < 1.0:
        L.stamp(x, y, w, v, soft=0)
        return
    L.stroke([(tx, ty), (x, y)], w, prof=FK.tp_head(0.8), v=v)


def puff(L, x, y, r, v=1.0, flat=0.75, seed=0):
    L.cloud(x, y, r, v=v, flat=flat, seed=seed)


# ---------------------------------------------------------------- 파편 시스템(결정적)
class Debris:
    """로컬에서 생성 → 화면에서 날림(중력 g). kind: flake(재 조각) / ember(불티) / dust(먼지 구름)."""

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.items = []

    def spawn(self, kind, p, vel, born, life, size=1.0, v=1.0, g=0.0):
        self.items.append(dict(kind=kind, p=p, vel=vel, born=born, life=life, size=size, v=v, g=g))

    def draw(self, f, t, layers, frame_i):
        for it in self.items:
            age = frame_i - it["born"]
            if age < 0 or age > it["life"]:
                continue
            k = age / max(1e-6, it["life"])
            p0 = t(it["p"])
            vx, vy = t(it["vel"])
            o = t((0, 0))
            vx, vy = vx - o[0], vy - o[1]
            x = p0[0] + vx * age
            y = p0[1] + vy * age + 0.5 * it["g"] * age * age
            vy2 = vy + it["g"] * age
            m = 5 + (it["size"] * 1.6 if it["kind"] == "dust" else 0)
            if x < m or y < m or x > f.w - 1 - m or y > f.h - 1 - m:
                continue                                # 틀 가장자리 근처는 그리지 않음(잘림 방지)
            kind = it["kind"]
            if kind == "ember" and "ember" in layers:
                ember(layers["ember"], x, y, vx, vy2, max(0.0, it["size"] * (1.4 - k)), w=0.75, v=it["v"] * (1 - 0.55 * k))
            elif kind == "flake" and "flake" in layers:
                flake(layers["flake"], x, y, it["size"] * (1 - 0.35 * k), it["v"] + age * 0.9, v=it["v"] * (1 - 0.3 * k))
            elif kind == "dust" and "dust" in layers:
                puff(layers["dust"], x, y, it["size"] * (0.7 + 0.5 * k), v=it["v"] * (1 - 0.4 * k), seed=int(it["v"] * 100) + age)


# ---------------------------------------------------------------- 시트·JSON·검사
def old_json(name):
    return json.load(open(os.path.join(OLD_FX, name + ".json"), encoding="utf-8"))


def colors_of(im):
    return {"#%02x%02x%02x" % px[:3] for px in im.getdata() if px[3]}


def has_partial(im):
    return any(0 < px[3] < 255 for px in im.getdata())


def edge_touch(im):
    w, h = im.size
    px = im.load()
    n = 0
    for x in range(w):
        n += (px[x, 0][3] > 0) + (px[x, h - 1][3] > 0)
    for y in range(h):
        n += (px[0, y][3] > 0) + (px[w - 1, y][3] > 0)
    return n


def scale_lengths(j):
    """도트 단위 길이 필드 ×4 (계약 §13 fx v3 규약). shake.px·scale·ratio 는 그대로."""
    j = json.loads(json.dumps(j))
    if "pivot" in j:
        j["pivot"] = {"x": j["pivot"]["x"] * K4, "y": j["pivot"]["y"] * K4}
    for k in ("hitRadiusPx", "drawnRadiusPx", "visualLengthPx"):
        if k in j and isinstance(j[k], (int, float)):
            j[k] = j[k] * K4
    if isinstance(j.get("thrust"), dict):
        for k in ("lengthPx", "widthPx", "fromPx"):
            if k in j["thrust"]:
                j["thrust"][k] = j["thrust"][k] * K4
    return j


PALETTE_NOTE = ("v3 무기 이펙트(53라운드 Q5): 주인공 v3 30색 팔레트 안의 재(#2a1e17~#90857a)·혼불 호박(#3f271d~#f4de9b) + 백열 코어 "
                "X0 #ffffff / X1 #fff4dc. 호박은 주인공 고정색 — 층 램프 스왑 대상 아님(paletteSwap: none). 구 무기 보조색 W0~W3 은 쓰지 않는다.")


def write_sheet(name, frames, old, extra=None, size=None, pivot=None, legacy_note=None, swap="none", edge_ok=False):
    """frames: {dir: [RGBA]} (directions 순서는 구 JSON). 구 JSON 을 복사해 v3 필드로 바꿔 쓴다."""
    dirs = old["directions"]
    F = len(frames[dirs[0]])
    assert F == old["frames"], (name, F, old["frames"])
    fw, fh = frames[dirs[0]][0].size
    sheet = Image.new("RGBA", (fw * F, fh * len(dirs)), (0, 0, 0, 0))
    for r, d in enumerate(dirs):
        assert len(frames[d]) == F
        for c, im in enumerate(frames[d]):
            assert im.size == (fw, fh)
            sheet.alpha_composite(im, (c * fw, r * fh))
    cols = colors_of(sheet)
    bad = cols - ALLOWED
    assert not bad, (name, sorted(bad))
    assert len(cols) <= COLOR_MAX, (name, len(cols), sorted(cols))
    assert not has_partial(sheet), name
    edges = sum(edge_touch(im) for d in dirs for im in frames[d])
    assert edge_ok or edges == 0, (name, "edge", edges)
    j = scale_lengths(old)
    legacy = {"image": "../%s.png" % old.get("image", name + ".png").split("/")[-1], "frameWidth": old["frameWidth"],
              "frameHeight": old["frameHeight"], "pivot": old.get("pivot"), "pixelScale": 2}
    for k in ("hitRadiusPx", "thrust", "drawnRadiusPx", "visualLengthPx", "note", "palette", "secondary", "trail"):
        if k in old:
            legacy[k] = old[k]
    j.update(image=name + ".png", action=old.get("action", name), version="v3", frameWidth=fw, frameHeight=fh, pixelScale=0.5,
             palette=PALETTE_NOTE, paletteSwap=swap,
             paletteSwapNote="53라운드 Q62 — fx 는 지역 바닥 팔레트 교체에서 제외(시스템은 이 시트에 색 교체를 하지 않는다).", source="parts/art/work/fx_weapons_v3/build.py", colors=len(cols),
             unitNote="모든 길이 필드(pivot·hitRadiusPx·thrust·drawnRadiusPx·visualLengthPx)는 이 시트 도트 단위. 논리 px = 도트 × "
                      "pixelScale(0.5). 화면 크기는 구 시트(pixelScale 2)와 같다(도트 ×4). shake.px·scale·비율 필드는 그대로.",
             timingNote="프레임 수·frameDurationsMs·loop·anchor·spawn·impact/hit/active/cancel 프레임·timingMs·arc 각도는 구 시트와 동일(판정 불변).")
    j.pop("secondary", None)
    if "hitOrigin" in j:
        j["hitOrigin"] = "몸 중심 = 피벗(발)에서 위로 40 도트(구 10px ×4)"
    if pivot is not None:
        j["pivot"] = {"x": pivot[0], "y": pivot[1]}
    for k in ("note", "revision", "design"):
        if k in j:
            legacy.setdefault(k, j.pop(k))
    import common
    j = common.remap(j, old.get("weapon"))
    if extra:
        extra = dict(extra)
        for k in extra.pop("_drop", ()):           # 2단 시트: 1단 구 JSON 에서 물려받지 않을 키
            j.pop(k, None)
        j.update(extra)
    j["note"] = "v3 (53라운드 Q5): " + (j.get("tierDesign") or j.get("branchDesignV3") or j.get("design") or "무기 이펙트 v3")
    j["legacy"] = legacy
    if legacy_note:
        j["legacy"]["v3Note"] = legacy_note
    os.makedirs(OUT_FX, exist_ok=True)
    sheet.save(os.path.join(OUT_FX, name + ".png"), optimize=True)
    with open(os.path.join(OUT_FX, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
    return sheet, j


def geom(old, size_mul=K4):
    """구 JSON → (프레임 w, h, 피벗 x, y, 판정 원점 x, y)."""
    fw, fh = old["frameWidth"] * size_mul, old["frameHeight"] * size_mul
    px, py = old["pivot"]["x"] * K4, old["pivot"]["y"] * K4
    return fw, fh, px, py


def hero_silhouette(sheet, row, col):
    """주인공 v3 몸 시트의 한 프레임(96×144) → 알파 마스크 set((x, y)) 와 크기."""
    j = json.load(open(os.path.join(HERO_P, sheet + ".json"), encoding="utf-8"))
    im = Image.open(os.path.join(HERO_P, sheet + ".png")).convert("RGBA")
    fw, fh = j["frameWidth"], j["frameHeight"]
    c = im.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))
    px = c.load()
    return {(x, y) for y in range(fh) for x in range(fw) if px[x, y][3]}, (fw, fh), (j["pivot"]["x"], j["pivot"]["y"])


def limit_colors(frames, cap, name=""):
    """55라운드 2단 시트 안전장치: 시트 전체 색이 cap 을 넘으면 가장 적게 쓰인 색부터 남은 색 중 가장 가까운 색(RGB)으로 합친다.
    백열 X0/X1 로는 합치지 않는다(빛 규칙). 합친 내역은 stdout note."""
    from collections import Counter
    cnt = Counter()
    for lst in frames.values():
        for im in lst:
            for px in im.getdata():
                if px[3]:
                    cnt[px[:3]] += 1
    if len(cnt) <= cap:
        return frames
    hot = {hexrgb(X0), hexrgb(X1)}
    keep = [c for c, _ in cnt.most_common()]
    m = {}
    while len(keep) > cap:
        c = keep.pop()
        cand = [k for k in keep if k not in hot] or keep
        m[c] = min(cand, key=lambda k: sum((a - b) ** 2 for a, b in zip(k, c)))
    for c in list(m):                                  # 사슬 정리
        while m[c] in m:
            m[c] = m[m[c]]
    print("  note limit_colors %s: %d → %d, 합침 %s" % (name, len(cnt), cap,
          ", ".join("#%02x%02x%02x→#%02x%02x%02x" % (c + m[c]) for c in m)))
    for lst in frames.values():
        for im in lst:
            px = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    p = px[x, y]
                    if p[3] and p[:3] in m:
                        px[x, y] = m[p[:3]] + (255,)
    return frames
