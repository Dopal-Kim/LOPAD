"""주인공 v3 미리보기 — 이 폴더(parts/art/work/hero_v3/)에만 쓴다.

preview_<act>_x2.png   동작별 전 프레임 2배 (행 = down/up/left/right, 빨간 점 = 피벗, 노란 테 = 판정(impact) 프레임)
preview_<act>_x3.gif   동작별 3배 움직임 (4방향 나란히, 실제 ms)
preview_mock_lit.png   외곽 v2 바닥 위 1배(1920×1080 내부 렌더 기준) 조명 합성 — 대기+칼 · 달리기 · 대쉬 · 연격 판정 · 피격 · 사망 끝
연격·휴대는 몸 + 칼 오버레이를 겹친 모습(128×128 캔버스에서 공통 범위만 잘라 보여 줌).
"""
import os

from PIL import Image, ImageDraw, ImageFont

import hero
import katana3 as K
from v3kit import kit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
FW, FH, PIV = hero.FW, hero.FH, hero.PIV
DIRS = hero.DIRS
BG = (46, 48, 56, 255)

FONT = None
for f in ["/usr/share/fonts/truetype/unifont/unifont.ttf", "/usr/share/fonts/opentype/unifont/unifont.otf"]:
    if os.path.exists(f):
        FONT = ImageFont.truetype(f, 16)
        break
FONT = FONT or ImageFont.load_default()


def label(d, x, y, t):
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        d.text((x + dx, y + dy), t, font=FONT, fill=(0, 0, 0))
    d.text((x, y), t, font=FONT, fill=(235, 236, 237))


def compose(body, weapon=None):
    """몸(64×96) [+ 무기(128×128)] → 128×128 캔버스(몸은 (32,32))."""
    c = Image.new("RGBA", (K.WF, K.WF), (0, 0, 0, 0))
    c.alpha_composite(body, (K.OFF, K.OFF))
    if weapon is not None:
        c.alpha_composite(weapon)
    return c


def union_box(frames_by_dir, margin=2):
    box = None
    for d in DIRS:
        for im in frames_by_dir[d]:
            b = im.getbbox()
            if b:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    x0, y0, x1, y1 = box
    return (max(0, x0 - margin), max(0, y0 - margin), min(K.WF, x1 + margin), min(K.WF, y1 + margin))


def frames_x2(name, frames_by_dir, ms, impact=None, active=(), states=None):
    """frames_by_dir: 128×128 합성 프레임. 전 프레임 2배."""
    k, pad = 2, 6
    box = union_box(frames_by_dir)
    bw, bh = box[2] - box[0], box[3] - box[1]
    n = len(frames_by_dir[DIRS[0]])
    W = 80 + n * (bw * k + pad)
    H = 50 + len(DIRS) * (bh * k + pad)
    out = Image.new("RGBA", (W, H), BG)
    dr = ImageDraw.Draw(out)
    label(dr, 6, 6, "%s · %d프레임 · ms %s" % (name, n, ms))
    for j, d in enumerate(DIRS):
        y = 50 + j * (bh * k + pad)
        label(dr, 6, y + bh * k // 2 - 8, d)
        for i, im in enumerate(frames_by_dir[d]):
            x = 80 + i * (bw * k + pad)
            if j == 0:
                t = str(i) + (" " + states[i] if states else "")
                label(dr, x, 28, t)
            if i in active:
                dr.rectangle((x - 3, y - 3, x + bw * k + 2, y + bh * k + 2), outline=(240, 200, 60, 255), width=2 if i == impact else 1)
            out.alpha_composite(im.crop(box).resize((bw * k, bh * k), Image.NEAREST), (x, y))
            px_, py_ = (PIV[0] + K.OFF - box[0]) * k, (PIV[1] + K.OFF - box[1]) * k
            dr.rectangle((x + px_ - 1, y + py_ - 1, x + px_, y + py_), fill=(220, 60, 60, 255))
    out.save(os.path.join(HERE, "preview_%s_x2.png" % name))


def gif_x3(name, frames_by_dir, ms):
    k = 3
    box = union_box(frames_by_dir, margin=4)
    bw, bh = box[2] - box[0], box[3] - box[1]
    n = len(frames_by_dir[DIRS[0]])
    frames = []
    for i in range(n):
        im = Image.new("RGBA", (bw * 4 * k, bh * k), (34, 36, 42, 255))
        for c, d in enumerate(DIRS):
            im.alpha_composite(frames_by_dir[d][i].crop(box).resize((bw * k, bh * k), Image.NEAREST), (c * bw * k, 0))
        frames.append(im.convert("RGB").quantize(colors=128, dither=Image.Dither.NONE))
    frames[0].save(os.path.join(HERE, "preview_%s_x3.gif" % name), save_all=True, append_images=frames[1:],
                   duration=list(ms), loop=0, disposal=2)


def mock_lit(spots_spec):
    """외곽 v2 albedo 목업(960×540)을 2배로 키운 바닥(1920×1080 내부 렌더 크기) 위에 1배 합성 + 조명.
    spots_spec: [(라벨, 128×128 합성 RGBA, 빛 여부)] — 왼쪽부터."""
    alb = Image.open(os.path.join(ROOT, "parts/art/work/v2_outer/preview_mock_albedo.png")).convert("RGBA")
    crop = alb.crop((300, 338, 600, 473)).resize((600, 270), Image.NEAREST)   # 빈 광장 바닥(다른 캐릭터 없음)
    canvas = crop.copy()
    dr = ImageDraw.Draw(canvas)
    lights = []
    step = 600 // (len(spots_spec) + 1)
    for j, (lab, im, lit) in enumerate(spots_spec):
        x = step * (j + 1) - 64
        y = 210 - 124
        dr.ellipse((x + 64 - 22, y + 120, x + 64 + 22, y + 129), fill=(10, 11, 14, 255))    # 발밑 그림자(목업 — 시스템이 그림)
    for j, (lab, im, lit) in enumerate(spots_spec):
        x = step * (j + 1) - 64
        y = 210 - 124
        canvas.alpha_composite(im, (x, y))
        if lit:
            lights.append({"x": x + 64, "y": y + 84, "color": "#b0611a", "radius": 70, "intensity": 0.45})   # 몸 혼불 빛(임시)
    em = kit.EMISSIVE
    lit_im = kit.light_scene(canvas, lights, scale=2, emissive=em)
    out = Image.new("RGB", (lit_im.width, lit_im.height + 52), (18, 19, 22))
    out.paste(lit_im, (0, 52))
    d = ImageDraw.Draw(out)
    label(d, 4, 4, "1배(1920×1080 내부 렌더) · 외곽 v2 바닥 · 몸 혼불 빛 임시")
    for j, (lab, im, lit) in enumerate(spots_spec):
        label(d, step * (j + 1) - 30, 28, lab)
    out.save(os.path.join(HERE, "preview_mock_lit.png"))
