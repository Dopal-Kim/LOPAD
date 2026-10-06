"""61 단계 5 (P13) 단검 재디자인 공용 — '재 발톱(灰爪)' 디자인 언어 · 팔레트 · 그리기 도구 · 시트 쓰기·게시.

디자인 언어(무기와 이펙트가 같은 모양에서 나온다):
  - 무기: 손에 감기는 짧은 곡선 날(발톱 날, 역수) — 볼록한 등은 재빛 강철, 오목한 안쪽 날선에 호박 불씨 한 줄, 끝이 앞으로 휜다.
          손잡이 끝 고리(손가락 고리)가 실루엣 표지. 판정 순간에만 날선·끝이 백열.
  - 이펙트: 같은 '발톱 곡선'을 가늘게 늘인 바늘 획(뭉툭한 원뿔 없음) + 짧고 많은 잔상 획 + 끝의 X 섬광.
            그림자 걸음·낙인은 검은 잉크(재 갈색·먹 #141516)가 번지는 얼룩, 낙인 = 적 몸에 새긴 발톱 자국.
좌표: 도트(pixelScale 0.5). 반투명 0. 색은 기존 팔레트만(새 색 없음).
기존 도구는 읽기만: atlas57(gridsheet·build.convert_sheet/apply_in_place·verify), boss61/k61(Cv), awaken60/kit60(층 램프).
"""
import json
import math
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets", "sprites")
STAGE = os.path.join(HERE, "out", "grid")
TMP = os.path.join(HERE, "out", "_atlas_tmp_dagger61s5")
BEFORE_REV = "fb037b8"          # 고치기 전(61 단계 5 배분 커밋) — 전/후 비교·치수 대조 기준
BEFORE = os.path.join(HERE, "out", "before")
for p in ("atlas57", "boss61", "awaken60"):
    sys.path.insert(0, os.path.join(WORK, p))

import gridsheet  # noqa: E402
import kit60 as K6  # noqa: E402

VERSION = "v3-r61s5"
SRC = "parts/art/work/dagger61s5/build.py (61 단계 5 P13 — 단검 무기+이펙트 재디자인 '재 발톱')"
R61S5 = "61 단계 5 P13 §2 — 단검 재디자인(무기+이펙트 한 디자인 언어). 계약 art §27"


def hx(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


# ---------------------------------------------------------------- 팔레트 (모두 기존 lopad.json 색)
G = [hx(c) for c in K6.G]                       # 무채 G0..G15
AR = [hx(c) for c in K6.A]                      # 1층 호박 램프
GRN = [hx(c) for c in K6.GRN]
TEAL = [hx(c) for c in K6.TEAL]
VIO = [hx(c) for c in K6.VIO]
SIL = [hx(c) for c in K6.SIL]
CRI = [hx(c) for c in K6.CRI]
PL = [hx(c) for c in K6.PL]
X0, X1 = hx("#ffffff"), hx("#fff4dc")
A17, A18, A19, A21, A23, A25, A26 = [hx(c) for c in ("#3f271d", "#653b24", "#8b4d22", "#d67a11", "#e2a33c", "#eecc78", "#f4de9b")]
B0, B1, B2, B3 = [hx(c) for c in ("#2a1e17", "#3b2a1f", "#4f3828", "#664a33")]
S0, S1, S2, S3 = [hx(c) for c in ("#45403b", "#5c554e", "#756c62", "#90857a")]
INK = hx("#141516")
INK2 = hx("#1d2028")
HERO_PAL = {"#141516", "#14161c", "#1d2028", "#212224", "#272b35", "#2a1e17", "#2f3033", "#3b2a1f", "#3e3f42", "#3f271d",
            "#3f4552", "#45403b", "#4d4f52", "#4e5563", "#4f3828", "#5c554e", "#5c5e62", "#626a78", "#653b24", "#664a33",
            "#6c6f73", "#756c62", "#7d8084", "#8b4d22", "#8e9195", "#90857a", "#d67a11", "#e2a33c", "#eecc78", "#f4de9b"}
HERO = {hx(c)[:3] for c in HERO_PAL}
FX_ALLOWED = HERO | {X0[:3], X1[:3]}
GLOW_ONLY = {X0[:3], X1[:3], A26[:3]}
AW_ALLOWED = None   # 각성(60 Q19): LOPAD 팔레트 전체 + SL·PL·WD + X0/X1 — awaken60 prod_common.ALLOWED 를 늦게 읽는다


def aw_allowed():
    global AW_ALLOWED
    if AW_ALLOWED is None:
        import prod_common as PCM
        AW_ALLOWED = {tuple(c[:3]) if not isinstance(c, str) else hx(c)[:3] for c in PCM.ALLOWED}
    return AW_ALLOWED


# ---------------------------------------------------------------- 결정적 잡음
def h2(x, y, s=0):
    n = (int(x) * 374761393 + int(y) * 668265263 + int(s) * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536.0


class Rand:
    def __init__(self, seed):
        self.s = seed * 9973 + 17

    def f(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s / float(0x7FFFFFFF)

    def i(self, a, b):
        return a + int(self.f() * (b - a + 1)) if b > a else a


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


# ---------------------------------------------------------------- 캔버스
class Cv:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.im.load()

    def put(self, x, y, c, only_empty=False):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            if only_empty and self.p[x, y][3]:
                return
            self.p[x, y] = c

    def get(self, x, y):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[x, y]
        return (0, 0, 0, 0)

    def poly(self, pts, c):
        m = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(m).polygon([(float(x), float(y)) for x, y in pts], fill=255)
        self.im.paste(tuple(c), (0, 0), m)

    def line(self, x0, y0, x1, y1, c, only_empty=False):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / float(max(1, n))
            self.put(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, c, only_empty)

    def disc(self, cx, cy, r, c, only_empty=False):
        ri = int(math.ceil(r)) + 1
        for y in range(-ri, ri + 1):
            for x in range(-ri, ri + 1):
                if x * x + y * y <= r * r + 0.3:
                    self.put(cx + x, cy + y, c, only_empty)

    def ring(self, cx, cy, r, c, ky=1.0, dash=None, phase=0.0):
        steps = int(2 * math.pi * r * 1.6) + 16
        for i in range(steps):
            a = 2 * math.pi * i / steps
            if dash and ((math.degrees(a) + phase) % (dash[0] + dash[1])) >= dash[0]:
                continue
            self.put(cx + math.cos(a) * r, cy + math.sin(a) * r * ky, c)

    def paste_over(self, im, x=0, y=0):
        self.im.alpha_composite(im, (x, y))


# ---------------------------------------------------------------- 국소 좌표 (u = 진행 방향, v = 법선, 화면 y 아래 +)
class Frame:
    def __init__(self, cv, ox, oy, ang_deg):
        self.cv, self.ox, self.oy = cv, ox, oy
        a = math.radians(ang_deg)
        self.c, self.s = math.cos(a), math.sin(a)

    def P(self, u, v):
        return self.ox + u * self.c - v * self.s, self.oy + u * self.s + v * self.c

    def put(self, u, v, col, only_empty=False):
        x, y = self.P(u, v)
        self.cv.put(x, y, col, only_empty)

    def line(self, u0, v0, u1, v1, col, only_empty=False):
        x0, y0 = self.P(u0, v0)
        x1, y1 = self.P(u1, v1)
        self.cv.line(x0, y0, x1, y1, col, only_empty)

    def claw(self, u0, u1, w, layers, hook=0.0, voff=0.0, peak=0.72, back=0.08, tipk=1.0, hp=2.2, n=26):
        """발톱 획(곡선 바늘): u0(꼬리, 뾰족) → peak 최대 폭 w → u1 뾰족 끝. 중심선 v = voff + hook·t^hp (끝이 휜다).
        layers = [(폭 비율, 색)] 바깥부터 — 안쪽 층일수록 끝 쪽으로 몰린다(백열 심이 끝에 맺힘)."""
        for frac, col in layers:
            ww = w * frac / 2.0
            if ww < 0.35:
                ww = 0.35
            up, dn = [], []
            start = 0.0 if frac >= 0.99 else (1 - frac) * 0.35
            for k in range(n + 1):
                t = start + (1 - start) * k / float(n)
                u = u0 + (u1 - u0) * t
                if t < peak:
                    s = back + (1 - back) * (t / peak) ** 0.9
                else:
                    s = 1.0 - ((t - peak) / (1 - peak)) ** (1.4 * tipk)
                s = max(0.0, s)
                vc = voff + hook * t ** hp
                up.append(self.P(u, vc - ww * s))
                dn.append(self.P(u, vc + ww * s))
            self.cv.poly(up + list(reversed(dn)), col)

    def xglint(self, u, v, arm, core=None, mid=None, edge=None, tilt=45.0, long=1.0):
        """X 섬광(단검 표지): 진행 방향 ±tilt 로 교차한 두 바늘 + 가운데 백열."""
        core = core or X0
        mid = mid or X1
        edge = edge or A25
        for sg in (-1, 1):
            a = math.radians(tilt * sg)
            ca, sa = math.cos(a), math.sin(a)
            for k in range(-int(arm * long), int(arm * long) + 1):
                kk = abs(k) / max(1.0, arm * long)
                col = mid if kk < 0.4 else edge
                self.put(u + k * ca, v + k * sa, col)
        self.put(u, v, core)
        for du, dv in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            self.put(u + du, v + dv, mid)


# ---------------------------------------------------------------- 잉크(그림자 걸음·낙인 바탕)
def ink_blot(cv, cx, cy, r, seed, core=INK, rim=None, ky=1.0, ragged=0.35, holes=0.0):
    """잉크 얼룩: 들쭉날쭉한 가장자리(각도별 반경 잡음) + 선택 테두리 + 구멍(마르는 중)."""
    ri = int(r * (1 + ragged)) + 2
    rad = [r * (1 + ragged * (h2(k, seed, 7) * 2 - 1)) for k in range(24)]
    pts = []
    for y in range(-ri, ri + 1):
        for x in range(-ri, ri + 1):
            yy = y / ky
            d = math.hypot(x, yy)
            a = (math.atan2(yy, x) / (2 * math.pi) + 1) % 1 * 24
            k0 = int(a) % 24
            fr = a - int(a)
            rr = rad[k0] * (1 - fr) + rad[(k0 + 1) % 24] * fr
            if d <= rr:
                if holes and h2(cx + x, cy + y, seed) < holes * clamp(d / max(1, rr) * 1.4):
                    continue
                pts.append((x, y, d >= rr - 1.0))
    for x, y, edge in pts:
        cv.put(cx + x, cy + y, rim if (edge and rim) else core)


def ink_tendril(cv, x0, y0, ang, ln, w0, col, seed, wav=0.6):
    """번지는 잉크 가닥: 굵기 w0 → 0, 살짝 휘청."""
    for i in range(int(ln) + 1):
        t = i / max(1.0, ln)
        a = ang + wav * math.sin(t * 3.0 + seed)
        x = x0 + math.cos(ang) * i + math.cos(a + math.pi / 2) * 1.5 * math.sin(t * 4 + seed)
        y = y0 + math.sin(ang) * i + math.sin(a + math.pi / 2) * 1.5 * math.sin(t * 4 + seed)
        w = w0 * (1 - t) ** 0.8
        if w < 0.6:
            cv.put(x, y, col)
        else:
            cv.disc(x, y, w / 2.0, col)


# ---------------------------------------------------------------- 시트 읽기 (전/후)
def before_root():
    """고치기 전 단검 시트를 git BEFORE_REV 에서 out/before/ 로 풀어 둔다(아틀라스 그대로)."""
    os.makedirs(BEFORE, exist_ok=True)
    mark = os.path.join(BEFORE, ".rev")
    if os.path.exists(mark) and open(mark).read().strip() == BEFORE_REV:
        return BEFORE
    ls = subprocess.run(["git", "-C", ROOT, "ls-tree", "-r", "--name-only", BEFORE_REV, "assets/sprites/"],
                        capture_output=True, text=True, check=True).stdout.split()
    keep = [p for p in ls if ("dagger" in os.path.basename(p) or "shadowstep_ghost" in p)]
    for p in keep:
        dst = os.path.join(BEFORE, os.path.relpath(p, "assets/sprites"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        b = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (BEFORE_REV, p)], capture_output=True, check=True).stdout
        open(dst, "wb").write(b)
    open(mark, "w").write(BEFORE_REV)
    return BEFORE


def grid(rel, root=None):
    """(격자 메타, [[행 프레임...]...]) — 기본은 고치기 전 원본."""
    root = root or before_root()
    jp = os.path.join(root, rel + ".json")
    m = gridsheet.load_meta(jp)
    im = gridsheet.open_grid(jp)
    fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
    rows = im.height // fh
    fr = [[im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r in range(rows)]
    return m, fr


def starts(ms):
    out, t = [], 0
    for d in ms:
        out.append(t)
        t += d
    return out


def clip_margin(im, m=1):
    """틀 가장자리 m 도트 안을 비움(번지는 먹처럼 끝이 정해지지 않은 그림 전용 — 가장자리 잘림 0 규칙)."""
    p = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            if x < m or y < m or x >= w - m or y >= h - m:
                p[x, y] = (0, 0, 0, 0)


def reduce_colors(rows, cap, keep=()):
    """시트 색이 cap 을 넘으면 가장 적게 쓴 색을 가장 가까운(쓰인) 색으로 합친다(결정적). keep 색은 합치지 않음."""
    from collections import Counter
    cnt = Counter()
    for row in rows:
        for im in row:
            for c in im.getdata():
                if c[3]:
                    cnt[c[:3]] += 1
    mapping = {}
    cols = dict(cnt)
    keep = {k[:3] for k in keep}
    while len(cols) > cap:
        cand = sorted((n, c) for c, n in cols.items() if c not in keep)
        if not cand:
            break
        n, c = cand[0]
        others = [o for o in cols if o != c and o not in GLOW_ONLY] or [o for o in cols if o != c]
        tgt = min(others, key=lambda o: sum((a - b) ** 2 for a, b in zip(o, c)))
        mapping[c] = tgt
        cols[tgt] += cols.pop(c)
        for k, v in list(mapping.items()):
            if v == c:
                mapping[k] = tgt
    if not mapping:
        return rows
    for row in rows:
        for im in row:
            p = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    c = p[x, y]
                    if c[3] and c[:3] in mapping:
                        p[x, y] = mapping[c[:3]] + (255,)
    return rows


# ---------------------------------------------------------------- 검사
def check(name, rows, glow_cols, allowed, cap, edge_ok=False, semi_ok=False):
    cols = set()
    for j, row in enumerate(rows):
        for i, im in enumerate(row):
            w, h = im.size
            px = im.load()
            for y in range(h):
                for x in range(w):
                    c = px[x, y]
                    if not c[3]:
                        continue
                    assert c[3] == 255 or semi_ok, (name, j, i, "semi", x, y)
                    if not edge_ok:
                        assert 0 < x < w - 1 and 0 < y < h - 1, (name, j, i, "edge", x, y)
                    cols.add(c[:3])
                    if glow_cols is not None and i not in glow_cols:
                        assert c[:3] not in GLOW_ONLY, (name, j, i, "glow colour outside glowFrames", c)
    bad = cols - allowed
    assert not bad, (name, "palette", sorted(bad)[:5])
    assert len(cols) <= cap, (name, "colours", len(cols), cap)
    return len(cols)


# ---------------------------------------------------------------- 쓰기·게시
WRITTEN = []


def write_grid(cat, sub, name, rows, meta):
    """격자 원본 PNG + JSON 을 out/grid/<cat>/<sub>/ 에. meta = 기존 격자 메타(load_meta) 를 고친 것."""
    fw, fh = rows[0][0].size
    cols = len(rows[0])
    sheet = Image.new("RGBA", (cols * fw, len(rows) * fh), (0, 0, 0, 0))
    for r, row in enumerate(rows):
        assert len(row) == cols, (name, r)
        for c, im in enumerate(row):
            assert im.size == (fw, fh), (name, r, c, im.size)
            sheet.alpha_composite(im, (c * fw, r * fh))
    meta = dict(meta)
    assert meta["frameWidth"] == fw and meta["frameHeight"] == fh and meta["frames"] == cols, (name, "규격")
    meta["image"] = name + ".png"
    d = os.path.join(STAGE, cat, sub)
    os.makedirs(d, exist_ok=True)
    sheet.save(os.path.join(d, name + ".png"), optimize=True)
    with open(os.path.join(d, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
        f.write("\n")
    WRITTEN.append((cat, sub, name))
    return sheet


def _atlas():
    import importlib.util
    spec = importlib.util.spec_from_file_location("atlas57_build_d5", os.path.join(WORK, "atlas57", "build.py"))
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    return A


def staged(only=None):
    out = []
    for cat in ("fx", "weapons"):
        for sub in ("v3", "v4"):
            d = os.path.join(STAGE, cat, sub)
            if os.path.isdir(d):
                for f in sorted(os.listdir(d)):
                    if f.endswith(".json") and (not only or any(o in f for o in only)):
                        out.append((cat, sub, f[:-5]))
    return out


def publish(only=None):
    """out/grid 의 격자 원본 → assets 트림 아틀라스(atlas57 convert_sheet + apply_in_place, 전 프레임 대조 통과 시만).
    덮어쓰기 대상은 이름에 dagger 가 든 시트·hit_dagger·shadowstep_ghost 만(칼 담당과 겹치지 않음)."""
    A = _atlas()
    log = []
    for cat, sub, name in staged(only):
        assert "dagger" in name or name == "shadowstep_ghost", name
        dst = os.path.join(SPR, cat, sub)
        jp, pp = os.path.join(dst, name + ".json"), os.path.join(dst, name + ".png")
        old_pages = []
        if os.path.exists(jp):
            om = json.load(open(jp, encoding="utf-8"))
            old_pages = [t["image"] for t in om.get("textures", [])] or [om.get("meta", {}).get("image", name + ".png")]
        shutil.copy2(os.path.join(STAGE, cat, sub, name + ".png"), pp)
        shutil.copy2(os.path.join(STAGE, cat, sub, name + ".json"), jp)
        od = os.path.join(TMP, cat, sub)
        os.makedirs(od, exist_ok=True)
        res = A.convert_sheet(pp, jp, od, 2, 4096, True)
        A.apply_in_place(res, od, dst, pp, jp, 4096)
        new_pages = [n for n, _, _ in res["pages"]]
        for op in old_pages:
            if op not in new_pages and os.path.exists(os.path.join(dst, op)):
                os.remove(os.path.join(dst, op))
        log.append(dict(cat=cat, sub=sub, name=name, pages=[[n, w, h] for n, w, h in res["pages"]],
                        gpuAfterMB=round(res["gpuAfter"] / 2 ** 20, 4)))
    shutil.rmtree(TMP, ignore_errors=True)
    lp = os.path.join(HERE, "publish_log.json")
    prev = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else []
    names = {(x["cat"], x["sub"], x["name"]) for x in log}
    log = sorted([x for x in prev if (x["cat"], x["sub"], x["name"]) not in names] + log, key=lambda x: (x["cat"], x["sub"], x["name"]))
    with open(lp, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    print("publish %d 시트" % len(names))


def page_mb(json_path):
    """아틀라스 페이지 RGBA MB(GPU 추정)."""
    m = json.load(open(json_path, encoding="utf-8"))
    if "atlas" not in m:
        im = Image.open(json_path[:-5] + ".png")
        return im.width * im.height * 4 / 2 ** 20
    pages = [t["size"] for t in m["textures"]] if "textures" in m else [m["meta"]["size"]]
    return sum(p["w"] * p["h"] * 4 for p in pages) / 2 ** 20
