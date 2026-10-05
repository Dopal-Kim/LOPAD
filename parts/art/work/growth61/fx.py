"""각성 연출 fx (무기 공통, 회백 — 시스템이 갈래·길 색을 tint):

  fx/v4/awaken1_crack  1차 각성 0.8초(게임 정지 중): 무기를 감싼 껍질(마름모 고치)에 금이 번지고(0~3) → 번쩍(4) →
                        껍질 조각이 바깥으로 깨져 날아가며(5~11) 안에서 새 모양이 드러남. 12프레임.
  fx/v4/awaken2_bloom  2차 각성 1.0초: 무기 축을 따라 빛 가시가 돋고(0~5) → 끝마다 꽃잎 반짝(6~8) → 빛 고리가 퍼지고
                        티끌이 떠오르며 사라짐(7~13). 14프레임.
축 = 화면 −40°(오른쪽 위로 든 무기 기준). 시스템은 무기 쥔 손 쪽에 맞추고, 무기 각도에 맞춰 회전해도 된다(rotate 허용).
"""
import math
import os

from PIL import Image

import g61 as Z
from g61 import Cv, G, X0, h2, clamp, smooth

W = H = 256
C = (128, 128)
ANG = math.radians(-40)
CA, SA = math.cos(ANG), math.sin(ANG)


def loc(x, y):
    dx, dy = x + 0.5 - C[0], y + 0.5 - C[1]
    return dx * CA + dy * SA, -dx * SA + dy * CA


def wpt(u, v):
    return (C[0] + u * CA - v * SA, C[1] + u * SA + v * CA)


# 고치(껍질) = 축 길이 ±74, 폭 ±26 의 렌즈
def in_husk(u, v, a=74.0, b=26.0):
    return abs(u) <= a and abs(v) <= b * (1 - (u / a) ** 2) ** 0.85


SEEDS = []
_r = 11
for k in range(26):
    for _ in range(50):
        u = (h2(k, 1, 901) * 2 - 1) * 70
        v = (h2(k, 2, 901 + _) * 2 - 1) * 24
        if in_husk(u, v, 70, 24) and all(math.hypot(u - a, (v - b) * 1.6) > 11 for a, b in SEEDS):
            SEEDS.append((u, v))
            break


def cell(u, v):
    ds = sorted(((u - s[0]) ** 2 + (v - s[1]) ** 2, i) for i, s in enumerate(SEEDS))
    d1, i1 = ds[0]
    d2 = ds[1][0]
    return i1, math.sqrt(d2) - math.sqrt(d1)


HUSK = {}
for y in range(H):
    for x in range(W):
        u, v = loc(x, y)
        if in_husk(u, v):
            HUSK[(x, y)] = (u, v) + cell(u, v)


def crack_frames():
    ms = [60, 60, 60, 70, 70, 50, 50, 60, 70, 80, 80, 90]
    frames = []
    for i in range(12):
        cv = Cv(W, H)
        if i <= 4:
            R = [18, 38, 58, 76, 90][i]
            for (x, y), (u, v, ci, gap) in HUSK.items():
                rim = not in_husk(u, v, 72.5, 24.5)
                dist = math.hypot(u, v * 2.2)
                crack = gap < 1.25 and dist < R
                if i == 4:
                    if crack or rim:
                        cv.put(x, y, X0, 2, False)
                    elif gap < 2.4:
                        cv.put(x, y, G[12], 1, False)
                    elif (x + y) % 2 == 0 or h2(ci, 0, 3) > 0.5:
                        cv.put(x, y, G[9], 0, False)
                    continue
                if rim:
                    cv.put(x, y, G[9] if i >= 2 else G[7], 1, False)
                elif crack:
                    edge = R - dist < 8
                    cv.put(x, y, X0 if edge else G[12], 2, False)
                elif i >= 1 and gap < 2.2 and dist < R + 6:
                    cv.put(x, y, G[7], 1, False)
                elif i >= 2:
                    # 껍질 면: 조각마다 다른 회색(뒤 무기가 비치게 띄엄띄엄 — 반투명 대신 체크)
                    lv = 5 + int(h2(ci, 0, 7) * 3)
                    if (x + y + ci) % 3 == 0:
                        cv.put(x, y, G[lv], 0, False)
            # 금이 시작되는 심(가운데) 번쩍
            for r in range(0, 3 + i):
                for a in range(8):
                    p = wpt(math.cos(a * math.pi / 4) * r * 1.6, math.sin(a * math.pi / 4) * r * 0.7)
                    cv.put(p[0], p[1], X0 if r < 2 + i // 2 else G[12], 3, False)
        else:
            k = i - 5                                    # 0..6
            disp = 4 + 7 * k + 1.2 * k * k
            keep = 1 - k / 7.5
            for (x, y), (u, v, ci, gap) in HUSK.items():
                if gap < 1.2:
                    continue
                s = SEEDS[ci]
                dl = math.hypot(s[0], s[1] * 2.2) or 1
                du, dv = s[0] / dl, s[1] * 2.2 / dl
                # 조각 안 반지름이 keep 보다 크면 버림(조각이 작아지며 사라짐)
                rr = math.hypot(u - s[0], v - s[1])
                if rr > 14 * keep:
                    continue
                if k >= 4 and h2(x, y, k) > keep + 0.25:
                    continue
                spin = 0.06 * k * (1 if ci % 2 else -1)
                ru = s[0] + (u - s[0]) * math.cos(spin) - (v - s[1]) * math.sin(spin)
                rv = s[1] + (u - s[0]) * math.sin(spin) + (v - s[1]) * math.cos(spin)
                p = wpt(ru + du * disp * 1.1, rv + dv * disp * 0.9)
                lv = 6 + int(h2(ci, 0, 7) * 3) - k // 2
                edge = gap < 2.2
                c = X0 if (edge and k < 2) else G[12] if edge else G[max(3, lv)]
                cv.put(p[0], p[1], c, 1, False)
            # 안쪽 빛(새 모양이 드러나는 자리) — 얇은 렌즈 테가 퍼지고 사라짐
            if k <= 4:
                a, b = 74 + 10 * k, 8 + 6 * k
                for t in range(0, 720):
                    th = t / 720 * 2 * math.pi
                    if (t // (6 + 3 * k)) % 2 and k >= 2:
                        continue
                    p = wpt(a * math.cos(th), b * math.sin(th))
                    cv.put(p[0], p[1], X0 if k < 2 else G[12] if k < 4 else G[10], 2, False)
            # 불티
            for m in range(18):
                ang = h2(m, 1, 55) * 2 * math.pi
                r = 30 + (8 + 10 * h2(m, 2, 55)) * k
                if h2(m, 3, 55) > keep + 0.2:
                    continue
                p = (C[0] + math.cos(ang) * r, C[1] + math.sin(ang) * r * 0.75)
                cv.put(p[0], p[1], X0 if k < 3 else G[11], 3, False)
        frames.append(cv.image())
    return frames, ms


def bloom_frames():
    ms = [70] * 13 + [90]
    spines = []
    for k in range(13):
        u = -60 + 120 * k / 12 + 3 * (h2(k, 0, 71) - 0.5)
        side = 1 if k % 2 else -1
        L = 16 + 20 * h2(k, 1, 71) * (1 - abs(u) / 110)
        tilt = (h2(k, 2, 71) - 0.5) * 0.7 + 0.35 * (u / 60)
        spines.append((u, side, L, tilt, 0.03 * k))
    frames = []
    for i in range(14):
        cv = Cv(W, H)
        tt = i / 13
        # 축 빛(무기 자리) 0~8
        if i <= 9:
            for u in range(-70, 71):
                if abs(u) > 70 * smooth(0.0, 0.35, tt + 0.05):
                    continue
                if i >= 8 and (u + i) % 3:
                    continue
                for v in (-1, 0, 1):
                    p = wpt(u, v)
                    c = X0 if (i in (6, 7) or v == 0) else G[11]
                    cv.put(p[0], p[1], c, 1, False)
        # 돋는 가시(캡슐) + 끝 마름모 꽃잎
        for (u, side, L, tilt, delay) in spines:
            g = smooth(delay, delay + 0.3, tt)
            fade = smooth(0.62, 0.95, tt)
            if g <= 0.02:
                continue
            L2 = (L + 8) * g
            th = side * (math.pi / 2) + tilt * 0.8
            p0 = wpt(u, side * 2)
            p1 = wpt(u + math.cos(th) * L2 * 0.35, side * 2 + math.sin(th) * L2)
            hot = i in (6, 7)

            def cf(t, d, x, y, L2=L2, hot=hot, fade=fade):
                if fade > 0 and h2(x, y, i) < fade:
                    return None
                if t > 0.82 or hot:
                    return X0
                return G[12] if d < 0.5 else G[9]
            cv.chain([p0, p1], lambda t: 1.7 * (1 - t) + 0.85, cf, 2, False)
            if 5 <= i <= 9 and g > 0.85:
                r = {5: 2, 6: 4, 7: 5, 8: 3, 9: 2}[i]
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        q = abs(dx) + abs(dy)
                        if q <= r and (q == r or q <= 1 or i in (6, 7)):
                            cv.put(p1[0] + dx, p1[1] + dy, X0 if q <= 1 or i in (6, 7) and q == r else G[12], 3, False)
        # 빛 고리(7~12)
        if 7 <= i <= 12:
            k = i - 7
            a, b = 80 + 9 * k, 30 + 9 * k
            for t in range(900):
                th = t / 900 * 2 * math.pi
                if k >= 2 and (t // (5 + 2 * k)) % 2:
                    continue
                p = wpt(a * math.cos(th), b * math.sin(th))
                cv.put(p[0], p[1], X0 if k == 0 else G[12] if k < 3 else G[10], 1, False)
        # 떠오르는 티끌(8~13)
        if i >= 8:
            k = i - 8
            for m in range(16):
                if h2(m, 4, 13) < k / 7:
                    continue
                u = (h2(m, 1, 13) * 2 - 1) * 72
                v = (h2(m, 2, 13) * 2 - 1) * 30
                p = wpt(u, v)
                cv.put(p[0], p[1] - 3 * k - 4 * h2(m, 3, 13), X0 if k < 3 else G[11], 3, False)
        frames.append(cv.image())
    return frames, ms


COMMON = dict(anchor="player_pivot", offsetDots={"x": 0, "y": -60}, pivot={"x": 128, "y": 128}, followPlayer=True,
              axisDeg=-40, rotate="allowed",
              rotateRule="그림의 무기 축 = 화면 −40°(오른쪽 위). 무기 쥔 방향에 맞추려면 (무기 각도 − (−40°)) 만큼 회전, 아니면 그대로",
              tintable=True, tintRule="회백(X0·무채 G)만 — 시스템이 갈래·길 강조색을 setTint(곱)로 입힌다(1차 = 갈래 대표색, 2차 = pathTint[길]). 흰 그대로도 됨",
              depth="above_player", drawOver="lightmap", paletteSwap="none", weapon="all", p12="61 단계 4 P12 — 계약 art §26")


def build():
    fr, ms = crack_frames()
    m = dict(COMMON, usage="1차 각성 순간(게임 정지 0.8초) — 1회. 4프레임(번쩍)에 a1 오버레이를 켠다(그 전은 기본 무기)",
             durationMs=sum(ms), frameRoles={"crack": [0, 1, 2, 3], "flash": [4], "shatter": [5, 6, 7, 8, 9, 10, 11]},
             swapFrame=4, swapRule="swapFrame 시작에 무기 오버레이를 기본 → <무기>_<갈래>_a1 로 바꾼다",
             sfxHint="0 금 가는 소리 · 4 깨짐", shakeHint={"frame": 4, "px": 4, "ms": 160})
    Z.write_sheet("fx", "awaken1_crack", ["main"], {"main": fr}, ms, m, loop=False, glow={4, 5})
    fr, ms = bloom_frames()
    m = dict(COMMON, usage="2차 각성 순간 1.0초 — 1회. 6프레임(꽃잎 반짝)에 a2·a2_glow 오버레이를 켠다",
             durationMs=sum(ms), frameRoles={"sprout": [0, 1, 2, 3, 4, 5], "bloom": [6, 7, 8, 9], "ring": [7, 8, 9, 10, 11, 12], "motes": [8, 9, 10, 11, 12, 13]},
             swapFrame=6, swapRule="swapFrame 시작에 <무기>_<갈래>_a2(+_a2_glow, pathTint) 를 켠다",
             sfxHint="0 돋음 · 6 꽃핌")
    Z.write_sheet("fx", "awaken2_bloom", ["main"], {"main": fr}, ms, m, loop=False, glow={6, 7})
    return True


def preview(path):
    from PIL import ImageDraw
    rows = []
    for name in ("awaken1_crack", "awaken2_bloom"):
        im = Image.open(os.path.join(Z.STAGE, "fx", name + ".png")).convert("RGBA")
        n = im.width // W
        out = Image.new("RGBA", (n * (W + 2), 2 * (H + 2)), (18, 18, 22, 255))
        for c in range(n):
            f = im.crop((c * W, 0, (c + 1) * W, H))
            bg = Image.new("RGBA", (W, H), (27, 28, 33, 255))
            bg.alpha_composite(f)
            out.alpha_composite(bg, (c * (W + 2), 0))
            from looks import tint
            bg2 = Image.new("RGBA", (W, H), (27, 28, 33, 255))
            bg2.alpha_composite(tint(f, (110, 232, 214) if name.startswith("awaken1") else (255, 212, 110)))
            out.alpha_composite(bg2, (c * (W + 2), H + 2))
        rows.append(out)
    Wd = max(r.width for r in rows)
    o = Image.new("RGBA", (Wd, sum(r.height + 6 for r in rows)), (10, 10, 12, 255))
    y = 0
    for r in rows:
        o.alpha_composite(r, (0, y))
        y += r.height + 6
    o.convert("RGB").save(path)


if __name__ == "__main__":
    build()
    preview(os.path.join(Z.HERE, "preview_fx.png"))
