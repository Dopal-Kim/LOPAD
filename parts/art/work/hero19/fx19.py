"""P19 위협감 fx — fx/v3/hero_* (계약 §31 형식: 트림 아틀라스, pixelScale 0.5, 주인공 피벗 기준).

  hero_eye_trail      눈빛 꼬리 — 움직일 때 눈 자리에 남는 호박 잔광 띠(진행 방향으로 회전, 제자리에서 꼬리부터 식음). 30ms(대쉬 16ms) 마다 겹쳐 찍음
  hero_ember_breath   대기 불씨 숨결 — 가슴 균열·어깨 혼불에서 피어오르는 불티(루프)
  hero_dash_afterimage 대쉬 잔상 — 대쉬 1·2·3 프레임 실루엣의 먹빛 몸 + 등 쪽 불씨 테두리 + 균열 → 구멍 뚫리며 재·불티로
  hero_skid_dust      급정지·방향 전환·대쉬 제동 — 발 밑 긁힘 줄 + 재 먼지 덩이 + 불티(새 방향 반대쪽으로 흩날림)
  dash_trail (갱신)   기존 대쉬 잔상 시트를 새 대쉬 2 프레임 실루엣으로 다시(같은 틀·프레임·ms·필드)
색: 주인공 30색 안 — 재 G1~G8 · 먹 SL0 · 호박 A19~A26(층 램프 교체 없음, paletteSwap none). 반투명 0.
"""
import json
import math
import os
import random

from PIL import Image

import body19 as B
import sync19 as S
from hero import A, G, SL, OUT

HERE = B.HERE
DIRS = B.DIRS
DVEC = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}
SRC = "parts/art/work/hero19/fx19.py (P19 주인공 위협감 fx)"
COMMON = {"version": "v3-p19", "pixelScale": 0.5, "paletteSwap": "none",
          "paletteSwapNote": "53라운드 Q62·Q68 — fx 는 지역·층 바닥 팔레트 교체에서 제외(그린 색 그대로).",
          "palette": "주인공 v3 30색 안(재 G · 먹 SL0 · 호박 A19~A26)", "semiTransparent": False, "source": SRC,
          "unitNote": "길이 필드(pivot·px 값)는 이 시트 도트 단위. 논리 px = 도트 × pixelScale(0.5)."}


def rgba(c):
    return tuple(c[:3]) + (255,) if len(c) >= 3 else c


def put(im, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), rgba(c))


def body_frames(body, col):
    """새로 내보낸 몸 격자(out/grid)의 한 열 — 방향별 (mask, amber, 이미지)."""
    p = os.path.join(S.GRID, "player", "v3", body + ".json")
    m = json.load(open(p, encoding="utf-8"))
    im = Image.open(p[:-5] + ".png").convert("RGBA")
    fw, fh = m["frameWidth"], m["frameHeight"]
    out = {}
    for r, d in enumerate(m["directions"]):
        c = im.crop((col * fw, r * fh, (col + 1) * fw, (r + 1) * fh))
        px = c.load()
        mask = {(x, y) for y in range(fh) for x in range(fw) if px[x, y][3]}
        amber = {(x, y) for (x, y) in mask if px[x, y][0] > 170 and px[x, y][0] - px[x, y][2] > 90 and px[x, y][1] > 70}
        out[d] = (mask, amber, c)
    return out, m


def sheet(frames_by_dir, meta, rel):
    m = dict(COMMON)
    m.update(meta)
    m["directions"] = list(frames_by_dir.keys())
    m["layout"] = "row = direction (directions order), column = frame index"
    m["frameIndex"] = "row * frames + column"
    m["fps"] = round(1000.0 * len(m["frameDurationsMs"]) / sum(m["frameDurationsMs"]), 2)
    cols = set()
    for lst in frames_by_dir.values():
        for im in lst:
            a = set(im.getchannel("A").getdata())
            assert a <= {0, 255}, (rel, "semi")
            cols |= {p[:3] for p in im.getdata() if p[3]}
    m["colors"] = len(cols)
    assert len(cols) <= 16, (rel, len(cols))
    return S.write_grid(rel, frames_by_dir, m)


# =============================================================================
# 눈빛 꼬리 — 16×16 피벗 (8,8) = 눈. 6 프레임 1회. 방향 무관(1행 'any')
# =============================================================================
def eye_trail():
    """오른쪽을 향해 그린 가는 꼬리(머리 = 피벗 = 눈, 꼬리 = 왼쪽). 시스템이 이동 방향으로 회전.
    한 장이 꼬리째 남고 꼬리 끝부터 식어 머리 쪽으로 줄어든다 → 30ms 마다 겹쳐 찍으면 끊기지 않는 잔광 띠."""
    ms = [30, 40, 40, 50, 60, 70]
    L0 = [24, 19, 14, 9, 5, 2]
    frames = []
    for f in range(6):
        im = Image.new("RGBA", (48, 8), (0, 0, 0, 0))
        n = L0[f]
        for k in range(n):
            t = k / max(1, n - 1)                    # 0 머리 → 1 꼬리
            if f == 0:
                c = A[26] if k < 2 else (A[25] if t < 0.35 else (A[23] if t < 0.7 else A[21]))
            elif f <= 2:
                c = A[25] if t < 0.25 else (A[23] if t < 0.6 else A[21])
            else:
                c = A[23] if t < 0.3 else (A[21] if t < 0.7 else A[19])
            if f >= 3 and k % 2 and t > 0.4:
                continue                              # 식으며 끊김
            put(im, 44 - k, 4, c)
        if f < 2:
            put(im, 44, 3, A[25])                     # 머리 위로 새는 한 점(눈빛과 같은 결)
        frames.append(im)
    return sheet({"any": frames}, {
        "action": "hero_eye_trail", "frameWidth": 48, "frameHeight": 8, "pivot": {"x": 44, "y": 4},
        "frameDurationsMs": ms, "loop": False, "anchor": "eye_anchor", "followsPlayer": False, "depth": "above_player",
        "rotate": True, "drawnFacing": "right",
        "rotateRule": "이동 방향 각도로 회전(머리 = 눈, 꼬리가 진행 반대쪽). 8방향 스냅 권장(픽셀 선이 덜 깨짐)",
        "spawn": {"rule": "이동 속도 ≥ 달리기의 60% 동안 30ms 마다, 대쉬 동안 16ms 마다 하나(방향 전환 미끄럼·급정지 중에는 찍지 않음 — 꼬리가 몸을 가로지름) — 그 순간 몸 시트 eyeAnchors[방향][프레임](도트, 몸 피벗 기준 = (x−48, y−138))에 놓고 제자리에서 식게 둔다",
                  "skipWhen": "eyeAnchors 값이 null(뒷모습 up · 대기 눈 깜빡 5 · 사망)", "maxAlive": 14},
        "blend": "NORMAL (어둠 속에서 ADD 는 과함 — 광원 없이도 호박이 읽힘)",
        "note": "P19 위협감: 움직일 때 분노한 눈에서 남는 호박 잔광. 머리 백열 → 꼬리 끝부터 식어 짧아지며 끊김. 겹쳐 찍히면 눈 높이에 가는 빛 띠가 뒤로 늘어진다.",
        "glowFrames": [0], "glowRule": "A26 은 0 프레임 머리 2점만",
    }, "fx/v3/hero_eye_trail")


# =============================================================================
# 불씨 숨결 — 48×80 피벗 (24,72) = 가슴 균열(chestAnchors). 12 × 80ms 루프
# =============================================================================
def ember_breath():
    ms = [80] * 12
    rnd = random.Random(1914)
    embers = []                       # (시작 프레임, x0, y0, 흔들림 위상, 속도)
    for k in range(7):
        embers.append((rnd.randrange(12), rnd.uniform(14, 34), rnd.uniform(58, 74), rnd.uniform(0, 6.28), rnd.uniform(3.2, 5.0)))
    frames = []
    for f in range(12):
        im = Image.new("RGBA", (48, 80), (0, 0, 0, 0))
        for (s, x0, y0, ph, v) in embers:
            t = (f - s) % 12
            if t > 8:
                continue
            x = x0 + 2.2 * math.sin(ph + t * 0.9)
            y = y0 - v * t
            c = [A[25], A[25], A[23], A[23], A[21], A[21], A[19], A[19], A[19]][t]
            put(im, x, y, c)
            if t < 3:
                put(im, x, y + 1, A[21])
        frames.append(im)
    return sheet({"any": frames}, {
        "action": "hero_ember_breath", "frameWidth": 48, "frameHeight": 80, "pivot": {"x": 24, "y": 72},
        "frameDurationsMs": ms, "loop": True, "anchor": "chest_anchor", "followsPlayer": True, "depth": "above_player",
        "playWhen": "player_idle / player_idle_free 재생 중(전투 대기). 다른 동작으로 바뀌면 끔",
        "note": "P19 대기 위협감: 가슴 균열에서 불티가 숨결처럼 피어올라 흔들리며 식는다(7점, 서로 다른 위상). 몸 시트의 균열 맥동(2·3 프레임 pulse)과 함께.",
    }, "fx/v3/hero_ember_breath")


# =============================================================================
# 대쉬 잔상 — 96×144 피벗 (48,138). 행 = 방향, 열 = 변주(대쉬 1·2·3 프레임) × 4 식음
# =============================================================================
def dash_afterimage():
    ms = [40, 50, 60, 70]
    out = {d: [] for d in DIRS}
    for var, col in enumerate((1, 2, 3)):
        cells, _ = body_frames("player_dash", col)
        for d in DIRS:
            mask, amber, _ = cells[d]
            bx, by = (-DVEC[d][0], -DVEC[d][1])
            rnd = random.Random(700 + 10 * var + DIRS.index(d))
            for f in range(4):
                im = Image.new("RGBA", (96, 144), (0, 0, 0, 0))
                sh = [0, 2, 5, 9][f]
                for (x, y) in mask:
                    back = (x + bx, y + by) not in mask
                    if f == 1 and (x + y) % 3 == 0:
                        continue
                    if f == 2 and (x + 2 * y) % 3 != 0:
                        continue
                    if f == 3:
                        continue
                    if (x, y) in amber:
                        c = [A[23], A[21], A[19]][f]
                    elif back:
                        c = [A[21], A[19], G[2]][f]          # 등 쪽(뒤) 가장자리 = 불씨 테
                    else:
                        c = [SL[0], G[1], G[1]][f]           # 먹빛 몸
                    put(im, x + bx * sh, y + by * sh, c)
                n = [0, 8, 12, 10][f]
                pts = sorted(mask)
                for _ in range(n):
                    x, y = pts[rnd.randrange(len(pts))]
                    s = (4 + 6 * f) * rnd.uniform(0.6, 1.3)
                    put(im, x + bx * s, y + by * s - s * 0.5, rnd.choice([A[21], A[23], G[4], G[5]]) if f < 3 else rnd.choice([A[19], G[3]]))
                out[d].append(im)
    return sheet(out, {
        "action": "hero_dash_afterimage", "frameWidth": 96, "frameHeight": 144, "pivot": {"x": 48, "y": 138},
        "frameDurationsMs": ms * 3, "loop": False, "anchor": "player_pivot", "followsPlayer": False, "depth": "below",
        "variants": {"dash1": [0, 3], "dash2": [4, 7], "dash3": [8, 11]},
        "spawn": {"rule": "대쉬 몸 1·2·3 프레임이 시작될 때 그 자리(주인공 피벗·방향 행)에 같은 번호 변주 하나씩 → 먹·불씨 잔상 3장. 변주 범위만 재생(4프레임 220ms)",
                  "dashFrames": [1, 2, 3]},
        "heroSource": "player/v3/player_dash 열 1·2·3 실루엣(P19 새 대쉬)",
        "note": "P19 'LOW LUNGING DASH' 잔상: 먹빛 몸 + 등 쪽 가장자리 불씨 테 + 몸의 균열 자리 호박 → 구멍이 뚫리며 뒤로 밀리고 재·불티로 흩어짐.",
        "glowFrames": [],
    }, "fx/v3/hero_dash_afterimage")


# =============================================================================
# 급정지·방향 전환 먼지 — 160×72 피벗 (80,56) = 발. 행 = 새 방향(먼지는 반대쪽으로), 6 프레임
# =============================================================================
def skid_dust():
    ms = [40, 50, 50, 60, 70, 80]
    out = {}
    for d in DIRS:
        bx, by = (-DVEC[d][0], -DVEC[d][1])          # 흩날리는 쪽 = 새 방향 반대(옛 진행 방향)
        sq = 0.5 if by else 1.0                       # 위아래는 바닥 원근으로 납작하게
        rnd = random.Random(31 + DIRS.index(d))
        puffs = [(rnd.uniform(4, 34), rnd.uniform(-12, 12), rnd.uniform(4.5, 9.0), rnd.uniform(0.6, 1.2)) for _ in range(9)]
        sparks = [(rnd.uniform(0, 20), rnd.uniform(-10, 10), rnd.uniform(18, 40), rnd.uniform(0.2, 1.0)) for _ in range(10)]
        frames = []
        for f in range(6):
            im = Image.new("RGBA", (160, 72), (0, 0, 0, 0))
            t = f / 5.0
            # 긁힘 줄 2개(0~2 프레임)
            if f <= 2:
                for lane in (-3, 3):
                    L0 = 26 - 6 * f
                    for k in range(int(L0)):
                        x = 80 + bx * k + (lane if by else 0)
                        y = 56 + by * k * sq + (lane * 0.5 if bx else 0)
                        put(im, x, y, [G[2], G[2], G[1]][f] if k % 5 else OUT)
            # 재 먼지 덩이: 뒤로 퍼지며 커졌다 작아짐
            for (dist, lat, r, sp) in puffs:
                rr = r * (0.6 + 0.9 * t) * (1.0 - 0.6 * max(0.0, t - 0.6) / 0.4)
                cx = 80 + bx * (dist * (0.5 + t)) + (lat if by else 0) * (0.6 + t)
                cy = 54 + by * (dist * (0.5 + t)) * sq + (lat * 0.3 if bx else 0) - 6 * t * sp
                if rr < 1:
                    continue
                for yy in range(int(-rr), int(rr) + 1):
                    for xx in range(int(-rr * 1.3), int(rr * 1.3) + 1):
                        if (xx / 1.3) ** 2 + yy ** 2 > rr * rr:
                            continue
                        if f >= 4 and (xx + yy + f) % 2:
                            continue
                        c = G[6] if yy < -rr * 0.4 else (G[5] if yy < rr * 0.3 else G[3])
                        if f >= 3:
                            c = [G[4], G[3], G[2]][f - 3] if yy < 0 else G[2]
                        put(im, cx + xx, cy + yy * sq, c)
            # 불티: 뒤·위로 튀며 식음
            for (s0, lat, v, up) in sparks:
                dd = s0 + v * t
                x = 80 + bx * dd + (lat if by else 0)
                y = 52 + by * dd * sq - 18 * up * t + 14 * t * t
                if f < 5:
                    put(im, x, y, [A[26], A[25], A[23], A[21], A[19]][f])
                    if f < 2:
                        put(im, x - bx, y - by, A[21])
            frames.append(im)
        out[d] = frames
    return sheet(out, {
        "action": "hero_skid_dust", "frameWidth": 160, "frameHeight": 72, "pivot": {"x": 80, "y": 56},
        "frameDurationsMs": ms, "loop": False, "anchor": "player_pivot", "followsPlayer": False, "depth": "below",
        "rowRule": "행 = 새로 향하는 방향(먼지·불티는 그 반대쪽 = 옛 진행 쪽으로 흩날림)",
        "uses": ["player_turn_skid 0 프레임(새 방향 행)", "player_dash 4 프레임 제동(대쉬 방향 행)",
                 "달리기 중 입력을 놓아 멈출 때(진행 방향 행) — 급정지", "높은 곳에서 착지(선택, 아래 행)"],
        "note": "P19 급정지·착지 먼지: 발 밑 긁힘 줄 2 → 재 먼지 덩이가 옛 진행 쪽으로 퍼지며 떠오름 → 체크로 성겨져 사라짐. 불티 6개가 튀어 식음.",
        "glowFrames": [0],
        "glowRule": "A26 은 0 프레임 불티 머리만",
    }, "fx/v3/hero_skid_dust")


# =============================================================================
# dash_trail 갱신 — fx_v3/feel_motion.dash_trail 그대로, 실루엣 입력만 새 대쉬 2 프레임
# =============================================================================
def dash_trail():
    import sys
    sys.path.insert(0, os.path.join(S.WORK, "fx_v3"))
    import feel_motion as FM
    cells, m = body_frames("player_dash", 2)
    FM.hero_cells = lambda sheet, col: ({d: (cells[d][0], cells[d][1]) for d in DIRS}, 96, 144, m["pivot"])
    FM.carry = lambda name, ms, extra=None: dict(extra or {}, frameDurationsMs=ms)
    frames, _ = FM.dash_trail()
    old = S.src_meta("fx/v3/dash_trail")
    old = {k: v for k, v in old.items() if k not in ("frames",)}
    old["heroSource"] = "player/v3/player_dash frame 2 (P19 새 대쉬 실루엣 — hero19/fx19.py 가 fx_v3/feel_motion.dash_trail 로 다시 그림)"
    old["p19"] = "P19: 새 대쉬(낮게 파고드는 자세) 실루엣으로 다시. 틀·프레임·ms·필드 그대로"
    old["source"] = SRC
    cols = set()
    for lst in frames.values():
        for im in lst:
            cols |= {p[:3] for p in im.getdata() if p[3]}
    old["colors"] = len(cols)
    return S.write_grid("fx/v3/dash_trail", {d: frames[d] for d in old["directions"]}, old)


def build():
    for fn in (eye_trail, ember_breath, dash_afterimage, skid_dust, dash_trail):
        r = fn()
        print("fx", fn.__name__, r)
