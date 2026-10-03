#!/usr/bin/env python3
"""4지역 쿼터뷰 바닥 타일셋 (53라운드) — 황무지·성문·양조·연회장, 외곽 v2 와 같은 규칙(32px, pixelScale 1, roomFloorMix).

python3 parts/art/work/floors_v2/build.py
산출: assets/tiles/v2/stage1_<region>.png/.json, parts/art/work/floors_v2/preview_tiles_<region>.png(인덱스 번호 2배),
      preview_floor_<region>.png(무작위 바닥 12×8칸 2배 — 격자·이음 점검)
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fk  # noqa: E402
import regions  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
OUT = os.path.join(ROOT, "assets/tiles/v2")
T, COLS = 32, 8
ROOM_FLOOR_MIX = 0.02          # 외곽 v2 와 같음(계약 §12)
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
NAMES_STD = {0: "floor_0", 1: "floor_1", 2: "floor_2", 3: "floor_3", 4: "corridor", 5: "wall_front_lower",
             6: "wall_top", 7: "void", 8: "door_open", 9: "door_closed", 10: "door_locked", 11: "exit", 12: "shop",
             21: "wall_front_lower_lit", 22: "wall_front_lower_b", 40: "wall_front_upper", 41: "wall_front_upper_b",
             42: "wall_front_upper_c", 43: "cover_lower", 44: "cover_upper", 45: "cover_top", 46: "cover_lower_b",
             47: "wall_top_eave", 48: "wall_top_edge_e", 49: "wall_top_edge_w", 50: "wall_top_edge_n",
             51: "wall_top_corner_ne", 52: "wall_top_corner_nw", 53: "floor_shadow_n", 54: "floor_shadow_w",
             55: "floor_shadow_e", 56: "floor_shadow_nw", 57: "floor_shadow_ne", 58: "void_b", 59: "void_c",
             60: "floor_feature_a", 61: "floor_feature_b", 62: "floor_feature_c", 63: "wall_front_lower_c"}
for k, nm in enumerate(("start", "trial", "rest", "boss")):
    for j in range(4):
        NAMES_STD[23 + k * 4 + j] = f"{nm}_{j}"
CANAL_NAMES = {64: "canal_0", 65: "canal_1", 66: "canal_2", 67: "bridge_l", 68: "bridge_r",
               69: "canal_lit_0", 70: "canal_lit_1", 71: "canal_lit_2"}


def assemble(R):
    n_idx = max(R.cells) + 1
    rows = -(-n_idx // COLS)
    # 데칼 선반 배치(32 격자, 시트 폭 256)
    place, x, y, sh = [], 0, rows * T, 0
    for (name, can, meta) in sorted(R.decals, key=lambda d: -d[1].h):
        if x + can.w > COLS * T:
            x, y, sh = 0, y + sh, 0
        place.append((name, can, meta, x, y))
        x += can.w
        sh = max(sh, can.h)
    H = y + sh
    sheet = Image.new("RGBA", (COLS * T, H), (0, 0, 0, 0))
    for i, c in R.cells.items():
        sheet.alpha_composite(c.im, ((i % COLS) * T, (i // COLS) * T))
    decals = []
    for (name, can, meta, dx, dy) in place:
        sheet.alpha_composite(can.im, (dx, dy))
        e = {"name": name, "rect": {"x": dx, "y": dy, "w": can.w, "h": can.h},
             "index": (dy // T) * COLS + dx // T}
        e.update(meta)
        decals.append(e)
    return sheet, decals


def write_json(R, sheet, decals):
    rid = R.rid
    names = {}
    for i in sorted(R.cells):
        names[str(i)] = (CANAL_NAMES.get(i) if rid == "brewery" else None) or NAMES_STD.get(i, f"t{i}")
    for i in range(13, 21):
        names[str(i)] = "reserved_prop(v3 시트 사용)"
    m = R.meta
    data = {
        "image": f"stage1_{rid}.png",
        "version": "v2 (53라운드 — 4지역 쿼터뷰 바닥, 외곽 v2 규칙)",
        "stage": 1, "region": rid, "name": m["name"],
        "tileWidth": T, "tileHeight": T, "columns": COLS, "rows": sheet.height // T,
        "indexFormula": "row * columns + column",
        "pixelScale": 1, "wallHeightTiles": 2, "quarter": True,
        "tiles": m["tiles"],
        "tilesNote": "목록 안 중복 = 가중치. 바닥 0~3 은 공유 주기 잡음으로 가장자리가 같아 어떤 변형끼리 붙어도 이어진다",
        "tileIdNames": {"0": "void", "1": "floor", "2": "wall", "3": "door_open", "4": "door_closed", "5": "door_locked",
                        "6": "corridor", "7": "exit", "8": "shop"},
        "walls": m["walls"],
        "wallsNote": ("벽은 최소(53라운드): 외벽은 Gemini 테두리 assets/tiles/border/" + rid +
                      "/border.json 이 덮는다. 이 타일은 전투장 안 장애물 벽(앞면 2칸 + 윗면)과 엄폐 담(stoneSet) 전용. "
                      "쌓는 규칙은 외곽 v2(walls.stacking)와 같다"),
        "floorShadows": {"n": 53, "w": 54, "e": 55, "nw": 56, "ne": 57},
        "floorFeatures": m["floorFeatures"],
        "roomFloors": {"start": [23, 24, 25, 26], "trial": [27, 28, 29, 30], "rest": [31, 32, 33, 34], "boss": [35, 36, 37, 38]},
        "roomFloorMix": ROOM_FLOOR_MIX,
        "roomFloorsNote": m["roomFloorsNote"],
        "props": [],
        "propsSheet": f"../v3/stage1_{rid}_props.json",
        "propsNote": "13~20 은 비움 — 소품은 v3 시트(2배 밀도, pixelScale 0.5)의 props·bigProps 를 쓴다(계약 문구 초안 참고)",
        "decals": decals,
        "decalsNote": "바닥 데칼(선택): rect 로 잘라 바닥 위·소품 아래에 반투명 겹침. footprint = 칸 수. 통과 가능",
        "tileLights": m["tileLights"],
        "emissiveColors": [fk.tohex(c) for c in fk.EMISSIVE],
        "border": f"../border/{rid}/border.json",
        "names": names,
        "palette": ("parts/art/palette/lopad.json (gray + 1층 램프 16~27, 런타임 스왑) + v2 재질 블록 SL·WD·PL·NT "
                    "(parts/art/work/v2_outer/palette_v2_proposal.json, 임시·고정색) — 새 색 없음"),
        "source": "parts/art/work/floors_v2/build.py (53라운드)",
    }
    if "canal" in m:
        data["canal"] = m["canal"]
    with open(os.path.join(OUT, f"stage1_{rid}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def preview_tiles(R, sheet):
    k = 3
    im = Image.new("RGBA", sheet.size, (60, 20, 60, 255))
    im.alpha_composite(sheet)
    im = im.resize((sheet.width * k, sheet.height * k), Image.NEAREST)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 14)
    for i in R.cells:
        x, y = (i % COLS) * T * k, (i // COLS) * T * k
        d.rectangle((x, y, x + T * k - 1, y + T * k - 1), outline=(0, 0, 0))
        d.text((x + 3, y + 2), str(i), fill=(255, 240, 120), font=f, stroke_width=2, stroke_fill=(0, 0, 0))
    im.convert("RGB").save(os.path.join(HERE, f"preview_tiles_{R.rid}.png"))


def preview_floor(R):
    """바닥 12×8칸 무작위(타일 해시) + roomFloor 섞기 + 안쪽 장애물 벽 + 엄폐 담 — 2배."""
    W, H = 14, 9
    can = Image.new("RGBA", (W * T, H * T), (0, 0, 0, 255))
    fl = R.meta["tiles"]["1"]
    rf = [23, 27, 31, 35]

    def h2(x, y, n):
        v = (x * 73856093) ^ (y * 19349663) ^ 0x5bd1e995
        return (((v * 2654435761) & 0xFFFFFFFF) >> 13) % n
    for ty in range(H):
        for tx in range(W):
            i = fl[h2(tx, ty, len(fl))]
            if h2(tx + 5, ty + 9, 100) < 6:
                i = rf[h2(tx, ty + 3, 4)] + h2(tx + 1, ty, 4)
            can.alpha_composite(R.cells[i].im, (tx * T, ty * T))
    # 장애물 벽(2칸 앞면 + 윗면 2줄) 가로 4칸 @ (2,1)
    wall = R.meta["walls"]
    for tx in range(2, 6):
        can.alpha_composite(R.cells[wall["top"]].im, (tx * T, 1 * T))
        can.alpha_composite(R.cells[wall["topAboveFront"]].im, (tx * T, 2 * T))
        up = wall["front"]["upper"][tx % len(wall["front"]["upper"])]
        lo = wall["front"]["lower"][tx % len(wall["front"]["lower"])]
        can.alpha_composite(R.cells[up].im, (tx * T, 3 * T))
        can.alpha_composite(R.cells[lo].im, (tx * T, 4 * T))
        can.alpha_composite(R.cells[53].im, (tx * T, 5 * T))
    # 엄폐 담 3칸 @ (9,5)
    ss = wall["stoneSet"]
    for tx in range(9, 12):
        can.alpha_composite(R.cells[ss["top"]].im, (tx * T, 4 * T))
        can.alpha_composite(R.cells[ss["upper"][0]].im, (tx * T, 5 * T))
        can.alpha_composite(R.cells[ss["lower"][tx % len(ss["lower"])]].im, (tx * T, 6 * T))
    if R.rid == "brewery":                     # 수로 한 줄 + 다리
        for tx in range(W):
            i = 64 if tx not in (6, 7) else (67 if tx == 6 else 68)
            if tx in (4, 5, 8, 9):
                i = 69
            can.alpha_composite(R.cells[i].im, (tx * T, 7 * T))
    can = can.resize((can.width * 2, can.height * 2), Image.NEAREST)
    can.convert("RGB").save(os.path.join(HERE, f"preview_floor_{R.rid}.png"))


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    for rid, fn in regions.ALL.items():
        if only and rid not in only:
            continue
        R = fn()
        sheet, decals = assemble(R)
        sheet.save(os.path.join(OUT, f"stage1_{rid}.png"))
        write_json(R, sheet, decals)
        preview_tiles(R, sheet)
        preview_floor(R)
        print(rid, sheet.size, len(R.cells), "tiles", len(decals), "decals")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
