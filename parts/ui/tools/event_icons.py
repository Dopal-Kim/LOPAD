"""62 루프 2 UI F — 사연·장터 아이콘 시트 (assets/ui/kit/event_icons.png + .json).

계약 D `UiEventIconKind` 중 키트 icons.png 에 없는 8종을 같은 결(16×16 칸, 1px 검은 외곽, 무채색 몸 + 1층 호박 한 점)로 손도트.
gold·potion·hp 는 키트 icons.png 그대로 쓴다 (sense 는 1층 화면에 없음 — 금지어).
팔레트: parts/art/palette/lopad.json 무채색 G00~G15 + 1층 강조 램프(호박) + UI 세피아 S0~S5 만.

실행: python3 parts/ui/tools/event_icons.py  (PIL 필요)
"""

import json
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT_PNG = os.path.join(ROOT, "assets", "ui", "kit", "event_icons.png")
OUT_JSON = os.path.join(ROOT, "assets", "ui", "kit", "event_icons.json")

COLORS = {
    ".": None,
    "k": "#000000",  # G00 외곽
    "d": "#2f3033",  # G03
    "e": "#3e3f42",  # G04
    "m": "#5c5e62",  # G06
    "g": "#7d8084",  # G08
    "l": "#a0a2a6",  # G10
    "w": "#c5c6c9",  # G12
    "W": "#ebeced",  # G14
    "r": "#3f271d",  # 1층 17 deep
    "a": "#8b4d22",  # 1층 19
    "A": "#d67a11",  # 1층 21 base
    "y": "#e2a33c",  # 1층 23
    "Y": "#eecc78",  # 1층 25 glow
    "s": "#403227",  # S2
    "q": "#503f32",  # S3
    "p": "#6a5645",  # S4
    "P": "#c6a58b",  # S5
}

# 16×16 칸 하나씩 (행 16자 × 16줄)
ICONS = {
    # 최대 체력: 심장 (회색 몸 + 호박 심지) — 체력(붕대 십자)과 다른 모양
    "maxHp": [
        "................",
        "................",
        "...kkk....kkk...",
        "..kwWwk..kwwgk..",
        ".kwWWwwkkwwwggk.",
        ".kwWwwwggwwwggk.",
        ".kwwwwAyAwwgggk.",
        ".kgwwwAYAwggggk.",
        "..kgwwwAwgggmk..",
        "...kgwwwwggmk...",
        "....kgwwggmk....",
        ".....kgggmk.....",
        "......kgmk......",
        ".......kk.......",
        "................",
        "................",
    ],
    # 각성 게이지: 불꽃 (호박)
    "growth": [
        "................",
        ".......k........",
        "......kAk.......",
        "......kAyk......",
        ".....kAyAk......",
        "....kAAyYAk.....",
        "....kAyYYyAk....",
        "...kaAyYWYyAk...",
        "...kaAYWWWYAk...",
        "...kaAyYWYyAk...",
        "...kaaAyYyAak...",
        "....kaaAAAak....",
        ".....kkaaakk....",
        ".......kkk......",
        "................",
        "................",
    ],
    # 유품: 끈 달린 둥근 패 (회색 테 + 호박 알)
    "passive": [
        "................",
        "..kk........kk..",
        "..kmk......kmk..",
        "...kmk....kmk...",
        "....kmk..kmk....",
        ".....kmkkmk.....",
        "......kwwk......",
        ".....kwWwgk.....",
        "....kwWAAggk....",
        "...kwWAYyAggk...",
        "...kwAYYyAagk...",
        "...kgwAyAagmk...",
        "....kgwaagmk....",
        ".....kggmmk.....",
        "......kkkk......",
        "................",
    ],
    # 저주: 들쭉날쭉한 먹 봉인 + 호박 금 (X)
    "curse": [
        "................",
        "......k..k......",
        "...k.kdkkdk.k...",
        "..kdkdddddddkdk.",
        "..kdddedddeddk..",
        ".kddAdddddddAdk.",
        "..kdeAddddeAddk.",
        ".kdddeAdddAeddk.",
        "..kddddAyAdddk..",
        ".kddddeAyAeddk..",
        "..kdddAdddAdddk.",
        ".kddeAdddddAedk.",
        "..kdAdddedddAk..",
        "...kdkdddddkdk..",
        "....k.kkdkk.k...",
        "................",
    ],
    # 값 깎기: 꼬리표 (세피아 종이 + 호박 구멍 + 사선)
    "discount": [
        "................",
        "........kkkkkk..",
        ".......kPPPPPPk.",
        "......kPPPPPPPk.",
        ".....kPPPPkkPPk.",
        "....kPPPPkYAkPk.",
        "...kPPPPPPkkPPk.",
        "..kPPkPPPPPPPpk.",
        ".kPPPPkPPPPPPpk.",
        ".kpPPPPkPPPPpk..",
        "..kpPPPPkPPpk...",
        "...kpPPPPkpk....",
        "....kpPPPpk.....",
        ".....kpppk......",
        "......kkk.......",
        "................",
    ],
    # 무리: 창날 둘 (회색) + 호박 술
    "enemies": [
        "................",
        "...k.......k....",
        "..kWk.....kWk...",
        "..kwk.....kwk...",
        ".kwWgk...kwWgk..",
        ".kwwgk...kwwgk..",
        ".kwwgk...kwwgk..",
        "..kgk.....kgk...",
        "..kAk.....kAk...",
        ".kAyAk...kAyAk..",
        "..kmk.....kmk...",
        "..kmk.....kmk...",
        "..kmk.....kmk...",
        "..kmk.....kmk...",
        "..kkk.....kkk...",
        "................",
    ],
    # 일기장: 펼친 책 (세피아 쪽 + 가죽 표지 + 호박 책갈피)
    "diary": [
        "................",
        "................",
        "..kkkk...kkkk...",
        ".kPPPPkkkPPPPk..",
        ".kPppPPkPPppPk..",
        ".kPPPPPkPPPPPk..",
        ".kPppPPkPPppPk..",
        ".kPPPPPkPPPPPk..",
        ".kPppPPkPPpAPk..",
        ".kPPPPPkPPPAPk..",
        ".kPPPPPkPPPAPk..",
        ".kkkkkksskkkkk..",
        ".ksssssskssssk..",
        "..kkkkkkkkkkk...",
        "................",
        "................",
    ],
    # 알 수 없음: 먹 쪽지 위 호박 '?'
    "unknown": [
        "................",
        "..kkkkkkkkkkk...",
        "..ksssssssssk...",
        "..ksssyYYyssk...",
        "..kssyAssAysk...",
        "..kssssssAysk...",
        "..ksssssyAssk...",
        "..kssssyAsssk...",
        "..kssssAssssk...",
        "..ksssssssssk...",
        "..kssssyAsssk...",
        "..kssssaasssk...",
        "..ksssssssssk...",
        "..kqqqqqqqqqk...",
        "..kkkkkkkkkkk...",
        "................",
    ],
}

ORDER = ["maxHp", "growth", "passive", "curse", "discount", "enemies", "diary", "unknown"]


def hex_rgba(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def main():
    cell = 16
    im = Image.new("RGBA", (cell * len(ORDER), cell), (0, 0, 0, 0))
    frames = {}
    for i, name in enumerate(ORDER):
        rows = ICONS[name]
        assert len(rows) == cell, (name, len(rows))
        for y, row in enumerate(rows):
            assert len(row) == cell, (name, y, len(row), row)
            for x, ch in enumerate(row):
                c = COLORS[ch]
                if c:
                    im.putpixel((i * cell + x, y), hex_rgba(c))
        frames[name] = {"index": i, "x": i * cell, "y": 0, "w": cell, "h": cell}
    im.save(OUT_PNG)
    meta = {
        "image": "event_icons.png",
        "cellWidth": cell,
        "cellHeight": cell,
        "columns": len(ORDER),
        "rows": 1,
        "frames": frames,
        "anchor": "ui",
        "source": "parts/ui/tools/event_icons.py (62 루프 2 UI F — UI 손도트, 키트 icons.png 결)",
        "notes": {
            "maxHp": "최대 체력 — 심장",
            "growth": "각성 게이지 — 불꽃",
            "passive": "유품 — 끈 달린 패",
            "curse": "저주 — 먹 봉인",
            "discount": "다음 장터 값 깎기 — 꼬리표",
            "enemies": "다음 싸움 무리 — 창날 둘",
            "diary": "일기장",
            "unknown": "숨은 보상 '?'",
        },
        "palette": "parts/art/palette/lopad.json (G00~G15 + 1층 강조 램프 + UI 세피아)",
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
