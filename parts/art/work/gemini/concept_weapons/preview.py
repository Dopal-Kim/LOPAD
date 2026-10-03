#!/usr/bin/env python3
"""53라운드 Q18 무기 개념 시안 미리보기.

preview_weapons_concepts.png     무기별 A/B 대표안 나란히(1/2 축소) + 같은 방향의 다른 시도(1/4 축소)
preview_weapons_readability.png  각 대표안의 '쥔 모습'을 몸 키 144 px(= v3 도트 96×144 의 몸 높이)로 줄인 시험
                                 1배·2배 — 실제 도트는 직접 그리므로 '덩어리·명암이 읽히는가' 만 보는 용도
실행: python3 preview.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = FONT_S = ImageFont.load_default()
for f in ["/usr/share/fonts/truetype/unifont/unifont.ttf", "/usr/share/fonts/opentype/unifont/unifont.otf",
          "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"]:
    if os.path.exists(f):
        FONT = ImageFont.truetype(f, 16)
        FONT_S = ImageFont.truetype(f, 16)
        break

BG = (24, 24, 28)
FG = (232, 226, 210)
AMBER = (232, 184, 88)
DIM = (150, 146, 140)

NAMES = {"katana": "칼", "greatsword": "대검", "dagger": "단검", "bow": "활"}
WAY = {"A": "A 주운 녹슨 실전 무기 + 스민 혼불", "B": "B 재·흙이 굳어 혼불로 벼린 무기"}

# 대표안(main)과 다른 시도(alts). 꼬리표 = 파일 raw_<weapon>_<tag>.jpg
ROWS = [
    ("katana", {"A": ("A", "녹슨 칼날 등줄기 균열 혼불·붕대 손잡이·금 간 칠 칼집"),
                "B": ("B2", "검은 재 칼날, 날 전체가 호박 균열 한 줄·흉갑 조각 코등이")},
     [("B", "B 1회차 — 라벨 글자·곧은 날(반려)")]),
    ("greatsword", {"A": ("A2", "츠바이헨더(갈고리·리카소)·화살촉 박힘·이 빠진 홈 혼불"),
                    "B": ("B", "잔해(창날·흉갑·화살·못)가 재·흙으로 굳은 판, 혼불 실로 등에 붙음")},
     [("A", "A 1회차 — 라벨 글자(반려)")]),
    ("dagger", {"A": ("A2", "론델 단검(원반 코등이·폼멜)·혼불이 녹아 떨어짐·역수"),
                "B": ("B", "자기 재 껍데기에서 부러낸 송곳니 조각, 균열 혼불·백열 끝")},
     [("A", "A 1회차 — 정수(역수 아님)·찌르기 불꽃 좋음")]),
    ("bow", {"A": ("A2", "주운 장궁(붕대·못 부목)·몸에 꽂힌 화살을 뽑아 씀"),
             "B": ("B", "재·흙 활대 + 혼불 시위(유일한 빛나는 선)·재 화살")},
     [("A", "A 1회차 — 'SAMPLE' 글자(반려)")]),
]

# '쥔 모습' 잘라내기 상자(원본 1376×768 좌표)와 그 안의 몸 키(머리 꼭대기 ~ 발바닥, 원본 px)
HOLD = {
    "katana_A": ((50, 310, 700, 705), 380),
    "katana_B2": ((235, 140, 565, 655), 505),
    "greatsword_A2": ((290, 35, 705, 695), 540),
    "greatsword_B": ((310, 55, 700, 685), 475),
    "dagger_A2": ((480, 250, 815, 685), 413),
    "dagger_B": ((315, 170, 685, 685), 495),
    "bow_A2": ((395, 20, 845, 695), 540),
    "bow_B": ((340, 25, 775, 705), 510),
}


def load(weapon, tag):
    return Image.open(os.path.join(HERE, "raw_%s_%s.jpg" % (weapon, tag))).convert("RGB")


def concepts():
    MW, MH = 688, 384
    TW, TH = 344, 192
    LW = 120
    head = 44
    rowh = head + MH + 14
    W = LW + 2 * (MW + 12) + TW + 12
    H = 48 + len(ROWS) * rowh
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((12, 14), "53라운드 Q18 무기 개념 시안 (Gemini 참고용, 12회) — 왼쪽 A: 주운 녹슨 실전 무기 + 혼불 / 가운데 B: 재·흙이 굳어 혼불로 벼린 무기 / 오른쪽: 같은 무기의 다른 시도",
           fill=FG, font=FONT)
    for r, (weapon, main, alts) in enumerate(ROWS):
        y = 48 + r * rowh
        d.text((14, y + head + MH // 2 - 10), NAMES[weapon], fill=AMBER, font=FONT)
        for c, way in enumerate("AB"):
            tag, desc = main[way]
            x = LW + c * (MW + 12)
            im.paste(load(weapon, tag).resize((MW, MH), Image.LANCZOS), (x, y + head))
            d.text((x, y + 2), "%s %s  [raw_%s_%s]" % (NAMES[weapon], WAY[way], weapon, tag), fill=FG, font=FONT)
            d.text((x, y + 21), desc, fill=DIM, font=FONT_S)
        x = LW + 2 * (MW + 12)
        for k, (tag, desc) in enumerate(alts):
            yy = y + head + k * (TH + 22)
            im.paste(load(weapon, tag).resize((TW, TH), Image.LANCZOS), (x, yy))
            d.text((x, yy + TH + 2), desc, fill=DIM, font=FONT_S)
    out = os.path.join(HERE, "preview_weapons_concepts.png")
    im.save(out)
    print(out, im.size)


FLOOR = (34, 33, 36)       # 어두운 게임 바닥 근사(숯빛 주변광 0.34 아래의 바닥 명도)


def on_dark_floor(im, bg):
    """시안 배경(평평한 청회 슬레이트)을 어두운 바닥색으로 바꾼다 — 실제 게임 대비로 시험하기 위해.
    배경과 색 거리가 가까운 픽셀만 바꾸고(가장자리는 섞음), 그림자·인물은 그대로 둔다."""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            c = px[x, y]
            dist = sum(abs(c[i] - bg[i]) for i in range(3))
            if dist < 18:
                t = 1.0
            elif dist < 36:
                t = (36 - dist) / 18.0
            else:
                continue
            px[x, y] = tuple(round(c[i] * (1 - t) + FLOOR[i] * t) for i in range(3))
    return im


def readability():
    """쥔 모습의 몸 키를 144 px 로 줄여 어두운 바닥 위에 1배·2배."""
    rows = []
    for weapon, main, _ in ROWS:
        cells = []
        for way in "AB":
            tag = main[way][0]
            box, body_h = HOLD["%s_%s" % (weapon, tag)]
            full = load(weapon, tag)
            bg = full.getpixel((6, 6))          # 원본 모서리 = 시안 배경색
            src = full.crop(box)
            sc = 144.0 / body_h
            small = src.resize((max(1, round(src.width * sc)), max(1, round(src.height * sc))), Image.LANCZOS)
            cells.append(("%s %s" % (NAMES[weapon], tag), on_dark_floor(small, bg)))
        rows.append(cells)
    pad = 16
    W = max(sum(c.width * 3 + pad * 2 for _, c in cells) + pad for cells in rows) + pad
    H = 44 + sum(max(c.height for _, c in cells) * 2 + 34 for cells in rows)
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((12, 12), "게임 크기 시험: 몸 키 144 px(v3 96×144)·어두운 바닥. 왼쪽 1배(1080p 실제)·오른쪽 2배",
           fill=FG, font=FONT)
    y = 44
    for cells in rows:
        x = pad
        for label, small in cells:
            d.text((x, y), label, fill=AMBER, font=FONT)
            im.paste(small, (x, y + 22))
            big = small.resize((small.width * 2, small.height * 2), Image.NEAREST)
            im.paste(big, (x + small.width + pad // 2, y + 22))
            x += small.width * 3 + pad * 2 + pad
        y += max(c.height for _, c in cells) * 2 + 34
    out = os.path.join(HERE, "preview_weapons_readability.png")
    im.save(out)
    print(out, im.size)


if __name__ == "__main__":
    concepts()
    readability()
