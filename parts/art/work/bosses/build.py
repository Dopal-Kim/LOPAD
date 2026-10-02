#!/usr/bin/env python3
"""LOPAD 보스 2종 스프라이트 빌드 — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/bosses/build.py
입력: parts/art/palette/lopad.json, assets/sprites/player/player_idle.png, assets/sprites/enemies/*_idle.png (크기 비교)
산출:
  assets/sprites/bosses/stage1_<action>.png/.json    1층 보스 양조장주 '취하지 않는 자' 32x48, 피벗 (16,47)
  assets/sprites/bosses/emperor_<action>.png/.json   황제 '평(平)' 48x64, 피벗 (24,63)
      가로 = 프레임, 세로 = 방향 (down/up/left/right). 계약 contracts/art-assets.md §1
  parts/art/work/bosses/preview_<id>.png   전 동작 한눈에 (3배)
  parts/art/work/bosses/preview_scale.png  주인공·적 3종·보스·황제 크기 비교 (바닥 G04)
  parts/art/work/bosses/gif/<id>_<action>_<dir>.gif

디자인
  stage1  양조장주 '취하지 않는 자' 32x48. 술통 몸집의 거구. 민머리, 굵은 콧수염, 맨정신의 날카로운 호박 눈(23).
          롤업한 린넨 셔츠(G12) 위에 가죽 앞치마(G06), 허리에 술병(21)·국자. 왼손에 통나무 망치(자루 G06, 통나무 머리 G07)를
          지팡이처럼 땅에 짚고 서 있다가, 공격 때 들어 올려 가로로 안고 돌진한다(통나무 = 공성추).
          강조: 눈 23 ·예고 눈빛 25 · 앞치마 술 얼룩 19/21 · 술병 21. 무채 11 + 강조 4.
  emperor 황제 '평(平)' 48x64. 늘씬하고 정중한 인간. 은발을 뒤로 넘긴 르네상스풍 군주. 높은 깃의 긴 외투(G12, 은빛 흰 = 1층 램프로는
          회색이지만 8층 램프 스왑 시 거의 무채), 어깨에서 허리로 내려오는 어두운 띠(G06), 검은 장갑·장화.
          오른손(화면 왼쪽) 서류 뭉치(G14), 왼손(화면 오른쪽) 지휘봉(G03, 끝 G13). 강조: 눈 23 · 훈장 21 = 2슬롯. 무채 11 + 강조 2.
  공통: 검정 셀아웃(inside, keep 마스크 예외), 빛 좌상단, 좌/우 뷰는 형태 반전 + 빛 역할 교환 + 보이는 소지품 교체.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "pixel-art-studio", "scripts"))
from pixelstudio import Sprite  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "parts", "art", "work", "player"))
from rimlight import rim_light  # noqa: E402  (공통 후처리, 40라운드 Q1)

OUT_ASSETS = os.path.join(ROOT, "assets", "sprites", "bosses")
os.makedirs(OUT_ASSETS, exist_ok=True)
os.makedirs(os.path.join(HERE, "gif"), exist_ok=True)

with open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8") as fp:
    PAL = json.load(fp)
G = PAL["gray"]
A = PAL["floors"][0]["ramp"]
# 40라운드 Q1: 림라이트 — 우·하 윤곽(빛 좌상단의 반대)의 셀아웃 G00 을 G04 로. 어두운 흙바닥(G00~G02) 대비용.
RIM = G[4]   # G03 은 바닥 G02/G03 잔점에 묻혀 G04 로 (1x 에서 읽히는 첫 단계, G05 부터는 회색 테두리로 보임)
RIM_SIDE = "rb"
DIRS = ["down", "up", "left", "right"]
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
FLOOR = (0x3e, 0x3f, 0x42)   # G04


class Pose:
    def __init__(self, **kw):
        self.body_dx = 0; self.body_dy = 0
        self.head_dx = 0; self.head_dy = 0
        self.l_lift = 0; self.r_lift = 0        # 정면/후면 다리 들림
        self.l_dx = 0; self.r_dx = 0            # 옆면 다리 앞뒤
        self.l_sl = 0; self.r_sl = 0            # 옆면 다리 들림
        self.l_hand = 0; self.r_hand = 0        # 팔 손 y 오프셋
        self.crouch = 0                          # 몸통 압축(아래로)
        self.lean = 0                            # 옆면 머리 앞뒤
        self.eye = None                          # 눈 교체 문자
        self.flash = False
        self.heap = None                         # 1, 2 : 쓰러진 더미 단계
        self.item = {}
        for k, v in kw.items():
            setattr(self, k, v)


class Rig:
    W = 32; H = 48
    LEGEND = {}
    LIGHT_SWAP = {}
    ID = ""
    TIMING = {}
    PIVOT = (16, 47)

    def __init__(self):
        self.GROUND = self.H - 1
        self.PALETTE = [v for v in self.LEGEND.values() if v]
        self._keep = set()

    # ---------- 기본 그리기
    def px(self, s, x, y, ch, only_empty=False, keep=False, swap=False):
        if swap:
            ch = self.LIGHT_SWAP.get(ch, ch)
        if 0 <= x < self.W and 0 <= y < self.H and ch in self.LEGEND and self.LEGEND[ch]:
            if only_empty and s.get(x, y) is not None:
                return
            s.px(x, y, self.LEGEND[ch])
            if keep:
                self._keep.add((x, y))
            else:
                self._keep.discard((x, y))

    def blit(self, s, rows, ox, oy, mirror=False, swap=False, only_empty=False, keep=False):
        for j, row in enumerate(rows):
            n = len(row)
            for i, ch in enumerate(row):
                if ch == ".":
                    continue
                x = ox + (n - 1 - i if mirror else i)
                self.px(s, x, oy + j, ch, only_empty, keep=keep)

    def hline(self, s, x0, x1, y, ch, swap=False, keep=False):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.px(s, x, y, ch, keep=keep)

    def vline(self, s, x, y0, y1, ch, swap=False, keep=False):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.px(s, x, y, ch, keep=keep)

    def box(self, s, x0, y0, x1, y1, ch, swap=False, keep=False):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.hline(s, x0, x1, y, ch, swap=swap, keep=keep)

    def kline(self, s, x0, y0, x1, y1, ch, keep=True, swap=False):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        x, y = x0, y0
        while True:
            self.px(s, x, y, ch, keep=keep)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x += sx
            if e2 <= dx:
                err += dx; y += sy

    def thick_line(self, s, x0, y0, x1, y1, w, hi, lo, swap=False, keep=False):
        """두께 w 의 팔/다리 선. 수직에 가까우면 x 방향으로, 수평에 가까우면 y 방향으로 두껍게. 첫 줄 hi, 나머지 lo."""
        horiz = abs(x1 - x0) > abs(y1 - y0)
        for i in range(w):
            ch = hi if i == 0 else lo
            if horiz:
                self.kline(s, x0, y0 + i, x1, y1 + i, ch, keep=keep)
            else:
                self.kline(s, x0 + i, y0, x1 + i, y1, ch, keep=keep)

    def finish(self, s, p):
        im = s._img(); px = im.load()
        W, H = self.W, self.H
        alpha = [[px[x, y][3] > 0 for x in range(W)] for y in range(H)]
        todo = []
        for y in range(H):
            for x in range(W):
                if alpha[y][x] and (x, y) not in self._keep:
                    if any(not (0 <= x + dx < W and 0 <= y + dy < H) or not alpha[y + dy][x + dx]
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        todo.append((x, y))
        k = tuple(int(self.LEGEND["K"][i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        for x, y in todo:
            px[x, y] = k
        if not p.flash:
            rim_light(im, RIM, side=RIM_SIDE)   # 림라이트: keep 소지품(비검정)·내부 검정은 자동 제외
        if p.flash:
            for y in range(H):
                for x in range(W):
                    r, g, b, a = px[x, y]
                    if a and (r, g, b) != (0, 0, 0):
                        px[x, y] = (0xeb, 0xec, 0xed, 255)

    def render(self, dir_, p):
        s = Sprite(self.W, self.H, palette=self.PALETTE)
        self._keep = set()
        if p.heap:
            self.draw_heap(s, p, dir_)
        elif dir_ == "down":
            self.draw_down(s, p)
        elif dir_ == "up":
            self.draw_up(s, p)
        else:
            self.draw_side(s, p, +1 if dir_ == "right" else -1)
        self.finish(s, p)
        return s

    def poses(self, action, dir_):
        return getattr(self, "poses_" + action)(dir_)

    def poses_hurt(self, dir_):
        back = {"down": (0, -1), "up": (0, 1), "right": (-1, 0), "left": (1, 0)}[dir_]
        ps = [Pose(flash=True, body_dx=back[0], body_dy=back[1], head_dx=back[0], eye="x"),
              Pose(body_dx=back[0], body_dy=back[1], head_dx=-1 if dir_ in ("down", "up") else 0,
                   eye="x", l_hand=-1, r_hand=-1, lean=-1 if dir_ in ("left", "right") else 0)]
        return ps, self.TIMING["hurt"]

    # 정면 다리: cols=((x0,x1),(x0,x1)), 들림은 다리를 짧게 + 장화 위로
    def legs_front(self, s, p, cols, top, leg, hi, boot, boot_h, boot_hi=None):
        for (x0, x1), lift in zip(cols, (p.l_lift, p.r_lift)):
            boot_top = self.GROUND - (boot_h - 1) - lift
            for y in range(top, boot_top):
                for x in range(x0, x1 + 1):
                    self.px(s, x, y, hi if x == x0 else leg)
            for y in range(boot_top, boot_top + boot_h):
                for x in range(x0, x1 + 1):
                    self.px(s, x, y, boot_hi if (boot_hi and x == x0 and y > boot_top) else boot)

    # 옆 다리: m=+1 우향. back_x/front_x 는 우향 기준 다리 왼쪽 x. 좌향은 거울 배치(빛은 swap 으로)
    def legs_side(self, s, p, m, back_x, front_x, w, top, leg, hi, sep, boot, boot_h, boot_hi=None):
        legs = [(False, p.r_dx, p.r_sl), (True, p.l_dx, p.l_sl)]
        for front, dx, lift in legs:
            if m > 0:
                x0 = (front_x if front else back_x) + dx
            else:
                x0 = (self.W - 1 - (front_x if front else back_x) - (w - 1)) - dx
            boot_top = self.GROUND - (boot_h - 1) - lift
            for y in range(top, boot_top):
                for i in range(w):
                    x = x0 + i
                    if front and ((m > 0 and i == 0) or (m < 0 and i == w - 1)):
                        ch = sep
                    elif (m > 0 and i == 0) or (m < 0 and i == w - 1 and not front):
                        ch = hi
                    else:
                        ch = leg
                    self.px(s, x, y, ch)
            bx0 = x0 if m > 0 else x0 - 1
            for y in range(boot_top, boot_top + boot_h):
                for i in range(w + 1):
                    x = bx0 + i
                    back_col = (m > 0 and i == 0) or (m < 0 and i == w)
                    if front and back_col:
                        ch = "K"                       # 앞 장화와 뒤 장화 분리
                    elif boot_hi and y > boot_top and back_col:
                        ch = boot_hi
                    else:
                        ch = boot
                    self.px(s, x, y, ch)


# ============================================================ 1. 양조장주 stage1 (32x48)
class Brewer(Rig):
    ID = "stage1"
    W, H = 32, 48
    PIVOT = (16, 47)
    LEGEND = {
        ".": None,
        "K": G[0],   # 셀아웃·장화·눈꺼풀·입
        "1": G[1],   # 깊은 그림자·허리띠·장화 그늘
        "3": G[3],   # 바지·망치 자루 그늘
        "5": G[5],   # 바지 하이라이트·앞치마 그늘·콧수염·통나무 껍질 그늘
        "6": G[6],   # 앞치마 가죽·망치 자루
        "7": G[7],   # 피부 그늘·통나무 껍질·국자
        "8": G[8],   # 앞치마 하이라이트·통나무 절단면
        "9": G[9],   # 피부
        "a": G[10],  # 셔츠 그늘
        "c": G[12],  # 셔츠
        "w": G[14],  # 셔츠 하이라이트 (피격 플래시와 공유)
        "E": A[7],   # 23 눈빛
        "F": A[9],   # 25 예고 눈빛
        "B": A[5],   # 21 술 (병·얼룩)
        "S": A[3],   # 19 술 얼룩 그늘
    }
    LIGHT_SWAP = {"8": "5", "5": "8", "9": "7", "7": "9", "w": "a", "a": "w"}
    TIMING = {"idle": [240, 240, 240, 200, 240, 240], "walk": [130] * 8, "attack": [350, 150, 150, 220],
              "hurt": [70, 90], "death": [100, 120, 130, 140, 160, 240]}

    # 머리 12폭 x10..21, y4..15. 민머리·굵은 눈썹 능선·가는 눈(K 꺼풀 + E 호박)·콧수염(5)
    HEAD_DOWN = [
        "....9999....",
        "..99999997..",
        ".9999999977.",
        ".9999999977.",
        ".9999999977.",
        ".9779999777.",
        ".99KE99KE77.",
        ".9799999777.",
        ".9995555577.",
        ".9955555577.",
        "..95KKKK77..",
        "...999977...",
    ]
    HEAD_UP = [          # 뒤통수: 귀 2개, 목덜미 주름
        "....9999....",
        "..99999997..",
        ".9999999977.",
        ".9999999977.",
        ".9999999977.",
        "99999999977.",
        "79999999977.",
        "7999999997..",
        ".9999999977.",
        ".9999999977.",
        "..99999777..",
        "...777777...",
    ]
    HEAD_SIDE = [        # 우향 (앞 = 오른쪽): 코·눈 앞쪽, 귀 뒤쪽
        "....9999....",
        "..99999999..",
        ".9999999999.",
        ".9999999999.",
        ".9999999999.",
        ".9999997799.",
        ".9799999KE9.",
        ".7799999999.",
        ".9999995559.",
        ".9999955559.",
        "..9999KKK9..",
        "...999977...",
    ]
    # 몸통(정면): y16..35 행별 (x0, x1). 술통처럼 가운데가 부푼 실루엣.
    TORSO = {16: (7, 24), 17: (6, 25), 18: (5, 26), 19: (4, 27), 20: (4, 27), 21: (3, 28), 22: (3, 28), 23: (3, 28),
             24: (3, 28), 25: (3, 28), 26: (3, 28), 27: (3, 28), 28: (3, 28), 29: (3, 28), 30: (4, 27), 31: (4, 27),
             32: (5, 26), 33: (5, 26), 34: (6, 25), 35: (7, 24)}
    # 옆면(우향): 등은 x0, 배는 x1 로 앞(오른쪽)으로 부푼다
    TORSO_SIDE = {16: (9, 21), 17: (8, 22), 18: (8, 23), 19: (7, 24), 20: (7, 25), 21: (7, 26), 22: (7, 26), 23: (7, 26),
                  24: (7, 27), 25: (7, 27), 26: (7, 27), 27: (7, 27), 28: (7, 27), 29: (7, 26), 30: (8, 26), 31: (8, 25),
                  32: (8, 24), 33: (9, 24), 34: (9, 23), 35: (10, 22)}

    # ---------- 부품
    def torso_front(self, s, p, dx, dy, back=False):
        """셔츠 몸통 + 앞치마(정면) 또는 등 끈(후면) + 허리띠."""
        cr = p.crouch
        for y, (x0, x1) in self.TORSO.items():
            yy = y + dy
            if cr and y < 16 + cr:
                continue
            for x in range(x0, x1 + 1):
                self.px(s, x + dx, yy, "c")
            self.px(s, x0 + dx, yy, "w"); self.px(s, x1 + dx, yy, "a"); self.px(s, x1 - 1 + dx, yy, "a")
        # 어깨 윗선 하이라이트
        x0, x1 = self.TORSO[16 + cr]
        self.hline(s, x0 + 1 + dx, x1 - 2 + dx, 16 + dy + cr, "w")
        # 목 밑 그늘
        self.hline(s, 12 + dx, 19 + dx, 16 + dy + cr, "a")
        if not back:
            # 앞치마: 가슴받이 y19..23 (x12..19) + 몸판 y24..35 (x9..22)
            for y in range(19 + cr, 36):
                yy = y + dy
                xa, xb = (12, 19) if y < 24 else (9, 22)
                for x in range(xa, xb + 1):
                    self.px(s, x + dx, yy, "6")
                self.px(s, xa + dx, yy, "8"); self.px(s, xb + dx, yy, "5"); self.px(s, xb - 1 + dx, yy, "5")
            # 앞치마 어깨 끈 (목 양옆으로)
            self.kline(s, 12 + dx, 19 + dy + cr, 10 + dx, 16 + dy + cr, "6", keep=False)
            self.kline(s, 19 + dx, 19 + dy + cr, 21 + dx, 16 + dy + cr, "6", keep=False)
            # 술 얼룩 (가슴받이 아래 왼쪽)
            for x, y, ch in ((13, 25, "S"), (14, 25, "B"), (13, 26, "B"), (14, 26, "B"), (15, 26, "S"), (14, 27, "S"), (12, 27, "S")):
                self.px(s, x + dx, y + dy, ch)
            # 허리띠 y31 + 버클
            self.hline(s, 9 + dx, 22 + dx, 31 + dy, "1")
            self.px(s, 15 + dx, 31 + dy, "8"); self.px(s, 16 + dx, 31 + dy, "8")
            # 국자 (왼쪽 허리, 띠에 걸림): 손잡이 세로 + 국자 머리
            self.vline(s, 7 + dx, 30 + dy, 34 + dy, "7", keep=True); self.px(s, 7 + dx, 29 + dy, "8", keep=True)
            self.box(s, 6 + dx, 35 + dy, 8 + dx, 36 + dy, "7", keep=True); self.px(s, 6 + dx, 35 + dy, "8", keep=True)
            # 술병 (오른쪽 허리띠에 꽂힘)
            self.bottle(s, 21 + dx, 26 + dy)
        else:
            # 등 끈 X 자 + 허리띠
            self.kline(s, 10 + dx, 17 + dy + cr, 20 + dx, 30 + dy, "6", keep=False)
            self.kline(s, 21 + dx, 17 + dy + cr, 11 + dx, 30 + dy, "6", keep=False)
            self.hline(s, 8 + dx, 23 + dx, 31 + dy, "1")
            # 등 가운데 주름
            self.vline(s, 16 + dx, 17 + dy + cr, 29 + dy, "a")

    def torso_side(self, s, p, dx, dy, m):
        swap = m < 0
        cr = p.crouch
        prof = self.TORSO_SIDE if m > 0 else {y: (self.W - 1 - x1, self.W - 1 - x0) for y, (x0, x1) in self.TORSO_SIDE.items()}
        for y, (x0, x1) in prof.items():
            yy = y + dy
            if cr and y < 16 + cr:
                continue
            for x in range(x0, x1 + 1):
                self.px(s, x + dx, yy, "c")
            self.px(s, x0 + dx, yy, "w"); self.px(s, x1 + dx, yy, "a")
            # 앞치마: 앞쪽 절반 (y19 부터)
            if y >= 19:
                n = (x1 - x0 + 1)
                if m > 0:
                    ax0, ax1 = x1 - n // 2, x1 - 1
                else:
                    ax0, ax1 = x0 + 1, x0 + n // 2
                for x in range(ax0, ax1 + 1):
                    self.px(s, x + dx, yy, "6")
                self.px(s, (ax0 if m > 0 else ax1) + dx, yy, "8" if m > 0 else "5")
                self.px(s, (ax1 if m > 0 else ax0) + dx, yy, "5" if m > 0 else "8")
        x0, x1 = prof[16 + cr]
        self.hline(s, x0 + 1 + dx, x1 - 1 + dx, 16 + dy + cr, "w")
        # 허리띠
        x0, x1 = prof[31]
        self.hline(s, x0 + dx, x1 + dx, 31 + dy, "1")
        # 술병: 우향이면 등 쪽(뒤) 허리에, 좌향이면 앞 허리에 보임
        if m > 0:
            self.bottle(s, 25 + dx, 26 + dy)
        else:
            self.bottle(s, 4 + dx, 26 + dy)

    def bottle(self, s, x, y):
        """술병 3폭: 목(7) + 몸통 3x5 (B/S), 술이 반쯤."""
        k = dict(keep=True)
        self.px(s, x + 1, y, "7", **k)
        self.px(s, x + 1, y + 1, "7", **k)
        for yy in range(y + 2, y + 7):
            for xx in range(x, x + 3):
                self.px(s, xx, yy, "B" if yy >= y + 4 else "7", **k)
        self.px(s, x, y + 4, "S", **k); self.px(s, x + 2, y + 5, "S", **k); self.px(s, x + 2, y + 6, "S", **k)
        self.px(s, x, y + 2, "8", **k)

    def log(self, s, x, y, axis="h", w=7, h=5, swap=False):
        """통나무 망치 머리. axis h: 가로로 누움 (w x h), v: 세로."""
        k = dict(keep=True)
        if axis == "h":
            self.box(s, x, y, x + w - 1, y + h - 1, "7", **k)
            self.hline(s, x, x + w - 1, y, "8", **k)                       # 윗면 빛
            self.hline(s, x, x + w - 1, y + h - 1, "5", **k)               # 밑 그늘
            self.vline(s, x + 1, y + 1, y + h - 2, "5", **k)                # 껍질 결
            self.vline(s, x + w - 2, y + 1, y + h - 2, "5", **k)
            # 절단면 (양 끝): 빛 쪽 밝게, 반대쪽 어둡게
            self.vline(s, x if not swap else x + w - 1, y, y + h - 1, "8", **k)
            self.vline(s, x + w - 1 if not swap else x, y, y + h - 1, "3", **k)
        else:
            self.box(s, x, y, x + w - 1, y + h - 1, "7", **k)
            self.vline(s, x, y, y + h - 1, "8" if not swap else "5", **k)
            self.vline(s, x + w - 1, y, y + h - 1, "5" if not swap else "8", **k)
            self.hline(s, x, x + w - 1, y, "8", **k)
            self.hline(s, x, x + w - 1, y + h - 1, "3", **k)
            self.hline(s, x + 1, x + w - 2, y + 2, "5", **k)

    def handle(self, s, x0, y0, x1, y1, swap=False):
        """망치 자루 2px: 나무(6) + 그늘(3)."""
        self.thick_line(s, x0, y0, x1, y1, 2, "6" if not swap else "3", "3" if not swap else "6", keep=True)

    def mallet_ground(self, s, hx, hy, side, swap=False):
        """지팡이처럼 땅에 짚은 통나무: 손(hx,hy) 아래로 자루, 바닥에 통나무 머리. side=+1 머리가 오른쪽."""
        gx = hx if side > 0 else hx - 1
        self.handle(s, gx, hy + 1, gx, 41)
        lx = hx - 3 if side > 0 else hx - 4
        self.log(s, lx, 42, "h", 7, 5)

    def arm_front(self, s, p, side, dx, dy, sx, sy, hx, hy):
        """팔: 소매 3px 어깨→팔꿈치, 맨 팔뚝 3px→손, 주먹 3x3. side<0 = 화면 왼쪽 팔(바깥이 빛), side>0 = 오른쪽 팔.
        몸통과 같은 재질이므로 몸통 쪽 열은 한 단계 어두운 G10(a) 로 분리한다."""
        ex, ey = sx + (hx - sx) // 2, sy + (hy - sy) // 2
        cols = ("w", "c", "a") if side < 0 else ("a", "c", "a")
        skin = ("9", "9", "7") if side < 0 else ("7", "9", "7")
        for i in range(3):
            self.kline(s, sx + i, sy, ex + i, ey, cols[i], keep=False)
        for i in range(3):
            self.kline(s, ex + i, ey, hx + i, hy, skin[i], keep=False)
        self.box(s, hx, hy, hx + 2, hy + 2, "9")
        self.px(s, hx + 2, hy + 2, "7"); self.px(s, hx + 2, hy + 1, "7"); self.px(s, hx, hy, "7" if side > 0 else "9")

    def head(self, s, p, hx, hy, kind, mirror=False, swap=False):
        rows = {"down": self.HEAD_DOWN, "up": self.HEAD_UP, "side": self.HEAD_SIDE}[kind]
        if p.eye and kind != "up":
            rows = [r.replace("E", p.eye) for r in rows]
        self.blit(s, rows, hx, hy, mirror=mirror)

    # ---------- 뷰
    def draw_down(self, s, p, back=False):
        dx, dy = p.body_dx, p.body_dy
        cr = p.crouch
        it = p.item
        self.legs_front(s, p, ((9, 13), (18, 22)), 36 + dy, "3", "5", "1", 4, boot_hi="3")
        self.torso_front(s, p, dx, dy, back=back)
        # 망치: 정면은 화면 오른쪽 손(= 그의 왼손), 후면은 화면 왼쪽 손
        mode = it.get("mallet", "ground")
        hand_x = 26 if not back else 3
        if mode == "ground":
            self.mallet_ground(s, (hand_x + 1 if not back else hand_x) + dx, 33 + dy + p.r_hand, +1 if not back else -1)
        elif mode == "over":          # 머리 위로 들어 올림 (가로)
            self.log(s, 9 + dx, 1 + dy + cr, "h", 14, 5)
            self.handle(s, 23 + dx, 3 + dy + cr, 30 + dx, 9 + dy + cr)
        elif mode == "ram":           # 배 앞에 가로로 안음 → 정면: 통나무가 몸을 가림 / 후면: 양 끝만 삐죽
            if not back:
                self.log(s, 5 + dx, it.get("ram_y", 30) + dy, "h", 22, 6)
            else:
                self.log(s, 1 + dx, it.get("ram_y", 30) + dy, "h", 4, 6)
                self.log(s, 27 + dx, it.get("ram_y", 30) + dy, "h", 4, 6)
        elif mode == "swing":         # 옆으로 휘두름 (화면 오른쪽 수평)
            self.handle(s, 22 + dx, 26 + dy, 27 + dx, 26 + dy)
            self.log(s, 25 + dx, 23 + dy, "v", 6, 9)
        # 팔
        if mode == "ground":
            if not back:
                # 화면 왼쪽 팔: 늘어뜨림 / 화면 오른쪽 팔: 자루 잡음
                self.arm_front(s, p, -1, dx, dy, 5 + dx, 18 + dy + cr, 2 + dx, 30 + dy + p.l_hand)
                self.arm_front(s, p, +1, dx, dy, 24 + dx, 18 + dy + cr, hand_x + dx, 32 + dy + p.r_hand)
            else:
                self.arm_front(s, p, -1, dx, dy, 5 + dx, 18 + dy + cr, hand_x - 1 + dx, 32 + dy + p.r_hand)
                self.arm_front(s, p, +1, dx, dy, 24 + dx, 18 + dy + cr, 27 + dx, 30 + dy + p.l_hand)
        elif mode == "over":
            self.arm_front(s, p, -1, dx, dy, 5 + dx, 18 + dy + cr, 9 + dx, 5 + dy + cr)
            self.arm_front(s, p, +1, dx, dy, 24 + dx, 18 + dy + cr, 24 + dx, 7 + dy + cr)
        elif mode == "ram":
            ry = it.get("ram_y", 30) + dy
            self.arm_front(s, p, -1, dx, dy, 5 + dx, 18 + dy + cr, 6 + dx, ry - 2)
            self.arm_front(s, p, +1, dx, dy, 24 + dx, 18 + dy + cr, 23 + dx, ry - 2)
        elif mode == "swing":
            self.arm_front(s, p, -1, dx, dy, 5 + dx, 18 + dy + cr, 1 + dx, 24 + dy)
            self.arm_front(s, p, +1, dx, dy, 24 + dx, 18 + dy + cr, 20 + dx, 25 + dy)
        # 머리
        self.head(s, p, 10 + dx + p.head_dx, 4 + dy + cr + p.head_dy, "up" if back else "down")

    def draw_up(self, s, p):
        self.draw_down(s, p, back=True)

    def draw_side(self, s, p, m):
        swap = m < 0
        dx, dy = p.body_dx * m, p.body_dy
        cr = p.crouch
        it = p.item
        mode = it.get("mallet", "ground")
        X = (lambda x: x + dx) if m > 0 else (lambda x: self.W - 1 - x + dx)   # 우향 좌표 → 실제
        # 먼 쪽 팔·망치 (몸 뒤) 먼저: 우향 = 왼손(망치)이 먼 쪽
        if mode == "ground" and m > 0:
            # 뒤쪽 바닥에 통나무, 자루는 몸 뒤로 올라가 어깨 뒤에서 끝남
            self.handle(s, X(6), 20 + dy + cr, X(6), 41 + dy)
            self.log(s, X(5) - 3, 42, "h", 7, 5)
        self.legs_side(s, p, m, 10, 16, 5, 36 + dy, "3", "5", "1", "1", 4, boot_hi="3")
        self.torso_side(s, p, dx, dy, m)
        # 가까운 팔
        sx, sy = (X(20) if m > 0 else X(20) - 2), 18 + dy + cr
        side = +1 if m > 0 else -1
        if mode == "ground":
            if m < 0:
                # 좌향: 가까운 왼손이 자루를 잡고 앞(왼쪽) 바닥에 통나무
                hx = X(24)
                self.arm_front(s, p, side, dx, dy, sx, sy, hx - 1, 32 + dy + p.r_hand)
                self.handle(s, hx - 1, 35 + dy + p.r_hand, hx - 1, 41)
                self.log(s, hx - 5, 42, "h", 7, 5)
            else:
                # 우향: 가까운 오른손은 배 앞에 늘어뜨림
                self.arm_front(s, p, side, dx, dy, sx, sy, X(23), 31 + dy + p.l_hand)
        elif mode == "over":
            # 통나무를 머리 위로 (세로로 세움, 몸 뒤쪽 위)
            self.handle(s, X(14), 16 + dy + cr, X(10), 6 + dy + cr)
            self.log(s, X(12) - 3, 0 + dy + cr, "h", 7, 5)
            self.arm_front(s, p, side, dx, dy, sx, sy, X(13), 10 + dy + cr)
        elif mode == "ram":
            # 앞으로 가로로 내민 통나무: 자루는 손에서 앞으로, 머리는 맨 앞
            ry = it.get("ram_y", 30) + dy
            hx = X(23)
            self.handle(s, X(14), ry + 2, X(23), ry + 2)
            self.log(s, X(24) if m > 0 else X(24) - 7, ry, "h", 8, 6)
            self.arm_front(s, p, side, dx, dy, sx, sy, X(21) if m > 0 else X(21) - 2, ry - 1)
        elif mode == "swing":
            # 앞 위로 휘두름 (사선)
            self.handle(s, X(20), 26 + dy, X(26), 20 + dy)
            self.log(s, X(26) if m > 0 else X(26) - 6, 12 + dy, "v", 6, 9)
            self.arm_front(s, p, side, dx, dy, sx, sy, X(19) if m > 0 else X(19) - 2, 24 + dy)
        # 머리 (우향 x10..21)
        hx = 10 + dx + p.lean * m
        self.head(s, p, hx, 4 + dy + cr + p.head_dy, "side", mirror=swap, swap=swap)

    def draw_heap(self, s, p, dir_):
        st = p.heap
        oy = 0 if st == 1 else 1
        # 술통처럼 옆으로 누운 몸: 큰 타원 (셔츠) + 앞치마 띠
        s.ellipse(3, 33 + oy, 28, 46 + oy, self.LEGEND["c"])
        s.ellipse(4, 33 + oy, 20, 40 + oy, self.LEGEND["w"], only=self.LEGEND["c"])
        s.ellipse(10, 40 + oy, 28, 46 + oy, self.LEGEND["a"], only=self.LEGEND["c"])
        for x in range(10, 22):
            for y in range(34 + oy, 46 + oy):
                if s.get(x, y) is not None:
                    self.px(s, x, y, "6" if x not in (10, 21) else "5")
        self.hline(s, 10, 21, 42 + oy, "1")
        # 머리: 방향별 위치
        head = {"down": (0, 36), "up": (21, 34), "right": (22, 36), "left": (0, 36)}[dir_]
        hx, hy = head
        s.ellipse(hx, hy + oy, hx + 9, hy + 9 + oy, self.LEGEND["9"])
        s.ellipse(hx + 5, hy + 4 + oy, hx + 9, hy + 9 + oy, self.LEGEND["7"], only=self.LEGEND["9"])
        self.hline(s, hx + 3, hx + 6, hy + 6 + oy, "5")
        if st == 1 and dir_ != "up":
            self.px(s, hx + 3, hy + 4 + oy, "K"); self.px(s, hx + 4, hy + 4 + oy, "E")
        else:
            self.px(s, hx + 3, hy + 4 + oy, "K"); self.px(s, hx + 4, hy + 4 + oy, "K")
        # 장화 (머리 반대쪽 끝)
        if hx < 10:
            self.box(s, 26, 36 + oy, 31, 39 + oy, "K"); self.box(s, 27, 41 + oy, 31, 44 + oy, "K")
            self.px(s, 26, 37 + oy, "1"); self.px(s, 27, 42 + oy, "1")
        else:
            self.box(s, 0, 36 + oy, 5, 39 + oy, "K"); self.box(s, 0, 41 + oy, 4, 44 + oy, "K")
            self.px(s, 1, 37 + oy, "1"); self.px(s, 1, 42 + oy, "1")
        # 떨어진 망치
        if dir_ in ("down", "right", "up"):
            self.handle(s, 3, 30 + oy, 14, 30 + oy); self.log(s, 0, 28 + oy, "h", 4, 5)
        else:
            self.handle(s, 17, 30 + oy, 28, 30 + oy); self.log(s, 28, 28 + oy, "h", 4, 5)
        # 깨진 병 + 쏟아진 술 (마지막 프레임에 넓어짐)
        px0 = 22 if dir_ != "right" else 2
        if st == 1:
            self.hline(s, px0, px0 + 3, 47, "B", keep=True); self.px(s, px0 + 1, 46, "S", keep=True)
        else:
            self.hline(s, px0 - 2, px0 + 6, 47, "B", keep=True); self.hline(s, px0, px0 + 4, 46, "B", keep=True)
            self.px(s, px0 + 1, 45, "S", keep=True); self.px(s, px0 + 2, 45, "S", keep=True)
            self.px(s, px0 - 2, 47, "S", keep=True); self.px(s, px0 + 6, 47, "S", keep=True)

    # ---------- 동작
    def poses_idle(self, dir_):
        bob = [0, 0, 1, 1, 0, 0]
        ps = []
        for i in range(6):
            ps.append(Pose(body_dy=bob[i], head_dy=[0, 0, 0, 1, 1, 0][i] - bob[i],
                           head_dx=[0, 0, 0, -1, -1, 0][i] if dir_ in ("down", "up") else 0,
                           lean=[0, 0, 0, 1, 1, 0][i] if dir_ in ("left", "right") else 0,
                           r_hand=[0, 0, 1, 1, 0, 0][i], l_hand=[0, 0, 1, 1, 1, 0][i]))
        return ps, self.TIMING["idle"]

    def poses_walk(self, dir_):
        side = dir_ in ("left", "right")
        ps = []
        if not side:
            L = [0, 2, 3, 2, 0, 0, 0, 0]; R = [0, 0, 0, 0, 0, 2, 3, 2]
            bob = [0, -1, -2, -1, 0, -1, -2, -1]; sway = [1, 1, 0, 0, -1, -1, 0, 0]
            for i in range(8):
                ps.append(Pose(l_lift=L[i], r_lift=R[i], body_dy=bob[i], body_dx=sway[i], head_dx=sway[i],
                               l_hand=[1, 1, 0, -1, -1, -1, 0, 1][i], r_hand=[-1, -1, 0, 1, 1, 1, 0, -1][i]))
        else:
            F = [3, 2, 0, -2, -3, -2, 0, 2]
            bob = [0, -1, -2, -1, 0, -1, -2, -1]
            LS = [0, 0, 0, 0, 0, 2, 2, 0]; RS = [0, 2, 2, 0, 0, 0, 0, 0]
            for i in range(8):
                ps.append(Pose(l_dx=F[i], r_dx=-F[i], l_sl=LS[i], r_sl=RS[i], body_dy=bob[i], lean=1 if i in (2, 3, 6, 7) else 0,
                               l_hand=-F[i] // 2, r_hand=-F[i] // 2))
        return ps, self.TIMING["walk"]

    def poses_attack(self, dir_):
        # 1 예고: 통나무를 머리 위로 들고 뒤로 젖힘, 눈 25 (telegraphMs 동안 유지)
        # 2·3 돌진: 통나무를 배 앞에 가로로 안고 앞으로 (durationMs 동안 2·3 반복)
        # 4 휘두름/복귀: 옆으로 휘두름 (부채꼴 탄 발사 자세 겸용)
        side = dir_ in ("left", "right")
        fwd = {"down": (0, 2), "up": (0, -2), "right": (2, 0), "left": (2, 0)}[dir_]
        ps = [Pose(item={"mallet": "over"}, eye="F", body_dy=-fwd[1] // 2 - 1, body_dx=-1 if side else 0, head_dy=-1, lean=-1,
                   l_lift=0, r_lift=0),
              Pose(item={"mallet": "ram", "ram_y": 29}, eye="F", body_dx=fwd[0], body_dy=fwd[1], lean=1, crouch=1,
                   l_lift=0 if not side else 0, r_lift=2 if not side else 0, l_dx=3 if side else 0, r_dx=-3 if side else 0, r_sl=2 if side else 0),
              Pose(item={"mallet": "ram", "ram_y": 30}, eye="F", body_dx=fwd[0], body_dy=fwd[1], lean=1, crouch=1,
                   l_lift=2 if not side else 0, r_lift=0, l_dx=-3 if side else 0, r_dx=3 if side else 0, l_sl=2 if side else 0),
              Pose(item={"mallet": "swing"}, body_dx=fwd[0] // 2, body_dy=fwd[1] // 2, lean=1)]
        return ps, self.TIMING["attack"]

    def poses_death(self, dir_):
        side = dir_ in ("left", "right")
        ps = [Pose(head_dx=1, eye="x", l_hand=-1, r_hand=-1, head_dy=-1),
              Pose(body_dx=-1, head_dx=-1, eye="x", body_dy=1, lean=1, item={"mallet": "none"}, l_hand=1, r_hand=1),
              Pose(crouch=4, body_dy=4, head_dy=2, eye="x", l_hand=3, r_hand=3, lean=1, item={"mallet": "none"}),
              Pose(crouch=7, body_dy=7, head_dy=2, head_dx=-1, eye="x", l_hand=5, r_hand=5, lean=2, item={"mallet": "none"}),
              Pose(heap=1), Pose(heap=2)]
        if side:
            for p in ps[:4]:
                p.l_dx = 2; p.r_dx = -2
        return ps, self.TIMING["death"]


# ============================================================ 2. 황제 emperor (48x64)
class Emperor(Rig):
    ID = "emperor"
    W, H = 48, 64
    PIVOT = (24, 63)
    LEGEND = {
        ".": None,
        "K": G[0],   # 셀아웃·눈꺼풀
        "1": G[1],   # 장갑·장화
        "3": G[3],   # 장화 하이라이트
        "6": G[6],   # 가슴 띠·훈장 리본
        "7": G[7],   # 피부 그늘
        "9": G[9],   # 피부
        "a": G[10],  # 외투 그늘·서류 글줄
        "b": G[11],  # 머리카락 그늘
        "c": G[12],  # 외투 본색
        "d": G[13],  # 머리카락(은발)·지휘봉 끝
        "w": G[14],  # 외투 하이라이트·깃·서류
        "E": A[7],   # 23 눈빛
        "M": A[5],   # 21 훈장
    }
    LIGHT_SWAP = {"w": "a", "a": "w", "9": "7", "7": "9", "d": "b", "b": "d"}
    TIMING = {"idle": [260, 260, 260, 220, 260, 260], "walk": [120] * 8, "attack": [300, 150, 150, 240],
              "hurt": [70, 90], "death": [100, 120, 130, 140, 160, 260]}

    # 머리 12폭 x18..29, y6..21: 뒤로 넘긴 은발, 긴 얼굴, 차분한 눈
    HEAD_DOWN = [
        "...dddddd...",
        "..dddddddb..",
        ".ddddddddbb.",
        ".dd999999bb.",
        ".d99999999b.",
        ".999999999b.",
        ".999999997b.",
        ".99KE99KE77.",
        ".999999977..",
        ".9999979977.",
        ".999999977..",
        ".999999977..",
        ".99977777...",
        "..9999777...",
        "...99777....",
        "....777.....",
    ]
    HEAD_UP = [
        "...dddddd...",
        "..dddddddb..",
        ".ddddddddbb.",
        ".ddddddddbb.",
        ".ddddddddbb.",
        ".ddddddddbb.",
        ".9ddddddddb.",
        ".9ddddddd9b.",
        ".99ddddd99..",
        ".999999997..",
        ".999999977..",
        ".999999977..",
        ".99977777...",
        "..9999777...",
        "...99777....",
        "....777.....",
    ]
    HEAD_SIDE = [         # 우향: 앞 = 오른쪽. 코·눈 앞쪽, 은발이 뒤로 흐름
        "...dddddd...",
        "..dddddddd..",
        ".dddddddddd.",
        ".ddd9999999.",
        ".dd99999999.",
        ".dd99999999.",
        ".bd999999999",
        ".bd99999KE99",
        ".bd999999999",
        ".b7999999997",
        "..7999999997",
        "..79999999..",
        "...9999997..",
        "...999977...",
        "....9977....",
        "....777.....",
    ]
    # 외투 정면 y22..53 행별 (x0,x1). 어깨 18폭 → 허리 → 밑단 24폭.
    COAT = {}
    for y in range(22, 54):
        if y <= 24:
            COAT[y] = (15, 32)
        elif y <= 34:
            COAT[y] = (15, 32)
        elif y <= 40:
            COAT[y] = (16, 31)
        else:
            f = (y - 40) // 3
            COAT[y] = (15 - f, 32 + f)
    COAT_SIDE = {}
    for y in range(22, 54):
        if y <= 34:
            COAT_SIDE[y] = (17, 30)
        elif y <= 40:
            COAT_SIDE[y] = (18, 30)
        else:
            f = (y - 40) // 3
            COAT_SIDE[y] = (17 - f, 30 + f // 2)

    # ---------- 부품
    def coat_front(self, s, p, dx, dy, back=False):
        cr = p.crouch
        flare = p.item.get("flare", 0)
        for y, (x0, x1) in self.COAT.items():
            yy = y + dy
            if cr and y < 22 + cr:
                continue
            if y >= 44 and flare:
                x0 -= flare; x1 += flare
            for x in range(x0, x1 + 1):
                self.px(s, x + dx, yy, "c")
            self.px(s, x0 + dx, yy, "w"); self.px(s, x1 + dx, yy, "a"); self.px(s, x1 - 1 + dx, yy, "a")
        # 어깨선
        x0, x1 = self.COAT[22 + cr]
        self.hline(s, x0 + dx, x1 - 2 + dx, 22 + dy + cr, "w")
        if not back:
            # 앞섶 (가운데 그늘선) + 라펠
            self.vline(s, 24 + dx, 26 + dy + cr, 53 + dy, "a")
            self.kline(s, 21 + dx, 22 + dy + cr, 24 + dx, 26 + dy + cr, "w", keep=False)
            self.kline(s, 27 + dx, 22 + dy + cr, 24 + dx, 26 + dy + cr, "w", keep=False)
            # 가슴 띠 (화면 왼쪽 어깨 → 오른쪽 허리) 3px
            self.thick_line(s, 16 + dx, 24 + dy + cr, 29 + dx, 40 + dy, 3, "6", "6")
            # 훈장: 리본 6 + 메달 M (마름모)
            mx, my = 20 + dx, 28 + dy + cr
            self.px(s, mx, my - 1, "6"); self.px(s, mx + 1, my - 1, "6")
            for x, y in ((mx, my), (mx - 1, my + 1), (mx, my + 1), (mx + 1, my + 1), (mx, my + 2)):
                self.px(s, x, y, "M")
            # 허리 단추 2개
            self.px(s, 24 + dx, 36 + dy, "1"); self.px(s, 24 + dx, 40 + dy, "1")
        else:
            # 등솔기 + 띠 뒤쪽
            self.vline(s, 24 + dx, 24 + dy + cr, 53 + dy, "a")
            self.thick_line(s, 31 + dx, 24 + dy + cr, 18 + dx, 40 + dy, 3, "6", "6")
            # 뒤트임 (밑단)
            self.vline(s, 23 + dx, 46 + dy, 53 + dy, "a")
        # 깃 (높은 깃, 목 양옆에서 턱선까지)
        cy = 20 + dy + cr
        for i in range(3):
            self.px(s, 16 + i + dx, cy - i, "w"); self.px(s, 31 - i + dx, cy - i, "w")
            self.px(s, 16 + i + dx, cy + 1 - i, "w"); self.px(s, 31 - i + dx, cy + 1 - i, "w")
        self.hline(s, 16 + dx, 31 + dx, 22 + dy + cr, "w")

    def coat_side(self, s, p, dx, dy, m):
        swap = m < 0
        cr = p.crouch
        flare = p.item.get("flare", 0)
        prof = self.COAT_SIDE if m > 0 else {y: (self.W - 1 - x1, self.W - 1 - x0) for y, (x0, x1) in self.COAT_SIDE.items()}
        for y, (x0, x1) in prof.items():
            yy = y + dy
            if cr and y < 22 + cr:
                continue
            if y >= 44 and flare:          # 돌진: 뒤 자락이 날림
                if m > 0:
                    x0 -= flare
                else:
                    x1 += flare
            for x in range(x0, x1 + 1):
                self.px(s, x + dx, yy, "c")
            self.px(s, x0 + dx, yy, "w"); self.px(s, x1 + dx, yy, "a")
        x0, x1 = prof[22 + cr]
        self.hline(s, x0 + dx, x1 - 1 + dx, 22 + dy + cr, "w")
        # 띠: 옆에서 어깨→허리 사선 (앞쪽)
        if m > 0:
            self.thick_line(s, 23 + dx, 24 + dy + cr, 29 + dx, 40 + dy, 2, "6", "6")
        else:
            self.thick_line(s, 23 + dx, 24 + dy + cr, 17 + dx, 40 + dy, 2, "6", "6")
        # 깃
        cy = 20 + dy + cr
        X = (lambda x: x + dx) if m > 0 else (lambda x: self.W - 1 - x + dx)
        for i in range(3):
            self.px(s, X(18 + i), cy - i, "w"); self.px(s, X(18 + i), cy + 1 - i, "w")
            self.px(s, X(29 - i), cy - i, "w"); self.px(s, X(29 - i), cy + 1 - i, "w")
        self.hline(s, X(18), X(29), 22 + dy + cr, "w")
        # 훈장: 우향(앞이 오른쪽)에서는 가슴 앞쪽에 보임
        if m > 0:
            mx, my = 27 + dx, 29 + dy + cr
            self.px(s, mx, my - 1, "6")
            for x, y in ((mx, my), (mx - 1, my + 1), (mx, my + 1), (mx + 1, my + 1), (mx, my + 2)):
                self.px(s, x, y, "M")

    def papers(self, s, x, y, swap=False):
        """서류 뭉치 6x8: 종이(w) + 글줄(a), 모서리 그늘."""
        k = dict(keep=True)
        self.box(s, x, y, x + 5, y + 7, "w", **k)
        for yy in (y + 2, y + 4, y + 6):
            self.hline(s, x + 1, x + 4, yy, "a", **k)
        self.vline(s, x + 5, y, y + 7, "d", **k)
        self.hline(s, x, x + 5, y + 7, "d", **k)

    def baton(self, s, x0, y0, x1, y1):
        """지휘봉: 자루 1, 양 끝 d."""
        self.kline(s, x0, y0, x1, y1, "1")
        self.px(s, x0, y0, "d", keep=True); self.px(s, x1, y1, "d", keep=True)
        if abs(x1 - x0) > abs(y1 - y0):
            self.px(s, x1 - (1 if x1 > x0 else -1), y1, "d", keep=True)
        else:
            self.px(s, x1, y1 - (1 if y1 > y0 else -1), "d", keep=True)

    def arm(self, s, sx, sy, hx, hy, glove=True, side=-1):
        """소매 3px 어깨→손, 장갑 2x2 (1). side<0 = 화면 왼쪽 팔(바깥 w, 안쪽 a), side>0 = 오른쪽 팔(안쪽 a, 바깥 a).
        수평에 가까우면 위 w / 아래 a."""
        horiz = abs(hx - sx) > abs(hy - sy)
        cols = ("w", "c", "a") if (side < 0 or horiz) else ("a", "c", "a")
        for i in range(3):
            if horiz:
                self.kline(s, sx, sy + i, hx, hy + i, cols[i], keep=False)
            else:
                self.kline(s, sx + i, sy, hx + i, hy, cols[i], keep=False)
        self.hline(s, sx, sx + 2, sy, "a")      # 어깨 솔기
        if glove:
            self.box(s, hx, hy + 1, hx + 1, hy + 2, "1")

    def head(self, s, p, hx, hy, kind, mirror=False, swap=False):
        rows = {"down": self.HEAD_DOWN, "up": self.HEAD_UP, "side": self.HEAD_SIDE}[kind]
        if p.eye and kind != "up":
            rows = [r.replace("E", p.eye) for r in rows]
        self.blit(s, rows, hx, hy, mirror=mirror)

    # ---------- 뷰
    def draw_down(self, s, p, back=False):
        dx, dy = p.body_dx, p.body_dy
        cr = p.crouch
        it = p.item
        mode = it.get("baton", "down")
        # 장화 (외투 밑단 아래)
        self.legs_front(s, p, ((19, 22), (25, 28)), 50 + dy, "1", "3", "1", 3, boot_hi="3")
        self.coat_front(s, p, dx, dy, back=back)
        # 팔. 정면: 화면 왼쪽 = 서류 손, 화면 오른쪽 = 지휘봉 손. 후면은 반대.
        pap_x, bat_x = (13, 33) if not back else (31, 11)
        sy = 24 + dy + cr
        if mode == "down":
            # 서류 팔: 팔꿈치 굽혀 허리 앞에
            self.arm(s, pap_x + 1 + dx, sy, pap_x + 2 + dx, 38 + dy + p.l_hand, side=-1 if not back else +1)
            if not back:
                self.papers(s, pap_x - 1 + dx, 33 + dy + p.l_hand)
            # 지휘봉 팔: 곧게 내림
            self.arm(s, bat_x - 1 + dx, sy, bat_x - 1 + dx, 42 + dy + p.r_hand, side=+1 if not back else -1)
            self.baton(s, bat_x + dx, 40 + dy + p.r_hand, bat_x + dx, 54 + dy + p.r_hand)
        elif mode == "raise":        # 예고: 지휘봉을 가슴 앞 가로로, 서류 손은 등 뒤로
            self.arm(s, pap_x + 1 + dx, sy, pap_x + 2 + dx, 34 + dy)
            self.arm(s, bat_x - 1 + dx, sy, bat_x - 6 + dx, 30 + dy)
            if not back:
                self.baton(s, bat_x - 14 + dx, 32 + dy, bat_x - 1 + dx, 32 + dy)
            else:
                self.baton(s, bat_x + 1 + dx, 32 + dy, bat_x + 4 + dx, 32 + dy)
        elif mode == "point":        # 돌진: 지휘봉이 정면(아래)으로 향함 = 짧게 보이고 끝이 큼
            self.arm(s, pap_x + 1 + dx, sy, pap_x - 1 + dx, 30 + dy)
            self.arm(s, bat_x - 1 + dx, sy, bat_x - 2 + dx, 36 + dy)
            if not back:
                self.baton(s, bat_x - 1 + dx, 38 + dy, bat_x - 1 + dx, 46 + dy)
                self.px(s, bat_x - 2 + dx, 46 + dy, "d", keep=True); self.px(s, bat_x + dx, 46 + dy, "d", keep=True)
            else:
                self.baton(s, bat_x - 1 + dx, 34 + dy, bat_x - 1 + dx, 24 + dy + cr)
        elif mode == "sweep":        # 휘두름: 지휘봉을 옆으로 뻗음
            self.arm(s, pap_x + 1 + dx, sy, pap_x + 2 + dx, 36 + dy)
            self.arm(s, bat_x - 1 + dx, sy, bat_x + 4 + dx, 28 + dy)
            if not back:
                self.baton(s, bat_x + 5 + dx, 29 + dy, bat_x + 14 + dx, 24 + dy)
            else:
                self.baton(s, bat_x - 5 + dx, 29 + dy, bat_x - 14 + dx, 24 + dy)
        elif mode == "none":
            self.arm(s, pap_x + 1 + dx, sy, pap_x + dx, 42 + dy + p.l_hand)
            self.arm(s, bat_x - 1 + dx, sy, bat_x - 1 + dx, 42 + dy + p.r_hand)
        self.head(s, p, 18 + dx + p.head_dx, 6 + dy + cr + p.head_dy, "up" if back else "down")

    def draw_up(self, s, p):
        self.draw_down(s, p, back=True)

    def draw_side(self, s, p, m):
        swap = m < 0
        dx, dy = p.body_dx * m, p.body_dy
        cr = p.crouch
        it = p.item
        mode = it.get("baton", "down")
        X = (lambda x: x + dx) if m > 0 else (lambda x: self.W - 1 - x + dx)
        # 먼 쪽 소지품 (몸 뒤): 우향 = 지휘봉(왼손) 끝이 밑단 아래로 / 좌향 = 서류 모서리가 가슴 앞으로
        if mode == "down":
            if m > 0:
                self.baton(s, X(21), 46 + dy, X(21), 54 + dy + p.r_hand)
        self.legs_side(s, p, m, 20, 25, 4, 50 + dy, "1", "3", "1", "1", 3, boot_hi="3")
        self.coat_side(s, p, dx, dy, m)
        sx, sy = (X(26) if m > 0 else X(26) - 2), 24 + dy + cr
        aside = +1 if m > 0 else -1
        if mode == "down":
            if m > 0:
                # 우향: 가까운 오른팔이 서류를 가슴 앞에 든다
                self.arm(s, sx, sy, X(27), 36 + dy + p.l_hand, side=aside)
                self.papers(s, X(27), 31 + dy + p.l_hand)
            else:
                # 좌향: 가까운 왼팔이 지휘봉을 내려 든다. 서류 모서리는 가슴 앞에 삐죽
                self.arm(s, sx, sy, X(25) - 2, 42 + dy + p.r_hand, side=aside)
                self.baton(s, X(25) - 1, 40 + dy + p.r_hand, X(25) - 1, 54 + dy + p.r_hand)
                self.box(s, X(28) - 2, 32 + dy, X(28), 38 + dy, "w", keep=True)
                self.hline(s, X(28) - 2, X(28) - 1, 34 + dy, "a", keep=True); self.hline(s, X(28) - 2, X(28) - 1, 36 + dy, "a", keep=True)
        elif mode == "raise":
            # 지휘봉을 앞으로 비스듬히 들어 올림 (가까운 팔로 통일)
            self.arm(s, sx, sy, X(27) - (2 if m < 0 else 0), 30 + dy, side=aside)
            self.baton(s, X(28), 31 + dy, X(37), 26 + dy)
        elif mode == "point":
            self.arm(s, sx, sy, X(30) - (2 if m < 0 else 0), 30 + dy, side=aside)
            self.baton(s, X(31), 32 + dy, X(44), 32 + dy)
        elif mode == "sweep":
            self.arm(s, sx, sy, X(29) - (2 if m < 0 else 0), 24 + dy, side=aside)
            self.baton(s, X(30), 25 + dy, X(40), 16 + dy)
        elif mode == "none":
            self.arm(s, sx, sy, X(24) - (2 if m < 0 else 0), 42 + dy + p.r_hand, side=aside)
        hx = 18 + dx + p.lean * m
        self.head(s, p, hx, 6 + dy + cr + p.head_dy, "side", mirror=swap, swap=swap)

    def draw_heap(self, s, p, dir_):
        st = p.heap
        oy = 0 if st == 1 else 1
        # 길게 누운 외투 (가로)
        s.ellipse(4, 44 + oy, 43, 56 + oy, self.LEGEND["c"])
        s.ellipse(5, 44 + oy, 30, 50 + oy, self.LEGEND["w"], only=self.LEGEND["c"])
        s.ellipse(14, 51 + oy, 43, 56 + oy, self.LEGEND["a"], only=self.LEGEND["c"])
        self.hline(s, 12, 36, 50 + oy, "a")
        # 띠
        self.thick_line(s, 14, 45 + oy, 26, 53 + oy, 2, "6", "6")
        # 장화 (끝)
        side_r = dir_ in ("down", "right", "up")
        if side_r:
            self.box(s, 40, 48 + oy, 46, 51 + oy, "1"); self.box(s, 41, 53 + oy, 47, 56 + oy, "1")
        else:
            self.box(s, 1, 48 + oy, 7, 51 + oy, "1"); self.box(s, 0, 53 + oy, 6, 56 + oy, "1")
        # 머리
        head = {"down": (2, 42), "up": (36, 42), "right": (2, 42), "left": (36, 42)}[dir_]
        hx, hy = head
        s.ellipse(hx, hy + oy, hx + 9, hy + 11 + oy, self.LEGEND["9"])
        self.box(s, hx, hy + oy, hx + 9, hy + 2 + oy, "d")
        self.px(s, hx + 9, hy + 2 + oy, "b"); self.px(s, hx + 9, hy + 1 + oy, "b")
        s.ellipse(hx + 5, hy + 5 + oy, hx + 9, hy + 11 + oy, self.LEGEND["7"], only=self.LEGEND["9"])
        if st == 1 and dir_ != "up":
            self.px(s, hx + 3, hy + 6 + oy, "K"); self.px(s, hx + 4, hy + 6 + oy, "E")
        else:
            self.px(s, hx + 3, hy + 6 + oy, "K"); self.px(s, hx + 4, hy + 6 + oy, "K")
        # 떨어진 지휘봉·흩어진 서류
        self.baton(s, 20, 41 + oy, 31, 38 + oy)
        self.papers(s, 6, 32 + oy); self.papers(s, 33, 34 + oy)
        if st == 2:
            self.papers(s, 15, 28)

    # ---------- 동작
    def poses_idle(self, dir_):
        # 거의 정지. 1px 숨, 4프레임에 서류 한 장 넘김(손 1px), 5·6 프레임 머리 미세 기울임
        bob = [0, 0, 1, 1, 0, 0]
        ps = []
        for i in range(6):
            ps.append(Pose(body_dy=bob[i], head_dy=[0, 0, 0, 0, 0, 0][i], l_hand=[0, 0, 0, -1, -1, 0][i],
                           head_dx=[0, 0, 0, 0, 1, 1][i] if dir_ in ("down", "up") else 0,
                           lean=[0, 0, 0, 0, 1, 1][i] if dir_ in ("left", "right") else 0))
        return ps, self.TIMING["idle"]

    def poses_walk(self, dir_):
        side = dir_ in ("left", "right")
        ps = []
        if not side:
            L = [0, 1, 2, 1, 0, 0, 0, 0]; R = [0, 0, 0, 0, 0, 1, 2, 1]
            bob = [0, 0, -1, 0, 0, 0, -1, 0]
            for i in range(8):
                ps.append(Pose(l_lift=L[i], r_lift=R[i], body_dy=bob[i], l_hand=[0, 0, -1, 0, 0, 0, -1, 0][i], r_hand=[0, 0, 1, 0, 0, 0, 1, 0][i]))
        else:
            F = [2, 1, 0, -1, -2, -1, 0, 1]
            bob = [0, 0, -1, 0, 0, 0, -1, 0]
            LS = [0, 0, 0, 0, 0, 1, 1, 0]; RS = [0, 1, 1, 0, 0, 0, 0, 0]
            for i in range(8):
                ps.append(Pose(l_dx=F[i], r_dx=-F[i], l_sl=LS[i], r_sl=RS[i], body_dy=bob[i], lean=1 if i in (2, 3, 6, 7) else 0,
                               item={"flare": 1 if i in (0, 1, 4, 5) else 0}))
        return ps, self.TIMING["walk"]

    def poses_attack(self, dir_):
        # 1 예고: 가벼운 목례 + 지휘봉 가슴 앞 (telegraphMs) · 2·3 돌진: 지휘봉 앞으로, 자락 날림 · 4 휘두름(부채꼴 탄 발사 겸용)
        side = dir_ in ("left", "right")
        fwd = {"down": (0, 2), "up": (0, -2), "right": (2, 0), "left": (2, 0)}[dir_]
        ps = [Pose(item={"baton": "raise"}, head_dy=1, body_dy=1 if not side else 0, lean=1, body_dx=-1 if side else 0),
              Pose(item={"baton": "point", "flare": 2}, body_dx=fwd[0], body_dy=fwd[1], lean=1, head_dy=1,
                   l_lift=0, r_lift=2 if not side else 0, l_dx=2 if side else 0, r_dx=-2 if side else 0, r_sl=1 if side else 0),
              Pose(item={"baton": "point", "flare": 3}, body_dx=fwd[0], body_dy=fwd[1], lean=1, head_dy=1,
                   l_lift=2 if not side else 0, r_lift=0, l_dx=-2 if side else 0, r_dx=2 if side else 0, l_sl=1 if side else 0),
              Pose(item={"baton": "sweep", "flare": 1}, body_dx=fwd[0] // 2, body_dy=fwd[1] // 2)]
        return ps, self.TIMING["attack"]

    def poses_death(self, dir_):
        side = dir_ in ("left", "right")
        ps = [Pose(head_dx=1, eye="x", head_dy=-1, l_hand=-1, r_hand=-1),
              Pose(body_dx=-1, head_dx=-1, eye="x", body_dy=1, lean=-1, item={"baton": "none"}, l_hand=1, r_hand=1),
              Pose(crouch=5, body_dy=5, head_dy=1, eye="x", lean=1, item={"baton": "none", "flare": 3}, l_hand=4, r_hand=4),
              Pose(crouch=9, body_dy=9, head_dy=1, head_dx=-1, eye="x", lean=2, item={"baton": "none", "flare": 4}, l_hand=6, r_hand=6),
              Pose(heap=1), Pose(heap=2)]
        if side:
            for p in ps[:4]:
                p.l_dx = 2; p.r_dx = -2
        return ps, self.TIMING["death"]


# ============================================================ 내보내기 · 미리보기
ACTIONS = [("idle", True), ("walk", True), ("attack", False), ("hurt", False), ("death", False)]


def build(rig):
    W, H = rig.W, rig.H
    all_frames = {}
    for name, loop in ACTIONS:
        frames = {}
        durations = None
        for d in DIRS:
            ps, durs = rig.poses(name, d)
            durations = durs
            frames[d] = [rig.render(d, p).composite(1) for p in ps]
        n = len(durations)
        sheet = Image.new("RGBA", (W * n, H * len(DIRS)), (0, 0, 0, 0))
        for r, d in enumerate(DIRS):
            for c, im in enumerate(frames[d]):
                sheet.alpha_composite(im, (c * W, r * H))
        sheet.save(os.path.join(OUT_ASSETS, "%s_%s.png" % (rig.ID, name)))
        fps = round(1000.0 / (sum(durations) / n))
        meta = {
            "image": "%s_%s.png" % (rig.ID, name),
            "action": name,
            "frameWidth": W, "frameHeight": H,
            "frames": n,
            "directions": DIRS,
            "layout": "row = direction (directions order), column = frame index",
            "frameIndex": "row * frames + column",
            "fps": fps,
            "frameDurationsMs": durations,
            "loop": loop,
            "pivot": {"x": rig.PIVOT[0], "y": rig.PIVOT[1]},
            "palette": "parts/art/palette/lopad.json (gray + floor 1 accent slots; system swaps slots 16..27 per floor)",
        }
        if name == "attack":
            meta["phaseFrames"] = {"telegraph": [0], "dash": [1, 2], "recover_or_fan": [3]}
            meta["note"] = "frame 0 = hold for phase.dash.telegraphMs; frames 1-2 loop during dash durationMs; frame 3 on stop / wall stun / fan release"
        with open(os.path.join(OUT_ASSETS, "%s_%s.json" % (rig.ID, name)), "w", encoding="utf-8") as fp:
            json.dump(meta, fp, ensure_ascii=False, indent=1)
        for d in DIRS:
            ims = [im.resize((W * 4, H * 4), Image.NEAREST) for im in frames[d]]
            bg = []
            for im in ims:
                b = Image.new("RGBA", im.size, FLOOR + (255,))
                b.alpha_composite(im)
                bg.append(b.convert("P", palette=Image.ADAPTIVE))
            bg[0].save(os.path.join(HERE, "gif", "%s_%s_%s.gif" % (rig.ID, name, d)), save_all=True,
                       append_images=bg[1:], loop=0, duration=durations, disposal=2)
        all_frames[name] = (frames, durations)
    preview(rig, all_frames)
    return all_frames


def preview(rig, all_frames, scale=3):
    W, H = rig.W, rig.H
    cw, ch = W * scale, H * scale
    gap = 2
    blocks = []
    for name, (frames, durs) in all_frames.items():
        n = len(durs)
        bw = n * (cw + gap) + gap + 40
        bh = len(DIRS) * (ch + gap) + gap + 16
        blk = Image.new("RGB", (bw, bh), (70, 72, 76))
        d = ImageDraw.Draw(blk)
        d.text((4, 1), "%s %s x%d  %s" % (rig.ID, name, n, durs), fill=(235, 235, 235), font=FONT)
        for r, dd in enumerate(DIRS):
            d.text((2, 16 + gap + r * (ch + gap) + ch // 2 - 6), dd[:2], fill=(235, 235, 235), font=FONT)
            for c, im in enumerate(frames[dd]):
                cell = Image.new("RGBA", (cw, ch), FLOOR + (255,))
                cell.alpha_composite(im.resize((cw, ch), Image.NEAREST))
                blk.paste(cell.convert("RGB"), (40 + gap + c * (cw + gap), 16 + gap + r * (ch + gap)))
        blocks.append(blk)
    cols = 2
    rows = (len(blocks) + 1) // 2
    bw = max(b.width for b in blocks)
    bh = max(b.height for b in blocks)
    img = Image.new("RGB", (cols * (bw + 8) + 8, rows * (bh + 8) + 8), (40, 40, 44))
    for i, b in enumerate(blocks):
        r, c = divmod(i, cols)
        img.paste(b, (8 + c * (bw + 8), 8 + r * (bh + 8)))
    img.save(os.path.join(HERE, "preview_%s.png" % rig.ID))


def preview_scale(rigs, scale=4):
    """주인공·적 3종·보스·황제 idle down (+ 보스·황제 right) 발바닥 정렬, 바닥 G04."""
    def load(path, w, h):
        return Image.open(path).convert("RGBA").crop((0, 0, w, h))
    items = [("player", load(os.path.join(ROOT, "assets", "sprites", "player", "player_idle.png"), 16, 24), 23)]
    for eid, w in (("dummy", 16), ("archer", 16), ("charger", 24)):
        items.append((eid, load(os.path.join(ROOT, "assets", "sprites", "enemies", "%s_idle.png" % eid), w, 24), 23))
    for rig in rigs:
        ps, _ = rig.poses("idle", "down")
        items.append((rig.ID, rig.render("down", ps[0]).composite(1), rig.GROUND))
        ps, _ = rig.poses("idle", "right")
        items.append((rig.ID + " R", rig.render("right", ps[0]).composite(1), rig.GROUND))
    gap = 10
    Hmax = 64
    Wd = sum(im.width * scale + gap for _, im, _ in items) + gap
    Hd = Hmax * scale + 36
    out = Image.new("RGB", (Wd, Hd), FLOOR)
    d = ImageDraw.Draw(out)
    x = gap
    for name, im, ground in items:
        w, h = im.width * scale, im.height * scale
        out.paste(im.resize((w, h), Image.NEAREST), (x, 20 + (Hmax - 1 - ground) * scale), im.resize((w, h), Image.NEAREST))
        d.text((x, 4), name, fill=(235, 235, 235), font=FONT)
        x += w + gap
    # 바닥선
    d.line([(0, 20 + Hmax * scale), (Wd, 20 + Hmax * scale)], fill=(33, 34, 36))
    out.save(os.path.join(HERE, "preview_scale.png"))


def stats(rig, all_frames, gray_budget, acc_budget):
    used = set()
    semi = 0
    iso = []
    for name, (frames, durs) in all_frames.items():
        for d in DIRS:
            for i, im in enumerate(frames[d]):
                px = im.load()
                for y in range(im.height):
                    for x in range(im.width):
                        r, g, b, a = px[x, y]
                        if a:
                            used.add("#%02x%02x%02x" % (r, g, b))
                            if 0 < a < 255:
                                semi += 1
                            if not any(0 <= x + dx < im.width and 0 <= y + dy < im.height and px[x + dx, y + dy][3] > 0
                                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                                iso.append((name, d, i + 1, x, y))
    gray = sorted(G.index(c) for c in used if c in G)
    amb = sorted(16 + A.index(c) for c in used if c in A)
    other = [c for c in used if c not in G and c not in A]
    print("[%s] gray %d/%d %s | accent %d/%d %s | other %s | semi %d | isolated %d" % (
        rig.ID, len(gray), gray_budget, gray, len(amb), acc_budget, amb, other, semi, len(iso)))
    for r in iso[:40]:
        print("   iso", r)


def main():
    rigs = [Brewer(), Emperor()]
    for rig in rigs:
        af = build(rig)
        stats(rig, af, 12, 6)
        print("built", rig.ID)
    preview_scale(rigs)


if __name__ == "__main__":
    main()
