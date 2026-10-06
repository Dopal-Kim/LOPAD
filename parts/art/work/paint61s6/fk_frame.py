"""61 단계 6 — 액자 `paint/frame.png` (9-slice). 낡은 나무 틀 + 바랜 종이 매트, 가운데 투명(방 화면 캡처가 들어감).

단위: 논리 px(pixelScale 1.0 — 키아트·입구 그림과 같은 판). 모서리 B×B 안에만 쇠 모서리판·못·옹이(늘어나지 않는 자리),
변 조각에는 변을 따라 흐르는 결만(늘려도 어색하지 않게). 빛: 왼쪽 위.
색: lopad gray(G) + v2 재질 WD(나무)·PL + UI 세피아 S0~S4(종이 매트 — 전환 연출은 UI 레이어). 새 색 없음.
"""
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
PAL = json.load(open(os.path.join(ROOT, "parts/art/palette/lopad.json"), encoding="utf-8"))
V2 = json.load(open(os.path.join(ROOT, "parts/art/work/v2_outer/palette_v2_proposal.json"), encoding="utf-8"))


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def _v2(key):
    v = V2[key] if key in V2 else V2.get("blocks", {}).get(key)
    if isinstance(v, dict):
        v = v.get("colors") or v.get("hex") or list(v.values())
    return [hx(c) for c in v]


G = [hx(c) for c in PAL["gray"]]
S = [hx(c) for c in PAL["ui"]["ramp"]]
WD = _v2("WD")
PL = _v2("PL")
A = [hx(c) for c in PAL["floors"][0]["ramp"]]

W = H = 128
B = 44                      # 9-slice 테 두께(네 변 같음)
CLEAR = (0, 0, 0, 0)


def h32(*v):
    x = 2166136261
    for a in v:
        x = ((x ^ (int(a) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    x ^= x >> 13
    x = (x * 0x5bd1e995) & 0xFFFFFFFF
    return (x ^ (x >> 15)) & 0xFFFF


def hf(*v):
    return h32(*v) / 65535.0


def side_of(x, y):
    d = {"top": y, "left": x, "bottom": H - 1 - y, "right": W - 1 - x}
    s = min(d, key=lambda k: (d[k], ["top", "left", "bottom", "right"].index(k)))
    return s, d[s]


def along(side, x, y):
    return x if side in ("top", "bottom") else y


def in_corner(x, y):
    return (x < B or x >= W - B) and (y < B or y >= H - B)


def draw():
    im = Image.new("RGBA", (W, H), CLEAR)
    p = im.load()
    lit_side = {"top": 1, "left": 1, "bottom": -1, "right": -1}
    for y in range(H):
        for x in range(W):
            side, d = side_of(x, y)
            a = along(side, x, y)
            ls = lit_side[side]
            c = CLEAR
            if d == 0:
                c = G[1]
            elif d <= 3:                                   # 바깥 둥근 테
                c = (WD[5] if d == 1 else WD[4]) if ls > 0 else (WD[1] if d == 1 else WD[2])
            elif d <= 5:                                   # 홈
                c = WD[1] if d == 4 else (WD[2] if ls > 0 else WD[0])
            elif d <= 20:                                  # 넓은 면 — 변을 따라 흐르는 결
                g = hf(d, 7, side in ("top", "bottom"))
                base = 3 if ls > 0 else 2
                k = base + (1 if g > 0.78 else (-1 if g < 0.25 else 0))
                if in_corner(x, y):                        # 모서리에서만 결이 흔들림·옹이
                    if hf(x // 3, y // 2, 11) > 0.93:
                        k -= 1
                if d in (6,):
                    k += 1 if ls > 0 else -1
                if d in (20,):
                    k -= 1
                c = WD[max(0, min(5, k))]
                # 닳은 자리(가장자리 결 하이라이트) — 결 줄 단위라 늘려도 이어진다
                if d == 7 and ls > 0 and hf(d, 3) > 0.2:
                    c = WD[5] if k >= 3 else WD[4]
            elif d <= 23:                                  # 안쪽 테 — 빛 반대(위·왼쪽 변은 아래를 봄 → 어둡게)
                c = (WD[1] if d == 21 else WD[2]) if ls > 0 else (WD[4] if d == 21 else WD[3])
            elif d <= 26:                                  # 매트에 드리운 틀 그림자
                c = G[1] if d == 24 else (S[0] if d == 25 else S[1])
                if ls < 0 and d >= 25:                     # 아래·오른 변은 그림자 짧게
                    c = S[2] if d == 25 else S[3]
            elif d <= 41:                                  # 종이 매트 — 넓은 얼룩 + 변을 따라 흐르는 섬유 몇 줄
                # 변 조각: 결이 변 방향으로만(늘려도 덩어리가 안 생김) · 모서리: 얼룩 덩어리
                n = hf(d, 17) * 0.75 + 0.1 if not in_corner(x, y) else hf(x // 5, y // 5, 5)
                k = 3
                if n > 0.80:
                    k = 4
                elif n < 0.10:
                    k = 2
                if d in (31, 37) and hf(d, side == "top", 41) > 0.3:     # 섬유 결(변 방향)
                    k = 2 if k == 3 else k
                if d == 27:
                    k = 4 if ls < 0 else 2
                c = S[k]
            elif d <= 43:                                  # 그림이 끼워지는 홈(어두운 선)
                c = S[1] if d == 42 else G[1]
            p[x, y] = c
    # 모서리 장식: 쇠 모서리판(L자) + 못 2 · 종이 얼룩 — 모서리 조각 안에만
    for cx, cy, sx, sy in ((0, 0, 1, 1), (W - 1, 0, -1, 1), (0, H - 1, 1, -1), (W - 1, H - 1, -1, -1)):
        for t in range(0, 17):
            for u in range(8, 15):
                for (xx, yy) in ((cx + sx * (u - 1), cy + sy * (t + 5)), (cx + sx * (t + 5), cy + sy * (u - 1))):
                    edge = u in (8, 14) or t == 16
                    lit = (sy > 0 and yy == cy + sy * 7) or (sx > 0 and xx == cx + sx * 7)
                    p[xx, yy] = G[2] if edge else (G[6] if lit else G[4])
        for (nx, ny) in ((cx + sx * 10, cy + sy * 17), (cx + sx * 17, cy + sy * 10)):
            p[nx, ny] = G[8]
            p[nx + sx, ny + sy] = G[2]
        # 녹 번짐 1점(층 램프 어두운 칸 — 발광 아님)
        p[cx + sx * 12, cy + sy * 20] = A[2]
        p[cx + sx * 20, cy + sy * 12] = A[1]
        # 종이 모서리 얼룩
        for k in range(28, 36):
            for j in range(28, 36):
                if (k - 28) + (j - 28) < 7 and hf(k, j, cx, cy) > 0.35:
                    p[cx + sx * k, cy + sy * j] = S[2]
    meta = {
        "width": W, "height": H, "pixelScale": 1.0,
        "slice": {"left": B, "right": B, "top": B, "bottom": B},
        "sliceNote": "Phaser NineSlice(leftWidth, rightWidth, topHeight, bottomHeight) = 44 · 44 · 44 · 44. 변 조각은 늘림(결이 변을 따라 흘러 "
                     "늘려도 이어짐), 모서리 44×44 는 그대로. 가운데(44..83)는 투명 — 그 자리에 굳힌 방 화면을 넣는다",
        "content": {"inset": B, "note": "그림이 들어가는 안쪽 = 바깥에서 44px 안(모든 변). 바깥 크기 = 그림 크기 + 88"},
        "layers": {"wood": [0, 23], "shadow": [24, 26], "paper": [27, 41], "groove": [42, 43]},
        "layersNote": "바깥에서 잰 거리(px): 낡은 나무 틀 0~23(쇠 모서리판·못은 모서리에만) · 틀 그림자 24~26 · 바랜 종이 매트 27~41 · 그림 홈 42~43",
        "palette": "lopad gray + v2 재질 WD(나무) + UI 세피아 S0~S4(종이) + 1층 램프 어두운 칸 2점(녹) — 새 색 없음, 발광 없음",
    }
    return im, meta
