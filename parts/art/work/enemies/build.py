#!/usr/bin/env python3
"""LOPAD 1층 일반 적 3종 스프라이트 빌드 — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/enemies/build.py
입력: parts/art/palette/lopad.json, assets/sprites/player/player_idle.png (크기 비교용)
산출:
  assets/sprites/enemies/<id>_<action>.png/.json   id = dummy / archer / charger
      가로 = 프레임, 세로 = 방향 (down/up/left/right). 계약 contracts/art-assets.md §1
  parts/art/work/enemies/preview_<id>.png   전 동작 한눈에 (4배)
  parts/art/work/enemies/preview_all.png    3종 idle down + 주인공 크기 비교 (6배)
  parts/art/work/enemies/gif/<id>_<action>_<dir>.gif

디자인 (실루엣으로 구분, 르네상스 화약 전장 + 술독 하층민)
  dummy   징집병 16x24  술통을 갑옷처럼 두른 주정뱅이. 왼손 술병, 오른손 곤봉. 벌어진 다리, 처진 천모자. 강조: 술(21)·코(23)
  archer  사수   16x24  마른 화승총병. 삼각 모자(챙 12폭), 긴 총신(쇠 G07), 탄띠. 강조: 화승 불씨(23), 총구 화염(21·25)
  charger 결사병 24x24  어깨 넓은 방패·망치병. 통 투구(눈 틈), 큰 파비스 방패(잔 문장=호박 잔), 어깨에 멘 큰 망치. 강조: 문장(21·19)
  공통: 검정 셀아웃(inside), 빛 좌상단, 좌/우 뷰는 거울이 아니라 형태 반전 + 빛 역할 교환 + 보이는 소지품 교체.
  색 예산: 무채 <=8 + 강조 <=3 (각 적).
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

OUT_ASSETS = os.path.join(ROOT, "assets", "sprites", "enemies")
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


class Pose:
    def __init__(self, **kw):
        self.body_dx = 0; self.body_dy = 0
        self.head_dx = 0; self.head_dy = 0
        self.hat_dx = 0; self.hat_dy = 0
        self.l_lift = 0; self.r_lift = 0        # 정면/후면 다리 들림
        self.l_dx = 0; self.r_dx = 0            # 옆면 다리 앞뒤
        self.l_sl = 0; self.r_sl = 0            # 옆면 다리 들림
        self.l_hand = 0; self.r_hand = 0        # 팔 손 y 오프셋
        self.l_arm = "rest"; self.r_arm = "rest"
        self.l_pos = None; self.r_pos = None    # 'pos' 모드 손 좌표
        self.crouch = 0
        self.lean = 0
        self.eye = None                          # 눈 교체 문자
        self.flash = False
        self.heap = None                         # 1, 2 : 쓰러진 더미 단계
        self.item = {}                           # 적별 소지품 상태
        for k, v in kw.items():
            setattr(self, k, v)


class Rig:
    """공통 리그. 하위 클래스가 W/H/LEGEND/지도/draw_* 를 정의한다."""
    W = 16; H = 24
    LEGEND = {}
    LIGHT_SWAP = {}
    ID = ""
    TIMING = {}

    def __init__(self):
        self.GROUND = self.H - 1
        self.PALETTE = [v for v in self.LEGEND.values() if v]
        self._keep = set()   # 셀아웃에서 제외할 픽셀 (소지품·강조색)

    # ---------- 기본 그리기
    def px(self, s, x, y, ch, only_empty=False, keep=False):
        if 0 <= x < self.W and 0 <= y < self.H and ch in self.LEGEND and self.LEGEND[ch]:
            if only_empty and s.get(x, y) is not None:
                return
            s.px(x, y, self.LEGEND[ch])
            if keep:
                self._keep.add((x, y))
            else:
                self._keep.discard((x, y))

    def kline(self, s, x0, y0, x1, y1, ch):
        """keep 선 (Bresenham)."""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        x, y = x0, y0
        while True:
            self.px(s, x, y, ch, keep=True)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x += sx
            if e2 <= dx:
                err += dx; y += sy

    def blit(self, s, rows, ox, oy, mirror=False, swap=False, only_empty=False):
        for j, row in enumerate(rows):
            n = len(row)
            for i, ch in enumerate(row):
                if ch == ".":
                    continue
                if swap:
                    ch = self.LIGHT_SWAP.get(ch, ch)
                x = ox + (n - 1 - i if mirror else i)
                self.px(s, x, oy + j, ch, only_empty)

    def hline(self, s, x0, x1, y, ch, swap=False, keep=False):
        if swap:
            ch = self.LIGHT_SWAP.get(ch, ch)
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.px(s, x, y, ch, keep=keep)

    def vline(self, s, x, y0, y1, ch, swap=False, keep=False):
        if swap:
            ch = self.LIGHT_SWAP.get(ch, ch)
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.px(s, x, y, ch, keep=keep)

    def arm(self, s, sx, sy, hx, hy, hi, lo, hand):
        """어깨→손 2px 두께 팔 (밝은 줄 + 어두운 줄), 끝에 손."""
        if abs(hx - sx) > abs(hy - sy):
            s.line(sx, sy, hx, hy, self.LEGEND[hi]); s.line(sx, sy + 1, hx, hy + 1, self.LEGEND[lo])
        else:
            d = 1 if hx >= sx else -1
            s.line(sx, sy, hx, hy, self.LEGEND[hi if d < 0 else lo])
            s.line(sx + d, sy, hx + d, hy, self.LEGEND[lo if d < 0 else hi])
        self.px(s, hx, hy, hand)

    def legs_front(self, s, p, cols, top, leg, hi, boot, boot_h=2, gap_ch=None):
        """정면 다리. cols = ((x0,x1),(x0,x1)). 들린 다리는 짧아지고 장화가 올라간다."""
        for (x0, x1), lift in zip(cols, (p.l_lift, p.r_lift)):
            boot_top = self.GROUND - (boot_h - 1) - lift
            for y in range(top, boot_top):
                for x in range(x0, x1 + 1):
                    self.px(s, x, y, hi if x == x0 else leg)
            for y in range(boot_top, boot_top + boot_h):
                for x in range(x0, x1 + 1):
                    self.px(s, x, y, boot if y > boot_top else boot[0])
        if gap_ch:
            gx0, gx1 = cols[0][1] + 1, cols[1][0] - 1
            for y in range(top, self.GROUND + 1):
                for x in range(gx0, gx1 + 1):
                    if s.get(cols[0][1], y) is not None and s.get(cols[1][0], y) is not None:
                        self.px(s, x, y, gap_ch)

    def legs_side(self, s, p, m, back_x, front_x, w, top, leg, hi, sep, boot, boot_h=2):
        """옆 다리. m=+1 우향. back_x/front_x = 우향 기준 뒷다리·앞다리 왼쪽 x. 좌향은 거울."""
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
                    elif i == 0:
                        ch = hi
                    else:
                        ch = leg
                    self.px(s, x, y, ch)
            bx0 = x0 if m > 0 else x0 - 1
            for y in range(boot_top, boot_top + boot_h):
                for i in range(w + 1):
                    self.px(s, bx0 + i, y, boot if y > boot_top else boot[0])

    def finish(self, s, p):
        """셀아웃(inside) — keep 마스크 픽셀은 제외. 그 뒤 피격 플래시."""
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
            im = s._img(); px = im.load()
            for y in range(self.H):
                for x in range(self.W):
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

    # ---------- 동작 (공통 기본값, 하위 클래스가 덮어쓴다)
    def poses(self, action, dir_):
        return getattr(self, "poses_" + action)(dir_)

    def poses_hurt(self, dir_):
        back = {"down": (0, -1), "up": (0, 1), "right": (-1, 0), "left": (1, 0)}[dir_]
        ps = [Pose(flash=True, body_dx=back[0], body_dy=back[1], head_dx=back[0], eye="x"),
              Pose(body_dx=back[0], body_dy=back[1], head_dx=-1 if dir_ in ("down", "up") else 0,
                   hat_dx=-1 if dir_ in ("down", "up") else 0, eye="x", l_hand=-1, r_hand=-1,
                   lean=-1 if dir_ in ("left", "right") else 0)]
        return ps, self.TIMING["hurt"]


# ============================================================ 공통 지도 유틸
def rows_mirror(rows):
    return [r[::-1] for r in rows]


# ============================================================ 1. 징집병 dummy
class Dummy(Rig):
    ID = "dummy"
    W, H = 16, 24
    LEGEND = {
        ".": None,
        "K": G[0],   # 셀아웃·장화
        "1": G[1],   # 깊은 그림자
        "3": G[3],   # 널 틈·바지 그늘
        "4": G[5],   # 술통 널·바지 (바닥 G04 보다 한 단 밝게)
        "6": G[6],   # 천(모자·소매)·곤봉
        "8": G[8],   # 쇠테 하이라이트·천 하이라이트
        "7": G[7],   # 피부 그늘·수염
        "9": G[9],   # 피부
        "B": A[5],   # 21 술
        "L": A[7],   # 23 취한 코
    }
    LIGHT_SWAP = {"8": "3", "3": "8", "9": "7", "7": "9"}
    TIMING = {"idle": [220, 220, 220, 180, 220, 220], "walk": [120] * 8, "attack": [120, 50, 110, 120],
              "hurt": [70, 90], "death": [90, 110, 110, 120, 140, 200]}

    CAP_DOWN = [
        "..8666..",
        ".866663.",
        "86666633",
    ]
    FACE_DOWN = [
        "99999997",
        "9K9999K7",
        "999L9977",
        "97777777",
        ".977777.",
    ]
    CAP_UP = [
        "..8666..",
        ".866663.",
        "86666633",
    ]
    FACE_UP = [       # 뒤통수: 목덜미·귀
        "97777777",
        "97777777",
        "97777777",
        ".777777.",
        "..9777..",
    ]
    CAP_SIDE = [      # 우향 (앞 = 오른쪽), 처진 끝이 뒤로
        "..8666.",
        ".866663",
        "866663.",
    ]
    FACE_SIDE = [     # 우향 6폭
        "999999",
        "9999K9",
        "99997L",
        "977777",
        ".9777.",
    ]
    # 술통 몸통: y10..17 행별 (x0, x1). 가운데가 배부르다.
    BARREL = {10: (4, 11), 11: (3, 12), 12: (3, 12), 13: (2, 13), 14: (2, 13), 15: (3, 12), 16: (3, 12), 17: (4, 11)}
    BARREL_SIDE = {10: (5, 10), 11: (4, 11), 12: (4, 11), 13: (4, 12), 14: (4, 12), 15: (4, 11), 16: (4, 11), 17: (5, 10)}

    def barrel(self, s, p, prof, dx, dy, swap=False, back=False):
        for y, (x0, x1) in prof.items():
            yy = y + dy
            for x in range(x0, x1 + 1):
                self.px(s, x + dx, yy, "4")
            self.px(s, x0 + dx, yy, "3" if swap else "6")      # 왼쪽 빛
            self.px(s, x1 + dx, yy, "6" if swap else "3")      # 오른쪽 그늘
            self.px(s, x1 - 1 + dx, yy, "4" if swap else "3")
        # 널 틈
        xs = (6, 9) if len(prof[13]) and prof[13][1] - prof[13][0] < 10 else (5, 8, 11)
        for x in xs:
            for y in prof:
                self.px(s, x + dx, y + dy, "3" if not swap else "3")
        # 쇠테 2줄 (y11, y16): 어두운 띠 + 빛 쪽 하이라이트 2px
        for y in (11, 16):
            x0, x1 = prof[y]
            self.hline(s, x0 + dx, x1 + dx, y + dy, "3")
            hx = x0 + 1 if not swap else x1 - 2
            self.px(s, hx + dx, y + dy, "8"); self.px(s, hx + 1 + dx, y + dy, "8")
        if back:   # 등 뒤 멜빵 끈
            self.vline(s, 6 + dx, 10 + dy, 17 + dy, "1"); self.vline(s, 9 + dx, 10 + dy, 17 + dy, "1")

    def club(self, s, hx, hy, dirn, length=4):
        """곤봉: 손에서 dirn 방향으로 length, 끝 2px 두껍게. 나무 G6, 그늘 G3."""
        dx, dy = dirn
        for i in range(1, length + 1):
            self.px(s, hx + dx * i, hy + dy * i, "6", keep=True)
        ex, ey = hx + dx * length, hy + dy * length
        ox, oy = (1 if dx == 0 else 0), (1 if dy == 0 else 0)
        for i in (0, 1):
            self.px(s, ex + dx * i, ey + dy * i, "6", keep=True)
            self.px(s, ex + dx * i + ox, ey + dy * i + oy, "3", keep=True)
        self.px(s, ex + dx * 2, ey + dy * 2, "3", keep=True)
        self.px(s, ex + dx * 2 + ox, ey + dy * 2 + oy, "1", keep=True)

    def bottle(self, s, x, y, up=False):
        """술병 (2폭): 목 1 + 몸통 2x3, 술 B 2px. up: 들어 올려 기울임."""
        k = dict(keep=True)
        if up:
            self.px(s, x, y, "7", **k); self.px(s, x + 1, y, "9", **k)
            self.px(s, x, y + 1, "B", **k); self.px(s, x + 1, y + 1, "B", **k); self.px(s, x, y + 2, "B", **k); self.px(s, x + 1, y + 2, "7", **k)
        else:
            self.px(s, x, y, "7", **k)
            for yy in range(y + 1, y + 4):
                self.px(s, x, yy, "9" if yy == y + 1 else "7", **k); self.px(s, x + 1, yy, "7", **k)
            self.px(s, x, y + 2, "B", **k); self.px(s, x + 1, y + 2, "B", **k); self.px(s, x, y + 3, "B", **k); self.px(s, x + 1, y + 3, "S" if "S" in self.LEGEND else "B", **k)

    def draw_down(self, s, p, back=False):
        dx, dy = p.body_dx, p.body_dy
        self.legs_front(s, p, ((4, 6), (9, 11)), 18 + dy + p.crouch, "4", "6", "K1")
        self.barrel(s, p, self.BARREL, dx, dy + p.crouch, back=back)
        # 팔: 소매 x1..2 / x13..14, y12..16  (rest)
        for side, ax, hoff, mode, pos in (("l", 1, p.l_hand, p.l_arm, p.l_pos), ("r", 13, p.r_hand, p.r_arm, p.r_pos)):
            if mode == "rest":
                top, bot = 12 + dy + p.crouch, 16 + dy + p.crouch + hoff
                for y in range(top, bot + 1):
                    self.px(s, ax + dx, y, "8" if side == "l" else "6"); self.px(s, ax + 1 + dx, y, "6" if side == "l" else "3")
                hx = ax + dx if side == "l" else ax + 1 + dx
                self.px(s, hx, bot + 1, "9")
                if side == "l" and not back:
                    if p.item.get("drink"):
                        self.bottle(s, 2 + dx, 7 + dy, up=True)
                    else:
                        self.bottle(s, 0 + dx, bot - 1, up=False)
                if side == "r" and not back:
                    self.club(s, hx, bot + 1, (0, 1), 3)
                if back:
                    if side == "l":
                        self.bottle(s, 0 + dx, bot - 1)
                    else:
                        self.club(s, hx, bot + 1, (0, 1), 3)
            elif mode == "pos":
                sx = (3 if side == "l" else 12) + dx
                self.arm(s, sx, 12 + dy + p.crouch, pos[0], pos[1], "8", "3", "9")
                if side == "r":
                    self.club(s, pos[0], pos[1], p.item.get("club_dir", (0, 1)), p.item.get("club_len", 3))
                if side == "l" and not back:
                    self.bottle(s, pos[0] - 1, pos[1] - 2)
        # 머리
        hy = 5 + dy + p.head_dy + p.crouch
        hx = 4 + dx + p.head_dx
        face = self.FACE_UP if back else self.FACE_DOWN
        if p.eye and not back:
            face = [face[0], face[1].replace("K", p.eye)] + face[2:]
        self.blit(s, face, hx, hy)
        self.blit(s, self.CAP_UP if back else self.CAP_DOWN, hx + p.hat_dx, hy - 3 + p.hat_dy)

    def draw_up(self, s, p):
        self.draw_down(s, p, back=True)

    def draw_side(self, s, p, m):
        swap = m < 0
        dx, dy = p.body_dx * m, p.body_dy
        self.legs_side(s, p, m, 5, 8, 3, 18 + dy + p.crouch, "4", "6", "3", "K1")
        prof = self.BARREL_SIDE if m > 0 else {y: (self.W - 1 - x1, self.W - 1 - x0) for y, (x0, x1) in self.BARREL_SIDE.items()}
        self.barrel(s, p, prof, dx, dy + p.crouch, swap=swap)
        # 가까운 팔: 우향 = 왼팔(술병) / 좌향 = 오른팔(곤봉)
        near_bottle = m > 0
        ax = (11 if m > 0 else 4) + dx
        top = 12 + dy + p.crouch
        mode = p.l_arm if near_bottle else p.r_arm
        pos = p.l_pos if near_bottle else p.r_pos
        hoff = p.l_hand if near_bottle else p.r_hand
        if mode == "rest":
            bot = 16 + dy + p.crouch + hoff
            for y in range(top, bot + 1):
                self.px(s, ax, y, "6"); self.px(s, ax - m, y, "3")
            self.px(s, ax, bot + 1, "9")
            if near_bottle:
                if p.item.get("drink"):
                    self.bottle(s, ax - 1, 7 + dy, up=True)
                else:
                    self.bottle(s, ax, bot - 1)
            else:
                self.club(s, ax, bot + 1, (0, 1), 3)
        elif mode == "pos":
            self.arm(s, ax, top, pos[0], pos[1], "8" if m > 0 else "3", "3" if m > 0 else "8", "9")
            if near_bottle:
                self.bottle(s, pos[0], pos[1] - 2)
            else:
                self.club(s, pos[0], pos[1], p.item.get("club_dir", (0, 1)), p.item.get("club_len", 3))
        # 먼 쪽 소지품 끝이 어깨 위로 삐죽
        if m > 0:
            self.px(s, 3 + dx, 8 + dy + p.crouch, "6", keep=True); self.px(s, 4 + dx, 8 + dy + p.crouch, "6", keep=True)
            self.px(s, 3 + dx, 9 + dy + p.crouch, "3", keep=True); self.px(s, 4 + dx, 9 + dy + p.crouch, "3", keep=True)
            self.px(s, 4 + dx, 10 + dy + p.crouch, "6", keep=True)
        else:
            self.px(s, 11 + dx, 10 + dy + p.crouch, "7", keep=True); self.px(s, 11 + dx, 9 + dy + p.crouch, "9", keep=True)
        # 머리 6폭: 우향 x5..10
        hy = 5 + dy + p.head_dy + p.crouch
        hx = (5 if m > 0 else 5) + dx + p.lean * m
        face = self.FACE_SIDE
        if p.eye:
            face = [face[0], face[1].replace("K", p.eye)] + face[2:]
        self.blit(s, face, hx, hy, mirror=swap, swap=swap)
        self.blit(s, self.CAP_SIDE, hx - 1 + (0 if m > 0 else 1), hy - 3 + p.hat_dy, mirror=swap, swap=swap)

    def draw_heap(self, s, p, dir_):
        st = p.heap
        oy = 0 if st == 1 else 1
        # 술통이 옆으로 누움 (가로로 긴 통)
        s.rect(2, 15 + oy, 13, 21 + oy, self.LEGEND["4"])
        s.rect(3, 14 + oy, 12, 14 + oy, self.LEGEND["4"]); s.rect(3, 22 + oy, 12, 22 + oy, self.LEGEND["3"])
        for x in (4, 11):
            self.vline(s, x, 14 + oy, 22 + oy, "6")
        self.px(s, 4, 15 + oy, "8"); self.px(s, 4, 16 + oy, "8")
        self.hline(s, 5, 10, 18 + oy, "3")
        head = {"down": (0, 17), "up": (11, 14), "right": (10, 16), "left": (0, 16)}[dir_]
        hx, hy = head
        s.rect(hx, hy + oy, hx + 3, hy + 3 + oy, self.LEGEND["9"])
        s.rect(hx, hy + 3 + oy, hx + 3, hy + 3 + oy, self.LEGEND["7"])
        if st == 1 and dir_ != "up":
            self.px(s, hx + 1, hy + 1 + oy, "x")
        # 쏟아진 술 (마지막 프레임에 넓어짐)
        if st == 1:
            self.px(s, 13, 22, "B"); self.px(s, 14, 22, "B")
        else:
            self.hline(s, 12, 15, 23, "B"); self.px(s, 14, 22, "B"); self.px(s, 15, 22, "B")
        # 곤봉 떨어짐
        self.hline(s, 1, 4, 23, "6") if dir_ != "left" else self.hline(s, 11, 14, 23, "6")

    # ---------- 동작
    def poses_idle(self, dir_):
        sway = [0, 0, 1, 1, 0, -1]
        bob = [0, 1, 1, 0, 0, 0]
        ps = []
        for i in range(6):
            ps.append(Pose(body_dx=sway[i], body_dy=bob[i], head_dx=sway[i], hat_dy=1 if i in (2, 3) else 0,
                           item={"drink": i in (3, 4)}, l_hand=-2 if i in (3, 4) else 0))
        return ps, self.TIMING["idle"]

    def poses_walk(self, dir_):
        side = dir_ in ("left", "right")
        ps = []
        if not side:
            L = [0, 1, 2, 1, 0, 0, 0, 0]; R = [0, 0, 0, 0, 0, 1, 2, 1]
            bob = [0, 0, -1, 0, 0, 0, -1, 0]; sway = [1, 1, 0, 0, -1, -1, 0, 0]
            for i in range(8):
                ps.append(Pose(l_lift=L[i], r_lift=R[i], body_dy=bob[i], body_dx=sway[i], head_dx=sway[i],
                               l_hand=[1, 1, 0, -1, -1, -1, 0, 1][i], r_hand=[-1, -1, 0, 1, 1, 1, 0, -1][i]))
        else:
            F = [2, 1, 0, -1, -2, -1, 0, 1]
            bob = [0, 0, -1, 0, 0, 0, -1, 0]
            LS = [0, 0, 0, 0, 0, 1, 1, 0]; RS = [0, 1, 1, 0, 0, 0, 0, 0]
            for i in range(8):
                ps.append(Pose(l_dx=F[i], r_dx=-F[i], l_sl=LS[i], r_sl=RS[i], body_dy=bob[i], lean=1 if i in (2, 3, 6, 7) else 0,
                               l_hand=-F[i] // 2, r_hand=-F[i] // 2))
        return ps, self.TIMING["walk"]

    def poses_attack(self, dir_):
        # 곤봉 내리치기: 1 머리 위로 들어올림 · 2 휘두름(짧게) · 3 땅에 내리꽂힘 유지 · 4 복귀
        if dir_ == "down":
            ps = [Pose(r_arm="pos", r_pos=(14, 7), item={"club_dir": (0, -1), "club_len": 4}, body_dy=-1, head_dy=-1),
                  Pose(r_arm="pos", r_pos=(14, 12), item={"club_dir": (1, 0), "club_len": 1}, body_dx=-1),
                  Pose(r_arm="pos", r_pos=(12, 19), item={"club_dir": (0, 1), "club_len": 3}, body_dy=1, head_dy=1, crouch=1, body_dx=-1),
                  Pose(r_hand=1, body_dy=1)]
        elif dir_ == "up":
            ps = [Pose(r_arm="pos", r_pos=(14, 8), item={"club_dir": (0, -1), "club_len": 4}, body_dy=-1),
                  Pose(r_arm="pos", r_pos=(14, 3), item={"club_dir": (-1, 0), "club_len": 3}, body_dy=-1),
                  Pose(r_arm="pos", r_pos=(10, 2), item={"club_dir": (-1, 0), "club_len": 4}, body_dy=1, crouch=1),
                  Pose(r_hand=1)]
        elif dir_ == "right":
            ps = [Pose(l_arm="pos", l_pos=(6, 7), item={"club_dir": (-1, 0), "club_len": 2}, body_dx=-1, lean=-1),
                  Pose(l_arm="pos", l_pos=(13, 8), body_dx=1, lean=1),
                  Pose(l_arm="pos", l_pos=(14, 14), body_dx=1, lean=1, body_dy=1, crouch=1),
                  Pose(l_hand=1, lean=1)]
            # 우향: 가까운 팔은 술병 팔이므로, 공격은 먼 쪽 곤봉이 머리 위로 돌아 나옴 → 곤봉을 손 위치에 직접 그림
            for p in ps[:3]:
                p.item.update({"club_side": True})
        else:
            ps = [Pose(r_arm="pos", r_pos=(9, 6), item={"club_dir": (1, 0), "club_len": 2}, body_dx=-1, lean=-1),
                  Pose(r_arm="pos", r_pos=(2, 8), item={"club_dir": (-1, 0), "club_len": 1}, body_dx=1, lean=1),
                  Pose(r_arm="pos", r_pos=(1, 14), item={"club_dir": (0, 1), "club_len": 3}, body_dx=1, lean=1, body_dy=1, crouch=1),
                  Pose(r_hand=1, lean=1)]
        return ps, self.TIMING["attack"]

    def poses_death(self, dir_):
        side = dir_ in ("left", "right")
        ps = [Pose(head_dx=1, hat_dx=1, eye="x", l_hand=-1, r_hand=-1),
              Pose(body_dx=-1, head_dx=-1, hat_dx=-1, eye="x", body_dy=1, lean=1),
              Pose(crouch=2, body_dy=2, head_dy=1, eye="x", l_hand=2, r_hand=2, lean=1),
              Pose(crouch=3, body_dy=3, head_dy=2, head_dx=-1, hat_dy=1, eye="x", l_hand=3, r_hand=3, lean=2),
              Pose(heap=1), Pose(heap=2)]
        if side:
            for p in ps[:4]:
                p.l_dx = 1; p.r_dx = -1
        return ps, self.TIMING["death"]


# ============================================================ 2. 사수 archer
class Archer(Rig):
    ID = "archer"
    W, H = 16, 24
    LEGEND = {
        ".": None,
        "K": G[0],   # 셀아웃·장화·눈
        "1": G[1],   # 모자 그늘·탄띠
        "3": G[3],   # 모자 펠트·바지 그늘
        "4": G[4],   # 튜닉 그늘·개머리판(나무)·바지
        "6": G[6],   # 튜닉 본색
        "7": G[7],   # 총신(쇠)·피부 그늘
        "8": G[8],   # 튜닉 하이라이트·탄통
        "9": G[9],   # 피부·총신 글린트
        "L": A[7],   # 23 화승 불씨
        "B": A[5],   # 21 총구 화염 바깥
        "W": A[9],   # 25 총구 화염 심
    }
    LIGHT_SWAP = {"8": "4", "4": "8", "9": "7", "7": "9"}
    TIMING = {"idle": [240, 240, 240, 200, 240, 240], "walk": [100] * 8, "attack": [160, 50, 110, 130],
              "hurt": [70, 90], "death": [90, 110, 110, 120, 140, 200]}

    HAT_DOWN = [          # 삼각 모자 12폭 (x2..13), y1..y4
        "33..4333..33",
        "334333333333",
        ".3333333333.",
        "..11111111..",
    ]
    HAT_UP = [
        "33..3333..33",
        "333333333333",
        ".3433333333.",
        "..33333333..",
    ]
    HAT_SIDE = [          # 우향: 앞(오른쪽) 챙이 들려 뾰족
        "...4333.....",
        "33333333..33",
        ".33333333333",
        "..11111111..",
    ]
    FACE_DOWN = [         # 6폭 x5..10, y5..y8  (y5 는 챙 그늘 밑)
        "797797",
        "7K7797",
        "977779",
        ".9779.",
    ]
    FACE_UP = [
        "777777",
        "777777",
        "177771",
        ".7777.",
    ]
    FACE_SIDE = [         # 우향: 눈은 앞쪽
        "779797",
        "7979K9",
        "977779",
        ".9779.",
    ]
    TORSO_DOWN = [        # 6폭 x5..10, y9..y16. 탄띠 사선(1) + 탄통(8)
        "866661",
        "866618",
        "866186",
        "861866",
        "KKKKKK",
        "666661",
        "666661",
        "6.66.1",
    ]
    TORSO_UP = [
        "866661",
        "816661",
        "861661",
        "866161",
        "KKKKKK",
        "666661",
        "666661",
        "6.66.1",
    ]
    TORSO_SIDE = [        # 우향 5폭 x6..10
        "86661",
        "86661",
        "86661",
        "86661",
        "KKKKK",
        "66661",
        "66661",
        "6.6.1",
    ]

    def gun_diag(self, s, x0, y0, x1, y1, stock_len=4):
        """개머리판(4)에서 총신(7)까지 사선. 총신 글린트 1px. 자물쇠 자리에 불씨."""
        self.kline(s, x0, y0, x1, y1, "7")
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(stock_len + 1):
            t = i / float(n)
            x = round(x0 + (x1 - x0) * t); y = round(y0 + (y1 - y0) * t)
            self.px(s, x, y, "4", keep=True)
            self.px(s, x, y + 1, "3", keep=True)
        t = (stock_len + 1) / float(n)
        self.px(s, round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t) - 1, "L", keep=True)
        self.px(s, x1, y1, "9", keep=True)

    def gun_h(self, s, x_stock, y, m, length=12, ember=True):
        """옆면 수평 총: 개머리판 4px (4/3) + 총신 (7), 앞끝 글린트. m 방향."""
        for i in range(4):
            self.px(s, x_stock + i * m, y, "4", keep=True); self.px(s, x_stock + i * m, y + 1, "3", keep=True)
        for i in range(4, length):
            self.px(s, x_stock + i * m, y, "7", keep=True)
        self.px(s, x_stock + (length - 1) * m, y, "9", keep=True)
        if ember:
            self.px(s, x_stock + 4 * m, y - 1, "L", keep=True)

    def gun_v(self, s, x, y0, y1, ember=True):
        """정면/후면 수직 총 (조준 자세): 개머리판 3px 가까운 쪽, 총신 멀리."""
        step = 1 if y1 > y0 else -1
        for i, y in enumerate(range(y0, y1 + step, step)):
            self.px(s, x, y, "4" if i < 3 else "7", keep=True)
            if i < 3:
                self.px(s, x + 1, y, "3", keep=True)
        self.px(s, x, y1, "9", keep=True)
        if ember:
            self.px(s, x + 1, y0 + 3 * step, "L", keep=True)

    def flash(self, s, x, y, dirn):
        """총구 화염: 심 W 1px, L 2~3px, B 테두리. dirn = (dx, dy)."""
        dx, dy = dirn
        k = dict(keep=True)
        self.px(s, x, y, "W", **k)
        self.px(s, x + dx, y + dy, "L", **k); self.px(s, x + dx * 2, y + dy * 2, "L", **k)
        self.px(s, x + dy, y + dx, "L", **k); self.px(s, x - dy, y - dx, "L", **k)
        self.px(s, x + dx + dy, y + dy + dx, "B", **k); self.px(s, x + dx - dy, y + dy - dx, "B", **k)
        self.px(s, x + dx * 3, y + dy * 3, "B", **k)

    def smoke(self, s, x, y):
        for xx, yy in ((0, 0), (1, 0), (0, -1), (1, -1), (2, -1)):
            self.px(s, x + xx, y + yy, "8", keep=True)

    def draw_down(self, s, p, back=False):
        dx, dy = p.body_dx, p.body_dy
        self.legs_front(s, p, ((5, 6), (9, 10)), 17 + dy + p.crouch, "4", "6", "K1")
        torso = self.TORSO_UP if back else self.TORSO_DOWN
        if p.crouch:
            torso = torso[:1] + torso[1 + p.crouch:]
        self.blit(s, torso, 5 + dx, 9 + dy + p.crouch)
        aim = p.item.get("aim")
        # 총 (팔보다 먼저: 팔·손이 총 위에 얹힘)
        if aim == "down":
            self.gun_v(s, 8 + dx, 11 + dy + p.crouch, 21 + dy)
        elif aim == "up":
            self.gun_v(s, 7 + dx, 11 + dy + p.crouch, 1 + dy)
        elif not back and not p.item.get("nogun"):
            self.gun_diag(s, 2 + dx, 19 + dy, 13 + dx, 6 + dy + p.crouch)
        elif back and not p.item.get("nogun"):
            # 등에 비스듬히 멘 총 (몸통 뒤로: 보이는 부분만 어깨 위·허리 아래)
            self.gun_diag(s, 13 + dx, 19 + dy, 2 + dx, 6 + dy + p.crouch)
        # 팔
        for side, sx, hoff, mode, pos in (("l", 4, p.l_hand, p.l_arm, p.l_pos), ("r", 11, p.r_hand, p.r_arm, p.r_pos)):
            if mode == "rest":
                top = 10 + dy + p.crouch
                if aim in ("down", "up"):
                    hx, hy = (7 + dx, 14 + dy + p.crouch) if side == "l" else (9 + dx, 13 + dy + p.crouch)
                    self.arm(s, sx + dx, top, hx, hy, "8", "4", "9")
                elif back or p.item.get("nogun"):
                    bot = 15 + dy + p.crouch + hoff
                    self.vline(s, sx + dx, top, bot, "6" if side == "l" else "4")
                    self.px(s, sx + dx, bot + 1, "9")
                else:
                    # 총을 쥔 손: 왼손 개머리판 근처, 오른손 총신 중간
                    hx, hy = (4 + dx, 17 + dy + hoff) if side == "l" else (10 + dx, 10 + dy + p.crouch)
                    self.arm(s, sx + dx, top, hx, hy, "8", "4", "9")
            elif mode == "pos":
                self.arm(s, sx + dx, 10 + dy + p.crouch, pos[0], pos[1], "8", "4", "9")
        if aim == "down" and p.item.get("fire"):
            self.flash(s, 8 + dx, 22 + dy, (0, 1))
        if aim == "up" and p.item.get("fire"):
            self.flash(s, 7 + dx, 1 + dy, (0, -1))
        if p.item.get("smoke"):
            self.smoke(s, (8 if aim == "down" else 6) + dx, (21 if aim == "down" else 2) + dy)
        # 머리
        hy = 5 + dy + p.head_dy + p.crouch
        hx = 5 + dx + p.head_dx
        face = self.FACE_UP if back else self.FACE_DOWN
        if p.eye and not back:
            face = [face[0], face[1].replace("K", p.eye)] + face[2:]
        self.blit(s, face, hx, hy)
        self.blit(s, self.HAT_UP if back else self.HAT_DOWN, hx - 3 + p.hat_dx, hy - 4 + p.hat_dy)

    def draw_up(self, s, p):
        self.draw_down(s, p, back=True)

    def draw_side(self, s, p, m):
        swap = m < 0
        dx, dy = p.body_dx * m, p.body_dy
        self.legs_side(s, p, m, 5, 8, 2, 17 + dy + p.crouch, "4", "6", "3", "K1")
        torso = self.TORSO_SIDE
        if p.crouch:
            torso = torso[:1] + torso[1 + p.crouch:]
        tx = 6 if m > 0 else 5
        self.blit(s, torso, tx + dx, 9 + dy + p.crouch, mirror=swap, swap=swap)
        aim = p.item.get("aim")
        gy = p.item.get("gun_y", 13)
        if not p.item.get("nogun"):
            if m > 0:
                self.gun_h(s, 3 + dx, gy + dy + p.crouch, +1, 13)
            else:
                self.gun_h(s, 12 + dx, gy + dy + p.crouch, -1, 13)
        # 가까운 팔: 어깨 → 개머리판/총신 위의 손
        sx = (9 if m > 0 else 6) + dx
        top = 10 + dy + p.crouch
        if p.r_arm == "pos" and p.r_pos:
            self.arm(s, sx, top, p.r_pos[0], p.r_pos[1], "8" if m > 0 else "4", "4" if m > 0 else "8", "9")
        elif p.item.get("nogun"):
            bot = 15 + dy + p.crouch + p.r_hand
            self.vline(s, sx, top, bot, "6"); self.vline(s, sx - m, top, bot, "4")
            self.px(s, sx, bot + 1, "9")
        else:
            hx = (11 if m > 0 else 4) + dx
            self.arm(s, sx, top, hx, gy - 1 + dy + p.crouch, "8" if m > 0 else "4", "4" if m > 0 else "8", "9")
            # 먼 손: 총신 앞쪽
            self.px(s, (8 if m > 0 else 7) + dx, gy + dy + p.crouch + 1, "9", keep=True)
        if aim == "side" and p.item.get("fire"):
            self.flash(s, (15 if m > 0 else 0) + dx, gy + dy + p.crouch, (m, 0))
        if p.item.get("smoke"):
            self.smoke(s, (13 if m > 0 else 1) + dx, gy - 1 + dy + p.crouch)
        # 머리
        hy = 5 + dy + p.head_dy + p.crouch
        hx = 5 + dx + p.lean * m
        face = self.FACE_SIDE
        if p.eye:
            face = [face[0], face[1].replace("K", p.eye)] + face[2:]
        self.blit(s, face, hx, hy, mirror=swap, swap=swap)
        self.blit(s, self.HAT_SIDE, hx - 3 + p.hat_dx * m, hy - 4 + p.hat_dy, mirror=swap, swap=swap)

    def draw_heap(self, s, p, dir_):
        st = p.heap
        oy = 0 if st == 1 else 1
        # 마른 몸이 길게 눕는다
        s.rect(2, 18 + oy, 13, 21 + oy, self.LEGEND["6"])
        s.rect(2, 21 + oy, 13, 21 + oy, self.LEGEND["4"])
        s.line(5, 18 + oy, 10, 20 + oy, self.LEGEND["1"])
        head = {"down": (0, 17), "up": (12, 16), "right": (12, 17), "left": (0, 17)}[dir_]
        hx, hy = head
        s.rect(hx, hy + oy, hx + 3, hy + 3 + oy, self.LEGEND["9"])
        s.rect(hx, hy + 3 + oy, hx + 3, hy + 3 + oy, self.LEGEND["7"])
        if st == 1 and dir_ != "up":
            self.px(s, hx + 1 if hx == 0 else hx + 2, hy + 1 + oy, "K")
        # 모자가 굴러 떨어짐
        hat = {"down": (5, 14), "up": (3, 14), "right": (4, 14), "left": (8, 14)}[dir_]
        x, y = hat
        self.hline(s, x, x + 5, y + 1 + oy, "3"); self.hline(s, x + 1, x + 4, y + oy, "3"); self.px(s, x + 1, y + oy, "4")
        # 총이 떨어져 있음
        self.hline(s, 1, 14, 23, "7", keep=True); self.hline(s, 1, 4, 23, "4", keep=True); self.px(s, 14, 23, "9", keep=True)
        if st == 2:
            self.px(s, 5, 22, "L", keep=True)   # 불씨만 아직 남음

    def poses_idle(self, dir_):
        bob = [0, 0, 1, 1, 1, 0]
        ps = []
        for i in range(6):
            ps.append(Pose(body_dy=bob[i], hat_dy=max(0, [0, 0, 0, 1, 1, 1][i] - bob[i]), item={"gun_y": 13 + bob[i]}))
        return ps, self.TIMING["idle"]

    def poses_walk(self, dir_):
        side = dir_ in ("left", "right")
        ps = []
        if not side:
            L = [0, 1, 2, 1, 0, 0, 0, 0]; R = [0, 0, 0, 0, 0, 1, 2, 1]
            bob = [0, 0, -1, 0, 0, 0, -1, 0]
            for i in range(8):
                ps.append(Pose(l_lift=L[i], r_lift=R[i], body_dy=bob[i], l_hand=[0, 0, -1, 0, 0, 0, -1, 0][i]))
        else:
            F = [2, 1, 0, -1, -2, -1, 0, 1]
            bob = [0, 0, -1, 0, 0, 0, -1, 0]
            LS = [0, 0, 0, 0, 0, 1, 1, 0]; RS = [0, 1, 1, 0, 0, 0, 0, 0]
            for i in range(8):
                ps.append(Pose(l_dx=F[i], r_dx=-F[i], l_sl=LS[i], r_sl=RS[i], body_dy=bob[i], lean=1, item={"gun_y": 13 + bob[i]}))
        return ps, self.TIMING["walk"]

    def poses_attack(self, dir_):
        # 1 조준(들어올림) 160 · 2 발사(화염, 반동) 50 · 3 연기 110 · 4 내림 130
        if dir_ == "down":
            ps = [Pose(item={"aim": "down"}, body_dy=-1),
                  Pose(item={"aim": "down", "fire": True}, body_dy=-2, head_dy=-1),
                  Pose(item={"aim": "down", "smoke": True}, body_dy=-1),
                  Pose(body_dy=0)]
        elif dir_ == "up":
            ps = [Pose(item={"aim": "up"}, body_dy=1),
                  Pose(item={"aim": "up", "fire": True}, body_dy=2, head_dy=1),
                  Pose(item={"aim": "up", "smoke": True}, body_dy=1),
                  Pose()]
        else:
            back = -1
            ps = [Pose(item={"aim": "side", "gun_y": 10}, lean=1),
                  Pose(item={"aim": "side", "gun_y": 10, "fire": True}, body_dx=back, lean=-1, head_dx=back),
                  Pose(item={"aim": "side", "gun_y": 11, "smoke": True}, body_dx=back, lean=0),
                  Pose(item={"gun_y": 13})]
        return ps, self.TIMING["attack"]

    def poses_death(self, dir_):
        side = dir_ in ("left", "right")
        ps = [Pose(head_dx=1, hat_dx=1, eye="7", l_hand=-1, r_hand=-1),
              Pose(body_dy=1, head_dx=-1, hat_dx=-1, eye="7", lean=-1, item={"nogun": True}, l_hand=1, r_hand=1),
              Pose(crouch=2, body_dy=2, head_dy=1, eye="7", lean=1, item={"nogun": True}, l_hand=2, r_hand=2),
              Pose(crouch=3, body_dy=3, head_dy=2, head_dx=-1, hat_dy=1, eye="7", lean=2, item={"nogun": True}, l_hand=3, r_hand=3),
              Pose(heap=1), Pose(heap=2)]
        if side:
            for p in ps[:4]:
                p.l_dx = 1; p.r_dx = -1
        return ps, self.TIMING["death"]


# ============================================================ 3. 결사병 charger (24x24)
class Charger(Rig):
    ID = "charger"
    W, H = 24, 24
    LEGEND = {
        ".": None,
        "K": G[0],   # 셀아웃·장화·눈 틈
        "1": G[1],   # 갑옷 그늘·방패 뒷면
        "3": G[3],   # 브리건딘(가죽 갑옷) 본색
        "4": G[4],   # 투구 그늘·방패 본색·바지·망치 자루
        "5": G[5],   # 투구 본색·견갑
        "6": G[6],   # 방패 테·망치 머리
        "7": G[7],   # 투구 하이라이트
        "8": G[8],   # 망치 머리 하이라이트·방패 테 빛
        "B": A[5],   # 21 방패 문장 (잔)
        "S": A[3],   # 19 문장 그늘
    }
    LIGHT_SWAP = {"7": "4", "4": "7", "8": "6", "6": "8"}
    TIMING = {"idle": [240, 240, 240, 240, 240, 240], "walk": [140] * 8, "attack": [180, 60, 120, 140],
              "hurt": [70, 90], "death": [100, 120, 120, 130, 150, 220]}

    HELM_DOWN = [        # 8폭 x8..15, y1..y7
        ".775555.",
        "77555554",
        "75555544",
        "5KK5KK44",
        "75555544",
        "54444444",
        ".444444.",
    ]
    HELM_UP = [
        ".775555.",
        "77555554",
        "75555544",
        "75555544",
        "75555544",
        "54444444",
        ".444444.",
    ]
    HELM_SIDE = [        # 우향: 앞이 오른쪽, 눈 틈 앞쪽
        ".775555.",
        "77555554",
        "75555554",
        "755KKK44",
        "75555544",
        "54444444",
        ".444444.",
    ]
    # 몸통 정면 14폭 x5..18, y8..y16: 견갑(5/4) + 가죽 갑옷(3/1) + 허리띠(K) + 치맛단(3)
    TORSO_DOWN = [
        "55533333333444",
        "55513333333144",
        "54413333333144",
        "...13333333144.",
        "...1333333314..",
        "...KKKKKKKKK...",
        "...3333333331..",
        "...3133313331..",
        "...3.33133.31..",
    ]
    TORSO_UP = [
        "55533333333444",
        "55513331333144",
        "54413331333144",
        "...13331333144.",
        "...1333133314..",
        "...KKKKKKKKK...",
        "...3333133331..",
        "...3333133331..",
        "...3.33133.31..",
    ]
    TORSO_SIDE = [       # 우향 10폭 x7..16
        "5553333331",
        "5513333331",
        "5413333331",
        ".133333331",
        ".133333331",
        ".KKKKKKKKK",
        ".333333331",
        ".333313331",
        ".3.3313.31",
    ]

    def shield(self, s, x, y, w=9, h=13, swap=False, emblem=True):
        """파비스 방패: 테 6(빛 쪽 8), 본색 4, 그늘 1, 문장 B/S."""
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.px(s, xx, yy, "5")
        for xx in range(x, x + w):
            self.px(s, xx, y, "8" if not swap else "6"); self.px(s, xx, y + h - 1, "1")
        for yy in range(y, y + h):
            self.px(s, x, yy, "8" if not swap else "6"); self.px(s, x + w - 1, yy, "6" if not swap else "8")
            self.px(s, x + w - 2, yy, "1" if not swap else "4")
            self.px(s, x + 1, yy, "4" if not swap else "1")
        self.px(s, x, y, "8" if not swap else "6")
        self.px(s, x + w - 1, y + h - 1, "1")
        if emblem and w >= 7:
            cx, cy = x + w // 2, y + h // 2
            # 잔(盞) 문장: 잔 모양 (윗변 3, 몸통 2, 받침 1)
            self.px(s, cx - 1, cy - 1, "B"); self.px(s, cx, cy - 1, "B"); self.px(s, cx + 1, cy - 1, "B")
            self.px(s, cx - 1, cy, "B"); self.px(s, cx, cy, "B"); self.px(s, cx + 1, cy, "S")
            self.px(s, cx, cy + 1, "S")
            self.px(s, cx - 1, cy + 2, "S"); self.px(s, cx, cy + 2, "S"); self.px(s, cx + 1, cy + 2, "S")

    def hammer(self, s, hx, hy, dirn, length=6, swap=False):
        """큰 망치: 자루(4) hx,hy 에서 dirn 으로 length, 끝에 머리 4x3 (6, 하이라이트 8)."""
        dx, dy = dirn
        k = dict(keep=True)
        for i in range(length):
            self.px(s, hx + dx * i, hy + dy * i, "4", **k)
            self.px(s, hx + dx * i + (1 if dx == 0 else 0), hy + dy * i + (1 if dy == 0 else 0), "1", **k)
        ex, ey = hx + dx * length, hy + dy * length
        if dx == 0:   # 수직 자루: 머리는 가로 4x3
            x0, y0 = ex - 2, ey - 1 if dy < 0 else ey
            w, h = 5, 3
        else:         # 수평 자루: 머리는 세로 3x4
            x0, y0 = ex if dx > 0 else ex - 2, ey - 2
            w, h = 3, 5
        for yy in range(y0, y0 + h):
            for xx in range(x0, x0 + w):
                self.px(s, xx, yy, "6", **k)
        for xx in range(x0, x0 + w):
            self.px(s, xx, y0, "8" if not swap else "6", **k)
            self.px(s, xx, y0 + h - 1, "1", **k)
        for yy in range(y0, y0 + h):
            self.px(s, x0, yy, "8" if not swap else "4", **k)
            self.px(s, x0 + w - 1, yy, "1" if not swap else "8", **k)
        self.px(s, x0 + w - 1, y0, "6", **k); self.px(s, x0, y0 + h - 1, "1", **k)

    def draw_down(self, s, p, back=False):
        dx, dy = p.body_dx, p.body_dy
        self.legs_front(s, p, ((7, 10), (13, 16)), 17 + dy + p.crouch, "4", "5", "K1")
        torso = self.TORSO_UP if back else self.TORSO_DOWN
        if p.crouch:
            torso = torso[:2] + torso[2 + p.crouch:]
        self.blit(s, torso, 5 + dx, 8 + dy + p.crouch)
        # 오른팔 + 망치 (화면 오른쪽)
        if not p.item.get("nohammer"):
            if p.r_arm == "pos" and p.r_pos:
                self.arm(s, 18 + dx, 10 + dy + p.crouch, p.r_pos[0], p.r_pos[1], "5", "1", "5")
                self.hammer(s, p.r_pos[0], p.r_pos[1], p.item.get("hammer_dir", (0, -1)), p.item.get("hammer_len", 5))
            else:
                hx, hy = 19 + dx, 15 + dy + p.crouch + p.r_hand
                self.vline(s, 18 + dx, 11 + dy + p.crouch, hy, "1"); self.vline(s, 19 + dx, 11 + dy + p.crouch, hy, "5")
                self.px(s, hx, hy + 1, "5")
                # 어깨에 멘 망치: 자루가 손에서 위로, 머리가 어깨 위
                self.hammer(s, 20 + dx, hy, (0, -1), 9 + p.r_hand)
        # 방패 (왼팔, 화면 왼쪽 앞) — 후면에서는 등 뒤로 돌려 뒷면(1)만 삐죽
        if not p.item.get("noshield"):
            sh = p.item.get("shield", (1, 9))
            if back:
                for yy in range(9 + dy + p.crouch, 21 + dy):
                    self.px(s, 2 + dx, yy, "1"); self.px(s, 3 + dx, yy, "1"); self.px(s, 4 + dx, yy, "6")
                self.hline(s, 2 + dx, 4 + dx, 9 + dy + p.crouch, "6")
            else:
                self.shield(s, sh[0] + dx, sh[1] + dy + p.crouch)
        # 머리
        hy = 1 + dy + p.head_dy + p.crouch
        hx = 8 + dx + p.head_dx
        helm = self.HELM_UP if back else self.HELM_DOWN
        if p.eye and not back:
            helm = helm[:3] + [helm[3].replace("K", p.eye)] + helm[4:]
        self.blit(s, helm, hx, hy)

    def draw_up(self, s, p):
        self.draw_down(s, p, back=True)

    def draw_side(self, s, p, m):
        swap = m < 0
        dx, dy = p.body_dx * m, p.body_dy
        self.legs_side(s, p, m, 7, 12, 4, 17 + dy + p.crouch, "4", "5", "1", "K1")
        torso = self.TORSO_SIDE
        if p.crouch:
            torso = torso[:2] + torso[2 + p.crouch:]
        tx = 7 if m > 0 else 7
        self.blit(s, torso, tx + dx, 8 + dy + p.crouch, mirror=swap, swap=swap)
        # 망치: 좌향이면 오른손이 가까워 전부 보임, 우향이면 머리만 어깨 뒤로 삐죽
        if not p.item.get("nohammer"):
            if p.r_arm == "pos" and p.r_pos:
                sx = (9 if m > 0 else 14) + dx
                self.arm(s, sx, 10 + dy + p.crouch, p.r_pos[0], p.r_pos[1], "5" if m > 0 else "1", "1" if m > 0 else "5", "5")
                self.hammer(s, p.r_pos[0], p.r_pos[1], p.item.get("hammer_dir", (0, -1)), p.item.get("hammer_len", 5), swap=swap)
            elif m < 0:
                hx, hy = 14 + dx, 15 + dy + p.crouch + p.r_hand
                self.vline(s, 14 + dx, 11 + dy + p.crouch, hy, "5"); self.vline(s, 15 + dx, 11 + dy + p.crouch, hy, "1")
                self.px(s, 14 + dx, hy + 1, "5")
                self.hammer(s, 13 + dx, hy, (0, -1), 9 + p.r_hand, swap=True)
            else:
                # 먼 쪽: 자루 끝과 머리가 뒤쪽 어깨 위로
                self.hammer(s, 6 + dx, 10 + dy + p.crouch + p.r_hand, (0, -1), 4 + p.r_hand)
        # 방패: 몸 앞쪽. 우향 x17.., 좌향 x1..
        if not p.item.get("noshield"):
            sdx = p.item.get("shield_dx", 0)
            if m > 0:
                self.shield(s, 17 + dx + sdx, 8 + dy + p.crouch, w=6, h=14, swap=False, emblem=False)
                self.px(s, 19 + dx + sdx, 14 + dy + p.crouch, "B"); self.px(s, 20 + dx + sdx, 14 + dy + p.crouch, "B")
                self.px(s, 19 + dx + sdx, 15 + dy + p.crouch, "S"); self.px(s, 20 + dx + sdx, 15 + dy + p.crouch, "S")
            else:
                self.shield(s, 1 + dx - sdx, 8 + dy + p.crouch, w=6, h=14, swap=True, emblem=False)
                self.px(s, 3 + dx - sdx, 14 + dy + p.crouch, "B"); self.px(s, 4 + dx - sdx, 14 + dy + p.crouch, "B")
                self.px(s, 3 + dx - sdx, 15 + dy + p.crouch, "S"); self.px(s, 4 + dx - sdx, 15 + dy + p.crouch, "S")
        # 투구
        hy = 1 + dy + p.head_dy + p.crouch
        hx = 8 + dx + p.lean * m
        helm = self.HELM_SIDE
        if p.eye:
            helm = helm[:3] + [helm[3].replace("K", p.eye)] + helm[4:]
        self.blit(s, helm, hx, hy, mirror=swap, swap=swap)

    def draw_heap(self, s, p, dir_):
        st = p.heap
        oy = 0 if st == 1 else 1
        # 큰 더미 (갑옷)
        s.ellipse(4, 15 + oy, 19, 22 + oy, self.LEGEND["3"])
        s.ellipse(6, 15 + oy, 15, 18 + oy, self.LEGEND["4"], only=self.LEGEND["3"])
        s.ellipse(10, 19 + oy, 19, 22 + oy, self.LEGEND["1"], only=self.LEGEND["3"])
        # 투구 (굴러감)
        helm = {"down": (1, 16), "up": (17, 14), "right": (17, 16), "left": (1, 16)}[dir_]
        x, y = helm
        s.rect(x, y + oy, x + 5, y + 4 + oy, self.LEGEND["5"])
        s.rect(x, y + oy, x + 5, y + oy, self.LEGEND["7"])
        s.rect(x, y + 4 + oy, x + 5, y + 4 + oy, self.LEGEND["4"])
        self.hline(s, x + 1, x + 4, y + 2 + oy, "K")
        # 방패가 납작하게 떨어짐 (문장 위로)
        sx = 3 if dir_ != "left" else 12
        s.rect(sx, 10 + oy, sx + 8, 14 + oy, self.LEGEND["5"])
        s.rect(sx, 10 + oy, sx + 8, 10 + oy, self.LEGEND["8"]); s.rect(sx, 14 + oy, sx + 8, 14 + oy, self.LEGEND["1"])
        self.px(s, sx + 3, 12 + oy, "B"); self.px(s, sx + 4, 12 + oy, "B"); self.px(s, sx + 5, 12 + oy, "B")
        self.px(s, sx + 4, 13 + oy, "S")
        # 망치 (자루 + 머리) 바닥에
        self.hline(s, 14, 20, 23, "4", keep=True)
        for yy in range(21, 24):
            for xx in range(20, 23):
                self.px(s, xx, yy, "6", keep=True)
        self.px(s, 20, 21, "8", keep=True); self.px(s, 22, 23, "1", keep=True)

    def poses_idle(self, dir_):
        bob = [0, 0, 1, 1, 1, 0]
        ps = []
        for i in range(6):
            ps.append(Pose(body_dy=bob[i], head_dy=[0, 0, 0, 1, 1, 1][i] - bob[i], r_hand=[0, 0, 0, 1, 1, 0][i]))
        return ps, self.TIMING["idle"]

    def poses_walk(self, dir_):
        side = dir_ in ("left", "right")
        ps = []
        if not side:
            L = [0, 1, 2, 1, 0, 0, 0, 0]; R = [0, 0, 0, 0, 0, 1, 2, 1]
            bob = [0, 0, -1, 0, 0, 0, -1, 0]; sway = [0, 1, 1, 0, 0, -1, -1, 0]
            for i in range(8):
                ps.append(Pose(l_lift=L[i], r_lift=R[i], body_dy=bob[i], head_dx=sway[i], r_hand=[0, 0, -1, 0, 0, 0, -1, 0][i]))
        else:
            F = [2, 1, 0, -1, -2, -1, 0, 1]
            bob = [0, 0, -1, 0, 0, 0, -1, 0]
            LS = [0, 0, 0, 0, 0, 1, 1, 0]; RS = [0, 1, 1, 0, 0, 0, 0, 0]
            for i in range(8):
                ps.append(Pose(l_dx=F[i], r_dx=-F[i], l_sl=LS[i], r_sl=RS[i], body_dy=bob[i], lean=1,
                               item={"shield_dx": 1 if i in (0, 1, 7) else 0}))
        return ps, self.TIMING["walk"]

    def poses_attack(self, dir_):
        # 1 예고(웅크림·방패 내림·뒤로 젖힘) 180 · 2 돌진(앞으로 2, 방패 앞) 60 · 3 망치 내리찍기 120 · 4 복귀 140
        if dir_ == "down":
            ps = [Pose(crouch=1, body_dy=1, head_dy=1, item={"shield": (1, 11)}, r_hand=-1),
                  Pose(body_dy=2, head_dy=0, item={"shield": (1, 10)}, lean=1),
                  Pose(r_arm="pos", r_pos=(17, 19), item={"hammer_dir": (0, 1), "hammer_len": 2, "shield": (1, 10)}, body_dy=2, crouch=1),
                  Pose(body_dy=1, item={"shield": (1, 10)})]
        elif dir_ == "up":
            ps = [Pose(crouch=1, body_dy=1, head_dy=1, r_hand=-1),
                  Pose(body_dy=-2, lean=1),
                  Pose(r_arm="pos", r_pos=(18, 6), item={"hammer_dir": (0, -1), "hammer_len": 3}, body_dy=-2, crouch=1),
                  Pose(body_dy=-1)]
        elif dir_ == "right":
            ps = [Pose(crouch=1, body_dy=1, body_dx=-1, lean=-1, item={"shield_dx": -1}, r_hand=-1),
                  Pose(body_dx=2, lean=1, item={"shield_dx": 1}),
                  Pose(body_dx=2, lean=1, r_arm="pos", r_pos=(14, 13), item={"hammer_dir": (1, 0), "hammer_len": 5, "shield_dx": 0}, crouch=1, body_dy=1),
                  Pose(body_dx=1, item={"shield_dx": 0})]
        else:
            ps = [Pose(crouch=1, body_dy=1, body_dx=-1, lean=-1, item={"shield_dx": -1}, r_hand=-1),
                  Pose(body_dx=2, lean=1, item={"shield_dx": 1}),
                  Pose(body_dx=2, lean=1, r_arm="pos", r_pos=(9, 13), item={"hammer_dir": (-1, 0), "hammer_len": 5, "shield_dx": 0}, crouch=1, body_dy=1),
                  Pose(body_dx=1, item={"shield_dx": 0})]
        return ps, self.TIMING["attack"]

    def poses_death(self, dir_):
        side = dir_ in ("left", "right")
        ps = [Pose(head_dx=1, eye="4", r_hand=-1),
              Pose(body_dy=1, head_dx=-1, eye="4", lean=-1, r_hand=1),
              Pose(crouch=2, body_dy=2, head_dy=1, eye="4", lean=1, item={"noshield": True}, r_hand=2),
              Pose(crouch=3, body_dy=3, head_dy=2, head_dx=-1, eye="4", lean=2, item={"noshield": True, "nohammer": True}),
              Pose(heap=1), Pose(heap=2)]
        if side:
            for p in ps[:4]:
                p.l_dx = 1; p.r_dx = -1
        return ps, self.TIMING["death"]


# ============================================================ 내보내기 · 미리보기
ACTIONS = [("idle", True), ("walk", True), ("attack", False), ("hurt", False), ("death", False)]


def checker(w, h, sq=8):
    bg = Image.new("RGB", (w, h), (232, 232, 232))
    d = ImageDraw.Draw(bg)
    for y in range(0, h, sq):
        for x in range(0, w, sq):
            if (x // sq + y // sq) % 2:
                d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=(203, 203, 203))
    return bg


def build_enemy(rig):
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
            "pivot": {"x": W // 2, "y": rig.GROUND},
            "palette": "parts/art/palette/lopad.json (gray + floor 1 accent slots; system swaps slots 16..27 per floor)",
        }
        with open(os.path.join(OUT_ASSETS, "%s_%s.json" % (rig.ID, name)), "w", encoding="utf-8") as fp:
            json.dump(meta, fp, ensure_ascii=False, indent=1)
        for d in DIRS:
            ims = [im.resize((W * 6, H * 6), Image.NEAREST) for im in frames[d]]
            bg = []
            for im in ims:
                b = Image.new("RGBA", im.size, (62, 63, 66, 255))
                b.alpha_composite(im)
                bg.append(b.convert("P", palette=Image.ADAPTIVE))
            bg[0].save(os.path.join(HERE, "gif", "%s_%s_%s.gif" % (rig.ID, name, d)), save_all=True,
                       append_images=bg[1:], loop=0, duration=durations, disposal=2)
        all_frames[name] = (frames, durations)
    preview_enemy(rig, all_frames)
    return all_frames


def preview_enemy(rig, all_frames, scale=4):
    """전 동작 한눈에: 동작별 블록(4행 x n열). 배경 = 1층 바닥 톤(G04) 과 체커 두 가지."""
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
                cell = Image.new("RGBA", (cw, ch), (0x3e, 0x3f, 0x42, 255))
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


def preview_all(rigs, scale=6):
    """3종 idle down 1프레임 + 주인공 idle down, 발바닥 정렬. 바닥 톤 배경과 체커."""
    pl = Image.open(os.path.join(ROOT, "assets", "sprites", "player", "player_idle.png")).convert("RGBA").crop((0, 0, 16, 24))
    items = [("player", pl, 23)]
    for rig in rigs:
        ps, _ = rig.poses("idle", "down")
        items.append((rig.ID, rig.render("down", ps[0]).composite(1), rig.GROUND))
        ps, _ = rig.poses("idle", "right")
        items.append((rig.ID + " R", rig.render("right", ps[0]).composite(1), rig.GROUND))
    gap = 12
    Wd = sum(im.width * scale + gap for _, im, _ in items) + gap
    Hd = 24 * scale + 40
    out = Image.new("RGB", (Wd, Hd * 2), (40, 40, 44))
    d = ImageDraw.Draw(out)
    for k, bgc in enumerate(((0x3e, 0x3f, 0x42), None)):
        x = gap
        oy = k * Hd
        for name, im, ground in items:
            w, h = im.width * scale, im.height * scale
            cell = (Image.new("RGB", (w, 24 * scale), bgc) if bgc else checker(w, 24 * scale)).convert("RGBA")
            cell.alpha_composite(im.resize((w, h), Image.NEAREST), (0, (23 - ground) * scale))
            out.paste(cell.convert("RGB"), (x, oy + 20))
            d.text((x, oy + 4), name, fill=(235, 235, 235), font=FONT)
            x += w + gap
    out.save(os.path.join(HERE, "preview_all.png"))


def stats(rig, all_frames):
    used = set()
    semi = 0
    iso_report = []
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
                                iso_report.append((name, d, i + 1, x, y))
    gray = sorted(G.index(c) for c in used if c in G)
    amb = sorted(16 + A.index(c) for c in used if c in A)
    other = [c for c in used if c not in G and c not in A]
    print("[%s] gray %d/8 %s | accent %d/3 %s | other %s | semi %d | isolated %d" % (
        rig.ID, len(gray), gray, len(amb), amb, other, semi, len(iso_report)))
    for r in iso_report[:30]:
        print("   iso", r)


def main():
    rigs = [Dummy(), Archer(), Charger()]
    for rig in rigs:
        af = build_enemy(rig)
        stats(rig, af)
        print("built", rig.ID)
    preview_all(rigs)


if __name__ == "__main__":
    # 53라운드: 구 적 시트(assets/sprites/enemies/{dummy,archer,charger}_*)는 삭제됨 — 적은 enemies/v3(enemies_v3).
    # 실행하면 지운 구 시트를 다시 만들므로 --legacy 없이는 멈춘다.
    if "--legacy" not in sys.argv:
        sys.exit("enemies/build.py 는 구 적 3종(53라운드 삭제) 보관용입니다. 다시 만들려면 --legacy")
    main()
