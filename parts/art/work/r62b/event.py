"""P1-12·P1-13 — 이벤트 NPC · 이벤트 결과 컷 · 상점 노점 칸 받침 · 상점 물건.

NPC(`structures/v3/npc_<id>`, 트림 아틀라스, 적 시트와 같은 규격 4방향 × idle 6):
- npc_conscript  낙오한 징집병 — 징집병(dummy) 몸을 주저앉힌 자세(무릎 세움·창을 어깨에 기댐). 이벤트 conscript.
- npc_merchant   종군 상인 — 독주 행상 몸 바탕, 외투를 차가운 청회로 바꾸고 허리에 호박 등(상호작용 표지 결). 상점.
- npc_brewer     양조장 시음 담당 — 술통 짐꾼 몸 바탕, 조끼를 바랜 앞치마로. 이벤트 tasting.
결과 컷(`events/cut_<eventId>.png`, 320×180, 일기장 삽화 결 — 세피아 먹 + 호박 한 점, 2px 도트).
"""
import math
import os

from PIL import Image, ImageDraw

import common
from common import SPR, SRC, dump, save_png, load_grid, cell, board, hexc, bayer, b2, PAL, hx
from kit2 import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_IRON, R_CLOTH, R_LEATHER, R_SKIN, R_HELM, R_PAPER, R_LIQ,
                  contact, cyl, shade_mask, ell_mask, poly_mask, ell, pol, cap, line, selout, spear_shaft, splash, flame,
                  glass_lantern, embers, plank_box, outline)

T = (0, 0, 0, 0)


def remap(im, table, y0=0):
    im = im.copy()
    p = im.load()
    for y in range(y0, im.height):
        for x in range(im.width):
            c = p[x, y]
            if c[3] and c[:3] in table:
                p[x, y] = table[c[:3]] + (c[3],)
    return im


def rgb(c):
    return tuple(c[:3])


# ---------------------------------------------------------------- NPC
def conscript_frame(src, k, d):
    """징집병 프레임 → 주저앉은 자세. src 96×144, 피벗 (48,138)."""
    w, h = src.size
    out = Canvas(w, h)
    waist = 96                               # 바지 시작(이 위가 몸통·머리)
    drop = 30
    breath = 1 if k in (2, 3) else 0
    top = src.crop((0, 0, w, waist))
    # 들고 있던 몽둥이(아래로 늘어진 막대)는 허리 아래 잘림 — 남는 손잡이 윗부분은 그대로(쥔 손)
    contact(out, 48, 136, 26, 7)
    # 엉덩이·접은 다리(바지 PL1~3, 장화 WD)
    R_TROUSER = [SL[0], PL[0], PL[1], PL[2], PL[3]]
    sx = 1 if d != "left" else -1
    hip_y = waist + drop - 4
    cap(out, [(48 - 10, hip_y), (48 + 10, hip_y)], 9, R_TROUSER, base=0.45, gain=0.7, soft=3)
    for side in (-1, 1):
        kx = 48 + side * 9 + sx * 4
        knee = (kx, hip_y - 14 + (1 if side > 0 else 0))
        foot = (kx + sx * 6, 134)
        cap(out, [(48 + side * 6, hip_y), knee], 5.2, R_TROUSER, base=0.5, gain=0.8, soft=2)
        cap(out, [knee, foot], 4.6, R_TROUSER, base=0.48, gain=0.8, soft=2)
        cap(out, [(foot[0], foot[1] - 1), (foot[0] + sx * 4, foot[1])], 3.6, R_LEATHER, base=0.5, soft=1)
    # 몸통 붙이기(앉은 높이, 숨 쉴 때 1도트)
    out.paste(top, 0, drop + breath)
    # 창: 오른쪽 어깨에 기대 비스듬히(행마다 쪽)
    if d in ("down", "right"):
        spear_shaft(out, (66, 134), (82, 26 + breath), w=2)
    elif d == "left":
        spear_shaft(out, (30, 134), (14, 26 + breath), w=2)
    else:
        spear_shaft(out, (60, 132), (70, 30 + breath), w=2)
    # 이마 붕대·피(낙오 표시) — down 행만 얼굴이 보임
    if d == "down":
        for x in range(40, 56):
            if out.get(x, drop + 34 + breath)[3]:
                out.px(x, drop + 34 + breath, PL[3])
        out.px(52, drop + 35 + breath, A[17])
    return out.im


def build_npcs(items):
    out = {}
    # 1) 낙오한 징집병
    m, g = load_grid("enemies/v3/dummy_idle")
    fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
    frames = []
    for r, d in enumerate(m["directions"]):
        for k in range(n):
            frames.append(conscript_frame(cell(m, g, r, k), k, d))
    out["npc_conscript"] = (frames, fw, fh, m, {
        "eventId": "conscript", "name": "낙오한 징집병", "base": "enemies/v3/dummy_idle(몸통·머리 재사용, 다리·창 새로)",
        "pose": "주저앉음 — 무릎 세움, 창을 어깨에 기댐, 이마 붕대"})
    # 2) 종군 상인 — 외투 WD1~5 → SL1~5 (차가운 청회), 허리 등불
    m, g = load_grid("enemies/v3/peddler_idle")
    tab = {rgb(WD[i]): rgb(SL[i]) for i in range(1, 6)}
    frames = []
    for r, d in enumerate(m["directions"]):
        for k in range(m["frames"]):
            im = remap(cell(m, g, r, k), tab, y0=46)
            c = Canvas(*im.size); c.paste(im, 0, 0)
            lx = 62 if d != "left" else 34
            if d != "up":
                ly = 98 + (1 if k in (2, 3) else 0)
                c.vline(lx, ly - 6, ly - 2, R_IRON[2])
                glass_lantern(c, lx, ly - 2, 7, 10)
            frames.append(c.im)
    out["npc_merchant"] = (frames, m["frameWidth"], m["frameHeight"], m, {
        "role": "shop", "name": "종군 상인", "base": "enemies/v3/peddler_idle(외투 갈색 → 청회로 바꿔 적 행상과 구별)",
        "pose": "선 채 대기 — 허리에 작은 호박 등(친화 NPC 표지)",
        "light": {"color": "#e8b858", "radius": 70, "intensity": 0.45, "offset": {"x": 62, "y": 96}, "flicker": {"amp": 0.15, "hz": 2}}})
    # 3) 양조장 시음 담당 — 조끼 SL3~6 → 바랜 앞치마 PL1~4
    m, g = load_grid("enemies/v3/porter_idle")
    tab = {rgb(SL[3]): rgb(PL[1]), rgb(SL[4]): rgb(PL[2]), rgb(SL[5]): rgb(PL[3]), rgb(SL[6]): rgb(PL[4])}
    frames = []
    for r, d in enumerate(m["directions"]):
        for k in range(m["frames"]):
            im = remap(cell(m, g, r, k), tab)
            c = Canvas(*im.size); c.paste(im, 0, 0)
            if d == "down":   # 술통 위 시음 잔 둘
                for cx in (70, 90):
                    cyl(c, cx, 136, 142, 4, R_WOOD, ry=2)
                    c.px(cx - 1, 135, A[19])
            frames.append(c.im)
    out["npc_brewer"] = (frames, m["frameWidth"], m["frameHeight"], m, {
        "eventId": "tasting", "name": "양조장 시음 담당", "base": "enemies/v3/porter_idle(조끼 청회 → 바랜 앞치마)",
        "pose": "술통에 손 짚고 대기 — 통 위에 시음 잔 둘"})
    for name, (frames, fw, fh, m, extra) in out.items():
        meta = {
            "directions": m["directions"], "layout": m.get("layout"), "pivot": m["pivot"],
            "kind": "npc", "states": {"idle": list(range(m["frames"]))}, "stateLoop": {"idle": True},
            "interact": {"key": "E", "radiusTiles": 1.5, "markAnchor": {"x": m["pivot"]["x"], "y": m["pivot"]["y"] - 128 if fh == 144 else m["pivot"]["y"] - 150},
                         "note": "말 걸기 표지(UI 'E' 키 표시) 자리 — 머리 위 약 10도트"},
            "facing": "주인공 쪽 행을 고른다(down·up·left·right). 고정 배치면 down",
            "solid": True, "footprint": [1, 1], "depth": "y", "paletteSwap": False,
            "palette": "적 시트 색 재사용 + 재질 SL·PL·WD — 새 색 없음", "version": "v3-r62b", "source": SRC + " · event.py",
            "method": "Claude 직접 — 적 시트 몸을 바탕으로 자세·옷 색만 바꿈(같은 세계 사람으로 읽히게)",
        }
        meta.update(extra)
        b2.write_sheet("structures", name, frames, fw, fh, meta, rows=len(m["directions"]),
                       durations=m["frameDurationsMs"], loop=True)
        items.append(board([frames[i] for i in range(0, len(frames), 1)][:6] + [frames[len(frames) // 4 * 2]], bg=(70, 58, 46), k=1, max_w=3000))
    return out


# ---------------------------------------------------------------- 결과 컷 (일기장 삽화)
S = [hx(c) for c in PAL["ui"]["ramp"]]          # 세피아 S0~S5 (UI 전용 — 컷은 UI 그림)
CW, CH = 160, 90                                # 도트 → ×2 = 320×180


def vn(x, y, s):
    n = (int(x) * 374761393 + int(y) * 668265263 + s * 974711) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n & 0xFFFF) / 65535.0


def smooth(x, y, s, f=0.15):
    x, y = x * f, y * f
    xi, yi = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - xi, y - yi
    a, b, c, d = vn(xi, yi, s), vn(xi + 1, yi, s), vn(xi, yi + 1, s), vn(xi + 1, yi + 1, s)
    return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fy


class Ink:
    """먹 삽화 캔버스: 종이(S3) 위에 먹 단계(S0 짙은 먹 ~ S2 옅은 먹), 빛 S4·S5, 호박 한 점."""

    def __init__(self, seed):
        self.seed = seed
        self.im = Image.new("RGBA", (CW, CH), T)
        self.p = self.im.load()
        self.m = Image.new("L", (CW, CH), 0)
        d = ImageDraw.Draw(self.m)
        # 붓 가장자리 종이 영역(불규칙)
        for y in range(CH):
            for x in range(CW):
                e = min(x, y, CW - 1 - x, CH - 1 - y)
                if e > 3 + 4 * smooth(x, y, seed, 0.2):
                    self.p[x, y] = S[3] + (255,)
                    if smooth(x, y, seed + 3, 0.18) > 0.78:
                        self.p[x, y] = S[2] + (255,)        # 얼룩
        self.d = ImageDraw.Draw(self.im)

    def wash(self, pts, tone, rough=0.5):
        """먹 물칠: 다각형을 잡음 가장자리로 tone(S 인덱스)."""
        m = Image.new("L", (CW, CH), 0)
        ImageDraw.Draw(m).polygon(pts, fill=255)
        mp = m.load()
        for y in range(CH):
            for x in range(CW):
                inside = mp[x, y] > 127
                if not inside:
                    continue
                if self.p[x, y][3] == 0:
                    continue
                self.p[x, y] = S[tone] + (255,)

    def ell(self, box, tone):
        m = Image.new("L", (CW, CH), 0)
        ImageDraw.Draw(m).ellipse(box, fill=255)
        mp = m.load()
        for y in range(CH):
            for x in range(CW):
                if mp[x, y] > 127 and self.p[x, y][3]:
                    self.p[x, y] = S[tone] + (255,)

    def stroke(self, pts, w0, w1, tone=0):
        """붓 획: 굵기 w0 → w1 (누름 → 삐침)."""
        segs = list(zip(pts, pts[1:]))
        tot = sum(math.dist(a, b) for a, b in segs) or 1
        acc = 0
        for a, b in segs:
            L = math.dist(a, b)
            n = max(1, int(L * 2))
            for i in range(n + 1):
                t = (acc + L * i / n) / tot
                x, y = a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n
                r = (w0 + (w1 - w0) * t) / 2
                for yy in range(int(y - r), int(y + r) + 1):
                    for xx in range(int(x - r), int(x + r) + 1):
                        if (xx - x) ** 2 + (yy - y) ** 2 <= r * r + 0.3 and 0 <= xx < CW and 0 <= yy < CH and self.p[xx, yy][3]:
                            self.p[xx, yy] = S[tone] + (255,)
            acc += L

    def dot(self, x, y, col):
        if 0 <= x < CW and 0 <= y < CH and self.p[x, y][3]:
            self.p[x, y] = tuple(col[:3]) + (255,)

    def glow(self, cx, cy, r):
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = math.hypot(x - cx, y - cy) / r
                if d < 1 and 0 <= x < CW and 0 <= y < CH and self.p[x, y][3] and bayer(x, y) < (1 - d) * 0.9:
                    cur = self.p[x, y][:3]
                    if cur in (S[3], S[2]):
                        self.p[x, y] = S[4] + (255,)
                    elif cur == S[4]:
                        self.p[x, y] = S[5] + (255,)

    def ground(self, y0, tone=2):
        pts = [(0, y0)] + [(x, y0 + 3 * math.sin(x * 0.07 + self.seed)) for x in range(0, CW + 1, 8)] + [(CW, CH), (0, CH)]
        self.wash(pts, tone)
        for x in range(4, CW - 4, 3):
            if vn(x, 1, self.seed) > 0.6:
                self.dot(x, int(y0 + 2 + 3 * math.sin(x * 0.07 + self.seed)), S[1])

    def out(self):
        return self.im.resize((CW * 2, CH * 2), Image.NEAREST)


def figure_seated(k, x, y, tone=0, spear=True):
    """앉은 사람 실루엣(먹)."""
    k.ell((x - 6, y - 30, x + 6, y - 18), tone)                 # 머리
    k.stroke([(x - 9, y - 31), (x + 9, y - 31)], 3, 2, tone)   # 투구 챙
    k.wash([(x - 9, y - 18), (x + 9, y - 18), (x + 12, y), (x - 12, y)], tone)
    k.wash([(x - 12, y), (x + 18, y - 10), (x + 22, y - 2), (x + 26, y + 2), (x - 14, y + 4)], tone)
    if spear:
        k.stroke([(x + 26, y + 4), (x - 2, y - 52)], 2, 1, tone)
        k.wash([(x - 2, y - 52), (x - 5, y - 60), (x + 1, y - 54)], tone)


def cut_conscript():
    k = Ink(11)
    k.wash([(0, 46), (40, 40), (90, 44), (160, 38), (160, 56), (0, 60)], 2)   # 먼 둔덕
    k.stroke([(112, 40), (112, 18), (106, 10)], 3, 1, 1)                        # 마른 나무
    k.stroke([(112, 24), (124, 16)], 2, 1, 1)
    k.stroke([(112, 30), (100, 22)], 2, 1, 1)
    k.ground(62)
    figure_seated(k, 62, 70)
    # 내민 잔(주인공 손) — 오른쪽에서
    k.stroke([(160, 60), (120, 62), (98, 60)], 4, 3, 1)
    k.wash([(92, 54), (100, 54), (99, 61), (93, 61)], 0)
    k.dot(95, 55, A[23]); k.dot(96, 55, A[24]); k.dot(97, 55, A[23])
    k.glow(96, 56, 12)
    return k.out(), "길가에 주저앉은 징집병, 내민 잔 하나"


def cut_diary():
    k = Ink(12)
    k.ground(70, 2)
    # 펼친 일기장
    k.wash([(30, 60), (78, 52), (80, 74), (32, 82)], 4)
    k.wash([(80, 52), (130, 58), (128, 82), (80, 74)], 4)
    k.stroke([(80, 52), (80, 74)], 2, 2, 1)
    for i in range(5):
        k.stroke([(38, 62 + i * 3), (74, 56 + i * 3)], 1, 1, 2)
    for i in range(3):
        k.stroke([(86, 58 + i * 3), (118, 62 + i * 3)], 1, 1, 2)
    # 붓 든 잿빛 손
    k.stroke([(150, 20), (124, 44), (112, 60)], 6, 4, 0)
    k.stroke([(112, 60), (108, 68)], 2, 1, 0)
    k.dot(108, 68, A[23]); k.dot(109, 67, A[24])
    k.glow(108, 66, 14)
    for (x, y) in ((40, 30), (60, 22), (90, 28)):
        k.dot(x, y, A[22])
    return k.out(), "펼친 일기장의 빈 쪽 위로 붓을 든 잿빛 손"


def cut_tasting():
    k = Ink(13)
    k.ground(64)
    # 술통 위 쟁반과 잔들
    k.wash([(54, 50), (106, 50), (110, 80), (50, 80)], 1)
    k.ell((52, 46, 108, 56), 2)
    for i, x in enumerate((60, 70, 80, 90, 100)):
        k.wash([(x - 3, 42), (x + 3, 42), (x + 2, 50), (x - 2, 50)], 0)
        if i == 2:
            k.dot(x, 43, A[23]); k.dot(x - 1, 43, A[22])
    k.glow(80, 44, 12)
    # 줄 선 사람들(멀수록 옅게)
    for i, x in enumerate((128, 140, 150)):
        tone = [0, 1, 2][i]
        k.ell((x - 4, 34 + i * 2, x + 4, 42 + i * 2), tone)
        k.wash([(x - 6, 42 + i * 2), (x + 6, 42 + i * 2), (x + 7, 66), (x - 7, 66)], tone)
    k.ell((22, 30, 32, 40), 0)
    k.wash([(18, 40), (36, 40), (40, 68), (14, 68)], 0)          # 시음 담당(앞치마)
    k.wash([(22, 44), (32, 44), (34, 64), (20, 64)], 2)
    return k.out(), "양조장 술통 쟁반의 잔들, 줄 선 사람들"


def cut_offering():
    k = Ink(14)
    k.ground(66)
    k.wash([(46, 68), (60, 50), (100, 48), (118, 68)], 1)        # 묘 둔덕
    k.stroke([(80, 50), (80, 22)], 4, 3, 0)                       # 꽂힌 검(묘비)
    k.stroke([(72, 30), (88, 30)], 3, 3, 0)
    k.wash([(74, 44), (86, 44), (84, 52), (76, 52)], 0)           # 술잔
    k.dot(78, 45, A[22]); k.dot(80, 45, A[23]); k.dot(82, 45, A[22])
    k.glow(80, 46, 16)
    k.stroke([(80, 44), (82, 34), (78, 26), (81, 18)], 1, 1, 2)  # 김·연기
    for (x, y) in ((30, 70), (130, 72), (140, 64)):
        k.stroke([(x, y), (x + 2, y - 10)], 2, 1, 1)              # 마른 풀
    return k.out(), "꽂힌 검 앞 묘 위의 술잔 하나"


def cut_droppedLedger():
    k = Ink(15)
    k.ground(58)
    # 진창에 떨어진 장부 + 흩어진 쪽
    k.wash([(54, 64), (100, 58), (108, 78), (60, 84)], 4)
    k.stroke([(54, 64), (60, 84)], 2, 2, 0)
    for i in range(4):
        k.stroke([(64, 68 + i * 3), (100, 63 + i * 3)], 1, 1, 1)
    k.stroke([(70, 70), (96, 72)], 1, 1, 0)                       # 그어진 줄
    for (x, y, a) in ((120, 40, 0.3), (132, 30, -0.4), (30, 48, 0.2)):
        k.wash([(x, y), (x + 10 * math.cos(a), y + 10 * math.sin(a)),
                (x + 10 * math.cos(a) - 6 * math.sin(a), y + 10 * math.sin(a) + 6 * math.cos(a)), (x - 6 * math.sin(a), y + 6 * math.cos(a))], 4)
    # 발자국(성 쪽으로)
    for i in range(6):
        k.ell((20 + i * 14, 78 - i * 2 + (i % 2) * 3, 25 + i * 14, 81 - i * 2 + (i % 2) * 3), 1)
    k.dot(104, 74, A[24]); k.dot(105, 73, A[23])
    k.glow(104, 74, 10)
    return k.out(), "진창에 떨어진 외상 장부와 흩날린 쪽"


CUTS = {"conscript": cut_conscript, "diary": cut_diary, "tasting": cut_tasting, "offering": cut_offering,
        "droppedLedger": cut_droppedLedger}
OPTIONS = {"conscript": ["give", "rob", "pass"], "diary": ["recall", "refine", "read"], "tasting": ["one", "two", "decline"],
           "offering": ["bow", "share", "pass"], "droppedLedger": ["return", "strike", "burn"]}


# ---------------------------------------------------------------- 노점 칸 받침 · 상점 물건
def shop_slot(state):
    c = Canvas(112, 96)
    contact(c, 56, 86, 40, 9)
    plank_box(c, 18, 46, 76, 40, 18, ramp=R_WOOD, seed=3, planks=4)
    if state != "sold":
        # 천 덮개(바랜 붉은 호박 줄무늬 — 1층 램프 어두운 칸)
        m = poly_mask(112, 96, [(14, 50), (56, 40), (98, 50), (100, 62), (56, 70), (12, 62)])
        shade_mask(c, m, [SL[0], A[16], A[17], A[18], PL[2], PL[3]], base=0.55, gain=0.6, soft=3)
        for x in range(16, 98, 9):
            for y in range(44, 70):
                if m.getpixel((x, y)) > 127:
                    c.px(x, y, A[18])
        for x in range(14, 100, 4):   # 술
            c.px(x, 63 + (x % 8 == 0), PL[3])
    else:
        c.poly([(16, 50), (40, 46), (44, 52), (18, 56)], PL[1])   # 걷어 놓은 천
    if state == "near":
        c.px(56, 74, A[23]); c.px(56, 73, A[25])   # 상호작용 표지 = 램프 25 한 점 + 23 받침
    im = c.im
    selout(im, G[1])
    return im


def build_shop(items):
    frames = [shop_slot(s) for s in ("idle", "near", "sold")]
    meta = {
        "directions": ["any"], "pivot": {"x": 56, "y": 86}, "kind": "shop_slot",
        "states": {"idle": [0], "near": [1], "sold": [2]}, "stateLoop": {"idle": False, "near": False, "sold": False},
        "itemAnchor": {"x": 56, "y": 54, "note": "물건 그림(items/v3/<id> 의 idle, 피벗 = 바닥 접점) 을 이 점에 세운다. 물건 그림자(shadow:true)는 천 위에 그대로"},
        "footprint": [1, 1], "solid": True, "depth": "y", "interact": {"key": "E", "radiusTiles": 1.2},
        "near": "주인공이 가까이 오면 near(표지 램프) — 카드 + E 사기는 UI",
        "paletteSwap": True, "paletteSwapNote": "천 줄무늬 = 층 램프 16~18(스왑 대상)",
        "palette": "재질 WD·PL·SL + 1층 램프 16~18·23·25 — 새 색 없음", "version": "v3-r62b", "source": SRC + " · event.py",
    }
    b2.write_sheet("structures", "shop_slot", frames, 112, 96, meta, rows=1, durations=[1000, 1000, 1000])
    items.append(board(frames, bg=(70, 58, 46), k=2))
    # 상점 물건(드랍 그림이 없는 품목) — items/v3/shop_goods 80×96 피벗 (40,88), 행 = 품목, 열 = idle 4
    kinds = ["relic_bundle", "temper", "reroll"]
    fr = []
    for kind in kinds:
        for k in range(4):
            c = Canvas(80, 96)
            contact(c, 40, 88, 16, 5)
            if kind == "relic_bundle":   # 끈으로 묶은 보자기 꾸러미 + 매단 표찰
                R_BOJA = [SL[0], A[16], A[17], A[18], A[19], PL[3]]
                ell(c, (18, 58, 62, 90), R_BOJA, base=0.5, gain=0.85, soft=4, tilt=0.25)
                for (x0, y0) in ((30, 50), (42, 50)):
                    pol(c, [(x0, y0 + 10), (x0 + 2, y0), (x0 + 8, y0 + 2), (x0 + 6, y0 + 10)], R_BOJA, base=0.55, soft=1)
                for y in range(62, 88, 6):
                    for x in range(20, 60):
                        if c.get(x, y)[3] and (x // 3) % 2:
                            c.px(x, y, PL[2])
                pol(c, [(52, 66), (62, 70), (60, 80), (50, 76)], [SL[0], WD[2], PL[1], PL[2], PL[3]], base=0.6, soft=1)
                c.px(56, 73, A[19])
            elif kind == "temper":       # 작은 모루 + 망치
                pol(c, [(22, 70), (58, 70), (52, 78), (46, 78), (46, 88), (34, 88), (34, 78), (28, 78)], R_IRON, base=0.5, gain=0.9, soft=2)
                pol(c, [(14, 70), (22, 70), (22, 74)], R_IRON, base=0.55, soft=1)
                line(c, (44, 66), (60, 46), R_WOOD[3], w=2)
                pol(c, [(54, 40), (66, 46), (62, 52), (50, 46)], R_IRON, base=0.6, soft=1)
            else:                        # 점괘 통(대나무 통 + 뽑힌 산가지)
                cyl(c, 40, 56, 86, 11, R_WOOD, ry=5)
                for i, (x, h) in enumerate(((34, 30), (38, 40), (42, 34), (46, 28))):
                    line(c, (x, 58), (x + (i - 1.5) * 2, 58 - h + 22), PL[3])
                c.px(39, 38, A[22])
            glint = [(40, 48), (30, 56), (50, 52), (44, 44)][k]
            if k in (1, 2):
                c.px(glint[0], glint[1], A[25]); c.px(glint[0] + 1, glint[1], A[23])
            im = c.im
            selout(im, G[1])
            fr.append(im)
    meta = {
        "directions": kinds, "rowsAre": "kinds", "pivot": {"x": 40, "y": 88}, "anchor": "ground", "shadow": True,
        "states": {"idle": [0, 1, 2, 3]}, "stateLoop": {"idle": True},
        "kinds": {"relic_bundle": "유품 카드 품목(보자기 꾸러미 + 표찰)", "temper": "단련 1회(모루 + 망치)", "reroll": "개성 다시 뽑기(점괘 통·산가지)"},
        "reuse": "회복약 = items/v3/potion(idle), 화염 술병 = items/v3/consumable_f1 fire_bottle 행 — 새로 그리지 않음",
        "pixelScale": 0.5, "paletteSwap": False, "version": "v3-r62b", "source": SRC + " · event.py",
    }
    b2.write_sheet("items", "shop_goods", fr, 80, 96, meta, rows=3, durations=[220, 140, 140, 400], loop=True)
    items.append(board(fr, bg=(70, 58, 46), k=2))


def build(preview_path=None):
    items = []
    build_npcs(items)
    build_shop(items)
    cmeta = {"size": [320, 180], "dotPx": 2, "uiScale": "UI 1배(논리 px) — 이벤트 결과 패널 그림 자리", "background": "붓 가장자리 종이(바깥 투명)",
             "palette": "UI 세피아 S0~S5(먹·종이) + 1층 램프 22~24 호박 한 점 — UI 그림", "method": "Claude 직접(Gemini 402) — r62b/event.py",
             "cuts": {}, "aliases": {}, "source": SRC + " · event.py"}
    for eid, fn in CUTS.items():
        im, note = fn()
        if not common.DRY:
            save_png(im, os.path.join(SPR, "events", f"cut_{eid}.png"))
        cmeta["cuts"][eid] = {"file": f"events/cut_{eid}.png", "scene": note}
        for o in OPTIONS[eid]:
            cmeta["aliases"][f"cut_{eid}_{o}"] = f"cut_{eid}"
        items.append(im)
    cmeta["aliasNote"] = "계약 UiEventResult.cutKey 는 `events/cut_<이벤트>_<선택지>` — 이번엔 이벤트당 한 장이라 선택지 키는 모두 이벤트 컷으로 별칭"
    if not common.DRY:
        dump(cmeta, os.path.join(SPR, "events", "cuts.json"))
    if preview_path:
        board(items, bg=(40, 36, 34), k=1, max_w=1800).save(preview_path)
