#!/usr/bin/env python3
"""[보관용 · 49라운드에 build.py(혼불 판)로 대체] LOPAD 탄생 연출 (48라운드 Q6, 계약 art-assets.md §6.3) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/birth/build.py
입력: parts/art/palette/lopad.json, assets/sprites/player/player_idle.png (마지막 프레임 이음),
      parts/art/work/player/rimlight.py (림라이트 G04, 40라운드 Q1),
      assets/tiles/stage1.png/json (미리보기 목업 바닥, roomFloors.start — 없으면 자체 흙바닥)
산출:
  assets/sprites/player/player_birth.png/json  32x32, ["down"] 1행, 피벗 (16,31)
  assets/sprites/fx/birth_dust.png/json        64x32, ["any"] 1행, 피벗 (32,22) = 주인공 발
  parts/art/work/birth/preview.png             4배 프레임 띠 + 1층 황폐 바닥 위 2배·4배 목업
  parts/art/work/birth/gif/*.gif               검수용 (4배·시간 그대로)

설계 (NOTES.md 에 이유)
  A 모임   f0~f4  : 흙 알갱이 3갈래가 발밑으로 소용돌이쳐 모이고 낮은 둔덕이 생긴다.
  B 솟음   f5~f7  : 둔덕 → 흙기둥 → 머리 혹이 있는 덩어리. 속에서 잔불 실금이 비친다.
  C 굳음   f8~f10 : 무릎 꿇은 사람 형체(흙). 실금이 밝아지다 f10 에서 잔불이 터진다(burstFrame).
  D 무릎   f11~f13: 흙 껍질이 부서져 떨어지고 검은 외투가 드러난다. f13 고개를 들어 눈빛이 켜진다.
  E 일어섬 f14~f17: 반쯤 → 거의 → 대기. f17 = player_idle down 0 원본 그대로(픽셀 동일).
색: 무채 16(흙·인물) + 1층 강조 램프(런타임 층 스왑 대상). 백열 코어·무기 보조색 없음.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "parts", "art", "work", "player"))
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from rimlight import rim_light  # noqa: E402

OUT_PLAYER = os.path.join(ROOT, "assets", "sprites", "player")
OUT_FX = os.path.join(ROOT, "assets", "sprites", "fx")
os.makedirs(os.path.join(HERE, "gif"), exist_ok=True)

with open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8") as fp:
    PAL = json.load(fp)
G = PAL["gray"]
A = PAL["floors"][0]["ramp"]          # 1층 잔(호박). A[k] = 슬롯 16+k


def rgba(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


# ------------------------------------------------------------ 캔버스 도우미
class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.p = self.im.load()

    def px(self, x, y, c, only_empty=False):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            if only_empty and self.p[x, y][3]:
                return
            self.p[x, y] = rgba(c) if isinstance(c, str) else c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            v = self.p[x, y]
            return v if v[3] else None
        return None

    def paste(self, other, ox=0, oy=0):
        self.im.alpha_composite(other.im if isinstance(other, Canvas) else other, (ox, oy))


def outline_inside(cv, color, mask=None):
    """셀아웃: 실루엣 가장자리 픽셀을 color 로 (pixelstudio outline inside 와 같은 규칙)."""
    w, h = cv.w, cv.h
    a = [[cv.p[x, y][3] > 0 for x in range(w)] for y in range(h)]
    todo = []
    for y in range(h):
        for x in range(w):
            if not a[y][x] or (mask is not None and not mask(x, y)):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < w and 0 <= ny < h) or not a[ny][nx]:
                    todo.append((x, y)); break
    c = rgba(color)
    for x, y in todo:
        cv.p[x, y] = c


# ============================================================ 주인공 부품 (player/build.py 지도 복제)
# 원본: parts/art/work/player/build.py — 같은 문자 지도·색 규칙. 대기 마지막 이음은 PNG 원본을 붙여 보장한다.
LEGEND = {
    "K": G[0], "1": G[1], "h": G[1], "3": G[3], "5": G[5], "6": G[6], "8": G[8],
    "a": G[10], "c": G[12], "e": G[14], "W": G[15],
    "E": A[7],   # 눈빛 A23
    "F": A[9],   # 눈빛이 켜지는 순간 A25 (f13 한 장)
    "D": A[5],   # 일기장 A21
}
HAT = ["..hhhhhh..", ".3hhhhhhh.", ".3hhhhhhh.", "3hhhhhhhhh"]
FACE_DOWN = ["aaEaaKaa", "ceeccccc", "cccccacc", ".acccca."]
TORSO_DOWN = ["53311133", "15333331", "15333311", "15333311",
              "KKK6KKKK", "13333311", "13333311", "3.33.3.1"]
BOOT_DOWN = ["111K111", "KKKKKKK"]
OX, OY = 8, 8      # 16x24 로컬 → 32x32 (피벗 (8,23) → (16,31))
GROUND = 23        # 로컬 발바닥 줄


def blit(cv, rows, ox, oy):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                cv.px(OX + ox + i, OY + oy + j, LEGEND[ch])


def lpx(cv, x, y, ch):
    cv.px(OX + x, OY + y, LEGEND[ch])


def draw_stand(cv, dy=0, crouch=0, eye="E", hat_dy=0, l_hand=0, r_hand=0, spread=0):
    """player/build.py draw_front 정면 축약판: 다리(spread=무릎 벌림) → 몸통 → 팔 → 머리 → 모자."""
    # 다리
    cols = ((4 - spread, 6 - spread), (8 + spread, 10 + spread))
    top = 15 + dy + crouch * 2
    for (x0, x1) in cols:
        for y in range(top, GROUND - 1):
            for x in range(x0, x1 + 1):
                lpx(cv, x, y, "8" if x == x0 else "6")
        seg0 = BOOT_DOWN[0][0:3] if x0 < 7 else BOOT_DOWN[0][4:7]
        blit(cv, [seg0, "KKK"], x0, GROUND - 1)
    for y in range(top, GROUND + 1):
        if cv.get(OX + 6, OY + y) and cv.get(OX + 8, OY + y) and not spread:
            lpx(cv, 7, y, "K")
    torso = TORSO_DOWN
    if crouch:
        torso = torso[:1] + torso[1 + crouch:]
    blit(cv, torso, 4, 9 + dy + crouch)
    # 일기장 (화면 오른쪽 허리)
    by = 9 + dy + crouch + torso.index("KKK6KKKK") + 1
    lpx(cv, 10, by, "D"); lpx(cv, 11, by, "D"); lpx(cv, 10, by + 1, "D"); lpx(cv, 11, by + 1, "K")
    # 팔
    for side, ax, hoff in (("l", 2, l_hand), ("r", 12, r_hand)):
        t = 10 + dy + crouch
        b = 15 + dy + hoff + crouch
        for y in range(t, b + 1):
            for x in (ax, ax + 1):
                lpx(cv, x, y, "5" if (x == ax and side == "l" and y == t) else "3")
        hx = ax if side == "l" else ax + 1
        lpx(cv, hx, b + 1, "c"); lpx(cv, hx + (1 if side == "l" else -1), b + 1, "a")
    hy = 5 + dy + crouch
    face = [FACE_DOWN[0].replace("E", eye)] + FACE_DOWN[1:]
    blit(cv, face, 4, hy)
    blit(cv, HAT, 3, hy - 4 + hat_dy)


# 무릎 꿇은 자세(정면) — 셀아웃(K/0)·림(4)까지 손으로 찍은 지도 (자동 셀아웃은 1~2px 무릎·주먹을 먹어 버린다).
# 화면 왼쪽 = 세운 무릎(장화가 땅에), 화면 오른쪽 = 땅에 댄 무릎. 왼손은 세운 무릎 바깥, 오른손 주먹은 땅을 짚는다.
# 고개 숙임: 모자가 한 줄 내려와 눈띠를 가리고, 얼굴은 챙 그늘(a) 한 줄 + 턱 한 줄만.
KLEG = dict(LEGEND)
KLEG.update({"0": G[0], "4": G[4], "H": A[7], "J": A[9]})
KNEEL_BODY = [            # 로컬 y15..23 (몸통·다리·팔), 16폭
    "....03311134....",   # 15 깃
    "..001533333104..",   # 16 어깨
    "..031533331134..",   # 17
    "..030006000034..",   # 18 허리띠 + 버클
    "..03886633DD34..",   # 19 세운 무릎머리 · 일기장
    "..0c866633D0034.",   # 20 왼손(무릎 바깥) · 오른팔이 바깥으로 꺾임
    "....03103134034.",   # 21 정강이 그늘 · 자락
    "...0111086640ca4",   # 22 장화 · 땅에 댄 무릎 · 주먹
    "...44444444..44.",   # 23 바닥 림
]
KNEEL_HEAD_DOWN = [       # 로컬 y9..14
    ".....000004.....",
    "....01111114....",
    "....01111114....",
    "...4111111114...",
    "....0aaaaaa4....",
    ".....0acca4.....",
]
KNEEL_HEAD_UP = [         # 로컬 y8..14 (눈띠 보임, 턱 한 줄 생략)
    ".....000004.....",
    "....01111114....",
    "....01111114....",
    "...4111111114...",
    "....0a{E}aa0a4....",
    "....0eecccc4....",
    ".....0cccc4.....",
]


def draw_kneel(cv, head_up=0, eye="H"):
    """head_up: 0 = 고개 숙임(눈 가림, f8~f12), 1 = 고개 듦(눈빛, f13). eye: H = A23, J = A25(켜지는 순간)."""
    def put(rows, oy):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    cv.px(OX + i, OY + oy + j, KLEG[ch])
    put(KNEEL_BODY, 15)
    if head_up:
        put([r.replace("{E}", eye) for r in KNEEL_HEAD_UP], 8)
    else:
        put(KNEEL_HEAD_DOWN, 9)


def finish_char(cv):
    outline_inside(cv, G[0])
    rim_light(cv.im, G[4], side="rb")
    return cv


def char_frame(fn, **kw):
    cv = Canvas(32, 32)
    fn(cv, **kw)
    return finish_char(cv)


# ============================================================ 흙 (무채) 셰이더
SOIL = {"out": G[0], "deep": G[2], "shadow": G[3], "base": G[5], "light": G[7], "peb": G[8]}


def shade_soil(mask, seed=0, rim=True, crack=None, edge="hard"):
    """mask: set((x,y)) → 흙덩어리 Canvas. 빛 좌상단: 윤곽 G00(우·하 림 G04), 안쪽 첫 줄 좌상 G07,
    우하 G03, 나머지 G05. 덩이 질감은 결정적 해시로 G03 알갱이·G08 자갈을 드물게."""
    cv = Canvas(32, 32)
    inside = lambda x, y: (x, y) in mask  # noqa: E731
    for (x, y) in mask:
        is_edge = any(not inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if is_edge:
            if edge == "soft":     # 낮은 흙더미: 검은 윤곽 대신 윗면 밝은 테·아랫면 어두운 테 (뚜껑처럼 보이지 않게)
                up = not inside(x, y - 1) or not inside(x - 1, y)
                cv.px(x, y, G[6] if up else G[2]); continue
            cv.px(x, y, SOIL["out"] if edge == "hard" else G[1]); continue
        tl = (not inside(x - 1, y - 1)) or (not inside(x - 2, y)) or (not inside(x, y - 2))
        br = (not inside(x + 1, y + 1)) or (not inside(x + 2, y)) or (not inside(x, y + 2))
        if tl and not br:
            c = SOIL["light"]
        elif br and not tl:
            c = SOIL["shadow"]
        else:
            c = SOIL["base"]
        hsh = (x * 73856093 ^ y * 19349663 ^ seed * 83492791) & 0xff
        if c == SOIL["base"] and hsh < 22:
            c = SOIL["shadow"]
        elif c == SOIL["base"] and hsh > 246:
            c = SOIL["peb"]
        cv.px(x, y, c)
    if rim and edge != "soft":
        rim_light(cv.im, G[4], side="rb", only=rgba(SOIL["out"] if edge == "hard" else G[1])[:3])
    return cv


def ellipse_mask(cx, cy, rx, ry):
    m = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                m.add((x, y))
    return m


def mask_of(cv):
    return {(x, y) for y in range(cv.h) for x in range(cv.w) if cv.p[x, y][3]}


def clip_ground(m, gy=31):
    return {(x, y) for (x, y) in m if y <= gy}


# ============================================================ 소용돌이 알갱이
def spiral_arms(cv, cx, cy, r_head, phase_deg, arms=3, span=80, grow=4.0, aspect=0.42,
                which="all", ember_arm=None, cols=None):
    """나선 팔(끊김 없는 호): 머리(밝음)가 반지름 r_head, 꼬리로 갈수록 반지름 +grow·어두움
    (바깥에서 안으로 감겨 드는 흙). 회전은 화면 반시계. which = back(중심보다 위=둔덕 뒤) | front | all."""
    cols = cols or [G[4], G[5], G[6], G[8]]
    for k in range(arms):
        th0 = phase_deg + k * 360.0 / arms
        pts = []
        steps = max(2, int(span / 5))
        for j in range(steps + 1):
            t = j / steps                       # 0 = 머리, 1 = 꼬리
            th = math.radians(th0 - t * span)
            r = r_head + t * grow
            p = (int(round(cx + r * math.cos(th))), int(round(cy - r * math.sin(th) * aspect)))
            if not pts or pts[-1][0] != p:
                pts.append((p, t))
        for (x, y), t in reversed(pts):         # 꼬리부터 → 머리가 위에
            if which == "back" and y > cy:
                continue
            if which == "front" and y <= cy:
                continue
            c = cols[min(len(cols) - 1, int((1 - t) * (len(cols) - 1) + 0.5))]
            if ember_arm is not None and k == ember_arm and t == 0:
                c = A[7]
            cv.px(x, y, c)


# ============================================================ player_birth 프레임
FRAME_MS = [200, 200, 190, 180, 180, 200, 220, 240, 260, 200, 120, 160, 240, 300, 200, 170, 150, 260]
BURST = 10
CX, CY = 16, 29     # 소용돌이 중심 (발 피벗 (16,31) 위 2px — 둔덕 무게중심)


def kneel_mask():
    cv = Canvas(32, 32)
    draw_kneel(cv)
    return mask_of(cv)


def lump_mask(stage):
    """B 단계 덩어리 실루엣 (꼭대기가 무릎 형체의 모자 높이 y17 을 넘지 않는다): 1 흙기둥, 2 머리 혹·어깨."""
    m = set()
    if stage == 1:
        m |= ellipse_mask(16, 29.0, 7.0, 3.2)        # 밑동
        m |= ellipse_mask(16, 25.5, 4.8, 5.0)        # 기둥
        m |= ellipse_mask(15.5, 21.5, 3.0, 2.6)      # 끝 (아직 둥근)
    else:
        m |= ellipse_mask(16, 29.0, 7.5, 3.0)
        m |= ellipse_mask(16.5, 25.5, 6.2, 4.6)      # 몸통 덩이 (앞으로 숙임)
        m |= ellipse_mask(13.5, 28.0, 3.0, 3.2)      # 세운 무릎 자리
        m |= ellipse_mask(16.0, 19.8, 4.2, 2.8)      # 머리 혹 (모자 자리)
        m |= ellipse_mask(21.8, 28.5, 1.7, 3.0)      # 땅 짚는 팔 자리
    return clip_ground(m)


def cracks(cv, pts, col):
    for (x, y) in pts:
        if cv.get(x, y) and cv.get(x, y)[:3] != rgba(G[0])[:3]:
            cv.px(x, y, col)


# 무릎 형체 위 잔불 실금 = 나중 인물의 구조선 자리: 모자 챙(y20) · 가슴 세로 금(x16) · 허리띠(y26) · 무릎(y28)
KNEEL_CRACK_FAINT = [(14, 20), (15, 20), (18, 20), (16, 24), (16, 25), (17, 26), (18, 26)]
KNEEL_CRACK_FULL = KNEEL_CRACK_FAINT + [(13, 20), (16, 20), (17, 20), (15, 23), (13, 26), (14, 26),
                                        (19, 26), (16, 26), (13, 28), (19, 28), (20, 25)]
KNEEL_CRACK_CORE = [(16, 24), (16, 25), (16, 26), (17, 26), (15, 23)]
LUMP1_CRACK = [(16, 26), (16, 27)]
LUMP2_CRACK = [(16, 24), (16, 25), (17, 26), (17, 27)]


def soil_kneel(seed, crack_pts=(), crack_col=None, swell=0):
    m = kneel_mask()
    if swell:   # 터지기 직전: 1px 부풀음 (윗면·옆면)
        m2 = set(m)
        for (x, y) in m:
            for dx, dy in ((1, 0), (-1, 0), (0, -1)):
                m2.add((x + dx, y + dy))
        m = clip_ground(m2)
    cv = shade_soil(m, seed=seed)
    if crack_pts:
        cracks(cv, crack_pts, crack_col)
    return cv


def burst_rays(cv, cx, cy, step):
    """잔불 터짐: 가슴에서 7방향 불티 줄(아래는 몸이 가림). step 0 = 터짐(밝음·몸에 붙음),
    1 = 바깥으로 떨어져 나감, 2 = 꺼져 가는 점."""
    dirs = [(0, -1), (1, -1), (1, 0), (1, 1), (-1, 1), (-1, 0), (-1, -1)]
    rad = [(6, 10), (9, 12), (11, 13)][step]
    for i, (dx, dy) in enumerate(dirs):
        r0, r1 = rad
        r1 += (i % 3) - 1
        ln = math.hypot(dx, dy)
        for r in range(r0, r1 + 1):
            x = cx + round(dx / ln * r)
            y = cy + round(dy / ln * r * 0.8)
            t = (r - r0) / max(1, r1 - r0)
            if step == 0:
                c = A[9] if t > 0.7 else (A[10] if t > 0.35 else A[11])   # 안쪽이 가장 뜨겁다
            elif step == 1:
                if t < 0.55:
                    continue
                c = A[9] if t > 0.85 else A[7]
            else:
                if r != r1:
                    continue
                c = A[5]
            cv.px(x, y, c)


def clods(cv, items):
    """떨어지는 흙 조각: (x, y, kind). kind 2 = 2x2, 1 = 2x1, 0 = 점."""
    for x, y, k in items:
        if k == 2:
            cv.px(x, y, G[7]); cv.px(x + 1, y, G[5]); cv.px(x, y + 1, G[5]); cv.px(x + 1, y + 1, G[3])
        elif k == 1:
            cv.px(x, y, G[6]); cv.px(x + 1, y, G[4])
        else:
            cv.px(x, y, G[6])


def ground_pile(w, seed, gy=31, h=2.6):
    """무릎 주변에 남은 흙더미: 낮은 반타원 + 좌우 작은 둔덕(고르지 않게). w = 반폭."""
    if w <= 0:
        return Canvas(32, 32)
    m = ellipse_mask(16, gy + 0.6, w, h)
    m |= ellipse_mask(16 - w * 0.55, gy + 0.4, w * 0.35, h * 1.15)
    m |= ellipse_mask(16 + w * 0.6, gy + 0.6, w * 0.3, h * 0.95)
    return shade_soil(clip_ground(m), seed=seed, edge="soft")


def soil_bits(cv, pts):
    """인물 위에 얹힌 흙(무조건 덮음): (x, y, gray index)."""
    for (x, y, gi) in pts:
        cv.px(x, y, G[gi])


def kneel_char(**kw):
    cv = Canvas(32, 32)
    draw_kneel(cv, **kw)
    return cv


def build_birth():
    frames = []

    # ---------------- A 모임 f0..f4 : 3갈래 나선이 안으로 감겨 들며 둔덕이 자란다
    heap = [None, (2.6, 1.0), (3.8, 1.6), (5.0, 2.2), (6.2, 3.0)]
    radius = [12, 10, 8.5, 7, 6]
    span = [70, 85, 95, 100, 100]
    for i in range(5):
        cv = Canvas(32, 32)
        kw = dict(span=span[i], grow=4.5 - i * 0.5, ember_arm=(0 if i >= 2 else None))
        spiral_arms(cv, CX, CY, radius[i], 90 + i * 50, which="back", **kw)
        if heap[i]:
            rx, ry = heap[i]
            cv.paste(shade_soil(clip_ground(ellipse_mask(16, 31.6, rx, ry * 1.25)), seed=i, edge="soft"))
        else:
            for (x, y, gi) in ((15, 31, 4), (16, 30, 5), (17, 31, 4)):   # 첫 장: 중심에 먼지 세 점
                cv.px(x, y, G[gi])
        spiral_arms(cv, CX, CY, radius[i], 90 + i * 50, which="front", **kw)
        frames.append(cv)

    # ---------------- B 솟음 f5..f7
    cv = Canvas(32, 32)                                   # f5 둥근 둔덕 (속에 잔불 한 점)
    spiral_arms(cv, CX, CY, 7, 90 + 5 * 50, span=90, grow=2.5, which="back")
    cv.paste(shade_soil(clip_ground(ellipse_mask(16, 31.0, 7.4, 5.4)), seed=5, edge="soft"))
    cracks(cv, [(16, 28)], A[3])
    spiral_arms(cv, CX, CY, 7, 90 + 5 * 50, span=90, grow=2.5, which="front", ember_arm=1)
    frames.append(cv)

    cv = Canvas(32, 32)                                   # f6 흙기둥
    spiral_arms(cv, CX, CY, 8, 90 + 6 * 50, span=70, grow=2, which="back", cols=[G[4], G[5], G[7]])
    cv.paste(shade_soil(lump_mask(1), seed=6, edge="mid"))
    cracks(cv, LUMP1_CRACK, A[3])
    spiral_arms(cv, CX, CY, 8, 90 + 6 * 50, span=70, grow=2, which="front", cols=[G[4], G[5], G[7]])
    frames.append(cv)

    cv = Canvas(32, 32)                                   # f7 머리 혹·어깨·무릎 자리
    cv.paste(shade_soil(lump_mask(2), seed=7))
    cracks(cv, LUMP2_CRACK, A[3])
    spiral_arms(cv, CX, CY, 9, 90 + 7 * 50, span=50, grow=1, which="front", cols=[G[4], G[6]])
    frames.append(cv)

    # ---------------- C 굳음 f8..f10
    frames.append(soil_kneel(8, KNEEL_CRACK_FAINT, A[3]))            # f8 형체, 실금 희미 (A19)
    cv = soil_kneel(9, KNEEL_CRACK_FULL, A[5])                       # f9 실금 A21 + 심 A23
    cracks(cv, KNEEL_CRACK_CORE, A[7])
    for (x, y) in ((11, 18), (21, 17), (9, 25)):                     # 들뜬 흙 알갱이
        cv.px(x, y, G[6])
    frames.append(cv)
    cv = soil_kneel(10, KNEEL_CRACK_FULL, A[9], swell=1)             # f10 터짐 (burstFrame)
    cracks(cv, KNEEL_CRACK_CORE, A[11])
    burst_rays(cv, 16, 24, 0)
    frames.append(cv)

    # ---------------- D 무릎 f11..f13
    # f11: 껍질이 깨져 인물이 드러남 — 모자·어깨·무릎에 흙이 얹혀 있고, 큰 조각이 튕겨 나간다
    cv = Canvas(32, 32)
    cv.paste(ground_pile(10, 11))
    k = kneel_char()
    soil_bits(k, [(14, 16, 5), (15, 16, 7), (13, 17, 5), (14, 17, 7), (15, 17, 6), (16, 17, 5),
                  (10, 24, 7), (11, 24, 5), (10, 25, 5), (20, 24, 6), (21, 24, 5), (21, 25, 4),
                  (12, 27, 7), (13, 27, 6), (17, 29, 5), (18, 29, 4)])
    cv.paste(k)
    clods(cv, [(7, 17, 2), (24, 16, 2), (5, 23, 1), (26, 22, 1), (13, 13, 0), (20, 12, 0)])
    burst_rays(cv, 16, 24, 1)
    frames.append(cv)

    # f12: 조각이 떨어지는 중, 얹힌 흙 줄어듦
    cv = Canvas(32, 32)
    cv.paste(ground_pile(10, 12))
    k = kneel_char()
    soil_bits(k, [(14, 17, 6), (15, 17, 5), (10, 24, 6), (10, 25, 4), (12, 27, 6), (21, 24, 5)])
    cv.paste(k)
    clods(cv, [(6, 22, 2), (25, 21, 1), (4, 27, 1), (27, 26, 0), (12, 16, 0), (21, 19, 0)])
    burst_rays(cv, 16, 24, 2)
    frames.append(cv)

    # f13: 고개를 들어 눈빛이 켜짐 (A25 한 장), 마지막 알갱이 바닥에 닿음
    cv = Canvas(32, 32)
    cv.paste(ground_pile(9.5, 13))
    k = kneel_char(head_up=1, eye="J")
    soil_bits(k, [(10, 24, 5), (12, 27, 6)])
    cv.paste(k)
    clods(cv, [(5, 29, 1), (26, 29, 0), (8, 30, 0)])
    frames.append(cv)

    # ---------------- E 일어섬 f14..f16
    # f14: 짚은 손을 떼고 무릎을 펴기 시작 — 반쯤 일어선 쪼그림
    cv = Canvas(32, 32)
    cv.paste(ground_pile(8, 14, h=2.2))
    cv.paste(char_frame(draw_stand, dy=3, crouch=1, spread=1, l_hand=-1, r_hand=-1))
    frames.append(cv)
    # f15: 거의 섬
    cv = Canvas(32, 32)
    cv.paste(ground_pile(6, 15, h=1.8))
    cv.paste(char_frame(draw_stand, dy=2, crouch=0, r_hand=0))
    frames.append(cv)
    # f16: 다 섰다가 숨 한 번 내려앉음 (대기 2~4 프레임과 같은 높이)
    cv = Canvas(32, 32)
    cv.paste(char_frame(draw_stand, dy=1, hat_dy=0))
    clods(cv, [(10, 31, 0), (21, 31, 0)])
    frames.append(cv)

    # ---------------- f17 = player_idle down 0 원본
    idle = Image.open(os.path.join(OUT_PLAYER, "player_idle.png")).convert("RGBA")
    cv = Canvas(32, 32)
    cv.paste(idle.crop((0, 0, 16, 24)), OX, OY)
    frames.append(cv)

    assert len(frames) == len(FRAME_MS), (len(frames), len(FRAME_MS))
    return frames


# ============================================================ fx/birth_dust (64x32)
DW, DH = 64, 32
DPX, DPY = 32, 22      # 피벗 = 주인공 발
SWIRL_MS = [110, 110, 110, 110]
SCATTER_MS = [70, 90, 110, 140, 170]


def dust_arm(cv, th_head, r_head, r_tail, span, cols, fade_tail=True, thick_head=True):
    """바닥 나선 팔 하나(끊김 없는 호). th_head(도) 에서 꼬리 쪽(시계 반대 반대)으로 span 만큼, 반지름 r_head→r_tail."""
    pts = []
    n = max(2, int(span / 3))
    for j in range(n + 1):
        t = j / n
        th = math.radians(th_head - t * span)
        r = r_head + (r_tail - r_head) * t
        p = (int(round(DPX + r * math.cos(th))), int(round(DPY - r * math.sin(th) * 0.36)))
        if not pts or pts[-1][0] != p:
            pts.append((p, t))
    for idx, ((x, y), t) in enumerate(reversed(pts)):
        if fade_tail and t > 0.8 and idx % 2:
            continue
        c = cols[min(len(cols) - 1, int(t * len(cols)))]
        cv.px(x, y, c)
    if thick_head and pts:
        (x, y), _ = pts[0]
        cv.px(x, y + 1, cols[1])            # 머리 2px (아래로 두께)
    return pts


def dust_swirl(i):
    """바닥 흙 소용돌이 루프 4f: 3갈래 나선(머리 반지름 14 → 꼬리 27, 120° 호), 프레임당 30° 회전
    (3겹 대칭 → 4f = 120° 이음새 없음). 주인공 시트의 안쪽 나선(반지름 6~12)보다 바깥을 맡는다."""
    cv = Canvas(DW, DH)
    cols = [G[9], G[7], G[6], G[5], G[4]]       # 머리 → 꼬리
    for k in range(3):
        th = 90 + i * 30 + k * 120
        pts = dust_arm(cv, th, 14, 27, 120, cols)
        # 팔마다 잔불 한 점: 호의 1/3 지점 1px 위, 프레임마다 A21/A23 번갈아 깜빡
        (x, y), _ = pts[len(pts) // 3]
        cv.px(x, y - 1, A[7] if (i + k) % 2 == 0 else A[5])
    return cv


def dust_scatter(i):
    """흩어짐 5f (burstFrame 에 시작): 나선 팔이 바깥으로 튕겨 펴지고, 흙먼지 덩이가 피어오르고, 잔불 몇 점이 튄다."""
    cv = Canvas(DW, DH)
    # 1) 바깥으로 펴지며 짧아지는 팔
    grow = [3, 6, 8, 9, 10][i]
    span = [90, 70, 50, 30, 16][i]
    cols = [[G[10], G[8], G[6], G[5]], [G[8], G[6], G[5], G[4]], [G[6], G[5], G[4]], [G[5], G[4]], [G[4], G[3]]][i]
    for k in range(3):
        th = 90 + 4 * 30 + k * 120 + i * 12
        dust_arm(cv, th, 14 + grow, 22 + grow * 0.6, span, cols, fade_tail=(i >= 1), thick_head=(i <= 1))
    # 2) 흙먼지 덩이 (솟아오르며 커졌다가 옅어짐) — 체커 디더 대신 덩이 모양
    PUFF = [
        [("ab", 0)],                                   # 0: 2x1
        [(".ab", 0), ("abc", 1)],                      # 1: 3x2
        [(".abb.", 0), ("abbcc", 1), (".cc..", 2)],    # 2: 5x3
        [(".b.c.", 0), ("c.c.c", 1)],                  # 3: 흩어짐
        [("..c..", 1)],                                # 4: 한 점
    ]
    pcol = {"a": G[7], "b": G[6], "c": G[4]}
    if i >= 3:
        pcol = {"a": G[5], "b": G[5], "c": G[3]}
    stage = [1, 2, 2, 3, 4][i]
    puffs = [(-19, 1), (17, 0), (-9, 6), (8, 7), (-1, -5)]
    for n, (dx, dy) in enumerate(puffs):
        if i == 0 and n == 4:
            continue
        sx = DPX + int(round(dx * (1 + i * 0.18))) - 2
        sy = DPY + dy - i - 1
        st = stage if n % 2 == 0 else max(0, stage - 1)
        for row, ry in PUFF[st]:
            for xx, ch in enumerate(row):
                if ch != ".":
                    cv.px(sx + xx, sy + ry, pcol[ch])
    # 3) 잔불 불티 6점: 위로 튀었다가 식으며 떨어진다
    sparks = [(-6, -6), (7, -8), (-13, -3), (13, -4), (2, -11), (-3, -10)]
    for n, (dx, dy) in enumerate(sparks):
        if i == 0 and n > 3:
            continue
        if i >= 3 and n % 2 == 0:
            continue
        x = DPX + int(round(dx * (1 + i * 0.35)))
        y = DPY + int(round(dy * (0.75 + i * 0.3))) + (i * i) // 2
        c = [A[10], A[9], A[7], A[5], A[3]][i]
        cv.px(x, y, c)
        if i <= 1:   # 꼬리(온 방향)
            cv.px(x - (1 if dx > 0 else -1), y + 1, [A[7], A[5]][i])
    return cv


def build_dust():
    return [dust_swirl(i) for i in range(4)] + [dust_scatter(i) for i in range(5)]


# ============================================================ 저장
def save_sheet(frames, fw, fh, path):
    sheet = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.alpha_composite(f.im, (i * fw, 0))
    sheet.save(path)
    return sheet


def used_colors(frames):
    s = set()
    for f in frames:
        for y in range(f.h):
            for x in range(f.w):
                v = f.p[x, y]
                if v[3]:
                    s.add("#%02x%02x%02x" % v[:3])
    return s


def check_palette(frames, allow, name):
    bad = used_colors(frames) - set(allow)
    assert not bad, "%s: 팔레트 밖 색 %s" % (name, bad)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=1)


# ============================================================ 미리보기
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)


def floor_tiles():
    """1층 황폐 바닥(roomFloors.start) 4변형. 없으면 None."""
    try:
        with open(os.path.join(ROOT, "assets", "tiles", "stage1.json"), encoding="utf-8") as fp:
            tj = json.load(fp)
        ts = Image.open(os.path.join(ROOT, "assets", "tiles", "stage1.png")).convert("RGBA")
        idx = (tj.get("roomFloors") or {}).get("start") or tj["tiles"]["1"]
        cols = tj.get("columns", ts.width // 16)
        return [ts.crop(((i % cols) * 16, (i // cols) * 16, (i % cols) * 16 + 16, (i // cols) * 16 + 16)) for i in idx]
    except Exception:
        return None


def floor_patch(w, h):
    tiles = floor_tiles()
    im = Image.new("RGBA", (w, h), rgba(G[2]))
    for ty in range(0, h, 16):
        for tx in range(0, w, 16):
            if tiles:
                t = tiles[((tx // 16) * 7 + (ty // 16) * 13 + (tx // 16) * (ty // 16)) % len(tiles)]
                im.alpha_composite(t, (tx, ty))
    return im


def dust_for(birth_i):
    """목업 시간표: 탄생 f0~f9 동안 소용돌이 루프, f10(burst)부터 흩어짐 5장, 이후 없음."""
    if birth_i < BURST:
        return ("swirl", birth_i % 4)
    j = birth_i - BURST
    return ("scatter", 4 + j) if j < 5 else None


def compose_scene(birth, dust, bi, w=96, h=64):
    """바닥 패치 위 발 피벗을 (w/2, h-14) 에 두고 dust(바닥) → 그림자 없음 → 주인공 순서로."""
    im = floor_patch(w, h)
    fx, fy = w // 2, h - 14
    d = dust_for(bi)
    if d:
        im.alpha_composite(dust[d[1]].im, (fx - DPX, fy - DPY))
    im.alpha_composite(birth[bi].im, (fx - 16, fy - 31))
    return im


def make_preview(birth, dust):
    S = 4
    gap = 6
    n = len(birth)
    # 1) 4배 프레임 띠 (체커 없이 1층 바닥 본색 G02 배경, 2행으로 나눔)
    per_row = 9
    cw, ch = 32 * S, 32 * S
    strip_w = per_row * (cw + gap) + gap
    strip_h = 2 * (ch + 22 + gap) + gap
    # 2) birth_dust 띠 4배
    dw, dh = DW * S, DH * S
    dust_cols = 5
    dust_h = 2 * (dh + 22 + gap) + gap
    # 3) 목업: 키프레임 6장, 2배와 4배
    keys = [1, 4, 6, 8, 10, 11, 13, 15, 17]
    mw, mh = 96, 64
    mock2_w = len(keys) * (mw * 2 + gap) + gap
    mock4_keys = [3, 9, 10, 12, 17]
    mock4_w = len(mock4_keys) * (mw * 4 + gap) + gap
    Wt = max(strip_w, dust_cols * (dw + gap) + gap, mock2_w, mock4_w)
    Ht = 24 + strip_h + 24 + dust_h + 24 + (mh * 2 + 22 + gap) + 24 + (mh * 4 + 22 + gap)
    img = Image.new("RGB", (Wt, Ht), (34, 34, 38))
    d = ImageDraw.Draw(img)
    y = 4
    d.text((6, y), "player_birth 32x32 x%d  (x4)  sum %dms  burstFrame=%d  pivot(16,31)" % (n, sum(FRAME_MS), BURST),
           fill=(235, 235, 235), font=FONT)
    y += 20
    for i, f in enumerate(birth):
        r, c = divmod(i, per_row)
        ox = gap + c * (cw + gap)
        oy = y + r * (ch + 22 + gap)
        d.text((ox, oy), "f%d %dms%s" % (i, FRAME_MS[i], " BURST" if i == BURST else ""),
               fill=(255, 200, 120) if i == BURST else (200, 200, 200), font=FONT)
        cell = Image.new("RGBA", (32, 32), rgba(G[2]))
        cell.alpha_composite(f.im)
        img.paste(cell.resize((cw, ch), Image.NEAREST).convert("RGB"), (ox, oy + 18))
        # 피벗 표시 (발): 작은 눈금
        px_, py_ = ox + 16 * S, oy + 18 + 32 * S
        d.line([px_ - 6, py_ + 2, px_ + 6, py_ + 2], fill=(90, 160, 220))
    y += strip_h
    d.text((6, y), "fx/birth_dust 64x32 x9  (x4)  swirl loop f0-3 / scatter f4-8  pivot(32,22)", fill=(235, 235, 235), font=FONT)
    y += 20
    labels = ["swirl0", "swirl1", "swirl2", "swirl3", "scat0", "scat1", "scat2", "scat3", "scat4"]
    for i, f in enumerate(dust):
        r, c = divmod(i, dust_cols) if i < 4 else (1, i - 4)
        if i < 4:
            r, c = 0, i
        ox = gap + c * (dw + gap)
        oy = y + r * (dh + 22 + gap)
        ms = (SWIRL_MS + SCATTER_MS)[i]
        d.text((ox, oy), "%s %dms" % (labels[i], ms), fill=(200, 200, 200), font=FONT)
        cell = Image.new("RGBA", (DW, DH), rgba(G[2]))
        cell.alpha_composite(f.im)
        img.paste(cell.resize((dw, dh), Image.NEAREST).convert("RGB"), (ox, oy + 18))
    y += dust_h
    d.text((6, y), "mockup x2 (1F start floor + birth_dust + player_birth)", fill=(235, 235, 235), font=FONT)
    y += 20
    for k, bi in enumerate(keys):
        sc = compose_scene(birth, dust, bi, mw, mh)
        ox = gap + k * (mw * 2 + gap)
        d.text((ox, y), "f%d" % bi, fill=(200, 200, 200), font=FONT)
        img.paste(sc.resize((mw * 2, mh * 2), Image.NEAREST).convert("RGB"), (ox, y + 18))
    y += mh * 2 + 22 + gap
    d.text((6, y), "mockup x4 (camera zoom 4 during birth)", fill=(235, 235, 235), font=FONT)
    y += 20
    for k, bi in enumerate(mock4_keys):
        sc = compose_scene(birth, dust, bi, mw, mh)
        ox = gap + k * (mw * 4 + gap)
        d.text((ox, y), "f%d" % bi, fill=(200, 200, 200), font=FONT)
        img.paste(sc.resize((mw * 4, mh * 4), Image.NEAREST).convert("RGB"), (ox, y + 18))
    img.save(os.path.join(HERE, "preview.png"))


def make_gifs(birth, dust):
    S = 4
    seq = []
    for i in range(len(birth)):
        seq.append(compose_scene(birth, dust, i, 96, 64).resize((96 * S, 64 * S), Image.NEAREST))
    # 마지막 프레임 뒤에 대기 루프 한 바퀴를 붙여 이음 확인
    idle = Image.open(os.path.join(OUT_PLAYER, "player_idle.png")).convert("RGBA")
    with open(os.path.join(OUT_PLAYER, "player_idle.json"), encoding="utf-8") as fp:
        idle_ms = json.load(fp)["frameDurationsMs"]
    for j in range(len(idle_ms)):
        im = floor_patch(96, 64)
        im.alpha_composite(idle.crop((j * 16, 0, j * 16 + 16, 24)), (48 - 8, 50 - 23))
        seq.append(im.resize((96 * S, 64 * S), Image.NEAREST))
    durs = FRAME_MS + idle_ms
    pal = [s.convert("RGB").convert("P", palette=Image.ADAPTIVE) for s in seq]
    pal[0].save(os.path.join(HERE, "gif", "birth_scene_x4.gif"), save_all=True, append_images=pal[1:],
                loop=0, duration=durs, disposal=2)
    # 소용돌이 루프만
    sw = []
    for i in range(4):
        im = floor_patch(DW, DH)
        im.alpha_composite(dust[i].im)
        sw.append(im.resize((DW * S, DH * S), Image.NEAREST).convert("RGB").convert("P", palette=Image.ADAPTIVE))
    sw[0].save(os.path.join(HERE, "gif", "birth_dust_swirl_x4.gif"), save_all=True, append_images=sw[1:],
               loop=0, duration=SWIRL_MS, disposal=2)


def main():
    birth = build_birth()
    dust = build_dust()
    allow_char = set(G) | set(A)
    check_palette(birth, allow_char, "player_birth")
    check_palette(dust, set(G) | set(A), "birth_dust")

    save_sheet(birth, 32, 32, os.path.join(OUT_PLAYER, "player_birth.png"))
    # 이음 검증: 마지막 프레임 == 대기 down 0
    idle = Image.open(os.path.join(OUT_PLAYER, "player_idle.png")).convert("RGBA").crop((0, 0, 16, 24))
    assert birth[-1].im.crop((OX, OY, OX + 16, OY + 24)).tobytes() == idle.tobytes()
    gray_n = len(used_colors(birth) & set(G))
    acc = sorted(16 + A.index(c) for c in used_colors(birth) & set(A))
    write_json(os.path.join(OUT_PLAYER, "player_birth.json"), {
        "image": "player_birth.png",
        "action": "birth",
        "frameWidth": 32,
        "frameHeight": 32,
        "frames": len(birth),
        "directions": ["down"],
        "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column",
        "fps": round(1000 * len(FRAME_MS) / sum(FRAME_MS), 2),
        "frameDurationsMs": FRAME_MS,
        "totalMs": sum(FRAME_MS),
        "loop": False,
        "pivot": {"x": 16, "y": 31},
        "pivotNote": "피벗 (16,31) = 주인공 발. 16x24 player_* 시트 피벗 (8,23) 과 같은 점 — 프레임 안 (8,8) 에 16x24 몸이 놓인다.",
        "burstFrame": BURST,
        "phases": {
            "gather": [0, 4], "rise": [5, 7], "form": [8, 10], "kneel": [11, 13], "standUp": [14, 17]
        },
        "eyeOpenFrame": 13,
        "endsWith": "player_idle_down frame 0 (f17 = 픽셀 동일, 이어서 player_idle_down 재생)",
        "skippable": "아무 키 → 마지막 프레임(=idle) 으로 건너뛰기 (시스템, 48라운드 Q6)",
        "camera": "재생 동안 시스템이 카메라 약 4배 확대 → 끝나면 2배 복귀 (48라운드 Q6). 시트 크기 불변.",
        "fx": {"under": "fx/birth_dust", "swirlUntilFrame": BURST, "scatterAtFrame": BURST},
        "palette": "parts/art/palette/lopad.json (gray + floor 1 accent %s, runtime swap 대상; 백열 코어·무기 보조 없음)" % acc,
        "colors": {"gray": gray_n, "accent": len(acc)},
    })

    save_sheet(dust, DW, DH, os.path.join(OUT_FX, "birth_dust.png"))
    acc_d = sorted(16 + A.index(c) for c in used_colors(dust) & set(A))
    write_json(os.path.join(OUT_FX, "birth_dust.json"), {
        "image": "birth_dust.png",
        "action": "birth_dust",
        "frameWidth": DW,
        "frameHeight": DH,
        "frames": len(dust),
        "directions": ["any"],
        "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column",
        "fps": 9,
        "frameDurationsMs": SWIRL_MS + SCATTER_MS,
        "loop": False,
        "pivot": {"x": DPX, "y": DPY},
        "anchor": "player_pivot",
        "spawn": "birth_start",
        "depth": "below",
        "followsPlayer": False,
        "segments": {
            "swirl": {"frames": [0, 1, 2, 3], "loop": True, "from": "player_birth frame 0", "until": "player_birth burstFrame"},
            "scatter": {"frames": [4, 5, 6, 7, 8], "loop": False, "at": "player_birth burstFrame", "then": "remove"}
        },
        "segmentsFallback": "segments 를 읽지 않으면: 0~3 을 loop 로 재생하다가 burstFrame 에 4~8 을 1회 재생하는 것과 같게 처리 요망. 전부 1회 재생해도 깨지지 않는다(약 1초).",
        "pivotNote": "피벗 (32,22) = 주인공 발(= player_birth 피벗 (16,31)). 소용돌이 타원 반지름 약 15~28 x 6~10, 흩어짐 고리 최대 30.",
        "weapon": "any",
        "palette": "parts/art/palette/lopad.json (gray 흙 + floor 1 accent %s 잔불, runtime swap; 백열 코어·무기 보조 없음)" % acc_d,
        "note": "48라운드 Q6 탄생 연출 바닥 이펙트. 흙 알갱이 3갈래 나선(바깥쪽, 주인공 시트의 안쪽 나선과 이어짐) 루프 4f(30°/f, 3겹 대칭 이음새 없음) → burstFrame 에 바깥으로 튕겨 흩어짐 + 먼지 피어오름 + 잔불 몇 점.",
        "colors": {"gray": len(used_colors(dust) & set(G)), "accent": len(acc_d)},
    })
    make_preview(birth, dust)
    make_gifs(birth, dust)
    print("player_birth: %d frames, %d ms, gray %d accent %s" % (len(birth), sum(FRAME_MS), gray_n, acc))
    print("birth_dust: %d frames, accent %s" % (len(dust), acc_d))


if __name__ == "__main__":
    # 49라운드: 혼불 탄생(build.py)으로 대체됨. 이 판을 실행하면 player_birth 를 흙 판으로 덮어쓰므로 --legacy 없이는 멈춘다.
    if "--legacy" not in sys.argv:
        sys.exit("build_soil_v1.py 는 48라운드 흙 탄생 판(보관용)입니다. 다시 만들려면 --legacy")
    main()
