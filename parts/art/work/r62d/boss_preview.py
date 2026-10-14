"""보스 새 도트 미리보기 — 전/후(git HEAD 시트 vs 지금) · 동작 모음 · 어둠 목업(림)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
sys.path.insert(0, os.path.join(WORK, "atlas57"))
import gridsheet  # noqa: E402

REL = "assets/sprites/bosses/v3"
FW, FH = 288, 360


def head_grid(name, rev="HEAD"):
    tmp = tempfile.mkdtemp(prefix="r62d_prev_")
    try:
        jb = subprocess.run(["git", "-C", ROOT, "show", f"{rev}:{REL}/{name}.json"], capture_output=True, check=True).stdout
        jp = os.path.join(tmp, name + ".json")
        open(jp, "wb").write(jb)
        m = json.loads(jb.decode("utf-8"))
        pages = [t["image"] for t in m["textures"]] if "textures" in m else [m["meta"]["image"]]
        for pg in pages:
            open(os.path.join(tmp, pg), "wb").write(
                subprocess.run(["git", "-C", ROOT, "show", f"{rev}:{REL}/{pg}"], capture_output=True, check=True).stdout)
        return gridsheet.open_grid(jp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cur_grid(name):
    return gridsheet.open_grid(os.path.join(ROOT, REL, name + ".json"))


def cell(g, r, c):
    return g.crop((c * FW, r * FH, (c + 1) * FW, (r + 1) * FH))


def board(cells, cols, bg=(46, 44, 50, 255), k=1):
    rows = (len(cells) + cols - 1) // cols
    im = Image.new("RGBA", (cols * FW, rows * FH), bg)
    for i, c in enumerate(cells):
        if c is not None:
            im.alpha_composite(c, ((i % cols) * FW, (i // cols) * FH))
    return im.resize((im.width * k, im.height * k), Image.NEAREST) if k > 1 else im


def build():
    out = []
    # 1) 전/후 — idle 0 네 방향
    try:
        old = head_grid("stage1_idle")
        new = cur_grid("stage1_idle")
        cells = [cell(old, r, 0) for r in range(4)] + [cell(new, r, 0) for r in range(4)]
        p = os.path.join(HERE, "preview_boss_before_after.png")
        board(cells, 4, k=2).convert("RGB").save(p)
        out.append(p)
    except subprocess.CalledProcessError:
        pass
    # 2) 동작 모음(정면 행, 동작마다 대표 칸)
    picks = [("intro", [0, 8, 10, 12]), ("idle", [0, 4]), ("walk", [1, 5]), ("attack", [3, 6, 9]), ("slam", [3, 6]),
             ("stagger_dash", [3, 6]), ("kick", [2, 4]), ("throw", [3, 5]), ("throw_torch", [5, 7]), ("drink", [5, 9]),
             ("drink_break", [1, 5]), ("phase_drink", [6, 12]), ("hurt", [0, 1]), ("fall", [4, 8, 12]), ("death", [3, 8, 13])]
    cells = []
    for act, fr in picks:
        g = cur_grid("stage1_" + act)
        for c in fr:
            cells.append(cell(g, 0, c))
    p = os.path.join(HERE, "preview_boss_actions.png")
    board(cells, 8).convert("RGB").save(p)
    out.append(p)
    # 3) 어둠 목업: 몸을 1/7 로 어둡게 + 림
    g = cur_grid("stage1_idle")
    rim = cur_grid("stage1_idle_rim")
    cells = []
    for r in range(4):
        f = cell(g, r, 0)
        px = f.load()
        for y in range(FH):
            for x in range(FW):
                c = px[x, y]
                if c[3]:
                    px[x, y] = (c[0] // 7, c[1] // 7, c[2] // 7, 255)
        f.alpha_composite(cell(rim, r, 0))
        cells.append(f)
    p = os.path.join(HERE, "preview_boss_dark_rim.png")
    board(cells, 4, bg=(8, 7, 10, 255)).convert("RGB").save(p)
    out.append(p)
    return out
