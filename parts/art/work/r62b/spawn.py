"""루프 1 요청(시스템 A → 아트) — fx/v3/spawn_ink: 적 등장 예고 바닥 먹 번짐(약 1초).

한 방울이 떨어져 바닥에 먹이 번지고(0~9), 번진 먹에서 붓 자국 같은 먹 기운이 일어선 뒤(6~9),
10 에서 튀며 적이 나타나고(spawnFrame), 11~13 에 먹이 말라 고리로 줄어 사라진다.
색: 먹 4단 + 젖은 먹 윤(차가운 청회색, rim 과 같은 색) + 접지 그림자(반투명 (10,11,16)). paletteSwap none.
"""
import math

from PIL import Image

from common import INK, COLD_RIM, b2, bayer, SRC, hexc

FW, FH = 208, 176
PX, PY = 104, 132          # 피벗 = 적 발(바닥 먹 가운데)
SQ = 0.5                   # 쿼터뷰 바닥 타원 납작함
DUR = [90, 90, 90, 90, 90, 90, 90, 90, 90, 90, 60, 90, 90, 100]
SPAWN = 10
SHADOW = (10, 11, 16)


def h2(x, y, s):
    n = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return (n & 0xFFFF) / 65535.0


def vnoise(x, y, s):
    xi, yi = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - xi, y - yi
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = h2(xi, yi, s), h2(xi + 1, yi, s)
    c, d = h2(xi, yi + 1, s), h2(xi + 1, yi + 1, s)
    return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fy


def blot_r(ang, R, seed):
    """각도별 번짐 반경(가장자리 흔들림 + 뻗는 먹 줄기 5)."""
    w = 1.0 + 0.14 * (vnoise(math.cos(ang) * 2.2 + 5, math.sin(ang) * 2.2 + 5, seed) - 0.5) * 2
    for k in range(5):
        a0 = k * 1.31 + seed * 0.7
        d = math.atan2(math.sin(ang - a0), math.cos(ang - a0))
        w += 0.16 * math.exp(-(d * d) / 0.05) * (0.6 + 0.4 * h2(k, seed, 3))
    return R * w


def frame(i):
    im = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    p = im.load()
    # 반경 곡선: 방울(0) → 퍼짐(1~9, 감속) → 튐(10) → 마름(11~13)
    if i <= 9:
        R = 5 + 59 * (1 - (1 - i / 9) ** 2.2)
    elif i == SPAWN:
        R = 68
    else:
        R = 68 - (i - SPAWN) * 4
    hole = 0.0 if i <= SPAWN else [0.45, 0.68, 0.86][i - SPAWN - 1]     # 마르며 가운데부터 비는 고리
    for y in range(FH):
        for x in range(FW):
            dx, dy = x - PX, (y - PY) / SQ
            d = math.hypot(dx, dy)
            if d > 110:
                continue
            ang = math.atan2(dy, dx)
            r = blot_r(ang, R, 7)
            if d <= r:
                t = d / r
                if hole and t < hole + 0.08 * (vnoise(x * 0.15, y * 0.3, 2) - 0.5):
                    continue
                b = bayer(x, y)
                if i > SPAWN and h2(x >> 1, y >> 1, 5) < (i - SPAWN) * 0.2 and t < 0.94:
                    continue
                if d > r - 2.4 and i <= SPAWN:
                    c = (COLD_RIM[2] if b < 0.5 else COLD_RIM[1]) if dy < 0 else COLD_RIM[0]   # 젖은 먹 윤(위쪽이 달빛)
                elif d > r - 3.5:
                    c = INK[3]
                else:
                    n = vnoise(x * 0.12, y * 0.24, 4 + i // 3)
                    c = INK[0] if n < 0.45 else INK[1] if n < 0.7 else INK[2]
                p[x, y] = c + (255,)
            elif d <= r + 5 and i <= SPAWN:
                a = int(70 * (1 - (d - r) / 5))                          # 번짐 앞 젖은 그림자
                if a > 0:
                    p[x, y] = SHADOW + (a,)
    # 흩뿌린 먹 방울(퍼질 때 · 튈 때 더 멀리)
    if 1 <= i <= SPAWN + 1:
        for k in range(16 if i == SPAWN else 9):
            ang = h2(k, 11, 1) * math.tau
            dist = (R + 6 + h2(k, 12, 1) * (34 if i == SPAWN else 14)) * (1.0 if i != SPAWN + 1 else 1.1)
            cx, cy = PX + math.cos(ang) * dist, PY + math.sin(ang) * dist * SQ
            rr = 1 + int(h2(k, 13, 1) * (3 if i == SPAWN else 2))
            for yy in range(-rr, rr + 1):
                for xx in range(-rr, rr + 1):
                    if xx * xx + yy * yy * 2 <= rr * rr and 0 <= int(cx + xx) < FW and 0 <= int(cy + yy) < FH:
                        p[int(cx + xx), int(cy + yy)] = INK[1] + (255,)
    # 일어서는 먹 기운(붓 자국 기둥) 6~10
    if 5 <= i <= SPAWN:
        k_up = (i - 4) / 6
        for s in range(5):
            bx = PX + (s - 2) * 11 + int((h2(s, 21, 2) - 0.5) * 6)
            top = PY - int((44 + 60 * h2(s, 22, 2) + (30 if s == 2 else 0)) * k_up) - (16 if i == SPAWN else 0)
            base_w = 5 + (3 if s == 2 else 0)
            for y in range(top, PY - 2):
                t = (PY - y) / max(1, PY - top)
                sway = math.sin(y * 0.18 + s + i * 0.9) * 2.5 * t
                w = base_w * (1 - t) ** 0.8 + 0.4
                for x in range(int(bx + sway - w), int(bx + sway + w) + 1):
                    if 0 <= x < FW and 0 <= y < FH:
                        b = bayer(x, y)
                        if t > 0.75 and b > (1 - t) * 4:
                            continue                           # 끝이 붓처럼 갈라짐
                        edge = x >= int(bx + sway + w) - 0
                        p[x, y] = (COLD_RIM[0] if edge and t > 0.2 else INK[1] if t < 0.5 else INK[2]) + (255,)
    return im


def build(preview_path=None):
    frames = [frame(i) for i in range(len(DUR))]
    meta = {
        "directions": ["any"], "pivot": {"x": PX, "y": PY},
        "anchor": "spawn_point", "anchorNote": "피벗 = 적이 나타날 발 위치(바닥). 적 피벗과 같은 점에 놓는다",
        "depth": "floor", "drawOver": "lightmap",
        "drawOverNote": "예고는 어둠 속에서도 읽혀야 해서 조명 위(제안). 너무 밝으면 조명 아래 + 젖은 윤만 가산.",
        "spawnFrame": SPAWN, "spawnAtMs": sum(DUR[:SPAWN]), "durationMs": sum(DUR),
        "phaseFrames": {"drop": [0], "spread": [1, 2, 3, 4, 5, 6, 7, 8, 9], "rise": [5, 6, 7, 8, 9], "burst": [SPAWN],
                        "dry": [11, 12, 13]},
        "timingNote": "spawnAtMs(900) 에 적을 세운다(적 등장 연출 시작). 경고 시간을 늘리려면 spread 끝 칸(9)을 stateHold 로 유지 — 그림은 맞는다",
        "holdFrame": 9,
        "radiusDots": {"max": 68, "squash": SQ, "note": "바닥 타원 가로 반경(도트). 약 1칸(지름 2칸)"},
        "colors": [hexc(c) for c in INK[:4]] + [hexc(c) for c in COLD_RIM[:3]],
        "palette": "먹(gray 1~3 + #0d0d10) + 젖은 먹 윤 차가운 청회색(적 림과 같은 색) + 접지 그림자 반투명 (10,11,16). paletteSwap none",
        "paletteSwap": "none", "version": "v3-r62b", "source": SRC + " · spawn.py",
        "design": "그림 세계(먹 붓) 결 — 바닥에 먹이 번지고 붓 자국 같은 먹 기운이 일어서며 적이 그려져 나온다. 소리 쪽 '적 등장 예고'와 같은 시각(spawnAtMs)에 맞춘다.",
    }
    b2.write_sheet("fx", "spawn_ink", frames, FW, FH, meta, rows=1, durations=DUR, loop=False)
    if preview_path:
        from common import board
        items = []
        for im in frames:
            bg = Image.new("RGBA", (FW, FH), (70, 56, 44, 255))
            bg.alpha_composite(im)
            items.append(bg)
        board(items, k=2, max_w=1600).save(preview_path)
    return frames
