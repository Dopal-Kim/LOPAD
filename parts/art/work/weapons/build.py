#!/usr/bin/env python3
"""LOPAD 4단계: 무기 4종 아이콘 · 손에 든 무기(공격 중 겹침) · 공격 이펙트 · 1차 진화 8종 이펙트 — 단일 소스.

실행: python3 parts/art/work/weapons/build.py
입력: parts/art/palette/lopad.json, assets/sprites/player/player_attack.png·player_idle.png (미리보기용)
산출:
  assets/sprites/weapons/<id>_icon.png/.json      16x16, 1프레임 (메뉴·HUD)
  assets/sprites/weapons/<id>_attack.png/.json    48x48, 4방향 x 4프레임. 주인공 attack 과 같은 프레임 번호로 겹친다.
                                                  피벗 (24,39) = 주인공 피벗 (8,23). 즉 주인공 16x24 프레임이 (16,16) 에 놓인 캔버스.
  assets/sprites/fx/<id>_slash.png/.json          32x32 4방향 x 4프레임 (katana/greatsword/dagger)
  assets/sprites/fx/bow_arrow.png / bow_arrow_aimed.png   8x8 / 12x6, 우향 1프레임 (시스템이 각도 회전)
  assets/sprites/fx/<진화id>.png/.json            iai 48 / batto 32 / crush 48 / weight 32x24 / twin 32 / gale 24 / pierce 16x8 / scatter 16
  parts/art/work/weapons/preview_icons.png, preview_attack.png, preview_fx.png

설계 메모
  - 무기는 "공격 순간에만 나타난다": 1프레임 호박빛 윤곽(실체화) → 2·3프레임 쇠(무채) + 날끝 글린트 → 4프레임 흩어지는 불티.
  - 이펙트는 강조색이 주역. 1층 '잔' 호박 램프(인덱스 16~27)로 그리고 시스템이 층 램프로 스왑한다.
  - 색 예산(무기·이펙트): 무채 <=4 + 강조 <=8.
  - 빛은 화면 좌상단: 칼날의 위/왼쪽 줄이 밝은 쇠(G13), 아래/오른쪽 줄이 쇠 본색(G08).
  - 이펙트 앵커: JSON `anchor`.  player_pivot = 피벗을 주인공 피벗(발)에 맞춘다 / hitbox_center = 피벗을 히트박스 중심에 /
    projectile = 피벗을 투사체 중심에 (rotate=true 면 진행 각도로 회전, 기본 그림은 우향).
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
OUT_W = os.path.join(ROOT, "assets", "sprites", "weapons")
OUT_FX = os.path.join(ROOT, "assets", "sprites", "fx")
PLAYER = os.path.join(ROOT, "assets", "sprites", "player")
os.makedirs(OUT_W, exist_ok=True)
os.makedirs(OUT_FX, exist_ok=True)

with open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8") as fp:
    PAL = json.load(fp)
GRAY = PAL["gray"]
RAMP = PAL["floors"][0]["ramp"]
DIRS = ["down", "up", "left", "right"]
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
FLOOR_BG = (0x3e, 0x3f, 0x42, 255)  # G04


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

    def blit(self, rows, ox, oy, legend):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    self.px(ox + i, oy + j, legend[ch])

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.25:
                    self.px(x, y, c)

    def despeckle8(self):
        """8방향 이웃이 하나도 없는 픽셀 제거."""
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

    def arc(self, cx, cy, a0, a1, t0, t1, r_mid, thick, colors, head=0.75, head_boost=1, min_t=0.9, r_curve=0.0):
        """호 띠. 각도 a0→a1 (deg, 화면 좌표: 0=우, 90=하). 구간 [t0,t1] 만 그린다.
        두께는 구간 양 끝에서 가늘어진다(sin). colors: 안쪽→바깥쪽 띠 색. head 이후 구간은 색을 head_boost 단계 밝게.
        r_curve: 구간을 따라 반지름을 t 에 비례해 더한다(나선 느낌)."""
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

    def pair(self, x, y, c, horiz=True):
        """2픽셀 불티 (고립 금지)."""
        self.px(x, y, c)
        self.px(x + (1 if horiz else 0), y + (0 if horiz else 1), c)


# ============================================================ 시트 저장
def save_sheet(folder, name, frames_by_dir, dirs, w, h, durations, loop, pivot, extra, action=None):
    n = len(durations)
    sheet = Image.new("RGBA", (w * n, h * len(dirs)), (0, 0, 0, 0))
    for r, d in enumerate(dirs):
        for c, cv in enumerate(frames_by_dir[d]):
            sheet.alpha_composite(cv.im, (c * w, r * h))
    sheet.save(os.path.join(folder, name + ".png"))
    meta = {
        "image": name + ".png",
        "action": action or name.split("_", 1)[-1],
        "frameWidth": w, "frameHeight": h,
        "frames": n,
        "directions": dirs,
        "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column",
        "fps": round(1000.0 / (sum(durations) / n)) if sum(durations) else 0,
        "frameDurationsMs": durations,
        "loop": loop,
        "pivot": {"x": pivot[0], "y": pivot[1]},
        "palette": "parts/art/palette/lopad.json (gray + floor 1 accent slots 16-27, runtime swap)",
    }
    meta.update(extra)
    with open(os.path.join(folder, name + ".json"), "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    return sheet


def color_report(frames_by_dir):
    cols = set()
    iso = 0
    semi = 0
    for d, fr in frames_by_dir.items():
        for cv in fr:
            iso += cv.isolated()
            for px in cv.im.get_flattened_data() if hasattr(cv.im, 'get_flattened_data') else cv.im.getdata():
                if px[3] == 255:
                    cols.add(px[:3])
                elif px[3]:
                    semi += 1
    grays = [c for c in cols if c in [G(i)[:3] for i in range(16)]]
    acc = [c for c in cols if c in [C(i)[:3] for i in range(16, 28)]]
    other = [c for c in cols if c not in grays and c not in acc]
    return len(grays), len(acc), other, iso, semi


# ============================================================ 1. 아이콘 16x16
ICON_LEGEND = {
    ".": None,
    "K": G(0), "S": G(9), "L": G(13), "W": G(15),
    "a": C(21),
}
ICONS = {
    # 사무라이 칼: 날끝은 가파르고 손잡이 쪽은 완만한 곡선(2폭 날 L+S, 등 쪽 K), 둥근 쓰바(K), 감은 손잡이(S/K), 술(a 2px)
    "katana": [
        "..............W.",
        ".............LS.",
        "............LSK.",
        "...........LSK..",
        "..........LSK...",
        ".........LSK....",
        "........LSK.....",
        ".......LSK......",
        ".....LLSK.......",
        "....LSSK........",
        "...KKKK.........",
        "..KSKK..........",
        "..SK............",
        ".KS.............",
        "aSK.............",
        "a...............",
    ],
    # 대검: 넓은 직선 날(3폭 + 등 K), 긴 십자 날밑(S/L 막대 + K 그늘), 감은 손잡이, 자루머리(a)
    "greatsword": [
        ".............W..",
        "............LLS.",
        "...........LLSK.",
        "..........LLSK..",
        ".........LLSK...",
        "........LLSK....",
        ".......LLSK.....",
        "...SL.LLSK......",
        "...KSLLSK.......",
        "....KSL.........",
        ".....KSL........",
        "...KS.KSL.......",
        "..SK...KSL......",
        ".KS.....K.......",
        "SK..............",
        "aa..............",
    ],
    # 단검: 세로 잎 모양 짧은 날, 가로 날밑, 짧은 손잡이, 자루머리(a)
    "dagger": [
        "................",
        ".......W........",
        ".......LS.......",
        "......LLS.......",
        "......LLSK......",
        "......LLSK......",
        "......LLSK......",
        "......LLSK......",
        ".......LSK......",
        "....KSSLSSK.....",
        "......SK........",
        "......KS........",
        "......SK........",
        "......KS........",
        "......aa........",
        "................",
    ],
    # 활: 세로 활대(밝은 나무 S/L, 감은 그립 S/K), 시위 L, 걸린 화살(W) + 촉 a
    "bow": [
        "........SS......",
        ".......LS.......",
        "......LS.L......",
        ".....LS..L......",
        ".....LS..L......",
        "....LS...L......",
        "....SK...L......",
        "....KSSSSSSSSWa.",
        "....SK...L......",
        "....LS...L......",
        ".....LS..L......",
        ".....LS..L......",
        "......LS.L......",
        ".......LS.......",
        "........SS......",
        "................",
    ],
}


def build_icons():
    out = {}
    for wid, rows in ICONS.items():
        cv = Canvas(16, 16)
        cv.blit(rows, 0, 0, ICON_LEGEND)
        out[wid] = cv
        save_sheet(OUT_W, wid + "_icon", {"any": [cv]}, ["any"], 16, 16, [0], False, (8, 8),
                   {"anchor": "ui", "frameDurationsMs": [0], "fps": 0}, action="icon")
    return out


# ============================================================ 2. 손에 든 무기 48x48 (주인공 16x24 는 (16,16) 에)
AW, AH = 48, 48
POFF = (16, 16)                 # 주인공 프레임 원점
APIVOT = (16 + 8, 16 + 23)      # = (24, 39)
# 주인공 attack 손 좌표 (player/build.py poses_attack 과 동일) — 프레임 1·2·3 + 4(휴식 손)
HANDS = {
    "down":  [(14, 7), (15, 12), (3, 17), (13, 17)],
    "up":    [(1, 7), (0, 12), (12, 17), (2, 17)],
    "right": [(3, 8), (13, 9), (15, 13), (9, 17)],
    "left":  [(12, 8), (2, 9), (0, 13), (6, 17)],
}
# 칼날 방향 (화면 좌표) 프레임 1·2·3
BLADE_DIR = {
    "down":  [(1, -1), (1, 1), (-1, 1)],
    "up":    [(-1, -1), (0, -1), (1, -1)],
    "right": [(-1, -1), (1, -1), (1, 0)],
    "left":  [(1, -1), (-1, -1), (-1, 0)],
}
ATTACK_DUR = [100, 50, 110, 110]

# 색: 무채 4 (G00 날밑·G05 손잡이/그늘·G08 쇠·G13 밝은 쇠) + 강조 (17 ink, 19, 21, 22, 24, 25, 27)
STEEL = {"edge": G(13), "body": G(8), "dark": G(5), "ink": G(0), "tip": C(27), "glow": C(25), "wrap": C(21)}
GHOST = {"edge": C(24), "body": C(22), "dark": C(19), "ink": C(17), "tip": C(25), "glow": C(25), "wrap": C(21)}


def vec_step(d, length):
    dx, dy = d
    n = math.hypot(dx, dy)
    return (round(dx / n * length), round(dy / n * length))


def perp(d):
    """좌상단 빛 기준: 밝은 줄이 놓일 수직 오프셋 (위/왼쪽)."""
    dx, dy = d
    if dy == 0:
        return (0, -1)
    if dx == 0:
        return (-1, 0)
    # 대각: (1,-1) 방향 날은 왼쪽/위가 밝다 → (-1,-1)? 2폭 대각선은 (0,-1) 또는 (-1,0) 오프셋만 가능
    return (0, -1) if dx * dy < 0 else (-1, 0)


def draw_blade(cv, grip, d, length, width, col, hilt=3, guard=1, wrap_px=(1,), tip_glow=False):
    """grip 에서 d 방향으로 length 의 날. width 1~3. hilt: 반대쪽 손잡이 길이. guard: 날밑 반폭."""
    gx, gy = grip
    tx, ty = gx + vec_step(d, length)[0], gy + vec_step(d, length)[1]
    bx, by = gx + vec_step(d, 1)[0], gy + vec_step(d, 1)[1]   # 날 시작 (날밑 다음)
    px_, py_ = perp(d)
    # 손잡이 (grip 뒤)
    hx_, hy_ = vec_step((-d[0], -d[1]), hilt)
    hx0, hy0 = gx - vec_step(d, 1)[0], gy - vec_step(d, 1)[1]
    cv.line(hx0, hy0, gx + hx_, gy + hy_, col["dark"])
    for k in wrap_px:
        wx, wy = vec_step((-d[0], -d[1]), k)
        cv.px(gx + wx, gy + wy, col["wrap"])
    # 날밑
    for k in range(-guard, guard + 1):
        cv.px(gx + px_ * k, gy + py_ * k, col["ink"])
    if guard >= 2:
        cv.px(gx, gy, col["dark"])
    # 날
    if width == 1:
        cv.line(bx, by, tx, ty, col["edge"])
    elif width == 2:
        cv.line(bx, by, tx, ty, col["body"])
        cv.line(bx + px_, by + py_, tx + px_, ty + py_, col["edge"])
    else:
        cv.line(bx, by, tx, ty, col["body"])
        cv.line(bx + px_, by + py_, tx + px_, ty + py_, col["edge"])
        cv.line(bx - px_, by - py_, tx - px_, ty - py_, col["dark"])
    cv.px(tx, ty, col["tip"])
    if width >= 2:
        cv.px(tx + px_, ty + py_, col["tip"] if tip_glow else col["edge"])
    if tip_glow:
        # 날끝 글로우 2px (날의 바깥쪽)
        cv.px(tx + vec_step(d, 1)[0], ty + vec_step(d, 1)[1], col["glow"])
        cv.px(tx + vec_step(d, 1)[0] + px_, ty + vec_step(d, 1)[1] + py_, col["glow"])


def draw_embers(cv, hand, d):
    """4프레임: 무기가 흩어지는 불티 (2px 쌍 3개)."""
    x, y = hand
    cv.pair(x - 2, y - 3, C(24))
    cv.pair(x + 1, y - 5, C(22), horiz=False)
    cv.pair(x + 3, y - 2, C(24))


def weapon_attack_frames(wid):
    spec = {
        "katana":     dict(length=10, width=2, hilt=3, guard=1, wrap=(1, 3)),
        "greatsword": dict(length=13, width=3, hilt=4, guard=2, wrap=(4,)),
        "dagger":     dict(length=5, width=2, hilt=2, guard=1, wrap=(2,)),
    }[wid]
    out = {}
    for d in DIRS:
        frames = []
        for f in range(4):
            cv = Canvas(AW, AH)
            hx_, hy_ = HANDS[d][f]
            grip = (hx_ + POFF[0], hy_ + POFF[1])
            if f == 3:
                draw_embers(cv, grip, d)
            else:
                col = GHOST if f == 0 else STEEL
                draw_blade(cv, grip, BLADE_DIR[d][f], spec["length"], spec["width"], col,
                           hilt=spec["hilt"], guard=spec["guard"], wrap_px=spec["wrap"], tip_glow=(f == 1))
            frames.append(cv)
        out[d] = frames
    return out


# 활: 손 위치를 따르지 않고 방향별 고정 위치(전방)에 둔다. 활대 13 길이, 전방으로 불룩(bulge).
BOW_BULGE = [0, 1, 2, 2, 3, 3, 3, 3, 3, 2, 2, 1, 0]
BOW_POS = {"right": (14, 11), "left": (1, 11), "down": (8, 18), "up": (8, 10)}   # 주인공 좌표, 활 중심(along 6, across 0)


def bow_map(d, cx, cy):
    """(along 0..12, across: + 전방) → 화면 좌표."""
    if d == "right":
        return lambda a, c: (cx + c, cy + a - 6)
    if d == "left":
        return lambda a, c: (cx - c, cy + a - 6)
    if d == "down":
        return lambda a, c: (cx + a - 6, cy + c)
    return lambda a, c: (cx + a - 6, cy - c)


def draw_bow(cv, d, f):
    """f=0 실체화(호박 윤곽, 시위 느슨) f=1 시위 당김+화살 f=2 발사(시위 복귀, 앞쪽 글로우, 1px 전진) f=3 불티"""
    col = GHOST if f == 0 else STEEL
    cx, cy = BOW_POS[d]
    cx += POFF[0]; cy += POFF[1]
    if f == 3:
        return draw_embers(cv, (cx, cy), d)
    push = 1 if f == 2 else 0
    fx_, fy_ = {"right": (1, 0), "left": (-1, 0), "down": (0, 1), "up": (0, -1)}[d]
    M = bow_map(d, cx + fx_ * push, cy + fy_ * push)
    # 활대: 앞 가장자리 = 밝은 쇠/나무(edge), 뒤쪽 1px = 본색(body). 그립 (along 5..7) = dark
    for a, b in enumerate(BOW_BULGE):
        x, y = M(a, b)
        cv.px(x, y, col["dark"] if 5 <= a <= 7 else col["edge"])
        if 1 <= a <= 11:
            x2, y2 = M(a, b - 1)
            cv.px(x2, y2, col["dark"] if 5 <= a <= 7 else col["body"])
    # 시위
    s_col = col["edge"] if f else C(24)
    x0, y0 = M(0, -1); x1, y1 = M(12, -1)
    if f == 1:
        nx, ny = M(6, -4)
        cv.line(x0, y0, nx, ny, s_col); cv.line(nx, ny, x1, y1, s_col)
        # 화살: 시위 꺾인 점에서 전방 +7 까지, 촉 27, 깃 21
        ax0, ay0 = M(6, -3); ax1, ay1 = M(6, 6)
        cv.line(ax0, ay0, ax1, ay1, G(13))
        tx, ty = M(6, 7); cv.px(tx, ty, C(27))
        for a in (5, 7):
            x, y = M(a, -3); cv.px(x, y, C(21))
    else:
        cv.line(x0, y0, x1, y1, s_col)
        if f == 2:
            # 시위 떨림 + 날아간 자리 글로우
            x, y = M(6, -2); cv.px(x, y, C(25)); x, y = M(5, -2); cv.px(x, y, C(25))
            x, y = M(6, 8); cv.px(x, y, C(24)); x, y = M(6, 9); cv.px(x, y, C(24))


def bow_attack_frames():
    out = {}
    for d in DIRS:
        out[d] = []
        for f in range(4):
            cv = Canvas(AW, AH)
            draw_bow(cv, d, f)
            out[d].append(cv)
    return out


# ============================================================ 3. 베기 이펙트 32x32 (피벗 (16,26) = 발, 몸 중심 (16,16))
# 방향별 호 각도 (시작→끝). 화면 좌표 0=우 90=하.
SWEEP = {
    "down":  (-20, 200),     # 우 → 하 → 좌
    "up":    (160, 380),     # 좌 → 상 → 우
    "right": (-100, 80),     # 상 → 우 → 하
    "left":  (280, 100),     # 상 → 좌 → 하 (감소)
}
SLASH_DUR = [50, 60, 70, 80]


def slash_frames(kind, w=32, cx=16, cy=16, dirs=DIRS, sweep=SWEEP):
    spec = {
        "katana":     dict(r=11.5, thick=4.2, dur=SLASH_DUR,
                           full=[C(22), C(24), C(26), C(27)], fade=[C(19), C(21), C(22), C(24)], rem=[C(17), C(18), C(19)]),
        "dagger":     dict(r=8, thick=2.8, dur=[40, 50, 60, 60],
                           full=[C(24), C(26), C(27)], fade=[C(21), C(22), C(24)], rem=[C(18), C(19)]),
        "greatsword": dict(r=12, thick=5.4, dur=[60, 80, 90, 100],
                           full=[C(18), C(22), C(24), C(26), C(27)], fade=[C(17), C(19), C(21), C(22), C(24)],
                           rem=[C(17), C(18), C(19)]),
        "iai":        dict(r=19, thick=7.0, dur=[50, 60, 80, 100, 120, 140],
                           full=[C(20), C(22), C(24), C(26), C(27)], fade=[C(18), C(19), C(21), C(22), C(24)],
                           rem=[C(18), C(19), C(20)]),
    }[kind]
    out = {}
    for d in dirs:
        a0, a1 = sweep[d]
        frames = []
        r, tk = spec["r"], spec["thick"]
        if kind == "iai":
            seq = [
                dict(t=(0.0, 0.35), th=tk * 0.8, col=spec["full"], head=0.6),
                dict(t=(0.0, 1.0), th=tk, col=spec["full"], head=0.7),
                dict(t=(0.0, 1.0), th=tk * 0.9, col=spec["fade"], head=0.75),
                dict(t=(0.05, 1.0), th=tk * 0.65, col=spec["fade"][:3], head=2),
                dict(t=(0.1, 0.95), th=tk * 0.45, col=spec["rem"][1:], head=2),
                dict(t=(0.2, 0.9), th=tk * 0.3, col=spec["rem"][:2], head=2, dash=True),
            ]
        elif kind == "greatsword":
            seq = [
                dict(t=(0.0, 0.4), th=tk * 0.7, col=spec["full"], head=0.6),
                dict(t=(0.0, 1.0), th=tk, col=spec["full"], head=0.7),
                dict(t=(0.2, 1.0), th=tk * 0.85, col=spec["fade"], head=0.8),
                dict(t=(0.5, 1.0), th=tk * 0.5, col=spec["rem"], head=2),
            ]
        else:
            seq = [
                dict(t=(0.0, 0.45), th=tk * 0.8, col=spec["full"], head=0.6),
                dict(t=(0.0, 1.0), th=tk, col=spec["full"], head=0.7),
                dict(t=(0.35, 1.0), th=tk * 0.6, col=spec["fade"], head=0.8),
                dict(t=(0.6, 1.0), th=tk * 0.35, col=spec["rem"], head=2),
            ]
        for i, st in enumerate(seq):
            cv = Canvas(w, w)
            cv.arc(cx, cy, a0, a1, st["t"][0], st["t"][1], r, st["th"], st["col"], head=st["head"], head_boost=1)
            if st.get("dash"):
                # 마지막 잔광: 띠를 3px 간격으로 끊어 점점 사라지는 느낌
                for y in range(w):
                    for x in range(w):
                        if cv.p[x, y][3] and ((x + y) % 4 == 0):
                            cv.p[x, y] = (0, 0, 0, 0)
            # 마지막 프레임 불티
            if i == len(seq) - 1:
                ang = math.radians(a1 - (a1 - a0) * 0.15)
                ex, ey = int(round(cx + (r + 2) * math.cos(ang))), int(round(cy + (r + 2) * math.sin(ang)))
                ex, ey = max(1, min(w - 3, ex)), max(1, min(w - 3, ey))
                cv.pair(ex, ey, C(22))
                ang2 = math.radians(a1 - (a1 - a0) * 0.4)
                cv.pair(int(cx + (r + 2) * math.cos(ang2)), int(cy + (r + 2) * math.sin(ang2)), C(21), horiz=False)
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out, spec["dur"]


# ============================================================ 4. 화살
def arrow_frames():
    a = Canvas(8, 8)
    # 우향: 깃 x0..1, 자루 x1..5, 촉 x5..7
    a.px(0, 3, C(21)); a.px(0, 5, C(21)); a.px(1, 3, C(21)); a.px(1, 5, C(21))
    a.line(1, 4, 5, 4, G(13))
    a.px(5, 3, G(8)); a.px(5, 5, G(8)); a.px(6, 4, G(13)); a.px(7, 4, C(27))
    b = Canvas(12, 6)
    # 조준 사격: 2폭 자루(밝은 쇠 + 그늘), 긴 촉, 깃 3개, 자루에 글로우 1줄
    b.px(0, 1, C(21)); b.px(1, 1, C(21)); b.px(0, 4, C(21)); b.px(1, 4, C(21)); b.px(0, 2, C(21)); b.px(0, 3, C(21))
    b.line(1, 2, 9, 2, G(13))
    b.line(1, 3, 9, 3, G(8))
    b.line(3, 2, 7, 2, C(25))
    b.px(8, 1, G(8)); b.px(8, 4, G(8)); b.px(9, 1, G(13)); b.px(9, 4, G(13))
    b.px(10, 2, C(27)); b.px(10, 3, C(27)); b.px(11, 2, C(27)); b.px(11, 3, C(27))
    return a, b


# ============================================================ 5. 진화 이펙트
def batto_frames():
    """발도 대쉬 잔광 32x32, 4방향 4프레임. 몸 뒤로 뻗는 속도선 3줄(가운데가 가장 밝고 길다) + 1·2프레임 전방 짧은 발도 호."""
    out = {}
    cx, cy = 16, 16
    for d in DIRS:
        fx_, fy_ = {"right": (1, 0), "left": (-1, 0), "down": (0, 1), "up": (0, -1)}[d]
        bx, by = -fx_, -fy_
        face = {"right": 0, "down": 90, "left": 180, "up": 270}[d]
        frames = []
        lens = [(5, 8, 4), (9, 11, 8), (7, 10, 6), (3, 5, 2)]
        cols = [[C(24), C(25), C(24)], [C(25), C(27), C(25)], [C(21), C(22), C(21)], [C(18), C(19), C(18)]]
        for f in range(4):
            cv = Canvas(32, 32)
            L = lens[f]; col = cols[f]
            for k, o in enumerate((-4, 0, 4)):
                x0 = cx + bx * (3 if k == 1 else 5) + (0 if d in ("left", "right") else o)
                y0 = cy + by * (3 if k == 1 else 5) + (o if d in ("left", "right") else 0)
                cv.line(x0, y0, x0 + bx * L[k], y0 + by * L[k], col[k])
            if f < 2:
                cv.arc(cx, cy, face - 40, face + 40, 0.0, 1.0, 9, 2.2 if f else 1.6,
                       [C(26), C(27)] if f else [C(24), C(25)], head=2, min_t=1.0)
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


def crush_frames():
    """파쇄 충격파 링 48x48, 방향 무관 4프레임. 피벗 = 중심 (24,24), hitbox_center 앵커."""
    cx, cy = 24, 24
    frames = []
    seq = [
        dict(r=5, th=3.0, col=[C(24), C(27)], cracks=0),
        dict(r=11, th=3.2, col=[C(22), C(24), C(26)], cracks=6),
        dict(r=17, th=2.4, col=[C(19), C(21), C(22)], cracks=9),
        dict(r=21, th=1.4, col=[C(17), C(18)], cracks=0, dash=True),
    ]
    for i, st in enumerate(seq):
        cv = Canvas(48, 48)
        # 전체 원: 두 호(0→180, 180→360)로 그린다 (두께 균일하게 min_t = th)
        cv.arc(cx, cy, 0, 360, 0, 1, st["r"], st["th"], st["col"], head=2, min_t=st["th"])
        # 바닥이 보이는 탑다운: 링을 세로로 0.75 압축 (타원) → 픽셀 재배치
        im2 = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
        p2 = im2.load()
        for y in range(48):
            for x in range(48):
                sy = cy + (y - cy) / 0.75
                yy = int(round(sy))
                if 0 <= yy < 48 and cv.p[x, yy][3]:
                    p2[x, y] = cv.p[x, yy]
        cv.im, cv.p = im2, p2
        if st.get("dash"):
            for y in range(48):
                for x in range(48):
                    if cv.p[x, y][3] and ((x * 3 + y) % 5 in (0, 1)):
                        cv.p[x, y] = (0, 0, 0, 0)
        # 갈라진 바닥: 방사형 짧은 금 (글로우)
        for k in range(st["cracks"]):
            ang = math.radians(k * 360.0 / st["cracks"] + 15)
            r0 = st["r"] - 4
            r1 = st["r"] + 2
            x0, y0 = int(round(cx + r0 * math.cos(ang))), int(round(cy + r0 * math.sin(ang) * 0.75))
            x1, y1 = int(round(cx + r1 * math.cos(ang))), int(round(cy + r1 * math.sin(ang) * 0.75))
            cv.line(x0, y0, x1, y1, C(21) if i == 1 else C(18))
        # 중심 섬광 (1·2프레임)
        if i == 0:
            cv.disc(cx, cy, 1.6, C(27))
        if i == 1:
            cv.pair(cx - 1, cy, C(24))
        if i == 3:
            cv.pair(cx - 9, cy - 8, C(19)); cv.pair(cx + 10, cy + 7, C(19), horiz=False); cv.pair(cx + 6, cy - 11, C(18))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def weight_frames():
    """중압 내려찍기 먼지 32x24, 방향 무관 4프레임. 피벗 (16,22) = 타격 지점(바닥)."""
    cx, cy = 16, 20
    frames = []
    DUST_L, DUST_M, DUST_D = G(12), G(9), G(6)
    for f in range(4):
        cv = Canvas(32, 24)
        if f == 0:
            cv.disc(cx, cy, 1.5, C(27))
            cv.px(cx - 3, cy, C(25)); cv.px(cx + 3, cy, C(25)); cv.px(cx - 2, cy, C(25)); cv.px(cx + 2, cy, C(25))
            cv.disc(cx - 5, cy + 1, 1.5, DUST_M); cv.disc(cx + 5, cy + 1, 1.5, DUST_M)
        elif f == 1:
            cv.disc(cx - 7, cy - 1, 3.0, DUST_D); cv.disc(cx + 7, cy - 1, 3.0, DUST_D)
            cv.disc(cx - 8, cy - 2, 2.2, DUST_M); cv.disc(cx + 6, cy - 2, 2.2, DUST_M)
            cv.disc(cx - 9, cy - 3, 1.2, DUST_L); cv.disc(cx + 5, cy - 3, 1.2, DUST_L)
            cv.px(cx - 1, cy, C(25)); cv.px(cx, cy, C(27)); cv.px(cx + 1, cy, C(25)); cv.px(cx, cy - 1, C(25))
            cv.line(cx - 4, cy + 1, cx - 2, cy + 1, C(21)); cv.line(cx + 2, cy + 1, cx + 4, cy + 1, C(21))
        elif f == 2:
            cv.disc(cx - 10, cy - 3, 3.4, DUST_D); cv.disc(cx + 10, cy - 3, 3.4, DUST_D)
            cv.disc(cx - 11, cy - 5, 2.4, DUST_M); cv.disc(cx + 9, cy - 5, 2.4, DUST_M)
            cv.disc(cx - 12, cy - 6, 1.2, DUST_L); cv.disc(cx + 8, cy - 7, 1.2, DUST_L)
            cv.disc(cx - 4, cy - 6, 1.6, DUST_M); cv.disc(cx + 4, cy - 7, 1.6, DUST_M)
            cv.pair(cx - 1, cy, C(22)); cv.line(cx - 6, cy + 1, cx - 3, cy + 1, C(19)); cv.line(cx + 3, cy + 1, cx + 6, cy + 1, C(19))
        else:
            cv.disc(cx - 12, cy - 6, 2.0, DUST_D); cv.disc(cx + 12, cy - 6, 2.0, DUST_D)
            cv.disc(cx - 7, cy - 9, 1.6, DUST_M); cv.disc(cx + 6, cy - 10, 1.6, DUST_M)
            cv.pair(cx - 11, cy - 10, DUST_M); cv.pair(cx + 10, cy - 11, DUST_M)
            cv.pair(cx - 2, cy, C(18)); cv.pair(cx + 1, cy, C(18))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def twin_frames():
    """쌍격 2중 베기 32x32, 4방향 4프레임: 안쪽 호 → 바깥 호가 뒤따른다."""
    out = {}
    cx, cy = 16, 16
    full_in = [C(24), C(26), C(27)]
    full_out = [C(22), C(24), C(27)]
    fade = [C(19), C(21), C(22)]
    rem = [C(17), C(18)]
    for d in DIRS:
        a0, a1 = SWEEP[d]
        frames = []
        for f in range(4):
            cv = Canvas(32, 32)
            if f == 0:
                cv.arc(cx, cy, a0, a1, 0.0, 0.8, 7.5, 2.6, full_in, head=0.6)
            elif f == 1:
                cv.arc(cx, cy, a0, a1, 0.3, 1.0, 7.5, 2.2, fade, head=2)
                cv.arc(cx, cy, a0, a1, 0.0, 0.9, 11.5, 3.0, full_out, head=0.65)
            elif f == 2:
                cv.arc(cx, cy, a0, a1, 0.6, 1.0, 7.5, 1.6, rem, head=2)
                cv.arc(cx, cy, a0, a1, 0.35, 1.0, 11.5, 2.4, fade, head=0.85)
            else:
                cv.arc(cx, cy, a0, a1, 0.65, 1.0, 11.5, 1.4, rem, head=2)
                ang = math.radians(a1 - (a1 - a0) * 0.1)
                cv.pair(int(cx + 14 * math.cos(ang)), int(cy + 14 * math.sin(ang)), C(21))
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


def gale_frames():
    """질풍 바람 잔상 24x24, 4방향 4프레임. 몸 뒤로 흐르는 곡선 바람 줄 3개. 피벗 (12,22)=발."""
    out = {}
    cx, cy = 12, 12
    for d in DIRS:
        # 바람은 몸 뒤쪽. 뒤쪽 중심 각도
        back = {"right": 180, "left": 0, "down": 270, "up": 90}[d]
        frames = []
        for f in range(4):
            cv = Canvas(24, 24)
            shift = f * 0.5
            cols = [[C(25), C(24)], [C(24), C(22)], [C(22), C(21)], [C(19), C(18)]][f]
            # 세 줄: 뒤 중심 각도 ±28° 와 중앙, 반지름 다르게. 줄은 짧은 호 (24° 폭)
            for k, (da, rr) in enumerate(((-32, 7.0), (0, 8.5), (32, 7.0))):
                a = back + da
                cv.arc(cx, cy, a - 36, a + 36, 0.2 + f * 0.08, 0.8 + f * 0.05, rr + shift, 1.4, cols, head=2, min_t=1.0)
            if f < 2:
                ang = math.radians(back)
                ex, ey = int(round(cx + (9.0 + shift) * math.cos(ang))), int(round(cy + (9.0 + shift) * math.sin(ang)))
                cv.pair(ex, ey, cols[0], horiz=(d in ("up", "down")))
            cv.despeckle8()
            frames.append(cv)
        out[d] = frames
    return out


def pierce_frames():
    """관통 화살 꼬리 16x8, 우향 1행 4프레임 루프. 피벗 (14,4) = 화살 중심. 뒤로 뻗는 빛줄."""
    frames = []
    for f in range(4):
        cv = Canvas(16, 8)
        L = [10, 12, 11, 9][f]
        cv.line(13, 4, 13 - L, 4, C(22))
        cv.line(12, 4, 12 - L + 4, 4, C(24))
        cv.line(11, 4, 11 - L + 8, 4, C(26))
        cv.line(12, 3, 12 - (L - 5), 3, C(21))
        cv.line(12, 5, 12 - (L - 5), 5, C(21))
        cv.line(13 - L + 1, 3, 13 - L + 2, 3, C(19)) if f % 2 == 0 else cv.line(13 - L + 1, 5, 13 - L + 2, 5, C(19))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


def scatter_frames():
    """산탄 3갈래 발사 섬광 16x16, 우향 1행 4프레임. 피벗 (2,8) = 발사점."""
    frames = []
    ox, oy = 2, 8
    for f in range(4):
        cv = Canvas(16, 16)
        L = [5, 8, 11, 11][f]
        cols = [[C(27), C(25)], [C(26), C(24)], [C(22), C(21)], [C(18), C(17)]][f]
        for ang in (-24, 0, 24):
            a = math.radians(ang)
            s0 = 2 if f < 3 else 7
            x0, y0 = int(round(ox + s0 * math.cos(a))), int(round(oy + s0 * math.sin(a)))
            x1, y1 = int(round(ox + L * math.cos(a))), int(round(oy + L * math.sin(a)))
            cv.line(x0, y0, x1, y1, cols[0] if ang == 0 else cols[1])
            if f in (1, 2):
                cv.px(x1 + 1, y1, cols[0])
        if f == 0:
            cv.disc(ox, oy, 1.5, C(27))
        if f == 1:
            cv.px(ox, oy - 1, C(25)); cv.px(ox, oy + 1, C(25)); cv.px(ox, oy, C(27))
        cv.despeckle8()
        frames.append(cv)
    return {"any": frames}


# ============================================================ 미리보기
def label(d, xy, text, col=(230, 230, 230)):
    d.text(xy, text, fill=col, font=FONT)


def scaled(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def preview_icons(icons):
    k = 8
    cell = 16 * k + 8
    img = Image.new("RGB", (len(icons) * cell + 8, cell * 2 + 40), (40, 40, 44))
    d = ImageDraw.Draw(img)
    for i, (wid, cv) in enumerate(icons.items()):
        label(d, (8 + i * cell, 4), wid)
        for r, bg in enumerate(((0x21, 0x22, 0x24, 255), (0xc5, 0xc6, 0xc9, 255))):
            c = Image.new("RGBA", (16 * k, 16 * k), bg)
            c.alpha_composite(scaled(cv.im, k))
            img.paste(c.convert("RGB"), (8 + i * cell, 20 + r * cell))
    # 1배 실크기도
    for i, (wid, cv) in enumerate(icons.items()):
        c = Image.new("RGBA", (16, 16), (0x21, 0x22, 0x24, 255))
        c.alpha_composite(cv.im)
        img.paste(c.convert("RGB"), (8 + i * 20, cell * 2 + 22))
    img.save(os.path.join(HERE, "preview_icons.png"))


def preview_attack(weapons):
    """주인공 attack 프레임 위에 무기를 겹쳐 4방향 x 4프레임, 무기 4종. 4배, 바닥 G04."""
    k = 4
    patt = Image.open(os.path.join(PLAYER, "player_attack.png")).convert("RGBA")
    cw, ch = AW * k, AH * k
    gap = 4
    bw = 4 * (cw + gap) + 48
    bh = 4 * (ch + gap) + 20
    img = Image.new("RGB", (bw * 2 + 16, bh * 2 + 16), (30, 30, 34))
    d = ImageDraw.Draw(img)
    for wi, (wid, frames) in enumerate(weapons.items()):
        bx, by = 8 + (wi % 2) * bw, 8 + (wi // 2) * bh
        label(d, (bx + 4, by + 2), "%s_attack  (48x48, pivot 24,39; player at 16,16; up row = weapon below player)  %s" % (wid, ATTACK_DUR))
        for r, dd in enumerate(DIRS):
            label(d, (bx + 4, by + 20 + r * (ch + gap) + ch // 2), dd)
            for c in range(4):
                cell = Image.new("RGBA", (AW, AH), FLOOR_BG)
                pf = patt.crop((c * 16, r * 24, c * 16 + 16, r * 24 + 24))
                if dd == "up":
                    cell.alpha_composite(frames[dd][c].im)
                    cell.alpha_composite(pf, POFF)
                else:
                    cell.alpha_composite(pf, POFF)
                    cell.alpha_composite(frames[dd][c].im)
                img.paste(scaled(cell, k).convert("RGB"), (bx + 48 + c * (cw + gap), by + 20 + r * (ch + gap)))
    img.save(os.path.join(HERE, "preview_attack.png"))


def preview_fx(fx_list):
    """모든 이펙트 한눈에. (name, frames_by_dir, dirs, w, h, pivot, anchor, durations). 3배, 바닥 G04.
    player_pivot 앵커는 주인공 idle 1프레임을 피벗에 얹어 크기를 비교한다."""
    k = 3
    pidle = Image.open(os.path.join(PLAYER, "player_idle.png")).convert("RGBA")
    blocks = []
    for name, fbd, dirs, w, h, pivot, anchor, durs in fx_list:
        n = len(durs)
        cw, ch = w * k, h * k
        gap = 3
        bw = 60 + n * (cw + gap)
        bh = 16 + len(dirs) * (ch + gap)
        blk = Image.new("RGB", (bw, bh), (34, 34, 38))
        d = ImageDraw.Draw(blk)
        label(d, (4, 1), "%s %dx%d %s pivot(%d,%d) %s" % (name, w, h, "/".join(dirs), pivot[0], pivot[1], durs))
        for r, dd in enumerate(dirs):
            label(d, (4, 16 + r * (ch + gap) + ch // 2 - 6), dd)
            for c in range(n):
                cell = Image.new("RGBA", (w, h), FLOOR_BG)
                below = name in ("batto", "gale")
                pf = None
                if anchor == "player_pivot":
                    row = DIRS.index(dd) if dd in DIRS else 0
                    pf = pidle.crop((0, row * 24, 16, row * 24 + 24))
                    if not below:
                        cell.alpha_composite(pf, (pivot[0] - 8, pivot[1] - 23))
                cell.alpha_composite(fbd[dd][c].im)
                if pf is not None and below:
                    cell.alpha_composite(pf, (pivot[0] - 8, pivot[1] - 23))
                blk.paste(scaled(cell, k).convert("RGB"), (60 + c * (cw + gap), 16 + r * (ch + gap)))
        blocks.append(blk)
    # 세로로 쌓되 2열
    col_w = max(b.width for b in blocks)
    half = (len(blocks) + 1) // 2
    cols = [blocks[:half], blocks[half:]]
    heights = [sum(b.height + 6 for b in c) for c in cols]
    img = Image.new("RGB", (col_w * 2 + 24, max(heights) + 16), (24, 24, 28))
    for ci, c in enumerate(cols):
        y = 8
        for b in c:
            img.paste(b, (8 + ci * (col_w + 8), y))
            y += b.height + 6
    img.save(os.path.join(HERE, "preview_fx.png"))


# ============================================================ main
def main():
    report = []
    # 1. 아이콘
    icons = build_icons()
    preview_icons(icons)
    for wid, cv in icons.items():
        g, a, other, iso, semi = color_report({"any": [cv]})
        report.append(("%s_icon" % wid, g, a, other, iso, semi))

    # 2. 손에 든 무기
    weapons = {}
    for wid in ("katana", "greatsword", "dagger"):
        weapons[wid] = weapon_attack_frames(wid)
    weapons["bow"] = bow_attack_frames()
    for wid, fbd in weapons.items():
        save_sheet(OUT_W, wid + "_attack", fbd, DIRS, AW, AH, ATTACK_DUR, False, APIVOT,
                   {"anchor": "player_pivot",
                    "overlay": "player_attack 과 같은 프레임 번호(row*4+col)를 같은 시각에 플레이어에 겹친다. 피벗 (24,39) = 플레이어 피벗 (8,23).",
                    "depth": {"down": "above", "left": "above", "right": "above", "up": "below"},
                    "frameNotes": ["1 실체화(호박 윤곽)", "2 휘두름(쇠, 날끝 글로우) / 활: 시위 당김", "3 뻗음 / 활: 발사(화살 생성 권장 시점)", "4 흩어지는 불티"],
                    "playerFrameOffset": {"x": POFF[0], "y": POFF[1]}})
        g, a, other, iso, semi = color_report(fbd)
        report.append(("%s_attack" % wid, g, a, other, iso, semi))
    preview_attack(weapons)

    # 3. 베기 이펙트 + 화살
    fx_list = []
    for wid in ("katana", "greatsword", "dagger"):
        fbd, durs = slash_frames(wid)
        save_sheet(OUT_FX, wid + "_slash", fbd, DIRS, 32, 32, durs, False, (16, 26),
                   {"anchor": "player_pivot", "spawn": "player attack 2프레임(휘두름) 시작 시점에 재생"})
        fx_list.append((wid + "_slash", fbd, DIRS, 32, 32, (16, 26), "player_pivot", durs))
        g, a, other, iso, semi = color_report(fbd)
        report.append(("%s_slash" % wid, g, a, other, iso, semi))
    arrow, aimed = arrow_frames()
    save_sheet(OUT_FX, "bow_arrow", {"any": [arrow]}, ["any"], 8, 8, [0], False, (4, 4),
               {"anchor": "projectile", "rotate": True, "drawnFacing": "right", "fps": 0}, action="arrow")
    save_sheet(OUT_FX, "bow_arrow_aimed", {"any": [aimed]}, ["any"], 12, 6, [0], False, (6, 3),
               {"anchor": "projectile", "rotate": True, "drawnFacing": "right", "fps": 0}, action="arrow_aimed")
    fx_list.append(("bow_arrow", {"any": [arrow]}, ["any"], 8, 8, (4, 4), "projectile", [0]))
    fx_list.append(("bow_arrow_aimed", {"any": [aimed]}, ["any"], 12, 6, (6, 3), "projectile", [0]))
    report.append(("bow_arrow",) + color_report({"any": [arrow]}))
    report.append(("bow_arrow_aimed",) + color_report({"any": [aimed]}))

    # 4. 진화 8종
    iai, iai_d = slash_frames("iai", w=48, cx=24, cy=24)
    save_sheet(OUT_FX, "iai", iai, DIRS, 48, 48, iai_d, False, (24, 34),
               {"anchor": "player_pivot", "spawn": "player attack 2프레임 시작. 4~6프레임은 남는 궤적(잔월 지속 피해 영역 표시용)"}, action="iai")
    fx_list.append(("iai", iai, DIRS, 48, 48, (24, 34), "player_pivot", iai_d))
    report.append(("iai",) + color_report(iai))

    bt = batto_frames(); bt_d = [50, 70, 80, 90]
    save_sheet(OUT_FX, "batto", bt, DIRS, 32, 32, bt_d, False, (16, 26),
               {"anchor": "player_pivot", "spawn": "대쉬 시작 시점, 플레이어 아래(depth) 권장"}, action="batto")
    fx_list.append(("batto", bt, DIRS, 32, 32, (16, 26), "player_pivot", bt_d))
    report.append(("batto",) + color_report(bt))

    cr = crush_frames(); cr_d = [50, 70, 90, 110]
    save_sheet(OUT_FX, "crush", cr, ["any"], 48, 48, cr_d, False, (24, 24),
               {"anchor": "hitbox_center", "spawn": "대검 적중 판정 시작 시점, 플레이어 아래(depth) 권장"}, action="crush")
    fx_list.append(("crush", cr, ["any"], 48, 48, (24, 24), "hitbox_center", cr_d))
    report.append(("crush",) + color_report(cr))

    wt = weight_frames(); wt_d = [50, 80, 100, 120]
    save_sheet(OUT_FX, "weight", wt, ["any"], 32, 24, wt_d, False, (16, 22),
               {"anchor": "hitbox_center", "pivotNote": "피벗 = 타격 지점 바닥. 히트박스 중심에서 아래로 6px 권장", "spawn": "대검 적중 판정 시작"}, action="weight")
    fx_list.append(("weight", wt, ["any"], 32, 24, (16, 22), "hitbox_center", wt_d))
    report.append(("weight",) + color_report(wt))

    tw = twin_frames(); tw_d = [40, 50, 60, 70]
    save_sheet(OUT_FX, "twin", tw, DIRS, 32, 32, tw_d, False, (16, 26),
               {"anchor": "player_pivot", "spawn": "player attack 2프레임 시작. 2프레임 = 두 번째 타격"}, action="twin")
    fx_list.append(("twin", tw, DIRS, 32, 32, (16, 26), "player_pivot", tw_d))
    report.append(("twin",) + color_report(tw))

    ga = gale_frames(); ga_d = [60, 70, 80, 90]
    save_sheet(OUT_FX, "gale", ga, DIRS, 24, 24, ga_d, True, (12, 22),
               {"anchor": "player_pivot", "spawn": "이동·대쉬 중 루프, 플레이어 아래(depth) 권장"}, action="gale")
    fx_list.append(("gale", ga, DIRS, 24, 24, (12, 22), "player_pivot", ga_d))
    report.append(("gale",) + color_report(ga))

    pi = pierce_frames(); pi_d = [60, 60, 60, 60]
    save_sheet(OUT_FX, "pierce", pi, ["any"], 16, 8, pi_d, True, (14, 4),
               {"anchor": "projectile", "rotate": True, "drawnFacing": "right", "spawn": "화살 뒤에 붙여 루프 (화살 중심 = 피벗)"}, action="pierce")
    fx_list.append(("pierce", pi, ["any"], 16, 8, (14, 4), "projectile", pi_d))
    report.append(("pierce",) + color_report(pi))

    sc = scatter_frames(); sc_d = [40, 50, 60, 70]
    save_sheet(OUT_FX, "scatter", sc, ["any"], 16, 16, sc_d, False, (2, 8),
               {"anchor": "projectile", "rotate": True, "drawnFacing": "right", "spawn": "발사점(활 위치)에 발사 각도로 회전해 1회"}, action="scatter")
    fx_list.append(("scatter", sc, ["any"], 16, 16, (2, 8), "projectile", sc_d))
    report.append(("scatter",) + color_report(sc))

    preview_fx(fx_list)
    print("%-18s gray acc other iso semi" % "asset")
    for row in report:
        print("%-18s %4d %3d %5d %3d %4d" % (row[0], row[1], row[2], len(row[3]), row[4], row[5]))


if __name__ == "__main__":
    import sys
    # 53라운드: 이 스크립트 산출 중 weapons/katana_attack 은 삭제됨(v3 로 대체), 미리보기 입력 player/player_attack·idle 도 삭제됨.
    # katana_icon·대검·단검·활 오버레이·fx 는 남아 있으나, 재실행하면 지운 시트를 다시 만들므로 --legacy 없이는 멈춘다.
    if "--legacy" not in sys.argv:
        sys.exit("weapons/build.py 는 보관용(katana_attack·구 주인공 53라운드 삭제)입니다. 다시 만들려면 --legacy")
    main()
