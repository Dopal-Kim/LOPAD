"""61 단계 5 칼 전/후 비교 미리보기 → parts/art/work/katana61s5/preview_*.png (긴 변 8000 이하).
전 = git SRC_REV(2aa9fe6) 사본(out/before, 처음 한 번 git 에서 꺼냄), 후 = assets."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pv  # noqa: E402
import kcommon as C  # noqa: E402
from PIL import Image  # noqa: E402

BEFORE = os.path.join(HERE, "out", "before")
AFTER = C.SPR
DIRS = ["down", "up", "left", "right"]


def ensure_before(rels):
    for rel in rels:
        jp = os.path.join(BEFORE, rel + ".json")
        if os.path.exists(jp) or os.path.exists(os.path.join(BEFORE, rel + ".png")):
            continue
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        if rel.startswith("looks/"):
            b = subprocess.run(["git", "-C", C.ROOT, "show", "%s:assets/sprites/%s.png" % (C.SRC_REV, rel)], capture_output=True, check=True).stdout
            open(os.path.join(BEFORE, rel + ".png"), "wb").write(b)
            continue
        raw = subprocess.run(["git", "-C", C.ROOT, "show", "%s:assets/sprites/%s.json" % (C.SRC_REV, rel)], capture_output=True, check=True).stdout
        open(jp, "wb").write(raw)
        m = json.loads(raw)
        pages = [t["image"] for t in m.get("textures", [])] or [m.get("meta", {}).get("image", os.path.basename(rel) + ".png")]
        for pg in pages:
            b = subprocess.run(["git", "-C", C.ROOT, "show", "%s:assets/sprites/%s/%s" % (C.SRC_REV, os.path.dirname(rel), pg)], capture_output=True, check=True).stdout
            open(os.path.join(os.path.dirname(jp), pg), "wb").write(b)


def starts(ms):
    o, t = [], 0
    for m in ms:
        o.append(t)
        t += m
    return o


def compose(root, body, layers, fx, row, col, size=(360, 320), anchor=(180, 250), bg=pv.BG):
    """몸 + 무기 층 + (fx, fx 칸) — 모두 주인공 피벗 기준. fx = (rel, fx_col) or None."""
    cv = Image.new("RGBA", size, bg + (255,))
    b, bm = pv.frame(AFTER, body, row, col)
    bp = bm.get("pivot", {"x": 48, "y": 138})
    cv.alpha_composite(b, (anchor[0] - bp["x"], anchor[1] - bp["y"]))
    for rel in layers:
        try:
            w, wm = pv.frame(root, rel, row, col)
        except Exception:
            continue
        p = wm.get("pivot", {"x": 96, "y": 186})
        cv.alpha_composite(w, (anchor[0] - p["x"], anchor[1] - p["y"]))
    if fx:
        rel, fc = fx
        f, fm = pv.frame(root, rel, row if len(fm_dirs(root, rel)) > 1 else 0, fc)
        p = fm.get("pivot")
        cv.alpha_composite(f, (anchor[0] - p["x"], anchor[1] - p["y"]))
    return cv


def fm_dirs(root, rel):
    return pv.sheet(root, rel)[0]["directions"]


def fx_col_at(root, body, fxrel, col):
    """몸 칸 col 시작 시각에 보이는 fx 칸(spawnAtMs 기준). 없으면 None."""
    bm = pv.sheet(AFTER, body)[0]
    fm = pv.sheet(root, fxrel)[0]
    t = starts(bm["frameDurationsMs"])[col] + 1
    sp = fm.get("spawnAtMs")
    if sp is None:
        return None
    dt = t - sp
    if dt < 0:
        return None
    st = starts(fm["frameDurationsMs"])
    for i in range(len(st) - 1, -1, -1):
        if dt >= st[i]:
            return i if dt < st[i] + fm["frameDurationsMs"][i] else None
    return None


def save(im, name):
    p = os.path.join(HERE, name)
    pv.fit(im, 7900).save(p)
    return p


def weapons_preview():
    items = [("katana_carry_idle", "player/v3/player_idle", 0), ("katana_carry_drawn_idle", "player/v3/player_idle", 0),
             ("katana_rise", None, 3), ("katana_fall", None, 2), ("katana_thrust", None, 4), ("katana_iai", None, 8),
             ("katana_issen_dash", None, 4), ("katana_spin", None, 2), ("katana_guardbreak", None, 9), ("katana_counter", None, 3),
             ("katana_special", None, 4), ("katana_sheathe", None, 3)]
    rels = []
    for s, b, c in items:
        rels += ["weapons/v3/" + s]
    ensure_before(rels)
    rows = []
    titles = []
    for row in (3, 0):
        for root, tag in ((BEFORE, "전(61 단계 4)"), (AFTER, "후(61 단계 5 은선)")):
            cells = []
            for s, b, c in items:
                body = b or "player/v3/player_" + s
                cells.append(pv.scale(compose(root, body, ["weapons/v3/" + s], None, row, c, size=(220, 220), anchor=(110, 200)), 3))
            rows.append(pv.grid(cells, len(cells), pad=4))
            titles.append("%s · %s 행 — %s" % (tag, DIRS[row], " / ".join("%s f%d" % (s.replace("katana_", ""), c) for s, b, c in items)))
    return save(pv.stack(rows, titles=titles), "preview_weapons.png")


def overlays_preview():
    items = [("katana_carry_drawn_idle", "player/v3/player_idle", 3, 0), ("katana_rise", None, 3, 3), ("katana_carry_idle", "player/v3/player_idle", 0, 0)]
    layers = [("기본", []), ("검기1", ["weapons/v3/@_ki1"]), ("검기2", ["weapons/v3/@_ki2"]), ("검기3", ["weapons/v3/@_ki3"]),
              ("각성(월인=만월 1차)", ["weapons/v3/@_awaken"]),
              ("선풍 1차", ["weapons/v4/katana_senpu_a1_#"]), ("선풍 2차", ["weapons/v4/katana_senpu_a1_#", "weapons/v4/katana_senpu_a2_#"]),
              ("투구 1차", ["weapons/v4/katana_kabuto_a1_#"]), ("투구 2차", ["weapons/v4/katana_kabuto_a1_#", "weapons/v4/katana_kabuto_a2_#"]),
              ("만월 1차", ["weapons/v4/katana_mangetsu_a1_#"]), ("만월 2차", ["weapons/v4/katana_mangetsu_a1_#", "weapons/v4/katana_mangetsu_a2_#"])]
    rels = []
    for s, b, r, c in items:
        for _, ls in layers:
            rels += [x.replace("@", s).replace("#", s.split("_", 1)[1]) for x in ls]
    ensure_before(sorted(set(rels)))
    rows, titles = [], []
    for s, b, r, c in items:
        body = b or "player/v3/player_" + s
        for root, tag in ((BEFORE, "전"), (AFTER, "후")):
            cells = []
            for lab, ls in layers:
                L = ["weapons/v3/" + s] + [x.replace("@", s).replace("#", s.split("_", 1)[1]) for x in ls]
                cells.append(pv.scale(compose(root, body, L, None, r, c, size=(200, 200), anchor=(80, 180)), 3))
            rows.append(pv.grid(cells, len(cells), pad=4))
            titles.append("%s · %s %s f%d — %s" % (tag, s, DIRS[r], c, " / ".join(l for l, _ in layers)))
    return save(pv.stack(rows, titles=titles), "preview_overlays.png")


def fx_preview():
    names = ["katana_rise", "katana_fall", "katana_thrust", "katana_counter", "katana_iai", "katana_issen_line_t2", "katana_spin",
             "katana_guardbreak", "katana_fall_wide", "katana_rise_awaken", "katana_thrust_ki3", "katana_iai_ki3", "katana_issen_line_t2_solo"]
    ensure_before(["fx/v3/" + n for n in names])
    ims, titles = [], []
    for n in names:
        for row in (3, 0):
            for root, tag in ((BEFORE, "전"), (AFTER, "후")):
                m = pv.sheet(root, "fx/v3/" + n)[0]
                ims.append(pv.strip(root, "fx/v3/" + n, row, 1))
                titles.append("%s %s · %s 행" % (tag, n, DIRS[row]))
    return save(pv.stack(ims, titles=titles, pad=4), "preview_fx.png")


def hit_preview():
    names = ["hit_katana", "hit_katana_heavy"]
    ensure_before(["fx/v3/" + n for n in names])
    ims, titles = [], []
    for n in names:
        for root, tag in ((BEFORE, "전"), (AFTER, "후")):
            ims.append(pv.strip(root, "fx/v3/" + n, 0, 3))
            titles.append("%s %s" % (tag, n))
    return save(pv.stack(ims, titles=titles), "preview_hit.png")


def fight_preview():
    """몸 + 무기 + fx 를 같은 시각으로 겹친 목업(전/후) — 연격·찌르기·발도·일섬·회전·내려베기·간파."""
    moves = [("katana_rise", "katana_rise", [2, 3, 4, 5]), ("katana_fall", "katana_fall", [1, 2, 3, 4]),
             ("katana_thrust", "katana_thrust", [3, 4, 5, 6]), ("katana_counter", "katana_counter", [2, 3, 4, 5]),
             ("katana_spin", "katana_spin", [9, 10, 11, 12]), ("katana_guardbreak", "katana_guardbreak", [9, 10, 11, 12])]
    rels = []
    for s, f, cols in moves:
        rels += ["weapons/v3/" + s, "fx/v3/" + f]
    ensure_before(rels)
    rows, titles = [], []
    for s, f, cols in moves:
        for row in (3, 0):
            for root, tag in ((BEFORE, "전"), (AFTER, "후")):
                cells = []
                for c in cols:
                    fc = fx_col_at(root, "player/v3/player_" + s, "fx/v3/" + f, c)
                    cells.append(pv.scale(compose(root, "player/v3/player_" + s, ["weapons/v3/" + s], ("fx/v3/" + f, fc) if fc is not None else None,
                                                  row, c, size=(420, 380), anchor=(210, 280)), 2))
                rows.append(pv.grid(cells, len(cells), pad=4))
                titles.append("%s %s %s 행 · 몸 칸 %s (fx 는 spawnAtMs 로 맞춤)" % (tag, s, DIRS[row], cols))
    return save(pv.stack(rows, titles=titles), "preview_fight.png")


def looks_preview():
    import glob
    names = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(AFTER, "looks", "katana_*.png")))
    ensure_before(["looks/" + n for n in names])
    rows, titles = [], []
    for root, tag in ((BEFORE, "전"), (AFTER, "후")):
        cells = []
        for n in names:
            im = Image.open(os.path.join(root, "looks", n + ".png")).convert("RGBA")
            bg = Image.new("RGBA", im.size, pv.BG + (255,))
            bg.alpha_composite(im)
            cells.append(pv.scale(bg, 2))
        rows.append(pv.grid(cells, 8, pad=4, labels=names))
        titles.append(tag + " looks/katana_*")
    return save(pv.stack(rows, titles=titles), "preview_looks.png")


if __name__ == "__main__":
    want = sys.argv[1:] or ["weapons", "overlays", "fx", "hit", "fight", "looks"]
    for w in want:
        print(globals()[w + "_preview"]())
