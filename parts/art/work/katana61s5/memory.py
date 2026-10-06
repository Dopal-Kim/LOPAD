"""61 단계 5 칼 — 바꾼 시트의 아틀라스 페이지 RGBA(MB) 전(SRC_REV)/후(assets) → out/memory.json + 표 출력."""
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kcommon as C  # noqa: E402


def area(m):
    if "textures" in m:
        return sum(t["size"]["w"] * t["size"]["h"] for t in m["textures"])
    return m["meta"]["size"]["w"] * m["meta"]["size"]["h"]


def before(rel):
    raw = subprocess.run(["git", "-C", C.ROOT, "show", "%s:assets/sprites/%s.json" % (C.SRC_REV, rel)], capture_output=True, check=True).stdout
    return area(json.loads(raw)) * 4 / 1048576.0


def after(rel):
    return area(json.load(open(os.path.join(C.SPR, rel + ".json"), encoding="utf-8"))) * 4 / 1048576.0


def groups():
    base = os.path.join(C.HERE, "out", "meta0")
    rels = sorted(os.path.relpath(p, base)[:-5].replace(os.sep, "/") for p in glob.glob(os.path.join(base, "*", "*", "*.json")))
    g = {}
    for r in rels:
        n = os.path.basename(r)
        if r.startswith("weapons/v4/"):
            k = "weapons/v4 " + n.split("_")[1]
        elif r.startswith("weapons/v3/"):
            k = "weapons/v3 " + ("ki" if "_ki" in n else "awaken" if n.endswith("_awaken") else "base")
        else:
            k = "fx/v3 " + ("awaken" if n.endswith("_awaken") else "base")
        g.setdefault(k, []).append(r)
    return g


def main():
    out = {}
    tb = ta = 0.0
    for k, rels in sorted(groups().items()):
        b = sum(before(r) for r in rels)
        a = sum(after(r) for r in rels)
        out[k] = dict(sheets=len(rels), beforeMB=round(b, 2), afterMB=round(a, 2), ratio=round(a / b, 3) if b else None)
        tb += b
        ta += a
        print("%-22s %3d  %7.2f → %7.2f  ×%.3f" % (k, len(rels), b, a, a / b if b else 0))
    out["total"] = dict(beforeMB=round(tb, 2), afterMB=round(ta, 2), ratio=round(ta / tb, 3))
    print("total %.2f → %.2f ×%.3f" % (tb, ta, ta / tb))
    json.dump(out, open(os.path.join(HERE, "memory.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
