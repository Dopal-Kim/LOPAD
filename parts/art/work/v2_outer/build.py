#!/usr/bin/env python3
"""50라운드 시범(1층 외곽 거리) v2 빌드 — 실행: python3 parts/art/work/v2_outer/build.py

내보냄 (기존 파일 덮어쓰기 없음 — 모두 v2 하위 폴더):
  assets/tiles/v2/stage1_outer.png/.json
  assets/sprites/player/v2/player_{idle,walk,dash,hurt,death,katana_combo1..3}.png/.json
  assets/sprites/weapons/v2/katana_{carry_idle,carry_walk,combo1..3}.png/.json
  assets/sprites/enemies/v2/charger_{idle,walk,attack,hurt,death}.png/.json
미리보기: parts/art/work/v2_outer/preview_*.png, palette_v2_proposal.json
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kit import *
from PIL import ImageDraw
import tiles as TL, scene as SC, player as PY, katana as K, charger as CH

OUT_T = os.path.join(ROOT, "assets/tiles/v2")
OUT_P = os.path.join(ROOT, "assets/sprites/player/v2")
OUT_W = os.path.join(ROOT, "assets/sprites/weapons/v2")
OUT_E = os.path.join(ROOT, "assets/sprites/enemies/v2")
for d in (OUT_T, OUT_P, OUT_W, OUT_E):
    os.makedirs(d, exist_ok=True)

SRC = "parts/art/work/v2_outer/build.py (50라운드 시범)"
PAL_NOTE = ("parts/art/palette/lopad.json (gray + 1층 램프 16~27, 런타임 스왑) + "
            "v2 재질 블록 제안 parts/art/work/v2_outer/palette_v2_proposal.json (SL·WD·PL·NT, 임시·고정색)")
STATS = {}


def stat(name, im):
    STATS[name] = {"colors": len(colors_of(im)), "isolated": isolated(im), "size": list(im.size)}


def base_json(image, action, fw, fh, frames, ms, loop, pivot, **extra):
    d = {
        "image": image, "action": action, "frameWidth": fw, "frameHeight": fh, "frames": frames,
        "directions": DIRS, "layout": "rows = directions (down, up, left, right), columns = frames",
        "frameIndex": "row * frames + column",
        "fps": round(1000 / (sum(ms) / len(ms))), "frameDurationsMs": ms, "loop": loop,
        "pivot": {"x": pivot[0], "y": pivot[1]}, "pixelScale": 1, "palette": PAL_NOTE, "source": SRC,
    }
    d.update(extra)
    return d


# ---------------------------------------------------------------------------
# 1. 타일셋
# ---------------------------------------------------------------------------
def export_tiles():
    sheet, cells, rects = TL.build_sheet()
    sheet.save(os.path.join(OUT_T, "stage1_outer.png"))
    stat("tiles/v2/stage1_outer", sheet)
    names = {
        0: "floor_0", 1: "floor_1", 2: "floor_2", 3: "floor_3", 4: "corridor_setts",
        5: "wall_front_lower_plain", 6: "wall_top_roof", 7: "void_roofs",
        8: "door_open", 9: "door_closed", 10: "door_locked", 11: "exit_steps", 12: "shop_deck",
        13: "prop_barrel", 14: "prop_crate", 15: "prop_puddle", 16: "prop_lantern", 17: "prop_brazier",
        18: "prop_sacks", 19: "prop_tipped_barrel", 20: "prop_debris",
        21: "wall_front_lower_window_lit", 22: "wall_front_lower_door",
        23: "start_0", 24: "start_1", 25: "start_2", 26: "start_3",
        27: "trial_0", 28: "trial_1", 29: "trial_2", 30: "trial_3",
        31: "rest_0", 32: "rest_1", 33: "rest_2", 34: "rest_3",
        35: "boss_0", 36: "boss_1", 37: "boss_2", 38: "boss_3", 39: "reserve",
        40: "wall_front_upper_plain", 41: "wall_front_upper_window", 42: "wall_front_upper_sign",
        43: "stone_front_lower", 44: "stone_front_upper", 45: "stone_top", 46: "stone_front_lower_ring",
        47: "wall_top_roof_eave", 48: "wall_top_edge_e", 49: "wall_top_edge_w", 50: "wall_top_edge_n",
        51: "wall_top_corner_ne", 52: "wall_top_corner_nw",
        53: "floor_shadow_n", 54: "floor_shadow_w", 55: "floor_shadow_e", 56: "floor_shadow_nw", 57: "floor_shadow_ne",
        58: "void_chimney", 59: "void_gap", 60: "floor_drain", 61: "floor_drain_grate", 62: "floor_gravel",
        63: "wall_front_lower_window_dark",
    }
    for nm, r in rects.items():
        for k in range(r["w"] // 32 * (r["h"] // 32)):
            pass
    big_cells = {64: "big:lamp_post", 72: "big:lamp_post", 65: "big:crate_stack", 73: "big:crate_stack",
                 66: "big:stall", 67: "big:stall", 74: "big:stall", 75: "big:stall",
                 68: "big:well", 69: "big:well", 76: "big:well", 77: "big:well",
                 70: "big:washing_line", 71: "big:washing_line", 78: "big:washing_line_b", 79: "big:washing_line_b"}
    names.update(big_cells)
    L = lambda col, rad, it, fl=None, off=(16, 18): {"color": col, "radius": rad, "intensity": it,
                                                     **({"flicker": fl} if fl else {}),
                                                     "offset": {"x": off[0], "y": off[1]}}
    props = [
        {"index": 13, "name": "barrel", "solid": True, "maxPerRoom": 3, "weight": 0.9, "pivot": {"x": 16, "y": 30}, "occludeAbove": 10},
        {"index": 14, "name": "crate", "solid": True, "maxPerRoom": 2, "weight": 0.8, "pivot": {"x": 16, "y": 30}, "occludeAbove": 10},
        {"index": 15, "name": "puddle", "solid": False, "maxPerRoom": 3, "weight": 1.0, "depth": "floor"},
        {"index": 16, "name": "lantern", "solid": True, "maxPerRoom": 2, "weight": 0.6, "pivot": {"x": 16, "y": 30}, "occludeAbove": 12,
         "light": L("#e8b858", 120, 0.9, {"amp": 0.08, "hz": 5}, (16, 20))},
        {"index": 17, "name": "brazier", "solid": True, "maxPerRoom": 1, "weight": 0.5, "pivot": {"x": 16, "y": 30}, "occludeAbove": 12,
         "light": L("#eecc78", 190, 1.2, {"amp": 0.15, "hz": 7}, (16, 10))},
        {"index": 18, "name": "sacks", "solid": True, "maxPerRoom": 1, "weight": 0.6, "pivot": {"x": 16, "y": 30}, "occludeAbove": 10},
        {"index": 19, "name": "tipped_barrel", "solid": True, "maxPerRoom": 1, "weight": 0.4, "pivot": {"x": 13, "y": 26}, "occludeAbove": 8},
        {"index": 20, "name": "debris", "solid": False, "maxPerRoom": 3, "weight": 1.0, "depth": "floor"},
    ]
    big = {
        "lamp_post": {"pivot": {"x": 13, "y": 62}, "footprint": [1, 1], "solid": True, "occludeAbove": 16, "placement": "floor",
                      "light": L("#e8b858", 150, 1.0, {"amp": 0.06, "hz": 4}, (24, 22))},
        "crate_stack": {"pivot": {"x": 16, "y": 62}, "footprint": [1, 1], "solid": True, "occludeAbove": 12, "placement": "floor"},
        "stall": {"pivot": {"x": 32, "y": 62}, "footprint": [2, 1], "solid": True, "occludeAbove": 22, "placement": "floor (방 가장자리 권장)"},
        "well": {"pivot": {"x": 32, "y": 61}, "footprint": [2, 1], "solid": True, "occludeAbove": 26, "placement": "floor"},
        "washing_line": {"pivot": {"x": 0, "y": 0}, "solid": False, "placement": "wallUpper — 앞면 윗단(40~42) 위 겹침, 가로 이어붙임", "depth": "above_wall"},
        "washing_line_b": {"pivot": {"x": 0, "y": 0}, "solid": False, "placement": "wallUpper", "depth": "above_wall"},
    }
    big_list = []
    for nm, meta in big.items():
        r = rects[nm]
        big_list.append({"name": nm, "rect": {"x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"]}, "index": r["index"], **meta})
    data = {
        "image": "stage1_outer.png", "version": "v2 (50라운드 시범)", "stage": 1, "region": "outer",
        "name": "잔(盞) — 외곽 거리 v2 (쿼터뷰)",
        "tileWidth": 32, "tileHeight": 32, "columns": 8, "rows": 10, "indexFormula": "row * columns + column",
        "pixelScale": 1, "wallHeightTiles": 2,
        "tiles": {"0": [7, 7, 7, 58, 59], "1": [0, 1, 2, 3], "2": [5, 5, 5, 21, 22, 63, 63],
                  "3": [8], "4": [9], "5": [10], "6": [4], "7": [11], "8": [12]},
        "tilesNote": "목록 안 중복 = 가중치(좌표 해시 균등 선택 가정). tiles['2'] 는 벽 앞면 아랫단 변형(5·21·22 + v2 63).",
        "tileIdNames": {"0": "void", "1": "floor", "2": "wall", "3": "door_open", "4": "door_closed", "5": "door_locked",
                        "6": "corridor", "7": "exit", "8": "shop"},
        "walls": {
            "front": {"lower": [5, 5, 5, 21, 22, 63, 63], "upper": [40, 40, 40, 41, 41, 42]},
            "wallFrontUpper": 40,
            "top": 6,
            "topAboveFront": 47,
            "left": 48, "right": 49, "bottom": 50,
            "corner_tl": 48, "corner_tr": 49, "corner_bl": 51, "corner_br": 52,
            "variants": [5, 21, 22, 63],
            "stoneSet": {"lower": [43, 43, 46], "upper": [44], "top": 45,
                         "note": "돌담 세트(선택). 같은 벽 구간 전체를 이 세트로 바꿔 쓴다(칸마다 섞지 말 것)"},
            "stacking": ("바닥과 맞닿은 북쪽 벽(앞면이 보이는 벽): 바닥 바로 위 칸 = front.lower, 그 위 칸 = front.upper, "
                         "그 위 = topAboveFront(처마) → 나머지 top. 앞면 2칸(64px)은 캐릭터를 가린다(Y 정렬, 벽 기준선 = 아랫단 밑변). "
                         "서·동·남 경계는 앞면 없이 윗면만: 서쪽 경계 = left(48, 동쪽 가장자리), 동쪽 = right(49), 남쪽 = bottom(50), "
                         "남쪽 모서리 = corner_bl/br. 문(8~10)은 아랫단 자리에 둔다(위 칸은 front.upper)."),
            "note": "계약 §9: walls.front = 앞면 세로 2칸, walls.top = 윗면(6). §9 문구의 '24~ 이후 새 인덱스' 는 roomFloors(23~38)와 겹쳐 40번부터 배정 — 확인 요청",
        },
        "floorShadows": {"n": 53, "w": 54, "e": 55, "nw": 56, "ne": 57,
                         "note": "반투명(알파 4단 계단) 겹침. 바닥 위·소품 아래. 북쪽 벽 발치 12px, 서·동 8px. 시스템이 지원하지 않으면 생략 가능"},
        "floorFeatures": {"drain": 60, "drainGrate": 61, "gravel": 62,
                          "note": "선택. drain 은 가로로 이어지는 배수로(같은 행에 연속 배치)"},
        "roomFloors": {"start": [23, 24, 25, 26], "trial": [27, 28, 29, 30], "rest": [31, 32, 33, 34], "boss": [35, 36, 37, 38]},
        "roomFloorMix": TL.ROOM_FLOOR_MIX,
        "roomFloorsNote": "v3 의미 유지. start = 그을음·흙·자갈, trial = 배수구·금, rest = 다진 흙·짚, boss = 광장 큰 포석(_0 잔 각인).",
        "props": props,
        "propsNote": "32×32, 배경 투명, pivot = 바닥 접점(Y 정렬 기준). occludeAbove(px) = 피벗 위 이 높이부터 캐릭터를 가림(§9). light 는 offset(시트 칸 좌표)에서 광원.",
        "bigProps": big_list,
        "bigPropsNote": "v2 신규(선택): rect 로 자르는 큰 소품. index 는 rect 왼쪽 위 칸. 시스템이 모르면 무시해도 된다(인덱스 소품 13~20 은 단독으로 동작).",
        "tileLights": {"21": {"color": "#e2a33c", "radius": 70, "intensity": 0.55, "offset": {"x": 16, "y": 26}},
                       "22": {"color": "#dc8e23", "radius": 46, "intensity": 0.45, "offset": {"x": 26, "y": 30}}},
        "tileLightsNote": "v2 제안(선택): 불 켜진 창(21)·문틈(22) 칸을 약한 광원으로 등록",
        "emissiveColors": palette_v2_json()["emissive"],
        "emissiveNote": palette_v2_json()["emissiveNote"],
        "names": {str(k): v for k, v in sorted(names.items())},
        "palette": PAL_NOTE,
        "source": SRC,
    }
    write_json(os.path.join(OUT_T, "stage1_outer.json"), data)
    return sheet, cells, rects


# ---------------------------------------------------------------------------
# 2. 주인공 · 칼
# ---------------------------------------------------------------------------
def export_player():
    sheets = {}
    for act in ("idle", "walk", "dash", "hurt", "death"):
        fr = PY.render_action(act)
        im = sheet({d: [f[0] for f in fr[d]] for d in DIRS}, 32, 48)
        im.save(os.path.join(OUT_P, f"player_{act}.png"))
        stat(f"player/v2/player_{act}", im)
        extra = {"note": "50라운드 v2(2배 해상도). 기존 player_<action> 과 같은 프레임 수·ms. 무기 휴대 오버레이 weapons/v2/katana_carry_<action>"}
        if act == "hurt":
            extra["flashFrame"] = 0
        if act == "death":
            extra["eyeOffFrame"] = 5
        write_json(os.path.join(OUT_P, f"player_{act}.json"),
                   base_json(f"player_{act}.png", act, 32, 48, len(PY.MS[act]), PY.MS[act], PY.LOOP[act], (16, 46), **extra))
        sheets[act] = fr
    return sheets


OLD_META = {
    1: dict(hitFrames=[1], activeFrames=[1], cancelFromFrame=3, timingMs={"hitAt": 90, "cancelAt": 250, "total": 350},
            arcDeg=140, arcFromDeg=-70, arcToDeg=70, nextCombo="katana_combo2"),
    2: dict(hitFrames=[1], activeFrames=[1], cancelFromFrame=2, timingMs={"hitAt": 40, "cancelAt": 80, "total": 170},
            arcDeg=130, arcFromDeg=65, arcToDeg=-65, nextCombo="katana_combo3"),
    3: dict(hitFrames=[1], activeFrames=[1], cancelFromFrame=None, timingMs={"hitAt": 40, "cancelAt": None, "total": 320},
            arcDeg=170, arcFromDeg=-85, arcToDeg=85, nextCombo=None),
}
STATES = {1: ["sheathed", "glow", "steel", "steel"], 2: ["steel", "glow", "fade"], 3: ["steel", "glow", "steel", "embers"]}


def export_katana(player_sheets):
    combos = {}
    for n in (1, 2, 3):
        B, Wp, D = K.combo_frames(n)
        ms = K.COMBO[n]["ms"]
        meta = dict(weapon="katana", comboIndex=n, comboLength=3, **OLD_META[n],
                    hitOrigin="몸 중심 = 피벗(발)에서 위로 20px (v2 시트 픽셀)",
                    hitRadiusPx=66,
                    hitNote="임시(아트 메모). 기존 33(16×24 기준) × 2 = v2 시트 픽셀 66. 시스템 실제 판정값이 우선 — 월드 단위 환산은 시스템 결정",
                    arcAngleNote="right 방향 화면각(0 = 정면, + = 아래, from→to = 휘두름 방향). down = +90° 회전, up = -90°, left = 좌우 반전(180-θ)",
                    framesBasis=f"player_katana_combo{n} 프레임 번호 (무기·몸·이펙트 공통 기준 = 몸 시트)")
        bim = sheet(B, 32, 48)
        bim.save(os.path.join(OUT_P, f"player_katana_combo{n}.png"))
        stat(f"player/v2/player_katana_combo{n}", bim)
        write_json(os.path.join(OUT_P, f"player_katana_combo{n}.json"),
                   base_json(f"player_katana_combo{n}.png", f"katana_combo{n}", 32, 48, len(ms), ms, False, (16, 46),
                             **meta, note=f"무기를 든 연격 몸 동작. weapons/v2/katana_combo{n} 를 같은 프레임 번호·같은 시각에 겹친다(§6.1)."))
        wim = sheet(Wp, 64, 64)
        wim.save(os.path.join(OUT_W, f"katana_combo{n}.png"))
        stat(f"weapons/v2/katana_combo{n}", wim)
        dep = {d: ("below" if all(x == "below" for x in D[d]) else "above") for d in DIRS}
        write_json(os.path.join(OUT_W, f"katana_combo{n}.json"),
                   base_json(f"katana_combo{n}.png", f"combo{n}", 64, 64, len(ms), ms, False, (32, 62), **meta,
                             anchor="player_pivot", playerFrameOffset={"x": 16, "y": 16},
                             depth=dep, depthByFrame=D, occlusionBaked=True,
                             overlay=f"player_katana_combo{n} 와 같은 프레임 번호(row*frames+col)를 같은 시각에 겹친다. 피벗 (32,62) = 주인공 피벗 (16,46).",
                             frameStates=STATES[n],
                             stateNote="sheathed 칼집 안(손잡이를 쥠) · steel 실물 · glow 판정 프레임(날 호박 글로우, 끝 1px 코어) · fade 다음 타로 넘어가는 흐림 · embers 불티",
                             fxNote="베기 이펙트(fx) v2 는 이번 범위 밖 — 기존 fx/katana_combo<n> 을 2배로 쓰거나 후속 제작"))
        combos[n] = (B, Wp, D)
    carries = {}
    for act in ("idle", "walk"):
        C = K.carry_frames(act)
        im = sheet(C, 64, 64)
        im.save(os.path.join(OUT_W, f"katana_carry_{act}.png"))
        stat(f"weapons/v2/katana_carry_{act}", im)
        dep = {d: K.CARRY[d][2] for d in DIRS}
        write_json(os.path.join(OUT_W, f"katana_carry_{act}.json"),
                   base_json(f"katana_carry_{act}.png", f"carry_{act}", 64, 64, len(PY.MS[act]), PY.MS[act], True, (32, 62),
                             weapon="katana", carry="waist sheath (허리 칼집)", bodySheet=f"player_{act}",
                             anchor="player_pivot", playerFrameOffset={"x": 16, "y": 16}, depth=dep,
                             depthByFrame={d: [dep[d]] * len(PY.MS[act]) for d in DIRS}, occlusionBaked=True,
                             depthNote="down 은 칼집이 몸 뒤로 가는 부분을 몸 실루엣으로 지워 두었다(above). right 는 먼 허리라 below.",
                             overlay=f"player_{act} 와 같은 프레임 번호를 같은 시각에 겹친다. 피벗 (32,62) = 주인공 피벗 (16,46)."))
        carries[act] = C
    return combos, carries


# ---------------------------------------------------------------------------
# 3. 결사병
# ---------------------------------------------------------------------------
def export_charger():
    out = {}
    for act in ("idle", "walk", "attack", "hurt", "death"):
        fr = CH.render_action(act)
        im = sheet(fr, 32, 48)
        im.save(os.path.join(OUT_E, f"charger_{act}.png"))
        stat(f"enemies/v2/charger_{act}", im)
        extra = {"note": "50라운드 v2 결사병(2배 해상도). 기존 24×24 → 32×48."}
        if act == "attack":
            extra["phaseFrames"] = {"telegraph": [0], "charge": [1], "smash": [2], "recover": [3]}
            extra["phaseNote"] = "돌진 거리·시간은 시스템(charge.telegraphMs 등). 스프라이트는 자세만"
        if act == "hurt":
            extra["flashFrame"] = 0
        write_json(os.path.join(OUT_E, f"charger_{act}.json"),
                   base_json(f"charger_{act}.png", act, 32, 48, len(CH.MS[act]), CH.MS[act], CH.LOOP[act], (16, 46), **extra))
        out[act] = fr
    return out


# ---------------------------------------------------------------------------
# 4. 미리보기
# ---------------------------------------------------------------------------
try:
    from PIL import ImageFont
    FONT = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 13)
except Exception:  # noqa
    FONT = None


def label(im, text, xy=(4, 2), col=(235, 225, 200, 255)):
    d = ImageDraw.Draw(im)
    if FONT is not None:
        x, y = xy
        d.text((x + 1, y + 1), text, fill=(0, 0, 0, 255), font=FONT)
        d.text((x, y), text, fill=col, font=FONT)
        return
    x, y = xy
    d.text((x + 1, y + 1), text, fill=(0, 0, 0, 255))
    d.text((x, y), text, fill=col)


def preview_tiles(sheet):
    bg = Image.new("RGBA", sheet.size, (52, 54, 62, 255))
    dr = ImageDraw.Draw(bg)
    for y in range(0, sheet.height, 8):
        for x in range(0, sheet.width, 8):
            if (x // 8 + y // 8) % 2:
                dr.rectangle((x, y, x + 7, y + 7), fill=(66, 68, 76, 255))
    bg.alpha_composite(sheet)
    im = upscale(bg, 3)
    d = ImageDraw.Draw(im)
    for i in range(80):
        x, y = (i % 8) * 96, (i // 8) * 96
        d.rectangle((x, y, x + 95, y + 95), outline=(200, 80, 200, 255))
        label(im, str(i), (x + 3, y + 2))
    im.save(os.path.join(HERE, "preview_tiles.png"))


def preview_actions(fname, groups, fw, fh, k=4):
    """groups: [(title, {dir:[img]})]"""
    maxn = max(len(g[1]["down"]) for g in groups)
    W = (maxn * (fw + 4) + 40) * k
    H = sum((len(DIRS) * (fh + 4) + 14) for _ in groups) * k
    out = Image.new("RGBA", (W // k, H // k), SL[4])
    y = 0
    titles = []
    for title, fr in groups:
        titles.append((title, y))
        y += 12
        for d in DIRS:
            for i, im in enumerate(fr[d]):
                out.alpha_composite(im, (36 + i * (fw + 4), y))
            titles.append((d[:2], y + fh // 2 - 4))
            y += fh + 4
        y += 2
    out = upscale(out, k)
    for t, yy in titles:
        label(out, t, (4, yy * k))
    out.save(os.path.join(HERE, fname))


def compose_overlay(body, weapon, depth):
    cell = Image.new("RGBA", (64, 64), CLEAR)
    if depth == "below":
        cell.alpha_composite(weapon)
    cell.alpha_composite(body, (16, 16))
    if depth == "above":
        cell.alpha_composite(weapon)
    return cell


def build_mock(sheet, cells, rects, psheets, combos, carries, csheets):
    img, rows, used = SC.build_tilemap(cells)

    def big(name):
        r = rects[name]
        return sheet.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]))
    items = []   # (바닥 y, x, image, pivot)

    def prop(idx, tx, ty):
        items.append((ty * 32 + 30, tx * 32 + 16, cells[idx], (16, 30)))

    def bp(name, x, y, piv):
        items.append((y, x, big(name), piv))
    for (i, x, y) in ((13, 2, 4), (13, 3, 4), (14, 2, 5), (18, 4, 4), (16, 9, 4), (13, 26, 4), (19, 24, 5),
                      (17, 19, 9), (15, 12, 8), (15, 22, 12), (20, 7, 11), (20, 16, 13), (14, 26, 13), (13, 27, 12),
                      (15, 6, 7)):
        prop(i, x, y)
    bp("stall", 6 * 32, 14 * 32 + 30, (32, 62))
    bp("well", 24 * 32 + 16, 8 * 32 + 30, (32, 61))
    bp("lamp_post", 13 * 32 + 16, 4 * 32 + 28, (13, 62))
    bp("lamp_post", 5 * 32 + 16, 10 * 32 + 28, (13, 62))
    bp("crate_stack", 3 * 32 + 16, 13 * 32 + 30, (16, 62))
    # 캐릭터: 주인공 칼 3연격 1타(판정 프레임, 오른쪽) + 결사병 4 (걷기·돌진·찍기·사망)
    B, Wp, D = combos[1]
    pl = compose_overlay(B["right"][1], Wp["right"][1], D["right"][1])
    items.append((8 * 32 + 20, 15 * 32, pl, (32, 62)))
    items.append((6 * 32 + 10, 18 * 32, csheets["walk"]["left"][2], (16, 46)))
    items.append((10 * 32 + 6, 17 * 32 + 8, csheets["attack"]["left"][1], (16, 46)))
    items.append((11 * 32 + 4, 9 * 32, csheets["walk"]["right"][5], (16, 46)))
    items.append((7 * 32 + 24, 20 * 32 + 8, csheets["death"]["down"][5], (16, 46)))
    items.append((12 * 32 + 20, 22 * 32, csheets["attack"]["up"][0], (16, 46)))
    items.sort(key=lambda t: t[0])
    chars = {id(pl)} | {id(t[2]) for t in items if t[2].size == (32, 48)}
    for (y, x, im, piv) in items:
        if id(im) in chars:
            # 발밑 그림자(시스템이 그리는 것을 흉내: 납작 타원, 반투명)
            sh = Image.new("RGBA", (26, 8), CLEAR)
            ImageDraw.Draw(sh).ellipse((0, 0, 25, 7), fill=(10, 12, 18, 120))
            img.alpha_composite(sh, (x - 13, y - 5))
        SC.paste_sprite(img, im, x, y, piv)
    img.alpha_composite(big("washing_line"), (10 * 32, 2 * 32))
    img.alpha_composite(big("washing_line_b"), (16 * 32, 2 * 32))
    lights = SC.tile_lights(rows, used)
    lights += [
        {"x": 13 * 32 + 27, "y": 4 * 32 + 6, "color": "#e8b858", "radius": 150, "intensity": 1.0},
        {"x": 5 * 32 + 27, "y": 10 * 32 + 6, "color": "#e8b858", "radius": 150, "intensity": 1.0},
        {"x": 19 * 32 + 16, "y": 9 * 32 + 18, "color": "#eecc78", "radius": 190, "intensity": 1.2},
        {"x": 9 * 32 + 16, "y": 4 * 32 + 20, "color": "#e8b858", "radius": 110, "intensity": 0.8},
        # 주인공 주변 잔불 빛(약) + 판정 프레임 칼 글로우
        {"x": 15 * 32, "y": 8 * 32 + 6, "color": "#b0611a", "radius": 85, "intensity": 0.55},
        {"x": 15 * 32 + 22, "y": 8 * 32 - 2, "color": "#eecc78", "radius": 60, "intensity": 0.5},
    ]
    lit = light_scene(img, lights)
    return img, lit


def build():
    pv = palette_v2_json()
    write_json(os.path.join(HERE, "palette_v2_proposal.json"), pv)
    sheet_, cells, rects = export_tiles()
    psheets = export_player()
    combos, carries = export_katana(psheets)
    csheets = export_charger()
    write_json(os.path.join(HERE, "stats.json"), STATS)

    # 미리보기 시트
    preview_tiles(sheet_)
    preview_actions("preview_player.png",
                    [(a, {d: [f[0] for f in psheets[a][d]] for d in DIRS}) for a in ("idle", "walk", "dash", "hurt", "death")], 32, 48)
    kgroups = []
    for n in (1, 2, 3):
        B, Wp, D = combos[n]
        kgroups.append((f"katana_combo{n} {K.COMBO[n]['ms']}", {d: [compose_overlay(B[d][i], Wp[d][i], D[d][i]) for i in range(len(B[d]))] for d in DIRS}))
    for act in ("idle", "walk"):
        kgroups.append((f"carry_{act}", {d: [compose_overlay(psheets[act][d][i][0], carries[act][d][i], K.CARRY[d][2])
                                              for i in range(len(carries[act][d]))] for d in DIRS}))
    preview_actions("preview_katana.png", kgroups, 64, 64, k=3)
    preview_actions("preview_charger.png", [(a, csheets[a]) for a in ("idle", "walk", "attack", "hurt", "death")], 32, 48)

    # 목업
    albedo, lit = build_mock(sheet_, cells, rects, psheets, combos, carries, csheets)
    albedo.save(os.path.join(HERE, "preview_mock_albedo.png"))
    lit.save(os.path.join(HERE, "preview_mock_lit.png"))

    # 기존 2배 도트와 비교 (같은 960×540 목업끼리)
    old = os.path.join(ROOT, "parts/art/work/tiles_regions/preview_x2_outer.png")
    cmp_ = Image.new("RGB", (1920, 556), (12, 12, 16))
    if os.path.exists(old):
        cmp_.paste(Image.open(old).convert("RGB").resize((960, 540), Image.NEAREST), (0, 16))
    cmp_.paste(lit, (960, 16))
    label(cmp_, "기존 v4 (16px 도트 x2, 정면 벽·조명 없음)  tiles_regions/preview_x2_outer.png", (6, 2))
    label(cmp_, "v2 시범 (32px 타일 x1, 쿼터뷰 앞면 2칸 + 어둠·광원 합성)", (966, 2))
    cmp_.save(os.path.join(HERE, "preview_compare_old_new.png"))

    # 캐릭터 비교: 기존 16×24 를 2배 vs v2 32×48 1배 (둘 다 화면 크기 같음) → 4배 표시
    oldp = os.path.join(ROOT, "assets/sprites/player/player_idle.png")
    oldc = os.path.join(ROOT, "assets/sprites/enemies/charger_idle.png")
    ch = Image.new("RGBA", (4 * 40 + 8, 2 * 56 + 16), SL[4])
    if os.path.exists(oldp):
        op = Image.open(oldp).convert("RGBA")
        for r in range(4):
            ch.alpha_composite(upscale(op.crop((0, r * 24, 16, r * 24 + 24)), 2), (4 + r * 40, 12))
    for r, d in enumerate(DIRS):
        ch.alpha_composite(psheets["idle"][d][0][0], (4 + r * 40, 12 + 56))
    big_ = upscale(ch, 4)
    label(big_, "기존 player_idle 16×24 (2배 확대)", (6, 4))
    label(big_, "v2 player_idle 32×48 (1배)", (6, 4 + 60 * 4))
    big_.save(os.path.join(HERE, "preview_compare_player.png"))

    ce = Image.new("RGBA", (4 * 52 + 8, 2 * 56 + 16), SL[4])
    if os.path.exists(oldc):
        oc = Image.open(oldc).convert("RGBA")
        for r in range(4):
            ce.alpha_composite(upscale(oc.crop((0, r * 24, 24, r * 24 + 24)), 2), (4 + r * 52, 12))
    for r, d in enumerate(DIRS):
        ce.alpha_composite(csheets["idle"][d][0], (12 + r * 52, 12 + 56))
    big_ = upscale(ce, 4)
    label(big_, "기존 charger_idle 24×24 (2배 확대)", (6, 4))
    label(big_, "v2 charger_idle 32×48 (1배)", (6, 4 + 60 * 4))
    big_.save(os.path.join(HERE, "preview_compare_charger.png"))

    # 목업 2배 확대 부분(주인공 주변)
    lit.crop((300, 150, 780, 420)).resize((960, 540), Image.NEAREST).save(os.path.join(HERE, "preview_mock_lit_zoom2x.png"))
    print("stats:")
    for k, v in STATS.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    build()
