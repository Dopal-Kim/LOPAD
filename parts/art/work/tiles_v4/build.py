#!/usr/bin/env python3
# [53라운드 Q73] 목업 속 캐릭터를 v3 그림으로 교체 — player/v3·enemies/v3 시트(96×144·128×176 도트, pixelScale 0.5)를 Scene.render_hi(내부 렌더 1920×1080 = 월드 ×4)에 도트 1:1 로 놓는다.
"""LOPAD 바닥 타일 v4 (48라운드 Q5, 계약 art-assets §6.4) — 1·2층 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_v4/build.py
산출: assets/tiles/stage1.png/json, assets/tiles/stage2.png/json (인덱스 표 v3, 128x80 — tilecommon2.Sheet2 로 JSON 동일 형식)
      parts/art/work/tiles_v4/stage1/·stage2/ preview.png · preview_seam.png (시트 6배 · 이음 4배)
      parts/art/work/tiles_v4/preview_x2.png — **카메라 2배 목업** (1층 전투·여정·보스, 2층 전투; 각 1920x1080 내부 렌더 = 논리 960x540 = 30x17타일)
      53라운드 Q73: 캐릭터 = v3 시트(주인공 96×144 pivot (48,138)·적 v3, pixelScale 0.5 → 화면 48×72). 타일·구조물·보스(구판 월드 px)는 ×4 최근접.
검사: python3 parts/art/work/tiles_floors/check_json.py (8개 층 JSON 동일성)
이전 판(37·40라운드 흙바닥)은 tiles_stage1/·tiles_stage2/build.py — v4 로 대체됨(실행하면 v4 를 덮어쓰므로 막아 둠).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pave  # noqa: E402
import tilecommon2 as tc2  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import stage1  # noqa: E402
import stage2  # noqa: E402

T = pave.T
try:
    LABEL_FONT = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 30)   # 1920 패널용 큰 글씨
except Exception:  # pragma: no cover
    LABEL_FONT = None


def build_stage(mod, stage):
    here = os.path.join(HERE, "stage%d" % stage)
    os.makedirs(here, exist_ok=True)
    sh = tc2.Sheet2(stage, mod.NAME, mod.tiles(), mod.PROPS, [19, 21, 23, 25], here, stage)
    sh.build_sheet()
    sh.preview_sheet()
    sh.preview_seam()
    sh.stats()
    return sh


# ---------------------------------------------------------------------- 2배 목업
def spr(rel, name, row=0, col=0, floor=1):
    img, m = pave.sprite(rel, name, row, col)
    return pave.ramp_swap(img, 1, floor), (m["pivot"]["x"], m["pivot"]["y"])


def char(sc, rel, name, row, col, foot_x, foot_y, floor=1):
    """v3 캐릭터(player/v3·enemies/v3) — 도트 시트를 발 위치(월드 px)에 1:1 로."""
    img, m = pave.sprite(rel, name, row, col)
    sc.put_sprite_dots(pave.ramp_swap(img, 1, floor), (m["pivot"]["x"], m["pivot"]["y"]), foot_x, foot_y, m.get("pixelScale", 0.5))


def scene_battle1(sh):
    kinds = ["trial_%d" % i for i in range(4)]
    sc = pave.Scene(sh.tile_img, kinds, seed=5)
    P = sh.prop_names
    for (tx, ty), nm in {(6, 12): P[1], (19, 4): P[1], (24, 13): P[2], (13, 15): P[7], (27, 7): P[4], (3, 4): P[3]}.items():
        sc.put_prop(tx, ty, nm)
    for rel, nm, tx, ty in [("structures", "barrel", 9, 4), ("structures", "still", 22, 9), ("structures", "crate_f1", 4, 15)]:
        img, pv = spr(rel, nm)
        sc.put_sprite(img, pv, tx * T + 8, ty * T + 16)
    char(sc, "player/v3", "player_idle", 0, 0, 15 * T + 8, 9 * T + 12)
    for nm, row, x, y in [("dummy_idle", 2, 20 * T, 7 * T), ("charger_idle", 2, 21 * T, 12 * T), ("archer_idle", 3, 9 * T, 10 * T)]:
        char(sc, "enemies/v3", nm, row, 1, x, y)
    return sc.render_hi(0, 0, extra_py=-T)


def scene_journey1(sh):
    kinds = ["start_%d" % i for i in range(4)]
    sc = pave.Scene(sh.tile_img, kinds, seed=8)
    P = sh.prop_names
    for (tx, ty), nm in {(8, 12): P[1], (22, 5): P[4]}.items():
        sc.put_prop(tx, ty, nm)
    for rel, nm, tx, ty in [("structures", "grave", 6, 6), ("structures", "bonfire", 21, 11)]:
        img, pv = spr(rel, nm)
        sc.put_sprite(img, pv, tx * T + 8, ty * T + 16)
    char(sc, "player/v3", "player_idle", 0, 0, 14 * T + 8, 9 * T + 12)
    for nm, row, x, y in [("dummy_idle", 2, 19 * T, 8 * T), ("dummy_idle", 3, 10 * T, 13 * T)]:
        char(sc, "enemies/v3", nm, row, 2, x, y)
    return sc.render_hi(0, 0, extra_py=-T)


def scene_boss1(sh):
    kinds = ["boss_%d" % i for i in range(4)]
    sc = pave.Scene(sh.tile_img, kinds, seed=13)
    char(sc, "player/v3", "player_idle", 2, 0, 19 * T + 8, 10 * T + 4)
    img, pv = spr("bosses", "stage1_idle", 3, 0)
    sc.put_sprite(img, pv, 11 * T, 9 * T)
    sc.put_prop(25, 4, sh.prop_names[6]); sc.put_prop(4, 13, sh.prop_names[0])
    return sc.render_hi(0, 0, extra_py=-T)


def scene_battle2(sh):
    kinds = ["trial_%d" % i for i in range(4)]
    sc = pave.Scene(sh.tile_img, kinds, seed=21)
    P = sh.prop_names
    for (tx, ty), nm in {(6, 12): P[0], (19, 3): P[7], (25, 14): P[7], (13, 15): P[2], (3, 4): P[3], (27, 6): P[4]}.items():
        sc.put_prop(tx, ty, nm)
    for rel, nm, tx, ty in [("structures", "roulette", 23, 10), ("structures", "bet_bell", 8, 4), ("structures", "crate_f2", 4, 15)]:
        img, pv = spr(rel, nm, floor=2)
        sc.put_sprite(img, pv, tx * T + 8, ty * T + 16)
    img, pv = spr("structures", "dog_ring", floor=2)
    sc.put_sprite(img, pv, 9 * T, 14 * T)
    char(sc, "player/v3", "player_idle", 0, 0, 15 * T + 8, 9 * T + 12, floor=2)
    for nm, row, x, y in [("dummy_idle", 2, 19 * T, 6 * T), ("charger_idle", 2, 18 * T, 12 * T), ("archer_idle", 3, 11 * T, 8 * T)]:
        char(sc, "enemies/v3", nm, row, 1, x, y, floor=2)
    return sc.render_hi(0, 0, extra_py=-T)


def preview_x2(sh1, sh2):
    panels = [("1층 잔 · 전투 노드 (trial)", scene_battle1(sh1), 1),
              ("1층 잔 · 여정 노드 (start, 황폐한 평화지역)", scene_journey1(sh1), 1),
              ("1층 잔 · 보스 (boss)", scene_boss1(sh1), 1),
              ("2층 패 · 전투 노드 (trial)", scene_battle2(sh2), 2)]
    W, H, gap = 1920, 1080, 16            # 53라운드 Q73: 내부 렌더 1배(도트 1:1) — v3 캐릭터 도트가 뭉개지지 않게
    out = Image.new("RGB", (2 * W + 3 * gap, 2 * H + 3 * gap), (60, 60, 64))
    for i, (lab, img, fl) in enumerate(panels):
        big = img.resize((W, H), Image.NEAREST) if img.size != (W, H) else img.copy()
        pave.label(big, "%s   accent %.2f%%   (1920x1080 내부 렌더, 캐릭터 v3)" % (lab, 100 * pave.accent_ratio(img, fl)),
                   (12, 8), LABEL_FONT)
        out.paste(big.convert("RGB"), (gap + (i % 2) * (W + gap), gap + (i // 2) * (H + gap)))
        big.convert("RGB").save(os.path.join(HERE, "stage%d" % fl, "x2_%d.png" % i))
    out.save(os.path.join(HERE, "preview_x2.png"))
    print("preview_x2.png", out.size)


if __name__ == "__main__":
    s1 = build_stage(stage1, 1)
    s2 = build_stage(stage2, 2)
    preview_x2(s1, s2)
