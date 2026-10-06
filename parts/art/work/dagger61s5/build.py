#!/usr/bin/env python3
"""61 단계 5 (P13 §2) 단검 재디자인 '재 발톱' — 무기와 이펙트를 한 디자인 언어로. 결정적, Gemini 미사용(도트 직접).

단계(인자 없으면 전부, 순서대로):
  weapons   손에 든 무기 11시트 → out/grid/weapons/v3                                  (weapons.py · blade.py)
  overlays  각성 _awaken 11 + v4 갈래 3 × (a1·a2·a2_glow) × 11 → out/grid/weapons/{v3,v4}  (overlays.py)
  fx        찌르기 계열 50시트(연격·가속·각성·갈래·쌍격 3타·난타·등 뒤·적중) → out/grid/fx/v3 (fx_thrust.py)
  misc      그림자 걸음·투척·부채 투척·낙인 4·꽂힌 날·쌍격 분신·백귀·각성 순간 11시트            (fx_misc.py)
  looks     미리보기 정지 그림 16장 + looks/dagger.json → assets/sprites/looks (바로 씀)      (looks.py)
  publish   out/grid → assets 트림 아틀라스(atlas57 convert_sheet·apply_in_place, 전 프레임 대조). 임시 폴더 out/_atlas_tmp_dagger61s5 전용
  memory    아틀라스 페이지 RGBA MB 전/후(고치기 전 = git BEFORE_REV) → memory.json (상한 ×1.2)
  preview   preview_*.png 전/후 비교                                                    (preview.py)
고치기 전 원본은 git BEFORE_REV 에서 out/before/ 로 풀어 읽는다(다시 돌려도 덧칠이 겹치지 않음).
사용: python3 parts/art/work/dagger61s5/build.py [단계...]
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

STEPS = {
    "weapons": "import weapons as W; W.build()",
    "overlays": "import overlays as O; O.build()",
    "fx": "import fx_build as F; F.thrust_family()",
    "misc": "import fx_build as F; F.misc()",
    "looks": "import looks as L; L.build()",
    "publish": "import d5; d5.publish()",
    "memory": "import build as B; B.memory()",
    "preview": "import preview as P; P.build()",
}


def memory():
    import d5
    before = d5.before_root()
    rows = []
    groups = {}
    for cat, sub, name in d5.staged():
        a = d5.page_mb(os.path.join(d5.SPR, cat, sub, name + ".json"))
        b = d5.page_mb(os.path.join(before, cat, sub, name + ".json"))
        if sub == "v4":
            g = "weapons/v4 " + name.split("_")[1]
        elif cat == "weapons":
            g = "weapons/v3 " + ("awaken" if name.endswith("_awaken") else "base")
        else:
            g = "fx/v3"
        G = groups.setdefault(g, [0.0, 0.0])
        G[0] += b
        G[1] += a
        rows.append(dict(sheet="%s/%s/%s" % (cat, sub, name), beforeMB=round(b, 3), afterMB=round(a, 3), ratio=round(a / b, 3) if b else None))
    tb = sum(v[0] for v in groups.values())
    ta = sum(v[1] for v in groups.values())
    out = dict(rule="아틀라스 페이지 RGBA(GPU 추정) 고치기 전 대비 ×1.2 이내", totalBeforeMB=round(tb, 2), totalAfterMB=round(ta, 2),
               totalRatio=round(ta / tb, 3), groups={k: dict(beforeMB=round(v[0], 2), afterMB=round(v[1], 2), ratio=round(v[1] / v[0], 3))
                                                    for k, v in sorted(groups.items())}, sheets=rows)
    with open(os.path.join(HERE, "memory.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for k, v in out["groups"].items():
        print("%-22s %7.2f → %7.2f MB  ×%.3f" % (k, v["beforeMB"], v["afterMB"], v["ratio"]))
    print("합계 %.2f → %.2f MB ×%.3f" % (tb, ta, ta / tb))
    assert ta / tb <= 1.2, "메모리 1.2배 초과"


def run(step):
    t0 = time.time()
    subprocess.run([sys.executable, "-W", "ignore", "-c", STEPS[step]], cwd=HERE, check=True)
    print("== %s %.1fs" % (step, time.time() - t0), flush=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a in STEPS] or list(STEPS)
    for s in args:
        run(s)
