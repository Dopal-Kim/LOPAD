"""P20 1단계 — 새 몸 모델 시트(96×144 게임 크기) + 키아트·옛 시트 비교 그림.

출력: parts/art/work/hero20/model_sheet_compare.png
  1행: 키아트 hero3_b (축소) · 2행: 새 모델 2배(정면·측면·뒷면·대기·질주·대쉬·내려베기 + 대각 2) · 3행: 같은 것 1배(게임 화면 48×72 크기, 줌 1.75 근사)
  4행: 옛 P19 시트 같은 자세(비교)
사용: python3 parts/art/work/hero20/model_sheet.py
"""
import math
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
import rig20  # noqa: E402
from rig20 import pose  # noqa: E402

BG = (52, 56, 70, 255)


def neutral(d):
    if d in rig20.SIDE:
        return pose(crouch=0.5, foot=((-4.0, 0), (4.5, 0)), hand=((-1.0, 0), (1.5, 0)), lean_body=0.2, flame=1)
    return pose(crouch=0.5, flame=1, stanceW=0.0)


def idle(d):
    if d in rig20.SIDE:
        return pose(breath=1, crouch=5.0, foot=((-9.5, 0), (8.5, 0)), tilt=16.0, lean_body=0.6, hdx=1.0, flame=2, eyeHot=1,
                    hand=((-2.0, -3.0), (4.0, -4.0)), elbow=None)
    return pose(breath=1, crouch=5.0, stanceW=2.0, squash=0.12, step=(2.5, -2.0), footdx=(1.0, -0.5), shift=-0.6, twist=-0.8,
                flame=2, eyeHot=1, hand=((1.5, -4.0), (1.0, -3.0)))


def sprint(d):
    return pose(crouch=5.0, tilt=28.0, lean_body=0.6, gdx=-3.0, foot=((-15.0, 6), (14.0, 0)), hand=((9.0, -10.0), (-9.0, -4.0)),
                head=0, flame=3, eyeHot=1)


def lunge(d):
    return pose(crouch=10.5, tilt=42.0, lean_body=0.5, gdx=-3.0, foot=((-20.0, 2), (12.0, 0)), hand=((12.0, -16.0), (-12.0, -6.0)),
                head=1, flame=4, eyeHot=1, glow=1, pulse=1)


def overhead(d):
    # 칼을 머리 위로 든 정점(키아트 OVERHEAD SLASH) — 두 손이 머리 위 뒤쪽
    f = 1 if d == "right" else -1
    hx = 32 + f * (-2.0)
    return pose(crouch=6.0, tilt=-6.0, gdx=-1.0, foot=((-10.0, 0), (11.0, 0)), handAt={"R": (hx, 9.0), "L": (hx + f * 2.5, 12.0)},
                head=0, flame=5, eyeHot=1, pulse=1)


SHOTS = [("front", "down", neutral), ("side R", "right", neutral), ("back", "up", neutral), ("side L", "left", neutral),
         ("idle", "down", idle), ("idle", "right", idle), ("sprint", "right", sprint), ("lunge dash", "right", lunge),
         ("overhead", "right", overhead), ("3/4 d-r", "down-right", lambda d: rig20.pose(crouch=3.0, flame=1, lean_f=0.6,
                                                                                        feet=((7.0, -2.5), (-7.0, 2.5)))),
         ("3/4 u-l", "up-left", lambda d: rig20.pose(crouch=3.0, flame=1, lean_f=0.6, feet=((7.0, -2.5), (-7.0, 2.5))))]


def render_all():
    out = []
    for label, d, fn in SHOTS:
        R = rig20.draw_rig(d, fn(d))
        out.append((label, d, R.image))
    return out


def old_frames():
    sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))
    import gridsheet
    pick = [("player_idle", "down", 0), ("player_idle", "right", 0), ("player_idle", "up", 0), ("player_idle", "left", 0),
            ("player_idle", "down", 2), ("player_idle", "right", 2), ("player_run", "right", 2), ("player_dash", "right", 2),
            ("player_katana_fall", "right", 1), ("player_greatsword_cleave", "down-right", 0), ("player_greatsword_cleave", "up-left", 0)]
    out = []
    for name, d, c in pick:
        jp = os.path.join(ROOT, "assets/sprites/player/v3/%s.json" % name)
        m = gridsheet.load_meta(jp)
        im = gridsheet.open_grid(jp)
        r = m["directions"].index(d)
        out.append(im.crop((c * 96, r * 144, c * 96 + 96, r * 144 + 144)))
    return out


def compare(path=None, frames=None, title=""):
    frames = frames or render_all()
    n = len(frames)
    key = Image.open(os.path.join(ROOT, "parts/art/work/gemini/concept_char/hero3_b.jpg")).convert("RGBA")
    kw = n * 96 * 2
    key = key.resize((kw // 2, round(key.height * (kw // 2) / key.width)), Image.LANCZOS)
    olds = old_frames()
    H = key.height + 144 * 2 + 30 + 160 + 144 + 40
    W = n * 192
    sheet = Image.new("RGBA", (W, H), BG)
    sheet.alpha_composite(key, (0, 0))
    dr = ImageDraw.Draw(sheet)
    dr.text((kw // 2 + 20, 20), "P20 model sheet — new rig (top: key art hero3_b)\nrow2: new x2 / row3: new x1 (game 48x72 @zoom~1.7 = x0.85 of this)\nrow4: old P19 sheets x1" + title, fill=(230, 230, 230, 255))
    y0 = key.height + 10
    for i, (label, d, im) in enumerate(frames):
        big = im.resize((192, 288), Image.NEAREST)
        sheet.alpha_composite(big, (i * 192, y0))
        dr.text((i * 192 + 4, y0 + 2), "%s %s" % (label, d), fill=(240, 220, 160, 255))
    y1 = y0 + 288 + 20
    for i, (label, d, im) in enumerate(frames):
        sheet.alpha_composite(im, (i * 192 + 48, y1))
        sm = im.resize((48, 72), Image.NEAREST)
        sheet.alpha_composite(sm.resize((82, 123), Image.NEAREST), (i * 192 + 150 - 41, y1 + 10)) if False else None
    y2 = y1 + 150
    for i, im in enumerate(olds):
        if i < n:
            sheet.alpha_composite(im, (i * 192 + 48, y2))
    sheet.save(path or os.path.join(HERE, "model_sheet_compare.png"))
    return sheet


if __name__ == "__main__":
    compare()
