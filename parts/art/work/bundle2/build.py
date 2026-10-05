"""2차 묶음 월드 아트 빌드 (57라운드 Q38 확정안 · 60라운드 Q4 '2차 묶음 아트').

    python3 parts/art/work/bundle2/build.py [--only 이름부분 ...] [--dry]

1) 격자 시트를 assets/sprites/<분류>/v3/ 에 쓰고 2) 곧바로 atlas57 변환(전 프레임 대조 → 트림 아틀라스로 교체)
3) 미리보기 parts/art/work/bundle2/preview_*.png (긴 변 8000 이하) 4) stats.json(시트별 크기·색 수).
--dry: assets 에 쓰지 않고 미리보기만.
"""
import argparse
import json
import math
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
    import fx2
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

    # ---- 2단계 fx (60 Q13): 접두어별 fx + 화염 술병 — 엘리트 외곽선 시트와 별개
    prev_fx2 = []
    fx2_out = fx2.build_all(want, elite.head_tops())
    for name, fr, piv in fx2_out:
        prev_fx2 += [(f, piv) for f in fr]
    if fx2_out:
        prev_fx2 += fx2_mock(fx2, elite, gridsheet, Image, {n: f for n, f, _ in fx2_out})

    # ---- 아틀라스
    rep = [] if args.dry else b2.to_atlas()
    for cat, name, src, pages in rep:
        print(f"{cat}/v3/{name}: 격자 {src[0]}x{src[1]} -> 아틀라스 " + ", ".join(f"{w}x{h}" for w, h in pages))

    # ---- 미리보기
    if prev_elite:
        print("preview_elite", b2.preview(os.path.join(HERE, "preview_elite.png"), prev_elite, k=3, max_w=1500))
    if prev_struct:
        print("preview_structures", b2.preview(os.path.join(HERE, "preview_structures.png"), prev_struct, k=2, max_w=1800))
    if prev_fx2:
        print("preview_fx2", b2.preview(os.path.join(HERE, "preview_fx2.png"), prev_fx2, k=2, max_w=1900))
    if prev_items:
        print("preview_items", b2.preview(os.path.join(HERE, "preview_items.png"), prev_items, k=4, max_w=700, pad=8))

    # ---- 통계
    if not args.dry:
        sp = os.path.join(HERE, "stats.json")
        stats = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
        stats = {k: v for k, v in stats.items() if os.path.exists(os.path.join(b2.SPR, k + ".json"))}
        for cat, name in b2.WRITTEN:
            jp = os.path.join(b2.SPR, cat, "v3", name + ".json")
            m = json.load(open(jp, encoding="utf-8"))
            g = gridsheet.open_grid(jp)
            stats[f"{cat}/v3/{name}"] = {
                "frame": [m["frameWidth"], m["frameHeight"]], "frames": m["atlas"]["grid"]["frameCount"],
                "rows": m["atlas"]["grid"]["rows"], "page": [m["meta"]["size"]["w"], m["meta"]["size"]["h"]],
                "opaqueColors": len({c[:3] for c in g.get_flattened_data() if c[3] == 255}),
                "note": "반투명은 접지 그림자 1색(#0a0b10, 알파 변화)만",
            }
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(dict(sorted(stats.items())), f, ensure_ascii=False, indent=1)
            f.write("\n")


def fx2_mock(fx2, elite, gridsheet, Image, made):
    """합성 목업: 적 위에 붙인 모습(통 갑옷·술 김·두목 연결·마시기) — 배치 규칙 확인용."""
    heads = elite.head_tops()
    boxes = fx2.body_boxes()
    out = []

    def enemy(e):
        jp = os.path.join(b2.SPR, "enemies", "v3", f"{e}_idle.json")
        g, m = gridsheet.open_grid(jp), gridsheet.load_meta(jp)
        return g.crop((0, 0, m["frameWidth"], m["frameHeight"])), (m["pivot"]["x"], m["pivot"]["y"])

    def put(cv, im, piv, at, scale=1.0):
        if scale != 1.0:
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.NEAREST)
            piv = (round(piv[0] * scale), round(piv[1] * scale))
        cv.alpha_composite(im, (at[0] - piv[0], at[1] - piv[1]))

    if "elite_barrel_armor" in made:
        for e in ("dummy", "charger"):
            body, bp = enemy(e)
            cv = Image.new("RGBA", (200, 230), (0, 0, 0, 0))
            foot = (100, 210)
            bx = boxes[e]
            at = (foot[0] + bx["cx"], foot[1] + bx["cy"] + 22)
            fr = made["elite_barrel_armor"]
            put(cv, fr[0], fx2.APIV, at, bx["scale"])
            put(cv, body, bp, foot)
            put(cv, fr[3], fx2.APIV, at, bx["scale"])
            out.append((cv, None))
    if "elite_drunk_vapor" in made:
        body, bp = enemy("archer")
        cv = Image.new("RGBA", (160, 230), (0, 0, 0, 0))
        foot = (80, 220)
        put(cv, body, bp, foot)
        put(cv, made["elite_drunk_vapor"][2], fx2.VPIV, (foot[0], foot[1] - heads["archer"] + 8))
        out.append((cv, None))
    if "elite_ringleader_link" in made:
        lead, lp = enemy("dummy")
        ally, ap = enemy("archer")
        cv = Image.new("RGBA", (420, 200), (0, 0, 0, 0))
        f1, f2 = (70, 180), (330, 160)
        put(cv, made["elite_ringleader_aura"][1], fx2.RPIV, f2)
        put(cv, lead, lp, f1)
        put(cv, ally, ap, f2)
        tile = made["elite_ringleader_link"][2]
        x0, y0, x1, y1 = f1[0], f1[1] - 60, f2[0], f2[1] - 60
        L = int(math.hypot(x1 - x0, y1 - y0))
        strip = Image.new("RGBA", (L, tile.height), (0, 0, 0, 0))
        for x in range(0, L, tile.width):
            strip.alpha_composite(tile.crop((0, 0, min(tile.width, L - x), tile.height)), (x, 0))
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        rs = strip.rotate(-ang, resample=Image.NEAREST, expand=True)
        cv.alpha_composite(rs, ((x0 + x1) // 2 - rs.width // 2, (y0 + y1) // 2 - rs.height // 2))
        out.append((cv, None))
    return out


if __name__ == "__main__":
    main()
