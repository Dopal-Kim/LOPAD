"""보스 재도트 단계(boss_redot.py 를 15 동작 시트 전부에) — 원본은 git BASE_REV 의 아틀라스에서 되살려 멱등.

격자 PNG+JSON 을 assets/sprites/bosses/v3/ 에 쓴 뒤 atlas57/build.py --in-place --cats bosses --only <시트> 로 아틀라스 변환
(전 프레임 대조 통과 시 교체). 메타는 원본 그대로 + `redot62c` 블록. 림·_rim_lite 시트는 건드리지 않는다(실루엣 알파 불변).
환경변수 BOSS_ACTS="idle walk" 로 일부만.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

import boss_redot as R
from c62 import ROOT, SRC, WORK, hx

sys.path.insert(0, os.path.join(WORK, "atlas57"))
import gridsheet  # noqa: E402

BASE_REV = "b2d9dee"      # 62 루프 3 시작 시점(1.5배 네이티브 61 시트 그대로)
ACTS = ["idle", "walk", "attack", "slam", "hurt", "stagger_dash", "kick", "throw", "throw_torch", "drink", "drink_break",
        "phase_drink", "fall", "death", "intro"]
REL = "assets/sprites/bosses/v3"


def git_file(rel, dst):
    data = subprocess.run(["git", "-C", ROOT, "show", f"{BASE_REV}:{rel}"], check=True, capture_output=True).stdout
    with open(dst, "wb") as f:
        f.write(data)


def original_grid(act):
    tmp = tempfile.mkdtemp(prefix="r62c_boss_")
    jrel = f"{REL}/stage1_{act}.json"
    jp = os.path.join(tmp, f"stage1_{act}.json")
    git_file(jrel, jp)
    m = json.load(open(jp, encoding="utf-8"))
    pages = [t["image"] for t in m["textures"]] if "textures" in m else [m["meta"]["image"]]
    for pg in pages:
        git_file(f"{REL}/{pg}", os.path.join(tmp, pg))
    meta = gridsheet.load_meta(jp)
    grid = gridsheet.open_grid(jp)
    shutil.rmtree(tmp, ignore_errors=True)
    return meta, grid


def redo(act):
    meta, grid = original_grid(act)
    fw, fh = meta["frameWidth"], meta["frameHeight"]
    em = {hx(h) for h in meta.get("emissiveColors", [])}
    ramps, index = R.fixed_ramps(em)
    out = Image.new("RGBA", grid.size, (0, 0, 0, 0))
    cols, rows = grid.size[0] // fw, grid.size[1] // fh
    for r in range(rows):
        for c in range(cols):
            fr = grid.crop((c * fw, r * fh, c * fw + fw, r * fh + fh))
            out.paste(R.redot_frame(fr, ramps, index, em), (c * fw, r * fh))
    # 알파 불변 확인
    assert list(out.getchannel("A").getdata()) == list(grid.getchannel("A").getdata()), act
    name = f"stage1_{act}"
    meta = dict(meta)
    meta["redot62c"] = {
        "note": "62 루프 3 재도트(P17 묶음 D) — 틀·피벗·프레임·ms·앵커·실루엣 알파 그대로, 색만: 재질 램프(시트에 있던 색만) 위 덩어리 부피 명암 "
                "(좌상단 빛) + 칸 경계 바이어 디더 + 실루엣 안쪽 먹 테(아래·오른 3칸·위·왼 2칸 어둡게) + 재질 경계 그늘 선. 발광 색 그대로",
        "base": f"git {BASE_REV} {REL}/{name}",
        "params": R.P,
        "source": SRC + " · boss.py / boss_redot.py",
    }
    out.save(os.path.join(ROOT, REL, name + ".png"))
    with open(os.path.join(ROOT, REL, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    r = subprocess.run([sys.executable, os.path.join(WORK, "atlas57", "build.py"), "--in-place", "--cats", "bosses",
                        "--only", name + "."], capture_output=True, text=True)
    if "assets 교체" not in r.stdout:
        # --only 는 부분 문자열 — 확장자 포함 이름이 안 맞으면 이름만으로
        r = subprocess.run([sys.executable, os.path.join(WORK, "atlas57", "build.py"), "--in-place", "--cats", "bosses",
                            "--only", name], capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if name in l and "->" in l]
    return line[0] if line else r.stdout[-400:] + r.stderr[-400:]


def build():
    acts = os.environ.get("BOSS_ACTS", "").split() or ACTS
    res = []
    for a in acts:
        res.append(redo(a))
        print(res[-1], flush=True)
    return res
