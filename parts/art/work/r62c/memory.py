"""62 루프 3 (P17 묶음 C · 점검 P1-N6) — 기억 장 아이콘 64×64 `ui_relics/memory_<id>.png` (pixelScale 0.5 → 화면 32px).

기억의 소품(r62b keepsakes.py)과 같은 결: 물건 한 점, 좌상단 빛, 1층 램프 + v2 재질(SL·WD·PL) + 무채, 바깥 1도트 외곽(selout),
반투명 접지 그림자, 투명 배경, 글자·테두리 없음. Claude 직접(Gemini 402).

- ink     장터의 먹물 — 먹물 한 병(검은 유약 단지 · 코르크 · 노끈 맨 종이표 · 흘러내린 먹)
- bellows 장터의 풀무 — 손풀무(나무 판 · 가죽 주름 · 쇠 주둥이 · 끝의 불티)
- hp      몸의 기억(최대 체력) — 붕대 감긴 숨 쉬는 심장(호박 불씨 빛 — 몸에 남은 불)
- attack  손의 기억(공격력) — 붕대 감은 주먹(마디에 불티 한 점)
- dash    발의 기억(대쉬 대기) — 내딛는 낡은 가죽 장화 + 재 빛 잔상 줄
- empty   빈손(소품 고르기 '아무것도 지니지 않고') — 위로 펼친 빈 손바닥(빛 없음)
"""
import math
import os
import sys

from PIL import Image, ImageDraw

from c62 import HERE, SPR, SRC, WORK, load_json, save_json

sys.path.insert(0, os.path.join(WORK, "r62b"))
import kit2  # noqa: E402  (r62b 그림 도구 — common 은 r62b 것)
from kit2 import (Canvas, G, A, SL, WD, PL, R_WOOD, R_IRON, R_LEATHER, contact, pol, ell, cap, line, selout,  # noqa: E402
                  shade_mask, qcol, flame, embers)

S = 64
OUTDIR = os.path.join(SPR, "ui_relics")
R_GLAZE = [G[0], G[1], G[2], G[3], G[5], G[8]]                   # 검은 유약
R_CORK = [SL[0], WD[1], WD[2], WD[3], WD[4], PL[1]]
R_HAND = [SL[0], WD[1], PL[0], PL[1], PL[2], PL[3]]               # 손(바랜 살빛 — 재 세계의 살)
R_BAND = [SL[0], G[5], G[8], G[10], G[11], G[12]]                 # 붕대
R_HEART = [A[16], A[17], A[18], A[19], A[20], A[21], A[22]]       # 심장(불씨)
R_BOOT = [SL[0], WD[0], WD[1], WD[2], WD[3], WD[4]]
R_SLEEVE = [G[1], G[2], G[3], G[4], G[5], G[6]]
R_CLOTHM = [G[1], G[3], G[4], G[5], G[6], G[7]]                   # 소매(중간 재빛 천)


def _m():
    m = Image.new("L", (S, S), 0)
    return m, ImageDraw.Draw(m)


def finish(c):
    im = c.im
    selout(im)
    return im


# ---------------------------------------------------------------- 먹물 한 병
def i_ink():
    c = Canvas(S, S)
    contact(c, 32, 53, 20, 5)
    # 흘린 먹 웅덩이(오른쪽 아래)
    for y in range(50, 58):
        for x in range(34, 56):
            d = math.hypot((x - 45) / 10.5, (y - 54) / 3.2)
            if d < 1:
                c.px(x, y, G[0] if d < 0.75 else G[1])
    c.px(41, 52, G[5]); c.px(42, 52, G[4])
    # 단지 몸(배 부른 항아리)
    m, d = _m()
    d.ellipse((15, 24, 49, 55), fill=255)
    d.rectangle((24, 18, 40, 30), fill=255)
    shade_mask(c, m, R_GLAZE, base=0.36, gain=0.9, soft=4)
    # 어깨 테 · 목
    line(c, (22, 28), (42, 28), G[0])
    for x in range(25, 40):
        c.px(x, 19, G[4] if x < 30 else G[3])
    # 코르크
    m, d = _m()
    d.rectangle((26, 10, 38, 19), fill=255)
    d.ellipse((26, 7, 38, 13), fill=255)
    shade_mask(c, m, R_CORK, base=0.55, gain=0.8, soft=2)
    for (x, y) in ((29, 13), (33, 15), (35, 11), (30, 17)):
        c.px(x, y, WD[1])
    # 유약 반짝임(좌상) — 긴 호
    for k, (x, y) in enumerate(((21, 34), (20, 36), (20, 38), (20, 40), (21, 42))):
        c.px(x, y, G[10] if 1 <= k <= 3 else G[8])
    c.px(23, 31, G[8]); c.px(24, 30, G[7])
    # 목에 감은 노끈 + 종이표(먹 한 획 — 글자 아님)
    line(c, (24, 22), (40, 22), WD[4])
    line(c, (24, 23), (40, 23), WD[2])
    pol(c, [(36, 23), (47, 27), (44, 41), (33, 37)], [SL[0], PL[0], PL[1], PL[2], PL[3], PL[4]], base=0.62, gain=0.5, soft=1)
    line(c, (39, 29), (41, 35), G[2])
    line(c, (38, 32), (43, 31), G[2])
    # 입구에서 흘러내린 먹 줄기
    for y in range(20, 34):
        x = 25 - (1 if y > 27 else 0)
        c.px(x, y, G[0])
    c.px(24, 34, G[0]); c.px(24, 35, G[1])
    # 1층 빛(호박) 한 점 — 노끈 매듭
    c.px(40, 22, A[22]); c.px(41, 23, A[20])
    return finish(c)


# ---------------------------------------------------------------- 풀무
def i_bellows():
    c = Canvas(S, S)
    contact(c, 32, 52, 25, 6)
    # 쇠 주둥이(왼쪽 아래로) — 먼저(판 아래)
    cap(c, [(20, 41), (6, 50)], 2.6, R_IRON, base=0.55, gain=0.9, soft=1)
    c.px(5, 51, G[0]); c.px(6, 51, G[0])
    # 아래 판(어둡게) · 가죽 주름 · 위 판
    def board(dy, base):
        m, d = _m()
        d.polygon([(18, 34 + dy), (32, 22 + dy), (50, 20 + dy), (56, 28 + dy), (50, 38 + dy), (30, 44 + dy)], fill=255)
        shade_mask(c, m, R_WOOD, base=base, gain=0.7, soft=2)
    board(8, 0.34)
    # 가죽 주름(판 사이 옆면) — 접힌 띠 셋
    for k in range(3):
        y0 = 36 + k * 3
        pol(c, [(20, y0 - 2), (30, y0 + 4), (50, y0 - 2), (54, y0 - 6), (50, y0 + 1), (30, y0 + 7), (20, y0 + 1)],
            R_LEATHER, base=0.5 - k * 0.04, gain=0.8, soft=1)
        line(c, (21, y0 + 1), (30, y0 + 7), WD[0])
    board(0, 0.6)
    # 위 판 무늬: 쇠 띠 · 못 · 공기 구멍
    line(c, (24, 31), (44, 23), G[3]); line(c, (24, 30), (44, 22), G[6])
    for (x, y) in ((27, 29), (35, 26), (42, 23)):
        c.px(x, y, G[8]); c.px(x + 1, y + 1, G[2])
    ell(c, (36, 30, 42, 34), [G[0], G[1], G[2], WD[1]], base=0.2, gain=0.4, soft=0)
    # 손잡이 둘(오른쪽 뒤)
    cap(c, [(50, 22), (61, 16)], 2.0, R_WOOD, base=0.62, gain=0.8, soft=1)
    cap(c, [(51, 30), (62, 27)], 2.0, R_WOOD, base=0.45, gain=0.8, soft=1)
    # 주둥이 끝 불티(1층 빛)
    for (x, y, col) in ((3, 47, A[25]), (2, 45, A[23]), (5, 44, A[24]), (1, 50, A[22]), (4, 42, A[22]), (7, 46, A[26])):
        c.px(x, y, col)
    c.px(4, 48, A[27]); c.px(3, 49, A[24])
    return finish(c)


# ---------------------------------------------------------------- 심장(몸의 기억)
def i_hp():
    c = Canvas(S, S)
    contact(c, 32, 55, 17, 4)
    m, d = _m()
    d.ellipse((12, 14, 34, 38), fill=255)                  # 왼 둥근 위
    d.ellipse((28, 13, 51, 37), fill=255)                  # 오른 둥근 위
    d.polygon([(13, 30), (50, 29), (33, 54), (30, 54)], fill=255)
    # 불씨 심장: 가운데(좌상)가 뜨겁고 가장자리가 식은 숯
    mp = m.load()
    for y in range(S):
        for x in range(S):
            if mp[x, y] <= 127:
                continue
            dd = math.hypot((x - 26) / 20, (y - 27) / 22)
            s = 0.95 - dd * 0.85
            c.px(x, y, qcol(R_HEART, s, x, y, 2.5))
    kit2.outline(c, m, R_HEART)
    # 굵은 혈관 줄기(위로 뻗은 대동맥 — 숯빛)
    cap(c, [(31, 16), (33, 7)], 3.0, [A[16], A[17], A[18], A[19]], base=0.5, gain=0.7, soft=1)
    cap(c, [(37, 16), (41, 9)], 2.2, [A[16], A[17], A[18], A[19]], base=0.45, gain=0.7, soft=1)
    # 숯 결(금) — 표면이 식어 갈라짐
    for a, b in (((18, 33), (24, 37)), ((40, 24), (45, 31)), ((34, 40), (31, 46))):
        line(c, a, b, A[16])
    # 붕대(왼 위 → 오른 아래 한 바퀴 비스듬히)
    pol(c, [(11, 25), (16, 21), (52, 33), (48, 38)], R_BAND, base=0.62, gain=0.6, soft=1)
    line(c, (14, 25), (49, 36), G[6])
    c.px(20, 26, G[13]); c.px(21, 26, G[12])
    # 하이라이트(좌상 덩이)
    for (x, y) in ((19, 19), (20, 18), (21, 18), (18, 21)):
        c.px(x, y, A[25])
    c.px(20, 19, A[26])
    return finish(c)


# ---------------------------------------------------------------- 주먹(손의 기억)
def i_attack():
    c = Canvas(S, S)
    contact(c, 32, 56, 20, 4)
    # 소매(오른쪽 아래로 빠짐, 천 주름)
    cap(c, [(40, 46), (54, 60)], 8.5, R_CLOTHM, base=0.5, gain=0.8, soft=3)
    line(c, (42, 52), (50, 58), G[2]); line(c, (46, 49), (55, 55), G[2])
    # 주먹 덩어리(둥근)
    m, d = _m()
    d.ellipse((12, 14, 50, 52), fill=255)
    d.rounded_rectangle((14, 20, 48, 50), radius=10, fill=255)
    shade_mask(c, m, R_HAND, base=0.5, gain=0.9, soft=5)
    # 접은 손가락 넷(앞면 둥근 덩이 — 왼쪽이 빛 쪽)
    for k in range(4):
        x0 = 14 + k * 8
        ell(c, (x0, 24 + (k % 2), x0 + 10, 42 + (k % 2)), R_HAND, base=0.66 - k * 0.06, gain=0.85, soft=2)
    for k in range(3):
        x = 23 + k * 8
        line(c, (x + (k % 2), 27), (x + (k % 2), 41), WD[1])           # 손가락 사이 골
    # 위 마디 줄(밝은 덩이)
    for k in range(4):
        x0 = 15 + k * 8
        ell(c, (x0, 18, x0 + 8, 25), R_HAND, base=0.78 - k * 0.07, gain=0.6, soft=1)
    # 엄지(앞을 가로질러 — 가장 밝음)
    cap(c, [(15, 43), (27, 41), (35, 37)], 4.4, R_HAND, base=0.72, gain=0.85, soft=1)
    c.px(35, 35, PL[4]); c.px(36, 36, PL[3])                        # 엄지 손톱
    line(c, (17, 48), (33, 42), WD[1])
    # 마디 붕대: 위 마디를 감은 두 줄(곡면 따라) + 늘어진 꼬리
    for k, y in enumerate((20, 24)):
        pts = [(13 + i, y + int(round(3 * ((i - 18) / 18) ** 2)) - (1 if i % 7 == 3 else 0)) for i in range(0, 36)]
        for (x, yy) in pts:
            c.px(x, yy, G[12] if k == 0 else G[11]); c.px(x, yy + 1, G[10] if k == 0 else G[9])
            c.px(x, yy + 2, G[6])
    line(c, (47, 26), (51, 33), G[11]); line(c, (48, 26), (53, 31), G[9]); c.px(52, 34, G[8])
    # 손등 빛(좌상)
    for (x, y) in ((19, 17), (20, 16), (21, 16), (18, 18)):
        c.px(x, y, PL[4])
    # 마디 불티(1층 빛 — 친 자리)
    for (x, y, col) in ((9, 14, A[24]), (7, 11, A[22]), (11, 10, A[23]), (6, 16, A[22]), (10, 7, A[22]), (4, 12, A[23])):
        c.px(x, y, col)
    c.px(8, 13, A[26])
    return finish(c)


# ---------------------------------------------------------------- 장화(발의 기억)
def i_dash():
    c = Canvas(S, S)
    # 재 빛 잔상 줄(뒤 왼쪽) — 먼저, 끝으로 갈수록 성기게
    for k, (y, x0, x1) in enumerate(((22, 2, 22), (32, 0, 20), (42, 4, 22))):
        for x in range(x0, x1):
            t = (x - x0) / max(1, x1 - x0)
            if t > 0.55 or (x + k) % 3 != 0:
                c.px(x, y, G[9] if t > 0.75 else G[6])
                if t > 0.6:
                    c.px(x, y + 1, G[4])
    contact(c, 38, 56, 19, 4)
    # 흙먼지(뒤꿈치)
    for (x, y, col) in ((22, 52, PL[1]), (24, 50, PL[2]), (20, 55, PL[0]), (26, 54, PL[1]), (19, 51, PL[0]), (23, 48, PL[0])):
        c.px(x, y, col)
    # 장화: 목(위) → 발등 → 앞코(오른쪽), 살짝 기울여 내딛음
    m, d = _m()
    d.polygon([(26, 6), (40, 5), (41, 27), (44, 31), (50, 33), (55, 36), (58, 40), (59, 45), (57, 50), (28, 51), (25, 44)], fill=255)
    shade_mask(c, m, R_BOOT, base=0.5, gain=0.85, soft=4)
    # 밑창(진하게) · 굽
    pol(c, [(26, 49), (57, 47), (58, 52), (27, 54)], [G[0], G[1], G[2], G[3]], base=0.4, gain=0.5, soft=0)
    pol(c, [(26, 50), (34, 50), (34, 56), (27, 56)], [G[0], G[1], G[2], G[3]], base=0.35, gain=0.5, soft=0)
    # 목 테 · 접힌 주름 · 끈
    line(c, (26, 8), (40, 7), WD[4]); line(c, (26, 9), (40, 8), WD[1])
    for (a, b) in (((28, 20), (38, 19)), ((28, 26), (37, 27)), ((30, 34), (36, 36))):
        line(c, a, b, WD[1])
        line(c, (a[0], a[1] - 1), (b[0], b[1] - 1), WD[4])
    for k in range(3):
        y = 33 + k * 4
        line(c, (40, y), (47, y + 3), PL[1])
    # 해진 앞코(밝은 닳음)
    for (x, y) in ((52, 39), (53, 40), (55, 43), (54, 42)):
        c.px(x, y, PL[2])
    # 1층 빛 한 점 — 굽 쇠징
    c.px(29, 55, A[22]); c.px(31, 55, A[20])
    return finish(c)


# ---------------------------------------------------------------- 빈손
def i_empty():
    c = Canvas(S, S)
    contact(c, 30, 56, 20, 4, a=80)
    # 소매(왼쪽 아래)
    cap(c, [(18, 54), (6, 62)], 8.0, R_CLOTHM, base=0.5, gain=0.8, soft=3)
    line(c, (8, 56), (16, 52), G[2])
    # 손가락(뒤 → 앞): 새끼·약지·중지·검지 — 위로 펼쳐 살짝 굽음
    fingers = [((44, 30), (50, 18), (50, 14), 2.6), ((39, 27), (42, 13), (42, 9), 3.0),
               ((33, 26), (34, 11), (33, 7), 3.1), ((27, 28), (25, 14), (23, 10), 3.0)]
    for (a, b, tip, r) in fingers:
        cap(c, [a, b, tip], r, R_HAND, base=0.74, gain=0.8, soft=1)
        bx, by = b
        line(c, (bx - 2, by + 6), (bx + 2, by + 6), WD[1])                 # 마디 주름
    # 손바닥(위로 펼친, 가운데 오목)
    m, d = _m()
    d.polygon([(22, 30), (46, 27), (50, 34), (46, 48), (28, 52), (18, 44)], fill=255)
    mp = m.load()
    for y in range(S):
        for x in range(S):
            if mp[x, y] <= 127:
                continue
            dd = math.hypot((x - 35) / 13, (y - 39) / 10)
            s = 0.42 + 0.3 * min(1, dd) + 0.12 * (1 - (x + y - 50) / 50)       # 가운데 오목 = 어둡게, 둘레 = 밝게
            c.px(x, y, qcol(R_HAND, s, x, y, 2.5))
    kit2.outline(c, m, R_HAND)
    # 손금(셋)
    for (a, b) in (((24, 37), (44, 33)), ((26, 42), (42, 40)), ((33, 49), (30, 36))):
        line(c, a, b, WD[1])
    # 엄지(왼쪽으로 벌림)
    cap(c, [(21, 42), (13, 34), (11, 28)], 3.4, R_HAND, base=0.74, gain=0.8, soft=1)
    # 손바닥 끝 빛(좌상)
    for (x, y) in ((23, 31), (24, 30), (25, 30)):
        c.px(x, y, PL[4])
    return finish(c)


MEMORY = {
    # 파일 id: (함수, memory.json/meta.json id, 이름, 장, 메모)
    "ink": (i_ink, "inkBottle", "장터의 먹물", "shop", "먹물 한 병 — 검은 유약 단지·코르크·노끈 맨 종이표·흘러내린 먹"),
    "bellows": (i_bellows, "bellows", "장터의 풀무", "shop", "손풀무 — 나무 판·가죽 주름·쇠 주둥이 끝 불티"),
    "hp": (i_hp, "maxHp", "몸의 기억", "stat", "붕대 감긴 불씨 심장 — 최대 체력"),
    "attack": (i_attack, "attack", "손의 기억", "stat", "마디에 붕대 감은 주먹 · 불티 — 공격력"),
    "dash": (i_dash, "dashCooldown", "발의 기억", "stat", "내딛는 낡은 장화 · 재 빛 잔상 줄 — 대쉬 대기"),
    "empty": (i_empty, "keepsakeNone", "빈손", "keepsake", "위로 펼친 빈 손바닥(빛 없음) — 소품 고르기 '빈손'"),
}


def build():
    out = {}
    for k, (fn, sid, name, chap, note) in MEMORY.items():
        im = fn()
        im.save(os.path.join(OUTDIR, f"memory_{k}.png"), optimize=True)
        cols = len({p for p in im.getdata() if p[3] == 255})
        out[k] = {"file": f"ui_relics/memory_{k}.png", "size": [S, S], "id": sid, "name": name, "chapter": chap,
                  "note": note, "colors": cols}
    rj = os.path.join(OUTDIR, "relics.json")
    meta = load_json(rj)
    meta["memory"] = out
    meta["memoryNote"] = ("62 루프 3 (P17 묶음 C) 기억 장 아이콘 — 64×64·pixelScale 0.5(화면 32px), 기억의 소품과 같은 결. "
                          "키 = ui_relics/memory_<파일 id>. id = data/memory.json items[].id(장터 inkBottle·bellows) · "
                          "data/meta.json upgrades[].id(maxHp·attack·dashCooldown) · memory.json pick.keepsakeNone(빈손). "
                          "'처음 모양'은 무기 기본 그림(looks/<weapon>_base) 재사용 권장. " + SRC + " · memory.py")
    save_json(rj, meta)
    return list(out)


def preview():
    names = list(MEMORY)
    ims = [Image.open(os.path.join(OUTDIR, f"memory_{k}.png")) for k in names]
    ks = [Image.open(os.path.join(OUTDIR, f"keepsake_{k}.png")) for k in ("brokenCup", "inkBrush")]
    allim = ims + ks
    sheet = Image.new("RGBA", (len(allim) * 266 + 10, 266 + 10 + 74), (48, 38, 30, 255))
    for i, im in enumerate(allim):
        sheet.alpha_composite(im.resize((256, 256), Image.NEAREST), (10 + i * 266, 10))
        sheet.alpha_composite(im.resize((64, 64), Image.LANCZOS) if False else im.resize((32, 32), Image.NEAREST), (10 + i * 266, 276))
        sheet.alpha_composite(im, (60 + i * 266, 276))
    p = os.path.join(HERE, "preview_memory.png")
    sheet.save(p)
    return p
