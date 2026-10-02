#!/usr/bin/env python3
"""52라운드 Q6 주인공 조합안 hero3 미리보기 → preview_hero3.png (C 원안과 비교)

윗줄: hero3_b(채택) · hero3_a(1회차) · hero2_C(원안) 나란히 (원본 1376×768 → 축소)
오른쪽 아래: 직접 찍은 32×48 도트 초안(parts/art/work/hero3) 정면 대기 4배
아랫줄: 각 안 정면을 32×48 칸으로 줄인 판독성 시험(LANCZOS 축소 → 최근접 4배·1배).
  게임 도트가 아니다 — 실루엣·명도 덩어리가 32×48 에서 남는지 보는 용도.
사용: python3 preview_hero2.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "preview_hero3.png")
FONT = None
for f in ["/usr/share/fonts/truetype/unifont/unifont.ttf", "/usr/share/fonts/opentype/unifont/unifont.otf",
          "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"]:
    if os.path.exists(f):
        FONT = ImageFont.truetype(f, 16)
        break
FONT = FONT or ImageFont.load_default()
BG = (18, 19, 22)
OPTS = [("hero3_b 조합안 (채택 — 그림 속 영문 라벨은 생성 오류)", "concept_char/hero3_b.jpg"),
        ("hero3_a 조합안 1회차 (해골 입·측면 눈빛 → 재생성)", "concept_char/hero3_a.jpg"),
        ("hero2_C 원안 (52라운드 Q6 '유지')", "concept_char/hero2_C.jpg")]
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
    label(d, PAD, 6, "주인공 조합안 hero3 (52라운드 Q6, gemini-3.1-flash-image, 참고 이미지 없음 — 참고용) + 32×48 축소 시험 · 직접 찍은 도트 초안")
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
    # 직접 찍은 도트 초안 (hero3/build.py 결과 중 대기 정면)
    import sys
    sys.path.insert(0, os.path.join(HERE, "..", "hero3"))
    import build as hero3build
    f = hero3build.idle()[0]
    cell = Image.new("RGBA", f.size, (46, 48, 56, 255)); cell.alpha_composite(f)
    x = PAD + 1 * (TW + PAD) + 240
    yy = LAB + PAD + LAB + TH + PAD
    label(d, x, yy, "직접 찍은 도트 초안 32×48: 4배 / 1배 (hero3/build.py)")
    sheet.paste(cell.convert("RGB").resize((128, 192), Image.NEAREST), (x, yy + LAB))
    sheet.paste(cell.convert("RGB"), (x + 128 + PAD, yy + LAB + 192 - 48))
    sheet.save(OUT, optimize=True)
    print("wrote", OUT, sheet.size)


if __name__ == "__main__":
    main()
