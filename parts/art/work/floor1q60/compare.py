"""60라운드 Q8 — 일반 적 3종 전(53라운드, before/ 사본) / 후(out/<id>60_*) 비교판.

python3 parts/art/work/floor1q60/compare.py
산출: preview_enemies_before_after.png (3배, 적마다 대표 프레임 전/후 두 줄)
      preview_enemy_attack_before_after.png (2배, 3종 공격 전 프레임 right 행 전/후 — 구 시각 표기)
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 22)
FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 16)
BG = (38, 36, 40, 255)
NAMES = {"dummy": "징집병", "archer": "사수", "charger": "결사병"}
DIRS = ["down", "up", "left", "right"]


def frames(path):
    j = json.load(open(path + ".json"))
    im = Image.open(path + ".png").convert("RGBA")
    fw, fh, n = j["frameWidth"], j["frameHeight"], j["frames"]
    return j, [[im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r in range(4)]


def before(eid, act):
    return frames(os.path.join(HERE, "before", f"{eid}_{act}"))


def after(eid, act):
    return frames(os.path.join(HERE, "out", f"{eid}60_{act}"))


def up(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def key_cols(eid):
    """(이름, 전 (동작, 행, 열), 후 (동작, 행, 열)) — 같은 순간끼리."""
    b_strike = {"dummy": 3, "archer": 2, "charger": 4}[eid]
    a_strike = {"dummy": 4, "archer": 3, "charger": 4}[eid]
    b_wind = {"dummy": 1, "archer": 1, "charger": 2}[eid]
    a_wind = {"dummy": 2, "archer": 2, "charger": 2}[eid]
    return [("대기 정면", ("idle", 0, 0), ("idle", 0, 0)), ("대기 측면", ("idle", 2, 0), ("idle", 2, 0)),
            ("걷기 측면", ("walk", 3, 2), ("walk", 3, 2)),
            ("공격 예비", ("attack", 3, b_wind), ("attack", 3, a_wind)), ("공격 타격·발사", ("attack", 3, b_strike), ("attack", 3, a_strike)),
            ("공격 정면", ("attack", 0, b_strike), ("attack", 0, a_strike)), ("피격", ("hurt", 3, 1), ("hurt", 3, 1))]


def board_key():
    k = 3
    rows = []
    for eid in ("dummy", "archer", "charger"):
        cols = key_cols(eid)
        for label, getter, idx in (("현행", before, 1), ("60라운드", after, 2)):
            cells = []
            for c in cols:
                act, r, cc = c[idx]
                _, fr = getter(eid, act)
                cells.append((c[0], fr[r][cc]))
            rows.append((f"{NAMES[eid]} {label}", cells))
    cw = max(cell.width for _, cs in rows for _, cell in cs) * k
    ch = max(cell.height for _, cs in rows for _, cell in cs) * k
    W = 170 + 7 * (cw + 8)
    H = 50 + len(rows) * (ch + 30)
    out = Image.new("RGB", (W, H), (20, 20, 24))
    d = ImageDraw.Draw(out)
    d.text((10, 10), "일반 적 3종 전/후 — 3배(징집병·사수 96×144, 결사병 128×176 도트). 짝수 줄 = 60라운드 보강", fill=(235, 225, 200), font=FONT)
    for ri, (lab, cells) in enumerate(rows):
        y = 50 + ri * (ch + 30)
        d.text((10, y + ch // 2), lab, fill=(232, 184, 88) if "60" in lab else (200, 190, 170), font=FONT)
        for ci, (name, im) in enumerate(cells):
            x = 170 + ci * (cw + 8)
            cell = Image.new("RGBA", (cw, ch), BG)
            u = up(im, k)
            cell.alpha_composite(u, ((cw - u.width) // 2, ch - u.height))
            out.paste(cell.convert("RGB"), (x, y + 24))
            if ri % 2 == 0:
                d.text((x + 4, y + 2), name, fill=(200, 190, 170), font=FONT_S)
    out.save(os.path.join(HERE, "preview_enemies_before_after.png"))
    print("board", out.size)


def board_attack():
    k = 2
    rows = []
    for eid in ("dummy", "archer", "charger"):
        jb, fb = before(eid, "attack")
        ja, fa = after(eid, "attack")
        rows.append((f"{NAMES[eid]} 현행 {jb['frames']}f", fb[3], jb["frameDurationsMs"], jb.get("phaseFrames") or {}))
        rows.append((f"{NAMES[eid]} 60 {ja['frames']}f", fa[3], ja["frameDurationsMs"], ja.get("phaseFrames") or {}))
    cw = max(fr[0].width for _, fr, _, _ in rows) * k
    ch = max(fr[0].height for _, fr, _, _ in rows) * k
    W = 10 + 10 * (cw + 4)
    H = 50 + len(rows) * (ch + 30)
    out = Image.new("RGB", (W, H), (20, 20, 24))
    d = ImageDraw.Draw(out)
    d.text((10, 10), "공격(오른쪽 보기) 전/후 — 2배. 구 프레임 시작 ms 그대로(판정 시각 불변), 숫자 = 시작 ms", fill=(235, 225, 200), font=FONT)
    for ri, (lab, fr, ms, ph) in enumerate(rows):
        y = 50 + ri * (ch + 30)
        t = 0
        for c, f in enumerate(fr):
            x = 10 + c * (cw + 4)
            st = next((kk for kk, v in ph.items() if c in v), "")
            hot = st in ("impact", "fire", "smash", "charge")
            cell = Image.new("RGBA", (cw, ch), (58, 44, 36, 255) if hot else BG)
            u = up(f, k)
            cell.alpha_composite(u, ((cw - u.width) // 2, ch - u.height))
            out.paste(cell.convert("RGB"), (x, y + 26))
            d.text((x + 2, y + 4), (lab + " · " if c == 0 else "") + f"{c} {st} {t}", fill=(200, 190, 170), font=FONT_S)
            t += ms[c]
    out.save(os.path.join(HERE, "preview_enemy_attack_before_after.png"))
    print("attack board", out.size)


if __name__ == "__main__":
    board_key()
    board_attack()
