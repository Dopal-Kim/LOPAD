"""루프 1 요청(시스템 A → 아트) · P1-4 — 일반 적 1도트 차가운 림 시트.

엘리트 외곽선(호박, ×1.15) 재사용 대신, 적 시트마다 같은 틀·피벗·프레임 번호의 '바깥 1도트 차가운 테'를 만든다.
- 테 = 몸 실루엣(불투명 칸) 바로 바깥 빈 칸 1도트. 위를 향한 테는 밝게(달빛), 옆은 중간, 아래(발·그림자 쪽)는 그리지 않는다.
- 색은 차가운 달빛 청회색 3단(층 램프 스왑 대상 아님) — 어두운 흙바닥·갈색 몸 둘 다에서 갈라 보인다.
"""
from PIL import Image

from common import COLD_RIM, b2, load_grid, SRC, hexc

ENEMIES = ["dummy", "archer", "charger", "peddler", "porter"]
ACTIONS = ["idle", "walk", "attack", "hurt", "death"]
SOLID_A = 200


def rim_frame(im, pivot_y):
    w, h = im.size
    p = im.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    q = out.load()

    def solid(x, y):
        return 0 <= x < w and 0 <= y < h and p[x, y][3] >= SOLID_A

    for y in range(h):
        for x in range(w):
            if solid(x, y):
                continue
            below, above, left, right = solid(x, y + 1), solid(x, y - 1), solid(x - 1, y), solid(x + 1, y)
            if not (below or above or left or right):
                continue
            if y >= pivot_y - 5 and not (left or right) and not below:
                continue                                   # 발밑 접지선은 비움
            if above and not (below or left or right):
                continue                                   # 아래쪽 테(몸 밑)는 그리지 않음
            if below:
                c = COLD_RIM[2] if (left or right) else COLD_RIM[3] if y < pivot_y - 40 else COLD_RIM[2]
            elif right:
                c = COLD_RIM[1]                            # 몸 왼쪽 테(달빛 쪽)
            else:
                c = COLD_RIM[0]                            # 몸 오른쪽 테(그늘 쪽)
            q[x, y] = c + (255,)
    return out


def build(preview_path=None):
    previews = []
    for e in ENEMIES:
        for a in ACTIONS:
            name = f"{e}_{a}"
            m, g = load_grid("enemies/v3/" + name)
            fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
            rows = len(m["directions"])
            frames = []
            for r in range(rows):
                for c in range(n):
                    src = g.crop((c * fw, r * fh, c * fw + fw, r * fh + fh))
                    frames.append(rim_frame(src, m["pivot"]["y"]))
            meta = {
                "directions": m["directions"], "layout": m.get("layout"),
                "pivot": m["pivot"], "role": "rim_cold", "baseSheet": "enemies/v3/" + name, "enemy": e,
                "overlayOf": "enemies/v3/" + name, "sameFrameAs": "enemies/v3/" + name,
                "draw": "적 스프라이트 바로 위(같은 컨테이너, 같은 프레임 번호·피벗·flip·scale). 그림은 실루엣 바깥 1도트라 몸을 가리지 않는다. "
                        "엘리트는 이 시트 대신 `_elite` 외곽선을 쓴다(둘 다 켜지 않음).",
                "rimColors": [hexc(c) for c in COLD_RIM],
                "rimNote": "위를 향한 테 #7d98b4/#a8c0d6(달빛) · 몸 왼쪽 #56708c · 오른쪽 #3a4a5e · 아래·발밑 없음. 비발광(조명 아래) — 어둠 속 가독성이 모자라면 시스템이 알파 0.6~0.8 가산 레이어로 올려도 된다(제안).",
                "drawOver": "lightmap 아래(비발광) 기본 — 시스템 판단",
                "flashRule": "피격 흰빛(가산) 때도 테는 그대로 둔다(몸 형태 유지)",
                "paletteSwap": "none", "palette": "차가운 달빛 청회색 4단(#3a4a5e·#56708c·#7d98b4·#a8c0d6) — 적 가독성 전용(층 램프 밖, 고정)",
                "regenerate": "적 시트를 다시 그리면 parts/art/work/r62b/build.py --only rim", "version": "v3-r62b",
                "source": SRC + " · rim.py",
            }
            b2.write_sheet("enemies", name + "_rim", frames, fw, fh, meta, rows=rows,
                           durations=m["frameDurationsMs"], loop=m.get("loop", False))
            if preview_path and a in ("idle", "attack"):
                body = g.crop((0, 0, fw * min(n, 6), fh))
                strip = Image.new("RGBA", body.size, (58, 46, 36, 255))
                strip.alpha_composite(body)
                for c in range(min(n, 6)):
                    strip.alpha_composite(frames[c], (c * fw, 0))
                previews.append(strip)
    if preview_path:
        from common import board
        board(previews, k=2, max_w=1400).save(preview_path)
