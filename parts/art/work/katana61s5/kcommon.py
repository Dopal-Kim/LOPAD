"""61 단계 5 칼 — 공용: 기존 메타 읽기 · 격자 시트 쓰기 · 트림 아틀라스 변환(이 작업 전용 임시 폴더) · 검사."""
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets", "sprites")
sys.path.insert(0, os.path.join(WORK, "atlas57"))
import gridsheet  # noqa: E402
from PIL import Image  # noqa: E402

VERSION = "v3-r61s5"
VERSION_V4 = "v4-r61s5-katana"
SRC = "parts/art/work/katana61s5/build.py (61 단계 5 P13 §2 — 칼 재디자인 '은선', 무기+이펙트 함께)"
GRID = os.path.join(HERE, "out", "grid")          # 격자 원본(검증·미리보기용, git 제외)

_ab = {}


def atlas_mod():
    if "m" not in _ab:
        spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(WORK, "atlas57", "build.py"))
        m = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.join(WORK, "atlas57"))
        spec.loader.exec_module(m)
        _ab["m"] = m
    return _ab["m"]


SRC_REV = "2aa9fe6"                                # 고치기 전 칼 그림이 있는 커밋(61 단계 4 a3e76f8 이후, 이 작업 이전) — 다시 돌려도 이것을 원본으로
META0 = os.path.join(HERE, "out", "meta0")         # SRC_REV 메타 캐시(격자 형식) — 덧칠·병렬 경쟁 방지


def old_meta(rel):
    p = os.path.join(META0, rel + ".json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return gridsheet.load_meta(os.path.join(SPR, rel + ".json"))


def snapshot_meta(rels, git_rev=None):
    """META0 에 없는 시트 메타를 git(기본 SRC_REV)의 아틀라스 JSON 에서 격자 형식으로 저장."""
    import subprocess
    git_rev = git_rev or SRC_REV
    for rel in rels:
        p = os.path.join(META0, rel + ".json")
        if os.path.exists(p):
            continue
        raw = subprocess.run(["git", "-C", ROOT, "show", "%s:assets/sprites/%s.json" % (git_rev, rel)], capture_output=True, check=True).stdout
        m = json.loads(raw)
        out = {}
        for k, v in m.items():
            if k in ("atlas", "meta", "textures"):
                continue
            if k == "framesPerDirection":
                out["frames"] = v
            elif k != "frames":
                out[k] = v
        if "atlas" in m:
            g = m["atlas"]["grid"]
            out.setdefault("frameWidth", g["frameWidth"])
            out.setdefault("frameHeight", g["frameHeight"])
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)


def old_frames(rel):
    m = old_meta(rel)
    g = gridsheet.open_grid(os.path.join(SPR, rel + ".json"))
    fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
    return m, {d: [g.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r, d in enumerate(m["directions"])}


def clear_border(im):
    px = im.load()
    W, H = im.size
    n = 0
    for x in range(W):
        for y in (0, H - 1):
            if px[x, y][3]:
                px[x, y] = (0, 0, 0, 0)
                n += 1
    for y in range(H):
        for x in (0, W - 1):
            if px[x, y][3]:
                px[x, y] = (0, 0, 0, 0)
                n += 1
    return n


def colors(frames_by_dir):
    s = set()
    for lst in frames_by_dir.values():
        for im in lst:
            s |= {p[:3] for p in im.getdata() if p[3]}
    return s


def check(name, frames_by_dir, glow_frames=None, hot=None):
    """반투명 0 · glowFrames 밖 백열(hot 색) 0."""
    for d, lst in frames_by_dir.items():
        for i, im in enumerate(lst):
            a = set(im.getchannel("A").getdata())
            assert a <= {0, 255}, (name, d, i, "semi")
            if hot and glow_frames is not None and i not in glow_frames:
                bad = {p[:3] for p in im.getdata() if p[3]} & hot
                assert not bad, (name, d, i, "hot outside glow", bad)


def write_grid(rel, frames_by_dir, meta):
    """rel = 'weapons/v3/katana_rise' — 격자 PNG + JSON 을 assets 와 out/grid 에 쓴 뒤 assets 를 트림 아틀라스로 바꾼다."""
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
    m.update(image=name + ".png", frameWidth=fw, frameHeight=fh, frames=n)
    m.pop("framesPerDirection", None)
    # 격자 원본 보관
    gd = os.path.join(GRID, os.path.dirname(rel))
    os.makedirs(gd, exist_ok=True)
    sheet.save(os.path.join(gd, name + ".png"), optimize=True)
    with open(os.path.join(gd, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    # assets: 옛 아틀라스 페이지 지우고 격자 → 아틀라스
    dst = os.path.join(SPR, os.path.dirname(rel))
    jp, pp = os.path.join(dst, name + ".json"), os.path.join(dst, name + ".png")
    if os.path.exists(jp):
        om = json.load(open(jp, encoding="utf-8"))
        for t in om.get("textures", []):
            p = os.path.join(dst, t["image"])
            if os.path.exists(p):
                os.remove(p)
    shutil.copy2(os.path.join(gd, name + ".png"), pp)
    shutil.copy2(os.path.join(gd, name + ".json"), jp)
    ab = atlas_mod()
    TMP = os.path.join(HERE, "out", "_atlas_tmp_k61s5_%d" % os.getpid())
    od = os.path.join(TMP, os.path.dirname(rel))
    os.makedirs(od, exist_ok=True)
    try:
        res = ab.convert_sheet(pp, jp, od, 2, 4096, True)
        ab.apply_in_place(res, od, dst, pp, jp, 4096)
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    return dict(size=[sheet.width, sheet.height], pages=[(w, h) for _, w, h in res["pages"]])


def gpu_mb(rel):
    """아틀라스 페이지 RGBA 면적(MB)."""
    jp = os.path.join(SPR, rel + ".json")
    m = json.load(open(jp, encoding="utf-8"))
    tot = 0
    if "textures" in m:
        for t in m["textures"]:
            tot += t["size"]["w"] * t["size"]["h"]
    else:
        tot = m["meta"]["size"]["w"] * m["meta"]["size"]["h"]
    return tot * 4 / 1048576.0
