"""61라운드 P3 — 1층 5지역 타일셋의 임시 2배 칸(upscaled60)을 64도트 설계로 교체.

python3 parts/art/work/struct61/tiles61_build.py [waste gate outer brewery hall] [--assets]
- 입력: before61/stage1_<지역>.png/.json (처음 실행 때 현재 assets/tiles/v2 를 복사해 둔 사본 — 다시 돌려도 같은 결과).
- 다시 그리는 칸: 문 8~12(공용) · 장애물 벽 5·6·21·22·40~42·47~52·63 · 그늘 53~57(공용, 반투명) · 공허 7·58·59 · 지역 데칼·수로.
- 그대로 두는 칸: 60라운드 redrawn60(바닥·엄폐 담) · 외곽 13~20·64~79(옛 v2 소품 — v3 소품 시트가 대신함, JSON supersededByPropsSheet).
- JSON: 인덱스·키·tileLights·decals rect 그대로. `redrawn61` 추가, `upscaled60` 은 남은 칸만(빈 칸 제외).
- --assets 면 assets/tiles/v2/stage1_<지역>.png/.json 을 덮어쓴다(경로·형식 유지 — 격자 타일셋, 계약 §19.1).
산출(out/): tiles61_<지역>.png, mock61_<지역>.png(전후 목업), board61_<지역>.png(새 칸 번호판)
"""
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import s61  # noqa: E402
import tk61  # noqa: E402
import walls61  # noqa: E402
import tilemock  # noqa: E402

N = 64
DST = os.path.join(s61.TILES, "v2")
BEFORE = os.path.join(HERE, "before61")
OUT = os.path.join(HERE, "out")
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
WALLS = {"waste": walls61.waste_walls, "gate": walls61.gate_walls, "outer": walls61.outer_walls,
         "brewery": walls61.brewery_walls, "hall": walls61.hall_walls}
SHADOW_IDX = (53, 54, 55, 56, 57)


def ensure_before(rid):
    os.makedirs(BEFORE, exist_ok=True)
    for ext in ("png", "json"):
        p = os.path.join(BEFORE, f"stage1_{rid}.{ext}")
        if not os.path.exists(p):
            shutil.copy(os.path.join(DST, f"stage1_{rid}.{ext}"), p)


def cells_for(rid):
    new = {}
    new.update(WALLS[rid]())
    new.update(walls61.voids(rid))
    new.update(tk61.door_tiles())
    new.update(tk61.shadows())
    return new


def build(rid, to_assets):
    ensure_before(rid)
    src = Image.open(os.path.join(BEFORE, f"stage1_{rid}.png")).convert("RGBA")
    meta = json.load(open(os.path.join(BEFORE, f"stage1_{rid}.json"), encoding="utf-8"))
    assert meta["tileWidth"] == 64 and meta.get("pixelScale") == 0.5, rid
    cols = meta["columns"]
    sheet = src.copy()
    new = cells_for(rid)
    redrawn = []
    for i, im in sorted(new.items()):
        assert im.size == (N, N), (rid, i, im.size)
        if i not in SHADOW_IDX:
            for c in im.get_flattened_data():
                assert c[3] in (0, 255), (rid, i, "반투명")
        x, y = (i % cols) * N, (i // cols) * N
        sheet.paste((0, 0, 0, 0), (x, y, x + N, y + N))
        sheet.alpha_composite(im, (x, y))
        redrawn.append(i)
    for (x, y), im in walls61.region_decals(rid).items():
        for c in im.get_flattened_data():
            assert c[3] in (0, 255), (rid, x, y, "데칼 반투명")
        sheet.paste((0, 0, 0, 0), (x, y, x + im.width, y + im.height))
        sheet.alpha_composite(im, (x, y))
        for cy in range(y // N, (y + im.height) // N):
            for cx in range(x // N, (x + im.width) // N):
                redrawn.append(cy * cols + cx)
    redrawn = sorted(set(redrawn))

    def empty(i):
        x, y = (i % cols) * N, (i // cols) * N
        return sheet.crop((x, y, x + N, y + N)).getbbox() is None
    superseded = list(range(13, 21)) + list(range(64, 80)) if rid == "outer" else []
    remain = [i for i in meta.get("upscaled60", []) if i not in redrawn and i not in superseded and not empty(i)]
    j = dict(meta)
    j["redrawn61"] = redrawn
    j["upscaled60"] = remain
    j["upscaledNote"] = ("61라운드 P3: 임시 2배 칸을 64도트 설계로 다시 그림(redrawn61). upscaled60 = 아직 32 그림 2배인 칸"
                         + (" — 없음" if not remain else "") + ". 빈 칸(예약)은 목록에서 뺐다")
    if superseded:
        j["supersededByPropsSheet"] = superseded
        j["supersededNote"] = ("외곽 13~20(옛 인덱스 소품)·64~79(옛 bigProps rect)는 v3 소품 시트 tiles/v3/stage1_outer_props 가 대신한다"
                               "(계약 §14 — v3 가 있으면 v3). 그림은 60라운드 2배 임시 그대로 둔다(로드 경로 호환용)")
    j["source"] = ("parts/art/work/struct61/tiles61_build.py (61라운드 P3 — 벽·문·그늘·공허·데칼 64도트). 이전: " + meta.get("source", ""))
    j["version"] = "61라운드 P3 — 임시 2배 칸 64도트 재작업. 이전: " + meta.get("version", "")
    os.makedirs(OUT, exist_ok=True)
    sheet.save(os.path.join(OUT, f"tiles61_{rid}.png"))
    if to_assets:
        sheet.save(os.path.join(DST, f"stage1_{rid}.png"))
        with open(os.path.join(DST, f"stage1_{rid}.json"), "w", encoding="utf-8") as f:
            json.dump(j, f, ensure_ascii=False, indent=1)
    # 미리보기: 전/후 목업(위·아래), 새 칸 번호판
    tilemock.mock(rid, {}, os.path.join(OUT, f"_mock_before_{rid}.png"), k=1, base=src)
    tilemock.mock(rid, {}, os.path.join(OUT, f"_mock_after_{rid}.png"), k=1, base=sheet)
    a = Image.open(os.path.join(OUT, f"_mock_before_{rid}.png")); b = Image.open(os.path.join(OUT, f"_mock_after_{rid}.png"))
    m = Image.new("RGB", (a.width, a.height * 2 + 60), (14, 14, 18))
    m.paste(a, (0, 30)); m.paste(b, (0, a.height + 60))
    d = ImageDraw.Draw(m)
    f = ImageFont.truetype(FONT, 20)
    d.text((8, 4), f"{rid} — 위: 60라운드(벽·문 2배 임시) / 아래: 61라운드 P3 64도트 · 1배", fill=(235, 225, 200), font=f)
    d.text((8, a.height + 34), "61라운드", fill=(232, 184, 88), font=f)
    m = m.resize((m.width * 2, m.height * 2), Image.NEAREST)
    m.save(os.path.join(OUT, f"mock61_{rid}.png"))
    for p in (f"_mock_before_{rid}.png", f"_mock_after_{rid}.png"):
        os.remove(os.path.join(OUT, p))
    bg = Image.new("RGBA", sheet.size, (110, 0, 110, 255)); bg.alpha_composite(sheet)
    d = ImageDraw.Draw(bg)
    for i in range(cols * meta["rows"]):
        x, y = (i % cols) * N, (i // cols) * N
        d.rectangle((x, y, x + N - 1, y + N - 1), outline=(232, 184, 88) if i in redrawn else (70, 70, 70))
        d.text((x + 2, y + 1), str(i), fill=(255, 255, 0) if i in redrawn else (170, 170, 170))
    bg.resize((bg.width * 2, bg.height * 2), Image.NEAREST).convert("RGB").save(os.path.join(OUT, f"board61_{rid}.png"))
    print(f"{rid}: 새로 그린 칸 {len(redrawn)} · 남은 임시 {remain} · 색 {len(s61.colors(sheet))}")
    return redrawn, remain


if __name__ == "__main__":
    regs = [a for a in sys.argv[1:] if not a.startswith("--")] or list(WALLS)
    rep = {r: build(r, "--assets" in sys.argv) for r in regs}
    json.dump(rep, open(os.path.join(OUT, "tiles61_stats.json"), "w"), indent=1)
