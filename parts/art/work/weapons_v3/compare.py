#!/usr/bin/env python3
"""무기 v3 비교 미리보기 (이 폴더에만 씀) — 시트(assets)를 읽어 합성한다. build.py 뒤에 실행.

preview_mock_lit.png      외곽 v2 바닥 위 1배(1920×1080 내부 렌더) 조명 합성 — 무기별 휴대·판정 프레임 나란히
preview_compare_old.png   구 무기 ↔ 새 무기 (칼: 이전 v3 강철 칼 git HEAD 사본 · 대검·단검: 구 16×24 무기 시트 ×6 손 맞춤)
사용: python3 parts/art/work/weapons_v3/compare.py [--old-katana <이전 katana_combo1.png>]
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

import wv3
from wv3 import PV, Q, hero, K

ROOT = os.path.normpath(os.path.join(wv3.HERE, "../../../.."))
P = os.path.join(ROOT, "assets/sprites")
PIV = (96, 186)


def frame(path, fw, fh, r, c):
    return Image.open(path).convert("RGBA").crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))


def comp(body, weapon, d, i, under=None):
    row = hero.DIRS.index(d)
    b = frame(os.path.join(P, "player/v3/%s.png" % body), 96, 144, row, i)
    c = Image.new("RGBA", (192, 192))
    if under is not None:
        c.alpha_composite(under)
    c.alpha_composite(b, (48, 48))
    if weapon:
        c.alpha_composite(frame(os.path.join(P, "weapons/v3/%s.png" % weapon), 192, 192, row, i))
    return c


SPOTS = [("칼 휴대", "player_idle", "katana_carry_idle", "down", 2),
         ("칼 1타 판정", "player_katana_combo1", "katana_combo1", "right", 2),
         ("대검 등", "player_idle_free", "greatsword_carry_idle", "up", 0),
         ("대검 1타", "player_greatsword_combo1", "greatsword_combo1", "right", 4),
         ("대검 끎", "player_idle_free", "greatsword_carry_drawn_idle", "down", 0),
         ("단검 역수", "player_idle_free", "dagger_carry_idle", "down", 0),
         ("단검 1타", "player_dagger_combo1", "dagger_combo1", "right", 2)]


def mock():
    spots = [(lab, comp(b, w, d, i), PIV, True) for lab, b, w, d, i in SPOTS]
    PV.mock_lit(spots, name="preview_mock_lit.png",
                title="1배(1920 내부 렌더) · 외곽 v2 바닥 · 무기 v3 (칼 B · 대검 A · 단검 B) — 활은 다음 단계")


def old_katana(path):
    if path and os.path.exists(path):
        return path
    tmp = os.path.join(wv3.HERE, "_old_katana_combo1.png")
    data = subprocess.run(["git", "-C", ROOT, "show", "HEAD:assets/sprites/weapons/v3/katana_combo1.png"], capture_output=True).stdout
    open(tmp, "wb").write(data)
    return tmp


def old_overlay(name, d, i):
    """구 16×24 무기 시트를 ×6 확대해 추정 손잡이를 새 손(handAnchors)에 맞춘 그림(2차 preview_oldweapon B 방식)."""
    import json
    js = json.load(open(os.path.join(P, "player/v3/player_%s.json" % name), encoding="utf-8"))
    seq, first, groups, old = Q.expand(name)
    oi = seq[i][2]
    ow = Q.old_weapon_frames(name)
    wf = ow["frames"][d][oi]
    g = Q.old_grip_estimate(wf, ow["off"], js["weapon"])
    h = js["handAnchors"][d][i]["handR"]
    big = wf.resize((wf.width * 6, wf.height * 6), Image.NEAREST)
    c = Image.new("RGBA", (192, 192))
    x, y = round(48 + h[0] - (g[0] * 6 + 3)), round(48 + h[1] - (g[1] * 6 + 3))
    tmp = Image.new("RGBA", (192, 192))
    tmp.alpha_composite(big, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))
    c.alpha_composite(tmp)
    return c


def compare(old_k):
    rows = [("칼 1타 판정", lambda: (comp_old_katana(old_k, "right", 2), comp("player_katana_combo1", "katana_combo1", "right", 2))),
            ("칼 3타", lambda: (comp_old_katana3(old_k, "down", 4), comp("player_katana_combo3", "katana_combo3", "down", 4))),
            ("대검 1타 판정", lambda: (old_gear("greatsword_combo1", "right", 4), comp("player_greatsword_combo1", "greatsword_combo1", "right", 4))),
            ("대검 내리찍기", lambda: (old_gear("greatsword_slam", "left", 8), comp("player_greatsword_slam", "greatsword_slam", "left", 8))),
            ("단검 1타 판정", lambda: (old_gear("dagger_combo1", "right", 2), comp("player_dagger_combo1", "dagger_combo1", "right", 2))),
            ("단검 3타", lambda: (old_gear("dagger_combo3", "left", 2), comp("player_dagger_combo3", "dagger_combo3", "left", 2)))]
    k = 2
    out = Image.new("RGBA", (2 * 2 * 192 * k + 60, 40 + 3 * 192 * k), PV.BG)
    dr = ImageDraw.Draw(out)
    PV.label(dr, 6, 6, "구 무기 ↔ 새 무기 v3 (2배) — 각 칸 왼쪽 = 구(칼: 이전 강철 칼 v3 · 대검/단검: 구 16×24 무기 ×6), 오른쪽 = 새")
    for j, (lab, fn) in enumerate(rows):
        a, b = fn()
        x0, y0 = 20 + (j % 2) * (192 * k * 2 + 20), 40 + (j // 2) * 192 * k
        for n, im in enumerate((a, b)):
            cell = Image.new("RGBA", (192, 192), (34, 36, 42, 255))
            cell.alpha_composite(im)
            cell = cell.crop((0, 24, 192, 192)).resize((192 * k, 168 * k), Image.NEAREST)
            out.alpha_composite(cell, (x0 + n * 192 * k, y0 + 20))
        PV.label(dr, x0 + 6, y0 + 22, lab)
    out.save(os.path.join(wv3.HERE, "preview_compare_old.png"))


def comp_old_katana(path, d, i):
    c = comp("player_katana_combo1", None, d, i)
    c.alpha_composite(frame(path, 192, 192, hero.DIRS.index(d), i))
    return c


def comp_old_katana3(path, d, i):
    p3 = path.replace("combo1", "combo3")
    if not os.path.exists(p3):
        data = subprocess.run(["git", "-C", ROOT, "show", "HEAD:assets/sprites/weapons/v3/katana_combo3.png"], capture_output=True).stdout
        open(p3, "wb").write(data)
    c = comp("player_katana_combo3", None, d, i)
    c.alpha_composite(frame(p3, 192, 192, hero.DIRS.index(d), i))
    return c


def old_gear(name, d, i):
    c = comp("player_" + name, None, d, i)
    c.alpha_composite(old_overlay(name, d, i))
    return c


if __name__ == "__main__":
    ok = sys.argv[sys.argv.index("--old-katana") + 1] if "--old-katana" in sys.argv else None
    mock()
    path = old_katana(ok)
    compare(path)
    for f in (os.path.join(wv3.HERE, "_old_katana_combo1.png"), os.path.join(wv3.HERE, "_old_katana_combo3.png")):
        if os.path.exists(f):
            os.remove(f)
    print("mock + compare ok")
