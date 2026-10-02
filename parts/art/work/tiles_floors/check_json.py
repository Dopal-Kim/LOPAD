#!/usr/bin/env python3
"""stage1~8.json 동일성 검사 (40라운드 v3). 키 집합·tiles·walls·roomFloors·props[].index·columns/rows·PNG 크기가 8개 층 전부 같은지 확인.
49라운드: assets/tiles/stage1_<region>.json (지역 타일, 계약 §7.3) 이 있으면 함께 검사한다 — 같은 인덱스 표 v3·같은 키.
실행: python3 parts/art/work/tiles_floors/check_json.py"""
import json
import os
import sys

from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
D = os.path.join(ROOT, "assets", "tiles")
import glob  # noqa: E402

metas = {n: json.load(open(os.path.join(D, "stage%d.json" % n), encoding="utf-8")) for n in range(1, 9)}
for _p in sorted(glob.glob(os.path.join(D, "stage1_*.json"))):
    metas[os.path.basename(_p)[:-5]] = json.load(open(_p, encoding="utf-8"))
ok = True


def same(label, fn):
    global ok
    vals = {n: fn(m) for n, m in metas.items()}
    ref = vals[1]
    bad = [n for n, v in vals.items() if v != ref]
    print("%-28s %s  %s" % (label, "OK " if not bad else "DIFF " + str(bad), json.dumps(ref, ensure_ascii=False) if len(json.dumps(ref)) < 110 else ""))
    ok = ok and not bad


same("key set", lambda m: sorted(m.keys()))
same("columns/rows", lambda m: (m["columns"], m["rows"]))
same("tiles", lambda m: m["tiles"])
same("walls (minus note)", lambda m: {k: v for k, v in m["walls"].items() if k != "note"})
same("roomFloors", lambda m: m["roomFloors"])
same("props[].index", lambda m: [p["index"] for p in m["props"]])
same("props[] key set", lambda m: sorted(set(k for p in m["props"] for k in p)))
same("props count", lambda m: len(m["props"]))
same("names index 0..12,21,22,23..39", lambda m: {k: v for k, v in m["names"].items() if not v.startswith("prop_")})
expect = {"0": [7], "1": [0, 1, 2, 3], "2": [5, 21, 22], "3": [8], "4": [9], "5": [10], "6": [4], "7": [11], "8": [12]}
print("tiles == v3 table:", "OK" if metas[1]["tiles"] == expect else "MISMATCH")
expect_rf = {"start": [23, 24, 25, 26], "trial": [27, 28, 29, 30], "rest": [31, 32, 33, 34], "boss": [35, 36, 37, 38]}
print("roomFloors == v3 table:", "OK" if metas[1]["roomFloors"] == expect_rf else "MISMATCH")
print("props index == 13..20:", "OK" if [p["index"] for p in metas[1]["props"]] == list(range(13, 21)) else "MISMATCH")
for n, m in metas.items():
    im = Image.open(os.path.join(D, m["image"]))
    sz_ok = im.size == (m["columns"] * m["tileWidth"], m["rows"] * m["tileHeight"]) == (128, 80)
    ok = ok and sz_ok
    print("%s png %s %s | props: %s" % (n if isinstance(n, str) else "stage%d" % n, im.size, "OK" if sz_ok else "BAD", ", ".join(
        "%s%s(%d,%.1f)" % (p["name"], "*" if p["solid"] else "", p["maxPerRoom"], p["weight"]) for p in m["props"])))
print("ALL SAME:", ok)
sys.exit(0 if ok else 1)
