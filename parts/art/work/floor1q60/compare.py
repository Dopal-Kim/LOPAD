"""60라운드 Q4 — 징집병 전(assets/enemies/v3 현행) / 후(out/dummy60_*) 비교판.

python3 parts/art/work/floor1q60/compare.py
산출: preview_enemy_before_after.png (4배, 대표 프레임) · preview_enemy_attack_before_after.png (2배, 공격 전 프레임 right·down)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "diag"))
from sheet import frames as asset_frames, SPR  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

FONT = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 22)
FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 16)
BG = (38, 36, 40, 255)
DIRS = ["down", "up", "left", "right"]


def after_frames(act):
    j = json.load(open(os.path.join(HERE, "out", "dummy60_%s.json" % act)))
    im = Image.open(os.path.join(HERE, "out", "dummy60_%s.png" % act)).convert("RGBA")
    fw, fh, n = j["frameWidth"], j["frameHeight"], j["frames"]
    return j, [[im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r in range(4)]


def before_frames(act):
    meta, fr = asset_frames(os.path.join(SPR, "enemies/v3", "dummy_%s" % act))
    return meta, fr


def up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def board_key():
    """대표 프레임 4배: idle down0·left0 · attack 젖힘·휘두름·내리꽂기(right) — 전/후 두 줄."""
    k = 4
    jb, ib = before_frames("idle")[0], before_frames("idle")[1]
    ja, ia = after_frames("idle")
    _, ab = before_frames("attack")
    ja2, aa = after_frames("attack")
    # 구 시트: windup 0~1, swing 2, impact 3~4 / 새: windup 0~2, swing 3, impact 4~6
    cols = [("대기 정면", ib[0][0], ia[0][0]), ("대기 측면", ib[2][0], ia[2][0]),
            ("공격 젖힘", ab[3][1], aa[3][2]), ("공격 휘두름", ab[3][2], aa[3][3]), ("공격 내리꽂기", ab[3][3], aa[3][4]),
            ("공격 정면 휘두름", ab[0][2], aa[0][3])]
    cw, ch = 96 * k, 144 * k
    W = 140 + len(cols) * (cw + 12)
    H = 60 + 2 * (ch + 40)
    out = Image.new("RGBA", (W, H), (20, 20, 24, 255))
    d = ImageDraw.Draw(out)
    d.text((10, 10), "징집병(주정뱅이 패거리) 전/후 — 4배, 96×144 도트(화면 48×72). 위 = 현행 assets, 아래 = 60라운드 샘플", fill=(235, 225, 200), font=FONT)
    for r, lab in enumerate(("현행", "보강안")):
        y = 60 + r * (ch + 40)
        d.text((10, y + ch // 2), lab, fill=(232, 184, 88), font=FONT)
        for c, (name, b, a) in enumerate(cols):
            x = 140 + c * (cw + 12)
            cell = Image.new("RGBA", (cw, ch), BG)
            cell.alpha_composite(up(b if r == 0 else a, k))
            out.alpha_composite(cell, (x, y + 28))
            d.text((x + 4, y + 2), name, fill=(200, 190, 170), font=FONT_S)
    out.convert("RGB").save(os.path.join(HERE, "preview_enemy_before_after.png"))
    print("board", out.size)


def board_attack():
    k = 2
    _, ab = before_frames("attack")
    ja, aa = after_frames("attack")
    jb = json.load(open(os.path.join(SPR, "enemies/v3/dummy_attack.json")))
    rows = []
    for di in (3, 0):
        rows.append(("현행 %s · 7프레임" % DIRS[di], ab[di], jb["frameDurationsMs"], jb.get("phaseFrames")))
        rows.append(("보강안 %s · 10프레임" % DIRS[di], aa[di], ja["frameDurationsMs"], ja.get("phaseFrames")))
    cw, ch = 96 * k, 144 * k
    W = 20 + 10 * (cw + 6)
    H = 50 + len(rows) * (ch + 34)
    out = Image.new("RGBA", (W, H), (20, 20, 24, 255))
    d = ImageDraw.Draw(out)
    d.text((10, 10), "징집병 공격 전/후 — 2배. 구 프레임 시작 ms 그대로(예비 0 · 휘두름 120 · 타격 170 · 회복 280ms, 계 400ms)", fill=(235, 225, 200), font=FONT)
    for r, (lab, fr, ms, ph) in enumerate(rows):
        y = 50 + r * (ch + 34)
        t = 0
        for c, f in enumerate(fr):
            x = 10 + c * (cw + 6)
            st = next((kk for kk, v in (ph or {}).items() if c in v), "")
            cell = Image.new("RGBA", (cw, ch), BG if st != "impact" else (58, 44, 36, 255))
            cell.alpha_composite(up(f, k))
            out.alpha_composite(cell, (x, y + 24))
            d.text((x + 2, y + 2), "%s %d %s %dms" % (lab if c == 0 else "", c, st, t), fill=(200, 190, 170), font=FONT_S)
            t += ms[c]
    out.convert("RGB").save(os.path.join(HERE, "preview_enemy_attack_before_after.png"))
    print("attack board", out.size)


if __name__ == "__main__":
    board_key()
    board_attack()
