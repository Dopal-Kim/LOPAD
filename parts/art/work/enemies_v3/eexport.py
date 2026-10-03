"""적 v3 시트·JSON 내보내기 + 타이밍 assert → assets/sprites/enemies/v3/<id>_<동작>.png/json (계약 §1·§11·§13)."""
import json
import os

import eanim as anim

OUT = os.path.join(anim.ROOT, "assets/sprites/enemies/v3")
PALETTE = ("parts/art/palette/lopad.json (gray G00~15 + 1층 램프 16~27, 런타임 스왑 — 술·문장·불씨·눈빛만) + v2 재질 블록 SL·WD·PL "
           "(parts/art/work/v2_outer/palette_v2_proposal.json, 임시·고정색). 새 색 없음")
EMISSIVE = ["#e2a33c", "#e8b858", "#eecc78", "#f4de9b", "#faeec0"]
NOTE = {
    "dummy": "v3 징집병 = 주정뱅이 패거리(52라운드 Q4) · 53라운드 Q33 주인공과 같은 크기 96×144 도트 = 화면 48×72. 개념 gemini/concept_char/raw_enemies_b.jpg",
    "archer": "v3 사수(삼각모·화승총) · 53라운드 Q33 주인공과 같은 크기 96×144 도트 = 화면 48×72. 개념 gemini/concept_char/raw_enemies_b.jpg",
    "charger": "v3 결사병(통 투구·파비스·망치) · 53라운드 Q33 '조금 더 크게' = 몸 1.15배(임시), 128×176 도트 = 화면 64×88. 개념 gemini/concept_char/raw_enemies_b.jpg",
}
STRONG = {"dummy": "impact", "archer": "fire", "charger": "charge"}


def sheet(frames_by_dir, fw, fh):
    from PIL import Image
    n = len(frames_by_dir["down"])
    im = Image.new("RGBA", (fw * n, fh * 4), (0, 0, 0, 0))
    for r, d in enumerate(anim.DIRS):
        assert len(frames_by_dir[d]) == n
        for c, f in enumerate(frames_by_dir[d]):
            assert f.size == (fw, fh)
            im.alpha_composite(f, (c * fw, r * fh))
    return im


def phases_new(mod, act, fmap):
    ph = getattr(mod, "PHASES", {}).get(act)
    if not ph:
        return None
    return {k: [i for o in v for i in fmap[o]] for k, v in ph.items()}


def export(mod, act, res):
    old, sp = anim.split_of(mod, act)
    ms, fmap = anim.split_ms(old["frameDurationsMs"], sp)
    anim.check_timing(mod.ID, act, old["frameDurationsMs"], ms, fmap)
    frames = {d: [im for im, _ in res[d]] for d in anim.DIRS}
    infos = {d: [inf for _, inf in res[d]] for d in anim.DIRS}
    for d in anim.DIRS:
        assert len(frames[d]) == len(ms), (mod.ID, act, d, len(frames[d]), len(ms))
        for f in frames[d]:
            assert not any(0 < a < 255 for a in f.getchannel("A").getdata()), "반투명 픽셀"
    name = "%s_%s" % (mod.ID, act)
    sheet(frames, mod.FW, mod.FH).save(os.path.join(OUT, name + ".png"))
    j = {
        "image": name + ".png", "action": act, "frameWidth": mod.FW, "frameHeight": mod.FH, "frames": len(ms),
        "directions": anim.DIRS, "layout": "rows = directions (down, up, left, right), columns = frames",
        "frameIndex": "row * frames + column", "fps": round(1000.0 * len(ms) / sum(ms), 2), "frameDurationsMs": ms,
        "loop": old["loop"], "pivot": {"x": mod.PIV[0], "y": mod.PIV[1]}, "pixelScale": 0.5,
        "palette": PALETTE, "source": "parts/art/work/enemies_v3/build.py (53라운드 Q33 — 적 v3)", "note": NOTE[mod.ID],
        "emissiveColors": EMISSIVE,
        "oldTiming": {"sheet": ("enemies/v2/" if mod.ID == "charger" else "enemies/") + "%s_%s.json" % (mod.ID, act),
                      "sheetDeleted": "53라운드 삭제됨(보관) — 사본 parts/art/work/enemies_v3/old_sheets/%s%s_%s.json"
                                      % (mod.ID, "_v2" if mod.ID == "charger" else "", act),
                      "frames": old["frames"], "frameDurationsMs": old["frameDurationsMs"], "framesMap": fmap,
                      "note": "구 프레임 k 의 시작 ms = 새 프레임 framesMap[k][0] 의 시작 ms (assert). 전체 길이 같음"},
    }
    ph = phases_new(mod, act, fmap)
    if ph:
        j["phaseFrames"] = ph
        key = STRONG[mod.ID]
        j["phaseStartMs"] = {k: anim.starts(ms)[v[0]] for k, v in ph.items()}
        if mod.ID == "charger":
            j["phaseNote"] = "v2 phaseFrames(telegraph 0 · charge 1 · smash 2 · recover 3)와 같은 시각. 돌진 거리·시간은 시스템"
        if mod.ID == "archer":
            j["fireFrame"] = ph["fire"][0]
            j["muzzleAnchors"] = {d: [inf.get("muzzle") for inf in infos[d]] for d in anim.DIRS}
            j["muzzleNote"] = "프레임별 총구 위치(시트 도트 좌표, 총을 놓친 프레임은 null) — 탄환 생성점. 발사 = fireFrame"
        if mod.ID == "dummy":
            j["impactFrame"] = ph["impact"][0]
        if mod.ID == "charger":
            j["impactFrame"] = ph["smash"][0]
            j["hammerFaceAnchors"] = {d: [inf.get("hammerFace") for inf in infos[d]] for d in anim.DIRS}
    if act == "hurt":
        j["flashFrame"] = 0
    with open(os.path.join(OUT, name + ".json"), "w") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
    return ms, fmap, ph, frames


def colors(frames_by_act):
    cs = set()
    for fr in frames_by_act.values():
        for lst in fr.values():
            for im in lst:
                cs |= {c[:3] for c in im.getdata() if c[3]}
    return cs
