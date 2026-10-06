"""out/grid 의 시트 하나를 바닥 위 k 배로 펼침: python3 zoom.py 이름 [k]"""
import json, os, sys
from PIL import Image
import tk, tview
name = sys.argv[1]; k = int(sys.argv[2]) if len(sys.argv) > 2 else 3
d = os.path.join(tk.STAGE, "fx", "v3")
m = json.load(open(os.path.join(d, name + ".json")))
im = Image.open(os.path.join(d, name + ".png")).convert("RGBA")
fw, fh, n = m["frameWidth"], m["frameHeight"], m["frames"]
rows = [[im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for c in range(n)] for r in range(im.height // fh)]
tview.strip(name, rows, m, k).save("out/z_%s.png" % name)
print("out/z_%s.png" % name)
