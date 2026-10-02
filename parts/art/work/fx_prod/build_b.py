#!/usr/bin/env python3
"""LOPAD 43라운드 — 인페르노 기반 무기 이펙트 양산 (B 묶음: 단검 7 · 활 9 · 보조 동작/대쉬 7 = 23종).

실행: python3 parts/art/work/fx_prod/build_b.py
입력: parts/art/palette/lopad.json (gray + floor1 ramp + fx 블록, 읽기만), assets/sprites/player/*.png (실루엣 마스크·미리보기),
      assets/sprites/enemies/*.png, assets/sprites/weapons/dagger_attack.png, assets/tiles/stage1.png (목업 합성용, 읽기만)
산출 (assets/sprites/fx/, 같은 id 로 기존 파일 교체):
  단검  dagger_slash 48 4dir 5f / twin 64 4dir 7f / gale 64 4dir 4f 루프 / dance 96 4dir 7f
        bleed 24 any 4f 루프 / afterimage 64 4dir 5f / assassin 64 any 5f
  활    bow_arrow 12x6 / bow_arrow_aimed 16x8 / pierce 32x8 4f 루프 / scatter 32 4f / flash 32x8 4f 루프
        heavyarrow 16x8 / heavyarrow_hit 64 any 5f / rain 32 4f / seek 24 4f 루프
  보조  parry_flash 48 any 5f / guard_wave 64x32 4dir 4f / shadowstep_ghost 16x24 4dir 3f / aim_charge 32 any 6f(진행도)
        aim_line 8x2 2f(상태) tile / dash_dust 16x8 4dir 3f (무채 유지) / dash_trail 16x24 4dir 3f (무채 유지, 시스템 틴트)
  미리보기: parts/art/work/fx_prod/preview_b.png (3배 블록 + 1배 띠), preview_b_fight.png (1배 목업 + 3배)
설계: parts/art/fx-design.md (3층 색 · 겹 1프레임 지연 · 섬광 → 광선 → 긴 꼬리 · 보조색 1무기/시트 · 예산 ≤11 · 반투명 0 · 고립 0).
칼·대검·공통·예고 묶음은 build.py (다른 에이전트). 이 스크립트는 그쪽 id 를 건드리지 않는다.
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OUT_FX = os.path.join(ROOT, "assets", "sprites", "fx")
SPR = os.path.join(ROOT, "assets", "sprites")
os.makedirs(OUT_FX, exist_ok=True)

with open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8") as fp:
    PAL = json.load(fp)
GRAY = PAL["gray"]
RAMP = PAL["floors"][0]["ramp"]
FX = PAL["fx"]
# 43라운드 결정: 대검 W2 #e35c1c → #d8441c. 팔레트 파일 갱신은 다른 에이전트 담당 — 아직 옛 값이면 여기서 결정값을 적용(guard_wave 만 대검 색을 쓴다).
if FX["weapons"]["greatsword"]["ramp"][2].lower() == "#e35c1c":
    FX["weapons"]["greatsword"]["ramp"][2] = "#d8441c"
DIRS = ["down", "up", "left", "right"]
DVEC = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}
FACE = {"right": 0, "down": 90, "left": 180, "up": 270}
# 1차 베기 호와 같은 방향 규약 (weapons/build.py SWEEP) — right 기준 그림을 회전해 쓰므로 결과는 동일
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
FONTB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 12)
PALETTE_NOTE = "parts/art/palette/lopad.json (gray + floor 1 accent 16-27 runtime swap + fx block: core X0/X1 + weapon secondary W0-W3, fixed)"
PALETTE_NOTE_GRAY = "parts/art/palette/lopad.json (gray only, no swap)"
PALETTE_NOTE_NOSEC = "parts/art/palette/lopad.json (gray + floor 1 accent 16-27 runtime swap + fx core X0/X1; no weapon secondary)"


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def G(i):
    return hx(GRAY[i])


def C(i):
    """층 강조 램프 인덱스 16~27 (1층 호박, 런타임 스왑)."""
    return hx(RAMP[i - 16])


X0, X1 = hx(FX["core"][0]), hx(FX["core"][1])


def W(wid, i):
    return hx(FX["weapons"][wid]["ramp"][i])


# ============================================================ 캔버스 (fx_concept/build.py 규약)
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.im.load()

    def px(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.p[x, y] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            v = self.p[x, y]
            return v if v[3] else None
        return None

    def line(self, x0, y0, x1, y1, c, pts=None):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        x, y = x0, y0
        while True:
            if pts is not None:
                pts.add((x, y))
            else:
                self.px(x, y, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x += sx
            if e2 <= dx:
                err += dx; y += sy

    def ray(self, ox, oy, ang_deg, r0, r1, c):
        a = math.radians(ang_deg)
        self.line(ox + r0 * math.cos(a), oy + r0 * math.sin(a), ox + r1 * math.cos(a), oy + r1 * math.sin(a), c)

    def disc(self, cx, cy, r, c, ky=1.0):
        for y in range(int(cy - r - 2), int(cy + r + 3)):
            for x in range(int(cx - r - 2), int(cx + r + 3)):
                if (x - cx) ** 2 + ((y - cy) / ky) ** 2 <= r * r + 0.25:
                    self.px(x, y, c)

    def ring(self, cx, cy, r, c, thick=1.0, a0=None, a1=None, dash=None, ky=1.0, phase=0):
        for y in range(self.h):
            for x in range(self.w):
                d = math.hypot(x - cx, (y - cy) / ky)
                if abs(d - r) > thick / 2.0:
                    continue
                th = math.degrees(math.atan2((y - cy) / ky, x - cx))
                if a0 is not None and (a1 - a0) % 360 != 0:
                    if (th - a0) % 360 > (a1 - a0) % 360:
                        continue
                if dash:
                    if (th - phase) % (dash[0] + dash[1]) >= dash[0]:
                        continue
                self.px(x, y, c)

    def arc(self, cx, cy, a0, a1, t0, t1, r_mid, thick, colors, head=0.75, head_boost=1, min_t=0.9, taper=0.55):
        """호 띠. colors 안쪽→바깥쪽. 양 끝은 가늘어진다 (taper 0 = 일정)."""
        span = a1 - a0
        aspan = abs(span)
        for y in range(self.h):
            for x in range(self.w):
                dx, dy = x - cx, y - cy
                r = math.hypot(dx, dy)
                if r < r_mid - thick - 2 or r > r_mid + thick + 2:
                    continue
                th = math.degrees(math.atan2(dy, dx))
                d = (th - a0) % 360 if span > 0 else (a0 - th) % 360
                if d > aspan:
                    continue
                t = d / aspan
                if t < t0 or t > t1:
                    continue
                s = (t - t0) / max(1e-6, (t1 - t0))
                tk = max(min_t, thick * math.sin(math.pi * s) ** taper)
                rin, rout = r_mid - tk / 2.0, r_mid + tk / 2.0
                if r < rin or r >= rout:
                    continue
                u = (r - rin) / (rout - rin)
                k = int(u * len(colors))
                if t >= head:
                    k += head_boost
                k = max(0, min(len(colors) - 1, k))
                self.px(x, y, colors[k])

    def blit(self, rows, ox, oy, legend):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    self.px(ox + i, oy + j, legend[ch])

    def pair(self, x, y, c, horiz=True):
        x, y = int(round(x)), int(round(y))
        self.px(x, y, c)
        self.px(x + (1 if horiz else 0), y + (0 if horiz else 1), c)

    def mask_paste(self, mask, ox, oy, color_fn):
        mp = mask.load()
        for y in range(mask.height):
            for x in range(mask.width):
                v = mp[x, y]
                if v[3]:
                    c = color_fn(x, y, v[:3])
                    if c is not None:
                        self.px(ox + x, oy + y, c)

    def outline_of(self, mask, ox, oy, c):
        mp = mask.load()
        Wm, Hm = mask.width, mask.height

        def a(x, y):
            return 0 <= x < Wm and 0 <= y < Hm and mp[x, y][3] > 0
        for y in range(Hm):
            for x in range(Wm):
                if a(x, y) and (not a(x - 1, y) or not a(x + 1, y) or not a(x, y - 1) or not a(x, y + 1)):
                    self.px(ox + x, oy + y, c)

    def dash_pattern(self, mod=4, keep=(0,), seed=0):
        for y in range(self.h):
            for x in range(self.w):
                if self.p[x, y][3] and ((x * 3 + y + seed) % mod) not in keep:
                    self.p[x, y] = (0, 0, 0, 0)

    def merge(self, other):
        for y in range(self.h):
            for x in range(self.w):
                if other.p[x, y][3]:
                    self.px(x, y, other.p[x, y])

    def despeckle8(self):
        rm = []
        for y in range(self.h):
            for x in range(self.w):
                if self.p[x, y][3] and not any(self.get(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)):
                    rm.append((x, y))
        for x, y in rm:
            self.p[x, y] = (0, 0, 0, 0)
        return len(rm)

    def isolated(self):
        n = 0
        for y in range(self.h):
            for x in range(self.w):
                if self.p[x, y][3] and not any(self.get(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)):
                    n += 1
        return n

    def rot90(self, k):
        im = self.im.rotate(90 * k, expand=True)
        cv = Canvas(im.width, im.height)
        cv.im, cv.p = im, im.load()
        return cv

    def flip_x(self):
        im = self.im.transpose(Image.FLIP_LEFT_RIGHT)
        cv = Canvas(im.width, im.height)
        cv.im, cv.p = im, im.load()
        return cv

    def bolt(self, pts_xy, layers):
        """폴리라인을 layers=[(dilate, color), ...] 순서(굵은 것 먼저)로 찍는다. 3겹 = 테두리·몸·코어."""
        base = set()
        for (x0, y0), (x1, y1) in zip(pts_xy, pts_xy[1:]):
            self.line(x0, y0, x1, y1, None, pts=base)
        for dil, col in layers:
            s = set(base)
            for _ in range(dil):
                s |= {(x + dx, y + dy) for (x, y) in s for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
            for x, y in s:
                self.px(x, y, col)


def prng(seed):
    s = (seed * 1103515245 + 12345) & 0x7fffffff
    while True:
        s = (s * 1103515245 + 12345) & 0x7fffffff
        yield (s >> 8) / float(1 << 23)


def zigzag(x0, y0, x1, y1, n, jag, seed):
    rnd = prng(seed)
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    pts = [(x0, y0)]
    for i in range(1, n):
        t = i / n
        off = (next(rnd) * 2 - 1) * jag
        pts.append((x0 + dx * t + nx * off, y0 + dy * t + ny * off))
    pts.append((x1, y1))
    return pts


def four_dirs_from_right(base):
    return {"right": base, "left": [cv.flip_x() for cv in base],
            "down": [cv.rot90(-1) for cv in base], "up": [cv.rot90(1) for cv in base]}


def sprite_frame(path, fw, fh, col, row):
    im = Image.open(path).convert("RGBA")
    return im.crop((col * fw, row * fh, col * fw + fw, row * fh + fh))


def player_frames(action, frame):
    im = Image.open(os.path.join(SPR, "player", "player_%s.png" % action)).convert("RGBA")
    return {d: im.crop((frame * 16, r * 24, frame * 16 + 16, r * 24 + 24)) for r, d in enumerate(DIRS)}


PDASH = player_frames("dash", 1)
PIDLE = player_frames("idle", 0)


def solid_fn(mask, fill, rim):
    """실루엣을 fill 단색, 우·하 가장자리만 rim 1px (분신끼리 겹쳐도 경계가 남는다)."""
    mp = mask.load()

    def a(x, y):
        return 0 <= x < mask.width and 0 <= y < mask.height and mp[x, y][3] > 0

    def fn(x, y, rgb):
        return rim if (not a(x + 1, y) or not a(x, y + 1)) else fill
    return fn


# ============================================================ 시트 저장 · 검사
GS = [G(i)[:3] for i in range(16)]
CS = [C(i)[:3] for i in range(16, 28)]
XS = [X0[:3], X1[:3]]
WS = {wid: [W(wid, i)[:3] for i in range(4)] for wid in FX["weapons"]}


def save_sheet(name, frames_by_dir, dirs, w, h, durations, loop, pivot, extra, action=None):
    n = len(durations)
    sheet = Image.new("RGBA", (w * n, h * len(dirs)), (0, 0, 0, 0))
    for r, d in enumerate(dirs):
        for c, cv in enumerate(frames_by_dir[d]):
            assert cv.w == w and cv.h == h, (name, cv.w, cv.h)
            sheet.alpha_composite(cv.im, (c * w, r * h))
    sheet.save(os.path.join(OUT_FX, name + ".png"))
    meta = {
        "image": name + ".png",
        "action": action or name,
        "frameWidth": w, "frameHeight": h,
        "frames": n,
        "directions": dirs,
        "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column",
        "fps": round(1000.0 / (sum(durations) / n)) if sum(durations) else 0,
        "frameDurationsMs": durations,
        "loop": loop,
        "pivot": {"x": pivot[0], "y": pivot[1]},
        "palette": PALETTE_NOTE,
    }
    meta.update(extra)
    with open(os.path.join(OUT_FX, name + ".json"), "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    return sheet


def color_report(name, frames_by_dir, wid=None, gray_budget=2, accent_budget=None):
    cols = set()
    iso = semi = 0
    for d, fr in frames_by_dir.items():
        for cv in fr:
            iso += cv.isolated()
            for px in cv.im.getdata():
                if px[3] == 255:
                    cols.add(px[:3])
                elif px[3]:
                    semi += 1
    grays = sorted(GS.index(c) for c in cols if c in GS and c not in XS)
    accents = sorted(16 + CS.index(c) for c in cols if c in CS)
    core = sorted(XS.index(c) for c in cols if c in XS)
    sec, other = {}, []
    for c in cols:
        if c in GS or c in CS or c in XS:
            continue
        hit = [(k, v.index(c)) for k, v in WS.items() if c in v]
        if hit:
            sec.setdefault(hit[0][0], []).append(hit[0][1])
        else:
            other.append(c)
    sec = {k: sorted(v) for k, v in sec.items()}
    if accent_budget is None:
        accent_budget = 3 if sec else 8
    total = len(grays) + len(accents) + len(core) + sum(len(v) for v in sec.values())
    bad = (len(grays) > gray_budget or len(accents) > accent_budget or other or iso or semi or len(sec) > 1
           or (wid and sec and wid not in sec) or (wid is None and sec) or total > 11)
    print("%-18s gray%s core%s accent%s sec%s total=%d other=%d iso=%d semi=%d%s" % (
        name, grays, core, accents, sec, total, len(other), iso, semi, "  <-- CHECK" if bad else ""))
    return not bad


# ============================================================ 공통 그리기 — 단검 '그림자 호'
DG = "dagger"


def dagger_stroke(cv, cx, cy, a0, a1, r, tk, t_main=None, t_shadow=None, mode="normal", head=0.7, shadow_r=3):
    """단검 호: 본 띠(얇음, 3층) + 바깥쪽 r+3 에 W0 단색 '그림자 잔상'(1프레임 늦게 따라옴).
    mode: hot(섬광 프레임: 몸체 전체 백열) / normal(W 몸체 + 1px 코어) / cool(W1/W2 만, 코어 없음)."""
    if t_shadow is not None and t_shadow[1] > t_shadow[0]:
        cv.arc(cx, cy, a0, a1, t_shadow[0], t_shadow[1], r + shadow_r, max(2.4, tk * 0.7), [W(DG, 1), W(DG, 0)], head=2, min_t=1.0)
    if t_main is None or t_main[1] <= t_main[0]:
        return
    if mode == "hot":
        cv.arc(cx, cy, a0, a1, t_main[0], t_main[1], r, tk, [W(DG, 0), W(DG, 3), X1, X0, X1, W(DG, 3)], head=head, head_boost=0)
    elif mode == "normal":
        cv.arc(cx, cy, a0, a1, t_main[0], t_main[1], r, tk, [W(DG, 0), W(DG, 1), W(DG, 2), W(DG, 3), W(DG, 2), W(DG, 1)], head=head, head_boost=0)
        cv.arc(cx, cy, a0, a1, t_main[0] + 0.05, t_main[1] - 0.02, r + 0.5, 1.0, [X1, X0], head=head, head_boost=1, min_t=1.0, taper=0.0)
    elif mode == "warm":   # 식는 중: 코어가 W3
        cv.arc(cx, cy, a0, a1, t_main[0], t_main[1], r, tk, [W(DG, 0), W(DG, 1), W(DG, 2), W(DG, 3), W(DG, 2), W(DG, 1)], head=head, head_boost=0)
        cv.arc(cx, cy, a0, a1, t_main[0] + 0.05, t_main[1] - 0.02, r + 0.5, 1.0, [W(DG, 3), X1], head=head, head_boost=1, min_t=1.0, taper=0.0)
    else:
        cv.arc(cx, cy, a0, a1, t_main[0], t_main[1], r, tk * 0.7, [W(DG, 0), W(DG, 1), W(DG, 2), W(DG, 1)], head=2, min_t=1.0)


def head_glint(cv, cx, cy, a0, a1, t, r, col, horiz=True):
    ang = math.radians(a0 + (a1 - a0) * t)
    cv.pair(cx + r * math.cos(ang), cy + r * math.sin(ang), col, horiz=horiz)


def spill_rays(cv, cx, cy, a0, a1, t, r, n=3, length=7, seed=1, cols=None):
    rnd = prng(seed)
    ang = math.radians(a0 + (a1 - a0) * t)
    ox, oy = cx + r * math.cos(ang), cy + r * math.sin(ang)
    for i in range(n):
        da = (i - (n - 1) / 2.0) * 28 + (next(rnd) * 10 - 5)
        a = ang + math.radians(da)
        L = length + next(rnd) * 3
        cv.bolt(zigzag(ox, oy, ox + L * math.cos(a), oy + L * math.sin(a), 3, 1.2, seed + i), cols)


def remnant(cv, cx, cy, a0, a1, t0, t1, r, cols, mod=4, keep=(0, 1, 2), seed=0, thick=2.2):
    tmp = Canvas(cv.w, cv.h)
    tmp.arc(cx, cy, a0, a1, t0, t1, r, thick, cols, head=2, min_t=1.0)
    tmp.dash_pattern(mod=mod, keep=keep, seed=seed)
    cv.merge(tmp)


def spark_at(cv, cx, cy, a_deg, r, col, horiz=True):
    ang = math.radians(a_deg)
    cv.pair(cx + r * math.cos(ang), cy + r * math.sin(ang), col, horiz=horiz)


# ============================================================ 단검 1. 기본 베기 48 · 5f
def dagger_slash_frames():
    """48×48, 피벗 (24,34). 짧고 빠른 호(140°, r11, 3.6px) + 바깥 W0 그림자 잔상 1프레임 지연. right 기준 -80°→60°."""
    cx, cy, r, tk = 24, 24, 11.0, 3.6
    a0, a1 = -80, 60
    fr = []
    cv = Canvas(48, 48)   # f0 예비: 코어 점선 앞 절반
    cv.arc(cx, cy, a0, a1, 0.0, 0.5, r, 1.6, [W(DG, 2), X1], head=0.35, min_t=1.0)
    head_glint(cv, cx, cy, a0, a1, 0.5, r + 1, C(27))
    fr.append(cv)
    cv = Canvas(48, 48)   # f1 본 띠 전체 + 그림자 앞 절반
    dagger_stroke(cv, cx, cy, a0, a1, r, tk, t_main=(0.0, 1.0), t_shadow=(0.0, 0.5), mode="normal", head=0.65)
    head_glint(cv, cx, cy, a0, a1, 0.97, r + 3, C(27))
    fr.append(cv)
    cv = Canvas(48, 48)   # f2 띠 식음(코어 W3) + 그림자 전체 + 광선 2
    dagger_stroke(cv, cx, cy, a0, a1, r, tk * 0.9, t_main=(0.12, 1.0), t_shadow=(0.0, 1.0), mode="warm", head=0.8)
    spill_rays(cv, cx, cy, a0, a1, 0.97, r, n=2, length=5, seed=3, cols=[(1, W(DG, 0)), (0, C(27))])
    fr.append(cv)
    cv = Canvas(48, 48)   # f3 어두운 띠 + 그림자 점선
    dagger_stroke(cv, cx, cy, a0, a1, r, tk, t_main=(0.3, 1.0), mode="cool")
    remnant(cv, cx, cy, a0, a1, 0.15, 1.0, r + 3, [W(DG, 0), W(DG, 0)], mod=4, keep=(0, 1, 2), seed=2)
    spark_at(cv, cx, cy, a1 - 10, r + 6, C(24))
    fr.append(cv)
    cv = Canvas(48, 48)   # f4 꼬리: 점선 + 불티
    remnant(cv, cx, cy, a0, a1, 0.45, 1.0, r, [W(DG, 0), W(DG, 1)], mod=4, keep=(0, 1, 2))
    remnant(cv, cx, cy, a0, a1, 0.35, 0.95, r + 3, [W(DG, 0), W(DG, 0)], mod=5, keep=(0, 1), seed=2)
    spark_at(cv, cx, cy, a1 - 20, r + 7, C(22), horiz=False)
    spark_at(cv, cx, cy, a1 - 50, r + 2, C(22))
    fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return four_dirs_from_right(fr)


# ============================================================ 단검 2. 쌍격 64 · 7f
def twin_frames():
    """64×64, 피벗 (32,42). 안쪽 호(r13) → 바깥 호(r19) 가 1프레임 늦게 = 2타. 각 호에 W0 그림자. -90°→70°."""
    cx, cy = 32, 32
    ri, ro = 13.0, 19.0
    tki, tko = 3.6, 4.2
    a0, a1 = -90, 70
    fr = []
    cv = Canvas(64, 64)   # f0 예비: 바깥 궤적 점선 + 안쪽 코어 머리
    cv.arc(cx, cy, a0, a1, 0.0, 1.0, ro, 1.4, [W(DG, 2)], head=2, min_t=1.0)
    cv.dash_pattern(mod=5, keep=(0, 1, 2), seed=1)
    cv.arc(cx, cy, a0, a1, 0.0, 0.3, ri, 2.0, [W(DG, 3), X1], head=0.2, min_t=1.0)
    head_glint(cv, cx, cy, a0, a1, 0.3, ri + 1, C(27))
    fr.append(cv)
    cv = Canvas(64, 64)   # f1 1타 섬광: 안쪽 호 백열 + 그림자 절반
    dagger_stroke(cv, cx, cy, a0, a1, ri, tki, t_main=(0.0, 1.0), t_shadow=(0.0, 0.5), mode="hot", head=0.5)
    head_glint(cv, cx, cy, a0, a1, 0.97, ri + 3, C(27))
    fr.append(cv)
    cv = Canvas(64, 64)   # f2 2타 섬광: 바깥 호 백열 + 안쪽 호 정상(코어) + 그림자 + 광선 3
    dagger_stroke(cv, cx, cy, a0, a1, ri, tki, t_main=(0.08, 1.0), t_shadow=(0.0, 1.0), mode="normal", head=0.8)
    dagger_stroke(cv, cx, cy, a0, a1, ro, tko, t_main=(0.0, 1.0), t_shadow=(0.0, 0.5), mode="hot", head=0.5, shadow_r=4)
    spill_rays(cv, cx, cy, a0, a1, 0.98, ro, n=3, length=8, seed=11, cols=[(1, W(DG, 0)), (0, X0)])
    head_glint(cv, cx, cy, a0, a1, 0.9, ro + 5, C(27), horiz=False)
    fr.append(cv)
    cv = Canvas(64, 64)   # f3 둘 다 식음: 바깥 정상(코어 X1) + 안쪽 cool + 그림자 둘 + 광선 2
    dagger_stroke(cv, cx, cy, a0, a1, ri, tki, t_main=(0.2, 1.0), t_shadow=(0.1, 1.0), mode="cool")
    dagger_stroke(cv, cx, cy, a0, a1, ro, tko * 0.9, t_main=(0.1, 1.0), t_shadow=(0.0, 1.0), mode="warm", head=0.85, shadow_r=4)
    spill_rays(cv, cx, cy, a0, a1, 0.99, ro, n=2, length=6, seed=12, cols=[(1, W(DG, 0)), (0, C(24))])
    fr.append(cv)
    cv = Canvas(64, 64)   # f4 어두운 띠 둘 + 그림자 점선
    dagger_stroke(cv, cx, cy, a0, a1, ri, tki, t_main=(0.35, 1.0), mode="cool")
    dagger_stroke(cv, cx, cy, a0, a1, ro, tko, t_main=(0.25, 1.0), mode="cool")
    remnant(cv, cx, cy, a0, a1, 0.2, 1.0, ro + 4, [W(DG, 0), W(DG, 0)], mod=4, keep=(0, 1, 2), seed=3)
    spark_at(cv, cx, cy, a1 - 12, ro + 7, C(24))
    fr.append(cv)
    cv = Canvas(64, 64)   # f5 점선
    remnant(cv, cx, cy, a0, a1, 0.4, 1.0, ri, [W(DG, 0), W(DG, 1)], mod=4, keep=(0, 1, 2), seed=4)
    remnant(cv, cx, cy, a0, a1, 0.35, 1.0, ro, [W(DG, 0), W(DG, 1), W(DG, 1)], mod=4, keep=(0, 1, 2), seed=5)
    remnant(cv, cx, cy, a0, a1, 0.3, 0.98, ro + 4, [W(DG, 0), W(DG, 0)], mod=5, keep=(0, 1), seed=6)
    spark_at(cv, cx, cy, a1 - 25, ro + 8, C(22), horiz=False)
    fr.append(cv)
    cv = Canvas(64, 64)   # f6 꼬리
    remnant(cv, cx, cy, a0, a1, 0.5, 1.0, ro, [W(DG, 0), W(DG, 0)], mod=6, keep=(0, 1), seed=7)
    remnant(cv, cx, cy, a0, a1, 0.55, 1.0, ri, [W(DG, 0), W(DG, 0)], mod=6, keep=(0, 1), seed=8)
    spark_at(cv, cx, cy, a1 - 40, ro + 2, C(22))
    spark_at(cv, cx, cy, a1 - 15, ro + 9, C(22), horiz=False)
    fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return four_dirs_from_right(fr)


# ============================================================ 단검 3. 질풍 64 · 4f 루프
def gale_frames():
    """64×64, 피벗 (32,42), 플레이어 아래. 몸 뒤(right 기준 왼쪽)를 감싸는 바람 호(r10) + 뒤로 길게 흐르는 곡선 바람 줄 3(2px: 색 + W0 그림자 밑줄).
    토막(9 on 3 off, 주기 12)이 프레임마다 3px 뒤로 흘러 4프레임 = 1주기 = 이음새 없음. 감싸는 호의 글린트도 4프레임에 한 바퀴."""
    bx, by = 32, 32
    fr = []
    streaks = [(-8, 0.32, 26, 0), (0, 0.0, 29, 4), (8, -0.32, 26, 8)]   # (y 오프셋, 벌어짐, 길이, 위상)
    for f in range(4):
        cv = Canvas(64, 64)
        # 몸 뒤를 감싸는 호 (W2) + 도는 글린트 (W3, 4프레임 = 한 바퀴)
        cv.arc(bx, by, 125, 235, 0.0, 1.0, 10.5, 2.0, [W(DG, 0), W(DG, 2)], head=2, min_t=1.5)
        g0 = (f * 0.25) % 1.0
        cv.arc(bx, by, 125, 235, g0, min(1.0, g0 + 0.22), 10.5, 2.0, [W(DG, 2), W(DG, 3)], head=2, min_t=1.5)
        if g0 + 0.22 > 1.0:
            cv.arc(bx, by, 125, 235, 0.0, g0 + 0.22 - 1.0, 10.5, 2.0, [W(DG, 2), W(DG, 3)], head=2, min_t=1.5)
        for k, (dy, spread, L, ph) in enumerate(streaks):
            for sidx in range(L):
                x = 24 - sidx
                y = by + dy + spread * (sidx * sidx) / 48.0
                u = sidx / float(L)
                col = W(DG, 3) if u < 0.18 else (W(DG, 2) if u < 0.5 else (W(DG, 1) if u < 0.8 else W(DG, 0)))
                on = ((sidx + f * 3 + ph) % 12) < 9
                yy = int(round(y))
                if on:
                    cv.px(x, yy, col)
                    if u < 0.8:
                        cv.px(x, yy + 1, W(DG, 0))
        # 가운데 줄의 코어 토막 (X1 2px, 흐름과 같이 이동)
        for sidx in range(29):
            m = (sidx + f * 3 + 4) % 12
            if m in (3, 4) and sidx < 14:
                cv.px(24 - sidx, by, X1)
        cv.pair(24 - 19 - (f % 2), by - 13 + (f // 2), W(DG, 2), horiz=True)
        cv.despeckle8()
        fr.append(cv)
    return four_dirs_from_right(fr)


# ============================================================ 단검 4. 난무 96 · 7f
def dance_frames():
    """96×96, 피벗 (48,58). 3중 베기 군집: r14(정방향) → r21(역방향) → r28(정방향) 호가 1프레임씩 이어지고 각자 W0 그림자. 2차 = 섬광 + 광선 4."""
    cx, cy = 48, 48
    a0, a1 = -95, 75
    sw = [(a0, a1), (a1, a0), (a0, a1)]
    rr = [14.0, 21.0, 28.0]
    tk = [3.6, 4.0, 4.6]
    fr = []
    cv = Canvas(96, 96)   # f0 예비: 세 궤적 점선 + 1타 머리
    for k in range(3):
        cv.arc(cx, cy, sw[k][0], sw[k][1], 0.0, 1.0, rr[k], 1.2, [W(DG, 1) if k else W(DG, 2)], head=2, min_t=1.0)
    cv.dash_pattern(mod=5, keep=(0, 1, 2), seed=1)
    cv.arc(cx, cy, a0, a1, 0.0, 0.3, rr[0], 2.0, [W(DG, 3), X1], head=0.2, min_t=1.0)
    head_glint(cv, cx, cy, a0, a1, 0.3, rr[0] + 1, C(27))
    fr.append(cv)
    cv = Canvas(96, 96)   # f1 1타 섬광
    dagger_stroke(cv, cx, cy, sw[0][0], sw[0][1], rr[0], tk[0], t_main=(0.0, 1.0), t_shadow=(0.0, 0.5), mode="hot", head=0.5)
    head_glint(cv, cx, cy, sw[0][0], sw[0][1], 0.97, rr[0] + 3, C(27))
    fr.append(cv)
    cv = Canvas(96, 96)   # f2 2타 섬광(역방향) + 1타 정상
    dagger_stroke(cv, cx, cy, sw[0][0], sw[0][1], rr[0], tk[0], t_main=(0.1, 1.0), t_shadow=(0.0, 1.0), mode="normal", head=0.8)
    dagger_stroke(cv, cx, cy, sw[1][0], sw[1][1], rr[1], tk[1], t_main=(0.0, 1.0), t_shadow=(0.0, 0.5), mode="hot", head=0.5)
    head_glint(cv, cx, cy, sw[1][0], sw[1][1], 0.97, rr[1] + 3, C(27))
    fr.append(cv)
    cv = Canvas(96, 96)   # f3 3타 섬광 + 2타 정상 + 1타 식음 + 광선 4
    dagger_stroke(cv, cx, cy, sw[0][0], sw[0][1], rr[0], tk[0], t_main=(0.25, 1.0), t_shadow=(0.1, 1.0), mode="cool")
    dagger_stroke(cv, cx, cy, sw[1][0], sw[1][1], rr[1], tk[1], t_main=(0.1, 1.0), t_shadow=(0.0, 1.0), mode="normal", head=0.8)
    dagger_stroke(cv, cx, cy, sw[2][0], sw[2][1], rr[2], tk[2], t_main=(0.0, 1.0), t_shadow=(0.0, 0.5), mode="hot", head=0.5, shadow_r=4)
    spill_rays(cv, cx, cy, sw[2][0], sw[2][1], 0.98, rr[2], n=4, length=10, seed=21, cols=[(1, W(DG, 0)), (0, X0)])
    head_glint(cv, cx, cy, sw[2][0], sw[2][1], 0.9, rr[2] + 6, C(27), horiz=False)
    for k in range(4):
        ang = math.radians(k * 90 + 45)
        cv.pair(cx + 9 * math.cos(ang), cy + 9 * math.sin(ang), C(27), horiz=(k % 2 == 0))
    fr.append(cv)
    cv = Canvas(96, 96)   # f4 3타 식음(코어 W3) + 1·2타 어두운 띠 + 그림자 + 광선 2
    dagger_stroke(cv, cx, cy, sw[0][0], sw[0][1], rr[0], tk[0], t_main=(0.4, 1.0), mode="cool")
    dagger_stroke(cv, cx, cy, sw[1][0], sw[1][1], rr[1], tk[1], t_main=(0.3, 1.0), t_shadow=(0.2, 1.0), mode="cool")
    dagger_stroke(cv, cx, cy, sw[2][0], sw[2][1], rr[2], tk[2] * 0.9, t_main=(0.1, 1.0), t_shadow=(0.0, 1.0), mode="warm", head=0.85, shadow_r=4)
    spill_rays(cv, cx, cy, sw[2][0], sw[2][1], 0.99, rr[2], n=2, length=7, seed=22, cols=[(1, W(DG, 0)), (0, C(24))])
    fr.append(cv)
    cv = Canvas(96, 96)   # f5 점선 셋
    remnant(cv, cx, cy, sw[0][0], sw[0][1], 0.5, 1.0, rr[0], [W(DG, 0), W(DG, 0)], mod=5, keep=(0, 1), seed=3)
    remnant(cv, cx, cy, sw[1][0], sw[1][1], 0.4, 1.0, rr[1], [W(DG, 0), W(DG, 1)], mod=4, keep=(0, 1, 2), seed=4)
    remnant(cv, cx, cy, sw[2][0], sw[2][1], 0.35, 1.0, rr[2], [W(DG, 0), W(DG, 1), W(DG, 1)], mod=4, keep=(0, 1, 2), seed=5)
    remnant(cv, cx, cy, sw[2][0], sw[2][1], 0.3, 0.98, rr[2] + 4, [W(DG, 0), W(DG, 0)], mod=5, keep=(0, 1), seed=6)
    spark_at(cv, cx, cy, a1 - 25, rr[2] + 9, C(22), horiz=False)
    fr.append(cv)
    cv = Canvas(96, 96)   # f6 꼬리
    remnant(cv, cx, cy, sw[2][0], sw[2][1], 0.5, 1.0, rr[2], [W(DG, 0), W(DG, 0)], mod=6, keep=(0, 1), seed=7)
    remnant(cv, cx, cy, sw[1][0], sw[1][1], 0.6, 1.0, rr[1], [W(DG, 0), W(DG, 0)], mod=6, keep=(0, 1), seed=8)
    spark_at(cv, cx, cy, a1 - 40, rr[2] + 3, C(22))
    spark_at(cv, cx, cy, a1 - 15, rr[2] + 10, C(22), horiz=False)
    fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return four_dirs_from_right(fr)


# ============================================================ 단검 5. 출혈 24 · 4f 루프
def bleed_frames():
    """24×24 any, 피벗 (12,12), 적 따라감. 핏방울 3줄(층 램프 17/18/20 = 피) + 단검 그림자(W0 밑·W1 그늘) + 발밑 W0 웅덩이. 4f = 틱 500ms, f0 = 틱 글린트(X1)."""
    fr = []
    LT, MD, DK = C(20), C(18), C(17)
    for f in range(4):
        cv = Canvas(24, 24)
        cv.disc(12, 21, 5.5, W(DG, 0), ky=0.32)                       # 그림자 웅덩이 (단검 어휘)
        for col_i, (x, ph) in enumerate(((4, 0), (10, 2), (16, 1))):
            k = (f + ph) % 4
            y = 2 + k * 4
            if k < 3:
                cv.px(x + 1, y, LT)
                cv.px(x, y + 1, LT); cv.px(x + 1, y + 1, MD); cv.px(x + 2, y + 1, W(DG, 1))
                cv.px(x, y + 2, MD); cv.px(x + 1, y + 2, MD); cv.px(x + 2, y + 2, W(DG, 1))
                cv.px(x + 1, y + 3, W(DG, 0))
                if k >= 1:
                    cv.px(x + 1, y - 1, DK); cv.px(x + 1, y - 2, W(DG, 1))   # 늘어진 꼬리
                if k == 2:
                    cv.px(x + 1, y + 4, W(DG, 0)); cv.px(x + 1, y - 3, W(DG, 1))
                if k == 0 and f == 0:
                    cv.px(x + 1, y, X1); cv.px(x, y, X1)                      # 틱 글린트
            else:
                cv.line(x - 1, 19, x + 3, 19, MD); cv.px(x - 1, 19, W(DG, 0)); cv.px(x + 3, 19, W(DG, 0))
                cv.px(x, 18, LT); cv.px(x + 2, 18, LT)
        cv.despeckle8()
        fr.append(cv)
    return {"any": fr}


# ============================================================ 단검 6. 잔상 64 · 5f (대쉬 출발점 분신 군집)
def afterimage_frames():
    """64×64 4방향, 피벗 (32,42) = 출발 발 위치, 바닥 깊이·고정. 돌진 실루엣 분신 3(가운데 + 좌우 8px)이 W2→W1→W0 로 흩어지고 바닥 W0 웅덩이 수축 + 교차 베기 2줄."""
    out = {}
    for d in DIRS:
        m = PDASH[d]
        ox, oy = 24, 19                       # 발 (8,23) → (32,42)
        side = (0, 1) if d in ("left", "right") else (1, 0)   # 분신이 벌어지는 축 = 대쉬에 수직
        fr = []
        for f in range(5):
            cv = Canvas(64, 64)
            pr = [13, 15, 13, 9, 5][f]
            cv.disc(32, 41, pr, W(DG, 0), ky=0.36)
            if f == 0:
                cv.mask_paste(m, ox, oy, solid_fn(m, W(DG, 2), W(DG, 1)))
                cv.outline_of(m, ox, oy, W(DG, 0))
                cv.mask_paste(m, ox, oy, solid_fn(m, W(DG, 2), W(DG, 1)))
                cv.px(ox + 7, oy + 8, X1); cv.px(ox + 8, oy + 8, X1)
            elif f == 1:
                cv.ring(32, 41, pr, W(DG, 1), thick=1.2, ky=0.36, dash=(30, 15))
                for sgn in (-1, 1):
                    cv.mask_paste(m, ox + sgn * 11 * side[0], oy + sgn * 11 * side[1], solid_fn(m, W(DG, 1), W(DG, 0)))
                cv.mask_paste(m, ox, oy, solid_fn(m, W(DG, 2), W(DG, 1)))
                cv.bolt([(16, 46), (48, 18)], [(1, W(DG, 0)), (0, W(DG, 3))])
                cv.bolt([(18, 46), (46, 20)], [(0, X0)])
                cv.bolt([(48, 44), (20, 20)], [(1, W(DG, 0)), (0, W(DG, 3))])
                cv.bolt([(44, 42), (22, 22)], [(0, X1)])
                cv.pair(32, 24, C(27)); cv.pair(30, 40, C(27))
            elif f == 2:
                tmp = Canvas(64, 64)
                for sgn in (-1, 1):
                    tmp.mask_paste(m, ox + sgn * 15 * side[0], oy + sgn * 15 * side[1], lambda x, y, rgb: W(DG, 1))
                tmp.mask_paste(m, ox, oy, lambda x, y, rgb: W(DG, 2))
                for y in range(64):
                    for x in range(64):
                        if tmp.p[x, y][3] and (x % 3 != 1):
                            cv.px(x, y, tmp.p[x, y])
                t2 = Canvas(64, 64)
                t2.bolt([(18, 44), (46, 20)], [(0, W(DG, 2))])
                t2.dash_pattern(mod=3, keep=(0, 1), seed=3)
                cv.merge(t2)
                cv.pair(24, 18, C(24), horiz=False); cv.pair(42, 46, C(24))
            elif f == 3:
                tmp = Canvas(64, 64)
                for sgn in (-1, 1):
                    tmp.mask_paste(m, ox + sgn * 18 * side[0], oy + sgn * 18 * side[1], lambda x, y, rgb: W(DG, 1) if (x % 3 == 0 and y % 2 == 0) else None)
                tmp.mask_paste(m, ox, oy, lambda x, y, rgb: W(DG, 1) if (x % 3 == 0) else None)
                cv.merge(tmp)
                cv.pair(30, 38, C(22))
            else:
                for (x, y) in ((14, 24), (46, 22), (26, 14), (40, 46), (18, 44)):
                    cv.pair(x, y, W(DG, 1), horiz=(x % 2 == 0))
                cv.pair(33, 28, W(DG, 2))
            cv.despeckle8()
            fr.append(cv)
        out[d] = fr
    return out


# ============================================================ 단검 7. 암살 64 · 5f (콘셉트 승격)
def assassin_frames():
    """64×64 any, 피벗 (32,32) = 적중점. 바닥 웅덩이(W0) + 그림자 분신 3이 모여듦 → 교차 섬광 2줄(3겹) → 세로 줄무늬로 흩어짐 → 웅덩이 수축."""
    cx, cy = 32, 32
    mask = PIDLE["down"]
    fr = []

    def pool(cv, r, col):
        cv.disc(cx, cy + 13, r, col, ky=0.42)

    cv = Canvas(64, 64)   # f0 멀리서 모여드는 분신 3 (W0)
    pool(cv, 15, W(DG, 0))
    for (ox, oy) in ((2, 26), (46, 24), (24, -6)):
        cv.mask_paste(mask, ox, oy, lambda x, y, rgb: W(DG, 0))
    fr.append(cv)
    cv = Canvas(64, 64)   # f1 가까이 (W1 + W0 림) + 웅덩이 림
    pool(cv, 17, W(DG, 0))
    cv.ring(cx, cy + 13, 17, W(DG, 1), thick=1.2, ky=0.42, dash=(30, 15))
    for (ox, oy) in ((7, 21), (41, 19), (24, -1)):
        cv.mask_paste(mask, ox, oy, solid_fn(mask, W(DG, 1), W(DG, 0)))
    cv.pair(cx, cy - 2, X1)
    fr.append(cv)
    cv = Canvas(64, 64)   # f2 교차 섬광 2줄(3겹) + 분신 W2
    pool(cv, 18, W(DG, 0))
    for (ox, oy) in ((11, 17), (37, 15), (24, 4)):
        cv.mask_paste(mask, ox, oy, solid_fn(mask, W(DG, 2), W(DG, 1)))
    cv.bolt([(10, 54), (54, 10)], [(1, W(DG, 0)), (0, W(DG, 3))])
    cv.bolt([(12, 56), (52, 12)], [(0, X0)])
    cv.bolt([(54, 52), (14, 14)], [(1, W(DG, 0)), (0, W(DG, 3))])
    cv.bolt([(50, 50), (16, 16)], [(0, X1)])
    for a in (0, 90, 180, 270):
        ang = math.radians(a + 45)
        cv.pair(cx + 12 * math.cos(ang), cy + 12 * math.sin(ang), C(27), horiz=(a % 180 == 0))
    fr.append(cv)
    cv = Canvas(64, 64)   # f3 섬광 점선 + 분신 세로 줄무늬
    pool(cv, 15, W(DG, 0))
    cv.ring(cx, cy + 13, 15, W(DG, 1), thick=1.0, ky=0.42, dash=(20, 20), phase=7)
    tmp = Canvas(64, 64)
    for (ox, oy) in ((7, 21), (41, 19), (24, -1)):
        tmp.mask_paste(mask, ox, oy, lambda x, y, rgb: W(DG, 1))
    for y in range(64):
        for x in range(64):
            if tmp.p[x, y][3] and (x % 3 != 1):
                cv.px(x, y, tmp.p[x, y])
    t2 = Canvas(64, 64)
    t2.bolt([(16, 48), (48, 16)], [(0, W(DG, 2))])
    t2.dash_pattern(mod=3, keep=(0, 1), seed=3)
    cv.merge(t2)
    pool(cv, 15, W(DG, 0))
    cv.pair(cx - 13, cy - 10, C(25), horiz=False)
    cv.pair(cx + 11, cy + 11, C(24))
    fr.append(cv)
    cv = Canvas(64, 64)   # f4 꼬리: 웅덩이 수축 + 조각
    pool(cv, 10, W(DG, 0))
    for (x, y) in ((13, 18), (46, 16), (27, 6), (40, 40), (16, 40)):
        cv.pair(x, y, W(DG, 1), horiz=(x % 2 == 0))
    cv.pair(cx + 2, cy - 5, W(DG, 2))
    fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return {"any": fr}


# ============================================================ 활 1~2. 화살 텍스처
BW = "bow"


def bow_arrow_frames():
    """12×6 우향, 피벗 (6,3). 코어 자루(X1 위 + W2 그늘) + 청백 꼬리(W1/W2 깃) + 촉 W3/X0."""
    cv = Canvas(12, 6)
    L = {"a": W(BW, 1), "b": W(BW, 2), "c": X1, "T": W(BW, 3), "t": X0, "e": W(BW, 0)}
    cv.blit([
        "............",
        ".aa.........",
        "abbcccccccTt",
        "abbbbbbbbbT.",
        ".aa.........",
        "............",
    ], 0, 0, L)
    return {"any": [cv]}


def bow_arrow_aimed_frames():
    """16×8 우향, 피벗 (8,4). 3폭 자루(W3 / X1 코어 / W2) + W0 밑 가장자리 + 긴 촉(W3→X0) + 깃 2겹."""
    cv = Canvas(16, 8)
    L = {"a": W(BW, 1), "b": W(BW, 2), "c": X1, "T": W(BW, 3), "t": X0, "e": W(BW, 0)}
    cv.blit([
        "................",
        "..aa............",
        ".abbTTTTTTTTT...",
        "abbcccccccccTtt.",
        ".abbbbbbbbbbT...",
        "..aa.eeeeeee....",
        "................",
        "................",
    ], 0, 0, L)
    return {"any": [cv]}


def heavyarrow_frames():
    """16×8 우향, 피벗 (8,4). 중시: 두꺼운 자루(W0 테두리·W3·X1·W2·W0) + 큰 미늘촉(W3 + X0) + 깃 2겹(W1/W2) + 번개 불티."""
    cv = Canvas(16, 8)
    L = {"a": W(BW, 1), "b": W(BW, 2), "c": X1, "T": W(BW, 3), "t": X0, "e": W(BW, 0)}
    cv.blit([
        ".aa....eeeee....",
        ".ab.eeeTTTTTTe..",
        "aabbTTTTTTTTTTT.",
        "abbccccccccccTtt",
        "aabbbbbbbbbbbbT.",
        ".ab.eeeeeeeeeee.",
        ".aa.............",
        "................",
    ], 0, 0, L)
    return {"any": [cv]}


# ============================================================ 활 3·5. 관통 / 섬광 꼬리 32×8 루프
def pierce_frames():
    """32×8 any 4f 루프, 피벗 (30,4) = 화살 중심. 화살 뒤 빛줄: 코어 X1(머리 쪽 9px) → W3 → W2 → W1, 위아래 W2/W1 줄, 머리 쪽 W0 가장자리. 끝 흔들림."""
    fr = []
    for f in range(4):
        cv = Canvas(32, 8)
        L = [22, 24, 23, 21][f]
        h = 29
        cv.line(h, 4, h - L, 4, W(BW, 1)); cv.line(h, 4, h - L + 7, 4, W(BW, 2)); cv.line(h, 4, h - L + 13, 4, W(BW, 3)); cv.line(h, 4, h - 8, 4, X1)
        cv.line(h - 1, 3, h - (L - 6), 3, W(BW, 1)); cv.line(h - 1, 5, h - (L - 6), 5, W(BW, 1))
        cv.line(h - 1, 3, h - 10, 3, W(BW, 2)); cv.line(h - 1, 5, h - 10, 5, W(BW, 2))
        cv.line(h - 2, 2, h - 9, 2, W(BW, 0)); cv.line(h - 2, 6, h - 9, 6, W(BW, 0))
        ty = 3 if f % 2 == 0 else 5
        cv.line(h - L - 1, ty, h - L + 1, ty, W(BW, 1))
        cv.px(h - L - 2, 4, W(BW, 0)); cv.px(h - L - 1, 4, W(BW, 0))
        cv.despeckle8()
        fr.append(cv)
    return {"any": fr}


def flash_frames():
    """32×8 any 4f 루프, 피벗 (30,4). 섬광: 관통보다 밝고 길다 — 코어 X0 가 거의 전체, W3 띠, 번개 토막 2(W2)이 꼬리를 뛰어다닌다."""
    fr = []
    for f in range(4):
        cv = Canvas(32, 8)
        L = [27, 29, 28, 26][f]
        h = 29
        cv.line(h, 4, h - L, 4, W(BW, 2)); cv.line(h, 4, h - L + 6, 4, X1); cv.line(h, 4, h - L + 12, 4, X0)
        cv.line(h - 1, 3, h - (L - 4), 3, W(BW, 2)); cv.line(h - 1, 5, h - (L - 4), 5, W(BW, 2))
        cv.line(h - 1, 3, h - 14, 3, W(BW, 3)); cv.line(h - 1, 5, h - 14, 5, W(BW, 3))
        cv.line(h - 2, 2, h - (L - 12), 2, W(BW, 1)); cv.line(h - 2, 6, h - (L - 12), 6, W(BW, 1))
        cv.line(h - 3, 1, h - 11, 1, W(BW, 0)); cv.line(h - 3, 7, h - 11, 7, W(BW, 0))
        # 번개 토막: 꼬리 가운데를 위아래로 뛰는 지그재그 (프레임마다 뒤로 3px)
        for k in range(2):
            sx = h - 8 - ((f * 3 + k * 9) % 18)
            pts = [(sx, 2), (sx - 2, 5), (sx - 4, 1), (sx - 6, 6)]
            cv.bolt(pts, [(0, W(BW, 3) if k == 0 else X1)])
        ty = 3 if f % 2 == 0 else 5
        cv.line(h - L - 1, ty, h - L + 1, ty, W(BW, 1))
        cv.px(h - L - 2, 4, W(BW, 0)); cv.px(h - L - 1, 4, W(BW, 1))
        cv.despeckle8()
        fr.append(cv)
    return {"any": fr}


# ============================================================ 활 4·8. 산탄 / 폭우 발사 섬광 32 · 4f
def burst_rays_frames(angles, lengths, seed0):
    """발사점 (4,16) 에서 뻗는 번개 광선: f0 짧은 3겹 → f1 전체 3겹(W0·W2·X0) → f2 바깥 토막 W2 점선 → f3 조각 W1/W0."""
    ox, oy = 4, 16
    fr = []
    for f in range(4):
        cv = Canvas(32, 32)
        for i, (a, L) in enumerate(zip(angles, lengths)):
            ang = math.radians(a)
            if f == 0:
                cv.bolt(zigzag(ox + 2 * math.cos(ang), oy + 2 * math.sin(ang), ox + L * 0.4 * math.cos(ang), oy + L * 0.4 * math.sin(ang), 2, 1.0, seed0 + i),
                        [(1, W(BW, 0)), (0, W(BW, 3))])
            elif f == 1:
                cv.bolt(zigzag(ox + 2 * math.cos(ang), oy + 2 * math.sin(ang), ox + L * math.cos(ang), oy + L * math.sin(ang), 4, 1.6, seed0 + i),
                        [(1, W(BW, 0)), (0, W(BW, 2))])
            elif f == 2:
                tmp = Canvas(32, 32)
                tmp.bolt(zigzag(ox + L * 0.35 * math.cos(ang), oy + L * 0.35 * math.sin(ang), ox + (L + 2) * math.cos(ang), oy + (L + 2) * math.sin(ang), 3, 1.6, seed0 + 10 + i),
                         [(0, W(BW, 2))])
                tmp.dash_pattern(mod=4, keep=(0, 1, 2), seed=i)
                cv.merge(tmp)
                cv.pair(ox + (L + 2) * math.cos(ang), oy + (L + 2) * math.sin(ang), W(BW, 3), horiz=abs(math.cos(ang)) > 0.5)
            else:
                cv.pair(ox + (L * 0.7) * math.cos(ang), oy + (L * 0.7) * math.sin(ang), W(BW, 1), horiz=(i % 2 == 0))
                cv.pair(ox + (L + 3) * math.cos(ang), oy + (L + 3) * math.sin(ang), W(BW, 0), horiz=(i % 2 == 1))
        if f == 1:
            for i, (a, L) in enumerate(zip(angles, lengths)):
                ang = math.radians(a)
                cv.bolt(zigzag(ox + 2 * math.cos(ang), oy + 2 * math.sin(ang), ox + L * math.cos(ang), oy + L * math.sin(ang), 4, 1.6, seed0 + i),
                        [(0, X0 if i % 2 == 0 else X1)])
        if f == 0:
            cv.disc(ox, oy, 2.2, X0); cv.ring(ox, oy, 3.5, W(BW, 3), thick=1.2)
        elif f == 1:
            cv.disc(ox, oy, 1.6, X1); cv.ring(ox, oy, 3.0, W(BW, 2), thick=1.0)
            cv.pair(ox - 1, oy - 5, C(27), horiz=False); cv.pair(ox - 1, oy + 4, C(27), horiz=False)
        elif f == 2:
            cv.ring(ox, oy, 2.5, W(BW, 1), thick=1.0, dash=(60, 30))
            cv.pair(ox + 1, oy - 1, C(24))
        cv.despeckle8()
        fr.append(cv)
    return {"any": fr}


def scatter_frames():
    return burst_rays_frames((-24, 0, 24), (20, 24, 20), 40)


def rain_frames():
    return burst_rays_frames((-50, -25, 0, 25, 50), (19, 23, 26, 23, 19), 50)


# ============================================================ 활 7. 중시 적중 '번개 낙하' 64 · 5f (콘셉트 승격)
def heavyarrow_hit_frames():
    """64×64 any, 피벗 (32,44) = 적중점. 하늘에서 떨어지는 번개 3겹 + 가지 2 → 적중 십자 X0 + 링 r8 + 바깥 가지 번개 3 → 점선 잔광 + 링 r14 → 꼬리 r18."""
    hx_, hy_ = 32, 44
    fr = []
    main = [(2, W(BW, 0)), (1, W(BW, 2)), (0, X0)]
    thin = [(1, W(BW, 1)), (0, W(BW, 3))]
    cv = Canvas(64, 64)   # f0 예고 가는 선
    cv.bolt(zigzag(27, 0, hx_, hy_ - 2, 6, 2.4, 31), [(0, W(BW, 3))])
    cv.pair(hx_ - 1, hy_, X1)
    fr.append(cv)
    cv = Canvas(64, 64)   # f1 번개 본체 + 가지 + 적중 십자
    cv.bolt(zigzag(27, 0, hx_, hy_ - 1, 7, 3.4, 32), main)
    cv.bolt(zigzag(30, 14, 44, 24, 3, 1.8, 33), thin)
    cv.bolt(zigzag(29, 26, 16, 34, 3, 1.8, 34), thin)
    for a in (0, 90, 180, 270):
        cv.ray(hx_, hy_, a, 0, 8, X0)
    for a in (45, 135, 225, 315):
        cv.ray(hx_, hy_, a, 2, 5, C(27))
    fr.append(cv)
    cv = Canvas(64, 64)   # f2 번개 코어만 + 링 r8 + 바깥 가지 번개 3
    cv.bolt(zigzag(27, 0, hx_, hy_ - 1, 7, 3.4, 32), [(1, W(BW, 1)), (0, W(BW, 3))])
    cv.ring(hx_, hy_, 8, W(BW, 0), thick=2.8)
    cv.ring(hx_, hy_, 8, W(BW, 3), thick=1.4)
    cv.ring(hx_, hy_, 8, X0, thick=1.0, dash=(30, 60))
    for i, a in enumerate((20, 160, 260)):
        ang = math.radians(a)
        cv.bolt(zigzag(hx_ + 8 * math.cos(ang), hy_ + 8 * math.sin(ang), hx_ + 19 * math.cos(ang), hy_ + 19 * math.sin(ang), 3, 1.8, 35 + i), [(0, W(BW, 2))])
    cv.disc(hx_, hy_, 1.8, X1)
    fr.append(cv)
    cv = Canvas(64, 64)   # f3 번개 점선 잔광 + 링 r14 점선 + 불티
    tmp = Canvas(64, 64)
    tmp.bolt(zigzag(27, 0, hx_, hy_ - 1, 7, 3.4, 32), [(0, W(BW, 2))])
    tmp.dash_pattern(mod=3, keep=(0, 1), seed=4)
    cv.merge(tmp)
    cv.ring(hx_, hy_, 14, W(BW, 0), thick=2.4)
    cv.ring(hx_, hy_, 14, W(BW, 2), thick=1.0, dash=(25, 20))
    for k, a in enumerate((45, 135, 225, 315)):
        ang = math.radians(a)
        cv.pair(hx_ + 16 * math.cos(ang), hy_ + 16 * math.sin(ang), C(26) if k % 2 else W(BW, 3), horiz=(k % 2 == 0))
    fr.append(cv)
    cv = Canvas(64, 64)   # f4 꼬리
    cv.ring(hx_, hy_, 18, W(BW, 1), thick=1.2, dash=(10, 16), phase=5)
    cv.pair(hx_ - 2, hy_ - 18, W(BW, 2), horiz=False)
    cv.pair(hx_ + 12, hy_ + 4, W(BW, 1))
    cv.pair(hx_ - 14, hy_ + 2, C(22))
    fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return {"any": fr}


# ============================================================ 활 9. 추적 24 · 4f 루프
def seek_frames():
    """24×24 any 4f 루프, 피벗 (20,12) = 화살 중심. 유도 소용돌이: 꼬인 두 가닥(W3/W2 → 뒤로 W1/W0)이 뒤로 흐르고(4f = 2π) 교차점에 X0, 머리 X1."""
    fr = []
    for f in range(4):
        cv = Canvas(24, 24)
        ph = f * math.pi / 2
        strands = {}
        for strand, sgn in enumerate((1, -1)):
            pts = []
            for x in range(19, 1, -1):
                s = 19 - x
                amp = 1.4 + s * 0.32
                y = 12 + sgn * amp * math.sin(2 * math.pi * s / 9.0 + ph)
                pts.append((x, int(round(y))))
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                s = 19 - x0
                if strand == 0:
                    col = W(BW, 3) if s < 6 else (W(BW, 2) if s < 12 else W(BW, 1))
                else:
                    col = W(BW, 2) if s < 6 else (W(BW, 1) if s < 12 else W(BW, 0))
                cv.line(x0, y0, x1, y1, col)
            strands[strand] = pts
        for (x0, y0), (x1, y1) in zip(strands[0], strands[1]):
            if y0 == y1 and 4 < x0 < 19:
                cv.px(x0, y0, X0)
        cv.px(19, 12, X1); cv.px(18, 12, X1)
        cv.despeckle8()
        fr.append(cv)
    return {"any": fr}


# ============================================================ 보조 1. 패링 섬광 48 · 5f (보조색 없음)
def parry_flash_frames():
    """48×48 any, 피벗 (24,24) = 접점. 시간 정지 섬광: f0 전체 X0 십자 + X1 코어 → 깨끗한 동심 고리 2(층 24/22, 4px 간격) + 광선 → 점선 → 조각."""
    cx, cy = 24, 24
    fr = []
    cv = Canvas(48, 48)   # f0 전체 십자 섬광 (히트스톱 + 화면 오버레이 X1 0.25)
    for a in (0, 90, 180, 270):
        cv.ray(cx, cy, a, 0, 22, X0)
        cv.ray(cx, cy, a, 0, 9, X1)
    for a in (45, 135, 225, 315):
        cv.ray(cx, cy, a, 2, 9, C(27))
    cv.disc(cx, cy, 2.6, X1)
    cv.ring(cx, cy, 5.5, C(25), thick=1.2)
    fr.append(cv)
    cv = Canvas(48, 48)   # f1 동심 고리 2 + 짧은 X0 광선
    cv.disc(cx, cy, 1.6, X1)
    cv.ring(cx, cy, 6.5, C(24), thick=1.4)
    cv.ring(cx, cy, 10.5, C(22), thick=1.2)
    for a in (0, 90, 180, 270):
        cv.ray(cx, cy, a, 12, 17, X0)
    for a in (45, 135, 225, 315):
        cv.ray(cx, cy, a, 12, 14, C(25))
    fr.append(cv)
    cv = Canvas(48, 48)   # f2 고리 확장 + 안쪽 점선 + 네 귀 글린트
    cv.ring(cx, cy, 11.5, C(24), thick=1.2)
    cv.ring(cx, cy, 15.5, C(22), thick=1.0)
    cv.ring(cx, cy, 7.0, C(21), thick=1.0, dash=(20, 20), phase=5)
    for k, a in enumerate((0, 90, 180, 270)):
        spark_at(cv, cx, cy, a, 18.5, C(27), horiz=(k % 2 == 1))
    cv.pair(cx - 1, cy, C(25))
    fr.append(cv)
    cv = Canvas(48, 48)   # f3 점선 고리
    cv.ring(cx, cy, 17.5, C(21), thick=1.0, dash=(14, 12), phase=3)
    cv.ring(cx, cy, 13.0, C(19), thick=1.0, dash=(9, 21), phase=12)
    cv.pair(cx - 1, cy - 1, C(22))
    fr.append(cv)
    cv = Canvas(48, 48)   # f4 조각
    cv.ring(cx, cy, 20.0, C(18), thick=1.0, dash=(8, 28), phase=0)
    for k, a in enumerate((30, 150, 270)):
        spark_at(cv, cx, cy, a, 15, C(19), horiz=(k % 2 == 0))
    fr.append(cv)
    for cv in fr:
        cv.despeckle8()
    return {"any": fr}


# ============================================================ 보조 2. 가드 충격파 64×32 · 4f (대검 보조색)
def guard_wave_frames():
    """64×32 4방향, 피벗 (32,16) = 발, 바닥 깊이. 발 앞 반타원(세로 0.5) 링 3겹(W0·W2·X1 1px 점선) r10→18→25→29 + 가장자리 재 G06/G09 + 짧은 균열 2."""
    GSW = "greatsword"
    out = {}
    cx, cy = 32, 16
    ky = 0.5
    for d in DIRS:
        fa = FACE[d]
        fr = []
        for f in range(4):
            cv = Canvas(64, 32)
            r = [10, 18, 25, 29][f]
            if f < 3:
                cv.ring(cx, cy, r, W(GSW, 0), thick=[3.4, 3.2, 2.6][f], a0=fa - 78, a1=fa + 78, ky=ky)
                cv.ring(cx, cy, r, W(GSW, 2) if f < 2 else W(GSW, 1), thick=[1.8, 1.6, 1.2][f], a0=fa - 70, a1=fa + 70, ky=ky)
                if f == 0:
                    cv.ring(cx, cy, r, X1, thick=1.0, a0=fa - 40, a1=fa + 40, ky=ky)
                elif f == 1:
                    cv.ring(cx, cy, r, X1, thick=1.0, a0=fa - 60, a1=fa + 60, ky=ky, dash=(18, 10), phase=fa)
                else:
                    cv.ring(cx, cy, r, W(GSW, 3), thick=1.0, a0=fa - 50, a1=fa + 50, ky=ky, dash=(12, 14), phase=fa + 4)
            else:
                cv.ring(cx, cy, r, W(GSW, 0), thick=1.6, a0=fa - 75, a1=fa + 75, ky=ky, dash=(14, 10), phase=fa)
                cv.ring(cx, cy, r - 1, W(GSW, 1), thick=1.0, a0=fa - 60, a1=fa + 60, ky=ky, dash=(10, 16), phase=fa + 6)
            # 균열 2 (발 앞, f1~f2 용암 W2 → f3 W0 점)
            if 1 <= f <= 3:
                for i, da in enumerate((-22, 24)):
                    ang = math.radians(fa + da)
                    L = [0, 9, 13, 13][f]
                    pts = zigzag(cx + 3 * math.cos(ang), cy + 3 * math.sin(ang) * ky, cx + L * math.cos(ang), cy + L * math.sin(ang) * ky, 3, 1.6, 90 + i)
                    tmp = Canvas(64, 32)
                    tmp.bolt(pts, [(0, W(GSW, 2) if f < 3 else W(GSW, 0))])
                    if f == 3:
                        tmp.dash_pattern(mod=3, keep=(0, 1), seed=i)
                    cv.merge(tmp)
            # 재 2px 쌍 (G06/G09) 파도 바깥 가장자리
            for k, da in enumerate((-50, 0, 50)):
                if f == 0 and k != 1:
                    continue
                a = math.radians(fa + da)
                rr = r + 2 + (f % 2)
                cv.pair(cx + rr * math.cos(a), cy + rr * math.sin(a) * ky, G(9) if f < 2 else G(6), horiz=(d in ("up", "down")) == (k == 1))
            cv.despeckle8()
            fr.append(cv)
        out[d] = fr
    return out


# ============================================================ 보조 3. 그림자 걸음 출발 잔상 16×24 · 3f (단검 보조색)
def shadowstep_ghost_frames():
    """16×24 4방향, 피벗 (8,23), 바닥 깊이·고정. 출발점 실루엣 W0 단색(우·하 림 W1) → 세로 줄무늬 W1 → 조각. 발밑 W0 웅덩이가 함께 수축. 암살 분신과 같은 어휘."""
    out = {}
    for d in DIRS:
        m = PIDLE[d]
        fr = []
        for f in range(3):
            cv = Canvas(16, 24)
            pr = [7, 5, 3][f]
            cv.disc(8, 22, pr, W(DG, 0), ky=0.3)
            if f == 0:
                cv.mask_paste(m, 0, 0, lambda x, y, rgb: W(DG, 0))
                cv.outline_of(m, 0, 0, W(DG, 1))
            elif f == 1:
                tmp = Canvas(16, 24)
                tmp.mask_paste(m, 0, 0, solid_fn(m, W(DG, 1), W(DG, 0)))
                for y in range(24):
                    for x in range(16):
                        if tmp.p[x, y][3] and (x % 3 != 1):
                            cv.px(x, y, tmp.p[x, y])
            else:
                tmp = Canvas(16, 24)
                tmp.mask_paste(m, 0, 1, lambda x, y, rgb: W(DG, 1) if (x + y) % 3 == 0 else None)
                tmp.outline_of(m, 0, 1, W(DG, 0))
                tmp.dash_pattern(mod=3, keep=(0, 1), seed=1)
                cv.merge(tmp)
                cv.line(5, 22, 10, 22, W(DG, 0))
            cv.despeckle8()
            fr.append(cv)
        out[d] = fr
    return out


# ============================================================ 보조 4. 조준 차지 32 · 6f 진행도 (활 보조색)
def aim_charge_frames():
    """32×32 any, 피벗 (16,16) = 몸 중심. r10 고리를 W1 점선으로 두고 진행도만큼 W3(가장자리 W0)로 채움, 머리 X1. 완료 f5 = 코어 X0 고리 + 네 귀 가지 번개."""
    cx, cy = 16, 16
    fr = []
    for f in range(6):
        cv = Canvas(32, 32)
        if f < 5:
            cv.ring(cx, cy, 10, W(BW, 1), 1.0, dash=(10, 20))
            for a in (0, 90, 180, 270):
                cv.ray(cx, cy, a, 12, 13, W(BW, 1))
            if f > 0:
                cv.ring(cx, cy, 10, W(BW, 0), 2.8, a0=-90, a1=-90 + 72 * f)
                cv.ring(cx, cy, 10, W(BW, 3), 1.4, a0=-90, a1=-90 + 72 * f)
                a = math.radians(-90 + 72 * f)
                cv.pair(cx + 10 * math.cos(a), cy + 10 * math.sin(a), X1, horiz=abs(math.cos(a)) < 0.5)
            cv.px(cx, cy - 10, W(BW, 3)); cv.px(cx, cy - 11, W(BW, 3))
        else:
            cv.ring(cx, cy, 10, W(BW, 0), 3.0)
            cv.ring(cx, cy, 10, W(BW, 3), 1.6)
            cv.ring(cx, cy, 10, X0, 1.0, dash=(40, 5))
            cv.ring(cx, cy, 13, W(BW, 2), 1.0, dash=(15, 15), phase=7)
            for i, a in enumerate((45, 135, 225, 315)):
                ang = math.radians(a)
                cv.bolt(zigzag(cx + 11 * math.cos(ang), cy + 11 * math.sin(ang), cx + 15.5 * math.cos(ang), cy + 15.5 * math.sin(ang), 2, 1.2, 60 + i),
                        [(0, W(BW, 3))])
                cv.px(cx + 15 * math.cos(ang), cy + 15 * math.sin(ang), X1)
            cv.disc(cx, cy, 1.4, X0)
        cv.despeckle8()
        fr.append(cv)
    return {"any": fr}


def aim_line_frames():
    """8×2 any, tile+rotate, 피벗 (0,1). 코어 점선(4 on / 4 off): f0 차지 중 = X1 코어 + W2 밑줄, f1 완료 = X0 코어 + W3 밑줄."""
    a = Canvas(8, 2)
    a.line(0, 0, 3, 0, X1); a.line(0, 1, 3, 1, W(BW, 2))
    b = Canvas(8, 2)
    b.line(0, 0, 3, 0, X0); b.line(0, 1, 3, 1, W(BW, 3))
    return {"any": [a, b]}


# ============================================================ 보조 5·6. 대쉬 먼지 · 대쉬 잔상 (무채, evolution_fx 와 동일 — 결정: 유지)
def gray_level(rgb):
    lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return G(2) if lum < 60 else (G(3) if lum < 140 else G(4))


def dash_dust_frames():
    out = {}
    D, M, L = G(6), G(9), G(12)
    for d in DIRS:
        bx, by = -DVEC[d][0], -DVEC[d][1]
        fr = []
        for f in range(3):
            cv = Canvas(16, 8)
            px_, py_ = 8, 6
            if d in ("left", "right"):
                cv.disc(px_ + bx * (2 + f * 2), py_ - 1 - f, 2.6 - f * 0.4, D, ky=0.75)
                cv.disc(px_ + bx * (5 + f * 2), py_ - 2 - f, 1.8 - f * 0.3, D, ky=0.75)
                cv.disc(px_ + bx * (2 + f * 2) - bx, py_ - 2 - f, 1.4 - f * 0.2, M, ky=0.75)
                cv.pair(px_ + bx * (6 + f * 2), py_ - 3 - f, L, horiz=True)
                if f < 2:
                    cv.pair(px_ + bx * (1 + f), py_, M, horiz=True)
            else:
                for sx in (-1, 1):
                    cv.disc(px_ + sx * (3 + f * 2), py_ + by * (1 + f), 2.4 - f * 0.4, D, ky=0.75)
                    cv.disc(px_ + sx * (2 + f * 2), py_ + by * (1 + f) - 1, 1.4 - f * 0.2, M, ky=0.75)
                    cv.pair(px_ + sx * (5 + f * 2) - (1 if sx < 0 else 0), py_ + by * (2 + f), L)
                if f == 0:
                    cv.pair(px_ - 1, py_, M)
            cv.despeckle8()
            fr.append(cv)
        out[d] = fr
    return out


def dash_trail_frames():
    out = {}
    for d in DIRS:
        m = PDASH[d]
        horiz = d in ("left", "right")
        fr = []
        for f in range(3):
            cv = Canvas(16, 24)
            if f == 0:
                cv.mask_paste(m, 0, 0, lambda x, y, rgb: (G(4) if gray_level(rgb) == G(4) else G(3)) if ((y if horiz else x) % 2 == 0) else G(2))
            elif f == 1:
                cv.mask_paste(m, 0, 0, lambda x, y, rgb: G(3) if ((y if horiz else x) % 2 == 0) else (G(2) if (x + y) % 3 == 0 else None))
            else:
                cv.mask_paste(m, 0, 0, lambda x, y, rgb: G(2) if ((y if horiz else x) % 3 == 0) else None)
                cv.dash_pattern(mod=5, keep=(0, 1, 2), seed=1)
            cv.despeckle8()
            fr.append(cv)
        out[d] = fr
    return out


# ============================================================ 미리보기
def label(d, xy, text, col=(230, 230, 230), bold=False):
    d.text(xy, text, fill=col, font=FONTB if bold else FONT)


def scaled(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


FLOOR_BG = (0x21, 0x22, 0x24)


def dir_block(fx, name, k=3, rows=None):
    fbd, dirs, w, h, durs, pivot = fx[name][:6]
    rows = rows or (["right", "down"] if "right" in dirs else dirs)
    n = len(durs)
    pad = 2
    W_ = 70 + (w * k + pad) * n
    H_ = 18 + (h * k + pad) * len(rows)
    im = Image.new("RGB", (W_, H_), (24, 24, 28))
    d = ImageDraw.Draw(im)
    label(d, (4, 2), "%s %dx%d %s pivot(%d,%d) %s" % (name, w, h, "/".join(dirs), pivot[0], pivot[1], durs), bold=True)
    for r, dr in enumerate(rows):
        y = 18 + r * (h * k + pad)
        label(d, (4, y + 4), dr)
        for c in range(n):
            x = 70 + c * (w * k + pad)
            cell = Image.new("RGBA", (w, h), FLOOR_BG + (255,))
            cell.alpha_composite(fbd[dr][c].im)
            im.paste(scaled(cell, k), (x, y))
    return im


def strip_1x(fx, names):
    cells = []
    for name in names:
        fbd, dirs, w, h, durs, pivot = fx[name][:6]
        dr = "right" if "right" in dirs else "any"
        for cv in fbd[dr]:
            cell = Image.new("RGBA", (max(w, 8), max(h, 8)), FLOOR_BG + (255,))
            cell.alpha_composite(cv.im)
            cells.append(cell)
        cells.append(None)
    Wt = sum((c.width + 2) if c else 6 for c in cells) + 2
    Ht = max(c.height for c in cells if c) + 2
    im = Image.new("RGB", (Wt, Ht), (24, 24, 28))
    x = 2
    for c in cells:
        if c is None:
            x += 6
            continue
        im.paste(c, (x, Ht - c.height - 1))
        x += c.width + 2
    return im


def stack(blocks, cols=2, bgc=(24, 24, 28)):
    colw = [0] * cols
    rows = [blocks[i:i + cols] for i in range(0, len(blocks), cols)]
    for row in rows:
        for j, b in enumerate(row):
            colw[j] = max(colw[j], b.width)
    H_ = sum(max(b.height for b in row) + 8 for row in rows) + 8
    W_ = sum(colw) + 8 * (cols + 1)
    im = Image.new("RGB", (W_, H_), bgc)
    y = 8
    for row in rows:
        x = 8
        for j, b in enumerate(row):
            im.paste(b, (x, y))
            x += colw[j] + 8
        y += max(b.height for b in row) + 8
    return im


def preview_b(fx):
    order = list(fx.keys())
    blocks = []
    for n in order:
        w = fx[n][2]
        k = 2 if w >= 96 else (3 if w >= 24 else 4)
        blocks.append(dir_block(fx, n, k=k))
    top = stack(blocks, cols=1)
    groups = [("dagger", ["dagger_slash", "twin", "gale", "bleed", "afterimage", "assassin"]), ("dagger dance", ["dance"]),
              ("bow", ["bow_arrow", "bow_arrow_aimed", "heavyarrow", "pierce", "flash", "scatter", "rain", "heavyarrow_hit", "seek"]),
              ("secondary", ["parry_flash", "guard_wave", "shadowstep_ghost", "aim_charge", "aim_line", "dash_dust", "dash_trail"])]
    strips = []
    for t, names in groups:
        s = strip_1x(fx, names)
        hdr = Image.new("RGB", (s.width, 16), (24, 24, 28))
        label(ImageDraw.Draw(hdr), (2, 2), "1x (real size, floor G02): " + t + " — " + " / ".join(names), bold=True)
        strips.append(hdr); strips.append(s)
    Wt = max([top.width] + [s.width for s in strips])
    Ht = top.height + sum(s.height + 4 for s in strips) + 8
    out = Image.new("RGB", (Wt, Ht), (24, 24, 28))
    out.paste(top, (0, 0))
    y = top.height
    for s in strips:
        out.paste(s, (8, y))
        y += s.height + 4
    out.save(os.path.join(HERE, "preview_b.png"))


def preview_b_fight(fx):
    """1배 목업: stage1 바닥 방 + 주인공 attack f1(right) + 단검 오버레이 + 난무 f3 + 징집병 hurt + 출혈 + 사수 + 중시 번개 f1 + 결사병 + 패링 링 f1."""
    tiles = Image.open(os.path.join(ROOT, "assets", "tiles", "stage1.png")).convert("RGBA")
    tile = [tiles.crop((i * 16, 0, i * 16 + 16, 16)) for i in range(4)]
    wall = tiles.crop((5 * 16, 0, 5 * 16 + 16, 16))
    cols_, rows_ = 16, 9
    room = Image.new("RGBA", (cols_ * 16, rows_ * 16), (0, 0, 0, 255))
    for ty in range(rows_):
        for tx in range(cols_):
            room.alpha_composite(wall if ty == 0 else tile[(tx * 7 + ty * 13 + (tx * ty) % 5) % 4], (tx * 16, ty * 16))
    scene = room.copy()

    def put(sprite, x, y):
        scene.alpha_composite(sprite, (int(x), int(y)))

    def shadow(x, y, w):
        cv = Canvas(w + 2, 4)
        cv.disc(w / 2 + 1, 2, w / 2, G(1), ky=0.5)
        put(cv.im, x - 1, y - 2)

    # 주인공 attack f1 right + 단검 오버레이 + 난무 f3 (피벗 (48,58) = 발 (8,23)) + 질풍 f1 아래
    px_, py_ = 60, 80
    player = sprite_frame(os.path.join(SPR, "player", "player_attack.png"), 16, 24, 1, 3)
    dagger = sprite_frame(os.path.join(SPR, "weapons", "dagger_attack.png"), 48, 48, 1, 3)
    put(fx["gale"][0]["right"][1].im, px_ + 8 - 32, py_ + 23 - 42)
    shadow(px_ + 2, py_ + 24, 12)
    put(player, px_, py_)
    put(dagger, px_ + 8 - 24, py_ + 23 - 39)
    put(fx["dance"][0]["right"][3].im, px_ + 8 - 48, py_ + 23 - 58)
    # 징집병 hurt (left 행) + 출혈 f0 — 난무 머리 쪽
    dummy = sprite_frame(os.path.join(SPR, "enemies", "dummy_hurt.png"), 16, 24, 0, 2)
    dx_, dy_ = px_ + 34, py_ - 4
    shadow(dx_ + 2, dy_ + 24, 12)
    put(dummy, dx_, dy_)
    put(fx["bleed"][0]["any"][0].im, dx_ + 8 - 12, dy_ + 12 - 12)
    # 사수 + 중시 번개 f1 (피벗 (32,44) = 히트박스 중심)
    arch = sprite_frame(os.path.join(SPR, "enemies", "archer_hurt.png"), 16, 24, 0, 2)
    ax_, ay_ = 190, 40
    shadow(ax_ + 2, ay_ + 24, 12)
    put(arch, ax_, ay_)
    put(fx["heavyarrow_hit"][0]["any"][1].im, ax_ + 8 - 32, ay_ + 12 - 44)
    # 결사병(charger) attack + 패링 링 f1 — 접점 = 주인공 왼쪽 몸 중심 근처
    chg = sprite_frame(os.path.join(SPR, "enemies", "charger_attack.png"), 16, 24, 2, 3)
    cx_, cy_ = px_ - 26, py_ + 2
    shadow(cx_ + 2, cy_ + 24, 12)
    put(chg, cx_, cy_)
    put(fx["parry_flash"][0]["any"][1].im, px_ - 6 - 24, py_ + 12 - 24)
    # 잔상 f1 (대쉬 출발점, 바닥) — 아래쪽 빈 자리에 크기 비교용
    put(fx["afterimage"][0]["right"][1].im, 150 - 32, 118 - 42)
    # 조준 차지 f3 + 조준선 (아래 오른쪽: 활 상태의 주인공 idle)
    pid = PIDLE["right"]
    bx_, by_ = 214, 104
    shadow(bx_ + 2, by_ + 24, 12)
    put(pid, bx_, by_)
    for i in range(3):
        put(fx["aim_line"][0]["any"][0].im, bx_ + 8 + 14 + i * 8, by_ + 12 - 1)
    put(fx["aim_charge"][0]["any"][3].im, bx_ + 8 - 16, by_ + 12 - 16)
    flash = scene.copy()
    ov = Image.new("RGBA", scene.size, X1[:3] + (64,))
    flash.alpha_composite(ov)
    out = Image.new("RGB", (scene.width * 3 + 24 + scene.width + 16, scene.height * 3 + 60), (24, 24, 28))
    d = ImageDraw.Draw(out)
    label(d, (8, 4), "mock fight 1x (left: real size, right: x3) — dance f3 + gale f1 on player, dummy + bleed f0, archer + heavyarrow_hit f1, charger + parry_flash f1, afterimage f1, aim_charge f3 + aim_line", bold=True)
    out.paste(scene.convert("RGB"), (8, 24))
    label(d, (8, 28 + scene.height), "with parry overlay (X1 @ alpha 0.25, 40ms)")
    out.paste(flash.convert("RGB"), (8, 44 + scene.height))
    out.paste(scaled(scene.convert("RGB"), 3), (scene.width + 24, 24))
    out.save(os.path.join(HERE, "preview_b_fight.png"))


# ============================================================ main
def main():
    fx = {}
    # name: (frames_by_dir, dirs, w, h, durations, pivot, loop, extra, palette_note)
    DGS, BWS = "fx.weapons.dagger", "fx.weapons.bow"
    trail = lambda a, ms, ff: {"color": "fx.weapons.dagger.ramp[1]", "alpha": a, "ms": ms, "fromFrame": ff, "widthRatio": 0.6}
    fx["dagger_slash"] = (dagger_slash_frames(), DIRS, 48, 48, [40, 50, 60, 70, 90], (24, 34), False, dict(
        anchor="player_pivot", spawn="attack_frame2", depth="above", weapon="dagger", secondary=DGS,
        trail=trail(0.6, 120, 2), tailFrames=1,
        spawnNote="f0(40ms) = 예비 코어 점선. 시스템이 spawn 오프셋(attack_frame2 - 40ms)을 지원하면 유지, 아니면 f0 를 건너뛰고 f1 부터 재생(결정 43: f0 는 지원 시 유지).",
        note="단검 기본 베기: 짧고 빠른 호(140°, r11) 2겹 = 본 띠(W0·W1·W2·W3 + 1px 코어 X1/X0) + 바깥 W0 '그림자 잔상' 1프레임 지연. f2 광선 2, f3 어두운 띠, f4 점선 꼬리(트레일 인계)."), PALETTE_NOTE)
    fx["twin"] = (twin_frames(), DIRS, 64, 64, [40, 40, 60, 80, 100, 120, 140], (32, 42), False, dict(
        anchor="player_pivot", spawn="attack_frame2", depth="above", weapon="dagger", secondary=DGS,
        trail=trail(0.7, 180, 2), tailFrames=3,
        flash={"color": "#fff4dc", "alpha": 0.18, "ms": 40, "atFrame": 1}, shake={"px": 2, "ms": 60},
        hitFrames=[1, 2], spawnNote="f0 예비(40ms) 는 spawn 오프셋 지원 시 유지, 아니면 f1 부터.",
        note="쌍격: 안쪽 호(r13) f1 백열 섬광 = 1타, 바깥 호(r19) f2 백열 섬광 = 2타(1프레임 늦음). 각 호에 W0 그림자 잔상. f2 광선 3, f4 어두운 띠 → f5 점선 → f6 꼬리."), PALETTE_NOTE)
    fx["gale"] = (gale_frames(), DIRS, 64, 64, [60, 70, 80, 90], (32, 42), True, dict(
        anchor="player_pivot", spawn="loop_move", depth="below", weapon="dagger", secondary=DGS, followsPlayer=True,
        note="질풍: 몸 뒤로 흐르는 보라 바람 줄 3(W3→W2→W1→W0, 밑줄 W0 그림자) + 가운데 줄 코어 토막 X1. 토막이 2px/프레임 뒤로 흘러 4프레임 = 1주기(이음새 없음). 이동·대쉬 중 루프, 플레이어 아래. 방향 = 이동 방향(바람은 반대쪽)."), PALETTE_NOTE)
    fx["dance"] = (dance_frames(), DIRS, 96, 96, [40, 40, 50, 70, 110, 140, 160], (48, 58), False, dict(
        anchor="player_pivot", spawn="attack_frame2", depth="above", weapon="dagger", secondary=DGS,
        trail=trail(0.7, 220, 2), tailFrames=3,
        flash={"color": "#fff4dc", "alpha": 0.22, "ms": 40, "atFrame": 1}, shake={"px": 3, "ms": 80},
        hitFrames=[1, 2, 3], spawnNote="f0 예비(40ms) 는 spawn 오프셋 지원 시 유지, 아니면 f1 부터. 1·2·3타 = f1/f2/f3 시작(0/40/90ms, f0 제외 기준).",
        note="난무(2차, twin 대체): 3중 베기 군집 — r14 정방향 → r21 역방향 → r28 정방향 호가 1프레임씩 이어지며 각자 백열 섬광 + W0 그림자. f3 광선 4 + 네 귀 글린트, f4 식음, f5 점선 셋, f6 꼬리."), PALETTE_NOTE)
    fx["bleed"] = (bleed_frames(), ["any"], 24, 24, [125, 125, 125, 125], (12, 12), True, dict(
        anchor="hitbox_center", spawn="hit", depth="above", followsTarget=True, weapon="dagger", secondary=DGS,
        note="출혈: 핏방울 3줄(피 = 층 램프 17~19, 런타임 스왑) + 단검 그림자(W0 밑·W1 그늘) + 발밑 W0 웅덩이. 4f = 틱 500ms, f0 = 틱 글린트(X1). 출혈 소진 시 제거, 재적중 시 갱신. 24 캔버스(기존 16 ×1.5)."), PALETTE_NOTE)
    fx["afterimage"] = (afterimage_frames(), DIRS, 64, 64, [40, 60, 80, 100, 130], (32, 42), False, dict(
        anchor="player_pivot", spawn="dash_start", depth="below", followsPlayer=False, weapon="dagger", secondary=DGS,
        note="잔상(2차): 대쉬 출발점(고정)에 분신 군집 — 돌진 실루엣 W2 + 좌우(대쉬에 수직) 8→14px 로 벌어지는 분신 W1 → 세로 줄무늬 → 조각, 바닥 W0 웅덩이 수축 + f1 교차 베기 2줄(W3 + X0/X1 코어). 방향 = 대쉬 방향(실루엣은 player_dash f1). 경로가 길면 중간점에 하나 더."), PALETTE_NOTE)
    fx["assassin"] = (assassin_frames(), ["any"], 64, 64, [40, 50, 60, 80, 110], (32, 32), False, dict(
        anchor="hitbox_center", spawn="hit", depth="above", weapon="dagger", secondary=DGS,
        note="암살(콘셉트 승격, 64): 적중점 둘레 바닥 웅덩이(W0) + 그림자 분신 3(player idle 실루엣, W0→W1→W2 우·하 림)이 모여들고 교차 섬광 2줄(3겹 W0·W3·X0/X1) → 세로 줄무늬로 흩어짐 → 웅덩이 수축. 층 강조 27/25/24 는 불티만. crit_burst/hit_burst 와 겹쳐도 됨."), PALETTE_NOTE)
    # ---- 활
    proj = dict(anchor="projectile", rotate=True, drawnFacing="right", weapon="bow", secondary=BWS)
    fx["bow_arrow"] = (bow_arrow_frames(), ["any"], 12, 6, [0], (6, 3), False, dict(proj, fps=0,
        note="기본 화살 12×6(기존 8×8): 코어 자루(X1 위 + W2 그늘) + 청백 깃·꼬리(W1/W2) + 촉 W3→X0. 피벗 (6,3) = 화살 중심."), PALETTE_NOTE)
    fx["bow_arrow_aimed"] = (bow_arrow_aimed_frames(), ["any"], 16, 8, [0], (8, 4), False, dict(proj, fps=0,
        note="조준 사격 화살 16×8(기존 12×6): 3폭 자루(W3 / X1 코어 / W2) + W0 밑 가장자리 + 긴 촉(W3→X0 2px) + 깃 2겹. 피벗 (8,4)."), PALETTE_NOTE)
    fx["pierce"] = (pierce_frames(), ["any"], 32, 8, [60, 60, 60, 60], (30, 4), True, dict(proj, spawn="loop_move", depth="below",
        note="관통 꼬리 32×8(기존 16×8): 화살 뒤 빛줄 — 코어 X1(머리 9px) → W3 → W2 → W1, 위아래 W2/W1 줄, 머리 쪽 W0 가장자리, 끝 흔들림. 피벗 (30,4) = 화살 중심. 투사체라 시스템 트레일 없음."), PALETTE_NOTE)
    fx["scatter"] = (scatter_frames(), ["any"], 32, 32, [40, 50, 60, 70], (4, 16), False, dict(proj, spawn="shot",
        note="산탄 발사 섬광 32(기존 16): 발사점 (4,16) 에서 ±24° 3갈래 번개 광선(3겹 W0·W2·X0/X1) f0 짧게 → f1 전체 + 코어 → f2 바깥 토막 점선 → f3 조각. 발사 각도로 회전."), PALETTE_NOTE)
    fx["flash"] = (flash_frames(), ["any"], 32, 8, [50, 50, 50, 50], (30, 4), True, dict(proj, spawn="loop_move", depth="below",
        note="섬광 꼬리 32×8(기존 24×8, pierce 대체): 코어 X0/X1 거의 전체 + W3 띠 + W0 가장자리 + 꼬리를 뛰어다니는 번개 토막 2(W3/X1, 3px/프레임 뒤로). 피벗 (30,4)."), PALETTE_NOTE)
    fx["heavyarrow"] = (heavyarrow_frames(), ["any"], 16, 8, [0], (8, 4), False, dict(proj, fps=0, spawn="aimed_shot",
        note="중시 화살 16×8: 두꺼운 자루(W0 테두리·W3·X1 코어·W2) + 큰 미늘촉(W3 + X0 2px) + 깃 2겹(W1/W2). bow_arrow_aimed 대신. 피벗 (8,4)."), PALETTE_NOTE)
    fx["heavyarrow_hit"] = (heavyarrow_hit_frames(), ["any"], 64, 64, [40, 50, 60, 80, 110], (32, 44), False, dict(
        anchor="hitbox_center", spawn="hit", depth="above", weapon="bow", secondary=BWS,
        flash={"color": "#cdefff", "alpha": 0.14, "ms": 40, "atFrame": 1}, shake={"px": 2, "ms": 60},
        pivotNote="피벗 (32,44) = 적중점(히트박스 중심). 번개는 캔버스 위 가장자리에서 떨어진다 (any — 회전 없음).",
        note="중시 적중(콘셉트 승격, 64): f0 가는 예고선 → f1 번개 낙하 3겹(W0·W2·X0) + 가지 2 + 적중 십자 X0 → f2 링 r8 + 바깥 가지 번개 3 → f3 점선 잔광 + 링 r14 → f4 꼬리 r18. 경직 600ms 시작."), PALETTE_NOTE)
    fx["rain"] = (rain_frames(), ["any"], 32, 32, [40, 50, 60, 70], (4, 16), False, dict(proj, spawn="shot",
        note="폭우 발사 섬광 32(기존 24, scatter 대체): 발사점 (4,16) 에서 ±50°/±25°/0° 5갈래 번개 광선(3겹) — scatter 와 같은 구조, 갈래 5·더 넓음."), PALETTE_NOTE)
    fx["seek"] = (seek_frames(), ["any"], 24, 24, [60, 60, 60, 60], (20, 12), True, dict(proj, spawn="loop_move", depth="below",
        note="추적 꼬리 24(기존 16): 유도 소용돌이 — 꼬인 두 가닥(W3/W2 → 뒤로 W1/W0)이 뒤로 흐르고(4f = 2π, 이음새 없음) 교차점 X0, 머리 X1. 피벗 (20,12) = 화살 중심. 화살이 선회해도 각도만 따라가면 됨."), PALETTE_NOTE)
    # ---- 보조 동작 · 대쉬
    fx["parry_flash"] = (parry_flash_frames(), ["any"], 48, 48, [40, 50, 60, 80, 100], (24, 24), False, dict(
        anchor="hitbox_center", spawn="parry_success", depth="above", weapon="any",
        flash={"color": "#fff4dc", "alpha": 0.25, "ms": 40, "atFrame": 0},
        note="패링 성공(48, 기존 32): 시간 정지 섬광 — f0 전체 X0 십자 + X1 코어(히트스톱·화면 오버레이 X1 0.25 와 동시) → f1 깨끗한 동심 고리 2(층 24/22, 4px 간격) + 짧은 X0 광선 → f2 고리 확장 + 네 귀 글린트 → f3 점선 → f4 조각. 무기 보조색 없음(층 램프 + 코어)."), PALETTE_NOTE_NOSEC)
    fx["guard_wave"] = (guard_wave_frames(), DIRS, 64, 32, [50, 60, 70, 80], (32, 16), False, dict(
        anchor="player_pivot", spawn="guard_release", depth="below", weapon="greatsword", secondary="fx.weapons.greatsword",
        pivotNote="피벗 (32,16) = 발(기존 (24,14)). 반타원 반경 29 = 밀쳐내기 40px 의 ~70%.",
        note="가드 밀쳐내기(64×32, 기존 48×24): 발 앞 반타원(세로 0.5) 충격파 3겹(W0 테두리 · W2 용암 몸 · X1 1px 코어 점선) r10→18→25→29 + 가장자리 재 G06/G09 + 짧은 균열 2(용암 W2 → f3 W0 점). 철벽이면 ironwall 과 동시."), PALETTE_NOTE)
    fx["shadowstep_ghost"] = (shadowstep_ghost_frames(), DIRS, 16, 24, [60, 80, 100], (8, 23), False, dict(
        anchor="player_pivot", spawn="shadowstep_start", depth="below", followsPlayer=False, weapon="dagger", secondary=DGS,
        note="그림자 걸음 출발 잔상(단검 보조색, 기존 무채): 출발점 실루엣 W0 단색(우·하 림 W1) → 세로 줄무늬 W1 → 조각, 발밑 W0 웅덩이 r7→5→3 수축. 암살 분신과 같은 어휘. 바닥 깊이·고정."), PALETTE_NOTE)
    fx["aim_charge"] = (aim_charge_frames(), ["any"], 32, 32, [100, 100, 100, 100, 100, 100], (16, 16), False, dict(
        anchor="player_pivot", spawn="aim_charge", depth="above", progressDriven=True, weapon="bow", secondary=BWS,
        pivotNote="피벗 (16,16) 을 플레이어 몸 중심(발 피벗에서 위로 11px)에 둔다",
        note="조준 차지(32, 기존 24): r10 고리 W1 점선 → 진행도만큼 W3(가장자리 W0)로 참, 머리 X1 → f5 완료 = 코어 X0 고리 + W3 고리 + 네 귀 가지 번개(4px) + 중심 X0. frame = min(5, floor(progress*5)). 취소 시 즉시 제거."), PALETTE_NOTE)
    fx["aim_line"] = (aim_line_frames(), ["any"], 8, 2, [0, 0], (0, 1), False, dict(
        anchor="player_pivot", rotate=True, drawnFacing="right", tile=True, fps=0, spawn="aim_charge", depth="below", weapon="bow", secondary=BWS,
        stateFrames={"charging": 0, "complete": 1},
        pivotNote="피벗 (0,1) = 선 시작(플레이어 몸 중심). TileSprite 폭 = 사거리, 회전 = 커서 각도",
        note="조준 궤적 코어 점선(4 on / 4 off): f0 차지 중 = X1 코어 + W2 밑줄, f1 차지 완료 = X0 코어 + W3 밑줄. 상태 프레임(시간 애니 아님) — 미지원이면 f0 만 사용."), PALETTE_NOTE)
    fx["dash_dust"] = (dash_dust_frames(), DIRS, 16, 8, [50, 70, 90], (8, 6), False, dict(
        anchor="player_pivot", spawn="dash_start", depth="below", followsPlayer=False, weapon="any",
        note="대쉬 출발 먼지(무채 G06/G09/G12, 42라운드 결정: 유지). 출발 위치(고정) 발 피벗에, 방향 = 대쉬 방향(먼지는 반대쪽). 바닥 깊이. 모든 무기 공통, 보조색 없음."), PALETTE_NOTE_GRAY)
    fx["dash_trail"] = (dash_trail_frames(), DIRS, 16, 24, [40, 60, 80], (8, 23), False, dict(
        anchor="player_pivot", spawn="dash_trail", depth="below", followsPlayer=False, weapon="any",
        tint={"when": "batto / longinvuln / afterimage node", "color": "fx.weapons.<katana|dagger>.ramp[1]", "method": "setTintFill (flat) — sheet is dark gray G02~G04, multiplicative setTint would go black"},
        note="대쉬 잔상(무채 G02~G04, 42라운드 결정: 유지 + 시스템 틴트). 대쉬 중 40~50ms 마다 현재 위치에 하나씩, 각 180ms 뒤 소멸. 발도술·허보·잔상 노드일 때만 그 무기 W1 로 틴트(setTintFill). 바닥 깊이."), PALETTE_NOTE_GRAY)

    ok = True
    for name, v in fx.items():
        fbd, dirs, w, h, durs, pivot, loop, extra, pnote = v
        extra = dict(extra)
        save_sheet(name, fbd, dirs, w, h, durs, loop, pivot, dict(extra, palette=pnote))
        wid = extra.get("weapon")
        wid = None if wid in (None, "any") else wid
        gb = 4 if name in ("dash_dust", "dash_trail") else 2
        ok &= color_report(name, fbd, wid=wid, gray_budget=gb)
    print("ALL OK" if ok else "CHECK above")
    preview_b(fx)
    preview_b_fight(fx)
    print("->", OUT_FX, "/", HERE)


if __name__ == "__main__":
    main()
