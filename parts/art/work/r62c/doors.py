"""62 루프 3 (P17 묶음 B) 입구 그림 단계: 저주 길 2장 → 작은 판(전부) → doors.json 색인 갱신."""
import glob
import os

import doors_curse
import doors_small
import figures as F
from c62 import PAINT, SRC, load_json, save_json

# 사연 카드 인물(두건 쓴 사람이 등을 들고 앉음) — 작은 판 좌표(512×288)의 발 자리 · 등 쪽
EVENT_FIG = {
    "door_outer_event": (150, 216, "right"),
    "door_brewery_event": (120, 222, "right"),
}


def event_overlay(name):
    fx, fy, facing = EVENT_FIG[name]

    def ov(im, meta, box):
        f, lamp = F.hooded_sitter(facing)
        out = F.place(im, f, fx, fy)
        return F.lamp_glow(out, fx - f.size[0] // 2 + lamp[0], fy - f.size[1] + lamp[1])
    return ov


def all_doors():
    return sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(PAINT, "door_*.png"))
                  if not p.endswith("_small.png"))


def update_index(names):
    idx = load_json(os.path.join(PAINT, "doors.json"))
    for n in names:
        m = load_json(os.path.join(PAINT, n + ".json"))
        key = n[len("door_"):]
        if key not in idx["doors"]:
            idx["doors"][key] = {"image": n + ".png", "json": n + ".json", "doorRect": m["doorRect"],
                                 "light": m["light"]["color"]}
        if os.path.exists(os.path.join(PAINT, n + "_small.png")):
            idx["doors"][key]["small"] = n + "_small.png"
            idx["doors"][key]["smallJson"] = n + "_small.json"
    idx["risk"] = {
        "elite": "<region>_elite", "curse": "<region>_curse",
        "note": "62 루프 3: 위험 노드(bundle2 risk elite·curse)는 노드 종류가 battle 이라 kind 로는 못 찾는다 — 미리보기·전환에서 "
                "risk 가 있으면 door_<region>_<risk> 를 먼저 찾고(없으면 기존 순서). 1층: outer·brewery 둘 다 elite·curse 있음",
    }
    idx["small"] = {
        "suffix": "_small", "size": [512, 288],
        "note": "62 루프 3 지도 미리보기 카드(UI §25 256×144 논리 × res 2) 전용 판 — 원본을 입구 둘레로 1:1 자른 것 + 밝기·대비 한 단 + 입구 빛. "
                "카드에서는 paint/door_<…>_small 이 매니페스트에 있으면 그것, 없으면 원본(같은 'cover' 맞춤). 사연 카드는 인물(등 든 두건 쓴 사람) 덧그림",
    }
    idx["usedFloor1_r62c"] = ("route.json 62: 여정 birth·road → waste_battle(별칭), post → gate_rest(별칭) / 단1 outer 전투 / 단2 outer 전투·사연 / "
                              "단3 brewery 전투 / 단4 brewery 장터·쉼터 / 보스 hall_boss. 위험(단2·단3 전투 하나) elite·curse → outer_·brewery_{elite,curse}. "
                              "전 조합 그림 있음")
    idx["source_r62c"] = SRC
    save_json(os.path.join(PAINT, "doors.json"), idx)
    return idx


def build():
    made = [n for n, _ in doors_curse.build()]
    names = all_doors()
    for n in names:
        doors_small.make_small(n, overlay=event_overlay(n) if n in EVENT_FIG else None)
    update_index(names)
    return made, names
