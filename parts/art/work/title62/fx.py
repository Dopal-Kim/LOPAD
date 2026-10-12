"""타이틀 루프 fx — 불티 입자 시트 · 가로로 이어지는 안개 띠. 도트 1칸 = 3px.

불티 시트 `title_fx_embers.png`: 칸 24×24px(논리 8×8), 열 = 깜빡임 8프레임, 행 = 종류 7
  0 호박 작은 불티 · 1 호박 중간 · 2 호박 큰 불티(꼬리) · 3 칼(서리) · 4 대검(용암) · 5 단검(독) · 6 활(비취)
  — 무기 색 행은 '원한의 목소리' 불씨: 그 무기 근처에서만 드물게 피운다.
안개 `title_fx_fog.png`: 1920×320, 가로 이음 없음(왼쪽 끝 = 오른쪽 끝), 알파 계단 5단(도트 결), 색 = 달빛 회색 G07 + 아래쪽 따뜻한 G05.
"""
import math
import random

from PIL import Image

from kit import A, G, WEAPON, Fbm, up, weapon_ramp

CELL, FR = 8, 8
ROWS = ["amber_s", "amber_m", "amber_l", "katana", "greatsword", "dagger", "bow"]


def ember_frame(kind, f):
    im = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    px = im.load()
    ph = f / FR * 2 * math.pi
    flick = 0.5 + 0.5 * math.sin(ph) * math.cos(ph * 0.5 + 1)        # 0..1
    cx, cy = 3, 4
    if kind.startswith("amber"):
        core, mid, rim, halo = A[11], A[9], A[6], A[4]
    else:
        r = weapon_ramp(kind)
        core, mid, rim, halo = r[2], r[1], r[1], r[0]
    size = {"amber_s": 0, "amber_m": 1, "amber_l": 2}.get(kind, 1)
    # 빛무리(낮은 알파)
    if size >= 1 or not kind.startswith("amber"):
        for (dx, dy) in ((-1, 0), (1, 0), (0, -1), (0, 1)) + (((-1, -1), (1, -1), (-1, 1), (1, 1)) if size == 2 else ()):
            px[cx + dx + (1 if size == 2 and dx > 0 else 0), cy + dy] = (*halo, int(70 + 60 * flick))
    if size == 0:
        px[cx, cy] = (*(core if flick > 0.45 else mid), 255)
        if flick > 0.7:
            px[cx, cy - 1] = (*rim, 150)
    elif size == 1:
        px[cx, cy] = (*core, 255)
        px[cx + 1, cy] = (*(mid if flick > 0.3 else rim), 255)
        px[cx, cy + 1] = (*rim, 255 if flick > 0.5 else 170)
        if flick > 0.6:
            px[cx + 1, cy - 1] = (*mid, 200)
    else:
        for (dx, dy, c) in ((0, 0, core), (1, 0, core), (0, 1, mid), (1, 1, mid), (0, -1, mid), (-1, 0, rim)):
            px[cx + dx, cy + dy] = (*c, 255)
        # 꼬리(아래로 — 올라가며 남기는 자국)
        for k in range(1, 3):
            px[cx + (k % 2), cy + 1 + k] = (*rim, int(200 - 70 * k * (1.2 - flick)))
        if flick > 0.55:
            px[cx + 1, cy - 2] = (*rim, 180)
    return im


def embers_sheet():
    sheet = Image.new("RGBA", (CELL * FR, CELL * len(ROWS)), (0, 0, 0, 0))
    for r, kind in enumerate(ROWS):
        for f in range(FR):
            sheet.alpha_composite(ember_frame(kind, f), (f * CELL, r * CELL))
    return up(sheet)


EMBERS_META = {
    "image": "title_fx_embers.png",
    "frameWidth": 24, "frameHeight": 24, "framesPerRow": 8, "rows": ROWS,
    "frameIndex": "row * 8 + column",
    "pivot": {"x": 10, "y": 13},
    "fps": 10, "loop": True,
    "blendMode": "ADD (빛무리 알파가 낮아 NORMAL 도 가능)",
    "emitters": [
        {"name": "mound", "rows": ["amber_s", "amber_m", "amber_l"], "weights": [5, 3, 1],
         "area": {"x": 1080, "y": 900, "w": 720, "h": 140}, "rate": "초당 6~9", "lifespanMs": [4500, 8000],
         "velocity": {"x": [8, 30], "y": [-46, -22]}, "drift": "사인 흔들림 진폭 6~14px, 주기 1.6~2.6s",
         "alpha": "0 → 1 (0.3s) → 0 (마지막 1.2s)", "scale": [1, 1], "note": "주인공 발밑 시체 더미에서 오른쪽 위로(바람 = 왼 → 오른)"},
        {"name": "back_crack", "rows": ["amber_s", "amber_m"], "weights": [3, 1],
         "area": {"x": 1440, "y": 600, "w": 60, "h": 150}, "rate": "초당 1~2", "lifespanMs": [2500, 4500],
         "velocity": {"x": [10, 26], "y": [-40, -18]}, "note": "등 상흔 균열·어깨 혼불에서 새는 불티"},
        {"name": "voices", "rows": ["katana", "greatsword", "dagger", "bow"],
         "origins": "title.json voices[].emberOrigin", "rate": "목소리가 켜진 무기에서만 초당 2~3", "lifespanMs": [1800, 3200],
         "velocity": {"x": [-6, 10], "y": [-34, -16]}, "note": "목소리(무기 빛) 펄스와 함께"},
        {"name": "city", "rows": ["amber_s"], "area": {"x": 560, "y": 520, "w": 520, "h": 120}, "rate": "초당 1", "lifespanMs": [3000, 5000],
         "velocity": {"x": [2, 8], "y": [-10, -4]}, "alpha": "최대 0.5", "depth": "far 와 mid 사이", "note": "먼 도시 굴뚝 불티(아주 작게, 느리게)"},
    ],
}


def fog_band(w=640, h=107, seed=701):
    """가로 이음 없는 안개 띠(논리) → 3배."""
    n1 = Fbm(seed, 6, 3, 4, wrap_x=True)
    n2 = Fbm(seed + 1, 16, 4, 3, wrap_x=True)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    steps = [0, 26, 48, 70, 92]
    for y in range(h):
        t = y / (h - 1)
        env = math.sin(math.pi * t) ** 1.4                         # 위·아래 끝은 0
        for x in range(w):
            u = x / w
            v = n1.at(u, t) * 0.7 + n2.at(u, t * 1.4) * 0.3
            a = (v - 0.32) * 2.2 * env
            j = (n2.at(u * 3 % 1.0, t) - 0.5) * 0.18                # 계단 경계를 붓 결로 흔듦
            lv = int(max(0, min(4, (a + j) * 4.6)))
            if lv == 0:
                continue
            c = G[7] if t < 0.55 else G[6]
            if lv >= 3 and t < 0.45:
                c = G[8]
            px[x, y] = (*c, steps[lv])
    return up(im)


FOG_META = {
    "image": "title_fx_fog.png",
    "size": [1920, 321],
    "tileX": True,
    "note": "가로 반복 이음 없음. TileSprite 로 흘린다. 색은 달빛 회색(필요하면 setTint 0xE8C890 로 도시 쪽을 데움). 알파 계단 5단(26·48·70·92/255).",
    "instances": [
        {"name": "fog_far", "depth": "far 와 mid 사이", "y": 600, "height": 240, "scaleY": 0.75, "alpha": 0.55, "speedPxPerSec": -4, "note": "지평선·성벽 발치에 깔리는 안개(왼쪽으로 아주 느리게)"},
        {"name": "fog_mid", "depth": "mid 와 near 사이", "y": 760, "height": 321, "alpha": 0.7, "speedPxPerSec": 9, "note": "들판 위를 흐르는 안개(바람 = 왼 → 오른)"},
        {"name": "fog_near", "depth": "near 위(로고·메뉴 아래)", "y": 930, "height": 200, "scaleY": 0.62, "alpha": 0.35, "speedPxPerSec": 16, "note": "발목 높이 안개 — 메뉴 글자를 가리지 않게 낮은 알파"},
    ],
}
