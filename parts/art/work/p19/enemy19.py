"""P19 새 적 2종 빌드 — drummer(깃발 고수) · bomber(술배 자폭병) × 동작 → 격자 → atlas57 트림 아틀라스 + _rim(차가운 림, r62b 규칙).

python3 parts/art/work/p19/enemy19.py [drummer bomber] [--acts=idle,attack] [--assets]
- 항상: out/<id>_<동작>.png/.json(격자) + out/preview_<id>_<동작>_x2.png · _x3.gif
- --assets: assets/sprites/enemies/v3/<id>_<동작>(+_rim) 격자 → 트림 아틀라스(계약 §19.5).
타이밍: 60라운드 P1 원칙(공격 10 · 피격 4 [70,30,30,30] · 사망 10) + bomber swell 6 · explode 6.
"""
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(WORK, "enemies61"))
import kit61  # noqa: E402,F401
import eanim as anim  # noqa: E402
import eprev  # noqa: E402
sys.path.insert(0, HERE)
from PIL import Image  # noqa: E402

OUT = os.path.join(HERE, "out")
ASSETS = os.path.join(anim.ROOT, "assets/sprites/enemies/v3")
MODS = {"drummer": "drummer19", "bomber": "bomber19"}
ACTS = {"drummer": ["idle", "walk", "attack", "hurt", "death"], "bomber": ["idle", "walk", "attack", "hurt", "death", "swell", "explode"]}
PALETTE = ("parts/art/palette/lopad.json (gray G00~15 + 1층 램프 16~27 — 북통·깃발·술독 띠·발광) + v2 재질 블록 SL·WD·PL. 새 색 없음")
TIMING = {
    "drummer": {"idle": [200] * 6, "walk": [110] * 8, "attack": [90, 90, 70, 60, 70, 60, 70, 60, 140, 120],
                "hurt": [70, 30, 30, 30], "death": [90, 55, 55, 55, 55, 60, 60, 70, 70, 200]},
    "bomber": {"idle": [160] * 6, "walk": [90] * 8, "attack": [100] * 10, "hurt": [70, 30, 30, 30],
               "death": [90, 55, 55, 55, 55, 60, 60, 70, 70, 200], "swell": [80] * 6, "explode": [40, 40, 80, 100, 120, 400]},
}
LOOP = {"idle": True, "walk": True, "attack": False, "hurt": False, "death": False, "swell": True, "explode": False}
NOTE = {
    "drummer": ("v3 깃발 고수(P19 C 새 적) · 96×144 = 화면 48×72 · 등에 꽂은 잔(盞) 깃발(머리 위 실루엣)·배 앞 붉은 북·북채 둘·머리띠. "
                "뒤에서 북을 쳐 주변 적 공속 +25% 오라, 도망 다님 — '먼저 잡을 대상'"),
    "bomber": ("v3 술배 자폭병(P19 C 새 적) · 96×144 · 배 앞 갈색 술독 + 굵은 호박 띠(위험물 표지) + 도화선 불티(발광) · 붉은 두건 · 웃는 입. "
               "달려와 1초 예고(attack) 뒤 폭발(explode). 쳐서 날리면 swell 루프 → 날아간 자리에서 폭발"),
}
STRIDE = {"drummer": {"px": 44, "cycleMs": 880, "note": "발 한 주기 이동(도트, 제안)"},
          "bomber": {"px": 48, "cycleMs": 720, "note": "발 한 주기 이동(도트, 제안) — 빠른 돌진"}}
SRC = "parts/art/work/p19/enemy19.py (P19 1-A 새 적, 리그 enemies_v3 공용)"


def sheet_of(frames, fw, fh):
    n = len(frames["down"])
    im = Image.new("RGBA", (fw * n, fh * 4), (0, 0, 0, 0))
    for r, d in enumerate(anim.DIRS):
        for c, f in enumerate(frames[d]):
            im.alpha_composite(f, (c * fw, r * fh))
    return im


def per_dir(infos, key):
    return {d: [inf.get(key) for inf in infos[d]] for d in anim.DIRS}


def meta_of(mod, eid, act, ms, infos):
    j = {"image": "%s_%s.png" % (eid, act), "action": act, "frameWidth": mod.FW, "frameHeight": mod.FH, "frames": len(ms),
         "directions": anim.DIRS, "layout": "rows = directions (down, up, left, right), columns = frames", "frameIndex": "row * frames + column",
         "fps": round(1000.0 * len(ms) / sum(ms), 2), "frameDurationsMs": ms, "loop": LOOP[act],
         "pivot": {"x": mod.PIV[0], "y": mod.PIV[1]}, "pixelScale": 0.5, "palette": PALETTE, "source": SRC, "note": NOTE[eid],
         "emissiveColors": ["#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0", "#ffffff"], "version": "v3-p19"}
    if act == "walk":
        j["stride"] = STRIDE[eid]
    if act == "hurt":
        j["flashFrame"] = 0
        j["hurtNote"] = "60라운드 P1 피격 4프레임 = [70,30,30,30], 0 = 흰빛 번쩍"
    if act == "death":
        j["deathNote"] = mod.DEATH_NOTE
    if act == "attack":
        st = anim.starts(ms)
        j["phaseFrames"] = mod.PHASES["attack"]
        j["phaseStartMs"] = {k: st[v[0]] for k, v in mod.PHASES["attack"].items()}
        j.update(mod.attack_meta(per_dir, infos, ms))
    if eid == "bomber" and act in ("idle", "walk", "swell"):
        j["fuseAnchors"] = per_dir(infos, "fuse")
        j["fuseLight"] = {"color": "#eecc78", "radius": 60, "intensity": 0.5, "flicker": {"amp": 0.4, "hz": 12},
                          "note": "도화선 불티 광원 제안(도트) — 어둠 속에서도 '터질 것'이 먼저 보이게"}
    if act == "swell":
        j["swellNote"] = "중·강 넉백으로 날아가는 동안·불붙은 동안 루프. 착지·벽꽝·볼링 순간 explode(시스템)"
    if act == "explode":
        j["explodeNote"] = ("0 번쩍(부푼 몸 흰빛) · 1 하얗게 · 2~5 몸 없음 + 바닥 독 파편·술 자국. "
                            "프레임 2 시작에 fx/v3/react_explode_m 을 피벗에(HAZARD_EXPLODED kind 'bottle' 또는 새 'bomber' — 시스템)")
        j["detonateFrame"] = 2
    return j


def build(eid, acts, to_assets):
    mod = importlib.import_module(MODS[eid])
    res = anim.render_all(MODS[eid], acts)
    written = []
    for act in acts:
        ms = TIMING[eid][act]
        frames = {d: [im for im, _ in res[act][d]] for d in anim.DIRS}
        infos = {d: [inf for _, inf in res[act][d]] for d in anim.DIRS}
        for d in anim.DIRS:
            assert len(frames[d]) == len(ms), (eid, act, d, len(frames[d]), len(ms))
        sh = sheet_of(frames, mod.FW, mod.FH)
        j = meta_of(mod, eid, act, ms, infos)
        os.makedirs(OUT, exist_ok=True)
        sh.save(os.path.join(OUT, "%s_%s.png" % (eid, act)))
        if to_assets:
            sh.save(os.path.join(ASSETS, "%s_%s.png" % (eid, act)))
            with open(os.path.join(ASSETS, "%s_%s.json" % (eid, act)), "w") as f:
                json.dump(j, f, ensure_ascii=False, indent=1)
            written.append("%s_%s" % (eid, act))
        eprev.frames_x2(os.path.join(OUT, "preview_%s_%s_x2.png" % (eid, act)), "%s(P19) %s" % (eid, act), frames, ms, mod.PIV)
        eprev.gif_x3(os.path.join(OUT, "preview_%s_%s_x3.gif" % (eid, act)), frames, ms)
        print(eid, act, len(ms))
    return written


def rims(names):
    """r62b rim_frame 규칙 그대로 _rim 시트(같은 틀·피벗·프레임)."""
    sys.path.insert(0, os.path.join(WORK, "r62b"))
    from rim import rim_frame
    from common import COLD_RIM, hexc
    import b2
    b2.WRITTEN.clear()
    for n in names:
        jp = os.path.join(ASSETS, n + ".json")
        m = json.load(open(jp))
        g = Image.open(os.path.join(ASSETS, n + ".png")).convert("RGBA")
        fw, fh, cnt = m["frameWidth"], m["frameHeight"], m["frames"]
        frames = []
        for r in range(4):
            for c in range(cnt):
                frames.append(rim_frame(g.crop((c * fw, r * fh, c * fw + fw, r * fh + fh)), m["pivot"]["y"]))
        e = n.split("_")[0]
        meta = {"directions": m["directions"], "layout": m["layout"], "pivot": m["pivot"], "role": "rim_cold", "baseSheet": "enemies/v3/" + n,
                "enemy": e, "overlayOf": "enemies/v3/" + n, "sameFrameAs": "enemies/v3/" + n,
                "draw": "적 스프라이트 바로 위(같은 프레임 번호·피벗·flip·scale). 실루엣 바깥 1도트. 엘리트는 `_elite` 만(계약 §31.3)",
                "rimColors": [hexc(c) for c in COLD_RIM], "paletteSwap": "none", "version": "v3-p19",
                "source": SRC + " · r62b/rim.py rim_frame"}
        b2.write_sheet("enemies", n + "_rim", frames, fw, fh, meta, rows=4, durations=m["frameDurationsMs"], loop=m.get("loop", False))
    return b2.to_atlas()


def to_atlas(names):
    import importlib.util
    a57 = os.path.join(WORK, "atlas57")
    if a57 not in sys.path:
        sys.path.insert(0, a57)
    spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(a57, "build.py"))
    ab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ab)
    import shutil
    tmp = os.path.join(HERE, "_atlas_tmp")
    for n in names:
        jp, pp = os.path.join(ASSETS, n + ".json"), os.path.join(ASSETS, n + ".png")
        res = ab.convert_sheet(pp, jp, tmp, 2, 4096, True)
        ab.apply_in_place(res, tmp, ASSETS, pp, jp, 4096)
        print("atlas", n, res["srcSize"], [(w, h) for _, w, h in res["pages"]])
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    names = []
    for eid in (args or ["drummer", "bomber"]):
        acts = ACTS[eid]
        for a in sys.argv[1:]:
            if a.startswith("--acts="):
                acts = a.split("=", 1)[1].split(",")
        names += build(eid, acts, "--assets" in sys.argv)
    if names:
        for cat, name, src, pages in rims(names):
            print("rim", name, src, pages)
        to_atlas(names)
