"""반복 검수용 — 이 작업이 바꾼 파일(changed.json)을 기준 커밋(REV)으로 되돌린다. 다른 파일은 건드리지 않는다.
사용: python3 parts/art/work/color61s6_gb/restore.py [--rev a2def0f]"""
import argparse
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))

ap = argparse.ArgumentParser()
ap.add_argument("--rev", default="a2def0f")
a = ap.parse_args()
c = json.load(open(os.path.join(HERE, "changed.json"), encoding="utf-8"))
paths = set()
for n in c["changed"] + c["metaOnly"]:
    base = os.path.join("assets/sprites", n)
    if n.endswith((".png", ".json")):
        paths.add(base)
        continue
    m = json.load(open(os.path.join(ROOT, base + ".json"), encoding="utf-8"))
    paths.add(base + ".json")
    for im in ([t["image"] for t in m["textures"]] if "textures" in m else [m.get("meta", {}).get("image", m.get("image"))]):
        paths.add(os.path.join(os.path.dirname(base), im))
paths = sorted(paths)
for i in range(0, len(paths), 200):
    subprocess.run(["git", "-C", ROOT, "checkout", a.rev, "--"] + paths[i:i + 200], check=True)
print("되돌림", len(paths))
