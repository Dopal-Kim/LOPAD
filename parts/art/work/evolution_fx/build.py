#!/usr/bin/env python3
# [53라운드 보관] 이 스크립트가 미리보기·목업·마스크 입력으로 읽던 구 시트(assets/sprites/player/player_*, player/v2/*, enemies/{dummy,archer,charger}_*, enemies/v2/*, weapons/katana_* 중 아이콘 외, weapons/v2/*)는 삭제됨 — 해당 단계는 재실행 시 FileNotFoundError.
"""LOPAD 35라운드 3단계: 2차 진화 전용 이펙트 16종 + 보조 동작·대쉬 연출 7종 — 단일 소스.

실행: python3 parts/art/work/evolution_fx/build.py
입력: parts/art/palette/lopad.json, assets/sprites/player/player_idle.png·player_dash.png (실루엣 마스크·미리보기), enemies/dummy_idle.png (미리보기)
산출 (assets/sprites/fx/, 전부 새 파일 — 기존 fx 는 손대지 않는다):
  [A. 2차 진화]  wide 64 4dir 6f / zangetsu 48 4dir 4f 루프 / longinvuln 32 4dir 4f / dashcrit 24 any 4f
                 quake 64 any 6f / pulverize 48 any 4f / ironwall 32 4dir 3f / giant 32x40 any 4f 루프
                 dance 32 4dir 6f / bleed 16 any 4f 루프 / afterimage 24 4dir 4f / assassin 32 any 4f
                 flash 24x8 any 4f 루프 / heavyarrow 16x8 any 1f + heavyarrow_hit 24 any 3f / rain 24 any 4f / seek 16 any 4f 루프
  [B. 보조 동작] parry_flash 32 any 4f / guard_wave 48x24 4dir 4f / shadowstep_ghost 16x24 4dir 3f (무채)
                 aim_charge 24 any 6f / aim_line 8x2 any 1f tile / dash_dust 16x8 4dir 3f / dash_trail 16x24 4dir 3f (무채)
  미리보기: parts/art/work/evolution_fx/preview_evolution.png, preview_secondary.png, preview_1x.png

설계 메모
  - 전부 1층 '잔' 호박 램프(인덱스 16~27)로 그리고 시스템이 층 램프로 스왑. 색 예산 무채 <=4 + 강조 <=8 (이펙트 하나 기준).
  - 1차 이펙트와의 구분: 2차는 '같은 계열 + 한 겹 더' — 만월은 거합보다 큰 호 + 안쪽 달무리, 잔월은 거합 반지름 그대로 남는 띠,
    지진은 파쇄 링이 두 번, 난무는 쌍격 호가 셋, 섬광은 관통 꼬리보다 길고 밝다.
  - 주인공 실루엣이 필요한 것(허보·잔상·그림자 걸음·대쉬 잔상)은 player_dash/idle PNG 의 알파를 마스크로 쓴다 (그림 재사용, 복제 아님).
  - 반투명 0, 고립 픽셀 0 (불티는 2px 쌍). 캔버스 유틸은 combat_fx/build.py 와 같은 규약.
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OUT_FX = os.path.join(ROOT, "assets", "sprites", "fx")
PLAYER = os.path.join(ROOT, "assets", "sprites", "player")
ENEMIES = os.path.join(ROOT, "assets", "sprites", "enemies")
os.makedirs(OUT_FX, exist_ok=True)

with open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8") as fp:
    PAL = json.load(fp)
GRAY = PAL["gray"]
RAMP = PAL["floors"][0]["ramp"]
DIRS = ["down", "up", "left", "right"]
DVEC = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}
FACE = {"right": 0, "down": 90, "left": 180, "up": 270}
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
FLOOR_BG = (0x21, 0x22, 0x24, 255)  # G02 (지시: 미리보기 바닥 G02)
PALETTE_NOTE = "parts/art/palette/lopad.json (gray + floor 1 accent slots 16-27, runtime swap)"
# 1차 거합/베기 호와 같은 방향 규약 (weapons/build.py SWEEP)
SWEEP = {"down": (-20, 200), "up": (160, 380), "right": (-100, 80), "left": (280, 100)}


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def G(i):
    return hx(GRAY[i])


def C(i):
    """강조 램프 인덱스 16~27."""
    return hx(RAMP[i - 16])


# ============================================================ 캔버스 유틸
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.im.load()

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            self.p[x, y] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            v = self.p[x, y]
            return v if v[3] else None
        return None

    def line(self, x0, y0, x1, y1, c):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        x, y = x0, y0
        while True:
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
        """반지름 r 고리 (ky 로 세로 압축 타원). a0..a1 각도 제한, dash=(on,off) 각도 단위, phase 각도 오프셋."""
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

    def arc(self, cx, cy, a0, a1, t0, t1, r_mid, thick, colors, head=0.75, head_boost=1, min_t=0.9, r_curve=0.0):
        """호 띠 (weapons/build.py 와 동일). 각도 a0→a1, 구간 [t0,t1], 두께는 양 끝에서 가늘어진다. colors 안쪽→바깥쪽."""
        span = a1 - a0
        aspan = abs(span)
        for y in range(self.h):
            for x in range(self.w):
                dx, dy = x - cx, y - cy
                r = math.hypot(dx, dy)
                if r < r_mid - thick - 2 or r > r_mid + thick + 2 + abs(r_curve):
                    continue
                th = math.degrees(math.atan2(dy, dx))
                d = (th - a0) % 360 if span > 0 else (a0 - th) % 360
                if d > aspan:
                    continue
                t = d / aspan
                if t < t0 or t > t1:
                    continue
                s = (t - t0) / max(1e-6, (t1 - t0))
                tk = max(min_t, thick * math.sin(math.pi * s) ** 0.55)
                rm = r_mid + r_curve * t
                rin, rout = rm - tk / 2.0, rm + tk / 2.0
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
        """2픽셀 불티 (고립 금지)."""
        x, y = int(round(x)), int(round(y))
        self.px(x, y, c)
        self.px(x + (1 if horiz else 0), y + (0 if horiz else 1), c)

    def mask_paste(self, mask, ox, oy, color_fn):
        """mask: 16x24 RGBA 플레이어 프레임. 알파 픽셀마다 color_fn(x, y, (r,g,b)) 색을 찍는다 (None 이면 건너뜀)."""
        mp = mask.load()
        for y in range(mask.height):
            for x in range(mask.width):
                v = mp[x, y]
                if v[3]:
                    c = color_fn(x, y, v[:3])
                    if c is not None:
                        self.px(ox + x, oy + y, c)

    def outline_of(self, mask, ox, oy, c, keep_inside=False):
        """마스크 실루엣의 바깥 테두리(투명 이웃 4방향이 있는 픽셀)를 c 로."""
        mp = mask.load()
        W, H = mask.width, mask.height

        def a(x, y):
            return 0 <= x < W and 0 <= y < H and mp[x, y][3] > 0
        for y in range(H):
            for x in range(W):
                if a(x, y) and (not a(x - 1, y) or not a(x + 1, y) or not a(x, y - 1) or not a(x, y + 1)):
                    self.px(ox + x, oy + y, c)

    def squash_y(self, cy, ky):
        """세로 압축 (탑다운 바닥 타원): 원 그림의 y 를 cy 기준 ky 배로 재배치."""
        im2 = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        p2 = im2.load()
        for y in range(self.h):
            sy = cy + (y - cy) / ky
            yy = int(round(sy))
            if 0 <= yy < self.h:
                for x in range(self.w):
                    if self.p[x, yy][3]:
                        p2[x, y] = self.p[x, yy]
        self.im, self.p = im2, p2

    def dash_pattern(self, mod=4, keep=(0,), seed=0):
        """띄엄띄엄: (x*3+y+seed) % mod 가 keep 에 없으면 지운다."""
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

    def copy(self):
        cv = Canvas(self.w, self.h)
        cv.im = self.im.copy(); cv.p = cv.im.load()
        return cv


def four_dirs_from_right(base):
    """정사각 캔버스 목록을 right 기준으로 4방향 회전. 90도 회전은 픽셀 밀도를 유지한다."""
    return {"right": base, "left": [cv.flip_x() for cv in base],
            "down": [cv.rot90(-1) for cv in base], "up": [cv.rot90(1) for cv in base]}


def player_frames(action, frame):
    """player_<action>.png 의 방향별 16x24 프레임 (실루엣 마스크·미리보기용)."""
    im = Image.open(os.path.join(PLAYER, "player_%s.png" % action)).convert("RGBA")
    return {d: im.crop((frame * 16, r * 24, frame * 16 + 16, r * 24 + 24)) for r, d in enumerate(DIRS)}


PDASH = player_frames("dash", 1)   # 돌진 프레임
PIDLE = player_frames("idle", 0)


# ============================================================ 시트 저장 · 검사
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


def color_report(name, frames_by_dir, gray_budget=4, accent_budget=8):
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
    gs = [G(i)[:3] for i in range(16)]
    cs = [C(i)[:3] for i in range(16, 28)]
    grays = sorted(gs.index(c) for c in cols if c in gs)
    accents = sorted(16 + cs.index(c) for c in cols if c in cs)
    other = [c for c in cols if c not in gs and c not in cs]
    flag = ""
    if len(grays) > gray_budget or len(accents) > accent_budget or other or iso or semi:
        flag = "  <-- CHECK"
    print("%-17s gray%s accent%s other=%d iso=%d semi=%d%s" % (name, grays, accents, len(other), iso, semi, flag))
    return flag == ""


# ============================================================ A. 칼
WIDE_SWEEP = {"down": (-50, 230), "up": (130, 410), "right": (-130, 110), "left": (320, 40)}


def wide_frames():
    """만월 64x64 4방향 6프레임. 거합(r19·220°)보다 큰 보름달 호(r26·280°) + 안쪽 달무리 띠. 피벗 (32,42)=발."""
    out = {}
    cx, cy, r, tk = 32, 32, 26.0, 8.0
    full = [C(22), C(24), C(26), C(27)]
    fade = [C(18), C(19), C(21), C(22), C(24)]
    rem = [C(17), C(18), C(19)]
    halo = [C(19), C(21)]
    for d in DIRS:
        a0, a1 = WIDE_SWEEP[d]
        frames = []
        seq = [
            dict(t=(0.0, 0.3), th=tk * 0.8, col=full, head=0.5, halo=None),
            dict(t=(0.0, 1.0), th=tk, col=full, head=0.7, halo=(0.05, 0.95)),
            dict(t=(0.0, 1.0), th=tk * 0.9, col=fade, head=0.8, halo=(0.1, 0.9)),
            dict(t=(0.05, 1.0), th=tk * 0.65, col=fade[:3], head=2, halo=(0.2, 0.8)),
            dict(t=(0.1, 0.95), th=tk * 0.45, col=rem[1:], head=2, halo=None),
            dict(t=(0.2, 0.9), th=tk * 0.3, col=rem[:2], head=2, halo=None, dash=True),
        ]
        for i, st in enumerate(seq):
            cv = Canvas(64, 64)
            cv.arc(cx, cy, a0, a1, st["t"][0], st["t"][1], r, st["th"], st["col"], head=st["head"], head_boost=1)
            if st["halo"]:
                # 달무리: 안쪽 가는 띠 (거합 반지름 19) — '보름달' 이중 테두리
                cv.arc(cx, cy, a0, a1, st["halo"][0], st["halo"][1], 19.0, 1.4, halo if i < 3 else [C(18), C(19)], head=2, min_t=1.0)
            if st.get("dash"):
                cv.dash_pattern(mod=4, keep=(1, 2, 3))
            if i == 1:
                # 머리 쪽 글린트 (순백 2px)
                ang = math.radians(a0 + (a1 - a0) * 0.82)
                cv.pair(cx + (r + 1) * math.cos(ang), cy + (r + 1) * math.sin(ang), G(15), horiz=(d in ("up", "down")))
            if i == len(seq) - 1:
                for k, (tt, col) in enumerate(((0.85, C(22)), (0.6, C(21)), (0.35, C(19)))):
                    ang = math.radians(a0 + (a1 - a0) * tt)
                    cv.pair(cx + (r + 3) * math.cos(ang), cy + (r + 3) * math.sin(ang), col, horiz=(k % 2 == 0))
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


def zangetsu_frames():
    """잔월 48x48 4방향 4프레임 루프. 거합 호(r19) 자리에 남는 어두운 띠 + 띠를 따라 도는 베기 글린트. 피벗 (24,34)."""
    out = {}
    cx, cy, r = 24, 24, 19.0
    band = [C(18), C(19), C(19)]
    band_tick = [C(19), C(21), C(21)]
    glint = [C(24), C(26), C(27)]
    for d in DIRS:
        a0, a1 = SWEEP[d]
        frames = []
        for f in range(4):
            cv = Canvas(48, 48)
            if f == 0:
                # 틱 순간: 바깥쪽 가는 점선 테두리 (규칙 점선, 노이즈 아님)
                cv.arc(cx, cy, a0, a1, 0.08, 0.92, r + 3.0, 1.0, [C(21)], head=2, min_t=1.0)
                cv.dash_pattern(mod=6, keep=(0, 1, 2, 3), seed=0)
            cv.arc(cx, cy, a0, a1, 0.05, 0.95, r, 3.2, band_tick if f == 0 else band, head=2, min_t=3.0)
            # 베기 글린트 2개가 띠를 따라 이동 (한 바퀴 = 4프레임 = 틱 300ms) — 띠 안의 밝은 토막
            for k in range(2):
                t0 = 0.05 + ((f * 0.1125 + k * 0.45) % 0.9)   # 4프레임에 0.45 이동 = 다음 글린트 자리 → 이음새 없음
                t1 = min(0.95, t0 + 0.12)
                cv.arc(cx, cy, a0, a1, t0, t1, r, 3.2, glint, head=2, min_t=3.0)
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


def longinvuln_frames():
    """허보 32x32 4방향 4프레임. 대쉬 중 몸이 비치는 잔상 윤곽: 실루엣 테두리(강조) + 성긴 속 + 뒤로 처지는 오프셋. 피벗 (16,26)."""
    out = {}
    ox, oy = 8, 3   # 16x24 를 (8,3) 에 — 발 (8,23) → (16,26)
    for d in DIRS:
        bx, by = -DVEC[d][0], -DVEC[d][1]
        m = PDASH[d]
        frames = []
        spec = [(C(25), C(20), 2, 0), (C(23), C(19), 3, 1), (C(21), None, 0, 2), (C(18), None, 0, 3)]
        for f, (oc, ic, mod, back) in enumerate(spec):
            cv = Canvas(32, 32)
            px_, py_ = ox + bx * back, oy + by * back
            if ic is not None:
                cv.mask_paste(m, px_, py_, lambda x, y, rgb, ic=ic, mod=mod: ic if (x + y) % mod == 0 else None)
            cv.outline_of(m, px_, py_, oc)
            if f == 3:
                cv.dash_pattern(mod=3, keep=(0, 1), seed=2)
            if f < 2:
                # 몸 뒤 짧은 속도선 2줄
                for o in (-3, 3):
                    sx = 16 + (o if d in ("up", "down") else 0) + bx * 7
                    sy = 14 + (o if d in ("left", "right") else 0) + by * 7
                    cv.line(sx, sy, sx + bx * (4 - f), sy + by * (4 - f), C(22) if f == 0 else C(20))
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


def dashcrit_frames():
    """급소 24x24 any 4프레임. 대쉬 베기 적중점에 꽂히는 점광: 흰 점 → 십자 + 마름모 → 바깥 마름모 점선 → 조각. 피벗 (12,12)."""
    cx, cy = 12, 12
    frames = []
    for f in range(4):
        cv = Canvas(24, 24)
        def diamond(rr, c):
            cv.line(cx + rr, cy, cx, cy - rr, c); cv.line(cx, cy - rr, cx - rr, cy, c)
            cv.line(cx - rr, cy, cx, cy + rr, c); cv.line(cx, cy + rr, cx + rr, cy, c)
        if f == 0:
            cv.disc(cx, cy, 2.0, C(27)); cv.ring(cx, cy, 3.5, C(25), 1.2)
            for a in (45, 135, 225, 315):
                cv.ray(cx, cy, a, 3, 5, C(24))
        elif f == 1:
            cv.disc(cx, cy, 1.5, C(27))
            for a in (0, 90, 180, 270):
                cv.ray(cx, cy, a, 2, 8, C(26))
                cv.ray(cx, cy, a, 2, 5, C(27))
            for a in (45, 135, 225, 315):
                cv.ray(cx, cy, a, 3, 5, C(24))
            diamond(6, C(24))
        elif f == 2:
            cv.disc(cx, cy, 1.0, C(26))
            for a in (0, 90, 180, 270):
                cv.ray(cx, cy, a, 6, 10, C(22))
            diamond(9, C(21))
            cv.dash_pattern(mod=4, keep=(0, 1, 2), seed=1)
            cv.disc(cx, cy, 1.0, C(26))
        else:
            for a in (0, 90, 180, 270):
                cv.ray(cx, cy, a, 9, 11, C(19))
            cv.pair(cx + 7, cy - 7, C(19)); cv.pair(cx - 8, cy + 7, C(19), horiz=False)
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


# ============================================================ A. 대검
def quake_frames():
    """지진 64x64 any 6프레임. 파쇄 링 1단(f0~2) → 220ms 뒤 2단 링(f3~5, 1.6배) + 바닥 균열이 남는다. 피벗 (32,32)."""
    cx, cy = 32, 32
    frames = []
    cracks_keep = []  # (angle, r0, r1) 누적 균열

    JIT = [0, 11, -7, 5, -12, 8, 3, -9, 13, -4]       # 각도 흩뜨림 (결정적)
    LEN = [1.0, 0.55, 0.8, 0.45, 0.9, 0.6, 0.7, 0.5, 0.85, 0.4]

    def crack(cv, k, n, r0, r1, col, jitter=0):
        ang = k * 360.0 / n + 15 + jitter + JIT[k % len(JIT)]
        r1 = r0 + (r1 - r0) * LEN[k % len(LEN)]
        a = math.radians(ang)
        x0, y0 = cx + r0 * math.cos(a), cy + r0 * math.sin(a) * 0.75
        x1, y1 = cx + r1 * math.cos(a), cy + r1 * math.sin(a) * 0.75
        # 꺾인 금: 중간점을 옆으로 1~2px, 끝에 가지 하나
        xm, ym = (x0 + x1) / 2 + (2 if k % 2 else -1), (y0 + y1) / 2 + (1 if k % 3 == 0 else 0)
        cv.line(x0, y0, xm, ym, col); cv.line(xm, ym, x1, y1, col)
        if k % 2 == 0 and r1 - r0 > 8:
            cv.line(xm, ym, xm + (2 if k % 4 else -2), ym + 1, col)

    seq = [
        dict(ring=(6, 3.0, [C(24), C(27)]), ring2=None, cracks=(0, 0, 0), dash=False, debris=0),
        dict(ring=(13, 3.2, [C(22), C(24), C(26)]), ring2=None, cracks=(6, 6, 15), dash=False, debris=0),
        dict(ring=(19, 2.4, [C(19), C(21), C(22)]), ring2=None, cracks=(6, 6, 20), dash=False, debris=1),
        dict(ring=(22, 1.4, [C(17), C(18)]), ring2=(8, 3.6, [C(24), C(27)]), cracks=(6, 6, 22), dash=True, debris=1),
        dict(ring=None, ring2=(18, 3.6, [C(22), C(24), C(26)]), cracks=(10, 5, 27), dash=False, debris=2),
        dict(ring=None, ring2=(28, 2.2, [C(18), C(19)]), cracks=(10, 5, 30), dash=True, debris=3),
    ]
    for i, st in enumerate(seq):
        cv = Canvas(64, 64)
        for key in ("ring", "ring2"):
            if st[key]:
                r, th, col = st[key]
                cv.arc(cx, cy, 0, 360, 0, 1, r, th, col, head=2, min_t=th)
        cv.squash_y(cy, 0.75)
        if st["dash"]:
            cv.dash_pattern(mod=5, keep=(2, 3, 4), seed=i)
        n, r0, r1 = st["cracks"]
        for k in range(n):
            col = C(21) if i in (1, 4) else (C(19) if i in (2, 3) else C(18))
            crack(cv, k, n, r0 if k < 6 else r0 + 6, r1 if k < 6 else r1 - 4, col, jitter=(7 if k >= 6 else 0))
        if i == 0:
            cv.disc(cx, cy, 1.6, C(27))
        if i == 3:
            cv.disc(cx, cy, 1.2, C(27))
        # 파편·먼지: 2px 쌍 (무채 G06/G09)
        dust = [(cx - 9, cy - 7, G(9)), (cx + 10, cy + 6, G(9)), (cx + 7, cy - 11, G(6)), (cx - 12, cy + 9, G(6)),
                (cx - 20, cy - 4, G(9)), (cx + 21, cy + 3, G(6)), (cx + 16, cy - 14, G(9)), (cx - 15, cy + 13, G(6))]
        for k in range(min(len(dust), st["debris"] * 3)):
            x, y, c = dust[k]
            spread = 1 + i * 0.6
            cv.pair(cx + (x - cx) * spread / 1.6, cy + (y - cy) * spread / 1.6, c, horiz=(k % 2 == 0))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def pulverize_frames():
    """분쇄 48x48 any 4프레임. 충격파 링 + 바깥으로 튀는 쐐기 파편 8개 + 투사체가 지워지는 X 표시. 피벗 (24,24)."""
    cx, cy = 24, 24
    frames = []
    for f in range(4):
        cv = Canvas(48, 48)
        ring = [(7, 3.0, [C(26), C(27)]), (13, 2.4, [C(22), C(24)]), (19, 1.6, [C(19), C(21)]), (22, 1.0, [C(17), C(18)])][f]
        cv.arc(cx, cy, 0, 360, 0, 1, ring[0], ring[1], ring[2], head=2, min_t=ring[1])
        if f >= 2:
            cv.dash_pattern(mod=4, keep=(1, 2), seed=f)
        # 쐐기 파편: 2px 폭 짧은 선, 바깥으로 이동
        s0, s1, cols = [(8, 11, (C(26), C(24))), (12, 17, (C(24), C(22))), (18, 22, (C(22), C(21))), (22, 24, (C(19), C(18)))][f]
        for k in range(8):
            ang = k * 45 + 22
            a = math.radians(ang)
            nx, ny = -math.sin(a), math.cos(a)
            cv.ray(cx, cy, ang, s0, s1, cols[0])
            cv.ray(cx + nx, cy + ny, ang, s0, s1 - 1, cols[1])
            if f in (1, 2):
                cv.px(int(round(cx + (s1 + 1) * math.cos(a))), int(round(cy + (s1 + 1) * math.sin(a))), C(27) if f == 1 else C(24))
        # X 표시 (투사체 소멸) — 축 4방향 r 15~17
        if f >= 1:
            xc = [C(27), C(26), C(22), C(19)][f]
            rr = [0, 15, 17, 18][f]
            for ang in (0, 90, 180, 270):
                a = math.radians(ang)
                px_, py_ = int(round(cx + rr * math.cos(a))), int(round(cy + rr * math.sin(a)))
                cv.line(px_ - 2, py_ - 2, px_ + 2, py_ + 2, xc); cv.line(px_ - 2, py_ + 2, px_ + 2, py_ - 2, xc)
        if f == 0:
            cv.disc(cx, cy, 1.5, C(27))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def ironwall_frames():
    """철벽 32x32 4방향 3프레임. 가드 반격 순간 전방에 서는 벽 섬광 (세로 띠 + 바깥 물결). right 기준 그리고 회전. 피벗 (16,22)."""
    cx, cy = 16, 16
    base = []
    for f in range(3):
        cv = Canvas(32, 32)
        wx = cx + 9
        if f == 0:
            for dy in range(-9, 10):
                cv.px(wx, cy + dy, C(27)); cv.px(wx - 1, cy + dy, C(25)); cv.px(wx + 1, cy + dy, C(25))
            cv.px(wx, cy - 10, C(25)); cv.px(wx, cy + 10, C(25))
            cv.line(wx - 5, cy - 3, wx - 2, cy - 3, C(24)); cv.line(wx - 5, cy + 3, wx - 2, cy + 3, C(24))
            cv.pair(wx - 1, cy, C(27))
        elif f == 1:
            for dy in range(-11, 12):
                cv.px(wx, cy + dy, C(26)); cv.px(wx - 1, cy + dy, C(24)); cv.px(wx + 1, cy + dy, C(24))
                cv.px(wx - 2, cy + dy, C(22)); cv.px(wx + 2, cy + dy, C(22))
            for dy in range(-9, 10):
                if dy % 3 != 1:
                    cv.px(wx + 4, cy + dy, C(22))
                if dy % 4 == 0:
                    cv.px(wx + 6, cy + dy, C(19)); cv.px(wx + 6, cy + dy + 1, C(19))
            cv.line(wx - 6, cy - 5, wx - 3, cy - 5, C(22)); cv.line(wx - 6, cy + 5, wx - 3, cy + 5, C(22))
            cv.line(wx - 4, cy, wx - 3, cy, C(24))
        else:
            for dy in range(-10, 11):
                if dy % 3 != 2:
                    cv.px(wx, cy + dy, C(21))
                if dy % 4 == 1:
                    cv.px(wx + 5, cy + dy, C(18)); cv.px(wx + 5, cy + dy + 1, C(18))
            cv.pair(wx + 1, cy - 7, C(19)); cv.pair(wx + 1, cy + 7, C(19))
        cv.despeckle8()
        base.append(cv)
    return four_dirs_from_right(base)


def giant_frames():
    """거인 32x40 any 4프레임 루프. 공격 중 슈퍼아머 오라: 발밑 타원 고리(도는 밝은 토막) + 몸 양옆에서 솟는 불빛 기둥. 피벗 (16,36), 플레이어 아래."""
    cx, cy = 16, 36
    frames = []
    for f in range(4):
        cv = Canvas(32, 40)
        cv.ring(cx, cy, 13, C(19), 1.6, ky=0.4)
        cv.ring(cx, cy, 13, C(22), 1.6, ky=0.4, dash=(40, 50), phase=f * 22.5)
        cv.ring(cx, cy, 13, C(24), 1.0, ky=0.4, dash=(14, 76), phase=f * 22.5 + 13)
        cv.ring(cx, cy, 9, C(18), 1.2, ky=0.4, dash=(30, 30), phase=-f * 15)
        # 솟는 기둥: 몸 양옆 2px 폭 기둥 하나씩(길이 6, 위로 3px/프레임, 주기 12) + 바깥쪽 1px 희미한 줄
        for k, x in enumerate((5, 25)):
            period = 12
            off = (f * 3 + k * 6) % period
            y1 = cy - 3 - off
            L = 6
            for yy in range(y1 - L, y1 + 1):
                u = (y1 - yy) / float(L)
                c = C(24) if u < 0.35 else (C(22) if u < 0.7 else C(21))
                cv.px(x, yy, c); cv.px(x + 1, yy, C(22) if u < 0.35 else (C(21) if u < 0.7 else C(19)))
            cv.px(x, y1 - L - 1, C(25)); cv.px(x + 1, y1 - L - 1, C(24))
            y2 = y1 - period
            if y2 - 3 > 2:
                cv.line(x, y2, x, y2 - 3, C(19)); cv.line(x + 1, y2, x + 1, y2 - 3, C(18))
            xo = 2 if k == 0 else 29
            yo = cy - 6 - ((f * 3 + 6 + k * 3) % period)
            cv.line(xo, yo, xo, yo - 3, C(19))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


# ============================================================ A. 단검
def dance_frames():
    """난무 32x32 4방향 6프레임. 쌍격의 2중 호 → 3중 호 (r7.5 / r10.5 / r13), 두 번째는 반대 방향으로 긋는다. 피벗 (16,26)."""
    out = {}
    cx, cy = 16, 16
    full = [[C(24), C(26), C(27)], [C(24), C(26), C(27)], [C(22), C(24), C(27)]]
    fade = [C(19), C(21), C(22)]
    rem = [C(17), C(18)]
    for d in DIRS:
        a0, a1 = SWEEP[d]
        sw = [(a0, a1), (a1, a0), (a0, a1)]
        rr = [7.5, 10.5, 13.0]
        frames = []
        for f in range(6):
            cv = Canvas(32, 32)
            hit = f // 2           # 0,1,2
            ph = f % 2             # 0 = 긋는 중, 1 = 전체 호
            # 이전 호들은 잔재
            for h in range(hit):
                cv.arc(cx, cy, sw[h][0], sw[h][1], 0.5, 1.0, rr[h], 1.6 if h == hit - 1 else 1.2, fade if h == hit - 1 else rem, head=2)
            if ph == 0:
                cv.arc(cx, cy, sw[hit][0], sw[hit][1], 0.0, 0.6, rr[hit], 2.6, full[hit], head=0.5)
            else:
                cv.arc(cx, cy, sw[hit][0], sw[hit][1], 0.0, 1.0, rr[hit], 3.0 if hit == 2 else 2.6, full[hit], head=0.7)
            if f == 5:
                ang = math.radians(a1 - (a1 - a0) * 0.12)
                cv.pair(cx + 15 * math.cos(ang), cy + 15 * math.sin(ang), C(24))
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


def bleed_frames():
    """출혈 16x16 any 4프레임 루프(125ms x4 = 틱 500ms). 적 몸에서 떨어지는 핏방울 2줄 + 틱 순간 글린트. 피벗 (8,8)."""
    frames = []
    DK, MD, LT, GL, HI = C(17), C(18), C(19), C(22), C(24)
    for f in range(4):
        cv = Canvas(16, 16)
        for col_i, (x, ph) in enumerate(((4, 0), (10, 2))):
            k = (f + ph) % 4
            y = 3 + k * 3
            # 방울 2x3: 글린트 1px(22) + 본체(19/18) + 밑 그늘(17). 떨어지며 길어진다
            if k < 3:
                cv.px(x, y, GL); cv.px(x + 1, y, LT)
                cv.px(x, y + 1, LT); cv.px(x + 1, y + 1, MD)
                cv.px(x, y + 2, MD); cv.px(x + 1, y + 2, DK)
                if k >= 1:
                    cv.px(x, y + 3, DK)
                if k == 2:
                    cv.px(x + 1, y + 3, DK); cv.px(x, y + 4, DK)
            else:
                # 바닥 튐 (2px 쌍)
                cv.line(x - 1, 14, x + 2, 14, MD); cv.px(x - 1, 14, DK); cv.px(x + 2, 14, DK)
                cv.px(x, 13, LT); cv.px(x + 1, 13, LT)
        if f == 0:
            cv.px(7, 5, HI); cv.px(8, 5, HI); cv.px(8, 6, GL); cv.px(7, 6, GL)   # 틱 글린트
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def afterimage_frames():
    """잔상 24x24 4방향 4프레임. 대쉬 출발점에 남아 베는 분신: 실루엣 채움(강조 어두운 단) + 테두리 + 베기 사선. 피벗 (12,23)."""
    out = {}
    ox, oy = 4, 0
    for d in DIRS:
        m = PDASH[d]
        frames = []
        spec = [(C(20), C(22), C(24), 1), (C(19), C(21), C(27), 1), (C(18), C(19), C(22), 2), (None, C(17), None, 3)]
        for f, (fill, oc, sl, mod) in enumerate(spec):
            cv = Canvas(24, 24)
            if fill is not None:
                cv.mask_paste(m, ox, oy, lambda x, y, rgb, fill=fill, mod=mod: fill if (x + y) % mod == 0 else None)
            cv.outline_of(m, ox, oy, oc)
            if f == 3:
                cv.dash_pattern(mod=3, keep=(0, 1), seed=1)
            if sl is not None:
                # 베기 사선: 몸을 가로지르는 2줄 (방향에 따라 기울기 고정, 분신이 긋는 X)
                L = [7, 11, 9][f]
                cv.line(12 - L, 12 + L // 2, 12 + L, 12 - L // 2, sl)
                if f == 1:
                    cv.line(12 - L + 1, 12 + L // 2 + 1, 12 + L - 1, 12 - L // 2 + 1, C(24))
                if f == 2:
                    cv.dash_pattern(mod=4, keep=(0, 1, 2), seed=3)
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


def assassin_frames():
    """암살 32x32 any 4프레임. 그림자 걸음 직후 치명 베기: 바닥 그림자 웅덩이(G01/G02) + 대각선 섬광 베기. 피벗 (16,16)."""
    cx, cy = 16, 16
    frames = []
    for f in range(4):
        cv = Canvas(32, 32)
        sr = [7, 8, 6, 4][f]
        if sr:
            cv.disc(cx, cy + 6, sr, G(2), ky=0.45)
            cv.disc(cx, cy + 6, sr - 2, G(1), ky=0.45)
            if f == 1:
                cv.ring(cx, cy + 6, sr + 1.5, C(17), 1.0, ky=0.45)
        if f == 0:
            cv.disc(cx, cy, 1.2, C(27))
            cv.line(cx - 3, cy + 2, cx + 3, cy - 2, C(25))
        elif f == 1:
            cv.line(3, 27, 29, 3, C(27)); cv.line(3, 26, 28, 3, C(25)); cv.line(4, 27, 29, 4, C(25))
            cv.line(2, 24, 10, 17, C(22)); cv.line(22, 10, 30, 3, C(22))
            cv.pair(cx - 1, cy, C(27))
        elif f == 2:
            cv.line(5, 26, 28, 4, C(23))
            cv.dash_pattern(mod=4, keep=(0, 1, 2), seed=2)
            cv.disc(cx, cy + 6, 6, G(2), ky=0.45); cv.disc(cx, cy + 6, 4, G(1), ky=0.45)
            cv.pair(cx + 8, cy - 8, C(24))
        else:
            cv.disc(cx, cy + 6, 4, G(2), ky=0.45)
            cv.dash_pattern(mod=3, keep=(0, 1), seed=1)
            cv.pair(7, 22, C(19)); cv.pair(24, 7, C(19), horiz=False)
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


# ============================================================ A. 활
def flash_frames():
    """섬광 24x8 any 4프레임 루프. 관통(16x8)보다 길고 밝은 화살 꼬리: 순백 코어 + 4단 띠 + 끝 흔들림. 피벗 (22,4)=화살 중심."""
    frames = []
    for f in range(4):
        cv = Canvas(24, 8)
        L = [18, 20, 19, 17][f]
        cv.line(21, 4, 21 - L, 4, C(24))
        cv.line(21, 4, 21 - L + 5, 4, C(26))
        cv.line(21, 4, 21 - L + 10, 4, C(27))
        cv.line(20, 3, 20 - (L - 4), 3, C(22)); cv.line(20, 5, 20 - (L - 4), 5, C(22))
        cv.line(19, 3, 19 - (L - 11), 3, C(25)); cv.line(19, 5, 19 - (L - 11), 5, C(25))
        cv.line(18, 2, 18 - (L - 9), 2, C(21)); cv.line(18, 6, 18 - (L - 9), 6, C(21))
        # 끝 흔들림
        ty = 3 if f % 2 == 0 else 5
        cv.line(21 - L - 1, ty, 21 - L + 1, ty, C(21))
        cv.px(21 - L - 2, 4, C(19))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def heavyarrow_frames():
    """중시 화살 16x8 우향 1프레임 (rotate). 3폭 자루(G13/G8/G5) + 큰 촉(27/25) + 두 겹 깃(21/19). 피벗 (8,4)."""
    a = Canvas(16, 8)
    a.blit([
        "....",
        "aa..",
        ".aa.",
        "....",
        "....",
        ".bb.",
        "bb..",
        "....",
    ], 0, 0, {"a": C(21), "b": C(19)})
    a.line(2, 3, 11, 3, G(13)); a.line(2, 4, 11, 4, G(8)); a.line(3, 5, 11, 5, G(5))
    a.line(4, 3, 8, 3, C(25))
    a.blit([
        "..W.",
        ".WW.",
        "wWWW",
        ".WW.",
        "..W.",
    ], 11, 2, {"W": C(27), "w": C(25)})
    a.px(12, 1, C(25)); a.px(12, 6, C(25))
    return {"any": [a]}


def heavyarrow_hit_frames():
    """중시 적중 경직 먼지 24x24 any 3프레임: 충격 별(27/25) + 네 귀퉁이 먼지(G06/G09/G12) 퍼짐. 피벗 (12,12)."""
    cx, cy = 12, 12
    D, M, L = G(6), G(9), G(12)
    frames = []
    for f in range(3):
        cv = Canvas(24, 24)
        if f == 0:
            cv.disc(cx, cy, 1.6, C(27))
            for a in (0, 90, 180, 270):
                cv.ray(cx, cy, a, 2, 5, C(25))
            for dx, dy in ((-5, 3), (5, 3)):
                cv.disc(cx + dx, cy + dy, 1.6, M)
            cv.pair(cx - 6, cy - 1, L); cv.pair(cx + 5, cy - 1, L)
        elif f == 1:
            cv.ring(cx, cy, 5.5, C(22), 1.2, dash=(30, 30))
            cv.pair(cx - 1, cy, C(24))
            for dx, dy in ((-7, 4), (7, 4), (-5, -5), (5, -5)):
                cv.disc(cx + dx, cy + dy, 2.4, D)
                cv.disc(cx + dx - 1, cy + dy - 1, 1.4, M)
            cv.px(cx - 8, cy + 2, L); cv.px(cx - 7, cy + 2, L); cv.px(cx + 6, cy - 7, L); cv.px(cx + 7, cy - 7, L)
        else:
            for dx, dy in ((-9, 5), (9, 5), (-7, -7), (7, -7)):
                cv.disc(cx + dx, cy + dy, 1.6, D)
                cv.px(cx + dx - 1, cy + dy - 1, M)
            cv.pair(cx - 2, cy + 8, M); cv.pair(cx + 1, cy - 9, M)
            cv.pair(cx - 1, cy, C(19))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def rain_frames():
    """폭우 24x24 any 4프레임. 발사점에서 5갈래(±50°) 섬광 — 산탄(3갈래 ±24°)보다 넓고 길다. 피벗 (3,12), rotate."""
    frames = []
    ox, oy = 3, 12
    for f in range(4):
        cv = Canvas(24, 24)
        L = [7, 12, 16, 17][f]
        cols = [[C(27), C(25), C(24)], [C(26), C(24), C(22)], [C(22), C(21), C(21)], [C(18), C(17), C(17)]][f]
        for ang in (-50, -25, 0, 25, 50):
            s0 = 2 if f < 3 else 9
            c = cols[0] if ang == 0 else (cols[1] if abs(ang) == 25 else cols[2])
            cv.ray(ox, oy, ang, s0, L - (2 if abs(ang) == 50 else 0), c)
            if f in (1, 2):
                a = math.radians(ang)
                tip = L - (2 if abs(ang) == 50 else 0) + 1
                cv.px(int(round(ox + tip * math.cos(a))), int(round(oy + tip * math.sin(a))), cols[0])
        if f == 0:
            cv.disc(ox, oy, 1.8, C(27))
        if f == 1:
            cv.disc(ox, oy, 1.2, C(27)); cv.px(ox, oy - 2, C(25)); cv.px(ox, oy + 2, C(25))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def seek_frames():
    """추적 16x16 any 4프레임 루프. 유도 화살 꼬리: 꼬인 두 가닥 파동(22/24)이 뒤로 흐른다 + 교차점 글린트. 피벗 (13,8), rotate."""
    frames = []
    for f in range(4):
        cv = Canvas(16, 16)
        ph = f * math.pi / 2
        prev = {}
        for strand, (col, sgn) in enumerate(((C(24), 1), (C(22), -1))):
            pts = []
            for x in range(12, 0, -1):
                amp = 1.2 + (12 - x) * 0.22
                y = 8 + sgn * amp * math.sin(2 * math.pi * (12 - x) / 8.0 + ph)
                pts.append((x, int(round(y))))
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                cv.line(x0, y0, x1, y1, col if x0 > 4 else (C(21) if strand == 0 else C(19)))
            prev[strand] = pts
        # 교차점 글린트 (두 가닥 y 가 같은 x)
        for (x0, y0), (x1, y1) in zip(prev[0], prev[1]):
            if y0 == y1 and 3 < x0 < 12:
                cv.px(x0, y0, C(26))
        cv.px(12, 8, C(26)); cv.px(11, 8, C(26))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


# ============================================================ B. 보조 동작 · 대쉬
def parry_flash_frames():
    """패링 성공 32x32 any 4프레임. 흰 별 섬광 → 멈춘 듯 깨끗한 동심 고리(가는 선) → 점선 고리 → 조각. 피벗 (16,16)."""
    cx, cy = 16, 16
    frames = []
    for f in range(4):
        cv = Canvas(32, 32)
        if f == 0:
            cv.disc(cx, cy, 2.0, C(27))
            for a in (0, 90, 180, 270):
                cv.ray(cx, cy, a, 2, 7, G(15))
            for a in (45, 135, 225, 315):
                cv.ray(cx, cy, a, 2, 4, C(25))
        elif f == 1:
            cv.disc(cx, cy, 1.2, C(27))
            cv.ring(cx, cy, 5.5, C(25), 1.2)
            cv.ring(cx, cy, 10.5, C(23), 1.0)
            for a in (0, 90, 180, 270):
                cv.ray(cx, cy, a, 7, 9, G(15))
        elif f == 2:
            cv.ring(cx, cy, 8.5, C(22), 1.0)
            cv.ring(cx, cy, 13.5, C(21), 1.0, dash=(20, 10), phase=5)
            cv.pair(cx - 1, cy, C(24))
        else:
            cv.ring(cx, cy, 15.0, C(19), 1.0, dash=(12, 18), phase=0)
            cv.ring(cx, cy, 11.0, C(18), 1.0, dash=(8, 37), phase=10)
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def guard_wave_frames():
    """가드 밀쳐내기 48x24 4방향 4프레임. 발 피벗 (24,14) 에서 바라보는 쪽으로 퍼지는 반타원 충격파(세로 0.5 압축) + 먼지. 플레이어 아래."""
    out = {}
    cx, cy = 24, 14
    for d in DIRS:
        fa = FACE[d]
        frames = []
        for f in range(4):
            cv = Canvas(48, 24)
            r, th, cols = [(8, 2.6, (C(27), C(25))), (14, 2.6, (C(24), C(22))), (20, 2.0, (C(21), C(19))), (24, 1.2, (C(18), C(17)))][f]
            ky = 0.5
            cv.ring(cx, cy, r, cols[1], th, a0=fa - 75, a1=fa + 75, ky=ky)
            cv.ring(cx, cy, r - 0.6, cols[0], th * 0.6, a0=fa - 60, a1=fa + 60, ky=ky)
            if f == 3:
                cv.dash_pattern(mod=4, keep=(1, 2), seed=1)
            # 먼지 2px 쌍 (G09/G06) 파도 바깥 가장자리
            for k, da in enumerate((-45, 0, 45)):
                if f == 0 and k != 1:
                    continue
                a = math.radians(fa + da)
                rr = r + 2 + (f % 2)
                cv.pair(cx + rr * math.cos(a), cy + rr * math.sin(a) * ky, G(9) if f < 2 else G(6), horiz=(d in ("up", "down")) == (k == 1))
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


def gray_level(rgb):
    lum = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return G(2) if lum < 60 else (G(3) if lum < 140 else G(4))


def shadowstep_ghost_frames():
    """그림자 걸음 출발 잔상 16x24 4방향 3프레임. 주인공 실루엣을 G02~G04 로 눌러 찍고 흩어진다. 피벗 (8,23)."""
    out = {}
    for d in DIRS:
        m = PIDLE[d]
        frames = []
        for f in range(3):
            cv = Canvas(16, 24)
            if f == 0:
                cv.mask_paste(m, 0, 0, lambda x, y, rgb: gray_level(rgb))
            elif f == 1:
                cv.mask_paste(m, 0, 0, lambda x, y, rgb: (G(2) if gray_level(rgb) == G(2) else G(3)) if (y % 2 == 0 or (x + y) % 3 == 0) else None)
                cv.outline_of(m, 0, 0, G(2))
                cv.dash_pattern(mod=5, keep=(0, 1, 2, 3), seed=2)
            else:
                cv.mask_paste(m, 0, 1, lambda x, y, rgb: G(2) if (x + y) % 3 == 0 else None)
                cv.outline_of(m, 0, 1, G(3))
                cv.dash_pattern(mod=3, keep=(0, 1), seed=1)
                # 2px 쌍 보강: 발밑 그림자
                cv.line(4, 23, 11, 23, G(2))
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


def aim_charge_frames():
    """조준 차지 24x24 any 6프레임 (진행도 기반: frame = floor(progress*5)). 위에서 시계 방향으로 차는 고리, 마지막 = 완료 발광. 피벗 (12,12)."""
    cx, cy = 12, 12
    frames = []
    for f in range(6):
        cv = Canvas(24, 24)
        cv.ring(cx, cy, 9, C(18), 1.0, dash=(10, 20))
        if f < 5:
            if f > 0:
                cv.ring(cx, cy, 9, C(22), 1.2, a0=-90, a1=-90 + 72 * f)
                a = math.radians(-90 + 72 * f)
                cv.px(int(round(cx + 9 * math.cos(a))), int(round(cy + 9 * math.sin(a))), C(25))
            cv.px(cx, cy - 9, C(24)); cv.px(cx, cy - 10, C(24))
            # 눈금 4개
            for a in (0, 90, 180, 270):
                cv.ray(cx, cy, a, 10, 11, C(20))
        else:
            cv.ring(cx, cy, 9, C(25), 1.6)
            cv.ring(cx, cy, 11, C(22), 1.0, dash=(15, 15), phase=7)
            for a in (0, 90, 180, 270):
                cv.ray(cx, cy, a, 10, 12, C(27))
            cv.disc(cx, cy, 1.2, C(27))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def aim_line_frames():
    """조준 궤적 점선 8x2 any 1프레임, tile+rotate. 4 on / 4 off, 위 줄 22, 아래 줄 20. 피벗 (0,1) = 선 시작."""
    cv = Canvas(8, 2)
    cv.line(0, 0, 3, 0, C(22)); cv.line(0, 1, 3, 1, C(20))
    return {"any": [cv]}


def dash_dust_frames():
    """대쉬 출발 먼지 16x8 4방향 3프레임. 발 피벗 (8,6) 뒤쪽으로 퍼지는 먼지 구름(G06/G09/G12). 바닥 깊이."""
    out = {}
    D, M, L = G(6), G(9), G(12)
    for d in DIRS:
        bx, by = -DVEC[d][0], -DVEC[d][1]
        frames = []
        for f in range(3):
            cv = Canvas(16, 8)
            px_, py_ = 8, 6
            if d in ("left", "right"):
                # 옆: 뒤로 길게 — 큰 뭉치(D) 안에 밝은 뭉치(M), 끝에 L 쌍
                cv.disc(px_ + bx * (2 + f * 2), py_ - 1 - f, 2.6 - f * 0.4, D, ky=0.75)
                cv.disc(px_ + bx * (5 + f * 2), py_ - 2 - f, 1.8 - f * 0.3, D, ky=0.75)
                cv.disc(px_ + bx * (2 + f * 2) - bx, py_ - 2 - f, 1.4 - f * 0.2, M, ky=0.75)
                cv.pair(px_ + bx * (6 + f * 2), py_ - 3 - f, L, horiz=True)
                if f < 2:
                    cv.pair(px_ + bx * (1 + f), py_, M, horiz=True)
            else:
                # 상하: 좌우로 퍼지는 두 뭉치 (뒤 = 위/아래로 1~2px)
                for sx in (-1, 1):
                    cv.disc(px_ + sx * (3 + f * 2), py_ + by * (1 + f), 2.4 - f * 0.4, D, ky=0.75)
                    cv.disc(px_ + sx * (2 + f * 2), py_ + by * (1 + f) - 1, 1.4 - f * 0.2, M, ky=0.75)
                    cv.pair(px_ + sx * (5 + f * 2) - (1 if sx < 0 else 0), py_ + by * (2 + f), L)
                if f == 0:
                    cv.pair(px_ - 1, py_, M)
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


def dash_trail_frames():
    """대쉬 잔상 16x24 4방향 3프레임 (무채). 돌진 실루엣을 이동 방향 줄무늬로 끊어 속도감만 남긴다. 피벗 (8,23)."""
    out = {}
    for d in DIRS:
        m = PDASH[d]
        horiz = d in ("left", "right")
        frames = []
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
            frames.append(cv)
        out[d] = frames
    return out


# ============================================================ 미리보기
def label(d, xy, text, col=(230, 230, 230)):
    d.text(xy, text, fill=col, font=FONT)


def scaled(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def cell_with_player(fx, name, d, f, below=None):
    """바닥 G02 위에 이펙트 프레임과 주인공을 얹은 1배 셀. player_pivot 앵커는 피벗에, 아니면 셀 왼쪽 아래에 크기 비교용."""
    fbd, dirs, w, h, pivot, extra = fx[name][1], fx[name][2], fx[name][3], fx[name][4], fx[name][5], fx[name][8]
    anchor = extra.get("anchor")
    below = extra.get("depth") == "below" if below is None else below
    pad = 10 if extra.get("followsPlayer") is False else 0
    cell = Image.new("RGBA", (max(w, 18) + 2 * pad, max(h, 26) + 2 * pad), FLOOR_BG)
    ox, oy = (cell.width - w) // 2, (cell.height - h) // 2
    pf = PIDLE[d if d in DIRS else "down"]
    if anchor == "player_pivot":
        ppos = (ox + pivot[0] - 8, oy + pivot[1] - 23)
        if extra.get("followsPlayer") is False:
            vx, vy = DVEC[d if d in DIRS else "right"]
            ppos = (ppos[0] + vx * 10, ppos[1] + vy * 8)
    else:
        ppos = (1, cell.height - 25)
    if not below:
        cell.alpha_composite(pf, ppos)
    cell.alpha_composite(fbd[d][f].im, (ox, oy))
    if below:
        cell.alpha_composite(pf, ppos)
    return cell


def block_rows(fx, names, k=3, title=""):
    """이름 목록을 한 행씩: 각 이펙트의 첫 방향(또는 down) 전 프레임 + 오른쪽에 1배 복사."""
    rows = []
    for name in names:
        dirs, durs = fx[name][2], fx[name][6]
        d = "down" if "down" in dirs else "any"
        cells = [cell_with_player(fx, name, d, f) for f in range(len(durs))]
        rows.append((name, cells, fx[name]))
    cw = max(c.width for _, cells, _ in rows for c in cells)
    ch = max(c.height for _, cells, _ in rows for c in cells)
    n_max = max(len(cells) for _, cells, _ in rows)
    gap = 3
    W = 150 + n_max * (cw * k + gap) + 12 + n_max * (cw + 2)
    H = 18 + sum(max(c.height for c in cells) * k + 20 for _, cells, _ in rows)
    img = Image.new("RGB", (W, H), (24, 24, 28))
    dr = ImageDraw.Draw(img)
    label(dr, (4, 2), title)
    y = 18
    for name, cells, v in rows:
        rh = max(c.height for c in cells) * k
        label(dr, (4, y + 2), "%s %dx%d" % (name, v[3], v[4]))
        label(dr, (4, y + 14), "%s %s" % ("/".join(v[2]) if len(v[2]) == 1 else "4dir", v[6]), (170, 170, 175))
        label(dr, (4, y + 26), "pv(%d,%d) %s%s" % (v[5][0], v[5][1], v[8].get("anchor", ""), " loop" if v[7] else ""), (170, 170, 175))
        x = 150
        for c in cells:
            img.paste(scaled(c, k).convert("RGB"), (x, y))
            x += cw * k + gap
        x = 150 + n_max * (cw * k + gap) + 12
        for c in cells:
            img.paste(c.convert("RGB"), (x, y + rh - c.height))
            x += cw + 2
        y += rh + 20
    return img


def dir_sheet(fx, name, k=3):
    """4방향 전 프레임 시트 블록 (주인공 얹음)."""
    v = fx[name]
    dirs, durs = v[2], v[6]
    cells = {d: [cell_with_player(fx, name, d, f) for f in range(len(durs))] for d in dirs}
    cw, ch = cells[dirs[0]][0].width * k, cells[dirs[0]][0].height * k
    gap = 3
    img = Image.new("RGB", (60 + len(durs) * (cw + gap), 16 + len(dirs) * (ch + gap)), (34, 34, 38))
    dr = ImageDraw.Draw(img)
    label(dr, (4, 1), "%s %dx%d %s" % (name, v[3], v[4], durs))
    for r, d in enumerate(dirs):
        label(dr, (4, 16 + r * (ch + gap) + ch // 2 - 6), d)
        for f, c in enumerate(cells[d]):
            img.paste(scaled(c, k).convert("RGB"), (60 + f * (cw + gap), 16 + r * (ch + gap)))
    return img


def stack(blocks, cols=2, bg=(24, 24, 28)):
    colw = [0] * cols
    coly = [8] * cols
    placed = []
    for i, b in enumerate(blocks):
        c = i % cols
        placed.append((c, coly[c], b))
        coly[c] += b.height + 6
        colw[c] = max(colw[c], b.width)
    xs = [8]
    for c in range(1, cols):
        xs.append(xs[-1] + colw[c - 1] + 8)
    img = Image.new("RGB", (xs[-1] + colw[-1] + 8, max(coly) + 8), bg)
    for c, y, b in placed:
        img.paste(b, (xs[c], y))
    return img


def preview_evolution(fx):
    groups = [("katana: wide / zangetsu / longinvuln / dashcrit", ["wide", "zangetsu", "longinvuln", "dashcrit"]),
              ("greatsword: quake / pulverize / ironwall / giant", ["quake", "pulverize", "ironwall", "giant"]),
              ("dagger: dance / bleed / afterimage / assassin", ["dance", "bleed", "afterimage", "assassin"]),
              ("bow: flash / heavyarrow(+hit) / rain / seek", ["flash", "heavyarrow", "heavyarrow_hit", "rain", "seek"])]
    top = [block_rows(fx, names, k=3, title=t + "   (x3, floor G02, player for scale; right = 1x)") for t, names in groups]
    sheets = [dir_sheet(fx, n) for n in ("wide", "zangetsu", "longinvuln", "ironwall", "dance", "afterimage")]
    img = stack(top, cols=1)
    img2 = stack(sheets, cols=2)
    out = Image.new("RGB", (max(img.width, img2.width), img.height + img2.height), (24, 24, 28))
    out.paste(img, (0, 0)); out.paste(img2, (0, img.height))
    out.save(os.path.join(HERE, "preview_evolution.png"))


def preview_secondary(fx):
    names = ["parry_flash", "guard_wave", "shadowstep_ghost", "aim_charge", "aim_line", "dash_dust", "dash_trail"]
    top = block_rows(fx, names, k=3, title="secondary actions / dash   (x3, floor G02; right = 1x)")
    sheets = [dir_sheet(fx, n) for n in ("guard_wave", "shadowstep_ghost", "dash_dust", "dash_trail")]
    img2 = stack(sheets, cols=2)
    out = Image.new("RGB", (max(top.width, img2.width), top.height + img2.height), (24, 24, 28))
    out.paste(top, (0, 0)); out.paste(img2, (0, top.height))
    out.save(os.path.join(HERE, "preview_secondary.png"))


def preview_1x(fx):
    """1배 가독성: 전 이펙트 첫 방향 프레임을 1배로 두고 전체를 2배만."""
    strips = []
    for name, v in fx.items():
        fbd, dirs, w, h = v[1], v[2], v[3], v[4]
        n = len(v[6])
        d = "down" if "down" in dirs else "any"
        st = Image.new("RGBA", (n * (w + 2) + 2, h + 2), FLOOR_BG)
        for c in range(n):
            st.alpha_composite(fbd[d][c].im, (2 + c * (w + 2), 1))
        strips.append((name, st))
    W = max(s.width for _, s in strips) + 130
    H = sum(s.height + 6 for _, s in strips) + 8
    img = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(img)
    y = 4
    for name, st in strips:
        label(d, (4, y + st.height // 2 - 6), name)
        img.paste(st.convert("RGB"), (126, y))
        y += st.height + 6
    scaled(img, 2).save(os.path.join(HERE, "preview_1x.png"))


# ============================================================ main
def main():
    fx = {}
    # name: (action, frames_by_dir, dirs, w, h, pivot, durations, loop, extra)
    # ---- A. 칼
    fx["wide"] = ("wide", wide_frames(), DIRS, 64, 64, (32, 42), [50, 60, 80, 100, 120, 140], False,
                  {"anchor": "player_pivot", "spawn": "attack_frame2", "depth": "above",
                   "note": "만월. 거합(iai) 대신 재생 (같은 시점·같은 피벗 규약, 캔버스만 64). 4~6프레임은 남는 궤적."})
    fx["zangetsu"] = ("zangetsu", zangetsu_frames(), DIRS, 48, 48, (24, 34), [75, 75, 75, 75], True,
                      {"anchor": "player_pivot", "spawn": "after_iai", "depth": "below",
                       "note": "잔월. 거합(iai) 재생이 끝난 자리(같은 피벗, 플레이어가 움직여도 그 자리 고정)에 루프. 한 바퀴 300ms = 틱 간격, 0프레임 = 틱 순간 밝음. 궤적 지속(1000ms) 끝나면 제거. 바닥 깊이."})
    fx["longinvuln"] = ("longinvuln", longinvuln_frames(), DIRS, 32, 32, (16, 26), [50, 70, 90, 110], False,
                        {"anchor": "player_pivot", "spawn": "dash_start", "depth": "above", "followsPlayer": True,
                         "note": "허보. 대쉬 시작에 플레이어를 따라다니며 1회(무적 연장 구간 표시). 실루엣 테두리만 빛나고 속은 성긴 격자 = 몸이 비침. batto 와 동시 재생 가능(batto 는 아래)."})
    fx["dashcrit"] = ("dashcrit", dashcrit_frames(), ["any"], 24, 24, (12, 12), [40, 50, 60, 70], False,
                      {"anchor": "hitbox_center", "spawn": "hit", "depth": "above",
                       "note": "급소. 대쉬 베기 적중 시 적중점에 crit_burst 대신(또는 위에) 재생. 점광이라 crit_burst(32, 방사선)보다 작고 날카롭다."})
    # ---- A. 대검
    fx["quake"] = ("quake", quake_frames(), ["any"], 64, 64, (32, 32), [50, 70, 100, 70, 100, 130], False,
                   {"anchor": "hitbox_center", "spawn": "hit_judge", "depth": "below",
                    "note": "지진. crush 대신 재생. 0~2프레임 = 1단 링(220ms), 3프레임부터 2단 링(1.6배) + 바닥 균열 유지. 시스템 2단 판정(220ms 뒤)과 3프레임 시작이 맞는다."})
    fx["pulverize"] = ("pulverize", pulverize_frames(), ["any"], 48, 48, (24, 24), [40, 60, 80, 100], False,
                       {"anchor": "hitbox_center", "spawn": "hit_judge", "depth": "below",
                        "note": "분쇄. crush 대신 재생. 쐐기 파편 + 축 4방향 X 표 = 투사체 소멸 표시. 실제로 지운 투사체 위치에는 hit_spark 를 겹쳐도 됨."})
    fx["ironwall"] = ("ironwall", ironwall_frames(), DIRS, 32, 32, (16, 22), [40, 60, 80], False,
                      {"anchor": "player_pivot", "spawn": "guard_release", "depth": "above",
                       "pivotNote": "피벗 (16,22): 캔버스 중심이 몸 중심(발에서 위로 6px)에 오도록. 벽은 몸 중심에서 바라보는 쪽 9px",
                       "note": "철벽. 가드 떼는(밀쳐내기+반격) 순간 바라보는 쪽 전방 9px 에 서는 벽 섬광. guard_wave 와 동시 재생(guard_wave 는 아래)."})
    fx["giant"] = ("giant", giant_frames(), ["any"], 32, 40, (16, 36), [90, 90, 90, 90], True,
                   {"anchor": "player_pivot", "spawn": "attack_start", "depth": "below", "followsPlayer": True,
                    "note": "거인. 공격 판정 시작부터 공격 애니 끝까지 플레이어 발 피벗에 루프(슈퍼아머 구간). 종료 조건 = attack 종료. 플레이어 아래 깊이."})
    # ---- A. 단검
    fx["dance"] = ("dance", dance_frames(), DIRS, 32, 32, (16, 26), [40, 40, 40, 40, 40, 40], False,
                   {"anchor": "player_pivot", "spawn": "attack_frame2", "depth": "above",
                    "note": "난무. twin 대신 재생. 0·2·4프레임 시작 = 1·2·3타(간격 80ms). 두 번째 호는 반대 방향으로 긋는다."})
    fx["bleed"] = ("bleed", bleed_frames(), ["any"], 16, 16, (8, 8), [125, 125, 125, 125], True,
                   {"anchor": "hitbox_center", "spawn": "hit", "depth": "above", "followsTarget": True,
                    "note": "출혈. 적중한 적의 히트박스 중심에 붙어 루프. 한 바퀴 500ms = 틱 간격, 0프레임 = 틱 글린트. 출혈 횟수 소진(재적중 시 갱신)되면 제거. 피 색 = 층 램프 17~19."})
    fx["afterimage"] = ("afterimage", afterimage_frames(), DIRS, 24, 24, (12, 23), [60, 80, 100, 120], False,
                        {"anchor": "player_pivot", "spawn": "dash_start", "depth": "below", "followsPlayer": False,
                         "note": "잔상. 대쉬 출발 위치(고정)에 분신 1회. 경로가 길면 중간점에도 하나 더 띄울 수 있음. gale 과 동시 재생 가능."})
    fx["assassin"] = ("assassin", assassin_frames(), ["any"], 32, 32, (16, 16), [40, 60, 80, 100], False,
                      {"anchor": "hitbox_center", "spawn": "hit", "depth": "above",
                       "note": "암살. 그림자 걸음 직후의 공격(3배)이 적중할 때 적중점에. 바닥 그림자 웅덩이(G01/G02) + 대각선 섬광 베기. crit_burst 와 겹쳐도 됨."})
    # ---- A. 활
    fx["flash"] = ("flash", flash_frames(), ["any"], 24, 8, (22, 4), [50, 50, 50, 50], True,
                   {"anchor": "projectile", "rotate": True, "drawnFacing": "right", "spawn": "loop_move", "depth": "below",
                    "note": "섬광. pierce 대신 화살 뒤에 루프(화살 중심 = 피벗). 24 길이 = 빨라진 화살(x1.5)에 맞춰 관통 꼬리보다 8px 길고 순백 코어."})
    fx["heavyarrow"] = ("heavyarrow", heavyarrow_frames(), ["any"], 16, 8, (8, 4), [0], False,
                        {"anchor": "projectile", "rotate": True, "drawnFacing": "right", "fps": 0, "spawn": "aimed_shot",
                         "note": "중시. 조준 사격 화살(bow_arrow_aimed) 대신 쓰는 무거운 화살 텍스처. 일반 화살은 그대로."})
    fx["heavyarrow_hit"] = ("heavyarrow_hit", heavyarrow_hit_frames(), ["any"], 24, 24, (12, 12), [50, 80, 110], False,
                            {"anchor": "hitbox_center", "spawn": "hit", "depth": "above",
                             "note": "중시 적중 경직 먼지. 중시 화살이 적중한 적의 히트박스 중심에 1회 (경직 600ms 시작)."})
    fx["rain"] = ("rain", rain_frames(), ["any"], 24, 24, (3, 12), [40, 50, 60, 70], False,
                  {"anchor": "projectile", "rotate": True, "drawnFacing": "right", "spawn": "shot",
                   "note": "폭우. scatter 대신 발사점(활 위치)에 발사 각도로 회전해 1회. 5갈래 ±50°."})
    fx["seek"] = ("seek", seek_frames(), ["any"], 16, 16, (13, 8), [60, 60, 60, 60], True,
                  {"anchor": "projectile", "rotate": True, "drawnFacing": "right", "spawn": "loop_move", "depth": "below",
                   "note": "추적. 유도 화살 뒤에 루프(화살 중심 = 피벗). 화살이 선회해도 회전 각도만 따라가면 꼬리가 휘어 보인다."})
    # ---- B. 보조 동작 · 대쉬
    fx["parry_flash"] = ("parry_flash", parry_flash_frames(), ["any"], 32, 32, (16, 16), [40, 60, 80, 100], False,
                         {"anchor": "hitbox_center", "spawn": "parry_success", "depth": "above",
                          "note": "패링 성공. 접점(적 공격 히트박스와 플레이어의 접점, 없으면 플레이어 몸 중심)에 1회. 히트스톱과 같이 걸면 1프레임이 멈춤 동안 보인다."})
    fx["guard_wave"] = ("guard_wave", guard_wave_frames(), DIRS, 48, 24, (24, 14), [50, 60, 70, 80], False,
                        {"anchor": "player_pivot", "spawn": "guard_release", "depth": "below",
                         "note": "가드 밀쳐내기. 가드 떼는 순간 발 피벗에, 바라보는 쪽으로 반타원 충격파(반경 24px ≈ 밀쳐내기 2.5칸의 60%, 나머지는 적의 넉백으로 읽힘). 바닥 깊이. 철벽이면 ironwall 과 동시."})
    fx["shadowstep_ghost"] = ("shadowstep_ghost", shadowstep_ghost_frames(), DIRS, 16, 24, (8, 23), [60, 80, 100], False,
                              {"anchor": "player_pivot", "spawn": "shadowstep_start", "depth": "below", "followsPlayer": False,
                               "note": "그림자 걸음 출발 잔상. 출발 위치(고정)에 플레이어가 보던 방향으로 1회. 무채(G02~G04)라 층 스왑 무관. 플레이어 아래 깊이(도착 직후 겹칠 일 없음)."})
    fx["aim_charge"] = ("aim_charge", aim_charge_frames(), ["any"], 24, 24, (12, 12), [100, 100, 100, 100, 100, 100], False,
                        {"anchor": "player_pivot", "spawn": "aim_charge", "depth": "above", "progressDriven": True,
                         "pivotNote": "피벗 (12,12) 를 플레이어 몸 중심(발 피벗에서 위로 11px)에 둔다",
                         "note": "조준 차지 게이지. 시간이 아니라 진행도: frame = min(5, floor(progress*5)); 0% 빈 고리 → 80% 4/5 → 100% 완료 발광(5프레임). 완료 즉시 발사되므로 5프레임은 1~2프레임(~60ms)만 보임. 취소 시 즉시 제거."})
    fx["aim_line"] = ("aim_line", aim_line_frames(), ["any"], 8, 2, (0, 1), [0], False,
                      {"anchor": "player_pivot", "rotate": True, "drawnFacing": "right", "tile": True, "fps": 0, "spawn": "aim_charge",
                       "pivotNote": "피벗 (0,1) = 선 시작(플레이어 몸 중심). TileSprite 폭 = 사거리, 회전 = 커서 각도",
                       "note": "조준 궤적 점선(4 on / 4 off). 차지 중 표시, 발사·취소 시 제거. 깊이 바닥."})
    fx["dash_dust"] = ("dash_dust", dash_dust_frames(), DIRS, 16, 8, (8, 6), [50, 70, 90], False,
                       {"anchor": "player_pivot", "spawn": "dash_start", "depth": "below", "followsPlayer": False,
                        "note": "대쉬 출발 먼지. 출발 위치(고정) 발 피벗에, 방향 = 대쉬 방향(먼지는 반대쪽으로 퍼짐). 바닥 깊이. 무채."})
    fx["dash_trail"] = ("dash_trail", dash_trail_frames(), DIRS, 16, 24, (8, 23), [40, 60, 80], False,
                        {"anchor": "player_pivot", "spawn": "dash_trail", "depth": "below", "followsPlayer": False,
                         "note": "대쉬 잔상(무채). 대쉬 중 40~50ms 마다 현재 위치에 하나씩 놓고 각자 180ms 뒤 소멸 (2~3개 겹침). 플레이어 아래 깊이. 발도술(batto)·질풍(gale) 과 겹쳐도 무채라 충돌 없음."})

    ok = True
    for name, v in fx.items():
        save_sheet(name, v[1], v[2], v[3], v[4], v[6], v[7], v[5], v[8], action=v[0])
        ok &= color_report(name, v[1])
    preview_evolution(fx)
    preview_secondary(fx)
    preview_1x(fx)
    print("ALL OK" if ok else "SOME CHECKS FAILED")


if __name__ == "__main__":
    main()
