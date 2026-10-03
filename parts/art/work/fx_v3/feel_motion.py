"""feel_motion — 움직임·행동 이펙트 데드셀 밀도 개선 (55라운드 Q1 '움직임·잔상').

dash_trail · dash_dust · parry_flash · guard_wave · ironwall · shadowstep_ghost · aim_charge.
의미 필드(anchor·spawn·depth·tint·flash·progressDriven·weapon …)는 이전 JSON 에서 그대로 옮기고,
프레임 수·ms 를 바꾼 시트는 JSON `previous` 에 이전 값을 남긴다.
"""
import json
import math
import os

from PIL import Image

from fxkit import Canvas, tp_both, tp_tail, tp_head, DIRS, DVEC
from feel_kit import (HERO, TAU, GROUND, UPRIGHT, sparks, chips, dots, needle, rng, hexrgb,
                      X0, X1, A17, A18, A19, A21, A23, A25, A26, B0, B1, B2, B3, S0, S1, S2, S3,
                      R_FLASH, R_FLASH2, R_WARM, R_COOL, R_DIM, R_DUST, R_DUSTD, R_FLAKE)

BEFORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feel", "before")
D2R = math.pi / 180
KEEP = ["anchor", "spawn", "depth", "followsPlayer", "weapon", "tint", "flash", "progressDriven", "design",
        "designRef", "heroSource", "heroSizeCheck", "legacy", "pivotNote", "tailFrames", "secondary"]


def old_json(name):
    return json.load(open(os.path.join(BEFORE, name + ".json")))


def carry(name, frames_ms, extra=None):
    o = old_json(name)
    m = {k: o[k] for k in KEEP if k in o}
    m["frameDurationsMs"] = frames_ms
    m["action"] = o.get("action", name)
    if len(frames_ms) != len(o["frameDurationsMs"]) or frames_ms != o["frameDurationsMs"]:
        m["previous"] = {"frames": len(o["frameDurationsMs"]), "frameDurationsMs": o["frameDurationsMs"],
                         "totalMs": sum(o["frameDurationsMs"]), "source": o.get("source")}
    if extra:
        m.update(extra)
    return m


def put(img, x, y, col):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((int(x), int(y)), hexrgb(col) + (255,))


# ---------------------------------------------------------------- hero silhouettes
def _is_amber(p):
    r, g, b, a = p
    return a and r > 170 and r - b > 90 and g > 70


def hero_cells(sheet, col):
    im = Image.open(os.path.join(HERO, sheet + ".png")).convert("RGBA")
    j = json.load(open(os.path.join(HERO, sheet + ".json")))
    fw, fh = j["frameWidth"], j["frameHeight"]
    out = {}
    for r, d in enumerate(j["directions"]):
        c = im.crop((col * fw, r * fh, (col + 1) * fw, (r + 1) * fh))
        px = c.load()
        mask = {(x, y) for y in range(fh) for x in range(fw) if px[x, y][3]}
        amber = {(x, y) for (x, y) in mask if _is_amber(px[x, y])}
        out[d] = (mask, amber)
    return out, fw, fh, j["pivot"]


# ======================================================================
# dash_trail — 재 실루엣 잔상: 호박 균열이 남은 채 이동 반대쪽으로 번지고(줄 끌림) 재로 부서짐
def dash_trail():
    cells, FW, FH, piv = hero_cells("player_dash", 2)
    out = {}
    for d in DIRS:
        mask, amber = cells[d]
        dx, dy = DVEC[d]
        bx, by = -dx, -dy                                   # 뒤쪽
        ys = [y for _, y in mask]
        top, bot = min(ys), max(ys)
        R = rng(91 + DIRS.index(d))
        frames = []
        for f in range(4):
            im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
            lane_of = (lambda x, y: y) if dx else (lambda x, y: x)
            for (x, y) in mask:
                lane = lane_of(x, y)
                h = (y - top) / max(1, bot - top)
                back = (x + bx, y + by) not in mask
                front = (x - bx, y - by) not in mask
                if f == 1 and lane % 4 == 0:
                    continue
                if f == 2 and lane % 3 != 1:
                    continue
                if f == 3:
                    continue
                if (x, y) in amber:
                    col = [A23, A21, A19][f]
                elif back:
                    col = [S1, S0, B2][f]
                elif front:
                    col = [B0, B0, B0][f]
                else:
                    col = [B1 if h < 0.5 else B0, B1, B0][f]
                # 앞으로 밀려 나가는 모양: 프레임마다 몸이 뒤로 1~3도트 미끄러짐
                sx, sy = x + bx * [0, 2, 5, 0][f], y + by * [0, 2, 5, 0][f]
                put(im, sx, sy, col)
            # 줄 끌림: 각 줄의 뒤쪽 끝에서 뒤로 끌리는 꼬리
            if f in (0, 1, 2):
                lanes = {}
                for (x, y) in mask:
                    lane = lane_of(x, y)
                    if f == 1 and lane % 4 == 0 or f == 2 and lane % 3 != 1:
                        continue
                    key = lane
                    along = x * bx + y * by                  # 클수록 뒤
                    if key not in lanes or along > lanes[key][0]:
                        lanes[key] = (along, x, y)
                for lane, (_, x, y) in lanes.items():
                    if (lane * 7) % 5 > (2 if f == 0 else 3):
                        continue
                    if dy and lane % 3:                      # 상하 대쉬: 꼬리 줄을 듬성하게(머리카락처럼 보이지 않게)
                        continue
                    ln = ([5, 9, 12][f] + (lane * 13) % 5) * (0.6 if dy else 1.0)
                    ln = int(ln)
                    for k in range(1, ln):
                        if f > 0 and k > ln * 0.6 and (k + lane) % 2:
                            continue
                        put(im, x + bx * ([0, 2, 5][f] + k), y + by * ([0, 2, 5][f] + k),
                            [S0, B2, B1][f] if k < ln * 0.4 else [B2, B1, B1][f])
            # 재 조각·불씨: 뒤쪽 가장자리에서 떨어져 뒤·위로
            if f >= 1:
                cv = Canvas(FW, FH)
                C = cv.layer(R_FLAKE)
                E = cv.layer(R_DIM)
                pts = sorted(mask)
                for i in range([0, 12, 16, 18][f]):
                    x, y = pts[R.randrange(len(pts))]
                    s = (5 + 7 * f) * R.uniform(0.5, 1.2)
                    cx, cy = x + bx * s, y + by * s - s * 0.45
                    C.stroke([(cx - 1, cy), (cx + 1, cy - 0.6)], 0.7, prof=tp_both(0.5), v=R.uniform(0.5, 1.0) * (1.1 - 0.2 * f), soft=0.5)
                am = sorted(amber)
                for i in range([0, 3, 5, 6][f] if am else 0):
                    x, y = am[R.randrange(len(am))]
                    s = (4 + 6 * f) * R.uniform(0.6, 1.2)
                    E.stamp(x + bx * s * 0.6, y + by * s * 0.6 - s * 0.7, 0.6, R.uniform(0.6, 1.0), soft=0.2)
                im.alpha_composite(cv.render())
            frames.append(im)
        out[d] = frames
    return out, carry("dash_trail", [30, 40, 50, 70], {
        "note": ("v3 55R: 주인공 v3 대쉬 프레임 2 실루엣 — f0 재 몸(갈색 재 위아래 명암) + 뒤쪽 가장자리 밝은 재 테두리 + "
                 "몸의 호박 균열 자리 그대로 A23 → f1 이동 줄 4개 중 1줄 빠짐 + 줄 뒤끝이 뒤로 끌림(재 꼬리) + 재 조각 "
                 "떨어져 나감 → f2 줄 3개 중 1줄만, 몸이 뒤로 5도트 밀림, 균열 A19 → f3 몸 없이 재 조각·불씨만."),
        "pivot": piv})


# ======================================================================
# dash_dust — 발 뒤로 박차 오르는 재 먼지 + 바닥 긁힘 줄 + 흙 알갱이
def dash_dust():
    W, H, px, py = 96, 48, 48, 36
    out = {}
    for d in DIRS:
        G = GROUND[d]
        frames = []
        for f in range(4):
            cv = Canvas(W, H)
            Sk = cv.layer([B0, B1, B2])                      # 바닥 긁힘 줄
            Gr = cv.layer(R_DUSTD + [S1])                   # 알갱이
            Dd = cv.layer(R_DUST)                           # 먼지 덩이
            M = lambda u, w: (px + G(u, w)[0], py + G(u, w)[1])
            # 긁힘: 발 뒤 2줄, f0~f2
            if f < 3:
                for side in (-1, 1):
                    l0, l1 = [-4, -6, -10][f], [-22, -34, -40][f]
                    Sk.stroke([M(l1, side * 5), M(l0, side * 4)], 1.0, prof=tp_head(0.7), v=[1.0, 0.9, 0.6][f])
            # 먼지 덩이: 발에서 뒤로 작아지는 4~5개, 옆으로 V 자로 벌어짐
            lobes = ((0.1, 1.0, 0.0), (0.4, 0.85, -1), (0.62, 0.72, 1), (0.85, 0.6, -0.5), (1.0, 0.45, 0.8))
            reach = [16, 30, 40, 46][f]
            for i, (far, sz, side) in enumerate(lobes):
                if f == 0 and i > 2:
                    continue
                u = -reach * far
                w = side * (4 + 4 * f) * (1.6 if d in ("up", "down") else 1.0)
                x, y = M(u, w)
                y -= (1.5 * f + i * 1.0) * 1.5
                r = [5.0, 7.5, 8.5, 7.0][f] * sz
                if f < 3:
                    Dd.cloud(x, y, r, v=[1.0, 0.92, 0.78][f], flat=0.62, seed=i + 3 * f)
                else:
                    Gr.cloud(x, y - 1, r * 0.6, v=0.7, flat=0.6, seed=i)
            # 알갱이 줄기: 뒤·위로 튐
            n = [5, 7, 6, 4][f]
            gl = [12, 24, 32, 36][f]
            import random as _r
            R = _r.Random(71 + DIRS.index(d))
            for k in range(n):                             # 알갱이: 뒤로 낮게 튀는 2~3도트 조각(세로 막대 금지)
                w = R.uniform(-12, 12)
                u = -gl * R.uniform(0.7, 1.15)
                x1, y1 = M(u, w)
                x0, y0 = M(u + [3, 2.5, 2, 1.5][f], w)
                lift = [2, 4, 5, 4][f] * R.uniform(0.5, 1.2)
                Gr.stroke([(x0, y0 - lift), (x1, y1 - lift - 0.6)], 0.7, prof=tp_both(0.5), v=R.uniform(0.6, 1.0), soft=0.5)
            cv.layers = [Sk, Dd, Gr] if f < 3 else [Sk, Gr, Dd]
            frames.append(cv.render())
        out[d] = frames
    return out, carry("dash_dust", [40, 50, 60, 80], {
        "note": ("v3 55R: 주인공 1.5배(×6). f0 발 뒤 바닥 긁힘 2줄 + 작은 먼지 3덩이 + 알갱이 → f1~f2 뒤로 작아지는 "
                 "재 먼지 5덩이(윗면 밝게, 상하 대쉬는 V 자) + 뒤·위로 튀는 알갱이 → f3 어두운 작은 덩이로 꺼짐."),
        "pivot": {"x": px, "y": py}})


# ======================================================================
# parry_flash — 시간이 멈추는 섬광: 가로 렌즈 줄 + 두꺼운 충격 고리 + 불티 폭발
def parry_flash():
    W = 192
    c = W / 2

    def frame(f):
        cv = Canvas(W, W)
        M = lambda u, v: (c + u, c + v)
        if f == 0:
            G = cv.layer(R_COOL)
            G.disc(c, c, 18, v=0.95, edge=0.5)
            G.stroke([(c - 90, c), (c + 90, c)], 3.6, prof=tp_both(0.7, 0.5), v=0.9)
            L = cv.layer(R_FLASH)
            L.stroke([(c - 92, c), (c + 92, c)], 1.8, prof=tp_both(0.7, 0.5), v=1.0)
            L.stroke([(c, c - 50), (c, c + 50)], 1.5, prof=tp_both(0.7, 0.5), v=0.95)
            for k in range(4):
                needle(L, M, TAU / 8 + k * TAU / 4, 4, 18, 1.1, 0.85)
            L.disc(c, c, 11, v=1.0, edge=0.55)
        elif f == 1:
            G = cv.layer(R_COOL)
            G.ring(c, c, 26, 6.0, v=0.9)
            L = cv.layer(R_FLASH2)
            L.ring(c, c, 26, 3.4, v=0.95)
            sparks(L, M, 14, 34, 60, 16, 1.2, 0.9, seed=801, bend=4)
            L.stroke([(c - 70, c), (c + 70, c)], 1.0, prof=tp_both(0.7, 0.5), v=0.75)
            L.star4(c, c, 9, 1.2, 0.85)
        elif f == 2:
            L = cv.layer(R_WARM)
            for a0 in (10, 130, 250):
                L.arc(c, c, 42, 42, a0 * D2R, (a0 + 96) * D2R, 2.6, prof=tp_both(0.6), v=0.9)
            sparks(L, M, 14, 56, 82, 11, 1.0, 0.88, seed=801, bend=4)
            for a in (35, 160, 290):
                L.star4(*M(math.cos(a * D2R) * 60, math.sin(a * D2R) * 60), 6, 0.9, 0.85, diag=0.5)
            C = cv.layer(R_FLAKE)
            chips(C, M, 6, 20, 36, 2.0, 0.85, seed=811)
        elif f == 3:
            L = cv.layer(R_WARM)
            L.ring(c, c, 54, 1.4, v=0.7, dash=(14, 0.5, 0.1))
            sparks(L, M, 14, 74, 92, 6, 0.85, 0.75, seed=801, bend=4)
            C = cv.layer(R_FLAKE)
            chips(C, M, 8, 28, 50, 1.8, 0.8, seed=812)
        elif f == 4:
            L = cv.layer(R_COOL)
            L.ring(c, c, 62, 1.0, v=0.75, dash=(16, 0.3, 0.3))
            dots(L, M, 12, 80, 94, 0.9, seed=801, size=0.8)
            C = cv.layer(R_FLAKE)
            chips(C, M, 8, 36, 60, 1.5, 0.7, seed=813)
        else:
            L = cv.layer(R_DIM)
            dots(L, M, 9, 84, 95, 0.8, seed=802)
            C = cv.layer(R_FLAKE)
            chips(C, M, 6, 44, 68, 1.3, 0.6, seed=814)
        return cv.render()
    return {"any": [frame(i) for i in range(6)]}, carry("parry_flash", [30, 40, 50, 60, 80, 100], {
        "note": ("v3 55R: f0 백열 코어 + 가로로 긴 렌즈 줄(±92) + 세로 줄 → f1 두꺼운 충격 고리 r26 + 휘어 나가는 "
                 "불티 14 → f2 고리가 세 토막으로 깨지며 r42 + 글린트 3 + 재 조각 → f3 점선 고리 → f4~f5 불씨·재. "
                 "백열은 f0~f1(Q65)."),
        "pivot": {"x": 96, "y": 96}})


# ======================================================================
# guard_wave — 대검 밀쳐내기: 바닥을 쓸고 나가는 녹·흙 띠 + 이 빠진 혼불 선 + 먼지
def guard_wave():
    W, H, px, py = 256, 128, 128, 64
    notches = (-38, 6, 44)                                     # 이 빠진 자리(각도)
    out = {}
    for d in DIRS:
        G = GROUND[d]
        M = lambda u, w: (px + G(u, w)[0], py + G(u, w)[1])
        frames = []
        for f in range(5):
            cv = Canvas(W, H)
            r = [42, 70, 90, 104, 112][f]
            span = [62, 70, 74, 76, 76][f] * D2R
            D = cv.layer(R_DUST)
            Bd = cv.layer([B1, B2, B3, A18])                   # 녹·흙 띠
            E = cv.layer([R_FLASH, R_WARM, R_WARM, R_COOL, R_DIM][f])
            C = cv.layer(R_FLAKE)

            def arc(rad, a0, a1, n=60):
                return [M(math.cos(a0 + (a1 - a0) * i / n) * rad, math.sin(a0 + (a1 - a0) * i / n) * rad)
                        for i in range(n + 1)]
            # 띠: 앞(가장 바깥)이 굵고 끝이 뾰족
            if f < 4:
                bw = [5.0, 6.0, 5.0, 3.2][f]
                Bd.stroke(arc(r - bw, -span, span), bw, prof=tp_both(0.55, 0.5), v=[1.0, 0.95, 0.85, 0.7][f],
                          dash=None if f < 3 else (14, 0.6, 0.2))
            # 혼불 선: 이 빠진 자리마다 끊김
            if f < 4:
                segs = [-span] + [a * D2R for a in notches] + [span]
                for i in range(len(segs) - 1):
                    a0, a1 = segs[i] + 0.06, segs[i + 1] - 0.06
                    if a1 <= a0:
                        continue
                    E.stroke(arc(r, a0, a1, 24), [2.0, 1.7, 1.4, 1.0][f], prof=tp_both(0.5, 0.5),
                             v=[1.0, 0.95, 0.9, 0.8][f], dash=None if f < 2 else (12, 0.65, 0.1 * i))
            # 먼지: 띠 양 끝·뒤쪽에서 피어오름
            if f >= 1:
                for i, a in enumerate((-span * 0.95, -span * 0.45, 0, span * 0.45, span * 0.95)):
                    rr = r - [0, 6, 10, 12, 14][f]
                    x, y = M(math.cos(a) * rr, math.sin(a) * rr)
                    rad = [0, 6, 8.5, 10, 9][f] * (1.15 if abs(a) > span * 0.8 else 0.85)
                    if f < 4:
                        D.cloud(x, y - 2 * f, rad, v=[0, 1.0, 0.9, 0.75][f], flat=0.62, seed=i + f)
                    else:
                        C.cloud(x, y - 8, rad * 0.55, v=0.65, flat=0.6, seed=i)
            # 재 조각·불씨: 앞으로 튐
            sp = [0, 6, 8, 8, 6][f]
            import random as _r
            R = _r.Random(91 + DIRS.index(d))
            for k in range(sp):
                a = R.uniform(-span, span)
                rr = r + R.uniform(4, 14)
                x, y = M(math.cos(a) * rr, math.sin(a) * rr)
                C.stroke([(x - 1.2, y), (x + 1.2, y - 0.8)], 0.9, prof=tp_both(0.5), v=R.uniform(0.6, 1.0), soft=0.5)
            if f >= 2:
                for k in range(4):
                    a = R.uniform(-span, span)
                    rr = r + R.uniform(-2, 10)
                    x, y = M(math.cos(a) * rr, math.sin(a) * rr)
                    E.stamp(x, y - R.uniform(2, 8), 0.6, 0.85, soft=0.2)
            cv.layers = [D, Bd, E, C]
            frames.append(cv.render())
        out[d] = frames
    return out, carry("guard_wave", [40, 50, 60, 70, 90], {
        "note": ("v3 55R: 대검 A 녹슨 양손검 — 발 앞 바닥(세로 0.5)을 쓸고 나가는 녹·흙 띠 r42→112(구 판정 29×4 안팎) + "
                 "바깥 가장자리 혼불 선(이 빠진 자리 3곳에서 끊김, f0 백열 → 호박 → 점선) + 띠 끝·뒤에서 피는 재 먼지 + "
                 "앞으로 튀는 재 조각·불씨 → f4 먼지만 남아 꺼짐."),
        "pivotNote": "피벗 (128,64) = 발. 띠 바깥 반경 112 도트(= 논리 56) 안팎, 세로 0.5(바닥).",
        "pivot": {"x": px, "y": py}})


# ======================================================================
# ironwall — 철벽: 앞에 솟는 재·쇳빛 판벽 + 혼불 균열 + 바닥 물결 → 부서져 내림
def ironwall():
    W, H, px, py = 256, 256, 128, 168
    U0, TH, HALF = 40, 10, 54                                # 정면 거리, 두께, 옆 반폭
    out = {}
    for d in DIRS:
        Up = UPRIGHT[d]
        Gd = GROUND[d]
        Hmax = 56 if d == "up" else 84
        frames = []
        for f in range(5):
            im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            rise = [0.7, 1.0, 1.0, 1.0, 0.45][f] * Hmax
            crumble = [0, 0, 0, 0.35, 0.7][f]
            pix = {}
            # 벽 몸: 녹슨 칼판 6장(판마다 높이 다르고 끝이 뾰족) — (u, w, h) 표본 → 화면.
            # 좌우 방향은 옆으로 비스듬히(면이 보이게) 기울인다.
            Rw = rng(161 + f // 3)
            npl = 6
            pw = HALF * 2 / npl
            hp = []
            for i in range(npl):
                hh = rise * (0.8 + 0.2 * ((i * 5 + 2) % 7) / 6)
                if crumble:
                    hh *= 1 - crumble * Rw.uniform(0.55, 1.1)
                hp.append(max(6.0, hh))
            for ui in range(TH):
                u = U0 + ui
                face = ui == 0
                for wi in range(-HALF * 2, HALF * 2 + 1):
                    w = wi / 2
                    i = min(npl - 1, int((w + HALF) / pw))
                    wc = -HALF + (i + 0.5) * pw
                    lw = (w + HALF) - i * pw                      # 판 안 가로 위치 0..pw
                    cap = hp[i] - abs(w - wc) * 1.1                # 뾰족한 판 끝
                    for hi in range(0, int(cap * 2) + 1):
                        h = hi / 2
                        x, y = Up(u, w, h)
                        if d in ("left", "right"):
                            x += w * 0.42 * (1 if d == "right" else -1)
                        X, Y = int(px + x), int(py + y)
                        t = h / max(1.0, hp[i])
                        top = h > cap - 2.2
                        n = ((X * 73856093) ^ (Y * 19349663) ^ (i * 83492791)) & 255
                        if crumble and top and n < 140:
                            continue                               # 부서진 윗가장자리(톱니)
                        if f == 0 and (top or lw < 1.0 or lw > pw - 1.0):
                            col = X1 if top else A25
                        elif lw > pw - 1.2:
                            col = B0                               # 판 이음새
                        elif lw < 1.2 and face:
                            col = S2                               # 판 왼쪽 밝은 모서리
                        elif top:
                            col = S3 if f < 3 else S2
                        elif face:
                            band = t * 3 + ((X + Y) % 2) * 0.35    # 띠 경계 체크 디더
                            col = [B1, S0, S1, S1][min(3, int(band))]
                            if n < 10:
                                col = B3                           # 녹 반점
                            elif n < 13 and f < 3:
                                col = A18
                        else:
                            col = [B0, B1, B2][min(2, int(t * 3))]
                        key = (X, Y)
                        if face or key not in pix:
                            pix[key] = col
            for (X, Y), col in pix.items():
                put(im, X, Y, col)
            cv = Canvas(W, H)
            Rp = cv.layer([[A19, A21, A23, A25, X1], R_WARM, R_WARM, [A18, A19, A21], [A18, A19]][f])  # 14색 안
            D = cv.layer(R_DUST)
            C = cv.layer(R_FLAKE)
            sk = 0.42 * (1 if d == "right" else -1 if d == "left" else 0)
            M3 = lambda u, w, h: (px + Up(u, w, h)[0] + w * sk, py + Up(u, w, h)[1])
            Mg = lambda u, w: (px + Gd(u, w)[0], py + Gd(u, w)[1])
            # 혼불 균열: 벽면을 가로지르는 가지 번개 (f1~f3)
            if 1 <= f <= 3:
                pts = [(-HALF * 0.85, 0.35), (-HALF * 0.4, 0.55), (-HALF * 0.1, 0.42), (HALF * 0.25, 0.66),
                       (HALF * 0.55, 0.5), (HALF * 0.8, 0.72)]
                sc = [M3(U0 - 0.5, w, min(rise, 70) * h) for w, h in pts]
                Rp.stroke(sc, [1.5, 1.2, 0.9][f - 1], prof=tp_both(0.4, 0.5), v=[0.95, 0.9, 0.8][f - 1],
                          dash=None if f < 3 else (8, 0.55, 0.1))
                for (w, h), (w2, h2) in (((-HALF * 0.1, 0.42), (-HALF * 0.2, 0.15)), ((HALF * 0.25, 0.66), (HALF * 0.35, 0.9))):
                    Rp.stroke([M3(U0 - 0.5, w, min(rise, 70) * h), M3(U0 - 0.5, w2, min(rise, 70) * h2)], 0.8, prof=tp_tail(0.7),
                              v=[0.85, 0.8, 0.7][f - 1])
            # 바닥 물결: 벽 앞으로 퍼지는 호 2개
            if f >= 1:
                for k, base in enumerate((U0 + 18, U0 + 34)):
                    rr = base + [0, 0, 12, 22, 30][f]
                    a = 0.9
                    pts = [Mg(math.cos(-a + 2 * a * i / 40) * rr, math.sin(-a + 2 * a * i / 40) * rr * 1.3)
                           for i in range(41)]
                    Rp.stroke(pts, [0, 1.4, 1.2, 1.0, 0.8][f] - 0.3 * k, prof=tp_both(0.6, 0.5),
                              v=[0, 0.85, 0.85, 0.75, 0.7][f] - 0.1 * k, dash=None if f < 3 else (10, 0.5, 0.2 * k))
            # 먼지: 벽 밑동
            if f >= 1:
                for i in range(6):
                    w = -HALF + i * HALF * 2 / 5
                    x, y = M3(U0 + 2, w, 0)
                    rad = [0, 6, 8, 9, 8][f] * (0.8 + 0.2 * (i % 2)) * (0.8 if sk else 1.0)
                    D.cloud(x, y - 2 - f, rad, v=[0, 0.95, 0.9, 0.8, 0.65][f], flat=0.6, seed=i + 7 * f)
            # 무너지는 재 조각 (f3, f4)
            if f >= 3:
                R = rng(121 + DIRS.index(d) + 10 * f)
                for k in range(14):
                    w = R.uniform(-HALF, HALF)
                    h = R.uniform(0.3, 1.0) * Hmax * (0.8 if f == 3 else 0.5)
                    x, y = M3(U0 + R.uniform(-6, 6), w, h)
                    s = R.uniform(1.2, 2.6)
                    C.stroke([(x - s, y), (x + s, y - s * 0.6)], 0.5 * s + 0.3, prof=tp_both(0.5), v=R.uniform(0.6, 1.0), soft=0.5)
            im.alpha_composite(cv.render())
            frames.append(im)
        out[d] = frames
    return out, carry("ironwall", [40, 50, 60, 80, 100], {
        "note": ("v3 55R: 대검 철벽 — 정면 40도트 앞에 녹슨 칼판 6장(옆 ±54, 높이 67~84, 판마다 끝이 뾰족, 녹 반점, 좌우 방향은 "
                 "면이 보이게 비스듬히)이 솟음(f0 백열 테두리) → f1 벽면을 가로지르는 혼불 균열 + 바닥 물결 2겹 + 밑동 먼지 → f2 물결 "
                 "퍼짐 → f3 판마다 윗부분이 톱니로 부서져 낮아지며 재 조각 → f4 낮은 밑동만 남고 꺼짐. guard_wave 와 동시."),
        "pivotNote": ("피벗 (128,168) = 발. 벽 = 정면 40~50도트·옆 ±54·높이 최대 84(위 방향은 56 — 주인공을 덜 가리게). "
                      "위(up) 방향은 벽이 주인공 뒤(화면 위)에 서므로 depthByDirection.up = below 권장."),
        "depthByDirection": {"up": "below"},
        "pivot": {"x": px, "y": py}})


# ======================================================================
# shadowstep_ghost — 출발점에 남는 재 껍데기: 호박 금이 공중에 남고 몸은 위로 재가 되어 흩어짐
def shadowstep_ghost():
    cells, FW, FH, piv = hero_cells("player_idle_free", 0)
    out = {}
    for d in DIRS:
        mask, amber = cells[d]
        ys = [y for _, y in mask]
        top, bot = min(ys), max(ys)
        R = rng(141 + DIRS.index(d))
        frames = []
        for f in range(4):
            im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
            cv0 = Canvas(FW, FH)
            P_ = cv0.layer([B0, B1])
            pr = [22, 18, 13, 8][f]
            P_.disc(piv["x"], piv["y"] - 1, pr, pr * 0.28, v=0.9, edge=0.5)
            im.alpha_composite(cv0.render())
            drop = [0.0, 0.3, 0.62, 1.0][f]                   # 아래부터 사라짐
            for (x, y) in mask:
                h = (bot - y) / max(1, bot - top)              # 0 발 .. 1 머리
                edge = any((x + ex, y + ey) not in mask for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if (x, y) in amber:
                    col = [A23, A21, A19, A18][f]
                    if f == 3 and (x + y) % 3:
                        continue
                    put(im, x, y - [0, 2, 5, 9][f], col)
                    continue
                if f == 3:
                    continue
                # 체크 구멍: drop 이 커질수록 발 쪽부터 비움
                if h < drop and (x + y) % 2:
                    continue
                if h < drop - 0.2:
                    continue
                if f == 2 and x % 3 == 0:
                    continue
                col = (S1 if f == 0 else B3) if edge else [B1, B1, B0][f]
                put(im, x, y - [0, 2, 5, 9][f], col)
            cv = Canvas(FW, FH)
            C = cv.layer(R_FLAKE)
            E = cv.layer(R_DIM)
            pts = sorted(mask)
            for i in range([0, 12, 16, 14][f]):
                x, y = pts[R.randrange(len(pts))]
                s = (6 + 8 * f) * R.uniform(0.5, 1.2)
                cx, cy = x + R.uniform(-3, 3), y - s
                C.stroke([(cx - 1, cy), (cx + 1, cy - 0.6)], 0.7, prof=tp_both(0.5), v=R.uniform(0.5, 1.0), soft=0.5)
            am = sorted(amber)
            for i in range([0, 3, 5, 6][f] if am else 0):
                x, y = am[R.randrange(len(am))]
                E.stamp(x + R.uniform(-4, 4), y - (4 + 6 * f) * R.uniform(0.6, 1.2), 0.6, R.uniform(0.6, 1.0), soft=0.2)
            im.alpha_composite(cv.render())
            frames.append(im)
        out[d] = frames
    return out, carry("shadowstep_ghost", [50, 60, 80, 100], {
        "note": ("v3 55R: 단검 그림자 밟기 출발 잔상 — 주인공 v3(free 대기 0열) 실루엣 재 껍데기(어두운 재 + 밝은 재 테두리) "
                 "+ 몸의 호박 금 자리 A23 + 발밑 어두운 웅덩이 → f1~f2 발부터 체크 구멍으로 비며 위로 떠오르고 재 조각·불씨가 "
                 "오름, 금은 A21→A19 로 공중에 남음 → f3 금 토막·재만. 주인공 크기(×6, Q64)."),
        "pivot": piv})


# ======================================================================
# aim_charge — 활 조준 차지: 혼불 실 고리가 차오르고 불씨가 빨려 듦 → 완료 백열
def aim_charge():
    W = 128
    c = W / 2
    RAD = 40

    def frame(f):
        cv = Canvas(W, W)
        M = lambda u, v: (c + u, c + v)
        Gd = cv.layer([B1, B3, S1])
        if f < 5:
            Gd.ring(c, c, RAD, 0.9, v=0.8, dash=(24, 0.45, 0.0))
            for k in range(4):
                a = k * TAU / 4
                Gd.stroke([M(math.cos(a) * (RAD + 6), math.sin(a) * (RAD + 6)),
                           M(math.cos(a) * (RAD + 13), math.sin(a) * (RAD + 13))], 0.8, prof=tp_both(0.5), v=0.9)
        if 0 < f < 5:
            frac = f / 5
            a0 = -math.pi / 2
            a1 = a0 + TAU * frac
            H = cv.layer(R_COOL)
            H.arc(c, c, RAD, RAD, a0, a1, 3.0, prof=tp_head(0.4), v=0.9)
            L = cv.layer(R_WARM)
            L.arc(c, c, RAD, RAD, a0, a1, 1.5, prof=tp_head(0.4), v=0.95)
            hx, hy = c + math.cos(a1) * RAD, c + math.sin(a1) * RAD
            L.stamp(hx, hy, 2.2, 1.0, soft=0.4)
            # 머리 뒤로 작은 불티
            for k in range(2):
                b = a1 - (0.18 + 0.12 * k)
                L.stamp(c + math.cos(b) * (RAD + 4 + 2 * k), c + math.sin(b) * (RAD + 4 + 2 * k), 0.6, 0.8, soft=0.2)
            # 빨려 드는 불씨 줄기: 진행도만큼 많이, 바깥 → 고리
            R = rng(901 + f)
            Ck = cv.layer(R_COOL)
            for k in range(2 + f):                         # 짧게 휘어 빨려 드는 불씨(바깥 어둡게 → 고리 쪽 밝게)
                a = R.uniform(0, TAU)
                r0 = RAD + R.uniform(10, 15)
                r1 = RAD + R.uniform(3, 5)
                Ck.stroke([M(math.cos(a + 0.18) * r0, math.sin(a + 0.18) * r0),
                           M(math.cos(a + 0.07) * (r0 + r1) / 2, math.sin(a + 0.07) * (r0 + r1) / 2),
                           M(math.cos(a) * r1, math.sin(a) * r1)], 0.75, prof=tp_head(0.8),
                          v=R.uniform(0.7, 1.0), vprof=lambda t: 0.5 + 0.5 * t)
            # 재 연기: 고리 안쪽 흐릿한 재 알갱이
            C = cv.layer(R_FLAKE)
            chips(C, M, 2 + f, 12, RAD - 8, 1.2, 0.75, seed=911 + f)
        if f == 5:
            G = cv.layer(R_COOL)
            G.ring(c, c, RAD, 5.0, v=0.9)
            L = cv.layer(R_FLASH)
            L.ring(c, c, RAD, 2.6, v=1.0)
            L.ring(c, c, RAD - 9, 0.9, v=0.75, dash=(20, 0.5, 0.0))
            for k in range(4):
                a = TAU / 8 + k * TAU / 4
                L.star4(c + math.cos(a) * RAD, c + math.sin(a) * RAD, 9, 1.0, 0.95, diag=0.4)
            sparks(L, M, 12, RAD + 8, RAD + 20, 7, 0.9, 0.85, seed=921)
            L.disc(c, c, 3.2, v=1.0, edge=0.6)
        return cv.render()
    return {"any": [frame(i) for i in range(6)]}, carry("aim_charge", [100] * 6, {
        "note": ("v3 55R: 활 조준 차지(진행도 구동, 프레임 수·공식 그대로 frame = min(5, floor(progress×5))) — 점선 안내 "
                 "고리 r40 + 네 방향 눈금 → 혼불 실 고리가 위에서 시계 방향으로 progress 만큼 참(머리 불씨 + 꼬리 불티) + "
                 "바깥에서 빨려 드는 불씨 줄기(진행도만큼 늘어남) + 안쪽 재 알갱이 → f5 완료 = 백열 고리 + 네 귀 별 + "
                 "바깥으로 터지는 불티 12 + 중심 점."),
        "pivotNote": ("피벗 (64,64) = 고리 중심. 붙이는 자리(플레이어 몸 중심, 발 피벗에서 위로)는 기존 시스템 규약 그대로 — "
                      "고리 반지름 40도트(= 논리 20)."),
        "pivot": {"x": 64, "y": 64}})


MOTION = {
    "dash_trail": (dash_trail, []),
    "dash_dust": (dash_dust, []),
    "parry_flash": (parry_flash, [0, 1]),
    "guard_wave": (guard_wave, [0]),
    "ironwall": (ironwall, [0]),
    "shadowstep_ghost": (shadowstep_ghost, []),
    "aim_charge": (aim_charge, [5]),
}

_ = (X0, A26, A17, R_FLASH2, tp_tail, needle, dots)
