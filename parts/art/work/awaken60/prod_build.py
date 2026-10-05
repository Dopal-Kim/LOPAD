#!/usr/bin/env python3
"""60라운드 Q15~Q21 최종 각성 실제 제작 — 결정적, Gemini 미사용.

  overlay  각성 무기 오버레이 60(칼 20·대검 20·단검 11·활 9) — weapons/v3/<무기 시트>_awaken 교체(틀 확대)   (prod_overlay.py)
  fx       시그니처 fx 4 교체 + 각성 순간 전환 4(새 <무기>_awaken_in) + 각성 전용 궤적 19(새 <기본 fx>_awaken)  (prod_fx.py)
  preview  미리보기 PNG → out/prod/ (긴 변 8000 이하)
  publish  격자 원본(out/grid) → assets 트림 아틀라스(atlas57/build.py 의 convert_sheet·apply_in_place — 전 프레임 대조 통과 시만 덮어씀).
           덮어쓰기 허용: 이 빌드가 만든 이름만, 기존 판이 57 build57(v3-r57-build) 또는 이 빌드(v3-r60-awaken)일 때만.
  (AWAKEN_ONLY=이름,이름 → publish·verify 를 그 시트만)
  verify   publish 한 시트: atlas57 verify.check_format + 격자 원본과 전 프레임 픽셀 대조 → verify_log.txt
사용: python3 parts/art/work/awaken60/prod_build.py [단계...]   (인자 없으면 전부, 순서대로)
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
OWN = "v3-r60-awaken"
REPLACEABLE = {"v3-r57-build", OWN}


def staged():
    """격자 원본 목록. 환경 변수 AWAKEN_ONLY=이름,이름 이면 그 시트만(publish·verify 부분 실행 — 예: 60 Q33 합친 궤적 2종)."""
    only = {x for x in os.environ.get("AWAKEN_ONLY", "").split(",") if x}
    out = []
    for cat in ("fx", "weapons"):
        d = os.path.join(STAGE, cat)
        if os.path.isdir(d):
            out += [(cat, f[:-5]) for f in sorted(os.listdir(d)) if f.endswith(".json") and (not only or f[:-5] in only)]
    return out


def step_preview():
    sys.path.insert(0, HERE)
    import prod_preview as PV
    import prod_fx as PF
    od = os.path.join(HERE, "out", "prod")
    os.makedirs(od, exist_ok=True)
    groups = {
        "katana": ["katana_rise", "katana_fall", "katana_issen", "katana_carry_drawn_idle", "katana_carry_idle", "katana_spin"],
        "greatsword": ["greatsword_sweep_cw", "greatsword_cleave", "greatsword_carry_drawn_idle", "greatsword_carry_idle", "greatsword_leap_slam"],
        "dagger": ["dagger_combo1", "dagger_combo3", "dagger_carry_idle", "dagger_flurry", "dagger_backstab"],
        "bow": ["bow_draw_hold", "bow_release", "bow_carry_idle", "bow_rapid_loop", "bow_reload"],
    }
    for w, lst in groups.items():
        print(w, PV.main(os.path.join(od, "overlay_%s.png" % w), lst, ("right", "down", "up"), scale=1, frames_max=12))
    print("sig", PV.fx_preview(os.path.join(od, "fx_signature.png"), ["katana_fullmoon", "dagger_hundred_ghosts", "bow_meteor_arrow", "greatsword_landslide"], rows_max=4))
    print("in", PV.fx_preview(os.path.join(od, "fx_awaken_in.png"), [w + "_awaken_in" for w in ("katana", "greatsword", "dagger", "bow")], rows_max=1))
    print("q33", PV.combo_preview(os.path.join(od, "fx_branch_awaken_q33.png"), [("katana_fall_wide", "katana_fall"), ("dagger_combo3_double", "dagger_combo3")]))
    names = [b + "_awaken" for w, l in PF.TRAILS.items() for b in l]
    print("trail", PV.fx_preview(os.path.join(od, "fx_trails_a.png"), names[:10], rows_max=1, scale=1))
    print("trail", PV.fx_preview(os.path.join(od, "fx_trails_b.png"), names[10:], rows_max=1, scale=1))


def step_publish():
    import importlib.util
    sys.path.insert(0, os.path.join(WORK, "atlas57"))
    spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(WORK, "atlas57", "build.py"))
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    tmp = os.path.join(HERE, "out", "_atlas_tmp")
    log = []
    for cat, name in staged():
        dst = os.path.join(SPR, cat, "v3")
        jp, pp = os.path.join(dst, name + ".json"), os.path.join(dst, name + ".png")
        old_pages = []
        if os.path.exists(jp):
            om = json.load(open(jp, encoding="utf-8"))
            v = om.get("version")
            assert v in REPLACEABLE, (name, "assets 에 다른 작업의 같은 이름 시트가 있음", v)
            old_pages = [t["image"] for t in om.get("textures", [])] or [om.get("meta", {}).get("image", name + ".png")]
        shutil.copy2(os.path.join(STAGE, cat, name + ".png"), pp)
        shutil.copy2(os.path.join(STAGE, cat, name + ".json"), jp)
        od = os.path.join(tmp, cat)
        os.makedirs(od, exist_ok=True)
        res = A.convert_sheet(pp, jp, od, 2, 4096, True)
        A.apply_in_place(res, od, dst, pp, jp, 4096)
        new_pages = [n for n, _, _ in res["pages"]]
        for op in old_pages:                         # 옛 판이 남긴 페이지 정리
            if op not in new_pages and os.path.exists(os.path.join(dst, op)):
                os.remove(os.path.join(dst, op))
        m = json.load(open(jp, encoding="utf-8"))
        assert m["framesPerDirection"] == m["atlas"]["grid"]["columns"], name
        log.append(dict(cat=cat, name=name, replaced=bool(old_pages), src=res["srcSize"], pages=[[n, w, h] for n, w, h in res["pages"]],
                        gpuBeforeMB=round(res["gpuBefore"] / 2 ** 20, 2), gpuAfterMB=round(res["gpuAfter"] / 2 ** 20, 2),
                        empty=res["empty"], deduped=res["deduped"]))
    shutil.rmtree(tmp, ignore_errors=True)
    lp = os.path.join(HERE, "publish_log.json")
    if os.environ.get("AWAKEN_ONLY") and os.path.exists(lp):        # 부분 실행 = 기존 기록에 합침(이름 같으면 갈아 끼움)
        new = {x["name"] for x in log}
        log = sorted([x for x in json.load(open(lp, encoding="utf-8")) if x["name"] not in new] + log, key=lambda x: (x["cat"], x["name"]))
    with open(lp, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    print("publish %d 시트(교체 %d · 새 %d) · GPU %.1f MB" % (len(log), sum(x["replaced"] for x in log), sum(not x["replaced"] for x in log),
                                                        sum(x["gpuAfterMB"] for x in log)))


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
        if m.get("version") != OWN:
            errs.append("version ≠ " + OWN)
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


STEPS = {
    "overlay": "import prod_overlay as O; O.build()",
    "fx": "import prod_fx as X; X.build()",
    "preview": "import prod_build as B; B.step_preview()",
    "publish": "import prod_build as B; B.step_publish()",
    "verify": "import prod_build as B; B.step_verify()",
}


def run(step):
    t0 = time.time()
    subprocess.run([sys.executable, "-W", "ignore", "-c", STEPS[step]], cwd=HERE, check=True)
    print("== %s %.1fs" % (step, time.time() - t0))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a in STEPS] or list(STEPS)
    for s in args:
        run(s)
