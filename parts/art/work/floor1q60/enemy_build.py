"""60라운드 Q8 — 일반 적 3종(징집병·사수·결사병) 보강판 빌드.

python3 parts/art/work/floor1q60/enemy_build.py [dummy archer charger] [--acts idle,attack] [--assets]
- 항상: out/<id>60_<동작>.png/.json(격자, 검수·목업용) + out/preview_<id>_<동작>_x2.png · _x3.gif
- --assets: assets/sprites/enemies/v3/<id>_<동작>.png/.json 에 격자 시트로 쓴다(계약 §1·§11·§14 필드 = 53라운드 eexport 와 같음).
  바로 뒤에 atlas57 변환 필수: python3 parts/art/work/atlas57/build.py --in-place --cats enemies --only <id>_
  그 뒤 엘리트 외곽선 재생성: python3 parts/art/work/bundle2/build.py --only elite
- 타이밍: 구 프레임 하나를 n 개로 나누고 구 프레임 시작 ms 유지(eanim.check_timing assert) → 공격 단계·판정 시각 불변.
  공격 7(또는 8)→10 = [3,1,3,3], 피격 3→4 = [1,3], 대기·걷기·사망은 그대로.
원본 53라운드 빌드(enemies_v3/build.py)는 이 판을 덮어쓰지 않게 막아 두었다(--legacy).
"""
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "../enemies_v3")))
import erig  # noqa: E402,F401
if HERE in sys.path:
    sys.path.remove(HERE)
sys.path.insert(0, HERE)
import eanim as anim  # noqa: E402
import eprev  # noqa: E402
from PIL import Image  # noqa: E402

OUT = os.path.join(HERE, "out")
ASSETS = os.path.join(anim.ROOT, "assets/sprites/enemies/v3")
MODS = {"dummy": "drunk60", "archer": "musket60", "charger": "bulwark60"}
PALETTE = ("parts/art/palette/lopad.json (gray G00~15 + 1층 램프 16~27, 런타임 스왑 — 술·문장·불씨·눈빛·놋쇠만) + v2 재질 블록 SL·WD·PL "
           "(parts/art/work/v2_outer/palette_v2_proposal.json, 임시·고정색). 새 색 없음")
EMISSIVE = ["#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0"]
NOTE = {
    "dummy": "v3 징집병 = 주정뱅이 패거리(52라운드 Q4) · 96×144 도트 = 화면 48×72 · 60라운드 Q8 보강(명도 층·술통 나뭇결·해진 천·취한 흔들림·공격 잔상, 술병 반짝임 A23 발광, 천모자 청회)",
    "archer": "v3 사수(삼각모·화승총) · 96×144 도트 = 화면 48×72 · 60라운드 Q8 보강(외투 명도·놋쇠 단추·굵은 총·호박 휘장·두리번, 정면 조준 비스듬히)",
    "charger": "v3 결사병(통 투구·파비스·망치) · 128×176 도트 = 화면 64×88 · 60라운드 Q8 보강(투구 긁힘·방패 나뭇결·숨 쉬는 대기·쿵 걸음·내리찍기 잔상·바닥 금)",
}
STRONG = {"dummy": "impact", "archer": "fire", "charger": "charge"}
SPLITS = {"attack": "ATTACK_SPLIT", "hurt": "HURT_SPLIT"}


def timing(mod, act):
    old = anim.old_json(mod.ID, act)
    sp = getattr(mod, SPLITS[act]) if act in SPLITS else (anim.SPLIT[act] or [1] * old["frames"])
    ms, fmap = anim.split_ms(old["frameDurationsMs"], sp)
    anim.check_timing(mod.ID, act, old["frameDurationsMs"], ms, fmap)
    return old, ms, fmap


def sheet_of(frames, fw, fh):
    n = len(frames["down"])
    im = Image.new("RGBA", (fw * n, fh * 4), (0, 0, 0, 0))
    for r, d in enumerate(anim.DIRS):
        for c, f in enumerate(frames[d]):
            assert f.size == (fw, fh)
            im.alpha_composite(f, (c * fw, r * fh))
    return im


def meta_of(mod, act, old, ms, fmap, infos):
    eid = mod.ID
    j = {
        "image": "%s_%s.png" % (eid, act), "action": act, "frameWidth": mod.FW, "frameHeight": mod.FH, "frames": len(ms),
        "directions": anim.DIRS, "layout": "rows = directions (down, up, left, right), columns = frames",
        "frameIndex": "row * frames + column", "fps": round(1000.0 * len(ms) / sum(ms), 2), "frameDurationsMs": ms,
        "loop": old["loop"], "pivot": {"x": mod.PIV[0], "y": mod.PIV[1]}, "pixelScale": 0.5,
        "palette": PALETTE, "source": "parts/art/work/floor1q60/enemy_build.py (60라운드 Q8 — 적 v3 보강, 원본 enemies_v3 53라운드)",
        "note": NOTE[eid], "emissiveColors": EMISSIVE,
        "oldTiming": {"sheet": ("enemies/v2/" if eid == "charger" else "enemies/") + "%s_%s.json" % (eid, act),
                      "sheetDeleted": "53라운드 삭제됨(보관) — 사본 parts/art/work/enemies_v3/old_sheets/%s%s_%s.json"
                                      % (eid, "_v2" if eid == "charger" else "", act),
                      "frames": old["frames"], "frameDurationsMs": old["frameDurationsMs"], "framesMap": fmap,
                      "note": "구 프레임 k 의 시작 ms = 새 프레임 framesMap[k][0] 의 시작 ms (assert). 전체 길이 같음"},
    }
    ph = getattr(mod, "PHASES", {}).get(act)
    if ph:
        pf = {k: [i for o in v for i in fmap[o]] for k, v in ph.items()}
        j["phaseFrames"] = pf
        j["phaseStartMs"] = {k: anim.starts(ms)[v[0]] for k, v in pf.items()}
        if eid == "charger":
            j["phaseNote"] = "v2 phaseFrames(telegraph 0 · charge 1 · smash 2 · recover 3)와 같은 시각. 돌진 거리·시간은 시스템"
            j["impactFrame"] = pf["smash"][0]
            j["hammerFaceAnchors"] = {d: [inf.get("hammerFace") for inf in infos[d]] for d in anim.DIRS}
        if eid == "archer":
            j["fireFrame"] = pf["fire"][0]
            j["muzzleAnchors"] = {d: [inf.get("muzzle") for inf in infos[d]] for d in anim.DIRS}
            j["muzzleNote"] = "프레임별 총구 위치(시트 도트 좌표, 총을 놓친 프레임은 null) — 탄환 생성점. 발사 = fireFrame"
        if eid == "dummy":
            j["impactFrame"] = pf["impact"][0]
    if act == "hurt":
        j["flashFrame"] = 0
    return j


def build(eid, acts, to_assets):
    modname = MODS[eid]
    mod = importlib.import_module(modname)
    res = anim.render_all(modname, acts)
    allc = set()
    report = {}
    for act in acts:
        old, ms, fmap = timing(mod, act)
        frames = {d: [im for im, _ in res[act][d]] for d in anim.DIRS}
        infos = {d: [inf for _, inf in res[act][d]] for d in anim.DIRS}
        for d in anim.DIRS:
            assert len(frames[d]) == len(ms), (eid, act, d, len(frames[d]), len(ms))
            for f in frames[d]:
                assert not any(0 < a < 255 for a in f.getchannel("A").get_flattened_data()), "반투명"
                allc |= {c[:3] for c in f.get_flattened_data() if c[3]}
        sh = sheet_of(frames, mod.FW, mod.FH)
        j = meta_of(mod, act, old, ms, fmap, infos)
        sh.save(os.path.join(OUT, "%s60_%s.png" % (eid, act)))
        jj = dict(j, image="%s60_%s.png" % (eid, act))
        json.dump(jj, open(os.path.join(OUT, "%s60_%s.json" % (eid, act)), "w"), ensure_ascii=False, indent=1)
        if to_assets:
            sh.save(os.path.join(ASSETS, "%s_%s.png" % (eid, act)))
            with open(os.path.join(ASSETS, "%s_%s.json" % (eid, act)), "w") as f:
                json.dump(j, f, ensure_ascii=False, indent=1)
        pf = j.get("phaseFrames")
        marks = strong = ()
        states = None
        if pf:
            marks = {i for k, v in pf.items() if k not in ("recover", "lower") for i in v}
            strong = {pf[STRONG[eid]][0]}
            if eid == "charger":
                strong = strong | {pf["smash"][0]}
            states = [next((k for k, v in pf.items() if i in v), "") for i in range(len(ms))]
        eprev.frames_x2(os.path.join(OUT, "preview_%s_%s_x2.png" % (eid, act)), "%s(60) %s" % (eid, act), frames, ms, mod.PIV,
                        marks=marks, strong=strong, states=states)
        eprev.gif_x3(os.path.join(OUT, "preview_%s_%s_x3.gif" % (eid, act)), frames, ms)
        report[act] = (len(ms), ms)
        print(eid, act, len(ms), ms)
    print(eid, "colors", len(allc))
    return report, len(allc)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    acts = anim.ACTS
    for a in sys.argv[1:]:
        if a.startswith("--acts="):
            acts = a.split("=", 1)[1].split(",")
    os.makedirs(OUT, exist_ok=True)
    for eid in (args or ["dummy", "archer", "charger"]):
        build(eid, acts, "--assets" in sys.argv)
