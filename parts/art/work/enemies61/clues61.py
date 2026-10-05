"""61라운드 P8 서사 소품 3종(59라운드 1층 단서) — structures/v3, pixelScale 0.5(64 도트 = 1칸), E 조사형(states idle/found).

- clue_masked_corpse   탄생지(벽 밖): 가면 쓴 '적' 시체 + 엎어진 '같은' 술병(징집병 술병과 같은 호박 병·헝겊 마개).
                       idle = 병과 시체 양쪽에서 같은 술 냄새 김이 올라와 한 줄기로 섞임 / found = 가면 이마의 잔(盞) 문양이 호박빛으로 드러남.
- clue_gate_register   성문 초소 출입 장부: 초소 책상 위 펼친 장부 — 줄 친 칸이 '나간 자' 한 칸뿐(오른쪽 '돌아온 자' 칸 자리가 비어 있음).
                       idle = 촛불 흔들림·책장 끝 들썩 / found = 빈 칸 자리를 따라 호박 점선이 드러남(돌아온 자 칸이 없다는 것이 보이게).
- clue_tab_ledgers     보스방 외상 장부 더미: 쌓인 장부·펼친 장부·흩어진 쪽·엎질러진 잔 얼룩.
                       idle = 흩어진 쪽 들썩·젖은 먹 반짝 / found = 펼친 장부 맨 끝 줄(방금 쓴 듯한 이름)이 호박빛.
규칙(계약 §22): 상호작용 표지 = 램프 25 한 점 + 23 받침(found 에서 꺼짐) · 자체 발광 = 23~27 · 1층 램프로 그림(paletteSwap false).
글자는 그리지 않는다(문장은 UI/스토리) — 줄·칸·문양만.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../bundle2"))
import b2  # noqa: E402
from b2 import (Canvas, Rand, G, A, SL, WD, PL, R_WOOD, R_WOODG, R_IRON, R_CLOTH, R_CLOTHG, R_EARTH, R_LIQ, R_BONE,  # noqa: E402
                contact, shade_mask, mask, poly_mask, ell_mask, splash, plank_box, flame, outline, EMISSIVE_HEX)
import structs  # noqa: E402  (bundle2 구조물: mark·states_json·L·ledger_book 재사용)
from structs import mark, states_json, L  # noqa: E402

SRC = "parts/art/work/enemies61/clues61.py (61라운드 P8 서사 소품)"
R_LEATHER = [SL[0], WD[0], WD[1], WD[2], WD[3], WD[4]]
R_BOTTLE = [A[16], A[17], A[18], A[19], A[20], A[21], A[22]]
R_MASK = [SL[1], PL[1], PL[2], PL[3], PL[4], G[12], G[13]]
R_COATF = [SL[0], SL[1], SL[2], G[4], G[5], G[6]]                   # 낯선 군복(무채 회색 — 1층 사람들의 갈색·청회와 다르게)


def capsule_mask(w, h, pts, r):
    m, d = mask(w, h)
    for (a, b) in zip(pts, pts[1:]):
        d.line([a, b], fill=255, width=int(r * 2))
    for p in pts:
        d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=255)
    return m


def capsule(c, pts, r, ramp, base=0.5, gain=0.7, soft=2):
    shade_mask(c, capsule_mask(c.w, c.h, pts, r), ramp, base=base, gain=gain, soft=soft)


def wisp(c, x0, y0, k, seed, length=26, cols=(PL[3], PL[2], PL[1]), lean=0.0):
    """냄새 김(비발광): 아래에서 위로 흔들리며 흩어지는 가는 줄."""
    for j in range(length):
        y = y0 - j * 2 - (k * 2 + seed) % 4
        x = x0 + lean * j + int(round((1.5 + j * 0.12) * math.sin(j * 0.3 + k * 1.05 + seed)))
        f = j / length
        if (j + k + seed) % 8 == 0 or (f > 0.55 and (x + y) % 2):
            continue
        c.px(x, y, cols[0] if f < 0.3 else (cols[1] if f < 0.65 else cols[2]))


# ====================================================================== 1. 가면 쓴 '적' 시체
def cup_mark(c, cx, cy, col, col2):
    """잔(盞) 문양 7×6 — 결사병 방패·행상 상자와 같은 잔 모양."""
    for dx in range(-3, 4):
        c.px(cx + dx, cy - 2, col)
    for (dx, dy) in ((-2, -1), (2, -1), (-1, 0), (1, 0), (0, 1), (0, 2), (-1, 3), (0, 3), (1, 3)):
        c.px(cx + dx, cy + dy, col2 if dy > 0 else col)


def corpse_base(c, found, k):
    W_, H_ = c.w, c.h
    contact(c, 100, 94, 74, 12, a=90)
    # 바닥 흙 얼룩(어두운 흙 — 피 없음)
    splash(c, 96, 96, 60, 9, ramp=[SL[0], WD[1], WD[2], PL[0], WD[1], PL[0]], seed=4, glint=False, blobs=5)
    # 부러진 창대(뒤)
    for t in range(56):
        x, y = 48 + t, 64 + int(t * 0.18)
        c.px(x, y, R_WOOD[3]); c.px(x, y + 1, R_WOOD[1])
    c.rect(103, 73, 106, 75, R_IRON[3]); c.px(103, 73, R_IRON[5])
    # 다리(오른쪽으로 뻗음) + 장화
    capsule(c, [(112, 80), (140, 84), (164, 86)], 6, [SL[0], G[1], G[2], G[3], G[4]], base=0.5)
    capsule(c, [(110, 86), (138, 92), (160, 96)], 6, [SL[0], G[1], G[2], G[3], G[4]], base=0.45)
    capsule(c, [(164, 85), (174, 82)], 5, R_LEATHER, base=0.5)
    capsule(c, [(160, 95), (171, 94)], 5, R_LEATHER, base=0.45)
    # 몸통(낯선 군복 — 누운 상체, 가슴 위)
    # 누운 상체: 가슴이 위로 솟은 덩어리 + 어깨 패드 + 덮인 망토 자락(바닥으로 흘러내림)
    m = poly_mask(W_, H_, [(60, 82), (72, 98), (110, 100), (118, 92), (114, 96), (104, 104), (66, 104)])
    shade_mask(c, m, [SL[0], SL[1], G[2], G[3]], base=0.45, gain=0.5, soft=2)
    m = poly_mask(W_, H_, [(64, 70), (90, 66), (112, 70), (120, 82), (114, 96), (72, 98), (58, 86)])
    shade_mask(c, m, R_COATF, base=0.55, gain=0.9, soft=6, tilt=0.25)
    for (x0, y0) in ((62, 70), (62, 90)):
        m = ell_mask(W_, H_, (x0, y0, x0 + 14, y0 + 10))
        shade_mask(c, m, [SL[0], G[3], G[4], G[6], G[8], G[10]], base=0.5, gain=0.8, soft=2)
    # 군복 단추·띠(다른 나라 옷: 가로 매듭 단추 3)
    for x in (82, 92, 102):
        c.hline(x - 2, x + 2, 79, G[9]); c.px(x, 80, G[2])
    c.line(70, 88, 116, 90, SL[0]); c.line(70, 87, 116, 89, G[7])
    # 팔: 왼팔은 몸 옆, 오른팔은 아래(카메라 쪽)로 술병을 향해 뻗음
    capsule(c, [(70, 76), (58, 70), (48, 74)], 4, R_COATF, base=0.45)
    capsule(c, [(98, 96), (102, 106), (112, 110)], 4, R_COATF, base=0.5)
    c.ellipse((111, 107, 117, 113), WD[4]); c.px(112, 108, PL[2]); c.px(116, 112, WD[2])
    c.ellipse((44, 71, 50, 77), WD[4])
    # 두건 + 가면(얼굴 위를 향함)
    capsule(c, [(44, 82), (58, 84)], 12, [SL[0], G[1], G[2], G[3], G[5]], base=0.42)
    # 가면: 세로로 긴 방패꼴(이마 넓고 턱 좁음), 얼굴은 위(하늘)를 봄 — 3/4 시점이라 위로 기운 타원
    m = poly_mask(W_, H_, [(38, 72), (47, 68), (57, 71), (59, 80), (55, 89), (47, 93), (40, 89), (36, 80)])
    shade_mask(c, m, R_MASK, base=0.6, gain=0.85, soft=3, tilt=0.25)
    # 콧날 세로 능선 + 눈구멍(가늘게 찢은 틈) + 입 없음(무표정)
    c.vline(47, 76, 86, R_MASK[4]); c.vline(48, 77, 86, R_MASK[2])
    for ex in (41, 51):
        c.hline(ex, ex + 4, 79, SL[0]); c.hline(ex + 1, ex + 3, 80, SL[0]); c.px(ex, 78, R_MASK[2])
    c.line(37, 81, 31, 86, R_LEATHER[2]); c.line(58, 82, 64, 88, R_LEATHER[2])
    # 가면 이마 잔 문양: idle = 바랜 칠(거의 안 보임) / found = 호박빛(자체 발광)
    if found:
        cup_mark(c, 47, 73, A[26], A[24])
    else:
        cup_mark(c, 47, 73, R_MASK[3], R_MASK[2])


def corpse_bottle(c, found, k):
    # 엎어진 술병(징집병 술병과 같은 호박 병 + 헝겊 마개) — 주둥이가 오른쪽 아래
    m = capsule_mask(c.w, c.h, [(124, 102), (138, 108)], 5)
    shade_mask(c, m, R_BOTTLE, base=0.55, gain=0.8, soft=2)
    c.line(139, 109, 145, 112, A[17]); c.line(139, 110, 145, 113, A[18])
    c.px(146, 113, PL[3]); c.px(147, 113, PL[4]); c.px(146, 114, PL[2])
    c.px(127, 101, A[22]); c.px(128, 101, A[21])
    # 쏟아진 술 웅덩이 + 떨어지는 방울(루프)
    splash(c, 156, 114, 14, 4, ramp=R_LIQ, seed=6, blobs=3, glint=True)
    if not found:
        dy = (k * 2) % 6
        c.px(147, 115 + dy // 3, A[21])
    else:
        for x in (148, 154, 160):
            c.px(x, 113, A[24])


def clue_masked_corpse():
    W_, H_, piv = 192, 128, (96, 112)
    fr = []
    for k in range(6):
        c = Canvas(W_, H_)
        corpse_base(c, False, k)
        corpse_bottle(c, False, k)
        # 같은 술 냄새: 병 웅덩이와 가면(시체) 양쪽에서 올라온 김이 위에서 한 줄기로 기운다
        wisp(c, 152, 108, k, 1, length=28, lean=-0.55)
        wisp(c, 50, 70, k, 4, length=22, lean=0.65)
        wisp(c, 98, 70, k + 3, 2, length=18, lean=0.1)
        mark(c, 132, 96, True)
        fr.append(c.im)
    c = Canvas(W_, H_)
    corpse_base(c, True, 0)
    corpse_bottle(c, True, 0)
    for s_, (x, y, ln) in enumerate(((152, 108, 30), (50, 70, 26))):
        wisp(c, x, y, 2, s_, length=ln, lean=-0.55 if s_ == 0 else 0.65, cols=(A[22], A[21], A[19]))
    mark(c, 132, 96, False)
    fr.append(c.im)
    st, lp = states_json([("idle", 6, True), ("found", 1, False)])
    m = {
        "id": "clue_masked_corpse", "clue": "탄생지 단서 — 가면 쓴 '적' 시체와 엎어진 같은 술병(59라운드 1층 단서 '같은 술 냄새')",
        "usage": "61라운드 P8 · 탄생지(벽 밖 전장) 노드에 1개. E 로 조사 → found + 문장(스토리 파트 텍스트)",
        "footprint": [2, 1], "solid": False, "depth": "y", "pivot": {"x": piv[0], "y": piv[1]}, "occludeAbove": 16,
        "states": st, "stateLoop": lp, "interact": "E", "uiKind": "clue",
        "markAnchor": {"x": 132, "y": 96}, "maskAnchor": {"x": 48, "y": 80}, "bottleAnchor": {"x": 132, "y": 106},
        "stateNote": ("idle: 병 웅덩이와 가면 쪽에서 같은 술 냄새 김이 올라와 한쪽으로 기울며 섞임(비발광 — 조명 받아야 보임), 술방울 똑똑. "
                      "found: 가면 이마의 바랜 잔(盞) 문양이 호박빛(자체 발광) — 우리와 같은 잔을 든 자 · 김도 호박빛 · 표지 꺼짐"),
        "designNote": "가면 = 무표정 흰 가면(눈구멍 두 줄), 군복 = 무채 회색(1층 갈색·청회 사람들과 다른 옷). 문양은 결사병 방패의 잔 문양과 같은 모양",
        "light": None, "lightByState": {"found": L("#e2a33c", 70, 0.55, 48, 76, 0.08, 2)},
        "emissiveColors": EMISSIVE_HEX, "floor": "stage1", "paletteSwap": False, "source": SRC, "version": "v3-r61",
    }
    b2.write_sheet("structures", "clue_masked_corpse", fr, W_, H_, m, durations=[170] * 6 + [100])
    return fr, piv


# ====================================================================== 2. 성문 초소 출입 장부
def register_page(c, x0, y0, w, h, base, found, flutter=0):
    """줄 친 장부 한 쪽: 위 머리띠(칸 이름 자리) 1칸 + 빽빽한 이름 줄. 오른쪽 1/3 은 '돌아온 자' 칸이 있어야 할 빈 자리."""
    pts = [(x0, y0), (x0 + w, y0 - 1 - flutter), (x0 + w + 1, y0 + h), (x0 + 1, y0 + h + 1)]
    m = poly_mask(c.w, c.h, pts)
    shade_mask(c, m, R_BONE, base=base, gain=0.35, soft=1, rim=False)
    col_w = int(w * 0.62)
    # 머리 칸(나간 자) — 진한 띠 + 칸 경계
    c.rect(x0 + 2, y0 + 2, x0 + col_w, y0 + 4, SL[3])
    c.vline(x0 + col_w + 1, y0 + 2, y0 + h - 1, PL[1])
    # 이름 줄(먹) — 길이 들쭉날쭉, 거의 끝까지 빽빽
    r = Rand(int(x0 * 7 + y0))
    y = y0 + 7
    while y < y0 + h - 2:
        ln = r.i(col_w - 14, col_w - 3)
        for x in range(x0 + 3, x0 + 3 + ln):
            if (x + y) % 5 != 0:
                c.px(x, y, SL[3] if r.f() < 0.7 else PL[0])
        y += 3
    if found:
        # 돌아온 자 칸이 있어야 할 자리 — 호박 점선 테(자체 발광)
        xa, xb = x0 + col_w + 4, x0 + w - 2
        for x in range(xa, xb + 1):
            if x % 2 == 0:
                c.px(x, y0 + 3, A[25]); c.px(x, y0 + h - 2, A[24])
        for yy in range(y0 + 3, y0 + h - 1):
            if yy % 2 == 0:
                c.px(xa, yy, A[25]); c.px(xb, yy, A[24])


def desk_candle(c, x, by, k, lit=True):
    c.rect(x - 3, by - 2, x + 3, by, R_IRON[3]); c.hline(x - 3, x + 3, by - 2, R_IRON[5])
    c.rect(x - 1, by - 9, x + 1, by - 3, PL[4]); c.vline(x + 1, by - 9, by - 3, PL[2])
    if lit:
        sw = [0, 1, 0, -1][k % 4]
        for (dx, dy, col) in ((0, -10, A[25]), (0, -11, A[26]), (sw, -12, A[27]), (sw, -13, A[26]), (sw, -14, A[24]), (-1, -11, A[23]),
                              (1, -11, A[23]), (sw, -15, A[23] if k % 2 else A[24])):
            c.px(x + dx, by + dy, col)


def register_frame(k, found):
    W_, H_ = 144, 160
    c = Canvas(W_, H_)
    contact(c, 72, 146, 52, 8)
    # 초소 책상(앞판 + 다리) — plank_box: 윗면 높이 22, 앞면 40
    plank_box(c, 20, 82, 104, 40, 22, ramp=R_WOODG, seed=5, planks=5, slats=True, brace=False)
    for x in (24, 112):
        c.rect(x, 144, x + 6, 147, R_WOODG[1])
    # 걸어 둔 출입 표찰(앞판, 잔 문양 낙인)
    c.rect(60, 112, 84, 124, R_WOODG[3]); c.hline(60, 84, 112, R_WOODG[5]); c.hline(60, 84, 124, R_WOODG[0])
    cup = [(-3, -2), (-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (3, -2), (-2, -1), (2, -1), (-1, 0), (1, 0), (0, 1), (0, 2), (-1, 3), (0, 3), (1, 3)]
    for dx, dy in cup:
        c.px(72 + dx, 117 + dy, A[18])
    c.line(66, 106, 72, 112, WD[1]); c.line(78, 106, 72, 112, WD[1])
    # 펼친 장부(두 쪽) — 표지 + 두 쪽 + 가운데 접힘
    c.poly([(26, 78), (118, 76), (122, 100), (24, 102)], R_LEATHER[2])
    c.hline(26, 118, 77, R_LEATHER[4])
    register_page(c, 28, 76, 44, 22, 0.78, found, 0)
    register_page(c, 74, 75, 44, 22, 0.66, found, 1 if k in (1, 2) else 0)
    c.line(73, 75, 73, 99, PL[1])
    # 먹통 + 붓
    c.ellipse((100, 98, 110, 104), SL[0]); c.ellipse((101, 98, 109, 101), SL[2]); c.px(104, 99, G[9])
    c.line(96, 92, 112, 86, WD[4]); c.line(96, 93, 112, 87, WD[2]); c.px(95, 93, SL[0]); c.px(94, 93, SL[0])
    # 촛대(책상 왼쪽 위) — 장부를 비추는 불
    desk_candle(c, 22, 82, k, True)
    # 통행 도장(쇠 손잡이)
    c.rect(38, 98, 44, 104, WD[3]); c.hline(38, 44, 98, WD[5]); c.rect(40, 94, 42, 97, R_IRON[4])
    mark(c, 72, 66, not found)
    return c.im


def clue_gate_register():
    W_, H_, piv = 144, 160, (72, 146)
    fr = [register_frame(k, False) for k in range(4)] + [register_frame(0, True)]
    st, lp = states_json([("idle", 4, True), ("found", 1, False)])
    m = {
        "id": "clue_gate_register", "clue": "국경 초소 단서 — 출입 장부: 줄 친 칸이 '나간 자' 하나뿐, '돌아온 자' 칸이 없다(59라운드 1층 단서)",
        "usage": "61라운드 P8 · 성문(국경 초소) 노드에 1개. E 로 조사 → found + 문장(스토리)",
        "footprint": [2, 1], "solid": True, "depth": "y", "pivot": {"x": piv[0], "y": piv[1]}, "occludeAbove": 64,
        "states": st, "stateLoop": lp, "interact": "E", "uiKind": "clue", "markAnchor": {"x": 72, "y": 66},
        "stateNote": ("idle: 책상 촛불 흔들림 · 오른쪽 책장 끝 들썩. 장부 양쪽 모두 왼쪽 2/3 칸에만 이름 줄이 빽빽하고 오른쪽 1/3 은 칸도 줄도 없다. "
                      "found: 그 빈 자리를 호박 점선(자체 발광)이 칸 모양으로 둘러 '없는 칸'을 보여 준다 · 표지 꺼짐"),
        "light": L("#e8b858", 110, 0.7, 22, 68, 0.15, 5), "lightNote": "책상 촛불 — 어두운 초소에서 장부가 먼저 보이게",
        "emissiveColors": EMISSIVE_HEX, "floor": "stage1", "paletteSwap": False, "source": SRC, "version": "v3-r61",
    }
    b2.write_sheet("structures", "clue_gate_register", fr, W_, H_, m, durations=[160, 160, 160, 160, 100])
    return fr, piv


# ====================================================================== 3. 보스방 외상 장부 더미
def closed_book(c, x, y, w, h, top_h, seed, tilt=0):
    """닫힌 장부(3/4): 윗면 가죽 + 앞면 종이 단면 + 등 라벨."""
    m = poly_mask(c.w, c.h, [(x, y + tilt), (x + w, y), (x + w, y + top_h), (x, y + top_h + tilt)])
    shade_mask(c, m, R_LEATHER, base=0.62, gain=0.5, soft=1, rim=False)
    c.poly([(x, y + top_h + tilt), (x + w, y + top_h), (x + w, y + top_h + h), (x, y + top_h + h + tilt)], PL[3])
    for j in range(1, h, 2):
        c.line(x + 1, y + top_h + tilt + j, x + w - 1, y + top_h + j, PL[2])
    c.line(x, y + top_h + h + tilt, x + w, y + top_h + h, SL[0])
    c.line(x, y + tilt, x + w, y, R_LEATHER[5])
    lx = x + w // 2 - 3
    c.rect(lx, y + 2, lx + 6, y + top_h - 2, A[18]); c.px(lx + 1, y + 3, A[20])


def tab_frame(k, found):
    W_, H_ = 176, 136
    c = Canvas(W_, H_)
    contact(c, 88, 118, 70, 11)
    # 엎질러진 잔 얼룩(술) — 바닥
    splash(c, 132, 118, 22, 6, ramp=R_LIQ, seed=11, blobs=4, glint=True)
    # 쌓인 장부 더미(뒤 → 앞)
    closed_book(c, 30, 70, 46, 12, 12, 1, tilt=2)
    closed_book(c, 34, 58, 42, 10, 12, 2, tilt=-2)
    closed_book(c, 28, 48, 44, 10, 10, 3, tilt=1)
    closed_book(c, 100, 72, 44, 12, 12, 4, tilt=-1)
    closed_book(c, 104, 60, 40, 10, 12, 5, tilt=2)
    closed_book(c, 56, 92, 50, 12, 12, 6, tilt=0)
    # 펼친 장부(맨 위 가운데) — 이름 줄이 쪽 끝까지
    structs.ledger_book(c, 88, 86, crossed=False, seal=False)
    if found:
        for x in range(92, 117):            # 맨 끝 줄 = 방금 쓴 듯한 이름(호박, 자체 발광, 2줄 굵기)
            if x % 6:
                c.px(x, 93, A[26]); c.px(x, 94, A[24])
        c.px(117, 93, A[27]); c.px(118, 92, A[25])
    else:
        c.px(110, 94, A[22] if k % 3 == 0 else PL[1])          # 젖은 먹 반짝
    # 흩어진 쪽(들썩 루프)
    lift = [0, 1, 2, 1, 0, 0][k]
    c.poly([(140, 100 - lift), (158, 98 - lift * 2), (160, 108), (142, 110)], PL[3])
    c.line(144, 102 - lift, 156, 101 - lift * 2, PL[1]); c.line(144, 105, 156, 104 - lift, PL[1])
    c.poly([(18, 104), (34, 100), (36, 110), (20, 112)], PL[2]); c.line(22, 105, 32, 103, SL[3])
    # 엎어진 잔(놋쇠)
    c.ellipse((116, 108, 128, 114), A[17]); c.ellipse((118, 109, 126, 112), A[19]); c.rect(126, 109, 132, 112, A[18]); c.px(127, 109, A[21])
    mark(c, 88, 70, not found)
    return c.im


def clue_tab_ledgers():
    W_, H_, piv = 176, 136, (88, 120)
    fr = [tab_frame(k, False) for k in range(6)] + [tab_frame(0, True)]
    st, lp = states_json([("idle", 6, True), ("found", 1, False)])
    m = {
        "id": "clue_tab_ledgers", "clue": "보스방 단서 — 외상 장부 더미(이름이 계속 늘어남 · 휴식 메모 '외상 장부에 내 이름이 있다' 연계)",
        "usage": "61라운드 P8 · 보스방(연회장) 구석에 1개. 보스 처치 뒤 E 로 조사 → found + 문장(스토리)",
        "footprint": [2, 1], "solid": True, "depth": "y", "pivot": {"x": piv[0], "y": piv[1]}, "occludeAbove": 30,
        "states": st, "stateLoop": lp, "interact": "E(보스 처치 후 제안)", "uiKind": "clue", "markAnchor": {"x": 88, "y": 70},
        "stateNote": "idle: 흩어진 쪽 들썩 · 젖은 먹 반짝. found: 펼친 장부 맨 끝 줄(방금 쓴 듯한 이름)이 호박빛(자체 발광) · 표지 꺼짐",
        "light": None, "lightByState": {"found": L("#e2a33c", 60, 0.45, 104, 92, 0.05, 2)},
        "solidNote": "보스전 중 엄폐로 쓰이지 않게 방 구석(기둥 뒤) 배치 제안 — 술통 되치기에는 '단단한 구조물'로 술통이 깨짐",
        "emissiveColors": EMISSIVE_HEX, "floor": "stage1", "paletteSwap": False, "source": SRC, "version": "v3-r61",
    }
    b2.write_sheet("structures", "clue_tab_ledgers", fr, W_, H_, m, durations=[200] * 6 + [100])
    return fr, piv


ALL = [clue_masked_corpse, clue_gate_register, clue_tab_ledgers]
