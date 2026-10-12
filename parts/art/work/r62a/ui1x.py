"""62a — 의식 UI 그림(UI 키트 1배 = 960×540 논리 1px): 일기장 첫 장 `ritual/diary_first_page` · 운명 공개 액자 `ritual/fate_frame`.

색: UI 세피아 S0~S5(UI 전용) + 무채 + 1층 호박(그을린 가장자리의 꺼져 가는 불씨·액자 불티 금만). 반투명 없음.
"""
import math
import random

from PIL import Image, ImageDraw

import os

from common import A, G, S, SPR, Fbm, Noise, mask

CLEAR = (0, 0, 0, 0)


def rgba(c):
    return (c[0], c[1], c[2], 255)


# ------------------------------------------------------------------ 일기장 첫 장
PW, PH = 360, 420
NAME_FIELD = (112, 150, 208, 52)        # x, y, w, h — 이름 붓글씨 자리(밑줄 = y + h - 6)
NAME_LABEL = (36, 160, 70, 28)          # '이름' 글자 자리(UI, page_title 또는 page_body)
TITLE_AREA = (40, 84, 280, 26)          # 첫 장 머리글 한 줄(예: '이 일기의 주인')
BODY_LINES = [236, 262, 288, 314, 340]  # 본문 괘선 y(글자 바닥선) — 안내·지난 생 기록
BODY_AREA = (40, 222, 270, 128)
STAMP_AREA = (262, 330, 64, 64)         # 도장 자리(stamp_* 48 을 가운데에 0.85)


def paper_tex(w, h, seed):
    """UI 키트 1.3절 종이 결(되풀이 없는 한 장): S3 본색 · S2 스티플(8px 잡음으로 농도) · S1 깊은 때 · S4 드문 밝은 점 · 섬유."""
    im = Image.new("RGB", (w, h), S[3])
    p = im.load()
    r = random.Random(seed)
    n8 = Noise(seed + 1, w // 8, h // 8)
    n24 = Noise(seed + 2, w // 24, h // 24)
    for y in range(h):
        for x in range(w):
            a = n8.at(x / w, y / h)
            b = n24.at(x / w, y / h)
            pr = 0.06 + 0.42 * max(0.0, a - 0.35) + 0.12 * max(0.0, b - 0.5)
            q = r.random()
            if q < 0.006:
                p[x, y] = S[4]
            elif q < pr:
                p[x, y] = S[2] if (b < 0.72 or r.random() < 0.7) else S[1]
    for _ in range(w * h // 900):
        x, y = r.randint(0, w - 1), r.randint(0, h - 1)
        L = r.randint(3, 8)
        dx = r.choice((0, 0, 1, -1))
        for k in range(L):
            xx, yy = x + (dx * k) // 2, y + k
            if 0 <= xx < w and 0 <= yy < h:
                p[xx, yy] = S[2]
    return im


def burn_shape(r):
    """그을려 타 들어간 가장자리 — 칸마다 타 들어간 깊이(도트). 오른쪽 아래가 가장 깊이 탔다."""
    fb = Fbm(501, 9, 9, 3)

    def depth(x, y):
        # 가장자리 둘레 위치에 따른 기본 깊이 + 잡음
        base = 2.0
        if x > PW * 0.50 and y > PH * 0.62:
            u = (x - PW * 0.50) / (PW * 0.50)
            v = (y - PH * 0.62) / (PH * 0.38)
            base += (u * v) ** 0.8 * 70
        if y < 40 and x > PW * 0.55:
            base += 5 * (x - PW * 0.55) / (PW * 0.45)
        if x < 30 and y > PH * 0.45:
            base += 4
        return base + (fb.at(x / PW, y / PH) - 0.5) * (14 + base * 0.7)
    return depth


def diary_page():
    im = Image.new("RGBA", (PW, PH), CLEAR)
    p = im.load()
    r = random.Random(511)
    depth = burn_shape(r)
    n8 = Noise(512, PW // 8, PH // 8)
    n3 = Noise(513, PW // 3, PH // 3)
    fib = Fbm(514, 3, 40, 2)
    # 1) 종이(UI 키트 paper_tile 64 를 깔고) + 그을음(가장자리에서 안쪽으로 S2 → S1 → S0 → 구멍)
    paper = paper_tex(PW, PH, 515)
    tp = paper.load()
    emb = []
    for y in range(PH):
        for x in range(PW):
            dmin = min(x, y, PW - 1 - x, PH - 1 - y)
            dep = depth(x, y)
            t = dmin - dep
            if t < 0:
                continue
            s = n8.at(x / PW, y / PH) * 0.6 + n3.at(x / PW, y / PH) * 0.4
            sc = 9.0 + s * 10 + dep * 0.35          # 그을음 폭(깊이 탄 곳일수록 넓게)
            if t < 2.2:
                c = S[0]
                if r.random() < 0.12:
                    emb.append((x, y))
            elif t < 5.5:
                c = S[1] if s < 0.66 or t > 3.5 else S[0]
            elif t < sc * 0.55:
                c = S[1] if (s > 0.55 and t < sc * 0.4) else S[2]
            elif t < sc:
                c = S[2] if (s * 0.8 + (t / sc) * 0.4) < 0.78 else tp[x, y][:3]
            else:
                c = tp[x, y][:3]
            p[x, y] = rgba(c)
    # 2) 왼쪽 제본 단: 찢겨 나온 실 구멍 · 홈 그늘
    for y in range(18, PH - 30, 22):
        for (dx, dy) in ((10, 0), (11, 0), (10, 1), (11, 1)):
            if p[dx, y + dy][3]:
                p[dx, y + dy] = rgba(S[1])
        if p[12, y + 2][3]:
            p[12, y + 2] = rgba(S[4])
    for y in range(PH):
        for x in range(4, 16):
            if p[x, y][3] and p[x, y][:3] == S[3] and (x < 8 or (x < 14 and (x + y) % 3 == 0)):
                p[x, y] = rgba(S[2])
    d = ImageDraw.Draw(im)
    # 3) 머리 장식: 바랜 잔(盞) 낙인 + 괘선
    cx = PW // 2
    for (pts, c) in (([(cx - 14, 34), (cx + 14, 34), (cx + 9, 50), (cx - 9, 50)], S[4]),):
        d.polygon(pts, outline=rgba(c))
    d.line([(cx, 50), (cx, 58)], fill=rgba(S[4]))
    d.line([(cx - 8, 59), (cx + 8, 59)], fill=rgba(S[4]))
    d.line([(cx - 11, 38), (cx + 11, 38)], fill=rgba(S[2]))
    for k in range(-1, 2):          # 잔에서 오르는 김 세 줄
        for t in range(6):
            x = cx + k * 6 + (1 if (t + k) % 3 == 0 else 0)
            p[x, 30 - t] = rgba(S[4] if t % 2 == 0 else S[2])
    # 바랜 자리(낙인 일부가 닳음)
    for _ in range(14):
        x, y = r.randint(cx - 14, cx + 14), r.randint(34, 59)
        if p[x, y][:3] == S[4]:
            p[x, y] = rgba(S[2])
    rule(p, 40, PW - 40, 72, faded=0.15, r=r)
    # 4) 이름 칸: 꺾쇠 4 + 붓 밑줄(빛나는 먹 S5, 할로 S4, 그늘 S2) — 마른 붓 끝
    fx, fy, fw, fh = NAME_FIELD
    for (x0, y0, sx, sy) in ((fx - 6, fy, 1, 1), (fx + fw + 5, fy, -1, 1), (fx - 6, fy + fh, 1, -1), (fx + fw + 5, fy + fh, -1, -1)):
        for k in range(8):
            p[x0 + sx * k, y0] = rgba(S[4])
            p[x0, y0 + sy * k] = rgba(S[4])
        p[x0 + sx, y0 + sy] = rgba(S[2])
    brush_rule(p, fx + 4, fx + fw - 4, fy + fh - 6, r)
    # 이름 칸 안쪽 아주 옅은 바탕(먹이 앉을 자리 — 종이가 한 단 덜 바램)
    for y in range(fy + 6, fy + fh - 10):
        for x in range(fx + 8, fx + fw - 8):
            if p[x, y][:3] == S[2] and (x + y) % 2 == 0:
                p[x, y] = rgba(S[3])
    # 이름 라벨 앞 작은 붓 점(항목 표시)
    lx, ly, lw, lh = NAME_LABEL
    for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
        p[lx - 10 + dx, ly + lh // 2 - 1 + dy] = rgba(S[5])
    # 5) 본문 괘선(옅게, 군데군데 끊김)
    for yy in BODY_LINES + [366]:
        rule(p, 40, PW - 52, yy, faded=0.35, r=r, dotted=True)
    # 6) 얼룩: 물자국 고리 · 술잔 자국(호박 아님 — 세피아) · 손때
    ring(p, 300, 116, 15, r)
    ring(p, 74, 386, 11, r, partial=True)
    smudge(p, 52, 120, 26, 10, r)
    # 7) 그을린 가장자리 불씨(꺼져 가는 호박 점 — 자체 발광, UI 가 깜빡여도 됨)
    embers = []
    for (x, y) in emb[::3]:
        if r.random() < 0.55:
            c = A[5] if r.random() < 0.4 else A[4]
            p[x, y] = rgba(c)
            embers.append([x, y])
    # 8) 바깥 1도트 먹 테(타 들어간 끝) — 투명 이웃이 있는 칸 = S0
    edge = []
    for y in range(PH):
        for x in range(PW):
            if p[x, y][3] == 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if not (0 <= xx < PW and 0 <= yy < PH) or p[xx, yy][3] == 0:
                    edge.append((x, y))
                    break
    for (x, y) in edge:
        if p[x, y][:3] not in (A[4], A[5]):
            p[x, y] = rgba(S[0])
    return im, embers


def rule(p, x0, x1, y, faded, r, dotted=False):
    for x in range(x0, x1):
        if r.random() < faded:
            continue
        if dotted and x % 3 == 2:
            continue
        if p[x, y][3] and p[x, y][:3] in (S[3], S[2]):
            p[x, y] = rgba(S[4] if not dotted else (S[4] if x % 3 == 0 else S[2]))
            if not dotted and p[x, y + 1][3]:
                p[x, y + 1] = rgba(S[2])


def brush_rule(p, x0, x1, y, r):
    """붓 밑줄: 누름(왼쪽 굵게) → 몸 2도트 → 마른 붓 끝(오른쪽 털 갈라짐). 빛나는 먹 규칙(S5 몸 · S4 할로 · S2 그늘)."""
    body = set()
    L = x1 - x0
    for x in range(x0, x1 + 1):
        t = (x - x0) / L
        w = 3 if t < 0.06 else (2 if t < 0.8 else 1)
        yc = y + int(round(math.sin(t * 3.0) * 1.2))
        if t > 0.8 and r.random() < (t - 0.8) * 3.5:
            continue
        for k in range(w):
            body.add((x, yc + k - (1 if w == 3 else 0)))
        if t > 0.86:            # 갈라진 털 한 가닥 위로
            if r.random() < 0.6:
                body.add((x, yc - 2))
    halo = set()
    for (x, yy) in body:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, yy + dy)
            if q not in body:
                halo.add(q)
    shade = set()
    for (x, yy) in halo:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, yy + dy)
            if q not in body and q not in halo:
                shade.add(q)
    for q in shade:
        if p[q][3]:
            p[q] = rgba(S[2])
    for q in halo:
        if p[q][3]:
            p[q] = rgba(S[4])
    for q in body:
        if p[q][3]:
            p[q] = rgba(S[5])


def ring(p, cx, cy, rad, r, partial=False):
    for k in range(int(rad * 7)):
        a = 2 * math.pi * k / (rad * 7)
        if partial and 0.6 < a < 2.6:
            continue
        if r.random() < 0.18:
            continue
        x = int(round(cx + math.cos(a) * rad))
        y = int(round(cy + math.sin(a) * rad * 0.92))
        if p[x, y][3] and p[x, y][:3] in (S[3], S[2]):
            p[x, y] = rgba(S[1] if k % 3 else S[2])


def smudge(p, cx, cy, rx, ry, r):
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d < 1 and r.random() < 0.35 * (1 - d) and p[x, y][:3] == S[3]:
                p[x, y] = rgba(S[2])


# ------------------------------------------------------------------ 운명 공개 액자 (9-slice)
FW = 128
SLICE = 40
INNER = 36          # 바깥에서 그림 칸까지


def fate_frame():
    """검게 옻칠하고 그을린 나무 틀 · 쇠 모서리 쇠붙이 · 안쪽 불씨 테(호박) · 먹 매트. 변 조각은 변 방향으로 같은 색(늘려도 덩어리 없음)."""
    im = Image.new("RGBA", (FW, FW), CLEAR)
    p = im.load()

    def band_color(t, along, corner):
        """t = 바깥에서 안쪽으로의 거리(0..INNER-1), along = 변 방향 좌표(모서리 칸에서만 무늬)."""
        if t <= 0:
            return S[0]
        if t <= 2:
            return G[1]
        if t <= 4:
            return S[1]                          # 옻칠 빛 받는 모서리(모따기)
        if t <= 15:
            # 그을린 나무 몸: 결(변 방향 줄)
            return S[0] if t in (7, 12) else (G[2] if t in (9, 10) else S[1])
        if t == 16:
            return G[1]
        if t <= 19:
            return G[0] if t == 17 else G[1]     # 홈
        if t == 20:
            return A[2]
        if t == 21:
            return A[5]                          # 불씨 테(자체 발광)
        if t == 22:
            return A[3]
        if t == 23:
            return G[0]
        if t <= 33:
            return G[1] if t not in (27, 30) else G[2]   # 먹 매트
        if t == 34:
            return G[0]
        return S[0]                              # 35 그림 홈

    for y in range(FW):
        for x in range(FW):
            t = min(x, y, FW - 1 - x, FW - 1 - y)
            if t >= INNER:
                continue
            p[x, y] = rgba(band_color(t, 0, False))
    # 빛 쪽(위·왼쪽) 모따기 한 단 밝게 · 아래·오른쪽 한 단 어둡게
    for y in range(FW):
        for x in range(FW):
            t = min(x, y, FW - 1 - x, FW - 1 - y)
            if t in (3, 4):
                if (y == t) or (x == t):
                    p[x, y] = rgba(S[2])
                else:
                    p[x, y] = rgba(S[0])
    for y in range(FW):            # 불씨 테 빛 쪽(위·왼쪽) 한 단 밝게
        for x in range(FW):
            t = min(x, y, FW - 1 - x, FW - 1 - y)
            if t == 21 and (y == 21 or x == 21) and not (y == FW - 22 or x == FW - 22):
                p[x, y] = rgba(A[6])
            elif t == 20 and (y == FW - 21 or x == FW - 21):
                p[x, y] = rgba(A[1])
    d = ImageDraw.Draw(im)
    r = random.Random(531)
    # 모서리 쇠붙이(네 귀) — 모서리 SLICE 칸 안에만
    for (cx, cy, sx, sy) in ((0, 0, 1, 1), (FW - 1, 0, -1, 1), (0, FW - 1, 1, -1), (FW - 1, FW - 1, -1, -1)):
        pts = [(cx, cy), (cx + sx * 30, cy), (cx + sx * 30, cy + sy * 8), (cx + sx * 8, cy + sy * 8), (cx + sx * 8, cy + sy * 30),
               (cx, cy + sy * 30)]
        d.polygon(pts, fill=rgba(G[4]))
        d.line([(cx + sx * 1, cy + sy * 1), (cx + sx * 29, cy + sy * 1)], fill=rgba(G[7]))
        d.line([(cx + sx * 1, cy + sy * 1), (cx + sx * 1, cy + sy * 29)], fill=rgba(G[6]))
        d.line([(cx + sx * 30, cy), (cx + sx * 30, cy + sy * 8), (cx + sx * 8, cy + sy * 8), (cx + sx * 8, cy + sy * 30),
                (cx, cy + sy * 30)], fill=rgba(G[1]))
        for (ox, oy) in ((4, 4), (22, 4), (4, 22)):
            x, y = cx + sx * ox, cy + sy * oy
            p[x, y] = rgba(G[9])
            p[x + sx, y + sy] = rgba(G[2])
        # 녹 점
        for _ in range(6):
            ox, oy = r.randint(2, 28), r.randint(2, 6)
            if r.random() < 0.5:
                ox, oy = oy, ox
            x, y = cx + sx * ox, cy + sy * oy
            if p[x, y][:3] == G[4]:
                p[x, y] = rgba(A[1] if r.random() < 0.6 else A[2])
        # 귀 안쪽 잔(盞) 문양 정(쇠 판 끝, 11~19)
        gx, gy = cx + sx * 14, cy + sy * 14
        for (ox, oy) in ((-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (-2, -1), (2, -1), (-1, 0), (1, 0), (0, 1), (0, 2), (-1, 2), (1, 2)):
            p[gx + ox, gy + oy] = rgba(A[6])
    # 모서리 그을음 금(불씨가 숨은 균열) — 모서리 칸 안 나무 몸에만
    for (cx, cy, sx, sy) in ((0, 0, 1, 1), (FW - 1, 0, -1, 1), (0, FW - 1, 1, -1), (FW - 1, FW - 1, -1, -1)):
        x, y = cx + sx * 33, cy + sy * 10
        for k in range(7):
            if 0 <= x < FW and 0 <= y < FW and 5 <= min(x, y, FW - 1 - x, FW - 1 - y) <= 15:
                p[x, y] = rgba(A[4] if k % 2 else A[3])
            x += sx
            y += sy * (1 if k % 3 == 0 else 0)
    return im


def fate_meta():
    return {
        "slice": {"left": SLICE, "right": SLICE, "top": SLICE, "bottom": SLICE},
        "inner": INNER,
        "innerNote": "그림(무기 미리보기 looks/<무기>_base 192×192) 이 들어가는 칸 = 바깥에서 36px 안쪽. 그 안은 투명 — 뒤에 어두운 판(G01 등)을 깔거나 그대로 둔다",
        "minSize": [96, 96],
        "layers": "0 먹 테 · 1~2 옻칠 모따기 · 3~15 그을린 나무(변 방향 결) · 16~19 홈 · 20~22 불씨 테(호박, 21 = #d67a11 자체 발광) · 23 먹 · 24~33 먹 매트 · 34~35 그림 홈",
        "emberLine": {"inset": 21, "color": "#d67a11", "note": "운명이 드러나는 순간 이 테를 ADD 로 한 번 밝혀도 된다(펄스 제안 0.6→1.0→0.8, 600ms)"},
        "cornerArt": "네 귀 = 쇠 모서리판(리벳 3·녹)·잔 문양 정(호박)·그을음 금 — 모서리 40 칸 안에만. 변 조각은 무늬 없음(늘려도 그대로)",
        "suggestedSize": {"w": 264, "h": 264, "note": "looks 192 를 1배로 담을 때 = 192 + 36×2. 화면 가운데(348,96) 권장, 아래 '왜' 한 줄은 y 372~"},
    }


# ------------------------------------------------------------------ 수련장 나무 팻말 (P1-17, 3-slice 가로)
PLANK_W, PLANK_H, PLANK_SLICE = 48, 24, 14


def plank_label():
    """허수아비·과녁 이름표 자리: 끈 두 가닥에 매단 낡은 나무 팻말. 가운데 조각은 가로 결만(늘려도 그대로).
    색: v2 나무 WD · 무채(못·끈) — 글자는 UI(Galmuri, ink_body 결 G14 + 먹 그늘)."""
    import sys as _s
    _s.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "v2_outer"))
    from kit import WD, SL, PL  # noqa: E402
    im = Image.new("RGBA", (PLANK_W, PLANK_H), CLEAR)
    p = im.load()
    top, bot = 6, PLANK_H - 2
    for y in range(top, bot + 1):
        for x in range(1, PLANK_W - 1):
            t = y - top
            # 모서리 깎임(왼·오른 끝 2도트)
            if (x in (1, PLANK_W - 2)) and t in (0, bot - top):
                continue
            if t == 0:
                col = WD[5]
            elif t == bot - top:
                col = SL[0]
            elif t == bot - top - 1:
                col = WD[1]
            elif t in (5, 11):
                col = WD[2]                    # 판자 이음 결
            else:
                col = WD[3] if t % 4 else WD[4]
            if x in (1, PLANK_W - 2):
                col = SL[0] if x == PLANK_W - 2 else WD[2]
            p[x, y] = col if len(col) == 4 else (*col, 255)
    # 못 · 끈(모서리 조각 안)
    for nx in (6, PLANK_W - 7):
        for (dx, dy, col) in ((0, 0, G[8]), (1, 0, G[5]), (0, 1, G[5]), (1, 1, G[3])):
            p[nx + dx, top + 3 + dy] = rgba(col[:3])
        for k in range(top + 3):
            x = nx + (0 if k < 2 else (1 if nx < 20 else 0))
            p[x, k] = (*PL[2][:3], 255) if k % 2 else (*PL[1][:3], 255)
    # 모서리 갈라짐 · 그을음
    for (x, y) in ((3, top + 9), (4, top + 10), (PLANK_W - 5, top + 2), (PLANK_W - 4, top + 3)):
        p[x, y] = (*SL[0][:3], 255)
    return im


PLANK_META = {
    "slice": {"left": PLANK_SLICE, "right": PLANK_SLICE, "top": 0, "bottom": 0},
    "kind": "3-slice 가로(Phaser NineSlice top/bottom 0)",
    "textArea": {"x": 6, "y": 8, "h": 13, "note": "글자 띠(팻말 판 안쪽, y 8~20). 폭은 늘린 만큼 — 좌우 여백 6"},
    "textStyle": "ink_body(G14 #ebeced + 강조 20 할로 0.5 + 먹 그늘) 또는 ink_faint. Galmuri11, 정수 좌표",
    "hangAnchor": {"x": 0.5, "y": 0.0, "note": "끈 위 끝 = 팻말 원점(위 가운데). 대상(허수아비 headTop) 위 8~12 논리 px 에"},
    "use": "P1-17 — 수련장·시험장 고정폭 디버그 라벨('사수 허수아비 · 7발' 등) 대신. 수치 표시는 시스템/UI 판단(점검: 수치 노출 금지 권장)",
}
