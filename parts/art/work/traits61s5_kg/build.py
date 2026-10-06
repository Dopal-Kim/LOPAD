"""61 단계 5 (P13) 개성 전투 fx — 칼·대검 (+ 그 무기 공명). 요청 원본 parts/system/notes/trait-art-requests-61s5.md §0·§1.

  python3 parts/art/work/traits61s5_kg/build.py            # 전부 그림 → 검사 → assets/sprites/fx/v3 트림 아틀라스 + 미리보기
  python3 parts/art/work/traits61s5_kg/build.py --dry      # 그림·검사·미리보기만(assets 안 씀)
  python3 parts/art/work/traits61s5_kg/build.py --only k_edgeLift g_launch

결정적(시드 고정). 격자 원본은 out/grid(git 제외), 임시 폴더 out/_atlas_tmp_tkg_<pid>.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kit  # noqa: E402
import katana  # noqa: E402
import greatsword  # noqa: E402
import preview  # noqa: E402

VERSION = "v3-r61s5-trait"
SRC = "parts/art/work/traits61s5_kg/build.py (61 단계 5 P13 — 개성 전투 fx 칼·대검)"
REQ = "parts/system/notes/trait-art-requests-61s5.md §1"
PAL = {
    "katana": "61 단계 5 칼 '은선' 램프: 무채 16(G1~G14)·청강 SL·호박 불티 A17~A25 + 갈래 표지색(묶음 청회 #9ab0d8 램프·달 청백 #c8d8f0 램프·피 적갈 #b04848 램프·술/불 = pool_liquor(_fire) 1층 호박) · 백열 X0/X1·A26 은 glowFrames 만. paletteSwap none",
    "greatsword": "대검 붓획 램프(53 Q61): 재 S0~S3·B0~B3 + 혼불 호박 A17~A25 + 갈래 표지색(불 = pool_liquor_fire 계열, 포효 적갈 #b04848 램프) · 백열 X0/X1·A26 은 glowFrames 만. paletteSwap none",
}
ANCHOR_NOTE = {
    "mob_feet": "적 발 피벗", "hitbox_center": "적 몸 중심", "player_pivot": "주인공 발", "contact": "박힌 자리(벽 면·두 적 사이)",
    "projectile": "투사체 중심(진행 각도로 회전)", "floor": "바닥 깊이(발 높이 바닥점)", "path_start": "길 시작점",
}


def build_meta(name, spec, weapon, ncolors):
    ms = spec["ms"]
    m = {
        "action": name,
        "version": VERSION,
        "directions": ["any"],
        "layout": "rows = directions, columns = frames",
        "frameIndex": "row * frames + column",
        "fps": round(1000.0 * len(ms) / sum(ms), 2),
        "frameDurationsMs": ms,
        "loop": bool(spec.get("loop", False)),
        "pixelScale": 0.5,
        "paletteSwap": "none",
        "paletteSwapNote": "53라운드 Q62·Q68 — fx 는 지역 바닥 팔레트 교체 제외",
        "palette": PAL[weapon],
        "colors": ncolors,
        "semiTransparent": False,
        "source": SRC,
        "request": REQ,
        "weapon": weapon,
        "anchor": spec["anchor"],
        "pivot": {"x": spec["pivot"][0], "y": spec["pivot"][1]},
        "depth": spec.get("depth", "above"),
        "scale": "none",
        "scaleNote": "전용 fx 는 시트 배율 그대로(요청 §0 — 시스템이 더 키우지 않음)",
        "glowFrames": spec.get("glow", []),
        "glowRule": "백열 X0/X1·A26 은 glowFrames 칸만(빌드 검사)",
        "design": spec["design"],
        "replaces": spec["replaces"],
    }
    if spec.get("trait"):
        m["trait"] = spec["trait"]
    if spec.get("resonance"):
        m["resonance"] = spec["resonance"]
    m["part"] = spec.get("part") or "body"
    m["anchorNote"] = spec.get("anchorNote") or ("pivot = " + ANCHOR_NOTE.get(spec["anchor"], spec["anchor"]))
    if spec.get("rotate"):
        m["rotate"] = True
        m["drawnFacing"] = "right"
        if spec.get("flipY"):
            m["flipY"] = spec["flipY"]
    if spec.get("flipX"):
        m["flipX"] = spec["flipX"]
        m["flipXNote"] = spec.get("flipXNote", "")
    if spec.get("anchorOffsetDots"):
        m["anchorOffsetDots"] = spec["anchorOffsetDots"]
    if spec.get("loopRange"):
        m["loopRange"] = spec["loopRange"]
        m["endFrames"] = spec.get("endFrames")
        m["lifeRule"] = spec.get("lifeRule", "")
        m["life"] = "loopRange"
    if spec.get("light"):
        m["light"] = spec["light"]
        m["lightNote"] = "radius = 도트(pixelScale 0.5 기준), ms = 켜 두는 시간(없으면 시트 수명 동안)"
    if spec.get("tile"):
        m["tile"] = True
        m["tilePeriodDots"] = spec["size"][0]
        m["tileNote"] = spec.get("tileNote", "")
    return m


def run(only=None, dry=False):
    stats = {}
    shown = {"katana": [], "greatsword": []}
    for weapon, mod in (("katana", katana), ("greatsword", greatsword)):
        for name, spec in mod.SHEETS.items():
            if only and not any(o in name for o in only):
                continue
            fs = katana.frames(spec["size"], len(spec["ms"]))
            spec["fn"](fs)
            ims = [fx.image() for fx in fs]
            if spec.get("tile"):
                for im in ims:  # 위아래 가장자리만 비움(좌우는 이어져야 함)
                    px = im.load()
                    for x in range(im.width):
                        px[x, 0] = px[x, im.height - 1] = (0, 0, 0, 0)
            else:
                ims = [kit.clear_edge(im) for im in ims]
            nc = kit.check_frames(name, ims, set(spec.get("glow", [])), max_colors=spec.get("maxColors", 24)) if not spec.get("tile") else _check_tile(name, ims, spec)
            meta = build_meta(name, spec, weapon, nc)
            shown[weapon].append((name, ims, meta))
            if not dry:
                st = kit.publish(name, ims, meta)
            else:
                st = {}
            st.update(colors=nc, frames=len(ims), size=list(spec["size"]))
            stats[name] = st
            print(name, st)
    for weapon, items in shown.items():
        if items:
            preview.sheets(items, os.path.join(HERE, "preview_%s.png" % weapon), title=weapon)
            preview.overview(items, os.path.join(HERE, "preview_%s_scene.png" % weapon))
    if not dry and not only:
        with open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=1)
    return stats


def _check_tile(name, ims, spec):
    cols = set()
    for i, im in enumerate(ims):
        a = set(im.getchannel("A").getdata())
        assert a <= {0, 255}, (name, i)
        cs = {p[:3] for p in im.getdata() if p[3]}
        if i not in spec.get("glow", []):
            assert not (cs & kit.HOT), (name, i, "백열")
        cols |= cs
    assert len(cols) <= 18
    return len(cols)


if __name__ == "__main__":
    args = sys.argv[1:]
    dry = "--dry" in args
    only = None
    if "--only" in args:
        only = args[args.index("--only") + 1:]
        only = [o for o in only if not o.startswith("--")]
    run(only, dry)
