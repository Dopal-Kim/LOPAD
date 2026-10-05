"""61라운드 P3 — 신규 적 2종(독주 행상 peddler · 술통 짐꾼 porter) 빌드.

python3 parts/art/work/enemies61/enemy_build.py [peddler porter] [--acts=idle,attack] [--assets]
- 항상: out/<id>_<동작>.png/.json(격자, 검수용) + out/preview_<id>_<동작>_x2.png · _x3.gif
- --assets: assets/sprites/enemies/v3/<id>_<동작>.png/.json(격자) → 곧바로 atlas57 트림 아틀라스로 교체(계약 §19.5).
  그 뒤 엘리트 외곽선: python3 parts/art/work/bundle2/build.py --only elite (bundle2/elite.py ENEMIES 에 두 적 포함)
- 타이밍: 옛 시트가 없는 신규 적이므로 여기 TIMING 이 기준(60라운드 P1 원칙: 공격 10 · 피격 4 [70,30,30,30] · 사망 10).
"""
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
import kit61  # noqa: E402,F401  (경로 정리 — enemies_v3·floor1q60 import 가능)
import eanim as anim  # noqa: E402
import eprev  # noqa: E402
from PIL import Image  # noqa: E402

OUT = os.path.join(HERE, "out")
ASSETS = os.path.join(anim.ROOT, "assets/sprites/enemies/v3")
MODS = {"peddler": "peddler61", "porter": "porter61"}
ACTS = ["idle", "walk", "attack", "hurt", "death"]
PALETTE = ("parts/art/palette/lopad.json (gray G00~15 + 1층 램프 16~27, 런타임 스왑 — 술·불씨·놋쇠·발광만) + v2 재질 블록 SL·WD·PL "
           "(parts/art/work/v2_outer/palette_v2_proposal.json, 임시·고정색). 새 색 없음")
TIMING = {
    "peddler": {"idle": [220] * 6, "walk": [130] * 8, "attack": [100, 100, 100, 120, 130, 45, 60, 80, 100, 110],
                "hurt": [70, 30, 30, 30], "death": [90, 55, 55, 55, 55, 60, 60, 70, 70, 200]},
    "porter": {"idle": [240] * 6, "walk": [140] * 8, "attack": [80, 80, 110, 120, 140, 45, 90, 110, 110, 120],
               "hurt": [70, 30, 30, 30], "death": [100, 60, 60, 60, 60, 65, 65, 75, 75, 220]},
}
LOOP = {"idle": True, "walk": True, "attack": False, "hurt": False, "death": False}
NOTE = {
    "peddler": ("v3 독주 행상(61라운드 P3 신규) · 96×144 도트 = 화면 48×72 · 삿갓·등 술병 상자·매단 놋쇠 등(발광)·청회 목도리 · "
                "거리 두고 화염 술병 포물선 투척(보스 '불붙은 술' 예습). 이벤트 E1 떠돌이 행상 NPC 와 그림 공유(idle)"),
    "porter": ("v3 술통 짐꾼(61라운드 P3 신규) · 160×192 도트 = 화면 80×96(몸은 결사병급, 틀은 앞 술통·등 지게 때문에 넓음) · "
               "민머리 수건·맨팔·청회 조끼·지게에 예비 술통 · 앞 술통을 밀며 걷고, 뒤로 당겨 감았다가 굴려 보냄(보스 '술통 되치기' 예습)"),
}
ACTION_NAME = {"peddler": "throw", "porter": "push"}
STRIDE = {"peddler": {"px": 48, "cycleMs": 1040, "note": "발 한 주기 이동(도트, 제안) — 시스템이 실제 속도에 맞춰 재생 속도 조절(52 Q10)"},
          "porter": {"px": 52, "cycleMs": 1120,
                     "note": "발 한 주기 이동(발 진폭 12 × 4 × 몸 배율 1.1 ≈ 52 도트) = 앞 술통 반 바퀴(지름 약 33 도트 × π / 2). 이 비율로 재생하면 술통이 미끄러지지 않고 구른다"}}


def sheet_of(frames, fw, fh):
    n = len(frames["down"])
    im = Image.new("RGBA", (fw * n, fh * 4), (0, 0, 0, 0))
    for r, d in enumerate(anim.DIRS):
        for c, f in enumerate(frames[d]):
            assert f.size == (fw, fh)
            im.alpha_composite(f, (c * fw, r * fh))
    return im


def per_dir(infos, key):
    return {d: [inf.get(key) for inf in infos[d]] for d in anim.DIRS}


def meta_of(mod, act, ms, infos):
    eid = mod.ID
    j = {
        "image": "%s_%s.png" % (eid, act), "action": act, "frameWidth": mod.FW, "frameHeight": mod.FH, "frames": len(ms),
        "directions": anim.DIRS, "layout": "rows = directions (down, up, left, right), columns = frames",
        "frameIndex": "row * frames + column", "fps": round(1000.0 * len(ms) / sum(ms), 2), "frameDurationsMs": ms,
        "loop": LOOP[act], "pivot": {"x": mod.PIV[0], "y": mod.PIV[1]}, "pixelScale": 0.5,
        "palette": PALETTE, "source": "parts/art/work/enemies61/enemy_build.py (61라운드 P3 — 신규 적, 리그 enemies_v3 공용)",
        "note": NOTE[eid], "emissiveColors": kit61.EMISSIVE, "version": "v3-r61",
    }
    if act == "walk":
        j["stride"] = STRIDE[eid]
    if act == "hurt":
        j["flashFrame"] = 0
        j["hurtNote"] = "60라운드 P1 피격 4프레임 = [70,30,30,30], 0 = 흰빛 번쩍"
    if act == "death":
        j["deathNote"] = mod.DEATH_NOTE
    if act in ("idle", "walk", "hurt") and eid == "peddler":
        j["lampAnchors"] = per_dir(infos, "lamp")
        j["lampNote"] = "등 뒤 매단 놋쇠 등 중심(시트 도트). 광원 제안: #e8b858 반경 70 도트 세기 0.5 flicker {amp 0.15, hz 4} — 행상이 어둠 속에서 먼저 보이게"
    if act == "attack":
        ph = mod.PHASES["attack"]
        st = anim.starts(ms)
        j["actionName"] = ACTION_NAME[eid]
        j["phaseFrames"] = ph
        j["phaseStartMs"] = {k: st[v[0]] for k, v in ph.items()}
        j["releaseFrame"] = mod.RELEASE
        j["fireFrame"] = mod.RELEASE
        j["releaseAtMs"] = st[mod.RELEASE]
        j.update(mod.attack_meta(per_dir, infos, ms))
    return j


def build(eid, acts, to_assets):
    mod = importlib.import_module(MODS[eid])
    res = anim.render_all(MODS[eid], acts)
    allc = set()
    written = []
    for act in acts:
        ms = TIMING[eid][act]
        frames = {d: [im for im, _ in res[act][d]] for d in anim.DIRS}
        infos = {d: [inf for _, inf in res[act][d]] for d in anim.DIRS}
        for d in anim.DIRS:
            assert len(frames[d]) == len(ms), (eid, act, d, len(frames[d]), len(ms))
            for f in frames[d]:
                assert not any(0 < a < 255 for a in f.getchannel("A").get_flattened_data()), "반투명"
                allc |= {c[:3] for c in f.get_flattened_data() if c[3]}
        sh = sheet_of(frames, mod.FW, mod.FH)
        j = meta_of(mod, act, ms, infos)
        sh.save(os.path.join(OUT, "%s_%s.png" % (eid, act)))
        with open(os.path.join(OUT, "%s_%s.json" % (eid, act)), "w") as f:
            json.dump(j, f, ensure_ascii=False, indent=1)
        if to_assets:
            sh.save(os.path.join(ASSETS, "%s_%s.png" % (eid, act)))
            with open(os.path.join(ASSETS, "%s_%s.json" % (eid, act)), "w") as f:
                json.dump(j, f, ensure_ascii=False, indent=1)
            written.append("%s_%s" % (eid, act))
        marks = strong = ()
        states = None
        if act == "attack":
            pf = j["phaseFrames"]
            marks = {i for k, v in pf.items() if k not in ("reload", "follow") for i in v}
            strong = {mod.RELEASE}
            states = [next((k for k, v in pf.items() if i in v), "") for i in range(len(ms))]
        eprev.frames_x2(os.path.join(OUT, "preview_%s_%s_x2.png" % (eid, act)), "%s(61) %s" % (eid, act), frames, ms, mod.PIV,
                        marks=marks, strong=strong, states=states)
        eprev.gif_x3(os.path.join(OUT, "preview_%s_%s_x3.gif" % (eid, act)), frames, ms)
        print(eid, act, len(ms), ms)
    print(eid, "colors", len(allc))
    return written, len(allc)


def to_atlas(names):
    import importlib.util
    a57 = os.path.normpath(os.path.join(HERE, "../atlas57"))
    if a57 not in sys.path:
        sys.path.insert(0, a57)               # atlas57/build.py 가 같은 폴더의 verify 를 import
    spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(HERE, "../atlas57/build.py"))
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
    acts = ACTS
    for a in sys.argv[1:]:
        if a.startswith("--acts="):
            acts = a.split("=", 1)[1].split(",")
    os.makedirs(OUT, exist_ok=True)
    names = []
    for eid in (args or ["peddler", "porter"]):
        w, _ = build(eid, acts, "--assets" in sys.argv)
        names += w
    if names:
        to_atlas(names)
