"""57라운드 Q19: 결정이 끝난 라운드(≤55)의 미리보기 PNG·GIF 정리.

삭제 대상 = 아래를 모두 만족하는 파일
  1) parts/art/work/** 의 .png/.gif, 단 보관 폴더 제외:
     combo56_*, gemini/weapon_moves(56라운드), atlas57(57라운드), palette
  2) 미리보기 이름: preview*, cmp_*, ba_*, *.gif, gif/·cmp/·motion/ 안, 미리보기 전용 x2_*·hits_*·scene_mock_*·*_x8/_x12 확대본·silhouette_*
  3) 같은 작업 폴더(또는 gemini/)의 스크립트 문자열 리터럴(%s·%d·{..} 는 와일드카드)과 이름이 맞음 = 스크립트로 다시 만들 수 있음
  4) 입력으로 읽히지 않음: 어떤 스크립트에서도 그 이름이 open(·paste·load 줄이나 다른 폴더에서 경로로 나오지 않음
보관(항상): gemini 원본(raw_*·jpg·생성 PNG), 스크립트, JSON, md, txt, before/·ref_64/(옛 판 스냅숏 = 재생성 불가),
           이름에 old·vs_old·nobias·neutral 이 든 비교본(옛 판·실험 설정이 지금 스크립트로 재현되지 않음)

사용: python3 cleanup_r57.py          (점검만, 목록 출력 + cleanup_r57_list.json)
      python3 cleanup_r57.py --apply  (삭제)
"""
from __future__ import annotations

import argparse
import json
import os
import re
from glob import glob

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, ".."))

KEEP_DIRS = ("combo56_", "atlas57", "palette")
KEEP_SUBPATHS = ("gemini/weapon_moves/", "/before/", "/ref_64/")
KEEP_WORDS = ("old", "nobias", "neutral")
PREVIEW_DIRS = ("/gif/", "/cmp/", "/motion/")
PREVIEW_RE = re.compile(r"^(preview|cmp_|ba_|hits_|scene_mock|silhouette_|x2_\d|particles_.*_x\d+|ribbon_.*_x\d+|tiers_|branch_).*\.(png|gif)$")

LIT_RE = re.compile(r"""[fr]?(["'])([^"'\n]{1,200})\1""")


def literal_patterns(text: str):
    pats = []
    for m in LIT_RE.finditer(text):
        s = m.group(2)
        if not re.search(r"\.(png|gif)$", s) and not s.endswith(("_x", "_right.gif")):
            # 확장자가 따로 붙는 경우도 있어 접두 리터럴도 모은다
            if not re.match(r"^[A-Za-z0-9_%{}.\-/]+$", s):
                continue
        base = s.split("/")[-1]
        rx = re.escape(base)
        rx = re.sub(r"%(\\\d)?[sd]|%\\\.?\d*[df]", ".+", rx)
        rx = re.sub(r"\\\{[^}]*\\\}", ".+", rx)
        rx = rx.replace(r"\%s", ".+").replace(r"\%d", ".+").replace("%s", ".+").replace("%d", ".+")
        pats.append(rx)
    return pats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    py_files = glob(os.path.join(WORK, "**", "*.py"), recursive=True)
    py_text = {p: open(p, encoding="utf-8", errors="replace").read() for p in py_files}

    def top(p):
        return os.path.relpath(p, WORK).split(os.sep)[0]

    # 폴더별 이름 패턴
    pats_by_top = {}
    for p, t in py_text.items():
        pats_by_top.setdefault(top(p), []).extend(literal_patterns(t))
    # 가변 이름 조립(접두 + 접미)을 위해 리터럴 조각도 보관
    cands = []
    for p in sorted(glob(os.path.join(WORK, "**", "*"), recursive=True)):
        if not p.endswith((".png", ".gif")) or not os.path.isfile(p):
            continue
        rel = os.path.relpath(p, WORK).replace(os.sep, "/")
        t = rel.split("/")[0]
        if t.startswith(KEEP_DIRS) or any(k in "/" + rel for k in KEEP_SUBPATHS):
            continue
        base = os.path.basename(rel)
        is_prev = PREVIEW_RE.match(base) or base.endswith(".gif") or any(d in "/" + rel for d in PREVIEW_DIRS)
        if not is_prev:
            continue
        cands.append((rel, base, t))

    delete, keep = [], []
    for rel, base, t in cands:
        reason = None
        if any(w in base for w in KEEP_WORDS):
            reason = "옛 판·실험 비교본(재현 불가)"
        # 입력으로 읽히는가
        if reason is None:
            for p, text in py_text.items():
                if base not in text:
                    continue
                for line in text.splitlines():
                    if base in line and "save(" not in line and (re.search(r"open\(|paste_png|load\(", line) or
                                         (t in line and re.search(r"join\(|ROOT", line))):
                        reason = f"입력으로 읽힘: {os.path.relpath(p, WORK)}"
                        break
                if reason:
                    break
        if reason is None:
            scopes = [t] + (["gemini"] if t == "gemini" else [])
            stem_ok = False
            for sc in scopes:
                for rx in pats_by_top.get(sc, []):
                    try:
                        if re.fullmatch(rx, base) or (rx and re.fullmatch(rx + r".*\.(png|gif)", base) and len(rx) >= 4):
                            stem_ok = True
                            break
                    except re.error:
                        continue
                if stem_ok:
                    break
            if not stem_ok:
                reason = "만든 스크립트 리터럴을 못 찾음(재생성 불확실)"
        full = os.path.join(WORK, rel)
        size = os.path.getsize(full)
        (keep if reason else delete).append({"path": rel, "bytes": size, **({"reason": reason} if reason else {})})

    by_top = {}
    for d in delete:
        t = d["path"].split("/")[0]
        a = by_top.setdefault(t, [0, 0])
        a[0] += 1
        a[1] += d["bytes"]
    total = sum(d["bytes"] for d in delete)
    print("| 폴더 | 삭제 수 | 절감(MB) |\n|---|---|---|")
    for t, (n, b) in sorted(by_top.items(), key=lambda x: -x[1][1]):
        print(f"| {t} | {n} | {b/1e6:.2f} |")
    print(f"| 합계 | {len(delete)} | {total/1e6:.2f} |")
    print(f"\n보관(미리보기 이름이지만 남김) {len(keep)}개:")
    for k in keep:
        print("  ", k["path"], "—", k["reason"])
    with open(os.path.join(HERE, "cleanup_r57_list.json"), "w", encoding="utf-8") as f:
        json.dump({"round": 57, "rule": "Q19 결정 완료 라운드(≤55) 미리보기 정리", "applied": args.apply,
                   "deletedBytes": total, "delete": delete, "keep": keep}, f, ensure_ascii=False, indent=1)
    if args.apply:
        for d in delete:
            os.remove(os.path.join(WORK, d["path"]))
        # 빈 폴더 정리
        for t in by_top:
            for dp, dn, fn in sorted(os.walk(os.path.join(WORK, t)), key=lambda x: -len(x[0])):
                if not dn and not fn and dp != os.path.join(WORK, t):
                    os.rmdir(dp)
        print("삭제 완료")


if __name__ == "__main__":
    main()
