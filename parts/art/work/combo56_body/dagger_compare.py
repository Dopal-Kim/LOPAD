"""56라운드 Q4 단검 1.3배 — 전(HEAD 사본 dagger_prev/old) ↔ 후(assets) 비교 그림. 몸 + 무기 + 찌르기 판정 참고 상자(이전 하늘색 · 56 노랑)."""
import json, math, os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
P = os.path.join(ROOT, "assets/sprites")
OLD = os.path.join(HERE, "dagger_prev/old")
DIRS = ["down", "up", "left", "right"]
BASE = {"right": 0, "down": 90, "left": 180, "up": -90}
W, OFF = 320, 64


def cell(png, j, d, i):
    fw, fh = j["frameWidth"], j["frameHeight"]
    r = j["directions"].index(d)
    return Image.open(png).convert("RGBA").crop((i * fw, r * fh, (i + 1) * fw, (r + 1) * fh))


def comp(name, d, i, old):
    bj = json.load(open(os.path.join(P, "player/v3/player_%s.json" % name)))
    body = cell(os.path.join(P, "player/v3/player_%s.png" % name), bj, d, i)
    wp = os.path.join(OLD if old else os.path.join(P, "weapons/v3"), name + ".png")
    wj = json.load(open(os.path.join(OLD if old else os.path.join(P, "weapons/v3"), name + ".json")))
    w = cell(wp, wj, d, i)
    c = Image.new("RGBA", (W, W), (34, 32, 38, 255))
    c.alpha_composite(body, (48 + OFF, 48 + OFF))
    c.alpha_composite(w, (OFF, OFF))
    th = bj.get("thrust")
    if th and i in (bj.get("activeFrames") or []):
        dr = ImageDraw.Draw(c)
        new = bj.get("hitReference56", {}).get("thrust", th)
        t = old and th or new
        ang = math.radians(BASE[d] + (t["angleDeg"] if d in ("right", "down") else -t["angleDeg"]))
        ox, oy = 96 + OFF, 186 - 40 + OFF
        ux, uy = math.cos(ang), math.sin(ang)
        nx, ny = -uy, ux
        hw = t["widthPx"] / 2
        a, b = t["fromPx"], t["lengthPx"]
        pts = [(ox + ux * a + nx * hw, oy + uy * a + ny * hw), (ox + ux * b + nx * hw, oy + uy * b + ny * hw),
               (ox + ux * b - nx * hw, oy + uy * b - ny * hw), (ox + ux * a - nx * hw, oy + uy * a - ny * hw)]
        dr.polygon(pts, outline=(90, 220, 230, 255) if old else (240, 200, 60, 255))
    return c


def main():
    rows = [("dagger_combo1", 2), ("dagger_combo3", 2), ("dagger_combo2", 3), ("dagger_special", 8), ("dagger_carry_idle", 0)]
    img = Image.new("RGBA", (W * 8, W * len(rows) + 20), (20, 20, 24, 255))
    dr = ImageDraw.Draw(img)
    dr.text((4, 4), "56 Q4 dagger x1.3 — each pair: before | after  (right, down, left, up) · box = thrust hit ref (cyan before, yellow x1.5)", fill=(230, 230, 230, 255))
    for r, (name, i) in enumerate(rows):
        for c, d in enumerate(["right", "down", "left", "up"]):
            if name.startswith("dagger_carry"):
                bj = json.load(open(os.path.join(P, "player/v3/player_idle_free.json")))
                body = cell(os.path.join(P, "player/v3/player_idle_free.png"), bj, d, 0)
                for k, old in enumerate((True, False)):
                    src = OLD if old else os.path.join(P, "weapons/v3")
                    wj = json.load(open(os.path.join(src, name + ".json")))
                    w = cell(os.path.join(src, name + ".png"), wj, d, 0)
                    cc = Image.new("RGBA", (W, W), (34, 32, 38, 255))
                    cc.alpha_composite(body, (48 + OFF, 48 + OFF)); cc.alpha_composite(w, (OFF, OFF))
                    img.paste(cc, ((c * 2 + k) * W, 20 + r * W))
                continue
            for k, old in enumerate((True, False)):
                img.paste(comp(name, d, i, old), ((c * 2 + k) * W, 20 + r * W))
    img.save(os.path.join(HERE, "preview_dagger_before_after_x1.png"))
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(os.path.join(HERE, "preview_dagger_before_after_x2.png"))


if __name__ == "__main__":
    main()
