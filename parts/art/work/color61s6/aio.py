"""atlas57 의 JSON·PNG 저장 규칙(프레임 한 줄·무손실 팔레트 PNG)을 그대로 쓰는 입출력 도우미."""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
_m = {}


def ab():
    if "m" not in _m:
        spec = importlib.util.spec_from_file_location("atlas57_build_c61s6", os.path.join(WORK, "atlas57", "build.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _m["m"] = m
    return _m["m"]


def read_json(p):
    return json.load(open(p, encoding="utf-8"))


def write_atlas_json(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        f.write(ab().dump_json(obj))


def write_plain_json(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def save_png(im, p):
    ab().save_png(ab().normalize(im), p)
