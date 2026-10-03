#!/usr/bin/env python3
"""LOPAD 주인공 스프라이트 빌드 (16x24, 4방향, 6동작) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/player/build.py
입력: parts/art/palette/lopad.json (무채 16 + 1층 '잔' 호박색 램프)
산출:
  assets/sprites/player/player_<action>.png  가로 = 프레임, 세로 = 방향 (down/up/left/right)
  assets/sprites/player/player_<action>.json 프레임 크기·수·방향 순서·fps 제안
  parts/art/work/player/preview_<action>.png (8배) / preview_sheet.png (전 동작) / gif/*.gif (검수용)

설계 메모
  - 전장의 망령: 검은 케틀햇(철모) + 붕대로 감은 얼굴 + 낡은 검은 외투 + 회색 각반 + 검은 장화.
  - 강조색은 1층 호박 램프 2칸만: 눈빛(왼눈, A23) · 일기장(오른쪽 허리, A21). 나머지는 전부 무채색.
  - 윤곽선: 검정(G00) 셀아웃(inside). 빛은 화면 좌상단 고정 → 좌/우 뷰는 거울이 아니라
    형태를 뒤집은 뒤 빛/그림자 역할을 다시 배치하고, 보이는 디테일(눈빛/일기장)을 바꾼다.
  - 발바닥 기준선 y=23 (프레임 맨 아래), 피벗 (8, 23).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, ".claude", "skills", "pixel-art-studio", "scripts"))
from pixelstudio import Sprite  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from rimlight import rim_light  # noqa: E402  (parts/art/work/player/rimlight.py, 40라운드 Q1)

OUT_ASSETS = os.path.join(ROOT, "assets", "sprites", "player")
OUT_WORK = HERE
os.makedirs(OUT_ASSETS, exist_ok=True)
os.makedirs(os.path.join(OUT_WORK, "gif"), exist_ok=True)

with open(os.path.join(ROOT, "parts", "art", "palette", "lopad.json"), encoding="utf-8") as fp:
    PAL = json.load(fp)
G = PAL["gray"]
A = PAL["floors"][0]["ramp"]  # 1층 잔(호박)

W, H = 16, 24
GROUND = 23
DIRS = ["down", "up", "left", "right"]

# 문자 → 색. 주인공 색 예산 12 (무채 10 + 강조 2)
LEGEND = {
    ".": None,
    "K": G[0],   # 순흑: 셀아웃·장화·모자 그림자
    "1": G[1],   # 외투 깊은 그림자
    "h": G[1],   # 모자 (빛 역할 교환에서 제외)
    "3": G[3],   # 외투 본색
    "5": G[5],   # 외투 주름 하이라이트
    "6": G[6],   # 각반(바지) 본색
    "8": G[8],   # 각반 하이라이트
    "a": G[10],  # 붕대 그림자
    "c": G[12],  # 붕대 본색
    "e": G[14],  # 붕대 하이라이트
    "W": G[15],  # 순백 글린트
    "E": A[7],   # 눈빛 (A23 light1)
    "D": A[5],   # 일기장 (A21 base)
}
PALETTE = [v for v in LEGEND.values() if v]
# 40라운드 Q1: 림라이트 — 우·하 윤곽(빛 좌상단의 반대)의 셀아웃 G00 을 G04 로. 어두운 흙바닥(G00~G02) 대비용.
RIM = G[4]   # G03 은 바닥 G02/G03 잔점에 묻혀 G04 로 (1x 에서 읽히는 첫 단계, G05 부터는 회색 테두리로 보임)
RIM_SIDE = "rb"
# 빛 방향 역할 교환용 (좌향 뷰): 하이라이트 <-> 그림자
LIGHT_SWAP = {"5": "1", "1": "5", "e": "a", "a": "e", "8": "6"}


def blit(s, rows, ox, oy, mirror=False, swap=False, only_empty=False):
    """문자 지도 rows 를 (ox, oy) 에 찍는다. mirror: 좌우 반전, swap: 빛 역할 교환."""
    for j, row in enumerate(rows):
        n = len(row)
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            if swap:
                ch = LIGHT_SWAP.get(ch, ch)
            x = ox + (n - 1 - i if mirror else i)
            y = oy + j
            if 0 <= x < W and 0 <= y < H:
                if only_empty and s.get(x, y) is not None:
                    continue
                s.px(x, y, LEGEND[ch])


# ============================================================ 부품 지도
# 케틀햇 (정면/후면 공통): 크라운 3줄 + 챙 1줄. 챙 10폭.
HAT = [
    "..hhhhhh..",
    ".3hhhhhhh.",
    ".3hhhhhhh.",
    "3hhhhhhhhh",
]
# 얼굴 정면 8폭 x 4 (y5..y8): 챙 그늘 눈띠 → 붕대 → 붕대 → 턱
FACE_DOWN = [
    "aaEaaKaa",
    "ceeccccc",
    "cccccacc",
    ".acccca.",
]
# 뒤통수 8폭 x 4: 눈 없음, 붕대 매듭
FACE_UP = [
    "aaaaaaaa",
    "ceeccccc",
    "cccacccc",
    ".accaac.",
]
# 옆얼굴 6폭 x 4 (우향, 앞이 오른쪽). 눈은 오른쪽 끝 근처
FACE_SIDE = [
    "aaaaKa",   # 눈띠, 앞쪽 눈구멍
    "ceeccc",
    "ccccac",
    ".accca",
]
# 옆 케틀햇 (우향): 챙이 앞으로 조금 더 나간다
HAT_SIDE = [
    "..hhhhhh..",
    ".3hhhhhhh.",
    ".3hhhhhhh.",
    "3hhhhhhhhh",
]
# 정면 몸통 8폭 x 8 (y9..y16): 깃 / 가슴 / 허리띠 / 자락
TORSO_DOWN = [
    "53311133",   # y9 깃
    "15333331",   # y10  양끝 1 = 팔과 가르는 그늘
    "15333311",   # y11
    "15333311",   # y12
    "KKK6KKKK",   # y13 허리띠 + 버클
    "13333311",   # y14
    "13333311",   # y15
    "3.33.3.1",   # y16 너덜한 자락
]
TORSO_UP = [
    "53333331",   # y9 깃 뒤 (높음)
    "15331331",   # y10 등솔기 1
    "15331311",   # y11
    "15331311",   # y12
    "KKKKKKKK",   # y13 허리띠
    "13331311",   # y14
    "13331311",   # y15
    "3.31.3.1",   # y16
]
# 옆 몸통 6폭 x 8 (우향): 뒤(왼쪽)가 밝다(빛 좌상단), 앞(오른쪽) 어둡다
TORSO_SIDE = [
    "533331",
    "533331",
    "533311",
    "533311",
    "KKKKKK",
    "333311",
    "333311",
    "3.33.1",
]
# 다리 정면 7폭 (x4..x10): 왼다리 3 + 구분선 K + 오른다리 3
LEG_ROW_DOWN = "866K666"
BOOT_DOWN = ["111K111", "KKKKKKK"]
# 옆 다리: 다리 2폭 각각
LEG_ROW_SIDE = "866"
BOOT_SIDE = ["1111", "KKKK"]  # 발끝이 앞으로 1 더


# ============================================================ 그리기 루틴
class Pose:
    """프레임 하나의 자세 파라미터."""

    def __init__(self, **kw):
        self.body_dy = 0        # 상체(모자·머리·몸통·팔) y
        self.body_dx = 0
        self.head_dy = 0        # 머리 추가 y (1프레임 지연 효과)
        self.head_dx = 0
        self.hat_dx = 0
        self.hat_dy = 0         # 모자만 따로 (숨쉬기 지연)
        self.l_lift = 0         # 정면/후면: 다리 들림 (0..2)
        self.r_lift = 0
        self.l_dx = 0           # 옆: 다리 앞뒤
        self.r_dx = 0
        self.l_sl = 0           # 옆: 다리 들림 (앞다리 l / 뒷다리 r)
        self.r_sl = 0
        self.l_hand = 0         # 팔: 손 y 오프셋 (정면/후면 흔들기)
        self.r_hand = 0
        self.l_arm = "rest"     # rest | 'xy' 특수 (공격·사망): 손 좌표 지정
        self.r_arm = "rest"
        self.hand_pos = None    # 공격 팔 손 좌표 (x, y) 어깨에서 선으로 잇는다
        self.eye = "E"          # 눈 문자 (깜빡임: 'a')
        self.crouch = 0         # 몸통 압축 (대쉬·사망)
        self.tail = 0           # 외투 자락 날림 (대쉬) 방향 부호
        self.flash = False      # 피격 흰색 플래시
        self.heap = None        # 사망 더미 단계 (1, 2)
        self.lean = 0           # 옆: 상체 기울기(머리 dx)
        for k, v in kw.items():
            setattr(self, k, v)


def draw_legs_front(s, p, dir_):
    """정면/후면 다리. 발바닥 y=23. 들린 다리는 짧아지고 장화가 올라간다."""
    lifts = (p.l_lift, p.r_lift)
    cols = ((4, 6), (8, 10))
    for (x0, x1), lift in zip(cols, lifts):
        top = 15 + p.body_dy + p.crouch * 2
        boot_top = GROUND - 1 - lift
        for y in range(top, boot_top):
            if 0 <= y < H:
                for x in range(x0, x1 + 1):
                    ch = "8" if x == x0 else "6"
                    s.px(x, y, LEGEND[ch])
        for j, row in enumerate(BOOT_DOWN):
            seg = row[x0 - 4:x1 - 4 + 1]
            blit(s, [seg], x0, boot_top + j)
    # 다리 사이 구분선 (두 다리가 모두 있는 높이에만)
    for y in range(15 + p.body_dy + p.crouch * 2, GROUND + 1):
        if s.get(6, y) is not None and s.get(8, y) is not None:
            s.px(7, y, LEGEND["K"])


def draw_legs_side(s, p, facing):
    """옆 다리. 뒷다리와 앞다리가 dx 로 앞뒤 교차. facing=1 우향, -1 좌향."""
    m = facing
    cx = 7  # 몸 중심
    top = 15 + p.body_dy + p.crouch * 2
    # 뒷다리(화면상 뒤) 먼저, 앞다리 나중
    legs = [(-1, p.r_dx, p.r_sl), (1, p.l_dx, p.l_sl)]  # (앞/뒤 부호, dx, 들림)
    for side, dx, lift in legs:
        front = side * m > 0
        # 우향 기준: 뒷다리 x4..x6, 앞다리 x7..x9. 좌향은 거울 위치.
        base = (7 if front else 4) if m > 0 else (5 if front else 8)
        x0 = base + dx * m
        boot_top = GROUND - 1 - lift
        for y in range(top, boot_top):
            if 0 <= y < H:
                for i in range(3):
                    x = x0 + i
                    if 0 <= x < W:
                        # 화면 왼쪽 열이 밝다. 앞다리의 뒤쪽 열은 '1' 로 뒷다리와 가른다.
                        if (m > 0 and front and i == 0) or (m < 0 and front and i == 2):
                            ch = "1"
                        elif (i == 0 and m > 0) or (i == 0 and m < 0):
                            ch = "8"
                        else:
                            ch = "6"
                        s.px(x, y, LEGEND[ch])
        # 장화: 앞쪽으로 1 더 (발끝)
        bx0 = x0 if m > 0 else x0 - 1
        for j, row in enumerate(BOOT_SIDE):
            blit(s, [row], bx0, boot_top + j)


def draw_arm(s, sx, sy, hx, hy, hand="c", thick=True):
    """어깨(sx,sy)에서 손(hx,hy)까지 팔. 2픽셀 두께: 밝은 줄(5) + 어두운 줄(K) 로 외투 위에서도 읽힌다. 끝에 손."""
    if abs(hx - sx) > abs(hy - sy):   # 수평에 가까움: 위 밝게, 아래 어둡게
        s.line(sx, sy, hx, hy, LEGEND["5"])
        s.line(sx, sy + 1, hx, hy + 1, LEGEND["K"])
    else:                              # 수직에 가까움: 빛 쪽(왼쪽) 밝게
        d = 1 if hx >= sx else -1
        s.line(sx, sy, hx, hy, LEGEND["5"] if d < 0 else LEGEND["K"])
        s.line(sx + d, sy, hx + d, hy, LEGEND["K"] if d < 0 else LEGEND["5"])
    s.px(hx, hy, LEGEND[hand])


def draw_front(s, p, back=False, facing_up=False):
    """정면(down) / 후면(up). 그리는 순서: 다리 → 몸통 → 팔 → 머리 → 모자."""
    if p.heap:
        return draw_heap(s, p, "up" if back else "down")
    dy, dx = p.body_dy, p.body_dx
    draw_legs_front(s, p, "up" if back else "down")
    torso = TORSO_UP if back else TORSO_DOWN
    if p.crouch:
        torso = torso[:1] + torso[1 + p.crouch:]  # 가슴 줄을 줄여 압축
    blit(s, torso, 4 + dx, 9 + dy + p.crouch)
    # 일기장: 정면은 화면 오른쪽 허리(캐릭터 왼쪽? → 캐릭터의 오른쪽 허리 = 화면 왼쪽.
    #   결정: 화면 기준 오른쪽 허리에 둔다(가독성). 후면은 끈만 보인다.)
    if not back:
        s.px(10 + dx, 14 + dy, LEGEND["D"]); s.px(11 + dx, 14 + dy, LEGEND["D"])
        s.px(10 + dx, 15 + dy, LEGEND["D"]); s.px(11 + dx, 15 + dy, LEGEND["K"])
    else:
        # 등 뒤 대각선 끈 (붕대색)
        for i in range(3):
            s.px(9 + dx - i, 10 + dy + i, LEGEND["a"])
    # 팔 (어깨 y10). rest: 몸통 옆 2폭, 손 y16 (+hand 오프셋)
    arms = [("l", 2, p.l_hand, p.l_arm), ("r", 12, p.r_hand, p.r_arm)]
    for side, ax, hoff, mode in arms:
        if mode == "rest":
            x0 = ax + dx
            top = 10 + dy + p.crouch
            bottom = 15 + dy + hoff + p.crouch
            for y in range(top, bottom + 1):
                for x in (x0, x0 + 1):
                    if 0 <= x < W and 0 <= y < H:
                        s.px(x, y, LEGEND["5" if (x == x0 and side == "l" and y == top) else "3"])
            # 손
            hx = x0 if side == "l" else x0 + 1
            if 0 <= bottom + 1 < H:
                s.px(hx, bottom + 1, LEGEND["c"])
                s.px(hx + (1 if side == "l" else -1), bottom + 1, LEGEND["a"])
        elif mode == "pos":
            hx, hy = p.hand_pos
            sx = (4 if side == "l" else 11) + dx
            draw_arm(s, sx, 10 + dy + p.crouch, hx, hy)
        elif mode == "none":
            pass
    # 머리
    face = FACE_UP if back else FACE_DOWN
    if not back:
        face = [face[0].replace("E", p.eye)] + face[1:]
    hy = 5 + dy + p.head_dy + p.crouch
    blit(s, face, 4 + dx + p.head_dx, hy)
    blit(s, HAT, 3 + dx + p.head_dx + p.hat_dx, hy - 4 + p.hat_dy)


def draw_side(s, p, facing):
    """옆면. facing=+1 우향(기본 지도), -1 좌향(지도 반전 + 빛 역할 교환)."""
    if p.heap:
        return draw_heap(s, p, "right" if facing > 0 else "left")
    m = facing
    swap = m < 0
    dy, dx = p.body_dy, p.body_dx * m
    draw_legs_side(s, p, m)
    torso = TORSO_SIDE
    if p.crouch:
        torso = torso[:1] + torso[1 + p.crouch:]
    tx = 5 if m > 0 else 5
    blit(s, torso, tx + dx, 9 + dy + p.crouch, mirror=swap, swap=swap)
    # 외투 자락 날림 (대쉬): 뒤쪽으로 꼬리
    if p.tail:
        bx = (4 if m > 0 else 11)
        for i in range(p.tail):
            x = bx - i * m + dx
            y = 13 + dy + p.crouch + (i // 2)
            if 0 <= x < W:
                s.px(x, y, LEGEND["3"])
                s.px(x, y + 1, LEGEND["1"])
    # 뒷팔(먼팔)은 몸통에 가려 보이지 않음. 앞팔(가까운 팔): 몸통 앞쪽 가장자리.
    if p.r_arm == "rest":
        ax = (9 if m > 0 else 6) + dx
        top = 10 + dy + p.crouch
        bottom = 15 + dy + p.crouch + p.r_hand
        for y in range(top, bottom + 1):
            s.px(ax, y, LEGEND["3" if m > 0 else "5"])
            s.px(ax - m, y, LEGEND["1"])  # 팔과 몸통을 가르는 어두운 선
        s.px(ax, bottom + 1, LEGEND["c"])
    elif p.r_arm == "pos":
        hx, hy = p.hand_pos
        sx = (9 if m > 0 else 6) + dx
        draw_arm(s, sx, 10 + dy + p.crouch, hx, hy)
    # 일기장: 우향에서만 보인다(캐릭터 오른쪽 허리가 화면 앞). 좌향은 끈만.
    if m > 0:
        s.px(9 + dx, 14 + dy, LEGEND["D"]); s.px(10 + dx, 14 + dy, LEGEND["D"])
        s.px(9 + dx, 15 + dy, LEGEND["K"])
    else:
        s.px(7 + dx, 11 + dy, LEGEND["a"]); s.px(7 + dx, 12 + dy, LEGEND["a"])
    # 머리: 6폭, x5..x10 (우향)
    face = FACE_SIDE
    if m < 0:
        # 좌향: 보이는 눈 = 빛나는 왼눈
        face = [face[0].replace("K", p.eye)] + face[1:]
    hy = 5 + dy + p.head_dy + p.crouch
    hx = 5 + dx + p.head_dx * m + p.lean * m
    blit(s, face, hx, hy, mirror=swap, swap=swap)
    blit(s, HAT_SIDE, hx - 2 + p.hat_dx * m, hy - 4 + p.hat_dy)


def draw_heap(s, p, dir_):
    """사망 5·6 프레임: 쓰러진 더미. 머리·모자 위치는 방향별."""
    st = p.heap
    oy = 0 if st == 1 else 1
    # 외투 더미 (납작한 타원)
    s.ellipse(3, 17 + oy, 12, 22 + oy, LEGEND["3"])
    s.ellipse(5, 17 + oy, 10, 19 + oy, LEGEND["5"], only=LEGEND["3"])
    s.ellipse(7, 20 + oy, 12, 22 + oy, LEGEND["1"], only=LEGEND["3"])
    # 머리 (붕대 뭉치) 와 모자
    if dir_ == "down":
        head = (3, 19 + oy); hat = (9, 20 + oy)
    elif dir_ == "up":
        head = (5, 14 + oy); hat = (10, 17 + oy)
    elif dir_ == "right":
        head = (10, 18 + oy); hat = (1, 19 + oy)
    else:
        head = (1, 18 + oy); hat = (10, 19 + oy)
    hx, hy = head
    s.rect(hx, hy, hx + 4, hy + 3, LEGEND["c"])
    s.rect(hx, hy, hx + 4, hy, LEGEND["e"])
    s.rect(hx, hy + 3, hx + 4, hy + 3, LEGEND["a"])
    if st == 1 and dir_ != "up":
        s.px(hx + (3 if dir_ != "left" else 1), hy + 1, LEGEND["E"])   # 아직 눈빛 남음
    x, y = hat
    s.rect(x, y, x + 4, y, LEGEND["1"])      # 챙 (옆에서 본 모자: 납작)
    s.rect(x + 1, y - 1, x + 3, y - 1, LEGEND["1"])
    # 일기장: 더미 위에 떨어져 있음, 마지막까지 호박색
    s.px(7, 18 + oy, LEGEND["D"]); s.px(8, 18 + oy, LEGEND["D"])


def finish(s, p):
    """셀아웃 + 림라이트(우·하 윤곽, 플래시 프레임 제외) + 플래시."""
    s.outline(LEGEND["K"], where="inside")
    if not p.flash:
        rim_light(s._img(), RIM, side=RIM_SIDE)
    if p.flash:
        im = s._img()
        px = im.load()
        for y in range(H):
            for x in range(W):
                r, g, b, a = px[x, y]
                if a and (r, g, b) != (0, 0, 0):
                    px[x, y] = (0xeb, 0xec, 0xed, 255)
    # 안전: 흰 글린트 — 모자 챙 좌상단 1px (정지 프레임에만)
    return s


# ============================================================ 동작별 자세표
def poses_idle():
    # 숨: 상체 1px 내려앉음, 머리는 한 프레임 늦게. 4번째에서 눈빛이 흔들린다.
    ps = []
    body = [0, 0, 1, 1, 1, 0]
    head = [0, 0, 0, 1, 1, 1]
    eye = ["E", "E", "E", "a", "E", "E"]
    for i in range(6):
        ps.append(Pose(body_dy=body[i], eye=eye[i], l_hand=0, r_hand=0, hat_dy=max(0, head[i] - body[i])))
    return ps, [220, 220, 220, 180, 220, 220]


def poses_walk(side):
    ps = []
    if not side:
        L = [0, 1, 2, 1, 0, 0, 0, 0]
        R = [0, 0, 0, 0, 0, 1, 2, 1]
        bob = [0, 0, -1, 0, 0, 0, -1, 0]
        la = [1, 1, 0, -1, -1, -1, 0, 1]
        for i in range(8):
            ps.append(Pose(l_lift=L[i], r_lift=R[i], body_dy=bob[i], l_hand=la[i], r_hand=-la[i]))
    else:
        F = [2, 1, 0, -1, -2, -1, 0, 1]   # 앞다리 dx (1·5 = 접지, 3·7 = 교차)
        bob = [0, 0, -1, 0, 0, 0, -1, 0]
        LS = [0, 0, 0, 0, 0, 1, 1, 0]      # 앞다리가 앞으로 돌아올 때 들림
        RS = [0, 1, 1, 0, 0, 0, 0, 0]
        for i in range(8):
            ps.append(Pose(l_dx=F[i], r_dx=-F[i], l_sl=LS[i], r_sl=RS[i], body_dy=bob[i],
                           r_hand=-F[i] // 2, lean=1))
    return ps, [110] * 8


def poses_attack(dir_):
    # 1 예비(팔 들어올림) 100ms · 2 휘두름 50ms · 3 뻗음 유지 110ms · 4 복귀 110ms
    if dir_ == "down":
        hands = [(14, 7), (15, 12), (3, 17), None]
        ps = [Pose(r_arm="pos", hand_pos=hands[0], head_dx=-1, body_dx=-1),
              Pose(r_arm="pos", hand_pos=hands[1], body_dx=0),
              Pose(r_arm="pos", hand_pos=hands[2], body_dx=-1, head_dx=-1, body_dy=1),
              Pose(r_hand=1)]
    elif dir_ == "up":
        hands = [(1, 7), (0, 12), (12, 17), None]
        ps = [Pose(l_arm="pos", hand_pos=hands[0], head_dx=1, body_dx=1),
              Pose(l_arm="pos", hand_pos=hands[1]),
              Pose(l_arm="pos", hand_pos=hands[2], body_dx=1, head_dx=1, body_dy=1),
              Pose(l_hand=1)]
    elif dir_ == "right":
        hands = [(3, 8), (13, 9), (15, 13), None]
        ps = [Pose(r_arm="pos", hand_pos=hands[0], body_dx=-1, lean=-1),
              Pose(r_arm="pos", hand_pos=hands[1], lean=1),
              Pose(r_arm="pos", hand_pos=hands[2], body_dx=1, lean=1, body_dy=1),
              Pose(r_hand=1, lean=1)]
    else:  # left
        hands = [(12, 8), (2, 9), (0, 13), None]
        ps = [Pose(r_arm="pos", hand_pos=hands[0], body_dx=-1, lean=-1),
              Pose(r_arm="pos", hand_pos=hands[1], lean=1),
              Pose(r_arm="pos", hand_pos=hands[2], body_dx=1, lean=1, body_dy=1),
              Pose(r_hand=1, lean=1)]
    return ps, [100, 50, 110, 110]


def poses_dash(side):
    if not side:
        ps = [Pose(crouch=1, l_lift=0, r_lift=0, l_hand=-1, r_hand=-1),
              Pose(body_dy=-1, l_lift=2, r_lift=1, l_hand=-2, r_hand=-2, crouch=0),
              Pose(l_lift=0, r_lift=1, l_hand=-1, r_hand=-1)]
    else:
        ps = [Pose(crouch=1, l_dx=1, r_dx=-1, r_hand=-1, lean=0),
              Pose(body_dx=1, lean=2, l_dx=2, r_dx=-2, r_hand=-2, tail=3, body_dy=-1),
              Pose(body_dx=1, lean=1, l_dx=1, r_dx=-1, r_hand=-1, tail=1)]
    return ps, [60, 90, 90]


def poses_hurt(dir_):
    back = {"down": (0, -1), "up": (0, 1), "right": (-1, 0), "left": (1, 0)}[dir_]
    ps = [Pose(flash=True, body_dx=back[0], body_dy=back[1], head_dx=back[0], eye="a"),
          Pose(body_dx=back[0], body_dy=back[1], head_dx=-1, hat_dx=-1, eye="a", l_hand=-1, r_hand=-1)]
    if dir_ in ("left", "right"):
        ps[1].head_dx = 0; ps[1].hat_dx = 0; ps[1].lean = -1
    return ps, [70, 90]


def poses_death(dir_):
    side = dir_ in ("left", "right")
    ps = [
        Pose(head_dx=1, hat_dx=1, eye="a", l_hand=-1, r_hand=-1),                       # 1 충격
        Pose(crouch=1, body_dy=1, head_dy=0, eye="a", l_hand=1, r_hand=1, lean=1),       # 2 무릎
        Pose(crouch=2, body_dy=2, head_dy=1, head_dx=-1, hat_dx=-1, eye="a", l_hand=2, r_hand=2, lean=1),  # 3 주저앉음
        Pose(crouch=3, body_dy=3, head_dy=3, head_dx=0, hat_dx=-1, hat_dy=1, eye=".", l_hand=3, r_hand=3, lean=3),  # 4 앞으로 꺾임
        Pose(heap=1),                                                                       # 5 더미
        Pose(heap=2),                                                                       # 6 안착
    ]
    if side:
        for p in ps[:4]:
            p.l_dx = 1; p.r_dx = -1
    return ps, [90, 110, 110, 120, 140, 200]


ACTIONS = {
    "idle":   (lambda d: poses_idle(), True),
    "walk":   (lambda d: poses_walk(d in ("left", "right")), True),
    "attack": (lambda d: poses_attack(d), False),
    "dash":   (lambda d: poses_dash(d in ("left", "right")), False),
    "hurt":   (lambda d: poses_hurt(d), False),
    "death":  (lambda d: poses_death(d), False),
}


def render(dir_, p):
    s = Sprite(W, H, palette=PALETTE)
    if dir_ == "down":
        draw_front(s, p, back=False)
    elif dir_ == "up":
        draw_front(s, p, back=True)
    elif dir_ == "right":
        draw_side(s, p, +1)
    else:
        draw_side(s, p, -1)
    finish(s, p)
    return s.composite(1)


def build_action(name):
    fn, loop = ACTIONS[name]
    frames = {}
    durations = None
    for d in DIRS:
        ps, durs = fn(d)
        durations = durs
        frames[d] = [render(d, p) for p in ps]
    n = len(durations)
    sheet = Image.new("RGBA", (W * n, H * len(DIRS)), (0, 0, 0, 0))
    for r, d in enumerate(DIRS):
        for c, im in enumerate(frames[d]):
            sheet.alpha_composite(im, (c * W, r * H))
    sheet.save(os.path.join(OUT_ASSETS, "player_%s.png" % name))
    fps = round(1000.0 / (sum(durations) / n))
    meta = {
        "image": "player_%s.png" % name,
        "action": name,
        "frameWidth": W, "frameHeight": H,
        "frames": n,
        "directions": DIRS,
        "layout": "row = direction (directions order), column = frame index",
        "frameIndex": "row * frames + column",
        "fps": fps,
        "frameDurationsMs": durations,
        "loop": loop,
        "pivot": {"x": 8, "y": GROUND},
        "palette": "parts/art/palette/lopad.json (gray + floor 1 accent slots 21, 23)",
    }
    with open(os.path.join(OUT_ASSETS, "player_%s.json" % name), "w", encoding="utf-8") as fp:
        json.dump(meta, fp, ensure_ascii=False, indent=1)
    # 검수용 미리보기 (8배, 체커 배경, 라벨)
    preview_action(name, frames, durations, scale=8)
    # GIF
    for d in DIRS:
        ims = [im.resize((W * 6, H * 6), Image.NEAREST) for im in frames[d]]
        bg = []
        for im in ims:
            b = Image.new("RGBA", im.size, (124, 128, 132, 255))
            b.alpha_composite(im)
            bg.append(b.convert("P", palette=Image.ADAPTIVE))
        bg[0].save(os.path.join(OUT_WORK, "gif", "%s_%s.gif" % (name, d)), save_all=True,
                   append_images=bg[1:], loop=0, duration=durations, disposal=2)
    return frames, durations


def checker(w, h, sq=8):
    bg = Image.new("RGB", (w, h), (232, 232, 232))
    d = ImageDraw.Draw(bg)
    for y in range(0, h, sq):
        for x in range(0, w, sq):
            if (x // sq + y // sq) % 2:
                d.rectangle([x, y, x + sq - 1, y + sq - 1], fill=(203, 203, 203))
    return bg


def preview_action(name, frames, durations, scale=8, path=None):
    n = len(durations)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
    cw, ch = W * scale, H * scale
    left, top, gap = 48, 20, 4
    # 두 종류 배경: 체커 + 중간 회색(실전 바닥 가정) 을 나란히
    Wd = left + n * (cw + gap) + gap
    Hd = top + len(DIRS) * (ch + gap) + gap
    img = Image.new("RGB", (Wd * 2, Hd), (60, 60, 64))
    d = ImageDraw.Draw(img)
    for k, bgmode in enumerate(("checker", "gray")):
        ox0 = k * Wd
        d.text((ox0 + 4, 4), "%s  %s" % (name, bgmode), fill=(230, 230, 230), font=font)
        for c in range(n):
            d.text((ox0 + left + c * (cw + gap) + 2, 6), "%d %dms" % (c + 1, durations[c]), fill=(200, 200, 200), font=font)
        for r, dd in enumerate(DIRS):
            oy = top + r * (ch + gap)
            d.text((ox0 + 4, oy + ch // 2 - 6), dd, fill=(230, 230, 230), font=font)
            for c, im in enumerate(frames[dd]):
                ox = ox0 + left + c * (cw + gap)
                cell = (checker(cw, ch) if bgmode == "checker" else Image.new("RGB", (cw, ch), (112, 115, 120))).convert("RGBA")
                cell.alpha_composite(im.resize((cw, ch), Image.NEAREST))
                img.paste(cell.convert("RGB"), (ox, oy))
    img.save(path or os.path.join(OUT_WORK, "preview_%s.png" % name))


def preview_sheet(all_frames, scale=4):
    """전 동작 한눈에: 동작별 블록(4행 x n열), 중간 회색 배경."""
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
    cw, ch = W * scale, H * scale
    gap = 2
    blocks = []
    for name, (frames, durs) in all_frames.items():
        n = len(durs)
        bw = n * (cw + gap) + gap
        bh = len(DIRS) * (ch + gap) + gap + 16
        blk = Image.new("RGB", (bw, bh), (70, 72, 76))
        ImageDraw.Draw(blk).text((4, 1), "%s x%d" % (name, n), fill=(235, 235, 235), font=font)
        for r, d in enumerate(DIRS):
            for c, im in enumerate(frames[d]):
                cell = Image.new("RGBA", (cw, ch), (112, 115, 120, 255))
                cell.alpha_composite(im.resize((cw, ch), Image.NEAREST))
                blk.paste(cell.convert("RGB"), (gap + c * (cw + gap), 16 + gap + r * (ch + gap)))
        blocks.append(blk)
    # 2열 배치
    cols = 2
    rows = (len(blocks) + 1) // 2
    bw = max(b.width for b in blocks)
    bh = max(b.height for b in blocks)
    img = Image.new("RGB", (cols * (bw + 8) + 8, rows * (bh + 8) + 8), (40, 40, 44))
    for i, b in enumerate(blocks):
        r, c = divmod(i, cols)
        img.paste(b, (8 + c * (bw + 8), 8 + r * (bh + 8)))
    img.save(os.path.join(OUT_WORK, "preview_sheet.png"))


def main():
    all_frames = {}
    for name in ACTIONS:
        all_frames[name] = build_action(name)
        print("built", name)
    preview_sheet(all_frames)
    # 통계: 정면 대기 1프레임
    s = Sprite(W, H, palette=PALETTE)
    draw_front(s, poses_idle()[0][0]); finish(s, poses_idle()[0][0])
    s.stats()
    s.save_silhouette(os.path.join(OUT_WORK, "silhouette_down.png"))
    s2 = Sprite(W, H, palette=PALETTE)
    draw_side(s2, poses_idle()[0][0], +1); finish(s2, poses_idle()[0][0])
    s2.save_silhouette(os.path.join(OUT_WORK, "silhouette_right.png"))
    s2.stats()


if __name__ == "__main__":
    # 53라운드: 16×24 구 주인공 시트(assets/sprites/player/*.png|json)는 삭제됨 — 주인공은 player/v3(hero_v3).
    # 실행하면 지운 구 시트를 다시 만들므로 --legacy 없이는 멈춘다. (다른 스크립트의 import 는 그대로 동작)
    if "--legacy" not in sys.argv:
        sys.exit("player/build.py 는 구 주인공(16×24, 53라운드 삭제) 보관용입니다. 다시 만들려면 --legacy")
    main()
