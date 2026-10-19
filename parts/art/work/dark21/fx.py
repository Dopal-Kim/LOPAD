"""타이틀 루프 fx (P21 다크: 불티는 검붉고 드물게, 안개는 검은 연기·젖은 재 색, 새 층 비·까마귀·재 낙하)

원본 설명: 타이틀 루프 fx — 불티 입자 시트 · 가로로 이어지는 안개 띠. 도트 1칸 = 3px.

불티 시트 `title_fx_embers.png`: 칸 24×24px(논리 8×8), 열 = 깜빡임 8프레임, 행 = 종류 7
  0 호박 작은 불티 · 1 호박 중간 · 2 호박 큰 불티(꼬리) · 3 칼(서리) · 4 대검(용암) · 5 단검(독) · 6 활(비취)
  — 무기 색 행은 '원한의 목소리' 불씨: 그 무기 근처에서만 드물게 피운다.
안개 `title_fx_fog.png`: 1920×320, 가로 이음 없음(왼쪽 끝 = 오른쪽 끝), 알파 계단 5단(도트 결), 색 = 달빛 회색 G07 + 아래쪽 따뜻한 G05.
"""
import math
import random

from PIL import Image

from kit import A, B, G, WEAPON, Fbm, up, weapon_ramp

CELL, FR = 8, 8
ROWS = ["amber_s", "amber_m", "amber_l", "katana", "greatsword", "dagger", "bow"]


def ember_frame(kind, f):
    im = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    px = im.load()
    ph = f / FR * 2 * math.pi
    flick = 0.5 + 0.5 * math.sin(ph) * math.cos(ph * 0.5 + 1)        # 0..1
    cx, cy = 3, 4
    if kind.startswith("amber"):
        core, mid, rim, halo = A[6], B[5], B[4], B[2]          # P21: 검붉은 불씨(심만 한 점 호박)
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
         "area": {"x": 1080, "y": 900, "w": 720, "h": 140}, "rate": "초당 1.5~2.5 (P21: 62 의 1/3)", "lifespanMs": [4500, 8000],
         "velocity": {"x": [8, 30], "y": [-46, -22]}, "drift": "사인 흔들림 진폭 6~14px, 주기 1.6~2.6s",
         "alpha": "0 → 1 (0.3s) → 0 (마지막 1.2s)", "scale": [1, 1], "note": "주인공 발밑 시체 더미에서 오른쪽 위로(바람 = 왼 → 오른)"},
        {"name": "back_crack", "rows": ["amber_s", "amber_m"], "weights": [3, 1],
         "area": {"x": 1440, "y": 600, "w": 60, "h": 150}, "rate": "초당 0.5~1", "lifespanMs": [2500, 4500],
         "velocity": {"x": [10, 26], "y": [-40, -18]}, "note": "등 상흔 균열에서 새는 불티(P21: 어깨 혼불은 꺼짐)"},
        {"name": "voices", "rows": ["katana", "greatsword", "dagger", "bow"],
         "origins": "title.json voices[].emberOrigin", "rate": "목소리가 켜진 무기에서만 초당 2~3", "lifespanMs": [1800, 3200],
         "velocity": {"x": [-6, 10], "y": [-34, -16]}, "note": "목소리(무기 빛) 펄스와 함께"},
        {"name": "city", "rows": ["amber_s"], "area": {"x": 640, "y": 560, "w": 300, "h": 80}, "rate": "초당 0.5 (P21: 먼 불길 세 곳 위만)", "lifespanMs": [3000, 5000],
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
            c = G[3] if t < 0.55 else G[2]                         # P21: 달빛 안개 → 검은 연기·젖은 재
            if lv >= 3 and t < 0.45:
                c = G[4]
            px[x, y] = (*c, steps[lv])
    return up(im)


FOG_META = {
    "image": "title_fx_fog.png",
    "size": [1920, 321],
    "tileX": True,
    "note": "가로 반복 이음 없음. TileSprite 로 흘린다. P21: 색 = 검은 연기·젖은 재(G02~G04) — 데우는 틴트 쓰지 말 것. 알파 계단 5단(26·48·70·92/255).",
    "instances": [
        {"name": "fog_far", "depth": "far 와 mid 사이", "y": 600, "height": 240, "scaleY": 0.75, "alpha": 0.55, "speedPxPerSec": -4, "note": "지평선·성벽 발치에 깔리는 안개(왼쪽으로 아주 느리게)"},
        {"name": "fog_mid", "depth": "mid 와 near 사이", "y": 760, "height": 321, "alpha": 0.7, "speedPxPerSec": 9, "note": "들판 위를 흐르는 안개(바람 = 왼 → 오른)"},
        {"name": "fog_near", "depth": "near 위(로고·메뉴 아래)", "y": 930, "height": 200, "scaleY": 0.62, "alpha": 0.35, "speedPxPerSec": 16, "note": "발목 높이 안개 — 메뉴 글자를 가리지 않게 낮은 알파"},
    ],
}


# ------------------------------------------------------------------ P21 새 층: 비 · 까마귀 · 재 낙하
def rain_tile(w=160, h=180, seed=811):
    """이음 없는 비 타일(논리 160×180 → 480×540). 바람 왼→오른: 줄기가 아래로 갈수록 오른쪽(기울기 0.25)."""
    r = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for _ in range(70):
        x0, y0 = r.randrange(w), r.randrange(h)
        ln = r.randint(4, 9)
        a = r.choice([46, 62, 80])
        for i in range(ln):
            x, y = int(x0 + i * 0.25) % w, (y0 + i) % h
            c = G[7] if i == ln - 1 else G[6]
            px[x, y] = (*c, a if i < ln - 1 else a + 20)
    return up(im)


RAIN_META = {
    "image": "title_fx_rain.png", "size": [480, 540], "tile": True,
    "instances": [
        {"name": "rain_far", "depth": "far 와 mid 사이(fog_far 위)", "scale": 0.67, "alpha": 0.35, "speedPxPerSec": {"x": 40, "y": 520},
         "note": "먼 비 — 작게·흐리게"},
        {"name": "rain_near", "depth": "near 위(fog_near 아래)", "scale": 1.0, "alpha": 0.55, "speedPxPerSec": {"x": 90, "y": 980},
         "note": "가까운 비 — 메뉴 틀 영역은 알파 0.3 으로 낮추면 글자가 덜 흔들린다(선택)"},
    ],
    "reducedMotion": "모션 줄이기면 rain_far 만 정지 상태로 알파 0.25 (또는 끔)",
}


def crow_frame(f):
    """나는 까마귀(옆모습, 오른쪽을 봄) 논리 24×16. 날갯짓 6프레임: 위 · 반위 · 수평 · 아래 · 반아래 · 수평(올림)."""
    from PIL import ImageDraw
    im = Image.new("RGBA", (24, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k, sh = (*G[0], 255), (*G[3], 255)
    d.ellipse([7, 6, 17, 10], fill=k)                               # 몸
    d.ellipse([15, 5, 19, 9], fill=k)                               # 머리
    d.polygon([(19, 7), (22, 8), (19, 9)], fill=k)                   # 부리
    d.polygon([(9, 8), (3, 7), (3, 11), (9, 10)], fill=k)            # 쐐기 꼬리
    wings = [[(15, 8), (14, 3), (11, 0), (8, 0), (6, 2), (7, 5), (9, 8)],
             [(15, 8), (13, 4), (9, 2), (5, 3), (5, 5), (8, 7), (10, 9)],
             [(15, 8), (10, 6), (3, 6), (1, 8), (4, 9), (10, 10)],
             [(15, 9), (13, 12), (10, 15), (7, 15), (7, 12), (9, 9)],
             [(15, 9), (12, 11), (7, 13), (4, 13), (5, 11), (9, 9)],
             [(15, 8), (11, 5), (5, 4), (2, 5), (5, 8), (10, 9)]]
    w = wings[f]
    d.polygon(w, fill=k)
    d.line(w[:3], fill=sh)                                           # 날개 앞전 달빛
    d.point((17, 7), fill=(*G[4], 255))                             # 눈
    return im


def crow_sheet():
    sheet = Image.new("RGBA", (24 * 6, 16), (0, 0, 0, 0))
    for f in range(6):
        sheet.alpha_composite(crow_frame(f), (f * 24, 0))
    return up(sheet)


CROW_META = {
    "image": "title_fx_crow.png", "frameWidth": 72, "frameHeight": 48, "frames": 6, "fps": 11, "loop": True,
    "facing": "right (왼쪽으로 날면 flipX)", "pivot": {"x": 36, "y": 25},
    "flights": {
        "intervalMs": [7000, 15000], "count": [1, 3], "spreadPx": [40, 120],
        "path": "화면 밖 한쪽 → 반대쪽, y 160~520 사이에서 시작, 진행하며 ±30px 사인 출렁임(주기 1.4s)",
        "speedPxPerSec": [150, 230], "scale": [0.5, 1.0], "alpha": 1.0,
        "depth": "scale < 0.75 = far 와 mid 사이 / 그 밖 = near 와 fog_near 사이",
        "avoid": "로고 글자 상자(title.json logo.lettersBox) 안을 지나지 않게 y 를 고른다",
        "note": "첫 3초(로고 등장) 동안은 띄우지 않는다. 음향 '까마귀'(sound P21 타이틀 곡 층)와 맞추면 좋다(선택)",
    },
    "reducedMotion": "모션 줄이기면 끔",
}


def ash_frame(kind, f):
    """젖은 재 조각(논리 6×6). kind 0 = 작은 재, 1 = 큰 재(뒤집히며 떨어짐)."""
    im = Image.new("RGBA", (6, 6), (0, 0, 0, 0))
    px = im.load()
    ph = f / 8 * 2 * math.pi
    if kind == 0:
        px[2, 2] = (*G[5], 220)
        if math.sin(ph) > 0:
            px[3, 2] = (*G[4], 200)
        else:
            px[2, 3] = (*G[4], 200)
    else:
        wdt = abs(math.cos(ph)) * 2 + 0.5                            # 뒤집힘 = 폭 변화
        for x in range(6):
            if abs(x - 2.5) <= wdt:
                px[x, 2] = (*(G[6] if x < 3 else G[4]), 230)
        px[2, 3] = (*G[3], 200)
    return im


def ash_sheet():
    sheet = Image.new("RGBA", (6 * 8, 6 * 2), (0, 0, 0, 0))
    for k in range(2):
        for f in range(8):
            sheet.alpha_composite(ash_frame(k, f), (f * 6, k * 6))
    return up(sheet)


ASH_META = {
    "image": "title_fx_ash.png", "frameWidth": 18, "frameHeight": 18, "framesPerRow": 8, "rows": ["ash_s", "ash_l"],
    "frameIndex": "row * 8 + column", "fps": 8, "loop": True, "blendMode": "NORMAL",
    "emitters": [
        {"name": "ash_fall", "rows": ["ash_s", "ash_l"], "weights": [3, 1], "area": {"x": -100, "y": -40, "w": 2120, "h": 20},
         "rate": "초당 4~6", "lifespanMs": [9000, 14000], "velocity": {"x": [14, 36], "y": [38, 70]},
         "drift": "사인 흔들림 진폭 8~18px, 주기 2~3.4s", "alpha": "0 → 0.8 (0.6s) → 0 (마지막 1.5s)", "scale": [0.67, 1],
         "depth": "near 와 fog_near 사이", "note": "비에 섞여 내리는 젖은 재(바람 왼→오른)"},
    ],
    "reducedMotion": "모션 줄이기면 초당 1 로",
}
