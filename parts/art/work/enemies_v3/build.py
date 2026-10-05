"""적 v3 빌드 (53라운드 Q33) — python3 parts/art/work/enemies_v3/build.py [dummy|archer|charger ...]

산출: assets/sprites/enemies/v3/<id>_<idle|walk|attack|hurt|death>.png/json
미리보기(이 폴더): preview_<id>_<동작>_x2.png · preview_<id>_<동작>_x3.gif · preview_mock_lit.png · stats.json
결정적(난수 없음, 고정 seed). hero_v3/v3kit.py 는 import 만.
"""
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import erig  # noqa: E402,F401  (경로 정리)
import eanim as anim  # noqa: E402
import eexport  # noqa: E402
import eprev  # noqa: E402
from PIL import Image  # noqa: E402

MODS = {"dummy": "drunk", "archer": "musket", "charger": "bulwark"}


def main(ids):
    os.makedirs(eexport.OUT, exist_ok=True)
    stats_path = os.path.join(HERE, "stats.json")
    stats = json.load(open(stats_path)) if os.path.exists(stats_path) else {}
    idle = {}
    for eid in ids:
        modname = MODS[eid]
        mod = importlib.import_module(modname)
        res = anim.render_all(modname)
        st = {"frame": [mod.FW, mod.FH], "pivot": list(mod.PIV), "scale": mod.SCALE, "actions": {}}
        all_frames = {}
        for act in anim.ACTS:
            ms, fmap, ph, frames = eexport.export(mod, act, res[act])
            all_frames[act] = frames
            marks, strong, states = set(), set(), None
            if ph:
                marks = {i for v in ph.values() for i in v if v is not ph.get("recover") and v is not ph.get("lower")}
                strong = {ph[eexport.STRONG[eid]][0]}
                if eid == "charger":
                    strong.add(ph["smash"][0])
                states = [next((k for k, v in ph.items() if i in v), "") for i in range(len(ms))]
            eprev.frames_x2(os.path.join(HERE, "preview_%s_%s_x2.png" % (eid, act)), "%s %s" % (eid, act), frames, ms, mod.PIV,
                            marks=marks, strong=strong, states=states)
            eprev.gif_x3(os.path.join(HERE, "preview_%s_%s_x3.gif" % (eid, act)), frames, ms)
            st["actions"][act] = {"frames": len(ms), "ms": ms, "framesMap": fmap, "phaseFrames": ph}
        cs = eexport.colors(all_frames)
        st["colors"] = len(cs)
        b = None
        for im in all_frames["idle"]["down"] + all_frames["idle"]["left"]:
            bb = im.getbbox()
            b = bb if b is None else (min(b[0], bb[0]), min(b[1], bb[1]), max(b[2], bb[2]), max(b[3], bb[3]))
        st["idleBBox"] = list(b)
        st["idleHeightDots"] = mod.PIV[1] - b[1]
        stats[eid] = st
        idle[eid] = (all_frames["idle"], mod.PIV)
        print(eid, "colors", len(cs), "idle height", st["idleHeightDots"])
    with open(stats_path, "w") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    if len(ids) == 3:
        mock(idle)


def mock(idle):
    root = anim.ROOT
    hero = Image.open(os.path.join(root, "assets/sprites/player/v3/player_idle.png")).convert("RGBA")
    hd = hero.crop((0, 0, 96, 144))
    hl = hero.crop((0, 288, 96, 432))
    hp = (48, 138)
    spots = [("주인공 v3", hd, hp, True)]
    for eid, lab in (("dummy", "징집병"), ("archer", "사수"), ("charger", "결사병")):
        fr, piv = idle[eid]
        spots.append((lab, fr["down"][0], piv, False))
    spots.append(("주인공 측면", hl, hp, True))
    for eid, lab in (("dummy", "징집병 측"), ("archer", "사수 측"), ("charger", "결사병 측")):
        fr, piv = idle[eid]
        spots.append((lab, fr["left"][0], piv, False))
    eprev.mock_lit(spots, os.path.join(HERE, "preview_mock_lit.png"),
                   "1배(1920×1080 내부 렌더) · 외곽 v2 바닥 · 주인공 v3 와 적 v3 크기 비교 · 조명 임시(주인공 혼불 빛만)")


if __name__ == "__main__":
    # 60라운드 Q8: 적 3종은 parts/art/work/floor1q60/enemy_build.py 보강판이 현행. 이 53라운드 빌드를 돌리면 assets 를 옛 그림(격자)으로
    # 덮으므로 --legacy 없이는 멈춘다(모듈 import 는 floor1q60 이 그대로 쓴다).
    if "--legacy" not in sys.argv:
        sys.exit("enemies_v3/build.py 는 53라운드 판 보관용입니다(현행 = floor1q60/enemy_build.py --assets). 다시 만들려면 --legacy")
    main([a for a in sys.argv[1:] if a != "--legacy"] or ["dummy", "archer", "charger"])
