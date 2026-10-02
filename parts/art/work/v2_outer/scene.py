"""960×540 목업 장면 조립 (카메라 1배 · 타일 32) — 외곽 거리 전투장.

맵 문자 지도로 타일 레이어를 깔고, 소품·큰 소품·캐릭터를 Y 정렬로 얹은 뒤 kit.light_scene 으로 어둠 + 광원 합성.
시스템의 실제 렌더 규칙은 모르므로(교차 참조 금지) 계약 §9 의 의미만으로 쌓는다:
  바닥 → 바닥 그늘(53~57) → 벽 앞면 아랫단(5·21·22) → 윗단(40~42) → 윗면(6·47·48~52) → 소품(Y 정렬, pivot = 바닥 접점).
"""
from kit import *
import tiles as TL

W, H = 960, 540
T = 32

# 열 30, 행 17 (마지막 행은 28px 만 보임)
# 기호: R 지붕(6) r 지붕 덧댐(47) E 지붕 동쪽 가장자리(48: 서쪽 경계) Wd 서쪽(49)…
MAP = [
    "RRRRRRRRRRRRRRRRRRRRRSSSSSSRRR",
    "RRPPPPPPPPPPPPPPPPPPPSSSSSSPRR",
    "REUUUUUUUUUUUUUUUUUUUQQQQQQUWR",
    "RELLLLLLLLLLLLLLLLLLLKKKKKKLWR",
    "RE............................",
    "RE..........................WR",
    "RE..........................WR",
    "RE..........................WR",
    "RE..........................WR",
    "RE..........................WR",
    "RE..........................WR",
    "RE..........................WR",
    "RE..........................WR",
    "RE..........................WR",
    "RE..........................WR",
    "RCNNNNNNNNNNNNNNNNNNNNNNNNNNDR",
    "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVV",
]


def h2(x, y, n):
    """좌표 해시 (시스템과 같은 방식은 모름 — 균등 분포용)."""
    v = (x * 73856093) ^ (y * 19349663) ^ 0x5bd1e995
    v = (v * 2654435761) & 0xFFFFFFFF
    return (v >> 13) % n


def build_tilemap(cells, floor_set=None, used=None):
    """반환 (albedo RGBA 960×540, rows, used). used = 앞면 칸 → 인덱스."""
    floor_set = floor_set or [0, 1, 2, 3]
    out = Image.new("RGBA", (W, H), NT[1])
    rows = [list(r.ljust(30, "V")) for r in MAP]
    used = used if used is not None else front_choice(rows)
    fixed = {".": None, "V": None, "R": 6, "P": 47, "S": 45, "E": 48, "W": 49, "N": 50, "C": 51, "D": 52, "Q": 44}

    def tile(idx, cx, cy):
        out.alpha_composite(cells[idx], (cx * T, cy * T))

    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ".":
                tile(floor_set[h2(x, y, len(floor_set))], x, y)
            elif ch == "V":
                tile([7, 7, 7, 58, 59][h2(x, y, 5)], x, y)
            elif ch in ("U", "L"):
                tile(used[(x, y)], x, y)
            elif ch == "K":
                tile([43, 43, 46][h2(x, y, 3)], x, y)
            elif fixed.get(ch) is not None:
                tile(fixed[ch], x, y)
    # 바닥 그늘 (벽 발치)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                continue
            n = y > 0 and rows[y - 1][x] in "LK"
            w = x > 0 and rows[y][x - 1] == "E"
            e = x < 29 and rows[y][x + 1] == "W"
            if n and w:
                tile(56, x, y)
            elif n and e:
                tile(57, x, y)
            elif n:
                tile(53, x, y)
            elif w:
                tile(54, x, y)
            elif e:
                tile(55, x, y)
    return out, rows, used


def tile_lights(rows, cells_used):
    """앞면 타일 중 창(21)·문(22)에 약한 광원."""
    lights = []
    for (x, y), idx in cells_used.items():
        if idx == 21:
            lights.append({"x": x * T + 16, "y": y * T + 26, "color": "#e2a33c", "radius": 70, "intensity": 0.55})
        elif idx == 22:
            lights.append({"x": x * T + 26, "y": y * T + 30, "color": "#dc8e23", "radius": 46, "intensity": 0.45})
    return lights


def front_choice(rows):
    """앞면 변형 선택(해시) + 몇 곳 고정 — 목업 구도용."""
    used = {}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "L":
                used[(x, y)] = [5, 21, 63, 22, 5, 5, 63, 21][h2(x, y, 8)]
            elif ch == "U":
                used[(x, y)] = [40, 41, 40, 42, 40][h2(x, y, 5)]
    return used


def paste_sprite(img, im, px, py, pivot):
    """pivot(바닥 접점)이 (px,py) 에 오도록."""
    img.alpha_composite(im, (px - pivot[0], py - pivot[1])) if px - pivot[0] >= 0 and py - pivot[1] >= 0 else \
        img.alpha_composite(im.crop((max(0, pivot[0] - px), max(0, pivot[1] - py), im.width, im.height)),
                            (max(0, px - pivot[0]), max(0, py - pivot[1])))
