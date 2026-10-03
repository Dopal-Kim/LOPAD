#!/usr/bin/env python3
# [53라운드 보관] 이 스크립트가 미리보기·목업·마스크 입력으로 읽던 구 시트(assets/sprites/player/player_*, player/v2/*, enemies/{dummy,archer,charger}_*, enemies/v2/*, weapons/katana_* 중 아이콘 외, weapons/v2/*)는 삭제됨 — 해당 단계는 재실행 시 FileNotFoundError.
"""LOPAD 1층 지역 타일셋 5종 (49라운드 4-2·7, 계약 art-assets §7.3) — 단일 소스. 재실행 시 전부 재생성.

실행: python3 parts/art/work/tiles_regions/build.py            (타일 5종 + 미리보기)
      python3 parts/art/work/tiles_regions/build.py --only outer
산출: assets/tiles/stage1_{waste,gate,outer,brewery,hall}.png/json (인덱스 표 v3, 128x80)
      parts/art/work/tiles_regions/<region>/preview.png · preview_seam.png (시트 6배 · 이음 4배)
      parts/art/work/tiles_regions/preview_x2_<region>.png — **카메라 2배 목업 960x540** (지역 화면 한 장)
      parts/art/work/tiles_regions/preview_x2_all.png — 다섯 지역 축소 비교(여정 순서)
검사: python3 parts/art/work/tiles_floors/check_json.py   (stage1~8 + stage1_* 지역 JSON 형식 동일성)
세트 소품 배치 예시(휴식 광장·상점 거리)는 parts/art/work/structures/build_sets.py 가 이 시트를 읽어 만든다.
"""
import importlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rkit as K  # noqa: E402
from PIL import Image  # noqa: E402

T = K.T
REGIONS = ["waste", "gate", "outer", "brewery", "hall"]
TITLE = {"waste": "황무지·전장", "gate": "성문", "outer": "외곽 거리", "brewery": "양조 구역", "hall": "지배자의 연회장"}


def build_region(region):
    mod = importlib.import_module(region)
    here = os.path.join(HERE, region)
    os.makedirs(here, exist_ok=True)
    sh = K.RegionSheet(region, mod.NAME, mod.tiles(), mod.PROPS, here)
    sh.build_sheet()
    sh.preview_sheet()
    sh.preview_seam()
    sh.report()
    return sh


# ---------------------------------------------------------------------- 지역별 2배 목업 (30x17)
def chars(a, spots):
    """spots: [(rel, name, row, col, tx, ty)] — 발 피벗을 타일 (tx, ty) 아래 가운데에."""
    for rel, nm, row, col, tx, ty in spots:
        a.put_char(rel, nm, row, col, tx * T + 8, ty * T + 14)


def has(name):
    return os.path.exists(os.path.join(K.SPR, "structures", name + ".png"))


def sets(a, items):
    """세트 소품·전장 소품(structures/build_sets.py 산출물)이 있으면 얹는다 — 지역 타일과 구조물이 한 화면에서 어울리는지 보려고."""
    for it in items:
        name, tx, ty = it[:3]
        state = it[3] if len(it) > 3 else "idle"
        if has(name):
            a.put_struct(name, tx, ty, state, 1)


def wisps(a, pts):
    if not os.path.exists(os.path.join(K.SPR, "fx", "soul_wisp.png")):
        return
    for i, (tx, ty) in enumerate(pts):
        im, m = K.load_sprite("fx", "soul_wisp", col=(i * 3) % 8)
        a.put(im, (m["pivot"]["x"], m["pivot"]["y"]), tx * T + 8, ty * T + 8)


def scene(sh, region):
    P = sh.prop_names
    if region == "waste":
        a = K.Arena(sh, "start", (2, 2, 27, 15), seed=4)
        for (tx, ty), k in {(6, 5): 0, (21, 4): 1, (24, 13): 3, (9, 13): 2, (4, 9): 7, (12, 4): 6}.items():
            a.prop(tx, ty, P[k])
        sets(a, [("battlefield_banner", 8, 7, "active"), ("battlefield_weapon", 18, 6), ("battlefield_fallen", 15, 12),
                 ("tutorial_sign_move", 13, 10, "active"), ("battlefield_dummy", 22, 9)])
        wisps(a, [(4, 4), (25, 6), (11, 14), (19, 3)])
        chars(a, [("player", "player_idle", 0, 0, 14, 8), ("enemies", "charger_idle", 3, 1, 7, 12)])
    elif region == "gate":
        a = K.Arena(sh, "trial", (2, 2, 27, 15), seed=7)
        for (tx, ty), k in {(5, 4): 0, (24, 4): 0, (4, 13): 1, (25, 13): 5, (11, 11): 3, (8, 8): 6, (21, 10): 2, (19, 13): 4}.items():
            a.prop(tx, ty, P[k])
        for x in (14, 15):
            for y in (2, 3):
                a.tile(x, y, "exit")
        a.tile(14, 1, "door_open"); a.tile(15, 1, "door_open")
        sets(a, [("set_gate_brazier", 12, 3, "active"), ("set_gate_brazier", 17, 3, "active")])
        chars(a, [("player", "player_idle", 1, 0, 14, 10), ("enemies", "charger_idle", 2, 1, 20, 8), ("enemies", "archer_idle", 3, 1, 8, 6)])
    elif region == "outer":
        a = K.Arena(sh, "trial", (2, 2, 27, 14), seed=11)
        for (tx, ty), k in {(4, 4): 0, (13, 13): 7, (20, 12): 1, (7, 11): 4, (23, 8): 2, (10, 3): 5}.items():
            a.prop(tx, ty, P[k])
        a.put_struct("barrel", 17, 4); a.put_struct("still", 5, 8); a.put_struct("crate_f1", 26, 13)
        sets(a, [("set_outer_lamppost", 3, 13, "active"), ("set_outer_lamppost", 25, 4, "active"), ("set_outer_stall_side", 21, 3)])
        chars(a, [("player", "player_idle", 0, 0, 15, 9), ("enemies", "dummy_idle", 2, 1, 20, 7), ("enemies", "charger_idle", 2, 1, 21, 12), ("enemies", "archer_idle", 3, 1, 9, 10)])
    elif region == "brewery":
        a = K.Arena(sh, "trial", (2, 2, 27, 14), seed=13)
        for (tx, ty), k in {(24, 6): 2, (12, 12): 1, (20, 11): 1, (8, 9): 6, (26, 12): 3, (17, 6): 7, (3, 13): 5}.items():
            a.prop(tx, ty, P[k])
        a.put_struct("still", 22, 6); a.put_struct("cask", 9, 5)
        sets(a, [("set_brewery_barrel_stack", 3, 4), ("set_brewery_barrel_stack", 13, 3)])
        chars(a, [("player", "player_idle", 0, 0, 15, 9), ("enemies", "charger_idle", 2, 1, 19, 12), ("enemies", "archer_idle", 3, 1, 7, 12)])
    else:
        a = K.Arena(sh, "boss", (3, 2, 26, 15), seed=17)
        for (tx, ty), k in {(5, 4): 2, (24, 4): 2, (8, 12): 0, (20, 13): 1, (6, 9): 6, (17, 12): 7, (14, 14): 0}.items():
            a.prop(tx, ty, P[k])
        sets(a, [("set_hall_long_table", 5, 6), ("set_hall_long_table", 21, 6)])
        chars(a, [("player", "player_idle", 1, 0, 15, 12)])
        im, m = K.load_sprite("bosses", "stage1_idle", 0, 0)
        a.put(im, (m["pivot"]["x"], m["pivot"]["y"]), 15 * T, 7 * T)
    return a


def mock(sh, region):
    a = scene(sh, region)
    img = a.render()
    big = K.x2(img).convert("RGB")
    K.label(big, "1층 · %s (%s)   bright accent %.2f%%" % (TITLE[region], region, 100 * K.bright_ratio(img)))
    big.save(os.path.join(HERE, "preview_x2_%s.png" % region))
    return img


def overview(imgs):
    """다섯 지역을 여정 순서로 1배(=480x270)씩 세로로. 축소 비교용."""
    W, H, gap = 480, 270, 6
    out = Image.new("RGB", (W * 2 + gap * 3, (H + gap) * 3 + gap), (40, 40, 44))
    for i, (r, im) in enumerate(imgs):
        x = gap + (i % 2) * (W + gap)
        y = gap + (i // 2) * (H + gap)
        tile = im.convert("RGB").copy()
        K.label(tile, "%d %s" % (i + 1, TITLE[r]), font=K.FONT_S)
        out.paste(tile, (x, y))
    out.save(os.path.join(HERE, "preview_x2_all.png"))


if __name__ == "__main__":
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else REGIONS
    imgs = []
    for r in REGIONS:
        if r not in only:
            continue
        sh = build_region(r)
        imgs.append((r, mock(sh, r)))
    if len(imgs) == len(REGIONS):
        overview(imgs)
