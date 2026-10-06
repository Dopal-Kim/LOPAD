"""미리보기: 1층 연회장 바닥(어둡게) 위에 시트 칸을 펼침. 큰 판 = 2배(디테일), 오른쪽 작은 판 = 실제 화면 배율(1920 렌더에서 도트 1:1)."""
import os

from PIL import Image, ImageDraw, ImageEnhance

import tk

BG = (27, 28, 32, 255)
_FLOOR = None


def floor_bg(w, h):
    global _FLOOR
    if _FLOOR is None:
        t = Image.open(os.path.join(tk.ROOT, "assets/tiles/v2/stage1_hall.png")).convert("RGBA")
        tiles = [t.crop((i * 64, 0, i * 64 + 64, 64)) for i in range(4)]
        big = Image.new("RGBA", (1024, 1024))
        for y in range(16):
            for x in range(16):
                big.paste(tiles[(x * 7 + y * 3) % 4], (x * 64, y * 64))
        _FLOOR = ImageEnhance.Brightness(big).enhance(0.55)
    out = Image.new("RGBA", (w, h))
    for y in range(0, h, 1024):
        for x in range(0, w, 1024):
            out.paste(_FLOOR, (x, y))
    return out


def strip(name, rows, meta, k=2):
    fw, fh = rows[0][0].size
    row = rows[0]
    gap = 6
    lab = 30
    W = len(row) * (fw * k + gap) + gap
    rr = len(rows)
    H = lab + rr * (fh * k + gap) + gap
    img = Image.new("RGBA", (max(W, 520), H), (38, 39, 44, 255))
    d = ImageDraw.Draw(img)
    info = "%s  %dx%d  %s  %s%s" % (name, fw, fh, meta["frameDurationsMs"], meta["anchor"],
                                     "  rot" if meta.get("rotate") is True else "")
    d.text((6, 4), info, fill=(225, 225, 220))
    d.text((6, 16), "glow %s  loop %s  colors %s" % (meta["glowFrames"], meta.get("loopRange", meta["loop"]), meta.get("colors")),
           fill=(150, 150, 150))
    for r, rw in enumerate(rows):
        for i, f in enumerate(rw):
            bg = floor_bg(fw, fh)
            bg.alpha_composite(f)
            dd = ImageDraw.Draw(bg)
            px, py = meta["pivot"]["x"], meta["pivot"]["y"]
            dd.point([(px, py)], fill=(255, 0, 255, 255))
            big = bg.resize((fw * k, fh * k), Image.NEAREST)
            x = gap + i * (fw * k + gap)
            y = lab + r * (fh * k + gap)
            img.paste(big, (x, y))
    return img


def sheet_board(items, path, k=2, maxw=2400):
    strips = [strip(n, r, m, k) for n, r, m in items]
    # 줄바꿈 배치
    lines, cur, cw = [], [], 0
    for s in strips:
        if cur and cw + s.width > maxw:
            lines.append(cur)
            cur, cw = [], 0
        cur.append(s)
        cw += s.width + 8
    if cur:
        lines.append(cur)
    W = max(sum(s.width + 8 for s in l) for l in lines)
    H = sum(max(s.height for s in l) + 8 for l in lines)
    out = Image.new("RGBA", (W, H), BG)
    y = 0
    for l in lines:
        x = 0
        for s in l:
            out.paste(s, (x, y))
            x += s.width + 8
        y += max(s.height for s in l) + 8
    out.save(path)
    return out.size


def dark_board(items, path, bright=0.32, maxw=1900):
    """실제 화면 배율(1920 렌더 = 도트 1:1) · 더 어두운 1층 바닥에서 시트마다 대표 칸 셋(처음·가운데·판정 뒤)."""
    global _FLOOR
    keep = _FLOOR
    _FLOOR = None
    floor_bg(8, 8)
    _FLOOR = ImageEnhance.Brightness(_FLOOR).enhance(bright / 0.55)
    tiles = []
    for name, rows, meta in items:
        row = rows[0]
        n = len(row)
        pick = sorted({0, n // 2, min(n - 1, (meta["glowFrames"] or [0])[-1] + 1)})
        fw, fh = row[0].size
        t = Image.new("RGBA", (fw * len(pick) + 4 * len(pick), fh + 12), (20, 20, 24, 255))
        ImageDraw.Draw(t).text((2, 0), name.replace("trait_", ""), fill=(170, 170, 170))
        for j, i in enumerate(pick):
            bg = floor_bg(fw, fh)
            bg.alpha_composite(row[i])
            t.paste(bg, (j * (fw + 4), 12))
        tiles.append(t)
    lines, cur, cw = [], [], 0
    for t in tiles:
        if cur and cw + t.width > maxw:
            lines.append(cur); cur, cw = [], 0
        cur.append(t); cw += t.width + 6
    if cur:
        lines.append(cur)
    W = max(sum(t.width + 6 for t in l) for l in lines)
    H = sum(max(t.height for t in l) + 6 for l in lines)
    out = Image.new("RGBA", (W, H), (20, 20, 24, 255))
    y = 0
    for l in lines:
        x = 0
        for t in l:
            out.paste(t, (x, y)); x += t.width + 6
        y += max(t.height for t in l) + 6
    out.save(path)
    _FLOOR = keep
    return out.size
