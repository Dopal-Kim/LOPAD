#!/usr/bin/env python3
"""52라운드 개념도·캐릭터 시안 모음 미리보기 → preview_concepts_f1.png

1행: 1층 여정 순서 쿼터뷰 개념도 5장 (황무지 → 성문 → 외곽 거리(시범) → 양조 → 연회장), 채택안
2행: 각 지역 비교안(같은 지역의 다른 회차) — 없으면 빈칸
3행: 캐릭터 시안 3장 (주인공 · 1층 일반 적 · 1층 보스), 채택안
원본은 1376×768 jpg. 미리보기는 축소본이므로 세부 검수는 원본을 볼 것.
사용: python3 preview_concepts.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "preview_concepts_f1.png")

FONT = None
for f in ["/usr/share/fonts/truetype/unifont/unifont.ttf", "/usr/share/fonts/opentype/unifont/unifont.otf",
          "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"]:
    if os.path.exists(f):
        FONT = ImageFont.truetype(f, 16)
        break
if FONT is None:
    FONT = ImageFont.load_default()

BG = (18, 19, 22)

# (라벨, 채택 경로, 비교안 경로 또는 None)
REGIONS = [
    ("1 황무지 waste (채택 b)", "concept_v2_waste/raw_b.jpg", ("비교 a", "concept_v2_waste/raw_a.jpg")),
    ("2 성문 gate (채택 a)", "concept_v2_gate/raw_a.jpg", None),
    ("3 외곽 거리 outer (시범, 기존 a)", "concept_v2_outer/raw_a.jpg", None),
    ("4 양조 brewery (채택 b)", "concept_v2_brewery/raw_b.jpg", ("비교 a (수로 빛 강함)", "concept_v2_brewery/raw_a.jpg")),
    ("5 연회장 hall (채택 b)", "concept_v2_hall/raw_b.jpg", ("비교 a (지배자 작음)", "concept_v2_hall/raw_a.jpg")),
]
CHARS = [
    ("주인공 (채택 hero_b)", "concept_char/raw_hero_b.jpg"),
    ("1층 일반 적 5종 (채택 enemies_b)", "concept_char/raw_enemies_b.jpg"),
    ("1층 보스 · 취한 지배자 (보관 boss_b — 크기는 연회장 b 참고)", "concept_char/raw_boss_b.jpg"),
]

TW, TH = 480, 268          # 지역 썸네일 (원본 1376×768 의 약 0.35배)
CW, CH = 800, 446          # 캐릭터 썸네일 (약 0.58배)
PAD, LAB = 12, 22


def label(d, x, y, text):
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((x + dx, y + dy), text, font=FONT, fill=(0, 0, 0))
    d.text((x, y), text, font=FONT, fill=(235, 236, 237))


def thumb(path, w, h):
    im = Image.open(os.path.join(HERE, path)).convert("RGB")
    return im.resize((w, h), Image.LANCZOS)


def main():
    W = PAD + len(REGIONS) * (TW + PAD)
    H = (LAB + PAD) + 2 * (TH + LAB + PAD) + (CH + LAB + PAD) + PAD
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    label(d, PAD, 6, "1층 '잔' 쿼터뷰 개념도 · 캐릭터 시안 (52라운드, gemini-3.1-flash-image, 참고용 — 게임 투입본 아님)")

    y0 = LAB + PAD
    for i, (name, path, alt) in enumerate(REGIONS):
        x = PAD + i * (TW + PAD)
        label(d, x, y0, name)
        sheet.paste(thumb(path, TW, TH), (x, y0 + LAB))
        y1 = y0 + LAB + TH + PAD
        if alt:
            label(d, x, y1, alt[0])
            sheet.paste(thumb(alt[1], TW, TH), (x, y1 + LAB))
        else:
            label(d, x, y1, "(비교안 없음 — 1회 호출)" if i != 2 else "(51라운드 이전 시범, 이번 호출 아님)")

    y2 = y0 + 2 * (LAB + TH + PAD)
    cw = (W - PAD * (len(CHARS) + 1)) // len(CHARS)
    ch = int(cw * 768 / 1376)
    for i, (name, path) in enumerate(CHARS):
        x = PAD + i * (cw + PAD)
        label(d, x, y2, name)
        sheet.paste(thumb(path, cw, ch), (x, y2 + LAB))
    sheet = sheet.crop((0, 0, W, y2 + LAB + ch + PAD))
    sheet.save(OUT, optimize=True)
    print("wrote", OUT, sheet.size)


if __name__ == "__main__":
    main()
