#!/usr/bin/env python3
"""52라운드 Q4 주인공 재시안 3안 미리보기 → preview_hero2.png

윗줄: 시트 A/B/C 나란히 (원본 1376×768 → 축소)
아랫줄: 각 안 정면을 32×48 칸으로 줄인 판독성 시험(LANCZOS 축소 → 최근접 4배·1배).
  게임 도트가 아니다 — 실루엣·명도 덩어리가 32×48 에서 남는지 보는 용도.
사용: python3 preview_hero2.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "preview_hero2.png")
FONT = None
for f in ["/usr/share/fonts/truetype/unifont/unifont.ttf", "/usr/share/fonts/opentype/unifont/unifont.otf",
          "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"]:
    if os.path.exists(f):
        FONT = ImageFont.truetype(f, 16)
        break
FONT = FONT or ImageFont.load_default()
BG = (18, 19, 22)
OPTS = [("A  흙 덩이 몸 + 갑옷 파편", "concept_char/hero2_A.jpg"),
        ("B  재 덮인 해골 같은 몸 + 붕대·사슬", "concept_char/hero2_B.jpg"),
        ("C  혼불이 새는 반쯤 무너진 형체 (추천)", "concept_char/hero2_C.jpg")]
FRONT = (40, 80, 340, 720)   # 세 시트 모두 정면 그림이 이 상자 안 (원본 좌표)
TW, TH, PAD, LAB = 800, 446, 14, 24


def label(d, x, y, t):
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((x + dx, y + dy), t, font=FONT, fill=(0, 0, 0))
    d.text((x, y), t, font=FONT, fill=(235, 236, 237))


def sprite_test(im):
    fr = im.crop(FRONT)
    s = 48 / fr.height
    w = max(1, round(fr.width * s))
    small = fr.resize((w, 48), Image.LANCZOS)
    cell = Image.new("RGB", (32, 48), im.getpixel((8, 8)))
    cell.paste(small.crop(((w - 32) // 2, 0, (w - 32) // 2 + 32, 48)) if w > 32 else small, (max(0, (32 - w) // 2), 0))
    return cell


def main():
    W = PAD + 3 * (TW + PAD)
    H = LAB + PAD + LAB + TH + PAD + LAB + 48 * 4 + PAD
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    label(d, PAD, 6, "주인공 재시안 3안 (52라운드 Q4, gemini-3.1-flash-image, 참고 이미지 없음 — 참고용, 게임 투입본 아님)")
    y = LAB + PAD
    for i, (name, p) in enumerate(OPTS):
        x = PAD + i * (TW + PAD)
        im = Image.open(os.path.join(HERE, p)).convert("RGB")
        label(d, x, y, name)
        sheet.paste(im.resize((TW, TH), Image.LANCZOS), (x, y + LAB))
        yy = y + LAB + TH + PAD
        label(d, x, yy, "32×48 축소 시험: 4배 / 1배")
        cell = sprite_test(im)
        sheet.paste(cell.resize((128, 192), Image.NEAREST), (x, yy + LAB))
        sheet.paste(cell, (x + 128 + PAD, yy + LAB + 192 - 48))
    sheet.save(OUT, optimize=True)
    print("wrote", OUT, sheet.size)


if __name__ == "__main__":
    main()
