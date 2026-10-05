"""60라운드 Q1 최종 각성 외형 재디자인 시안 — 무기별 3개 × 4 = 12. 실행: python3 parts/art/work/awaken60/build.py [katana greatsword dagger bow]
출력: parts/art/work/awaken60/out/<무기>/<키>_preview.png · <키>.gif · compare_<무기>.png. assets 는 바꾸지 않는다(읽기만).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit60 as K  # noqa: E402
import stage  # noqa: E402

WEAPONS = ["katana", "greatsword", "dagger", "bow"]


def run(wname):
    mod = __import__(wname)
    outdir = os.path.join(K.OUT, wname)
    sums = []
    for c in mod.CONCEPTS:
        t0 = time.time()
        im, sm = stage.preview(c, mod.POSES, outdir)
        print(f"  {c.key} {im.size} {time.time() - t0:.1f}s")
        sums.append((c, sm))
    compare(wname, sums, outdir)


def compare(wname, sums, outdir):
    from PIL import Image
    cols = []
    for c, sm in sums:
        ctx = sm["ctx"]
        CW = ctx.width
        hero = K.up(sm["hero_1x"], max(2, min(6, int(CW * 0.6 / max(sm["hero_1x"].size)))))
        strip = sm["strip"]
        ks = CW / strip.width
        strip = strip.resize((int(strip.width * ks), int(strip.height * ks)), Image.NEAREST)
        loop = sm["loop"]
        kl = CW / loop.width
        loop = loop.resize((int(loop.width * kl), int(loop.height * kl)), Image.NEAREST)
        head = K.text_block(CW, [(f"[{c.key}] {c.title}", 22, None), ("형태: " + c.form, 16, (190, 190, 184)),
                                 ("색: " + c.color, 16, (190, 190, 184)), ("fx: " + c.fx, 16, (190, 190, 184))])
        col = K.stack_v([head, K.pad(hero, 6), ctx, strip, loop], gap=8)
        cols.append(col)
    base = sums[0][1]["base_1x"]
    base = K.up(base, max(2, min(6, int(600 / max(base.size)))))
    bcol = K.caption(K.pad(base, 6), "원래 무기", 18, 30)
    out = K.stack_h([bcol] + cols, gap=20)
    out = K.caption(K.pad(out, 10), f"{wname} — 최종 각성 시안 비교 (A·B·C) · 60라운드 Q1", 26, 44)
    if max(out.size) > 8000:
        k = 8000 / max(out.size)
        out = out.resize((int(out.width * k), int(out.height * k)), Image.NEAREST)
    out.save(os.path.join(outdir, f"compare_{wname}.png"))
    print(f"  compare {out.size}")


if __name__ == "__main__":
    for w in (sys.argv[1:] or WEAPONS):
        print(w)
        run(w)
