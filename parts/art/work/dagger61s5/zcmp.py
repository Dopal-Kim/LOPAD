import sys, view, d5
rel = sys.argv[1]; body = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None
cells = [tuple(map(int, x.split(","))) for x in sys.argv[3].split()] if len(sys.argv) > 3 else [(3, 2), (0, 1), (2, 3), (1, 2)]
half = int(sys.argv[4]) if len(sys.argv) > 4 else 28
sc = int(sys.argv[5]) if len(sys.argv) > 5 else 6
a = view.zoom_grip(rel, cells, d5.before_root(), body, half, sc)
b = view.zoom_grip(rel, cells, d5.STAGE, body, half, sc)
view.stack([a, b]).save("out/z.png")
