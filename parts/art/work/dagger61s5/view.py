"""단검 61s5 — 시트 보기 도구(격자 되살림 + 몸 합성 + 확대). 미리보기·비평 전용, assets 에 쓰지 않음."""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, os.path.join(ROOT, "parts/art/work/atlas57"))
import gridsheet  # noqa: E402

SPR = os.path.join(ROOT, "assets", "sprites")
BG = (38, 34, 40, 255)


def load(rel, root=SPR):
    jp = os.path.join(root, rel + ".json")
    return gridsheet.load_meta(jp), gridsheet.open_grid(jp)


def frames(rel, root=SPR):
    m, im = load(rel, root)
    fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
    rows = im.height // fh
    out = [[im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r in range(rows)]
    return m, out


def strip(rel, row=None, scale=2, body=None, root=SPR, label=None, bg=BG):
    """한 시트의 행(들)을 가로로. body = player 시트 rel(같은 프레임 번호로 합성, playerFrameOffset)."""
    m, fr = frames(rel, root)
    rows = range(len(fr)) if row is None else [row]
    fw, fh = m["frameWidth"], m["frameHeight"]
    bm, bfr = (frames(body)[0], frames(body)[1]) if body else (None, None)
    W = fw * m["frames"]
    H = fh * len(list(rows))
    canvas = Image.new("RGBA", (W, H + 12), bg)
    for ri, r in enumerate(rows):
        for c in range(m["frames"]):
            cell = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            if bfr:
                off = m.get("playerFrameOffset", {"x": 0, "y": 0})
                bc = bfr[r][min(c, len(bfr[r]) - 1)]
                cell.alpha_composite(bc, (off["x"], off["y"]))
            cell.alpha_composite(fr[r][c])
            canvas.alpha_composite(cell, (c * fw, 12 + ri * fh))
    ImageDraw.Draw(canvas).text((2, 0), label or rel, fill=(230, 220, 200, 255))
    return canvas.resize((canvas.width * scale, canvas.height * scale), Image.NEAREST)


def stack(imgs, bg=BG, pad=4):
    W = max(i.width for i in imgs)
    H = sum(i.height + pad for i in imgs)
    out = Image.new("RGBA", (W, H), bg)
    y = 0
    for i in imgs:
        out.alpha_composite(i, (0, y))
        y += i.height + pad
    return out


def side(imgs, bg=BG, pad=8):
    W = sum(i.width + pad for i in imgs)
    H = max(i.height for i in imgs)
    out = Image.new("RGBA", (W, H), bg)
    x = 0
    for i in imgs:
        out.alpha_composite(i, (x, 0))
        x += i.width + pad
    return out


if __name__ == "__main__":
    rel = sys.argv[1]
    row = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "all" else None
    sc = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    body = sys.argv[4] if len(sys.argv) > 4 else None
    out = sys.argv[5] if len(sys.argv) > 5 else os.path.join(HERE, "out", "view.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    strip(rel, row, sc, body).save(out)
    print(out)


def tight(rel, row=3, scale=6, root=SPR, body=None, margin=6, label=None, box=None):
    """프레임마다 같은 상자(전 프레임 불투명 합집합)로 잘라 확대해 가로로."""
    m, fr = frames(rel, root)
    cells = fr[row]
    if box is None:
        bb = None
        for c in cells:
            b = c.getbbox()
            if b:
                bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
        bb = bb or (0, 0, 8, 8)
        box = (max(0, bb[0] - margin), max(0, bb[1] - margin), min(m["frameWidth"], bb[2] + margin), min(m["frameHeight"], bb[3] + margin))
    bfr = frames(body)[1] if body else None
    off = m.get("playerFrameOffset", {"x": 0, "y": 0})
    w, h = box[2] - box[0], box[3] - box[1]
    out = Image.new("RGBA", ((w + 2) * len(cells), h + 10), BG)
    for i, c in enumerate(cells):
        cell = Image.new("RGBA", (m["frameWidth"], m["frameHeight"]), (0, 0, 0, 0))
        if bfr:
            cell.alpha_composite(bfr[row][min(i, len(bfr[row]) - 1)], (off["x"], off["y"]))
        cell.alpha_composite(c)
        out.alpha_composite(cell.crop(box), (i * (w + 2), 10))
    try:
        sys.path.insert(0, os.path.join(ROOT, "parts/art/work/awaken60"))
        import kit60
        fnt = kit60.font(9)
    except Exception:
        fnt = None
    ImageDraw.Draw(out).text((1, 0), label or rel.split("/")[-1], fill=(230, 220, 200, 255), font=fnt)
    return out.resize((out.width * scale, out.height * scale), Image.NEAREST)


def zoom_grip(rel, frames_list, root, body=None, half=30, scale=8, label=None):
    """[(row, col)] 칸을 쥔 곳 중심 (2·half)² 로 잘라 확대(몸 합성)."""
    m, fr = frames(rel, root)
    gm = m.get("gripAnchors")
    bfr = frames(body)[1] if body else None
    off = m.get("playerFrameOffset", {"x": 0, "y": 0})
    out = []
    for r, c in frames_list:
        cell = Image.new("RGBA", (m["frameWidth"], m["frameHeight"]), BG)
        if bfr:
            cell.alpha_composite(bfr[r][c], (off["x"], off["y"]))
        cell.alpha_composite(fr[r][c])
        d = m["directions"][r]
        g = gm[d][c] if gm else (m["frameWidth"] / 2, m["frameHeight"] / 2)
        dx = m.get("pivotDelta", {"x": 0})["x"] if "pivotDelta" in m else 0
        dy = m.get("pivotDelta", {"y": 0})["y"] if "pivotDelta" in m else 0
        gx, gy = int(g[0]) + dx, int(g[1]) + dy
        out.append(cell.crop((gx - half, gy - half, gx + half, gy + half)).resize((2 * half * scale, 2 * half * scale), Image.NEAREST))
    return side(out, pad=6)
