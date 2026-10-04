#!/usr/bin/env python3
"""57라운드 갈래 1단 수단 빌드 — 칼 2 · 단검 2 · 활 2 수단 + 대검 1단 충격파 2종(파쇄 균열 강화판 · 중압 원형 진동). 결정적, Gemini 미사용
(키아트 parts/art/work/gemini/weapon_moves/sheet_*.png 는 참고만).

  katana   칼 몸·무기 4방향(bk.py)          → player/v3/player_katana_{spin,guardbreak} · weapons/v3/katana_{spin,guardbreak}
  body     단검·활 몸·무기 4방향(bd.py)      → player/v3/player_{dagger_fan_throw,bow_rapid_loop} · weapons/v3/같은 이름
  fx       이펙트(bfx.py — 몸 JSON 타이밍을 읽으므로 katana·body 뒤)
           → fx/v3/katana_spin · katana_spin_ready · katana_guardbreak · greatsword_shatter_crack_t1~t5 · greatsword_shatter_snuff ·
             greatsword_quake_ring · dagger_fan_throw · dagger_thrown · dagger_cross_clone · bow_arrow_pierce · bow_arrow_pierce_hit
  overlay  검기 오버레이 weapons/v3/katana_{spin,guardbreak}_ki1~3(combo56_res/overlay.job 그대로 — 그 파일은 고치지 않음)
  preview  미리보기 PNG·GIF(이 폴더 preview_*.png, gif/*.gif — bprev.py)
  publish  atlas57 트림 아틀라스로 assets 교체(계약 §19.5 — atlas57/build.py --in-place 와 같은 함수: 격자 → 전 프레임 대조 → 통과 시 덮어씀).
           이 빌드가 만든 시트 이름만 정확히 골라 바꾼다(다른 작업의 시트·임시 폴더와 섞이지 않게 임시 폴더는 이 폴더 out/_atlas_tmp)
  verify   atlas57/verify.py 형식·픽셀 점검을 이 빌드 시트만(새 시트라 git 원본 없음 → 형식 + 저장 직전 대조는 publish 가 함)
사용: python3 parts/art/work/branch57/build.py [katana] [body] [fx] [overlay] [preview] [publish] [verify]   (인자 없으면 전부, 순서대로)
각 단계는 별도 프로세스(칼·단검이 combo55/hero_v3 모듈을 프로세스 안에서만 바꾸므로).
대각 행 없음: 이번 산출은 칼·단검·활 4방향 + 대검 fx(rotate/원 — 방향 행 없음)라 58라운드 진짜 3/4 대각 리그와 겹치지 않는다.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(WORK, "../../.."))
SPR = os.path.join(ROOT, "assets/sprites")

KATANA_BODY = ["katana_spin", "katana_guardbreak"]
OTHER_BODY = ["dagger_fan_throw", "bow_rapid_loop"]
FX = ["katana_spin", "katana_spin_ready", "katana_guardbreak"] + ["greatsword_shatter_crack_t%d" % n for n in range(1, 6)] + ["greatsword_shatter_snuff", "greatsword_quake_ring",
      "dagger_fan_throw", "dagger_thrown", "dagger_cross_clone", "bow_arrow_pierce", "bow_arrow_pierce_hit"]
KI = ["%s_ki%d" % (n, lv) for n in KATANA_BODY for lv in (1, 2, 3)]


def sheets():
    out = []
    for n in KATANA_BODY + OTHER_BODY:
        out += [("player", "player_" + n), ("weapons", n)]
    out += [("weapons", n) for n in KI]
    out += [("fx", n) for n in FX]
    return out


# =============================================================================
def step_overlay():
    sys.path.insert(0, os.path.join(WORK, "combo56_res"))
    sys.path.insert(0, os.path.join(WORK, "atlas57"))
    import gridsheet
    import rk
    import overlay

    def load_sheet(path):                     # 격자·아틀라스 양쪽(57 이후 assets 가 아틀라스일 수 있음)
        j = gridsheet.load_meta(os.path.join(SPR, path + ".json"))
        im = gridsheet.open_grid(os.path.join(SPR, path + ".json"))
        fw, fh, n = j["frameWidth"], j["frameHeight"], j["frames"]
        return j, {d: [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r, d in enumerate(j["directions"])}
    rk.load_sheet = load_sheet
    rk.VERSION = "v3-r57-branch"
    rk.SRC = "parts/art/work/branch57/build.py overlay (57라운드 갈래 1단 — combo56_res/overlay.job 검기 오버레이 그대로)"
    for n in KATANA_BODY:
        print(overlay.job(("ki", n)))


def step_publish():
    sys.path.insert(0, os.path.join(WORK, "atlas57"))
    import shutil
    import importlib.util
    spec = importlib.util.spec_from_file_location("atlas57_build", os.path.join(WORK, "atlas57", "build.py"))
    A = importlib.util.module_from_spec(spec)   # atlas57/build.py (이 파일과 이름이 같아 경로로 읽음)
    spec.loader.exec_module(A)
    tmp = os.path.join(HERE, "out", "_atlas_tmp")
    log = []
    for cat, name in sheets():
        src_dir = os.path.join(SPR, cat, "v3")
        jp, pp = os.path.join(src_dir, name + ".json"), os.path.join(src_dir, name + ".png")
        state = A.sheet_state(jp)
        if state == "atlas":
            log.append(dict(cat=cat, name=name, state="이미 아틀라스 — 건너뜀"))
            continue
        assert state == "grid", (name, state)
        keep = os.path.join(HERE, "out", "grid", cat)          # 원 격자 보관(작업 폴더 — 미리보기·verify 대조용, assets 에는 두지 않음)
        os.makedirs(keep, exist_ok=True)
        shutil.copy2(pp, os.path.join(keep, name + ".png"))
        shutil.copy2(jp, os.path.join(keep, name + ".json"))
        od = os.path.join(tmp, cat)
        os.makedirs(od, exist_ok=True)
        res = A.convert_sheet(pp, jp, od, 2, 4096, True)
        A.apply_in_place(res, od, src_dir, pp, jp, 4096)
        m = json.load(open(jp, encoding="utf-8"))
        assert m["framesPerDirection"] == m["atlas"]["grid"]["columns"], name     # 계약 §19.5(57 Q38)
        log.append(dict(cat=cat, name=name, state="아틀라스로 교체", src=res["srcSize"], pages=[[n, w, h] for n, w, h in res["pages"]],
                        gpuBeforeMB=round(res["gpuBefore"] / 2 ** 20, 2), gpuAfterMB=round(res["gpuAfter"] / 2 ** 20, 2),
                        empty=res["empty"], deduped=res["deduped"]))
        print("%s/%s: %s -> %s" % (cat, name, res["srcSize"], ", ".join("%dx%d" % (w, h) for _, w, h in res["pages"])))
    shutil.rmtree(tmp, ignore_errors=True)
    with open(os.path.join(HERE, "publish_log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)


def step_verify():
    sys.path.insert(0, os.path.join(WORK, "atlas57"))
    import verify as V
    import gridsheet
    bad = 0
    for cat, name in sheets():
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
        gp = os.path.join(HERE, "out", "grid", cat, name + ".png")
        if os.path.exists(gp) and not errs:                    # 보관한 원 격자와 전 프레임 픽셀 대조
            from PIL import Image
            gm = json.load(open(gp[:-4] + ".json", encoding="utf-8"))
            nbad = V.compare_sheet(Image.open(gp).convert("RGBA"), gm, m, os.path.join(SPR, cat, "v3"))
            if nbad:
                errs.append("픽셀 불일치 %d 프레임" % nbad)
        print("%-8s %-36s %s" % (cat, name, "OK" if not errs else errs[:3]))
        bad += bool(errs)
    print("검사 %d 시트 · 오류 %d" % (len(sheets()), bad))
    assert bad == 0


STEPS = {
    "katana": "import bk; bk.build()",
    "body": "import bd; bd.build()",
    "fx": "import bfx; bfx.build()",
    "overlay": "import build; build.step_overlay()",
    "preview": "import bprev; bprev.main()",
    "publish": "import sys; sys.path.insert(0, %r); import build as B57; B57.step_publish()" % HERE,
    "verify": "import build; build.step_verify()",
}


def run(step):
    t0 = time.time()
    subprocess.run([sys.executable, "-c", STEPS[step]], cwd=HERE, check=True)
    print("== %s %.1fs" % (step, time.time() - t0))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a in STEPS] or list(STEPS)
    for s in args:
        run(s)
