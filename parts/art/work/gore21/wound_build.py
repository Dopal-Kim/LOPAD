"""P21 아트 B 단계 2 — 주인공 상흔 오버레이 3단 + 박힌 화살 앵커.

방식: hero20 파이프라인(자세·IK·오프셋 그대로)으로 몸 시트를 rig20.WOUND = 0·1·2·3 네 번 렌더 →
  WOUND 0 이 assets 본 시트와 픽셀까지 같은지 확인(어긋나면 중단) → 단계 k 그림과 0 의 차이 픽셀만 남긴 투명 시트
  = assets/sprites/player/v3/hero_wound{k}_<본 시트 이름>(같은 프레임 수·크기·피벗·ms). 단계는 누적(3 = 1·2·3 전부) — 한 번에 하나만 그린다.
박힌 화살 앵커: rig20.arrow_anchors(같은 렌더의 리그) → 각 오버레이 JSON arrowAnchors.

python3 parts/art/work/gore21/wound_build.py [시트…] [--no-assets] [--procs 4]
"""
import json
import math
import os
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SHEETS = ["player_idle", "player_idle_free", "player_walk", "player_walk_free", "player_run", "player_run_free", "player_dash",
          "player_hurt",
          "player_katana_rise", "player_katana_fall", "player_katana_thrust",
          "player_greatsword_sweep_cw", "player_greatsword_cleave", "player_greatsword_sweep_ccw",
          "player_dagger_combo1", "player_dagger_combo2", "player_dagger_combo3",
          "player_bow_aim", "player_bow_draw_hold", "player_bow_release"]
ARROW_ORDER = ["back", "shoulderL", "shoulderR", "thigh", "arm"]
ARROW_ANG = [-90, -120, -150, 180, 150]          # fx/v5/stuck_arrow 프레임 각(fx_blood.ARROW_ANG 와 같아야 함)
STAGE_NOTE = {1: "1단(HP ≤ 75%): 가는 균열(어두운 불씨 선) + 재 딱지 — 가슴·배·옆구리·등·위팔",
              2: "2단(HP ≤ 50%): 1단 균열이 벌어진 틈(불빛 테) + 아래로 흐르는 불씨 줄 + 아래팔 균열",
              3: "3단(HP ≤ 25%): 왼어깨 → 오른허리(등은 반대 대각) 크게 갈라진 뜨거운 틈(심 백열) + 위팔 길게 갈라짐 + 불씨 방울"}


def angdiff(a, b):
    return abs((a - b + 180) % 360 - 180)


def pick_arrow(angle):
    best = None
    for i, a in enumerate(ARROW_ANG):
        for flip, aa in ((False, a), (True, 180 - a)):
            d = angdiff(angle, aa)
            if best is None or d < best[0]:
                best = (d, i, flip)
    return best[1], best[2]


def anchors_of(R):
    import hero
    if R is None:
        return None
    out = {}
    for k in ARROW_ORDER:
        a = R.anchors["arrows"][k]
        x, y = hero.to_px(a["pt"])
        v, flip = pick_arrow(a["angle"])
        out[k] = {"x": round(x, 1), "y": round(y, 1), "frame": v, "flipX": flip, "depth": "above" if a["front"] else "below"}
    return out


def task(sheet):
    import hero_harness as hh
    from PIL import Image, ImageChops
    meta, af = hh.asset_frames(sheet)
    base, rigs = hh.render(sheet, 0)
    bad = [(d, i) for d in af for i, (a, b) in enumerate(zip(af[d], base[d]))
           if ImageChops.difference(a.convert("RGBA"), b.convert("RGBA")).getbbox()]
    if bad:
        return sheet, None, "WOUND 0 이 본 시트와 다름: %s" % bad[:5]
    stages = {}
    for k in (1, 2, 3):
        wk, _ = hh.render(sheet, k)
        rows = []
        for d in meta["directions"]:
            lst = []
            for b, w in zip(base[d], wk[d]):
                bp, wp = b.load(), w.load()
                o = Image.new("RGBA", b.size, (0, 0, 0, 0))
                op = o.load()
                for y in range(b.size[1]):
                    for x in range(b.size[0]):
                        if wp[x, y] != bp[x, y]:
                            assert wp[x, y][3] == 255, (sheet, k, d, x, y, "상흔이 몸을 지움")
                            op[x, y] = wp[x, y]
                lst.append(o.tobytes())
            rows.append(lst)
        stages[k] = rows
    anchors = {d: [anchors_of(R) for R in rigs[d]] for d in meta["directions"]}
    return sheet, dict(stages=stages, anchors=anchors, size=af[meta["directions"][0]][0].size), None


def main(argv):
    import gk
    from PIL import Image
    names = [a for a in argv if not a.startswith("-")] or SHEETS
    assets = "--no-assets" not in argv
    procs = 4
    for a in argv:
        if a.startswith("--procs="):
            procs = int(a.split("=")[1])
    with Pool(procs) as pool:
        res = pool.map(task, names, chunksize=1)
    stats = {}
    for sheet, r, err in res:
        if err:
            raise SystemExit(sheet + ": " + err)
        bm = json.load(open(os.path.join(gk.SPR, "player", "v3", sheet + ".json"), encoding="utf-8"))
        W, H = r["size"]
        for k in (1, 2, 3):
            rows = [[Image.frombytes("RGBA", (W, H), raw) for raw in lst] for lst in r["stages"][k]]
            name = "hero_wound%d_%s" % (k, sheet)
            m = {"action": "hero_wound%d" % k, "directions": bm["directions"], "frameDurationsMs": bm["frameDurationsMs"],
                 "loop": bm.get("loop", False), "pivot": bm["pivot"],
                 "overlayOf": "player/v3/" + sheet, "bodySheet": sheet, "woundStage": k,
                 "syncRule": "무기 오버레이와 같은 동기(§18.10·§19.2): 몸 시트와 같은 프레임 번호·같은 틀·같은 피벗으로 몸 바로 위에 겹쳐 그린다. 한 번에 한 단계만(3 = 1·2·3 누적 그림)",
                 "depth": "몸 바로 위 · 무기 오버레이·박힌 화살(above) 아래",
                 "note": STAGE_NOTE[k] + ". 투명 + 상흔 층만(본 몸을 지우지 않음 — 실루엣 그대로). 불빛 픽셀(호박 A21~A26)은 보정 영향이 적은 층 권장(계약 §7)",
                 "emissiveColors": [gk.A[21], gk.A[23], gk.A[25], gk.A[26]],
                 "palette": "주인공 몸 30색 안(숯 G · 호박 A17~A26) — 새 색 없음", "paletteSwap": "none",
                 "source": "parts/art/work/gore21/wound_build.py (hero20 파이프라인 + rig20.WOUND — 본 시트와 같은 자세·같은 렌더)",
                 "arrowAnchors": r["anchors"],
                 "arrowAnchorsNote": ("박힌 화살 앵커(몸 도트 좌표, 피벗 기준 = (x − %d, y − %d)): 원거리 피격마다 1대(최대 5) back → shoulderL → shoulderR → thigh → arm 순(계약 §3). "
                                      "frame = fx/v5/stuck_arrow 프레임(각), flipX, depth above = 몸·상흔 위 / below = 몸 뒤. null = 그 프레임은 몸이 무기 오버레이 안(빈 칸) — 화살 숨김") % (bm["pivot"]["x"], bm["pivot"]["y"])}
            if assets:
                gk.write_sheet("player", "v3", name, rows, m)
            n = sum(1 for row in rows for im in row for a in im.getchannel("A").getdata() if a)
            stats[name] = n
        gk.preview([[Image.frombytes("RGBA", (W, H), raw) for raw in r["stages"][3][0]]], os.path.join(HERE, "out", "preview", "w3_" + sheet + ".png"), scale=2)
        print(sheet, {k: stats["hero_wound%d_%s" % (k, sheet)] for k in (1, 2, 3)}, flush=True)
    with open(os.path.join(HERE, "out", "wound_stats.json"), "w") as f:
        json.dump(stats, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1:])
