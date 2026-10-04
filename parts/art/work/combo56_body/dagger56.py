"""56라운드 Q4 단검 보강 — 무기 그림 1.3배(늘이기 아님: 길이·폭을 1.3배로 다시 래스터) + 수평 사거리 ×1.5 판정 참고값.

weapons_v3/dagger.py 를 고치지 않고 이 프로세스에서만 치수·폭·균열 차선을 1.3배로 바꾼 뒤 weapons_v3/build.py 의 dagger 경로를 그대로 돌린다
(몸 시트 player_dagger_* · player_*_free 는 같은 코드로 다시 쓰여 바이트 동일 — build 가 git 으로 확인).
산출: assets/sprites/weapons/v3/dagger_{combo1,combo2,combo3,special,carry_idle,carry_walk,carry_run,carry_dash}.png/.json (4방향 그대로)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "weapons_v3")))

import wv3  # noqa: E402
import dagger as DG  # noqa: E402

SCALE = 1.3
THRUST_X = 1.5                 # Q4 수평 사거리 ×1.5
OLD = dict(FANG=DG.FANG, GRIP=DG.GRIP, bladeLengthDots=DG.DESIGN["bladeLengthDots"], hiltLengthDots=DG.DESIGN["hiltLengthDots"])


def _scale_lanes(lanes):
    a, b = min(lanes), max(lanes)
    return tuple(range(round(a * SCALE), round(b * SCALE) + 1))


_W0 = DG.width


def width13(t):
    return _scale_lanes(_W0(t))


CRACKS13 = {(kk, round(lane * SCALE)) for kk, lane in DG.CRACKS}


def install():
    DG.FANG = round(OLD["FANG"] * SCALE, 2)
    DG.GRIP = round(OLD["GRIP"] * SCALE, 2)
    DG.width = width13
    DG.CRACKS = CRACKS13
    DG.DESIGN = dict(DG.DESIGN, bladeLengthDots=round(OLD["bladeLengthDots"] * SCALE), hiltLengthDots=round(OLD["hiltLengthDots"] * SCALE),
                     scale56="56라운드 Q4: 무기 그림 1.3배 — 조각 길이 %.1f→%.1f(설계)·폭 최대 7→9 도트·손잡이 %.1f→%.1f, 같은 디자인을 새 치수로 다시 래스터(최근접 확대 아님)"
                             % (OLD["FANG"], DG.FANG, OLD["GRIP"], DG.GRIP))


BASE55_LEN = {"dagger_combo1": 96, "dagger_combo2": 96, "dagger_combo3": 112}   # 55라운드 찌르기 길이(도트) — ×1.5 의 기준(재실행해도 두 번 곱하지 않게)


def thrust56(t, base_len):
    o = dict(t)
    o["lengthPx"] = round(base_len * THRUST_X)
    return o


REF_NOTE = ("56라운드 Q4 판정 참고값: 찌르기 직사각 판정의 수평 길이 ×1.5(lengthPx), 폭·시작점·각도는 그대로. "
            "최상위 thrust 와 같은 값(56라운드 Q51 정리), fx/v3/dagger_combo* 의 thrust 와도 같다. 피해 ×1.4 는 시스템 데이터. 단위 도트(월드 px = 도트/4)")
THRUST_NOTE = ("몸 중심에서 정면(right 기준 angleDeg)으로 fromPx~lengthPx, 폭 widthPx 의 직사각 판정. 방향 변환은 호와 같은 규약. "
               "56라운드 Q4 수평 사거리 ×1.5 반영값(%d → %d 도트, Q51 정리 — 이전 값은 previousThrust)")


def patch_refs():
    """몸·무기 JSON 의 thrust 를 56라운드 값(×1.5)으로 맞추고 hitReference56 도 같은 값으로(56라운드 Q51). 이전 값은 previousThrust."""
    out = {}
    for n in ("dagger_combo1", "dagger_combo2", "dagger_combo3"):
        for path in (os.path.join(wv3.EX.OUT_P, "player_%s.json" % n), os.path.join(wv3.EX.OUT_W, "%s.json" % n)):
            j = json.load(open(path, encoding="utf-8"))
            if "thrust" not in j:
                continue
            old = dict(j["thrust"], lengthPx=BASE55_LEN[n])
            new = thrust56(j["thrust"], BASE55_LEN[n])
            j["thrust"] = new
            j["previousThrust"] = old
            j["thrustNote"] = THRUST_NOTE % (old["lengthPx"], new["lengthPx"])
            j["hitReference56"] = dict(thrust=new, previousThrust=old, note=REF_NOTE)
            out[n] = dict(old=old, new=new)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(j, f, ensure_ascii=False, indent=1)
    return out


def build():
    install()
    import importlib.util
    spec = importlib.util.spec_from_file_location("wv3_build", os.path.join(os.path.dirname(wv3.__file__), "build.py"))
    WB = importlib.util.module_from_spec(spec)       # weapons_v3/build.py (이름 'build' 은 설치된 다른 패키지와 겹침)
    spec.loader.exec_module(WB)
    wv3.PV.HERE = os.path.join(HERE, "dagger_prev")   # 미리보기는 이 작업 폴더에(weapons_v3 미리보기를 덮지 않음)
    os.makedirs(wv3.PV.HERE, exist_ok=True)
    WB.main({"dagger"})
    for n in ("dagger_combo1", "dagger_combo2", "dagger_combo3", "dagger_special", "dagger_carry_idle", "dagger_carry_walk",
              "dagger_carry_run", "dagger_carry_dash"):
        p = os.path.join(wv3.EX.OUT_W, n + ".json")
        j = json.load(open(p, encoding="utf-8"))
        j["source"] = "parts/art/work/combo56_body/build.py dagger (56라운드 Q4 — weapons_v3 단검 1.3배 재출력)"
        j["version"] = "v3-r56"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(j, f, ensure_ascii=False, indent=1)
    return patch_refs()


if __name__ == "__main__":
    print(build())
