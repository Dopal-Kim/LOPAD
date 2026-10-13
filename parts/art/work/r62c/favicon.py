"""62 루프 3 (P17 묶음 A · P2-N1) favicon — 먹 붓 망령(지도 표식 map_marker_ghost 와 같은 인물) 16·32·48 + favicon.ico.

양피지 둥근 판(UI 세피아 S5 #c6a58b, 테 S3) 위에 먹 망령(둥근 머리 + 어깨 + 갈라지는 붓 꼬리), 호박 눈 하나(A23·A25).
밝은 탭·어두운 탭 둘 다에서 보이게 판을 밝게 깔았다. 크기마다 손으로 좌표를 맞춘 도트(축소 아님).
산출: parts/art/work/favicon/favicon_{16,32,48}.png · favicon.ico(16·32·48 묶음) — 시스템이 public/ 로 옮기고 index.html 에 link.
"""
import os

from PIL import Image, ImageDraw

from c62 import AMB, GRAY, SEPIA, WORK

OUT = os.path.join(WORK, "favicon")
INK = GRAY[1]
INK2 = GRAY[3]
PARCH = SEPIA[5]
PARCH_D = SEPIA[4]
RIM = SEPIA[2]

# 크기별 도형(정수 좌표): 판 원, 머리 원, 몸 다각형, 꼬리 갈래(선), 눈, 판 그늘 호
SPEC = {
    16: dict(disc=(0, 0, 15, 15), head=(5, 1, 10, 6),
             body=[(4, 6), (11, 6), (12, 8), (11, 10), (9, 12), (8, 13), (10, 14), (7, 14), (6, 12), (4, 10), (3, 8)],
             streaks=[], eye=[(9, 3)], hl=[]),
    32: dict(disc=(0, 0, 31, 31), head=(11, 3, 21, 13),
             body=[(9, 12), (23, 12), (25, 16), (24, 20), (21, 23), (18, 25), (17, 27), (19, 29), (22, 29), (17, 30), (14, 28),
                   (13, 25), (10, 22), (7, 18), (7, 15)],
             streaks=[[(15, 20), (14, 25)], [(19, 21), (17, 25)], [(16, 27), (18, 29)]],
             eye=[(17, 7), (18, 7)], hl=[(12, 6), (12, 7), (13, 5)]),
    48: dict(disc=(0, 0, 47, 47), head=(16, 4, 32, 20),
             body=[(13, 18), (35, 18), (38, 24), (36, 30), (32, 35), (27, 38), (26, 41), (29, 44), (33, 44), (26, 46), (21, 43),
                   (19, 38), (15, 33), (10, 27), (10, 22)],
             streaks=[[(20, 28), (21, 36)], [(26, 29), (24, 36)], [(29, 30), (27, 34)], [(23, 40), (27, 44)]],
             eye=[(25, 10), (26, 10), (27, 10)], hl=[(18, 9), (18, 10), (19, 8), (20, 7), (18, 11)]),
}


def draw(n):
    s = SPEC[n]
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse(s["disc"], fill=RIM + (255,))
    x0, y0, x1, y1 = s["disc"]
    k = 1 if n <= 16 else 2
    d.ellipse((x0 + k, y0 + k, x1 - k, y1 - k), fill=PARCH + (255,))
    # 판 아래쪽 그늘(오른쪽 아래 초승달)
    # 망령
    d.ellipse(s["head"], fill=INK + (255,))
    d.polygon(s["body"], fill=INK + (255,))
    for t in s["streaks"]:
        d.line(t, fill=INK2 + (255,), width=1)                       # 붓 마른 결
    for (x, y) in s["hl"]:
        im.putpixel((x, y), INK2 + (255,))
    for i, (x, y) in enumerate(s["eye"]):
        im.putpixel((x, y), (AMB[9] if i == len(s["eye"]) // 2 else AMB[7]) + (255,))
    if n >= 32:   # 눈 빛 번짐 한 칸
        ex, ey = s["eye"][len(s["eye"]) // 2]
        im.putpixel((ex, ey + 1), AMB[4] + (255,))
    return im


def build():
    os.makedirs(OUT, exist_ok=True)
    ims = {}
    for n in (16, 32, 48):
        ims[n] = draw(n)
        ims[n].save(os.path.join(OUT, f"favicon_{n}.png"), optimize=True)
    ims[48].save(os.path.join(OUT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)],
                 append_images=[ims[16], ims[32]])
    # 미리보기: 밝은·어두운 탭 바탕 위 1배·8배
    pv = Image.new("RGBA", (16 + 32 + 48 + 40 + 48 * 8 + 10, 48 * 8 + 20), (0, 0, 0, 255))
    for row, bg in enumerate(((235, 235, 235, 255), (40, 40, 44, 255))):
        x = 10
        for n in (16, 32, 48):
            b = Image.new("RGBA", (n, n), bg)
            b.alpha_composite(ims[n])
            pv.paste(b, (x, 10 + row * 60))
            x += n + 10
    big = Image.new("RGBA", (48 * 8, 48 * 8), (40, 40, 44, 255))
    big.alpha_composite(ims[48].resize((384, 384), Image.NEAREST))
    pv.paste(big, (16 + 32 + 48 + 40, 10))
    p = os.path.join(OUT, "preview_favicon.png")
    pv.save(p)
    return [os.path.join(OUT, f) for f in ("favicon_16.png", "favicon_32.png", "favicon_48.png", "favicon.ico")]
