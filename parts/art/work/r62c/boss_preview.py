"""보스 재도트 전후 미리보기 → preview_boss.png (위 = git BASE_REV, 아래 = 지금, 1920 렌더 1:1 = 도트 1:1, 연회장 돌바닥 위)."""
import os
import sys

from PIL import Image

import boss
from c62 import HERE, ROOT, WORK

sys.path.insert(0, os.path.join(WORK, "atlas57"))
import gridsheet  # noqa: E402

PICK = [("idle", 0, 0), ("walk", 2, 3), ("attack", 3, 6), ("slam", 0, 7), ("hurt", 1, 1), ("drink", 0, 6), ("fall", 2, 12),
        ("intro", 0, 12)]


def floor_bg(w, h):
    try:
        t = Image.open(os.path.join(ROOT, "assets/tiles/v2/stage1_hall.png")).convert("RGBA").crop((0, 0, 64, 64))
    except Exception:
        t = Image.new("RGBA", (64, 64), (48, 44, 40, 255))
    bg = Image.new("RGBA", (w, h))
    for y in range(0, h, 64):
        for x in range(0, w, 64):
            bg.paste(t, (x, y))
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 90))
    return Image.alpha_composite(bg, dark)


def build():
    W = 288 * len(PICK)
    sheet = floor_bg(W, 720)
    for i, (a, r, c) in enumerate(PICK):
        _, old = boss.original_grid(a)
        new = gridsheet.open_grid(os.path.join(ROOT, boss.REL, f"stage1_{a}.json"))
        box = (c * 288, r * 360, c * 288 + 288, r * 360 + 360)
        sheet.alpha_composite(old.crop(box), (i * 288, 0))
        sheet.alpha_composite(new.crop(box), (i * 288, 360))
    p = os.path.join(HERE, "preview_boss.png")
    sheet.save(p)
    return p
