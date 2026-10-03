#!/usr/bin/env python3
"""무기 v3 비교 미리보기 (이 폴더에만 씀) — assets 시트를 읽어 합성한다. build.py 뒤에 실행.

preview_mock_lit.png      외곽 v2 바닥 위 1배(1920×1080 내부 렌더) 조명 합성 — 4무기 휴대·판정 프레임 나란히
preview_compare_old.png   구 무기 ↔ 새 무기 (칼: 재디자인 전 강철 칼 v3(git OLD_REF) · 대검·단검·활: 구 16×24 무기 시트 ×6 손 맞춤)
시트마다 틀 크기가 다르므로(대검 확대 틀, Q45) JSON frameWidth/frameHeight·playerFrameOffset 을 읽어 공통 캔버스에 놓는다.
사용: python3 parts/art/work/weapons_v3/compare.py
"""
import json
import os
import subprocess

from PIL import Image, ImageDraw

import wv3
from wv3 import PV, Q, hero

ROOT = os.path.normpath(os.path.join(wv3.HERE, "../../../.."))
P = os.path.join(ROOT, "assets/sprites")
OLD_REF = "f39a0cf~1"                                  # 재디자인 전(강철 칼 v3) 커밋
CW, CH, BOX, BOY = 256, 288, 80, 80                    # 공통 캔버스 · 몸 놓는 자리
PIV = (BOX + hero.PIV[0], BOY + hero.PIV[1])


def frame(path, fw, fh, r, c):
    return Image.open(path).convert("RGBA").crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))


def comp(body, weapon, d, i, extra=None):
    """몸 + 무기(JSON 틀 크기·오프셋) → 공통 캔버스. extra = (192 틀 그림, 몸 오프셋 48) 덧그림(구 무기)."""
    row = hero.DIRS.index(d)
    c = Image.new("RGBA", (CW, CH))
    c.alpha_composite(frame(os.path.join(P, "player/v3/%s.png" % body), hero.FW, hero.FH, row, i), (BOX, BOY))
    if weapon:
        js = json.load(open(os.path.join(P, "weapons/v3/%s.json" % weapon), encoding="utf-8"))
        o = js["playerFrameOffset"]
        c.alpha_composite(frame(os.path.join(P, "weapons/v3/%s.png" % weapon), js["frameWidth"], js["frameHeight"], row, i),
                          (BOX - o["x"], BOY - o["y"]))
    if extra is not None:
        c.alpha_composite(extra, (BOX - 48, BOY - 48))
    return c


SPOTS = [("칼 휴대", "player_idle", "katana_carry_idle", "down", 2),
         ("칼 1타", "player_katana_combo1", "katana_combo1", "right", 2),
         ("대검 등", "player_idle_free", "greatsword_carry_idle", "up", 0),
         ("대검 1타", "player_greatsword_combo1", "greatsword_combo1", "right", 4),
         ("단검 역수", "player_idle_free", "dagger_carry_idle", "down", 0),
         ("단검 1타", "player_dagger_combo1", "dagger_combo1", "right", 2),
         ("활 휴대", "player_idle_free", "bow_carry_idle", "down", 0),
         ("활 가득", "player_bow_aim", "bow_aim", "right", 5)]


def mock():
    spots = [(lab, comp(b, w, d, i), PIV, True) for lab, b, w, d, i in SPOTS]
    PV.mock_lit(spots, name="preview_mock_lit.png",
                title="1배(1920 내부 렌더) · 외곽 v2 바닥 · 무기 v3 4종 (Q44 굵고 크게 · Q45 대검 확대 틀)")


def git_png(path, out):
    data = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (OLD_REF, path)], capture_output=True).stdout
    open(out, "wb").write(data)
    return out


def old_overlay(name, d, i):
    """구 16×24 무기 시트 ×6 — 추정 손잡이를 새 손(handAnchors[gripHand])에 맞춘 그림(192 틀, 몸 (48,48))."""
    js = json.load(open(os.path.join(P, "player/v3/player_%s.json" % name), encoding="utf-8"))
    seq, first, groups, old = Q.expand(name)
    ow = Q.old_weapon_frames(name)
    wf = ow["frames"][d][seq[i][2]]
    g = Q.old_grip_estimate(wf, ow["off"], js["weapon"])
    h = js["handAnchors"][d][i][Q.GRIP_HAND[js["weapon"]]]
    big = wf.resize((wf.width * 6, wf.height * 6), Image.NEAREST)
    x, y = round(48 + h[0] - (g[0] * 6 + 3)), round(48 + h[1] - (g[1] * 6 + 3))
    c = Image.new("RGBA", (192, 192))
    c.alpha_composite(big, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))
    return c


def old_katana(n, d, i, tmp):
    p = git_png("assets/sprites/weapons/v3/katana_combo%d.png" % n, tmp)
    return comp("player_katana_combo%d" % n, None, d, i, extra=frame(p, 192, 192, hero.DIRS.index(d), i))


def old_gear(name, d, i):
    return comp("player_" + name, None, d, i, extra=old_overlay(name, d, i))


def compare():
    tmp = os.path.join(wv3.HERE, "_old_katana.png")
    rows = [("칼 1타 판정", old_katana(1, "right", 2, tmp), comp("player_katana_combo1", "katana_combo1", "right", 2)),
            ("칼 3타", old_katana(3, "down", 4, tmp), comp("player_katana_combo3", "katana_combo3", "down", 4)),
            ("대검 1타 판정", old_gear("greatsword_combo1", "right", 4), comp("player_greatsword_combo1", "greatsword_combo1", "right", 4)),
            ("대검 내리찍기", old_gear("greatsword_slam", "down", 8), comp("player_greatsword_slam", "greatsword_slam", "down", 8)),
            ("단검 1타 판정", old_gear("dagger_combo1", "right", 2), comp("player_dagger_combo1", "dagger_combo1", "right", 2)),
            ("단검 3타", old_gear("dagger_combo3", "left", 2), comp("player_dagger_combo3", "dagger_combo3", "left", 2)),
            ("활 가득 당김", old_gear("bow_aim", "right", 5), comp("player_bow_aim", "bow_aim", "right", 5)),
            ("활 장전(뽑기)", old_gear("bow_reload", "up", 3), comp("player_bow_reload", "bow_reload", "up", 3))]
    if os.path.exists(tmp):
        os.remove(tmp)
    k = 2
    cw, ch = CW, 248                                    # 캔버스에서 보여 줄 부분(대검 확대 틀까지)
    x_off, y_off = (CW - cw) // 2, CH - ch
    out = Image.new("RGBA", (2 * (2 * cw * k + 24) + 20, 40 + 4 * (ch * k + 24)), PV.BG)
    dr = ImageDraw.Draw(out)
    PV.label(dr, 6, 6, "구 무기 ↔ 새 무기 v3 (2배) — 각 칸 왼쪽 = 구(칼: 재디자인 전 강철 칼 · 대검/단검/활: 구 16×24 무기 ×6), 오른쪽 = 새(Q44 굵고 크게)")
    for j, (lab, a, b) in enumerate(rows):
        x0, y0 = 20 + (j % 2) * (2 * cw * k + 24), 40 + (j // 2) * (ch * k + 24)
        for n, im in enumerate((a, b)):
            cell = Image.new("RGBA", (CW, CH), (34, 36, 42, 255))
            cell.alpha_composite(im)
            out.alpha_composite(cell.crop((x_off, y_off, x_off + cw, y_off + ch)).resize((cw * k, ch * k), Image.NEAREST), (x0 + n * cw * k, y0 + 20))
        PV.label(dr, x0 + 6, y0 + 22, lab)
    out.save(os.path.join(wv3.HERE, "preview_compare_old.png"))


if __name__ == "__main__":
    mock()
    compare()
    print("mock + compare ok")
