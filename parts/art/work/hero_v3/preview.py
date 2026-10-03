"""주인공 v3 미리보기 — 이 폴더(parts/art/work/hero_v3/)에만 쓴다.

preview_<act>_x2.png   동작별 전 프레임 2배 (행 = down/up/left/right, 빨간 점 = 피벗, 노란 테 = 판정(impact) 프레임)
preview_<act>_x3.gif   동작별 3배 움직임 (4방향 나란히, 실제 ms)
preview_mock_lit.png   외곽 v2 바닥 위 1배(1920×1080 내부 렌더 기준) 조명 합성 — 64×96 이전 판 · 결사병 v2 · 96×144 새 판 동작들
preview_scar_x3.png    등 상흔 기준점 확인(임시 상흔)
연격·휴대는 몸 + 칼 오버레이를 겹친 모습(192×192 캔버스에서 공통 범위만 잘라 보여 줌).
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
    """몸(96×144) [+ 무기(192×192)] → 192×192 캔버스(몸은 (48,48))."""
    c = Image.new("RGBA", (K.WF, K.WF), (0, 0, 0, 0))
    c.alpha_composite(body, (K.OFF, K.OFF))
    if weapon is not None:
        c.alpha_composite(weapon)
    return c


def union_box(frames_by_dir, margin=2):
    box = None
    for d in [d for d in DIRS if d in frames_by_dir]:
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
    dirs = [d for d in DIRS if d in frames_by_dir]
    n = len(frames_by_dir[dirs[0]])
    W = 80 + n * (bw * k + pad)
    H = 50 + len(dirs) * (bh * k + pad)
    out = Image.new("RGBA", (W, H), BG)
    dr = ImageDraw.Draw(out)
    label(dr, 6, 6, "%s · %d프레임 · ms %s" % (name, n, ms))
    for j, d in enumerate(dirs):
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
    dirs = [d for d in DIRS if d in frames_by_dir]
    n = len(frames_by_dir[dirs[0]])
    frames = []
    for i in range(n):
        im = Image.new("RGBA", (bw * len(dirs) * k, bh * k), (34, 36, 42, 255))
        for c, d in enumerate(dirs):
            im.alpha_composite(frames_by_dir[d][i].crop(box).resize((bw * k, bh * k), Image.NEAREST), (c * bw * k, 0))
        frames.append(im.convert("RGB").quantize(colors=128, dither=Image.Dither.NONE))
    frames[0].save(os.path.join(HERE, "preview_%s_x3.gif" % name), save_all=True, append_images=frames[1:],
                   duration=list(ms), loop=0, disposal=2)


def mock_lit(spots_spec, name="preview_mock_lit.png", title="1배(1920×1080 내부 렌더) · 외곽 v2 바닥 · 몸 혼불 빛 임시"):
    """외곽 v2 albedo 목업(960×540)을 2배로 키운 바닥(1920×1080 내부 렌더 크기) 위에 1배 합성 + 조명.
    spots_spec: [(라벨, RGBA, 발 피벗 (x, y) — 그 그림 안 좌표, 빛 여부)] — 왼쪽부터."""
    alb = Image.open(os.path.join(ROOT, "parts/art/work/v2_outer/preview_mock_albedo.png")).convert("RGBA")
    strip = alb.crop((300, 338, 600, 473)).resize((600, 270), Image.NEAREST)   # 빈 광장 바닥(다른 캐릭터 없음) — 2배 = 1920 내부 렌더
    canvas = Image.new("RGBA", (1200, 270))
    canvas.paste(strip, (0, 0))
    canvas.paste(strip.transpose(Image.FLIP_LEFT_RIGHT), (600, 0))
    dr = ImageDraw.Draw(canvas)
    lights = []
    step = 1200 // (len(spots_spec) + 1)
    gy = 240
    for j, (lab, im, piv, lit) in enumerate(spots_spec):
        cx = step * (j + 1)
        rw = max(14, im.getbbox()[2] - im.getbbox()[0]) // 3 if im.getbbox() else 14
        dr.ellipse((cx - rw, gy - 5, cx + rw, gy + 5), fill=(10, 11, 14, 255))    # 발밑 그림자(목업 — 시스템이 그림)
    for j, (lab, im, piv, lit) in enumerate(spots_spec):
        cx = step * (j + 1)
        canvas.alpha_composite(im, (cx - piv[0], gy - piv[1]))
        if lit:
            lights.append({"x": cx, "y": gy - 60, "color": "#b0611a", "radius": 90, "intensity": 0.45})   # 몸 혼불 빛(임시)
    em = kit.EMISSIVE
    lit_im = kit.light_scene(canvas, lights, scale=2, emissive=em)
    out = Image.new("RGB", (lit_im.width, lit_im.height + 52), (18, 19, 22))
    out.paste(lit_im, (0, 52))
    d = ImageDraw.Draw(out)
    label(d, 4, 4, title)
    for j, (lab, im, piv, lit) in enumerate(spots_spec):
        label(d, step * (j + 1) - 40, 28, lab)
    out.save(os.path.join(HERE, name))


def scar_preview(spots, name="preview_scar_x3.png"):
    """등 상흔 기준점 확인: 128 합성 프레임 위에 scarAnchor 사각형(청록 테) + 임시 상흔(아무 획 — 호박 균열)을 겹친다. 3배.
    spots: [(라벨, 192×192 합성 RGBA, scarAnchor dict)]"""
    import math
    k = 3
    cells = []
    for lab, im, sc in spots:
        c = im.copy()
        if sc["visible"]:
            px = c.load()
            cx, cy = sc["x"] + K.OFF, sc["y"] + K.OFF
            ca, sa = math.cos(math.radians(sc["rot"])), math.sin(math.radians(sc["rot"]))

            def T(u, v):
                x, y = u * sc["w"] / 2, v * sc["h"] / 2
                return (cx + x * ca - y * sa, cy + x * sa + y * ca)
            stroke = [(-0.75, -0.7), (-0.2, -0.25), (-0.45, 0.05), (0.15, 0.25), (-0.05, 0.5), (0.7, 0.8)]   # 임시 획(플레이어가 그은 모양 대신)
            from v3kit import raster_path
            pts = raster_path([T(u, v) for u, v in stroke])
            for x, y in pts:
                for dx, dy, col in ((1, 0, kit.A[21]), (0, 1, kit.A[21]), (0, 0, kit.A[25])):
                    if 0 <= x + dx < c.width and 0 <= y + dy < c.height and px[x + dx, y + dy][3]:
                        px[x + dx, y + dy] = col if (dx, dy) == (0, 0) else (px[x + dx, y + dy] if px[x + dx, y + dy][:3] == kit.A[25][:3] else col)
        cells.append((lab, c, sc))
    box = union_box({d: [c for _, c, _ in cells] for d in DIRS}, margin=4)
    bw, bh = box[2] - box[0], box[3] - box[1]
    per = 7
    nrow = (len(cells) + per - 1) // per
    rh = bh * k + 36
    out = Image.new("RGBA", (per * (bw * k + 8) + 8, nrow * rh + 30), BG)
    dr = ImageDraw.Draw(out)
    label(dr, 6, 4, "등 상흔 기준점(scarAnchor) — 청록 테 = 사각형, 호박 선 = 임시 상흔. down 은 visible:false")
    for i, (lab, c, sc) in enumerate(cells):
        x = 8 + (i % per) * (bw * k + 8)
        y0 = 30 + (i // per) * rh
        out.alpha_composite(c.crop(box).resize((bw * k, bh * k), Image.NEAREST), (x, y0 + 26))
        if sc["visible"]:
            import math
            ca, sa = math.cos(math.radians(sc["rot"])), math.sin(math.radians(sc["rot"]))
            cx, cy = (sc["x"] + K.OFF - box[0]) * k, (sc["y"] + K.OFF - box[1]) * k
            corners = []
            for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1)):
                xx, yy = u * sc["w"] / 2 * k, v * sc["h"] / 2 * k
                corners.append((x + cx + xx * ca - yy * sa, y0 + 26 + cy + xx * sa + yy * ca))
            dr.line(corners, fill=(80, 220, 220, 255), width=1)
        label(dr, x, y0 + 4, lab)
    out.save(os.path.join(HERE, name))
