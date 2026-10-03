"""적 v3 미리보기 — 이 폴더(parts/art/work/enemies_v3/)에만 쓴다.

preview_<id>_<act>_x2.png  전 프레임 2배(행 = down/up/left/right, 빨간 점 = 피벗, 노란 테 = 공격 단계 프레임, 굵은 테 = 타격·발사·돌진 시작)
preview_<id>_<act>_x3.gif  3배 움직임(4방향 나란히, 실제 ms)
preview_mock_lit.png       외곽 v2 바닥 위 1배(1920×1080 내부 렌더 기준) + 주인공 v3 — 크기·어둠 속 실루엣 비교
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(HERE, "..", "hero_v3"))
from v3kit import kit  # noqa: E402
sys.path.insert(0, HERE)

DIRS = ["down", "up", "left", "right"]
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


def union_box(frames_by_dir, W, H, margin=2):
    box = None
    for d in frames_by_dir:
        for im in frames_by_dir[d]:
            b = im.getbbox()
            if b:
                box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    x0, y0, x1, y1 = box
    return (max(0, x0 - margin), max(0, y0 - margin), min(W, x1 + margin), min(H, y1 + margin))


def frames_x2(path, title, frames_by_dir, ms, piv, marks=(), strong=(), states=None, k=2):
    W, H = frames_by_dir["down"][0].size
    pad = 6
    box = union_box(frames_by_dir, W, H)
    bw, bh = box[2] - box[0], box[3] - box[1]
    n = len(frames_by_dir["down"])
    out = Image.new("RGBA", (80 + n * (bw * k + pad), 50 + 4 * (bh * k + pad)), BG)
    dr = ImageDraw.Draw(out)
    label(dr, 6, 6, "%s · %d프레임 · ms %s" % (title, n, list(ms)))
    for j, d in enumerate(DIRS):
        y = 50 + j * (bh * k + pad)
        label(dr, 6, y + bh * k // 2 - 8, d)
        for i, im in enumerate(frames_by_dir[d]):
            x = 80 + i * (bw * k + pad)
            if j == 0:
                label(dr, x, 28, str(i) + (" " + states[i] if states and states[i] else ""))
            if i in marks:
                dr.rectangle((x - 3, y - 3, x + bw * k + 2, y + bh * k + 2), outline=(240, 200, 60, 255), width=2 if i in strong else 1)
            out.alpha_composite(im.crop(box).resize((bw * k, bh * k), Image.NEAREST), (x, y))
            px_, py_ = (piv[0] - box[0]) * k, (piv[1] - box[1]) * k
            dr.rectangle((x + px_ - 1, y + py_ - 1, x + px_, y + py_), fill=(220, 60, 60, 255))
    out.save(path)


def gif_x3(path, frames_by_dir, ms, k=3):
    W, H = frames_by_dir["down"][0].size
    box = union_box(frames_by_dir, W, H, margin=4)
    bw, bh = box[2] - box[0], box[3] - box[1]
    n = len(frames_by_dir["down"])
    frames = []
    for i in range(n):
        im = Image.new("RGBA", (bw * 4 * k, bh * k), (34, 36, 42, 255))
        for c, d in enumerate(DIRS):
            im.alpha_composite(frames_by_dir[d][i].crop(box).resize((bw * k, bh * k), Image.NEAREST), (c * bw * k, 0))
        frames.append(im.convert("RGB").quantize(colors=160, dither=Image.Dither.NONE))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=list(ms), loop=0, disposal=2)


def mock_lit(spots, path, title):
    """외곽 v2 albedo 목업 바닥(2배 = 1920 내부 렌더) 위에 1배 합성 + 조명(주인공 v3 미리보기와 같은 방식).
    spots: [(라벨, RGBA, 피벗, 빛 여부)]"""
    alb = Image.open(os.path.join(ROOT, "parts/art/work/v2_outer/preview_mock_albedo.png")).convert("RGBA")
    strip = alb.crop((300, 338, 600, 473)).resize((600, 270), Image.NEAREST)
    canvas = Image.new("RGBA", (1200, 270))
    canvas.paste(strip, (0, 0))
    canvas.paste(strip.transpose(Image.FLIP_LEFT_RIGHT), (600, 0))
    dr = ImageDraw.Draw(canvas)
    lights = []
    step = 1200 // (len(spots) + 1)
    gy = 236
    for j, (lab, im, piv, lit) in enumerate(spots):
        cx = step * (j + 1)
        bb = im.getbbox()
        rw = max(14, (bb[2] - bb[0]) // 3) if bb else 14
        dr.ellipse((cx - rw, gy - 5, cx + rw, gy + 5), fill=(10, 11, 14, 255))
    for j, (lab, im, piv, lit) in enumerate(spots):
        cx = step * (j + 1)
        canvas.alpha_composite(im, (cx - piv[0], gy - piv[1]))
        if lit:
            lights.append({"x": cx, "y": gy - 60, "color": "#b0611a", "radius": 90, "intensity": 0.45})
    lit_im = kit.light_scene(canvas, lights, scale=2, emissive=kit.EMISSIVE)
    out = Image.new("RGB", (lit_im.width, lit_im.height + 52), (18, 19, 22))
    out.paste(lit_im, (0, 52))
    d = ImageDraw.Draw(out)
    label(d, 4, 4, title)
    for j, (lab, im, piv, lit) in enumerate(spots):
        label(d, step * (j + 1) - 40, 28, lab)
    out.save(path)
