"""60라운드 Q4 샘플 — 징집병 보강안 렌더 + 전/후 미리보기 (assets 에 쓰지 않음).

python3 parts/art/work/floor1q60/enemy_build.py [동작 ...]
산출(이 폴더 out/): dummy60_<동작>.png/.json(격자 시트, 검수용 — assets 미반영), preview_enemy_<동작>_x2.png, preview_enemy_<동작>_x3.gif
전/후 비교는 compare.py.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "../enemies_v3")))
import erig  # noqa: E402,F401
sys.path.insert(0, HERE)
import eanim as anim  # noqa: E402
import eprev  # noqa: E402
import drunk60 as mod  # noqa: E402
from PIL import Image  # noqa: E402

OUT = os.path.join(HERE, "out")
SPLITS = {"attack": mod.ATTACK_SPLIT, "hurt": mod.HURT_SPLIT}


def timing(act):
    old = anim.old_json("dummy", act)
    sp = SPLITS.get(act) or anim.SPLIT[act] or [1] * old["frames"]
    ms, fmap = anim.split_ms(old["frameDurationsMs"], sp)
    anim.check_timing("dummy60", act, old["frameDurationsMs"], ms, fmap)
    return old, ms, fmap


def main(acts):
    os.makedirs(OUT, exist_ok=True)
    res = anim.render_all("drunk60", acts)
    allc = set()
    for act in acts:
        old, ms, fmap = timing(act)
        frames = {d: [im for im, _ in res[act][d]] for d in anim.DIRS}
        for d in anim.DIRS:
            assert len(frames[d]) == len(ms), (act, d, len(frames[d]), len(ms))
            for f in frames[d]:
                assert not any(0 < a < 255 for a in f.getchannel("A").get_flattened_data()), "반투명"
                allc |= {c[:3] for c in f.get_flattened_data() if c[3]}
        n = len(ms)
        sheet = Image.new("RGBA", (mod.FW * n, mod.FH * 4), (0, 0, 0, 0))
        for r, d in enumerate(anim.DIRS):
            for c, f in enumerate(frames[d]):
                sheet.alpha_composite(f, (c * mod.FW, r * mod.FH))
        sheet.save(os.path.join(OUT, "dummy60_%s.png" % act))
        j = {"image": "dummy60_%s.png" % act, "action": act, "frameWidth": mod.FW, "frameHeight": mod.FH, "frames": n,
             "directions": anim.DIRS, "frameDurationsMs": ms, "loop": old["loop"], "pivot": {"x": mod.PIV[0], "y": mod.PIV[1]},
             "pixelScale": 0.5, "oldTiming": {"frameDurationsMs": old["frameDurationsMs"], "framesMap": fmap},
             "note": "60라운드 Q4 샘플(검수용, assets 미반영). 구 프레임 시작 ms 불변"}
        ph = getattr(mod, "PHASES", {}).get(act)
        if ph:
            j["phaseFrames"] = {k: [i for o in v for i in fmap[o]] for k, v in ph.items()}
            j["impactFrame"] = j["phaseFrames"]["impact"][0]
        if act == "hurt":
            j["flashFrame"] = 0
        json.dump(j, open(os.path.join(OUT, "dummy60_%s.json" % act), "w"), ensure_ascii=False, indent=1)
        marks = strong = ()
        states = None
        if ph:
            pf = j["phaseFrames"]
            marks = {i for k, v in pf.items() if k != "recover" for i in v}
            strong = {pf["impact"][0]}
            states = [next((k for k, v in pf.items() if i in v), "") for i in range(n)]
        eprev.frames_x2(os.path.join(OUT, "preview_enemy_%s_x2.png" % act), "dummy60 %s" % act, frames, ms, mod.PIV,
                        marks=marks, strong=strong, states=states)
        eprev.gif_x3(os.path.join(OUT, "preview_enemy_%s_x3.gif" % act), frames, ms)
        print(act, n, "frames", ms)
    print("colors", len(allc))


if __name__ == "__main__":
    main(sys.argv[1:] or anim.ACTS)
