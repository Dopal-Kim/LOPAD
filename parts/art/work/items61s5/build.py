#!/usr/bin/env python3
"""61 단계 5 (P13 §3·§4) — 드랍 아이템 3시트 + 보스방 기둥 무너짐. 결정적(시드 고정).

사용: python3 parts/art/work/items61s5/build.py [--dry] [--only voucher potion fire_bottle boss1_pillar]
  --dry : assets 를 건드리지 않고 미리보기만
산출(트림 아틀라스 — 계약 §19):
  assets/sprites/items/v3/{voucher,potion,fire_bottle}       80×96 · 피벗 (40,88) · 열 24(idle 8 · spawn 8 · pickup 6 · magnet 2)
  assets/sprites/structures/v3/boss1_pillar                   160×448 · 피벗 (80,440) · 18 → 30 프레임(collapse 18~27 · rubble 28~29)
미리보기: parts/art/work/items61s5/preview_{items,items_dark,pillar,pillar_dark}.png
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kit5  # noqa: E402
from kit5 import A, R, G, CONTACT, tohex, EMISSIVE, X0, X1  # noqa: E402
import items5 as I  # noqa: E402
import pillar5 as P  # noqa: E402
import preview5  # noqa: E402

SRC = "parts/art/work/items61s5/build.py (61 단계 5 · P13)"
PAL_NOTE = ("parts/art/palette/lopad.json gray + 1층 램프 16~27 + floors[6] '적' 램프(물약 붉은 술·인주) + v2 재질 SL·WD·PL "
            "(v2_outer/palette_v2_proposal.json) + 백열 X0/X1 — 새 색 없음. paletteSwap 없음(층마다 같은 색)")
EMIS_BASE = [tohex(c) for c in EMISSIVE]

ITEM_INFO = {
    "voucher": dict(
        kindNames={"small": "전표 몇 장", "mid": "전표 한 묶음", "large": "전표 무더기"},
        kindRule={"by": "줍는 전표 양", "small": "1~5", "mid": "6~14", "large": "15 이상",
                  "note": "경계는 시스템 데이터 economy.json pickup.voucherSize(mid 6 · large 15, 61 단계 5 작업 중 값)가 기준 — 바뀌면 데이터를 따른다"},
        look="잔(盞) 낙인 찍힌 종이 군표 — 바랜 종이 + 호박 인쇄 테두리 + 그을린 잔 낙인 + 붉은 인주. small = 낱장 2, mid = 끈 묶음 1 + 낱장, large = 묶음 3 무더기 + 낱장 2",
        light=None,
        lightByKind={"small": None, "mid": None,
                     "large": {"color": "#e2a33c", "radius": 36, "intensity": 0.35, "offset": {"x": 40, "y": 74}}},
        emissive=EMIS_BASE, sizeDots={"small": [26, 14], "mid": [34, 20], "large": [48, 30]}),
    "potion": dict(
        kindNames={"potion": "잔의 독주"},
        look="둥근 유리 약병 — 붉은 술이 몸 3/4(속에서 빛남, 자체 발광) + 검붉은 밀랍 코르크 + 목 끈의 작은 놋 패",
        light={"color": "#d65457", "radius": 40, "intensity": 0.5, "offset": {"x": 40, "y": 76}},
        emissive=EMIS_BASE + [tohex(R[i]) for i in (8, 9, 10, 11)], sizeDots={"potion": [24, 35]}),
    "fire_bottle": dict(
        kindNames={"fire_bottle": "화염 술병"},
        look="목 긴 짙은 유리병 + 호박 술(비발광) + 목에 쑤셔 넣은 헝겊 심지 끝 작은 불(자체 발광) + 잔 낙인 딱지 — consumable_f1 행 fire_bottle 의 작은 판",
        light={"color": "#eebb6d", "radius": 64, "intensity": 0.8, "flicker": {"amp": 0.25, "hz": 7}, "offset": {"x": 47, "y": 52}},
        emissive=EMIS_BASE, sizeDots={"fire_bottle": [22, 44]},
        replaces="items/v3/consumable_f1 행 fire_bottle 의 월드 드롭 용도(바닥에 떨어진 것). consumable_f1 은 지우지 않음 — 진열대(행상 매트) 등 기존 쓰임은 시스템 판단"),
}


def item_meta(kind, rows):
    info = ITEM_INFO[kind]
    ncol = I.NCOL
    glow = sorted(r * ncol + c for r in range(len(rows)) for c in I.GLOW_COLS)
    m = {
        "directions": ["any"] * len(rows),
        "layout": "row = kind(rowsAre·kinds 순서), column = 프레임(상태는 열 번호)",
        "frameIndex": "row * columns + column (§19 아틀라스 키)",
        "version": "v3-r61s5",
        "rowsAre": "kinds", "kinds": rows, "kindNames": info["kindNames"],
        "kindNamesNote": "이름 임시(스토리·데이터 이름이 우선). HUD·메뉴 아이콘은 UI 파트 몫",
        "pivot": {"x": I.PIV[0], "y": I.PIV[1]}, "anchor": "ground",
        "anchorRule": "pivot = 바닥 접점(그림자 가운데). 물건 높이(튀어 오름·둥실)는 그림에 들어 있다 — 시스템은 바닥 위치만 옮긴다",
        "depth": "y",
        "statesAre": "columns — 같은 행 안에서 프레임 번호 = row * columns + column",
        "states": {"idle": I.IDLE, "spawn": I.SPAWN, "pickup": I.PICKUP, "magnet": I.MAGNET},
        "stateLoop": {"idle": True, "spawn": False, "pickup": False, "magnet": True},
        "stateNext": {"spawn": "idle", "pickup": None, "magnet": "magnet"},
        "stateMs": {"idle": sum(I.MS[0:8]), "spawn": sum(I.MS[8:16]), "pickup": sum(I.MS[16:22]), "magnet": sum(I.MS[22:24])},
        "stateNote": ("idle = 바닥에서 살짝 둥실 + 빛 띠가 지나가고 별 반짝(어두운 바닥에서 찾게). "
                      "spawn = 떨어질 때 1회: 바닥 팝(백열) → 늘어나며 솟음 → 꼭대기(열 11, 22도트) → 떨어짐 → 착지 눌림 + 먼지(열 14) → idle. "
                      "시스템이 흩뿌림 수평 이동만 같은 530ms 동안 tween 하면 포물선이 된다(높이는 그림). "
                      "magnet = 자석으로 끌려가는 동안 반복(그림자 없음, 그린 축 '위'로 늘어남 + 꼬리 속도선). "
                      "pickup = 획득 확정 순간 1회: 눌림 → 위로 늘어나 빨려 듦 → 백열 팝 → 불티, 끝나면 제거"),
        "spawn": {"peakDots": 22, "peakColumn": 11, "landColumn": 14, "popColumn": 8,
                  "note": "높이는 그림에 포함. 시스템이 따로 포물선 높이를 주는 방식(옛 consumable_f1)이라면 spawn 대신 idle 을 쓰면 된다"},
        "magnet": {"drawnAxis": "up", "rotate": "allowed",
                   "rotateRule": "rotation = atan2(target.y − y, target.x − x) + π/2 (그린 축 위 → 주인공 쪽). 돌리지 않아도 읽힘",
                   "liftDots": 8},
        "pickup": {"flashColumn": 19, "removeAfter": True},
        "shadow": True,
        "shadowNote": ("접지 그림자 포함(반투명 1색 rgba(10,11,16,≤110) — 구조물 접지 그림자와 같은 색). idle·spawn(높이에 따라 작아짐)·pickup 16~17 에만 있고 "
                       "magnet·pickup 18~21 은 없음. 시스템이 그림자를 따로 그리지 않는다"),
        "glowColumns": I.GLOW_COLS,
        "glowFrames": glow,
        "glowNote": "백열 X0/X1 이 있는 프레임(스폰 팝 · 흡수 섬광). 그 밖 프레임의 반짝임은 호박 A23~A27(자체 발광)",
        "emissiveColors": info["emissive"],
        "emissiveNote": "어둠 속에서도 보이는 색(조명 위 자체 발광): 반짝임 별·빛 띠 일부·불꽃" + (" · 물약 붉은 술 속 빛(R8~R11)" if kind == "potion" else ""),
        "light": info["light"],
        "lightNote": "아트 제안 — offset = 프레임 왼쪽 위 기준 도트, radius 도트(구조물 JSON 과 같은 규칙). 바닥에 많이 깔리면 광원 상한 때문에 생략해도 된다(emissive 만으로 보임)",
        "sizeDots": info["sizeDots"],
        "sizeNote": "쉴 때 물건 크기(도트, 그림자 제외) — 64도트 = 1칸이라 화면에서 반 칸 안팎",
        "look": info["look"],
        "floor": "any", "paletteSwap": False, "palette": PAL_NOTE, "source": SRC + " · items5.py",
    }
    if "lightByKind" in info:
        m["lightByKind"] = info["lightByKind"]
    if "kindRule" in info:
        m["kindRule"] = info["kindRule"]
    if "replaces" in info:
        m["replaces"] = info["replaces"]
    return m


def build_items(only, stats):
    out = {}
    pal = kit5.palette_set()
    for kind, spec in I.KINDS.items():
        if only and kind not in only:
            continue
        rows = spec["rows"]
        fr = []
        for row in rows:
            fr += I.frames_for(kind, row)
        cols = kit5.check_frames(fr, kind)
        bad = cols - pal
        assert not bad, (kind, "new colors", bad)
        for r in range(len(rows)):           # glow 열 밖 백열 0
            for cidx in range(I.NCOL):
                if cidx in I.GLOW_COLS:
                    continue
                im = fr[r * I.NCOL + cidx]
                assert not any(p[3] and p[:3] in (X0[:3], X1[:3]) for p in im.get_flattened_data()), (kind, r, cidx, "white outside glow")
        meta = item_meta(kind, rows)
        meta["colors"] = len(cols)
        kit5.write_grid("items", kind, fr, I.FW, I.FH, meta, rows=len(rows), durations=I.MS, loop=False)
        stats[kind] = dict(frame=[I.FW, I.FH], rows=len(rows), cols=I.NCOL, colors=len(cols))
        out[kind] = (rows, fr)
        print(kind, stats[kind])
    return out


def build_pillar(stats):
    old, col = P.collapse_frames()
    rub = P.rubble_frames()
    assert len(old) == 18 and len(col) == 10 and len(rub) == 2
    fr = old + col + rub
    new = col + rub
    cols = kit5.check_frames(new, "boss1_pillar")
    bad = cols - kit5.palette_set()
    assert not bad, ("pillar new colors", bad)
    base = json.load(open(os.path.join(HERE, "before61s5", "boss1_pillar_meta.json"), encoding="utf-8"))
    meta = {k: v for k, v in base.items() if k not in ("image", "action", "frameWidth", "frameHeight", "frames",
                                                         "framesPerDirection", "frameDurationsMs", "loop", "pixelScale")}
    ms = list(base["frameDurationsMs"]) + [70, 70, 80, 80, 90, 110, 120, 130, 140, 160] + [220, 1000]
    states = dict(base["states"])
    states["collapse"] = list(range(18, 28))
    states["rubble"] = [28, 29]
    states["rubble_idle"] = [29]
    hold = dict(base["stateHold"])
    hold["rubble"] = 29
    stages = dict(base["stages"])
    stages["4"] = {"enter": "collapse", "then": "rubble", "idle": "rubble_idle", "hit": None}
    solid = {k: True for k in states}
    solid["rubble"] = False
    solid["rubble_idle"] = False
    meta.update({
        "version": "v3-r61s5",
        "states": states, "stateHold": hold, "stages": stages,
        "stateNext": {"collapse": "rubble"},
        "solidByState": solid,
        "collapse": {"impactFrame": 23, "solidOffFrame": 23, "dustFrames": [23, 24, 25, 26, 27],
                     "ms": sum(ms[18:28]),
                     "note": ("18 흔들림·금에서 먼지 → 19~21 금 자리(impactPoint 높이)에서 윗동이 주저앉으며 기욺·아랫동 머리가 깨짐 → "
                              "22 주두와 윗동 머리만 남아 먼지 기둥 속으로 → 23 땅에 부딪힘(가장 큰 먼지 — 흔들림·소리 자리) → 24~27 먼지가 옆으로 퍼지며 "
                              "얇아지고 잔해가 드러남. 충돌 판정은 23 에서 끄기를 제안(solidOffFrame) — 그 전에 끄면 먼지 뒤에서 주인공이 기둥 자리로 들어가 보임")},
        "rubble": {"heightDots": 40, "footprint": [2, 2], "occludeAbove": 0, "depthHint": "below_actors",
                   "note": ("낮은 잔해 = 기단(2단) + 누운 드럼 2 · 주두 판 · 돌무더기 · 떨어진 휘장. 위로 솟은 높이 약 40도트(윗단 윗면 330 기준 약 10) — "
                            "통과 가능. 주인공·적이 위를 걸으므로 액터 아래(바닥 데칼·소품과 같은 층)에 그리기를 제안, occludeAbove 0")},
        "occludeAboveByState": {"rubble": 0, "rubble_idle": 0},
        "stateNote": ("61라운드 AR-5 균열 3단 + 61 단계 5(P13 §3) 무너짐. 0~2 = 54라운드(idle · hit), 3~17 = 균열 3단(61 단계 2·3 그대로). "
                      "3단에서 다음 충돌 → 'collapse'(18~27, 1회) → 'rubble'(28 남은 먼지·구르는 돌 → 29 유지, stateHold). rubble 은 solid 아님(solidByState)."),
        "changed61s5": ["프레임 18 → 30(뒤에 덧붙임, 0~17 픽셀 불변)", "states collapse·rubble·rubble_idle", "stateHold.rubble", "stages.4",
                        "solidByState", "collapse", "rubble", "occludeAboveByState", "stateNext"],
        "previous": "61 단계 2·3: 18프레임(0~2 54라운드 idle·hit + 균열 3단). 무너짐 없음",
        "source": SRC + " · pillar5.py (0~17 = before61s5/boss1_pillar_grid.png 사본 — boss61/readable.py 산출)",
    })
    meta["colors"] = len(cols | kit5.check_frames(old, "boss1_pillar_old", allow_edge=True))
    kit5.write_grid("structures", "boss1_pillar", fr, P.PW, P.PH, meta, rows=1, durations=ms, loop=False)
    stats["boss1_pillar"] = dict(frame=[P.PW, P.PH], rows=1, cols=len(fr), colors=meta["colors"])
    print("boss1_pillar", stats["boss1_pillar"])
    return old, col, rub


def check_pillar_kept():
    """아틀라스로 바꾼 뒤 0~17 이 입력 사본과 픽셀 그대로인지."""
    from PIL import ImageChops
    grid = kit5.gridsheet.open_grid(os.path.join(kit5.SPR, "structures", "v3", "boss1_pillar.json"))
    old = P.old_frames()
    for i, f in enumerate(old):
        g = grid.crop((i * P.PW, 0, (i + 1) * P.PW, P.PH))
        a = f.copy(); b = g.copy()
        for im in (a, b):
            px = im.load()
            for y in range(im.height):
                for x in range(im.width):
                    if px[x, y][3] == 0:
                        px[x, y] = (0, 0, 0, 0)
        assert ImageChops.difference(a, b).getbbox() is None, ("pillar frame changed", i)
    print("boss1_pillar 0~17 픽셀 불변 확인")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    kit5.DRY = a.dry
    stats = {}
    items = build_items(a.only, stats)
    pil = None
    if not a.only or "boss1_pillar" in a.only:
        pil = build_pillar(stats)
    if not a.dry:
        for r in kit5.to_atlas():
            print("atlas", r)
        if pil:
            check_pillar_kept()
        p = os.path.join(HERE, "stats.json")
        old = json.load(open(p)) if os.path.exists(p) else {}
        old.update(stats)
        json.dump(old, open(p, "w"), ensure_ascii=False, indent=1)
    if items:
        preview5.ITEM_INFO = ITEM_INFO
        preview5.items_preview(items)
    if pil:
        preview5.pillar_preview(*pil)


if __name__ == "__main__":
    main()
