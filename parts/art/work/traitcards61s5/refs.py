"""Gemini 참고 그림 — 주인공·1층 적 오른쪽 대기 프레임 + 무기 looks 를 한 장에 (트림 아틀라스에서 잘라 냄)."""
import json, os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
SP = os.path.join(ROOT, "assets/sprites")


def atlas_frame(name, idx):
    j = json.load(open(os.path.join(SP, name + ".json"), encoding="utf-8"))
    im = Image.open(os.path.join(SP, name + ".png")).convert("RGBA")
    f = j["frames"][str(idx)]
    fr, ss, src = f["frame"], f["spriteSourceSize"], f["sourceSize"]
    out = Image.new("RGBA", (src["w"], src["h"]))
    out.paste(im.crop((fr["x"], fr["y"], fr["x"] + fr["w"], fr["y"] + fr["h"])), (ss["x"], ss["y"]))
    return out.crop(out.getbbox())


def build(weapon=None, bg=(128, 128, 128)):
    figs = [atlas_frame("player/v3/player_idle", 18)]
    for e in ("charger", "archer", "peddler", "porter"):
        figs.append(atlas_frame(f"enemies/v3/{e}_idle", 18 if e != "porter" else 12))
    if weapon:
        w = Image.open(os.path.join(SP, f"looks/{weapon}_base.png")).convert("RGBA")
        figs.insert(1, w.crop(w.getbbox()))
    H = max(f.height for f in figs) + 16
    W = sum(f.width for f in figs) + 16 * (len(figs) + 1)
    c = Image.new("RGBA", (W, H), bg + (255,))
    x = 16
    for f in figs:
        c.alpha_composite(f, (x, H - 8 - f.height))
        x += f.width + 16
    return c.resize((c.width * 3, c.height * 3), Image.NEAREST).convert("RGB")


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "ref"), exist_ok=True)
    for w in ("katana", "greatsword", "dagger", "bow"):
        build(w).save(os.path.join(HERE, "ref", f"ref_{w}.png"))
    print("ok")
