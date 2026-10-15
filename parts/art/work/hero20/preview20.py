"""P20 미리보기 — 이전(git HEAD = P19) ↔ 새 몸(assets) 몸 + 무기 오버레이 겹친 비교.

사용: python3 parts/art/work/hero20/preview20.py [동작 …]   → out/preview/<동작>.png (위 = 이전, 아래 = P20, 2배) · <동작>.gif
"""
import json
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))
import gridsheet  # noqa: E402

REV = "ee9c0fd"          # P20 직전(P19 결과)
CACHE = os.path.join(HERE, "out", "head")
OUT = os.path.join(HERE, "out", "preview")
BG = (40, 42, 52, 255)

PAIRS = {  # 동작: (몸, 오버레이)
    "idle_katana": ("player_idle", "weapons/v3/katana_carry_idle"),
    "run_greatsword": ("player_run_free", "weapons/v3/greatsword_carry_run"),
    "dash": ("player_dash", "weapons/v3/katana_carry_dash"),
    "turn_skid": ("player_turn_skid", "weapons/v3/katana_carry_turn_skid"),
    "hurt": ("player_hurt", None), "death": ("player_death", None),
    "katana_fall": ("player_katana_fall", "weapons/v3/katana_fall"),
    "katana_iai": ("player_katana_iai", "weapons/v3/katana_iai"),
    "katana_spin": ("player_katana_spin", "weapons/v3/katana_spin"),
    "greatsword_cleave": ("player_greatsword_cleave", "weapons/v3/greatsword_cleave"),
    "greatsword_leap_slam": ("player_greatsword_leap_slam", "weapons/v3/greatsword_leap_slam"),
    "greatsword_charge_swing": ("player_greatsword_charge_swing", "weapons/v3/greatsword_charge_swing"),
    "dagger_backstab": ("player_dagger_backstab", "weapons/v3/dagger_backstab"),
    "bow_draw_hold": ("player_bow_draw_hold", "weapons/v3/bow_draw_hold"),
    "bow_reload": ("player_bow_reload", "weapons/v3/bow_reload"),
    "groggy": ("player_groggy", "weapons/v3/katana_carry_groggy"),
    "birth": ("player_birth", None),
}


def _git(path):
    return subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (REV, path)], capture_output=True, check=True).stdout


def head_json(rel):
    jp = os.path.join(CACHE, rel + ".json")
    if not os.path.exists(jp):
        raw = _git("assets/sprites/%s.json" % rel)
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        m = json.loads(raw)
        for t in m.get("textures", []) or [{"image": m.get("image") or os.path.basename(rel) + ".png"}]:
            with open(os.path.join(os.path.dirname(jp), t["image"]), "wb") as f:
                f.write(_git("assets/sprites/%s/%s" % (os.path.dirname(rel), t["image"])))
        with open(jp, "wb") as f:
            f.write(raw)
    return jp


def grid(rel, head):
    jp = head_json(rel) if head else os.path.join(ROOT, "assets", "sprites", rel + ".json")
    m = gridsheet.load_meta(jp)
    return m, gridsheet.open_grid(jp)


def frames(body, ov, d, head):
    bm, bi = grid("player/v3/" + body, head)
    r = bm["directions"].index(d) if d in bm["directions"] else 0
    fw, fh = bm["frameWidth"], bm["frameHeight"]
    om = oi = None
    if ov:
        om, oi = grid(ov, head)
    out = []
    for c in range(bm["frames"]):
        can = Image.new("RGBA", (240, 240), BG)
        ox, oy = 72, 60
        if fw == 192:
            ox, oy = 24, 12
        can.alpha_composite(bi.crop((c * fw, r * fh, c * fw + fw, r * fh + fh)), (ox, oy))
        if om and c < om["frames"]:
            ro = om["directions"].index(d)
            po = om["playerFrameOffset"]
            cell = oi.crop((c * om["frameWidth"], ro * om["frameHeight"], (c + 1) * om["frameWidth"], (ro + 1) * om["frameHeight"]))
            t = Image.new("RGBA", can.size, (0, 0, 0, 0))
            t.paste(cell, (ox - po["x"], oy - po["y"]))
            can.alpha_composite(t)
        out.append(can)
    return out, bm["frameDurationsMs"]


def build(names=None, dirs=("right", "down", "left", "up")):
    os.makedirs(OUT, exist_ok=True)
    for name in names or PAIRS:
        body, ov = PAIRS[name]
        rows, gif = [], []
        for d in dirs:
            try:
                a, ms = frames(body, ov, d, True)
                b, ms2 = frames(body, ov, d, False)
            except (ValueError, subprocess.CalledProcessError):
                continue
            rows += [a, b]
            if d == dirs[0]:
                for x, y in zip(a + [a[-1]] * (len(b) - len(a)), b):
                    g = Image.new("RGBA", (480, 240), BG)
                    g.paste(x, (0, 0)); g.paste(y, (240, 0))
                    gif.append(g.resize((960, 480), Image.NEAREST))
                gms = ms2
        n = max(len(r) for r in rows)
        sheet = Image.new("RGBA", (240 * n, 240 * len(rows)), BG)
        for i, r in enumerate(rows):
            for j, im in enumerate(r):
                sheet.alpha_composite(im, (j * 240, i * 240))
        sheet.save(os.path.join(OUT, name + ".png"))
        gif[0].save(os.path.join(OUT, name + ".gif"), save_all=True, append_images=gif[1:], duration=[max(40, m * 2) for m in gms], loop=0,
                    disposal=2)
        print(name, len(rows), n)


if __name__ == "__main__":
    build(sys.argv[1:] or None)
