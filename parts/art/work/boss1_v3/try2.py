"""작업용: TRYDIR=/절대/폴더 python3 try2.py <동작...> → 그 폴더에 2배 시트(TRYDIR 필수 — 빈 값이면 중단)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "enemies_v3")); sys.path.insert(0, HERE)
import eanim, eprev
import b1acts
out = os.environ.get("TRYDIR", "")
assert out and os.path.isabs(out) and os.path.isdir(out), "TRYDIR 에 존재하는 절대 경로 폴더를 주세요: %r" % out
acts = sys.argv[1:]
res = eanim.render_all("b1acts", acts)
for a in acts:
    fr = {d: [im for im, _ in res[a][d]] for d in eanim.DIRS}
    ms = b1acts.META[a]["ms"]
    assert len(ms) == len(fr["down"]), (a, len(ms), len(fr["down"]))
    eprev.frames_x2(os.path.join(out, "b1_%s.png" % a), a, fr, ms, b1acts.PIV)
    print(os.path.join(out, "b1_%s.png" % a))
