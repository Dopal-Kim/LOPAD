"""1층 보스 '만취' 불타는 오버레이 (54라운드 Q18 · 계약 §15 맨 끝) — python3 parts/art/work/boss1_v3/onfire.py
(build.py 를 먼저 실행 — 보스 idle·walk 시트에서 몸 윤곽을 읽는다)

산출:
  assets/sprites/fx/v3/boss1_onfire.png/.json   192×240 · 피벗 (96,220) = 보스 시트와 같은 좌표계(발 중앙) · 행 = down/up/left/right
                                                 열 = 점화(ignite 4) → 루프(loop 8) → 꺼짐(out 4)
  parts/art/work/boss1_v3/preview_onfire_x3.gif  보스 idle 위에 얹은 불길(4방향, 3배) — 점화 → 루프 3바퀴 → 꺼짐
  parts/art/work/boss1_v3/preview_onfire_x2.png  전 프레임 2배(위 = 오버레이만, 아래 = idle 위에 얹음)

방식: 보스 idle+walk 전 프레임 윤곽(행 = 방향)의 합집합에서 높이별 좌우 가장자리를 구하고, 그 가장자리를 따라
발 → 무릎 → 배 → 어깨로 혀 모양 불꽃(아래가 크고 위로 갈수록 가늘게)을 세운다. 얼굴·가슴 가운데는 비운다(웃는 얼굴이 보이게).
모든 움직임이 t = i/8 의 정수배 주기 함수 → 루프 8프레임이 이음매 없이 이어진다. 반투명 0, 색 = 재·호박 램프 + 백열.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(HERE, "..", "v2_outer"))
from kit import G, A, X, Canvas, Rand  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

FW, FH = 192, 240
PIV = (96, 220)
DIRS = ["down", "up", "left", "right"]
OUT_F = os.path.join(ROOT, "assets/sprites/fx/v3")
BOSS = os.path.join(ROOT, "assets/sprites/bosses/v3")
N_IGN, N_LOOP, N_OUT = 4, 8, 4
MS = [60, 60, 70, 70] + [80] * N_LOOP + [80, 90, 110, 140]
EMISSIVE = ["#d67a11", "#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0", "#ffffff", "#fff4dc"]
SRC = "parts/art/work/boss1_v3/onfire.py (54라운드 Q18 — 보스 불타는 오버레이)"
BG = (46, 48, 56, 255)

# 불꽃 색(바깥 → 안): 식은 끝 A19 · 바깥 A21 · 중간 A23 · 안 A25 · 속 A27 · 심 X1
C_TIP, C_OUT, C_MID, C_IN, C_HOT, C_CORE = A[19], A[21], A[23], A[25], A[27], X[1]
ASH = [G[4], G[6], G[8]]
EMBER = [A[26], A[24], A[22], A[20]]


# ------------------------------------------------------------------------------------------- 몸 윤곽
def envelopes():
    """방향별 높이 y → (왼쪽 x, 오른쪽 x) — idle·walk 전 프레임 합집합, 위아래 5줄 이동 평균."""
    env = {}
    sheets = []
    for a in ("idle", "walk"):
        im = Image.open(os.path.join(BOSS, "stage1_%s.png" % a)).convert("RGBA")
        sheets.append(im)
    for r, d in enumerate(DIRS):
        lo, hi = {}, {}
        for im in sheets:
            n = im.width // FW
            for c in range(n):
                al = im.crop((c * FW, r * FH, (c + 1) * FW, (r + 1) * FH)).getchannel("A").load()
                for y in range(FH):
                    xs = [x for x in range(FW) if al[x, y] == 255]
                    if xs:
                        lo[y] = min(lo.get(y, 999), xs[0])
                        hi[y] = max(hi.get(y, -1), xs[-1])
        e = {}
        for y in lo:
            ys = [yy for yy in range(y - 2, y + 3) if yy in lo]
            e[y] = (sum(lo[yy] for yy in ys) / len(ys), sum(hi[yy] for yy in ys) / len(ys))
        env[d] = e
    return env


# ------------------------------------------------------------------------------------------- 불 연료장(정적) → 불꽃장(프레임)
def fuel_map(d, e):
    """방향 d 의 연료 지도: (x, y) → (세기, 위로 번지는 길이 L). 발밑 고리 · 몸 좌우 가장자리 띠(발 → 어깨, 위로 갈수록 약하고 짧게) ·
    다리 앞 · 어깨 깃 끝. 얼굴·가슴 가운데에는 연료가 없다."""
    fu = {}

    def put(x, y, s, L):
        x, y = int(round(x)), int(round(y))
        if not (0 <= x < FW and 0 <= y < FH):
            return
        o = fu.get((x, y))
        if o is None or s > o[0]:
            fu[(x, y)] = (s, L)
    ys = sorted(e)
    near = lambda y: e[y] if y in e else e[min(ys, key=lambda yy: abs(yy - y))]  # noqa: E731
    # 발밑 고리(납작한 타원 띠) — 몸 아래 폭 + 여유
    lx, rx = near(214)
    cx = (lx + rx) / 2
    rxg = (rx - lx) / 2 + 16
    for y in range(206, 228):
        for x in range(int(cx - rxg - 4), int(cx + rxg + 5)):
            q = ((x - cx) / rxg) ** 2 + ((y - 218) / 8.0) ** 2
            if q <= 1.15:
                put(x, y, 1.0 - 0.3 * max(0.0, q - 0.5), 22 + 12 * (1 - min(1, q)))
    ytop = {"down": 84, "up": 86, "left": 90, "right": 90}[d]
    yb = 208
    r = Rand({"down": 31, "up": 32, "left": 33, "right": 34}[d])
    for side in (0, 1):
        # 좌우 가장자리에 불 조각(뿌리)을 띄엄띄엄 — 발 쪽은 촘촘·길게(이어져 보임), 위로 갈수록 성기고 짧게(떨어진 혀)
        y = yb - side * 6
        while y >= ytop:
            f = (y - ytop) / (yb - ytop)                # 1 = 발, 0 = 어깨
            lx, rx = near(y)
            s = 0.7 + 0.36 * f
            L = 15 + 24 * f + r.i(0, 6)
            wd = 4 + 5 * f
            inset = r.i(-1, 3)
            mid = (wd - 2) / 2
            for yy in range(y - 6, y + 2):
                q = (yy - (y - 6)) / 7.0                 # 0 = 조각 위, 1 = 아래 → 아래로 갈수록 좁고 약하게(둥근 밑)
                half = (wd + 2) / 2 * (1 - 0.6 * q * q)
                for k in range(-2, int(wd) + 1):
                    if abs(k - mid) > half:
                        continue
                    fall = (1 - 0.2 * abs(k - mid) / max(1, half)) * (1 - 0.25 * q * q)
                    put((lx + k + inset) if side == 0 else (rx - k - inset), yy, s * fall, L)
            y -= 15 + int(9 * (1 - f)) + r.i(0, 4)
    # 앞쪽 작은 불(정면·뒷면만): 배 아랫선·팔 아래에 2~3개 — 몸에도 불이 붙은 느낌, 얼굴·배 가운데는 비움
    if d in ("down", "up"):
        lx, rx = near(158)
        for u_, yy0, L_ in ((0.18, 160, 18), (0.8, 156, 16), (0.33, 186, 14), (0.68, 184, 16)):
            x0 = lx + (rx - lx) * u_
            for yy in range(yy0 - 5, yy0 + 2):
                q = (yy - (yy0 - 5)) / 6.0
                half = 3.5 * (1 - 0.6 * q * q)
                for x in range(int(x0) - 4, int(x0) + 5):
                    if abs(x - x0) <= half:
                        put(x, yy, 0.8 * (1 - 0.25 * q * q), L_)
    # 다리 앞(장화 둘레) — 낮게만, 가운데는 약하게(장화가 비쳐 보이게)
    lx, rx = near(204)
    for y in range(202, 214):
        for x in range(int(lx), int(rx) + 1):
            u = abs((x - (lx + rx) / 2) / max(1, (rx - lx) / 2))
            put(x, y, 0.7 + 0.2 * u + 0.1 * (y - 202) / 12, 22)
    # 어깨 깃 끝 작은 불(둥근 뿌리, 짧은 혀)
    lx, rx = near(96)
    for x0 in (lx + 9, rx - 9):
        for yy in range(92, 99):
            q = (yy - 92) / 6.0
            half = 3.0 * (1 - 0.65 * q * q)
            for x in range(int(x0) - 4, int(x0) + 5):
                if abs(x - x0) <= half:
                    put(x, yy, 0.74 * (1 - 0.3 * q * q), 16)
    return fu


def smear(fu):
    """연료가 위로 번진 정적 세기장 S[(x, y)] = max 세기 × (1 − 위로 간 거리 / L)."""
    S = [[0.0] * FW for _ in range(FH)]
    for (x, y), (s, L) in fu.items():
        Li = int(L)
        for dy in range(Li + 1):
            yy = y - dy
            if yy < 0:
                break
            v = s * (1 - dy / L)
            if v > S[yy][x]:
                S[yy][x] = v
    return S


def ramp_col(v):
    if v > 0.93:
        return C_CORE
    if v > 0.82:
        return C_HOT
    if v > 0.68:
        return C_IN
    if v > 0.54:
        return C_MID
    if v > 0.40:
        return C_OUT
    if v > 0.30:
        return C_TIP
    return None


def fire(cv, S, t, gain=1.0, ycut=None, seed=0.0):
    """t = 0~1 주기. 불꽃 = 정적 세기장을 위로 흐르는 물결로 비틀고(가로 흔들림) 위로 흐르는 무늬로 깎는다.
    시간 항은 모두 2π·(정수)·t → 8프레임 루프 이음매 없음. ycut = 이 높이보다 위는 그리지 않음(점화·꺼짐)."""
    T = 2 * math.pi * t
    for y in range(FH):
        if ycut is not None and y < ycut:
            continue
        row = S
        wy = 2.4 * math.sin(0.085 * y + 2 * T + seed) + 0.8 * math.sin(0.17 * y + 3 * T + 1.3 + seed)
        for x in range(FW):
            xs = int(round(x + wy * (1 + 0.0025 * (FH - y))))
            if not (0 <= xs < FW):
                continue
            s = row[y][xs]
            if s <= 0.2:
                continue
            xw = x + wy
            c = (0.5 * math.sin(0.47 * xw + 2 * T + seed) + 0.3 * math.sin(0.83 * xw - 3 * T + 1.0 + seed)
                 + 0.2 * math.sin(0.29 * xw + 1 * T + 2.3 + seed)) * 0.5 + 0.5
            fl = 0.1 * math.sin(0.23 * y + 4 * T + 0.37 * x)          # 위로 흐르는 깜박임
            v = s * gain * (0.5 + 0.62 * c + fl)
            col = ramp_col(v)
            if col is not None:
                cv.px(x, y, col)
    # 외톨이 점 정리(4 이웃 중 불 0 → 지움)
    im = cv.im
    px = im.load()
    kill = []
    for y in range(1, FH - 1):
        for x in range(1, FW - 1):
            if px[x, y][3] and not (px[x - 1, y][3] or px[x + 1, y][3] or px[x, y - 1][3] or px[x, y + 1][3]):
                kill.append((x, y))
    for x, y in kill:
        px[x, y] = (0, 0, 0, 0)


def embers(cv, pts, t, n, seed, rise=70, k=1):
    r = Rand(seed)
    for j in range(n):
        bx, by = pts[r.i(0, len(pts) - 1)]
        s = r.f()
        q = (k * t + s) % 1.0
        x = bx + r.i(-6, 6) + 4 * math.sin(2 * math.pi * (q + s))
        y = by - 6 - q * rise
        col = EMBER[min(3, int(q * 4))]
        cv.px(int(round(x)), int(round(y)), col)
        if q < 0.35 and j % 3 == 0:
            cv.px(int(round(x)), int(round(y)) - 1, EMBER[0])


def ash(cv, pts, t, n, seed):
    """꺼질 때 재·연기 점(불투명 회색)."""
    r = Rand(seed)
    for j in range(n):
        bx, by = pts[r.i(0, len(pts) - 1)]
        s = r.f()
        q = (t + s) % 1.0
        x = bx + r.i(-8, 8) + 5 * math.sin(2 * math.pi * (q + s))
        y = by - 6 - q * 46
        col = ASH[min(2, int(q * 3))]
        cv.px(int(round(x)), int(round(y)), col)
        if j % 2 == 0:
            cv.px(int(round(x)) + 1, int(round(y)), col)


def draw_frame(d, fu, S, roots, phase, i):
    """phase = 'ignite'·'loop'·'out', i = 그 단계 안 번호."""
    cv = Canvas(FW, FH)
    if phase == "ignite":
        ycut = [206, 176, 136, 96][i]                  # 불이 발에서 위로 타고 오름
        gain = [0.66, 0.84, 0.95, 1.0][i]
        t = (i - N_IGN) / N_LOOP                       # 점화 끝 → 루프 0 이 이어지게
    elif phase == "out":
        ycut = [120, 160, 192, 214][i]                 # 위에서부터 꺼짐
        gain = [0.92, 0.8, 0.66, 0.5][i]
        t = (N_LOOP + i) / N_LOOP
    else:
        ycut, gain, t = None, 1.0, i / N_LOOP
    if ycut is not None:
        S = smear({p: v for p, v in fu.items() if p[1] >= ycut})   # 연료를 그 높이 아래만 → 끝이 자연스럽게 혀 모양
    fire(cv, S, t, gain)
    live = [(x, y) for (x, y) in roots if ycut is None or y >= ycut]
    if phase == "ignite":
        embers(cv, [(PIV[0] + dx, 222) for dx in range(-44, 45, 8)], 0.3 + 0.2 * i, 18 - 3 * i, 5 + i, rise=40 + 30 * i)
    elif phase == "out":
        ash(cv, roots[::3], 0.22 * i, 10 + 6 * i, 40 + i)
        if live:
            embers(cv, live, 0.15 * i, max(0, 14 - 3 * i), 50 + i, rise=60)
    else:
        embers(cv, roots, t, 26, 21, rise=80)
    return cv.im


def no_partial(im):
    assert not any(0 < a < 255 for a in im.getchannel("A").tobytes()), "반투명 픽셀"


def build():
    env = envelopes()
    rows = []
    for d in DIRS:
        e = env[d]
        fu = fuel_map(d, e)
        S = smear(fu)
        roots = sorted({(x, y) for (x, y) in fu if (x + 3 * y) % 23 == 0}, key=lambda p: (p[1], p[0]))
        row = [draw_frame(d, fu, S, roots, "ignite", i) for i in range(N_IGN)]
        row += [draw_frame(d, fu, S, roots, "loop", i) for i in range(N_LOOP)]
        row += [draw_frame(d, fu, S, roots, "out", i) for i in range(N_OUT)]
        rows.append(row)
    n = len(rows[0])
    sheet = Image.new("RGBA", (FW * n, FH * 4), (0, 0, 0, 0))
    cols = set()
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            no_partial(im)
            sheet.alpha_composite(im, (c * FW, r * FH))
            b = im.tobytes()
            cols |= {b[q:q + 3] for q in range(0, len(b), 4) if b[q + 3] == 255}
    assert len(cols) <= 40, len(cols)
    os.makedirs(OUT_F, exist_ok=True)
    sheet.save(os.path.join(OUT_F, "boss1_onfire.png"))
    ign = list(range(N_IGN))
    lp = list(range(N_IGN, N_IGN + N_LOOP))
    out = list(range(N_IGN + N_LOOP, n))
    meta = {
        "image": "boss1_onfire.png", "action": "onfire", "frameWidth": FW, "frameHeight": FH, "frames": n,
        "directions": DIRS, "layout": "rows = directions (down, up, left, right) — 보스 시트와 같은 방향 행, columns = frames",
        "frameIndex": "row * frames + column", "fps": round(1000.0 * n / sum(MS), 2), "frameDurationsMs": MS,
        "loop": True, "loopRange": [lp[0], lp[-1]],
        "phaseFrames": {"ignite": ign, "loop": lp, "out": out},
        "phaseStartMs": {"ignite": 0, "loop": sum(MS[:N_IGN]), "out": sum(MS[:N_IGN + N_LOOP])},
        "phaseNote": ("불 위에 서면 ignite(0~3, 1회 260ms) → loop(4~11 반복, 한 바퀴 640ms) — 불에서 나와 잠시 뒤(시스템 임시값) "
                      "out(12~15, 1회 420ms, 위에서부터 꺼지며 재·불티) → 오버레이 제거. loop 중 다시 꺼짐 조건이 풀리면 loop 유지"),
        "pivot": {"x": PIV[0], "y": PIV[1]},
        "anchor": "boss_pivot",
        "anchorNote": ("보스 v3 시트(stage1_*, 192×240, 피벗 (96,220))와 같은 크기·같은 피벗 — 보스 스프라이트 위치에 그대로 겹쳐 "
                       "보스 바로 위 깊이(+0.01)로 그린다. 방향 행은 보스의 현재 방향 행과 같게. 보스 동작(대기·걷기·돌진 등)과 "
                       "프레임을 맞출 필요 없음(몸 윤곽은 idle·walk 합집합 기준). 쓰러진 동작(fall·death)의 전 방향 공통 프레임은 누운 불길 "
                       "boss1_onfire_down 으로 바꿔 낀다(같은 열 번호·같은 시간 — 그 JSON 의 useFor·standFor·frameOffsets, 54라운드 Q23)"),
        "lyingSheet": "boss1_onfire_down",
        "pixelScale": 0.5, "version": "v3", "paletteSwap": "none",
        "paletteSwapNote": "53라운드 Q62·Q68 — fx 는 지역 바닥 팔레트 교체 제외",
        "drawOver": "lightmap", "drawOverNote": "53라운드 Q63 — fx 는 조명 위에 그린다",
        "light": {"color": "#e8b858", "radius": 230, "intensity": 0.85, "flicker": {"amp": 0.22, "hz": 8}, "offset": [96, 150]},
        "lightByPhase": {
            "ignite": {"color": "#e2a33c", "radius": 150, "intensity": 0.6, "flicker": {"amp": 0.3, "hz": 10}, "offset": [96, 190]},
            "loop": {"color": "#e8b858", "radius": 230, "intensity": 0.85, "flicker": {"amp": 0.22, "hz": 8}, "offset": [96, 150]},
            "out": {"color": "#d67a11", "radius": 120, "intensity": 0.45, "flicker": {"amp": 0.35, "hz": 10}, "offset": [96, 200]},
        },
        "lightNote": "radius·offset = 도트(시스템이 pixelScale 로 환산). offset = 프레임 왼쪽 위 기준 [x, y] — 배꼽 높이",
        "emissiveColors": EMISSIVE,
        "palette": "v3 이펙트: 1층 재·호박 램프 A19~A27 + 백열 X1 #fff4dc + 재(G4·G6·G8, 꺼질 때). 새 색 없음. paletteSwap none",
        "source": SRC,
        "note": ("54라운드 Q18 — 보스가 불붙은 술 위에 서 있으면 발에서 몸통·어깨까지 타고 오르는 불길(보스는 무피해, 오히려 강해짐). "
                 "얼굴·가슴 가운데는 비워 둠 — 아무렇지 않은 듯 웃는 표정이 보이게(보스 시트는 그대로)"),
        "colors": len(cols),
    }
    with open(os.path.join(OUT_F, "boss1_onfire.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return rows, meta


# ------------------------------------------------------------------------------------------- 미리보기
def boss_frames(act):
    j = json.load(open(os.path.join(BOSS, "stage1_%s.json" % act)))
    im = Image.open(os.path.join(BOSS, "stage1_%s.png" % act)).convert("RGBA")
    n = j["frames"]
    return [[im.crop((c * FW, r * FH, (c + 1) * FW, (r + 1) * FH)) for c in range(n)] for r in range(4)], j["frameDurationsMs"]


def pool(im):
    """미리보기용 불붙은 술 웅덩이(바닥, 오버레이 산출물 아님)."""
    d = ImageDraw.Draw(im)
    d.ellipse((PIV[0] - 70, PIV[1] - 10, PIV[0] + 70, PIV[1] + 12), fill=A[18])
    d.ellipse((PIV[0] - 58, PIV[1] - 7, PIV[0] + 58, PIV[1] + 9), fill=A[20])
    d.ellipse((PIV[0] - 40, PIV[1] - 4, PIV[0] + 40, PIV[1] + 6), fill=A[21])


def previews(rows):
    from PIL import ImageFont  # noqa: F401
    sys.path.insert(0, os.path.join(HERE, "..", "enemies_v3"))
    import eprev
    bf, bms = boss_frames("idle")
    k = 3
    seq = [("ignite", c) for c in range(N_IGN)] + [("loop", N_IGN + c) for _ in range(3) for c in range(N_LOOP)] + \
          [("out", N_IGN + N_LOOP + c) for c in range(N_OUT)] + [("none", None)] * 4
    gif, durs = [], []
    tb = 0
    for si, (ph, col) in enumerate(seq):
        ms = MS[col] if col is not None else 120
        bi = (tb // 170) % len(bf[0])
        fr = Image.new("RGBA", (FW * 4 * k, FH * k + 30), BG)
        dr = ImageDraw.Draw(fr)
        for c in range(4):
            cell = Image.new("RGBA", (FW, FH), BG)
            if ph != "none":
                pool(cell)
            cell.alpha_composite(bf[c][bi])
            if col is not None:
                cell.alpha_composite(rows[c][col])
            fr.alpha_composite(cell.resize((FW * k, FH * k), Image.NEAREST), (c * FW * k, 30))
        eprev.label(dr, 6, 6, "boss1_onfire · %s %s · 보스 idle 위(웅덩이는 미리보기용) · 3배 · down/up/left/right" % (ph, "" if col is None else col))
        gif.append(fr.convert("RGB").quantize(colors=255, method=Image.MEDIANCUT))
        durs.append(ms)
        tb += ms
    gif[0].save(os.path.join(HERE, "preview_onfire_x3.gif"), save_all=True, append_images=gif[1:], duration=durs, loop=0)
    # 2배 전 프레임
    k = 2
    n = len(rows[0])
    W = 60 + n * (FW * k + 4)
    H = 40 + 8 * (FH * k + 4)
    out = Image.new("RGBA", (W, H), BG)
    dr = ImageDraw.Draw(out)
    eprev.label(dr, 6, 6, "boss1_onfire 2배 · 열 0~3 ignite · 4~11 loop · 12~15 out · 위 4행 = 오버레이만, 아래 4행 = idle 0 위 · 빨간 점 = 피벗(96,220)")
    for r in range(8):
        for c in range(n):
            x, y = 50 + c * (FW * k + 4), 30 + r * (FH * k + 4)
            cell = Image.new("RGBA", (FW, FH), BG)
            if r >= 4:
                cell.alpha_composite(bf[r - 4][0])
            cell.alpha_composite(rows[r % 4][c])
            out.alpha_composite(cell.resize((FW * k, FH * k), Image.NEAREST), (x, y))
            dr.rectangle((x + PIV[0] * k - 1, y + PIV[1] * k - 1, x + PIV[0] * k + 1, y + PIV[1] * k + 1), fill=(220, 60, 60, 255))
            if r == 0:
                eprev.label(dr, x + 4, y + 4, str(c))
        eprev.label(dr, 4, 30 + r * (FH * k + 4) + FH, DIRS[r % 4][:2])
    out.save(os.path.join(HERE, "preview_onfire_x2.png"))


if __name__ == "__main__":
    rows, meta = build()
    previews(rows)
    print("onfire colors", meta["colors"])
