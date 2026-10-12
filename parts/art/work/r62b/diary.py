"""62 루프 2 — 메인 요청: 장터 국밥(shop_goods heal 행) · 일기장 사연(E4) 방 소품 `structures/v3/event_diary_open`.

- soup(k): 80×96 피벗 (40,88) — 뚝배기 국밥 한 그릇(숟가락 걸침) + 김 4프레임(같은 결: 바닥 접지 그림자, 외곽 G1, 호박 반짝임 1~2 프레임).
- event_diary_open: 128×112 피벗 (64,100) — 낮은 소반 위 펼친 일기장 + 붓, 대기 6프레임 은은한 먹 번짐(쪽 위 먹점이 퍼졌다 옅어짐).
  NPC 시트와 같은 json 형식(interact{key E, radiusTiles, markAnchor}).
색: lopad gray + 1층 램프 + v2 재질 SL·WD·PL — 새 색 없음.
"""
import math

from PIL import Image

from common import SRC, b2, board
from kit2 import (Canvas, G, A, SL, WD, PL, R_WOOD, R_IRON, R_PAPER, contact, cyl, ell, pol, line, selout, shade_mask,
                  qcol, poly_mask)

R_CLAY = [SL[0], G[1], G[2], G[3], G[4], G[5]]          # 검은 뚝배기(유약 먹빛)
R_BROTH = [WD[2], WD[4], PL[2], PL[3], PL[4], G[12]]     # 뽀얀 국물(사골 — 담색)


# ---------------------------------------------------------------- 국밥
def soup(k):
    c = Canvas(80, 96)
    contact(c, 40, 88, 22, 6)
    # 뚝배기: 몸통(넓은 사발) — 위 지름 44, 아래 좁음
    m = poly_mask(80, 96, [(16, 64), (64, 64), (60, 80), (54, 87), (26, 87), (20, 80)])
    shade_mask(c, m, R_CLAY, base=0.5, gain=0.9, soft=4)
    for y in range(66, 86, 5):                          # 거친 질감 줄
        for x in range(20, 60):
            if c.get(x, y)[3] and (x * 3 + y) % 7 == 0:
                c.px(x, y, G[1])
    # 입구 테 + 국물
    c.ellipse((15, 58, 65, 70), R_CLAY[3])
    c.ellipse((17, 59, 63, 69), R_CLAY[1])
    m2 = Image.new("L", (80, 96), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(m2).ellipse((19, 60, 61, 68), fill=255)
    shade_mask(c, m2, R_BROTH, base=0.55, gain=0.6, soft=2, rim=False)
    # 건더기: 밥 덩이(밝은 PL) · 고기 편(WD) · 파(어두운 회녹 대신 SL)
    for (x, y, col) in ((30, 63, PL[4]), (31, 63, PL[3]), (29, 64, PL[3]), (44, 62, WD[3]), (45, 62, WD[4]), (46, 63, WD[3]),
                        (52, 65, SL[4]), (53, 65, SL[5]), (36, 66, SL[4]), (25, 65, WD[4]), (40, 64, PL[4])):
        c.px(x, y, col)
    for (x, y) in ((34, 61), (48, 66), (27, 62)):        # 기름 윤(호박)
        c.px(x, y, A[22])
    c.px(35, 61, A[21])
    for (x, y) in ((38, 62), (39, 62), (41, 65)):        # 다진 파(먹빛 점)
        c.px(x, y, SL[3])
    # 숟가락(테에 걸침)
    line(c, (52, 62), (68, 48), R_IRON[4], w=2)
    line(c, (53, 63), (69, 49), R_IRON[2])
    ell(c, (47, 61, 54, 66), R_IRON, base=0.6, soft=1)
    # 김(4프레임 — 세 줄기가 위로 흔들리며 오름)
    steam = [PL[2], PL[3], PL[4]]
    for j, bx in enumerate((30, 40, 50)):
        ph = k * 0.9 + j * 1.7
        for t in range(0, 26):
            y = 58 - t
            x = bx + 3.2 * math.sin(ph + t * 0.28)
            if (t + k + j) % 6 == 0 or t > 22 - j * 2:
                continue
            col = steam[2] if t < 8 else steam[1] if t < 16 else steam[0]
            if t > 12 and (int(x) + y + k) % 2:
                continue                                 # 위쪽은 성기게(사라짐)
            c.px(int(round(x)), y, col)
    if k in (1, 2):
        g = [(22, 62), (58, 64)][k - 1]
        c.px(g[0], g[1], A[25]); c.px(g[0] + 1, g[1], A[23])
    im = c.im
    selout(im, G[1])
    # 김은 외곽선 없이(외곽이 김을 감싸면 딱딱해짐) — selout 은 불투명 픽셀 기준이라 김 둘레도 잡힌다 → 김 위쪽 외곽 지움
    p = im.load()
    for y in range(28, 57):
        for x in range(80):
            if p[x, y][:3] == tuple(G[1][:3]) and p[x, y][3] == 255:
                p[x, y] = (0, 0, 0, 0)
    return im


# ---------------------------------------------------------------- 일기장 사연 소품
FW, FH = 128, 112
PIV = (64, 100)


def diary_frame(k):
    c = Canvas(FW, FH)
    contact(c, 64, 100, 46, 9)
    # 낮은 소반(쿼터뷰): 윗판 평행사변형 + 두께 + 짧은 다리 넷
    for (lx, ly) in ((26, 88), (100, 88), (36, 96), (92, 96)):
        c.rect(lx - 2, ly - 10, lx + 2, ly, R_WOOD[2])
        c.vline(lx - 2, ly - 10, ly, R_WOOD[4])
        c.hline(lx - 2, lx + 2, ly, R_WOOD[0])
    top = [(18, 70), (110, 70), (118, 84), (10, 84)]
    c.poly([(10, 84), (118, 84), (118, 89), (10, 89)], R_WOOD[1])
    c.hline(10, 118, 84, R_WOOD[3])
    shade_mask(c, poly_mask(FW, FH, top), R_WOOD, base=0.55, gain=0.5, soft=2, tilt=0.1)
    for x in range(22, 108, 18):                         # 판 이음
        line(c, (x, 71), (x - 6, 83), R_WOOD[2])
    # 펼친 일기장(왼·오른 쪽, 가운데 접힘) — 표지 가장자리(가죽) 먼저
    pol(c, [(30, 60), (64, 64), (98, 60), (102, 80), (64, 84), (26, 80)], [SL[0], WD[0], WD[1], WD[2], WD[3]], base=0.5, soft=1)
    pol(c, [(32, 58), (63, 62), (63, 80), (29, 77)], R_PAPER, base=0.74, gain=0.4, soft=2)
    pol(c, [(65, 62), (96, 58), (99, 77), (65, 80)], R_PAPER, base=0.66, gain=0.4, soft=2)
    line(c, (64, 62), (64, 81), PL[0])
    c.vline(63, 63, 80, PL[4])
    # 먹 글줄(왼쪽 쪽) · 오른쪽은 쓰다 만 두 줄
    for i in range(5):
        y = 63 + i * 3
        line(c, (35, y), (59, y + 2), SL[2] if i % 2 else SL[1])
    for i in range(2):
        y = 63 + i * 3
        line(c, (69, y + 1), (88 - i * 7, y - 1), SL[1])
    # 먹 번짐(오른쪽 쪽 가운데) — 6프레임: 퍼졌다(0→3) 옅어짐(4·5)
    R = [1.6, 2.4, 3.2, 3.8, 3.4, 2.4][k]
    tone = [0, 0, 0, 1, 2, 2][k]
    bx, by = 80, 71
    for y in range(by - 6, by + 6):
        for x in range(bx - 7, bx + 8):
            dd = math.hypot((x - bx) / 1.3, y - by)
            wob = 0.35 * math.sin(math.atan2(y - by, x - bx) * 3 + k)
            if dd < R + wob:
                core = dd < R * 0.55
                col = [G[0], G[1], G[2], G[3]][min(3, tone + (0 if core else 1))]
                c.px(x, y, col)
            elif dd < R + wob + 1.2 and (x + y + k) % 2 == 0:
                c.px(x, y, PL[1])                        # 번짐 가장자리 젖은 종이
    # 붓(쪽 위에 비스듬히) — 끝에 먹
    line(c, (88, 48), (104, 66), R_WOOD[4], w=2)
    line(c, (89, 49), (105, 67), R_WOOD[2])
    c.rect(85, 45, 88, 48, R_IRON[3])
    pol(c, [(82, 41), (86, 44), (85, 46), (80, 45)], [G[0], G[1], G[2]], base=0.5, soft=0)
    # 호박 한 점(쪽에 떨어진 등불 빛) — 프레임마다 아주 조금 숨쉼
    gl = [A[21], A[22], A[23], A[22], A[21], A[21]][k]
    c.px(46, 66, gl); c.px(47, 66, A[21])
    im = c.im
    selout(im, G[1])
    return im


DIARY_DUR = [260, 220, 220, 300, 260, 340]


def build_diary(items):
    frames = [diary_frame(k) for k in range(6)]
    meta = {
        "directions": ["any"], "rowsAre": "directions", "pivot": {"x": PIV[0], "y": PIV[1]},
        "kind": "event_prop", "eventId": "diary", "name": "펼친 일기장(사연 E4)",
        "states": {"idle": list(range(6))}, "stateLoop": {"idle": True},
        "interact": {"key": "E", "radiusTiles": 1.4, "markAnchor": {"x": 64, "y": 40},
                     "note": "말 걸기 표지(UI 'E' 키 표시) 자리 — 펼친 책 가운데 위(붓 끝 높이), 책 윗변에서 약 18도트 위"},
        "facing": "고정(any 한 행)",
        "solid": True, "footprint": [2, 1], "depth": "y", "paletteSwap": False, "shadow": True,
        "scene": "낮은 소반 위 펼친 일기장 + 먹 묻은 붓, 오른쪽 쪽 먹점이 은은하게 번졌다 옅어진다",
        "palette": "재질 WD·PL·SL + gray + 1층 램프 21~23 — 새 색 없음", "version": "v3-r62b", "source": SRC + " · diary.py",
        "method": "Claude 직접 도트",
    }
    b2.write_sheet("structures", "event_diary_open", frames, FW, FH, meta, rows=1, durations=DIARY_DUR, loop=True)
    items.append(board(frames, bg=(70, 58, 46), k=2))
    return frames
