"""56라운드 Q30 — 대검 이펙트 8행 통일.

작업 A(combo56_fx/build.py)가 이미 대검 이펙트 6시트를 8행(directions = 몸 시트 순서)으로 냈다(PNG 행 = 대각 그림 포함).
이 단계는 PNG 를 다시 그리지 않고(그림은 작업 A 원본 그대로) JSON 만 몸·무기 시트와 같은 규격으로 정리한다:
  · directionRows(행 번호·방향·화면각·몸 면)를 몸 시트에서 그대로 복사, directions 순서 일치 검사
  · spawnRule(spawnAtMs = 몸 hitAt − sum(frameDurationsMs[:impactFrame])) 을 현재 몸 JSON 으로 다시 계산·검사
  · 행 높이·프레임 수 검사(PNG 크기 = frameWidth×frames, frameHeight×8)
"""
import json
import os

from PIL import Image

import rk

PAIRS = [("greatsword_sweep_cw", "greatsword_sweep_cw"), ("greatsword_sweep_ccw", "greatsword_sweep_ccw"),
         ("greatsword_cleave", "greatsword_cleave"), ("greatsword_charge_slam_lv1", "greatsword_charge_slam"),
         ("greatsword_charge_slam_lv2", "greatsword_charge_slam"), ("greatsword_charge_slam_lv3", "greatsword_charge_slam")]


def build():
    rep = []
    for fx, body in PAIRS:
        fp = os.path.join(rk.OUT_FX, fx + ".json")
        fj = json.load(open(fp, encoding="utf-8"))
        bj = json.load(open(os.path.join(rk.OUT_P, "player_%s.json" % body), encoding="utf-8"))
        assert fj["directions"] == bj["directions"], fx
        im = Image.open(os.path.join(rk.OUT_FX, fj["image"]))
        assert im.size == (fj["frameWidth"] * fj["frames"], fj["frameHeight"] * len(fj["directions"])), (fx, im.size)
        assert len(fj["directions"]) == 8
        hit = bj["timingMs"]["hitAt"]
        spawn = hit - sum(fj["frameDurationsMs"][:fj["impactFrame"]])
        st = [sum(bj["frameDurationsMs"][:i]) for i in range(bj["frames"])]
        changed = spawn != fj.get("spawnAtMs") or hit != fj.get("impactAtBodyMs")
        fj["spawnAtMs"] = spawn
        fj["impactAtBodyMs"] = hit
        if spawn in st:
            fj["spawnBodyFrame"] = st.index(spawn)
        else:
            fj.pop("spawnBodyFrame", None)
        fj["directionRows"] = bj["directionRows"]
        fj["directionRowsNote"] = ("56라운드 Q30: 이펙트도 8행 시트로 통일 — 행 = 몸·무기 시트와 같은 directionRows(down, up, left, right, "
                                   "down-right, down-left, up-right, up-left). 몸 시트에서 고른 행 번호를 이 시트에도 그대로 쓴다. "
                                   "대각 행(4~7)은 작업 A 가 조준 45° 로 다시 그린 붓획(별도 _diag 시트는 만들지 않음)")
        fj["bodyTimingSource"] = "player_%s %s" % (body, bj.get("version", ""))
        fj["timingCheck"] = {"bodyHitAt": hit, "bodyImpactFrame": bj["impactFrame"], "bodyFrameStartsMs": st,
                             "fxImpactFrame": fj["impactFrame"], "spawnAtMs": spawn,
                             "rule": "spawnAtMs + sum(fx frameDurationsMs[:impactFrame]) = 몸 hitAt",
                             "checkedBy": "parts/art/work/combo56_res/gs8.py"}
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(fj, f, ensure_ascii=False, indent=1)
        rep.append("%-28s rows8 ok · body %s hitAt %d · spawnAtMs %d%s" % (fx, body, hit, spawn, " (갱신)" if changed else ""))
    return rep


if __name__ == "__main__":
    print("\n".join(build()))
