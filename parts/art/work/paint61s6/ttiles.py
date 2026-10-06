"""61 단계 6 (P14 §1) — 수련장 타일셋 `assets/tiles/v2/stage1_training.png/.json` (64도트 = 1칸, pixelScale 0.5).

성문 타일셋(stage1_gate, 61 P3 재작업본)의 변주: 인덱스·키·벽 쌓기 규칙·tileLights 를 그대로 두고
- 바닥 0~3·통로 4·방 바닥 start/trial/rest(23~34) = 새로 그린 '갈퀴로 고른 모래 마당'(밝고 고요한 톤, 64 주기로 이음),
  trial 은 발자국, rest 는 짚 멍석 조각. boss(35~38, 만취 그림자 연습방) = 성문 큰 판석을 한 단 밝힘.
- 나머지 칸(벽·문·그늘·공허·엄폐 담)은 램프 안에서 한 단 밝힘(발광 23~27·백열은 그대로).
- 데칼(바퀴 자국·문빛 웅덩이)은 수련장에 맞지 않아 목록에서 뺀다(그림 칸은 남음). floorFeatures 는 grate 만.
색: lopad gray + 1층 램프 + v2 재질 SL·WD·PL — 새 색 없음. 반투명은 그늘 칸(53~57)만(원본 그대로).
"""
import json
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
sys.path.insert(0, os.path.join(WORK, "v2_outer"))
from kit import G, A, SL, WD, PL  # noqa: E402

TIL = os.path.join(ROOT, "assets", "tiles", "v2")
N = 64


def h32(*v):
    x = 2166136261
    for a in v:
        x = ((x ^ (int(a) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    x ^= x >> 13
    x = (x * 0x5bd1e995) & 0xFFFFFFFF
    return (x ^ (x >> 15)) & 0xFFFF


def hf(*v):
    return h32(*v) / 65535.0


def vnoise(x, y, s, seed, period=N):
    gx, gy = x / s, y / s
    x0, y0 = math.floor(gx), math.floor(gy)
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    P = int(round(period / s))

    def r(i, j):
        return hf(i % P, j % P, seed)
    a = r(x0, y0) + (r(x0 + 1, y0) - r(x0, y0)) * fx
    b = r(x0, y0 + 1) + (r(x0 + 1, y0 + 1) - r(x0, y0 + 1)) * fx
    return a + (b - a) * fy


SAND = [PL[1], PL[2], PL[3], PL[4], G[11], G[12]]      # 어두움 → 밝음


def sand(var, kind="plain"):
    """갈퀴 자국 모래(가로 골 8도트 간격, 64 주기 물결). var 별로 잔돌·자국 위치만 다름(가장자리 4도트 안은 공유)."""
    im = Image.new("RGBA", (N, N))
    p = im.load()
    for y in range(N):
        for x in range(N):
            n = vnoise(x, y, 32, 3) * 0.7 + vnoise(x, y, 16, 4) * 0.3
            k = 2 + (-1 if n < 0.2 else 0)
            e = min(x, y, N - 1 - x, N - 1 - y)
            if e >= 4 and hf(x // 2, y // 2, var, 17) > 0.97:
                k += 1 if hf(x, y, var) > 0.4 else -1        # 변형마다 다른 모래 알갱이(가장자리 4도트 밖)
            wy = (y + 1.5 * math.sin(2 * math.pi * x / N)) % 8
            if wy < 1.0 and k >= 2:
                k = 1                        # 골(그늘)
            elif 1.0 <= wy < 2.0 and k == 2 and (x // 3) % 4:
                k = 3                        # 골 윗변(빛, 끊어진 줄)
            if hf(x, y, 9) > 0.99:
                k += 1
            p[x, y] = SAND[max(0, min(5, k))]
    inner = lambda x, y: 6 <= x < N - 6 and 6 <= y < N - 6  # noqa: E731
    # 잔돌
    for i in range(3):
        cx, cy = 8 + int(hf(var, i, 1) * 48), 8 + int(hf(var, i, 2) * 48)
        if inner(cx, cy):
            p[cx, cy] = G[7]
            p[cx + 1, cy] = G[9]
            p[cx, cy + 1] = SL[3]
    if kind == "trial":                      # 발자국 한 줄(대각)
        for k in range(3):
            fx, fy = 14 + k * 14 + int(hf(var, k) * 4), 46 - k * 12
            for dy in range(-3, 4):
                for dx in range(-1, 2):
                    if inner(fx + dx + (k % 2) * 5, fy + dy):
                        p[fx + dx + (k % 2) * 5, fy + dy] = SAND[1] if dy > -2 else SAND[0]
    if kind == "rest":                       # 짚 멍석 조각
        x0, y0 = 8 + int(hf(var, 5) * 4), 18 + int(hf(var, 6) * 6)
        for y in range(y0, y0 + 24):
            for x in range(x0, x0 + 46):
                v = WD[4] if (y - y0) % 3 else WD[3]
                if (x - x0) % 15 == 0:
                    v = WD[3]
                p[x, y] = v
        for x in range(x0, x0 + 46):
            p[x, y0] = WD[5]
            p[x, y0 + 23] = WD[1]
            p[x, y0 + 24] = PL[1]
    if kind == "corridor":                   # 디딤돌 둘
        for (cx, cy) in ((20, 24), (44, 42)):
            for y in range(cy - 7, cy + 7):
                for x in range(cx - 10, cx + 10):
                    if ((x - cx) / 10) ** 2 + ((y - cy) / 7) ** 2 <= 1:
                        p[x, y] = G[9] if y < cy - 2 else (G[8] if y < cy + 4 else G[6])
            for x in range(cx - 8, cx + 8):
                p[x, cy + 7] = SL[2]
    return im


def lift_map():
    m = {}
    for ramp in (list(G), list(SL), list(WD), list(PL), [A[i] for i in range(16, 23)]):
        for i, c in enumerate(ramp):
            m.setdefault(c[:3], ramp[min(len(ramp) - 1, i + 1)][:3])
    return m


def build():
    src = Image.open(os.path.join(TIL, "stage1_gate.png")).convert("RGBA")
    meta = json.load(open(os.path.join(TIL, "stage1_gate.json"), encoding="utf-8"))
    cols = meta["columns"]
    lm = lift_map()
    out = src.copy()
    p = out.load()
    for y in range(out.height):
        for x in range(out.width):
            c = p[x, y]
            if c[3] and c[:3] in lm:
                p[x, y] = lm[c[:3]] + (c[3],)

    def put(idx, im):
        out.paste(im, ((idx % cols) * N, (idx // cols) * N))
    for i in range(4):
        put(i, sand(i))
    put(4, sand(9, "corridor"))
    for i, idx in enumerate((23, 24, 25, 26)):
        put(idx, sand(10 + i))
    for i, idx in enumerate((27, 28, 29, 30)):
        put(idx, sand(20 + i, "trial" if i % 2 == 0 else "plain"))
    for i, idx in enumerate((31, 32, 33, 34)):
        put(idx, sand(30 + i, "rest" if i == 0 else "plain"))
    out.save(os.path.join(TIL, "stage1_training.png"), optimize=True)

    m = dict(meta)
    m.update({
        "image": "stage1_training.png", "region": "training", "name": "수련장 — 고요한 모래 마당 (성문 타일 변주)",
        "version": "61 단계 6 (P14 §1) — 성문 v2(61 P3 재작업본) 변주: 바닥·통로·방 바닥 start/trial/rest 새로 그림(모래 마당), 나머지 한 단 밝힘",
        "roomFloorsNote": "start = 갈퀴 자국 모래, trial = 모래 + 발자국, rest = 모래 + 짚 멍석, boss = 성문 큰 판석 한 단 밝힘(만취 그림자 연습방)",
        "decals": [], "decalsNote": "수련장은 데칼 없음(성문 칸 64~68 그림은 남아 있으나 쓰지 않음)",
        "floorFeatures": {"grate": 61, "note": "선택. 바퀴 자국·웅덩이(60·62)는 수련장에서 쓰지 않음"},
        "border": "../border/gate/border.json",
        "borderNote": "외벽은 성문 Gemini 테두리를 재사용(성벽 안 마당). 수련장 전용 외벽 그림은 후속(필요하면)",
        "propsSheet": "../v3/stage1_gate_props.json",
        "propsNote": "수련장 소품은 structures/v3/training_*(무기 걸이 4·과제 표지판·도장 판·연습 깃발) + tutorial_dummy. 성문 props 시트는 보조",
        "redrawn61s6": [0, 1, 2, 3, 4, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34],
        "lifted61s6": "그 밖 칸 = 성문 칸을 같은 램프 안 한 단 밝힘(발광 23~27 그대로)",
        "source": "parts/art/work/paint61s6/ttiles.py (61 단계 6) · 원 칸 parts/art/work/struct61/tiles61_build.py(성문)",
    })
    for k in ("redrawn60", "redrawn61"):
        m.pop(k, None)
    json.dump(m, open(os.path.join(TIL, "stage1_training.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("tiles stage1_training", out.size)
    return out
