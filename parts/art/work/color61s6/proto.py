import sys, os
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import view as V
def lut_img(im, lut):
    px = im.load(); W, H = im.size
    L = {tuple(int(k[i:i+2],16) for i in (1,3,5)): tuple(int(v[i:i+2],16) for i in (1,3,5)) for k, v in lut.items()}
    for y in range(H):
        for x in range(W):
            p = px[x, y]
            if p[3] and p[:3] in L:
                px[x, y] = L[p[:3]] + (255,)
    return im
def strip_lut(rel, lut, row="right", scale=1, dark=0.5, maxn=8):
    m, sh = V.load(rel)
    sh = lut_img(sh, lut)
    fr = V.frames_of(m, sh, row)[:maxn]
    fw, fh = fr[0].size
    out = V.floor_bg(fw * len(fr), fh, dark)
    for i, f in enumerate(fr): out.alpha_composite(f, (i * fw, 0))
    return out.resize((out.width*scale, out.height*scale), Image.NEAREST)
A = {"#d8d9db":"#8fe3ff","#c5c6c9":"#64c4ec","#b2b4b8":"#48a3d4","#8e9195":"#3a82b4","#7e8693":"#2f6996","#626a78":"#264f75","#4e5563":"#1d3a58","#fff4dc":"#dcfaff","#ebeced":"#c8f5ff",
     "#eecc78":"#c8f5ff","#e2a33c":"#8fe3ff","#d67a11":"#48a3d4","#8b4d22":"#264f75","#f4de9b":"#dcfaff"}
B = dict(A); B.update({"#c5c6c9":"#cfe6f0","#b2b4b8":"#a6c2d2","#8e9195":"#7f9cb2","#7e8693":"#5e7a92","#626a78":"#455d74","#4e5563":"#33465a"})
rels = sys.argv[2:]
ims = []
for r in rels:
    ims += [V.strip(r, None, "right", 2, 0.5, 6), strip_lut(r, A, scale=2, maxn=6), strip_lut(r, B, scale=2, maxn=6)]
V.stack(ims).save(sys.argv[1])
