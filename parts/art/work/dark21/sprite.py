"""트림 아틀라스(phaser-json-hash)에서 원 프레임을 복원한다 — 읽기 전용."""
import json, os
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.."))


def frame(rel, idx):
    js = json.load(open(os.path.join(ROOT, rel + ".json"), encoding="utf-8"))
    sheet = Image.open(os.path.join(ROOT, rel + ".png")).convert("RGBA")
    f = js["frames"][str(idx)]
    fr, ss, src = f["frame"], f["spriteSourceSize"], f["sourceSize"]
    out = Image.new("RGBA", (src["w"], src["h"]), (0, 0, 0, 0))
    out.paste(sheet.crop((fr["x"], fr["y"], fr["x"] + fr["w"], fr["y"] + fr["h"])), (ss["x"], ss["y"]))
    return out, js
