"""P19 내보낸 시트 점검: out/grid(격자 원본) ↔ assets 트림 아틀라스를 전 프레임 픽셀 대조 + 메타 핵심 필드 일치 + 몸 색 합계.
python3 check19.py → 불일치 0 이어야 함."""
import json
import os
import sys
from glob import glob

from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "atlas57"))
import gridsheet  # noqa: E402

GRID = os.path.join(HERE, "out", "grid")
SPR = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "assets", "sprites"))
bad, n = [], 0
body_cols = set()
for jp in sorted(glob(os.path.join(GRID, "**", "*.json"), recursive=True)):
    rel = os.path.relpath(jp, GRID)[:-5]
    g = Image.open(jp[:-5] + ".png").convert("RGBA")
    gm = json.load(open(jp, encoding="utf-8"))
    aj = os.path.join(SPR, rel + ".json")
    try:
        am = gridsheet.load_meta(aj)
        a = gridsheet.open_grid(aj[:-5] + ".png").convert("RGBA")
    except Exception as e:
        bad.append((rel, "읽기 실패 %s" % e))
        continue
    n += 1
    for k in ("frameWidth", "frameHeight", "frames", "frameDurationsMs", "pivot", "directions"):
        if gm.get(k) != am.get(k):
            bad.append((rel, "메타 %s" % k))
    if g.size != a.size or ImageChops.difference(g, a).getbbox():
        # 알파 0 RGB 정규화 차이는 무시
        ga = [p if p[3] else (0, 0, 0, 0) for p in g.getdata()]
        aa = [p if p[3] else (0, 0, 0, 0) for p in a.getdata()]
        if g.size != a.size or ga != aa:
            bad.append((rel, "픽셀"))
    if rel.startswith("player/"):
        body_cols |= {p[:3] for p in g.getdata() if p[3]}
    semi = set(g.getchannel("A").getdata()) - {0, 255}
    if semi:
        bad.append((rel, "반투명"))
print("시트", n, "불일치", len(bad))
for b in bad[:30]:
    print("  ", b)
print("몸 시트(이번에 낸 것) 색 합계", len(body_cols))
