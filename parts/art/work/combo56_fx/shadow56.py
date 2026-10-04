"""56라운드 Q3 그림자 분신 — fx/v3/katana_issen_shadow.

주인공 v3 일섬 몸 + 칼(player_katana_issen · weapons/v3/katana_issen) 프레임을 어두운 재 실루엣으로 바꾼다.
  · 색: 어두운 재 4단(#141516 → #45403b) 순서 디더 + 앞쪽 가장자리 불씨 테(A18) + 균열·눈은 꺼져 가는 호박(A18/A19), 칼날 선 A19.
  · 반투명 없음 — 뒤쪽 35%는 베이어 디더로 픽셀을 비워 '달리는 잔상'처럼 끌리게, 뒤로 속도선 3줄(재).
  · 소멸: 2×2 덩어리로 부서져 재 조각이 뒤·위로 흩날리고 불티 몇 개.
프레임: 0~2 달리기(일섬 돌진 4·5·6 자세) 50ms씩 = 150ms 이동 · 3 도착 베기(7 자세) 60 · 4~7 소멸 50/60/70/80.
"""
import json
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fx56 as F  # noqa: E402
from brush import W  # noqa: E402

ROOT = F.X.W.OUT_FX.rsplit("/assets/", 1)[0]
P3 = os.path.join(ROOT, "assets/sprites/player/v3")
W3 = os.path.join(ROOT, "assets/sprites/weapons/v3")
NAME = "katana_issen_shadow"
POSE = [4, 5, 6, 7, 7, 7, 7, 7]                     # 몸 프레임
MS = [50, 50, 50, 60, 50, 60, 70, 80]
TRAVEL = [0, 1, 2]
VANISH = [4, 5, 6, 7]
DARK = ["#141516", "#212224", "#2f3033", "#45403b"]
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
DV = {"right": (1, 0), "left": (-1, 0), "down": (0, 1), "up": (0, -1)}
PAD = 72


def rgb(h):
    return W.hexrgb(h)


def load(folder, name):
    j = json.load(open(os.path.join(folder, name + ".json"), encoding="utf-8"))
    return j, Image.open(os.path.join(folder, name + ".png")).convert("RGBA")


def cell(j, im, d, i):
    r = j["directions"].index(d)
    fw, fh = j["frameWidth"], j["frameHeight"]
    return im.crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh))


def compose(bj, bim, wj, wim, d, i):
    fw, fh = wj["frameWidth"], wj["frameHeight"]
    c = Image.new("RGBA", (fw + 2 * PAD, fh + 2 * PAD), (0, 0, 0, 0))
    ox, oy = wj["playerFrameOffset"]["x"], wj["playerFrameOffset"]["y"]
    c.alpha_composite(cell(bj, bim, d, i), (PAD + ox, PAD + oy))
    body_mask = c.getchannel("A").point(lambda a: 255 if a else 0)
    c.alpha_composite(cell(wj, wim, d, i), (PAD, PAD))
    return c, body_mask


def silhouette(c, body_mask, d, travel, k_vanish, seed):
    W_, H_ = c.size
    src = c.load()
    bm = body_mask.load()
    out = Image.new("RGBA", c.size, (0, 0, 0, 0))
    px = out.load()
    dx, dy = DV[d]
    pts = [(x, y) for y in range(H_) for x in range(W_) if src[x, y][3]]
    if not pts:
        return out
    proj = [x * dx + y * dy for x, y in pts]
    pmin, pmax = min(proj), max(proj)
    ys = [y for _, y in pts]
    ymin, ymax = min(ys), max(ys)
    for (x, y), p in zip(pts, proj):
        r, g, b, a = src[x, y]
        u = (p - pmin) / max(1, pmax - pmin)                  # 0 = 뒤, 1 = 앞(돌진 방향)
        bay = (BAYER[y % 4][x % 4] + 0.5) / 16
        if travel and u < 0.38 and bay < (0.38 - u) / 0.38 * 0.9:
            continue                                          # 뒤쪽 디더 비움(잔상 끌림)
        if k_vanish > 0:
            hv = W.h2(x >> 1, y >> 1, seed)
            top = (y - ymin) / max(1, ymax - ymin)            # 위쪽부터 먼저 부서짐
            if hv < k_vanish * 1.25 - 0.35 * top:
                continue
        lum = 0.3 * r + 0.59 * g + 0.11 * b
        amber = r > g + 35 and lum > 165                      # 균열·눈·날선 빛만(주머니 같은 갈색 소품은 어둡게)
        if amber:
            col = W.A19 if bm[x, y] else W.A18
        else:
            f = min(0.999, max(0.0, (lum - 20) / 110.0)) * 3
            lo = int(f)
            col = DARK[min(3, lo + (1 if (f - lo) > bay else 0))]
        # 가장자리
        nb_front = (x + dx, y + dy)
        edge_front = not (0 <= nb_front[0] < W_ and 0 <= nb_front[1] < H_) or src[nb_front][3] == 0
        if edge_front and not amber:
            col = W.A19 if travel else W.A18
        elif (y - 1 < 0 or src[x, y - 1][3] == 0) and not amber:
            col = DARK[3]
        px[x, y] = rgb(col) + (255,)
    return out


def streaks(out, d, i, seed):
    """뒤로 끌리는 속도선 3줄(재) — 달리기 프레임만."""
    fr = F.frame(None)
    fr.w, fr.h = out.size
    Ls = fr.L([W.S0, DARK[2], DARK[3]])
    a = out.getchannel("A")
    bb = a.getbbox()
    if not bb:
        return out
    dx, dy = DV[d]
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    r = random.Random(seed + i)
    for j, lat in enumerate((-22, -4, 14)):
        ln = r.uniform(34, 58) * (1.15 if j == 1 else 0.85)
        if dx:
            back_x = bb[0] if dx > 0 else bb[2]
            p0 = (back_x + dx * 6, cy + lat + 6)
            p1 = (p0[0] - dx * ln, p0[1])
        else:
            back_y = bb[1] if dy > 0 else bb[3]
            p0 = (cx + lat, back_y + dy * 4)
            p1 = (p0[0], p0[1] - dy * ln)
        Ls.stroke([p0, p1], 1.1 - 0.2 * abs(j - 1), prof=W.FK.tp_tail(1.1), v=0.85 - 0.15 * abs(j - 1))
    img = Image.new("RGBA", out.size, (0, 0, 0, 0))
    fr.render(img)
    img.alpha_composite(out)
    return img


def ash(out, d, k, seed):
    """소멸: 부서진 재 조각이 뒤·위로 흩날림 + 불티."""
    fr = F.frame(None)
    fr.w, fr.h = out.size
    Lf = fr.L([W.S0, W.S1, W.S2])
    Le = fr.L([W.A18, W.A19, W.A21])
    bb = out.getchannel("A").getbbox() or (out.width // 2 - 20, out.height // 2 - 60, out.width // 2 + 20, out.height // 2 + 40)
    dx, dy = DV[d]
    r = random.Random(seed)
    for j in range(26):
        x = r.uniform(bb[0], bb[2])
        y = r.uniform(bb[1], bb[1] + (bb[3] - bb[1]) * 0.8)
        t = k * r.uniform(0.7, 1.3)
        fx = x - dx * 18 * t + r.uniform(-6, 6) * t
        fy = y - dy * 18 * t - 16 * t + 10 * t * t
        if r.random() < k * 0.5:
            continue
        W.flake(Lf, fx, fy, r.uniform(1.0, 2.2) * (1 - 0.3 * k), r.uniform(0, 6), v=r.uniform(0.5, 1.0))
    if k < 0.75:
        for j in range(5):
            x = r.uniform(bb[0], bb[2])
            y = r.uniform(bb[1], bb[3] - 20)
            W.ember(Le, x - dx * 10 * k, y - 14 * k, -dx * 0.3, -1, 3 * (1 - k), w=0.6, v=0.9 - 0.4 * k)
    img = Image.new("RGBA", out.size, (0, 0, 0, 0))
    fr.render(img)
    img.alpha_composite(out)
    return img


def build():
    bj, bim = load(P3, "player_katana_issen")
    wj, wim = load(W3, "katana_issen")
    frames = {}
    for d in F.DIRS4:
        lst = []
        for i, pose in enumerate(POSE):
            c, bm = compose(bj, bim, wj, wim, d, pose)
            if i in TRAVEL:
                s = silhouette(c, bm, d, True, 0.0, 91)
                s = streaks(s, d, i, 93)
            elif i in VANISH:
                k = (VANISH.index(i) + 1) / len(VANISH)
                s = silhouette(c, bm, d, False, k, 92 + i)
                s = ash(s, d, k, 95)
            else:
                s = silhouette(c, bm, d, False, 0.0, 91)
            lst.append(s)
        frames[d] = lst
    # 자르기: 합집합 상자(피벗 포함)
    fw, fh = wj["frameWidth"], wj["frameHeight"]
    piv = (PAD + wj["pivot"]["x"], PAD + wj["pivot"]["y"])
    box = [piv[0], piv[1], piv[0] + 1, piv[1] + 1]
    for lst in frames.values():
        for im in lst:
            b = im.getbbox()
            if b:
                box = [min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3])]
    m = 3
    x0, y0 = box[0] - m, box[1] - m
    Wd = -(-(box[2] + m - x0) // 8) * 8
    Hd = -(-(box[3] + m - y0) // 8) * 8
    cut = {d: [im.crop((x0, y0, x0 + Wd, y0 + Hd)) for im in lst] for d, lst in frames.items()}
    pivot = (piv[0] - x0, piv[1] - y0)
    d0 = bj["dash"]["startMs"]
    upd = dict(weapon="katana", design="그림자 분신(Q3) — 일섬 0.2초 뒤 같은 선을 달려 베고 재로 부서져 사라지는 어두운 재 실루엣(주인공 v3 일섬 자세 기반). "
                                       "반투명 대신 어두운 재 4단 디더 · 뒤쪽 디더 비움 · 불씨 테",
               anchor="issen_shadow_path", pivot={"x": pivot[0], "y": pivot[1]},
               anchorNote="pivot = 분신의 발. travelFrames 동안 일섬 출발 피벗 → 도착 피벗(주인공이 실제로 멈춘 자리)으로 선형 이동, 그 뒤 프레임은 도착 피벗에 고정. 행 = 돌진 방향",
               spawn="body_ms", spawnAtMs=d0 + F.ISSEN_SHADOW_AT, spawnNote="katana_issen 몸 시트 기준(돌진 시작 + 200ms)",
               travelFrames=TRAVEL, travelMs=sum(MS[i] for i in TRAVEL), slashFrame=3, vanishFrames=VANISH,
               damageScale=0.5, hitShapeRef="player_katana_issen.hitShape(같은 선 — 실제 이동 거리로)",
               hitTimingOptions={"A(아트 제안)": "도착 순간 1회 = 일섬 선 터짐 프레임(katana_issen_line burstFrame, 몸 기준 %dms)" % (d0 + F.ISSEN_SHADOW_AT + 150),
                                 "B": "travelFrames 동안 분신 위치 주변 판정(지나가며 벰)"},
               depth="같은 Y 정렬(주인공처럼) — 조명 위가 아니라 일반 스프라이트 깊이 권장",
               lit=False, litNote="어두운 실루엣이라 조명(라이트맵) 아래·위 어느 쪽이든 읽힘 — fx 규칙대로 조명 위 권장",
               basedOn="player_katana_issen f%s + weapons/v3/katana_issen" % sorted(set(POSE)),
               frameRoles=["달리기(칼 앞으로)", "달리기(가로 긋기)", "달리기(지나감)", "도착 베기(잔심)", "소멸 1(위부터 부서짐)", "소멸 2", "소멸 3", "소멸 4"])
    sheet, j, _ = F.write(NAME, cut, F.DIRS4, MS, None, upd, None, F.X.W.OUT_FX)
    # 반투명·색 검사는 write 가 함. 백열 금지(분신은 판정 프레임이어도 어둡게)
    hot = {W.X0, W.X1, W.A26, W.A25}
    assert not (W.colors_of(sheet) & hot), "분신에 밝은 색"
    print(NAME, j["frameWidth"], j["frameHeight"], "colors", j["colors"])
    return j
