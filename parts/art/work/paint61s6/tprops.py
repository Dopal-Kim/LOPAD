"""61 단계 6 (P14 §1, 계약 art §28) — 수련장 소품 7시트 `structures/v3/training_*` (트림 아틀라스, 64도트 = 1칸, pixelScale 0.5).

- training_rack_{katana,greatsword,dagger,bow}: 무기가 걸린 받침(무기 방 표지·무기 집기). 무기 모양은 looks/<무기>_base 설계를 따른 축소 도트.
  상태 idle [0] · active [1..4] 루프(집을 수 있음: 무기 색 매듭이 흔들리고 날에 빛이 지나감) · taken [5](무기를 집어 빈 받침).
  무기 색(계약 §28): 매듭·술 장식만 — 칼 서리 #8fe3ff · 대검 용암 #ff5a2a · 단검 독 #c060ff · 활 비취 #40e0a0(+ 그늘 섞음 2단).
- training_task_sign: 과제 표지판(지붕 달린 나무 판 + 종이 쪽지 3, 글자 없음 — 과제 글은 UI). idle · active(등 켜짐·쪽지 팔랑) · done(인주 도장).
- training_stamp_board: 도장 판(받침대 위 종이 판). blank · stamp 4(인장이 내려와 찍힘) · stamped(붉은 잔 인장).
- training_flag: 연습 깃발(이동·대쉬 과제 목표). idle · wave 4 루프 · reached(깃대 아래 호박 고리 켜짐).
색: lopad gray + 1층 램프 16~27 + v2 재질 SL·WD·PL + '적' 램프(인주) + 무기 색 4(매듭) — 무기 색 밖 새 색 없음.
"""
import json
import math
import os
import shutil
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
sys.path.insert(0, os.path.join(WORK, "props_v3"))
sys.path.insert(0, os.path.join(WORK, "atlas57"))

from pk import (Canvas, Rand, G, A, SL, WD, PL, X, CONTACT, R_WOOD, R_IRON, R_NSTONE, R_CLOTH, qcol, mask,  # noqa: E402
                shade_mask, face, cyl, contact, grain, glass_lantern, tohex, outline)
import gridsheet  # noqa: E402,F401

SPR = os.path.join(ROOT, "assets", "sprites")
PALJ = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))
RED = [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,) for h in PALJ["floors"][6]["ramp"]]
CLEAR = (0, 0, 0, 0)
SRC = "parts/art/work/paint61s6/tprops.py (61 단계 6 · P14 §1 수련장 소품)"
PAL_NOTE = ("parts/art/palette/lopad.json gray + 1층 램프 16~27 + v2 재질 SL·WD·PL + floors[6] '적' 램프(인주) + 무기 색 §28 매듭 3단"
            "(주 색 · 주 색×SL1 55% · 35% 섞음) — 그 밖 새 색 없음")
EMIS_BASE = [tohex(A[i]) for i in (23, 24, 25, 26, 27)] + [tohex(c) for c in X]
MS = [200, 110, 110, 110, 110, 200]


def mix(a, b, t):
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3)) + (255,)


def hx(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


WCOL = {"katana": "#8fe3ff", "greatsword": "#ff5a2a", "dagger": "#c060ff", "bow": "#40e0a0"}
WRAMP = {k: [mix(hx(v), SL[1], 0.65), mix(hx(v), SL[1], 0.45), hx(v)] for k, v in WCOL.items()}
WNAME = {"katana": "칼", "greatsword": "대검", "dagger": "단검", "bow": "활"}

R_WD = R_WOOD
R_DARKW = [SL[0], WD[0], WD[1], WD[2], WD[3], WD[4]]
R_STEEL = [SL[0], G[4], G[6], G[8], G[10], G[12], G[13]]
R_LACQ = [SL[0], G[1], G[2], G[3], G[5], G[7]]
R_PAPER = [PL[1], PL[2], PL[3], PL[4], G[12], G[13]]


# ---------------------------------------------------------------- 공용 조각
def wood_post(c, x0, y0, x1, y1, ramp=R_WD, seed=1):
    """세운 각목: 왼쪽 면 밝게 · 오른쪽 1/3 어둡게(3/4 시점 옆면) · 윗면 1~2 밝은 줄."""
    w = x1 - x0 + 1
    side = max(2, w // 3)
    face(c, x0, y0, x1 - side, y1, ramp, 0.62, grad=0.12)
    face(c, x1 - side + 1, y0, x1, y1, ramp, 0.34, grad=0.1)
    c.vline(x0, y0, y1, ramp[4])
    c.vline(x1, y0, y1, ramp[0])
    c.hline(x0, x1 - side, y0, ramp[5])
    c.hline(x1 - side + 1, x1, y0, ramp[3])
    grain(c, x0 + 1, y0 + 2, x1 - 1, y1 - 1, ramp, seed, vertical=True, density=0.09, length=(4, 10))


def beam(c, x0, y0, x1, y1, ramp=R_WD, seed=2, top=3):
    """가로 들보: 윗면(top 줄) 밝게 + 앞면."""
    face(c, x0, y0, x1, y0 + top - 1, ramp, 0.82)
    face(c, x0, y0 + top, x1, y1, ramp, 0.5, grad=0.2)
    c.hline(x0, x1, y0, ramp[5])
    c.hline(x0, x1, y1, ramp[0])
    c.vline(x0, y0, y1, ramp[3])
    c.vline(x1, y0, y1, ramp[1])
    grain(c, x0 + 1, y0 + top, x1 - 1, y1 - 1, ramp, seed, vertical=False, density=0.1, length=(5, 14))


def sled(c, cx, y0, y1, w, ramp=R_WD, seed=3):
    """앞뒤로 놓인 받침 다리(3/4 시점: 윗면 길쭉 + 앞 끝면)."""
    x0, x1 = cx - w // 2, cx + w // 2
    face(c, x0, y0, x1, y1 - 6, ramp, 0.72, grad=0.15)
    face(c, x0, y1 - 5, x1, y1, ramp, 0.42)
    c.hline(x0, x1, y1 - 6, ramp[5])
    c.vline(x0, y0, y1, ramp[3])
    c.vline(x1, y0, y1, ramp[0])
    c.hline(x0, x1, y1, ramp[0])
    c.px(cx - 1, y1 - 3, G[8])
    c.px(cx, y1 - 2, G[2])


def peg(c, x, y, ramp=R_DARKW):
    """앞으로 튀어나온 나무 못(걸이)."""
    c.rect(x - 2, y - 1, x + 2, y + 3, ramp[3])
    c.hline(x - 2, x + 2, y - 1, ramp[5])
    c.hline(x - 2, x + 2, y + 3, ramp[0])
    c.vline(x + 2, y, y + 3, ramp[1])
    c.px(x - 1, y, ramp[4])


def tassel(c, x, y, ramp3, length=22, sway=0, seed=5):
    """무기 색 매듭 + 늘어진 술(폭 5). sway(-4..4): 끝이 옆으로 흔들림."""
    d0, d1, m = ramp3
    # 매듭(마름모 고리 7×7)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if abs(dx) + abs(dy) <= 3:
                edge = abs(dx) + abs(dy) == 3
                col = d0 if edge and (dx > 0 or dy > 0) else (m if (dx < 0 and dy <= 0) else d1)
                if abs(dx) + abs(dy) <= 1:
                    col = d0
                c.px(x + dx, y + 3 + dy, col)
    for k in range(length):
        t = k / max(1, length - 1)
        ox = int(round(sway * t * t))
        yy = y + 7 + k
        c.px(x - 2 + ox, yy, d0)
        c.px(x - 1 + ox, yy, m if k % 6 else d1)
        c.px(x + ox, yy, d1 if k % 5 else m)
        c.px(x + 1 + ox, yy, d1)
        c.px(x + 2 + ox, yy, d0)
    yy = y + 7 + length
    for dx in (-2, 0, 2):
        c.px(x + dx + sway, yy, d1)
        c.px(x + dx + sway, yy + 1, d0)


def glint_line(c, pts, k, n, col_hi, col_mid):
    """날을 따라 지나가는 빛(활성 루프): pts 의 k/n 위치에 3점."""
    if not pts:
        return
    i = int(len(pts) * (k + 0.5) / n)
    for j, col in ((i - 3, col_mid), (i - 2, col_mid), (i - 1, col_hi), (i, col_hi), (i + 1, col_mid), (i + 2, col_mid)):
        if 0 <= j < len(pts):
            c.px(pts[j][0], pts[j][1], col)
            c.px(pts[j][0] + 1, pts[j][1] - 1, col_mid)


def outline_alpha(c, col):
    outline_im(c.im, col)


def outline_im(im, col):
    w, h = im.size
    p = im.load()
    add = []
    for y in range(h):
        for x in range(w):
            if p[x, y][3]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and p[xx, yy][3] == 255:
                    add.append((x, y))
                    break
    for x, y in add:
        p[x, y] = col


# ---------------------------------------------------------------- 무기(받침에 놓인 모양)
def katana_h(c, x0, y, length=100, seed=1):
    """가로로 누운 칼(은선): 왼쪽 손잡이 → 오른쪽 칼끝, 끝으로 갈수록 살짝 위로 휨. 날을 따라가는 점 목록 반환."""
    hilt = 24
    # 손잡이(검은 감은 끈 + 마름모 눈)
    for xx in range(x0, x0 + hilt):
        for dy in range(-3, 4):
            col = G[1] if abs(dy) == 3 else (G[4] if (xx + dy) % 4 == 0 else G[2])
            c.px(xx, y + dy, col)
        if (xx - x0) % 4 == 2:
            c.px(xx, y, A[20])
    c.vline(x0 - 1, y - 2, y + 2, A[21])          # 카시라(호박 금)
    c.vline(x0 - 2, y - 1, y + 1, A[19])
    # 코등이(둥근 검은 쇠)
    tx = x0 + hilt
    for dy in range(-5, 6):
        c.px(tx, y + dy, G[3] if dy < 0 else G[2])
        c.px(tx + 1, y + dy, G[1])
    c.px(tx, y - 5, G[6])
    c.rect(tx + 2, y - 2, tx + 4, y + 2, A[21])  # 하바키
    c.px(tx + 2, y - 2, A[24])
    # 날
    pts = []
    bl = length - hilt - 5
    for k in range(bl):
        t = k / max(1, bl - 1)
        xx = tx + 5 + k
        yc = y - int(round(4 * t * t))
        th = 5 if t < 0.8 else (4 if t < 0.9 else (3 if t < 0.97 else 1))
        c.px(xx, yc - th + 1, G[4])                 # 등
        for j in range(-th + 2, 1):
            c.px(xx, yc + j, G[9] if j < -th // 2 else (G[10] if (k // 6) % 2 else G[11]))
        c.px(xx, yc + 1, G[14] if t < 0.97 else G[12])    # 날선(백광)
        if (k % 9) in (3, 4) and th >= 3:
            c.px(xx, yc - 1, G[12])                 # 하몬 물결
        pts.append((xx, yc + 1))
    return pts


def saya_h(c, x0, y, length=96):
    for xx in range(x0, x0 + length):
        t = (xx - x0) / length
        yc = y - int(round(3 * t * t))
        c.px(xx, yc - 2, G[3])
        c.px(xx, yc - 1, G[5] if (xx // 7) % 3 else G[7])     # 윤기 줄
        c.px(xx, yc, G[2])
        c.px(xx, yc + 1, G[1])
        c.px(xx, yc + 2, SL[0])
    c.rect(x0, y - 2, x0 + 2, y + 2, A[21])                     # 입구테
    xe = x0 + length
    c.rect(xe - 3, y - 5, xe, y - 1, A[20])                     # 끝 장식
    for k in range(10):                                         # 짙은 호박 끈(늘어짐)
        c.px(x0 + 8 + k // 2, y + 3 + k, A[18] if k % 3 else A[17])


def greatsword_v(c, cx, y_tip, y_pommel):
    """세워 꽂힌 대검: 칼끝이 아래(받침 안), 손잡이 위. 날 가운데 홈 + 녹 자국. 날 점 목록 반환."""
    guard_y = y_pommel + 30
    pts = []
    for y in range(guard_y + 3, y_tip + 1):
        t = (y - guard_y) / max(1, y_tip - guard_y)
        hw = 7 if t < 0.85 else max(1, int(7 * (1 - t) / 0.15))
        for x in range(cx - hw, cx + hw + 1):
            u = (x - cx) / max(1, hw)
            if u < -0.6:
                col = G[10]
            elif u < 0:
                col = G[8]
            elif abs(u) < 0.15:
                col = G[4]                 # 가운데 홈
            elif u < 0.7:
                col = G[6]
            else:
                col = G[4]
            c.px(x, y, col)
        c.px(cx - hw, y, G[12])
        c.px(cx + hw, y, G[2])
        pts.append((cx - hw, y))
    # 녹 자국
    r = Rand(7)
    for _ in range(9):
        x, y = cx + r.i(-5, 5), r.i(guard_y + 8, y_tip - 10)
        c.px(x, y, A[18])
        c.px(x + 1, y, A[17])
    # 코등이(가로대)
    c.rect(cx - 20, guard_y, cx + 20, guard_y + 4, G[4])
    c.hline(cx - 20, cx + 20, guard_y, G[8])
    c.hline(cx - 20, cx + 20, guard_y + 4, G[2])
    c.rect(cx - 22, guard_y - 1, cx - 19, guard_y + 5, G[5])
    c.rect(cx + 19, guard_y - 1, cx + 22, guard_y + 5, G[3])
    # 손잡이(가죽 감음)
    for y in range(y_pommel + 6, guard_y):
        for x in range(cx - 3, cx + 4):
            c.px(x, y, WD[3] if (y + (x > cx)) % 4 else WD[1])
        c.px(cx - 3, y, WD[4])
        c.px(cx + 3, y, WD[0])
    # 폼멜
    for y in range(y_pommel, y_pommel + 7):
        for x in range(cx - 5, cx + 6):
            if (x - cx) ** 2 / 30 + (y - y_pommel - 3) ** 2 / 12 <= 1:
                c.px(x, y, G[7] if x < cx and y < y_pommel + 3 else G[4])
    return pts


def claw_dagger(c, x, y, ang, scale=1.0):
    """'재 발톱' 단검: 둥근 쇠 폼멜 + 짧은 손잡이 + 굽은 넓은 날(호박 날선). 날 끝이 (x,y)에 박힘, ang = 손잡이 쪽 방향(라디안)."""
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    L = int(34 * scale)
    pts = []
    for k in range(L):
        t = k / L
        bx, by = x + ca * k, y + sa * k
        if t < 0.62:                                    # 날(박힌 끝 → 밑동으로 넓어짐, 한쪽으로 굽음)
            hw = 1 + 4.5 * (t / 0.62) ** 0.8
            bend = 3.0 * math.sin(t / 0.62 * math.pi) * scale
            for j in range(-int(hw), int(hw) + 1):
                px_, py_ = int(round(bx + nx * (j + bend))), int(round(by + ny * (j + bend)))
                if j == -int(hw):
                    col = A[22]                         # 호박 날선(바깥 굽은 쪽)
                elif j == -int(hw) + 1:
                    col = G[10]
                elif j >= int(hw) - 1:
                    col = G[3]
                else:
                    col = G[7] if j < 0 else G[5]
                c.px(px_, py_, col)
            pts.append((int(round(bx + nx * (-int(hw) + bend))), int(round(by + ny * (-int(hw) + bend)))))
        elif t < 0.66:                                  # 밑동 쇠
            for j in range(-4, 5):
                c.px(int(round(bx + nx * j)), int(round(by + ny * j)), G[4] if j < 0 else G[2])
        else:                                           # 손잡이(감은 끈)
            for j in range(-2, 3):
                c.px(int(round(bx + nx * j)), int(round(by + ny * j)), (G[2] if (k % 3) else G[4]) if abs(j) < 2 else G[1])
    ex, ey = x + ca * L, y + sa * L                     # 둥근 폼멜
    for j in range(-3, 4):
        for i in range(-3, 4):
            if i * i + j * j <= 10:
                c.px(int(ex + i), int(ey + j), G[6] if (i + j) < 0 else G[3])
    return pts


def bow_v(c, cx, y0, y1, strung=True):
    """세워 걸린 짧은 반곡궁: 어두운 몸 + 호박 징, 줄은 가는 회백. 몸 점 목록 반환."""
    H = y1 - y0
    pts = []
    for y in range(y0, y1 + 1):
        t = (y - y0) / H
        u = 2 * t - 1
        off = 10 * (1 - u * u) - 3 * (abs(u) > 0.8) * (abs(u) - 0.8) / 0.2   # 끝이 살짝 되휨
        x = int(round(cx + off))
        th = 3 if abs(u) < 0.3 else 2
        for k in range(th):
            c.px(x + k, y, [WD[1], WD[2], WD[3]][min(2, k)] if abs(u) > 0.25 else [G[2], G[4], G[3]][min(2, k)])
        c.px(x - 1, y, SL[0])
        if (y - y0) % 11 == 5 and abs(u) < 0.85:
            c.px(x + 1, y, A[21])
        pts.append((x + 1, y))
    if strung:
        c.vline(cx - 2, y0 + 2, y1 - 2, G[10])
        c.px(cx - 2, y0 + 1, G[6])
        c.px(cx - 2, y1 - 1, G[6])
    # 손잡이 감음
    ym = (y0 + y1) // 2
    c.rect(cx + 9, ym - 5, cx + 12, ym + 5, WD[2])
    c.hline(cx + 9, cx + 12, ym - 5, A[20])
    c.hline(cx + 9, cx + 12, ym + 5, A[19])
    return pts


def quiver(c, x0, y0, h=46, seed=3):
    """기대 세운 화살통 + 깃 화살 5."""
    r = Rand(seed)
    for k in range(5):
        ax = x0 + 2 + k * 3
        top = y0 - 10 - r.i(0, 6)
        c.vline(ax, top + 4, y0, WD[4])
        c.rect(ax - 1, top, ax + 1, top + 4, G[11] if k % 2 else PL[4])
        c.px(ax, top, G[13])
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + 17):
            u = (x - x0) / 16
            col = WD[3] if u < 0.35 else (WD[2] if u < 0.75 else WD[1])
            c.px(x, y, col)
        c.px(x0, y, WD[4])
        c.px(x0 + 16, y, WD[0])
    for yy in (y0 + 4, y0 + h - 8):
        c.hline(x0, x0 + 16, yy, A[19])
        c.hline(x0, x0 + 16, yy + 1, A[17])
    c.hline(x0, x0 + 16, y0 + h - 1, WD[0])


# ---------------------------------------------------------------- 시트별 그리기
def frame_canvas(fw, fh):
    return Canvas(fw, fh)


def rack_katana(fi, wcol):
    FW, FH = 176, 192
    c = frame_canvas(FW, FH)
    contact(c, 88, 172, 70, 14)
    sled(c, 44, 140, 178, 14, seed=1)
    sled(c, 132, 140, 178, 14, seed=2)
    wood_post(c, 38, 58, 49, 162, seed=3)
    wood_post(c, 126, 58, 137, 162, seed=4)
    # 윗 들보(끝이 살짝 들린)
    beam(c, 22, 50, 153, 59, seed=5)
    for k in range(4):
        c.px(22 - k, 50 - k // 2, R_WD[4])
        c.px(153 + k, 50 - k // 2, R_WD[2])
    beam(c, 40, 132, 136, 137, seed=6, top=2)       # 아래 가로대
    for x in (54, 121):
        peg(c, x, 86)
        peg(c, x, 112)
    pts = []
    if fi != 5:
        pts = katana_h(c, 36, 84, length=110)
    saya_h(c, 38, 110, length=100)
    sway = [0, -2, 1, 3, 1, 0][fi]
    tassel(c, 150, 58, wcol, length=24, sway=sway)
    if 1 <= fi <= 4 and pts:
        glint_line(c, pts, fi - 1, 4, G[15], wcol[2])
    return c.im


def rack_greatsword(fi, wcol):
    FW, FH = 128, 208
    c = frame_canvas(FW, FH)
    contact(c, 64, 188, 46, 12)
    # 받침 통나무 덩이(쇠테 두름)
    cyl(c, 64, 158, 186, 30, R_WD, ry=10, staves=0, hoops=((166, 3),), hoop_ramp=R_IRON, seed=3)
    # 갈라진 홈(대검 꽂힌 자리 / 빈 자리)
    c.rect(58, 154, 70, 158, SL[0])
    c.hline(58, 70, 159, R_WD[1])
    pts = []
    if fi != 5:
        pts = greatsword_v(c, 64, 158, 22)
    else:
        for k in range(5):
            c.px(57 + k * 3, 152 - (k % 2), R_WD[2])
    # 매듭: 코등이에 감은 용암 색 끈(빈 받침이면 통 쇠테에 걸림)
    sway = [0, -2, 1, 3, 1, 0][fi]
    if fi != 5:
        tassel(c, 86, 54, wcol, length=26, sway=sway)
    else:
        tassel(c, 90, 162, wcol, length=12, sway=0)
    if 1 <= fi <= 4 and pts:
        glint_line(c, pts[::-1], fi - 1, 4, G[15], wcol[2])
    return c.im


def rack_dagger(fi, wcol):
    FW, FH = 128, 176
    c = frame_canvas(FW, FH)
    contact(c, 64, 158, 44, 12)
    # 굵은 말뚝(나무 기둥) — 위가 잘린 그루터기
    cyl(c, 64, 70, 152, 22, R_WD, ry=9, staves=5, hoops=((90, 2), (138, 2)), hoop_ramp=R_IRON, seed=4)
    # 칼자국
    r = Rand(9)
    for _ in range(14):
        x, y = 50 + r.i(0, 26), 96 + r.i(0, 36)
        c.px(x, y, R_WD[0])
        c.px(x + 1, y + 1, R_WD[1])
    pts = []
    if fi != 5:
        pts += claw_dagger(c, 52, 104, math.radians(200), 0.95)
        pts += claw_dagger(c, 76, 118, math.radians(-25), 0.9)
        pts += claw_dagger(c, 62, 76, math.radians(-100), 0.85)
    else:
        for (x, y) in ((52, 104), (76, 118), (62, 76)):
            c.rect(x - 1, y - 1, x + 1, y + 1, SL[0])
    sway = [0, -2, 1, 3, 1, 0][fi]
    tassel(c, 82, 66, wcol, length=20, sway=sway)
    if 1 <= fi <= 4 and pts:
        glint_line(c, pts, fi - 1, 4, G[15], wcol[2])
    return c.im


def rack_bow(fi, wcol):
    FW, FH = 128, 208
    c = frame_canvas(FW, FH)
    contact(c, 64, 190, 46, 12)
    sled(c, 52, 166, 194, 40, seed=7)
    wood_post(c, 46, 30, 57, 180, seed=8)
    beam(c, 34, 24, 70, 31, seed=9)
    peg(c, 64, 46)
    peg(c, 64, 150)
    pts = []
    if fi != 5:
        pts = bow_v(c, 66, 42, 156)
    quiver(c, 82, 150, h=40)
    sway = [0, -2, 1, 3, 1, 0][fi]
    tassel(c, 38, 31, wcol, length=22, sway=sway)
    if 1 <= fi <= 4 and pts:
        glint_line(c, pts, fi - 1, 4, G[13], wcol[2])
    return c.im


def task_sign(fi):
    FW, FH = 176, 192
    c = frame_canvas(FW, FH)
    contact(c, 88, 174, 66, 12)
    wood_post(c, 34, 66, 43, 176, seed=11)
    wood_post(c, 132, 66, 141, 176, seed=12)
    # 판(앞면) + 테
    face(c, 28, 70, 148, 142, R_WD, 0.52, grad=0.25)
    grain(c, 30, 72, 146, 140, R_WD, 13, vertical=False, density=0.12, length=(6, 16))
    for yy in (94, 118):
        c.hline(28, 148, yy, R_WD[1])
        c.hline(28, 148, yy + 1, R_WD[3])
    c.rect(26, 68, 150, 70, R_WD[4]); c.hline(26, 150, 68, R_WD[5])
    c.rect(26, 141, 150, 143, R_WD[1]); c.hline(26, 150, 143, R_WD[0])
    c.vline(26, 68, 143, R_WD[3]); c.vline(150, 68, 143, R_WD[0])
    # 작은 지붕(널판 두 장)
    for k in range(10):
        c.hline(18 + k, 158 - k, 58 + k // 2 * 0 + (10 - k) // 3 + 50 - 50, R_WD[2] if k > 6 else R_WD[4])
    face(c, 16, 54, 160, 63, R_DARKW, 0.55, grad=0.3)
    c.hline(16, 160, 54, R_DARKW[5])
    c.hline(16, 160, 63, SL[0])
    for x in range(20, 158, 12):
        c.vline(x, 55, 62, R_DARKW[2])
    # 종이 쪽지 3(글자 없음 — 흐린 줄만) + 못
    flutter = [0, 1, -1, 1, 0, 0][fi]
    for i, (x0, y0) in enumerate(((40, 78), (78, 76), (114, 80))):
        w, h = 28, 52
        for y in range(y0, y0 + h):
            dx = flutter if (y > y0 + h - 8 and i == 1) else 0
            for x in range(x0, x0 + w):
                col = R_PAPER[3] if x < x0 + w - 3 else R_PAPER[1]
                if y == y0 + h - 1:
                    col = R_PAPER[0]
                c.px(x + dx, y, col)
        for k in range(4):
            yy = y0 + 10 + k * 9
            c.hline(x0 + 4, x0 + w - 7 - (k % 2) * 5, yy, R_PAPER[1])
            c.rect(x0 + 4, yy - 2, x0 + 6, yy, R_PAPER[0]) if True else None   # 체크 칸
        c.px(x0 + w // 2, y0 + 2, G[8])
        c.px(x0 + w // 2 + 1, y0 + 3, G[2])
    # 걸린 등(오른쪽 기둥) — 켜짐은 active
    if 1 <= fi <= 4:
        glass_lantern(c, 154, 76, 12, 20)
        c.px(154, 74, R_IRON[3])
    else:
        c.rect(149, 80, 159, 94, R_IRON[1]); c.vline(154, 80, 94, R_IRON[3]); c.hline(149, 159, 80, R_IRON[4])
        c.rect(150, 83, 158, 92, G[3])
    # done: 판 가운데 붉은 인주 잔 도장
    if fi == 5:
        seal(c, 88, 104, 12)
    return c.im


def seal(c, cx, cy, s, a=1.0):
    """붉은 인주 네모 인장 + 가운데 잔 무늬(글자 없음)."""
    for y in range(cy - s, cy + s + 1):
        for x in range(cx - s, cx + s + 1):
            edge = abs(x - cx) >= s - 1 or abs(y - cy) >= s - 1
            # 잔 모양(비운 자리)
            u, v = (x - cx) / s, (y - cy) / s
            cup = (abs(u) < 0.55 - 0.25 * max(0, v + 0.5) and -0.6 < v < 0.0) or (abs(u) < 0.12 and 0.0 <= v < 0.45) or \
                  (abs(u) < 0.42 and 0.45 <= v < 0.6)
            if edge:
                c.px(x, y, RED[7] if (x + y) % 7 else RED[5])
            elif not cup:
                c.px(x, y, RED[6] if (x * 3 + y) % 11 else RED[5])
            else:
                pass


def stamp_board(fi):
    FW, FH = 112, 176
    c = frame_canvas(FW, FH)
    contact(c, 56, 160, 36, 10)
    wood_post(c, 50, 92, 61, 162, seed=21)
    sled(c, 56, 148, 166, 40, seed=22)
    # 비스듬한 판(독서대처럼) — 윗면이 보이는 종이 판
    pts = [(18, 54), (94, 54), (100, 100), (12, 100)]
    m, d = mask(FW, FH)
    d.polygon(pts, fill=255)
    shade_mask(c, m, R_WD, base=0.5, gain=0.4, soft=2, tilt=0.2)
    pm, pd = mask(FW, FH)
    pd.polygon([(24, 58), (88, 58), (92, 95), (20, 95)], fill=255)
    shade_mask(c, pm, R_PAPER, base=0.62, gain=0.3, soft=2, tilt=0.15, rim=False)
    for k in range(3):
        y = 66 + k * 8
        c.hline(30, 82 - k * 6, y, R_PAPER[1])
    c.hline(12, 100, 101, R_WD[0])
    c.hline(12, 100, 102, R_WD[1])
    # 인장(손잡이 달린 도장) — 내려와 찍힘
    sy = {0: None, 1: 46, 2: 70, 3: 86, 4: 62, 5: None}[fi]
    if fi in (3, 4, 5):
        seal(c, 56, 80, 9)
    if fi == 3:                                  # 찍히는 순간 번쩍(인주 밝은 칸 + 백열 점)
        for (dx, dy) in ((-13, 0), (13, 0), (0, -12), (0, 12), (-10, -9), (10, -9), (-10, 9), (10, 9)):
            c.px(56 + dx, 80 + dy, RED[9])
        c.px(56, 66, X[1])
    if sy is not None:
        # 도장 몸(나무 손잡이 + 붉은 바닥)
        c.rect(50, sy - 22, 62, sy - 6, R_WD[3]); c.vline(50, sy - 22, sy - 6, R_WD[4]); c.vline(62, sy - 22, sy - 6, R_WD[1])
        for y in range(sy - 30, sy - 21):
            for x in range(52, 61):
                if (x - 56) ** 2 / 20 + (y - sy + 26) ** 2 / 16 <= 1:
                    c.px(x, y, R_WD[4] if x < 56 else R_WD[2])
        c.rect(47, sy - 6, 65, sy, RED[4]); c.hline(47, 65, sy - 6, RED[6]); c.hline(47, 65, sy, RED[2])
    return c.im


def flag(fi):
    FW, FH = 112, 224
    c = frame_canvas(FW, FH)
    contact(c, 56, 208, 24, 8)
    # 돌 받침 + 깃대
    cyl(c, 56, 196, 206, 12, R_NSTONE, ry=5, seed=31)
    for y in range(28, 200):
        c.px(55, y, R_WD[4])
        c.px(56, y, R_WD[3])
        c.px(57, y, R_WD[1])
    c.rect(54, 24, 58, 28, A[21]); c.px(54, 24, A[24])
    # 깃발(바랜 천 + 호박 줄 하나), 펄럭임
    ph = [0.0, 0.0, 1.3, 2.6, 3.9, 0.0][fi]
    amp = 0 if fi in (0, 5) else 3
    for x in range(58, 100):
        t = (x - 58) / 42
        wave = int(round(amp * t * math.sin(ph + t * 5.0))) if amp else int(round(2 * t))
        top = 32 + wave + int(6 * t)
        bot = 70 + wave - int(10 * t)
        for y in range(top, bot + 1):
            v = (y - top) / max(1, bot - top)
            shade = 0.62 - 0.3 * t + (0.12 if amp and math.sin(ph + t * 5.0) > 0.3 else 0)
            col = qcol(R_CLOTH, shade - 0.15 * v, x, y)
            if abs(v - 0.45) < 0.09:
                col = A[19] if shade > 0.45 else A[18]
            c.px(x, y, col)
        c.px(x, top, R_CLOTH[5] if t < 0.7 else R_CLOTH[3])
        c.px(x, bot, R_CLOTH[1])
    # 깃대 아래 고리(reached 에 켜짐)
    ring = [A[19], A[18]] if fi != 5 else [A[24], A[25]]
    for k in range(16):
        a = 2 * math.pi * k / 16
        x, y = 56 + int(round(math.cos(a) * 18)), 202 + int(round(math.sin(a) * 6))
        if c.get(x, y)[3] == 0 or c.get(x, y)[3] < 255:
            c.px(x, y, ring[k % 2])
    return c.im


# ---------------------------------------------------------------- 시트 정의
def rack_meta(weapon, fw, fh, pivot, footprint, light_off, mark):
    m = {
        "id": f"training_rack_{weapon}", "kind": "training", "name": f"{WNAME[weapon]} 걸이(임시)",
        "usage": f"수련장 {WNAME[weapon]}의 방 — 받침에 걸린 {WNAME[weapon]}. 다가가 E 로 집으면 taken(빈 받침)",
        "footprint": footprint, "solid": True, "depth": "y", "pivot": {"x": pivot[0], "y": pivot[1]},
        "states": {"idle": [0], "active": [1, 2, 3, 4], "taken": [5]},
        "stateLoop": {"idle": False, "active": True, "taken": False},
        "stateFlow": "idle(멀리) → 주인공이 가까우면 active(무기 색 매듭이 흔들리고 날에 빛이 지나감, 루프) → E 로 집으면 taken(빈 받침, 매듭만 남음)",
        "interact": "E", "interactMark": mark,
        "weapon": weapon, "weaponColor": WCOL[weapon],
        "weaponColorRamp": [tohex(cc) for cc in WRAMP[weapon]],
        "weaponColorNote": "계약 art §28 무기 색표의 주 색(매듭·술·활성 빛 끝점만) — 무기 본체(강철·나무)는 기존 무기 그림 색",
        "light": {"color": WCOL[weapon], "radius": 90, "intensity": 0.35, "offset": light_off},
        "lightByState": {"idle": None, "active": "켜짐", "taken": None},
        "emissiveColors": EMIS_BASE + [WCOL[weapon]],
        "occludeAbove": 40,
    }
    return m


SHEETS = {
    "training_rack_katana": dict(fn=lambda i: rack_katana(i, WRAMP["katana"]), fw=176, fh=192,
                                 meta=lambda: rack_meta("katana", 176, 192, (88, 184), [2, 1], {"x": 150, "y": 70}, {"x": 88, "y": 40})),
    "training_rack_greatsword": dict(fn=lambda i: rack_greatsword(i, WRAMP["greatsword"]), fw=128, fh=208,
                                     meta=lambda: rack_meta("greatsword", 128, 208, (64, 196), [1, 1], {"x": 86, "y": 66}, {"x": 64, "y": 12})),
    "training_rack_dagger": dict(fn=lambda i: rack_dagger(i, WRAMP["dagger"]), fw=128, fh=176,
                                 meta=lambda: rack_meta("dagger", 128, 176, (64, 164), [1, 1], {"x": 82, "y": 76}, {"x": 64, "y": 50})),
    "training_rack_bow": dict(fn=lambda i: rack_bow(i, WRAMP["bow"]), fw=128, fh=208,
                              meta=lambda: rack_meta("bow", 128, 208, (64, 196), [1, 1], {"x": 40, "y": 42}, {"x": 64, "y": 14})),
    "training_task_sign": dict(fn=task_sign, fw=176, fh=192, meta=lambda: {
        "id": "training_task_sign", "kind": "training", "name": "과제 표지판(임시)",
        "usage": "수련장 방마다 1 — 그 방 과제 목록 자리(글은 UI 오른쪽 목록이 그림). 지붕 달린 나무 판 + 종이 쪽지 3(글자 없음, 체크 칸 모양만)",
        "footprint": [2, 1], "solid": True, "depth": "y", "pivot": {"x": 88, "y": 184},
        "states": {"idle": [0], "active": [1, 2, 3, 4], "done": [5]},
        "stateLoop": {"idle": False, "active": True, "done": False},
        "stateFlow": "idle(등 꺼짐) → 방에 남은 과제가 있으면 active(등 켜짐·쪽지 팔랑, 루프) → 방 과제를 다 하면 done(판 가운데 붉은 잔 도장, 등 꺼짐)",
        "interact": "E_optional", "interactMark": {"x": 88, "y": 44},
        "light": {"color": "#e8b858", "radius": 140, "intensity": 0.6, "flicker": {"amp": 0.15, "hz": 5}, "offset": {"x": 154, "y": 88}},
        "lightByState": {"idle": None, "active": "켜짐", "done": None},
        "emissiveColors": EMIS_BASE, "occludeAbove": 50}),
    "training_stamp_board": dict(fn=stamp_board, fw=112, fh=176, meta=lambda: {
        "id": "training_stamp_board", "kind": "training", "name": "도장 판(임시)",
        "usage": "방 과제를 다 하면 도장이 찍히는 받침대(방 출구 옆 권장). 붉은 인주 잔 인장(글자 없음)",
        "footprint": [1, 1], "solid": True, "depth": "y", "pivot": {"x": 56, "y": 168},
        "states": {"blank": [0], "stamp": [1, 2, 3, 4], "stamped": [5]},
        "stateLoop": {"blank": False, "stamp": False, "stamped": False},
        "stateNext": {"stamp": "stamped"},
        "stampFrame": 3,
        "stateFlow": "blank → (방 과제 완료 순간) stamp 1회: 1 도장이 들림 · 2 내려옴 · 3 찍힘(번쩍 — 소리 training_stamp·작은 흔들림 자리) · 4 들림 → stamped 유지",
        "frameDurationsNote": "stamp 구간 합 440ms",
        "light": {"color": "#d65457", "radius": 70, "intensity": 0.5, "offset": {"x": 56, "y": 80}},
        "lightByFrame": {"3": "켜짐(한 칸)"},
        "emissiveColors": EMIS_BASE + [tohex(RED[9])], "occludeAbove": 40}),
    "training_flag": dict(fn=flag, fw=112, fh=224, meta=lambda: {
        "id": "training_flag", "kind": "training", "name": "연습 깃발(임시)",
        "usage": "이동·대쉬·회피 과제의 목표 지점(걸음과 숨 방). 깃대 아래 호박 고리가 도착 판정 자리",
        "footprint": [1, 1], "solid": False, "depth": "y", "pivot": {"x": 56, "y": 208},
        "states": {"idle": [0], "wave": [1, 2, 3, 4], "reached": [5]},
        "stateLoop": {"idle": False, "wave": True, "reached": False},
        "stateFlow": "idle(바람 없음) → 목표로 켜지면 wave(펄럭임 루프) → 주인공이 고리 안에 닿으면 reached(고리 호박 빛, 깃발 멈춤)",
        "ringAnchor": {"x": 56, "y": 202, "rx": 18, "ry": 6, "note": "도착 고리(도트) — 판정 반경은 시스템이 정함"},
        "light": {"color": "#e2a33c", "radius": 80, "intensity": 0.5, "offset": {"x": 56, "y": 202}},
        "lightByState": {"idle": None, "wave": None, "reached": "켜짐"},
        "emissiveColors": EMIS_BASE, "occludeAbove": 120}),
}


def common_meta(name, fw, fh, extra):
    m = {"image": f"{name}.png", "action": name, "frameWidth": fw, "frameHeight": fh, "frames": 6,
         "directions": ["any"], "layout": "row = direction/kind (directions·rowsAre 순서), column = frame index",
         "frameIndex": "row * columns + column (§19 아틀라스 키)"}
    m.update(extra)
    m.update({"frameDurationsMs": MS, "loop": False, "pixelScale": 0.5, "floor": "training", "paletteSwap": False,
              "version": "v3-r61s6",
              "pivotNote": "pivot = 발자국 아래 변 가운데(바닥 접점). 도트 단위 — 시스템은 pixelScale 0.5 로 환산",
              "palette": PAL_NOTE, "source": SRC})
    return m


def check(frames, name):
    """반투명은 접지 그림자 색만 · 가장자리 잘림 0."""
    cols = set()
    for i, im in enumerate(frames):
        w, h = im.size
        p = im.load()
        for y in range(h):
            for x in range(w):
                cc = p[x, y]
                if not cc[3]:
                    continue
                if cc[3] < 255:
                    assert cc[:3] == CONTACT[:3], (name, i, "semi", x, y, cc)
                    continue
                cols.add(cc[:3])
                assert x not in (0, w - 1) and y not in (0, h - 1), (name, i, "edge", x, y)
    return cols


def allowed():
    s = {c[:3] for c in G} | {c[:3] for c in A.values()} | {c[:3] for c in SL} | {c[:3] for c in WD} | {c[:3] for c in PL} | \
        {c[:3] for c in RED} | {X[0][:3], X[1][:3]} | {c[:3] for r in WRAMP.values() for c in r}
    return s


def to_atlas(written):
    import importlib.util
    spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(WORK, "atlas57", "build.py"))
    ab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ab)
    tmp_root = os.path.join(HERE, "_atlas_tmp_%d" % os.getpid())
    try:
        for name in written:
            src_dir = os.path.join(SPR, "structures", "v3")
            jp, pp = os.path.join(src_dir, name + ".json"), os.path.join(src_dir, name + ".png")
            out_dir = os.path.join(tmp_root, "structures", "v3")
            os.makedirs(out_dir, exist_ok=True)
            res = ab.convert_sheet(pp, jp, out_dir, 2, 4096, True)
            ab.apply_in_place(res, out_dir, src_dir, pp, jp, 4096)
            print("atlas", name, res["srcSize"], [(w, h) for _, w, h in res["pages"]])
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


FRAMES = {}


def build(dry=False, only=None):
    ok = allowed()
    written = []
    stats = {}
    for name, spec in SHEETS.items():
        if only and name not in only:
            continue
        fr = [spec["fn"](i) for i in range(6)]
        for im in fr:
            outline_im(im, SL[0])
        cols = check(fr, name)
        bad = cols - ok
        assert not bad, (name, "new colors", [tohex(b) for b in bad])
        FRAMES[name] = fr
        fw, fh = spec["fw"], spec["fh"]
        sheet = Image.new("RGBA", (fw * 6, fh), CLEAR)
        for i, im in enumerate(fr):
            sheet.alpha_composite(im, (i * fw, 0))
        meta = common_meta(name, fw, fh, spec["meta"]())
        meta["colors"] = len(cols)
        stats[name] = {"frame": [fw, fh], "colors": len(cols)}
        if dry:
            continue
        d = os.path.join(SPR, "structures", "v3")
        sheet.save(os.path.join(d, name + ".png"))
        with open(os.path.join(d, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
            f.write("\n")
        written.append(name)
    if written:
        to_atlas(written)
    json.dump(stats, open(os.path.join(HERE, "stats_props.json"), "w"), ensure_ascii=False, indent=1)
    print("props", stats)
    return FRAMES
