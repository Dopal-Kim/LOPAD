#!/usr/bin/env python3
"""P20 주인공 새 몸(키아트 비율 재설계) — 전 동작 재렌더 빌드.

1단계 모델 시트: model_sheet.py → model_sheet_compare.png
2단계(이 파일): 모든 주인공 몸 시트를 새 리그 rig20 으로 다시 그리고, 그 몸을 쓰는 무기 오버레이를 프레임마다 손 앵커 오프셋(b+)으로 옮긴다.
  loco   — 대기·걷기·달리기(+_free)·대쉬·피격·사망 (P19 자세 loco19 그대로, 새 리그)
  skid   — 방향 전환 미끄럼(대쉬 휴대 오버레이에서 파생)
  attack — P19 9시트(칼 rise/fall/thrust · 대검 sweep_cw/cleave/sweep_ccw(무게 프레임) · 단검 1~3) — attack19 그대로, 새 리그
  gen    — 나머지 공격·특수기·차지·홀드·활·groggy (gen20 — 역할 결 재자세)
  flip   — 대검 공중제비(몸이 오버레이 안에 그려진 칸) 새 몸으로 다시 합성
  birth  — 탄생(birth3 연출 그대로, 몸만 새 리그)
  fx     — hero_* fx·dash_trail (fx19, 새 몸 그리드에서)
  (타이틀 주인공 그림은 parts/art/work/title62/build.py — near.py 등 상흔을 찢긴 균열로)
원본은 항상 git sync19.SRC_REV(P19 직전) → 다시 돌려도 결정적.
사용: python3 parts/art/work/hero20/build.py [loco] [skid] [attack] [gen | player_<이름>…] [flip] [birth] [fx] [stamp]
"""
import importlib.util
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import body20 as B  # noqa: E402
import rig20  # noqa: E402
import sync19 as S  # noqa: E402

P20_NOTE = ("P20 주인공 새 몸(2026-10-15, 프로듀서 재점검 '부적합 — 몸 설계부터 다시'): 키아트 hero3_b 비율 — 약 6.8등신, 작은 숯빛 맨머리·좁은 턱·"
            "가늘게 빛나는 한쪽 눈, 마른 근육질, 찢긴 가슴·등 균열(번개 아님), 붕대 팔뚝·정강이, 왼어깨 견갑·오른정강이 갑주, 등에 박힌 화살 3대, "
            "찢긴 허리천 + 작은 가죽 주머니. 새 리그 parts/art/work/hero20/rig20.py. 틀·피벗·프레임 수·ms·판정 필드 그대로, "
            "무기 오버레이는 프레임마다 weaponOffsetDots 만큼 옮겨 구움(손 앵커 오프셋 동기 b+).")
LOG = {}


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def h19():
    if "h19build" not in sys.modules:
        mod = load_mod("h19build", os.path.join(WORK, "hero19", "build.py"))
        mod.B = B
        mod.SRC = "parts/art/work/hero20/build.py (P20 새 몸 리그 rig20 · P19 이동 자세 loco19 · 무기 오버레이 오프셋 동기)"
        mod.P19_NOTE = P20_NOTE
        mod.LOG = LOG
        _bm = mod.body_meta

        def body_meta(meta, fr, extra=None):
            m = _bm(meta, fr, extra)
            m["p20"] = P20_NOTE
            m.pop("p19", None)
            return m
        mod.body_meta = body_meta
    return sys.modules["h19build"]


class _B19Shim:
    """attack19 이 부르는 body19 함수 자리에 새 리그 판(body20)."""
    pinned_pose = staticmethod(B.pinned_pose)
    fold_elbows = staticmethod(B.fold_elbows)
    scar_of = staticmethod(B.scar_of)

    @staticmethod
    def hand_err(R, hands, off, d=None):
        return B.hand_err(R, hands, off)


def build_attack(names=None):
    import attack19 as A19
    A19.B = _B19Shim
    import gen20
    A19.draw = gen20.draw          # 새 리그 + 허리띠 측정용 부위 표시(gen20.belt — A19.belt 도 바꿈)
    A19.SRC = "parts/art/work/hero20/build.py attack (P20 새 몸 리그 · attack19 역할 결 · 대검 무게 프레임 · 무기 오버레이 오프셋 동기)"
    import gen20
    cur = {}
    _ra, _bt, _rend = A19.rise_adjust, A19.blade_tw, A19.render_attack

    def blade_tw(meta, i, d):              # 지금 그리는 (방향, 옛 프레임)을 기억
        cur["d"], cur["i"] = d, i
        return _bt(meta, i, d)

    def rise_adjust(st, elev, weapon):     # 옛 안무의 깊은 웅크림(허리띠 높이)을 살림 — gen20 과 같은 규칙
        st = _ra(st, elev, weapon)
        bo = A19.belt(cur["cells"][cur["d"]][cur["i"]])
        if bo is not None:
            oc = (bo[1] - gen20.ref_belt(cur["d"])) / 1.5 + 1.0
            if oc > st["crouch"] + 1.5:
                st = dict(st, crouch=min(16.0, oc + 1.0))
        return st

    def render_attack(name):
        meta, im = S.src_grid("player/v3/player_" + name)
        cur["cells"] = S.cells(meta, im)
        return _rend(name)
    A19.blade_tw, A19.rise_adjust, A19.render_attack = blade_tw, rise_adjust, render_attack
    _mc = S.move_cells
    S.move_cells = lambda meta, im, plan, grow_tl=False: _mc(meta, im, plan, grow_tl=True)   # 왼쪽·위로 넘친 칼끝도 틀을 키워 보존
    A19.build(names)


def stamp(names):
    """몸 JSON 에 p20 표기(attack19 가 쓴 것 포함)."""
    for body in names:
        p = os.path.join(S.SPR, "player", "v3", body + ".json")
        m = json.load(open(p, encoding="utf-8"))
        m["p20"] = P20_NOTE
        m["bodyRig"] = "parts/art/work/hero20/rig20.py"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False, indent=1)


ATTACK19 = ["katana_rise", "katana_fall", "katana_thrust", "greatsword_sweep_cw", "greatsword_cleave", "greatsword_sweep_ccw",
            "dagger_combo1", "dagger_combo2", "dagger_combo3"]
GEN = ["attack", "bow_aim", "bow_arrow_rain", "bow_arrow_rain_stand", "bow_draw_hold", "bow_rapid_loop", "bow_release", "bow_reload",
       "dagger_backstab", "dagger_fan_throw", "dagger_flurry", "dagger_special",
       "greatsword_brace_upswing", "greatsword_charge", "greatsword_charge_plunge", "greatsword_charge_slam", "greatsword_charge_swing",
       "greatsword_combo1", "greatsword_combo2", "greatsword_combo3", "greatsword_dashslash", "greatsword_draw", "greatsword_guard_rush",
       "greatsword_leap_slam", "greatsword_sheathe", "greatsword_slam", "greatsword_special", "greatsword_tackle", "groggy",
       "katana_combo1", "katana_combo2", "katana_combo3", "katana_counter", "katana_crescent", "katana_draw", "katana_guardbreak",
       "katana_iai", "katana_issen", "katana_issen_dash", "katana_sheathe", "katana_special", "katana_spin"]


def main(argv):
    steps = [a for a in argv if not a.startswith("-")] or ["loco", "skid", "attack", "gen", "flip", "birth", "fx", "stamp"]
    only = [a[7:] for a in steps if a.startswith("player_") and a[7:] in GEN]   # 시트 하나만: player_<이름>
    t0 = time.time()
    if "loco" in steps:
        h19().build_loco(None)
    if "skid" in steps:
        h19().build_skid()
    if "attack" in steps:
        build_attack()
    if "gen" in steps or only:
        import gen20
        gen20.build(only or GEN, LOG)
    if "flip" in steps:
        import flip20
        flip20.build(LOG)
    if "birth" in steps:
        import birth20
        birth20.build(LOG)
    if "fx" in steps:
        sys.modules.setdefault("body19", B)
        import fx19
        fx19.B = B
        fx19.SRC = "parts/art/work/hero20/build.py fx (P20 새 몸 — fx19 그대로, 새 몸 그리드에서)"
        fx19.build()
    if "stamp" in steps:
        stamp(sorted(os.path.basename(p)[:-5] for p in __import__("glob").glob(os.path.join(S.SPR, "player", "v3", "*.json"))))
    lp = os.path.join(HERE, "stats.json")
    old = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else {}
    old.update(json.loads(json.dumps(LOG, default=list)))
    with open(lp, "w", encoding="utf-8") as f:
        json.dump(old, f, ensure_ascii=False, indent=1)
    print("done %.0fs" % (time.time() - t0))


if __name__ == "__main__":
    main(sys.argv[1:])
