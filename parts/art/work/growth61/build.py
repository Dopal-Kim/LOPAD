#!/usr/bin/env python3
"""61라운드 단계 4 (P12) 무기 1차·2차 각성 외형 — 결정적, Gemini 미사용. 계약 art §26.

  looks    미리보기 정지 그림 → assets/sprites/looks/ (192×192, 무기만)                       (looks.py)
  sheets   무기 오버레이 격자 원본 → out/grid/weapons (a1·a2·a2_glow × 갈래 12 × 시트)           (sheets.py)
  fx       각성 연출 fx 2종 → out/grid/fx (awaken1_crack · awaken2_bloom) + preview_fx.png       (fx.py)
  publish  격자 원본 → assets/sprites/{weapons,fx}/v4 트림 아틀라스(atlas57 convert_sheet·apply_in_place — 전 프레임 대조 통과 시만)
           덮어쓰기 허용: 이 빌드(version v4-r61-growth)가 만든 같은 이름만. 임시 폴더 out/_atlas_tmp_growth61 (전용)
  verify   publish 한 시트: atlas57 verify.check_format + 격자 원본과 전 프레임 픽셀 대조 → verify_log.txt
  memory   갈래 하나 분량(a1+a2+a2_glow) GPU MB vs 기존 _awaken 세트(awaken60 publish_log) → memory.json
  preview  preview_<weapon>.png (정지 그림 줄 + 게임 합성)                                       (preview.py)
사용: python3 parts/art/work/growth61/build.py [단계...]   (인자 없으면 전부, 순서대로)
"""
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import g61 as Z  # noqa: E402

OWN = Z.VERSION


def staged():
    only = {x for x in os.environ.get("GROWTH_ONLY", "").split(",") if x}
    out = []
    for cat in ("fx", "weapons"):
        d = os.path.join(Z.STAGE, cat)
        if os.path.isdir(d):
            out += [(cat, f[:-5]) for f in sorted(os.listdir(d)) if f.endswith(".json") and (not only or f[:-5] in only)]
    return out


def _atlas():
    import importlib.util
    spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(Z.WORK, "atlas57", "build.py"))
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    return A


def step_publish():
    A = _atlas()
    log = []
    for cat, name in staged():
        dst = os.path.join(Z.SPR, cat, "v4")
        os.makedirs(dst, exist_ok=True)
        jp, pp = os.path.join(dst, name + ".json"), os.path.join(dst, name + ".png")
        old_pages = []
        if os.path.exists(jp):
            om = json.load(open(jp, encoding="utf-8"))
            assert om.get("version") == OWN, (name, "assets 에 다른 작업의 같은 이름 시트", om.get("version"))
            old_pages = [t["image"] for t in om.get("textures", [])] or [om.get("meta", {}).get("image", name + ".png")]
        shutil.copy2(os.path.join(Z.STAGE, cat, name + ".png"), pp)
        shutil.copy2(os.path.join(Z.STAGE, cat, name + ".json"), jp)
        od = os.path.join(Z.TMP, cat)
        os.makedirs(od, exist_ok=True)
        res = A.convert_sheet(pp, jp, od, 2, 4096, True)
        A.apply_in_place(res, od, dst, pp, jp, 4096)
        new_pages = [n for n, _, _ in res["pages"]]
        for op in old_pages:
            if op not in new_pages and os.path.exists(os.path.join(dst, op)):
                os.remove(os.path.join(dst, op))
        m = json.load(open(jp, encoding="utf-8"))
        assert m["framesPerDirection"] == m["atlas"]["grid"]["columns"], name
        log.append(dict(cat=cat, name=name, src=res["srcSize"], pages=[[n, w, h] for n, w, h in res["pages"]],
                        gpuBeforeMB=round(res["gpuBefore"] / 2 ** 20, 3), gpuAfterMB=round(res["gpuAfter"] / 2 ** 20, 3),
                        empty=res["empty"], deduped=res["deduped"]))
    shutil.rmtree(Z.TMP, ignore_errors=True)
    lp = os.path.join(HERE, "publish_log.json")
    if os.environ.get("GROWTH_ONLY") and os.path.exists(lp):
        new = {x["name"] for x in log}
        log = sorted([x for x in json.load(open(lp, encoding="utf-8")) if x["name"] not in new] + log, key=lambda x: (x["cat"], x["name"]))
    with open(lp, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    print("publish %d 시트 · GPU %.1f MB" % (len(log), sum(x["gpuAfterMB"] for x in log)))


def step_verify():
    import verify as V
    import gridsheet
    from PIL import Image
    bad = 0
    lines = []
    for cat, name in staged():
        jp = os.path.join(Z.SPR, cat, "v4", name + ".json")
        m = json.load(open(jp, encoding="utf-8"))
        grid = gridsheet.load_meta(jp)
        errs = V.check_format(grid, m, 4096)
        if "atlas" not in m:
            errs.append("격자 그대로(publish 전)")
        if m.get("version") != OWN:
            errs.append("version ≠ " + OWN)
        for p in (m.get("textures") or [{"image": m["meta"]["image"]}]):
            if not os.path.exists(os.path.join(Z.SPR, cat, "v4", p["image"])):
                errs.append("페이지 없음 " + p["image"])
        gp = os.path.join(Z.STAGE, cat, name + ".png")
        if not errs:
            gm = json.load(open(gp[:-4] + ".json", encoding="utf-8"))
            nbad = V.compare_sheet(Image.open(gp).convert("RGBA"), gm, m, os.path.join(Z.SPR, cat, "v4"))
            if nbad:
                errs.append("픽셀 불일치 %d 프레임" % nbad)
        lines.append("%-8s %-52s %s" % (cat, name, "OK" if not errs else errs[:3]))
        bad += bool(errs)
    lines.append("검사 %d 시트 · 오류 %d" % (len(staged()), bad))
    open(os.path.join(HERE, "verify_log.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(lines[-1])
    assert bad == 0


def step_memory():
    pl = json.load(open(os.path.join(HERE, "publish_log.json"), encoding="utf-8"))
    aw = json.load(open(os.path.join(Z.AW, "publish_log.json"), encoding="utf-8"))
    out = {}
    for w in Z.WEAPONS:
        ref = sum(x["gpuAfterMB"] for x in aw if x["cat"] == "weapons" and x["name"].startswith(w + "_") and x["name"].endswith("_awaken"))
        ref_live = sum(x["gpuAfterMB"] for x in aw if x["cat"] == "weapons" and x["name"].startswith(w + "_") and x["name"].endswith("_awaken")
                       and x["name"][:-7] not in Z.DEPRECATED)
        for bid, *_ in Z.BRANCHES[w]:
            pre = "%s_%s_" % (w, bid)
            a1 = sum(x["gpuAfterMB"] for x in pl if x["name"].startswith(pre + "a1_"))
            a2 = sum(x["gpuAfterMB"] for x in pl if x["name"].startswith(pre + "a2_") and not x["name"].startswith(pre + "a2_glow_"))
            gl = sum(x["gpuAfterMB"] for x in pl if x["name"].startswith(pre + "a2_glow_"))
            tot = a1 + a2 + gl
            out[pre[:-1]] = dict(a1MB=round(a1, 2), a2MB=round(a2, 2), a2GlowMB=round(gl, 2), totalMB=round(tot, 2),
                                 awakenSetMB=round(ref, 2), awakenSetLiveMB=round(ref_live, 2), ratio=round(tot / ref, 3) if ref else None)
    fx = {x["name"]: x["gpuAfterMB"] for x in pl if x["cat"] == "fx"}
    with open(os.path.join(HERE, "memory.json"), "w", encoding="utf-8") as f:
        json.dump(dict(branches=out, fx=fx, rule="갈래 하나(a1+a2+a2_glow) ≤ 기존 _awaken 세트 × 1.5 (아틀라스 페이지 RGBA 기준)"), f, ensure_ascii=False, indent=1)
    worst = max(v["ratio"] for v in out.values())
    for k, v in out.items():
        print("%-22s a1 %6.2f  a2 %5.2f  glow %5.2f  = %6.2f MB  / awaken %6.2f  ×%.2f" % (k, v["a1MB"], v["a2MB"], v["a2GlowMB"], v["totalMB"], v["awakenSetMB"], v["ratio"]))
    print("최대 비율 ×%.3f" % worst)
    assert worst <= 1.5, "메모리 1.5배 초과"


STEPS = {
    "looks": "import looks as L; L.build()",
    "sheets": "import sheets as S; S.build()",
    "fx": "import fx as X; X.build(); import os, g61 as Z; X.preview(os.path.join(Z.HERE, 'preview_fx.png'))",
    "publish": "import build as B; B.step_publish()",
    "verify": "import build as B; B.step_verify()",
    "memory": "import build as B; B.step_memory()",
    "preview": "import preview as P; [print(P.build(w)) for w in ('katana','greatsword','dagger','bow')]",
}


def run(step):
    t0 = time.time()
    subprocess.run([sys.executable, "-W", "ignore", "-c", STEPS[step]], cwd=HERE, check=True)
    print("== %s %.1fs" % (step, time.time() - t0))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a in STEPS] or list(STEPS)
    for s in args:
        run(s)
