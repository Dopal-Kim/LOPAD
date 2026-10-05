"""61라운드 미리보기 — 기존 적·주인공과 나란히(크기·실루엣) + 어둠 조명 목업 + 엘리트 외곽선. 긴 변 8000 이하.

python3 parts/art/work/enemies61/preview61.py
→ preview_lineup.png(3배, 방향 4줄) · preview_mock_lit.png(eprev.mock_lit, 1배 2배 확대 조명) · preview_attack_strip.png(공격 핵심 프레임 4배)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
import kit61  # noqa: F401
import eprev  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "../atlas57"))
import gridsheet  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "../bundle2"))
import elite  # noqa: E402
from PIL import Image  # noqa: E402

SPR = os.path.normpath(os.path.join(HERE, "../../../../assets/sprites"))


def frame(cat, name, row, col):
    jp = os.path.join(SPR, cat, "v3", name + ".json")
    g, m = gridsheet.open_grid(jp), gridsheet.load_meta(jp)
    fw, fh = m["frameWidth"], m["frameHeight"]
    return g.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh)), (m["pivot"]["x"], m["pivot"]["y"])


def lineup(path, k=3):
    cast = [("player", "player_idle"), ("enemies", "dummy_idle"), ("enemies", "archer_idle"), ("enemies", "charger_idle"),
            ("enemies", "peddler_idle"), ("enemies", "porter_idle"), ("enemies", "peddler_idle_elite"), ("enemies", "porter_idle_elite")]
    rows = []
    for r in range(4):
        row = []
        for i, (cat, n) in enumerate(cast):
            im, piv = frame(cat, n, r, 0)
            if n.endswith("_elite"):
                base, _ = frame(cat, n[:-6], r, 0)
                im = im.copy()
                im.alpha_composite(base)
            row.append((im, piv))
        rows.append(row)
    colw = 170
    H = 210
    out = Image.new("RGBA", (colw * len(cast), H * 4), (40, 42, 50, 255))
    for r, row in enumerate(rows):
        for i, (im, piv) in enumerate(row):
            out.alpha_composite(im, (i * colw + colw // 2 - piv[0], r * H + 190 - piv[1]))
    out = out.resize((out.width * k, out.height * k), Image.NEAREST)
    out.convert("RGB").save(path)
    return out.size


def mock(path):
    spots = []
    for cat, n, lit in (("player", "player_idle", True), ("enemies", "dummy_idle", False), ("enemies", "peddler_idle", False),
                        ("enemies", "peddler_attack", False), ("enemies", "porter_idle", False), ("enemies", "porter_attack", False)):
        col = 3 if n == "peddler_attack" else (3 if n == "porter_attack" else 0)
        im, piv = frame(cat, n, 0 if "attack" not in n else 3, col)
        spots.append((n, im, piv, lit))
    eprev.mock_lit(spots, path, "61 신규 적 — 어둠 속 1배(2배 확대): 행상 등·심지 불이 먼저, 짐꾼은 술통 실루엣")


def attack_strip(path, k=4):
    items = []
    for n, cols in (("peddler_attack", (0, 1, 3, 4, 5, 6, 8)), ("porter_attack", (0, 3, 4, 5, 6, 7, 8, 9))):
        for r in (0, 3):
            for c in cols:
                items.append(frame("enemies", n, r, c))
    W = sum(im.width for im, _ in items[:15]) + 8 * 15
    out = Image.new("RGBA", (1200, 4 * 200), (40, 42, 50, 255))
    x = y = 0
    rowh = 0
    for im, piv in items:
        bb = im.getbbox()
        cr = im.crop((max(0, bb[0] - 2), 0, min(im.width, bb[2] + 2), im.height))
        if x + cr.width > 1200:
            x, y = 0, y + rowh + 6
            rowh = 0
        out.alpha_composite(cr, (x, y))
        x += cr.width + 6
        rowh = max(rowh, cr.height)
    out = out.crop((0, 0, 1200, y + rowh + 4))
    k = min(k, 8000 // max(out.size))
    out.resize((out.width * k, out.height * k), Image.NEAREST).convert("RGB").save(path)
    return out.size


if __name__ == "__main__":
    print("lineup", lineup(os.path.join(HERE, "preview_lineup.png")))
    mock(os.path.join(HERE, "preview_mock_lit.png"))
    print("attack", attack_strip(os.path.join(HERE, "preview_attack_strip.png")))
