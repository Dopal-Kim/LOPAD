"""1층 보스 '만취' 누운 자세 불길 오버레이 (54라운드 Q23 · 계약 §15 맨 끝) — python3 parts/art/work/boss1_v3/onfire_down.py
(build.py 먼저 — 보스 fall·death 시트에서 누운 몸 윤곽을 읽는다. onfire.py 의 불꽃 함수를 그대로 쓴다)

산출:
  assets/sprites/fx/v3/boss1_onfire_down.png/.json   192×240 · 피벗 (96,220) = 보스 시트와 같은 좌표계 · 행 1개(전 방향 공통, Q16)
                                                      열 16 = boss1_onfire 와 같은 배치·같은 시간(ignite 4 · loop 8 · out 4)
                                                      → 서 있는 불길 ↔ 누운 불길을 같은 열 번호로 바꿔 끼울 수 있다
  parts/art/work/boss1_v3/preview_onfire_down_x3.gif  fall 전체(매핑 적용) · fall 누운 루프 위 점화→루프→꺼짐 · death 누운 구간
  parts/art/work/boss1_v3/preview_onfire_down_x2.png  전 프레임 2배(오버레이만 · fall 6 위 · death 11 위)

방식: fall 4~9 · death 9~13(누운 그림) 몸 윤곽을 자세별 합집합으로 구하고(잔·왕관·웅덩이·먼지 제외), 두 자세의 행별 교집합을
'누운 몸 윤곽'으로 쓴다(어느 자세에서도 불이 몸 밖 허공에 뜨지 않게). 그 윤곽의 바닥 고리 · 좌우 가장자리 조각 · 몸 위 작은 불(배 옆·팔·망토 단)에
연료를 놓고 위로 번지게 → onfire.fire 로 흔들림·혀 무늬·6단 램프. 얼굴(두 자세의 얼굴 타원 합)은 세기장과 결과 모두에서 비운다.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import onfire as OF  # noqa: E402
from onfire import FW, FH, PIV, MS, N_IGN, N_LOOP, N_OUT, BOSS, OUT_F, BG, EMISSIVE  # noqa: E402
from kit import A, Canvas, Rand  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SRC = "parts/art/work/boss1_v3/onfire_down.py (54라운드 Q23 — 보스 누운 자세 불길)"
FALL_LYING = [4, 5, 6, 7, 8, 9]
DEATH_LYING = [9, 10, 11, 12, 13]
# 시트 사용 매핑 — 규칙: 전 방향 공통 그림(Q16 누운 그림 · 넘어가는/일어나는 공통 프레임) = 누운 불길, 방향별 그림 = 서 있는 불길(방향 행)
USE_DOWN = {"fall": list(range(2, 12)), "death": list(range(8, 14))}
USE_STAND = {"fall": [0, 1, 12, 13, 14, 15, 16], "death": list(range(0, 8))}
REF = ("fall", 6)                       # 오프셋 0 기준 프레임(누워 버둥 루프 첫 장)
FACES = [(97, 117, 18, 20), (94, 106, 18, 18)]   # 얼굴 타원(cx, cy, rx, ry) — fall 누움 · death 누움


def load(act):
    j = json.load(open(os.path.join(BOSS, "stage1_%s.json" % act)))
    im = Image.open(os.path.join(BOSS, "stage1_%s.png" % act)).convert("RGBA")
    return [im.crop((c * FW, 0, (c + 1) * FW, FH)) for c in range(j["frames"])], j["frameDurationsMs"]


def body_alpha(act, im):
    """몸만 남긴 알파(잔·왕관·웅덩이·먼지 제외 — 좌표는 v3 그림 실측)."""
    a = im.getchannel("A").load()
    keep = set()
    for y in range(FH):
        for x in range(FW):
            if a[x, y] != 255:
                continue
            if act == "fall" and x < 64 and y < 108:          # 치켜든 술통 잔·잔 든 팔
                continue
            if act == "death" and (y >= 212 or x >= 172 or (x < 66 and y > 196)):   # 웅덩이·먼지·떨어진 왕관
                continue
            keep.add((x, y))
    return keep


def envelope_of(act, frames):
    lo, hi = {}, {}
    for im in frames:
        for (x, y) in body_alpha(act, im):
            lo[y] = min(lo.get(y, 999), x)
            hi[y] = max(hi.get(y, -1), x)
    return lo, hi


def lying_envelope():
    """두 누운 자세의 행별 교집합(왼쪽 = 더 안쪽, 오른쪽 = 더 안쪽), 위아래 5줄 이동 평균."""
    ff, _ = load("fall")
    df, _ = load("death")
    l1, h1 = envelope_of("fall", [ff[i] for i in FALL_LYING])
    l2, h2 = envelope_of("death", [df[i] for i in DEATH_LYING])
    lo, hi = {}, {}
    for y in set(l1) & set(l2):
        a, b = max(l1[y], l2[y]), min(h1[y], h2[y])
        if b - a >= 6:
            lo[y], hi[y] = a, b
    e = {}
    for y in lo:
        ys = [yy for yy in range(y - 2, y + 3) if yy in lo]
        e[y] = (sum(lo[yy] for yy in ys) / len(ys), sum(hi[yy] for yy in ys) / len(ys))
    return e


def bottom_center(act, im):
    """몸 아랫선(불투명 60 이상인 가장 낮은 줄)과 그 줄 가운데 x."""
    pts = body_alpha(act, im)
    rows = {}
    for (x, y) in pts:
        rows.setdefault(y, []).append(x)
    ys = [y for y, xs in rows.items() if len(xs) >= 60]
    yb = max(ys)
    xs = rows[yb]
    return yb, (min(xs) + max(xs)) / 2


def frame_offsets():
    """누운 불길을 쓰는 프레임별 [dx, dy](도트) — 몸 아랫선을 기준 프레임(fall 6)에 맞춤. 누움 구간은 거의 0."""
    frames = {"fall": load("fall")[0], "death": load("death")[0]}
    yb0, xc0 = bottom_center(REF[0], frames[REF[0]][REF[1]])
    out = {}
    for act, idx in USE_DOWN.items():
        out[act] = {}
        for i in idx:
            yb, xc = bottom_center(act, frames[act][i])
            dx, dy = 0, yb - yb0                     # 가로는 몸 무게중심 차가 ±6 이내 → 0(피벗 = 몸 가운데)
            if abs(dy) <= 2:
                dy = 0
            out[act][str(i)] = [dx, dy]
    return out


def in_face(x, y, grow=0):
    return any(((x - cx) / (rx + grow)) ** 2 + ((y - cy) / (ry + grow)) ** 2 <= 1.0 for cx, cy, rx, ry in FACES)


# ------------------------------------------------------------------------------------------- 연료
def fuel_map(e):
    fu = {}

    def put(x, y, s, L):
        x, y = int(round(x)), int(round(y))
        if not (0 <= x < FW and 0 <= y < FH) or in_face(x, y, 3):
            return
        o = fu.get((x, y))
        if o is None or s > o[0]:
            fu[(x, y)] = (s, L)

    def blob(x0, y0, w, s, L, h=7):
        """밑이 둥근 불 뿌리 조각(위 넓고 아래 좁고 약하게)."""
        for yy in range(y0 - h + 1, y0 + 2):
            q = (yy - (y0 - h + 1)) / float(h)
            half = w / 2 * (1 - 0.6 * q * q)
            for x in range(int(x0 - w), int(x0 + w) + 1):
                if abs(x - x0) <= half:
                    put(x, yy, s * (1 - 0.25 * q * q) * (1 - 0.15 * abs(x - x0) / max(1, half)), L)

    ys = sorted(e)
    near = lambda y: e[y] if y in e else e[min(ys, key=lambda yy: abs(yy - y))]  # noqa: E731
    # 1) 바닥 고리 — 누운 몸 아래(망토 단) 둘레. 빈틈 있는 마디(각도별 세기 물결)로 끊고 혀는 짧게 → 벽처럼 보이지 않게
    lx, rx = near(212)
    cx = (lx + rx) / 2
    rxg = (rx - lx) / 2 + 18
    for y in range(206, 230):
        for x in range(int(cx - rxg - 4), int(cx + rxg + 5)):
            q = ((x - cx) / rxg) ** 2 + ((y - 219) / 8.0) ** 2
            if q <= 1.12:
                u = (x - cx) / rxg
                wave = 0.82 + 0.18 * math.cos(9.0 * u + 0.6) + 0.08 * math.cos(17.0 * u)
                front = 1.0 - 0.18 * max(0.0, 1 - abs(u) * 1.6) * (1 if y > 219 else 0)   # 앞 가운데는 조금 낮게(망토 단이 비침)
                put(x, y, (1.0 - 0.3 * max(0.0, q - 0.5)) * wave * front, 13 + 7 * (1 - min(1, q)) + 4 * wave)
    # 2) 좌우 가장자리 혀 — 누운 몸은 길이 내내 바닥에 닿아 있으므로 세기를 고르게, 혀는 짧게(기둥처럼 이어지지 않게)
    ytop, yb = 124, 204
    r = Rand(71)
    for side in (0, 1):
        y = yb - side * 4
        while y >= ytop:
            f = (y - ytop) / (yb - ytop)
            lx, rx = near(y)
            wd = 5 + 2 * f
            inset = r.i(0, 2)
            x0 = (lx + wd / 2 + inset) if side == 0 else (rx - wd / 2 - inset)
            blob(x0, y, wd + 2, 0.84 + 0.14 * f, 11 + 4 * f + r.i(0, 4), h=6)
            y -= 11 + r.i(0, 4)
    # 3) 몸 위 불 덩이 — 옷(배 옆·허벅지·망토 단 위)에 붙은 불을 6 덩이로 모음(흩뿌린 점은 잎사귀처럼 산만해 버림).
    #    덩이 = 가운데 큰 뿌리 + 양옆 작은 뿌리 2(조금 아래) → 한 덩어리 불. 배꼽 세로줄·얼굴은 비움
    for u_, y0, L in ((0.16, 152, 15), (0.84, 150, 16), (0.26, 182, 14), (0.74, 180, 15), (0.40, 199, 11), (0.61, 201, 12)):
        lx, rx = near(y0)
        x0 = lx + (rx - lx) * u_
        blob(x0, y0, 8, 0.82, L, h=7)
        blob(x0 - 5, y0 + 3, 5, 0.74, L - 5, h=5)
        blob(x0 + 5, y0 + 2, 5, 0.74, L - 4, h=5)
    # 4) 오른팔(fall 은 옆으로 뻗음 · death 는 벌림 — 두 자세가 겹치는 자리) · 어깨(머리 양옆) — 얼굴 쪽으로 번지지 않게 바깥으로
    blob(160, 146, 6, 0.8, 12, h=6)
    lx, rx = near(130)
    for x0 in (lx + 6, rx - 6):
        blob(x0, 131, 5, 0.74, 11, h=5)
    return fu


def masked_smear(fu):
    S = OF.smear(fu)
    for y in range(FH):
        for x in range(FW):
            if S[y][x] and in_face(x, y, 4):
                S[y][x] = 0.0
    return S


def clear_face(im):
    px = im.load()
    for y in range(FH):
        for x in range(FW):
            if px[x, y][3] and in_face(x, y, 1):
                px[x, y] = (0, 0, 0, 0)


def draw_frame(fu, S, roots, ring, phase, i):
    cv = Canvas(FW, FH)
    if phase == "ignite":
        ycut = [208, 188, 160, 122][i]                  # 바닥 고리 → 몸 아래 → 배 → 어깨
        gain = [0.66, 0.84, 0.95, 1.0][i]
        t = (i - N_IGN) / N_LOOP
    elif phase == "out":
        ycut = [148, 176, 198, 214][i]                  # 위(몸)부터 꺼지고 바닥 고리가 마지막
        gain = [0.92, 0.8, 0.66, 0.5][i]
        t = (N_LOOP + i) / N_LOOP
    else:
        ycut, gain, t = None, 1.0, i / N_LOOP
    if ycut is not None:
        S = masked_smear({p: v for p, v in fu.items() if p[1] >= ycut})
    OF.fire(cv, S, t, gain)
    live = [(x, y) for (x, y) in roots if ycut is None or y >= ycut]
    if phase == "ignite":
        OF.embers(cv, ring, 0.3 + 0.2 * i, 18 - 3 * i, 85 + i, rise=34 + 22 * i)
    elif phase == "out":
        OF.ash(cv, roots[::3], 0.22 * i, 10 + 6 * i, 90 + i)
        if live:
            OF.embers(cv, live, 0.15 * i, max(0, 14 - 3 * i), 95 + i, rise=52)
    else:
        OF.embers(cv, roots, t, 26, 81, rise=70)
    clear_face(cv.im)
    return cv.im


def build():
    e = lying_envelope()
    fu = fuel_map(e)
    S = masked_smear(fu)
    roots = sorted({(x, y) for (x, y) in fu if (x + 3 * y) % 23 == 0}, key=lambda p: (p[1], p[0]))
    ring = [(PIV[0] + dx, 222) for dx in range(-56, 57, 8)]
    row = [draw_frame(fu, S, roots, ring, "ignite", i) for i in range(N_IGN)]
    row += [draw_frame(fu, S, roots, ring, "loop", i) for i in range(N_LOOP)]
    row += [draw_frame(fu, S, roots, ring, "out", i) for i in range(N_OUT)]
    n = len(row)
    sheet = Image.new("RGBA", (FW * n, FH), (0, 0, 0, 0))
    cols = set()
    for c, im in enumerate(row):
        OF.no_partial(im)
        sheet.alpha_composite(im, (c * FW, 0))
        b = im.tobytes()
        cols |= {b[q:q + 3] for q in range(0, len(b), 4) if b[q + 3] == 255}
    assert len(cols) <= 40, len(cols)
    sheet.save(os.path.join(OUT_F, "boss1_onfire_down.png"))
    ign = list(range(N_IGN))
    lp = list(range(N_IGN, N_IGN + N_LOOP))
    out = list(range(N_IGN + N_LOOP, n))
    offs = frame_offsets()
    meta = {
        "image": "boss1_onfire_down.png", "action": "onfire_down", "frameWidth": FW, "frameHeight": FH, "frames": n,
        "directions": ["any"], "rows": 1,
        "layout": "행 1개 = 전 방향 공통(54라운드 Q16 누운 그림 전 방향 공통), columns = frames — 보스 방향과 무관하게 0행",
        "frameIndex": "column", "fps": round(1000.0 * n / sum(MS), 2), "frameDurationsMs": MS,
        "loop": True, "loopRange": [lp[0], lp[-1]],
        "phaseFrames": {"ignite": ign, "loop": lp, "out": out},
        "phaseStartMs": {"ignite": 0, "loop": sum(MS[:N_IGN]), "out": sum(MS[:N_IGN + N_LOOP])},
        "phaseNote": ("boss1_onfire 와 열 배치·프레임 시간이 같다(ignite 0~3 · loop 4~11 · out 12~15). 누운 상태에서 불이 붙으면 ignite(바닥 고리 → 몸 위로), "
                      "꺼질 때 out(몸 위부터 꺼지고 바닥 고리가 마지막)"),
        "pivot": {"x": PIV[0], "y": PIV[1]},
        "anchor": "boss_pivot",
        "useFor": USE_DOWN,
        "standFor": USE_STAND,
        "frameOffsets": offs,
        "useForNote": ("보스 동작·프레임별 시트 선택. useFor = 이 시트(0행), standFor = boss1_onfire(보스 현재 방향 행). "
                       "규칙: 전 방향 공통 그림(넘어가는 중 fall 2~3 · 누움 fall 4~9 · 일어나 앉음/무릎 fall 10~11 · 넘어가는 중 death 8 · 누움 death 9~13) = 누운 불길, "
                       "방향별 그림(발 걸림 fall 0~1 · 일어섬 fall 12~16 · 맞고 무너짐 death 0~7) = 서 있는 불길. 그 밖의 동작은 전부 boss1_onfire. "
                       "두 시트는 같은 열 번호·같은 시간이므로 바꿔 낄 때 현재 열(단계·루프 위상)을 그대로 이어 쓴다(점화를 다시 하지 않음). "
                       "frameOffsets = 그 보스 프레임에서 이 오버레이를 옮길 [dx, dy] 도트(몸 아랫선 맞춤, 없거나 [0,0] 이면 그대로) — 논리 px = 도트 × 0.5"),
        "pixelScale": 0.5, "version": "v3", "paletteSwap": "none",
        "paletteSwapNote": "53라운드 Q62·Q68 — fx 는 지역 바닥 팔레트 교체 제외",
        "drawOver": "lightmap", "drawOverNote": "53라운드 Q63 — fx 는 조명 위에 그린다",
        "light": {"color": "#e8b858", "radius": 230, "intensity": 0.85, "flicker": {"amp": 0.22, "hz": 8}, "offset": [96, 176]},
        "lightByPhase": {
            "ignite": {"color": "#e2a33c", "radius": 150, "intensity": 0.6, "flicker": {"amp": 0.3, "hz": 10}, "offset": [96, 204]},
            "loop": {"color": "#e8b858", "radius": 230, "intensity": 0.85, "flicker": {"amp": 0.22, "hz": 8}, "offset": [96, 176]},
            "out": {"color": "#d67a11", "radius": 120, "intensity": 0.45, "flicker": {"amp": 0.35, "hz": 10}, "offset": [96, 208]},
        },
        "lightNote": ("boss1_onfire 와 같은 색·반경·세기, offset 만 낮춤(누운 몸 가운데). radius·offset = 도트(pixelScale 로 환산), "
                      "offset = 프레임 왼쪽 위 기준 [x, y] — frameOffsets 가 있으면 함께 옮긴다"),
        "emissiveColors": EMISSIVE,
        "palette": "v3 이펙트: 1층 재·호박 램프 A19~A27 + 백열 X1 #fff4dc + 재(G4·G6·G8, 꺼질 때). boss1_onfire 와 같은 색. 새 색 없음. paletteSwap none",
        "source": SRC,
        "note": ("54라운드 Q23 — 넘어짐(fall)·죽음(death) 누운 그림 위에 겹치는 불길. 누운 몸 윤곽(바닥 고리·좌우 가장자리·배 옆·팔·망토 단)을 따라 위로 솟고 "
                 "얼굴은 비움(누워서도 웃거나 X 눈이 보이게). fall 의 치켜든 술통 잔도 가리지 않음"),
        "colors": len(cols),
    }
    with open(os.path.join(OUT_F, "boss1_onfire_down.json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return row, meta


# ------------------------------------------------------------------------------------------- 미리보기
def stand_rows():
    im = Image.open(os.path.join(OUT_F, "boss1_onfire.png")).convert("RGBA")
    n = im.width // FW
    return [[im.crop((c * FW, r * FH, (c + 1) * FW, (r + 1) * FH)) for c in range(n)] for r in range(4)]


def overlay_for(act, bi, col, row, stand, offs):
    """보스 act 프레임 bi 에 얹을 오버레이 이미지와 오프셋(down 방향 기준)."""
    if bi in USE_DOWN[act]:
        dx, dy = offs[act].get(str(bi), [0, 0])
        return row[col], dx, dy
    return stand[0][col], 0, 0


def previews(row, meta):
    sys.path.insert(0, os.path.join(HERE, "..", "enemies_v3"))
    import eprev
    ff, fms = load("fall")
    df, dms = load("death")
    stand = stand_rows()
    offs = meta["frameOffsets"]
    k = 3
    lp0 = N_IGN
    # 패널 A: fall 전체(매핑·오프셋 적용, 불은 loop 반복) / B: fall 누움 루프(6~9) 위 점화 → 루프 3바퀴 → 꺼짐 / C: death 전체 → 누운 채 유지
    seqB = [("ignite", c) for c in range(N_IGN)] + [("loop", N_IGN + c) for _ in range(3) for c in range(N_LOOP)] + \
           [("out", N_IGN + N_LOOP + c) for c in range(N_OUT)] + [("none", None)] * 3
    total = sum(MS[c] if c is not None else 120 for _, c in seqB)
    step = 40
    gif, durs = [], []
    fall_total = sum(fms)
    death_total = sum(dms)

    def at(ms_list, t, hold_last=False, loop_from=None):
        tot = sum(ms_list)
        if t >= tot:
            if hold_last:
                return len(ms_list) - 1
            t = t % tot
        acc = 0
        for i, m in enumerate(ms_list):
            acc += m
            if t < acc:
                return i
        return len(ms_list) - 1

    loop_ms = MS[N_IGN:N_IGN + N_LOOP]
    seq_ms = [MS[c] if c is not None else 120 for _, c in seqB]
    t = 0
    last = None
    while t < total:
        sb = at(seq_ms, t)
        ph, colB = seqB[sb]
        colL = lp0 + at(loop_ms, t)                     # 패널 A·C 의 불(루프 위상)
        fi = at(fms, t % (fall_total + 400)) if t % (fall_total + 400) < fall_total else 16
        di = at(dms, t, hold_last=True)
        downi = 6 + at(fms[6:10], t)                    # 패널 B 보스 = 누워 버둥 루프
        key = (fi, colL, colB, di, downi)
        if key != last:
            fr = Image.new("RGBA", (FW * 3 * k, FH * k + 30), BG)
            dr = ImageDraw.Draw(fr)
            cells = []
            # A
            c = Image.new("RGBA", (FW, FH), BG)
            c.alpha_composite(ff[fi])
            ov, dx, dy = overlay_for("fall", fi, colL, row, stand, offs)
            c.alpha_composite(ov, (dx, dy))
            cells.append((c, "fall %d %s" % (fi, "down" if fi in USE_DOWN["fall"] else "stand")))
            # B
            c = Image.new("RGBA", (FW, FH), BG)
            c.alpha_composite(ff[downi])
            if colB is not None:
                c.alpha_composite(row[colB])
            cells.append((c, "fall %d · %s %s" % (downi, ph, "" if colB is None else colB)))
            # C
            c = Image.new("RGBA", (FW, FH), BG)
            c.alpha_composite(df[di])
            ov, dx, dy = overlay_for("death", di, colL, row, stand, offs)
            c.alpha_composite(ov, (dx, dy))
            cells.append((c, "death %d %s" % (di, "down" if di in USE_DOWN["death"] else "stand")))
            for j, (cell, lab) in enumerate(cells):
                fr.alpha_composite(cell.resize((FW * k, FH * k), Image.NEAREST), (j * FW * k, 30))
                eprev.label(dr, j * FW * k + 8, 34, lab)
            eprev.label(dr, 6, 6, "boss1_onfire_down · 3배 · 왼쪽 fall 전체(useFor 매핑, 서 있는 불길 down 행) · 가운데 fall 누움 루프 위 점화→루프→꺼짐 · 오른쪽 death")
            gif.append(fr.convert("RGB").quantize(colors=255, method=Image.MEDIANCUT))
            durs.append(step)
            last = key
        else:
            durs[-1] += step
        t += step
    gif[0].save(os.path.join(HERE, "preview_onfire_down_x3.gif"), save_all=True, append_images=gif[1:], duration=durs, loop=0)
    # 2배 전 프레임
    k = 2
    n = len(row)
    W = 60 + n * (FW * k + 4)
    H = 40 + 3 * (FH * k + 4)
    out = Image.new("RGBA", (W, H), BG)
    dr = ImageDraw.Draw(out)
    eprev.label(dr, 6, 6, "boss1_onfire_down 2배 · 열 0~3 ignite · 4~11 loop · 12~15 out · 1행 오버레이만 · 2행 fall 6 위 · 3행 death 11 위 · 빨간 점 = 피벗(96,220)")
    under = [None, ff[6], df[11]]
    for r in range(3):
        for c in range(n):
            x, y = 50 + c * (FW * k + 4), 30 + r * (FH * k + 4)
            cell = Image.new("RGBA", (FW, FH), BG)
            if under[r] is not None:
                cell.alpha_composite(under[r])
            cell.alpha_composite(row[c])
            out.alpha_composite(cell.resize((FW * k, FH * k), Image.NEAREST), (x, y))
            dr.rectangle((x + PIV[0] * k - 1, y + PIV[1] * k - 1, x + PIV[0] * k + 1, y + PIV[1] * k + 1), fill=(220, 60, 60, 255))
            if r == 0:
                eprev.label(dr, x + 4, y + 4, str(c))
    out.save(os.path.join(HERE, "preview_onfire_down_x2.png"))


if __name__ == "__main__":
    if "--legacy" not in sys.argv:   # 61라운드: 보스 1.5배 네이티브·균열 기둥·고친 촛대는 boss61/ 이 만든다 — 이 빌드는 옛 판(192×240 등)으로 덮어씀
        sys.exit("61라운드 이후 이 빌드는 assets 를 옛 그림으로 덮어씁니다. boss61/hires_build.py · boss61/build.py 를 쓰세요(꼭 필요하면 --legacy).")
    sys.argv = [a for a in sys.argv if a != "--legacy"]
    row, meta = build()
    previews(row, meta)
    print("onfire_down colors", meta["colors"], "offsets", meta["frameOffsets"])
