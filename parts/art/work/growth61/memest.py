"""격자 원본으로 갈래별 메모리 어림(트림 상자 면적 합 × 4B, 포장 여유 미포함) — 검수용."""
import json, glob, os, sys
from PIL import Image
from collections import defaultdict
import g61 as Z
w = sys.argv[1]
tot = defaultdict(float)
for jp in glob.glob(os.path.join(Z.STAGE, 'weapons', w + '_*.json')):
    j = json.load(open(jp)); im = Image.open(jp[:-5] + '.png'); fw, fh = j['frameWidth'], j['frameHeight']
    a = 0
    for r in range(im.height // fh):
        for c in range(im.width // fw):
            b = im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)).getbbox()
            if b: a += (b[2] - b[0] + 2) * (b[3] - b[1] + 2)
    n = os.path.basename(jp)[:-5]; br = n.split('_')[1]
    layer = 'glow' if '_a2_glow_' in n else 'a2' if '_a2_' in n else 'a1'
    tot[(br, layer)] += a * 4 / 2 ** 20
aw = json.load(open(os.path.join(Z.AW, 'publish_log.json')))
ref = sum(x['gpuAfterMB'] for x in aw if x['cat'] == 'weapons' and x['name'].startswith(w + '_'))
for b in sorted({k[0] for k in tot}):
    s = sum(tot[(b, l)] for l in ('a1', 'a2', 'glow'))
    print(b, {l: round(tot[(b, l)], 2) for l in ('a1', 'a2', 'glow')}, 'sum', round(s, 2), 'ref', round(ref, 2), 'x%.2f' % (s / ref))
