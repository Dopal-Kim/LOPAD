"""P19 시트 입출력 — 원본(SRC_REV) 읽기 · 무기 오버레이 프레임 이동/재배열 · 격자 → 트림 아틀라스 내보내기.

다시 돌려도 오프셋이 두 번 걸리지 않게 '원본' 은 항상 git SRC_REV(이 작업 직전 커밋)의 아틀라스에서 되살린다(out/src0 캐시).
"""
import copy
import json
import os
import shutil
import subprocess
import sys
from glob import glob

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "..", "..", ".."))
SPR = os.path.join(ROOT, "assets", "sprites")
sys.path.insert(0, os.path.join(WORK, "atlas57"))
import gridsheet  # noqa: E402

SRC_REV = "811fa42"                     # P19 주인공 작업 직전 커밋 — 몸·무기 오버레이 원본
CACHE = os.path.join(HERE, "out", "src0")
GRID = os.path.join(HERE, "out", "grid")
DIRS4 = ["down", "up", "left", "right"]


def _git(path):
    return subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (SRC_REV, path)], capture_output=True, check=True).stdout


def _fetch(rel):
    """SRC_REV 의 아틀라스 JSON + 페이지 PNG 를 CACHE/<rel> 로 내려받는다."""
    jp = os.path.join(CACHE, rel + ".json")
    if os.path.exists(jp):
        return jp
    raw = _git("assets/sprites/%s.json" % rel)
    os.makedirs(os.path.dirname(jp), exist_ok=True)
    m = json.loads(raw)
    pages = [t["image"] for t in m.get("textures", [])] or [m.get("image") or os.path.basename(rel) + ".png"]
    for pg in pages:
        with open(os.path.join(os.path.dirname(jp), pg), "wb") as f:
            f.write(_git("assets/sprites/%s/%s" % (os.path.dirname(rel), pg)))
    with open(jp, "wb") as f:
        f.write(raw)
    return jp


def exists_src(rel):
    try:
        _fetch(rel)
        return True
    except subprocess.CalledProcessError:
        return False


def src_meta(rel):
    return gridsheet.load_meta(_fetch(rel))


def src_grid(rel):
    jp = _fetch(rel)
    return gridsheet.load_meta(jp), gridsheet.open_grid(jp[:-5] + ".png")


def cells(meta, im):
    fw, fh, n = meta["frameWidth"], meta["frameHeight"], meta["frames"]
    return {d: [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r, d in enumerate(meta["directions"])}


# -----------------------------------------------------------------------------
# 무기 오버레이 묶음
# -----------------------------------------------------------------------------
_BODYSHEET = {}


def _bodysheet_index():
    """SRC_REV 의 weapons/v3·v4 JSON → bodySheet (git 한 번에 읽어 out/src0/bodysheet.json 캐시)."""
    if _BODYSHEET:
        return _BODYSHEET
    cp = os.path.join(CACHE, "bodysheet.json")
    if os.path.exists(cp):
        _BODYSHEET.update(json.load(open(cp, encoding="utf-8")))
        return _BODYSHEET
    names = subprocess.run(["git", "-C", ROOT, "ls-tree", "--name-only", SRC_REV, "assets/sprites/weapons/v3/", "assets/sprites/weapons/v4/"],
                           capture_output=True, check=True, text=True).stdout.split()
    for p in names:
        if p.endswith(".json"):
            m = json.loads(_git(p))
            _BODYSHEET[p[len("assets/sprites/"):-5]] = m.get("bodySheet")
    os.makedirs(CACHE, exist_ok=True)
    json.dump(_BODYSHEET, open(cp, "w", encoding="utf-8"), ensure_ascii=False)
    return _BODYSHEET


def family(body):
    """bodySheet == body 인 무기 오버레이(weapons/v3·v4) 상대 경로 목록 — 원본(SRC_REV) 기준(작업 중 assets 상태와 무관)."""
    return sorted(rel for rel, b in _bodysheet_index().items() if b == body)


def is_back_carry(rel):
    """등에 멘 대검(칼집 없이 등 끈) — 몸 가슴 이동을 따른다."""
    n = os.path.basename(rel)
    return n.startswith("greatsword") and "_carry_" in n and "_drawn_" not in n


def _shift_pt(v, dx, dy):
    if v is None:
        return None
    if isinstance(v, list) and len(v) == 2 and all(isinstance(c, (int, float)) for c in v):
        return [round(v[0] + dx, 1), round(v[1] + dy, 1)]
    if isinstance(v, dict):
        if "x" in v and "y" in v and isinstance(v["x"], (int, float)):
            w = dict(v)
            w["x"], w["y"] = round(v["x"] + dx, 1), round(v["y"] + dy, 1)
            return w
        return {k: _shift_pt(x, dx, dy) for k, x in v.items()}
    return v


PER_FRAME_KEYS = ("frameDurationsMs", "frameStates", "bladeLocal")


def remap_meta(meta, plan, n_old):
    """plan = {d: [(src_col, dx, dy)]}. 앵커(…Anchors) 를 프레임마다 이동·재배열, 프레임별 목록을 재배열."""
    m = copy.deepcopy(meta)
    d0 = m["directions"][0]
    cols0 = [c for c, _, _ in plan[d0]]
    for k, v in list(m.items()):
        if k.endswith("Anchors") and isinstance(v, dict):
            nv = {}
            for d, lst in v.items():
                if d in plan and isinstance(lst, list) and len(lst) == n_old:
                    nv[d] = [_shift_pt(copy.deepcopy(lst[c]), dx, dy) for c, dx, dy in plan[d]]
                else:
                    nv[d] = lst
            m[k] = nv
        elif k == "depthByFrame" and isinstance(v, dict):
            m[k] = {d: ([lst[c] for c, _, _ in plan[d]] if d in plan and len(lst) == n_old else lst) for d, lst in v.items()}
        elif k in PER_FRAME_KEYS and isinstance(v, list) and len(v) == n_old:
            m[k] = [v[c] for c in cols0]
    m["frames"] = len(cols0)
    return m


def grow_need(meta, im, plan):
    """옮긴 뒤 틀 아래·오른쪽으로 나가는 도트 수(피벗이 왼위 기준이라 아래·오른쪽으로만 키우면 피벗·오프셋 불변)."""
    src = cells(meta, im)
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    gw = gh = 0
    for d in meta["directions"]:
        for c, dx, dy in plan[d]:
            bb = src[d][c].getbbox()
            if bb:
                gw, gh = max(gw, bb[2] + dx - fw), max(gh, bb[3] + dy - fh)
    return max(0, gw), max(0, gh)


def grow_tl_need(meta, im, plan):
    src = cells(meta, im)
    gl = gt = 0
    for d in meta["directions"]:
        for c, dx, dy in plan[d]:
            bb = src[d][c].getbbox()
            if bb:
                gl, gt = max(gl, -(bb[0] + dx)), max(gt, -(bb[1] + dy))
    return gl + gl % 2, gt + gt % 2


def shift_frame_coords(m, gl, gt):
    """틀을 왼쪽·위로 키운 만큼 피벗·playerFrameOffset·모든 …Anchors 를 옮긴다."""
    if not (gl or gt):
        return m
    for k in ("pivot", "playerFrameOffset"):
        if isinstance(m.get(k), dict):
            m[k] = {"x": m[k]["x"] + gl, "y": m[k]["y"] + gt}
    for k, v in list(m.items()):
        if k.endswith("Anchors") and isinstance(v, dict):
            m[k] = {d: ([_shift_pt(x, gl, gt) for x in lst] if isinstance(lst, list) else lst) for d, lst in v.items()}
    return m


def move_cells(meta, im, plan, grow_tl=False):
    """오버레이 칸을 plan 대로 옮겨 새 칸 목록 {d: [Image]} — 틀 밖으로 나간 픽셀 수도 돌려준다.
    아래·오른쪽으로 넘치면 틀을 짝수 도트만큼 키운다(meta frameWidth/Height 갱신, 피벗 불변 — p19FrameGrow 기록)."""
    gw, gh = grow_need(meta, im, plan)
    gl, gt = grow_tl_need(meta, im, plan) if grow_tl else (0, 0)
    src = cells(meta, im)
    if gl or gt:                              # 왼쪽·위로 키움: 칸을 (gl, gt) 만큼 밀고 피벗·앵커도 같이(remap 뒤 shift_frame_coords)
        meta["p19FrameGrowTL"] = {"addLeft": gl, "addTop": gt, "fromPivot": dict(meta["pivot"]),
                                  "note": "P19: 옮긴 칼끝이 틀 왼쪽·위를 넘어 틀을 키움 — pivot·playerFrameOffset·앵커가 그만큼 이동(JSON 값을 읽을 것)"}
        meta["frameWidth"] += gl
        meta["frameHeight"] += gt
        for d in src:
            nl = []
            for c in src[d]:
                t = Image.new("RGBA", (meta["frameWidth"], meta["frameHeight"]), (0, 0, 0, 0))
                t.paste(c, (gl, gt))
                nl.append(t)
            src[d] = nl
    if gw or gh:
        gw, gh = gw + gw % 2, gh + gh % 2
        meta["p19FrameGrow"] = {"from": [meta["frameWidth"], meta["frameHeight"]], "addRight": gw, "addBottom": gh,
                                "note": "P19: 몸이 낮아져 옮긴 무기 끝이 틀 아래·오른쪽을 넘어 틀만 키움(피벗·playerFrameOffset 불변)"}
        meta["frameWidth"] += gw
        meta["frameHeight"] += gh
        for d in src:
            nl = []
            for c in src[d]:
                t = Image.new("RGBA", (meta["frameWidth"], meta["frameHeight"]), (0, 0, 0, 0))
                t.paste(c, (0, 0))
                nl.append(t)
            src[d] = nl
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    out, lost = {}, 0
    for d in meta["directions"]:
        lst = []
        for c, dx, dy in plan[d]:
            s = src[d][c]
            if dx == 0 and dy == 0:
                lst.append(s.copy())
                continue
            bb = s.getbbox()
            if bb:
                nb = (bb[0] + dx, bb[1] + dy, bb[2] + dx, bb[3] + dy)
                if nb[0] < 0 or nb[1] < 0 or nb[2] > fw or nb[3] > fh:
                    a = s.getchannel("A")
                    tot = sum(1 for p in a.getdata() if p)
                    t = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
                    t.paste(s, (dx, dy), s)
                    lost += tot - sum(1 for p in t.getchannel("A").getdata() if p)
            t = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            t.paste(s, (dx, dy), s)
            lst.append(t)
        out[d] = lst
    return out, lost


def rename_strings(m, pairs):
    def f(v):
        if isinstance(v, str):
            for a, b in pairs:
                v = v.replace(a, b)
            return v
        if isinstance(v, list):
            return [f(x) for x in v]
        if isinstance(v, dict):
            return {k: f(x) for k, x in v.items()}
        return v
    return f(m)


# -----------------------------------------------------------------------------
# 내보내기 (격자 → assets 트림 아틀라스)
# -----------------------------------------------------------------------------
_ab = {}


def atlas_mod():
    if "m" not in _ab:
        import importlib.util
        spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(WORK, "atlas57", "build.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _ab["m"] = mod
    return _ab["m"]


def write_grid(rel, frames_by_dir, meta):
    """격자 PNG + JSON 을 out/grid 에 남기고 assets 의 같은 이름을 트림 아틀라스로 교체(atlas57 전 프레임 대조)."""
    m = dict(meta)
    dirs = m["directions"]
    fw, fh = frames_by_dir[dirs[0]][0].size
    n = len(frames_by_dir[dirs[0]])
    sheet = Image.new("RGBA", (fw * n, fh * len(dirs)), (0, 0, 0, 0))
    for r, d in enumerate(dirs):
        assert len(frames_by_dir[d]) == n, (rel, d)
        for c, im in enumerate(frames_by_dir[d]):
            assert im.size == (fw, fh), (rel, d, c, im.size)
            sheet.alpha_composite(im, (c * fw, r * fh))
    name = os.path.basename(rel)
    for k in ("atlas", "meta", "textures", "framesPerDirection"):
        m.pop(k, None)
    m.update(image=name + ".png", frameWidth=fw, frameHeight=fh, frames=n)
    gd = os.path.join(GRID, os.path.dirname(rel))
    os.makedirs(gd, exist_ok=True)
    sheet.save(os.path.join(gd, name + ".png"), optimize=True)
    with open(os.path.join(gd, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    dst = os.path.join(SPR, os.path.dirname(rel))
    os.makedirs(dst, exist_ok=True)
    jp, pp = os.path.join(dst, name + ".json"), os.path.join(dst, name + ".png")
    if os.path.exists(jp):
        try:
            om = json.load(open(jp, encoding="utf-8"))
        except ValueError:                       # 깨진(빈) JSON — 덮어쓴다
            om = {}
        for t in om.get("textures", []):
            p = os.path.join(dst, t["image"])
            if os.path.exists(p):
                os.remove(p)
    shutil.copy2(os.path.join(gd, name + ".png"), pp)
    shutil.copy2(os.path.join(gd, name + ".json"), jp)
    ab = atlas_mod()
    tmp = os.path.join(HERE, "out", "_atlas_tmp_%d" % os.getpid())
    od = os.path.join(tmp, os.path.dirname(rel))
    os.makedirs(od, exist_ok=True)
    try:
        res = ab.convert_sheet(pp, jp, od, 2, 4096, True)
        ab.apply_in_place(res, od, dst, pp, jp, 4096)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return dict(size=[sheet.width, sheet.height], pages=[(w, h) for _, w, h in res["pages"]])
