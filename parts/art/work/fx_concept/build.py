#!/usr/bin/env python3
"""LOPAD 42라운드 — 무기 이펙트 '인페르노 언어' 콘셉트 시트 (목업, 승인 후 34종 양산 시 교체).

실행: python3 parts/art/work/fx_concept/build.py
입력: parts/art/palette/lopad.json (gray + floor1 ramp + **fx 블록**), assets/sprites/player/*.png,
      assets/sprites/weapons/katana_attack.png, assets/sprites/enemies/dummy_hurt.png,
      assets/sprites/bosses/stage1_idle.png, assets/tiles/stage1.png (목업 합성용, 읽기만)
산출 (assets/sprites/fx/concept_*.png + .json — 전부 새 파일, 기존 fx 미변경):
  칼   concept_katana_slash 48 4dir 5f / concept_iai 64 4dir 7f / concept_wide 96 4dir 7f / concept_zangetsu 64 4dir 4f 루프
  대검 concept_quake_bolt 64 any 6f (파쇄→지진 '바닥 균열 + 낙뢰')
  단검 concept_assassin 48 any 5f (그림자 분신 군집 + 교차 섬광)
  활   concept_heavyarrow_bolt 48 any 5f (중시 '번개 낙하')
  공통 concept_hit_burst 24 any 4f (적중 시 쏟아지는 광선, 무기 무관)
  보스 concept_telegraph_line 16 any 2f 루프·tile / concept_telegraph_circle 64 any 6f 진행도 / concept_telegraph_aura 64 any 4f 루프
  미리보기: parts/art/work/fx_concept/preview_concept.png (3배 + 1배 띠), preview_mock_fight.png (1배 합성 + 3배 확대)

설계 (fx-design.md 요약)
  - 3층 색: 백열 코어 X0/X1 → 층 강조색 25~27 (하이라이트: 머리 글린트·불티·섬광) → 무기 보조 램프 W3→W1 (몸체) → W0 어두운 가장자리.
  - '겹친 광선' = 같은 궤적에 폭·반지름이 다른 2~3겹을 **1프레임씩 어긋나게** (바깥 겹이 한 프레임 늦게 따라온다).
  - '긴 잔상' = 시트 꼬리 프레임(어두운 W1/W0 띠 + 점선) + 시스템 트레일.  '번개' = 지그재그 폴리라인 3겹(W0 테두리·W2 몸·X0 코어) + 가지.
  - 예고 = 4px 굵은 실선(가운데 2px 코어), 닫히는 원(바깥 링이 범위 링으로 수렴), 수렴 오라(안쪽으로 흐르는 토막).
  - 반투명 0, 고립 픽셀 0 (불티는 2px 쌍). 방향 4행은 right 기준 그림을 90° 회전/좌우 반전 (픽셀 밀도 유지).
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
DIRS = ["down", "up", "left", "right"]
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
FONTB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 12)
PALETTE_NOTE = "parts/art/palette/lopad.json (gray + floor 1 accent 16-27 runtime swap + fx block: core X0/X1 + weapon secondary W0-W3, fixed)"


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def G(i):
    return hx(GRAY[i])


def C(i):
    """층 강조 램프 인덱스 16~27 (1층 호박, 런타임 스왑)."""
    return hx(RAMP[i - 16])


X0, X1 = hx(FX["core"][0]), hx(FX["core"][1])


def W(wid, i):
    """무기 보조 램프 W0(어두운 가장자리)~W3(밝은 몸체)."""
    return hx(FX["weapons"][wid]["ramp"][i])


# ============================================================ 캔버스
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
        """호 띠 (weapons/build.py 와 같은 규약). colors 는 안쪽→바깥쪽. 양 끝은 가늘어진다."""
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

    def dash_pattern(self, mod=4, keep=(0,), seed=0):
        for y in range(self.h):
            for x in range(self.w):
                if self.p[x, y][3] and ((x * 3 + y + seed) % mod) not in keep:
                    self.p[x, y] = (0, 0, 0, 0)

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

    # ---- 겹친 광선용: 두꺼운 폴리라인(번개) ----
    def bolt(self, pts_xy, layers, seed=0):
        """pts_xy 폴리라인을 layers=[(dilate, color), ...] 순서로 (굵은 것 먼저) 찍는다. 3겹이면 테두리·몸·코어."""
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
    """결정적 의사난수 (0~1)."""
    s = (seed * 1103515245 + 12345) & 0x7fffffff
    while True:
        s = (s * 1103515245 + 12345) & 0x7fffffff
        yield (s >> 8) / float(1 << 23)


def zigzag(x0, y0, x1, y1, n, jag, seed):
    """(x0,y0)→(x1,y1) 를 n 토막으로 나누고 수직 방향으로 ±jag 흔든 폴리라인."""
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
        "concept": "42라운드 콘셉트 목업. 승인 후 양산 시 정식 id(접두어 없는 이름)로 교체·삭제.",
    }
    meta.update(extra)
    with open(os.path.join(OUT_FX, name + ".json"), "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    return sheet


def color_report(name, frames_by_dir, wid=None):
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
    sec = {}
    other = []
    for c in cols:
        if c in GS or c in CS or c in XS:
            continue
        hit = [(k, v.index(c)) for k, v in WS.items() if c in v]
        if hit:
            sec.setdefault(hit[0][0], []).append(hit[0][1])
        else:
            other.append(c)
    sec = {k: sorted(v) for k, v in sec.items()}
    acc_budget = 3 if sec else 8   # 무기 보조색이 있으면 층 강조는 하이라이트 3칸까지, 예고·공통은 층 램프만 8칸까지
    bad = len(grays) > 2 or len(accents) > acc_budget or other or iso or semi or len(sec) > 1 or (wid and sec and wid not in sec)
    print("%-26s gray%s core%s accent%s sec%s other=%d iso=%d semi=%d%s" % (
        name, grays, core, accents, sec, len(other), iso, semi, "  <-- CHECK" if bad else ""))
    return not bad


# ============================================================ 공통: 겹친 초승달 (칼)
def layered_crescent(cv, cx, cy, a0, a1, r, tk, wid, t_main, t_ghost, t_ghost2=None, core=True, head=0.7,
                     ghost_r=4, body=None, ghost_cols=None, ghost2_cols=None, core_cols=None):
    """칼 시그니처: 본 띠(어두운 가장자리→몸체→코어→몸체→가장자리) + 바깥 잔상 겹(1프레임 늦음) + 안쪽 잔상 겹(2프레임 늦음)."""
    body = body or [W(wid, 0), W(wid, 1), W(wid, 2), W(wid, 3), W(wid, 2), W(wid, 1)]
    ghost_cols = ghost_cols or [W(wid, 0), W(wid, 1), W(wid, 2)]
    ghost2_cols = ghost2_cols or [W(wid, 0), W(wid, 1)]
    core_cols = core_cols or [X1, X0]
    if t_ghost2 is not None and t_ghost2[1] > t_ghost2[0]:
        cv.arc(cx, cy, a0, a1, t_ghost2[0], t_ghost2[1], r - ghost_r, max(2.0, tk * 0.4), ghost2_cols, head=2, min_t=1.0)
    if t_ghost is not None and t_ghost[1] > t_ghost[0]:
        cv.arc(cx, cy, a0, a1, t_ghost[0], t_ghost[1], r + ghost_r, max(2.4, tk * 0.5), ghost_cols, head=2, min_t=1.0)
    if t_main is not None and t_main[1] > t_main[0]:
        cv.arc(cx, cy, a0, a1, t_main[0], t_main[1], r, tk, body, head=head, head_boost=0)
        if core:
            # 코어: 본 띠 가운데를 지나는 1px 백열 선 (머리 쪽 1/3 만 순백 X0, 나머지 X1). 몸체(은빛)가 보이도록 절대 1px 를 넘기지 않는다.
            cv.arc(cx, cy, a0, a1, t_main[0] + 0.04, t_main[1] - 0.02, r + 0.5, 1.0, core_cols, head=head, head_boost=1, min_t=1.0, taper=0.0)


def head_glint(cv, cx, cy, a0, a1, t, r, col, horiz=True):
    ang = math.radians(a0 + (a1 - a0) * t)
    cv.pair(cx + r * math.cos(ang), cy + r * math.sin(ang), col, horiz=horiz)


def spill_rays(cv, cx, cy, a0, a1, t, r, wid, n=3, length=7, seed=1, cols=None):
    """적중 순간 머리에서 번개처럼 바깥으로 쏟아지는 짧은 광선 (W0 테두리 + X0 코어)."""
    rnd = prng(seed)
    cols = cols or [(1, W(wid, 0)), (0, X0)]
    ang = math.radians(a0 + (a1 - a0) * t)
    ox, oy = cx + r * math.cos(ang), cy + r * math.sin(ang)
    for i in range(n):
        da = (i - (n - 1) / 2.0) * 28 + (next(rnd) * 10 - 5)
        a = ang + math.radians(da)
        L = length + next(rnd) * 3
        pts = zigzag(ox, oy, ox + L * math.cos(a), oy + L * math.sin(a), 3, 1.2, seed + i)
        cv.bolt(pts, cols)


def remnant(cv, cx, cy, a0, a1, t0, t1, r, wid, mod=4, keep=(0, 1, 2), seed=0, cols=None):
    """꼬리 프레임: 어두운 띠를 규칙 점선으로 끊는다."""
    tmp = Canvas(cv.w, cv.h)
    tmp.arc(cx, cy, a0, a1, t0, t1, r, 2.2, cols or [W(wid, 0), W(wid, 1)], head=2, min_t=1.0)
    tmp.dash_pattern(mod=mod, keep=keep, seed=seed)
    for y in range(cv.h):
        for x in range(cv.w):
            if tmp.p[x, y][3]:
                cv.px(x, y, tmp.p[x, y])


# ============================================================ 1. 칼 기본 베기 48 · 5f
def katana_slash_frames():
    """48×48, 피벗 (24,34). 2겹 (본 띠 + 바깥 잔상 1프레임 지연). right 기준 -100°→80°."""
    cx, cy, r, tk = 24, 24, 13.0, 5.0
    a0, a1 = -100, 80
    wid = "katana"
    frames = []
    # f0 예비: 코어 선만 앞 40% (인페르노의 '예고 선' 축소판)
    cv = Canvas(48, 48)
    cv.arc(cx, cy, a0, a1, 0.0, 0.4, r, 1.6, [W(wid, 1), X1], head=0.3, min_t=1.0)
    head_glint(cv, cx, cy, a0, a1, 0.4, r + 1, C(27))
    frames.append(cv)
    # f1 본 띠 전체 + 코어, 잔상은 아직 앞 절반
    cv = Canvas(48, 48)
    layered_crescent(cv, cx, cy, a0, a1, r, tk, wid, t_main=(0.0, 1.0), t_ghost=(0.0, 0.45), head=0.65)
    head_glint(cv, cx, cy, a0, a1, 0.96, r + 3, C(27))
    frames.append(cv)
    # f2 본 띠 유지(코어 X1 로 식음) + 잔상 전체 + 머리에서 쏟아지는 광선 2
    cv = Canvas(48, 48)
    layered_crescent(cv, cx, cy, a0, a1, r, tk * 0.9, wid, t_main=(0.1, 1.0), t_ghost=(0.0, 1.0), head=0.8,
                     core_cols=[W(wid, 3), X1])
    spill_rays(cv, cx, cy, a0, a1, 0.97, r, wid, n=2, length=5, seed=3, cols=[(1, W(wid, 0)), (0, C(27))])
    frames.append(cv)
    # f3 식음: 본 띠가 W1/W2 로, 잔상은 W0/W1
    cv = Canvas(48, 48)
    cv.arc(cx, cy, a0, a1, 0.3, 1.0, r, tk * 0.6, [W(wid, 0), W(wid, 1), W(wid, 2), W(wid, 1)], head=2, min_t=1.0)
    cv.arc(cx, cy, a0, a1, 0.15, 1.0, r + 4, 2.0, [W(wid, 0), W(wid, 1)], head=2, min_t=1.0)
    cv.pair(cx + (r + 6) * math.cos(math.radians(a1 - 10)), cy + (r + 6) * math.sin(math.radians(a1 - 10)), C(24))
    frames.append(cv)
    # f4 꼬리: 점선 잔재 + 불티 (시스템 트레일이 이어받는 구간)
    cv = Canvas(48, 48)
    remnant(cv, cx, cy, a0, a1, 0.45, 1.0, r, wid, mod=4, keep=(0, 1, 2))
    remnant(cv, cx, cy, a0, a1, 0.3, 0.95, r + 4, wid, mod=5, keep=(0, 1), seed=2, cols=[W(wid, 0), W(wid, 0)])
    cv.pair(cx + (r + 7) * math.cos(math.radians(a1 - 20)), cy + (r + 7) * math.sin(math.radians(a1 - 20)), C(22), horiz=False)
    cv.pair(cx + (r + 2) * math.cos(math.radians(a1 - 55)), cy + (r + 2) * math.sin(math.radians(a1 - 55)), C(22))
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return four_dirs_from_right(frames)


# ============================================================ 2. 칼 거합 64 · 7f
def iai_frames():
    """64×64, 피벗 (32,42). 3겹 (본 띠 + 바깥 잔상 1프레임 지연 + 안쪽 잔상 2프레임 지연) + 적중 광선. -110°→110°."""
    cx, cy, r, tk = 32, 32, 21.0, 7.0
    a0, a1 = -110, 110
    wid = "katana"
    frames = []
    # f0 예고 선: 궤적 전체를 가는 코어 점선으로 미리 보여준다 (굵고 선명한 예고의 칼 버전)
    cv = Canvas(64, 64)
    cv.arc(cx, cy, a0, a1, 0.0, 1.0, r, 1.4, [W(wid, 2)], head=2, min_t=1.0)
    cv.dash_pattern(mod=5, keep=(0, 1, 2), seed=1)
    cv.arc(cx, cy, a0, a1, 0.0, 0.25, r, 2.0, [W(wid, 3), X1], head=0.2, min_t=1.0)
    head_glint(cv, cx, cy, a0, a1, 0.25, r + 1, C(27))
    frames.append(cv)
    # f1 섬광 프레임: 본 띠 전체가 백열 (1프레임 40ms) — 화면 섬광과 동시
    cv = Canvas(64, 64)
    layered_crescent(cv, cx, cy, a0, a1, r, tk, wid, t_main=(0.0, 1.0), t_ghost=(0.0, 0.5), head=0.5,
                     body=[W(wid, 0), W(wid, 3), X1, X0, X1, W(wid, 3), W(wid, 1)], core=False)
    head_glint(cv, cx, cy, a0, a1, 0.98, r + 4, C(27))
    frames.append(cv)
    # f2 본 띠(정상 3층) + 바깥 잔상 전체 + 안쪽 잔상 절반 + 적중 광선 3
    cv = Canvas(64, 64)
    layered_crescent(cv, cx, cy, a0, a1, r, tk, wid, t_main=(0.0, 1.0), t_ghost=(0.0, 1.0), t_ghost2=(0.0, 0.55), head=0.7)
    spill_rays(cv, cx, cy, a0, a1, 0.98, r, wid, n=3, length=8, seed=11)
    head_glint(cv, cx, cy, a0, a1, 0.9, r + 5, C(27), horiz=False)
    frames.append(cv)
    # f3 본 띠 식음(코어 X1) + 안쪽 잔상 전체, 바깥 잔상 어두워짐
    cv = Canvas(64, 64)
    layered_crescent(cv, cx, cy, a0, a1, r, tk * 0.85, wid, t_main=(0.12, 1.0), t_ghost=(0.1, 1.0), t_ghost2=(0.0, 1.0),
                     head=0.85, core_cols=[W(wid, 3), W(wid, 3)], ghost_cols=[W(wid, 0), W(wid, 1), W(wid, 1)])
    spill_rays(cv, cx, cy, a0, a1, 0.99, r, wid, n=2, length=6, seed=12, cols=[(1, W(wid, 0)), (0, C(24))])
    frames.append(cv)
    # f4 어두운 세 띠 (잔월 지속 영역의 시작 모양)
    cv = Canvas(64, 64)
    cv.arc(cx, cy, a0, a1, 0.25, 1.0, r, tk * 0.55, [W(wid, 0), W(wid, 1), W(wid, 2), W(wid, 1)], head=2, min_t=1.0)
    cv.arc(cx, cy, a0, a1, 0.2, 1.0, r + 4, 2.2, [W(wid, 0), W(wid, 1)], head=2, min_t=1.0)
    cv.arc(cx, cy, a0, a1, 0.05, 0.95, r - 4, 2.0, [W(wid, 0), W(wid, 1)], head=2, min_t=1.0)
    cv.pair(cx + (r + 8) * math.cos(math.radians(a1 - 12)), cy + (r + 8) * math.sin(math.radians(a1 - 12)), C(24))
    frames.append(cv)
    # f5 띠가 점선으로 끊김
    cv = Canvas(64, 64)
    remnant(cv, cx, cy, a0, a1, 0.35, 1.0, r, wid, mod=4, keep=(0, 1, 2), cols=[W(wid, 0), W(wid, 1), W(wid, 1)])
    remnant(cv, cx, cy, a0, a1, 0.3, 0.98, r + 4, wid, mod=5, keep=(0, 1), seed=3, cols=[W(wid, 0), W(wid, 0)])
    remnant(cv, cx, cy, a0, a1, 0.1, 0.9, r - 4, wid, mod=5, keep=(0, 1), seed=4, cols=[W(wid, 0), W(wid, 0)])
    cv.pair(cx + (r + 9) * math.cos(math.radians(a1 - 25)), cy + (r + 9) * math.sin(math.radians(a1 - 25)), C(22), horiz=False)
    frames.append(cv)
    # f6 꼬리: 희미한 점선 + 불티 둘
    cv = Canvas(64, 64)
    remnant(cv, cx, cy, a0, a1, 0.5, 1.0, r, wid, mod=6, keep=(0, 1), seed=5, cols=[W(wid, 0), W(wid, 0)])
    cv.pair(cx + (r + 3) * math.cos(math.radians(a1 - 40)), cy + (r + 3) * math.sin(math.radians(a1 - 40)), C(22))
    cv.pair(cx + (r + 10) * math.cos(math.radians(a1 - 15)), cy + (r + 10) * math.sin(math.radians(a1 - 15)), C(22), horiz=False)
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return four_dirs_from_right(frames)


# ============================================================ 3. 칼 만월 96 · 7f
def wide_frames():
    """96×96, 피벗 (48,58). 거합 3겹 + 보름달 고리(안쪽 r=21 달무리가 f3 에서 닫힌 원이 됨). -140°→140°."""
    cx, cy, r, tk = 48, 48, 33.0, 9.0
    a0, a1 = -140, 140
    wid = "katana"
    frames = []
    cv = Canvas(96, 96)   # f0 예고: 궤적 점선 + 보름달 자리 희미한 원
    cv.arc(cx, cy, a0, a1, 0.0, 1.0, r, 1.6, [W(wid, 2)], head=2, min_t=1.0)
    cv.dash_pattern(mod=5, keep=(0, 1, 2), seed=1)
    cv.ring(cx, cy, 21, W(wid, 1), thick=1.2, dash=(26, 10))
    cv.arc(cx, cy, a0, a1, 0.0, 0.2, r, 2.2, [W(wid, 3), X1], head=0.15, min_t=1.0)
    head_glint(cv, cx, cy, a0, a1, 0.2, r + 1, C(27))
    frames.append(cv)
    cv = Canvas(96, 96)   # f1 섬광
    layered_crescent(cv, cx, cy, a0, a1, r, tk, wid, t_main=(0.0, 1.0), t_ghost=(0.0, 0.5), head=0.5, ghost_r=5,
                     body=[W(wid, 0), W(wid, 3), X1, X0, X0, X1, W(wid, 3), W(wid, 1)], core=False)
    cv.ring(cx, cy, 21, W(wid, 2), thick=1.4, dash=(26, 10), phase=5)
    head_glint(cv, cx, cy, a0, a1, 0.98, r + 5, C(27))
    frames.append(cv)
    cv = Canvas(96, 96)   # f2 3겹 + 광선 4 + 달무리 밝아짐
    layered_crescent(cv, cx, cy, a0, a1, r, tk, wid, t_main=(0.0, 1.0), t_ghost=(0.0, 1.0), t_ghost2=(0.0, 0.55), head=0.7, ghost_r=5)
    cv.ring(cx, cy, 21, W(wid, 2), thick=1.6)
    cv.ring(cx, cy, 21, X1, thick=1.0, dash=(14, 22), phase=0)
    spill_rays(cv, cx, cy, a0, a1, 0.98, r, wid, n=4, length=10, seed=21)
    head_glint(cv, cx, cy, a0, a1, 0.9, r + 6, C(27), horiz=False)
    frames.append(cv)
    cv = Canvas(96, 96)   # f3 보름달: 안쪽 원이 닫히며 백열, 본 띠 식음
    layered_crescent(cv, cx, cy, a0, a1, r, tk * 0.85, wid, t_main=(0.1, 1.0), t_ghost=(0.1, 1.0), t_ghost2=(0.0, 1.0),
                     head=0.85, ghost_r=5, core_cols=[W(wid, 3), W(wid, 3)], ghost_cols=[W(wid, 0), W(wid, 1), W(wid, 1)])
    cv.ring(cx, cy, 21, W(wid, 1), thick=3.0)
    cv.ring(cx, cy, 21, W(wid, 3), thick=1.6)
    cv.ring(cx, cy, 21, X0, thick=1.0, dash=(30, 15), phase=10)
    spill_rays(cv, cx, cy, a0, a1, 0.99, r, wid, n=2, length=7, seed=22, cols=[(1, W(wid, 0)), (0, C(24))])
    for k in range(4):
        ang = math.radians(k * 90 + 45)
        cv.pair(cx + 24 * math.cos(ang), cy + 24 * math.sin(ang), C(27), horiz=(k % 2 == 0))
    frames.append(cv)
    cv = Canvas(96, 96)   # f4 어두운 세 띠 + 달 고리 W2
    cv.arc(cx, cy, a0, a1, 0.25, 1.0, r, tk * 0.55, [W(wid, 0), W(wid, 1), W(wid, 2), W(wid, 1)], head=2, min_t=1.0)
    cv.arc(cx, cy, a0, a1, 0.2, 1.0, r + 5, 2.4, [W(wid, 0), W(wid, 1)], head=2, min_t=1.0)
    cv.arc(cx, cy, a0, a1, 0.05, 0.95, r - 5, 2.0, [W(wid, 0), W(wid, 1)], head=2, min_t=1.0)
    cv.ring(cx, cy, 21, W(wid, 1), thick=2.2)
    cv.ring(cx, cy, 21, W(wid, 2), thick=1.0, dash=(20, 20), phase=20)
    cv.pair(cx + (r + 9) * math.cos(math.radians(a1 - 12)), cy + (r + 9) * math.sin(math.radians(a1 - 12)), C(24))
    frames.append(cv)
    cv = Canvas(96, 96)   # f5 점선
    remnant(cv, cx, cy, a0, a1, 0.35, 1.0, r, wid, mod=4, keep=(0, 1, 2), cols=[W(wid, 0), W(wid, 1), W(wid, 1)])
    remnant(cv, cx, cy, a0, a1, 0.3, 0.98, r + 5, wid, mod=5, keep=(0, 1), seed=3, cols=[W(wid, 0), W(wid, 0)])
    remnant(cv, cx, cy, a0, a1, 0.1, 0.9, r - 5, wid, mod=5, keep=(0, 1), seed=4, cols=[W(wid, 0), W(wid, 0)])
    cv.ring(cx, cy, 21, W(wid, 1), thick=1.4, dash=(12, 10), phase=3)
    cv.pair(cx + (r + 10) * math.cos(math.radians(a1 - 25)), cy + (r + 10) * math.sin(math.radians(a1 - 25)), C(22), horiz=False)
    frames.append(cv)
    cv = Canvas(96, 96)   # f6 꼬리
    remnant(cv, cx, cy, a0, a1, 0.5, 1.0, r, wid, mod=6, keep=(0, 1), seed=5, cols=[W(wid, 0), W(wid, 0)])
    cv.ring(cx, cy, 21, W(wid, 0), thick=1.2, dash=(8, 14), phase=6)
    cv.pair(cx + (r + 3) * math.cos(math.radians(a1 - 40)), cy + (r + 3) * math.sin(math.radians(a1 - 40)), C(22))
    cv.pair(cx + (r + 11) * math.cos(math.radians(a1 - 15)), cy + (r + 11) * math.sin(math.radians(a1 - 15)), C(22), horiz=False)
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return four_dirs_from_right(frames)


# ============================================================ 4. 칼 잔월 64 · 4f 루프
def zangetsu_frames():
    """64×64, 피벗 (32,42), 바닥 깊이. 거합 자리의 어두운 3띠 + 띠 사이를 뛰는 번개 토막 + 도는 글린트. 4f = 한 바퀴 = 틱 300ms."""
    cx, cy, r = 32, 32, 21.0
    a0, a1 = -110, 110
    wid = "katana"
    frames = []
    for f in range(4):
        cv = Canvas(64, 64)
        band = [W(wid, 0), W(wid, 1), W(wid, 1)] if f else [W(wid, 0), W(wid, 1), W(wid, 2)]
        cv.arc(cx, cy, a0, a1, 0.05, 0.95, r, 3.4, band, head=2, min_t=3.0)
        outer = Canvas(64, 64)
        outer.arc(cx, cy, a0, a1, 0.08, 0.97, r + 4, 1.2, [W(wid, 1)], head=2, min_t=1.0)
        outer.dash_pattern(mod=7, keep=(0, 1, 2, 3, 4), seed=f)
        for y in range(64):
            for x in range(64):
                if outer.p[x, y][3]:
                    cv.px(x, y, outer.p[x, y])
        cv.arc(cx, cy, a0, a1, 0.0, 0.9, r - 4, 1.0, [W(wid, 0)], head=2, min_t=1.0)
        if f == 0:
            # 틱 순간: 바깥 점선 테두리 + 띠 전체 한 단 밝음
            cv.arc(cx, cy, a0, a1, 0.05, 0.95, r + 7, 1.0, [W(wid, 2)], head=2, min_t=1.0)
            cv.dash_pattern(mod=6, keep=(0, 1, 2, 3), seed=0)
            cv.arc(cx, cy, a0, a1, 0.05, 0.95, r, 3.4, band, head=2, min_t=3.0)
        # 띠 안을 도는 글린트 2개 (4프레임에 다음 글린트 자리까지 = 이음새 없음)
        for k in range(2):
            t0 = 0.05 + ((f * 0.1125 + k * 0.45) % 0.9)
            t1 = min(0.95, t0 + 0.12)
            cv.arc(cx, cy, a0, a1, t0, t1, r, 3.4, [W(wid, 2), W(wid, 3), X1], head=2, min_t=3.0)
            cv.arc(cx, cy, a0, a1, t0 + 0.03, t1 - 0.03, r + 0.5, 1.0, [X0], head=2, min_t=1.0, taper=0.0)
        # 띠 사이를 뛰는 번개 토막 (바깥 띠 ↔ 본 띠), 프레임마다 자리 이동
        for k in range(2):
            t = 0.15 + ((f * 0.2 + k * 0.4) % 0.8)
            ang = math.radians(a0 + (a1 - a0) * t)
            p0 = (cx + (r + 4) * math.cos(ang), cy + (r + 4) * math.sin(ang))
            ang2 = ang + math.radians(6)
            p1 = (cx + (r - 4) * math.cos(ang2), cy + (r - 4) * math.sin(ang2))
            cv.bolt(zigzag(p0[0], p0[1], p1[0], p1[1], 3, 1.5, 40 + f * 7 + k), [(0, W(wid, 3))])
        cv.despeckle8()
        frames.append(cv)
    return four_dirs_from_right(frames)


# ============================================================ 5. 대검 파쇄→지진 '바닥 균열 + 낙뢰' 64 · 6f
def quake_bolt_frames():
    """64×64 any, 피벗 (32,40) = 타격점(바닥). 위에서 떨어지는 낙뢰(3겹) → 타격점 섬광 → 세로 압축 링 + 방사 균열 + 재·불티."""
    wid = "greatsword"
    hx_, hy_ = 32, 40
    frames = []
    bolt_cols = [(2, W(wid, 0)), (1, W(wid, 2)), (0, X0)]
    thin_cols = [(1, W(wid, 1)), (0, X1)]
    cracks = [(a, L) for a, L in ((12, 15), (58, 11), (113, 17), (160, 12), (205, 16), (248, 10), (298, 14), (338, 9))]

    def crack_lines(cv, scale, cols, dashed=False):
        tmp = Canvas(64, 64)
        for i, (a, L) in enumerate(cracks):
            ang = math.radians(a)
            L2 = L * scale
            pts = zigzag(hx_ + 3 * math.cos(ang), hy_ + 3 * math.sin(ang) * 0.6, hx_ + L2 * math.cos(ang), hy_ + L2 * math.sin(ang) * 0.6, 4, 2.2, 70 + i)
            tmp.bolt(pts, cols)
        if dashed:
            tmp.dash_pattern(mod=3, keep=(0, 1), seed=1)
        for y in range(64):
            for x in range(64):
                if tmp.p[x, y][3]:
                    cv.px(x, y, tmp.p[x, y])

    cv = Canvas(64, 64)   # f0 예고: 하늘에서 가는 선이 먼저 내려온다 + 타격점 점
    cv.bolt(zigzag(36, 0, hx_, hy_ - 2, 5, 2.5, 5), thin_cols)
    cv.pair(hx_ - 1, hy_, X1)
    frames.append(cv)
    cv = Canvas(64, 64)   # f1 낙뢰 본체(3겹) + 가지 2 + 타격 섬광 별
    cv.bolt(zigzag(36, 0, hx_, hy_ - 1, 6, 3.0, 6), bolt_cols)
    cv.bolt(zigzag(33, 14, 22, 24, 3, 1.5, 7), thin_cols)
    cv.bolt(zigzag(35, 22, 44, 30, 3, 1.5, 8), thin_cols)
    for a in (0, 45, 90, 135, 180, 225, 270, 315):
        ang = math.radians(a)
        L = 6 if a % 90 == 0 else 4
        cv.line(hx_, hy_, hx_ + L * math.cos(ang), hy_ + L * math.sin(ang) * 0.7, C(27))
    cv.disc(hx_, hy_, 2.2, X0, ky=0.6)
    frames.append(cv)
    cv = Canvas(64, 64)   # f2 낙뢰 조각(코어만 남음) + 1단 링 r8 + 균열 시작
    cv.bolt(zigzag(36, 0, hx_, hy_ - 1, 6, 3.0, 6), [(0, W(wid, 2))])
    cv.dash_pattern(mod=3, keep=(0, 1), seed=2)
    cv.ring(hx_, hy_, 8, W(wid, 0), thick=3.0, ky=0.6)
    cv.ring(hx_, hy_, 8, W(wid, 3), thick=1.6, ky=0.6)
    cv.ring(hx_, hy_, 8, X1, thick=1.0, ky=0.6, dash=(40, 50))
    crack_lines(cv, 0.5, [(0, W(wid, 1))])
    cv.disc(hx_, hy_, 2.0, X1, ky=0.6)
    frames.append(cv)
    cv = Canvas(64, 64)   # f3 링 r16 + 균열 전체(용암이 비침) + 재·불티
    cv.ring(hx_, hy_, 16, W(wid, 0), thick=3.2, ky=0.6)
    cv.ring(hx_, hy_, 16, W(wid, 2), thick=1.8, ky=0.6)
    cv.ring(hx_, hy_, 16, X1, thick=1.0, ky=0.6, dash=(25, 65), phase=20)
    crack_lines(cv, 0.85, [(1, W(wid, 0)), (0, W(wid, 2))])
    cv.disc(hx_, hy_, 2.4, W(wid, 3), ky=0.6)
    cv.px(hx_, hy_, X1)
    for k, (a, rr) in enumerate(((30, 20), (150, 19), (260, 21), (330, 18))):
        ang = math.radians(a)
        cv.pair(hx_ + rr * math.cos(ang), hy_ + rr * math.sin(ang) * 0.6 - 2, C(26) if k % 2 else G(9), horiz=(k % 2 == 0))
    frames.append(cv)
    cv = Canvas(64, 64)   # f4 2단 링 r24 (지진 2단 판정) + 균열 W1 + 재 G6/G9
    cv.ring(hx_, hy_, 24, W(wid, 0), thick=2.6, ky=0.6)
    cv.ring(hx_, hy_, 24, W(wid, 2), thick=1.2, ky=0.6, dash=(30, 10))
    crack_lines(cv, 1.0, [(1, W(wid, 0)), (0, W(wid, 1))])
    cv.disc(hx_, hy_, 2.0, W(wid, 2), ky=0.6)
    for k, (a, rr) in enumerate(((20, 27), (120, 26), (200, 28), (300, 26), (75, 25))):
        ang = math.radians(a)
        cv.pair(hx_ + rr * math.cos(ang), hy_ + rr * math.sin(ang) * 0.6 - 3, G(6) if k % 2 else G(9), horiz=(k % 2 == 1))
    frames.append(cv)
    cv = Canvas(64, 64)   # f5 잔재: 점선 링 + 어두운 균열(식은 용암 W1 점) + 불씨
    cv.ring(hx_, hy_, 27, W(wid, 0), thick=1.4, ky=0.6, dash=(12, 14))
    crack_lines(cv, 1.0, [(0, W(wid, 0))], dashed=True)
    for k, (a, L) in enumerate(cracks[::2]):
        ang = math.radians(a)
        cv.pair(hx_ + L * 0.6 * math.cos(ang), hy_ + L * 0.6 * math.sin(ang) * 0.6, W(wid, 1), horiz=(k % 2 == 0))
    cv.pair(hx_ + 5, hy_ - 9, C(22), horiz=False)
    cv.pair(hx_ - 9, hy_ + 4, C(22))
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return {"any": frames}


# ============================================================ 6. 단검 암살 '그림자 분신 군집' 48 · 5f
def assassin_frames():
    """48×48 any, 피벗 (24,24) = 적중점 (적 히트박스 중심). 적 둘레에 그림자 분신 3이 모여들고(바닥 웅덩이), 교차 섬광 2 → 분신 흩어짐."""
    wid = "dagger"
    cx, cy = 24, 24
    mask = sprite_frame(os.path.join(SPR, "player", "player_idle.png"), 16, 24, 0, 0)   # down idle 실루엣
    frames = []

    def ghost(cv, ox, oy, col_fn):
        cv.mask_paste(mask, ox, oy, col_fn)

    def solid(fill, rim):
        """실루엣을 fill 단색으로, 우·하 가장자리(그림자 쪽)만 rim 1px — 분신끼리 겹쳐도 경계가 남는다."""
        mp = mask.load()

        def a(x, y):
            return 0 <= x < 16 and 0 <= y < 24 and mp[x, y][3] > 0

        def fn(x, y, rgb):
            return rim if (not a(x + 1, y) or not a(x, y + 1)) else fill
        return fn

    def flat(c):
        return lambda x, y, rgb: c

    def pool(cv, r, col):
        cv.disc(cx, cy + 10, r, col, ky=0.42)

    cv = Canvas(48, 48)   # f0 바닥 웅덩이 + 멀리서 모여드는 분신 3 (W0 실루엣, 어두움)
    pool(cv, 12, W(wid, 0))
    for (ox, oy) in ((0, 16), (32, 14), (16, -6)):
        ghost(cv, ox, oy, flat(W(wid, 0)))
    frames.append(cv)
    cv = Canvas(48, 48)   # f1 분신이 가까이 (W1, 가장자리 W2 줄무늬) + 웅덩이 W1 림
    pool(cv, 13, W(wid, 0))
    cv.ring(cx, cy + 10, 13, W(wid, 1), thick=1.2, ky=0.42, dash=(30, 15))
    for (ox, oy) in ((3, 13), (29, 11), (16, -3)):
        ghost(cv, ox, oy, solid(W(wid, 1), W(wid, 0)))
    cv.pair(cx, cy - 2, X1)
    frames.append(cv)
    cv = Canvas(48, 48)   # f2 교차 섬광: 대각선 2줄(3겹) + 분신은 W2 로 밝아지며 몸을 가로지름
    pool(cv, 14, W(wid, 0))
    for (ox, oy) in ((5, 11), (27, 9), (16, 0)):
        ghost(cv, ox, oy, solid(W(wid, 2), W(wid, 1)))
    cv.bolt([(8, 40), (40, 8)], [(1, W(wid, 0)), (0, W(wid, 3))])
    cv.bolt([(10, 42), (38, 10)], [(0, X0)])
    cv.bolt([(40, 38), (12, 12)], [(1, W(wid, 0)), (0, W(wid, 3))])
    cv.bolt([(36, 36), (14, 14)], [(0, X1)])
    for a in (0, 90, 180, 270):
        ang = math.radians(a + 45)
        cv.pair(cx + 9 * math.cos(ang), cy + 9 * math.sin(ang), C(27), horiz=(a % 180 == 0))
    frames.append(cv)
    cv = Canvas(48, 48)   # f3 섬광 점선 + 분신이 세로 줄무늬로 흩어짐 (W1/W2)
    pool(cv, 12, W(wid, 0))
    cv.ring(cx, cy + 10, 12, W(wid, 1), thick=1.0, ky=0.42, dash=(20, 20), phase=7)
    tmp = Canvas(48, 48)
    for (ox, oy) in ((3, 13), (29, 11), (16, -3)):
        tmp.mask_paste(mask, ox, oy, lambda x, y, rgb: W(wid, 1))
    for y in range(48):
        for x in range(48):
            if tmp.p[x, y][3] and (x % 3 != 1):   # 세로 줄무늬 2 on 1 off 로 흩어짐
                cv.px(x, y, tmp.p[x, y])
    cv.bolt([(12, 36), (36, 12)], [(0, W(wid, 2))])
    cv.dash_pattern(mod=3, keep=(0, 1), seed=3)
    pool(cv, 12, W(wid, 0))
    cv.pair(cx - 10, cy - 8, C(25), horiz=False)
    cv.pair(cx + 8, cy + 9, C(24))
    frames.append(cv)
    cv = Canvas(48, 48)   # f4 꼬리: 웅덩이 수축 + 조각
    pool(cv, 8, W(wid, 0))
    for (x, y) in ((10, 14), (34, 12), (20, 6), (30, 30), (12, 30)):
        cv.pair(x, y, W(wid, 1), horiz=(x % 2 == 0))
    cv.pair(cx + 2, cy - 4, W(wid, 2))
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return {"any": frames}


# ============================================================ 7. 활 중시 '번개 낙하' 48 · 5f
def heavyarrow_bolt_frames():
    """48×48 any, 피벗 (24,34) = 적중점. 하늘에서 떨어지는 번개 3겹 + 가지 → 적중 십자 섬광 + 링 → 잔광 가지."""
    wid = "bow"
    hx_, hy_ = 24, 34
    frames = []
    main = [(2, W(wid, 0)), (1, W(wid, 2)), (0, X0)]
    thin = [(1, W(wid, 1)), (0, W(wid, 3))]
    cv = Canvas(48, 48)   # f0 예고 가는 선 (W3) — 1프레임
    cv.bolt(zigzag(21, 0, hx_, hy_ - 2, 5, 2.0, 31), [(0, W(wid, 3))])
    cv.pair(hx_ - 1, hy_, X1)
    frames.append(cv)
    cv = Canvas(48, 48)   # f1 번개 본체 + 가지 + 적중 십자(순백)
    cv.bolt(zigzag(21, 0, hx_, hy_ - 1, 6, 3.0, 32), main)
    cv.bolt(zigzag(23, 12, 34, 20, 3, 1.5, 33), thin)
    cv.bolt(zigzag(22, 20, 12, 26, 3, 1.5, 34), thin)
    for a in (0, 90, 180, 270):
        ang = math.radians(a)
        cv.line(hx_, hy_, hx_ + 6 * math.cos(ang), hy_ + 6 * math.sin(ang), X0)
    for a in (45, 135, 225, 315):
        ang = math.radians(a)
        cv.line(hx_ + 2 * math.cos(ang), hy_ + 2 * math.sin(ang), hx_ + 4 * math.cos(ang), hy_ + 4 * math.sin(ang), C(27))
    frames.append(cv)
    cv = Canvas(48, 48)   # f2 번개 코어만 남고 가지 W2, 링 r6 + 바깥 가지 번개 3
    cv.bolt(zigzag(21, 0, hx_, hy_ - 1, 6, 3.0, 32), [(1, W(wid, 1)), (0, W(wid, 3))])
    cv.ring(hx_, hy_, 6, W(wid, 0), thick=2.6)
    cv.ring(hx_, hy_, 6, W(wid, 3), thick=1.2)
    cv.ring(hx_, hy_, 6, X0, thick=1.0, dash=(30, 60))
    for i, a in enumerate((20, 160, 260)):
        ang = math.radians(a)
        cv.bolt(zigzag(hx_ + 6 * math.cos(ang), hy_ + 6 * math.sin(ang), hx_ + 15 * math.cos(ang), hy_ + 15 * math.sin(ang), 3, 1.6, 35 + i),
                [(0, W(wid, 2))])
    cv.disc(hx_, hy_, 1.6, X1)
    frames.append(cv)
    cv = Canvas(48, 48)   # f3 번개 점선 잔광 + 링 r11 점선 + 불티
    tmp = Canvas(48, 48)
    tmp.bolt(zigzag(21, 0, hx_, hy_ - 1, 6, 3.0, 32), [(0, W(wid, 2))])
    tmp.dash_pattern(mod=3, keep=(0, 1), seed=4)
    for y in range(48):
        for x in range(48):
            if tmp.p[x, y][3]:
                cv.px(x, y, tmp.p[x, y])
    cv.ring(hx_, hy_, 11, W(wid, 0), thick=2.2)
    cv.ring(hx_, hy_, 11, W(wid, 2), thick=1.0, dash=(25, 20))
    for k, a in enumerate((45, 135, 225, 315)):
        ang = math.radians(a)
        cv.pair(hx_ + 13 * math.cos(ang), hy_ + 13 * math.sin(ang), C(26) if k % 2 else W(wid, 3), horiz=(k % 2 == 0))
    frames.append(cv)
    cv = Canvas(48, 48)   # f4 꼬리: 점선 링 + 조각
    cv.ring(hx_, hy_, 13, W(wid, 1), thick=1.2, dash=(10, 16), phase=5)
    cv.pair(hx_ - 2, hy_ - 14, W(wid, 2), horiz=False)
    cv.pair(hx_ + 9, hy_ + 3, W(wid, 1))
    cv.pair(hx_ - 11, hy_ + 2, C(22))
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return {"any": frames}


# ============================================================ 8. 공통 적중 '쏟아지는 광선' 24 · 4f
def hit_burst_frames():
    """24×24 any, 피벗 (12,12). 적중점에서 5~6갈래 번개 광선(층 강조 26 몸 + X0 코어 + 18 테두리). 무기 무관 — 보조색 없음."""
    cx, cy = 12, 12
    frames = []
    angs = (-80, -20, 40, 110, 170, 230)
    cv = Canvas(24, 24)   # f0 압축 코어
    cv.disc(cx, cy, 2.0, X0)
    cv.ring(cx, cy, 3.5, C(26), thick=1.2)
    frames.append(cv)
    cv = Canvas(24, 24)   # f1 광선 6 (3겹)
    for i, a in enumerate(angs):
        ang = math.radians(a)
        L = 9 if i % 2 == 0 else 7
        cv.bolt(zigzag(cx, cy, cx + L * math.cos(ang), cy + L * math.sin(ang), 3, 1.3, 50 + i), [(1, C(18)), (0, C(26))])
    for i, a in enumerate(angs):
        ang = math.radians(a)
        L = 9 if i % 2 == 0 else 7
        cv.bolt(zigzag(cx, cy, cx + L * math.cos(ang), cy + L * math.sin(ang), 3, 1.3, 50 + i), [(0, X0 if i % 2 == 0 else X1)])
    cv.disc(cx, cy, 1.6, X0)
    frames.append(cv)
    cv = Canvas(24, 24)   # f2 광선 바깥 토막만 (끊김)
    for i, a in enumerate(angs):
        ang = math.radians(a)
        L = 10 if i % 2 == 0 else 8
        cv.bolt(zigzag(cx + 4 * math.cos(ang), cy + 4 * math.sin(ang), cx + L * math.cos(ang), cy + L * math.sin(ang), 2, 1.2, 60 + i), [(0, C(22))])
    cv.ring(cx, cy, 3.0, C(22), thick=1.0, dash=(60, 30))
    frames.append(cv)
    cv = Canvas(24, 24)   # f3 불티
    for i, a in enumerate(angs[::2]):
        ang = math.radians(a)
        cv.pair(cx + 10 * math.cos(ang), cy + 10 * math.sin(ang), C(22), horiz=(i % 2 == 0))
    frames.append(cv)
    for cv in frames:
        cv.despeckle8()
    return {"any": frames}


# ============================================================ 9. 보스 예고 3종 (층 램프 + 코어, 보조색 없음)
def telegraph_line_frames():
    """16×16 tile, 피벗 (0,8) = 선 시작. 4px 실선: 18 테두리 / 22 몸 / 가운데 2px 코어(27 ↔ 25 맥동). x 타일링."""
    frames = []
    for f in range(2):
        cv = Canvas(16, 16)
        for x in range(16):
            cv.px(x, 5, C(18)); cv.px(x, 10, C(18))
            cv.px(x, 6, C(22)); cv.px(x, 9, C(22))
            core = C(27) if f == 0 else C(25)
            # 코어는 흐르는 토막: 12 on / 4 off, 프레임마다 8px 이동 (타일 주기 16 안에서 이음새 없음)
            on = ((x + f * 8) % 16) < 12
            cv.px(x, 7, core if on else C(24))
            cv.px(x, 8, core if on else C(24))
        frames.append(cv)
    return {"any": frames}


def telegraph_circle_frames():
    """64×64, 피벗 (32,32). 닫히는 원: 바깥 가는 링이 r30→r22(범위 링)로 수렴, 범위 링은 3px 굵게, 닿는 순간 코어 섬광. 진행도 기반 6f."""
    cx, cy = 32, 32
    R = 22.0
    frames = []
    for f in range(6):
        cv = Canvas(64, 64)
        t = f / 5.0
        # 범위 링 (굵고 선명): 18 테두리 + 22 몸, 시간이 갈수록 몸이 밝아짐
        body = [C(20), C(21), C(22), C(23), C(24), C(26)][f]
        cv.ring(cx, cy, R, C(18), thick=4.0)
        cv.ring(cx, cy, R, body, thick=2.0)
        # 수렴 링: r 30 → 22, 점선, 밝음 24→27
        r_in = 31 - 9 * t
        if f < 5:
            cv.ring(cx, cy, r_in, C(24) if f < 3 else C(26), thick=1.0, dash=(18, 6), phase=f * 7)
        else:
            cv.ring(cx, cy, R, X0, thick=1.0, dash=(28, 8), phase=4)   # 닫힌 순간 백열
        # 중심 십자 + 눈금 4 (안쪽): 프레임마다 길어짐
        L = 2 + f
        for a in (0, 90, 180, 270):
            ang = math.radians(a)
            cv.line(cx + 2 * math.cos(ang), cy + 2 * math.sin(ang), cx + L * math.cos(ang), cy + L * math.sin(ang), C(22) if f < 5 else C(27))
            cv.line(cx + (R - 5) * math.cos(ang), cy + (R - 5) * math.sin(ang), cx + (R - 3) * math.cos(ang), cy + (R - 3) * math.sin(ang), C(24))
        cv.disc(cx, cy, 1.2, C(27) if f % 2 == 0 else C(24))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def telegraph_aura_frames():
    """64×64, 피벗 (32,32). 수렴 오라: 바깥(r30)에서 중심(r8)으로 흐르는 토막 12줄 + 맥동 코어. 4f 루프, 위상 1/4 씩 → 이음새 없음."""
    cx, cy = 32, 32
    frames = []
    for f in range(4):
        cv = Canvas(64, 64)
        ph = f / 4.0
        for i in range(12):
            a = i * 30 + (7 if i % 2 else 0)
            ang = math.radians(a)
            # 각 줄에 토막 2개: 반지름 30→8 로 흐름 (주기 22px 를 2등분, 위상 ph)
            for k in range(2):
                s = ((k * 0.5 + ph) % 1.0)
                r1 = 30 - 22 * s
                r0 = r1 + 2 + 4 * s   # 안으로 갈수록 토막이 길어진다 (수렴하는 질량감)
                col = [C(19), C(21), C(23), C(25)][min(3, int((1 - s) * 4))]   # 중심으로 갈수록 밝아짐
                cv.line(cx + r0 * math.cos(ang), cy + r0 * math.sin(ang), cx + r1 * math.cos(ang), cy + r1 * math.sin(ang), col)
                if s > 0.7:
                    cv.px(cx + r1 * math.cos(ang), cy + r1 * math.sin(ang), C(27))
        # 중심 코어: 18 테두리 + 22 몸 + 백열 점 (맥동 반지름 4→5)
        rr = 4.0 + (1.0 if f in (1, 2) else 0.0)
        cv.disc(cx, cy, rr + 1.5, C(18))
        cv.disc(cx, cy, rr, C(22))
        cv.disc(cx, cy, 1.5, X0 if f == 0 else C(27))
        cv.ring(cx, cy, 8.5, C(20), thick=1.0, dash=(20, 10), phase=f * 8)
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


# ============================================================ 미리보기
def label(d, xy, text, col=(230, 230, 230), bold=False):
    d.text(xy, text, fill=col, font=FONTB if bold else FONT)


def scaled(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def dir_block(fx, name, k=3, bg=(0x21, 0x22, 0x24), rows=None):
    fbd, dirs, w, h, durs, pivot = fx[name]
    rows = rows or dirs
    n = len(durs)
    pad = 2
    W_ = 70 + (w * k + pad) * n
    H_ = 18 + (h * k + pad) * len(rows)
    im = Image.new("RGB", (W_, H_), (24, 24, 28))
    d = ImageDraw.Draw(im)
    label(d, (4, 2), "%s %dx%d %s pivot(%d,%d) %s" % (name.replace("concept_", ""), w, h, "/".join(dirs), pivot[0], pivot[1], durs), bold=True)
    for r, dr in enumerate(rows):
        y = 18 + r * (h * k + pad)
        label(d, (4, y + 4), dr)
        for c in range(n):
            x = 70 + c * (w * k + pad)
            cell = Image.new("RGBA", (w, h), bg + (255,))
            cell.alpha_composite(fbd[dr][c].im)
            im.paste(scaled(cell, k), (x, y))
    return im


def strip_1x(fx, names, bg=(0x21, 0x22, 0x24)):
    """1배 띠: 각 시트의 right/any 행 전체 프레임을 실제 크기로."""
    cells = []
    for name in names:
        fbd, dirs, w, h, durs, pivot = fx[name]
        dr = "right" if "right" in dirs else "any"
        for cv in fbd[dr]:
            cell = Image.new("RGBA", (w, h), bg + (255,))
            cell.alpha_composite(cv.im)
            cells.append(cell)
    Wt = sum(c.width + 2 for c in cells) + 2
    Ht = max(c.height for c in cells) + 2
    im = Image.new("RGB", (Wt, Ht), (24, 24, 28))
    x = 2
    for c in cells:
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


def preview_concept(fx):
    blocks = [
        dir_block(fx, "concept_katana_slash", k=3, rows=["right", "down"]),
        dir_block(fx, "concept_iai", k=3, rows=["right", "down"]),
        dir_block(fx, "concept_wide", k=2, rows=["right", "down"]),
        dir_block(fx, "concept_zangetsu", k=3, rows=["right", "down"]),
        dir_block(fx, "concept_quake_bolt", k=3),
        dir_block(fx, "concept_assassin", k=3),
        dir_block(fx, "concept_heavyarrow_bolt", k=3),
        dir_block(fx, "concept_hit_burst", k=4),
        dir_block(fx, "concept_telegraph_line", k=4),
        dir_block(fx, "concept_telegraph_circle", k=2),
        dir_block(fx, "concept_telegraph_aura", k=2),
    ]
    top = stack(blocks, cols=1)
    s1 = strip_1x(fx, ["concept_katana_slash", "concept_iai", "concept_zangetsu", "concept_quake_bolt", "concept_assassin",
                       "concept_heavyarrow_bolt", "concept_hit_burst", "concept_telegraph_circle", "concept_telegraph_aura"])
    s2 = strip_1x(fx, ["concept_wide"])
    hdr = Image.new("RGB", (max(top.width, s1.width, s2.width), 20), (24, 24, 28))
    label(ImageDraw.Draw(hdr), (8, 3), "1x (real size, floor G02): katana_slash / iai / zangetsu / quake_bolt / assassin / heavyarrow_bolt / hit_burst / telegraph_circle / aura — then wide", bold=True)
    out = Image.new("RGB", (hdr.width, top.height + hdr.height + s1.height + s2.height + 16), (24, 24, 28))
    out.paste(top, (0, 0))
    out.paste(hdr, (0, top.height))
    out.paste(s1, (8, top.height + hdr.height))
    out.paste(s2, (8, top.height + hdr.height + s1.height + 8))
    out.save(os.path.join(HERE, "preview_concept.png"))


def preview_mock_fight(fx):
    """1배 합성: stage1 공통 바닥(0~3) 12×8 방 + 주인공 attack f1(right) + 칼 오버레이 + 거합 콘셉트 f2 + 징집병 hurt + 적중 광선 + 보스 + 닫히는 원."""
    tiles = Image.open(os.path.join(ROOT, "assets", "tiles", "stage1.png")).convert("RGBA")
    tile = [tiles.crop((i * 16, 0, i * 16 + 16, 16)) for i in range(4)]
    wall = tiles.crop((5 * 16, 0, 5 * 16 + 16, 16))
    cols_, rows_ = 14, 9
    room = Image.new("RGBA", (cols_ * 16, rows_ * 16), (0, 0, 0, 255))
    for ty in range(rows_):
        for tx in range(cols_):
            if ty == 0:
                room.alpha_composite(wall, (tx * 16, 0))
            else:
                room.alpha_composite(tile[(tx * 7 + ty * 13 + (tx * ty) % 5) % 4], (tx * 16, ty * 16))
    scene = room.copy()

    def put(sprite, x, y):
        scene.alpha_composite(sprite, (int(x), int(y)))

    def shadow(x, y, w):
        cv = Canvas(w + 2, 4)
        cv.disc(w / 2 + 1, 2, w / 2, G(1), ky=0.5)
        put(cv.im, x - 1, y - 2)

    # 보스 (양조장주 idle down f0) + 닫히는 원(f4) — 바닥 깊이
    boss = sprite_frame(os.path.join(SPR, "bosses", "stage1_idle.png"), 32, 48, 0, 0)
    bx, by = 128, 18
    circ = fx["concept_telegraph_circle"][0]["any"][4].im
    put(circ, bx + 16 - 32, by + 40 - 32)
    shadow(bx + 3, by + 48, 26)
    put(boss, bx, by)
    # 주인공 attack f1 right + 칼 오버레이 f1 right + 거합 f2 right (피벗 (32,42) = 발 (8,23))
    px_, py_ = 56, 84   # 주인공 프레임 좌상단
    player = sprite_frame(os.path.join(SPR, "player", "player_attack.png"), 16, 24, 1, 3)
    katana = sprite_frame(os.path.join(SPR, "weapons", "katana_attack.png"), 48, 48, 1, 3)
    iai = fx["concept_iai"][0]["right"][2].im
    shadow(px_ + 2, py_ + 24, 12)
    put(player, px_, py_)
    put(katana, px_ + 8 - 24, py_ + 23 - 39)
    put(iai, px_ + 8 - 32, py_ + 23 - 42)
    # 징집병 hurt f0 (left 행 = 플레이어를 바라봄) + 적중 광선 f1 — 거합 머리 쪽
    dummy = sprite_frame(os.path.join(SPR, "enemies", "dummy_hurt.png"), 16, 24, 0, 2)
    dx_, dy_ = px_ + 30, py_ - 2
    shadow(dx_ + 2, dy_ + 24, 12)
    put(dummy, dx_, dy_)
    burst = fx["concept_hit_burst"][0]["any"][1].im
    put(burst, dx_ + 8 - 12, dy_ + 12 - 12)
    # 두 번째 적 (뒤) 에 수렴 오라 — 결사병 대신 징집병 idle 로 대체 (오라 = 돌진 예고)
    arch = sprite_frame(os.path.join(SPR, "enemies", "archer_idle.png"), 16, 24, 0, 2)
    ax_, ay_ = 200, 88
    aura = fx["concept_telegraph_aura"][0]["any"][1].im
    put(aura, ax_ + 8 - 32, ay_ + 12 - 32)
    shadow(ax_ + 2, ay_ + 24, 12)
    put(arch, ax_, ay_)
    # 예고 선: 사수 → 주인공 (tile ×6, 회전 없이 가로로 두고 각도 메모) — 1배에서 굵기 확인용
    line = fx["concept_telegraph_line"][0]["any"][0].im
    for i in range(6):
        put(line, 100 + i * 16, 100 - 8)
    # 패널 2: 화면 섬광 오버레이(거합 f1 시각, X1 알파 0.18) 를 입힌 같은 장면
    flash = scene.copy()
    ov = Image.new("RGBA", scene.size, X1[:3] + (46,))
    flash.alpha_composite(ov)
    out = Image.new("RGB", (scene.width * 3 + 24 + scene.width * 2 + 16, scene.height * 3 + 60), (24, 24, 28))
    d = ImageDraw.Draw(out)
    label(d, (8, 4), "mock fight 1x (left: real size, right: x3) — iai concept f2 on player attack f1, dummy hurt + hit_burst, boss + closing circle f4, archer + aura f1, telegraph_line x5", bold=True)
    out.paste(scene.convert("RGB"), (8, 24))
    label(d, (8, 28 + scene.height), "with screen flash overlay (incandescent X1 @ alpha 0.18, iai f1 40ms)")
    out.paste(flash.convert("RGB"), (8, 44 + scene.height))
    out.paste(scaled(scene.convert("RGB"), 3), (scene.width + 24, 24))
    out.save(os.path.join(HERE, "preview_mock_fight.png"))


# ============================================================ main
def main():
    fx = {}
    fx["concept_katana_slash"] = (katana_slash_frames(), DIRS, 48, 48, [40, 50, 60, 70, 90], (24, 34))
    fx["concept_iai"] = (iai_frames(), DIRS, 64, 64, [40, 40, 60, 80, 100, 120, 140], (32, 42))
    fx["concept_wide"] = (wide_frames(), DIRS, 96, 96, [40, 50, 70, 90, 110, 140, 160], (48, 58))
    fx["concept_zangetsu"] = (zangetsu_frames(), DIRS, 64, 64, [75, 75, 75, 75], (32, 42))
    fx["concept_quake_bolt"] = (quake_bolt_frames(), ["any"], 64, 64, [40, 50, 70, 90, 110, 130], (32, 40))
    fx["concept_assassin"] = (assassin_frames(), ["any"], 48, 48, [40, 50, 60, 80, 110], (24, 24))
    fx["concept_heavyarrow_bolt"] = (heavyarrow_bolt_frames(), ["any"], 48, 48, [40, 50, 60, 80, 110], (24, 34))
    fx["concept_hit_burst"] = (hit_burst_frames(), ["any"], 24, 24, [40, 40, 40, 50], (12, 12))
    fx["concept_telegraph_line"] = (telegraph_line_frames(), ["any"], 16, 16, [120, 120], (0, 8))
    fx["concept_telegraph_circle"] = (telegraph_circle_frames(), ["any"], 64, 64, [100] * 6, (32, 32))
    fx["concept_telegraph_aura"] = (telegraph_aura_frames(), ["any"], 64, 64, [100] * 4, (32, 32))

    extra = {
        "concept_katana_slash": dict(anchor="player_pivot", spawn="attack_frame2", depth="above", weapon="katana",
                                     secondary="fx.weapons.katana", trail="system trail: W1 @ 0.6 → 0, 120ms, from f2",
                                     note="기본 베기 새 언어: 본 띠(W0·W2·W3·X1 코어·W3·W1) + 바깥 잔상 겹 1프레임 지연. f0 예비 코어선, f4 꼬리(트레일 인계)."),
        "concept_iai": dict(anchor="player_pivot", spawn="attack_frame2", depth="above", weapon="katana", secondary="fx.weapons.katana",
                            flash="screen flash X1 alpha 0.18 for 40ms at f1", shake="2px 60ms at f1", trail="W1 @ 0.7 → 0, 180ms, from f2",
                            note="거합: 3겹(본·바깥 +1f·안쪽 +2f) + f1 백열 섬광 프레임 + f2 적중 광선 3. f4~f6 는 잔월 띠의 시작 모양."),
        "concept_wide": dict(anchor="player_pivot", spawn="attack_frame2", depth="above", weapon="katana", secondary="fx.weapons.katana",
                             flash="screen flash X1 alpha 0.22 for 40ms at f1", shake="3px 80ms at f1", trail="W1 @ 0.7 → 0, 220ms, from f2",
                             note="만월: 거합 3겹 + 안쪽 r21 달무리가 f3 에서 닫힌 보름달(백열 점선)로. 96 캔버스."),
        "concept_zangetsu": dict(anchor="player_pivot", spawn="after_iai", depth="below", weapon="katana", secondary="fx.weapons.katana",
                                 note="잔월: 어두운 3띠 + 띠 사이 번개 토막 + 도는 글린트(X0). 4f = 300ms 틱, f0 = 틱 순간."),
        "concept_quake_bolt": dict(anchor="hitbox_center", spawn="hit_judge", depth="below", weapon="greatsword", secondary="fx.weapons.greatsword",
                                   flash="screen flash W3 alpha 0.16 for 40ms at f1", shake="4px 120ms at f1",
                                   pivotNote="피벗 (32,40) = 바닥 타격점. 낙뢰는 캔버스 위 가장자리에서 내려온다 (any — 회전 없음).",
                                   note="대검 파쇄→지진: 낙뢰(3겹 번개 + 가지) → 타격 섬광 → 세로 0.6 압축 링 r8→16→24 + 방사 균열(용암 W2 → 식어서 W1/W0) + 재 G06/G09. f4 = 2단 판정(220ms)."),
        "concept_assassin": dict(anchor="hitbox_center", spawn="hit", depth="above", weapon="dagger", secondary="fx.weapons.dagger",
                                 note="단검 암살: 바닥 웅덩이(W0) + 그림자 분신 3(player idle 실루엣, W0→W1/W2 줄무늬)이 모여들고 교차 섬광 2줄(3겹) → 분신이 세로 줄무늬로 흩어짐. 층 강조 27/25/24 는 불티만."),
        "concept_heavyarrow_bolt": dict(anchor="hitbox_center", spawn="hit", depth="above", weapon="bow", secondary="fx.weapons.bow",
                                        flash="screen flash W3 alpha 0.14 for 40ms at f1", shake="2px 60ms",
                                        pivotNote="피벗 (24,34) = 적중점. 번개는 캔버스 위 가장자리에서 떨어진다 (any — 회전 없음).",
                                        note="활 중시: 번개 낙하(3겹 + 가지 2) → 적중 십자(X0) + 링 r6 + 바깥 가지 번개 3 → 점선 잔광 + 링 r11 → 꼬리."),
        "concept_hit_burst": dict(anchor="hitbox_center", spawn="hit", depth="above", weapon="any",
                                  note="공통 적중: 쏟아지는 광선 6갈래(18 테두리 · 26 몸 · X0/X1 코어, 지그재그). 무기 보조색 없음 → 어떤 무기와도 겹친다. hit_spark 대체 후보."),
        "concept_telegraph_line": dict(anchor="hitbox_center", spawn="telegraph", depth="below", tile=True, rotate=True, drawnFacing="right", scale="allowed",
                                       pivotNote="피벗 (0,8) = 선 시작(공격자). 두께 4px(5~10행 중 6~9), 코어 2px 가 x 방향으로 흐른다(프레임당 8px). TileSprite 폭 = 사거리.",
                                       note="굵고 선명한 예고 선. 층 램프 18/22/24/25/27 만 (보조색 없음)."),
        "concept_telegraph_circle": dict(anchor="hitbox_center", spawn="telegraph", depth="below", progressDriven=True, scale="allowed",
                                         pivotNote="피벗 (32,32) = 범위 중심. 범위 링 r22 (지름 44) 기준, 실제 반지름 R 이면 scale = R/22. frame = min(5, floor(progress*6)).",
                                         note="닫히는 원: 바깥 점선 링이 r31→r22 로 수렴, 범위 링(4px, 18+22→26)이 밝아지다 f5 에서 백열 점선. 중심 십자가 자람. 보조색 없음."),
        "concept_telegraph_aura": dict(anchor="hitbox_center", spawn="telegraph", depth="below", scale="allowed", followsTarget=True,
                                       pivotNote="피벗 (32,32) = 공격자 몸 중심. 적 히트박스 중심에 붙어 따라감.",
                                       note="수렴 오라: 12줄 토막이 r30→r8 로 흘러들어오며 밝아짐(19→25, 끝 27 점) + 맥동 코어. 4f 루프, 위상 1/4 씩 → 이음새 없음. 돌진·대기술 예고용."),
    }
    ok = True
    for name, (fbd, dirs, w, h, durs, pivot) in fx.items():
        loop = name in ("concept_zangetsu", "concept_telegraph_line", "concept_telegraph_aura")
        save_sheet(name, fbd, dirs, w, h, durs, loop, pivot, extra[name])
        ok &= color_report(name, fbd, wid=extra[name].get("weapon") if extra[name].get("weapon") not in (None, "any") else None)
    print("ALL OK" if ok else "CHECK above")
    preview_concept(fx)
    preview_mock_fight(fx)
    print("->", OUT_FX, "/", HERE)


if __name__ == "__main__":
    main()
