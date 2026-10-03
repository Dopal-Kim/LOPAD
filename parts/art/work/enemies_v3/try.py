"""작업용: python3 try.py <모듈> <동작...> → 스크래치에 2배 시트(병렬 렌더)."""
import importlib
import os
import sys

import eanim as anim
import eprev as preview

mod = importlib.import_module(sys.argv[1])
acts = sys.argv[2:] or anim.ACTS
outdir = os.environ.get("TRYDIR", "/tmp")
res = anim.render_all(sys.argv[1], acts)
for a in acts:
    old, sp = anim.split_of(mod, a)
    ms, fmap = anim.split_ms(old["frameDurationsMs"], sp)
    fr = {d: [im for im, _ in res[a][d]] for d in anim.DIRS}
    preview.frames_x2(os.path.join(outdir, "%s_%s.png" % (mod.ID, a)), "%s %s" % (mod.ID, a), fr, ms, mod.PIV)
    print(os.path.join(outdir, "%s_%s.png" % (mod.ID, a)))
