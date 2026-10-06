"""개성 카드 그림(ui_traits) 강조색 — 칼 = 은선 백광 획·달 분신 → 서리, 단검 = 호박 발톱 획·X 불티 → 독.
카드는 Gemini 콘셉트를 카드 팔레트로 양자화한 '장면' 이라 같은 색이 주인공 균열·술 웅덩이·흰 옷에도 쓰인다 →
색만 보지 않고 '획' 덩어리만 고른다: 강조색 픽셀의 8-이웃 연결 덩어리 중 가늘고 긴 것(칼: 긴 변 ≥ 6·채움 ≤ 0.6 / 단검: 긴 변 ≥ 7·채움 ≤ 0.55, 크기 ≥ 5).
작은 점(주인공 균열·눈)·뭉친 덩어리(술 웅덩이·흰 옷)는 그대로. 달 청백 M0 은 달 분신에만 쓰이므로 통째로.
단검의 X1·A27(크림 흰색)은 흰 옷에도 쓰여 빼고 A20~A26 만. 불·술 메커니즘 카드(불티 난타·독주 투척·취한 그림자)는 그대로(불은 무기 색이 아니라 환경 색 — 개성 fx 와 같은 판단)."""
import os

from PIL import Image

import ramps as R
import recolor as RC

K_STROKE = {"#ffffff": R.FROST["white"], "#fff4dc": R.FROST["white"], "#ebeced": R.FROST["pale"], "#d8d9db": R.FROST["main"],
            "#c5c6c9": R.FROST["f5"], "#b2b4b8": R.FROST["f3"]}
K_MOON = {"#c8d8f0": "#b4e6fa"}
D_STROKE = {"#f4de9b": R.POISON["a26"], "#eecc78": R.POISON["pale"],
            "#e8b858": "#d878ff", "#e2a33c": R.POISON["main"], "#dc8e23": "#a84ce8", "#d67a11": R.POISON["p4"], "#b0611a": R.POISON["p3"]}
D_SKIP = {"dagger_d_sparkFlurry.png", "dagger_liquorThrow.png", "dagger_d_ghostFire.png"}
K_SKIP = set()


def stroke_mask(im, keys, min_len=10, max_fill=0.5, min_size=6):
    W, H = im.size
    px = im.load()
    ks = {RC.h2t(k) for k in keys}
    seen = [[False] * W for _ in range(H)]
    mask = Image.new("L", (W, H), 0)
    mp = mask.load()
    for y in range(H):
        for x in range(W):
            if seen[y][x] or not px[x, y][3] or px[x, y][:3] not in ks:
                continue
            st, comp = [(x, y)], []
            seen[y][x] = True
            while st:
                cx, cy = st.pop()
                comp.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < W and 0 <= ny < H and not seen[ny][nx] and px[nx, ny][3] and px[nx, ny][:3] in ks:
                            seen[ny][nx] = True
                            st.append((nx, ny))
            xs, ys = [p[0] for p in comp], [p[1] for p in comp]
            w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
            if len(comp) >= min_size and max(w, h) >= min_len and len(comp) / float(w * h) <= max_fill:
                for p in comp:
                    mp[p] = 255
    return mask


def apply(weapon, rels):
    out = {}
    for rel in rels:
        b = os.path.basename(rel)
        p = os.path.join(RC.SPR, rel)
        if weapon == "katana":
            if b in K_SKIP:
                continue
            im = Image.open(p).convert("RGBA")
            n = RC.lut_image(im, K_STROKE, stroke_mask(im, K_STROKE, 6, 0.6, 5))
            n += RC.lut_image(im, K_MOON)
        else:
            if b in D_SKIP:
                continue
            im = Image.open(p).convert("RGBA")
            n = RC.lut_image(im, D_STROKE, stroke_mask(im, D_STROKE, 7, 0.55, 5))
        if n:
            im.save(p, optimize=True)
        out[b] = n
    return out
