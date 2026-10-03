#!/usr/bin/env python3
# [53라운드 보관] 이 스크립트가 미리보기·목업·마스크 입력으로 읽던 구 시트(assets/sprites/player/player_*, player/v2/*, enemies/{dummy,archer,charger}_*, enemies/v2/*, weapons/katana_* 중 아이콘 외, weapons/v2/*)는 삭제됨 — 해당 단계는 재실행 시 FileNotFoundError.
"""림라이트 전/후 비교 미리보기 (40라운드 Q1).

실행: python3 parts/art/work/player/preview_rimlight.py
  before = git HEAD 의 assets/sprites/**  (림라이트 이전 시트)
  after  = 작업 트리의 assets/sprites/**  (빌드 결과)
  바닥   = assets/tiles/stage1.png 공통 바닥 4변형(인덱스 0~3)을 깔고 그 위에 얹는다.
산출: parts/art/work/player/preview_rimlight.png  (위 1배, 아래 4배. 각 배율에서 윗줄 before / 아랫줄 after)
"""
import io
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)

TILES = Image.open(os.path.join(ROOT, "assets", "tiles", "stage1.png")).convert("RGBA")
FLOOR = [TILES.crop((i * 16, 0, i * 16 + 16, 16)) for i in range(4)]   # 공통 바닥 4변형

# (시트 경로, 프레임 폭, 프레임 높이, 행(방향), 열 목록)
ITEMS = [
    ("player/player_idle.png", 16, 24, 0, [0]),
    ("player/player_walk.png", 16, 24, 0, [0, 1, 2, 3, 4, 5, 6, 7]),
    ("player/player_walk.png", 16, 24, 3, [0, 2, 4, 6]),
    ("player/player_walk.png", 16, 24, 2, [0, 2]),
    ("player/player_hurt.png", 16, 24, 0, [0, 1]),
    ("enemies/dummy_idle.png", 16, 24, 0, [0]),
    ("enemies/dummy_walk.png", 16, 24, 3, [0, 2, 4, 6]),
    ("enemies/archer_idle.png", 16, 24, 0, [0]),
    ("enemies/archer_walk.png", 16, 24, 3, [0, 2, 4, 6]),
    ("enemies/charger_idle.png", 24, 24, 0, [0]),
    ("enemies/charger_walk.png", 24, 24, 3, [0, 2, 4, 6]),
    ("bosses/stage1_idle.png", 32, 48, 0, [0]),
    ("bosses/stage1_walk.png", 32, 48, 3, [0, 4]),
    ("bosses/emperor_idle.png", 48, 64, 0, [0]),
    ("bosses/emperor_walk.png", 48, 64, 3, [0, 4]),
]


def load(rel, before):
    path = os.path.join("assets", "sprites", rel)
    if before:
        data = subprocess.check_output(["git", "-C", ROOT, "show", "HEAD:" + path])
        return Image.open(io.BytesIO(data)).convert("RGBA")
    return Image.open(os.path.join(ROOT, path)).convert("RGBA")


def floor_bg(w, h, seed=0):
    bg = Image.new("RGBA", (w, h))
    k = seed
    for y in range(0, h, 16):
        for x in range(0, w, 16):
            bg.alpha_composite(FLOOR[(k * 7 + 3) % 4], (x, y)); k += 1
    return bg


def row(before, pad=4):
    """바닥 위에 프레임을 한 줄로. 발바닥 정렬(각 셀 하단 = 바닥 기준선). 1배 RGBA 반환."""
    cells = []
    for rel, fw, fh, r, cols in ITEMS:
        sheet = load(rel, before)
        for c in cols:
            cells.append(sheet.crop((c * fw, r * fh, c * fw + fw, r * fh + fh)))
    H = 64 + 16
    W = sum(im.width for im in cells) + pad * (len(cells) + 1)
    out = floor_bg(W + 16, H)
    x = pad
    for im in cells:
        out.alpha_composite(im, (x, H - 8 - im.height))
        x += im.width + pad
    return out.crop((0, 0, W, H))


def main():
    b = row(True)
    a = row(False)
    label_h = 14
    blocks = []
    for scale in (1, 4):
        bw, bh = b.width * scale, b.height * scale
        blk = Image.new("RGB", (bw, (bh + label_h) * 2), (24, 24, 26))
        d = ImageDraw.Draw(blk)
        for i, (im, name) in enumerate(((b, "before (HEAD)"), (a, "after: rim G04 right+bottom"))):
            oy = i * (bh + label_h)
            d.text((4, oy + 1), "x%d  %s" % (scale, name), fill=(220, 220, 220), font=FONT)
            blk.paste(im.resize((bw, bh), Image.NEAREST).convert("RGB"), (0, oy + label_h))
        blocks.append(blk)
    W = max(bk.width for bk in blocks)
    H = sum(bk.height for bk in blocks) + 8 * (len(blocks) + 1)
    img = Image.new("RGB", (W + 16, H), (24, 24, 26))
    y = 8
    for bk in blocks:
        img.paste(bk, (8, y)); y += bk.height + 8
    img.save(os.path.join(HERE, "preview_rimlight.png"))
    print("saved", os.path.join(HERE, "preview_rimlight.png"), img.size)


if __name__ == "__main__":
    main()
