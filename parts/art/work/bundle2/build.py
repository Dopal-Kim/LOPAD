"""2차 묶음 월드 아트 빌드 (57라운드 Q38 확정안 · 60라운드 Q4 '2차 묶음 아트').

    python3 parts/art/work/bundle2/build.py [--only 이름부분 ...] [--dry]

1) 격자 시트를 assets/sprites/<분류>/v3/ 에 쓰고 2) 곧바로 atlas57 변환(전 프레임 대조 → 트림 아틀라스로 교체)
3) 미리보기 parts/art/work/bundle2/preview_*.png (긴 변 8000 이하) 4) stats.json(시트별 크기·색 수).
--dry: assets 에 쓰지 않고 미리보기만.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import b2  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    b2.DRY = args.dry

    import elite
    import items
    import structs
    sys.path.insert(0, os.path.join(HERE, "../atlas57"))
    import gridsheet
    from PIL import Image

    def want(name):
        return not args.only or any(o in name for o in args.only)

    prev_elite, prev_struct, prev_items = [], [], []
    hero = gridsheet.open_grid(os.path.join(b2.SPR, "player", "v3", "player_idle.json"))
    hm = gridsheet.load_meta(os.path.join(b2.SPR, "player", "v3", "player_idle.json"))
    hero0 = hero.crop((0, 0, hm["frameWidth"], hm["frameHeight"]))
    hpiv = (hm["pivot"]["x"], hm["pivot"]["y"])

    # ---- 엘리트
    if want("elite"):
        heads = elite.head_tops()
        em = elite.emblems(heads)
        npl = elite.nameplate()
        elite.outlines()
        prev_elite += [(f, elite.EPIV) for f in em] + [(npl, None)]
        # 적 3종 합성(외곽선 + 몸 + 문장 + 이름표) — 엘리트 모습 확인용
        for i, e in enumerate(elite.ENEMIES):
            jp = os.path.join(b2.SPR, "enemies", "v3", f"{e}_idle.json")
            g, m = gridsheet.open_grid(jp), gridsheet.load_meta(jp)
            f0 = g.crop((0, 0, m["frameWidth"], m["frameHeight"]))
            o = elite.outline_frame(f0); o.alpha_composite(f0)
            cv = Image.new("RGBA", (max(m["frameWidth"], elite.NW) + 8, m["frameHeight"] + 110), (0, 0, 0, 0))
            ox = (cv.width - m["frameWidth"]) // 2
            cv.alpha_composite(o, (ox, 110))
            py = 110 + m["pivot"]["y"] - heads[e] - 10
            cv.alpha_composite(em[2 * [1, 0, 2][i]], (ox + m["pivot"]["x"] - elite.EPIV[0], py - elite.EPIV[1]))
            cv.alpha_composite(npl, (ox + m["pivot"]["x"] - elite.NW // 2, max(0, py - elite.EPIV[1] - 34)))
            prev_elite.append((cv, None))
        prev_elite.append((hero0, hpiv))

    # ---- 구조물·소품
    for fn in structs.ALL:
        if want(fn.__name__):
            fr, piv = fn()
            prev_struct += [(f, piv) for f in fr]
    if prev_struct:
        prev_struct.append((hero0, hpiv))

    # ---- 소모품
    if want("consumable"):
        fr = items.consumables()
        prev_items += [(f, items.IPIV) for f in fr] + [(hero0, hpiv)]

    # ---- 아틀라스
    rep = [] if args.dry else b2.to_atlas()
    for cat, name, src, pages in rep:
        print(f"{cat}/v3/{name}: 격자 {src[0]}x{src[1]} -> 아틀라스 " + ", ".join(f"{w}x{h}" for w, h in pages))

    # ---- 미리보기
    if prev_elite:
        print("preview_elite", b2.preview(os.path.join(HERE, "preview_elite.png"), prev_elite, k=3, max_w=1500))
    if prev_struct:
        print("preview_structures", b2.preview(os.path.join(HERE, "preview_structures.png"), prev_struct, k=2, max_w=1800))
    if prev_items:
        print("preview_items", b2.preview(os.path.join(HERE, "preview_items.png"), prev_items, k=4, max_w=700, pad=8))

    # ---- 통계
    if not args.dry:
        sp = os.path.join(HERE, "stats.json")
        stats = {}
        for cat, name in b2.WRITTEN:
            jp = os.path.join(b2.SPR, cat, "v3", name + ".json")
            m = json.load(open(jp, encoding="utf-8"))
            g = gridsheet.open_grid(jp)
            stats[f"{cat}/v3/{name}"] = {
                "frame": [m["frameWidth"], m["frameHeight"]], "frames": m["atlas"]["grid"]["frameCount"],
                "rows": m["atlas"]["grid"]["rows"], "page": [m["meta"]["size"]["w"], m["meta"]["size"]["h"]],
                "opaqueColors": len({c[:3] for c in g.getdata() if c[3] == 255}),
                "note": "반투명은 접지 그림자 1색(#0a0b10, 알파 변화)만",
            }
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(dict(sorted(stats.items())), f, ensure_ascii=False, indent=1)
            f.write("\n")


if __name__ == "__main__":
    main()
