#!/usr/bin/env python3
"""차지 번쩍임 lv1~3 비교 미리보기(55라운드 Q27 — 3단만 백열) — 이 폴더에만 쓴다.

preview_charge_flash.png   행 = lv1 · lv2 · lv3, 열 = 프레임 0~4(right | down), 몸 + 무기(차지 홀드 자세) + 번쩍임, ×2.
                           보라 테 = glowFrames(백열 허용 프레임). 아래 띠 = 1배 조명 합성(가장 밝은 프레임).
사용: python3 parts/art/work/combo55/preview_charge_flash.py
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import preview55 as P  # noqa: E402
import moves as M  # noqa: E402

CW, CH = 200, 270                       # 1배 칸
DIRS = ("right", "down")
GLOW = (170, 90, 220, 255)


def cell_img(lv, d, k):
    ch = M.GS["greatsword_charge"]
    bi = ch["loopFrames"][0]
    c = Image.new("RGBA", (CW, CH), P.BG)
    px, py = CW // 2, CH - 30
    bj, bim = P.load(P.P3, "player_greatsword_charge")
    wj, wim = P.load(P.W3, "greatsword_charge")
    c.alpha_composite(P.cell(bj, bim, d, bi), (px - bj["pivot"]["x"], py - bj["pivot"]["y"]))
    c.alpha_composite(P.cell(wj, wim, d, bi), (px - wj["pivot"]["x"], py - wj["pivot"]["y"]))
    j, im = P.load(P.F3, "greatsword_charge_flash_lv%d" % lv)
    if k is not None:
        f = P.cell(j, im, d, k)
        c.alpha_composite(f, (px - j["pivot"]["x"], py - j["pivot"]["y"]))
    return c, j


def main():
    S = 2
    F = 5
    head = 26
    colw = CW * S + 4
    W_ = 90 + colw * F * len(DIRS) + 8
    rowh = CH * S + 22
    lit_h = CH + 24
    out = Image.new("RGBA", (W_, head + rowh * 3 + lit_h), (14, 14, 17, 255))
    dr = ImageDraw.Draw(out)
    P.FXP.label(dr, 6, 6, "대검 차지 번쩍임 lv1~3 (×2 · 몸+무기 = 차지 홀드 자세) · 보라 테 = glowFrames(백열 허용, Q27 = 3단만) · 왼쪽 열 묶음 right / 오른쪽 down")
    for r, lv in enumerate((1, 2, 3)):
        y0 = head + r * rowh
        for di, d in enumerate(DIRS):
            for k in range(F):
                c, j = cell_img(lv, d, k)
                x0 = 90 + (di * F + k) * colw
                out.alpha_composite(c.resize((CW * S, CH * S), Image.NEAREST), (x0, y0 + 18))
                if k in (j.get("glowFrames") or []):
                    dr.rectangle((x0 - 2, y0 + 16, x0 + CW * S + 1, y0 + 18 + CH * S + 1), outline=GLOW, width=2)
                P.FXP.label(dr, x0 + 2, y0 + 2, "%s f%d %dms" % (d, k, j["frameDurationsMs"][k]))
        P.FXP.label(dr, 6, y0 + 18 + CH, "lv%d" % lv)
        P.FXP.label(dr, 6, y0 + 36 + CH, "glow %s" % (j.get("glowFrames"),))
        P.FXP.label(dr, 6, y0 + 54 + CH, "colors %d" % j["colors"])
    # 1배 조명 합성: lv1·lv2·lv3 의 f1(가장 밝은 프레임) right · down
    y0 = head + rowh * 3
    n = 6
    base = P.FXP.floor(CW * n, CH)
    lights = []
    for i, (lv, d) in enumerate([(lv, d) for lv in (1, 2, 3) for d in DIRS]):
        c, _ = cell_img(lv, d, 1)
        base.alpha_composite(P._transparent(c), (i * CW, 0))
        lights.append(dict(x=i * CW + CW // 2, y=CH - 110, color="#b0611a", radius=150, intensity=0.75))
    lit = P.FXP.light_scene(base, lights)
    out.paste(lit.convert("RGBA"), (90, y0 + 20))
    P.FXP.label(dr, 6, y0 + 4, "1배 조명 합성 · f1 · lv1 right/down · lv2 right/down · lv3 right/down (외곽 거리 바닥, 주변광 0.425/0.425/0.475)")
    out.convert("RGB").save(os.path.join(HERE, "preview_charge_flash.png"))
    print("preview_charge_flash.png", out.size)


if __name__ == "__main__":
    main()
