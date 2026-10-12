#!/usr/bin/env python3
"""62라운드 루프 1 아트 (P0-2 · P1-17 · P1-19) — 단일 소스, 결정적. Pillow 만. Claude 직접 디자인(Gemini 402).

python3 parts/art/work/r62a/build.py [--only ritual,birth,tiles,plank,preview] [--dry]

산출:
- assets/sprites/ritual/{diary_first_page, back_canvas(+_glow), ink_brush, fate_frame}.png + .json   (P0-2 첫 생 의식 그림)
- assets/sprites/structures/v3/birth_{corpse_pile, corpse_mound, spear_thicket, banner_bloody, fallen_soldier, broken_spears}  (트림 아틀라스)
- assets/tiles/v2/stage1_waste.{png,json}   (P1-19: start 둥근 재 얼룩 · 바닥 변주 13~16 · 모래주머니 3면 · 데칼 알파 가장자리 + 4)
- assets/tiles/v2/stage1_training.{png,json} (P1-17: 밤 수련장 색)
- assets/sprites/ui/plank_label.{png,json}  (P1-17: 수련장 나무 팻말 3-slice)
- 미리보기 parts/art/work/r62a/preview_*.png
(타이틀 추가 요청 — 로고 획 순서 마스크·성문 좌표 — 는 title62/build.py 의 reveal·meta 단계)
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from common import SPR, dump, save  # noqa: E402

STEPS = ["ritual", "birth", "tiles", "plank", "preview"]


def build_plank(dry):
    import ui1x
    im = ui1x.plank_label()
    if not dry:
        save(im, os.path.join(SPR, "ui", "plank_label.png"))
        meta = {"image": "plank_label.png", "id": "plank_label", "version": "r62a", "size": {"w": im.width, "h": im.height},
                "pixelScale": 1, "palette": "v2 나무 WD · SL · PL(끈) · 무채(못) — 반투명 없음",
                "source": "parts/art/work/r62a/ui1x.py (62라운드 P1-17)"}
        meta.update(ui1x.PLANK_META)
        dump(meta, os.path.join(SPR, "ui", "plank_label.json"))
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    steps = a.only.split(",") if a.only else STEPS
    if "ritual" in steps:
        import ritual
        ritual.build()
        print("done ritual", flush=True)
    if "birth" in steps:
        import birthprops
        _, rep = birthprops.build(dry=a.dry)
        for r in rep:
            print("atlas", r)
        print("done birth", flush=True)
    if "tiles" in steps:
        import tiles62
        tiles62.build(dry=a.dry)
        print("done tiles", flush=True)
    if "plank" in steps:
        build_plank(a.dry)
        print("done plank", flush=True)
    if "preview" in steps:
        import preview
        preview.main()
        print("done preview", flush=True)


if __name__ == "__main__":
    main()
