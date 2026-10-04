#!/usr/bin/env python3
"""57라운드 빌드 축 아트(57 Q39 '특성·갈래 본격 디벨롭') — 결정적, Gemini 미사용.

  combo    1단 갈래 '연격 한 타 변화' fx 7      (fx_combo.py)
  branch   2단 갈래 전용 fx 26(16갈래)           (fx_branch.py)
  awaken   최종 각성 시그니처 fx 4               (fx_awaken.py)
  overlay  최종 각성 무기 변형 오버레이 60       (fx_awaken.py — weapons/v3/<무기 시트>_awaken)
  status   상태·세트·저주 표시 fx 15             (fx_status.py)
  preview  미리보기 PNG(이 폴더 preview_*.png)·GIF(gif/)
  publish  격자 원본(out/grid) → assets 트림 아틀라스(계약 §19.5 — atlas57/build.py --in-place 와 같은 함수: 격자 → 전 프레임 대조 → 통과 시 덮어씀).
           이 빌드가 만든 시트만(out/grid 목록). 임시 폴더 out/_atlas_tmp
  verify   atlas57/verify.py 형식 점검 + 보관 격자와 전 프레임 픽셀 대조(이 빌드 시트만)
사용: python3 parts/art/work/build57/build.py [단계...]   (인자 없으면 전부, 순서대로)
다른 작업과 겹치지 않게: 새 시트 이름만 쓴다(기존 assets 시트를 덮지 않음 — publish 가 확인). 칼 찌르기 검기 오버레이(katana_thrust_ki1~3)는 다른 작업 몫.
"""
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets/sprites")
STAGE = os.path.join(HERE, "out", "grid")
OWN_VERSION = "v3-r57-build"


def staged():
    out = []
    for cat in ("fx", "weapons"):
        d = os.path.join(STAGE, cat)
        if os.path.isdir(d):
            out += [(cat, f[:-5]) for f in sorted(os.listdir(d)) if f.endswith(".json")]
    return out


def step_publish():
    sys.path.insert(0, os.path.join(WORK, "atlas57"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(WORK, "atlas57", "build.py"))
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    tmp = os.path.join(HERE, "out", "_atlas_tmp")
    log = []
    for cat, name in staged():
        dst = os.path.join(SPR, cat, "v3")
        jp, pp = os.path.join(dst, name + ".json"), os.path.join(dst, name + ".png")
        if os.path.exists(jp):                     # 남의 시트를 덮지 않는다
            v = json.load(open(jp, encoding="utf-8")).get("version")
            assert v == OWN_VERSION, (name, "assets 에 다른 작업의 같은 이름 시트가 있음", v)
        shutil.copy2(os.path.join(STAGE, cat, name + ".png"), pp)
        shutil.copy2(os.path.join(STAGE, cat, name + ".json"), jp)
        od = os.path.join(tmp, cat)
        os.makedirs(od, exist_ok=True)
        res = A.convert_sheet(pp, jp, od, 2, 4096, True)
        A.apply_in_place(res, od, dst, pp, jp, 4096)
        m = json.load(open(jp, encoding="utf-8"))
        assert m["framesPerDirection"] == m["atlas"]["grid"]["columns"], name     # 계약 §19.5(57 Q38)
        log.append(dict(cat=cat, name=name, src=res["srcSize"], pages=[[n, w, h] for n, w, h in res["pages"]],
                        gpuBeforeMB=round(res["gpuBefore"] / 2 ** 20, 2), gpuAfterMB=round(res["gpuAfter"] / 2 ** 20, 2),
                        empty=res["empty"], deduped=res["deduped"], noTrim=bool(m["atlas"].get("noTrim"))))
    shutil.rmtree(tmp, ignore_errors=True)
    with open(os.path.join(HERE, "publish_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    print("publish %d 시트 · GPU %.1f → %.1f MB" % (len(log), sum(x["gpuBeforeMB"] for x in log), sum(x["gpuAfterMB"] for x in log)))


def step_verify():
    sys.path.insert(0, os.path.join(WORK, "atlas57"))
    import verify as V
    import gridsheet
    from PIL import Image
    bad = 0
    lines = []
    for cat, name in staged():
        jp = os.path.join(SPR, cat, "v3", name + ".json")
        m = json.load(open(jp, encoding="utf-8"))
        grid = gridsheet.load_meta(jp)
        errs = V.check_format(grid, m, 4096)
        if "atlas" not in m:
            errs.append("격자 그대로(publish 전)")
        if m.get("framesPerDirection") != m.get("atlas", {}).get("grid", {}).get("columns"):
            errs.append("framesPerDirection ≠ atlas.grid.columns")
        for p in (m.get("textures") or [{"image": m["meta"]["image"]}]):
            if not os.path.exists(os.path.join(SPR, cat, "v3", p["image"])):
                errs.append("페이지 없음 " + p["image"])
        gp = os.path.join(STAGE, cat, name + ".png")
        if not errs:
            gm = json.load(open(gp[:-4] + ".json", encoding="utf-8"))
            nbad = V.compare_sheet(Image.open(gp).convert("RGBA"), gm, m, os.path.join(SPR, cat, "v3"))
            if nbad:
                errs.append("픽셀 불일치 %d 프레임" % nbad)
        lines.append("%-8s %-40s %s" % (cat, name, "OK" if not errs else errs[:3]))
        bad += bool(errs)
    lines.append("검사 %d 시트 · 오류 %d" % (len(staged()), bad))
    open(os.path.join(HERE, "verify_log.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(lines[-1])
    assert bad == 0


def step_preview():
    sys.path.insert(0, HERE)
    import pv57
    import pv_ov
    import fx_combo
    import fx_branch
    import fx_awaken
    import fx_status
    pv57.sheet_preview(fx_combo.NAMES, os.path.join(HERE, "preview_1_combo.png"))
    nb = [n for n in fx_branch.NAMES if n != "katana_cleave_crack"]
    pv57.sheet_preview(nb[:13], os.path.join(HERE, "preview_2_branch_a.png"))
    pv57.sheet_preview(nb[13:] + ["katana_cleave_crack"], os.path.join(HERE, "preview_2_branch_b.png"))
    pv57.sheet_preview(fx_awaken.SIG, os.path.join(HERE, "preview_3_awaken_fx.png"))
    pv_ov.main(os.path.join(HERE, "preview_3_awaken_weapons.png"),
               ["katana_rise", "katana_carry_idle", "greatsword_sweep_cw", "greatsword_carry_idle", "dagger_combo1", "dagger_carry_idle",
                "bow_draw_hold", "bow_carry_idle"], dirs=("right", "down"))
    pv57.sheet_preview(fx_status.NAMES, os.path.join(HERE, "preview_4_status.png"))
    for f in os.listdir(HERE):                     # 작업 중 임시 미리보기 정리
        if f.startswith("preview_fx_") and f.endswith(".png"):
            os.remove(os.path.join(HERE, f))


STEPS = {
    "combo": "import run; run.build('fx_combo')",
    "branch": "import run; run.build('fx_branch')",
    "awaken": "import run; run.build('fx_awaken')",
    "overlay": "import ov_run; ov_run.build()",
    "status": "import run; run.build('fx_status')",
    "preview": "import build; build.step_preview()",
    "publish": "import build; build.step_publish()",
    "verify": "import build; build.step_verify()",
}


def run(step):
    t0 = time.time()
    subprocess.run([sys.executable, "-W", "ignore", "-c", STEPS[step]], cwd=HERE, check=True)
    print("== %s %.1fs" % (step, time.time() - t0))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a in STEPS] or list(STEPS)
    for s in args:
        run(s)
