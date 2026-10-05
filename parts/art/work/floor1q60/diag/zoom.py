import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet import frames, strip, SPR
from PIL import Image
# zoom.py <category/v3/name> row col[,col] scale out
p, row, cols, sc, out = sys.argv[1], int(sys.argv[2]), [int(c) for c in sys.argv[3].split(",")], int(sys.argv[4]), sys.argv[5]
meta, fr = frames(os.path.join(SPR, p))
strip([fr[row][c] for c in cols], sc).save(out)
