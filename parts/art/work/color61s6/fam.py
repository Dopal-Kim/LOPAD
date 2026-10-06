import sys, os, colorsys
from collections import Counter
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import targets as T, colors as CO
FAM = {}
def fam(h):
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    hh, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255); hh*=360
    if h in ("#ffffff",): return "X0"
    if h == "#fff4dc": return "X1"
    if s < 0.12: return "grey"
    if 210 <= hh <= 232 and s < 0.45: return "steel"
    if 15 <= hh <= 34 and v < 0.5: return "ash"
    if 15 <= hh <= 46: return "amber"
    if 47 <= hh <= 60: return "gold"
    if 150 <= hh <= 195: return "teal"
    if 255 <= hh <= 300: return "violet"
    if hh >= 330 or hh <= 14: return "red"
    return "other%d" % hh
for g in sys.argv[1:]:
    rels = getattr(T, g.split(':')[0])(*g.split(':')[1:]) if ':' in g else getattr(T, g)()
    for r in rels:
        C, _ = CO.hist([r])
        F = Counter()
        for h, n in C.items(): F[fam(h)] += n
        print(os.path.basename(r), dict(F.most_common()))
