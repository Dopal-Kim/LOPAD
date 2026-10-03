"""1층 보스 '만취' v3 빌드 (54라운드 Q12 · 계약 §15) — python3 parts/art/work/boss1_v3/build.py [동작 ...]

산출:
  assets/sprites/bosses/v3/stage1_<동작>.png/.json   (128×192 · pixelScale 0.5 · 피벗 (64,184) · 행 = down/up/left/right)
  이 폴더: preview_<동작>_x2.png · preview_<동작>_x3.gif · stats.json
소품·fx 는 props.py, 시안·목업은 design.py. 결정적(난수 없음).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "enemies_v3"))
import eanim  # noqa: E402
import eprev  # noqa: E402
sys.path.insert(0, HERE)
import b1acts  # noqa: E402
from b1body import EMIT, FW, FH, PIV  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
OUT = os.path.join(ROOT, "assets/sprites/bosses/v3")
DIRS = eanim.DIRS
ORDER = ["idle", "walk", "hurt", "death", "attack", "slam", "drink", "drink_break", "stagger_dash", "fall", "kick", "throw",
         "throw_torch", "phase_drink"]
PALETTE = ("parts/art/palette/lopad.json (gray G00~15 + 1층 램프 16~27, 런타임 스왑 — 술·눈빛·볼·코·놋쇠만) + v2 재질 블록 SL·WD·PL "
           "(parts/art/work/v2_outer/palette_v2_proposal.json). 새 색 없음 — 주인공·적 v3 와 같은 재·호박 계열")
NOTE = ("v3 1층 보스 양조장주 '만취(滿醉)'(52라운드 Q2·Q5, 54라운드) · 128×192 도트 = 화면 64×96 · "
        "개념 gemini/concept_char/raw_boss_c.jpg(54라운드 참고 이미지 없이 1회 재생성) — 눈으로 참고만, 도트는 직접")


def sheet(frames):
    from PIL import Image
    n = len(frames["down"])
    im = Image.new("RGBA", (FW * n, FH * 4), (0, 0, 0, 0))
    for r, d in enumerate(DIRS):
        assert len(frames[d]) == n
        for c, f in enumerate(frames[d]):
            assert f.size == (FW, FH)
            im.alpha_composite(f, (c * FW, r * FH))
    return im


def starts(ms):
    out, t = [], 0
    for m in ms:
        out.append(t)
        t += m
    return out


def anchors(infos, key, fn=None):
    return {d: [(fn(inf) if fn else inf.get(key)) for inf in infos[d]] for d in DIRS}


def export(act, res):
    meta = b1acts.META[act]
    ms = meta["ms"]
    frames = {d: [im for im, _ in res[d]] for d in DIRS}
    infos = {d: [inf for _, inf in res[d]] for d in DIRS}
    for d in DIRS:
        assert len(frames[d]) == len(ms), (act, d, len(frames[d]), len(ms))
        for f in frames[d]:
            assert not any(0 < a < 255 for a in f.getchannel("A").getdata()), "반투명 픽셀"
    name = "stage1_%s" % act
    sheet(frames).save(os.path.join(OUT, name + ".png"))
    j = {
        "image": name + ".png", "action": act, "frameWidth": FW, "frameHeight": FH, "frames": len(ms), "directions": DIRS,
        "layout": "rows = directions (down, up, left, right), columns = frames", "frameIndex": "row * frames + column",
        "fps": round(1000.0 * len(ms) / sum(ms), 2), "frameDurationsMs": ms, "loop": meta["loop"],
        "pivot": {"x": PIV[0], "y": PIV[1]}, "pixelScale": 0.5, "version": "v3",
        "palette": PALETTE, "source": "parts/art/work/boss1_v3/build.py (54라운드 — 1층 보스 v3)", "note": NOTE,
        "emissiveColors": EMIT[:5] + ["#ffffff", "#fff4dc"],
        "emissiveNote": "눈빛(A23~25)·술 표면 반짝임·횃불 불꽃만 자체 발광. 조명 곱하기 뒤 원색으로 다시 그림(적 v3 와 같음)",
        "unitNote": "모든 좌표(pivot·*Anchors)는 이 시트 한 프레임 안의 도트(왼쪽 위 0,0). 논리 px = (도트 − pivot) × 0.5",
        "actionNote": meta.get("note", ""),
    }
    for k in ("phaseFrames", "holdFrame", "dashLoop", "gulpLoop", "staggerLoop", "downLoop", "impactFrame", "releaseFrame",
              "groundHitFrame", "roarFrame", "flashFrame", "stride", "events"):
        if k in meta:
            j[k] = meta[k]
    if "phaseFrames" in meta:
        st = starts(ms)
        j["phaseStartMs"] = {k: st[v[0]] for k, v in meta["phaseFrames"].items()}
        j["durationMs"] = sum(ms)
    if act in ("drink", "phase_drink", "drink_break"):
        j["cupAnchors"] = anchors(infos, "cup")
        j["cupAnchorsNote"] = ("프레임별 약점 잔 판정 사각형 {x, y, w, h}(시트 도트, 왼쪽 위 기준) — 잔 몸통(유리+술) 전체, 몸에 가려진 부분 포함. "
                               "visible = 화면에 12도트 이상 보임(뒷모습에서 머리에 가려지면 false — 판정은 유지 권장). 잔이 없는 프레임은 null")
    if act == "kick":
        j["footAnchors"] = anchors(infos, "foot")
        j["footAnchorsNote"] = "프레임별 차는 발(왼발) 발끝 [x, y] 시트 도트 — impactFrame 의 점이 술통에 힘이 들어가는 자리"
    if act == "throw":
        j["handAnchors"] = anchors(infos, None, lambda inf: [round(v, 1) for v in inf["cupTop"]] if inf.get("cupTop") else None)
        j["handAnchorsNote"] = "프레임별 잔 테 가운데 [x, y] 시트 도트 — releaseFrame 의 점이 술(투사체·웅덩이) 생성점. 오른손은 handR"
        j["handR"] = anchors(infos, "handR")
    if act == "throw_torch":
        j["handAnchors"] = anchors(infos, "torchTip")
        j["handAnchorsNote"] = "프레임별 횃불 끝(불꽃 밑) [x, y] 시트 도트, 횃불이 없는 프레임 null — releaseFrame 직전 점이 횃불 투사체(fx/v3/boss1_torch) 생성점"
        j["handL"] = anchors(infos, "handL")
    if act == "slam":
        j["impactAnchors"] = anchors(infos, "handL")
        j["impactAnchorsNote"] = "프레임별 내리찍는 왼 주먹 [x, y] 시트 도트 — impactFrame 의 점 근처 바닥이 boss_slam fx 중심"
    if act in ("attack", "stagger_dash"):
        j["bellyAnchors"] = anchors(infos, "belly")
        j["bellyAnchorsNote"] = "배 중심 [x, y] 시트 도트(돌진 충돌 판정 참고용)"
    if act == "hurt":
        j["flashFrame"] = 0
    with open(os.path.join(OUT, name + ".json"), "w") as f:
        json.dump(j, f, ensure_ascii=False, indent=1)
    return ms, frames, j


def colors(frames):
    cs = set()
    for lst in frames.values():
        for im in lst:
            cs |= {c[:3] for c in im.getdata() if c[3]}
    return cs


def main(acts):
    os.makedirs(OUT, exist_ok=True)
    res = eanim.render_all("b1acts", acts)
    sp = os.path.join(HERE, "stats.json")
    stats = json.load(open(sp)) if os.path.exists(sp) else {}
    allc = set()
    for act in acts:
        ms, frames, j = export(act, res[act])
        ph = j.get("phaseFrames") or {}
        strong = {v for k in ("impactFrame", "releaseFrame", "holdFrame", "groundHitFrame", "roarFrame") if k in j for v in [j[k]]}
        marks = {i for k, v in ph.items() for i in v if k not in ("recover", "finish", "rise", "stop")}
        states = [next((k for k, v in ph.items() if i in v), "") for i in range(len(ms))] if ph else None
        eprev.frames_x2(os.path.join(HERE, "preview_%s_x2.png" % act), "만취 %s" % act, frames, ms, PIV, marks=marks, strong=strong,
                        states=states)
        eprev.gif_x3(os.path.join(HERE, "preview_%s_x3.gif" % act), frames, ms, k=2)
        cs = colors(frames)
        allc |= cs
        stats[act] = {"frames": len(ms), "ms": ms, "totalMs": sum(ms), "colors": len(cs)}
        print(act, len(ms), "frames", len(cs), "colors")
        assert len(cs) <= 40, (act, len(cs))
    stats["_note"] = "colors = 시트(4방향) 불투명 색 수. 계약 §15 권장 40 이하"
    with open(sp, "w") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print("union colors", len(allc))


if __name__ == "__main__":
    main(sys.argv[1:] or ORDER)
