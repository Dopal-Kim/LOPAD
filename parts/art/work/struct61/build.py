#!/usr/bin/env python3
"""61라운드 아트 단계 2 — 구조물 v1 → 64도트(AR-4) · 임시 2배 타일 재작업(P3) · 방 다양화 소품 군.

python3 parts/art/work/struct61/build.py [--dry] [--only structs,tiles,props]
  structs : structs61(구조물 9) + sets61(세트·튜토리얼 17) → assets/sprites/structures/v3/<id>.png/.json (격자로 쓴 뒤 atlas57 트림 아틀라스로 교체)
  tiles   : tiles61_build → assets/tiles/v2/stage1_<지역>.png/.json (격자 타일셋 유지)
  props   : props61 → assets/tiles/v3/stage1_<지역>_props.png/.json 아래에 새 줄 덧붙임(기존 rect·그림 불변)
  --dry   : assets 를 건드리지 않고 out/ 미리보기만
미리보기: preview61.py (이 스크립트 끝에서 부름)
"""
import json
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import s61  # noqa: E402
import b2  # noqa: E402
import structs61  # noqa: E402
import sets61  # noqa: E402
import props61  # noqa: E402

V1 = os.path.join(s61.SPR, "structures")
STRUCTS, SETS, v1json = s61.STRUCTS, s61.SETS, s61.v1json
PROPS_DIR = os.path.join(s61.TILES, "v3")
BEFORE_PROPS = os.path.join(HERE, "before61", "props")
OUT = os.path.join(HERE, "out")


def build_structs(dry):
    b2.DRY = dry
    res = {}
    for id_ in STRUCTS + SETS:
        v1 = v1json(id_)
        mod = structs61 if hasattr(structs61, id_) else sets61
        fr, W, H, piv, m = getattr(mod, id_)(v1)
        n = len(fr)
        dur = v1.get("frameDurationsMs") or [200] * n
        assert len(dur) == n, (id_, len(dur), n)
        mx = max(max(v) for v in v1["states"].values())
        assert mx < n, (id_, "states 프레임 번호 초과")
        if id_ in SETS:
            m["replaces"] = f"structures/{id_} (49라운드 v1 16도트 칸) — v3 → 구 순 우선 로드"
        m.setdefault("frameSizeNote", "v1 은 칸 = 16 도트, v3 는 칸 = 64 도트(pixelScale 0.5). footprint·상태·프레임 수·ms 는 v1 과 같다")
        semi = sum(s61.semi(im) for im in fr)
        cols = set()
        for im in fr:
            cols |= s61.colors(im)
        b2.write_sheet("structures", id_, fr, W, H, m, durations=dur, loop=bool(v1.get("loop", False)))
        res[id_] = {"size": [W, H], "frames": n, "pivot": list(piv), "colors": len(cols), "semiPx": semi}
    rep = [] if dry else b2.to_atlas()
    return res, rep


def append_props(rid, dry):
    os.makedirs(BEFORE_PROPS, exist_ok=True)
    for ext in ("png", "json"):
        p = os.path.join(BEFORE_PROPS, f"stage1_{rid}_props.{ext}")
        if not os.path.exists(p):
            shutil.copy(os.path.join(PROPS_DIR, f"stage1_{rid}_props.{ext}"), p)
    old = Image.open(os.path.join(BEFORE_PROPS, f"stage1_{rid}_props.png")).convert("RGBA")
    meta = json.load(open(os.path.join(BEFORE_PROPS, f"stage1_{rid}_props.json"), encoding="utf-8"))
    SW, CELL = old.width, 64
    small = [f() for f in props61.NEW[rid]["small"]]
    big = [f() for f in props61.NEW[rid]["big"]]
    y = old.height
    placed = []
    x = 0
    for p in small:
        if x + 128 > SW:
            x, y = 0, y + 128
        placed.append((p, x, y, False)); x += 128
    if small:
        y += 128
    x, shelf = 0, 0
    for p in sorted(big, key=lambda q: -q.im.height):
        w = -(-p.im.width // CELL) * CELL
        h = -(-p.im.height // CELL) * CELL
        if x + w > SW:
            x, y, shelf = 0, y + shelf, 0
        placed.append((p, x, y, True)); x += w; shelf = max(shelf, h)
    H = -(-(y + shelf) // CELL) * CELL
    sheet = Image.new("RGBA", (SW, H), (0, 0, 0, 0))
    sheet.alpha_composite(old, (0, 0))
    j = dict(meta)
    j["props"] = list(meta["props"]); j["bigProps"] = list(meta["bigProps"])
    names = {e["name"] for e in j["props"] + j["bigProps"]}
    for (p, px_, py_, isbig) in placed:
        assert p.name not in names, (rid, p.name)
        assert p.im.size[0] <= (SW - px_)
        sheet.alpha_composite(p.im, (px_, py_))
        e = {"name": p.name, "index": (py_ // CELL) * (SW // CELL) + px_ // CELL,
             "rect": {"x": px_, "y": py_, "w": p.im.width, "h": p.im.height},
             "pivot": {"x": p.pivot[0], "y": p.pivot[1]}, "footprint": list(p.footprint), "solid": p.solid}
        if p.occlude is not None and p.extra.get("depth") != "floor":
            e["occludeAbove"] = p.occlude
        for k in ("maxPerRoom", "weight", "depth", "placement", "note"):
            if k in p.extra:
                e[k] = p.extra[k]
        if isbig:
            e.setdefault("maxPerRoom", 1)
        if p.light:
            e["light"] = p.light
        e["added61"] = True
        e["variantTag"] = props61.TAGS[p.name]
        (j["bigProps"] if isbig else j["props"]).append(e)
    assert sheet.crop((0, 0, old.width, old.height)).tobytes() == old.tobytes(), "기존 그림이 바뀜"
    j["added61Note"] = ("61라운드 방 다양화 소품 군: 시트 아래(y ≥ %d)에 덧붙임 — 기존 항목 rect·그림 불변. added61 = 새 항목, "
                        "variantTag = 방 배치 변주 묶음 제안(같은 태그끼리 한 방에 모아 두면 장면이 됨: 예 hall_brawl = 엎어진 식탁 + 부서진 의자 + 엎어진 쟁반)" % old.height)
    j["source"] = meta.get("source", "") + " + parts/art/work/struct61/build.py (61라운드 방 다양화 소품)"
    os.makedirs(OUT, exist_ok=True)
    sheet.save(os.path.join(OUT, f"props61_{rid}.png"))
    if not dry:
        sheet.save(os.path.join(PROPS_DIR, f"stage1_{rid}_props.png"))
        with open(os.path.join(PROPS_DIR, f"stage1_{rid}_props.json"), "w", encoding="utf-8") as f:
            json.dump(j, f, ensure_ascii=False, indent=1)
    return {"sheet": list(sheet.size), "added": [p.name for (p, *_) in placed], "colors": len(s61.colors(sheet))}


def main():
    dry = "--dry" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))
    stats = {}
    if not only or "structs" in only:
        res, rep = build_structs(dry)
        stats["structs"] = res
        stats["atlas"] = [list(map(str, r)) for r in rep]
        print("구조물", len(res), "시트 · 아틀라스", len(rep))
    if not only or "tiles" in only:
        import tiles61_build
        stats["tiles"] = {r: tiles61_build.build(r, not dry) for r in tiles61_build.WALLS}
    if not only or "props" in only:
        stats["props"] = {r: append_props(r, dry) for r in props61.NEW}
        print("소품", {r: v["added"] for r, v in stats["props"].items()})
    os.makedirs(OUT, exist_ok=True)
    json.dump(stats, open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    import preview61
    preview61.main()


if __name__ == "__main__":
    main()
