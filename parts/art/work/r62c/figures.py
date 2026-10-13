"""작은 판 덧그림 — '사연' 카드의 인물(NPC 시트 몸을 그림 결의 실루엣으로).

NPC 시트(structures/v3/npc_*) idle 아래 0 프레임을 알파 마스크로 쓰고, 명도는 먹~재 회색 사이로 눌러(그림의 어둠 결),
빛 쪽 가장자리에 호박 테 1~2칸, 2배 굵은 도트(그림의 덩어리 크기와 맞춤)로 얹는다.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

from c62 import AMB, GRAY, SPR, WORK, lerp

sys.path.insert(0, os.path.join(WORK, "atlas57"))
import gridsheet  # noqa: E402

NPC = {"conscript": (96, 144), "merchant": (96, 144), "brewer": (160, 192)}


def npc_frame(name, row=0, col=0):
    fw, fh = NPC[name]
    grid = gridsheet.open_grid(os.path.join(SPR, "structures", "v3", f"npc_{name}.json"))
    f = grid.crop((col * fw, row * fh, col * fw + fw, row * fh + fh))
    return f.crop(f.getbbox())


def silhouette(spr, height, light_from="left", chunk=2, value=(0.0, 0.55), rim=True, keep_warm=True):
    """spr(RGBA) → 그림 결 실루엣. height = 결과 높이(px), chunk = 도트 크기."""
    w0, h0 = spr.size
    hh = max(4, round(height / chunk))
    ww = max(2, round(w0 * hh / h0))
    s = spr.resize((ww, hh), Image.NEAREST)
    px = s.load()
    out = Image.new("RGBA", (ww, hh), (0, 0, 0, 0))
    po = out.load()
    lo, hi = value
    for y in range(hh):
        for x in range(ww):
            r, g, b, a = px[x, y]
            if a < 100:
                continue
            L = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            t = lo + (hi - lo) * L
            c = lerp(GRAY[1], GRAY[6], t)
            warm = keep_warm and r > 150 and r - b > 70        # 호박 소품(등·잔) 은 빛으로 남긴다
            if warm:
                c = AMB[6] if L > 0.55 else AMB[4]
            po[x, y] = c + (255,)
    if rim:
        dx = -1 if light_from == "left" else 1
        src = out.copy().load()
        for y in range(hh):
            for x in range(ww):
                if src[x, y][3] == 0:
                    continue
                nx = x + dx
                edge = nx < 0 or nx >= ww or src[nx, y][3] == 0
                up = y == 0 or src[x, y - 1][3] == 0
                if edge:
                    po[x, y] = AMB[7] + (255,)
                    nx2 = x - dx
                    if 0 <= nx2 < ww and src[nx2, y][3] and not (nx2 + dx < 0):
                        po[nx2, y] = lerp(po[nx2, y][:3], AMB[4], 0.55) + (255,)
                elif up:
                    po[x, y] = lerp(po[x, y][:3], AMB[5], 0.45) + (255,)
    return out.resize((ww * chunk, hh * chunk), Image.NEAREST)


def place(im, fig, foot_x, foot_y, shadow=True):
    """fig 를 발(아래 가운데)이 (foot_x, foot_y) 에 오게. 바닥 그늘 타원."""
    im = im.convert("RGBA")
    w, h = fig.size
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(sh)
        d.ellipse((foot_x - w * 0.55, foot_y - 5, foot_x + w * 0.55, foot_y + 4), fill=GRAY[0] + (150,))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(2)))
    im.alpha_composite(fig, (int(round(foot_x - w / 2)), int(round(foot_y - h))))
    return im


def hooded_sitter(facing="left", lantern=True):
    """손으로 그린 '사연' 인물: 두건 쓴 사람이 고개 숙이고 앉아 등을 든 실루엣(1칸 = 2px). 반환 RGBA(2배), 발 기준 = 아래 가운데.

    facing = 등이 놓인 쪽(빛 쪽). 그림은 왼쪽 보기로 그리고 'right' 면 좌우 반전.
    """
    W, H = 34, 40
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    # 두건(머리 숙여 앞으로) · 어깨 · 망토 자락 · 무릎
    d.ellipse((9, 2, 20, 13), fill=255)                                               # 두건 머리(앞으로 숙임)
    d.polygon([(15, 2), (21, 0), (24, 6), (22, 11)], fill=255)                        # 두건 뾰족한 뒤
    d.polygon([(14, 11), (22, 8), (27, 12), (30, 22), (31, 34), (30, 39), (8, 39), (6, 33), (9, 24), (12, 16)], fill=255)  # 굽은 등·망토
    d.polygon([(3, 29), (10, 26), (14, 31), (12, 37), (2, 38), (1, 33)], fill=255)    # 앞으로 모은 무릎
    d.polygon([(10, 15), (15, 15), (13, 23), (8, 25), (7, 21)], fill=255)             # 등 든 팔
    face = [(9, 7), (13, 6), (15, 10), (12, 13), (9, 12)]                             # 두건 속 얼굴 그늘
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    po = out.load()
    pm = m.load()
    for y in range(H):
        for x in range(W):
            if not pm[x, y]:
                continue
            # 빛(왼쪽 아래 등)에서 멀수록 어둡게
            t = max(0.0, min(1.0, 1 - ((x - 5) ** 2 + (y - 22) ** 2) ** 0.5 / 24))
            c = lerp(GRAY[1], GRAY[6], t ** 1.3)
            po[x, y] = c + (255,)
    # 접힘 선(먹)
    dd = ImageDraw.Draw(out)
    for line in [((19, 14), (22, 31)), ((24, 14), (27, 34)), ((15, 27), (17, 38)), ((16, 4), (19, 9))]:
        dd.line(line, fill=GRAY[1] + (255,))
    dd.polygon(face, fill=GRAY[0] + (255,))
    dd.line([(10, 6), (13, 5)], fill=GRAY[6] + (255,))                                # 두건 테 위 빛
    # 빛 쪽 테(호박) — 바깥 테두리 중 왼쪽 면
    src = out.copy().load()
    for y in range(H):
        for x in range(W):
            if src[x, y][3] and (x == 0 or src[x - 1, y][3] == 0):
                near = max(0.0, 1 - abs(y - 22) / 20)
                if near > 0.15:
                    po[x, y] = lerp(GRAY[5], AMB[7], near) + (255,)
                    if x + 1 < W and src[x + 1, y][3]:
                        po[x + 1, y] = lerp(src[x + 1, y][:3], AMB[3], near * 0.6) + (255,)
    if lantern:
        # 손에 든 작은 등: 고리·몸·불
        dd.line([(7, 19), (7, 21)], fill=GRAY[2] + (255,))
        dd.rectangle((5, 22, 9, 26), fill=GRAY[2] + (255,))
        dd.rectangle((6, 23, 8, 25), fill=AMB[9] + (255,))
        po[7, 24] = AMB[11] + (255,)
        dd.line([(5, 27), (9, 27)], fill=GRAY[2] + (255,))
    big = out.resize((W * 2, H * 2), Image.NEAREST)
    if facing == "right":
        big = big.transpose(Image.FLIP_LEFT_RIGHT)
    lamp = (7 * 2 + 1, 24 * 2 + 1) if facing == "left" else ((W - 8) * 2 + 1, 24 * 2 + 1)
    return big, lamp


def lamp_glow(im, x, y, rad=26, color=None, amount=0.55):
    """등 빛 번짐(screen)."""
    from PIL import ImageChops
    color = color or AMB[5]
    g = Image.new("RGB", im.size, (0, 0, 0))
    d = ImageDraw.Draw(g)
    for i in range(16, 0, -1):
        t = i / 16
        a = amount * (1 - t) ** 1.8
        r = rad * t
        d.ellipse((x - r, y - r, x + r, y + r), fill=tuple(int(c * a) for c in color))
    g = g.filter(ImageFilter.GaussianBlur(rad * 0.15))
    rgb = ImageChops.screen(im.convert("RGB"), g)
    return rgb.convert("RGBA")
