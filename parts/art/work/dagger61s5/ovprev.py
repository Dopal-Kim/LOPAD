"""오버레이 미리보기: 무기 → a1 → a2 → glow(tint) 합성, 쥔 곳 중심 확대 — 전/후."""
import sys
from PIL import Image
import view, d5

TINT = {"twin": (192, 226, 255), "gale": (172, 255, 150), "hyakki": (100, 240, 220)}


def tint(im, rgb):
    out = im.copy(); p = out.load()
    for y in range(im.height):
        for x in range(im.width):
            c = p[x, y]
            if c[3]:
                p[x, y] = (c[0] * rgb[0] // 255, c[1] * rgb[1] // 255, c[2] * rgb[2] // 255, 255)
    return out


def comp(root, sheet, b, r, c, stage=2, half=34, sc=5, body=None):
    act = sheet.split("_", 1)[1]
    m, fr = view.frames("weapons/v3/" + sheet, root)
    cell = Image.new("RGBA", (m["frameWidth"] + 64, m["frameHeight"] + 64), view.BG)
    if body:
        bf = view.frames(body)[1]
        cell.alpha_composite(bf[r][c], (80, 80))
    cell.alpha_composite(fr[r][c], (32, 32))
    if b == "awaken":
        cell.alpha_composite(view.frames("weapons/v3/%s_awaken" % sheet, root)[1][r][c])
    else:
        cell.alpha_composite(view.frames("weapons/v4/dagger_%s_a1_%s" % (b, act), root)[1][r][c])
        if stage >= 2:
            cell.alpha_composite(view.frames("weapons/v4/dagger_%s_a2_%s" % (b, act), root)[1][r][c])
            cell.alpha_composite(tint(view.frames("weapons/v4/dagger_%s_a2_glow_%s" % (b, act), root)[1][r][c], TINT[b]))
    g = m["gripAnchors"][m["directions"][r]][c]
    gx, gy = int(g[0]) + 32, int(g[1]) + 32
    return cell.crop((gx - half, gy - half, gx + half, gy + half)).resize((2 * half * sc, 2 * half * sc), Image.NEAREST)


if __name__ == "__main__":
    sheet = sys.argv[1]
    body = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None
    cells = [tuple(map(int, x.split(","))) for x in sys.argv[3].split()] if len(sys.argv) > 3 else [(3, 2), (0, 1), (2, 3)]
    out = []
    for b in ("awaken", "twin", "gale", "hyakki"):
        for root in (d5.before_root(), d5.STAGE):
            out.append(view.side([comp(root, sheet, b, r, c, body=body) for r, c in cells], pad=4))
    view.stack(out).save("out/ov.png")
