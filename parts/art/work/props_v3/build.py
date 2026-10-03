#!/usr/bin/env python3
"""바닥 소품 v3 (53라운드 Q12) — 2배 밀도(pixelScale 0.5) 소품 시트 5지역.

python3 parts/art/work/props_v3/build.py
산출: assets/tiles/v3/stage1_<region>_props.png/.json (region = outer·waste·gate·brewery·hall)
      parts/art/work/props_v3/preview_<region>.png (2배, 이름·피벗·발자국 표시), preview_compare_outer.png, stats.json
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pk  # noqa: E402
import outer, waste, gate, brewery, hall  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
OUT = os.path.join(ROOT, "assets/tiles/v3")
SHEET_W = 1024
CELL = 64
RID = None
REGIONS = {"outer": outer, "waste": waste, "gate": gate, "brewery": brewery, "hall": hall}
NAMES = {"outer": "외곽 거리", "waste": "황무지", "gate": "성문", "brewery": "양조 구역", "hall": "연회장"}
SRC = "parts/art/work/props_v3/build.py (53라운드 Q12)"
# 53라운드 Q51~Q54 세부안: 테두리 그림에 이미 같은 물건이 있는 큰 소품 → 그 쪽 테두리 앞에 두지 않음(중복 방지).
# 근거: gemini/NOTES_borders_f1.md 3절(띠별 내용) · 목업 확인.
AVOID = {
    "outer": {"stall": ["north"], "crate_stack": ["north"]},
    "waste": {"stakes": ["north"], "broken_cart": ["north", "east"], "weapons_stuck": ["north"]},
    "gate": {"toll_booth": ["north", "east"], "barricade_x": ["north", "east"], "barrel_cart": ["east"],
             "crate_stack": ["north"]},
    "brewery": {"barrel_pyramid": ["north", "west"], "crane_barrel": ["north", "west"], "steel_vat": ["west"],
                "handcart": ["north"], "crate_stack": ["north"]},
    "hall": {"candelabra_stand": ["north"], "pillar": ["north"]},
}
AVOID_TILES = 3
PAL = ("parts/art/palette/lopad.json (gray + 1층 램프 16~27, 런타임 스왑) + v2 재질 블록 SL·WD·PL "
       "(parts/art/work/v2_outer/palette_v2_proposal.json, 임시·고정색) — 새 색 없음")
HERO = os.path.join(ROOT, "assets/sprites/player/v3/player_idle")


def font(sz=14):
    for f in ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
              "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def pack(small, big):
    """소품 = 128×128 칸(가로 8개), 큰 소품 = 64 격자 정렬 선반 배치."""
    placed = []
    x = y = 0
    for p in small:
        if x + 128 > SHEET_W:
            x, y = 0, y + 128
        placed.append((p, x, y))
        x += 128
    y += 128 if small else 0
    x, shelf_h = 0, 0
    for p in sorted(big, key=lambda q: -q.im.height):
        w = -(-p.im.width // CELL) * CELL
        h = -(-p.im.height // CELL) * CELL
        if x + w > SHEET_W:
            x, y, shelf_h = 0, y + shelf_h, 0
        placed.append((p, x, y))
        x += w
        shelf_h = max(shelf_h, h)
    H = y + shelf_h
    H = -(-H // CELL) * CELL
    sheet = Image.new("RGBA", (SHEET_W, H), (0, 0, 0, 0))
    for (p, px_, py_) in placed:
        sheet.alpha_composite(p.im, (px_, py_))
    return sheet, placed


def entry(p, x, y, big):
    e = {"name": p.name, "index": (y // CELL) * (SHEET_W // CELL) + x // CELL,
         "rect": {"x": x, "y": y, "w": p.im.width, "h": p.im.height},
         "pivot": {"x": p.pivot[0], "y": p.pivot[1]},
         "footprint": list(p.footprint), "solid": p.solid}
    if p.occlude is not None:
        e["occludeAbove"] = p.occlude
    ex = dict(p.extra)
    for k in ("slot", "maxPerRoom", "weight", "depth", "placement", "note"):
        if k in ex:
            e[k] = ex.pop(k)
    av = AVOID.get(RID, {}).get(p.name) if big else None
    if av:
        e["avoidNearBorder"] = av
    if p.light:
        e["light"] = p.light
    if "lights" in ex:
        e["lights"] = ex.pop("lights")
    return e


def build_region(rid, mod):
    global RID
    RID = rid
    small, big = mod.small(), mod.big()
    sheet, placed = pack(small, big)
    os.makedirs(OUT, exist_ok=True)
    sheet.save(os.path.join(OUT, f"stage1_{rid}_props.png"))
    props = [entry(p, x, y, False) for (p, x, y) in placed if p in small]
    bigs = [entry(p, x, y, True) for (p, x, y) in placed if p not in small]
    data = {
        "image": f"stage1_{rid}_props.png",
        "version": "v3 (53라운드 Q12 — 바닥 소품 2배 밀도)",
        "stage": 1, "region": rid, "name": f"잔(盞) — {NAMES[rid]} 바닥 소품 v3",
        "pixelScale": 0.5,
        "units": "모든 길이·좌표(rect·pivot·occludeAbove·light.radius·light.offset)는 시트 도트. 논리 px = 도트 × pixelScale(0.5). 1920 렌더에서 1:1",
        "cell": CELL, "columns": SHEET_W // CELL, "indexFormula": "row * columns + column (64 도트 격자, rect 왼쪽 위 칸)",
        "propCell": {"w": 128, "h": 128},
        "anchorRule": ("props: pivot 을 놓일 칸의 논리 (16, 30) 자리에 둔다(v2 와 같은 자리). "
                       "bigProps: pivot 을 발자국(footprint 가로×세로 칸) 맨 아래 줄의 가로 가운데, 바닥 위 2 논리 px 에 둔다. "
                       "Y 정렬 기준 = pivot.y, 피벗 위 occludeAbove 도트부터 캐릭터를 가림(§9). light.offset = rect 왼쪽 위 기준 도트"),
        "props": props,
        "propsNote": ("인덱스 소품(무작위 배치, 계약 §2 의 13~20 자리). 128×128 칸, 배경 투명. slot = v2 타일셋의 같은 뜻 인덱스(외곽만). "
                      "depth 'floor' = 바닥 데칼(통과·Y 정렬 없음)."),
        "bigProps": bigs,
        "bigPropsNote": "계약 §12 bigProps 규칙 배치용. rect 로 자른다. lights[] 가 있으면 light 대신 여러 광원(연회 탁자 촛대).",
        "avoidNearBorderNote": (f"avoidNearBorder = 테두리 그림에 같은 물건이 이미 있는 쪽(north·south·west·east). 그 쪽 바닥 끝(테두리 기준선)에서 "
                                f"{AVOID_TILES}칸 안에 발자국이 걸치지 않게 둔다(53라운드 Q51~Q54, 칸 수 임시)"),
        "emissiveColors": [pk.tohex(c) for c in pk.EMISSIVE],
        "emissiveNote": "이 색 픽셀은 자체 발광(불꽃·등불·촛불·끓는 술). 조명 곱하기 뒤 가산 레이어로 다시 그린다(목업 방식)",
        "palette": PAL, "source": SRC,
    }
    with open(os.path.join(OUT, f"stage1_{rid}_props.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return sheet, placed, small


def hero_frame():
    j = json.load(open(HERO + ".json", encoding="utf-8"))
    im = Image.open(HERO + ".png").convert("RGBA").crop((0, 0, j["frameWidth"], j["frameHeight"]))
    return im, j


def preview(rid, sheet, placed, small):
    """2배: 소품 + 피벗(빨강 점) + 발자국(파랑 상자) + 이름, 왼쪽에 주인공 v3."""
    hero, hj = hero_frame()
    items = [(p, p.im) for (p, x, y) in placed]
    pad = 16
    W = 1200
    rows, cur, cw, ch = [], [], hero.width + pad, hero.height
    for (p, im) in items:
        if cw + im.width + pad > W:
            rows.append((cur, ch)); cur, cw, ch = [], 0, 0
        cur.append((p, im)); cw += im.width + pad; ch = max(ch, im.height)
    rows.append((cur, ch))
    H = sum(h + 40 for _, h in rows) + 50
    out = Image.new("RGBA", (W, H), (44, 46, 54, 255))
    y = 40
    fx = 0
    for ri, (row, h) in enumerate(rows):
        x = 8
        if ri == 0:
            out.alpha_composite(hero, (x, y + h - hero.height)); x += hero.width + pad
        for (p, im) in row:
            by = y + h
            ox, oy = x, by - p.pivot[1] - (im.height - p.pivot[1])
            oy = by - im.height
            # 발자국(논리 32px 칸 = 64 도트)
            fw, fh = p.footprint[0] * 64, max(1, p.footprint[1]) * 64
            px_, py_ = ox + p.pivot[0], oy + p.pivot[1]
            out.alpha_composite(im, (ox, oy))
            d = ImageDraw.Draw(out)
            if p.footprint[1]:
                d.rectangle((px_ - fw // 2, py_ + 4 - fh, px_ + fw // 2, py_ + 4), outline=(90, 140, 220, 255))
            d.rectangle((px_ - 1, py_ - 1, px_ + 1, py_ + 1), fill=(230, 60, 60, 255))
            x += im.width + pad
        y += h + 40
    out = out.resize((W * 2, H * 2), Image.NEAREST)
    d = ImageDraw.Draw(out)
    d.text((16, 10), f"{NAMES[rid]} 소품 v3 — 왼쪽 주인공 v3 · 파랑 = 발자국(칸) · 빨강 = 피벗 · 2배 확대", fill=(235, 225, 200), font=font(26))
    # 이름
    y = 40
    for ri, (row, h) in enumerate(rows):
        x = 8 + (hero.width + pad if ri == 0 else 0)
        for (p, im) in row:
            d.text((x * 2, (y + h) * 2 + 12), p.name, fill=(235, 225, 200), font=font(20))
            x += im.width + pad
        y += h + 40
    out.convert("RGB").save(os.path.join(HERE, f"preview_{rid}.png"))


def compare_outer(small, big):
    """v2(32px 소품, 2배 확대) vs v3 — 같은 화면 크기(1920 렌더)."""
    v2 = Image.open(os.path.join(ROOT, "assets/tiles/v2/stage1_outer.png")).convert("RGBA")
    meta = json.load(open(os.path.join(ROOT, "assets/tiles/v2/stage1_outer.json"), encoding="utf-8"))
    hero, _ = hero_frame()
    cols = meta["columns"]
    olds = []
    for i in range(13, 21):
        olds.append(v2.crop(((i % cols) * 32, (i // cols) * 32, (i % cols) * 32 + 32, (i // cols) * 32 + 32)))
    for b in meta["bigProps"][:4]:
        r = b["rect"]
        olds.append(v2.crop((r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"])))
    olds = [o.resize((o.width * 2, o.height * 2), Image.NEAREST) for o in olds]
    news = [p.im for p in small + big[:4]]
    W = 2400
    H = 2 * 260 + 60
    out = Image.new("RGBA", (W, H), (44, 46, 54, 255))
    for row, ims in enumerate((olds, news)):
        y = 40 + row * 280 + 220
        x = 8
        out.alpha_composite(hero, (x, y - hero.height)); x += hero.width + 20
        for im in ims:
            out.alpha_composite(im, (x, y - im.height)); x += im.width + 12
    d = ImageDraw.Draw(out)
    d.text((10, 6), "위: v2 소품(32px, 2배 표시) · 아래: v3 소품(2배 밀도, 1.5배 주인공 비율) — 둘 다 1920 렌더 1:1, 왼쪽 주인공 v3", fill=(235, 225, 200), font=font(22))
    out.convert("RGB").save(os.path.join(HERE, "preview_compare_outer.png"))


def main():
    stats = {}
    for rid, mod in REGIONS.items():
        sheet, placed, small = build_region(rid, mod)
        preview(rid, sheet, placed, small)
        cols = set()
        for c in sheet.get_flattened_data():
            if c[3] == 255:
                cols.add(c[:3])
        stats[rid] = {"sheet": list(sheet.size), "props": len(small), "bigProps": len(placed) - len(small),
                      "opaqueColors": len(cols)}
        if rid == "outer":
            bn = {p.name: p for (p, x, y) in placed}
            compare_outer(small, [bn[n] for n in ("lamp_post", "crate_stack", "stall", "well")])
        print(rid, stats[rid])
    json.dump(stats, open(os.path.join(HERE, "stats.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
