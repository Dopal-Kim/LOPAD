"""62 루프 3 (P17 묶음 D · 점검 P1-N9) 단검·활 궤적.

단검 `fx/v3/dagger_combo{1,2,3}_smear` — 칼·대검 스미어(§31-1, r62b smear.py)와 같은 형식·같은 코드:
  틀·피벗·방향 행·프레임 번호·ms = weapons/v3/dagger_combo<n> (192×192 · (96,186) · playerFrameOffset (48,48)), 무기 바로 아래 depth.
  1·2타 = 짧은 베기(휘두름 칸 1·2, 사라짐 3·4), 3타 = 찌르기(찌름 줄기 2·3·4 + 칼끝 앞 짧은 찌름 섬광, 사라짐 5).
  색 = 단검 '독' 램프(§28 #c060ff), 흰 끝은 판정 칸(무기 impactFrame 2)만. 단검 칼날이 짧아(약 30~40도트) 폭 비율을 칼보다 크게.
활 `fx/v3/bow_shot_flash` · `fx/v3/bow_arrow_trail` — bow.py.
"""
import os
import sys

from c62 import WORK

sys.path.insert(0, os.path.join(WORK, "r62b"))
import common as rc  # noqa: E402  (r62b common — 시트 쓰기·램프)
import smear as S62b  # noqa: E402

DAGGER = {
    "dagger_combo1": dict(weapon="katana", ramp=rc.POISON, sweep=[1, 2], decay=[3, 4], width=0.85, hit=1),
    "dagger_combo2": dict(weapon="katana", ramp=rc.POISON, sweep=[1, 2], decay=[3, 4], width=0.85, hit=2),
    "dagger_combo3": dict(weapon="katana", ramp=rc.POISON, thrust=[2, 3, 4], decay=[5], width=0.0, hit=3),
}
_orig_load = S62b.load_grid
_orig_write = S62b.b2.write_sheet


def _load(rel):
    m, g = _orig_load(rel)
    if rel.startswith("weapons/v3/dagger_combo") and not m.get("glowFrames"):
        m = dict(m)
        m["glowFrames"] = [m.get("impactFrame", 2)]       # 단검 무기 시트엔 glowFrames 가 없다 → 판정 칸 = impactFrame
    return m, g


def _write(cat, name, frames, fw, fh, meta, **kw):
    if name.startswith("dagger_"):
        meta["weapon"] = "dagger"                          # (r62b 코드의 무기 색 표에 단검이 없어 'katana' 로 돌린 뒤 여기서 바로잡음)
        meta["weaponColor"] = "독 #c060ff(흰 끝 #fbe0ff 는 판정 칸만 — 무기 impactFrame 2)"
        meta["version"] = "v3-r62c"
        meta["source"] = "parts/art/work/r62c/build.py (62 루프 3 · P17) · smear.py → r62b smear.py 같은 코드"
        meta["glowFramesNote"] = "무기 시트 weapons/v3/dagger_combo<n> 에 glowFrames 가 없어 impactFrame(2) 을 판정 칸으로 씀"
        meta["design"] = ("단검: 1·2타 짧은 베기 스미어(칼보다 짧고 굵게 — 칼날이 짧다), 3타 찌르기 = 칼끝 뒤 찌름 줄기 + 칼끝 앞 짧은 찌름 섬광. "
                          "사라짐 칸은 제자리에서 식는다")
        meta["systemHint"] = ("P1-N9 시스템: 단검 1~3타 오버레이(weapons/v3/dagger_combo<n>)와 같은 프레임·시각에 무기 바로 아래로. "
                              "가속 시트(fx dagger_combo<n>_accel2·3)는 그대로 — 스미어는 무기 시트 프레임을 따른다(공속 배율로 무기가 빨라지면 같이)")
    return _orig_write(cat, name, frames, fw, fh, meta, **kw)


def build():
    S62b.load_grid = _load
    S62b.b2.write_sheet = _write
    out = {}
    try:
        for name, cfg in DAGGER.items():
            out[name] = S62b.build_move(name, cfg)
    finally:
        S62b.load_grid = _orig_load
        S62b.b2.write_sheet = _orig_write
    import bow
    res = bow.build()
    rep = S62b.b2.to_atlas() if hasattr(S62b.b2, "to_atlas") else None
    try:
        S62b.preview(out, os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview_smear_dagger.png"))
    except Exception as e:  # 미리보기 실패는 산출물과 무관
        print("미리보기 건너뜀:", e)
    return {"dagger": {k: v[2] for k, v in out.items()}, "bow": res, "atlas": rep}
