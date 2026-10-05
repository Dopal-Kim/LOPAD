"""60라운드 Q9 B안 — 1층 5지역 타일셋을 64도트 = 1칸(pixelScale 0.5)으로 교체.

python3 parts/art/work/floor1q60/floors64_build.py [waste gate outer brewery hall] [--assets]
- 입력(원본): before/tiles/stage1_<지역>.png/.json (60라운드 직전 v2 32도트 사본 — assets 를 덮어써도 다시 돌릴 수 있게).
- 새로 그린 칸(regions64.NEW_IDX): 0~4 바닥·복도 · 23~38 방 종류 바닥 · 43~46 엄폐 담 · 60~62 바닥 특징.
- 나머지 칸(문 8~12 · 장애물 벽 5·6·21·22·40~42·47~52·63 · 그늘 53~57 · void 7·58·59 · 수로 64~71 · 데칼·큰 소품 rect)은
  32 그림을 2배 최근접으로 키워 같은 자리에 둔다(P3 에서 다시 그림 — JSON upscaled60 에 목록).
- JSON: 인덱스 표·키는 그대로. tileWidth/Height 64, pixelScale 0.5, 도트 단위 길이(rect·pivot·occludeAbove·light radius·offset)는 2배.
- --assets 면 assets/tiles/v2/stage1_<지역>.png/.json 을 덮어쓴다(경로 유지 — 시스템은 pixelScale 로 64도트 칸을 처리, 계약 §11).
산출(이 폴더 out/): tiles64_<지역>.png/.json, preview_tiles64_<지역>.png(번호판), preview_floor64_<지역>.png(무작위 이어붙임)
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fk64  # noqa: E402
import regions64 as R  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))
SRC = os.path.join(HERE, "before", "tiles")
DST = os.path.join(ROOT, "assets", "tiles", "v2")
OUT = os.path.join(HERE, "out")
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
LEN_KEYS = ("occludeAbove", "radius")


def scale_json(node):
    """도트 단위 길이 2배(rect·pivot·offset·occludeAbove·radius). flicker·intensity·footprint·index 는 그대로."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k in ("rect", "pivot") and isinstance(v, dict):
                out[k] = {kk: (vv * 2 if isinstance(vv, (int, float)) else vv) for kk, vv in v.items()}
            elif k == "offset":
                if isinstance(v, dict):
                    out[k] = {kk: (vv * 2 if isinstance(vv, (int, float)) else vv) for kk, vv in v.items()}
                elif isinstance(v, list):
                    out[k] = [vv * 2 for vv in v]
                else:
                    out[k] = v
            elif k in LEN_KEYS and isinstance(v, (int, float)) and not isinstance(v, bool):
                out[k] = v * 2
            else:
                out[k] = scale_json(v)
        return out
    if isinstance(node, list):
        return [scale_json(v) for v in node]
    return node


def build(rid, to_assets):
    src = Image.open(os.path.join(SRC, f"stage1_{rid}.png")).convert("RGBA")
    meta = json.load(open(os.path.join(SRC, f"stage1_{rid}.json"), encoding="utf-8"))
    cols = meta["columns"]
    assert meta["tileWidth"] == 32 and meta.get("pixelScale", 1) == 1, (rid, "원본이 32 판이 아님")
    sheet = fk64.upscale2(src)
    tiles = R.REGIONS[rid]()
    for i in R.NEW_IDX:
        assert i in tiles, (rid, i)
        t = tiles[i]
        assert t.size == (64, 64), (rid, i, t.size)
        for c in t.get_flattened_data():
            assert c[3] in (0, 255), (rid, i, "반투명")
        x, y = (i % cols) * 64, (i // cols) * 64
        sheet.paste((0, 0, 0, 0), (x, y, x + 64, y + 64))
        sheet.alpha_composite(t, (x, y))
    j = scale_json(copy.deepcopy(meta))
    j["tileWidth"] = j["tileHeight"] = 64
    j["pixelScale"] = 0.5
    j["version"] = "60라운드 Q9 B안 — 64도트 = 1칸(pixelScale 0.5). 이전: " + meta.get("version", "v2")
    j["source"] = "parts/art/work/floor1q60/floors64_build.py (60라운드 Q9·Q10 — 지역 재질 64도트). 이전: " + meta.get("source", "")
    j["pixelScaleNote"] = ("60라운드 Q9 B안: 칸 = 64도트 = 논리 32px. rect·pivot·occludeAbove·light.radius·light.offset 은 도트 단위(이전 32 판의 2배). "
                           "인덱스 표·키는 그대로(계약 §9·§11·§12)")
    j["redrawn60"] = R.NEW_IDX
    j["upscaled60"] = sorted(set(range(cols * meta["rows"])) - set(R.NEW_IDX))
    j["upscaledNote"] = "upscaled60 칸은 32 그림을 2배로 키운 임시(문·장애물 벽·그늘·void·수로·데칼 등) — P3 에서 64 설계로 다시 그림"
    os.makedirs(OUT, exist_ok=True)
    sheet.save(os.path.join(OUT, f"tiles64_{rid}.png"))
    json.dump(dict(j, image=f"tiles64_{rid}.png"), open(os.path.join(OUT, f"tiles64_{rid}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if to_assets:
        sheet.save(os.path.join(DST, f"stage1_{rid}.png"))
        with open(os.path.join(DST, f"stage1_{rid}.json"), "w", encoding="utf-8") as f:
            json.dump(j, f, ensure_ascii=False, indent=1)
    old_cell = lambda i: src.crop(((i % cols) * 32, (i // cols) * 32, (i % cols) * 32 + 32, (i // cols) * 32 + 32))
    lo = fk64.luma([old_cell(i) for i in range(4)])
    ln = fk64.luma([tiles[i] for i in range(4)])
    cs = set()
    for i in R.NEW_IDX:
        cs |= {c[:3] for c in tiles[i].get_flattened_data() if c[3]}
    print(f"{rid}: 바닥 루마 현행 {lo:.1f} → 새 {ln:.1f} (차 {ln - lo:+.1f}) · 새 칸 색 {len(cs)} · 시트 {sheet.size}")
    previews(rid, sheet, meta, tiles, src)
    return lo, ln, len(cs)


def previews(rid, sheet, meta, tiles, src):
    cols = meta["columns"]
    f = ImageFont.truetype(FONT, 14)
    # 번호판(1배 64칸) — 새 칸은 노란 테, 키운 칸은 회색 테
    k = 2
    W, H = sheet.width * k, sheet.height * k
    im = Image.new("RGBA", (W, H), (255, 0, 255, 255))
    im.alpha_composite(sheet.resize((W, H), Image.NEAREST))
    d = ImageDraw.Draw(im)
    for i in range(cols * meta["rows"]):
        x, y = (i % cols) * 64 * k, (i // cols) * 64 * k
        new = i in R.NEW_IDX
        d.rectangle((x, y, x + 64 * k - 1, y + 64 * k - 1), outline=(232, 184, 88) if new else (90, 90, 90), width=2 if new else 1)
        d.text((x + 4, y + 2), str(i), fill=(255, 255, 0) if new else (180, 180, 180), font=f)
    im.convert("RGB").save(os.path.join(OUT, f"preview_tiles64_{rid}.png"))
    # 무작위 이어붙임: 현행(32 → 2배) | 새(64) — 10×6칸 2배
    fl_w = meta["tiles"]["1"]
    rf = meta["roomFloors"]
    ocell = lambda i: src.crop(((i % cols) * 32, (i // cols) * 32, (i % cols) * 32 + 32, (i // cols) * 32 + 32)).resize((64, 64), Image.NEAREST)
    nw, nh, kk = 10, 6, 2
    out = Image.new("RGB", ((nw * 64 * kk) * 2 + 24, nh * 64 * kk + 40), (12, 12, 16))
    dd = ImageDraw.Draw(out)
    for side, getter in enumerate((ocell, lambda i: tiles[i])):
        x0 = side * (nw * 64 * kk + 24)
        for ty in range(nh):
            for tx in range(nw):
                i = fl_w[fk64.h(tx, ty, 3) % len(fl_w)]
                if (tx, ty) in ((3, 1), (7, 4)):
                    i = rf["trial"][(tx + ty) % 4]
                elif (tx, ty) in ((8, 1),):
                    i = rf["start"][1]
                elif ty == 3 and tx < 4:
                    i = 4
                out.paste(getter(i).resize((64 * kk, 64 * kk), Image.NEAREST).convert("RGB"), (x0 + tx * 64 * kk, 40 + ty * 64 * kk))
        dd.text((x0 + 6, 8), ("현행 32도트(2배 표시)" if side == 0 else "60라운드 B안 64도트") + f" — {rid} 바닥 0~3 무작위 + 복도 4 + trial·start",
                fill=(235, 225, 200), font=ImageFont.truetype(FONT, 22))
    out.save(os.path.join(OUT, f"preview_floor64_{rid}.png"))


def board_all():
    """5지역 전/후 타일판(2배): 바닥 0~3 · 복도 4 · trial 27 · boss 35 · 담 43·44·45·46 · 특징 60~62 — 현행(32 → 2배) / 64."""
    idx = [0, 1, 2, 3, 4, 27, 35, 43, 44, 45, 46, 60, 61, 62]
    k = 2
    cs = 64 * k
    f = ImageFont.truetype(FONT, 18)
    W = 120 + len(idx) * (cs + 4)
    H = 40 + len(R.REGIONS) * 2 * (cs + 6) + len(R.REGIONS) * 10
    out = Image.new("RGB", (W, H), (14, 14, 18))
    d = ImageDraw.Draw(out)
    d.text((8, 8), "1층 5지역 타일 전/후 — 위 = 현행 32도트(2배 표시), 아래 = 60라운드 64도트 · 2배 확대", fill=(235, 225, 200), font=f)
    y = 40
    for rid in R.REGIONS:
        src = Image.open(os.path.join(SRC, f"stage1_{rid}.png")).convert("RGBA")
        new = Image.open(os.path.join(OUT, f"tiles64_{rid}.png")).convert("RGBA")
        for row, (sheet, ts) in enumerate(((src, 32), (new, 64))):
            d.text((8, y + cs // 2 - 10), f"{rid}\n{'현행' if row == 0 else '64'}", fill=(232, 184, 88) if row else (200, 190, 170), font=f)
            for c, i in enumerate(idx):
                t = sheet.crop(((i % 8) * ts, (i // 8) * ts, (i % 8) * ts + ts, (i // 8) * ts + ts)).resize((cs, cs), Image.NEAREST)
                bg = Image.new("RGBA", (cs, cs), (60, 40, 60, 255))
                bg.alpha_composite(t)
                out.paste(bg.convert("RGB"), (120 + c * (cs + 4), y))
                if rid == "waste" and row == 0:
                    d.text((120 + c * (cs + 4) + 2, 22), str(i), fill=(180, 180, 180), font=f)
            y += cs + 6
        y += 10
    out.save(os.path.join(HERE, "preview_tiles_regions_before_after.png"))
    print("board", out.size)


if __name__ == "__main__":
    regs = [a for a in sys.argv[1:] if not a.startswith("--")] or list(R.REGIONS)
    rep = {}
    for r in regs:
        rep[r] = build(r, "--assets" in sys.argv)
    json.dump(rep, open(os.path.join(OUT, "tiles64_stats.json"), "w"), indent=1)
    if len(regs) == len(R.REGIONS):
        board_all()
